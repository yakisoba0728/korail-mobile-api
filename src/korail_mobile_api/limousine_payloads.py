from __future__ import annotations

from typing import TypeVar

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
    name: str,
) -> QueryT:
    if not isinstance(query, expected):
        raise TypeError(f"{name} query must be a {expected.__name__}")
    query.__post_init__()
    return query


def validate_limousine_schedule_query(
    query: object,
) -> LimousineScheduleQuery:
    return _validated_query(query, LimousineScheduleQuery, "schedule")


def validate_limousine_seat_inventory_query(
    query: object,
) -> LimousineSeatInventoryQuery:
    return _validated_query(
        query,
        LimousineSeatInventoryQuery,
        "seat inventory",
    )


def validate_limousine_schedule_view_query(
    query: object,
) -> LimousineScheduleViewQuery:
    return _validated_query(
        query,
        LimousineScheduleViewQuery,
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
