import pytest
import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import KorailAppError, KorailAuthError, KorailProtocolError


def test_login_posts_transformed_password_and_tracks_cookie(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
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
    assert session.jsessionid == "session-123"
    assert session.member_no == "member1"


def test_login_accepts_live_no_aes_bootstrap_without_idx_or_key(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
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
    assert "idx=" in captured["body"]
    assert session.jsessionid == "session-live-n"


def test_login_success_without_jsessionid_raises_auth_error(load_json_fixture):
    def handler(request: httpx.Request) -> httpx.Response:
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
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={"h_msg_cd": "ERR", "h_msg_txt": "bootstrap failed", "strResult": "FAIL"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAppError):
        client.login("member1", "pw123")

    assert called_paths == ["/classes/com.korail.mobile.common.code.do"]


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
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=payload)
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.login("member1", "pw123")

    assert called_paths == ["/classes/com.korail.mobile.common.code.do"]
