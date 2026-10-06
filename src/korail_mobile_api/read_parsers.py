# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 파서의 기존 import 경로와 열차·좌석 조회 파서를 유지합니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    _nullable_scalar_fields,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
)
from ._read_account_parsers import parse_cart_list_response as parse_cart_list_response
from ._read_account_parsers import parse_crew_request_list_response as parse_crew_request_list_response
from ._read_account_parsers import parse_customer_trip_info_response as parse_customer_trip_info_response
from ._read_account_parsers import parse_delay_discount_ticket_response as parse_delay_discount_ticket_response
from ._read_account_parsers import parse_deposit_bank_response as parse_deposit_bank_response
from ._read_account_parsers import parse_discount_coupon_response as parse_discount_coupon_response
from ._read_account_parsers import parse_korail_point_summary_response as parse_korail_point_summary_response
from ._read_account_parsers import parse_maas_cancel_fee_response as parse_maas_cancel_fee_response
from ._read_account_parsers import (
    parse_maas_service_detail_list_response as parse_maas_service_detail_list_response,
)
from ._read_account_parsers import parse_mileage_history_response as parse_mileage_history_response
from ._read_account_parsers import (
    parse_multi_child_discount_target_response as parse_multi_child_discount_target_response,
)
from ._read_account_parsers import parse_product_detail_response as parse_product_detail_response
from ._read_account_parsers import (
    parse_product_reservation_list_response as parse_product_reservation_list_response,
)
from ._read_account_parsers import parse_service_status_response as parse_service_status_response
from ._read_account_parsers import parse_travel_product_search_response as parse_travel_product_search_response
from ._read_account_parsers import parse_trip_change_date_response as parse_trip_change_date_response
from ._read_account_parsers import parse_trip_menu_response as parse_trip_menu_response
from ._read_parser_common import _optional_add_srv_item as _optional_add_srv_item
from ._read_parser_common import _optional_read_rows as _optional_read_rows
from ._read_parser_common import _parse_add_srv_item as _parse_add_srv_item
from ._read_parser_common import _required_read_rows as _required_read_rows
from ._read_parser_common import _required_read_strings as _required_read_strings
from ._read_parser_common import _validate_envelope, _validate_strict_read_envelope
from ._read_pass_parsers import _parse_pass_goods_info as _parse_pass_goods_info
from ._read_pass_parsers import _parse_pass_menu_data as _parse_pass_menu_data
from ._read_pass_parsers import _primitive_json_integer as _primitive_json_integer
from ._read_pass_parsers import parse_commuter_info_response as parse_commuter_info_response
from ._read_pass_parsers import parse_commuter_kind_menu_response as parse_commuter_kind_menu_response
from ._read_pass_parsers import parse_discount_card_schedule_response as parse_discount_card_schedule_response
from ._read_pass_parsers import parse_discount_card_usage_response as parse_discount_card_usage_response
from ._read_pass_parsers import parse_pass_availability_response as parse_pass_availability_response
from ._read_pass_parsers import parse_pass_menu_response as parse_pass_menu_response
from ._read_pass_parsers import parse_pass_schedule_response as parse_pass_schedule_response
from ._read_ticket_parsers import _discount_card_on_ticket as _discount_card_on_ticket
from ._read_ticket_parsers import (
    _parse_reservation_history_reservation as _parse_reservation_history_reservation,
)
from ._read_ticket_parsers import parse_delay_certificate_response as parse_delay_certificate_response
from ._read_ticket_parsers import parse_delay_return_receipt_response as parse_delay_return_receipt_response
from ._read_ticket_parsers import parse_delivery_recipient_response as parse_delivery_recipient_response
from ._read_ticket_parsers import (
    parse_original_ticket_inquiry_response as parse_original_ticket_inquiry_response,
)
from ._read_ticket_parsers import (
    parse_pbp_acceptance_specification_response as parse_pbp_acceptance_specification_response,
)
from ._read_ticket_parsers import (
    parse_recent_delivery_history_response as parse_recent_delivery_history_response,
)
from ._read_ticket_parsers import parse_refund_commission_response as parse_refund_commission_response
from ._read_ticket_parsers import parse_refund_ticket_detail_response as parse_refund_ticket_detail_response
from ._read_ticket_parsers import parse_reservation_history_response as parse_reservation_history_response
from ._read_ticket_parsers import parse_self_checkin_info_response as parse_self_checkin_info_response
from ._read_ticket_parsers import (
    parse_self_checkin_seat_check_response as parse_self_checkin_seat_check_response,
)
from ._read_ticket_parsers import parse_self_seat_change_info_response as parse_self_seat_change_info_response
from ._read_ticket_parsers import (
    parse_ticket_duplication_check_response as parse_ticket_duplication_check_response,
)
from ._read_ticket_parsers import parse_ticket_list_response as parse_ticket_list_response
from ._read_ticket_parsers import parse_ticket_receipt_response as parse_ticket_receipt_response
from ._read_ticket_parsers import (
    parse_ticket_reservation_detail_response as parse_ticket_reservation_detail_response,
)
from .errors import KorailProtocolError
from .read_models import (
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    MergeSeatsInquiryResponse,
    PriceFare,
    PriceFareQuoteResponse,
    SeatAssignmentScheduleResponse,
    TrainScheduleItem,
)

_MERGE_SEATS_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_no_qb": "h_trn_no_qb",
    "train_sequence": "h_trn_seq",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "shuttle_standing_open_flag": "shtmStndOpFlg",
    "run_date": "h_run_dt",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_date": "h_dpt_dt",
    "arrival_date": "h_arv_dt",
    "departure_time": "h_dpt_tm",
    "departure_time_qb": "h_dpt_tm_qb",
    "arrival_time": "h_arv_tm",
    "arrival_time_qb": "h_arv_tm_qb",
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "general_reservation_code": "h_gen_rsv_cd",
    "general_reservation_name": "h_gen_rsv_nm",
    "remaining_standing_count": "restStndNum",
    "standing_reservation_code": "h_stnd_rsv_cd",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "journey_reservation_code": "h_jrny_rsv_cd",
    "journey_reservation_name": "h_jrny_rsv_nm",
}

_TRAIN_SCHEDULE_OUT_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "run_date": "h_run_dt",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "car_type_name": "h_car_tp_nm",
    "general_room_name": "h_gen_psrm_cl_nm",
    "special_room_name": "h_spe_psrm_cl_nm",
    "general_reservation_code": "h_gen_rsv_cd",
    "special_reservation_code": "h_spe_rsv_cd",
    "free_seat_reservation_code": "h_free_rsv_cd",
    "standing_reservation_code": "h_stnd_rsv_cd",
    # 네 개의 *_rsv_nm — TrainScheduleOutTrainInfo.java:1228/1380/1344/1196 이 코드 짝과 나란히 선언하며, 전송에 '예약하기'/'역발매중' 같은
    # 값으로 옵니다(: menu_id='A1','A2' 각 10행).
    "general_reservation_name": "h_gen_rsv_nm",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "special_reservation_name": "h_spe_rsv_nm",
    "free_seat_reservation_name": "h_free_rsv_nm",
    "seat_map_flag": "h_rd_seat_map_flg",
    "delay_sale_flag": "h_dlay_sale_flg",
    "wait_reservation_flag": "h_wait_rsv_flg",
    "reservation_possible_name": "h_rsv_psb_nm",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "info_text": "h_info_txt",
    "popup_message": "h_popup_msg",
    # TrainScheduleOutTrainInfo.java:1204,1364,1468,1480.
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "first_remaining_seat_count": "h_fst_rest_seat_cnt",
    "merge_target_flag": "h_yms_apl_flg",
    "train_suspended_flag": "h_trn_sps_flg",
}


@_preserve_read_raw
def parse_free_seat_car_response(
    raw: Mapping[str, Any],
) -> FreeSeatCarResponse:
    _validate_strict_read_envelope(raw)
    return FreeSeatCarResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "title": "fresTtl",
                "car_no": "fresScarNo",
                "content": "fresCont",
            },
            context="train read",
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_guide_seat_condition_response(
    raw: Mapping[str, Any],
) -> GuideSeatConditionResponse:
    # 앱은 실패 응답의 h_msg_txt를 안내합니다(TrainOptionViewModel.java:290-300).
    _validate_envelope(raw, return_all_failures=True)
    if raw.get("strResult") not in {"SUCC", "FAIL"}:
        raise KorailProtocolError("KORAIL seat guidance result must be SUCC or FAIL")
    # 실서버 검증 못 함. timeStamp 는 속성명(GuideSeatCndOut.java:29). 보호된 descriptor 의 9자 길이는 평문을 증명하지
    # 않습니다(GuideSeatCndOut$$serializer.java:39).
    return GuideSeatConditionResponse(
        time_stamp=_optional_integer(raw, "timeStamp", "guide seat condition"),
        **_response_fields(raw),
    )


def _parse_train_schedule_item(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
) -> TrainScheduleItem:
    return TrainScheduleItem(
        **_nullable_scalar_fields(raw, field_map, "train schedule item"),
        raw=raw,
    )


def _parse_train_schedule_container(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
    *,
    read_merge_flag: bool,
) -> tuple[str | None, tuple[TrainScheduleItem, ...]]:
    """병합 플래그는 MergeSeatsCOutTrnInfos.java:25-26,85 에만 선언되며, TrainScheduleOutTrainInfos.java:25-26,78 은
    trn_info 만 선언합니다."""
    container = _optional_mapping(raw, "trn_infos")
    if container is None:
        return None, ()
    merge_flag = _optional_scalar_string(container, "h_merge_rsv_psb_flg") if read_merge_flag else None
    trains = tuple(_parse_train_schedule_item(value, field_map) for value in _rows(container, "trn_info"))
    return merge_flag, trains


@_preserve_read_raw
def parse_seat_assignment_schedule_response(
    raw: Mapping[str, Any],
) -> SeatAssignmentScheduleResponse:
    """TrainScheduleOut.java:67 의 커서·조건을 함께 읽습니다. h_merge_rsv_psb_flg 는 다른 응답
    컨테이너(MergeSeatsCOutTrnInfos.java:85)의 필드라 읽지 않습니다."""
    _validate_strict_read_envelope(raw)
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        _TRAIN_SCHEDULE_OUT_TRAIN_FIELDS,
        read_merge_flag=False,
    )
    return SeatAssignmentScheduleResponse(
        next_page_flag=_optional_scalar_string(
            raw,
            "h_next_pg_flg",
        ),
        merge_reservation_possible_flag=merge_flag,
        **_nullable_scalar_fields(
            raw,
            {
                "job_id": "strJobId",
                "menu_id": "h_menu_id",
                "goods_no": "h_gd_no",
                "notice_message": "h_notice_msg",
                "first_seat_count": "h_seat_cnt_first",
                "second_seat_count": "h_seat_cnt_second",
                "agreement_text": "h_agree_txt",
                "first_departure_time": "txtGoHour_first",
                "result_count": "h_rslt_cnt",
                "next_query_station_no": "h_qry_st_no_next",
                "next_train_no": "h_trn_no_next",
                "next_preceding_train_no": "h_prcd_trn_no_next",
                "next_connecting_train_no": "h_ectb_trn_no_next",
                "remaining_seat_count": "h_rest_seat_cnt",
            },
            "seat assignment schedule",
        ),
        trains=trains,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_merge_seats_inquiry_response(
    raw: Mapping[str, Any],
) -> MergeSeatsInquiryResponse:
    _validate_strict_read_envelope(raw)
    stations = []
    for station in _rows(raw, "midStnList"):
        stations.append(
            IntermediateStation(
                **_nullable_scalar_fields(
                    station,
                    {
                        "code": "rsStnCd",
                        "name": "rsStnNm",
                        "run_order": "runOrdr",
                    },
                    context="train read",
                ),
                raw=station,
            )
        )
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        _MERGE_SEATS_TRAIN_FIELDS,
        read_merge_flag=True,
    )
    return MergeSeatsInquiryResponse(
        merge_reservation_possible_flag=merge_flag,
        # runDt 는 최상위 선언(MergeSeatsCOut.java:29,112)이지만 관측 20여 회에는 없었고 행별 h_run_dt 만 있었습니다. 다른 조건에서도 없다고 일반화하지
        # 않습니다.
        run_date=_optional_scalar_string(raw, "runDt", "merge seats inquiry"),
        intermediate_stations=tuple(stations),
        trains=trains,
        **_response_fields(raw),
    )


_PRICE_FARE_FIELDS = {
    "journey_sequence": "jrnySqno",
    "room_class_name": "psrmClNm",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "total_amount": "sumAmt",
    "train_no": "trnNo",
}


@_preserve_read_raw
def parse_price_fare_quote_response(
    raw: Mapping[str, Any],
) -> PriceFareQuoteResponse:
    _validate_strict_read_envelope(raw)
    fares = []
    for item in _rows(raw, "prcList"):
        fares.append(
            PriceFare(
                **_nullable_scalar_fields(
                    item,
                    _PRICE_FARE_FIELDS,
                    context="train read",
                ),
                raw=item,
            )
        )
    return PriceFareQuoteResponse(
        fares=tuple(fares),
        **_response_fields(raw),
    )


# Keep existing function import/pickle paths while implementations live in private domain modules.
# Signatures and type-hint globals remain those of the original functions.
_parser: object = None
for _parser in tuple(globals().values()):
    if getattr(_parser, "__module__", None) in {
        "korail_mobile_api._read_parser_common",
        "korail_mobile_api._read_account_parsers",
        "korail_mobile_api._read_pass_parsers",
        "korail_mobile_api._read_ticket_parsers",
    }:
        setattr(_parser, "__module__", __name__)
del _parser
