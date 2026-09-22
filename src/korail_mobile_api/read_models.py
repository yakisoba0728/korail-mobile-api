# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 전용 조회 응답 타입 — 승차권, 환불, 할인카드, 마이페이지.

열차 검색·좌석 조회 타입은 :mod:`korail_mobile_api.models`.
전부 ``frozen=True`` 데이터클래스이며 ``raw`` 에 원본 JSON 보존.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


@dataclass(frozen=True)
class TicketListTicket:
    pnr_no: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    return_sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    ticket_status_code: str | None = None
    #: ``h_tk_knd_cd``/``h_tk_knd_nm`` — 승차권 종류(``'72'``/``'스마트티켓'``).
    #: 예약 행이 아니라 승차권 행에 실려 옵니다(라이브 131/131행).
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    train_info: tuple[Mapping[str, Any], ...] = field(default=(), repr=False, compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketListReservation:
    """``MyTicketListOutReservation.java`` — ``ticket_list`` 만 ``@SerialName``
    이 있고 나머지 15개 멤버는 없습니다(PROTECTED, 코틀린 필드명이 최선).
    그중 ``addSrvInfo``(부가서비스, ``AddSrvItem`` 객체)와
    ``ticketKind``(``TicketDefine.TicketKind`` 열거형)는 중첩 타입이 더
    필요해 아직 스칼라만 모델링했습니다 — 둘 다 :attr:`raw` 로 계속 닿을 수
    있습니다.
    """

    tickets: tuple[TicketListTicket, ...] = ()
    #: 아래 스칼라들은 모두 ``@SerialName`` 이 없어 코틀린 필드명을 추측한
    #: 것이고, 실서버 예약 행에는 ``ticket_list`` **하나만** 옵니다
    #: (2026-09-22: ``mode="2"`` 예약 128행 전부, 다른 키 0개). 따라서 지금은
    #: 전부 ``None`` 입니다. 불리언들이 ``False`` 가 아니라 ``None`` 인 이유가
    #: 이것입니다 — 서버가 "거짓" 이라고 말한 것이 아니라 아무 말도 하지
    #: 않았습니다. 승차권 종류는 예약이 아니라 **승차권** 행에 있습니다
    #: (:attr:`TicketListTicket.ticket_kind_code`, ``h_tk_knd_cd``, 라이브
    #: 131/131행).
    departure_datetime: str | None = field(default=None, repr=False)
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketListResponse(BaseKorailResponse):
    reservations: tuple[TicketListReservation, ...] = ()
    #: ``h_total_cnt`` — 구매이력(``mode="2"``)의 서버측 총건수. 0 을 채운
    #: 문자열로 오므로(``'0128'``) 문자열로 둡니다. ``mode="1"`` 과 빈
    #: 응답에는 이 키가 없어 ``None`` 입니다.
    total_count: str | None = None


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
    #: ``h_tk_cnt`` — ``CartInfo.java:51`` 의 선언은 ``String`` 입니다. 예전에는
    #: int 로 강제 변환해 읽었습니다(6.5.0 Gson 전제를 잘못 적용한 것 —
    #: 이 DTO 는 kotlinx 입니다).
    ticket_count: str | None = None
    usage_start_date: str | None = None
    usage_start_time: str | None = None
    usage_close_time: str | None = None
    partner_reservation_no: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    lump_sum_target_no: str | None = field(default=None, repr=False)
    customer_no: str | None = field(default=None, repr=False)
    virtual_reservation_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)

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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DepositBankListResponse(BaseKorailResponse):
    items: tuple[DepositBank, ...] = ()


@dataclass(frozen=True)
class DelayDiscountTicket:
    """지연배상 쿠폰 한 장(``DelayCoupon.java:32-55``, 23개 String 필드).

    ``h_use_psb_dt``(사용 가능 기한)는 전 디컴파일에 0건이라 더 이상 읽지
    않습니다 — 예전에는 이 자리를 채우던 팬텀 키였습니다.
    """

    fare: str | None = None
    original_sale_date: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    #: ``h_tk_sqno`` — 이 줄이 어느 실물 승차권에 붙었는지를 가리키는 신원 앵커.
    ticket_sequence: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    #: ``h_orgtk_sale_dt`` — 원표 자체의 발매일. ``original_sale_date``
    #: (``h_orgtk_ret_sale_dt``, 반환일)와는 다른 필드입니다.
    original_ticket_sale_date: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — ``fare``(``h_dlay_fare``)와 별개인 수령 금액.
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
    #: ``h_buy_ps_nm``/``h_abrd_ps_nm`` — 구매자·탑승자 성명. 둘 다 개인정보.
    buyer_name: str | None = field(default=None, repr=False)
    passenger_name: str | None = field(default=None, repr=False)
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DelayDiscountTicketListResponse(BaseKorailResponse):
    items: tuple[DelayDiscountTicket, ...] = ()


@dataclass(frozen=True)
class DiscountCoupon:
    guide: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None
    discount_kind_code: str | None = None
    discount_values: tuple[str, ...] = ()
    remarks: tuple[str, ...] = ()
    coupon_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCouponListResponse(BaseKorailResponse):
    items: tuple[DiscountCoupon, ...] = ()
    current_page: int | None = None
    total_pages: int | None = None
    total_count: str | None = None
    row_count: str | None = None


@dataclass(frozen=True)
class PassOffice:
    code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TripMenuItem:
    title: str | None = None
    detail: str | None = None
    menu_type: str | None = None
    button: str | None = None
    contents: tuple[TripMenuContent, ...] = ()
    url: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    detail_raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReceiptPayment:
    payment_method: str | None = None
    #: ``h_apv_dt``. 형제 필드(계좌·승인·카드·포인트 번호)는 전부 보호되는데
    #: 이 필드만 빠져 있었습니다.
    approval_date: str | None = field(default=None, repr=False)
    installment_months: int | None = None
    amount: int | None = None
    account_no: str | None = field(default=None, repr=False)
    approval_no: str | None = field(default=None, repr=False)
    card_no: str | None = field(default=None, repr=False)
    point_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReceiptCashPayment:
    """현금영수증 줄 (``ReceiptDao.java:12-40,43-44``)."""

    #: ``h_apv_mtd_nm`` — 사람이 읽는 승인방법 라벨. 형제 필드(인증도메인
    #: 인식번호·현금영수증 승인번호)는 보호되는데 이 필드만 빠져 있었습니다.
    approval_method_name: str | None = field(default=None, repr=False)
    authentication_domain_recognition_no: str | None = field(
        default=None, repr=False
    )
    cash_receipt_approval_no: str | None = field(default=None, repr=False)
    cash_receipt_transaction_division_code: str | None = None
    total_approved_amount: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketReceipt:
    travel_date: str | None = None
    departure_station: str | None = None
    departure_time: str | None = None
    arrival_station: str | None = None
    arrival_time: str | None = None
    commuter_kind_code: str | None = None
    journey_type_code: str | None = None
    #: ``h_prt_disc_knd_nm``/``h_prt_disc_knd_cd`` — 영수증에 인쇄된 할인
    #: 종류의 이름·코드. ``ReceiptInfo.java`` 의 19개 String 중 셋(이 코드
    #: 포함)이 빠져 있었습니다.
    printed_discount_name: str | None = None
    printed_discount_kind_code: str | None = None
    print_type: str | None = None
    seat_class_name: str | None = None
    ticket_kind_code: str | None = None
    #: ``h_tk_knd_nm`` — 승차권 종류의 사람이 읽는 이름.
    ticket_kind_name: str | None = None
    ticket_status_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    #: ``h_trn_gp_cd`` — 열차 그룹 코드(KTX/새마을 등).
    train_group_code: str | None = None
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
    #: ``cash_rcet_info`` — 현금영수증 줄들.
    cash_receipts: tuple[ReceiptCashPayment, ...] = ()
    member_card_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    #: ``h_rsv_amt`` — 이 열차 행의 유일한 금액 필드
    #: (``ReservationViewOutTrainInfo.java:496``).
    reserved_amount: str | None = None
    seat_count: int | None = None
    standing_count: int | None = None
    pnr_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryTicket:
    """예약 이력 여정의 ``ReservationOut.tkList`` 행 하나(``ReservationOutTK.java``).

    할인(``dcntList``)·동반가족(``fmlyList``)·정산(``stlList``) 하위 목록은
    일부러 :attr:`raw` 에만 남깁니다 — :class:`OriginalTicket` 이 같은 이유로
    ``cmpnList``/``stlList`` 를 raw 전용으로 두는 것과 같은 판단입니다.
    """

    sale_date: str | None = None
    sale_window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    movie_ticket_flag: str | None = None
    delay_discount_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryOriginalTicket:
    """예약 이력 여정의 ``ReservationOut.orgTkList`` 행 하나(``ReservationOrgTk.java``)."""

    sale_date: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    #: ``ogtkRetPwd`` — 원표 반환 비밀번호. 그 자체로 반환 권한이라 민감합니다.
    return_password: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryPassenger:
    """예약 이력 여정의 ``ReservationOut.psgInfos.psgInfo`` 행 하나(``ReservationOutPsgInfo.java``)."""

    passenger_type_code: str | None = None
    passenger_count_per_info: str | None = None
    discount_kind_code: str | None = None
    discount_kind_code_2: str | None = None
    discount_no: str | None = field(default=None, repr=False)
    discount_no_2: str | None = field(default=None, repr=False)
    delay_original_window_no: str | None = field(default=None, repr=False)
    delay_original_sale_date: str | None = field(default=None, repr=False)
    delay_original_sale_sequence: str | None = field(default=None, repr=False)
    #: ``dlayOgtkRetPwd`` — 지연배상 원표의 반환 비밀번호.
    delay_original_return_password: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryReservation:
    """예약 이력 여정에 매달린 ``ReservationOut`` — 실제 PNR·운임·결제 층.

    7.0.6 이 이 층 전체를 여정 옆에 익명 중첩으로 선언합니다
    (``ReservationViewOutJrnyInfo.java:55`` 의 다섯 번째 생성자 인자). 이전에는
    예약 이력 파서가 여정·열차 층만 읽고 이 층 전체를 건너뛰어, PNR 의 실제
    운임·결제·발권 내용이 타입 API 어디에도 없었습니다.

    이 중첩 자체의 정확한 와이어 철자는 ``@SerialName`` 이 없어 PROTECTED 입니다
    — 코틀린 필드명 ``reservationOut`` 을 최선으로 사용합니다
    (``ReservationViewOutJrnyInfo.java`` 의 ``getReservationOut$annotations()``
    부재).
    """

    #: ``h_pnr_no``.
    pnr_no: str | None = field(default=None, repr=False)
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 이 PNR 의 실제 결제(정산) 금액.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    tickets: tuple[ReservationHistoryTicket, ...] = ()
    original_tickets: tuple[ReservationHistoryOriginalTicket, ...] = ()
    passengers: tuple[ReservationHistoryPassenger, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryJourney:
    """예약 이력의 여정 하나(``ReservationViewOutJrnyInfo.java``).

    ``srv_infos``/``acmp_infos`` 는 아직 행 단위로 모델링하지 않고 원본 그대로
    노출합니다 — 이전에는 이 층 자체가 최상위 ``raw`` 블롭에만 남아 타입
    응답 어디로도 들어오지 못했으므로, 원본 그대로라도 여정 단위로 닿을 수
    있게 하는 것이 이번 수정의 목적입니다.
    """

    trains: tuple[ReservationHistoryTrain, ...] = ()
    service_infos: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    accompanying_infos: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    reservation: ReservationHistoryReservation | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationHistoryResponse(BaseKorailResponse):
    """``ReservationViewOut`` — 예약 이력(``research.reservationView.do``).

    최상위 신원 필드(``h_rsv_ps_nm``/``h_tel_no`` 등)와 :attr:`journeys` 는
    이전에는 전혀 파싱되지 않고 최상위 ``raw`` 안에만 있었습니다
    (``ReservationViewOut.java:64``).
    """

    #: ``h_rsv_ps_nm`` — 예약자 성명.
    reservation_passenger_name: str | None = field(default=None, repr=False)
    #: ``h_tel_no`` — 예약자 전화번호.
    phone_no: str | None = field(default=None, repr=False)
    reservation_limit_flag: str | None = None
    seatmap_flag: str | None = None
    process_flag: str | None = None
    follow_flag: str | None = None
    #: ``h_cust_no`` — 고객관리번호. 신원 식별자라 민감.
    customer_no: str | None = field(default=None, repr=False)
    customer_division_code: str | None = None
    customer_sort_code: str | None = None
    customer_class_code: str | None = None
    journey_count: str | None = None
    #: ``guide_infos.guide_info`` — 단일 안내 문구.
    guide_info: str | None = None
    journeys: tuple[ReservationHistoryJourney, ...] = ()
    #: 모든 여정의 열차 행을 평탄화한 목록입니다. 개별 여정의 돈·PNR 층에
    #: 닿으려면 :attr:`journeys` 를 쓰십시오.
    items: tuple[ReservationHistoryTrain, ...] = ()

    @property
    def trains(self) -> tuple[ReservationHistoryTrain, ...]:
        return self.items


@dataclass(frozen=True)
class FreeSeatCarResponse(BaseKorailResponse):
    title: str | None = None
    car_no: str | None = field(default=None, repr=False)
    content: str | None = None


@dataclass(frozen=True)
class GuideSeatConditionResponse(BaseKorailResponse):
    """``reservation.guideSeatCnd.do`` 의 응답.

    ``FAIL``/``MRR800011``(도우미 좌석 안내)도 예외가 아니라 이 응답으로 옵니다.
    안내 문구는 ``h_msg_txt`` 에 있습니다.

    ``GuideSeatCndOut`` 이 선언하는 자체 필드는 :attr:`time_stamp`
    (``long timeStamp``, ``:29``) 하나뿐입니다 — 그래서 이전에는 봉투 밖으로
    아무것도 읽지 않았습니다. ``@SerialName`` 이 없어 정확한 와이어 철자는
    PROTECTED 이며, 코틀린 필드명 ``timeStamp`` 를 최선으로 사용합니다.
    """

    time_stamp: int | None = None


@dataclass(frozen=True)
class TrainScheduleItem:
    """열차 행 하나 — ``assignScheduleView.do``(``TrainScheduleOutTrainInfo``)와
    ``mergeSeatsC.do``(``MergeSeatsCOutTrnInfo``) 두 라우트가 공유합니다.

    두 DTO 는 서로 다른데(``TrainScheduleOutTrainInfo`` 는 100여 필드,
    ``MergeSeatsCOutTrnInfo`` 는 30필드) 실제 필드 이름의 상당수가
    (``train_no``/``run_date``/``departure_*``/``arrival_*``/
    ``*_reservation_code`` 등) 의미상 겹칩니다. 완전히 별개 데이터클래스로
    쪼개는 대신, 각 라우트 전용 필드 맵(``_MERGE_SEATS_TRAIN_FIELDS``와
    ``_TRAIN_SCHEDULE_OUT_TRAIN_FIELDS``, ``read_parsers.py``)으로 각 DTO 의
    실제 와이어 키만 채우도록 나누고, 이 데이터클래스는 두 DTO 의 필드를
    합친 상위집합으로 유지합니다 — 한쪽 라우트에서 안 쓰는 필드는 그냥
    ``None`` 입니다. 필드 맵을 하나로 재사용하던 이전 버그(서로의 DTO 에
    없는 키를 읽고, 있는 키는 빠뜨림)의 근본 원인이 바로 이 공유였습니다.
    """

    train_no: str | None = None
    #: ``h_trn_no_qb`` — 병합예약 조회 전용 열차번호(``MergeSeatsCOutTrnInfo``).
    train_no_qb: str | None = field(default=None, repr=False)
    #: ``h_trn_seq`` — 열차 순번(``MergeSeatsCOutTrnInfo``).
    train_sequence: str | None = field(default=None, repr=False)
    train_group_code: str | None = None
    train_class_code: str | None = None
    train_class_name: str | None = None
    run_date: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    #: ``h_dpt_tm_qb``(``MergeSeatsCOutTrnInfo``).
    departure_time_qb: str | None = field(default=None, repr=False)
    arrival_date: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_tm_qb``(``MergeSeatsCOutTrnInfo``).
    arrival_time_qb: str | None = field(default=None, repr=False)
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_construction_order: str | None = None
    arrival_construction_order: str | None = None
    departure_run_order: str | None = None
    arrival_run_order: str | None = None
    car_type_name: str | None = None
    general_room_name: str | None = None
    special_room_name: str | None = None
    general_reservation_code: str | None = None
    #: ``h_gen_rsv_nm``(``MergeSeatsCOutTrnInfo``).
    general_reservation_name: str | None = None
    special_reservation_code: str | None = None
    free_seat_reservation_code: str | None = None
    standing_reservation_code: str | None = None
    standing_reservation_name: str | None = None
    #: ``h_jrny_rsv_cd``/``h_jrny_rsv_nm``(``MergeSeatsCOutTrnInfo``).
    journey_reservation_code: str | None = None
    journey_reservation_name: str | None = None
    seat_map_flag: str | None = None
    delay_sale_flag: str | None = None
    wait_reservation_flag: str | None = None
    reservation_possible_name: str | None = None
    special_reservation_possible_name: str | None = None
    info_text: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    #: ``shtmStndOpFlg`` — 셔틀 입석 오픈 여부(``MergeSeatsCOutTrnInfo``).
    shuttle_standing_open_flag: str | None = None
    #: ``restStndNum`` — 잔여 입석수(``MergeSeatsCOutTrnInfo``).
    remaining_standing_count: str | None = None
    #: ``h_std_rest_seat_cnt`` — 일반실 잔여석. 두 DTO 모두 선언합니다.
    standard_remaining_seat_count: str | None = None
    #: ``h_fst_rest_seat_cnt`` — 특실 잔여석(``TrainScheduleOutTrainInfo``).
    first_remaining_seat_count: str | None = None
    #: ``h_yms_apl_flg`` — 이 행이 병합(입석+좌석) 대상인지를 정하는 유일한
    #: 입력(``TrainScheduleOutTrainInfo``, ``models.TrainSummary`` 참고).
    merge_target_flag: str | None = None
    #: ``h_trn_sps_flg`` — 운휴 표시/예약 게이트(``TrainScheduleOutTrainInfo``).
    train_suspended_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassScheduleTrain:
    """정기권 일정의 열차 한 행(``TrainList.java:25-70``, 20개 필드).

    이전에는 8개만 매핑돼 :attr:`run_date`(``h_run_dt``) — 이 행의 유일한
    날짜 — 조차 없었습니다.
    """

    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    departure_station_code: str | None = None
    departure_station_name: str | None = None
    detour_code: str | None = None
    schedule_price: str | None = None
    train_group_code: str | None = None
    train_no: str | None = None
    #: ``h_trn_seq`` — 열차 순번.
    train_sequence: str | None = field(default=None, repr=False)
    #: ``h_chg_trn_seq``/``h_chg_trn_dv_cd`` — 변경된 열차의 순번·구분 코드.
    change_train_sequence: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = None
    #: ``h_run_dt`` — 이 행의 유일한 운행일자.
    run_date: str | None = None
    price_class_code: str | None = None
    route_code: str | None = field(default=None, repr=False)
    departure_construction_order: str | None = field(default=None, repr=False)
    arrival_construction_order: str | None = field(default=None, repr=False)
    car_type_code: str | None = None
    train_class_code: str | None = None
    commuter_use_terminal_code: str | None = None
    commuter_use_terminal_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassAgeOption:
    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassScheduleInfo:
    trains: tuple[PassScheduleTrain, ...] = field(
        default=(),
        repr=False,
    )
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassScheduleMainInfo:
    sale_window_no: str | None = field(default=None, repr=False)
    work_date: str | None = field(default=None, repr=False)
    work_time: str | None = field(default=None, repr=False)
    job_id: str | None = field(default=None, repr=False)
    version_no: str | None = None
    message_code: str | None = None
    selected_count: str | None = None
    total_selected_count: str | None = None
    count_per_page: str | None = None
    page_count: str | None = None
    next_page_flag: str | None = None
    change_train_division_code: str | None = None
    page_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SeatAssignmentScheduleResponse(BaseKorailResponse):
    """``assignScheduleView.do`` — ``TrainScheduleOut.java:67`` 의 전체 필드.

    이전에는 :attr:`next_page_flag` 만 꺼내 페이징 신호는 있는데 되실을
    커서가 없었습니다. 같은 DTO 모양을 쓰는 형제 파서
    ``parsers.py::parse_train_search_metadata``/``TrainSearchMetadata`` 가
    이미 이 필드 집합을 정확히 이렇게 읽으므로 그 이름을 그대로 따릅니다.
    """

    next_page_flag: str | None = None
    merge_reservation_possible_flag: str | None = None
    job_id: str | None = None
    menu_id: str | None = None
    goods_no: str | None = None
    notice_message: str | None = None
    first_seat_count: str | None = None
    second_seat_count: str | None = None
    agreement_text: str | None = None
    first_departure_time: str | None = None
    result_count: str | None = None
    next_query_station_no: str | None = None
    next_train_no: str | None = None
    next_preceding_train_no: str | None = None
    next_connecting_train_no: str | None = None
    remaining_seat_count: str | None = None
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class IntermediateStation:
    code: str | None = None
    name: str | None = None
    run_order: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPeriodOption:
    commuter_period_code: str | None = None
    display_name: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MergeSeatsInquiryResponse(BaseKorailResponse):
    merge_reservation_possible_flag: str | None = None
    #: ``runDt`` — 최상위 운행일자(``MergeSeatsCOut.java:29,112``).
    run_date: str | None = None
    intermediate_stations: tuple[IntermediateStation, ...] = ()
    trains: tuple[TrainScheduleItem, ...] = ()


@dataclass(frozen=True)
class PassMenuData:
    commuter_kind_code: str | None = None
    station_selection: str | None = None
    age_options: tuple[PassAgeOption, ...] = ()
    period_options: tuple[PassPeriodOption, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPassengerInfo:
    h_cls_prnb: int | None = None
    h_dcnt_knd_cd: str | None = None
    h_st_prnb: int | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassPassengerInfos:
    h_chtn_allw_flg: str | None = None
    h_max_cnt: str | None = None
    h_min_cnt: str | None = None
    psg_info: tuple[PassPassengerInfo, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassGoodsInfo:
    h_cnd_flg_disc_no: str | None = field(default=None, repr=False)
    psg_infos: PassPassengerInfos | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PassMenuItem:
    #: ``afterDay`` — 서버가 문자열로 보냅니다(``PassMenuOutItem.java:28``
    #: ``String``). 형제 :class:`CommuterKindMenuResponse.after_day` 와 형이
    #: 같습니다. 정수가 필요하면 호출자가 변환하십시오 — 앱도 그 자리에서
    #: ``StringExKt.safeToInt`` 로 파싱 실패 시 0을 씁니다.
    after_day: str | None = None
    agreement: str | None = None
    detail_type: str | None = None
    detail_description: str | None = None
    enabled: str | None = None
    item_id: str | None = None
    information: str | None = None
    sale_message_1: str | None = None
    sale_message_2: str | None = None
    sale_message_3: str | None = None
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CrewRequestListResponse(BaseKorailResponse):
    items: tuple[CrewRequestOption, ...] = ()


@dataclass(frozen=True)
class PassScheduleResponse(BaseKorailResponse):
    main_info: PassScheduleMainInfo | None = None
    schedules: tuple[PassScheduleInfo, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class DiscountCardSection:
    """할인카드가 등록된 구간 하나.

    ``TicketDetailDao.AppSegInfo``
    (``dao/refund/TicketDetailDao.java:25-64``). N카드는 이런 구간 1~3 개에
    대해 팔리고, 그 구간을 지나는 열차에만 쓸 수 있습니다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_schedule`
    가 역코드가 아니라 역 **이름** 을 받는 것도 그것이 여기서 나오기
    때문입니다.
    """

    departure_station_name: str | None = None
    arrival_station_name: str | None = None
    #: ``jrnySqno`` — 이 구간의 순번. 예전에는 존재하지 않는 키
    #: (``dcntCrdAplSegSqno``, 전 디컴파일 0건)를 ``section_sequence`` 로
    #: 잘못 읽었는데, 실제로 가장 가까운 필드는 바로 이 ``journey_sequence``
    #: 입니다.
    journey_sequence: str | None = field(default=None, repr=False)
    journey_type_code: str | None = field(default=None, repr=False)
    train_group_code: str | None = field(default=None, repr=False)
    #: ``stlbDturDvNm`` — 경유 이름. 앱이 좌석지정 시각표 요청에 그대로
    #: 넘깁니다(``u4/b.java:104``).
    detour_division_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCardOnTicket:
    """승차권 상세가 설명하는 할인카드.

    ``TicketDetailDao.DiscountCardInfo``
    (``dao/refund/TicketDetailDao.java:123-142``)이며
    ``TicketDetailResponse.dcnt_crd_info`` 로 옵니다(``:233``). 읽고 있는
    "승차권"이 실은 카드일 때만 있고, 보통 승차권에는 이 객체가 없습니다.

    :attr:`card_no` 를 얻으려고 있는 모델입니다.
    :meth:`~korail_mobile_api.client.KorailClient.get_discount_card_usage_history`
    의 유일한 입력이고, 할인코드 ``"153"`` 과 함께 평범한 예약을 할인 예약으로
    바꾸는 유일한 입력이기도 합니다(``w4/a.java:100-101``).
    :mod:`korail_mobile_api.redaction` 에 등록돼 있어 마스킹됩니다.
    """

    #: ``h_dcnt_crd_no``.
    card_no: str | None = field(default=None, repr=False)
    #: ``h_dcnt_crd_trm_extn_psb_flg`` — 기간연장이 가능하면 ``"Y"``.
    #: 앱에서 "기간연장" 버튼을 켜는 것도 이 값 하나입니다
    #: (``Y4/C0907b.java:301`` → ``Y4/Q.java:1013-1026``).
    term_extension_possible_flag: str | None = None
    sections: tuple[DiscountCardSection, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class KorailPointSummaryResponse(BaseKorailResponse):
    """``xPoint.MyXPointView`` — 포인트·자격 요약
    (``KorailPointInquiryDao.java:11-85``).

    ``h_hdcp_flg == "Y"`` 일 때만 장애인 할인 자격 있음
    (``MyPageActivity.java:206-212``).
    """

    #: ``h_korail_point`` — 마이페이지에 뜨는 코레일 포인트 잔액.
    korail_point: str | None = None
    #: ``h_disc_coup_cnt`` — 계정이 가진 할인쿠폰 개수.
    #: :meth:`~korail_mobile_api.client.KorailClient.get_discount_coupons` 가
    #: 실제로 돌려주는 목록의 개수입니다.
    discount_coupon_count: str | None = None
    #: ``h_delay_cnt`` — 계정이 가진 지연할인권 개수.
    delay_discount_count: str | None = None
    #: ``h_hdcp_flg`` — 장애인 등록이 있으면 ``"Y"``.
    disability_flag: str | None = field(default=None, repr=False)
    #: ``h_subt_dcs_cl_nm`` / ``h_subt_dcs_cl_cd`` — 그 등록이 주는 우대할인
    #: 등급. 앱에서 장애인증 라벨 아래 찍힙니다.
    welfare_discount_class_name: str | None = field(default=None, repr=False)
    welfare_discount_class_code: str | None = field(default=None, repr=False)
    #: ``h_cust_lead_flg_nm`` — 앱에서 보조견 라벨 아래 찍힙니다.
    customer_lead_flag_name: str | None = field(default=None, repr=False)
    #: ``h_cp_athn_flg`` / ``h_emil_athn_flg`` — 휴대폰·이메일 인증 여부.
    phone_verified_flag: str | None = field(default=None, repr=False)
    email_verified_flag: str | None = field(default=None, repr=False)
    contact_channel_content: str | None = field(default=None, repr=False)
    #: ``h_logn_tp_cd1``/``2``/``4``/``5`` — 네이버·카카오·구글·애플 소셜
    #: 로그인 연동. ``MyPageActivity.java:214-236`` 이 읽는 순서 그대로입니다.
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
    #: ``pontAmt`` — 이 줄의 포인트 증감. 부호가 붙습니다.
    point_amount: str | None = None
    #: ``savePontValNum`` — 이 줄 시점의 누적 잔액.
    saved_point_value: str | None = field(default=None, repr=False)
    #: ``stlAmt`` — 이 줄이 나온 정산 운임.
    settlement_amount: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MileageHistoryResponse(BaseKorailResponse):
    """``mlg.amtSpec.do`` — 마일리지 적립/사용 내역 한 페이지.

    ``MileageInquiryDao.MileageInquiryResponse``
    (``dao/xPoint/MileageInquiryDao.java:72-126``).

    앱의 합계 줄은 :attr:`total_available_rail_point` 와
    :attr:`total_available_rail_point_1` 을 KTX 마일리지와 삼성카드
    마일리지로 각각 찍고 더합니다(``MileageHistoryActivity.java:574-578``).
    그래서 하나로 합치지 않고 둘 다 내놓습니다.
    """

    #: ``pgCnt`` — 전체 페이지 수. 앱은 무한 스크롤의 상한으로 씁니다
    #: (``MileageHistoryActivity.java:581``).
    page_count: str | None = None
    query_count: str | None = None
    total_available_rail_point: str | None = None
    total_available_rail_point_1: str | None = None
    total_available_affiliate_point: str | None = None
    total_accumulated_rail_point_1: str | None = field(
        default=None,
        repr=False,
    )
    total_used_rail_point_1: str | None = field(default=None, repr=False)
    #: ``delPontValNum`` — 이번 달에 소멸하는 포인트.
    expiring_point_value: str | None = None
    ktx_mileage_info: str | None = field(default=None, repr=False)
    entries: tuple[MileageHistoryEntry, ...] = ()


@dataclass(frozen=True)
class DiscountCardUsage:
    """할인카드(N카드)를 이미 쓴 여행 한 건.

    ``NCardHistoryDao.NCardHistoryInfo``
    (``dao/research/NCardHistoryDao.java:12-61``). 앱은 정확히 이 다섯 필드로
    번호 매긴 목록을 그립니다 — 승객 이름,
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
    #: ``"Y"`` 입니다(N카드 2인용).
    additional_user_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCardUsageListResponse(BaseKorailResponse):
    """``ticket.dcntCrdUseQry.do`` — 카드가 쓰인 여행 목록.

    ``NCardHistoryDao.NCardHistoryResponse``
    (``dao/research/NCardHistoryDao.java:78-87``)가 싣는 것은 ``tkUseList``
    하나뿐이라, 전선에 없는 요약 필드를 이 모델도 만들어 붙이지 않습니다.
    """

    items: tuple[DiscountCardUsage, ...] = ()


@dataclass(frozen=True)
class DiscountCardScheduleTrain:
    """할인카드를 아직 쓸 수 있는 열차 하나.

    ``NCardInquiryDao.TrainInfo``
    (``dao/research/NCardInquiryDao.java:144-236``).

    ``stationInfo`` 는 일부러 없습니다. 그것은 앱이 중간 정차역 문자열로부터
    스스로 만들어 내는 ``android.text.Spanned`` 이지 전선에서 읽는 값이
    아닙니다. ``stationStringInfo`` 라는 전선 키 자체가 전 디컴파일에 0건이라
    더 이상 읽지 않습니다.

    ``NCardScheduleItem`` 은 20개 필드를 선언하는데(``:25-49``) 전부
    ``@SerialName`` 이 없어 정확한 와이어 철자는 PROTECTED 입니다 — 코틀린
    필드명을 최선으로 사용합니다.
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
    #: ``dptStnRunOrdr`` — 승차역 "운행" 순서. ``departure_station_order``
    #: (``dptStnConsOrdr``, "편성" 순서)와는 다른 필드입니다.
    departure_run_order: str | None = field(default=None, repr=False)
    #: ``arvStnRunOrdr`` — 하차역 운행 순서.
    arrival_run_order: str | None = field(default=None, repr=False)
    #: ``chtnTrnOrdrNo`` — 환승 열차 순번.
    transfer_train_order_no: str | None = field(default=None, repr=False)
    #: ``prcClCd`` — 운임 구분 코드.
    price_class_code: str | None = None
    #: ``stlbCarTpCd``/``stlbTrnClsfCd`` — 정산용 호차·열차 종류 코드.
    settlement_car_type_code: str | None = field(default=None, repr=False)
    settlement_train_class_code: str | None = field(default=None, repr=False)
    #: ``cmtrPrc`` — 이 카드의 구간에 매겨진 운임.
    commuter_price: str | None = None
    direct_transfer_division_code: str | None = field(default=None, repr=False)
    detour_code: str | None = field(default=None, repr=False)
    detour_name: str | None = field(default=None, repr=False)
    route_code: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class DiscountCardScheduleResponse(BaseKorailResponse):
    """``research.dcntCrdScheduleView.do`` — 카드로 예약할 수 있는 열차들.

    ``NCardInquiryDao.NCardInquiryResponse``
    (``dao/research/NCardInquiryDao.java:128-142``).

    :attr:`following_page_exists` 는 더 이상 채워지지 않습니다. 7.0.6
    ``NCardScheduleOut``(``:27-28``)은 ``trnScdlList`` 하나만 선언할 뿐
    ``fllwPgExt`` 를 갖지 않습니다 — 그 키는 다른 DTO(``ScdlQryOut``, 리무진
    일정)의 필드입니다. ``NCardScheduleOut`` 자체에는 대체할 다른 페이징
    신호도 없어(정확히 이 한 필드만 선언), 이 라우트의 서버측 페이징 여부는
    현재 미확인입니다 — 항상 ``None`` 인 이 필드를 폴링 신호로 쓰지
    마십시오.
    """

    #: 항상 ``None``. 아래 클래스 독스트링 참고.
    following_page_exists: str | None = None
    trains: tuple[DiscountCardScheduleTrain, ...] = ()


@dataclass(frozen=True)
class MultiChildDiscountTarget:
    birth_date: str | None = field(default=None, repr=False)
    customer_family_name: str | None = field(default=None, repr=False)
    discount_kind_code: str | None = None
    family_sequence: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = None
    passenger_type_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    requested_discount_kind_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MultiChildDiscountTargetResponse(BaseKorailResponse):
    targets: tuple[MultiChildDiscountTarget, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class CustomerTripInfo:
    additional_seat_attribute_code: str | None = None
    adult_disabled_person_count: str | None = None
    adult_count: str | None = None
    arrival_station_code: str | None = None
    arrival_station_name: str | None = None
    baby_accompanying_person_count: str | None = None
    changed_at: str | None = None
    changed_by: str | None = field(default=None, repr=False)
    child_count: str | None = None
    child_disabled_person_count: str | None = None
    customer_management_no: str | None = field(default=None, repr=False)
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
    room_class_code: str | None = field(default=None, repr=False)
    passenger_total: str | None = None
    registered_at: str | None = None
    registration_sequence: str | None = None
    registered_by: str | None = field(default=None, repr=False)
    trip_day_no: str | None = None
    train_classification_code: str | None = None
    train_connection_flag: str | None = None
    train_group_code: str | None = None
    usage_day_no: str | None = None
    #: ``gdNo`` — 상품번호. ``CustTripInfo.java`` 33필드 중 마지막으로
    #: 빠져 있던 필드. ``@SerialName`` 이 없어 와이어 철자는 PROTECTED 이며
    #: 코틀린 필드명을 최선으로 사용합니다.
    goods_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CustomerTripInfoResponse(BaseKorailResponse):
    trips: tuple[CustomerTripInfo, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class MaasServiceDetailInfo:
    additional_service_request_no: str | None = field(default=None, repr=False)
    booking_time: str | None = None
    branch_name: str | None = None
    partner_name: str | None = None
    delivery_datetime: str | None = None
    drop_times: str | None = None
    dropoff_name: str | None = None
    image: str | None = field(default=None, repr=False)
    name: str | None = None
    option_name: str | None = None
    pickup_name: str | None = None
    pickup_place: str | None = None
    pickup_times: str | None = None
    reservation_date: str | None = None
    return_datetime: str | None = None
    start_datetime: str | None = None
    cancel_deadline_date: str | None = None
    cancel_return_amount: str | None = None
    cancel_return_fee: str | None = None
    goods_sequence: str | None = field(default=None, repr=False)
    intermediate_value: str | None = None
    received_amount: str | None = None
    reservation_status_name: str | None = None
    reservation_passenger_name: str | None = field(default=None, repr=False)
    settlement_deadline_date: str | None = None
    settlement_deadline_datetime: str | None = None
    settlement_status_code: str | None = None
    settlement_status_name: str | None = None
    total_settlement_amount: str | None = None
    usage_period_content: str | None = None
    entity_one: tuple[Mapping[str, Any], ...] = field(default=(), repr=False, compare=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    reservation_station_code_name: str | None = None
    reservation_specification_url: str | None = field(default=None, repr=False)
    usage_close_date: str | None = field(default=None, repr=False)
    usage_start_date: str | None = field(default=None, repr=False)
    detail_info: MaasServiceDetailInfo | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    details: tuple[MaasServiceDetail, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class TripChangeDateResponse(BaseKorailResponse):
    """``research.tripChgDateInquiry.do`` (``TipChgDateInquiryOut.java:28-30``).

    ``tripChgDate``(단수)는 **요청** DTO(``TipChgDateInquiryIn.java:29``)의
    필드입니다 — 응답은 복수형 ``tripChgDates``(``List<String>``)만
    선언하므로, 여기서는 단수형을 읽지 않습니다.
    """

    last_run_date: str | None = None
    trip_change_dates: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommuterPassengerOption:
    """``Psg.java:28-33``, 6개 필드 중 4개만 있으면 연령 하한/상한이 없습니다."""

    commuter_usage_age_code: str | None = None
    common_code_name: str | None = None
    #: ``custAgeFrom``/``custAgeTo`` — 이 옵션이 적용되는 연령 하한/상한.
    customer_age_from: int = 0
    customer_age_to: int = 0
    passenger_count_from: int = 0
    passenger_count_to: int = 0
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class CommuterInfoResponse(BaseKorailResponse):
    additional_service_goods_flag: str | None = None
    companion_flag: str | None = None
    commuter_kind_code: str | None = None
    commuter_usage_age_code: str | None = None
    menu_id: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    promotion_message: str | None = None
    promotion_url: str | None = None
    seat_attribute_code: str | None = None
    available_passenger_count_from: int = 0
    available_passenger_count_to: int = 0
    passenger_options: tuple[CommuterPassengerOption, ...] = ()


@dataclass(frozen=True)
class PriceFare:
    journey_sequence: str | None = None
    room_class_name: str | None = field(default=None, repr=False)
    received_fare: str | None = None
    received_price: str | None = None
    total_amount: str | None = None
    train_no: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PriceFareQuoteResponse(BaseKorailResponse):
    fares: tuple[PriceFare, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class DeliveryRecipientResponse(BaseKorailResponse):
    acceptance_customer_management_no: str | None = field(
        default=None,
        repr=False,
    )
    acceptance_customer_name: str | None = field(default=None, repr=False)
    acceptance_customer_phone: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class TicketDuplicationCheckResponse(BaseKorailResponse):
    #: ``rsvCnt`` — ``TicketDupCheckOut.java:28`` 의 선언은 ``String`` 입니다.
    #: 예전 주석은 "Gson 이 DAO 의 Java int 를 강제 변환한다" 고 적었지만 이
    #: DTO 는 kotlinx이고 끝까지 String 입니다 — 지금까지는 동작이 중립이었을
    #: 뿐(둘 다 ASCII-decimal 문자열을 받아들이므로), 그 잘못된 근거를 믿고
    #: 나중에 문자열 처리 경로를 지우는 사고를 막기 위해 고칩니다.
    reservation_count: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class PbpAcceptanceSeat:
    passenger_type_division_name: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    car_no: int = field(default=0, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PbpAcceptanceTicket:
    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_sequence: str | None = field(default=None, repr=False)
    sale_window_no: str | None = field(default=None, repr=False)
    return_password: str | None = field(default=None, repr=False)
    journeys: tuple[PbpAcceptanceJourney, ...] = field(default=(), repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class PbpAcceptanceSpecificationResponse(BaseKorailResponse):
    tickets: tuple[PbpAcceptanceTicket, ...] = field(default=(), repr=False)


@dataclass(frozen=True)
class SelfSeatChangeStation:
    """자율 좌석 변경으로 옮겨 갈 수 있는 승차역 하나.

    ``CallSelfSeatChgInfoDao.ChgStnList``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:157-204``).

    이 줄을 고를 수 있는지는 좌석 수 둘이 정합니다 —
    :attr:`general_remaining_seats`(``gnrmRestSeatNum``)와
    :attr:`special_remaining_seats`(``sprmRestSeatNum``)가 이 역에서 시작하는
    구간의 일반실·특실 잔여 좌석입니다.
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SelfSeatChangeReason:
    """좌석 변경 사유 한 줄(``CallSelfSeatChgInfoDao.java:136-155``)."""

    query_code: str | None = None
    query_order: str | None = None
    reason_text: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class SelfSeatChangeInfoResponse(BaseKorailResponse):
    """``self.seatChgInfo.do`` — 자율 좌석·열차 변경이 무엇으로 바뀔 수 있는지.

    ``CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse``
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:64-134``).

    :attr:`general_reservation_possible_code` /
    :attr:`special_reservation_possible_code`
    (``gnrmRsvPsbCd``/``sprmRsvPsbCd``)는 객실 등급별 **열차 단위**
    가부입니다. 역별 잔여 좌석은 :attr:`stations` 쪽에 있습니다.
    """

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

    좌석 식별자 자체(``scarNo``/``seatNo``)는
    :mod:`korail_mobile_api.redaction` 에 등록돼 있습니다.
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicketJourney:
    """원표의 구간 하나(``response/research/Jrny.java``).

    변경 흐름이 이 줄을 열쇠로 삼습니다 — ``jrnySqno`` 와 출발·도착 역코드·
    운행순서가 뒤따르는 조회들이 그대로 요구하는 인자입니다.
    """

    journey_sequence: str | None = None
    journey_order: str | None = None
    #: ``jrnyTpCd``. 전선 철자와 속성 철자 양쪽이 민감 키로 등록돼 있어, 이
    #: 값을 드러내는 다른 모델과 마찬가지로 표현에서 뺍니다.
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicket:
    """원표 하나(``response/research/OrgTk.java``).

    ``original_*`` 네 값은 승차권 자신의 반환번호가 되돌아온 것입니다 — 요청이
    보낸 것과 같은 비밀이라 전선 철자와 속성 철자 양쪽에서 마스킹됩니다.

    ``cmpnList``(동반 할인)와 ``stlList``(정산 줄)는 일부러 :attr:`raw` 에만
    남깁니다. 지연증명 반환번호, 카드번호, 승인번호 같은 자격증명이 더 들어
    있는데 변경 흐름에는 쓸 일이 없기 때문입니다. 그 전선 키들도
    :mod:`korail_mobile_api.redaction` 에 등록돼 있어 ``raw`` 안에서 마스킹된
    채로 있습니다.
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class OriginalTicketInquiryResponse(BaseKorailResponse):
    """``research.tripChgOgtk.do`` — 변경이 출발점으로 삼을 원표들.

    ``OgTkInquiryDao.OgTkInquiryResponse``
    (``dao/research/OgTkInquiryDao.java:38-46``).
    """

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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class RecentDeliveryHistoryResponse(BaseKorailResponse):
    changed_acceptance_reservation_no: str | None = field(default=None, repr=False)
    recipients: tuple[RecentDeliveryRecipient, ...] = field(
        default=(),
        repr=False,
    )


@dataclass(frozen=True)
class ReservationSeatDetail:
    """보류된 예약의 좌석 한 줄(``seat_infos.seat_info[]``).

    필드 이름은 ``ReservationResponse.SeatInfo``
    (``response/certification/ReservationResponse.java:296-313``)를 따릅니다.

    :attr:`passenger_type_code` 는 ``h_psg_tp_cd`` 입니다. 앱은 이 줄의 승객
    종류를 **코드** 로 선언하고, 디컴파일된 앱 어디에도
    ``h_psg_tp_dv_nm`` 이 없습니다. 그래서 일부 서드파티 클라이언트가 이름
    붙인 표시명 변형은 모델링하지 않았습니다. 서버가 그것을 보낸다면
    :attr:`raw` 로 닿을 수 있습니다.

    운임 재계산 요청의
    :class:`~korail_mobile_api.mutation_models.PriceRecalculationRow` 는 이
    줄에서 앞의 세 값을 그대로 베낍니다.
    """

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — 이 좌석에 실제로 걷히는 금액. 예약 응답에
    #: ``h_tot_rcvd_amt`` 가 없을 때 결제 경로가 ``hidMnsStlAmt1`` 을 이 값들의
    #: 합으로 구하므로, 정산 금액을 다른 출처로 대조해 볼 수 있습니다.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    #: ``h_tot_disc_amt`` — 이 좌석의 총 할인액. 형제 금액 필드(수령액·좌석가·
    #: 좌석운임)와 함께 있었는데 이 필드만 빠져 있었습니다. 같은 와이어 키를
    #: ``_REFUND_TICKET_DETAIL_FIELDS`` 가 ``total_discount_amount`` 로 매핑하는
    #: 것과 이름을 맞춥니다.
    total_discount_amount: str | None = None
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class ReservationDetailJourney:
    """보류된 예약의 여정 하나(``jrny_infos.jrny_info[]``)."""

    journey_sequence: str | None = None
    journey_type_code: str | None = field(default=None, repr=False)
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    #: ``h_arv_dt`` — 도착일. ``arrival_time``(``h_arv_tm``)과 별개 필드라,
    #: 심야·익일 도착 열차에서 도착 시각을 고정할 날짜가 이 필드 없이는
    #: 없었습니다.
    arrival_date: str | None = None
    departure_station_name: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_class_name: str | None = None
    seats: tuple[ReservationSeatDetail, ...] = ()
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class TicketReservationDetailResponse(BaseKorailResponse):
    """PNR 로 다시 읽은 보류 예약(``certification.ReservationList``).

    응답 타입이 예약 요청이 돌려주는 것과 같은 ``ReservationResponse``
    입니다. 그래서 이 조회는 이 패키지가 이미 만들 수 있는 예약을 **다른
    출처로** 다시 보는 셈이고, 창구번호(``h_wct_no``)와 결제 폼이 정산할
    좌석별 금액을 여기서 확인할 수 있습니다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 정산 합계. 결제 폼의 ``hidMnsStlAmt1`` 을 예약
    #: 응답이 아닌 출처로 대조할 수 있습니다.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """원표 하나의 환불 수수료와 환불액.

    필드는 ``RefundCommissionDao.RefundCommissionResponse``
    (``dao/refund/RefundCommissionDao.java:70-77``)를 따릅니다.

    "얼마가 돌아오고 수수료는 얼마인가"를 미리 보는 조회입니다. 실제 환불을
    보내기 전에 먼저 불러야 합니다.
    """

    #: ``ret_amt`` — 돌려받을 금액.
    refund_amount: str | None = None
    #: ``ret_fee`` — 거기서 떼는 수수료.
    refund_fee: str | None = None
    #: ``prg_psb_flg`` — 환불을 진행할 수 있는지 여부입니다.
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — 이 경로가 봉투의 것과 별개로 싣는
    #: **두 번째** 메시지 짝. 성공한 사전 조회에 수수료 정책 안내가 붙는
    #: 식입니다.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RefundTicketSeat:
    """환불 대상 승차권의 좌석 하나(``tk_seat_info[]``)."""

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    buyer_name: str | None = field(default=None, repr=False)
    checkin_status_code: str | None = None
    discount_kind_code: str | None = None
    discount_kind_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = None
    passenger_type_name: str | None = field(default=None, repr=False)
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class RefundTicketDetailResponse(BaseKorailResponse):
    """환불 대상 승차권의 상세(``refunds.SelTicketInfo``).

    필드는 ``TicketDetailDao.TicketDetailResponse``
    (``dao/refund/TicketDetailDao.java:227-281``)를 따릅니다.

    두 조회가 사슬로 이어집니다. 앱은 :attr:`companion_name` 과
    :attr:`companion_birth_date` 를 뒤따르는 ``CommissionView`` 호출에
    ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 넘깁니다
    (``TicketListActivity.java:908-909``).

    환불 신원을 손으로 조립하지 말고
    :meth:`~korail_mobile_api.mutation_models.PaidTicket.from_refund_detail`
    에 이 응답을 넘겨야 합니다.

    ``mlgSaveFlg``(환불 시 마일리지 복구 여부)는 더 이상 읽지 않습니다 — 전
    디컴파일에 0건인 팬텀 키였습니다.
    """

    pnr_no: str | None = field(default=None, repr=False)
    sale_date: str | None = field(default=None, repr=False)
    sale_time: str | None = field(default=None, repr=False)
    window_name: str | None = field(default=None, repr=False)
    original_sale_date: str | None = field(default=None, repr=False)
    original_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    #: ``h_tk_knd_cd`` — 승차권 종류 코드. 개인정보가 아닙니다. 형제 클래스
    #: ``OriginalTicket``/``StationRefundOriginalTicket`` 에서도 평범한
    #: 필드라, 그쪽과 표시를 맞춥니다.
    ticket_kind_code: str | None = None
    ticket_kind_name: str | None = None
    #: ``retPsbFlg`` — 이 승차권이 환불 가능한지 여부. 환불 전에 볼 수 있는
    #: 가장 싼 사전 점검입니다.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    #: ``h_abrd_ps_nm``/``s_brth`` — **탑승자 본인**의 성명·생년월일.
    #: ``h_compa_nm``/``h_compa_brth``(동승자 쌍, 아래)와는 별개의, 최상위
    #: 단일 필드 쌍입니다(``TicketDetailOut.java:410,418``). ``psgNmList``
    #: (아래 :attr:`passenger_names`, 승객 성명 **목록**)와도 서로 다른
    #: 필드입니다 — 요약 필드 하나와 목록 하나이지 같은 것의 중복이
    #: 아닙니다.
    passenger_name: str | None = field(default=None, repr=False)
    passenger_birth_date: str | None = field(default=None, repr=False)
    #: ``h_compa_nm``/``h_compa_brth`` — CommissionView 요청에
    #: ``h_comp_nm``/``h_comp_cert_no`` 로 그대로 복사돼 나갑니다.
    companion_name: str | None = field(default=None, repr=False)
    companion_birth_date: str | None = field(default=None, repr=False)
    #: ``h_pbp_acep_tgt_flg`` — PBP 인수 대상 여부 (``ticketReturn/a.java:430-431``).
    pbp_acceptance_target_flag: str | None = None
    #: ``h_dlay_flg``/``h_dlay_tk_flg`` — 지연 보상 대상 여부.
    delay_flag: str | None = None
    delay_ticket_flag: str | None = None
    #: ``addSrvFlg``/``addSrvCancel`` — 딸린 부가서비스가 있는지, 환불이 그것도
    #: 함께 취소하는지 여부.
    additional_service_flag: str | None = None
    additional_service_cancel: str | None = None
    #: ``h_qrcode`` — 이 승차권의 QR 코드(``TicketDetailOut.java:478``).
    qr_code: str | None = field(default=None, repr=False)
    #: ``psgNmList`` — 승객 성명 목록(``List<PsgNameInfo>``). ``@SerialName``
    #: 이 없어 와이어 철자는 PROTECTED, 코틀린 필드명을 최선으로 사용합니다.
    #: 각 원소는 아직 행 단위로 모델링하지 않고 원본 그대로 노출합니다.
    passenger_names: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    #: ``seatTicketList`` — 좌석 배정 목록(``List<SeatAssignInfo>``, PROTECTED).
    seat_tickets: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    #: ``limousine`` — 연계된 리무진 예약(단일 객체, PROTECTED). 없으면 ``None``.
    limousine: Mapping[str, Any] | None = field(default=None, repr=False, compare=False)
    #: ``dtlList`` — 지연 정보 목록(``List<DelayInfo>``, PROTECTED).
    delay_details: tuple[Mapping[str, Any], ...] = field(
        default=(), repr=False, compare=False
    )
    journeys: tuple[RefundTicketJourney, ...] = ()
    #: ``dcnt_crd_info`` — 이 "승차권"이 실은 할인카드(N카드)일 때만 있습니다.
    #: 보통 승차권에서는 ``None`` 입니다.
    discount_card: DiscountCardOnTicket | None = None
