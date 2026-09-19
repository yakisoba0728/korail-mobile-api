# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Bounded, redacted live retry for reads with server-derived inputs.

Two opt-ins are required: ``KORAIL_MOBILE_API_LIVE=1`` (the package-wide live
switch) and ``KORAIL_LIVE_RETRY_READS=1`` (this script). Neither alone runs.
Credentials are prompted in memory. Nothing from the raw server body, account,
ticket identity, or PNR is printed or written to disk.
"""

from __future__ import annotations

import getpass
import os
import sys
import time
from collections.abc import Callable
from typing import Any

from korail_mobile_api import (
    KorailClient,
    KorailConfig,
    MergeSeatsInquiryRequest,
    PriceFareLeg,
    PriceFareQuoteRequest,
    TrainSearchQuery,
)


def _describe(value: Any) -> str:
    raw = getattr(value, "raw", None)
    result = raw.get("strResult") if isinstance(raw, dict) else None
    code = raw.get("h_msg_cd") if isinstance(raw, dict) else None
    parts = [
        f"type={type(value).__name__}",
        f"result={getattr(value, 'str_result', result or 'parsed')}",
        f"code={getattr(value, 'h_msg_cd', code)}",
    ]
    for name in ("trains", "stops", "intermediate_stations", "items", "reservations"):
        rows = getattr(value, name, None)
        if isinstance(rows, (tuple, list)):
            parts.append(f"{name}={len(rows)}")
    return " ".join(parts)


def _try(name: str, function: Callable[[], Any]) -> Any | None:
    try:
        value = function()
    except Exception as exc:
        print(f"{name}: {type(exc).__name__} code={getattr(exc, 'code', None)}")
        return None
    print(f"{name}: {_describe(value)}")
    return value


def main() -> int:
    if (
        os.environ.get("KORAIL_MOBILE_API_LIVE") != "1"
        or os.environ.get("KORAIL_LIVE_RETRY_READS") != "1"
    ):
        raise SystemExit(
            "Set KORAIL_MOBILE_API_LIVE=1 and KORAIL_LIVE_RETRY_READS=1 to run live reads"
        )
    member = getpass.getpass("member (hidden): ")
    password = getpass.getpass("password (hidden): ")
    client = KorailClient(KorailConfig(enable_dynapath=True))
    last_request = 0.0

    def pace(_request: Any) -> None:
        nonlocal last_request
        elapsed = time.monotonic() - last_request
        if last_request and elapsed < 1.5:
            time.sleep(1.5 - elapsed)
        last_request = time.monotonic()

    client.http._client.event_hooks["request"].append(pace)
    try:
        if _try("login", lambda: client.login(member, password)) is None:
            return 1
        if "--post-refund" in sys.argv[1:]:
            _try("reservation_history", client.get_reservation_history)
            _try("active_ticket_list", client.get_ticket_list)
            return 0
        if "--fallback-routes" in sys.argv[1:]:
            for departure, arrival in (("포항", "목포"), ("진주", "강릉")):
                query = TrainSearchQuery(departure, arrival, "20260929", "060000")
                _try(
                    f"fallback_{departure}_{arrival}",
                    lambda query=query: client.search_trains_with_transfer_fallback(query),
                )
            return 0
        _try("v7_specific_date", lambda: client.v7.call("NetworkApi.postSpecificDateData"))
        _try("multi_child_20260929", lambda: client.get_multi_child_discount_targets("20260929"))
        route = TrainSearchQuery("서울", "부산", "20260929", "000000")
        search = _try("search_seoul_busan", lambda: client.search_trains(route))
        if search is None or not search.trains:
            return 0
        train = search.trains[0]
        schedule = _try(
            "schedule_selected_train",
            lambda: client.get_train_schedule(train.run_date or "20260929", train.train_no),
        )
        if schedule is not None:
            middle = next(
                (stop for stop in schedule.stops[1:-1] if stop.station_name), None
            )
            if middle is not None:
                departure_time = (train.departure_time or "000000").zfill(6)
                _try(
                    "merge_seats_real_middle_station",
                    lambda: client.get_merge_seats_inquiry(
                        MergeSeatsInquiryRequest(
                            boarding_datetime=(train.departure_date or "20260929") + departure_time,
                            run_datetime=(train.run_date or "20260929") + departure_time,
                            train_no=train.train_no,
                            departure_station_name=train.departure_station_name or "서울",
                            arrival_station_name=train.arrival_station_name or "부산",
                            selected_station_name=middle.station_name or "",
                            room_class_code="1",
                            seat_attribute_code=train.seat_attribute_code or "015",
                            passenger_count=1,
                        )
                    ),
                )
        goods_no = train.goods_no or search.metadata.product_no
        standing_code = train.raw.get("h_stlb_trn_clsf_cd") or (
            schedule.raw.get("stlbTrnClsfCd")
            if schedule is not None and isinstance(schedule.raw, dict)
            else None
        )
        print(
            "fare_sources: "
            f"goods={bool(goods_no)} standing={bool(standing_code)}"
        )
        if goods_no and isinstance(standing_code, str) and standing_code:
            _try(
                "fare_quote_server_goods",
                lambda: client.get_price_fare_quote(
                    PriceFareQuoteRequest(
                        legs=(
                            PriceFareLeg(
                                departure_station_code=train.departure_station_code or "0001",
                                arrival_station_code=train.arrival_station_code or "0020",
                                run_date=train.run_date or "20260929",
                                train_no=train.train_no,
                                goods_no=goods_no,
                                requested_seat_attribute_code=train.seat_attribute_code or "015",
                                train_group_code=train.train_group_code or "",
                                standing_train_classification_code=standing_code,
                            ),
                        )
                    )
                ),
            )
        else:
            print("fare_quote_server_goods: unavailable (source values incomplete)")
        late = TrainSearchQuery("서울", "부산", "20260929", "235900")
        _try(
            "direct_transfer_fallback_late",
            lambda: client.search_trains_with_transfer_fallback(late),
        )
        return 0
    finally:
        try:
            client.logout()
        except Exception:
            print("logout: failed")
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
