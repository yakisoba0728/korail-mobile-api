"""Offline refund quote binding: local identity checks, not signatures or expiry guarantees."""

from __future__ import annotations

import sys
from copy import deepcopy
from dataclasses import replace
from inspect import Parameter, signature
from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import (
    KorailConfig,
    KorailProtocolError,
    KorailTransportError,
    OriginalTicketReference,
    PaidTicket,
    RefundCommissionResponse,
    RefundCompanion,
    RefundTicketDetailResponse,
    TicketResource,
)
from korail_mobile_api.read_parsers import parse_refund_commission_response


def _reference():
    return OriginalTicketReference("SYNTH-WINDOW-A", "1017", "SYNTH-SEQUENCE-A", "SYNTH-PASSWORD-A")


def _ticket(**changes):
    values = {
        "pnr_no": "SYNTH-PNR-A",
        "sale_date": "20991019",
        "sale_window_no": "SYNTH-WINDOW-A",
        "sale_sequence": "SYNTH-SEQUENCE-A",
        "return_password": "SYNTH-PASSWORD-A",
        "return_sale_date": "1017",
        "companion_name": "",
        "companion_certificate_no": "",
        "train_no": "90001",
    }
    values.update(changes)
    return PaidTicket(**values)


def _fee_raw():
    return {
        "strResult": "SUCC",
        "h_msg_cd": "IRZ000001",
        "h_msg_txt": "synthetic quote",
        "ret_amt": "19600",
        "ret_fee": "400",
        "use_psb_mlg_num": "500",
        "tk_ret_tms_dv_cd": "SYNTH-TIMES",
        "extra": {"server_only": ["preserve", 7]},
    }


def _refund_raw():
    return {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "stlList": [{"stl_mns_cd": "02"}]}


@pytest.fixture
def binding_client(scripted_client_factory, f8_logged_in_session):
    """A strict two-route transport: every extra lookup or mutation is observable."""
    recorded = []
    config = KorailConfig(
        base_url="https://api.example.invalid",
        key="SYNTH-KEY",
        netfunnel_enabled=False,
        disable_dynapath=True,
    )

    def make(*, fee_raw=None, refund_reply=None):
        fee = _fee_raw() if fee_raw is None else fee_raw
        reply = _refund_raw() if refund_reply is None else refund_reply
        client, requests, _ = scripted_client_factory([fee, reply], config=config, session=f8_logged_in_session)
        client.http.cookies.set("JSESSIONID", f8_logged_in_session.jsessionid)
        recorded.append(requests)
        return client, requests

    yield make
    paths = [
        "/classes/com.korail.mobile.refunds.CommissionView",
        "/classes/com.korail.mobile.refunds.RefundsRequest",
    ]
    for requests in recorded:
        assert all(request.method == "POST" for request in requests)
        assert [request.url.path for request in requests] == paths[: len(requests)]


def _form(request):
    return parse_qs(request.content.decode(), keep_blank_values=True)


def _assert_private_error(error, *extra):
    for value in (
        "SYNTH-PNR-A",
        "SYNTH-PNR-B",
        "SYNTH-WINDOW-A",
        "SYNTH-SEQUENCE-A",
        "SYNTH-PASSWORD-A",
        "SYNTH-COMPANION-A",
        "20991231",
        "1017",
        *extra,
    ):
        assert value not in str(error)


def test_matching_lookup_and_refund_make_exactly_two_http_requests(binding_client):
    raw = _fee_raw()
    unchanged = deepcopy(raw)
    client, requests = binding_client(fee_raw=raw)

    commission = client.get_refund_commission(_reference())
    assert commission.raw == unchanged
    assert commission.refund_fee == "400"
    assert commission.refund_amount == "19600"
    result = client.refund(_ticket(), commission=commission)

    assert result.str_result == "SUCC"
    assert result.settlement_method_codes == ("02",)
    assert len(requests) == 2
    assert requests[0].url.path.endswith("refunds.CommissionView")
    assert requests[1].url.path.endswith("refunds.RefundsRequest")
    assert _form(requests[0])["h_orgtk_ret_sale_dt"] == ["1017"]
    assert _form(requests[1])["h_orgtk_sale_dt"] == ["20991019"]
    assert _form(requests[1])["tk_ret_tms_dv_cd"] == ["SYNTH-TIMES"]
    assert raw == unchanged
    assert commission.raw == unchanged


@pytest.mark.parametrize("limit", [640, 0], ids=["minimum-limit", "disabled-limit"])
def test_oversized_mileage_is_zero_and_cannot_cover_the_fee(binding_client, limit):
    raw = {**_fee_raw(), "use_psb_mlg_num": "9" * 4301}
    client, requests = binding_client(fee_raw=raw)
    commission = client.get_refund_commission(_reference())
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(limit)
        with pytest.raises(KorailProtocolError, match="mileage is below the fee"):
            client.refund(_ticket(), commission=commission, settle_mileage=True)
        assert sys.get_int_max_str_digits() == limit
    finally:
        sys.set_int_max_str_digits(previous)
    assert len(requests) == 1
    assert commission.raw == raw


@pytest.mark.parametrize(
    "usable,fee,allowed",
    [
        pytest.param("0" * 4301 + "400", "400", True, id="padded-mileage-equal"),
        pytest.param("+" + "0" * 4301 + "399", "400", False, id="padded-positive-mileage-below"),
        pytest.param("-" + "0" * 4301 + "1", "0", False, id="padded-negative-mileage"),
        pytest.param("400", "+" + "0" * 4301 + "400", True, id="padded-fee-equal"),
        pytest.param("399", "0" * 4301 + "400", False, id="padded-fee-above"),
        pytest.param("0" * 4301, "1", False, id="all-zero-mileage"),
        pytest.param("-" + "0" * 4301, "0", True, id="padded-negative-zero"),
        pytest.param("2147483647", "1", True, id="int32-max-mileage"),
        pytest.param("2147483646", "2147483647", False, id="int32-max-fee"),
        pytest.param("2147483648", "1", False, id="positive-overflow-mileage"),
        pytest.param("0", "2147483648", True, id="positive-overflow-fee-is-zero"),
        pytest.param("-2147483648", "-1", False, id="int32-min-mileage"),
        pytest.param("-2147483647", "-2147483648", True, id="int32-min-fee"),
        pytest.param("-2147483649", "-1", True, id="negative-overflow-mileage-is-zero"),
        pytest.param("-1", "-2147483649", False, id="negative-overflow-fee-is-zero"),
        pytest.param("0", "9" * 4301, True, id="oversized-fee-is-zero"),
        pytest.param("-1", "-" + "9" * 4301, False, id="oversized-negative-fee-is-zero"),
        pytest.param(None, "1", False, id="null-mileage-is-zero"),
        pytest.param("0", None, True, id="null-fee-is-zero"),
        *[
            pytest.param(value, "1", False, id=name)
            for name, value in (
                ("empty", ""),
                ("leading-space", " +400"),
                ("trailing-space", "400 "),
                ("unicode-digits", "４００"),
                ("positive-sign-only", "+"),
                ("negative-sign-only", "-"),
                ("repeated-sign", "++400"),
                ("mixed-signs", "+-400"),
            )
        ],
    ],
)
def test_refund_mileage_comparison_follows_app_int32_rules(binding_client, usable, fee, allowed):
    """Keep the SDK's ASCII gate and TextHelper.java:169-181 int32/zero fallback rules."""
    raw = {**_fee_raw(), "use_psb_mlg_num": usable, "ret_fee": fee}
    client, requests = binding_client(fee_raw=raw)
    commission = client.get_refund_commission(_reference())
    if allowed:
        assert client.refund(_ticket(), commission=commission, settle_mileage=True).str_result == "SUCC"
        assert len(requests) == 2
        assert _form(requests[1])["h_mlg_stl"] == ["Y"]
    else:
        with pytest.raises(KorailProtocolError, match="mileage is below the fee"):
            client.refund(_ticket(), commission=commission, settle_mileage=True)
        assert len(requests) == 1
    assert commission.usable_mileage == usable
    assert commission.refund_fee == fee
    assert commission.raw == raw


@pytest.mark.parametrize(
    "changes",
    [
        pytest.param({"sale_sequence": "SYNTH-SEQUENCE-B"}, id="same-pnr-other-sequence"),
        pytest.param({"sale_window_no": "SYNTH-WINDOW-B"}, id="same-pnr-other-window"),
        pytest.param({"return_password": "SYNTH-PASSWORD-B"}, id="same-pnr-other-password"),
        pytest.param({"return_sale_date": "1018"}, id="same-pnr-other-original-date"),
        pytest.param({"companion_name": "SYNTH-COMPANION-B"}, id="same-pnr-other-companion-name"),
        pytest.param({"companion_certificate_no": "20991230"}, id="same-pnr-other-companion-certificate"),
        pytest.param(
            {
                "pnr_no": "SYNTH-PNR-B",
                "sale_window_no": "SYNTH-WINDOW-B",
                "sale_sequence": "SYNTH-SEQUENCE-B",
                "return_password": "SYNTH-PASSWORD-B",
                "return_sale_date": "1018",
            },
            id="different-ticket",
        ),
    ],
)
def test_quote_for_a_cannot_refund_mismatching_ticket(binding_client, changes):
    raw = _fee_raw()
    unchanged = deepcopy(raw)
    client, requests = binding_client(fee_raw=raw)
    companion = RefundCompanion("SYNTH-COMPANION-A", "20991231")
    commission = client.get_refund_commission(_reference(), companion=companion)
    ticket = _ticket(companion_name=companion.name, companion_certificate_no=companion.certificate_no)
    changed = replace(ticket, **changes)

    with pytest.raises(KorailProtocolError) as caught:
        client.refund(changed, commission=commission)

    assert len(requests) == 1  # No refresh, detail lookup or refund after the quote.
    assert caught.value.raw == unchanged
    assert commission.raw == unchanged
    assert raw == unchanged
    _assert_private_error(caught.value, *changes.values())


@pytest.mark.parametrize(
    "ticket_changes,commission_changes",
    [
        *[({"return_sale_date": value}, {}) for value in (None, "", "   ")],
        *[({}, {"str_result": value}) for value in ("FAIL", "UNKNOWN", "", None)],
    ],
    ids=[
        "missing-original-date",
        "empty-original-date",
        "blank-original-date",
        "FAIL",
        "UNKNOWN",
        "empty-result",
        "null-result",
    ],
)
def test_bound_lookup_still_requires_original_date_and_success(
    binding_client, ticket_changes, commission_changes
):
    client, requests = binding_client()
    commission = client.get_refund_commission(_reference())
    # Change public result data only; never manufacture or access private context.
    supplied = replace(commission, **commission_changes)

    with pytest.raises(KorailProtocolError) as caught:
        client.refund(_ticket(**ticket_changes), commission=supplied)

    assert len(requests) == 1
    assert caught.value.raw == commission.raw
    _assert_private_error(caught.value)


@pytest.mark.parametrize("source", ["constructor", "base-parser", "fee-parser", "empty-constructor"])
def test_direct_responses_cannot_forge_binding_from_server_raw(binding_client, source):
    raw = _fee_raw()
    raw.update(
        {
            "context": {
                "sale_window_no": "SYNTH-WINDOW-A",
                "return_sale_date": "1017",
                "sale_sequence": "SYNTH-SEQUENCE-A",
                "return_password": "SYNTH-PASSWORD-A",
                "companion_name": "",
                "companion_certificate_no": "",
            },
            "_refund_context": {"bound": True},
        }
    )
    if source == "empty-constructor":
        raw = {}
    unchanged = deepcopy(raw)
    client, requests = binding_client()
    if source == "empty-constructor":
        commission = RefundCommissionResponse(str_result="SUCC")
    elif source == "constructor":
        commission = RefundCommissionResponse(str_result="SUCC", raw=raw)
    elif source == "base-parser":
        commission = RefundCommissionResponse.from_raw(raw)
    else:
        commission = parse_refund_commission_response(raw)

    with pytest.raises(KorailProtocolError) as caught:
        client.refund(_ticket(), commission=commission)

    assert requests == []
    assert caught.value.raw == unchanged
    assert commission.raw == unchanged
    assert raw == unchanged
    _assert_private_error(caught.value)


@pytest.mark.parametrize("original_date", ["1017", None], ids=["original-date", "missing-original-date"])
def test_from_detail_preserves_current_sale_date_and_maps_original_and_companion(binding_client, original_date):
    companion = RefundCompanion("SYNTH-COMPANION-A", "20991231")
    detail = RefundTicketDetailResponse(
        str_result="SUCC",
        pnr_no="SYNTH-PNR-A",
        sale_date="20991019",
        original_sale_date=original_date,
        original_window_no="SYNTH-WINDOW-A",
        original_sale_sequence="SYNTH-SEQUENCE-A",
        original_return_password="SYNTH-PASSWORD-A",
        companion_name=companion.name,
        companion_birth_date=companion.certificate_no,
    )
    client, requests = binding_client()
    commission = client.get_refund_commission(_reference(), companion=companion)
    if original_date is None:
        with pytest.raises(KorailProtocolError):
            ticket = PaidTicket.from_refund_detail(detail)
            client.refund(ticket, commission=commission)
        assert len(requests) == 1
        return

    ticket = PaidTicket.from_refund_detail(detail)
    assert ticket.sale_date == "20991019"
    assert ticket.return_sale_date == "1017"
    assert ticket.companion_name == companion.name
    assert ticket.companion_certificate_no == companion.certificate_no

    assert client.refund(ticket, commission=commission).str_result == "SUCC"
    assert len(requests) == 2
    assert _form(requests[0])["h_comp_nm"] == [companion.name]
    assert _form(requests[0])["h_comp_cert_no"] == [companion.certificate_no]
    assert _form(requests[1])["h_orgtk_sale_dt"] == ["20991019"]


def test_new_ticket_identity_fields_are_keyword_only_and_hidden_from_repr(binding_client):
    parameters = signature(PaidTicket).parameters
    for name, default in (
        ("return_sale_date", None),
        ("companion_name", ""),
        ("companion_certificate_no", ""),
    ):
        assert parameters[name].kind is Parameter.KEYWORD_ONLY
        assert parameters[name].default == default

    ticket = _ticket(companion_name="SYNTH-COMPANION-A", companion_certificate_no="20991231")
    for secret in ("1017", "SYNTH-COMPANION-A", "20991231"):
        assert secret not in repr(ticket)

    client, requests = binding_client()
    commission = client.get_refund_commission(
        _reference(), companion=RefundCompanion(ticket.companion_name, ticket.companion_certificate_no)
    )
    # Quote raw has no request identity. Attaching local context must not expose it via repr.
    for secret in ("SYNTH-WINDOW-A", "1017", "SYNTH-SEQUENCE-A", "SYNTH-PASSWORD-A", "20991231"):
        assert secret not in repr(commission)
    assert "SYNTH-COMPANION-A" not in repr(commission)
    assert len(requests) == 1


@pytest.mark.parametrize("failure", ["transport", "parser"])
def test_refund_failure_after_quote_is_never_retried(binding_client, failure):
    if failure == "transport":
        reply = httpx.ReadTimeout("synthetic uncertain refund outcome")
        expected_error = KorailTransportError
    else:
        reply = {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "stlList": [{"stl_mns_cd": []}]}
        expected_error = KorailProtocolError
    client, requests = binding_client(refund_reply=reply)
    commission = client.get_refund_commission(_reference())
    unchanged = deepcopy(commission.raw)

    with pytest.raises(expected_error) as caught:
        client.refund(_ticket(), commission=commission)

    assert len(requests) == 2
    assert sum(request.url.path.endswith("refunds.RefundsRequest") for request in requests) == 1
    assert commission.raw == unchanged
    if failure == "parser":
        assert caught.value.raw == reply


@pytest.mark.parametrize("mismatch", [False, True], ids=["matching", "mismatching"])
def test_ticket_facade_forwards_companion_and_preserves_binding_checks(binding_client, mismatch):
    client, requests = binding_client()
    tickets = TicketResource(client)
    companion = RefundCompanion("SYNTH-COMPANION-A", "20991231")
    commission = tickets.refund_fee(_reference(), companion=companion)
    ticket = _ticket(companion_name=companion.name, companion_certificate_no=companion.certificate_no)

    if mismatch:
        with pytest.raises(KorailProtocolError) as caught:
            tickets.refund(replace(ticket, sale_sequence="SYNTH-SEQUENCE-B"), commission=commission)
        assert caught.value.raw == commission.raw
        _assert_private_error(caught.value, "SYNTH-SEQUENCE-B")
        assert len(requests) == 1
    else:
        assert tickets.refund(ticket, commission=commission).str_result == "SUCC"
        assert len(requests) == 2

    assert _form(requests[0])["h_comp_nm"] == [companion.name]
    assert _form(requests[0])["h_comp_cert_no"] == [companion.certificate_no]


def test_ticket_facade_default_companion_retains_two_request_workflow(binding_client):
    client, requests = binding_client()
    tickets = TicketResource(client)
    commission = tickets.refund_fee(_reference())

    assert tickets.refund(_ticket(), commission=commission).str_result == "SUCC"
    assert len(requests) == 2
