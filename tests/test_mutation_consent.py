"""Offline tests for the mutation safety-model foundation.

These cover the consent gate, the safe-by-default consent/preview types, the
payload redaction guarantee, and the route tiering. They deliberately assert
that NO callable mutation capability exists yet: the infrastructure only
classifies and gates: it never sends.
"""

from __future__ import annotations

import dataclasses

import pytest

import korail_mobile_api
from korail_mobile_api import (
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    require_mutation_consent,
)
from korail_mobile_api.errors import KorailApiError
from korail_mobile_api.redaction import redact_payload
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
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


def test_mutation_consent_is_frozen():
    consent = MutationConsent()
    with pytest.raises(dataclasses.FrozenInstanceError):
        consent.allow_payment = True  # type: ignore[misc]


# --- Consent gating -----------------------------------------------------------


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_rejects_none_consent(category):
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(None, category)


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_rejects_category_not_allowed(category):
    # A consent that opts into every OTHER category must still deny this one.
    other_flags = {
        f"allow_{name}": True for name in CATEGORIES if name != category
    }
    consent = MutationConsent(**other_flags)
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(consent, category)


@pytest.mark.parametrize("category", CATEGORIES)
def test_require_mutation_consent_allows_matching_category_returns_none(
    category,
):
    assert require_mutation_consent(_allow(category), category) is None


def test_require_mutation_consent_rejects_unknown_category():
    with pytest.raises(MutationNotAllowedError):
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
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(object(), "reserve")  # type: ignore[arg-type]


def test_mutation_not_allowed_error_is_a_korail_api_error():
    assert issubclass(MutationNotAllowedError, KorailApiError)


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


def test_no_callable_client_method_can_send_a_mutation():
    # The safety foundation must not add any state-changing client method.
    method_names = {
        name for name in dir(korail_mobile_api.KorailClient)
        if not name.startswith("_")
    }
    for verb in ("reserve", "pay", "payment", "cancel", "refund"):
        assert not any(verb in name for name in method_names), (
            f"unexpected mutation-shaped client method containing {verb!r}"
        )
