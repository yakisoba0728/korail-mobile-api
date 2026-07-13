from __future__ import annotations

import os
import time
from typing import Any

from .client import KorailClient
from .config import KorailConfig
from .dynapath import (
    DynapathConfig,
    DynapathTokenSettings,
    KORAIL_DYNAPATH_AS_VALUE,
)
from .models import TrainSearchQuery


def live_enabled() -> bool:
    return os.environ.get("KORAIL_MOBILE_API_LIVE") == "1"


def read_credentials_from_env() -> tuple[str, str]:
    member_no = os.environ.get("KORAIL_MEMBER_NO")
    password = os.environ.get("KORAIL_PASSWORD")
    if not member_no or not password:
        raise RuntimeError("KORAIL_MEMBER_NO and KORAIL_PASSWORD are required for live smoke")
    return member_no, password


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    advertising_id = _required_env("KORAIL_ADVERTISING_ID")
    settings = DynapathTokenSettings(
        device_id=device_id,
        as_value=os.environ.get(
            "KORAIL_DYNAPATH_AS_VALUE",
            KORAIL_DYNAPATH_AS_VALUE,
        ),
        app_start_ts=str(int(time.time() * 1000)),
        os_version=os_version,
        device_model=device_model,
    )
    dynapath = DynapathConfig(
        enabled=True,
        token_settings=settings,
        device_name=device_model,
        os_version=os_version,
    )
    return KorailConfig(
        base_url=os.environ.get(
            "KORAIL_BASE_URL",
            "https://smart.letskorail.com:443",
        ),
        user_agent=os.environ.get(
            "KORAIL_USER_AGENT",
            f"Dalvik/2.1.0 (Linux; U; Android {os_version}; {device_model})",
        ),
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", "1440")),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", "3088")),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", "33")),
        dynapath=dynapath,
        advertising_id=advertising_id,
    )


def run_live_smoke_from_env() -> dict[str, Any]:
    if not live_enabled():
        raise RuntimeError("Set KORAIL_MOBILE_API_LIVE=1 to run live smoke")
    member_no, password = read_credentials_from_env()
    client = KorailClient(build_config_from_env())
    try:
        app_data = client.get_app_data()
        notice = client.get_notice()
        session = client.login(member_no, password)
        common = client.get_common_code("")
        station_info = client.get_station_info()
        station_data = client.get_station_data()
        calendar = client.get_train_calendar()
        days = (
            calendar.raw.get("days")
            if isinstance(calendar.raw.get("days"), list)
            else []
        )
        departure_date = os.environ.get("KORAIL_TEST_DATE") or (
            str(days[0].get("runDt"))
            if days and isinstance(days[0], dict)
            else ""
        )
        if not departure_date:
            raise RuntimeError(
                "KORAIL_TEST_DATE is required when the calendar has no run date"
            )
        query = TrainSearchQuery(
            departure_station_code=os.environ.get(
                "KORAIL_DEPARTURE_STATION",
                "서울",
            ),
            arrival_station_code=os.environ.get(
                "KORAIL_ARRIVAL_STATION",
                "부산",
            ),
            departure_date=departure_date,
            departure_time=os.environ.get(
                "KORAIL_DEPARTURE_TIME",
                "060000",
            ),
        )
        search = client.search_trains(query)
        schedule = (
            client.get_train_schedule(
                search.trains[0].departure_date or departure_date,
                search.trains[0].train_no,
            )
            if search.trains
            else None
        )
        transfer = client.get_transfer_stations(
            os.environ.get("KORAIL_DEPARTURE_STATION_CODE", "0001"),
            os.environ.get("KORAIL_ARRIVAL_STATION_CODE", "0020"),
        )
        tickets = client.get_ticket_list()
        stations = (station_data.raw.get("stns") or {}).get("stn")
        return {
            "appDataLoaded": bool(app_data.raw),
            "noticeLoaded": bool(notice.raw),
            "loggedIn": bool(session.jsessionid),
            "commonCode": common.h_msg_cd,
            "stationInfoLoaded": bool(station_info.raw),
            "stationDataCount": (
                len(stations) if isinstance(stations, list) else 0
            ),
            "calendarCode": calendar.h_msg_cd,
            "trainCount": len(search.trains),
            "scheduleCode": schedule.h_msg_cd if schedule else None,
            "transferCode": transfer.h_msg_cd,
            "ticketCode": tickets.h_msg_cd,
        }
    finally:
        client.close()
