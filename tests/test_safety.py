# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""The mutation send boundary's field-shape contract.

The read side has had an exact per-route field contract since early on
(``assert_read_only_request_fields``). The mutation side had only
``isinstance(data, Mapping)``, so route, category, consent and card kind were
each gated and then the body itself went out unexamined. The 2026-07-27 sweep
recorded that as the remaining asymmetry between the two boundaries.
"""

import ast
import inspect
import re
import textwrap

import pytest

from korail_mobile_api import safety
from korail_mobile_api.errors import KorailProtocolError


# --------------------------------------------------------------------------
# The mutation send boundary had no field contract at all. Route, category,
# consent and card kind were each gated, and then the body went out with only
# an isinstance(data, Mapping) check behind it.
# --------------------------------------------------------------------------


def test_a_mutation_form_must_carry_the_common_three():
    with pytest.raises(KorailProtocolError, match="common fields"):
        safety.assert_mutation_form_shape(
            "/classes/com.korail.mobile.cart.addCartList",
            {"hidPnrNo": "123456789"},
        )


@pytest.mark.parametrize(
    "value",
    [
        1,  # would encode as an unpadded number
        True,  # would encode as "True"
        None,  # would encode as "None"
        {"nested": "map"},
        ["a", 1],  # a list is fine; a list with a non-string is not
    ],
)
def test_a_mutation_form_refuses_a_value_a_builder_cannot_produce(value):
    form = {
        "Device": "AOS",
        "Version": "250601003",
        "Key": "synthetic",
        "hidPnrNo": value,
    }

    with pytest.raises(KorailProtocolError, match="hidPnrNo"):
        safety.assert_mutation_form_shape(
            "/classes/com.korail.mobile.cart.addCartList", form
        )


def test_a_mutation_form_accepts_repeated_keys_as_a_list_of_strings():
    """운임 재계산 sends six parallel @Field List<String> parameters.

    The contract is a SHAPE, not an exact field set, precisely so that this
    keeps working without re-deriving the row grammar at the send boundary.
    """
    safety.assert_mutation_form_shape(
        "/classes/com.korail.mobile.certification.PriceReCalculation",
        {
            "Device": "AOS",
            "Version": "250601003",
            "Key": "synthetic",
            "dcnt_knd_cd1": ["000", "000"],
            "psg_tp_dv_cd1": ["1", "1"],
        },
    )


def test_every_registered_mutation_route_is_reachable_by_the_shape_check():
    """The check is keyed off nothing route-specific, so it covers all nine.

    Stated as a test rather than as a comment because the read side's contract
    IS per-route, and someone reading both would reasonably expect this one to
    be too.
    """
    common = {"Device": "AOS", "Version": "250601003", "Key": "synthetic"}
    for _, path in safety.KORAIL_MUTATION_ROUTES:
        safety.assert_mutation_form_shape(path, common)
        with pytest.raises(KorailProtocolError):
            safety.assert_mutation_form_shape(path, {**common, "x": 1})


def _called_names(function) -> set[str]:
    """The names a function calls, read from its syntax tree.

    A comment is not in the tree, so a call that has been commented out is not
    counted -- which is exactly what a text search of the source got wrong.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.add(node.func.attr)
    return called


def test_every_mutation_send_path_runs_the_shape_check(monkeypatch):
    """Both send paths, asserted by running them rather than by reading them.

    The gate went onto `post_mutation_form` first, and `get_mutation_query`
    -- the GET half, which exists because 6.5.0 declared
    `reservation.dcntCrdExtn.do` @GET -- kept sending unexamined values while
    its own docstring said "every gate of post_mutation_form applies here
    unchanged". Tracing a suite run is what surfaced it.

    This used to assert that each method's source contained the text
    ``assert_mutation_form_shape(``, and a comment satisfies that: with the
    call commented out the suite stayed green. Now each path is driven to the
    transport with the check wrapped in a spy, and the transport refuses to
    answer unless the spy has already seen that form. A path that stops calling
    the check, or calls it after sending, fails here. A new send path -- any
    method that calls ``assert_mutation_route`` -- fails the first assertion
    until it is driven here too.

    7.0.6 declares `dcntCrdExtn.do` @POST, so no registered mutation route is a
    GET and `get_mutation_query` refuses every real path at the route check.
    It is still a send path; the test registers a GET route for its own
    duration to reach the shape check behind that refusal.
    """
    import httpx

    from korail_mobile_api import http as http_module
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.consent import MutationConsent

    senders = {
        name
        for name, member in vars(http_module.KorailHttpClient).items()
        if inspect.isfunction(member)
        and "assert_mutation_route" in _called_names(member)
    }
    assert senders == {"post_mutation_form", "get_mutation_query"}

    seen: list[tuple[str, dict]] = []
    shape_check = safety.assert_mutation_form_shape

    def spy(path, values):
        seen.append((path, dict(values)))
        shape_check(path, values)

    monkeypatch.setattr(http_module, "assert_mutation_form_shape", spy)

    def answer(request: httpx.Request) -> httpx.Response:
        assert seen and seen[-1][0] == request.url.path, (
            f"{request.url.path} was sent before its shape check ran"
        )
        return httpx.Response(
            200,
            json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": ""},
        )

    client = http_module.KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(answer),
    )
    cart = "/classes/com.korail.mobile.cart.addCartList"
    extension = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"
    form = {**client.common_fields(), "hidPnrNo": "SYNTHETIC_PNR"}
    query = {**client.common_fields(), "txtCrdNo": "SYNTHETIC_CARD"}
    try:
        client.post_mutation_form(
            cart,
            form,
            consent=MutationConsent(allow_cart=True, dry_run=False),
            category="cart",
        )
        monkeypatch.setattr(
            safety,
            "KORAIL_MUTATION_ROUTES",
            safety.KORAIL_MUTATION_ROUTES | {("GET", extension)},
        )
        client.get_mutation_query(
            extension,
            query,
            consent=MutationConsent(allow_discount_card=True, dry_run=False),
            category="discount_card",
        )
    finally:
        client.close()

    assert seen == [(cart, form), (extension, query)]


@pytest.mark.parametrize(
    ("guard", "routes", "refusal"),
    [
        (
            safety.assert_read_only_route,
            safety.KORAIL_READ_ONLY_ROUTES,
            "KORAIL request route is not allowed",
        ),
        (
            safety.assert_mutation_route,
            safety.KORAIL_MUTATION_ROUTES,
            "KORAIL mutation route is not allowed",
        ),
    ],
    ids=["read", "mutation"],
)
def test_both_route_guards_refuse_the_same_things_the_same_way(
    guard, routes, refusal
):
    """What the two route guards do today, pinned before anyone merges them.

    They differ only in which table they consult and in one word of the
    refusal. The src plan's batch 40 extracts that shared skeleton, so what
    the skeleton does is fixed here first: a registered route passes whatever
    the case of its method, a path carrying a scheme, host, query or fragment
    is refused before any table is consulted, and an unregistered route is
    refused with the guard's own message.
    """
    method, path = sorted(routes)[0]
    guard(method.lower(), path)
    for target in (
        f"https://smart.letskorail.com{path}",
        f"//smart.letskorail.com{path}",
        f"{path}?Key=x",
        f"{path}#x",
    ):
        with pytest.raises(
            KorailProtocolError,
            match="KORAIL request target is not a registered relative path",
        ):
            guard(method, target)
    with pytest.raises(KorailProtocolError, match=re.escape(f"{refusal}: {method} /x")):
        guard(method, "/x")


def test_each_route_guard_refuses_every_route_of_the_other_table():
    """A read route is not a mutation route, and the other way round.

    The two guards share one skeleton and differ in the table they pass it.
    Handing the mutation guard the read table as well would let the mutation
    transport send to any read endpoint, and nothing else in the suite would
    notice: the other guard tests only try an unregistered "/x".
    """
    assert not safety.KORAIL_READ_ONLY_ROUTES & safety.KORAIL_MUTATION_ROUTES
    for method, path in sorted(safety.KORAIL_READ_ONLY_ROUTES):
        with pytest.raises(KorailProtocolError, match="KORAIL mutation route is not allowed"):
            safety.assert_mutation_route(method, path)
    for method, path in sorted(safety.KORAIL_MUTATION_ROUTES):
        with pytest.raises(KorailProtocolError, match="KORAIL request route is not allowed"):
            safety.assert_read_only_route(method, path)


def test_both_route_guards_call_the_same_things():
    """If the shared skeleton is extracted, it is extracted from both.

    The reachability scan below passes as soon as ONE guard calls a new
    helper, so an extraction done on only one side -- the other keeping its
    inline copy -- would pass everything else. This compares what the two
    guards call, without naming a helper that does not exist yet.
    """
    assert _called_names(safety.assert_read_only_route) == _called_names(
        safety.assert_mutation_route
    )


def test_the_get_mutation_route_carries_the_common_three_the_check_requires():
    """The GET mutation is gated by the same rule, so it must satisfy it.

    A contract that the one @GET route could not meet would be a contract
    that gets loosened the first time it fires. It is built by _common_fields
    exactly like a POST body, so it meets it.
    """
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.mutation_models import DiscountCardTicket
    from korail_mobile_api.mutation_payloads import (
        build_discount_card_extension_query,
    )

    query = build_discount_card_extension_query(
        KorailConfig(),
        DiscountCardTicket(
            sale_date="20260727",
            sale_window_no="0001",
            sale_sequence="0001",
            return_password="0000",
        ),
    )

    safety.assert_mutation_form_shape(
        "/classes/com.korail.mobile.reservation.dcntCrdExtn.do", query
    )


def test_no_module_level_definition_is_unreachable():
    """AST reachability over src/, so removal residue fails instead of lingering.

    The 2026-07-27 sweep found fifteen orphaned module-level names in one day:
    seven _TRIP_CHANGE_* constants, four _OFFLINE_REFUND_*_FIELDS dicts, two
    helpers and two field tuples, all left behind when the features that read
    them were deleted. Grepping the deletion diff cannot find these -- that
    finds CALLERS of what was removed, and these are the opposite direction:
    definitions that were only ever read from inside the removed block.

    Anything genuinely meant to be unused belongs in the allowlist below with
    a reason, so "unused" stays a decision rather than an accident.

    A use is a reference in the syntax tree: a name loaded, an attribute
    accessed, a name imported. This used to count every whole-word occurrence
    in the text, comments and strings included, so one comment naming a dead
    constant was enough to keep it alive.
    """
    from pathlib import Path

    #: Public API is exported, not called; dunders are protocol.
    allowed_prefixes = ("__",)
    #: Deliberately unreferenced, each for a stated reason. The point of the
    #: allowlist is that "unused" has to be argued for once, here, rather than
    #: being indistinguishable from residue.
    deliberately_unused = {
        # Documentation-by-constant: declared beside APP_UPDATE_REQUIRED_CODE
        # (which IS used) so the pair reads together, and its own docstring
        # says why it is not in the error map -- KorailSessionExpiredError
        # handles P058 before that map is consulted.
        "SESSION_EXPIRED_CODE",
        # The policy table the safety model is written against. Prose that
        # happens to be a dict; deleting it would delete the statement of
        # intent, not dead code.
        "SAFETY_DEFAULTS",
        # The precomputed table for the default index. Kept as the named,
        # inspectable value behind build_dynapath_prefix's default rather than
        # recomputed at each call site.
        "DYNAPATH_ENCODING_TABLE",
        # The signing certificate's SHA-256, recorded beside the app-signature
        # hash the token actually carries. Nothing reads it: the token is built
        # from the hash, and this is the artefact the hash was derived FROM,
        # kept so a reader can re-derive it instead of trusting the hash. It
        # became visible to this scan only when the public surface narrowed --
        # `__all__` had been standing in as its reason for existing, which was
        # never the real one.
        "KORAIL_DYNAPATH_SIGNING_CERT_SHA256",
    }
    package = Path(__file__).parents[1] / "src" / "korail_mobile_api"
    sources = {path: path.read_text(encoding="utf-8") for path in package.glob("*.py")}
    referenced: set[str] = set()
    for text in (
        *sources.values(),
        *(
            path.read_text(encoding="utf-8")
            for path in (Path(__file__).parent).glob("*.py")
        ),
    ):
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                referenced.add(node.id)
            elif isinstance(node, ast.Attribute):
                referenced.add(node.attr)
            elif isinstance(node, ast.alias):
                referenced.add(node.name.rsplit(".", 1)[-1])

    import korail_mobile_api

    exported = set(korail_mobile_api.__all__)
    orphans = []
    for path, text in sources.items():
        if path.name == "__init__.py":
            continue
        for node in ast.parse(text).body:
            names = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = [node.name]
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            for name in names:
                if (
                    name.startswith(allowed_prefixes)
                    or name in exported
                    or name in deliberately_unused
                ):
                    continue
                # A definition stores its name; only a load, an attribute
                # access or an import refers to it.
                if name not in referenced:
                    orphans.append(f"{path.name}:{node.lineno} {name}")

    assert not orphans, "unreachable module-level definitions:\n  " + "\n  ".join(
        sorted(orphans)
    )


# --------------------------------------------------------------------------
# The queue is a SECOND ORIGIN. It lives on a different host from every other
# route in this package, which is why it could not simply be added to
# KORAIL_READ_ONLY_ROUTES and deliberately was not. The two boundaries had
# never been tested against each other -- each was tested from the inside.
# --------------------------------------------------------------------------


def test_the_ordinary_origin_gate_refuses_the_queue_host():
    """post_form / get_json must never be able to target ts.wseq."""
    from korail_mobile_api.constants import KORAIL_NETFUNNEL_URL

    for url in (KORAIL_NETFUNNEL_URL, "https://rnf1.letskorail.com"):
        with pytest.raises(KorailProtocolError):
            safety.assert_korail_origin(url)


def test_the_read_only_allowlist_refuses_the_queue_path():
    """And the queue path is not reachable through the read-only boundary."""
    from korail_mobile_api.constants import KORAIL_NETFUNNEL_PATH

    for method in ("GET", "POST"):
        with pytest.raises(KorailProtocolError):
            safety.assert_read_only_route(method, KORAIL_NETFUNNEL_PATH)


def test_the_queue_gate_refuses_an_ordinary_route():
    """The other direction: the queue contract is not a general-purpose GET."""
    with pytest.raises(KorailProtocolError):
        safety.assert_netfunnel_request(
            "GET", "/classes/com.korail.mobile.common.code.do", {}
        )


@pytest.mark.parametrize(
    "url",
    [
        # A suffix that merely CONTAINS the allowed host.
        "https://rnf1.letskorail.com.evil.example",
        # The allowed host smuggled into a query string.
        "https://evil.example/?x=https://rnf1.letskorail.com",
        "http://rnf1.letskorail.com",  # not https
        "https://user:pw@rnf1.letskorail.com",  # userinfo
        "https://rnf1.letskorail.com:8443",  # wrong port
        "https://rnf0.letskorail.com",  # outside the observed pool
        "https://rnf1.letskorail.com/path",  # a path
        "https://rnf1.letskorail.com#frag",  # a fragment
    ],
)
def test_a_queue_node_lookalike_is_refused(url):
    with pytest.raises(KorailProtocolError):
        safety.assert_korail_netfunnel_node_origin(url)


def test_a_queue_hostname_is_matched_case_insensitively():
    """Not a hole: DNS is case-insensitive and the gate casefolds on purpose.

    Pinned so that a future "tighten the host check" edit does not turn a
    correct behaviour into a refusal of the app's own traffic.
    """
    safety.assert_korail_netfunnel_node_origin("https://RNF1.LETSKORAIL.COM")


def test_a_caller_supplied_queue_url_is_gated_before_any_request():
    """The config field is caller-writable, so it is checked, not trusted.

    ``netfunnel_enabled=True`` is set because the disabled-by-default refusal
    fires FIRST and would otherwise be what this test observed. That ordering
    is defence in depth and is pinned separately below; here the point is that
    a caller who legitimately enables the queue still cannot redirect it.
    """
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.netfunnel import KorailNetFunnelClient

    for hostile in ("https://evil.example", "http://nf.letskorail.com"):
        with pytest.raises(KorailProtocolError):
            KorailNetFunnelClient(
                KorailConfig(netfunnel_url=hostile, netfunnel_enabled=True)
            )


def test_the_queue_is_refused_before_its_origin_is_even_considered():
    """Disabled by default, and that refusal precedes the origin check.

    Two independent reasons a hostile queue URL goes nowhere, in the order
    they fire. Worth pinning because the outer one silently makes the inner
    one unreachable in tests -- which is exactly how it was noticed.
    """
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.errors import KorailNetFunnelError
    from korail_mobile_api.netfunnel import KorailNetFunnelClient

    with pytest.raises(KorailNetFunnelError, match="disabled by default"):
        KorailNetFunnelClient(KorailConfig(netfunnel_url="https://evil.example"))
