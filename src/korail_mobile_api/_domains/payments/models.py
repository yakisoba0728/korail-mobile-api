# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""결제·환불 응답 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class DiscountCardSection:
    """N카드를 적용할 수 있는 구간 한 개를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 적용 구간(AppSegInfo.java:24-37,
    # DiscountCardInfo.java:28). @SerialName 별칭이 없는 키는 보호된 serializer 대신 속성명을 사용한 추정입니다.
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    journey_sequence: str | None = None
    journey_type_code: str | None = None
    train_group_code: str | None = None
    # 경유 이름(AppSegInfo.java:36)은 NCardReservationViewModel.java:154-164 의 Triple 을 거쳐
    # TrainScheduleViewModel.java:2639,2730-2736,2749,2831 에서 입력에 복사됩니다. 대상 필드: AssignScheduleIn.java:41 의
    # stlbDturDvNm1. 라이브러리에서는 SeatAssignmentScheduleRequest.standing_detour_division_name 이 같은 폼 키로 나갑니다.
    #: 경유 구분 이름(``stlbDturDvNm``)입니다. 앱은 N카드 구간으로 좌석배정 열차를 조회할 때 이 값을
    #: ``SeatAssignmentScheduleRequest.standing_detour_division_name``과 같은 입력 필드로 보냅니다.
    detour_division_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세에 포함된 N카드와 적용 구간을 담습니다."""

    # N카드 적용 구간은 상세 DTO에 따르며 코드 평문·실서버 검증 못 함입니다(DiscountCardInfo.java:27-32; TicketDetailOut.java:49,438).
    # h_dcnt_crd_no: DiscountCardInfo.java:113 의 @SerialName.
    #: N카드 번호(``h_dcnt_crd_no``)입니다.
    card_no: str | None = None
    # 실서버 검증 못 함. 기간연장 플래그는 DiscountCardInfo.java:30,117에 선언됩니다. 앱은 이 값을 비교해 연장 버튼에 전달합니다
    # (NCardTicketSectionKt.smali:7821-7843).
    #: 기간 연장 가능 여부 플래그(``h_dcnt_crd_trm_extn_psb_flg``)입니다.
    term_extension_possible_flag: str | None = None
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

    # 앱 근거: NetworkApi.java:598-600. 키 근거: RefundCommissionOut.java:35-41,62,140-164.
    refund_amount: str | None = None
    refund_fee: str | None = None
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    secondary_message_code: str | None = None
    secondary_message_text: str | None = None
    # raw/서버 필드에서 복원하지 않습니다. 클라이언트가 검증한 조회 입력만 로컬에서 연결합니다.
    _request_context: _RefundCommissionContext | None = field(
        default=None, repr=False, compare=False, kw_only=True
    )


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 한 자리를 담습니다."""

    car_no: str | None = None
    seat_no: str | None = None
    buyer_name: str | None = None
    checkin_status_code: str | None = None
    discount_kind_code: str | None = None
    discount_kind_name: str | None = None
    passenger_type_code: str | None = None
    passenger_type_name: str | None = None
    seat_group_name: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """환불 대상 승차권의 여정 한 개를 담습니다."""

    journey_sequence: str | None = None
    journey_type_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_name: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_name: str | None = None
    train_no: str | None = None
    train_class_name: str | None = None
    room_class_name: str | None = None
    platform_no: str | None = None
    seats: tuple[RefundTicketSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 식별자·여정·운임 상세를 담습니다.

    일부 필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 앱 근거: TicketDetailOut.java:38,117. 별칭 없는 전송 키는 추정입니다.
    pnr_no: str | None = None
    sale_date: str | None = None
    sale_time: str | None = None
    window_name: str | None = None
    original_sale_date: str | None = None
    original_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    # retPsbFlg는 환불 성공 보장이 아닙니다(TicketDetailOut.java:71). 실서버 관측: 상세 40응답은 Y였지만 수수료 조회는 승차일 경과
    # 5건 WRT200022·이미 반환 2건 WRT200399였고, 목록 이력 143장은 N이었습니다. 앱은 사용 여부도 검사합니다
    # (NormalTicketSectionKt.java:951).
    #: 환불 가능 여부 플래그(``retPsbFlg``)입니다. ``"Y"``여도 환불할 수 있다는 보장은 없으므로 ``get_refund_commission``의 결과로
    #: 확인하세요.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    # 탑승자 이름·생년월일 요약이며 동승자(h_compa_nm/h_compa_brth)나 psgNmList 와 별개입니다(TicketDetailOut.java:410,418).
    #: 탑승자 이름(``h_abrd_ps_nm``)입니다. 동승자 이름(``companion_name``)이나 ``passenger_names`` 목록과는 다른 필드입니다.
    passenger_name: str | None = None
    #: 탑승자 생년월일(``s_brth``)입니다.
    passenger_birth_date: str | None = None
    #: 동승자 이름(``h_compa_nm``)입니다.
    companion_name: str | None = None
    #: 동승자 생년월일(``h_compa_brth``)입니다.
    companion_birth_date: str | None = None
    # 상세 40응답(20승차권×2모드)에는 후보 키가 없었으며 목록 Y 6건도 같았습니다. 목록 키는 MyTicketListOutTicket.java:92,300, 상세
    # 필드·setter는 TicketDetailOut.java:65,1936입니다.
    #: 대리수령 대상 여부 플래그입니다. 응답에 ``pbpAcepTgtFlg`` 키가 있을 때만 채우며 보통은 ``None``입니다. 앱처럼 환불하려면
    #: ``get_ticket_list`` 승차권의 ``pbp_acceptance_target_flag``를 ``refund``에 넘기세요.
    pbp_acceptance_target_flag: str | None = None
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    # h_qrcode: TicketDetailOut.java:478.
    #: 이 승차권의 QR 코드(``h_qrcode``)입니다.
    qr_code: str | None = None
    # psgNmList: @SerialName 이 없어 와이어 철자는 보호됨, 코틀린 필드명을 추정해 사용합니다. 각 원소는 아직 행 단위로 모델링하지
    # 않고 원본 그대로 노출합니다.
    #: 승객 이름 목록(``psgNmList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    passenger_names: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    # seatTicketList — List<SeatAssignInfo>, 보호됨.
    #: 좌석 배정 목록(``seatTicketList``)입니다. 추정한 응답 키로 읽으며, 각 원소는 해석하지 않은 원본 매핑입니다.
    seat_tickets: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    # limousine — 단일 객체, 보호됨.
    #: 연계된 리무진 예약(``limousine``)입니다. 추정한 응답 키로 읽은 원본 매핑이며, 없으면 ``None``입니다.
    limousine: Mapping[str, object] | None = field(default=None, compare=False)
    # dtlList — List<DelayInfo>, 보호됨.
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

    # stlList 는 필수이면서 null 일 수 있습니다(RefundTicketOut.java:48-53).

    settlement_method_codes: tuple[str, ...] = ()
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """역에서 발권한 승차권의 환불 확인 응답에 들어 있는 원표 한 행을 담습니다."""

    pnr_no: str
    original_sale_date: str | None = None
    original_sale_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    ticket_kind_code: str | None = None
    refund_division_code: str | None = None
    refund_reason_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """역에서 발권한 승차권의 환불 확인 결과(금액과 원표 목록)를 담습니다.

    서버가 원표 목록을 ``null``로 보내면 ``original_tickets``는 빈 튜플이고 ``original_ticket_list_is_null``이
    ``True``입니다."""

    received_amount: str | None = None
    refund_fee: str | None = None
    refund_amount: str | None = None
    popup_message: str | None = None
    result_message: str | None = None
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionResponse(BaseKorailResponse):
    """역에서 발권한 승차권의 환불 실행 결과를 담습니다."""

    refund_division_code: str | None = None


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    """결제 결과에 포함된 쿠폰 정보를 담습니다."""

    certificate_password: str | None = None
    coupon_no: str | None = None
    management_close_date: str | None = None
    management_start_date: str | None = None
    ticket_return_no: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTicket:
    """결제로 발권된 승차권 한 장의 식별자와 반환 식별자를 담습니다."""

    ticket_sequence: str | None = None
    sale_date: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    return_no: str | None = None
    recipient_name: str | None = None
    discount_card_no: str | None = None
    ticket_price: str | None = None
    ticket_fare: str | None = None
    bz5_fare_discount_amount: str | None = None
    bz6_fare_discount_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    standard_seat_price_fare: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """결제 결과의 정산수단 한 행을 담습니다.

    카드번호·승인번호 같은 값이 들어 있을 수 있으므로 로그에 남길 때 주의하세요."""

    # 거래·오류 필드(ReservationPaymentOutActInfo.java:28-31,52)라는 이유만으로 개인정보가 없다고 보장할 수 없습니다.

    settlement_sequence: str | None = None
    settlement_type_code: str | None = None
    settlement_result: str | None = None
    transaction_division: str | None = None
    card_installment_count: str | None = None
    installment_months: str | None = None
    settlement_amount: str | None = None
    settlement_card_no: str | None = None
    card_company_code: str | None = None
    card_company_name: str | None = None
    approval_date: str | None = None
    approval_time: str | None = None
    approval_no: str | None = None
    point_division: str | None = None
    point_no: str | None = None
    point_approval_no: str | None = None
    remnant_amount: str | None = None
    remote_point: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """결제 결과에 포함된 두 구간 단체석 정보를 담습니다."""

    room_class_name_1: str | None = None
    car_no_1: str | None = None
    seat_no_start_1: str | None = None
    seat_no_end_1: str | None = None
    seat_count_1: str | None = None
    group_name_1: str | None = None
    room_class_name_2: str | None = None
    car_no_2: str | None = None
    seat_no_start_2: str | None = None
    seat_no_end_2: str | None = None
    seat_count_2: str | None = None
    group_name_2: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    """카드 결제 시도의 발권·정산·좌석 결과를 담습니다."""

    image_ticket_flag: str | None = None
    # 관측: 카드 결제 응답에서는 빈 문자열이었습니다.
    #: 결제 응답의 예약 번호 필드입니다. 카드 결제 응답에서는 빈 문자열일 수 있습니다. 결제 응답에는 PNR(``h_pnr_no``)이
    #: 없으므로 PNR은 홀드의 ``pnr_no``를 쓰세요.
    reservation_no: str | None = None
    settlement_approval_no: str | None = None
    total_received_amount: str | None = None
    settlement_amount: str | None = None
    total_settlement_amount: str | None = None
    customer_no: str | None = None
    member_card_no: str | None = None
    buyer_name: str | None = None
    publication_start_no: str | None = None
    publication_end_no: str | None = None
    mixed_settlement_division: str | None = None
    cancellation_fee: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
    tickets: tuple[ReservationPaymentTicket, ...] = ()
    settlements: tuple[ReservationPaymentSettlement, ...] = ()
    table_seats: tuple[ReservationPaymentTableSeat, ...] = ()
    # 여기부터 ReservationPaymentOut 의 나머지 스칼라입니다(ReservationPaymentOut.java:90 의 @SerialName).
    #: 창구 번호(``h_wct_no``)입니다.
    window_no: str | None = None
    settlement_count: str | None = None
    discount_card_count: str | None = None
    total_price: str | None = None
    total_fare: str | None = None
    total_discount_amount: str | None = None
    adult_count: str | None = None
    child_count: str | None = None
    table_seat_count: str | None = None
    ticket_count: str | None = None
    settlement_type_code: str | None = None
    trade_division: str | None = None
    remark: str | None = None
    survey_flag: str | None = None
    survey_title: str | None = None
    survey_text: str | None = None
    survey_url: str | None = None
