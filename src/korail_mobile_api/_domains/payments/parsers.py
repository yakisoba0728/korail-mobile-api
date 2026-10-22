# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""결제·환불 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _nested_rows,
    _optional_mapping,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from ..reservations.parsers import _response_mapping, _row
from .models import (
    DiscountCardOnTicket,
    DiscountCardSection,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketResponse,
    RefundTicketSeat,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
    ReservationPaymentSettlement,
    ReservationPaymentTableSeat,
    ReservationPaymentTicket,
    StationRefundExecutionResponse,
    StationRefundOriginalTicket,
    StationRefundVerificationResponse,
)


@_preserve_read_raw
def parse_refund_commission_response(raw: Mapping[str, object]) -> RefundCommissionResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(RefundCommissionResponse, raw, "refund commission", **_response_fields(raw))


def _discount_card_on_ticket(raw: Mapping[str, object]) -> DiscountCardOnTicket | None:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    info = _optional_mapping(raw, "dcnt_crd_info")
    if info is None:
        return None
    sections = wire_models(DiscountCardSection, _rows(info, "appSegList"), "discount card section")
    return wire_model(DiscountCardOnTicket, info, "discount card", sections=sections, raw=info)


@_preserve_read_raw
def parse_refund_ticket_detail_response(raw: Mapping[str, object]) -> RefundTicketDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = tuple(
        wire_model(
            RefundTicketJourney,
            journey,
            "refund ticket journey",
            seats=wire_models(RefundTicketSeat, _rows(journey, "tk_seat_info"), "refund ticket seat"),
            raw=journey,
        )
        for journey in _nested_rows(raw, "ticket_infos", "ticket_info")
    )
    # 네 키는 명시적 별칭이 없어 속성명으로 추정합니다. 보호된 descriptor 로 확인한 전송 키가 아닙니다.
    return wire_model(
        RefundTicketDetailResponse,
        raw,
        "refund ticket detail",
        passenger_names=tuple(_rows(raw, "psgNmList")),
        seat_tickets=tuple(_rows(raw, "seatTicketList")),
        limousine=_optional_mapping(raw, "limousine"),
        delay_details=tuple(_rows(raw, "dtlList")),
        journeys=journeys,
        discount_card=_discount_card_on_ticket(raw),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_refund_ticket_response(raw: Mapping[str, object]) -> RefundTicketResponse:
    """stlList 는 키 필수·값 nullable 이고 각 행의 stl_mns_cd 는 필수입니다."""
    copied = _response_mapping(raw)
    if "stlList" not in copied:
        raise KorailProtocolError("KORAIL refund stlList is required")
    rows = copied["stlList"]
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL refund stlList must be a list or null")
    codes: list[str] = []
    for value in rows or ():
        try:
            row = _row(value, "refund settlement")
            code = _strict_scalar_string(row, "stl_mns_cd", "refund settlement")
            if code is None:
                raise KorailProtocolError("KORAIL refund stl_mns_cd is required and non-null")
        except KorailProtocolError as error:
            error.raw = value
            raise
        codes.append(code)
    return RefundTicketResponse(
        **_response_fields(copied),
        settlement_method_codes=tuple(codes),
        settlement_list_is_null=rows is None,
    )


@_preserve_read_raw
def parse_station_refund_verification_response(raw: Mapping[str, object]) -> StationRefundVerificationResponse:
    context = "station refund Orgtkinfo"
    copied = _response_mapping(raw)
    rows = copied.get("orgtkinfo_list", [])
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station refund orgtkinfo_list must be a list")
    original_tickets: list[StationRefundOriginalTicket] = []
    for value in rows or ():
        row = _row(value, context)
        pnr_no = _strict_scalar_string(row, "pnr_no", context)
        if not pnr_no:
            raise KorailProtocolError("KORAIL station refund Orgtkinfo.pnr_no is required")
        original_tickets.append(
            wire_model(StationRefundOriginalTicket, row, context, pnr_no=pnr_no, raw=dict(row))
        )
    return wire_model(
        StationRefundVerificationResponse,
        copied,
        "station refund verification",
        original_tickets=tuple(original_tickets),
        original_ticket_list_is_null=rows is None,
        **_response_fields(copied),
    )


@_preserve_read_raw
def parse_station_refund_execution_response(raw: Mapping[str, object]) -> StationRefundExecutionResponse:
    copied = _response_mapping(raw)
    return wire_model(
        StationRefundExecutionResponse, copied, "station refund execution", **_response_fields(copied)
    )


@_preserve_read_raw
def parse_reservation_payment_response(raw: Mapping[str, object]) -> ReservationPaymentResponse:
    """결제 결과의 중첩 목록을 관대하게 읽으며 성공 여부는 판정하지 않습니다. 이미 승인됐을 수 있으므로 파싱 결과만 보고 결제를 재전송하지 마십시오."""
    copied = _response_mapping(raw)
    context = "reservation payment"
    return wire_model(
        ReservationPaymentResponse,
        copied,
        context,
        coupons=wire_models(ReservationPaymentCoupon, _rows(copied, "tk_coupon_info"), context, copy_raw=True),
        tickets=wire_models(
            ReservationPaymentTicket, _nested_rows(copied, "tk_infos", "tk_info"), context, copy_raw=True
        ),
        settlements=wire_models(
            ReservationPaymentSettlement, _nested_rows(copied, "stl_infos", "stl_info"), context, copy_raw=True
        ),
        table_seats=wire_models(
            ReservationPaymentTableSeat,
            _nested_rows(copied, "tbl_seat_infos", "tbl_seat_info"),
            context,
            copy_raw=True,
        ),
        **_response_fields(copied),
    )
