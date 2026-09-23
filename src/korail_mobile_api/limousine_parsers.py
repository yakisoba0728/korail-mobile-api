# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 연계 조회 응답을 :mod:`korail_mobile_api.limousine_models` 로 옮깁니다.

두 파서가 두 라우트를 맡습니다. 봉투는 정확히 ``SUCC`` 여야 하고 그 밖은
:class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

목록 키를 다루는 방식은 라우트마다 다르지 않습니다. 스케줄 조회의 ``trainList``,
좌석 재고의 ``seatList`` 모두 없거나 ``null`` 이면 빈 결과이고, 리스트가 아닌
값이면 오류입니다. 근거는 두 군데입니다. **키 누락**은 컴파일된 기본 생성자가 직접 정의합니다
(``TResidualSeatsResearchOut.java:79``:
``this.seatList = (i & 128) == 0 ? emptyList() : list;`` — 출현 비트가 없을
때만 ``emptyList()`` 이고, 이 줄은 명시적 ``null`` 에 대해서는 아무 말도
하지 않습니다). **명시적 ``null``** 은 앱의 kotlinx Json 설정이 처리합니다 —
``coerceInputValues = true`` 로 **추론**되므로(아래), 널 불가 프로퍼티에 온
``null`` 은 예외가 아니라 기본값으로 강제될 것입니다
(``analysis/jadx/sources/com/korail/talk/network/di/NetworkModule.java:858-862``
``providesNetworkJson()``, 같은 설정이
``analysis/jadx/sources/com/korail/talk/network/NetworkServiceKt.java:25-29``
``KJson`` 에도 글자까지 같게 있습니다:
다섯 setter 중 ``ignoreUnknownKeys``/``encodeDefaults``/``coerceInputValues``/
``isLenient`` 는 ``Integer.parseInt(AlienGuard…) > 0``, ``setExplicitNulls`` 한 줄만
``> 1`` 입니다).

**읽히는 것은 그 비교식 모양까지입니다.** 복호화된 정수 값 자체는 보호돼 있어
불리언 값은 직접 확인되지 않습니다. 이 문단은 "``> 0`` 은 참, ``> 1`` 은
거짓"이라는 관용구 판독에 기대고 있고, 그 판독은 ``ErrorHelper.java:47-49``
의 ``checkNotNullParameter`` 인수 순서로 **교차 확인했을 뿐 검증한 것이
아닙니다** — 따라서 ``coerceInputValues = true`` 와 ``explicitNulls = false`` 는
추론입니다. 키가 있는데 리스트가 아니면 둘 다 여전히
:class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
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
from .read_parsers import (
    _nullable_string_fields,
    _optional_scalar_string,
    _optional_string,
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
    # ScdlQryOutTrain.java:48-49 의 Kotlin **속성명**은 trnOrdrNo 와
    # ymsAplFlgYMS 입니다(trnOrdrNo 는 아래 _SCHEDULE_ADDED_FIELDS).
    # 이 클래스에는 @SerialName 이 하나도 없고(파일 전체 0건), 전선 이름은
    # ScdlQryOutTrain$$serializer.java:35-55 의 addElement() 인수 21개로만
    # 남는데 전부 AlienGuard 로 싸여 있어 정적으로는 철자를 못 읽습니다
    # (YMS 칸은 인덱스 5 = :40, write$Self 의 index 5 와 같은 자리).
    # 전선 키는 속성명이 아니라 그 descriptor 의 이름입니다 — 실서버는
    # ``ymsAplFlg`` 를 보냅니다(2026-09-22 확인). 속성명과
    # 전선 철자가 갈리는 자리에서는 **라이브가 근거**입니다.
    "yms_application_flag": "ymsAplFlg",
}
#: 스칼라로 관대하게 읽는 **전선 키**. 모양이 어긋나면 응답 전체가 아니라 이 칸만
#: ``None`` 입니다.
#:
#: * ``trnOrdrNo`` — ScdlQryOutTrain.java:48 의 Kotlin 속성명이며, 라이브로
#:   확인된 적은 없습니다.
#: * ``rcvdPrc`` — ScdlQryOutTrain.java:40. 2026-09-22 라이브 359행 전부에 있었고
#:   값은 0으로 앞을 채운 14자리 원 단위 문자열이었습니다.
_SCHEDULE_ADDED_FIELDS = {
    "train_order_no": "trnOrdrNo",
    "received_price": "rcvdPrc",
}


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
                **_nullable_string_fields(row, _SCHEDULE_FIELDS, "limousine schedule"),
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
            "limousine schedule response",
        ),
        long_short_division_code=_optional_string(
            raw,
            "lgtmShtmDvCd",
            "limousine schedule response",
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


def parse_limousine_seat_inventory_response(
    response: BaseKorailResponse,
) -> LimousineSeatInventoryResponse:
    """``lms.TResidualSeatsResearch.do`` 의 응답을 파싱합니다.

    봉투가 정확히 ``SUCC`` 여야 합니다. ``seatList`` 키가 없거나 ``null`` 이면
    빈 결과로 취급하는데, 두 경우의 근거가 다릅니다 — **키 누락**은
    컴파일된 기본 생성자가(``TResidualSeatsResearchOut.java:79``, 출현 비트가
    없을 때만 ``emptyList()``), **명시적 ``null``** 은 앱의 Json 설정
    ``coerceInputValues = true`` 가(``NetworkModule.java:858-862`` 와
    ``NetworkServiceKt.java:25-29``) 각각 담당합니다. :79 한 줄만으로는 명시
    ``null`` 을 설명할 수 없습니다. 키가 있는데 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    같은 DTO(``research.TResidualSeatsResearch.do`` 와 공유 —
    ``NetworkApi.java:271,741``)가 선언하는 ``layout_type``·``vrBnrUrl``·
    ``windowList`` 도 읽습니다. 형제 파서
    :func:`~korail_mobile_api.parsers.parse_seat_inventory_response` 와 달리 이
    셋은 선택 필드라 **관대하게** 읽습니다 — 모양이 어긋나면 그
    칸만 비우고 응답은 받습니다. ``layout_type`` 은 문자열·정수 둘 다
    받습니다(같은 DTO 를 공유하는 일반 좌석재고 라우트가 2026-09-21 실서버
    확인에서 JSON 정수로 오는 걸 확인했습니다), ``vrBnrUrl`` 은 선택,
    ``windowList`` 는 ``seatList`` 와 같은 컴파일된 기본값(없으면 빈 목록,
    ``TResidualSeatsResearchOut.java:80``) 규칙입니다.
    """
    _require_exact_success(response)
    raw = response.raw
    seats = []
    # TResidualSeatsResearchOut.java:79 -- the DTO's compiled default
    # constructor treats an absent seatList as emptyList(), not an error:
    # `this.seatList = (i & 128) == 0 ? emptyList() : list;`. An explicit null
    # is empty too (the docstring's coerceInputValues reading). A present
    # non-list value is still an error.
    for value in (
        _required_list(raw, "seatList", "limousine seat inventory")
        if raw.get("seatList") is not None
        else []
    ):
        row = _row(value, "limousine seat inventory seatList")
        seats.append(
            LimousineSeat(
                **_nullable_string_fields(row, _SEAT_FIELDS, "limousine seat inventory"),
                raw=row,
            )
        )
    # Mirrors parsers.py::parse_seat_inventory_response's identical handling
    # of the same DTO shape.
    # ``windowList``·``layout_type``·``vrBnrUrl`` 은 선택 필드입니다. 이 셋
    # 때문에 응답을 거절하지 않도록 모양이 어긋나면
    # 그 칸만 비웁니다 — 리스트가 아니면 빈 목록, 망가진 행은 건너뜀.
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
            "limousine seat inventory response",
        ),
        car_no=_optional_string(
            raw,
            "scar_no",
            "limousine seat inventory response",
        ),
        seat_arrangement_code=_optional_string(
            raw,
            "seat_ary_cd",
            "limousine seat inventory response",
        ),
        layout_type=_optional_scalar_string(raw, "layout_type", "limousine seat inventory"),
        vr_banner_url=_optional_scalar_string(raw, "vrBnrUrl", "limousine seat inventory"),
        windows=tuple(windows),
        up_down_division_code=_optional_string(
            raw,
            "up_dn_dv_cd",
            "limousine seat inventory response",
        ),
        seats=tuple(seats),
        **_response_fields(response),
    )

