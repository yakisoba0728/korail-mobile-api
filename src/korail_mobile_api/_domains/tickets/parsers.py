# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""승차권·계정·마일리지 조회 응답을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _is_list,
    _is_mapping,
    _nested_rows,
    _optional_mapping,
    _optional_read_rows,
    _present_strings,
    _preserve_read_raw,
    _required_integer,
    _required_read_rows,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_envelope,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from ..airport_bus.parsers import parse_maas_service_detail
from .models import (
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayCertificateResponse,
    DelayCertificateRow,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DelayReturnReceiptResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    KorailPointSummaryResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    ReceiptCashPayment,
    ReceiptPayment,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    TicketListReservation,
    TicketListResponse,
    TicketListTicket,
    TicketListTrain,
    TicketReceipt,
    TicketReceiptResponse,
    TripChangeDateResponse,
)


@_preserve_read_raw
def parse_deposit_bank_response(raw: Mapping[str, object]) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = wire_models(DepositBank, _rows(raw, "dptnBank"), "deposit bank")
    return DepositBankListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_delay_discount_ticket_response(raw: Mapping[str, object]) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = wire_models(
        DelayDiscountTicket, _nested_rows(raw, "disc_infos", "disc_info"), "delay discount ticket"
    )
    # 페이지 필드는 응답 최상위가 아니라 main_info 블록에 있습니다.
    return wire_model(
        DelayDiscountTicketListResponse,
        _optional_mapping(raw, "main_info") or {},
        "delay discount main_info",
        items=items,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_coupon_response(raw: Mapping[str, object]) -> DiscountCouponListResponse:
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return DiscountCouponListResponse(**_response_fields(raw))
    items = tuple(
        wire_model(
            DiscountCoupon,
            item,
            "discount coupon",
            remarks=_present_strings(item, ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont")),
            raw=item,
        )
        for item in _nested_rows(raw, "coupon_infos", "coupon_info")
    )
    return wire_model(
        DiscountCouponListResponse, raw, "discount coupon list", items=items, **_response_fields(raw)
    )


@_preserve_read_raw
def parse_korail_point_summary_response(raw: Mapping[str, object]) -> KorailPointSummaryResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(KorailPointSummaryResponse, raw, "point summary", **_response_fields(raw))


@_preserve_read_raw
def parse_mileage_history_response(raw: Mapping[str, object]) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = wire_models(MileageHistoryEntry, _rows(raw, "specList"), "mileage history entry")
    return wire_model(MileageHistoryResponse, raw, "mileage history", entries=entries, **_response_fields(raw))


@_preserve_read_raw
def parse_multi_child_discount_target_response(raw: Mapping[str, object]) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = wire_models(MultiChildDiscountTarget, _rows(raw, "fmlyList"), "multi-child target")
    return MultiChildDiscountTargetResponse(targets=targets, **_response_fields(raw))


@_preserve_read_raw
def parse_customer_trip_info_response(raw: Mapping[str, object]) -> CustomerTripInfoResponse:
    _validate_strict_read_envelope(raw)
    trips = wire_models(
        CustomerTripInfo, _required_read_rows(raw, "mainList", "customer trip info"), "customer trip info"
    )
    return CustomerTripInfoResponse(trips=trips, **_response_fields(raw))


@_preserve_read_raw
def parse_trip_change_date_response(raw: Mapping[str, object]) -> TripChangeDateResponse:
    _validate_strict_read_envelope(raw)
    dates = raw.get("tripChgDates")
    if not _is_list(dates):
        raise KorailProtocolError("KORAIL tripChgDates must be a string list")
    normalized_dates: list[str] = []
    for value in dates:
        date = _strict_scalar_string({"tripChgDates": value}, "tripChgDates", "trip change dates")
        if date is None:
            raise KorailProtocolError("KORAIL tripChgDates must not contain null")
        normalized_dates.append(date)
    return wire_model(
        TripChangeDateResponse,
        raw,
        "trip change dates",
        trip_change_dates=tuple(normalized_dates),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_ticket_list_response(raw: Mapping[str, object]) -> TicketListResponse:
    _validate_envelope(raw)
    reservations: list[TicketListReservation] = []
    for reservation in _rows(raw, "pnr_list"):
        tickets: list[TicketListTicket] = []
        for ticket in _rows(reservation, "ticket_list"):
            train_info = tuple(_rows(ticket, "jrn_info"))
            trains = wire_models(TicketListTrain, train_info, "ticket list train")
            tickets.append(
                wire_model(
                    TicketListTicket,
                    ticket,
                    "ticket list ticket",
                    train_info=train_info,
                    raw=ticket,
                    trains=trains,
                )
            )
        add_srv = _optional_mapping(reservation, "addSrvInfo")
        additional_service = None if add_srv is None else parse_maas_service_detail(add_srv)
        reservations.append(
            wire_model(
                TicketListReservation,
                reservation,
                "ticket list reservation",
                tickets=tuple(tickets),
                raw=reservation,
                additional_service=additional_service,
            )
        )
    return wire_model(
        TicketListResponse, raw, "ticket list", reservations=tuple(reservations), **_response_fields(raw)
    )


@_preserve_read_raw
def parse_ticket_receipt_response(raw: Mapping[str, object]) -> TicketReceiptResponse:
    _validate_envelope(raw)
    receipt_infos = raw.get("receipt_infos")
    if not _is_mapping(receipt_infos):
        raise KorailProtocolError("KORAIL receipt_infos must be an object")
    items: list[TicketReceipt] = []
    for item in _required_read_rows(receipt_infos, "receipt_info", "ticket receipt"):
        payments = wire_models(
            ReceiptPayment, _required_read_rows(item, "stl_info", "ticket receipt"), "receipt payment"
        )
        cash_receipts = wire_models(
            ReceiptCashPayment,
            _required_read_rows(item, "cash_rcet_info", "ticket receipt"),
            "receipt cash payment",
        )
        passenger_counts = (
            _required_integer(item, "h_psg_type1_cnt", "ticket receipt"),
            _required_integer(item, "h_psg_type2_cnt", "ticket receipt"),
            _required_integer(item, "h_psg_type3_cnt", "ticket receipt"),
        )
        items.append(
            wire_model(
                TicketReceipt,
                item,
                "ticket receipt",
                passenger_counts=passenger_counts,
                payments=payments,
                cash_receipts=cash_receipts,
                raw=item,
            )
        )
    return TicketReceiptResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_self_seat_change_info_response(raw: Mapping[str, object]) -> SelfSeatChangeInfoResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(
        SelfSeatChangeInfoResponse,
        raw,
        "self seat change info",
        stations=wire_models(SelfSeatChangeStation, _rows(raw, "chgStnList"), "self seat change station"),
        reasons=wire_models(SelfSeatChangeReason, _rows(raw, "chgRsnList"), "self seat change reason"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_original_ticket_inquiry_response(raw: Mapping[str, object]) -> OriginalTicketInquiryResponse:
    """원표→여정→좌석 행은 대리수령 내역의 여정·좌석과 다른 앱 타입이라 모델을 따로 둡니다."""
    _validate_strict_read_envelope(raw)
    tickets: list[OriginalTicket] = []
    for ticket in _rows(raw, "orgTkList"):
        journeys = tuple(
            wire_model(
                OriginalTicketJourney,
                journey,
                "original ticket journey",
                seats=wire_models(OriginalTicketSeat, _rows(journey, "seatList"), "original ticket seat"),
                raw=journey,
            )
            for journey in _rows(ticket, "jrnyList")
        )
        tickets.append(wire_model(OriginalTicket, ticket, "original ticket", journeys=journeys, raw=ticket))
    return OriginalTicketInquiryResponse(tickets=tuple(tickets), **_response_fields(raw))


@_preserve_read_raw
def parse_delay_certificate_response(raw: Mapping[str, object]) -> DelayCertificateResponse:
    _validate_strict_read_envelope(raw)
    delays = wire_models(
        DelayCertificateRow, _optional_read_rows(raw, "dlayList", "delay certificate"), "delay certificate"
    )
    return DelayCertificateResponse(delays=delays, **_response_fields(raw))


@_preserve_read_raw
def parse_delay_return_receipt_response(raw: Mapping[str, object]) -> DelayReturnReceiptResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(DelayReturnReceiptResponse, raw, "delay return receipt", **_response_fields(raw))
