# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""NetFunnel 가상 대기열(``nf.letskorail.com``).

7.0.6 앱은 열차조회·예약·결제·예약내역 요청 앞에서 대기열 표를 받고, 통과한 뒤에만 그
요청을 보내고, 표를 반납합니다. :class:`~korail_mobile_api.client.KorailClient` 는
:attr:`~korail_mobile_api.config.KorailConfig.netfunnel_enabled` 가 참(기본값)이면 같은
자리에서 :meth:`KorailNetFunnelClient.run` 을 거칩니다.

근거는 7.0.6 기준입니다. NetFunnel SDK(``com/netfunnel/api/``, 버전 ``1.7.18`` —
``Netfunnel.java:18``)는 난독화되지 않아 평문으로 읽히고, 앱 쪽 연결부
(``ui/screen/common/ScreenViewModel.java``)는 호출 구조는 읽히지만 문자열이 AlienGuard 로
보호돼 있습니다.

앱의 흐름
---------
``ScreenViewModel.withNetFunnel(aid, loading, mode, onPass)``(``ScreenViewModel.java:1719``)
가 유일한 연결부입니다.

1. ``Netfunnel.BEGIN(sid, aid, nodeId, listener, handler)``(``:1955``; SDK
   ``Netfunnel.java:976-987``)이 작업 스레드에서 5101 ``getTidChkEnter`` 를 보냅니다
   (``Netfunnel.java:610``). ``sid`` 는 len 9 보호 문자열(``ScreenViewModel.java:1864``,
   ``service_1``)입니다.
2. 응답 코드가 201/202(대기)가 아니면 곧바로 끝냅니다(``Netfunnel.java:622-628``). 즉 5101
   이 200 이면 5002 없이 통과입니다.
3. 대기면 ``ttl`` 초(``getTTL(maxTTL=30, 1)`` 로 [1, 30] 에 묶음, ``:634``,
   ``Response.java:59-66``) 잔 뒤 5002 ``chkEnter`` 를 최신 키로 보내고 2 로 돌아갑니다
   (``Netfunnel.java:636-654``). 반복 횟수·누적 시간 상한은 없습니다 — 끝나는 길은
   비-대기 코드와 사용자의 중단(``StopContinue``, 화면이 닫힐 때 ``stopNetFunnel``)뿐입니다.
4. 끝나면 ``finish``(``ScreenViewModel.java:857-900``)가 ``mode`` 에 따라 통과 여부를
   정하고, 통과면 ``onPass`` 로 KORAIL 요청 코루틴을 띄운 **직후** ``End()`` 로 5004
   ``setComplete`` 를 보냅니다(``:893``; SDK ``Netfunnel.java:848-880``). 통과가 아니어도
   ``End()`` 는 불립니다. 5004 응답은 읽지 않고(``CommandClient.java:182-184``) 실패도
   무시됩니다.

키는 대기열 안에서만 쓰입니다. ``onPass`` 가 띄우는 요청(예:
``TrainScheduleViewModel.requestNonMemTicket(nonMemTicketIn, ticketReservationIn)``,
``TrainScheduleViewModel.java:5045``)은 키를 인자로 받지 않고, KORAIL API 요청에 키를
싣는 헤더나 필드도 없습니다 — **클라이언트 쪽 관문**입니다.

``mode`` 는 두 가지가 쓰입니다(``ScreenViewModel.java:1986``):

* ``mode=1`` — 사용자 중단만 아니면 통과. 열차조회(``TrainScheduleViewModel.java:5244``,
  리터럴 ``1``)가 씁니다. SDK 는 오류를 기본으로 ``ErrorBypass`` 로 바꾸므로
  (``Netfunnel.java:269-270``, ``Property.java:9`` ``err_bypass_ = true``) 대기열 서버
  장애에도 조회는 나갑니다.
* ``mode=0`` — ``EvnetCode.Success``(200)일 때만 통과. 기본값(``withNetFunnel$default``,
  ``ScreenViewModel.java:837-853``, 마스크 ``6``)이라 예약·결제가 씁니다. 300/303·오류·차단
  에서는 요청을 보내지 않고 조용히 끝납니다.

이 라이브러리의 차이
--------------------
* 차단(301/302)은 조회에서도 :class:`~korail_mobile_api.errors.KorailQueueRejectedError`
  입니다. 앱의 ``mode=1`` 조회는 차단이어도 요청을 보냅니다.
* 반납(5004)은 KORAIL 응답을 받은 **뒤** ``finally`` 에서 보냅니다. 앱은 요청을 띄운
  직후 보냅니다(동시 진행). 슬롯을 요청 한 번의 왕복만큼 더 쥡니다.
* 5002/5004 는 응답이 지목한 노드로 갑니다. 앱(SDK 기본값)은 정문에 머뭅니다 —
  :mod:`korail_mobile_api.netfunnel_safety` 참고.
* 앱에는 대기 상한이 없고 이 라이브러리도 기본은 없습니다.
  :attr:`~korail_mobile_api.config.KorailConfig.netfunnel_wait_limit` 로 둘 수 있고, 넘으면
  앱의 사용자 중단처럼 요청 없이 반납하고 :class:`~korail_mobile_api.errors.KorailNetFunnelError`
  입니다.
* ``mode=0`` 에서 앱이 조용히 멈추는 경우는 요청을 보내지 않고
  :class:`~korail_mobile_api.errors.KorailNetFunnelError` 를 냅니다.

**라이브 관측(2026-09-24, 열차조회 ``inquiry`` 관문, 비로그인 조회 두 번)**:

* 5101 → ``201:key=...`` (대기) → 5002 → ``200:key=...`` (통과) → ScheduleView → 5004 ``200``.
* 5101 → ``200:key=...`` (바로 통과) → 5002 없이 ScheduleView → 5004 ``200``.

**미검증**: 202·차단(301/302)·300/303 응답과, 예약·결제 관문(``mode=0``)의 실제 동작.
"""

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
from .netfunnel_safety import (
    assert_korail_netfunnel_key,
    assert_korail_netfunnel_origin,
    korail_netfunnel_node_url,
)

T = TypeVar("T")

_log = logging.getLogger(__name__)

#: ``Code.Success`` — ``com/netfunnel/api/Code.java:27``.
SUCCESS_CODE = "200"
#: 대기. SDK 대기 루프는 ``Code.Continue``(201)/``ContinueDebug``(202)에서만 돕니다
#: (``Netfunnel.java:622``, ``Code.java:28-29``).
CONTINUE_CODES = frozenset({"201", "202"})
#: 차단. ``EvnetCode.isBlocking()``(``Netfunnel.java:114-116``)이 참인 ``Block``(301)/
#: ``IpBlock``(302).
BLOCK_CODES = frozenset({"301", "302"})
#: ``ttl`` 을 묶는 범위. 호출부가 ``getTTL(getProperty().getMaxTTL(), 1)`` 로 부르고
#: (``Netfunnel.java:634``) ``max_ttl_`` 의 기본값이 30 입니다(``Property.java:22``).
MIN_TTL_SECONDS = 1
MAX_TTL_SECONDS = 30

#: 대기열 요청에 앱이 싣는 헤더(``com/netfunnel/api/http/Client.java:259-260``).
#: ``Context_Type`` 은 SDK 의 철자 그대로입니다.
_APP_HEADERS = {
    "Accept-Charset": "UTF-8",
    "Context_Type": "application/x-www-form-urlencoded;charset=UTF-8",
}


@dataclass(frozen=True)
class KorailNetFunnelGate:
    """대기열이 걸린 작업 하나.

    ``action`` 은 5101 의 ``aid``, ``success_only`` 는 앱의 ``mode`` 입니다 — 참이면
    ``mode=0``(200 일 때만 요청), 거짓이면 ``mode=1``(중단만 아니면 요청).
    """

    name: str
    action: str
    success_only: bool


def _gate(name: str, action: KorailNetFunnelAction, *, success_only: bool) -> KorailNetFunnelGate:
    return KorailNetFunnelGate(name, action.value, success_only)


#: 대기열이 걸린 작업 전부. 키는
#: :attr:`~korail_mobile_api.config.KorailConfig.netfunnel_actions` 가 ``aid`` 를 바꿀 때
#: 쓰는 이름입니다. ``aid`` 리터럴은 전부 보호돼 있어 길이와 호출부 이름으로 고른 값입니다
#: (:class:`~korail_mobile_api.constants.KorailNetFunnelAction`).
#:
#: * ``inquiry`` — ``act_8``, mode 1. ``TrainScheduleViewModel.netFunnelTrainSchedule``
#:   (``:5208``, 호출 ``:5244``) → ``requestTrainSchedule``(``:7216``) →
#:   ``seatMovie.ScheduleView``·``research.assignScheduleView.do``. 다음 페이지
#:   (``inquiryNextTrainSchedule``, ``:1126``)도 같은 길입니다.
#: * ``peak_season_inquiry`` — ``act_8_2``, mode 1. 같은 곳, 성수기 날(``:5225-5229``).
#: * ``product_inquiry`` — ``act_6``, mode 1. 같은 곳, ``specialOffer`` 갈래
#:   (``:5213-5215``) → ``seatMovie.ScheduleViewSpecial``. aid·라우트 대응 모두 **추정**.
#: * ``reserve`` — ``act_14``, mode 0. ``netFunnelTicketReservation``
#:   (``TrainScheduleViewModel.java:5104``, ``TrainSeatMapViewModel.java:2719``,
#:   ``HomeViewModel.java:6231``, ``ReservationWaitViewModel.java:578``) →
#:   ``certification.TicketReservation``·``reservation.seatAssign.do``;
#:   ``netFunnelNonMemTicket``(``TrainScheduleViewModel.java:5003``,
#:   ``TrainSeatMapViewModel.java:2627``) → ``nonMember.NonMemTicket``.
#: * ``pay`` — ``act_18``, mode 0. ``PayViewModel.executePayment``(``:6724``) →
#:   ``payment.ReservationPayment``·``pay.intgStl.do``·``pass.passPayIssue``·
#:   ``pass.passOtrPayIssue``; ``FPayViewModel.java:795`` → ``payment.ReservationPayment``.
#: * ``reservation_view`` — ``act_21``, mode **미검증**(0 으로 둠, ``mode`` 인자가 보호됨).
#:   ``MyReservationViewModel.reqReservationView``(``:2528``) →
#:   ``reservation.ReservationView``.
#:
#: 대기열을 거치지 않는 것: 관광열차 조회(``getTour()`` 면 aid 가 ``""`` 이고 곧바로
#: ``requestTrainSchedule``, ``TrainScheduleViewModel.java:5216-5242``), 병합예약
#: (``ReservationMergeViewModel`` 에 ``withNetFunnel`` 호출 없음), 예약대기 옵션
#: (``reservationWait.ReservationWait``), 환불·취소·장바구니 등 나머지 전부.
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

    ``node`` 는 응답이 지목한 노드 origin(없으면 ``""``), ``raw`` 는 받은 본문입니다.
    """

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
        """다음 5002 까지 잘 시간 — ``ttl`` 을 [1, 30] 으로 묶은 값(``Response.java:59-66``)."""
        ttl = _digits(self.params.get("ttl", ""))
        return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


def _digits(raw: str) -> int:
    return int(raw) if raw.isascii() and raw.isdigit() else 0


def parse_netfunnel_body(body: str) -> KorailNetFunnelToken:
    """응답 본문을 코드와 파라미터로 가릅니다(``Response.Parser``, ``Response.java:128-163``).

    첫 ``:`` 앞이 코드, 뒤가 ``&`` 로 나뉜 ``name=value`` 쌍입니다. ``:`` 가 없거나 코드가
    숫자가 아니면 :class:`~korail_mobile_api.errors.KorailNetFunnelError`(앱의
    ``Code.ErrorData``)입니다. 서버가 준 ``key`` 와 ``ip``/``port`` 는
    :mod:`~korail_mobile_api.netfunnel_safety` 의 가드를 통과해야 합니다.
    """
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
    if key:
        assert_korail_netfunnel_key(key)
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
    """대기열 전용 HTTP 클라이언트. ``nf.letskorail.com`` 과 그 노드의 ``/ts.wseq`` 만 부릅니다.

    ``sleeper``/``clock`` 은 시험에서 대기를 건너뛰려고 바꿔 끼우는 자리입니다.
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
        assert_korail_netfunnel_origin(config.netfunnel_url)
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
        """대기열을 통과한 뒤 ``send()`` 를 부르고, 어떻게 끝나든 키를 반납합니다.

        통과하지 못하면 ``send`` 를 부르지 않습니다 — 차단(301/302)은
        :class:`~korail_mobile_api.errors.KorailQueueRejectedError`, 그 밖은
        :class:`~korail_mobile_api.errors.KorailNetFunnelError` 입니다. ``mode=1`` 관문은
        대기열 요청 자체가 실패하면(앱의 ``ErrorBypass``) 키 없이 ``send`` 로 넘어갑니다.
        반납(5004)은 ``finally`` 에서 한 번 보내고 실패는 로그로만 남깁니다(앱과 같음).
        """
        if isinstance(gate, str):
            gate = self.gate(gate)
        slot = _Slot()
        try:
            self._admit(gate, slot)
            return send()
        finally:
            self._complete(slot)

    # ------------------------------------------------------------------

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
        """한 명령을 보내고 파싱합니다. 실패하면 앱처럼 다시 보냅니다.

        ``_run``(``Netfunnel.java:280-374``)은 실패한 시도 뒤 그 시도의 시작부터 타임아웃이
        찰 때까지 자고(``:352-358``) 다시 보냅니다. 재시도 횟수 ``retry_acount`` 는 인스턴스
        필드라 ``Begin`` 에서만 0 이 되고(``:593``) 명령 사이에 공유됩니다(``:360-363``) —
        KORAIL 의 ``retry=1`` 은 대기열 세션 전체에서 한 번입니다.
        """
        while True:
            started = self._clock()
            try:
                return parse_netfunnel_body(self._get(url))
            except (KorailTransportError, KorailNetFunnelError):
                if slot.retries_left <= 0:
                    raise
                slot.retries_left -= 1
                remaining = self.config.netfunnel_timeout - (self._clock() - started)
                if remaining > 0:
                    self._sleep(remaining)

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
                # The SDK would keep sleeping and skip every 5002
                # (CommandClient.java:104-108 returns early on an empty key).
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
                # Netfunnel.java:654-664: a failed 5002 is ErrorCheckEnter, which
                # notice() turns into ErrorBypass.
                self._error_bypass(gate, exc)
                return
            slot.token, slot.node = token, token.node or slot.node
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
        """5004 — 가장 최근 응답의 키를 반납합니다. 키가 없으면 보내지 않습니다.

        ``End(Integer)``(``Netfunnel.java:848-880``)와 ``CommandClient.Complete``
        (``CommandClient.java:158-199``)처럼 재시도하지 않고 응답을 읽지 않으며, 실패는
        무시합니다(여기서는 경고 로그).
        """
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
