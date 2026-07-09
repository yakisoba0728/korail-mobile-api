import httpx

from korail_mobile_api import KorailClient, KorailConfig


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
