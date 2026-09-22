# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 연계 조회 응답을 :mod:`korail_mobile_api.limousine_models` 로 옮깁니다.

세 파서가 세 라우트를 맡습니다. 봉투는 정확히 ``SUCC`` 여야 하고 그 밖은
:class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

목록 키를 다루는 방식은 라우트마다 다르지 않습니다. 스케줄 조회의 ``trainList``,
좌석이동 목록의 ``trn_infos``, 좌석 재고의 ``seatList`` 모두 없거나 ``null`` 이면
빈 결과일 뿐입니다 — ``seatList`` 도 마찬가지인 것은 ``TResidualSeatsResearchOut``
의 컴파일된 기본 생성자가 그렇게 정의하기 때문입니다
(``TResidualSeatsResearchOut.java:79``:
``this.seatList = (i & 128) == 0 ? emptyList() : list;``). 키가 있는데 리스트가
아니면 셋 다 여전히 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .limousine_models import (
    LimousineRecommendedProduct,
    LimousineSchedule,
    LimousineScheduleResponse,
    LimousineScheduleViewResponse,
    LimousineScheduleViewTrain,
    LimousineSeat,
    LimousineSeatInventoryResponse,
)
from .models import BaseKorailResponse, SeatWindow
from .parsers import (
    _inventory_optional_string,
    _inventory_ratio,
    _inventory_required_scalar_string,
    _response_fields,
)
from .read_parsers import _nullable_string_fields, _optional_string, _row
from .read_parsers import _optional_list as _nullable_list


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


def _optional_nonnegative_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    value = data.get(key)
    if value is None:
        return 0
    if type(value) is not int or value < 0:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a non-negative integer"
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
    # ScdlQryOutTrain.java:48,68 의 Kotlin **속성명**은 trnOrdrNo 와
    # ymsAplFlgYMS 이고, @SerialName 인덱스는 AlienGuard 로 싸여 있어
    # 정적으로는 전선 철자를 못 읽습니다. 그래서 한때 속성명을 그대로
    # 베꼬았는데, 전선 키는 속성명이 아니라 @SerialName 입니다 — 실서버는
    # ``ymsAplFlg`` 를 보냅니다(2026-09-22 확인). 속성명을 쓰는 동안
    # ``yms_application_flag`` 는 언제나 ``None`` 이었습니다. 속성명과
    # 전선 철자가 갈리는 자리에서는 **라이브가 근거**입니다.
    #
    # ``trnOrdrNo`` 는 아직 라이브로 확인된 적이 없어 속성명 그대로 둡니다.
    "train_order_no": "trnOrdrNo",
    "yms_application_flag": "ymsAplFlg",
    # ScdlQryOutTrain.java:40 의 rcvdPrc. DTO 가 선언하는 21개 필드 중 이
    # 하나만 이 맵에 빠져 있어서 행의 유일한 운임이 raw 로만 닿았습니다.
    # 2026-09-22 라이브 359행 전부에 있었고 값은 0으로 앞을 채운 14자리
    # 원 단위 문자열입니다 -- 나머지 20개와 같이 문자열 그대로 둡니다.
    "received_price": "rcvdPrc",
}


def parse_limousine_schedule_response(
    response: BaseKorailResponse,
) -> LimousineScheduleResponse:
    """``lmu.scdlQry.do`` 의 응답을 파싱합니다."""
    _require_exact_success(response)
    raw = response.raw
    schedules = []
    for value in _nullable_list(raw, "trainList", "limousine schedule"):
        row = _row(value, "limousine schedule trainList")
        schedules.append(
            LimousineSchedule(
                **_nullable_string_fields(row, _SCHEDULE_FIELDS, "limousine schedule"),
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
    빈 결과로 취급합니다 — ``TResidualSeatsResearchOut`` 의 컴파일된 기본
    생성자가 그렇게 정의합니다(``TResidualSeatsResearchOut.java:79``). 키가
    있는데 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    같은 DTO(``research.TResidualSeatsResearch.do`` 와 공유 —
    ``NetworkApi.java:271,741``)가 선언하는 ``layout_type``·``vrBnrUrl``·
    ``windowList`` 도 형제 파서
    :func:`~korail_mobile_api.parsers.parse_seat_inventory_response` 와 같은
    규칙으로 읽습니다 — ``layout_type`` 은 필수지만 문자열·정수 둘 다
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
    # `this.seatList = (i & 128) == 0 ? emptyList() : list;`. Mirrors
    # parsers.py::parse_seat_inventory_response's identical handling of the
    # same DTO shape (`_inventory_required_list(raw, "seatList") if
    # "seatList" in raw else []`). A present-but-non-list value is still an
    # error.
    for value in (
        _required_list(raw, "seatList", "limousine seat inventory")
        if "seatList" in raw
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
    window_rows = (
        _required_list(raw, "windowList", "limousine seat inventory")
        if "windowList" in raw
        else []
    )
    windows = []
    for value in window_rows:
        window_row = _row(value, "limousine seat inventory windowList")
        windows.append(
            SeatWindow(
                start_location_ratio=_inventory_ratio(window_row, "st_loc_rt"),
                close_location_ratio=_inventory_ratio(window_row, "cls_loc_rt"),
            )
        )
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
        layout_type=_inventory_required_scalar_string(raw, "layout_type"),
        vr_banner_url=_inventory_optional_string(raw, "vrBnrUrl"),
        windows=tuple(windows),
        up_down_division_code=_optional_string(
            raw,
            "up_dn_dv_cd",
            "limousine seat inventory response",
        ),
        seats=tuple(seats),
        **_response_fields(response),
    )


_PRODUCT_FIELDS = {
    "discount_amount": "dcntAmt",
    "discount_rate": "dcntSurRt",
    "fare_amount_division_code": "famtPctDvCd",
    "goods_name": "gdNm",
    "goods_no": "gdNo",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "received_price_secondary": "rcvdPrc2",
}

_SCHEDULE_VIEW_FIELDS = {
    "detour_via_popup": "dturViaPopp",
    "elevator_damage_control": "elevDmgCtrl",
    "arrival_date": "h_arv_dt",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "arrival_consist_order": "h_arv_stn_cons_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "arrival_time": "h_arv_tm",
    "car_type_name": "h_car_tp_nm",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "change_train_sequence": "h_chg_trn_seq",
    "connection_required_time": "h_cnec_trfc_nd_hm",
    "connection_possible_flag": "h_cnec_trfc_psb_flg",
    "connection_received_price": "h_cnec_trfc_rcvd_prc",
    "delay_sale_flag": "h_dlay_sale_flg",
    "departure_date": "h_dpt_dt",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "departure_consist_order": "h_dpt_stn_cons_ordr",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "departure_time": "h_dpt_tm",
    "detour_flag": "h_dtour_flg",
    "detour_text": "h_dtour_txt",
    "expected_delay_hours": "h_expct_dlay_hr",
    "expected_departure_delay_count": "h_expn_dpt_dlay_tnum",
    "free_reservation_code": "h_free_rsv_cd",
    "free_car_count": "h_free_sracar_cnt",
    "general_room_class_name": "h_gen_psrm_cl_nm",
    "general_reservation_code": "h_gen_rsv_cd",
    "general_reservation_code_secondary": "h_gen_rsv_cd2",
    "information_text": "h_info_txt",
    "journey_reservation_code": "h_jrny_rsv_cd",
    "journey_reservation_name": "h_jrny_rsv_nm",
    "nonstop_message": "h_nonstop_msg",
    "nonstop_message_text": "h_nonstop_msg_txt",
    "popup_message": "h_popup_msg",
    "received_amount": "h_rcvd_amt",
    "received_fare": "h_rcvd_fare",
    "received_price_secondary": "h_rcvd_prc2",
    "seat_map_flag": "h_rd_seat_map_flg",
    "reservation_possible_name": "h_rsv_psb_nm",
    "run_date": "h_run_dt",
    "run_time": "h_run_tm",
    "seat_attribute_code": "h_seat_att_cd",
    "smns_train_flag": "h_smns_trn_flg",
    "special_discount_rate": "h_spe_disc_rt",
    "special_room_class_name": "h_spe_psrm_cl_nm",
    "special_reservation_code": "h_spe_rsv_cd",
    "special_reservation_code_secondary": "h_spe_rsv_cd2",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "station_popup_message": "h_station_popup_msg",
    "standing_reservation_code": "h_stnd_rsv_cd",
    "general_train_discount_rate": "h_train_disc_gen_rt",
    "origin_train_discount_rate": "h_train_disc_origin_rt",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "service_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    "use_time_care_content": "h_use_tim_care_atcl_cont",
    "wait_reservation_flag": "h_wait_rsv_flg",
    "yms_application_flag": "h_yms_apl_flg",
    "goods_no": "txtGdNo",
}


def _recommended_products(
    row: Mapping[str, Any],
) -> tuple[LimousineRecommendedProduct, ...]:
    products = []
    for value in _nullable_list(
        row,
        "rcmdGdList",
        "limousine schedule view train",
    ):
        product = _row(
            value,
            "limousine schedule view train rcmdGdList",
        )
        products.append(
            LimousineRecommendedProduct(
                **_nullable_string_fields(
                    product, _PRODUCT_FIELDS, "limousine recommended product"
                ),
                raw=product,
            )
        )
    return tuple(products)


def parse_limousine_schedule_view_response(
    response: BaseKorailResponse,
) -> LimousineScheduleViewResponse:
    """``seatMovie.LimousineScheduleView`` 의 응답을 파싱합니다."""
    _require_exact_success(response)
    raw = response.raw
    container_value = raw.get("trn_infos")
    if container_value is None:
        container: Mapping[str, Any] | None = None
        rows: list[Any] = []
    elif isinstance(container_value, Mapping):
        container = container_value
        rows = _nullable_list(
            container,
            "trn_info",
            "limousine schedule view trn_infos",
        )
    else:
        raise KorailProtocolError(
            "KORAIL limousine schedule view field trn_infos must be an "
            "object or null"
        )

    schedules = []
    for value in rows:
        row = _row(value, "limousine schedule view trn_info")
        schedules.append(
            LimousineScheduleViewTrain(
                **_nullable_string_fields(
                    row, _SCHEDULE_VIEW_FIELDS, "limousine schedule view train"
                ),
                recommended_products=_recommended_products(row),
                total_passenger_count=_optional_nonnegative_integer(
                    row,
                    "totPsgCnt",
                    "limousine schedule view train",
                ),
                raw=row,
            )
        )

    return LimousineScheduleViewResponse(
        next_ectb_train_no=_optional_string(
            raw,
            "h_ectb_trn_no_next",
            "limousine schedule view response",
        ),
        goods_no=_optional_string(
            raw,
            "h_gd_no",
            "limousine schedule view response",
        ),
        next_page_flag=_optional_string(
            raw,
            "h_next_pg_flg",
            "limousine schedule view response",
        ),
        notice_message=_optional_string(
            raw,
            "h_notice_msg",
            "limousine schedule view response",
        ),
        next_preceding_train_no=_optional_string(
            raw,
            "h_prcd_trn_no_next",
            "limousine schedule view response",
        ),
        next_query_station_no=_optional_string(
            raw,
            "h_qry_st_no_next",
            "limousine schedule view response",
        ),
        result_count=_optional_string(
            raw,
            "h_rslt_cnt",
            "limousine schedule view response",
        ),
        next_train_no=_optional_string(
            raw,
            "h_trn_no_next",
            "limousine schedule view response",
        ),
        merge_reservation_possible_flag=(
            _optional_string(
                container,
                "h_merge_rsv_psb_flg",
                "limousine schedule view trn_infos",
            )
            if container is not None
            else None
        ),
        schedules=tuple(schedules),
        **_response_fields(response),
    )
