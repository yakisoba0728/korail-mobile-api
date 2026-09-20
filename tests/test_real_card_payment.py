# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""Offline tests for ``pay_with_card``.

``pay_with_card`` and ``pay_with_fake_card`` are two separate methods, not one
method with a card-kind flag — the method name alone is the caller's
statement of which kind of card it is sending, same as korail2/SRT/srtgo.
These tests pin that both send unconditionally once a session exists, that
they build and transmit the same wire form, and that PNR/PAN redaction and
P058 session clearing still hold.

Everything runs against ``httpx.MockTransport``. No network, no credentials, and
the only card numbers here are obviously-fake placeholders.
"""

from __future__ import annotations

from urllib.parse import parse_qsl

import httpx
import pytest

from _helpers import ReplyRecorder as _Recorder
from _helpers import client_with_replies as _client_with
from korail_mobile_api import (
    CardPayment,
    KorailAuthError,
    KorailClient,
    KorailSession,
    KorailSessionExpiredError,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from korail_mobile_api.mutation_payloads import build_card_payment_form


PAYMENT_ROUTE = "/classes/com.korail.mobile.payment.ReservationPayment"

# Obviously-fake placeholders. 4111111111111111 is the industry-standard test
# PAN; it is not a real card and nothing here is ever transmitted anywhere.
PLACEHOLDER_CARD_NUMBER = "4111111111111111"
PLACEHOLDER_CARD_PASSWORD = "00"
PLACEHOLDER_CARD_EXPIRE = "3012"
PLACEHOLDER_BIRTHDAY = "900101"
SYNTHETIC_PNR = "SYNTHETIC_PNR_REFERENCE"

_PAYMENT_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRZ000001",
    "h_msg_txt": "paid",
    "h_img_tk_flg": "N",
}


def _hold() -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd="IRR000000",
        str_result="SUCC",
        raw={},
        pnr_no=SYNTHETIC_PNR,
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        temporary_job_sequence_1="SYNTHETIC_JOB_1",
        temporary_job_sequence_2="SYNTHETIC_JOB_2",
        total_price="8400",
        received_amount="8400",
    )


def _placeholder_card() -> CardPayment:
    return CardPayment(
        card_number=PLACEHOLDER_CARD_NUMBER,
        card_password=PLACEHOLDER_CARD_PASSWORD,
        card_expire=PLACEHOLDER_CARD_EXPIRE,
        birthday=PLACEHOLDER_BIRTHDAY,
    )


def test_pay_with_card_requires_an_authenticated_session():
    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({PAYMENT_ROUTE: _PAYMENT_SUCCESS}))
    )
    with pytest.raises(KorailAuthError):
        logged_out.pay_with_card(_hold(), _placeholder_card())


def test_pay_with_card_live_posts_to_the_payment_route_and_parses_the_receipt():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    result = client.pay_with_card(_hold(), _placeholder_card())
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "SUCC"
    assert result.h_msg_cd == "IRZ000001"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].method == "POST"
    assert recorder.requests[0].url.path == PAYMENT_ROUTE


def test_pay_with_card_returns_a_declined_envelope_instead_of_raising():
    # Deliberate: a real payment that the PG refuses must hand the caller the
    # server's own code so it can cancel the still-unpaid hold, not an
    # exception that says nothing about whether the hold survived.
    client, recorder = _client_with(
        {
            PAYMENT_ROUTE: {
                "strResult": "FAIL",
                "h_msg_cd": "WRC000123",
                "h_msg_txt": "card declined",
            }
        }
    )
    result = client.pay_with_card(_hold(), _placeholder_card())
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "FAIL"
    assert result.h_msg_cd == "WRC000123"
    assert len(recorder.requests) == 1


def _sent_form(request: httpx.Request) -> dict[str, str]:
    """The decoded form body. A repeated key fails rather than keeping the last."""
    pairs = parse_qsl(
        request.content.decode("ascii"),
        keep_blank_values=True,
        strict_parsing=True,
    )
    form = dict(pairs)
    assert len(form) == len(pairs), "the payment form repeated a key"
    return form


def test_pay_with_card_and_pay_with_fake_card_remain_two_distinct_methods():
    # Neither takes a card-kind flag; the method name alone is the caller's
    # statement, and both send unconditionally once a session exists.
    assert KorailClient.pay_with_card is not KorailClient.pay_with_fake_card
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    client.pay_with_card(_hold(), _placeholder_card())
    client.pay_with_fake_card(_hold(), _placeholder_card())
    assert len(recorder.requests) == 2


def test_pay_with_card_sends_the_same_form_pay_with_fake_card_would():
    # The two methods differ only in name; the wire shape is one builder, so
    # a real payment cannot drift from the verified one.
    # Keys AND values: set() over a dict compares the keys alone.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    client.pay_with_card(_hold(), _placeholder_card())
    client.pay_with_fake_card(_hold(), _placeholder_card())
    real, fake = (_sent_form(request) for request in recorder.requests)
    expected = build_card_payment_form(
        client.config, _hold(), _placeholder_card()
    )
    assert real == expected
    assert fake == real


def test_pay_with_card_transmits_the_card_the_caller_passed():
    # The test above measures the client against its own builder, so a card
    # swapped inside the builder would pass it. These pin the charged values
    # against the caller's literals instead.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_SUCCESS})
    client.pay_with_card(_hold(), _placeholder_card())
    sent = _sent_form(recorder.requests[0])
    assert sent["hidStlCrCrdNo1"] == PLACEHOLDER_CARD_NUMBER
    assert sent["hidVanPwd1"] == PLACEHOLDER_CARD_PASSWORD
    assert sent["hidCrdVlidTrm1"] == PLACEHOLDER_CARD_EXPIRE
    assert sent["hidAthnVal1"] == PLACEHOLDER_BIRTHDAY
    assert sent["hidMnsStlAmt1"] == _hold().received_amount


_SESSION_EXPIRED = {
    "strResult": "FAIL",
    "h_msg_cd": "P058",
    "h_msg_txt": "session expired",
}


def test_an_expired_session_on_pay_with_card_clears_the_client_before_raising():
    # The same pin as test_mutation_live_paths.py's parametrized P058 test,
    # for pay_with_card: one request out, no session or cookie left after P058.
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_SESSION_EXPIRED)

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    client.http.cookies.set(
        "JSESSIONID", "synthetic-secret", domain="smart.letskorail.com"
    )
    try:
        with pytest.raises(KorailSessionExpiredError):
            client.pay_with_card(_hold(), _placeholder_card())
    finally:
        client.close()
    assert len(seen) == 1
    assert client.session.current is None
    assert not client.http.cookies
