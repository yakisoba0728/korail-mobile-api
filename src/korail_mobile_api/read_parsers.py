# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""필수 필드의 파싱 실패는 거절한 전체 응답을 raw에 보존합니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    RESERVATION_OUT_EXTRA_FIELDS,
    _envelope,
    _nested_rows,
    _nullable_scalar_fields,
    _nullable_string_fields,
    _optional_bool,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _present_strings,
    _preserve_read_raw,
    _required_integer,
    _reservation_passengers,
    _response_fields,
    _rows,
    _strict_scalar_string,
)
from .errors import (
    SESSION_EXPIRED_CODE,
    KorailProtocolError,
    KorailSessionExpiredError,
    classify_app_error,
)
from .models import BaseKorailResponse
from .read_models import (
    CartItem,
    CartListResponse,
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CommuterPassengerOption,
    CrewRequestListResponse,
    CrewRequestOption,
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayCertificateResponse,
    DelayCertificateRow,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DelayReturnReceiptResponse,
    DeliveryRecipientResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCardOnTicket,
    DiscountCardScheduleResponse,
    DiscountCardScheduleTrain,
    DiscountCardSection,
    DiscountCardUsage,
    DiscountCardUsageListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    KorailPointSummaryResponse,
    MaasCancelFeeResponse,
    MaasServiceDetail,
    MaasServiceDetailInfo,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    PassAgeOption,
    PassAvailabilityMainInfo,
    PassAvailabilityResponse,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassOpenDate,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PassScheduleInfo,
    PassScheduleMainInfo,
    PassScheduleResponse,
    PassScheduleTrain,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    PriceFare,
    PriceFareQuoteResponse,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ReceiptCashPayment,
    ReceiptPayment,
    RecentDeliveryHistoryResponse,
    RecentDeliveryRecipient,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketSeat,
    ReservationDetailJourney,
    ReservationHistoryJourney,
    ReservationHistoryOriginalTicket,
    ReservationHistoryPassenger,
    ReservationHistoryReservation,
    ReservationHistoryResponse,
    ReservationHistoryTicket,
    ReservationHistoryTrain,
    ReservationSeatDetail,
    SeatAssignmentScheduleResponse,
    SelfCheckInInfoResponse,
    SelfCheckInSeat,
    SelfCheckInSeatCheckResponse,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    ServiceStatusResponse,
    TicketDuplicationCheckResponse,
    TicketListReservation,
    TicketListResponse,
    TicketListTicket,
    TicketListTrain,
    TicketReceipt,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TrainScheduleItem,
    TravelProduct,
    TravelProductSearchResponse,
    TripChangeDateResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)


@_preserve_read_raw
def parse_ticket_list_response(response: BaseKorailResponse) -> TicketListResponse:
    """승차권 목록의 pnr_list를 읽습니다(MyTicketListOut.java:82). 이 관측을 모든 응답에 일반화하지 않습니다."""
    raw = response.raw
    reservations: list[TicketListReservation] = []
    for reservation_raw in _rows(raw, "pnr_list"):
        tickets: list[TicketListTicket] = []
        for ticket_raw in _rows(reservation_raw, "ticket_list"):
            train_info = tuple(_rows(ticket_raw, "jrn_info"))
            tickets.append(
                TicketListTicket(
                    **_nullable_scalar_fields(ticket_raw, _TICKET_LIST_TICKET_FIELDS, "ticket list"),
                    train_info=train_info,
                    raw=ticket_raw,
                    trains=tuple(
                        TicketListTrain(
                            **_nullable_scalar_fields(row, _TICKET_LIST_TRAIN_FIELDS, "ticket list jrn_info"),
                            raw=row,
                        )
                        for row in train_info
                    ),
                )
            )
        # ticket_list 외 키는 MyTicketListOutReservation 의 속성명에서 추정합니다. addSrvInfo 는 공통 파서로 읽고 ticketKind 는 보호 enum
        # 을 임의 매핑하지 않습니다 (MyTicketListOutReservation.java:39,52; TicketDefine.java:1092-1130).
        additional_service = _optional_add_srv_item(
            reservation_raw,
            "addSrvInfo",
            "ticket list addSrvInfo",
            "ticket list addSrvInfo detailInfo",
        )
        reservations.append(
            TicketListReservation(
                tickets=tuple(tickets),
                **_nullable_scalar_fields(
                    reservation_raw,
                    {
                        "departure_datetime": "hDptDtTm",
                        "ticket_kind_code": "hTkKndCd",
                        "list_count": "listCnt",
                    },
                    "ticket list reservation",
                ),
                seat_assign_count=_optional_integer(
                    reservation_raw, "seatAssignCount", "ticket list reservation"
                ),
                ticket_status=_optional_scalar_string(
                    reservation_raw, "ticketStatus", "ticket list reservation"
                ),
                is_finished=_optional_bool(reservation_raw, "isFinished"),
                is_history=_optional_bool(reservation_raw, "isHistory"),
                is_emergency=_optional_bool(reservation_raw, "isEmergency"),
                display_ticket_name=_optional_scalar_string(
                    reservation_raw, "displayTicketName", "ticket list reservation"
                ),
                is_non_member=_optional_bool(reservation_raw, "isNonMember"),
                is_transfer=_optional_bool(reservation_raw, "isTransfer"),
                is_wheelchair_member=_optional_bool(reservation_raw, "isWheelchairMember"),
                is_rail_police_enabled=_optional_bool(reservation_raw, "isRailPoliceEnabled"),
                raw=reservation_raw,
                additional_service=additional_service,
                ticket_kind=_optional_scalar_string(reservation_raw, "ticketKind", "ticket list reservation"),
            )
        )
    return TicketListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        reservations=tuple(reservations),
        total_count=_optional_scalar_string(raw, "h_total_cnt", "ticket list"),
    )


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    returned_failure_codes: frozenset[str] = frozenset(),
    return_all_failures: bool = False,
    allow_result_only_success: bool = False,
) -> bool:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    # raw 를 직접 받는 호출자는 http.parse_base_response 를 거치지 않으므로 봉투 필드 타입을 여기서도 확인합니다.
    envelope = _envelope(raw)
    if "strResult" not in raw:
        raise KorailProtocolError(
            "KORAIL response omitted strResult; the protected APK default "
            "cannot be inferred for this typed read"
        )
    if allow_result_only_success and ("h_msg_cd" not in raw and "h_msg_txt" not in raw):
        if raw["strResult"] != "SUCC":
            raise KorailProtocolError("KORAIL result-only envelope requires the exact success result")
        return False
    code = envelope["h_msg_cd"]
    message = envelope["h_msg_txt"]
    result = envelope["strResult"]
    # 앱은 strResult 실패일 때만 로그인 필요로 봅니다(CommonOut.java:426-438).
    if result == "FAIL" and code == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(code, message, raw=raw)
    failed = result == "FAIL"
    if (
        failed
        and not return_all_failures
        and code not in accepted_empty_codes
        and code not in returned_failure_codes
    ):
        raise classify_app_error(code, message, raw=raw)
    return failed


def _validate_strict_read_envelope(
    raw: Mapping[str, Any],
    *,
    allow_result_only_success: bool = False,
) -> None:
    _validate_envelope(
        raw,
        allow_result_only_success=allow_result_only_success,
    )
    if raw.get("strResult") != "SUCC":
        raise KorailProtocolError("KORAIL strict read response strResult must be SUCC")


# 필수값 오류는 KorailProtocolError이며 원문은 raw에 보존합니다.

_TICKET_LIST_TICKET_FIELDS: dict[str, str] = {
    "pnr_no": "h_pnr_no",
    "sale_window_no": "h_orgtk_wct_no",
    "sale_date": "h_orgtk_sale_dt",
    "return_sale_date": "h_orgtk_ret_sale_dt",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
    "ticket_status_code": "h_tk_stt_cd",
    # 예약 행 hTkKndCd 는 보호된 serializer 대신 속성명을 사용한 추정입니다. 다른 조건의 키 부재를 보장하지 않습니다.
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    # MyTicketListOutTicket.java:92의 선언 중 여섯 필드를 읽습니다. 다른 응답에서도 필수인지는 검증 못 함입니다.
    "ticket_sequence": "h_tk_sqno",
    "ticket_status_name": "h_tk_stt_nm",
    "return_possible_flag": "h_ret_psb_flg",
    "use_transaction_no": "h_use_tno",
    "notify_use_transaction_no": "h_noty_use_tno",
    "pbp_acceptance_target_flag": "h_pbp_acep_tgt_flg",
}

#: jrn_info 행(TicketListTrainInfo.java:72 의 @SerialName 21개). h_srcar_no 는 String 선언이지만 JSON 정수로 오므로 스칼라로 읽습니다
#: (라이브 139행 전부 정수).
_TICKET_LIST_TRAIN_FIELDS: dict[str, str] = {
    "journey_sequence": "h_jrny_sqno",
    "run_date": "h_run_dt",
    "train_no": "h_trn_no",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "seat_count": "h_seat_cnt",
    "passenger_type_code": "h_psg_tp_cd",
    "received_amount": "h_rcvd_amt",
    "buyer_name": "h_buy_ps_nm",
    "passenger_name": "h_abrd_ps_nm",
    "train_suspension_flag": "trnSpsFlg",
}

_CART_ITEM_FIELDS: dict[str, str] = {
    "service_code": "addSrvDvCd",
    "provider_name": "h_add_srv_mrk_ent_nm",
    "product_name": "h_gd_nm",
    "item_type": "h_item_dv_nm",
    "departure_date": "h_dpt_dt",
    "received_amount": "h_rcvd_amt",
    "reservation_received_date": "h_rsv_rcp_dt",
    "usage_start_date": "utlStDt",
    "usage_start_time": "utlStTm",
    "usage_close_time": "utlClsTm",
    "partner_reservation_no": "coptEntRsvNo",
    "pnr_no": "h_pnr_no",
    "lump_sum_target_no": "h_lump_stl_tgt_no",
    "customer_no": "h_cust_no",
    "virtual_reservation_no": "h_vr_rsv_no",
}

# CartInfo.java:28-61,281-392의 문자열 28개를 읽습니다. 숫자형 전송 가능성을 고려해 JSON 정수도 허용하지만 각 장바구니 필드의 실제 숫자 형식은 미확인입니다.
_CART_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "item_type_code": "h_item_dv_cd",
    "provider_id": "h_add_srv_mrk_ent_id",
    "item_sequence": "h_item_sqno",
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "usage_close_date": "utlClsDt",
    "settlement_limit_time": "h_stl_lmt_tm",
    "settlement_extension_transaction_no": "h_stl_extns_tno",
    "settlement_means_allow_value": "h_stl_mns_allw_val",
    "field_settlement_division": "h_fld_stl_dv",
    "supervising_station_code": "h_spvs_rs_stn_cd",
    "filler": "h_filler",
}

_DEPOSIT_BANK_FIELDS: dict[str, str] = {
    "code": "dptnBankCd",
    "display_name": "dptnBankNm",
}

_DELAY_DISCOUNT_TICKET_FIELDS: dict[str, str] = {
    "fare": "h_dlay_fare",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "window_no": "h_orgtk_wct_no",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
}

_DELAY_DISCOUNT_TICKET_SCALAR_FIELDS: dict[str, str] = {
    "ticket_sequence": "h_tk_sqno",
    "ticket_kind_code": "h_tk_knd_cd",
    "original_ticket_sale_date": "h_orgtk_sale_dt",
    "received_amount": "h_rcvd_amt",
    "train_class_code": "h_trn_clsf_cd",
    "room_class_code": "h_psrm_cl_cd",
    "train_no": "h_trn_no",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "ticket_status_code": "h_tk_stt_cd",
    "ticket_status_name": "h_tk_stt_nm",
    "buyer_name": "h_buy_ps_nm",
    "passenger_name": "h_abrd_ps_nm",
    "page_no": "h_page_no",
}

_DELAY_DISCOUNT_MAIN_INFO_FIELDS: dict[str, str] = {
    "current_page": "h_page_no",
    "total_pages": "h_tot_page_cnt",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "last_page_flag": "h_last_page_yn",
}

_CREW_REQUEST_OPTION_FIELDS: dict[str, str] = {
    "message_code": "intgMsgCd",
    "content": "prsCont",
}

_PASS_MENU_ITEM_FIELDS: dict[str, str] = {
    # afterDay는 문자열입니다(PassMenuOutItem.java:28). : menu_no=1의 25행·2의 10행 모두 문자열이었고, 같은 25행의
    # detailType·isExpand·saleMsg1-3에는 빈 문자열도 있었습니다.
    "after_day": "afterDay",
    "agreement": "agree",
    "detail_type": "detailType",
    "detail_description": "dtlDsc",
    "enabled": "enable",
    "item_id": "id",
    "information": "information",
    "expanded": "isExpand",
    "parent_id": "parentId",
    "representative_arrival": "repSegArv",
    "representative_departure": "repSegDpt",
    "title": "title",
    "train_group_code": "trnGpCd",
    "item_type": "type",
}

_PASS_MENU_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "sale_message_1": "saleMsg1",
    "sale_message_2": "saleMsg2",
    "sale_message_3": "saleMsg3",
}

_COMMUTER_KIND_MENU_FIELDS: dict[str, str] = {
    "after_day": "afterDay",
    "agreement": "agree",
    "information": "information",
    "title": "title",
}

_TRIP_MENU_CONTENT_FIELDS: dict[str, str] = {
    "title": "contTitle",
    "detail": "contDetail",
    # detailType은 항목 종류로 해석하지 않습니다(TrGdMenuLtOutCont.java:42).
    "detail_type": "detailType",
    "active": "passActive",
    "agree": "passAgree",
    "info": "passInfo",
    "image": "contImage",
    "url": "contUrl",
    # 앱은 cmtrKndCd로 항목을 찾아 passData가 없으면 화면을 되돌립니다(PassConditionViewModel.java:1241,1244,1247-1248). :
    # menuType='P'인 6/60행에서 확인했습니다.
    "commuter_kind_code": "cmtrKndCd",
    "pass_type": "passType",
}

_TRIP_MENU_ITEM_FIELDS: dict[str, str] = {
    "title": "menuTitle",
    "detail": "menuDetail",
    "menu_type": "menuType",
    "button": "menuBtn",
    "url": "menuUrl",
}

_PRODUCT_RESERVATION_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "payment_deadline": "strStlDlnDt",
    "payment_status": "strStlSttCd",
    "virtual_reservation_no": "strVrRsvNo",
    "reservation_sequence": "strVrRsvSqno",
    "reservation_status_code": "strRsvSttCd",
}

_PRODUCT_DETAIL_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "cancellation_deadline": "strCncDlnDt",
    "cancellation_amount": "strCncRetAmt",
    "cancellation_fee": "strCncRetFee",
    "received_amount": "strRcvdAmt",
    "total_amount": "strTotStlAmt",
    "usage_period": "strUtlTrmCont",
    "virtual_reservation_no": "strVrRsvNo",
    "goods_sequence": "strGdSqno",
}

_RECEIPT_PAYMENT_FIELDS: dict[str, str] = {
    "payment_method": "h_stl_way_nm",
    "approval_date": "h_apv_dt",
    "account_no": "h_acnt_no",
    "approval_no": "h_apv_no",
    "card_no": "h_stl_crd_no",
    "point_no": "h_xpot_no",
}

_RECEIPT_CASH_PAYMENT_FIELDS: dict[str, str] = {
    "approval_method_name": "h_apv_mtd_nm",
    "authentication_domain_recognition_no": "h_athn_dmn_rcgn_no",
    "cash_receipt_approval_no": "h_cash_rcet_apv_no",
    "cash_receipt_transaction_division_code": "h_cash_rcet_txn_dv_cd",
}

_TICKET_RECEIPT_FIELDS: dict[str, str] = {
    "travel_date": "h_abrd_dt",
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "commuter_kind_code": "h_cmtr_knd_cd",
    "journey_type_code": "h_jrny_tp_cd",
    "printed_discount_name": "h_prt_disc_knd_nm",
    "printed_discount_kind_code": "h_prt_disc_knd_cd",
    "print_type": "h_prt_type",
    "seat_class_name": "h_psrm_cl_nm",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    "ticket_status_code": "h_tk_stt_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    "member_card_no": "h_stl_mb_crd_no",
}

_RESERVATION_HISTORY_TRAIN_FIELDS: dict[str, str] = {
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "run_date": "h_run_dt",
    "train_no": "h_trn_no",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "reservation_type_code": "h_rsv_tp_cd",
    "acceptance_possible_flag": "h_acpt_ps_flg",
    "payment_flag": "h_payment_flg",
    "settlement_flag": "h_stl_flg",
    # ReservationViewOutTrainInfo.java:496 의 금액 필드.
    "reserved_amount": "h_rsv_amt",
    "pnr_no": "h_pnr_no",
    # 결제 기한 선언: ReservationViewOutTrainInfo.java:94; 채워진 기한 값은 미확인입니다.
    "payment_deadline_date": "h_ntisu_lmt_dt",
    "payment_deadline_time": "h_ntisu_lmt_tm",
    "payment_message": "h_payment_msg",
    "payment_possible_date": "h_ntisu_psb_dt",
    "prepayment_target_flag": "h_pre_stl_tgt_flg",
    "journey_sequence": "h_jrny_sqno",
}

_RESERVATION_HISTORY_TOP_FIELDS: dict[str, str] = {
    "reservation_passenger_name": "h_rsv_ps_nm",
    "phone_no": "h_tel_no",
    "reservation_limit_flag": "h_rsv_lmt_flg",
    "seatmap_flag": "h_seatmap_flg",
    "process_flag": "h_proc_flag",
    "follow_flag": "h_fllw_flag",
    "customer_no": "h_cust_no",
    "customer_division_code": "h_cust_dv_cd",
    "customer_sort_code": "h_cust_srt_cd",
    "customer_class_code": "h_cust_cl_cd",
}

_RESERVATION_HISTORY_TICKET_FIELDS: dict[str, str] = {
    "sale_date": "saleDt",
    "sale_window_no": "saleWctNo",
    "sale_sequence": "saleSqno",
    "ticket_kind_code": "tkKndCd",
    "movie_ticket_flag": "mvieTkFlg",
    "delay_discount_flag": "dlayDscpFlg",
}

_RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS: dict[str, str] = {
    "sale_date": "ogtkSaleDt",
    "window_no": "ogtkWctNo",
    "sale_sequence": "ogtkSaleSqno",
    "return_password": "ogtkRetPwd",
}

_RESERVATION_HISTORY_PASSENGER_FIELDS: dict[str, str] = {
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_count_per_info": "h_psg_info_per_prnb",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_code_2": "h_dcnt_knd_cd2",
    "discount_no": "h_dcsp_no",
    "discount_no_2": "h_dcsp_no2",
    "delay_original_window_no": "dlayOgtkWctNo",
    "delay_original_sale_date": "dlayOgtkSaleDt",
    "delay_original_sale_sequence": "dlayOgtkSaleSqno",
    "delay_original_return_password": "dlayOgtkRetPwd",
}

_RESERVATION_HISTORY_RESERVATION_FIELDS: dict[str, str] = {
    "pnr_no": "h_pnr_no",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "payment_flag": "h_payment_flg",
}


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

_PASS_SCHEDULE_TRAIN_FIELDS: dict[str, str] = {
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "detour_code": "h_dtour",
    "schedule_price": "h_schd_prc",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    # TrainList.java:25-70 의 필드 중 h_run_dt 는 운행일입니다.
    "train_sequence": "h_trn_seq",
    "change_train_sequence": "h_chg_trn_seq",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "run_date": "h_run_dt",
    "price_class_code": "h_prc_cl_cd",
    "route_code": "h_rout_cd",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "car_type_code": "h_car_tp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "commuter_use_terminal_code": "h_cmtr_utl_trm_cd",
    "commuter_use_terminal_name": "h_cmtr_utl_trm_nm",
}

_PASS_SCHEDULE_MAIN_FIELDS: dict[str, str] = {
    "sale_window_no": "h_wct_no",
    "work_date": "h_work_dt",
    "work_time": "h_work_tm",
    "job_id": "h_job_id",
    "version_no": "h_ver_no",
    "message_code": "h_msg_cd",
    "selected_count": "h_sel_cnt",
    "total_selected_count": "h_tot_sel_cnt",
    "count_per_page": "h_cnt_per_page",
    "page_count": "h_page_cnt",
    "next_page_flag": "h_next_pg_flg",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "page_no": "h_page_no",
}

_PASS_AVAILABILITY_MAIN_FIELDS: dict[str, str] = {
    "message_code": "h_msg_cd",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "selected_page_no": "h_sel_pg_no",
}

_PASS_AGE_OPTION_FIELDS: dict[str, str] = {
    "commuter_age_code": "h_cmtr_utl_age_cd",
    "display_name": "h_comn_cd_nm",
    "minimum_age": "h_min_age",
    "maximum_age": "h_max_age",
}

_PASS_PERIOD_OPTION_FIELDS: dict[str, str] = {
    "commuter_period_code": "h_cmtr_utl_trm_cd",
    "display_name": "h_comn_cd_nm",
}


def _parse_pass_menu_data(
    data: Mapping[str, Any] | None,
    *,
    station_selection_key: str = "h_select_station",
) -> PassMenuData | None:
    if data is None:
        return None
    age_options = tuple(
        PassAgeOption(
            **_nullable_string_fields(row, _PASS_AGE_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(data, "pass_ageinfo")
    )
    period_options = tuple(
        PassPeriodOption(
            **_nullable_string_fields(row, _PASS_PERIOD_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(data, "pass_periodinfo")
    )
    return PassMenuData(
        commuter_kind_code=_optional_scalar_string(data, "h_cmtr_knd_cd"),
        station_selection=_optional_scalar_string(data, station_selection_key),
        age_options=age_options,
        period_options=period_options,
        raw=data,
    )


def _parse_pass_goods_info(
    data: Mapping[str, Any] | None,
) -> PassGoodsInfo | None:
    if data is None:
        return None
    passenger_infos_data = _optional_mapping(data, "psg_infos")
    passenger_infos = None
    if passenger_infos_data is not None:
        passengers = []
        for item in _rows(
            passenger_infos_data,
            "psg_info",
        ):
            passengers.append(
                PassPassengerInfo(
                    # 관측된 패스 인원은 000001 같은 패딩 문자열입니다.
                    h_cls_prnb=_optional_integer(
                        item,
                        "h_cls_prnb",
                        "pass passenger info",
                    ),
                    h_dcnt_knd_cd=_optional_scalar_string(
                        item,
                        "h_dcnt_knd_cd",
                    ),
                    h_st_prnb=_optional_integer(
                        item,
                        "h_st_prnb",
                        "pass passenger info",
                    ),
                    raw=item,
                )
            )
        passenger_infos = PassPassengerInfos(
            **_nullable_string_fields(
                passenger_infos_data,
                {
                    "h_chtn_allw_flg": "h_chtn_allw_flg",
                    "h_max_cnt": "h_max_cnt",
                    "h_min_cnt": "h_min_cnt",
                },
            ),
            psg_info=tuple(passengers),
            raw=passenger_infos_data,
        )
    return PassGoodsInfo(
        h_cnd_flg_disc_no=_optional_scalar_string(
            data,
            "h_cnd_flg_disc_no",
        ),
        psg_infos=passenger_infos,
        raw=data,
    )


@_preserve_read_raw
def parse_pass_menu_response(raw: Mapping[str, Any]) -> PassMenuResponse:
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _rows(raw, "list"):
        web_data = _optional_mapping(item, "webData")
        items.append(
            PassMenuItem(
                **_nullable_string_fields(item, _PASS_MENU_ITEM_FIELDS),
                **_nullable_scalar_fields(item, _PASS_MENU_ITEM_SCALAR_FIELDS, "pass menu item"),
                goods_data=_parse_pass_goods_info(
                    _optional_mapping(item, "goodsData"),
                ),
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(item, "passData"),
                ),
                url=(_optional_scalar_string(web_data, "url") if web_data is not None else None),
                raw=item,
            )
        )
    return PassMenuResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_commuter_kind_menu_response(
    raw: Mapping[str, Any],
) -> CommuterKindMenuResponse:
    _validate_strict_read_envelope(raw)
    return CommuterKindMenuResponse(
        **_nullable_string_fields(raw, _COMMUTER_KIND_MENU_FIELDS),
        pass_data=_parse_pass_menu_data(
            _optional_mapping(raw, "passData"),
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_crew_request_list_response(
    raw: Mapping[str, Any],
) -> CrewRequestListResponse:
    _validate_strict_read_envelope(raw)
    items = tuple(
        CrewRequestOption(
            **_nullable_string_fields(row, _CREW_REQUEST_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(raw, "prsList")
    )
    return CrewRequestListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_service_status_response(
    raw: Mapping[str, Any],
) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))


@_preserve_read_raw
def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _nested_rows(raw, "cart_infos", "cart_info"):
        items.append(
            CartItem(
                **_nullable_string_fields(item, _CART_ITEM_FIELDS),
                **_nullable_scalar_fields(item, _CART_ITEM_SCALAR_FIELDS, "cart item"),
                # h_tk_cnt 는 String 선언입니다(CartInfo.java:51).
                ticket_count=_optional_scalar_string(item, "h_tk_cnt"),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_deposit_bank_response(
    raw: Mapping[str, Any],
) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = tuple(
        DepositBank(
            **_required_read_strings(row, _DEPOSIT_BANK_FIELDS, "deposit bank"),
            raw=row,
        )
        for row in _rows(raw, "dptnBank")
    )
    return DepositBankListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_delay_discount_ticket_response(
    raw: Mapping[str, Any],
) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    rows = _nested_rows(raw, "disc_infos", "disc_info")
    items = tuple(
        DelayDiscountTicket(
            **_nullable_string_fields(row, _DELAY_DISCOUNT_TICKET_FIELDS),
            **_nullable_scalar_fields(row, _DELAY_DISCOUNT_TICKET_SCALAR_FIELDS, "delay discount ticket"),
            raw=row,
        )
        for row in rows
    )
    # main_info 는 DTO 밖 서버 추가 블록(DelayDiscountViewOut.java:24,51). 관측은 할인권 없는 계정의 0 값뿐입니다.
    main_info = _optional_mapping(raw, "main_info")
    pagination: dict[str, Any] = {}
    if main_info is not None:
        pagination = _nullable_scalar_fields(
            main_info,
            _DELAY_DISCOUNT_MAIN_INFO_FIELDS,
            "delay discount ticket list main_info",
        )
    return DelayDiscountTicketListResponse(
        items=items,
        **pagination,
        **_response_fields(raw),
    )


# CouponOutInfo.java:63 의 13필드는 모두 선택입니다.
_DISCOUNT_COUPON_FIELDS = {
    "guide": "guide",
    "start_date": "h_fdcert_mg_st_dt",
    "expiration_date": "h_fdcert_mg_cls_dt",
    "discount_kind_code": "h_dscp_knd_cd",
    "discount_rate_amount_division_code": "h_disc_rt_amt_dv_cd",
    "weekday_fare_discount": "h_inwk_fare_disc_rt_amt",
    "weekday_price_discount": "h_inwk_prc_disc_rt_amt",
    "weekend_fare_discount": "h_wknd_fare_disc_rt_amt",
    "weekend_price_discount": "h_wknd_prc_disc_rt_amt",
    "coupon_no": "h_cpn_no",
}


@_preserve_read_raw
def parse_discount_coupon_response(
    raw: Mapping[str, Any],
) -> DiscountCouponListResponse:
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"WRG000000"}),
    )
    if empty:
        return DiscountCouponListResponse(**_response_fields(raw))
    items = []
    rows = _nested_rows(
        raw,
        "coupon_infos",
        "coupon_info",
    )
    for item in rows:
        items.append(
            DiscountCoupon(
                **_nullable_scalar_fields(item, _DISCOUNT_COUPON_FIELDS, "discount coupon"),
                remarks=_present_strings(item, ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont")),
                raw=item,
            )
        )
    return DiscountCouponListResponse(
        items=tuple(items),
        current_page=_optional_integer(raw, "h_page_no", "coupon response"),
        total_pages=_optional_integer(raw, "h_tot_page_cnt", "coupon response"),
        total_count=_optional_scalar_string(raw, "h_tot_cnt", "coupon response"),
        row_count=_optional_scalar_string(raw, "h_row_cnt", "coupon response"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pass_availability_response(
    raw: Mapping[str, Any],
) -> PassAvailabilityResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    # PassInfo.java:92,96,100의 세 값은 pass_info에, 사용 개시일만 모은 편의 목록은 open_dates에 둡니다.
    open_dates = []
    pass_rows = []
    for item in _rows(raw, "pass_info"):
        date = _optional_scalar_string(item, "h_use_open_dt")
        if date is not None:
            open_dates.append(date)
        pass_rows.append(
            PassOpenDate(
                open_date=date,
                item_sequence=_optional_scalar_string(item, "h_item_sqno", "pass date"),
                pnr_no=_optional_scalar_string(item, "h_pnr_no", "pass date"),
                raw=item,
            )
        )
    ticket_issue_dates = []
    for item in _rows(raw, "ticket_info"):
        date = _optional_scalar_string(item, "h_ise_dt2")
        if date is not None:
            ticket_issue_dates.append(date)
    offices = []
    for item in _rows(raw, "wct_info"):
        offices.append(
            PassOffice(
                code=_optional_scalar_string(item, "eng_cd_val"),
                display_name=_optional_scalar_string(item, "kor_cd_val"),
                raw=item,
            )
        )
    # 상태는 중첩 main_info에서 읽습니다(PassInfoListOut.java:115; MainInfo.java:103,107,111,115). 29종은 최상위 h_msg_cd 없이
    # SUCC와 중첩 IRZ000005 등을 반환했습니다.
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassAvailabilityMainInfo(
            **_nullable_scalar_fields(main_raw, _PASS_AVAILABILITY_MAIN_FIELDS, "pass availability main info"),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    return PassAvailabilityResponse(
        open_dates=tuple(open_dates),
        ticket_issue_dates=tuple(ticket_issue_dates),
        offices=tuple(offices),
        pass_info=tuple(pass_rows),
        main_info=main_info,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_trip_menu_response(raw: Mapping[str, Any]) -> TripMenuResponse:
    _validate_envelope(raw)
    items = []
    for item in _rows(raw, "menuList"):
        contents = tuple(
            TripMenuContent(
                **_nullable_scalar_fields(row, _TRIP_MENU_CONTENT_FIELDS, "trip menu content"),
                # TrGdMenuLtOutCont.java:45 passData → TrGdMenuLtOutPass.java:29-35.
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(row, "passData"),
                    # TrGdMenuLtOutPass.java:152 — 여행 메뉴의 키 철자는 별도입니다.
                    station_selection_key="h_seiect_station",
                ),
                raw=row,
            )
            for row in _rows(item, "contList")
        )
        items.append(
            TripMenuItem(
                **_nullable_string_fields(item, _TRIP_MENU_ITEM_FIELDS),
                content_count=_optional_integer(item, "contCount", "trip menu item"),
                contents=contents,
                raw=item,
            )
        )
    return TripMenuResponse(
        items=tuple(items),
        popup_message=_optional_scalar_string(raw, "poppMsg"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_product_reservation_list_response(
    raw: Mapping[str, Any],
) -> ProductReservationListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductReservationListResponse(**_response_fields(raw))
    items = tuple(
        ProductReservation(
            **_nullable_string_fields(row, _PRODUCT_RESERVATION_FIELDS),
            raw=row,
        )
        for row in _rows(main, "entity")
    )
    return ProductReservationListResponse(
        items=items,
        total_count=_optional_integer(main, "strTotCnt", "product reservation list"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_product_detail_response(
    raw: Mapping[str, Any],
) -> ProductDetailResponse:
    _validate_envelope(raw)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductDetailResponse(**_response_fields(raw))
    included_items = []
    for item in _rows(main, "entityOne"):
        name = _optional_scalar_string(item, "strGdConsItmNm")
        if name is not None:
            included_items.append(name)
    return ProductDetailResponse(
        **_nullable_string_fields(main, _PRODUCT_DETAIL_FIELDS),
        included_item_names=tuple(included_items),
        detail_raw=main,
        **_response_fields(raw),
    )


def _required_read_rows(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Mapping[str, Any]]:
    """누락·null·비객체 행은 거절합니다(ReceiptInfos.java:49, DeliveredTicketOut.java:50 의 필수 마스크)."""
    value = data.get(key)
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be an object list")
    return value


def _required_read_strings(
    data: Mapping[str, Any],
    fields: Mapping[str, str],
    context: str,
) -> dict[str, Any]:
    """누락·null 은 거절하고, JSON 정수는 문자열로 받습니다(String 선언 필드가 정수로 온 관측, :func:`_strict_scalar_string`)."""
    values = {}
    for attr, key in fields.items():
        value = _strict_scalar_string(data, key, context)
        if value is None:
            raise KorailProtocolError(f"KORAIL {context} field {key} is required")
        values[attr] = value
    return values


@_preserve_read_raw
def parse_ticket_receipt_response(
    raw: Mapping[str, Any],
) -> TicketReceiptResponse:
    _validate_envelope(raw)
    items = []
    receipt_infos = raw.get("receipt_infos")
    if not isinstance(receipt_infos, Mapping):
        raise KorailProtocolError("KORAIL receipt_infos must be an object")
    rows = _required_read_rows(receipt_infos, "receipt_info", "ticket receipt")
    for item in rows:
        payments = []
        for payment in _required_read_rows(item, "stl_info", "ticket receipt"):
            payments.append(
                ReceiptPayment(
                    **_required_read_strings(payment, _RECEIPT_PAYMENT_FIELDS, "receipt payment"),
                    installment_months=_required_integer(payment, "h_ismt_mnth_num", "receipt payment"),
                    amount=_required_integer(payment, "h_stl_amt", "receipt payment"),
                    raw=payment,
                )
            )
        cash_receipts = []
        for cash in _required_read_rows(item, "cash_rcet_info", "ticket receipt"):
            cash_receipts.append(
                ReceiptCashPayment(
                    **_required_read_strings(
                        cash,
                        _RECEIPT_CASH_PAYMENT_FIELDS,
                        "receipt cash payment",
                    ),
                    total_approved_amount=_required_integer(cash, "h_tot_apv_amt", "receipt cash payment"),
                    raw=cash,
                )
            )
        items.append(
            TicketReceipt(
                **_required_read_strings(item, _TICKET_RECEIPT_FIELDS, "ticket receipt"),
                passenger_counts=(
                    _required_integer(item, "h_psg_type1_cnt", "ticket receipt"),
                    _required_integer(item, "h_psg_type2_cnt", "ticket receipt"),
                    _required_integer(item, "h_psg_type3_cnt", "ticket receipt"),
                ),
                received_amount=_required_integer(item, "h_rcvd_amt", "ticket receipt"),
                card_refund_amount=_required_integer(item, "h_crd_ret_amt", "ticket receipt"),
                refund_fee=_required_integer(item, "h_ret_fee", "ticket receipt"),
                refund_received_amount=_required_integer(item, "h_ret_rcvd_amt", "ticket receipt"),
                point_refund_amount=_required_integer(item, "h_xpoint_ret_amt", "ticket receipt"),
                payments=tuple(payments),
                cash_receipts=tuple(cash_receipts),
                raw=item,
            )
        )
    return TicketReceiptResponse(items=tuple(items), **_response_fields(raw))


def _parse_reservation_history_reservation(
    raw: Mapping[str, Any] | None,
) -> ReservationHistoryReservation | None:
    """ReservationViewOutJrnyInfo.java:55의 다섯 번째 생성자 인자입니다. @SerialName이 없어 전송 키는 보호돼 있으며 속성명 reservationOut을
    추정해 사용합니다."""
    if raw is None:
        return None
    tickets = tuple(
        ReservationHistoryTicket(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_TICKET_FIELDS,
                "reservation history ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "tkList")
    )
    original_tickets = tuple(
        ReservationHistoryOriginalTicket(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_ORIGINAL_TICKET_FIELDS,
                "reservation history original ticket",
            ),
            raw=item,
        )
        for item in _rows(raw, "orgTkList")
    )
    passengers = tuple(
        ReservationHistoryPassenger(
            **_nullable_scalar_fields(
                item,
                _RESERVATION_HISTORY_PASSENGER_FIELDS,
                "reservation history passenger",
            ),
            raw=item,
        )
        for item in _nested_rows(raw, "psg_infos", "psg_info")
    )
    return ReservationHistoryReservation(
        **_nullable_scalar_fields(
            raw,
            _RESERVATION_HISTORY_RESERVATION_FIELDS,
            "reservation history reservation",
        ),
        tickets=tickets,
        original_tickets=original_tickets,
        passengers=passengers,
        raw=raw,
    )


@_preserve_read_raw
def parse_reservation_history_response(
    raw: Mapping[str, Any],
) -> ReservationHistoryResponse:
    """예약 이력의 예약자 정보와 여정별 상세를 읽습니다(ReservationViewOut.java:64)."""
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"P100"}),
    )
    if empty:
        return ReservationHistoryResponse(**_response_fields(raw))
    guide_infos = _optional_mapping(raw, "guide_infos")
    guide_info = (
        _optional_scalar_string(guide_infos, "guide_info", "reservation history guide_infos")
        if guide_infos is not None
        else None
    )
    journeys: list[ReservationHistoryJourney] = []
    all_trains: list[ReservationHistoryTrain] = []
    for journey in _nested_rows(raw, "jrny_infos", "jrny_info"):
        trains: list[ReservationHistoryTrain] = []
        for train in _nested_rows(journey, "train_infos", "train_info"):
            history_train = ReservationHistoryTrain(
                **_nullable_scalar_fields(
                    train, _RESERVATION_HISTORY_TRAIN_FIELDS, "reservation history train"
                ),
                seat_count=_optional_integer(
                    train,
                    "h_tot_seat_cnt",
                    "reservation history train",
                ),
                standing_count=_optional_integer(
                    train,
                    "h_tot_stnd_cnt",
                    "reservation history train",
                ),
                raw=train,
            )
            trains.append(history_train)
            all_trains.append(history_train)
        service_infos = tuple(_nested_rows(journey, "srv_infos", "srv_info"))
        accompanying_infos = tuple(_nested_rows(journey, "acmp_infos", "acmp_info"))
        reservation = _parse_reservation_history_reservation(
            _optional_mapping(journey, "reservationOut"),
        )
        journeys.append(
            ReservationHistoryJourney(
                trains=tuple(trains),
                service_infos=service_infos,
                accompanying_infos=accompanying_infos,
                reservation=reservation,
                raw=journey,
            )
        )
    return ReservationHistoryResponse(
        **_nullable_scalar_fields(raw, _RESERVATION_HISTORY_TOP_FIELDS, "reservation history"),
        journey_count=_optional_scalar_string(raw, "h_jrny_cnt", "reservation history"),
        guide_info=guide_info,
        journeys=tuple(journeys),
        items=tuple(all_trains),
        **_response_fields(raw),
    )


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


@_preserve_read_raw
def parse_pass_schedule_response(
    raw: Mapping[str, Any],
) -> PassScheduleResponse:
    # WRG000000 안내문은 조회 결과 없음(assets/error_json.json:4173,14397). 비치명적 처리의 근거는 안내문·라이브 기록이며 앱 호출부의 평문 분기는 확인되지
    # 않았습니다.
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassScheduleMainInfo(
            **_nullable_scalar_fields(main_raw, _PASS_SCHEDULE_MAIN_FIELDS, "pass schedule main info"),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    schedules = []
    for schedule in _rows(raw, "schedule_info"):
        trains = tuple(
            PassScheduleTrain(
                **_nullable_scalar_fields(row, _PASS_SCHEDULE_TRAIN_FIELDS, "pass schedule train"),
                raw=row,
            )
            for row in _rows(
                schedule,
                "train_list",
            )
        )
        schedules.append(PassScheduleInfo(trains=trains, raw=schedule))
    return PassScheduleResponse(
        main_info=main_info,
        schedules=tuple(schedules),
        **_response_fields(raw),
    )


_KORAIL_POINT_SUMMARY_FIELDS = {
    "korail_point": "h_korail_point",
    "discount_coupon_count": "h_disc_coup_cnt",
    "delay_discount_count": "h_delay_cnt",
    "disability_flag": "h_hdcp_flg",
    "welfare_discount_class_name": "h_subt_dcs_cl_nm",
    "welfare_discount_class_code": "h_subt_dcs_cl_cd",
    "customer_lead_flag_name": "h_cust_lead_flg_nm",
    "phone_verified_flag": "h_cp_athn_flg",
    "email_verified_flag": "h_emil_athn_flg",
    "contact_channel_content": "h_cntc_chn_cont1",
    # MyXPointViewOut.java:43,53,54 — customer_lead_flag_name 의 플래그 짝과 disability_flag 의 유형 코드·이름입니다.
    "customer_lead_flag": "h_cust_lead_flg",
    "disability_type_code": "h_hdcp_tp_cd",
    "disability_type_name": "h_hdcp_tp_cd_nm",
    # 아래 넷의 네이버/카카오/구글/애플 **순서는 7.0.6 에서 미확인** 입니다 (read_models.KorailPointSummaryResponse 의 해당 주석 참고).
    "naver_linked_flag": "h_logn_tp_cd1",
    "kakao_linked_flag": "h_logn_tp_cd2",
    "google_linked_flag": "h_logn_tp_cd4",
    "apple_linked_flag": "h_logn_tp_cd5",
}

_MILEAGE_HISTORY_FIELDS = {
    "page_count": "pgCnt",
    "query_count": "qryCnt",
    "total_available_rail_point": "totAvlRailPontValNum",
    "total_available_rail_point_1": "totAvlRailPontValNum1",
    "total_available_affiliate_point": "totAvlAfltPontValNum",
    "total_accumulated_rail_point_1": "totAcmRailPontValNum1",
    "total_used_rail_point_1": "totUseRailPontValNum1",
    # railNowSavePontValNum1 은 DTO 미선언(AmtSpecOut.java:29-39, AmtSpecOutSpecInfo.java:29-35). 관측: KTX/RAIL_POINT
    # 의 모든 확인 페이지에 9자리 문자열로 있었으며 해당 계정에서는 totAcmRailPontValNum1 과 같았습니다.
    "expiring_point_value": "delPontValNum",
    "ktx_mileage_info": "ktxMlgInfo",
}

_MILEAGE_HISTORY_ENTRY_FIELDS = {
    "departure_date": "dptDt",
    "point_division_name": "pontDvNm",
    "accrual_division_name": "mlgAcmDvCdNm",
    "receipt_division_name": "rcpDvNm",
    "point_amount": "pontAmt",
    "saved_point_value": "savePontValNum",
    "settlement_amount": "stlAmt",
}


@_preserve_read_raw
def parse_korail_point_summary_response(
    raw: Mapping[str, Any],
) -> KorailPointSummaryResponse:
    _validate_strict_read_envelope(raw)
    return KorailPointSummaryResponse(
        # MyXPointViewOut.java:27-74 는 String 이고 표본도 48키 모두 문자열이었습니다.
        **_nullable_scalar_fields(raw, _KORAIL_POINT_SUMMARY_FIELDS, "korail point summary"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_mileage_history_response(
    raw: Mapping[str, Any],
) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = []
    for item in _rows(raw, "specList"):
        entries.append(
            MileageHistoryEntry(
                **_nullable_scalar_fields(
                    item,
                    _MILEAGE_HISTORY_ENTRY_FIELDS,
                    "mileage history entry",
                ),
                raw=item,
            )
        )
    return MileageHistoryResponse(
        **_nullable_scalar_fields(raw, _MILEAGE_HISTORY_FIELDS, "mileage history"),
        entries=tuple(entries),
        **_response_fields(raw),
    )


_DISCOUNT_CARD_USAGE_FIELDS = {
    "passenger_name": "custNm",
    "departure_station_name": "dptStnNm",
    "arrival_station_name": "arvStnNm",
    "run_date": "runDt1",
    "additional_user_flag": "apdUsrFlg",
    # NCardHistoryInfo.java:224 의 8속성 중 판매 식별자 3개도 보존합니다. 화면은 나머지 5개를
    # 소비합니다(NCardHistoryScreenKt.java:431,439,526,528,301).
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
}

_DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS = {
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "run_date": "runDt",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "departure_station_order": "dptStnConsOrdr",
    "arrival_station_order": "arvStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "arrival_run_order": "arvStnRunOrdr",
    "transfer_train_order_no": "chtnTrnOrdrNo",
    "price_class_code": "prcClCd",
    "settlement_car_type_code": "stlbCarTpCd",
    "settlement_train_class_code": "stlbTrnClsfCd",
    "commuter_price": "cmtrPrc",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "detour_code": "dturCd",
    "detour_name": "dturNm",
    "route_code": "routCd",
    # stationStringInfo 는 NCardScheduleItem.java:25-49 의 응답 필드가 아니므로 읽지 않습니다. 서버가 추가로 보낸 값은 raw 에 남으며 DTO 미선언만으로
    # 전송 부재를 보장하지 않습니다.
}


@_preserve_read_raw
def parse_discount_card_usage_response(
    raw: Mapping[str, Any],
) -> DiscountCardUsageListResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    items = []
    for item in _rows(raw, "tkUseList"):
        items.append(
            DiscountCardUsage(
                # 다른 조회의 숫자형 관측을 고려해 순번은 문자열·정수를 모두 허용합니다(이 경로는 미검증).
                **_nullable_scalar_fields(item, _DISCOUNT_CARD_USAGE_FIELDS, "discount card usage"),
                raw=item,
            )
        )
    return DiscountCardUsageListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_card_schedule_response(
    raw: Mapping[str, Any],
) -> DiscountCardScheduleResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    trains = []
    for item in _rows(raw, "trnScdlList"):
        trains.append(
            DiscountCardScheduleTrain(
                # 이 라우트의 라이브 근거는 없으며 파서 정책입니다.
                **_nullable_scalar_fields(
                    item, _DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS, "discount card schedule train"
                ),
                raw=item,
            )
        )
    # fllwPgExt 는 ScdlQryOut 필드이며 NCardScheduleOut.java:27-28 은 trnScdlList 만 선언합니다. 이 라우트의 페이지 신호는 미확인이라
    # following_page_exists 는 채우지 않습니다.
    return DiscountCardScheduleResponse(
        trains=tuple(trains),
        **_response_fields(raw),
    )


_MULTI_CHILD_FIELDS = {
    "birth_date": "btdt",
    "customer_family_name": "custFmlyNm",
    "discount_kind_code": "dcntKndCd",
    "family_sequence": "fmlySqno",
    "passenger_type_code": "psgTpCd",
    "passenger_type_name": "psgTpNm",
    "room_class_code": "psrmClCd",
    "requested_discount_kind_code": "rqDcntKndCd",
}

_CUSTOMER_TRIP_FIELDS = {
    "additional_seat_attribute_code": "addSeatAttCd",
    "adult_disabled_person_count": "adltHdcpPrnb",
    "adult_count": "adulCnt",
    "arrival_station_code": "arvStnCd",
    "arrival_station_name": "arvStnNm",
    "baby_accompanying_person_count": "babyAcpnPrnb",
    "changed_at": "chgDttm",
    "changed_by": "chgUsrId",
    "child_count": "chilCnt",
    "child_disabled_person_count": "chldHdcpPrnb",
    "customer_management_no": "custMgNo",
    "day_code": "dayCd",
    "direction_seat_attribute_group_code": "dirSeatAttGpCd",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "departure_station_code": "dptStnCd",
    "departure_station_name": "dptStnNm",
    "early_train_departure_time": "ectbTrnDptTm",
    "elderly_person_count": "edrPrnb",
    "included_flag": "inclFlg",
    "job_start_hour": "jobStHr",
    "location_seat_attribute_group_code": "locSeatAttGpCd",
    "media_division_code": "medDvCd",
    "room_class_code": "psrmClCd",
    "passenger_total": "ptwtTtl",
    "registered_at": "regDttm",
    "registration_sequence": "regSqno",
    "registered_by": "regUsrId",
    "trip_day_no": "tripDno",
    "train_classification_code": "trnClsfCd",
    "train_connection_flag": "trnCnecFlg",
    "train_group_code": "trnGpCd",
    "usage_day_no": "utlDno",
    # CustTripInfo.java:48 의 별칭 없는 속성명에서 키를 추정합니다. 보호 descriptor 는 미확인입니다.
    "goods_no": "gdNo",
}

_MAAS_DETAIL_FIELDS = {
    "additional_service_division_code": "addSrvDvCd",
    "additional_service_goods_code": "addSrvGdCd",
    "additional_service_id": "addSrvId",
    "marketing_entity_id": "addSrvMrkEntId",
    "marketing_entity_name": "addSrvMrkEntNm",
    "additional_service_name": "addSrvNm",
    "progress_status_code": "addSrvPrgSttCd",
    "request_no": "addSrvReqNo",
    "passenger_reference_content": "cgPsRefAtclCont",
    "partner_reservation_no": "coptEntRsvNo",
    "delivery_close_time": "dlivPsbClsTm",
    "delivery_start_time": "dlivPsbStTm",
    "lead_message_1": "leadMsgCont1",
    "lead_message_2": "leadMsgCont2",
    "pnr_no": "pnrNo",
    "request_date": "reqDt",
    "request_quantity": "reqQnty",
    "reservation_station_code_name": "rsStnCdNm",
    "reservation_specification_url": "rsvSpecUrl",
    "usage_close_date": "utlClsDt",
    "usage_start_date": "utlStDt",
}

_MAAS_DETAIL_INFO_FIELDS = {
    "additional_service_request_no": "addSrvReqNo",
    "booking_time": "bookTime",
    "branch_name": "branchName",
    "partner_name": "coptEntName",
    "delivery_datetime": "deliveryDtm",
    "drop_times": "dropTimes",
    "dropoff_name": "dropoffName",
    "image": "image",
    "name": "name",
    "option_name": "optionName",
    "pickup_name": "pickupName",
    "pickup_place": "pickupPlace",
    "pickup_times": "pickupTimes",
    "reservation_date": "reserveDt",
    "return_datetime": "returnDttm",
    "start_datetime": "startDttm",
    "cancel_deadline_date": "strCncDlnDt",
    "cancel_return_amount": "strCncRetAmt",
    "cancel_return_fee": "strCncRetFee",
    "goods_sequence": "strGdSqno",
    "intermediate_value": "strInt11",
    "received_amount": "strRcvdAmt",
    "reservation_status_name": "strRsvSttNm",
    "reservation_passenger_name": "strRsvpsnm",
    "settlement_deadline_date": "strStlDlnDt",
    "settlement_deadline_datetime": "strStlDlnDttm",
    "settlement_status_code": "strStlSttCd",
    "settlement_status_name": "strStlSttNm",
    "total_settlement_amount": "strTotStlAmt",
    "usage_period_content": "strUtlTrmCont",
}


@_preserve_read_raw
def parse_multi_child_discount_target_response(
    raw: Mapping[str, Any],
) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = []
    for item in _rows(raw, "fmlyList"):
        targets.append(
            MultiChildDiscountTarget(
                **_nullable_string_fields(
                    item,
                    _MULTI_CHILD_FIELDS,
                ),
                raw=item,
            )
        )
    return MultiChildDiscountTargetResponse(
        targets=tuple(targets),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_customer_trip_info_response(
    raw: Mapping[str, Any],
) -> CustomerTripInfoResponse:
    _validate_strict_read_envelope(raw)
    trips = []
    for item in _required_read_rows(raw, "mainList", "customer trip info"):
        trips.append(
            CustomerTripInfo(
                **_nullable_scalar_fields(item, _CUSTOMER_TRIP_FIELDS, "customer trip info"),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
        **_response_fields(raw),
    )


def _parse_add_srv_item(
    item: Mapping[str, Any],
    context: str,
    info_context: str,
) -> MaasServiceDetail:
    """MaaS 상세와 승차권의 부가서비스를 같은 모델로 읽습니다 (AddSrvItem.java:28-49, MaasDetailOut.java:27,
    MyTicketListOutReservation.java:39). @SerialName 이 없고 serializer 이름이 보호돼 있어 전송 키는 속성명에 따른 추정입니다."""
    info_raw = _optional_mapping(item, "detailInfo")
    detail_info = None
    if info_raw is not None:
        detail_info = MaasServiceDetailInfo(
            **_nullable_scalar_fields(info_raw, _MAAS_DETAIL_INFO_FIELDS, info_context),
            entity_one=tuple(_rows(info_raw, "entityOne")),
            raw=info_raw,
        )
    return MaasServiceDetail(
        **_nullable_scalar_fields(item, _MAAS_DETAIL_FIELDS, context),
        detail_info=detail_info,
        raw=item,
    )


def _optional_add_srv_item(
    data: Mapping[str, Any],
    key: str,
    item_context: str,
    info_context: str,
) -> MaasServiceDetail | None:
    """객체가 아니면 ``None``."""
    item = _optional_mapping(data, key)
    if item is None:
        return None
    return _parse_add_srv_item(item, item_context, info_context)


@_preserve_read_raw
def parse_maas_cancel_fee_response(raw: Mapping[str, Any]) -> MaasCancelFeeResponse:
    """지원하지 않는 부가서비스 환불 수수료 응답을 읽습니다. maas.cncFee.do 응답. cncRetFee 는 선택 스칼라로 읽습니다(MaasCancelFeeOut.java)."""
    _validate_envelope(raw)
    return MaasCancelFeeResponse(
        cancel_fee=_optional_scalar_string(raw, "cncRetFee", "MaaS cancel fee"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for item in _rows(raw, "addSrvList"):
        details.append(_parse_add_srv_item(item, "MaaS service detail", "MaaS detail info"))
    return MaasServiceDetailListResponse(
        details=tuple(details),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_trip_change_date_response(
    raw: Mapping[str, Any],
) -> TripChangeDateResponse:
    _validate_strict_read_envelope(raw)
    dates = raw.get("tripChgDates")
    if not isinstance(dates, list):
        raise KorailProtocolError("KORAIL tripChgDates must be a string list")
    normalized_dates = []
    for value in dates:
        date = _strict_scalar_string({"tripChgDates": value}, "tripChgDates", "trip change dates")
        if date is None:
            raise KorailProtocolError("KORAIL tripChgDates must not contain null")
        normalized_dates.append(date)
    # 응답은 복수형 tripChgDates 입니다(TipChgDateInquiryOut.java:28-30). 단수형 tripChgDate 는 요청
    # 필드(TipChgDateInquiryIn.java:29)이므로 응답 별칭으로 쓰지 않습니다.
    return TripChangeDateResponse(
        last_run_date=_optional_scalar_string(raw, "lastRunDt"),
        trip_change_dates=tuple(normalized_dates),
        **_response_fields(raw),
    )


def _primitive_json_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int | None:
    """Kotlin Int 값을 읽되 누락은 0, 잘못된 형식은 None으로 처리합니다."""
    if data.get(key) is None:
        return 0
    return _optional_integer(data, key, context)


@_preserve_read_raw
def parse_commuter_info_response(
    raw: Mapping[str, Any],
) -> CommuterInfoResponse:
    _validate_strict_read_envelope(raw)
    passenger_options = []
    for item in _rows(raw, "psgList"):
        passenger_options.append(
            CommuterPassengerOption(
                commuter_usage_age_code=_optional_scalar_string(
                    item,
                    "cmtrUtlAgeCd",
                ),
                common_code_name=_optional_scalar_string(
                    item,
                    "comnCdNm",
                ),
                # Psg.java:30-31 의 연령 범위는 int 입니다.
                customer_age_from=_primitive_json_integer(
                    item,
                    "custAgeFrom",
                    "commuter passenger option",
                ),
                customer_age_to=_primitive_json_integer(
                    item,
                    "custAgeTo",
                    "commuter passenger option",
                ),
                passenger_count_from=_primitive_json_integer(
                    item,
                    "psgPrnbFrom",
                    "commuter passenger option",
                ),
                passenger_count_to=_primitive_json_integer(
                    item,
                    "psgPrnbTo",
                    "commuter passenger option",
                ),
                raw=item,
            )
        )
    return CommuterInfoResponse(
        **_nullable_string_fields(
            raw,
            {
                "additional_service_goods_flag": "addSrvGdFlg",
                "companion_flag": "cmpaFlg",
                "commuter_kind_code": "cmtrKndCd",
                "commuter_usage_age_code": "cmtrUtlAgeCd",
                "menu_id": "menuId",
                "popup_message": "poppMsg",
                "promotion_message": "prmoMsg",
                "promotion_url": "prmoUrl",
                "seat_attribute_code": "seatAttCd1",
            },
        ),
        available_passenger_count_from=_primitive_json_integer(
            raw,
            "avlPrnbFrom",
            "commuter info",
        ),
        available_passenger_count_to=_primitive_json_integer(
            raw,
            "avlPrnbTo",
            "commuter info",
        ),
        passenger_options=tuple(passenger_options),
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


_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
    "return_password": "tkRetPwd",
}

_PBP_ACCEPTANCE_JOURNEY_FIELDS = {
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "journey_type_code": "jrnyTpCd",
    "member_division_name": "mbDvNm",
    "acceptance_kind_name": "pbpAcepKndNm",
    "pbp_reservation_no": "pbpRsvNo",
    "registered_date": "regDt",
    "withdrawal_possible_flag": "wdrwPsbFlg",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_SEAT_FIELDS = {
    "passenger_type_division_name": "psgTpDvNm",
    "room_class_code": "psrmClCd",
    "room_class_name": "psrmClNm",
    "seat_no": "seatNo",
}

_RECENT_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_flag": "acepCustMgFlg",
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "acceptance_customer_phone_2": "acepCustTeln2",
    "member_card_no": "mbCrdNo",
}


@_preserve_read_raw
def parse_delivery_recipient_response(
    raw: Mapping[str, Any],
) -> DeliveryRecipientResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    return DeliveryRecipientResponse(
        **_required_read_strings(
            raw,
            _DELIVERY_RECIPIENT_FIELDS,
            "delivery recipient",
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_ticket_duplication_check_response(
    raw: Mapping[str, Any],
) -> TicketDuplicationCheckResponse:
    _validate_strict_read_envelope(raw)
    return TicketDuplicationCheckResponse(
        # rsvCnt 는 String 선언입니다(TicketDupCheckOut.java:28,50).
        reservation_count=_optional_scalar_string(
            raw,
            "rsvCnt",
            "ticket duplication check",
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pbp_acceptance_specification_response(
    raw: Mapping[str, Any],
) -> PbpAcceptanceSpecificationResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _required_read_rows(raw, "tkList", "PBP acceptance"):
        journeys = []
        for journey in _required_read_rows(ticket, "jrnyList", "PBP ticket"):
            seats = []
            for seat in _required_read_rows(journey, "seatList", "PBP journey"):
                seats.append(
                    PbpAcceptanceSeat(
                        # Seat.java:53-59 는 마스크 31 로 다섯 필드 누락을 거절하므로 필수로 읽습니다.
                        **_required_read_strings(seat, _PBP_ACCEPTANCE_SEAT_FIELDS, "PBP acceptance seat"),
                        # scarNo 는 int 선언(Seat.java:35,53). 앱 Json 설정 리터럴이 보호돼 있어 인용된 설정만으로 quoted Int 허용 이유는
                        # 확정하지 않습니다 (NetworkServiceKt.java:15-31).
                        car_no=_required_integer(
                            seat,
                            "scarNo",
                            "PBP acceptance seat",
                        ),
                        raw=seat,
                    )
                )
            journeys.append(
                PbpAcceptanceJourney(
                    **_required_read_strings(
                        journey,
                        _PBP_ACCEPTANCE_JOURNEY_FIELDS,
                        "PBP journey",
                    ),
                    seats=tuple(seats),
                    raw=journey,
                )
            )
        tickets.append(
            PbpAcceptanceTicket(
                **_required_read_strings(
                    ticket,
                    _PBP_ACCEPTANCE_TICKET_FIELDS,
                    "PBP ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return PbpAcceptanceSpecificationResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_recent_delivery_history_response(
    raw: Mapping[str, Any],
) -> RecentDeliveryHistoryResponse:
    _validate_strict_read_envelope(raw)
    # RecentDeliveryHistoryOut.java:51-57 의 마스크 24 는 두 키를 필수로 둡니다. 실서버 응답에는 acepList 가 있고 chgePbpRsvNo 만 없었으므로
    # chgePbpRsvNo 만 선택으로 읽습니다. acepList 는 nullable List 라 null 은 빈 목록입니다.
    if "acepList" not in raw:
        raise KorailProtocolError("KORAIL recent delivery history field acepList is required")
    recipients = []
    for recipient in (
        _required_read_rows(raw, "acepList", "recent delivery history") if raw["acepList"] is not None else ()
    ):
        recipients.append(
            RecentDeliveryRecipient(
                **_required_read_strings(
                    recipient,
                    _RECENT_DELIVERY_RECIPIENT_FIELDS,
                    "recent delivery recipient",
                ),
                raw=recipient,
            )
        )
    return RecentDeliveryHistoryResponse(
        changed_acceptance_reservation_no=_optional_scalar_string(
            raw, "chgePbpRsvNo", "recent delivery history"
        ),
        recipients=tuple(recipients),
        **_response_fields(raw),
    )


_RESERVATION_SEAT_DETAIL_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "room_class_code": "h_psrm_cl_cd",
    "room_class_name": "h_psrm_cl_nm",
    # h_psg_tp_dv_nm 은 앱 내장 응답 예시에 존재(BasketTicketDataKt.java:44)하나 ReservationOutSeatInfo.java:81 의 @SerialName
    # 에는 없습니다. 한 계정 8좌석에서 확인했지만 항상 전송된다는 보장은 없습니다.
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_dv_nm",
    "received_amount": "h_rcvd_amt",
    "seat_price": "h_seat_prc",
    "seat_fare": "h_seat_fare",
    # ReservationOutSeatInfo.java:269 — @SerialName("h_tot_disc_amt").
    "total_discount_amount": "h_tot_disc_amt",
    "seat_group_name": "h_sgr_nm",
}

_RESERVATION_DETAIL_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "reservation_change_no": "h_rsv_chg_no",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_time": "h_arv_tm",
    # 도착일 h_arv_dt 는 도착시각과 별개입니다(ReservationOutJrnyInfo.java:86,305).
    "arrival_date": "h_arv_dt",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
}

_TICKET_RESERVATION_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "window_no": "h_wct_no",
    "journey_count": "h_jrny_cnt",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "payment_flag": "h_payment_flg",
}


@_preserve_read_raw
def parse_ticket_reservation_detail_response(
    raw: Mapping[str, Any],
) -> TicketReservationDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for journey in _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
    ):
        seats = []
        for seat in _nested_rows(
            journey,
            "seat_infos",
            "seat_info",
        ):
            seats.append(
                ReservationSeatDetail(
                    **_nullable_scalar_fields(seat, _RESERVATION_SEAT_DETAIL_FIELDS, "reservation seat detail"),
                    raw=seat,
                )
            )
        journeys.append(
            ReservationDetailJourney(
                **_nullable_scalar_fields(
                    journey, _RESERVATION_DETAIL_JOURNEY_FIELDS, "reservation detail journey"
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    return TicketReservationDetailResponse(
        **_nullable_scalar_fields(
            raw,
            _TICKET_RESERVATION_DETAIL_FIELDS,
            "ticket reservation detail",
        ),
        journeys=tuple(journeys),
        **_nullable_scalar_fields(raw, RESERVATION_OUT_EXTRA_FIELDS, "ticket reservation detail"),
        passengers=_reservation_passengers(raw),
        **_response_fields(raw),
    )


_REFUND_COMMISSION_FIELDS = {
    "refund_amount": "ret_amt",
    "refund_fee": "ret_fee",
    "proceed_possible_flag": "prg_psb_flg",
    "ticket_return_times_division_code": "tk_ret_tms_dv_cd",
    "usable_mileage": "use_psb_mlg_num",
    "secondary_message_code": "h_msg_cd2",
    "secondary_message_text": "h_msg_txt2",
}


@_preserve_read_raw
def parse_refund_commission_response(
    raw: Mapping[str, Any],
) -> RefundCommissionResponse:
    _validate_strict_read_envelope(raw)
    return RefundCommissionResponse(
        **_nullable_scalar_fields(
            raw,
            _REFUND_COMMISSION_FIELDS,
            "refund commission",
        ),
        **_response_fields(raw),
    )


_REFUND_TICKET_SEAT_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "buyer_name": "h_buy_ps_nm",
    "checkin_status_code": "h_chckn_stt_cd",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_name": "h_dcnt_knd_nm",
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_nm",
    "seat_group_name": "h_sgr_nm",
}

_REFUND_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
    "room_class_name": "h_psrm_cl_nm",
    "platform_no": "h_plf_no",
}

_REFUND_TICKET_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "sale_date": "h_sale_dt",
    "sale_time": "h_sale_tm",
    "window_name": "h_wct_nm",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "original_window_no": "h_orgtk_wct_no",
    "original_sale_sequence": "h_orgtk_sale_sqno",
    "original_return_password": "h_orgtk_ret_pwd",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    "refund_possible_flag": "retPsbFlg",
    "return_flag": "h_ret_flg",
    "total_fare_amount": "h_tot_fare_amt",
    "total_discount_amount": "h_tot_disc_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "train_running_flag": "h_trn_running_flg",
    # 탑승자 이름·생년월일 요약이며 동반자나 psgNmList 와 별개입니다(TicketDetailOut.java:410,418).
    "passenger_name": "h_abrd_ps_nm",
    "passenger_birth_date": "s_brth",
    "companion_name": "h_compa_nm",
    "companion_birth_date": "h_compa_brth",
    # 목록의 PBP 대상 키는 MyTicketListOutTicket.java:92,300에 있으며 상세의 명시적 키에는 없습니다 (TicketDetailOut.java:117). 앱의 주입은
    # TicketDetailOut.java:65,1936과 MyTicketBaseViewModel.java:769을 따릅니다.
    "delay_flag": "h_dlay_flg",
    "delay_ticket_flag": "h_dlay_tk_flg",
    # mlgSaveFlg/mlgSaveTgt 는 TicketDetailOut.java:39-91,117 에 없지만 서버 상세 40/40 표본에는 빈 문자열로 있었습니다. 타입화하지 않고 raw 에
    # 보존합니다.
    "additional_service_flag": "addSrvFlg",
    "additional_service_cancel": "addSrvCancel",
}


_DISCOUNT_CARD_SECTION_FIELDS = {
    "departure_station_name": "dptRsStnNm",
    "arrival_station_name": "arvRsStnNm",
    "journey_sequence": "jrnySqno",
    "journey_type_code": "jrnyTpCd",
    "train_group_code": "trnGpCd",
    "detour_division_name": "stlbDturDvNm",
}


def _discount_card_on_ticket(
    raw: Mapping[str, Any],
) -> DiscountCardOnTicket | None:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 상세의 선택 dcnt_crd_info(TicketDetailOut.java:438)."""
    info = _optional_mapping(raw, "dcnt_crd_info")
    if info is None:
        return None
    sections = []
    for item in _rows(
        info,
        "appSegList",
    ):
        sections.append(
            DiscountCardSection(
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_SECTION_FIELDS,
                    "discount card section",
                ),
                raw=item,
            )
        )
    return DiscountCardOnTicket(
        card_no=_optional_scalar_string(
            info,
            "h_dcnt_crd_no",
            "discount card info",
        ),
        term_extension_possible_flag=_optional_scalar_string(
            info,
            "h_dcnt_crd_trm_extn_psb_flg",
        ),
        sections=tuple(sections),
        raw=info,
    )


@_preserve_read_raw
def parse_refund_ticket_detail_response(
    raw: Mapping[str, Any],
) -> RefundTicketDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for journey in _nested_rows(
        raw,
        "ticket_infos",
        "ticket_info",
    ):
        seats = []
        for seat in _rows(
            journey,
            "tk_seat_info",
        ):
            seats.append(
                RefundTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _REFUND_TICKET_SEAT_FIELDS,
                        "refund ticket seat",
                    ),
                    raw=seat,
                )
            )
        journeys.append(
            RefundTicketJourney(
                **_nullable_scalar_fields(
                    journey,
                    _REFUND_TICKET_JOURNEY_FIELDS,
                    "refund ticket journey",
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    detail_fields = _nullable_scalar_fields(raw, _REFUND_TICKET_DETAIL_FIELDS, "refund ticket detail")
    # pbpAcepTgtFlg는 보호된 전송 키 대신 속성명으로 읽는 후보입니다(TicketDetailOut.java:65). 40응답에는 없었습니다.
    if "pbpAcepTgtFlg" in raw:
        detail_fields["pbp_acceptance_target_flag"] = _optional_scalar_string(
            raw, "pbpAcepTgtFlg", "refund ticket detail"
        )
    # h_qrcode 의 명시적 별칭: TicketDetailOut.java:478.
    qr_code = _optional_scalar_string(raw, "h_qrcode", "refund ticket detail")
    # psgNmList/seatTicketList/limousine/dtlList 는 명시적 별칭이 없어 속성명으로 추정합니다. 보호된 descriptor 를 확인한 전송 키라는 뜻은 아닙니다.
    passenger_names = tuple(_rows(raw, "psgNmList"))
    seat_tickets = tuple(_rows(raw, "seatTicketList"))
    limousine = _optional_mapping(raw, "limousine")
    delay_details = tuple(_rows(raw, "dtlList"))
    return RefundTicketDetailResponse(
        **detail_fields,
        qr_code=qr_code,
        passenger_names=passenger_names,
        seat_tickets=seat_tickets,
        limousine=limousine,
        delay_details=delay_details,
        journeys=tuple(journeys),
        discount_card=_discount_card_on_ticket(raw),
        **_response_fields(raw),
    )


_SELF_SEAT_CHANGE_STATION_FIELDS = {
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "departure_construction_order": "dptStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "general_remaining_seats": "gnrmRestSeatNum",
    "special_remaining_seats": "sprmRestSeatNum",
}
_SELF_SEAT_CHANGE_REASON_FIELDS = {
    "query_code": "qryCode",
    "query_order": "qryOrdr",
    "reason_text": "frcSaleRsnCont",
}
_SELF_SEAT_CHANGE_INFO_FIELDS = {
    "train_no": "trnNo",
    "train_class_code": "trnClsfCd",
    "train_class_name": "trnClsfNm",
    "train_group_code": "trnGpCd",
    "train_group_name": "trnGpNm",
    "run_date": "runDt",
    "general_reservation_possible_code": "gnrmRsvPsbCd",
    "special_reservation_possible_code": "sprmRsvPsbCd",
    "change_before_departure_construction_order": "chgBfDptStnConsOrdr",
    "change_before_arrival_construction_order": "chgBfArvStnConsOrdr",
    "existing_departure_run_order": "exsDptStnRunOrdr",
    "existing_arrival_run_order": "exsArvStnRunOrdr",
}


@_preserve_read_raw
def parse_self_seat_change_info_response(
    raw: Mapping[str, Any],
) -> SelfSeatChangeInfoResponse:
    """DTO: SeatAvailabilityOut.java:28-42, ChgStnInfo.java:21-35, ChgRsnInfo.java:21-24. 라우트:
    NetworkApi.java:806-808."""
    _validate_strict_read_envelope(raw)
    stations = tuple(
        SelfSeatChangeStation(
            **_nullable_scalar_fields(
                station,
                _SELF_SEAT_CHANGE_STATION_FIELDS,
                "self seat change station",
            ),
            raw=station,
        )
        for station in (
            value
            for value in _rows(
                raw,
                "chgStnList",
            )
        )
    )
    reasons = tuple(
        SelfSeatChangeReason(
            **_nullable_scalar_fields(
                reason,
                _SELF_SEAT_CHANGE_REASON_FIELDS,
                "self seat change reason",
            ),
            raw=reason,
        )
        for reason in (
            value
            for value in _rows(
                raw,
                "chgRsnList",
            )
        )
    )
    return SelfSeatChangeInfoResponse(
        **_nullable_scalar_fields(
            raw,
            _SELF_SEAT_CHANGE_INFO_FIELDS,
            "self seat change info",
        ),
        stations=stations,
        reasons=reasons,
        **_response_fields(raw),
    )


_ORIGINAL_TICKET_SEAT_FIELDS = {
    "passenger_sequence": "psgSqno",
    "assign_sequence": "asgnSqno",
    "passenger_type_code": "psgTpDvCd",
    "room_class_code": "psrmClCd",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "seat_count": "seatNum",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "requested_seat_attribute_code": "rqSeatAttCd",
    "direction_seat_attribute_code": "dirSeatAttCd",
    "location_seat_attribute_code": "locSeatAttCd",
    "smoking_seat_attribute_code": "smkSeatAttCd",
    "additional_seat_attribute_code": "addSeatAttCd",
    "etc_seat_attribute_code": "etcSeatAttCd",
}
_ORIGINAL_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "jrnySqno",
    "journey_order": "jrnyOrdr",
    "journey_type_code": "jrnyTpCd",
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_construction_order": "dptStnConsOrdr",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "arrival_construction_order": "arvStnConsOrdr",
    "goods_no": "gdNo",
    "total_seat_count": "totSeatNum",
    "total_standing_count": "totStndNum",
    "general_change_allowed_flag": "genChgAllwFlg",
    "single_ticket_flag": "snglTkFlg",
}
_ORIGINAL_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "ticket_kind_code": "tkKndCd",
    "original_sale_datetime": "ogtkSaleDt",
    "original_window_no": "ogtkSaleWctNo",
    "original_sale_sequence": "ogtkSaleSqno",
    "original_return_password": "ogtkRetPwd",
    "member_card_no": "mbCrdNo",
    "adult_count": "adulCnt",
    "child_count": "chilCnt",
    "group_discount_count": "grpDcntCnt",
    "passenger_type_division_code": "psgTpDvCd",
    "received_amount": "rcvdAmt",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "change_sale_transaction_no": "chgSaleTno",
    "sms_send_flag": "smsSndFlg",
    "forced_sale_reason_text": "frcSaleRsnCont",
}


@_preserve_read_raw
def parse_original_ticket_inquiry_response(
    raw: Mapping[str, Any],
) -> OriginalTicketInquiryResponse:
    """원표의 OrgTk→JrnyInfo→SeatInfo는 대리수령의 Jrny/Seat와 다른 모델입니다(OgTicketInquiryOut.java:27; OrgTk.java:38;
    JrnyInfo.java:58)."""
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _rows(raw, "orgTkList"):
        journeys = []
        for journey in _rows(
            ticket,
            "jrnyList",
        ):
            seats = tuple(
                OriginalTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _ORIGINAL_TICKET_SEAT_FIELDS,
                        "original ticket seat",
                    ),
                    raw=seat,
                )
                for seat in (
                    seat_value
                    for seat_value in _rows(
                        journey,
                        "seatList",
                    )
                )
            )
            journeys.append(
                OriginalTicketJourney(
                    **_nullable_scalar_fields(
                        journey,
                        _ORIGINAL_TICKET_JOURNEY_FIELDS,
                        "original ticket journey",
                    ),
                    seats=seats,
                    raw=journey,
                )
            )
        tickets.append(
            OriginalTicket(
                **_nullable_scalar_fields(
                    ticket,
                    _ORIGINAL_TICKET_FIELDS,
                    "original ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return OriginalTicketInquiryResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


def _optional_read_rows(data: Mapping[str, Any], key: str, context: str) -> list[Mapping[str, Any]]:
    """선택·nullable 객체 목록을 읽습니다. 누락·null 은 빈 목록이고, 목록이 아니거나 객체가 아닌 행은 거절합니다."""
    if data.get(key) is None:
        return []
    return _required_read_rows(data, key, context)


_DELAY_CERTIFICATE_FIELDS = {
    "run_day": "runDay",
    "train_no": "trnNo",
    "departure_station_code": "dptRsStnCd",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "delay_arrival_flag": "dlayArvFlg",
    "delay_minutes": "trnDlayTm",
}


@_preserve_read_raw
def parse_delay_certificate_response(raw: Mapping[str, Any]) -> DelayCertificateResponse:
    _validate_strict_read_envelope(raw)
    delays = []
    for row in _optional_read_rows(raw, "dlayList", "delay certificate"):
        # DelayCertificate.java:57-60 의 마스크는 runDt 도 필수로 두지만 실서버의 지연 승차권 2장은 runDt 없이 나머지 7키만 돌려줬습니다.
        delays.append(
            DelayCertificateRow(
                **_required_read_strings(row, _DELAY_CERTIFICATE_FIELDS, "delay certificate"),
                run_date=_optional_scalar_string(row, "runDt", "delay certificate"),
                raw=row,
            )
        )
    return DelayCertificateResponse(delays=tuple(delays), **_response_fields(raw))


@_preserve_read_raw
def parse_delay_return_receipt_response(raw: Mapping[str, Any]) -> DelayReturnReceiptResponse:
    _validate_strict_read_envelope(raw)
    return DelayReturnReceiptResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "return_date": "retDt",
                "payment_method_name": "dlayFarePymtMtdNm",
                "return_amount": "dlayFareRetAmt",
            },
            "delay return receipt",
        ),
        **_response_fields(raw),
    )


_TRAVEL_PRODUCT_FIELDS = {
    "goods_no": "gdNo",
    "name": "gdNm",
    "area_code": "gdTripArCd",
    "area_name": "gdTripArNm",
    "event_start_date": "evtStDt",
    "event_end_date": "evtClsDt",
    "company_name": "entNm",
    "info_url": "gdInfoUrlAdr",
    "representative_fare": "gdRepFare",
    "description": "ln1DscCont",
    "standard_clause_1": "gdStdrClauValCont1",
    "standard_clause_2": "gdStdrClauValCont2",
}


@_preserve_read_raw
def parse_travel_product_search_response(raw: Mapping[str, Any]) -> TravelProductSearchResponse:
    _validate_strict_read_envelope(raw)
    listing = raw.get("lst")
    if listing is None:
        return TravelProductSearchResponse(**_response_fields(raw))
    if not isinstance(listing, Mapping):
        raise KorailProtocolError("KORAIL travel product search field lst must be an object or null")
    products = tuple(
        TravelProduct(**_nullable_scalar_fields(row, _TRAVEL_PRODUCT_FIELDS, "travel product"), raw=row)
        for row in _optional_read_rows(listing, "gdList", "travel product search")
    )
    return TravelProductSearchResponse(
        products=products,
        query_count=_optional_scalar_string(listing, "qryCnt", "travel product search"),
        page_count=_optional_scalar_string(listing, "pgCnt", "travel product search"),
        **_response_fields(raw),
    )


_SELF_CHECKIN_SEAT_FIELDS = {
    "pnr_no": "pnrNo",
    "journey_sequence": "jrnySqno",
    "assignment_sequence": "asgnSqno",
    "run_date": "runDt",
    "train_no": "trnNo",
    "departure_construction_order": "dptStnConsOrdr",
    "departure_station_code": "dptRsStnCd",
    "arrival_construction_order": "arvStnConsOrdr",
    "arrival_station_code": "arvRsStnCd",
    "ticket_kind_code": "tkKndCd",
    "train_group_code": "trnGpCd",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "departure_datetime": "dptDttm",
    "arrival_datetime": "arvDttm",
    "cps_no": "cpsNo",
}


@_preserve_read_raw
def parse_self_checkin_seat_check_response(raw: Mapping[str, Any]) -> SelfCheckInSeatCheckResponse:
    _validate_strict_read_envelope(raw)
    if "consList" not in raw:
        raise KorailProtocolError("KORAIL self check-in seat check field consList is required")
    seats = tuple(
        SelfCheckInSeat(**_required_read_strings(row, _SELF_CHECKIN_SEAT_FIELDS, "self check-in seat"), raw=row)
        for row in _optional_read_rows(raw, "consList", "self check-in seat check")
    )
    return SelfCheckInSeatCheckResponse(seats=seats, **_response_fields(raw))


_SELF_CHECKIN_INFO_FIELDS = {
    "pnr_no": "pnrNo",
    "train_no": "trnNo",
    "departure_station_name": "dptRsStnNm",
    "departure_time": "dptTmQb",
    "arrival_station_name": "arvRsStnNm",
    "arrival_time": "arvTmQb",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "train_class_name": "stlbTrnClsfNm",
    "checkin_division_code": "chcknDvCd",
}


@_preserve_read_raw
def parse_self_checkin_info_response(raw: Mapping[str, Any]) -> SelfCheckInInfoResponse:
    _validate_strict_read_envelope(raw)
    values: dict[str, Any] = {}
    for attribute, key in _SELF_CHECKIN_INFO_FIELDS.items():
        # 열 키 모두 필수이지만 값은 nullable 입니다(SelfCheckInInfoOut.java:56-59).
        if key not in raw:
            raise KorailProtocolError(f"KORAIL self check-in info field {key} is required")
        values[attribute] = _strict_scalar_string(raw, key, "self check-in info")
    return SelfCheckInInfoResponse(**values, **_response_fields(raw))
