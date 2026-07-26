from __future__ import annotations

from pathlib import Path

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.consent import (
    MUTATION_CATEGORIES,
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from korail_mobile_api.constants import KORAIL_MAX_DISCOUNT_CARD_SECTIONS
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
    MutationNotAllowedError,
)
from korail_mobile_api.http import KorailHttpClient
from korail_mobile_api.models import KorailSession
from korail_mobile_api.mutation_models import (
    DiscountCardAdditionalUser,
    DiscountCardPurchaseRequest,
    DiscountCardPurchaseResponse,
    DiscountCardSectionRequest,
    DiscountCardTicket,
)
from korail_mobile_api.mutation_parsers import (
    parse_discount_card_purchase_response,
)
from korail_mobile_api.mutation_payloads import (
    build_discount_card_extension_query,
    build_discount_card_purchase_form,
)
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


PURCHASE_ROUTE = "/classes/com.korail.mobile.research.dcntCrdInfo.do"
EXTENSION_ROUTE = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"

ALLOWED = MutationConsent(allow_discount_card=True, dry_run=False)
DRY_RUN = MutationConsent(allow_discount_card=True)


def _section(index: int = 1) -> DiscountCardSectionRequest:
    return DiscountCardSectionRequest(
        run_date="20990101",
        train_no=f"0010{index}",
        departure_station_code="0001",
        arrival_station_code="0020",
    )


def _purchase(**overrides: object) -> DiscountCardPurchaseRequest:
    fields: dict[str, object] = {
        "card_kind_management_no": "B2N23100501",
        "customer_no": "SYNTHETIC_CUSTOMER_NO",
        "validity_start_date": "20990101",
        "usable_trip_count": "10",
        "sections": (_section(),),
    }
    fields.update(overrides)
    return DiscountCardPurchaseRequest(**fields)  # type: ignore[arg-type]


def _ticket() -> DiscountCardTicket:
    return DiscountCardTicket(
        sale_window_no="0001",
        sale_date="20990101",
        sale_sequence="0001",
        return_password="SYNTHETIC_PWD",
    )


def _client(handler) -> KorailClient:
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        customer_no="SYNTHETIC_CUSTOMER_NO",
        raw={},
    )
    return client


def _refuse(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"nothing may be sent: {request.method} {request.url}")


def test_discount_card_is_its_own_consent_category():
    assert "discount_card" in MUTATION_CATEGORIES
    assert len(MUTATION_CATEGORIES) == 6
    # A default consent grants it no more than it grants anything else.
    assert MutationConsent().allow_discount_card is False
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(MutationConsent(), "discount_card")
    # ...and no other category's opt-in unlocks it.
    for other in ("allow_reserve", "allow_payment", "allow_cancel", "allow_refund"):
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(**{other: True}),
                "discount_card",
            )
    require_mutation_consent(
        MutationConsent(allow_discount_card=True),
        "discount_card",
    )
    # ...and it unlocks nothing else.
    for category in ("reserve", "payment", "cancel", "refund"):
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(allow_discount_card=True),
                category,
            )


def test_both_routes_are_mutation_routes_owned_by_that_category():
    assert ("POST", PURCHASE_ROUTE) in KORAIL_MUTATION_ROUTES
    # Registered with the method the app actually uses, not coerced to POST.
    assert ("GET", EXTENSION_ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("POST", EXTENSION_ROUTE) not in KORAIL_MUTATION_ROUTES
    assert len(KORAIL_MUTATION_ROUTES) == 9
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    for route in (PURCHASE_ROUTE, EXTENSION_ROUTE):
        assert KORAIL_MUTATION_ROUTE_CATEGORIES[route] == "discount_card"
        assert_mutation_route_category(route, "discount_card")
        for wrong in ("reserve", "payment", "cancel", "refund"):
            with pytest.raises(KorailProtocolError):
                assert_mutation_route_category(route, wrong)
    with pytest.raises(KorailProtocolError):
        assert_mutation_route("POST", EXTENSION_ROUTE)
    for route in (PURCHASE_ROUTE, EXTENSION_ROUTE):
        for method in ("GET", "POST"):
            with pytest.raises(KorailProtocolError):
                assert_read_only_route(method, route)


def test_purchase_form_matches_the_dao_key_spellings():
    form = build_discount_card_purchase_form(KorailConfig(), _purchase())
    assert form["dcntCrdKndMgNo"] == "B2N23100501"
    assert form["custMgNo"] == "SYNTHETIC_CUSTOMER_NO"
    assert form["vlidTrmStDt"] == "20990101"
    assert form["usePsbTno"] == "10"
    # NCardReservationDao.java:74-108 -- the jrnyInfo map's indexed keys.
    assert form["jrnyCnt"] == "1"
    assert form["jrnyTpCd_1"] == "11"
    assert form["runDt_1"] == "20990101"
    assert form["trnNo_1"] == "00101"
    assert form["dptRsStnCd_1"] == "0001"
    assert form["arvRsStnCd_1"] == "0020"
    # A 1인용 card contributes no apdUsrInfo keys at all: the app's own map is
    # empty and Retrofit emits nothing for an empty @FieldMap.
    assert not any(name.startswith("apdUsr") for name in form)
    assert not any(name.startswith("apdCust") for name in form)
    assert not any(name.startswith("custMgNo_") for name in form)
    # mCustomData is never passed to executeDao (NCardReservationDao.java:180).
    assert not any("CUSTOM_STATION_INFO" in name for name in form)


def test_purchase_form_carries_a_second_registered_user():
    form = build_discount_card_purchase_form(
        KorailConfig(),
        _purchase(
            sections=(_section(1), _section(2)),
            additional_users=(
                DiscountCardAdditionalUser(
                    customer_no="SYNTHETIC_OTHER_CUSTOMER",
                    name="홍길동",
                    phone="01000000000",
                ),
            ),
        ),
    )
    assert form["jrnyCnt"] == "2"
    assert form["trnNo_2"] == "00102"
    assert form["apdUsrCnt"] == "1"
    assert form["custMgNo_1"] == "SYNTHETIC_OTHER_CUSTOMER"
    assert form["apdCustName_1"] == "홍길동"
    assert form["apdCustTeln_1"] == "01000000000"
    # custMgNo (the buyer) and custMgNo_1 (the second user) are different keys
    # and must not collide.
    assert form["custMgNo"] == "SYNTHETIC_CUSTOMER_NO"


@pytest.mark.parametrize(
    "overrides",
    [
        {"card_kind_management_no": ""},
        {"customer_no": " "},
        {"validity_start_date": ""},
        {"usable_trip_count": ""},
        {"sections": ()},
        {"sections": tuple(_section() for _ in range(4))},
        {"sections": ("not a section",)},
        {"additional_users": ("not a user",), "sections": (_section(),)},
    ],
)
def test_purchase_form_refuses_out_of_contract_requests(overrides):
    with pytest.raises(KorailProtocolError):
        build_discount_card_purchase_form(KorailConfig(), _purchase(**overrides))


def test_three_sections_is_the_apps_own_ceiling():
    assert KORAIL_MAX_DISCOUNT_CARD_SECTIONS == 3
    form = build_discount_card_purchase_form(
        KorailConfig(),
        _purchase(sections=tuple(_section(i) for i in range(1, 4))),
    )
    assert form["jrnyCnt"] == "3"
    assert "arvRsStnCd_3" in form
    assert "arvRsStnCd_4" not in form


def test_extension_query_is_the_card_tickets_own_credential():
    query = build_discount_card_extension_query(KorailConfig(), _ticket())
    assert set(query) == {
        "Device",
        "Version",
        "Key",
        "saleWctNo",
        "saleDd",
        "saleSqno",
        "tkRetPwd",
    }
    assert query["saleWctNo"] == "0001"
    assert query["saleDd"] == "20990101"
    assert query["saleSqno"] == "0001"
    assert query["tkRetPwd"] == "SYNTHETIC_PWD"
    with pytest.raises(KorailProtocolError):
        build_discount_card_extension_query(KorailConfig(), "not a ticket")
    with pytest.raises(KorailProtocolError):
        build_discount_card_extension_query(
            KorailConfig(),
            DiscountCardTicket(
                sale_window_no="0001",
                sale_date="20990101",
                sale_sequence="0001",
                return_password="",
            ),
        )


def test_default_consent_previews_and_sends_nothing():
    client = _client(_refuse)
    try:
        preview = client.register_discount_card(_purchase(), consent=DRY_RUN)
        assert type(preview) is MutationPreview
        assert preview.category == "discount_card"
        assert preview.method == "POST"
        assert preview.route == PURCHASE_ROUTE
        # custMgNo is PII and is redacted even in a preview that never left.
        assert "SYNTHETIC_CUSTOMER_NO" not in str(preview.payload)

        preview = client.extend_discount_card(_ticket(), consent=DRY_RUN)
        assert type(preview) is MutationPreview
        assert preview.method == "GET"
        assert preview.route == EXTENSION_ROUTE
        assert "SYNTHETIC_PWD" not in str(preview.payload)
    finally:
        client.close()


def test_methods_refuse_without_the_matching_consent():
    client = _client(_refuse)
    try:
        for consent in (
            None,
            MutationConsent(),
            MutationConsent(allow_reserve=True, dry_run=False),
            MutationConsent(allow_payment=True, dry_run=False),
        ):
            with pytest.raises(MutationNotAllowedError):
                client.register_discount_card(_purchase(), consent=consent)
            with pytest.raises(MutationNotAllowedError):
                client.extend_discount_card(_ticket(), consent=consent)
    finally:
        client.close()


def test_methods_require_a_session_even_with_consent():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.register_discount_card(_purchase(), consent=DRY_RUN)
        with pytest.raises(KorailAuthError):
            client.extend_discount_card(_ticket(), consent=DRY_RUN)
    finally:
        client.close()


def test_get_mutation_query_carries_every_gate_post_mutation_form_does():
    http = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        # No consent, wrong category, dry-run, wrong route, wrong method.
        with pytest.raises(MutationNotAllowedError):
            http.get_mutation_query(
                EXTENSION_ROUTE,
                {},
                consent=MutationConsent(),
                category="discount_card",
            )
        with pytest.raises(MutationNotAllowedError):
            http.get_mutation_query(
                EXTENSION_ROUTE,
                {},
                consent=DRY_RUN,
                category="discount_card",
            )
        with pytest.raises(KorailProtocolError):
            http.get_mutation_query(
                EXTENSION_ROUTE,
                {},
                consent=MutationConsent(allow_refund=True, dry_run=False),
                category="refund",
            )
        with pytest.raises(KorailProtocolError):
            http.get_mutation_query(
                "/classes/com.korail.mobile.common.stationdata",
                {},
                consent=ALLOWED,
                category="discount_card",
            )
        with pytest.raises(KorailProtocolError):
            http.get_mutation_query(
                PURCHASE_ROUTE,
                {},
                consent=ALLOWED,
                category="discount_card",
            )
        with pytest.raises(KorailProtocolError):
            http.get_mutation_query(
                EXTENSION_ROUTE,
                "not a mapping",
                consent=ALLOWED,
                category="discount_card",
            )
    finally:
        http.close()


def test_an_acknowledged_send_transmits_exactly_the_built_shapes():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == PURCHASE_ROUTE:
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "IRG000000",
                    "h_msg_txt": "정상처리되었습니다",
                    "strResult": "SUCC",
                    "lumpStlTgtNo": "SYNTHETIC_TARGET",
                    "rcvdAmt": "60000",
                    "usePsbTno": "10",
                    "vlidTrmStDt": "20990101",
                    "vlidTrmClsDt": "20990301",
                },
            )
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
        purchased = client.register_discount_card(
            _purchase(),
            consent=ALLOWED,
        )
        extended = client.extend_discount_card(_ticket(), consent=ALLOWED)
    finally:
        client.close()

    assert type(purchased) is DiscountCardPurchaseResponse
    assert purchased.lump_settlement_target_no == "SYNTHETIC_TARGET"
    assert purchased.received_amount == "60000"
    assert purchased.validity_end_date == "20990301"
    assert extended.str_result == "SUCC"
    assert [request.method for request in seen] == ["POST", "GET"]
    assert seen[0].url.path == PURCHASE_ROUTE
    assert seen[1].url.path == EXTENSION_ROUTE
    assert "tkRetPwd=SYNTHETIC_PWD" in str(seen[1].url)


def test_purchase_parser_reads_the_dao_shape():
    parsed = parse_discount_card_purchase_response(
        {
            "h_msg_cd": "IRG000000",
            "h_msg_txt": "정상처리되었습니다",
            "strResult": "SUCC",
            # The settlement target is the point of the call.
            "lumpStlTgtNo": "SYNTHETIC_TARGET",
            "rcvdAmt": 60000,
        }
    )
    assert parsed.lump_settlement_target_no == "SYNTHETIC_TARGET"
    assert parsed.received_amount == "60000"
    assert parsed.usable_trip_count is None
    assert "SYNTHETIC_TARGET" not in repr(parsed)
    with pytest.raises(KorailProtocolError):
        parse_discount_card_purchase_response("not a mapping")


def test_no_live_path_reaches_this_category():
    # The live smoke runner must not gain a discount-card call: this category
    # is deliberately not live-enabled, and nothing in the repository's live
    # or scripted paths may send it.
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
            "register_discount_card",
            "extend_discount_card",
            "allow_discount_card",
        ):
            assert name not in source, f"{relative} reaches {name}"


def test_public_surface_exports_the_mutation_names():
    for name in (
        "DiscountCardAdditionalUser",
        "DiscountCardPurchaseRequest",
        "DiscountCardPurchaseResponse",
        "DiscountCardSectionRequest",
        "DiscountCardTicket",
        "KORAIL_MAX_DISCOUNT_CARD_SECTIONS",
        "parse_discount_card_purchase_response",
    ):
        assert name in korail_mobile_api.__all__
        assert hasattr(korail_mobile_api, name)
