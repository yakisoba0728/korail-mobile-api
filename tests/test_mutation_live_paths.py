"""Offline contract tests for the live mutation send paths.

These exercise `reserve(dry_run=False)`, `cancel_unpaid_hold(dry_run=False)`,
and the double-gated `KorailHttpClient.post_mutation_form` against an
`httpx.MockTransport` that records requests and returns synthetic envelopes.
No real network, no real credentials, no real card. They prove that a live
mutation goes ONLY to the evidenced mutation route, only with a non-dry-run
consent that opts into the category, and that the read-only path still refuses
every mutation route.
"""

from __future__ import annotations

import dataclasses

import httpx
import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    CardPayment,
    KorailClient,
    KorailConfig,
    KorailProtocolError,
    KorailSession,
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    ReservationHoldResponse,
    ReservationPaymentResponse,
    TrainSummary,
)
from korail_mobile_api.mutation_payloads import (
    build_single_adult_reservation_form,
)

RESERVE_ROUTE = "/classes/com.korail.mobile.certification.TicketReservation"
CANCEL_ROUTE = (
    "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk"
)
PAYMENT_ROUTE = "/classes/com.korail.mobile.payment.ReservationPayment"

# Synthetic, non-secret placeholders.
SYNTHETIC_PNR = "SYNTHETIC_PNR_REFERENCE"

_HOLD_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRR000000",
    "h_msg_txt": "success",
    "h_pnr_no": SYNTHETIC_PNR,
    "h_jrny_cnt": "1",
    "h_wct_no": "SYNTHETIC_WINDOW",
    "h_tmp_job_sqno1": "SYNTHETIC_JOB_1",
    "h_tmp_job_sqno2": "SYNTHETIC_JOB_2",
    "h_payment_flg": "Y",
    "h_tot_prc": "8400",
}

_CANCEL_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRP000000",
    "h_msg_txt": "cancelled",
}


def _eligible_train() -> TrainSummary:
    return TrainSummary(
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


class _Recorder:
    """A MockTransport handler that records requests and replies by path."""

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


def _live(**allow: bool) -> MutationConsent:
    return MutationConsent(dry_run=False, **allow)


# --- reserve(dry_run=False) live send --------------------------------------


def test_reserve_live_posts_to_reservation_route_and_returns_hold():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    hold = client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert isinstance(hold, ReservationHoldResponse)
    assert hold.str_result == "SUCC"
    assert hold.pnr_no == SYNTHETIC_PNR
    assert hold.journey_count == "1"
    # Exactly one request, and it went to the mutation route via POST.
    assert len(recorder.requests) == 1
    assert recorder.requests[0].method == "POST"
    assert recorder.requests[0].url.path == RESERVE_ROUTE


def test_reserve_live_still_requires_matching_consent():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    # dry_run=False but no allow_reserve: denied before any send.
    with pytest.raises(MutationNotAllowedError):
        client.reserve(_eligible_train(), consent=_live(allow_cancel=True))
    assert recorder.requests == []


def test_reserve_live_raises_app_error_on_fail_envelope_and_holds_nothing():
    client, recorder = _client_with(
        {
            RESERVE_ROUTE: {
                "strResult": "FAIL",
                "h_msg_cd": "WRC000288",
                "h_msg_txt": "no seat",
            }
        }
    )
    from korail_mobile_api import KorailAppError

    with pytest.raises(KorailAppError):
        client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert len(recorder.requests) == 1


# --- cancel_unpaid_hold ------------------------------------------------------


def _hold() -> ReservationHoldResponse:
    from korail_mobile_api.mutation_parsers import (
        parse_reservation_hold_response,
    )

    return parse_reservation_hold_response(dict(_HOLD_SUCCESS))


def test_cancel_dry_run_returns_redacted_preview_without_sending():
    client, recorder = _client_with({})
    preview = client.cancel_unpaid_hold(
        _hold(), consent=MutationConsent(allow_cancel=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "cancel"
    assert preview.route == CANCEL_ROUTE
    # PNR is redacted in the preview payload; nothing was sent.
    assert preview.payload["txtPnrNo"] == "[REDACTED]"
    assert recorder.requests == []


def test_cancel_live_posts_to_cancel_route():
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    result = client.cancel_unpaid_hold(_hold(), consent=_live(allow_cancel=True))
    assert isinstance(result, BaseKorailResponse)
    assert result.str_result == "SUCC"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == CANCEL_ROUTE


def test_cancel_requires_matching_consent_and_session():
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    with pytest.raises(MutationNotAllowedError):
        client.cancel_unpaid_hold(_hold(), consent=MutationConsent())
    assert recorder.requests == []

    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({CANCEL_ROUTE: _CANCEL_SUCCESS}))
    )
    from korail_mobile_api import KorailAuthError

    with pytest.raises(KorailAuthError):
        logged_out.cancel_unpaid_hold(
            _hold(), consent=_live(allow_cancel=True)
        )


# --- post_mutation_form double-gate -----------------------------------------


def test_post_mutation_form_refuses_a_non_mutation_route():
    client, recorder = _client_with({})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    # A read route (or any non-mutation route) is rejected by assert_mutation_route.
    with pytest.raises(KorailProtocolError):
        client.http.post_mutation_form(
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            form,
            consent=_live(allow_reserve=True),
            category="reserve",
        )
    assert recorder.requests == []


def test_post_mutation_form_refuses_none_and_unknown_category():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    with pytest.raises(MutationNotAllowedError):
        client.http.post_mutation_form(
            RESERVE_ROUTE, form, consent=None, category="reserve"  # type: ignore[arg-type]
        )
    with pytest.raises(MutationNotAllowedError):
        client.http.post_mutation_form(
            RESERVE_ROUTE,
            form,
            consent=_live(allow_reserve=True),
            category="checkin",
        )
    assert recorder.requests == []


def test_reserve_returns_cancelable_hold_even_if_optional_field_malformed():
    # The server created a real hold (PNR present) but an unrelated optional
    # field is malformed, so strict parsing would raise. reserve must still
    # return a hold carrying the PNR + journey count so it can be auto-cancelled.
    malformed = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        "h_msg_txt": "success",
        "h_pnr_no": SYNTHETIC_PNR,
        "h_jrny_cnt": "1",
        "h_tot_prc": 8400,  # int, not a string -> strict parser raises
    }
    client, recorder = _client_with({RESERVE_ROUTE: malformed})
    hold = client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert isinstance(hold, ReservationHoldResponse)
    assert hold.pnr_no == SYNTHETIC_PNR
    assert hold.journey_count == "1"
    assert hold.str_result == "SUCC"
    # And that recovered hold is acceptable to cancel_unpaid_hold.
    client2, recorder2 = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    result = client2.cancel_unpaid_hold(hold, consent=_live(allow_cancel=True))
    assert result.str_result == "SUCC"


def test_reserve_reraises_when_no_pnr_returned():
    # A malformed response with NO PNR means no hold to orphan: re-raise.
    no_pnr = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        "h_tot_prc": 8400,  # triggers strict-parse failure; no h_pnr_no present
    }
    client, _ = _client_with({RESERVE_ROUTE: no_pnr})
    with pytest.raises(KorailProtocolError):
        client.reserve(_eligible_train(), consent=_live(allow_reserve=True))


def test_post_mutation_form_rejects_category_route_mismatch():
    # A consent/category for one route cannot be used to POST another route.
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    with pytest.raises(KorailProtocolError):
        client.http.post_mutation_form(
            CANCEL_ROUTE,  # cancel route ...
            form,
            consent=_live(allow_reserve=True),
            category="reserve",  # ... but a reserve category
        )
    assert recorder.requests == []


def _paid_hold() -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd="IRR000018",
        str_result="SUCC",
        raw={},
        pnr_no=SYNTHETIC_PNR,
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        total_price="8400",
    )


def _fake_card() -> CardPayment:
    return CardPayment(
        card_number="0000000000000000",
        card_password="00",
        card_expire="2612",
        birthday="900101",
    )


_PAYMENT_DECLINE = {
    "strResult": "FAIL",
    "h_msg_cd": "WRC000123",
    "h_msg_txt": "card declined",
}


def test_pay_dry_run_preview_redacts_card_and_sends_nothing():
    client, recorder = _client_with({})
    preview = client.pay_with_fake_card(
        _paid_hold(), _fake_card(), consent=MutationConsent(allow_payment=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "payment"
    assert preview.route == PAYMENT_ROUTE
    # Raw PAN and card secrets are never present in the preview.
    assert preview.payload["hidStlCrCrdNo1"] == "[REDACTED]"
    assert preview.payload["hidVanPwd1"] == "[REDACTED]"
    assert preview.payload["hidAthnVal1"] == "[REDACTED]"
    assert preview.payload["hidPnrNo"] == "[REDACTED]"
    assert "0000000000000000" not in "".join(preview.payload.values())
    assert recorder.requests == []


def test_pay_live_posts_to_payment_route_and_returns_decline_without_raising():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_DECLINE})
    result = client.pay_with_fake_card(
        _paid_hold(),
        _fake_card(),
        consent=MutationConsent(allow_payment=True, dry_run=False),
    )
    # A decline is a FAIL envelope; pay must NOT raise, so the caller sees it.
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "FAIL"
    assert result.h_msg_cd == "WRC000123"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == PAYMENT_ROUTE


def test_pay_requires_payment_consent_and_refuses_real_card_mode():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_DECLINE})
    # Wrong category consent -> denied.
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(allow_reserve=True, dry_run=False),
        )
    # payment allowed but fake_card_only disabled -> refused (no real cards).
    with pytest.raises(MutationNotAllowedError):
        client.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(
                allow_payment=True, dry_run=False, fake_card_only=False
            ),
        )
    assert recorder.requests == []


def test_pay_requires_authenticated_session():
    from korail_mobile_api import KorailAuthError

    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({PAYMENT_ROUTE: _PAYMENT_DECLINE}))
    )
    with pytest.raises(KorailAuthError):
        logged_out.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(allow_payment=True, dry_run=False),
        )


def test_read_only_post_form_still_refuses_mutation_routes():
    # The enduring guarantee: the read-only send path rejects mutation routes,
    # so a mutation can only ever leave through post_mutation_form.
    client, _ = _client_with({})
    for route in (RESERVE_ROUTE, CANCEL_ROUTE, PAYMENT_ROUTE):
        with pytest.raises(KorailProtocolError):
            client.http.post_form(route, {"x": "1"})


# --- reserve -> auto-cancel round trip (offline model of the live flow) ------


def test_reserve_then_auto_cancel_round_trip_offline():
    client, recorder = _client_with(
        {RESERVE_ROUTE: _HOLD_SUCCESS, CANCEL_ROUTE: _CANCEL_SUCCESS}
    )
    consent = _live(allow_reserve=True, allow_cancel=True)
    hold = client.reserve(_eligible_train(), consent=consent)
    assert isinstance(hold, ReservationHoldResponse)
    cancel = client.cancel_unpaid_hold(hold, consent=consent)
    assert cancel.str_result == "SUCC"
    assert [r.url.path for r in recorder.requests] == [
        RESERVE_ROUTE,
        CANCEL_ROUTE,
    ]
