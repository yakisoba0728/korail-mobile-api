from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


@dataclass(frozen=True)
class ReservationJourney:
    journey_sequence: str | None = None
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    departure_station_code: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationHoldResponse(BaseKorailResponse):
    pnr_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    window_no: str | None = field(default=None, repr=False)
    temporary_job_sequence_1: str | None = field(default=None, repr=False)
    temporary_job_sequence_2: str | None = field(default=None, repr=False)
    payment_flag: str | None = None
    payment_message: str | None = field(default=None, repr=False)
    payment_deadline_message: str | None = field(default=None, repr=False)
    total_fare: str | None = None
    total_price: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    certificate_password: str | None = field(default=None, repr=False)
    coupon_no: str | None = field(default=None, repr=False)
    management_close_date: str | None = None
    management_start_date: str | None = None
    ticket_return_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    image_ticket_flag: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
