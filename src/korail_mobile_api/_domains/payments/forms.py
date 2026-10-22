# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""결제·환불 입력과 폼입니다. 입력 모델의 생성은 전송하지 않습니다. CardPayment 출력은 숨기며 다른 raw·repr은 마스킹하지 않습니다.

DTO 필드·배열 순서와 빈 값 생략은 실제 전송에 영향을 주므로 유지합니다."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
from datetime import datetime, timedelta, timezone
from typing import Literal, NoReturn

from ..._core.validation import _optional_text, _required_mutation_text, _required_text
from ..._core.wire import _device_version_key, _is_ascii_digits
from ...config import KorailConfig
from ...constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION, KorailReservationJobType
from ...errors import KorailInvalidInputError
from ..reservations.forms import _successful_hold_pnr
from ..reservations.models import ReservationHoldResponse
from ..tickets.forms import OriginalTicketReference, _exact_original_ticket_reference
from .models import (
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    StationRefundVerificationResponse,
    _RefundCommissionContext,
)


def _require_every_field(
    request: StationRefundVerificationRequest | StationRefundExecutionRequest,
    step: str,
) -> None:
    for field_ in fields(request):
        value = getattr(request, field_.name)
        if not isinstance(value, str) or not value.strip():
            raise KorailInvalidInputError(f"KORAIL station refund {step} requires {field_.name}")


@dataclass(frozen=True)
class StationRefundVerificationRequest:
    """역에서 발권한 승차권의 환불 확인에 필요한 이름과 반환 식별자를 구성합니다.

    ``return_no_1``~``return_no_4``에는 반환번호 네 칸을 차례로 넣습니다. 모든 필드는 비어 있지 않은
    문자열이어야 하며, 아니면 ``KorailInvalidInputError``가 발생합니다."""

    customer_name: str
    return_no_1: str
    return_no_2: str
    return_no_3: str
    return_no_4: str

    def __post_init__(self) -> None:
        _require_every_field(self, "verification")


@dataclass(frozen=True)
class StationRefundExecutionRequest:
    """역에서 발권한 승차권의 환불 실행 입력을 구성합니다.

    보통 ``from_verification()``으로 환불 확인 결과에서 만듭니다. 만들기만 해서는 요청을 보내지 않으며, 실제 환불은
    ``KorailClient.execute_station_ticket_refund()``를 호출해야 합니다. 모든 필드는 비어 있지 않은 문자열이어야 하며,
    아니면 ``KorailInvalidInputError``가 발생합니다."""

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

        확인 응답이 성공(``"SUCC"``)이 아니거나 원표가 없거나 옮겨 담을 값이 비어 있으면 ``KorailInvalidInputError``가
        발생합니다."""
        if verification.str_result != "SUCC" or not verification.original_tickets:
            raise KorailInvalidInputError(
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
        parts: dict[str, str] = {}
        missing: list[str] = []
        for name, value in echoed.items():
            if value and value.strip():
                parts[name] = value
            else:
                missing.append(name)
        if missing:
            raise KorailInvalidInputError(
                "KORAIL station refund verification is missing " + ", ".join(sorted(missing))
            )
        return cls(**parts, customer_phone=customer_phone, customer_name=customer_name)


# 숫자 모양 검사만으로 카드 유효성이나 비과금을 보장하지 않습니다. 앱의 칸별 길이 값은 보호돼 있습니다.
_CARD_FORMATS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("card_number", re.compile(r"[0-9]{13,16}"), "KORAIL payment card number must be 13 to 16 digits"),
    (
        "installment",
        re.compile(r"[0-9]{1,2}"),
        'KORAIL payment installment must be one or two digits, "0" for a lump sum',
    ),
    ("card_expire", re.compile(r"[0-9]{4}"), "KORAIL payment card_expire must be YYMM digits"),
    ("card_password", re.compile(r"[0-9]{2}"), "KORAIL payment requires the first two card password digits"),
)
_CARD_AUTH_FORMATS = {"J": re.compile(r"[0-9]{6}"), "S": re.compile(r"[0-9]{10}")}
_CARD_EXPIRY_MESSAGE = "KORAIL payment card has expired or has an invalid month"


@dataclass(frozen=True)
class CardPayment:
    """예약 결제에 사용할 카드 정보를 구성합니다.

    ``repr()``과 ``str()``은 모든 필드를 숨깁니다. 직접 속성과 명시적 직렬화에는
    실제 값이 남으며 결제 요청도 실제 값을 사용합니다. 형식은 만들 때, 유효기간 경과는 결제 요청 직전에 검사합니다."""

    card_number: str = field(repr=False)
    card_password: str = field(repr=False)
    card_expire: str = field(repr=False)
    birthday: str = field(repr=False)
    # evidence: app InstallmentViewModel.java:55,94-96 (INS_0; its value is protected, so "0" vs "00" is unconfirmed)
    #: 할부 개월 수입니다. 숫자 1~2자리이며 기본값 ``"0"``은 일시불입니다.
    installment: str = field(default="0", repr=False)
    #: 카드 종류입니다. ``"J"``(기본값)는 개인 카드, ``"S"``는 법인 카드입니다. 다른 값이면 ``KorailInvalidInputError``가
    #: 발생합니다.
    card_type: Literal["J", "S"] = field(default="J", repr=False)

    def __post_init__(self) -> None:
        # 메시지에 입력값을 싣지 않습니다.
        if not isinstance(self.card_type, str) or self.card_type not in _CARD_AUTH_FORMATS:
            raise KorailInvalidInputError('card_type must be "J" (personal) or "S" (corporate)')
        auth = (
            "birthday",
            _CARD_AUTH_FORMATS[self.card_type],
            "KORAIL payment card authentication value must be 6 or 10 digits",
        )
        for name, pattern, message in (*_CARD_FORMATS, auth):
            value = getattr(self, name)
            if not isinstance(value, str) or pattern.fullmatch(value) is None:
                raise KorailInvalidInputError(message)
        if not 1 <= int(self.card_expire[2:]) <= 12:
            raise KorailInvalidInputError(_CARD_EXPIRY_MESSAGE)


@dataclass(frozen=True)
class PaidTicket:
    """환불할 발권 승차권 한 장의 PNR과 반환 식별자를 구성합니다.

    보통 ``from_refund_detail()``로 승차권 상세 응답에서 만드세요. 환불 요청은 상세 응답의 판매일(``sale_date``)을 쓰고,
    수수료 조회는 원표 반환일을 쓰므로 두 값을 섞어 쓰지 마세요. ``refund()``에는 이 값과 함께 ``get_refund_commission()``의
    응답을 ``commission``으로 넘겨야 합니다. 앞의 다섯 필드가 비어 있으면 만들 때 ``KorailInvalidInputError``가 발생합니다."""

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
    #: 수수료를 조회한 원표의 반환일입니다. 현재 판매일(``sale_date``)과 구분하며 환불 전에 필요합니다.
    #: ``from_refund_detail()``은 상세의 ``original_sale_date``를 복사합니다.
    return_sale_date: str | None = field(default=None, repr=False, kw_only=True)
    #: 수수료 조회에 사용한 동반자 이름입니다. 동반자가 없으면 빈 문자열입니다.
    companion_name: str = field(default="", repr=False, kw_only=True)
    #: 수수료 조회에 사용한 동반자 증빙값입니다. 상세 팩토리는 동반자 생년월일을 복사합니다.
    companion_certificate_no: str = field(default="", repr=False, kw_only=True)

    def __post_init__(self) -> None:
        for name in ("pnr_no", "sale_date", "sale_window_no", "sale_sequence", "return_password"):
            _required_mutation_text(getattr(self, name), field=f"PaidTicket.{name}", context="refund")

    @classmethod
    def from_refund_detail(
        cls,
        detail: RefundTicketDetailResponse,
        *,
        train_no: str = "",
    ) -> PaidTicket:
        """승차권 상세 응답에서 환불 입력을 앱과 같은 방식으로 만듭니다.

        ``train_no``를 주지 않으면 첫 여정의 열차 번호를 씁니다. 상세 응답에 PNR, 판매일, 원표 창구번호·일련번호·반환
        비밀번호 중 빈 값이 있으면 ``KorailInvalidInputError``가 발생합니다."""
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
            raise KorailInvalidInputError(
                "KORAIL refund identity is incomplete; the ticket detail is "
                f"missing {', '.join(sorted(missing))}"
            )
        if not train_no and detail.journeys:
            train_no = detail.journeys[0].train_no or ""
        return cls(
            **parts,
            train_no=train_no,
            pbp_acceptance_target_flag=detail.pbp_acceptance_target_flag,
            return_sale_date=detail.original_sale_date,
            companion_name=detail.companion_name or "",
            companion_certificate_no=detail.companion_birth_date or "",
        )


@dataclass(frozen=True)
class PriceRecalculationRow:
    """예약 할인 재계산에 사용할 승객 한 행을 구성합니다.

    보통 ``PriceRecalculationRequest.for_hold()``가 홀드의 좌석마다 한 행씩 만듭니다. 값이 없는 칸은 ``None``이 아니라
    빈 문자열로 두세요. 모든 필드는 문자열이어야 하고 ``passenger_type_code``, ``room_class_code``,
    ``discount_kind_code``는 비어 있으면 안 됩니다. 이 검사는 요청을 보내기 전에 합니다."""

    passenger_type_code: str
    room_class_code: str
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

    pnr_no: str
    rows: tuple[PriceRecalculationRow, ...] = ()
    #: 비회원 고객번호입니다. 값이 있으면 비회원 구분과 함께 보내고, ``None``이면 보내지 않습니다.
    non_member_no: str | None = None
    cabin_class_code: str | None = None
    seat_attribute_code_2: str | None = None
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
        같은 개수여야 합니다. 홀드가 성공(``"SUCC"``)이 아니거나 PNR·좌석 행이 없거나 개수가 다르면 ``KorailInvalidInputError``가
        발생합니다."""
        pnr_no = hold.pnr_no
        if hold.str_result != "SUCC" or not isinstance(pnr_no, str) or not pnr_no.strip():
            raise KorailInvalidInputError("KORAIL price recalculation needs a successful hold with a PNR")
        # 재계산 결과는 결제 가능한 새 홀드로 돌아오므로 예약대기 홀드를 여기서 막습니다.
        if hold.payable is False:
            raise KorailInvalidInputError(
                "KORAIL price recalculation refuses a standby hold, which is never card-paid"
            )
        if isinstance(requested_discount_codes, str) or not isinstance(requested_discount_codes, Sequence):
            raise KorailInvalidInputError("requested_discount_codes must be a sequence with one code per seat")
        container = hold.journeys[0].raw.get("seat_infos") if hold.journeys else None
        seats = container.get("seat_info") if isinstance(container, Mapping) else None
        if not isinstance(seats, list) or not seats or not all(isinstance(seat, Mapping) for seat in seats):
            raise KorailInvalidInputError("KORAIL price recalculation needs the hold's first-journey seat rows")
        if len(requested_discount_codes) != len(seats):
            raise KorailInvalidInputError(
                f"KORAIL price recalculation needs one requested code per seat of the first journey "
                f"({len(seats)})"
            )

        def text(seat: Mapping[str, object], key: str) -> str:
            # 좌석 필드는 String 선언입니다. JSON 정수만 문자열로 받고 bool·객체 등은 보내지 않습니다.
            value = seat.get(key)
            if value is None or isinstance(value, str):
                return value or ""
            if type(value) is int:
                try:
                    return str(value)
                except ValueError as exc:
                    error = KorailInvalidInputError(
                        f"KORAIL price recalculation seat field {key} is an integer too long to use"
                    )
                    error.raw = hold.raw
                    error.parser_raw = seat
                    raise error from exc
            raise KorailInvalidInputError(
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
class RefundCompanion:
    """환불 수수료 조회에 사용할 동반자 이름과 생년월일을 구성합니다.

    이름은 ``name``, 생년월일은 ``certificate_no``에 넣습니다. 동반자가 없으면 기본값(빈 문자열)을 그대로 두세요. 빈 값은
    요청에 싣지 않습니다."""

    name: str = ""
    certificate_no: str = ""

    def __post_init__(self) -> None:
        _optional_text(self.name, "name")
        _optional_text(self.certificate_no, "certificate_no")


def _exact_refund_companion(companion: RefundCompanion) -> RefundCompanion:
    if not isinstance(companion, RefundCompanion):
        raise KorailInvalidInputError("companion must be a RefundCompanion")
    return companion


def build_station_refund_verification_form(
    request: StationRefundVerificationRequest,
) -> dict[str, str]:
    if not isinstance(request, StationRefundVerificationRequest):
        raise KorailInvalidInputError(
            "KORAIL station refund verification requires an exact verification request"
        )
    return {
        "strName": request.customer_name,
        "retNo1": request.return_no_1,
        "retNo2": request.return_no_2,
        "retNo3": request.return_no_3,
        "retNo4": request.return_no_4,
    }


def build_refund_commission_form(
    ticket: OriginalTicketReference,
    companion: RefundCompanion = RefundCompanion(),
) -> dict[str, str]:
    """판매일 키 h_orgtk_ret_sale_dt 는 환불 실행의 h_orgtk_sale_dt 와 다릅니다."""
    reference = _exact_original_ticket_reference(ticket)
    party = _exact_refund_companion(companion)
    return {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        "h_comp_nm": party.name,
        "h_comp_cert_no": party.certificate_no,
    }


def build_refund_ticket_detail_form(
    ticket: OriginalTicketReference,
    *,
    from_purchase_history: bool = False,
    txt_index: str | None = None,
) -> dict[str, str]:
    reference = _exact_original_ticket_reference(ticket)
    if type(from_purchase_history) is not bool:
        raise KorailInvalidInputError("from_purchase_history must be a bool")
    form = {
        "h_orgtk_ret_sale_dt": reference.sale_date,
        "h_orgtk_wct_no": reference.sale_window_no,
        "h_orgtk_sale_sqno": reference.sale_sequence,
        "h_orgtk_ret_pwd": reference.return_password,
        # evidence: app MyTicketBaseViewModel.java:696 (chosen by a boolean; the literals are protected)
        "h_purchase_history": "Y" if from_purchase_history else "N",
    }
    if txt_index is not None:
        form["txtIndex"] = _required_text(txt_index, "txt_index")
    return form


_KST = timezone(timedelta(hours=9))


def _current_year_month() -> int:
    now = datetime.now(_KST)
    return now.year * 100 + now.month


# 라이브러리 정책이며 앱 기본값은 미확인입니다(2026-07 라이브 2건은 시퀀스를 모두 제공해 이 대체값을 검증하지 않았습니다).
_ABSENT_JOB_SEQUENCE = "000000"
# 실서버 홀드 45여정에는 변경번호 키가 없었고 목록으로 되읽으면 000 이었습니다. 보호 리터럴은 미확인입니다.
_ABSENT_RESERVATION_CHANGE_NO = "000"


def _echo_or(value: str | None, fallback: str) -> str:
    """홀드 값을 그대로 되울리며 숫자로 온 값의 앞자리 0 을 복원하지 않습니다."""
    return value if isinstance(value, str) and value.strip() else fallback


def build_card_payment_form(
    config: KorailConfig,
    hold: ReservationHoldResponse,
    card: CardPayment,
) -> dict[str, str]:
    """결제액은 received_amount이며 total_price로 대체하지 않습니다."""
    if not isinstance(card, CardPayment):
        raise KorailInvalidInputError("KORAIL payment requires a CardPayment")
    if not isinstance(hold, ReservationHoldResponse):
        raise KorailInvalidInputError("KORAIL payment requires an exact reservation hold response")
    if not hold.payable:
        raise KorailInvalidInputError(
            "KORAIL payment refuses a standby (예약대기) hold: the app saves its wait options instead of paying it"
        )
    unpaid_hold = "KORAIL payment requires a fresh successful unpaid hold with a PNR, window number, and numeric received amount"
    pnr_no = _successful_hold_pnr(hold, context=unpaid_hold)
    window_no = hold.window_no
    amount = hold.received_amount
    if not isinstance(window_no, str) or not window_no.strip() or not _is_ascii_digits(amount):
        raise KorailInvalidInputError(unpaid_hold)
    # 앱은 0원이면 카드 없이 발권하며, 라이브러리는 그 경로가 없으므로 0원 카드 결제를 보내지 않습니다.
    if not amount.lstrip("0"):
        raise KorailInvalidInputError(
            "KORAIL card payment refuses a zero-amount hold: the app issues it without a card"
        )
    # 앱처럼 결제 직전 시점으로 만료를 검사합니다. 형식은 CardPayment 를 만들 때 검사했습니다.
    expire = card.card_expire
    if _current_year_month() > (2000 + int(expire[:2])) * 100 + int(expire[2:]):
        raise KorailInvalidInputError(_CARD_EXPIRY_MESSAGE)
    form = _device_version_key(config)
    form.update(
        {
            "hidPnrNo": pnr_no,
            "hidWctNo": window_no,
            "hidTmpJobSqno1": _echo_or(hold.temporary_job_sequence_1, _ABSENT_JOB_SEQUENCE),
            "hidTmpJobSqno2": _echo_or(hold.temporary_job_sequence_2, _ABSENT_JOB_SEQUENCE),
            "hidRsvChgNo": _echo_or(
                hold.journeys[0].reservation_change_no if hold.journeys else None, _ABSENT_RESERVATION_CHANGE_NO
            ),
            # evidence: app PaymentMethodHelper.java:110-130 (grid count, method 1/02 and input way @ are protected, unresolved)
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
            # evidence: app PayViewModel.java:6600-6604 (member branch; the constant is protected, so "Y" is unconfirmed)
            "hiduserYn": "Y",
        }
    )
    return form


def _refund_echo_field(value: object, *, field: str) -> str:
    """국내 앱은 상세의 pbpAcepTgtFlg 를 전달하며 외국인 경로의 값은 보호돼 있습니다."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise KorailInvalidInputError(
            f"KORAIL refund {field} must be a string echoed from a prior server response"
        )
    return value


def _app_integer(value: object) -> int:
    """앱 TextHelper 의 int32·실패 시 0 규칙을 따르며 SDK의 기존 ASCII 검증은 유지합니다."""
    if value is None:
        return 0
    if not isinstance(value, str):
        raise KorailInvalidInputError(
            "KORAIL refund commission amounts must be strings read from get_refund_commission"
        )
    if re.fullmatch(r"[+-]?[0-9]+", value) is None:
        return 0
    digits = value.lstrip("+-").lstrip("0")
    # int32는 최대 10자리이므로 Python의 전역 정수 변환 한도에 의존하지 않습니다.
    if len(digits) > 10:
        return 0
    number = int(digits or "0") * (-1 if value.startswith("-") else 1)
    return number if -(2**31) <= number < 2**31 else 0


def _validated_refund_commission(ticket: PaidTicket, commission: object) -> RefundCommissionResponse:
    """수수료 응답의 로컬 조회 입력을 대조합니다. 금액 유효기간·서버 승인은 검증하지 않습니다."""
    if not isinstance(commission, RefundCommissionResponse):
        raise KorailInvalidInputError(
            "KORAIL refund requires the get_refund_commission response as commission="
        )

    def reject(message: str) -> NoReturn:
        error = KorailInvalidInputError(message)
        error.raw = commission.raw
        raise error

    if commission.str_result != "SUCC":
        reject("KORAIL refund requires a successful commission response")
    context = commission._request_context
    if not isinstance(context, _RefundCommissionContext):
        reject(
            "KORAIL refund requires a response bound by get_refund_commission; direct construction or parsing is not sufficient"
        )
    if not isinstance(ticket.return_sale_date, str) or not ticket.return_sale_date.strip():
        reject("KORAIL refund requires PaidTicket.return_sale_date from the original ticket")
    expected = _RefundCommissionContext(
        ticket.sale_window_no,
        ticket.return_sale_date,
        ticket.sale_sequence,
        ticket.return_password,
        ticket.companion_name,
        ticket.companion_certificate_no,
    )
    if context != expected:
        reject("KORAIL refund commission does not match the original ticket and companion")
    return commission


def build_refund_form(
    config: KorailConfig,
    ticket: PaidTicket,
    *,
    settle_mileage: bool = False,
    pbp_acceptance_target_flag: str | None = None,
    commission: RefundCommissionResponse,
    latitude: str | None = None,
    longitude: str | None = None,
) -> dict[str, str]:
    """수수료 확인값을 에코하고 보호된 ctlDvCd는 추측하지 않아 생략합니다."""
    if not isinstance(ticket, PaidTicket):
        raise KorailInvalidInputError("KORAIL refund requires a PaidTicket")
    commission = _validated_refund_commission(ticket, commission)
    # bool("N") 변환으로 마일리지 사용 의도가 뒤집히지 않도록 bool 만 받습니다.
    if not isinstance(settle_mileage, bool):
        raise KorailInvalidInputError("settle_mileage must be a bool")
    pbp_flag = _refund_echo_field(
        pbp_acceptance_target_flag
        if pbp_acceptance_target_flag is not None
        else ticket.pbp_acceptance_target_flag,
        field="pbp_acceptance_target_flag",
    )
    # 생성자 인자 순서가 아니라 write$Self 의 CommonIn-first 순서입니다.
    form = {
        **_device_version_key(config),
        "txtPnrNo": ticket.pnr_no,
        "h_orgtk_sale_dt": ticket.sale_date,
        "h_orgtk_sale_wct_no": ticket.sale_window_no,
        "h_orgtk_sale_sqno": ticket.sale_sequence,
        "h_orgtk_ret_pwd": ticket.return_password,
        "h_mlg_stl": "Y" if settle_mileage else "N",
    }
    # 승차권 상세 화면은 위 필드만 채우고 나머지는 null 입니다.
    if commission.ticket_return_times_division_code:
        form["tk_ret_tms_dv_cd"] = commission.ticket_return_times_division_code
    if ticket.train_no:
        form["trnNo"] = ticket.train_no
    # 앱은 사용 가능 마일리지가 수수료 이상일 때만 마일리지 정산을 묻습니다. 보호된 진행 플래그 비교값은 보지 않습니다.
    if settle_mileage and _app_integer(commission.usable_mileage) < _app_integer(commission.refund_fee):
        raise KorailInvalidInputError(
            "KORAIL refund cannot pay the fee with mileage: usable mileage is below the fee"
        )
    form["pbpAcepTgtFlg"] = pbp_flag
    for key, coordinate in (("latitude", latitude), ("longitude", longitude)):
        if coordinate is not None:
            form[key] = str(coordinate)
    return form


def build_station_refund_execution_form(
    config: KorailConfig,
    request: StationRefundExecutionRequest,
) -> dict[str, str]:
    if not isinstance(request, StationRefundExecutionRequest):
        raise KorailInvalidInputError("KORAIL station refund requires an exact execution request")
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
    form = _device_version_key(config)
    form.update((wire_name, getattr(request, attribute)) for wire_name, attribute in fields)
    return form


# Retrofit 은 @FieldMap 뒤에 @Field 목록을 선언 순서대로 붙입니다.
_PRICE_RECALCULATION_ROW_FIELDS: tuple[tuple[str, str], ...] = (
    ("psg_tp_dv_cd", "passenger_type_code"),
    ("psrm_cl_cd", "room_class_code"),
    ("dcnt_knd_cd1", "discount_kind_code"),
    ("hidDscpNo", "certificate_no"),
    ("hidDcntKndCd", "requested_discount_code"),
    ("hidFmlyNo", "family_sequence_no"),
)

# 네 선택 스칼라의 키는 속성명에서 추정했으며(serializer 이름은 보호됨) 실서버에서 검증하지 못했습니다.
_PRICE_RECALCULATION_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("txtPsrmClCd1", "cabin_class_code"),
    ("txtSeatAttCd2", "seat_attribute_code_2"),
    ("txtSeatAttCd4", "seat_attribute_code_4"),
    ("txtSeatAttCd5", "seat_attribute_code_5"),
)


def build_price_recalculation_form(
    config: KorailConfig,
    request: PriceRecalculationRequest,
) -> dict[str, str | list[str]]:
    """여섯 병렬 List 필드를 반복 키로 보냅니다."""
    if not isinstance(request, PriceRecalculationRequest):
        raise KorailInvalidInputError("KORAIL price recalculation requires an exact PriceRecalculationRequest")
    pnr_no = _required_mutation_text(request.pnr_no, field="pnr_no", context="price recalculation")
    rows = tuple(request.rows)
    if not rows or len(rows) > KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailInvalidInputError(
            f"KORAIL price recalculation needs 1 to {KORAIL_MAX_PASSENGERS_PER_RESERVATION} passenger rows"
        )

    columns: dict[str, list[str]] = {name: [] for name, _ in _PRICE_RECALCULATION_ROW_FIELDS}
    for row in rows:
        if not isinstance(row, PriceRecalculationRow):
            raise KorailInvalidInputError(
                "KORAIL price recalculation requires exact PriceRecalculationRow values"
            )
        for wire_name, attribute in _PRICE_RECALCULATION_ROW_FIELDS:
            value = getattr(row, attribute)
            # None 은 목록 전송에서 빠져 다른 병렬 목록과 인덱스가 어긋날 수 있으므로 문자열만 허용합니다.
            if type(value) is not str:
                raise KorailInvalidInputError(
                    f"KORAIL price recalculation row field {attribute} must be a string"
                )
            columns[wire_name].append(value)
        for attribute in (
            "passenger_type_code",
            "room_class_code",
            "discount_kind_code",
        ):
            if not getattr(row, attribute).strip():
                raise KorailInvalidInputError(
                    f"KORAIL price recalculation copies {attribute} off the held seat; it must not be empty"
                )

    form: dict[str, str | list[str]] = dict(_device_version_key(config))
    form["hidPnrNo"] = pnr_no
    # evidence: app ReservationJobId.java:20,42-45 (the job id is protected; the value follows live records)
    form["txtJobId"] = KorailReservationJobType.IMMEDIATE.value
    non_member_no = request.non_member_no
    if non_member_no is not None:
        if not isinstance(non_member_no, str) or not non_member_no.strip():
            raise KorailInvalidInputError(
                "KORAIL price recalculation non_member_no must be a non-empty string when present"
            )
        # evidence: app PayViewModel.java:6167-6168 (the key and "N" are protected and unconfirmed)
        form["hiduserYn"] = "N"
        form["hidCustNo"] = non_member_no
    form["txtPsgGridcnt"] = str(len(rows))
    for wire_name, attribute in _PRICE_RECALCULATION_SCALAR_FIELDS:
        value = getattr(request, attribute)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            raise KorailInvalidInputError(
                f"KORAIL price recalculation {attribute} must be a non-empty string when present"
            )
        form[wire_name] = value
    for wire_name, _ in _PRICE_RECALCULATION_ROW_FIELDS:
        form[wire_name] = columns[wire_name]
    return form
