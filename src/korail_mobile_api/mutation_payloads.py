# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""DTO 필드·배열 순서와 빈 값 생략은 실제 전송에 영향을 주므로 유지합니다."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import TypeVar

from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KORAIL_DISCOUNT_CARD_DISCOUNT_CODE,
    KORAIL_DISCOUNT_CARD_MENU_ID,
    KORAIL_MAX_DISCOUNT_CARD_SECTIONS,
    KORAIL_MAX_JOURNEY_LEGS,
    KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    KORAIL_MERGE_SEAT_FLAGS_BY_CABIN,
    KORAIL_STANDBY_WAIT_FLAG,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
    KorailReservationJobType,
    KorailSeatClass,
)
from .errors import KorailProtocolError
from .limousine_models import LimousineSchedule
from .models import TrainSummary
from .mutation_models import (
    CardPayment,
    CartAddRequest,
    DiscountCardAdditionalUser,
    DiscountCardPurchaseRequest,
    DiscountCardSectionRequest,
    DiscountCardTicket,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
    StationRefundExecutionRequest,
)
from .read_models import (
    CartItem,
    PbpAcceptanceTicket,
    ProductDetailResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    SelfCheckInSeat,
    TrainScheduleItem,
)
from .read_payloads import self_checkin_ticket_fields

_DATE_RE = re.compile(r"[0-9]{8}")
_TIME_RE = re.compile(r"[0-9]{6}")
_DIGITS_RE = re.compile(r"[0-9]+")
_CARD_NUMBER_RE = re.compile(r"[0-9]{13,16}")
_INSTALLMENT_RE = re.compile(r"[0-9]{1,2}")
_KST = timezone(timedelta(hours=9))


def _current_year_month() -> int:
    now = datetime.now(_KST)
    return now.year * 100 + now.month


def _required_digits(value: str | None, *, field: str) -> str:
    if not isinstance(value, str) or _DIGITS_RE.fullmatch(value) is None:
        raise KorailProtocolError(f"KORAIL reservation train field {field} must be decimal digits")
    return value


def _required_pattern(
    value: str | None,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise KorailProtocolError(f"KORAIL reservation train field {field} has an invalid shape")
    return value


def _common_fields(config: KorailConfig) -> dict[str, str]:
    """CommonIn.java:381 의 lang 은 config.lang 이 None 이 아닐 때만 포함합니다. 앱의 언어 기본값은 보호돼 있습니다."""
    fields = {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


# TicketReservationIn 합성 생성자(TicketReservationIn.java:80)의 선언 순서입니다.
_RESERVATION_KEY_ORDER: tuple[str, ...] = (
    *(
        "Device",
        "Version",
        "Key",
        "lang",
        "txtMenuId",
        "txtJobId",
        "txtGdNo",
        "hidFreeFlg",
        "txtStndFlg",
        "txtTotPsgCnt",
    ),
    *("txtSeatAttCd1", "txtSeatAttCd2", "txtSeatAttCd3", "txtSeatAttCd4", "txtSeatAttCd5", "txtSeatAttCd4_1"),
    *("txtJrnyCnt", "txtSrcarCnt", "txtSrcarCnt1"),
    *(
        f"{field}{row}"
        for row in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        for field in ("txtCompaCnt", "txtPsgTpCd", "txtDiscKndCd", "txtCardNo_")
    ),
    *(
        f"{field}{journey}"
        for journey in (1, 2)
        for field in (
            *(
                "txtJrnyTpCd",
                "txtJrnySqno",
                "txtTrnNo",
                "txtTrnClsfCd",
                "txtTrnGpCd",
                "txtRunDt",
                "txtDptDt",
                "txtDptTm",
            ),
            *("txtDptRsStnCd", "txtDptStnConsOrdr", "txtDptStnRunOrdr", "txtArvRsStnCd", "txtArvStnConsOrdr"),
            *("txtArvStnRunOrdr", "txtChgFlg", "txtPsrmClCd"),
        )
    ),
    *(
        f"{prefix}{seat}"
        for prefixes in (("txtSrcarNo", "txtSeatNo"), ("txtSrcarNo1_", "txtSeatNo1_"))
        for seat in range(1, KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
        for prefix in prefixes
    ),
    *("txtMidRsStnCd", "txtMidStnConsOrdr", "txtMidStnRunOrdr"),
)


def _in_reservation_order(form: dict[str, str]) -> dict[str, str]:
    """표에 없는 키는 원래 순서대로 뒤에 둡니다."""
    ordered = {key: form[key] for key in _RESERVATION_KEY_ORDER if key in form}
    ordered.update(form)
    return ordered


# 0명 행을 제외한 뒤 연속 인덱스를 붙입니다(Passengers.java:743-752).
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


def _add_passenger_rows(form: dict[str, str], passengers: KorailPassengerCounts) -> None:
    index = 0
    for attribute, passenger_type, discount_code in _PASSENGER_ROWS:
        count = getattr(passengers, attribute)
        if count == 0:
            continue
        index += 1
        form[f"txtCompaCnt{index}"] = str(count)
        form[f"txtPsgTpCd{index}"] = passenger_type
        form[f"txtDiscKndCd{index}"] = discount_code


def _seat_attribute_code(train: TrainSummary, selected_code: str | None = None) -> str:
    # 명시한 좌석속성→조회 행→기본 선택 순서입니다(TrainScheduleViewModel.java:2914-2930,2982-2999).
    candidate = selected_code if selected_code is not None else train.seat_attribute_code or "015"
    return _required_pattern(
        candidate,
        field="seat_attribute_code",
        pattern=re.compile(r"[0-9]{3}"),
    )


def _validated_seat_assignments(
    seats: Sequence[KorailSeatAssignment] | None,
    *,
    job_type: KorailReservationJobType,
    passenger_total: int,
) -> tuple[KorailSeatAssignment, ...]:
    """앱도 좌석 목록·개수와 SEAT job 을 함께 설정합니다 (TrainSeatMapViewModel.java:2135-2138,2289). 1103 은 관측값이며 enum 평문은
    보호돼 있습니다 (ReservationJobId.java:22)."""
    if job_type is not KorailReservationJobType.SEAT_DESIGNATED:
        if seats:
            raise KorailProtocolError(
                "KORAIL designated seats belong to a seat-designated "
                f'reservation (txtJobId "1103"), not "{job_type.value}"'
            )
        return ()
    if seats is None or isinstance(seats, (str, bytes)):
        raise KorailProtocolError(
            "KORAIL seat-designated reservation requires a sequence of KorailSeatAssignment"
        )
    assignments = tuple(seats)
    for assignment in assignments:
        if not isinstance(assignment, KorailSeatAssignment):
            raise KorailProtocolError(
                "KORAIL seat-designated reservation requires exact KorailSeatAssignment values"
            )
    if len(assignments) != passenger_total:
        raise KorailProtocolError(
            "KORAIL seat-designated reservation needs exactly one seat per "
            f"passenger: {passenger_total} passenger(s), "
            f"{len(assignments)} seat(s)"
        )
    identities = {(item.car_no, item.seat_no) for item in assignments}
    if len(identities) != len(assignments):
        raise KorailProtocolError("KORAIL seat-designated reservation cannot book the same seat twice")
    return assignments


def build_reservation_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[KorailSeatAssignment] | None = None,
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """DTO 배열은 1기반이며 txtSrcarCnt는 호차 수가 아닌 좌석 수입니다(NetworkService.java:15350,15366;
    TrainSeatMapViewModel.java:2108-2113)."""
    return _build_journey_reservation_form(
        config,
        (train,),
        passengers=passengers,
        seat_classes=(seat_class,),
        job_type=job_type,
        leg_seats=None if seats is None else (seats,),
        seat_attribute_codes=(seat_attribute_code,),
    )


def build_transfer_reservation_form(
    config: KorailConfig,
    legs: Sequence[TrainSummary],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (KorailSeatClass.GENERAL),
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
    seat_attribute_codes: Sequence[str | None] | None = None,
) -> dict[str, str]:
    """앱의 환승 오버로드는 구간 수·등급· 입석 여부를 받아 같은 DTO 를 구성합니다(TrainScheduleViewModel.java:2937-3004). 두 구간 모두
    isTransfer=true 를 넘깁니다(:2968); 여정 종류 선택은 TrainScheduleOutTrainInfo.java:3674-3683 입니다."""
    return _build_journey_reservation_form(
        config,
        legs,
        passengers=passengers,
        seat_classes=seat_classes,
        job_type=job_type,
        leg_seats=seats,
        require_legs=KORAIL_MAX_JOURNEY_LEGS,
        seat_attribute_codes=seat_attribute_codes,
    )


def build_merge_reservation_form(
    config: KorailConfig,
    standing_hold_train: TrainSummary,
    merge_rows: Sequence[TrainScheduleItem],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.MERGE_STANDING,
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """첫 홀드 폼에서 입석 플래그와 중간역 세 필드만 바꿉니다(ReservationMergeViewModel.smali:7671-7774)."""
    rows = tuple(merge_rows) if not isinstance(merge_rows, (str, bytes)) else ()
    if not rows or not all(isinstance(row, TrainScheduleItem) for row in rows):
        raise KorailProtocolError("KORAIL 병합 reservation requires the research.mergeSeatsC.do rows")
    hold_train_no = _required_digits(standing_hold_train.train_no, field="train_no")
    for row in rows:
        if _required_digits(row.train_no, field="train_no") != hold_train_no:
            raise KorailProtocolError(
                "KORAIL 병합 reservation splits ONE train: every merge row must "
                f"carry the standing hold's train_no {hold_train_no!r}"
            )
        # 행별 h_run_dt 는 관측에 있었지만 없는 행도 받습니다. 있으면 다른 날 조회한 행을 거절합니다.
        if row.run_date is not None and row.run_date != standing_hold_train.run_date:
            raise KorailProtocolError(
                f"KORAIL 병합 reservation merge rows must share the standing hold's run_date "
                f"{standing_hold_train.run_date!r}"
            )
    first, last = rows[0], rows[-1]
    middle = {
        "txtMidRsStnCd": first.arrival_station_code,
        "txtMidStnConsOrdr": first.arrival_construction_order,
        "txtMidStnRunOrdr": first.arrival_run_order,
    }
    missing = [key for key, value in middle.items() if not value]
    if missing:
        raise KorailProtocolError(f"KORAIL 병합 reservation first merge row lacks {', '.join(missing)}")
    form = build_reservation_form(
        config,
        standing_hold_train,
        passengers=passengers,
        seat_class=seat_class,
        job_type=job_type,
        seat_attribute_code=seat_attribute_code,
    )
    standing = any(
        row.general_reservation_code == "13" and row.standing_reservation_code == "11" for row in (first, last)
    )
    form["txtStndFlg"] = "Y" if standing else "N"
    form.update({key: str(value) for key, value in middle.items()})
    return _in_reservation_order(form)


#: 앱 상수 DEFINE_SRCARNO(AirportBusSeatMapViewModel.java:101)는 보호된 4바이트이며 좌석 조회와 예약에 같은 값을 씁니다(:766-783,853,865).
LIMOUSINE_CAR_NO = "0001"


def build_limousine_reservation_form(
    config: KorailConfig,
    schedule: LimousineSchedule,
    seat_nos: Sequence[str],
    *,
    passengers: KorailPassengerCounts | None = None,
    car_no: str = LIMOUSINE_CAR_NO,
) -> dict[str, str]:
    """같은 예약 DTO를 쓰되 구성순서는 보내지 않으며 보호된 기본값은 관측값입니다(AirportBusSeatMapViewModel.java:752-788)."""
    if not isinstance(schedule, LimousineSchedule):
        raise KorailProtocolError("KORAIL airport bus reservation requires a LimousineSchedule")
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif not isinstance(passengers, KorailPassengerCounts):
        raise KorailProtocolError("KORAIL reservation requires an exact KorailPassengerCounts")
    if passengers.total - passengers.adult - passengers.child:
        raise KorailProtocolError("KORAIL airport bus passengers can only be adults and children")
    if isinstance(seat_nos, (str, bytes)) or not isinstance(seat_nos, Sequence):
        raise KorailProtocolError("seat_nos must be a sequence of seat numbers")
    seats = tuple(
        _required_mutation_text(seat, field="seat_no", context="airport bus reservation") for seat in seat_nos
    )
    if len(seats) != passengers.total:
        raise KorailProtocolError("KORAIL airport bus reservation needs exactly one seat per passenger")
    # 앱은 seat_no 를 토글하므로 같은 좌석을 두 번 선택할 수 없습니다(AirportBusSeatMapViewModel.java:1996-2038).
    if len(set(seats)) != len(seats):
        raise KorailProtocolError("KORAIL airport bus reservation requires distinct seat numbers")
    remaining = schedule.general_remaining_seat_count
    # 앱은 잔여석이 인원보다 적은 행을 고를 수 없게 합니다(AirportBusScheduleViewModel.java:407-426).
    if isinstance(remaining, str) and remaining.isdigit() and int(remaining) < passengers.total:
        raise KorailProtocolError("KORAIL airport bus schedule has fewer remaining seats than passengers")
    context = "airport bus reservation"
    journey = {
        "txtTrnNo1": _required_mutation_text(schedule.train_no, field="train_no", context=context),
        "txtTrnClsfCd1": _required_mutation_text(
            schedule.train_class_code, field="train_class_code", context=context
        ),
        "txtTrnGpCd1": _required_mutation_text(schedule.service_code, field="service_code", context=context),
        "txtRunDt1": _required_pattern(schedule.run_date, field="run_date", pattern=_DATE_RE),
        "txtDptDt1": _required_pattern(schedule.departure_date, field="departure_date", pattern=_DATE_RE),
        "txtDptTm1": _required_pattern(schedule.departure_time, field="departure_time", pattern=_TIME_RE),
        "txtDptRsStnCd1": _required_digits(schedule.departure_station_code, field="departure_station_code"),
        "txtDptStnRunOrdr1": _required_digits(schedule.departure_run_order, field="departure_run_order"),
        "txtArvRsStnCd1": _required_digits(schedule.arrival_station_code, field="arrival_station_code"),
        "txtArvStnRunOrdr1": _required_digits(schedule.arrival_run_order, field="arrival_run_order"),
    }
    car = _required_mutation_text(car_no, field="car_no", context=context)
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": KorailReservationJobType.IMMEDIATE.value,
            "hidFreeFlg": "N",
            "txtStndFlg": "N",
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": KorailSeatClass.GENERAL.value,
            "txtJrnyCnt": KORAIL_DIRECT_ITINERARY_CODE,
            "txtJrnyTpCd1": KORAIL_DIRECT_JOURNEY_TYPE_CODE,
            "txtJrnySqno1": _sequence_no(KORAIL_DIRECT_ITINERARY_CODE),
            **journey,
            "txtSrcarCnt": str(len(seats)),
        }
    )
    for index, seat in enumerate(seats, start=1):
        form[_srcar_no_key(1, index)] = car
        form[_seat_no_key(1, index)] = seat
    return _in_reservation_order(form)


def is_merge_eligible(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> bool:
    """앱은 hYmsAplFlg 를 비교합니다(TrainScheduleOutTrainInfo.java:1500-1552,2842-2847,3588-3589). 앱의 보호 리터럴은 등급별 세
    개, 라이브러리는 두 개입니다."""
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("KORAIL merge eligibility requires an exact TrainSummary")
    cabin = _coerced_seat_class(seat_class)
    flag = train.merge_seat_application_flag
    if not isinstance(flag, str):
        return False
    return flag in KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[cabin.value]


def _seat_attribute_key(journey: int) -> str:
    """앱 근거: TicketReservationIn.java:80,189-191,237-239."""
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    """앱 근거: TicketReservationIn.java:80,193-195,245-247."""
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    """앱 근거: TicketReservationInSrcar.java:51,85; TicketReservationInSrcarTrailing.java:52,86. 배열 인덱스는 1부터
    붙습니다(NetworkService.java:15350,15366)."""
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    """앱 근거: TicketReservationInSrcar.java:51,81; TicketReservationInSrcarTrailing.java:52,82."""
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


_T = TypeVar("_T")


def _coerced_seat_class(value: object) -> KorailSeatClass:
    try:
        if not isinstance(value, str):
            raise ValueError(value)
        return KorailSeatClass(value)
    except ValueError:
        raise KorailProtocolError('KORAIL reservation seat class must be "1" (일반실) or "2" (특실)')


def _resolved_sequence(value: Sequence[_T], message: str) -> tuple[_T, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KorailProtocolError(message)
    return tuple(value)


def _validated_legs(
    legs: Sequence[TrainSummary],
    *,
    require: int | None,
) -> tuple[TrainSummary, ...]:
    """구간 타입·개수를 검증합니다. require=None 도 무제한이 아니라 라이브러리 최대 구간 수를 적용합니다."""
    resolved = _resolved_sequence(legs, "KORAIL reservation requires a sequence of legs")
    for leg in resolved:
        if not isinstance(leg, TrainSummary):
            raise KorailProtocolError("KORAIL reservation requires an exact TrainSummary")
    if require is not None and len(resolved) != require:
        # 후행 좌석 키는 하나입니다(TicketReservationIn.java:80; TicketReservationInSrcarTrailing.java:52). 이 모델로 세 번째 구간을
        # 표현할 수 없다는 제한이며 앱의 모든 여행 형태에 대한 주장은 아닙니다.
        raise KorailProtocolError(
            f"KORAIL 환승 reservation books exactly {require} legs, got "
            f"{len(resolved)}: the reservation form has no journey-{require + 1} "
            "spelling at all (only TicketReservationInSrcar and "
            "TicketReservationInSrcarTrailing exist, splitting on "
            '"journey 1 or not"), so a further leg would overwrite leg '
            f"{require} rather than be added"
        )
    if not resolved or len(resolved) > KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            f"KORAIL reservation carries between 1 and {KORAIL_MAX_JOURNEY_LEGS} legs, got {len(resolved)}"
        )
    return resolved


def _validated_seat_classes(
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass,
    *,
    leg_count: int,
) -> tuple[KorailSeatClass, ...]:
    """앱도 환승에서 구간별 PsrmType 을 선택합니다 (TrainScheduleViewModel.java:2952-2968;
    TicketReservationInJrny.java:69,234)."""
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
            "KORAIL reservation seat class must be a KorailSeatClass or a sequence of one per leg"
        )
    if len(candidates) != leg_count:
        raise KorailProtocolError(
            f"KORAIL reservation needs one cabin class per leg: {leg_count} leg(s), {len(candidates)} class(es)"
        )
    return tuple(_coerced_seat_class(candidate) for candidate in candidates)


def _validated_leg_seats(
    leg_seats: Sequence[Sequence[KorailSeatAssignment]] | None,
    *,
    leg_count: int,
    job_type: KorailReservationJobType,
    passenger_total: int,
) -> tuple[tuple[KorailSeatAssignment, ...], ...]:
    if leg_seats is None:
        per_leg: tuple[Sequence[KorailSeatAssignment] | None, ...] = (None,) * leg_count
    elif isinstance(leg_seats, (str, bytes)) or not isinstance(
        leg_seats,
        Sequence,
    ):
        raise KorailProtocolError(
            "KORAIL seat-designated reservation requires one sequence of KorailSeatAssignment per leg"
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
    seat_attribute_codes: Sequence[str | None] | None = None,
) -> dict[str, str]:
    """앱의 두 오버로드는 같은 DTO 를 채우지만 입력 분기는 다릅니다 (TrainScheduleViewModel.java:2849,2937;
    TicketReservationIn.java:139-179)."""
    resolved_legs = _validated_legs(legs, require=require_legs)
    if seat_attribute_codes is None:
        selected_attributes: tuple[str | None, ...] = (None,) * len(resolved_legs)
    else:
        selected_attributes = tuple(seat_attribute_codes)
        if len(selected_attributes) != len(resolved_legs):
            raise KorailProtocolError("KORAIL reservation requires one selected seat attribute per leg")
    resolved_attributes = tuple(
        _seat_attribute_code(train, selected)
        for train, selected in zip(resolved_legs, selected_attributes, strict=True)
    )
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif not isinstance(passengers, KorailPassengerCounts):
        raise KorailProtocolError("KORAIL reservation requires an exact KorailPassengerCounts")
    # 앱 인원 선택기는 이 두 조합을 고를 수 없게 합니다(PassengersBottomSheetKt.java:20715-20729,21124-21185 의
    # warningPassengerType): 유아가 있으면 유아·어린이 외 인원(안내견 포함)이 있어야 하고, 안내견은 중증·경증 장애 승객 합계를 넘을 수 없습니다.
    if passengers.infant and passengers.total - passengers.infant - passengers.child == 0:
        raise KorailProtocolError("KORAIL infant passengers require an accompanying passenger")
    if passengers.guide_dog > passengers.severe_disability + passengers.mild_disability:
        raise KorailProtocolError("KORAIL guide dogs cannot outnumber disability passengers")
    resolved_classes = _validated_seat_classes(
        seat_classes,
        leg_count=len(resolved_legs),
    )
    try:
        job_type = KorailReservationJobType(job_type)
    except ValueError:
        raise KorailProtocolError(
            "KORAIL reservation job type must be one of "
            + ", ".join(f'"{member.value}"' for member in KorailReservationJobType)
        )
    # STANDBY·MERGE_STANDING 을 단일 구간으로 제한하지 않습니다. 앱의 특실 상태에는 WAIT/STAND/FREE 반환이
    # 없습니다(TrainScheduleOutTrainInfo.java:3587-3625).
    assignments = _validated_leg_seats(
        leg_seats,
        leg_count=len(resolved_legs),
        job_type=job_type,
        passenger_total=passengers.total,
    )
    for leg, seat_class in zip(resolved_legs, resolved_classes, strict=True):
        _assert_leg_is_bookable(leg, seat_class=seat_class, job_type=job_type)
    journeys = tuple(_journey_fields(leg) for leg in resolved_legs)
    _assert_boarding_order(resolved_legs, journeys)
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": job_type.value,
            "txtGdNo": "",
            "hidFreeFlg": "N",
            # 환승은 구간별 판정의 OR 입니다 (TrainScheduleViewModel.java:2961-2967). 대기를 입석 홀드로 바꾸지 않기 위한 구분입니다.
            "txtStndFlg": (
                "N"
                if job_type is KorailReservationJobType.STANDBY
                else _itinerary_standing_flag(
                    resolved_legs,
                    seat_classes=resolved_classes,
                )
            ),
            # Passengers.java:610-616 의 전체 합계와 PassengerType.java:38-45 의 여덟 종류,
            # TrainScheduleViewModel.java:2912 참고.
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    # 속성 선언은 TicketReservationIn.java:80,139-179; 앱 평탄화는 NetworkService.java:15304-15343. 미지정 속성의 기본값은 보호돼
    # 있습니다(TicketReservationIn.java:96-100).
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): resolved_attributes[0],
            "txtSeatAttCd5": "000",
            # 객실은 구간 DTO 필드(TicketReservationInJrny.java:69,234)입니다. 앱은 평탄화 중 인덱스를
            # 붙입니다(NetworkService.java:15366).
            "txtPsrmClCd1": resolved_classes[0].value,
        }
    )
    for journey, seat_class in enumerate(resolved_classes[1:], start=2):
        # 앱도 각 행의 좌석속성을 선행/후행 필드로 전달합니다(TrainScheduleViewModel.java:2982-3004).
        form[_seat_attribute_key(journey)] = resolved_attributes[journey - 1]
        form[f"txtPsrmClCd{journey}"] = seat_class.value
    form["txtJrnyCnt"] = (
        KORAIL_DIRECT_ITINERARY_CODE if len(resolved_legs) == 1 else KORAIL_TRANSFER_ITINERARY_CODE
    )
    journey_type_code = (
        KORAIL_DIRECT_JOURNEY_TYPE_CODE if len(resolved_legs) == 1 else KORAIL_TRANSFER_JOURNEY_TYPE_CODE
    )
    _write_journey_rows(form, journeys, (journey_type_code,) * len(journeys))
    # 앱 일반 빌더는 목록·개수를 채우지 않습니다 (TrainScheduleViewModel.java:2932,3004; TicketReservationIn.java:182). 개수 필드는
    # 목록보다 앞에 선언되며(TicketReservationIn.java:80) 마지막에 순서를 맞춥니다.
    for journey, leg_assignments in enumerate(assignments, start=1):
        for index, assignment in enumerate(leg_assignments, start=1):
            if index == 1:
                # 선택 좌석 수입니다(TrainSeatMapViewModel.java:2108-2113,2136-2138). 개수 키는 구간별 두
                # 개(TicketReservationIn.java:80)입니다.
                form[_srcar_count_key(journey)] = str(len(leg_assignments))
            form[_srcar_no_key(journey, index)] = str(assignment.car_no)
            form[_seat_no_key(journey, index)] = assignment.seat_no
    return _in_reservation_order(form)


def _sequence_no(code: str) -> str:
    """관측된 001/002 를 재현하기 위한 라이브러리 포맷팅입니다. 앱은 전달받은 값을 그대로 씁니다(TrainScheduleOutTrainInfo.java:1631,3683;
    TrainScheduleViewModel.java:2968)."""
    return f"{int(code):03d}"


def _write_journey_rows(
    form: dict[str, str],
    journeys: Sequence[dict[str, str]],
    journey_type_codes: Sequence[str],
) -> None:
    """선언: TicketReservationInJrny.java:69; 구성: TrainScheduleOutTrainInfo.java:3683; 1기반 인덱스:
    NetworkService.java:15350,15366. 도착시각 키는 없습니다."""
    for journey, (fields, journey_type_code) in enumerate(
        zip(journeys, journey_type_codes, strict=True), start=1
    ):
        form[f"txtJrnyTpCd{journey}"] = journey_type_code
        form[f"txtJrnySqno{journey}"] = _sequence_no(
            KORAIL_DIRECT_ITINERARY_CODE if journey == 1 else KORAIL_TRANSFER_ITINERARY_CODE
        )
        for wire, attribute in (
            ("txtTrnNo", "train_no"),
            ("txtTrnClsfCd", "train_class_code"),
            ("txtTrnGpCd", "train_group_code"),
            ("txtRunDt", "run_date"),
            ("txtDptDt", "departure_date"),
            ("txtDptTm", "departure_time"),
            ("txtDptRsStnCd", "departure_station_code"),
            ("txtDptStnConsOrdr", "departure_construction_order"),
            ("txtDptStnRunOrdr", "departure_run_order"),
            ("txtArvRsStnCd", "arrival_station_code"),
            ("txtArvStnConsOrdr", "arrival_construction_order"),
            ("txtArvStnRunOrdr", "arrival_run_order"),
        ):
            form[f"{wire}{journey}"] = fields[attribute]
        form[f"txtChgFlg{journey}"] = "N"


def _assert_leg_is_bookable(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
    job_type: KorailReservationJobType,
) -> None:
    if job_type is KorailReservationJobType.STANDBY:
        # 앱의 특실 상태에는 WAIT 가 없습니다(TrainScheduleOutTrainInfo.java:3587-3625).
        if seat_class is not KorailSeatClass.GENERAL:
            raise KorailProtocolError("KORAIL standby (예약대기) is offered on the 일반실 cabin only")
        if train.wait_reservation_flag != KORAIL_STANDBY_WAIT_FLAG:
            raise KorailProtocolError(
                "KORAIL standby requires a train whose h_wait_rsv_flg is "
                f"{KORAIL_STANDBY_WAIT_FLAG!r}, got "
                f"{train.wait_reservation_flag!r}"
            )
        # 대기 가능 여부를 일반실 잔여좌석 코드로 막지 않습니다.
        return
    if job_type is KorailReservationJobType.MERGE_STANDING:
        if not is_merge_eligible(train, seat_class=seat_class):
            raise KorailProtocolError(_merge_ineligible_message(train, seat_class))
        # 관측: 서울→부산 열차 125 에 일반실 매진 코드 13 과 병합 플래그 A 가 함께 있었습니다. 일반 가용 코드 11 을 추가 요구하면 이 표본을 거절하게 됩니다.
        return
    # 선택 객실의 가용성을 검사합니다(TrainScheduleOutTrainInfo.java:2810,3587; TrainScheduleViewModel.java:3457-3458). 보호
    # 리터럴은 미확인입니다.
    if seat_class is KorailSeatClass.SPECIAL:
        if train.special_reservation_code != "11":
            raise KorailProtocolError("KORAIL reservation requires an evidenced available special seat")
    elif train.general_reservation_code != "11":
        # 앱은 일반 job 에서 일반실이 STAND 이면 입석 홀드를 보냅니다(TrainScheduleViewModel.java:2856-2874). 그러나 STAND 는 운행중지·대기· 병합
        # 판정을 먼저 거친 뒤에만 나오고(TrainScheduleOutTrainInfo.java:2810-2885,3557-3567) 그 비교값이 보호돼 있어, 13/11 만으로는 앱이 입석
        # 홀드를 만들 행인지 알 수 없습니다.
        raise KorailProtocolError("KORAIL reservation requires an evidenced available general seat")


def _assert_boarding_order(
    legs: Sequence[TrainSummary],
    journeys: Sequence[dict[str, str]],
) -> None:
    """앱은 환승 조회가 묶은 두 행으로만 폼을 만듭니다 (TrainScheduleViewModel.java:2952-2968). 두 역 코드가 다른 환승도 있어 역 연결은 보지 않습니다
    (TransferItinerary.transfer_station_code)."""
    for index in range(1, len(journeys)):
        earlier, later = journeys[index - 1], journeys[index]
        if (earlier["train_no"], earlier["run_date"]) == (later["train_no"], later["run_date"]):
            raise KorailProtocolError("KORAIL 환승 reservation legs must be different trains")
        departs = later["departure_date"] + later["departure_time"]
        previous = legs[index - 1]
        if departs <= earlier["departure_date"] + earlier["departure_time"] or (
            isinstance(previous.arrival_date, str)
            and isinstance(previous.arrival_time, str)
            and departs < previous.arrival_date + previous.arrival_time
        ):
            raise KorailProtocolError(
                "KORAIL 환승 reservation legs must be in boarding order: "
                "each leg departs after the previous one arrives"
            )


def _merge_ineligible_message(
    train: TrainSummary,
    seat_class: KorailSeatClass,
) -> str:
    return (
        'KORAIL 입석+좌석 (txtJobId "1202") requires a merge-eligible row: '
        "h_yms_apl_flg must be one of "
        + ", ".join(sorted(KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[seat_class.value]))
        + f" for this cabin, got {train.merge_seat_application_flag!r}"
    )


def _journey_fields(train: TrainSummary | TrainScheduleItem) -> dict[str, str]:
    """구간 입력의 12개 신원·운행 값을 읽습니다(TicketReservationInJrny.java:69). DTO 는 String 이지만 그 선언만으로 서버의 숫자·날짜 제약 부재를
    증명하지는 않습니다."""
    return {
        "train_no": _required_digits(train.train_no, field="train_no"),
        "train_group_code": _required_digits(
            train.train_group_code,
            field="train_group_code",
        ),
        # 열차종류는 0A 같은 영숫자도 관측됐으므로 숫자로 제한하지 않고 에코합니다.
        "train_class_code": _required_mutation_text(
            train.train_class_code,
            field="train_class_code",
            context="reservation train",
        ),
        **{
            attribute: _required_pattern(getattr(train, attribute), field=attribute, pattern=pattern)
            for attribute, pattern in (
                ("run_date", _DATE_RE),
                ("departure_date", _DATE_RE),
                ("departure_time", _TIME_RE),
            )
        },
        **{
            attribute: _required_digits(getattr(train, attribute), field=attribute)
            for attribute in (
                "departure_station_code",
                "arrival_station_code",
                "departure_construction_order",
                "arrival_construction_order",
                "departure_run_order",
                "arrival_run_order",
            )
        },
    }


def _itinerary_standing_flag(
    legs: Sequence[TrainSummary],
    *,
    seat_classes: Sequence[KorailSeatClass],
) -> str:
    """앱의 구간별 OR: TrainScheduleViewModel.java:2961-2967,3004."""
    flag = "N"
    for index, (train, seat_class) in enumerate(zip(legs, seat_classes, strict=True)):
        if index == 0 or flag == "N":
            flag = _standing_flag(train, seat_class=seat_class)
    return flag


def _standing_flag(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
) -> str:
    """일반실·일반좌석 매진·입석 가용 조건입니다(TrainScheduleOutTrainInfo.java:2881-2889;
    TrainScheduleViewModel.java:2870-2874,2961-2967). 13/11 은 관측값이고 TrainReservationCode.java:21,24 의 코드
    평문은 보호돼 있습니다."""
    if (
        seat_class is KorailSeatClass.GENERAL
        and train.general_reservation_code == "13"
        and train.standing_reservation_code == "11"
    ):
        return "Y"
    return "N"


# 앱은 SMS 선택 시 세 부분 전화번호를 합쳐 길이 11 을 검사합니다 (ReservationWaitApplyUiData.java:85;
# ReservationWaitViewModel.java:503-513). 서버의 문자 수용 여부는 미확인입니다.
_STANDBY_PHONE_RE = re.compile(r"[0-9]{11}")


def _successful_hold_pnr(hold: ReservationHoldResponse, *, context: str) -> str:
    """실패 메시지는 context 로 구분합니다."""
    pnr_no = hold.pnr_no
    if hold.str_result != "SUCC" or not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailProtocolError(context)
    return pnr_no


def build_standby_wait_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    *,
    allow_seat_class_change: bool = False,
    sms_notify: bool = False,
    phone_no: str | None = None,
) -> dict[str, str]:
    """SMS 선택 때만 번호를 검증하고 미선택 번호는 생략합니다(ReservationWaitViewModel.java:520-527; Json 설정은 보호됨)."""
    pnr_no = _successful_hold_pnr(
        hold,
        context="KORAIL standby options require one successful hold with a PNR",
    )
    # bool("N") 은 True 이므로 문자열 플래그를 bool 로 묵시 변환하지 않습니다.
    if not isinstance(allow_seat_class_change, bool):
        raise KorailProtocolError("allow_seat_class_change must be a bool")
    if not isinstance(sms_notify, bool):
        raise KorailProtocolError("sms_notify must be a bool")
    contact = ""
    if sms_notify:
        if not isinstance(phone_no, str) or (_STANDBY_PHONE_RE.fullmatch(phone_no) is None):
            raise KorailProtocolError("KORAIL standby SMS notification requires an 11-digit phone number")
        contact = phone_no
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtPsrmClChgFlg": "Y" if allow_seat_class_change else "N",
            "txtSmsSndFlg": "Y" if sms_notify else "N",
        }
    )
    if sms_notify:
        form["txtCpNo"] = contact  # 위에서 11자리 문자열로 확인
    return form


def build_unpaid_reservation_cancel_form(
    config: KorailConfig,
    response: ReservationHoldResponse,
) -> dict[str, str]:
    """앱도 응답 여정 수를 전달합니다 (ReservationWaitViewModel.java:398; MyReservationViewModel.java:1557). 순번·변경번호는 첫 여정
    값을 되울리고, 없을 때만 아래 대체값을 씁니다."""
    if not isinstance(response, ReservationHoldResponse):
        raise KorailProtocolError("KORAIL cancellation requires an exact reservation hold response")
    # 앱의 여정 수 에코: ReservationWaitViewModel.java:398; ReservationMergeViewModel.java:445;
    # AirportBusSeatMapViewModel.java:542; PayViewModel.java:4686,4725,4805,4847;
    # BasketTicketViewModel.java:3232; MyReservationViewModel.java:1557. 보호 리터럴은 미확인입니다.
    journey_count = response.journey_count
    legs = None
    if isinstance(journey_count, str) and journey_count.strip().isdigit():
        legs = int(journey_count)
    pnr_no = _successful_hold_pnr(
        response,
        context="KORAIL cancellation requires a fresh successful unpaid hold",
    )
    if not isinstance(journey_count, str) or legs is None or legs < 1:
        raise KorailProtocolError("KORAIL cancellation requires a fresh successful unpaid hold")
    # 7.0.6 예약목록 (MyReservationViewModel.java:1557,1566)과 결제 화면 (PayViewModel.java:4678-4686)이 그렇게 하고, 결제 화면은 값이
    # 없을 때만 AlienGuard 로 보호된 대체 리터럴(4·3바이트)을 씁니다.
    first = response.journeys[0] if response.journeys else None
    sequence = first.journey_sequence if first is not None else None
    change_no = first.reservation_change_no if first is not None else None
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtJrnySqno": sequence if sequence else "0001",
            "txtJrnyCnt": journey_count,
            # DTO 는 공통 4+고유 4필드(ReservationCancelChkIn.java:29-32,53)이나 전송 개수는 가변입니다. lang 기록 여부는 인코더 설정과 언어
            # 제공자에 따릅니다(CommonIn.java:467-474).
            "hidRsvChgNo": change_no if change_no else "000",
        }
    )
    return form


# 결제 시퀀스가 없을 때 쓰는 000000 은 라이브러리 정책이며 앱 기본값은 미확인입니다. 2026-07 라이브 2건은 시퀀스를 모두 제공했으므로 이 폴백을 검증한 표본이 아닙니다.
_ABSENT_JOB_SEQUENCE = "000000"


def _echoed_job_sequence(value: str | None) -> str:
    """홀드 시퀀스를 에코합니다(PayViewModel.java:6682-6683). 숫자로 온 값의 앞자리 0 을 복원하지 않습니다."""
    if isinstance(value, str) and value.strip():
        return value
    return _ABSENT_JOB_SEQUENCE


# 응답 첫 여정의 변경번호가 없을 때의 대체값입니다. 항상 없음으로 가정하지 않습니다. : reserve/reserve_transfer/reserve_merge/ recalculate_price 의
# 45여정 모두 해당 키가 없었고, 같은 예약을 목록으로 되읽으면 000 이었습니다. 보호 리터럴은 미확인입니다.
_ABSENT_RESERVATION_CHANGE_NO = "000"


def _echoed_reservation_change_no(hold: ReservationHoldResponse) -> str:
    # 첫 여정의 변경번호를 에코합니다(PayViewModel.java:6684).
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
    """결제액은 received_amount이며 total_price로 대체하지 않습니다(PayViewModel.java:11027-11028,11303-11307)."""
    if not isinstance(card, CardPayment):
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    if not hold.payable:
        raise KorailProtocolError(
            "KORAIL payment refuses a standby (예약대기) hold: the app saves its wait options instead of paying it"
        )
    window_no = hold.window_no
    amount = hold.received_amount
    pnr_no = _successful_hold_pnr(
        hold,
        context=(
            "KORAIL payment requires a fresh successful unpaid hold with a "
            "PNR, window number, and numeric received amount"
        ),
    )
    if (
        not isinstance(window_no, str)
        or not window_no.strip()
        or not isinstance(amount, str)
        or _DIGITS_RE.fullmatch(amount) is None
    ):
        raise KorailProtocolError(
            "KORAIL payment requires a fresh successful unpaid hold with a "
            "PNR, window number, and numeric received amount"
        )
    # 앱은 결제할 금액이 0 이면 카드 요청을 만들지 않고(PayViewModel.java:15572, 카드 입력 검사도 금액이 0 이 아닐 때만 :18144) 결제수단 없이 발권 요청을
    # 보냅니다(:5148). 라이브러리는 그 경로를 구현하지 않으므로 0원 카드 결제를 보내지 않습니다.
    if int(amount) == 0:
        raise KorailProtocolError(
            "KORAIL card payment refuses a zero-amount hold: the app issues it without a card"
        )
    # 숫자 모양 검사만으로 카드 유효성이나 비과금을 보장하지 않습니다. 앱은 앞 세 칸의 길이와 넷째 칸의 최소 길이를 검사하지만 길이 값은 보호돼
    # 있습니다(PayViewModel.java:16196-16210).
    if not isinstance(card.card_number, str) or _CARD_NUMBER_RE.fullmatch(card.card_number) is None:
        raise KorailProtocolError("KORAIL payment card number must be 13 to 16 digits")
    if not isinstance(card.installment, str) or _INSTALLMENT_RE.fullmatch(card.installment) is None:
        raise KorailProtocolError('KORAIL payment installment must be one or two digits, "0" for a lump sum')
    # 유효기간: 앱은 월 1~12 와 만료 여부(현재 yyyyMM <= 카드 yyyyMM)를 결제 전에 검사합니다(PayViewModel.java:16211-16224).
    expire = card.card_expire
    if not isinstance(expire, str) or len(expire) != 4 or _DIGITS_RE.fullmatch(expire) is None:
        raise KorailProtocolError("KORAIL payment card_expire must be YYMM digits")
    month = int(expire[2:])
    if not 1 <= month <= 12 or _current_year_month() > (2000 + int(expire[:2])) * 100 + month:
        raise KorailProtocolError("KORAIL payment card has expired or has an invalid month")
    # PayViewModel.java:16233-16243; smali:53727-53863 (국내 직접입력 카드).
    if not isinstance(card.card_password, str) or re.fullmatch(r"[0-9]{2}", card.card_password) is None:
        raise KorailProtocolError("KORAIL payment requires the first two card password digits")
    auth_length = 6 if card.card_type == "J" else 10
    if not isinstance(card.birthday, str) or re.fullmatch(rf"[0-9]{{{auth_length}}}", card.birthday) is None:
        raise KorailProtocolError("KORAIL payment card authentication value must be 6 or 10 digits")
    form = _common_fields(config)
    form.update(
        {
            "hidPnrNo": pnr_no,
            "hidWctNo": window_no,
            "hidTmpJobSqno1": _echoed_job_sequence(hold.temporary_job_sequence_1),
            "hidTmpJobSqno2": _echoed_job_sequence(hold.temporary_job_sequence_2),
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
            # 앱은 로그인 여부로 이 필드를 나눕니다 (PayViewModel.java:6600-6604; FPayViewModel.java:772-778). 양쪽 상수는 보호돼 있으며 Y
            # 가 앱의 회원 값이라는 직접 근거는 없습니다.
            "hiduserYn": "Y",
        }
    )
    return form


def _refund_echo_field(value: object, *, field: str) -> str:
    """국내 앱은 상세의 pbpAcepTgtFlg 를 전달합니다(MyTicketDetailViewModel.java:1521). 외국인 경로는 보호
    상수입니다(FTicketDetailViewModel.java:634)."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise KorailProtocolError(f"KORAIL refund {field} must be a string echoed from a prior server response")
    return value


def _app_integer(value: str | None) -> int:
    """TextHelper.getInteger 처럼 읽습니다: Integer.parseInt 이고 없거나 읽을 수 없으면 0 입니다(TextHelper.java:169-181)."""
    if value is None or re.fullmatch(r"[+-]?[0-9]+", value) is None:
        return 0
    number = int(value)
    return number if -(2**31) <= number < 2**31 else 0


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
    *,
    settle_mileage: bool = False,
    pbp_acceptance_target_flag: str | None = None,
    commission: RefundCommissionResponse | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
) -> dict[str, str]:
    """수수료 확인값을 에코하고 보호된 ctlDvCd는 추측하지 않아 생략합니다(MyTicketDetailViewModel.java:1811-1858;
    RefundTicketIn.java:66)."""
    for name, value in (
        ("pnr_no", ticket.pnr_no),
        ("sale_date", ticket.sale_date),
        ("sale_window_no", ticket.sale_window_no),
        ("sale_sequence", ticket.sale_sequence),
        ("return_password", ticket.return_password),
    ):
        _required_mutation_text(value, field=f"PaidTicket.{name}", context="refund")
    # bool("N") 변환으로 마일리지 사용 의도가 뒤집히지 않도록 bool 만 받습니다.
    if not isinstance(settle_mileage, bool):
        raise KorailProtocolError("settle_mileage must be a bool")
    pbp_flag = _refund_echo_field(
        pbp_acceptance_target_flag
        if pbp_acceptance_target_flag is not None
        else ticket.pbp_acceptance_target_flag,
        field="pbp_acceptance_target_flag",
    )
    # 키 순서는 RefundTicketIn 합성 생성자(RefundTicketIn.java:66)의 선언 순서이며 공통 필드가 맨 뒤입니다.
    form = {
        "txtPnrNo": ticket.pnr_no,
        "h_orgtk_sale_dt": ticket.sale_date,
        "h_orgtk_sale_wct_no": ticket.sale_window_no,
        "h_orgtk_sale_sqno": ticket.sale_sequence,
        "h_orgtk_ret_pwd": ticket.return_password,
        "h_mlg_stl": "Y" if settle_mileage else "N",
    }
    # 승차권 상세(MyTicketDetailViewModel.java:1521)는 위 필드만 채우고 나머지는 null 입니다.
    if commission is not None:
        if not isinstance(commission, RefundCommissionResponse):
            raise KorailProtocolError("commission must be a RefundCommissionResponse")
        # RefundTicketViewModel$executeRefundCommission$2.smali:1045-1086.
        if commission.str_result != "SUCC":
            error = KorailProtocolError("KORAIL refund requires a successful commission response")
            error.raw = commission.raw
            raise error
        if commission.ticket_return_times_division_code:
            form["tk_ret_tms_dv_cd"] = commission.ticket_return_times_division_code
        if ticket.train_no:
            form["trnNo"] = ticket.train_no
    # 진행 가능 플래그가 보호된 1글자 값과 같고 사용 가능 마일리지가 수수료 이상일 때만 묻고, 아니면 마일리지 없이
    # 환불합니다(MyTicketDetailViewModel.java:1811-1823; 환불 화면은 수수료 합계와 비교, RefundTicketViewModel.java:924-942). 플래그
    # 비교값은 보호돼 있어 보지 않습니다.
    if settle_mileage:
        if commission is None:
            raise KorailProtocolError(
                "settle_mileage=True requires the commission response (get_refund_commission)"
            )
        if _app_integer(commission.usable_mileage) < _app_integer(commission.refund_fee):
            raise KorailProtocolError(
                "KORAIL refund cannot pay the fee with mileage: usable mileage is below the fee"
            )
    form["pbpAcepTgtFlg"] = pbp_flag
    for key, coordinate in (("latitude", latitude), ("longitude", longitude)):
        if coordinate is not None:
            form[key] = str(coordinate)
    form.update(_common_fields(config))
    return form


def build_station_refund_execution_form(
    config: KorailConfig,
    request: StationRefundExecutionRequest,
) -> dict[str, str]:
    """12키는 ExecuteOnlineRefundsIn.java:60."""
    if not isinstance(request, StationRefundExecutionRequest):
        raise KorailProtocolError("KORAIL station refund requires an exact execution request")
    fields = (
        ("pnrNo", "pnr_no"),
        ("ogtkSaleDt", "original_sale_date"),
        ("ogtkSaleWctNo", "original_sale_window_no"),
        ("ogtkSaleSqno", "original_sale_sequence"),
        ("ogtkRetPwd", "original_return_password"),
        ("retDvCd", "refund_division_code"),
        ("retRsnCd", "refund_reason_code"),
        ("tkKndCd", "ticket_kind_code"),
        ("custTeln", "customer_phone"),
        ("retAmt", "refund_amount"),
        ("retFee", "refund_fee"),
        ("acepCustNm", "customer_name"),
    )
    form = _common_fields(config)
    form.update((wire_name, getattr(request, attribute)) for wire_name, attribute in fields)
    return form


def _required_mutation_text(
    value: object,
    *,
    field: str,
    context: str = "discount card request",
    allow_blank: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_blank and not value.strip()):
        raise KorailProtocolError(f"KORAIL {context} requires a non-empty {field}")
    return value


def build_discount_card_purchase_form(
    config: KorailConfig,
    request: DiscountCardPurchaseRequest,
) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 단일 FieldMap 라우트(NetworkApi.java:336-337)와
    NCardInfoIn.java:29-39, NCardjrny.java:55 의 @SerialName 을 따릅니다."""
    if not isinstance(request, DiscountCardPurchaseRequest):
        raise KorailProtocolError("KORAIL discount card purchase requires an exact DiscountCardPurchaseRequest")
    form = _common_fields(config)
    form.update(
        {
            wire: _required_mutation_text(getattr(request, attr), field=attr)
            for wire, attr in (
                ("dcntCrdKndMgNo", "card_kind_management_no"),
                ("custMgNo", "customer_no"),
                ("vlidTrmStDt", "validity_start_date"),
                ("usePsbTno", "usable_trip_count"),
            )
        }
    )
    sections = tuple(request.sections)
    if not sections or len(sections) > KORAIL_MAX_DISCOUNT_CARD_SECTIONS:
        raise KorailProtocolError(
            f"KORAIL discount card purchase needs 1 to {KORAIL_MAX_DISCOUNT_CARD_SECTIONS} sections"
        )
    form["jrnyCnt"] = str(len(sections))
    for index, section in enumerate(sections, start=1):
        if not isinstance(section, DiscountCardSectionRequest):
            raise KorailProtocolError(
                "KORAIL discount card purchase requires exact DiscountCardSectionRequest values"
            )
        for wire, attr in (
            ("jrnyTpCd", "journey_type_code"),
            ("runDt", "run_date"),
            ("trnNo", "train_no"),
            ("dptRsStnCd", "departure_station_code"),
            ("arvRsStnCd", "arrival_station_code"),
        ):
            form[f"{wire}_{index}"] = _required_mutation_text(
                getattr(section, attr),
                field=attr,
            )
    users = tuple(request.additional_users)
    # 이 입력 모델은 부가사용자 _1 키 한 묶음만 표현합니다(NCardInfoIn.java:29-39).
    if len(users) > 1:
        raise KorailProtocolError("KORAIL discount card purchase takes at most 1 additional user")
    if users:
        form["apdUsrCnt"] = str(len(users))
        for index, user in enumerate(users, start=1):
            if not isinstance(user, DiscountCardAdditionalUser):
                raise KorailProtocolError(
                    "KORAIL discount card purchase requires exact DiscountCardAdditionalUser values"
                )
            for wire, attr in (
                ("custMgNo", "customer_no"),
                ("apdCustName", "name"),
                ("apdCustTeln", "phone"),
            ):
                form[f"{wire}_{index}"] = _required_mutation_text(
                    getattr(user, attr),
                    field=f"additional user {attr}",
                )
    return form


def build_discount_card_extension_query(
    config: KorailConfig,
    ticket: DiscountCardTicket,
) -> dict[str, str]:
    """이름과 달리 POST이며 키는 속성명 추정·실서버 검증 못 함입니다(NetworkApi.java:518-520; NCardExtensionIn.java:31-34)."""
    if not isinstance(ticket, DiscountCardTicket):
        raise KorailProtocolError("KORAIL discount card extension requires an exact DiscountCardTicket")
    query = _common_fields(config)
    query.update(
        {
            wire: _required_mutation_text(getattr(ticket, attr), field=attr)
            for wire, attr in (
                ("saleWctNo", "sale_window_no"),
                ("saleDd", "sale_date"),
                ("saleSqno", "sale_sequence"),
                ("tkRetPwd", "return_password"),
            )
        }
    )
    return query


#: 일반 예약에서는 0명 행을 전송하지 않으며, N카드 홀드는 존재하는 행을 한 행으로 대체합니다.
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
    """생성만으로 예약하거나 결제하지 않습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
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
    rebuilt["txtMenuId"] = KORAIL_DISCOUNT_CARD_MENU_ID
    return _in_reservation_order(rebuilt)


# Retrofit 은 @FieldMap 뒤에 @Field 목록을 선언 순서대로 붙입니다(NetworkApi.java:584, RequestFactory.java:89-101).
_PRICE_RECALCULATION_ROW_FIELDS: tuple[tuple[str, str], ...] = (
    ("psg_tp_dv_cd", "passenger_type_code"),
    ("psrm_cl_cd", "room_class_code"),
    ("dcnt_knd_cd1", "discount_kind_code"),
    ("hidDscpNo", "certificate_no"),
    ("hidDcntKndCd", "requested_discount_code"),
    ("hidFmlyNo", "family_sequence_no"),
)

_PRICE_RECALCULATION_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("txtPsrmClCd1", "cabin_class_code"),
    ("txtSeatAttCd2", "seat_attribute_code_2"),
    ("txtSeatAttCd4", "seat_attribute_code_4"),
    ("txtSeatAttCd5", "seat_attribute_code_5"),
)


# 실서버 검증 못 함. 네 선택 스칼라는 PriceReCalculationIn.java:38-41,114-133 의 nullable 속성입니다. 키는 속성명에서 추정했으며 serializer 이름은
# 보호돼 있습니다 (PriceReCalculationIn$$serializer.java:44-47).
def build_price_recalculation_form(
    config: KorailConfig,
    request: PriceRecalculationRequest,
) -> dict[str, str | list[str]]:
    """예약 할인 재계산 요청 폼을 구성하며 전송하지 않습니다. NetworkApi.java:583-584 의 여섯 병렬 List 필드를 반복 키로 보냅니다."""
    if not isinstance(request, PriceRecalculationRequest):
        raise KorailProtocolError("KORAIL price recalculation requires an exact PriceRecalculationRequest")
    pnr_no = _required_mutation_text(request.pnr_no, field="pnr_no", context="price recalculation")
    rows = tuple(request.rows)
    if not rows or len(rows) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            f"KORAIL price recalculation needs 1 to {KORAIL_MAX_PASSENGERS_PER_RESERVATION} passenger rows"
        )

    columns: dict[str, list[str]] = {name: [] for name, _ in _PRICE_RECALCULATION_ROW_FIELDS}
    for row in rows:
        if not isinstance(row, PriceRecalculationRow):
            raise KorailProtocolError("KORAIL price recalculation requires exact PriceRecalculationRow values")
        for wire_name, attribute in _PRICE_RECALCULATION_ROW_FIELDS:
            value = getattr(row, attribute)
            # None 은 목록 전송에서 빠져 다른 병렬 목록과 인덱스가 어긋날 수 있으므로 문자열만 허용합니다.
            if type(value) is not str:
                raise KorailProtocolError(f"KORAIL price recalculation row field {attribute} must be a string")
            columns[wire_name].append(value)
        for attribute in (
            "passenger_type_code",
            "room_class_code",
            "discount_kind_code",
        ):
            if not getattr(row, attribute).strip():
                raise KorailProtocolError(
                    f"KORAIL price recalculation copies {attribute} off the held seat; it must not be empty"
                )

    form: dict[str, str | list[str]] = dict(_common_fields(config))
    form["hidPnrNo"] = pnr_no
    form["txtJobId"] = KorailReservationJobType.IMMEDIATE.value
    non_member_no = request.non_member_no
    if non_member_no is not None:
        if not isinstance(non_member_no, str) or not non_member_no.strip():
            raise KorailProtocolError(
                "KORAIL price recalculation non_member_no must be a non-empty string when present"
            )
        # 앱 속성: PriceReCalculationIn.java:32,34,114-129; 구성: PayViewModel.java:6167-6168; smali 근거
        # :11764-11805,11834-11850. 전송 키와 N 리터럴의 평문은 보호돼 직접 확인되지 않았습니다.
        form["hiduserYn"] = "N"
        form["hidCustNo"] = non_member_no
    form["txtPsgGridcnt"] = str(len(rows))
    for wire_name, attribute in _PRICE_RECALCULATION_SCALAR_FIELDS:
        value = getattr(request, attribute)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(
                f"KORAIL price recalculation {attribute} must be a non-empty string when present"
            )
        form[wire_name] = value
    for wire_name, _ in _PRICE_RECALCULATION_ROW_FIELDS:
        form[wire_name] = columns[wire_name]
    return form


def build_product_cancel_query(detail: ProductDetailResponse) -> dict[str, str]:
    """여행상품 예약 취소의 GET 쿼리를 구성하며 전송하지 않습니다. ProductCancelIn.java:67-70 의 txtVrRsNo·txtGdSqno 이며 둘 다
    get_product_detail 결과에서 옵니다(ProductReservationListScreenKt.java:1252-1253,
    MyTicketDetailViewModel.java:3290)."""
    if not isinstance(detail, ProductDetailResponse):
        raise KorailProtocolError("detail must be a ProductDetailResponse from get_product_detail")
    return {
        "txtVrRsNo": _required_mutation_text(
            detail.virtual_reservation_no, field="virtual_reservation_no", context="product cancel"
        ),
        "txtGdSqno": _required_mutation_text(
            detail.goods_sequence, field="goods_sequence", context="product cancel"
        ),
    }


def build_maas_cancel_form(config: KorailConfig, item: CartItem, *, customer_no: str) -> dict[str, str]:
    """PNR이 빈 미결제 부가서비스 해제용이며 결제 후 환불과 다릅니다(BasketTicketViewModel.java:3080-3160,5692-5723)."""
    if not isinstance(item, CartItem):
        raise KorailProtocolError("item must be a CartItem from get_cart_list")
    if item.pnr_no:
        raise KorailProtocolError(
            "KORAIL cart row with a PNR is a train or bus hold; use cancel_unpaid_hold for it"
        )
    form = _common_fields(config)
    form["custMgNo"] = _required_mutation_text(customer_no, field="customer_no", context="MaaS cancel")
    form["lumpStlTgtNo"] = _required_mutation_text(
        item.lump_sum_target_no, field="lump_sum_target_no", context="MaaS cancel"
    )
    return form


def build_cart_add_form(
    config: KorailConfig,
    request: CartAddRequest,
) -> dict[str, str]:
    """CommonIn 외에는 hidPnrNo만 보냅니다(AddCartListIn.java:25,30,52,79)."""
    if not isinstance(request, CartAddRequest):
        raise KorailProtocolError("KORAIL cart request requires an exact CartAddRequest")
    pnr_no = _required_mutation_text(request.pnr_no, field="pnr_no", context="cart request")
    form = _common_fields(config)
    form["hidPnrNo"] = pnr_no
    return form


def build_self_checkin_register_form(
    config: KorailConfig,
    detail: RefundTicketDetailResponse,
    seat: SelfCheckInSeat,
) -> dict[str, str]:
    """좌석 칸은 좌석 확인(check_self_checkin_seat)의 행에서, 승차권 칸은 상세에서 옵니다 (SelfCheckInInfoViewModel.java:224-225;
    SelfCheckInRegisterIn.java:59). jrnySqno 는 좌석 행이 아닌 상세의 값입니다."""
    if not isinstance(seat, SelfCheckInSeat):
        raise KorailProtocolError("seat must be a SelfCheckInSeat from check_self_checkin_seat")
    return {
        **_common_fields(config),
        "cpsNo": _required_mutation_text(seat.cps_no, field="cps_no", context="self check-in"),
        "scarNo": _required_mutation_text(seat.car_no, field="car_no", context="self check-in"),
        "seatNo": _required_mutation_text(seat.seat_no, field="seat_no", context="self check-in"),
        **self_checkin_ticket_fields(detail, sale_date_key="saleDd"),
    }


def build_self_checkin_cancel_form(config: KorailConfig, detail: RefundTicketDetailResponse) -> dict[str, str]:
    """칸은 정보 조회와 같습니다(SelfCheckInResultViewModel.java:111-112; SelfCheckInCancelIn.java:53)."""
    return {**_common_fields(config), **self_checkin_ticket_fields(detail, sale_date_key="saleDt")}


def build_delivered_ticket_retrieval_form(
    config: KorailConfig,
    ticket: PbpAcceptanceTicket,
) -> dict[str, str | list[str]]:
    """앱은 첫 여정의 pbpRsvNo 로 묶은 승차권마다 한 번, 그 묶음의 pbpRsvNo 와 첫 승차권의 pnrNo 를
    보냅니다(DeliveredTicketViewModel.java:185-205,283). pbpCnt 는 쌍의 수 1 이고, 두 목록은 FieldMap 뒤의 @Field 반복 키입니다
    (NetworkApi.java:642-644)."""
    if not isinstance(ticket, PbpAcceptanceTicket):
        raise KorailProtocolError("ticket must be a PbpAcceptanceTicket from get_pbp_acceptance_specifications")
    if not ticket.journeys:
        raise KorailProtocolError("KORAIL delivered ticket retrieval needs the ticket's first journey")
    context = "delivered ticket retrieval"
    return {
        **_common_fields(config),
        "pbpCnt": "1",
        "pbpRsvNo": [
            _required_mutation_text(
                ticket.journeys[0].pbp_reservation_no, field="pbp_reservation_no", context=context
            )
        ],
        "pnrNo": [_required_mutation_text(ticket.pnr_no, field="pnr_no", context=context)],
    }
