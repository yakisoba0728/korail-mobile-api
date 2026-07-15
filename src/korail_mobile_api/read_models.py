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
class PassAgeOption:
    commuter_age_code: str | None = None
    display_name: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
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
