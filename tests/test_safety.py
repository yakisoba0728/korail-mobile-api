"""The mutation send boundary's field-shape contract.

The read side has had an exact per-route field contract since early on
(``assert_read_only_request_fields``). The mutation side had only
``isinstance(data, Mapping)``, so route, category, consent and card kind were
each gated and then the body itself went out unexamined. The 2026-07-27 sweep
recorded that as the remaining asymmetry between the two boundaries.
"""

import re

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


def test_every_mutation_send_path_runs_the_shape_check():
    """Both send paths, asserted structurally rather than by coverage.

    The gate went onto `post_mutation_form` first, and `get_mutation_query`
    -- the GET half, which exists because `reservation.dcntCrdExtn.do` is
    declared @GET and mis-registering it as a POST was rejected -- kept
    sending unexamined values while its own docstring said "every gate of
    post_mutation_form applies here unchanged". Tracing a suite run is what
    surfaced it; this makes the next send path fail instead.
    """
    import inspect

    from korail_mobile_api.http import KorailHttpClient

    for name in ("post_mutation_form", "get_mutation_query"):
        source = inspect.getsource(getattr(KorailHttpClient, name))
        assert "assert_mutation_form_shape(" in source, name


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
    """
    import ast
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
    corpus = "\n".join(sources.values()) + "\n".join(
        path.read_text(encoding="utf-8")
        for path in (Path(__file__).parent).glob("*.py")
    )

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
                # Its own definition is one occurrence; anything else is a use.
                if len(re.findall(rf"\b{re.escape(name)}\b", corpus)) <= 1:
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
