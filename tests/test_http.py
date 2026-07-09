import httpx
import pytest

from korail_mobile_api import KorailConfig
from korail_mobile_api.errors import KorailAppError, KorailProtocolError
from korail_mobile_api.http import KorailHttpClient, parse_base_response
from korail_mobile_api.safety import EXCLUDED_API_DOMAINS
from conftest import load_json_fixture


def test_post_form_adds_common_fields_and_form_encoding():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers["content-type"]
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.post_form("/classes/example.do", {"custom": "value"})

    assert captured["url"] == "https://smart.letskorail.com/classes/example.do"
    assert captured["content_type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    assert "Device=AD" in captured["body"]
    assert "Version=250601003" in captured["body"]
    assert "Key=korail1234567890" in captured["body"]
    assert "custom=value" in captured["body"]
    assert response.h_msg_cd == "IRG000000"


def test_get_json_returns_parsed_response():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["query"] = request.url.query.decode()
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json("/classes/example.json", {"custom": "value"})

    assert captured["url"] == "https://smart.letskorail.com/classes/example.json?custom=value"
    assert captured["query"] == "custom=value"
    assert response.str_result == "SUCC"


def test_parse_base_response_raises_app_error_for_fail():
    try:
        parse_base_response({"h_msg_cd": "WRG000000", "h_msg_txt": "조회 결과 없음", "strResult": "FAIL"})
    except KorailAppError as exc:
        assert exc.code == "WRG000000"
        assert "조회 결과 없음" in str(exc)
    else:
        raise AssertionError("KorailAppError was not raised")


def test_parse_base_response_requires_dict():
    try:
        parse_base_response(["not", "a", "dict"])
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


def test_parse_base_response_requires_korail_envelope_fields():
    try:
        parse_base_response(load_json_fixture("dynapath_403.json"))
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


def test_post_form_raises_protocol_error_for_non_json_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    try:
        client.post_form("/classes/example.do")
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


def test_get_json_raises_protocol_error_for_non_json_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    try:
        client.get_json("/classes/example.json")
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


@pytest.mark.parametrize("blocked_domain", sorted(EXCLUDED_API_DOMAINS))
def test_http_client_blocks_excluded_domains_before_post(blocked_domain: str):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.post_form(f"/classes/com.korail.mobile.{blocked_domain}.Example")

    assert called is False


@pytest.mark.parametrize("blocked_domain", sorted(EXCLUDED_API_DOMAINS))
def test_http_client_blocks_excluded_domains_before_get(blocked_domain: str):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.get_json(f"/classes/com.korail.mobile.{blocked_domain}.Example")

    assert called is False
