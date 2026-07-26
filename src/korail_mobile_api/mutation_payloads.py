from __future__ import annotations

import re
from collections.abc import Sequence

from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KORAIL_MAX_DISCOUNT_CARD_SECTIONS,
    KORAIL_MAX_JOURNEY_LEGS,
    KORAIL_STANDBY_WAIT_FLAG,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
    KorailReservationJobType,
    KorailSeatClass,
)
from .errors import KorailProtocolError
from .models import TrainSummary
from .mutation_models import (
    DiscountCardAdditionalUser,
    DiscountCardPurchaseRequest,
    DiscountCardSectionRequest,
    DiscountCardTicket,
    CardPayment,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    ReservationHoldResponse,
)


_DATE_RE = re.compile(r"[0-9]{8}")
_TIME_RE = re.compile(r"[0-9]{6}")
_DIGITS_RE = re.compile(r"[0-9]+")


def _required_digits(value: str | None, *, field: str) -> str:
    if not isinstance(value, str) or _DIGITS_RE.fullmatch(value) is None:
        raise KorailProtocolError(
            f"KORAIL reservation train field {field} must be decimal digits"
        )
    return value


def _required_pattern(
    value: str | None,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise KorailProtocolError(
            f"KORAIL reservation train field {field} has an invalid shape"
        )
    return value


def _common_fields(config: KorailConfig) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }


# The eight passenger rows the app's reservation request ALWAYS carries, in the
# order w4/a.java:49-73 writes them into OPsg. OPsg is a LinkedHashMap
# (OPsg.java:6) whose keys are "txtCompaCnt"/"txtPsgTpCd"/"txtDiscKndCd" plus the
# row number (OPsg.java:8-10, 17-27), so the build order below IS the wire order.
# Only the count varies with the mix; the type and discount codes are fixed per
# row, which is why a row that carries nobody still goes out as "0".
_PASSENGER_ROWS: tuple[tuple[str, str, str], ...] = (
    ("adult", "1", "000"),  # 어른
    ("teenager", "1", "P11"),  # 청소년
    ("child", "3", "000"),  # 어린이
    ("infant", "3", "321"),  # 동반유아
    ("senior", "1", "131"),  # 경로
    ("severe_disability", "1", "111"),  # 1~3급 장애
    ("mild_disability", "1", "112"),  # 4~6급 장애
    ("guide_dog", "1", "173"),  # 안내견
)


def _validated_seat_assignments(
    seats: Sequence[KorailSeatAssignment] | None,
    *,
    job_type: KorailReservationJobType,
    passenger_total: int,
) -> tuple[KorailSeatAssignment, ...]:
    """Check one leg's designated-seat list against the job type and the mix.

    A seat list belongs to ``"1103"`` and to nothing else: the app switches the
    job id to ``"1103"`` in the same three lines that install the ``OSrcar``
    map (``C5/a.java:143-146``), and clears that map whenever it rebuilds an
    ordinary ``"1101"`` journey (``C5/a.java:118``).

    The count rule is the app's own: ``SeatSearchActivity.java:902`` enables
    "선택완료" only while ``selectedSeatCount == G0()``, and ``G0()``
    (``:273-278``) is the request's ``txtTotPsgCnt``. A short list is refused
    here, before anything is sent, because the server would otherwise be asked
    to seat N passengers in fewer than N seats. The rule is per leg because the
    app's seat picker is per leg: ``C5/a.java:120-133`` launches
    ``SeatSearchActivity`` once per journey index and passes that index on as
    the ``TRAIN_INDEX`` extra, while the passenger total it compares against
    (``SeatSearchActivity.java:273-278``) is the whole booking's.
    """
    if job_type is not KorailReservationJobType.SEAT_DESIGNATED:
        if seats:
            raise KorailProtocolError(
                "KORAIL designated seats belong to a seat-designated "
                f'reservation (txtJobId "1103"), not "{job_type.value}"'
            )
        return ()
    if seats is None or isinstance(seats, (str, bytes)):
        raise KorailProtocolError(
            "KORAIL seat-designated reservation requires a sequence of "
            "KorailSeatAssignment"
        )
    assignments = tuple(seats)
    for assignment in assignments:
        if type(assignment) is not KorailSeatAssignment:
            raise KorailProtocolError(
                "KORAIL seat-designated reservation requires exact "
                "KorailSeatAssignment values"
            )
    if len(assignments) != passenger_total:
        raise KorailProtocolError(
            "KORAIL seat-designated reservation needs exactly one seat per "
            f"passenger: {passenger_total} passenger(s), "
            f"{len(assignments)} seat(s)"
        )
    identities = {(item.car_no, item.seat_no) for item in assignments}
    if len(identities) != len(assignments):
        raise KorailProtocolError(
            "KORAIL seat-designated reservation cannot book the same seat "
            "twice"
        )
    return assignments


def build_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[KorailSeatAssignment] | None = None,
) -> dict[str, str]:
    """Build the reservation-hold form for a passenger mix and a cabin class.

    ``passengers`` defaults to :class:`KorailPassengerCounts`'s own default of
    one adult and ``seat_class`` to
    :attr:`KorailSeatClass.GENERAL <korail_mobile_api.KorailSeatClass.GENERAL>`,
    so calling this with neither reproduces the exact form this package sent
    before mixes existed -- see
    :func:`build_single_adult_reservation_form`.

    ``job_type`` selects which of the booking screen's three actions is being
    performed and defaults to
    :attr:`KorailReservationJobType.IMMEDIATE <korail_mobile_api.KorailReservationJobType.IMMEDIATE>`
    (``txtJobId="1101"``), the only one that existed before:

    * :attr:`~korail_mobile_api.KorailReservationJobType.SEAT_DESIGNATED`
      (``"1103"``) additionally requires ``seats``, one
      :class:`~korail_mobile_api.KorailSeatAssignment` per passenger, and adds
      the ``OSrcar`` keys described below.
    * :attr:`~korail_mobile_api.KorailReservationJobType.STANDBY` (``"1102"``)
      is 예약대기. It does not require an available seat -- the point is that
      there is none -- but it does require the train row's own
      standby-eligibility flag and the 일반실 cabin, and it computes
      ``txtStndFlg`` the way the app does instead of pinning ``"N"``.

    ``seats`` is accepted only for the seat-designated job. Its keys are
    ``OSrcar``'s (``OSrcar.java:6-11``), a ``@FieldMap`` appended after the
    journey keys (``CertificationService.java:52-54``): ``txtSrcarCnt`` first,
    then ``txtSrcarNo{i}``/``txtSeatNo{i}`` for ``i`` counting from **1**
    (``SeatSearchActivity.java:675-683`` -- ``setSrcarCnt(this.f29973o + 1, …)``
    picks the *journey* index, which is 1 for a direct train, and the loop's
    ``i11`` starts at 1). ``txtSrcarCnt`` is the number of **seats**, not cars:
    it is ``String.valueOf(selectedSeatList.size())``.

    This books **one** journey: ``txtJrnyCnt="1"`` and a single journey block,
    because ``C5/a.java:55`` derives the count from the length of the train
    array it is handed. For a 환승 itinerary's two legs use
    :func:`build_transfer_reservation_form`, which is the same builder with a
    longer array.

    Only the single-adult, general-class, ``"1101"`` shape has ever been sent to
    the live server. Multi-passenger and 특실 forms, and both non-default job
    types, are built from the app's own request builder but are NOT
    live-verified.
    """
    return _build_journey_reservation_form(
        config,
        (train,),
        passengers=passengers,
        seat_classes=(seat_class,),
        job_type=job_type,
        leg_seats=None if seats is None else (seats,),
    )


def build_transfer_reservation_form(
    config: KorailConfig,
    legs: Sequence[TrainSummary],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (
        KorailSeatClass.GENERAL
    ),
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
) -> dict[str, str]:
    """Build the reservation-hold form for a 환승 itinerary -- two legs, one PNR.

    This is :func:`build_reservation_form` with the journey block repeated. The
    app has one builder for both cases (``C5/a.java:52-119``, ``N0``) and it is
    a loop over the train array it was handed, so the leg count alone decides
    the field set:

    * ``txtJrnyCnt`` is ``(length == 1 ? DIRECT_SQ_NO : TRANSFER_SQ_NO)`` --
      ``C5/a.java:55``. It is derived from the array length, not from a flag,
      which is why a direct booking cannot be made to emit a transfer form by
      setting something.
    * the loop writes at ``i10 = i9 + 1``, so journey indices are **1-based**
      (``C5/a.java:57-77``).
    * ``txtJrnyTpCd{i}`` is ``(length == 1 ? DIRECT : TRANSFER)`` -- also keyed
      on the LENGTH even though it is written inside the loop
      (``C5/a.java:60``, re-read as ``smali/C5/a.smali:306-338``), so **both**
      legs of a transfer carry ``"14"``.
    * ``txtJrnySqno{i}`` is keyed on the loop INDEX -- ``(i == 0 ?
      DIRECT_SQ_NO : TRANSFER_SQ_NO)`` fed through ``O.getSequenceNo``, which
      is ``DecimalFormat("000")`` (``S4/O.java:19-21``, ``S4/N.java:32-38``) --
      so leg 1 sends ``"001"`` and leg 2 ``"002"``.

    ``legs`` must hold exactly
    :data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS` (2) trains, in boarding
    order; :attr:`TransferItinerary.legs
    <korail_mobile_api.TransferItinerary.legs>` produces one. Any other count is
    refused -- see :data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS` for why
    the form has no third journey and what a third leg would overwrite.

    What composes, and what does not:

    * **passenger mix** -- composes, and is per booking rather than per leg.
      ``OPsg`` is built once on the booking-options screen (``w4/a.java:47-74``)
      before any itinerary is chosen, and ``N0`` never touches it.
    * **cabin class** -- composes, and is genuinely **per leg**. ``C5/a.java:59``
      reads ``U4.a.getSelectSeatTypeCode(D0(), i9)`` with the leg index and
      ``:97`` writes it as ``txtPsrmClCd{i}``, so 일반실 on one leg and 특실 on
      the other is a shape the app can produce. Pass either one
      :class:`~korail_mobile_api.KorailSeatClass` for both legs or a sequence of
      one per leg.
    * **seat designation** (``"1103"``) -- composes, and is also per leg.
      ``C5/a.java:120-133`` launches the seat picker once per journey index and
      passes it as ``TRAIN_INDEX``; ``SeatSearchActivity.java:675-682`` then
      writes ``setSrcarCnt(TRAIN_INDEX + 1, …)``, and ``OSrcar.java:21-30``
      spells journey 2 as ``txtSrcarCnt1``/``txtSrcarNo1_{n}``/``txtSeatNo1_{n}``.
      Pass ``seats`` as one sequence per leg, each holding one
      :class:`~korail_mobile_api.KorailSeatAssignment` per passenger.
    * **standby** (``"1102"``, 예약대기) -- does **not** compose, and this
      builder refuses it. Two independent gates in the app say so. ``G0()``, the
      standby-eligibility check, opens with ``if (!isDirect) return false``
      (``a5/k.java:120-127``), so the 예약대기 button is never enabled on a
      transfer result (``a5/u.java:369-371`` feeds that into the button state at
      ``:401-404``); and the only ``setJobId("1102")`` in the app is
      ``DirectInquiryActivity.java:434``, in a branch of an ``onClick``
      that ``TransferInquiryActivity`` overrides and never reaches.

    NOT live-verified: no transfer form built here has been sent to KORAIL.
    """
    return _build_journey_reservation_form(
        config,
        legs,
        passengers=passengers,
        seat_classes=seat_classes,
        job_type=job_type,
        leg_seats=seats,
        require_legs=KORAIL_MAX_JOURNEY_LEGS,
    )


# The app's own key-selection methods, which are the reason a third leg is
# impossible rather than merely unsupported: every one of them is a two-way
# `i == 1 ? … : …`, so a journey-3 write lands on the journey-2 key.
def _seat_attribute_key(journey: int) -> str:
    """``OSeat.setSeatAttCd4`` -- OSeat.java:32-35."""
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    """``OSrcar.setSrcarCnt`` -- OSrcar.java:21-23."""
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    """``OSrcar.setSrcarNo`` -- OSrcar.java:25-30."""
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    """``OSrcar.setSeatNo`` -- OSrcar.java:14-19."""
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


def _validated_legs(
    legs: Sequence[TrainSummary],
    *,
    require: int | None,
) -> tuple[TrainSummary, ...]:
    """The legs of one reservation, checked for type and count.

    ``require`` is the exact count a caller demands (two, for a 환승 booking) or
    ``None`` for "whatever the app supports". The single-leg builder passes
    ``None`` and keeps its own rejection message, so a caller who handed
    ``build_reservation_form`` something that is not a ``TrainSummary`` reads
    the same sentence it has always read.
    """
    if isinstance(legs, (str, bytes)) or not isinstance(legs, Sequence):
        raise KorailProtocolError(
            "KORAIL reservation requires a sequence of legs"
        )
    resolved = tuple(legs)
    for leg in resolved:
        if type(leg) is not TrainSummary:
            raise KorailProtocolError(
                "KORAIL reservation requires an exact TrainSummary"
            )
    if require is not None and len(resolved) != require:
        raise KorailProtocolError(
            f"KORAIL 환승 reservation books exactly {require} legs, got "
            f"{len(resolved)}: the reservation form has no journey-{require + 1} "
            "spelling at all (OSeat.java:32-35 and OSrcar.java:21-30 both split "
            'on "journey 1 or not"), so a further leg would overwrite leg '
            f"{require} rather than be added"
        )
    if not resolved or len(resolved) > KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            "KORAIL reservation carries between 1 and "
            f"{KORAIL_MAX_JOURNEY_LEGS} legs, got {len(resolved)}"
        )
    return resolved


def _validated_seat_classes(
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass,
    *,
    leg_count: int,
) -> tuple[KorailSeatClass, ...]:
    """One cabin per leg, from either one value or a per-leg sequence.

    Per leg because the app is per leg: ``C5/a.java:59`` reads the cabin with
    ``U4.a.getSelectSeatTypeCode(D0(), i9)``, the leg index, and ``:97`` writes
    ``txtPsrmClCd{i}`` from it.
    """
    if isinstance(seat_classes, (str, KorailSeatClass)):
        candidates: tuple[object, ...] = (seat_classes,) * leg_count
    elif isinstance(seat_classes, Sequence) and not isinstance(
        seat_classes,
        bytes,
    ):
        candidates = tuple(seat_classes)
        if len(candidates) == 1:
            candidates = candidates * leg_count
    else:
        raise KorailProtocolError(
            "KORAIL reservation seat class must be a KorailSeatClass or a "
            "sequence of one per leg"
        )
    if len(candidates) != leg_count:
        raise KorailProtocolError(
            f"KORAIL reservation needs one cabin class per leg: {leg_count} "
            f"leg(s), {len(candidates)} class(es)"
        )
    resolved: list[KorailSeatClass] = []
    for candidate in candidates:
        try:
            resolved.append(KorailSeatClass(candidate))
        except ValueError:
            raise KorailProtocolError(
                'KORAIL reservation seat class must be "1" (일반실) or "2" '
                "(특실)"
            ) from None
    return tuple(resolved)


def _validated_leg_seats(
    leg_seats: Sequence[Sequence[KorailSeatAssignment]] | None,
    *,
    leg_count: int,
    job_type: KorailReservationJobType,
    passenger_total: int,
) -> tuple[tuple[KorailSeatAssignment, ...], ...]:
    if leg_seats is None:
        per_leg: tuple[Sequence[KorailSeatAssignment] | None, ...] = (
            (None,) * leg_count
        )
    elif isinstance(leg_seats, (str, bytes)) or not isinstance(
        leg_seats,
        Sequence,
    ):
        raise KorailProtocolError(
            "KORAIL seat-designated reservation requires one sequence of "
            "KorailSeatAssignment per leg"
        )
    else:
        per_leg = tuple(leg_seats)
        if len(per_leg) != leg_count:
            raise KorailProtocolError(
                "KORAIL seat-designated reservation needs one seat list per "
                f"leg: {leg_count} leg(s), {len(per_leg)} list(s)"
            )
    return tuple(
        _validated_seat_assignments(
            seats,
            job_type=job_type,
            passenger_total=passenger_total,
        )
        for seats in per_leg
    )


def _build_journey_reservation_form(
    config: KorailConfig,
    legs: Sequence[TrainSummary],
    *,
    passengers: KorailPassengerCounts | None,
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass,
    job_type: KorailReservationJobType,
    leg_seats: Sequence[Sequence[KorailSeatAssignment]] | None,
    require_legs: int | None = None,
) -> dict[str, str]:
    """The one builder behind both public reservation forms.

    ``C5/a.java:52-119`` is a single loop over the train array, so one
    implementation covers a direct booking and a 환승 booking; the leg count is
    the only thing that differs. A one-leg call therefore emits exactly the
    bytes it emitted before this function existed, key order included.
    """
    resolved_legs = _validated_legs(legs, require=require_legs)
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif type(passengers) is not KorailPassengerCounts:
        raise KorailProtocolError(
            "KORAIL reservation requires an exact KorailPassengerCounts"
        )
    resolved_classes = _validated_seat_classes(
        seat_classes,
        leg_count=len(resolved_legs),
    )
    try:
        job_type = KorailReservationJobType(job_type)
    except ValueError:
        raise KorailProtocolError(
            "KORAIL reservation job type must be one of "
            + ", ".join(
                f'"{member.value}"' for member in KorailReservationJobType
            )
        ) from None
    if (
        job_type is KorailReservationJobType.STANDBY
        and len(resolved_legs) > 1
    ):
        # a5/k.java:120-127 -- G0(), the standby-eligibility check, returns
        # false outright for a transfer result, so a5/u.java:369-371/:401-404
        # never enables the 예약대기 button there; and the app's only
        # setJobId("1102") lives in DirectInquiryActivity.java:434, in an
        # onClick branch TransferInquiryActivity overrides away.
        raise KorailProtocolError(
            "KORAIL standby (예약대기) is a 직통 booking only: the app's "
            "standby check returns false for a transfer itinerary "
            "(a5/k.java:120-127) and its only txtJobId \"1102\" is on the "
            "direct screen (DirectInquiryActivity.java:434)"
        )
    assignments = _validated_leg_seats(
        leg_seats,
        leg_count=len(resolved_legs),
        job_type=job_type,
        passenger_total=passengers.total,
    )
    for leg, seat_class in zip(resolved_legs, resolved_classes):
        _assert_leg_is_bookable(leg, seat_class=seat_class, job_type=job_type)
    journeys = tuple(
        _journey_fields(leg) for leg in resolved_legs
    )
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": job_type.value,
            "txtGdNo": "",
            "hidFreeFlg": "N",
            # The app sets it from
            # J.isStndSeat(seatClass, h_gen_rsv_cd, h_stnd_rsv_cd)
            # (c5/b.java:69), which is true only for a GENERAL request on a
            # train whose general seats are sold out ("13") and whose standing
            # inventory is open -- S4/J.java:83-85. For "1101"/"1103" it is
            # always "N": neither cabin those jobs accept can be in that state,
            # since both demand "11". A standby train usually IS "13", so the
            # rule has to be evaluated rather than pinned there.
            #
            # C5/a.java:78-82 makes it a property of the whole booking rather
            # than of a leg: leg 1 assigns it, and every later leg overwrites it
            # only while it still reads "N" -- so one standing leg makes the
            # whole itinerary standing.
            "txtStndFlg": _itinerary_standing_flag(
                resolved_legs,
                seat_classes=resolved_classes,
            ),
            # w4/a.java:49 sends the app's TOTAL_PERSON_COUNT, and that is the
            # sum of ALL eight counters -- 동반유아 and 안내견 included
            # (m5/c.java:330).
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    for index, (attribute, passenger_type, discount_code) in enumerate(
        _PASSENGER_ROWS,
        start=1,
    ):
        form[f"txtCompaCnt{index}"] = str(getattr(passengers, attribute))
        form[f"txtPsgTpCd{index}"] = passenger_type
        form[f"txtDiscKndCd{index}"] = discount_code
    # OSeat, in w4/a.java:82-91's insertion order. The five txtSeatAttCd* keys
    # and txtPsrmClCd1 are written once on the booking-options screen; C5/a.java
    # :84-97 then re-puts journey 1's two and appends journey 2's. Because
    # OSeat is a LinkedHashMap and ReservationRequest.setOSeat is a putAll
    # (ReservationRequest.java:165-167), re-putting an existing key keeps its
    # position -- so the second leg's pair lands after txtPsrmClCd1 and the
    # one-leg block is untouched.
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): "015",
            "txtSeatAttCd5": "000",
            # OSeat.PSRM_CL_CD + journey number (OSeat.java:8,16-18), set from
            # the user's chosen tab: c5/b.java:72 passes
            # U4/a.java:88's GENERAL("1")/SPECIAL("2").
            "txtPsrmClCd1": resolved_classes[0].value,
        }
    )
    for journey, seat_class in enumerate(resolved_classes[1:], start=2):
        # C5/a.java:88-97 for the second leg. txtSeatAttCd4_1 carries the same
        # search-request seat attribute leg 1 does: C5/a.java:90's t2() is
        # b5/c.java:453-455, the ScheduleView request's txtSeatAttCd_4, which
        # this package always sends as "015" (K4/p.DEFAULT).
        form[_seat_attribute_key(journey)] = "015"
        form[f"txtPsrmClCd{journey}"] = seat_class.value
    # OJrny (OJrny.java:6-27), a LinkedHashMap in C5/a.java:54-76's write order:
    # the count once, then the sixteen per-leg keys for journey 1, then the same
    # sixteen for journey 2.
    form["txtJrnyCnt"] = (
        KORAIL_DIRECT_ITINERARY_CODE
        if len(resolved_legs) == 1
        else KORAIL_TRANSFER_ITINERARY_CODE
    )
    journey_type_code = (
        KORAIL_DIRECT_JOURNEY_TYPE_CODE
        if len(resolved_legs) == 1
        else KORAIL_TRANSFER_JOURNEY_TYPE_CODE
    )
    for journey, fields in enumerate(journeys, start=1):
        form[f"txtJrnyTpCd{journey}"] = journey_type_code
        form[f"txtJrnySqno{journey}"] = _sequence_no(
            KORAIL_DIRECT_ITINERARY_CODE
            if journey == 1
            else KORAIL_TRANSFER_ITINERARY_CODE
        )
        form[f"txtTrnNo{journey}"] = fields["train_no"]
        form[f"txtTrnClsfCd{journey}"] = fields["train_class_code"]
        form[f"txtTrnGpCd{journey}"] = fields["train_group_code"]
        form[f"txtRunDt{journey}"] = fields["run_date"]
        form[f"txtDptDt{journey}"] = fields["departure_date"]
        form[f"txtDptTm{journey}"] = fields["departure_time"]
        # OJrny.ARV_TM is "arvTm_", not "txtArvTm" (OJrny.java:12, 40-42).
        form[f"arvTm_{journey}"] = fields["arrival_time"]
        form[f"txtDptRsStnCd{journey}"] = fields["departure_station_code"]
        form[f"txtDptStnConsOrdr{journey}"] = fields[
            "departure_construction_order"
        ]
        form[f"txtDptStnRunOrdr{journey}"] = fields["departure_run_order"]
        form[f"txtArvRsStnCd{journey}"] = fields["arrival_station_code"]
        form[f"txtArvStnConsOrdr{journey}"] = fields[
            "arrival_construction_order"
        ]
        form[f"txtArvStnRunOrdr{journey}"] = fields["arrival_run_order"]
        form[f"txtChgFlg{journey}"] = "N"
    # OSrcar is the LAST @FieldMap on the Retrofit call
    # (CertificationService.java:52-54), so its keys go after the journey keys.
    # For "1101"/"1102" the map is empty and contributes nothing at all --
    # C5/a.java:118 clears it while building an ordinary journey -- which is why
    # a txtSrcarCnt of "0" never appears on the wire.
    #
    # Per leg, the order below is SeatSearchActivity.java:676-682's: the count,
    # then (car, seat) per index. The app itself cannot guarantee it -- :650
    # collects into a plain HashMap and :144 of C5/a.java putAll()s that back
    # into the LinkedHashMap -- so KORAIL demonstrably tolerates any OSrcar
    # ordering, and emitting the builder's own order is the reproducible choice.
    # Across legs the order is the app's screen order: the picker is opened per
    # journey index (C5/a.java:120-133) and each return merges its own block in.
    for journey, leg_assignments in enumerate(assignments, start=1):
        for index, assignment in enumerate(leg_assignments, start=1):
            if index == 1:
                # SeatSearchActivity.java:676. The count is the SEAT count, and
                # the key is chosen by the JOURNEY index, not the seat index
                # (OSrcar.java:21-23).
                form[_srcar_count_key(journey)] = str(len(leg_assignments))
            form[_srcar_no_key(journey, index)] = str(assignment.car_no)
            form[_seat_no_key(journey, index)] = assignment.seat_no
    return form


def _sequence_no(code: str) -> str:
    """``S4/O.getSequenceNo`` -- ``N.addZero(3, parseInt(code))``.

    ``S4/O.java:19-21`` into ``S4/N.java:32-38``, which is
    ``DecimalFormat("000").format(n)``. So the itinerary codes ``"1"``/``"2"``
    reach the wire as ``"001"``/``"002"``.
    """
    return f"{int(code):03d}"


def _assert_leg_is_bookable(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
    job_type: KorailReservationJobType,
) -> None:
    if job_type is KorailReservationJobType.STANDBY:
        # 예약대기 is offered on the 일반실 tab only. U4.a.b() sets the "wait"
        # bundle flag solely on the standard-cabin bundle (the p3 branch,
        # smali/U4/a.smali:1969-1981), and a5/u.java:371 enables the button only
        # when the selected tab is K4.o.GENERAL. There is no 특실 standby.
        if seat_class is not KorailSeatClass.GENERAL:
            raise KorailProtocolError(
                "KORAIL standby (예약대기) is offered on the 일반실 cabin "
                "only"
            )
        if train.wait_reservation_flag != KORAIL_STANDBY_WAIT_FLAG:
            raise KorailProtocolError(
                "KORAIL standby requires a train whose h_wait_rsv_flg is "
                f"{KORAIL_STANDBY_WAIT_FLAG!r}, got "
                f"{train.wait_reservation_flag!r}"
            )
        # Deliberately NO h_gen_rsv_cd check. The app never consults it for
        # standby; a standby train is normally 매진 ("13"), which is exactly the
        # state the "11" rule below refuses.
        return
    # The train list checks the availability code of the cabin the user picked,
    # not always the general one: a5/u.java:319 reads h_gen_rsv_cd for the
    # standard tab and h_spe_rsv_cd for the suite tab (likewise
    # DirectInquiryActivity.java:198). Keep this package's stricter rule -- only
    # an explicit "11" counts as available -- and apply it to whichever cabin is
    # being booked. On a transfer it is applied to every leg, because a booking
    # whose second leg is sold out is not bookable either.
    if seat_class is KorailSeatClass.SPECIAL:
        if train.special_reservation_code != "11":
            raise KorailProtocolError(
                "KORAIL reservation requires an evidenced available special seat"
            )
    elif train.general_reservation_code != "11":
        raise KorailProtocolError(
            "KORAIL reservation requires an evidenced available general seat"
        )


def _journey_fields(train: TrainSummary) -> dict[str, str]:
    """The sixteen ``OJrny`` values one leg contributes, all shape-checked."""
    return {
        "train_no": _required_digits(train.train_no, field="train_no"),
        "train_group_code": _required_digits(
            train.train_group_code,
            field="train_group_code",
        ),
        "train_class_code": _required_digits(
            train.train_class_code,
            field="train_class_code",
        ),
        "run_date": _required_pattern(
            train.run_date,
            field="run_date",
            pattern=_DATE_RE,
        ),
        "departure_date": _required_pattern(
            train.departure_date,
            field="departure_date",
            pattern=_DATE_RE,
        ),
        "departure_time": _required_pattern(
            train.departure_time,
            field="departure_time",
            pattern=_TIME_RE,
        ),
        "arrival_time": _required_pattern(
            train.arrival_time,
            field="arrival_time",
            pattern=_TIME_RE,
        ),
        "departure_station_code": _required_digits(
            train.departure_station_code,
            field="departure_station_code",
        ),
        "arrival_station_code": _required_digits(
            train.arrival_station_code,
            field="arrival_station_code",
        ),
        "departure_construction_order": _required_digits(
            train.departure_construction_order,
            field="departure_construction_order",
        ),
        "arrival_construction_order": _required_digits(
            train.arrival_construction_order,
            field="arrival_construction_order",
        ),
        "departure_run_order": _required_digits(
            train.departure_run_order,
            field="departure_run_order",
        ),
        "arrival_run_order": _required_digits(
            train.arrival_run_order,
            field="arrival_run_order",
        ),
    }


def _itinerary_standing_flag(
    legs: Sequence[TrainSummary],
    *,
    seat_classes: Sequence[KorailSeatClass],
) -> str:
    """``txtStndFlg`` for a whole itinerary -- C5/a.java:78-82.

    Leg 1 assigns the flag unconditionally; every later leg recomputes it only
    while the current value is still ``"N"``. The observable result is "Y if any
    leg is standing", and it is written as the app writes it so the equivalence
    stays visible.
    """
    flag = "N"
    for index, (train, seat_class) in enumerate(zip(legs, seat_classes)):
        if index == 0 or flag == "N":
            flag = _standing_flag(train, seat_class=seat_class)
    return flag


def _standing_flag(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
) -> str:
    """``txtStndFlg`` for one leg: S4/J.java:83-84's ``isStndSeat``, verbatim.

    ``GENERAL`` cabin, general seats 매진 (``"13"``) and standing inventory open
    (``"11"``). c5/b.java:69 is the caller that feeds it into the reservation
    request.
    """
    if (
        seat_class is KorailSeatClass.GENERAL
        and train.general_reservation_code == "13"
        and train.standing_reservation_code == "11"
    ):
        return "Y"
    return "N"


def build_single_adult_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
) -> dict[str, str]:
    """The one-adult, 일반실 hold form -- the only live-verified shape.

    A thin call into :func:`build_reservation_form` with both of its defaults,
    kept because this is the exact request the 2026-07-24/25 live reserve →
    cancel round trip sent and the only one KORAIL has been observed to accept
    from this package.
    """
    return build_reservation_form(config, train)


# The app concatenates three phone-number fields, capped at 3 + 4 + 4 digits
# (res/values/integers.xml:34-35, phone_number_max_length_3 and
# phone_number_max_length, applied in ReservationWaitActivity.java:88-89), and
# refuses the dialog when the concatenation is shorter than 10
# (ReservationWaitActivity.java:220-224). So 10 or 11 digits, nothing else.
_STANDBY_PHONE_RE = re.compile(r"[0-9]{10,11}")


def build_standby_wait_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    *,
    allow_seat_class_change: bool = False,
    sms_notify: bool = False,
    phone_no: str | None = None,
) -> dict[str, str]:
    """Build the 예약대기 follow-up form for a standby hold.

    This is ``reservationWait.ReservationWait``
    (``ReservationWaitService.java:10-12``), the second half of a standby
    booking: the ``"1102"`` hold creates the PNR, and this call records the two
    options the 예약대기 screen collects for it.

    Fields, in the order ``RsvWaitDao.executeDao()`` passes them:

    * ``txtPnrNo`` -- the hold's PNR (``ReservationWaitActivity.java:150``).
    * ``txtPsrmClChgFlg`` -- ``"Y"``/``"N"``, 좌석등급 변경 동의: may KORAIL
      assign a different cabin than the one waited for
      (``:213``/``:219``, ``check0``). The app hides that checkbox entirely
      for tour trains (``:115``), so it can only ever be ``"N"`` there.
    * ``txtSmsSndFlg`` -- ``"Y"``/``"N"``, SMS notification on assignment
      (``:214``/``:218``, ``check1``).
    * ``txtCpNo`` -- the notification number. The app sets it ONLY when SMS is
      on (``:220-227``); otherwise ``OWait`` has no ``PHONE_NO`` entry, the
      getter returns null and Retrofit drops the ``@Field``. This builder omits
      the key in exactly that case rather than sending an empty string.

    ``hold`` must be a successful hold carrying a PNR. A standby hold is the one
    whose ``h_msg_cd`` is
    :data:`~korail_mobile_api.KORAIL_STANDBY_HOLD_MESSAGE_CODE` (``IRR000014``)
    -- the only code that opens this screen in the app
    (``ui/inquiry/rir/orr/a.java:222-225``). That is not enforced here, because
    it is a routing condition rather than a wire constraint and a hold that
    carried some other advisory code would still be a real standby PNR; check it
    yourself if you want the app's exact behaviour.

    NOT live-verified.
    """
    if type(hold) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL standby options require an exact reservation hold response"
        )
    if (
        hold.str_result != "SUCC"
        or not isinstance(hold.pnr_no, str)
        or not hold.pnr_no.strip()
    ):
        raise KorailProtocolError(
            "KORAIL standby options require one successful hold with a PNR"
        )
    if type(allow_seat_class_change) is not bool:
        raise KorailProtocolError(
            "allow_seat_class_change must be a bool"
        )
    if type(sms_notify) is not bool:
        raise KorailProtocolError("sms_notify must be a bool")
    if sms_notify:
        if not isinstance(phone_no, str) or (
            _STANDBY_PHONE_RE.fullmatch(phone_no) is None
        ):
            raise KorailProtocolError(
                "KORAIL standby SMS notification requires a 10- or 11-digit "
                "phone number"
            )
    elif phone_no is not None:
        raise KorailProtocolError(
            "KORAIL standby sends no phone number unless sms_notify is True"
        )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": hold.pnr_no,
            "txtPsrmClChgFlg": "Y" if allow_seat_class_change else "N",
            "txtSmsSndFlg": "Y" if sms_notify else "N",
        }
    )
    if sms_notify:
        assert phone_no is not None
        form["txtCpNo"] = phone_no
    return form


def build_unpaid_reservation_cancel_form(
    config: KorailConfig,
    response: ReservationHoldResponse,
) -> dict[str, str]:
    if type(response) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL cancellation requires an exact reservation hold response"
        )
    # A live TicketReservation returns the journey count zero-padded
    # (h_jrny_cnt="0001"), not "1", so compare numerically rather than by
    # spelling -- a formatting difference must never make a hold uncancellable.
    #
    # The count is ECHOED, not fixed at one. DReservationConfirmActivity.java:
    # 269-278 is decisive: executeRsvCancel(ReservationResponse) sets
    # txtJrnySqno="0001" and hidRsvChgNo="000" as constants but passes
    # setTxtJrnyCnt(reservationResponse.getH_jrny_cnt()) straight through. A
    # 환승 hold carries two journeys, and refusing it here would leave a live
    # transfer reservation with no way to release it -- the orphaned hold this
    # whole subsystem exists to prevent.
    journey_count = response.journey_count
    legs = None
    if isinstance(journey_count, str) and journey_count.strip().isdigit():
        legs = int(journey_count)
    if (
        response.str_result != "SUCC"
        or not isinstance(response.pnr_no, str)
        or not response.pnr_no.strip()
        or legs is None
        or legs < 1
    ):
        raise KorailProtocolError(
            "KORAIL cancellation requires a fresh successful unpaid hold"
        )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": response.pnr_no,
            "txtJrnySqno": "0001",
            "txtJrnyCnt": str(legs),
            # A literal "000" here, NOT the hold's h_rsv_chg_no -- deliberately
            # unlike build_card_payment_form below. Every app flow that cancels
            # a just-created hold from its ReservationResponse hardcodes it,
            # next to the same fixed txtJrnySqno="0001":
            # DReservationConfirmActivity.java:270-279 is decisive, because
            # executeRsvCancel(ReservationResponse) reads getH_pnr_no() and
            # getH_jrny_cnt() off that very response, even stores the whole
            # object via setReservationResponse, and STILL sets "000" rather
            # than jrny_info[0].getH_rsv_chg_no(). Likewise
            # ReservationWaitActivity.java:118-128, a6/x.java:97-106,
            # LimousineActivity.java:134-143 and
            # LimousineSelectSeatActivity.java:325. The only cancel call sites
            # that pass a real change number are the reservation-LIST screens
            # (ReservedTicketActivity.java:228, BasketTicketActivity.java:276),
            # which cancel an arbitrary listed row and therefore also pass that
            # row's own h_jrny_sqno instead of "0001". This builder is the
            # fresh-single-journey-hold flow, so it sends the app's constant.
            "hidRsvChgNo": "000",
        }
    )
    return form


_CARD_FIELD_RE = re.compile(r"[0-9]+")

# What the app sends when the hold response withheld the sequence. The app
# passes whatever getH_tmp_job_sqno1/2() returned, including null, and Retrofit
# then omits the @Field entirely — a shape this client cannot reproduce without
# making the field conditional, and one no observed hold has produced (both
# 2026-07 live holds returned populated sequences). "000000" is the value this
# builder has always sent and the value srtgo hardcodes, so it stays as the
# explicit last resort rather than dropping reservation state silently.
_ABSENT_JOB_SEQUENCE = "000000"


def _echoed_job_sequence(value: str | None) -> str:
    if isinstance(value, str) and value.strip():
        return value
    return _ABSENT_JOB_SEQUENCE


# What the payment form sends when the hold response carried no usable
# first-journey h_rsv_chg_no. The app never handles that case: V4/b.java:41
# dereferences getJrny_infos().getJrny_info().get(0) unconditionally, so a hold
# without a journey row would throw inside the app rather than produce a wire
# value, and a null h_rsv_chg_no would be forwarded and then dropped by Retrofit
# -- neither shape is reproducible here without making the @Field conditional,
# and no observed hold has produced one. "000" is the value this builder has
# always sent, the value every fresh-hold cancel in the app hardcodes, and the
# value srtgo uses, so it stays as the explicit last resort. Note V4/b.java:25-30
# falls back to "0" instead, but only on getRecalculationRsvPaymentRequest,
# whose source is a previous request object rather than the reservation
# response; it is not this path's fallback.
_ABSENT_RESERVATION_CHANGE_NO = "000"


def _echoed_reservation_change_no(hold: ReservationHoldResponse) -> str:
    # The FIRST journey specifically, mirroring the app's
    # getJrny_infos().getJrny_info().get(0).getH_rsv_chg_no() (V4/b.java:41).
    journeys = hold.journeys
    if journeys:
        value = journeys[0].reservation_change_no
        if isinstance(value, str) and value.strip():
            return value
    return _ABSENT_RESERVATION_CHANGE_NO


def build_card_payment_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    card: CardPayment,
) -> dict[str, str]:
    """Build the single-card ReservationPayment form for an unpaid hold.

    Field set and constants mirror the evidenced app/srtgo ``pay_with_card``
    (``ktx.py:1030-1051``, cross-validated against decompiled ``PaymentMethod``):
    a single card settlement row (``hidStlMnsCd1="02"``) carrying the raw PAN.
    ``hidTmpJobSqno1/2`` echo the hold response, not a constant: ``V4/b.java:39-40``
    does ``setJobSqNo1(reservationResponse.getH_tmp_job_sqno1())`` (likewise 2)
    and ``RsvPaymentDao.executeDao()`` (``:129-131``) hands those straight to
    ``PaymentService.payment``'s ``@Field("hidTmpJobSqno1"/"2")``
    (``PaymentService.java:14``). ``hidRsvChgNo`` echoes the hold the same way:
    ``V4/b.java:41`` does ``setHidRsvChgNo(reservationResponse.getJrny_infos()
    .getJrny_info().get(0).getH_rsv_chg_no())`` — the FIRST journey's change
    number — and the app repeats that exact expression at every other payment
    call site (``MainBookingActivity.java:998``,
    ``OldMainBookingActivity.java:505``, ``TicketListActivity.java:1518``,
    ``ReservedTicketActivity.java:414``, ``LimousineActivity.java:189``,
    ``LimousineSelectSeatActivity.java:180``). It is per-reservation state, not a
    protocol constant; the cancel builder's fixed ``"000"`` is a genuinely
    different case, evidenced separately there. The reservation identity and
    amount come from ``hold`` (a fresh successful hold with a PNR, window
    number, and a received amount). This builder does not decide whether ``card``
    is chargeable and cannot tell: both ``pay_with_fake_card`` and
    ``pay_with_card`` build through here, and the consent they each accept is
    what separates a test card from an acknowledged real charge.

    ``hidMnsStlAmt1`` is the app's ``getReceivedAmount()``, not the display
    total: ``AbstractC1269e.java:406`` puts ``String.valueOf(getReceivedAmount())``
    into ``PAYMENT_AMOUNT`` and ``V4/a.java:27`` sets that as ``hidMnsStlAmt1``.
    ``h_tot_prc`` goes to ``mTotPrc`` (``PaymentActivity.java:174``), which is
    read only by ``getmTotPrc()`` (``:497``) for the UI. The two coincide for a
    single undiscounted adult, which is why the one live (card-declined) run
    never exposed the difference, but they diverge as soon as a discount or a
    second passenger is involved.
    """
    if type(hold) is not ReservationHoldResponse:
        raise KorailProtocolError(
            "KORAIL payment requires an exact reservation hold response"
        )
    if type(card) is not CardPayment:
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    pnr_no = hold.pnr_no
    window_no = hold.window_no
    # Deliberately NOT hold.total_price: that is the display figure. See the
    # docstring — the app settles getReceivedAmount(). When a hold response
    # carries neither h_tot_rcvd_amt nor readable per-seat h_rcvd_amt rows we
    # refuse rather than substitute the display total, because substituting is
    # exactly the defect this replaces.
    amount = hold.received_amount
    if (
        hold.str_result != "SUCC"
        or not isinstance(pnr_no, str)
        or not pnr_no.strip()
        or not isinstance(window_no, str)
        or not window_no.strip()
        or not isinstance(amount, str)
        or _DIGITS_RE.fullmatch(amount) is None
    ):
        raise KorailProtocolError(
            "KORAIL payment requires a fresh successful unpaid hold with a "
            "PNR, window number, and numeric received amount"
        )
    # The card number must be all digits (a fake test PAN is still digits); the
    # decline happens server-side at authorization.
    if _CARD_FIELD_RE.fullmatch(card.card_number) is None:
        raise KorailProtocolError("KORAIL payment card number must be digits")
    form = _common_fields(config)
    form.update(
        {
            "hidPnrNo": pnr_no,
            "hidWctNo": window_no,
            "hidTmpJobSqno1": _echoed_job_sequence(
                hold.temporary_job_sequence_1
            ),
            "hidTmpJobSqno2": _echoed_job_sequence(
                hold.temporary_job_sequence_2
            ),
            "hidRsvChgNo": _echoed_reservation_change_no(hold),
            "hidInrecmnsGridcnt": "1",
            "hidStlMnsSqno1": "1",
            "hidStlMnsCd1": "02",
            "hidMnsStlAmt1": amount,
            "hidCrdInpWayCd1": "@",
            "hidStlCrCrdNo1": card.card_number,
            "hidVanPwd1": card.card_password,
            "hidCrdVlidTrm1": card.card_expire,
            "hidIsmtMnthNum1": card.installment,
            "hidAthnDvCd1": card.card_type,
            "hidAthnVal1": card.birthday,
            "hiduserYn": "Y",
        }
    )
    return form


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
) -> dict[str, str]:
    """Build the ticket-refund (``refunds.RefundsRequest``) form for a paid ticket.

    Field set and order follow the app's own Retrofit declaration
    (``RefundService.java:29`` / ``RefundService.smali:212``): the PNR is
    ``txtPnrNo`` (P-n-r), plus the original-ticket sale window/date/sequence and
    return password, with the fixed ``h_mlg_stl="N"``,
    ``tk_ret_tms_dv_cd="21"``, ``pbpAcepTgtFlg="N"`` and empty geo fields.
    srtgo's ``ktx.py:1082`` spells the same field ``txtPrnNo``; that is a
    korail2-lineage typo which occurs ZERO times in the decompiled app, and
    Retrofit ``@Field`` names are exact-match, so sending it would transmit a
    refund with no PNR at all. A refund acts on a settled ticket; the caller
    supplies the :class:`PaidTicket` identity.
    """
    if type(ticket) is not PaidTicket:
        raise KorailProtocolError("KORAIL refund requires a PaidTicket")
    for name, value in (
        ("pnr_no", ticket.pnr_no),
        ("sale_date", ticket.sale_date),
        ("sale_window_no", ticket.sale_window_no),
        ("sale_sequence", ticket.sale_sequence),
        ("return_password", ticket.return_password),
    ):
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(
                f"KORAIL refund requires a non-empty PaidTicket.{name}"
            )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": ticket.pnr_no,
            "h_orgtk_sale_dt": ticket.sale_date,
            "h_orgtk_sale_wct_no": ticket.sale_window_no,
            "h_orgtk_sale_sqno": ticket.sale_sequence,
            "h_orgtk_ret_pwd": ticket.return_password,
            "h_mlg_stl": "N",
            "tk_ret_tms_dv_cd": "21",
            "trnNo": ticket.train_no,
            "pbpAcepTgtFlg": "N",
            "latitude": "",
            "longitude": "",
        }
    )
    return form


def _required_mutation_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL discount card request requires a non-empty {field}"
        )
    return value


def build_discount_card_purchase_form(
    config: KorailConfig,
    request: DiscountCardPurchaseRequest,
) -> dict[str, str]:
    """``research.dcntCrdInfo.do`` — buy a 할인카드(N카드).

    Four scalars plus two flattened maps, in the order
    ``ResearchService.java:68-70`` declares them. The scalar half is built by
    ``w4/a.java:106-113``; the two maps are the ``jrnyInfo`` and ``apdUsrInfo``
    ``HashMap``s of ``NCardReservationDao.NCardReservationRequest``
    (``dao/research/NCardReservationDao.java:31-32``), whose keys are the
    indexed spellings its setters write (``:74-124``):

    * ``jrnyInfo``: ``jrnyCnt`` once, then ``jrnyTpCd_N`` / ``runDt_N`` /
      ``trnNo_N`` / ``dptRsStnCd_N`` / ``arvRsStnCd_N`` per section.
    * ``apdUsrInfo``: ``apdUsrCnt`` once, then ``custMgNo_N`` /
      ``apdCustName_N`` / ``apdCustTeln_N`` per additional user.

    ``mCustomData`` (``:33,102-104``) is deliberately absent: it is a
    ``LinkedHashMap`` the request object carries for the confirmation screen
    and is not passed to ``executeDao`` (``:180``), so it never reaches the
    wire.

    **NOT VERIFIED, AND NOT ONLY BECAUSE IT WAS NEVER SENT.** No call site in
    v6.5.0 was found that populates ``jrnyInfo``/``apdUsrInfo`` — only the
    setters that would. The counts and key spellings come from the DAO;
    whether the server also requires a section for a 1-section card, and
    whether ``apdUsrCnt`` must be present as ``"0"`` for a 1인용 card rather
    than omitted, are open questions an operator must settle.
    """
    if type(request) is not DiscountCardPurchaseRequest:
        raise KorailProtocolError(
            "KORAIL discount card purchase requires an exact "
            "DiscountCardPurchaseRequest"
        )
    form = _common_fields(config)
    form.update(
        {
            "dcntCrdKndMgNo": _required_mutation_text(
                request.card_kind_management_no,
                field="card_kind_management_no",
            ),
            "custMgNo": _required_mutation_text(
                request.customer_no,
                field="customer_no",
            ),
            "vlidTrmStDt": _required_mutation_text(
                request.validity_start_date,
                field="validity_start_date",
            ),
            "usePsbTno": _required_mutation_text(
                request.usable_trip_count,
                field="usable_trip_count",
            ),
        }
    )
    sections = tuple(request.sections)
    if not sections or len(sections) > KORAIL_MAX_DISCOUNT_CARD_SECTIONS:
        raise KorailProtocolError(
            "KORAIL discount card purchase needs 1 to "
            f"{KORAIL_MAX_DISCOUNT_CARD_SECTIONS} sections"
        )
    form["jrnyCnt"] = str(len(sections))
    for index, section in enumerate(sections, start=1):
        if type(section) is not DiscountCardSectionRequest:
            raise KorailProtocolError(
                "KORAIL discount card purchase requires exact "
                "DiscountCardSectionRequest values"
            )
        form[f"jrnyTpCd_{index}"] = _required_mutation_text(
            section.journey_type_code,
            field="journey_type_code",
        )
        form[f"runDt_{index}"] = _required_mutation_text(
            section.run_date,
            field="run_date",
        )
        form[f"trnNo_{index}"] = section.train_no
        form[f"dptRsStnCd_{index}"] = _required_mutation_text(
            section.departure_station_code,
            field="departure_station_code",
        )
        form[f"arvRsStnCd_{index}"] = _required_mutation_text(
            section.arrival_station_code,
            field="arrival_station_code",
        )
    users = tuple(request.additional_users)
    if users:
        form["apdUsrCnt"] = str(len(users))
        for index, user in enumerate(users, start=1):
            if type(user) is not DiscountCardAdditionalUser:
                raise KorailProtocolError(
                    "KORAIL discount card purchase requires exact "
                    "DiscountCardAdditionalUser values"
                )
            form[f"custMgNo_{index}"] = _required_mutation_text(
                user.customer_no,
                field="additional user customer_no",
            )
            form[f"apdCustName_{index}"] = _required_mutation_text(
                user.name,
                field="additional user name",
            )
            form[f"apdCustTeln_{index}"] = _required_mutation_text(
                user.phone,
                field="additional user phone",
            )
    return form


def build_discount_card_extension_query(
    config: KorailConfig,
    ticket: DiscountCardTicket,
) -> dict[str, str]:
    """``reservation.dcntCrdExtn.do`` — extend a 할인카드's validity.

    Seven ``@Query`` parameters (``ResearchService.java:65-66``): the common
    three plus the card ticket's four-part credential, which
    ``TicketListActivity.java:1067-1072`` reads off the N카드 ticket row as
    ``h_orgtk_wct_no`` / ``h_orgtk_ret_sale_dt`` / ``h_orgtk_sale_sqno`` /
    ``h_orgtk_ret_pwd``.

    The app offers 기간연장 only when the card says it may:
    ``Y4/C0907b.java:301`` gates the button on
    ``dcnt_crd_info.h_dcnt_crd_trm_extn_psb_flg == "Y"``
    (:attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.term_extension_possible_flag`).
    That gate is NOT reproduced here, because it is a property of the card
    rather than of the request and a caller may hold the flag from a different
    read; check it before calling.

    **NOT VERIFIED.** The response is a bare ``BaseResponse`` in the DAO, so
    what a successful extension answers with — and what it costs — is unknown.
    """
    if type(ticket) is not DiscountCardTicket:
        raise KorailProtocolError(
            "KORAIL discount card extension requires an exact "
            "DiscountCardTicket"
        )
    query = _common_fields(config)
    query.update(
        {
            "saleWctNo": _required_mutation_text(
                ticket.sale_window_no,
                field="sale_window_no",
            ),
            "saleDd": _required_mutation_text(
                ticket.sale_date,
                field="sale_date",
            ),
            "saleSqno": _required_mutation_text(
                ticket.sale_sequence,
                field="sale_sequence",
            ),
            "tkRetPwd": _required_mutation_text(
                ticket.return_password,
                field="return_password",
            ),
        }
    )
    return query
