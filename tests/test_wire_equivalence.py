"""Refactor oracle: normalized v2.6.1 smoke requests, in observed request order.

Captured once from the SDK at tag ``pre-3.0-overhaul`` (4412c93), not from the app or server.
The pin preserves decoded body pairs, not raw encoding, full query order, ports or raw headers.
Never edit or regenerate it; new byte contracts use independent literal expectations below.
"""

from __future__ import annotations

import ast
import hashlib
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

import httpx
import pytest
from conftest import synthetic_config

sys.path.insert(0, str(Path(__file__).parent))

from test_public_api_smoke import F8_CASE_DATA, _f8_arguments  # noqa: E402

import korail_mobile_api as api  # noqa: E402

PIN_PATH = Path(__file__).with_name("_wire_pin.py")
FIXED_TIME = 4102444800.0
CONFIG_VARIANTS: dict[str, dict[str, Any]] = {
    "lang-empty": {"lang": ""},
    "lang-set": {"lang": "SYNTHETIC-LANG"},
    "app-version-none": {"app_version": None},
    "app-version-7010": {"app_version": "7.0.10", "version": "250722001"},
    "key-empty": {"key": ""},
}
# 3.0 renamed these methods; the pin keeps the v2.6.1 scenario names.
RENAMED = {
    "retrieve_delivered_ticket": "recall_delivered_ticket",
    "confirm_standby_hold": "set_standby_options",
    "get_reservation_history": "list_reservations",
    "verify_station_ticket_refund": "check_station_ticket_refund",
    "execute_station_ticket_refund": "refund_station_ticket",
    "get_common_code": "get_common_codes",
    "get_cart_list": "list_cart_items",
    "get_ticket_list": "list_tickets",
    "get_maas_menu_list": "list_maas_menus",
    "get_crew_request_list": "list_crew_request_reasons",
    "get_discount_coupons": "list_discount_coupons",
    "get_deposit_banks": "list_deposit_banks",
    "get_delay_discount_tickets": "list_delay_discount_tickets",
    "get_product_reservations": "list_product_reservations",
    "get_trip_change_dates": "list_trip_change_dates",
    "get_transfer_stations": "list_transfer_stations",
    "get_seat_cars": "list_seat_cars",
    "get_multi_child_discount_targets": "list_multi_child_discount_targets",
    "get_maas_service_details": "list_maas_services",
    "get_maas_station_data": "list_maas_stations",
    "get_station_data": "list_stations",
    "get_station_info": "get_station_list_version",
    "get_pbp_acceptance_specifications": "list_pbp_acceptances",
    "get_recent_delivery_history": "list_recent_delivery_recipients",
    "get_discount_card_usage_history": "list_discount_card_usages",
    "get_limousine_schedules": "list_airport_bus_schedules",
    "get_limousine_seat_inventory": "get_airport_bus_seat_inventory",
    "reserve_limousine": "reserve_airport_bus",
    "get_free_seat_car_info": "get_free_seat_cars",
    "get_self_seat_change_info": "get_self_seat_change_options",
    "get_merge_seats_inquiry": "get_merge_seat_options",
    "get_original_ticket_inquiry": "get_original_tickets",
    "get_customer_trip_info": "get_trip_preferences",
    "get_korail_point_summary": "get_point_summary",
    "get_price_fare_quote": "get_fare_quote",
    "get_pass_available_dates": "get_pass_availability",
    "get_refund_commission": "get_refund_fee",
    "get_self_checkin_info": "get_self_checkin",
}
# 3.0 removed these methods; their pinned requests stay as a record and are not run.
REMOVED = frozenset({"get_notice", "register_discount_card"})
# Pin scenario names (v2.6.1 method names).
VARIANT_METHODS = (
    "login",
    "search_trains",
    "get_train_schedule",
    "get_deposit_banks",
    "get_commuter_kind_menu",
    "get_app_data",
    "get_ticket_list",
    "get_refund_commission",
    "reserve",
    "pay_with_card",
    "get_limousine_schedules",
)


def _config(**overrides: Any) -> api.KorailConfig:
    base: dict[str, Any] = {
        "base_url": "https://api.example.invalid",
        "netfunnel_url": "https://queue.example.invalid",
        "key": "SYNTHETIC-APP-KEY",
    }
    return api.KorailConfig(**{**base, **overrides})


def _record(request: httpx.Request) -> dict[str, Any]:
    content = request.content
    return {
        "method": request.method,
        "url": f"{request.url.scheme}://{request.url.host}{request.url.path}",
        "query": [list(pair) for pair in request.url.params.multi_items()],
        "headers": {k: v for k, v in request.headers.items() if k not in {"host", "content-length"}},
        "body": [list(pair) for pair in parse_qsl(content.decode(), keep_blank_values=True)],
    }


@contextmanager
def _fixed_time() -> Iterator[None]:
    original = time.time
    time.time = lambda: FIXED_TIME
    try:
        yield
    finally:
        time.time = original


def run_scenario(method_name: str, overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    pending = list(F8_CASE_DATA[method_name]["exchanges"])
    seen: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(_record(request))
        payload = pending.pop(0)["response"]
        if isinstance(payload, str):
            return httpx.Response(200, text=payload)
        headers = (
            {"set-cookie": "JSESSIONID=SYNTHETIC-SESSION; Path=/"}
            if request.url.path.endswith("login.Login")
            else {}
        )
        return httpx.Response(200, json=payload, headers=headers)

    with _fixed_time():
        arguments = _f8_arguments(method_name)[method_name]
        client = api.KorailClient(_config(**(overrides or {})), transport=httpx.MockTransport(handle))
        try:
            if method_name != "login":
                client.session.current = api.KorailSession(
                    jsessionid="SYNTHETIC-SESSION",
                    member_no="SYNTHETIC-MEMBER",
                    member_card_no="SYNTHETIC-MEMBER-CARD",
                    customer_no="SYNTHETIC-CUSTOMER",
                    raw={"source": "f8-synthetic"},
                )
                client.http.cookies.set("JSESSIONID", "SYNTHETIC-SESSION")
            getattr(client, method_name)(**arguments)
        finally:
            client.close()
    return seen


def scenarios() -> Iterator[tuple[str, str, dict[str, Any] | None]]:
    old_names = {new: old for old, new in RENAMED.items()}
    for method_name in F8_CASE_DATA:
        yield old_names.get(method_name, method_name), method_name, None
    for variant, overrides in CONFIG_VARIANTS.items():
        for scenario_name in VARIANT_METHODS:
            yield f"{scenario_name}[{variant}]", RENAMED.get(scenario_name, scenario_name), overrides


def _load_pin() -> dict[str, list[dict[str, Any]]]:
    namespace: dict[str, Any] = {}
    exec(PIN_PATH.read_text(encoding="utf-8"), namespace)
    pin: dict[str, list[dict[str, Any]]] = namespace["WIRE_PIN"]
    return pin


@pytest.mark.parametrize(("scenario", "method_name", "overrides"), list(scenarios()))
def test_requests_match_the_v261_wire(
    scenario: str, method_name: str, overrides: dict[str, Any] | None, f8_block_sockets: None
) -> None:
    assert run_scenario(method_name, overrides) == _load_pin()[scenario]


def test_pin_covers_every_scenario() -> None:
    assert set(_load_pin()) == {scenario for scenario, _, _ in scenarios()} | REMOVED


def test_wire_oracle_has_no_write_entrypoint() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, ast.If)
        and any(isinstance(child, ast.Name) and child.id == "__name__" for child in ast.walk(node.test))
        for node in tree.body
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            assert not (isinstance(node.func, ast.Name) and node.func.id == "open")
            assert not (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"write_text", "write_bytes", "open", "rename", "replace", "unlink"}
            )
    assert hashlib.sha256(PIN_PATH.read_bytes()).hexdigest() == (
        "2cfbda0d65b926435d9b0076fab4dfa8e6d306ce4ce4016e8e84f38089196cb4"
    )


def test_public_common_codes_keep_literal_body_and_origin(scripted_client_factory) -> None:
    """Canonical byte contract added independently of the normalized historical capture."""
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC"}],
        config=synthetic_config(
            base_url="https://api.example.invalid:8443",
            device="SYNTHETIC-DEVICE",
            version="SYNTHETIC-VERSION",
            app_version="SYNTHETIC-APP",
            key="",
            lang="",
            device_width=0,
            device_height=1,
            android_sdk_int=2,
        ),
    )
    client.get_common_codes(["한 글+%&=\n", "", "A B", "C+D"])
    assert not pending and len(requests) == 1
    request = requests[0]
    assert str(request.url) == "https://api.example.invalid:8443/classes/com.korail.mobile.common.code.do"
    assert (request.url.scheme, request.url.host, request.url.port) == ("https", "api.example.invalid", 8443)
    assert request.headers["host"] == "api.example.invalid:8443"
    assert request.content == (
        b"Device=SYNTHETIC-DEVICE&Version=SYNTHETIC-VERSION&AppVersion=SYNTHETIC-APP"
        b"&code=%ED%95%9C+%EA%B8%80%2B%25%26%3D%0A&code=&code=A+B&code=C%2BD"
        b"&deviceWidth=0&deviceHeight=1&OSVersion=2"
    )
    assert request.url.query == b""


def test_public_commuter_menu_keeps_literal_query_and_empty_body(scripted_client_factory) -> None:
    """HTTPX 0.28.0 switched QueryParams from its %20 encoder to stdlib's + encoder."""
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC"}],
        config=synthetic_config(
            base_url="https://api.example.invalid:8443",
            device="SYNTHETIC-DEVICE",
            version="SYNTHETIC-VERSION",
            key="",
        ),
    )
    client.get_commuter_kind_menu("한 글+%&=")
    assert not pending and len(requests) == 1
    request = requests[0]
    assert request.method == "GET"
    assert request.url.port == 8443
    assert request.url.path == "/classes/com.korail.mobile.push.cmtrKnd.do"
    httpx_version = tuple(int(part) for part in httpx.__version__.split(".")[:2])
    if httpx_version < (0, 28):
        expected_query = (
            b"Device=SYNTHETIC-DEVICE&Version=SYNTHETIC-VERSION&Key="
            b"&cmtrKndCd=%ED%95%9C%20%EA%B8%80%2B%25%26%3D"
        )
    else:
        expected_query = (
            b"Device=SYNTHETIC-DEVICE&Version=SYNTHETIC-VERSION&Key=&cmtrKndCd=%ED%95%9C+%EA%B8%80%2B%25%26%3D"
        )
    assert request.url.query == expected_query
    assert request.content == b""
    assert "content-type" not in request.headers
