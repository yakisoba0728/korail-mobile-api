# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""결제·환불 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..._core.parsing import (
    _nested_rows,
    _nullable_scalar_fields,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_strict_read_envelope,
)
from ..._core.parsing import _response_fields as _base_fields
from ...errors import KorailProtocolError
from ..reservations.parsers import _response_mapping, _row
from .models import (
    DiscountCardOnTicket,
    DiscountCardSection,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketResponse,
    RefundTicketSeat,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
    ReservationPaymentSettlement,
    ReservationPaymentTableSeat,
    ReservationPaymentTicket,
    StationRefundExecutionResponse,
    StationRefundOriginalTicket,
    StationRefundVerificationResponse,
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


@_preserve_read_raw
def parse_refund_ticket_response(raw: Mapping[str, Any]) -> RefundTicketResponse:
    """필수·nullable stlList 와 각 행의 필수 stl_mns_cd 를 읽습니다. RefundTicketOut.java:48-53 의 마스크는 8,
    StlList.java:46-55 는 1입니다."""
    copied = _response_mapping(raw)
    if "stlList" not in copied:
        raise KorailProtocolError("KORAIL refund stlList is required")
    rows = copied["stlList"]
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL refund stlList must be a list or null")
    codes: list[str] = []
    for value in rows or ():
        try:
            row = _row(value, "refund settlement")
            code = _strict_scalar_string(row, "stl_mns_cd", "refund settlement")
            if code is None:
                raise KorailProtocolError("KORAIL refund stl_mns_cd is required and non-null")
        except KorailProtocolError as error:
            error.raw = value
            raise
        codes.append(code)
    return RefundTicketResponse(
        **_base_fields(copied),
        settlement_method_codes=tuple(codes),
        settlement_list_is_null=rows is None,
    )


_STATION_REFUND_ORIGINAL_FIELDS = {
    "original_sale_date": "ogtk_sale_dt",
    "original_sale_window_no": "ogtk_sale_wct_no",
    "original_sale_sequence": "ogtk_sale_sqno",
    "original_return_password": "ogtk_ret_pwd",
    "ticket_kind_code": "tk_knd_cd",
    "refund_division_code": "ret_dv_cd",
    "refund_reason_code": "ret_rsn_cd",
}


@_preserve_read_raw
def parse_station_refund_verification_response(
    raw: Mapping[str, Any],
) -> StationRefundVerificationResponse:
    copied = _response_mapping(raw)
    rows = copied.get("orgtkinfo_list", [])
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station refund orgtkinfo_list must be a list")
    original_tickets: list[StationRefundOriginalTicket] = []
    for row in rows or ():
        row = _row(row, "station refund Orgtkinfo")
        pnr_no = _strict_scalar_string(row, "pnr_no", "station refund Orgtkinfo")
        if not pnr_no:
            raise KorailProtocolError("KORAIL station refund Orgtkinfo.pnr_no is required")
        identity_fields = {
            attr: _strict_scalar_string(row, wire_key, "station refund Orgtkinfo")
            for attr, wire_key in _STATION_REFUND_ORIGINAL_FIELDS.items()
        }
        original_tickets.append(
            StationRefundOriginalTicket(
                pnr_no=pnr_no,
                **identity_fields,
                raw=dict(row),
            )
        )
    return StationRefundVerificationResponse(
        **_base_fields(copied),
        received_amount=_strict_scalar_string(copied, "rcvd_amt", "station refund verification"),
        refund_fee=_strict_scalar_string(copied, "ret_fee", "station refund verification"),
        refund_amount=_strict_scalar_string(copied, "ret_amt", "station refund verification"),
        popup_message=_optional_scalar_string(copied, "poppMsg", "station refund verification"),
        result_message=_optional_scalar_string(copied, "strMsg", "station refund verification"),
        original_tickets=tuple(original_tickets),
        original_ticket_list_is_null=rows is None,
    )


@_preserve_read_raw
def parse_station_refund_execution_response(
    raw: Mapping[str, Any],
) -> StationRefundExecutionResponse:
    copied = _response_mapping(raw)
    return StationRefundExecutionResponse(
        **_base_fields(copied),
        refund_division_code=_optional_scalar_string(copied, "h_ret_dv_cd", "station refund execution"),
    )


_PAYMENT_COUPON_FIELDS = {
    "certificate_password": "h_cert_pwd",
    "coupon_no": "h_coup_no",
    "management_close_date": "h_fdcert_mg_cls_dt",
    "management_start_date": "h_fdcert_mg_st_dt",
    "ticket_return_no": "h_tk_ret_no",
}

# 결제 응답 고유 스칼라(ReservationPaymentOut.java:90).
_RESERVATION_PAYMENT_FIELDS = {
    "reservation_no": "h_rsv_no",
    "settlement_approval_no": "h_stl_cd_apprv_no",
    "total_received_amount": "h_tot_rcvd_amt",
    "settlement_amount": "h_stl_amt",
    "total_settlement_amount": "h_tot_stl_amt",
    "customer_no": "h_cust_no",
    "member_card_no": "h_mb_crd_no",
    "buyer_name": "h_buy_name",
    "publication_start_no": "h_publ_start_no",
    "publication_end_no": "h_publ_end_no",
    "mixed_settlement_division": "h_mix_stl_dv",
    "cancellation_fee": "h_cnc_fee",
    "window_no": "h_wct_no",
    "settlement_count": "h_stl_cnt",
    "discount_card_count": "h_disc_card_cnt",
    "total_price": "h_tot_prc",
    "total_fare": "h_tot_fare",
    "total_discount_amount": "h_tot_disc_amt",
    "adult_count": "h_adult_cnt",
    "child_count": "h_child_cnt",
    "table_seat_count": "h_tbl_seat_cnt",
    "ticket_count": "h_tk_cnt",
    "settlement_type_code": "h_stl_tp_cd",
    "trade_division": "h_trade_gbn",
    "remark": "h_bigo",
    "survey_flag": "h_survey_flg",
    "survey_title": "h_survey_title",
    "survey_text": "h_survey_text",
    "survey_url": "h_survey_url",
}

_RESERVATION_PAYMENT_TICKET_FIELDS = {
    "ticket_sequence": "h_tk_sqno",
    "sale_date": "h_sale_dt",
    "sale_sequence": "h_sale_sqno",
    "return_password": "h_tk_ret_pwd",
    "return_no": "h_tk_ret_no",
    "recipient_name": "h_take_name",
    "discount_card_no": "h_disc_card_no",
    "ticket_price": "h_tk_prc",
    "ticket_fare": "h_tk_fare",
    "bz5_fare_discount_amount": "h_bz5_fare_disc_amt",
    "bz6_fare_discount_amount": "h_bz6_fare_disc_amt",
    "total_discount_amount": "h_tot_disc_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "standard_seat_price_fare": "h_std_seat_prc_fare",
}

_RESERVATION_PAYMENT_SETTLEMENT_FIELDS = {
    "settlement_sequence": "h_stl_sqno",
    "settlement_type_code": "h_stl_tp_cd",
    "settlement_result": "h_stl_rlt",
    "transaction_division": "h_tr_gubun",
    "card_installment_count": "h_crd_stl_cnt",
    "installment_months": "h_inst_month",
    "settlement_amount": "h_stl_amt",
    "settlement_card_no": "h_stl_crd_no",
    "card_company_code": "h_crd_corp_cd",
    "card_company_name": "h_crd_corp_nm",
    "approval_date": "h_apv_dt",
    "approval_time": "h_apv_tm",
    "approval_no": "h_apv_no",
    "point_division": "h_xpoint_dv",
    "point_no": "h_xpoint_no",
    "point_approval_no": "h_xpoint_apv_no",
    "remnant_amount": "h_remnant_amt",
    "remote_point": "h_rmt_point",
}

_RESERVATION_PAYMENT_TABLE_SEAT_FIELDS = {
    "room_class_name_1": "h_psrm_cl_cd_nm1",
    "car_no_1": "h_srcar_no1",
    "seat_no_start_1": "h_tbl_seat_no_sno_1",
    "seat_no_end_1": "h_tbl_seat_no_eno_1",
    "seat_count_1": "h_tbl_seat_cnt_1",
    "group_name_1": "h_sgr_nm_1",
    "room_class_name_2": "h_psrm_cl_cd_nm2",
    "car_no_2": "h_srcar_no2",
    "seat_no_start_2": "h_tbl_seat_no_sno_2",
    "seat_no_end_2": "h_tbl_seat_no_eno_2",
    "seat_count_2": "h_tbl_seat_cnt_2",
    "group_name_2": "h_sgr_nm_2",
}


@_preserve_read_raw
def parse_reservation_payment_response(
    raw: Mapping[str, Any],
) -> ReservationPaymentResponse:
    """결제 결과의 중첩 목록을 관대하게 읽으며 성공 여부는 판정하지 않습니다. 이미 승인됐을 수 있으므로 파싱 결과만 보고 결제를 재전송하지 마십시오."""
    copied = _response_mapping(raw)
    coupons: list[ReservationPaymentCoupon] = []
    for value in _rows(copied, "tk_coupon_info"):
        row = dict(value)
        coupons.append(
            ReservationPaymentCoupon(
                **_nullable_scalar_fields(row, _PAYMENT_COUPON_FIELDS, "payment coupon"),
                raw=row,
            )
        )

    tickets: list[ReservationPaymentTicket] = []
    for value in _nested_rows(copied, "tk_infos", "tk_info"):
        row = dict(value)
        tickets.append(
            ReservationPaymentTicket(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_TICKET_FIELDS, "payment ticket"),
                raw=row,
            )
        )

    settlements: list[ReservationPaymentSettlement] = []
    for value in _nested_rows(copied, "stl_infos", "stl_info"):
        row = dict(value)
        settlements.append(
            ReservationPaymentSettlement(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_SETTLEMENT_FIELDS, "payment settlement"),
                raw=row,
            )
        )

    table_seats: list[ReservationPaymentTableSeat] = []
    for value in _nested_rows(copied, "tbl_seat_infos", "tbl_seat_info"):
        row = dict(value)
        table_seats.append(
            ReservationPaymentTableSeat(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_TABLE_SEAT_FIELDS, "payment table seat"),
                raw=row,
            )
        )

    return ReservationPaymentResponse(
        **_base_fields(copied),
        image_ticket_flag=_optional_scalar_string(copied, "h_im_flg", "payment"),
        **_nullable_scalar_fields(copied, _RESERVATION_PAYMENT_FIELDS, "payment"),
        coupons=tuple(coupons),
        tickets=tuple(tickets),
        settlements=tuple(settlements),
        table_seats=tuple(table_seats),
    )
