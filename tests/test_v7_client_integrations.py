# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Offline wire checks for newly connected 7.0.6 client flows."""

from urllib.parse import parse_qs, parse_qsl

import httpx

from korail_mobile_api import (
    KorailClient,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
    TrainSearchQuery,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.mutation_models import StationRefundExecutionResponse


def test_special_search_selects_apk_route_and_common_shape(load_json_fixture):
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == (
            "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"
        )
        return httpx.Response(200, json=load_json_fixture("schedule_view_success.json"))

    client = KorailClient(transport=httpx.MockTransport(respond))
    try:
        result = client.search_trains(
            TrainSearchQuery("서울", "부산", "20260710"),
            use_special_schedule=True,
        )
    finally:
        client.close()

    assert len(result.trains) > 0
    assert len(requests) == 1
    fields = parse_qs(requests[0].content.decode())
    assert fields["Key"] == [client.config.key]
    assert "Sid" not in fields
    assert fields["txtGoStart"] == ["서울"]
    assert fields["txtGoEnd"] == ["부산"]


def test_ticket_maas_menu_preserves_repeated_return_number_fields():
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"strResult": "SUCC", "h_msg_cd": "API.I00000", "menuList": []},
        )

    client = KorailClient(transport=httpx.MockTransport(respond))
    client.session.current = KorailSession(jsessionid="synthetic-session")
    try:
        result = client.get_maas_menu_list(
            pnr_no="synthetic-pnr",
            ticket_return_numbers=("return-one", "return-two"),
        )
    finally:
        client.close()

    assert result.items == ()
    assert requests[0].url.path == "/classes/com.korail.mobile.copt.gdMenuLt.do"
    pairs = parse_qsl(requests[0].content.decode())
    assert pairs[-3:] == [
        ("pnrNo", "synthetic-pnr"),
        ("tkRetNo", "return-one"),
        ("tkRetNo", "return-two"),
    ]


def test_station_refund_quote_feeds_execution():
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/classes/com.korail.mobile.refunds.verifyOnlineRefunds":
            return httpx.Response(
                200,
                json={
                    "strResult": "SUCC",
                    "h_msg_cd": "API.I00000",
                    "rcvd_amt": "10000",
                    "ret_fee": "0",
                    "ret_amt": "10000",
                    "orgtkinfo_list": [
                        {
                            "pnr_no": "synthetic-pnr",
                            "ogtk_sale_dt": "20260701",
                            "ogtk_sale_wct_no": "1",
                            "ogtk_sale_sqno": "2",
                            "ogtk_ret_pwd": "synthetic-return-password",
                            "ret_dv_cd": "synthetic-refund-kind",
                            "ret_rsn_cd": "synthetic-reason",
                            "tk_knd_cd": "synthetic-ticket-kind",
                        }
                    ],
                },
            )
        assert request.url.path == "/classes/com.korail.mobile.refunds.executeOnlineRefunds"
        return httpx.Response(
            200,
            json={
                "strResult": "SUCC",
                "h_msg_cd": "API.I00000",
                "h_ret_dv_cd": "synthetic-refund-kind",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(respond))
    client.session.current = KorailSession(jsessionid="synthetic-session")
    try:
        verified = client.verify_station_ticket_refund(
            StationRefundVerificationRequest(
                "synthetic-name", "part-1", "part-2", "part-3", "part-4"
            )
        )
        request = StationRefundExecutionRequest.from_verification(
            verified,
            customer_phone="synthetic-phone",
            customer_name="synthetic-name",
        )
        result = client.execute_station_ticket_refund(request)
    finally:
        client.close()

    assert parse_qs(requests[0].content.decode())["retNo4"] == ["part-4"]
    assert len(requests) == 2
    assert isinstance(result, StationRefundExecutionResponse)
    assert result.refund_division_code == "synthetic-refund-kind"
    assert request.refund_amount == "10000"
    assert request.refund_fee == "0"


def test_station_ticket_refund_without_a_session_is_refused_by_name():
    # Both said "account read requires an authenticated session", which is
    # not what a refund is. Neither sends anything.
    import pytest

    from korail_mobile_api import KorailAuthError

    def never(_request):
        raise AssertionError("nothing may be sent without a session")

    client = KorailClient(transport=httpx.MockTransport(never))
    request = StationRefundExecutionRequest(
        "synthetic-pnr", "20260701", "1", "2", "synthetic-password",
        "kind", "reason", "ticket", "synthetic-phone", "8400", "0",
        "synthetic-name",
    )
    try:
        with pytest.raises(
            KorailAuthError,
            match=r"^KORAIL station ticket refund verification requires an authenticated session$",
        ):
            client.verify_station_ticket_refund(
                StationRefundVerificationRequest("n", "1", "2", "3", "4")
            )
        with pytest.raises(
            KorailAuthError,
            match=r"^KORAIL station ticket refund requires an authenticated session$",
        ):
            client.execute_station_ticket_refund(request)
    finally:
        client.close()


def test_an_expired_session_on_a_station_ticket_refund_clears_the_client():
    # The same pin as test_mutation_live_paths.py's P058 test, for the one
    # mutation that goes through client.v7: one request out, no session or
    # cookie left after P058.
    import pytest

    from korail_mobile_api.errors import KorailSessionExpiredError

    seen: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={"strResult": "FAIL", "h_msg_cd": "P058", "h_msg_txt": "expired"},
        )

    client = KorailClient(transport=httpx.MockTransport(respond))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    client.http.cookies.set(
        "JSESSIONID", "synthetic-secret", domain="smart.letskorail.com"
    )
    request = StationRefundExecutionRequest(
        "synthetic-pnr", "20260701", "1", "2", "synthetic-password",
        "kind", "reason", "ticket", "synthetic-phone", "8400", "0",
        "synthetic-name",
    )
    try:
        with pytest.raises(KorailSessionExpiredError):
            client.execute_station_ticket_refund(request)
    finally:
        client.close()
    assert len(seen) == 1
    assert client.session.current is None
    assert not client.http.cookies


def test_v7_call_with_common_fields_puts_device_version_key_first():
    # Every CommonIn subclass serializes CommonIn first (VerifyOnlineRefundsIn
    # .java:123-124), so the wire form must carry Device/Version/Key ahead of
    # the DTO's own fields, not after them.
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.http import KorailHttpClient
    from korail_mobile_api.read_payloads import build_station_refund_verification_form
    from korail_mobile_api.v7 import V7Gateway

    captured: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    http = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(respond))
    gw = V7Gateway(http)
    try:
        gw.call(
            "NetworkApi.verifyOnlineRefunds",
            build_station_refund_verification_form(
                StationRefundVerificationRequest("synthetic-name", "11", "22", "33", "44")
            ),
            include_common=True,
        )
    finally:
        http.close()
    assert len(captured) == 1
    body = parse_qsl(captured[0].content.decode())
    assert [key for key, _ in body] == [
        "Device", "Version", "Key", "strName", "retNo1", "retNo2", "retNo3", "retNo4",
    ]
