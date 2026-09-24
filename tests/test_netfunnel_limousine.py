"""F5, baseline 291e01c. Run after changes.patch with PYTHONPATH=src.

No live server evidence is produced here. MockTransport responses and identifiers
are synthetic. App-parity cases cite supplied 7.0.6 Java/smali; library-policy
cases are explicitly labelled and must not be read as decrypted app constants.
"""
from __future__ import annotations

import ast
import inspect
import socket
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.errors import (
    KorailApiError, KorailAuthError, KorailNetFunnelError,
    KorailProtocolError, KorailQueueRejectedError, KorailTransportError,
)
from korail_mobile_api.limousine_models import (
    LimousineSchedule, LimousineScheduleQuery, LimousineSeatInventoryQuery,
)
from korail_mobile_api.limousine_parsers import (
    parse_limousine_schedule_response, parse_limousine_seat_inventory_response,
)
from korail_mobile_api.limousine_payloads import (
    build_limousine_schedule_form, build_limousine_seat_inventory_form,
)
from korail_mobile_api.models import BaseKorailResponse, KorailSession
from korail_mobile_api.mutation_models import KorailPassengerCounts
from korail_mobile_api.mutation_payloads import build_limousine_reservation_form
from korail_mobile_api.netfunnel import (
    KORAIL_NETFUNNEL_GATES, KorailNetFunnelClient, KorailNetFunnelGate,
    parse_netfunnel_body,
)
from korail_mobile_api.netfunnel_safety import korail_netfunnel_node_url


@pytest.fixture(autouse=True)
def block_real_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("F5: real network is forbidden; use MockTransport")
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", deny)


def test_network_guard() -> None:
    with pytest.raises(AssertionError, match="real network"):
        socket.getaddrinfo("never-resolve.invalid", 443)
    with httpx.Client() as client:
        with pytest.raises(AssertionError, match="real network"):
            client.get("https://never-send.invalid/")


@dataclass
class Clock:
    now: float = 0.0
    overshoot: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0
        self.sleeps.append(seconds)
        self.now += seconds + self.overshoot


@dataclass
class Reply:
    text: str = "200:key=SYNTHETIC-KEY"
    delay: float = 0.0
    error: str | None = None
    status: int = 200


class QueueWorld:
    def __init__(self, clock: Clock, replies: list[Reply], complete: Reply) -> None:
        self.clock = clock
        self.replies = list(replies)
        self.complete = complete
        self.events: list[tuple[str, str, dict[str, str], float]] = []
        self.requests: list[httpx.Request] = []
        self.sent = 0

    def handler(self, request: httpx.Request) -> httpx.Response:
        assert request.method == "GET" and request.url.path == "/ts.wseq"
        self.requests.append(request)
        params = dict(request.url.params)
        op = params["opcode"]
        self.events.append((op, request.url.host, params, self.clock()))
        if op == "5004":
            reply = self.complete
        else:
            assert self.replies, "Unexpected extra queue request"
            reply = self.replies.pop(0)
        self.clock.now += reply.delay
        if reply.error == "read":
            raise httpx.ReadTimeout("synthetic read timeout", request=request)
        if reply.error:
            raise httpx.ConnectError("synthetic connect error", request=request)
        return httpx.Response(reply.status, text=reply.text)

    def send(self) -> str:
        self.sent += 1
        self.events.append(("API", "api.invalid", {}, self.clock()))
        return "SYNTHETIC-RESULT"

    def ops(self) -> list[str]:
        return [event[0] for event in self.events]


@pytest.fixture
def queue_factory():
    clients: list[KorailNetFunnelClient] = []

    def make(
        replies: list[Reply], *, mode: int = 0, limit: float | None = None,
        complete: Reply | None = None, overshoot: float = 0.0,
    ):
        clock = Clock(overshoot=overshoot)
        world = QueueWorld(clock, replies, complete or Reply(text="unparsed completion"))
        config = KorailConfig(netfunnel_timeout=3.0, netfunnel_wait_limit=limit)
        client = KorailNetFunnelClient(
            config, transport=httpx.MockTransport(world.handler),
            sleeper=clock.sleep, clock=clock,
        )
        clients.append(client)
        gate = KorailNetFunnelGate("synthetic", "SYNTHETIC-AID", mode == 0)
        return client, gate, world, clock

    yield make
    for client in clients:
        client.close()


@pytest.mark.parametrize("mode", [0, 1])
def test_immediate_pass_and_release(queue_factory, mode: int) -> None:
    """CommandClient.java:40-80,158-199; SDK 5101/5004, callback order is library policy."""
    client, gate, world, clock = queue_factory([Reply()], mode=mode)
    assert client.run(gate, world.send) == "SYNTHETIC-RESULT"
    assert world.ops() == ["5101", "API", "5004"]
    assert world.events[0][2] == {
        "opcode": "5101", "sid": "service_1", "aid": "SYNTHETIC-AID",
    }  # sid is the library default, NOT a recovered KORAIL app literal.
    assert world.events[2][2] == {"opcode": "5004", "key": "SYNTHETIC-KEY"}
    assert clock.sleeps == []
    assert world.requests[0].headers["Accept-Charset"] == "UTF-8"
    assert world.requests[0].headers["Context_Type"] == "application/x-www-form-urlencoded;charset=UTF-8"


@pytest.mark.parametrize("code", ["201", "202"])
@pytest.mark.parametrize("ttl,expected", [("0", 1), ("1", 1), ("7", 7), ("300", 30)])
def test_wait_pass_ttl_and_latest_key(queue_factory, code: str, ttl: str, expected: int) -> None:
    """Netfunnel.java:622-664; Response.java:59-66; CommandClient.java:110-137."""
    client, gate, world, clock = queue_factory([
        Reply(f"{code}:key=SYNTHETIC-OLD&ttl={ttl}&nwait=5"),
        Reply("200:key=SYNTHETIC-NEW"),
    ])
    client.run(gate, world.send)
    assert world.ops() == ["5101", "5002", "API", "5004"]
    assert world.events[1][2] == {"opcode": "5002", "key": "SYNTHETIC-OLD"}
    assert world.events[-1][2] == {"opcode": "5004", "key": "SYNTHETIC-NEW"}
    assert clock.sleeps == [expected]


@pytest.mark.parametrize("code", ["301", "302"])
@pytest.mark.parametrize("mode", [0, 1])
def test_block_is_never_bypassed(queue_factory, code: str, mode: int) -> None:
    """Library policy: stricter than ScreenViewModel.java:1986, keep block rejection."""
    client, gate, world, _ = queue_factory([Reply(f"{code}:key=SYNTHETIC-BLOCK")], mode=mode)
    with pytest.raises(KorailQueueRejectedError) as raised:
        client.run(gate, world.send)
    assert str(raised.value.code) == code
    assert world.sent == 0
    assert world.ops() == ["5101", "5004"]


@pytest.mark.parametrize("code", ["300", "303", "500"])
@pytest.mark.parametrize("mode", [0, 1])
def test_terminal_non_success_modes(queue_factory, code: str, mode: int) -> None:
    """ScreenViewModel.java:1986; Code.java:30-33. No live bypass claim."""
    client, gate, world, _ = queue_factory([Reply(f"{code}:key=SYNTHETIC-END")], mode=mode)
    if mode == 0:
        with pytest.raises(KorailNetFunnelError):
            client.run(gate, world.send)
        assert world.sent == 0
    else:
        client.run(gate, world.send)
        assert world.sent == 1
    assert world.ops()[-1] == "5004"


@pytest.mark.parametrize("kind", ["connect", "read", "http", "parse"])
@pytest.mark.parametrize("mode", [0, 1])
def test_error_bypass_modes(queue_factory, kind: str, mode: int) -> None:
    """Netfunnel.java:263-276,352-363; ScreenViewModel.java:1986; read retry is library policy."""
    reply = {"connect": Reply(error="connect"), "read": Reply(error="read"),
             "http": Reply(status=503), "parse": Reply(text="not a queue response")}[kind]
    client, gate, world, clock = queue_factory([reply, reply], mode=mode)
    if mode == 0:
        with pytest.raises(KorailNetFunnelError):
            client.run(gate, world.send)
    else:
        client.run(gate, world.send)
    assert world.sent == mode
    assert world.ops() == ["5101", "5101"] + (["API"] if mode else [])
    assert clock.sleeps == [3.0, 3.0]


@pytest.mark.parametrize("mode", [0, 1])
def test_retry_budget_is_shared_between_enter_and_poll(queue_factory, mode: int) -> None:
    """Netfunnel.java:352-363,592: one app retry for the entire Begin operation."""
    client, gate, world, clock = queue_factory([
        Reply(error="connect"), Reply("201:key=SYNTHETIC-WAIT&ttl=1"),
        Reply(error="connect"),
    ], mode=mode)
    if mode == 0:
        with pytest.raises(KorailNetFunnelError):
            client.run(gate, world.send)
    else:
        client.run(gate, world.send)
    assert world.ops() == ["5101", "5101", "5002"] + (["API"] if mode else []) + ["5004"]
    assert clock.sleeps == [3.0, 1, 3.0]


@pytest.mark.parametrize("mode", [0, 1])
def test_waiting_poll_error_with_available_retry(queue_factory, mode: int) -> None:
    """Netfunnel.java:654-664 converts a failed check-enter to an error callback."""
    client, gate, world, clock = queue_factory([
        Reply("201:key=SYNTHETIC-WAIT&ttl=1"), Reply(error="connect"), Reply(error="connect"),
    ], mode=mode)
    if mode == 0:
        with pytest.raises(KorailNetFunnelError):
            client.run(gate, world.send)
    else:
        client.run(gate, world.send)
    assert world.ops() == ["5101", "5002", "5002"] + (["API"] if mode else []) + ["5004"]
    assert clock.now == 7


LIMIT_CASES = [
    ("slow-immediate", [Reply(delay=2)], 1.0, 0.0),
    ("ttl-would-exceed", [Reply("201:key=SYNTHETIC-WAIT&ttl=5")], 2.0, 0.0),
    ("slow-poll-success", [Reply("201:key=SYNTHETIC-WAIT&ttl=1"), Reply(delay=2)], 2.0, 0.0),
    ("cumulative-wait", [Reply("201:key=SYNTHETIC-WAIT&ttl=1"), Reply("202:key=SYNTHETIC-NEXT&ttl=2")], 2.0, 0.0),
    ("enter-errors", [Reply(error="connect"), Reply(error="connect")], 1.0, 0.0),
    ("poll-errors", [Reply("201:key=SYNTHETIC-WAIT&ttl=1"), Reply(error="connect"), Reply(error="connect")], 2.0, 0.0),
    ("retry-then-success", [Reply(error="connect"), Reply()], 2.0, 0.0),
    ("oversleep-success", [Reply("201:key=SYNTHETIC-WAIT&ttl=1"), Reply()], 1.0, 0.25),
    ("slow-terminal", [Reply("300:key=SYNTHETIC-END", delay=2)], 1.0, 0.0),
]


@pytest.mark.parametrize("mode", [0, 1])
@pytest.mark.parametrize("label,replies,limit,overshoot", LIMIT_CASES, ids=[x[0] for x in LIMIT_CASES])
def test_wait_limit_never_starts_api_after_budget(
    queue_factory, mode: int, label: str, replies: list[Reply], limit: float, overshoot: float,
) -> None:
    """Library admission budget, not an app timer; includes every error/pass/wait exit."""
    client, gate, world, _ = queue_factory(replies, mode=mode, limit=limit, overshoot=overshoot)
    with pytest.raises(KorailNetFunnelError):
        client.run(gate, world.send)
    assert world.sent == 0, label
    assert "API" not in world.ops()


@pytest.mark.parametrize("mode", [0, 1])
@pytest.mark.parametrize("delay,limit", [(0.0, 0.0), (1.0, 1.0)])
def test_wait_limit_inclusive_boundary(queue_factory, mode: int, delay: float, limit: float) -> None:
    """Library policy: elapsed == limit is allowed; > limit is rejected."""
    client, gate, world, _ = queue_factory([Reply(delay=delay)], mode=mode, limit=limit)
    client.run(gate, world.send)
    assert world.sent == 1


def test_wait_limit_is_not_hard_wall_clock_deadline(queue_factory) -> None:
    """An existing 1s budget can return at 6s, but cannot start the API. No hard-bound claim."""
    client, gate, world, clock = queue_factory(
        [Reply(error="connect"), Reply(error="connect")], mode=1, limit=1,
    )
    with pytest.raises(KorailNetFunnelError):
        client.run(gate, world.send)
    assert clock.now == 6 and world.sent == 0


def test_api_and_completion_time_are_outside_admission_budget(queue_factory) -> None:
    """Library run budget only governs the admission time, not API duration or cleanup."""
    client, gate, world, clock = queue_factory([Reply()], limit=0, complete=Reply(delay=4))
    def send() -> str:
        result = world.send()
        clock.now += 9
        return result
    assert client.run(gate, send) == "SYNTHETIC-RESULT"
    assert clock.now == 13
    assert world.ops() == ["5101", "API", "5004"]


def test_no_total_or_callback_timeout_is_implicitly_added(queue_factory) -> None:
    """SDK TTL can be 30s. App 15s callback watchdog is NOT a total wait deadline."""
    client, gate, world, clock = queue_factory([
        Reply("201:key=SYNTHETIC-WAIT&ttl=30"), Reply("202:key=SYNTHETIC-WAIT&ttl=30"), Reply(),
    ])
    client.run(gate, world.send)
    assert clock.now == 60 and world.sent == 1


@pytest.mark.parametrize("node", ["nf.letskorail.com", "rnf1.letskorail.com", "rnf12.letskorail.com", "rnf99.letskorail.com"])
def test_allowed_node_following(queue_factory, node: str) -> None:
    """Library node policy, not proof that app overrides Property.java:23 host_notmodify."""
    client, gate, world, _ = queue_factory([
        Reply(f"201:key=SYNTHETIC-WAIT&ttl=1&ip={node}&port=443"),
        Reply(f"200:key=SYNTHETIC-PASS&ip={node}&port=443"),
    ])
    client.run(gate, world.send)
    assert [e[1] for e in world.events] == ["nf.letskorail.com", node, "api.invalid", node]


def test_missing_new_node_resets_to_front(queue_factory) -> None:
    """CommandClient.java:117-137 replaces the response; library does not retain an old node."""
    client, gate, world, _ = queue_factory([
        Reply("201:key=SYNTHETIC-A&ttl=1&ip=rnf12.letskorail.com&port=443"),
        Reply("201:key=SYNTHETIC-B&ttl=1"), Reply("200:key=SYNTHETIC-C"),
    ])
    client.run(gate, world.send)
    assert [e[1] for e in world.events] == [
        "nf.letskorail.com", "rnf12.letskorail.com", "nf.letskorail.com", "api.invalid", "nf.letskorail.com",
    ]


BAD_NODES = [
    ("elsewhere.invalid", "443"), ("127.0.0.1", "443"), ("rnf0.letskorail.com", "443"),
    ("rnf100.letskorail.com", "443"), ("rnf01.letskorail.com", "443"),
    ("RNF12.letskorail.com", "443"), ("rnf12.letskorail.com", "80"),
    ("rnf12.letskorail.com", "0443"), ("rnf12.letskorail.com", ""), ("", "443"),
    ("rnf12.letskorail.com.evil.invalid", "443"), ("https://rnf12.letskorail.com", "443"),
]


@pytest.mark.parametrize("host,port", BAD_NODES)
@pytest.mark.parametrize("mode", [0, 1])
def test_rejected_node_never_falls_back_to_unqueued_api(queue_factory, host: str, port: str, mode: int) -> None:
    """Library guard is a ProtocolError, intentionally not caught by ErrorBypass."""
    client, gate, world, _ = queue_factory([Reply(f"200:key=SYNTHETIC&ip={host}&port={port}")], mode=mode)
    with pytest.raises(KorailProtocolError):
        client.run(gate, world.send)
    assert world.ops() == ["5101"] and world.sent == 0


def test_rejected_poll_node_releases_previous_trusted_slot(queue_factory) -> None:
    client, gate, world, _ = queue_factory([
        Reply("201:key=SYNTHETIC-OLD&ttl=1&ip=rnf12.letskorail.com&port=443"),
        Reply("200:key=SYNTHETIC-BAD&ip=elsewhere.invalid&port=443"),
    ], mode=1)
    with pytest.raises(KorailProtocolError):
        client.run(gate, world.send)
    assert world.ops() == ["5101", "5002", "5004"]
    assert world.events[-1][1:3] == ("rnf12.letskorail.com", {"opcode": "5004", "key": "SYNTHETIC-OLD"})


@pytest.mark.parametrize("text", ["201:ttl=1", "202:ttl=1"])
def test_wait_without_key_rejected(queue_factory, text: str) -> None:
    """CommandClient.java:104-108 sends no empty-key poll; Python raises instead of looping."""
    client, gate, world, _ = queue_factory([Reply(text)], mode=1)
    with pytest.raises(KorailNetFunnelError):
        client.run(gate, world.send)
    assert world.ops() == ["5101"]


def test_empty_final_key_is_not_replaced_by_old_key(queue_factory) -> None:
    client, gate, world, _ = queue_factory([Reply("201:key=SYNTHETIC-OLD&ttl=1"), Reply("200:key=")])
    client.run(gate, world.send)
    assert world.ops() == ["5101", "5002", "API"]


@pytest.mark.parametrize("completion", [Reply(text="invalid completion payload"), Reply(status=503), Reply(error="connect")])
def test_complete_once_without_parsing_or_retry(queue_factory, completion: Reply) -> None:
    """CommandClient.java:158-199; Netfunnel.java:848-880, completion failures are not rethrown."""
    client, gate, world, _ = queue_factory([Reply()], complete=completion)
    assert client.run(gate, world.send) == "SYNTHETIC-RESULT"
    assert world.ops() == ["5101", "API", "5004"]


def test_callback_exception_preserved_and_slot_returned(queue_factory) -> None:
    client, gate, world, _ = queue_factory([Reply()], complete=Reply(error="connect"))
    error = RuntimeError("synthetic callback failure")
    def send() -> Any:
        world.send()
        raise error
    with pytest.raises(RuntimeError) as raised:
        client.run(gate, send)
    assert raised.value is error and world.ops() == ["5101", "API", "5004"]


def test_body_parse_retains_raw_and_library_field_policy() -> None:
    """Response.java:128-163 is the structural source; '=' retention is Python policy."""
    raw = " 201:key=SYNTHETIC=PART&ttl=-4&nwait=not-numeric&extra=x "
    token = parse_netfunnel_body(raw)
    assert token.raw == raw and token.key == "SYNTHETIC=PART"
    assert token.wait_seconds == 1 and token.wait_count == 0
    assert token.params["extra"] == "x"
    assert korail_netfunnel_node_url("", "") == ""


@pytest.mark.parametrize("text", ["", "200", "oops:key=x", "２００:key=x", "+200:key=x"])
def test_invalid_body_keeps_raw(text: str) -> None:
    with pytest.raises(KorailNetFunnelError) as raised:
        parse_netfunnel_body(text)
    assert raised.value.raw == text


EXPECTED_GATES = {
    "inquiry": ("act_8", False), "peak_season_inquiry": ("act_8_2", False),
    "product_inquiry": ("act_6", False), "reserve": ("act_14", True),
    "pay": ("act_18", True), "reservation_view": ("act_21", True),
}
EXPECTED_GATED_METHODS = {
    "get_reservation_history", "get_seat_assignment_schedule", "search_trains",
    "search_transfer_trains", "search_trains_with_transfer_fallback", "reserve",
    "reserve_transfer", "pay_with_card", "reserve_with_discount_card",
}


def test_gate_defaults_and_action_overrides() -> None:
    """Library defaults only. Protected KORAIL aid/mode literals are NOT established by this test."""
    assert {n: (g.action, g.success_only) for n, g in KORAIL_NETFUNNEL_GATES.items()} == EXPECTED_GATES
    config = KorailConfig(netfunnel_actions={n: f"SYNTHETIC-{n}" for n in EXPECTED_GATES})
    client = KorailNetFunnelClient(config, transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    try:
        for name, (_, success_only) in EXPECTED_GATES.items():
            assert client.gate(name) == KorailNetFunnelGate(name, f"SYNTHETIC-{name}", success_only)
    finally:
        client.close()


def test_all_77_public_methods_gate_call_graph() -> None:
    """Exhaustive library AST connectivity, not a claim that unknown app gate literals match."""
    tree = ast.parse(inspect.getsource(KorailClient))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef))
    methods = {n.name: n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    public = {n for n in methods if not n.startswith("_")}
    edges = {
        name: {call.func.attr for call in ast.walk(node)
               if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
               and isinstance(call.func.value, ast.Name) and call.func.value.id == "self"}
        for name, node in methods.items()
    }
    def reaches_queue(name: str, seen: frozenset[str] = frozenset()) -> bool:
        if name in seen or name not in edges:
            return False
        return "_queued" in edges[name] or any(reaches_queue(n, seen | {name}) for n in edges[name])
    assert len(public) == 77
    assert {n for n in public if reaches_queue(n)} == EXPECTED_GATED_METHODS
    calls = [n for n in ast.walk(cls) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute) and n.func.attr == "_queued"]
    assert len(calls) == 7
    direct = {}
    for name, node in methods.items():
        for call in ast.walk(node):
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr == "_queued":
                direct[name] = ast.unparse(call.args[0])
    assert direct == {
        "get_reservation_history": "'reservation_view'",
        "get_seat_assignment_schedule": "self._inquiry_gate(peak_season=peak_season)",
        "_post_schedule_view": "self._inquiry_gate(peak_season=peak_season, special=use_special_schedule)",
        "reserve": "'reserve'", "reserve_transfer": "'reserve'",
        "pay_with_card": "'pay'", "reserve_with_discount_card": "'reserve'",
    }


@pytest.mark.parametrize("peak,special,gate", [
    (False, False, "inquiry"), (True, False, "peak_season_inquiry"),
    (False, True, "product_inquiry"), (True, True, "product_inquiry"),
])
def test_inquiry_gate_selection(peak: bool, special: bool, gate: str) -> None:
    """Library selection priority; TrainScheduleViewModel.java:5208-5244 has protected aid values."""
    assert KorailClient._inquiry_gate(peak_season=peak, special=special) == gate


def test_disabled_queue_sends_directly() -> None:
    client = KorailClient(KorailConfig(netfunnel_enabled=False), transport=httpx.MockTransport(lambda r: httpx.Response(200)))
    try:
        assert client.netfunnel is None
        assert client._queued("inquiry", lambda: "synthetic") == "synthetic"
    finally:
        client.close()


@pytest.fixture
def config() -> KorailConfig:
    return KorailConfig(base_url="https://api.invalid", device="SYNTHETIC-DEVICE", version="SYNTHETIC-VERSION", key="SYNTHETIC-KEY", lang="ko")


@pytest.fixture
def schedule_query() -> LimousineScheduleQuery:
    return LimousineScheduleQuery("20990101", "9001", "9002", "980", "1", "120000", "", "015", "")


@pytest.fixture
def seat_query() -> LimousineSeatInventoryQuery:
    return LimousineSeatInventoryQuery("99", "980", "20990101", "99001", "0001", "1", "9001", "9002", "015", "1", "2", 2)


def expected_schedule_form() -> dict[str, str]:
    return {"Device": "SYNTHETIC-DEVICE", "Version": "SYNTHETIC-VERSION", "Key": "SYNTHETIC-KEY", "lang": "ko",
            "dptDt": "20990101", "dptRsStnCd": "9001", "arvRsStnCd": "9002", "trnGpCd": "980",
            "psrmClCd": "1", "dptTm": "120000", "trnNo": "", "seatAttCd": "015", "rsvSaleDvCd": ""}


def expected_seat_form() -> dict[str, str]:
    return {"Device": "SYNTHETIC-DEVICE", "Version": "SYNTHETIC-VERSION", "Key": "SYNTHETIC-KEY", "lang": "ko",
            "trnClsfCd": "99", "trnGpCd": "980", "runDt": "20990101", "trnNo": "99001", "srcarNo": "0001",
            "psrmClCd": "1", "dptRsStnCd": "9001", "arvRsStnCd": "9002", "seatAttCd": "015",
            "dptStnRunOrdr": "1", "arvStnRunOrdr": "2", "totPsgCnt": "2", "isArrow": "false"}


def test_full_schedule_form(config, schedule_query) -> None:
    """ScdlQryIn.java:60-78; AirportBusScheduleViewModel.java:221-248. Wire trnGpCd stays unverified."""
    assert build_limousine_schedule_form(config, schedule_query) == expected_schedule_form()
    assert "lang" not in build_limousine_schedule_form(replace(config, lang=None), schedule_query)


def test_full_inventory_form(config, seat_query) -> None:
    """TResidualSeatsResearchIn.java:65-138,163-219; AirportBusSeatMapViewModel.java:843-865."""
    assert build_limousine_seat_inventory_form(config, seat_query) == expected_seat_form()
    q = replace(seat_query, product_no="SYNTHETIC-PRODUCT", is_arrow=True)
    assert build_limousine_seat_inventory_form(config, q) == {**expected_seat_form(), "gdNo": "SYNTHETIC-PRODUCT", "isArrow": "true"}
    assert "ctlDvCd" not in build_limousine_seat_inventory_form(config, q)
    assert "lang" not in build_limousine_seat_inventory_form(replace(config, lang=None), q)


@pytest.mark.parametrize("field_name,value", [("passenger_count", True), ("passenger_count", "2"), ("passenger_count", 1.0), ("is_arrow", 1), ("is_arrow", "false"), ("is_arrow", None)])
def test_query_type_rejections(seat_query, field_name: str, value: Any) -> None:
    with pytest.raises(KorailProtocolError):
        replace(seat_query, **{field_name: value})


@pytest.mark.parametrize("count", [-1, 0, 10])
def test_inventory_query_has_no_reservation_count_range(config, seat_query, count: int) -> None:
    """Read query does NOT impose the reservation 1..9 rule; TResidualSeatsResearchIn.java:65-138."""
    assert build_limousine_seat_inventory_form(config, replace(seat_query, passenger_count=count))["totPsgCnt"] == str(count)


# Independent field tables from DTO properties/annotations. Protected schedule
# SerialName strings remain a limitation, even where the library/live keys work.
SCHEDULE_FIELDS = {
    "arvDt": "arrival_date", "arvRsStnCd": "arrival_station_code", "arvStnRunOrdr": "arrival_run_order", "arvTm": "arrival_time",
    "chtnDvCd": "transfer_division_code", "dptDt": "departure_date", "dptRsStnCd": "departure_station_code", "dptStnRunOrdr": "departure_run_order",
    "dptTm": "departure_time", "gnrmRestSeatNum": "general_remaining_seat_count", "ocurDlayTnum": "delay_minutes", "restFresNum": "free_remaining_seat_count",
    "restStndNum": "standing_remaining_seat_count", "runDt": "run_date", "sprmRestSeatNum": "special_remaining_seat_count", "stlbTrnClsfCd": "train_class_code",
    "trnGpCd": "service_code", "trnNo": "train_no", "ymsAplFlg": "yms_application_flag", "trnOrdrNo": "train_order_no", "rcvdPrc": "received_price",
}
SEAT_FIELDS = {
    "dir_seat_att_cd": "direction_attribute_code", "etc_seat_att_cd": "other_attribute_code", "intg_msg": "integrated_message", "intg_msg_cd": "integrated_message_code",
    "rq_seat_att_cd": "requested_attribute_code", "sale_psb_flg": "sale_possible_flag", "seat_no": "seat_no", "seat_spec": "specification",
    "sqr_no": "sequence_no", "vz_msg_dv_cd": "visual_message_division_code",
}
SCHEDULE_TOP = {"fllwPgExt": "following_page_extension", "lgtmShtmDvCd": "long_short_division_code"}
SEAT_TOP = {"car_tp_cd": "car_type_code", "scar_no": "car_no", "seat_ary_cd": "seat_arrangement_code", "up_dn_dv_cd": "up_down_division_code", "layout_type": "layout_type", "vrBnrUrl": "vr_banner_url"}


def envelope(**values: Any) -> BaseKorailResponse:
    return BaseKorailResponse.from_raw({"strResult": "SUCC", "h_msg_cd": "SYNTHETIC", "h_msg_txt": "synthetic", **values})


@pytest.mark.parametrize("parser,list_key,fields", [
    (parse_limousine_schedule_response, "trainList", SCHEDULE_FIELDS),
    (parse_limousine_seat_inventory_response, "seatList", SEAT_FIELDS),
])
def test_every_row_field_string_and_raw(parser, list_key: str, fields: dict[str, str]) -> None:
    """ScdlQryOutTrain.java:70-123; TResidualSeatsResearchOutSeat.java:62-104, optional masks."""
    row = {key: f"000{i}" for i, key in enumerate(fields)}
    row["synthetic_unknown"] = {"preserved": True}
    response = envelope(**{list_key: [row]})
    parsed = parser(response)
    rows = parsed.schedules if list_key == "trainList" else parsed.seats
    assert len(rows) == 1
    for wire, attr in fields.items():
        assert getattr(rows[0], attr) == row[wire]
    assert rows[0].raw == row and parsed.raw is response.raw


@pytest.mark.parametrize("wire,attr", list(SCHEDULE_FIELDS.items()))
def test_schedule_integer_string_field_preserved(wire: str, attr: str) -> None:
    """ScdlQryOutTrain.java:70-123 optional String masks; SESSION_CONTEXT §3.6 integer normalization."""
    result = parse_limousine_schedule_response(envelope(trainList=[{wire: 7}]))
    assert getattr(result.schedules[0], attr) == "7"
    assert result.schedules[0].raw[wire] == 7


@pytest.mark.parametrize("wire,attr", list(SEAT_FIELDS.items()))
def test_seat_integer_string_field_preserved(wire: str, attr: str) -> None:
    """TResidualSeatsResearchOutSeat.java:62-104; shared DTO String/int policy."""
    result = parse_limousine_seat_inventory_response(envelope(seatList=[{wire: 7}]))
    assert getattr(result.seats[0], attr) == "7"


@pytest.mark.parametrize("parser,wire,attr", [
    *[(parse_limousine_schedule_response, k, v) for k, v in SCHEDULE_TOP.items()],
    *[(parse_limousine_seat_inventory_response, k, v) for k, v in SEAT_TOP.items()],
])
def test_top_level_integer_string_field_preserved(parser, wire: str, attr: str) -> None:
    """ScdlQryOut.java:58-74; TResidualSeatsResearchOut.java:61-82 optional String fields."""
    response = envelope(**{wire: 7})
    result = parser(response)
    assert getattr(result, attr) == "7" and result.raw is response.raw


@pytest.mark.parametrize("bad", [True, False, 1.5, [], {}, None])
def test_optional_bad_scalars_stay_none(bad: Any) -> None:
    a = parse_limousine_schedule_response(envelope(trainList=[dict.fromkeys(SCHEDULE_FIELDS, bad)], **dict.fromkeys(SCHEDULE_TOP, bad)))
    b = parse_limousine_seat_inventory_response(envelope(seatList=[dict.fromkeys(SEAT_FIELDS, bad)], **dict.fromkeys(SEAT_TOP, bad)))
    assert all(getattr(a.schedules[0], attr) is None for attr in SCHEDULE_FIELDS.values())
    assert all(getattr(b.seats[0], attr) is None for attr in SEAT_FIELDS.values())
    assert all(getattr(a, attr) is None for attr in SCHEDULE_TOP.values())
    assert all(getattr(b, attr) is None for attr in SEAT_TOP.values())


@pytest.mark.parametrize("parser,key,attr", [(parse_limousine_schedule_response, "trainList", "schedules"), (parse_limousine_seat_inventory_response, "seatList", "seats")])
def test_optional_list_defaults(parser, key: str, attr: str) -> None:
    """ScdlQryOut.java:74; TResidualSeatsResearchOut.java:79. Null leniency is library policy."""
    for values in ({}, {key: None}, {key: []}):
        assert getattr(parser(envelope(**values)), attr) == ()


@pytest.mark.parametrize("parser,key", [(parse_limousine_schedule_response, "trainList"), (parse_limousine_seat_inventory_response, "seatList")])
@pytest.mark.parametrize("bad", [{}, "bad", 7, [None], ["bad"]])
def test_bad_lists_preserve_full_error_raw(parser, key: str, bad: Any) -> None:
    """Library ACCEPTANCE list/row contract, stricter than optional-field masks alone."""
    response = envelope(**{key: bad, "synthetic_extra": [1, 2]})
    with pytest.raises(KorailProtocolError) as raised:
        parser(response)
    assert raised.value.raw is response.raw


@pytest.mark.parametrize("parser", [parse_limousine_schedule_response, parse_limousine_seat_inventory_response])
@pytest.mark.parametrize("result", [None, "", "succ", "FAIL", "SUCC "])
def test_exact_success_envelope(parser, result: Any) -> None:
    response = envelope(strResult=result)
    with pytest.raises(KorailProtocolError) as raised:
        parser(response)
    assert raised.value.raw is response.raw


def test_window_optional_parsing_and_raw() -> None:
    """TResidualSeatsResearchOutWindow.java:51-58; forgiving windows are library policy."""
    response = envelope(windowList=[
        {"st_loc_rt": "0.25", "cls_loc_rt": 1}, {"st_loc_rt": -2, "cls_loc_rt": 1.5},
        None, {}, {"st_loc_rt": True, "cls_loc_rt": 1}, {"st_loc_rt": "NaN", "cls_loc_rt": 1},
        {"st_loc_rt": float("inf"), "cls_loc_rt": 1},
    ])
    result = parse_limousine_seat_inventory_response(response)
    assert [(w.start_location_ratio, w.close_location_ratio) for w in result.windows] == [(0.25, 1.0), (-2.0, 1.5)]
    assert result.raw is response.raw
    assert parse_limousine_seat_inventory_response(envelope(windowList={})).windows == ()


@pytest.fixture
def schedule() -> LimousineSchedule:
    return LimousineSchedule(
        arrival_date="20990101", arrival_station_code="9002", arrival_run_order="2", arrival_time="140000",
        departure_date="20990101", departure_station_code="9001", departure_run_order="1", departure_time="120000",
        general_remaining_seat_count="09", run_date="20990101", train_class_code="99", service_code="980", train_no="99001",
    )


def expected_reservation_form() -> dict[str, str]:
    # Current library wire values / dated accepted observation, NOT recovered protected enums.
    return {"Device": "SYNTHETIC-DEVICE", "Version": "SYNTHETIC-VERSION", "Key": "SYNTHETIC-KEY", "lang": "ko",
        "txtMenuId": "11", "txtJobId": "1101", "hidFreeFlg": "N", "txtStndFlg": "N", "txtTotPsgCnt": "2",
        "txtCompaCnt1": "1", "txtPsgTpCd1": "1", "txtDiscKndCd1": "000",
        "txtCompaCnt2": "1", "txtPsgTpCd2": "3", "txtDiscKndCd2": "000",
        "txtSeatAttCd1": "000", "txtSeatAttCd2": "000", "txtSeatAttCd3": "000", "txtSeatAttCd4": "015", "txtSeatAttCd5": "000",
        "txtPsrmClCd1": "1", "txtJrnyCnt": "1", "txtJrnyTpCd1": "11", "txtJrnySqno1": "001",
        "txtTrnNo1": "99001", "txtTrnClsfCd1": "99", "txtTrnGpCd1": "980", "txtRunDt1": "20990101", "txtDptDt1": "20990101", "txtDptTm1": "120000",
        "txtDptRsStnCd1": "9001", "txtDptStnRunOrdr1": "1", "txtArvRsStnCd1": "9002", "txtArvStnRunOrdr1": "2",
        "txtSrcarCnt": "2", "txtSrcarNo1": "0001", "txtSeatNo1": "SYNTHETIC-SEAT-A", "txtSrcarNo2": "0001", "txtSeatNo2": "SYNTHETIC-SEAT-B"}


def test_full_reservation_form_adult_child(config, schedule) -> None:
    """AirportBusScheduleViewModel.java:165-184; AirportBusSeatMapViewModel.java:752-788; ScdlQryOutTrain.java:613-620."""
    assert build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A", "SYNTHETIC-SEAT-B"], passengers=KorailPassengerCounts(adult=1, child=1)) == expected_reservation_form()


@pytest.mark.parametrize("adult,child", [(1, 0), (0, 1), (0, 2), (5, 4)])
def test_reservation_passenger_rows_only_nonzero(config, schedule, adult: int, child: int) -> None:
    """PassengerType.java:56-63; Passengers.java:743-753: only selected nonzero rows."""
    passengers = KorailPassengerCounts(adult=adult, child=child)
    seats = [f"SYNTHETIC-SEAT-{i}" for i in range(passengers.total)]
    form = build_limousine_reservation_form(config, schedule, seats, passengers=passengers)
    expected_rows = [(count, kind) for count, kind in [(adult, "1"), (child, "3")] if count]
    for i, (count, kind) in enumerate(expected_rows, 1):
        assert (form[f"txtCompaCnt{i}"], form[f"txtPsgTpCd{i}"], form[f"txtDiscKndCd{i}"]) == (str(count), kind, "000")
    assert f"txtCompaCnt{len(expected_rows) + 1}" not in form
    assert form["txtSrcarCnt"] == form["txtTotPsgCnt"] == str(passengers.total)


def test_duplicate_seat_rejected(config, schedule) -> None:
    """AirportBusSeatMapViewModel.java:1996-2038 toggles seat_no, so the app never selects it twice."""
    with pytest.raises(KorailProtocolError, match="distinct|duplicate|unique"):
        build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A"] * 2, passengers=KorailPassengerCounts(adult=2))


@pytest.mark.parametrize("seats", [None, "SYNTHETIC-SEAT-A", b"seat", {"seat"}, [], [""], [" "], [None], [7], [True], ["A", "B"]])
def test_reservation_seat_input_rejections(config, schedule, seats: Any) -> None:
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, schedule, seats)


@pytest.mark.parametrize("kind", ["teenager", "infant", "senior", "severe_disability", "mild_disability", "guide_dog"])
def test_reservation_only_adult_and_child(config, schedule, kind: str) -> None:
    """PassengerType.java:56-63 airportList contains only ADULT and CHILD."""
    passengers = KorailPassengerCounts(adult=0, **{kind: 1})
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A"], passengers=passengers)


@pytest.mark.parametrize("kwargs", [{"adult": 0}, {"adult": 10}, {"adult": -1}, {"adult": True}, {"adult": "1"}])
def test_passenger_count_rejections(kwargs: dict[str, Any]) -> None:
    with pytest.raises(KorailProtocolError):
        KorailPassengerCounts(**kwargs)


@pytest.mark.parametrize("attr,value", [
    ("train_no", None), ("train_class_code", ""), ("service_code", ""),
    ("run_date", "2099-01-01"), ("departure_date", "2099010"), ("departure_time", "1200"),
    ("departure_station_code", "station"), ("arrival_station_code", None),
    ("departure_run_order", "one"), ("arrival_run_order", ""), ("general_remaining_seat_count", "0"),
])
def test_reservation_bad_schedule_rejected(config, schedule, attr: str, value: Any) -> None:
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, replace(schedule, **{attr: value}), ["SYNTHETIC-SEAT-A"])


def test_reservation_wrong_types_and_car_override(config, schedule) -> None:
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, {}, ["SYNTHETIC-SEAT-A"])
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A"], passengers={"adult": 1})
    with pytest.raises(KorailProtocolError):
        build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A"], car_no="")
    form = build_limousine_reservation_form(config, schedule, ["SYNTHETIC-SEAT-A"], car_no="SYNTHETIC-CAR")
    assert form["txtSrcarNo1"] == "SYNTHETIC-CAR"


@pytest.fixture
def api_factory(config):
    clients: list[KorailClient] = []
    def make(payload: dict[str, Any] | Exception, *, authenticated: bool = True):
        requests: list[httpx.Request] = []
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.host == "api.invalid", "A limousine method unexpectedly entered NetFunnel"
            requests.append(request)
            if isinstance(payload, Exception):
                raise payload
            return httpx.Response(200, json=payload)
        client = KorailClient(config, transport=httpx.MockTransport(handler))
        clients.append(client)
        if authenticated:
            client.session.current = KorailSession(jsessionid="SYNTHETIC-SESSION", member_no="SYNTHETIC-MEMBER")
        return client, requests
    yield make
    for client in clients:
        client.close()


def decoded_form(request: httpx.Request) -> dict[str, str]:
    pairs = parse_qs(request.content.decode(), keep_blank_values=True)
    assert all(len(values) == 1 for values in pairs.values())
    return {key: values[0] for key, values in pairs.items()}


def test_schedule_client_wire_and_parse_no_queue(api_factory, schedule_query) -> None:
    """NetworkApi.java:654-656; AirportBusScheduleViewModel.java:248 directly calls the repository."""
    raw = {"strResult": "SUCC", "trainList": [{"trnNo": "99001", "rcvdPrc": "00000000000100"}]}
    client, requests = api_factory(raw, authenticated=False)
    result = client.get_limousine_schedules(schedule_query)
    assert len(requests) == 1 and requests[0].method == "POST"
    assert requests[0].url.path == "/classes/com.korail.mobile.lmu.scdlQry.do"
    assert decoded_form(requests[0]) == {k: v for k, v in expected_schedule_form().items() if v != ""}
    assert result.schedules[0].received_price == "00000000000100" and result.raw == raw


def test_seat_client_wire_and_parse_no_queue(api_factory, seat_query) -> None:
    """NetworkApi.java:269-271; AirportBusSeatMapViewModel.java:843-865 provides this DTO."""
    raw = {"strResult": "SUCC", "seatList": [{"seat_no": "SYNTHETIC-SEAT-A"}], "layout_type": 7}
    client, requests = api_factory(raw, authenticated=False)
    result = client.get_limousine_seat_inventory(seat_query)
    assert len(requests) == 1 and requests[0].method == "POST"
    assert requests[0].url.path == "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do"
    assert decoded_form(requests[0]) == expected_seat_form()
    assert result.layout_type == "7" and result.seats[0].seat_no == "SYNTHETIC-SEAT-A"


def test_reserve_client_full_wire_no_queue(api_factory, schedule) -> None:
    """AirportBusSeatMapViewModel.java:638-688,1513-1552: direct reservation, no withNetFunnel."""
    raw = {"strResult": "SUCC", "h_pnr_no": "SYNTHETIC-NOT-A-REAL-PNR", "h_tot_rcvd_amt": "100", "h_jrny_cnt": "1"}
    client, requests = api_factory(raw)
    result = client.reserve_limousine(schedule, ["SYNTHETIC-SEAT-A", "SYNTHETIC-SEAT-B"], passengers=KorailPassengerCounts(adult=1, child=1))
    assert len(requests) == 1 and requests[0].method == "POST"
    assert requests[0].url.path == "/classes/com.korail.mobile.certification.TicketReservation"
    assert decoded_form(requests[0]) == expected_reservation_form()
    assert result.pnr_no == raw["h_pnr_no"] and result.raw == raw


def test_reserve_client_requires_session_before_send(api_factory, schedule) -> None:
    client, requests = api_factory({"strResult": "SUCC"}, authenticated=False)
    with pytest.raises(KorailAuthError):
        client.reserve_limousine(schedule, ["SYNTHETIC-SEAT-A"])
    assert requests == []


def test_duplicate_rejected_before_any_request(api_factory, schedule) -> None:
    """AirportBusSeatMapViewModel.java:1996-2038 uniqueness must hold before an actual hold is sent."""
    client, requests = api_factory({"strResult": "SUCC"})
    with pytest.raises(KorailProtocolError):
        client.reserve_limousine(schedule, ["SYNTHETIC-SEAT-A"] * 2, passengers=KorailPassengerCounts(adult=2))
    assert requests == []


def test_reservation_parser_failure_preserves_raw_without_retry(api_factory, schedule) -> None:
    raw = {"strResult": "SUCC", "h_pnr_no": "SYNTHETIC-NOT-A-REAL-PNR", "h_jrny_cnt": [], "synthetic_extra": "keep"}
    client, requests = api_factory(raw)
    with pytest.raises(KorailProtocolError) as raised:
        client.reserve_limousine(schedule, ["SYNTHETIC-SEAT-A"])
    assert raised.value.raw == raw
    assert hasattr(raised.value, "parser_raw") and len(requests) == 1


def test_reservation_transport_failure_is_not_retried(api_factory, schedule) -> None:
    client, requests = api_factory(httpx.ReadTimeout("synthetic reservation timeout"))
    with pytest.raises(KorailTransportError):
        client.reserve_limousine(schedule, ["SYNTHETIC-SEAT-A"])
    assert len(requests) == 1


def test_read_fail_envelope_preserves_raw(api_factory, schedule_query) -> None:
    raw = {"strResult": "FAIL", "h_msg_cd": "SYNTHETIC-ERROR", "h_msg_txt": "synthetic"}
    client, requests = api_factory(raw)
    with pytest.raises(KorailApiError) as raised:
        client.get_limousine_schedules(schedule_query)
    assert raised.value.raw == raw and len(requests) == 1


def test_fallback_wait_budget_restarts_for_each_admission() -> None:
    """Library policy: client.py search_trains_with_transfer_fallback starts two independent runs.

    A 1s queue budget is not a 1s bound on the entire two-query public method.
    App confirmation/filter differences are outside this queue contract test.
    """
    from korail_mobile_api.models import TrainSearchQuery
    clock = Clock()
    events: list[str] = []
    api_count = 0
    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal api_count
        if request.url.path == "/ts.wseq":
            op = request.url.params["opcode"]
            events.append(op)
            if op == "5101":
                clock.now += 1
            return httpx.Response(200, text="200:key=SYNTHETIC-FALLBACK")
        assert request.url.host == "api.invalid"
        api_count += 1
        events.append("API")
        if api_count == 1:
            return httpx.Response(200, json={"strResult": "FAIL", "h_msg_cd": "WRD000061", "h_msg_txt": "synthetic"})
        return httpx.Response(200, json={"strResult": "SUCC", "h_msg_cd": "IRG000000", "h_msg_txt": "synthetic"})
    client = KorailClient(KorailConfig(base_url="https://api.invalid", netfunnel_wait_limit=1), transport=httpx.MockTransport(handler))
    try:
        assert client.netfunnel is not None
        client.netfunnel._clock = clock
        client.netfunnel._sleep = clock.sleep
        client._station_names = {"9001": "SYNTHETIC-DEPARTURE", "9002": "SYNTHETIC-ARRIVAL"}
        client.search_trains_with_transfer_fallback(TrainSearchQuery("9001", "9002", "20990101"))
        assert api_count == 2 and clock.now == 2
        assert events == ["5101", "API", "5004", "5101", "API", "5004"]
    finally:
        client.close()
