# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""5101→필요한 5002→API→5004 순서를 유지하며 노드·오류 정책은 checks/BEHAVIOR.md에 명시합니다.

서버가 준 노드라도 허용 범위 밖이면 신뢰하지 않고 정문을 사용합니다. SDK 근거는 tests/test_netfunnel_limousine.py 에
있습니다."""

from __future__ import annotations

import logging
import re
import time
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, TypeAlias, TypeVar
from urllib.parse import urlencode, urlsplit

import httpx

from ..config import KorailConfig
from ..constants import KORAIL_NETFUNNEL_URL
from ..errors import KorailNetFunnelError, KorailProtocolError, KorailQueueRejectedError, KorailTransportError
from .http import build_transport, redact_failed_request

T = TypeVar("T")

# Logger names predate the _core move; docs/guide/configuration.md names this one.
_log = logging.getLogger("korail_mobile_api.netfunnel")
_safety_log = logging.getLogger("korail_mobile_api.netfunnel_safety")

# evidence: app 7.0.6 NetworkConstants.java:80-99 (보호 문자열, 미확인)
KORAIL_NETFUNNEL_PATH = "/ts.wseq"
KORAIL_NETFUNNEL_SERVICE_ID = "service_1"
# 첫 시도 외 재시도 횟수입니다. SDK 는 실패한 시도의 제한 시간을 채운 뒤 다시 보냅니다.
# evidence: app 7.0.6 NetworkConstants.java:83, KorailTalkApplication.java:388
KORAIL_NETFUNNEL_RETRY = 1


class KorailNetFunnelAction(StrEnum):
    """대기열 관문별로 대기열 서버에 보내는 식별값(``aid``)입니다.

    앱이 쓰는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 다른 값이 필요하면 ``KorailConfig.netfunnel_actions``로
    관문별 값을 바꾸세요."""

    # 앱의 액션 상수 일곱 개는 보호 문자열이라 기본값은 길이와 호출부 문맥으로 고른 미확인 값입니다.
    # evidence: app 7.0.6 NetworkConstants.java:88-94
    # evidence: app 7.0.6 호출부 TrainScheduleViewModel.java:5213-5234, PayViewModel.java:6724
    # evidence: app 7.0.6 호출부 MyReservationViewModel.java:2528, KorailTalkApplication.java:382-386

    INQUIRY = "act_8"
    PEAK_SEASON_INQUIRY = "act_8_2"
    PRODUCT = "act_6"
    RESERVE = "act_14"
    PAY = "act_18"
    RESERVED = "act_21"
    # 앱에 선언만 있고 라이브러리는 쓰지 않습니다.
    TEST = "act_4"


class KorailNetFunnelOpcode(StrEnum):
    """대기열 서버에 보내는 명령 코드(``opcode``)입니다."""

    # evidence: app 7.0.6 com/netfunnel/api/Command.java:4-21

    CHK_ENTER = "5002"
    ALIVE_NOTICE = "5003"
    SET_COMPLETE = "5004"
    GET_TID_CHK_ENTER = "5101"
    INIT = "5105"
    STOP = "5106"


# evidence: app 7.0.6 com/netfunnel/api/Code.java:27-33
SUCCESS_CODE = "200"
# SDK 대기 루프는 Continue(201)/ContinueDebug(202)에서만 돕니다.
CONTINUE_CODES = frozenset({"201", "202"})
BLOCK_CODES = frozenset({"301", "302"})
# evidence: app 7.0.6 Netfunnel.java:634, com/netfunnel/api/Property.java:22
MIN_TTL_SECONDS = 1
MAX_TTL_SECONDS = 30

# 앞의 둘은 SDK 가 싣고(Context_Type 은 SDK 의 철자 그대로), 나머지는 안드로이드 HttpURLConnection 이 붙입니다.
_APP_HEADERS = {
    "Accept-Charset": "UTF-8",
    "Context_Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}

KorailNetFunnelGateName: TypeAlias = Literal[
    "inquiry", "peak_season_inquiry", "product_inquiry", "reserve", "pay", "reservation_view"
]


@dataclass(frozen=True)
class KorailNetFunnelGate:
    name: str
    action: str
    success_only: bool


#: 라이브러리 관문 목록입니다. ``netfunnel_actions`` 로 aid 를 덮어쓸 수 있습니다.
KORAIL_NETFUNNEL_GATES: Mapping[str, KorailNetFunnelGate] = {
    gate.name: gate
    for gate in (
        KorailNetFunnelGate("inquiry", KorailNetFunnelAction.INQUIRY.value, False),
        KorailNetFunnelGate("peak_season_inquiry", KorailNetFunnelAction.PEAK_SEASON_INQUIRY.value, False),
        KorailNetFunnelGate("product_inquiry", KorailNetFunnelAction.PRODUCT.value, False),
        KorailNetFunnelGate("reserve", KorailNetFunnelAction.RESERVE.value, True),
        KorailNetFunnelGate("pay", KorailNetFunnelAction.PAY.value, True),
        KorailNetFunnelGate("reservation_view", KorailNetFunnelAction.RESERVED.value, True),
    )
}


@dataclass(frozen=True)
class KorailNetFunnelToken:
    code: str
    key: str = ""
    params: dict[str, str] = field(default_factory=dict[str, str])
    node: str = ""
    raw: str = ""

    @property
    def wait_count(self) -> int:
        return _java_int(self.params.get("nwait", "")) or 0

    @property
    def wait_seconds(self) -> int:
        ttl = _java_int(self.params.get("ttl", "")) or 0
        return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _java_int(text: str) -> int | None:
    """자바 ``Integer.parseInt`` 처럼 부호 하나 뒤의 십진 숫자를 int32 로 읽고, 아니면 None 입니다. 자바는 UTF-16 코드 단위마다
    ``Character.digit`` 을 보므로 보충 평면 숫자는 받지 않고, 앞의 0 은 길이와 상관없이 받습니다."""
    digits = text[1:] if text[:1] in ("+", "-") else text
    if not digits:
        return None
    value = 0
    for character in digits:
        digit = unicodedata.decimal(character, -1) if ord(character) <= 0xFFFF else -1
        if digit < 0:
            return None
        value = value * 10 + digit
        if value > 2**31:
            return None
    value = -value if text[:1] == "-" else value
    return value if -(2**31) <= value < 2**31 else None


def parse_netfunnel_body(body: str) -> KorailNetFunnelToken:
    """SDK처럼 첫 콜론으로 나누고 코드는 Java int32로 읽습니다."""
    head, separator, tail = body.strip().partition(":")
    code = _java_int(head) if separator else None
    if code is None:
        raise KorailNetFunnelError(None, "KORAIL NetFunnel reply is not '<code>:<params>'", raw=body)
    params: dict[str, str] = {}
    for item in tail.split("&"):
        name, found, value = item.partition("=")
        if found:
            params[name] = value
    return KorailNetFunnelToken(
        code=str(code),
        key=params.get("key", ""),
        params=params,
        node=korail_netfunnel_node_url(params.get("ip", ""), params.get("port", "")),
        raw=body,
    )


@dataclass
class _Slot:
    token: KorailNetFunnelToken | None = None
    node: str = ""
    retries_left: int = KORAIL_NETFUNNEL_RETRY


class KorailNetFunnelClient:
    def __init__(
        self,
        config: KorailConfig | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        config = config or KorailConfig()
        self.config = config
        self._front = config.netfunnel_url.rstrip("/")
        self._sleep = sleeper
        self._clock = clock
        self._client = httpx.Client(
            timeout=config.netfunnel_timeout,
            headers={"User-Agent": config.netfunnel_user_agent, **_APP_HEADERS},
            follow_redirects=False,
            transport=build_transport(config, transport),
        )
        del self._client.headers["Accept"]

    def close(self) -> None:
        self._client.close()

    def gate(self, name: KorailNetFunnelGateName) -> KorailNetFunnelGate:
        gate = KORAIL_NETFUNNEL_GATES[name]
        override = (self.config.netfunnel_actions or {}).get(name)
        if override:
            return KorailNetFunnelGate(gate.name, override, gate.success_only)
        return gate

    def run(self, gate: KorailNetFunnelGate | KorailNetFunnelGateName, send: Callable[[], T]) -> T:
        """차단은 KorailQueueRejectedError이며, mode=1은 통신 오류에도 진행할 수 있지만 mode=0은 API를 보내지 않습니다. 반납 실패는 로그만 남기며,
        전체 정책과 앱의 차이는 모듈 설명을 따릅니다."""
        if isinstance(gate, str):
            gate = self.gate(gate)
        slot = _Slot()
        started = self._clock()
        try:
            self._admit(gate, slot)
            # 느린 대기열 응답·ErrorBypass 도 누적 상한을 넘길 수 있으므로 _admit 직후 다시 검사합니다.
            limit = self.config.netfunnel_wait_limit
            if limit is not None and self._clock() - started > limit:
                token = slot.token
                raise KorailNetFunnelError(
                    token.code if token is not None else None,
                    f"KORAIL NetFunnel took longer than netfunnel_wait_limit={limit}s; "
                    "the API request was not sent",
                    raw=token.raw if token is not None else None,
                )
            return send()
        finally:
            self._complete(slot)

    def _url(self, origin: str, params: tuple[tuple[str, str], ...]) -> str:
        return f"{origin}{KORAIL_NETFUNNEL_PATH}?{urlencode(params)}"

    def _post(self, url: str) -> str:
        """SDK 는 GET 으로 부르지만 setDoOutput(true) 때문에 안드로이드 HttpURLConnection 이 빈 본문 POST 로 보냅니다."""
        if self._client.is_closed:
            raise KorailProtocolError(
                f"KORAIL NetFunnel client is closed; POST {KORAIL_NETFUNNEL_PATH} was not sent"
            )
        try:
            response = self._client.post(url, content=b"")
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
            redact_failed_request(exc)
            raise KorailTransportError(
                f"KORAIL NetFunnel transport failed for POST {KORAIL_NETFUNNEL_PATH}"
            ) from exc
        if response.is_error:
            raise KorailTransportError(
                f"KORAIL NetFunnel HTTP {response.status_code} for POST {KORAIL_NETFUNNEL_PATH}",
                status_code=response.status_code,
            )
        return response.text

    def _request(self, url: str, slot: _Slot) -> KorailNetFunnelToken:
        """공유 재시도 예산을 쓰며 마지막 실패도 timeout 을 채웁니다."""
        while True:
            started = self._clock()
            try:
                return parse_netfunnel_body(self._post(url))
            except (KorailTransportError, KorailNetFunnelError):
                remaining = self.config.netfunnel_timeout - (self._clock() - started)
                if remaining > 0:
                    self._sleep(remaining)
                if slot.retries_left <= 0:
                    raise
                slot.retries_left -= 1

    def _enter(
        self, gate: KorailNetFunnelGate, slot: _Slot, origin: str, params: tuple[tuple[str, str], ...]
    ) -> KorailNetFunnelToken | None:
        """5101·5002 한 번입니다. 실패하면 ErrorBypass 정책을 적용하고 None 을 돌려줍니다."""
        try:
            token = self._request(self._url(origin, params), slot)
        except (KorailTransportError, KorailNetFunnelError) as exc:
            self._error_bypass(gate, exc)
            return None
        slot.token, slot.node = token, token.node
        return token

    def _admit(self, gate: KorailNetFunnelGate, slot: _Slot) -> None:
        started = self._clock()
        token = self._enter(
            gate,
            slot,
            self._front,
            (
                ("opcode", KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value),
                ("sid", KORAIL_NETFUNNEL_SERVICE_ID),
                ("aid", gate.action),
            ),
        )
        while token is not None and token.code in CONTINUE_CODES:
            if not token.key:
                # SDK 는 빈 키에서 5002 를 보내지 않고 대기합니다.
                raise KorailNetFunnelError(
                    token.code, "KORAIL NetFunnel told this request to wait but gave no key", raw=token.raw
                )
            wait = token.wait_seconds
            limit = self.config.netfunnel_wait_limit
            if limit is not None and self._clock() - started + wait > limit:
                raise KorailNetFunnelError(
                    token.code,
                    f"KORAIL NetFunnel queue did not admit this request within "
                    f"netfunnel_wait_limit={limit}s (nwait={token.wait_count})",
                    raw=token.raw,
                )
            self._sleep(wait)
            token = self._enter(
                gate,
                slot,
                slot.node or self._front,
                (("opcode", KorailNetFunnelOpcode.CHK_ENTER.value), ("key", token.key)),
            )
        if token is None:
            return
        if token.code in BLOCK_CODES:
            raise KorailQueueRejectedError(token.code, "KORAIL NetFunnel blocked this request", raw=token.raw)
        if token.code == SUCCESS_CODE or not gate.success_only:
            return
        raise KorailNetFunnelError(
            token.code,
            f"KORAIL NetFunnel answered {token.code}; the app sends the "
            f"{gate.name!r} request only on 200, so this one was not sent",
            raw=token.raw,
        )

    def _error_bypass(self, gate: KorailNetFunnelGate, exc: Exception) -> None:
        """대기열 오류 시 mode=1만 통과시키고 mode=0은 요청 전에 거절합니다."""
        if gate.success_only:
            raise KorailNetFunnelError(
                None,
                f"KORAIL NetFunnel failed before the {gate.name!r} request; the "
                "app does not send it then, so neither does this client",
            ) from exc
        _log.warning(
            "KORAIL NetFunnel failed (%s); sending %r without a queue pass as the app does (ErrorBypass)",
            exc,
            gate.name,
        )

    def _complete(self, slot: _Slot) -> None:
        """재시도·응답 파싱은 하지 않으며 실패는 경고 로그만 남깁니다."""
        token = slot.token
        if token is None or not token.key:
            return
        try:
            self._post(
                self._url(
                    slot.node or self._front,
                    (("opcode", KorailNetFunnelOpcode.SET_COMPLETE.value), ("key", token.key)),
                )
            )
        except Exception as exc:
            # 반납은 finally 에서 불리므로 어떤 실패도 API 쪽 원래 예외를 가리지 않게 로그만 남깁니다.
            _log.warning("KORAIL NetFunnel setComplete failed: %s", exc)


KORAIL_NETFUNNEL_HTTPS_HOST = urlsplit(KORAIL_NETFUNNEL_URL).hostname
# SDK 기본값 host_notmodify=true 는 응답 노드 이동을 막으며, 앱 기동 시 바꾸는지는 보호된 setter 때문에 미확인입니다.
KORAIL_NETFUNNEL_NODE_HOST_RE = re.compile(r"rnf[1-9][0-9]?\.letskorail\.com")
KORAIL_NETFUNNEL_NODE_PORT = 443


def korail_netfunnel_node_url(ip: str, port: str) -> str:
    """노드가 없거나 허용 범위 밖이면 빈 문자열이며, 호출자는 정문을 씁니다."""
    if not ip and not port:
        return ""
    host_allowed = ip == KORAIL_NETFUNNEL_HTTPS_HOST or KORAIL_NETFUNNEL_NODE_HOST_RE.fullmatch(ip) is not None
    if not host_allowed or port != str(KORAIL_NETFUNNEL_NODE_PORT):
        _safety_log.warning(
            "KORAIL NetFunnel reply named node %r port %r; only rnf<1-99>.letskorail.com (lowercase) or the "
            "front door on %d are followed, so the front door is used",
            ip,
            port,
            KORAIL_NETFUNNEL_NODE_PORT,
        )
        return ""
    return f"https://{ip}"
