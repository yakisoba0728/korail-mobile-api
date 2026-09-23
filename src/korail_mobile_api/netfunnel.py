# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""NetFunnel 가상 대기열(``nf.letskorail.com``).

앱은 조회·예약·결제·예약목록 경로에 대기열을 물려 두었고 성수기 조회 전용
액션(``act_8_2``)까지 따로 갖고 있습니다. **기본값은 꺼짐**
(:attr:`~korail_mobile_api.config.KorailConfig.netfunnel_enabled`).

인용
----
7.0.6 의 NetFunnel SDK 는 ``com/netfunnel/api/`` 아래에 **난독화되지 않은
평문**으로 들어 있습니다(``Code``·``Command``·``CommandClient``·``Netfunnel``·
``Property``·``Response``, ``http/URL``·``http/Client``). 아래 줄 번호는 모두
7.0.6 기준입니다.

KORAIL 은 JS 방언을 쓰지 않습니다
-----------------------------------
KORAIL 은 STCLab **네이티브 안드로이드 SDK**(``com.netfunnel.api`` 패키지)를
씁니다. SRT 의 WebView ``netfunnel.js`` 와 차이:

1. ``js``·``nfid``·``prefix``·epoch 꼬리 없음. 요청 파라미터를 싣는 네 곳이
   ``CommandClient`` 에 다 있고 ``addParam`` 호출이 전부입니다 —
   5101 ``GetTidCheckedEnter``(``CommandClient.java:59-67``),
   5002 ``CheckedEnter``(``:122-125``),
   5004 ``Complete``(``:178-181``),
   5003 ``AliveNotice``(``:217-220``). 그 밖의 파라미터는 없습니다.
2. ``sid``/``aid`` 는 5101 에만(``CommandClient.java:61``, ``:63``). 5002 에
   싣는 JS 방언과 반대이고, 5002/5004 는 ``opcode``+``key`` 뿐입니다.
3. ``ttl`` 은 되돌려 보내지 않음 — 순수 클라이언트 힌트. 위 네 파라미터
   블록 어디에도 ``ttl`` 이 없고, 읽은 ``ttl`` 은
   ``Netfunnel.java:519-521`` 에서 **로컬 sleep 기한**을 계산하는 데만
   쓰입니다(``getTTL(...)`` → ``currentTimeMillis() + ttl*1000``).
4. 응답은 ``<code>:<params>`` (``Response.Parser``,
   ``Response.java:128-137`` — 첫 ``:`` 위치를 ``indexOf`` 로 찾고
   (``:129``) 없으면 ``Code.ErrorData``(``:130-131``), 있으면 앞을
   코드로 파싱하고 뒤를 ``&`` 로 쪼개 ``=`` 로 가릅니다(``:135-137``)).

진입 순서: 5101 → 5002 → 5004
-------------------------------
5101 표는 ``chkEnter`` 가 더 짧은 세션 키로 바꿔 주고, 그 키만 ``setComplete``
가 받습니다. 매 단계의 키가 앞 키를 **대체**합니다 — ``CommandClient`` 는
키만 따로 들지 않고 응답 객체 전체를 갈아 끼웁니다:
``this.response_ = responseParser.clone()`` 이 5101 뒤(``:80``), 5002 뒤
(``:137``), 5003 뒤(``:232``)에 있고, 5004 는 대신 비웁니다
(``this.response_.clear()``, ``:184``).

대기열은 풀이고 세션은 그중 한 노드에 삽니다
----------------------------------------------
``nf.letskorail.com`` 은 분산 정문. 세션을 완료할 수 있는 곳은 진입이 떨어진
노드뿐이고, 응답의 ``ip``/``port`` 가 그 노드입니다 —
``Response.Parser`` 가 ``ip`` 를 ``setHost``, ``port`` 를 ``setPort`` 에
넣고(``Response.java:143-146``), ``CommandClient.makeURL(Property, Response)``
(``:33-38``)가 그 host/port 로 URL 을 다시 만듭니다.
**단** 그 재조립에는 ``!property.isHostNotmodify()`` 조건이 붙어 있고 7.0.6
의 컴파일된 기본값은 ``true`` 입니다 —
:mod:`korail_mobile_api.netfunnel_safety` 의 같은 대목 참고.
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
from .netfunnel_safety import (
    assert_korail_netfunnel_opcode_origin,
    assert_korail_netfunnel_origin,
    assert_netfunnel_request,
    korail_netfunnel_node_url,
)


# ---------------------------------------------------------------------------
# Status codes — 7.0.6: com/netfunnel/api/Code.java:13-... (평문으로 읽힘).
# 아래 상수에 해당하는 항목:
#   Success(200)            Code.java:27
#   Continue(201)           :28   ← jadx 가 ComposerKt.providerKey 로 표기;
#                                   ComposerKt.java:35 에서 201
#   ContinueDebug(202)      :29   ← ComposerKt.compositionLocalMapKey = 202
#                                   (ComposerKt.java:29)
#   TsBypass(300)           :30
#   TsBlock(301)            :31
#   TsIpBlock(302)          :32
#   TsExpressNumber(303)    :33
#   TsErrorAComplete(502)   :36
#   TsErrorWrongServer(503) :37
# ---------------------------------------------------------------------------
SUCCESS_CODE = "200"
BYPASS_CODE = "300"
#: ExpressNumber — 300 처럼 키 없이 통과한다.
EXPRESS_CODE = "303"
#: 키 없이 통과할 수 있는 코드. 키 없는 토큰 가운데 이것만 우회이고, 놓을 슬롯도 없다.
KEYLESS_PASS_CODES = frozenset({BYPASS_CODE, EXPRESS_CODE})
#: 통과. 200 은 키 발급, 300·303 은 키 없이도 통과할 수 있다.
SUCCESS_CODES = frozenset({SUCCESS_CODE, *KEYLESS_PASS_CODES})
#: 아직 대기 중. 7.0.6: ``Netfunnel.EvnetCode.isContinue()``
#: (``Netfunnel.java:106-108``) 이 ``Continue`` 와 ``ContinueInterval``
#: 둘만 참으로 봅니다(``:62``, ``:65``). 대기 루프의 실제 탈출 조건은
#: ``Netfunnel.java:505`` 의 ``getCode() != Code.Continue &&
#: getCode() != Code.ContinueDebug`` 이므로, 와이어 코드로는 201/202 가
#: 대기입니다(``Code.java:28-29``).
CONTINUE_CODES = frozenset({"201", "202"})
#: ``TsErrorAComplete`` — setComplete 에서만 받아들임.
ALREADY_COMPLETE_CODE = "502"
#: 완료 불가. ``503:msg="Wrong Server ID"`` — 5101 표를 setComplete 에 보낸 경우
#: 또는 엉뚱한 노드에 요청한 경우.
NOT_COMPLETABLE_CODE = "503"
#: ``TsBlock``(301)/``TsIpBlock``(302) — ``Code.java:31-32``. 7.0.6 의
#: ``isBlocking()`` 은 ``Netfunnel.java:114-116`` 이고 정확히 이 둘만
#: 참입니다(``EvnetCode.Block``/``IpBlock``, ``:67-68``).
#: ``TsExpressNumber``(303, ``Code.java:33``)는 성공 쪽입니다 —
#: ``isSuccess()``(``Netfunnel.java:102-104``)가 ``Success``·``NotUsed``·
#: ``Bypass``·``ErrorBypass``·``ExpressNumber`` 다섯을 참으로 봅니다.
#: (``NotUsed``/``ErrorBypass`` 는 이 라이브러리가 성공으로 세지 않는
#: 항목이라 :data:`SUCCESS_CODES` 와 완전히 같지는 않습니다.)
QUEUE_REJECTED_CODES = frozenset({"301", "302"})

# TTL clamp: 7.0.6 ``Response.getTTL(int, int)`` 는
# ``com/netfunnel/api/Response.java:59-66`` 이고, 실제 clamp 본문은
# ``:61-65`` 입니다.
#
#   * 상한은 ``:62-64`` (``if (i <= 0 || i3 <= i) i = i3;``), **하한은
#     ``:65``** (``return i < i2 ? i2 : i;``) 입니다. ``:60`` 은 DLog 한 줄입니다.
#   * 1 과 30 은 메서드에 박힌 값이 아니라 **호출자가 넘기는 인자**입니다
#     (시그니처는 ``getTTL(int max, int min)``). 그래서 메서드 자체는
#     clamp(min, max) 이고, 상한 인자가 0 이하면 상한을 아예 적용하지
#     않습니다.
# 결과는 clamp(1, 30) 입니다 — 네 호출부 전부가 ``getTTL(getProperty().getMaxTTL(),
# 1)`` 로 부르므로(``Netfunnel.java:519,634,736,790``) 하한은 리터럴 1 이고
# 상한은 maxTTL 입니다. 상한 30 은 ``Property.java:22`` 의
# 컴파일된 기본값 ``max_ttl_ = 30`` 이며(게터는 ``Property.java:164``),
# ``LoadProperty.java:92`` 의 ``setMaxTTL(jSONObject2.getInt("max_ttl"))`` 가
# 원격 JSON 으로 override 할 수 있게 해 두어 런타임 실제 값은 PROTECTED 다.
MAX_TTL_SECONDS = 30
MIN_TTL_SECONDS = 1

# 이 라이브러리 자체의 폴링 상한 — 7.0.6 의 대기 스레드는 정말 무한 루프다
# (``com/netfunnel/api/Netfunnel.java:503`` ``while (true)``), 반복 횟수도
# 누적 wall-clock 상한도 없다. 빠져나가는 것은 비-Continue 코드(:505)와
# ``is_continue_stop_`` 플래그(:528)뿐이고, 그 플래그는 화면이 닫힐 때
# ``stopNetFunnel()`` 로 켜진다(``TrainScheduleScreenKt.java:205``,
# ``HomeScreenKt.java:630``, ``PayScreenKt.java:606``) — 이 주석이 말하는
# "대기실 대화상자" 가 바로 그 탈출구다. 이 라이브러리에는 화면이 없어 그런
# 탈출구도 없으므로 대신 이 상한을 둔다.
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
    """5101 파라미터: ``opcode``, ``sid``, ``aid``.

    7.0.6: ``CommandClient.GetTidCheckedEnter()``
    (``com/netfunnel/api/CommandClient.java:40-99``)의 ``addParam`` 블록 —
    ``opcode``(``:59``, 값은 ``Command.GET_TID_CHK_ENTER.value()`` = 5101,
    ``:57``), ``sid``(``:61``, ``property.getServiceID()``),
    ``aid``(``:63``, ``property.getActionID()``). 넷째로 ``user_data`` 가
    있지만 **길이가 0 이 아닐 때만** 붙고(``:65-68``) KORAIL 은 설정하지
    않습니다(``Property.java:21`` 의 ``user_data_ = ""`` 이 기본값이고
    ``KorailTalkApplication.setNetFunnel()`` 이 건드리지 않음) — 그래서
    이 함수도 싣지 않습니다.
    """
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

    빈 키는 :class:`~korail_mobile_api.errors.KorailProtocolError` 다 — 맨
    ``ValueError`` 가 아니다. :meth:`KorailNetFunnelClient.check` 가 키 가드 없이
    여기 닿으므로(``release`` 와 달리 ``if not token.key`` 가 없다), 이 패키지의
    실패를 ``except KorailApiError`` 로 받는 호출자에게 닿으려면
    ``errors`` 모듈의 "모든 실패의 뿌리" 안에 있어야 한다.
    """
    if not key:
        raise KorailProtocolError(f"{purpose} requires a non-empty key")
    return (
        ("opcode", opcode.value),
        ("key", key),
    )


def chk_enter_params(key: str) -> tuple[tuple[str, str], ...]:
    """5002 파라미터: ``opcode``, ``key``.

    7.0.6: ``CommandClient.CheckedEnter()``(``CommandClient.java:101-156``)
    — ``opcode``(``:122``, ``Command.CHK_ENTER.value()`` = 5002, ``:120``)
    와 ``key``(``:124``, ``this.response_.getKey()``) 둘뿐입니다.
    """
    return _keyed_opcode_params(
        KorailNetFunnelOpcode.CHK_ENTER,
        key,
        purpose="chkEnter",
    )


def set_complete_params(key: str) -> tuple[tuple[str, str], ...]:
    """5004 파라미터: ``opcode``, ``key``.

    7.0.6: ``CommandClient.Complete()``(``CommandClient.java:158-199``)
    — ``opcode``(``:178``, ``Command.SET_COMPLETE.value()`` = 5004,
    ``:176``)와 ``key``(``:180``) 둘뿐입니다.
    """
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
    """네이티브 SDK 응답을 코드와 파라미터로 가름.

    7.0.6 원본은 ``Response.Parser(String)``
    (``com/netfunnel/api/Response.java:128-163``, 평문으로 읽힘).

    첫 ``:`` 앞 = 상태 코드, 나머지 = ``&`` 로 갈라 ``name=value`` 쌍
    (``Response.java:129-137``). 원본이 이름으로 알아보는 키는 여덟 개뿐
    입니다 — ``key``(``:139``), ``utime``(``:141``), ``ip``(``:143``),
    ``port``(``:145``), ``ttl``(``:147``), ``tps``(``:149``),
    ``nwait``(``:151``), ``nnext``(``:153``) — 그리고 ``=`` 가 없거나
    조각이 둘 미만이면 **조용히 버립니다**(``:138``). 이 함수는 대신 모든
    쌍을 :attr:`KorailNetFunnelToken.params` 에 담아 둡니다.

    ``ip``/``port`` 는 :func:`~korail_mobile_api.netfunnel_safety.korail_netfunnel_node_url`
    을 통과시킵니다 — 풀 밖 호스트는 여기서 예외.
    """
    head, separator, tail = body.strip().partition(":")
    if not separator or not head.isdigit():
        raise KorailNetFunnelError(
            None,
            "KORAIL NetFunnel response was not the native SDK's "
            "'<code>:<params>' form; a 'NetFunnel.gRtype=...' body would mean "
            "the server answered the JavaScript dialect, which this app's own "
            "parser (com/netfunnel/api/Response.java:129-137) cannot read "
            "either",
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
    """다음 chkEnter 까지 잘 시간.

    7.0.6: ``Response.getTTL(int max, int min)``
    (``com/netfunnel/api/Response.java:59-66``, clamp 본문 ``:61-65``)에
    네 호출부가 모두 ``(getProperty().getMaxTTL(), 1)`` 을 넘겨
    (``Netfunnel.java:519,634,736,790``) 결과적으로 clamp(1, 30) 이
    됩니다 — 자세한 갈래는 위 :data:`MAX_TTL_SECONDS` 주석 참고.
    """
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

        키 없는 BYPASS(300)·ExpressNumber(303)는 놓을 것이 없으므로 즉시 리턴.
        7.0.6 도 같습니다 — ``CommandClient.Complete()`` 가 본문 맨 앞에서
        ``response == null || response.getKey().length() < 1`` 이면 로그만
        남기고 ``return`` 합니다(``com/netfunnel/api/CommandClient.java:161-165``).
        ``CheckedEnter()`` 에도 같은 가드가 있습니다(``:104-108``).
        그 외의 키 없는 토큰
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

        해제는 양쪽 경로에서 일어남 — 7.0.6 의 실제 연결점은
        ``ScreenViewModel.withNetFunnel``(``ui/screen/common/ScreenViewModel.java:1719``)
        이고, 그 종료 헬퍼가 성공/실패 분기 밖에서 무조건
        ``Netfunnel.getGlobalInstance(nodeId).End()`` 를 부른다(``:893``,
        전체 분기는 ``:857-896``). 해제가 감싼 블록보다 먼저인지 나중인지는
        그 지점의 코틀린 코드가 디컴파일되지 않아(``JadxOverflowException``)
        PROTECTED 다. 본문 성공 시 해제 실패는 예외, 본문 실패 시 해제 실패는
        note 로 붙임.
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
    """열차조회 액션 선택.

    7.0.6 대응 분기는 ``TrainScheduleViewModel.java:5219-5235`` 입니다 —
    ``getRunDateMap()`` 에서 출발일(``getYyyyMMdd()``, ``:5220``)의
    ``RunDateOutItem`` 을 꺼내(``:5224``) ``isPeakSeason()`` 으로 갈라
    ``:5227``/``:5229`` 의 보호된 액션 id 문자열을 고르고, 그것을
    ``withNetFunnel(str, ...)``(``:5244``)에 넘깁니다.

    ``isPeakSeason`` 은 서버 달력 데이터입니다 — 7.0.6 에서는
    ``RunDateOutItem.isPeakSeason()``(``network/model/RunDateOutItem.java:516-523``)
    이 응답 필드 ``bizDdStgCd``(``:517``)를 어떤 코드값과 견줍니다(비교
    자체는 AppSuitLinker 뒤라 그 코드값은 PROTECTED).
    달력을 아직 받지 않았으면 ``runDateOutItem == null`` 이 되어
    비-성수기 갈래로 갑니다(``TrainScheduleViewModel.java:5225``,
    ``:5231-5234``) — 즉 ``peak_season=False`` 입니다.

    이 함수는 날짜가 아니라 플래그를 받음.
    """
    return (
        KorailNetFunnelAction.PEAK_SEASON_INQUIRY
        if peak_season
        else KorailNetFunnelAction.INQUIRY
    )
