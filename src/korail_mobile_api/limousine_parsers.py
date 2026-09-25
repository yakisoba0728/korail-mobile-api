# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스는 정확한 SUCC를 요구하며 null 목록의 허용은 라이브러리 정책입니다(TResidualSeatsResearchOut.java:79)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    _nullable_scalar_fields,
    _optional_scalar_string,
    _preserve_read_raw,
    _row,
)
from .errors import KorailProtocolError
from .limousine_models import (
    LimousineSchedule,
    LimousineScheduleResponse,
    LimousineSeat,
    LimousineSeatInventoryResponse,
)
from .models import BaseKorailResponse, SeatWindow
from .parsers import (
    _inventory_ratio,
    _response_fields,
)


def _required_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a list")
    return value


def _require_exact_success(response: BaseKorailResponse) -> None:
    if response.str_result != "SUCC":
        raise KorailProtocolError("KORAIL limousine read strResult must be exact SUCC")


_SCHEDULE_FIELDS = {
    "arrival_date": "arvDt",
    "arrival_station_code": "arvRsStnCd",
    "arrival_run_order": "arvStnRunOrdr",
    "arrival_time": "arvTm",
    "transfer_division_code": "chtnDvCd",
    "departure_date": "dptDt",
    "departure_station_code": "dptRsStnCd",
    "departure_run_order": "dptStnRunOrdr",
    "departure_time": "dptTm",
    "general_remaining_seat_count": "gnrmRestSeatNum",
    "delay_minutes": "ocurDlayTnum",
    "free_remaining_seat_count": "restFresNum",
    "standing_remaining_seat_count": "restStndNum",
    "run_date": "runDt",
    "special_remaining_seat_count": "sprmRestSeatNum",
    "train_class_code": "stlbTrnClsfCd",
    "service_code": "trnGpCd",
    "train_no": "trnNo",
    # 속성 ymsAplFlgYMS(ScdlQryOutTrain.java:48-49)와 전송 키를 구분합니다. serializer 이름은
    # 보호됨(ScdlQryOutTrain$$serializer.java:35-55). ymsAplFlg 전송 키는 라이브 관측에 근거합니다.
    "yms_application_flag": "ymsAplFlg",
}
#: 선택 스칼라. trnOrdrNo 는 속성 선언만 확인돼 실서버 검증 못 함입니다(ScdlQryOutTrain.java:48). rcvdPrc 의 선언(ScdlQryOutTrain.java:40)과
#: 날짜 있는 359행 관측은 LimousineSchedule.received_price 설명 참고.
_SCHEDULE_ADDED_FIELDS = {
    "train_order_no": "trnOrdrNo",
    "received_price": "rcvdPrc",
}


@_preserve_read_raw
def parse_limousine_schedule_response(
    response: BaseKorailResponse,
) -> LimousineScheduleResponse:
    _require_exact_success(response)
    raw = response.raw
    schedules = []
    rows = [] if raw.get("trainList") is None else _required_list(raw, "trainList", "limousine schedule")
    for value in rows:
        row = _row(value, "limousine schedule trainList")
        schedules.append(
            LimousineSchedule(
                **_nullable_scalar_fields(row, _SCHEDULE_FIELDS, "limousine schedule"),
                **{
                    name: _optional_scalar_string(row, wire, "limousine schedule")
                    for name, wire in _SCHEDULE_ADDED_FIELDS.items()
                },
                raw=row,
            )
        )
    return LimousineScheduleResponse(
        following_page_extension=_optional_scalar_string(
            raw,
            "fllwPgExt",
            "limousine schedule",
        ),
        long_short_division_code=_optional_scalar_string(
            raw,
            "lgtmShtmDvCd",
            "limousine schedule",
        ),
        schedules=tuple(schedules),
        **_response_fields(response),
    )


_SEAT_FIELDS = {
    "direction_attribute_code": "dir_seat_att_cd",
    "other_attribute_code": "etc_seat_att_cd",
    "integrated_message": "intg_msg",
    "integrated_message_code": "intg_msg_cd",
    "requested_attribute_code": "rq_seat_att_cd",
    "sale_possible_flag": "sale_psb_flg",
    "seat_no": "seat_no",
    "specification": "seat_spec",
    "sequence_no": "sqr_no",
    "visual_message_division_code": "vz_msg_dv_cd",
}


@_preserve_read_raw
def parse_limousine_seat_inventory_response(
    response: BaseKorailResponse,
) -> LimousineSeatInventoryResponse:
    """공항버스 좌석 재고를 읽습니다. seatList 생략·null 은 빈 목록, 비목록·비객체 행은 오류입니다. 일반 좌석 재고와 DTO 를
    공유합니다(NetworkApi.java:271,741). layout_type 은 문자열·정수를 허용합니다."""
    _require_exact_success(response)
    raw = response.raw
    seats = []
    # seatList 누락 기본값은 emptyList()(TResidualSeatsResearchOut.java:79). null 허용 근거는 아닙니다.
    for value in (
        _required_list(raw, "seatList", "limousine seat inventory") if raw.get("seatList") is not None else []
    ):
        row = _row(value, "limousine seat inventory seatList")
        seats.append(
            LimousineSeat(
                **_nullable_scalar_fields(row, _SEAT_FIELDS, "limousine seat inventory"),
                raw=row,
            )
        )
    window_value = raw.get("windowList")
    windows = []
    for value in window_value if isinstance(window_value, list) else ():
        if not isinstance(value, Mapping):
            continue
        try:
            windows.append(
                SeatWindow(
                    start_location_ratio=_inventory_ratio(value, "st_loc_rt"),
                    close_location_ratio=_inventory_ratio(value, "cls_loc_rt"),
                )
            )
        except (KorailProtocolError, ValueError, OverflowError):
            continue
    return LimousineSeatInventoryResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "car_type_code": "car_tp_cd",
                "car_no": "scar_no",
                "seat_arrangement_code": "seat_ary_cd",
            },
            "limousine seat inventory",
        ),
        layout_type=_optional_scalar_string(raw, "layout_type", "limousine seat inventory"),
        vr_banner_url=_optional_scalar_string(raw, "vrBnrUrl", "limousine seat inventory"),
        windows=tuple(windows),
        up_down_division_code=_optional_scalar_string(
            raw,
            "up_dn_dv_cd",
            "limousine seat inventory",
        ),
        seats=tuple(seats),
        **_response_fields(response),
    )
