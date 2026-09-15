"""7.0.6 계약 경로가 상위 API의 안전 경계를 우회하지 않는지 확인한다."""

from __future__ import annotations

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
