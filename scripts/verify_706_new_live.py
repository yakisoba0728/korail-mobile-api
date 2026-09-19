# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Redacted, paced live checks for the newly connected 7.0.6 reads.

Two opt-ins are required: ``KORAIL_MOBILE_API_LIVE=1`` (the package-wide live
switch) and ``KORAIL_LIVE_706_READS=1`` (this script). Neither alone runs.
No raw body, credential, cookie, PNR or ticket identity is printed or saved.
Authenticated checks prompt for a member and password in memory. This script
never sends a reservation, payment, refund, or other mutation.

The device identity comes from ``KORAIL_DYNAPATH_DEVICE_ID``,
``KORAIL_DYNAPATH_OS_VERSION`` and ``KORAIL_DYNAPATH_DEVICE_MODEL``
(``korail_mobile_api.live.build_config_from_env``; README says where to read
them), so every run is made from the same device. Without them it stops, with
exit code 2, before asking for anything.
"""

from __future__ import annotations

import argparse
import getpass
import os
import time
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from korail_mobile_api import KorailClient, TrainSearchQuery
from korail_mobile_api.live import build_config_from_env


MIN_INTERVAL_SECONDS = 1.5


def _summary(value: Any) -> str:
    result = getattr(value, "str_result", None)
    code = getattr(value, "h_msg_cd", None)
    if result is None or code is None:
        response = getattr(value, "response", None)
        result = result or getattr(response, "str_result", None)
        code = code or getattr(response, "h_msg_cd", None)
    parts = [f"result={result or 'parsed'}", f"code={code or 'none'}"]
    for attr in ("trains", "days", "items", "reservations"):
        rows = getattr(value, attr, None)
        if isinstance(rows, (tuple, list)):
            parts.append(f"{attr}={len(rows)}")
    return " ".join(parts)


def _check(label: str, run: Callable[[], Any]) -> Any | None:
    try:
        value = run()
    except Exception as exc:
        print(
            f"{label}: error={type(exc).__name__} "
            f"code={getattr(exc, 'code', None) or 'none'}",
            flush=True,
        )
        return None
    print(f"{label}: {_summary(value)}", flush=True)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authenticated", action="store_true")
    parser.add_argument("--special-only", action="store_true")
    parser.add_argument("--ticket-maas-history", action="store_true")
    args = parser.parse_args()
    if (
        os.environ.get("KORAIL_MOBILE_API_LIVE") != "1"
        or os.environ.get("KORAIL_LIVE_706_READS") != "1"
    ):
        raise SystemExit(
            "Set KORAIL_MOBILE_API_LIVE=1 and KORAIL_LIVE_706_READS=1 to run live checks"
        )

    # The device identity comes from the environment, as it does for the
    # real-card scripts, so every run is made from the same real device, not a
    # new synthetic one. Checked before any secret is asked for.
    try:
        config = build_config_from_env()
    except RuntimeError as exc:
        print(f"ABORTED: {exc}")
        return 2
    client = KorailClient(config)
    last_send = 0.0

    def pace(_request: Any) -> None:
        nonlocal last_send
        elapsed = time.monotonic() - last_send
        if last_send and elapsed < MIN_INTERVAL_SECONDS:
            time.sleep(MIN_INTERVAL_SECONDS - elapsed)
        last_send = time.monotonic()

    client.http._client.event_hooks["request"].append(pace)
    try:
        if args.ticket_maas_history:
            member = getpass.getpass("member (hidden): ")
            password = getpass.getpass("password (hidden): ")
            if _check("login", lambda: client.login(member, password)) is None:
                return 1
            today = date.today()
            history = _check(
                "ticket_history",
                lambda: client.get_ticket_list(
                    mode="2",
                    boarding_date_from=(today - timedelta(days=365)).strftime("%Y%m%d"),
                    boarding_date_to=today.strftime("%Y%m%d"),
                ),
            )
            if history is None:
                return 1
            for reservation in sorted(
                history.reservations,
                key=lambda row: len(row.tickets),
                reverse=True,
            ):
                valid = [
                    ticket
                    for ticket in reservation.tickets
                    if ticket.pnr_no
                    and ticket.sale_window_no
                    and ticket.return_sale_date
                    and ticket.sale_sequence
                    and ticket.return_password
                ]
                if not valid or len(valid) > 8:
                    continue
                pnr_no = valid[0].pnr_no
                same_pnr = [ticket for ticket in valid if ticket.pnr_no == pnr_no]
                refs = tuple(
                    "-".join((
                        ticket.sale_window_no,
                        ticket.return_sale_date,
                        ticket.sale_sequence,
                        ticket.return_password,
                    ))
                    for ticket in same_pnr
                )
                print(f"ticket_maas_input: ticket_count={len(refs)}", flush=True)
                return 0 if _check(
                    "ticket_maas_menu",
                    lambda pnr=pnr_no, numbers=refs: client.get_maas_menu_list(
                        pnr_no=pnr,
                        ticket_return_numbers=numbers,
                    ),
                ) is not None else 1
            print("ticket_maas_input: no_complete_historical_reference", flush=True)
            return 1
        if args.special_only:
            target = (date.today() + timedelta(days=14)).strftime("%Y%m%d")
            query = TrainSearchQuery(
                "서울", "부산", target, departure_time="060000"
            )
            return 0 if _check(
                "search_special_first_page",
                lambda: client.search_trains(query, use_special_schedule=True),
            ) is not None else 1
        calendar = _check("calendar", client.get_train_calendar)
        target = date.today() + timedelta(days=14)
        if calendar is not None:
            available = sorted(
                day.run_date
                for day in calendar.days
                if day.run_date and day.run_date.isdigit()
            )
            future = [value for value in available if value >= target.strftime("%Y%m%d")]
            if future:
                target = date.fromisoformat(
                    f"{future[0][:4]}-{future[0][4:6]}-{future[0][6:8]}"
                )
        date_text = target.strftime("%Y%m%d")
        query = TrainSearchQuery("서울", "부산", date_text, departure_time="060000")
        _check("search_legacy", lambda: client.search_trains(query))
        _check(
            "search_special",
            lambda: client.search_trains(query, use_special_schedule=True),
        )
        _check("maas_generic", client.get_maas_menu_list)
        if not args.authenticated:
            return 0

        member = getpass.getpass("member (hidden): ")
        password = getpass.getpass("password (hidden): ")
        if _check("login", lambda: client.login(member, password)) is None:
            return 1
        _check("search_special_authenticated", lambda: client.search_trains(
            query, use_special_schedule=True
        ))
        _check(
            "delay_discount_query",
            lambda: client.get_delay_discount_tickets(
                (date.today() + timedelta(days=30)).strftime("%Y%m%d")
            ),
        )
        _check("product_reservations", client.get_product_reservations)
        _check("coupons", client.get_discount_coupons)
        return 0
    finally:
        if (args.authenticated or args.ticket_maas_history) and client.session.current is not None:
            _check("logout", client.logout)
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())
