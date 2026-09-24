"""F1, 291e01c + changes.patch. Run: PYTHONPATH=src pytest tests/test_auth_transport.py.

All HTTP uses MockTransport; socket connections and DNS are disabled. Source
references are relative to analysis/jadx/sources/com/korail/talk unless stated.
Protected literals are not decoded. Cipher vectors pin the Python implementation,
not a claim that the protected Android cipher transformation was recovered.
"""
from __future__ import annotations

import ast
import base64
import json
import socket
import sys
from pathlib import Path
from urllib.parse import parse_qs, parse_qsl

import httpx
import pytest

import korail_mobile_api as package
from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS, KORAIL_COMMON_CODE_BOOTSTRAP_CODES
from korail_mobile_api.crypto import transform_login_password
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api import errors as E
from korail_mobile_api.http import parse_base_response
from korail_mobile_api.models import LoginCryptoInfo
from korail_mobile_api.session import infer_login_input_flag

LOGIN = '/classes/com.korail.mobile.login.Login'
LOGOUT = '/classes/com.korail.mobile.login.Logout'
SERVICE = '/file/CACHE/MobileService.cache'
COMMON = '/classes/com.korail.mobile.common.code.do'
OPTIONAL_COMMON = '/classes/com.korail.mobile.common.getUUID.do'
NON_COMMON = '/classes/com.korail.mobile.common.stationdata'
KEY = '0123456789abcdef'
ID = '0000000000'
PASSWORD = 'synthetic-password'
COOKIE = 'synthetic-session'


def envelope(code='IRZ000001', result='SUCC', **extra):
    return {'strResult': result, 'h_msg_cd': code, 'h_msg_txt': 'synthetic message', **extra}


def bootstrap(**crypto):
    return [envelope(), envelope(**{'app.login.cphd': {'idx': 'synthetic-index', 'key': KEY, 'pwdAESCphd': 'N', **crypto}})]


def login_response(code='IRZ000001', result='SUCC', cookie=True, **extra):
    headers = {'Set-Cookie': f'JSESSIONID={COOKIE}; Path=/; HttpOnly'} if cookie else {}
    return httpx.Response(200, json=envelope(code, result, **extra), headers=headers)


def form(request):
    return parse_qs(request.content.decode('utf-8'), keep_blank_values=True)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*args, **kwargs):
        raise RuntimeError('F1 offline test: network/DNS disabled')
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    monkeypatch.setattr(socket.socket, 'connect_ex', blocked)
    monkeypatch.setattr(socket.socket, 'sendto', blocked)
    monkeypatch.setattr(socket, 'create_connection', blocked)
    monkeypatch.setattr(socket, 'getaddrinfo', blocked)


@pytest.fixture
def factory():
    clients = []
    def make(responses=(), *, config=None):
        requests = []
        replies = iter(responses)
        def handler(request):
            requests.append(request)
            reply = next(replies)  # Unexpected extra requests fail rather than hit a server.
            if isinstance(reply, Exception):
                raise reply
            if callable(reply):
                reply = reply(request)
            if isinstance(reply, httpx.Response):
                return reply
            return httpx.Response(200, content=json.dumps(reply, ensure_ascii=True).encode("ascii"), headers={"Content-Type": "application/json"})
        config = config or KorailConfig(
            base_url='https://offline.invalid', netfunnel_enabled=False,
            dynapath=DynapathConfig(enabled=True, token_provider=lambda context: 'synthetic-token'),
        )
        client = KorailClient(config=config, transport=httpx.MockTransport(handler))
        clients.append(client)
        return client, requests
    yield make
    for client in clients:
        client.close()


def test_socket_guard_is_active():
    with pytest.raises(RuntimeError, match='offline'):
        socket.create_connection(('offline.invalid', 443))
    with pytest.raises(RuntimeError, match='offline'):
        socket.getaddrinfo('offline.invalid', 443)


@pytest.mark.parametrize('code', ['IRZ000001', 'S200'])
@pytest.mark.parametrize('result', ['SUCC', 'FAIL'])
def test_login_success_code_and_session_cookie(factory, code, result):
    """LoginOut.java:1161-1180: code-based override; literal values are library policy, protected in APK."""
    client, requests = factory([*bootstrap(), login_response(code, result, strMbCrdNo='synthetic-card', strCustNo='synthetic-customer')])
    session = client.login(ID, PASSWORD)
    assert session is client.session.current
    assert session.jsessionid == COOKIE
    assert session.member_card_no == 'synthetic-card'
    assert session.customer_no == 'synthetic-customer'
    assert session.raw['strResult'] == result
    assert client.session.pending is None
    assert [r.url.path for r in requests] == [SERVICE, COMMON, LOGIN]
    assert all(r.method == 'POST' for r in requests)
    assert form(requests[-1])['txtInputFlg'] == ['2']
    assert form(requests[-1])['checkValidPw'] == ['Y']
    assert form(requests[-1])['idx'] == ['synthetic-index']
    assert PASSWORD not in requests[-1].content.decode()
    assert 'custId' not in form(requests[-1]) and 'etrPath' not in form(requests[-1])


LOGIN_HASHES = {
    'WRC000116': -699977554, 'WRC000390': -699975390,
    'WRC000420': -699974646, 'WRC000421': -699974645,
    'WRC000450': -699974553, 'WRR000101': -272324263,
    'S034': 2520414, 'S135': 2521376, 'WRT200320': 1559943384,
}


def java_hash(text):
    units = text.encode('utf-16-be')
    value = 0
    for i in range(0, len(units), 2):
        value = (31 * value + int.from_bytes(units[i:i + 2], 'big')) & 0xffffffff
    return value - 2**32 if value >= 2**31 else value


@pytest.mark.parametrize('code, expected', LOGIN_HASHES.items())
def test_login_code_java_hash(code, expected):
    """LoginViewModel.java:1392-1490; smali_classes6/.../LoginViewModel.smali:5809-5819."""
    assert java_hash(code) == expected


@pytest.mark.parametrize('code', [c for c in LOGIN_HASHES if c not in {'WRC000116', 'WRC000420'}] + ['WRC000288', 'SYNTHETIC-UNKNOWN'])
def test_login_refusal_classes_and_cleanup(factory, code):
    """LoginViewModel.java:1425-1490: the other seven switch cases are not web continuation."""
    client, requests = factory([*bootstrap(), login_response(code, 'FAIL')])
    client.http.cookies.set('OLD', 'synthetic-old')
    with pytest.raises(E.KorailAuthError) as caught:
        client.login(ID, PASSWORD)
    assert type(caught.value) is E.KorailAuthError
    assert caught.value.code == code
    assert caught.value.raw['h_msg_cd'] == code
    assert client.session.current is None and client.session.pending is None
    assert not client.http.cookies
    assert 'cookie' not in requests[0].headers


@pytest.mark.parametrize('code', ['WRC000116', 'WRC000420'])
@pytest.mark.parametrize('redirect', ['/synthetic-web', None, 123])
def test_web_pending_preserves_cookie_but_not_logged_in(factory, code, redirect):
    """LoginViewModel.java:1393-1421,1435-1445; library returns raw redirect, does not navigate."""
    client, requests = factory([*bootstrap(), login_response(code, 'FAIL', strRedirectUrl=redirect)])
    with pytest.raises(E.KorailAuthContinuationRequired) as caught:
        client.login(ID, PASSWORD)
    assert client.session.pending is caught.value
    assert caught.value.code == code
    assert caught.value.redirect_url == (redirect if isinstance(redirect, str) else '')
    assert caught.value.raw['strRedirectUrl'] == redirect
    assert client.session.current is None
    assert client.http.cookies.get('JSESSIONID') == COOKIE
    assert len(requests) == 3  # No browser, follow-up, or retry.


def test_pending_relogin_clears_old_cookie(factory):
    client, requests = factory([*bootstrap(), login_response('WRC000116', 'FAIL'), *bootstrap(), login_response()])
    with pytest.raises(E.KorailAuthContinuationRequired):
        client.login(ID, PASSWORD)
    client.login(ID, PASSWORD)
    assert 'cookie' not in requests[3].headers
    assert client.session.pending is None


@pytest.mark.parametrize('code', ['IRZ000001', 'S200'])
def test_success_without_cookie_is_auth_error(factory, code):
    client, _ = factory([*bootstrap(), login_response(code, cookie=False)])
    with pytest.raises(E.KorailAuthError) as caught:
        client.login(ID, PASSWORD)
    assert caught.value.code == code and caught.value.raw['h_msg_cd'] == code
    assert client.session.current is None and not client.http.cookies


@pytest.mark.parametrize('code, exception', [('SEMGTK', E.KorailServiceUnavailableError), ('SUPDATE', E.KorailAppUpdateRequiredError), ('P058', E.KorailSessionExpiredError)])
def test_login_special_errors(factory, code, exception):
    """CommonOut.java:426-452; NetworkService.java:6916-6919. P058 literal: dated 2026-09-24 observation."""
    client, _ = factory([*bootstrap(), login_response(code, 'FAIL')])
    with pytest.raises(exception) as caught:
        client.login(ID, PASSWORD)
    assert caught.value.code == code and caught.value.raw['h_msg_cd'] == code
    assert not client.http.cookies and client.session.current is None


@pytest.mark.parametrize('stage', [0, 1])
def test_preflight_failure_never_sends_login(factory, stage):
    replies = bootstrap()[:stage] + [envelope('SYNTHETIC-FAILURE', 'FAIL')]
    client, requests = factory(replies)
    with pytest.raises(E.KorailAppError):
        client.login(ID, PASSWORD)
    assert len(requests) == stage + 1
    assert not any(r.url.path == LOGIN for r in requests)
    assert not client.http.cookies


@pytest.mark.parametrize('key', ['', 'too-short', '\ud800'])
def test_invalid_crypto_key_never_sends_credentials(factory, key):
    client, requests = factory([*bootstrap(key=key)])
    with pytest.raises(E.KorailProtocolError):
        client.login(ID, PASSWORD)
    assert [r.url.path for r in requests] == [SERVICE, COMMON]


@pytest.mark.parametrize('value', ['Y', 'N', '', 'unexpected', None])
def test_login_does_not_gate_encryption_on_pwd_aes_flag(factory, value):
    """LoginRepositoryImpl.java:922-936,1237-1253 ignores pwdAESCphd for password encryption."""
    client, requests = factory([*bootstrap(pwdAESCphd=value), login_response()])
    client.login(ID, PASSWORD)
    assert form(requests[-1])['txtPwd'][0] != PASSWORD


def test_login_overrides_and_common_code_repeated_fields(factory):
    """LoginIn.java:57-76; CommonCodeIn.java:31-34,55; NetworkService.java:15342-15343."""
    client, requests = factory([*bootstrap(idx=''), login_response()])
    client.login(ID, PASSWORD, input_flag='synthetic-flag', check_valid_pw='N', cust_id='synthetic-cust', etr_path='synthetic-entry')
    sent = form(requests[-1])
    assert sent['txtInputFlg'] == ['synthetic-flag'] and sent['checkValidPw'] == ['N']
    assert sent['custId'] == ['synthetic-cust'] and sent['etrPath'] == ['synthetic-entry']
    assert 'idx' not in sent
    assert form(requests[1])['code'] == list(KORAIL_COMMON_CODE_BOOTSTRAP_CODES)
    assert form(requests[1])['OSVersion'] == ['37']
    assert form(requests[1])['deviceWidth'] == ['1440']
    assert len(form(requests[0])['timeStamp']) == 1


@pytest.mark.parametrize('login_id, flag', [('0000000000', '2'), ('00000000000', '4'), ('synthetic@example.invalid', '5'), ('x', '2')])
def test_input_flag_policy(login_id, flag):
    """LoginViewModel.java:1850-1876. Invalid-ID fallback is library policy, not Android validation."""
    assert infer_login_input_flag(login_id) == flag


@pytest.mark.parametrize('require_result, common_out', [(True, None), (False, True)])
@pytest.mark.parametrize('raise_on_fail', [True, False])
@pytest.mark.parametrize('missing', [False, True])
def test_p058_commonout_even_with_optional_envelope(require_result, common_out, raise_on_fail, missing):
    """CommonOut.java:361,426-438,455-463; NetworkService.java:6916-6919."""
    raw = envelope('P058', 'FAIL')
    if missing:
        raw.pop('strResult')
    with pytest.raises(E.KorailSessionExpiredError) as caught:
        parse_base_response(raw, require_result=require_result, common_out=common_out, raise_on_fail=raise_on_fail)
    assert caught.value.code == 'P058' and caught.value.raw is raw


@pytest.mark.parametrize('path, expected', [(OPTIONAL_COMMON, E.KorailSessionExpiredError), (NON_COMMON, None)])
def test_path_specific_optional_commonout_p058(factory, path, expected):
    client, _ = factory([{'h_msg_cd': 'P058'}])
    if expected:
        with pytest.raises(expected):
            client.http.post_form(path, require_envelope=False)
    else:
        assert client.http.post_form(path, require_envelope=False).h_msg_cd == 'P058'


@pytest.mark.parametrize('code', ['P058', 'WRC000288', 'ERB000001', 'IRR000014', 'IRT800005', 'WRS800036', 'IRZ000001', 'S200', 'IRT000000', 'MRT200105', 'WRR664296'])
def test_success_code_does_not_override_success_envelope(code):
    """CommonOut.java:426-463: failure gating precedes required-login/service classification."""
    raw = envelope(code)
    assert parse_base_response(raw).raw is raw


def test_read_envelope_does_not_fail_success_with_wrc000288():
    """CommonOut.java:426-463: the typed-read envelope follows the same failure gate as transport."""
    from korail_mobile_api.read_parsers import _validate_envelope

    assert _validate_envelope(envelope('WRC000288')) is False
    with pytest.raises(E.KorailApiError):
        _validate_envelope(envelope('WRC000288', result='FAIL'))


@pytest.mark.parametrize('require_result, raises', [(True, True), (False, False)])
def test_missing_result_policy(require_result, raises):
    raw = {'h_msg_cd': 'SYNTHETIC-CODE'}
    if raises:
        with pytest.raises(E.KorailAppError) as caught:
            parse_base_response(raw, require_result=require_result)
        assert caught.value.raw is raw
    else:
        assert parse_base_response(raw, require_result=require_result).raw is raw


@pytest.mark.parametrize('value', [None, '', 'UNKNOWN'])
def test_existing_non_fail_result_policy(value):
    """CommonOut.java:455-463 uses failure equality; protected null/coercion settings are not inferred."""
    assert parse_base_response(envelope(result=value)).str_result == value


@pytest.mark.parametrize('field, attribute', [('h_msg_cd', 'h_msg_cd'), ('h_msg_txt', 'h_msg_txt'), ('strResult', 'str_result')])
@pytest.mark.parametrize('value', [0, 123, -1])
def test_integer_string_fields_preserve_original_raw(field, attribute, value):
    """SESSION_CONTEXT.md §3.6: integer JSON String compatibility (2026-09-21); decoder:468-472."""
    raw = envelope(**({field: value} if field != 'strResult' else {}))
    raw[field] = value
    result = parse_base_response(raw)
    assert getattr(result, attribute) == str(value)
    assert result.raw is raw and type(raw[field]) is int


@pytest.mark.parametrize('value', [True, False, 1.5, {}, []])
@pytest.mark.parametrize('field', ['h_msg_cd', 'h_msg_txt', 'strResult'])
def test_invalid_envelope_types_keep_full_raw(field, value):
    raw = envelope()
    raw[field] = value
    raw['synthetic_nested'] = {'keep': ['whole', 'response']}
    with pytest.raises(E.KorailProtocolError) as caught:
        parse_base_response(raw)
    assert caught.value.raw is raw
    assert caught.value.parser_raw is None


@pytest.mark.parametrize('raw', [None, [], 'synthetic', 123, True])
def test_nonobject_json_keeps_full_raw(raw):
    with pytest.raises(E.KorailProtocolError) as caught:
        parse_base_response(raw)
    assert caught.value.raw is raw


@pytest.mark.parametrize('status', [200, 201, 202, 206, 299])
def test_all_2xx_json_statuses_accepted(factory, status):
    """retrofit2/OkHttpCall.java:184-201 uses 200 <= status < 300."""
    client, _ = factory([httpx.Response(status, json=envelope())])
    assert client.http.post_form(SERVICE).str_result == 'SUCC'


@pytest.mark.parametrize('status', [301, 302, 304, 400, 401, 403, 404, 429, 500, 503])
@pytest.mark.parametrize('json_body', [True, False])
def test_non2xx_before_json_or_app_error(factory, status, json_body):
    """retrofit2/OkHttpCall.java:184-201: non-2xx body is not a success DTO."""
    raw = envelope('P058', 'FAIL')
    response = httpx.Response(status, json=raw) if json_body else httpx.Response(status, content=b'synthetic non-json')
    client, requests = factory([response])
    with pytest.raises(E.KorailTransportError) as caught:
        client.http.post_form(SERVICE)
    assert type(caught.value) is E.KorailTransportError
    assert caught.value.raw == (raw if json_body else b'synthetic non-json')
    assert len(requests) == 1


@pytest.mark.parametrize('status', [200, 204, 205])
@pytest.mark.parametrize('body', [b'', b'<html>synthetic</html>', b'{bad-json'])
def test_2xx_nonjson_preserves_body(factory, status, body):
    client, _ = factory([httpx.Response(status, content=body)])
    with pytest.raises(E.KorailProtocolError) as caught:
        client.http.post_form(SERVICE)
    assert caught.value.raw == body


@pytest.mark.parametrize('code', [-1203, -1406, -2000, -8005, -8201, -8202, -8203])
@pytest.mark.parametrize('status', [200, 503])
def test_dynapath_detection_precedes_status_and_envelope(factory, code, status):
    """DynaPathInterceptor.java:41,97-124. Synthetic field is a library heuristic, not recovered key."""
    raw = {'synthetic_detection_field': code, 'h_msg_cd': 'P058', 'strResult': 'FAIL'}
    client, _ = factory([httpx.Response(status, json=raw)])
    with pytest.raises(E.KorailDynaPathError) as caught:
        client.http.post_form(LOGIN)
    assert caught.value.raw == raw


def test_dynapath_detection_limited_to_fixed_paths(factory):
    raw = envelope(synthetic_value=-1203)
    client, _ = factory([raw])
    assert client.http.post_form(SERVICE).raw == raw


@pytest.mark.parametrize('failure', [httpx.ConnectError('synthetic'), httpx.ReadTimeout('synthetic'), httpx.InvalidURL('synthetic')])
def test_transport_errors_are_wrapped_without_retry(factory, failure):
    client, requests = factory([failure])
    with pytest.raises(E.KorailTransportError) as caught:
        client.http.post_form(SERVICE)
    assert caught.value.__cause__ is failure
    assert len(requests) == 1


def test_common_fields_headers_override_and_empty_omission(factory):
    """CommonIn.java:424-474; NetworkService.java:15342-15343. UA/Connection values are library policy."""
    contexts = []
    def provider(context):
        contexts.append(context)
        return 'synthetic-custom-token'
    config = KorailConfig(base_url='https://offline.invalid', device='synthetic-device', version='synthetic-version', key='synthetic-key', lang='synthetic-lang', user_agent='synthetic-ua', timeout=12.0, netfunnel_enabled=False, dynapath=DynapathConfig(enabled=True, token_provider=provider, header_name='X-Synthetic-Token', device_name='synthetic-model', os_version='synthetic-os'))
    client, requests = factory([envelope(), envelope()], config=config)
    client.http.post_form(LOGIN, {'empty': '', 'zero': 0})
    client.http.post_form(SERVICE)
    first = form(requests[0])
    assert first == {'Device': ['synthetic-device'], 'Version': ['synthetic-version'], 'Key': ['synthetic-key'], 'lang': ['synthetic-lang'], 'zero': ['0']}
    assert requests[0].headers['User-Agent'] == 'synthetic-ua'
    assert requests[0].headers['Connection'] == 'close'
    assert requests[0].headers['Content-Type'] == 'application/x-www-form-urlencoded'
    assert requests[0].headers['X-Synthetic-Token'] == 'synthetic-custom-token'
    assert 'X-Synthetic-Token' not in requests[1].headers
    assert len(contexts) == 1
    assert contexts[0].url == 'https://offline.invalid' + LOGIN
    assert contexts[0].device_name == 'synthetic-model' and contexts[0].os_version == 'synthetic-os'


@pytest.mark.parametrize('path', sorted(DYNAPATH_ALLOWLIST_PATHS))
def test_token_provider_called_only_on_configured_paths(factory, path):
    client, requests = factory([envelope()])
    client.http.post_form(path)
    assert requests[0].headers['x-dynapath-m-token'] == 'synthetic-token'


def test_none_provider_token_is_omitted(factory):
    config = KorailConfig(base_url='https://offline.invalid', netfunnel_enabled=False, dynapath=DynapathConfig(enabled=True, token_provider=lambda context: None))
    client, requests = factory([envelope()], config=config)
    client.http.post_form(LOGIN)
    assert 'x-dynapath-m-token' not in requests[0].headers


def test_provider_failure_never_sends_request(factory):
    def provider(context):
        raise ValueError('synthetic provider error')
    config = KorailConfig(base_url='https://offline.invalid', netfunnel_enabled=False, dynapath=DynapathConfig(enabled=True, token_provider=provider))
    client, requests = factory(config=config)
    with pytest.raises(E.KorailProtocolError) as caught:
        client.http.post_form(LOGIN)
    assert isinstance(caught.value.__cause__, ValueError) and not requests


def test_explicit_disable_and_raw_header_bypass_policy(factory):
    config = KorailConfig(base_url='https://offline.invalid', netfunnel_enabled=False, disable_dynapath=True)
    client, requests = factory([envelope()], config=config)
    with pytest.raises(E.KorailDynaPathRequiredError):
        client.http.post_form(LOGIN)
    assert not requests
    client.http.post_form(SERVICE)
    assert 'x-dynapath-m-token' not in requests[0].headers


def test_default_configuration_and_explicit_overrides():
    # Construction only: no token generation formula is executed or inspected.
    config = KorailConfig()
    assert config.dynapath.enabled and config.dynapath.token_settings is not None
    assert config.device == 'AD' and config.version == '250601003'
    assert config.key == 'korail1234567890' and config.timeout == 60.0
    assert config.lang is None
    assert KorailConfig(disable_dynapath=True).dynapath.enabled is False
    with pytest.raises(ValueError):
        KorailConfig(disable_dynapath=True, dynapath=DynapathConfig(enabled=True, token_provider=lambda context: None))
    with pytest.raises(ValueError):
        DynapathConfig(enabled=True)


@pytest.mark.parametrize('failure, expected', [
    (envelope('SYNTHETIC-FAIL', 'FAIL'), None),
    (envelope('P058', 'FAIL'), E.KorailSessionExpiredError),
    (httpx.Response(503, content=b'synthetic error'), E.KorailTransportError),
    (httpx.Response(200, content=b'synthetic invalid JSON'), E.KorailProtocolError),
    (httpx.ConnectError('synthetic'), E.KorailTransportError),
])
def test_logout_always_clears_local_state(factory, failure, expected):
    """NetworkApi.java:471-472; library finally cleanup, korail-api-status.html:254 (2026-09-24)."""
    client, requests = factory([*bootstrap(), login_response(), failure])
    client.login(ID, PASSWORD)
    if expected:
        with pytest.raises(expected):
            client.logout()
    else:
        client.logout()
    assert client.session.current is None and client.session.pending is None and not client.http.cookies
    assert requests[-1].url.path == LOGOUT
    assert form(requests[-1])['timeStamp'][0].isdigit()
    assert requests[-1].headers['cookie'] == f'JSESSIONID={COOKIE}'
    assert len(requests) == 4


def test_logout_without_current_session_is_local(factory):
    client, requests = factory()
    client.http.cookies.set('JSESSIONID', 'synthetic-orphan')
    client.session.pending = E.KorailAuthContinuationRequired('/synthetic', raw=envelope('WRC000116', 'FAIL'))
    client.logout()
    assert not requests and not client.http.cookies and client.session.pending is None


def test_clear_session_is_local(factory):
    client, requests = factory([*bootstrap(), login_response()])
    client.login(ID, PASSWORD)
    client.session.pending = E.KorailAuthContinuationRequired('/synthetic')
    client.clear_session()
    assert len(requests) == 3
    assert client.session.current is None and client.session.pending is None and not client.http.cookies


def test_close_keeps_session_and_cookies_without_request(factory):
    client, requests = factory([*bootstrap(), login_response()])
    current = client.login(ID, PASSWORD)
    client.close()
    assert len(requests) == 3 and client.session.current is current
    assert client.http.cookies.get('JSESSIONID') == COOKIE


def test_close_finally_closes_netfunnel(monkeypatch):
    client = KorailClient(config=KorailConfig(base_url='https://offline.invalid', disable_dynapath=True), transport=httpx.MockTransport(lambda request: pytest.fail('unexpected HTTP')))
    calls = []
    original_http_close = client.http.close
    original_nf_close = client.netfunnel.close
    def fail_close():
        calls.append('http')
        raise RuntimeError('synthetic close failure')
    monkeypatch.setattr(client.http, 'close', fail_close)
    monkeypatch.setattr(client.netfunnel, 'close', lambda: calls.append('netfunnel'))
    try:
        with pytest.raises(RuntimeError, match='synthetic close'):
            client.close()
        assert calls == ['http', 'netfunnel']
    finally:
        original_http_close()
        original_nf_close()


# Fixed literal table, independent from errors._APP_ERROR_BY_CODE at test runtime.
# This pins current policy; it does not assert each mapping is an Android exception class.
EXPECTED_GROUPS = {
    'KorailNoResultsError': '''WRG000000 P114 P100 WRT300005 ERR000100 WRT800083 WRG500116 IRR800002 IRT200279 IRZ000005 MRT200648 WRC000008 WRC000256 WRD000016 WRS600208 WRS600209 WRS600210 WRT100192 WRT200125 WRT300003 WRT800091''',
    'KorailNoDirectTrainError': 'WRD000061',
    'KorailSoldOutError': '''ERR211161 IRT010110 WRT300001 ERR800048 IRT010510 IRT011010 IRT011210 IRT011310 WRG500113 WRG500114 ERI411321 EAZ000038''',
    'KorailSeatUnavailableError': '''WRI411345 WRT800176 ERR521128 WRS200019 WRS600242 WRS800009 WRS900309''',
    'KorailReservationRefusedError': '''WRR800029 ERR911531 ERR911051 ERR911501 ERR299920 ERR299922 ERR299932 ERR299933 ERR299934 ERR299935 ERR299936 ERR299937 ERR299939 ERR299941 ERR299992 ERR299993 ERR521143 ERR521158 ERR521185 ERR800052 ERR911421 ERR911528 WRR664254 WRR800045 ERR911081 ERR800056 S-ERR911411 S021 WRR664325 WRR700001 WRX000007''',
    'KorailInvalidRequestError': '''ERB000001 WRG200018 WRT100002 WRT100124 WRG200001 WRG200002 WRG200003 WRG200004 WRG200005 WRG200006 WRG200007 WRG200008 WRG200009 WRG200010 WRG200011 WRG200012 WRG200013 WRG200014 WRG200015 WRG200016 WRG200017 WRG200019 WRG200020 ERR800001 ERR800002 ERR800003 ERR800004 ERR800005 ERR800006 ERR800008 ERR800009 ERR800010 ERR800011 ERR800012 ERR800014 ERR800015 ERR800016 ERR800017 ERR800018 ERR800019 ERR800020 ERR800021 ERR800022 ERR800023 ERR800024 ERR800025 ERR800026 ERR800029 ERR800030 ERR800031 ERR800033 ERR800034 ERR800035 ERR800036 ERR800037 ERR800038 ERR930224 ERR930226 ERR930227 ERR930228 ERR930250 ERR930260 ERR930261 ERR930267 ERR930268 ERR930278 ERR930279 ERR930280 ERR930292 ERR930293 ERR930310 ERR930312 ERR930328 ERR930329 WRC000063 WRC000210 WRC000260 WRC000370 WRC000392 WRC000436 WRR664227 WRT400191 WRT400235 WRT400356 WRT800053 WRT800074 WRT800075''',
    'KorailNotEntitledError': '''ERR299943 ERR800049 WRC000419 WRC800030 WRR800058 MRR000008 MRT200005 WRC000107 WRC000302 WRC000373 WRC000412 WRC000446 WRR664211''',
    'KorailServiceUnavailableError': 'SEMGTK',
    'KorailAppUpdateRequiredError': 'SUPDATE',
}
EXPECTED = {code: getattr(E, name) for name, codes in EXPECTED_GROUPS.items() for code in codes.split()}


@pytest.mark.parametrize('code, expected', sorted(EXPECTED.items()))
def test_error_table_each_code_type_message_and_raw(code, expected):
    """ErrorHelper.java:44-114 + asset per-code matrix in REPORT.md; policy, not UI equivalence."""
    raw = envelope(code, 'FAIL', synthetic_nested={'keep': True})
    error = E.classify_app_error(code, 'synthetic message', raw=raw)
    assert type(error) is expected
    assert error.code == code and error.message == 'synthetic message' and error.raw is raw
    with pytest.raises(expected) as caught:
        parse_base_response(raw)
    assert caught.value.raw is raw


def test_error_table_has_no_hidden_extra_or_overlapping_codes():
    assert len(EXPECTED) == 174
    assert len(EXPECTED) == sum(len(codes.split()) for codes in EXPECTED_GROUPS.values())
    assert E._APP_ERROR_BY_CODE == EXPECTED


@pytest.mark.parametrize('code', [None, '', 'SYNTHETIC-UNKNOWN', 'ERR800007', 'ERR800013', 'ERR800028', 'P058'])
def test_unclassified_codes_and_p058_classifier_boundary(code):
    # P058 is deliberately handled by the envelope layer, not this classifier.
    assert type(E.classify_app_error(code, 'synthetic')) is E.KorailAppError


@pytest.mark.parametrize('code', ['ERR911081', 'ERR800056', 'S-ERR911411', 'S021', 'WRR664325', 'WRR700001', 'WRR800029', 'WRX000007'])
def test_reservation_switch_late_and_exist_are_not_sold_out(code):
    """TicketReservationKt.java:87-139; smali:681-684(EXIST),818-821(SOLD_OUT),962-965(LATE)."""
    assert type(E.classify_app_error(code, 'synthetic')) is E.KorailReservationRefusedError


def test_social_record_has_no_inbound_import_or_public_method():
    root = Path(package.__file__).parent
    for path in root.glob('*.py'):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names] + [getattr(node, 'module', '') or '']
                assert all('_social_login_unsupported' not in name for name in names), (path, node.lineno)
    assert 'korail_mobile_api._social_login_unsupported' not in sys.modules
    assert not hasattr(KorailClient, 'login_social')


@pytest.mark.parametrize('key, password, expected', [
    ('0123456789abcdef', '', 'N1VmKzRGUmNQNmZkQncxRXVHNlkyUT09\n'),
    ('0123456789abcdef', 'synthetic-password', 'd2pDQ3FIZ3ZQdXV2d1BxUkE5azRCV1RZSWJFVk5Oc2ZrS0o5K09wOHU0RT0=\n'),
    ('0123456789abcdefghijklmn', '합성 암호', 'S1Zmb1pNbEpDdjVsR3hmMFdxbGY1Zz09\n'),
    ('0123456789abcdefghijklmnopqrstuv', 'x' * 160,
     'NlFpZUZjNzlZdmlrZXFGb25WdzFYLys4LzhEam5oRzNxQ2JFRjI3UnJURy85Y050STVKSFhXRVFS\n'
     'bjlzMEdBSlkwNWpTR0ZpdkkxWnRnQm5pNlk3UG90amJJSWVUNkRYVlIzNFVuNVVkcmZ6d2ppNXoy\n'
     'T1lXbVNYa0tHY3VGS1hVbDlTUzFGQkY3VmRVUFRTYnJ0RjRvc0w0MFZvQ3FRemR5cHNJSVREeWJN\n'
     'M3EzdDc2dGVmNE9vMk5YandiZVFxbHpnajRWWnJFR1RJNHRkTkZZemk4MlYveG0yM0hMYnBydk5o\n'
     'UVVkRm0xND0=\n'),
])
def test_crypto_independent_openssl_vectors(key, password, expected):
    """AESCrypto.java:174-182, LoginRepositoryImpl.java:929-931. Cipher/IV are compatibility vectors only."""
    actual = transform_login_password(password, LoginCryptoInfo(key=key))
    assert actual == expected
    assert actual.endswith('\n') and all(len(line) <= 76 for line in actual.splitlines())
    inner = base64.urlsafe_b64decode(actual).decode('ascii')
    assert '\n' not in inner
    ciphertext = base64.b64decode(inner, validate=True)
    assert len(ciphertext) % 16 == 0


def test_login_wire_encryption_matches_independent_vector(factory):
    client, requests = factory([*bootstrap(), login_response()])
    client.login(ID, PASSWORD)
    assert form(requests[-1])['txtPwd'] == ['d2pDQ3FIZ3ZQdXV2d1BxUkE5azRCV1RZSWJFVk5Oc2ZrS0o5K09wOHU0RT0=\n']
