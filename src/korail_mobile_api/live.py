"""환경변수로 실기기 값을 고정하고 라이브 스모크를 돌리는 보조 모듈.

여기 있는 것은 두 가지다. :func:`build_config_from_env` 는 DynaPath 의 기기
식별자·OS·모델을 환경변수에서 읽어
:class:`~korail_mobile_api.config.KorailConfig` 를 만든다 — 프로세스를 넘어
안정적인 기기 식별자를 얻는 유일한 방법이다. :func:`run_live_smoke_from_env`
는 실제 서버에 붙어 읽기 표면을 한 바퀴 돈다.

라이브 호출은 ``KORAIL_MOBILE_API_LIVE=1`` 이 없으면 시작하지 않는다
(:func:`live_enabled`).
"""
from __future__ import annotations

import os
import time
from typing import Any

from .client import KorailClient
from .config import KorailConfig
from .constants import build_dalvik_user_agent
from .dynapath import (
    KORAIL_DYNAPATH_AS_VALUE,
    DynapathConfig,
    DynapathTokenSettings,
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
    """기기 신원을 환경변수에서 가져온 :class:`KorailConfig`.

    맨손 ``KorailConfig()`` 로도 로그인은 된다. 인스턴스마다 합성된 기기 값을
    쓴다. 이 함수는 **실제 값**을 고정하는 방법이고, 프로세스를 넘어 안정적인
    기기 식별자를 얻는 유일한 길이다 — 이 패키지는 아무 상태도 저장하지 않으므로
    합성 값은 그럴 수 없다.

    세 변수는 필수이며 기본값이 없다. 여기서는 틀린 값이 없는 값보다 나쁘다.

    ``KORAIL_DYNAPATH_DEVICE_ID``
        DynaPath 의 ``di``. 기기의 ``Settings.Secure.ANDROID_ID``
        (``AbstractC1228a.java:16``), 소문자 hex 16자.
    ``KORAIL_DYNAPATH_OS_VERSION``
        ``Build.VERSION.RELEASE``. 예: ``"15"``. SDK 정수가 아니다.
    ``KORAIL_DYNAPATH_DEVICE_MODEL``
        ``Build.MODEL``. 예: ``"SM-S928N"``.

    뒤의 둘은 일부러 두 번 쓰인다. 토큰의 ``os``·``dm`` 으로 들어가고,
    :func:`~korail_mobile_api.constants.build_dalvik_user_agent` 를 통해
    ``User-Agent`` 로도 들어간다. 그래서 ``KORAIL_USER_AGENT`` 만 따로 덮어쓰면
    토큰이 뒷받침하지 않는 기기를 헤더에서 주장하게 된다.

    나머지는 — base URL, 화면 크기, SDK 정수, 광고 식별자,
    ``KORAIL_DYNAPATH_AS_VALUE`` — 패키지 기본값으로 떨어진다.
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
