from __future__ import annotations

import re
from collections.abc import Sequence

from .config import KorailConfig
from .constants import (
    KORAIL_STANDBY_WAIT_FLAG,
    KorailReservationJobType,
    KorailSeatClass,
)
from .errors import KorailProtocolError
from .models import TrainSummary
from .mutation_models import (
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
    """Check the designated-seat list against the job type and the mix.

    A seat list belongs to ``"1103"`` and to nothing else: the app switches the
    job id to ``"1103"`` in the same three lines that install the ``OSrcar``
    map (``C5/a.java:143-146``), and clears that map whenever it rebuilds an
    ordinary ``"1101"`` journey (``C5/a.java:118``).

    The count rule is the app's own: ``SeatSearchActivity.java:902`` enables
    "선택완료" only while ``selectedSeatCount == G0()``, and ``G0()``
    (``:273-278``) is the request's ``txtTotPsgCnt``. A short list is refused
    here, before anything is sent, because the server would otherwise be asked
    to seat N passengers in fewer than N seats.
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

    Only the single-adult, general-class, ``"1101"`` shape has ever been sent to
    the live server. Multi-passenger and 특실 forms, and both non-default job
    types, are built from the app's own request builder but are NOT
    live-verified.
    """
    if type(train) is not TrainSummary:
        raise KorailProtocolError(
            "KORAIL reservation requires an exact TrainSummary"
        )
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif type(passengers) is not KorailPassengerCounts:
        raise KorailProtocolError(
            "KORAIL reservation requires an exact KorailPassengerCounts"
        )
    try:
        seat_class = KorailSeatClass(seat_class)
    except ValueError:
        raise KorailProtocolError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        ) from None
    try:
        job_type = KorailReservationJobType(job_type)
    except ValueError:
        raise KorailProtocolError(
            "KORAIL reservation job type must be one of "
            + ", ".join(
                f'"{member.value}"' for member in KorailReservationJobType
            )
        ) from None
    assignments = _validated_seat_assignments(
        seats,
        job_type=job_type,
        passenger_total=passengers.total,
    )
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
    # The train list checks the availability code of the cabin the user picked,
    # not always the general one: a5/u.java:319 reads h_gen_rsv_cd for the
    # standard tab and h_spe_rsv_cd for the suite tab (likewise
    # DirectInquiryActivity.java:198). Keep this package's stricter rule -- only
    # an explicit "11" counts as available -- and apply it to whichever cabin is
    # being booked.
    elif seat_class is KorailSeatClass.SPECIAL:
        if train.special_reservation_code != "11":
            raise KorailProtocolError(
                "KORAIL reservation requires an evidenced available special seat"
            )
    elif train.general_reservation_code != "11":
        raise KorailProtocolError(
            "KORAIL reservation requires an evidenced available general seat"
        )

    train_no = _required_digits(train.train_no, field="train_no")
    train_group_code = _required_digits(
        train.train_group_code,
        field="train_group_code",
    )
    train_class_code = _required_digits(
        train.train_class_code,
        field="train_class_code",
    )
    run_date = _required_pattern(
        train.run_date,
        field="run_date",
        pattern=_DATE_RE,
    )
    departure_date = _required_pattern(
        train.departure_date,
        field="departure_date",
        pattern=_DATE_RE,
    )
    departure_time = _required_pattern(
        train.departure_time,
        field="departure_time",
        pattern=_TIME_RE,
    )
    arrival_time = _required_pattern(
        train.arrival_time,
        field="arrival_time",
        pattern=_TIME_RE,
    )
    departure_station_code = _required_digits(
        train.departure_station_code,
        field="departure_station_code",
    )
    arrival_station_code = _required_digits(
        train.arrival_station_code,
        field="arrival_station_code",
    )
    departure_construction_order = _required_digits(
        train.departure_construction_order,
        field="departure_construction_order",
    )
    arrival_construction_order = _required_digits(
        train.arrival_construction_order,
        field="arrival_construction_order",
    )
    departure_run_order = _required_digits(
        train.departure_run_order,
        field="departure_run_order",
    )
    arrival_run_order = _required_digits(
        train.arrival_run_order,
        field="arrival_run_order",
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
            "txtStndFlg": _standing_flag(train, seat_class=seat_class),
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
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            # OSeat.PSRM_CL_CD + journey number (OSeat.java:8,16-18), set from
            # the user's chosen tab: c5/b.java:72 passes
            # U4/a.java:88's GENERAL("1")/SPECIAL("2").
            "txtPsrmClCd1": seat_class.value,
            "txtJrnyCnt": "1",
            "txtJrnyTpCd1": "11",
            "txtJrnySqno1": "001",
            "txtTrnNo1": train_no,
            "txtTrnClsfCd1": train_class_code,
            "txtTrnGpCd1": train_group_code,
            "txtRunDt1": run_date,
            "txtDptDt1": departure_date,
            "txtDptTm1": departure_time,
            "arvTm_1": arrival_time,
            "txtDptRsStnCd1": departure_station_code,
            "txtDptStnConsOrdr1": departure_construction_order,
            "txtDptStnRunOrdr1": departure_run_order,
            "txtArvRsStnCd1": arrival_station_code,
            "txtArvStnConsOrdr1": arrival_construction_order,
            "txtArvStnRunOrdr1": arrival_run_order,
            "txtChgFlg1": "N",
        }
    )
    # OSrcar is the LAST @FieldMap on the Retrofit call
    # (CertificationService.java:52-54), so its keys go after the journey keys.
    # For "1101"/"1102" the map is empty and contributes nothing at all --
    # C5/a.java:118 clears it while building an ordinary journey -- which is why
    # a txtSrcarCnt of "0" never appears on the wire.
    #
    # The order below is SeatSearchActivity.java:676-682's: the count, then
    # (car, seat) per index. The app itself cannot guarantee it -- :650 collects
    # into a plain HashMap and :144 of C5/a.java putAll()s that back into the
    # LinkedHashMap -- so KORAIL demonstrably tolerates any OSrcar ordering, and
    # emitting the builder's own order is the reproducible choice.
    for index, assignment in enumerate(assignments, start=1):
        if index == 1:
            # SeatSearchActivity.java:676. The count is the SEAT count, and the
            # key is unsuffixed for journey 1 (OSrcar.java:21-23 selects
            # "txtSrcarCnt" vs "txtSrcarCnt1" on the journey index, not the seat
            # index).
            form["txtSrcarCnt"] = str(len(assignments))
        form[f"txtSrcarNo{index}"] = str(assignment.car_no)
        form[f"txtSeatNo{index}"] = assignment.seat_no
    return form


def _standing_flag(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
) -> str:
    """``txtStndFlg``: S4/J.java:83-84's ``isStndSeat``, verbatim.

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
    # (h_jrny_cnt="0001"), not "1". Accept any digit string that is numerically
    # one single journey; the cancel form still transmits the app's txtJrnyCnt.
    journey_count = response.journey_count
    is_single_journey = (
        isinstance(journey_count, str)
        and journey_count.strip().isdigit()
        and int(journey_count) == 1
    )
    if (
        response.str_result != "SUCC"
        or not isinstance(response.pnr_no, str)
        or not response.pnr_no.strip()
        or not is_single_journey
    ):
        raise KorailProtocolError(
            "KORAIL cancellation requires one fresh successful unpaid hold"
        )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": response.pnr_no,
            "txtJrnySqno": "0001",
            "txtJrnyCnt": "1",
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
