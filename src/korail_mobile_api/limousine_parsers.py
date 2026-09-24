# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 조회 파서. 봉투는 정확한 SUCC 를 요구합니다.

trainList 와 seatList 는 누락·null 이면 빈 목록이고, 키가 있는데 목록이 아니면 KorailProtocolError 입니다. 두 목록의 비객체 행도
KorailProtocolError 입니다. seatList 누락 기본값의 앱 근거: TResidualSeatsResearchOut.java:79. 앱 Json 설정은 보호돼 있으므로
null 강제 변환 여부는 확정할 수 없습니다 (NetworkModule.java:858-862, NetworkServiceKt.java:25-29). 배치·배너·windowList
는 선택 필드로 잘못된 값이나 창측 행을 비웁니다.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
from ._parsing import (
    _nullable_string_fields,
    _optional_scalar_string,
    _optional_string,
    _preserve_read_raw,
    _row,
)


def _required_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a list"
        )
    return value


def _require_exact_success(response: BaseKorailResponse) -> None:
    if response.str_result != "SUCC":
        raise KorailProtocolError(
            "KORAIL limousine read strResult must be exact SUCC"
        )


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
    # 보호됨(ScdlQryOutTrain$$serializer.java:35-55). ymsAplFlg 전송 키는 2026-09-22 라이브 관측에 근거합니다.
    "yms_application_flag": "ymsAplFlg",
}
#: 선택 스칼라. trnOrdrNo 는 속성 선언만 확인(ScdlQryOutTrain.java:48), 라이브 미확인. rcvdPrc(ScdlQryOutTrain.java:40)는
#: 2026-09-22 관측 359행 모두 14자리 영 채움 문자열.
_SCHEDULE_ADDED_FIELDS = {
    "train_order_no": "trnOrdrNo",
    "received_price": "rcvdPrc",
}


@_preserve_read_raw
def parse_limousine_schedule_response(
    response: BaseKorailResponse,
) -> LimousineScheduleResponse:
    """``lmu.scdlQry.do`` 의 응답을 파싱합니다."""
    _require_exact_success(response)
    raw = response.raw
    schedules = []
    rows = (
        []
        if raw.get("trainList") is None
        else _required_list(raw, "trainList", "limousine schedule")
    )
    for value in rows:
        row = _row(value, "limousine schedule trainList")
        schedules.append(
            LimousineSchedule(
                **_nullable_string_fields(row, _SCHEDULE_FIELDS),
                **{
                    name: _optional_scalar_string(row, wire, "limousine schedule")
                    for name, wire in _SCHEDULE_ADDED_FIELDS.items()
                },
                raw=row,
            )
        )
    return LimousineScheduleResponse(
        following_page_extension=_optional_string(
            raw,
            "fllwPgExt",
        ),
        long_short_division_code=_optional_string(
            raw,
            "lgtmShtmDvCd",
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
    """리무진 좌석 재고. seatList 가 없거나 null 이면 빈 목록, 목록이 아니거나 비객체 행이면 오류입니다.

    일반 좌석 재고와 응답 DTO 를 공유합니다(NetworkApi.java:271,741). 선택 필드 layout_type 은 문자열·정수를 허용합니다. 정수형 근거는 일반
    좌석 재고의 2026-09-21 관측이며 리무진 응답 자체의 라이브 검증은 아닙니다.
    """
    _require_exact_success(response)
    raw = response.raw
    seats = []
    # seatList 누락 기본값은 emptyList()(TResidualSeatsResearchOut.java:79). null 허용 근거는 아닙니다.
    for value in (
        _required_list(raw, "seatList", "limousine seat inventory")
        if raw.get("seatList") is not None
        else []
    ):
        row = _row(value, "limousine seat inventory seatList")
        seats.append(
            LimousineSeat(
                **_nullable_string_fields(row, _SEAT_FIELDS),
                raw=row,
            )
        )
    # 선택 창측 목록은 비목록이면 비우고 잘못된 행은 건너뜁니다.
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
        car_type_code=_optional_string(
            raw,
            "car_tp_cd",
        ),
        car_no=_optional_string(
            raw,
            "scar_no",
        ),
        seat_arrangement_code=_optional_string(
            raw,
            "seat_ary_cd",
        ),
        layout_type=_optional_scalar_string(raw, "layout_type", "limousine seat inventory"),
        vr_banner_url=_optional_scalar_string(raw, "vrBnrUrl", "limousine seat inventory"),
        windows=tuple(windows),
        up_down_division_code=_optional_string(
            raw,
            "up_dn_dv_cd",
        ),
        seats=tuple(seats),
        **_response_fields(response),
    )

