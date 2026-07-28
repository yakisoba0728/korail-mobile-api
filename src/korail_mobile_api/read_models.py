"""읽기 전용 조회가 돌려주는 타입 — 승차권, 환불, 할인카드, 마이페이지.

열차 검색과 좌석 조회 쪽 타입은 :mod:`korail_mobile_api.models` 에 있다.
여기 있는 것은 전부 ``frozen=True`` 데이터클래스이고
:class:`~korail_mobile_api.models.BaseKorailResponse` 를 상속하거나 그 안에
들어가는 행 타입이다.

이름을 붙이지 않은 서버 필드는 어느 모델에서든 ``raw`` 에 그대로 남아 있다.
``repr=False`` 인 필드는 로그에 실수로 찍히지 않게 표현에서 뺀 것이고, 전선
이름이 :mod:`korail_mobile_api.redaction` 에 등록된 것은 ``raw`` 안에서도
마스킹된다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


@dataclass(frozen=True)
class ServiceStatusResponse(BaseKorailResponse):
    pass


@dataclass(frozen=True)
class CartItem:
    service_code: str | None = None
    provider_name: str | None = None
    product_name: str | None = None
    item_type: str | None = None
    departure_date: str | None = None
    received_amount: str | None = None
    reservation_received_date: str | None = None
    ticket_count: int | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    lump_sum_target_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)
    virtual_reservation_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    @property
    def usage_window(
        self,
    ) -> tuple[str | None, str | None, str | None]:
        return (
            self.usage_start_date,
            self.usage_start_time,
            self.usage_close_time,
        )


@dataclass(frozen=True)
class CartListResponse(BaseKorailResponse):
    items: tuple[CartItem, ...] = ()


@dataclass(frozen=True)
class DepositBank:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    fare: str | None = None
    usable_until_date: str | None = None
    original_sale_date: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    items: tuple[DelayDiscountTicket, ...] = ()


@dataclass(frozen=True)
class DiscountCoupon:
    guide: str | None = None
    expiration_date: str | None = None
    discount_values: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None


@dataclass(frozen=True)
class PassOffice:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassAvailabilityResponse(BaseKorailResponse):
    open_dates: tuple[str, ...] = ()
    ticket_issue_dates: tuple[str, ...] = ()
    offices: tuple[PassOffice, ...] = ()


@dataclass(frozen=True)
class TripMenuContent:
    title: str | None = None
    detail: str | None = None
    content_type: str | None = None
    active: str | None = None
    agree: str | None = None
    info: str | None = None
    image: str | None = field(default=None, repr=False)
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TripMenuItem:
    title: str | None = None
    detail: str | None = None
    menu_type: str | None = None
    button: str | None = None
    contents: tuple[TripMenuContent, ...] = ()
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TripMenuResponse(BaseKorailResponse):
    items: tuple[TripMenuItem, ...] = ()
    popup_message: str | None = None


@dataclass(frozen=True)
class ProductReservation:
    product_name: str | None = None
    reservation_status: str | None = None
    payment_deadline: str | None = None
    payment_status: str | None = None
    virtual_reservation_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ProductReservationListResponse(BaseKorailResponse):
    items: tuple[ProductReservation, ...] = ()
    total_count: int | None = None


@dataclass(frozen=True)
class ProductDetailResponse(BaseKorailResponse):
    product_name: str | None = None
    reservation_status: str | None = None
    cancellation_deadline: str | None = None
    cancellation_amount: str | None = None
    cancellation_fee: str | None = None
    received_amount: str | None = None
    total_amount: str | None = None
    usage_period: str | None = None
    included_item_names: tuple[str, ...] = ()
    virtual_reservation_no: str | None = field(default=None, repr=False)
    detail_raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ReceiptPayment:
    payment_method: str | None = None
    approval_date: str | None = None
    installment_months: int | None = None
    amount: int | None = None
    account_no: str | None = field(default=None, repr=False)
    approval_no: str | None = field(default=None, repr=False)
    card_no: str | None = field(default=None, repr=False)
    point_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ReceiptCashPayment:
    """영수증의 현금영수증 줄 하나(``ReceiptDao.CashReceiptInfo``).

    :class:`ReceiptPayment` 와 형제다. ``stl_info`` 는 카드·포인트 정산을,
    ``cash_rcet_info`` 는 현금영수증을 싣는다
    (``ReceiptDao.java:12-40,43-44``). 앱에서 정수인 것은
    ``h_tot_apv_amt`` 뿐이고 나머지는 문자열이다.
    """

    #: ``h_apv_mtd_nm`` — 승인 방법 이름.
    approval_method_name: str | None = None
    #: ``h_athn_dmn_rcgn_no`` — 영수증이 어느 번호 앞으로 발행됐는지(휴대폰
    #: 또는 사업자번호). 신원으로 다뤄 표현에서 뺀다.
    authentication_domain_recognition_no: str | None = field(
        default=None, repr=False
    )
    #: ``h_cash_rcet_apv_no`` — 현금영수증 승인번호.
    cash_receipt_approval_no: str | None = field(default=None, repr=False)
    #: ``h_cash_rcet_txn_dv_cd`` — 발행인지 취소인지.
    cash_receipt_transaction_division_code: str | None = None
    #: ``h_tot_apv_amt`` — 총 승인금액.
    total_approved_amount: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TicketReceipt:
    travel_date: str | None = None
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    commuter_kind_code: str | None = None
    journey_type_code: str | None = None
    printed_discount_name: str | None = None
    print_type: str | None = None
    seat_class_name: str | None = None
    ticket_kind_code: str | None = None
    ticket_status_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    train_no: str | None = None
    passenger_counts: tuple[int | None, int | None, int | None] = (
        None,
        None,
        None,
    )
    received_amount: int | None = None
    card_refund_amount: int | None = None
    refund_fee: int | None = None
    refund_received_amount: int | None = None
    point_refund_amount: int | None = None
    payments: tuple[ReceiptPayment, ...] = ()
    #: ``cash_rcet_info`` — 현금영수증 줄들. 현금영수증이 없는 영수증에서는
    #: 비어 있다. 카드·포인트 정산을 싣는 :attr:`payments` 의 형제 목록이다.
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TicketReceiptResponse(BaseKorailResponse):
    items: tuple[TicketReceipt, ...] = ()


@dataclass(frozen=True)
class ReservationHistoryTrain:
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    run_date: str | None = None
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    reservation_type_code: str | None = None
    acceptance_possible_flag: str | None = None
    payment_flag: str | None = None
    settlement_flag: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    title: str | None = field(default=None, repr=False)
    car_no: str | None = field(default=None, repr=False)
    content: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TrainScheduleItem:
    train_no: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    train_class_code: str | None = field(default=None, repr=False)
    train_class_name: str | None = field(default=None, repr=False)
    run_date: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    arrival_date: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    departure_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    arrival_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    departure_run_order: str | None = field(default=None, repr=False)
    arrival_run_order: str | None = field(default=None, repr=False)
    car_type_name: str | None = field(default=None, repr=False)
    general_room_name: str | None = field(default=None, repr=False)
    special_room_name: str | None = field(default=None, repr=False)
    general_reservation_code: str | None = field(default=None, repr=False)
    special_reservation_code: str | None = field(default=None, repr=False)
    free_seat_reservation_code: str | None = field(
        default=None,
        repr=False,
    )
    standing_reservation_code: str | None = field(default=None, repr=False)
    seat_map_flag: str | None = field(default=None, repr=False)
    delay_sale_flag: str | None = field(default=None, repr=False)
    wait_reservation_flag: str | None = field(default=None, repr=False)
    reservation_possible_name: str | None = field(default=None, repr=False)
    special_reservation_possible_name: str | None = field(
        default=None,
        repr=False,
    )
    info_text: str | None = field(default=None, repr=False)
    popup_message: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassScheduleTrain:
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    detour_code: str | None = field(default=None, repr=False)
    schedule_price: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassAgeOption:
    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    trains: tuple[PassScheduleTrain, ...] = field(
        default=(),
        repr=False,
    )
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    merge_reservation_possible_flag: str | None = None
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class IntermediateStation:
    code: str | None = field(default=None, repr=False)
    name: str | None = field(default=None, repr=False)
    run_order: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassPeriodOption:
    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    merge_reservation_possible_flag: str | None = None
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class PassMenuData:
    commuter_kind_code: str | None = None
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    h_cnd_flg_disc_no: str | None = field(default=None, repr=False)
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassMenuItem:
    after_day: int | None = None
    agreement: str | None = None
    detail_type: str | None = None
    detail_description: str | None = None
    enabled: str | None = None
    item_id: str | None = None
    information: str | None = None
    expanded: str | None = None
    parent_id: str | None = None
    representative_arrival: str | None = None
    representative_departure: str | None = None
    title: str | None = None
    train_group_code: str | None = None
    item_type: str | None = None
    goods_data: PassGoodsInfo | None = None
    pass_data: PassMenuData | None = None
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PassMenuResponse(BaseKorailResponse):
    items: tuple[PassMenuItem, ...] = ()


@dataclass(frozen=True)
class CommuterKindMenuResponse(BaseKorailResponse):
    after_day: str | None = None
    agreement: str | None = None
    information: str | None = None
    title: str | None = None
    pass_data: PassMenuData | None = None


@dataclass(frozen=True)
class CrewRequestOption:
    message_code: str | None = None
    content: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    items: tuple[CrewRequestOption, ...] = ()


@dataclass(frozen=True)
class PassScheduleResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    schedules: tuple[PassScheduleInfo, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class DiscountCardSection:
    """할인카드가 등록된 구간 하나.

    ``TicketDetailDao.AppSegInfo``
    (``dao/refund/TicketDetailDao.java:25-64``). N카드는 이런 구간 1~3 개에
    대해 팔리고, 그 구간을 지나는 열차에만 쓸 수 있다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_schedule`
    가 역코드가 아니라 역 **이름** 을 받는 것도 그것이 여기서 나오기
    때문이다.
    """

    #: ``dcntCrdAplSegSqno`` — 카드 안에서 이 구간의 순번.
    section_sequence: str | None = None
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    journey_sequence: str | None = field(default=None, repr=False)
    journey_type_code: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    #: ``stlbDturDvNm`` — 경유 이름. 앱이 좌석지정 시각표 요청에 그대로
    #: 넘긴다(``u4/b.java:104``).
    detour_division_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세가 설명하는 할인카드.

    ``TicketDetailDao.DiscountCardInfo``
    (``dao/refund/TicketDetailDao.java:123-142``)이며
    ``TicketDetailResponse.dcnt_crd_info`` 로 온다(``:233``). 읽고 있는
    "승차권"이 실은 카드일 때만 있다 — 보통 승차권에는 이 객체가 없다.

    :attr:`card_no` 를 얻으려고 있는 모델이다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_usage_history`
    의 유일한 입력이고, 할인코드 ``"153"`` 과 함께 평범한 예약을 할인 예약으로
    바꾸는 유일한 입력이기도 하다(``w4/a.java:100-101``). 미리보기와 로그에서
    마스킹된다.
    """

    #: ``h_dcnt_crd_no``.
    card_no: str | None = field(default=None, repr=False)
    #: ``h_dcnt_crd_trm_extn_psb_flg`` — 기간연장이 가능하면 ``"Y"``.
    #: 앱에서 "기간연장" 버튼을 켜는 것도 이 값 하나다
    #: (``Y4/C0907b.java:301`` → ``Y4/Q.java:1013-1026``).
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """``xPoint.MyXPointView`` — 마이페이지의 포인트·자격 요약.

    ``KorailPointInquiryDao.KorailPointInquiryResponse``
    (``dao/xPoint/KorailPointInquiryDao.java:11-85``). 앱은 마이페이지를 열
    때(``MyPageActivity.java:414``)와 회원카드 화면에서
    (``MemberCardActivity.java:67``) 무조건 부른다.

    **"이 계정이 어떤 할인 자격을 갖고 있는가"에 KORAIL 이 내놓는 것 중 가장
    가까운 답이다.** ``MyPageActivity.java:206-212`` 는 장애 관련 영역 전체를
    ``h_hdcp_flg == "Y"`` 일 때만, 그리고 그것만 보고 드러낸 뒤,
    :attr:`welfare_discount_class_name`(장애인증 라벨)과
    :attr:`customer_lead_flag_name`(보조견 라벨) 두 줄을 채운다.

    그러므로 ``h_hdcp_flg`` 가 ``"Y"`` 가 아닌 계정에는 장애인 등록도 보조견
    등록도 없다. 폼이 앱과 정확히 같았는데도 1~3급 장애 + 안내견 예약이
    ``ERR299943`` "예약할인이 지원되지 않습니다"로 거절된 것을 설명할 수 있는
    조건이다 — 다만 이것은 앱이 이 플래그로 **무엇을 하는지** 에서 끌어낸
    추론이지, 이 플래그와 그 거절이 함께 관측된 것은 아니다.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``h_korail_point`` — 마이페이지에 뜨는 코레일 포인트 잔액.
    korail_point: str | None = None
    #: ``h_disc_coup_cnt`` — 계정이 가진 할인쿠폰 개수.
    #: :meth:`~korail_mobile_api.client.KorailClient.get_discount_coupons` 가
    #: 실제로 돌려주는 목록의 개수다.
    discount_coupon_count: str | None = None
    #: ``h_delay_cnt`` — 계정이 가진 지연할인권 개수.
    delay_discount_count: str | None = None
    #: ``h_hdcp_flg`` — 장애인 등록이 있으면 ``"Y"``.
    disability_flag: str | None = field(default=None, repr=False)
    #: ``h_subt_dcs_cl_nm`` / ``h_subt_dcs_cl_cd`` — 그 등록이 주는 우대할인
    #: 등급. 앱에서 장애인증 라벨 아래 찍힌다.
    welfare_discount_class_name: str | None = field(default=None, repr=False)
    welfare_discount_class_code: str | None = field(default=None, repr=False)
    #: ``h_cust_lead_flg_nm`` — 앱에서 보조견 라벨 아래 찍힌다.
    customer_lead_flag_name: str | None = field(default=None, repr=False)
    #: ``h_cp_athn_flg`` / ``h_emil_athn_flg`` — 휴대폰·이메일 인증 여부.
    phone_verified_flag: str | None = field(default=None, repr=False)
    email_verified_flag: str | None = field(default=None, repr=False)
    contact_channel_content: str | None = field(default=None, repr=False)
    #: ``h_logn_tp_cd1``/``2``/``4``/``5`` — 네이버·카카오·구글·애플 소셜
    #: 로그인 연동. ``MyPageActivity.java:214-236`` 이 읽는 순서 그대로다.
    naver_linked_flag: str | None = field(default=None, repr=False)
    kakao_linked_flag: str | None = field(default=None, repr=False)
    google_linked_flag: str | None = field(default=None, repr=False)
    apple_linked_flag: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class MileageHistoryEntry:
    """마일리지 내역의 적립 또는 사용 한 줄.

    ``MileageInquiryDao.SpecList``
    (``dao/xPoint/MileageInquiryDao.java:128-167``).
    """

    #: ``dptDt`` — 이 줄이 귀속된 출발일.
    departure_date: str | None = None
    #: ``pontDvNm`` — 적립/사용 구분 이름.
    point_division_name: str | None = None
    #: ``mlgAcmDvCdNm`` — 어떤 방식으로 적립됐는지.
    accrual_division_name: str | None = None
    #: ``rcpDvNm`` — 수납 구분 이름.
    receipt_division_name: str | None = None
    #: ``pontAmt`` — 이 줄의 포인트 증감. 부호가 붙는다.
    point_amount: str | None = None
    #: ``savePontValNum`` — 이 줄 시점의 누적 잔액.
    saved_point_value: str | None = field(default=None, repr=False)
    #: ``stlAmt`` — 이 줄이 나온 정산 운임.
    settlement_amount: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """``mlg.amtSpec.do`` — 마일리지 적립/사용 내역 한 페이지.

    ``MileageInquiryDao.MileageInquiryResponse``
    (``dao/xPoint/MileageInquiryDao.java:72-126``).

    앱의 합계 줄은 :attr:`total_available_rail_point` 와
    :attr:`total_available_rail_point_1` 을 KTX 마일리지와 삼성카드
    마일리지로 각각 찍고 더한다(``MileageHistoryActivity.java:574-578``).
    그래서 하나로 합치지 않고 둘 다 내놓는다.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``pgCnt`` — 전체 페이지 수. 앱은 무한 스크롤의 상한으로 쓴다
    #: (``MileageHistoryActivity.java:581``).
    page_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = field(
        default=None,
        repr=False,
    )
    total_used_rail_point_1: str | None = field(default=None, repr=False)
    rail_now_saved_point_1: str | None = field(default=None, repr=False)
    #: ``delPontValNum`` — 이번 달에 소멸하는 포인트.
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = field(default=None, repr=False)
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class DiscountCardUsage:
    """할인카드(N카드)를 이미 쓴 여행 한 건.

    ``NCardHistoryDao.NCardHistoryInfo``
    (``dao/research/NCardHistoryDao.java:12-61``). 앱은 정확히 이 다섯 필드로
    번호 매긴 목록을 그린다 — 승객 이름,
    :attr:`additional_user_flag` 가 ``"Y"`` 면 "(추가사용자)", 출발 → 도착,
    그리고 ``yyyy.MM.dd`` 로 다시 쓴 운행일
    (``TicketNCardHistoryActivity.java:84-97``).
    """

    #: ``custNm`` — 이 구간을 실제로 탄 사람의 이름.
    passenger_name: str | None = field(default=None, repr=False)
    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: ``runDt1``, ``yyyyMMdd``.
    run_date: str | None = None
    #: ``apdUsrFlg`` — 카드 소유자가 아니라 **두 번째** 등록 사용자가 탔으면
    #: ``"Y"``(N카드 2인용).
    additional_user_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """``ticket.dcntCrdUseQry.do`` — 카드가 쓰인 여행 목록.

    ``NCardHistoryDao.NCardHistoryResponse``
    (``dao/research/NCardHistoryDao.java:78-87``)가 싣는 것은 ``tkUseList``
    하나뿐이라, 전선에 없는 요약 필드를 이 모델도 만들어 붙이지 않는다.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """할인카드를 아직 쓸 수 있는 열차 하나.

    ``NCardInquiryDao.TrainInfo``
    (``dao/research/NCardInquiryDao.java:144-236``).

    ``stationInfo`` 는 일부러 없다. 그것은 앱이
    :attr:`station_string_info` 로부터 스스로 만들어 내는
    ``android.text.Spanned`` 이지 전선에서 읽는 값이 아니다(``:157``,
    유일한 기록 지점이 ``:229`` 의 ``setStationInfo``).
    """

    train_no: str | None = None
    train_group_code: str | None = None
    run_date: str | None = None
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = None
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = None
    departure_station_order: str | None = field(default=None, repr=False)
    arrival_station_order: str | None = field(default=None, repr=False)
    #: ``cmtrPrc`` — 이 카드의 구간에 매겨진 운임.
    commuter_price: str | None = None
    direct_transfer_division_code: str | None = field(default=None, repr=False)
    detour_code: str | None = field(default=None, repr=False)
    detour_name: str | None = field(default=None, repr=False)
    route_code: str | None = field(default=None, repr=False)
    #: ``stationStringInfo`` — 앱이 서식을 입혀 그리는 중간 정차역 줄.
    station_string_info: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """``research.dcntCrdScheduleView.do`` — 카드로 예약할 수 있는 열차들.

    ``NCardInquiryDao.NCardInquiryResponse``
    (``dao/research/NCardInquiryDao.java:128-142``).

    :attr:`following_page_exists` 가 페이징 신호다. 앱은 그 값이 ``"Y"`` 인
    동안 ``qryPgNo`` 를 하나씩 올려 다시 조회한다
    (``SectionNCardInquiryActivity.java:406-408``).
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``fllwPgExt`` — 다음 페이지가 있으면 ``"Y"``.
    following_page_exists: str | None = None
    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    birth_date: str | None = field(default=None, repr=False)
    customer_family_name: str | None = field(default=None, repr=False)
    discount_kind_code: str | None = field(default=None, repr=False)
    family_sequence: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    passenger_type_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    requested_discount_kind_code: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    targets: tuple[MultiChildDiscountTarget, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class CustomerTripInfo:
    additional_seat_attribute_code: str | None = field(default=None, repr=False)
    adult_disabled_person_count: str | None = field(default=None, repr=False)
    adult_count: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    baby_accompanying_person_count: str | None = field(default=None, repr=False)
    changed_at: str | None = field(default=None, repr=False)
    changed_by: str | None = field(default=None, repr=False)
    child_count: str | None = field(default=None, repr=False)
    child_disabled_person_count: str | None = field(default=None, repr=False)
    customer_management_no: str | None = field(default=None, repr=False)
    day_code: str | None = field(default=None, repr=False)
    direction_seat_attribute_group_code: str | None = field(default=None, repr=False)
    direct_transfer_division_code: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    early_train_departure_time: str | None = field(default=None, repr=False)
    elderly_person_count: str | None = field(default=None, repr=False)
    included_flag: str | None = field(default=None, repr=False)
    job_start_hour: str | None = field(default=None, repr=False)
    location_seat_attribute_group_code: str | None = field(default=None, repr=False)
    media_division_code: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    passenger_total: str | None = field(default=None, repr=False)
    registered_at: str | None = field(default=None, repr=False)
    registration_sequence: str | None = field(default=None, repr=False)
    registered_by: str | None = field(default=None, repr=False)
    trip_day_no: str | None = field(default=None, repr=False)
    train_classification_code: str | None = field(default=None, repr=False)
    train_connection_flag: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    usage_day_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    trips: tuple[CustomerTripInfo, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class MaasServiceDetail:
    additional_service_division_code: str | None = field(default=None, repr=False)
    additional_service_goods_code: str | None = field(default=None, repr=False)
    additional_service_id: str | None = field(default=None, repr=False)
    marketing_entity_id: str | None = field(default=None, repr=False)
    marketing_entity_name: str | None = field(default=None, repr=False)
    additional_service_name: str | None = field(default=None, repr=False)
    progress_status_code: str | None = field(default=None, repr=False)
    request_no: str | None = field(default=None, repr=False)
    passenger_reference_content: str | None = field(default=None, repr=False)
    partner_reservation_no: str | None = field(default=None, repr=False)
    delivery_close_time: str | None = field(default=None, repr=False)
    delivery_start_time: str | None = field(default=None, repr=False)
    lead_message_1: str | None = field(default=None, repr=False)
    lead_message_2: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    request_date: str | None = field(default=None, repr=False)
    request_quantity: str | None = field(default=None, repr=False)
    reservation_specification_url: str | None = field(default=None, repr=False)
    usage_close_date: str | None = field(default=None, repr=False)
    usage_start_date: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    details: tuple[MaasServiceDetail, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    last_run_date: str | None = field(default=None, repr=False)
    trip_change_date: str | None = field(default=None, repr=False)
    trip_change_dates: tuple[str, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class TourTrainSeatAdditionalInfo:
    passenger_count: int = field(repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TourTrainSeatInfo:
    seat_attribute_code: str | None = field(default=None, repr=False)
    additional_infos: tuple[TourTrainSeatAdditionalInfo, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TourTrainInfoResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    seat_infos: tuple[TourTrainSeatInfo, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class GiftTicket:
    integrated_customer_name_1: str | None = field(default=None, repr=False)
    integrated_customer_name_2: str | None = field(default=None, repr=False)
    current_point_value: str | None = field(default=None, repr=False)
    received_date: str | None = field(default=None, repr=False)
    return_amount: str | None = field(default=None, repr=False)
    return_date: str | None = field(default=None, repr=False)
    return_time: str | None = field(default=None, repr=False)
    ticket_id: str | None = field(default=None, repr=False)
    transaction_amount: str | None = field(default=None, repr=False)
    usage_close_date: str | None = field(default=None, repr=False)
    used_point_value: str | None = field(default=None, repr=False)
    usable_flag: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class GiftTicketListResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    tickets: tuple[GiftTicket, ...] = field(default=(), repr=False)
    query_count: str | None = field(default=None, repr=False)
    next_query_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class CommuterPassengerOption:
    commuter_usage_age_code: str | None = field(default=None, repr=False)
    common_code_name: str | None = field(default=None, repr=False)
    passenger_count_from: int = field(default=0, repr=False)
    passenger_count_to: int = field(default=0, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    additional_service_goods_flag: str | None = field(default=None, repr=False)
    companion_flag: str | None = field(default=None, repr=False)
    commuter_kind_code: str | None = field(default=None, repr=False)
    commuter_usage_age_code: str | None = field(default=None, repr=False)
    menu_id: str | None = field(default=None, repr=False)
    popup_message: str | None = field(default=None, repr=False)
    promotion_message: str | None = field(default=None, repr=False)
    promotion_url: str | None = field(default=None, repr=False)
    seat_attribute_code: str | None = field(default=None, repr=False)
    available_passenger_count_from: int = field(default=0, repr=False)
    available_passenger_count_to: int = field(default=0, repr=False)
    passenger_options: tuple[CommuterPassengerOption, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class PriceFare:
    journey_sequence: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price: str | None = field(default=None, repr=False)
    total_amount: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    fares: tuple[PriceFare, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    acceptance_customer_management_no: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    reservation_count: int = field(default=0, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceSeat:
    passenger_type_division_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    car_no: int = field(default=0, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceJourney:
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    journey_type_code: str | None = field(default=None, repr=False)
    member_division_name: str | None = field(default=None, repr=False)
    acceptance_kind_name: str | None = field(default=None, repr=False)
    pbp_reservation_no: str | None = field(default=None, repr=False)
    registered_date: str | None = field(default=None, repr=False)
    withdrawal_possible_flag: str | None = field(default=None, repr=False)
    seats: tuple[PbpAcceptanceSeat, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceTicket:
    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    journeys: tuple[PbpAcceptanceJourney, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    tickets: tuple[PbpAcceptanceTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class PlatformNumberJourney:
    platform_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PlatformNumberTicket:
    sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    ticket_return_no: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    journeys: tuple[PlatformNumberJourney, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class PlatformNumberResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    tickets: tuple[PlatformNumberTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석 변경으로 옮겨 갈 수 있는 승차역 하나.

    ``CallSelfSeatChgInfoDao.ChgStnList``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:157-204``).

    이 줄을 고를 수 있는지는 좌석 수 둘이 정한다 —
    :attr:`general_remaining_seats`(``gnrmRestSeatNum``)와
    :attr:`special_remaining_seats`(``sprmRestSeatNum``)가 이 역에서 시작하는
    구간의 일반실·특실 잔여 좌석이다.
    """

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
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """좌석 변경 사유 한 줄(``CallSelfSeatChgInfoDao.java:136-155``)."""

    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """``self.seatChgInfo.do`` — 자율 좌석·열차 변경이 무엇으로 바뀔 수 있는지.

    ``CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:64-134``).

    :attr:`general_reservation_possible_code` /
    :attr:`special_reservation_possible_code`
    (``gnrmRsvPsbCd``/``sprmRsvPsbCd``)는 객실 등급별 **열차 단위** 가부다.
    역별 잔여 좌석은 :attr:`stations` 쪽에 있다.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    train_no: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    train_group_code: str | None = None
    train_group_name: str | None = None
    run_date: str | None = None
    general_reservation_possible_code: str | None = None
    special_reservation_possible_code: str | None = None
    change_before_departure_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    change_before_arrival_construction_order: str | None = field(
        default=None,
        repr=False,
    )
    existing_departure_run_order: str | None = field(
        default=None,
        repr=False,
    )
    existing_arrival_run_order: str | None = field(
        default=None,
        repr=False,
    )
    stations: tuple[SelfSeatChangeStation, ...] = ()
    reasons: tuple[SelfSeatChangeReason, ...] = ()


@dataclass(frozen=True)
class OriginalTicketSeat:
    """원표의 한 여정에 딸린 좌석 하나(``response/research/Seat.java``).

    좌석 식별자 자체(``scarNo``/``seatNo``)는 미리보기에서 마스킹된다.
    """

    passenger_sequence: str | None = None
    assign_sequence: str | None = None
    passenger_type_code: str | None = None
    room_class_code: str | None = field(default=None, repr=False)
    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    seat_count: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    requested_seat_attribute_code: str | None = None
    direction_seat_attribute_code: str | None = None
    location_seat_attribute_code: str | None = None
    smoking_seat_attribute_code: str | None = None
    additional_seat_attribute_code: str | None = None
    etc_seat_attribute_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """원표의 구간 하나(``response/research/Jrny.java``).

    변경 흐름이 이 줄을 열쇠로 삼는다 — ``jrnySqno`` 와 출발·도착 역코드·
    운행순서가 뒤따르는 조회들이 그대로 요구하는 인자다.
    """

    journey_sequence: str | None = None
    journey_order: str | None = None
    #: ``jrnyTpCd``. 전선 철자와 속성 철자 양쪽이 민감 키로 등록돼 있어, 이
    #: 값을 드러내는 다른 모델과 마찬가지로 표현에서 뺀다.
    journey_type_code: str | None = field(default=None, repr=False)
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
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class OriginalTicket:
    """원표 하나(``response/research/OrgTk.java``).

    ``original_*`` 네 값은 승차권 자신의 반환번호가 되돌아온 것이다 — 요청이
    보낸 것과 같은 비밀이라 전선 철자와 속성 철자 양쪽에서 마스킹된다.

    ``cmpnList``(동반 할인)와 ``stlList``(정산 줄)는 일부러 :attr:`raw` 에만
    남긴다. 지연증명 반환번호, 카드번호, 승인번호 같은 자격증명이 더 들어
    있는데 변경 흐름에는 쓸 일이 없기 때문이다. 그 전선 키들도
    :mod:`korail_mobile_api.redaction` 에 등록돼 있어 ``raw`` 안에서 마스킹된
    채로 있다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    original_sale_datetime: str | None = field(default=None, repr=False)
    original_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    adult_count: str | None = None
    child_count: str | None = None
    group_discount_count: str | None = None
    passenger_type_division_code: str | None = None
    received_amount: str | None = None
    received_fare: str | None = None
    received_price: str | None = None
    change_sale_transaction_no: str | None = field(default=None, repr=False)
    sms_send_flag: str | None = None
    forced_sale_reason_text: str | None = None
    journeys: tuple[OriginalTicketJourney, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """``research.tripChgOgtk.do`` — 변경이 출발점으로 삼을 원표들.

    ``OgTkInquiryDao.OgTkInquiryResponse``
    (``dao/research/OgTkInquiryDao.java:38-46``).
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    tickets: tuple[OriginalTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class RecentDeliveryRecipient:
    acceptance_customer_management_flag: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_management_no: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    acceptance_customer_phone_2: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    recipients: tuple[RecentDeliveryRecipient, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class ProductRecommendation:
    discount_amount: str | None = field(default=None, repr=False)
    discount_surcharge_rate: str | None = field(default=None, repr=False)
    fare_amount_percent_division_code: str | None = field(default=None, repr=False)
    goods_name: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price: str | None = field(default=None, repr=False)
    received_price_2: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ProductTrain:
    detour_via_popup: str | None = field(default=None, repr=False)
    elevator_damage_control: str | None = field(default=None, repr=False)
    arrival_date: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    arrival_station_construction_order: str | None = field(default=None, repr=False)
    arrival_station_run_order: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    car_type_name: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = field(default=None, repr=False)
    change_train_sequence: str | None = field(default=None, repr=False)
    connection_traffic_need_time: str | None = field(default=None, repr=False)
    connection_traffic_possible_flag: str | None = field(default=None, repr=False)
    connection_traffic_received_price: str | None = field(default=None, repr=False)
    delayed_sale_flag: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    departure_station_construction_order: str | None = field(default=None, repr=False)
    departure_station_run_order: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    detour_flag: str | None = field(default=None, repr=False)
    detour_text: str | None = field(default=None, repr=False)
    expected_delay_hour: str | None = field(default=None, repr=False)
    expected_departure_delay_count: str | None = field(default=None, repr=False)
    free_reservation_code: str | None = field(default=None, repr=False)
    free_seat_car_count: str | None = field(default=None, repr=False)
    general_room_class_name: str | None = field(default=None, repr=False)
    general_reservation_code: str | None = field(default=None, repr=False)
    general_reservation_code_2: str | None = field(default=None, repr=False)
    information_text: str | None = field(default=None, repr=False)
    journey_reservation_code: str | None = field(default=None, repr=False)
    journey_reservation_name: str | None = field(default=None, repr=False)
    nonstop_message: str | None = field(default=None, repr=False)
    nonstop_message_text: str | None = field(default=None, repr=False)
    popup_message: str | None = field(default=None, repr=False)
    received_amount: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price_2: str | None = field(default=None, repr=False)
    road_seat_map_flag: str | None = field(default=None, repr=False)
    reservation_possible_name: str | None = field(default=None, repr=False)
    run_date: str | None = field(default=None, repr=False)
    run_time: str | None = field(default=None, repr=False)
    seat_attribute_code: str | None = field(default=None, repr=False)
    simultaneous_train_flag: str | None = field(default=None, repr=False)
    special_discount_rate: str | None = field(default=None, repr=False)
    special_room_class_name: str | None = field(default=None, repr=False)
    special_reservation_code: str | None = field(default=None, repr=False)
    special_reservation_code_2: str | None = field(default=None, repr=False)
    special_reservation_possible_name: str | None = field(default=None, repr=False)
    station_popup_message: str | None = field(default=None, repr=False)
    standing_reservation_code: str | None = field(default=None, repr=False)
    train_discount_general_rate: str | None = field(default=None, repr=False)
    train_discount_origin_rate: str | None = field(default=None, repr=False)
    train_classification_code: str | None = field(default=None, repr=False)
    train_classification_name: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    use_time_care_article_content: str | None = field(default=None, repr=False)
    waiting_reservation_flag: str | None = field(default=None, repr=False)
    youth_mileage_application_flag: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    total_passenger_count: int = field(default=0, repr=False)
    recommendations: tuple[ProductRecommendation, ...] = field(
        default=(),
        repr=False,
    )
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ProductTrainInquiryResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    early_train_no_next: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = field(default=None, repr=False)
    notice_message: str | None = field(default=None, repr=False)
    preceding_train_no_next: str | None = field(default=None, repr=False)
    next_query_station_no: str | None = field(default=None, repr=False)
    result_count: str | None = field(default=None, repr=False)
    next_train_no: str | None = field(default=None, repr=False)
    merge_reservation_possible_flag: str | None = field(default=None, repr=False)
    trains: tuple[ProductTrain, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class ReservationSeatDetail:
    """보류된 예약의 좌석 한 줄(``seat_infos.seat_info[]``).

    필드 이름은 ``ReservationResponse.SeatInfo``
    (``response/certification/ReservationResponse.java:296-313``)를 따른다.

    :attr:`passenger_type_code` 는 ``h_psg_tp_cd`` 다. 앱은 이 줄의 승객
    종류를 **코드** 로 선언하고, 디컴파일된 앱 어디에도
    ``h_psg_tp_dv_nm`` 이 없다. 그래서 일부 서드파티 클라이언트가 이름 붙인
    표시명 변형은 모델링하지 않았다. 서버가 그것을 보낸다면 :attr:`raw` 로
    닿을 수 있다.

    운임 재계산 요청의
    :class:`~korail_mobile_api.mutation_models.PriceRecalculationRow` 는 이
    줄에서 앞의 세 값을 그대로 베낀다.
    """

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — 이 좌석에 실제로 걷히는 금액. 예약 응답에
    #: ``h_tot_rcvd_amt`` 가 없을 때 결제 경로가 ``hidMnsStlAmt1`` 을 이 값들의
    #: 합으로 구하므로, 정산 금액을 다른 출처로 대조해 볼 수 있다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ReservationDetailJourney:
    """보류된 예약의 여정 하나(``jrny_infos.jrny_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = field(default=None, repr=False)
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR 로 다시 읽은 보류 예약(``certification.ReservationList``).

    응답 타입이 예약 요청이 돌려주는 것과 같은 ``ReservationResponse`` 다.
    그래서 이 조회는 이 패키지가 이미 만들 수 있는 예약을 **다른 출처로**
    다시 보는 셈이다 — 창구번호(``h_wct_no``)와 결제 폼이 정산할 좌석별
    금액을 여기서 확인할 수 있다.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 정산 합계. 결제 폼의 ``hidMnsStlAmt1`` 을 예약
    #: 응답이 아닌 출처로 대조할 수 있다.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """원표 하나의 환불 수수료와 환불액.

    필드는 ``RefundCommissionDao.RefundCommissionResponse``
    (``dao/refund/RefundCommissionDao.java:70-77``)를 따른다.

    "얼마가 돌아오고 수수료는 얼마인가"를 미리 보는 조회다. 실제 환불을
    보내기 전에 먼저 불러라.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``ret_amt`` — 돌려받을 금액.
    refund_amount: str | None = None
    #: ``ret_fee`` — 거기서 떼는 수수료.
    refund_fee: str | None = None
    #: ``prg_psb_flg`` — 환불을 진행할 수 있는지.
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — 이 경로가 봉투의 것과 별개로 싣는
    #: **두 번째** 메시지 짝. 성공한 사전 조회에 수수료 정책 안내가 붙는 식이다.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 하나(``tk_seat_info[]``)."""

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    buyer_name: str | None = field(default=None, repr=False)
    checkin_status_code: str | None = field(default=None, repr=False)
    discount_kind_code: str | None = field(default=None, repr=False)
    discount_kind_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    passenger_type_name: str | None = field(default=None, repr=False)
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """환불 대상 승차권의 여정 하나(``ticket_infos.ticket_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_date: str | None = None
    arrival_time: str | None = None
    arrival_station_name: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_class_name: str | None = None
    room_class_name: str | None = field(default=None, repr=False)
    platform_no: str | None = field(default=None, repr=False)
    seats: tuple[RefundTicketSeat, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 상세(``refunds.SelTicketInfo``).

    필드는 ``TicketDetailDao.TicketDetailResponse``
    (``dao/refund/TicketDetailDao.java:227-281``)를 따른다.

    두 조회가 사슬로 이어진다. 앱은 :attr:`companion_name` 과
    :attr:`companion_birth_date` 를 뒤따르는 ``CommissionView`` 호출에
    ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 넘긴다
    (``TicketListActivity.java:908-909``).

    환불 신원을 손으로 조립하지 말고
    :meth:`~korail_mobile_api.mutation_models.PaidTicket.from_refund_detail`
    에 이 응답을 넘겨라.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_time: str | None = field(default=None, repr=False)
    window_name: str | None = field(default=None, repr=False)
    original_sale_date: str | None = field(default=None, repr=False)
    original_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = field(default=None, repr=False)
    ticket_kind_name: str | None = None
    #: ``retPsbFlg`` — 이 승차권이 환불 가능한지. 환불 전에 볼 수 있는 가장
    #: 싼 사전 점검이다.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    #: ``h_compa_nm``/``h_compa_brth`` — CommissionView 요청에
    #: ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 복사돼 나간다.
    companion_name: str | None = field(default=None, repr=False)
    companion_birth_date: str | None = field(default=None, repr=False)
    #: ``h_pbp_acep_tgt_flg`` — 이 승차권이 PBP 인수 대상인지. 앱은 이 값을
    #: 환불 요청의 ``pbpAcepTgtFlg`` 로 그대로 되돌려 보낸다
    #: (``ticketReturn/a.java:430-431``). 환불 폼을 만들 때 이 값을 넘겨야
    #: 기본값 ``"N"`` 이 아니라 서버가 말한 것을 되말한다.
    pbp_acceptance_target_flag: str | None = None
    #: ``h_dlay_flg``/``h_dlay_tk_flg`` — 지연 보상 대상 여부.
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    #: ``mlgSaveFlg`` — 환불하면 마일리지가 복구되는지.
    mileage_save_flag: str | None = None
    #: ``addSrvFlg``/``addSrvCancel`` — 딸린 부가서비스가 있는지, 환불이 그것도
    #: 함께 취소하는지.
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: ``dcnt_crd_info`` — 이 "승차권"이 실은 할인카드(N카드)일 때만 있다.
    #: 보통 승차권에서는 ``None``.
    discount_card: DiscountCardOnTicket | None = None
