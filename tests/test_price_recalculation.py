from __future__ import annotations

from pathlib import Path

import pytest

import korail_mobile_api
from korail_mobile_api.consent import (
    MUTATION_CATEGORIES,
    MutationConsent,
    require_mutation_consent,
)
from korail_mobile_api.errors import MutationNotAllowedError
from korail_mobile_api.safety import (
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


ROUTE = "/classes/com.korail.mobile.certification.PriceReCalculation"

OTHER_CATEGORIES = ("reserve", "payment", "cancel", "refund", "discount_card")
OTHER_FLAGS = (
    "allow_reserve",
    "allow_payment",
    "allow_cancel",
    "allow_refund",
    "allow_discount_card",
)


def test_price_recalculation_is_its_own_consent_category():
    assert "price_recalculation" in MUTATION_CATEGORIES
    assert len(MUTATION_CATEGORIES) == 6
    # A default consent grants it no more than it grants anything else.
    assert MutationConsent().allow_price_recalculation is False
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(MutationConsent(), "price_recalculation")
    # ...and no other category's opt-in unlocks it. allow_payment is the one
    # that matters most: a consent to settle a quoted amount must not also
    # authorise rewriting what that amount is.
    for other in OTHER_FLAGS:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(**{other: True}),
                "price_recalculation",
            )
    require_mutation_consent(
        MutationConsent(allow_price_recalculation=True),
        "price_recalculation",
    )
    # ...and it unlocks nothing else.
    for category in OTHER_CATEGORIES:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(allow_price_recalculation=True),
                category,
            )


def test_route_is_a_mutation_route_owned_by_that_category():
    assert ("POST", ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("GET", ROUTE) not in KORAIL_MUTATION_ROUTES
    assert len(KORAIL_MUTATION_ROUTES) == 8
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[ROUTE] == "price_recalculation"
    assert_mutation_route("POST", ROUTE)
    assert_mutation_route_category(ROUTE, "price_recalculation")
    # A consent for another category can never be redirected onto this route.
    for wrong in OTHER_CATEGORIES:
        with pytest.raises(Exception):
            assert_mutation_route_category(ROUTE, wrong)
    # The read-only guarantee stays intact.
    assert ("POST", ROUTE) not in KORAIL_READ_ONLY_ROUTES
    with pytest.raises(Exception):
        assert_read_only_route("POST", ROUTE)


def test_category_carries_no_card_and_never_reaches_the_card_gate():
    # The form has no PAN: its fourteen @Fields are a PNR, a job id, a member
    # flag/number, a row count and six code/number lists
    # (CertificationService.java:35-37). It must therefore NOT be registered
    # as card-bearing, or the payment gate would demand a card kind it has no
    # card for.
    assert "price_recalculation" not in KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    assert KORAIL_CARD_BEARING_MUTATION_CATEGORIES <= set(MUTATION_CATEGORIES)


def test_no_live_path_reaches_this_category():
    root = Path(korail_mobile_api.__file__).parents[2]
    for relative in (
        "src/korail_mobile_api/live.py",
        "tests/test_live.py",
        "tests/test_live_service.py",
        "tests/test_mutation_live_paths.py",
        "scripts/reserve_pay_refund_roundtrip.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        for name in (
            "recalculate_price",
            "allow_price_recalculation",
            "PriceReCalculation",
        ):
            assert name not in source, f"{relative} reaches {name}"
