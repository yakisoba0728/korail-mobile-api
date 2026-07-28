"""NetFunnel 가상 대기열(``nf.letskorail.com``).

앱은 조회·예약·결제·예약목록 경로에 대기열을 물려 두었고 성수기 조회 전용
액션(``act_8_2``)까지 따로 가지고 있습니다. 이 모듈은 그 줄을 서는 방법이며
**기본값은 꺼짐**입니다
(:attr:`~korail_mobile_api.config.KorailConfig.netfunnel_enabled`).

KORAIL 은 자바스크립트 방언을 쓰지 않습니다
============================================
``nf.letskorail.com`` 은 KORAIL 과 SRT 를 함께 받지만 두 앱이 심은 SDK 가 다릅니다.
SRT 는 WebView 위의 ``netfunnel.js`` 라 ``&nfid=0&prefix=…&js=yes&<epochMillis>`` 를
보내고 ``NetFunnel.gControl.result='5002:200:key=…'`` 같은 자바스크립트 대입문을
받습니다. KORAIL 은 STCLab 의 **네이티브 안드로이드 SDK**(``T6``/``U6`` 패키지)를
심었고 그 어느 것도 보내지 않습니다. 차이는 넷입니다.

1. **``js``·``nfid``·``prefix``·꼬리 epoch 이 없습니다.** ``T6/d.java`` 는
   ``U6.a.addParam`` 을 두세 번 부를 뿐이고(``:30-31``, ``:54-55``, ``:78-79``,
   ``:99-101``), ``U6/a.java`` 가 ``URLEncodedUtils.format(params, "utf-8")`` 로
   붙이므로 쿼리는 추가된 순서 그대로입니다.
2. **``sid``/``aid`` 는 5101 에만 실립니다.** ``GetTidCacekedEnter``
   (``T6/d.java:99-101``)만 둘을 넣고 ``CheckedEnter``(``:54-55``)는 넣지 않습니다 —
   5002 가 둘을 싣는 JS 방언과 반대이며, 5002 와 5004 는 모두 ``opcode``+``key``
   뿐입니다.
3. **``ttl`` 은 되돌려 보내지 않습니다.** ttl 은 얼마나 잘지 정하는 데만
   쓰고(``T6/g.java:462``, ``:467`` 의 ``Thread.sleep``) 전선에는 올리지 않는 순수한
   클라이언트 힌트입니다.
4. **응답은 ``<code>:<params>`` 이지 ``<rtype>:<code>:<params>`` 가 아닙니다.**
   ``T6/i.java:36-43`` 은 첫 ``:`` 앞을 상태 코드로 파싱하므로 JS 방언의
   ``5002:200:key=…`` 를 먹이면 코드를 5002 로 읽습니다. 서버도 ``js`` 없는 요청에는
   ``200:key=…&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=…`` 로만 답합니다.

진입 순서는 5101 → 5002 → 5004 입니다
=====================================
**5101 이 주는 키는 들어갈 표이지 완료할 수 있는 세션이 아닙니다.** 그대로
``setComplete`` 에 보내면 ``503:msg="Wrong Server ID"`` 로 거부됩니다(``sid``/``aid``
를 붙여도 마찬가지입니다). ``chkEnter`` 가 발급한 키만 완료할 수 있고, ``chkEnter``
는 더 짧은 새 키를 줍니다::

    5101  -> 200:key=<252자 hex>&nwait=0&…
    5002  -> 200:key=<다른, 더 짧은 키>&…
    5004  -> 200:key=&nwait=0&…&chk_enter_cnt=0&…

즉 매 단계의 키가 앞 키를 **대체**하며(``T6/d.java`` 는 응답 객체 하나를 모든 opcode
가 덮어쓰고 ``Complete()`` 는 마지막 키를 보냅니다 — ``:61``, ``:79``, ``:107``),
:meth:`KorailNetFunnelClient.acquire` 는 5101 이 대기 없이 200 을 줘도 5002 를 반드시
거칩니다. ``T6/g.java`` 의 폴 루프를 글자 그대로 읽으면 5101 이 200 일 때 5002 없이
완료하지만 실제 서버는 그 키를 완료해 주지 않습니다 — :data:`NOT_COMPLETABLE_CODE`
가 그 코드에 이름을 붙여 둔 이유입니다.

대기열은 풀이고 세션은 그중 한 노드에 삽니다
=============================================
``nf.letskorail.com`` 은 진입 호출을 분산하는 **정문**입니다. 세션을 완료할 수 있는
곳은 진입이 떨어진 노드뿐이고, 모든 응답이 그 노드를 ``ip``/``port`` 로 알려
줍니다(``T6/i.java:50-53``). 앱도 그 이름을 따라 URL 을 다시 만듭니다
(``T6/d.makeURL``, ``T6/d.java:17-19``. ``host_notmodify`` 는 기본 false 이며
``T6/h.java:43`` 이후 아무도 켜지 않습니다).

============ ============================================================
``5101``     **정문**(``config.netfunnel_url``). 분산이 정문의 일이고,
             가리킬 앞선 응답도 없습니다.
``5002``     앞 응답이 가리킨 **노드**. :class:`KorailNetFunnelToken` 의
             ``node`` 가 그것을 나르고 키와 똑같이 대체됩니다.
``5004``     같은 노드 — 놓아줄 세션을 발급한 그 노드.
============ ============================================================

**따르되 믿지는 않습니다.** 서버가 지목한 호스트는 대기열 자신의
풀(``rnf<1-99>.letskorail.com`` 또는 정문, https, 443)만 허용하고 그 밖은 **하드
에러**입니다. 규칙과 근거는
:func:`~korail_mobile_api.safety.korail_netfunnel_node_url` 에 있습니다.

``follow_redirects`` 는 ``False`` 입니다. HTTP 30x 는 ``ip``/``port`` 지목과 다른
메커니즘이라 같은 허용을 받지 않습니다. ``AliveNotice``(5003)도 구현하지 않습니다 —
보이는 대기실 팝업을 살려 두는 용도이고(``T6/g.java:517-527``) 이 라이브러리는 팝업을
그리지도, 한 번의 작업보다 오래 슬롯을 쥐지도 않습니다.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
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
    KorailQueueRejectedError,
    KorailTransportError,
)
from .safety import (
    assert_korail_netfunnel_opcode_origin,
    assert_korail_netfunnel_origin,
    assert_netfunnel_request,
    korail_netfunnel_node_url,
)


# The status codes, read off ``T6/a.java`` — and off ``analysis/apktool/smali/
# T6/a.smali`` where jadx substituted unrelated named constants for the numbers.
# The smali is the authority for the 3xx/5xx values: ``const/16 v2, 0x12c``
# through ``0x12f`` at :228-281 give TsBypass/TsBlock/TsIpBlock/TsExpressNumber
# = 300/301/302/303, and ``const/16 v2, 0x1f6`` at :319 gives TsErrorAComplete =
# 502. Success/Continue/ContinueDebug are ``0xc8``/``0xc9``/``0xca`` at :510-574.
#
# These are byte-for-byte the values SRT's ``netfunnel.js`` declares, which is
# the evidence that the two apps embed two SDKs for ONE product.
SUCCESS_CODE = "200"
BYPASS_CODE = "300"
#: 통과. 200 은 키를 발급하고, 300 은 대기열을 건너뛴 것이라 키가 없습니다.
SUCCESS_CODES = frozenset({SUCCESS_CODE, BYPASS_CODE})
#: 아직 대기 중 — ``T6/g.java:451`` 이 정확히 이 둘에서만 루프를 돕니다.
CONTINUE_CODES = frozenset({"201", "202"})
#: ``TsErrorAComplete``. setComplete 에서만 받아들입니다. 그것이 왜 추론인지는
#: :func:`parse_set_complete_response` 참조.
ALREADY_COMPLETE_CODE = "502"
#: 이 호스트가 소유하지 않은 세션을 ``setComplete`` 로 놓으려 할 때 서버가
#: 주는 답. ``msg="Wrong Server ID"`` 는 서로 다른 두 원인을 덮고 전선으로는
#: 구분되지 않아 여기 이름을 붙여 두었습니다.
#:
#: 1. 키가 완료 가능한 세션이 아닙니다 — 실제로는 ``chkEnter`` 가 발급한 키
#:    대신 5101 표를 보낸 경우입니다. ``sid``/``aid`` 를 붙여도 소용없습니다.
#:    표는 세션이 아닙니다.
#: 2. 키는 세션이 맞는데 요청이 엉뚱한 대기열 노드에 닿았습니다. 이때 메시지는
#:    글자 그대로입니다 — 질문받은 풀 구성원에게 그런 세션이 없습니다. 5004 를
#:    :attr:`KorailNetFunnelToken.node` 로 보내는 이유입니다.
#:
#: 이 코드는 **거부**하며 502 와 나란히 받아들이지 않습니다. "놓였다"고 치는
#: 것이 슬롯이 조용히 새는 방식 그 자체입니다.
NOT_COMPLETABLE_CODE = "503"
#: ``TsBlock``/``TsIpBlock``. 대기실이 우리를 거부했다는 뜻이고, 대기실이
#: 고장 났다는 것과는 다른 사실입니다 — ``T6/g.d.isBlocking()``
#: (``T6/g.java:892-894``)이 이 둘에 전용 술어를 주며, 세 줄 아래의
#: ``isError()`` 와 구분됩니다. 그래도 둘 다 예외가 됩니다. 거부는 대기가
#: 아니고, 통과가 아니면서 실패도 아닌 것은 대기뿐이기 때문입니다. 숫자 코드를
#: 읽지 않고도 구분할 수 있도록
#: :class:`~korail_mobile_api.errors.KorailQueueRejectedError` 로 올립니다.
#:
#: ``TsExpressNumber``(303)는 일부러 여기 넣지 않았습니다. 앱은 그것을 성공으로
#: 셉니다(``T6/g.d.isSuccess()``, ``:909`` 가 ``ExpressNumber`` 를 포함). 입장
#: 허가를 거부로 접어 넣는 것보다 일반 오류 경로에 두는 편이 낫습니다.
QUEUE_REJECTED_CODES = frozenset({"301", "302"})

# The ttl clamp, ours copied from the app's. ``T6/g.java:462`` asks
# ``getResponse().getTTL(getProperty().getMaxTTL(), 1)`` and ``T6/i.java:175-181``
# implements that as "cap at max_ttl, floor at 1". ``max_ttl`` defaults to 30
# (``T6/h.java:40``) and nothing in this app overrides it — note that this is NOT
# the JS bundle's ``TS_MAX_TTL = 5`` that the SRT client clamps to. The floor
# matters as much as the cap: a ttl of 0 would otherwise turn the loop into a
# spin.
MAX_TTL_SECONDS = 30
MIN_TTL_SECONDS = 1

# HARD caps on the polling loop. These are OURS, not the app's: ``T6/g.java``
# polls forever (``while (true)`` at :449) behind a waiting-room dialog a human
# can close, and this library has no such escape hatch. A queue is a wait, not a
# retry, and this library's standing position is that it never retries on its own
# initiative — so an engaged queue must end in bounded time either way.
# Whichever limit is reached first ends the wait with
# :class:`~korail_mobile_api.errors.KorailNetFunnelError`.
QUEUE_POLL_LIMIT = 20
QUEUE_WAIT_LIMIT_SECONDS = 60.0


@dataclass(frozen=True)
class KorailNetFunnelToken:
    """파싱된 NetFunnel 응답 하나.

    ``key`` 는 대기열 슬롯의 식별자이며 후속 요청이 슬롯을 가리키는 유일한 수단입니다 —
    ``chkEnter`` 와 ``setComplete`` 는 그것 말고 아무것도 보내지 않습니다
    (``T6/d.java:54-55``, ``:78-79``).

    토큰은 세션 하나가 아니라 **응답 하나**입니다. 응답마다 키가 앞 키를 대체하므로 여기
    든 키는 바로 다음 요청에만 쓸 수 있습니다. 5101 표는 ``chkEnter`` 가 소진하고, 201
    폴마다 키가 다시 발급됩니다. :meth:`KorailNetFunnelClient.acquire` 가 돌려주는 최신
    토큰만 ``setComplete`` 가 받습니다.

    ``node`` 는 응답한 대기열 노드의 origin — 응답의 ``ip``/``port`` 를 ``https://`` 꼴로
    만든 것이며 :func:`~korail_mobile_api.safety.korail_netfunnel_node_url` 이 풀 이름
    규칙으로 이미 검사했습니다. 아무 노드도 가리키지 않은 응답에서는 ``""`` 이고 그것은
    정문을 뜻합니다. 키는 어느 슬롯인지, 노드는 그 슬롯이 어디 사는지를 말합니다. 맞는
    키를 틀린 노드에 보내면 ``503:msg="Wrong Server ID"`` 라 둘은 함께 다닙니다.
    """

    action: str
    key: str
    code: str
    params: dict[str, str] = field(default_factory=dict)
    node: str = ""

    @property
    def wait_count(self) -> int:
        """``nwait`` — 앞에 몇 명이 서 있는지. 대기열이 한가하면 0 입니다."""
        raw = self.params.get("nwait", "")
        return int(raw) if raw.isdigit() else 0


def _netfunnel_url(netfunnel_url: str, params: Sequence[tuple[str, str]]) -> str:
    """대기열 URL 하나를 조립하면서 가드를 통과시킵니다.

    가드는 인코딩 전의 순서 있는 쌍에 대해 돌기 때문에 :mod:`korail_mobile_api.safety` 의
    opcode 별 계약이 파라미터 이름과 값뿐 아니라 **순서**까지 검사합니다. 쿼리 문자열을
    다시 파싱하지 않습니다.

    origin 은 opcode 별로 가드합니다. 핸드셰이크가 호스트를 넘나들기 때문입니다 — 5101 은
    정문만, 5002 와 5004 는 대기열 노드도 됩니다. 요청 계약을 먼저 단언하므로 그 아래에서
    읽는 opcode 는 이미 가드가 보증한 값입니다.
    """
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
    """``opcode``, ``sid``, ``aid`` — 그 순서로.

    ``T6/d.java:99-101`` 이 정확히 셋만 넣고, ``U6/a.addParam`` 은 ``ArrayList`` 에
    덧붙이며(``U6/a.java:57-63``) ``URLEncodedUtils.format`` 이 그 순서대로 훑습니다.
    그래서 순서는 앱의 것입니다.
    """
    return (
        ("opcode", KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value),
        ("sid", service_id),
        ("aid", str(action)),
    )


def chk_enter_params(key: str) -> tuple[tuple[str, str], ...]:
    """``opcode``, ``key``. ``sid`` 도 ``aid`` 도 ``ttl`` 도 없습니다.

    ``T6/d.java:54-55``. 자바스크립트 방언과 가장 눈에 띄게 갈리는 지점입니다 — 그쪽 5002
    는 서비스/액션 쌍을 싣고 직전 201 의 ttl 을 되돌려 보냅니다.
    """
    if not key:
        raise ValueError("chkEnter requires the key the queue issued")
    return (
        ("opcode", KorailNetFunnelOpcode.CHK_ENTER.value),
        ("key", key),
    )


def set_complete_params(key: str) -> tuple[tuple[str, str], ...]:
    """``opcode``, ``key`` — "끝났으니 슬롯을 놓아 달라"(``T6/d.java:78-79``).

    보내지 않으면 서버가 시간 초과로 걷어 갈 때까지 자리가 잡혀 있습니다. 앱도 자동으로
    놓습니다. ``NetfunnelDao.runRunner()`` 가 ``T6.g.END()`` 를 부르고
    (``com/korail/talk/network/NetfunnelDao.java:41``) 그 호출은 ``BaseDaoHelper`` 의
    ``onPostExecute``(``:105-107``)에서 나오므로 성공 경로와 실패 경로 양쪽에서
    실행됩니다.
    """
    if not key:
        raise ValueError("setComplete requires the key whose slot is released")
    return (
        ("opcode", KorailNetFunnelOpcode.SET_COMPLETE.value),
        ("key", key),
    )


def build_get_tid_chk_enter_url(
    netfunnel_url: str,
    *,
    action: str,
    service_id: str = KORAIL_NETFUNNEL_SERVICE_ID,
) -> str:
    """5101 URL — "``action`` 줄에 세워 달라".

    ``netfunnel_url`` 은 **정문**이어야 합니다. 진입 호출이라 아직 노드가 없고, 그 분산이
    정문의 일입니다.
    """
    return _netfunnel_url(
        netfunnel_url,
        get_tid_chk_enter_params(action, service_id=service_id),
    )


def build_chk_enter_url(netfunnel_url: str, *, key: str) -> str:
    """5002 URL — "이제 들어가도 되나".

    ``netfunnel_url`` 은 세션을 발급한 **노드**입니다(아직 아무 응답도 노드를 가리키지
    않았다면 정문). 풀 밖의 노드는 가드가 거부합니다.
    """
    return _netfunnel_url(netfunnel_url, chk_enter_params(key))


def build_set_complete_url(netfunnel_url: str, *, key: str) -> str:
    """5004 URL — "끝났으니 슬롯을 놓아 달라".

    ``netfunnel_url`` 은 세션을 발급한 **노드**입니다. 대신 정문으로 보내면, 분산기가 마침
    그 노드로 되돌려 주지 않는 한 ``503:msg="Wrong Server ID"`` 가 돌아옵니다.
    """
    return _netfunnel_url(netfunnel_url, set_complete_params(key))


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
    """네이티브 SDK 응답을 코드와 파라미터로 가르기만 합니다. 판정은 하지 않습니다.

    ``T6/i.Parser``(``T6/i.java:35-63``)를 그대로 옮겼습니다. 첫 ``:`` 앞이 상태 코드,
    나머지는 ``&`` 로 갈라 ``name=value`` 쌍이 됩니다. 성공의 정의는 어느 요청에 대한
    응답이냐에 따라 다르므로 상태 판정은 호출자마다 따로 합니다.

    앱은 값 쪽을 ``split("=")`` 하고 ``[1]`` 을 취해서 ``=`` 가 든 값을 잘라 먹지만,
    여기서는 한 번만 갈라 그런 값도 온전히 남습니다. 알려진 NetFunnel 파라미터 중 ``=``
    를 담는 것은 없습니다.

    **여기서 내리는 유일한 판단은 상태가 아니라 라우팅입니다.** ``ip`` 와 ``port`` 는 어느
    노드가 답했는지를 말하고 후속 opcode 는 그리로 가야 하므로, 파싱 시점에
    :func:`~korail_mobile_api.safety.korail_netfunnel_node_url` 을 통과시킵니다. 풀 밖
    호스트를 가리킨 응답은 여기서
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 파서에서 하면 모든 파싱
    함수의 모든 호출자가 검사를 받고, 검증되지 않은 ``node`` 를 가진 토큰을 얻을 수 있는
    경로가 남지 않습니다.
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
    # A BYPASS carries no key: ``TsBypass`` means the queue was skipped entirely,
    # so there is no place in line to identify. ``T6/g.d.isSuccess()``
    # (``T6/g.java:909``) counts Bypass as a success and the caller simply
    # proceeds. A 200 without a key is a different matter and stays refused — a
    # pass is identified BY its key, and every follow-up request we could make
    # consists of nothing but that key.
    if not token.key and token.code != BYPASS_CODE:
        raise KorailNetFunnelError(
            None,
            "KORAIL NetFunnel response did not include a non-empty key",
            raw=body,
        )


def parse_queue_response(body: str, *, action: str) -> KorailNetFunnelToken:
    """5101/5002 응답을 읽습니다. "아직 대기 중"도 포함합니다.

    통과(200/300)든 대기(201/202)든 토큰을 돌려주고, 둘의 구분은 호출자가
    :func:`is_queued` 로 합니다. 그 밖은 예외입니다 — 301 과 302 는
    :class:`~korail_mobile_api.errors.KorailQueueRejectedError`, 나머지는
    :class:`~korail_mobile_api.errors.KorailNetFunnelError`.

    대기 응답은 키를 되울려 줄 의무가 없습니다. 이미 하나 쥐고 있고, 키가 없다고 거절하면
    그저 줄을 서 있을 뿐인 작업을 중단시키게 됩니다.
    """
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


def parse_set_complete_response(
    body: str,
    *,
    action: str,
) -> KorailNetFunnelToken:
    """5004 응답을 읽습니다. 200(놓임)과 502(이미 완료)를 받아들입니다.

    **502 를 받아들이는 것은 추론입니다.** 앱은 이에 대해 말이 없습니다 —
    ``T6/d.Complete()``(``T6/d.java:69-88``)는 응답을 보지도 않고 ``execute()`` 뒤 상태를
    지웁니다. 호출자의 질문은 "내 슬롯이 놓였는가"이고 200 과 ``TsErrorAComplete`` 는 둘
    다 그렇다고 답합니다.

    **응답에 키가 없어도 되고, 성공한 해제는 키를 보내지 않습니다.** 해제 성공은
    ``200:key=&nwait=0&…&chk_enter_cnt=0&…`` 처럼 빈 ``key=`` 로 옵니다 — 잘린 본문이
    아니라 슬롯이 사라졌다는 서버의 말입니다. 그래서 여기서는 :func:`_require_pass_key`
    를 돌리지 않습니다. 빈 키는 5101/5002 에서만 실패이고 거기서는 키가 응답의 전부입니다.

    :data:`NOT_COMPLETABLE_CODE` 에만 따로 메시지를 붙인 것은 서버 문구가 원인을 잘못
    가리키기 때문입니다. 나머지는 일반 메시지를 씁니다.
    """
    token = parse_netfunnel_body(body, action=action)
    if token.code == NOT_COMPLETABLE_CODE:
        raise _queue_failure(
            token,
            "KORAIL NetFunnel setComplete refused this key as a session THIS "
            "host owns; the server calls that 'Wrong Server ID' and means one "
            "of two things — either the key was never exchanged for a session, "
            "which is what chkEnter (5002) does (a slot entered as 5101 -> 5002 "
            "releases with the key 5002 issued, never with the 5101 ticket), or "
            "the request went to a queue node that did not issue this session, "
            "in which case the message is literal and the fix is to send it to "
            "the ip/port the reply named",
            body,
        )
    if token.code not in {SUCCESS_CODE, ALREADY_COMPLETE_CODE}:
        raise _queue_failure(
            token,
            "KORAIL NetFunnel setComplete did not release the queue slot",
            body,
        )
    return token


def is_queued(token: KorailNetFunnelToken) -> bool:
    """대기열이 "나중에 다시 오라"고 했는지(Continue/ContinueDebug)."""
    return token.code in CONTINUE_CODES


def queue_wait_seconds(token: KorailNetFunnelToken) -> int:
    """다음 ``chkEnter`` 까지 잘 시간. 앱이 자르는 대로 자릅니다.

    ``T6/i.java:175-181`` 의 ``max_ttl=30``, ``min=1`` — :data:`MAX_TTL_SECONDS` 참조.
    이 값은 서버로 돌아가지 않습니다. 자바스크립트 방언과 달리 네이티브 SDK 는 ttl 을
    전적으로 클라이언트에만 둡니다.
    """
    raw = token.params.get("ttl", "")
    ttl = int(raw) if raw.isdigit() else 0
    return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


class KorailNetFunnelClient:
    """대기열 전용 클라이언트. 대기열 자신의 호스트에만 고정되고 폴링에 상한이 있습니다.

    :class:`~korail_mobile_api.http.KorailHttpClient` 와 **일부러 분리했습니다**. 그쪽은
    ``assert_korail_origin`` 으로 ``smart.letskorail.com`` 에 고정되고 그대로 있어야 하며,
    이쪽은 대기열 정문과 대기열 노드의 ``/ts.wseq`` 밖으로 나갈 수 없습니다. 어느 쪽도
    상대의 origin 에 닿는 데 쓸 수 없고, 모듈 docstring 이 설명하는 풀은 대기열 호스트만의
    사정이라 API 호스트의 단일 origin 보장은 그대로입니다.
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
        # The default-off guarantee, enforced at construction rather than at
        # send. A caller who has not set netfunnel_enabled does not get an object
        # that might make a queue request later; they get a refusal here, with
        # nothing constructed and no socket in existence. See
        # KorailConfig.netfunnel_enabled for why the default is what it is.
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
            # A queue reply names the node that owns the session in
            # ``ip``/``port`` and we follow that (see the module docstring),
            # but only into the pool's own naming and only via a URL this
            # client builds. An HTTP 30x is a different mechanism and gets no
            # such allowance.
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
        """5101 — **정문**에서 ``action`` 의 표를 받습니다.

        대기 토큰이 나올 수 있습니다. 여기서 받은 키는 아직 세션이 아닙니다. :meth:`check` 가
        그것을 세션으로 바꿔 주고, ``setComplete`` 는 이 키를 거부합니다
        (:data:`NOT_COMPLETABLE_CODE`). 놓아줄 수 있는 슬롯이 필요하면 교환까지 수행하는
        :meth:`acquire` 를 쓰면 됩니다.

        무조건 ``config.netfunnel_url`` 로 가는 유일한 opcode 입니다. 정문이 풀 전체로
        분산하는 호출이고, 그 응답이 나머지 세션이 속한 노드를 가리킵니다.
        """
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
        """5002 — ``key`` 로 입장하거나 다시 묻습니다. ``node`` 에서.

        대기 토큰이 나올 수 있습니다. 같은 opcode 의 두 국면입니다. 첫 호출은 5101 표를 완료
        가능한 세션으로 바꾸고, 이후 호출은 직전 201 이 발급한 키로 다시 묻습니다. 어느
        쪽이든 응답의 키가 ``key`` 를 대체하므로 호출자는 넘긴 토큰이 아니라 받은 토큰을 들고
        가야 합니다.

        ``node`` 는 앞 응답이 가리킨 origin 입니다 — :attr:`KorailNetFunnelToken.node` 를
        그대로 넘기면 됩니다. 노드가 없는 호출자를 위해 정문이 기본값이고, 그것이 옳은 경우는
        아직 아무 응답도 노드를 가리키지 않았을 때뿐입니다. :meth:`acquire` 는 여기 올 때 이미
        노드를 압니다.
        """
        body = self._get(
            build_chk_enter_url(node or self.config.netfunnel_url, key=key)
        )
        return parse_queue_response(body, action=str(action))

    def release(self, token: KorailNetFunnelToken) -> None:
        """5004 — 슬롯을 그 **노드**에서 놓습니다. 놓이지 않으면 예외입니다.

        요청은 세션을 발급한 ``token.node`` 로 갑니다. 정문은 그 세션의 주인이 아니라서,
        분산기가 마침 주인 노드로 되돌려 주지 않는 한 ``503:msg="Wrong Server ID"`` 로
        답합니다. 아무도 노드를 가리키지 않은 토큰은 정문으로 갑니다 — 호스트가 지목되지
        않았을 때의 ``T6/d.makeURL`` 동작 그대로이며, 거부에 대한 대체 경로가 아닙니다. 거부된
        호스트는 여기 오기 훨씬 전에 예외가 됩니다.

        실패를 삼키지 않고 **올립니다**. 보낼 수 없는 해제는 소리를 내야 합니다. 조용히
        실패하면 슬롯이 새고, 샌 슬롯은 아무 신호도 남기지 않습니다.

        키가 없는 토큰은 우회(300)이고 놓을 것이 없으므로 아무것도 보내지 않고 돌아옵니다 —
        ``T6/d.Complete()`` 가 짧게 끊는 조건과 같습니다(``T6/d.java:70-73``,
        ``getKey().length() < 1``). 다만 그 지름길은 우회에만 허용합니다. 키 없음이 정당한
        상태인 코드는 하나뿐이고, 다른 무키 토큰에까지 조용한 경로를 열어 주면 요청이 거부되는
        것도 아니고 아예 만들어지지 않는 쪽으로 슬롯이 샙니다.
        """
        if not token.key:
            if token.code == BYPASS_CODE:
                return
            raise KorailNetFunnelError(
                token.code or None,
                "KORAIL NetFunnel slot cannot be released because its token "
                "carries no key, and only a bypass (300) is allowed to; the "
                "slot is held until the server times it out",
            )
        body = self._get(
            build_set_complete_url(
                token.node or self.config.netfunnel_url,
                key=token.key,
            )
        )
        parse_set_complete_response(body, action=token.action)

    def acquire(self, action: str) -> KorailNetFunnelToken:
        """표를 받고, 그것으로 입장하고, 들어갈 때까지 상한 안에서 폴링합니다.

        전체 순서는 5101 → 5002 이지 5101 단독이 아니며, 두 호스트에 걸칩니다::

            enter(action)                     # 5101, 정문
            check(action, key, node=node)     # 5002, 정문이 가리킨 노드
            ...                               # 201/202 인 동안 5002 반복
            -> setComplete 가 받아 줄 키와 노드를 가진 토큰

        5002 는 조건 없이 보냅니다. 5101 이 ``nwait=0`` 으로 200 을 줘도 그것은 표일 뿐이고,
        그 표를 놓으려 하면 :data:`NOT_COMPLETABLE_CODE` 로 실패합니다. 예외는 우회(300)뿐이며
        설 줄이 없으니 키도 없고 교환할 것도 없습니다.

        통과 토큰(200 또는 300)을 돌려주며 그 키는 서버가 마지막으로 발급한 것입니다. 호출자는
        반드시 이 토큰을 놓아야 하고 앞선 토큰을 놓으면 안 됩니다. 키를 되울리지 않은 201 은
        마지막 키를 그대로 둡니다 — 대기는 취소가 아닙니다.

        노드도 같은 방식으로 대체됩니다. 돌려주는 토큰은 어떤 응답이든 마지막으로 가리킨
        노드를 싣고 있어서 :meth:`release` 가 세션의 주인 호스트에 닿습니다. 노드를 말하지
        않은 응답은 직전 노드를 그대로 두고, 우회는 세션이 없으니 노드도 없습니다.

        :data:`QUEUE_POLL_LIMIT` 번 폴링하거나 :data:`QUEUE_WAIT_LIMIT_SECONDS` 초가 지나도록
        대기열이 놓아 주지 않으면 :class:`~korail_mobile_api.errors.KorailNetFunnelError`
        입니다. 그 포기는 슬롯을 서버의 시간 초과에 맡깁니다 — :meth:`slot` 은 토큰을 받은 적이
        없어 놓을 것이 없고, 손으로 놓고 싶은 호출자를 위해 현재 키를 예외의 ``raw`` 에 실어
        줍니다.
        """
        token = self.enter(action)
        if not token.key:
            # A bypass. No ticket was issued, so there is nothing to exchange
            # and nothing to release — T6/d.Complete() short-circuits on the
            # same emptiness (T6/d.java:70-73). There is no session, so there is
            # no node either, and `release` never gets far enough to want one.
            return token
        # The key and the node ride alongside the token because a 201 is allowed
        # to omit either: we must not send an empty key to the next chkEnter, and
        # we must not lose the node a previous reply named just because this one
        # was silent about routing.
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
                # The node is put back on the token rather than left in this
                # loop's local, so the caller holds one object that says both
                # which slot it is and where that slot lives. The key is NOT
                # written back: a keyless pass is a bypass, and giving it the
                # previous key would send it to a setComplete it has no business
                # reaching.
                return replace(token, node=node)

    @contextmanager
    def slot(self, action: str) -> Iterator[KorailNetFunnelToken]:
        """한 작업이 도는 동안 대기열 슬롯을 쥐었다가 놓습니다.

        ``with client.slot(KorailNetFunnelAction.INQUIRY): ...``

        해제는 **양쪽 경로**에서 일어납니다. 앱도 그렇게 합니다(``BaseDaoHelper.java:105-107``
        이 ``onPostExecute`` 에서 부르므로 게이트된 호출이 실패했든 아니든 실행됩니다). 두
        경로는 *해제 실패*를 얼마나 크게 말하느냐만 다릅니다.

        * 본문이 성공했으면 — 해제 실패는 예외로 **올립니다**. 가릴 다른 것이 없고, 조용히
          새는 슬롯이야말로 이 모듈이 막으려는 것입니다.
        * 본문이 실패했으면 — 해제는 여전히 시도하되, 해제 자신의 실패는 호출자의 예외를
          밀어내는 대신 그 예외에 note 로 붙습니다. 호출자에게 필요한 것은 자기 오류이고,
          누수는 감추지 않고 기록만 합니다.
        """
        token = self.acquire(action)
        try:
            yield token
        except BaseException as exc:
            try:
                self.release(token)
            except Exception as release_error:  # 넓게 잡는다: 이유는 docstring 참조
                exc.add_note(
                    "KORAIL NetFunnel slot release also failed and the slot may "
                    f"be held until the server times it out: {release_error}"
                )
            raise
        self.release(token)


#: 어느 액션 id 가 어느 작업을 막는지, 앱이 짝지은 대로. 항목마다 APK 호출
#: 지점이 있습니다.
#:
#: * ``INQUIRY``/``PEAK_SEASON_INQUIRY``/``PRODUCT`` — ``b5/c.java:439`` 의
#:   열차조회 경로가 한 줄에서 셋 중 하나를 고릅니다. 규칙은
#:   :func:`inquiry_action` 참조.
#: * ``RESERVE`` — ``com/korail/talk/ui/inquiry/rir/orr/
#:   DirectInquiryActivity.java:442``, ``:469``, ``:499``(예약대기·일반 예약·
#:   공무원 인증 변형이 모두 ``act_14`` 를 씁니다).
#: * ``PAY`` — ``B6/AbstractC1269e.java:1046`` 과 ``B6/C1270f.java:232``.
#: * ``RESERVED`` — ``com/korail/talk/ui/menu/ReservedTicketActivity.java:553``
#:   의 예약목록 조회.
#: * ``TEST`` — ``com/korail/talk/test/NetfunnelTestActivity.java:54`` 는
#:   ``act_4`` 가 아니라 ``act_8`` 을 씁니다. ``act_4`` 와 ``act_22`` 는
#:   ``K4/g.java:47,50`` 에 선언돼 있지만 APK 안 어느 호출 지점에서도 쓰이지
#:   않습니다. 앱이 선언하므로 노출은 하되, 이 표에 없다는 것이 앱에서 아무도
#:   그것들에 닿지 않는다는 진술입니다.
KORAIL_NETFUNNEL_GATED_OPERATIONS: dict[str, KorailNetFunnelAction] = {
    "search_trains": KorailNetFunnelAction.INQUIRY,
    "search_product_trains": KorailNetFunnelAction.PRODUCT,
    "reserve": KorailNetFunnelAction.RESERVE,
    "confirm_standby_hold": KorailNetFunnelAction.RESERVE,
    "pay_with_card": KorailNetFunnelAction.PAY,
    "pay_with_fake_card": KorailNetFunnelAction.PAY,
    "get_reservation_history": KorailNetFunnelAction.RESERVED,
}


def inquiry_action(*, peak_season: bool) -> KorailNetFunnelAction:
    """열차조회 액션을 앱이 고르는 방식대로 고릅니다.

    ``b5/c.java:439`` 는 조건식 하나입니다::

        request instanceof ProductTrainInquiryRequest
            ? NETFUNNEL_ACTION_PRODUCT_ID                       // act_6
            : isPeakSeason(getCalendarInfo(y0()))
                ? NETFUNNEL_ACTION_ID_PEAKSEASON                // act_8_2
                : NETFUNNEL_ACTION_ID                           // act_8

    ``MainBookingActivity.java:749`` 와 ``OldMainBookingActivity.java:321`` 이 간편구매
    흐름에서 성수기 쪽 절반을 되풀이합니다. 즉 선택은 *출발일자*마다, 요청이 나가기 전에
    클라이언트에서 이뤄집니다.

    **``isPeakSeason`` 은 달력 규칙이 아니라 서버 데이터입니다.**
    ``S4/C0805e.java:116-121`` 은 ``f4891k`` 로 답하는데, 그것은 ``isPeakSeason()`` 이 참인
    ``RunningCalendar`` 행들로 ``:199-201`` 에서 만든 ``AvailableDates`` 입니다 — 이
    라이브러리가 :meth:`~korail_mobile_api.client.KorailClient.get_train_calendar` 로 이미
    읽는 ``schedule.runDt`` 열차운행달력 응답입니다. 그러니 이것은 *조회*이고 다시 구현할
    것이 없습니다. 달력을 아직 받지 않았으면 앱 자신의 답도 ``false`` 이며(``:117`` 은
    표가 null 이면 false), 그래서 이 함수는 날짜가 아니라 플래그를 받습니다.

    ``act_8`` 과 ``act_8_2`` 는 같은 서비스의 서로 다른 액션이므로 서로 다른 줄입니다.
    부하가 몰릴 때 걸리는 것은 보통 조회 큐이고, 달력을 읽은 호출자는 엉뚱한 줄에서
    기다리는 대신 성수기 줄을 요청할 수 있습니다.
    """
    return (
        KorailNetFunnelAction.PEAK_SEASON_INQUIRY
        if peak_season
        else KorailNetFunnelAction.INQUIRY
    )
