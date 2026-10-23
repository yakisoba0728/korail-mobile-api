"""INVALID public-call input raises before any request leaves the client, NetFunnel gate included.

Each row makes one argument of a working smoke call (``test_public_api_smoke._f8_arguments``) invalid
and pins the exception raised today. ``FIXES`` rows pin defects fixed in 2.6.2 without ``match=``, so a
reworded message still passes. Synthetic values only; offline.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import date
from typing import Any

import httpx
import pytest
from conftest import synthetic_config
from test_public_api_smoke import F8_DATE, _f8_arguments

import korail_mobile_api as api
from korail_mobile_api.constants import KORAIL_STANDBY_WAIT_FLAG

Job = api.KorailReservationJobType
Cabin = api.KorailSeatClass
Option = api.KorailReserveOption

F8 = _f8_arguments()
TRAIN: api.TrainSummary = F8["reserve"]["train"]
LEGS: tuple[api.TrainSummary, ...] = F8["reserve_transfer"]["legs"]
MERGE_TRAIN: api.TrainSummary = F8["reserve_merge"]["standing_hold_train"]
MERGE_ROWS: tuple[api.TrainScheduleItem, ...] = F8["reserve_merge"]["merge_rows"]
HOLD: api.ReservationHoldResponse = F8["pay_with_card"]["hold"]
CARD: api.CardPayment = F8["pay_with_card"]["card"]
TICKET: api.OriginalTicketReference = F8["get_refund_fee"]["ticket"]
DETAIL: api.RefundTicketDetailResponse = F8["register_self_checkin"]["detail"]
EXECUTION: api.StationRefundExecutionRequest = F8["refund_station_ticket"]["request"]
RECALC: api.PriceRecalculationRequest = F8["recalculate_price"]["request"]
FARE_LEG: api.PriceFareLeg = F8["get_fare_quote"]["request"].legs[0]
QUERY: api.TrainSearchQuery = F8["search_trains"]["query"]
SEAT = api.KorailSeatAssignment(car_no=1, seat_no="1A")
SEAT_ROW = api.PhysicalSeat(
    seat_no="1A",
    sale_possible="Y",
    direction_code="0",
    other_attribute_code=None,
    requested_attribute_code="015",
    floor=None,
    specification="1A",
    sequence_no="1",
    message_code="",
    message="",
    visual_message_division_code=None,
)
# A hold whose first journey carries the seat rows PriceRecalculationRequest.for_hold copies.
SEATED_HOLD = replace(
    HOLD,
    journeys=(
        api.ReservationJourney(
            raw={
                "seat_infos": {
                    "seat_info": [{"h_psg_tp_cd": "1", "h_psrm_cl_cd": "1", "h_dcnt_knd_cd1": "000"}]
                }
            }
        ),
    ),
)
LOGGED_OUT: dict[str, Any] = {"error": api.KorailAuthError, "logged_in": False}
INVALID = api.KorailInvalidInputError


@dataclass(frozen=True)
class Row:
    id: str
    call: Callable[[api.KorailClient], object]
    match: str | None = None
    error: type[Exception] = INVALID
    logged_in: bool = True


def _train(**changes: Any) -> api.TrainSummary:
    return replace(TRAIN, **changes)


def _hold(**changes: Any) -> api.ReservationHoldResponse:
    return replace(HOLD, **changes)


def _designated(c: api.KorailClient, *seats: object, adults: int = 1) -> object:
    passengers = api.KorailPassengerCounts(adult=adults)
    return c.reserve(TRAIN, passengers=passengers, job_type=Job.SEAT_DESIGNATED, seats=seats)


def _from_inventory(seat: api.PhysicalSeat = SEAT_ROW, **inventory: Any) -> api.KorailSeatAssignment:
    return api.KorailSeatAssignment.from_inventory(api.SeatInventoryResponse(**inventory), seat)


def _merge(c: api.KorailClient, first: dict[str, Any], **options: Any) -> object:
    return c.reserve_merge(MERGE_TRAIN, (replace(MERGE_ROWS[0], **first), MERGE_ROWS[1]), **options)


def _refund(c: api.KorailClient, changes: dict[str, Any] | None = None, **overrides: Any) -> object:
    """Refund with a commission genuinely bound by an offline get_refund_fee."""
    arguments = _f8_arguments("refund")["refund"]
    arguments["ticket"] = replace(arguments["ticket"], **(changes or {}))
    return c.refund(**{**arguments, **overrides})


def _refund_with_quote(c: api.KorailClient, **quote: Any) -> object:
    """A bound quote edited through replace(), which keeps the binding, so only the amount types differ."""
    arguments = _f8_arguments("refund")["refund"]
    return c.refund(
        **{**arguments, "commission": replace(arguments["commission"], **quote), "settle_mileage": True}
    )


def _station_refund(c: api.KorailClient, **verification: Any) -> object:
    original = api.StationRefundOriginalTicket(
        pnr_no="SYNTHETIC-PNR",
        original_sale_date=F8_DATE,
        original_sale_window_no="SYNTHETIC-WINDOW",
        original_sale_sequence="1",
        original_return_password="SYNTHETIC-RETURN",
        ticket_kind_code="1",
        refund_division_code="1",
        refund_reason_code="1",
    )
    values = {"str_result": "SUCC", "refund_amount": "1000", "refund_fee": "0", "original_tickets": (original,)}
    response = api.StationRefundVerificationResponse(**{**values, **verification})
    return c.refund_station_ticket(
        api.StationRefundExecutionRequest.from_verification(
            response, customer_phone="00000000000", customer_name="SYNTHETIC-NAME"
        )
    )


def _recalc(c: api.KorailClient, row: dict[str, Any] | None = None, **changes: Any) -> object:
    if row is not None:
        changes["rows"] = (replace(RECALC.rows[0], **row),)
    return c.recalculate_price(replace(RECALC, **changes))


def _free(**changes: Any) -> api.FreeSeatCarRequest:
    return replace(F8["get_free_seat_cars"]["request"], **changes)


def _merge_inquiry(**changes: Any) -> api.MergeSeatsInquiryRequest:
    return replace(F8["get_merge_seat_options"]["request"], **changes)


def _search(c: api.KorailClient, **changes: Any) -> object:
    return c.search_trains(replace(QUERY, **changes))


def _without_customer_no(c: api.KorailClient) -> api.KorailClient:
    assert c.session.current is not None
    c.session.current = replace(c.session.current, customer_no=None)
    return c


ROWS = [
    # Train reservations: legs, passengers, cabin, job type and designated seats.
    Row("reserve-train-type", lambda c: c.reserve("90001"), "exact TrainSummary"),
    Row("reserve-passengers-type", lambda c: c.reserve(TRAIN, passengers=1), "KorailPassengerCounts"),
    Row("reserve-seat-class-unknown", lambda c: c.reserve(TRAIN, seat_class="3"), "seat class must be"),
    Row("reserve-job-type-unknown", lambda c: c.reserve(TRAIN, job_type="9999"), "job type must be one of"),
    Row("reserve-seats-on-immediate-job", lambda c: c.reserve(TRAIN, seats=[SEAT]), "designated seats belong"),
    Row(
        "designated-no-seats",
        lambda c: c.reserve(TRAIN, job_type=Job.SEAT_DESIGNATED),
        "sequence of KorailSeat",
    ),
    Row("designated-seat-type", lambda c: _designated(c, (1, "1A")), "exact KorailSeatAssignment"),
    Row(
        "designated-seat-count",
        lambda c: _designated(c, SEAT, api.KorailSeatAssignment(car_no=1, seat_no="1B")),
        "one seat per",
    ),
    Row("designated-same-seat-twice", lambda c: _designated(c, SEAT, SEAT, adults=2), "same seat twice"),
    Row(
        "seat-car-zero",
        lambda c: _designated(c, api.KorailSeatAssignment(car_no=0, seat_no="1A")),
        "car_no must be",
    ),
    Row(
        "seat-no-blank",
        lambda c: _designated(c, api.KorailSeatAssignment(car_no=1, seat_no="")),
        "seat_no must be",
    ),
    Row(
        "seat-inventory-type", lambda c: api.KorailSeatAssignment.from_inventory({}, SEAT_ROW), "inventory must"
    ),
    Row("seat-inventory-no-car", lambda c: _from_inventory(seats=(SEAT_ROW,)), "did not echo a car number"),
    Row("seat-not-in-inventory", lambda c: _from_inventory(car_no=1), "does not belong"),
    Row(
        "seat-not-sellable",
        lambda c: _from_inventory(
            replace(SEAT_ROW, sale_possible="N"), car_no=1, seats=(replace(SEAT_ROW, sale_possible="N"),)
        ),
        "not marked sellable",
    ),
    Row(
        "standby-special-cabin",
        lambda c: c.reserve(
            _train(wait_reservation_flag=KORAIL_STANDBY_WAIT_FLAG),
            seat_class=Cabin.SPECIAL,
            job_type=Job.STANDBY,
        ),
        "is offered on the",
    ),
    Row("standby-without-wait-flag", lambda c: c.reserve(TRAIN, job_type=Job.STANDBY), "h_wait_rsv_flg"),
    Row(
        "merge-job-ineligible-train", lambda c: c.reserve(TRAIN, job_type=Job.MERGE_STANDING), "merge-eligible"
    ),
    Row("special-unavailable", lambda c: c.reserve(TRAIN, seat_class=Cabin.SPECIAL), "available special seat"),
    Row("transfer-legs-type", lambda c: c.reserve_transfer(TRAIN), "requires a sequence of legs"),
    Row("transfer-one-leg", lambda c: c.reserve_transfer(LEGS[:1]), "books exactly 2 legs"),
    Row("transfer-cabins-type", lambda c: c.reserve_transfer(LEGS, seat_classes=1), "one per leg"),
    Row(
        "transfer-cabins-count",
        lambda c: c.reserve_transfer(LEGS, seat_classes=("1",) * 3),
        "one cabin class per",
    ),
    Row(
        "transfer-attributes-count",
        lambda c: c.reserve_transfer(LEGS, seat_attribute_codes=("015",)),
        "seat attribute per leg",
    ),
    Row(
        "transfer-seats-type",
        lambda c: c.reserve_transfer(LEGS, job_type=Job.SEAT_DESIGNATED, seats="1A"),
        "one sequence of KorailSeatAssignment per leg",
    ),
    Row(
        "transfer-seats-count",
        lambda c: c.reserve_transfer(LEGS, job_type=Job.SEAT_DESIGNATED, seats=[[SEAT]]),
        "one seat list per",
    ),
    Row("merge-without-rows", lambda c: c.reserve_merge(MERGE_TRAIN, ()), "requires the research"),
    Row("merge-row-other-train", lambda c: _merge(c, {"train_no": "90002"}), "every merge row must"),
    Row("merge-first-row-no-middle", lambda c: _merge(c, {"arrival_run_order": None}), "first merge row lacks"),
    # The D1 fix may reword this rejection; type and zero sends must hold.
    Row("n-card-reserve-blank-card", lambda c: c.reserve_with_discount_card(TRAIN, card_no=" "), "card_no"),
    # The convenience facade keeps its own TypeError/ValueError guards.
    Row(
        "facade-option-and-seat-class",
        lambda c: api.ReservationResource(c).create(
            TRAIN, option=Option.GENERAL_FIRST, seat_class=Cabin.SPECIAL
        ),
        "option requires immediate",
        ValueError,
    ),
    Row(
        "facade-option-type",
        lambda c: api.ReservationResource(c).create(TRAIN, option="1"),
        "option must",
        TypeError,
    ),
    Row(
        "facade-option-train-type",
        lambda c: api.ReservationResource(c).create("90001", option=Option.GENERAL_FIRST),
        "train must be TrainSummary",
        TypeError,
    ),
    Row(
        "facade-option-no-seat",
        lambda c: api.ReservationResource(c).create(TRAIN, option=Option.SPECIAL_ONLY),
        "evidenced available seat",
    ),
    Row(
        "facade-detail-no-pnr",
        lambda c: api.ReservationResource(c).detail(_hold(pnr_no=None)),
        "PNR",
        ValueError,
    ),
    Row("facade-bus-seats-type", lambda c: api.AirportBusResource(c).seats("bus"), "schedule must", TypeError),
    # Standby options and unpaid-hold cancellation.
    Row(
        "standby-class-flag-text", lambda c: c.set_standby_options(HOLD, allow_seat_class_change="N"), "a bool"
    ),
    Row("standby-sms-flag-text", lambda c: c.set_standby_options(HOLD, sms_notify="Y"), "sms_notify must be"),
    Row(
        "standby-sms-phone-shape",
        lambda c: c.set_standby_options(HOLD, sms_notify=True, phone_no="000-0000-0000"),
        "11-digit phone number",
    ),
    Row("cancel-hold-type", lambda c: c.cancel_unpaid_hold({}), "exact reservation hold response"),
    Row("cancel-journey-count-text", lambda c: c.cancel_unpaid_hold(_hold(journey_count="abc")), "unpaid hold"),
    Row("cancel-journey-count-zero", lambda c: c.cancel_unpaid_hold(_hold(journey_count="0")), "unpaid hold"),
    Row("cancel-journey-count-none", lambda c: c.cancel_unpaid_hold(_hold(journey_count=None)), "unpaid hold"),
    Row(
        "cancel-reference-blank-pnr",
        lambda c: c.cancel_unpaid_hold(api.HoldReference(pnr_no=" ", journey_count="1")),
        "pnr_no",
    ),
    Row(
        "cancel-reference-journey-count-zero",
        lambda c: c.cancel_unpaid_hold(api.HoldReference(pnr_no="SYNTHETIC-PNR", journey_count="0")),
        "unpaid hold",
    ),
    Row(
        "cancel-reference-sequence-type",
        lambda c: c.cancel_unpaid_hold(
            api.HoldReference(pnr_no="SYNTHETIC-PNR", journey_count="1", journey_sequence=7)
        ),  # type: ignore[arg-type]
        "journey_sequence",
    ),
    # Card payment charges the hold's received_amount, and only a fresh payable hold.
    Row("pay-card-type", lambda c: c.pay_with_card(HOLD, "card"), "requires a CardPayment", INVALID),
    Row("pay-hold-type", lambda c: c.pay_with_card({}, CARD), "exact reservation hold response", INVALID),
    Row("pay-card-format-on-build", lambda c: replace(CARD, card_number="0" * 12), "13 to 16 digits", INVALID),
    Row("pay-standby-hold", lambda c: c.pay_with_card(_hold(payable=False), CARD), "refuses a standby"),
    Row("pay-zero-amount", lambda c: c.pay_with_card(_hold(received_amount="0"), CARD), "zero-amount"),
    Row(
        "pay-full-width-amount",
        lambda c: c.pay_with_card(_hold(received_amount="１０"), CARD),
        "received amount",
    ),
    Row(
        "pay-card-kind-unknown", lambda c: c.pay_with_card(HOLD, replace(CARD, card_type="X")), "card_type must"
    ),
    # Ticket refunds are bound to their commission lookup; station refunds echo a verification.
    Row("refund-ticket-type", lambda c: _refund(c, ticket="ticket"), "requires a PaidTicket"),
    Row("refund-settle-mileage-text", lambda c: _refund(c, settle_mileage="Y"), "settle_mileage must be"),
    Row("refund-pbp-flag-type", lambda c: _refund(c, pbp_acceptance_target_flag=1), "must be a string echoed"),
    Row(
        "refund-unbound-commission",
        lambda c: _refund(c, commission=api.RefundCommissionResponse(str_result="SUCC")),
        "bound by get_refund_fee",
    ),
    Row("refund-other-ticket", lambda c: _refund(c, {"sale_sequence": "2"}), "does not match the original"),
    Row("refund-integer-fee", lambda c: _refund_with_quote(c, refund_fee=400), "must be strings", INVALID),
    Row(
        "refund-integer-mileage",
        lambda c: _refund_with_quote(c, usable_mileage=500),
        "must be strings",
        INVALID,
    ),
    Row(
        "refund-ticket-blank-on-build",
        lambda c: api.PaidTicket(
            pnr_no=" ",
            sale_date=F8_DATE,
            sale_window_no="SYNTHETIC-WINDOW",
            sale_sequence="1",
            return_password="SYNTHETIC-RETURN",
        ),
        "non-empty PaidTicket.pnr_no",
    ),
    Row(
        "refund-detail-incomplete",
        lambda c: api.PaidTicket.from_refund_detail(replace(DETAIL, original_window_no=None)),
        "identity is incomplete",
    ),
    Row("station-refund-type", lambda c: c.refund_station_ticket({}), "exact execution request"),
    Row(
        "station-refund-blank-amount",
        lambda c: c.refund_station_ticket(replace(EXECUTION, refund_amount="")),
        "requires refund_amount",
    ),
    Row(
        "station-refund-failed-verification",
        lambda c: _station_refund(c, str_result="FAIL"),
        "successful verif",
    ),
    Row(
        "station-refund-no-original-ticket",
        lambda c: _station_refund(c, original_tickets=()),
        "successful verif",
    ),
    Row("station-refund-no-fee", lambda c: _station_refund(c, refund_fee=None), "missing refund_fee"),
    Row(
        "station-verify-blank-name",
        lambda c: c.check_station_ticket_refund(
            replace(F8["check_station_ticket_refund"]["request"], customer_name=" ")
        ),
        "verification requires customer_name",
        INVALID,
    ),
    Row(
        "station-verify-type",
        lambda c: c.check_station_ticket_refund({}),
        "exact verification request",
        INVALID,
    ),
    # Discount cards, recalculation, cart, products, delivered tickets and self check-in.
    Row("n-card-extend-type", lambda c: c.extend_discount_card({}), "OriginalTicketReference"),
    Row("recalc-type", lambda c: c.recalculate_price({}), "exact PriceRecalculationRequest"),
    Row("recalc-no-rows", lambda c: _recalc(c, rows=()), "needs 1 to"),
    Row("recalc-row-type", lambda c: _recalc(c, rows=("x",)), "exact PriceRecalculationRow"),
    Row("recalc-row-field-none", lambda c: _recalc(c, {"certificate_no": None}), "certificate_no must be"),
    Row("recalc-row-type-blank", lambda c: _recalc(c, {"passenger_type_code": " "}), "must not be empty"),
    Row("recalc-non-member-blank", lambda c: _recalc(c, non_member_no=""), "non_member_no must be"),
    Row("recalc-cabin-blank", lambda c: _recalc(c, cabin_class_code=""), "cabin_class_code must be"),
    Row("cart-add-type", lambda c: c.add_to_cart({}), "exact CartAddRequest"),
    Row("product-cancel-type", lambda c: c.cancel_product_reservation({}), "ProductDetailResponse"),
    Row("delivered-ticket-type", lambda c: c.recall_delivered_ticket({}), "PbpAcceptanceTicket"),
    Row(
        "delivered-no-journeys",
        lambda c: c.recall_delivered_ticket(replace(F8["recall_delivered_ticket"]["ticket"], journeys=())),
        "first journey",
    ),
    Row(
        "checkin-register-detail-type",
        lambda c: c.register_self_checkin({}, F8["register_self_checkin"]["seat"]),
        "RefundTicketDetailResponse",
    ),
    Row(
        "checkin-cancel-blank-window",
        lambda c: c.cancel_self_checkin(replace(DETAIL, original_window_no="")),
        "window",
    ),
    # A session (and its customer number) is required before any state change.
    Row("reserve-logged-out", lambda c: c.reserve(TRAIN), "authenticated session", **LOGGED_OUT),
    Row("cancel-logged-out", lambda c: c.cancel_unpaid_hold(HOLD), "authenticated session", **LOGGED_OUT),
    Row("pay-logged-out", lambda c: c.pay_with_card(HOLD, CARD), "authenticated session", **LOGGED_OUT),
    Row("refund-logged-out", lambda c: _refund(c), "authenticated session", **LOGGED_OUT),
    Row(
        "trip-info-no-customer-no",
        lambda c: _without_customer_no(c).get_trip_preferences(),
        "login customer number",
        api.KorailAuthError,
    ),
    # Reads: seat maps, train search, lists, ticket references and fares.
    Row("seat-cars-train-type", lambda c: c.list_seat_cars("90001"), "train must be a TrainSummary", INVALID),
    Row("seat-cars-no-passengers", lambda c: c.list_seat_cars(TRAIN, passenger_count=0), "passenger_count"),
    Row(
        "seat-inventory-car-zero",
        lambda c: c.get_seat_inventory(TRAIN, 0),
        "car_no must be a positive",
        INVALID,
    ),
    Row(
        "seat-cars-goods-no-space",
        lambda c: c.list_seat_cars(_train(goods_no="A B")),
        "printable ASCII",
        INVALID,
    ),
    Row(
        "seat-cars-room-class",
        lambda c: c.list_seat_cars(TRAIN, room_class_code="3"),
        "room_class_code",
        INVALID,
    ),
    # Per-train reads send the row's identifiers; a missing one used to go out blank (or as 00000).
    Row(
        "seat-cars-train-no-blank",
        lambda c: c.list_seat_cars(_train(train_no="")),
        "train_no must not",
        INVALID,
    ),
    Row(
        "seat-cars-run-date-none",
        lambda c: c.list_seat_cars(_train(run_date=None)),
        "run_date must not",
        INVALID,
    ),
    Row(
        "seat-inventory-station-blank",
        lambda c: c.get_seat_inventory(_train(arrival_station_code=" "), 1),
        "arrival_station_code must not",
        INVALID,
    ),
    Row(
        "seat-inventory-run-order-none",
        lambda c: c.get_seat_inventory(_train(departure_run_order=None), 1),
        "departure_run_order must not",
        INVALID,
    ),
    Row("train-schedule-train-no-none", lambda c: c.get_train_schedule(F8_DATE, None), "train_no", INVALID),
    Row("train-schedule-train-no-blank", lambda c: c.get_train_schedule(F8_DATE, " "), "train_no", INVALID),
    Row("train-schedule-train-no-int", lambda c: c.get_train_schedule(F8_DATE, 90001), "train_no", INVALID),
    Row("train-schedule-run-date-blank", lambda c: c.get_train_schedule("", "90001"), "run_date", INVALID),
    Row(
        "free-seat-car-train-no-blank",
        lambda c: c.get_free_seat_cars(_free(train_no="")),
        "train_no",
        INVALID,
    ),
    Row(
        "free-seat-car-construction-order-none",
        lambda c: c.get_free_seat_cars(_free(departure_construction_order=None)),
        "departure_construction_order",
        INVALID,
    ),
    Row(
        "merge-inquiry-train-no-none",
        lambda c: c.get_merge_seat_options(_merge_inquiry(train_no=None)),
        "train_no",
        INVALID,
    ),
    Row(
        "merge-inquiry-station-blank",
        lambda c: c.get_merge_seat_options(_merge_inquiry(departure_station_name="")),
        "departure_station_name",
        INVALID,
    ),
    Row(
        "merge-inquiry-run-date-blank",
        lambda c: c.get_merge_seat_options(_merge_inquiry(run_datetime=" ")),
        "run_datetime",
        INVALID,
    ),
    Row(
        "search-continuation-type",
        lambda c: c.search_trains(QUERY, continuation=("1", "2")),
        "continuation",
        INVALID,
    ),
    Row("search-station-blank", lambda c: _search(c, departure_station=" "), "must not be empty", INVALID),
    # A non-str station used to reach the station-name lookup as an AttributeError.
    Row(
        "search-station-int",
        lambda c: _search(c, arrival_station=1),
        "arrival_station must be a string",
    ),
    Row("search-attribute-blank", lambda c: _search(c, seat_attribute_code=""), "seat_attribute_code", INVALID),
    Row("search-division-blank", lambda c: _search(c, query_division_code=""), "query_division_code", INVALID),
    Row(
        "search-connections-text",
        lambda c: _search(c, connection_station_codes="0001"),
        "connection_station",
        INVALID,
    ),
    Row(
        "search-connection-group",
        lambda c: _search(c, connection_train_group_code=""),
        "connection_train_group",
        INVALID,
    ),
    Row("ticket-list-page-text", lambda c: c.list_tickets("1"), "page_no must be an integer", error=INVALID),
    Row("ticket-list-mode-blank", lambda c: c.list_tickets(mode=""), "ticket list mode", error=INVALID),
    # Boarding dates are "" (omitted) or YYYYMMDD; a date object used to go out as 2026-07-01.
    Row(
        "ticket-list-date-object",
        lambda c: c.list_tickets(mode="2", boarding_date_from=date(2026, 7, 1), boarding_date_to="20260928"),
        "boarding_date_from must be empty or exactly 8 ASCII digits",
        error=INVALID,
    ),
    Row(
        "ticket-list-date-dashed",
        lambda c: c.list_tickets(mode="2", boarding_date_from="20260701", boarding_date_to="2026-09-28"),
        "boarding_date_to must be empty or exactly 8 ASCII digits",
        error=INVALID,
    ),
    Row(
        "ticket-list-date-none",
        lambda c: c.list_tickets(boarding_date_to=None),
        "boarding_date_to",
        error=INVALID,
    ),
    Row("maas-stations-blank", lambda c: c.list_maas_stations(" "), "additional_service_code must be"),
    Row("delay-discount-date-length", lambda c: c.list_delay_discount_tickets("2099010"), "exactly 8 ASCII"),
    Row(
        "self-seat-change-train-no",
        lambda c: c.get_self_seat_change_options(
            api.SelfSeatChangeInfoRequest(
                run_date=F8_DATE, train_no="900001", departure_station_code="9901", arrival_station_code="9903"
            )
        ),
        "at most 5 digits",
    ),
    Row("multi-child-date-invalid", lambda c: c.list_multi_child_discount_targets("20990230"), "calendar date"),
    Row(
        "receipt-index-type",
        lambda c: c.get_ticket_receipt(**{**F8["get_ticket_receipt"], "txt_index": 1}),
        "txt_index must be",
        error=INVALID,
    ),
    # A blank txtIndex used to be dropped silently; refund detail already rejected it.
    Row(
        "receipt-index-blank",
        lambda c: c.get_ticket_receipt(**{**F8["get_ticket_receipt"], "txt_index": " "}),
        "txt_index must be a non-empty string or None",
        error=INVALID,
    ),
    Row("recipient-ticket-type", lambda c: c.get_delivery_recipient({}), "OriginalTicketReference"),
    Row("pbp-specifications-empty", lambda c: c.list_pbp_acceptances(()), "at least one"),
    Row("duplication-type", lambda c: c.check_ticket_duplication({}), "TicketDuplicationCheckRequest"),
    Row(
        "original-count-text",
        lambda c: c.get_original_tickets((TICKET,), ticket_count="1"),
        "ticket_count",
        error=INVALID,
    ),
    Row(
        "commuter-inquiry-type",
        lambda c: c.get_commuter_info(
            api.CommuterTicketInquiryRequest(original_ticket=TICKET, inquiry_type="2")
        ),
        "inquiry_type must be",
    ),
    Row(
        "commuter-ticket-type",
        lambda c: c.get_commuter_info(api.CommuterTicketInquiryRequest(original_ticket={})),
        "original_ticket must be",
    ),
    Row("commuter-request-type", lambda c: c.get_commuter_info({}), "commuter request variant"),
    Row(
        "fare-legs-text",
        lambda c: c.get_fare_quote(api.PriceFareQuoteRequest(legs="x")),
        "one or two",
        INVALID,
    ),
    Row("fare-no-legs", lambda c: c.get_fare_quote(api.PriceFareQuoteRequest(legs=())), "one or two", INVALID),
    Row(
        "fare-leg-type",
        lambda c: c.get_fare_quote(api.PriceFareQuoteRequest(legs=("x",))),
        "PriceFareLeg",
        INVALID,
    ),
    Row("fare-request-type", lambda c: c.get_fare_quote({}), "must be a PriceFareQuoteRequest", INVALID),
    Row(
        "fare-goods-no-on-one-leg",
        lambda c: c.get_fare_quote(
            api.PriceFareQuoteRequest(legs=(replace(FARE_LEG, goods_no="G1"), FARE_LEG))
        ),
        "every leg or on none",
        INVALID,
    ),
    Row("reservation-detail-type", lambda c: c.get_ticket_reservation_detail({}), "TicketReservationDetail"),
    Row("commission-companion-type", lambda c: c.get_refund_fee(TICKET, companion={}), "RefundCompanion"),
    Row(
        "refund-detail-history-text",
        lambda c: c.get_refund_ticket_detail(TICKET, from_purchase_history="Y"),
        "bool",
    ),
    # Same txt_index rule as the receipt (the refund detail used to say "txt_index must not be empty").
    Row(
        "refund-detail-index-type",
        lambda c: c.get_refund_ticket_detail(TICKET, txt_index=1),
        "txt_index must be a non-empty string or None",
    ),
    Row(
        "refund-detail-index-blank",
        lambda c: c.get_refund_ticket_detail(TICKET, txt_index=" "),
        "txt_index must be a non-empty string or None",
    ),
    # Common codes are a str or a sequence of str; bytes used to go out one code per byte (code=97&code=98).
    Row("common-code-bytes", lambda c: c.get_common_codes(b"ab"), "sequence of strings", INVALID, False),
    Row("common-code-empty-bytes", lambda c: c.get_common_codes(b""), "sequence of strings", INVALID, False),
    Row(
        "common-code-int-item",
        lambda c: c.get_common_codes(["SYNTH", 1]),
        "sequence of strings",
        INVALID,
        False,
    ),
    Row("common-code-int", lambda c: c.get_common_codes(1), "sequence of strings", INVALID, False),
]

# Defects fixed in 2.6.2.
FIXES = [
    Row("search-query-mapping", lambda c: c.search_trains({})),
    Row("search-query-none", lambda c: c.search_transfer_trains(None)),
    Row("search-connections-none", lambda c: _search(c, connection_station_codes=None)),
    Row("search-connections-mapping", lambda c: _search(c, connection_station_codes={"0001": "x"})),
    Row("search-connections-generator", lambda c: _search(c, connection_station_codes=iter(["0001"]))),
    Row("search-srt-text", lambda c: _search(c, include_srt="False")),
    Row("search-nearby-int", lambda c: _search(c, include_nearby_stations=1)),
    Row("search-special-text", lambda c: c.search_trains(QUERY, use_special_schedule="False")),
    Row("search-peak-int", lambda c: c.search_transfer_trains(QUERY, peak_season=1)),
    Row(
        "search-numeric-invalid-cursor",
        lambda c: c.search_trains(replace(QUERY, departure_station="0001"), continuation=("1", "2")),
    ),
    Row("search-numeric-blank-arrival", lambda c: _search(c, departure_station="0001", arrival_station=" ")),
    Row("mileage-request-mapping", lambda c: c.get_mileage_history({})),
    Row("self-seat-change-request-none", lambda c: c.get_self_seat_change_options(None)),
    # D6: non-ASCII digits reach int() (bare ValueError) or the wire.
    Row(
        "cancel-journey-count-superscript",
        lambda c: c.cancel_unpaid_hold(_hold(journey_count="²")),
    ),
    Row(
        "cancel-journey-count-arabic-indic",
        lambda c: c.cancel_unpaid_hold(_hold(journey_count="٢")),
    ),
    Row(
        "cancel-journey-count-full-width",
        lambda c: c.cancel_unpaid_hold(_hold(journey_count="１")),
    ),
    # D5: a None request field is sent as an empty "key=".
    Row("search-departure-date-none", lambda c: _search(c, departure_date=None)),
    Row("train-schedule-run-date-none", lambda c: c.get_train_schedule(None, "90001")),
    Row(
        "bus-schedule-departure-date-none",
        lambda c: c.list_airport_bus_schedules(
            replace(F8["list_airport_bus_schedules"]["query"], departure_date=None)
        ),
    ),
    Row(
        "pass-schedule-page-none",
        lambda c: c.get_pass_schedule(replace(F8["get_pass_schedule"]["request"], page_no=None)),
    ),
    Row(
        "free-seat-car-run-date-none",
        lambda c: c.get_free_seat_cars(replace(F8["get_free_seat_cars"]["request"], run_date=None)),
    ),
    # D1: a standby hold is not recalculated (3.0 removed reserve_merge(job_type=); it is always MERGE_STANDING).
    Row(
        "recalc-standby-hold",
        lambda c: c.recalculate_price(
            api.PriceRecalculationRequest.for_hold(replace(SEATED_HOLD, payable=False), ["000"])
        ),
    ),
    # D9: login sends the service check and crypto key request before rejecting the password.
    Row("login-password-none", lambda c: c.login("0000000000", None), logged_in=False),
    Row("login-password-not-text", lambda c: c.login("0000000000", 123), logged_in=False),
]


def _recording(sent: list[httpx.Request]) -> Callable[[httpx.Request], httpx.Response]:
    """Answer like a healthy server so a missing guard shows up as a recorded request, not a parse error."""

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        if request.url.host == "queue.example.invalid":
            return httpx.Response(200, text="200:key=SYNTHETIC-QUEUE&nwait=0&ttl=1")
        return httpx.Response(200, json={"strResult": "SUCC", "h_msg_cd": "SYNTHETIC-SENT"})

    return handler


@pytest.mark.parametrize("row", [pytest.param(row, id=row.id) for row in ROWS + FIXES])
def test_invalid_input_is_rejected_before_any_request(
    f8_client_factory: Callable[..., api.KorailClient], row: Row
) -> None:
    """The default config keeps NetFunnel on, so zero requests also means no 5101 gate entry."""
    sent: list[httpx.Request] = []
    client = f8_client_factory(_recording(sent), logged_in=row.logged_in)
    with pytest.raises(row.error, match=row.match) as caught:
        row.call(client)
    if isinstance(caught.value, api.KorailApiError):
        assert caught.value.request_sent is None
    assert [request.url.path for request in sent] == []


@pytest.mark.parametrize(
    "method,field,path,before,after",
    [
        (
            "list_discount_coupons",
            "page_no",
            "passCard.CouponView",
            b"&txtSelPage=",
            b"&pnrNo=SYNTHETIC-PNR",
        ),
        (
            "list_product_reservations",
            "page_no",
            "product.ReservationList",
            b"&txtSelPage=",
            b"&txtCntPerPage=10",
        ),
        (
            "list_product_reservations",
            "page_size",
            "product.ReservationList",
            b"&txtSelPage=1&txtCntPerPage=",
            b"",
        ),
        (
            "list_tickets",
            "page_no",
            "myTicket.MyTicketNewList.do",
            b"&txtIndex=1&hiduserYn=Y&h_page_no=",
            b"",
        ),
        (
            "get_mileage_history",
            "page_no",
            "mlg.amtSpec.do",
            b"&pontTpVal=1&qryDvVal=0&qryStDt=20990102&qryClsDt=20990102&pgPrCnt=20&nowPgNo=",
            b"",
        ),
    ],
)
@pytest.mark.parametrize(
    "value,text",
    [
        pytest.param(-1, b"-1", id="negative"),
        pytest.param(0, b"0", id="zero"),
        pytest.param(10**600, b"1" + b"0" * 600, id="large-convertible"),
        pytest.param(10 ** max(5000, sys.get_int_max_str_digits()), None, id="too-long"),
    ],
)
def test_page_integer_conversion_preserves_wire_or_rejects_before_send(
    f8_client_factory, method, field, path, before, after, value, text
):
    limit = sys.get_int_max_str_digits()
    if text is None and limit == 0:
        pytest.skip("interpreter integer-to-string conversion limit is disabled")
    sent = []
    provider_calls = []
    path = "/classes/com.korail.mobile." + path
    config = synthetic_config(
        dynapath=api.DynapathConfig(
            enabled=True,
            allowlist_paths=frozenset({path}),
            token_provider=lambda context: provider_calls.append(context) or "SYNTHETIC-TOKEN",
        )
    )
    client = f8_client_factory(_recording(sent), config=config)
    arguments = dict(F8[method])
    if method == "get_mileage_history":
        arguments["request"] = replace(arguments["request"], page_no=value)
    else:
        arguments[field] = value

    if text is None:
        with pytest.raises(ValueError) as conversion:
            str(value)
        with pytest.raises(INVALID) as caught:
            getattr(client, method)(**arguments)
        assert isinstance(caught.value, api.KorailProtocolError)
        assert isinstance(caught.value, ValueError)
        assert type(caught.value.__cause__) is ValueError
        assert caught.value.__cause__.args == conversion.value.args
        assert str(caught.value) == f"{field} cannot be converted to a decimal string"
        assert caught.value.request_sent is None
        assert sent == provider_calls == []
    else:
        getattr(client, method)(**arguments)
        assert len(sent) == len(provider_calls) == 1
        assert sent[0].url.host == "api.example.invalid"
        assert sent[0].url.path == path
        is_query = method == "list_product_reservations"
        assert sent[0].method == ("GET" if is_query else "POST")
        assert (sent[0].url.query if is_query else sent[0].content) == (
            b"Device=AD&Version=250601003&AppVersion=7.0.8&Key=SYNTHETIC-APP-KEY" + before + text + after
        )
    assert sys.get_int_max_str_digits() == limit


@pytest.mark.parametrize("factory", ["detail", "verification"])
@pytest.mark.parametrize(
    "response",
    [
        pytest.param({}, id="mapping"),
        pytest.param(None, id="none"),
        pytest.param(object(), id="object"),
        pytest.param(api.RefundCommissionResponse(str_result="SUCC"), id="other-response"),
    ],
)
def test_refund_factory_wrong_response_is_rejected_before_send(f8_client_factory, factory, response):
    sent = []
    provider_calls = []
    config = synthetic_config(
        dynapath=api.DynapathConfig(
            enabled=True,
            token_provider=lambda context: provider_calls.append(context) or "SYNTHETIC-TOKEN",
        )
    )
    client = f8_client_factory(_recording(sent), config=config)
    with pytest.raises(INVALID) as caught:
        if factory == "detail":
            ticket = api.PaidTicket.from_refund_detail(response)
            client.refund(ticket, commission=F8["refund"]["commission"])
        else:
            request = api.StationRefundExecutionRequest.from_verification(
                response, customer_phone="00000000000", customer_name="SYNTHETIC-NAME"
            )
            client.refund_station_ticket(request)
    expected_type = "RefundTicketDetailResponse" if factory == "detail" else "StationRefundVerificationResponse"
    assert str(caught.value) == f"{factory} must be a {expected_type}"
    assert caught.value.request_sent is None
    assert sent == provider_calls == []
