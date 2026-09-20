# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Offline tests for the ``cart`` mutation: adding a PNR to the 장바구니.

Model: ``tests/test_discount_card_mutations.py``. Same shape: route/category
cross-check and one acknowledged send against a ``MockTransport`` that
records what actually left the process.

``cart.addCartList`` (``CartService.java:11-13``) takes exactly one request
field beyond the common three -- ``hidPnrNo`` -- confirmed against
``AddCartDao.java:9-24`` and, independently, against
``AddCartDao$AddCartRequest.smali`` (the ``hidPnrNo`` field declaration) and
``CartService.smali`` (the ``@Field("hidPnrNo")`` annotation on ``addCart``
and the ``@POST("/classes/com.korail.mobile.cart.addCartList")`` route
annotation).
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from _helpers import make_authenticated_client as _client
from _helpers import refuse_transport as _refuse
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
)
from korail_mobile_api.models import BaseKorailResponse
from korail_mobile_api.mutation_models import CartAddRequest
from korail_mobile_api.mutation_payloads import build_cart_add_form
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


CART_ADD_ROUTE = "/classes/com.korail.mobile.cart.addCartList"

# Synthetic, non-secret placeholder -- never a real PNR.
SYNTHETIC_PNR = "SYNTHETIC_PNR_REFERENCE"


def _request(**overrides: object) -> CartAddRequest:
    fields: dict[str, object] = {"pnr_no": SYNTHETIC_PNR}
    fields.update(overrides)
    return CartAddRequest(**fields)  # type: ignore[arg-type]


# --- Route tiering: bidirectional route<->category binding ------------------


def test_route_is_a_mutation_route_owned_by_the_cart_category():
    assert ("POST", CART_ADD_ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("GET", CART_ADD_ROUTE) not in KORAIL_MUTATION_ROUTES
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    assert CART_ADD_ROUTE not in {path for _, path in KORAIL_READ_ONLY_ROUTES}

    assert KORAIL_MUTATION_ROUTE_CATEGORIES[CART_ADD_ROUTE] == "cart"
    assert_mutation_route_category(CART_ADD_ROUTE, "cart")
    for wrong in (
        "reserve",
        "payment",
        "cancel",
        "refund",
        "discount_card",
        "price_recalculation",
    ):
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(CART_ADD_ROUTE, wrong)

    # And the reverse: every OTHER route's category is never "cart".
    for path, category in KORAIL_MUTATION_ROUTE_CATEGORIES.items():
        if path != CART_ADD_ROUTE:
            assert category != "cart"

    assert_mutation_route("POST", CART_ADD_ROUTE)
    with pytest.raises(KorailProtocolError):
        assert_mutation_route("GET", CART_ADD_ROUTE)
    for method in ("GET", "POST"):
        with pytest.raises(KorailProtocolError):
            assert_read_only_route(method, CART_ADD_ROUTE)


def test_cart_route_deliberately_has_no_read_only_field_contract():
    # KORAIL_EXACT_REQUEST_FIELDS is the field allowlist for the READ-ONLY
    # send path (assert_read_only_request_fields, reached only from
    # post_form/get_json). A mutation route is refused by assert_read_only_
    # route before any field check runs, so it never needs -- and by this
    # repository's own convention deliberately does NOT get -- an entry
    # there. Mirrors the identical assertion for the refund mutation route
    # in test_reference_derived_reads.py and for the crew-call mutation
    # route in test_p0_menu_reads.py.
    assert CART_ADD_ROUTE not in KORAIL_EXACT_REQUEST_FIELDS


# --- Form contract ------------------------------------------------------------


def test_add_to_cart_form_matches_the_dao_field_contract():
    form = build_cart_add_form(KorailConfig(), _request())
    assert set(form) == {"Device", "Version", "Key", "hidPnrNo"}
    assert form["hidPnrNo"] == SYNTHETIC_PNR


@pytest.mark.parametrize(
    "overrides",
    [
        {"pnr_no": ""},
        {"pnr_no": "   "},
    ],
)
def test_add_to_cart_form_refuses_out_of_contract_requests(overrides):
    with pytest.raises(KorailProtocolError):
        build_cart_add_form(KorailConfig(), _request(**overrides))


def test_add_to_cart_form_refuses_a_non_exact_request_type():
    with pytest.raises(KorailProtocolError):
        build_cart_add_form(KorailConfig(), "not a request")  # type: ignore[arg-type]


# --- add_to_cart(): sends immediately once a session exists ----------------


def test_add_to_cart_requires_a_session():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.add_to_cart(_request())
    finally:
        client.close()


def test_an_acknowledged_send_transmits_exactly_the_built_shape():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "정상처리되었습니다",
                "strResult": "SUCC",
            },
        )

    client = _client(handler)
    try:
        result = client.add_to_cart(_request())
    finally:
        client.close()

    assert type(result) is BaseKorailResponse
    assert result.str_result == "SUCC"
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == CART_ADD_ROUTE
    sent = dict(parse_qsl(seen[0].read().decode(), keep_blank_values=True))
    assert sent == {
        "Device": KorailConfig().device,
        "Version": KorailConfig().version,
        "Key": KorailConfig().key,
        "hidPnrNo": SYNTHETIC_PNR,
    }


def test_no_live_path_reaches_this_category():
    # The live smoke runner must not gain a cart call: this category is
    # deliberately not live-enabled, and nothing in the repository's live or
    # scripted paths may send it.
    root = Path(korail_mobile_api.__file__).parents[2]
    # Every script, not one: each is an operator tool that talks to the live
    # server, and any of them could gain a call.
    scripts = sorted((root / "scripts").glob("*.py"))
    assert scripts, "no scripts found; the scan would pass on nothing"
    for path in (
        root / "src/korail_mobile_api/live.py",
        root / "tests/test_live.py",
        root / "tests/test_live_service.py",
        root / "tests/test_mutation_live_paths.py",
        *scripts,
    ):
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        for name in ("add_to_cart", "allow_cart"):
            assert name not in source, f"{relative} reaches {name}"


def test_public_surface_exports_the_cart_mutation_names():
    for name in ("CartAddRequest",):
        assert name in korail_mobile_api.__all__
        assert hasattr(korail_mobile_api, name)
