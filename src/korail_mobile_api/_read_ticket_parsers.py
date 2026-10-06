# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·예약·영수증·환불·전달·체크인 조회 응답을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    RESERVATION_OUT_EXTRA_FIELDS,
    _nested_rows,
    _nullable_scalar_fields,
    _optional_bool,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _required_integer,
    _reservation_passengers,
    _response_fields,
    _rows,
    _strict_scalar_string,
)
from ._read_parser_common import (
    _optional_add_srv_item,
    _optional_read_rows,
    _required_read_rows,
    _required_read_strings,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from .errors import KorailProtocolError
from .models import BaseKorailResponse
from .read_models import (
    DelayCertificateResponse,
    DelayCertificateRow,
    DelayReturnReceiptResponse,
    DeliveryRecipientResponse,
    DiscountCardOnTicket,
    DiscountCardSection,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
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
    SelfCheckInInfoResponse,
    SelfCheckInSeat,
    SelfCheckInSeatCheckResponse,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    TicketDuplicationCheckResponse,
    TicketListReservation,
    TicketListResponse,
    TicketListTicket,
    TicketListTrain,
    TicketReceipt,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
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
                run_date=(
                    _optional_scalar_string(journey, "h_run_dt", "reservation detail journey")
                    if "h_run_dt" in journey
                    else ""
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
