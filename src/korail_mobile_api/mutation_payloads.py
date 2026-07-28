"""상태를 바꾸는 라우트의 요청 폼 빌더.

예약(직통·환승·병합·예약대기·좌석지정), 미결제 취소, 카드 결제, 환불, 운임
재계산, 할인카드(N카드) 구매·연장·예약, 장바구니 추가의 폼을 만듭니다. 읽기
쪽은 :mod:`korail_mobile_api.payloads` 와
:mod:`korail_mobile_api.read_payloads` 입니다.

여기 함수들은 dict 를 만들 뿐 아무것도 보내지 않습니다. 실제 전송은
:meth:`~korail_mobile_api.http.KorailHttpClient.post_mutation_form` 하나이고 그
앞에 consent 와 라우트 가드가 있습니다.

**라이브로 확인된 조합은 좁습니다.** 성인 1명·일반실·직통 즉시예약
(``txtJobId="1101"``)의 예약 → 취소 왕복만 KORAIL 이 받아들이는 것이
확인됐습니다. 환승·병합·예약대기·좌석지정 폼과 다인·특실 조합, 할인카드 관련
폼은 전부 APK 의 요청 빌더를 그대로 옮긴 것이며 전송된 적이 없습니다. 각
빌더의 docstring 이 그 경계를 따로 적어 둡니다.
"""
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
    """한 구간의 좌석지정 목록을 job 종류와 승객 구성에 비추어 검사합니다.

    좌석 목록은 ``"1103"`` 에만 속합니다. 앱도 ``OSrcar`` 맵을 설치하는 바로 그
    자리에서 job id 를 ``"1103"`` 으로 바꾸고(``C5/a.java:143-146``), 평범한
    ``"1101"`` 여정을 다시 만들 때마다 그 맵을 비웁니다(``C5/a.java:118``).

    개수 규칙도 앱의 것입니다. ``SeatSearchActivity.java:902`` 는
    ``selectedSeatCount == G0()`` 인 동안만 "선택완료"를 활성화하고 ``G0()``
    (``:273-278``)은 요청의 ``txtTotPsgCnt`` 입니다. 모자란 목록은 보내기 전에
    여기서 거부합니다. 규칙이 구간별인 것은 앱의 좌석 선택기가 구간별이기
    때문이며(``C5/a.java:120-133``), 비교 대상인 승객 총수는 예약 전체의
    값입니다.
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
    """승객 구성과 좌석 등급으로 예약(홀드) 폼을 만듭니다.

    ``passengers`` 는 성인 1명, ``seat_class`` 는
    :attr:`KorailSeatClass.GENERAL <korail_mobile_api.KorailSeatClass.GENERAL>`
    이 기본입니다. 둘 다 생략한 호출은
    :func:`build_single_adult_reservation_form` 과 같은 폼을 만듭니다.

    ``job_type`` 은 예매 화면의 세 동작 중 무엇인지를 고르며 기본값은
    :attr:`KorailReservationJobType.IMMEDIATE
    <korail_mobile_api.KorailReservationJobType.IMMEDIATE>`
    (``txtJobId="1101"``)입니다.

    * :attr:`~korail_mobile_api.KorailReservationJobType.SEAT_DESIGNATED`
      (``"1103"``)는 ``seats`` 를 추가로 요구합니다. 승객 한 명당
      :class:`~korail_mobile_api.KorailSeatAssignment` 하나입니다.
    * :attr:`~korail_mobile_api.KorailReservationJobType.STANDBY`(``"1102"``)는
      예약대기입니다. 좌석을 요구하지 않는 대신 열차 행 자신의 예약대기 가능
      플래그와 일반실을 요구합니다.

    ``seats`` 는 좌석지정 job 에서만 받습니다. 키는 ``OSrcar`` 의 것이고
    (``OSrcar.java:6-11``) 여정 키 뒤에 붙는 ``@FieldMap`` 입니다
    (``CertificationService.java:52-54``). ``txtSrcarCnt`` 가 먼저, 그다음
    ``txtSrcarNo{i}``/``txtSeatNo{i}`` 가 ``i`` 를 **1**부터 셉니다
    (``SeatSearchActivity.java:675-683``). ``txtSrcarCnt`` 는 호차 수가 아니라
    **좌석 수**입니다.

    이 빌더는 여정 **하나**를 예약합니다(``txtJrnyCnt="1"``). 환승 여정의 두
    구간은 :func:`build_transfer_reservation_form` 을 쓰면 됩니다.

    라이브로 확인된 것은 성인 1명·일반실·``"1101"`` 모양뿐입니다. 다인·특실
    폼과 나머지 두 job 종류는 앱의 요청 빌더를 옮긴 것이지만 전송된 적이
    없습니다.
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
    """환승 여정의 예약(홀드) 폼을 만듭니다 — 두 구간, PNR 하나.

    :func:`build_reservation_form` 에서 여정 블록이 반복된 것입니다. 앱도 두
    경우를 빌더 하나로 처리하므로(``C5/a.java:52-119``) 필드 구성을 정하는 것은
    구간 수뿐입니다.

    * ``txtJrnyCnt`` 는 배열 길이에서 유도됩니다(``C5/a.java:55``). 플래그가
      아니므로 직통 예약이 환승 폼을 내보내게 만들 수 없습니다.
    * 여정 인덱스는 **1부터**입니다(``C5/a.java:57-77``).
    * ``txtJrnyTpCd{i}`` 는 인덱스가 아니라 **길이**를 봅니다
      (``C5/a.java:60``). 그래서 환승의 **두** 구간이 모두 ``"14"`` 를 싣습니다.
    * ``txtJrnySqno{i}`` 는 ``DecimalFormat("000")`` 을 거친 루프 인덱스라
      1구간이 ``"001"``, 2구간이 ``"002"`` 입니다(``S4/O.java:19-21``).

    ``legs`` 는 정확히
    :data:`~korail_mobile_api.KORAIL_MAX_JOURNEY_LEGS`(2)개의 열차를 승차 순서로
    담아야 하고, :attr:`TransferItinerary.legs
    <korail_mobile_api.TransferItinerary.legs>` 가 그것을 만들어 줍니다.

    무엇이 함께 쓰이고 무엇이 안 되는지.

    * **승객 구성** — 함께 쓰입니다. 구간별이 아니라 예약 단위입니다
      (``w4/a.java:47-74``).
    * **좌석 등급** — 함께 쓰이며 정말로 **구간별**입니다(``C5/a.java:59,97``).
      두 구간에 같은 :class:`~korail_mobile_api.KorailSeatClass` 하나를 주거나
      구간별 시퀀스를 주면 됩니다.
    * **좌석지정**(``"1103"``) — 함께 쓰이며 역시 구간별입니다
      (``C5/a.java:120-133``, ``OSrcar.java:21-30``). ``seats`` 는 구간당 시퀀스
      하나이고, 각 시퀀스는 승객당
      :class:`~korail_mobile_api.KorailSeatAssignment` 하나를 담습니다.
    * **예약대기**(``"1102"``) — 함께 쓰이지 **않으며** 이 빌더가 거부합니다.
      앱에도 독립된 관문이 둘 있습니다. 예약대기 가능 검사가
      ``if (!isDirect) return false`` 로 시작하고(``a5/k.java:120-127``), 유일한
      ``setJobId("1102")``(``DirectInquiryActivity.java:434``)는
      ``TransferInquiryActivity`` 가 그 메서드를 재정의해 결코 닿지 않습니다.

    라이브 미검증 — 여기서 만든 환승 폼이 KORAIL 로 전송된 적은 없습니다.
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
    """병합예약의 **두 번째** 홀드 폼을 만듭니다 — 열차 하나, 여정 둘.

    병합은 환승이 아닙니다. 물리적으로 한 대인 열차를 중간역에서 갈라 두 구간을
    다르게 앉히는 것이며(좌석+좌석 또는 좌석+입석), 앱은 자기만의 루프로
    만듭니다(``DirectInquiryActivity.java:576-601``). 다섯 단계 전체 흐름은
    :data:`~korail_mobile_api.KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` 에
    있습니다.

    환승 폼과 다른 네 가지는 전부 그 루프에서 나옵니다.

    * ``txtJrnyTpCd{i}`` 가 루프 **인덱스**를 봅니다. 1구간은 ``"21"``(병합
      선행), 2구간은 ``"22"``(병합 후행)입니다. 환승은 두 구간이 모두 ``"14"``
      인데 여기서는 갈립니다(``smali:5641``).
    * ``txtStndFlg`` 는 ``isStndSeat`` 에서 유도하지 않고 ``"Y"`` 로 박습니다
      (``smali:5887-5891``). 전환 대상이 입석 홀드라는 것이 이 흐름의
      전제이기 때문입니다.
    * ``txtPsrmClCd2`` 는 ``txtPsrmClCd1`` 에서 **복사**됩니다
      (``smali:5919-5983``). 그래서 ``seat_class`` 를 구간별이 아니라 **하나**만
      받습니다 — 앱도 두 반쪽이 서로 다른 등급인 병합 예약을 만들 수 없습니다.
    * ``arvTm_2`` 가 **없고**, ``arvTm_1`` 은 1구간이 아니라 **전체 구간**의
      도착시각입니다. 병합 루프가 ``setArvTm`` 을 부르지 않고 ``"1202"`` 홀드
      요청의 ``OJrny`` 가 치환이 아니라 병합되기 때문입니다
      (``ReservationRequest.java:29-46``, ``:158-160``). 이 빌더가
      ``standing_hold_train`` 을 요구하는 이유가 그것입니다.

    ``standing_hold_train`` 은 ``"1202"`` 홀드를 건 직통 행 —
    ``job_type=MERGE_STANDING`` 으로 :meth:`KorailClient.reserve
    <korail_mobile_api.KorailClient.reserve>` 에 넘긴 바로 그
    :class:`~korail_mobile_api.TrainSummary` 입니다. ``legs`` 는
    ``research.mergeSeatsC.do`` 가 순서대로 답한 두 행입니다
    (:attr:`MergeSeatsInquiryResponse.trains
    <korail_mobile_api.MergeSeatsInquiryResponse.trains>`).

    전송된 적 없음 — 여기서 만든 것이 KORAIL 로 나간 적이 없습니다.
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
    """이 조회 행에 앱이 입석+좌석 예매를 제시할지.

    ``S4/J.java:61-63`` 의 ``isMixedSeat(cabin, h_yms_apl_flg)`` 를 등급별 플래그
    집합으로 풀어 쓴 것입니다 —
    :data:`~korail_mobile_api.KORAIL_MERGE_SEAT_FLAGS_BY_CABIN` 참조. 앱이 보는
    행 속성도 이것 하나뿐이고(``a5/u.java:378-380``), ``:394-397`` 이 그것만
    보고 예매 버튼의 문구를 바꾸며 ``"1202"`` 를 붙입니다.
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
    """병합된 여정 하나가 싣는 열두 값.

    ``_journey_fields`` 의 집합에서 ``arrival_time`` 을 뺀 것입니다. 병합 루프는
    ``TrainInfo`` 마다 게터 열둘을 읽고 ``getH_arv_tm()`` 은 그중에 없습니다
    (``smali/…/DirectInquiryActivity.smali:5730-5880``). 열세 번째 구간 키인
    ``txtChgFlg{i}`` 는 상수 ``"N"`` 입니다.
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
    """좌석 속성 키 — ``OSeat.setSeatAttCd4``, OSeat.java:32-35."""
    return "txtSeatAttCd4" if journey == 1 else "txtSeatAttCd4_1"


def _srcar_count_key(journey: int) -> str:
    """좌석 수 키 — ``OSrcar.setSrcarCnt``, OSrcar.java:21-23."""
    return "txtSrcarCnt" if journey == 1 else "txtSrcarCnt1"


def _srcar_no_key(journey: int, seat: int) -> str:
    """호차번호 키 — ``OSrcar.setSrcarNo``, OSrcar.java:25-30."""
    return f"txtSrcarNo{seat}" if journey == 1 else f"txtSrcarNo1_{seat}"


def _seat_no_key(journey: int, seat: int) -> str:
    """좌석번호 키 — ``OSrcar.setSeatNo``, OSrcar.java:14-19."""
    return f"txtSeatNo{seat}" if journey == 1 else f"txtSeatNo1_{seat}"


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
    """구간당 등급 하나. 값 하나로 주거나 구간별 시퀀스로 주면 됩니다.

    구간별인 것은 앱이 구간별이기 때문입니다. ``C5/a.java:59`` 는 구간 인덱스로
    ``U4.a.getSelectSeatTypeCode(D0(), i9)`` 를 읽고 ``:97`` 이 그것을
    ``txtPsrmClCd{i}`` 로 씁니다.
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
    """공개 예약 폼 둘 뒤에 있는 단 하나의 빌더.

    ``C5/a.java:52-119`` 는 열차 배열을 도는 루프 하나이므로 구현 하나가 직통
    예약과 환승 예약을 모두 덮습니다. 다른 것은 구간 수뿐이고, 구간이 하나인
    호출은 키 순서까지 단일 구간 폼과 동일한 바이트를 냅니다.
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
    """여정 일련번호를 세 자리로 채웁니다 — ``S4/O.getSequenceNo``.

    ``S4/O.java:19-21`` 이 ``S4/N.java:32-38`` 로 들어가고 그것은
    ``DecimalFormat("000").format(n)`` 입니다. 그래서 여정 코드 ``"1"``/``"2"``
    는 ``"001"``/``"002"`` 로 전선에 오릅니다.
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
    """구간 하나가 싣는 ``OJrny`` 값 열여섯 개. 전부 모양을 검사합니다."""
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
    """여정 전체의 ``txtStndFlg`` — C5/a.java:78-82.

    1구간은 조건 없이 플래그를 대입하고, 이후 구간은 현재 값이 아직 ``"N"`` 일
    때만 다시 계산합니다. 결과는 "한 구간이라도 입석이면 Y"이며, 그 동치가 눈에
    보이도록 앱이 쓴 대로 씁니다.
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
    """구간 하나의 ``txtStndFlg`` — S4/J.java:83-84 의 ``isStndSeat`` 그대로.

    일반실이고, 일반 좌석이 매진(``"13"``)이며, 입석 재고가 열려 있을 때
    (``"11"``) 참입니다. 이 값을 예약 요청에 넣는 호출자는 ``c5/b.java:69``
    입니다.
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
    """성인 1명·일반실 홀드 폼 — 라이브로 확인된 유일한 모양.

    :func:`build_reservation_form` 을 두 기본값 그대로 부르는 얇은 함수입니다.
    이 패키지에서 KORAIL 이 받아들이는 것이 관측된 요청은 이것 하나뿐입니다.
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
    """예약대기 홀드의 후속 폼을 만듭니다.

    ``reservationWait.ReservationWait``
    (``ReservationWaitService.java:10-12``)이며 예약대기 예매의 후반부입니다.
    ``"1102"`` 홀드가 PNR 을 만들고, 이 호출이 예약대기 화면에서 받은 두 옵션을
    그 PNR 에 기록합니다.

    * ``txtPnrNo`` — 홀드의 PNR(``ReservationWaitActivity.java:150``).
    * ``txtPsrmClChgFlg`` — ``"Y"``/``"N"``, 좌석등급 변경 동의
      (``:213``/``:219``). 관광열차에는 앱이 이 체크박스를 감추므로(``:115``)
      거기서는 ``"N"`` 뿐입니다.
    * ``txtSmsSndFlg`` — ``"Y"``/``"N"``, 배정 시 SMS 알림(``:214``/``:218``).
    * ``txtCpNo`` — 알림받을 번호. 앱은 SMS 가 켜졌을 때만 넣습니다
      (``:220-227``). 이 빌더도 그 경우 빈 문자열을 보내는 대신 키를
      생략합니다.

    ``hold`` 는 PNR 을 실은 성공한 홀드여야 합니다. 예약대기 홀드는 ``h_msg_cd``
    가 :data:`~korail_mobile_api.KORAIL_STANDBY_HOLD_MESSAGE_CODE`
    (``IRR000014``)인 것이지만(``ui/inquiry/rir/orr/a.java:222-225``) 여기서
    강제하지는 않습니다. 전선 제약이 아니라 화면 이동 조건이고, 다른 안내 코드를
    실은 홀드라도 실제 예약대기 PNR 이기 때문입니다. 앱과 똑같이 하려면 직접
    확인하면 됩니다.

    라이브 미검증.
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
    """미결제 홀드를 취소하는 폼을 만듭니다.

    ``response`` 는 방금 성공한 :class:`ReservationHoldResponse` 여야 하고
    (``strResult`` 가 ``"SUCC"``, PNR 이 있고, 여정 수가 1 이상) 그렇지 않으면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    여정 수는 상수가 아니라 **되울려 보냅니다.**
    ``DReservationConfirmActivity.java:269-278`` 은 ``txtJrnySqno="0001"`` 과
    ``hidRsvChgNo="000"`` 은 상수로 두면서
    ``setTxtJrnyCnt(reservationResponse.getH_jrny_cnt())`` 는 그대로
    통과시킵니다. 환승 홀드는 여정이 둘이므로 여기서 하나만 받아들이면 살아 있는
    환승 예약을 놓을 방법이 없어집니다.

    살아 있는 ``TicketReservation`` 응답은 여정 수를 ``"1"`` 이 아니라
    ``h_jrny_cnt="0001"`` 로 0 을 채워 보냅니다. 그래서 철자가 아니라 숫자로
    비교합니다.
    """
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
    """홀드의 ``tmpJobSqno`` 를 결제 폼에 그대로 되울립니다.

    **자릿수를 복원하지 않습니다.** 숫자로 도착한 ``tmpJobSqno`` 는 앞의 0 이
    사라진 채 전선에 오릅니다. 앱도 그렇게 하기 때문입니다 —
    ``TCReservationDao.java:28,107,183`` 은 ``tmpJobSqno`` 를 평범한 ``String``
    으로 선언하고 어디에서도 ``addZero`` 가 이 값을 건드리지 않습니다. 여기서
    0 을 채우면 앱이 보내지 않는 것을 보내게 됩니다.

    ``_echoed_reservation_change_no`` 도 같습니다. 그쪽의 ``"000"`` 기본값은
    전선 폭이 3자라는 근거가 아니라 박아 넣은 상수입니다.
    """
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
    """미결제 홀드에 대한 단일 카드 ReservationPayment 폼을 만듭니다.

    필드 구성과 상수는 근거가 확인된 앱/srtgo 의 ``pay_with_card``
    (``ktx.py:1030-1051``)와 같습니다. 카드 정산 행 하나
    (``hidStlMnsCd1="02"``)가 카드번호를 평문으로 싣습니다.

    ``hidTmpJobSqno1/2`` 와 ``hidRsvChgNo`` 는 상수가 아니라 홀드 응답을 되울린
    것입니다(``V4/b.java:39-41``, ``PaymentService.java:14``). ``hidRsvChgNo``
    는 **첫** 여정의 변경번호이며 앱도 모든 결제 호출 지점에서 같은 식을
    반복합니다. 프로토콜 상수가 아니라 예약별 상태입니다 — 취소 빌더의 고정된
    ``"000"`` 은 다른 경우입니다.

    예약 신원과 금액은 ``hold``(PNR·발권창구번호·수납금액을 실은 방금 성공한
    홀드)에서 옵니다. 이 빌더는 ``card`` 가 청구되는 카드인지 판단하지 않고 알
    수도 없습니다. ``pay_with_fake_card`` 와 ``pay_with_card`` 가 모두 여기를
    지나가고, 테스트 카드와 실제 청구를 가르는 것은 각자가 받는 consent 입니다.

    ``hidMnsStlAmt1`` 은 화면의 합계가 아니라 앱의 ``getReceivedAmount()``
    입니다(``AbstractC1269e.java:406`` → ``V4/a.java:27``). ``h_tot_prc`` 는
    UI 전용 값입니다(``PaymentActivity.java:174,497``). 할인 없는 성인 1명이면
    두 값이 같지만, 할인이나 두 번째 승객이 끼는 순간 갈라집니다.
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
    """되울리는 환불 플래그 하나를 검사하고, 없으면 앱의 기본값으로 떨어집니다.

    ``None`` 은 "호출자가 이 값을 서버에서 읽지 않았다"는 뜻이며 허용됩니다. 그
    밖에는 비어 있지 않은 문자열이어야 합니다. 빈 값은 서버가 자기 값을 되받기를
    기대하는 필드를 조용히 지워 버리기 때문입니다.
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
    """발권된 승차권의 환불(``refunds.RefundsRequest``) 폼을 만듭니다.

    필드 구성과 순서는 앱의 Retrofit 선언을 따릅니다
    (``RefundService.java:29`` / ``RefundService.smali:212``). PNR 필드는
    ``txtPnrNo``(P-n-r)입니다. srtgo 의 ``ktx.py:1082`` 는 이것을 ``txtPrnNo``
    로 쓰는데, korail2 계보의 오타이며 디컴파일된 앱에 0회 등장합니다. Retrofit
    ``@Field`` 이름은 정확히 일치해야 하므로 그대로 보내면 PNR 없는 환불이
    전송됩니다. 신원은 호출자가 :class:`PaidTicket` 로 줍니다.

    나머지 셋은 앱에서도 상수가 아닙니다.

    ``return_times_division_code``
        ``tk_ret_tms_dv_cd``. 앱은
        ``RefundCommissionResponse.tk_ret_tms_dv_cd`` 를 그대로 복사하며
        (``ticketReturn/a.smali:3149-3153``) 그 값은 출발 전 ``"21"``, 출발 후
        ``"15"`` 입니다(``I4/a.java:5-6``).
        :meth:`~korail_mobile_api.KorailClient.get_refund_commission` 의
        :attr:`ticket_return_times_division_code` 에서 읽어 넘겨야 합니다.
        그러지 않으면 출발 후 환불이 출발 전이라고 주장하게 됩니다. 기본값은
        ``"21"``.
    ``settle_mileage``
        ``h_mlg_stl``. 나머지 둘과 달리 서버 에코가 아니라 호출자의
        결정입니다. 앱은 승차권이 마일리지 정산 대상이고 사용 가능 마일리지가
        수수료를 덮을 때만 ``"Y"`` 를 보냅니다
        (``ticketReturn/a.java:185-190``). 기본값은 ``False``(``"N"``).
    ``pbp_acceptance_target_flag``
        ``pbpAcepTgtFlg``. ``RefundTicketDetailResponse.pbp_acceptance_target_flag``
        를 되울립니다(``ticketReturn/a.smali:3165-3171``). 기본값은 ``"N"``.

    승차권 상세와 수수료 조회 결과를 쥔 호출자는 셋 다 넘겨야 합니다. 앱은 그
    밖의 조합을 보내지 않습니다.
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
    """``research.dcntCrdInfo.do`` — 할인카드(N카드)를 구매합니다.

    스칼라 넷에 평평하게 편 맵 둘이며, 순서는 ``ResearchService.java:68-70`` 의
    선언 순서입니다. 두 맵은
    ``NCardReservationDao.NCardReservationRequest`` 의 ``jrnyInfo``·
    ``apdUsrInfo`` ``HashMap``(``dao/research/NCardReservationDao.java:31-32``)
    이고, 키는 그 setter 들이 쓰는 인덱스 철자입니다(``:74-124``).

    * ``jrnyInfo``: ``jrnyCnt`` 한 번, 그다음 구간마다 ``jrnyTpCd_N`` /
      ``runDt_N`` / ``trnNo_N`` / ``dptRsStnCd_N`` / ``arvRsStnCd_N``.
    * ``apdUsrInfo``: ``apdUsrCnt`` 한 번, 그다음 추가 사용자마다
      ``custMgNo_N`` / ``apdCustName_N`` / ``apdCustTeln_N``.

    ``mCustomData``(``:33,102-104``)는 일부러 없습니다. 확인 화면용
    ``LinkedHashMap`` 이고 ``executeDao``(``:180``)에 넘어가지 않아 전선에
    오르지 않습니다.

    **미검증이며, 전송된 적이 없다는 것만이 이유가 아닙니다.** v6.5.0 에서
    ``jrnyInfo``/``apdUsrInfo`` 를 채우는 호출 지점을 찾지 못했습니다. 개수와 키
    철자는 DAO 에서 나왔습니다. 1구간 카드에도 서버가 구간을 요구하는지, 1인용
    카드에서 ``apdUsrCnt`` 를 생략하는 대신 ``"0"`` 으로 보내야 하는지는 열린
    질문입니다.
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
    """``reservation.dcntCrdExtn.do`` — 할인카드의 유효기간을 연장합니다.

    ``@Query`` 일곱 개입니다(``ResearchService.java:65-66``). 공통 셋에 카드
    승차권의 네 부분 자격증명이 붙으며, 그 넷은
    ``TicketListActivity.java:1067-1072`` 이 N카드 승차권 행에서
    ``h_orgtk_wct_no`` / ``h_orgtk_ret_sale_dt`` / ``h_orgtk_sale_sqno`` /
    ``h_orgtk_ret_pwd`` 로 읽는 값입니다.

    앱은 카드가 허용할 때만 기간연장을 제시합니다 —
    ``dcnt_crd_info.h_dcnt_crd_trm_extn_psb_flg == "Y"``
    (``Y4/C0907b.java:301``,
    :attr:`~korail_mobile_api.read_models.DiscountCardOnTicket.term_extension_possible_flag`).
    그 관문은 여기 재현하지 않으므로 부르기 전에 직접 확인해야 합니다.

    **미검증.** DAO 의 응답 타입이 맨 ``BaseResponse`` 라, 성공한 연장이 무엇을
    답하는지도 비용이 얼마인지도 알 수 없습니다.
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


#: 보통의 홀드가 싣는 승객 행 키 접두사 여덟 개(``OPsg.java:8-10``).
#: N카드 홀드는 이 전부를 한 행으로 대체합니다.
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

    **평범한 예약 라우트입니다.** ``w4/a.java:93-104`` 가 보통의
    ``ReservationRequest`` 를 만들고 보통의 ``ReservationDao`` 로
    ``certification.TicketReservation``(``CertificationService.java:52-54``)에
    POST 합니다. N카드 예약 엔드포인트는 없고 N카드 승객 블록이 있을 뿐입니다.

    :func:`build_reservation_form` 의 성인 1명·일반실 폼과 다른 것은 둘입니다.

    1. **승객 블록이 카드를 실은 한 행으로 줄어듭니다.** 여덟 행이
       ``txtTotPsgCnt="1"``, ``txtCompaCnt1="1"``, ``txtPsgTpCd1="1"``,
       ``txtDiscKndCd1="153"``, ``txtCardNo_1=<card_no>`` 가 됩니다
       (``w4/a.java:96-101``). 철자가 고르지 않은 데 주의해야 합니다.
       ``OPsg.CARD_NO`` 만 뒤에 밑줄이 붙은 ``"txtCardNo_"`` 이므로
       (``OPsg.java:7-10``) 전송 키는 ``txtCardNo1`` 이 아니라 ``txtCardNo_1``
       입니다.
    2. ``txtMenuId`` 가 ``"11"`` 대신 ``"A2"`` 가 됩니다
       (``SeatAssignBookingActivity.java:159``).

    나머지는 바이트까지 같습니다. 이 빌더는 :func:`build_reservation_form` 의
    출력에서 승객 블록만 **제자리에서** 갈아 끼우므로 여정 블록, 좌석 블록,
    ``txtJobId``, ``txtStndFlg``, ``hidFreeFlg``, ``txtGdNo`` 가 라이브로 확인된
    경로가 보내는 값 그대로 같은 위치에 남습니다.

    카드 하나는 좌석 하나입니다. 앱은 여기서 승객 구성도 특실도 제시하지 않으므로
    (``w4/a.java:88,97-98``) 둘 다 매개변수가 아니라 고정값입니다.

    **전송된 적 없음.** 전적으로 APK 에서 만든 것입니다. 확인된 것은 라우트,
    위의 두 차이, 키 철자입니다. 서버가 이 폼을 받아들이는지, 카드가
    만료·소진됐을 때 무엇을 답하는지는 확인되지 않았습니다.
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
    """``certification.PriceReCalculation`` — 홀드된 PNR 의 운임을 다시 계산합니다.

    ``CertificationService.java:35-37``(``getDiscountPrice``)이며
    ``a6/C1042B.java:265-296``(``k2()``)이 만들고
    ``DiscountPriceDao.executeDao``(``DiscountPriceDao.java:118-120``)가
    보냅니다.

    **여섯 개의 평행 리스트는 좌석당 한 행이고 인덱스로 짝지어집니다.**
    ``k2()`` 는 ``DiscountPriceParams[]`` 하나를 도는 단일 루프이며 반복마다
    같은 원소의 필드 하나씩을 여섯 ``ArrayList`` 에 덧붙입니다
    (``a6/C1042B.java:275-283``, ``smali/a6.1/B.smali`` 로 확인). 다자녀
    변형(``a6/C1041A.java:57-80``)도 **같은** ``k2()`` 를 부르고 행 수가 좌석
    수와 같지 않으면 제출을 거부하므로(``:91-94``) "좌석당 한 행"은 양쪽에서
    성립합니다.

    **리스트는 인덱스 키가 아니라 반복 키로 나갑니다.** Retrofit 1.x 는
    ``Iterable`` ``@Field`` 를 순회하며 이름을 그대로 둔 채
    ``addField(name, element)`` 를 부릅니다
    (``RequestBuilder.smali:1537-1601``). 그래서 본문은
    ``psg_tp_dv_cd=..&psg_tp_dv_cd=..`` 이고 ``[]`` 도 인덱스 접미사도
    없습니다. 이 빌더가 ``list`` 값을 돌려주는 이유이며 httpx 도 같은 방식으로
    인코딩합니다.

    ``txtJobId`` 는 고정 ``"1101"``(``a6/C1042B.java:267``), ``txtPsgGridcnt``
    는 행 수입니다.

    ``hiduserYn``/``hidCustNo`` 는 비회원일 때만 전송됩니다(``:290-293``).
    회원이면 null 이고 Retrofit 이 null ``@Field`` 를 통째로 빼므로, 회원의
    폼은 키가 열넷이 아니라 열둘입니다.

    **미검증.** 여기서 만든 것이 전송된 적이 없습니다. 짝짓기와 키 철자, 반복
    키 인코딩은 APK 에서 확정했지만, ``dcnt_knd_cd1`` 이 홀드와 어긋나는 행에
    서버가 무엇을 하는지는 실제 홀드에 대고 불러 봐야 알 수 있습니다.
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


def build_cart_add_form(
    config: KorailConfig,
    request: CartAddRequest,
) -> dict[str, str]:
    """``cart.addCartList`` — 홀드된 예약을 장바구니에 담습니다.

    공통 셋 외의 필드는 ``hidPnrNo`` 하나입니다(``CartService.java:11-13``,
    ``AddCartDao.java:9-24``). DAO 의 응답 타입이 맨 ``BaseResponse`` 라 전용
    응답 데이터클래스도 파서도 없고,
    :meth:`~korail_mobile_api.client.KorailClient.add_to_cart` 는 파싱하지 않은
    봉투를 돌려줍니다.

    **라이브 확인됨.** 홀드된 PNR 이 담겼고 봉투가 ``IRZ000002`` 와 함께
    ``SUCC`` 로 돌아왔으며 그 행을 ``get_cart_list`` 로 다시 읽었습니다. 잘못된
    PNR 이 아닌 다른 이유로는 무엇을 답하는지 아직 모릅니다. 이 저장소의 어떤
    스크립트나 테스트도 이것을 보내지 않습니다.
    """
    if type(request) is not CartAddRequest:
        raise KorailProtocolError(
            "KORAIL cart request requires an exact CartAddRequest"
        )
    pnr_no = request.pnr_no
    if not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailProtocolError(
            "KORAIL cart request requires a non-empty pnr_no"
        )
    form = _common_fields(config)
    form["hidPnrNo"] = pnr_no
    return form
