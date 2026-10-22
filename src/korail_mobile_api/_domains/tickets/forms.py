# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정 조회 입력과 폼입니다. 조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypeAlias

from ..._core.validation import _ascii_digits, _calendar_date, _int_text, _optional_text, _required_text
from ...config import KorailConfig
from ...errors import KorailProtocolError

TICKET_LIST_MODE_ACTIVE = "1"


def build_ticket_list_form(
    config: KorailConfig,
    page_no: int,
    *,
    mode: str = TICKET_LIST_MODE_ACTIVE,
    boarding_date_from: str = "",
    boarding_date_to: str = "",
) -> dict[str, str]:
    """목록 종류·날짜·쪽번호를 보정하지 않으며 mode 의미는 관측값입니다(MyTicketListIn.java:62; 호출 리터럴 보호됨)."""
    if not isinstance(mode, str) or not mode:
        raise KorailProtocolError("ticket list mode must be a non-empty string")
    if type(page_no) is not int:
        raise KorailProtocolError("page_no must be an integer")
    # 키 순서는 MyTicketListIn 합성 생성자(MyTicketListIn.java:62)의 선언 순서입니다.
    return {
        "txtIndex": mode,
        "h_abrd_dt_from": boarding_date_from,
        "h_abrd_dt_to": boarding_date_to,
        "txtDeviceId": config.advertising_id,
        "hiduserYn": "Y",
        "h_page_no": str(page_no),
    }


#: 마일리지 원장입니다. ``"1"``은 KTX 마일리지, ``"2"``는 레일포인트입니다.
KorailMileageLedger = Literal["1", "2"]

#: 마일리지 증감 구분입니다. ``"0"``은 전체, ``"1"``은 적립, ``"2"``는 사용입니다.
KorailMileageMovement = Literal["0", "1", "2"]

#: 두 값 모두 라이브로는 동작하지만 7.0.6 출처가 없는 **미출처** 상수입니다.
KORAIL_MILEAGE_LEDGER_KTX: KorailMileageLedger = "1"
KORAIL_MILEAGE_LEDGER_RAIL_POINT: KorailMileageLedger = "2"

KORAIL_MILEAGE_MOVEMENT_ALL: KorailMileageMovement = "0"
KORAIL_MILEAGE_MOVEMENT_EARNED: KorailMileageMovement = "1"
KORAIL_MILEAGE_MOVEMENT_SPENT: KorailMileageMovement = "2"

_KORAIL_MILEAGE_LEDGERS = frozenset({KORAIL_MILEAGE_LEDGER_KTX, KORAIL_MILEAGE_LEDGER_RAIL_POINT})
_KORAIL_MILEAGE_MOVEMENTS = frozenset(
    {
        KORAIL_MILEAGE_MOVEMENT_ALL,
        KORAIL_MILEAGE_MOVEMENT_EARNED,
        KORAIL_MILEAGE_MOVEMENT_SPENT,
    }
)


@dataclass(frozen=True)
class MileageHistoryRequest:
    """마일리지 내역의 기간·종류·페이지 조건을 구성합니다.

    기본값은 KTX 마일리지 원장(``"1"``), 전체 증감(``"0"``), 1페이지입니다. ``start_date``와 ``end_date``는 ``YYYYMMDD``
    형식이어야 하고 시작일이 종료일보다 늦으면 안 됩니다. 이 검사는 요청을 보내기 전에 합니다."""

    # 앱 근거: NetworkApi.java:274.

    start_date: str
    end_date: str
    ledger: KorailMileageLedger = KORAIL_MILEAGE_LEDGER_KTX
    movement: KorailMileageMovement = KORAIL_MILEAGE_MOVEMENT_ALL
    page_no: int = 1


def build_mileage_history_form(
    request: MileageHistoryRequest,
) -> dict[str, str]:
    if request.ledger not in _KORAIL_MILEAGE_LEDGERS:
        raise KorailProtocolError(
            "ledger must be KORAIL_MILEAGE_LEDGER_KTX or KORAIL_MILEAGE_LEDGER_RAIL_POINT"
        )
    if request.movement not in _KORAIL_MILEAGE_MOVEMENTS:
        raise KorailProtocolError(
            "movement must be one of KORAIL_MILEAGE_MOVEMENT_ALL, "
            "KORAIL_MILEAGE_MOVEMENT_EARNED, KORAIL_MILEAGE_MOVEMENT_SPENT"
        )
    start_date = _ascii_digits(request.start_date, "start_date", lengths=frozenset({8}))
    end_date = _ascii_digits(request.end_date, "end_date", lengths=frozenset({8}))
    if start_date > end_date:
        raise KorailProtocolError("start_date must not be after end_date")
    return {
        "pontTpVal": request.ledger,
        "qryDvVal": request.movement,
        "qryStDt": start_date,
        "qryClsDt": end_date,
        # 앱은 보호된 상수를 씁니다(MileageHistoryViewModelKt.java:11).
        "pgPrCnt": "20",
        "nowPgNo": _int_text(request.page_no, "page_no"),
    }


@dataclass(frozen=True)
class OriginalTicketReference:
    """원표 조회와 환불·대리수령 같은 후속 처리에 쓰는 반환 식별자를 구성합니다.

    네 필드 모두 비어 있지 않은 문자열이어야 하며, 아니면 ``KorailProtocolError``가 발생합니다. ``sale_date``의 형식은
    메서드마다 다릅니다. 수령자·대리수령 조회 두 메서드는 승차권의 ``sale_date``(``YYYYMMDD``)를 받고, 그 밖의 메서드는
    ``return_sale_date``(``MMDD``)를 받습니다. 메서드 사이에 값을 섞어 쓰지 마세요."""

    # 반환 경로는 MMDD, 수령자·PBP 경로는 YYYYMMDD 를 사용합니다(실서버 관측).

    sale_window_no: str
    sale_date: str
    sale_sequence: str
    return_password: str

    def __post_init__(self) -> None:
        for value, name in (
            (self.sale_window_no, "sale_window_no"),
            (self.sale_date, "sale_date"),
            (self.sale_sequence, "sale_sequence"),
            (self.return_password, "return_password"),
        ):
            _required_text(value, name)


def _exact_original_ticket_reference(
    reference: OriginalTicketReference,
) -> OriginalTicketReference:
    if not isinstance(reference, OriginalTicketReference):
        raise KorailProtocolError("ticket must be an OriginalTicketReference")
    return reference


def _ticket_reference_tuple(
    tickets: Sequence[OriginalTicketReference],
) -> tuple[OriginalTicketReference, ...]:
    if isinstance(tickets, (str, bytes)) or not isinstance(tickets, Sequence):
        raise KorailProtocolError("tickets must be a sequence of OriginalTicketReference")
    if not tickets:
        raise KorailProtocolError("tickets must contain at least one reference")
    for ticket in tickets:
        _exact_original_ticket_reference(ticket)
    return tuple(tickets)


def build_original_ticket_inquiry_form(
    tickets: Sequence[OriginalTicketReference],
    *,
    ticket_count: int | None = None,
) -> tuple[tuple[str, str | int], ...]:
    """앱 근거: NetworkApi.java:235. 키 접두사·순서: ChangeOrtkInfo.java:52. 보호 리터럴은 미확인입니다."""
    references = _ticket_reference_tuple(tickets)
    if ticket_count is None:
        count = len(references)
    elif type(ticket_count) is not int:
        raise KorailProtocolError("ticket_count must be an integer")
    else:
        count = ticket_count
    # 앱 호출별 값이 달라 길이 일치를 강제하지는 않습니다.
    rows: list[tuple[str, str | int]] = [("tkCnt", count)]
    for index, ticket in enumerate(references, start=1):
        rows.append((f"ogtkSaleWctNo_{index}", ticket.sale_window_no))
        rows.append((f"ogtkSaleDd_{index}", ticket.sale_date))
        rows.append((f"ogtkSaleSqno_{index}", ticket.sale_sequence))
        rows.append((f"ogtkRetPwd_{index}", ticket.return_password))
    return tuple(rows)


# 라이브 기록에 따른 값입니다. PsrmType.java:19-29 의 리터럴은 보호돼 있습니다.
#: 자율 좌석 변경 조회의 객실 등급 문자열입니다. 알려진 값은 ``"1"``(일반실), ``"2"``(특실)이며 다른 서버 코드도 그대로 받습니다.
KorailSelfSeatChangeRoomClassCode: TypeAlias = str


@dataclass(frozen=True)
class SelfSeatChangeInfoRequest:
    """자율 좌석 변경 대상 역·사유 조회 입력을 구성합니다.

    앱처럼 승차권의 운행일·열차 번호·출발역·도착역을 그대로 넣습니다. ``room_class_code``가 ``None``이면 객실 등급을 보내지
    않습니다. ``run_date``는 8자리 숫자, ``train_no``는 5자리 이하 숫자여야 하고 역 코드는 비어 있으면 안 되며, 아니면
    ``KorailProtocolError``가 발생합니다."""

    # 앱 근거: NetworkApi.java:806-808; SeatAvailabilityIn.java:26-30,55. 앱은 승차권의 식별자를 복사하고 객실 값이 null 이
    # 아닐 때 요청합니다(SelfSeatChangeOptionViewModel.java:342-344).

    run_date: str
    train_no: str
    departure_station_code: str
    arrival_station_code: str
    room_class_code: KorailSelfSeatChangeRoomClassCode | None = None

    def __post_init__(self) -> None:
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(self.train_no, "train_no", maximum_length=5)
        _required_text(
            self.departure_station_code,
            "departure_station_code",
        )
        _required_text(self.arrival_station_code, "arrival_station_code")
        # 객실 코드는 허용목록으로 거르지 않습니다: 앱 DTO 는 String 이고 코드 리터럴은 보호돼 있습니다(PsrmType.java:19-29).
        if self.room_class_code is not None:
            _required_text(self.room_class_code, "room_class_code")


def build_self_seat_change_info_form(
    request: SelfSeatChangeInfoRequest,
) -> dict[str, str]:
    form = {
        "runDt": request.run_date,
        "trnNo": request.train_no,
        "dptRsStnCd": request.departure_station_code,
        "arvRsStnCd": request.arrival_station_code,
    }
    if request.room_class_code is not None:
        form["psrmClCd"] = request.room_class_code
    return form


def build_delay_certificate_form(ticket: OriginalTicketReference) -> dict[str, str]:
    """앱은 승차권 상세의 h_orgtk_wct_no·h_orgtk_ret_sale_dt·h_orgtk_sale_sqno·h_orgtk_ret_pwd 를
    넣습니다(DelayCertificateViewModel.java:94; DelayCertificateIn.java:52). sale_date 에는 return_sale_date 를
    쓰십시오."""
    reference = _exact_original_ticket_reference(ticket)
    return {
        "ogtkSaleWctNo": _required_text(reference.sale_window_no, "sale_window_no"),
        "ogtkSaleDd": _required_text(reference.sale_date, "sale_date"),
        "ogtkSaleSqno": _required_text(reference.sale_sequence, "sale_sequence"),
        "ogtkRetPwd": _required_text(reference.return_password, "return_password"),
    }


def build_delay_return_receipt_form(ticket: OriginalTicketReference) -> dict[str, str]:
    """값의 출처는 지연확인증과 같습니다(DelayReturnReceiptViewModel.java:88; TicketReceiptRouteKt.java:309-313;
    DelayReturnReceiptIn.java:52)."""
    reference = _exact_original_ticket_reference(ticket)
    return {
        "saleWctNo": _required_text(reference.sale_window_no, "sale_window_no"),
        "saleDd": _required_text(reference.sale_date, "sale_date"),
        "saleSqno": _required_text(reference.sale_sequence, "sale_sequence"),
        "tkRetPwd": _required_text(reference.return_password, "return_password"),
    }


def build_delay_discount_ticket_form(
    departure_date_to: str,
) -> dict[str, str]:
    # dptDtTo 속성의 전송 키는 명시적 h_page_no(DelayDiscountViewIn.java:50,77). 관측: 날짜·1·다른 후보 키·키 생략 모두 같은 빈 SUCC.
    return {"h_page_no": _ascii_digits(departure_date_to, "departure_date_to", lengths=frozenset({8}))}


def build_discount_coupon_form(
    page_no: int = 1,
    pnr_no: str = "",
) -> dict[str, str]:
    return {
        "txtSelPage": _int_text(page_no, "page_no"),
        "pnrNo": _optional_text(pnr_no, "pnr_no"),
    }


def build_multi_child_discount_target_form(
    departure_date: str,
) -> dict[str, str]:
    # 검증한 입력을 그대로 보냅니다. strftime 의 %Y 는 glibc 에서 1000년 미만을 0 으로 채우지 않습니다.
    _calendar_date(departure_date, "departure_date")
    return {"dptDt": departure_date}


def build_korail_point_summary_form() -> dict[str, str]:
    """앱 근거: NetworkApi.java:515."""
    return {"point_dv_cd": "0"}


def build_customer_trip_info_form(customer_no: str) -> dict[str, str]:
    # 앱의 두 값은 보호돼 있습니다(HomeViewModel.java:4335).
    return {
        "custMgNo": _required_text(customer_no, "customer_no"),
        "medDvCd": "03",
        "regSqno": "0",
    }


def build_trip_change_date_form(departure_date: str) -> dict[str, str]:
    # 달력 검증은 앱에 없는 라이브러리 검사입니다(앱은 날짜 선택기 값만 보냅니다). 라이브: 20260230·20261340 은 SUCC/API.I00000 에 tripChgDates 없이
    # 돌아왔고, 정상 날짜는 변경 가능일이 없어도 빈 tripChgDates 를 실었습니다(20250101·20991231 등).
    _calendar_date(departure_date, "departure_date")
    return {"tripChgDate": departure_date}


def build_ticket_receipt_form(
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
    txt_index: str | None = None,
) -> dict[str, str]:
    form = {
        # 여기서 막지 않으면 TicketListTicket.sale_date 를 그대로 넘긴 호출자가 원인이 모호한 서버 오류를 받습니다.
        "h_orgtk_sale_dt": _ascii_digits(sale_date, "sale_date", lengths=frozenset({4})),
        "h_orgtk_wct_no": _required_text(window_no, "window_no"),
        "h_orgtk_sale_sqno": _required_text(
            sale_sequence,
            "sale_sequence",
        ),
        "h_orgtk_tk_ret_pwd": _required_text(
            return_password,
            "return_password",
        ),
    }
    if txt_index is not None:
        if not isinstance(txt_index, str):
            raise KorailProtocolError("txt_index must be a string or None")
        if txt_index.strip():
            form["txtIndex"] = txt_index
    return form
