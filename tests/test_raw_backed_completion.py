from __future__ import annotations

import math

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.http import KorailHttpClient
from korail_mobile_api.models import BaseKorailResponse, KorailSession
from korail_mobile_api.parsers import parse_seat_inventory_response
from korail_mobile_api.read_models import (
    CartListResponse,
    DelayDiscountTicketListResponse,
    ProductReservationListResponse,
)
from korail_mobile_api.read_parsers import (
    parse_cart_list_response,
    parse_delay_discount_ticket_response,
    parse_deposit_bank_response,
    parse_product_reservation_list_response,
    parse_service_status_response,
    parse_trip_menu_response,
)


RESULT_ONLY_CASES = (
    (
        "cart_list_result_only_success.json",
        parse_cart_list_response,
        "get_cart_list",
        (),
        CartListResponse,
        None,
    ),
    (
        "delay_discount_tickets_result_only_success.json",
        parse_delay_discount_ticket_response,
        "get_delay_discount_tickets",
        ("20991230",),
        DelayDiscountTicketListResponse,
        None,
    ),
    (
        "product_reservations_result_only_success.json",
        parse_product_reservation_list_response,
        "get_product_reservations",
        (3, 7),
        ProductReservationListResponse,
        37,
    ),
)


@pytest.mark.parametrize(
    (
        "fixture_name",
        "parser",
        "_method_name",
        "_args",
        "response_type",
        "total_count",
    ),
    RESULT_ONLY_CASES,
)
def test_result_only_success_parsers_preserve_optional_envelope_fields(
    load_json_fixture,
    fixture_name,
    parser,
    _method_name,
    _args,
    response_type,
    total_count,
):
    raw = load_json_fixture(fixture_name)

    result = parser(raw)

    assert isinstance(result, response_type)
    assert result.h_msg_cd is None
    assert result.h_msg_txt is None
    assert result.str_result == "SUCC"
    assert result.items == ()
    assert result.raw is raw
    if isinstance(result, ProductReservationListResponse):
        assert result.total_count == total_count


@pytest.mark.parametrize(
    (
        "fixture_name",
        "_parser",
        "method_name",
        "args",
        "response_type",
        "total_count",
    ),
    RESULT_ONLY_CASES,
)
def test_result_only_success_reaches_route_parser_through_http_gate(
    load_json_fixture,
    fixture_name,
    _parser,
    method_name,
    args,
    response_type,
    total_count,
):
    raw = load_json_fixture(fixture_name)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=raw,
            headers={"Content-Type": "text/html"},
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session",
        member_no="synthetic-member",
    )
    try:
        result = getattr(client, method_name)(*args)
    finally:
        client.close()

    assert len(requests) == 1
    assert isinstance(result, response_type)
    assert result.h_msg_cd is None
    assert result.h_msg_txt is None
    assert result.str_result == "SUCC"
    assert result.items == ()
    if isinstance(result, ProductReservationListResponse):
        assert result.total_count == total_count


@pytest.mark.parametrize(
    ("fixture_name", "parser", "_method_name", "_args", "_type", "_count"),
    RESULT_ONLY_CASES,
)
@pytest.mark.parametrize(
    ("result_value", "error_match"),
    [
        ("FAIL", "result-only"),
        ("SYNTHETIC-UNKNOWN", "result-only"),
        (None, "result-only"),
        (7, "strResult"),
    ],
)
def test_result_only_envelopes_require_the_exact_success_string(
    load_json_fixture,
    fixture_name,
    parser,
    _method_name,
    _args,
    _type,
    _count,
    result_value,
    error_match,
):
    raw = load_json_fixture(fixture_name)
    raw["strResult"] = result_value

    with pytest.raises(KorailProtocolError, match=error_match):
        parser(raw)


@pytest.mark.parametrize(
    ("fixture_name", "parser", "_method_name", "_args", "_type", "_count"),
    RESULT_ONLY_CASES,
)
def test_result_only_envelopes_type_check_present_optional_fields(
    load_json_fixture,
    fixture_name,
    parser,
    _method_name,
    _args,
    _type,
    _count,
):
    raw = load_json_fixture(fixture_name)
    raw["h_msg_cd"] = ["synthetic-invalid"]

    with pytest.raises(KorailProtocolError, match="h_msg_cd"):
        parser(raw)


@pytest.mark.parametrize(
    ("fixture_name", "parser", "_method_name", "_args", "_type", "_count"),
    RESULT_ONLY_CASES,
)
def test_full_failures_remain_typed_for_result_only_routes(
    load_json_fixture,
    fixture_name,
    parser,
    _method_name,
    _args,
    _type,
    _count,
):
    raw = load_json_fixture(fixture_name)
    raw.update(
        {
            "h_msg_cd": "SYNTHETIC-FAILURE",
            "h_msg_txt": "synthetic failure",
            "strResult": "FAIL",
        }
    )
    with pytest.raises(KorailAppError):
        parser(raw)

    raw.update(
        {
            "h_msg_cd": "P058",
            "h_msg_txt": "synthetic expiry",
        }
    )
    with pytest.raises(KorailSessionExpiredError):
        parser(raw)


@pytest.mark.parametrize(
    "parser",
    [parse_deposit_bank_response, parse_trip_menu_response],
)
def test_session_coupled_route_parsers_preserve_full_server_expiry(parser):
    with pytest.raises(KorailSessionExpiredError):
        parser(
            {
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic expiry",
                "strResult": "FAIL",
            }
        )


def test_strict_parser_default_rejects_result_only_envelope():
    with pytest.raises(KorailProtocolError):
        parse_service_status_response({"strResult": "SUCC"})


@pytest.mark.parametrize("method_name", ["post_form", "get_json"])
def test_http_default_still_requires_the_full_envelope(method_name):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"strResult": "SUCC"},
            headers={"Content-Type": "text/html"},
        )

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    try:
        if method_name == "post_form":
            call = lambda: client.post_form(
                "/classes/com.korail.mobile.dlay.dptnBank.do",
                include_dynapath=False,
            )
        else:
            call = lambda: client.get_json(
                "/classes/com.korail.mobile.common.stationinfo",
                include_dynapath=False,
            )
        with pytest.raises(KorailProtocolError):
            call()
    finally:
        client.close()


def _parse_decimal_window(raw: dict):
    response = BaseKorailResponse.from_raw(raw)
    return parse_seat_inventory_response(response)


def test_seat_window_ascii_decimal_fixture_normalizes_to_finite_floats(
    load_json_fixture,
):
    raw = load_json_fixture("seat_inventory_decimal_string_windows.json")

    result = _parse_decimal_window(raw)

    assert result.windows[0].start_location_ratio == 12.5
    assert result.windows[0].close_location_ratio == -3.25
    assert math.isfinite(result.windows[0].start_location_ratio)
    assert math.isfinite(result.windows[0].close_location_ratio)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0.0),
        (-4, -4.0),
        (2.5, 2.5),
        ("0", 0.0),
        ("-4", -4.0),
        ("00012.500", 12.5),
        ("-0003.250", -3.25),
        ("125.75", 125.75),
    ],
)
@pytest.mark.parametrize("field_name", ["st_loc_rt", "cls_loc_rt"])
def test_seat_window_ratios_accept_numbers_and_strict_ascii_decimals(
    load_json_fixture,
    value,
    expected,
    field_name,
):
    raw = load_json_fixture("seat_inventory_decimal_string_windows.json")
    raw["windowList"][0] = {"st_loc_rt": 0.0, "cls_loc_rt": 0.0}
    raw["windowList"][0][field_name] = value

    result = _parse_decimal_window(raw)

    window = result.windows[0]
    parsed = (
        window.start_location_ratio
        if field_name == "st_loc_rt"
        else window.close_location_ratio
    )
    assert parsed == expected
    assert type(parsed) is float


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        None,
        "",
        " ",
        " 1",
        "1 ",
        "１",
        "+1",
        ".5",
        "1.",
        "1e2",
        "nan",
        "inf",
        [],
        {},
        "9" * 400,
        math.inf,
        -math.inf,
        math.nan,
    ],
)
@pytest.mark.parametrize("field_name", ["st_loc_rt", "cls_loc_rt"])
def test_seat_window_ratios_reject_non_ascii_malformed_and_non_finite_values(
    load_json_fixture,
    value,
    field_name,
):
    raw = load_json_fixture("seat_inventory_decimal_string_windows.json")
    raw["windowList"][0] = {"st_loc_rt": 0.0, "cls_loc_rt": 0.0}
    raw["windowList"][0][field_name] = value

    with pytest.raises(KorailProtocolError, match=field_name):
        _parse_decimal_window(raw)


@pytest.mark.parametrize("field_name", ["st_loc_rt", "cls_loc_rt"])
def test_seat_window_ratios_remain_required(load_json_fixture, field_name):
    raw = load_json_fixture("seat_inventory_decimal_string_windows.json")
    raw["windowList"][0] = {"st_loc_rt": 0.0, "cls_loc_rt": 0.0}
    raw["windowList"][0].pop(field_name)

    with pytest.raises(KorailProtocolError, match=field_name):
        _parse_decimal_window(raw)
