"""Removed APK calls must fail at the current transport boundary."""

import httpx
import pytest

from korail_mobile_api import KorailClient
from korail_mobile_api.errors import KorailProtocolError


def test_old_v7_routes_are_blocked_before_transport():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={})

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        for path in (
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            "/classes/com.korail.mobile.gift.gdLst.do",
            "/classes/com.korail.mobile.seatMovie.LimousineScheduleView",
            "/classes/com.korail.mobile.tk.plfNo.do",
        ):
            with pytest.raises(KorailProtocolError):
                client.http.post_form(path)
        with pytest.raises(KorailProtocolError):
            client.http.get_json("/file/CACHE/prdMobilePlusNotice.cache")
    finally:
        client.close()

    assert seen == []
    for method in (
        "get_gift_ticket_list",
        "get_limousine_schedule_view",
        "get_platform_numbers",
    ):
        assert not hasattr(KorailClient, method)
