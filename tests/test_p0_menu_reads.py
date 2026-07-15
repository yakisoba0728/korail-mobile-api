from __future__ import annotations

import copy
import inspect
from dataclasses import FrozenInstanceError
from typing import get_type_hints
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api
import korail_mobile_api.read_payloads as read_payloads
import korail_mobile_api.read_models as read_models
import korail_mobile_api.read_parsers as read_parsers
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
)


PASS_MENU_PATH = "/classes/com.korail.mobile.pass.passMenu.do"
CREW_REQUEST_LIST_PATH = "/classes/com.korail.mobile.push.crwCallRq.do"
COMMUTER_KIND_MENU_PATH = "/classes/com.korail.mobile.push.cmtrKnd.do"
CALL_CREW_MUTATION_PATH = "/classes/com.korail.mobile.push.callCrew.do"


def test_p0_menu_routes_have_exact_read_only_contracts():
    assert {
        ("POST", PASS_MENU_PATH),
        ("GET", CREW_REQUEST_LIST_PATH),
        ("GET", COMMUTER_KIND_MENU_PATH),
    } <= KORAIL_READ_ONLY_ROUTES
    assert KORAIL_EXACT_REQUEST_FIELDS[PASS_MENU_PATH] == {
        "Device",
        "Version",
        "Key",
        "menuNo",
    }
    assert KORAIL_EXACT_REQUEST_FIELDS[CREW_REQUEST_LIST_PATH] == {
        "Device",
        "Version",
        "Key",
        "qryDvCd",
    }
    assert KORAIL_EXACT_REQUEST_FIELDS[COMMUTER_KIND_MENU_PATH] == {
        "Device",
        "Version",
        "Key",
        "cmtrKndCd",
    }


def test_state_changing_crew_call_route_stays_outside_transport_boundary():
    assert ("GET", CALL_CREW_MUTATION_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert CALL_CREW_MUTATION_PATH not in KORAIL_EXACT_REQUEST_FIELDS


def test_p0_menu_payload_builders_forward_only_caller_supplied_codes():
    cases = (
        (
            read_payloads.build_pass_menu_form,
            "menu_no",
            "CALLER-MENU",
            {"menuNo": "CALLER-MENU"},
        ),
        (
            read_payloads.build_crew_request_list_query,
            "query_division_code",
            "CALLER-QUERY-DIVISION",
            {"qryDvCd": "CALLER-QUERY-DIVISION"},
        ),
        (
            read_payloads.build_commuter_kind_menu_query,
            "commuter_kind_code",
            "CALLER-COMMUTER-KIND",
            {"cmtrKndCd": "CALLER-COMMUTER-KIND"},
        ),
    )
    for builder, parameter_name, caller_value, expected in cases:
        assert list(inspect.signature(builder).parameters) == [parameter_name]
        assert (
            inspect.signature(builder).parameters[parameter_name].default
            is inspect.Parameter.empty
        )
        assert builder(caller_value) == expected


@pytest.mark.parametrize(
    "builder_name",
    (
        "build_pass_menu_form",
        "build_crew_request_list_query",
        "build_commuter_kind_menu_query",
    ),
)
@pytest.mark.parametrize("invalid", ("", "   ", None, 7))
def test_p0_menu_payload_builders_reject_invalid_codes(builder_name, invalid):
    builder = getattr(read_payloads, builder_name)
    with pytest.raises(ValueError):
        builder(invalid)


def test_pass_menu_parser_exposes_typed_immutable_static_contract(
    load_json_fixture,
):
    raw = load_json_fixture("pass_menu_success.json")
    result = read_parsers.parse_pass_menu_response(raw)

    assert isinstance(result, read_models.PassMenuResponse)
    assert result.raw is raw
    assert isinstance(result.items, tuple)
    assert len(result.items) == 1
    item = result.items[0]
    assert isinstance(item, read_models.PassMenuItem)
    assert item.after_day == 5
    assert item.agreement == "Synthetic agreement"
    assert item.detail_type == "SYNTHETIC-DETAIL-TYPE"
    assert item.detail_description == "Synthetic detail description"
    assert item.enabled == "Y"
    assert item.item_id == "SYNTHETIC-MENU-ID"
    assert item.information == "Synthetic pass information"
    assert item.expanded == "N"
    assert item.parent_id == "SYNTHETIC-PARENT-ID"
    assert item.representative_arrival == "Synthetic Arrival"
    assert item.representative_departure == "Synthetic Departure"
    assert item.title == "Synthetic Pass Menu"
    assert item.train_group_code == "SYNTHETIC-TRAIN-GROUP"
    assert item.item_type == "SYNTHETIC-MENU-TYPE"
    assert item.url.endswith("SYNTHETIC-RAW-SECRET")
    assert item.raw is raw["list"][0]

    pass_data = item.pass_data
    assert isinstance(pass_data, read_models.PassMenuData)
    assert pass_data.commuter_kind_code == "SYNTHETIC-SERVER-KIND"
    assert pass_data.station_selection == "Y"
    assert isinstance(pass_data.age_options, tuple)
    assert isinstance(pass_data.period_options, tuple)
    age = pass_data.age_options[0]
    assert isinstance(age, read_models.PassAgeOption)
    assert age.commuter_age_code == "SYNTHETIC-SERVER-AGE"
    assert age.display_name == "Synthetic Adult"
    assert age.minimum_age == "18"
    assert age.maximum_age == "64"
    period = pass_data.period_options[0]
    assert isinstance(period, read_models.PassPeriodOption)
    assert period.commuter_period_code == "SYNTHETIC-SERVER-PERIOD"
    assert period.display_name == "Synthetic Period"

    with pytest.raises(FrozenInstanceError):
        item.title = "changed"


def test_commuter_kind_menu_parser_reuses_server_supplied_pass_options(
    load_json_fixture,
):
    raw = load_json_fixture("commuter_kind_menu_success.json")
    result = read_parsers.parse_commuter_kind_menu_response(raw)

    assert isinstance(result, read_models.CommuterKindMenuResponse)
    assert result.raw is raw
    assert result.after_day == "7"
    assert result.agreement == "Synthetic commuter agreement"
    assert result.information == "Synthetic commuter information"
    assert result.title == "Synthetic Commuter Menu"
    assert result.pass_data is not None
    assert (
        result.pass_data.commuter_kind_code
        == "SYNTHETIC-SERVER-COMMUTER-KIND"
    )
    assert (
        result.pass_data.age_options[0].commuter_age_code
        == "SYNTHETIC-SERVER-COMMUTER-AGE"
    )
    assert (
        result.pass_data.period_options[0].commuter_period_code
        == "SYNTHETIC-SERVER-COMMUTER-PERIOD"
    )


def test_crew_request_list_parser_exposes_options_without_calling_crew(
    load_json_fixture,
):
    raw = load_json_fixture("crew_request_list_success.json")
    result = read_parsers.parse_crew_request_list_response(raw)

    assert isinstance(result, read_models.CrewRequestListResponse)
    assert result.raw is raw
    assert isinstance(result.items, tuple)
    assert result.items == (
        read_models.CrewRequestOption(
            message_code="SYNTHETIC-SERVER-CREW-CODE",
            content="Synthetic crew request option",
            raw=raw["prsList"][0],
        ),
    )
    assert result.items[0].raw is raw["prsList"][0]


@pytest.mark.parametrize(
    ("fixture_name", "parser_name", "mutation"),
    (
        (
            "pass_menu_success.json",
            "parse_pass_menu_response",
            lambda raw: raw.__setitem__("list", {}),
        ),
        (
            "pass_menu_success.json",
            "parse_pass_menu_response",
            lambda raw: raw["list"].__setitem__(0, "not-an-object"),
        ),
        (
            "pass_menu_success.json",
            "parse_pass_menu_response",
            lambda raw: raw["list"][0].__setitem__("passData", []),
        ),
        (
            "pass_menu_success.json",
            "parse_pass_menu_response",
            lambda raw: raw["list"][0]["passData"].__setitem__(
                "pass_ageinfo", ["not-an-object"]
            ),
        ),
        (
            "commuter_kind_menu_success.json",
            "parse_commuter_kind_menu_response",
            lambda raw: raw.__setitem__("afterDay", 7),
        ),
        (
            "crew_request_list_success.json",
            "parse_crew_request_list_response",
            lambda raw: raw.__setitem__("prsList", {}),
        ),
        (
            "crew_request_list_success.json",
            "parse_crew_request_list_response",
            lambda raw: raw["prsList"].__setitem__(0, "not-an-object"),
        ),
    ),
)
def test_p0_menu_parsers_reject_malformed_static_shapes(
    fixture_name,
    parser_name,
    mutation,
    load_json_fixture,
):
    raw = copy.deepcopy(load_json_fixture(fixture_name))
    mutation(raw)
    parser = getattr(read_parsers, parser_name)
    with pytest.raises(KorailProtocolError):
        parser(raw)


@pytest.mark.parametrize(
    "parser_name",
    (
        "parse_pass_menu_response",
        "parse_commuter_kind_menu_response",
        "parse_crew_request_list_response",
    ),
)
def test_p0_menu_parsers_preserve_application_and_session_errors(parser_name):
    parser = getattr(read_parsers, parser_name)
    with pytest.raises(KorailAppError):
        parser(
            {
                "h_msg_cd": "SYNTHETIC-ERROR",
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
    with pytest.raises(KorailProtocolError):
        parser({"h_msg_cd": "SYNTHETIC-INCOMPLETE"})


@pytest.mark.parametrize(
    ("fixture_name", "parser_name"),
    (
        ("pass_menu_success.json", "parse_pass_menu_response"),
        (
            "commuter_kind_menu_success.json",
            "parse_commuter_kind_menu_response",
        ),
        (
            "crew_request_list_success.json",
            "parse_crew_request_list_response",
        ),
    ),
)
def test_p0_menu_model_reprs_hide_raw_and_inert_url_values(
    fixture_name,
    parser_name,
    load_json_fixture,
):
    result = getattr(read_parsers, parser_name)(
        load_json_fixture(fixture_name)
    )
    assert "SYNTHETIC-RAW-SECRET" not in repr(result)


CLIENT_CASES = (
    (
        "get_pass_menu",
        "CALLER-MENU",
        "POST",
        PASS_MENU_PATH,
        "menuNo",
        read_models.PassMenuResponse,
    ),
    (
        "get_crew_request_list",
        "CALLER-QUERY-DIVISION",
        "GET",
        CREW_REQUEST_LIST_PATH,
        "qryDvCd",
        read_models.CrewRequestListResponse,
    ),
    (
        "get_commuter_kind_menu",
        "CALLER-COMMUTER-KIND",
        "GET",
        COMMUTER_KIND_MENU_PATH,
        "cmtrKndCd",
        read_models.CommuterKindMenuResponse,
    ),
)
CLIENT_CODE_CASES = tuple((name, code) for name, code, *_ in CLIENT_CASES)


@pytest.mark.parametrize(
    (
        "method_name",
        "caller_code",
        "http_method",
        "path",
        "wire_name",
        "response_type",
    ),
    CLIENT_CASES,
)
def test_p0_menu_client_issues_one_exact_account_neutral_read(
    method_name,
    caller_code,
    http_method,
    path,
    wire_name,
    response_type,
):
    requests = []
    token_contexts = []

    def token_provider(context):
        token_contexts.append(context)
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
    assert client.session.current is None
    try:
        result = getattr(client, method_name)(caller_code)
    finally:
        client.close()

    assert isinstance(result, response_type)
    assert len(requests) == 1
    request = requests[0]
    assert request.method == http_method
    assert request.url.path == path
    assert request.url.host == "smart.letskorail.com"
    expected = {
        "Device": [config.device],
        "Version": [config.version],
        "Key": [config.key],
        wire_name: [caller_code],
    }
    if http_method == "GET":
        assert parse_qs(
            request.url.query.decode(),
            keep_blank_values=True,
        ) == expected
        assert request.content == b""
    else:
        assert request.url.query == b""
        assert parse_qs(
            request.content.decode(),
            keep_blank_values=True,
        ) == expected
    assert "x-dynapath-m-token" not in request.headers
    assert token_contexts == []


@pytest.mark.parametrize(
    ("method_name", "caller_code"),
    CLIENT_CODE_CASES,
)
def test_p0_menu_client_validates_before_transport(method_name, caller_code):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError):
            getattr(client, method_name)("   ")
    finally:
        client.close()
    assert calls == 0


@pytest.mark.parametrize(
    ("method_name", "caller_code"),
    CLIENT_CODE_CASES,
)
def test_p0_menu_client_clears_stale_session_on_p058(
    method_name,
    caller_code,
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
            getattr(client, method_name)(caller_code)
    finally:
        client.close()
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies


@pytest.mark.parametrize(
    ("method_name", "caller_code"),
    CLIENT_CODE_CASES,
)
def test_p0_menu_client_preserves_application_failures(
    method_name,
    caller_code,
):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC-ERROR",
                "h_msg_txt": "synthetic failure",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAppError):
            getattr(client, method_name)(caller_code)
    finally:
        client.close()


def test_p0_menu_public_methods_require_runtime_codes_and_are_typed():
    expected = {
        "get_pass_menu": ("menu_no", read_models.PassMenuResponse),
        "get_crew_request_list": (
            "query_division_code",
            read_models.CrewRequestListResponse,
        ),
        "get_commuter_kind_menu": (
            "commuter_kind_code",
            read_models.CommuterKindMenuResponse,
        ),
    }
    for method_name, (parameter_name, response_type) in expected.items():
        method = getattr(KorailClient, method_name)
        signature = inspect.signature(method)
        assert list(signature.parameters) == ["self", parameter_name]
        assert (
            signature.parameters[parameter_name].default
            is inspect.Parameter.empty
        )
        hints = get_type_hints(method)
        assert hints[parameter_name] is str
        assert hints["return"] is response_type


def test_p0_menu_models_are_exported_from_package_root():
    names = (
        "PassAgeOption",
        "PassPeriodOption",
        "PassMenuData",
        "PassMenuItem",
        "PassMenuResponse",
        "CommuterKindMenuResponse",
        "CrewRequestOption",
        "CrewRequestListResponse",
    )
    for name in names:
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is getattr(read_models, name)


def test_client_exposes_no_crew_call_mutation_method():
    assert not hasattr(KorailClient, "call_crew")
    assert not hasattr(KorailClient, "request_crew_call")
