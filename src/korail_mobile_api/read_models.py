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
    """One seat row of a held reservation (``seat_infos.seat_info[]``).

    Field names follow ``ReservationResponse.SeatInfo``
    (``response/certification/ReservationResponse.java:296-313``).
    ``passenger_type_code`` is ``h_psg_tp_cd``: the app declares the passenger
    type as a CODE on this row and there is no ``h_psg_tp_dv_nm`` anywhere in
    the decompiled app, so the display-name variant some third-party clients
    name is not modelled. If the server does send it, it stays reachable
    through :attr:`raw`.
    """

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    room_class_code: str | None = field(default=None, repr=False)
    room_class_name: str | None = field(default=None, repr=False)
    passenger_type_code: str | None = field(default=None, repr=False)
    #: ``h_rcvd_amt`` — the amount actually collected for this seat. Summing
    #: these is how the payment path derives ``hidMnsStlAmt1`` when the hold
    #: response omits ``h_tot_rcvd_amt``, so this read is an independent source
    #: for cross-checking the settled amount.
    received_amount: str | None = None
    seat_price: str | None = None
    seat_fare: str | None = None
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class ReservationDetailJourney:
    """One journey of a held reservation (``jrny_infos.jrny_info[]``)."""

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
    """A held reservation read back by PNR (``certification.ReservationList``).

    The response type is the app's ``ReservationResponse`` — the same DAO the
    reserve mutation returns — so this read gives an independent view of a hold
    the package can already create: ``window_no`` (``h_wct_no``) and the
    per-seat amounts that the payment form settles.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    pnr_no: str | None = field(default=None, repr=False)
    window_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    total_fare: str | None = None
    total_price: str | None = None
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — the settled total. Cross-checks ``hidMnsStlAmt1``
    #: on the payment form against a source that is not the hold response.
    total_received_amount: str | None = None
    payment_flag: str | None = None
    journeys: tuple[ReservationDetailJourney, ...] = ()


@dataclass(frozen=True)
class RefundCommissionResponse(BaseKorailResponse):
    """Refund fee and refundable amount for one original ticket.

    Fields follow ``RefundCommissionDao.RefundCommissionResponse``
    (``dao/refund/RefundCommissionDao.java:70-77``). This is the "how much comes
    back and what is the fee" pre-check that must precede a first live refund.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``ret_amt`` — the amount that would be returned.
    refund_amount: str | None = None
    #: ``ret_fee`` — the fee withheld from it.
    refund_fee: str | None = None
    #: ``prg_psb_flg`` — whether the refund may proceed at all.
    proceed_possible_flag: str | None = None
    ticket_return_times_division_code: str | None = None
    usable_mileage: str | None = None
    #: ``h_msg_cd2``/``h_msg_txt2`` — a SECOND message pair this route carries
    #: alongside the envelope's own, e.g. a fee-policy notice on a successful
    #: pre-check.
    secondary_message_code: str | None = None
    secondary_message_text: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class RefundTicketSeat:
    """One seat of a refund-target ticket (``tk_seat_info[]``)."""

    car_no: str | None = field(default=None, repr=False)
    seat_no: str | None = field(default=None, repr=False)
    buyer_name: str | None = field(default=None, repr=False)
    checkin_status_code: str | None = field(default=None, repr=False)
    discount_kind_code: str | None = field(default=None, repr=False)
    discount_kind_name: str | None = None
    passenger_type_code: str | None = field(default=None, repr=False)
    passenger_type_name: str | None = None
    seat_group_name: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class RefundTicketJourney:
    """One journey of a refund-target ticket (``ticket_infos.ticket_info[]``)."""

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
    """The refund target's ticket detail (``refunds.SelTicketInfo``).

    Fields follow ``TicketDetailDao.TicketDetailResponse``
    (``dao/refund/TicketDetailDao.java:227-281``). :attr:`companion_name` and
    :attr:`companion_birth_date` are what the app feeds straight into the
    following ``CommissionView`` call as ``h_comp_nm``/``h_comp_cert_no``
    (``TicketListActivity.java:908-909``), so the two reads chain.
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
    #: ``retPsbFlg`` — whether this ticket is refundable at all. The cheapest
    #: possible pre-flight for a refund.
    refund_possible_flag: str | None = None
    return_flag: str | None = None
    total_fare_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    train_running_flag: str | None = None
    #: ``h_compa_nm``/``h_compa_brth`` — copied verbatim into the CommissionView
    #: request as ``h_comp_nm``/``h_comp_cert_no``.
    companion_name: str | None = field(default=None, repr=False)
    companion_birth_date: str | None = field(default=None, repr=False)
    journeys: tuple[RefundTicketJourney, ...] = ()
