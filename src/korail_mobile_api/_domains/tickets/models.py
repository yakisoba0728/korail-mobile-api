# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정 조회 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..._core.parsing import optional_bool, optional_int, required_int, required_str, wire
from ..airport_bus.models import MaasServiceDetail
from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class TicketListTrain:
    """승차권 한 장에 포함된 열차 구간 정보를 담습니다.

    호차 번호(``car_no``)처럼 서버가 정수로 보내는 값도 문자열로 담습니다."""

    # 앱 근거: TicketListTrainInfo.java:72. 라이브 이력 139행: 21개 키가 모두 있었고 h_srcar_no 는 String 선언과 달리 모두 JSON
    # 정수였습니다(문자열로 받습니다).
    journey_sequence: str | None = wire("h_jrny_sqno")
    run_date: str | None = wire("h_run_dt")
    train_no: str | None = wire("h_trn_no")
    train_class_code: str | None = wire("h_trn_clsf_cd")
    train_class_name: str | None = wire("h_trn_clsf_nm")
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd")
    departure_station_name: str | None = wire("h_dpt_rs_stn_nm")
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    arrival_station_code: str | None = wire("h_arv_rs_stn_cd")
    arrival_station_name: str | None = wire("h_arv_rs_stn_nm")
    arrival_date: str | None = wire("h_arv_dt")
    arrival_time: str | None = wire("h_arv_tm")
    car_no: str | None = wire("h_srcar_no")
    seat_no: str | None = wire("h_seat_no")
    seat_count: str | None = wire("h_seat_cnt")
    passenger_type_code: str | None = wire("h_psg_tp_cd")
    received_amount: str | None = wire("h_rcvd_amt")
    buyer_name: str | None = wire("h_buy_ps_nm")
    passenger_name: str | None = wire("h_abrd_ps_nm")
    train_suspension_flag: str | None = wire("trnSpsFlg")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketListTicket:
    """승차권 한 장의 식별자·상태와 열차 구간을 담습니다."""

    pnr_no: str | None = wire("h_pnr_no")
    sale_window_no: str | None = wire("h_orgtk_wct_no")
    sale_date: str | None = wire("h_orgtk_sale_dt")
    return_sale_date: str | None = wire("h_orgtk_ret_sale_dt")
    sale_sequence: str | None = wire("h_orgtk_sale_sqno")
    return_password: str | None = wire("h_orgtk_ret_pwd")
    ticket_status_code: str | None = wire("h_tk_stt_cd")
    # 한 계정 관측에서 131행 모두에 있었습니다.
    #: 승차권 종류 코드(``h_tk_knd_cd``)입니다. 예약 행이 아니라 승차권 행의 값을 읽습니다.
    ticket_kind_code: str | None = wire("h_tk_knd_cd")
    ticket_kind_name: str | None = wire("h_tk_knd_nm")
    train_info: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # h_tk_sqno 선언: MyTicketListOutTicket.java:92. 다른 조건에서도 필수인지는 검증 못 함입니다.
    ticket_sequence: str | None = wire("h_tk_sqno")
    #: 승차권 상태 이름(``h_tk_stt_nm``)입니다. 서버가 보낸 이름을 그대로 담으며 ``ticket_status_code``를 따로 번역하지 않습니다.
    ticket_status_name: str | None = wire("h_tk_stt_nm")
    # 앱 버튼 조건은 상세 플래그와 사용 여부 검사입니다(NormalTicketSectionKt.java:951, TicketHelper.java:3173-3199). 비교 리터럴은
    # 보호돼 있습니다.
    #: 반환 가능 여부 플래그(``h_ret_psb_flg``)입니다. 앱은 승차권 상세의 플래그와 사용 여부도 함께 확인하므로 이 값만으로 환불할 수
    #: 있는지 판단할 수 없습니다. 앱이 비교하는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    return_possible_flag: str | None = wire("h_ret_psb_flg")
    use_transaction_no: str | None = wire("h_use_tno")
    notify_use_transaction_no: str | None = wire("h_noty_use_tno")
    # 실서버 검증 못 함. 앱은 목록 값을 상세에 주입합니다(MyTicketBaseViewModel.java:769, MyTicketDetailViewModel.java:1521). 상세
    # 40응답에는 두 후보 키가 없었습니다.
    #: 대리수령 대상 여부 플래그(``h_pbp_acep_tgt_flg``)입니다. 승차권 상세 응답에는 이 값이 보통 없으므로, 앱처럼 환불하려면 이 값을
    #: ``refund``의 ``pbp_acceptance_target_flag``로 넘기세요.
    pbp_acceptance_target_flag: str | None = wire("h_pbp_acep_tgt_flg")
    trains: tuple[TicketListTrain, ...] = ()


@dataclass(frozen=True)
class TicketListReservation:
    """예약 하나에 속한 승차권 목록과 부가서비스를 담습니다.

    ``tickets`` 외의 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 키가
    다르면 해당 필드는 ``None``입니다."""

    # MyTicketListOutReservation 의 명시적 키는 ticket_list 이며 나머지는 보호된 serializer 대신 속성명으로 읽는 추정입니다.
    tickets: tuple[TicketListTicket, ...] = ()
    # 선택 스칼라의 전송 키는 속성명에 따른 추정입니다. mode=2 의 예약 128행은 ticket_list 외 키가 없었습니다. 다른 응답의 필드
    # 부재까지 보장하지 않습니다.
    #: 출발 일시(``hDptDtTm``)입니다. 응답에 없으면 ``None``입니다.
    departure_datetime: str | None = wire("hDptDtTm")
    ticket_kind_code: str | None = wire("hTkKndCd")
    list_count: str | None = wire("listCnt")
    seat_assign_count: int | None = wire("seatAssignCount", optional_int, default=None)
    ticket_status: str | None = wire("ticketStatus")
    is_finished: bool | None = wire("isFinished", optional_bool, default=None)
    is_history: bool | None = wire("isHistory", optional_bool, default=None)
    is_emergency: bool | None = wire("isEmergency", optional_bool, default=None)
    display_ticket_name: str | None = wire("displayTicketName")
    is_non_member: bool | None = wire("isNonMember", optional_bool, default=None)
    is_transfer: bool | None = wire("isTransfer", optional_bool, default=None)
    is_wheelchair_member: bool | None = wire("isWheelchairMember", optional_bool, default=None)
    is_rail_police_enabled: bool | None = wire("isRailPoliceEnabled", optional_bool, default=None)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 선택값의 타입이 어긋나면 해당 값만 비웁니다. addSrvInfo(MyTicketListOutReservation.java:39)는 MaaS 의 AddSrvItem 과 같은 타입이라 모델을
    # 공유합니다(MaasDetailOut.java:27, AddSrvItem.java:28-49).
    additional_service: MaasServiceDetail | None = None
    # ticketKind 는 보호된 enum 이름을 매핑하지 않고 문자열로 둡니다 (MyTicketListOutReservation.java:52,59;
    # TicketDefine.java:1078-1131).
    #: 승차권 종류(``ticketKind``)입니다. 서버가 보낸 문자열을 그대로 담으며, 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지
    #: 못했습니다.
    ticket_kind: str | None = wire("ticketKind")


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    """현재 승차권 또는 구매 이력을 예약별로 묶어 담습니다."""

    reservations: tuple[TicketListReservation, ...] = ()
    #: 전체 건수(``h_total_cnt``)입니다. 키가 없으면 ``None``입니다.
    total_count: str | None = wire("h_total_cnt")


@dataclass(frozen=True)
class DepositBank:
    """입금 가능한 은행의 코드와 이름을 담습니다."""

    code: str | None = wire("dptnBankCd", required_str, default=None)
    display_name: str | None = wire("dptnBankNm", required_str, default=None)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    """입금 가능한 은행 목록을 담습니다."""

    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연할인권 한 장의 식별자·사용 조건을 담습니다.

    사용 가능 기한(``h_use_psb_dt``)은 읽지 않습니다. 응답에 있으면 ``raw``에서 확인하세요."""

    # 앱 근거: DelayCoupon.java:32-55. h_use_psb_dt(사용 가능 기한)는 전 디컴파일에 0건이라 읽지 않습니다.
    fare: str | None = wire("h_dlay_fare")
    original_sale_date: str | None = wire("h_orgtk_ret_sale_dt")
    window_no: str | None = wire("h_orgtk_wct_no")
    sale_sequence: str | None = wire("h_orgtk_sale_sqno")
    return_password: str | None = wire("h_orgtk_ret_pwd")
    ticket_sequence: str | None = wire("h_tk_sqno")
    ticket_kind_code: str | None = wire("h_tk_knd_cd")
    original_ticket_sale_date: str | None = wire("h_orgtk_sale_dt")
    received_amount: str | None = wire("h_rcvd_amt")
    train_class_code: str | None = wire("h_trn_clsf_cd")
    room_class_code: str | None = wire("h_psrm_cl_cd")
    train_no: str | None = wire("h_trn_no")
    departure_station_code: str | None = wire("h_dpt_rs_stn_cd")
    departure_date: str | None = wire("h_dpt_dt")
    departure_time: str | None = wire("h_dpt_tm")
    arrival_station_code: str | None = wire("h_arv_rs_stn_cd")
    arrival_date: str | None = wire("h_arv_dt")
    arrival_time: str | None = wire("h_arv_tm")
    ticket_status_code: str | None = wire("h_tk_stt_cd")
    ticket_status_name: str | None = wire("h_tk_stt_nm")
    buyer_name: str | None = wire("h_buy_ps_nm")
    passenger_name: str | None = wire("h_abrd_ps_nm")
    page_no: str | None = wire("h_page_no")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    """지연할인권 목록과 페이지 정보를 담습니다.

    페이지 정보(``current_page``, ``total_pages``, ``total_count``, ``row_count``, ``last_page_flag``)는 응답의 ``main_info``
    블록에서 읽습니다. 블록이 없으면 모두 ``None``입니다."""

    # main_info는 DTO 밖 서버 추가 블록입니다(DelayDiscountViewOut.java:24,51). 날짜 입력 8종에서 12키를 확인했지만 할인권 없는
    # 응답뿐이었습니다.
    items: tuple[DelayDiscountTicket, ...] = ()
    current_page: str | None = wire("h_page_no")
    total_pages: str | None = wire("h_tot_page_cnt")
    total_count: str | None = wire("h_tot_cnt")
    row_count: str | None = wire("h_row_cnt")
    last_page_flag: str | None = wire("h_last_page_yn")


@dataclass(frozen=True)
class DiscountCoupon:
    """할인쿠폰 한 장의 조건과 유효기간을 담습니다."""

    guide: str | None = wire("guide")
    start_date: str | None = wire("h_fdcert_mg_st_dt")
    expiration_date: str | None = wire("h_fdcert_mg_cls_dt")
    discount_kind_code: str | None = wire("h_dscp_knd_cd")
    # CouponOutInfo.java:63.
    #: 할인율·할인액 구분 코드(``h_disc_rt_amt_dv_cd``)입니다. 코드 값의 의미를 확인하지 못했습니다.
    discount_rate_amount_division_code: str | None = wire("h_disc_rt_amt_dv_cd")
    weekday_fare_discount: str | None = wire("h_inwk_fare_disc_rt_amt")
    weekday_price_discount: str | None = wire("h_inwk_prc_disc_rt_amt")
    weekend_fare_discount: str | None = wire("h_wknd_fare_disc_rt_amt")
    weekend_price_discount: str | None = wire("h_wknd_prc_disc_rt_amt")
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = wire("h_cpn_no")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    """할인쿠폰 목록과 안내를 담습니다."""

    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = wire("h_page_no", optional_int, default=None)
    total_pages: int | None = wire("h_tot_page_cnt", optional_int, default=None)
    total_count: str | None = wire("h_tot_cnt")
    row_count: str | None = wire("h_row_cnt")


@dataclass(frozen=True, kw_only=True)
class ReceiptPayment:
    """영수증의 결제수단 한 행을 담습니다."""

    payment_method: str = wire("h_stl_way_nm", required_str)
    approval_date: str = wire("h_apv_dt", required_str)
    installment_months: int = wire("h_ismt_mnth_num", required_int)
    amount: int = wire("h_stl_amt", required_int)
    account_no: str = wire("h_acnt_no", required_str)
    approval_no: str = wire("h_apv_no", required_str)
    card_no: str = wire("h_stl_crd_no", required_str)
    point_no: str = wire("h_xpot_no", required_str)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class ReceiptCashPayment:
    """영수증에 포함된 현금영수증 한 행을 담습니다.

    인증 도메인 인식번호와 현금영수증 승인번호도 가리지 않고 서버가 보낸 값 그대로 담습니다."""

    # 앱 근거: ReceiptInfo.java:37. String 4개·int 금액 1개이며 전송 키는 CashReceiptInfo.java:26-35,52 의 명시적 @SerialName
    # 입니다.
    #: 승인 방법 이름(``h_apv_mtd_nm``)입니다.
    approval_method_name: str = wire("h_apv_mtd_nm", required_str)
    authentication_domain_recognition_no: str = wire("h_athn_dmn_rcgn_no", required_str)
    cash_receipt_approval_no: str = wire("h_cash_rcet_apv_no", required_str)
    cash_receipt_transaction_division_code: str = wire("h_cash_rcet_txn_dv_cd", required_str)
    total_approved_amount: int = wire("h_tot_apv_amt", required_int)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class TicketReceipt:
    """승차권 영수증의 이용 내역과 결제 정보를 담습니다."""

    travel_date: str = wire("h_abrd_dt", required_str)
    departure_station: str = wire("h_dpt_rs_stn_nm", required_str)
    departure_time: str = wire("h_dpt_tm", required_str)
    arrival_station: str = wire("h_arv_rs_stn_nm", required_str)
    arrival_time: str = wire("h_arv_tm", required_str)
    commuter_kind_code: str = wire("h_cmtr_knd_cd", required_str)
    journey_type_code: str = wire("h_jrny_tp_cd", required_str)
    printed_discount_name: str = wire("h_prt_disc_knd_nm", required_str)
    printed_discount_kind_code: str = wire("h_prt_disc_knd_cd", required_str)
    print_type: str = wire("h_prt_type", required_str)
    seat_class_name: str = wire("h_psrm_cl_nm", required_str)
    ticket_kind_code: str = wire("h_tk_knd_cd", required_str)
    ticket_kind_name: str = wire("h_tk_knd_nm", required_str)
    ticket_status_code: str = wire("h_tk_stt_cd", required_str)
    train_class_code: str = wire("h_trn_clsf_cd", required_str)
    train_class_name: str = wire("h_trn_clsf_nm", required_str)
    train_group_code: str = wire("h_trn_gp_cd", required_str)
    train_no: str = wire("h_trn_no", required_str)
    passenger_counts: tuple[int, int, int]
    received_amount: int = wire("h_rcvd_amt", required_int)
    card_refund_amount: int = wire("h_crd_ret_amt", required_int)
    refund_fee: int = wire("h_ret_fee", required_int)
    refund_received_amount: int = wire("h_ret_rcvd_amt", required_int)
    point_refund_amount: int = wire("h_xpoint_ret_amt", required_int)
    payments: tuple[ReceiptPayment, ...] = ()
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str = wire("h_stl_mb_crd_no", required_str)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    """승차권 영수증 조회 결과를 담습니다."""

    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """계정의 포인트·쿠폰·복지 자격 요약을 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 소셜 연동 플래그 네
    개(``naver_linked_flag``, ``kakao_linked_flag``, ``google_linked_flag``, ``apple_linked_flag``)가 각각 어느 서비스에
    대응하는지도 확인하지 못했으므로, 필드 이름의 서비스 대응을 확정된 것으로 보지 마세요."""

    # 앱 근거: MyXPointViewOut.java:27-74. 별칭 없는 키는 속성명에 따른 추정입니다.
    korail_point: str | None = wire("h_korail_point")
    #: 서버가 알려 준 할인쿠폰 개수(``h_disc_coup_cnt``)입니다. ``get_discount_coupons`` 결과의 개수와 항상 같다는 보장은 없습니다.
    discount_coupon_count: str | None = wire("h_disc_coup_cnt")
    delay_discount_count: str | None = wire("h_delay_cnt")
    disability_flag: str | None = wire("h_hdcp_flg")
    welfare_discount_class_name: str | None = wire("h_subt_dcs_cl_nm")
    welfare_discount_class_code: str | None = wire("h_subt_dcs_cl_cd")
    customer_lead_flag_name: str | None = wire("h_cust_lead_flg_nm")
    phone_verified_flag: str | None = wire("h_cp_athn_flg")
    email_verified_flag: str | None = wire("h_emil_athn_flg")
    contact_channel_content: str | None = wire("h_cntc_chn_cont1")
    # 소셜 연동 플래그의 서비스별 순서는 7.0.6 에서 미확인입니다. 소비 값이 보호된 LoginMethodApiData.java:18-21 을 거치므로 Python
    # 필드명을 확정된 매핑으로 신뢰하지 않습니다.
    #: 네이버 연동 여부로 추정하는 플래그(``h_logn_tp_cd1``)입니다.
    naver_linked_flag: str | None = wire("h_logn_tp_cd1")
    #: 카카오 연동 여부로 추정하는 플래그(``h_logn_tp_cd2``)입니다.
    kakao_linked_flag: str | None = wire("h_logn_tp_cd2")
    #: 구글 연동 여부로 추정하는 플래그(``h_logn_tp_cd4``)입니다.
    google_linked_flag: str | None = wire("h_logn_tp_cd4")
    #: 애플 연동 여부로 추정하는 플래그(``h_logn_tp_cd5``)입니다.
    apple_linked_flag: str | None = wire("h_logn_tp_cd5")
    # ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그 그 자체.
    customer_lead_flag: str | None = wire("h_cust_lead_flg")
    #: 장애 유형 코드(``h_hdcp_tp_cd``)입니다. 장애 유형은 ``disability_flag``가 아니라 이 필드와 ``disability_type_name``에
    #: 있습니다.
    disability_type_code: str | None = wire("h_hdcp_tp_cd")
    #: 장애 유형 이름(``h_hdcp_tp_cd_nm``)입니다.
    disability_type_name: str | None = wire("h_hdcp_tp_cd_nm")


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 적립 또는 사용 내역 한 행을 담습니다."""

    # AmtSpecOutSpecInfo.java:29-35 가 선언하는 것이 정확히 아래 일곱 필드입니다. 라이브에서 3페이지 14행 전부가 이 일곱 키를
    # 문자열로 싣고 그 밖의 키는 없었습니다.
    departure_date: str | None = wire("dptDt")
    point_division_name: str | None = wire("pontDvNm")
    accrual_division_name: str | None = wire("mlgAcmDvCdNm")
    receipt_division_name: str | None = wire("rcpDvNm")
    point_amount: str | None = wire("pontAmt")
    saved_point_value: str | None = wire("savePontValNum")
    settlement_amount: str | None = wire("stlAmt")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """마일리지 내역 한 페이지와 적립·사용 합계를 담습니다.

    응답에 따로 있는 합계 필드는 서로 합치지 않고 각각 담습니다."""

    # 앱 근거: AmtSpecOut.java:29-39,199-247. pgCnt 는 AmtSpecOut.java:32.
    #: 전체 페이지 수(``pgCnt``)입니다.
    page_count: str | None = wire("pgCnt")
    query_count: str | None = wire("qryCnt")
    total_available_rail_point: str | None = wire("totAvlRailPontValNum")
    total_available_rail_point_1: str | None = wire("totAvlRailPontValNum1")
    total_available_affiliate_point: str | None = wire("totAvlAfltPontValNum")
    total_accumulated_rail_point_1: str | None = wire("totAcmRailPontValNum1")
    total_used_rail_point_1: str | None = wire("totUseRailPontValNum1")
    expiring_point_value: str | None = wire("delPontValNum")
    ktx_mileage_info: str | None = wire("ktxMlgInfo")
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    """다자녀 할인 대상으로 등록된 가족 한 명을 담습니다."""

    birth_date: str | None = wire("btdt")
    customer_family_name: str | None = wire("custFmlyNm")
    discount_kind_code: str | None = wire("dcntKndCd")
    family_sequence: str | None = wire("fmlySqno")
    passenger_type_code: str | None = wire("psgTpCd")
    passenger_type_name: str | None = wire("psgTpNm")
    room_class_code: str | None = wire("psrmClCd")
    requested_discount_kind_code: str | None = wire("rqDcntKndCd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    """다자녀 할인 대상 가족 목록을 담습니다."""

    targets: tuple[MultiChildDiscountTarget, ...] = ()


@dataclass(frozen=True)
class CustomerTripInfo:
    """계정에 저장된 여행 편의설정을 담습니다."""

    additional_seat_attribute_code: str | None = wire("addSeatAttCd")
    adult_disabled_person_count: str | None = wire("adltHdcpPrnb")
    adult_count: str | None = wire("adulCnt")
    arrival_station_code: str | None = wire("arvStnCd")
    arrival_station_name: str | None = wire("arvStnNm")
    baby_accompanying_person_count: str | None = wire("babyAcpnPrnb")
    changed_at: str | None = wire("chgDttm")
    changed_by: str | None = wire("chgUsrId")
    child_count: str | None = wire("chilCnt")
    child_disabled_person_count: str | None = wire("chldHdcpPrnb")
    customer_management_no: str | None = wire("custMgNo")
    day_code: str | None = wire("dayCd")
    direction_seat_attribute_group_code: str | None = wire("dirSeatAttGpCd")
    direct_transfer_division_code: str | None = wire("dirtChtnDvCd")
    departure_station_code: str | None = wire("dptStnCd")
    departure_station_name: str | None = wire("dptStnNm")
    early_train_departure_time: str | None = wire("ectbTrnDptTm")
    elderly_person_count: str | None = wire("edrPrnb")
    included_flag: str | None = wire("inclFlg")
    job_start_hour: str | None = wire("jobStHr")
    location_seat_attribute_group_code: str | None = wire("locSeatAttGpCd")
    media_division_code: str | None = wire("medDvCd")
    room_class_code: str | None = wire("psrmClCd")
    passenger_total: str | None = wire("ptwtTtl")
    registered_at: str | None = wire("regDttm")
    registration_sequence: str | None = wire("regSqno")
    registered_by: str | None = wire("regUsrId")
    trip_day_no: str | None = wire("tripDno")
    train_classification_code: str | None = wire("trnClsfCd")
    train_connection_flag: str | None = wire("trnCnecFlg")
    train_group_code: str | None = wire("trnGpCd")
    usage_day_no: str | None = wire("utlDno")
    # @SerialName 이 없어 와이어 철자는 보호됨 이며 코틀린 필드명을 추정해 사용합니다(CustTripInfo.java:48).
    #: 상품 번호입니다. 추정한 응답 키(``gdNo``)로 읽으며, 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    goods_no: str | None = wire("gdNo")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    """여행 편의설정 조회 결과를 담습니다."""

    trips: tuple[CustomerTripInfo, ...] = ()


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """승차권을 변경할 수 있는 날짜 목록을 담습니다.

    ``trip_change_dates``는 응답의 ``tripChgDates`` 목록입니다. 목록이 없거나 ``null`` 원소가 있으면 ``KorailProtocolError``가
    발생합니다."""

    # 앱 근거: NetworkApi.java:238; TipChgDateInquiryOut.java:28-30. tripChgDate(단수)는 요청 DTO(TipChgDateInquiryIn.java:29)의
    # 필드입니다 — 응답은 복수형 tripChgDates(List<String>)만 선언하므로, 여기서는 단수형을 읽지 않습니다.
    last_run_date: str | None = wire("lastRunDt")
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석변경이 가능한 승차역과 잔여석을 담습니다.

    응답의 도착역 코드·이름과 도착역 편성·운행 순서는 읽지 않습니다. 원본은 ``raw``에 남습니다."""

    # 앱 근거: ChgStnInfo.java:21-35; SeatAvailabilityOut.java:32. DTO 의 도착역 코드·이름·편성/운행순서 4개 필드는 이 모델에서
    # 읽지 않습니다.
    departure_station_code: str | None = wire("dptRsStnCd")
    departure_station_name: str | None = wire("dptRsStnNm")
    departure_date: str | None = wire("dptDt")
    departure_time: str | None = wire("dptTm")
    arrival_date: str | None = wire("arvDt")
    arrival_time: str | None = wire("arvTm")
    departure_construction_order: str | None = wire("dptStnConsOrdr")
    departure_run_order: str | None = wire("dptStnRunOrdr")
    general_remaining_seats: str | None = wire("gnrmRestSeatNum")
    special_remaining_seats: str | None = wire("sprmRestSeatNum")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """자율 좌석변경 시 선택할 변경 사유를 담습니다.

    필드는 추정한 응답 키(``qryCode``, ``qryOrdr``, ``frcSaleRsnCont``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아
    확인하지 못했습니다."""

    # 앱 근거: ChgRsnInfo.java:21-24; SeatAvailabilityOut.java:31. serializer descriptor 의 이름이 보호돼 있어
    # (ChgRsnInfo$$serializer.java:34-36) 전송 키는 속성명에 따른 추정입니다.
    query_code: str | None = wire("qryCode")
    query_order: str | None = wire("qryOrdr")
    reason_text: str | None = wire("frcSaleRsnCont")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """자율 좌석변경의 대상 역·사유·열차 정보를 담습니다."""

    # 앱 근거: NetworkApi.java:806-808; SeatAvailabilityOut.java:28-42,68.
    train_no: str | None = wire("trnNo")
    train_class_code: str | None = wire("trnClsfCd")
    train_class_name: str | None = wire("trnClsfNm")
    train_group_code: str | None = wire("trnGpCd")
    train_group_name: str | None = wire("trnGpNm")
    run_date: str | None = wire("runDt")
    general_reservation_possible_code: str | None = wire("gnrmRsvPsbCd")
    special_reservation_possible_code: str | None = wire("sprmRsvPsbCd")
    change_before_departure_construction_order: str | None = wire("chgBfDptStnConsOrdr")
    change_before_arrival_construction_order: str | None = wire("chgBfArvStnConsOrdr")
    existing_departure_run_order: str | None = wire("exsDptStnRunOrdr")
    existing_arrival_run_order: str | None = wire("exsArvStnRunOrdr")
    stations: tuple[SelfSeatChangeStation, ...] = ()
    reasons: tuple[SelfSeatChangeReason, ...] = ()


@dataclass(frozen=True)
class OriginalTicketSeat:
    """변경 기준인 원표의 좌석 정보를 담습니다."""

    # 앱 근거: SeatInfo.java:25-51; JrnyInfo.java:58. 대리수령용 Seat.java:27-36 과는 이름과 구조가 다른 타입입니다.
    passenger_sequence: str | None = wire("psgSqno")
    assign_sequence: str | None = wire("asgnSqno")
    passenger_type_code: str | None = wire("psgTpDvCd")
    room_class_code: str | None = wire("psrmClCd")
    car_no: str | None = wire("scarNo")
    seat_no: str | None = wire("seatNo")
    seat_count: str | None = wire("seatNum")
    received_fare: str | None = wire("rcvdFare")
    received_price: str | None = wire("rcvdPrc")
    requested_seat_attribute_code: str | None = wire("rqSeatAttCd")
    direction_seat_attribute_code: str | None = wire("dirSeatAttCd")
    location_seat_attribute_code: str | None = wire("locSeatAttCd")
    smoking_seat_attribute_code: str | None = wire("smkSeatAttCd")
    additional_seat_attribute_code: str | None = wire("addSeatAttCd")
    etc_seat_attribute_code: str | None = wire("etcSeatAttCd")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """변경 기준인 원표의 구간과 좌석 목록을 담습니다."""

    # 앱 근거: OrgTk.java:38; JrnyInfo.java:29-63. 대리수령용 Jrny.java:29-38 과 다릅니다.
    journey_sequence: str | None = wire("jrnySqno")
    journey_order: str | None = wire("jrnyOrdr")
    journey_type_code: str | None = wire("jrnyTpCd")
    train_no: str | None = wire("trnNo")
    train_group_code: str | None = wire("trnGpCd")
    departure_date: str | None = wire("dptDt")
    departure_time: str | None = wire("dptTm")
    departure_station_code: str | None = wire("dptRsStnCd")
    departure_station_name: str | None = wire("dptRsStnNm")
    departure_construction_order: str | None = wire("dptStnConsOrdr")
    arrival_date: str | None = wire("arvDt")
    arrival_time: str | None = wire("arvTm")
    arrival_station_code: str | None = wire("arvRsStnCd")
    arrival_station_name: str | None = wire("arvRsStnNm")
    arrival_construction_order: str | None = wire("arvStnConsOrdr")
    goods_no: str | None = wire("gdNo")
    total_seat_count: str | None = wire("totSeatNum")
    total_standing_count: str | None = wire("totStndNum")
    general_change_allowed_flag: str | None = wire("genChgAllwFlg")
    single_ticket_flag: str | None = wire("snglTkFlg")
    seats: tuple[OriginalTicketSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """변경 기준인 원표의 식별자·상태·여정을 담습니다.

    필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. ``original_*`` 필드는
    요청한 승차권의 반환 식별자가 그대로 돌아온 값이며 ``repr``에서도 가리지 않습니다."""

    # 앱 근거: OrgTk.java:28-52; OgTicketInquiryOut.java:27. 전송 키는 속성명에 따른 추정입니다.
    pnr_no: str | None = wire("pnrNo")
    ticket_kind_code: str | None = wire("tkKndCd")
    original_sale_datetime: str | None = wire("ogtkSaleDt")
    original_window_no: str | None = wire("ogtkSaleWctNo")
    original_sale_sequence: str | None = wire("ogtkSaleSqno")
    original_return_password: str | None = wire("ogtkRetPwd")
    member_card_no: str | None = wire("mbCrdNo")
    adult_count: str | None = wire("adulCnt")
    child_count: str | None = wire("chilCnt")
    group_discount_count: str | None = wire("grpDcntCnt")
    passenger_type_division_code: str | None = wire("psgTpDvCd")
    received_amount: str | None = wire("rcvdAmt")
    received_fare: str | None = wire("rcvdFare")
    received_price: str | None = wire("rcvdPrc")
    change_sale_transaction_no: str | None = wire("chgSaleTno")
    sms_send_flag: str | None = wire("smsSndFlg")
    forced_sale_reason_text: str | None = wire("frcSaleRsnCont")
    journeys: tuple[OriginalTicketJourney, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """변경 기준인 원표 목록을 담습니다."""

    # 앱 근거: NetworkApi.java:234-236; OgTicketInquiryOut.java:26-27,54.
    tickets: tuple[OriginalTicket, ...] = ()


@dataclass(frozen=True)
class DelayCertificateRow:
    """지연확인증 한 행을 담습니다.

    ``run_date``를 뺀 일곱 필드는 응답에 반드시 있어야 하며, 없거나 ``null``이면 ``KorailProtocolError``가 발생합니다. 앱은
    ``delay_arrival_flag``가 특정 값인 행만 보여 주지만, 라이브러리는 거르지 않고 모든 행을 돌려줍니다. 앱이 고르는 값은 앱 내부
    값이 공개돼 있지 않아 확인하지 못했습니다."""

    # DelayCertificate.java:57-60 의 마스크는 여덟 키 모두 필수로 둡니다. 앱은 dlayArvFlg 가 보호된 1글자 값과 같은 행만 보여
    # 주므로(DelayCertificateViewModel.java:139-150) 이 라이브러리는 거르지 않고 모두 돌려줍니다.
    run_day: str = wire("runDay", required_str)
    train_no: str = wire("trnNo", required_str)
    departure_station_code: str = wire("dptRsStnCd", required_str)
    arrival_station_code: str = wire("arvRsStnCd", required_str)
    arrival_station_name: str = wire("arvRsStnNm", required_str)
    delay_arrival_flag: str = wire("dlayArvFlg", required_str)
    delay_minutes: str = wire("trnDlayTm", required_str)
    # runDt 는 마스크상 필수이지만 실서버 응답에는 없었습니다.
    #: 운행일(``runDt``)입니다. 응답에 없으면 ``None``이며, 운행일은 ``run_day``에도 있습니다(예: 요일이 붙은 날짜).
    run_date: str | None = wire("runDt")
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DelayCertificateResponse(BaseKorailResponse):
    """지연확인증의 행을 담습니다.

    응답에 목록(``dlayList``)이 없거나 ``null``이면 ``delays``는 빈 튜플입니다."""

    # dlay.athnIsu.do. dlayList 는 선택·nullable 입니다(DelayCertificateOut.java:53-59).
    delays: tuple[DelayCertificateRow, ...] = ()


@dataclass(frozen=True)
class DelayReturnReceiptResponse(BaseKorailResponse):
    """지연료 반환 영수증을 담습니다.

    세 필드 모두 응답에 없으면 ``None``입니다."""

    # 세 필드 모두 선택입니다(DelayReturnReceiptOut.java:53-69).
    return_date: str | None = wire("retDt")
    payment_method_name: str | None = wire("dlayFarePymtMtdNm")
    return_amount: str | None = wire("dlayFareRetAmt")
