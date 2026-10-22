# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""결제·환불 응답 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import strict_str, wire
from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class DiscountCardSection:
    """N카드를 적용할 수 있는 구간 한 개를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    departure_station_name: str | None = wire("dptRsStnNm")
    arrival_station_name: str | None = wire("arvRsStnNm")
    journey_sequence: str | None = wire("jrnySqno")
    journey_type_code: str | None = wire("jrnyTpCd")
    train_group_code: str | None = wire("trnGpCd")
    #: 경유 구분 이름(``stlbDturDvNm``)입니다. 앱은 N카드 구간으로 좌석배정 열차를 조회할 때 이 값을
    #: ``SeatAssignmentScheduleRequest.standing_detour_division_name``과 같은 입력 필드로 보냅니다.
    detour_division_name: str | None = wire("stlbDturDvNm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세에 포함된 N카드와 적용 구간을 담습니다."""

    #: N카드 번호(``h_dcnt_crd_no``)입니다.
    card_no: str | None = wire("h_dcnt_crd_no")
    #: 기간 연장 가능 여부 플래그(``h_dcnt_crd_trm_extn_psb_flg``)입니다.
    term_extension_possible_flag: str | None = wire("h_dcnt_crd_trm_extn_psb_flg")
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, repr=False)
class _RefundCommissionContext:
    """수수료를 조회한 원표·동반자 입력입니다. 서버 응답이나 인증 증명이 아닙니다."""

    window_no: str
    return_sale_date: str
    sale_sequence: str
    return_password: str
    companion_name: str
    companion_certificate_no: str


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """환불 전 예상 환불액과 수수료를 담습니다.

    ``get_refund_commission``이 돌려줍니다. 환불하려면 이 응답을 ``refund``의 ``commission``에 넘기세요. ``refund``는
    ``commission``이 실제 조회 결과가 아니거나(``None``·직접 생성·직접 파싱 포함), 조회한 원표·동반자가
    환불 대상과 다르면 요청 전에 ``KorailProtocolError``를 발생시킵니다. 로컬 연결 검사는 수수료의
    유효기간이나 서버의 환불 승인을 보장하지 않습니다."""

    refund_amount: str | None = wire("ret_amt")
    refund_fee: str | None = wire("ret_fee")
    proceed_possible_flag: str | None = wire("prg_psb_flg")
    ticket_return_times_division_code: str | None = wire("tk_ret_tms_dv_cd")
    usable_mileage: str | None = wire("use_psb_mlg_num")
    secondary_message_code: str | None = wire("h_msg_cd2")
    secondary_message_text: str | None = wire("h_msg_txt2")
    # raw/서버 필드에서 복원하지 않습니다. 클라이언트가 검증한 조회 입력만 로컬에서 연결합니다.
    _request_context: _RefundCommissionContext | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 한 자리를 담습니다."""

    car_no: str | None = wire("h_srcar_no")
    seat_no: str | None = wire("h_seat_no")
    buyer_name: str | None = wire("h_buy_ps_nm")
    checkin_status_code: str | None = wire("h_chckn_stt_cd")
    discount_kind_code: str | None = wire("h_dcnt_knd_cd")
    discount_kind_name: str | None = wire("h_dcnt_knd_nm")
    passenger_type_code: str | None = wire("h_psg_tp_cd")
    passenger_type_name: str | None = wire("h_psg_tp_nm")
    seat_group_name: str | None = wire("h_sgr_nm")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """환불 대상 승차권의 여정 한 개를 담습니다."""

    journey_sequence: str | None = wire("h_jrny_sqno")
    journey_type_code: str | None = wire("h_jrny_tp_cd")
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    arrival_date: str | None = wire("h_arv_dt")
    arrival_time: str | None = wire("h_arv_tm")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    train_no: str | None = wire("h_trn_no")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    room_class_name: str | None = wire("h_psrm_cl_nm")
    platform_no: str | None = wire("h_plf_no")
    seats: tuple[RefundTicketSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 식별자·여정·운임 상세를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    pnr_no: str | None = wire("h_pnr_no")
    sale_date: str | None = wire("h_sale_dt")
    sale_time: str | None = wire("h_sale_tm")
    window_name: str | None = wire("h_wct_nm")
    original_sale_date: str | None = wire("h_orgtk_ret_sale_dt")
    original_window_no: str | None = wire("h_orgtk_wct_no")
    original_sale_sequence: str | None = wire("h_orgtk_sale_sqno")
    original_return_password: str | None = wire("h_orgtk_ret_pwd")
    ticket_kind_code: str | None = wire("h_tk_knd_cd")
    ticket_kind_name: str | None = wire("h_tk_knd_nm")
    # 실서버에서 Y 인 상세도 수수료 조회는 WRT200022·WRT200399 로 거절됐습니다(docs/status.md).
    #: 환불 가능 여부 플래그(``retPsbFlg``)입니다. ``"Y"``여도 환불할 수 있다는 보장은 없으므로 ``get_refund_commission``의 결과로
    #: 확인하세요.
    refund_possible_flag: str | None = wire("retPsbFlg")
    return_flag: str | None = wire("h_ret_flg")
    total_fare_amount: str | None = wire("h_tot_fare_amt")
    total_discount_amount: str | None = wire("h_tot_disc_amt")
    total_received_amount: str | None = wire("h_tot_rcvd_amt")
    train_running_flag: str | None = wire("h_trn_running_flg")
    #: 탑승자 이름(``h_abrd_ps_nm``)입니다. 동승자 이름(``companion_name``)이나 ``passenger_names`` 목록과는 다른 필드입니다.
    passenger_name: str | None = wire("h_abrd_ps_nm")
    #: 탑승자 생년월일(``s_brth``)입니다.
    passenger_birth_date: str | None = wire("s_brth")
    #: 동승자 이름(``h_compa_nm``)입니다.
    companion_name: str | None = wire("h_compa_nm")
    #: 동승자 생년월일(``h_compa_brth``)입니다.
    companion_birth_date: str | None = wire("h_compa_brth")
    # 보호된 전송 키 대신 속성명으로 읽는 후보이며 실서버 상세 응답에는 없었습니다.
    #: 대리수령 대상 여부 플래그입니다. 응답에 ``pbpAcepTgtFlg`` 키가 있을 때만 채우며 보통은 ``None``입니다. 앱처럼 환불하려면
    #: ``get_ticket_list`` 승차권의 ``pbp_acceptance_target_flag``를 ``refund``에 넘기세요.
    pbp_acceptance_target_flag: str | None = wire("pbpAcepTgtFlg")
    delay_flag: str | None = wire("h_dlay_flg")
    delay_ticket_flag: str | None = wire("h_dlay_tk_flg")
    # mlgSaveFlg/mlgSaveTgt 는 앱 DTO 에 없지만 서버 상세에는 빈 문자열로 왔으므로 타입화하지 않고 raw 에 둡니다.
    additional_service_flag: str | None = wire("addSrvFlg")
    additional_service_cancel: str | None = wire("addSrvCancel")
    #: 이 승차권의 QR 코드(``h_qrcode``)입니다.
    qr_code: str | None = wire("h_qrcode")
    #: 승객 이름 목록(``psgNmList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    passenger_names: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    #: 좌석 배정 목록(``seatTicketList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    seat_tickets: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    #: 연계된 리무진 예약(``limousine``)입니다. 추정한 응답 키로 읽은 원본 매핑이며, 없으면 ``None``입니다.
    limousine: Mapping[str, object] | None = field(default=None, compare=False)
    #: 지연 정보 목록(``dtlList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    delay_details: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: N카드 정보(``dcnt_crd_info``)입니다. 응답에 없으면 ``None``이며, N카드 승차권이 아니면 보통 ``None``입니다.
    discount_card: DiscountCardOnTicket | None = None


@dataclass(frozen=True)
class RefundTicketResponse(BaseKorailResponse):
    """승차권 환불 결과의 정산수단 코드를 담습니다.

    응답의 정산 목록(``stlList``)이 ``null``이면 ``settlement_method_codes``는 빈 튜플이고 ``settlement_list_is_null``이
    ``True``입니다. 정산 목록 키가 없으면 ``KorailProtocolError``가 발생합니다."""

    settlement_method_codes: tuple[str, ...] = ()
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """역에서 발권한 승차권의 환불 확인 응답에 들어 있는 원표 한 행을 담습니다."""

    pnr_no: str
    original_sale_date: str | None = wire("ogtk_sale_dt", strict_str, default=None)
    original_sale_window_no: str | None = wire("ogtk_sale_wct_no", strict_str, default=None)
    original_sale_sequence: str | None = wire("ogtk_sale_sqno", strict_str, default=None)
    original_return_password: str | None = wire("ogtk_ret_pwd", strict_str, default=None)
    ticket_kind_code: str | None = wire("tk_knd_cd", strict_str, default=None)
    refund_division_code: str | None = wire("ret_dv_cd", strict_str, default=None)
    refund_reason_code: str | None = wire("ret_rsn_cd", strict_str, default=None)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """역에서 발권한 승차권의 환불 확인 결과(금액과 원표 목록)를 담습니다.

    서버가 원표 목록을 ``null``로 보내면 ``original_tickets``는 빈 튜플이고 ``original_ticket_list_is_null``이
    ``True``입니다."""

    received_amount: str | None = wire("rcvd_amt", strict_str, default=None)
    refund_fee: str | None = wire("ret_fee", strict_str, default=None)
    refund_amount: str | None = wire("ret_amt", strict_str, default=None)
    popup_message: str | None = wire("poppMsg")
    result_message: str | None = wire("strMsg")
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionResponse(BaseKorailResponse):
    """역에서 발권한 승차권의 환불 실행 결과를 담습니다."""

    refund_division_code: str | None = wire("h_ret_dv_cd")


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    """결제 결과에 포함된 쿠폰 정보를 담습니다."""

    certificate_password: str | None = wire("h_cert_pwd")
    coupon_no: str | None = wire("h_coup_no")
    management_close_date: str | None = wire("h_fdcert_mg_cls_dt")
    management_start_date: str | None = wire("h_fdcert_mg_st_dt")
    ticket_return_no: str | None = wire("h_tk_ret_no")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationPaymentTicket:
    """결제로 발권된 승차권 한 장의 식별자와 반환 식별자를 담습니다."""

    ticket_sequence: str | None = wire("h_tk_sqno")
    sale_date: str | None = wire("h_sale_dt")
    sale_sequence: str | None = wire("h_sale_sqno")
    return_password: str | None = wire("h_tk_ret_pwd")
    return_no: str | None = wire("h_tk_ret_no")
    recipient_name: str | None = wire("h_take_name")
    discount_card_no: str | None = wire("h_disc_card_no")
    ticket_price: str | None = wire("h_tk_prc")
    ticket_fare: str | None = wire("h_tk_fare")
    bz5_fare_discount_amount: str | None = wire("h_bz5_fare_disc_amt")
    bz6_fare_discount_amount: str | None = wire("h_bz6_fare_disc_amt")
    total_discount_amount: str | None = wire("h_tot_disc_amt")
    total_received_amount: str | None = wire("h_tot_rcvd_amt")
    standard_seat_price_fare: str | None = wire("h_std_seat_prc_fare")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """결제 결과의 정산수단 한 행을 담습니다.

    카드번호·승인번호 같은 값이 들어 있을 수 있으므로 로그에 남길 때 주의하세요."""

    settlement_sequence: str | None = wire("h_stl_sqno")
    settlement_type_code: str | None = wire("h_stl_tp_cd")
    settlement_result: str | None = wire("h_stl_rlt")
    transaction_division: str | None = wire("h_tr_gubun")
    card_installment_count: str | None = wire("h_crd_stl_cnt")
    installment_months: str | None = wire("h_inst_month")
    settlement_amount: str | None = wire("h_stl_amt")
    settlement_card_no: str | None = wire("h_stl_crd_no")
    card_company_code: str | None = wire("h_crd_corp_cd")
    card_company_name: str | None = wire("h_crd_corp_nm")
    approval_date: str | None = wire("h_apv_dt")
    approval_time: str | None = wire("h_apv_tm")
    approval_no: str | None = wire("h_apv_no")
    point_division: str | None = wire("h_xpoint_dv")
    point_no: str | None = wire("h_xpoint_no")
    point_approval_no: str | None = wire("h_xpoint_apv_no")
    remnant_amount: str | None = wire("h_remnant_amt")
    remote_point: str | None = wire("h_rmt_point")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """결제 결과에 포함된 두 구간 단체석 정보를 담습니다."""

    room_class_name_1: str | None = wire("h_psrm_cl_cd_nm1")
    car_no_1: str | None = wire("h_srcar_no1")
    seat_no_start_1: str | None = wire("h_tbl_seat_no_sno_1")
    seat_no_end_1: str | None = wire("h_tbl_seat_no_eno_1")
    seat_count_1: str | None = wire("h_tbl_seat_cnt_1")
    group_name_1: str | None = wire("h_sgr_nm_1")
    room_class_name_2: str | None = wire("h_psrm_cl_cd_nm2")
    car_no_2: str | None = wire("h_srcar_no2")
    seat_no_start_2: str | None = wire("h_tbl_seat_no_sno_2")
    seat_no_end_2: str | None = wire("h_tbl_seat_no_eno_2")
    seat_count_2: str | None = wire("h_tbl_seat_cnt_2")
    group_name_2: str | None = wire("h_sgr_nm_2")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    """카드 결제 시도의 발권·정산·좌석 결과를 담습니다."""

    image_ticket_flag: str | None = wire("h_im_flg")
    #: 결제 응답의 예약 번호 필드입니다. 카드 결제 응답에서는 빈 문자열일 수 있습니다. 결제 응답에는 PNR(``h_pnr_no``)이
    #: 없으므로 PNR은 홀드의 ``pnr_no``를 쓰세요.
    reservation_no: str | None = wire("h_rsv_no")
    settlement_approval_no: str | None = wire("h_stl_cd_apprv_no")
    total_received_amount: str | None = wire("h_tot_rcvd_amt")
    settlement_amount: str | None = wire("h_stl_amt")
    total_settlement_amount: str | None = wire("h_tot_stl_amt")
    customer_no: str | None = wire("h_cust_no")
    member_card_no: str | None = wire("h_mb_crd_no")
    buyer_name: str | None = wire("h_buy_name")
    publication_start_no: str | None = wire("h_publ_start_no")
    publication_end_no: str | None = wire("h_publ_end_no")
    mixed_settlement_division: str | None = wire("h_mix_stl_dv")
    cancellation_fee: str | None = wire("h_cnc_fee")
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
    tickets: tuple[ReservationPaymentTicket, ...] = ()
    settlements: tuple[ReservationPaymentSettlement, ...] = ()
    table_seats: tuple[ReservationPaymentTableSeat, ...] = ()
    #: 창구 번호(``h_wct_no``)입니다.
    window_no: str | None = wire("h_wct_no")
    settlement_count: str | None = wire("h_stl_cnt")
    discount_card_count: str | None = wire("h_disc_card_cnt")
    total_price: str | None = wire("h_tot_prc")
    total_fare: str | None = wire("h_tot_fare")
    total_discount_amount: str | None = wire("h_tot_disc_amt")
    adult_count: str | None = wire("h_adult_cnt")
    child_count: str | None = wire("h_child_cnt")
    table_seat_count: str | None = wire("h_tbl_seat_cnt")
    ticket_count: str | None = wire("h_tk_cnt")
    settlement_type_code: str | None = wire("h_stl_tp_cd")
    trade_division: str | None = wire("h_trade_gbn")
    remark: str | None = wire("h_bigo")
    survey_flag: str | None = wire("h_survey_flg")
    survey_title: str | None = wire("h_survey_title")
    survey_text: str | None = wire("h_survey_text")
    survey_url: str | None = wire("h_survey_url")
