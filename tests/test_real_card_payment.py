"""Offline tests for the explicit real-card payment opt-in.

Until this feature existed the package could only ever send a fake card. That
was enforced by two independent gates, and BOTH are still in place: what changed
is that a caller may now state, explicitly and loudly, that the card is real.
These tests pin the new semantics:

* ``MutationConsent.real_card_acknowledged`` defaults to ``False``, so every
  consent written before it existed means exactly what it meant before.
* The transmit gate accepts a payment only on an UNAMBIGUOUS consent — exactly
  one of ``fake_card_only`` / ``real_card_acknowledged``. Neither is the
  historical refusal; both is a contradiction and is also refused.
* ``pay_with_card`` requires the acknowledgement and refuses a fake-card
  consent, and its dry run redacts the PAN exactly like its sibling.

Everything runs against ``httpx.MockTransport``. No network, no credentials, and
the only card numbers here are obviously-fake placeholders.
"""

from __future__ import annotations

import httpx
import pytest

from korail_mobile_api import (
    CardPayment,
    KorailAuthError,
    KorailClient,
    KorailConfig,
    KorailSession,
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from korail_mobile_api.mutation_payloads import build_card_payment_form

PAYMENT_ROUTE = "/classes/com.korail.mobile.payment.ReservationPayment"

# Obviously-fake placeholders. 4111111111111111 is the industry-standard test
# PAN; it is not a real card and nothing here is ever transmitted anywhere.
PLACEHOLDER_CARD_NUMBER = "4111111111111111"
PLACEHOLDER_CARD_PASSWORD = "00"
PLACEHOLDER_CARD_EXPIRE = "3012"
PLACEHOLDER_BIRTHDAY = "900101"
SYNTHETIC_PNR = "SYNTHETIC_PNR_REFERENCE"

_PAYMENT_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRZ000001",
    "h_msg_txt": "paid",
    "h_img_tk_flg": "N",
}


class _Recorder:
    def __init__(self, replies: dict[str, dict]) -> None:
        self.replies = replies
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        reply = self.replies.get(request.url.path)
        if reply is None:  # pragma: no cover - guards test wiring mistakes
            raise AssertionError(f"unexpected request to {request.url.path}")
        return httpx.Response(200, json=reply)


def _client_with(replies: dict[str, dict]) -> tuple[KorailClient, _Recorder]:
    recorder = _Recorder(replies)
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client, recorder


def _hold() -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd="IRR000000",
        str_result="SUCC",
        raw={},
        pnr_no=SYNTHETIC_PNR,
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        temporary_job_sequence_1="SYNTHETIC_JOB_1",
        temporary_job_sequence_2="SYNTHETIC_JOB_2",
        total_price="8400",
        received_amount="8400",
    )


def _placeholder_card() -> CardPayment:
    return CardPayment(
        card_number=PLACEHOLDER_CARD_NUMBER,
        card_password=PLACEHOLDER_CARD_PASSWORD,
        card_expire=PLACEHOLDER_CARD_EXPIRE,
        birthday=PLACEHOLDER_BIRTHDAY,
    )


def _real_card_consent(**overrides: bool) -> MutationConsent:
    """The only consent shape that may carry a real card."""
    fields: dict[str, bool] = {
        "allow_payment": True,
        "dry_run": False,
        "fake_card_only": False,
        "real_card_acknowledged": True,
    }
    fields.update(overrides)
    return MutationConsent(**fields)


# --- MutationConsent.real_card_acknowledged semantics ------------------------


def test_real_card_acknowledged_defaults_to_false():
    # Additive by construction: a consent that names nothing new is unchanged.
    consent = MutationConsent()
    assert consent.real_card_acknowledged is False
    assert consent.fake_card_only is True


def test_every_pre_existing_consent_shape_still_means_fake_card_only():
    for consent in (
        MutationConsent(allow_payment=True),
        MutationConsent(allow_payment=True, dry_run=False),
        MutationConsent(
            allow_reserve=True,
            allow_payment=True,
            allow_cancel=True,
            allow_refund=True,
            dry_run=False,
        ),
    ):
        assert consent.real_card_acknowledged is False
        assert consent.fake_card_only is True


# --- the transmit gate: exactly one card claim -------------------------------


def _post_payment(client: KorailClient, consent: MutationConsent):
    form = build_card_payment_form(KorailConfig(), _hold(), _placeholder_card())
    return client.http.post_mutation_form(
        PAYMENT_ROUTE, form, consent=consent, category="payment"
    )


def test_transport_gate_refuses_a_payment_with_neither_card_claim():
    # The historical refusal, unchanged: fake_card_only turned off on its own
    # never authorised anything and still does not.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    consent = MutationConsent(
        allow_payment=True,
        dry_run=False,
        fake_card_only=False,
        real_card_acknowledged=False,
    )
    with pytest.raises(MutationNotAllowedError) as excinfo:
        _post_payment(client, consent)
    assert "real_card_acknowledged" in str(excinfo.value)
    assert recorder.requests == []


def test_transport_gate_refuses_a_payment_claiming_both_card_kinds():
    # A consent cannot claim a test card AND acknowledge a real charge. Paying
    # on an ambiguous consent is the exact mistake this gate exists to prevent,
    # so it is refused rather than resolved in either direction.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    consent = MutationConsent(
        allow_payment=True,
        dry_run=False,
        fake_card_only=True,
        real_card_acknowledged=True,
    )
    with pytest.raises(MutationNotAllowedError) as excinfo:
        _post_payment(client, consent)
    assert "contradictory" in str(excinfo.value)
    assert recorder.requests == []


def test_transport_gate_allows_a_payment_on_the_fake_card_claim():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    response = _post_payment(
        client, MutationConsent(allow_payment=True, dry_run=False)
    )
    assert response.str_result == "SUCC"
    assert [request.url.path for request in recorder.requests] == [PAYMENT_ROUTE]


def test_transport_gate_allows_a_payment_on_the_acknowledged_real_card_claim():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    response = _post_payment(client, _real_card_consent())
    assert response.str_result == "SUCC"
    assert [request.url.path for request in recorder.requests] == [PAYMENT_ROUTE]


def test_the_card_gate_is_keyed_on_the_card_bearing_category_set():
    # The gate asks "does this category's form carry a PAN", not "is this
    # category literally called payment". Both questions have the same answer
    # today; only one of them keeps having the right answer when a second
    # card-bearing product is added.
    from korail_mobile_api import KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    from korail_mobile_api.consent import MUTATION_CATEGORIES
    from korail_mobile_api.safety import (
        KORAIL_MUTATION_ROUTES,
        KORAIL_MUTATION_ROUTE_CATEGORIES,
    )

    assert "payment" in KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    assert KORAIL_CARD_BEARING_MUTATION_CATEGORIES <= set(MUTATION_CATEGORIES)
    # get_mutation_query has no card branch, and its docstring says that is
    # because no card-bearing category owns a GET route. Keep that a fact.
    get_categories = {
        KORAIL_MUTATION_ROUTE_CATEGORIES[path]
        for method, path in KORAIL_MUTATION_ROUTES
        if method == "GET"
    }
    assert not (get_categories & KORAIL_CARD_BEARING_MUTATION_CATEGORIES)


def test_the_card_gate_applies_only_to_the_payment_category():
    # A reserve/cancel/refund consent is untouched by the card claim rules.
    from korail_mobile_api.mutation_payloads import (
        build_single_adult_reservation_form,
    )
    from korail_mobile_api import TrainSummary

    reserve_route = "/classes/com.korail.mobile.certification.TicketReservation"
    client, recorder = _client_with(
        {
            reserve_route: {
                "strResult": "SUCC",
                "h_msg_cd": "IRR000000",
                "h_msg_txt": "held",
            }
        }
    )
    train = TrainSummary(
        train_no="00209",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0501",
        departure_date="20990101",
        departure_time="100700",
        arrival_time="102400",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="2",
        general_reservation_code="11",
        departure_construction_order="1",
        arrival_construction_order="2",
        seat_attribute_code="015",
    )
    form = build_single_adult_reservation_form(KorailConfig(), train)
    # Both card flags set would be a contradiction for a payment; for a reserve
    # the card claim is simply irrelevant and must not block the send.
    response = client.http.post_mutation_form(
        reserve_route,
        form,
        consent=MutationConsent(
            allow_reserve=True,
            dry_run=False,
            fake_card_only=True,
            real_card_acknowledged=True,
        ),
        category="reserve",
    )
    assert response.str_result == "SUCC"
    assert len(recorder.requests) == 1


def test_the_dry_run_gate_still_precedes_the_card_gate():
    # An acknowledged real charge does not make a preview sendable.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError) as excinfo:
        _post_payment(client, _real_card_consent(dry_run=True))
    assert "dry_run" in str(excinfo.value)
    assert recorder.requests == []


def test_the_category_gate_still_precedes_the_card_gate():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError):
        _post_payment(client, _real_card_consent(allow_payment=False))
    assert recorder.requests == []


# --- pay_with_fake_card is untouched ----------------------------------------


def test_pay_with_fake_card_still_refuses_an_acknowledged_real_card():
    # Its name must keep meaning what it says: it is not a real-card path, no
    # matter what the consent acknowledges.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_fake_card(
            _hold(), _placeholder_card(), consent=_real_card_consent()
        )
    assert recorder.requests == []


# --- pay_with_card gating ----------------------------------------------------


def test_pay_with_card_requires_payment_consent():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_card(
            _hold(),
            _placeholder_card(),
            consent=_real_card_consent(allow_payment=False),
        )
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_card(
            _hold(), _placeholder_card(), consent=None  # type: ignore[arg-type]
        )
    assert recorder.requests == []


def test_pay_with_card_refuses_a_default_fake_card_consent():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError) as excinfo:
        client.pay_with_card(
            _hold(),
            _placeholder_card(),
            consent=MutationConsent(allow_payment=True, dry_run=False),
        )
    assert "real_card_acknowledged" in str(excinfo.value)
    assert recorder.requests == []


def test_pay_with_card_refuses_a_contradictory_consent():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_card(
            _hold(),
            _placeholder_card(),
            consent=_real_card_consent(fake_card_only=True),
        )
    assert recorder.requests == []


def test_pay_with_card_requires_an_authenticated_session():
    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({PAYMENT_ROUTE: _PAYMENT_SUCCESS}))
    )
    with pytest.raises(KorailAuthError):
        logged_out.pay_with_card(
            _hold(), _placeholder_card(), consent=_real_card_consent()
        )


def test_pay_with_card_dry_run_redacts_the_pan_and_sends_nothing():
    client, recorder = _client_with({})
    preview = client.pay_with_card(
        _hold(),
        _placeholder_card(),
        consent=_real_card_consent(dry_run=True),
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "payment"
    assert preview.route == PAYMENT_ROUTE
    assert preview.note == "dry-run: not sent"
    for key in (
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        "hidAthnVal1",
        "hidAthnDvCd1",
        "hidIsmtMnthNum1",
        "hidPnrNo",
        "hidWctNo",
        "hidTmpJobSqno1",
        "hidTmpJobSqno2",
    ):
        assert preview.payload[key] == "[REDACTED]", key
    joined = "".join(preview.payload.values())
    for secret in (
        PLACEHOLDER_CARD_NUMBER,
        PLACEHOLDER_CARD_EXPIRE,
        PLACEHOLDER_BIRTHDAY,
        SYNTHETIC_PNR,
    ):
        assert secret not in joined, secret
    # Not even a partial PAN survives.
    assert PLACEHOLDER_CARD_NUMBER[:6] not in joined
    assert PLACEHOLDER_CARD_NUMBER[-4:] not in joined
    assert recorder.requests == []


def test_pay_with_card_live_posts_to_the_payment_route_and_parses_the_receipt():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    result = client.pay_with_card(
        _hold(), _placeholder_card(), consent=_real_card_consent()
    )
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "SUCC"
    assert result.h_msg_cd == "IRZ000001"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].method == "POST"
    assert recorder.requests[0].url.path == PAYMENT_ROUTE


def test_pay_with_card_returns_a_declined_envelope_instead_of_raising():
    # Deliberate: a real payment that the PG refuses must hand the caller the
    # server's own code so it can cancel the still-unpaid hold, not an
    # exception that says nothing about whether the hold survived.
    client, recorder = _client_with(
        {
            PAYMENT_ROUTE: {
                "strResult": "FAIL",
                "h_msg_cd": "WRC000123",
                "h_msg_txt": "card declined",
            }
        }
    )
    result = client.pay_with_card(
        _hold(), _placeholder_card(), consent=_real_card_consent()
    )
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "FAIL"
    assert result.h_msg_cd == "WRC000123"
    assert len(recorder.requests) == 1


def test_pay_with_card_sends_the_same_form_pay_with_fake_card_would():
    # The two methods differ only in which consent they accept; the wire shape
    # is one builder, so a real payment cannot drift from the verified one.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    client.pay_with_card(_hold(), _placeholder_card(), consent=_real_card_consent())
    sent = dict(
        pair.split("=", 1)
        for pair in recorder.requests[0].content.decode().split("&")
    )
    expected = build_card_payment_form(
        client.config, _hold(), _placeholder_card()
    )
    assert set(sent) == set(expected)
