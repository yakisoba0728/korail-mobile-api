"""상태변경 요청이 받는 입력 타입과 그 응답 타입.

여기 있는 것은 값 객체일 뿐이라 아무것도 전송하지 않습니다. 실제로 보내려면
:class:`~korail_mobile_api.consent.MutationConsent` 로 범주를 열고
``dry_run=False`` 로 꺼야 합니다 — 그 규칙은
:mod:`korail_mobile_api.consent` 에 있습니다.

민감한 필드는 ``repr=False`` 라 객체를 찍어도 값이 보이지 않고, 전선 이름이
:mod:`korail_mobile_api.redaction` 에 등록돼 있어
:class:`~korail_mobile_api.consent.MutationPreview` 에서도 마스킹됩니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError
from .models import BaseKorailResponse, PhysicalSeat, SeatInventoryResponse


if TYPE_CHECKING:
    from .read_models import RefundTicketDetailResponse


@dataclass(frozen=True)
class KorailPassengerCounts:
    """예약 하나에 실을 승객 종류별 인원 수.

    (``w4/a.java:49-73``), ``OPsg`` 가 ``LinkedHashMap`` 이라

    (``OPsg.java:6``) 만드는 순서가 곧 전선 순서입니다. 아래 필드는 그

    것이고(``m5/c.java:330``), 그 값이 그대로 ``txtTotPsgCnt`` 로 나갑니다.

    필드는 ``txtCardNo_`` 하나뿐이고(``OPsg.java:7``) 그것을 쓰는 곳은 별개인

    N카드 예약 요청뿐입니다(``w4/a.java:101``). korail2 와 srtgo 가 보내는

    어른/청소년/경로/장애가 하나 이상 필요하고(``m5/c.java:452-455``),
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
        for name in (
            "adult",
            "teenager",
            "child",
            "infant",
            "senior",
            "severe_disability",
            "mild_disability",
            "guide_dog",
        ):
            value = getattr(self, name)
            # isinstance 가 아니라 type(...) is int. bool 이 int 의 하위
            # 타입이고, True 는 승객 수가 아니다.
            if type(value) is not int or value < 0:
                raise ValueError(
                    f"{name} must be a non-negative integer"
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

    호차를 그대로 보냅니다(``SeatSearchActivity.java:678``, ``:269-271``).

    것입니다(``SeatSearchActivity.java:680``). ``seat_spec`` 이

    **아닙니다** — 그쪽은 앱이 화면에 찍는 사람용 표시("5A")이지 전선
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
        if (
            not isinstance(seat_no, str)
            or not seat_no
            or not seat_no.isascii()
            or any(character <= " " or character == "\x7f" for character in seat_no)
        ):
            raise ValueError(
                "seat_no must be a non-empty printable ASCII value taken from "
                "a seat-inventory read"
            )

    @classmethod
    def from_inventory(
        cls,
        inventory: SeatInventoryResponse,
        seat: PhysicalSeat,
    ) -> KorailSeatAssignment:
        """좌석표와 그 안의 좌석 하나를 짝지어 만듭니다. 손으로 옮길 값이 없습니다."""
        if type(inventory) is not SeatInventoryResponse:
            raise ValueError(
                "inventory must be an exact SeatInventoryResponse"
            )
        if type(seat) is not PhysicalSeat:
            raise ValueError("seat must be an exact PhysicalSeat")
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
    departure_station_code: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(
        default_factory=dict,
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
    payment_message: str | None = field(default=None, repr=False)
    #: ``h_pay_limit_msg``. 앱의 ``ReservationResponse`` 에 선언은 돼 있으나
    #: (``:22``, 게터 ``:529``) 어느 화면도 읽지 않고 실제 응답은 비어
    #: 옵니다. **결제 기한이 아닙니다** — 기한은 아래 세 필드입니다.
    payment_deadline_message: str | None = field(default=None, repr=False)
    #: ``h_ntisu_lmt`` — 서버가 문장으로 적어 준 기한. 예: "…까지 미결제시
    #: 승차권이 자동으로 취소됩니다."
    payment_deadline_notice: str | None = field(default=None, repr=False)
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
        default_factory=dict,
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
    card_type: str = "J"


@dataclass(frozen=True)
class PaidTicket:
    """환불(``refunds.RefundsRequest``)이 요구하는 발권 승차권의 신원.

    ``TicketListActivity.java:965`` 는

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

    @classmethod
    def from_refund_detail(
        cls,
        detail: RefundTicketDetailResponse,
        *,
        train_no: str = "",
    ) -> PaidTicket:
        """승차권 상세에서 환불 신원을 앱과 같은 방식으로 만듭니다.

        세 개에서 가져옵니다. ``TicketListActivity.java:964-968`` 과 필드
        """
        parts = {
            "pnr_no": detail.pnr_no,
            "sale_date": detail.sale_date,
            "sale_window_no": detail.original_window_no,
            "sale_sequence": detail.original_sale_sequence,
            "return_password": detail.original_return_password,
        }
        missing = [name for name, value in parts.items() if not value]
        if missing:
            raise KorailProtocolError(
                "KORAIL refund identity is incomplete; the ticket detail is "
                f"missing {', '.join(sorted(missing))}"
            )
        return cls(train_no=train_no, **parts)  # type: ignore[arg-type]


@dataclass(frozen=True)
class DiscountCardSectionRequest:
    """구매하려는 할인카드의 구간 하나(``dcntCrdInfo.do`` 의 ``jrnyInfo``).

    (``dao/research/NCardReservationDao.java:74-108``)가 구간마다 인덱스 키로

    (``ResearchService.java:68-70``). 구간 하나에 항목 하나, 1~3 개입니다 —
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

    세 필드 모두 개인정보라 ``repr=False`` 이고 미리보기에서도 마스킹됩니다.
    """

    customer_no: str = field(repr=False)
    name: str = field(repr=False)
    phone: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """할인카드를 사는 데 ``research.dcntCrdInfo.do`` 가 요구하는 전부.

    스칼라 절반은 ``w4/a.java:106-113`` 이 만듭니다 — 상품
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
    """

    sale_window_no: str = field(repr=False)
    sale_date: str = field(repr=False)
    sale_sequence: str = field(repr=False)
    return_password: str = field(repr=False)


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """``research.dcntCrdInfo.do`` 의 답. 아직 결제 전입니다.

    (``dao/research/NCardReservationDao.java:127-174``).

    (``SectionNCardInquiryActivity.java:213-257``) — 이 응답은 정산을
    """

    h_msg_txt: str | None = field(default=None, repr=False)
    #: ``lumpStlTgtNo`` — 결제가 청구할 정산 대상.
    lump_settlement_target_no: str | None = field(default=None, repr=False)
    #: ``rcvdAmt`` — 그 정산의 금액.
    received_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None


@dataclass(frozen=True)
class PriceRecalculationRow:
    """운임 재계산 요청의 승객 한 줄.

    이것의 배열이며 ``a6/C1042B.java:275-283`` 이 그것을 DAO 가 선언한 여섯

    **인덱스로 맞물려** 있고, 이 클래스가 그것을 다시 한 줄로 묶은 것입니다.

    아닙니다 — ``S4/D.java:176-190`` 이 ``seat_infos.seat_info[i]`` 의

    ``a6/C1041A.java:75`` 하나뿐입니다.

    (``RequestBuilder.smali:1559-1571``) 한 키만 짧아지고, 그 뒤의 모든 줄이
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

    (``AddCartDao.java:9-24``, 바이트코드에서도 확인).
    """

    pnr_no: str = field(repr=False)
