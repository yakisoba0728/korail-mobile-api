# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""변경 입력 모델의 생성은 전송하지 않으며 raw·repr의 민감값은 자동 마스킹하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Literal

from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError
from .models import BaseKorailResponse, PhysicalSeat, ReservationPassengerInfo, SeatInventoryResponse

if TYPE_CHECKING:
    from .read_models import RefundTicketDetailResponse


@dataclass(frozen=True)
class RefundTicketResponse(BaseKorailResponse):
    """승차권 환불 결과의 정산수단 코드를 담습니다.

    응답의 정산 목록(``stlList``)이 ``null``이면 ``settlement_method_codes``는 빈 튜플이고 ``settlement_list_is_null``이
    ``True``입니다. 정산 목록 키가 없으면 ``KorailProtocolError``가 발생합니다."""

    # stlList 는 필수이면서 null 일 수 있습니다(RefundTicketOut.java:48-53).

    settlement_method_codes: tuple[str, ...] = ()
    settlement_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundOriginalTicket:
    """역에서 발권한 승차권의 환불 확인 응답에 들어 있는 원표 한 행을 담습니다."""

    pnr_no: str
    original_sale_date: str | None = None
    original_sale_window_no: str | None = None
    original_sale_sequence: str | None = None
    original_return_password: str | None = None
    ticket_kind_code: str | None = None
    refund_division_code: str | None = None
    refund_reason_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


def _require_every_field(
    request: StationRefundVerificationRequest | StationRefundExecutionRequest,
    step: str,
) -> None:
    """역 환불의 모든 필드는 비어 있지 않은 문자열이어야 합니다."""
    for field_ in fields(request):
        value = getattr(request, field_.name)
        if not isinstance(value, str) or not value.strip():
            raise KorailProtocolError(f"KORAIL station refund {step} requires {field_.name}")


@dataclass(frozen=True)
class StationRefundVerificationRequest:
    """역에서 발권한 승차권의 환불 확인에 필요한 이름과 반환 식별자를 구성합니다.

    ``return_no_1``~``return_no_4``에는 반환번호 네 칸을 차례로 넣습니다. 모든 필드는 비어 있지 않은
    문자열이어야 하며, 아니면 ``KorailProtocolError``가 발생합니다."""

    customer_name: str
    return_no_1: str
    return_no_2: str
    return_no_3: str
    return_no_4: str

    def __post_init__(self) -> None:
        _require_every_field(self, "verification")


@dataclass(frozen=True)
class StationRefundVerificationResponse(BaseKorailResponse):
    """역에서 발권한 승차권의 환불 확인 결과(금액과 원표 목록)를 담습니다.

    서버가 원표 목록을 ``null``로 보내면 ``original_tickets``는 빈 튜플이고 ``original_ticket_list_is_null``이
    ``True``입니다."""

    received_amount: str | None = None
    refund_fee: str | None = None
    refund_amount: str | None = None
    popup_message: str | None = None
    result_message: str | None = None
    original_tickets: tuple[StationRefundOriginalTicket, ...] = ()
    original_ticket_list_is_null: bool = False


@dataclass(frozen=True)
class StationRefundExecutionRequest:
    """역에서 발권한 승차권의 환불 실행 입력을 구성합니다.

    보통 ``from_verification()``으로 환불 확인 결과에서 만듭니다. 만들기만 해서는 요청을 보내지 않으며, 실제 환불은
    ``KorailClient.execute_station_ticket_refund()``를 호출해야 합니다. 모든 필드는 비어 있지 않은 문자열이어야 하며,
    아니면 ``KorailProtocolError``가 발생합니다."""

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
        """환불 확인 응답의 첫 원표와 확인된 환불액·수수료로 실행 입력을 만듭니다.

        확인 응답이 성공(``"SUCC"``)이 아니거나 원표가 없거나 옮겨 담을 값이 비어 있으면 ``KorailProtocolError``가
        발생합니다."""
        # 첫 Orgtkinfo 행을 씁니다.
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
        # 확인 응답의 필수값 누락은 프로토콜 오류입니다.
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
    """역에서 발권한 승차권의 환불 실행 결과를 담습니다."""

    refund_division_code: str | None = None


@dataclass(frozen=True)
class KorailPassengerCounts:
    """승객 종류별 예약 인원을 구성합니다.

    인원이 0인 승객 종류는 요청에 싣지 않습니다. 유아·안내견을 포함한 전체 인원은 1~9명이어야 합니다. 인원에 음수나 정수가
    아닌 값이 있거나 전체 인원이 이 범위를 벗어나면 ``KorailProtocolError``가 발생합니다."""

    # 근거: Passengers.java:48,610-616,743-753.

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
        """유아·안내견을 포함한 전체 승객 수를 반환합니다."""
        # 앱 근거: Passengers.java:610-616.
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
    """호차 번호와 좌석 식별자로 좌석 지정 입력을 구성합니다.

    ``seat_no``에는 좌석 재고 응답의 ``seat_no``를 그대로 넣으세요. 보통 ``from_inventory()``로 만듭니다. ``car_no``는 1
    이상의 정수, ``seat_no``는 비어 있지 않은 문자열이어야 하며, 아니면 ``KorailProtocolError``가 발생합니다."""

    # 앱도 선택 호차와 getSeatNo 를 복사합니다(TrainSeatMapViewModel.java:2210). 선행 키:
    # TicketReservationInSrcar.java:81-88, 후행 호차 키: TicketReservationInSrcarTrailing.java:86-89.

    car_no: int
    seat_no: str

    def __post_init__(self) -> None:
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
        """좌석 재고 응답과 그 응답의 판매 가능한 좌석으로 좌석 지정 입력을 만듭니다.

        ``inventory.car_no``가 없으면 이 메서드를 쓸 수 없으므로 ``KorailSeatAssignment(car_no=..., seat_no=...)``로 직접
        만드세요. 호차 번호가 없거나, ``seat``이 ``inventory.seats``에 없거나, ``seat.sale_possible``이 ``"Y"``가 아니면
        ``KorailProtocolError``가 발생합니다."""
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

    # 선언: ReservationOutJrnyInfo.java:86,361. 관측: 예약 생성 응답 21/21행에는 없고 재계산 4/4행·예약 상세 8/8행에는
    # 있었습니다. 이 관측이 모든 예약 생성 응답에서 None임을 보장하지는 않습니다.
    #: 여정 순번(``h_jrny_sqno``)입니다. 예약 생성 응답에는 없을 수 있으며, 그러면 ``None``입니다.
    journey_sequence: str | None = None
    reservation_change_no: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    # 선언: ReservationOutJrnyInfo.java:86,305. 관측: reserve/transfer/merge 의 21여정에는 키가 없었으며 익일 도착도
    # 포함됐습니다.
    #: 도착일(``h_arv_dt``)입니다. 예약 응답에는 없을 수 있으며, 그러면 ``None``입니다. 밤을 넘기는 열차는 도착 시각만으로
    #: 도착일을 알 수 없습니다.
    arrival_date: str | None = None
    arrival_time: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    train_no: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationHoldResponse(BaseKorailResponse):
    """홀드(결제 전 예약) 요청의 결과와 결제 기한·금액을 담습니다.

    이 객체를 받았다는 것만으로 예약이 성공했다고 보장하지 않으므로 응답 상태(``str_result``)와 ``pnr_no``를 확인하세요.
    결제할 금액은 ``received_amount``입니다."""

    pnr_no: str | None = None
    journey_count: str | None = None
    window_no: str | None = None
    temporary_job_sequence_1: str | None = None
    temporary_job_sequence_2: str | None = None
    payment_flag: str | None = None
    payment_message: str | None = None
    # 근거: ReservationOut.java:49,408-409.
    #: ``h_pay_limit_msg`` 값입니다. 결제 기한은 이 필드가 아니라 ``payment_deadline_date``와 ``payment_deadline_time``에
    #: 있습니다.
    payment_deadline_message: str | None = None
    payment_deadline_notice: str | None = None
    # 근거: ReservationOut.java:400,404; 표시는 MyReservationScreenKt.java:6008-6010, DateHelper.java:302.
    #: 결제 기한 날짜입니다. 앱은 이 값과 ``payment_deadline_time``을 이어 붙여 결제 기한으로 표시합니다.
    payment_deadline_date: str | None = None
    payment_deadline_time: str | None = None
    # h_tot_fare는 선언됐지만 일반적인 의미는 미확인입니다(ReservationOut.java:444). 내장 표본(BasketTicketDataKt.java:44)은
    # 일반식의 증거가 아닙니다.
    #: ``h_tot_fare`` 값입니다. 의미를 확인하지 못했습니다. 결제 금액으로는 ``received_amount``를 쓰세요.
    total_fare: str | None = None
    # h_tot_prc는 앱의 표시 합계에 쓰입니다(ReservationOut.java:448; PayViewModel.java:11314-11318). 실서버 관측: 일반실·특실
    # 기준액은 54,400원, 정산액은 53,900/78,400원이었습니다.
    #: 앱이 표시하는 합계 금액(``h_tot_prc``)입니다. 결제에는 ``received_amount``를 쓰세요.
    total_price: str | None = None
    # 좌석 합을 먼저 구하고 선언 총액과 대조하며, 사용할 좌석 행이 없으면 선언 총액을 사용합니다(mutation_parsers._received_amount).
    #: 결제할 금액입니다. 좌석별 금액(``h_rcvd_amt``)의 합이며, 응답의 총액(``h_tot_rcvd_amt``)과 다르면 응답을 읽을 때
    #: ``KorailProtocolError``가 발생합니다. 좌석 행이 없으면 응답의 총액을 쓰고, 좌석 금액을 읽을 수 없으면 ``None``입니다.
    received_amount: str | None = None
    journeys: tuple[ReservationJourney, ...] = ()
    total_discount_amount: str | None = None
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
    # 앱은 예약대기 홀드를 결제하지 않고 대기 옵션만 저장합니다(TrainScheduleViewModel.java:5096-5101;
    # ReservationWaitViewModel.java:1155-1160). reserve·reserve_transfer 가 STANDBY 홀드에 False 를 넣습니다.
    #: 결제할 수 있는 홀드인지 나타냅니다. 예약대기(``STANDBY``)로 만든 홀드는 ``False``이며, ``pay_with_card``는 이런 홀드를
    #: 요청 전에 거절합니다.
    payable: bool = True
    # 근거: client.recalculate_price 의 add_to_cart 분기(raise_on_fail=False).
    #: ``recalculate_price(..., add_to_cart=True)``로 받은 결과에만 장바구니 추가 결과가 들어갑니다. 장바구니 추가가
    #: 실패해도 예외 없이 이 필드에 담기므로 ``str_result``를 확인하세요. 그 밖에는 ``None``입니다.
    cart_addition: CartAddResponse | None = None


@dataclass(frozen=True)
class ReservationPaymentCoupon:
    """결제 결과에 포함된 쿠폰 정보를 담습니다."""

    certificate_password: str | None = None
    coupon_no: str | None = None
    management_close_date: str | None = None
    management_start_date: str | None = None
    ticket_return_no: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTicket:
    """결제로 발권된 승차권 한 장의 식별자와 반환 식별자를 담습니다."""

    ticket_sequence: str | None = None
    sale_date: str | None = None
    sale_sequence: str | None = None
    return_password: str | None = None
    return_no: str | None = None
    recipient_name: str | None = None
    discount_card_no: str | None = None
    ticket_price: str | None = None
    ticket_fare: str | None = None
    bz5_fare_discount_amount: str | None = None
    bz6_fare_discount_amount: str | None = None
    total_discount_amount: str | None = None
    total_received_amount: str | None = None
    standard_seat_price_fare: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentSettlement:
    """결제 결과의 정산수단 한 행을 담습니다.

    카드번호·승인번호 같은 값이 들어 있을 수 있으므로 로그에 남길 때 주의하세요."""

    # 거래·오류 필드(ReservationPaymentOutActInfo.java:28-31,52)라는 이유만으로 개인정보가 없다고 보장할 수 없습니다.

    settlement_sequence: str | None = None
    settlement_type_code: str | None = None
    settlement_result: str | None = None
    transaction_division: str | None = None
    card_installment_count: str | None = None
    installment_months: str | None = None
    settlement_amount: str | None = None
    settlement_card_no: str | None = None
    card_company_code: str | None = None
    card_company_name: str | None = None
    approval_date: str | None = None
    approval_time: str | None = None
    approval_no: str | None = None
    point_division: str | None = None
    point_no: str | None = None
    point_approval_no: str | None = None
    remnant_amount: str | None = None
    remote_point: str | None = None
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentTableSeat:
    """결제 결과에 포함된 두 구간 단체석 정보를 담습니다."""

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
    raw: Mapping[str, object] = field(
        default_factory=dict[str, object],
        compare=False,
    )


@dataclass(frozen=True)
class ReservationPaymentResponse(BaseKorailResponse):
    """카드 결제 시도의 발권·정산·좌석 결과를 담습니다."""

    image_ticket_flag: str | None = None
    # 관측: 카드 결제 응답에서는 빈 문자열이었습니다.
    #: 결제 응답의 예약 번호 필드입니다. 카드 결제 응답에서는 빈 문자열일 수 있습니다. 결제 응답에는 PNR(``h_pnr_no``)이
    #: 없으므로 PNR은 홀드의 ``pnr_no``를 쓰세요.
    reservation_no: str | None = None
    settlement_approval_no: str | None = None
    total_received_amount: str | None = None
    settlement_amount: str | None = None
    total_settlement_amount: str | None = None
    customer_no: str | None = None
    member_card_no: str | None = None
    buyer_name: str | None = None
    publication_start_no: str | None = None
    publication_end_no: str | None = None
    mixed_settlement_division: str | None = None
    cancellation_fee: str | None = None
    coupons: tuple[ReservationPaymentCoupon, ...] = ()
    tickets: tuple[ReservationPaymentTicket, ...] = ()
    settlements: tuple[ReservationPaymentSettlement, ...] = ()
    table_seats: tuple[ReservationPaymentTableSeat, ...] = ()
    # 여기부터 ReservationPaymentOut 의 나머지 스칼라입니다(ReservationPaymentOut.java:90 의 @SerialName).
    #: 창구 번호(``h_wct_no``)입니다.
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
    card_password: str
    card_expire: str
    birthday: str
    # 앱 INS_0 이름만으로 "0"/"00"을 확정하지 않습니다. enum 값은 보호돼 있습니다(PaymentDefine.java:152-164,185-189,207-210).
    # 기본 선택은 InstallmentViewModel.java:55,94-96, 결제수단 인덱스 접미사는 PaymentMethod.java:672-694와
    # ReservationPaymentInStlInfo.java:33을 따릅니다. 형식 검사는 mutation_payloads.build_card_payment_form 에 있습니다.
    #: 할부 개월 수입니다. 숫자 1~2자리이며 기본값 ``"0"``은 일시불입니다.
    installment: str = "0"
    #: 카드 종류입니다. ``"J"``(기본값)는 개인 카드, ``"S"``는 법인 카드입니다. 다른 값이면 ``KorailProtocolError``가
    #: 발생합니다.
    card_type: Literal["J", "S"] = "J"

    def __post_init__(self) -> None:
        # 타입 힌트만으로 런타임 결제 입력이 검증되지는 않으므로 직접 검사합니다.
        if self.card_type not in ("J", "S"):
            raise KorailProtocolError('card_type must be "J" (personal) or "S" (corporate)')


@dataclass(frozen=True)
class PaidTicket:
    """환불할 발권 승차권 한 장의 PNR과 반환 식별자를 구성합니다.

    보통 ``from_refund_detail()``로 승차권 상세 응답에서 만드세요. 환불 요청은 상세 응답의 판매일(``sale_date``)을 쓰고,
    수수료 조회는 원표 반환일을 쓰므로 두 값을 섞어 쓰지 마세요. ``refund()``에는 이 값과 함께 ``get_refund_commission()``의
    응답을 ``commission``으로 넘겨야 합니다."""

    # 환불은 현재 sale_date, 수수료 조회는 원표 반환일을 사용합니다(MyTicketDetailViewModel.java:277,1521). 재발행된 승차권은
    # sale_date 가 원표의 판매일자와 같지 않습니다.

    pnr_no: str
    #: 환불 요청의 판매일(``h_orgtk_sale_dt``)입니다. 재발행된 승차권은 원표의 판매일과 다를 수 있습니다.
    #: ``from_refund_detail()``로 만들면 상세 응답의 ``sale_date``가 들어갑니다.
    sale_date: str
    sale_window_no: str
    sale_sequence: str
    return_password: str
    #: 환불 요청에 함께 싣는 열차 번호입니다. 빈 문자열이면 보내지 않습니다. ``from_refund_detail()``은 따로 주지 않으면
    #: 첫 여정의 열차 번호를 넣습니다.
    train_no: str = ""
    #: 대리수령 대상 플래그입니다. ``refund()``의 ``pbp_acceptance_target_flag``가 ``None``일 때 이 값을 쓰며, 둘 다
    #: ``None``이면 보내지 않습니다.
    pbp_acceptance_target_flag: str | None = None

    @classmethod
    def from_refund_detail(
        cls,
        detail: RefundTicketDetailResponse,
        *,
        train_no: str = "",
    ) -> PaidTicket:
        """승차권 상세 응답에서 환불 입력을 앱과 같은 방식으로 만듭니다.

        ``train_no``를 주지 않으면 첫 여정의 열차 번호를 씁니다. 상세 응답에 PNR, 판매일, 원표 창구번호·일련번호·반환
        비밀번호 중 빈 값이 있으면 ``KorailProtocolError``가 발생합니다."""
        # 7.0.6 의 analysis/jadx/sources/com/korail/talk/ui/screen/myticket/MyTicketDetailViewModel.java:1521 과 필드 단위로
        # 같습니다.
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
    """구매할 N카드의 적용 구간을 구성합니다.

    요청에는 구간마다 1부터 매긴 번호를 붙여 보냅니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. DTO 키는 밑줄로 끝나며(NCardjrny.java:96-112) 공통
    # 평탄화가 1-기반 인덱스를 붙입니다(NetworkService.java:15345-15366).

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    journey_type_code: str = "11"


@dataclass(frozen=True)
class DiscountCardAdditionalUser:
    """2인용 N카드의 추가 사용자 정보를 구성합니다.

    요청 키 이름은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. NCardInfoIn.java:30-34 의 속성명 자체에 _1 이
    # 포함됩니다. serializer 이름은 보호돼 전송 키는 속성명에 따른 추정입니다.

    customer_no: str
    name: str
    phone: str


@dataclass(frozen=True)
class DiscountCardPurchaseRequest:
    """N카드 구매에 필요한 구간·사용자·상품 정보를 구성합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 라우트는 NetworkApi.java:335-337 입니다.

    card_kind_management_no: str
    customer_no: str
    validity_start_date: str = ""
    usable_trip_count: str = ""
    sections: tuple[DiscountCardSectionRequest, ...] = ()
    additional_users: tuple[DiscountCardAdditionalUser, ...] = ()


@dataclass(frozen=True)
class DiscountCardTicket:
    """N카드 기간연장에 필요한 원표의 반환 식별자를 구성합니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. 기간연장용 원표 식별자(MyTicketDetailViewModel.java:1049,
    # NCardExtensionIn.java:180).

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str


@dataclass(frozen=True)
class DiscountCardPurchaseResponse(BaseKorailResponse):
    """N카드 구매의 결제 전 예약 결과를 담습니다."""

    # 검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. N카드 구매의 결제 전 응답(NCardInfoOut.java:25-38,
    # NetworkApi.java:335-337).

    lump_settlement_target_no: str | None = None
    discount_card_settlement_target_no: str | None = None
    received_amount: str | None = None
    stx_amount: str | None = None
    taxt_supply_amount: str | None = None
    usable_trip_count: str | None = None
    validity_start_date: str | None = None
    validity_end_date: str | None = None
    # 요청의 DiscountCardPurchaseRequest.card_kind_management_no ("요청한 값")과 다른 이름을 써서, 호출자가 "무엇을
    # 요청했는지"와 "서버가 실제로 등록한 것"을 구분할 수 있게 합니다 (NCardInfoOut.java:30, dcntCrdStlTgtNo 와는 별개 필드).
    #: 응답에 담긴 카드 종류 관리번호입니다. 요청한 값은 ``DiscountCardPurchaseRequest.card_kind_management_no``에 있습니다.
    registered_card_kind_management_no: str | None = None


@dataclass(frozen=True)
class PriceRecalculationRow:
    """예약 할인 재계산에 사용할 승객 한 행을 구성합니다.

    보통 ``PriceRecalculationRequest.for_hold()``가 홀드의 좌석마다 한 행씩 만듭니다. 값이 없는 칸은 ``None``이 아니라
    빈 문자열로 두세요. 모든 필드는 문자열이어야 하고 ``passenger_type_code``, ``room_class_code``,
    ``discount_kind_code``는 비어 있으면 안 됩니다. 이 검사는 요청을 보내기 전에 합니다."""

    # None 원소를 보내면 병렬 6목록의 인덱스가 어긋나므로 빈 문자열을 사용합니다(NetworkApi.java:582-584;
    # ParameterHandler.java:18-31).

    passenger_type_code: str
    room_class_code: str
    # 근거: PayViewModel.java:16858.
    #: 홀드 좌석의 기존 할인 종류 코드(``h_dcnt_knd_cd1``)를 그대로 옮겨 담습니다. 새로 요청할 할인
    #: 코드(``requested_discount_code``)와 다른 값이므로 임의로 덮어쓰지 마세요.
    discount_kind_code: str
    requested_discount_code: str = ""
    certificate_no: str = ""
    family_sequence_no: str = ""


@dataclass(frozen=True)
class PriceRecalculationRequest:
    """PNR 한 건의 할인 재계산 조건을 구성합니다.

    보통 ``for_hold()``로 홀드에서 만듭니다. 비회원일 때만 ``non_member_no``를 채우세요. 요청에 싣는 작업 구분 값과
    비회원 구분 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # 앱 근거: PayViewModel.java:6142-6171; PriceReCalculationIn.java:31-41. 비회원일 때만 hiduserYn·hidCustNo 를 함께
    # 넣습니다. job id·N 리터럴은 보호돼 있으며 라이브러리의 값은 라이브 기록에 의존합니다(ReservationJobId.java:20,42-45).

    pnr_no: str
    rows: tuple[PriceRecalculationRow, ...] = ()
    # 비회원 고객번호는 hiduserYn 과 함께 채웁니다(PayViewModel.java:6167-6168). 고유 폼 키 수는 lang=None 일 때 회원 12/비회원
    # 14, lang 지정 시 13/15 이며 배열 원소 수와 다릅니다.
    #: 비회원 고객번호입니다. 값이 있으면 비회원 구분과 함께 보내고, ``None``이면 보내지 않습니다.
    non_member_no: str | None = None
    cabin_class_code: str | None = None
    seat_attribute_code_2: str | None = None
    # 재계산에서도 같은 의미인지는 검증 못 함이며 슬롯 번호만 대응시킵니다.
    #: 좌석 속성 코드 4번 칸(``txtSeatAttCd4``)입니다. 재계산 요청에서의 의미는 확인하지 못했습니다. ``None``이면 보내지
    #: 않습니다.
    seat_attribute_code_4: str | None = None
    seat_attribute_code_5: str | None = None

    @classmethod
    def for_hold(
        cls,
        hold: ReservationHoldResponse,
        requested_discount_codes: Sequence[str],
    ) -> PriceRecalculationRequest:
        """홀드의 첫 여정 좌석마다 한 행씩, 앱과 같은 방식으로 재계산 조건을 만듭니다.

        좌석별 승객 유형·객실 등급·기존 할인 코드·증빙 번호를 옮겨 담으므로 ``requested_discount_codes``는 첫 여정 좌석 수와
        같은 개수여야 합니다. 홀드가 성공(``"SUCC"``)이 아니거나 PNR·좌석 행이 없거나 개수가 다르면 ``KorailProtocolError``가
        발생합니다."""
        # 근거: PayViewModel.java:5518,16856-16863,17469.
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

        def text(seat: Mapping[str, object], key: str) -> str:
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
    """장바구니 추가 결과의 승객별 할인 정보를 담습니다."""

    # 명시적 키: PsgDiscAddInfo.java:81,85.

    passenger_sequence_no: str | None = None
    # h_duty_ref_rcgn_ps_dv_cd 는 DTO 에 선언된 구분 코드입니다(APK 필드명 보존).
    #: ``h_duty_ref_rcgn_ps_dv_cd`` 값입니다. 의미와 가능한 값을 확인하지 못했습니다.
    duty_reference_recognition_division_code: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class CartAddResponse(BaseKorailResponse):
    """장바구니 추가 결과와 승객별 할인 목록을 담습니다.

    할인 행이 없으면 ``discount_additions``는 빈 튜플입니다."""

    # 구조: AddCartListOut.java:24-25,76 → PsgDiscAddInfos.java:81.

    discount_additions: tuple[CartDiscountAddition, ...] = ()


@dataclass(frozen=True)
class ProductCancelResponse(BaseKorailResponse):
    """여행상품 예약의 실제 취소 결과를 담습니다."""

    integrated_message_code: str | None = None


@dataclass(frozen=True)
class MaasCancelResponse(BaseKorailResponse):
    """지원하지 않는 결제 전 부가서비스 해제 응답 구조를 기록합니다."""

    integrated_message_code: str | None = None


@dataclass(frozen=True)
class CartAddRequest:
    """홀드를 장바구니에 추가할 PNR 입력을 구성합니다.

    PNR은 ``hidPnrNo``로 보내며, 비어 있으면 요청을 보내기 전에 ``KorailProtocolError``가 발생합니다."""

    # 자체 필드는 hidPnrNo 하나입니다 (AddCartListIn.java:25-30,79; NetworkApi.java:265-267).

    pnr_no: str


@dataclass(frozen=True)
class SelfCheckInRegisterResponse(BaseKorailResponse):
    """셀프 체크인 등록 결과를 담습니다.

    ``message_id``(``msgId``)는 ``null``일 수 있으며 앱은 이 값을 쓰지 않습니다. 응답에 ``msgId`` 키가 없으면
    ``KorailProtocolError``가 발생합니다."""

    # checkin.reg.do. msgId 는 필수·nullable 이며 앱은 읽지 않습니다(SelfCheckInRegisterOut.java:47-52).

    message_id: str | None = None


@dataclass(frozen=True)
class SelfCheckInCancelResponse(BaseKorailResponse):
    """셀프 체크인 취소 결과를 담습니다.

    ``message_id``(``msgId``)는 응답에 없으면 ``None``입니다."""

    # checkin.cnc.do. msgId 는 선택입니다(SelfCheckInCancelOut.java:50-56).

    message_id: str | None = None


@dataclass(frozen=True)
class DeliveredTicketRetrievalResponse(BaseKorailResponse):
    """대리수령으로 전달한 승차권을 회수한 결과를 담습니다.

    ``process_flags``에는 응답 행마다 처리 결과 플래그(``prsFlg``)가 들어 있습니다. 응답에 목록(``prsList``)이 없거나
    행에 ``prsFlg``가 없으면 ``KorailProtocolError``가 발생합니다."""

    # tk.pbpWdrw.do. prsList 는 필수이고 각 행의 prsFlg 도 필수입니다(RetrieveTicketOut.java:54-59, Prs.java:46-50).

    process_flags: tuple[str, ...] = ()
