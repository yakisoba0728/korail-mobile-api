# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""7.0.6 신규 계약의 실제 요청 형태와 상태변경 경계."""

from __future__ import annotations

from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import KorailClient
from korail_mobile_api.errors import KorailMutationNotAllowedError, KorailProtocolError
from korail_mobile_api.v7 import V7_CONTRACTS, V7MutationConsent, V7MutationPreview


def test_all_annotated_additions_are_registered() -> None:
    assert len(V7_CONTRACTS) == 117
    assert len({(item.http, item.route) for item in V7_CONTRACTS.values()}) == 112
    assert all(item.route and not item.route.startswith("//")
               for item in V7_CONTRACTS.values())
    assert all(item.request_model for item in V7_CONTRACTS.values()
               if "Body" in item.params)


def test_main_read_uses_exact_query_and_existing_session() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"strResult": "SUCCESS", "version": "7"})

    client = KorailClient(transport=httpx.MockTransport(respond))
    client.http.cookies.set("JSESSIONID", "test-session", domain="smart.letskorail.com")
    response = client.v7.call("NetworkApi.getSearchMetaData", {"version": "7"})
    assert response.raw["version"] == "7"
    assert requests[0].method == "GET"
    assert requests[0].url.path == "/classes/com.korail.mobile.goods.meta.do"
    assert dict(requests[0].url.params) == {"version": "7"}
    assert requests[0].headers["cookie"] == "JSESSIONID=test-session"
    client.v7.call("NetworkApi.getSearchMetaData", {})
    assert dict(requests[1].url.params) == {}
    client.close()


def test_mutating_get_requires_exact_method_consent_and_dry_run_never_sends() -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"strResult": "SUCCESS"})

    client = KorailClient(transport=httpx.MockTransport(respond))
    with pytest.raises(KorailMutationNotAllowedError):
        client.v7.call(
            "NetworkApi.productCancel",
            {"txtVrRsNo": "reservation", "txtGdSqno": "product"},
        )
    consent = V7MutationConsent(allow_methods=frozenset({"NetworkApi.productCancel"}))
    preview = client.v7.call(
        "NetworkApi.productCancel",
        {"txtVrRsNo": "reservation", "txtGdSqno": "product"},
        consent=consent,
    )
    assert isinstance(preview, V7MutationPreview)
    assert preview.payload["txtVrRsNo"] == "[REDACTED]"
    assert V7_CONTRACTS["NetworkApi.productCancel"].effect == "mutation"
    assert calls == 0
    with pytest.raises(KorailProtocolError):
        V7MutationConsent(allow_methods=frozenset({"NetworkApi.getSearchMetaData"}))
    client.close()


def test_product_cancel_accepts_only_apk_dto_keys_and_two_identifiers() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"strResult": "SUCCESS"})

    client = KorailClient(transport=httpx.MockTransport(respond))
    consent = V7MutationConsent(
        allow_methods=frozenset({"NetworkApi.productCancel"}), dry_run=False
    )
    try:
        for invalid in (
            {},
            {"txtVrRsNo": "reservation"},
            {"txtVrRsNo": "", "txtGdSqno": "product"},
            {"txtVrRsNo": "reservation", "txtGdSqno": "product", "pnrNo": "extra"},
        ):
            with pytest.raises(KorailProtocolError):
                client.v7.call("NetworkApi.productCancel", invalid, consent=consent)
        assert requests == []
        client.v7.call(
            "NetworkApi.productCancel",
            {"txtVrRsNo": "reservation", "txtGdSqno": "product", "lang": "ko"},
            consent=consent,
            include_common=True,
        )
    finally:
        client.close()
    assert len(requests) == 1
    assert requests[0].method == "GET"
    assert set(requests[0].url.params) == {
        "txtVrRsNo", "txtGdSqno", "lang", "Device", "Version", "Key"
    }


def test_auth_checkin_and_payment_status_are_never_unconsented_reads() -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"strResult": "SUCC"})

    names = (
        "NetworkApi.postDiscountCheck", "NetworkApi.postInquiryIsMember",
        "NetworkApi.postLPotAthn", "NetworkApi.postXPointView",
        "NetworkApi.postOkCashbagCertView", "NetworkApi.postSelfCheckInInfo",
        "NetworkApi.postSelfCheckInPossible",
        "NetworkApi.postLocalRailwayTravelQrAuth",
        "NetworkApi.postMemberVerify", "NetworkApi.paymentMassStatusIn",
    )
    client = KorailClient(transport=httpx.MockTransport(respond))
    for name in names:
        assert V7_CONTRACTS[name].effect == "mutation"
        with pytest.raises(KorailMutationNotAllowedError):
            client.v7.call(name, {})
        preview = client.v7.call(
            name, {}, consent=V7MutationConsent(allow_methods=frozenset({name}))
        )
        assert isinstance(preview, V7MutationPreview)
    assert calls == 0
    client.close()


def test_repeated_field_and_partner_origin_are_separate() -> None:
    main: list[httpx.Request] = []
    partner: list[httpx.Request] = []

    def main_respond(request: httpx.Request) -> httpx.Response:
        main.append(request)
        return httpx.Response(200, json={"strResult": "SUCCESS"})

    def partner_respond(request: httpx.Request) -> httpx.Response:
        partner.append(request)
        return httpx.Response(200, json={"items": []})

    client = KorailClient(
        transport=httpx.MockTransport(main_respond),
        partner_origins={"GreenCarNetworkApi": "https://partner.example"},
        partner_transport=httpx.MockTransport(partner_respond),
    )
    client.http.cookies.set("JSESSIONID", "main-only", domain="smart.letskorail.com")
    consent = V7MutationConsent(
        allow_methods=frozenset({"NetworkApi.postBuyConfirm"}), dry_run=False
    )
    client.v7.call(
        "NetworkApi.postBuyConfirm",
        {"addSrvReqNo": ["a", "b"], "jobDvCd": "Q"}, consent=consent,
    )
    assert parse_qs(main[0].content.decode()) == {
        "addSrvReqNo": ["a", "b"], "jobDvCd": ["Q"]
    }
    assert main[0].url.host == "smart.letskorail.com"
    client.v7.call(
        "GreenCarNetworkApi.getGreenCarItems",
        {"rsStnLng": "1", "rsStnLat": "2", "startDtm": "3",
         "endDtm": "4", "recView": "Y"},
    )
    assert partner[0].url.host == "partner.example"
    assert "cookie" not in partner[0].headers
    client.close()


def test_partner_clients_share_domain_scoped_cookie_jar_with_main() -> None:
    main: list[httpx.Request] = []
    partner: list[httpx.Request] = []
    unrelated: list[httpx.Request] = []

    def main_respond(request: httpx.Request) -> httpx.Response:
        main.append(request)
        headers = (
            [
                ("Set-Cookie", "shared=main; Domain=letskorail.com; Path=/; Secure"),
                ("Set-Cookie", "hostonly=main; Path=/; Secure"),
            ]
            if len(main) == 1 else []
        )
        return httpx.Response(200, headers=headers, json={"strResult": "SUCCESS"})

    def partner_respond(request: httpx.Request) -> httpx.Response:
        if request.url.host == "cookie-partner.letskorail.com":
            partner.append(request)
            headers = (
                [("Set-Cookie", "frompartner=partner; Domain=letskorail.com; Path=/; Secure")]
                if len(partner) == 1 else []
            )
        else:
            unrelated.append(request)
            headers = (
                [("Set-Cookie", "isolated=parking; Domain=parking.example; Path=/; Secure")]
                if len(unrelated) == 1 else []
            )
        return httpx.Response(200, headers=headers, json={"items": []})

    client = KorailClient(
        transport=httpx.MockTransport(main_respond),
        partner_origins={
            "GreenCarNetworkApi": "https://cookie-partner.letskorail.com",
            "KNParkNetworkApi": "https://parking.example",
        },
        partner_transport=httpx.MockTransport(partner_respond),
    )
    try:
        def main_read() -> None:
            client.v7.call("NetworkApi.getSearchMetaData", {})

        def partner_read() -> None:
            client.v7.call("GreenCarNetworkApi.getGreenCarCount", {})

        def unrelated_read() -> None:
            client.v7.call("KNParkNetworkApi.getParkingCount", {})
        main_read()
        partner_read()
        main_read()
        unrelated_read()
        partner_read()
        main_read()
    finally:
        client.close()

    assert "shared=main" in partner[0].headers.get("cookie", "")
    assert "hostonly=main" not in partner[0].headers.get("cookie", "")
    assert "frompartner=partner" in main[1].headers.get("cookie", "")
    assert "hostonly=main" in main[1].headers.get("cookie", "")
    assert "shared=main" not in unrelated[0].headers.get("cookie", "")
    assert "frompartner=partner" not in unrelated[0].headers.get("cookie", "")
    assert "isolated=parking" not in partner[1].headers.get("cookie", "")
    assert "isolated=parking" not in main[2].headers.get("cookie", "")


def test_partner_host_and_unknown_wire_fields_fail_before_request() -> None:
    with pytest.raises(KorailProtocolError):
        KorailClient(partner_origins={"KNParkNetworkApi": "http://park.example"})
    client = KorailClient()
    with pytest.raises(KorailProtocolError):
        client.v7.call("NetworkApi.getSearchMetaData", {"other": "7"})
    client.close()


def test_body_contracts_reject_incomplete_dto_shapes_before_io() -> None:
    seen: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    client = KorailClient(transport=httpx.MockTransport(respond))
    try:
        for name, values in (
            ("GreenCarNetworkApi.getGreenCarDetail", {}),
            ("GreenCarNetworkApi.getGreenCarDetail", {"addSrvReqNo": "A"}),
            ("NetworkApi.postCacheCheck", {}),
            ("NetworkApi.postCacheCheck", {"versions": {"station": 1}}),
        ):
            with pytest.raises(KorailProtocolError):
                client.v7.call(name, values)
    finally:
        client.close()
    assert seen == []


def test_push_web_host_uses_main_http_client_and_cookie_scope() -> None:
    main: list[httpx.Request] = []
    partner: list[httpx.Request] = []

    def main_respond(request: httpx.Request) -> httpx.Response:
        main.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    def partner_respond(request: httpx.Request) -> httpx.Response:
        partner.append(request)
        return httpx.Response(200, json={})

    client = KorailClient(
        transport=httpx.MockTransport(main_respond),
        partner_origins={"PushService": "https://smart.letskorail.com"},
        partner_transport=httpx.MockTransport(partner_respond),
    )
    client.http.cookies.set("JSESSIONID", "test-session", domain="smart.letskorail.com")
    consent = V7MutationConsent(
        allow_methods=frozenset({"PushService.pushUpdate"}), dry_run=False
    )
    try:
        client.v7.call(
            "PushService.pushUpdate", {"job_dv_cd": "U"}, consent=consent
        )
    finally:
        client.close()
    assert len(main) == 1 and partner == []
    assert main[0].method == "GET"
    assert main[0].url.path == "/classes/com.korail.mobile.push.update"
    assert main[0].headers["cookie"] == "JSESSIONID=test-session"


LOTTE_COUNT = "LotteRentalCarNetworkApi.getLotteRentalCarCount"


def _partner_client(seen: list[httpx.Request]) -> KorailClient:
    def refuse_main(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError(f"unexpected main-host request {request.url.path}")

    def partner(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"count": 0})

    return KorailClient(
        transport=httpx.MockTransport(refuse_main),
        partner_origins={"LotteRentalCarNetworkApi": "https://partner.example"},
        partner_transport=httpx.MockTransport(partner),
    )


def test_a_declared_header_reaches_the_partner_request() -> None:
    # @Header(Authentication) is this contract's only parameter.
    assert V7_CONTRACTS[LOTTE_COUNT].headers == {"Authentication"}
    seen: list[httpx.Request] = []
    client = _partner_client(seen)
    try:
        client.v7.call(LOTTE_COUNT, {}, headers={"Authentication": "Bearer synthetic"})
    finally:
        client.close()
    assert len(seen) == 1
    assert seen[0].url.host == "partner.example"
    assert seen[0].headers["authentication"] == "Bearer synthetic"


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Undeclared": "value"},
        {"Authentication": "Bearer synthetic", "X-Undeclared": "value"},
        {"Authentication": "Bearer synthetic\r\nX-Injected: 1"},
        {"Authentication": "Bearer synthetic\nX-Injected: 1"},
    ],
    ids=["undeclared", "declared-plus-undeclared", "crlf", "lf"],
)
def test_a_header_the_contract_does_not_declare_or_a_split_value_never_leaves(
    headers,
) -> None:
    # Only @Header names may be sent, and a value cannot smuggle a second
    # header in with a line break.
    seen: list[httpx.Request] = []
    client = _partner_client(seen)
    try:
        with pytest.raises(KorailProtocolError, match="header"):
            client.v7.call(LOTTE_COUNT, {}, headers=headers)
    finally:
        client.close()
    assert seen == []


SPAY_ORDER = "NetworkApi.postSpayOrdNo"


@pytest.mark.parametrize(
    ("fake_card_only", "real_card_acknowledged"),
    [(False, False), (True, True)],
    ids=["neither", "both"],
)
def test_a_card_bearing_v7_mutation_refuses_an_unstated_card_kind(
    fake_card_only, real_card_acknowledged
) -> None:
    # The V7 twin of post_mutation_form's card gate: exactly one card kind, or
    # nothing is sent -- and not even previewed.
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        calls.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    client = KorailClient(transport=httpx.MockTransport(respond))
    try:
        for dry_run in (False, True):
            consent = V7MutationConsent(
                allow_methods=frozenset({SPAY_ORDER}),
                dry_run=dry_run,
                fake_card_only=fake_card_only,
                real_card_acknowledged=real_card_acknowledged,
            )
            with pytest.raises(
                KorailMutationNotAllowedError, match="explicit card kind"
            ):
                client.v7.call(SPAY_ORDER, {"lumpStlTgtNo": "SYNTHETIC"}, consent=consent)
    finally:
        client.close()
    assert calls == []


def test_a_card_bearing_v7_mutation_with_one_card_kind_is_sent() -> None:
    calls: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200, json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": ""}
        )

    client = KorailClient(transport=httpx.MockTransport(respond))
    try:
        client.v7.call(
            SPAY_ORDER,
            {"lumpStlTgtNo": "SYNTHETIC"},
            consent=V7MutationConsent(
                allow_methods=frozenset({SPAY_ORDER}), dry_run=False
            ),
        )
    finally:
        client.close()
    assert len(calls) == 1
    assert calls[0].url.path == V7_CONTRACTS[SPAY_ORDER].route
    assert parse_qs(calls[0].content.decode()) == {"lumpStlTgtNo": ["SYNTHETIC"]}
