# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태 변경 요청의 폼 빌더. 이 모듈은 전송하지 않으며 전송은 KorailHttpClient.post_mutation_form 이 담당합니다. 라우트·범주·폼을 함께 검증하는 별도 사전 단언은 없습니다.

보호된 앱 상수와 라이브 관측을 구분합니다. 병합·재계산의 관측 범위는 client 의 해당 메서드, 나머지 제약은 각 빌더를 참고하십시오. 역발행 환불·N카드 경로와 일부 선택값은
라이브 미검증입니다.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
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
from .read_models import TrainScheduleItem


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
    """CommonIn.java:381 의 lang 은 config.lang 이 None 이 아닐 때만 포함합니다. 앱의 언어 기본값은 보호돼 있습니다."""
    fields = {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


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


def _add_passenger_rows(
    form: dict[str, str], passengers: KorailPassengerCounts
) -> None:
    index = 0
    for attribute, passenger_type, discount_code in _PASSENGER_ROWS:
        count = getattr(passengers, attribute)
        if count == 0:
            continue
        index += 1
        form[f"txtCompaCnt{index}"] = str(count)
        form[f"txtPsgTpCd{index}"] = passenger_type
        form[f"txtDiscKndCd{index}"] = discount_code


def _seat_attribute_code(
    train: TrainSummary, selected_code: str | None = None
) -> str:
    # 명시한 좌석속성→조회 행→기본 선택 순서입니다(TrainScheduleViewModel.java:2914-2930,2982-2999).
    candidate = (
        selected_code
        if selected_code is not None
        else train.seat_attribute_code or "015"
    )
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
    """좌석지정은 승객당 좌석 하나를 요구합니다. 앱도 좌석 목록·개수와 SEAT job 을 함께 설정합니다
    (TrainSeatMapViewModel.java:2135-2138,2289). 1103 은 관측값이며 enum 평문은 보호돼 있습니다
    (ReservationJobId.java:22). 일반 빌더는 좌석 목록·개수를 채우지 않습니다 (TrainScheduleViewModel.java:2932,3004;
    TicketReservationIn.java:182).
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
        if not isinstance(assignment, KorailSeatAssignment):
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
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """단일 열차의 홀드 폼. 좌석 지정 키는 TicketReservationInSrcar.java:51, 후행 키는
    TicketReservationInSrcarTrailing.java:52, 개수는 TicketReservationIn.java:80 입니다. 앱은 한 FieldMap 으로
    전송하고(NetworkApi.java:752-753), DTO 를 평탄화하며 배열에 1기반 인덱스를
    붙입니다(NetworkService.java:14155-14162,15350,15366). txtSrcarCnt 는 호차 수가 아닌 좌석
    수입니다(TrainSeatMapViewModel.java:2108-2113,2136-2138). 라이브러리의 삽입 순서가 DTO 의 모든 필드 순서와 같다는 보장은 없습니다.
    """
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
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = (
        KorailSeatClass.GENERAL
    ),
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
    seat_attribute_codes: Sequence[str | None] | None = None,
) -> dict[str, str]:
    """두 TrainSummary 구간을 한 홀드 폼으로 만듭니다. 앱의 환승 오버로드는 구간 수·등급· 입석 여부를 받아 같은 DTO 를
    구성합니다(TrainScheduleViewModel.java:2937-3004). 두 구간 모두 isTransfer=true 를 넘깁니다(:2968); 여정 종류 선택은
    TrainScheduleOutTrainInfo.java:3674-3683 입니다. 여정 코드·일련번호의 앱 평문은 보호돼 있으며 14 와 001/002 는 라이브 기록값입니다.
    길이 일치로 그 값을 복호했다고 보지 않습니다.
    """
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
    """병합의 두 번째 홀드 폼 — 첫 홀드 요청을 그대로 다시 만들고 네 값만 바꿉니다.

    7.0.6 병합 화면은 첫 홀드의 ``TicketReservationIn`` 을 넘겨받아
    (``ReservationMergeRoute.getTicketReservationIn()``, ``ReservationMergeViewModel.smali:425-435``)
    ``copy$default`` 마스크 ``0x7ffef`` 로 다시 보냅니다(``:7671-7774``). 바뀌는 것은 인자 4
    ``txtStndFlg`` 와 인자 19-21 ``txtMidRsStnCd``/``txtMidStnConsOrdr``/``txtMidStnRunOrdr``
    (``TicketReservationIn.java:486`` 의 인자 순서)뿐이고, 세 중간역 값은 고른
    ``MergeSeatsCOutTrnInfo`` 행의 도착역 코드·구성순서·운행순서입니다. 여정은 원래대로 하나이고
    job 도 첫 요청 그대로입니다.

    그래서 ``standing_hold_train``·``passengers``·``seat_class``·``job_type``·``seat_attribute_code`` 는
    **첫 홀드를 만들 때와 같은 값**이어야 합니다. ``merge_rows`` 는 병합 좌석 조회
    (:meth:`~korail_mobile_api.client.KorailClient.get_merge_seats_inquiry`)의 ``trains`` 입니다.
    중간역은 **첫 행**의 도착역이고(``trnInfoList.first()``, ``:7270-7300``), ``txtStndFlg`` 는
    첫 행이나 마지막 행이 일반석 ``SOLD_OUT``·입석 ``AVAILABLE`` 이면 켭니다(``:7372-7560``;
    ``TrainReservationCode`` 평문은 보호돼 일반 예약과 같은 13/11 관측값을 씁니다).
    2026-09-24 서울→부산 175: 행이 서울→영등포(11/11)·영등포→부산(13/11) 두 개였습니다.
    """
    rows = tuple(merge_rows) if not isinstance(merge_rows, (str, bytes)) else ()
    if not rows or not all(isinstance(row, TrainScheduleItem) for row in rows):
        raise KorailProtocolError(
            "KORAIL 병합 reservation requires the research.mergeSeatsC.do rows"
        )
    hold_train_no = _required_digits(standing_hold_train.train_no, field="train_no")
    for row in rows:
        if _required_digits(row.train_no, field="train_no") != hold_train_no:
            raise KorailProtocolError(
                "KORAIL 병합 reservation splits ONE train: every merge row must "
                f"carry the standing hold's train_no {hold_train_no!r}"
            )
    first, last = rows[0], rows[-1]
    middle = {
        "txtMidRsStnCd": first.arrival_station_code,
        "txtMidStnConsOrdr": first.arrival_construction_order,
        "txtMidStnRunOrdr": first.arrival_run_order,
    }
    missing = [key for key, value in middle.items() if not value]
    if missing:
        raise KorailProtocolError(
            f"KORAIL 병합 reservation first merge row lacks {', '.join(missing)}"
        )
    form = build_reservation_form(
        config,
        standing_hold_train,
        passengers=passengers,
        seat_class=seat_class,
        job_type=job_type,
        seat_attribute_code=seat_attribute_code,
    )
    standing = any(
        row.general_reservation_code == "13" and row.standing_reservation_code == "11"
        for row in (first, last)
    )
    form["txtStndFlg"] = "Y" if standing else "N"
    form.update({key: str(value) for key, value in middle.items()})
    return form


def is_merge_eligible(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> bool:
    """라이브러리 플래그 집합으로 병합 가능성을 판단합니다. 앱은 hYmsAplFlg 를
    비교합니다(TrainScheduleOutTrainInfo.java:1500-1552,2842-2847,3588-3589). 앱의 보호 리터럴은 등급별 세 개, 라이브러리는 두
    개입니다. 평문을 모르므로 라이브러리 집합이 앱 집합의 부분집합인지도 미확인입니다. 잘못 허용하거나 거절할 가능성을 모두 배제하지 않습니다.
    """
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError(
            "KORAIL merge eligibility requires an exact TrainSummary"
        )
    cabin = _coerced_seat_class(seat_class)
    flag = train.merge_seat_application_flag
    if not isinstance(flag, str):
        return False
    return flag in KORAIL_MERGE_SEAT_FLAGS_BY_CABIN[cabin.value]


# 후행 좌석 키가 하나뿐인 모델을 사용하므로 라이브러리는 최대 두 구간만 허용합니다.
def _seat_attribute_key(journey: int) -> str:
    """선행/후행 속성 키: TicketReservationIn.java:80,189-191,237-239."""
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    """선행/후행 좌석 수 키: TicketReservationIn.java:80,193-195,245-247."""
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    """호차 키: TicketReservationInSrcar.java:51,85; TicketReservationInSrcarTrailing.java:52,86. 배열 인덱스는
    1부터 붙습니다(NetworkService.java:15350,15366).
    """
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    """좌석 키: TicketReservationInSrcar.java:51,81; TicketReservationInSrcarTrailing.java:52,82."""
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


_T = TypeVar("_T")


def _coerced_seat_class(value: object) -> KorailSeatClass:
    """``"1"``(일반실)·``"2"``(특실) 또는 :class:`KorailSeatClass` 만 받습니다."""
    try:
        return KorailSeatClass(value)
    except ValueError:
        raise KorailProtocolError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        )


def _resolved_sequence(value: Sequence[_T], message: str) -> tuple[_T, ...]:
    """구간 목록을 튜플로 굳힙니다. 문자열·바이트는 시퀀스여도 목록이 아닙니다."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise KorailProtocolError(message)
    return tuple(value)


def _validated_legs(
    legs: Sequence[TrainSummary],
    *,
    require: int | None,
) -> tuple[TrainSummary, ...]:
    """구간 타입·개수를 검증합니다. require=None 도 무제한이 아니라 라이브러리 최대 구간 수를 적용합니다."""
    resolved = _resolved_sequence(
        legs, "KORAIL reservation requires a sequence of legs"
    )
    for leg in resolved:
        if not isinstance(leg, TrainSummary):
            raise KorailProtocolError(
                "KORAIL reservation requires an exact TrainSummary"
            )
    if require is not None and len(resolved) != require:
        # 후행 좌석 키는 하나입니다(TicketReservationIn.java:80; TicketReservationInSrcarTrailing.java:52). 이 모델로
        # 세 번째 구간을 표현할 수 없다는 제한이며 앱의 모든 여행 형태에 대한 주장은 아닙니다.
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
            "KORAIL reservation carries between 1 and "
            f"{KORAIL_MAX_JOURNEY_LEGS} legs, got {len(resolved)}"
        )
    return resolved


def _validated_seat_classes(
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass,
    *,
    leg_count: int,
) -> tuple[KorailSeatClass, ...]:
    """공통 등급 또는 구간별 등급을 받습니다. 앱도 환승에서 구간별 PsrmType 을 선택합니다 (TrainScheduleViewModel.java:2952-2968;
    TicketReservationInJrny.java:69,234).
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
    return tuple(_coerced_seat_class(candidate) for candidate in candidates)


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
    seat_attribute_codes: Sequence[str | None] | None = None,
) -> dict[str, str]:
    """직통·환승 공통 빌더. 앱의 두 오버로드는 같은 DTO 를 채우지만 입력 분기는 다릅니다 (TrainScheduleViewModel.java:2849,2937;
    TicketReservationIn.java:139-179).
    """
    resolved_legs = _validated_legs(legs, require=require_legs)
    if seat_attribute_codes is None:
        selected_attributes: tuple[str | None, ...] = (None,) * len(resolved_legs)
    else:
        selected_attributes = tuple(seat_attribute_codes)
        if len(selected_attributes) != len(resolved_legs):
            raise KorailProtocolError(
                "KORAIL reservation requires one selected seat attribute per leg"
            )
    resolved_attributes = tuple(
        _seat_attribute_code(train, selected)
        for train, selected in zip(
            resolved_legs, selected_attributes, strict=True
        )
    )
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif not isinstance(passengers, KorailPassengerCounts):
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
        )
    # STANDBY·MERGE_STANDING 을 단일 구간으로 제한하지 않습니다. 조합 수용은 서버가 결정합니다. 앱의 특실 상태에는 WAIT/STAND/FREE 반환이
    # 없습니다(TrainScheduleOutTrainInfo.java:3587-3625). 일반실 분기는 같은 파일 :2810-2890 이며 단일 구간 제한을 증명하는 근거는
    # 아닙니다.
    assignments = _validated_leg_seats(
        leg_seats,
        leg_count=len(resolved_legs),
        job_type=job_type,
        passenger_total=passengers.total,
    )
    # 구간 수와 객실 수가 같음은 _validated_seat_classes 에서 검증합니다.
    for leg, seat_class in zip(resolved_legs, resolved_classes, strict=True):
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
            # 일반 입석 판정은 _standing_flag 참고. 환승은 구간별 판정의 OR 입니다 (TrainScheduleViewModel.java:2961-2967).
            # 예약대기만 N 으로 고정합니다. 2026-09-16 같은 대기 열차에 N 은 SUCC/IRR000014, Y 는 SUCC/IRR000018 과 입석 좌석·입석
            # 인원 1·결제기한을 돌려줬습니다. 대기를 입석 홀드로 바꾸지 않기 위한 구분입니다. 앱의 STAND 판정 사용은
            # TrainScheduleViewModel.java:2870-2874 참고.
            "txtStndFlg": (
                "N"
                if job_type is KorailReservationJobType.STANDBY
                else _itinerary_standing_flag(
                    resolved_legs,
                    seat_classes=resolved_classes,
                )
            ),
            # 동반유아·안내견도 합계에 포함합니다. Passengers.java:610-616 의 전체 합계와 PassengerType.java:38-45 의 여덟 종류,
            # TrainScheduleViewModel.java:2912 참고.
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    # 속성 선언은 TicketReservationIn.java:80,139-179; 앱 평탄화는 NetworkService.java:15304-15343. 미지정 속성의 기본값은
    # 보호돼 있습니다(TicketReservationIn.java:96-100). 3바이트라는 사실은 라이브러리 값 000 을 증명하지 않습니다.
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): resolved_attributes[0],
            "txtSeatAttCd5": "000",
            # 객실은 구간 DTO 필드(TicketReservationInJrny.java:69,234)입니다. 앱은 평탄화 중 인덱스를
            # 붙입니다(NetworkService.java:15366). 1/2 값은 관측이며 PsrmType.java:19-20,63-65 의 코드 평문은 보호돼
            # 있습니다.
            "txtPsrmClCd1": resolved_classes[0].value,
        }
    )
    for journey, seat_class in enumerate(resolved_classes[1:], start=2):
        # 앱도 각 행의 좌석속성을 선행/후행 필드로 전달합니다(TrainScheduleViewModel.java:2982-3004).
        form[_seat_attribute_key(journey)] = resolved_attributes[journey - 1]
        form[f"txtPsrmClCd{journey}"] = seat_class.value
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
    _write_journey_rows(form, journeys, (journey_type_code,) * len(journeys))
    # 좌석 지정에만 개수·좌석쌍을 추가합니다. 앱 일반 빌더는 목록·개수를 채우지 않습니다 (TrainScheduleViewModel.java:2932,3004;
    # TicketReservationIn.java:182). DTO 는 두 개수 필드를 목록보다 앞에 선언하므로(TicketReservationIn.java:80) 라이브러리의
    # 구간별 묶음 삽입 순서와 전체 순서가 같다고 단정할 수 없습니다.
    for journey, leg_assignments in enumerate(assignments, start=1):
        for index, assignment in enumerate(leg_assignments, start=1):
            if index == 1:
                # 선택 좌석 수입니다(TrainSeatMapViewModel.java:2108-2113,2136-2138). 개수 키는 구간별 두
                # 개(TicketReservationIn.java:80)입니다.
                form[_srcar_count_key(journey)] = str(len(leg_assignments))
            form[_srcar_no_key(journey, index)] = str(assignment.car_no)
            form[_seat_no_key(journey, index)] = assignment.seat_no
    return form


def _sequence_no(code: str) -> str:
    """관측된 001/002 를 재현하기 위한 라이브러리 포맷팅입니다. 앱은 전달받은 값을 그대로 씁니다(TrainScheduleOutTrainInfo.java:1631,3683;
    TrainScheduleViewModel.java:2968). 보호 상수의 길이만으로 평문을 확정하지 않습니다.
    """
    return f"{int(code):03d}"


def _write_journey_rows(
    form: dict[str, str],
    journeys: Sequence[dict[str, str]],
    journey_type_codes: Sequence[str],
) -> None:
    """구간별 여정 필드를 씁니다. 선언: TicketReservationInJrny.java:69; 구성: TrainScheduleOutTrainInfo.java:3683; 1기반
    인덱스: NetworkService.java:15350,15366. 도착시각 키는 없습니다. 객실 키는 호출자가 먼저 쓰므로 앱 DTO 전체 순서와 다릅니다.
    txtChgFlg=N 은 라이브러리 값이고 앱 상수는 보호돼 있습니다. 길이 일치는 동등성 증명이 아닙니다.
    """
    for journey, (fields, journey_type_code) in enumerate(
        zip(journeys, journey_type_codes, strict=True), start=1
    ):
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


def _assert_leg_is_bookable(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass,
    job_type: KorailReservationJobType,
) -> None:
    if job_type is KorailReservationJobType.STANDBY:
        # 앱의 특실 상태에는 WAIT 가 없습니다(TrainScheduleOutTrainInfo.java:3587-3625). 일반실 대기 분기는 같은 파일
        # :2839-2850 입니다.
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
        # 대기 가능 여부를 일반실 잔여좌석 코드로 막지 않습니다. 매진 상태에서도 대기가 가능합니다.
        return
    if job_type is KorailReservationJobType.MERGE_STANDING:
        if not is_merge_eligible(train, seat_class=seat_class):
            raise KorailProtocolError(_merge_ineligible_message(train, seat_class))
        # 병합은 일반 좌석 가용성 대신 병합 플래그로 검사합니다. 2026-07-26 관측: 서울→부산 열차 125 에 일반실 매진 코드 13 과 병합 플래그 A 가 함께
        # 있었습니다. 일반 가용 코드 11 을 추가 요구하면 이 표본을 거절하게 됩니다.
        return
    # 선택 객실의 가용성을 검사합니다(TrainScheduleOutTrainInfo.java:2810,3587;
    # TrainScheduleViewModel.java:3457-3458). 이 라이브러리는 명시적 가용 코드 11 만 허용합니다. 앱 자유석 경로의 보호된 요청값은 구현하지
    # 않습니다(TrainScheduleViewModel.java:2875,2899-2915,3004; TrainScheduleOutTrainInfo.java:2881-2889;
    # TrainReservationCode.java:21,24; SeatType.java:299,307). 2026-07-26 매진 표본의 13 은 관측값이며 보호 enum 의
    # 복호 결과가 아닙니다.
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


def _journey_fields(train: TrainSummary | TrainScheduleItem) -> dict[str, str]:
    """구간 입력의 12개 신원·운행 값을 읽습니다(TicketReservationInJrny.java:69). DTO 는 String 이지만 그 선언만으로 서버의 숫자·날짜 제약
    부재를 증명하지는 않습니다.
    """
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
    """하나라도 입석이면 여정 전체를 Y 로 합니다. 앱의 구간별 OR: TrainScheduleViewModel.java:2961-2967,3004."""
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
    TrainScheduleViewModel.java:2870-2874,2961-2967). 13/11 은 관측값이고 TrainReservationCode.java:21,24 의
    코드 평문은 보호돼 있습니다.
    """
    if (
        seat_class is KorailSeatClass.GENERAL
        and train.general_reservation_code == "13"
        and train.standing_reservation_code == "11"
    ):
        return "Y"
    return "N"


# 앱은 SMS 선택 시 세 부분 전화번호를 합쳐 길이 11 을 검사합니다 (ReservationWaitApplyUiData.java:85;
# ReservationWaitViewModel.java:503-513). 라이브러리는 숫자만 허용하므로 앱의 길이 검사보다 엄격합니다. 서버의 문자 수용 여부는 미확인입니다.
_STANDBY_PHONE_RE = re.compile(r"[0-9]{11}")


def _successful_hold_pnr(hold: ReservationHoldResponse, *, context: str) -> str:
    """후속 요청에 필요한 SUCC 홀드와 PNR 을 검증합니다. 실패 메시지는 context 로 구분합니다."""
    pnr_no = hold.pnr_no
    if (
        hold.str_result != "SUCC"
        or not isinstance(pnr_no, str)
        or not pnr_no.strip()
    ):
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
    """예약대기 홀드의 알림·특실변경 옵션 폼. 라우트: NetworkApi.java:639-640; 필드: ReservationWaitIn.java:59; 선택값 구성:
    ReservationWaitViewModel.java:520-527. 옵션의 Y/N 평문은 보호돼 있습니다. 관광열차의 특실 선택 숨김은 같은 파일 :565-572 참고.
    SMS 선택 시만 번호를 검증합니다. 앱의 미선택 번호는 null(:522-524)이지만 Json 설정값은 보호돼 최종 직렬화를 여기서 단정하지
    않습니다(NetworkModule.java:861). 라이브러리는 그 키를 생략합니다.
    """
    pnr_no = _successful_hold_pnr(
        hold,
        context="KORAIL standby options require one successful hold with a PNR",
    )
    # bool("N") 은 True 이므로 문자열 플래그를 bool 로 묵시 변환하지 않습니다.
    if not isinstance(allow_seat_class_change, bool):
        raise KorailProtocolError("allow_seat_class_change must be a bool")
    if not isinstance(sms_notify, bool):
        raise KorailProtocolError("sms_notify must be a bool")
    if sms_notify:
        if not isinstance(phone_no, str) or (
            _STANDBY_PHONE_RE.fullmatch(phone_no) is None
        ):
            raise KorailProtocolError(
                "KORAIL standby SMS notification requires an 11-digit "
                "phone number"
            )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtPsrmClChgFlg": "Y" if allow_seat_class_change else "N",
            "txtSmsSndFlg": "Y" if sms_notify else "N",
        }
    )
    # SMS 를 끄면 번호는 싣지 않습니다(위 docstring 의 :522-524).
    if sms_notify:
        form["txtCpNo"] = phone_no  # type: ignore[assignment] — 위에서 11자리 문자열로 확인
    return form


def build_unpaid_reservation_cancel_form(
    config: KorailConfig,
    response: ReservationHoldResponse,
) -> dict[str, str]:
    """여정 수를 홀드에서 에코해 미결제 취소 폼을 만듭니다. 앱도 응답 여정 수를 전달합니다 (ReservationWaitViewModel.java:398;
    MyReservationViewModel.java:1557). 순번·변경번호는 첫 여정 값을 되울리고, 없을 때만 아래 대체값을 씁니다.
    """
    if not isinstance(response, ReservationHoldResponse):
        raise KorailProtocolError(
            "KORAIL cancellation requires an exact reservation hold response"
        )
    # h_jrny_cnt 는 0001 처럼 패딩돼 오므로 숫자로 검사하고 원래 철자는 에코합니다. 앱의 여정 수 에코:
    # ReservationWaitViewModel.java:398; ReservationMergeViewModel.java:445;
    # AirportBusSeatMapViewModel.java:542; PayViewModel.java:4686,4725,4805,4847;
    # BasketTicketViewModel.java:3232; MyReservationViewModel.java:1557. 여정번호·변경번호의 보호 기본값은 길이만으로 확인할
    # 수 없습니다.
    journey_count = response.journey_count
    legs = None
    if isinstance(journey_count, str) and journey_count.strip().isdigit():
        legs = int(journey_count)
    pnr_no = _successful_hold_pnr(
        response,
        context="KORAIL cancellation requires a fresh successful unpaid hold",
    )
    if not isinstance(journey_count, str) or legs is None or legs < 1:
        raise KorailProtocolError(
            "KORAIL cancellation requires a fresh successful unpaid hold"
        )
    # 순번·변경번호는 홀드 응답의 첫 여정 값을 되울립니다. 7.0.6 예약목록
    # (MyReservationViewModel.java:1557,1566)과 결제 화면
    # (PayViewModel.java:4678-4686)이 그렇게 하고, 결제 화면은 값이 없을 때만
    # AlienGuard 로 보호된 대체 리터럴(4·3바이트)을 씁니다. 대체값 "0001"/"000"
    # 은 복호값이 아니라 라이브 확인값입니다 — 2026-09-22 reserve/
    # reserve_transfer/reserve_merge/recalculate_price 응답의 여정 행 45개 중
    # h_rsv_chg_no 를 가진 행은 0개였고, "000" 으로 보낸 취소는 모두
    # IRG000000 으로 성립했습니다.
    first = response.journeys[0] if response.journeys else None
    sequence = first.journey_sequence if first is not None else None
    change_no = first.reservation_change_no if first is not None else None
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtJrnySqno": sequence if sequence else "0001",
            "txtJrnyCnt": journey_count,
            # DTO 는 공통 4+고유 4필드(ReservationCancelChkIn.java:29-32,53)이나 전송 개수는 가변입니다.
            # lang 기록 여부는 인코더 설정과 언어 제공자에 따릅니다(CommonIn.java:467-474).
            "hidRsvChgNo": change_no if change_no else "000",
        }
    )
    return form


# 결제 시퀀스가 없을 때 쓰는 000000 은 라이브러리 정책이며 앱 기본값은 미확인입니다. 2026-07 라이브 2건은 시퀀스를 모두 제공했으므로 이 폴백을 검증한 표본이
# 아닙니다. 결제는 FieldMap(NetworkApi.java:630-632,646-648)이며 null 값을 자동 생략한다고 볼 수 없습니다
# (ParameterHandler.java:252-259 의 Field 와 :276-293 의 FieldMap 은 처리가 다릅니다).
_ABSENT_JOB_SEQUENCE = "000000"


def _echoed_job_sequence(value: str | None) -> str:
    """홀드 시퀀스를 에코합니다. 숫자로 온 값의 앞자리 0 을 복원하지 않습니다. 결제 응답→hidTmpJobSqno 경로의 앱 근거는 미확인입니다.
    TripChgPrsCIn.java:47 은 여정변경 입력이므로 그 근거로 대체하지 않습니다.
    """
    if isinstance(value, str) and value.strip():
        return value
    return _ABSENT_JOB_SEQUENCE


# 응답 첫 여정의 변경번호가 없을 때의 대체값입니다. 항상 없음으로 가정하지 않습니다. 2026-09-22: reserve/reserve_transfer/reserve_merge 의
# 45여정 모두 해당 키가 없었고, 같은 예약을 목록으로 되읽으면 000 이었습니다. 표본 밖의 응답을 보장하지 않습니다. 앱은 응답값 또는 보호 기본값을
# 사용합니다(PayViewModel.java:6581-6593). 대체값은 앱 보호 문자열의 복호 결과가 아니라 관측에 근거한 선택입니다.
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
    """홀드·카드 입력으로 결제 폼을 만듭니다. 실제 전송은 결제 시도를 일으킬 수 있습니다. 정산액은 hold.received_amount 를 사용하며 total_price 로
    대체하지 않습니다. 일반 예약의 앱 금액 흐름은 PayViewModel.java:11027-11028,11303-11307,11368,11440 과
    PayAmountUiData.java:65,248-249, ReservationOut.java:452 참고. initAmountData 의 jadx 중복 경고로 모든 분기 수를
    확정할 수 없습니다. 기존 smali 근거는 PayViewModel.smali:25740-27914 입니다. h_tot_prc 가 UI 전용이라는 주장은 하지 않습니다.

    포인트·마일리지 병용은 구현하지 않습니다(PaymentMethodHelper.java:89-137,587-689). 앱의 미병용 경로는 hidPontDvCd1 도
    넣지만(:130) 보호값을 모르므로 라이브러리는 생략합니다. 관측된 결제 성공이 누락 필드·시퀀스 폴백·모든 카드 조합의 성공을 보장하지 않습니다. 카드 정보는 폼에 들어가므로
    로그·예외 원문 노출에 주의하십시오.
    """
    if not isinstance(card, CardPayment):
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    window_no = hold.window_no
    # 좌석별 정산액·합계가 없으면 거절합니다. total_price 를 실제 정산액으로 대체하지 않습니다.
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
    # 숫자 모양 검사만으로 카드 유효성이나 비과금을 보장하지 않습니다.
    if (
        not isinstance(card.card_number, str)
        or _DIGITS_RE.fullmatch(card.card_number) is None
    ):
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
            # 클라이언트 결제는 로그인 전용입니다. 앱은 로그인 여부로 이 필드를 나눕니다 (PayViewModel.java:6600-6604;
            # FPayViewModel.java:772-778). 양쪽 상수는 보호돼 있으며 Y 가 앱의 회원 값이라는 직접 근거는 없습니다.
            "hiduserYn": "Y",
        }
    )
    return form


def _refund_echo_field(value: object, *, field: str) -> str:
    """국내 앱은 상세의 pbpAcepTgtFlg 를 전달합니다(MyTicketDetailViewModel.java:1521). 외국인 경로는 보호
    상수입니다(FTicketDetailViewModel.java:634). 응답 필드는 선택적이나 기본값 평문은 보호돼 있습니다(TicketDetailOut.java:167).
    2026-09-21 발권·환불 기록에서 상세에 후보 키가 없었고 빈 값으로 만든 환불 폼이 성공했습니다. 라이브러리는 None 만 빈 문자열로 바꾸며 실제 전송에서는 빈 필드가
    생략됩니다.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL refund {field} must be a string echoed from a prior "
            "server response"
        )
    return value


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
    *,
    settle_mileage: bool = False,
    pbp_acceptance_target_flag: str | None = None,
) -> dict[str, str]:
    """승차권 한 장의 환불 폼. PNR 키는 txtPnrNo 입니다(RefundTicketIn.java:194; NetworkApi.java:603).
    settle_mileage=False 는 라이브러리 기본 정책입니다. 앱의 수수료·마일리지 비교와 선택 흐름은
    MyTicketDetailViewModel.java:1811-1858, 선택값 전달은 :1466-1469,1515-1521,2074-2093 이지만 기본 bool·Y/N 평문은
    보호돼 있습니다.

    pbp_acceptance_target_flag 는 명시값 또는 승차권 값을 사용합니다. 값 누락 시 처리와 국내/외국인 차이는 _refund_echo_field 참고. 보호
    기본값을 빈 문자열로 확정하지 않습니다. tk_ret_tms_dv_cd 는 이 빌더에서 생략합니다. 두 앱 구성 지점은 null 을 넘기고
    (MyTicketDetailViewModel.java:1521; FTicketDetailViewModel.java:634), DTO 기본값도 null 입니다
    (RefundTicketIn.java:135). 이 사실만으로 모든 직렬화 설정에서 키가 없다고 단정하지 않습니다. 수수료 응답의 같은 필드는
    RefundTicketViewModel.java:1012 의 UI 판단에 쓰입니다.
    """
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
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": ticket.pnr_no,
            "h_orgtk_sale_dt": ticket.sale_date,
            "h_orgtk_sale_wct_no": ticket.sale_window_no,
            "h_orgtk_sale_sqno": ticket.sale_sequence,
            "h_orgtk_ret_pwd": ticket.return_password,
            "h_mlg_stl": "Y" if settle_mileage else "N",
            "pbpAcepTgtFlg": _refund_echo_field(
                (
                    pbp_acceptance_target_flag
                    if pbp_acceptance_target_flag is not None
                    else ticket.pbp_acceptance_target_flag
                ),
                field="pbp_acceptance_target_flag",
            ),
        }
    )
    # tk_ret_tms_dv_cd 는 라이브러리에서 생략합니다. 앱 입력의 null 근거는 위 docstring 참고.
    return form


def build_station_refund_execution_form(
    config: KorailConfig,
    request: StationRefundExecutionRequest,
) -> dict[str, str]:
    """역발행 승차권의 확인 결과로 실행 폼을 만듭니다. 12키는 ExecuteOnlineRefundsIn.java:60. 입력 타입은
    StationRefundExecutionRequest 에서 검증하며 클라이언트 실행은 로그인이 필요합니다.
    """
    if not isinstance(request, StationRefundExecutionRequest):
        raise KorailProtocolError(
            "KORAIL station refund requires an exact execution request"
        )
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
    # 필수 12값은 StationRefundExecutionRequest.__post_init__ 에서 검사합니다.
    form.update(
        (wire_name, getattr(request, attribute)) for wire_name, attribute in fields
    )
    return form


def _required_mutation_text(
    value: object,
    *,
    field: str,
    context: str = "discount card request",
    allow_blank: bool = False,
) -> str:
    if not isinstance(value, str) or (not allow_blank and not value.strip()):
        raise KorailProtocolError(
            f"KORAIL {context} requires a non-empty {field}"
        )
    return value


def build_discount_card_purchase_form(
    config: KorailConfig,
    request: DiscountCardPurchaseRequest,
) -> dict[str, str]:
    """N카드 미결제 구매 폼. 단일 FieldMap 라우트(NetworkApi.java:336-337)와 NCardInfoIn.java:29-39, NCardjrny.java:55
    의 @SerialName 을 따릅니다. 배열 평탄화: NetworkService.java:15345-15367. 부가사용자 키·보호 기본값·최종 순서와 실제 구매 수용 여부는
    미검증입니다.
    """
    if not isinstance(request, DiscountCardPurchaseRequest):
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
        if not isinstance(section, DiscountCardSectionRequest):
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
        form[f"trnNo_{index}"] = _required_mutation_text(
            section.train_no,
            field="train_no",
        )
        form[f"dptRsStnCd_{index}"] = _required_mutation_text(
            section.departure_station_code,
            field="departure_station_code",
        )
        form[f"arvRsStnCd_{index}"] = _required_mutation_text(
            section.arrival_station_code,
            field="arrival_station_code",
        )
    users = tuple(request.additional_users)
    # 이 입력 모델은 부가사용자 _1 키 한 묶음만 표현합니다(NCardInfoIn.java:29-39).
    if len(users) > 1:
        raise KorailProtocolError(
            "KORAIL discount card purchase takes at most 1 additional user"
        )
    if users:
        form["apdUsrCnt"] = str(len(users))
        for index, user in enumerate(users, start=1):
            if not isinstance(user, DiscountCardAdditionalUser):
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
    """N카드 연장용 POST 폼입니다. 이름의 query 와 달리 GET 요청이 아닙니다 (NetworkApi.java:518-520). 원승차권의 네 자격증명은
    MyTicketDetailViewModel.java:1049 에서 읽습니다(TicketDetailOut.java:117,458-470). 키
    saleWctNo/saleDd/saleSqno/tkRetPwd 는 NCardExtensionIn.java:31-34,55,158 의 속성명에서 추정했으며 serializer
    이름은 보호돼 있습니다. lang 포함 여부로 빌더 필드 수가 달라집니다 (CommonIn.java:467-474). 라이브 연장은 미검증입니다.
    """
    if not isinstance(ticket, DiscountCardTicket):
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


#: 가능한 승객 행 키 접두사 최대 여덟 개. 일반 예약에서는 0명 행을 전송하지 않으며, N카드 홀드는 존재하는 행을 한 행으로 대체합니다.
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
    """N카드 승객 블록으로 미결제 홀드를 만듭니다. 결제를 수행하지 않습니다. 같은 예약 라우트(NetworkApi.java:752-753)에서 N카드 분기는
    Passengers.java:731,765-766, 네 승객 키는 TicketReservationInPassengerInfo.java:55,105-117 입니다.
    ReqDiscount.java:36 의 N_CARD 코드 평문은 보호돼 있고 이 경로의 라이브 수용은 미검증입니다.
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
    # 기존 메뉴 키의 위치를 유지한 채 값만 교체합니다.
    rebuilt["txtMenuId"] = KORAIL_DISCOUNT_CARD_MENU_ID
    return rebuilt


_PRICE_RECALCULATION_ROW_FIELDS: tuple[tuple[str, str], ...] = (
    ("psg_tp_dv_cd", "passenger_type_code"),
    ("hidDcntKndCd", "requested_discount_code"),
    ("dcnt_knd_cd1", "discount_kind_code"),
    ("hidDscpNo", "certificate_no"),
    ("psrm_cl_cd", "room_class_code"),
    ("hidFmlyNo", "family_sequence_no"),
)

#: 폼 전체에 하나씩 가는 선택 스칼라 넷. 행 리스트와 달리 개수가 없습니다.
_PRICE_RECALCULATION_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("txtPsrmClCd1", "cabin_class_code"),
    ("txtSeatAttCd2", "seat_attribute_code_2"),
    ("txtSeatAttCd4", "seat_attribute_code_4"),
    ("txtSeatAttCd5", "seat_attribute_code_5"),
)


# 네 선택 스칼라는 PriceReCalculationIn.java:38-41,114-133 의 nullable 속성입니다. 키는 속성명에서 추정했으며 serializer 이름은
# 보호돼 있습니다 (PriceReCalculationIn$$serializer.java:44-47). 값 채움은 라이브 미검증입니다. 일반 경로의 default-null 기존 근거:
# PayViewModel.smali:11834-11850. smali 대조 필요.
def build_price_recalculation_form(
    config: KorailConfig,
    request: PriceRecalculationRequest,
) -> dict[str, str | list[str]]:
    """할인 재계산 폼. NetworkApi.java:583-584 의 여섯 병렬 List 필드를 반복 키로 보냅니다. 결제 화면 입력은
    PayViewModel.java:1233,1308-1316 으로 이어집니다. 입력 생성의 기존 근거는 PayViewModel.smali:11291,11834-11850,
    PayViewModel$executeDiscountPrice$1.smali:420,543 이며 jadx 복원 실패 부분은 smali 대조가 필요합니다.
    """
    if not isinstance(request, PriceRecalculationRequest):
        raise KorailProtocolError(
            "KORAIL price recalculation requires an exact "
            "PriceRecalculationRequest"
        )
    pnr_no = _required_mutation_text(
        request.pnr_no, field="pnr_no", context="price recalculation"
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
        if not isinstance(row, PriceRecalculationRow):
            raise KorailProtocolError(
                "KORAIL price recalculation requires exact "
                "PriceRecalculationRow values"
            )
        for wire_name, attribute in _PRICE_RECALCULATION_ROW_FIELDS:
            value = getattr(row, attribute)
            # 빈 문자열은 유효한 자리표시자입니다. None 은 목록 전송에서 빠져 다른 병렬 목록과 인덱스가 어긋날 수 있으므로 문자열만 허용합니다.
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
        # 명시한 비회원 번호가 있을 때 두 필드를 함께 추가하는 빌더 동작입니다. 클라이언트 재계산은 여전히 로그인 필요합니다. 앱 속성:
        # PriceReCalculationIn.java:32,34,114-129; 구성: PayViewModel.java:6167-6168; 기존 smali 근거
        # :11764-11805,11834-11850. 전송 키와 N 리터럴의 평문은 보호돼 직접 확인되지 않았습니다.
        form["hiduserYn"] = "N"
        form["hidCustNo"] = non_member_no
    form["txtPsgGridcnt"] = str(len(rows))
    for wire_name, _ in _PRICE_RECALCULATION_ROW_FIELDS:
        form[wire_name] = columns[wire_name]
    # 네 스칼라는 호출자가 준 것만 포함합니다. 앱 일반 입력의 기존 근거는 위 주석 참고.
    for wire_name, attribute in _PRICE_RECALCULATION_SCALAR_FIELDS:
        value = getattr(request, attribute)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(
                f"KORAIL price recalculation {attribute} must be a non-empty "
                "string when present"
            )
        form[wire_name] = value
    return form


def build_cart_add_form(
    config: KorailConfig,
    request: CartAddRequest,
) -> dict[str, str]:
    """홀드 PNR 의 장바구니 추가 폼. AddCartListIn.java:25,30,52,79 는 CommonIn 외 hidPnrNo 하나를 선언합니다. 라우트:
    NetworkApi.java:266-267; 호출 예: PayViewModel.java:5942, TrainSeatMapViewModel.java:267,
    TrainScheduleViewModel.java:370, ReservationMergeViewModel.java:164,
    AirportBusSeatMapViewModel.java:159. 선택 lang 때문에 공통 필드 수는 고정이 아닙니다(CommonIn.java:467-474). 추가 응답의
    할인 행 구조는 CartAddResponse 를 참고하십시오.
    """
    if not isinstance(request, CartAddRequest):
        raise KorailProtocolError(
            "KORAIL cart request requires an exact CartAddRequest"
        )
    pnr_no = _required_mutation_text(
        request.pnr_no, field="pnr_no", context="cart request"
    )
    form = _common_fields(config)
    form["hidPnrNo"] = pnr_no
    return form
