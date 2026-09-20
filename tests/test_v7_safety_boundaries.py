# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""7.0.6 계약 경로가 상위 API의 안전 경계를 우회하지 않는지 확인한다."""

from __future__ import annotations

import json
from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig, TrainSearchQuery
from korail_mobile_api.errors import KorailMutationNotAllowedError, KorailProtocolError
from korail_mobile_api.payloads import build_train_schedule_special_form
from korail_mobile_api.v7 import V7_CONTRACTS, V7Response


def _never_send(request: httpx.Request) -> httpx.Response:
    pytest.fail(f"request must not be sent: {request.method} {request.url.path}")


@pytest.mark.parametrize("field", ["device", "version"])
def test_schedule_view_special_keeps_an_empty_device_or_version(field: str) -> None:
    # Before the fix, the empty-value filter ran ahead of the Device/Version
    # pops, so an empty config.device or config.version raised KeyError; they
    # must come back as "" instead.
    form = build_train_schedule_special_form(
        KorailConfig(**{field: ""}),
        TrainSearchQuery("0001", "0723", "20990101"),
        departure_name="서울",
        arrival_name="부산",
    )
    assert list(form)[:3] == ["Device", "Version", "Key"]
    assert form[field.capitalize()] == ""


@pytest.mark.parametrize("effect", ["write", "Mutation", "", None])
def test_the_registry_refuses_a_row_whose_effect_is_neither_read_nor_mutation(
    monkeypatch: pytest.MonkeyPatch, effect: object
) -> None:
    # call() gates on `effect == "mutation"` and treats everything else as a
    # read, so a misspelled effect in the generated rows would send a mutation
    # with no consent. The loader refuses it instead.
    from korail_mobile_api import v7

    rows = list(v7.CONTRACT_ROWS)
    rows[0] = {**rows[0], "effect": effect}
    monkeypatch.setattr(v7, "CONTRACT_ROWS", tuple(rows))
    with pytest.raises(KorailProtocolError, match="effect"):
        v7._load_registry()


def test_every_loaded_contract_is_a_read_or_a_mutation() -> None:
    assert {contract.effect for contract in V7_CONTRACTS.values()} == {"read", "mutation"}


# --------------------------------------------------------------------------
# Every contract, one at a time. The registry and the gateway share one source,
# so a round trip alone cannot notice a row that was edited wrongly: the row
# and the request would agree. The structural test holds each row to
# Retrofit's own rules instead, which do not come from that source.
# --------------------------------------------------------------------------

# The 정기권/패스 purchases the gateway refuses by name; they are pinned by the
# refusal tests at the end of this file, not sent here.
_PASS_PURCHASES = (
    "NetworkApi.postPassReserve",
    "NetworkApi.postPassPayIssue",
    "NetworkApi.passOtrReserve",
    "NetworkApi.postPassOtrPayIssue",
)
_CONTRACT_NAMES = sorted(V7_CONTRACTS)
_SENT_CONTRACT_NAMES = sorted(set(V7_CONTRACTS) - set(_PASS_PURCHASES))
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH"})


def _bare_params(params: str) -> set[str]:
    return {
        token.strip()
        for token in params.split(",")
        if token.strip() and "(" not in token
    }


@pytest.mark.parametrize("name", _CONTRACT_NAMES)
def test_every_contract_obeys_retrofits_own_rules(name: str) -> None:
    """@Field, @FieldMap and @Body need a request body; a GET has none.

    Retrofit refuses @Field without @FormUrlEncoded, and @FormUrlEncoded or
    @Body on a method with no body. A row that turned a field-carrying POST
    into a GET would still round-trip -- the gateway sends what the row says
    -- but it describes a call the app cannot make.
    """
    contract = V7_CONTRACTS[name]
    bare = _bare_params(contract.params)
    carries_fields = bool(contract.fields) or "FieldMap" in bare
    carries_body = "Body" in bare
    if carries_fields or carries_body:
        assert contract.http in _BODY_METHODS
    assert contract.form == carries_fields
    assert not (carries_fields and carries_body)
    if contract.http == "GET":
        assert not contract.fields and "FieldMap" not in bare


def _wire_values(name: str) -> tuple[dict, bool]:
    """A valid set of wire values for one contract, and whether to merge common."""
    contract = V7_CONTRACTS[name]
    declared = contract.fields if contract.form else contract.queries
    values: dict = {key: f"v-{key}" for key in sorted(declared)}
    if ("FieldMap" if contract.form else "QueryMap") in _bare_params(contract.params):
        values["mapKey"] = "v-mapKey"
    return values, False


@pytest.mark.parametrize("name", _SENT_CONTRACT_NAMES)
def test_every_contract_goes_out_as_its_row_describes(name: str) -> None:
    """Method, host, path, headers and encoding, for each surviving contract it sends.

    The pass purchases are refused by name, not sent here.

    Every contract sends immediately; there is no separate mutation-consent
    step any more.
    """
    contract = V7_CONTRACTS[name]
    values, include_common = _wire_values(name)
    headers = {header: f"v-{header}" for header in sorted(contract.headers)}
    seen: list[httpx.Request] = []

    def main(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": ""}
        )

    client = KorailClient(transport=httpx.MockTransport(main))
    try:
        result = client.v7.call(
            name,
            values,
            headers=headers,
            include_common=include_common,
        )
    finally:
        client.close()

    assert isinstance(result, V7Response)
    assert len(seen) == 1
    request = seen[0]
    assert request.method == contract.http
    assert request.url.path == "/" + contract.route.lstrip("/")
    expected_host = "smart.letskorail.com"
    assert request.url.host == expected_host
    for header, value in headers.items():
        assert request.headers[header] == value
    if "Body" in _bare_params(contract.params):
        assert request.headers["content-type"] == "application/json"
        assert json.loads(request.content) == values
    elif contract.form:
        sent = parse_qsl(request.content.decode("ascii"), keep_blank_values=True)
        expected = {**(client.http.common_fields() if include_common else {}), **values}
        assert dict(sent) == expected
        assert len(sent) == len(expected)
        assert not request.url.query
    else:
        assert dict(request.url.params) == values
        assert request.content == b""


@pytest.mark.parametrize("name", _PASS_PURCHASES)
def test_the_gateway_refuses_a_pass_purchase_by_name(name: str) -> None:
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        with pytest.raises(KorailMutationNotAllowedError, match="never sends"):
            client.v7.call(name, {})
    finally:
        client.close()
