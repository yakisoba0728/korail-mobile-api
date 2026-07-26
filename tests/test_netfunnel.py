"""Offline tests for the NetFunnel virtual waiting room.

EVERY TEST HERE IS A FIXTURE TEST, BUT THE FIXTURES ARE NOT ALL GUESSES. Two
live probes on 2026-07-26 settled the wire format, the entry sequence and the
routing, and their transcripts are quoted verbatim in the fixtures below. What
is still fixture-only is the **201 queued path**: the server was not queueing,
so nobody has ever seen this client wait in an actual line, and the polling
loop, the ttl sleep and the two bounds are covered by nothing else. See the
module docstring of :mod:`korail_mobile_api.netfunnel`.

The second of those probes is why this file now asserts a HOST alongside every
opcode. The queue is a pool: ``nf.letskorail.com`` balances the entry call and
the node it lands on is the only one that can complete the session. Releasing at
the front door therefore failed about half the time — non-deterministically,
with ``503:msg="Wrong Server ID"`` — and no assertion in this file could see it,
because none of them recorded where a request went.

No test in this file may reach the network. ``httpx.MockTransport`` is the only
transport used, and the tests that exercise the polling loop inject a fake
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
    KORAIL_NETFUNNEL_KEYED_OPCODES,
    KORAIL_NETFUNNEL_NODE_OPCODES,
    KORAIL_NETFUNNEL_QUERY_CONTRACTS,
    KORAIL_NETFUNNEL_ROUTES,
    assert_korail_netfunnel_node_origin,
    assert_korail_netfunnel_opcode_origin,
    assert_korail_netfunnel_origin,
    assert_netfunnel_request,
    korail_netfunnel_node_url,
)


# A REALISTIC KEY. The one real NetFunnel key this project has ever captured (on
# the SRT side, from the same nf.letskorail.com host) was 256 characters of
# uppercase hex. That length is the whole reason this constant exists: the
# sibling implementation bounded the field at 128, so every release request was
# refused before it was sent and the failure was swallowed. A short "ABC123" in a
# fixture would have passed that broken guard too.
REAL_LENGTH_KEY = "0F3B" * 64
ENABLED = KorailConfig(netfunnel_enabled=True)

# THE LIVE 2026-07-26 TRANSCRIPT, as fixtures. These are the bodies
# nf.letskorail.com actually returned, with only the key material replaced by
# hex of the same length and the 5101 reply's node name (which the probe
# recorded elided, as `ip=...`) filled in with the one the 5004 reply did name.
# Everything else — parameter names, order, `tps=0.000000`, the empty `key=` on
# a successful release, the quoted `msg` — is verbatim.
#
# The two lengths are the point of the pair: 5101 issued 252 characters and the
# chkEnter that superseded it issued 104. Neither is the 256 the SRT side saw,
# which is why the guard bounds keys at 512 and must not be tightened to any of
# the three observed lengths.
TICKET_KEY = "0F3B" * 63
SESSION_KEY = "9C4A" * 26
TICKET_BODY = (
    f"200:key={TICKET_KEY}&nwait=0&nnext=0&tps=0.000000&ttl=0"
    "&ip=rnf13.letskorail.com&port=443"
)
SESSION_BODY = f"200:key={SESSION_KEY}&nwait=0&nnext=0&tps=0.000000&ttl=0"
RELEASED_BODY = (
    "200:key=&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=rnf13.letskorail.com"
    "&port=443&vwr_html=&live_message=&chk_enter_cnt=0"
)
WRONG_SERVER_ID_BODY = '503:msg="Wrong Server ID"'

# THE QUEUE IS A POOL, DIAGNOSED LIVE ON 2026-07-26. `nf.letskorail.com` is a
# front door that balances the entry call; the node it lands on is the only one
# that can complete the session, and it names itself in the reply's `ip`/`port`.
# Sending `setComplete` to the front door instead answered
# 503:msg="Wrong Server ID" on three of five cycles and 200 on the other two —
# the two being the balancer happening to land back on the owning node.
#
# The three node names below are the ones the probe actually saw. They are the
# whole evidence base for the admissibility rule, so they are spelled out here
# rather than generated.
FRONT_DOOR_HOST = "nf.letskorail.com"
OBSERVED_NODE_HOSTS = (
    "rnf12.letskorail.com",
    "rnf13.letskorail.com",
    "rnf14.letskorail.com",
)
# The node TICKET_BODY and RELEASED_BODY name, i.e. where the session lives for
# every fixture below that walks the whole sequence.
NODE_HOST = "rnf13.letskorail.com"


def _sequence_handler(
    bodies: dict[str, str],
    seen: list[tuple[str, str, str]],
):
    """A MockTransport handler that answers per OPCODE, recording the order.

    Every test below that walks the entry sequence needs to distinguish the
    5002 from the 5004, which is exactly what the pre-2026-07-26 fixtures could
    not do: they answered "5101, or else the release", so the newly-required
    chkEnter would have been served the setComplete's reply.

    THE RECORDED TUPLE GREW A HOST ON 2026-07-26, and that is the second pin
    that moved that day. It used to be ``(opcode, key)``, which could not tell
    the front door from a queue node — so the leak this file now covers was
    invisible to every sequence assertion in it. It is ``(opcode, host, key)``
    now, and the host is asserted alongside the key everywhere the sequence is.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        opcode = request.url.params["opcode"]
        seen.append(
            (opcode, request.url.host, request.url.params.get("key", ""))
        )
        return httpx.Response(200, text=bodies[opcode])

    return handler


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


def test_netfunnel_origin_is_pinned_to_the_front_door():
    assert_korail_netfunnel_origin(KORAIL_NETFUNNEL_URL)
    assert_korail_netfunnel_origin("https://nf.letskorail.com:443")
    for bad in (
        "http://nf.letskorail.com",
        "https://smart.letskorail.com",
        # THIS PIN DID NOT MOVE ON 2026-07-26, AND THAT IS THE POINT. The queue
        # really is a pool and the session really does live on a node, but this
        # function guards the CONFIGURED origin and the 5101 entry call, and
        # neither of those may be a node. The wider guard is a separate function
        # so that widening one cannot widen the other by accident.
        "https://rnf14.letskorail.com",
        "https://nf.letskorail.com:8443",
        "https://nf.letskorail.com/ts.wseq",
        "https://user:pw@nf.letskorail.com",
    ):
        with pytest.raises(KorailProtocolError):
            assert_korail_netfunnel_origin(bad)


# ---------------------------------------------------------------------------
# The pool, and the rule that admits it. Diagnosed live on 2026-07-26: see the
# block comment above KORAIL_NETFUNNEL_NODE_HOST_RE in safety.py for the
# transcript. The rule is CONSTRAINED, not trusting — a reply names a node, and
# the guard decides whether that name is one the pool could have produced.
# ---------------------------------------------------------------------------


def test_the_node_rule_admits_every_node_the_probe_saw():
    # The whole evidence base, and all of it must pass.
    for host in OBSERVED_NODE_HOSTS:
        assert korail_netfunnel_node_url(host, "443") == f"https://{host}"
        assert_korail_netfunnel_node_origin(f"https://{host}")


def test_the_node_rule_admits_the_front_door_naming_itself():
    # The balancer naming itself grants no reach the client did not already
    # have, so it is admitted rather than treated as an attack.
    assert korail_netfunnel_node_url(FRONT_DOOR_HOST, "443") == (
        f"https://{FRONT_DOOR_HOST}"
    )
    assert_korail_netfunnel_node_origin(KORAIL_NETFUNNEL_URL)


def test_a_reply_that_names_no_node_at_all_is_not_a_redirection():
    # T6/d.makeURL's `getHost().length() <= 0 || getPort() <= 0` branch: with
    # nothing named there is nothing to follow, and the front door is where the
    # request goes. This is the ONE legitimate front-door fall-back, and it is
    # not a fall-back from a refusal — a refusal raises.
    assert korail_netfunnel_node_url("", "") == ""


@pytest.mark.parametrize(
    "host",
    [
        # Not the queue's naming at all.
        "smart.letskorail.com",
        "evil.example.com",
        # Suffix and prefix tricks on a name that contains a real one.
        "rnf13.letskorail.com.evil.example.com",
        "evil-rnf13.letskorail.com",
        "rnf13.evil.example.com",
        "a.rnf13.letskorail.com",
        # Shaped like a node but not one the pool hands out.
        "rnf.letskorail.com",
        "rnfX.letskorail.com",
        "rnf0.letskorail.com",
        "rnf013.letskorail.com",
        "rnf100.letskorail.com",
        # Case the wire has never used; a guard comparing response bytes should
        # not be the place where DNS case-insensitivity is relitigated.
        "RNF13.letskorail.com",
        # Not a bare hostname at all.
        "rnf13.letskorail.com:443",
        "rnf13.letskorail.com/ts.wseq",
        "user:pw@rnf13.letskorail.com",
        "https://rnf13.letskorail.com",
        # A port without a host is naming a node badly, not naming none.
        "",
    ],
)
def test_a_host_outside_the_pool_is_refused_rather_than_falling_back(host):
    # HARD ERROR, NOT A FALL-BACK. Quietly reverting to the front door here is
    # what produced the flaky release: it turns "this reply is lying" into "this
    # slot leaked", and a leaked slot makes no noise whatsoever.
    with pytest.raises(KorailProtocolError, match="queue's own nodes"):
        korail_netfunnel_node_url(host, "443")


@pytest.mark.parametrize("port", ["80", "8443", "0", "", "443 ", "0443"])
def test_a_port_other_than_443_is_refused_rather_than_followed(port):
    # The port is not followed on the server's say-so either. 443 is the only
    # value any reply has carried and the only one the origin guard permits.
    with pytest.raises(KorailProtocolError, match="named port"):
        korail_netfunnel_node_url(NODE_HOST, port)


def test_the_node_origin_guard_is_as_structural_as_the_front_door_one():
    # Widening the hostname rule widened nothing else: scheme, userinfo, path,
    # query, fragment and port are checked exactly as they are for the front
    # door, because both guards share one implementation.
    for bad in (
        f"http://{NODE_HOST}",
        f"https://{NODE_HOST}:8443",
        f"https://{NODE_HOST}/ts.wseq",
        f"https://user:pw@{NODE_HOST}",
        f"https://{NODE_HOST}?opcode=5004",
        f"https://{NODE_HOST}#x",
        "https://smart.letskorail.com",
    ):
        with pytest.raises(KorailProtocolError):
            assert_korail_netfunnel_node_origin(bad)


def test_the_entry_opcode_may_not_be_sent_to_a_node():
    # Which host each opcode goes to is answered by the guard, not by whichever
    # call site built the URL. 5101 is the call the front door balances.
    assert_korail_netfunnel_opcode_origin("5101", KORAIL_NETFUNNEL_URL)
    with pytest.raises(KorailProtocolError):
        assert_korail_netfunnel_opcode_origin("5101", f"https://{NODE_HOST}")
    for session_opcode in ("5002", "5004"):
        assert_korail_netfunnel_opcode_origin(
            session_opcode,
            f"https://{NODE_HOST}",
        )
        assert_korail_netfunnel_opcode_origin(
            session_opcode,
            KORAIL_NETFUNNEL_URL,
        )


def test_the_session_opcodes_are_exactly_the_ones_that_carry_a_key():
    # Not a coincidence: a session is identified by its key and lives on its
    # node, so the opcodes that carry one are the opcodes that must reach the
    # other. They are separate constants because they answer different
    # questions, and this is the assertion that they agree.
    assert KORAIL_NETFUNNEL_NODE_OPCODES == {"5002", "5004"}
    assert KORAIL_NETFUNNEL_NODE_OPCODES == KORAIL_NETFUNNEL_KEYED_OPCODES
    assert (
        KorailNetFunnelOpcode.GET_TID_CHK_ENTER.value
        not in KORAIL_NETFUNNEL_NODE_OPCODES
    )


def test_the_url_builders_refuse_the_wrong_host_for_their_opcode():
    # The guard is reached through the builders, not only by calling it
    # directly, so a future call site cannot route an opcode by mistake.
    with pytest.raises(KorailProtocolError):
        build_get_tid_chk_enter_url(
            f"https://{NODE_HOST}",
            action=KorailNetFunnelAction.INQUIRY,
        )
    assert build_chk_enter_url(
        f"https://{NODE_HOST}", key=REAL_LENGTH_KEY
    ) == (f"https://{NODE_HOST}/ts.wseq?opcode=5002&key={REAL_LENGTH_KEY}")
    assert build_set_complete_url(
        f"https://{NODE_HOST}", key=REAL_LENGTH_KEY
    ) == (f"https://{NODE_HOST}/ts.wseq?opcode=5004&key={REAL_LENGTH_KEY}")
    for builder in (build_chk_enter_url, build_set_complete_url):
        with pytest.raises(KorailProtocolError):
            builder("https://smart.letskorail.com", key=REAL_LENGTH_KEY)


def test_a_parsed_reply_carries_the_node_that_answered_it():
    token = parse_netfunnel_body(TICKET_BODY, action="act_8")
    assert token.params["ip"] == NODE_HOST
    assert token.params["port"] == "443"
    assert token.node == f"https://{NODE_HOST}"
    # A reply that names nothing carries no node, which means the front door.
    assert parse_netfunnel_body(SESSION_BODY, action="act_8").node == ""


def test_a_reply_naming_a_host_outside_the_pool_is_refused_at_parse_time():
    # Doing this in the parser means every caller of every parse function gets
    # the check and no code path can hold a token whose node was never vetted.
    body = f"200:key={SESSION_KEY}&ip=evil.example.com&port=443"
    with pytest.raises(KorailProtocolError, match="queue's own nodes"):
        parse_netfunnel_body(body, action="act_8")
    with pytest.raises(KorailProtocolError):
        parse_queue_response(body, action="act_8")
    with pytest.raises(KorailProtocolError):
        parse_set_complete_response(
            "200:key=&ip=evil.example.com&port=443",
            action="act_8",
        )


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
# The entry sequence: 5101 -> 5002 -> (work) -> 5004, live-confirmed 2026-07-26.
#
# The defect these pin: `acquire` used to return the 5101 reply directly, so
# `release` sent the TICKET to setComplete and the server answered
# 503:msg="Wrong Server ID" every time. Only a key that chkEnter issued is a
# completable session, and each step's key supersedes the one before it.
# ---------------------------------------------------------------------------


def test_the_live_transcript_keys_have_the_lengths_the_probe_saw():
    assert len(TICKET_KEY) == 252
    assert len(SESSION_KEY) == 104
    # Different lengths, different values — the whole point of the exchange.
    assert TICKET_KEY != SESSION_KEY
    # ...and both inside the 512 the guard allows, which is why it stays at 512.
    for key in (TICKET_KEY, SESSION_KEY):
        assert_netfunnel_request(
            "GET",
            KORAIL_NETFUNNEL_PATH,
            (("opcode", "5004"), ("key", key)),
        )


def test_acquire_exchanges_the_ticket_for_a_session_before_returning():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": RELEASED_BODY},
            seen,
        )
    )

    token = client.acquire(KorailNetFunnelAction.INQUIRY)

    # 5101 with no key at the front door, then 5002 carrying the TICKET the
    # 5101 issued, at the node the 5101 named.
    assert seen == [
        ("5101", FRONT_DOOR_HOST, ""),
        ("5002", NODE_HOST, TICKET_KEY),
    ]
    # The token that comes back is the chkEnter's, not the ticket.
    assert token.key == SESSION_KEY
    assert token.key != TICKET_KEY
    assert token.code == "200"
    # ...and it carries the node, so the caller can release at the right host.
    assert token.node == f"https://{NODE_HOST}"


def test_the_full_sequence_releases_with_the_key_chk_enter_issued():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": RELEASED_BODY},
            seen,
        )
    )

    with client.slot(KorailNetFunnelAction.RESERVE) as token:
        assert token.key == SESSION_KEY

    assert seen == [
        ("5101", FRONT_DOOR_HOST, ""),
        ("5002", NODE_HOST, TICKET_KEY),
        ("5004", NODE_HOST, SESSION_KEY),
    ]


def test_the_entry_call_goes_to_the_front_door_and_the_session_to_the_node():
    # THE 2026-07-26 DEFECT, stated as a routing pin rather than as a sequence.
    # Every opcode used to go to the front door, which released the slot only
    # when the balancer happened to land back on the owning node — roughly half
    # the time. 5101 is the call the front door balances; 5002 and 5004 belong
    # to the session and must reach the node that issued it.
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": RELEASED_BODY},
            seen,
        )
    )

    with client.slot(KorailNetFunnelAction.INQUIRY):
        pass

    hosts = {opcode: host for opcode, host, _ in seen}
    assert hosts == {
        "5101": FRONT_DOOR_HOST,
        "5002": NODE_HOST,
        "5004": NODE_HOST,
    }
    # The entry call is the ONLY one on the front door, and the node it went to
    # is the one the reply named rather than anything configured.
    assert NODE_HOST != FRONT_DOOR_HOST
    assert f"ip={NODE_HOST}" in TICKET_BODY
    assert ENABLED.netfunnel_url == f"https://{FRONT_DOOR_HOST}"


def test_the_5002_is_sent_even_when_nobody_is_queued():
    # The trap: 5101 answers 200 with nwait=0 and looks like a finished
    # handshake. It is not — the key it issued cannot be completed by the front
    # door. Whether the NODE would complete it was never probed, so the extra
    # round trip stays rather than being optimised away on a guess.
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler({"5101": TICKET_BODY, "5002": SESSION_BODY}, seen)
    )

    client.acquire(KorailNetFunnelAction.PAY)

    assert [opcode for opcode, _host, _key in seen] == ["5101", "5002"]


def test_a_201_from_chk_enter_supersedes_the_key_on_every_poll():
    # The queued path, which the live server did NOT exercise: it was not
    # queueing on 2026-07-26, so this shape is built from the confirmed one and
    # remains offline-only evidence.
    queued_first = f"201:key={SESSION_KEY}&nwait=4213&nnext=100&ttl=2"
    reissued_key = "5E17" * 26
    queued_again = f"201:key={reissued_key}&nwait=12&nnext=100&ttl=2"
    admitted_key = "A2D9" * 26
    admitted = f"200:key={admitted_key}&nwait=0&nnext=0&tps=0.000000&ttl=0"

    bodies = [TICKET_BODY, queued_first, queued_again, admitted, RELEASED_BODY]
    seen: list[tuple[str, str, str]] = []
    clock = _FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.url.params["opcode"],
                request.url.host,
                request.url.params.get("key", ""),
            )
        )
        return httpx.Response(200, text=bodies[len(seen) - 1])

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    with client.slot(KorailNetFunnelAction.INQUIRY) as token:
        assert token.key == admitted_key

    # Each request carries the key the PREVIOUS reply issued, never the first
    # one — and the release carries the last of all. None of these 201s names a
    # node, so the one the 5101 named stays in force for the whole wait.
    assert seen == [
        ("5101", FRONT_DOOR_HOST, ""),
        ("5002", NODE_HOST, TICKET_KEY),
        ("5002", NODE_HOST, SESSION_KEY),
        ("5002", NODE_HOST, reissued_key),
        ("5004", NODE_HOST, admitted_key),
    ]
    # Two waits, so two sleeps; the entry 5002 is not preceded by one.
    assert clock.slept == [2, 2]


def test_a_wait_that_echoes_no_key_keeps_the_last_key_in_force():
    # parse_queue_response allows a 201 to omit the key ("we already hold one").
    # Superseding must therefore mean "the newest key there was", not "whatever
    # the newest reply said" — otherwise the next chkEnter is built with an
    # empty key and never leaves the process.
    bodies = [TICKET_BODY, "201:nwait=7&ttl=1", SESSION_BODY]
    seen: list[tuple[str, str, str]] = []
    clock = _FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.url.params["opcode"],
                request.url.host,
                request.url.params.get("key", ""),
            )
        )
        return httpx.Response(200, text=bodies[len(seen) - 1])

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    token = client.acquire(KorailNetFunnelAction.INQUIRY)

    assert seen == [
        ("5101", FRONT_DOOR_HOST, ""),
        ("5002", NODE_HOST, TICKET_KEY),
        ("5002", NODE_HOST, TICKET_KEY),
    ]
    assert token.key == SESSION_KEY


def test_a_wait_that_names_no_node_keeps_the_last_node_in_force():
    # The node supersedes exactly as the key does, and for the same reason: a
    # poll that says nothing about routing has not re-routed anything. The 201
    # here names neither, and both the key and the node from before it survive.
    bodies = [TICKET_BODY, "201:nwait=7&ttl=1", SESSION_BODY, RELEASED_BODY]
    seen: list[tuple[str, str, str]] = []
    clock = _FakeClock()

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.url.params["opcode"],
                request.url.host,
                request.url.params.get("key", ""),
            )
        )
        return httpx.Response(200, text=bodies[len(seen) - 1])

    client = _client(handler, sleeper=clock.sleep, clock=clock)
    with client.slot(KorailNetFunnelAction.INQUIRY) as token:
        # SESSION_BODY names no node either, so the admitted token still points
        # at the node the 5101 named.
        assert "ip=" not in SESSION_BODY
        assert token.node == f"https://{NODE_HOST}"

    assert [host for _opcode, host, _key in seen] == [
        FRONT_DOOR_HOST,
        NODE_HOST,
        NODE_HOST,
        NODE_HOST,
    ]


def test_a_reply_may_hand_the_session_on_to_another_node_in_the_pool():
    # Supersession is not "the 5101's node forever". If a later reply names a
    # different node of the pool, that is where the session now lives, and the
    # release has to follow it there — the same rule as the key, applied to the
    # other half of what identifies a slot.
    handed_on = (
        f"200:key={SESSION_KEY}&nwait=0&nnext=0&tps=0.000000&ttl=0"
        "&ip=rnf14.letskorail.com&port=443"
    )
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": handed_on, "5004": RELEASED_BODY},
            seen,
        )
    )

    with client.slot(KorailNetFunnelAction.RESERVE) as token:
        assert token.node == "https://rnf14.letskorail.com"

    assert seen == [
        ("5101", FRONT_DOOR_HOST, ""),
        # The 5002 still goes to the node the 5101 named...
        ("5002", NODE_HOST, TICKET_KEY),
        # ...and the 5004 goes to the one the 5002 named instead.
        ("5004", "rnf14.letskorail.com", SESSION_KEY),
    ]


def test_releasing_the_5101_ticket_surfaces_the_503_instead_of_leaking():
    # The first live failure of 2026-07-26. 503 must never join 502 in the
    # accepted set, whichever of its two causes produced it: the key was never
    # exchanged for a session (this test — re-attaching sid/aid did not help),
    # or the request reached a node that does not own the session (the pool
    # defect, covered above). Treating either as released is a silent leak.
    with pytest.raises(KorailNetFunnelError, match="never exchanged") as caught:
        parse_set_complete_response(WRONG_SERVER_ID_BODY, action="act_8")
    assert caught.value.code == "503"
    assert not isinstance(caught.value, KorailQueueRejectedError)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=WRONG_SERVER_ID_BODY)

    with pytest.raises(KorailNetFunnelError, match="never exchanged"):
        _client(handler).release(
            KorailNetFunnelToken(action="act_8", key=TICKET_KEY, code="200")
        )


def test_a_503_during_a_slot_is_audible_on_the_success_path():
    # Same failure through the context manager, which is where it actually bit:
    # the gated call succeeds and the release quietly does nothing.
    def handler(request: httpx.Request) -> httpx.Response:
        opcode = request.url.params["opcode"]
        if opcode == "5101":
            return httpx.Response(200, text=TICKET_BODY)
        if opcode == "5002":
            return httpx.Response(200, text=SESSION_BODY)
        return httpx.Response(200, text=WRONG_SERVER_ID_BODY)

    with pytest.raises(KorailNetFunnelError, match="never exchanged"):
        with _client(handler).slot(KorailNetFunnelAction.RESERVE):
            pass


def test_a_reply_naming_a_foreign_host_aborts_instead_of_falling_back():
    # The client-level statement of the same rule: a 5101 that names a host
    # outside the pool must stop the handshake, NOT quietly send the 5002 to the
    # front door. The silent fall-back is what made the release flaky, so the
    # request count is asserted as well as the exception — nothing may follow.
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {
                "5101": (
                    f"200:key={TICKET_KEY}&nwait=0&ttl=0"
                    "&ip=evil.example.com&port=443"
                ),
                "5002": SESSION_BODY,
            },
            seen,
        )
    )

    with pytest.raises(KorailProtocolError, match="queue's own nodes"):
        client.acquire(KorailNetFunnelAction.INQUIRY)
    assert [opcode for opcode, _host, _key in seen] == ["5101"]


def test_a_reply_naming_a_non_443_port_aborts_instead_of_falling_back():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {
                "5101": (
                    f"200:key={TICKET_KEY}&nwait=0&ttl=0"
                    f"&ip={NODE_HOST}&port=8443"
                ),
                "5002": SESSION_BODY,
            },
            seen,
        )
    )

    with pytest.raises(KorailProtocolError, match="named port"):
        client.acquire(KorailNetFunnelAction.INQUIRY)
    assert [opcode for opcode, _host, _key in seen] == ["5101"]


def test_a_release_at_the_front_door_is_what_the_503_was_telling_us():
    # The controlled pair from the 2026-07-26 probe, as a fixture. One session,
    # released twice: at the front door it is 503:msg="Wrong Server ID", at the
    # node that issued it, 200. "Wrong Server ID" is LITERAL — it is the pool
    # saying "that session is not mine", not a complaint about the key.
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == NODE_HOST:
            return httpx.Response(200, text=RELEASED_BODY)
        return httpx.Response(200, text=WRONG_SERVER_ID_BODY)

    client = _client(handler)
    at_the_node = KorailNetFunnelToken(
        action="act_8",
        key=SESSION_KEY,
        code="200",
        node=f"https://{NODE_HOST}",
    )
    client.release(at_the_node)

    # The same key with no node goes to the front door and is refused — which
    # is exactly the token this client used to build for every release.
    with pytest.raises(KorailNetFunnelError, match="never exchanged"):
        client.release(
            KorailNetFunnelToken(action="act_8", key=SESSION_KEY, code="200")
        )


def test_the_empty_key_of_a_successful_release_is_not_a_parse_failure():
    # 200:key= with chk_enter_cnt=0 is what a real release answered. An empty
    # key is the server saying the slot is gone; only 5101/5002 require one.
    token = parse_set_complete_response(RELEASED_BODY, action="act_8")
    assert token.code == "200"
    assert token.key == ""
    assert token.params["chk_enter_cnt"] == "0"
    # The reply names a queue node, and we ignore it rather than following it.
    assert token.params["ip"] == "rnf13.letskorail.com"
    # Empty-valued parameters survive as empty rather than being dropped.
    assert token.params["vwr_html"] == ""


def test_the_same_empty_key_would_be_refused_from_chk_enter():
    # The asymmetry is deliberate: a pass is identified BY its key, so 5101 and
    # 5002 must carry one; a release has nothing left to identify.
    with pytest.raises(KorailNetFunnelError, match="non-empty key"):
        parse_queue_response(RELEASED_BODY, action="act_8")


def test_release_refuses_a_keyless_token_that_is_not_a_bypass():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        calls.append(request)
        return httpx.Response(200, text=RELEASED_BODY)

    with pytest.raises(KorailNetFunnelError, match="carries no key"):
        _client(handler).release(
            KorailNetFunnelToken(action="act_8", key="", code="200")
        )
    assert calls == []


def test_a_bypass_still_skips_the_5002_and_the_5004():
    # 300 issues no key because there is no line, so there is nothing to
    # exchange and nothing to release.
    seen: list[tuple[str, str, str]] = []
    client = _client(_sequence_handler({"5101": "300:"}, seen))

    with client.slot(KorailNetFunnelAction.INQUIRY) as token:
        assert token.key == ""
    assert [opcode for opcode, _host, _key in seen] == ["5101"]


def test_a_bypass_token_has_no_node_and_still_short_circuits():
    # A bypass has no session, so it has no node either — nothing named one and
    # nothing needs one. The keyless short-circuit in release fires before
    # routing is ever consulted, so the missing node cannot become a request to
    # the wrong host or a crash on an empty origin.
    seen: list[tuple[str, str, str]] = []
    client = _client(_sequence_handler({"5101": "300:"}, seen))

    token = client.acquire(KorailNetFunnelAction.INQUIRY)
    assert token.code == "300"
    assert token.key == ""
    assert token.node == ""

    client.release(token)
    assert [opcode for opcode, _host, _key in seen] == ["5101"]


def test_a_bypass_that_names_a_node_anyway_is_still_released_by_short_circuit():
    # Defence in depth: even if a 300 did name a node, there is no key to
    # release, so the short-circuit still wins and no request is built.
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": f"300:ip={NODE_HOST}&port=443"},
            seen,
        )
    )

    token = client.acquire(KorailNetFunnelAction.INQUIRY)
    assert token.key == ""
    assert token.node == f"https://{NODE_HOST}"

    client.release(token)
    assert [opcode for opcode, _host, _key in seen] == ["5101"]


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


# THE PIN MOVED HERE ON 2026-07-26. Each of the four tests below used to assert
# the sequence `["5101", "5004"]` and used a handler that answered "5101, or
# else the release". Both encoded the defect the live probe exposed: 5101 alone
# is a ticket, not a completable session, so the real sequence is
# `["5101", "5002", "5004"]` and the released key is the one chkEnter issued.
# What each test is actually *about* — that the slot is released on both paths,
# and how loudly a failed release may complain — is unchanged.


def test_slot_releases_after_a_successful_body():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": RELEASED_BODY},
            seen,
        )
    )

    with client.slot(KorailNetFunnelAction.PAY) as token:
        assert token.key == SESSION_KEY
    assert [opcode for opcode, _host, _key in seen] == [
        "5101",
        "5002",
        "5004",
    ]


def test_slot_releases_after_the_body_raises_and_keeps_the_original_error():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": RELEASED_BODY},
            seen,
        )
    )

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom):
        with client.slot(KorailNetFunnelAction.RESERVE):
            raise Boom("the gated operation failed")
    # The app releases from onPostExecute (BaseDaoHelper.java:105-107), which
    # runs whether or not the gated call raised. So do we.
    assert [opcode for opcode, _host, _key in seen] == [
        "5101",
        "5002",
        "5004",
    ]
    assert seen[-1] == ("5004", NODE_HOST, SESSION_KEY)


def test_a_failed_release_on_the_failure_path_is_noted_not_substituted():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": "507:"},
            seen,
        )
    )

    class Boom(RuntimeError):
        pass

    with pytest.raises(Boom) as caught:
        with client.slot(KorailNetFunnelAction.RESERVE):
            raise Boom("the gated operation failed")
    # The caller's error survives, and the leak is recorded rather than hidden.
    notes = getattr(caught.value, "__notes__", [])
    assert any("slot release also failed" in note for note in notes)


def test_a_failed_release_on_the_success_path_is_raised():
    seen: list[tuple[str, str, str]] = []
    client = _client(
        _sequence_handler(
            {"5101": TICKET_BODY, "5002": SESSION_BODY, "5004": "507:"},
            seen,
        )
    )

    with pytest.raises(KorailNetFunnelError, match="did not release"):
        with client.slot(KorailNetFunnelAction.RESERVE):
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
# THIS PIN MOVED ON 2026-07-26 AND NARROWED. It used to require every document
# to call the whole subsystem BUILT and UNPROVEN, which was right while nothing
# had ever been on the wire. A live probe has since confirmed the wire format
# and the entry sequence, so that blanket claim would now understate what is
# known — while the 201 queued path genuinely is still fixture-only, because the
# server was not queueing. The docs must therefore say BOTH things, and the two
# assertions below hold them apart: the phrase "NOT live-exercised" survives but
# must now be attached to the queued path, and the confirmation date must be
# recorded so the docs cannot drift back to either extreme.
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_docs_scope_the_unproven_claim_to_the_queued_path():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    for document in (readme, progress, changelog):
        # The live confirmation is dated, and the queued path is still named as
        # the part that is not covered by it.
        assert "2026-07-26" in document
        assert "201" in document
        head, _, tail = document.partition("NOT live-exercised")
        assert tail, "the unproven claim must still be made somewhere"
        # ...and it must be about the queue, not about the subsystem.
        assert "queued path" in head[-200:] or "queued path" in tail[:200]


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


def test_docs_record_the_now_confirmed_response_shape():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    for document in (readme, progress):
        assert "<code>:<params>" in document
        assert "NetFunnel.gRtype" in document


def test_docs_record_the_entry_sequence_and_the_ticket_trap():
    # The correction a reader most needs: 5101 alone is not a session, so any
    # document that still describes acquiring and releasing as a two-step
    # handshake is describing a client that leaks every slot it takes.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for document in (readme, progress, changelog):
        assert "Wrong Server ID" in document
        assert "supersede" in document
        assert "ticket" in document


def test_docs_say_the_queue_spans_nodes_and_which_host_each_opcode_uses():
    # The correction after the ticket one, and the more expensive of the two to
    # rediscover: a document that still says every opcode goes to
    # nf.letskorail.com is describing a client that leaks about half its slots.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    for document in (readme, progress, changelog):
        # The queue legitimately spans hosts, and the front door is named as a
        # balancer rather than as the whole queue.
        assert "front door" in document
        # Every node the probe saw is quoted, so the admissibility rule can be
        # checked against its evidence without leaving the document.
        for host in OBSERVED_NODE_HOSTS:
            assert host in document
        # Which host each opcode goes to.
        assert "5101" in document and "5002" in document and "5004" in document
        # The redirect is constrained rather than trusted, and a host outside
        # the rule is refused rather than quietly sent to the front door.
        assert "rnf<1-99>.letskorail.com" in document
        assert "hard error" in document
        # ...and the reason a silent fall-back is not acceptable.
        assert "leaked" in document or "leaks" in document


def test_docs_record_the_live_diagnosis_and_the_misleading_symptom():
    # "Wrong Server ID" reads like a credential or parameter complaint and is
    # neither. Every document has to say so, and has to say when it was found,
    # because the next person to meet that message will otherwise spend an hour
    # on it — which is exactly what happened here.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    for document in (readme, progress, changelog):
        assert "2026-07-26" in document
        assert "Wrong Server ID" in document
        # The symptom, in the words that make it recognisable: it was neither
        # a clean failure nor a clean success.
        assert "half the time" in document
        assert "non-deterministic" in document
        # And the message is literal, not a misnomer to be worked around.
        assert "literal" in document
        # The transcript that proves it is quoted rather than summarised.
        assert "release via rnf13.letskorail.com" in document


def test_docs_no_longer_claim_the_redirection_is_declined():
    # The withdrawn claim. It was correct as an instinct and wrong as an
    # outcome, and it appeared in all three documents plus the divergence list.
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    progress = (ROOT / "docs/IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    for document in (readme, progress, changelog):
        assert "we do not follow" not in document.casefold()
        assert "the redirection this client\ndeclines" not in document
        assert "decline the redirection" not in document
        assert "We pin the origin instead;" not in document


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
