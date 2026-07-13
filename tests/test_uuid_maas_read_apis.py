import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.models import BaseKorailResponse
from korail_mobile_api.parsers import (
    parse_station_data_response,
    parse_uuid_response,
)
from korail_mobile_api.payloads import build_maas_station_form


def test_uuid_parser_returns_repr_safe_typed_code(load_json_fixture):
    raw = load_json_fixture("uuid_success.json")
    result = parse_uuid_response(BaseKorailResponse.from_raw(raw))
    assert result.verification_code == "fixture-verification-code"
    assert result.h_msg_cd == "API.I00000"
    assert result.raw is raw
    assert "fixture-verification-code" not in repr(result)


def test_station_parser_returns_typed_rows_from_envelope_free_payload(load_json_fixture):
    raw = load_json_fixture("maas_station_data.json")
    result = parse_station_data_response(BaseKorailResponse(raw=raw))
    assert [(item.code, item.name) for item in result.stations] == [
        ("0001", "서울"),
        ("0020", "부산"),
    ]
    assert result.stations[0].longitude == "126.9708"
    assert result.raw is raw


def test_station_parser_preserves_a_present_common_envelope(load_json_fixture):
    raw = load_json_fixture("maas_station_data.json")
    raw.update(
        {
            "h_msg_cd": "API.I00000",
            "h_msg_txt": "Success",
            "strResult": "SUCC",
        }
    )
    result = parse_station_data_response(BaseKorailResponse.from_raw(raw))
    assert result.h_msg_cd == "API.I00000"
    assert len(result.stations) == 2


@pytest.mark.parametrize("value", [None, "", "   ", 101, False])
def test_maas_station_form_rejects_missing_or_nonstring_code(value):
    with pytest.raises(ValueError, match="additional_service_code"):
        build_maas_station_form(value)


def test_maas_station_form_preserves_exact_nonempty_code():
    assert build_maas_station_form(" M10 ") == {"addSrvDvCd": " M10 "}


@pytest.mark.parametrize(
    "raw",
    [
        {"stns": None},
        {"stns": {}},
        {"stns": {"stn": "not-a-list"}},
        {"stns": {"stn": ["not-an-object"]}},
        {"stns": {"stn": [{"stn_cd": "", "stn_nm": "서울"}]}},
        {"stns": {"stn": [{"stn_cd": "0001", "stn_nm": None}]}},
        {"stns": {"stn": [{"stn_cd": "0001", "stn_nm": "서울", "latitude": 37.5}]}},
    ],
)
def test_station_parser_rejects_malformed_known_structure(raw):
    with pytest.raises(KorailProtocolError):
        parse_station_data_response(BaseKorailResponse(raw=raw))


@pytest.mark.parametrize("value", [None, "", "   ", 123, [], {}])
def test_uuid_parser_rejects_missing_or_malformed_code(value):
    raw = {
        "h_msg_cd": "API.I00000",
        "h_msg_txt": "Success",
        "strResult": "SUCC",
        "mutMrkVrfCd": value,
    }
    with pytest.raises(KorailProtocolError, match="mutMrkVrfCd"):
        parse_uuid_response(BaseKorailResponse.from_raw(raw))


def test_client_sends_exact_uuid_and_maas_requests(load_json_fixture):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/ebizcross/getUUID.do":
            return httpx.Response(
                200,
                json=load_json_fixture("uuid_success.json"),
            )
        if request.url.path == "/ebizmaas/EbizMaasStationList.do":
            return httpx.Response(
                200,
                json=load_json_fixture("maas_station_data.json"),
            )
        raise AssertionError(request.url.path)

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    try:
        uuid = client.get_uuid()
        stations = client.get_maas_station_data("M10")
    finally:
        client.close()
    assert uuid.verification_code == "fixture-verification-code"
    assert len(stations.stations) == 2
    assert captured[0].method == "GET"
    assert captured[0].url.scheme == "https"
    assert captured[0].url.host == "smart.letskorail.com"
    assert captured[0].url.path == "/ebizcross/getUUID.do"
    assert captured[0].url.query == b""
    assert captured[1].method == "POST"
    assert captured[1].url.scheme == "https"
    assert captured[1].url.host == "smart.letskorail.com"
    assert captured[1].url.path == "/ebizmaas/EbizMaasStationList.do"
    assert captured[1].url.query == b""
    assert captured[1].content == b"addSrvDvCd=M10"


@pytest.mark.parametrize("value", [None, "", "   ", 10, False])
def test_client_rejects_invalid_maas_code_before_io(value):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="additional_service_code"):
            client.get_maas_station_data(value)
    finally:
        client.close()
    assert called is False
