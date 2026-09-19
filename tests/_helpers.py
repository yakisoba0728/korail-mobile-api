# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Plain helpers several test files share. Not fixtures, and not in conftest.

Test modules import these by name (``from _helpers import ...``); pytest puts
this directory on ``sys.path`` for them. conftest.py stays for fixtures, since
importing a conftest module directly is something pytest advises against.

Only helpers that were identical in every file that now uses them live here.
A file whose helper differs keeps its own, under its own name, so a shared
name never means two different things.
"""

from __future__ import annotations

import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.models import KorailSession


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
