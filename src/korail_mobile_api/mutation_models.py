from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError
from .models import BaseKorailResponse, PhysicalSeat, SeatInventoryResponse


if TYPE_CHECKING:
    from .read_models import RefundTicketDetailResponse


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
    ) -> KorailSeatAssignment:
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
    #: ``hidIsmtMnthNum1`` — installment months. Lump sum is ``"0"``, ONE zero:
    #: ``K4/h.smali:44-52`` builds the INS_0 constant with ``const-string "0"``
    #: and every other value is unpadded too (``"2"``, ``"3"``, ``"12"``,
    #: ``"24"``). ``"00"`` occurs nowhere in the APK for this field.
    #:
    #: Re-checked against a SECOND, independent site on 2026-07-27, because the
    #: line above was carried on the strength of one citation:
    #: ``v4/a.java:288`` calls ``setHidIsmtMnthNum(i9, "0")`` with the literal
    #: inline, and ``:239`` defaults ``h hVar = h.INS_0`` before the dropdown
    #: switch assigns INS_2/INS_3/INS_4 for the other options. Two sites, one
    #: value, no padding.
    installment: str = "0"
    card_type: str = "J"  # hidAthnDvCd1: "J" personal / "S" corporate


@dataclass(frozen=True)
class PaidTicket:
    """The paid-ticket identity a refund (``refunds.RefundsRequest``) needs.

    Mirrors the app/srtgo ``refund`` inputs (``ktx.py:1077-1094``): the PNR, the
    sale date, the original-ticket sale window/sequence and return password, and
    the train number. These come from a settled ticket (e.g. a ticket-list row,
    or :meth:`~korail_mobile_api.client.KorailClient.get_refund_ticket_detail`).

    .. warning::
       :attr:`sale_date` is the CURRENT ticket's ``h_sale_dt``, not the original
       ticket's ``h_orgtk_ret_sale_dt``, even though the wire key it fills is
       spelled ``h_orgtk_sale_dt``. The app is explicit about this:
       ``TicketListActivity.java:965`` does
       ``setH_orgtk_sale_dt(detail.getH_sale_dt())`` while taking the window,
       sequence and password from the ``h_orgtk_*`` fields beside it, and
       ``ticketReturn/a.java:413`` agrees. The refund-commission request is the
       one that wants ``h_orgtk_ret_sale_dt`` (``ticketReturn/a.java:352``).
       On an unchanged ticket the two dates are equal and the mistake is
       invisible; on a ticket that was changed or reissued they differ and the
       four-part return identity no longer matches. Use
       :meth:`from_refund_detail` instead of assembling this by hand.

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
    #: The CURRENT ticket's ``h_sale_dt``. Fills the wire key
    #: ``h_orgtk_sale_dt`` -- see the warning above; these are not the same
    #: thing on a reissued ticket.
    sale_date: str = field(repr=False)
    sale_window_no: str = field(repr=False)  # h_orgtk_wct_no -> h_orgtk_sale_wct_no
    sale_sequence: str = field(repr=False)  # h_orgtk_sale_sqno
    return_password: str = field(repr=False)  # h_orgtk_ret_pwd
    train_no: str = ""  # trnNo

    @classmethod
    def from_refund_detail(
        cls,
        detail: RefundTicketDetailResponse,
        *,
        train_no: str = "",
    ) -> PaidTicket:
        """Build the refund identity from a ticket detail, the way the app does.

        Takes the sale date from ``h_sale_dt`` and the window, sequence and
        password from the ``h_orgtk_*`` trio, matching
        ``TicketListActivity.java:964-968`` field for field. Prefer this over
        constructing :class:`PaidTicket` directly: the wire key for the sale
        date is spelled ``h_orgtk_sale_dt``, which invites reusing
        :attr:`~RefundTicketDetailResponse.original_sale_date`, and that is the
        one value here that must NOT come from the ``h_orgtk_*`` group.

        Raises :class:`KorailProtocolError` if any of the four identity parts is
        missing, rather than letting a refund go out with a blank in it.
        """
        parts = {
            "pnr_no": detail.pnr_no,
            "sale_date": detail.sale_date,
            "sale_window_no": detail.original_window_no,
            "sale_sequence": detail.original_sale_sequence,
            "return_password": detail.original_return_password,
        }
        missing = [name for name, value in parts.items() if not value]
        if missing:
            raise KorailProtocolError(
                "KORAIL refund identity is incomplete; the ticket detail is "
                f"missing {', '.join(sorted(missing))}"
            )
        return cls(train_no=train_no, **parts)  # type: ignore[arg-type]


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


@dataclass(frozen=True)
class PriceRecalculationRow:
    """One passenger row of a 운임 재계산 request.

    The app's ``DiscountPriceParams``
    (``network/data/certification/DiscountPriceParams.java``) — a flat
    six-field POJO, one instance per seat of the held journey. The whole
    request is an array of these, which ``a6/C1042B.java:275-283`` fans out
    into the six parallel ``List`` ``@Field``s the DAO declares. The six lists
    are therefore INDEX-ALIGNED, and this class is the row they zip back into.

    The first three fields are copied straight off the held seat, and
    :attr:`raw_room_class_code` is not a choice the caller makes:
    ``S4/D.java:176-190`` (``makeDiscountParams``) reads ``h_psg_tp_cd`` and
    ``h_psrm_cl_cd`` off ``seat_infos.seat_info[i]`` verbatim. Read them from
    :class:`~korail_mobile_api.read_models.ReservationSeatDetail` for the same
    PNR.

    The last three carry the discount being APPLIED:

    * :attr:`requested_discount_code` — ``hidDcntKndCd``, the discount kind
      the payment screen just selected for this passenger. ``""`` when none.
      Observed values: ``"151"``/``"152"`` (쿠폰·국가유공자 본인),
      ``"171"``/``"172"`` (장애인·유공자 보호자), ``"321"`` (동반유아),
      ``"401"`` (지연할인), ``"402"`` (국회의원).
    * :attr:`certificate_no` — ``hidDscpNo``, the coupon or certificate number
      that backs it (``h_cpn_no``, or the four-part 지연증명 return number
      ``H4/a.getReturnNumber``). ``""`` when the discount needs none.
    * :attr:`family_sequence_no` — ``hidFmlyNo``, the 다자녀 family member's
      ``fmlySqno``. ``""`` for every discount except that one; only
      ``a6/C1041A.java:75`` ever writes it non-empty.

    Every value is a plain string and none may be ``None``: Retrofit SKIPS a
    null element when it flattens the list (``RequestBuilder.smali:1559-1571``
    jumps back to the loop head on ``if-eqz v5``), which would shorten one key
    relative to the other five and silently re-pair every row after it.
    """

    #: ``psg_tp_dv_cd`` ← the seat's ``h_psg_tp_cd``.
    passenger_type_code: str
    #: ``psrm_cl_cd`` ← the seat's ``h_psrm_cl_cd``.
    room_class_code: str
    #: ``dcnt_knd_cd1`` ← the seat's EXISTING ``h_dcnt_knd_cd1``, i.e. the
    #: discount the hold already carries. ``makeDiscountParams`` overwrites it
    #: in exactly two cases, both enforced by the builder: ``"432"`` for a
    #: 군장병 row, and ``"000"`` when the applied discount is an integrated
    #: 국가유공자 one.
    discount_kind_code: str
    #: ``hidDcntKndCd`` — the discount being applied now.
    requested_discount_code: str = ""
    #: ``hidDscpNo`` — a spendable coupon/certificate number. Redacted.
    certificate_no: str = field(default="", repr=False)
    #: ``hidFmlyNo`` — 다자녀 family member sequence. Redacted.
    family_sequence_no: str = field(default="", repr=False)


@dataclass(frozen=True)
class PriceRecalculationRequest:
    """A 운임 재계산 for one held PNR.

    ``a6/C1042B.java:265-296`` (``k2()``) builds exactly this: the PNR, the
    fixed job id ``"1101"``, a row count, the six lists, and — only when the
    account is a non-member — ``hiduserYn="N"`` plus the non-member number.

    :attr:`rows` must carry one row per seat of the journey being re-priced,
    in seat order, because ``txtPsgGridcnt`` is derived from its length and
    the server pairs the six repeated keys by position.
    """

    pnr_no: str = field(repr=False)
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: ``hidCustNo``. Set ONLY for a non-member session, which is the only
    #: case in which ``k2()`` writes either this or ``hiduserYn``
    #: (``a6/C1042B.java:290-293``). ``None`` for a member, and then neither
    #: field is transmitted at all — Retrofit omits a null ``@Field``
    #: (``RequestBuilder.smali:1531`` branches past ``addField`` on a null
    #: value), so a member's form genuinely has twelve keys, not fourteen.
    non_member_no: str | None = field(default=None, repr=False)




@dataclass(frozen=True)
class CartAddRequest:
    """Add a held reservation's PNR to the 장바구니 (cart).

    ``cart.addCartList`` (``CartService.java:11-13``) takes exactly one
    request field beyond the common three: ``hidPnrNo``. The DAO
    (``AddCartDao.java:9-24``, request class ``AddCartDao$AddCartRequest``)
    carries the same single field, confirmed against
    ``AddCartDao$AddCartRequest.smali`` (``hidPnrNo:Ljava/lang/String;`` and
    the matching ``@Field("hidPnrNo")`` annotation on
    ``CartService.smali``'s ``addCart`` method).

    ``pnr_no`` is a ticket identifier and is ``repr=False``; it is also
    already registered in :data:`~korail_mobile_api.redaction.SENSITIVE_KEYS`
    under its wire name ``hidPnrNo``, so a :class:`~korail_mobile_api.consent.MutationPreview`
    of this request redacts it automatically.
    """

    pnr_no: str = field(repr=False)
