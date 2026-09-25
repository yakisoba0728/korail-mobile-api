# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""5101→필요한 5002→API→5004 순서를 유지하며 노드·오류 정책은 checks/BEHAVIOR.md에 명시합니다."""

from __future__ import annotations

import logging
import time
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TypeVar
from urllib.parse import urlencode

import httpx

from .config import KorailConfig
from .constants import (
    KORAIL_NETFUNNEL_PATH,
    KORAIL_NETFUNNEL_RETRY,
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
from .netfunnel_safety import korail_netfunnel_node_url

T = TypeVar("T")

_log = logging.getLogger(__name__)

#: ``Code.Success`` — ``com/netfunnel/api/Code.java:27``.
SUCCESS_CODE = "200"
#: SDK 대기 루프는 ``Code.Continue``(201)/``ContinueDebug``(202)에서만 돕니다 (``Netfunnel.java:622``,
#: ``com/netfunnel/api/Code.java:28-29``).
CONTINUE_CODES = frozenset({"201", "202"})
#: ``EvnetCode.isBlocking()``(``Netfunnel.java:114-116``)이 참인 ``Block``(301)/ ``IpBlock``(302).
BLOCK_CODES = frozenset({"301", "302"})
#: 호출부가 ``getTTL(getProperty().getMaxTTL(), 1)`` 로 부르고 (``Netfunnel.java:634``) ``max_ttl_`` 의 기본값이 30
#: 입니다(``com/netfunnel/api/Property.java:22``).
MIN_TTL_SECONDS = 1
MAX_TTL_SECONDS = 30

#: 앞의 둘은 SDK 가 싣고(``com/netfunnel/api/http/Client.java:259-260``, ``Context_Type`` 은 SDK 의 철자 그대로), 나머지는 안드로이드
#: HttpURLConnection 이 붙입니다: 본문을 쓰는 요청의 Content-Type 은 AOSP external/okhttp HttpURLConnectionImpl.newHttpEngine,
#: Connection·Accept-Encoding 은 HttpEngine.networkRequest.
_APP_HEADERS = {
    "Accept-Charset": "UTF-8",
    "Context_Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}


@dataclass(frozen=True)
class KorailNetFunnelGate:
    name: str
    action: str
    success_only: bool


def _gate(name: str, action: KorailNetFunnelAction, *, success_only: bool) -> KorailNetFunnelGate:
    return KorailNetFunnelGate(name, action.value, success_only)


#: 라이브러리 관문 목록. netfunnel_actions 로 aid 를 덮어쓸 수 있습니다. aid 값은 보호 문자열의 길이와 호출 문맥으로 고른 미확인 값입니다(constants 참고).
#: inquiry/peak_season_inquiry/product_inquiry: TrainScheduleViewModel.java:5208-5244, 다음 페이지 :1126, 요청 :7216.
KORAIL_NETFUNNEL_GATES: Mapping[str, KorailNetFunnelGate] = {
    gate.name: gate
    for gate in (
        _gate("inquiry", KorailNetFunnelAction.INQUIRY, success_only=False),
        _gate(
            "peak_season_inquiry",
            KorailNetFunnelAction.PEAK_SEASON_INQUIRY,
            success_only=False,
        ),
        _gate("product_inquiry", KorailNetFunnelAction.PRODUCT, success_only=False),
        _gate("reserve", KorailNetFunnelAction.RESERVE, success_only=True),
        _gate("pay", KorailNetFunnelAction.PAY, success_only=True),
        _gate("reservation_view", KorailNetFunnelAction.RESERVED, success_only=True),
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
        return _digits(self.params.get("nwait", ""))

    @property
    def wait_seconds(self) -> int:
        """앱 근거: com/netfunnel/api/Response.java:59-66."""
        ttl = _digits(self.params.get("ttl", ""))
        return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _digits(raw: str) -> int:
    return _java_int(raw) or 0


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
    """SDK처럼 첫 콜론으로 나누고 코드는 Java int32로 읽습니다(com/netfunnel/api/Response.java:128-163)."""
    head, separator, tail = body.strip().partition(":")
    code = _java_int(head) if separator else None
    if code is None:
        raise KorailNetFunnelError(
            None,
            "KORAIL NetFunnel reply is not '<code>:<params>'",
            raw=body,
        )
    params: dict[str, str] = {}
    for item in tail.split("&"):
        name, found, value = item.partition("=")
        if found:
            params[name] = value
    key = params.get("key", "")
    return KorailNetFunnelToken(
        code=str(code),
        key=key,
        params=params,
        node=korail_netfunnel_node_url(params.get("ip", ""), params.get("port", "")),
        raw=body,
    )


class _Slot:
    def __init__(self) -> None:
        self.token: KorailNetFunnelToken | None = None
        self.node = ""
        self.retries_left = KORAIL_NETFUNNEL_RETRY


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
            transport=transport,
        )
        del self._client.headers["Accept"]

    def close(self) -> None:
        self._client.close()

    def gate(self, name: str) -> KorailNetFunnelGate:
        gate = KORAIL_NETFUNNEL_GATES[name]
        override = (self.config.netfunnel_actions or {}).get(name)
        if override:
            return KorailNetFunnelGate(gate.name, override, gate.success_only)
        return gate

    def run(self, gate: KorailNetFunnelGate | str, send: Callable[[], T]) -> T:
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
        """SDK 는 GET 으로 부르지만 setDoOutput(true)(Client.java:257) 때문에 안드로이드 HttpURLConnection 이 빈 본문 POST 로
        보냅니다(AOSP external/okhttp HttpURLConnectionImpl.initHttpEngine)."""
        if self._client.is_closed:
            raise KorailProtocolError(
                f"KORAIL NetFunnel client is closed; POST {KORAIL_NETFUNNEL_PATH} was not sent"
            )
        try:
            response = self._client.post(url, content=b"")
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL NetFunnel transport failed for POST {KORAIL_NETFUNNEL_PATH}"
            ) from exc
        if response.is_error:
            raise KorailTransportError(
                f"KORAIL NetFunnel HTTP {response.status_code} for POST {KORAIL_NETFUNNEL_PATH}"
            )
        return response.text

    def _request(self, url: str, slot: _Slot) -> KorailNetFunnelToken:
        """공유 재시도 예산을 쓰며 마지막 실패도 timeout 을 채웁니다 (Netfunnel.java:352-363,592)."""
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

    def _admit(self, gate: KorailNetFunnelGate, slot: _Slot) -> None:
        started = self._clock()
        try:
            token = self._request(
                self._url(
                    self._front,
                    (
                        ("opcode", KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value),
                        ("sid", KORAIL_NETFUNNEL_SERVICE_ID),
                        ("aid", gate.action),
                    ),
                ),
                slot,
            )
        except (KorailTransportError, KorailNetFunnelError) as exc:
            self._error_bypass(gate, exc)
            return
        slot.token, slot.node = token, token.node
        while token.code in CONTINUE_CODES:
            if not token.key:
                # SDK 는 빈 키에서 5002 를 보내지 않고 대기합니다(CommandClient.java:104-108).
                raise KorailNetFunnelError(
                    token.code,
                    "KORAIL NetFunnel told this request to wait but gave no key",
                    raw=token.raw,
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
            try:
                token = self._request(
                    self._url(
                        slot.node or self._front,
                        (
                            ("opcode", KorailNetFunnelOpcode.CHK_ENTER.value),
                            ("key", token.key),
                        ),
                    ),
                    slot,
                )
            except (KorailTransportError, KorailNetFunnelError) as exc:
                # 실패한 5002 는 ErrorCheckEnter→ErrorBypass 로 처리됩니다(Netfunnel.java:654-664).
                self._error_bypass(gate, exc)
                return
            slot.token, slot.node = token, token.node
        if token.code in BLOCK_CODES:
            raise KorailQueueRejectedError(
                token.code,
                "KORAIL NetFunnel blocked this request",
                raw=token.raw,
            )
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
        """재시도·응답 파싱은 하지 않습니다 (Netfunnel.java:848-880, CommandClient.java:158-199). 실패는 경고 로그만 남깁니다."""
        token = slot.token
        if token is None or not token.key:
            return
        try:
            self._post(
                self._url(
                    slot.node or self._front,
                    (
                        ("opcode", KorailNetFunnelOpcode.SET_COMPLETE.value),
                        ("key", token.key),
                    ),
                )
            )
        except Exception as exc:
            # 반납은 finally 에서 불리므로 어떤 실패도 API 쪽 원래 예외를 가리지 않게 로그만 남깁니다.
            _log.warning("KORAIL NetFunnel setComplete failed: %s", exc)
