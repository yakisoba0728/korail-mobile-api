"""리무진 연계 조회 응답을 :mod:`korail_mobile_api.limousine_models` 로 옮긴다.

세 파서가 세 라우트를 맡는다. 봉투는 정확히 ``SUCC`` 여야 하고 그 밖은
:class:`~korail_mobile_api.errors.KorailProtocolError` 다.

목록 키를 다루는 방식이 라우트마다 다르며 그것은 앱 선언을 따른 것이다.
스케줄 조회의 ``trainList`` 와 좌석이동 목록의 ``trn_infos`` 는 없거나
``null`` 이어도 빈 결과일 뿐이지만, 좌석 재고의 ``seatList`` 는 필수라서
키가 없으면 오류다.
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
from .models import BaseKorailResponse


def _optional_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or null"
        )
    return value


def _row(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} contained a non-object item"
        )
    return value


def _nullable_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a list or null"
        )
    return value


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


def _response_fields(response: BaseKorailResponse) -> dict[str, Any]:
    return {
        "h_msg_cd": response.h_msg_cd,
        "h_msg_txt": response.h_msg_txt,
        "str_result": response.str_result,
        "raw": response.raw,
    }


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
    "train_order_no": "trnOrdNo",
    "yms_application_flag": "ymsAplFlg",
}


def parse_limousine_schedule_response(
    response: BaseKorailResponse,
) -> LimousineScheduleResponse:
    """``lmu.scdlQry.do`` 의 응답을 파싱한다.

    봉투가 정확히 ``SUCC`` 여야 하고 그 밖은
    :class:`~korail_mobile_api.errors.KorailProtocolError` 다.

    ``trainList`` 는 없거나 ``null`` 이어도 되고 그때 ``schedules`` 는 빈
    튜플이다 — 조건에 맞는 편이 없다는 뜻이지 오류가 아니다. 다음 페이지가
    있는지는 ``following_page_extension`` 으로 본다.
    """
    _require_exact_success(response)
    raw = response.raw
    schedules = []
    for value in _nullable_list(raw, "trainList", "limousine schedule"):
        row = _row(value, "limousine schedule trainList")
        schedules.append(
            LimousineSchedule(
                **{
                    field_name: _optional_string(
                        row,
                        wire_name,
                        "limousine schedule",
                    )
                    for field_name, wire_name in _SCHEDULE_FIELDS.items()
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
    """``lms.TResidualSeatsResearch.do`` 의 응답을 파싱한다.

    봉투가 정확히 ``SUCC`` 여야 한다. 스케줄 조회와 달리 ``seatList`` 키는
    **필수**라서 키가 없으면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 다. 빈 리스트 자체는
    정상이며 좌석 정보가 하나도 없다는 뜻이다.
    """
    _require_exact_success(response)
    raw = response.raw
    seats = []
    for value in _required_list(raw, "seatList", "limousine seat inventory"):
        row = _row(value, "limousine seat inventory seatList")
        seats.append(
            LimousineSeat(
                **{
                    field_name: _optional_string(
                        row,
                        wire_name,
                        "limousine seat inventory",
                    )
                    for field_name, wire_name in _SEAT_FIELDS.items()
                },
                raw=row,
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
                **{
                    field_name: _optional_string(
                        product,
                        wire_name,
                        "limousine recommended product",
                    )
                    for field_name, wire_name in _PRODUCT_FIELDS.items()
                },
                raw=product,
            )
        )
    return tuple(products)


def parse_limousine_schedule_view_response(
    response: BaseKorailResponse,
) -> LimousineScheduleViewResponse:
    """``seatMovie.LimousineScheduleView`` 의 응답을 파싱한다.

    봉투가 정확히 ``SUCC`` 여야 한다. 열차 행은 ``trn_infos.trn_info`` 에
    있고, ``trn_infos`` 가 ``null`` 이면 ``schedules`` 가 빈 튜플이다. 행마다
    추천 상품 목록이 함께 오며 :class:`LimousineRecommendedProduct` 로 파싱한다.

    다음 페이지 여부는 ``next_page_flag``, 전체 건수는 ``result_count`` 다.
    """
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
                **{
                    field_name: _optional_string(
                        row,
                        wire_name,
                        "limousine schedule view train",
                    )
                    for field_name, wire_name in _SCHEDULE_VIEW_FIELDS.items()
                },
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
