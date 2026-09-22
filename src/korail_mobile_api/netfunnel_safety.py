# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""대기열 호스트로 나가는 것을 제한하는 가드.

:mod:`korail_mobile_api.safety` 와 같은 성격입니다 — 실행 로직이 없고 목록과 단언뿐이며,
:mod:`korail_mobile_api.netfunnel` 의 요청이 나가기 직전에 이 단언들을 통과합니다.
파일만 다릅니다.

나뉘기 전 ``safety.py`` 는 744줄 가운데 294줄을 대기열에 내주고 있었습니다. 메인 API
전송 경계가 무엇을 허용하는지 보려고 그 파일을 여는 사람이, 관계없는 대기열 노드
리다이렉션 규칙을 함께 읽어야 했습니다. 두 호스트는 서로에게 닿을 수 없으므로 두 가드도
함께 놓일 이유가 없습니다.

여기 있는 것은 **별도 호스트**(``nf.letskorail.com``)와 그 노드 풀의 규칙입니다.
메인 API 의 라우트 허용목록과 상태변경 3중 게이트는 :mod:`korail_mobile_api.safety` 에
있습니다.
"""
import re
from collections.abc import Sequence
from urllib.parse import urlsplit

from .constants import (
    KORAIL_NETFUNNEL_PATH,
    KORAIL_NETFUNNEL_SERVICE_ID,
    KORAIL_NETFUNNEL_URL,
    KorailNetFunnelAction,
    KorailNetFunnelOpcode,
)
from .errors import KorailProtocolError


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname

# ---------------------------------------------------------------------------
# NetFunnel queue protocol: one exact query contract per opcode.
#
# Three named contracts for three opcodes on a SEPARATE host (nf.letskorail.com).
#
# 옛 인용 T6/d.java / U6/a.java 는 6.5.0 난독화 이름이고 7.0.6 디컴파일에 그
# 경로가 없습니다. 7.0.6 은 같은 STCLab SDK 를 com/netfunnel/api/ 아래 평문으로
# 담고 있어 세 계약을 전부 다시 짚었습니다 (T6/d → CommandClient,
# U6/a.addParam → http/Client.addParam; 대응 근거는
# korail_mobile_api.netfunnel 머리말의 표 참고).
#
# 각 튜플은 com/netfunnel/api/http/Client.addParam(String, String)
# (http/Client.java:121-127) 호출 순서입니다 — addParam 은 params_ 를
# List<NameValuePair> (http/Client.java:42) 로 들고 :126 에서 add() 하므로
# 순서가 그대로 보존됩니다:
#   5101 GetTidCheckedEnter (CommandClient.java:40-99)    opcode :59, sid :61, aid :63
#   5002 CheckedEnter       (CommandClient.java:101-156)  opcode :122, key :124
#   5004 Complete           (CommandClient.java:158-199)  opcode :178, key :180
# (옛 주석의 "GetTidCacekedEnter" 는 오타였고 7.0.6 의 메서드 이름은
# GetTidCheckedEnter 입니다.)
#
# Absent: no `js`, no `nfid`, no `prefix`, no trailing epoch, no `ttl`.
# Those belong to the JavaScript NetFunnel client that SRT uses.
# KORAIL embeds the native Android SDK (7.0.6: com/netfunnel/api +
# com/netfunnel/api/http — 6.5.0 의 T6/U6 패키지에 해당). 위 세 블록과 5003
# AliveNotice (CommandClient.java:217,:219) 를 합친 네 곳이 SDK 의 addParam
# 호출 전부이고, 그 어디에도 ttl 은 없습니다. 넷째 파라미터 user_data 는 길이가
# 0 이 아닐 때만 붙는데(CommandClient.java:65-68) KORAIL 은 설정하지 않습니다.
#
# 5003 ALIVE_NOTICE, 5105 INIT and 5106 STOP are NOT registered: the first
# keeps a waiting-room popup alive; the other two are administrative and the
# SDK refuses them. 7.0.6 근거는 CommandClient.Stop() (CommandClient.java:253-255)
# 과 CommandClient.Init() (:257-259) — 둘 다 본문이 한 줄이고 즉시
# `throw new CodeException(Code.ErrorNotSupport)` 입니다(Code.ErrorNotSupport =
# 998, Code.java:74). 옛 인용 T6/d.java:115-121 은 그 경로가 없을 뿐 아니라
# 7.0.6 의 :115-121 은 CheckedEnter 안의 setPort/setURL 줄이므로 줄 번호를
# 그대로 옮겨서는 안 됩니다. 5003 은 거절되지 않고 온전히 구현돼 있습니다
# (CommandClient.AliveNotice(), :201-251) — 옛 주석이 "the first keeps a
# waiting-room popup alive" 로 5003 을 나머지 둘과 갈라 둔 것은 맞습니다.
# ---------------------------------------------------------------------------
KORAIL_NETFUNNEL_ROUTES = frozenset({("GET", KORAIL_NETFUNNEL_PATH)})

KORAIL_NETFUNNEL_QUERY_CONTRACTS: dict[str, tuple[str, ...]] = {
    KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value: ("opcode", "sid", "aid"),
    KorailNetFunnelOpcode.CHK_ENTER.value: ("opcode", "key"),
    KorailNetFunnelOpcode.SET_COMPLETE.value: ("opcode", "key"),
}

#: 요청에 슬롯 키를 싣는 opcode. "어느 opcode 에 어느 필드가 있는가"를 코드를
#: 따라가지 않고 읽어서 답할 수 있도록 계약 옆에 데이터로 둡니다.
KORAIL_NETFUNNEL_KEYED_OPCODES = frozenset(
    {
        KorailNetFunnelOpcode.CHK_ENTER.value,
        KorailNetFunnelOpcode.SET_COMPLETE.value,
    }
)

#: ``aid`` 에 나타날 수 있는 액션 id 전부. ``aid`` 가 자유 문자열 필드가 되지
#: 않게 하려고 :class:`~korail_mobile_api.constants.KorailNetFunnelAction` 의
#: 값 집합으로 닫아 둡니다.
#:
#: **"앱이 선언한 여덟 개" 라는 옛 서술은 7.0.6 에서 맞지 않습니다.** 옛 인용
#: ``K4/g.java:43-51`` 은 6.5.0 난독화 이름으로 그 경로가 7.0.6 에 없고,
#: 7.0.6 의 정본 ``NetworkConstants.Netfunnel``
#: (``com/korail/talk/common/NetworkConstants.java:80-99``)이 선언하는 액션
#: 상수는 **일곱 개**입니다 — ``ACTION_ID``(``:88``),
#: ``ACTION_RESERVE_ID``(``:89``), ``ACTION_PAY_ID``(``:90``),
#: ``ACTION_PEAK_SEASON_ID``(``:91``), ``ACTION_PRODUCT_ID``(``:92``),
#: ``ACTION_TEST_ID``(``:93``), ``ACTION_RESERVATION_TICKET_ID``(``:94``).
#: 환불에 해당하는 이름은 없습니다. 그래서 이 집합이 여덟 개인 것은 앱을
#: 따른 결과가 아니라, 이 enum 이 7.0.6 에 대응 상수가 없는
#: :attr:`~korail_mobile_api.constants.KorailNetFunnelAction.REFUND`
#: (``"act_22"``, 6.5.0 기원이며 **미출처**)를 아직 들고 있기 때문입니다.
#: 값별 근거 등급은 :class:`~korail_mobile_api.constants.KorailNetFunnelAction`
#: 의 항목별 주석에 있습니다.
#:
#: "한 번도 부르지 않는 둘" 도 7.0.6 에서는 숫자가 다릅니다 — 선언은 있으나
#: 호출부를 찾지 못한 것이 ``ACTION_PRODUCT_ID``/``ACTION_RESERVATION_TICKET_ID``/
#: ``ACTION_TEST_ID`` 셋입니다. 다만 ``act_*`` 리터럴이 전부 AlienGuard 런타임
#: 복호화라 호출부 귀속 자체가 부분적으로 추론이므로, "없다" 가 아니라
#: "정적으로 찾지 못했다" 로 읽어야 합니다.
#:
#: 넓게 잡는 쪽이 안전한 방향입니다 — 이 집합은 나가는 ``aid`` 를 **제한**할
#: 뿐이고, 여기 없는 값을 보내는 것은 어차피 거절됩니다.
KORAIL_NETFUNNEL_ACTION_IDS = frozenset(
    action.value for action in KorailNetFunnelAction
)

# The key is opaque and server-issued, so it is validated by SHAPE: a non-empty
# run of the characters a NetFunnel key is made of.
#
# THE 512 BOUND IS A CEILING TAKEN FROM A SCAR, NOT A GUESS. The sibling SRT
# implementation bounded the same field at 128 while real keys are 256 characters
# of uppercase hex. Every setComplete therefore failed this check before it was
# sent, and because a failed release was swallowed there, it failed SILENTLY —
# every slot leaked until a live run exposed it. Nothing offline could have
# caught it, which is why the bound here is generous. The release transport
# failure remains visible even though the v7 SDK ignores the 5004 response body.
KORAIL_NETFUNNEL_KEY_RE = re.compile(r"[A-Za-z0-9_.:@~-]{1,512}")

# ---------------------------------------------------------------------------
# THE QUEUE IS A POOL OF NODES, AND FOLLOWING ONE IS NOT OPTIONAL.
#
# `nf.letskorail.com` is a front door that load-balances entry calls.
# The node that issues a session is the only one that can complete it.
# Replies name the owning node in `ip`/`port`. 7.0.6: Response.Parser(String)
# (com/netfunnel/api/Response.java:128-163) 가 `ip` 를 setHost 로(:143-144),
# `port` 를 setPort 로(:145-146) 넣습니다 — 이 패키지는 AlienGuard 가 걸려
# 있지 않아 평문으로 읽힙니다. 옛 인용 T6/i.java:50-53 은 이 클래스의 6.5.0
# 난독화 이름이고 7.0.6 에 그 경로가 없습니다.
#
# THE NATIVE SDK'S OWN DEFAULT DOES NOT FOLLOW THAT REDIRECT. Confirmed
# directly in 7.0.6:
#   - Property.java:23: `private boolean host_notmodify_ = true;` -- the
#     compiled default is true.
#   - CommandClient.makeURL() (CommandClient.java:33-38) only rebuilds the
#     URL from the response's host/port when `!property.isHostNotmodify()`
#     -- i.e. only once host_notmodify has been explicitly turned OFF. Left
#     at its default (true), it falls through to `URL.make(property)` and
#     stays on whatever host/port the Property already had.
# No reachable 7.0.6 code path ever flips this default: the sole writer,
# KorailTalkApplication.setNetFunnel(), only ever passes decoded Strings or
# bare Integer literals (443, 3, 1) into Property -- no Boolean reaches
# setHostNotmodify() there -- and the only other candidate,
# LoadProperty.Parser(), is statically dead (LoadCheck() returns immediately
# on an empty url_, and setUrl(...) is never called anywhere in 7.0.6). So
# the SDK, run with its own compiled defaults, would never rebuild the URL
# from a node reply on its own.
#
# THIS FILE FOLLOWS THE REDIRECT ANYWAY, deliberately, and NOT because it
# mirrors the app's default (an earlier version of this comment claimed the
# opposite default and was wrong -- corrected here; the functional logic
# below was not, and is not, changed by this correction). The justification
# is independent, from observed production behavior:
#
# LIVE EVIDENCE (2026-07-26): sending setComplete to the front door instead
# of the named node failed ~50% of the time with 503:msg="Wrong Server ID".
# Observed nodes: rnf12, rnf13, rnf14 — all under letskorail.com, https/443.
#
# CONSTRAINED, NOT TRUSTED. The redirection is admitted only into the pool's
# own naming; a reply naming anything else is a hard error.
#
# THE RULE:
#   * label: `rnf` + decimal 1..99, no leading zero
#   * parent: exactly `letskorail.com`, whole labels
#   * lowercase only (as observed on wire)
#   * https port 443 only
#   * plus the front door itself (nf.letskorail.com)
# ---------------------------------------------------------------------------

#: 대기열 응답이 가리킬 수 있는 노드 이름. 각 부분을 왜 이만큼 좁혔는지는
#: 위의 블록 주석에 있습니다.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")

#: 지목된 노드에 허용되는 유일한 포트. 관측된 모든 응답이 443 이었고,
#: :func:`assert_korail_netfunnel_origin` 이 정문에 허용하는 포트도 그것뿐입니다.
KORAIL_NETFUNNEL_NODE_PORT = 443

#: **이미 성립한 세션**에 속하는 opcode. 그래서 그 세션을 발급한 노드로 갑니다.
#: ``5101`` 은 일부러 빠져 있습니다. 진입 호출은 정문이 분산하는 것이고, 노드를
#: 가리킬 앞선 응답도 없습니다.
#:
#: 지금은 :data:`KORAIL_NETFUNNEL_KEYED_OPCODES` 와 같은 집합이며 우연이
#: 아닙니다 — 세션은 키로 식별되고 자기 노드에 살기 때문에, 키를 싣는 opcode 가
#: 곧 노드에 닿아야 하는 opcode 입니다. 서로 다른 질문에 답하므로 상수는 따로
#: 둡니다.
KORAIL_NETFUNNEL_NODE_OPCODES = frozenset(
    {
        KorailNetFunnelOpcode.CHK_ENTER.value,
        KorailNetFunnelOpcode.SET_COMPLETE.value,
    }
)


def _assert_netfunnel_origin(netfunnel_url: str, *, allow_nodes: bool) -> None:
    """대기열 origin 가드 둘의 공통 골격.

    정문과 대기열 노드 사이에서 **어떤 호스트명을 받아들이냐**를 빼면 검사가 동일합니다 —
    https, userinfo 없음, path·query·fragment 없음, 443 또는 생략된 포트. 그래서 한 번만
    쓰고 호스트명 규칙만 매개변수로 받습니다.
    """
    parsed = urlsplit(netfunnel_url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        ) from exc
    hostname = (parsed.hostname or "").casefold()
    host_allowed = hostname == KORAIL_NETFUNNEL_HTTPS_HOST or (
        allow_nodes
        and KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(hostname) is not None
    )
    if (
        parsed.scheme.casefold() != "https"
        or parsed.hostname is None
        or not host_allowed
        or port not in {None, KORAIL_NETFUNNEL_NODE_PORT}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel request origin is not allowed"
        )


def assert_korail_netfunnel_origin(netfunnel_url: str) -> None:
    """대기열 **정문**을 ``https://nf.letskorail.com``(443)으로 고정합니다.

    :func:`assert_korail_origin` 의 NetFunnel 짝이며 상수도 함수도 일부러 분리했습니다.
    API 클라이언트는 대기열 호스트에 닿을 수 없고 대기열 클라이언트는 API 호스트에 닿을 수
    없습니다.

    설정된 origin 과 진입 호출(``5101``)에 쓰는 가드이고 정문만 허용합니다 — 대기열 노드는
    여기서 거부됩니다. 후속 opcode 는 더 넓은
    :func:`assert_korail_netfunnel_node_origin` 을 쓰며, 어느 opcode 가 어느 쪽인지는
    :func:`assert_korail_netfunnel_opcode_origin` 이 정합니다.
    """
    _assert_netfunnel_origin(netfunnel_url, allow_nodes=False)


def assert_korail_netfunnel_node_origin(netfunnel_url: str) -> None:
    """세션의 origin 을 정문 또는 대기열 자신의 노드로 제한합니다.

    ``https://nf.letskorail.com`` 과 ``https://rnf<N>.letskorail.com`` 을 443 포트로만
    허용하고 그 밖은 없습니다. 풀이 실재한다는 근거와 경계를 왜 정확히 여기 그었는지는
    :data:`KORAIL_NETFUNNEL_NODE_HOST_RE` 위의 주석에 있습니다.
    """
    _assert_netfunnel_origin(netfunnel_url, allow_nodes=True)


def assert_korail_netfunnel_opcode_origin(
    opcode: str,
    netfunnel_url: str,
) -> None:
    """이 opcode 를 어느 호스트로 보내도 되는지 정합니다.

    ``5101`` getTidChkEnter 는 진입 호출이라 **정문**으로 갑니다. 분산이 정문의 일입니다.
    ``5002`` chkEnter 와 ``5004`` setComplete 는 세션에 속하므로 그 세션을 발급한
    **노드**로 갑니다 — 정문은 그 세션의 주인이 아니라서 완료를 요구하면
    ``503:msg="Wrong Server ID"`` 로 답합니다.

    이 분기가 클라이언트가 아니라 가드에 있는 것은, "이 opcode 는 어느 호스트로 가는가"를
    URL 을 만든 호출 지점이 아니라 가드가 답하게 하기 위해서입니다.
    """
    if opcode in KORAIL_NETFUNNEL_NODE_OPCODES:
        assert_korail_netfunnel_node_origin(netfunnel_url)
    else:
        assert_korail_netfunnel_origin(netfunnel_url)


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """응답의 ``ip``/``port`` 를 답한 노드의 origin 으로 바꿉니다.

    origin URL(``https://<host>``)을 돌려주고, 응답이 아무 노드도 가리키지 않았으면 ``""``
    입니다. 후자는 7.0.6 ``CommandClient.makeURL(Property, Response)``
    (``com/netfunnel/api/CommandClient.java:33-38``)의 조건이 떨어지는 가지입니다 —
    ``:34`` 가 ``response != null && !property.isHostNotmodify() &&
    response.getHost().length() > 0 && response.getPort() > 0`` 을 모두 만족할
    때만 노드 host/port 로 URL 을 다시 만들고(``:35``), 아니면 ``URL.make(property)``
    로 정문에 머뭅니다(``:37``). 후속 요청이 정당하게 정문으로 가는 유일한 경우입니다.
    옛 인용 ``T6/d.makeURL``/``T6/d.java:17-19`` 는 이 메서드의 6.5.0 난독화
    이름이고 7.0.6 에 그 경로가 없습니다.
    ``ip`` 와 ``port`` 는 관측된 모든 응답에서 함께 오므로, 한쪽만 온 것은 "노드를 가리키지
    않았다"가 아니라 "노드를 잘못 가리켰다"로 다룹니다.

    대기열 자신의 노드 이름 규칙 밖 호스트와 443 이 아닌 포트는
    :class:`KorailProtocolError` 입니다. 그 거부는 일부러 시끄럽습니다. 여기서 조용히
    정문으로 되돌아가면 잘못된 재지정이 샌 슬롯으로 바뀌고, 샌 슬롯은 아무 소리도 내지
    않습니다.
    """
    if not ip and not port:
        return ""
    if (
        ip != KORAIL_NETFUNNEL_HTTPS_HOST
        and KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(ip) is None
    ):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named {ip!r} as the host for the rest of "
            "this session, and it is not one of the queue's own nodes "
            "(rnf<1-99>.letskorail.com, lowercase) nor the front door "
            f"{KORAIL_NETFUNNEL_HTTPS_HOST!r}; the redirection this queue needs "
            "is constrained to the pool, never trusted as given"
        )
    if port != str(KORAIL_NETFUNNEL_NODE_PORT):
        raise KorailProtocolError(
            f"KORAIL NetFunnel reply named port {port!r} for queue node {ip!r}; "
            f"only {KORAIL_NETFUNNEL_NODE_PORT} is allowed, and the port is no "
            "more followed on the server's say-so than the host is"
        )
    return f"https://{ip}"


def _are_name_value_pairs(
    pairs: tuple[object, ...],
    *,
    value_type: type | None = None,
) -> bool:
    """Whether every item is a plain 2-tuple with a str name.

    A tuple subclass does not count. With ``value_type`` the value is checked
    too; without it, the caller checks values itself.
    """
    return all(
        type(pair) is tuple
        and len(pair) == 2
        and isinstance(pair[0], str)
        and (value_type is None or isinstance(pair[1], value_type))
        for pair in pairs
    )


def assert_netfunnel_request(
    method: str,
    path: str,
    params: Sequence[tuple[str, str]],
) -> None:
    """등록된 대기열 opcode 만, 정확히 그 순서의 파라미터로만 허용합니다.

    ``params`` 는 요청이 만들어질 이름/값 쌍을 인코딩 전에 순서 그대로 받습니다. 그래서
    계약이 파라미터 구성뿐 아니라 **순서**까지 덮습니다. 앱의 순서는 장식이 아니라
    SDK 가 만든 리스트를 ``URLEncodedUtils.format`` 이 그대로 뱉은 결과입니다 —
    7.0.6 에서 ``CommandClient`` 의 ``addParam`` 호출이
    ``com/netfunnel/api/http/Client.addParam``(``http/Client.java:121-127``)로
    가고, 그것이 ``params_``(``:42``, ``List<NameValuePair>``)에 순서대로
    ``BasicNameValuePair`` 를 add 합니다(``:126``). 그 리스트를 그대로
    ``URLEncodedUtils.format(list, "utf-8")``(``http/Client.GetParamMerge``,
    ``http/Client.java:197-212``, 호출은 ``:202``)이 질의 문자열로 폅니다.
    옛 인용 ``T6/d.java`` 는 ``CommandClient`` 의 6.5.0 난독화 이름입니다.

    :class:`KorailProtocolError` 가 되는 경우는 등록되지 않은 opcode(5003, 5105, 5106 과
    지어낸 값), 계약과 정확히 같지 않거나 순서가 다른 파라미터 목록, ``service_1`` 이 아닌
    ``sid``, :data:`KORAIL_NETFUNNEL_ACTION_IDS` 밖의 ``aid``, NetFunnel 키의 모양이 아닌
    키입니다.
    """
    route = (method.upper(), urlsplit(path).path)
    if route not in KORAIL_NETFUNNEL_ROUTES:
        raise KorailProtocolError(
            f"KORAIL NetFunnel route is not allowed: {route[0]} {route[1]}"
        )
    pairs = tuple(params)
    if not _are_name_value_pairs(pairs, value_type=str):
        raise KorailProtocolError(
            "KORAIL NetFunnel parameters must be ordered string pairs"
        )
    values = dict(pairs)
    opcode = values.get("opcode", "")
    contract = KORAIL_NETFUNNEL_QUERY_CONTRACTS.get(opcode)
    if contract is None:
        raise KorailProtocolError(
            f"KORAIL NetFunnel opcode {opcode!r} is not one of the registered "
            "queue operations (5101 getTidChkEnter, 5002 chkEnter, "
            "5004 setComplete)"
        )
    if tuple(name for name, _value in pairs) != contract:
        raise KorailProtocolError(
            f"KORAIL NetFunnel request is not the registered opcode-{opcode} "
            "contract: expected exactly " + ", ".join(contract) + " in order"
        )
    if opcode in KORAIL_NETFUNNEL_KEYED_OPCODES and (
        KORAIL_NETFUNNEL_KEY_RE.fullmatch(values["key"]) is None
    ):
        raise KorailProtocolError(
            "KORAIL NetFunnel key parameter is missing or malformed"
        )
    if "sid" in values and values["sid"] != KORAIL_NETFUNNEL_SERVICE_ID:
        raise KorailProtocolError(
            "KORAIL NetFunnel service id must be "
            f"{KORAIL_NETFUNNEL_SERVICE_ID!r}"
        )
    if "aid" in values and values["aid"] not in KORAIL_NETFUNNEL_ACTION_IDS:
        raise KorailProtocolError(
            f"KORAIL NetFunnel action id {values['aid']!r} is not one the app "
            "declares"
        )
