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
    #: ``h_pay_limit_msg``. Declared on the app's ``ReservationResponse``
    #: (``:22``, getter ``:529``) but read by NO app screen, and a live hold
    #: returns it empty. It is NOT the payment deadline — use the three fields
    #: below, which are what the app actually renders.
    payment_deadline_message: str | None = field(default=None, repr=False)
    #: ``h_ntisu_lmt`` — the server's own prose deadline, e.g. "…까지 미결제시
    #: 승차권이 자동으로 취소됩니다."
    payment_deadline_notice: str | None = field(default=None, repr=False)
    #: ``h_ntisu_lmt_dt`` / ``h_ntisu_lmt_tm`` — the structured deadline the app
    #: concatenates and parses as ``yyyyMMddHHmmss`` to show when an unpaid hold
    #: self-cancels (``S4/C0816p.java:64-70``,
    #: ``ReservedTicketActivity.java:356,365``).
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    total_fare: str | None = None
    #: ``h_tot_prc`` — the DISPLAY total. ``PaymentActivity.java:174`` assigns it
    #: to ``mTotPrc``, which is only ever read back by ``getmTotPrc()``
    #: (``:497``) for the UI. It is NOT the amount the app settles.
    total_price: str | None = None
    #: The amount the app actually collects (``hidMnsStlAmt1``): the app's
    #: ``getReceivedAmount()`` (``PaymentActivity.java:186-199``, sent via
    #: ``AbstractC1269e.java:406`` → ``V4/a.java:27``). Sourced from
    #: ``h_tot_rcvd_amt`` when the hold response carries it, else summed from the
    #: per-seat ``h_rcvd_amt`` rows the way the app computes it.
    received_amount: str | None = None
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
    wire in the clear (no client-side encryption), so which kind of card this
    may carry is decided by the consent, never by this type:

    * By default it can only be a non-chargeable FAKE test card.
      :meth:`~korail_mobile_api.client.KorailClient.pay_with_fake_card` refuses
      to send unless ``MutationConsent.fake_card_only`` is True, which is the
      default, and it accepts nothing else.
    * A REAL, CHARGEABLE card is possible only through the separate
      :meth:`~korail_mobile_api.client.KorailClient.pay_with_card`, and only on
      a consent that explicitly sets ``real_card_acknowledged=True`` together
      with ``fake_card_only=False``. That combination has to be written on
      purpose; nothing infers it, and the transmit gate refuses a consent that
      states neither claim or both.

    Sensitive fields are ``repr=False``.
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
    train number. These come from a settled ticket (e.g. a ticket-list row, or
    :meth:`~korail_mobile_api.client.KorailClient.get_refund_ticket_detail`).

    A fake-card payment is always declined and so never produces one of these;
    for as long as that was the only payment path, refund could be exercised
    offline only. :meth:`~korail_mobile_api.client.KorailClient.pay_with_card`
    changes that — an explicitly acknowledged real charge does settle a ticket,
    and that ticket is refundable. The refund send path itself is unchanged and
    still has no live-verified success envelope; call
    :meth:`~korail_mobile_api.client.KorailClient.get_refund_commission` first to
    see the refundable amount and the fee before issuing one.

    Sale-identity fields are ``repr=False``.
    """

    pnr_no: str = field(repr=False)
    sale_date: str = field(repr=False)  # h_orgtk_sale_dt
    sale_window_no: str = field(repr=False)  # h_orgtk_sale_wct_no
    sale_sequence: str = field(repr=False)  # h_orgtk_sale_sqno
    return_password: str = field(repr=False)  # h_orgtk_ret_pwd
    train_no: str = ""  # trnNo
