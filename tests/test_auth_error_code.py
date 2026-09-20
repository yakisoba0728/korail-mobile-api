# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""``KorailAuthError.code`` 는 로그인 요청이 받은 서버 ``h_msg_cd`` 를 들고 있다.

README 는 진짜 ``SUPDATE`` 를 ``error.code`` 로 가르라고 안내한다. 로그인은 서버
실패를 ``KorailAuthError`` 로 감싸므로, 그 예외에 ``code`` 가 없으면 안내대로 한
호출자가 ``AttributeError`` 를 받는다.
"""

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppUpdateRequiredError,
    KorailAuthError,
    KorailSessionExpiredError,
)


SERVICE_CHECK_PATH = "/file/CACHE/MobileService.cache"
COMMON_CODE_PATH = "/classes/com.korail.mobile.common.code.do"
LOGIN_PATH = "/classes/com.korail.mobile.login.Login"


def _client_whose_login_answers(
    login_body: dict[str, str], load_json_fixture
) -> KorailClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return httpx.Response(
                200, json={"h_msg_cd": "S000", "h_msg_txt": "OK", "strResult": "SUCC"}
            )
        if request.url.path == COMMON_CODE_PATH:
            return httpx.Response(
                200, json=load_json_fixture("common_code_login_crypto_n.json")
            )
        if request.url.path == LOGIN_PATH:
            return httpx.Response(200, json=login_body)
        raise AssertionError(f"unexpected path {request.url.path}")

    return KorailClient(
        KorailConfig(enable_dynapath=True),
        transport=httpx.MockTransport(handler),
    )


def test_a_refused_login_keeps_the_server_code_and_the_cause(load_json_fixture):
    client = _client_whose_login_answers(
        {"strResult": "FAIL", "h_msg_cd": "SUPDATE", "h_msg_txt": "업데이트"},
        load_json_fixture,
    )
    with pytest.raises(KorailAuthError) as excinfo:
        client.login("member1", "pw123")
    assert excinfo.value.code == "SUPDATE"
    assert isinstance(excinfo.value.__cause__, KorailAppUpdateRequiredError)


def test_an_unfinished_login_keeps_the_server_code(load_json_fixture):
    client = _client_whose_login_answers(
        {"strResult": "SUCC", "h_msg_cd": "WRZ000999", "h_msg_txt": "미완료"},
        load_json_fixture,
    )
    with pytest.raises(KorailAuthError) as excinfo:
        client.login("member1", "pw123")
    assert excinfo.value.code == "WRZ000999"
    assert excinfo.value.__cause__ is None


def test_session_expiry_keeps_its_own_code():
    error = KorailSessionExpiredError("P058", "세션 만료")
    assert isinstance(error, KorailAuthError)
    assert error.code == "P058"


def test_an_auth_failure_without_a_server_answer_has_no_code():
    assert KorailAuthError("KORAIL reservation requires an authenticated session").code is None
