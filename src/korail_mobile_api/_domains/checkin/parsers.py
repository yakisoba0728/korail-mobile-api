# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대리수령·셀프 체크인 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..._core.parsing import (
    _optional_read_rows,
    _optional_scalar_string,
    _preserve_read_raw,
    _required_integer,
    _required_read_rows,
    _required_read_strings,
    _response_fields,
    _strict_scalar_string,
    _validate_strict_read_envelope,
)
from ..._core.parsing import _response_fields as _base_fields
from ...errors import KorailProtocolError
from ..reservations.parsers import _response_mapping, _row
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

_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
    "return_password": "tkRetPwd",
}

_PBP_ACCEPTANCE_JOURNEY_FIELDS = {
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "journey_type_code": "jrnyTpCd",
    "member_division_name": "mbDvNm",
    "acceptance_kind_name": "pbpAcepKndNm",
    "pbp_reservation_no": "pbpRsvNo",
    "registered_date": "regDt",
    "withdrawal_possible_flag": "wdrwPsbFlg",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_SEAT_FIELDS = {
    "passenger_type_division_name": "psgTpDvNm",
    "room_class_code": "psrmClCd",
    "room_class_name": "psrmClNm",
    "seat_no": "seatNo",
}

_RECENT_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_flag": "acepCustMgFlg",
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "acceptance_customer_phone_2": "acepCustTeln2",
    "member_card_no": "mbCrdNo",
}


@_preserve_read_raw
def parse_delivery_recipient_response(
    raw: Mapping[str, Any],
) -> DeliveryRecipientResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    return DeliveryRecipientResponse(
        **_required_read_strings(
            raw,
            _DELIVERY_RECIPIENT_FIELDS,
            "delivery recipient",
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pbp_acceptance_specification_response(
    raw: Mapping[str, Any],
) -> PbpAcceptanceSpecificationResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket in _required_read_rows(raw, "tkList", "PBP acceptance"):
        journeys = []
        for journey in _required_read_rows(ticket, "jrnyList", "PBP ticket"):
            seats = []
            for seat in _required_read_rows(journey, "seatList", "PBP journey"):
                seats.append(
                    PbpAcceptanceSeat(
                        # Seat.java:53-59 는 마스크 31 로 다섯 필드 누락을 거절하므로 필수로 읽습니다.
                        **_required_read_strings(seat, _PBP_ACCEPTANCE_SEAT_FIELDS, "PBP acceptance seat"),
                        # scarNo 는 int 선언(Seat.java:35,53). 앱 Json 설정 리터럴이 보호돼 있어 인용된 설정만으로 quoted Int 허용 이유는
                        # 확정하지 않습니다 (NetworkServiceKt.java:15-31).
                        car_no=_required_integer(
                            seat,
                            "scarNo",
                            "PBP acceptance seat",
                        ),
                        raw=seat,
                    )
                )
            journeys.append(
                PbpAcceptanceJourney(
                    **_required_read_strings(
                        journey,
                        _PBP_ACCEPTANCE_JOURNEY_FIELDS,
                        "PBP journey",
                    ),
                    seats=tuple(seats),
                    raw=journey,
                )
            )
        tickets.append(
            PbpAcceptanceTicket(
                **_required_read_strings(
                    ticket,
                    _PBP_ACCEPTANCE_TICKET_FIELDS,
                    "PBP ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return PbpAcceptanceSpecificationResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_recent_delivery_history_response(
    raw: Mapping[str, Any],
) -> RecentDeliveryHistoryResponse:
    _validate_strict_read_envelope(raw)
    # RecentDeliveryHistoryOut.java:51-57 의 마스크 24 는 두 키를 필수로 둡니다. 실서버 응답에는 acepList 가 있고 chgePbpRsvNo 만 없었으므로
    # chgePbpRsvNo 만 선택으로 읽습니다. acepList 는 nullable List 라 null 은 빈 목록입니다.
    if "acepList" not in raw:
        raise KorailProtocolError("KORAIL recent delivery history field acepList is required")
    recipients = []
    for recipient in (
        _required_read_rows(raw, "acepList", "recent delivery history") if raw["acepList"] is not None else ()
    ):
        recipients.append(
            RecentDeliveryRecipient(
                **_required_read_strings(
                    recipient,
                    _RECENT_DELIVERY_RECIPIENT_FIELDS,
                    "recent delivery recipient",
                ),
                raw=recipient,
            )
        )
    return RecentDeliveryHistoryResponse(
        changed_acceptance_reservation_no=_optional_scalar_string(
            raw, "chgePbpRsvNo", "recent delivery history"
        ),
        recipients=tuple(recipients),
        **_response_fields(raw),
    )


_SELF_CHECKIN_SEAT_FIELDS = {
    "pnr_no": "pnrNo",
    "journey_sequence": "jrnySqno",
    "assignment_sequence": "asgnSqno",
    "run_date": "runDt",
    "train_no": "trnNo",
    "departure_construction_order": "dptStnConsOrdr",
    "departure_station_code": "dptRsStnCd",
    "arrival_construction_order": "arvStnConsOrdr",
    "arrival_station_code": "arvRsStnCd",
    "ticket_kind_code": "tkKndCd",
    "train_group_code": "trnGpCd",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "departure_datetime": "dptDttm",
    "arrival_datetime": "arvDttm",
    "cps_no": "cpsNo",
}


@_preserve_read_raw
def parse_self_checkin_seat_check_response(raw: Mapping[str, Any]) -> SelfCheckInSeatCheckResponse:
    _validate_strict_read_envelope(raw)
    if "consList" not in raw:
        raise KorailProtocolError("KORAIL self check-in seat check field consList is required")
    seats = tuple(
        SelfCheckInSeat(**_required_read_strings(row, _SELF_CHECKIN_SEAT_FIELDS, "self check-in seat"), raw=row)
        for row in _optional_read_rows(raw, "consList", "self check-in seat check")
    )
    return SelfCheckInSeatCheckResponse(seats=seats, **_response_fields(raw))


_SELF_CHECKIN_INFO_FIELDS = {
    "pnr_no": "pnrNo",
    "train_no": "trnNo",
    "departure_station_name": "dptRsStnNm",
    "departure_time": "dptTmQb",
    "arrival_station_name": "arvRsStnNm",
    "arrival_time": "arvTmQb",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "train_class_name": "stlbTrnClsfNm",
    "checkin_division_code": "chcknDvCd",
}


@_preserve_read_raw
def parse_self_checkin_info_response(raw: Mapping[str, Any]) -> SelfCheckInInfoResponse:
    _validate_strict_read_envelope(raw)
    values: dict[str, Any] = {}
    for attribute, key in _SELF_CHECKIN_INFO_FIELDS.items():
        # 열 키 모두 필수이지만 값은 nullable 입니다(SelfCheckInInfoOut.java:56-59).
        if key not in raw:
            raise KorailProtocolError(f"KORAIL self check-in info field {key} is required")
        values[attribute] = _strict_scalar_string(raw, key, "self check-in info")
    return SelfCheckInInfoResponse(**values, **_response_fields(raw))


@_preserve_read_raw
def parse_self_checkin_register_response(raw: Mapping[str, Any]) -> SelfCheckInRegisterResponse:
    """msgId 는 필수·nullable 입니다(SelfCheckInRegisterOut.java:47-52)."""
    data = _response_mapping(raw)
    if "msgId" not in data:
        raise KorailProtocolError("KORAIL self check-in register field msgId is required")
    return SelfCheckInRegisterResponse(
        **_base_fields(data),
        message_id=_strict_scalar_string(data, "msgId", "self check-in register"),
    )


@_preserve_read_raw
def parse_self_checkin_cancel_response(raw: Mapping[str, Any]) -> SelfCheckInCancelResponse:
    """msgId 는 선택입니다(SelfCheckInCancelOut.java:50-56)."""
    data = _response_mapping(raw)
    return SelfCheckInCancelResponse(
        **_base_fields(data),
        message_id=_optional_scalar_string(data, "msgId", "self check-in cancel"),
    )


@_preserve_read_raw
def parse_delivered_ticket_retrieval_response(raw: Mapping[str, Any]) -> DeliveredTicketRetrievalResponse:
    """prsList 와 각 행의 prsFlg 는 필수입니다(RetrieveTicketOut.java:54-59; Prs.java:46-50)."""
    data = _response_mapping(raw)
    rows = data.get("prsList")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL delivered ticket retrieval field prsList must be a list")
    flags = []
    for value in rows:
        try:
            flag = _strict_scalar_string(
                _row(value, "delivered ticket retrieval"), "prsFlg", "delivered ticket retrieval"
            )
            if flag is None:
                raise KorailProtocolError("KORAIL delivered ticket retrieval prsFlg is required and non-null")
        except KorailProtocolError as error:
            error.raw = value
            raise
        flags.append(flag)
    return DeliveredTicketRetrievalResponse(**_base_fields(data), process_flags=tuple(flags))
