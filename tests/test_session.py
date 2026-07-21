import pytest
import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthContinuationRequired,
    KorailAuthError,
    KorailProtocolError,
)

SERVICE_CHECK_PATH = "/file/CACHE/MobileService.cache"


def service_check_response() -> httpx.Response:
    return httpx.Response(200, json={"h_msg_cd": "S000", "h_msg_txt": "OK", "strResult": "SUCC"})


def make_success_then_failure_client(load_json_fixture):
    login_attempt = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal login_attempt
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json=load_json_fixture("common_code_login_crypto_n.json"),
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            login_attempt += 1
            if login_attempt == 1:
                return httpx.Response(
                    200,
                    json=load_json_fixture("login_success.json"),
                    headers={
                        "Set-Cookie": "JSESSIONID=first-session; Path=/; HttpOnly"
                    },
                )
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "AUTH_FAIL",
                    "h_msg_txt": "bad credentials",
                    "strResult": "FAIL",
                },
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))


def make_continuation_client():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "API.I00000",
                    "h_msg_txt": "Success",
                    "strResult": "SUCC",
                    "pwdAESCphd": "N",
                },
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "S201",
                    "h_msg_txt": "additional auth",
                    "strResult": "SUCC",
                    "strRedirectUrl": (
                        "/classes/com.korail.mobile.onepass.login.do"
                    ),
                },
                headers={
                    "Set-Cookie": "JSESSIONID=session-cont; Path=/; HttpOnly"
                },
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))


def test_login_posts_transformed_password_and_tracks_cookie(load_json_fixture):
    captured = {"paths": []}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["paths"].append(request.url.path)
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            captured["bootstrap_body"] = request.content.decode()
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=session-123; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    session = client.login("member1", "pw123")

    assert "txtMemberNo=member1" in captured["body"]
    assert "txtPwd=cHcxMjM%3D" in captured["body"]
    assert "txtInputFlg=2" in captured["body"]
    assert "checkValidPw=Y" in captured["body"]
    assert "code=app.var.data" in captured["bootstrap_body"]
    assert "code=app.login.cphd" in captured["bootstrap_body"]
    assert "deviceWidth=" in captured["bootstrap_body"]
    assert "deviceHeight=" in captured["bootstrap_body"]
    assert "OSVersion=" in captured["bootstrap_body"]
    assert captured["paths"] == [
        SERVICE_CHECK_PATH,
        "/classes/com.korail.mobile.common.code.do",
        "/classes/com.korail.mobile.login.Login",
    ]
    assert session.jsessionid == "session-123"
    assert session.member_no == "member1"


def test_login_infers_email_input_flag_and_omits_unset_optional_fields(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=session-email; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    session = client.login("user@example.com", "pw123")

    assert "txtMemberNo=user%40example.com" in captured["body"]
    assert "txtInputFlg=5" in captured["body"]
    assert "checkValidPw=Y" in captured["body"]
    assert "custId=" not in captured["body"]
    assert "etrPath=" not in captured["body"]
    assert session.jsessionid == "session-email"


def test_login_accepts_live_no_aes_bootstrap_without_idx_or_key(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_live_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=session-live-n; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    session = client.login("member1", "pw123")

    assert "txtPwd=cHcxMjM%3D" in captured["body"]
    assert "idx=" not in captured["body"]
    assert session.jsessionid == "session-live-n"


def test_login_reads_crypto_from_app_login_cphd_common_code_key(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "API.I00000",
                    "h_msg_txt": "Success",
                    "strResult": "SUCC",
                    "app.login.cphd": {
                        "idx": "IDX-AES",
                        "key": "1234567890abcdef",
                        "pwdAESCphd": "Y",
                    },
                },
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=session-aes; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    session = client.login("member1", "pw123")

    assert "idx=IDX-AES" in captured["body"]
    assert (
        "txtPwd=ZkpkU2JycXlJSzYyeGNxcSsxdUNmUT09Cg%3D%3D"
        in captured["body"]
    )
    assert session.jsessionid == "session-aes"


def test_login_rejects_non_app_success_code_even_with_jsessionid():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={"h_msg_cd": "API.I00000", "h_msg_txt": "Success", "strResult": "SUCC", "pwdAESCphd": "N"},
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "S003",
                    "h_msg_txt": "서비스에 문제가 발생하였습니다.",
                    "strResult": "SUCC",
                },
                headers={"Set-Cookie": "JSESSIONID=session-not-final; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAuthError, match="S003"):
        client.login("member1", "pw123")


def test_login_redirect_response_raises_continuation_error():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={"h_msg_cd": "API.I00000", "h_msg_txt": "Success", "strResult": "SUCC", "pwdAESCphd": "N"},
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "S201",
                    "h_msg_txt": "additional auth",
                    "strResult": "SUCC",
                    "strRedirectUrl": "/classes/com.korail.mobile.onepass.login.do",
                    "strCustNo": "cust-1",
                },
                headers={"Set-Cookie": "JSESSIONID=session-cont; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAuthContinuationRequired) as exc_info:
        client.login("user@example.com", "pw123")

    exc = exc_info.value
    assert exc.redirect_url == "/classes/com.korail.mobile.onepass.login.do"
    assert exc.post_data.startswith("callLogin=Y&memId=user@example.com&inputFlg=5&")
    assert "h_msg_cd=S201" in exc.post_data
    assert "strCustNo=cust-1" in exc.post_data
    assert "strResult=" not in exc.post_data
    assert "h_msg_txt=" not in exc.post_data


def test_login_success_without_jsessionid_raises_auth_error(load_json_fixture):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(200, json=load_json_fixture("login_success.json"))
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAuthError):
        client.login("member1", "pw123")


def test_login_fail_response_raises_auth_error(load_json_fixture):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={"h_msg_cd": "ERR", "h_msg_txt": "bad credentials", "strResult": "FAIL"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAuthError):
        client.login("member1", "pw123")


def test_login_crypto_bootstrap_app_failure_raises_library_error_without_login_post():
    called_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        called_paths.append(request.url.path)
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={"h_msg_cd": "ERR", "h_msg_txt": "bootstrap failed", "strResult": "FAIL"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAppError):
        client.login("member1", "pw123")

    assert called_paths == [SERVICE_CHECK_PATH, "/classes/com.korail.mobile.common.code.do"]


@pytest.mark.parametrize(
    "payload",
    [
        {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"},
        {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC", "idx": "IDX", "key": "KEY", "pwdAESCphd": ""},
        {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC", "idx": "IDX", "key": "KEY", "pwdAESCphd": "maybe"},
        {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC", "idx": "", "key": "KEY", "pwdAESCphd": "Y"},
        {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC", "idx": "IDX", "key": "", "pwdAESCphd": "Y"},
    ],
)
def test_login_crypto_bootstrap_requires_complete_metadata(payload):
    called_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        called_paths.append(request.url.path)
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=payload)
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.login("member1", "pw123")

    assert called_paths == [SERVICE_CHECK_PATH, "/classes/com.korail.mobile.common.code.do"]


def test_failed_relogin_clears_old_session_and_cookies(load_json_fixture):
    client = make_success_then_failure_client(load_json_fixture)
    client.login("member1", "pw123")
    with pytest.raises(KorailAuthError):
        client.login("member2", "bad")
    assert client.session.current is None
    assert client.session.pending is None
    assert "JSESSIONID" not in client.http.cookies


def test_continuation_keeps_only_pending_state_and_new_cookie():
    client = make_continuation_client()
    with pytest.raises(KorailAuthContinuationRequired) as exc_info:
        client.login("user@example.com", "pw123")
    assert client.session.current is None
    assert client.session.pending is exc_info.value
    assert client.http.cookies.get("JSESSIONID") == "session-cont"
    client.clear_session()
    assert client.session.pending is None
    assert "JSESSIONID" not in client.http.cookies


LOGOUT_PATH = "/classes/com.korail.mobile.login.Logout"


def make_logged_in_client(load_json_fixture, *, logout_response):
    """Client that logs in, then serves ``logout_response`` for the Logout GET.

    ``logout_response`` is a callable ``(request) -> httpx.Response`` so tests can
    inject success, an app-level FAIL, or a transport-level error.
    """
    events: dict[str, object] = {"logout_calls": []}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200, json=load_json_fixture("common_code_login_crypto_n.json")
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=logout-sess; Path=/; HttpOnly"},
            )
        if request.url.path == LOGOUT_PATH:
            events["logout_calls"].append(
                {
                    "method": request.method,
                    "query": request.url.query.decode(),
                    "cookie": request.headers.get("cookie"),
                }
            )
            return logout_response(request)
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    return client, events


def _logout_success(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"},
    )


def test_logout_invalidates_server_session_then_clears_local(load_json_fixture):
    client, events = make_logged_in_client(
        load_json_fixture, logout_response=_logout_success
    )
    client.login("member1", "pw123")
    assert client.session.current is not None
    assert client.http.cookies.get("JSESSIONID") == "logout-sess"

    client.logout()

    # Server-side invalidation was hit exactly once, as a bare GET with no query
    # envelope (authenticated purely by the JSESSIONID cookie, LoginService.java:30).
    assert len(events["logout_calls"]) == 1
    call = events["logout_calls"][0]
    assert call["method"] == "GET"
    assert call["query"] == ""
    assert "JSESSIONID=logout-sess" in (call["cookie"] or "")
    # Local session state is always cleared afterward.
    assert client.session.current is None
    assert client.session.pending is None
    assert "JSESSIONID" not in client.http.cookies


def test_logout_without_session_does_not_call_server(load_json_fixture):
    client, events = make_logged_in_client(
        load_json_fixture, logout_response=_logout_success
    )

    client.logout()

    assert events["logout_calls"] == []
    assert client.session.current is None


def test_logout_is_resilient_to_server_failure(load_json_fixture):
    def _logout_fail(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"h_msg_cd": "ERR", "strResult": "FAIL"})

    client, events = make_logged_in_client(
        load_json_fixture, logout_response=_logout_fail
    )
    client.login("member1", "pw123")

    # A transport/app failure during server-side logout must not raise nor leave
    # the local session behind.
    client.logout()

    assert len(events["logout_calls"]) == 1
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies
