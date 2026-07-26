"""The NetFunnel virtual waiting room (``nf.letskorail.com``).

WHY THIS EXISTS AT ALL. Every live call this repository has ever made to
``smart.letskorail.com`` succeeded WITHOUT a NetFunnel token, so the server does
not presently enforce the queue on us. The app nonetheless wires it on the
inquiry, reserve, pay and 예약목록 paths, and it carries a *dedicated
peak-season inquiry action* (``act_8_2``) — which is exactly the load at which a
client with no way to wait its turn starts failing. This module is the way to
wait, and it is **off by default** (:attr:`~korail_mobile_api.config.
KorailConfig.netfunnel_enabled`); see that field for why.

THE BIG ONE: KORAIL DOES NOT SPEAK THE JAVASCRIPT DIALECT.
==========================================================
``nf.letskorail.com`` serves both KORAIL and SRT, and the sibling
``srt-mobile-api`` implementation of this same product is live-verified. It is
prior art, but it is **not a template**, because the two apps embed two
different NetFunnel client SDKs:

* SRT is a WebView over ``netfunnel.js``, so it sends the browser dialect:
  ``&nfid=0&prefix=NetFunnel.gRtype=5002;&js=yes&<epochMillis>``, and gets back
  a JavaScript assignment ``NetFunnel.gRtype=…;NetFunnel.gControl.result=
  '5002:200:key=…'``.
* KORAIL embeds STCLab's **native Android SDK** (the ``T6``/``U6`` packages),
  and it sends none of that.

Everything below is read off the native SDK, which is the only NetFunnel client
in ``korail.apk``. Four consequences, each one a place where following SRT would
have produced a request KORAIL's own app never sends:

1. **No ``js``, no ``nfid``, no ``prefix``, no trailing epoch.** ``T6/d.java``
   builds each request with ``U6.a.addParam`` calls and there are only ever two
   or three of them (:30-31, :54-55, :78-79, :99-101). ``U6/a.java`` then does
   ``URLEncodedUtils.format(params, "utf-8")`` and appends it, so the query is
   exactly the parameters that were added, in the order they were added.
2. **``sid``/``aid`` ride on 5101 ONLY.** ``GetTidCacekedEnter``
   (``T6/d.java:99-101``) is the single builder that adds them. ``CheckedEnter``
   (:54-55) does not — which is the opposite of the JS dialect, where 5002
   carries them and only 5004 drops them. Here *both* 5002 and 5004 are bare
   ``opcode``+``key``.
3. **``ttl`` is never sent back.** In the JS dialect the ttl from a 201 is
   echoed on the next ``chkEnter``. The native SDK reads ttl only to decide how
   long to sleep (``T6/g.java:462``, ``Thread.sleep(ttl * 1000)`` at :467) and
   never puts it on the wire. So ttl here is purely a client-side hint.
4. **The response is ``<code>:<params>``, not ``<rtype>:<code>:<params>``.**
   ``T6/i.java:36-43`` takes ``indexOf(":")``, ``parseInt``\\ s everything before
   it as *the status code*, and splits the remainder on ``&``. Feed it the JS
   dialect's ``5002:200:key=…`` and it parses the code as 5002 — which
   ``T6/a.toEnum`` maps to ``None`` — and finds no key. The app can only work
   with the bare form, so that is the only form parsed here.

That last point used to be the one thing in this module that had never been seen
on the wire. **A live probe on 2026-07-26 confirmed it**: ``nf.letskorail.com``
answers a ``js``-less native-SDK request with exactly ``<code>:<params>`` —
``200:key=…&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=…`` — and never with a
``NetFunnel.gRtype=…`` assignment. :func:`parse_netfunnel_body` still names the
JavaScript dialect in its error message, but now as a diagnosis for a server that
changed rather than as an admission that we were guessing.

THE ENTRY SEQUENCE IS 5101 → 5002 → 5004, AND 5101 ALONE IS NOT A SESSION
========================================================================
The same 2026-07-26 probe settled a second question, and the answer contradicts
the obvious reading of the APK. **The key 5101 hands out is a ticket to enter,
not a session that can be completed.** Sending it straight to ``setComplete``
fails::

    GET opcode=5101&sid=service_1&aid=act_8
     -> 200:key=<252 hex chars>&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=…
    GET opcode=5004&key=<that key>
     -> 503:msg="Wrong Server ID"          # and adding sid/aid does not help

Only a key that ``chkEnter`` issued is completable, and ``chkEnter`` issues a new
and *shorter* one::

    GET opcode=5002&key=<the 5101 key>
     -> 200:key=<a DIFFERENT, shorter key>&…
    GET opcode=5004&key=<the 5002 key>
     -> 200:key=&nwait=0&…&chk_enter_cnt=0&…

So every step's key **supersedes** the previous one, and :meth:`
KorailNetFunnelClient.acquire` always performs the 5002 before handing a token
back — even when 5101 answered 200 with nobody in line.

``503:msg="Wrong Server ID"`` is a misleading message for "this key is not a
completable session"; :data:`NOT_COMPLETABLE_CODE` names it so that a regression
here reports its own cause instead of the server's.

**WHERE THE APK DISAGREES.** Read literally, ``T6/g.java`` does *not* do this.
Its poll loop (the ``a`` Runnable, :77-129) enters at ``GetTidCacekedEnter`` and
leaves the loop the moment the code is not Continue/ContinueDebug — the smali
(``T6/g$a.smali``, ``:243-247`` then ``:282`` → ``goto :goto_3`` → ``:892``)
confirms the fall-through is a return — so on a 200 from 5101 the app issues **no
5002 at all** and completes with the 5101 key. The live server wins over that
reading, and the most likely reconciliation is the redirection this module
declines: ``T6/d.makeURL`` (``T6/d.java:17-19``) sends ``chkEnter`` and
``setComplete`` to the ``ip``/``port`` the previous reply named, and the 5101
reply names one. "Wrong Server ID" is then literally true — the front door does
not own a session that a queue node issued. Since we stay pinned to the front
door (see below), we must obtain a key the front door *does* own, and ``chkEnter``
is what issues it.

What the APK does corroborate is the supersession itself: ``T6/d.java`` keeps one
response object and every opcode overwrites it — ``this.f5141b = iVarParser.
m184clone()`` at :61 (chkEnter) and :107 (getTidChkEnter) — while ``Complete()``
sends ``this.f5141b.getKey()`` (:79), i.e. whatever key arrived last. The app has
no notion of "the original key" either.

WHAT THE APP DOES THAT WE DELIBERATELY DO NOT
=============================================
``T6/d.java:17-19`` (``makeURL``) sends ``chkEnter``/``aliveNotice``/
``setComplete`` to the ``ip``/``port`` a previous response named, unless
``host_notmodify`` is set — and it is false by default (``T6/h.java:43``) and
never set by ``KTApplication``. We do not follow that redirection. The whole
client is pinned to canonical origins, and following a server-named host means
letting a response choose where the next request goes. Our own 2026-07-26 probe
is the evidence that we do not have to — the front door released a ``chkEnter``
key perfectly well, and answered with an ``ip`` of ``rnf13.letskorail.com`` that
we simply ignored — and the sibling SRT run said the same before it. The price of
staying pinned is exactly the extra 5002 documented above.

``AliveNotice`` (5003) is likewise not implemented. It exists to keep a visible
waiting-room popup alive (``T6/g.java:517-527``); this library renders no popup
and holds no slot longer than one bounded operation.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
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
from .safety import assert_korail_netfunnel_origin, assert_netfunnel_request


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
#: A pass. 200 issues a key; 300 means the queue was bypassed and there is none.
SUCCESS_CODES = frozenset({SUCCESS_CODE, BYPASS_CODE})
#: Still queued — ``T6/g.java:451`` loops on exactly these two.
CONTINUE_CODES = frozenset({"201", "202"})
#: ``TsErrorAComplete``. Accepted for setComplete only; see
#: :func:`parse_set_complete_response` for why that is an inference.
ALREADY_COMPLETE_CODE = "502"
#: What the live server answers when ``setComplete`` is handed a key that is not
#: a completable session — in practice, the 5101 ticket instead of the key
#: ``chkEnter`` issued for it. The wire message is ``msg="Wrong Server ID"``,
#: which is misleading enough to be worth naming: it is not a routing complaint
#: that a different host would satisfy (the probe re-sent it with ``sid``/``aid``
#: attached and got the same answer). It is REFUSED, never accepted alongside
#: 502 — treating it as "released" is exactly how a slot leaks silently.
NOT_COMPLETABLE_CODE = "503"
#: ``TsBlock``/``TsIpBlock``. The waiting room refused us, which is a different
#: fact from the waiting room malfunctioning — ``T6/g.d.isBlocking()``
#: (``T6/g.java:892-894``) gives the pair its own predicate, distinct from
#: ``isError()`` three lines below it. Both still raise, because a refusal is
#: not a wait and a wait is the only non-failure that is not a pass; they raise
#: :class:`~korail_mobile_api.errors.KorailQueueRejectedError` so a caller can
#: tell them apart without reading the numeric code.
#:
#: ``TsExpressNumber`` (303) is deliberately NOT mapped here: the app counts it
#: as a SUCCESS (``T6/g.d.isSuccess()``, :909, lists ``ExpressNumber``), we have
#: never seen one, and folding an admission into a refusal would be worse than
#: leaving it in the generic error path.
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
    """One parsed NetFunnel reply.

    ``key`` is the queue slot's identifier and the ONLY thing that identifies it
    on the follow-up requests — ``chkEnter`` and ``setComplete`` send nothing
    else (``T6/d.java:54-55``, :78-79).

    A token is one REPLY, not one session: each reply's key supersedes the last,
    so the key here is only good for the *next* request. The 5101 ticket is
    spent by ``chkEnter``, and every 201 poll reissues the key again. Holding on
    to an earlier token and releasing that is the defect this type's immutability
    is meant to make obvious — :meth:`KorailNetFunnelClient.acquire` returns the
    latest token and that is the only one ``setComplete`` will accept.
    """

    action: str
    key: str
    code: str
    params: dict[str, str] = field(default_factory=dict)

    @property
    def wait_count(self) -> int:
        """``nwait`` — how many are ahead of us. 0 when the queue is idle."""
        raw = self.params.get("nwait", "")
        return int(raw) if raw.isdigit() else 0


def _netfunnel_url(netfunnel_url: str, params: Sequence[tuple[str, str]]) -> str:
    """Assemble and GUARD one queue URL.

    The guard runs on the ordered pairs before they are encoded, so the
    per-opcode contract in :mod:`korail_mobile_api.safety` is checked against the
    parameter names, values *and order* rather than against a re-parsed query
    string.
    """
    assert_korail_netfunnel_origin(netfunnel_url)
    assert_netfunnel_request("GET", KORAIL_NETFUNNEL_PATH, params)
    return (
        f"{netfunnel_url.rstrip('/')}{KORAIL_NETFUNNEL_PATH}"
        f"?{urlencode(params)}"
    )


def get_tid_chk_enter_params(
    action: str,
    *,
    service_id: str = KORAIL_NETFUNNEL_SERVICE_ID,
) -> tuple[tuple[str, str], ...]:
    """``opcode``, ``sid``, ``aid`` — in that order.

    ``T6/d.java:99-101`` adds exactly these three and nothing else, and
    ``U6/a.addParam`` appends to an ``ArrayList`` (``U6/a.java:57-63``) that
    ``URLEncodedUtils.format`` then walks in order, so the order is the app's.
    """
    return (
        ("opcode", KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value),
        ("sid", service_id),
        ("aid", str(action)),
    )


def chk_enter_params(key: str) -> tuple[tuple[str, str], ...]:
    """``opcode``, ``key``. No ``sid``, no ``aid``, no ``ttl``.

    ``T6/d.java:54-55``. This is the parameter list that most obviously diverges
    from the JavaScript dialect, where 5002 carries the service/action pair and
    echoes the previous 201's ttl.
    """
    if not key:
        raise ValueError("chkEnter requires the key the queue issued")
    return (
        ("opcode", KorailNetFunnelOpcode.CHK_ENTER.value),
        ("key", key),
    )


def set_complete_params(key: str) -> tuple[tuple[str, str], ...]:
    """``opcode``, ``key`` — "I am done, release my slot" (``T6/d.java:78-79``).

    Sending this is not optional politeness. Without it our place in line is held
    until the server times it out, and at peak load that is queue pollution we
    caused. The app releases automatically too: ``NetfunnelDao.runRunner()``
    calls ``T6.g.END()`` (``com/korail/talk/network/NetfunnelDao.java:41``) from
    ``BaseDaoHelper``'s ``onPostExecute`` (:105-107) — i.e. after the gated call
    has returned, on the success and the failure path alike, because
    ``onPostExecute`` runs either way.
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
    """The 5101 URL: "put me in line for ``action``"."""
    return _netfunnel_url(
        netfunnel_url,
        get_tid_chk_enter_params(action, service_id=service_id),
    )


def build_chk_enter_url(netfunnel_url: str, *, key: str) -> str:
    """The 5002 URL: "am I admitted yet?"."""
    return _netfunnel_url(netfunnel_url, chk_enter_params(key))


def build_set_complete_url(netfunnel_url: str, *, key: str) -> str:
    """The 5004 URL: "I am done, release my slot"."""
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
    """Split a native-SDK reply into code and parameters, judging neither.

    Mirrors ``T6/i.Parser`` (``T6/i.java:35-63``): everything before the first
    ``:`` is the status code, the remainder splits on ``&`` into ``name=value``
    pairs. Each caller below applies its own status policy on top, because
    "success" is not one set of codes — it depends on which request the reply
    answers.

    The app parses the value half with ``split("=")`` and takes element ``[1]``,
    which would truncate a value containing ``=``; this splits once so such a
    value survives intact. That is strictly more faithful to the wire than to the
    decompiled Java, and no NetFunnel parameter is known to contain one.
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
    """A 5101/5002 reply, including "still queued".

    Returns the token for a pass (200/300) **and** for a wait (201/202); the
    caller separates them with :func:`is_queued`. Everything else raises — 301
    and 302 as :class:`~korail_mobile_api.errors.KorailQueueRejectedError`, the
    rest as :class:`~korail_mobile_api.errors.KorailNetFunnelError`.

    A wait is not required to echo a key: we already hold one, and refusing a
    wait over a missing echo would abort an operation that was merely queued.
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
    """A 5004 reply. Accepts 200 (released) and 502 ("already complete").

    **The 502 acceptance is our inference and is labelled as such.** The app does
    not state it: ``T6/d.Complete()`` (``T6/d.java:69-88``) does not even look at
    the reply — it calls ``execute()`` and clears its state regardless — so the
    APK has no opinion to copy. Our caller's question is "is my slot released?",
    and both 200 and ``TsErrorAComplete`` answer yes.

    **No key is required in the reply, and a successful release does not send
    one.** The live 2026-07-26 release answered
    ``200:key=&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=rnf13.letskorail.com&
    port=443&…&chk_enter_cnt=0&…`` — an EMPTY ``key=``, which is the server
    saying the slot is gone rather than a truncated body. This deliberately does
    not run :func:`_require_pass_key`: an empty key is a success here and only a
    failure on 5101/5002, where the key is the whole point of the reply.

    :data:`NOT_COMPLETABLE_CODE` gets a message of its own because the server's
    is actively misleading. Everything else keeps the generic one.
    """
    token = parse_netfunnel_body(body, action=action)
    if token.code == NOT_COMPLETABLE_CODE:
        raise _queue_failure(
            token,
            "KORAIL NetFunnel setComplete refused this key as a session to "
            "release; the server calls that 'Wrong Server ID' but it means the "
            "key was never exchanged for one, which is what chkEnter (5002) "
            "does — a slot entered as 5101 -> 5002 releases with the key 5002 "
            "issued, never with the 5101 ticket",
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
    """Whether the queue said "come back later" (Continue/ContinueDebug)."""
    return token.code in CONTINUE_CODES


def queue_wait_seconds(token: KorailNetFunnelToken) -> int:
    """How long to sleep before the next ``chkEnter``, clamped as the app clamps.

    ``T6/i.java:175-181`` with ``max_ttl=30``, ``min=1`` — see
    :data:`MAX_TTL_SECONDS`. The value is NOT sent back to the server; unlike the
    JavaScript dialect, the native SDK keeps ttl entirely client-side.
    """
    raw = token.params.get("ttl", "")
    ttl = int(raw) if raw.isdigit() else 0
    return max(MIN_TTL_SECONDS, min(ttl, MAX_TTL_SECONDS))


class KorailNetFunnelClient:
    """A bounded client for the waiting room, pinned to ``nf.letskorail.com``.

    Deliberately a SEPARATE client from
    :class:`~korail_mobile_api.http.KorailHttpClient`: that one is pinned to
    ``smart.letskorail.com`` by ``assert_korail_origin`` and must stay that way,
    and this one can reach nothing but ``/ts.wseq`` on the queue host. Neither
    can be used to reach the other's origin.
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
            # A queue reply names another queue node in ``ip``/``port`` and the
            # app follows it (``T6/d.java:17-19``); we do not, and a redirect is
            # the same hazard by another name.
            follow_redirects=False,
            transport=transport,
        )

    def close(self) -> None:
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
        """5101 — take a TICKET for ``action``. May return a WAIT token.

        The key this returns is not yet a session: it is what :meth:`check`
        exchanges for one, and ``setComplete`` refuses it
        (:data:`NOT_COMPLETABLE_CODE`). Callers who want a slot they can release
        want :meth:`acquire`, which performs the exchange.
        """
        body = self._get(
            build_get_tid_chk_enter_url(
                self.config.netfunnel_url,
                action=action,
            )
        )
        return parse_queue_response(body, action=str(action))

    def check(self, action: str, key: str) -> KorailNetFunnelToken:
        """5002 — enter with ``key``, or ask again. May return a WAIT token.

        This is both halves of the same opcode: the first call exchanges the
        5101 ticket for a completable session, and each later call re-asks with
        whatever key the previous 201 issued. Either way the reply's key
        supersedes ``key``, so the caller must carry the returned token forward
        rather than the one it passed in.
        """
        body = self._get(
            build_chk_enter_url(self.config.netfunnel_url, key=key)
        )
        return parse_queue_response(body, action=str(action))

    def release(self, token: KorailNetFunnelToken) -> None:
        """5004 — release the slot. Raises if the server did not release it.

        This RAISES rather than swallowing, and that is the whole point. The
        sibling SRT implementation guarded its key against a 128-character bound
        while real keys are 256, so every release request was rejected before it
        was sent — and because the failure was swallowed, every slot leaked
        silently until a live run exposed it. A release that cannot be sent must
        be audible.

        A token with no key is a bypass (300) and there is nothing to release, so
        that returns without sending — the same condition ``T6/d.Complete()``
        short-circuits on (``T6/d.java:70-73``, ``getKey().length() < 1``). That
        short-circuit is deliberately narrowed to a bypass: "no key" is a
        legitimate state for exactly one status code, and letting any other
        keyless token take the silent path would rebuild the leak from the other
        end — the request would not merely be refused, it would never be built.
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
            build_set_complete_url(self.config.netfunnel_url, key=token.key)
        )
        parse_set_complete_response(body, action=token.action)

    def acquire(self, action: str) -> KorailNetFunnelToken:
        """Take a ticket, enter with it, and poll until admitted, within bounds.

        The full sequence, which is 5101 → 5002 and NOT 5101 alone::

            enter(action)          # 5101, issues the ticket
            check(action, key)     # 5002, exchanges it for a session
            ...                    # more 5002s while the answer is 201/202
            -> the token whose key setComplete will accept

        The 5002 is unconditional. A 5101 that answers 200 with ``nwait=0`` has
        still only issued a ticket, and releasing that ticket fails with
        :data:`NOT_COMPLETABLE_CODE` — see the module docstring for the live
        transcript. The single exception is a bypass (300), which issues no key
        because there is no line to stand in and so has nothing to exchange.

        Returns the passing token (200 or 300), whose key is the LATEST one the
        server issued — every reply supersedes its predecessor, so the caller
        must release this token and not an earlier one. A 201 that echoes no key
        leaves the last known key in force, because a wait is not a revocation.

        Raises :class:`~korail_mobile_api.errors.KorailNetFunnelError` if the
        queue is still holding us after :data:`QUEUE_POLL_LIMIT` polls or
        :data:`QUEUE_WAIT_LIMIT_SECONDS` seconds, whichever comes first. That
        give-up leaves the slot to the server's own timeout: :meth:`slot` never
        received a token, so it has nothing to release, and the current key is
        put on the error's ``raw`` for a caller who wants to release it by hand.
        """
        token = self.enter(action)
        if not token.key:
            # A bypass. No ticket was issued, so there is nothing to exchange
            # and nothing to release — T6/d.Complete() short-circuits on the
            # same emptiness (T6/d.java:70-73).
            return token
        # The key rides alongside the token because a 201 is allowed to omit it
        # and we must not send an empty one to the next chkEnter.
        key = token.key
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
            token = self.check(action, key)
            key = token.key or key
            if not is_queued(token):
                return token

    @contextmanager
    def slot(self, action: str) -> Iterator[KorailNetFunnelToken]:
        """Hold a queue slot for the duration of one operation, then release it.

        ``with client.slot(KorailNetFunnelAction.INQUIRY): ...``

        The release happens on BOTH paths, which is what the app does
        (``BaseDaoHelper.java:105-107`` runs it from ``onPostExecute``, i.e.
        whether or not the gated call raised). The two paths differ only in how
        loud a *failed* release is allowed to be:

        * body succeeded — a failed release RAISES. Nothing else is in flight to
          mask, and a silently leaked slot is the bug this module was written
          against.
        * body raised — the release is still attempted, but its own failure is
          attached as a note to the caller's exception instead of replacing it.
          The caller's error is the one they need; the leak is recorded, not
          hidden.
        """
        token = self.acquire(action)
        try:
            yield token
        except BaseException as exc:
            try:
                self.release(token)
            except Exception as release_error:  # noqa: BLE001 - see docstring
                exc.add_note(
                    "KORAIL NetFunnel slot release also failed and the slot may "
                    f"be held until the server times it out: {release_error}"
                )
            raise
        self.release(token)


#: Which action id gates which operation, as the app pairs them. Each entry is
#: an APK call site, and none of them is a guess:
#:
#: * ``INQUIRY``/``PEAK_SEASON_INQUIRY``/``PRODUCT`` — ``b5/c.java:439``, the
#:   열차조회 path, which picks between all three on one line. See
#:   :func:`inquiry_action` for the rule.
#: * ``RESERVE`` — ``com/korail/talk/ui/inquiry/rir/orr/
#:   DirectInquiryActivity.java:442``, :469 and :499 (예약대기, 일반 예약 and the
#:   공무원 인증 variant all gate on ``act_14``).
#: * ``PAY`` — ``B6/AbstractC1269e.java:1046`` and ``B6/C1270f.java:232``.
#: * ``RESERVED`` — ``com/korail/talk/ui/menu/ReservedTicketActivity.java:553``,
#:   the 예약목록 read.
#: * ``TEST`` — ``com/korail/talk/test/NetfunnelTestActivity.java:54`` gates on
#:   ``act_8``, NOT on ``act_4``; ``act_4`` and ``act_22`` are declared in
#:   ``K4/g.java:47,50`` and used at ZERO call sites in the APK. They are exposed
#:   because the app declares them, and their absence from this map is the
#:   statement that nothing in the app reaches them.
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
    """Pick the 열차조회 action the way the app picks it.

    ``b5/c.java:439`` is one conditional expression::

        request instanceof ProductTrainInquiryRequest
            ? NETFUNNEL_ACTION_PRODUCT_ID                       // act_6
            : isPeakSeason(getCalendarInfo(y0()))
                ? NETFUNNEL_ACTION_ID_PEAKSEASON                // act_8_2
                : NETFUNNEL_ACTION_ID                           // act_8

    and ``MainBookingActivity.java:749`` / ``OldMainBookingActivity.java:321``
    repeat the peak-season half for the 간편구매 flow. So the choice is made per
    *departure date*, on the client, before any request goes out.

    **``isPeakSeason`` is server data, not a calendar rule.**
    ``S4/C0805e.java:116-121`` answers from ``f4891k``, an ``AvailableDates``
    built at :199-201 from every ``RunningCalendar`` row whose ``isPeakSeason()``
    is true — i.e. from the ``schedule.runDt`` 열차운행달력 response this library
    already reads as
    :meth:`~korail_mobile_api.client.KorailClient.get_train_calendar`. It is
    therefore a *lookup*, and there is nothing to reimplement: before the
    calendar has been fetched the app's own answer is ``false`` (:117 returns
    false on a null table), which is why this takes the flag rather than a date.

    That makes ``act_8_2`` the reason this module exists. ``act_8`` and
    ``act_8_2`` are separate actions on the same service, so they are separate
    queues: at peak load the ordinary inquiry queue is the one that engages, and
    a caller who has read the calendar can ask for the peak-season line instead
    of waiting in the wrong one.
    """
    return (
        KorailNetFunnelAction.PEAK_SEASON_INQUIRY
        if peak_season
        else KorailNetFunnelAction.INQUIRY
    )
