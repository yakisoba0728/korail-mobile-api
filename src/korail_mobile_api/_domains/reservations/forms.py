# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약 입력과 폼입니다. 입력 모델의 생성은 전송하지 않으며 raw·repr은 마스킹하지 않습니다.

DTO 필드·배열 순서와 빈 값 생략은 실제 전송에 영향을 주므로 유지합니다."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, fields
from typing import TypeVar

from ..._core.validation import (
    _DATE_RE,
    _DIGITS_RE,
    _TIME_RE,
    _optional_text,
    _required_mutation_text,
    _required_text,
)
from ..._core.wire import _device_version_key, _in_reservation_order, _is_ascii_digits
from ...config import KorailConfig
from ...constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    KORAIL_STANDBY_WAIT_FLAG,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KorailReservationJobType,
    KorailSeatClass,
)
from ...errors import KorailInvalidInputError
from ..trains.models import PhysicalSeat, SeatInventoryResponse, TrainScheduleItem, TrainSummary
from .models import HoldReference, ReservationHoldResponse

# 병합 홀드 응답의 여정 종류는 선행 "21"·후행 "22" 이지만 요청은 여정을 나누지 않습니다(build_merge_reservation_form).
# evidence: app 7.0.6 JourneyDefine.java:87-90 (평문은 보호돼 미확인)
KORAIL_TRANSFER_JOURNEY_TYPE_CODE = "14"
# 객실 등급 코드별로 병합 예약을 할 수 있는 merge_seat_application_flag 값입니다.
# evidence: app 7.0.6 TrainScheduleOutTrainInfo.java:147,1480,1500-1552
KORAIL_MERGE_SEAT_FLAGS_BY_CABIN = {
    "1": frozenset({"A", "G"}),
    "2": frozenset({"A", "S"}),
}
# 선행·후행 좌석 필드가 한 쌍이라는 근거이며 모든 앱 여정의 상한을 증명하지는 않습니다.
# evidence: app 7.0.6 TicketReservationIn.java:32-54
KORAIL_MAX_JOURNEY_LEGS = 2


@dataclass(frozen=True, kw_only=True)
class KorailPassengerCounts:
    """승객 종류별 검색·예약 인원을 구성합니다.

    인원이 0인 승객 종류는 요청에 싣지 않습니다. 유아·안내견을 포함한 전체 인원은 1~9명이어야 합니다. 인원에 음수나 정수가
    아닌 값이 있거나 전체 인원이 이 범위를 벗어나면 ``KorailInvalidInputError``가 발생합니다.

    ``teenager``는 검색 호환용으로 유지하며 검색에서는 어른 수에 합산합니다. 열차 예약 메서드는 이 값이 0보다 크면
    요청 전에 ``KorailInvalidInputError``로 거절합니다. 청소년드림 할인 상품을 선택하는 필드가 아닙니다."""

    adult: int = 1
    teenager: int = 0
    child: int = 0
    infant: int = 0
    senior: int = 0
    severe_disability: int = 0
    mild_disability: int = 0
    guide_dog: int = 0

    def __post_init__(self) -> None:
        for field_ in fields(self):
            value = getattr(self, field_.name)
            # bool 을 인원으로 받지 않도록 정확한 int 타입만 허용합니다.
            if type(value) is not int or value < 0:
                raise KorailInvalidInputError(f"{field_.name} must be a non-negative integer")
        total = self.total
        if total < 1:
            raise KorailInvalidInputError("a reservation must carry at least one passenger")
        if total > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
            raise KorailInvalidInputError(
                f"a reservation carries at most {KORAIL_MAX_PASSENGERS_PER_RESERVATION} passengers, got {total}"
            )

    @property
    def total(self) -> int:
        """유아·안내견을 포함한 전체 승객 수를 반환합니다."""
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


def _passenger_counts(passengers: KorailPassengerCounts | None) -> KorailPassengerCounts:
    """생략하면 어른 1명이고, 다른 타입은 요청 전에 거절합니다."""
    if passengers is None:
        return KorailPassengerCounts()
    if not isinstance(passengers, KorailPassengerCounts):
        raise KorailInvalidInputError("KORAIL reservation requires an exact KorailPassengerCounts")
    return passengers


@dataclass(frozen=True, kw_only=True)
class KorailSeatAssignment:
    """호차 번호와 좌석 식별자로 좌석 지정 입력을 구성합니다.

    ``seat_no``에는 좌석 재고 응답의 ``seat_no``를 그대로 넣으세요. 보통 ``from_inventory()``로 만듭니다. ``car_no``는 1
    이상의 정수, ``seat_no``는 비어 있지 않은 문자열이어야 하며, 아니면 ``KorailInvalidInputError``가 발생합니다."""

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
        if type(self.car_no) is not int or self.car_no < 1:
            raise KorailInvalidInputError("car_no must be a positive integer")
        seat_no = self.seat_no
        if not isinstance(seat_no, str) or not seat_no:
            raise KorailInvalidInputError("seat_no must be a non-empty value taken from a seat-inventory read")

    @classmethod
    def from_inventory(
        cls,
        inventory: SeatInventoryResponse,
        seat: PhysicalSeat,
    ) -> KorailSeatAssignment:
        """좌석 재고 응답과 그 응답의 판매 가능한 좌석으로 좌석 지정 입력을 만듭니다.

        ``inventory.car_no``가 없으면 이 메서드를 쓸 수 없으므로 ``KorailSeatAssignment(car_no=..., seat_no=...)``로 직접
        만드세요. 호차 번호가 없거나, ``seat``이 ``inventory.seats``에 없거나, ``seat.sale_possible``이 ``"Y"``가 아니면
        ``KorailInvalidInputError``가 발생합니다."""
        if not isinstance(inventory, SeatInventoryResponse):
            raise KorailInvalidInputError("inventory must be a SeatInventoryResponse")
        if not isinstance(seat, PhysicalSeat):
            raise KorailInvalidInputError("seat must be a PhysicalSeat")
        car_no = inventory.car_no
        if type(car_no) is not int:
            raise KorailInvalidInputError(
                "seat inventory did not echo a car number (scar_no); "
                "construct KorailSeatAssignment with an explicit car_no"
            )
        if seat not in inventory.seats:
            raise KorailInvalidInputError("seat does not belong to this seat inventory")
        if seat.sale_possible != "Y":
            raise KorailInvalidInputError(
                'seat is not marked sellable by the seat-inventory read (sale_psb_flg must be "Y")'
            )
        return cls(car_no=car_no, seat_no=seat.seat_no)


@dataclass(frozen=True, kw_only=True)
class CartAddRequest:
    """홀드를 장바구니에 추가할 PNR 입력을 구성합니다.

    PNR은 ``hidPnrNo``로 보내며, 비어 있으면 요청을 보내기 전에 ``KorailInvalidInputError``가 발생합니다."""

    pnr_no: str


@dataclass(frozen=True, kw_only=True)
class TicketDuplicationCheckRequest:
    """PNR 기준 중복 예약 확인 입력을 구성합니다."""

    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_ticket_duplication_check_form(
    request: TicketDuplicationCheckRequest,
) -> dict[str, str]:
    if not isinstance(request, TicketDuplicationCheckRequest):
        raise KorailInvalidInputError("request must be a TicketDuplicationCheckRequest")
    return {"pnrNo": request.pnr_no}


@dataclass(frozen=True, kw_only=True)
class TicketReservationDetailRequest:
    """PNR 기준 예약 상세 조회 입력을 구성합니다.

    PNR은 ``hidPnrNo``로 보냅니다. ``pnr_no``가 비어 있으면 ``KorailInvalidInputError``가 발생합니다."""

    pnr_no: str

    def __post_init__(self) -> None:
        _required_text(self.pnr_no, "pnr_no")


def build_ticket_reservation_detail_query(
    request: TicketReservationDetailRequest,
) -> dict[str, str]:
    if not isinstance(request, TicketReservationDetailRequest):
        raise KorailInvalidInputError("request must be a TicketReservationDetailRequest")
    return {"hidPnrNo": request.pnr_no}


def build_cart_list_form(
    pnr_no: str = "",
    additional_service_request_no: str = "",
) -> dict[str, str]:
    return {
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
        "addSrvReqNo": _optional_text(
            additional_service_request_no,
            "additional_service_request_no",
        ),
    }


_SEAT_ATTRIBUTE_RE = re.compile(r"[0-9]{3}")


def _required_digits(value: str | None, *, field: str) -> str:
    if not isinstance(value, str) or _DIGITS_RE.fullmatch(value) is None:
        raise KorailInvalidInputError(f"KORAIL reservation train field {field} must be decimal digits")
    return value


def _required_pattern(
    value: str | None,
    *,
    field: str,
    pattern: re.Pattern[str],
) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise KorailInvalidInputError(f"KORAIL reservation train field {field} has an invalid shape")
    return value


# 0명 행을 제외한 뒤 연속 인덱스를 붙입니다. PassengerType.basicList()의 열차 승객 7종입니다.
# evidence: app 7.0.8 ReqDiscount (요청 할인 값 복원)
_PASSENGER_ROWS: tuple[tuple[str, str, str], ...] = (
    ("adult", "1", "000"),  # 어른
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
    # 명시한 좌석속성→조회 행→기본 선택 순서입니다.
    candidate = selected_code if selected_code is not None else train.seat_attribute_code or "015"
    return _required_pattern(candidate, field="seat_attribute_code", pattern=_SEAT_ATTRIBUTE_RE)


def _validated_seat_assignments(
    seats: Sequence[KorailSeatAssignment] | None,
    *,
    job_type: KorailReservationJobType,
    passenger_total: int,
) -> tuple[KorailSeatAssignment, ...]:
    """좌석 목록은 좌석 지정 job(1103, 관측값)에서만 보냅니다."""
    if job_type is not KorailReservationJobType.SEAT_DESIGNATED:
        if seats:
            raise KorailInvalidInputError(
                "KORAIL designated seats belong to a seat-designated "
                f'reservation (txtJobId "1103"), not "{job_type.value}"'
            )
        return ()
    if seats is None or isinstance(seats, (str, bytes)):
        raise KorailInvalidInputError(
            "KORAIL seat-designated reservation requires a sequence of KorailSeatAssignment"
        )
    assignments = tuple(seats)
    for assignment in assignments:
        if not isinstance(assignment, KorailSeatAssignment):
            raise KorailInvalidInputError(
                "KORAIL seat-designated reservation requires exact KorailSeatAssignment values"
            )
    if len(assignments) != passenger_total:
        raise KorailInvalidInputError(
            "KORAIL seat-designated reservation needs exactly one seat per "
            f"passenger: {passenger_total} passenger(s), "
            f"{len(assignments)} seat(s)"
        )
    identities = {(item.car_no, item.seat_no) for item in assignments}
    if len(identities) != len(assignments):
        raise KorailInvalidInputError("KORAIL seat-designated reservation cannot book the same seat twice")
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
    """DTO 배열은 1기반이며 txtSrcarCnt는 호차 수가 아닌 좌석 수입니다."""
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
    """앱의 환승 오버로드처럼 구간별 등급·좌석속성을 받아 같은 DTO 를 구성하며 두 구간 모두 환승 여정 종류를 씁니다."""
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
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """첫 홀드 폼에서 입석 플래그와 중간역 세 필드만 바꿉니다. 작업 유형은 항상 MERGE_STANDING 입니다."""
    rows = tuple(merge_rows) if not isinstance(merge_rows, (str, bytes)) else ()
    if not rows or not all(isinstance(row, TrainScheduleItem) for row in rows):
        raise KorailInvalidInputError("KORAIL 병합 reservation requires the research.mergeSeatsC.do rows")
    hold_train_no = _required_digits(standing_hold_train.train_no, field="train_no")
    for row in rows:
        if _required_digits(row.train_no, field="train_no") != hold_train_no:
            raise KorailInvalidInputError(
                "KORAIL 병합 reservation splits ONE train: every merge row must "
                f"carry the standing hold's train_no {hold_train_no!r}"
            )
        # 행별 h_run_dt 는 관측에 있었지만 없는 행도 받습니다. 있으면 다른 날 조회한 행을 거절합니다.
        if row.run_date is not None and row.run_date != standing_hold_train.run_date:
            raise KorailInvalidInputError(
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
        raise KorailInvalidInputError(f"KORAIL 병합 reservation first merge row lacks {', '.join(missing)}")
    form = build_reservation_form(
        config,
        standing_hold_train,
        passengers=passengers,
        seat_class=seat_class,
        # 다른 작업 유형은 입석 플래그를 덮어써 예약대기·입석 홀드를 결제 가능한 결과로 만들었습니다.
        job_type=KorailReservationJobType.MERGE_STANDING,
        seat_attribute_code=seat_attribute_code,
    )
    form["txtStndFlg"] = "Y" if any(_standing_only(row) for row in (first, last)) else "N"
    form.update({key: str(value) for key, value in middle.items()})
    return _in_reservation_order(form)


def is_merge_eligible(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> bool:
    """앱의 보호 리터럴은 등급별 세 개, 라이브러리는 두 개입니다."""
    if not isinstance(train, TrainSummary):
        raise KorailInvalidInputError("KORAIL merge eligibility requires an exact TrainSummary")
    cabin = _coerced_seat_class(seat_class)
    flag = train.merge_seat_application_flag
    if not isinstance(flag, str):
        return False
    return flag in KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[cabin.value]


def _seat_attribute_key(journey: int) -> str:
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


_T = TypeVar("_T")


def _coerced_seat_class(value: object) -> KorailSeatClass:
    try:
        if not isinstance(value, str):
            raise ValueError(value)
        return KorailSeatClass(value)
    except ValueError as exc:
        raise KorailInvalidInputError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        ) from exc


def _resolved_sequence(value: Sequence[_T], message: str) -> tuple[_T, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KorailInvalidInputError(message)
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
            raise KorailInvalidInputError("KORAIL reservation requires an exact TrainSummary")
    if require is not None and len(resolved) != require:
        # 후행 좌석 키가 하나뿐이라 세 번째 구간을 표현할 수 없다는 이 모델의 제한이며 앱의 모든 여행 형태에 대한 주장은 아닙니다.
        raise KorailInvalidInputError(
            f"KORAIL 환승 reservation books exactly {require} legs, got "
            f"{len(resolved)}: the reservation form has no journey-{require + 1} "
            "spelling at all (only TicketReservationInSrcar and "
            "TicketReservationInSrcarTrailing exist, splitting on "
            '"journey 1 or not"), so a further leg would overwrite leg '
            f"{require} rather than be added"
        )
    if not resolved or len(resolved) > KORAIL_MAX_JOURNEY_LEGS:
        raise KorailInvalidInputError(
            f"KORAIL reservation carries between 1 and {KORAIL_MAX_JOURNEY_LEGS} legs, got {len(resolved)}"
        )
    return resolved


def _validated_seat_classes(
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass,
    *,
    leg_count: int,
) -> tuple[KorailSeatClass, ...]:
    """등급 하나는 모든 구간에, 목록은 구간별로 씁니다."""
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
        raise KorailInvalidInputError(
            "KORAIL reservation seat class must be a KorailSeatClass or a sequence of one per leg"
        )
    if len(candidates) != leg_count:
        raise KorailInvalidInputError(
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
        raise KorailInvalidInputError(
            "KORAIL seat-designated reservation requires one sequence of KorailSeatAssignment per leg"
        )
    else:
        per_leg = tuple(leg_seats)
        if len(per_leg) != leg_count:
            raise KorailInvalidInputError(
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
    """직통·환승은 같은 DTO 를 채우지만 입력 분기는 다릅니다."""
    resolved_legs = _validated_legs(legs, require=require_legs)
    if seat_attribute_codes is None:
        selected_attributes: tuple[str | None, ...] = (None,) * len(resolved_legs)
    else:
        selected_attributes = tuple(seat_attribute_codes)
        if len(selected_attributes) != len(resolved_legs):
            raise KorailInvalidInputError("KORAIL reservation requires one selected seat attribute per leg")
    resolved_attributes = tuple(
        _seat_attribute_code(train, selected)
        for train, selected in zip(resolved_legs, selected_attributes, strict=True)
    )
    passengers = _passenger_counts(passengers)
    # TEENAGER는 basicList()에 없으며 P11 예약은 ERR299943으로 거절됩니다. 청소년드림 상품과도 별개입니다.
    if passengers.teenager > 0:
        raise KorailInvalidInputError("KORAIL train reservations do not support teenager passengers (P11)")
    # 앱 인원 선택기는 이 두 조합을 고를 수 없게 합니다: 유아가 있으면 유아·어린이 외 인원(안내견 포함)이 있어야 하고,
    # 안내견은 중증·경증 장애 승객 합계를 넘을 수 없습니다.
    if passengers.infant and passengers.total - passengers.infant - passengers.child == 0:
        raise KorailInvalidInputError("KORAIL infant passengers require an accompanying passenger")
    if passengers.guide_dog > passengers.severe_disability + passengers.mild_disability:
        raise KorailInvalidInputError("KORAIL guide dogs cannot outnumber disability passengers")
    resolved_classes = _validated_seat_classes(
        seat_classes,
        leg_count=len(resolved_legs),
    )
    try:
        job_type = KorailReservationJobType(job_type)
    except ValueError as exc:
        raise KorailInvalidInputError(
            "KORAIL reservation job type must be one of "
            + ", ".join(f'"{member.value}"' for member in KorailReservationJobType)
        ) from exc
    # STANDBY·MERGE_STANDING 을 단일 구간으로 제한하지 않습니다. 앱의 특실 상태에는 WAIT/STAND/FREE 반환이 없습니다.
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
    form = _device_version_key(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": job_type.value,
            "txtGdNo": "",
            "hidFreeFlg": "N",
            # 환승은 구간별 판정의 OR 입니다. 대기를 입석 홀드로 바꾸지 않기 위한 구분입니다.
            "txtStndFlg": (
                "Y"
                if job_type is not KorailReservationJobType.STANDBY
                and any(
                    seat_class is KorailSeatClass.GENERAL and _standing_only(leg)
                    for leg, seat_class in zip(resolved_legs, resolved_classes, strict=True)
                )
                else "N"
            ),
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    # 미지정 좌석속성의 앱 기본값은 보호돼 있어 관측값 000 을 보냅니다.
    # evidence: app 7.0.6 TicketReservationIn.java:96-100
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): resolved_attributes[0],
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": resolved_classes[0].value,
        }
    )
    for journey, seat_class in enumerate(resolved_classes[1:], start=2):
        form[_seat_attribute_key(journey)] = resolved_attributes[journey - 1]
        form[f"txtPsrmClCd{journey}"] = seat_class.value
    form["txtJrnyCnt"] = (
        KORAIL_DIRECT_ITINERARY_CODE if len(resolved_legs) == 1 else KORAIL_TRANSFER_ITINERARY_CODE
    )
    _write_journey_rows(
        form,
        journeys,
        KORAIL_DIRECT_JOURNEY_TYPE_CODE if len(resolved_legs) == 1 else KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
    )
    # 좌석 목록·개수는 좌석 지정에서만 채웁니다. 개수 필드는 목록보다 앞에 선언돼 있어 마지막에 순서를 맞춥니다.
    for journey, leg_assignments in enumerate(assignments, start=1):
        for index, assignment in enumerate(leg_assignments, start=1):
            if index == 1:
                form[_srcar_count_key(journey)] = str(len(leg_assignments))
            form[_srcar_no_key(journey, index)] = str(assignment.car_no)
            form[_seat_no_key(journey, index)] = assignment.seat_no
    return _in_reservation_order(form)


def _write_journey_rows(
    form: dict[str, str],
    journeys: Sequence[dict[str, str]],
    journey_type_code: str,
) -> None:
    """도착시각 키는 없습니다."""
    for journey, journey_values in enumerate(journeys, start=1):
        form[f"txtJrnyTpCd{journey}"] = journey_type_code
        # 관측된 001/002 를 재현하는 라이브러리 포맷팅입니다. 앱은 전달받은 값을 그대로 씁니다.
        form[f"txtJrnySqno{journey}"] = f"{journey:03d}"
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
            form[f"{wire}{journey}"] = journey_values[attribute]
        form[f"txtChgFlg{journey}"] = "N"


def _assert_leg_is_bookable(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
    job_type: KorailReservationJobType,
) -> None:
    if job_type is KorailReservationJobType.STANDBY:
        # 앱의 특실 상태에는 WAIT 가 없습니다.
        if seat_class is not KorailSeatClass.GENERAL:
            raise KorailInvalidInputError("KORAIL standby (예약대기) is offered on the 일반실 cabin only")
        if not train.has_waiting_list():
            raise KorailInvalidInputError(
                "KORAIL standby requires a train whose h_wait_rsv_flg is "
                f"{KORAIL_STANDBY_WAIT_FLAG!r}, got "
                f"{train.wait_reservation_flag!r}"
            )
        # 대기 가능 여부를 일반실 잔여좌석 코드로 막지 않습니다.
        return
    if job_type is KorailReservationJobType.MERGE_STANDING:
        if not is_merge_eligible(train, seat_class=seat_class):
            raise KorailInvalidInputError(_merge_ineligible_message(train, seat_class))
        # 병합 가능 행은 일반실 매진(13)과 함께 관측됐으므로 일반 가용(11)을 요구하지 않습니다.
        return
    if seat_class is KorailSeatClass.SPECIAL:
        if not train.has_special_seat():
            raise KorailInvalidInputError("KORAIL reservation requires an evidenced available special seat")
    elif not train.has_general_seat():
        # 앱은 일반실이 STAND 이면 입석 홀드를 보내지만, STAND 판정의 비교값이 보호돼 있어 13/11 만으로는 그런 행을
        # 가릴 수 없습니다.
        raise KorailInvalidInputError("KORAIL reservation requires an evidenced available general seat")


def _assert_boarding_order(
    legs: Sequence[TrainSummary],
    journeys: Sequence[dict[str, str]],
) -> None:
    """앱은 환승 조회가 묶은 두 행으로만 폼을 만듭니다. 두 역 코드가 다른 환승도 있어 역 연결은 보지 않습니다
    (TransferItinerary.transfer_station_code)."""
    for index in range(1, len(journeys)):
        earlier, later = journeys[index - 1], journeys[index]
        if (earlier["train_no"], earlier["run_date"]) == (later["train_no"], later["run_date"]):
            raise KorailInvalidInputError("KORAIL 환승 reservation legs must be different trains")
        departs = later["departure_date"] + later["departure_time"]
        previous = legs[index - 1]
        if departs <= earlier["departure_date"] + earlier["departure_time"] or (
            isinstance(previous.arrival_date, str)
            and isinstance(previous.arrival_time, str)
            and departs < previous.arrival_date + previous.arrival_time
        ):
            raise KorailInvalidInputError(
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
    """구간 입력의 12개 신원·운행 값을 읽습니다. DTO 는 String 이지만 그 선언만으로 서버의 숫자·날짜 제약 부재를 증명하지는 않습니다."""
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


def _standing_only(row: TrainSummary | TrainScheduleItem) -> bool:
    """일반실 매진(13)이면서 입석 가용(11)인 행입니다. 13/11 은 관측값입니다."""
    # evidence: app 7.0.6 TrainReservationCode.java:21,24 (코드 평문은 보호돼 미확인)
    return row.general_reservation_code == "13" and row.standing_reservation_code == "11"


# 앱은 SMS 선택 시 세 부분 전화번호를 합쳐 길이 11 을 검사합니다. 서버의 문자 수용 여부는 미확인입니다.
_STANDBY_PHONE_RE = re.compile(r"[0-9]{11}")


def _successful_hold_pnr(hold: ReservationHoldResponse, *, context: str) -> str:
    """실패 메시지는 context 로 구분합니다."""
    pnr_no = hold.pnr_no
    if hold.str_result != "SUCC" or not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailInvalidInputError(context)
    return pnr_no


def build_standby_wait_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    *,
    allow_seat_class_change: bool = False,
    sms_notify: bool = False,
    phone_no: str | None = None,
) -> dict[str, str]:
    """SMS 선택 때만 번호를 검증하고 미선택 번호는 생략합니다."""
    pnr_no = _successful_hold_pnr(
        hold,
        context="KORAIL standby options require one successful hold with a PNR",
    )
    # bool("N") 은 True 이므로 문자열 플래그를 bool 로 묵시 변환하지 않습니다.
    if not isinstance(allow_seat_class_change, bool):
        raise KorailInvalidInputError("allow_seat_class_change must be a bool")
    if not isinstance(sms_notify, bool):
        raise KorailInvalidInputError("sms_notify must be a bool")
    if sms_notify and (not isinstance(phone_no, str) or _STANDBY_PHONE_RE.fullmatch(phone_no) is None):
        raise KorailInvalidInputError("KORAIL standby SMS notification requires an 11-digit phone number")
    form = _device_version_key(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtPsrmClChgFlg": "Y" if allow_seat_class_change else "N",
            "txtSmsSndFlg": "Y" if sms_notify else "N",
        }
    )
    if sms_notify and phone_no is not None:
        form["txtCpNo"] = phone_no
    return form


def build_unpaid_reservation_cancel_form(
    config: KorailConfig,
    hold: ReservationHoldResponse | HoldReference,
) -> dict[str, str]:
    """홀드의 여정 수를 되울립니다. 순번·변경번호는 첫 여정 값을 되울리고, 없을 때만 아래 대체값을 씁니다."""
    if isinstance(hold, ReservationHoldResponse):
        _successful_hold_pnr(hold, context="KORAIL cancellation requires a fresh successful unpaid hold")
        if not isinstance(hold.journey_count, str):
            raise KorailInvalidInputError("KORAIL cancellation requires a fresh successful unpaid hold")
        reference = hold.reference
    elif isinstance(hold, HoldReference):
        reference = hold
        _required_text(reference.pnr_no, "pnr_no")
        for value, name in (
            (reference.journey_sequence, "journey_sequence"),
            (reference.change_no, "change_no"),
        ):
            if value is not None:
                _optional_text(value, name)
    else:
        raise KorailInvalidInputError(
            "KORAIL cancellation requires an exact reservation hold response or a HoldReference"
        )
    journey_count = reference.journey_count.strip() if isinstance(reference.journey_count, str) else ""
    # 검사한 값을 그대로 보내며, 0 채움은 유지하고 0 만으로 된 값은 int() 없이 거절합니다.
    if not _is_ascii_digits(journey_count) or not journey_count.lstrip("0"):
        raise KorailInvalidInputError("KORAIL cancellation requires a fresh successful unpaid hold")
    pnr_no, sequence, change_no = reference.pnr_no, reference.journey_sequence, reference.change_no
    form = _device_version_key(config)
    # 값이 없을 때 앱 결제 화면은 4·3바이트 보호 리터럴을 씁니다. 0001·000 은 그 자리의 라이브러리 값입니다.
    # evidence: app 7.0.6 PayViewModel.java:4678-4686
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtJrnySqno": sequence or "0001",
            "txtJrnyCnt": journey_count,
            "hidRsvChgNo": change_no or "000",
        }
    )
    return form


def build_cart_add_form(
    config: KorailConfig,
    request: CartAddRequest,
) -> dict[str, str]:
    """공통 필드 외에는 hidPnrNo만 보냅니다."""
    if not isinstance(request, CartAddRequest):
        raise KorailInvalidInputError("KORAIL cart request requires an exact CartAddRequest")
    pnr_no = _required_mutation_text(request.pnr_no, field="pnr_no", context="cart request")
    form = _device_version_key(config)
    form["hidPnrNo"] = pnr_no
    return form
