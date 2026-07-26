from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .models import BaseKorailResponse, PhysicalSeat, SeatInventoryResponse


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
class KorailSeatAssignment:
    """One physical seat a seat-designated (``txtJobId="1103"``) hold asks for.

    A seat is identified by exactly the two values the seat-map reads already
    return, and by nothing else:

    * ``car_no`` is :attr:`~korail_mobile_api.SeatCar.car_no` from
      :meth:`KorailClient.get_seat_cars <korail_mobile_api.KorailClient.get_seat_cars>`
      (parsed from ``h_srcar_no``), i.e. the same number
      :meth:`~korail_mobile_api.KorailClient.get_seat_inventory` is then called
      with and echoes back as
      :attr:`~korail_mobile_api.SeatInventoryResponse.car_no`. The app sends the
      car currently on screen: ``SeatSearchActivity.java:678`` writes
      ``String.valueOf(F0())`` and ``F0()`` (``:269-271``) is
      ``SeatSearchRequest.getTxtSrcarNo()``, the car the seat map was asked for.
    * ``seat_no`` is :attr:`~korail_mobile_api.PhysicalSeat.seat_no` from
      :meth:`~korail_mobile_api.KorailClient.get_seat_inventory` (parsed from
      ``seat_no``), forwarded verbatim: ``SeatSearchActivity.java:680`` sends
      ``selectedSeatList.get(i).getSeat_no()``. It is deliberately NOT
      ``seat_spec`` -- that is the human label ("5A") the app renders at
      ``:894``, not the wire identifier.

    Both are taken as-is from an inventory read; this package never synthesises
    a seat identifier, and there is no format assumption beyond "printable
    ASCII, non-empty".
    """

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
        # type(...) is int, not isinstance: bool is an int subclass and True is
        # not a car number. Matches validate_seat_inventory_inputs' car_no rule
        # so a car that could be read cannot be rejected here and vice versa.
        if type(self.car_no) is not int or self.car_no < 1:
            raise ValueError("car_no must be a positive integer")
        seat_no = self.seat_no
        if (
            not isinstance(seat_no, str)
            or not seat_no
            or not seat_no.isascii()
            or any(character <= " " or character == "\x7f" for character in seat_no)
        ):
            raise ValueError(
                "seat_no must be a non-empty printable ASCII value taken from "
                "a seat-inventory read"
            )

    @classmethod
    def from_inventory(
        cls,
        inventory: SeatInventoryResponse,
        seat: PhysicalSeat,
    ) -> "KorailSeatAssignment":
        """Pair a :class:`~korail_mobile_api.SeatInventoryResponse` with one of its seats.

        ``inventory`` must be a seat-inventory read whose ``car_no`` the server
        echoed back (``scar_no``), and ``seat`` one of its
        :attr:`~korail_mobile_api.SeatInventoryResponse.seats` rows. This is the
        only constructor that needs no hand-copied identifiers, and it refuses a
        seat the read itself marked unsellable (``sale_psb_flg != "Y"``) --
        ``com/korail/talk/ui/seat/a.java`` only makes a ``"Y"`` seat tappable, so
        designating one the map would not let a user pick can only produce a
        server refusal, or worse a partial hold.
        """
        if type(inventory) is not SeatInventoryResponse:
            raise ValueError(
                "inventory must be an exact SeatInventoryResponse"
            )
        if type(seat) is not PhysicalSeat:
            raise ValueError("seat must be an exact PhysicalSeat")
        car_no = inventory.car_no
        if type(car_no) is not int:
            raise ValueError(
                "seat inventory did not echo a car number (scar_no); "
                "construct KorailSeatAssignment with an explicit car_no"
            )
        if seat not in inventory.seats:
            raise ValueError("seat does not belong to this seat inventory")
        if seat.sale_possible != "Y":
            raise ValueError(
                "seat is not marked sellable by the seat-inventory read "
                '(sale_psb_flg must be "Y")'
            )
        return cls(car_no=car_no, seat_no=seat.seat_no)


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


@dataclass(frozen=True)
class DiscountCardSectionRequest:
    """One 구간 of a 할인카드 being bought (``dcntCrdInfo.do`` ``jrnyInfo``).

    ``NCardReservationDao.NCardReservationRequest``
    (``dao/research/NCardReservationDao.java:74-108``) writes each section into
    a ``HashMap`` under an indexed key, and Retrofit flattens that map into the
    form (``ResearchService.java:68-70``). One entry per section, 1..3.

    ``jrnyTpCd`` is the app's own journey-type code and ``trnNo`` may be empty
    on a section the user has not pinned to a train; both are passed through
    rather than defaulted, because no v6.5.0 call site was found that fills
    this map, only the setters that would.
    """

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """The second registered user of an N카드 2인용 (``apdUsrInfo``).

    ``NCardReservationDao.java:66-72,122-124``. The app's own copy for a 1인용
    card is simply an empty map, which contributes no form fields at all.

    ``customer_no`` and ``phone`` are PII and are ``repr=False``; both are
    redacted in any preview.
    """

    customer_no: str = field(repr=False)
    name: str = field(repr=False)
    phone: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """Everything ``research.dcntCrdInfo.do`` needs to buy a 할인카드.

    ``w4/a.java:106-113`` builds the scalar half: the product
    (``dcntCrdKndMgNo``), the logged-in member number, ``vlidTrmStDt`` as the
    device's own today, and the trip count. ``vlidTrmStDt`` is therefore a
    caller argument here rather than an implicit ``date.today()`` — a payload
    builder with a clock in it cannot be tested for what it sends.
    """

    card_kind_management_no: str
    customer_no: str = field(repr=False)
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """The four-part ticket credential of a 할인카드, for 기간연장.

    ``TicketListActivity.java:1066-1074`` reads all four off the N카드 ticket's
    own row — ``h_orgtk_wct_no``, ``h_orgtk_ret_sale_dt``,
    ``h_orgtk_sale_sqno``, ``h_orgtk_ret_pwd`` — which is the same credential
    every other original-ticket operation uses. All four are ``repr=False``.
    """

    sale_window_no: str = field(repr=False)
    sale_date: str = field(repr=False)
    sale_sequence: str = field(repr=False)
    return_password: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """What ``research.dcntCrdInfo.do`` answers with.

    ``NCardReservationDao.NCardReservationResponse``
    (``dao/research/NCardReservationDao.java:127-174``).

    :attr:`lump_settlement_target_no` is the point of the call: the app hands
    it straight to the payment screen
    (``SectionNCardInquiryActivity.java:213-257``), so this response is an
    unpaid purchase awaiting settlement, not a completed one.
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``lumpStlTgtNo`` — the settlement target a payment would then charge.
    lump_settlement_target_no: str | None = field(default=None, repr=False)
    #: ``rcvdAmt`` — the amount that settlement would be for.
    received_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
