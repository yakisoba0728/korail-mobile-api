from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from typing import get_type_hints
from urllib.parse import parse_qs

import httpx
import korail_mobile_api
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_payloads import (
    build_cart_list_form,
    build_delay_discount_ticket_form,
    build_discount_coupon_form,
    build_pass_availability_form,
    build_product_detail_query,
    build_product_reservations_query,
    build_service_status_query,
    build_ticket_receipt_form,
    build_trip_menu_form,
)
from korail_mobile_api.read_models import (
    CartItem,
    CartListResponse,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    PassAvailabilityResponse,
    PassOffice,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ReceiptPayment,
    ReservationHistoryResponse,
    ReservationHistoryTrain,
    ServiceStatusResponse,
    TicketReceipt,
    TicketReceiptResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)
from korail_mobile_api.read_parsers import (
    parse_cart_list_response,
    parse_delay_discount_ticket_response,
    parse_deposit_bank_response,
    parse_discount_coupon_response,
    parse_pass_availability_response,
    parse_product_detail_response,
    parse_product_reservation_list_response,
    parse_reservation_history_response,
    parse_service_status_response,
    parse_ticket_receipt_response,
    parse_trip_menu_response,
)
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
)


PUBLIC_METHODS = {
    "get_service_status": ["self", "timestamp_ms"],
    "get_cart_list": [
        "self",
        "pnr_no",
        "additional_service_request_no",
    ],
    "get_deposit_banks": ["self"],
    "get_delay_discount_tickets": ["self", "departure_date_to"],
    "get_discount_coupons": ["self", "page_no", "pnr_no"],
    "get_pass_available_dates": [
        "self",
        "kind_code",
        "period_code",
        "age_code",
    ],
    "get_trip_menu": ["self"],
    "get_product_reservations": ["self", "page_no", "page_size"],
    "get_product_detail": [
        "self",
        "reservation_no",
        "reservation_sequence",
    ],
    "get_ticket_receipt": [
        "self",
        "sale_date",
        "window_no",
        "sale_sequence",
        "return_password",
    ],
    "get_reservation_history": ["self"],
}

NEW_ROUTES = {
    ("POST", "/classes/com.korail.mobile.cart.showCartList"),
    ("POST", "/classes/com.korail.mobile.dlay.dptnBank.do"),
    ("POST", "/classes/com.korail.mobile.passCard.DelayDiscountView"),
    ("POST", "/classes/com.korail.mobile.passCard.CouponView"),
    ("POST", "/classes/com.korail.mobile.pass.passInfoList"),
    ("POST", "/classes/com.korail.mobile.pass.trGdMenuLt.do"),
    ("GET", "/classes/com.korail.mobile.product.ReservationList"),
    ("GET", "/classes/com.korail.mobile.product.ReservationDetail"),
    ("POST", "/classes/com.korail.mobile.receipt.ReceiptInfo"),
    ("GET", "/classes/com.korail.mobile.reservation.ReservationView"),
}

EXACT_FIELDS = {
    "/file/CACHE/MobileService.cache": {"timeStamp"},
    "/classes/com.korail.mobile.cart.showCartList": {
        "Device",
        "Version",
        "Key",
        "pnrNo",
        "addSrvReqNo",
    },
    "/classes/com.korail.mobile.dlay.dptnBank.do": {
        "Device",
        "Version",
        "Key",
    },
    "/classes/com.korail.mobile.passCard.DelayDiscountView": {
        "Device",
        "Version",
        "Key",
        "dptDtTo",
    },
    "/classes/com.korail.mobile.passCard.CouponView": {
        "Device",
        "Version",
        "Key",
        "txtSelPage",
        "pnrNo",
    },
    "/classes/com.korail.mobile.pass.passInfoList": {
        "Device",
        "Version",
        "Key",
        "txtCmtrKndCd",
        "txtCmtrUtlTrmCd",
        "txtCmtrUtlAgeCd",
    },
    "/classes/com.korail.mobile.pass.trGdMenuLt.do": {
        "Device",
        "Version",
    },
    "/classes/com.korail.mobile.product.ReservationList": {
        "Device",
        "Version",
        "Key",
        "txtSelPage",
        "txtCntPerPage",
    },
    "/classes/com.korail.mobile.product.ReservationDetail": {
        "Device",
        "Version",
        "Key",
        "txtVrRsNo",
        "txtVrRsvSqNo",
    },
    "/classes/com.korail.mobile.receipt.ReceiptInfo": {
        "Device",
        "Version",
        "Key",
        "h_orgtk_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_tk_ret_pwd",
    },
    "/classes/com.korail.mobile.reservation.ReservationView": {
        "Device",
        "Version",
        "Key",
    },
}


REQUEST_CASES = (
    (
        "get_service_status",
        (1234567890,),
        "GET",
        "/file/CACHE/MobileService.cache",
        {"timeStamp": "1234567890"},
        False,
    ),
    (
        "get_cart_list",
        ("SYNTHETIC-PNR", "SYNTHETIC-SERVICE"),
        "POST",
        "/classes/com.korail.mobile.cart.showCartList",
        {"pnrNo": "SYNTHETIC-PNR", "addSrvReqNo": "SYNTHETIC-SERVICE"},
        True,
    ),
    (
        "get_deposit_banks",
        (),
        "POST",
        "/classes/com.korail.mobile.dlay.dptnBank.do",
        {},
        True,
    ),
    (
        "get_delay_discount_tickets",
        ("20260714",),
        "POST",
        "/classes/com.korail.mobile.passCard.DelayDiscountView",
        {"dptDtTo": "20260714"},
        True,
    ),
    (
        "get_discount_coupons",
        (2, "SYNTHETIC-PNR"),
        "POST",
        "/classes/com.korail.mobile.passCard.CouponView",
        {"txtSelPage": "2", "pnrNo": "SYNTHETIC-PNR"},
        True,
    ),
    (
        "get_pass_available_dates",
        ("K", "P", "A"),
        "POST",
        "/classes/com.korail.mobile.pass.passInfoList",
        {
            "txtCmtrKndCd": "K",
            "txtCmtrUtlTrmCd": "P",
            "txtCmtrUtlAgeCd": "A",
        },
        False,
    ),
    (
        "get_trip_menu",
        (),
        "POST",
        "/classes/com.korail.mobile.pass.trGdMenuLt.do",
        {},
        True,
    ),
    (
        "get_product_reservations",
        (2, 30),
        "GET",
        "/classes/com.korail.mobile.product.ReservationList",
        {"txtSelPage": "2", "txtCntPerPage": "30"},
        True,
    ),
    (
        "get_product_detail",
        ("SYNTHETIC-RESERVATION", "3"),
        "GET",
        "/classes/com.korail.mobile.product.ReservationDetail",
        {"txtVrRsNo": "SYNTHETIC-RESERVATION", "txtVrRsvSqNo": "3"},
        True,
    ),
    (
        "get_ticket_receipt",
        ("20260714", "001", "2", "SYNTHETIC-PASSWORD"),
        "POST",
        "/classes/com.korail.mobile.receipt.ReceiptInfo",
        {
            "h_orgtk_sale_dt": "20260714",
            "h_orgtk_wct_no": "001",
            "h_orgtk_sale_sqno": "2",
            "h_orgtk_tk_ret_pwd": "SYNTHETIC-PASSWORD",
        },
        True,
    ),
    (
        "get_reservation_history",
        (),
        "GET",
        "/classes/com.korail.mobile.reservation.ReservationView",
        {},
        True,
    ),
)

INVALID_CALLS = (
    ("get_service_status", (True,)),
    ("get_delay_discount_tickets", ("２０２６０７１４",)),
    ("get_discount_coupons", (0, "")),
    ("get_pass_available_dates", ("", "P", "A")),
    ("get_product_reservations", (1, 0)),
    ("get_product_detail", ("", "1")),
    ("get_ticket_receipt", ("20260714", "", "1", "pw")),
)

AUTH_CALLS = (
    ("get_cart_list", ()),
    ("get_deposit_banks", ()),
    ("get_delay_discount_tickets", ("20260714",)),
    ("get_discount_coupons", ()),
    ("get_product_reservations", ()),
    ("get_product_detail", ("SYNTHETIC-RESERVATION", "1")),
    ("get_ticket_receipt", ("20260714", "001", "1", "pw")),
    ("get_trip_menu", ()),
    ("get_reservation_history", ()),
)

FIXTURE_WRAPPERS = {
    "cart_list_success.json": ("cart_infos", "cart_info"),
    "deposit_banks_success.json": ("dptnBank", None),
    "delay_discount_tickets_success.json": ("disc_infos", "disc_info"),
    "discount_coupons_success.json": ("coupon_infos", "coupon_info"),
    "pass_availability_success.json": (
        "pass_info",
        "ticket_info",
        "wct_info",
    ),
    "trip_menu_success.json": ("menuList", None),
    "product_reservations_success.json": ("mainInfo", "entity"),
    "product_detail_success.json": ("mainInfo", "entityOne"),
    "ticket_receipt_success.json": ("receipt_infos", "receipt_info"),
    "reservation_history_success.json": ("jrny_infos", "jrny_info"),
}

SECRET_SENTINELS = {
    "SYNTHETIC-PNR-SECRET",
    "SYNTHETIC-RETURN-PASSWORD",
    "SYNTHETIC-CARD-NUMBER",
    "SYNTHETIC-ACCOUNT-NUMBER",
    "SYNTHETIC-APPROVAL-NUMBER",
    "SYNTHETIC-RESERVATION-NUMBER",
    "SYNTHETIC-RAW-SECRET",
}

MODEL_EXPORTS = {
    "ServiceStatusResponse": ServiceStatusResponse,
    "CartItem": CartItem,
    "CartListResponse": CartListResponse,
    "DepositBank": DepositBank,
    "DepositBankListResponse": DepositBankListResponse,
    "DelayDiscountTicket": DelayDiscountTicket,
    "DelayDiscountTicketListResponse": DelayDiscountTicketListResponse,
    "DiscountCoupon": DiscountCoupon,
    "DiscountCouponListResponse": DiscountCouponListResponse,
    "PassOffice": PassOffice,
    "PassAvailabilityResponse": PassAvailabilityResponse,
    "TripMenuContent": TripMenuContent,
    "TripMenuItem": TripMenuItem,
    "TripMenuResponse": TripMenuResponse,
    "ProductReservation": ProductReservation,
    "ProductReservationListResponse": ProductReservationListResponse,
    "ProductDetailResponse": ProductDetailResponse,
    "ReceiptPayment": ReceiptPayment,
    "TicketReceipt": TicketReceipt,
    "TicketReceiptResponse": TicketReceiptResponse,
    "ReservationHistoryTrain": ReservationHistoryTrain,
    "ReservationHistoryResponse": ReservationHistoryResponse,
}


def _common_fields(config: KorailConfig) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
    }


def test_successful_read_routes_have_exact_final_fields():
    assert len(KORAIL_READ_ONLY_ROUTES) == 56
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    for path, fields in EXACT_FIELDS.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == fields


def test_new_public_methods_have_exact_signatures_and_return_hints():
    for name, parameters in PUBLIC_METHODS.items():
        method = getattr(KorailClient, name)
        assert list(inspect.signature(method).parameters) == parameters
        assert (
            get_type_hints(method)["return"].__module__
            == "korail_mobile_api.read_models"
        )


def test_read_payload_builders_emit_only_exact_caller_fields():
    config = KorailConfig()
    assert build_service_status_query(7) == {"timeStamp": "7"}
    assert build_cart_list_form("PNR", "SERVICE") == {
        "pnrNo": "PNR",
        "addSrvReqNo": "SERVICE",
    }
    assert build_cart_list_form() == {"pnrNo": "", "addSrvReqNo": ""}
    assert build_delay_discount_ticket_form("20260714") == {
        "dptDtTo": "20260714"
    }
    assert build_discount_coupon_form() == {"txtSelPage": "1", "pnrNo": ""}
    assert build_pass_availability_form("K", "P", "A") == {
        "txtCmtrKndCd": "K",
        "txtCmtrUtlTrmCd": "P",
        "txtCmtrUtlAgeCd": "A",
    }
    assert build_trip_menu_form(config) == {
        "Device": config.device,
        "Version": config.version,
    }
    assert build_product_reservations_query() == {
        "txtSelPage": "1",
        "txtCntPerPage": "20",
    }
    assert build_product_detail_query("RESERVATION", "SEQUENCE") == {
        "txtVrRsNo": "RESERVATION",
        "txtVrRsvSqNo": "SEQUENCE",
    }
    assert build_ticket_receipt_form("20260714", "001", "2", "pw") == {
        "h_orgtk_sale_dt": "20260714",
        "h_orgtk_wct_no": "001",
        "h_orgtk_sale_sqno": "2",
        "h_orgtk_tk_ret_pwd": "pw",
    }


def test_read_payload_builders_have_exact_public_signatures():
    expected = {
        build_service_status_query: ["timestamp_ms"],
        build_cart_list_form: ["pnr_no", "additional_service_request_no"],
        build_delay_discount_ticket_form: ["departure_date_to"],
        build_discount_coupon_form: ["page_no", "pnr_no"],
        build_pass_availability_form: [
            "kind_code",
            "period_code",
            "age_code",
        ],
        build_trip_menu_form: ["config"],
        build_product_reservations_query: ["page_no", "page_size"],
        build_product_detail_query: [
            "reservation_no",
            "reservation_sequence",
        ],
        build_ticket_receipt_form: [
            "sale_date",
            "window_no",
            "sale_sequence",
            "return_password",
        ],
    }
    for builder, parameter_names in expected.items():
        assert list(inspect.signature(builder).parameters) == parameter_names


def test_service_status_query_uses_current_epoch_milliseconds(monkeypatch):
    import korail_mobile_api.read_payloads as read_payloads

    monkeypatch.setattr(read_payloads.time, "time", lambda: 1234.567)
    assert build_service_status_query() == {"timeStamp": "1234567"}


@pytest.mark.parametrize(
    ("builder", "args", "match"),
    [
        (build_cart_list_form, (1, ""), "pnr_no"),
        (build_cart_list_form, ("", None), "additional_service_request_no"),
        (build_discount_coupon_form, (1, None), "pnr_no"),
    ],
)
def test_optional_identifier_payload_fields_still_require_strings(
    builder,
    args,
    match,
):
    with pytest.raises(ValueError, match=match):
        builder(*args)


@pytest.mark.parametrize(
    (
        "method_name",
        "args",
        "expected_method",
        "path",
        "caller_fields",
        "requires_auth",
    ),
    REQUEST_CASES,
)
def test_successful_read_requests_are_exact_single_calls_without_dynapath(
    method_name,
    args,
    expected_method,
    path,
    caller_fields,
    requires_auth,
):
    requests: list[httpx.Request] = []
    provider_contexts = []

    def token_provider(context):
        provider_contexts.append(context)
        return "must-not-be-used"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC-SUCCESS",
                "h_msg_txt": "synthetic success",
                "strResult": "SUCC",
            },
        )

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({path}),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    if requires_auth:
        client.session.current = KorailSession(
            jsessionid="synthetic-session",
            member_no="synthetic-member",
        )
    try:
        result = getattr(client, method_name)(*args)
    finally:
        client.close()

    expected_fields = dict(caller_fields)
    if path != "/file/CACHE/MobileService.cache":
        expected_fields.update(_common_fields(config))
    if path == "/classes/com.korail.mobile.pass.trGdMenuLt.do":
        expected_fields.pop("Key")

    assert len(requests) == 1
    request = requests[0]
    assert request.method == expected_method
    assert request.url.path == path
    assert request.url.scheme == "https"
    assert request.url.host == "smart.letskorail.com"
    if expected_method == "GET":
        assert parse_qs(
            request.url.query.decode(), keep_blank_values=True
        ) == {key: [value] for key, value in expected_fields.items()}
        assert request.content == b""
    else:
        assert request.url.query == b""
        assert parse_qs(
            request.content.decode(), keep_blank_values=True
        ) == {key: [value] for key, value in expected_fields.items()}
    assert "x-dynapath-m-token" not in request.headers
    assert provider_contexts == []
    assert result.__class__ is get_type_hints(
        getattr(KorailClient, method_name)
    )["return"]


@pytest.mark.parametrize(("method_name", "args"), INVALID_CALLS)
def test_invalid_read_arguments_fail_before_transport(method_name, args):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session",
        member_no="synthetic-member",
    )
    try:
        with pytest.raises(ValueError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 0


@pytest.mark.parametrize(("method_name", "args"), AUTH_CALLS)
def test_account_reads_require_a_local_session_before_transport(
    method_name,
    args,
):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAuthError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 0


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("get_delay_discount_tickets", ("invalid",)),
        ("get_discount_coupons", (0, "")),
        ("get_product_reservations", (0, 0)),
        ("get_product_detail", ("", "")),
        ("get_ticket_receipt", ("invalid", "", "", "")),
    ],
)
def test_authenticated_reads_check_session_before_payload_validation(
    method_name,
    args,
):
    client = KorailClient(
        transport=httpx.MockTransport(
            lambda _: pytest.fail("transport must not be called")
        )
    )
    try:
        with pytest.raises(KorailAuthError):
            getattr(client, method_name)(*args)
    finally:
        client.close()


@pytest.mark.parametrize(("method_name", "args"), AUTH_CALLS)
def test_p058_clears_session_for_every_new_authenticated_read(
    method_name,
    args,
):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic expiry",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session",
        member_no="synthetic-member",
    )
    client.http.cookies.set("JSESSIONID", "synthetic-session")
    try:
        with pytest.raises(KorailSessionExpiredError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies


@pytest.mark.parametrize(
    ("method_name", "args"),
    (
        ("get_service_status", (1,)),
        ("get_pass_available_dates", ("K", "P", "A")),
    ),
)
def test_account_neutral_reads_do_not_require_a_local_session(
    method_name,
    args,
):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC-SUCCESS",
                "h_msg_txt": "synthetic success",
                "strResult": "SUCC",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    assert client.session.current is None
    try:
        getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 1


@pytest.mark.parametrize(("fixture_name", "wrappers"), FIXTURE_WRAPPERS.items())
def test_synthetic_success_fixtures_use_the_verified_wrapper_shapes(
    fixture_name,
    wrappers,
    load_json_fixture,
):
    raw = load_json_fixture(fixture_name)
    assert all(
        isinstance(raw[field], str)
        for field in ("h_msg_cd", "h_msg_txt", "strResult")
    )
    if len(wrappers) == 3:
        assert all(isinstance(raw[key], list) for key in wrappers)
    else:
        outer, inner = wrappers
        if inner is None:
            assert isinstance(raw[outer], list)
        else:
            assert isinstance(raw[outer], dict)
            assert isinstance(raw[outer][inner], list)


def test_service_status_parser_preserves_the_typed_envelope_and_raw_identity(
    load_json_fixture,
):
    raw = load_json_fixture("service_status_success.json")
    result = parse_service_status_response(raw)
    assert result.h_msg_cd == "SYNTHETIC-SUCCESS"
    assert result.h_msg_txt == "synthetic service status"
    assert result.str_result == "SUCC"
    assert result.raw is raw


def test_cart_parser_exposes_all_approved_fields_and_raw_identity(
    load_json_fixture,
):
    raw = load_json_fixture("cart_list_success.json")
    source_item = raw["cart_infos"]["cart_info"][0]
    result = parse_cart_list_response(raw)
    assert isinstance(result, CartListResponse)
    assert result.raw is raw
    assert isinstance(result.items, tuple)
    assert len(result.items) == 1
    item = result.items[0]
    assert item.service_code == "SYNTHETIC-SERVICE-CODE"
    assert item.provider_name == "Synthetic Provider"
    assert item.product_name == "Synthetic Product"
    assert item.item_type == "Synthetic Item Type"
    assert item.departure_date == "20991231"
    assert item.received_amount == "12345"
    assert item.reservation_received_date == "20990101"
    assert item.ticket_count == 2
    assert item.usage_start_date == "20990201"
    assert item.usage_start_time == "090000"
    assert item.usage_close_time == "180000"
    assert item.usage_window == ("20990201", "090000", "180000")
    assert item.partner_reservation_no == "SYNTHETIC-PARTNER-RESERVATION"
    assert item.pnr_no == "SYNTHETIC-PNR-SECRET"
    assert item.lump_sum_target_no == "SYNTHETIC-LUMP-SUM-NUMBER"
    assert item.customer_no == "SYNTHETIC-CUSTOMER-NUMBER"
    assert item.virtual_reservation_no == "SYNTHETIC-VIRTUAL-RESERVATION"
    assert item.raw is source_item


def test_bank_and_delay_parsers_expose_approved_fields(load_json_fixture):
    bank_raw = load_json_fixture("deposit_banks_success.json")
    banks = parse_deposit_bank_response(bank_raw)
    assert isinstance(banks, DepositBankListResponse)
    assert banks.items == (
        DepositBank(
            code="SYNTHETIC-BANK",
            display_name="Synthetic Bank",
            raw=bank_raw["dptnBank"][0],
        ),
    )
    assert banks.items[0].raw is bank_raw["dptnBank"][0]

    delay_raw = load_json_fixture("delay_discount_tickets_success.json")
    delays = parse_delay_discount_ticket_response(delay_raw)
    assert isinstance(delays, DelayDiscountTicketListResponse)
    ticket = delays.items[0]
    assert ticket.fare == "1234"
    assert ticket.usable_until_date == "20991231"
    assert ticket.original_sale_date == "20990101"
    assert ticket.window_no == "SYNTHETIC-WINDOW-NUMBER"
    assert ticket.sale_sequence == "SYNTHETIC-SALE-SEQUENCE"
    assert ticket.return_password == "SYNTHETIC-RETURN-PASSWORD"
    assert ticket.raw is delay_raw["disc_infos"]["disc_info"][0]


def test_coupon_parser_exposes_values_remarks_pages_and_sensitive_number(
    load_json_fixture,
):
    raw = load_json_fixture("discount_coupons_success.json")
    result = parse_discount_coupon_response(raw)
    assert isinstance(result, DiscountCouponListResponse)
    assert result.current_page == 2
    assert result.total_pages == 5
    item = result.items[0]
    assert item.guide == "Synthetic coupon guide"
    assert item.expiration_date == "20991231"
    assert item.discount_values == (
        "SYNTHETIC-DISCOUNT-TYPE",
        "10",
        "1000",
        "20",
        "2000",
    )
    assert item.remarks == (
        "Synthetic remark one",
        "Synthetic remark two",
        "Synthetic remark three",
    )
    assert item.coupon_no == "SYNTHETIC-COUPON-NUMBER"
    assert item.raw is raw["coupon_infos"]["coupon_info"][0]


def test_pass_and_trip_parsers_expose_immutable_approved_content(
    load_json_fixture,
):
    pass_raw = load_json_fixture("pass_availability_success.json")
    availability = parse_pass_availability_response(pass_raw)
    assert isinstance(availability, PassAvailabilityResponse)
    assert availability.open_dates == ("20990101", "20990102")
    assert availability.ticket_issue_dates == ("20981231",)
    assert availability.offices[0].code == "SYNTHETIC-OFFICE"
    assert availability.offices[0].display_name == "Synthetic Office"
    assert availability.offices[0].raw is pass_raw["wct_info"][0]

    trip_raw = load_json_fixture("trip_menu_success.json")
    trip = parse_trip_menu_response(trip_raw)
    assert isinstance(trip, TripMenuResponse)
    assert trip.popup_message == "Synthetic popup"
    menu = trip.items[0]
    assert menu.title == "Synthetic Menu"
    assert menu.detail == "Synthetic menu detail"
    assert menu.menu_type == "SYNTHETIC-MENU-TYPE"
    assert menu.button == "Synthetic Button"
    assert menu.url.endswith("SYNTHETIC-RAW-SECRET")
    content = menu.contents[0]
    assert content.title == "Synthetic Content"
    assert content.detail == "Synthetic content detail"
    assert content.content_type == "SYNTHETIC-CONTENT-TYPE"
    assert content.active == "Y"
    assert content.agree == "N"
    assert content.info == "Synthetic pass info"
    assert content.image.endswith("SYNTHETIC-RAW-SECRET")
    assert content.url.endswith("SYNTHETIC-RAW-SECRET")
    assert menu.raw is trip_raw["menuList"][0]
    assert content.raw is trip_raw["menuList"][0]["contList"][0]


def test_product_parsers_expose_list_and_detail_fields(load_json_fixture):
    list_raw = load_json_fixture("product_reservations_success.json")
    reservations = parse_product_reservation_list_response(list_raw)
    assert isinstance(reservations, ProductReservationListResponse)
    assert reservations.total_count == 1
    item = reservations.items[0]
    assert item.product_name == "Synthetic Product Reservation"
    assert item.reservation_status == "Synthetic Reserved"
    assert item.payment_deadline == "20991231"
    assert item.payment_status == "SYNTHETIC-PAID"
    assert item.virtual_reservation_no == "SYNTHETIC-RESERVATION-NUMBER"
    assert item.raw is list_raw["mainInfo"]["entity"][0]

    detail_raw = load_json_fixture("product_detail_success.json")
    detail = parse_product_detail_response(detail_raw)
    assert isinstance(detail, ProductDetailResponse)
    assert detail.product_name == "Synthetic Product Detail"
    assert detail.reservation_status == "Synthetic Reserved"
    assert detail.cancellation_deadline == "20991231"
    assert detail.cancellation_amount == "9000"
    assert detail.cancellation_fee == "1000"
    assert detail.received_amount == "10000"
    assert detail.total_amount == "10000"
    assert detail.usage_period == "20990101 through 20991231"
    assert detail.included_item_names == (
        "Synthetic Included Item One",
        "Synthetic Included Item Two",
    )
    assert detail.virtual_reservation_no == "SYNTHETIC-RESERVATION-NUMBER"
    assert detail.detail_raw is detail_raw["mainInfo"]
    assert detail.raw is detail_raw


def test_receipt_parser_exposes_all_approved_travel_payment_and_amount_fields(
    load_json_fixture,
):
    raw = load_json_fixture("ticket_receipt_success.json")
    result = parse_ticket_receipt_response(raw)
    assert isinstance(result, TicketReceiptResponse)
    receipt = result.items[0]
    assert receipt.travel_date == "20990102"
    assert receipt.departure_station == "Synthetic Departure"
    assert receipt.departure_time == "090000"
    assert receipt.arrival_station == "Synthetic Arrival"
    assert receipt.arrival_time == "120000"
    assert receipt.commuter_kind_code == "SYNTHETIC-PASS"
    assert receipt.journey_type_code == "SYNTHETIC-JOURNEY"
    assert receipt.printed_discount_name == "Synthetic Discount"
    assert receipt.print_type == "SYNTHETIC-PRINT"
    assert receipt.seat_class_name == "Synthetic Seat Class"
    assert receipt.ticket_kind_code == "SYNTHETIC-TICKET-KIND"
    assert receipt.ticket_status_code == "SYNTHETIC-TICKET-STATUS"
    assert receipt.train_class_code == "SYNTHETIC-TRAIN-CLASS"
    assert receipt.train_class_name == "Synthetic Train Class"
    assert receipt.train_no == "00999"
    assert receipt.passenger_counts == (1, 2, 0)
    assert receipt.received_amount == 12300
    assert receipt.card_refund_amount == 300
    assert receipt.refund_fee == 100
    assert receipt.refund_received_amount == 200
    assert receipt.point_refund_amount == 50
    assert receipt.member_card_no == "SYNTHETIC-MEMBER-CARD"
    payment = receipt.payments[0]
    assert payment.payment_method == "Synthetic Card"
    assert payment.approval_date == "20990101"
    assert payment.installment_months == 3
    assert payment.amount == 12300
    assert payment.account_no == "SYNTHETIC-ACCOUNT-NUMBER"
    assert payment.approval_no == "SYNTHETIC-APPROVAL-NUMBER"
    assert payment.card_no == "SYNTHETIC-CARD-NUMBER"
    assert payment.point_no == "SYNTHETIC-POINT-NUMBER"
    assert receipt.raw is raw["receipt_infos"]["receipt_info"][0]
    assert payment.raw is receipt.raw["stl_info"][0]


def test_history_parser_flattens_trains_and_preserves_original_raw_nesting(
    load_json_fixture,
):
    raw = load_json_fixture("reservation_history_success.json")
    source = raw["jrny_infos"]["jrny_info"][0]["train_infos"][
        "train_info"
    ][0]
    result = parse_reservation_history_response(raw)
    assert isinstance(result, ReservationHistoryResponse)
    assert result.raw is raw
    train = result.items[0]
    assert result.trains is result.items
    assert train.departure_station == "Synthetic Departure"
    assert train.departure_time == "090000"
    assert train.arrival_station == "Synthetic Arrival"
    assert train.arrival_time == "120000"
    assert train.run_date == "20990102"
    assert train.train_no == "00999"
    assert train.train_class_code == "SYNTHETIC-TRAIN-CLASS"
    assert train.train_class_name == "Synthetic Train Class"
    assert train.reservation_type_code == "SYNTHETIC-RESERVATION-TYPE"
    assert train.acceptance_possible_flag == "Y"
    assert train.payment_flag == "Y"
    assert train.settlement_flag == "Y"
    assert train.seat_count == 2
    assert train.standing_count == 0
    assert train.pnr_no == "SYNTHETIC-PNR-SECRET"
    assert train.raw is source


def test_all_read_models_are_frozen_and_collection_fields_are_tuples(
    load_json_fixture,
):
    cart = parse_cart_list_response(load_json_fixture("cart_list_success.json"))
    trip = parse_trip_menu_response(load_json_fixture("trip_menu_success.json"))
    receipt = parse_ticket_receipt_response(
        load_json_fixture("ticket_receipt_success.json")
    )
    history = parse_reservation_history_response(
        load_json_fixture("reservation_history_success.json")
    )
    for value in (
        cart.items,
        trip.items,
        trip.items[0].contents,
        receipt.items,
        receipt.items[0].payments,
        history.items,
    ):
        assert isinstance(value, tuple)
    with pytest.raises(FrozenInstanceError):
        cart.items[0].product_name = "changed"
    with pytest.raises(FrozenInstanceError):
        trip.popup_message = "changed"


def _contains_value(value, target):
    if isinstance(value, dict):
        return any(_contains_value(item, target) for item in value.values())
    if isinstance(value, list):
        return any(_contains_value(item, target) for item in value)
    return value == target


def test_sensitive_typed_fields_and_raw_values_are_accessible_but_repr_hidden(
    load_json_fixture,
):
    parsed = (
        parse_service_status_response(
            load_json_fixture("service_status_success.json")
        ),
        parse_cart_list_response(load_json_fixture("cart_list_success.json")),
        parse_delay_discount_ticket_response(
            load_json_fixture("delay_discount_tickets_success.json")
        ),
        parse_trip_menu_response(load_json_fixture("trip_menu_success.json")),
        parse_product_reservation_list_response(
            load_json_fixture("product_reservations_success.json")
        ),
        parse_product_detail_response(
            load_json_fixture("product_detail_success.json")
        ),
        parse_ticket_receipt_response(
            load_json_fixture("ticket_receipt_success.json")
        ),
        parse_reservation_history_response(
            load_json_fixture("reservation_history_success.json")
        ),
    )
    combined_raw = [response.raw for response in parsed]
    for sentinel in SECRET_SENTINELS:
        assert any(_contains_value(raw, sentinel) for raw in combined_raw)
        for response in parsed:
            assert sentinel not in repr(response)

    items = (
        parsed[1].items[0],
        parsed[2].items[0],
        parsed[3].items[0],
        parsed[3].items[0].contents[0],
        parsed[4].items[0],
        parsed[6].items[0],
        parsed[6].items[0].payments[0],
        parsed[7].items[0],
    )
    for item in items:
        for sentinel in SECRET_SENTINELS:
            assert sentinel not in repr(item)


@pytest.mark.parametrize(
    ("parser", "payload", "match"),
    [
        (
            parse_cart_list_response,
            {"cart_infos": []},
            "cart_infos",
        ),
        (
            parse_cart_list_response,
            {"cart_infos": {"cart_info": {}}},
            "cart_info",
        ),
        (
            parse_cart_list_response,
            {"cart_infos": {"cart_info": ["not-an-object"]}},
            "cart_info",
        ),
        (
            parse_trip_menu_response,
            {"menuList": [{"contList": {}}]},
            "contList",
        ),
        (
            parse_product_reservation_list_response,
            {"mainInfo": []},
            "mainInfo",
        ),
        (
            parse_ticket_receipt_response,
            {"receipt_infos": {"receipt_info": [{"stl_info": {}}]}},
            "stl_info",
        ),
        (
            parse_reservation_history_response,
            {"jrny_infos": {"jrny_info": [{"train_infos": []}]}},
            "train_infos",
        ),
    ],
)
def test_read_parsers_reject_wrong_wrapper_list_and_item_shapes(
    parser,
    payload,
    match,
):
    raw = {
        "h_msg_cd": "SYNTHETIC-SUCCESS",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
        **payload,
    }
    with pytest.raises(KorailProtocolError, match=match):
        parser(raw)


@pytest.mark.parametrize("value", [True, False, "12.5", "１２", [], {}])
def test_known_numeric_fields_reject_non_ascii_decimal_values(value):
    raw = {
        "h_msg_cd": "SYNTHETIC-SUCCESS",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
        "cart_infos": {"cart_info": [{"h_tk_cnt": value}]},
    }
    with pytest.raises(KorailProtocolError, match="h_tk_cnt"):
        parse_cart_list_response(raw)


@pytest.mark.parametrize("value", [2, "2"])
def test_known_numeric_fields_accept_integers_and_ascii_decimal_strings(value):
    raw = {
        "h_msg_cd": "SYNTHETIC-SUCCESS",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
        "cart_infos": {"cart_info": [{"h_tk_cnt": value}]},
    }
    assert parse_cart_list_response(raw).items[0].ticket_count == 2


@pytest.mark.parametrize(
    ("parser", "collection_name"),
    [
        (parse_cart_list_response, "items"),
        (parse_deposit_bank_response, "items"),
        (parse_delay_discount_ticket_response, "items"),
        (parse_discount_coupon_response, "items"),
        (parse_trip_menu_response, "items"),
        (parse_product_reservation_list_response, "items"),
        (parse_ticket_receipt_response, "items"),
        (parse_reservation_history_response, "items"),
    ],
)
def test_missing_nested_collections_normalize_to_typed_empty_tuples(
    parser,
    collection_name,
):
    raw = {
        "h_msg_cd": "SYNTHETIC-SUCCESS",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
    }
    assert getattr(parser(raw), collection_name) == ()


@pytest.mark.parametrize(
    ("parser", "payload", "collection_name"),
    [
        (parse_cart_list_response, {"cart_infos": None}, "items"),
        (parse_deposit_bank_response, {"dptnBank": None}, "items"),
        (
            parse_delay_discount_ticket_response,
            {"disc_infos": None},
            "items",
        ),
        (
            parse_discount_coupon_response,
            {"coupon_infos": None},
            "items",
        ),
        (parse_trip_menu_response, {"menuList": None}, "items"),
        (
            parse_product_reservation_list_response,
            {"mainInfo": None},
            "items",
        ),
        (
            parse_ticket_receipt_response,
            {"receipt_infos": None},
            "items",
        ),
        (
            parse_reservation_history_response,
            {"jrny_infos": None},
            "items",
        ),
    ],
)
def test_null_nested_collections_normalize_to_typed_empty_tuples(
    parser,
    payload,
    collection_name,
):
    raw = {
        "h_msg_cd": "SYNTHETIC-SUCCESS",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
        **payload,
    }
    assert getattr(parser(raw), collection_name) == ()


def test_coupon_no_data_is_typed_empty():
    result = parse_discount_coupon_response(
        {
            "h_msg_cd": "WRG000000",
            "h_msg_txt": "no data",
            "strResult": "FAIL",
        }
    )
    assert result.items == ()


def test_history_no_data_is_typed_empty():
    result = parse_reservation_history_response(
        {
            "h_msg_cd": "P100",
            "h_msg_txt": "no data",
            "strResult": "FAIL",
        }
    )
    assert result.items == ()


def test_unexpected_application_failures_and_p058_remain_typed_errors():
    from korail_mobile_api.errors import KorailAppError, KorailSessionExpiredError

    for parser in (
        parse_cart_list_response,
        parse_discount_coupon_response,
        parse_reservation_history_response,
    ):
        with pytest.raises(KorailAppError):
            parser(
                {
                    "h_msg_cd": "SYNTHETIC-FAILURE",
                    "h_msg_txt": "synthetic failure",
                    "strResult": "FAIL",
                }
            )
        with pytest.raises(KorailSessionExpiredError):
            parser(
                {
                    "h_msg_cd": "P058",
                    "h_msg_txt": "synthetic expiry",
                    "strResult": "FAIL",
                }
            )


def test_new_read_models_are_package_root_exports():
    for name, model in MODEL_EXPORTS.items():
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is model


def test_every_sensitive_typed_field_is_accessible_but_hidden_from_item_repr(
    load_json_fixture,
):
    cart = parse_cart_list_response(load_json_fixture("cart_list_success.json"))
    delay = parse_delay_discount_ticket_response(
        load_json_fixture("delay_discount_tickets_success.json")
    )
    coupon = parse_discount_coupon_response(
        load_json_fixture("discount_coupons_success.json")
    )
    trip = parse_trip_menu_response(load_json_fixture("trip_menu_success.json"))
    products = parse_product_reservation_list_response(
        load_json_fixture("product_reservations_success.json")
    )
    detail = parse_product_detail_response(
        load_json_fixture("product_detail_success.json")
    )
    receipts = parse_ticket_receipt_response(
        load_json_fixture("ticket_receipt_success.json")
    )
    history = parse_reservation_history_response(
        load_json_fixture("reservation_history_success.json")
    )
    cases = (
        (
            cart.items[0],
            (
                "partner_reservation_no",
                "pnr_no",
                "lump_sum_target_no",
                "customer_no",
                "virtual_reservation_no",
            ),
        ),
        (
            delay.items[0],
            (
                "original_sale_date",
                "window_no",
                "sale_sequence",
                "return_password",
            ),
        ),
        (coupon.items[0], ("coupon_no",)),
        (trip.items[0], ("url",)),
        (trip.items[0].contents[0], ("image", "url")),
        (products.items[0], ("virtual_reservation_no",)),
        (detail, ("virtual_reservation_no",)),
        (receipts.items[0], ("member_card_no",)),
        (
            receipts.items[0].payments[0],
            ("account_no", "approval_no", "card_no", "point_no"),
        ),
        (history.items[0], ("pnr_no",)),
    )
    for model, field_names in cases:
        rendered = repr(model)
        for field_name in field_names:
            value = getattr(model, field_name)
            assert value is not None
            assert value not in rendered
