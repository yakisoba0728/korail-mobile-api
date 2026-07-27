from __future__ import annotations

import os
import time
from typing import Any

from .client import KorailClient
from .config import KorailConfig
from .constants import build_dalvik_user_agent
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
    """A :class:`KorailConfig` whose device identity comes from the environment.

    A bare ``KorailConfig()`` already logs in, on synthetic device values
    generated per instance. This is the supported way to pin REAL ones instead,
    and it is the only way to get a device id that is stable across processes —
    the generated one cannot be, since nothing in this package persists state.

    Three variables are required and have no default, because a wrong value
    here is worse than a missing one:

    ``KORAIL_DYNAPATH_DEVICE_ID``
        The DynaPath ``di``: the device's ``Settings.Secure.ANDROID_ID``
        (``AbstractC1228a.java:16``), 16 lowercase hex characters.
    ``KORAIL_DYNAPATH_OS_VERSION``
        ``Build.VERSION.RELEASE``, e.g. ``"15"`` — not the SDK int.
    ``KORAIL_DYNAPATH_DEVICE_MODEL``
        ``Build.MODEL``, e.g. ``"SM-S928N"``.

    The last two are used TWICE on purpose: they go into the token's ``os`` and
    ``dm``, and into the ``User-Agent``, which is derived from them by
    :func:`~korail_mobile_api.constants.build_dalvik_user_agent` rather than
    written separately. Overriding ``KORAIL_USER_AGENT`` on its own therefore
    means asserting a device in the header that the token does not confirm.

    Everything else — base URL, screen geometry, SDK int, advertising id,
    ``KORAIL_DYNAPATH_AS_VALUE`` — falls back to the package defaults.
    """
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    advertising_id = os.environ.get("KORAIL_ADVERTISING_ID", "")
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
            build_dalvik_user_agent(
                os_release=os_version,
                device_model=device_model,
            ),
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
        uuid = client.get_uuid()
        maas_menu = client.get_maas_menu_list()
        maas_service_code = os.environ.get("KORAIL_MAAS_SERVICE_CODE")
        if not maas_service_code:
            maas_service_code = next(
                (
                    item.additional_service_code
                    for item in maas_menu.items
                    if item.uses_station_selection
                ),
                None,
            )
        session = client.login(member_no, password)
        deposit_banks = client.get_deposit_banks()
        trip_menu = client.get_trip_menu()
        maas_stations = (
            client.get_maas_station_data(maas_service_code)
            if maas_service_code
            else None
        )
        common = client.get_common_code("")
        station_info = client.get_station_info()
        station_data = client.get_station_data()
        calendar = client.get_train_calendar()
        days = (
            calendar.raw.get("runningCalendar")
            if isinstance(calendar.raw.get("runningCalendar"), list)
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
            "uuidLoaded": bool(uuid.verification_code),
            "maasMenuCount": len(maas_menu.items),
            "maasStationTested": maas_stations is not None,
            "maasStationCount": (
                len(maas_stations.stations) if maas_stations is not None else 0
            ),
            "loggedIn": bool(session.jsessionid),
            "depositBankCount": len(deposit_banks.items),
            "tripMenuCount": len(trip_menu.items),
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
