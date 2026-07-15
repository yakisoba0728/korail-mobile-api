from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


def _ascii_digits(
    value: object,
    name: str,
    *,
    lengths: frozenset[int],
    allow_empty: bool = False,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if allow_empty and value == "":
        return
    if (
        len(value) not in lengths
        or any(character < "0" or character > "9" for character in value)
    ):
        expected = ", ".join(str(length) for length in sorted(lengths))
        raise ValueError(f"{name} must contain {expected} ASCII digit(s)")


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _optional_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value and not value.strip():
        raise ValueError(f"{name} must be empty or contain non-whitespace text")


def _passenger_count(value: object, name: str, *, allow_zero: bool) -> None:
    minimum = 0 if allow_zero else 1
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not minimum <= value <= 9:
        qualifier = "0 through 9" if allow_zero else "1 through 9"
        raise ValueError(f"{name} must be an integer from {qualifier}")


def _boolean(value: object, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a boolean")


@dataclass(frozen=True)
class LimousineScheduleQuery:
    departure_date: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    service_code: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_time: str = field(repr=False)
    train_no: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    reservation_sale_division_code: str = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.departure_date,
            "departure_date",
            lengths=frozenset({8}),
        )
        _ascii_digits(
            self.departure_station_code,
            "departure_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.arrival_station_code,
            "arrival_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.room_class_code,
            "room_class_code",
            lengths=frozenset({1, 2}),
        )
        _ascii_digits(
            self.departure_time,
            "departure_time",
            lengths=frozenset({6}),
        )
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
            allow_empty=True,
        )
        _ascii_digits(
            self.seat_attribute_code,
            "seat_attribute_code",
            lengths=frozenset({3}),
            allow_empty=True,
        )
        _required_text(
            self.reservation_sale_division_code,
            "reservation_sale_division_code",
        )


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    train_class_code: str = field(repr=False)
    service_code: str = field(repr=False)
    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    car_no: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    departure_run_order: str = field(repr=False)
    arrival_run_order: str = field(repr=False)
    passenger_count: int = field(repr=False)
    product_no: str = field(repr=False)
    is_arrow: bool = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.train_class_code,
            "train_class_code",
            lengths=frozenset({2}),
        )
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
        )
        _ascii_digits(
            self.car_no,
            "car_no",
            lengths=frozenset({1, 2, 3, 4}),
        )
        _ascii_digits(
            self.room_class_code,
            "room_class_code",
            lengths=frozenset({1, 2}),
        )
        _ascii_digits(
            self.departure_station_code,
            "departure_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.arrival_station_code,
            "arrival_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.seat_attribute_code,
            "seat_attribute_code",
            lengths=frozenset({3}),
            allow_empty=True,
        )
        _ascii_digits(
            self.departure_run_order,
            "departure_run_order",
            lengths=frozenset({6}),
        )
        _ascii_digits(
            self.arrival_run_order,
            "arrival_run_order",
            lengths=frozenset({6}),
        )
        _passenger_count(
            self.passenger_count,
            "passenger_count",
            allow_zero=False,
        )
        _optional_text(self.product_no, "product_no")
        _boolean(self.is_arrow, "is_arrow")


@dataclass(frozen=True)
class LimousineScheduleViewQuery:
    menu_id: str = field(repr=False)
    job_id: str = field(repr=False)
    job_division: str = field(repr=False)
    service_code: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_time: str = field(repr=False)
    passenger_group_1_count: int = field(repr=False)
    passenger_group_2_count: int = field(repr=False)
    senior_count: int = field(repr=False)
    severe_disability_count: int = field(repr=False)
    mild_disability_count: int = field(repr=False)
    direction_seat_attribute_code: str = field(repr=False)
    location_seat_attribute_code: str = field(repr=False)
    room_seat_attribute_code: str = field(repr=False)
    ebiz_cross_check: bool = field(repr=False)
    srt_check: bool = field(repr=False)
    round_trip: bool = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.menu_id,
            "menu_id",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.job_id,
            "job_id",
            lengths=frozenset({1, 2, 3}),
        )
        _optional_text(self.job_division, "job_division")
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
            allow_empty=True,
        )
        _required_text(self.departure_station_name, "departure_station_name")
        _required_text(self.arrival_station_name, "arrival_station_name")
        _ascii_digits(
            self.departure_date,
            "departure_date",
            lengths=frozenset({8}),
        )
        _ascii_digits(
            self.departure_time,
            "departure_time",
            lengths=frozenset({6}),
        )
        passenger_fields = (
            ("passenger_group_1_count", self.passenger_group_1_count),
            ("passenger_group_2_count", self.passenger_group_2_count),
            ("senior_count", self.senior_count),
            ("severe_disability_count", self.severe_disability_count),
            ("mild_disability_count", self.mild_disability_count),
        )
        for name, value in passenger_fields:
            _passenger_count(value, name, allow_zero=True)
        total = sum(value for _, value in passenger_fields)
        if not 1 <= total <= 9:
            raise ValueError(
                "passenger counts must total an integer from 1 through 9"
            )
        for name, value in (
            (
                "direction_seat_attribute_code",
                self.direction_seat_attribute_code,
            ),
            (
                "location_seat_attribute_code",
                self.location_seat_attribute_code,
            ),
            ("room_seat_attribute_code", self.room_seat_attribute_code),
        ):
            _ascii_digits(value, name, lengths=frozenset({3}))
        _boolean(self.ebiz_cross_check, "ebiz_cross_check")
        _boolean(self.srt_check, "srt_check")
        _boolean(self.round_trip, "round_trip")


@dataclass(frozen=True)
class LimousineSchedule:
    arrival_date: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_run_order: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    transfer_division_code: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_run_order: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    general_remaining_seat_count: str | None = None
    delay_minutes: str | None = None
    free_remaining_seat_count: str | None = None
    standing_remaining_seat_count: str | None = None
    run_date: str | None = field(default=None, repr=False)
    special_remaining_seat_count: str | None = None
    train_class_code: str | None = field(default=None, repr=False)
    service_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_order_no: str | None = field(default=None, repr=False)
    yms_application_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    following_page_extension: str | None = field(default=None, repr=False)
    long_short_division_code: str | None = None
    schedules: tuple[LimousineSchedule, ...] = ()


@dataclass(frozen=True)
class LimousineSeat:
    direction_attribute_code: str | None = field(default=None, repr=False)
    other_attribute_code: str | None = field(default=None, repr=False)
    integrated_message: str | None = field(default=None, repr=False)
    integrated_message_code: str | None = field(default=None, repr=False)
    requested_attribute_code: str | None = field(default=None, repr=False)
    sale_possible_flag: str | None = None
    seat_no: str | None = field(default=None, repr=False)
    specification: str | None = field(default=None, repr=False)
    sequence_no: str | None = field(default=None, repr=False)
    visual_message_division_code: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    car_type_code: str | None = None
    car_no: str | None = field(default=None, repr=False)
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    seats: tuple[LimousineSeat, ...] = ()


@dataclass(frozen=True)
class LimousineRecommendedProduct:
    discount_amount: str | None = field(default=None, repr=False)
    discount_rate: str | None = field(default=None, repr=False)
    fare_amount_division_code: str | None = field(default=None, repr=False)
    goods_name: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price: str | None = field(default=None, repr=False)
    received_price_secondary: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleViewTrain:
    detour_via_popup: str | None = field(default=None, repr=False)
    elevator_damage_control: str | None = field(default=None, repr=False)
    arrival_date: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    arrival_consist_order: str | None = field(default=None, repr=False)
    arrival_run_order: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    car_type_name: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = field(default=None, repr=False)
    change_train_sequence: str | None = field(default=None, repr=False)
    connection_required_time: str | None = field(default=None, repr=False)
    connection_possible_flag: str | None = field(default=None, repr=False)
    connection_received_price: str | None = field(default=None, repr=False)
    delay_sale_flag: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    departure_consist_order: str | None = field(default=None, repr=False)
    departure_run_order: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    detour_flag: str | None = field(default=None, repr=False)
    detour_text: str | None = field(default=None, repr=False)
    expected_delay_hours: str | None = field(default=None, repr=False)
    expected_departure_delay_count: str | None = field(
        default=None,
        repr=False,
    )
    free_reservation_code: str | None = field(default=None, repr=False)
    free_car_count: str | None = field(default=None, repr=False)
    general_room_class_name: str | None = field(default=None, repr=False)
    general_reservation_code: str | None = field(default=None, repr=False)
    general_reservation_code_secondary: str | None = field(
        default=None,
        repr=False,
    )
    information_text: str | None = field(default=None, repr=False)
    journey_reservation_code: str | None = field(default=None, repr=False)
    journey_reservation_name: str | None = field(default=None, repr=False)
    nonstop_message: str | None = field(default=None, repr=False)
    nonstop_message_text: str | None = field(default=None, repr=False)
    popup_message: str | None = field(default=None, repr=False)
    received_amount: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price_secondary: str | None = field(default=None, repr=False)
    seat_map_flag: str | None = field(default=None, repr=False)
    reservation_possible_name: str | None = field(default=None, repr=False)
    run_date: str | None = field(default=None, repr=False)
    run_time: str | None = field(default=None, repr=False)
    seat_attribute_code: str | None = field(default=None, repr=False)
    smns_train_flag: str | None = field(default=None, repr=False)
    special_discount_rate: str | None = field(default=None, repr=False)
    special_room_class_name: str | None = field(default=None, repr=False)
    special_reservation_code: str | None = field(default=None, repr=False)
    special_reservation_code_secondary: str | None = field(
        default=None,
        repr=False,
    )
    special_reservation_possible_name: str | None = field(
        default=None,
        repr=False,
    )
    station_popup_message: str | None = field(default=None, repr=False)
    standing_reservation_code: str | None = field(default=None, repr=False)
    general_train_discount_rate: str | None = field(default=None, repr=False)
    origin_train_discount_rate: str | None = field(default=None, repr=False)
    train_class_code: str | None = field(default=None, repr=False)
    train_class_name: str | None = field(default=None, repr=False)
    service_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    use_time_care_content: str | None = field(default=None, repr=False)
    wait_reservation_flag: str | None = field(default=None, repr=False)
    yms_application_flag: str | None = field(default=None, repr=False)
    recommended_products: tuple[LimousineRecommendedProduct, ...] = ()
    total_passenger_count: int = 0
    goods_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleViewResponse(BaseKorailResponse):
    h_msg_txt: str | None = field(default=None, repr=False)
    next_ectb_train_no: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    notice_message: str | None = field(default=None, repr=False)
    next_preceding_train_no: str | None = field(default=None, repr=False)
    next_query_station_no: str | None = field(default=None, repr=False)
    result_count: str | None = None
    next_train_no: str | None = field(default=None, repr=False)
    merge_reservation_possible_flag: str | None = None
    schedules: tuple[LimousineScheduleViewTrain, ...] = ()
