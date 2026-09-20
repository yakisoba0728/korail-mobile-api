# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""``strResult`` 가 빠진 응답의 판정을 7.0.6 ``CommonOut`` 에 맞춘다.

``CommonOut`` 은 빠진 ``strResult`` 를 ``commonFail()`` 이 비교하는 보호 상수로
채운다(``analysis/jadx/sources/com/korail/talk/network/model/CommonOut.java:361,455-462``).
역 정보처럼 봉투가 없는 응답은 ``require_envelope=False`` 로 이 판정을 거치지 않고,
``CommonOut`` 을 상속하지 않는 7.0.6 응답 모델은 V7 게이트웨이가 제외한다.
"""

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailNoResultsError,
    KorailSessionExpiredError,
)
from korail_mobile_api.http import KorailHttpClient, parse_base_response
from korail_mobile_api.v7 import V7Response


DELAY_DISCOUNT = "/classes/com.korail.mobile.passCard.DelayDiscountView"


def _client_returning(payload: dict[str, object]) -> KorailHttpClient:
    return KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    )


def test_missing_str_result_is_a_failure_by_default():
    with pytest.raises(KorailNoResultsError) as excinfo:
        parse_base_response({"h_msg_cd": "WRG000000", "h_msg_txt": "없음"})
    assert excinfo.value.code == "WRG000000"
    with pytest.raises(KorailAppError):
        parse_base_response({})


def test_missing_str_result_keeps_session_expiry_first():
    with pytest.raises(KorailSessionExpiredError):
        parse_base_response({"h_msg_cd": "P058", "h_msg_txt": "세션 만료"})


def test_missing_str_result_opt_outs_return_the_envelope():
    payload = {"h_msg_cd": "WRG000000", "h_msg_txt": "없음"}
    assert parse_base_response(payload, raise_on_fail=False).str_result is None
    assert parse_base_response(payload, require_result=False).str_result is None
    assert parse_base_response({"strResult": "SUCC"}).str_result == "SUCC"


def test_transport_rejects_an_envelope_without_str_result():
    client = _client_returning({"h_msg_cd": "WRG000000", "h_msg_txt": "없음"})
    with pytest.raises(KorailNoResultsError):
        client.post_query(DELAY_DISCOUNT, {"h_page_no": "20991231"})


def test_envelope_free_reads_are_unchanged():
    client = _client_returning({"stns": {"stn": []}})
    response = client.post_query(
        DELAY_DISCOUNT, {"h_page_no": "20991231"}, require_envelope=False
    )
    assert response.str_result is None
    assert response.raw == {"stns": {"stn": []}}


def _v7_client(payload: dict[str, object]) -> KorailClient:
    return KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=payload)),
    )


def test_v7_common_out_model_without_str_result_fails():
    # ExecuteOnlineRefundsOut extends CommonOut (it is NOT in the trimmed
    # _NON_COMMON_OUT_RESPONSE_MODELS).
    client = _v7_client({"h_msg_cd": "WRG000000", "h_msg_txt": "없음"})
    try:
        with pytest.raises(KorailNoResultsError):
            client.v7.call("NetworkApi.executeOnlineRefunds", {"x": "y"})
    finally:
        client.close()


def test_v7_non_common_out_model_without_str_result_is_returned():
    # VerifyOnlineRefundsOut does not extend CommonOut (it IS the one entry
    # left in _NON_COMMON_OUT_RESPONSE_MODELS).
    client = _v7_client({"h_msg_cd": "S000"})
    try:
        response = client.v7.call("NetworkApi.verifyOnlineRefunds", {"x": "y"})
    finally:
        client.close()
    assert isinstance(response, V7Response)
    assert response.raw == {"h_msg_cd": "S000"}
