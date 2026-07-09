import httpx
import pytest

from korail_mobile_api import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_API_VERSION,
    KORAIL_APP_KEY,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEVICE_ANDROID,
    KorailConfig,
)
from korail_mobile_api.dynapath import DynapathConfig
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


def test_korail_runtime_constants_are_importable():
    assert KORAIL_DEVICE_ANDROID == "AD"
    assert KORAIL_API_VERSION == "250601003"
    assert KORAIL_APP_KEY == "korail1234567890"
    assert KORAIL_DEFAULT_DEVICE_NAME
    assert DYNAPATH_HEADER_NAME == "x-dynapath-m-token"
    assert "/classes/com.korail.mobile.login.Login" in DYNAPATH_ALLOWLIST_PATHS


def test_post_form_adds_dynapath_header_for_allowlisted_path():
    captured = {}
    contexts = []

    def token_provider(context):
        contexts.append(context)
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    response = client.post_form("/classes/com.korail.mobile.login.Login")

    assert response.str_result == "SUCC"
    assert captured["token"] == "dynapath-token"
    assert len(contexts) == 1
    assert contexts[0].method == "POST"
    assert contexts[0].path == "/classes/com.korail.mobile.login.Login"
    assert contexts[0].device == KORAIL_DEVICE_ANDROID
    assert contexts[0].device_name == KORAIL_DEFAULT_DEVICE_NAME


def test_dynapath_provider_is_not_called_for_non_allowlisted_path():
    called = False

    def token_provider(_context):
        nonlocal called
        called = True
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get(DYNAPATH_HEADER_NAME) is None
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form("/classes/com.korail.mobile.common.code.do")

    assert called is False


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


def test_get_json_can_return_raw_object_without_korail_envelope():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": "281", "map_version": "260608002"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json("/classes/example.json", require_envelope=False)

    assert response.h_msg_cd is None
    assert response.raw["map_version"] == "260608002"


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
