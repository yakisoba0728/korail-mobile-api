# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 연계 조회의 요청 질의와 응답 타입.

``lmu.scdlQry.do``(운행 스케줄)와 ``lms.TResidualSeatsResearch.do``(좌석 재고)가
씁니다. ``seatMovie.LimousineScheduleView``(좌석이동 화면의 열차 목록)는 7.0.6
앱에서 사라져 클라이언트가 더는 보내지 않습니다. 그 질의·응답 타입은 저장해 둔 6.5.0
응답을 해석할 수 있도록 남겨 두었습니다(``docs/7.0.6-removals.md``).

``*Query`` 두 클래스는 얼어붙은 데이터클래스이고 ``__post_init__`` 에서 형식을
검사합니다. 둘 다 역**코드**(4자리)로 역을 받습니다.
``LimousineScheduleQuery``·``LimousineSeatInventoryQuery`` 는 운행/열차 식별자를
그대로 보여 주고 ``room_class_code``(좌석 재고는 ``car_no`` 도)만 가립니다.

운행 스케줄은 2026-09-16 실서버에서 확인했습니다 — 광명역→인천공항T1 42편을
파싱했습니다(``docs/7.0.6-live-verification.md``). 좌석 재고와 좌석이동 목록은
라이브 미검증이며 요청과 응답 모양이 APK 선언에서 나왔습니다.
"""
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


def _non_empty_ascii(value: object, name: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if allow_empty and value == "":
        return
    if not value or not value.isascii():
        raise ValueError(f"{name} must be a non-empty ASCII string")


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
    """``lmu.scdlQry.do`` 운행 스케줄 조회의 입력."""
    departure_date: str
    departure_station_code: str
    arrival_station_code: str
    service_code: str
    room_class_code: str = field(repr=False)
    departure_time: str
    train_no: str
    seat_attribute_code: str
    reservation_sale_division_code: str

    def __post_init__(self) -> None:
        # The exact digit-length each field must have on the wire is the
        # server's format check to make, not this client's -- lmu.scdlQry.do
        # forwards every one of these straight into the form
        # (build_limousine_schedule_form) with nothing here branching on a
        # specific length. Only "is this a real ASCII string" stays.
        text_fields: tuple[tuple[str, str, bool], ...] = (
            (self.departure_date, "departure_date", False),
            (self.departure_station_code, "departure_station_code", False),
            (self.arrival_station_code, "arrival_station_code", False),
            (self.service_code, "service_code", False),
            (self.room_class_code, "room_class_code", False),
            (self.departure_time, "departure_time", False),
            (self.train_no, "train_no", True),
            (self.seat_attribute_code, "seat_attribute_code", True),
        )
        for value, name, allow_empty in text_fields:
            _non_empty_ascii(value, name, allow_empty=allow_empty)
        _required_text(
            self.reservation_sale_division_code,
            "reservation_sale_division_code",
        )


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    """``lms.TResidualSeatsResearch.do`` 좌석 재고 조회의 입력."""
    train_class_code: str
    service_code: str
    run_date: str
    train_no: str
    car_no: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_station_code: str
    arrival_station_code: str
    seat_attribute_code: str
    departure_run_order: str
    arrival_run_order: str
    passenger_count: int
    product_no: str
    is_arrow: bool

    def __post_init__(self) -> None:
        # Same reasoning as LimousineScheduleQuery.__post_init__: exact wire
        # length is lms.TResidualSeatsResearch.do's format check to make, not
        # this client's -- build_limousine_seat_inventory_form never branches
        # on a specific length either.
        text_fields: tuple[tuple[str, str, bool], ...] = (
            (self.train_class_code, "train_class_code", False),
            (self.service_code, "service_code", False),
            (self.run_date, "run_date", False),
            (self.train_no, "train_no", False),
            (self.car_no, "car_no", False),
            (self.room_class_code, "room_class_code", False),
            (self.departure_station_code, "departure_station_code", False),
            (self.arrival_station_code, "arrival_station_code", False),
            (self.seat_attribute_code, "seat_attribute_code", True),
            (self.departure_run_order, "departure_run_order", False),
            (self.arrival_run_order, "arrival_run_order", False),
        )
        for value, name, allow_empty in text_fields:
            _non_empty_ascii(value, name, allow_empty=allow_empty)
        _passenger_count(
            self.passenger_count,
            "passenger_count",
            allow_zero=False,
        )
        _optional_text(self.product_no, "product_no")
        _boolean(self.is_arrow, "is_arrow")


@dataclass(frozen=True)
class LimousineSchedule:
    """운행 스케줄 조회 결과의 한 편."""
    arrival_date: str | None = None
    arrival_station_code: str | None = None
    arrival_run_order: str | None = None
    arrival_time: str | None = None
    transfer_division_code: str | None = None
    departure_date: str | None = None
    departure_station_code: str | None = None
    departure_run_order: str | None = None
    departure_time: str | None = None
    general_remaining_seat_count: str | None = None
    delay_minutes: str | None = None
    free_remaining_seat_count: str | None = None
    standing_remaining_seat_count: str | None = None
    run_date: str | None = None
    special_remaining_seat_count: str | None = None
    train_class_code: str | None = None
    service_code: str | None = None
    train_no: str | None = None
    train_order_no: str | None = None
    yms_application_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class LimousineScheduleResponse(BaseKorailResponse):
    """``lmu.scdlQry.do`` 의 응답."""
    following_page_extension: str | None = None
    long_short_division_code: str | None = None
    schedules: tuple[LimousineSchedule, ...] = ()


@dataclass(frozen=True)
class LimousineSeat:
    """좌석표의 좌석 한 자리."""
    direction_attribute_code: str | None = None
    other_attribute_code: str | None = None
    integrated_message: str | None = None
    integrated_message_code: str | None = None
    requested_attribute_code: str | None = None
    sale_possible_flag: str | None = None
    seat_no: str | None = field(default=None, repr=False)
    specification: str | None = None
    sequence_no: str | None = None
    visual_message_division_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    """``lms.TResidualSeatsResearch.do`` 의 응답 — 한 호차의 좌석표."""
    car_type_code: str | None = None
    car_no: str | None = field(default=None, repr=False)
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    seats: tuple[LimousineSeat, ...] = ()


@dataclass(frozen=True)
class LimousineRecommendedProduct:
    """열차 행에 딸려 오는 추천 상품 한 건."""
    discount_amount: str | None = field(default=None, repr=False)
    discount_rate: str | None = field(default=None, repr=False)
    fare_amount_division_code: str | None = field(default=None, repr=False)
    goods_name: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price: str | None = field(default=None, repr=False)
    received_price_secondary: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class LimousineScheduleViewTrain:
    """좌석이동 화면이 쓰는 열차 목록의 한 행(6.5.0 응답 해석용)."""
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class LimousineScheduleViewResponse(BaseKorailResponse):
    """``seatMovie.LimousineScheduleView`` 의 응답(6.5.0 응답 해석용)."""
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
