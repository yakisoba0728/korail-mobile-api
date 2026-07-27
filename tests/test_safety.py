"""The mutation send boundary's field-shape contract.

The read side has had an exact per-route field contract since early on
(``assert_read_only_request_fields``). The mutation side had only
``isinstance(data, Mapping)``, so route, category, consent and card kind were
each gated and then the body itself went out unexamined. The 2026-07-27 sweep
recorded that as the remaining asymmetry between the two boundaries.
"""

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
