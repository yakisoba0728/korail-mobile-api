from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .models import BaseKorailResponse


@dataclass(frozen=True)
class KorailPassengerCounts:
    """How many of each passenger type one reservation carries.

    The app's reservation request always transmits eight passenger rows,
    whatever the mix: ``w4/a.java:49-73`` fills rows 1..8 unconditionally, each
    row a count plus a fixed passenger-type code and discount-kind code, and
    ``OPsg`` is a ``LinkedHashMap`` (``OPsg.java:6``) so that build order is the
    wire order. The fields below are declared in that same row order:

    ==== ===================== ============ ============= =================
    row  field                 app bundle   ``txtPsgTpCd``  ``txtDiscKndCd``
    ==== ===================== ============ ============= =================
    1    ``adult``             ADULT        ``"1"``       ``"000"``
    2    ``teenager``          TEENAGER     ``"1"``       ``"P11"``
    3    ``child``             CHILD        ``"3"``       ``"000"``
    4    ``infant``            CHILD_ACCOMPANY ``"3"``    ``"321"``
    5    ``senior``            SENIOR       ``"1"``       ``"131"``
    6    ``severe_disability`` HIGH_DISABLE ``"1"``       ``"111"``
    7    ``mild_disability``   LOW_DISABLE  ``"1"``       ``"112"``
    8    ``guide_dog``         GUIDE_DOG    ``"1"``       ``"173"``
    ==== ===================== ============ ============= =================

    ``adult`` defaults to 1 and everything else to 0, so the default instance
    reproduces the one-adult mix this package sent before mixes existed.

    ``infant`` is 동반유아, the lap infant. It **is** counted in
    :attr:`total` and therefore in ``txtTotPsgCnt``: the app's own total is
    ``m5/c.java:330``/``:335``, a plain sum of all eight counters including
    ``CHILD_ACCOMPANY_COUNT``, and ``w4/a.java:49`` sends exactly that bundle
    value as ``txtTotPsgCnt``. The same is true of ``guide_dog``.

    No discount-card field accompanies a discounted row. ``OPsg`` declares one
    card field, ``txtCardNo_`` (``OPsg.java:7``), and the only writer of it is
    the separate N-card reservation request (``w4/a.java:101``, discount kind
    ``"153"``). The 경로/장애 rows here send a count and a discount code and
    nothing else, and neither ``txtCardCode_`` nor ``txtCardPw_`` -- which
    korail2 (``korail2.py:363-370``) and srtgo (``ktx.py:286-295``) send --
    exists anywhere in the decompiled app.

    Validation mirrors the app's picker: every count is a non-negative integer
    (each picker's range starts at 0, ``m5/c.java:111-118``), the total is at
    least one (the booking screen enables its search button only on
    ``TOTAL_PERSON_COUNT > 0``, e.g. ``OldMainBookingActivity.java:1023``), and
    the total is at most :data:`KORAIL_MAX_PASSENGERS_PER_RESERVATION`.

    Two further app-side rules are **not** enforced here, because they are
    warning dialogs on the picker rather than anything visible on the wire, and
    guessing at the server's version of them would reject mixes it may accept:
    a 동반유아 needs at least one 어른/청소년/경로/장애 to sit with
    (``m5/c.java:452-455``), and a 안내견 needs more 장애 passengers than dogs
    (``m5/c.java:458-465``). A mix breaking either is likely to be refused by
    the server.
    """

    adult: int = 1
    teenager: int = 0
    child: int = 0
    infant: int = 0
    senior: int = 0
    severe_disability: int = 0
    mild_disability: int = 0
    guide_dog: int = 0

    def __post_init__(self) -> None:
        for name in (
            "adult",
            "teenager",
            "child",
            "infant",
            "senior",
            "severe_disability",
            "mild_disability",
            "guide_dog",
        ):
            value = getattr(self, name)
            # type(...) is int, not isinstance: bool is an int subclass and
            # True is not a passenger count.
            if type(value) is not int or value < 0:
                raise ValueError(
                    f"{name} must be a non-negative integer"
                )
        total = self.total
        if total < 1:
            raise ValueError(
                "a reservation must carry at least one passenger"
            )
        if total > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
            raise ValueError(
                "a reservation carries at most "
                f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} passengers, "
                f"got {total}"
            )

    @property
    def total(self) -> int:
        """``txtTotPsgCnt``: every row summed, infants and guide dogs included.

        This is the app's ``TOTAL_PERSON_COUNT`` exactly (``m5/c.java:330``,
        and the identical ``getTotalCount()`` at ``:335``).
        """
        return (
            self.adult
            + self.teenager
            + self.child
            + self.infant
            + self.senior
            + self.severe_disability
            + self.mild_disability
            + self.guide_dog
        )


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
