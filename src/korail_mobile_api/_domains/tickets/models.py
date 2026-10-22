# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정 조회 모델입니다. raw는 원문 객체이며 frozen 모델도 내부 값을 동결·마스킹하지 않습니다; 개인정보를 로그에 남기지 마십시오. 선택 스칼라의 부재는 None입니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..airport_bus.models import MaasServiceDetail
from ..common.models import BaseKorailResponse


@dataclass(frozen=True)
class TicketListTrain:
    """승차권 한 장에 포함된 열차 구간 정보를 담습니다.

    호차 번호(``car_no``)처럼 서버가 정수로 보내는 값도 문자열로 담습니다."""

    # 앱 근거: TicketListTrainInfo.java:72. 라이브 이력 139행: 21개 키가 모두 있었고 h_srcar_no 는 String 선언과 달리 모두 JSON
    # 정수였습니다(문자열로 받습니다).
    journey_sequence: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    seat_count: str | None = None
    passenger_type_code: str | None = None
    received_amount: str | None = None
    buyer_name: str | None = None
    passenger_name: str | None = None
    train_suspension_flag: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TicketListTicket:
    """승차권 한 장의 식별자·상태와 열차 구간을 담습니다."""

    pnr_no: str | None = None
    sale_window_no: str | None = None
    sale_date: str | None = None
    return_sale_date: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_status_code: str | None = None
    # 한 계정 관측에서 131행 모두에 있었습니다.
    #: 승차권 종류 코드(``h_tk_knd_cd``)입니다. 예약 행이 아니라 승차권 행의 값을 읽습니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # h_tk_sqno 선언: MyTicketListOutTicket.java:92. 다른 조건에서도 필수인지는 검증 못 함입니다.
    ticket_sequence: str | None = None
    #: 승차권 상태 이름(``h_tk_stt_nm``)입니다. 서버가 보낸 이름을 그대로 담으며 ``ticket_status_code``를 따로 번역하지 않습니다.
    ticket_status_name: str | None = None
    # 앱 버튼 조건은 상세 플래그와 사용 여부 검사입니다(NormalTicketSectionKt.java:951, TicketHelper.java:3173-3199). 비교 리터럴은
    # 보호돼 있습니다.
    #: 반환 가능 여부 플래그(``h_ret_psb_flg``)입니다. 앱은 승차권 상세의 플래그와 사용 여부도 함께 확인하므로 이 값만으로 환불할 수
    #: 있는지 판단할 수 없습니다. 앱이 비교하는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    return_possible_flag: str | None = None
    use_transaction_no: str | None = None
    notify_use_transaction_no: str | None = None
    # 실서버 검증 못 함. 앱은 목록 값을 상세에 주입합니다(MyTicketBaseViewModel.java:769, MyTicketDetailViewModel.java:1521). 상세
    # 40응답에는 두 후보 키가 없었습니다.
    #: 대리수령 대상 여부 플래그(``h_pbp_acep_tgt_flg``)입니다. 승차권 상세 응답에는 이 값이 보통 없으므로, 앱처럼 환불하려면 이 값을
    #: ``refund``의 ``pbp_acceptance_target_flag``로 넘기세요.
    pbp_acceptance_target_flag: str | None = None
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
    departure_datetime: str | None = None
    ticket_kind_code: str | None = None
    list_count: str | None = None
    seat_assign_count: int | None = None
    ticket_status: str | None = None
    is_finished: bool | None = None
    is_history: bool | None = None
    is_emergency: bool | None = None
    display_ticket_name: str | None = None
    is_non_member: bool | None = None
    is_transfer: bool | None = None
    is_wheelchair_member: bool | None = None
    is_rail_police_enabled: bool | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # 선택값의 타입이 어긋나면 해당 값만 비웁니다. addSrvInfo(MyTicketListOutReservation.java:39)는 MaaS 의 AddSrvItem 과 같은 타입이라 모델을
    # 공유합니다(MaasDetailOut.java:27, AddSrvItem.java:28-49).
    additional_service: MaasServiceDetail | None = None
    # ticketKind 는 보호된 enum 이름을 매핑하지 않고 문자열로 둡니다 (MyTicketListOutReservation.java:52,59;
    # TicketDefine.java:1078-1131).
    #: 승차권 종류(``ticketKind``)입니다. 서버가 보낸 문자열을 그대로 담으며, 값의 의미는 앱 내부 값이 공개돼 있지 않아 확인하지
    #: 못했습니다.
    ticket_kind: str | None = None


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    """현재 승차권 또는 구매 이력을 예약별로 묶어 담습니다."""

    reservations: tuple[TicketListReservation, ...] = ()
    #: 전체 건수(``h_total_cnt``)입니다. 키가 없으면 ``None``입니다.
    total_count: str | None = None


@dataclass(frozen=True)
class DepositBank:
    """입금 가능한 은행의 코드와 이름을 담습니다."""

    code: str | None = None
    display_name: str | None = None
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
    fare: str | None = None
    original_sale_date: str | None = None
    window_no: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    ticket_sequence: str | None = None
    ticket_kind_code: str | None = None
    original_ticket_sale_date: str | None = None
    received_amount: str | None = None
    train_class_code: str | None = None
    room_class_code: str | None = None
    train_no: str | None = None
    departure_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_station_code: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    ticket_status_code: str | None = None
    ticket_status_name: str | None = None
    buyer_name: str | None = None
    passenger_name: str | None = None
    page_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    """지연할인권 목록과 페이지 정보를 담습니다.

    페이지 정보(``current_page``, ``total_pages``, ``total_count``, ``row_count``, ``last_page_flag``)는 응답의 ``main_info``
    블록에서 읽습니다. 블록이 없으면 모두 ``None``입니다."""

    # main_info는 DTO 밖 서버 추가 블록입니다(DelayDiscountViewOut.java:24,51). 날짜 입력 8종에서 12키를 확인했지만 할인권 없는
    # 응답뿐이었습니다.
    items: tuple[DelayDiscountTicket, ...] = ()
    current_page: str | None = None
    total_pages: str | None = None
    total_count: str | None = None
    row_count: str | None = None
    last_page_flag: str | None = None


@dataclass(frozen=True)
class DiscountCoupon:
    """할인쿠폰 한 장의 조건과 유효기간을 담습니다."""

    guide: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    discount_kind_code: str | None = None
    # CouponOutInfo.java:63.
    #: 할인율·할인액 구분 코드(``h_disc_rt_amt_dv_cd``)입니다. 코드 값의 의미를 확인하지 못했습니다.
    discount_rate_amount_division_code: str | None = None
    weekday_fare_discount: str | None = None
    weekday_price_discount: str | None = None
    weekend_fare_discount: str | None = None
    weekend_price_discount: str | None = None
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    """할인쿠폰 목록과 안내를 담습니다."""

    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None
    total_count: str | None = None
    row_count: str | None = None


@dataclass(frozen=True, kw_only=True)
class ReceiptPayment:
    """영수증의 결제수단 한 행을 담습니다."""

    payment_method: str
    approval_date: str
    installment_months: int
    amount: int
    account_no: str
    approval_no: str
    card_no: str
    point_no: str
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class ReceiptCashPayment:
    """영수증에 포함된 현금영수증 한 행을 담습니다.

    인증 도메인 인식번호와 현금영수증 승인번호도 가리지 않고 서버가 보낸 값 그대로 담습니다."""

    # 앱 근거: ReceiptInfo.java:37. String 4개·int 금액 1개이며 전송 키는 CashReceiptInfo.java:26-35,52 의 명시적 @SerialName
    # 입니다.
    #: 승인 방법 이름(``h_apv_mtd_nm``)입니다.
    approval_method_name: str
    authentication_domain_recognition_no: str
    cash_receipt_approval_no: str
    cash_receipt_transaction_division_code: str
    total_approved_amount: int
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True, kw_only=True)
class TicketReceipt:
    """승차권 영수증의 이용 내역과 결제 정보를 담습니다."""

    travel_date: str
    departure_station: str
    departure_time: str
    arrival_station: str
    arrival_time: str
    commuter_kind_code: str
    journey_type_code: str
    printed_discount_name: str
    printed_discount_kind_code: str
    print_type: str
    seat_class_name: str
    ticket_kind_code: str
    ticket_kind_name: str
    ticket_status_code: str
    train_class_code: str
    train_class_name: str
    train_group_code: str
    train_no: str
    passenger_counts: tuple[int, int, int]
    received_amount: int
    card_refund_amount: int
    refund_fee: int
    refund_received_amount: int
    point_refund_amount: int
    payments: tuple[ReceiptPayment, ...] = ()
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str
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
    korail_point: str | None = None
    #: 서버가 알려 준 할인쿠폰 개수(``h_disc_coup_cnt``)입니다. ``get_discount_coupons`` 결과의 개수와 항상 같다는 보장은 없습니다.
    discount_coupon_count: str | None = None
    delay_discount_count: str | None = None
    disability_flag: str | None = None
    welfare_discount_class_name: str | None = None
    welfare_discount_class_code: str | None = None
    customer_lead_flag_name: str | None = None
    phone_verified_flag: str | None = None
    email_verified_flag: str | None = None
    contact_channel_content: str | None = None
    # 소셜 연동 플래그의 서비스별 순서는 7.0.6 에서 미확인입니다. 소비 값이 보호된 LoginMethodApiData.java:18-21 을 거치므로 Python
    # 필드명을 확정된 매핑으로 신뢰하지 않습니다.
    #: 네이버 연동 여부로 추정하는 플래그(``h_logn_tp_cd1``)입니다.
    naver_linked_flag: str | None = None
    #: 카카오 연동 여부로 추정하는 플래그(``h_logn_tp_cd2``)입니다.
    kakao_linked_flag: str | None = None
    #: 구글 연동 여부로 추정하는 플래그(``h_logn_tp_cd4``)입니다.
    google_linked_flag: str | None = None
    #: 애플 연동 여부로 추정하는 플래그(``h_logn_tp_cd5``)입니다.
    apple_linked_flag: str | None = None
    # ``h_cust_lead_flg``(``MyXPointViewOut.java:43``) — 보조견 등록 플래그 그 자체.
    customer_lead_flag: str | None = None
    #: 장애 유형 코드(``h_hdcp_tp_cd``)입니다. 장애 유형은 ``disability_flag``가 아니라 이 필드와 ``disability_type_name``에
    #: 있습니다.
    disability_type_code: str | None = None
    #: 장애 유형 이름(``h_hdcp_tp_cd_nm``)입니다.
    disability_type_name: str | None = None


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 적립 또는 사용 내역 한 행을 담습니다."""

    # AmtSpecOutSpecInfo.java:29-35 가 선언하는 것이 정확히 아래 일곱 필드입니다. 라이브에서 3페이지 14행 전부가 이 일곱 키를
    # 문자열로 싣고 그 밖의 키는 없었습니다.
    departure_date: str | None = None
    point_division_name: str | None = None
    accrual_division_name: str | None = None
    receipt_division_name: str | None = None
    point_amount: str | None = None
    saved_point_value: str | None = None
    settlement_amount: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """마일리지 내역 한 페이지와 적립·사용 합계를 담습니다.

    응답에 따로 있는 합계 필드는 서로 합치지 않고 각각 담습니다."""

    # 앱 근거: AmtSpecOut.java:29-39,199-247. pgCnt 는 AmtSpecOut.java:32.
    #: 전체 페이지 수(``pgCnt``)입니다.
    page_count: str | None = None
    query_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = None
    total_used_rail_point_1: str | None = None
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = None
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    """다자녀 할인 대상으로 등록된 가족 한 명을 담습니다."""

    birth_date: str | None = None
    customer_family_name: str | None = None
    discount_kind_code: str | None = None
    family_sequence: str | None = None
    passenger_type_code: str | None = None
    passenger_type_name: str | None = None
    room_class_code: str | None = None
    requested_discount_kind_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    """다자녀 할인 대상 가족 목록을 담습니다."""

    targets: tuple[MultiChildDiscountTarget, ...] = ()


@dataclass(frozen=True)
class CustomerTripInfo:
    """계정에 저장된 여행 편의설정을 담습니다."""

    additional_seat_attribute_code: str | None = None
    adult_disabled_person_count: str | None = None
    adult_count: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    baby_accompanying_person_count: str | None = None
    changed_at: str | None = None
    changed_by: str | None = None
    child_count: str | None = None
    child_disabled_person_count: str | None = None
    customer_management_no: str | None = None
    day_code: str | None = None
    direction_seat_attribute_group_code: str | None = None
    direct_transfer_division_code: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    early_train_departure_time: str | None = None
    elderly_person_count: str | None = None
    included_flag: str | None = None
    job_start_hour: str | None = None
    location_seat_attribute_group_code: str | None = None
    media_division_code: str | None = None
    room_class_code: str | None = None
    passenger_total: str | None = None
    registered_at: str | None = None
    registration_sequence: str | None = None
    registered_by: str | None = None
    trip_day_no: str | None = None
    train_classification_code: str | None = None
    train_connection_flag: str | None = None
    train_group_code: str | None = None
    usage_day_no: str | None = None
    # @SerialName 이 없어 와이어 철자는 보호됨 이며 코틀린 필드명을 추정해 사용합니다(CustTripInfo.java:48).
    #: 상품 번호입니다. 추정한 응답 키(``gdNo``)로 읽으며, 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
    goods_no: str | None = None
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
    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석변경이 가능한 승차역과 잔여석을 담습니다.

    응답의 도착역 코드·이름과 도착역 편성·운행 순서는 읽지 않습니다. 원본은 ``raw``에 남습니다."""

    # 앱 근거: ChgStnInfo.java:21-35; SeatAvailabilityOut.java:32. DTO 의 도착역 코드·이름·편성/운행순서 4개 필드는 이 모델에서
    # 읽지 않습니다.
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_construction_order: str | None = None
    departure_run_order: str | None = None
    general_remaining_seats: str | None = None
    special_remaining_seats: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """자율 좌석변경 시 선택할 변경 사유를 담습니다.

    필드는 추정한 응답 키(``qryCode``, ``qryOrdr``, ``frcSaleRsnCont``)로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아
    확인하지 못했습니다."""

    # 앱 근거: ChgRsnInfo.java:21-24; SeatAvailabilityOut.java:31. serializer descriptor 의 이름이 보호돼 있어
    # (ChgRsnInfo$$serializer.java:34-36) 전송 키는 속성명에 따른 추정입니다.
    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """자율 좌석변경의 대상 역·사유·열차 정보를 담습니다."""

    # 앱 근거: NetworkApi.java:806-808; SeatAvailabilityOut.java:28-42,68.
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    train_group_code: str | None = None
    train_group_name: str | None = None
    run_date: str | None = None
    general_reservation_possible_code: str | None = None
    special_reservation_possible_code: str | None = None
    change_before_departure_construction_order: str | None = None
    change_before_arrival_construction_order: str | None = None
    existing_departure_run_order: str | None = None
    existing_arrival_run_order: str | None = None
    stations: tuple[SelfSeatChangeStation, ...] = ()
    reasons: tuple[SelfSeatChangeReason, ...] = ()


@dataclass(frozen=True)
class OriginalTicketSeat:
    """변경 기준인 원표의 좌석 정보를 담습니다."""

    # 앱 근거: SeatInfo.java:25-51; JrnyInfo.java:58. 대리수령용 Seat.java:27-36 과는 이름과 구조가 다른 타입입니다.
    passenger_sequence: str | None = None
    assign_sequence: str | None = None
    passenger_type_code: str | None = None
    room_class_code: str | None = None
    car_no: str | None = None
    seat_no: str | None = None
    seat_count: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    requested_seat_attribute_code: str | None = None
    direction_seat_attribute_code: str | None = None
    location_seat_attribute_code: str | None = None
    smoking_seat_attribute_code: str | None = None
    additional_seat_attribute_code: str | None = None
    etc_seat_attribute_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """변경 기준인 원표의 구간과 좌석 목록을 담습니다."""

    # 앱 근거: OrgTk.java:38; JrnyInfo.java:29-63. 대리수령용 Jrny.java:29-38 과 다릅니다.
    journey_sequence: str | None = None
    journey_order: str | None = None
    journey_type_code: str | None = None
    train_no: str | None = None
    train_group_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    arrival_construction_order: str | None = None
    goods_no: str | None = None
    total_seat_count: str | None = None
    total_standing_count: str | None = None
    general_change_allowed_flag: str | None = None
    single_ticket_flag: str | None = None
    seats: tuple[OriginalTicketSeat, ...] = ()
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """변경 기준인 원표의 식별자·상태·여정을 담습니다.

    필드는 추정한 응답 키로 읽습니다. 실제 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. ``original_*`` 필드는
    요청한 승차권의 반환 식별자가 그대로 돌아온 값이며 ``repr``에서도 가리지 않습니다."""

    # 앱 근거: OrgTk.java:28-52; OgTicketInquiryOut.java:27. 전송 키는 속성명에 따른 추정입니다.
    pnr_no: str | None = None
    ticket_kind_code: str | None = None
    original_sale_datetime: str | None = None
    original_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    member_card_no: str | None = None
    adult_count: str | None = None
    child_count: str | None = None
    group_discount_count: str | None = None
    passenger_type_division_code: str | None = None
    received_amount: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    change_sale_transaction_no: str | None = None
    sms_send_flag: str | None = None
    forced_sale_reason_text: str | None = None
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
    run_day: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    arrival_station_name: str
    delay_arrival_flag: str
    delay_minutes: str
    # runDt 는 마스크상 필수이지만 실서버 응답에는 없었습니다.
    #: 운행일(``runDt``)입니다. 응답에 없으면 ``None``이며, 운행일은 ``run_day``에도 있습니다(예: 요일이 붙은 날짜).
    run_date: str | None = None
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
    return_date: str | None = None
    payment_method_name: str | None = None
    return_amount: str | None = None
