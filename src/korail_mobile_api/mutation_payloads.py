from __future__ import annotations

import re
from collections.abc import Sequence

from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KORAIL_DISCOUNT_CARD_DISCOUNT_CODE,
    KORAIL_DISCOUNT_CARD_MENU_ID,
    KORAIL_MAX_DISCOUNT_CARD_SECTIONS,
    KORAIL_MAX_JOURNEY_LEGS,
    KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE,
    KORAIL_MERGE_SEAT_FLAGS_BY_CABIN,
    KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE,
    KORAIL_STANDBY_WAIT_FLAG,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
    KorailReservationJobType,
    KorailSeatClass,
)
from .errors import KorailProtocolError
from .models import TrainSummary
from .read_models import TrainScheduleItem
from .mutation_models import (
    DiscountCardAdditionalUser,
    DiscountCardPurchaseRequest,
    DiscountCardSectionRequest,
    DiscountCardTicket,
    CardPayment,
    KorailPassengerCounts,
    KorailSeatAssignment,
    OfflineRefundReturnNumber,
    OfflineRefundVerifyResponse,
    PaidTicket,
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
    ReservationPassengerChangeLeg,
    ReservationPassengerChangeRequest,
    TripChangeDiscount,
    TripChangeLeg,
    TripChangeOriginalTicket,
    TripChangePassenger,
    TripChangeReservationRequest,
    TripChangeSeatAssignment,
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


def build_merge_reservation_form(
    config: KorailConfig,
    standing_hold_train: TrainSummary,
    legs: Sequence[TrainScheduleItem],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> dict[str, str]:
    """Build the SECOND hold of a 병합예약 -- one train, two journeys.

    병합 is not a transfer and not a third case of ``C5/a.java``'s journey loop.
    It is one physical train split at an intermediate station so the two halves
    can be seated differently (좌석+좌석 or 좌석+입석 --
    ``res/values/strings.xml:577``), and the app builds it in a loop of its own:
    ``DirectInquiryActivity.java:576-601``, re-read as
    ``smali/…/DirectInquiryActivity.smali:5580-6010``. See
    :data:`~korail_mobile_api.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` for the
    whole five-step flow and where each step's evidence is.

    The four differences from a 환승 form, all of them from that loop:

    * ``txtJrnyTpCd{i}`` keys on the loop **index**, so leg 1 is ``"21"``
      (병합 선행) and leg 2 is ``"22"`` (병합 후행). Both legs of a 환승 carry
      ``"14"``; here they differ, and the bytecode branch is ``if-nez v2`` on the
      index (``smali:5641``).
    * ``txtStndFlg`` is pinned ``"Y"`` (``smali:5887-5891``) rather than derived
      from ``isStndSeat`` -- the whole point of the flow is that the standing
      hold is being converted, so the app does not re-derive it.
    * ``txtPsrmClCd2`` is **copied** from ``txtPsrmClCd1`` (``smali:5919-5983``),
      falling back to 일반실 if the hold somehow carried no cabin. So ``legs``
      takes ONE ``seat_class``, not one per leg: the app cannot produce a merged
      booking whose halves are in different cabins even though its 환승 builder
      can.
    * there is **no** ``arvTm_2``, and ``arvTm_1`` is the WHOLE ROUTE's arrival
      time rather than leg 1's. The merge loop never calls ``setArvTm``
      (no such call anywhere in ``smali:5730-6010``), and the request it fills
      is a clone of the ``"1202"`` hold's whose ``OJrny`` merges rather than
      replaces (``ReservationRequest.java:29-46``, ``:158-160``). That is why
      this builder needs ``standing_hold_train``: the stale arrival time is a
      real field on the wire and reproducing the app means reproducing it.

    ``standing_hold_train`` is the 직통 row the ``"1202"`` hold was placed on --
    the same :class:`~korail_mobile_api.TrainSummary` passed to
    :meth:`KorailClient.reserve
    <korail_mobile_api.KorailClient.reserve>` with
    ``job_type=MERGE_STANDING``. ``legs`` are the two rows
    ``research.mergeSeatsC.do`` answered with, in order, from
    :attr:`MergeSeatsInquiryResponse.trains
    <korail_mobile_api.MergeSeatsInquiryResponse.trains>`; they are the same
    train number twice, split at the chosen 연결역.

    NEVER TRANSMITTED. Nothing built here has been sent to KORAIL, and no
    live-test path in this repository sends it.
    """
    if type(standing_hold_train) is not TrainSummary:
        raise KorailProtocolError(
            "KORAIL 병합 reservation requires the exact TrainSummary the "
            "입석+좌석 hold was placed on"
        )
    if isinstance(legs, (str, bytes)) or not isinstance(legs, Sequence):
        raise KorailProtocolError(
            "KORAIL 병합 reservation requires a sequence of merge-seat legs"
        )
    resolved_legs = tuple(legs)
    for leg in resolved_legs:
        if type(leg) is not TrainScheduleItem:
            raise KorailProtocolError(
                "KORAIL 병합 reservation legs are the TrainScheduleItem rows "
                "research.mergeSeatsC.do answers with"
            )
    if len(resolved_legs) != KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            f"KORAIL 병합 reservation books exactly {KORAIL_MAX_JOURNEY_LEGS} "
            f"journeys on one train, got {len(resolved_legs)}: the merge loop "
            'writes txtJrnyCnt="2" before it starts '
            "(DirectInquiryActivity.java:578) and the form has no journey-3 "
            "spelling at all"
        )
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif type(passengers) is not KorailPassengerCounts:
        raise KorailProtocolError(
            "KORAIL reservation requires an exact KorailPassengerCounts"
        )
    try:
        cabin = KorailSeatClass(seat_class)
    except ValueError:
        raise KorailProtocolError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        ) from None
    # The two halves must be the one train the standing hold was placed on.
    # The app never checks this because it cannot be otherwise -- the rows come
    # straight back from mergeSeatsC.do, which was asked about that train
    # (DirectInquiryActivity.java:358-360 sends its txtTrnNo1) -- but a caller
    # assembling the call by hand can get it wrong, and a merged booking of two
    # unrelated trains is a 환승 spelled with the wrong journey type.
    hold_train_no = _required_digits(
        standing_hold_train.train_no,
        field="train_no",
    )
    for leg in resolved_legs:
        if _required_digits(leg.train_no, field="train_no") != hold_train_no:
            raise KorailProtocolError(
                "KORAIL 병합 reservation splits ONE train: both legs must "
                f"carry the standing hold's train_no {hold_train_no!r}"
            )
    journeys = tuple(_merge_leg_fields(leg) for leg in resolved_legs)
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            # Back to "1101". The "1202" job id belongs to the standing hold
            # this one replaces; the merge loop re-sets it inside the loop
            # (DirectInquiryActivity.java:583, smali:5573-5575).
            "txtJobId": KorailReservationJobType.IMMEDIATE.value,
            "txtGdNo": "",
            "hidFreeFlg": "N",
            # Pinned, not derived. smali:5887-5891 is a bare const-string "Y".
            "txtStndFlg": "Y",
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
    # OSeat. The merge loop re-puts journey 1's pair and appends journey 2's,
    # into the LinkedHashMap the standing hold left behind, so the order is the
    # ordinary two-leg order -- see build_transfer_reservation_form.
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): "015",
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": cabin.value,
        }
    )
    form[_seat_attribute_key(2)] = "015"
    # Copied, not read per leg (smali:5919-5983).
    form["txtPsrmClCd2"] = cabin.value
    form["txtJrnyCnt"] = KORAIL_TRANSFER_ITINERARY_CODE
    for journey, fields in enumerate(journeys, start=1):
        form[f"txtJrnyTpCd{journey}"] = (
            KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE
            if journey == 1
            else KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE
        )
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
        if journey == 1:
            # The standing hold's own arvTm_1, kept because the merge loop
            # never overwrites it. It is the arrival time of the WHOLE route,
            # not of this half.
            form["arvTm_1"] = _required_pattern(
                standing_hold_train.arrival_time,
                field="arrival_time",
                pattern=_TIME_RE,
            )
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
    # No OSrcar: the standing hold cleared it (C5/a.java:118) and the merge
    # loop never writes one, so an empty @FieldMap contributes no fields.
    return form


def is_merge_eligible(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> bool:
    """Would the app offer 입석+좌석 예매 on this search row?

    ``S4/J.java:61-63``'s ``isMixedSeat(cabin, h_yms_apl_flg)``, expressed as
    the per-cabin flag sets it collapses to -- see
    :data:`~korail_mobile_api.KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`. It is the only
    row property the app consults: ``a5/u.java:378-380`` computes it per row and
    ``:394-397`` re-labels the booking button and tags it ``"1202"`` on the
    strength of it alone.
    """
    if type(train) is not TrainSummary:
        raise KorailProtocolError(
            "KORAIL merge eligibility requires an exact TrainSummary"
        )
    try:
        cabin = KorailSeatClass(seat_class)
    except ValueError:
        raise KorailProtocolError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        ) from None
    flag = train.merge_seat_application_flag
    if not isinstance(flag, str):
        return False
    return flag in KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[cabin.value]


def _merge_leg_fields(leg: TrainScheduleItem) -> dict[str, str]:
    """The twelve values one merged journey contributes.

    ``_journey_fields``'s set minus ``arrival_time``: the merge loop reads
    twelve getters off each ``TrainInfo`` and ``getH_arv_tm()`` is not among
    them (``smali/…/DirectInquiryActivity.smali:5730-5880``). The thirteenth
    per-leg key, ``txtChgFlg{i}``, is the constant ``"N"``.
    """
    return {
        "train_no": _required_digits(leg.train_no, field="train_no"),
        "train_group_code": _required_digits(
            leg.train_group_code,
            field="train_group_code",
        ),
        "train_class_code": _required_digits(
            leg.train_class_code,
            field="train_class_code",
        ),
        "run_date": _required_pattern(
            leg.run_date,
            field="run_date",
            pattern=_DATE_RE,
        ),
        "departure_date": _required_pattern(
            leg.departure_date,
            field="departure_date",
            pattern=_DATE_RE,
        ),
        "departure_time": _required_pattern(
            leg.departure_time,
            field="departure_time",
            pattern=_TIME_RE,
        ),
        "departure_station_code": _required_digits(
            leg.departure_station_code,
            field="departure_station_code",
        ),
        "arrival_station_code": _required_digits(
            leg.arrival_station_code,
            field="arrival_station_code",
        ),
        "departure_construction_order": _required_digits(
            leg.departure_construction_order,
            field="departure_construction_order",
        ),
        "arrival_construction_order": _required_digits(
            leg.arrival_construction_order,
            field="arrival_construction_order",
        ),
        "departure_run_order": _required_digits(
            leg.departure_run_order,
            field="departure_run_order",
        ),
        "arrival_run_order": _required_digits(
            leg.arrival_run_order,
            field="arrival_run_order",
        ),
    }


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
    if (
        job_type is KorailReservationJobType.MERGE_STANDING
        and len(resolved_legs) > 1
    ):
        # The 입석+좌석 button lives on the direct screen only. a5/u.java:346-360
        # disables the booking button outright while a transfer result has an
        # unselected leg, and the "1202" tag is set at :394-397 -- inside the
        # same U1() -- whereas the only reader of that tag is
        # DirectInquiryActivity.java:448-451, on the direct screen's own
        # onClick. The merged form that FOLLOWS a "1202" hold has two journeys,
        # but the hold itself is always one; that form is
        # build_merge_reservation_form, not this one.
        raise KorailProtocolError(
            "KORAIL 입석+좌석 (txtJobId \"1202\") is a 직통 hold: it is the "
            "FIRST of the two holds a 병합예약 is made of. Its two-journey "
            "successor is build_merge_reservation_form"
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
    if job_type is KorailReservationJobType.MERGE_STANDING:
        if not is_merge_eligible(train, seat_class=seat_class):
            raise KorailProtocolError(_merge_ineligible_message(train, seat_class))
        # Deliberately NO h_gen_rsv_cd check, for the same reason as standby
        # above: a merge-eligible train is normally 매진, which is exactly the
        # state the "11" rule below refuses. 입석+좌석 exists BECAUSE the seats
        # are gone.
        #
        # This replaced an earlier reading that made the "11" rule additive,
        # reasoning from a5/u.java:346-360 that the app disables the booking
        # button while any selected cabin reads 매진 or 좌석부족 and only then
        # (:394-397) lets isMixedSeat turn it into 입석+좌석 예매. That control
        # flow is real, but the string it tests is a DISPLAY state assembled in
        # U4.a.b() -- which jadx cannot decompile -- not h_gen_rsv_cd, and a
        # sold-out row can still have standing stock.
        #
        # LIVE 2026-07-26 settled it: 서울->부산 20260731 train 125 came back
        # with h_gen_rsv_cd="13" AND h_yms_apl_flg="A". On the additive reading
        # the merge flag could never fire, because the rows that carry it are
        # precisely the rows the "11" rule rejects. The flag is the gate.
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


def _merge_ineligible_message(
    train: TrainSummary,
    seat_class: KorailSeatClass,
) -> str:
    return (
        "KORAIL 입석+좌석 (txtJobId \"1202\") requires a merge-eligible row: "
        "h_yms_apl_flg must be one of "
        + ", ".join(sorted(KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[seat_class.value]))
        + f" for this cabin, got {train.merge_seat_application_flag!r}"
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


def _refund_echo_field(value: object, *, default: str, field: str) -> str:
    """Validate one echoed refund flag, falling back to the app's own default.

    ``None`` means "the caller did not read this off the server", which is the
    pre-existing behaviour and stays allowed. Anything else has to be a
    non-empty string, because a blank here would silently clear a field the
    server expects to get its own value back in.
    """
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL refund {field} must be a non-empty string when given"
        )
    return value


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
    *,
    return_times_division_code: str | None = None,
    settle_mileage: bool = False,
    pbp_acceptance_target_flag: str | None = None,
) -> dict[str, str]:
    """Build the ticket-refund (``refunds.RefundsRequest``) form for a paid ticket.

    Field set and order follow the app's own Retrofit declaration
    (``RefundService.java:29`` / ``RefundService.smali:212``): the PNR is
    ``txtPnrNo`` (P-n-r), plus the original-ticket sale window/date/sequence and
    return password, ``tk_ret_tms_dv_cd``, ``h_mlg_stl``, ``pbpAcepTgtFlg`` and
    empty geo fields. srtgo's ``ktx.py:1082`` spells the PNR field
    ``txtPrnNo``; that is a korail2-lineage typo which occurs ZERO times in the
    decompiled app, and Retrofit ``@Field`` names are exact-match, so sending it
    would transmit a refund with no PNR at all. A refund acts on a settled
    ticket; the caller supplies the :class:`PaidTicket` identity.

    Three of those fields are NOT constants in the app -- it echoes back what
    the server just told it, and this builder used to send a fixed value for
    each:

    ``return_times_division_code``
        ``tk_ret_tms_dv_cd``. The app copies
        ``RefundCommissionResponse.tk_ret_tms_dv_cd`` verbatim
        (``ticketReturn/a.smali:3149-3153``), which is ``"21"`` before
        departure and ``"15"`` after (``I4/a.java:5-6``). Read it off
        :meth:`~korail_mobile_api.KorailClient.get_refund_commission`'s
        :attr:`ticket_return_times_division_code` and pass it here; a refund
        after departure otherwise claims to be one before it. Defaults to
        ``"21"``.
    ``settle_mileage``
        ``h_mlg_stl``. Unlike the other two this is a caller decision, not a
        server echo: the app passes ``"Y"`` only when the ticket is
        mileage-settleable AND the usable mileage covers the fee
        (``ticketReturn/a.java:185-190``). Defaults to ``False`` (``"N"``).
    ``pbp_acceptance_target_flag``
        ``pbpAcepTgtFlg``. Echoed from
        ``RefundTicketDetailResponse.pbp_acceptance_target_flag``
        (``ticketReturn/a.smali:3165-3171``). Defaults to ``"N"``.

    Passing nothing keeps the previous fixed values, so existing callers are
    unaffected -- but a caller who has the ticket detail and the commission in
    hand should pass all three, because the app never sends any other
    combination.
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
            "h_mlg_stl": "Y" if settle_mileage else "N",
            "tk_ret_tms_dv_cd": _refund_echo_field(
                return_times_division_code,
                default="21",
                field="return_times_division_code",
            ),
            "trnNo": ticket.train_no,
            "pbpAcepTgtFlg": _refund_echo_field(
                pbp_acceptance_target_flag,
                default="N",
                field="pbp_acceptance_target_flag",
            ),
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


#: The eight passenger-row key prefixes an ordinary hold carries
#: (``OPsg.java:8-10``). An N카드 hold replaces all of them with one row.
_PASSENGER_ROW_KEYS = frozenset(
    f"{prefix}{index}"
    for prefix in ("txtCompaCnt", "txtPsgTpCd", "txtDiscKndCd")
    for index in range(1, len(_PASSENGER_ROWS) + 1)
)


def build_discount_card_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    card_no: str,
) -> dict[str, str]:
    """Build a hold that pays for one seat with a 할인카드(N카드).

    **This is the ordinary reservation route.** ``w4/a.java:93-104``
    (``getNCardReservationRequest``) produces a plain ``ReservationRequest``,
    and its single caller —
    ``SeatAssignBookingActivity.java:153-163`` (``setNCCardTicket``) — hands it
    to ``NCardDirectInquiryActivity``, whose base class POSTs it with an
    ordinary ``ReservationDao`` (``c5/b.java:128-138`` →
    ``ReservationDao.java:12-22``) to
    ``certification.TicketReservation`` (``CertificationService.java:52-54``).
    There is no N카드 reservation endpoint; there is an N카드 passenger block.

    Two things, and only two, differ from
    :func:`build_reservation_form`'s one-adult 일반실 form:

    1. **The passenger block collapses to one row carrying the card.** The
       eight rows become ``txtTotPsgCnt="1"``, ``txtCompaCnt1="1"``,
       ``txtPsgTpCd1="1"``, ``txtDiscKndCd1="153"`` and
       ``txtCardNo_1=<card_no>`` (``w4/a.java:96-101``). Note the inconsistent
       spelling: ``OPsg.CARD_NO`` is ``"txtCardNo_"`` WITH a trailing
       underscore while the other three prefixes have none
       (``OPsg.java:7-10``), so the transmitted key is ``txtCardNo_1``, not
       ``txtCardNo1``.
    2. ``txtMenuId`` becomes ``"A2"``
       (``SeatAssignBookingActivity.java:159``) instead of ``"11"``.

    Everything else is byte-identical, and deliberately so: this builder starts
    from :func:`build_reservation_form`'s output and substitutes the passenger
    block **in place**, so the journey block, the seat block, ``txtJobId``,
    ``txtStndFlg``, ``hidFreeFlg`` and ``txtGdNo`` are the values the live-
    verified path already sends, in the positions it already sends them. The
    app agrees that they are shared: ``c5/b.java:42-77`` writes ``OJrny`` and
    ``OSeat`` for an N카드 hold with the same code that writes them for an
    ordinary one.

    A card is one seat. The app never offers a passenger mix here —
    ``w4/a.java:97-98`` hardcodes a total of one — and never offers 특실:
    ``w4/a.java:88`` pins ``psrmClCd1`` to ``o.GENERAL``. Both are therefore
    fixed rather than parameters.

    **NEVER TRANSMITTED.** This is a reserve-surface addition built entirely
    from the APK, and no account this project can reach owns an N카드 to send
    it with. What is verified is the route, the two differences, and the key
    spellings; what is not verified is that a server accepts this form, or
    what it answers when the card is expired, spent or not the caller's.
    """
    form = build_reservation_form(config, train)
    rebuilt: dict[str, str] = {}
    for name, value in form.items():
        if name == "txtTotPsgCnt":
            rebuilt[name] = "1"
            rebuilt["txtCompaCnt1"] = "1"
            rebuilt["txtPsgTpCd1"] = "1"
            rebuilt["txtDiscKndCd1"] = KORAIL_DISCOUNT_CARD_DISCOUNT_CODE
            rebuilt["txtCardNo_1"] = _required_mutation_text(
                card_no,
                field="card_no",
            )
            continue
        if name in _PASSENGER_ROW_KEYS:
            continue
        rebuilt[name] = value
    # Re-assigning an existing key keeps its position, so the menu id stays
    # where build_reservation_form put it.
    rebuilt["txtMenuId"] = KORAIL_DISCOUNT_CARD_MENU_ID
    return rebuilt


# The one wire value ``hidDcntKndCd`` can never carry. ``makeDiscountParams``
# (``S4/D.java:181-183``) special-cases 군장병: it writes "432" into
# ``dcnt_knd_cd1`` and BLANKS the applied-discount field. The smali is
# unambiguous that the blanking happens -- ``S4/D.smali`` line 24 of the method
# is ``move-object p3, v2`` with ``v2`` the empty string, immediately before
# the shared ``:goto_1`` tail that calls ``setHidDcntKndCd(p3)``. jadx renders
# the same reassignment, and here the two agree.
_SOLDIER_DISCOUNT_CODE = "432"

# ``T4/a.java:51-53`` -> ``T4/b.java:46,62``: an "integrated" 국가유공자
# discount is a certificate number beginning "51" under discount kind "151" or
# "152". ``makeDiscountParams`` then sends ``dcnt_knd_cd1="000"`` -- CLEARING
# the seat's existing discount -- instead of echoing it back.
_MERIT_DISCOUNT_CODES = frozenset({"151", "152"})
_MERIT_CERTIFICATE_PREFIX = "51"

_PRICE_RECALCULATION_ROW_FIELDS: tuple[tuple[str, str], ...] = (
    ("psg_tp_dv_cd", "passenger_type_code"),
    ("hidDcntKndCd", "requested_discount_code"),
    ("dcnt_knd_cd1", "discount_kind_code"),
    ("hidDscpNo", "certificate_no"),
    ("psrm_cl_cd", "room_class_code"),
    ("hidFmlyNo", "family_sequence_no"),
)


def build_price_recalculation_form(
    config: KorailConfig,
    request: PriceRecalculationRequest,
) -> dict[str, str | list[str]]:
    """``certification.PriceReCalculation`` — re-price a held PNR.

    ``CertificationService.java:35-37`` (``getDiscountPrice``), built by
    ``a6/C1042B.java:265-296`` (``k2()``) and dispatched by
    ``DiscountPriceDao.executeDao`` (``DiscountPriceDao.java:118-120``).

    **THE SIX PARALLEL LISTS ARE ONE ROW PER SEAT, PAIRED BY INDEX.** ``k2()``
    is a single loop over one ``DiscountPriceParams[]`` that appends one field
    of the same element to each of six ``ArrayList``s per iteration
    (``a6/C1042B.java:275-283``), so element *i* of all six belongs to seat
    *i*. Verified against ``smali/a6.1/B.smali`` (the ``k2()`` body: one
    ``:goto_0`` loop over ``z0``, six ``List->add`` calls between
    ``aget-object v11`` and ``add-int/lit8 v10, v10, 0x1``), because jadx has
    mangled this codebase before. ``a6/C1041A.java:57-80``, the 다자녀 variant,
    builds its rows differently and then calls the SAME ``k2()``, and its own
    screen refuses to submit unless the row count equals the seat count
    (``:91-94``) — so "one row per seat" holds on both paths.

    **The lists go out as REPEATED KEYS, not indexed ones.** Retrofit 1.x
    flattens an ``Iterable`` ``@Field`` by iterating it and calling
    ``addField(name, element)`` with the name unchanged
    (``RequestBuilder.smali:1537-1601``: the ``instance-of ... Iterable``
    branch, then ``invoke-virtual {v6, v3, v5}`` inside the ``:goto_3`` loop
    where ``v3`` is loop-invariant). ``FormUrlEncodedTypedOutput.addField``
    just appends ``&`` and URL-encodes. So the body carries
    ``psg_tp_dv_cd=..&psg_tp_dv_cd=..``, with no ``[]`` and no index suffix.
    This builder therefore returns ``list`` values, which httpx encodes the
    same way.

    ``txtJobId`` is the fixed ``"1101"`` of ``a6/C1042B.java:267``, and
    ``txtPsgGridcnt`` is the row count — the app sends the journey's seat count
    (``:269``), which is the same number.

    ``hiduserYn``/``hidCustNo`` are transmitted ONLY for a non-member
    (``:290-293``). For a member they are null, and Retrofit omits a null
    ``@Field`` entirely (``RequestBuilder.smali:1531``), so a member's form has
    twelve keys rather than fourteen.

    **NOT VERIFIED.** Nothing here has ever been sent. The pairing, the key
    spellings and the repeated-key encoding are all settled from the APK, but
    what the server does with a row whose ``dcnt_knd_cd1`` disagrees with the
    hold, and whether it validates ``txtPsgGridcnt`` against the PNR at all,
    can only be learned from a live call against a real hold.
    """
    if type(request) is not PriceRecalculationRequest:
        raise KorailProtocolError(
            "KORAIL price recalculation requires an exact "
            "PriceRecalculationRequest"
        )
    pnr_no = request.pnr_no
    if not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailProtocolError(
            "KORAIL price recalculation requires a non-empty pnr_no"
        )
    rows = tuple(request.rows)
    if not rows or len(rows) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            "KORAIL price recalculation needs 1 to "
            f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} passenger rows"
        )

    columns: dict[str, list[str]] = {
        name: [] for name, _ in _PRICE_RECALCULATION_ROW_FIELDS
    }
    for row in rows:
        if type(row) is not PriceRecalculationRow:
            raise KorailProtocolError(
                "KORAIL price recalculation requires exact "
                "PriceRecalculationRow values"
            )
        for wire_name, attribute in _PRICE_RECALCULATION_ROW_FIELDS:
            value = getattr(row, attribute)
            # Not `or not value`: three of the six are legitimately "". What is
            # refused is a non-string -- above all None, which Retrofit would
            # DROP from its list rather than send empty, shortening one key
            # against the other five and re-pairing every later row.
            if type(value) is not str:
                raise KorailProtocolError(
                    f"KORAIL price recalculation row field {attribute} must "
                    "be a string"
                )
            columns[wire_name].append(value)
        for attribute in (
            "passenger_type_code",
            "room_class_code",
            "discount_kind_code",
        ):
            if not getattr(row, attribute).strip():
                raise KorailProtocolError(
                    "KORAIL price recalculation copies "
                    f"{attribute} off the held seat; it must not be empty"
                )
        if row.requested_discount_code == _SOLDIER_DISCOUNT_CODE:
            raise KorailProtocolError(
                "KORAIL price recalculation never sends 군장병 as "
                "requested_discount_code: the app moves \"432\" into "
                "discount_kind_code and blanks this field "
                "(S4/D.java:181-183)"
            )
        if (
            row.requested_discount_code in _MERIT_DISCOUNT_CODES
            and row.certificate_no.startswith(_MERIT_CERTIFICATE_PREFIX)
            and row.discount_kind_code != "000"
        ):
            raise KorailProtocolError(
                "KORAIL price recalculation must send discount_kind_code "
                "\"000\" for an integrated 국가유공자 discount "
                "(S4/D.java:184-186 via T4/a.java:51-53)"
            )

    form: dict[str, str | list[str]] = dict(_common_fields(config))
    form["hidPnrNo"] = pnr_no
    form["txtJobId"] = KorailReservationJobType.IMMEDIATE.value
    non_member_no = request.non_member_no
    if non_member_no is not None:
        if not isinstance(non_member_no, str) or not non_member_no.strip():
            raise KorailProtocolError(
                "KORAIL price recalculation non_member_no must be a non-empty "
                "string when present"
            )
        # Only a non-member session writes these two, and it writes them
        # together (a6/C1042B.java:290-293).
        form["hiduserYn"] = "N"
        form["hidCustNo"] = non_member_no
    form["txtPsgGridcnt"] = str(len(rows))
    for wire_name, _ in _PRICE_RECALCULATION_ROW_FIELDS:
        form[wire_name] = columns[wire_name]
    return form


def _required_identity_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL offline refund requires a non-empty {field}"
        )
    return value


def build_offline_refund_verify_form(
    config: KorailConfig,
    return_number: OfflineRefundReturnNumber,
    *,
    requester_name: str,
) -> dict[str, str]:
    """``refunds.verifyOnlineRefunds`` — 비회원 오프라인 반환 1단계 (조회).

    NOT the member refund. There is no session, no PNR and no
    :class:`~korail_mobile_api.mutation_models.PaidTicket` here: the ticket is
    a paper one bought at a station window, and it is identified by the
    16-digit 반환번호 printed on it plus the requester's own name. The member
    path is :func:`build_refund_form` (``refunds.RefundsRequest``).

    Five fields after the common envelope, in the order the app's Retrofit
    signature declares them — ``Device``, ``Version``, ``Key``, ``retNo1``,
    ``retNo2``, ``retNo3``, ``retNo4``, ``strName``
    (``RefundService.java:31-33``; re-read from
    ``smali/com/korail/talk/network/dao/refund/RefundService.smali:273-320``,
    where the eight ``retrofit/http/Field`` annotations carry exactly those
    values and the ``POST`` annotation carries
    ``/classes/com.korail.mobile.refunds.verifyOnlineRefunds``).

    ``strName`` is the 요청자 — the ``requestorEdit`` box of
    ``offline_return_input_fragment.xml``, read at ``s5/c.java:71``. The
    phone number the same screen collects is NOT sent here; it is held for the
    execute call (``s5/c.java:106`` passes it along, ``s5/h.java:123`` sends
    it).

    Every field this builds is a bearer credential or PII, and none of them is
    caught by a value-shaped regex — the 16 digits arrive split 5/4/5/2, so
    ``CARD_RE`` never sees 13 consecutive digits. All five wire keys are
    registered in :data:`~korail_mobile_api.redaction.SENSITIVE_KEYS`.
    """
    if type(return_number) is not OfflineRefundReturnNumber:
        raise KorailProtocolError(
            "KORAIL offline refund verification requires an "
            "OfflineRefundReturnNumber"
        )
    form = _common_fields(config)
    form.update(
        {
            "retNo1": return_number.return_no_1,
            "retNo2": return_number.return_no_2,
            "retNo3": return_number.return_no_3,
            "retNo4": return_number.return_no_4,
            "strName": _required_identity_text(
                requester_name,
                field="requester_name",
            ),
        }
    )
    return form


def build_offline_refund_execute_form(
    config: KorailConfig,
    verified: OfflineRefundVerifyResponse,
    *,
    requester_name: str,
    requester_phone: str,
) -> dict[str, str]:
    """``refunds.executeOnlineRefunds`` — 비회원 오프라인 반환 2단계 (접수/환불).

    NOT the member refund (:func:`build_refund_form`). This one moves money on
    a paper ticket nobody is logged in to own.

    Twelve fields after the common envelope, in the order the app's Retrofit
    signature declares them — ``Device``, ``Version``, ``Key``, ``pnrNo``,
    ``tkKndCd``, ``retDvCd``, ``retRsnCd``, ``ogtkSaleDt``, ``ogtkSaleWctNo``,
    ``ogtkSaleSqno``, ``ogtkRetPwd``, ``retAmt``, ``retFee``, ``custTeln``,
    ``acepCustNm`` (``RefundService.java:15-17``; re-read from
    ``RefundService.smali:1-90``, whose fifteen ``Field`` annotation values are
    exactly those and whose ``POST`` value is
    ``/classes/com.korail.mobile.refunds.executeOnlineRefunds``).

    ``verified`` is the PARSED VERIFY RESPONSE rather than a hand-assembled
    identity, because that is precisely what the app does: ``s5/h.java:114-125``
    takes nine of the twelve values off ``getOrgTkInfos().get(0)`` and the two
    amounts off the response itself, and only the last two come from the user.
    Letting a caller assemble the four-part sale identity by hand is how a
    mismatched credential reaches a real refund.

    **The two identity fields are crossed relative to their bundle keys.** The
    app stashes the requester's NAME under the bundle key ``"CUSTOMER_NUMBER"``
    and the PHONE under ``"PHONE_NUMBER"`` (``s5/h.java:100-108``, from
    ``s5/c.java:106`` which passes ``requestorEdit`` then ``phoneNoEdit``), then
    reads them back as ``setAcepCustNm(...getString("CUSTOMER_NUMBER"))`` and
    ``setCustTeln(...getString("PHONE_NUMBER"))`` (``:122-123``). So
    ``acepCustNm`` is the name and ``custTeln`` is the phone number — the
    misleading bundle key is the app's, and it is exactly the kind of thing a
    later reader "fixes" the wrong way.

    Only the FIRST resolved ticket is refunded, matching the app's
    ``get(0)``. A 반환번호 that resolved to more than one ticket is refused
    rather than silently refunding one of them.
    """
    if type(verified) is not OfflineRefundVerifyResponse:
        raise KorailProtocolError(
            "KORAIL offline refund execution requires an "
            "OfflineRefundVerifyResponse from verifyOnlineRefunds"
        )
    tickets = verified.tickets
    if len(tickets) != 1:
        raise KorailProtocolError(
            "KORAIL offline refund execution requires exactly one verified "
            f"ticket; the verification returned {len(tickets)}"
        )
    ticket = tickets[0]
    identity = {
        "pnrNo": ticket.pnr_no,
        "tkKndCd": ticket.ticket_kind_code,
        "retDvCd": ticket.return_division_code,
        "retRsnCd": ticket.return_reason_code,
        "ogtkSaleDt": ticket.original_sale_date,
        "ogtkSaleWctNo": ticket.original_window_no,
        "ogtkSaleSqno": ticket.original_sale_sequence,
        "ogtkRetPwd": ticket.original_return_password,
        "retAmt": verified.refund_amount,
        "retFee": verified.refund_fee,
    }
    missing = [name for name, value in identity.items() if not value]
    if missing:
        raise KorailProtocolError(
            "KORAIL offline refund execution is missing verified fields: "
            f"{', '.join(missing)}"
        )
    form = _common_fields(config)
    form.update({name: str(value) for name, value in identity.items()})
    form["custTeln"] = _required_identity_text(
        requester_phone,
        field="requester_phone",
    )
    form["acepCustNm"] = _required_identity_text(
        requester_name,
        field="requester_name",
    )
    return form


# ---------------------------------------------------------------------------
# 승차권 여행변경 (ticket_change)
#
# THE INDEXING RULE, ONCE, FOR ALL THREE ROUTES BELOW. Every R* class in
# network/data/reservation is a LinkedHashMap<String,String> whose setters
# append a decimal index to a constant prefix, and Retrofit's @FieldMap
# flattens the map key-for-key (RequestBuilder.smali:1440-1508 walks
# entrySet() and calls addField(key, value)). So the wire key IS the map key,
# the map's INSERTION order is the wire order -- which is not the same as the
# order the calls appear in, because a LinkedHashMap re-put keeps the key's
# first position (see the RSeat block of build_trip_change_reservation_form,
# the one map two files write) -- and there are exactly two shapes:
#
#   one index   prefix + N            e.g. dptDt_1, psgTpDvCd_2
#   two indices prefix + N + "_" + K  e.g. rqSeatAttCd_1_1, dcntKndCd_2_1
#
# EVERY index is 1-based. The app's loops all increment before the first use
# (w4/b.java:148, C5/d.java:48, w4/a.java:140), and the two-index writers are
# called with a literal 1 for the inner index on every path found.
#
# Two prefixes are NOT what their setter names suggest and are easy to get
# wrong (RSrcar.java:7-10, 24-26):
#
#   setScarCnt  -> "scarCnt_"     setSrcarCnt -> "srcarCnt_"
#   setSrcarNo  -> "scarNo_"      setSeatNo   -> "seatNo_"
#
# and the two routes below disagree about which count they send:
# reservationChange.do writes scarCnt_ (w4/a.java:154) while the trip-change
# seat picker writes srcarCnt_ (SeatSearchActivity.java:660).
# ---------------------------------------------------------------------------

#: ``jrnySqno_N`` for leg N. ``C5/d.java:51`` writes
#: ``addZero(4, int(K4.d.DIRECT_SQ_NO))`` for the first leg and
#: ``TRANSFER_SQ_NO`` for every later one; the codes are "1" and "2"
#: (``K4/d.java:5-6``), so the two possible values are these.
_TRIP_CHANGE_JOURNEY_SEQUENCE_NOS = ("0001", "0002")

#: The three ``RSeat`` attribute codes ``w4/b.java:165-167`` writes before
#: ``rqSeatAttCd`` and ``C5/d.java`` never touches. Each is
#: ``prefix + leg + "_1"``. The values are enum codes: ``K4/q.DISABLE``
#: 사용안함, ``K4/l.DEFAULT`` 모든방향, ``K4/n.DEFAULT`` 모든 위치 — all
#: ``"000"``, but spelled out per key because they come from three different
#: enums and only coincide.
_TRIP_CHANGE_SEAT_OPTION_CODES: tuple[tuple[str, str], ...] = (
    ("smkSeatAttCd_", "000"),  # K4/q.java:6 DISABLE
    ("dirSeatAttCd_", "000"),  # K4/l.java:5 DEFAULT
    ("locSeatAttCd_", "000"),  # K4/n.java:5 DEFAULT
)

#: ``etcSeatAttCd_N_1`` (``K4/m.java:5`` DISABLE), written LAST of the six
#: (``w4/b.java:169``) — after ``rqSeatAttCd``, which is why it is not in the
#: tuple above.
_TRIP_CHANGE_ETC_SEAT_ATTRIBUTE_CODE = "000"

#: ``trvlKndCd`` (``w4/b.java:135``), ``intgTktIseFlg`` (``:139``),
#: ``alcSeatDmnPsDvCd`` (``:140``) and the two "second journey" counters
#: ``jrny2Cnt``/``psg2Cnt``, both ``addZero(4, 0)`` (``:141-142``). No call
#: site varies any of them, so they are constants rather than parameters.
_TRIP_CHANGE_TRAVEL_KIND_CODE = "1"
_TRIP_CHANGE_INTEGRATED_TICKET_FLAG = "N"
_TRIP_CHANGE_SEAT_DEMAND_CODE = "000"
_TRIP_CHANGE_SECOND_JOURNEY_COUNT = "0000"


def _zero_padded(value: int, *, width: int) -> str:
    """``S4/N.addZero(width, value)`` — a ``DecimalFormat`` of ``width`` zeros.

    ``S4/N.java:32-38`` builds a format string of ``width`` ``"0"`` characters
    and formats the integer with it, which is left-zero-padding that does NOT
    truncate a longer number.
    """
    return f"{value:0{width}d}"


def _required_trip_change_text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL ticket change request requires a non-empty {field}"
        )
    return value


#: ``RJrny`` keys ``C5/d.java:54-66`` writes after the three derived ones, in
#: the order it writes them. Prefixes from ``RJrny.java:5-18``.
_TRIP_CHANGE_JOURNEY_FIELDS: tuple[tuple[str, str], ...] = (
    ("runDt_", "run_date"),
    ("stlbTrnClsfCd_", "train_classification_code"),
    ("trnGpCd_", "train_group_code"),
    ("dptDt_", "departure_date"),
    ("dptTm_", "departure_time"),
    ("dptRsStnCd_", "departure_station_code"),
    ("dptStnConsOrdr_", "departure_station_consecutive_order"),
    ("dptStnRunOrdr_", "departure_station_run_order"),
    ("arvDt_", "arrival_date"),
    ("arvTm_", "arrival_time"),
    ("arvRsStnCd_", "arrival_station_code"),
    ("arvStnConsOrdr_", "arrival_station_consecutive_order"),
    ("arvStnRunOrdr_", "arrival_station_run_order"),
)

#: ``ROrtg`` keys ``w4/b.java:149-153`` writes per original ticket, in order.
#: Prefixes from ``ROrtg.java:7-13``.
_TRIP_CHANGE_ORIGINAL_TICKET_FIELDS: tuple[tuple[str, str], ...] = (
    ("ogtkSaleWctNo_", "sale_window_no"),
    ("ogtkSaleDd_", "sale_date"),
    ("ogtkSaleSqno_", "sale_sequence"),
    ("ogtkRetPwd_", "return_password"),
    ("retNoMnlInpFlg_", "manual_return_no_flag"),
)


def build_trip_change_reservation_form(
    config: KorailConfig,
    request: TripChangeReservationRequest,
) -> dict[str, str]:
    """``reservation.tripChgPrsC.do`` — hold the replacement of a 여행변경.

    Fifteen ``@Field``s then SIX ``@FieldMap``s
    (``ReservationService.java:24-26``). The maps are not interchangeable and
    their identity is not guessable from the signature — it is fixed by the
    argument order of ``TCReservationDao.executeDao`` (``:218-223``), which
    passes ``getRJrny()``, ``getRSrcar()``, ``getRSeat()``, ``getRPsg()``,
    ``getROrtg()``, ``getRDscp()`` in that order. This builder emits them in
    that order, and the form below is a ``dict``, whose insertion order httpx
    preserves on the wire.

    ``getOrgRDscp()`` — the SEVENTH map on the request object
    (``TCReservationDao.java:36``) — is deliberately absent: ``executeDao``
    does not pass it. The app carries it so the payment screen can clone it and
    add discounts (``a6/C1043C.java:85,230``); it never reaches the network.

    Field by field, with the two builders that produce them:

    ==================== ============================= =======================
    field                value                          evidence
    ==================== ============================= =======================
    ``trvlKndCd``        ``"1"``                        w4/b.java:135
    ``totPrnb``          原票 count                     w4/b.java:136
    ``isePrnb``          原票 count                     w4/b.java:137
    ``stndSeatFlg``      caller                         w4/b.java:138 →
                                                        C5/d.java:68
    ``intgTktIseFlg``    ``"N"``                        w4/b.java:139
    ``prcFareReCalcFlg`` ``"N"``/``"Y"``                C5/d.java:136,144
    ``tmpJobSqno``       omitted / PNR                  C5/d.java:137,145
    ``alcSeatDmnPsDvCd`` ``"000"``                      w4/b.java:140
    ``jrny2Cnt``         ``"0000"``                     w4/b.java:141
    ``psg2Cnt``          ``"0000"``                     w4/b.java:142
    ``ctlDvCd``          omitted / ``"3584"``           SeatSearchActivity:784
    ``frcSaleRsnCont``   omitted / reason code          SeatSearchActivity:779
    ==================== ============================= =======================

    ``totPrnb``/``isePrnb`` are the number of ORIGINAL tickets, not the number
    of passengers: ``w4/b.java:136-137`` uses ``orgTkList.size()`` for both
    while ``psgCnt`` (``:175``) uses the picker's total. They differ whenever
    a 동반유아 is added or removed, and this builder keeps them separate.

    **``ctlDvCd``/``frcSaleRsnCont`` DO NOT SELECT THE 발상역 변경 PATH.**
    They are the two extra scalars that path sends, and they are exposed
    because they are real ``@Field``s of this route — but nothing else about
    that path is reproduced here. ``SeatSearchActivity.java:793,820`` writes
    ``jrnyTpCd`` as ``"21"``/``"22"`` (``K4/e`` STANDING_SEAT_1/2, not
    ``"11"``/``"14"``), rebuilds the ``RJrny`` block out of a
    ``StartStationDto`` whose station orders are the ``chgBf``/``exs`` pairs
    rather than the train's own, and indexes ``RSrcar`` off a TRAIN index
    (``:780-782``, ``:845-850``) instead of a leg. Setting these two on an
    ordinary request produces a form the app never sends. Treat 발상역 변경 as
    NOT IMPLEMENTED.

    **THE THREE OMITTED FIELDS ARE OMITTED, NOT BLANK.** ``tmpJobSqno``,
    ``ctlDvCd`` and ``frcSaleRsnCont`` are ``null`` on the ordinary path and
    Retrofit drops a null ``@Field`` outright — ``RequestBuilder.smali:1510``
    is ``if-eqz v4, :cond_16`` at the head of the ``@Field`` branch, and
    ``:cond_16``/``:goto_a`` (``:2086-2087``) is the argument loop's own head.
    Sending them as ``""`` would be a different request.

    **VERIFIED FROM THE APK: the route, the method, all fifteen ``@Field``
    names, the six ``@FieldMap`` identities and their order, every map's key
    prefix and index arity, and the constant values above.**

    **NEVER TRANSMITTED.** No account this project can reach holds a paid
    ticket it is willing to have changed, so nothing here has been sent, by
    this package or under observation. A live call re-books a paid ticket and
    commits the holder to a settlement; treat the first one as an experiment
    and be ready to undo it with
    :meth:`~korail_mobile_api.KorailClient.roll_back_trip_change`.
    """
    if type(request) is not TripChangeReservationRequest:
        raise KorailProtocolError(
            "KORAIL ticket change requires an exact "
            "TripChangeReservationRequest"
        )
    tickets = tuple(request.original_tickets)
    legs = tuple(request.legs)
    passengers = tuple(request.passengers)
    if not tickets or len(tickets) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            "KORAIL ticket change needs 1 to "
            f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} original tickets"
        )
    if not legs or len(legs) > KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            f"KORAIL ticket change needs 1 to {KORAIL_MAX_JOURNEY_LEGS} legs"
        )
    if not passengers or len(passengers) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            "KORAIL ticket change needs 1 to "
            f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} passengers"
        )
    recalculate = request.recalculate_fare
    job_sequence = request.temporary_job_sequence
    if recalculate and not (
        isinstance(job_sequence, str) and job_sequence.strip()
    ):
        # C5/d.java:144-145 sets the two together: the re-price call names the
        # PNR it is re-pricing. A "Y" without one is a request the app never
        # makes.
        raise KorailProtocolError(
            "KORAIL ticket change re-price needs the temporary_job_sequence "
            "returned by the first call"
        )
    if not recalculate and job_sequence is not None:
        raise KorailProtocolError(
            "KORAIL ticket change sends temporary_job_sequence only with "
            "recalculate_fare=True (C5/d.java:136-137)"
        )

    form = _common_fields(config)
    form["trvlKndCd"] = _TRIP_CHANGE_TRAVEL_KIND_CODE
    form["totPrnb"] = str(len(tickets))
    form["isePrnb"] = str(len(tickets))
    form["stndSeatFlg"] = _required_trip_change_text(
        request.standing_seat_flag,
        field="standing_seat_flag",
    )
    form["intgTktIseFlg"] = _TRIP_CHANGE_INTEGRATED_TICKET_FLAG
    form["prcFareReCalcFlg"] = "Y" if recalculate else "N"
    if job_sequence is not None:
        form["tmpJobSqno"] = job_sequence
    form["alcSeatDmnPsDvCd"] = _TRIP_CHANGE_SEAT_DEMAND_CODE
    form["jrny2Cnt"] = _TRIP_CHANGE_SECOND_JOURNEY_COUNT
    form["psg2Cnt"] = _TRIP_CHANGE_SECOND_JOURNEY_COUNT
    if request.control_division_code is not None:
        form["ctlDvCd"] = _required_trip_change_text(
            request.control_division_code,
            field="control_division_code",
        )
    if request.forced_sale_reason is not None:
        form["frcSaleRsnCont"] = _required_trip_change_text(
            request.forced_sale_reason,
            field="forced_sale_reason",
        )

    # --- FieldMap 1/6: RJrny (C5/d.java:43-89) -----------------------------
    journey_type = (
        KORAIL_DIRECT_JOURNEY_TYPE_CODE
        if len(legs) == 1
        else KORAIL_TRANSFER_JOURNEY_TYPE_CODE
    )
    form["jrnyCnt"] = _zero_padded(len(legs), width=4)
    for index, leg in enumerate(legs, start=1):
        if type(leg) is not TripChangeLeg:
            raise KorailProtocolError(
                "KORAIL ticket change requires exact TripChangeLeg values"
            )
        form[f"jrnySqno_{index}"] = _TRIP_CHANGE_JOURNEY_SEQUENCE_NOS[index - 1]
        form[f"jrnyTpCd_{index}"] = journey_type
        form[f"trnNo_{index}"] = _zero_padded(
            int(_required_digits(leg.train_no, field="train_no")),
            width=5,
        )
        for wire_name, attribute in _TRIP_CHANGE_JOURNEY_FIELDS:
            form[f"{wire_name}{index}"] = _required_trip_change_text(
                getattr(leg, attribute),
                field=attribute,
            )

    # --- FieldMap 2/6: RSrcar (C5/d.java:90,109-111) -----------------------
    # Empty by default: the journey screen clears it and only a seat pick
    # refills it. The count key is srcarCnt_ on this branch, NOT scarCnt_
    # (SeatSearchActivity.java:660 vs :658).
    seats_by_leg: dict[int, list[TripChangeSeatAssignment]] = {}
    for seat in request.seats:
        if type(seat) is not TripChangeSeatAssignment:
            raise KorailProtocolError(
                "KORAIL ticket change requires exact "
                "TripChangeSeatAssignment values"
            )
        if type(seat.leg) is not int or not 1 <= seat.leg <= len(legs):
            raise KorailProtocolError(
                "KORAIL ticket change seat names a leg that is not in the "
                "request"
            )
        seats_by_leg.setdefault(seat.leg, []).append(seat)
    for leg_index in sorted(seats_by_leg):
        leg_seats = seats_by_leg[leg_index]
        form[f"srcarCnt_{leg_index}"] = str(len(leg_seats))
        for seat_index, seat in enumerate(leg_seats, start=1):
            form[f"scarNo_{leg_index}_{seat_index}"] = (
                _required_trip_change_text(seat.car_no, field="car_no")
            )
            form[f"seatNo_{leg_index}_{seat_index}"] = (
                _required_trip_change_text(seat.seat_no, field="seat_no")
            )

    # --- FieldMap 3/6: RSeat (w4/b.java:156-171 then C5/d.java:69-75) ------
    # seatCnt_N is written TWICE by the app and the second write wins: "1"/"2"
    # from w4/b.java:164, then addZero(4, len(legs)) from C5/d.java:69. The two
    # loops agree on their bound -- w4/b.java:160 uses the ORIGINAL ticket's
    # journey type and C5/d.java:47 the selected trains, and TCBookingActivity
    # sends a direct original to the direct inquiry and a transfer original to
    # the transfer one (:274 -> :93), so a replacement has the original's leg
    # count.
    #
    # THE ORDER INSIDE THIS MAP IS THE ONE PLACE THE TWO BUILDERS INTERLEAVE.
    # RSeat is a LinkedHashMap, and re-putting an existing key keeps its
    # ORIGINAL position while a new key is appended. So of C5/d.java's three
    # writes per leg (:69,70,72/74) only roomClsfCd_ is new: seatCnt_ and
    # rqSeatAttCd_ land back where w4/b.java:164,168 first put them, which is
    # why rqSeatAttCd_ sits BETWEEN locSeatAttCd_ and etcSeatAttCd_ rather
    # than after them, and why every roomClsfCd_ key comes after EVERY leg's
    # block rather than inside its own.
    for index, leg in enumerate(legs, start=1):
        form[f"seatCnt_{index}"] = _zero_padded(len(legs), width=4)
        for prefix, code in _TRIP_CHANGE_SEAT_OPTION_CODES:
            form[f"{prefix}{index}_1"] = code
        form[f"rqSeatAttCd_{index}_1"] = _required_trip_change_text(
            leg.seat_attribute_code,
            field="seat_attribute_code",
        )
        form[f"etcSeatAttCd_{index}_1"] = _TRIP_CHANGE_ETC_SEAT_ATTRIBUTE_CODE
    for index, leg in enumerate(legs, start=1):
        form[f"roomClsfCd_{index}_1"] = _required_trip_change_text(
            leg.room_class_code,
            field="room_class_code",
        )

    # --- FieldMap 4/6: RPsg (w4/b.java:174-289) ----------------------------
    form["psgCnt"] = str(len(passengers))
    for index, passenger in enumerate(passengers, start=1):
        if type(passenger) is not TripChangePassenger:
            raise KorailProtocolError(
                "KORAIL ticket change requires exact TripChangePassenger "
                "values"
            )
        form[f"psgInfoPerPrnb_{index}"] = _required_trip_change_text(
            passenger.passengers_per_person,
            field="passengers_per_person",
        )
        form[f"psgTpDvCd_{index}"] = _required_trip_change_text(
            passenger.passenger_type_code,
            field="passenger_type_code",
        )

    # --- FieldMap 5/6: ROrtg (w4/b.java:143-155) ---------------------------
    form["ortgCnt"] = _zero_padded(len(tickets), width=4)
    for index, ticket in enumerate(tickets, start=1):
        if type(ticket) is not TripChangeOriginalTicket:
            raise KorailProtocolError(
                "KORAIL ticket change requires exact TripChangeOriginalTicket "
                "values"
            )
        for wire_name, attribute in _TRIP_CHANGE_ORIGINAL_TICKET_FIELDS:
            form[f"{wire_name}{index}"] = _required_trip_change_text(
                getattr(ticket, attribute),
                field=attribute,
            )

    # --- FieldMap 6/6: RDscp (W4/b.smali rel. 816-824, a6/C1043C.java) -----
    # dscpCnt_N is UNCONDITIONAL, even at zero: the tail of W4.b.b writes
    # rDscp2.setDscpCnt(index, addZero(4, count)) on every passenger, and
    # a6/C1043C.java:100 parses it back for every passenger.
    for index, passenger in enumerate(passengers, start=1):
        discounts = tuple(passenger.discounts)
        form[f"dscpCnt_{index}"] = _zero_padded(len(discounts), width=4)
        for row, discount in enumerate(discounts, start=1):
            if type(discount) is not TripChangeDiscount:
                raise KorailProtocolError(
                    "KORAIL ticket change requires exact TripChangeDiscount "
                    "values"
                )
            form[f"dcntKndCd_{index}_{row}"] = _required_trip_change_text(
                discount.discount_kind_code,
                field="discount_kind_code",
            )
            if discount.certificate_no:
                form[f"dscpNo_{index}_{row}"] = discount.certificate_no
            delay = (
                discount.delay_window_no,
                discount.delay_sale_date,
                discount.delay_sale_sequence,
                discount.delay_return_password,
            )
            if any(delay):
                # a6/C1043C.java:161-164 writes all four together or none;
                # a partial 지연할인증 return number identifies no ticket.
                if not all(delay):
                    raise KorailProtocolError(
                        "KORAIL ticket change 지연할인증 needs all four of "
                        "delay_window_no / delay_sale_date / "
                        "delay_sale_sequence / delay_return_password"
                    )
                form[f"dlayOgtkWctNo_{index}_{row}"] = discount.delay_window_no
                form[f"dlayOgtkSaleDd_{index}_{row}"] = discount.delay_sale_date
                form[f"dlayOgtkSaleSqno_{index}_{row}"] = (
                    discount.delay_sale_sequence
                )
                form[f"dlayOgtkRetPwd_{index}_{row}"] = (
                    discount.delay_return_password
                )
    return form


def build_trip_change_rollback_form(
    config: KorailConfig,
    lump_settlement_target_nos: Sequence[str],
) -> dict[str, str]:
    """``ticket.tripChgHndgCnc.do`` — undo a 여행변경 that was never settled.

    The whole request is the common three, a count, and ONE ``@FieldMap``
    (``TicketService.java:98-100``). ``TCCancelDao.TCCancelRequest``
    (``:12-35``) is a ``lumpStlCnt`` plus a ``HashMap`` whose only writer is
    ``setLumpStlTgtNo(int, String)`` at ``:32-34``, spelling the key
    ``"lumpStlTgtNo_" + index``.

    Both call sites send exactly one target, 1-INDEXED — ``a6/x.java:111-112``
    and ``DReservationConfirmActivity.java:285-286``, each
    ``setLumpStlCnt("1")`` then ``setLumpStlTgtNo(1, ...)``. A list is accepted
    here because the field is a count and a map rather than a scalar, but the
    only shape ever observed is a single target.

    ``lumpStlCnt`` is derived from the list length rather than taken as a
    parameter: it is the count of the map beside it, and the two disagreeing is
    not a request any app path can produce.

    **NOT VERIFIED: the response.** ``TicketService.java:98`` declares a bare
    ``BaseResponse``, so what a successful rollback answers with beyond the
    common ``h_msg_cd``/``h_msg_txt`` is unknown. Nothing here has ever been
    transmitted.
    """
    targets = tuple(lump_settlement_target_nos)
    if not targets or len(targets) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            "KORAIL ticket change rollback needs 1 to "
            f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} settlement targets"
        )
    form = _common_fields(config)
    form["lumpStlCnt"] = str(len(targets))
    for index, target in enumerate(targets, start=1):
        form[f"lumpStlTgtNo_{index}"] = _required_trip_change_text(
            target,
            field="lump settlement target no",
        )
    return form


#: The six passenger counters ``w4/a.java:164-235`` actually reads, in the
#: order it reads them, with the ``psgTpDvCd`` and the ``RDscp`` row each one
#: writes. The two absentees are the point: 청소년 (TEENAGER) and 안내견
#: (GUIDE_DOG) are offered by the picker and IGNORED by this builder, so a mix
#: containing either cannot be sent on this route.
_RESERVATION_CHANGE_PASSENGER_ROWS: tuple[
    tuple[str, str, str, str | None], ...
] = (
    ("adult", "1", "0", None),  # w4/a.java:164-177 어른
    ("child", "3", "0", None),  # :178-188 어린이
    ("infant", "3", "1", "321"),  # :189-200 동반유아
    ("senior", "1", "1", "131"),  # :201-212 경로
    ("severe_disability", "1", "1", "111"),  # :213-224 1~3급 장애
    ("mild_disability", "1", "1", "112"),  # :225-235 4~6급 장애
)

#: ``RJrny`` keys ``w4/a.java:142-153`` writes per leg, in order, AFTER the
#: zero-padded train number. Four keys the trip-change route sends are missing
#: here because this builder never writes them.
_RESERVATION_CHANGE_JOURNEY_FIELDS: tuple[tuple[str, str], ...] = (
    ("runDt_", "departure_date"),
    ("stlbTrnClsfCd_", "train_classification_code"),
    ("trnGpCd_", "train_group_code"),
    ("dptDt_", "departure_date"),
    ("dptTm_", "departure_time"),
    ("dptRsStnCd_", "departure_station_code"),
    ("dptStnConsOrdr_", "departure_station_consecutive_order"),
    ("arvRsStnCd_", "arrival_station_code"),
    ("arvStnConsOrdr_", "arrival_station_consecutive_order"),
)


def build_reservation_passenger_change_form(
    config: KorailConfig,
    request: ReservationPassengerChangeRequest,
) -> dict[str, str]:
    """``reservation.reservationChange.do`` — re-mix a held PNR's passengers.

    Eleven ``@Field``s then FIVE ``@FieldMap``s. The route is declared TWICE,
    byte-identically — ``BusReservationService.java:23-25`` and
    ``ReservationCancelService.java:23-25`` — and only the second is bound:
    ``ReservationChangeDao.executeDao`` (``:164-166``) asks for
    ``ReservationCancelService``. The duplicate declaration changes nothing on
    the wire.

    The five maps' identity comes from that same ``executeDao`` argument order:
    ``getRJrny()``, ``getRSrcar()``, ``getRSeat()``, ``getRPsg()``,
    ``getRDscp()``. Note that ``ROrtg`` is absent — this route re-mixes a hold
    that has not been paid for, so there is no 원표 to stake.

    **``psgCnt`` REACHES THE WIRE EXACTLY ONCE, FROM THE MAP.** The eleventh
    ``@Field`` is declared as ``@Field(RPsg.PSG_CNT)``, i.e. literally
    ``"psgCnt"`` (``RPsg.java:7``), and it would collide with the ``RPsg``
    map's own ``psgCnt`` key — except that ``ReservationChangeRequest.setPsgCnt``
    (``ReservationChangeDao.java:114-116``) has NO call site anywhere in
    v6.5.0. The scalar is therefore always null and Retrofit drops it
    (``RequestBuilder.smali:1510``), leaving ``rPsg.setPsgCnt``
    (``w4/a.java:163``) as the only writer. This builder emits it once, in the
    map's position.

    The other four scalars beside the PNR are pinned by ``w4/a.java:131-134``:
    ``stndFlg``, ``evntWctFlg``, ``wctHndgCncDvCd`` and ``lrgCrgFlg`` are all
    ``"N"`` on every path. ``totPrnb`` (``:130``) is the picker's total.

    ``jrnyCnt`` is ECHOED, not recomputed: ``w4/a.java:137`` passes the
    reservation's own ``h_jrny_cnt`` through, so it is not zero-padded the way
    the trip-change route's is.

    **VERIFIED FROM THE APK: the route, both declarations, the eleven
    ``@Field`` names, the five ``@FieldMap`` identities and order, every key
    prefix, and that ``psgCnt`` has exactly one writer.**

    **NEVER TRANSMITTED.** No live-test path in this repository sends it.
    """
    if type(request) is not ReservationPassengerChangeRequest:
        raise KorailProtocolError(
            "KORAIL reservation passenger change requires an exact "
            "ReservationPassengerChangeRequest"
        )
    legs = tuple(request.legs)
    if not legs or len(legs) > KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            "KORAIL reservation passenger change needs 1 to "
            f"{KORAIL_MAX_JOURNEY_LEGS} legs"
        )
    counts = request.passengers
    if type(counts) is not KorailPassengerCounts:
        raise KorailProtocolError(
            "KORAIL reservation passenger change requires an exact "
            "KorailPassengerCounts"
        )
    if counts.teenager or counts.guide_dog:
        raise KorailProtocolError(
            "KORAIL reservation passenger change cannot carry 청소년 or "
            "안내견: w4/a.java:164-235 reads only the other six counters, so "
            "the row block would not match totPrnb"
        )

    form = _common_fields(config)
    form["pnrNo"] = _required_trip_change_text(request.pnr_no, field="pnr_no")
    form["chgTno"] = _required_trip_change_text(
        request.reservation_change_no,
        field="reservation_change_no",
    )
    form["totPrnb"] = str(counts.total)
    form["stndFlg"] = "N"
    form["evntWctFlg"] = "N"
    form["wctHndgCncDvCd"] = "N"
    form["lrgCrgFlg"] = "N"

    # --- FieldMap 1/5: RJrny (w4/a.java:137-153) ---------------------------
    form["jrnyCnt"] = _required_trip_change_text(
        request.journey_count,
        field="journey_count",
    )
    for index, leg in enumerate(legs, start=1):
        if type(leg) is not ReservationPassengerChangeLeg:
            raise KorailProtocolError(
                "KORAIL reservation passenger change requires exact "
                "ReservationPassengerChangeLeg values"
            )
        form[f"jrnySqno_{index}"] = _required_trip_change_text(
            leg.journey_sequence_no,
            field="journey_sequence_no",
        )
        form[f"jrnyTpCd_{index}"] = _required_trip_change_text(
            leg.journey_type_code,
            field="journey_type_code",
        )
        form[f"trnNo_{index}"] = _zero_padded(
            int(_required_digits(leg.train_no, field="train_no")),
            width=5,
        )
        for wire_name, attribute in _RESERVATION_CHANGE_JOURNEY_FIELDS:
            form[f"{wire_name}{index}"] = _required_trip_change_text(
                getattr(leg, attribute),
                field=attribute,
            )

    # --- FieldMap 2/5: RSrcar (w4/a.java:154) ------------------------------
    # scarCnt_, NOT srcarCnt_ (RSrcar.java:7,12-14), and always "0": this route
    # never designates a seat.
    for index in range(1, len(legs) + 1):
        form[f"scarCnt_{index}"] = "0"

    # --- FieldMap 3/5: RSeat (w4/a.java:156-158) ---------------------------
    # seatPsrmClCd_, NOT roomClsfCd_ -- the other trip-change route spells the
    # same idea the other way (RSeat.java:10,13).
    for index, leg in enumerate(legs, start=1):
        form[f"seatCnt_{index}"] = "1"
        form[f"seatPsrmClCd_{index}_1"] = _required_trip_change_text(
            leg.room_class_code,
            field="room_class_code",
        )
        form[f"rqSeatAttCd_{index}_1"] = _required_trip_change_text(
            leg.seat_attribute_code,
            field="seat_attribute_code",
        )

    # --- FieldMap 4/5: RPsg and 5/5: RDscp (w4/a.java:161-235) -------------
    # One RPsg row and one RDscp row per PERSON, both 1-based and sharing the
    # same running index, emitted in the counter order w4/a.java walks. The
    # RDscp counts here are bare "0"/"1", not the zero-padded "0000"/"0001"
    # the trip-change route sends -- w4/a.java:171 writes the literal string.
    form["psgCnt"] = str(counts.total)
    person = 0
    discount_rows: dict[str, str] = {}
    for attribute, type_code, discount_count, discount_code in (
        _RESERVATION_CHANGE_PASSENGER_ROWS
    ):
        for _ in range(getattr(counts, attribute)):
            person += 1
            form[f"psgInfoPerPrnb_{person}"] = "1"
            form[f"psgTpDvCd_{person}"] = type_code
            discount_rows[f"dscpCnt_{person}"] = discount_count
            if discount_code is not None:
                discount_rows[f"dcntKndCd_{person}_1"] = discount_code
    form.update(discount_rows)
    return form
