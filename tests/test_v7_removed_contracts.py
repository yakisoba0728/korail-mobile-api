# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

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
