"""Drive the live KORAIL read surface once and capture every RAW response.

This script exists so a live verification run is reproducible. It logs in a
single time, reuses that session for every subsequent call, derives real
arguments from real responses (search a route, pick a real train, then ask for
that train's cars/seats/fares/schedule), and records the untouched response body
for each call BEFORE the client parses it. The captures are the evidence used to
check the parsers in ``src/`` against what the server actually sends.

Safety posture
--------------
* Two opt-ins are required: ``KORAIL_MOBILE_API_LIVE=1`` (the package-wide live
  switch) and ``KORAIL_LIVE_READ_SURFACE=1`` (this script). Neither alone runs.
* The module is import-safe: importing it performs no I/O and reads no
  credentials. Everything happens under ``main()``.
* Every request is paced by :class:`_Pacer` (default 1.5s minimum spacing, i.e.
  <= 40 requests/minute) because KORAIL bans IPs for macro-like traffic. The
  pacing is enforced at the HTTP hook, so calls the client makes internally are
  throttled too.
* This script NEVER pays and NEVER refunds. It does not import ``CardPayment``
  or ``PaidTicket``, and the only :class:`MutationConsent` it can build sets
  ``allow_reserve``/``allow_cancel`` -- ``allow_payment`` and ``allow_refund``
  are never passed. :func:`_reserve_consent` and :func:`_cancel_consent` are the
  only consent factories, and both are asserted to withhold money categories.
* ``--reserve`` (gated additionally by ``KORAIL_LIVE_ALLOW_RESERVE=1``) performs
  ONE hold and immediately cancels it. The PNR is printed the instant it exists,
  the cancel is retried once on failure, and an uncancelled hold aborts the run
  with an unmissable banner rather than being left behind.

Output
------
``--out DIR`` receives ``raw/NNN-<step>.json`` (the verbatim bodies -- these
contain personal data and must stay OUTSIDE the repo, e.g. in a scratchpad) and
``summary.json`` plus stdout progress, both of which are passed through
:func:`~korail_mobile_api.redaction.redact_value` so credentials and personal
fields never reach the console or the summary.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx

from korail_mobile_api import (
    CommuterInitialRequest,
    FreeSeatCarRequest,
    GiftTicketHistoryRequest,
    GuideSeatConditionRequest,
    KorailClient,
    LimousineScheduleQuery,
    LimousineSeatInventoryQuery,
    MergeSeatsInquiryRequest,
    MutationConsent,
    OriginalTicketReference,
    PassMenuData,
    PassScheduleRequest,
    PriceFareLeg,
    PriceFareQuoteRequest,
    SeatAssignmentScheduleRequest,
    TicketDuplicationCheckRequest,
    TrainSearchQuery,
    TrainSummary,
)
from korail_mobile_api.live import (
    build_config_from_env,
    live_enabled,
    read_credentials_from_env,
)
from korail_mobile_api.redaction import redact_value

LIVE_READ_SURFACE_ENV = "KORAIL_LIVE_READ_SURFACE"
LIVE_RESERVE_ENV = "KORAIL_LIVE_ALLOW_RESERVE"
DEFAULT_MIN_INTERVAL_S = 1.5


class _Pacer:
    """Enforce a minimum spacing between outbound requests."""

    def __init__(self, min_interval_s: float) -> None:
        self.min_interval_s = min_interval_s
        self._last: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last is not None:
            remaining = self.min_interval_s - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
        self._last = time.monotonic()


@dataclass
class _HttpRecord:
    method: str
    path: str
    status: int
    body: str
    dynapath_result: str | None = None


@dataclass
class _StepResult:
    name: str
    method: str
    ok: bool
    detail: Any = None
    error: str | None = None
    http: list[_HttpRecord] = field(default_factory=list)


def _install_hooks(
    client: KorailClient,
    records: list[_HttpRecord],
    pacer: _Pacer,
) -> None:
    """Pace every request and record every raw response body.

    The response hook runs before the client parses anything, so a body that
    makes a parser raise is still captured verbatim.
    """
    inner = client.http._client

    def on_request(request: httpx.Request) -> None:
        pacer.wait()

    def on_response(response: httpx.Response) -> None:
        response.read()
        records.append(
            _HttpRecord(
                method=response.request.method,
                path=response.request.url.path,
                status=response.status_code,
                body=response.text,
                dynapath_result=response.headers.get("DynaPath-Result"),
            )
        )

    hooks = dict(inner.event_hooks)
    hooks["request"] = [*hooks.get("request", []), on_request]
    hooks["response"] = [*hooks.get("response", []), on_response]
    inner.event_hooks = hooks


def _reserve_consent() -> MutationConsent:
    """Consent that permits exactly one live hold and nothing else."""
    consent = MutationConsent(allow_reserve=True, dry_run=False)
    assert not consent.allow_payment and not consent.allow_refund
    return consent


def _cancel_consent() -> MutationConsent:
    """Consent that permits exactly one live cancellation and nothing else."""
    consent = MutationConsent(allow_cancel=True, dry_run=False)
    assert not consent.allow_payment and not consent.allow_refund
    return consent


class SurfaceRunner:
    """Drive read methods in dependency order, recording each one."""

    def __init__(
        self,
        client: KorailClient,
        records: list[_HttpRecord],
        *,
        only: frozenset[str] | None = None,
    ) -> None:
        self.client = client
        self._records = records
        self.results: list[_StepResult] = []
        #: When set, every step whose name is not listed is skipped without
        #: touching the network. Used by ``--skip-reads`` so the reserve round
        #: trip costs the minimum number of live requests.
        self.only = only

    def run(self, name: str, method: str, call: Callable[[], Any]) -> Any:
        if self.only is not None and name not in self.only:
            return None
        start = len(self._records)
        try:
            value = call()
        except (KeyboardInterrupt, SystemExit):
            # Never swallow an abort: a live run must stay interruptible.
            raise
        except Exception as exc:  # noqa: BLE001 - a failure IS the evidence
            result = _StepResult(
                name=name,
                method=method,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                http=self._records[start:],
            )
            self.results.append(result)
            print(f"  [FAIL] {name}: {redact_value(result.error)}")
            return None
        result = _StepResult(
            name=name,
            method=method,
            ok=True,
            detail=_describe(value),
            http=self._records[start:],
        )
        self.results.append(result)
        print(f"  [ ok ] {name}: {json.dumps(redact_value(result.detail), ensure_ascii=False)}")
        return value


def _describe(value: Any) -> Any:
    """Summarise a parsed result without dumping personal data."""
    if value is None:
        return None
    summary: dict[str, Any] = {"type": type(value).__name__}
    for attr in ("h_msg_cd", "str_result"):
        if hasattr(value, attr):
            summary[attr] = getattr(value, attr)
    for attr in (
        "items",
        "trains",
        "cars",
        "seats",
        "stations",
        "tickets",
        "coupons",
        "reservations",
        "journeys",
        "options",
        "schedules",
    ):
        collection = getattr(value, attr, None)
        if isinstance(collection, (list, tuple)):
            summary[f"{attr}_count"] = len(collection)
    raw = getattr(value, "raw", None)
    if isinstance(raw, dict):
        summary["raw_keys"] = sorted(raw)[:40]
    return summary


def _first_train(trains: list[TrainSummary]) -> TrainSummary | None:
    for train in trains:
        if train.general_reservation_code == "11":
            return train
    return trains[0] if trains else None


_TICKET_IDENTITY_KEYS = (
    "h_orgtk_ret_sale_dt",
    "h_orgtk_wct_no",
    "h_orgtk_sale_sqno",
    "h_orgtk_ret_pwd",
)


def _find_ticket_reference(raw: Any) -> OriginalTicketReference | None:
    """Recursively locate one original-ticket identity in a raw response.

    The account may own no tickets at all, in which case this returns ``None``
    and the ticket-identity reads are reported as unreachable rather than
    invented.
    """
    if isinstance(raw, dict):
        if all(
            isinstance(raw.get(key), str) and raw.get(key, "").strip()
            for key in _TICKET_IDENTITY_KEYS
        ):
            return OriginalTicketReference(
                sale_window_no=raw["h_orgtk_wct_no"],
                sale_date=raw["h_orgtk_ret_sale_dt"],
                sale_sequence=raw["h_orgtk_sale_sqno"],
                return_password=raw["h_orgtk_ret_pwd"],
            )
        for value in raw.values():
            found = _find_ticket_reference(value)
            if found is not None:
                return found
    elif isinstance(raw, list):
        for item in raw:
            found = _find_ticket_reference(item)
            if found is not None:
                return found
    return None


def _drive_ticket_identity_reads(
    runner: SurfaceRunner,
    ticket: OriginalTicketReference,
) -> None:
    client = runner.client
    runner.run(
        "ticket_receipt",
        "get_ticket_receipt",
        lambda: client.get_ticket_receipt(
            ticket.sale_date,
            ticket.sale_window_no,
            ticket.sale_sequence,
            ticket.return_password,
        ),
    )
    runner.run(
        "delivery_recipient",
        "get_delivery_recipient",
        lambda: client.get_delivery_recipient(ticket),
    )
    runner.run(
        "pbp_acceptance_specifications",
        "get_pbp_acceptance_specifications",
        lambda: client.get_pbp_acceptance_specifications((ticket,)),
    )
    runner.run(
        "platform_numbers",
        "get_platform_numbers",
        lambda: client.get_platform_numbers((ticket,)),
    )


def _drive_reads(runner: SurfaceRunner, args: argparse.Namespace) -> dict[str, Any]:
    """Call the read surface, deriving arguments from real responses."""
    client = runner.client
    ctx: dict[str, Any] = {}
    date = args.date
    departure = os.environ.get("KORAIL_DEPARTURE_STATION", "서울")
    arrival = os.environ.get("KORAIL_ARRIVAL_STATION", "부산")
    departure_code = os.environ.get("KORAIL_DEPARTURE_STATION_CODE", "0001")
    arrival_code = os.environ.get("KORAIL_ARRIVAL_STATION_CODE", "0020")
    departure_time = os.environ.get("KORAIL_DEPARTURE_TIME", "060000")

    print("-- anonymous reads --")
    runner.run("app_data", "get_app_data", client.get_app_data)
    runner.run("notice", "get_notice", client.get_notice)
    runner.run("uuid", "get_uuid", client.get_uuid)
    runner.run("service_status", "get_service_status", client.get_service_status)
    runner.run("station_info", "get_station_info", client.get_station_info)
    runner.run("station_data", "get_station_data", client.get_station_data)
    runner.run("train_calendar", "get_train_calendar", client.get_train_calendar)
    runner.run("common_code", "get_common_code", lambda: client.get_common_code(""))
    maas_menu = runner.run(
        "maas_menu_list", "get_maas_menu_list", client.get_maas_menu_list
    )
    maas_code = os.environ.get("KORAIL_MAAS_SERVICE_CODE")
    if not maas_code and maas_menu is not None:
        maas_code = next(
            (
                item.additional_service_code
                for item in maas_menu.items
                if item.uses_station_selection
            ),
            None,
        )
    if maas_code:
        ctx["maas_service_code"] = maas_code
        runner.run(
            "maas_station_data",
            "get_maas_station_data",
            lambda: client.get_maas_station_data(maas_code),
        )
    runner.run(
        "transfer_stations",
        "get_transfer_stations",
        lambda: client.get_transfer_stations(departure_code, arrival_code),
    )
    runner.run(
        "crew_request_list",
        "get_crew_request_list",
        lambda: client.get_crew_request_list("1"),
    )
    limousine = runner.run(
        "limousine_schedules",
        "get_limousine_schedules",
        lambda: client.get_limousine_schedules(
            LimousineScheduleQuery(
                departure_date=date,
                departure_station_code=departure_code,
                arrival_station_code=arrival_code,
                service_code="001",
                room_class_code="1",
                departure_time=departure_time,
                train_no="",
                seat_attribute_code="",
                reservation_sale_division_code="1",
            )
        ),
    )
    if limousine is not None and limousine.schedules:
        bus = limousine.schedules[0]
        runner.run(
            "limousine_seat_inventory",
            "get_limousine_seat_inventory",
            lambda: client.get_limousine_seat_inventory(
                LimousineSeatInventoryQuery(
                    train_class_code=bus.train_class_code or "",
                    service_code=bus.service_code or "001",
                    run_date=bus.run_date or date,
                    train_no=bus.train_no or "",
                    car_no="0001",
                    room_class_code="1",
                    departure_station_code=bus.departure_station_code or departure_code,
                    arrival_station_code=bus.arrival_station_code or arrival_code,
                    seat_attribute_code="015",
                    departure_run_order=bus.departure_run_order or "",
                    arrival_run_order=bus.arrival_run_order or "",
                    passenger_count=1,
                    product_no="",
                    is_arrow=False,
                )
            ),
        )
    else:
        print("  [skip] limousine seat/view reads: route has no limousine schedule")

    print("-- login --")
    member_no, password = read_credentials_from_env()
    session = runner.run(
        "login", "login", lambda: client.login(member_no, password)
    )
    if session is None:
        print("login failed; skipping authenticated reads")
        return ctx

    print("-- authenticated account reads --")
    # These four answer P058 ("please log in") when called anonymously, so they
    # are driven only after the session exists.
    pass_menu = runner.run(
        "pass_menu", "get_pass_menu", lambda: client.get_pass_menu("1")
    )
    if pass_menu is not None and pass_menu.items:
        ctx["pass_menu_item"] = pass_menu.items[0]
    runner.run(
        "pass_available_dates",
        "get_pass_available_dates",
        lambda: client.get_pass_available_dates("1", "1", "1"),
    )
    runner.run(
        "commuter_kind_menu",
        "get_commuter_kind_menu",
        lambda: client.get_commuter_kind_menu("1"),
    )
    runner.run(
        "guide_seat_condition",
        "get_guide_seat_condition",
        lambda: client.get_guide_seat_condition(
            GuideSeatConditionRequest(seat_attribute_code="015")
        ),
    )
    runner.run("deposit_banks", "get_deposit_banks", client.get_deposit_banks)
    runner.run("trip_menu", "get_trip_menu", client.get_trip_menu)
    runner.run("cart_list", "get_cart_list", client.get_cart_list)
    runner.run(
        "delay_discount_tickets",
        "get_delay_discount_tickets",
        lambda: client.get_delay_discount_tickets(date),
    )
    runner.run(
        "discount_coupons", "get_discount_coupons", client.get_discount_coupons
    )
    history = runner.run(
        "reservation_history",
        "get_reservation_history",
        client.get_reservation_history,
    )
    tickets = runner.run("ticket_list", "get_ticket_list", client.get_ticket_list)
    products = runner.run(
        "product_reservations",
        "get_product_reservations",
        client.get_product_reservations,
    )
    ticket = None
    for source in (tickets, history):
        if source is not None:
            ticket = _find_ticket_reference(getattr(source, "raw", None))
            if ticket is not None:
                break
    if ticket is not None:
        ctx["ticket_reference"] = True
        _drive_ticket_identity_reads(runner, ticket)
    else:
        print("  [skip] ticket-identity reads: account owns no ticket to reference")
    pnr = next(
        (
            item.pnr_no
            for item in (history.items if history is not None else ())
            if item.pnr_no
        ),
        None,
    )
    if pnr:
        runner.run(
            "check_ticket_duplication",
            "check_ticket_duplication",
            lambda: client.check_ticket_duplication(
                TicketDuplicationCheckRequest(pnr_no=pnr)
            ),
        )
    else:
        print("  [skip] check_ticket_duplication: no reservation PNR on the account")
    if products is not None and products.items:
        product = products.items[0]
        runner.run(
            "product_detail",
            "get_product_detail",
            lambda: client.get_product_detail(
                product.virtual_reservation_no or "", "1"
            ),
        )
    else:
        print("  [skip] product_detail: account has no product reservation")
    # PassScheduleRequest.selected_train_code must be non-empty and names a
    # commuter-pass train the caller has already chosen. Nothing in the read
    # surface hands one back, so this read is only reachable with a
    # caller-supplied code.
    selected_train_code = os.environ.get("KORAIL_PASS_TRAIN_CODE", "")
    if ctx.get("pass_menu_item") is not None and selected_train_code:
        runner.run(
            "pass_schedule",
            "get_pass_schedule",
            lambda: client.get_pass_schedule(
                PassScheduleRequest(
                    selected_train_code=selected_train_code,
                    departure_date=date,
                    departure_time=departure_time,
                    transfer_type_code="",
                    pass_kind_code="1",
                    pass_period_code="1",
                    pass_age_code="1",
                    page_no="1",
                    page_size="10",
                    departure_station_name=departure,
                    arrival_station_name=arrival,
                    weekend_use_flag="N",
                )
            ),
        )
    else:
        print(
            "  [skip] pass_schedule: needs a caller-chosen commuter-pass train "
            "code (set KORAIL_PASS_TRAIN_CODE)"
        )
    runner.run(
        "multi_child_discount_targets",
        "get_multi_child_discount_targets",
        lambda: client.get_multi_child_discount_targets(date),
    )
    runner.run(
        "customer_trip_info",
        "get_customer_trip_info",
        client.get_customer_trip_info,
    )
    runner.run(
        "maas_service_details",
        "get_maas_service_details",
        client.get_maas_service_details,
    )
    runner.run(
        "trip_change_dates",
        "get_trip_change_dates",
        lambda: client.get_trip_change_dates(date),
    )
    runner.run(
        "gift_ticket_list",
        "get_gift_ticket_list",
        lambda: client.get_gift_ticket_list(
            GiftTicketHistoryRequest.sent(date, date)
        ),
    )
    runner.run(
        "commuter_info",
        "get_commuter_info",
        lambda: client.get_commuter_info(
            CommuterInitialRequest(PassMenuData(commuter_kind_code="1"))
        ),
    )
    runner.run(
        "recent_delivery_history",
        "get_recent_delivery_history",
        client.get_recent_delivery_history,
    )

    print("-- train search and train-derived reads --")
    query = TrainSearchQuery(
        departure_station_code=departure,
        arrival_station_code=arrival,
        departure_date=date,
        departure_time=departure_time,
    )
    search = runner.run(
        "search_trains", "search_trains", lambda: client.search_trains(query)
    )
    train = _first_train(search.trains) if search is not None else None
    continuation = search.next_page() if search is not None else None
    if continuation is not None:
        runner.run(
            "search_trains_page_2",
            "search_trains",
            lambda: client.search_trains(query, continuation=continuation),
        )
    elif search is not None:
        # A live ScheduleView sets h_next_pg_flg="Y" but sends
        # h_qry_st_no_next/h_trn_no_next as null, so next_page() correctly
        # refuses to build a half-filled cursor that would re-request page one.
        print(
            f"  [note] next_page_flag={search.metadata.next_page_flag!r} but the "
            f"cursor fields are "
            f"{search.metadata.next_query_station_no!r}/"
            f"{search.metadata.next_train_no!r}; no second page is reachable"
        )
    if train is None:
        print("no train available; skipping train-derived reads")
        return ctx
    ctx["train_no"] = train.train_no
    print(f"  picked train_no={train.train_no} rsv_code={train.general_reservation_code}")
    runner.run(
        "train_schedule",
        "get_train_schedule",
        lambda: client.get_train_schedule(
            train.departure_date or date, train.train_no
        ),
    )
    # PriceFareLeg.goods_no must be non-empty. A live ScheduleView row carries
    # no h_gd_no/txtGdNo at all and the envelope's h_gd_no is "", so fall back
    # to the envelope and report the read as unreachable when both are empty.
    goods_no = train.goods_no or (
        search.metadata.product_no if search is not None else None
    )
    if goods_no:
        runner.run(
            "price_fare_quote",
            "get_price_fare_quote",
            lambda: client.get_price_fare_quote(
                PriceFareQuoteRequest(
                    legs=(
                        PriceFareLeg(
                            departure_station_code=train.departure_station_code
                            or departure_code,
                            arrival_station_code=train.arrival_station_code
                            or arrival_code,
                            run_date=train.run_date or date,
                            train_no=train.train_no,
                            goods_no=goods_no,
                            requested_seat_attribute_code=train.seat_attribute_code
                            or "015",
                            train_group_code=train.train_group_code or "",
                            standing_train_classification_code="",
                        ),
                    )
                )
            ),
        )
    else:
        print(
            "  [skip] price_fare_quote: the live search sends no goods number "
            "(row h_gd_no/txtGdNo absent, envelope h_gd_no empty)"
        )
    runner.run(
        "free_seat_car_info",
        "get_free_seat_car_info",
        lambda: client.get_free_seat_car_info(
            FreeSeatCarRequest(
                run_date=train.run_date or date,
                train_no=train.train_no,
                departure_construction_order=train.departure_construction_order or "",
                arrival_construction_order=train.arrival_construction_order or "",
                departure_run_order=train.departure_run_order or "",
                arrival_run_order=train.arrival_run_order or "",
            )
        ),
    )
    runner.run(
        "seat_assignment_schedule",
        "get_seat_assignment_schedule",
        lambda: client.get_seat_assignment_schedule(
            SeatAssignmentScheduleRequest(
                menu_id="11",
                departure_date=train.departure_date or date,
                departure_time=train.departure_time or departure_time,
                departure_station_name=train.departure_station_name or departure,
                arrival_station_name=train.arrival_station_name or arrival,
                train_group_code=train.train_group_code or "",
                room_class_code="1",
                seat_attribute_code=train.seat_attribute_code or "015",
                passenger_count=1,
                standing_detour_division_name="",
                # h_chg_trn_dv_cd on the live row: "1" = 직통 (direct).
                transfer_type_code=str(train.raw.get("h_chg_trn_dv_cd") or "1"),
                connection_arrival_station_name="",
            )
        ),
    )
    runner.run(
        "merge_seats_inquiry",
        "get_merge_seats_inquiry",
        lambda: client.get_merge_seats_inquiry(
            MergeSeatsInquiryRequest(
                boarding_datetime=(train.departure_date or date)
                + (train.departure_time or departure_time),
                run_datetime=(train.run_date or date)
                + (train.departure_time or departure_time),
                train_no=train.train_no,
                departure_station_name=train.departure_station_name or departure,
                arrival_station_name=train.arrival_station_name or arrival,
                selected_station_name=train.departure_station_name or departure,
                room_class_code="1",
                seat_attribute_code=train.seat_attribute_code or "015",
                passenger_count=1,
            )
        ),
    )
    cars = runner.run(
        "seat_cars", "get_seat_cars", lambda: client.get_seat_cars(train)
    )
    car_no = None
    if cars is not None and cars.cars:
        for car in cars.cars:
            try:
                car_no = int(car.car_no)
            except (TypeError, ValueError):
                continue
            break
    if car_no is not None:
        ctx["car_no"] = car_no
        runner.run(
            "seat_inventory",
            "get_seat_inventory",
            lambda: client.get_seat_inventory(train, car_no),
        )
    ctx["train"] = train
    return ctx


def _run_reserve_round_trip(runner: SurfaceRunner, train: TrainSummary) -> None:
    """Hold one seat and release it immediately. Never leaves a hold behind."""
    client = runner.client
    print("-- reserve/cancel round trip --")
    hold = runner.run(
        "reserve", "reserve", lambda: client.reserve(train, consent=_reserve_consent())
    )
    if hold is None:
        # The call failed, but the server may still have committed a hold (for
        # example a timeout after commit). Prove the account is clean instead of
        # assuming it.
        print("reserve did not return a hold; verifying no hold was orphaned")
        history = runner.run(
            "reservation_history_after_failed_reserve",
            "get_reservation_history",
            client.get_reservation_history,
        )
        outstanding = [item for item in (history.items if history else ()) if item.pnr_no]
        if outstanding:
            banner = "!" * 72
            print(
                f"\n{banner}\n!! RESERVE FAILED BUT {len(outstanding)} RESERVATION(S) EXIST\n"
                + "\n".join(f"!! pnr_no={item.pnr_no}" for item in outstanding)
                + f"\n!! Cancel them manually in the KORAIL app NOW.\n{banner}\n",
                flush=True,
            )
            raise SystemExit(2)
        print("   confirmed: no outstanding reservation on the account")
        return
    pnr = getattr(hold, "pnr_no", None)
    # Print the PNR the instant it exists, before anything else can fail.
    print(f"!! LIVE HOLD CREATED pnr_no={pnr}", flush=True)
    print(
        f"   strResult={hold.str_result} h_msg_cd={hold.h_msg_cd} "
        f"h_msg_txt={hold.h_msg_txt}",
        flush=True,
    )
    for attempt in (1, 2):
        cancel = runner.run(
            f"cancel_unpaid_hold_attempt_{attempt}",
            "cancel_unpaid_hold",
            lambda: client.cancel_unpaid_hold(hold, consent=_cancel_consent()),
        )
        if cancel is not None and cancel.str_result == "SUCC":
            print(
                f"   cancel strResult={cancel.str_result} "
                f"h_msg_cd={cancel.h_msg_cd} h_msg_txt={cancel.h_msg_txt}",
                flush=True,
            )
            runner.run(
                "reservation_history_after_cancel",
                "get_reservation_history",
                client.get_reservation_history,
            )
            return
    banner = "!" * 72
    print(f"\n{banner}\n!! CANCEL FAILED -- OUTSTANDING HOLD pnr_no={pnr}\n"
          f"!! Cancel it manually in the KORAIL app NOW.\n{banner}\n", flush=True)
    raise SystemExit(2)


def _write_output(out_dir: Path, results: list[_StepResult]) -> None:
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    index = 0
    summary = []
    for result in results:
        files = []
        for record in result.http:
            index += 1
            name = f"{index:03d}-{result.name}.json"
            (raw_dir / name).write_text(
                json.dumps(
                    {
                        "step": result.name,
                        "method": result.method,
                        "http_method": record.method,
                        "path": record.path,
                        "status": record.status,
                        "dynapath_result": record.dynapath_result,
                        "body": record.body,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            files.append(name)
        summary.append(
            {
                "step": result.name,
                "method": result.method,
                "ok": result.ok,
                "error": redact_value(result.error),
                "detail": redact_value(result.detail),
                "raw_files": files,
                "paths": [record.path for record in result.http],
                "statuses": [record.status for record in result.http],
            }
        )
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nraw captures  -> {raw_dir} (UNREDACTED; keep outside the repo)")
    print(f"redacted summary -> {out_dir / 'summary.json'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="capture directory")
    parser.add_argument(
        "--date",
        default=os.environ.get("KORAIL_TEST_DATE", ""),
        help="departure date YYYYMMDD (must be today or later)",
    )
    parser.add_argument(
        "--min-interval",
        type=float,
        default=DEFAULT_MIN_INTERVAL_S,
        help="minimum seconds between requests (rate-limit protection)",
    )
    parser.add_argument(
        "--reserve",
        action="store_true",
        help=(
            "perform ONE hold and immediately cancel it; also requires "
            f"{LIVE_RESERVE_ENV}=1"
        ),
    )
    parser.add_argument(
        "--skip-reads",
        action="store_true",
        help=(
            "run only login + train search (the minimum needed to reserve), so "
            "a --reserve pass does not re-drive the whole read surface"
        ),
    )
    parser.add_argument(
        "--only",
        default="",
        help=(
            "comma-separated step names to run (login is always kept), so a "
            "single fix can be re-verified live without a full pass"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not live_enabled():
        raise SystemExit("Set KORAIL_MOBILE_API_LIVE=1 to run the live capture")
    if os.environ.get(LIVE_READ_SURFACE_ENV) != "1":
        raise SystemExit(
            f"Set {LIVE_READ_SURFACE_ENV}=1 to opt in to the live read-surface capture"
        )
    if args.reserve and os.environ.get(LIVE_RESERVE_ENV) != "1":
        raise SystemExit(
            f"--reserve additionally requires {LIVE_RESERVE_ENV}=1"
        )
    if not args.date or len(args.date) != 8 or not args.date.isdigit():
        raise SystemExit("--date must be an 8-digit YYYYMMDD departure date")
    today = time.strftime("%Y%m%d")
    if args.date < today:
        raise SystemExit(
            f"--date {args.date} is in the past (today is {today}); "
            "a past date makes every search return nothing"
        )
    if args.min_interval < 1.0:
        raise SystemExit("--min-interval below 1.0s risks a KORAIL IP ban")

    records: list[_HttpRecord] = []
    pacer = _Pacer(args.min_interval)
    client = KorailClient(build_config_from_env())
    _install_hooks(client, records, pacer)
    only: frozenset[str] | None = None
    if args.only.strip():
        only = frozenset(
            {"login", *(name.strip() for name in args.only.split(",") if name.strip())}
        )
    elif args.skip_reads:
        only = frozenset(
            {
                "login",
                "search_trains",
                "reserve",
                "cancel_unpaid_hold_attempt_1",
                "cancel_unpaid_hold_attempt_2",
                "reservation_history_after_cancel",
            }
        )
    runner = SurfaceRunner(client, records, only=only)
    try:
        ctx = _drive_reads(runner, args)
        train = ctx.get("train")
        if args.reserve and isinstance(train, TrainSummary):
            _run_reserve_round_trip(runner, train)
        elif args.reserve:
            print("no reservable train found; skipping the round trip")
    finally:
        args.out.mkdir(parents=True, exist_ok=True)
        _write_output(args.out, runner.results)
        client.close()
    passed = sum(1 for result in runner.results if result.ok)
    print(f"\n{passed}/{len(runner.results)} steps returned a parsed result")
    return 0


if __name__ == "__main__":
    sys.exit(main())
