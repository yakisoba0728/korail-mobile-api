from __future__ import annotations

import os
from typing import Any

from .client import KorailClient
from .config import KorailConfig


def live_enabled() -> bool:
    return os.environ.get("KORAIL_MOBILE_API_LIVE") == "1"


def read_credentials_from_env() -> tuple[str, str]:
    member_no = os.environ.get("KORAIL_MEMBER_NO")
    password = os.environ.get("KORAIL_PASSWORD")
    if not member_no or not password:
        raise RuntimeError("KORAIL_MEMBER_NO and KORAIL_PASSWORD are required for live smoke")
    return member_no, password


def run_live_smoke_from_env() -> dict[str, Any]:
    if not live_enabled():
        raise RuntimeError("Set KORAIL_MOBILE_API_LIVE=1 to run live smoke")
    member_no, password = read_credentials_from_env()
    client = KorailClient(KorailConfig())
    try:
        session = client.login(member_no, password)
        station_data = client.get_station_data()
        calendar = client.get_train_calendar()
        return {
            "loggedIn": bool(session.jsessionid),
            "stationDataCode": station_data.h_msg_cd,
            "calendarCode": calendar.h_msg_cd,
        }
    finally:
        client.close()
