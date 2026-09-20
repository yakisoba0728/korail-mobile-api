# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""NetFunnel 가상 대기열(``nf.letskorail.com``).

앱은 조회·예약·결제·예약목록 경로에 대기열을 물려 두었고 성수기 조회 전용
액션(``act_8_2``)까지 따로 갖고 있습니다. **기본값은 꺼짐**
(:attr:`~korail_mobile_api.config.KorailConfig.netfunnel_enabled`).

KORAIL 은 JS 방언을 쓰지 않습니다
-----------------------------------
KORAIL 은 STCLab **네이티브 안드로이드 SDK**(``T6``/``U6`` 패키지)를 씁니다.
SRT 의 WebView ``netfunnel.js`` 와 차이:

1. ``js``·``nfid``·``prefix``·epoch 꼬리 없음(``T6/d.java:30-31,54-55,78-79,99-101``).
2. ``sid``/``aid`` 는 5101 에만(``T6/d.java:99-101``). 5002 에 싣는 JS 방언과 반대.
3. ``ttl`` 은 되돌려 보내지 않음 — 순수 클라이언트 힌트(``T6/g.java:462,467``).
4. 응답은 ``<code>:<params>`` (``T6/i.java:36-43``).

진입 순서: 5101 → 5002 → 5004
-------------------------------
5101 표는 ``chkEnter`` 가 더 짧은 세션 키로 바꿔 주고, 그 키만 ``setComplete``
가 받습니다. 매 단계의 키가 앞 키를 **대체**합니다(``T6/d.java:61,79,107``).

대기열은 풀이고 세션은 그중 한 노드에 삽니다
----------------------------------------------
``nf.letskorail.com`` 은 분산 정문. 세션을 완료할 수 있는 곳은 진입이 떨어진
노드뿐이고, 응답의 ``ip``/``port`` 가 그 노드입니다(``T6/i.java:50-53``,
``T6/d.makeURL``, ``T6/d.java:17-19``).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from urllib.parse import urlencode

import httpx

from .config import KorailConfig
from .constants import (
    KORAIL_NETFUNNEL_PATH,
    KORAIL_NETFUNNEL_SERVICE_ID,
    KorailNetFunnelAction,
    KorailNetFunnelOpcode,
)
from .errors import (
    KorailNetFunnelError,
    KorailProtocolError,
    KorailQueueRejectedError,
    KorailTransportError,
)
from .safety import (
    assert_korail_netfunnel_opcode_origin,
    assert_korail_netfunnel_origin,
    assert_netfunnel_request,
    korail_netfunnel_node_url,
)


# ---------------------------------------------------------------------------
# Status codes — ``T6/a.java``, smali ``T6/a.smali:228-281,319,510-574``.
# ---------------------------------------------------------------------------
SUCCESS_CODE = "200"
BYPASS_CODE = "300"
#: ExpressNumber — 300 처럼 키 없이 통과한다.
EXPRESS_CODE = "303"
#: 키 없이 통과할 수 있는 코드. 키 없는 토큰 가운데 이것만 우회이고, 놓을 슬롯도 없다.
KEYLESS_PASS_CODES = frozenset({BYPASS_CODE, EXPRESS_CODE})
#: 통과. 200 은 키 발급, 300·303 은 키 없이도 통과할 수 있다.
SUCCESS_CODES = frozenset({SUCCESS_CODE, *KEYLESS_PASS_CODES})
#: 아직 대기 중(``T6/g.java:451``).
CONTINUE_CODES = frozenset({"201", "202"})
#: ``TsErrorAComplete`` — setComplete 에서만 받아들임.
ALREADY_COMPLETE_CODE = "502"
#: 완료 불가. ``503:msg="Wrong Server ID"`` — 5101 표를 setComplete 에 보낸 경우
#: 또는 엉뚱한 노드에 요청한 경우.
NOT_COMPLETABLE_CODE = "503"
#: ``TsBlock``(301)/``TsIpBlock``(302). ``T6/g.java:892-894`` ``isBlocking()``.
#: ``TsExpressNumber``(303)는 성공(``T6/g.java:909`` ``isSuccess()``).
QUEUE_REJECTED_CODES = frozenset({"301", "302"})

# TTL clamp: ``T6/g.java:462`` → ``T6/i.java:175-181``, max_ttl=30(``T6/h.java:40``), floor=1.
MAX_TTL_SECONDS = 30
MIN_TTL_SECONDS = 1

# 이 라이브러리 자체의 폴링 상한 — 앱은 ``while(true)``(``T6/g.java:449``)이지만
# 대기실 대화상자가 있어 사람이 닫을 수 있다. 이 라이브러리에는 그런 탈출구가 없다.
QUEUE_POLL_LIMIT = 20
QUEUE_WAIT_LIMIT_SECONDS = 60.0


@dataclass(frozen=True)
class KorailNetFunnelToken:
    """파싱된 NetFunnel 응답 하나.

    ``key`` 는 슬롯 식별자. ``node`` 는 응답한 대기열 노드 origin (풀 규칙 검사 통과).
    토큰은 세션이 아니라 응답 하나 — 응답마다 키가 대체됩니다.
    """

    action: str
    key: str
    code: str
    params: dict[str, str] = field(default_factory=dict[str, str])
    node: str = ""

    @property
    def wait_count(self) -> int:
        """``nwait`` — 앞에 몇 명이 서 있는지."""
        raw = self.params.get("nwait", "")
        return int(raw) if raw.isascii() and raw.isdigit() else 0


# ---------------------------------------------------------------------------
# URL builders
# ---------------------------------------------------------------------------

def _netfunnel_url(netfunnel_url: str, params: Sequence[tuple[str, str]]) -> str:
    """대기열 URL 을 조립하며 가드를 통과시킵니다."""
    assert_netfunnel_request("GET", KORAIL_NETFUNNEL_PATH, params)
    assert_korail_netfunnel_opcode_origin(dict(params)["opcode"], netfunnel_url)
    return (
        f"{netfunnel_url.rstrip('/')}{KORAIL_NETFUNNEL_PATH}"
        f"?{urlencode(params)}"
    )


def get_tid_chk_enter_params(
    action: str,
    *,
    service_id: str = KORAIL_NETFUNNEL_SERVICE_ID,
) -> tuple[tuple[str, str], ...]:
    """5101 파라미터: ``opcode``, ``sid``, ``aid`` (``T6/d.java:99-101``)."""
    return (
        ("opcode", KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value),
        ("sid", service_id),
        ("aid", str(action)),
    )


def _keyed_opcode_params(
    opcode: KorailNetFunnelOpcode,
    key: str,
    *,
    purpose: str,
) -> tuple[tuple[str, str], ...]:
    """``opcode``+``key`` 만 싣는 요청 파라미터 — 5002/5004 공통 형태.

    빈 키는 :class:`~korail_mobile_api.errors.KorailProtocolError` 다. 맨
    ``ValueError`` 였을 때는 :meth:`KorailNetFunnelClient.check` 가 키 가드 없이
    여기 닿으므로(``release`` 와 달리 ``if not token.key`` 가 없다), 이 패키지의
    실패를 ``except KorailApiError`` 로 받던 호출자를 그냥 통과해 버렸다 —
    ``errors`` 모듈이 계약처럼 선언하는 "모든 실패의 뿌리" 밖이었다.
    """
    if not key:
        raise KorailProtocolError(f"{purpose} requires a non-empty key")
    return (
        ("opcode", opcode.value),
        ("key", key),
    )


def chk_enter_params(key: str) -> tuple[tuple[str, str], ...]:
    """5002 파라미터: ``opcode``, ``key`` (``T6/d.java:54-55``)."""
    return _keyed_opcode_params(
        KorailNetFunnelOpcode.CHK_ENTER,
        key,
        purpose="chkEnter",
    )


def set_complete_params(key: str) -> tuple[tuple[str, str], ...]:
    """5004 파라미터: ``opcode``, ``key`` (``T6/d.java:78-79``)."""
    return _keyed_opcode_params(
        KorailNetFunnelOpcode.SET_COMPLETE,
        key,
        purpose="setComplete",
    )


def build_get_tid_chk_enter_url(
    netfunnel_url: str,
    *,
    action: str,
    service_id: str = KORAIL_NETFUNNEL_SERVICE_ID,
) -> str:
    """5101 URL — 정문에서 ``action`` 의 표를 받습니다."""
    return _netfunnel_url(
        netfunnel_url,
        get_tid_chk_enter_params(action, service_id=service_id),
    )


def build_chk_enter_url(netfunnel_url: str, *, key: str) -> str:
    """5002 URL — 노드에서 입장을 확인합니다."""
    return _netfunnel_url(netfunnel_url, chk_enter_params(key))


def build_set_complete_url(netfunnel_url: str, *, key: str) -> str:
    """5004 URL — 노드에서 슬롯을 놓습니다."""
    return _netfunnel_url(netfunnel_url, set_complete_params(key))


# ---------------------------------------------------------------------------
# Response parsers
# ---------------------------------------------------------------------------

def _queue_failure(
    token: KorailNetFunnelToken,
    message: str,
    body: str,
) -> KorailNetFunnelError:
    subclass = (
        KorailQueueRejectedError
        if token.code in QUEUE_REJECTED_CODES
        else KorailNetFunnelError
    )
    return subclass(token.code or None, message, raw=body)


def parse_netfunnel_body(body: str, *, action: str) -> KorailNetFunnelToken:
    """네이티브 SDK 응답을 코드와 파라미터로 가름. ``T6/i.Parser``(``T6/i.java:35-63``).

    첫 ``:`` 앞 = 상태 코드, 나머지 = ``&`` 로 갈라 ``name=value`` 쌍.
    ``ip``/``port`` 는 :func:`~korail_mobile_api.safety.korail_netfunnel_node_url`
    을 통과시킵니다 — 풀 밖 호스트는 여기서 예외.
    """
    head, separator, tail = body.strip().partition(":")
    if not separator or not head.isdigit():
        raise KorailNetFunnelError(
            None,
            "KORAIL NetFunnel response was not the native SDK's "
            "'<code>:<params>' form; a 'NetFunnel.gRtype=...' body would mean "
            "the server answered the JavaScript dialect, which this app's own "
            "parser (T6/i.java:36-42) cannot read either",
            raw=body,
        )
    params: dict[str, str] = {}
    for item in tail.split("&"):
        name, found, value = item.partition("=")
        if found:
            params[name] = value
    return KorailNetFunnelToken(
        action=action,
        key=params.get("key", ""),
        code=head,
        params=params,
        node=korail_netfunnel_node_url(
            params.get("ip", ""),
            params.get("port", ""),
        ),
    )


def _require_pass_key(token: KorailNetFunnelToken, body: str) -> None:
    """300·303은 키 없이도 성공한다. 슬롯을 가진 200은 키가 필요하다."""
    if not token.key and token.code not in KEYLESS_PASS_CODES:
        raise KorailNetFunnelError(
            None,
            "KORAIL NetFunnel response did not include a non-empty key",
            raw=body,
        )


def parse_queue_response(body: str, *, action: str) -> KorailNetFunnelToken:
    """5101/5002 응답. 통과(200/300)·대기(201/202) → 토큰, 그 밖 → 예외."""
    token = parse_netfunnel_body(body, action=action)
    if token.code in CONTINUE_CODES:
        return token
    if token.code not in SUCCESS_CODES:
        raise _queue_failure(
            token,
            "KORAIL NetFunnel did not admit this request to the queue",
            body,
        )
    _require_pass_key(token, body)
    return token


def is_queued(token: KorailNetFunnelToken) -> bool:
    """대기열이 "나중에 다시 오라"고 했는지."""
    return token.code in CONTINUE_CODES


def queue_wait_seconds(token: KorailNetFunnelToken) -> int:
    """다음 chkEnter 까지 잘 시간. ``T6/i.java:175-181`` max=30, min=1."""
    raw = token.params.get("ttl", "")
    ttl = int(raw) if raw.isascii() and raw.isdigit() else 0
    return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class KorailNetFunnelClient:
    """대기열 전용 클라이언트. 대기열 호스트의 ``/ts.wseq`` 밖으로 나갈 수 없음.

    :class:`~korail_mobile_api.http.KorailHttpClient` 와 분리 — 그쪽은
    ``smart.letskorail.com`` 에 고정, 이쪽은 대기열 정문+노드 전용.
    """

    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        config = config or KorailConfig()
        if not config.netfunnel_enabled:
            raise KorailNetFunnelError(
                None,
                "KORAIL NetFunnel is disabled by default and must be opted into "
                "explicitly with KorailConfig(netfunnel_enabled=True); every "
                "live call this library has made succeeded without a queue "
                "token, so enabling it costs a round trip per gated operation "
                "and buys nothing until the server actually meters us",
            )
        assert_korail_netfunnel_origin(config.netfunnel_url)
        self.config = config
        self._sleep = sleeper
        self._clock = clock
        self._client = httpx.Client(
            base_url=config.netfunnel_url,
            timeout=config.netfunnel_timeout,
            headers={
                "User-Agent": config.user_agent,
                "Connection": "close",
            },
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        """대기열 HTTP 연결을 닫습니다."""
        self._client.close()

    def _get(self, url: str) -> str:
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                "KORAIL transport failed for GET "
                f"{KORAIL_NETFUNNEL_PATH}"
            ) from exc
        if response.is_error:
            raise KorailTransportError(
                f"KORAIL NetFunnel HTTP {response.status_code} for GET "
                f"{KORAIL_NETFUNNEL_PATH}"
            )
        return response.text

    def enter(self, action: str) -> KorailNetFunnelToken:
        """5101 — 정문에서 표를 받습니다."""
        body = self._get(
            build_get_tid_chk_enter_url(
                self.config.netfunnel_url,
                action=action,
            )
        )
        return parse_queue_response(body, action=str(action))

    def check(
        self,
        action: str,
        key: str,
        *,
        node: str = "",
    ) -> KorailNetFunnelToken:
        """5002 — 입장 확인 또는 대기 재질의."""
        body = self._get(
            build_chk_enter_url(node or self.config.netfunnel_url, key=key)
        )
        return parse_queue_response(body, action=str(action))

    def release(self, token: KorailNetFunnelToken) -> None:
        """5004 — 슬롯을 놓습니다.

        키 없는 BYPASS(300)·ExpressNumber(303)는 놓을 것이 없으므로 즉시 리턴
        (``T6/d.java:70-73`` ``getKey().length() < 1``). 그 외의 키 없는 토큰
        (코드가 300/303 이 아님)은 네트워크를 건드리지 않고 바로
        :class:`~korail_mobile_api.errors.KorailNetFunnelError` 를 냅니다.
        """
        if not token.key:
            if token.code in KEYLESS_PASS_CODES:
                return
            raise KorailNetFunnelError(
                token.code or None,
                "KORAIL NetFunnel slot cannot be released because its token "
                "carries no key, and only keyless 300/303 passes may skip release; the "
                "slot is held until the server times it out",
            )
        self._get(
            build_set_complete_url(
                token.node or self.config.netfunnel_url,
                key=token.key,
            )
        )
        # 7.0.6 CommandClient.Complete clears its response without parsing it.

    def acquire(self, action: str) -> KorailNetFunnelToken:
        """5101→5002 교환 + 대기 폴링. 통과 토큰을 돌려줍니다.

        키 없는 BYPASS(300)·ExpressNumber(303)면 키·세션·노드 없이 즉시 리턴.
        그 외에는 5002 를 무조건 거쳐야 setComplete 가 받는 키를 얻습니다. 키 없이
        대기(201/202)를 받으면 폴링할 수 없으므로
        :class:`~korail_mobile_api.errors.KorailNetFunnelError` 입니다.

        상한: :data:`QUEUE_POLL_LIMIT` 또는 :data:`QUEUE_WAIT_LIMIT_SECONDS`.
        """
        token = self.enter(action)
        if not token.key:
            # parse_queue_response lets a keyless token through for exactly two
            # reasons: a 300/303 pass, or a wait. Only the first is a bypass.
            if is_queued(token):
                raise KorailNetFunnelError(
                    token.code,
                    "KORAIL NetFunnel told this request to wait but gave it no "
                    "key to poll with; only a 300/303 pass may arrive without one",
                )
            return token  # bypass
        key = token.key
        node = token.node
        started = self._clock()
        polls = 0
        while True:
            if is_queued(token):
                if polls >= QUEUE_POLL_LIMIT:
                    raise KorailNetFunnelError(
                        token.code,
                        "KORAIL NetFunnel queue did not admit this request "
                        f"within {QUEUE_POLL_LIMIT} polls; the wait is bounded "
                        "on purpose and this library does not retry on its own "
                        "initiative",
                        raw=key,
                    )
                wait = queue_wait_seconds(token)
                if self._clock() - started + wait > QUEUE_WAIT_LIMIT_SECONDS:
                    raise KorailNetFunnelError(
                        token.code,
                        "KORAIL NetFunnel queue did not admit this request "
                        f"within {QUEUE_WAIT_LIMIT_SECONDS:.0f}s; the wait is "
                        "bounded on purpose and this library does not retry on "
                        "its own initiative",
                        raw=key,
                    )
                self._sleep(wait)
                polls += 1
            token = self.check(action, key, node=node)
            key = token.key or key
            node = token.node or node
            if not is_queued(token):
                return replace(token, node=node)

    @contextmanager
    def slot(self, action: str) -> Generator[KorailNetFunnelToken, None, None]:
        """한 작업 동안 슬롯을 쥐었다가 놓습니다.

        해제는 양쪽 경로에서 일어남(``BaseDaoHelper.java:105-107`` ``onPostExecute``).
        본문 성공 시 해제 실패는 예외, 본문 실패 시 해제 실패는 note 로 붙임.
        """
        token = self.acquire(action)
        try:
            yield token
        except BaseException as exc:
            try:
                self.release(token)
            except Exception as release_error:
                exc.add_note(
                    "KORAIL NetFunnel slot release also failed and the slot may "
                    f"be held until the server times it out: {release_error}"
                )
            raise
        self.release(token)


# ---------------------------------------------------------------------------
# Action routing
# ---------------------------------------------------------------------------

def inquiry_action(*, peak_season: bool) -> KorailNetFunnelAction:
    """열차조회 액션 선택(``b5/c.java:439``).

    ``isPeakSeason`` 은 서버 달력 데이터(``S4/C0805e.java:116-121``). 달력을
    아직 받지 않았으면 ``false``(``:117``). 이 함수는 날짜가 아니라 플래그를 받음.
    """
    return (
        KorailNetFunnelAction.PEAK_SEASON_INQUIRY
        if peak_season
        else KorailNetFunnelAction.INQUIRY
    )
