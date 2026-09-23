# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태를 바꾸는 라우트의 요청 폼 빌더.

예약(직통·환승·병합·예약대기·좌석지정), 미결제 취소, 카드 결제, 환불, 역발행
승차권 환불, 운임 재계산, 할인카드(N카드) 구매·연장·예약, 장바구니 추가의 폼을
만듭니다. 읽기 쪽은 :mod:`korail_mobile_api.payloads` 와
:mod:`korail_mobile_api.read_payloads` 입니다.

여기 함수들은 dict 를 만들 뿐 아무것도 보내지 않습니다. 실제 전송은
:meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 하나이고, 그 앞에
라우트·범주·폼 모양 세 가지 단언이 있습니다. 역발행 환불만 따로 ``V7Gateway.call``
로 나가면서 그중 폼 모양 단언을 건너뛰던 것은 없어졌습니다.

**라이브로 확인된 것과 아닌 것.** 즉시·좌석지정·예약대기·입석+좌석 홀드(다인·특실
포함), 환승 홀드, 결제 전 취소, 카드 결제, 환불, 장바구니 담기는 실서버가 받아들인
것을 확인했습니다. 병합예약의 두 번째 홀드(:func:`build_merge_reservation_form`),
역발행 승차권 환불, 운임 재계산, 할인카드 구매·연장·예약 폼은 전송된 적이 없습니다.
예약대기에서 입석 플래그를 ``"N"`` 으로 박는 근거는
:func:`_build_journey_reservation_form` 안의 주석에 있습니다.
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
    """변경 폼의 공통 필드. 읽기 쪽
    :meth:`~korail_mobile_api.http.KorailHttpClient.common_fields` 와 같은 규칙입니다.

    ``lang`` 은 ``CommonIn`` 의 4번째 공통 필드이고(``CommonIn.java:381``)
    ``CommonIn`` 은 읽기·변경 입력 DTO가 모두 상속합니다. 그런데 여기서는
    빠져 있어서, ``KorailConfig(lang=...)`` 를 설정해도 읽기 요청에만 실리고
    예약·결제·환불에는 실리지 않았습니다. 기본값 ``None`` 이면 예전과 똑같이
    아무것도 싣지 않으므로, 달라지는 것은 실제 값을 넘긴 호출자뿐입니다.
    """
    fields = {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


# Passenger types are ordered here, but only positive counts are assigned
# consecutive wire indices. Passengers.toTicketReservationInput filters zero
# entries before indexing (7.0.6 Passengers.java:743-752).
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
    # 7.0.6 TrainScheduleViewModel.java:2914-2930,2982-2999: explicit
    # wheelchair/seat-type selection wins; otherwise the row's hSeatAttCd is
    # used when present, falling back to the basic selection code.
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
    """한 구간의 좌석지정 목록을 job 종류와 승객 구성에 비추어 검사합니다.

    좌석 목록은 ``"1103"`` 에만 속합니다. 7.0.6 도 좌석 목록을 설치하는 바로 그
    한 번의 ``copy()`` 안에서 job id 를 좌석지정 값으로 바꿉니다 —
    ``TrainSeatMapViewModel.buildTicketReservationIn()`` 이
    ``ui/screen/train/TrainSeatMapViewModel.java:2289`` 의 단일
    ``ticketReservationIn.copy(...)`` 에서 ``txtJobId`` 를
    ``ReservationJobId.SEAT.getJobId()``(``:2135``·``:2166``·``:2234``·``:2261``
    에서 읽음)로, ``srcarList``·``txtSrcarCnt`` 를 고른 좌석 목록과 그 개수로
    한꺼번에 덮어씁니다. 그 job id 리터럴 자체는 AlienGuard 로 보호되어 있어
    (``common/define/ReservationJobId.java:22``, 4바이트 암호문) 정적분석으로는
    값을 읽을 수 없고, ``"1103"`` 은 이 패키지의 라이브 확인값입니다.

    반대로 평범한 여정 빌더(``TrainScheduleViewModel.buildTicketReservationIn()``,
    ``ui/screen/train/TrainScheduleViewModel.java:2932``·``:3004``)는
    ``srcarList``·``txtSrcarCnt`` 자리에 아무것도 넘기지 않아 기본값(빈 리스트 /
    ``null``, ``network/model/TicketReservationIn.java:182``)으로 떨어집니다.
    그래서 ``"1101"``/``"1102"`` 요청에는 좌석 키가 한 개도 실리지 않습니다 —
    "맵을 비운다"가 아니라 "애초에 채우지 않는다"가 7.0.6 의 실제 모양입니다.

    이전 판의 근거 ``C5/a.java:143-146``·``C5/a.java:118`` 은 6.5.0 잔재입니다:
    7.0.6 디컴파일에 ``C5`` 패키지가 존재하지 않습니다.
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
    """승객 구성과 좌석 등급으로 예약(홀드) 폼을 만듭니다.

    ``seats`` 는 좌석지정 job 에서만 받습니다. 7.0.6 기준 전선 키는
    ``TicketReservationInSrcar`` 의 ``@SerialName`` 두 개
    (``network/model/TicketReservationInSrcar.java:51``, ``txtSrcarNo``·
    ``txtSeatNo``)와 후행 구간용 ``TicketReservationInSrcarTrailing``
    (``network/model/TicketReservationInSrcarTrailing.java:52``,
    ``txtSrcarNo1_``·``txtSeatNo1_``), 그리고 개수 키 ``txtSrcarCnt``/
    ``txtSrcarCnt1``(``network/model/TicketReservationIn.java:80``)입니다.

    **별도의 ``@FieldMap`` 이 아닙니다.** 이전 판은 이 자리를
    ``CertificationService.java:52-54`` 로 인용하며 "여정 키 뒤에 붙는
    ``@FieldMap``"이라고 했지만, 7.0.6 의 ``certification.TicketReservation``
    선언에는 ``@FieldMap`` 이 **하나**뿐입니다
    (``network/NetworkApi.java:752-753``). 요청 전체가 kotlinx 로 직렬화된
    ``TicketReservationIn`` 하나이고, 그것을 ``NetworkService.STLibw`` 가
    평평한 ``Map<String,String>`` 으로 펴서 그 한 맵으로 보냅니다
    (``network/NetworkService.java:14155-14162``, 펴는 함수는 ``:15304-15420``).
    ``CertificationService`` 클래스는 7.0.6 디컴파일에 없습니다.

    순서는 그래서 화면 코드가 아니라 DTO 선언 순서에서 나옵니다:
    ``TicketReservationIn.java:80`` 에서 ``txtSrcarCnt``/``txtSrcarCnt1`` 이
    ``srcarList``/``trailingSrcarList`` 보다 앞에 선언되므로 개수가 먼저 실리고,
    배열 원소 키에는 **1부터** 세는 인덱스가 붙습니다(``NetworkService.java:15350``
    의 ``i9 + 1``, 키 조립은 ``:15366``). ``txtSrcarCnt`` 는 호차 수가 아니라
    **좌석 수**입니다 — 7.0.6 은 고른 좌석마다
    ``TicketReservationInSrcar`` 하나를 만들고(``TrainSeatMapViewModel.java
    :2108-2113``) 그 리스트의 크기를 ``txtSrcarCnt`` 로 씁니다(``:2136-2138``).
    옛 인용 ``OSrcar.java:6-11``·``SeatSearchActivity.java:675-683`` 은 6.5.0
    잔재이며 두 클래스 모두 7.0.6 에 없습니다.
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
    """환승 여정의 예약(홀드) 폼을 만듭니다 — 두 구간, PNR 하나.

    :func:`build_reservation_form` 에서 여정 블록이 반복된 것입니다. 이전 판은
    "앱도 두 경우를 빌더 하나로 처리한다(``C5/a.java:52-119``)"고 적었는데,
    7.0.6 은 같은 DTO 를 만드는 **오버로드 두 개**로 갈라져 있습니다 —
    ``TrainScheduleViewModel.buildTicketReservationIn(TrainScheduleOutTrainInfo,
    …)``(``ui/screen/train/TrainScheduleViewModel.java:2849``)가 직통,
    ``…buildTicketReservationIn(List<TrainScheduleOutTrainInfo>, …)``(``:2937``)
    가 환승입니다. 둘 다 같은 ``TicketReservationIn`` 을 채우므로 전선 모양은
    하나고, 그 모양을 정하는 것은 여전히 구간 수뿐입니다. ``C5`` 패키지는
    7.0.6 디컴파일에 없습니다.

    * ``txtJrnyCnt`` 는 배열 길이에서 유도됩니다 — 환승 오버로드가 여정
      리스트의 ``size()`` 를 문자열로 바꿔 그 자리에 넣습니다
      (``TrainScheduleViewModel.java:3002-3004``). 플래그가 아니므로 직통
      예약이 환승 폼을 내보내게 만들 수 없습니다.
    * 여정 인덱스는 **1부터**입니다. 인덱스를 붙이는 것은 화면 코드가 아니라
      JSON→폼 평탄화기이고, 그 카운터가 1에서 시작합니다
      (``network/NetworkService.java:15350`` 의 ``i9 + 1``, 키 조립 ``:15366``).
    * ``txtJrnyTpCd{i}`` 는 인덱스도 길이도 보지 않습니다. 구간별 DTO 를 만드는
      ``TrainScheduleOutTrainInfo.toTicketReservationInput(boolean isTransfer,
      …)``(``network/model/TrainScheduleOutTrainInfo.java:3661``)가 **불리언
      인자 하나**로 두 리터럴 중 하나를 고르고(``:3674-3682``), 환승 오버로드는
      **두** 구간에 모두 ``isTransfer=true`` 를 넘깁니다
      (``TrainScheduleViewModel.java:2968``). 그래서 결론("두 구간이 같은 코드를
      싣는다")은 그대로지만 기구는 "길이 비교"가 아니라 플래그입니다. 리터럴
      자체는 AlienGuard 로 보호되어 있고, 암호문 길이가 2바이트라 ``"11"``/
      ``"14"`` 와 일관됩니다. 값 ``"14"`` 는 라이브 확인값입니다.
    * ``txtJrnySqno{i}`` 에 ``DecimalFormat("000")`` 은 없습니다. 7.0.6 은
      ``jrnySqno`` 를 인자로 받아 그대로 실어 보내고
      (``TrainScheduleOutTrainInfo.java:3683``), 1구간은 ``$default`` 가 넣는
      3바이트 보호 리터럴(``:1631``), 2구간은 호출부가 넘기는 다른 3바이트 보호
      리터럴(``TrainScheduleViewModel.java:2968``)입니다 — 포맷팅이 아니라 고정
      상수 두 개입니다. 암호문 길이가 ``"001"``/``"002"`` 와 일관되고 그 두 값은
      라이브 확인값입니다. 옛 인용 ``S4/O.java:19-21`` 은 6.5.0 잔재입니다.
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
    legs: Sequence[TrainScheduleItem],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """병합예약의 **두 번째** 홀드 폼을 만듭니다 — 열차 하나, 여정 둘.

    병합은 환승이 아닙니다. 물리적으로 한 대인 열차를 중간역에서 갈라 두 구간을
    다르게 앉히는 것입니다(좌석+좌석 또는 좌석+입석). 다섯 단계 전체 흐름은
    :data:`~korail_mobile_api.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` 에
    있습니다 — 이 폼이 두 여정을 루프로 만든다는 서술의 출처였던
    ``DirectInquiryActivity.java:576-601`` 은 6.5.0 잔재이며(그 클래스 자체가
    7.0.6 디컴파일에 없습니다), 7.0.6 이 실제로 최종 재제출을 어떻게 만드는지
    (정적분석으로 완전히 확정하지 못한 부분 포함)와 이 폼의 아래 세 규칙이
    실서버로는 검증됐다는 근거는 같은 위치의 주석에 적어 뒀습니다.

    * ``txtJrnyTpCd{i}`` 가 루프 **인덱스**를 봅니다. 1구간은 ``"21"``(병합
      선행), 2구간은 ``"22"``(병합 후행)입니다. 환승은 두 구간이 모두 ``"14"``
      인데 여기서는 갈립니다(``smali:5641`` — 이 스몰리 오프셋은 6.5.0
      기준이라 7.0.6 에서 같은 줄을 가리키지는 않지만, 값 자체("14" 대
      "21"/"22")는 이 저장소의 다른 곳(``KORAIL_DIRECT_JOURNEY_TYPE_CODE``
      등)과 일관됩니다).
    * ``txtStndFlg`` 를 ``"Y"`` 로 고정해 보냅니다. 전환 대상이 입석 홀드라는
      것이 이 흐름의 전제이기 때문입니다.
    * ``txtPsrmClCd2`` 는 ``txtPsrmClCd1`` 에서 **복사**됩니다. 그래서
      ``seat_class`` 를 구간별이 아니라 **하나**만 받습니다 — 두 반쪽이 서로
      다른 등급인 병합 예약은 만들 수 없습니다.
    """
    resolved_legs = _resolved_sequence(
        legs, "KORAIL 병합 reservation requires a sequence of merge-seat legs"
    )
    for leg in resolved_legs:
        if not isinstance(leg, TrainScheduleItem):
            raise KorailProtocolError(
                "KORAIL 병합 reservation legs are the TrainScheduleItem rows "
                "research.mergeSeatsC.do answers with"
            )
    if len(resolved_legs) != KORAIL_MAX_JOURNEY_LEGS:
        raise KorailProtocolError(
            f"KORAIL 병합 reservation books exactly {KORAIL_MAX_JOURNEY_LEGS} "
            f"journeys on one train, got {len(resolved_legs)}: this form has "
            "no journey-3 spelling at all (KORAIL_MAX_JOURNEY_LEGS)"
        )
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif not isinstance(passengers, KorailPassengerCounts):
        raise KorailProtocolError(
            "KORAIL reservation requires an exact KorailPassengerCounts"
        )
    cabin = _coerced_seat_class(seat_class)
    # The two halves must be the one train the standing hold was placed on.
    # The app never checks this because it cannot be otherwise -- the rows come
    # straight back from mergeSeatsC.do, which was asked about that train. 7.0.6:
    # ReservationMergeViewModel.buildMergeSeatsCInput() (java:760-828, smali
    # :773-1242) sends it as the wire field "trnNo" (MergeSeatsCIn.java:63,
    # renamed from the old "txtTrnNo1" -- this form asks about one train, not a
    # numbered leg) sourced from the standing hold's own echoed journey info
    # (reservationOutJrnyInfo.getHTrnNo()) -- but a caller assembling the call
    # by hand can get it wrong, and a merged booking of two unrelated trains is
    # a 환승 spelled with the wrong journey type.
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
    journeys = tuple(_journey_fields(leg) for leg in resolved_legs)
    form = _common_fields(config)
    form.update(
        {
            "txtMenuId": "11",
            # Back to "1101". The "1202"/MERGE job id belongs to the standing
            # hold this one replaces. 7.0.6 static analysis of the actual
            # resubmission (ReservationMergeViewModel.smali:7736-7772,
            # TicketReservationIn.copy$default) suggests the app may instead
            # KEEP the original hold's job id through to the final POST rather
            # than reset it -- that reading is not fully confirmed (jadx
            # decompile of this method failed, reconstructed from smali) and
            # directly contradicts what this line has always sent. Left as
            # "1101" because that is what this package's own live test
            # confirmed working end to end (2026-09-21: reserve_merge on
            # 서울->울산 train 023 returned h_jrny_tp_cd "21"/"22" as expected)
            # -- changing a live-verified value on unconfirmed static
            # reconstruction alone would be reckless. If a live test ever
            # shows "1101" failing where the original hold's job id would
            # have worked, that is the evidence to act on, not this comment.
            "txtJobId": KorailReservationJobType.IMMEDIATE.value,
            "txtGdNo": "",
            "hidFreeFlg": "N",
            # Pinned, not derived. smali:5887-5891 is a bare const-string "Y".
            "txtStndFlg": "Y",
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    # OSeat. The merge loop re-puts journey 1's pair and appends journey 2's,
    # into the LinkedHashMap the standing hold left behind, so the order is the
    # ordinary two-leg order -- see build_transfer_reservation_form.
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): _seat_attribute_code(
                standing_hold_train, seat_attribute_code
            ),
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": cabin.value,
        }
    )
    form[_seat_attribute_key(2)] = _seat_attribute_code(
        standing_hold_train, seat_attribute_code
    )
    # Copied, not read per leg (smali:5919-5983).
    form["txtPsrmClCd2"] = cabin.value
    form["txtJrnyCnt"] = KORAIL_TRANSFER_ITINERARY_CODE
    journey_type_codes = tuple(
        KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE
        if journey == 1
        else KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE
        for journey in range(1, len(journeys) + 1)
    )
    _write_journey_rows(form, journeys, journey_type_codes)
    # No OSrcar. 7.0.6's ordinary journey builder leaves the srcarList /
    # txtSrcarCnt slots unset, so they fall to their defaults -- an empty list
    # and null (TicketReservationIn.java:182, filled at
    # TrainScheduleViewModel.java:2932 and :3004) -- and an empty list plus a
    # null scalar contribute no form fields at all. So it is "never populated",
    # not "cleared". The old citation C5/a.java:118 is 6.5.0 jetsam; there is
    # no C5 package in the 7.0.6 decompile.
    return form


def is_merge_eligible(
    train: TrainSummary,
    *,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
) -> bool:
    """이 조회 행에 앱이 입석+좌석 예매를 제시할지.

    등급별 플래그 집합(:data:`~korail_mobile_api.KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`)
    으로 풀어 쓴 것입니다. 7.0.6 에서 같은 판정을 하는 것은 조회 행 DTO 자신의
    ``isCombination()``/``isSpecialCombination()`` 두 메서드이고, 둘 다
    ``h_yms_apl_flg``(속성명 ``hYmsAplFlg``) **하나만** 봅니다 —
    ``network/model/TrainScheduleOutTrainInfo.java:1500-1525``(일반실),
    ``:1527-1552``(특실). 그 결과는 등급별 예약상태로 올라가
    ``generalReservationStatus()`` 가 ``COMBINATION``/``COMBINATION_WAIT``
    (``:2842-2847``), ``specialReservationStatus()`` 가 ``COMBINATION``
    (``:3588-3589``)을 돌려주는 경로가 됩니다.

    **다만 집합의 크기가 다릅니다.** 7.0.6 의 두 메서드는 각각 보호된 1바이트
    리터럴 **셋**을 비교하고 그중 둘은 두 등급이 공유합니다(일반실 = {A,C,D},
    특실 = {B,C,D} 꼴). 이 패키지의 상수는 등급당 둘이고 하나만 공유합니다.
    리터럴이 AlienGuard 로 보호되어 실제 값을 복구할 수 없으므로 어느 쪽이
    맞는지 정적분석으로는 확정할 수 없고, 상수를 넓히면 서버가 거절할 행에
    홀드를 걸 수 있으므로 여기서는 좁은 쪽을 그대로 둡니다. 이 함수가 틀릴 수
    있는 방향은 "될 행을 거절"뿐입니다.

    옛 인용 ``S4/J.java:61-63``(``isMixedSeat``)·``a5/u.java:378-380``·``:394-397``
    은 6.5.0 잔재이며 두 클래스 모두 7.0.6 디컴파일에 없습니다. 예매 버튼
    문구를 바꾸고 ``"1202"`` 를 붙이는 UI 경로는 7.0.6 에서 다시 찾지
    못했습니다 — 미출처.
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


# The app's own key-selection methods, which are the reason a third leg is
# impossible rather than merely unsupported: every one of them is a two-way
# `i == 1 ? … : …`, so a journey-3 write lands on the journey-2 key.
def _seat_attribute_key(journey: int) -> str:
    """좌석 속성 키 — 7.0.6 ``TicketReservationIn`` 의
    ``txtSeatAttCd4``(``@SerialName``,
    ``network/model/TicketReservationIn.java:80``·``:237-239``)와 후행 구간용
    ``txtSeatAttCd4_1``(속성명 ``trailingTxtSeatAttCd4``, 같은 파일 ``:80``·
    ``:189-191``). 후행 키가 하나뿐이므로 3구간 자리가 없습니다. 옛 인용
    ``OSeat.java:32-35`` 은 6.5.0 잔재 — 7.0.6 에 ``OSeat`` 클래스가 없습니다.
    """
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    """좌석 수 키 — 7.0.6 ``TicketReservationIn`` 의 ``txtSrcarCnt``
    (``network/model/TicketReservationIn.java:80``·``:245-247``)와 후행 구간용
    ``txtSrcarCnt1``(속성명 ``trailingTxtSrcarCnt``, 같은 파일 ``:80``·
    ``:193-195``). 옛 인용 ``OSrcar.java:21-23`` 은 6.5.0 잔재입니다.
    """
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    """호차번호 키 — 7.0.6 ``TicketReservationInSrcar`` 의 ``txtSrcarNo``
    (``network/model/TicketReservationInSrcar.java:51``·``:85``)와 후행 구간용
    ``TicketReservationInSrcarTrailing`` 의 ``txtSrcarNo1_``
    (``network/model/TicketReservationInSrcarTrailing.java:52``·``:86``).
    좌석 인덱스는 폼 평탄화기가 1부터 붙입니다
    (``network/NetworkService.java:15350``·``:15366``). 옛 인용
    ``OSrcar.java:25-30`` 은 6.5.0 잔재입니다.
    """
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    """좌석번호 키 — 7.0.6 ``TicketReservationInSrcar`` 의 ``txtSeatNo``
    (``network/model/TicketReservationInSrcar.java:51``·``:81``)와 후행 구간용
    ``txtSeatNo1_``(``network/model/TicketReservationInSrcarTrailing.java:52``·
    ``:82``). 옛 인용 ``OSrcar.java:14-19`` 은 6.5.0 잔재입니다.
    """
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


_T = TypeVar("_T")


def _coerced_seat_class(value: object) -> KorailSeatClass:
    """``"1"``(일반실)·``"2"``(특실) 또는 :class:`KorailSeatClass` 만 받습니다."""
    try:
        return KorailSeatClass(value)
    except ValueError:
        raise KorailProtocolError(
            'KORAIL reservation seat class must be "1" (일반실) or "2" (특실)'
        ) from None


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
    """예약 하나의 구간들을 타입과 개수로 검사합니다.

    ``require`` 는 호출자가 요구하는 정확한 개수(환승 예약이면 2)이거나 "앱이
    지원하는 만큼"을 뜻하는 ``None`` 입니다. 단일 구간 빌더는 ``None`` 을 넘기고
    자기 거부 메시지를 유지합니다.
    """
    resolved = _resolved_sequence(
        legs, "KORAIL reservation requires a sequence of legs"
    )
    for leg in resolved:
        if not isinstance(leg, TrainSummary):
            raise KorailProtocolError(
                "KORAIL reservation requires an exact TrainSummary"
            )
    if require is not None and len(resolved) != require:
        # NOTE: the message below still names OSeat.java:32-35 and
        # OSrcar.java:21-30. Both are 6.5.0 jetsam -- neither class exists in
        # the 7.0.6 decompile -- but the message is a runtime string, not a
        # comment, so it is left byte-identical here and reported instead. The
        # 7.0.6 evidence for the same fact is the DTO itself: TicketReservationIn
        # declares exactly one trailing-journey spelling per key
        # (txtSeatAttCd4_1 / txtSrcarCnt1, TicketReservationIn.java:80) and one
        # trailing srcar DTO (TicketReservationInSrcarTrailing.java:52), so a
        # third leg has no key to land on and would overwrite leg 2.
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
    """구간당 등급 하나. 값 하나로 주거나 구간별 시퀀스로 주면 됩니다.

    구간별인 것은 앱이 구간별이기 때문입니다. 7.0.6 의 환승 빌더는 등급을
    ``List<? extends PsrmType> psrmTypes`` 로 받아 1·2구간 몫을 따로 꺼내고
    (``ui/screen/train/TrainScheduleViewModel.java:2952-2957``) 각 구간의
    ``toTicketReservationInput(…, psrmType.getPsrmClCd(), …)`` 로 넘깁니다
    (``:2968``). 즉 ``txtPsrmClCd`` 는 구간 DTO 의 필드이고
    (``network/model/TicketReservationInJrny.java:69``·``:234``) 인덱스는 폼
    평탄화기가 붙여 ``txtPsrmClCd1``/``txtPsrmClCd2`` 가 됩니다. 옛 인용
    ``C5/a.java:59``·``:97`` 은 6.5.0 잔재입니다.
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
    """공개 예약 폼 둘 뒤에 있는 단 하나의 빌더.

    구현 하나가 직통 예약과 환승 예약을 모두 덮습니다. 다른 것은 구간 수뿐이고,
    구간이 하나인 호출은 키 순서까지 단일 구간 폼과 동일한 바이트를 냅니다.

    이전 판은 이것을 "``C5/a.java:52-119`` 가 열차 배열을 도는 루프 하나"라는
    근거로 정당화했지만 그 클래스는 6.5.0 잔재입니다. 7.0.6 은 오히려
    오버로드 **둘**로 갈라져 있습니다 — 직통
    ``ui/screen/train/TrainScheduleViewModel.java:2849``, 환승 ``:2937``.
    합쳐도 되는 근거는 "앱이 루프 하나"가 아니라 "두 오버로드가 같은
    ``TicketReservationIn``(``network/model/TicketReservationIn.java:139-179``)을
    채우고, 전선 모양은 그 DTO 하나가 정한다"는 쪽입니다.
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
        ) from None
    # STANDBY와 MERGE_STANDING의 "구간 하나만" 규칙은 예전에 여기서도 거절했지만,
    # 그 근거로 적었던 a5/k.java:120-127, a5/u.java:346-360/:394-397 은 6.5.0
    # 잔재입니다 — 두 클래스 모두 7.0.6 디컴파일에 없습니다. 그 주장 자체도
    # "앱 UI가 버튼을 활성화하지 않는다"는 것뿐이었습니다. 이 패키지에는 UI 가
    # 없고, 잘못된 job_type·구간 수 조합을 받았을 때 서버가 스스로 거절하도록
    # 둡니다.
    #
    # 7.0.6 에서 구조적으로 확인되는 것은 등급 쪽 제약뿐입니다:
    # network/model/TrainScheduleOutTrainInfo.java:3587-3625 의
    # specialReservationStatus() 는 WAIT / STAND / FREE 를 **한 번도** 돌려주지
    # 않고, generalReservationStatus()(:2810-2890)만 WAIT(:2840,:2849)·
    # STAND(:2887)·FREE(:2889)를 돌려줍니다. "구간이 하나여야 한다"는 쪽은
    # 7.0.6 에서 대응 지점을 찾지 못했습니다 — 미출처.
    assignments = _validated_leg_seats(
        leg_seats,
        leg_count=len(resolved_legs),
        job_type=job_type,
        passenger_total=passengers.total,
    )
    # strict=True 는 새 제약이 아니라 이미 성립하는 불변식을 검사로 바꾼 것이다.
    # _validated_seat_classes() 가 leg 당 정확히 하나의 좌석등급을 보장한다.
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
            # 7.0.6 computes it as
            #   psrmType == PsrmType.GENERAL
            #     && train.generalReservationStatus() == TrainReservationStatus.STAND
            # (ui/screen/train/TrainScheduleViewModel.java:2870-2874, single
            # leg). STAND is itself reached only when h_gen_rsv_cd equals the
            # SOLD_OUT code AND h_stnd_rsv_cd equals the AVAILABLE code --
            # network/model/TrainScheduleOutTrainInfo.java:2881-2889, whose two
            # codes come from TrainReservationCode.SOLD_OUT / .AVAILABLE
            # (common/define/TrainReservationCode.java:24, :21; both rsvCd
            # literals are AlienGuard-protected 2-char ciphertexts, so "13" and
            # "11" here are this package's live-verified readings, not decoded
            # constants). For "1101"/"1103" it is therefore always "N": neither
            # cabin those jobs accept can be in that state, since both demand
            # the AVAILABLE code. A standby train usually IS sold out, so the
            # rule has to be evaluated rather than pinned there.
            #
            # It is a property of the whole booking, not of a leg. 7.0.6's
            # transfer overload evaluates the same predicate per leg and ORs
            # the two: z (leg 1) || z2 (leg 2) -> z3, which is what goes into
            # txtStndFlg (TrainScheduleViewModel.java:2961-2967). The result is
            # identical to the old reading ("one standing leg makes the whole
            # itinerary standing"), but the mechanism is a plain OR of two
            # booleans, not "leg 1 assigns and later legs overwrite while the
            # value still reads N". The old citations c5/b.java:69,
            # S4/J.java:83-85 and C5/a.java:78-82 are 6.5.0 jetsam -- none of
            # those three classes exists in the 7.0.6 decompile.
            #
            # 예약대기("1102")만은 예외로 "N" 을 박습니다. 이 플래그는 서버에게
            # "입석을 사겠다"는 뜻이고, 예약대기 요청에 실리면 대기가 아니라 입석
            # 승차권 예약이 만들어집니다. 2026-09-16 실서버에서 같은 예약대기 열차
            # (h_wait_rsv_flg=" 9", h_gen_rsv_cd="13")에 이 값만 바꿔 두 번 보냈고,
            # "N" 은 SUCC/IRR000014 "예약대기 가능합니다", "Y" 는
            # SUCC/IRR000018 "결제하지 않으면 예약이 취소됩니다" 에 h_seat_no="입석",
            # h_tot_stnd_cnt="00001", 결제 기한까지 붙은 입석 예약을 돌려줬습니다.
            # 7.0.6 도 STAND 상태에서만 이 값을
            # 채우므로 WAIT 행은 거짓입니다(TrainScheduleViewModel.java:2870).
            "txtStndFlg": (
                "N"
                if job_type is KorailReservationJobType.STANDBY
                else _itinerary_standing_flag(
                    resolved_legs,
                    seat_classes=resolved_classes,
                )
            ),
            # 7.0.6 sends passengers.sum() here
            # (ui/screen/train/TrainScheduleViewModel.java:2912), and
            # Passengers.sum() adds up EVERY value in the dataMap with no
            # filtering (common/define/Passengers.java:610-616). The map is
            # keyed by PassengerType, which has exactly eight entries --
            # ADULT, CHILD, BABY, SENIOR, DISABILITY_SEVERE, DISABILITY_MILD,
            # GUIDE_DOG, TEENAGER (common/define/PassengerType.java:38-45) --
            # so 동반유아 (BABY) and 안내견 (GUIDE_DOG) are included. The old
            # citations w4/a.java:49 and m5/c.java:330 are 6.5.0 jetsam.
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    # The five txtSeatAttCd* keys, in the order TicketReservationIn declares
    # them: txtSeatAttCd1..5, then the trailing-journey txtSeatAttCd4_1
    # (network/model/TicketReservationIn.java:80 for the @SerialName list,
    # :139-179 for the declaration order the serializer follows). 순서를 정하는 것은 맵 삽입이
    # 아니라 DTO 선언입니다 -- 요청은 kotlinx 로 직렬화된 DTO 하나이고, 그
    # JSON 객체를 NetworkService.STLibw (network/NetworkService.java:15304-15343)
    # 가 선언 순서대로 훑습니다.
    #
    # 예전에 "이 경로에는 LinkedHashMap 이 없다" 고 적었던 것은 틀렸습니다 --
    # STLibw 자신이 :15306 에서 LinkedHashMap 을 만들어 결과를 담습니다. 맞는
    # 이야기는 "DTO 를 먼저 직렬화하므로 순서가 맵 삽입에 좌우되지 않는다" 이지
    # "맵이 없다" 가 아닙니다.
    # txtSeatAttCd1/2/3/5 are not written by either builder and fall to the
    # DTO's protected 3-char default (:96-100), which is consistent with the
    # "000" this builder sends. The old citations w4/a.java:82-91,
    # C5/a.java:84-97 and ReservationRequest.java:165-167 are 6.5.0 jetsam --
    # none of those three classes exists in the 7.0.6 decompile, and the
    # LinkedHashMap/putAll story they carried cannot happen in 7.0.6 at all.
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            _seat_attribute_key(1): resolved_attributes[0],
            "txtSeatAttCd5": "000",
            # txtPsrmClCd + journey number. In 7.0.6 this key belongs to the
            # per-journey DTO, not to a top-level seat block
            # (network/model/TicketReservationInJrny.java:69, :234) -- the
            # spelling this builder emits (txtPsrmClCd1 / txtPsrmClCd2) is the
            # same because the flattener appends the 1-based journey index
            # (network/NetworkService.java:15366), but it sits at a different
            # position in the DTO's declaration order. The value is
            # PsrmType.getPsrmClCd() (common/define/PsrmType.java:63-65) for
            # GENERAL or SPECIAL (:19-20); both psrmClCd literals are
            # AlienGuard-protected 1-char ciphertexts, so "1"/"2" here are
            # live-verified readings rather than decoded constants. The old
            # citations OSeat.java:8,16-18, c5/b.java:72 and U4/a.java:88 are
            # 6.5.0 jetsam.
            "txtPsrmClCd1": resolved_classes[0].value,
        }
    )
    for journey, seat_class in enumerate(resolved_classes[1:], start=2):
        # The second leg. 7.0.6's transfer overload resolves a seat-attribute
        # code per leg from each selected row's own hSeatAttCd, with the
        # wheelchair/seat-type fallback, and hands leg 1's to txtSeatAttCd4 and
        # leg 2's to txtSeatAttCd4_1 (trailingTxtSeatAttCd4):
        # ui/screen/train/TrainScheduleViewModel.java:2982-3001 computes the
        # two, :3004 passes both. The old citation C5/a.java:88-97 is 6.5.0
        # jetsam.
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
    # The seat keys go after the journey keys because that is where
    # TicketReservationIn declares them: txtSrcarCnt (18) / txtSrcarCnt1 (19),
    # then passengerInfoList, jrnyList, srcarList (22) and trailingSrcarList
    # (network/model/TicketReservationIn.java:80, :139-179). There is no
    # "last @FieldMap" in 7.0.6: certification.TicketReservation takes exactly
    # one @FieldMap (network/NetworkApi.java:752-753) built by flattening the
    # whole DTO (network/NetworkService.java:14155-14162).
    #
    # For "1101"/"1102" nothing at all is contributed: the ordinary journey
    # builder leaves both slots unset, so srcarList defaults to an empty list
    # and txtSrcarCnt to null (TicketReservationIn.java:182, called from
    # TrainScheduleViewModel.java:2932 and :3004). A null scalar is simply not
    # emitted, which is why a txtSrcarCnt of "0" never appears on the wire.
    #
    # Per leg the order below -- the count, then (car, seat) per index -- is
    # likewise the DTO's, since txtSrcarCnt precedes srcarList. Unlike 6.5.0
    # this IS deterministic: 7.0.6 builds an immutable List<
    # TicketReservationInSrcar> in selection order (TrainSeatMapViewModel.java
    # :2099-2113) and the flattener walks it with a 1-based index
    # (NetworkService.java:15350, :15366). So the old sentence that "the app
    # itself cannot guarantee it, KORAIL demonstrably tolerates any OSrcar
    # ordering" no longer describes the app -- emitting the count first and
    # then the pairs is what 7.0.6 does, not merely what KORAIL tolerates.
    # Across legs the order is leg 1's block then leg 2's, because srcarList
    # precedes trailingSrcarList in the DTO.
    #
    # Old citations dropped as 6.5.0 jetsam: CertificationService.java:52-54,
    # C5/a.java:118, SeatSearchActivity.java:676-682, C5/a.java:650/:144 and
    # C5/a.java:120-133 -- none of those classes exists in the 7.0.6 decompile.
    for journey, leg_assignments in enumerate(assignments, start=1):
        for index, assignment in enumerate(leg_assignments, start=1):
            if index == 1:
                # The count is the SEAT count: 7.0.6 makes one
                # TicketReservationInSrcar per selected seat
                # (TrainSeatMapViewModel.java:2108-2113) and writes that
                # list's size into txtSrcarCnt (:2136-2138, installed by the
                # copy() at :2289). The key is chosen by the JOURNEY index, not
                # the seat index, because there are only two count keys in the
                # DTO -- txtSrcarCnt and txtSrcarCnt1
                # (TicketReservationIn.java:80). Old citations
                # SeatSearchActivity.java:676 and OSrcar.java:21-23 are 6.5.0
                # jetsam.
                form[_srcar_count_key(journey)] = str(len(leg_assignments))
            form[_srcar_no_key(journey, index)] = str(assignment.car_no)
            form[_seat_no_key(journey, index)] = assignment.seat_no
    return form


def _sequence_no(code: str) -> str:
    """여정 일련번호를 세 자리로 채웁니다.

    **7.0.6 에는 이 포맷팅이 없습니다.** 이전 판은 ``S4/O.java:19-21`` →
    ``S4/N.java:32-38`` 의 ``DecimalFormat("000").format(n)`` 을 근거로 들었지만
    두 클래스 모두 6.5.0 잔재이며 7.0.6 디컴파일에 없습니다. 7.0.6 은
    ``txtJrnySqno`` 를 계산하지 않고 고정 상수 두 개를 그대로 실어 보냅니다 —
    ``TrainScheduleOutTrainInfo.toTicketReservationInput(…)`` 이 받은
    ``jrnySqno`` 인자를 손대지 않고 DTO 에 넣고
    (``network/model/TrainScheduleOutTrainInfo.java:3683``), 1구간은 ``$default``
    가 채우는 리터럴(``:1631``), 2구간은 호출부가 넘기는 다른 리터럴
    (``ui/screen/train/TrainScheduleViewModel.java:2968``)입니다. 둘 다
    AlienGuard 로 보호되어 값을 읽을 수 없고, 암호문이 3바이트라 세 자리와
    일관됩니다. ``"001"``/``"002"`` 는 이 패키지의 라이브 확인값이고, 여기서
    0 을 채우는 것은 그 두 값을 재현하기 위한 것입니다 — 앱의 알고리즘을 따라
    한 것이 아닙니다.
    """
    return f"{int(code):03d}"


def _write_journey_rows(
    form: dict[str, str],
    journeys: Sequence[dict[str, str]],
    journey_type_codes: Sequence[str],
) -> None:
    """여정 1..N 의 OJrny 행을 폼에 씁니다.

    Key order is TicketReservationInJrny's own declaration order, which the
    serializer and the form flattener both follow:
    network/model/TicketReservationInJrny.java:69 lists txtJrnyTpCd,
    txtJrnySqno, txtTrnNo, txtTrnClsfCd, txtTrnGpCd, txtRunDt, txtDptDt,
    txtDptTm, txtDptRsStnCd, txtDptStnConsOrdr, txtDptStnRunOrdr,
    txtArvRsStnCd, txtArvStnConsOrdr, txtArvStnRunOrdr, txtChgFlg,
    txtPsrmClCd -- and TrainScheduleOutTrainInfo.toTicketReservationInput()
    fills them in exactly that order
    (network/model/TrainScheduleOutTrainInfo.java:3683). There is no arvTm_
    key. The 1-based journey suffix is appended by the flattener, not by the
    DTO (network/NetworkService.java:15350, :15366).

    Two differences from what this helper emits, both deliberate and both
    harmless on the wire: txtPsrmClCd{i} is written by the caller's seat block
    rather than here, and txtChgFlg is pinned "N" where 7.0.6 uses a protected
    1-char literal (TrainScheduleOutTrainInfo.java:3683) whose ciphertext
    length is consistent with "N".

    옛 인용 ``OJrny.java:6-27`` 과 ``C5/a.java:54-76`` 은 7.0.6 에 없는 6.5.0
    클래스입니다. 다만 그때 함께 적었던 "이 경로에는 LinkedHashMap 이 없다" 는
    틀렸습니다 -- 평탄화기 ``NetworkService.STLibw`` 가 ``:15306`` 에서
    ``LinkedHashMap`` 을 만듭니다. 순서가 삽입에 좌우되지 않는 이유는 맵이
    없어서가 아니라 DTO 를 먼저 직렬화하기 때문입니다.
    ``txtJrnyCnt`` 자체는 이 헬퍼가 돌기 전에 각 호출부가 씁니다.
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
        # 예약대기 is offered on the 일반실 tab only, and in 7.0.6 that is
        # structural rather than a UI rule: the row DTO's
        # specialReservationStatus() cannot return WAIT at all -- its only
        # returns are COMBINATION, SUSPENDED, NONE, LACK, DISCOUNT_SOLD_OUT,
        # DISCOUNT_LACK, SOLD_OUT and AVAILABLE
        # (network/model/TrainScheduleOutTrainInfo.java:3587-3625), while
        # generalReservationStatus() does return WAIT (:2839-2850). So there is
        # no 특실 standby to ask for. The old citations
        # smali/U4/a.smali:1969-1981 and a5/u.java:371 are 6.5.0 jetsam -- no
        # U4 smali and no a5 package exist in the 7.0.6 decompile.
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
        # reasoning from a5/u.java:346-360 (6.5.0 jetsam; no a5 package exists
        # in the 7.0.6 decompile) that the app disables the booking
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
    # not always the general one. 7.0.6: TrainScheduleOutTrainInfo's own
    # generalReservationStatus()/specialReservationStatus() (java:2810, :3587)
    # read h_gen_rsv_cd and h_spe_rsv_cd respectively, and
    # TrainScheduleViewModel.getTrainPsrmTypeInitValue() (java:3457-3458)
    # picks between them by which cabin's status is actually enabled (a5/u.java
    # is 6.5.0 jetsam -- that package does not exist in the 7.0.6 decompile).
    # Keep this package's stricter rule -- only
    # an explicit "11" counts as available -- and apply it to whichever cabin is
    # being booked. On a transfer it is applied to every leg, because a booking
    # whose second leg is sold out is not bookable either.
    #
    # 7.0.6 자유석 분기도 이 규칙이 막습니다. 단일 열차 빌더는 일반실이면서
    # generalReservationStatus() 가 FREE 인 열차에서 hidFreeFlg 와 txtSeatAttCd4 를
    # AlienGuard 로 보호된 값으로 바꾸고, 이 패키지는 그 값을 재현할 수 없습니다. FREE 는
    # h_gen_rsv_cd 가 SOLD_OUT 코드일 때만 나옵니다. 그 코드도
    # 보호되어 있지만 7.0.6 이전 앱의 평문 리터럴과 2026-07-26 라이브 매진 행은 "13" 이고,
    # 이 규칙은 "11" 만 통과시키므로 자유석 열차는 I/O 전에 거절됩니다. 보호된 값을
    # 추측해 홀드를 거는 것보다 거절하는 편이 안전합니다. 환승 빌더는 hidFreeFlg 를
    # 고정값으로 보내므로 이 분기가 없습니다.
    #   analysis/jadx/sources/com/korail/talk/ui/screen/train/TrainScheduleViewModel.java:2875
    #     (:2899-2909 hidFreeFlg, :2914-2915 txtSeatAttCd4, :3004 환승)
    #   analysis/jadx/sources/com/korail/talk/network/model/TrainScheduleOutTrainInfo.java:2881-2889
    #   analysis/jadx/sources/com/korail/talk/common/define/TrainReservationCode.java:21,24
    #   analysis/jadx/sources/com/korail/talk/common/define/SeatType.java:299,307
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
    """구간 하나가 싣는 7.0.6 TicketReservationInJrny 값들을 검사합니다.

    직통·환승 구간(:class:`TrainSummary`)과 병합 여정(:class:`TrainScheduleItem`)이
    같은 열두 값을 씁니다. 7.0.6 기준 전선 이름과 타입은
    ``TicketReservationInJrny.java:69`` 의 ``@SerialName`` 목록이며
    (``txtTrnNo``·``txtTrnClsfCd``·``txtTrnGpCd``·``txtRunDt``·``txtDptDt``·
    ``txtDptTm``·``txtDptRsStnCd``·``txtDptStnConsOrdr``·``txtDptStnRunOrdr``·
    ``txtArvRsStnCd``·``txtArvStnConsOrdr``·``txtArvStnRunOrdr``), 열둘 다
    ``String`` 입니다 — 숫자 제약은 어디에도 없습니다.
    """
    return {
        "train_no": _required_digits(train.train_no, field="train_no"),
        "train_group_code": _required_digits(
            train.train_group_code,
            field="train_group_code",
        ),
        # Not _required_digits: KTX-산천 legs live-confirmed sending
        # alphanumeric class codes (e.g. "0A") for h_trn_clsf_cd, which a
        # decimal-only check rejected outright -- booking became impossible
        # for any itinerary containing such a leg. The real app never treats
        # this as a number (TrainSummary.train_class_code is str everywhere
        # else in this library too); echo it as given.
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
    """여정 전체의 ``txtStndFlg``.

    "한 구간이라도 입석이면 Y"입니다. 7.0.6 은 이것을 구간별 술어 둘의 **OR**
    로 씁니다 — ``z``(1구간)와 ``z2``(2구간)를 각각 구해 ``z3 = z || z2`` 를
    ``txtStndFlg`` 자리에 넣습니다
    (``ui/screen/train/TrainScheduleViewModel.java:2961-2967``, 사용은
    ``:3004``). 여기 구현("1구간은 조건 없이 대입, 이후 구간은 값이 아직 ``"N"``
    일 때만 다시 계산")은 그 OR 과 결과가 동치이고 구간이 최대 둘이므로 차이가
    나지 않습니다. 이전 판이 근거로 적은 ``C5/a.java:78-82`` 는 6.5.0 잔재이며,
    "1구간 대입 후 N 일 때만 덮어쓴다"는 서술 자체가 7.0.6 의 모양이 아닙니다.
    """
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
    """구간 하나의 ``txtStndFlg``.

    일반실이고, 일반 좌석이 매진(``"13"``)이며, 입석 재고가 열려 있을 때
    (``"11"``) 참입니다. 7.0.6 에서 이것은 조회 행 DTO 의
    ``generalReservationStatus()`` 가 ``STAND`` 를 돌려주는 조건과 같습니다 —
    ``h_gen_rsv_cd`` 가 ``TrainReservationCode.SOLD_OUT`` 이고 ``h_stnd_rsv_cd``
    가 ``TrainReservationCode.AVAILABLE`` 일 때
    (``network/model/TrainScheduleOutTrainInfo.java:2881-2889``, 코드 정의는
    ``common/define/TrainReservationCode.java:24``·``:21``). 두 ``rsvCd`` 는
    AlienGuard 로 보호된 2바이트 리터럴이라 ``"13"``/``"11"`` 은 이 패키지의
    라이브 확인값입니다.

    이 값을 예약 요청에 넣는 호출자는
    ``ui/screen/train/TrainScheduleViewModel.java:2870-2874``(직통) 와
    ``:2961-2967``(환승) 이며, 두 곳 모두 ``psrmType == PsrmType.GENERAL`` 을
    함께 요구합니다 — 그래서 일반실 조건이 여기에도 남습니다. 옛 인용
    ``S4/J.java:83-84``(``isStndSeat``)·``c5/b.java:69`` 은 6.5.0 잔재입니다.
    """
    if (
        seat_class is KorailSeatClass.GENERAL
        and train.general_reservation_code == "13"
        and train.standing_reservation_code == "11"
    ):
        return "Y"
    return "N"


# 7.0.6 holds the number as a three-part Triple<String, String, String> (the
# `phoneNo` property of ReservationWaitApplyUiData,
# ui/screen/train/ReservationWaitApplyUiData.java:85), concatenates the three
# parts into one string (ui/screen/train/ReservationWaitViewModel.java:503-512,
# a StringBuilder over phoneNo's first/second/third), and refuses to send
# unless that concatenation is exactly 11 long -- the gate at :513 is
# `checkedSMS && length != 11`, and it alerts R.string.error_cellphone
# ("휴대폰 번호를 정확히 입력해주세요.", res/values/strings.xml:834) instead of
# building the request. Note it is conditional on the SMS checkbox, which is
# why build_standby_wait_form below only validates when sms_notify is set.
#
# The old citation -- "capped at 3 + 4 + 4 digits (res/values/integers.xml
# :34-35, phone_number_max_length_3 and phone_number_max_length, applied in
# ReservationWaitActivity.java:88-89)" -- is wrong twice over for 7.0.6. There
# is no ReservationWaitActivity class, and 7.0.6's integers.xml contains no
# phone_number_max_length* entry at all: its whole <resources> block is eleven
# unrelated integers (abc_config_activityDefaultDur through
# status_bar_notification_info_maxnum). The 3 + 4 + 4 split survives only as
# the arity of the Triple; the per-part caps are not in the resources any more.
# This pattern is also slightly STRICTER than 7.0.6, which tests length alone
# and would accept eleven non-digits -- deliberately, since a non-numeric
# txtCpNo cannot be a Korean mobile number and the server would reject it.
_STANDBY_PHONE_RE = re.compile(r"[0-9]{11}")


def _successful_hold_pnr(hold: ReservationHoldResponse, *, context: str) -> str:
    """홀드가 성공(``SUCC``)이고 PNR 을 가졌는지 확인하고 그 PNR 을 돌려줍니다.

    build_standby_wait_form, build_unpaid_reservation_cancel_form,
    build_card_payment_form 셋이 거의 같은 모양으로 따로 반복하던 검사를 하나로
    모았습니다. 실패 메시지는 호출자마다 다르므로 ``context`` 로 받습니다.
    """
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
    """예약대기 홀드의 후속 폼을 만듭니다.

    ``reservationWait.ReservationWait`` 이며 예약대기 예매의 후반부입니다.
    ``"1102"`` 홀드가 PNR 을 만들고, 이 호출이 예약대기 화면에서 받은 두 옵션을
    그 PNR 에 기록합니다. 7.0.6 의 라우트 선언은
    ``@POST("/classes/com.korail.mobile.reservationWait.ReservationWait")``
    ``postReservationWait(@FieldMap Map<String,String>, …)``
    (``network/NetworkApi.java:639-640``) 하나뿐이고, 옛 인용
    ``ReservationWaitService.java:10-12`` 은 6.5.0 잔재입니다 — 그 클래스는
    7.0.6 디컴파일에 없습니다.

    전선 키 넷은 ``ReservationWaitIn`` 의 ``@SerialName`` 그대로입니다
    (``network/model/ReservationWaitIn.java:55``, 개별 선언은 ``:111``·``:115``·
    ``:119``·``:107``). 값을 채우는 곳은 ``ReservationWaitViewModel`` 의
    ``reservationWait$1`` 하나입니다
    (``ui/screen/train/ReservationWaitViewModel.java:517-525``).

    * ``txtPnrNo`` — 홀드의 PNR. 7.0.6 은 직전 예약 응답 객체에서
      ``reservationOut.getHPnrNo()`` 를 읽어 그대로 넣습니다(``:519``, 생성은
      ``:525``). 옛 인용 ``ReservationWaitActivity.java:150`` 은 6.5.0 잔재.
    * ``txtPsrmClChgFlg`` — 좌석등급 변경 동의. ``checkedSpecial`` 삼항으로
      보호된 1바이트 리터럴 둘 중 하나를 고릅니다(``:520``). 암호문 길이가
      ``"Y"``/``"N"`` 과 일관되고 그 두 값은 이 패키지의 라이브 확인값입니다 —
      AlienGuard 로 보호되어 정적으로는 읽을 수 없습니다. 관광열차에서 이
      체크박스가 사라지는 것도 7.0.6 에 그대로 있습니다: 생성자가 1구간의
      ``txtTrnGpCd`` 로 ``TrainGroup.findBy(...)`` 를 돌려
      ``isTourGroup``(``common/define/TrainGroup.java:460-461``)이면
      ``applyUiData`` 를 ``copy$default(…, 62, null)`` 로 덮어 첫 인자
      ``showSpecial`` 만 ``false`` 로 내립니다
      (``ReservationWaitViewModel.java:565-572``; 인자 순서는
      ``ReservationWaitApplyUiData.java:85``). 그러면 ``checkedSpecial`` 은 켤
      수 없으니 거기서는 ``"N"`` 뿐입니다.
    * ``txtSmsSndFlg`` — 배정 시 SMS 알림. 같은 모양의 ``checkedSMS`` 삼항
      (``:521``)입니다.
    * ``txtCpNo`` — 알림받을 번호. 앱은 SMS 가 켜졌을 때만 싣습니다:
      ``if (!checkedSMS) str3 = null;``(``:522-524``)로 널을 넘기고, 앱의
      Json 이 ``explicitNulls`` 를 끈 것으로 보여 널 필드는 직렬화에서
      빠집니다 — ``setExplicitNulls`` 호출은 ``NetworkModule.java:861``
      입니다(``:860`` 은 ``setCoerceInputValues`` 이고, 예전에 여기 적혀
      있던 줄번호가 그것이었습니다). **단정이 아니라 추론입니다**: 인자가
      ``Integer.parseInt(AlienGuard…)`` 로 보호돼 실제 값은 읽을 수 없고,
      비교 연산자가 ``> 1`` 이라는 것만 평문입니다. 그래서 빈 문자열이 아니라 **키 생략**이
      맞고, 이 빌더도 그렇게 합니다. DTO 자신도 ``txtCpNo`` 만 기본값을 널로
      두고 나머지 셋은 빈 문자열로 둡니다(``ReservationWaitIn.java:87``).
      옛 인용 ``:213``/``:219``/``:115``/``:214``/``:218``/``:220-227`` 은 모두
      ``ReservationWaitActivity.java`` 의 줄번호이므로 함께 폐기했습니다.
    """
    pnr_no = _successful_hold_pnr(
        hold,
        context="KORAIL standby options require one successful hold with a PNR",
    )
    # Not coerced with bool(): every other flag on the wire is "Y"/"N", and a
    # caller who passes the string "N" expecting it to read as false would
    # otherwise get bool("N") is True -- "Y" on the wire, the opposite of what
    # was asked, on a flag that decides whether a standby hold may be filled
    # at a different seat class.
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
    elif phone_no is not None:
        raise KorailProtocolError(
            "KORAIL standby sends no phone number unless sms_notify is True"
        )
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
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
    """미결제 홀드를 취소하는 폼을 만듭니다.

    여정 수는 상수가 아니라 **되울려 보냅니다.** 7.0.6 에서 이것은 예외 없는
    규칙입니다 — ``new ReservationCancelIn(txtPnrNo, txtJrnySqno, txtJrnyCnt,
    hidRsvChgNo)``(인자 순서는 ``network/model/ReservationCancelIn.java:74``,
    전선 키는 ``:53``·``:106``·``:110``·``:114``·``:118``)를 만드는 7.0.6 의
    호출부 **아홉 곳 전부**가 세 번째 인자로 ``reservationOut.getHJrnyCnt()``
    를 넘깁니다. 여정 수를 상수로 박는 곳은 한 곳도 없습니다. 환승 홀드는
    여정이 둘이므로 여기서 하나만 받아들이면 살아 있는 환승 예약을 놓을 방법이
    없어집니다.

    옛 인용 ``DReservationConfirmActivity.java:269-278`` 은 6.5.0 잔재입니다 —
    그 클래스는 7.0.6 디컴파일에 없고, 7.0.6 에는
    ``executeRsvCancel(ReservationResponse)`` 도 ``setTxtJrnyCnt`` 세터도
    없습니다(요청은 불변 DTO 하나입니다). 그 주장의 내용 자체는 7.0.6 에서도
    그대로 성립하고, 아래 두 주석에 재도출한 근거를 적어 뒀습니다.
    """
    if not isinstance(response, ReservationHoldResponse):
        raise KorailProtocolError(
            "KORAIL cancellation requires an exact reservation hold response"
        )
    # A live TicketReservation returns the journey count zero-padded
    # (h_jrny_cnt="0001"), not "1", so compare numerically rather than by
    # spelling -- a formatting difference must never make a hold uncancellable.
    #
    # The count is ECHOED, not fixed at one. In 7.0.6 that is settled by
    # enumeration rather than by one call site: grepping for
    # `new ReservationCancelIn(` over the whole decompile finds nine call
    # sites, and every one of them passes reservationOut.getHJrnyCnt() as the
    # third (txtJrnyCnt) argument --
    #   ui/screen/train/ReservationWaitViewModel.java:398
    #   ui/screen/train/ReservationMergeViewModel.java:445
    #   ui/screen/transit/AirportBusSeatMapViewModel.java:542
    #   ui/screen/pay/PayViewModel.java:4686, :4725, :4805, :4847
    #   ui/screen/basketticket/BasketTicketViewModel.java:3232
    #   ui/screen/myticket/reservation/MyReservationViewModel.java:1557
    # (plus a retry path, BasketTicketViewModel.java:627, that replays a saved
    # input verbatim, and ui/screen/sample/Sample09ViewModel.java:197, which is
    # a sample screen). The same enumeration shows the two constants: those
    # sites that do NOT read a listed row pass an AlienGuard-protected 4-byte
    # ciphertext for txtJrnySqno (ReservationWaitViewModel.java:393,
    # ReservationMergeViewModel.java:445,
    # AirportBusSeatMapViewModel.java:531) and a 3-byte one for hidRsvChgNo
    # (:398, :445, :542) -- lengths consistent with "0001" and "000", which are
    # this package's live-verified readings, not decoded constants.
    #
    # A 환승 hold carries two journeys, and refusing it here would leave a live
    # transfer reservation with no way to release it -- the orphaned hold this
    # whole subsystem exists to prevent.
    #
    # The old citation DReservationConfirmActivity.java:269-278 is 6.5.0
    # jetsam: no such class in 7.0.6, and nothing on this path has a
    # setTxtJrnyCnt setter at all.
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
    form = _common_fields(config)
    form.update(
        {
            "txtPnrNo": pnr_no,
            "txtJrnySqno": "0001",
            "txtJrnyCnt": journey_count,
            # A literal "000" here, NOT the hold's h_rsv_chg_no -- deliberately
            # unlike build_card_payment_form below.
            #
            # **이것은 "앱은 언제나 고정 상수를 보낸다"는 뜻이 아닙니다.** 예전
            # 판이 여기 그런 전칭 주장을 적어 두었는데 틀렸습니다. 7.0.6 에서
            # ``hidRsvChgNo`` 를 **응답에서 꺼내 넘기는** 화면이 확인된 것만
            # 둘입니다:
            #
            #   * 예약목록 화면 -- ``MyReservationViewModel.java:1566`` 이
            #     ``new ReservationCancelChkIn(hPnrNo, …getHJrnySqno(),
            #     …getHJrnyCnt(), …getHRsvChgNo())`` 로 응답 여정 객체의 값을
            #     네 자리 모두에 그대로 넘깁니다(취소 전 단계인
            #     ``requestReservationCancel`` 쪽도 같은 모양, ``:1557``).
            #   * 결제 화면 -- ``PayViewModel.java:4678-4686`` 과 ``:4717-4725``
            #     (같은 모양이 ``:4798``/``:4805``, ``:4840``/``:4847`` 에 두 번
            #     더 있습니다)가 ``ReservationCancelIn`` 을 만들면서 여정 목록이
            #     비었거나 꺼낸 값이 비면 AlienGuard 로 보호된 3바이트 리터럴을
            #     쓰고, 그렇지 않으면 ``jrnyInfo[0].getHRsvChgNo()`` 를 씁니다 --
            #     즉 **조건부 치환**이지 고정 상수가 아닙니다. 그렇게 만든
            #     ``ReservationCancelIn`` 이 ``:15305`` 에서 그대로
            #     ``ReservationCancelChkIn`` 으로 옮겨져 이 라우트로 나갑니다.
            #
            # 앱이 그 조건부 분기에서 쓰는 **대체 리터럴의 평문**은 읽을 수
            # 없습니다 -- AlienGuard 호출의 3바이트 암호문
            # (``new byte[]{-110, -122, -15}``, ``PayViewModel.java:4679``·
            # ``:4683``·``:4718``·``:4722``)이라 길이가 ``"000"`` 과 맞는다는
            # 것까지만 말할 수 있습니다. 아래 ``"000"`` 은 이 패키지의 라이브
            # 확인값이지 그 암호문을 복호한 결과가 아닙니다.
            #
            # 예전 인용 ``DReservationConfirmActivity.java:270-279``
            # (``executeRsvCancel(ReservationResponse)``,
            # ``setReservationResponse``)은 **철회합니다** -- 6.5.0 클래스이고
            # 7.0.6 디컴파일에 그 이름의 파일이 없습니다. 7.0.6 에서
            # ``requestReservationCancelChk`` 를 부르는 곳은 일곱 개
            # (PayViewModel, ReservationWaitViewModel, ReservationMergeViewModel,
            # MyReservationViewModel, BasketTicketViewModel,
            # AirportBusSeatMapViewModel, Sample09ViewModel)이고, 위 둘 말고
            # 나머지 다섯이 무엇을 넣는지는 확인하지 않았습니다.
            #
            # 요청 DTO ``ReservationCancelChkIn`` 의 **선언 필드**는 여덟 개이지
            # 일곱 개가 아닙니다 -- ``ReservationCancelChkIn.java:53`` 의 직렬화
            # 생성자가 ``@SerialName("Device")``/``("Version")``/``("Key")``/
            # ``(Constants.LANG)`` 넷(``CommonIn`` 상속, ``CommonIn.java:40,381``)
            # 에 더해 ``txtPnrNo``/``txtJrnySqno``/``txtJrnyCnt``/``hidRsvChgNo``
            # 넷(같은 파일 ``:29-32``)을 받습니다. 한때 여기 "정확히 일곱"이라고
            # 적었던 것은 ``lang`` 을 빠뜨린 오류입니다.
            #
            # **선언 필드 수와 실제로 전송되는 키 수는 다른 주장입니다.**
            # kotlinx 가 원소를 건너뛸 수 있어
            # (``ReservationCancelChkIn.java:120-150`` 의 ``write$Self``)
            # 한 요청이 여덟 키를 다 싣는다는 보장은 없습니다. 다만 ``lang``
            # 의 생략은 **값 비교 하나가 아닙니다** -- ``CommonIn.java:467`` 이
            # 먼저 ``output.shouldEncodeElementDefault(serialDesc, 3)`` 를 묻고,
            # 그것이 false 인 **경우에만** ``self.lang`` 을
            # ``languageProvider?.getSTLeec()`` 와 비교해 같을 때 return 합니다
            # (``:470-471``). 어느 한쪽이라도 어긋나면 ``:474`` 가 ``lang`` 을
            # 씁니다. 즉 기준값은 정적 기본값이 아니라 **런타임 언어 제공자**의
            # 값이고, 인코더가 기본값 기록을 요구하면 값이 같아도 실립니다.
            # 이 빌더가 내보내는 키 수도 고정이 아닙니다 -- ``_common_fields``
            # 가 ``config.lang`` 이 ``None`` 이 아닐 때만 ``lang`` 을 붙이므로
            # 기본값에서는 일곱 키, ``lang`` 을 주면 여덟 키입니다.
            #
            # 이 빌더가 ``"000"`` 을 쓰는 근거는 그래서 앱 재현이 아니라 라이브
            # **관찰**입니다: 2026-09-22 에 reserve/reserve_transfer/
            # reserve_merge/recalculate_price 응답에서 모은 여정 행 45 개 중
            # ``h_rsv_chg_no`` 키를 가진 행이 0 개였고, ``"000"`` 으로 보낸
            # 취소가 그 표본 안에서 모두 ``IRG000000`` 으로 성립했습니다.
            # **45 개는 유한 표본이지 보장이 아닙니다** -- 그날의 우리 기록일
            # 뿐이고 재측정된 적이 없습니다. 홀드 응답이 변경번호를 주는
            # 경우에는 그것을 넘기는 편이 앱에 더 가깝습니다. This builder is the
            # fresh-single-journey-hold case: the hold it is handed has no
            # change number to echo, so it sends the constant. That is a
            # statement about THIS builder, not about every cancel form.
            "hidRsvChgNo": "000",
        }
    )
    return form


# What this builder sends when the hold response withheld the sequence.
#
# 예전 근거였던 "앱이 null 을 넘기면 Retrofit 이 ``@Field`` 를 통째로
# 생략한다"는 **이 라우트에는 적용되지 않습니다.** 7.0.6 의 결제 오버로드는
# 둘 다 ``@FieldMap`` 입니다 -- ``NetworkApi.java:630-632``
# (``postReservationPayment(@FieldMap Map<String, String>, …)``)와
# ``:646-648`` (``postRsvPayment(@FieldMap …, @FieldMap …, …)``). null 을
# 조용히 생략하는 규칙은 ``ParameterHandler.java:252-259`` 의 ``Field.apply``
# 뿐이고(``t == null`` 이면 그냥 ``return``), ``FieldMap.apply``
# (``:276-293``)는 정반대로 **던집니다** -- 값이 null 이면 ``:286-287`` 의
# ``Utils.parameterError(…, "Field map contained null value for key '…'")``.
# 게다가 맵 타입이 ``Map<String, String>`` 이라 null 이 들어갈 자리도
# 아닙니다.
#
# 즉 **앱이 이 키를 비워 보내는 모양은 재도출되지 않았습니다** -- 상류에서
# 키를 아예 빼는지, 빈 문자열을 넣는지 확인하지 못했습니다. 아래 값은 그래서
# 앱 재현이 아니라 이 라이브러리의 선택입니다: "000000" 은 이 빌더가 늘 보내
# 온 값이고 srtgo 가 박는 값이며, 관측된 홀드는 모두 시퀀스를 채워
# 돌려줬습니다(2026-07 라이브 2건). 값 자체가 맞는지는 별개 문제입니다.
_ABSENT_JOB_SEQUENCE = "000000"


def _echoed_job_sequence(value: str | None) -> str:
    """홀드의 ``tmpJobSqno`` 를 결제 폼에 그대로 되울립니다.

    **자릿수를 복원하지 않습니다.** 숫자로 도착한 ``tmpJobSqno`` 는 앞의 0 이
    사라진 채 전선에 오릅니다.

    다만 **그 근거는 아직 없습니다.** 예전 인용 ``TCReservationDao.java``
    (6.5.0)를 7.0.6 의 ``TripChgPrsCIn.java:47`` 로 바꿔 적었던 것은 잘못된
    교체였습니다 — 그쪽은 **여정변경** 입력의 단일 ``tmpJobSqno`` 이고,
    여기서 문제 삼는 것은 **결제 홀드 응답**의 ``hidTmpJobSqno1``/``2`` 라서
    같은 필드가 아닙니다. 결제 쪽 두 필드가 어떻게 만들어지는지는 재유도하지
    못했습니다 — **미출처**입니다.

    0 을 채우지 않는 현재 동작 자체는 라이브로 문제가 없었습니다.
    """
    if isinstance(value, str) and value.strip():
        return value
    return _ABSENT_JOB_SEQUENCE


# What the payment form sends for hidRsvChgNo when the hold response carried no
# usable first-journey h_rsv_chg_no -- which, on this library's reserve routes,
# is EVERY time.
#
# This comment used to call the literal "the explicit last resort" and claim
# that "no observed hold has produced one". Both were wrong, and backwards: the
# absent key is not the edge case, it is the only shape certification.Ticket-
# Reservation has ever answered with. As of 2026-09-22, h_rsv_chg_no was missing
# from 45 of 45 live journey rows returned by reserve / reserve_transfer /
# reserve_merge -- direct 일반실 and 특실, 무궁화호, 새마을호, ITX-마음,
# 어른2+어린이1, 경로, overnight, four 예약대기 holds, both transfer legs, both
# merge-standing legs and both merge legs. So
# ReservationJourney.reservation_change_no is always None off a fresh hold and
# _echoed_reservation_change_no below always returns this literal. Do not
# "restore" a fallback-flavoured reading of this path: the echo branch is there
# because the app echoes, not because any observed hold has filled the key.
#
# What makes the literal safe is not habit but corroboration: reading the same
# PNRs back through certification.ReservationList returns h_rsv_chg_no="000" on
# 8 of 8 journey rows (direct, 예약대기 x4, merge x2, transfer x2). "000" is the
# server's OWN value for a fresh hold, so emitting it is an echo by another
# route, not a guess. srtgo sends the same literal.
#
# **다만 "앱은 모든 신선홀드 취소에서 이 상수를 박는다"는 뜻은 아닙니다.**
# 한때 여기 그렇게 적었는데 틀렸습니다 -- ``PayViewModel.java:4678-4686`` 과
# ``:4717-4725`` 는 여정 목록이 비었거나 꺼낸 값이 비었을 때에만 AlienGuard
# 3바이트 리터럴을 쓰고, 그렇지 않으면 ``jrnyInfo[0].getHRsvChgNo()`` 를
# 그대로 넣습니다. 즉 앱의 취소 폼은 고정 상수가 아니라 **조건부 치환**이고,
# 위 문장은 변경번호가 비어 오는 홀드에 한정된 관찰입니다.
#
# Also dropped here: the old sentence that "a null h_rsv_chg_no would be
# forwarded and then dropped by Retrofit". That is a 6.5.0 story and it cannot
# happen in 7.0.6 -- ReservationOutJrnyInfo.java:48 declares hRsvChgNo as a
# NON-nullable String and :138 gives it an AlienGuard-decrypted `new byte[0]`
# default (i.e. "") whenever the seen1 bit 131072 is clear, so the app would
# place "" there, never null. The receiving field is equally non-null with the
# same "" default: RsvPaymentIn.java:28,75. The old citation V4/b.java:41 is
# unverifiable in this repo (analysis/jadx/sources has no V4 package at all);
# the 7.0.6 site that actually does this is
# analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6684,
# which sets hidRsvChgNo from the FIRST element of
# reservationOut.getJrnyInfos().getJrnyInfo().
_ABSENT_RESERVATION_CHANGE_NO = "000"


def _echoed_reservation_change_no(hold: ReservationHoldResponse) -> str:
    # The FIRST journey specifically, mirroring 7.0.6's
    # setHidRsvChgNo(<first>(reservationOut.getJrnyInfos().getJrnyInfo())
    # .getHRsvChgNo()) at PayViewModel.java:6684.
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
    """미결제 홀드에 대한 단일 카드 ReservationPayment 폼을 만듭니다.

    ``hidTmpJobSqno1/2`` 와 ``hidRsvChgNo`` 는 상수가 아니라 홀드 응답을 되울린
    것입니다(``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6684``,
    라우트 선언은 ``NetworkApi.java:631`` 의 ``postReservationPayment``
    (``@FieldMap``, 응답 ``ReservationPaymentOut``)이고 ``:647`` 에 같은 경로의
    오버로드가 하나 더 있습니다 — 예전 인용 ``PaymentService.java:14`` 는 7.0.6
    에 없는 클래스입니다). ``hidRsvChgNo`` 는 **첫** 여정의 변경번호이며
    앱도 모든 결제 호출 지점에서 같은 식을 반복합니다. 구조상 프로토콜 상수가
    아니라 예약별 상태입니다.

    다만 **관찰된 범위에서는** ``reserve``/``reserve_transfer``/
    ``reserve_merge`` 가 ``h_rsv_chg_no`` 를 보낸 적이 없어(2026-09-22,
    여정 행 45 개 중 0 개) 그 표본에서 이 빌더가 내보낸 값은 모두
    ``_ABSENT_RESERVATION_CHANGE_NO``(``"000"``)였습니다. 45 개는 유한
    표본이라 "언제나" 를 세우지 못하며, 재측정된 적도 없습니다 -- 바로 위
    문단대로 이 필드는 프로토콜 상수가 아니라 예약별 상태이므로, 홀드 응답이
    변경번호를 실어 주면 ``_echoed_reservation_change_no`` 가 그것을
    내보냅니다.
    그 리터럴이 왜 안전한지는 그 상수의 주석에 적어 뒀습니다 — 요약하면 같은
    PNR 을 ``certification.ReservationList`` 로 되읽으면 서버 자신이
    ``h_rsv_chg_no='000'`` 을 돌려줍니다(8/8 행). 이전 판은 이 자리를
    ``V4/b.java:39-41`` 로 인용했는데 그 패키지는 이 저장소의 7.0.6 디컴파일에
    존재하지 않아 확인이 불가능했습니다.

    ``hidMnsStlAmt1`` 은 화면의 합계가 아니라 앱이 계산한 **수령액**입니다.
    예전 인용 ``AbstractC1269e.java:406`` → ``V4/a.java:27`` 과
    ``PaymentActivity.java:174,497`` 은 **철회합니다** -- 셋 다 6.5.0 이름이고
    이 저장소의 7.0.6 디컴파일(``analysis/jadx/sources/``,
    ``analysis/apktool/smali*``)에 그 이름의 파일도, 클래스 참조도 없습니다.

    7.0.6 에서 재도출한 값 경로는 다음과 같습니다(모두 실재하는 줄입니다):
    ``PaymentMethodHelper.java:113`` 이 ``hidMnsStlAmt`` 를 넘겨받은 Bundle
    에서 꺼내 넣고, 그 Bundle 은 ``PayViewModel.java:15571,15573-15575`` 가
    ``getPgAmountForPayment()`` 값으로 채우며,
    ``getPgAmountForPayment()``(``:11050-11051``)는
    ``getPaymentSnapshot().getPgAmount()``,
    그 ``pgAmount``(인자 순서는 ``PaymentSnapshot.java:54`` 의 ``copy``
    시그니처 ``copy(total, pgAmount, pointAmount, cityPointAmount, pointType)``
    두 번째 자리, 접근자는 ``:97``)는
    ``capturePaymentSnapshot()``(``PayViewModel.java:5730-5756``)에서
    ``getOriginalReceivedAmount()`` 에서 포인트 사용액을 뺀 값입니다. 포인트를
    쓰지 않는 이 빌더의 경우 그 차감이 0 이라 ``getOriginalReceivedAmount()``
    자체입니다. (앱에는 ``getReceivedAmount()`` 도 실제로 있습니다 --
    ``PayViewModel.java:11058`` -- 다만 결제 금액 경로에 직접 들어가는 것은
    ``getOriginalReceivedAmount()``, ``:11027`` 입니다.)

    **이 체인은 7.0.6 에서 재도출됩니다.** ``getOriginalReceivedAmount()``
    (``PayViewModel.java:11027-11028``)가 읽는 ``PayAmountUiData`` 필드는
    ``STLfan`` 이고(``ui/screen/pay/data/PayAmountUiData.java:248-249``),
    ``STLfan`` 은 생성자의 **11번째** 인자입니다(같은 파일 ``:65``, ``str8``).
    ``PayViewModel.java:11440`` 의 ``new PayAmountUiData(...)`` 는 그 자리에
    ``NumberExKt.formatSeparator(j5)`` 를 넣고, 합성 생성자의 기본값 마스크가
    ``193``(= 비트 0·6·7)이라 11번째 인자는 **마스크에 덮이지 않습니다**.
    ``j5`` 는 일반 예약 분기에서 ``mReservationOutList`` 의
    ``getHTotRcvdAmt()`` 합이고(``:11303-11307`` → ``:11368``), 그 전선 키가
    ``@SerialName("h_tot_rcvd_amt")``(``ReservationOut.java:452``)입니다.
    여정변경 분기는 대신 ``getScnIndcAmt()`` 를 더하며(``:11297-11301``),
    장바구니·상품이 있으면 ``h_rcvd_amt`` 합(``:11390``)과 ``strMrkAmtSum``
    합(``:11405``)이 뒤에 더해집니다.

    **여러 분기가 하나의 생성 지점으로 모입니다.** 한때 여기 "``:11521`` 에서
    ``PayAmountUiData`` 를 한 번 더 만든다" 고 적었는데 틀렸습니다. jadx 가
    ``new PayAmountUiData(...)`` 식을 ``:11440`` 과 ``:11521`` 두 번 보여 주는
    것은 맞지만, ``initAmountData()``(선언 ``:11222``)에는 jadx 의 코드 중복
    경고가 열 줄 붙어 있습니다(``:11212-11221``,
    ``JADX WARN: Code duplicated, block: …``). 같은 메서드의 smali
    (``analysis/apktool/smali_classes5/.../PayViewModel.smali``, 범위
    ``:25740-27914``)에는 생성이 **하나**뿐입니다 -- ``new-instance``
    ``:27527``, ``<init>`` ``:27541``. (파일 전체에서 다른 ``new-instance`` 는
    ``:1116`` 하나이고, 그것은 자바 ``:5321`` 의 StateFlow 초기값입니다.)

    따라서 위 분기들 -- ``:11292-11293`` 트래블패스(``PayTicketItem`` 의
    ``h_rcvd_amt``), ``:11296-11301`` 여정변경(``getScnIndcAmt``),
    ``:11303-11307`` 일반 예약(``getHTotRcvdAmt``), ``:11384-11390``
    장바구니(``CartInfo.getH_rcvd_amt``), ``:11399-11405`` 상품 -- 은 서로
    다른 객체가 아니라 **같은 한 자리**로 들어가는 서로 다른 입력입니다.
    ``:11477-11478``/``:11486`` 은 ``:11293`` 과 같은 트래블패스 분기의 중복
    렌더링이지 별도 경로가 아닙니다. 위 유도는 그 한 자리에 **일반 예약
    분기**가 넣는 값에 한정된 주장입니다.

    ``h_tot_prc`` 가 **UI 전용**이라는 부분도 지금은 정황 증거뿐입니다:
    7.0.6 에서 ``getHTotPrc()`` 를 읽는 곳은 화면 합산·로깅 세 군데
    (``ui/screen/pay/complete/PayCompleteViewModel.java:513``,
    ``PayViewModel.java:11317``,
    ``ui/screen/myticket/refundticket/data/OneTicketPartialRefundTripChangeLogger.java:382``)
    뿐이고 어느 요청 빌더도 읽지 않습니다. 이것은 "요청에 안 쓰인다"는 부재
    증거이지 "표시용 값이다"라는 **양성** 출처가 아닙니다.

    할인 없는 성인 1명이면 두 값이 같지만, 할인이나 두 번째 승객이 끼는 순간
    갈라진다 -- 이 부분은 라이브 관찰이며 앱 소스 근거가 아닙니다.

    **스코프**: 이 빌더는 7.0.6 ``PaymentMethodHelper.getCardRequest``
    (``analysis/jadx/sources/com/korail/talk/common/helper/PaymentMethodHelper.java:89-137``)
    중 포인트/마일리지 **미병용** 분기(``pointType`` 이 "없음" 센티넬과 일치해
    ``:130`` 에서 조기 ``return`` 하는 경로)만 구현합니다. :class:`CardPayment`
    에 포인트/마일리지 인자가 없는 것과 정확히 대응하는 의도된 스코프입니다.
    같은 함수가 그 분기를 타지 않을 때 실행하는 병용 경로
    (``:134``, ``paymentMethod.putAll(getPointRequest(i2 + 1, pointData))`` →
    ``getPointRequest``, 같은 파일 ``:587-689``, 카드+마일리지/포인트 결합
    행을 추가로 쌓는 별도의 대형 분기)는 이 라이브러리가 구현하지 않습니다.

    그 조기 반환 분기는 카드 필드들과 별도로 ``hidPontDvCd1`` 도 무조건
    설정합니다(``:130``). 그 인자는 AppSuit 문자열 암호화(``AlienGuard``)
    뒤에 있어 실제 값은 PROTECTED — 정적 분석으로 복구 불가합니다. 이
    빌더는 값을 추측해 채우는 대신 그 키 자체를 보내지 않습니다; 서버가
    ``hidPontDvCd1`` 없이도 이 요청을 받아들이는지는 미확인입니다.
    """
    if not isinstance(card, CardPayment):
        raise KorailProtocolError("KORAIL payment requires a CardPayment")
    window_no = hold.window_no
    # Deliberately NOT hold.total_price: that is the display figure. See the
    # docstring — the amount the app settles is getOriginalReceivedAmount()
    # (PayViewModel.java:11027-11028, which reads PayAmountUiData's
    # getOriginalReceivedAmount at PayAmountUiData.java:248-250), NOT the
    # separate getReceivedAmount() at PayViewModel.java:11058. This comment
    # used to name the latter; that was the wrong getter.
    # When a hold response
    # carries neither h_tot_rcvd_amt nor readable per-seat h_rcvd_amt rows we
    # refuse rather than substitute the display total, because substituting is
    # exactly the defect this replaces.
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
    # The card number must be all digits (a fake test PAN is still digits); the
    # decline happens server-side at authorization.
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
            # 7.0.6's two payment ViewModels both branch on login state before
            # setting this field: PayViewModel.java:6600-6604 (domestic) and
            # FPayViewModel.java:772-778 (foreign) do
            #   if (userState.isLogin()) { setHiduserYn(<literal A>) }
            #   else { setHiduserYn(<literal B>); setHidMbCrdNo(<non-member id>) }
            # The two literals are AppSuit string-encrypted, so neither A nor
            # B's actual value is recoverable from static analysis -- "Y" is
            # unconfirmed. But this client's payment methods (pay_with_card,
            # pay_with_fake_card) both call self._require_session("payment
            # requires") before reaching build_card_payment_form, and no
            # client.py method ever builds a payment form without a session --
            # there is no non-member/guest payment call site anywhere in this
            # library. The "else" (guest) branch above is therefore
            # structurally unreachable here regardless of how this field is
            # fixed, so "Y" is left as the single literal this codebase has
            # ever sent, rather than inventing hidMbCrdNo plumbing for a path
            # nothing calls. Contrast build_price_recalculation_form below,
            # which DOES thread a caller-supplied non_member_no through to a
            # conditional hiduserYn/hidCustNo pair -- proof this codebase
            # already knows the correct pattern when a builder's caller
            # actually offers a non-member identity to branch on. That
            # builder's client.py call site (recalculate_price) still
            # requires a login session like this one does; the difference is
            # only that its request type carries an explicit non_member_no
            # slot for the caller to populate, while ReservationHoldResponse
            # (this builder's only input besides the card) carries no such
            # slot at all -- there is no data here to branch on even if a
            # branch were added.
            "hiduserYn": "Y",
        }
    )
    return form


def _refund_echo_field(value: object, *, field: str) -> str:
    """되울리는 환불 플래그 하나를 그대로 넘깁니다. **비어 있어도 거부하지 않습니다.**

    이 필드를 서버 응답에서 되울리는 실호출부는
    ``MyTicketDetailViewModel.java:1521`` 하나이고, 거기서
    ``ticketDetailOut.getPbpAcepTgtFlg()`` 를 조건 없이 그대로 넘깁니다
    (외국인 승차권 쪽 ``FTicketDetailViewModel.java:634`` 은 이 자리에
    AlienGuard 리터럴 상수를 넣습니다 — 에코가 아닙니다). 그리고 응답 쪽
    DTO(``TicketDetailOut.java:167``)의 이 필드는
    **옵셔널**입니다 — kotlinx 역직렬화 비트마스크가 서버가 이 키를 아예
    안 보낸 경우를 대비해 조건부 기본값(디컴파일에서 빈 문자열로 보이는
    AlienGuard 상수)으로 떨어지도록 생성자를 짜 놨습니다. 즉 실앱도 이 값이
    빈 채로 요청에 실려 나가는 경우가 실제로 있고, 두 호출부 어디에도 그
    값을 검사하거나 되살리는 분기가 없습니다 — "non-null 강제"는 Kotlin
    타입 수준(``null`` 이 아니라는 것)일 뿐이지 "내용이 있어야 한다"는
    뜻이 아니었습니다. 라이브 발권 승차권(스마트티켓, 2026-09-21
    결제, 이후 환불)으로 직접 확인했습니다: 승차권 상세
    조회 응답에 ``pbpAcepTgtFlg``/``h_pbp_acep_tgt_flg`` 키 자체가 없는
    정상 케이스가 있고, 그때 환불 제출은 빈 문자열을 그대로 실어 보내야
    성공합니다. ``None`` 만 빈 문자열로 바꾸고, 그 밖의 비문자열 값은
    여전히 프로그래밍 오류로 거부합니다.
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
    """발권된 승차권의 환불(``refunds.RefundsRequest``) 폼을 만듭니다.

    PNR 필드는 앱의 Retrofit 선언대로 ``txtPnrNo``(P-n-r)입니다 —
    ``NetworkApi.java:603`` 의 ``postRequestRefund`` 가 ``@FieldMap`` 으로
    보내고, 그 맵의 키는 ``RefundTicketIn.java:194`` 의
    ``@SerialName("txtPnrNo")`` 입니다. (예전 인용 ``RefundService.java:29`` /
    ``RefundService.smali:212`` 은 7.0.6 에 없는 클래스였습니다.) srtgo 의 ``ktx.py:1082`` 는 이것을 ``txtPrnNo``
    로 쓰는데, korail2 계보의 오타이며 디컴파일된 앱에 0회 등장합니다. Retrofit
    ``@Field`` 이름은 정확히 일치해야 하므로 그대로 보내면 PNR 없는 환불이
    전송됩니다. 신원은 호출자가 :class:`PaidTicket` 로 줍니다.

    ``settle_mileage``
        ``h_mlg_stl``. 서버 에코가 아니라 호출자의 결정입니다. 기본값은
        ``False``(``"N"``).

        7.0.6 에서 **조건 자체를 재도출했습니다.**
        ``MyTicketDetailViewModel.java:1811`` 의
        ``checkMileage(RefundCommissionOut, TicketDetailOut)`` 이 평문 정수
        비교를 합니다 -- ``:1814`` 가 ``refundCommission.getUsePsbMlgNum()``
        (사용 가능 마일리지)을, ``:1815`` 가 ``getRetFee()``(환불 수수료)를
        ``TextHelper.getInteger`` 로 읽고, ``:1821`` 이 ``prgPsbFlg``
        (``:1812``)가 기대 리터럴과 다르거나 ``usePsbMlgNum < retFee`` 이면
        ``refundTicket$default(this, ticketDetail, false, 2, null)`` 로
        빠집니다.

        **다만 그때 되돌아가는 ``useMileage`` 기본값이 false 라는 것은
        재도출되지 않았습니다.** 예전 판은 ``:2093`` 의 AlienGuard 식
        (``method_name_2(1772681635, -406003104, new byte[]{58}, false)`` 을
        ``Integer.parseInt(...) > 1`` 로 감싼 것)이 ``:1819`` 에서 배열 첨자
        0 으로 쓰이므로 false 라고 논증했는데, ``:1819`` 의 실제 모양은
        ``objArr[... > 1 ? (char) 1 : (char) 0]`` 이고 ``:1818`` 이 만드는
        배열의 길이는 ``... <= 3 ? 2 : 3`` -- 즉 2 아니면 3 입니다. 첨자 0 과
        1 이 모두 유효하므로 그 논증은 닫히지 않습니다.

        **정황 증거는 있습니다(결정적이지는 않습니다).** ``:1828`` 이 똑같은
        식을 첨자로 쓰는 배열 ``objArr2`` 는 ``:1827`` 에서 길이가
        ``... > 0 ? 1 : 0`` 이라 최대 1 입니다. 그 대입이 예외 없이 돈다면
        첨자는 0 일 수밖에 없고 그러면 식은 false 입니다 -- 그러나 이것은
        "앱이 실제로 이 줄을 예외 없이 지난다"는 런타임 가정에 기대는
        추론이지 정적 텍스트만으로 닫히는 결론이 아닙니다.

        그래서 위의 ``False`` 기본값은 **이 라이브러리의 정책**이지 앱의
        기본값을 확인한 결과가 아닙니다. 둘 다 통과할 때에만 ``:1840`` 의
        확인 대화가 뜨고, ``:1855-1858`` 이 Positive/Negative 에 서로 다른
        boolean 을 실어 ``refundTicket(ticketDetail, useMileage)``(``:2074``)
        를 부릅니다. 거기서 ``useMileage`` 는 ``:2079`` 가 만드는 코루틴 객체의
        생성자(``:1466-1469``)를 거쳐 필드 ``STLgly`` 로 잡히고, ``:1515`` 가
        다시 읽어 ``:1521`` 의 ``RefundTicketIn`` 여섯 번째 인자
        (``h_mlg_stl``, DTO 필드 ``RefundTicketIn.java:36``,
        ``@SerialName("h_mlg_stl")`` 은 ``:146``)에
        ``z ? <리터럴 A> : <리터럴 B>`` 로 들어갑니다.

        **아직 평문이 아닌 것**: ``:1821`` 의 ``prgPsbFlg`` 비교 대상,
        ``:1521`` 의 두 1바이트 값(길이만 ``"Y"``/``"N"`` 과 일치), 그리고
        ``:1856``/``:1858`` 의 boolean 식이 모두 AlienGuard 로 보호돼 있어
        **어느 갈래가 "Y" 를 싣는지는 확정하지 못했습니다.** 예전 인용
        ``ticketReturn/a.java:185-190`` 은 철회합니다 -- 6.5.0 경로이고 7.0.6
        디컴파일에 ``ticketReturn`` 패키지가 없습니다.
    ``pbp_acceptance_target_flag``
        ``pbpAcepTgtFlg``. **항상 그대로 에코합니다 — 값이 없어도 거부하지
        않습니다.** 7.0.6 에서 이 값을 서버 응답에서 되울리는 곳은
        ``MyTicketDetailViewModel.java:1521`` 하나로, 조건 없이
        ``ticketDetailOut.getPbpAcepTgtFlg()`` 를 넘깁니다(외국인 승차권
        경로 ``FTicketDetailViewModel.java:634`` 은 에코가 아니라 리터럴
        상수를 넣습니다). DTO
        (``RefundTicketIn.java:111``)는 이 필드를 non-null 로 강제하지만,
        그건 Kotlin 타입 수준의 제약일 뿐입니다 — 응답 쪽 DTO
        (``TicketDetailOut.java:167``)에서 이 필드는 옵셔널이라 서버가 키를
        아예 안 보내면 조건부 기본값(빈 문자열)으로 떨어지고, 그 기본값이
        검사 없이 그대로 요청에 실립니다. 이전 구현은 값이 없으면 ``"N"``
        을 대신 지어 보냈는데, 이는 서버가 준 값을 조용히 대체하는
        SUBSTITUTION 이었습니다(W1 finding 7). 지금은 ``None`` 이면(그리고
        :attr:`PaidTicket.pbp_acceptance_target_flag` 도 ``None`` 이면) 빈
        문자열로 에코합니다 — 이것도 지어내는 게 아니라 실앱이 같은 상황에서
        내리는 기본값과 같은 값입니다. 사전 응답에 실제 값이 있었다면(예:
        승차권 상세 조회 응답의 ``pbp_acceptance_target_flag``) 그 값을
        넘기십시오; 없었다면 아무것도 넘기지 않아도 됩니다.

    **더 이상 받지 않는 인자: ``return_times_division_code``.** 이전 버전은
    이 값을 ``tk_ret_tms_dv_cd`` 로 실었지만, 7.0.6 은 이 필드를 실제
    환불 제출에 절대 싣지 않습니다 —
    ``RefundTicketIn.java:135`` 의 컴파일된 기본값이 ``null`` 이고, 이 DTO를
    만드는 유일한 두 호출부(``MyTicketDetailViewModel.java:1521``,
    ``FTicketDetailViewModel.java:634``)가 둘 다 리터럴 ``(String) null`` 을
    넘기며, 두 곳의 "기본값 사용" 비트마스크조차 이 필드의 비트를 포함해
    "기본값 경로"도 ``null`` 로 떨어집니다. 수수료 응답이 돌려주는 같은
    이름의 필드는 ``RefundTicketViewModel.java:1012`` 에서 UI 다이얼로그
    변형을 고르는 데만 쓰이고 제출로 되돌아가지 않습니다(W3 finding 6). 즉
    이 키는 앱이 한 번도 만든 적 없는 전선 모양이었고, 그 인자를 받아들이는
    것 자체가 잘못이라 제거했습니다 — PyPI 배포가 보류 중이라 호환성 약속이
    없으므로 조용한 no-op 대신 시그니처에서 뺐습니다. 여전히 수수료 응답의
    ``tk_ret_tms_dv_cd`` 를 읽고 싶다면
    :meth:`~korail_mobile_api.KorailClient.get_refund_commission` 이 돌려주는
    :attr:`ticket_return_times_division_code` 를 UI 판단용으로만 쓰십시오.
    """
    for name, value in (
        ("pnr_no", ticket.pnr_no),
        ("sale_date", ticket.sale_date),
        ("sale_window_no", ticket.sale_window_no),
        ("sale_sequence", ticket.sale_sequence),
        ("return_password", ticket.return_password),
    ):
        _required_mutation_text(value, field=f"PaidTicket.{name}", context="refund")
    # Not coerced with bool(): the wire flag is "Y"/"N", and a caller who passes
    # the string "N" expecting it to read as false would otherwise get
    # bool("N") is True -- "Y" on the wire, the opposite of what was asked, on
    # the flag that decides whether mileage is settled against this refund.
    # build_standby_wait_form refuses the same shape for the same reason.
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
    # tk_ret_tms_dv_cd is deliberately absent -- see the docstring above.
    # 7.0.6 never sends this field on a real refund submission (its only two
    # call sites both pass a literal null), so there is nothing correct to
    # echo here.
    return form


def build_station_refund_execution_form(
    config: KorailConfig,
    request: StationRefundExecutionRequest,
) -> dict[str, str]:
    """Build ``ExecuteOnlineRefundsIn`` from a verified station ticket.

    The APK declares these twelve ``@SerialName`` keys in
    ``ExecuteOnlineRefundsIn.java:60``. This function prepares a form only;
    execution still requires an authenticated session and the refund category
    route. Values are validated once, by the request's ``__post_init__``.
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
    # StationRefundExecutionRequest.__post_init__ already refused a blank
    # value on every one of these twelve fields.
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
    """``research.dcntCrdInfo.do`` — 할인카드(N카드)를 구매합니다.

    스칼라 넷에 평평하게 편 맵 둘입니다. 라우트는 ``NetworkApi.java:336`` 의
    ``postDcntCrdInfo`` 이고 ``@FieldMap Map<String, String>`` 하나만 받으므로
    (응답은 ``NCardInfoOut``) 평평하게 펴는 것 자체는 7.0.6 과 맞습니다.

    여정 맵의 키 다섯은 **7.0.6 에 평문으로 남아 있습니다** —
    ``NCardjrny.java`` 의 ``@SerialName`` 이 ``jrnyTpCd_``·``runDt_``·
    ``trnNo_``·``dptRsStnCd_``·``arvRsStnCd_`` 입니다(전부 꼬리 밑줄).
    입력 모델은 ``NCardInfoIn.java:29-39`` 이고, 배열을 1-based 로 인덱싱하는
    분기는 ``NetworkService.java:15345-15367`` 에 있습니다. 한때 여기 "두 맵 다
    미출처" 라고 적었던 것은 지나쳤습니다.

    아직 확인 못 한 것은 **부가사용자 맵(``apdUsrInfo``) 쪽 키와 기본 인자의
    실제 값, 그리고 최종 런타임 순서**입니다. 옛 인용
    ``ResearchService.java:68-70`` 과 ``NCardReservationDao.java`` 는 7.0.6 에
    없는 6.5.0 클래스이고, 이 계정은 할인카드가 없어 라이브 확인도 못 했습니다.
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
    # 7.0.6 NCardInfoIn declares apdUsrCnt and only the _1 keys of one
    # additional user; a second would go out under keys no DTO has.
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
    """``reservation.dcntCrdExtn.do`` — 할인카드의 유효기간을 연장합니다.

    7.0.6 은 이 경로에 ``@FieldMap`` 폼으로 보냅니다 --
    ``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:518-520``
    이 ``@FormUrlEncoded`` 와
    ``@POST("/classes/com.korail.mobile.reservation.dcntCrdExtn.do")`` 를 달고
    ``postNCardExtension(@FieldMap Map<String, String>)`` →
    ``NCardExtensionOut`` 을 선언합니다. 줄 번호를 믿지 않고 ``@POST`` 문자열을
    직접 읽었으며, 그 문자열은 이 폼을 붙여 보내는 경로(``client.py:2263``)와
    정확히 같습니다.

    아직 출처가 없는 것은 **"6.5.0 은 ``@Query`` 로 보냈다"는 대조 하나**
    입니다 -- 근거였던 ``ResearchService.java:65-66`` 은 이 저장소의 7.0.6
    디컴파일에 없고, 위 ``NetworkApi`` 줄은 7.0.6 만 말해 주므로 6.5.0 쪽을
    대신 증명하지 못합니다. 6.5.0 시절 기록으로만 남겨 둡니다.

    공통 셋에 카드 승차권의 네 부분 자격증명이 붙습니다. 예전 인용
    ``TicketListActivity.java:1067-1072`` 은 **철회합니다** -- 6.5.0 클래스이고
    7.0.6 디컴파일에 그 이름의 파일이 없습니다(``analysis/`` 전체에서 그 이름은
    ``analysis/device-pull/2026-09-14_korail-7.0.6/NOTES.md`` 의 "6.5.0 인용은
    7.0.6 에서 찾을 수 없다"는 메모에만 나옵니다).

    **같은 주장을 7.0.6 에서 재도출했습니다.** 이 네 필드는
    ``NCardExtensionIn`` 의 ``saleWctNo``/``saleDd``/``saleSqno``/``tkRetPwd``
    이고(``network/model/NCardExtensionIn.java:31-34``, 인자 이름은 ``:158`` 의
    ``copy`` 시그니처), 넷 다 ``@SerialName`` 이 없으므로(``:55``) 전선 키가
    속성명 그대로라고 **추론**합니다 -- kotlinx 기본 규칙에 기댄 추론이고, 이
    빌더가 쓰는 키와 일치합니다. ``NCardExtensionIn$$serializer.java`` 의
    디스크립터 원소 이름은 보호되어 있어 직접 검증하지 못했습니다. 값의 출처는
    ``MyTicketDetailViewModel.java:1049`` 이 ``new NCardExtensionIn(
    ticketDetailOut.getOrgtkWctNo(), …getOrgtkRetSaleDt(), …getOrgtkSaleSqno(),
    …getOrgtkRetPwd())`` 로 넘기는 ``TicketDetailOut`` 의 네 값이며, 그 전선
    이름이 바로 ``h_orgtk_wct_no`` / ``h_orgtk_ret_sale_dt`` /
    ``h_orgtk_sale_sqno`` / ``h_orgtk_ret_pwd`` 입니다
    (``network/model/TicketDetailOut.java:117``, 접근자 애노테이션은
    ``:458,462,466,470``). 즉 짝은 ``saleDd`` ← ``h_orgtk_ret_sale_dt``,
    ``tkRetPwd`` ← ``h_orgtk_ret_pwd`` 입니다.

    필드 수를 세는 문장은 일부러 뺐습니다 -- DTO 의 **선언** 원소는 공통 넷
    (Device/Version/Key/lang, ``CommonIn`` 상속)에 위 넷을 더해 여덟이지만,
    kotlinx 가 원소를 건너뛸 수 있어 **실제 전송 키 수**는 요청마다 다릅니다.
    다만 ``lang`` 의 생략은 "기본값과 같으면 뺀다" 는 값 비교 하나가
    아닙니다 -- ``CommonIn.java:467`` 이 먼저
    ``output.shouldEncodeElementDefault(serialDesc, 3)`` 를 묻고, 그것이
    false 인 **경우에만** ``self.lang`` 을 ``languageProvider?.getSTLeec()``
    와 비교해 같을 때 return 합니다(``:470-471``). 어느 한쪽이라도 어긋나면
    ``:474`` 가 ``lang`` 을 씁니다. 이 빌더는 ``config.lang`` 이 없으면 일곱
    키, 있으면 여덟 키를 보냅니다.
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


#: 가능한 승객 행 키 접두사 최대 여덟 개. 일반 예약에서는 0명 행을
#: 전송하지 않으며, N카드 홀드는 존재하는 행을 한 행으로 대체합니다.
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
    """할인카드(N카드)로 좌석 하나를 결제하는 홀드 폼을 만듭니다.

    **평범한 예약 라우트입니다.** 예전 인용 ``w4/a.java:93-104`` /
    ``ReservationRequest`` / ``ReservationDao`` /
    ``CertificationService.java:52-54`` 는 **철회합니다** -- 넷 다 6.5.0
    이름이고 7.0.6 디컴파일에 그 파일도 클래스도 없습니다.

    **같은 주장을 7.0.6 에서 재도출했습니다.** 라우트는 보통의
    ``certification.TicketReservation`` 하나이고
    (``network/NetworkApi.java:752-753``, ``postTicketReservation`` →
    ``ReservationOut``), N카드 전용 엔드포인트는 없습니다. N카드는 승객 블록
    분기일 뿐입니다 -- ``Passengers.toTicketReservationInput(ReservationType
    screenMode, String nCardCrdNo)``(``common/define/Passengers.java:731``)
    가 ``:765-766`` 에서 ``screenMode == ReservationType.MY_N_CARD_RESERVATION``
    일 때만 ``txtDiscKndCd`` 에 ``ReqDiscount.N_CARD.getDiscKndCd()`` 를,
    ``txtCardNo_`` 에 ``nCardCrdNo`` 를 넣고, 아닐 때는 승객 타입 자신의 할인
    코드와 빈 문자열을 넣습니다. 그 네 자리가 곧
    ``txtCompaCnt``/``txtPsgTpCd``/``txtDiscKndCd``/``txtCardNo_`` 입니다
    (``network/model/TicketReservationInPassengerInfo.java:55``,
    ``@SerialName`` 은 ``:105,109,113,117``) -- 이 빌더가 쓰는 키와 같은
    집합입니다(인덱스 ``1`` 은 이 패키지가 붙입니다).

    :data:`KORAIL_DISCOUNT_CARD_DISCOUNT_CODE` 의 **값**은 여전히 미확인입니다
    -- ``ReqDiscount.N_CARD`` 의 코드가 AlienGuard 로 암호화돼 있어
    (``common/define/ReqDiscount.java:36``) 평문을 읽을 수 없습니다. 그 리터럴은
    라이브 확인값이며 앱 소스에서 재도출한 것이 아닙니다.
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


# 7.0.6 PriceReCalculationIn 이 선언하는 네 스칼라 txtPsrmClCd1, txtSeatAttCd2,
# txtSeatAttCd4, txtSeatAttCd5 는 **이제 표현할 자리가 있습니다** —
# PriceRecalculationRequest 의 cabin_class_code 와 seat_attribute_code_2/4/5 입니다.
# 넷 다 선택이고 기본값은 None 이라, 넘기지 않으면 예전과 똑같이 하나도 실리지
# 않습니다. 그 기본 동작이 앱과 어긋나지 않는다는 근거는 PayViewModel.smali
# :11834-11850 으로, 일반 재계산 경로가 네 인자를 default-null 로 구성합니다.
#   analysis/jadx/sources/com/korail/talk/network/model/PriceReCalculationIn.java:38-41
#     -- 넷 다 @SerialName 이 없으므로 전선 키는 속성명 그대로라고 추론합니다
#        (kotlinx 기본 규칙에 기댄 추론). 생성자 :114-133 에서 넷 다
#        checkNotNullParameter 대상이 아니라 널 허용입니다.
#   analysis/jadx/sources/com/korail/talk/network/model/PriceReCalculationIn$$serializer.java:44-47
#     -- 이 자리의 디스크립터 원소 이름은 AlienGuard 로 보호되어 있어, 위 키
#        추론을 직접 검증하지 못했습니다.
# 값을 **실제로 채워 보낸 적은 없습니다** — 어떤 화면 상태가 그 값을 만드는지는
# 추적하지 않았으므로, 채워 보내는 쪽은 여전히 미검증입니다.
def build_price_recalculation_form(
    config: KorailConfig,
    request: PriceRecalculationRequest,
) -> dict[str, str | list[str]]:
    """``certification.PriceReCalculation`` — 홀드된 PNR 의 운임을 다시 계산합니다.

    라우트 선언은 ``NetworkApi.java:583`` 의 ``postPriceReCalculation`` 입니다 —
    ``@FieldMap`` 하나에 ``@Field("psg_tp_dv_cd")``/``@Field("psrm_cl_cd")`` 처럼
    **병렬 리스트**들이 따로 붙는 모양이고, 그래서 이 폼도 반복 키를 냅니다.
    요청 DTO 는 ``PriceReCalculationIn.java:31`` 입니다.

    예전에 달려 있던 ``CertificationService.java:35-37``·``a6/C1042B.java``·
    ``DiscountPriceDao.java`` 는 전부 7.0.6 에 없는 6.5.0 클래스였습니다.

    **어느 화면이 이 호출을 만드는지는 재도출했습니다** -- 결제 화면의
    ``PayViewModel.executeDiscountPrice`` 입니다. smali 쪽:
    ``PayViewModel.smali:11291`` 이
    ``.method private final executeDiscountPrice(ILjava/util/List;)V`` 이고,
    그 본문 ``:11834-11850`` 이 ``PriceReCalculationIn`` 을 생성합니다. 그
    인스턴스는 ``PayViewModel$executeDiscountPrice$1.smali:420`` 에서 필드
    ``STLavu`` 로 읽혀 ``:543`` 의
    ``NetworkRepository.priceReCalculation(PriceReCalculationIn, Continuation)``
    으로 들어갑니다. jadx 쪽에서도 같은 줄이 보입니다 --
    ``PayViewModel.java:1233`` 의 ``@DebugMetadata`` 가 그 내부 클래스를
    ``PayViewModel$executeDiscountPrice$1`` 로 이름 짓고, ``:1308`` 이
    ``STLavu`` 를 읽어 ``:1316`` 이
    ``networkRepository.priceReCalculation(...)`` 을 부릅니다.
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
        # 비회원 세션만 이 둘을 쓰고, 쓸 때는 함께 씁니다. 근거는 7.0.6 에
        # 있습니다 — ``PriceReCalculationIn.java:32,34`` 가 ``hidCustNo`` 와
        # ``hiduserYn`` 을 평문 필드로 선언하고(생성자 인자 대응 ``:114-129``),
        # ``PayViewModel.java:6167-6168`` 이 비로그인 조건에서 두 값을 함께
        # 준비합니다. 거기서 잘린 구성·전송 단계는 smali 로 이어집니다:
        # ``PayViewModel.smali:11764-11805`` 가 값을 만들고 ``:11834-11850`` 이
        # ``PriceReCalculationIn`` 에 넣습니다.
        #
        # 한때 여기 "두 키가 이 DTO 에 있는지조차 확인할 수 없다 — 미출처" 라고
        # 적었던 것은 틀렸습니다. **속성이 보이지 않는 것**과 **@SerialName 전선
        # 철자가 보호된 것**을 같은 것으로 본 실수였습니다. 아직 확인 못 한 것은
        # 후자, 그리고 ``"N"`` 리터럴의 평문입니다. 예전 인용
        # ``a6/C1042B.java:290-293`` 은 7.0.6 에 없는 6.5.0 클래스입니다.
        form["hiduserYn"] = "N"
        form["hidCustNo"] = non_member_no
    form["txtPsgGridcnt"] = str(len(rows))
    for wire_name, _ in _PRICE_RECALCULATION_ROW_FIELDS:
        form[wire_name] = columns[wire_name]
    # 네 선택 스칼라. 넘긴 것만 싣습니다 — 기본값 None 이면 키 자체가 없고,
    # 그것이 앱의 일반 경로와 같습니다(위 주석의 PayViewModel.smali 근거).
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
    """``cart.addCartList`` — 홀드된 예약을 장바구니에 담습니다.

    예전 인용 ``CartService.java:11-13`` / ``AddCartDao.java:9-24`` 는
    **철회합니다** -- 둘 다 6.5.0 이름이고 7.0.6 디컴파일에 그 파일이 없습니다
    (``AddCartDao`` 는 ``analysis/`` 전체에서 0회, ``CartService`` 는 우리
    보고서 ``analysis/reports/src-verification/`` 안의 6.5.0→7.0.6 대응표에만
    나옵니다).

    **같은 필드 주장을 7.0.6 에서 재도출했습니다.** 공통 셋 외의 필드는
    ``hidPnrNo`` 하나입니다 -- ``network/model/AddCartListIn.java:25`` 가
    ``extends CommonIn`` 이고 추가 필드가 ``hidPnrNo``(``:30``) 하나뿐이며
    전선 이름은 ``@SerialName("hidPnrNo")``(``:52``, ``:79``)입니다. 라우트는
    ``network/NetworkApi.java:266-267`` 의 ``postAddCartList``
    (``@FieldMap`` → ``AddCartListOut``)입니다. 호출부 다섯 곳
    (``PayViewModel.java:5942``, ``TrainSeatMapViewModel.java:267``,
    ``TrainScheduleViewModel.java:370``,
    ``ReservationMergeViewModel.java:164``,
    ``AirportBusSeatMapViewModel.java:159``)이 모두 문자열 **하나**만
    넘기며, 그 값이 PNR 임을 평문으로 읽을 수 있는 **호출 경로**는 이제 다섯
    곳 모두에서 하나씩 확인됩니다(예전 판은 "둘"이라고 적었는데 좁았습니다):

      * ``ReservationMergeViewModel.java:164`` --
        ``new AddCartListIn(…this.reservationOut.getHPnrNo())`` 한 줄.
      * ``TrainSeatMapViewModel`` -- ``:968`` 이 예약 응답의
        ``reservationOut.getHPnrNo()`` 를 ``hPnrNo`` 로 잡고, ``:997`` 이
        ``addCartList(hPnrNo)`` 를 부르며, ``:1766-1771`` 이 코루틴 객체
        생성자로 넘겨 ``:242-244`` 가 필드 ``STLapk`` 에 저장하고, ``:267`` 이
        ``new AddCartListIn(this.STLapk)`` 로 씁니다.
      * ``TrainScheduleViewModel`` -- ``:1452``
        (``final String hPnrNo = reservationOut.getHPnrNo()``) → ``:1481``
        ``addCartList(hPnrNo)`` → ``:2572-2577`` → 생성자 ``:345-347``
        (``this.STLapk = str``) → ``:370`` ``new AddCartListIn(this.STLapk)``.
      * ``AirportBusSeatMapViewModel`` -- ``:1620``
        (``((ReservationOut) success.getData()).getHPnrNo()``) → ``:1638``
        ``addCartList(hPnrNo)`` → ``:735-740`` → 생성자 ``:134-136`` →
        ``:159`` ``new AddCartListIn(this.STLapk)``.
      * ``PayViewModel`` -- ``:14427`` 이 **응답이 아니라 재계산 입력**의
        ``priceReCalculationIn2.getHidPnrNo()`` 를 읽어 ``:14431`` 의
        ``executeAddCart(hidPnrNo, …)`` 로 넘기고, ``:5920`` 의
        ``executeAddCart(String str, …)`` 가 ``:5942``
        ``new AddCartListIn(str)`` 로 씁니다. 앞의 넷과 달리 PNR 이 어느 서버
        응답에서 왔는지까지는 추적하지 않았습니다.

    **이것은 확인된 호출 경로이지 모든 진입점에 대한 증명이 아닙니다.** 각
    ViewModel 의 ``addCartList``/``executeAddCart`` 에는 위에서 추적한 것
    말고도 호출부가 더 있습니다 -- ``TrainScheduleViewModel`` ``:2382``·
    ``:6478``·``:6729``·``:6926``, ``TrainSeatMapViewModel`` ``:3692``·
    ``:3769``·``:4363``·``:4573``, ``AirportBusSeatMapViewModel`` ``:1779``,
    ``PayViewModel`` ``:14563``. 그쪽이 무엇을 넘기는지는 확인하지
    않았습니다.

    **다만 "응답이 맨 ``BaseResponse``" 라는 부분은 7.0.6 에서 틀렸습니다.**
    ``network/model/AddCartListOut.java:24-25`` 는 ``extends CommonOut`` 에
    더해 ``psgDiscAddInfos`` 를 갖습니다(``@SerialName("psgDiscAdd_infos")``,
    ``:51``·``:76``). ``CommonOut`` 자체의 맨 형태는 **속성** 셋
    ``_hMsgTxt``/``hMsgCd``/``strResult``
    (``network/model/CommonOut.java:42-44``)이고, **전선 키**는 각각
    ``h_msg_txt``/``h_msg_cd``/``strResult`` 입니다 -- 앞의 둘만
    ``@SerialName`` 으로 이름이 바뀌고(``:392``, ``:388``), ``strResult`` 는
    애노테이션이 없어 속성명이 그대로 전선 이름입니다. 한때는 이 응답을
    모델링하지 않아 전용 파서가 없었지만 **지금은 아닙니다** --
    :class:`~korail_mobile_api.mutation_models.CartAddResponse` 와
    :func:`~korail_mobile_api.mutation_parsers.parse_cart_add_response` 가
    있고, :meth:`~korail_mobile_api.client.KorailClient.add_to_cart` 는 그
    파서를 거친 타입을 돌려줍니다. ``psgDiscAdd_infos`` 안의 행은
    :attr:`~korail_mobile_api.CartAddResponse.discount_additions` 로 나오고
    원본은 ``raw`` 에 남습니다 -- 다만 행 부분은 라이브 미검증입니다.
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
