from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import KorailClient
from korail_mobile_api.errors import KorailAppError, KorailProtocolError
from korail_mobile_api.models import BaseKorailResponse
from korail_mobile_api.parsers import (
    parse_app_data_response,
    parse_notice_response,
)
from korail_mobile_api.payloads import build_cache_query


def test_app_data_parser_returns_typed_known_fields_and_preserves_raw(
    load_json_fixture,
):
    raw = load_json_fixture("cache_app_data_success.json")

    result = parse_app_data_response(BaseKorailResponse.from_raw(raw))

    assert result.disability_certification_msg == "synthetic certification guidance"
    assert result.for_seat_intg == "Y"
    assert result.airport_bus_msg == "synthetic airport bus guidance"
    assert result.railplus_cardinfo == "synthetic railplus guidance"
    assert result.version is not None
    assert result.version.message == "synthetic update guidance"
    assert result.version.new_version == "999999999"
    assert result.raw is raw
    assert result.raw["unknownField"] == "preserved"
    assert "unknownField" not in repr(result)


def test_notice_parser_returns_typed_known_fields_and_preserves_raw(
    load_json_fixture,
):
    raw = load_json_fixture("cache_notice_success.json")

    result = parse_notice_response(BaseKorailResponse.from_raw(raw))

    assert result.board_id == "SYNTHETIC"
    assert result.post_sequence == "1"
    assert result.post_title == "Synthetic notice"
    assert result.raw is raw
    assert result.raw["unknownField"] == "preserved"
    assert "unknownField" not in repr(result)


@pytest.mark.parametrize(
    ("parser", "payload", "field"),
    [
        (parse_app_data_response, {"version": []}, "version"),
        (
            parse_app_data_response,
            {"disability_certification_msg": 1},
            "disability_certification_msg",
        ),
        (parse_app_data_response, {"forSeatIntg": 1}, "forSeatIntg"),
        (parse_app_data_response, {"airportBusMsg": []}, "airportBusMsg"),
        (
            parse_app_data_response,
            {"railplus_cardinfo": {}},
            "railplus_cardinfo",
        ),
        (
            parse_app_data_response,
            {"version": {"AMESSAGE": 1}},
            "AMESSAGE",
        ),
        (
            parse_app_data_response,
            {"version": {"NEWDVERSION": []}},
            "NEWDVERSION",
        ),
        (parse_notice_response, {"bbrdId": 1}, "bbrdId"),
        (parse_notice_response, {"ptwtSqno": []}, "ptwtSqno"),
        (parse_notice_response, {"ptwtTtl": {}}, "ptwtTtl"),
    ],
)
def test_cache_parsers_reject_every_malformed_known_field(
    parser,
    payload,
    field,
):
    raw = {
        "h_msg_cd": "S000",
        "h_msg_txt": "",
        "strResult": "SUCC",
        **payload,
    }

    with pytest.raises(KorailProtocolError, match=field):
        parser(BaseKorailResponse.from_raw(raw))


@pytest.mark.parametrize("value", [-1, True, False, 1.5, "1000"])
def test_cache_query_rejects_invalid_timestamp(value):
    with pytest.raises(ValueError, match="timestamp_ms"):
        build_cache_query(value)


def test_cache_query_uses_explicit_timestamp():
    assert build_cache_query(1234567890) == {"timeStamp": "1234567890"}


def test_cache_query_uses_current_epoch_milliseconds(monkeypatch):
    import korail_mobile_api.payloads as payloads

    monkeypatch.setattr(payloads.time, "time", lambda: 1234.567)
    assert payloads.build_cache_query() == {"timeStamp": "1234567"}


@pytest.mark.parametrize(
    ("method_name", "path", "fixture_name"),
    [
        (
            "get_app_data",
            "/file/CACHE/prdMobilePlusMain.cache",
            "cache_app_data_success.json",
        ),
        (
            "get_notice",
            "/file/CACHE/prdMobilePlusNotice.cache",
            "cache_notice_success.json",
        ),
    ],
)
def test_cache_client_methods_use_exact_account_neutral_get(
    method_name,
    path,
    fixture_name,
    load_json_fixture,
):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=load_json_fixture(fixture_name))

    client = KorailClient(transport=httpx.MockTransport(handler))
    assert client.session.current is None
    try:
        result = getattr(client, method_name)(1234567890)
    finally:
        client.close()

    assert client.session.current is None
    assert len(seen) == 1
    assert seen[0].method == "GET"
    assert seen[0].url.path == path
    assert parse_qs(seen[0].url.query.decode()) == {
        "timeStamp": ["1234567890"]
    }
    assert set(seen[0].url.params) == {"timeStamp"}
    assert seen[0].content == b""
    assert "x-dynapath-m-token" not in seen[0].headers
    assert result.h_msg_cd == "S000"


@pytest.mark.parametrize("method_name", ["get_app_data", "get_notice"])
@pytest.mark.parametrize("timestamp_ms", [-1, True, 1.5, "1000"])
def test_cache_client_rejects_invalid_timestamp_before_io(
    method_name,
    timestamp_ms,
):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="timestamp_ms"):
            getattr(client, method_name)(timestamp_ms)
    finally:
        client.close()
    assert called is False


@pytest.mark.parametrize("method_name", ["get_app_data", "get_notice"])
@pytest.mark.parametrize(
    ("response_kind", "error_type"),
    [
        ("malformed-json", KorailProtocolError),
        ("application-failure", KorailAppError),
    ],
)
def test_cache_client_preserves_strict_response_classification(
    method_name,
    response_kind,
    error_type,
):
    def handler(_: httpx.Request) -> httpx.Response:
        if response_kind == "malformed-json":
            return httpx.Response(200, text="not json")
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "E001",
                "h_msg_txt": "failed",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(error_type):
            getattr(client, method_name)(1)
    finally:
        client.close()


@pytest.mark.parametrize(
    ("method_name", "payload"),
    [
        ("get_app_data", {"forSeatIntg": "Y"}),
        ("get_notice", {"bbrdId": "SYNTHETIC"}),
    ],
)
def test_cache_client_accepts_envelope_free_objects(method_name, payload):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        result = getattr(client, method_name)(1)
    finally:
        client.close()

    assert result.h_msg_cd is None
    assert result.raw == payload
