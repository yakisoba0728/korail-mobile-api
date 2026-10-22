# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대리수령·셀프 체크인 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _optional_read_rows,
    _preserve_read_raw,
    _required_read_rows,
    _response_fields,
    _row,
    _validate_strict_read_envelope,
    required_str,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from ..reservations.parsers import _response_mapping
from .models import (
    DeliveredTicketRetrievalResponse,
    DeliveryRecipientResponse,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    RecentDeliveryHistoryResponse,
    RecentDeliveryRecipient,
    SelfCheckInCancelResponse,
    SelfCheckInInfoResponse,
    SelfCheckInRegisterResponse,
    SelfCheckInSeat,
    SelfCheckInSeatCheckResponse,
)


@_preserve_read_raw
def parse_delivery_recipient_response(raw: Mapping[str, object]) -> DeliveryRecipientResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(DeliveryRecipientResponse, raw, "delivery recipient", **_response_fields(raw))


@_preserve_read_raw
def parse_pbp_acceptance_specification_response(
    raw: Mapping[str, object],
) -> PbpAcceptanceSpecificationResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _required_read_rows(raw, "tkList", "PBP acceptance"):
        journeys = []
        for journey in _required_read_rows(ticket, "jrnyList", "PBP ticket"):
            seats = wire_models(
                PbpAcceptanceSeat,
                _required_read_rows(journey, "seatList", "PBP journey"),
                "PBP acceptance seat",
            )
            journeys.append(wire_model(PbpAcceptanceJourney, journey, "PBP journey", seats=seats, raw=journey))
        tickets.append(
            wire_model(PbpAcceptanceTicket, ticket, "PBP ticket", journeys=tuple(journeys), raw=ticket)
        )
    return PbpAcceptanceSpecificationResponse(tickets=tuple(tickets), **_response_fields(raw))


@_preserve_read_raw
def parse_recent_delivery_history_response(raw: Mapping[str, object]) -> RecentDeliveryHistoryResponse:
    _validate_strict_read_envelope(raw)
    # acepList 는 키 필수·값 nullable 이고 null 은 빈 목록입니다.
    if "acepList" not in raw:
        raise KorailProtocolError("KORAIL recent delivery history field acepList is required")
    recipients = wire_models(
        RecentDeliveryRecipient,
        _optional_read_rows(raw, "acepList", "recent delivery history"),
        "recent delivery recipient",
    )
    return wire_model(
        RecentDeliveryHistoryResponse,
        raw,
        "recent delivery history",
        recipients=recipients,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_self_checkin_seat_check_response(raw: Mapping[str, object]) -> SelfCheckInSeatCheckResponse:
    _validate_strict_read_envelope(raw)
    if "consList" not in raw:
        raise KorailProtocolError("KORAIL self check-in seat check field consList is required")
    seats = wire_models(
        SelfCheckInSeat, _optional_read_rows(raw, "consList", "self check-in seat check"), "self check-in seat"
    )
    return SelfCheckInSeatCheckResponse(seats=seats, **_response_fields(raw))


@_preserve_read_raw
def parse_self_checkin_info_response(raw: Mapping[str, object]) -> SelfCheckInInfoResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(SelfCheckInInfoResponse, raw, "self check-in info", **_response_fields(raw))


@_preserve_read_raw
def parse_self_checkin_register_response(raw: Mapping[str, object]) -> SelfCheckInRegisterResponse:
    data = _response_mapping(raw)
    return wire_model(SelfCheckInRegisterResponse, data, "self check-in register", **_response_fields(data))


@_preserve_read_raw
def parse_self_checkin_cancel_response(raw: Mapping[str, object]) -> SelfCheckInCancelResponse:
    data = _response_mapping(raw)
    return wire_model(SelfCheckInCancelResponse, data, "self check-in cancel", **_response_fields(data))


@_preserve_read_raw
def parse_delivered_ticket_retrieval_response(raw: Mapping[str, object]) -> DeliveredTicketRetrievalResponse:
    context = "delivered ticket retrieval"
    data = _response_mapping(raw)
    rows = data.get("prsList")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL delivered ticket retrieval field prsList must be a list")
    flags = []
    for value in rows:
        try:
            flags.append(required_str(_row(value, context), "prsFlg", context))
        except KorailProtocolError as error:
            error.raw = value
            raise
    return DeliveredTicketRetrievalResponse(**_response_fields(data), process_flags=tuple(flags))
