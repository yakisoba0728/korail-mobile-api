# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권 반환 식별자와 셀프 체크인 응답에서 조회 폼을 구성합니다."""

from __future__ import annotations

from typing import Literal

from ._read_payload_validation import _ascii_digits, _required_text
from .errors import KorailProtocolError
from .read_models import RefundTicketDetailResponse


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
