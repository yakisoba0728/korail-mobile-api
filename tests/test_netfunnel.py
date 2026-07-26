"""Offline tests for the NetFunnel virtual waiting room.

EVERY TEST HERE IS A FIXTURE TEST, AND THAT IS A LIMITATION, NOT A CLAIM. The
KORAIL server has never queued this repository — every live call it has made
succeeded without a token — so the 201 polling path, the release path and the
response shape below have never been seen on the wire. What these tests pin is
that the client builds the requests the APK builds and reacts the way the APK
reacts. Whether ``nf.letskorail.com`` answers a keyless, ``js``-less request in
the native SDK's ``<code>:<params>`` form is the one thing only a live run can
settle; see the module docstring of :mod:`korail_mobile_api.netfunnel`.

No test in this file may reach the network. ``httpx.MockTransport`` is the only
transport used, and the two tests that exercise the polling loop inject a fake
sleeper and clock so a bounded wait costs no wall-clock time.
"""

import pathlib
import re

import httpx
import pytest

from korail_mobile_api import KorailConfig
from korail_mobile_api.constants import (
    KORAIL_NETFUNNEL_PATH,
    KORAIL_NETFUNNEL_SERVICE_ID,
    KORAIL_NETFUNNEL_TIMEOUT_SECONDS,
    KORAIL_NETFUNNEL_URL,
    KorailNetFunnelAction,
    KorailNetFunnelOpcode,
)
from korail_mobile_api.errors import (
    KorailNetFunnelError,
    KorailProtocolError,
    KorailQueueRejectedError,
    KorailTransportError,
)
from korail_mobile_api.netfunnel import (
    KORAIL_NETFUNNEL_GATED_OPERATIONS,
    MAX_TTL_SECONDS,
    MIN_TTL_SECONDS,
    QUEUE_POLL_LIMIT,
    QUEUE_WAIT_LIMIT_SECONDS,
    KorailNetFunnelClient,
    KorailNetFunnelToken,
    build_chk_enter_url,
    build_get_tid_chk_enter_url,
    build_set_complete_url,
    inquiry_action,
    is_queued,
    parse_netfunnel_body,
    parse_queue_response,
    parse_set_complete_response,
    queue_wait_seconds,
)
from korail_mobile_api.safety import (
    KORAIL_NETFUNNEL_ACTION_IDS,
    KORAIL_NETFUNNEL_QUERY_CONTRACTS,
    KORAIL_NETFUNNEL_ROUTES,
    assert_korail_netfunnel_origin,
    assert_netfunnel_request,
)


# A REALISTIC KEY. The one real NetFunnel key this project has ever captured (on
# the SRT side, from the same nf.letskorail.com host) was 256 characters of
# uppercase hex. That length is the whole reason this constant exists: the
# sibling implementation bounded the field at 128, so every release request was
# refused before it was sent and the failure was swallowed. A short "ABC123" in a
# fixture would have passed that broken guard too.
REAL_LENGTH_KEY = "0F3B" * 64
ENABLED = KorailConfig(netfunnel_enabled=True)


def _client(
    handler,
    *,
    config: KorailConfig = ENABLED,
    sleeper=None,
    clock=None,
) -> KorailNetFunnelClient:
    kwargs = {}
    if sleeper is not None:
        kwargs["sleeper"] = sleeper
    if clock is not None:
        kwargs["clock"] = clock
    return KorailNetFunnelClient(
        config,
        transport=httpx.MockTransport(handler),
        **kwargs,
    )


def test_real_length_key_is_the_shape_a_live_key_has():
    assert len(REAL_LENGTH_KEY) == 256
    assert re.fullmatch(r"[0-9A-F]{256}", REAL_LENGTH_KEY)


# ---------------------------------------------------------------------------
# The URL of each opcode, parameter ORDER included.
# ---------------------------------------------------------------------------


def test_get_tid_chk_enter_url_is_opcode_sid_aid_in_that_order():
    # T6/d.java:99-101 adds opcode, sid, aid — in that order and nothing else.
    assert build_get_tid_chk_enter_url(
        KORAIL_NETFUNNEL_URL,
        action=KorailNetFunnelAction.INQUIRY,
    ) == (
        "https://nf.letskorail.com/ts.wseq"
        "?opcode=5101&sid=service_1&aid=act_8"
    )


def test_get_tid_chk_enter_url_carries_the_peak_season_action():
    # act_8_2 is a SEPARATE queue from act_8, which is the entire point of it.
    assert build_get_tid_chk_enter_url(
        KORAIL_NETFUNNEL_URL,
        action=KorailNetFunnelAction.PEAK_SEASON_INQUIRY,
    ).endswith("?opcode=5101&sid=service_1&aid=act_8_2")


def test_chk_enter_url_is_opcode_then_key_and_nothing_else():
    # T6/d.java:54-55. No sid, no aid, no ttl — the native SDK sends neither the
    # service/action pair (unlike the JS dialect's 5002) nor the previous 201's
    # ttl (which it keeps client-side, T6/g.java:462-467).
    url = build_chk_enter_url(KORAIL_NETFUNNEL_URL, key=REAL_LENGTH_KEY)
    assert url == (
        f"https://nf.letskorail.com/ts.wseq?opcode=5002&key={REAL_LENGTH_KEY}"
    )


def test_set_complete_url_is_opcode_then_key_and_nothing_else():
    # T6/d.java:78-79.
    url = build_set_complete_url(KORAIL_NETFUNNEL_URL, key=REAL_LENGTH_KEY)
    assert url == (
        f"https://nf.letskorail.com/ts.wseq?opcode=5004&key={REAL_LENGTH_KEY}"
    )


def test_no_url_carries_the_javascript_dialects_parameters():
    # The premise this implementation was written against described the SRT
    # WebView's netfunnel.js query. KORAIL embeds the native Android SDK and
    # sends none of it. If any of these ever reappears, it came from the wrong
    # app.
    urls = (
        build_get_tid_chk_enter_url(
            KORAIL_NETFUNNEL_URL,
            action=KorailNetFunnelAction.RESERVE,
        ),
        build_chk_enter_url(KORAIL_NETFUNNEL_URL, key=REAL_LENGTH_KEY),
        build_set_complete_url(KORAIL_NETFUNNEL_URL, key=REAL_LENGTH_KEY),
    )
    for url in urls:
        query = url.partition("?")[2]
        for absent in ("js=", "nfid=", "prefix=", "ttl=", "user_data="):
            assert absent not in query, (url, absent)
        # ...and no bare trailing epoch-millisecond parameter either.
        assert not re.search(r"&\d{10,}(?:&|$)", query)


def test_every_builder_refuses_an_empty_key():
    with pytest.raises(ValueError):
        build_chk_enter_url(KORAIL_NETFUNNEL_URL, key="")
    with pytest.raises(ValueError):
        build_set_complete_url(KORAIL_NETFUNNEL_URL, key="")


# ---------------------------------------------------------------------------
# The safety contract.
# ---------------------------------------------------------------------------


def test_safety_rejects_an_unregistered_opcode():
    # 5003 aliveNotice and 5105/5106 init/stop are declared by the app
    # (T6/c.java:6-11) and deliberately not implemented, so the guard must
    # refuse them rather than pattern-matching "looks like an opcode".
    for opcode in (
        KorailNetFunnelOpcode.ALIVE_NOTICE.value,
        KorailNetFunnelOpcode.INIT.value,
        KorailNetFunnelOpcode.STOP.value,
        "9999",
        "",
    ):
        with pytest.raises(KorailProtocolError, match="not one of the registered"):
            assert_netfunnel_request(
                "GET",
                KORAIL_NETFUNNEL_PATH,
                (("opcode", opcode), ("key", REAL_LENGTH_KEY)),
            )


def test_safety_pins_the_parameter_order_not_just_the_membership():
    reordered = (("sid", KORAIL_NETFUNNEL_SERVICE_ID), ("opcode", "5101"), ("aid", "act_8"))
    with pytest.raises(KorailProtocolError, match="registered opcode-5101 contract"):
        assert_netfunnel_request("GET", KORAIL_NETFUNNEL_PATH, reordered)


def test_safety_rejects_extra_and_missing_parameters():
    with pytest.raises(KorailProtocolError):
        assert_netfunnel_request(
            "GET",
            KORAIL_NETFUNNEL_PATH,
            (("opcode", "5002"), ("key", REAL_LENGTH_KEY), ("js", "yes")),
        )
    with pytest.raises(KorailProtocolError):
        assert_netfunnel_request(
            "GET",
            KORAIL_NETFUNNEL_PATH,
            (("opcode", "5101"), ("sid", KORAIL_NETFUNNEL_SERVICE_ID)),
        )


def test_safety_rejects_a_foreign_route_or_method():
    with pytest.raises(KorailProtocolError, match="route is not allowed"):
        assert_netfunnel_request(
            "POST",
            KORAIL_NETFUNNEL_PATH,
            (("opcode", "5002"), ("key", REAL_LENGTH_KEY)),
        )
    with pytest.raises(KorailProtocolError, match="route is not allowed"):
        assert_netfunnel_request(
            "GET",
            "/classes/com.korail.mobile.login.Login",
            (("opcode", "5002"), ("key", REAL_LENGTH_KEY)),
        )


def test_safety_accepts_a_256_character_key_and_rejects_a_malformed_one():
    # The regression the SRT sibling shipped: a real key is 256 characters, and
    # a guard written for a shorter one refuses every release silently.
    assert_netfunnel_request(
        "GET",
        KORAIL_NETFUNNEL_PATH,
        (("opcode", "5004"), ("key", REAL_LENGTH_KEY)),
    )
    for bad in ("", "has space", "a" * 513, "semi;colon"):
        with pytest.raises(KorailProtocolError, match="key parameter"):
            assert_netfunnel_request(
                "GET",
                KORAIL_NETFUNNEL_PATH,
                (("opcode", "5004"), ("key", bad)),
            )


def test_safety_constrains_the_service_and_action_ids():
    with pytest.raises(KorailProtocolError, match="service id"):
        assert_netfunnel_request(
            "GET",
            KORAIL_NETFUNNEL_PATH,
            (("opcode", "5101"), ("sid", "service_2"), ("aid", "act_8")),
        )
    with pytest.raises(KorailProtocolError, match="action id"):
        assert_netfunnel_request(
            "GET",
            KORAIL_NETFUNNEL_PATH,
            (
                ("opcode", "5101"),
                ("sid", KORAIL_NETFUNNEL_SERVICE_ID),
                ("aid", "act_10"),
            ),
        )


def test_registered_contracts_are_exactly_the_three_we_issue():
    assert set(KORAIL_NETFUNNEL_QUERY_CONTRACTS) == {"5101", "5002", "5004"}
    assert KORAIL_NETFUNNEL_ROUTES == {("GET", "/ts.wseq")}
    # All eight action ids the app declares (K4/g.java:43-51), no more.
    assert KORAIL_NETFUNNEL_ACTION_IDS == {
        "act_4",
        "act_6",
        "act_8",
        "act_8_2",
        "act_14",
        "act_18",
        "act_21",
        "act_22",
    }


def test_netfunnel_origin_is_pinned_to_the_queue_host():
    assert_korail_netfunnel_origin(KORAIL_NETFUNNEL_URL)
    assert_korail_netfunnel_origin("https://nf.letskorail.com:443")
    for bad in (
        "http://nf.letskorail.com",
        "https://smart.letskorail.com",
        # The queue names another node in ip/port and the app follows it
        # (T6/d.java:17-19). We never do.
        "https://rnf14.letskorail.com",
        "https://nf.letskorail.com:8443",
        "https://nf.letskorail.com/ts.wseq",
        "https://user:pw@nf.letskorail.com",
    ):
        with pytest.raises(KorailProtocolError):
            assert_korail_netfunnel_origin(bad)


# ---------------------------------------------------------------------------
# Status handling: 200 pass, 201 wait, 502 already-complete.
# ---------------------------------------------------------------------------


def test_200_is_a_pass_carrying_the_key():
    token = parse_queue_response(
        f"200:key={REAL_LENGTH_KEY}&nwait=0&nnext=0&tps=0.000000&ttl=0",
        action="act_8",
    )
    assert token.code == "200"
    assert token.key == REAL_LENGTH_KEY
    assert token.wait_count == 0
    assert not is_queued(token)


def test_201_is_a_wait_not_a_failure():
    token = parse_queue_response(
        f"201:key={REAL_LENGTH_KEY}&nwait=4213&nnext=100&ttl=7",
        action="act_8",
    )
    assert is_queued(token)
    assert token.wait_count == 4213
    assert queue_wait_seconds(token) == 7


def test_202_continue_debug_is_also_a_wait():
    assert is_queued(
        parse_queue_response(f"202:key={REAL_LENGTH_KEY}&ttl=1", action="act_8")
    )


def test_300_bypass_passes_without_a_key():
    # T6/g.java:909 counts Bypass as a success; there is no place in line, so
    # there is nothing to issue a key for.
    token = parse_queue_response("300:", action="act_8")
    assert token.code == "300"
    assert token.key == ""
    assert not is_queued(token)


def test_200_without_a_key_is_refused():
    with pytest.raises(KorailNetFunnelError, match="non-empty key"):
        parse_queue_response("200:nwait=0&ttl=0", action="act_8")


def test_502_is_a_failure_for_chk_enter_but_a_release_for_set_complete():
    # 502 TsErrorAComplete = "already complete". For a chkEnter that is an
    # error; for a setComplete our question is "is my slot released?" and both
    # 200 and 502 answer yes. The APK has no opinion on the latter — T6/d.java's
    # Complete() never reads the reply — so accepting it is our inference.
    with pytest.raises(KorailNetFunnelError) as caught:
        parse_queue_response("502:", action="act_8")
    assert caught.value.code == "502"
    assert not isinstance(caught.value, KorailQueueRejectedError)

    assert parse_set_complete_response("502:", action="act_8").code == "502"
    assert (
        parse_set_complete_response("200:utime=1234", action="act_8").code
        == "200"
    )


def test_set_complete_rejects_a_status_that_is_neither_200_nor_502():
    with pytest.raises(KorailNetFunnelError, match="did not release"):
        parse_set_complete_response("505:", action="act_8")


def test_301_and_302_are_a_refusal_rather_than_a_malfunction():
    # T6/g.d.isBlocking() (T6/g.java:892-894) gives the pair its own predicate,
    # separate from isError().
    for code in ("301", "302"):
        with pytest.raises(KorailQueueRejectedError) as caught:
            parse_queue_response(f"{code}:", action="act_8")
        assert caught.value.code == code


def test_303_express_number_is_not_folded_into_the_refusal_bucket():
    # The app counts ExpressNumber as a SUCCESS (T6/g.java:909); we have never
    # seen one, so it stays a plain error rather than being guessed either way.
    with pytest.raises(KorailNetFunnelError) as caught:
        parse_queue_response("303:", action="act_8")
    assert not isinstance(caught.value, KorailQueueRejectedError)


def test_the_javascript_dialects_body_is_rejected_and_says_so():
    # T6/i.java:36-42 would parse "5002" as the status code and find no key, so
    # the app cannot read this body either. The error names the cause instead of
    # guessing, because this is the one assumption a live run has never checked.
    body = (
        "NetFunnel.gRtype=4999;NetFunnel.gControl.result="
        f"'5002:200:key={REAL_LENGTH_KEY}&nwait=0';"
    )
    with pytest.raises(KorailNetFunnelError, match="native SDK"):
        parse_queue_response(body, action="act_8")


def test_a_body_with_no_colon_is_rejected():
    with pytest.raises(KorailNetFunnelError, match="native SDK"):
        parse_netfunnel_body("nonsense", action="act_8")


def test_a_parameter_value_containing_an_equals_sign_survives():
    token = parse_netfunnel_body("200:key=AB=CD&nwait=0", action="act_8")
    assert token.key == "AB=CD"


# ---------------------------------------------------------------------------
# The ttl clamp.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("ttl", "expected"),
    [
        ("", MIN_TTL_SECONDS),
        ("0", MIN_TTL_SECONDS),
        ("1", 1),
        ("7", 7),
        ("30", MAX_TTL_SECONDS),
        ("900", MAX_TTL_SECONDS),
        ("garbage", MIN_TTL_SECONDS),
    ],
)
def test_ttl_is_clamped_the_way_the_app_clamps_it(ttl, expected):
    # T6/i.java:175-181 with max_ttl=30 (T6/h.java:40) and min=1
    # (T6/g.java:462). Note 30, NOT the JS bundle's TS_MAX_TTL of 5.
    token = KorailNetFunnelToken(
        action="act_8",
        key=REAL_LENGTH_KEY,
        code="201",
        params={"ttl": ttl} if ttl else {},
    )
    assert queue_wait_seconds(token) == expected


def test_max_ttl_is_the_native_sdks_thirty_not_the_js_bundles_five():
    assert (MAX_TTL_SECONDS, MIN_TTL_SECONDS) == (30, 1)


# ---------------------------------------------------------------------------
# The default-off guarantee.
# ---------------------------------------------------------------------------


def test_netfunnel_is_off_by_default():
    assert KorailConfig().netfunnel_enabled is False


def test_a_disabled_config_cannot_even_construct_a_queue_client():
    with pytest.raises(KorailNetFunnelError, match="disabled by default"):
        KorailNetFunnelClient(KorailConfig())
    with pytest.raises(KorailNetFunnelError, match="disabled by default"):
        KorailNetFunnelClient()


def test_a_disabled_client_makes_no_request_at_all():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        calls.append(request)
        return httpx.Response(200, text="200:")

    with pytest.raises(KorailNetFunnelError):
        _client(handler, config=KorailConfig())
    assert calls == []


def test_the_queue_defaults_are_the_apps_own():
    config = KorailConfig()
    assert config.netfunnel_url == "https://nf.letskorail.com"
    # KTApplication.java:85 setTimeout(3) — not the API client's 60.
    assert config.netfunnel_timeout == KORAIL_NETFUNNEL_TIMEOUT_SECONDS == 3.0
    assert config.timeout == 60.0


# ---------------------------------------------------------------------------
# The round trips, over a mock transport.
# ---------------------------------------------------------------------------


def test_enter_sends_exactly_the_5101_request():
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, text=f"200:key={REAL_LENGTH_KEY}&ttl=0")

    client = _client(handler)
    token = client.enter(KorailNetFunnelAction.RESERVE)
    assert token.key == REAL_LENGTH_KEY
    assert token.action == "act_14"
    assert len(seen) == 1
    assert seen[0].host == "nf.letskorail.com"
    assert seen[0].path == "/ts.wseq"
    assert seen[0].raw_path.decode() == (
        "/ts.wseq?opcode=5101&sid=service_1&aid=act_14"
    )


def test_release_sends_the_5004_request_with_the_full_key():
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path.decode())
        return httpx.Response(200, text="200:utime=17")

    client = _client(handler)
    client.release(
        KorailNetFunnelToken(action="act_8", key=REAL_LENGTH_KEY, code="200")
    )
    assert seen == [f"/ts.wseq?opcode=5004&key={REAL_LENGTH_KEY}"]


def test_release_of_a_bypass_token_sends_nothing():
    # A 300 carries no key, so there is no slot to release — the same
    # short-circuit T6/d.Complete() applies at T6/d.java:70-73.
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        calls.append(request)
        return httpx.Response(200, text="200:")

    _client(handler).release(
        KorailNetFunnelToken(action="act_8", key="", code="300")
    )
    assert calls == []


def test_a_failed_release_raises_rather_than_being_swallowed():
    # The SRT cautionary tale, inverted: a release that does not release must be
    # audible on the success path.
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="507:")

    with pytest.raises(KorailNetFunnelError, match="did not release"):
        _client(handler).release(
            KorailNetFunnelToken(
                action="act_8",
                key=REAL_LENGTH_KEY,
                code="200",
            )
        )


def test_an_http_error_from_the_queue_is_a_transport_error():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="")

    with pytest.raises(KorailTransportError):
        _client(handler).enter(KorailNetFunnelAction.INQUIRY)


# ---------------------------------------------------------------------------
# Bounded polling.
# ---------------------------------------------------------------------------


class _FakeClock:
    """A monotonic clock that only advances when the fake sleeper sleeps."""

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds

    def __call__(self) -> float:
        return self.now


def test_polling_stops_as_soon_as_the_queue_admits_us():
    clock = _FakeClock()
    bodies = [
        f"201:key={REAL_LENGTH_KEY}&nwait=90&ttl=2",
        f"201:key={REAL_LENGTH_KEY}&nwait=40&ttl=2",
        f"200:key={REAL_LENGTH_KEY}&nwait=0&ttl=0",
    ]
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.params["opcode"])
        return httpx.Response(200, text=bodies[len(seen) - 1])

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    token = client.acquire(KorailNetFunnelAction.INQUIRY)
    assert token.code == "200"
    # One 5101 to join the line, then a 5002 per poll.
    assert seen == ["5101", "5002", "5002"]
    assert clock.slept == [2, 2]


def test_polling_gives_up_on_the_iteration_cap():
    clock = _FakeClock()
    calls: list[int] = []

    def handler(_: httpx.Request) -> httpx.Response:
        calls.append(1)
        # ttl=1 so the wall-clock ceiling is never the binding constraint.
        return httpx.Response(200, text=f"201:key={REAL_LENGTH_KEY}&ttl=1")

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    with pytest.raises(KorailNetFunnelError, match=f"within {QUEUE_POLL_LIMIT} polls"):
        client.acquire(KorailNetFunnelAction.INQUIRY)
    # The 5101 plus exactly QUEUE_POLL_LIMIT chkEnters, and then it stops. The
    # app would have looped forever here (T6/g.java:449, `while (true)`).
    assert len(calls) == QUEUE_POLL_LIMIT + 1
    assert len(clock.slept) == QUEUE_POLL_LIMIT
    assert clock.now < QUEUE_WAIT_LIMIT_SECONDS


def test_polling_gives_up_on_the_wall_clock_cap_before_sleeping_past_it():
    clock = _FakeClock()

    def handler(_: httpx.Request) -> httpx.Response:
        # ttl=30 is the app's own maximum, so three sleeps would exceed the 60s
        # ceiling — and the third is never taken.
        return httpx.Response(200, text=f"201:key={REAL_LENGTH_KEY}&ttl=30")

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    with pytest.raises(KorailNetFunnelError, match="within 60s"):
        client.acquire(KorailNetFunnelAction.INQUIRY)
    assert clock.slept == [30, 30]
    assert clock.now <= QUEUE_WAIT_LIMIT_SECONDS


def test_a_queue_refusal_during_polling_propagates_immediately():
    clock = _FakeClock()
    bodies = [f"201:key={REAL_LENGTH_KEY}&ttl=1", "302:"]
    seen: list[int] = []

    def handler(_: httpx.Request) -> httpx.Response:
        seen.append(1)
        return httpx.Response(200, text=bodies[len(seen) - 1])

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    with pytest.raises(KorailQueueRejectedError):
        client.acquire(KorailNetFunnelAction.INQUIRY)
    assert len(seen) == 2


# ---------------------------------------------------------------------------
# Slot release on both the success and the failure path.
# ---------------------------------------------------------------------------


def test_slot_releases_after_a_successful_body():
    opcodes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        opcode = request.url.params["opcode"]
        opcodes.append(opcode)
        if opcode == "5101":
            return httpx.Response(200, text=f"200:key={REAL_LENGTH_KEY}&ttl=0")
        return httpx.Response(200, text="200:utime=17")

    with _client(handler).slot(KorailNetFunnelAction.PAY) as token:
        assert token.key == REAL_LENGTH_KEY
    assert opcodes == ["5101", "5004"]


def test_slot_releases_after_the_body_raises_and_keeps_the_original_error():
    opcodes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        opcodes.append(request.url.params["opcode"])
        if opcodes[-1] == "5101":
            return httpx.Response(200, text=f"200:key={REAL_LENGTH_KEY}&ttl=0")
        return httpx.Response(200, text="200:utime=17")

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with _client(handler).slot(KorailNetFunnelAction.RESERVE):
            raise Boom("the gated operation failed")
    # The app releases from onPostExecute (BaseDaoHelper.java:105-107), which
    # runs whether or not the gated call raised. So do we.
    assert opcodes == ["5101", "5004"]


def test_a_failed_release_on_the_failure_path_is_noted_not_substituted():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params["opcode"] == "5101":
            return httpx.Response(200, text=f"200:key={REAL_LENGTH_KEY}&ttl=0")
        return httpx.Response(200, text="507:")

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom) as caught:
        with _client(handler).slot(KorailNetFunnelAction.RESERVE):
            raise Boom("the gated operation failed")
    # The caller's error survives, and the leak is recorded rather than hidden.
    notes = getattr(caught.value, "__notes__", [])
    assert any("slot release also failed" in note for note in notes)


def test_a_failed_release_on_the_success_path_is_raised():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params["opcode"] == "5101":
            return httpx.Response(200, text=f"200:key={REAL_LENGTH_KEY}&ttl=0")
        return httpx.Response(200, text="507:")

    with pytest.raises(KorailNetFunnelError, match="did not release"):
        with _client(handler).slot(KorailNetFunnelAction.RESERVE):
            pass


def test_slot_releases_even_when_the_queue_bypassed_us_without_a_key():
    opcodes: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        opcodes.append(request.url.params["opcode"])
        return httpx.Response(200, text="300:")

    with _client(handler).slot(KorailNetFunnelAction.INQUIRY) as token:
        assert token.key == ""
    # Nothing to release, so nothing sent — but the context manager still ran
    # its release path.
    assert opcodes == ["5101"]


# ---------------------------------------------------------------------------
# The action-id map.
# ---------------------------------------------------------------------------


def test_inquiry_action_switches_on_the_peak_season_flag():
    # b5/c.java:439 picks act_8_2 when isPeakSeason(departure date), and
    # S4/C0805e.java:116-121 answers that from the 열차운행달력 the app already
    # downloaded — so it is a lookup, not a calendar rule to reimplement.
    assert inquiry_action(peak_season=False) is KorailNetFunnelAction.INQUIRY
    assert (
        inquiry_action(peak_season=True)
        is KorailNetFunnelAction.PEAK_SEASON_INQUIRY
    )
    assert KorailNetFunnelAction.PEAK_SEASON_INQUIRY.value == "act_8_2"


def test_gated_operations_map_to_the_action_ids_the_apk_pairs_them_with():
    assert KORAIL_NETFUNNEL_GATED_OPERATIONS == {
        "search_trains": KorailNetFunnelAction.INQUIRY,
        "search_product_trains": KorailNetFunnelAction.PRODUCT,
        "reserve": KorailNetFunnelAction.RESERVE,
        "confirm_standby_hold": KorailNetFunnelAction.RESERVE,
        "pay_with_card": KorailNetFunnelAction.PAY,
        "pay_with_fake_card": KorailNetFunnelAction.PAY,
        "get_reservation_history": KorailNetFunnelAction.RESERVED,
    }
    # act_4 and act_22 are declared by the app and reached by nothing in it, so
    # they are exposed as constants but map to no operation here.
    unmapped = KORAIL_NETFUNNEL_ACTION_IDS - {
        action.value for action in KORAIL_NETFUNNEL_GATED_OPERATIONS.values()
    }
    assert unmapped == {"act_4", "act_22", "act_8_2"}


# ---------------------------------------------------------------------------
# The documentation contract.
#
# The single most important thing these docs have to keep saying is that this
# subsystem is BUILT and UNPROVEN. A queue client that is quietly described as
# working, when the server has never queued us and the response shape has never
# been seen, would be the most misleading sentence in the repository.
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_docs_say_netfunnel_is_implemented_but_not_live_exercised():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "### NetFunnel virtual waiting room" in readme
    assert "## NetFunnel virtual waiting room" in progress
    for document in (readme, progress, changelog):
        assert "NOT live-exercised" in document
    assert "off by default" in readme.casefold()
    # The peak-season action is the reason the subsystem exists; each document
    # has to name it.
    for document in (readme, progress, changelog):
        assert "act_8_2" in document


def test_docs_record_the_unverified_response_shape():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    for document in (readme, progress):
        assert "<code>:<params>" in document
        assert "NetFunnel.gRtype" in document


def test_release_gap_plan_no_longer_claims_korail_has_no_netfunnel():
    plan = (ROOT / "docs/RELEASE_GAP_PLAN.md").read_text(encoding="utf-8")
    # The withdrawn claim, which survived in the srtgo-corrections appendix long
    # after the body of the document had corrected it.
    assert "Korail\n  uses **no** NetFunnel at all" not in plan
    assert "uses **no** NetFunnel at all — only SRT does." not in plan
    assert "WITHDRAWN and IMPLEMENTED" in plan


def test_the_opcode_table_is_the_apks_own():
    # T6/c.java:6-11 — identical to SRT's, which is the evidence that the two
    # apps embed two SDKs for one product.
    assert {op.name: op.value for op in KorailNetFunnelOpcode} == {
        "CHK_ENTER": "5002",
        "ALIVE_NOTICE": "5003",
        "SET_COMPLETE": "5004",
        "GET_TID_CHK_ENTER": "5101",
        "INIT": "5105",
        "STOP": "5106",
    }
