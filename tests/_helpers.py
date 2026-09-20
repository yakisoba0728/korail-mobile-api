# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""Plain helpers several test files share. Not fixtures, and not in conftest.

Test modules import these by name (``from _helpers import ...``); pytest puts
this directory on ``sys.path`` for them. conftest.py stays for fixtures, since
importing a conftest module directly is something pytest advises against.

Only helpers that were identical in every file that now uses them live here.
A file whose helper differs keeps its own, under its own name, so a shared
name never means two different things.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig, KorailSessionExpiredError
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_payloads import OriginalTicketReference


def make_authenticated_client(handler) -> KorailClient:
    """A default-config client with a synthetic session, answering through ``handler``."""
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        customer_no="SYNTHETIC_CUSTOMER_NO",
        raw={},
    )
    return client


def refuse_transport(request: httpx.Request) -> httpx.Response:
    """A transport handler for tests in which nothing may be sent."""
    raise AssertionError(f"nothing may be sent: {request.method} {request.url}")


def no_network_client() -> KorailClient:
    """A client with no session whose transport fails the test on any request.

    For the refusals that must come before anything is sent: no consent, no
    session.
    """
    return KorailClient(transport=httpx.MockTransport(refuse_transport))


def logged_in_no_network_client() -> KorailClient:
    """The same, with a session: for dry runs, which must not send either."""
    client = no_network_client()
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client


def korail_ok_envelope(**extra: object) -> dict[str, object]:
    """KORAIL's own success envelope (IRG000000, 정상처리되었습니다) plus ``extra``."""
    return {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "정상처리되었습니다",
        "strResult": "SUCC",
        **extra,
    }


def synthetic_ok_envelope(message: str, /, **extra: object) -> dict[str, object]:
    """A success envelope whose ``h_msg_txt`` is ``message``, plus ``extra``.

    ``message`` is required on purpose. Several files use a ``...SECRET`` text
    here to prove a response's repr hides h_msg_txt; a shared default would
    quietly take that canary away from whichever file stopped passing one.
    """
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": message,
        "strResult": "SUCC",
        **extra,
    }


def secret_ticket_reference(suffix: str = "1") -> OriginalTicketReference:
    """A ticket reference whose every value says SECRET, for redaction checks."""
    return OriginalTicketReference(
        sale_window_no=f"WINDOW_SECRET_{suffix}",
        sale_date=f"SALE_DATE_SECRET_{suffix}",
        sale_sequence=f"SALE_SEQUENCE_SECRET_{suffix}",
        return_password=f"RETURN_PASSWORD_SECRET_{suffix}",
    )


def recording_path_handler(
    responses: Mapping[str, Any],
    requests: list[httpx.Request],
) -> Callable[[httpx.Request], httpx.Response]:
    """A transport handler that records each request and answers by its path."""

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=responses[request.url.path])

    return handler


class ReplyRecorder:
    """A MockTransport handler that records requests and replies by path.

    A path with no reply fails the test, which catches a request the test did
    not expect as well as a wiring mistake.
    """

    def __init__(self, replies: dict[str, dict]) -> None:
        self.replies = replies
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        reply = self.replies.get(request.url.path)
        if reply is None:  # pragma: no cover - guards test wiring mistakes
            raise AssertionError(f"unexpected request to {request.url.path}")
        return httpx.Response(200, json=reply)


def client_with_replies(
    replies: dict[str, dict],
) -> tuple[KorailClient, ReplyRecorder]:
    """A logged-in client answering from ``replies``, and the recorder it uses."""
    recorder = ReplyRecorder(replies)
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client, recorder


def require_symbol(module: object, name: str) -> Any:
    """The attribute ``name`` of ``module``, or a clear assertion if absent."""
    value = getattr(module, name, None)
    assert value is not None, f"missing symbol: {name}"
    return value


def assert_p058_clears_session(
    build_client: Callable[[], KorailClient],
    call: Callable[[KorailClient], object],
) -> None:
    """A P058 envelope on a read must clear the session and cookies.

    ``build_client()`` returns a fresh client, already logged in and cookied,
    whose transport is wired to answer P058; ``call(client)`` is the read that
    must see it. Asserts the read raises ``KorailSessionExpiredError`` and
    that neither the session nor any cookie survives it.
    """
    client = build_client()
    try:
        with pytest.raises(KorailSessionExpiredError):
            call(client)
    finally:
        client.close()
    assert client.session.current is None
    assert not client.http.cookies


def raise_if_dynapath_invoked(context: object) -> str:
    """A DynaPath token provider for reads that must never ask for one."""
    raise AssertionError("DynaPath provider must not be invoked")


def recording_json_handler(
    requests: list[httpx.Request],
    body: object,
) -> Callable[[httpx.Request], httpx.Response]:
    """A transport handler that records each request and answers ``body`` as JSON.

    A fresh response per request: one httpx.Response shared across requests
    would carry one request's state into the next.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=body)

    return handler
