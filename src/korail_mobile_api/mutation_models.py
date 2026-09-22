# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태변경 요청이 받는 입력 타입과 그 응답 타입.

여기 있는 것은 값 객체일 뿐이라 아무것도 전송하지 않습니다. 실제로 보내려면
인증된 세션이 있는 :class:`~korail_mobile_api.client.KorailClient` 로 해당
메서드를 부르기만 하면 됩니다.

민감한 필드는 ``repr=False`` 라 객체를 찍어도 값이 보이지 않고, 전선 이름이
:mod:`korail_mobile_api.redaction` 에 등록돼 있어 페이로드가 되비칠 때도 어디서나
마스킹됩니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Literal

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError
from .models import BaseKorailResponse, PhysicalSeat, SeatInventoryResponse


if TYPE_CHECKING:
    from .read_models import RefundTicketDetailResponse


@dataclass(frozen=True)
class RefundTicketResponse(BaseKorailResponse):
    """7.0.6 환불 결과의 nullable ``stlList`` 정산 수단 코드."""

    settlement_method_codes: tuple[str, ...] = ()
    #: ``stlList: null`` and ``stlList: []`` are distinct APK responses.
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """An ``Orgtkinfo`` row returned by station-issued ticket verification."""

    pnr_no: str = field(repr=False)
    original_sale_date: str | None = field(default=None, repr=False)
    original_sale_window_no: str | None = field(default=None, repr=False)
    original_sale_sequence: str | None = field(default=None, repr=False)
    original_return_password: str | None = field(default=None, repr=False)
    ticket_kind_code: str | None = None
    refund_division_code: str | None = None
    refund_reason_code: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


def _require_every_field(
    request: StationRefundVerificationRequest | StationRefundExecutionRequest,
    step: str,
) -> None:
    """Every field of a station refund request is a required non-blank string.

    ``ValueError``, like the other request constructors here: this is the
    caller's input. A verification response that falls short is refused
    separately, as :class:`KorailProtocolError`, by
    :meth:`StationRefundExecutionRequest.from_verification`.
    """
    for field_ in fields(request):
        value = getattr(request, field_.name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"KORAIL station refund {step} requires {field_.name}"
            )


@dataclass(frozen=True)
class StationRefundVerificationRequest:
    """``VerifyOnlineRefundsIn`` name and four station-ticket return parts."""

    customer_name: str = field(repr=False)
    return_no_1: str = field(repr=False)
    return_no_2: str = field(repr=False)
    return_no_3: str = field(repr=False)
    return_no_4: str = field(repr=False)

    def __post_init__(self) -> None:
        _require_every_field(self, "verification")


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """``VerifyOnlineRefundsOut`` amounts and verified original tickets."""

    received_amount: str | None = None
    refund_fee: str | None = None
    refund_amount: str | None = None
    popup_message: str | None = field(default=None, repr=False)
    result_message: str | None = None
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionRequest:
    """``ExecuteOnlineRefundsIn`` values echoed from a verified ticket.

    This object only prepares fields. Sending is a separate call, and it
    goes out on the refund route the moment it is made.
    """

    pnr_no: str = field(repr=False)
    original_sale_date: str = field(repr=False)
    original_sale_window_no: str = field(repr=False)
    original_sale_sequence: str = field(repr=False)
    original_return_password: str = field(repr=False)
    refund_division_code: str
    refund_reason_code: str
    ticket_kind_code: str
    customer_phone: str = field(repr=False)
    refund_amount: str
    refund_fee: str
    customer_name: str = field(repr=False)

    def __post_init__(self) -> None:
        _require_every_field(self, "execution")

    @classmethod
    def from_verification(
        cls,
        verification: StationRefundVerificationResponse,
        *,
        customer_phone: str,
        customer_name: str,
    ) -> StationRefundExecutionRequest:
        """Use the APK's first verified ``Orgtkinfo`` row and quoted amounts."""
        if verification.str_result != "SUCC" or not verification.original_tickets:
            raise KorailProtocolError(
                "KORAIL station refund requires a successful verification "
                "with an original ticket"
            )
        ticket = verification.original_tickets[0]
        echoed = {
            "pnr_no": ticket.pnr_no,
            "original_sale_date": ticket.original_sale_date,
            "original_sale_window_no": ticket.original_sale_window_no,
            "original_sale_sequence": ticket.original_sale_sequence,
            "original_return_password": ticket.original_return_password,
            "refund_division_code": ticket.refund_division_code,
            "refund_reason_code": ticket.refund_reason_code,
            "ticket_kind_code": ticket.ticket_kind_code,
            "refund_amount": verification.refund_amount,
            "refund_fee": verification.refund_fee,
        }
        # A value the verification should have echoed and did not is the
        # server's answer falling short. The caller's phone and name are
        # input, and the constructor checks those.
        parts: dict[str, str] = {}
        missing: list[str] = []
        for name, value in echoed.items():
            if value and value.strip():
                parts[name] = value
            else:
                missing.append(name)
        if missing:
            raise KorailProtocolError(
                "KORAIL station refund verification is missing "
                + ", ".join(sorted(missing))
            )
        return cls(**parts, customer_phone=customer_phone, customer_name=customer_name)


@dataclass(frozen=True)
class StationRefundExecutionResponse(BaseKorailResponse):
    """``ExecuteOnlineRefundsOut.h_ret_dv_cd`` after a server call."""

    refund_division_code: str | None = None


@dataclass(frozen=True)
class KorailPassengerCounts:
    """예약 하나에 실을 승객 종류별 인원 수.

    각 줄은 인원 수 하나에 고정된 승객종류 코드와 할인종류 코드를 달고 있습니다.
    옛 인용 ``w4/a.java:49-73`` 은 6.5.0 클래스로 7.0.6 디컴파일에 없고
    (2026-09-22 확인), 7.0.6 의 대응물은
    ``analysis/jadx/sources/com/korail/talk/common/define/PassengerType.java:25-45``
    입니다 — 여덟 enum 상수(``ADULT``/``CHILD``/``BABY``/``SENIOR``/
    ``DISABILITY_SERIOUS``/``DISABILITY_MILD``/``GUIDE_DOG``/``TEENAGER``)가
    각각 ``psgTpCd`` 와 ``discKndCd`` 를 들고 있습니다. **다만 그 코드
    리터럴은 AlienGuard 로 보호돼 있습니다**(``ReqDiscount``/``ResDiscount``
    의 게터를 거치고, enum 이름 문자열마저
    ``AlienGuard1789016769018.method_name_*`` 호출입니다). 그래서 아래
    값 표는 실서버 관측에서 온 것이고 디컴파일로 대조할 수 없습니다.

    인원 맵이 ``LinkedHashMap`` 이라 만드는 순서가 곧 전선 순서입니다 —
    옛 인용 ``OPsg.java:6`` 의 ``OPsg`` 도 7.0.6 에 없고, 그 자리를
    ``Passengers.java:50``(``dataMap: Map<PassengerType, Integer>``)과
    ``Passengers.java:745``(인원 0 을 걸러 낸 뒤 남은 줄을 새
    ``LinkedHashMap`` 에 옮겨 담는 곳)이 차지합니다. 아래 필드는 그
    순서로 선언돼 있습니다 — 필드, ``txtPsgTpCd``, ``txtDiscKndCd`` 순:

    * ``adult`` 어른 — ``"1"``, ``"000"``
    * ``teenager`` 청소년 — ``"1"``, ``"P11"``
    * ``child`` 어린이 — ``"3"``, ``"000"``
    * ``infant`` 동반유아 — ``"3"``, ``"321"``
    * ``senior`` 경로 — ``"1"``, ``"131"``
    * ``severe_disability`` 중증장애 — ``"1"``, ``"111"``
    * ``mild_disability`` 경증장애 — ``"1"``, ``"112"``
    * ``guide_dog`` 안내견 — ``"1"``, ``"173"``

    인원이 0 인 줄은 보내지 않습니다. 이 주장은 7.0.6 에서 **두 곳**에 나뉘어
    있으므로 인용도 둘입니다 — 종전에는 두 주장을 모두
    ``Passengers.java:743-752`` 하나로 묶었는데, 그 범위는 필터일 뿐이고
    번호 붙이기는 그 안에 없습니다. (1) 0 걸러내기:
    ``analysis/jadx/sources/com/korail/talk/common/define/Passengers.java:743-753``
    — ``toTicketReservationInput`` 이 ``dataMap`` 을 훑어 값이 0 보다 큰
    항목만 ``LinkedHashMap`` 에 남깁니다. (2) 남은 줄에 1부터 번호 붙이기:
    ``analysis/jadx/sources/com/korail/talk/network/NetworkService.java:15345-15366``
    — ``STLibw(JsonElement, boolean)``(``:15304``, JSON→폼 평탄화)의
    ``JsonArray`` 분기가 원소 인덱스 ``i10 = i9 + 1``(``:15350``)을 내부 키
    뒤에 그대로 이어 붙입니다(``:15366``). 대괄호도 0-기반도 아닙니다.
    번호를 붙이는 쪽은 승객 목록 전용 코드가 아니라 모든 배열에 같은
    규칙을 적용하는 공통 평탄화입니다.

    참고로 7.0.6 자신의 승객 행 순서는 ``PassengerType.INSTANCE.basicList()``
    (``PassengerType.java:74-84``: ADULT, CHILD, BABY, SENIOR,
    DISABILITY_SERIOUS, DISABILITY_MILD, GUIDE_DOG)이고 아래 필드 순서와
    다릅니다. 줄마다 자기 ``txtPsgTpCd``/``txtDiscKndCd`` 를 달고 가므로 줄
    순서 자체가 계약은 아니며, 이 순서로 보내는 예약이 실서버에서 통과하는
    것은 확인돼 있습니다.

    ``infant``(동반유아)와 ``guide_dog``(안내견)도 :attr:`total` 에, 따라서
    ``txtTotPsgCnt`` 에 **들어갑니다**. 앱의 합계도 여덟 계수기를 그냥 더한
    것입니다 — 옛 인용 ``m5/c.java:330`` 은 7.0.6 에 없고, 7.0.6 에서는
    ``analysis/jadx/sources/com/korail/talk/common/define/Passengers.java:610-616``
    의 ``sum()`` 이 ``dataMap.values()`` 를 통째로 더합니다(승객 종류를
    가리지 않으므로 동반유아·안내견도 포함). 같은 파일 ``:48`` 의
    ``MAX_COUNT = 9`` 가 :data:`~korail_mobile_api.constants.KORAIL_MAX_PASSENGERS_PER_RESERVATION`
    에 대응합니다.

    할인이 붙은 줄에 카드 필드가 따라붙지 않습니다. 7.0.6 의 승객 행 DTO
    ``TicketReservationInPassengerInfo`` 는 정확히 네 필드를 선언하고
    (``txtCompaCnt``, ``txtPsgTpCd``, ``txtDiscKndCd``, ``txtCardNo_``
    — ``TicketReservationInPassengerInfo.java:105``), 카드 필드는
    ``txtCardNo_`` 하나뿐이며 그 밑줄이 이미 ``@SerialName`` 안에 있습니다.
    이 예약 폼(``_add_passenger_rows``)은 그 필드를 만들지 않고, 별개인
    N카드 예약 요청(``build_discount_card_reservation_form``)만
    ``txtCardNo_1`` 을 만듭니다(``mutation_payloads.py:1631``) — W3 finding
    11 의 접미사 없는 flattening 규칙과 같은 부류입니다. korail2 와 srtgo 가
    보내는 ``txtCardCode_``/``txtCardPw_`` 는 디컴파일된 앱 어디에도 없습니다.

    앱에 있는 규칙 둘은 여기서 강제하지 않습니다. 옛 인용
    ``m5/c.java:452-455``/``:458-465`` 는 7.0.6 에 없고, 7.0.6 에서 두 규칙은
    ``analysis/jadx/sources/com/korail/talk/ui/bottomsheet/PassengersBottomSheetKt.java:21124-21185``
    의 ``warningPassengerType(Map<PassengerType, Integer>)`` 한 함수에 있습니다:

    * ``:21132-21161`` — 동반유아(``BABY``)가 1명 이상이면서 **``BABY`` 도
      ``CHILD`` 도 아닌** 종류의 인원 합이 0 이면 ``BABY`` 를 경고로
      돌려줍니다. 즉 동반 조건은 "어른/청소년/경로/장애"가 아니라 "유아와
      어린이를 뺀 아무 종류 하나"이고, 여기에는 ``GUIDE_DOG`` 도 포함됩니다
      — 종전 설명이 열거로 좁혀 놓았던 것을 바로잡았습니다.
    * ``:21163-21182`` — 안내견(``GUIDE_DOG``)이 1명 이상이면서
      ``DISABILITY_SERIOUS`` + ``DISABILITY_MILD`` 합이 안내견 수보다 작으면
      ``GUIDE_DOG`` 을 경고로 돌려줍니다(안내견 ≤ 장애 승객 수).

    둘 다 선택기의 경고 대화상자일 뿐 전선에 드러나지 않아서, 서버 쪽 규칙을
    짐작해 막으면 서버가 받아 줄 조합까지 거부하게 됩니다. 다만 어긴 조합은
    서버가 거절할 가능성이 높습니다.
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
        # 여덟 필드 모두 인원 수다 — _require_every_field 와 같은 방식.
        for field_ in fields(self):
            value = getattr(self, field_.name)
            # isinstance 가 아니라 type(...) is int. bool 이 int 의 하위
            # 타입이고, True 는 승객 수가 아니다.
            if type(value) is not int or value < 0:
                raise ValueError(
                    f"{field_.name} must be a non-negative integer"
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
        """``txtTotPsgCnt`` — 여덟 줄의 합. 동반유아와 안내견도 셉니다.

        7.0.6 ``Passengers.sum()`` 과 정확히 같습니다
        (``analysis/jadx/sources/com/korail/talk/common/define/Passengers.java:610-616``
        — ``dataMap.values()`` 전체 합). 옛 인용이 가리켰던
        ``m5/c.java:330``/``:335`` 의 ``TOTAL_PERSON_COUNT``/
        ``getTotalCount()`` 는 6.5.0 이름이고 7.0.6 디컴파일에 없습니다.
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
    """좌석지정 예약(``txtJobId="1103"``)이 지목하는 좌석 한 자리.

    * ``car_no`` 는
      :meth:`~korail_mobile_api.client.KorailClient.get_seat_cars` 가 준
      :attr:`~korail_mobile_api.models.SeatCar.car_no`, 즉
      :meth:`~korail_mobile_api.client.KorailClient.get_seat_inventory` 를
      부를 때 넣고 응답이 되돌려 주는 그 번호입니다. 앱도 화면에 떠 있는
      호차를 그대로 보냅니다. 옛 인용 ``SeatSearchActivity.java:678``,
      ``:269-271`` 은 6.5.0 이고 7.0.6 에 그 클래스가 없습니다; 7.0.6 의
      대응 위치는
      ``analysis/jadx/sources/com/korail/talk/ui/screen/train/TrainSeatMapViewModel.java:2210``
      으로, ``buildTicketReservationIn()``(``:1989``)이
      ``new TicketReservationInSrcar(trainSeatMapSeatData.getSelectedCarNo(), …)``
      를 만듭니다 — 좌석표 화면이 선택해 둔 호차를 그대로 씁니다.
      그 필드의 전선 이름은
      ``analysis/jadx/sources/com/korail/talk/network/model/TicketReservationInSrcar.java:85-88``
      의 ``@SerialName("txtSrcarNo")`` 입니다(후속 구간용 형제 DTO
      ``TicketReservationInSrcarTrailing.java:86-89`` 는
      ``@SerialName("txtSrcarNo1_")`` — 밑줄이 이미 이름 안에 있습니다).
    * ``seat_no`` 는
      :attr:`~korail_mobile_api.models.PhysicalSeat.seat_no` 를 그대로 넘긴
      것입니다 — 같은 ``TrainSeatMapViewModel.java:2210`` 이 두 번째 인자로
      ``TResidualSeatsResearchOutSeat.getSeatNo()`` 를 넘기고, 전선 이름은
      ``TicketReservationInSrcar.java:81-84`` 의 ``@SerialName("txtSeatNo")``
      입니다(옛 인용 ``SeatSearchActivity.java:680`` 은 7.0.6 에 없습니다).
      ``seat_spec`` 이 **아닙니다** — 좌석 응답 DTO 는 둘을 따로
      선언하고(``TResidualSeatsResearchOutSeat.java:172`` ``seat_no`` /
      ``:176`` ``seat_spec``), 예약 폼이 읽는 쪽은 ``seat_no`` 입니다.
      ``seat_spec`` 은 앱이 화면에 찍는 사람용 표시("5A")이지 전선
      식별자가 아닙니다.
    """

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
        # isinstance 가 아니라 type(...) is int. bool 이 int 의 하위 타입이고,
        # True 는 호차 번호가 아니다. validate_seat_inventory_inputs 의 car_no
        # 규칙과 같게 두어, 조회할 수 있었던 호차가 여기서 거절되거나 그 반대가
        # 되는 일이 없게 한다.
        if type(self.car_no) is not int or self.car_no < 1:
            raise ValueError("car_no must be a positive integer")
        seat_no = self.seat_no
        if not isinstance(seat_no, str) or not seat_no:
            raise ValueError(
                "seat_no must be a non-empty value taken from a seat-inventory read"
            )

    @classmethod
    def from_inventory(
        cls,
        inventory: SeatInventoryResponse,
        seat: PhysicalSeat,
    ) -> KorailSeatAssignment:
        """좌석표와 그 안의 좌석 하나를 짝지어 만듭니다. 손으로 옮길 값이 없습니다."""
        if not isinstance(inventory, SeatInventoryResponse):
            raise ValueError("inventory must be a SeatInventoryResponse")
        if not isinstance(seat, PhysicalSeat):
            raise ValueError("seat must be a PhysicalSeat")
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
    #: ``h_jrny_sqno`` — 여정 번호(``ReservationOutJrnyInfo.java:86,361``).
    #: :attr:`arrival_date` 와 정확히 같은 분포입니다: ``reserve()`` 계열
    #: 응답에서는 2026-09-22 기준 21/21 행이 이 키를 보내지 않아 항상 ``None``
    #: 이고, ``recalculate_price`` 응답(4/4 행)과 ``get_ticket_reservation_detail``
    #: (8/8 행)에는 들어 있습니다.
    journey_sequence: str | None = None
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
    #: ``h_arv_dt`` — 도착일. 출발 쪽(``departure_date``)과 짝이며, 심야·익일
    #: 도착 열차에서 ``arrival_time`` 하나만으로는 날짜를 고정할 수 없어
    #: 별도 필드로 둡니다(``ReservationOutJrnyInfo.java:86,305``).
    #:
    #: **다만 홀드 응답에서는 쓸 수 없습니다.**
    #: ``certification.TicketReservation`` 은 이 키를 아예 보내지 않습니다 —
    #: 2026-09-22 에 :meth:`~korail_mobile_api.KorailClient.reserve` /
    #: :meth:`~korail_mobile_api.KorailClient.reserve_transfer` /
    #: :meth:`~korail_mobile_api.KorailClient.reserve_merge` 가 돌려준 여정 행
    #: 21 개 전부에 없었고, 여기에는 일부러 고른 최악의 경우인 KTX 083
    #: 서울→부산 ``20260926`` 22:28 출발 → 익일 01:04 도착도 포함됩니다. 그
    #: 홀드에서 얻을 수 있는 것은 ``h_dpt_dt='20260926'`` 과
    #: ``h_arv_tm='010400'`` 뿐이라 익일이라는 사실이 복원되지 않습니다. 그래서
    #: 이 클래스가 ``reserve*`` 결과로 올 때 이 필드는 **언제나** ``None`` 이고,
    #: 익일 날짜는 :meth:`~korail_mobile_api.KorailClient.get_ticket_reservation_detail`
    #: 에서 받아야 합니다 — 같은 PNR 로 물으면 ``h_arv_dt='20260927'`` 이
    #: 옵니다(2026-09-22 확인). 죽은 필드는 아닙니다: 같은 클래스를
    #: :meth:`~korail_mobile_api.KorailClient.recalculate_price` 응답에도 쓰는데
    #: 거기서는 ``h_arv_dt`` 와 ``h_jrny_sqno`` 가 둘 다 들어옵니다.
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    train_no: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationHoldResponse(BaseKorailResponse):
    """예약이 잡혔을 때 서버가 주는 것. 아직 결제 전입니다."""

    pnr_no: str | None = field(default=None, repr=False)
    journey_count: str | None = None
    window_no: str | None = field(default=None, repr=False)
    temporary_job_sequence_1: str | None = field(default=None, repr=False)
    temporary_job_sequence_2: str | None = field(default=None, repr=False)
    payment_flag: str | None = None
    payment_message: str | None = None
    #: ``h_pay_limit_msg``. 앱의 ``ReservationResponse`` 에 선언은 돼 있으나
    #: (``:22``, 게터 ``:529``) 어느 화면도 읽지 않고 실제 응답은 비어
    #: 옵니다. **결제 기한이 아닙니다** — 기한은 아래 세 필드입니다.
    payment_deadline_message: str | None = None
    #: ``h_ntisu_lmt`` — 서버가 문장으로 적어 준 기한. 예: "…까지 미결제시
    #: 승차권이 자동으로 취소됩니다."
    payment_deadline_notice: str | None = None
    #: ``h_ntisu_lmt_dt`` / ``h_ntisu_lmt_tm`` — 구조화된 결제 기한. 두 키는
    #: 홀드 응답 DTO 에 그대로 선언돼 있고
    #: (``analysis/jadx/sources/com/korail/talk/network/model/ReservationOut.java:400``
    #: ``@SerialName("h_ntisu_lmt_dt")`` / ``:404``
    #: ``@SerialName("h_ntisu_lmt_tm")``), 앱은 둘을 **이어 붙여 하나의
    #: 날짜시각 문자열로** 읽습니다 —
    #: ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/reservation/MyReservationScreenKt.java:6008``
    #: 이 ``getHNtisuLmtDt() + getHNtisuLmtTm()`` 를 만들어
    #: ``DateHelper.convertFormat(…)``(``common/helper/DateHelper.java:302``)에
    #: 넘깁니다(``:6010``). **입력 패턴 리터럴은 AlienGuard 로 보호돼 있어
    #: ``yyyyMMddHHmmss`` 라는 모양은 두 필드의 자릿수(8+6)에서 나온 추정이고
    #: 디컴파일로 확인되지 않습니다.** 화면 문구도 "자동 취소"가 아니라
    #: ``R.string.reserved_ticket_pay_deadline``
    #: ("%s까지 결제해 주세요.", ``analysis/apktool/res/values/strings.xml:3041``)
    #: 이고, 자동 취소를 말하는 쪽은 문장형 :attr:`payment_deadline_notice`
    #: (``h_ntisu_lmt``, ``ReservationOut.java:396``)입니다. 같은 두 키를 쓰는
    #: 예약조회 DTO 는 ``ReservationViewOutTrainInfo.java:464,468`` 입니다.
    #: 옛 인용 ``S4/C0816p.java:64-70`` 과 ``ReservedTicketActivity.java:356,365``
    #: 는 6.5.0 이고 7.0.6 디컴파일에 없습니다(2026-09-22 확인).
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    #: ``h_tot_fare`` — **총액이 아니라 요금(특실 차액) 합계**입니다. 좌석별
    #: ``h_seat_fare`` 의 합이며, 한국 철도의 운임/요금 이분법에서 뒤쪽입니다
    #: (``ReservationOut.java:444`` ``@SerialName("h_tot_fare")``). 일반실이면
    #: 항상 ``"00000000000"`` 입니다 — 2026-09-22 에 KTX·무궁화호·새마을호·
    #: ITX-마음·입석·예약대기·환승·병합 홀드 전부에서 0 이었고, 앱 자신의 샘플
    #: ``ReservationOut`` 도 일반실 승차권을 ``h_tot_fare='00000000000'`` /
    #: ``h_seat_fare='00000000000000'`` 로 적어 둡니다
    #: (``analysis/jadx/sources/com/korail/talk/ui/screen/basketticket/data/BasketTicketDataKt.java:44``).
    #: 0 이 아니게 되는 경우는 특실뿐입니다(같은 KTX 013 서울→부산 좌석 하나에
    #: 24,500원, 2인이면 49,000원). **받을 돈은 이 필드가 아니라
    #: :attr:`received_amount` 입니다**; 정산식은
    #: ``total_price + total_fare - total_discount_amount == received_amount``.
    total_fare: str | None = None
    #: ``h_tot_prc`` — **표시용** 합계
    #: (``analysis/jadx/sources/com/korail/talk/network/model/ReservationOut.java:448``
    #: ``@SerialName("h_tot_prc")``). 옛 인용
    #: ``PaymentActivity.java:174``/``:497`` 의 ``mTotPrc`` 는 6.5.0 이고
    #: 7.0.6 에 그 클래스가 없습니다; 7.0.6 의 대응 위치는
    #: ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:11314-11318``
    #: 로, ``initAmountData()``(``:11222``)가 이 값을 예약 목록에 걸쳐 더해
    #: 화면 표시용 금액 묶음의 한 항으로만 씁니다 — 결제 요청 필드로
    #: 흘러가는 경로는 없습니다. 구체적으로는 좌석별 ``h_seat_prc`` 의 합,
    #: 즉 **할인 전·요금 전의 운임 기준액**입니다. 그래서 같은 열차의 일반실
    #: 홀드와 특실 홀드가 이 값이 똑같이 나옵니다 — 2026-09-22 KTX 013
    #: 서울→부산에서 둘 다 ``h_tot_prc='00000054400'`` 인데 실제로 받는 돈은
    #: 53,900원과 78,400원이었습니다. 이 필드로 금액을 판단하면 특실 차액과
    #: 할인이 통째로 사라집니다.
    total_price: str | None = None
    #: 앱이 실제로 걷는 금액(``hidMnsStlAmt1``). 예약 응답에
    #: ``h_tot_rcvd_amt``(``ReservationOut.java:452``)가 있으면 그것이고,
    #: 없으면 좌석별 ``h_rcvd_amt`` 를 더한 값입니다.
    #:
    #: 옛 인용 ``PaymentActivity.java:186-199`` 의 ``getReceivedAmount()`` 는
    #: 6.5.0 이고 7.0.6 에 없습니다. 7.0.6 이 실제로 하는 일은 더 단순합니다 —
    #: ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:11303-11307``
    #: 이 ``ReservationOut.getHTotRcvdAmt()`` 를 예약 목록에 걸쳐 그냥 더합니다
    #: (여정변경 분기는 ``:11297-11301`` 에서 ``scnIndcAmt`` 를 씁니다).
    #: 좌석별 ``h_seat_prc``/``h_seat_fare`` 를 다시 더하는 코드는 7.0.6 에
    #: 없습니다(``getHSeatPrc()``/``getHSeatFare()`` 호출자 0건). 그 합계가
    #: ``hidMnsStlAmt<N>`` 로 들어가는 마지막 한 걸음은
    #: ``analysis/jadx/sources/com/korail/talk/common/helper/PaymentMethodHelper.java:113``
    #: (``getCardRequest``, ``:89``) / ``:211``(``getEasyRequest``, ``:147``)
    #: 이 **AlienGuard 로 보호된 키**로 ``Bundle`` 에서 꺼내는 값이므로
    #: 정적으로 이어 붙일 수 없습니다 — 미출처로 둡니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    #: ``h_tot_dcnt_amt`` — 할인 합계. 이 필드가 없어서 홀드 응답만으로는
    #: :attr:`total_price` 와 :attr:`received_amount` 를 맞춰 볼 수 없었고,
    #: ``recalculate_price`` 로 할인을 바꿔 놓고도 얼마가 깎였는지 ``raw`` 를
    #: 뒤지지 않으면 알 수 없었습니다. 앱 DTO 는 처음부터 선언하고 있었고
    #: (``analysis/jadx/sources/com/korail/talk/network/model/ReservationOut.java:440``
    #: ``@SerialName("h_tot_dcnt_amt")``, 합성 생성자 ``:100``), 같은
    #: ``ReservationOut`` 모양을 읽는 이 패키지의 다른 두 파서는 이미 이 키를
    #: ``total_discount_amount`` 라는 **같은 이름**으로 매핑합니다
    #: (:attr:`~korail_mobile_api.read_models.ReservationHistoryReservation.total_discount_amount`,
    #: :attr:`~korail_mobile_api.read_models.TicketReservationDetailResponse.total_discount_amount`)
    #: — 이름을 맞춘 건 한 전선 키가 패키지 안에서 두 이름을 갖지 않게 하려는
    #: 것입니다.
    #:
    #: 정산식: ``h_tot_prc + h_tot_fare - h_tot_dcnt_amt == h_tot_rcvd_amt``.
    #: 2026-09-22 에 잡은 홀드 11 건(일반실·특실 1인/2인, 무궁화호·새마을호·
    #: ITX-마음, 어른2+어린이1, 경로 1인, 환승, 병합 입석, 병합, 예약대기)
    #: 전부와 ``recalculate_price`` 응답 두 건에서 성립했습니다. 구별력이 있는
    #: 사례들: 어른2+어린이1 ``163200+0-28500=134700``, 특실 2인
    #: ``108800+49000-1000=156800``, 경로 1인 ``108800+0-1000=107800``.
    total_discount_amount: str | None = None


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    certificate_password: str | None = field(default=None, repr=False)
    coupon_no: str | None = field(default=None, repr=False)
    management_close_date: str | None = None
    management_start_date: str | None = None
    ticket_return_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTicket:
    """``tk_infos.tk_info`` 의 승차권 한 장(``ReservationPaymentOutTkInfo.java``).

    행 신원(발권일련번호·판매일자·판매일련번호)과 운임·할인 금액, 그리고 세
    민감 필드를 담습니다. 나머지(구간별 열차·좌석 표시용 필드 등)는 ``raw``
    로만 남습니다.
    """

    #: ``h_tk_sqno`` — 이 승차권 행의 신원 앵커.
    ticket_sequence: str | None = None
    #: ``h_sale_dt``.
    sale_date: str | None = None
    #: ``h_sale_sqno``.
    sale_sequence: str | None = None
    #: ``h_tk_ret_pwd`` — 승차권 반환 비밀번호. 그 자체로 반환 권한이라
    #: ``repr=False``.
    return_password: str | None = field(default=None, repr=False)
    #: ``h_tk_ret_no``. 이 파일의 :class:`ReservationPaymentCoupon` 이 같은
    #: 의미의 필드를 ``repr=False`` 로 두는 것과 맞춥니다.
    return_no: str | None = field(default=None, repr=False)
    #: ``h_take_name`` — 수령인 성명(PII).
    recipient_name: str | None = field(default=None, repr=False)
    #: ``h_disc_card_no`` — 할인카드번호.
    discount_card_no: str | None = field(default=None, repr=False)
    #: ``h_tk_prc``.
    ticket_price: str | None = None
    #: ``h_tk_fare``.
    ticket_fare: str | None = None
    #: ``h_bz5_fare_disc_amt`` — APK 필드명을 보존.
    bz5_fare_discount_amount: str | None = None
    #: ``h_bz6_fare_disc_amt`` — APK 필드명을 보존.
    bz6_fare_discount_amount: str | None = None
    #: ``h_tot_disc_amt``.
    total_discount_amount: str | None = None
    #: ``h_tot_rcvd_amt`` — 이 승차권 행의 수령액.
    total_received_amount: str | None = None
    #: ``h_std_seat_prc_fare``.
    standard_seat_price_fare: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """``stl_infos.stl_info`` 의 정산 수단 한 줄(``ReservationPaymentOutStlInfo.java``).

    ``h_mix_stl_dv`` 가 복수 행을 암시하는 대로, 결제수단(카드/포인트 등)별로
    한 행씩입니다. ``acnt_info``(``ReservationPaymentOutActInfo``)는 결제
    게이트웨이 트랜잭션/에러 기록이라 PII 가 아니므로 ``raw`` 에만 남깁니다.
    """

    #: ``h_stl_sqno``.
    settlement_sequence: str | None = None
    #: ``h_stl_tp_cd``.
    settlement_type_code: str | None = None
    #: ``h_stl_rlt``.
    settlement_result: str | None = None
    #: ``h_tr_gubun``.
    transaction_division: str | None = None
    #: ``h_crd_stl_cnt``.
    card_installment_count: str | None = None
    #: ``h_inst_month``.
    installment_months: str | None = None
    #: ``h_stl_amt``.
    settlement_amount: str | None = None
    #: ``h_stl_crd_no`` — 결제에 쓰인 카드번호.
    settlement_card_no: str | None = field(default=None, repr=False)
    #: ``h_crd_corp_cd``.
    card_company_code: str | None = None
    #: ``h_crd_corp_nm``.
    card_company_name: str | None = None
    #: ``h_apv_dt``.
    approval_date: str | None = None
    #: ``h_apv_tm``.
    approval_time: str | None = None
    #: ``h_apv_no`` — 결제 승인번호. 최상위
    #: :attr:`ReservationPaymentResponse.settlement_approval_no` 와 같은
    #: 성격이라 ``repr=False``.
    approval_no: str | None = field(default=None, repr=False)
    #: ``h_xpoint_dv``.
    point_division: str | None = None
    #: ``h_xpoint_no`` — 포인트(마일리지) 번호.
    point_no: str | None = field(default=None, repr=False)
    #: ``h_xpoint_apv_no`` — 포인트 승인번호.
    point_approval_no: str | None = field(default=None, repr=False)
    #: ``h_remnant_amt``.
    remnant_amount: str | None = None
    #: ``h_rmt_point``.
    remote_point: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """``tbl_seat_infos.tbl_seat_info`` 의 단체석 한 줄(``ReservationPaymentOutTblSeatInfo.java``).

    두 구간(다리 1/2)이 나란히 선언돼 있는 DTO 를 그대로 반영합니다. 어느
    필드도 민감하지 않습니다.
    """

    room_class_name_1: str | None = None
    car_no_1: str | None = None
    seat_no_start_1: str | None = None
    seat_no_end_1: str | None = None
    seat_count_1: str | None = None
    group_name_1: str | None = None
    room_class_name_2: str | None = None
    car_no_2: str | None = None
    seat_no_start_2: str | None = None
    seat_no_end_2: str | None = None
    seat_count_2: str | None = None
    group_name_2: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    image_ticket_flag: str | None = None
    #: ``h_rsv_no`` — 이번 결제로 생성/확정된 예약번호.
    reservation_no: str | None = None
    #: ``h_stl_cd_apprv_no`` — 결제 승인번호. 그 자체로 결제 증빙이라
    #: ``repr=False``.
    settlement_approval_no: str | None = field(default=None, repr=False)
    #: ``h_tot_rcvd_amt`` — 청구된 총 수령액.
    total_received_amount: str | None = None
    #: ``h_stl_amt``.
    settlement_amount: str | None = None
    #: ``h_tot_stl_amt``.
    total_settlement_amount: str | None = None
    #: ``h_cust_no``.
    customer_no: str | None = None
    #: ``h_mb_crd_no`` — 회원카드번호.
    member_card_no: str | None = field(default=None, repr=False)
    #: ``h_buy_name`` — 구매자 성명(PII).
    buyer_name: str | None = field(default=None, repr=False)
    #: ``h_publ_start_no``.
    publication_start_no: str | None = None
    #: ``h_publ_end_no``.
    publication_end_no: str | None = None
    #: ``h_mix_stl_dv`` — 혼합결제 구분.
    mixed_settlement_division: str | None = None
    #: ``h_cnc_fee``.
    cancellation_fee: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
    #: ``tk_infos.tk_info``.
    tickets: tuple[ReservationPaymentTicket, ...] = ()
    #: ``stl_infos.stl_info``.
    settlements: tuple[ReservationPaymentSettlement, ...] = ()
    #: ``tbl_seat_infos.tbl_seat_info``.
    table_seats: tuple[ReservationPaymentTableSeat, ...] = ()


@dataclass(frozen=True)
class CardPayment:
    """예약 결제의 카드 입력(정산코드 02)."""

    card_number: str = field(repr=False)
    #: 카드 비밀번호 앞 두 자리.
    card_password: str = field(repr=False)
    #: 유효기간 ``YYMM``.
    card_expire: str = field(repr=False)
    #: 개인 인증이면 생년월일 ``YYMMDD``, 법인이면 사업자번호.
    birthday: str = field(repr=False)
    #: ``hidIsmtMnthNum1`` — 할부 개월. 일시불은 ``"0"``, 0 **하나** 입니다.
    #: 다른 값도 자릿수를 채우지 않습니다(``"2"``, ``"3"``, ``"12"``,
    #: ``"24"``).
    #:
    #: 옛 인용 ``K4/h.smali:44-52``(``const-string "0"``)과 ``v4/a.java:288``
    #: 은 6.5.0 이고 7.0.6 에 없습니다. 7.0.6 에서 **리터럴 자체는 AlienGuard
    #: 로 보호돼 있어 읽을 수 없습니다** — 할부 개월 코드는
    #: ``analysis/jadx/sources/com/korail/talk/common/define/PaymentDefine.java:152-164``
    #: 의 ``InstallmentType`` enum 이 들고 있고(생성자 ``:185-189`` 의
    #: ``displayName``/``code`` 둘 다 보호된 문자열, 게터 ``:207-210``),
    #: 확인할 수 있는 것은 **상수 이름**뿐입니다: ``INS_0``, ``INS_2``,
    #: ``INS_3``, ``INS_4``, ``INS_5``, ``INS_6``, ``INS_12``, ``INS_24`` —
    #: 즉 자릿수를 채우지 않은 개월 수이고 ``"00"`` 을 시사하는 이름은
    #: 없습니다. 기본값이 일시불이라는 것도 이름으로만 확인됩니다
    #: (``analysis/jadx/sources/com/korail/talk/ui/screen/pay/payment/InstallmentViewModel.java:55``
    #: 생성자와 ``:94-96`` ``initState()`` 가 둘 다
    #: ``PaymentDefine.InstallmentType.INS_0`` 을 넣습니다).
    #: 폼 키에 붙는 ``1`` 은 이름의 일부가 아니라 결제수단 배열의 1-기반
    #: 인덱스입니다 —
    #: ``analysis/jadx/sources/com/korail/talk/network/model/PaymentMethod.java:672-694``
    #: 의 ``setHidIsmtMnthNum(index, value)`` 가 ``ISMT_MNTH_NUM`` 접두사에
    #: 인덱스를 이어 붙여 키를 만듭니다(``:679-688``). 값을 채우는 쪽은
    #: ``common/helper/PaymentMethodHelper.java:66``/``:632``/``:646``/``:667``
    #: (보호된 1자 리터럴)과 ``:213``/``:239``/``:255``/``:503``
    #: (``easyPayInstallmentType.getCode()``)입니다. 대응 요청 DTO 필드는
    #: ``network/model/ReservationPaymentInStlInfo.java:33``
    #: (``@SerialName`` 없음 → 전선 이름이 프로퍼티 이름과 같습니다).
    installment: str = "0"
    #: ``hidAthnDvCd1`` — ``"J"`` 개인 / ``"S"`` 법인.
    card_type: Literal["J", "S"] = "J"

    def __post_init__(self) -> None:
        # The annotation does not reach an untyped caller, and this value goes
        # into a real payment form unexamined, so it is checked here.
        if self.card_type not in ("J", "S"):
            raise ValueError('card_type must be "J" (personal) or "S" (corporate)')


@dataclass(frozen=True)
class PaidTicket:
    """환불(``refunds.RefundsRequest``)이 요구하는 발권 승차권의 신원.

    .. warning::
       :attr:`sale_date` 는 **현재** 승차권의 ``h_sale_dt`` 이지 원표의
       ``h_orgtk_ret_sale_dt`` 가 아닙니다. 이 값이 채우는 전선 키 이름이
       ``h_orgtk_sale_dt`` 라서 헷갈리기 쉽습니다. 7.0.6 도 명확합니다 —
       옛 인용 ``TicketListActivity.java:965`` 와
       ``ticketReturn/a.java:413``/``:352`` 는 6.5.0 이고 디스크에 없지만,
       같은 사실이 7.0.6 에서 한 줄로 드러납니다:

       ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1521``

           new RefundTicketIn(ticketDetailOut.getPnrNo(),
                              ticketDetailOut.getSaleDt(),
                              ticketDetailOut.getOrgtkWctNo(),
                              ticketDetailOut.getOrgtkSaleSqno(),
                              ticketDetailOut.getOrgtkRetPwd(), …)

       생성자 인자 순서는
       ``analysis/jadx/sources/com/korail/talk/network/model/RefundTicketIn.java:364``
       의 ``(txtPnrNo, hOrgtkSaleDt, hOrgtkWctNo, hOrgtkSaleSqno, …)`` 이므로
       ``h_orgtk_sale_dt``(``RefundTicketIn.java:154``)에 들어가는 값은
       **현재 승차권의 ``h_sale_dt``** (``TicketDetailOut.java:486``)이고,
       창구·일련번호·비밀번호만 옆의 ``h_orgtk_*``
       (``TicketDetailOut.java:470``/``:466``/``:458``)에서 옵니다.

       ``h_orgtk_ret_sale_dt`` 를 원하는 것은 환불수수료 조회 쪽입니다 —
       같은 파일 ``:277`` 이
       ``new RefundCommissionIn(ticketDetailOut.getOrgtkRetSaleDt(), …)`` 를
       만들고, 그 첫 필드의 전선 이름이
       ``network/model/RefundCommissionIn.java:141``
       ``@SerialName("h_orgtk_ret_sale_dt")`` 입니다. 두 DTO 는 창구 키
       철자마저 다릅니다 — 환불은 ``h_orgtk_sale_wct_no``
       (``RefundTicketIn.java:162``), 수수료는 ``h_orgtk_wct_no``
       (``RefundCommissionIn.java:149``).
    """

    pnr_no: str = field(repr=False)
    #: **현재** 승차권의 ``h_sale_dt``. 전선 키 ``h_orgtk_sale_dt`` 를 채우지만
    #: 재발행된 승차권에서는 원표의 판매일자와 같지 않습니다 — 위 경고 참조.
    sale_date: str = field(repr=False)
    #: ``h_orgtk_wct_no`` → 전선 키 ``h_orgtk_sale_wct_no``.
    sale_window_no: str = field(repr=False)
    #: ``h_orgtk_sale_sqno``.
    sale_sequence: str = field(repr=False)
    #: ``h_orgtk_ret_pwd``.
    return_password: str = field(repr=False)
    #: ``trnNo``.
    train_no: str = ""
    #: ``pbpAcepTgtFlg`` — 상세 응답의 값을 환불 요청에 그대로 되울립니다.
    pbp_acceptance_target_flag: str | None = None

    @classmethod
    def from_refund_detail(
        cls,
        detail: RefundTicketDetailResponse,
        *,
        train_no: str = "",
    ) -> PaidTicket:
        """승차권 상세에서 환불 신원을 앱과 같은 방식으로 만듭니다.

        판매일자는 ``h_sale_dt`` 에서, 창구·일련번호·비밀번호는 ``h_orgtk_*``
        세 개에서 가져옵니다. 7.0.6 의
        ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1521``
        과 필드 단위로 같습니다(위 :class:`PaidTicket` 경고의 인용 참조).
        옛 인용 ``TicketListActivity.java:964-968`` 은 6.5.0 이고 7.0.6
        디컴파일에 없습니다.
        """
        candidate_parts = {
            "pnr_no": detail.pnr_no,
            "sale_date": detail.sale_date,
            "sale_window_no": detail.original_window_no,
            "sale_sequence": detail.original_sale_sequence,
            "return_password": detail.original_return_password,
        }
        parts: dict[str, str] = {}
        missing: list[str] = []
        for name, value in candidate_parts.items():
            if value:
                parts[name] = value
            else:
                missing.append(name)
        if missing:
            raise KorailProtocolError(
                "KORAIL refund identity is incomplete; the ticket detail is "
                f"missing {', '.join(sorted(missing))}"
            )
        return cls(
            **parts,
            train_no=train_no,
            pbp_acceptance_target_flag=detail.pbp_acceptance_target_flag,
        )


@dataclass(frozen=True)
class DiscountCardSectionRequest:
    """구매하려는 할인카드의 구간 하나(``dcntCrdInfo.do`` 의 ``jrnyInfo``).

    7.0.6 의 대응 DTO 는
    ``analysis/jadx/sources/com/korail/talk/network/model/NCardjrny.java:25-34``
    이고, 다섯 필드의 전선 이름이 **이미 밑줄로 끝납니다** —
    ``@SerialName("runDt_")``, ``("trnNo_")``, ``("dptRsStnCd_")``,
    ``("arvRsStnCd_")``, ``("jrnyTpCd_")``(``:96-112``). 구간 목록은
    ``NCardInfoIn.java:37`` 의 ``jrnyList: List<NCardjrny>`` 이고, 거기에
    1-기반 인덱스를 이어 붙여 ``runDt_1`` 같은 폼 키를 만드는 것은 Retrofit
    이 아니라 그 앞단의 공통 JSON→폼 평탄화입니다
    (``analysis/jadx/sources/com/korail/talk/network/NetworkService.java:15304``
    ``STLibw``, 배열 분기 ``:15345-15366``). Retrofit 은 그렇게 만들어진 맵을
    ``@FieldMap`` 으로 받기만 합니다
    (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:335-337``
    ``postDcntCrdInfo``). 구간 하나에 항목 하나, 1~3 개입니다 —
    :data:`~korail_mobile_api.constants.KORAIL_MAX_DISCOUNT_CARD_SECTIONS`.

    옛 인용 ``dao/research/NCardReservationDao.java:74-108`` 과
    ``ResearchService.java:68-70`` 은 6.5.0 이고 7.0.6 디컴파일에
    없습니다(2026-09-22 확인).
    """

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """N카드 2인용의 두 번째 등록 사용자(``apdUsrInfo``).

    7.0.6 요청 DTO
    ``analysis/jadx/sources/com/korail/talk/network/model/NCardInfoIn.java:30-34``
    가 세 필드를 이름에 ``_1`` 을 박은 채로 선언합니다 — ``apdCustName_1``,
    ``apdCustTeln_1``, ``custMgNo_1`` (``@SerialName`` 이 없으므로 전선 이름이
    프로퍼티 이름과 같습니다). 인원 수는 같은 DTO 의 ``apdUsrCnt``
    (``:32``)입니다. 1인용 카드에서는 앱도 빈 값을 보내므로 폼에 뜻있는
    값이 붙지 않습니다.

    옛 인용 ``NCardReservationDao.java:66-72,122-124`` 는 6.5.0 이고 7.0.6
    디컴파일에 없습니다.

    세 필드 모두 개인정보라 ``repr=False`` 이고, 전선 이름이
    :mod:`korail_mobile_api.redaction` 에 등록돼 있습니다.
    """

    customer_no: str = field(repr=False)
    name: str = field(repr=False)
    phone: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """할인카드를 사는 데 ``research.dcntCrdInfo.do`` 가 요구하는 전부.

    스칼라 절반은 7.0.6 요청 DTO
    ``analysis/jadx/sources/com/korail/talk/network/model/NCardInfoIn.java:29-39``
    에 그대로 선언돼 있습니다 — 상품(``dcntCrdKndMgNo``, ``:35``), 로그인한
    회원의 고객번호(``custMgNo``, ``:33``), 유효기간 시작일
    (``vlidTrmStDt``, ``:39``), 사용 횟수(``usePsbTno``, ``:38``). 이 DTO 에는
    ``@SerialName`` 이 없으므로 전선 이름이 프로퍼티 이름과 같습니다.
    라우트는 ``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:335-337``
    (``postDcntCrdInfo`` → ``research.dcntCrdInfo.do``)입니다.

    옛 인용 ``w4/a.java:106-113`` 은 6.5.0 이고 7.0.6 디컴파일에 없습니다 —
    라우트는 같지만 필드/분기 전체가 같다는 뜻은 아닙니다.
    """

    card_kind_management_no: str
    customer_no: str = field(repr=False)
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """기간연장에 쓰는 할인카드의 네 조각짜리 승차권 자격증명.

    7.0.6 은 넷 다 승차권 상세 응답의 ``h_orgtk_*`` 네 칸에서 읽습니다 —
    ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1049``

        new NCardExtensionIn(ticketDetailOut.getOrgtkWctNo(),
                             ticketDetailOut.getOrgtkRetSaleDt(),
                             ticketDetailOut.getOrgtkSaleSqno(),
                             ticketDetailOut.getOrgtkRetPwd())

    생성자 인자 순서는
    ``analysis/jadx/sources/com/korail/talk/network/model/NCardExtensionIn.java:180``
    의 ``(saleWctNo, saleDd, saleSqno, tkRetPwd)`` 이고, 네 원본 키는
    ``TicketDetailOut.java:470``(``h_orgtk_wct_no``) /
    ``:462``(``h_orgtk_ret_sale_dt``) / ``:466``(``h_orgtk_sale_sqno``) /
    ``:458``(``h_orgtk_ret_pwd``) 입니다. 다른 원표 작업이 쓰는 것과 같은
    자격증명입니다. **판매일자만 ``h_orgtk_ret_sale_dt``** 라는 점이
    :class:`PaidTicket` (환불)과 정반대입니다. 넷 다 ``repr=False`` 입니다.

    옛 인용 ``TicketListActivity.java:1066-1074`` 는 6.5.0 이고 7.0.6
    디컴파일에 없습니다.
    """

    sale_window_no: str = field(repr=False)
    sale_date: str = field(repr=False)
    sale_sequence: str = field(repr=False)
    return_password: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """``research.dcntCrdInfo.do`` 의 답. 아직 결제 전입니다.

    7.0.6 응답 DTO 는
    ``analysis/jadx/sources/com/korail/talk/network/model/NCardInfoOut.java:25-38``
    (``CommonOut`` 상속, ``@SerialName`` 없음 → 전선 이름 = 프로퍼티 이름:
    ``dcntCrdKndMgNo``, ``dcntCrdStlTgtNo``, ``lumpStlTgtNo``, ``rcvdAmt``,
    ``stxAmt``, ``taxtSplAmt``, ``usePsbTno``, ``vlidTrmClsDt``,
    ``vlidTrmStDt``)이고, 라우트는 ``NetworkApi.java:335-337`` 입니다.
    옛 인용 ``dao/research/NCardReservationDao.java:127-174`` 는 6.5.0 이고
    7.0.6 디컴파일에 없습니다.

    :attr:`lump_settlement_target_no` 를 받으려고 부르는 호출입니다. 앱은 그
    값을 곧바로 결제로 넘깁니다 —
    ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6628``
    이 ``executePayment``(``:6596``) 안에서
    ``intgStlIn.setCart_LumpStlTgtNo(payTicketItem.getNCardData().getNCardInfoOut().getLumpStlTgtNo())``
    를 합니다(``NCardInfoOut`` 자체가 결제 화면 경로 인자로 실려 갑니다 —
    ``ui/navigation/PayRoute.java:1323`` 의 ``PayTicketNCardData``). 즉 이
    응답은 정산을 기다리는 미결제 구매이지 끝난 구매가 아닙니다. 옛 인용
    ``SectionNCardInquiryActivity.java:213-257`` 은 6.5.0 이고 7.0.6 에
    없습니다.
    """

    #: ``lumpStlTgtNo`` — 결제가 청구할 정산 대상.
    lump_settlement_target_no: str | None = field(default=None, repr=False)
    #: ``dcntCrdStlTgtNo`` — N카드 자체의 정산 대상 번호.
    discount_card_settlement_target_no: str | None = field(default=None, repr=False)
    #: ``rcvdAmt`` — 그 정산의 금액.
    received_amount: str | None = None
    #: ``stxAmt`` — APK 필드명을 보존한 세액.
    stx_amount: str | None = None
    #: ``taxtSplAmt`` — APK 필드명을 보존한 공급 금액.
    taxt_supply_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
    #: ``dcntCrdKndMgNo`` — 서버가 실제로 등록한 할인카드 종류 관리번호.
    #: 요청의 :attr:`DiscountCardPurchaseRequest.card_kind_management_no`
    #: ("요청한 값")과 다른 이름을 써서, 호출자가 "무엇을 요청했는지"와
    #: "서버가 실제로 등록한 것"을 구분할 수 있게 합니다
    #: (``NCardInfoOut.java:30``, ``dcntCrdStlTgtNo`` 와는 별개 필드).
    registered_card_kind_management_no: str | None = None


@dataclass(frozen=True)
class PriceRecalculationRow:
    """운임 재계산 요청의 승객 한 줄.

    앱의 ``DiscountPriceParams`` — 여섯 필드짜리 평평한 객체이고, 보류된
    여정의 좌석 하나마다 하나씩입니다. 클래스는 7.0.6 에도 같은 이름으로
    살아 있고 패키지만 옮겼습니다:
    ``analysis/jadx/sources/com/korail/talk/data/DiscountPriceParams.java:13-39``
    — ``psg_tp_dv_cd``, ``psrm_cl_cd``, ``dcnt_knd_cd1``, ``hidDscpNo``,
    ``hidDcntKndCd``, ``hidFmlyNo`` 여섯 필드 그대로입니다(옛 인용
    ``network/data/certification/DiscountPriceParams.java`` 의 경로는 7.0.6
    에 없습니다).

    요청 전체는 이것의 배열입니다. 흩뿌리기는 7.0.6 에서 두 걸음입니다 —
    ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6161-6165``
    가 각 ``DiscountPriceParams`` 를 직렬화 DTO
    ``PriceReCalculationInPassengerInfo``
    (``network/model/PriceReCalculationInPassengerInfo.java:31-36``, 같은 여섯
    키가 ``@SerialName`` 으로 ``:127-148``)로 바꾸고,
    ``analysis/jadx/sources/com/korail/talk/network/NetworkService.java:9997-10043``
    이 그 리스트를 여섯 번 ``map`` 해서 여섯 개의 병렬 ``List<String>`` 으로
    쪼갠 뒤 ``postPriceReCalculation`` 에 넘깁니다. 그 여섯 개가 Retrofit
    선언의 여섯 ``@Field List<String>`` 입니다
    (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:582-584``:
    ``psg_tp_dv_cd``, ``psrm_cl_cd``, ``dcnt_knd_cd1``, ``hidDscpNo``,
    ``hidDcntKndCd``, ``hidFmlyNo``). 그래서 여섯 리스트는 **인덱스로
    맞물려** 있고, 이 클래스가 그것을 다시 한 줄로 묶은 것입니다. 옛 인용
    ``a6/C1042B.java:275-283`` 은 6.5.0 이고 7.0.6 디컴파일에 없습니다.

    앞의 세 필드는 보류된 좌석에서 그대로 베낍니다. 호출자가 고르는 값이
    아닙니다 —
    ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:16856-16858``
    (``getDiscountPriceParamsListData(int)``, ``:16802``)이
    ``ReservationOutSeatInfo`` 하나에서 ``getHPsgTpCd()`` / ``getHPsrmClCd()``
    / ``getHDcntKndCd1()`` 을 그대로 읽어 세 필드에 넣습니다(같은 쌍이
    ``:5518``/``:5520`` ``applyCouponDiscount`` 에도 있습니다). 옛 인용
    ``S4/D.java:176-190`` 은 6.5.0 이고 7.0.6 에 없습니다. 같은 PNR 의
    :class:`~korail_mobile_api.read_models.ReservationSeatDetail` 에서 읽으면
    됩니다.

    * :attr:`requested_discount_code`(``hidDcntKndCd``) — 결제 화면이 이
      승객에게 방금 고른 할인 종류. 없으면 ``""``. 관측된 값:
      ``"131"``(경로), ``"151"``/``"152"``(쿠폰·국가유공자 본인),
      ``"171"``/``"172"``(장애인·유공자 보호자), ``"321"``(동반유아),
      ``"401"``(지연할인), ``"402"``(국회의원). 2026-09-22 에 실서버로 실제
      성공시켜 본 유일한 값은 ``"131"`` 이고, 아무 자격도 등록되지 않은 평범한
      회원 계정에서 ``SUCC``/``IRZ000008`` 로 통과했습니다(그 뒤 좌석은
      ``h_dcnt_knd_cd1='204'``/``'경로 할인'``). 이 목록에 ``"131"`` 이 빠져
      있었는데, 하필 그게 자격 없이 동작하는 값이라 없을 이유가 없었습니다.
      반대로 ``"000"`` 은 이 필드에 넣으면 안 됩니다 — 할인 없음을 뜻하는 값이
      아니라 ``WZZ000001``("단말기할인종류코드 입력이 잘못되었습니다")로
      거절됩니다. 할인을 고르지 않았으면 ``""`` 입니다.
    * :attr:`certificate_no`(``hidDscpNo``) — 그 할인을 뒷받침하는
      쿠폰·증명 번호(``h_cpn_no``, 또는 네 조각짜리 지연증명 반환번호).
      필요 없는 할인이면 ``""``.
    * :attr:`family_sequence_no`(``hidFmlyNo``) — 다자녀 가족 구성원의
      ``fmlySqno``. 다자녀 말고는 전부 ``""`` 이고, 7.0.6 전체에서 비어 있지
      않게 쓰는 곳도 한 줄뿐입니다 —
      ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:16863``
      의 ``discountPriceParams.setHidFmlyNo(payFmly.getFmly().getFmlySqno())``
      (출처 키는 ``network/model/Fmly.java:145``
      ``@SerialName("fmlySqno")``). 같은 메서드의 바로 위 줄들은
      ``hidDscpNo`` 에 보호된 빈 문자열을 넣습니다(``:16859``). 옛 인용
      ``a6/C1041A.java:75`` 는 6.5.0 이고 7.0.6 디컴파일에 없습니다.

    여섯 값 모두 문자열이어야 하고 ``None`` 이면 안 됩니다. Retrofit 은
    리스트를 펼칠 때 널 원소를 **건너뛰므로** 한 키만 짧아지고, 그 뒤의 모든
    줄이 조용히 다시 짝지어집니다. 근거는
    ``analysis/jadx/sources/retrofit2/ParameterHandler.java:18-31``
    (``iterable()`` 이 원소마다 같은 핸들러를 다시 호출 — 이름은 루프
    불변)과 ``:252-259``(``Field.apply`` 가 값이나 변환 결과가 ``null`` 이면
    ``addFormField`` 를 부르지 않고 그냥 돌아옵니다)입니다. 옛 인용
    ``RequestBuilder.smali:1559-1571`` 은 7.0.6
    ``analysis/apktool/smali_classes7/retrofit2/RequestBuilder.smali`` 의 총
    922 행을 넘어서는 범위여서 아무것도 가리키지 못합니다.
    """

    #: ``psg_tp_dv_cd`` ← 좌석의 ``h_psg_tp_cd``.
    passenger_type_code: str
    #: ``psrm_cl_cd`` ← 좌석의 ``h_psrm_cl_cd``.
    room_class_code: str
    #: ``dcnt_knd_cd1`` ← 좌석이 **이미 갖고 있는** ``h_dcnt_knd_cd1``, 즉 지금
    #: 보류된 예약에 붙어 있는 할인. 앱의 ``makeDiscountParams`` 가 이 값을
    #: 덮어쓰는 경우는 둘뿐이고 폼 빌더도 그것을 강제합니다 — 군장병 줄이면
    #: ``"432"``, 적용 할인이 통합 국가유공자면 ``"000"``.
    discount_kind_code: str
    #: ``hidDcntKndCd`` — 지금 적용하는 할인.
    requested_discount_code: str = ""
    #: ``hidDscpNo`` — 쓸 수 있는 쿠폰·증명 번호. 마스킹됩니다.
    certificate_no: str = field(default="", repr=False)
    #: ``hidFmlyNo`` — 다자녀 가족 구성원 일련번호. 마스킹됩니다.
    family_sequence_no: str = field(default="", repr=False)


@dataclass(frozen=True)
class PriceRecalculationRequest:
    """보류된 PNR 하나의 운임 재계산.

    7.0.6 의
    ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6142-6171``
    (``executeDiscountPrice(int, List<DiscountPriceParams>)``)이 만드는 것이
    정확히 이것입니다 — PNR(``:6150``), 고정 job id(``:6166``
    ``ReservationJobId.DEFAULT.getJobId()``), 줄 수(``:6169-6170``), 여섯 개의
    리스트가 될 행 목록(``:6161-6165``), 그리고 **비회원일 때만**
    ``hiduserYn`` 과 비회원 번호(``:6167-6168``). 요청 DTO 의 스칼라 목록은
    ``network/model/PriceReCalculationIn.java:31-41``
    (``txtJobId``, ``hidPnrNo``, ``hiduserYn``, ``hidCustNo``,
    ``txtPsgGridcnt``, ``passengerInfos``, ``txtPsrmClCd1``,
    ``txtSeatAttCd2``/``4``/``5``)입니다.

    ``"1101"`` 과 ``"N"`` 이라는 **리터럴 자체는 확인할 수 없습니다** —
    job id 는 ``common/define/ReservationJobId.java:20``(``DEFAULT``)의
    AlienGuard 로 보호된 생성자 인자이고(생성자 ``:42-45``),
    ``hiduserYn`` 에 들어가는 값도 ``PayViewModel.java:6167`` 의 보호된 1바이트
    리터럴입니다. 두 값은 실서버 관측에서 온 것입니다. 옛 인용
    ``a6/C1042B.java:265-296``(``k2()``)은 6.5.0 이고 7.0.6 에 없습니다.
    """

    pnr_no: str = field(repr=False)
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: ``hidCustNo``. 비회원 세션에서만 채웁니다. 7.0.6 도 이 값과
    #: ``hiduserYn`` 을 **둘 다 ``!userData.isLogin()`` 일 때만** 넣습니다 —
    #: ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:6167-6168``
    #: 이 로그인 상태면 두 인자에 ``null`` 을 넘깁니다(옛 인용
    #: ``a6/C1042B.java:290-293`` 은 6.5.0 이고 7.0.6 에 없습니다).
    #: 회원이면 ``None`` 이고, 그러면 두 필드 다 전송되지 않습니다 —
    #: Retrofit 은 널 ``@Field`` 를 빼므로
    #: (``analysis/jadx/sources/retrofit2/ParameterHandler.java:252-259``:
    #: 값이 ``null`` 이면 ``addFormField`` 를 부르지 않고 반환) 회원의 폼은
    #: 실제로 열네 개가 아니라 열두 개 키를 갖습니다. 옛 인용
    #: ``RequestBuilder.smali:1531`` 은 7.0.6 의 922행짜리
    #: ``retrofit2/RequestBuilder.smali`` 범위 밖입니다.
    non_member_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class CartAddRequest:
    """보류된 예약의 PNR 을 장바구니에 담습니다.

    ``cart.addCartList``
    (``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:265-267``
    ``postAddCartList(@FieldMap …)``)가 공통 필드 말고 받는 것은
    ``hidPnrNo`` 하나뿐입니다 — 요청 DTO
    ``analysis/jadx/sources/com/korail/talk/network/model/AddCartListIn.java:25-30``
    이 ``CommonIn`` 을 상속하고 자기 필드로는 ``hidPnrNo`` 하나만 선언하며,
    그 전선 이름이 ``:79`` 의 ``@SerialName("hidPnrNo")`` 입니다
    (``CommonIn`` 쪽은 ``Device``/``Version``/``Key`` 와 선택적 ``lang``).
    옛 인용 ``CartService.java:11-13`` 과 ``AddCartDao.java:9-24`` 는 6.5.0
    이고 7.0.6 디컴파일에 없습니다 — 라우트는 같지만 그것이 필드 전체
    동일성을 뜻하지는 않으므로, 위 7.0.6 DTO 로 다시 세었습니다.
    """

    pnr_no: str = field(repr=False)
