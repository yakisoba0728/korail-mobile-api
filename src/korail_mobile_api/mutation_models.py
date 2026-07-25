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


@dataclass(frozen=True)
class CardPayment:
    """Card settlement inputs for a reservation payment (settlement code 02).

    Mirrors the app/srtgo ``pay_with_card`` card fields. The PAN goes over the
    wire in the clear (no client-side encryption), so this must only ever carry
    a non-chargeable FAKE test card: the payment method refuses to send unless
    ``MutationConsent.fake_card_only`` is True. Sensitive fields are ``repr=False``.
    """

    card_number: str = field(repr=False)
    card_password: str = field(repr=False)  # first two digits of the card PIN
    card_expire: str = field(repr=False)  # YYMM
    birthday: str = field(repr=False)  # YYMMDD (personal auth) or biz no
    installment: str = "00"  # months; "00" = lump sum
    card_type: str = "J"  # hidAthnDvCd1: "J" personal / "S" corporate


@dataclass(frozen=True)
class PaidTicket:
    """The paid-ticket identity a refund (``refunds.RefundsRequest``) needs.

    Mirrors the app/srtgo ``refund`` inputs (``ktx.py:1077-1094``): the PNR plus
    the original-ticket sale window/date/sequence and return password, and the
    train number. These come from a settled ticket (e.g. a ticket-list row).
    Because a fake-card payment is always declined, no real paid ticket is
    produced in this package's test flow, so refund is exercised offline only.
    Sale-identity fields are ``repr=False``.
    """

    pnr_no: str = field(repr=False)
    sale_date: str = field(repr=False)  # h_orgtk_sale_dt
    sale_window_no: str = field(repr=False)  # h_orgtk_sale_wct_no
    sale_sequence: str = field(repr=False)  # h_orgtk_sale_sqno
    return_password: str = field(repr=False)  # h_orgtk_ret_pwd
    train_no: str = ""  # trnNo
