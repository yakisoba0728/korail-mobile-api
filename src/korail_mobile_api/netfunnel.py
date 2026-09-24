# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""NetFunnel 대기열. KORAIL API 요청 전에 관문을 통과하고 키를 반납합니다.

앱 SDK 1.7.18(Netfunnel.java:18)은 5101 로 진입하고 201/202 에서만 TTL 1~30초 대기 후 5002 를 반복합니다(Netfunnel.java:610-664,
com/netfunnel/api/Response.java:59-66). SDK 루프에는 누적 대기 상한이 없습니다. 다만 앱의 연결부에는 마지막 콜백과 현재 시계의 차를 15000 과 비교해
finish(false) 로 끝내는 감시가 따로 있습니다 (ScreenViewModel$withNetFunnel$2$1$5.smali:603-692,875-889; 시계 단위는 보호돼 ms 이면
15초). 콜백이 끊겼을 때의 감시이지 전체 대기 상한이 아니며, 이 라이브러리에는 없습니다. ScreenViewModel.java:837-900,1719,1955,1986 의 연결부는 mode=0
에서 Success 만, mode=1 에서 사용자 중단 이외의 결과를 통과시킵니다. SDK 는 오류를 기본으로 ErrorBypass 로 바꾸므로(Netfunnel.java:269-270,
com/netfunnel/api/Property.java:9 ``err_bypass_ = true``) 대기열 서버 장애에도 조회(mode=1)는 나갑니다. aid·sid 평문은 보호돼 있습니다. 키는
대기열용이며 이 라이브러리는 KORAIL 요청에 싣지 않습니다.

앱과 다른 정책:
* 차단 301/302 는 mode=1 에서도 KorailQueueRejectedError 입니다.
* 반납(5004)은 KORAIL 응답 뒤 finally 에서 보냅니다. 앱 finish(ScreenViewModel.java:857-900)는 onPass 디스패치(:876) 뒤에
  보호된 디스패치(:893-894)를 두어 요청 직후 End() 로 보이지만 대상이 식별되지 않아 확정하지 않습니다.
* 5002/5004 는 응답이 지목한 노드로 갑니다(앱의 SDK 기본값은 정문에 머뭅니다). 허용 규칙은 netfunnel_safety.
* 선택적 netfunnel_wait_limit 초과나 mode=0 비성공은 요청 없이 예외를 냅니다.
5004 는 재시도·응답 파싱 없이 처리하며 실패는 로그로 남깁니다 (Netfunnel.java:848-880, CommandClient.java:182-184).

2026-09-24 라이브 관측(비로그인 inquiry 2회): 5101→201→5002→200→ScheduleView→5004(200), 5101→200→ScheduleView→5004(200).
202·301/302·300/303 과 예약·결제 mode=0 은 라이브 미검증입니다."""

from __future__ import annotations

import logging
import time
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
    KorailQueueRejectedError,
    KorailTransportError,
)
from .netfunnel_safety import korail_netfunnel_node_url

T = TypeVar("T")

_log = logging.getLogger(__name__)

#: ``Code.Success`` — ``com/netfunnel/api/Code.java:27``.
SUCCESS_CODE = "200"
#: 대기. SDK 대기 루프는 ``Code.Continue``(201)/``ContinueDebug``(202)에서만 돕니다 (``Netfunnel.java:622``,
#: ``com/netfunnel/api/Code.java:28-29``).
CONTINUE_CODES = frozenset({"201", "202"})
#: 차단. ``EvnetCode.isBlocking()``(``Netfunnel.java:114-116``)이 참인 ``Block``(301)/ ``IpBlock``(302).
BLOCK_CODES = frozenset({"301", "302"})
#: ``ttl`` 을 묶는 범위. 호출부가 ``getTTL(getProperty().getMaxTTL(), 1)`` 로 부르고 (``Netfunnel.java:634``) ``max_ttl_`` 의
#: 기본값이 30 입니다(``com/netfunnel/api/Property.java:22``).
MIN_TTL_SECONDS = 1
MAX_TTL_SECONDS = 30

#: 대기열 요청에 앱이 싣는 헤더(``com/netfunnel/api/http/Client.java:259-260``). ``Context_Type`` 은 SDK 의 철자 그대로입니다.
_APP_HEADERS = {
    "Accept-Charset": "UTF-8",
    "Context_Type": "application/x-www-form-urlencoded;charset=UTF-8",
}


@dataclass(frozen=True)
class KorailNetFunnelGate:
    """action 은 aid, success_only 는 mode=0 에 해당합니다. 앱과의 정책 차이는 모듈 설명 참고."""

    name: str
    action: str
    success_only: bool


def _gate(name: str, action: KorailNetFunnelAction, *, success_only: bool) -> KorailNetFunnelGate:
    return KorailNetFunnelGate(name, action.value, success_only)


#: 라이브러리 관문 목록. netfunnel_actions 로 aid 를 덮어쓸 수 있습니다. aid 값은 보호 문자열의 길이와 호출 문맥으로 고른 미확인 값입니다(constants 참고).
#: inquiry/peak_season_inquiry/product_inquiry: TrainScheduleViewModel.java:5208-5244, 다음 페이지 :1126, 요청 :7216.
#: 상품 aid·라우트 연결은 추정입니다. reserve: TrainScheduleViewModel.java:5003,5104, TrainSeatMapViewModel.java:2627,2719,
#: HomeViewModel.java:6231, ReservationWaitViewModel.java:578. pay: PayViewModel.java:6724,
#: FPayViewModel.java:795. reservation_view: MyReservationViewModel.java:2528. mode 리터럴이 보호돼 0 배정은 미검증. 관광열차 분기는
#: 관문 없이 요청(TrainScheduleViewModel.java:5216-5242). 그 밖의 작업 연결 여부는 client.py 를 보십시오. 이 표가 모든 앱 호출을 증명하지는 않습니다.
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
    """대기열 응답 하나(``<code>:<name>=<value>&...``).

    ``node`` 는 응답이 지목한 노드 origin(없으면 ``""``), ``raw`` 는 받은 본문입니다."""

    code: str
    key: str = ""
    params: dict[str, str] = field(default_factory=dict[str, str])
    node: str = ""
    raw: str = ""

    @property
    def wait_count(self) -> int:
        """``nwait`` — 앞에 선 사람 수."""
        return _digits(self.params.get("nwait", ""))

    @property
    def wait_seconds(self) -> int:
        """다음 5002 까지 잘 시간 — ``ttl`` 을 [1, 30] 으로 묶은 값(``com/netfunnel/api/Response.java:59-66``)."""
        ttl = _digits(self.params.get("ttl", ""))
        return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _digits(raw: str) -> int:
    return int(raw) if raw.isascii() and raw.isdigit() else 0


def parse_netfunnel_body(body: str) -> KorailNetFunnelToken:
    """응답 본문을 코드와 파라미터로 가릅니다(``Response.Parser``, ``com/netfunnel/api/Response.java:128-163``).

    첫 ``:`` 앞이 코드, 뒤가 ``&`` 로 나뉜 ``name=value`` 쌍입니다. ``:`` 가 없거나 코드가 숫자가 아니면
    :class:`~korail_mobile_api.errors.KorailNetFunnelError`(앱의 ``Code.ErrorData``)입니다. 서버가 준 ``ip``/``port`` 는
    :mod:`~korail_mobile_api.netfunnel_safety` 의 가드를 통과해야 합니다."""
    head, separator, tail = body.strip().partition(":")
    if not separator or not head.isascii() or not head.isdigit():
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
        code=head,
        key=key,
        params=params,
        node=korail_netfunnel_node_url(params.get("ip", ""), params.get("port", "")),
        raw=body,
    )


class _Slot:
    """가장 최근에 받은 응답 — 앱의 ``CommandClient.response_`` 처럼 응답마다 통째로 바뀝니다."""

    def __init__(self) -> None:
        self.token: KorailNetFunnelToken | None = None
        self.node = ""
        self.retries_left = KORAIL_NETFUNNEL_RETRY


class KorailNetFunnelClient:
    """설정된 netfunnel_url 과 netfunnel_safety 검사를 통과한 응답 노드로 요청하는 대기열 클라이언트입니다. sleeper/clock 은 오프라인 시험용으로 주입할 수
    있습니다."""

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
            headers={"User-Agent": config.user_agent, **_APP_HEADERS},
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
        """대기열 HTTP 연결을 닫습니다."""
        self._client.close()

    def gate(self, name: str) -> KorailNetFunnelGate:
        """:data:`KORAIL_NETFUNNEL_GATES` 의 관문에 설정의 ``aid`` 덮어쓰기를 적용합니다."""
        gate = KORAIL_NETFUNNEL_GATES[name]
        override = (self.config.netfunnel_actions or {}).get(name)
        if override:
            return KorailNetFunnelGate(gate.name, override, gate.success_only)
        return gate

    def run(self, gate: KorailNetFunnelGate | str, send: Callable[[], T]) -> T:
        """관문 통과 후 send 를 호출하고 finally 에서 최신 키를 한 번 반납합니다.

        차단은 KorailQueueRejectedError. mode=1 은 대기열 통신 오류 시 키 없이 진행할 수 있으나, mode=0 은 요청하지 않고 KorailNetFunnelError
        를 냅니다. 반납 실패는 로그만 남깁니다."""
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

    def _get(self, url: str) -> str:
        try:
            response = self._client.get(url)
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL NetFunnel transport failed for GET {KORAIL_NETFUNNEL_PATH}"
            ) from exc
        if response.is_error:
            raise KorailTransportError(
                f"KORAIL NetFunnel HTTP {response.status_code} for GET "
                f"{KORAIL_NETFUNNEL_PATH}"
            )
        return response.text

    def _request(self, url: str, slot: _Slot) -> KorailNetFunnelToken:
        """공유 재시도 예산을 쓰며 마지막 실패도 timeout 을 채웁니다 (Netfunnel.java:352-363,592)."""
        while True:
            started = self._clock()
            try:
                return parse_netfunnel_body(self._get(url))
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
        """대기열 요청이 실패했을 때 — ``mode=1`` 은 통과, ``mode=0`` 은 요청하지 않음."""
        if gate.success_only:
            raise KorailNetFunnelError(
                None,
                f"KORAIL NetFunnel failed before the {gate.name!r} request; the "
                "app does not send it then, so neither does this client",
            ) from exc
        _log.warning(
            "KORAIL NetFunnel failed (%s); sending %r without a queue pass as "
            "the app does (ErrorBypass)",
            exc,
            gate.name,
        )

    def _complete(self, slot: _Slot) -> None:
        """최신 키가 있을 때만 5004 를 보냅니다. 재시도·응답 파싱은 하지 않습니다 (Netfunnel.java:848-880, CommandClient.java:158-199). 실패는
        경고 로그만 남깁니다."""
        token = slot.token
        if token is None or not token.key:
            return
        try:
            self._get(
                self._url(
                    slot.node or self._front,
                    (
                        ("opcode", KorailNetFunnelOpcode.SET_COMPLETE.value),
                        ("key", token.key),
                    ),
                )
            )
        except KorailTransportError as exc:
            _log.warning("KORAIL NetFunnel setComplete failed: %s", exc)
