# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정·마일리지 조회 응답을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..._core.parsing import (
    _nested_rows,
    _nullable_scalar_fields,
    _optional_bool,
    _optional_integer,
    _optional_mapping,
    _optional_read_rows,
    _optional_scalar_string,
    _present_strings,
    _preserve_read_raw,
    _required_integer,
    _required_read_rows,
    _required_read_strings,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from ...errors import KorailProtocolError
from ..airport_bus.parsers import _optional_add_srv_item
from ..common.models import BaseKorailResponse
from .models import (
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayCertificateResponse,
    DelayCertificateRow,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DelayReturnReceiptResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    KorailPointSummaryResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    ReceiptCashPayment,
    ReceiptPayment,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    TicketListReservation,
    TicketListResponse,
    TicketListTicket,
    TicketListTrain,
    TicketReceipt,
    TicketReceiptResponse,
    TripChangeDateResponse,
)

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
            **_nullable_scalar_fields(row, _DELAY_DISCOUNT_TICKET_FIELDS),
            **_nullable_scalar_fields(row, _DELAY_DISCOUNT_TICKET_SCALAR_FIELDS),
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
                **_nullable_scalar_fields(item, _DISCOUNT_COUPON_FIELDS),
                remarks=_present_strings(item, ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont")),
                raw=item,
            )
        )
    return DiscountCouponListResponse(
        items=tuple(items),
        current_page=_optional_integer(raw, "h_page_no"),
        total_pages=_optional_integer(raw, "h_tot_page_cnt"),
        total_count=_optional_scalar_string(raw, "h_tot_cnt"),
        row_count=_optional_scalar_string(raw, "h_row_cnt"),
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
    # 아래 넷의 네이버/카카오/구글/애플 **순서는 7.0.6 에서 미확인** 입니다 (tickets/models.py 의 KorailPointSummaryResponse 해당 주석 참고).
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
        **_nullable_scalar_fields(raw, _KORAIL_POINT_SUMMARY_FIELDS),
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
                ),
                raw=item,
            )
        )
    return MileageHistoryResponse(
        **_nullable_scalar_fields(raw, _MILEAGE_HISTORY_FIELDS),
        entries=tuple(entries),
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


@_preserve_read_raw
def parse_multi_child_discount_target_response(
    raw: Mapping[str, Any],
) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = []
    for item in _rows(raw, "fmlyList"):
        targets.append(
            MultiChildDiscountTarget(
                **_nullable_scalar_fields(
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
                **_nullable_scalar_fields(item, _CUSTOMER_TRIP_FIELDS),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
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
                    **_nullable_scalar_fields(ticket_raw, _TICKET_LIST_TICKET_FIELDS),
                    train_info=train_info,
                    raw=ticket_raw,
                    trains=tuple(
                        TicketListTrain(
                            **_nullable_scalar_fields(row, _TICKET_LIST_TRAIN_FIELDS),
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
                ),
                seat_assign_count=_optional_integer(reservation_raw, "seatAssignCount"),
                ticket_status=_optional_scalar_string(reservation_raw, "ticketStatus"),
                is_finished=_optional_bool(reservation_raw, "isFinished"),
                is_history=_optional_bool(reservation_raw, "isHistory"),
                is_emergency=_optional_bool(reservation_raw, "isEmergency"),
                display_ticket_name=_optional_scalar_string(reservation_raw, "displayTicketName"),
                is_non_member=_optional_bool(reservation_raw, "isNonMember"),
                is_transfer=_optional_bool(reservation_raw, "isTransfer"),
                is_wheelchair_member=_optional_bool(reservation_raw, "isWheelchairMember"),
                is_rail_police_enabled=_optional_bool(reservation_raw, "isRailPoliceEnabled"),
                raw=reservation_raw,
                additional_service=additional_service,
                ticket_kind=_optional_scalar_string(reservation_raw, "ticketKind"),
            )
        )
    return TicketListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        reservations=tuple(reservations),
        total_count=_optional_scalar_string(raw, "h_total_cnt"),
    )


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
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return OriginalTicketInquiryResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


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
                run_date=_optional_scalar_string(row, "runDt"),
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
        ),
        **_response_fields(raw),
    )
