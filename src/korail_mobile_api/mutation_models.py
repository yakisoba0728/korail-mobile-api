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

    각 줄은 인원 수 하나에 고정된 승객종류 코드와 할인종류 코드를 달고 있고
    (``w4/a.java:49-73``), ``OPsg`` 가 ``LinkedHashMap`` 이라
    (``OPsg.java:6``) 만드는 순서가 곧 전선 순서입니다. 아래 필드는 그
    순서로 선언돼 있습니다 — 필드, ``txtPsgTpCd``, ``txtDiscKndCd`` 순:

    * ``adult`` 어른 — ``"1"``, ``"000"``
    * ``teenager`` 청소년 — ``"1"``, ``"P11"``
    * ``child`` 어린이 — ``"3"``, ``"000"``
    * ``infant`` 동반유아 — ``"3"``, ``"321"``
    * ``senior`` 경로 — ``"1"``, ``"131"``
    * ``severe_disability`` 중증장애 — ``"1"``, ``"111"``
    * ``mild_disability`` 경증장애 — ``"1"``, ``"112"``
    * ``guide_dog`` 안내견 — ``"1"``, ``"173"``

    인원이 0 인 줄은 보내지 않습니다. 7.0.6 은 0 을 걸러 낸 뒤 남은 줄에만 1부터
    이어지는 번호를 붙입니다
    (``analysis/jadx/sources/com/korail/talk/common/define/Passengers.java:743-752``).

    ``infant``(동반유아)와 ``guide_dog``(안내견)도 :attr:`total` 에, 따라서
    ``txtTotPsgCnt`` 에 **들어갑니다**. 앱의 합계도 여덟 계수기를 그냥 더한
    것이고(``m5/c.java:330``), 그 값이 그대로 ``txtTotPsgCnt`` 로 나갑니다.

    할인이 붙은 줄에 카드 필드가 따라붙지 않습니다. ``OPsg`` 가 선언하는 카드
    필드는 ``txtCardNo_`` 하나뿐이고(``OPsg.java:7``) 그것을 쓰는 곳은 별개인
    N카드 예약 요청뿐입니다(``w4/a.java:101``). korail2 와 srtgo 가 보내는
    ``txtCardCode_``/``txtCardPw_`` 는 디컴파일된 앱 어디에도 없습니다.

    앱에 있는 규칙 둘은 여기서 강제하지 않습니다 — 동반유아에게는 함께 앉을
    어른/청소년/경로/장애가 하나 이상 필요하고(``m5/c.java:452-455``),
    안내견은 장애 승객 수보다 많을 수 없습니다(``:458-465``). 둘 다 선택기의
    경고 대화상자일 뿐 전선에 드러나지 않아서, 서버 쪽 규칙을 짐작해 막으면
    서버가 받아 줄 조합까지 거부하게 됩니다. 다만 어긴 조합은 서버가 거절할
    가능성이 높습니다.
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

        앱의 ``TOTAL_PERSON_COUNT`` 와 정확히 같습니다(``m5/c.java:330``,
        같은 내용의 ``getTotalCount()`` 가 ``:335``).
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
      호차를 그대로 보냅니다(``SeatSearchActivity.java:678``, ``:269-271``).
    * ``seat_no`` 는
      :attr:`~korail_mobile_api.models.PhysicalSeat.seat_no` 를 그대로 넘긴
      것입니다(``SeatSearchActivity.java:680``). ``seat_spec`` 이
      **아닙니다** — 그쪽은 앱이 화면에 찍는 사람용 표시("5A")이지 전선
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
    journey_sequence: str | None = None
    reservation_change_no: str | None = field(default=None, repr=False)
    departure_date: str | None = None
    departure_time: str | None = None
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
    #: ``h_ntisu_lmt_dt`` / ``h_ntisu_lmt_tm`` — 구조화된 결제 기한. 앱은 둘을
    #: 이어 붙여 ``yyyyMMddHHmmss`` 로 읽고, 미결제 예약이 언제 스스로
    #: 취소되는지 보여 줍니다(``S4/C0816p.java:64-70``,
    #: ``ReservedTicketActivity.java:356,365``).
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    total_fare: str | None = None
    #: ``h_tot_prc`` — **표시용** 합계. ``PaymentActivity.java:174`` 가
    #: ``mTotPrc`` 에 넣고, 그 값은 화면을 위해서만 되읽힙니다(``:497``).
    #: 앱이 정산하는 금액이 아닙니다.
    total_price: str | None = None
    #: 앱이 실제로 걷는 금액(``hidMnsStlAmt1``). 앱의
    #: ``getReceivedAmount()`` 와 같습니다(``PaymentActivity.java:186-199``).
    #: 예약 응답에 ``h_tot_rcvd_amt`` 가 있으면 그것이고, 없으면 앱이 하듯
    #: 좌석별 ``h_rcvd_amt`` 를 더한 값입니다.
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
        default_factory=dict[str, Any],
        repr=False,
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    image_ticket_flag: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()


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
    #: ``"24"``). 이 필드에 ``"00"`` 은 APK 어디에도 없습니다 —
    #: ``K4/h.smali:44-52`` 가 ``const-string "0"`` 으로 상수를 만들고,
    #: ``v4/a.java:288`` 도 리터럴 ``"0"`` 을 그대로 넘깁니다.
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
       ``h_orgtk_sale_dt`` 라서 헷갈리기 쉽습니다. 앱은 명확합니다 —
       ``TicketListActivity.java:965`` 는
       ``setH_orgtk_sale_dt(detail.getH_sale_dt())`` 를 하면서 창구·일련번호·
       비밀번호만 옆의 ``h_orgtk_*`` 에서 가져옵니다
       (``ticketReturn/a.java:413`` 도 같습니다). ``h_orgtk_ret_sale_dt`` 를
       원하는 것은 환불수수료 조회 쪽입니다(``ticketReturn/a.java:352``).
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
        세 개에서 가져옵니다. ``TicketListActivity.java:964-968`` 과 필드
        단위로 같습니다.
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

    ``NCardReservationDao.NCardReservationRequest``
    (``dao/research/NCardReservationDao.java:74-108``)가 구간마다 인덱스 키로
    맵에 넣고, Retrofit 이 그 맵을 폼으로 펼칩니다
    (``ResearchService.java:68-70``). 구간 하나에 항목 하나, 1~3 개입니다 —
    :data:`~korail_mobile_api.constants.KORAIL_MAX_DISCOUNT_CARD_SECTIONS`.
    """

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """N카드 2인용의 두 번째 등록 사용자(``apdUsrInfo``).

    ``NCardReservationDao.java:66-72,122-124``. 1인용 카드에서는 앱도 빈
    맵을 보내므로 폼에 필드가 하나도 붙지 않습니다.

    세 필드 모두 개인정보라 ``repr=False`` 이고, 전선 이름이
    :mod:`korail_mobile_api.redaction` 에 등록돼 있습니다.
    """

    customer_no: str = field(repr=False)
    name: str = field(repr=False)
    phone: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """할인카드를 사는 데 ``research.dcntCrdInfo.do`` 가 요구하는 전부.

    스칼라 절반은 ``w4/a.java:106-113`` 이 만듭니다 — 상품
    (``dcntCrdKndMgNo``), 로그인한 회원의 고객번호, 유효기간 시작일
    (``vlidTrmStDt``), 사용 횟수.
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

    ``TicketListActivity.java:1066-1074`` 는 넷 다 N카드 승차권 자신의 행에서
    읽습니다 — ``h_orgtk_wct_no``, ``h_orgtk_ret_sale_dt``,
    ``h_orgtk_sale_sqno``, ``h_orgtk_ret_pwd``. 다른 원표 작업이 쓰는 것과
    같은 자격증명입니다. 넷 다 ``repr=False`` 입니다.
    """

    sale_window_no: str = field(repr=False)
    sale_date: str = field(repr=False)
    sale_sequence: str = field(repr=False)
    return_password: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """``research.dcntCrdInfo.do`` 의 답. 아직 결제 전입니다.

    ``NCardReservationDao.NCardReservationResponse``
    (``dao/research/NCardReservationDao.java:127-174``).

    :attr:`lump_settlement_target_no` 를 받으려고 부르는 호출입니다. 앱은 그
    값을 곧바로 결제 화면으로 넘깁니다
    (``SectionNCardInquiryActivity.java:213-257``) — 이 응답은 정산을
    기다리는 미결제 구매이지 끝난 구매가 아닙니다.
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


@dataclass(frozen=True)
class PriceRecalculationRow:
    """운임 재계산 요청의 승객 한 줄.

    앱의 ``DiscountPriceParams``
    (``network/data/certification/DiscountPriceParams.java``) — 여섯 필드짜리
    평평한 객체이고, 보류된 여정의 좌석 하나마다 하나씩입니다. 요청 전체는
    이것의 배열이며 ``a6/C1042B.java:275-283`` 이 그것을 DAO 가 선언한 여섯
    개의 병렬 ``List`` ``@Field`` 로 흩뿌립니다. 그래서 여섯 리스트는
    **인덱스로 맞물려** 있고, 이 클래스가 그것을 다시 한 줄로 묶은 것입니다.

    앞의 세 필드는 보류된 좌석에서 그대로 베낍니다. 호출자가 고르는 값이
    아닙니다 — ``S4/D.java:176-190`` 이 ``seat_infos.seat_info[i]`` 의
    ``h_psg_tp_cd`` 와 ``h_psrm_cl_cd`` 를 그대로 읽습니다. 같은 PNR 의
    :class:`~korail_mobile_api.read_models.ReservationSeatDetail` 에서 읽으면
    됩니다.

    * :attr:`requested_discount_code`(``hidDcntKndCd``) — 결제 화면이 이
      승객에게 방금 고른 할인 종류. 없으면 ``""``. 관측된 값:
      ``"151"``/``"152"``(쿠폰·국가유공자 본인),
      ``"171"``/``"172"``(장애인·유공자 보호자), ``"321"``(동반유아),
      ``"401"``(지연할인), ``"402"``(국회의원).
    * :attr:`certificate_no`(``hidDscpNo``) — 그 할인을 뒷받침하는
      쿠폰·증명 번호(``h_cpn_no``, 또는 네 조각짜리 지연증명 반환번호).
      필요 없는 할인이면 ``""``.
    * :attr:`family_sequence_no`(``hidFmlyNo``) — 다자녀 가족 구성원의
      ``fmlySqno``. 다자녀 말고는 전부 ``""`` 이고, 비어 있지 않게 쓰는 곳은
      ``a6/C1041A.java:75`` 하나뿐입니다.

    여섯 값 모두 문자열이어야 하고 ``None`` 이면 안 됩니다. Retrofit 은
    리스트를 펼칠 때 널 원소를 **건너뛰므로**
    (``RequestBuilder.smali:1559-1571``) 한 키만 짧아지고, 그 뒤의 모든 줄이
    조용히 다시 짝지어집니다.
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

    ``a6/C1042B.java:265-296``(``k2()``)이 만드는 것이 정확히 이것입니다 —
    PNR, 고정 job id ``"1101"``, 줄 수, 여섯 개의 리스트, 그리고 **비회원일
    때만** ``hiduserYn="N"`` 과 비회원 번호.
    """

    pnr_no: str = field(repr=False)
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: ``hidCustNo``. 비회원 세션에서만 채웁니다. ``k2()`` 가 이 값이나
    #: ``hiduserYn`` 을 쓰는 경우도 그때뿐입니다(``a6/C1042B.java:290-293``).
    #: 회원이면 ``None`` 이고, 그러면 두 필드 다 전송되지 않습니다 —
    #: Retrofit 은 널 ``@Field`` 를 빼므로(``RequestBuilder.smali:1531``)
    #: 회원의 폼은 실제로 열네 개가 아니라 열두 개 키를 갖습니다.
    non_member_no: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class CartAddRequest:
    """보류된 예약의 PNR 을 장바구니에 담습니다.

    ``cart.addCartList``(``CartService.java:11-13``)가 공통 세 필드 말고
    받는 것은 ``hidPnrNo`` 하나뿐입니다. DAO 도 같은 한 필드입니다
    (``AddCartDao.java:9-24``, 바이트코드에서도 확인).
    """

    pnr_no: str = field(repr=False)
