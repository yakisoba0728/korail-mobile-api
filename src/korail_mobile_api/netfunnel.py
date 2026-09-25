# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""API 요청 전에 대기열을 통과하고 처리 후 키를 반납합니다.

앱 SDK 1.7.18(Netfunnel.java:18)은 5101 진입 후 201/202에서만 TTL 1~30초마다 5002를 반복합니다 (Netfunnel.java:610-664;
com/netfunnel/api/Response.java:59-66). SDK에는 누적 상한이 없습니다. 앱의 별도 콜백 감시는 시계 차를 15000과 비교하지만 단위는 보호돼 있으며, 전체 대기
상한이 아닙니다 (ScreenViewModel$withNetFunnel$2$1$5.smali:603-692,875-889). 라이브러리는 이 감시를 구현하지 않습니다.

앱은 mode=0에서 Success만, mode=1에서 사용자 중단 이외의 결과를 통과시킵니다 (ScreenViewModel.java:837-900,1719,1955,1986). SDK의 기본 오류
처리는 ErrorBypass입니다 (Netfunnel.java:269-270; com/netfunnel/api/Property.java:9). aid·sid 평문은 보호돼 있습니다. 라이브러리는
301/302를 항상 거절하고, mode=0 비성공·설정된 누적 상한 초과 시 API를 보내지 않습니다. 5002/5004의 노드는 netfunnel_safety로 제한하며, 키를 KORAIL 요청에
싣지 않습니다.

5004는 API 응답 뒤 finally에서 한 번 보내며, 실패는 로그만 남깁니다(Netfunnel.java:848-880; CommandClient.java:182-184). 앱의 onPass 뒤
디스패치 대상은 보호돼 있어 같은 반납 시점인지는 검증 못 함입니다(ScreenViewModel.java:857-900).

2026-09-24 비로그인 조회에서 5101→201→5002→200→ScheduleView→5004(200)와 5101→200→ScheduleView→5004(200)를 확인했습니다.
202·301/302·300/303 분기는 검증 못 함입니다. 예약·결제 API의 성공 기록은 보호된 앱 mode=0 배정이나 비성공 분기의 검증과는 구별합니다."""

from __future__ import annotations

import logging
import re
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
    KorailProtocolError,
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

#: 대기열 요청의 헤더. 앞의 둘은 SDK 가 싣고(``com/netfunnel/api/http/Client.java:259-260``, ``Context_Type`` 은
#: SDK 의 철자 그대로), 나머지는 안드로이드 HttpURLConnection 이 붙입니다: 본문을 쓰는 요청의 Content-Type 은 AOSP
#: external/okhttp HttpURLConnectionImpl.newHttpEngine, Connection·Accept-Encoding 은 HttpEngine.networkRequest.
#: Accept 는 붙이지 않습니다.
_APP_HEADERS = {
    "Accept-Charset": "UTF-8",
    "Context_Type": "application/x-www-form-urlencoded;charset=UTF-8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}


@dataclass(frozen=True)
class KorailNetFunnelGate:
    """대기열 관문의 액션과 통과 조건을 담습니다. action은 aid, success_only는 라이브러리의 성공 전용 관문입니다. 앱 mode와의 대응 한계는 모듈 설명을 따릅니다."""

    name: str
    action: str
    success_only: bool


def _gate(name: str, action: KorailNetFunnelAction, *, success_only: bool) -> KorailNetFunnelGate:
    return KorailNetFunnelGate(name, action.value, success_only)


#: 라이브러리 관문 목록. netfunnel_actions 로 aid 를 덮어쓸 수 있습니다. aid 값은 보호 문자열의 길이와 호출 문맥으로 고른 미확인 값입니다(constants 참고).
#: inquiry/peak_season_inquiry/product_inquiry: TrainScheduleViewModel.java:5208-5244, 다음 페이지 :1126, 요청 :7216.
#: 상품 aid·라우트 연결은 추정입니다. reserve: TrainScheduleViewModel.java:5003,5104, TrainSeatMapViewModel.java:2627,2719,
#: HomeViewModel.java:6231, ReservationWaitViewModel.java:578. pay: PayViewModel.java:6724,
#: FPayViewModel.java:795. reservation_view: MyReservationViewModel.java:2528. mode 리터럴이 보호돼 0 배정은 미검증.
#: 관광열차의 선택값과 직접 요청 분기의 조건도 보호돼 연결을 확정하지 않습니다(TrainScheduleViewModel.java:5216-5242).
#: 그 밖의 작업 연결 여부는 client.py 를 보십시오. 이 표가 모든 앱 호출을 증명하지는 않습니다.
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
    """대기열 응답의 코드·키·대기 조건을 담습니다. node는 응답 노드의 원점 주소이며, raw는 응답 본문입니다."""

    code: str
    key: str = ""
    params: dict[str, str] = field(default_factory=dict[str, str])
    node: str = ""
    raw: str = ""

    @property
    def wait_count(self) -> int:
        """앞에서 기다리는 요청 수를 반환합니다."""
        return _digits(self.params.get("nwait", ""))

    @property
    def wait_seconds(self) -> int:
        """다음 대기 확인까지의 시간을 1~30초로 제한해 반환합니다. 앱 근거: com/netfunnel/api/Response.java:59-66."""
        ttl = _digits(self.params.get("ttl", ""))
        return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _digits(raw: str) -> int:
    return int(raw) if raw.isascii() and raw.isdigit() else 0


_JAVA_INT_RE = re.compile(r"[+-]?\d+")


def _java_int(text: str) -> int | None:
    """자바 ``Integer.parseInt`` 처럼 부호 하나와 유니코드 십진 숫자를 받아 int32 범위의 값을 돌려주고, 아니면 None 입니다."""
    if _JAVA_INT_RE.fullmatch(text) is None:
        return None
    try:
        value = int(text)
    except ValueError:  # 파이썬의 정수 자릿수 한도
        return None
    return value if -(2**31) <= value < 2**31 else None


def parse_netfunnel_body(body: str) -> KorailNetFunnelToken:
    """응답 본문을 코드와 파라미터로 가릅니다(``Response.Parser``, ``com/netfunnel/api/Response.java:128-163``).

    첫 ``:`` 앞이 코드, 뒤가 ``&`` 로 나뉜 ``name=value`` 쌍입니다. 코드는 SDK 처럼 ``Integer.parseInt`` 로 읽어 ``0200``·``+200`` 도
    ``200`` 입니다. ``:`` 가 없거나 코드가 int32 정수가 아니면 ``errors.KorailNetFunnelError``(앱의 ``Code.ErrorData``)입니다. 서버가 준
    ``ip``/``port`` 는 ``netfunnel_safety`` 의 가드를 통과해야 합니다."""
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
    """대기열 처리 중 최신 응답·노드·재시도 예산을 보관합니다."""

    def __init__(self) -> None:
        self.token: KorailNetFunnelToken | None = None
        self.node = ""
        self.retries_left = KORAIL_NETFUNNEL_RETRY


class KorailNetFunnelClient:
    """API 요청 전 대기열 통과와 처리 후 키 반납을 수행합니다. sleeper/clock 은 오프라인 시험용으로 주입할 수 있습니다."""

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
        """대기열 HTTP 연결을 닫습니다."""
        self._client.close()

    def gate(self, name: str) -> KorailNetFunnelGate:
        """관문 설정을 읽고 netfunnel_actions의 aid 덮어쓰기를 적용합니다."""
        gate = KORAIL_NETFUNNEL_GATES[name]
        override = (self.config.netfunnel_actions or {}).get(name)
        if override:
            return KorailNetFunnelGate(gate.name, override, gate.success_only)
        return gate

    def run(self, gate: KorailNetFunnelGate | str, send: Callable[[], T]) -> T:
        """관문을 통과한 뒤 send를 호출하고 최신 키를 한 번 반납합니다. 차단은 KorailQueueRejectedError이며, mode=1은 통신 오류에도 진행할 수 있지만
        mode=0은 API를 보내지 않습니다. 반납 실패는 로그만 남기며, 전체 정책과 앱의 차이는 모듈 설명을 따릅니다."""
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
        보냅니다(AOSP external/okhttp HttpURLConnectionImpl.initHttpEngine). 인자는 URL 에 남고 Content-Length 는 0 입니다."""
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
        """최신 키가 있을 때만 5004 를 보냅니다. 재시도·응답 파싱은 하지 않습니다 (Netfunnel.java:848-880, CommandClient.java:158-199). 실패는
        경고 로그만 남깁니다."""
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
