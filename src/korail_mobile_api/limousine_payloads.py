"""리무진 연계 조회의 요청 폼 빌더.

:mod:`korail_mobile_api.limousine_models` 의 질의를 전선 키로 옮깁니다.
``validate_*`` 함수는 질의가 **정확히** 그 타입인지 확인한 뒤
``__post_init__`` 의 검사를 다시 돌립니다.

세 폼 모두 공통 ``Device``/``Version`` 을 싣습니다.
:func:`build_limousine_schedule_view_form` 만은 공통 ``Key`` 대신 호출자가 넘긴
``Sid``(:func:`~korail_mobile_api.crypto.generate_sid`)를 싣습니다.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from .config import KorailConfig
from .limousine_models import (
    LimousineScheduleQuery,
    LimousineScheduleViewQuery,
    LimousineSeatInventoryQuery,
)


QueryT = TypeVar("QueryT")


def _validated_query(
    query: object,
    expected: type[QueryT],
    validator: Callable[[QueryT], None],
    name: str,
) -> QueryT:
    if type(query) is not expected:
        raise TypeError(
            f"{name} query must be exactly {expected.__name__}"
        )
    validated = cast(QueryT, query)
    validator(validated)
    return validated


def validate_limousine_schedule_query(
    query: object,
) -> LimousineScheduleQuery:
    """``query`` 가 정확히 :class:`LimousineScheduleQuery` 인지 확인하고 돌려줍니다."""
    return _validated_query(
        query,
        LimousineScheduleQuery,
        LimousineScheduleQuery.__post_init__,
        "schedule",
    )


def validate_limousine_seat_inventory_query(
    query: object,
) -> LimousineSeatInventoryQuery:
    """``query`` 가 정확히 :class:`LimousineSeatInventoryQuery` 인지 확인하고
    돌려줍니다.

    :func:`validate_limousine_schedule_query` 와 같은 규칙입니다.
    """
    return _validated_query(
        query,
        LimousineSeatInventoryQuery,
        LimousineSeatInventoryQuery.__post_init__,
        "seat inventory",
    )


def validate_limousine_schedule_view_query(
    query: object,
) -> LimousineScheduleViewQuery:
    """``query`` 가 정확히 :class:`LimousineScheduleViewQuery` 인지 확인하고
    돌려줍니다.
    """
    return _validated_query(
        query,
        LimousineScheduleViewQuery,
        LimousineScheduleViewQuery.__post_init__,
        "schedule view",
    )


def _sid(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("sid must be a string")
    if not value.strip():
        raise ValueError("sid must not be empty")
    return value


def _wire_flag(value: bool) -> str:
    return "Y" if value else "N"


def build_limousine_schedule_form(
    config: KorailConfig,
    query: LimousineScheduleQuery,
) -> dict[str, str]:
    """``lmu.scdlQry.do`` 의 운행 스케줄 조회 폼을 만듭니다.

    ``BusReservationService.java:27``. 역은 역이름이 아니라 4자리 역코드
    (``dptRsStnCd``/``arvRsStnCd``)이고, 날짜는 ``YYYYMMDD``, 시각은
    ``HHMMSS`` 입니다.
    """
    query = validate_limousine_schedule_query(query)
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "dptDt": query.departure_date,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        "tmGpCd": query.service_code,
        "psrmClCd": query.room_class_code,
        "dptTm": query.departure_time,
        "trnNo": query.train_no,
        "seatAttCd": query.seat_attribute_code,
        "rsvSaleDvCd": query.reservation_sale_division_code,
    }


def build_limousine_seat_inventory_form(
    config: KorailConfig,
    query: LimousineSeatInventoryQuery,
) -> dict[str, str]:
    """``lms.TResidualSeatsResearch.do`` 의 좌석 재고 조회 폼을 만듭니다.

    ``BusReservationService.java:31``. 두 값만 문자열이 아닌 파이썬 값에서
    옵니다 — ``totPsgCnt`` 는 ``str(int)``, ``isArrow`` 는 ``"Y"``/``"N"`` 이
    아니라 ``"true"``/``"false"`` 입니다.
    """
    query = validate_limousine_seat_inventory_query(query)
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "trnClsfCd": query.train_class_code,
        "trnGpCd": query.service_code,
        "runDt": query.run_date,
        "trnNo": query.train_no,
        "srcarNo": query.car_no,
        "psrmClCd": query.room_class_code,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        "seatAttCd": query.seat_attribute_code,
        "dptStnRunOrdr": query.departure_run_order,
        "arvStnRunOrdr": query.arrival_run_order,
        "totPsgCnt": str(query.passenger_count),
        "gdNo": query.product_no,
        "isArrow": "true" if query.is_arrow else "false",
    }


def build_limousine_schedule_view_form(
    config: KorailConfig,
    query: LimousineScheduleViewQuery,
    *,
    sid: str,
) -> dict[str, str]:
    """``seatMovie.LimousineScheduleView`` 의 열차 목록 조회 폼을 만듭니다.

    ``SeatMovieService.java:16``. 이 폼만은 공통 ``Key`` 대신 호출자가 넘긴
    """
    query = validate_limousine_schedule_view_query(query)
    return {
        "Device": config.device,
        "Version": config.version,
        "Sid": _sid(sid),
        "txtMenuId": query.menu_id,
        "radJobId": query.job_id,
        "txtJobDv": query.job_division,
        "selGoTrain": query.service_code,
        "txtTrnGpCd": query.service_code,
        "txtGoTrnNo": query.train_no,
        "txtGoStart": query.departure_station_name,
        "txtGoEnd": query.arrival_station_name,
        "txtGoAbrdDt": query.departure_date,
        "txtGoHour": query.departure_time,
        "txtPsgFlg_1": str(query.passenger_group_1_count),
        "txtPsgFlg_2": str(query.passenger_group_2_count),
        "txtPsgFlg_3": str(query.senior_count),
        "txtPsgFlg_4": str(query.severe_disability_count),
        "txtPsgFlg_5": str(query.mild_disability_count),
        "txtSeatAttCd_2": query.direction_seat_attribute_code,
        "txtSeatAttCd_3": query.location_seat_attribute_code,
        "txtSeatAttCd_4": query.room_seat_attribute_code,
        "ebizCrossCheck": _wire_flag(query.ebiz_cross_check),
        "srtCheckYn": _wire_flag(query.srt_check),
        "rtYn": _wire_flag(query.round_trip),
    }
