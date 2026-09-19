# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""7.0.6 계약 경로가 상위 API의 안전 경계를 우회하지 않는지 확인한다."""

from __future__ import annotations

import json
from dataclasses import replace
from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig, TrainSearchQuery
from korail_mobile_api.errors import KorailMutationNotAllowedError, KorailProtocolError
from korail_mobile_api.payloads import build_train_schedule_special_form
from korail_mobile_api.safety import KORAIL_MUTATION_ROUTES, KORAIL_READ_ONLY_ROUTES
from korail_mobile_api.v7 import (
    V7_CONTRACTS,
    V7MutationConsent,
    V7MutationPreview,
    V7Response,
)


SPECIAL = "NetworkApi.postScheduleViewSpecial"
SPECIAL_PATH = "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"


def _never_send(request: httpx.Request) -> httpx.Response:
    pytest.fail(f"request must not be sent: {request.method} {request.url.path}")


def _special_form() -> dict[str, str]:
    return build_train_schedule_special_form(
        KorailConfig(),
        TrainSearchQuery("0001", "0723", "20990101"),
        departure_name="서울",
        arrival_name="부산",
    )


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


def test_non_member_ticket_is_a_method_scoped_mutation() -> None:
    name = "NetworkApi.postNonMemTicket"
    values = {"txtJobId": "synthetic-job", "txtCustNm": "synthetic-name"}
    assert V7_CONTRACTS[name].effect == "mutation"
    assert V7_CONTRACTS["NetworkApi.postNonMemTicketList"].effect == "read"
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        with pytest.raises(KorailMutationNotAllowedError):
            client.v7.call(name, values)
        consent = V7MutationConsent(allow_methods=frozenset({name}))
        preview = client.v7.call(name, values, consent=consent)
    finally:
        client.close()
    assert isinstance(preview, V7MutationPreview)
    assert preview.route == "/classes/com.korail.mobile.nonMember.NonMemTicket"
    assert preview.payload == {"txtJobId": "[REDACTED]", "txtCustNm": "[REDACTED]"}


def test_v7_routes_shared_with_high_level_tables_are_exactly_known() -> None:
    # A V7 contract on a safety.py route either reuses the read-only field check
    # or is refused (mutation). Any new overlap must be decided explicitly here.
    shared = KORAIL_READ_ONLY_ROUTES | KORAIL_MUTATION_ROUTES
    assert {
        contract.name for contract in V7_CONTRACTS.values()
        if (contract.http, contract.route) in shared
    } == {SPECIAL}


def test_schedule_view_special_applies_high_level_field_contract() -> None:
    form = _special_form()
    without_common = {
        key: value for key, value in form.items()
        if key not in {"Device", "Version", "Key"}
    }
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        for invalid in (
            {**form, "Sid": "legacy"},
            {**form, "chtnCnt": "1"},
            without_common,
        ):
            with pytest.raises(KorailProtocolError):
                client.v7.call(SPECIAL, invalid)
    finally:
        client.close()


def test_schedule_view_special_well_formed_call_is_sent() -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    form = _special_form()
    client = KorailClient(transport=httpx.MockTransport(respond))
    try:
        # The common fields come from the include_common merge, so the check
        # must run on the merged data for this call to pass.
        response = client.v7.call(
            SPECIAL,
            {key: value for key, value in form.items()
             if key not in {"Device", "Version", "Key"}},
            include_common=True,
        )
    finally:
        client.close()
    assert isinstance(response, V7Response)
    assert response.raw == {"strResult": "SUCC"}
    assert len(requests) == 1
    assert requests[0].url.path == SPECIAL_PATH
    pairs = parse_qsl(requests[0].content.decode())
    assert len(pairs) == len(form)
    assert dict(pairs) == form


def test_contract_on_high_level_mutation_route_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "NetworkApi.postNonMemTicket"
    monkeypatch.setitem(V7_CONTRACTS, name, replace(
        V7_CONTRACTS[name],
        route="/classes/com.korail.mobile.certification.TicketReservation",
    ))
    consent = V7MutationConsent(allow_methods=frozenset({name}), dry_run=False)
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        with pytest.raises(KorailProtocolError, match="high-level KorailClient"):
            client.v7.call(name, {"txtJobId": "synthetic-job"}, consent=consent)
    finally:
        client.close()


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
_PARTNER_ORIGINS = {
    interface: f"https://{interface.lower()}.example"
    for interface in {contract.interface for contract in V7_CONTRACTS.values()}
    if interface != "NetworkApi"
}


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
    if name == SPECIAL:
        form = _special_form()
        return (
            {k: v for k, v in form.items() if k not in {"Device", "Version", "Key"}},
            True,
        )
    if name == "NetworkApi.productCancel":
        return {"txtVrRsNo": "v-reservation", "txtGdSqno": "v-product"}, False
    if contract.request_model == "com.korail.talk.network.model.GreenCarDetailRequest":
        return {"first": "v-first", "second": "v-second"}, False
    if contract.request_model == "com.korail.talk.data.CacheCheckRequest":
        return {"versions": {"station": "1"}}, False
    declared = contract.fields if contract.form else contract.queries
    values: dict = {key: f"v-{key}" for key in sorted(declared)}
    if ("FieldMap" if contract.form else "QueryMap") in _bare_params(contract.params):
        values["mapKey"] = "v-mapKey"
    return values, False


@pytest.mark.parametrize("name", _SENT_CONTRACT_NAMES)
def test_every_contract_goes_out_as_its_row_describes(name: str) -> None:
    """Method, host, path, headers and encoding, for each of the 113 it sends.

    The other four of the 117 are the pass purchases, refused by name.

    Mutations are sent with a consent naming that one method; a card-bearing
    one gets the fake-card claim, which is the default.
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

    def partner(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    consent = (
        V7MutationConsent(allow_methods=frozenset({name}), dry_run=False)
        if contract.effect == "mutation"
        else None
    )
    client = KorailClient(
        transport=httpx.MockTransport(main),
        partner_origins=_PARTNER_ORIGINS,
        partner_transport=httpx.MockTransport(partner),
    )
    try:
        result = client.v7.call(
            name,
            values,
            headers=headers,
            consent=consent,
            include_common=include_common,
        )
    finally:
        client.close()

    assert isinstance(result, V7Response)
    assert len(seen) == 1
    request = seen[0]
    assert request.method == contract.http
    # One route is relative in its annotation (SamsungWalletApi's
    # "wallet/cmn/..."). Retrofit resolves that against the base URL, and a
    # partner origin here is path-less by rule, so it lands at the root.
    assert request.url.path == "/" + contract.route.lstrip("/")
    expected_host = (
        "smart.letskorail.com"
        if contract.interface == "NetworkApi"
        else httpx.URL(_PARTNER_ORIGINS[contract.interface]).host
    )
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
def test_no_consent_can_name_a_pass_purchase(name: str) -> None:
    # A 정기권/패스 settlement is ₩150,000-₩250,000 with no refund or cancel
    # route here, and the shipped app never sends passPayIssue at all.
    # MUTATION_HANDOFF promises no amount of consent can send one; the 7.0.6
    # gateway lists the contracts because the APK declares them.
    assert V7_CONTRACTS[name].effect == "mutation"
    with pytest.raises(KorailProtocolError):
        V7MutationConsent(allow_methods=frozenset({name}), dry_run=False)


@pytest.mark.parametrize("name", _PASS_PURCHASES)
def test_the_gateway_refuses_a_pass_purchase_even_with_a_forged_consent(
    name: str,
) -> None:
    consent = V7MutationConsent(dry_run=False, real_card_acknowledged=True, fake_card_only=False)
    object.__setattr__(consent, "allow_methods", frozenset({name}))
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        with pytest.raises(KorailMutationNotAllowedError, match="never sends"):
            client.v7.call(name, {}, consent=consent)
    finally:
        client.close()


# The mutation contracts that settle a payment, and so need a consent that
# says which card kind it means. Written out here, not imported.
_CARD_BEARING = (
    "NetworkApi.paymentMassStatusIn",
    "NetworkApi.postIntgStl",
    "NetworkApi.postKrPassPayment",
    "NetworkApi.postNaverPayMoneyRsv",
    "NetworkApi.postNaverPayRsv",
    "NetworkApi.postPayco",
    "NetworkApi.postRailplusAutoCharge",
    "NetworkApi.postSpayOrdNo",
    "NetworkApi.postStbkAcnt",
    "NetworkApi.postStbkRegBank",
    "NetworkApi.postStlKeyPrs",
    "NetworkApi.postTossautoC",
)


def _unstated_card_kind(name: str) -> V7MutationConsent:
    # Neither claim: fake_card_only and real_card_acknowledged both False.
    return V7MutationConsent(allow_methods=frozenset({name}), fake_card_only=False)


@pytest.mark.parametrize("name", _CARD_BEARING)
def test_a_payment_contract_needs_a_stated_card_kind(name: str) -> None:
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        with pytest.raises(KorailMutationNotAllowedError, match="explicit card kind"):
            client.v7.call(name, {}, consent=_unstated_card_kind(name))
    finally:
        client.close()


@pytest.mark.parametrize(
    "name",
    ["NetworkApi.postShinhanEncrypt", "NetworkApi.postMaasCancel", "NetworkApi.postAcpnMlgSave"],
)
def test_a_mutation_that_carries_no_payment_card_does_not(name: str) -> None:
    # Checked against the APK: postShinhanEncrypt's value is the locked amount
    # (PayViewModel.executeSeedEncrypt), postMaasCancel carries settlement ids,
    # and postAcpnMlgSave's *MbCrdNo fields are membership card numbers.
    values, include_common = _wire_values(name)
    client = KorailClient(transport=httpx.MockTransport(_never_send))
    try:
        preview = client.v7.call(
            name,
            values,
            consent=_unstated_card_kind(name),
            include_common=include_common,
        )
    finally:
        client.close()
    assert isinstance(preview, V7MutationPreview)
