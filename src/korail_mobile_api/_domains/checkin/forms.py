# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대리수령·셀프 체크인 폼입니다. 조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ..._core.validation import _required_mutation_text, _required_text
from ..._core.wire import _device_version_key
from ...config import KorailConfig
from ...errors import KorailProtocolError
from ..payments.models import RefundTicketDetailResponse
from ..tickets.forms import OriginalTicketReference, _exact_original_ticket_reference, _ticket_reference_tuple
from .models import PbpAcceptanceTicket, SelfCheckInSeat


def _ticket_return_number(reference: OriginalTicketReference) -> str:
    ticket = _exact_original_ticket_reference(reference)
    return "-".join(
        (
            ticket.sale_window_no,
            ticket.sale_date,
            ticket.sale_sequence,
            ticket.return_password,
        )
    )


def build_delivery_recipient_form(
    ticket: OriginalTicketReference,
) -> dict[str, str]:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    reference = _exact_original_ticket_reference(ticket)
    return {
        "saleWctNo": reference.sale_window_no,
        "saleDt": reference.sale_date,
        "saleSqno": reference.sale_sequence,
        "tkRetPwd": reference.return_password,
    }


def build_pbp_acceptance_specification_form(
    tickets: Sequence[OriginalTicketReference],
) -> tuple[tuple[str, str | int], ...]:
    references = _ticket_reference_tuple(tickets)
    return (
        ("tkCnt", len(references)),
        *(("tkRetNo", _ticket_return_number(ticket)) for ticket in references),
    )


def build_recent_delivery_history_form(customer_no: str) -> dict[str, str]:
    return {"custMgNo": _required_text(customer_no, "customer_no")}


def self_checkin_ticket_fields(
    detail: RefundTicketDetailResponse,
    *,
    sale_date_key: Literal["saleDt", "saleDd"],
) -> dict[str, str]:
    """가능 여부·등록은 saleDd 에 h_orgtk_ret_sale_dt 를, 정보·취소는 saleDt 에 h_sale_dt 를
    넣습니다(SelfCheckInInfoViewModel.java:102-108,224-225; SelfCheckInResultViewModel.java:111-112,249-250).
    jrnySqno 는 첫 여정의 h_jrny_sqno 이며 여정이 없으면 뺍니다."""
    if not isinstance(detail, RefundTicketDetailResponse):
        raise KorailProtocolError("detail must be a RefundTicketDetailResponse from get_refund_ticket_detail")
    sale_date = detail.original_sale_date if sale_date_key == "saleDd" else detail.sale_date
    fields = {
        "saleWctNo": _required_text(detail.original_window_no, "original_window_no"),
        sale_date_key: _required_text(
            sale_date, "original_sale_date" if sale_date_key == "saleDd" else "sale_date"
        ),
        "saleSqno": _required_text(detail.original_sale_sequence, "original_sale_sequence"),
        "tkRetPwd": _required_text(detail.original_return_password, "original_return_password"),
    }
    journey_sequence = detail.journeys[0].journey_sequence if detail.journeys else None
    if journey_sequence is not None:
        fields["jrnySqno"] = journey_sequence
    return fields


def build_self_checkin_info_form(detail: RefundTicketDetailResponse) -> dict[str, str]:
    """셀프 체크인 정보 조회 폼입니다(SelfCheckInInfoIn.java:55)."""
    return self_checkin_ticket_fields(detail, sale_date_key="saleDt")


def build_self_checkin_seat_check_form(detail: RefundTicketDetailResponse, qr_code: str) -> dict[str, str]:
    """셀프 체크인 좌석 확인 폼입니다(SelfCheckInPossibleIn.java:56). qr_code 는 좌석 테이블의 QR 을 스캔한 문자열이며 승차권 자체의 h_qrcode 가
    아닙니다(SelfCheckInInfoRouteKt.java:241-254; strings.xml:3245-3247)."""
    return {
        "qrcode": _required_text(qr_code, "qr_code"),
        **self_checkin_ticket_fields(detail, sale_date_key="saleDd"),
    }


def build_self_checkin_register_form(
    config: KorailConfig,
    detail: RefundTicketDetailResponse,
    seat: SelfCheckInSeat,
) -> dict[str, str]:
    """좌석 칸은 좌석 확인(check_self_checkin_seat)의 행에서, 승차권 칸은 상세에서 옵니다 (SelfCheckInInfoViewModel.java:224-225;
    SelfCheckInRegisterIn.java:59). jrnySqno 는 좌석 행이 아닌 상세의 값입니다."""
    if not isinstance(seat, SelfCheckInSeat):
        raise KorailProtocolError("seat must be a SelfCheckInSeat from check_self_checkin_seat")
    return {
        **_device_version_key(config),
        "cpsNo": _required_mutation_text(seat.cps_no, field="cps_no", context="self check-in"),
        "scarNo": _required_mutation_text(seat.car_no, field="car_no", context="self check-in"),
        "seatNo": _required_mutation_text(seat.seat_no, field="seat_no", context="self check-in"),
        **self_checkin_ticket_fields(detail, sale_date_key="saleDd"),
    }


def build_self_checkin_cancel_form(config: KorailConfig, detail: RefundTicketDetailResponse) -> dict[str, str]:
    """칸은 정보 조회와 같습니다(SelfCheckInResultViewModel.java:111-112; SelfCheckInCancelIn.java:53)."""
    return {**_device_version_key(config), **self_checkin_ticket_fields(detail, sale_date_key="saleDt")}


def build_delivered_ticket_retrieval_form(
    config: KorailConfig,
    ticket: PbpAcceptanceTicket,
) -> dict[str, str | list[str]]:
    """앱은 첫 여정의 pbpRsvNo 로 묶은 승차권마다 한 번, 그 묶음의 pbpRsvNo 와 첫 승차권의 pnrNo 를
    보냅니다(DeliveredTicketViewModel.java:185-205,283). pbpCnt 는 쌍의 수 1 이고, 두 목록은 FieldMap 뒤의 @Field 반복 키입니다
    (NetworkApi.java:642-644)."""
    if not isinstance(ticket, PbpAcceptanceTicket):
        raise KorailProtocolError("ticket must be a PbpAcceptanceTicket from get_pbp_acceptance_specifications")
    if not ticket.journeys:
        raise KorailProtocolError("KORAIL delivered ticket retrieval needs the ticket's first journey")
    context = "delivered ticket retrieval"
    return {
        **_device_version_key(config),
        "pbpCnt": "1",
        "pbpRsvNo": [
            _required_mutation_text(
                ticket.journeys[0].pbp_reservation_no, field="pbp_reservation_no", context=context
            )
        ],
        "pnrNo": [_required_mutation_text(ticket.pnr_no, field="pnr_no", context=context)],
    }
