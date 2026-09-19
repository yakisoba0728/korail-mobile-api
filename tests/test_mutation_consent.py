# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Offline tests for the mutation safety model.

These cover the consent gate, the safe-by-default consent and preview types,
the payload redaction guarantee and the route tiering, and then reserve()
behind them: refused without its consent or a session, a redacted preview
under the default dry run, and post_mutation_form refusing a dry-run consent
outright. Nothing here sends: every client's transport fails the test.
"""

from __future__ import annotations

import dataclasses

import pytest

from _helpers import logged_in_no_network_client as _logged_in_no_network_client
from _helpers import no_network_client as _no_network_client
from _mutation_fixtures import eligible_train as _eligible_train
from korail_mobile_api import (
    KorailMutationNotAllowedError,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailSeatClass,
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from korail_mobile_api.errors import KorailApiError, KorailAuthError
from korail_mobile_api.mutation_payloads import (
    build_single_adult_reservation_form,
)
from korail_mobile_api.redaction import redact_payload
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_route,
)


CATEGORIES = ("reserve", "payment", "cancel", "refund")

# Obviously-fake, non-chargeable placeholders. No real card / credential.
FAKE_CARD_NUMBER = "0000000000000000"
FAKE_PNR = "SYNTHETIC_PNR_REFERENCE"


def _allow(category: str) -> MutationConsent:
    return MutationConsent(**{f"allow_{category}": True})


# --- MutationConsent defaults -------------------------------------------------


def test_mutation_consent_defaults_are_safe():
    consent = MutationConsent()
    assert consent.allow_reserve is False
    assert consent.allow_payment is False
    assert consent.allow_cancel is False
    assert consent.allow_refund is False
    assert consent.dry_run is True
    assert consent.fake_card_only is True
    # A real, chargeable card is never the default: it has to be acknowledged.
    assert consent.real_card_acknowledged is False


def test_mutation_consent_is_frozen():
    consent = MutationConsent()
    with pytest.raises(dataclasses.FrozenInstanceError):
        consent.allow_payment = True  # type: ignore[misc]


# --- Consent gating -----------------------------------------------------------


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_rejects_none_consent(category):
    with pytest.raises(KorailMutationNotAllowedError):
        require_mutation_consent(None, category)


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_rejects_category_not_allowed(category):
    # A consent that opts into every OTHER category must still deny this one.
    other_flags = {
        f"allow_{name}": True for name in CATEGORIES if name != category
    }
    consent = MutationConsent(**other_flags)
    with pytest.raises(KorailMutationNotAllowedError):
        require_mutation_consent(consent, category)


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_allows_matching_category_returns_none(
    category,
):
    assert require_mutation_consent(_allow(category), category) is None


def test_require_mutation_consent_rejects_unknown_category():
    with pytest.raises(KorailMutationNotAllowedError):
        require_mutation_consent(
            MutationConsent(
                allow_reserve=True,
                allow_payment=True,
                allow_cancel=True,
                allow_refund=True,
            ),
            "checkin",
        )


def test_require_mutation_consent_rejects_non_consent_object():
    with pytest.raises(KorailMutationNotAllowedError):
        require_mutation_consent(object(), "reserve")  # type: ignore[arg-type]


def test_mutation_not_allowed_error_is_a_korail_api_error():
    assert issubclass(KorailMutationNotAllowedError, KorailApiError)


# --- MutationPreview construction + redaction ---------------------------------


def test_mutation_preview_has_safe_default_note_and_fields():
    preview = MutationPreview(
        category="reserve",
        method="POST",
        route="/classes/com.korail.mobile.certification.TicketReservation",
        payload={"txtMenuId": "11"},
    )
    assert preview.category == "reserve"
    assert preview.method == "POST"
    assert preview.route.endswith("TicketReservation")
    assert preview.note == "dry-run: not sent"
    assert preview.payload == {"txtMenuId": "11"}


def test_mutation_preview_payload_is_redacted_masking_card_values():
    preview = MutationPreview(
        category="payment",
        method="POST",
        route="/classes/com.korail.mobile.payment.ReservationPayment",
        payload={
            "hidStlCrCrdNo1": FAKE_CARD_NUMBER,
            "hidVanPwd1": "00",
            "hidCrdVlidTrm1": "9912",
            "hidAthnVal1": "000000",
            "txtPnrNo": FAKE_PNR,
            "hidWctNo": "0000",
        },
    )
    # Card and PNR fields are masked; the raw card number never survives.
    assert preview.payload["hidStlCrCrdNo1"] == "[REDACTED]"
    assert preview.payload["hidVanPwd1"] == "[REDACTED]"
    assert preview.payload["hidCrdVlidTrm1"] == "[REDACTED]"
    assert preview.payload["hidAthnVal1"] == "[REDACTED]"
    assert preview.payload["txtPnrNo"] == "[REDACTED]"
    assert FAKE_CARD_NUMBER not in "".join(preview.payload.values())
    assert FAKE_PNR not in "".join(preview.payload.values())


def test_redact_payload_masks_bare_card_shaped_value_under_any_key():
    redacted = redact_payload({"someKey": "4111 1111 1111 1111"})
    assert "4111" not in redacted["someKey"]
    assert "[REDACTED_CARD]" in redacted["someKey"]


def test_mutation_preview_is_frozen():
    preview = MutationPreview(
        category="cancel",
        method="POST",
        route="/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
        payload={},
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        preview.note = "sent"  # type: ignore[misc]


# --- Route tiering ------------------------------------------------------------


def test_mutation_routes_are_classified_but_not_read_only():
    expected = {
        ("POST", "/classes/com.korail.mobile.certification.TicketReservation"),
        ("POST", "/classes/com.korail.mobile.payment.ReservationPayment"),
        (
            "POST",
            "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
        ),
        ("POST", "/classes/com.korail.mobile.refunds.RefundsRequest"),
    }
    assert expected <= KORAIL_MUTATION_ROUTES
    # The read-only guarantee stays intact: no mutation route leaked into it.
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    for route in expected:
        assert route not in KORAIL_READ_ONLY_ROUTES


# --- reserve(): consent-gated, dry-run, never sends -------------------------


def test_reserve_denied_without_matching_consent_and_sends_nothing():
    client = _logged_in_no_network_client()
    train = _eligible_train()
    # Default consent opts into nothing; None is also denied. Neither sends.
    with pytest.raises(KorailMutationNotAllowedError):
        client.reserve(train, consent=MutationConsent())
    with pytest.raises(KorailMutationNotAllowedError):
        client.reserve(train, consent=None)  # type: ignore[arg-type]


def test_reserve_dry_run_returns_preview_without_sending():
    client = _logged_in_no_network_client()
    preview = client.reserve(
        _eligible_train(), consent=MutationConsent(allow_reserve=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "reserve"
    assert preview.method == "POST"
    assert preview.route.endswith("certification.TicketReservation")
    assert preview.note == "dry-run: not sent"
    # The preview carries the exact form that WOULD be posted (built, not sent).
    assert preview.payload["txtMenuId"] == "11"
    assert preview.payload["txtJobId"] == "1101"
    assert preview.payload["txtTotPsgCnt"] == "1"


def test_post_mutation_form_refuses_a_dry_run_consent():
    # The send boundary itself refuses to transmit a dry-run consent, so a
    # preview can never reach the network even via the low-level send path.
    from korail_mobile_api import KorailConfig

    client = _no_network_client()
    route = "/classes/com.korail.mobile.certification.TicketReservation"
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    # dry_run defaults to True; the guard fires before any network use.
    with pytest.raises(KorailMutationNotAllowedError):
        client.http.post_mutation_form(
            route,
            form,
            consent=MutationConsent(allow_reserve=True),
            category="reserve",
        )


def test_reserve_requires_authenticated_session():
    client = _no_network_client()  # no session established
    with pytest.raises(KorailAuthError):
        client.reserve(
            _eligible_train(), consent=MutationConsent(allow_reserve=True)
        )


def test_reserve_rejects_a_train_without_an_available_general_seat():
    client = _logged_in_no_network_client()
    unavailable = dataclasses.replace(
        _eligible_train(), general_reservation_code="00"
    )
    with pytest.raises(KorailProtocolError):
        client.reserve(
            unavailable, consent=MutationConsent(allow_reserve=True)
        )


def test_reserve_previews_a_passenger_mix_and_a_special_cabin():
    client = _logged_in_no_network_client()
    train = dataclasses.replace(_eligible_train(), special_reservation_code="11")

    preview = client.reserve(
        train,
        consent=MutationConsent(allow_reserve=True),
        passengers=KorailPassengerCounts(adult=2, child=1, senior=1),
        seat_class=KorailSeatClass.SPECIAL,
    )

    assert isinstance(preview, MutationPreview)
    assert preview.payload["txtTotPsgCnt"] == "4"
    assert preview.payload["txtCompaCnt1"] == "2"  # 어른
    assert preview.payload["txtCompaCnt2"] == "1"  # 어린이
    assert preview.payload["txtCompaCnt3"] == "1"  # 경로
    assert "txtCompaCnt4" not in preview.payload
    assert preview.payload["txtPsrmClCd1"] == "2"  # 특실


def test_reserve_without_a_mix_still_previews_the_single_adult_form():
    client = _logged_in_no_network_client()
    train = _eligible_train()

    preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
    explicit = client.reserve(
        train,
        consent=MutationConsent(allow_reserve=True),
        passengers=KorailPassengerCounts(),
        seat_class=KorailSeatClass.GENERAL,
    )

    assert isinstance(preview, MutationPreview)
    assert isinstance(explicit, MutationPreview)
    assert preview.payload == explicit.payload
    assert preview.payload == build_single_adult_reservation_form(
        client.config, train
    )


def test_reserve_rejects_a_special_cabin_that_is_not_available():
    client = _logged_in_no_network_client()
    # General seats free, suite sold out (a5/u.java:319 reads h_spe_rsv_cd for
    # the suite tab).
    train = dataclasses.replace(_eligible_train(), special_reservation_code="13")

    with pytest.raises(KorailProtocolError):
        client.reserve(
            train,
            consent=MutationConsent(allow_reserve=True),
            seat_class=KorailSeatClass.SPECIAL,
        )


def test_reserve_refuses_an_over_large_mix_before_building_anything():
    # KorailPassengerCounts itself refuses, so an over-large mix cannot even be
    # spelled, let alone previewed or sent.
    with pytest.raises(ValueError):
        KorailPassengerCounts(adult=9, infant=1)


def test_http_layer_still_refuses_every_mutation_route_post():
    # The enduring network guarantee: no code path can POST a mutation route,
    # because it is not in the read-only allowlist. This holds regardless of
    # the (dry-run-only) reserve() method above.
    for method, path in KORAIL_MUTATION_ROUTES:
        with pytest.raises(KorailProtocolError):
            assert_read_only_route(method, path)
