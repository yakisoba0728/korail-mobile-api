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
