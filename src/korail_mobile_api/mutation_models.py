# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태 변경의 입력·응답 값 객체. 생성만으로 전송하지는 않습니다. 필드·폼·raw 는 repr 을 포함해 모두 평문이므로 로그·보관 정책은 호출자가
정해야 합니다.
"""

from __future__ import annotations

from collections.abc import Mapping
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
    #: stlList 의 null 과 빈 목록을 구분해 보존합니다.
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """역발행 승차권 환불 확인의 Orgtkinfo 행."""

    pnr_no: str
    original_sale_date: str | None = None
    original_sale_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    ticket_kind_code: str | None = None
    refund_division_code: str | None = None
    refund_reason_code: str | None = None
    raw: dict[str, Any] = field(default_factory=dict[str, Any], compare=False)


def _require_every_field(
    request: StationRefundVerificationRequest | StationRefundExecutionRequest,
    step: str,
) -> None:
    """역 환불의 모든 필드는 비어 있지 않은 문자열이어야 합니다. 조합 검증 전의 입력 경계입니다."""
    for field_ in fields(request):
        value = getattr(request, field_.name)
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(
                f"KORAIL station refund {step} requires {field_.name}"
            )


@dataclass(frozen=True)
class StationRefundVerificationRequest:
    """VerifyOnlineRefundsIn 의 이름·역발행 승차권 반환 자격증명 입력."""

    customer_name: str
    return_no_1: str
    return_no_2: str
    return_no_3: str
    return_no_4: str

    def __post_init__(self) -> None:
        _require_every_field(self, "verification")


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """역발행 환불 확인의 금액·원승차권 목록."""

    received_amount: str | None = None
    refund_fee: str | None = None
    refund_amount: str | None = None
    popup_message: str | None = None
    result_message: str | None = None
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionRequest:
    """역발행 승차권의 확인 결과를 에코할 입력입니다. 생성은 전송하지 않으며, 실제 환불은 클라이언트 실행 메서드를 별도로 호출해야 합니다."""

    pnr_no: str
    original_sale_date: str
    original_sale_window_no: str
    original_sale_sequence: str
    original_return_password: str
    refund_division_code: str
    refund_reason_code: str
    ticket_kind_code: str
    customer_phone: str
    refund_amount: str
    refund_fee: str
    customer_name: str

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
        """첫 Orgtkinfo 행과 확인된 금액으로 실행 입력을 만듭니다."""
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
        # 확인 응답의 필수값 누락은 프로토콜 오류입니다. 호출자 이름·전화번호는 생성자에서 검증합니다.
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
    """환불 실행 응답의 h_ret_dv_cd 를 보존합니다."""

    refund_division_code: str | None = None


@dataclass(frozen=True)
class KorailPassengerCounts:
    """승객 종류별 인원. 코드 배정은 mutation_payloads 의 표를 사용하며, PassengerType.java:25-45 의 보호된 enum 값으로 평문을 확인한 것은
    아닙니다.

    0명 행은 빼고(Passengers.java:743-753), 배열에는 1부터 번호를 붙입니다 (NetworkService.java:15345-15366). 라이브러리의 청소년
    포함 순서는 앱 basicList 와 다릅니다 (PassengerType.java:74-84). 각 행에 종류·할인 코드가 함께 들어갑니다. 합계에는 유아·안내견도 포함되며
    상한은 9명입니다(Passengers.java:48,610-616). 일반 예약은 카드 필드를 만들지 않습니다. DTO 의 카드 키는 txtCardNo_ 하나입니다
    (TicketReservationInPassengerInfo.java:105).

    앱 선택기의 유아 동반·안내견 수 경고를 여기서 강제하지는 않습니다 (PassengersBottomSheetKt.java:21124-21185). 유아 조건은
    BABY·CHILD 외 인원 존재, 안내견 조건은 장애 승객 합계 이상으로 늘리지 않는 것입니다. 서버 허용은 별도입니다.
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
            # isinstance 가 아니라 type(...) is int. bool 이 int 의 하위 타입이고, True 는 승객 수가 아니다.
            if type(value) is not int or value < 0:
                raise KorailProtocolError(
                    f"{field_.name} must be a non-negative integer"
                )
        total = self.total
        if total < 1:
            raise KorailProtocolError(
                "a reservation must carry at least one passenger"
            )
        if total > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
            raise KorailProtocolError(
                "a reservation carries at most "
                f"{KORAIL_MAX_PASSENGERS_PER_RESERVATION} passengers, "
                f"got {total}"
            )

    @property
    def total(self) -> int:
        """``txtTotPsgCnt`` — 여덟 줄의 합. 동반유아와 안내견도 셉니다.

        7.0.6 ``Passengers.sum()`` 과 정확히 같습니다
        (``analysis/jadx/sources/com/korail/talk/common/define/Passengers.java:610-616`` —
        ``dataMap.values()`` 전체 합).
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
    """좌석지정 입력. car_no 와 식별자 seat_no 를 사용하며 표시용 seat_spec 을 보내지 마십시오. 앱도 선택 호차와 getSeatNo 를
    복사합니다(TrainSeatMapViewModel.java:2210). 선행 키: TicketReservationInSrcar.java:81-88, 후행 호차 키:
    TicketReservationInSrcarTrailing.java:86-89. 좌석 식별자·표시 구분:
    TResidualSeatsResearchOutSeat.java:172,176.
    """

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
        # isinstance 가 아니라 type(...) is int. bool 이 int 의 하위 타입이고, True 는 호차 번호가 아니다.
        # validate_seat_inventory_inputs 의 car_no 규칙과 같게 두어, 조회할 수 있었던 호차가 여기서 거절되거나 그 반대가 되는 일이 없게
        # 한다.
        if type(self.car_no) is not int or self.car_no < 1:
            raise KorailProtocolError("car_no must be a positive integer")
        seat_no = self.seat_no
        if not isinstance(seat_no, str) or not seat_no:
            raise KorailProtocolError(
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
            raise KorailProtocolError("inventory must be a SeatInventoryResponse")
        if not isinstance(seat, PhysicalSeat):
            raise KorailProtocolError("seat must be a PhysicalSeat")
        car_no = inventory.car_no
        if type(car_no) is not int:
            raise KorailProtocolError(
                "seat inventory did not echo a car number (scar_no); "
                "construct KorailSeatAssignment with an explicit car_no"
            )
        if seat not in inventory.seats:
            raise KorailProtocolError("seat does not belong to this seat inventory")
        if seat.sale_possible != "Y":
            raise KorailProtocolError(
                "seat is not marked sellable by the seat-inventory read "
                '(sale_psb_flg must be "Y")'
            )
        return cls(car_no=car_no, seat_no=seat.seat_no)


@dataclass(frozen=True)
class ReservationJourney:
    #: ``h_jrny_sqno`` — 여정 번호(``ReservationOutJrnyInfo.java:86,361``). :attr:`arrival_date` 와 정확히 같은
    #: 분포입니다: ``reserve()`` 계열 응답에서는 2026-09-22 기준 21/21 행이 이 키를 보내지 않아 항상 ``None`` 이고,
    #: ``recalculate_price`` 응답(4/4 행)과 ``get_ticket_reservation_detail`` (8/8 행)에는 들어 있습니다.
    journey_sequence: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    #: 도착일 h_arv_dt(ReservationOutJrnyInfo.java:86,305). 야간 열차는 시각만으로 날짜를 복원할 수 없습니다. 2026-09-22
    #: reserve/transfer/merge 의 21여정 관측에는 키가 없었으며 익일 도착도 포함됐습니다. 같은 예약의 get_ticket_reservation_detail
    #: 에서는 도착일을 받았고 재계산 응답에도 있었습니다. 홀드에서 항상 None 이라는 보장은 아닙니다. 없으면 상세 조회로 확인하십시오.
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    train_no: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationHoldResponse(BaseKorailResponse):
    """예약이 잡혔을 때 서버가 주는 것. 아직 결제 전입니다."""

    pnr_no: str | None = None
    journey_count: str | None = None
    window_no: str | None = None
    temporary_job_sequence_1: str | None = None
    temporary_job_sequence_2: str | None = None
    payment_flag: str | None = None
    payment_message: str | None = None
    #: ``h_pay_limit_msg``. 앱의 ``ReservationOut`` 에 선언은 돼 있으나 (``ReservationOut.java:49``,
    #: ``@SerialName`` 은 ``:408-409``) 어느 화면도 읽지 않고(``getHPayLimitMsg()`` 호출자가 DTO 밖에 0건) 실제 응답은 비어
    #: 옵니다. **결제 기한이 아닙니다** — 기한은 아래 세 필드입니다.
    payment_deadline_message: str | None = None
    #: ``h_ntisu_lmt`` — 서버가 문장으로 적어 준 기한. 예: "…까지 미결제시 승차권이 자동으로 취소됩니다."
    payment_deadline_notice: str | None = None
    #: 구조화된 결제 기한(ReservationOut.java:400,404). 앱은 두 값을 이어 붙여 표시합니다
    #: (MyReservationScreenKt.java:6008-6010, DateHelper.java:302). 날짜 패턴은 보호돼 있습니다. 문장형
    #: payment_deadline_notice 와 구분하십시오. 예약조회 선언: ReservationViewOutTrainInfo.java:464,468.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    #: h_tot_fare 선언: ReservationOut.java:444. 선언만으로 합계 의미·항상 0인 조건은 알 수 없습니다. 2026-09-22 한 계정 기록: 일반실
    #: 0, KTX 특실 1인 24,500원·2인 49,000원. 캡처 미연결로 재검산 불가. 내장 일반실 표본(BasketTicketDataKt.java:44)도 규칙을
    #: 증명하지 않습니다. 결제 금액은 이 값이 아니라 received_amount 를 사용하십시오.
    total_fare: str | None = None
    #: h_tot_prc 선언: ReservationOut.java:448. 앱 표시 합계에 사용(PayViewModel.java:11314-11318). 2026-09-22 한
    #: 계정 기록: 일반실·특실 기준액은 둘 다 54,400원, 정산액은 53,900/78,400원. 캡처 미연결이며 의미는 추정입니다. 이 값만으로 청구 금액을 정하지
    #: 마십시오.
    total_price: str | None = None
    #: 라이브러리가 계산한 정산액. 좌석 합을 먼저 구하고 선언 총액과 대조하며, 사용할 좌석 행이 없으면 선언 총액을
    #: 사용합니다(mutation_parsers._received_amount). 앱은 h_tot_rcvd_amt 를 합산합니다(ReservationOut.java:452,
    #: PayViewModel.java:11297-11307). hidMnsStlAmt1 까지의 최종 연결은 보호돼 있어 앱 계산을 그대로 재현한 것으로 보장하지 않습니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    #: 할인 합계 h_tot_dcnt_amt. 다른 예약 모델과 같은 이름을 사용합니다. 2026-09-22 기록: 홀드 11건과 재계산 2건에서
    #: prc+fare-discount=received 가 성립했습니다. 혼합 승객 163200+0-28500=134700, 특실 2인
    #: 108800+49000-1000=156800, 경로 표본 108800+0-1000=107800. 관측 사례이며 보장된 정산식은 아닙니다.
    total_discount_amount: str | None = None


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    certificate_password: str | None = None
    coupon_no: str | None = None
    management_close_date: str | None = None
    management_start_date: str | None = None
    ticket_return_no: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTicket:
    """``tk_infos.tk_info`` 의 승차권 한 장(``ReservationPaymentOutTkInfo.java``).

    행 신원(발권일련번호·판매일자·판매일련번호)과 운임·할인 금액, 그리고 세 민감 필드를 담습니다. 나머지(구간별 열차·좌석 표시용 필드 등)는 ``raw`` 로만 남습니다.
    """

    #: ``h_tk_sqno`` — 이 승차권 행의 신원 앵커.
    ticket_sequence: str | None = None
    #: ``h_sale_dt``.
    sale_date: str | None = None
    #: ``h_sale_sqno``.
    sale_sequence: str | None = None
    #: ``h_tk_ret_pwd`` — 승차권 반환 비밀번호.
    return_password: str | None = None
    #: ``h_tk_ret_no``.
    return_no: str | None = None
    #: ``h_take_name`` — 수령인 성명(PII).
    recipient_name: str | None = None
    #: ``h_disc_card_no`` — 할인카드번호.
    discount_card_no: str | None = None
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
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """``stl_infos.stl_info`` 의 정산 수단 한 줄(``ReservationPaymentOutStlInfo.java``).

    ``h_mix_stl_dv`` 가 복수 행을 암시하는 대로, 결제수단(카드/포인트 등)별로 한 행씩입니다.
    ``acnt_info``(``ReservationPaymentOutActInfo``)는 결제 게이트웨이 트랜잭션/에러 기록이라 PII 가 아니므로 ``raw`` 에만 남깁니다.
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
    settlement_card_no: str | None = None
    #: ``h_crd_corp_cd``.
    card_company_code: str | None = None
    #: ``h_crd_corp_nm``.
    card_company_name: str | None = None
    #: ``h_apv_dt``.
    approval_date: str | None = None
    #: ``h_apv_tm``.
    approval_time: str | None = None
    #: ``h_apv_no`` — 결제 승인번호.
    approval_no: str | None = None
    #: ``h_xpoint_dv``.
    point_division: str | None = None
    #: ``h_xpoint_no`` — 포인트(마일리지) 번호.
    point_no: str | None = None
    #: ``h_xpoint_apv_no`` — 포인트 승인번호.
    point_approval_no: str | None = None
    #: ``h_remnant_amt``.
    remnant_amount: str | None = None
    #: ``h_rmt_point``.
    remote_point: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """``tbl_seat_infos.tbl_seat_info`` 의 단체석 한 줄(``ReservationPaymentOutTblSeatInfo.java``).

    두 구간(다리 1/2)이 나란히 선언돼 있는 DTO 를 그대로 반영합니다. 어느 필드도 민감하지 않습니다.
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
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    image_ticket_flag: str | None = None
    #: ``h_rsv_no`` — 이번 결제로 생성/확정된 예약번호.
    reservation_no: str | None = None
    #: ``h_stl_cd_apprv_no`` — 결제 승인번호.
    settlement_approval_no: str | None = None
    #: ``h_tot_rcvd_amt`` — 청구된 총 수령액.
    total_received_amount: str | None = None
    #: ``h_stl_amt``.
    settlement_amount: str | None = None
    #: ``h_tot_stl_amt``.
    total_settlement_amount: str | None = None
    #: ``h_cust_no``.
    customer_no: str | None = None
    #: ``h_mb_crd_no`` — 회원카드번호.
    member_card_no: str | None = None
    #: ``h_buy_name`` — 구매자 성명(PII).
    buyer_name: str | None = None
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

    card_number: str
    #: 카드 비밀번호 앞 두 자리.
    card_password: str
    #: 유효기간 ``YYMM``.
    card_expire: str
    #: 개인 인증이면 생년월일 ``YYMMDD``, 법인이면 사업자번호.
    birthday: str
    #: 이 라이브러리의 일시불 값은 "0" 이며 영 채움하지 않습니다. 앱 enum 이름은 INS_0/2/3/4/5/6/12/24 이지만 code 리터럴은 보호돼 있습니다
    #: (PaymentDefine.java:152-164,185-189,207-210). INS_0 이름만으로 "0"/"00" 을 확정할 수 없습니다. 앱 기본 선택:
    #: InstallmentViewModel.java:55,94-96. 폼 접미사는 결제수단 인덱스입니다 (PaymentMethod.java:672-694;
    #: ReservationPaymentInStlInfo.java:33).
    installment: str = "0"
    #: ``hidAthnDvCd1`` — ``"J"`` 개인 / ``"S"`` 법인.
    card_type: Literal["J", "S"] = "J"

    def __post_init__(self) -> None:
        # 타입 힌트만으로 런타임 결제 입력이 검증되지는 않으므로 직접 검사합니다.
        if self.card_type not in ("J", "S"):
            raise KorailProtocolError('card_type must be "J" (personal) or "S" (corporate)')


@dataclass(frozen=True)
class PaidTicket:
    """환불 승차권 식별자. sale_date 는 원표 반환일이 아니라 현재 승차권 h_sale_dt 입니다. 앱 호출은 getSaleDt 와 원표 창구·순번·비밀번호를 함께
    전달합니다 (MyTicketDetailViewModel.java:1521, RefundTicketIn.java:154,162,364,
    TicketDetailOut.java:458,466,470,486). 반면 수수료 조회는 h_orgtk_ret_sale_dt 를 사용합니다
    (MyTicketDetailViewModel.java:277, RefundCommissionIn.java:141,149). 비슷한 필드 이름만 보고 두 날짜나 창구 키를 바꾸어
    쓰지 마십시오.
    """

    pnr_no: str
    #: **현재** 승차권의 ``h_sale_dt``. 전선 키 ``h_orgtk_sale_dt`` 를 채우지만
    #: 재발행된 승차권에서는 원표의 판매일자와 같지 않습니다 — 위 경고 참조.
    sale_date: str
    #: ``h_orgtk_wct_no`` → 전선 키 ``h_orgtk_sale_wct_no``.
    sale_window_no: str
    #: ``h_orgtk_sale_sqno``.
    sale_sequence: str
    #: ``h_orgtk_ret_pwd``.
    return_password: str
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

        판매일자는 ``h_sale_dt`` 에서, 창구·일련번호·비밀번호는 ``h_orgtk_*`` 세 개에서 가져옵니다. 7.0.6 의
        ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1521``
        과 필드 단위로 같습니다(위 :class:`PaidTicket` 경고의 인용 참조).
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
    """N카드 구매 구간. DTO 키는 밑줄로 끝나며(NCardjrny.java:96-112) 공통 평탄화가 1-기반 인덱스를
    붙입니다(NetworkService.java:15345-15366). 구간 목록 선언: NCardInfoIn.java:37, 라우트:
    NetworkApi.java:335-337. 허용 1~3구간은 라이브러리 상한입니다.
    """

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """2인용 N카드의 추가 사용자. NCardInfoIn.java:30-34 의 속성명 자체에 _1 이 포함됩니다. serializer 이름은 보호돼 전송 키는 속성명에 따른
    추정입니다.
    """

    customer_no: str
    name: str
    phone: str


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """N카드 구매 정보(NetworkApi.java:335-337). 자체 필드는 NCardInfoIn.java:29-39 참고. 명시적 별칭이 없는 필드의 전송 키는 보호된
    serializer 대신 속성명을 사용한 추정입니다.
    """

    card_kind_management_no: str
    customer_no: str
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """기간연장용 원표 식별자(MyTicketDetailViewModel.java:1049, NCardExtensionIn.java:180). 판매일은
    h_orgtk_ret_sale_dt 이므로 현재 h_sale_dt 를 쓰는 PaidTicket 환불과 다릅니다. 출처:
    TicketDetailOut.java:458,462,466,470.
    """

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """N카드 구매의 결제 전 응답(NCardInfoOut.java:25-38, NetworkApi.java:335-337). 자체 전송 키는 속성명에 따른 추정입니다.
    lump_settlement_target_no 를 받았다고 결제 완료는 아닙니다. 앱은 이를 결제 화면에 전달해 별도 정산에 사용합니다(PayRoute.java:1323,
    PayViewModel.java:6628).
    """

    #: ``lumpStlTgtNo`` — 결제가 청구할 정산 대상.
    lump_settlement_target_no: str | None = None
    #: ``dcntCrdStlTgtNo`` — N카드 자체의 정산 대상 번호.
    discount_card_settlement_target_no: str | None = None
    #: ``rcvdAmt`` — 그 정산의 금액.
    received_amount: str | None = None
    #: ``stxAmt`` — APK 필드명을 보존한 세액.
    stx_amount: str | None = None
    #: ``taxtSplAmt`` — APK 필드명을 보존한 공급 금액.
    taxt_supply_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
    #: ``dcntCrdKndMgNo`` — 서버가 실제로 등록한 할인카드 종류 관리번호. 요청의
    #: :attr:`DiscountCardPurchaseRequest.card_kind_management_no` ("요청한 값")과 다른 이름을 써서, 호출자가 "무엇을
    #: 요청했는지"와 "서버가 실제로 등록한 것"을 구분할 수 있게 합니다 (``NCardInfoOut.java:30``, ``dcntCrdStlTgtNo`` 와는 별개 필드).
    registered_card_kind_management_no: str | None = None


@dataclass(frozen=True)
class PriceRecalculationRow:
    """재계산 승객 한 줄. 기존 좌석의 종류·객실·할인 코드를 복사하고 새 할인·증명·가족번호를 별도로 둡니다 (DiscountPriceParams.java:13-39,
    PayViewModel.java:16856-16863). DTO 변환은 PayViewModel.java:6161-6165, 병렬 6목록 전송은
    NetworkService.java:9997-10043 와 NetworkApi.java:582-584 입니다.

    여섯 값은 None 아닌 문자열이어야 합니다. Retrofit 이 null 원소를 건너뛰면 병렬 목록의 인덱스가
    어긋납니다(ParameterHandler.java:18-31,252-259). 할인 미선택은 빈 문자열입니다. 2026-09-22 관측: 요청 할인 131 은
    SUCC/IRZ000008 및 응답 할인 204, 000 은 WZZ000001 이었습니다. 다른 코드들은 이 실험으로 검증하지 않았습니다. 성공 봉투는 할인 자격의 보장이
    아니며 실제 자격에 맞는 값만 사용해야 합니다. certificate_no 는 필요한 증명번호, family_sequence_no 는 다자녀 fmlySqno
    입니다(Fmly.java:145).
    """

    #: ``psg_tp_dv_cd`` ← 좌석의 ``h_psg_tp_cd``.
    passenger_type_code: str
    #: ``psrm_cl_cd`` ← 좌석의 ``h_psrm_cl_cd``.
    room_class_code: str
    #: 기존 좌석의 h_dcnt_knd_cd1 을 복사합니다(PayViewModel.java:16858). 새로 요청할 할인 hidDcntKndCd 와 다르므로 임의로 덮어쓰지
    #: 마십시오.
    discount_kind_code: str
    #: ``hidDcntKndCd`` — 지금 적용하는 할인.
    requested_discount_code: str = ""
    #: ``hidDscpNo`` — 쓸 수 있는 쿠폰·증명 번호.
    certificate_no: str = ""
    #: ``hidFmlyNo`` — 다자녀 가족 구성원 일련번호.
    family_sequence_no: str = ""


@dataclass(frozen=True)
class PriceRecalculationRequest:
    """PNR 한 건의 재계산(PayViewModel.java:6142-6171, PriceReCalculationIn.java:31-41). 비회원일 때만
    hiduserYn·hidCustNo 를 함께 넣습니다. job id·N 리터럴은 보호돼 있으며 라이브러리의 값은 라이브 기록에
    의존합니다(ReservationJobId.java:20,42-45).
    """

    pnr_no: str
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: 비회원 고객번호. 앱도 비회원일 때만 hiduserYn 과 함께 채웁니다(PayViewModel.java:6167-6168). 2026-09-23 폼 생성 확인:
    #: lang=None 은 회원 12/비회원 14개의 고유 키, lang 설정 시 13/15개입니다. 배열 반복 항목 수와 고유 키 수는 구분하십시오. FieldMap 의
    #: null 은 생략이 아니라 오류이므로 빌더가 키를 빼야 합니다 (ParameterHandler.java:252-259,276-293;
    #: NetworkApi.java:583).
    non_member_no: str | None = None
    #: ``txtPsrmClCd1`` — 여정의 객실 등급. **행의** :attr:`PriceRecalculationRow.room_class_code` (전선
    #: ``psrm_cl_cd``)와 다른 자리입니다: 저쪽은 승객 행마다 하나씩 가는 리스트이고 이쪽은 폼 전체에 하나입니다. 예약 폼도 같은 키를 여정 등급으로 씁니다
    #: (``mutation_payloads.build_reservation_form`` 의 ``txtPsrmClCd1``).
    cabin_class_code: str | None = None
    #: ``txtSeatAttCd2`` — 좌석 속성 2번 슬롯.
    seat_attribute_code_2: str | None = None
    #: ``txtSeatAttCd4`` — 좌석 속성 4번 슬롯. 예약 폼에서 **실제 좌석 속성이 들어가는 자리**가 이
    #: 번호입니다(``_seat_attribute_key(1)``), 2·5번은 거기서 ``"000"`` 으로 채워집니다. 재계산 라우트에서도 같은 역할인지는 확인하지 않았습니다
    #: — 슬롯 번호만 맞춰 두었습니다.
    seat_attribute_code_4: str | None = None
    #: ``txtSeatAttCd5`` — 좌석 속성 5번 슬롯.
    seat_attribute_code_5: str | None = None


@dataclass(frozen=True)
class CartDiscountAddition:
    """승객별 할인 추가 행. 명시적 키: PsgDiscAddInfo.java:81,85."""

    #: ``h_psg_sqno`` — 이 행이 가리키는 승객의 순번.
    passenger_sequence_no: str | None = None
    #: ``h_duty_ref_rcgn_ps_dv_cd`` — APK 필드명을 보존한 구분 코드.
    #: **뜻은 확인하지 않았습니다.** 전선 키와 이 DTO 에 있다는 것까지가
    #: 확인된 전부이고, 코드값의 의미나 가능한 값 목록은 미출처입니다.
    duty_reference_recognition_division_code: str | None = None
    raw: Mapping[str, Any] = field(
        default_factory=dict[str, Any], compare=False
    )


@dataclass(frozen=True)
class CartAddResponse(BaseKorailResponse):
    """장바구니 추가 결과. 구조: AddCartListOut.java:24-25,76 → PsgDiscAddInfos.java:81. 라이브 미검증이며 행이 없으면
    discount_additions 는 빈 튜플입니다.
    """

    #: ``psgDiscAdd_infos`` → ``psgDiscAdd_info`` 의 각 행.
    discount_additions: tuple[CartDiscountAddition, ...] = ()


@dataclass(frozen=True)
class CartAddRequest:
    """홀드 PNR 을 장바구니에 추가하는 입력. 자체 필드는 hidPnrNo 하나입니다 (AddCartListIn.java:25-30,79;
    NetworkApi.java:265-267).
    """

    pnr_no: str
