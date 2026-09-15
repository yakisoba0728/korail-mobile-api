"""Offline wire checks for newly connected 7.0.6 client flows."""

from urllib.parse import parse_qs, parse_qsl

import httpx

from korail_mobile_api import (
    KorailClient,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
    TrainSearchQuery,
    V7MutationConsent,
    V7MutationPreview,
)
from korail_mobile_api.models import KorailSession


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


def test_station_refund_quote_feeds_execution_without_socket_in_dry_run():
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.url.path == (
            "/classes/com.korail.mobile.refunds.verifyOnlineRefunds"
        )
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
        preview = client.execute_station_ticket_refund(
            request,
            consent=V7MutationConsent(
                allow_methods=frozenset({"NetworkApi.executeOnlineRefunds"}),
            ),
        )
    finally:
        client.close()

    assert parse_qs(requests[0].content.decode())["retNo4"] == ["part-4"]
    assert len(requests) == 1
    assert isinstance(preview, V7MutationPreview)
    assert preview.name == "NetworkApi.executeOnlineRefunds"
    assert request.refund_amount == "10000"
    assert request.refund_fee == "0"
