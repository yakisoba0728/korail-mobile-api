# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예약·결제·환불 등 상태 변경의 입력과 응답 모델을 제공합니다. 모델 생성은 전송하지 않습니다. 전송 키 대응은 mutation_payloads·mutation_parsers를 따릅니다.
필드·폼·repr·raw는 마스킹하지 않으므로 개인정보·카드정보·반환 비밀번호의 기록과 노출에 주의하십시오."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Any, Literal

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError
from .models import BaseKorailResponse, PhysicalSeat, ReservationPassengerInfo, SeatInventoryResponse

if TYPE_CHECKING:
    from .read_models import RefundTicketDetailResponse


@dataclass(frozen=True)
class RefundTicketResponse(BaseKorailResponse):
    """승차권 환불 결과의 정산수단 코드를 담습니다. ``stlList`` 는 필수이면서 null 일 수 있습니다(RefundTicketOut.java:48-53)."""

    settlement_method_codes: tuple[str, ...] = ()
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """역발행 환불 확인에 포함된 원승차권 한 행을 담습니다."""

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
            raise KorailProtocolError(f"KORAIL station refund {step} requires {field_.name}")


@dataclass(frozen=True)
class StationRefundVerificationRequest:
    """역발행 승차권 환불 확인에 필요한 이름과 반환 자격증명을 구성합니다."""

    customer_name: str
    return_no_1: str
    return_no_2: str
    return_no_3: str
    return_no_4: str

    def __post_init__(self) -> None:
        _require_every_field(self, "verification")


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """역발행 승차권 환불 확인의 금액과 원표 목록을 담습니다."""

    received_amount: str | None = None
    refund_fee: str | None = None
    refund_amount: str | None = None
    popup_message: str | None = None
    result_message: str | None = None
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionRequest:
    """역발행 승차권 환불 확인 결과를 재사용할 실행 입력을 구성합니다. 생성은 전송하지 않으며, 실제 환불은 클라이언트 실행 메서드를 별도로 호출해야 합니다."""

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
                "KORAIL station refund requires a successful verification with an original ticket"
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
                "KORAIL station refund verification is missing " + ", ".join(sorted(missing))
            )
        return cls(**parts, customer_phone=customer_phone, customer_name=customer_name)


@dataclass(frozen=True)
class StationRefundExecutionResponse(BaseKorailResponse):
    """역발행 승차권의 실제 환불 실행 결과를 담습니다."""

    refund_division_code: str | None = None


@dataclass(frozen=True)
class KorailPassengerCounts:
    """승객 종류별 예약 인원을 구성합니다. 코드 표는 mutation_payloads 를 따르며 PassengerType.java:25-45 의 보호된 enum 평문은 미확인입니다.

    0명 행은 생략(Passengers.java:743-753), 배열 번호는 1부터 시작합니다(NetworkService.java:15345-15366). 청소년 포함 순서는 앱 basicList
    와 다릅니다(PassengerType.java:74-84). 유아·안내견 포함 합계 상한은 9명입니다(Passengers.java:48,610-616). 일반 예약은 카드 필드를 만들지 않으며
    DTO 카드 키는 txtCardNo_ 하나입니다(TicketReservationInPassengerInfo.java:105).

    앱 선택기의 유아 동반(유아·어린이 외 인원 필요)·안내견 수(장애 승객 합계 이하) 조건은 이 객체가 아니라 예약 폼 빌더가 검사합니다
    (PassengersBottomSheetKt.java:21124-21185). 서버 수용은 별도입니다."""

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
                raise KorailProtocolError(f"{field_.name} must be a non-negative integer")
        total = self.total
        if total < 1:
            raise KorailProtocolError("a reservation must carry at least one passenger")
        if total > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
            raise KorailProtocolError(
                f"a reservation carries at most {KORAIL_MAX_PASSENGERS_PER_RESERVATION} passengers, got {total}"
            )

    @property
    def total(self) -> int:
        """유아·안내견을 포함한 전체 승객 수를 반환합니다. 앱 근거: Passengers.java:610-616."""
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
    """호차 번호와 좌석 식별자로 지정 좌석 입력을 구성합니다. car_no 와 식별자 seat_no 를 사용하며 표시용 seat_spec 을 보내지 마십시오. 앱도 선택 호차와 getSeatNo
    를 복사합니다(TrainSeatMapViewModel.java:2210). 선행 키: TicketReservationInSrcar.java:81-88, 후행 호차 키:
    TicketReservationInSrcarTrailing.java:86-89. 좌석 식별자·표시 구분: TResidualSeatsResearchOutSeat.java:172,176."""

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
        # bool 을 배제하고 validate_seat_inventory_inputs 와 같은 car_no 범위를 검사합니다.
        if type(self.car_no) is not int or self.car_no < 1:
            raise KorailProtocolError("car_no must be a positive integer")
        seat_no = self.seat_no
        if not isinstance(seat_no, str) or not seat_no:
            raise KorailProtocolError("seat_no must be a non-empty value taken from a seat-inventory read")

    @classmethod
    def from_inventory(
        cls,
        inventory: SeatInventoryResponse,
        seat: PhysicalSeat,
    ) -> KorailSeatAssignment:
        """재고 응답과 판매 가능한 좌석으로 좌석지정 입력을 만듭니다. inventory.car_no가 없으면 car_no를 명시해 직접 생성하십시오."""
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
                'seat is not marked sellable by the seat-inventory read (sale_psb_flg must be "Y")'
            )
        return cls(car_no=car_no, seat_no=seat.seat_no)


@dataclass(frozen=True)
class ReservationJourney:
    """예약된 여정 한 개의 열차·구간·변경 식별자를 담습니다."""

    #: 여정 순번은 h_jrny_sqno입니다(ReservationOutJrnyInfo.java:86,361). 2026-09-22: 예약 생성 응답 21/21행에는 없고 재계산 4/4행·예약
    #: 상세 8/8행에는 있었습니다. 이 관측이 모든 예약 생성 응답에서 None임을 보장하지는 않습니다.
    journey_sequence: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    #: 도착일 h_arv_dt(ReservationOutJrnyInfo.java:86,305). 야간 열차는 시각만으로 날짜를 복원할 수 없습니다. 2026-09-22
    #: reserve/transfer/merge 의 21여정 관측에는 키가 없었으며 익일 도착도 포함됐습니다. 같은 예약의 get_ticket_reservation_detail 에서는 도착일을
    #: 받았고 재계산 응답에도 있었습니다. 홀드에서 항상 None 이라는 보장은 아닙니다. 없으면 상세 조회로 확인하십시오.
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
    """미결제 예약 요청의 결과와 결제 기한·금액을 담습니다. 이 객체만으로 실제 예약 성공을 보장하지 않으므로 응답 상태를 확인하십시오."""

    pnr_no: str | None = None
    journey_count: str | None = None
    window_no: str | None = None
    temporary_job_sequence_1: str | None = None
    temporary_job_sequence_2: str | None = None
    payment_flag: str | None = None
    payment_message: str | None = None
    #: h_pay_limit_msg는 결제 기한 필드가 아닙니다(ReservationOut.java:49,408-409). 기한은
    #: payment_deadline_notice·payment_deadline_date·payment_deadline_time을 확인하십시오.
    payment_deadline_message: str | None = None
    #: ``h_ntisu_lmt`` — 서버가 문장으로 적어 준 기한. 예: "…까지 미결제시 승차권이 자동으로 취소됩니다."
    payment_deadline_notice: str | None = None
    #: 구조화된 결제 기한(ReservationOut.java:400,404). 앱은 두 값을 이어 붙여 표시합니다 (MyReservationScreenKt.java:6008-6010,
    #: DateHelper.java:302). 날짜 패턴은 보호돼 있습니다. 문장형 payment_deadline_notice 와 구분하십시오. 예약조회 선언:
    #: ReservationViewOutTrainInfo.java:464,468.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    #: h_tot_fare는 선언됐지만 일반적인 의미는 미확인입니다(ReservationOut.java:444). 2026-09-22 일반실은 0원, 특실은 1인 24,500원·2인
    #: 49,000원이었습니다. 내장 표본(BasketTicketDataKt.java:44)은 일반식의 증거가 아니며 결제에는 received_amount를 사용하십시오.
    total_fare: str | None = None
    #: h_tot_prc는 앱의 표시 합계에 쓰입니다(ReservationOut.java:448; PayViewModel.java:11314-11318). 2026-09-22: 일반실·특실
    #: 기준액은 54,400원, 정산액은 53,900/78,400원이었습니다. 이 값만으로 청구 금액을 정하지 마십시오.
    total_price: str | None = None
    #: 라이브러리가 계산한 정산액. 좌석 합을 먼저 구하고 선언 총액과 대조하며, 사용할 좌석 행이 없으면 선언 총액을 사용합니다(mutation_parsers._received_amount).
    #: 앱은 h_tot_rcvd_amt 를 합산합니다(ReservationOut.java:452, PayViewModel.java:11297-11307). hidMnsStlAmt1 까지의 최종
    #: 연결은 보호돼 있어 앱 계산을 그대로 재현한 것으로 보장하지 않습니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    #: 2026-09-22 홀드 11건·재계산 2건에서 prc+fare-discount=received가 성립했습니다. 표본은 혼합 승객 163200+0-28500=134700, 특실 2인
    #: 108800+49000-1000=156800, 경로 108800+0-1000=107800이며 일반적으로 보장되는 정산식은 아닙니다.
    total_discount_amount: str | None = None
    #: ReservationOut의 추가 스칼라는 _parsing.RESERVATION_OUT_EXTRA_FIELDS의 대응표를 따릅니다.
    customer_management_no: str | None = None
    mandatory_message: str | None = None
    additional_service_flag: str | None = None
    disability_certificate_number: str | None = None
    pre_settlement_target_flag: str | None = None
    family_info_confirm_flag: str | None = None
    special_room_fare: str | None = None
    issue_possible_date: str | None = None
    issue_possible_time: str | None = None
    passengers: tuple[ReservationPassengerInfo, ...] = ()
    #: 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다(TrainScheduleViewModel.java:5096-5101;
    #: ReservationWaitViewModel.java:1155-1160). reserve·reserve_transfer 가 STANDBY 홀드에 False 를 넣고
    #: pay_with_card 는 전송 전에 거절합니다. 병합 첫 홀드는 앱의 병합 화면에서도 결제할 수 있어 True 입니다
    #: (ReservationMergeViewModel.java:2094-2107).
    payable: bool = True
    #: recalculate_price(add_to_cart=True) 가 이어서 보낸 장바구니 추가의 응답입니다. FAIL 이어도 그대로 담깁니다. 그 밖에는 None.
    cart_addition: CartAddResponse | None = None


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    """결제 결과에 포함된 쿠폰 정보를 담습니다."""

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
    """결제로 발권된 승차권 한 장의 식별자와 반환 자격증명을 담습니다. 앱 근거: ReservationPaymentOutTkInfo.java. 타입화한 신원·운임·할인 외 필드는 raw 에
    남으며 민감정보 경고는 모듈 설명을 따릅니다."""

    ticket_sequence: str | None = None
    sale_date: str | None = None
    sale_sequence: str | None = None
    #: ``h_tk_ret_pwd`` — 승차권 반환 비밀번호.
    return_password: str | None = None
    return_no: str | None = None
    #: h_take_name은 수령인 성명이므로 로그·repr 노출에 주의하십시오.
    recipient_name: str | None = None
    #: ``h_disc_card_no`` — 할인카드번호.
    discount_card_no: str | None = None
    ticket_price: str | None = None
    ticket_fare: str | None = None
    bz5_fare_discount_amount: str | None = None
    bz6_fare_discount_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    standard_seat_price_fare: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """결제 결과의 정산수단 한 행을 담습니다. 앱 근거: ReservationPaymentOutStlInfo.java. acnt_info 는 raw 에 남습니다. 거래·오류
    필드(ReservationPaymentOutActInfo.java:28-31,52)라는 이유만으로 개인정보가 없다고 보장할 수 없습니다."""

    settlement_sequence: str | None = None
    settlement_type_code: str | None = None
    settlement_result: str | None = None
    transaction_division: str | None = None
    card_installment_count: str | None = None
    installment_months: str | None = None
    settlement_amount: str | None = None
    #: ``h_stl_crd_no`` — 결제에 쓰인 카드번호.
    settlement_card_no: str | None = None
    card_company_code: str | None = None
    card_company_name: str | None = None
    approval_date: str | None = None
    approval_time: str | None = None
    #: ``h_apv_no`` — 결제 승인번호.
    approval_no: str | None = None
    point_division: str | None = None
    #: ``h_xpoint_no`` — 포인트(마일리지) 번호.
    point_no: str | None = None
    #: ``h_xpoint_apv_no`` — 포인트 승인번호.
    point_approval_no: str | None = None
    remnant_amount: str | None = None
    remote_point: str | None = None
    raw: dict[str, Any] = field(
        default_factory=dict[str, Any],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """결제 결과에 포함된 두 구간 단체석 정보를 담습니다. 앱 근거: ReservationPaymentOutTblSeatInfo.java. 단체명·좌석도 노출될 수 있으며 기록 경고는 모듈
    설명을 따릅니다."""

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
    """카드 결제 시도의 발권·정산·좌석 결과를 담습니다."""

    image_ticket_flag: str | None = None
    #: ``h_rsv_no``. 2026-09-24 카드 결제 응답에서는 빈 문자열이었고 PNR(h_pnr_no)은 결제 응답에 없습니다. 결제한 승차권은 홀드의 pnr_no 로 찾으십시오(같은
    #: 날 승차권 목록의 h_pnr_no 와 같았습니다).
    reservation_no: str | None = None
    settlement_approval_no: str | None = None
    total_received_amount: str | None = None
    settlement_amount: str | None = None
    total_settlement_amount: str | None = None
    customer_no: str | None = None
    member_card_no: str | None = None
    #: h_buy_name은 구매자 성명이므로 로그·repr 노출에 주의하십시오.
    buyer_name: str | None = None
    publication_start_no: str | None = None
    publication_end_no: str | None = None
    mixed_settlement_division: str | None = None
    cancellation_fee: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
    tickets: tuple[ReservationPaymentTicket, ...] = ()
    settlements: tuple[ReservationPaymentSettlement, ...] = ()
    table_seats: tuple[ReservationPaymentTableSeat, ...] = ()
    #: ReservationPaymentOut 의 나머지 스칼라(ReservationPaymentOut.java:90 의 @SerialName). 2026-09-24 라이브 결제 응답에 모두
    #: 있었습니다.
    window_no: str | None = None
    settlement_count: str | None = None
    discount_card_count: str | None = None
    total_price: str | None = None
    total_fare: str | None = None
    total_discount_amount: str | None = None
    adult_count: str | None = None
    child_count: str | None = None
    table_seat_count: str | None = None
    ticket_count: str | None = None
    settlement_type_code: str | None = None
    trade_division: str | None = None
    remark: str | None = None
    survey_flag: str | None = None
    survey_title: str | None = None
    survey_text: str | None = None
    survey_url: str | None = None


@dataclass(frozen=True)
class CardPayment:
    """예약 결제에 사용할 카드 정보를 구성합니다."""

    card_number: str
    #: 카드 비밀번호 앞 두 자리.
    card_password: str
    #: 유효기간 ``YYMM``.
    card_expire: str
    #: 개인 인증이면 생년월일 ``YYMMDD``, 법인이면 사업자번호.
    birthday: str
    #: 일시불은 라이브러리에서 "0"으로 보냅니다. 앱 INS_0 이름만으로 "0"/"00"을 확정하지 않습니다. enum 값은 보호돼
    #: 있습니다(PaymentDefine.java:152-164,185-189,207-210). 기본 선택은 InstallmentViewModel.java:55,94-96, 결제수단 인덱스
    #: 접미사는 PaymentMethod.java:672-694와 ReservationPaymentInStlInfo.java:33을 따릅니다.
    installment: str = "0"
    #: ``hidAthnDvCd1`` — ``"J"`` 개인 / ``"S"`` 법인.
    card_type: Literal["J", "S"] = "J"

    def __post_init__(self) -> None:
        # 타입 힌트만으로 런타임 결제 입력이 검증되지는 않으므로 직접 검사합니다.
        if self.card_type not in ("J", "S"):
            raise KorailProtocolError('card_type must be "J" (personal) or "S" (corporate)')


@dataclass(frozen=True)
class PaidTicket:
    """환불할 발권 승차권 한 장의 식별자와 반환 자격증명을 구성합니다. sale_date 는 원표 반환일이 아니라 현재 승차권 h_sale_dt 입니다. 앱 호출은 getSaleDt 와 원표
    창구·순번·비밀번호를 함께 전달합니다 (MyTicketDetailViewModel.java:1521, RefundTicketIn.java:154,162,364,
    TicketDetailOut.java:458,466,470,486). 반면 수수료 조회는 h_orgtk_ret_sale_dt 를 사용합니다
    (MyTicketDetailViewModel.java:277, RefundCommissionIn.java:141,149). 비슷한 필드 이름만 보고 두 날짜나 창구 키를 바꾸어 쓰지
    마십시오."""

    pnr_no: str
    #: **현재** 승차권의 ``h_sale_dt``. 전송 키 ``h_orgtk_sale_dt`` 를 채우지만 재발행된 승차권에서는 원표의 판매일자와 같지 않습니다 — 위 경고 참조.
    sale_date: str
    #: ``h_orgtk_wct_no`` → 전송 키 ``h_orgtk_sale_wct_no``.
    sale_window_no: str
    sale_sequence: str
    return_password: str
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
        ``analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1521`` 과 필드 단위로
        같습니다(위 :class:`PaidTicket` 경고의 인용 참조)."""
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
        # train_no 를 주지 않으면 첫 여정의 열차번호를 씁니다 — 앱 환불 화면이 trnNo 로 싣는 값 (ticketInfos[0].trnNo,
        # RefundTicketViewModel$refundTicket$1.smali:854-868)과 같습니다.
        if not train_no and detail.journeys:
            train_no = detail.journeys[0].train_no or ""
        return cls(
            **parts,
            train_no=train_no,
            pbp_acceptance_target_flag=detail.pbp_acceptance_target_flag,
        )


@dataclass(frozen=True)
class DiscountCardSectionRequest:
    """구매할 N카드의 적용 구간을 구성합니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. DTO 키는 밑줄로
    끝나며(NCardjrny.java:96-112) 공통 평탄화가 1-기반 인덱스를 붙입니다(NetworkService.java:15345-15366). 구간 목록 선언:
    NCardInfoIn.java:37, 라우트: NetworkApi.java:335-337. 허용 1~3구간은 라이브러리 상한입니다."""

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """2인용 N카드의 추가 사용자 정보를 구성합니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다.
    NCardInfoIn.java:30-34 의 속성명 자체에 _1 이 포함됩니다. serializer 이름은 보호돼 전송 키는 속성명에 따른 추정입니다."""

    customer_no: str
    name: str
    phone: str


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """N카드 구매에 필요한 구간·사용자·상품 정보를 구성합니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 라우트는
    NetworkApi.java:335-337 입니다. 자체 필드는 NCardInfoIn.java:29-39 참고. 명시적 별칭이 없는 필드의 전송 키는 보호된 serializer 대신
    속성명을 사용한 추정입니다."""

    card_kind_management_no: str
    customer_no: str
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """N카드 기간연장에 필요한 원표 식별자를 구성합니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 기간연장용 원표
    식별자(MyTicketDetailViewModel.java:1049, NCardExtensionIn.java:180). 판매일은 h_orgtk_ret_sale_dt 이므로 현재
    h_sale_dt 를 쓰는 PaidTicket 환불과 다릅니다. 출처: TicketDetailOut.java:458,462,466,470."""

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """N카드 구매의 결제 전 예약 결과를 담습니다. 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 구매의 결제 전 응답(NCardInfoOut.java:25-38,
    NetworkApi.java:335-337). 자체 전송 키는 속성명에 따른 추정입니다. lump_settlement_target_no 를 받았다고 결제 완료는 아닙니다. 앱은 이를 결제
    화면에 전달해 별도 정산에 사용합니다(PayRoute.java:1323, PayViewModel.java:6628)."""

    lump_settlement_target_no: str | None = None
    discount_card_settlement_target_no: str | None = None
    received_amount: str | None = None
    stx_amount: str | None = None
    taxt_supply_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
    #: ``dcntCrdKndMgNo`` — 서버가 실제로 등록한 할인카드 종류 관리번호. 요청의
    #: :attr:`DiscountCardPurchaseRequest.card_kind_management_no` ("요청한 값")과 다른 이름을 써서, 호출자가 "무엇을 요청했는지"와 "서버가
    #: 실제로 등록한 것"을 구분할 수 있게 합니다 (``NCardInfoOut.java:30``, ``dcntCrdStlTgtNo`` 와는 별개 필드).
    registered_card_kind_management_no: str | None = None


@dataclass(frozen=True)
class PriceRecalculationRow:
    """예약 할인 재계산에 사용할 승객 한 행을 구성합니다. 기존 좌석의 종류·객실·할인 코드를 복사하고 새 할인·증명·가족번호를 별도로 둡니다
    (DiscountPriceParams.java:13-39, PayViewModel.java:16856-16863). DTO 변환은 PayViewModel.java:6161-6165, 병렬
    6목록 전송은 NetworkService.java:9997-10043 와 NetworkApi.java:582-584 입니다.

    여섯 값은 None 아닌 문자열이어야 합니다. Retrofit 이 null 원소를 건너뛰면 병렬 목록의 인덱스가 어긋납니다(ParameterHandler.java:18-31,252-259).
    할인 미선택은 빈 문자열입니다. 2026-09-22 관측: 요청 할인 131 은 SUCC/IRZ000008 및 응답 할인 204, 000 은 WZZ000001 이었습니다. 다른 코드들은 이
    실험으로 검증하지 않았습니다. 성공 봉투는 할인 자격의 보장이 아니며 실제 자격에 맞는 값만 사용해야 합니다. certificate_no 는 필요한 증명번호, family_sequence_no
    는 다자녀 fmlySqno 입니다(Fmly.java:145)."""

    passenger_type_code: str
    room_class_code: str
    #: 기존 좌석의 h_dcnt_knd_cd1 을 복사합니다(PayViewModel.java:16858). 새로 요청할 할인 hidDcntKndCd 와 다르므로 임의로 덮어쓰지 마십시오.
    discount_kind_code: str
    requested_discount_code: str = ""
    certificate_no: str = ""
    family_sequence_no: str = ""


@dataclass(frozen=True)
class PriceRecalculationRequest:
    """PNR 한 건의 할인 재계산 조건을 구성합니다. 앱 근거: PayViewModel.java:6142-6171; PriceReCalculationIn.java:31-41. 비회원일 때만
    hiduserYn·hidCustNo 를 함께 넣습니다. job id·N 리터럴은 보호돼 있으며 라이브러리의 값은 라이브 기록에
    의존합니다(ReservationJobId.java:20,42-45)."""

    pnr_no: str
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: 비회원 고객번호는 hiduserYn 과 함께 채웁니다(PayViewModel.java:6167-6168). 고유 폼 키 수는 lang=None 일 때 회원 12/비회원 14, lang 지정
    #: 시 13/15 이며 배열 원소 수와 다릅니다. FieldMap 의 null 값은 오류여서 빌더가 키를 뺍니다(ParameterHandler.java:252-259,276-293;
    #: NetworkApi.java:583).
    non_member_no: str | None = None
    #: txtPsrmClCd1은 여정 전체의 객실 등급이며, 승객별 psrm_cl_cd 목록과 다릅니다. 예약 폼의 같은 키는
    #: mutation_payloads.build_reservation_form을 따릅니다.
    cabin_class_code: str | None = None
    seat_attribute_code_2: str | None = None
    #: txtSeatAttCd4는 예약 폼에서 실제 좌석 속성을 넣는 슬롯입니다(_seat_attribute_key(1)). 재계산에서도 같은 의미인지는 검증 못 함이며 슬롯 번호만 대응시킵니다.
    seat_attribute_code_4: str | None = None
    seat_attribute_code_5: str | None = None

    @classmethod
    def for_hold(
        cls,
        hold: ReservationHoldResponse,
        requested_discount_codes: Sequence[str],
    ) -> PriceRecalculationRequest:
        """홀드의 첫 여정 좌석마다 한 행을 앱처럼 만듭니다. 앱은 승객마다 첫 좌석으로 행을 만들고 승객 유형·객실·현재 할인 코드를 좌석에서
        복사하며(PayViewModel.java:5405-5520, 16802-16863), 할인 화면 경로는 좌석의 dcnt_reld_no 를 hidDscpNo 로 옮깁니다(:5518).
        requested_discount_codes 는 좌석 순서대로 하나씩이고 수가 다르면 앱처럼 보내지 않습니다(:17469). 요청 코드 매핑(ReqDiscount)은
        보호돼 있어 호출자가 정합니다. 다자녀 가족번호는 이 메서드가 채우지 않습니다."""
        pnr_no = hold.pnr_no
        if hold.str_result != "SUCC" or not isinstance(pnr_no, str) or not pnr_no.strip():
            raise KorailProtocolError("KORAIL price recalculation needs a successful hold with a PNR")
        if isinstance(requested_discount_codes, str) or not isinstance(requested_discount_codes, Sequence):
            raise KorailProtocolError("requested_discount_codes must be a sequence with one code per seat")
        container = hold.journeys[0].raw.get("seat_infos") if hold.journeys else None
        seats = container.get("seat_info") if isinstance(container, Mapping) else None
        if not isinstance(seats, list) or not seats or not all(isinstance(seat, Mapping) for seat in seats):
            raise KorailProtocolError("KORAIL price recalculation needs the hold's first-journey seat rows")
        if len(requested_discount_codes) != len(seats):
            raise KorailProtocolError(
                f"KORAIL price recalculation needs one requested code per seat of the first journey "
                f"({len(seats)})"
            )

        def text(seat: Mapping[str, Any], key: str) -> str:
            # 좌석 필드는 String 선언입니다(ReservationOutSeatInfo.java:80-109). JSON 정수만 문자열로 받고 bool·객체 등은 보내지 않습니다.
            value = seat.get(key)
            if value is None or isinstance(value, str):
                return value or ""
            if type(value) is int:
                try:
                    return str(value)
                except ValueError as exc:
                    error = KorailProtocolError(
                        f"KORAIL price recalculation seat field {key} is an integer too long to use"
                    )
                    error.raw = hold.raw
                    error.parser_raw = seat
                    raise error from exc
            raise KorailProtocolError(
                f"KORAIL price recalculation seat field {key} must be a string or an integer"
            )

        rows = tuple(
            PriceRecalculationRow(
                text(seat, "h_psg_tp_cd"),
                text(seat, "h_psrm_cl_cd"),
                text(seat, "h_dcnt_knd_cd1"),
                code,
                text(seat, "dcnt_reld_no"),
            )
            for seat, code in zip(seats, requested_discount_codes, strict=True)
        )
        return cls(pnr_no, rows)


@dataclass(frozen=True)
class CartDiscountAddition:
    """장바구니 추가 결과의 승객별 할인 정보를 담습니다. 명시적 키: PsgDiscAddInfo.java:81,85."""

    passenger_sequence_no: str | None = None
    #: h_duty_ref_rcgn_ps_dv_cd 는 DTO 에 선언된 구분 코드이며(APK 필드명 보존) 의미·가능한 값은 미확인입니다.
    duty_reference_recognition_division_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class CartAddResponse(BaseKorailResponse):
    """장바구니 추가 결과와 승객별 할인 목록을 담습니다. 구조: AddCartListOut.java:24-25,76 → PsgDiscAddInfos.java:81. 행이 없으면
    discount_additions 는 빈 튜플입니다. 2026-09-24 라이브: 열차·공항버스 홀드 PNR 모두 SUCC/IRZ000002 였고 할인 행은 없었습니다."""

    discount_additions: tuple[CartDiscountAddition, ...] = ()


@dataclass(frozen=True)
class ProductCancelResponse(BaseKorailResponse):
    """여행상품 예약의 실제 취소 결과를 담습니다. 앱 근거: ProductCancelOut.java."""

    integrated_message_code: str | None = None


@dataclass(frozen=True)
class MaasCancelResponse(BaseKorailResponse):
    """지원하지 않는 미결제 부가서비스 해제 응답 구조를 기록합니다. 미결제 부가서비스 해제 결과(addService.cancelPay.do, MaasCancelOut.java)."""

    integrated_message_code: str | None = None


@dataclass(frozen=True)
class CartAddRequest:
    """미결제 예약을 장바구니에 추가할 PNR 입력을 구성합니다. 자체 필드는 hidPnrNo 하나입니다 (AddCartListIn.java:25-30,79;
    NetworkApi.java:265-267)."""

    pnr_no: str


@dataclass(frozen=True)
class SelfCheckInRegisterResponse(BaseKorailResponse):
    """셀프 체크인 등록(checkin.reg.do) 결과를 담습니다. msgId 는 필수·nullable 이며 앱은 읽지
    않습니다(SelfCheckInRegisterOut.java:47-52)."""

    message_id: str | None = None


@dataclass(frozen=True)
class SelfCheckInCancelResponse(BaseKorailResponse):
    """셀프 체크인 취소(checkin.cnc.do) 결과를 담습니다. msgId 는 선택입니다(SelfCheckInCancelOut.java:50-56)."""

    message_id: str | None = None


@dataclass(frozen=True)
class DeliveredTicketRetrievalResponse(BaseKorailResponse):
    """전달한 승차권 회수(tk.pbpWdrw.do) 결과를 담습니다. prsList 는 필수이고 각 행의 prsFlg 도 필수입니다(RetrieveTicketOut.java:54-59,
    Prs.java:46-50). 앱은 성공 여부와 h_msg_txt 만 씁니다."""

    process_flags: tuple[str, ...] = ()
