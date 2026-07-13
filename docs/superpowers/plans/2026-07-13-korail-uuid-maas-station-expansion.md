# KORAIL UUID And MAAS Station Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add typed, account-neutral KORAIL UUID and MAAS station reads with exact route/form enforcement, repr-safe output, and bounded live evidence.

**Architecture:** Keep `KorailClient` as the only public request facade. Add small frozen result models and parsers, extend the exact route registry by two, and add an opt-in live summary that always tests UUID but calls MAAS only when a private `KORAIL_MAAS_SERVICE_CODE` exists. Preserve strict response envelopes by default and opt out only for the live-evidenced partial UUID response and the envelope-free MAAS station call.

**Tech Stack:** Python 3.11+, `httpx>=0.27,<1`, `cryptography>=42,<47`, frozen dataclasses, `pytest>=8,<10`, setuptools.

## Global Constraints

- Work only in `/Users/yakisoba/Documents/GitHub/korail-mobile-api`; preserve all unrelated user changes and never reset or stash them.
- Implement only `GET /ebizcross/getUUID.do` and `POST /ebizmaas/EbizMaasStationList.do` on `https://smart.letskorail.com`.
- Require a non-empty caller-supplied MAAS additional-service code; never invent an empty, fixed, or guessed default.
- Send only `addSrvDvCd` to the MAAS route; do not add `Device`, `Version`, or `Key`.
- Permit relaxed envelope decoding only at the UUID and MAAS public call sites.
  UUID must still contain a non-empty string `mutMrkVrfCd`; no general transport
  default or existing caller may be weakened.
- Do not change `DYNAPATH_ALLOWLIST_PATHS`, the fixed `rt=0` token engine, or any existing token behavior.
- Never add or call MAAS menu, cart, reservation, payment, cancellation, refund, check-in, member, point, mileage, or cross-package orchestration APIs.
- Keep raw mappings and `mutMrkVrfCd` caller-accessible where designed but absent from repr, rendered exceptions, logs, docs examples, and live output.
- Default tests remain offline with `httpx.MockTransport`; live calls require explicit opt-in and ignored local environment values.
- Keep Python support at `>=3.11` and add no dependency.

---

## File Structure

Files created by this plan:

- `tests/fixtures/uuid_success.json`: sanitized successful UUID envelope.
- `tests/fixtures/maas_station_data.json`: sanitized envelope-free MAAS station payload.
- `tests/test_uuid_maas_read_apis.py`: focused model, parser, payload, and client tests.

Existing files modified by this plan:

- `src/korail_mobile_api/models.py`: add `UuidResponse`, `KorailStation`, and `StationDataResponse`.
- `src/korail_mobile_api/parsers.py`: add strict typed UUID and station parsers.
- `src/korail_mobile_api/payloads.py`: add the exact MAAS form builder.
- `src/korail_mobile_api/safety.py`: add exactly two read-only routes.
- `src/korail_mobile_api/http.py`: add default-strict `require_envelope` support to POST.
- `src/korail_mobile_api/client.py`: add the two public facade methods.
- `src/korail_mobile_api/redaction.py`: classify mutual-verification names as sensitive.
- `src/korail_mobile_api/__init__.py`: export the three new models.
- `src/korail_mobile_api/live.py`: add bounded UUID/optional-MAAS metrics.
- `tests/test_http.py`: lock routes, envelope behavior, and no-DynaPath behavior.
- `tests/test_models.py`: lock frozen/repr-safe model behavior.
- `tests/test_public_contract.py`: lock methods, signatures, annotations, and exports.
- `tests/test_redaction_safety.py`: lock code redaction.
- `tests/test_live.py`: lock both MAAS-code branches and bounded output.
- `tests/test_live_service.py`: require UUID success and conditionally require MAAS success.
- `README.md`: document the public surface, environment gate, and exclusions.
- `docs/IMPLEMENTATION_PROGRESS.md`: record actual verification and remaining gate.

---

### Task 1: Typed Models, Payload, And Parsers

**Files:**

- Create: `tests/fixtures/uuid_success.json`
- Create: `tests/fixtures/maas_station_data.json`
- Create: `tests/test_uuid_maas_read_apis.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/payloads.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `tests/test_models.py`

**Interfaces:**

- Consumes: `BaseKorailResponse` and `KorailProtocolError`.
- Produces: `UuidResponse`, `KorailStation`, `StationDataResponse`, `build_maas_station_form()`, `parse_uuid_response()`, and `parse_station_data_response()`.

- [ ] **Step 1: Add sanitized fixtures and failing parser/payload tests**

Create `tests/fixtures/uuid_success.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","mutMrkVrfCd":"fixture-verification-code"}
```

Create `tests/fixtures/maas_station_data.json`:

```json
{"stns":{"stn":[{"stn_cd":"0001","stn_nm":"서울","longitude":"126.9708","latitude":"37.5547"},{"stn_cd":"0020","stn_nm":"부산","longitude":"129.0403","latitude":"35.1151"}]}}
```

Create `tests/test_uuid_maas_read_apis.py` with these initial tests:

```python
import pytest

from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.models import BaseKorailResponse
from korail_mobile_api.parsers import (
    parse_station_data_response,
    parse_uuid_response,
)
from korail_mobile_api.payloads import build_maas_station_form


def test_uuid_parser_returns_repr_safe_typed_code(load_json_fixture):
    raw = load_json_fixture("uuid_success.json")
    result = parse_uuid_response(BaseKorailResponse.from_raw(raw))
    assert result.verification_code == "fixture-verification-code"
    assert result.h_msg_cd == "API.I00000"
    assert result.raw is raw
    assert "fixture-verification-code" not in repr(result)


def test_station_parser_returns_typed_rows_from_envelope_free_payload(load_json_fixture):
    raw = load_json_fixture("maas_station_data.json")
    result = parse_station_data_response(BaseKorailResponse(raw=raw))
    assert [(item.code, item.name) for item in result.stations] == [
        ("0001", "서울"),
        ("0020", "부산"),
    ]
    assert result.stations[0].longitude == "126.9708"
    assert result.raw is raw


def test_station_parser_preserves_a_present_common_envelope(load_json_fixture):
    raw = load_json_fixture("maas_station_data.json")
    raw.update(
        {
            "h_msg_cd": "API.I00000",
            "h_msg_txt": "Success",
            "strResult": "SUCC",
        }
    )
    result = parse_station_data_response(BaseKorailResponse.from_raw(raw))
    assert result.h_msg_cd == "API.I00000"
    assert len(result.stations) == 2


@pytest.mark.parametrize("value", [None, "", "   ", 101, False])
def test_maas_station_form_rejects_missing_or_nonstring_code(value):
    with pytest.raises(ValueError, match="additional_service_code"):
        build_maas_station_form(value)


def test_maas_station_form_preserves_exact_nonempty_code():
    assert build_maas_station_form(" M10 ") == {"addSrvDvCd": " M10 "}


@pytest.mark.parametrize(
    "raw",
    [
        {"stns": None},
        {"stns": {}},
        {"stns": {"stn": "not-a-list"}},
        {"stns": {"stn": ["not-an-object"]}},
        {"stns": {"stn": [{"stn_cd": "", "stn_nm": "서울"}]}},
        {"stns": {"stn": [{"stn_cd": "0001", "stn_nm": None}]}},
        {"stns": {"stn": [{"stn_cd": "0001", "stn_nm": "서울", "latitude": 37.5}]}},
    ],
)
def test_station_parser_rejects_malformed_known_structure(raw):
    with pytest.raises(KorailProtocolError):
        parse_station_data_response(BaseKorailResponse(raw=raw))


@pytest.mark.parametrize("value", [None, "", "   ", 123, [], {}])
def test_uuid_parser_rejects_missing_or_malformed_code(value):
    raw = {
        "h_msg_cd": "API.I00000",
        "h_msg_txt": "Success",
        "strResult": "SUCC",
        "mutMrkVrfCd": value,
    }
    with pytest.raises(KorailProtocolError, match="mutMrkVrfCd"):
        parse_uuid_response(BaseKorailResponse.from_raw(raw))
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py -q
```

Expected: collection fails because the new models, payload builder, and parsers do not exist.

- [ ] **Step 3: Implement the models and exact payload builder**

Append to `src/korail_mobile_api/models.py` after `NoticeResponse`:

```python
@dataclass(frozen=True)
class UuidResponse(BaseKorailResponse):
    verification_code: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class KorailStation:
    code: str
    name: str
    longitude: str | None = None
    latitude: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class StationDataResponse(BaseKorailResponse):
    stations: tuple[KorailStation, ...] = ()
```

Append to `src/korail_mobile_api/payloads.py`:

```python
def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise ValueError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
```

- [ ] **Step 4: Implement strict typed parsers**

Add `KorailStation`, `StationDataResponse`, and `UuidResponse` to the model imports in `src/korail_mobile_api/parsers.py`, then append:

```python
def _station_optional_string(row: Mapping[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL station field {key} must be a string or null"
        )
    return value


def _station_required_string(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL station field {key} must be a non-empty string"
        )
    return value


def parse_uuid_response(response: BaseKorailResponse) -> UuidResponse:
    value = response.raw.get("mutMrkVrfCd")
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            "KORAIL UUID response mutMrkVrfCd must be a non-empty string"
        )
    return UuidResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=response.raw,
        verification_code=value,
    )


def parse_station_data_response(
    response: BaseKorailResponse,
) -> StationDataResponse:
    container = response.raw.get("stns")
    if not isinstance(container, Mapping):
        raise KorailProtocolError("KORAIL station data missing stns object")
    rows = container.get("stn")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    stations: list[KorailStation] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL station data contained a non-object row"
            )
        raw = dict(row)
        stations.append(
            KorailStation(
                code=_station_required_string(row, "stn_cd"),
                name=_station_required_string(row, "stn_nm"),
                longitude=_station_optional_string(row, "longitude"),
                latitude=_station_optional_string(row, "latitude"),
                raw=raw,
            )
        )
    return StationDataResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=response.raw,
        stations=tuple(stations),
    )
```

- [ ] **Step 5: Lock frozen/repr-safe model behavior and run GREEN**

Add to `tests/test_models.py` imports and append:

```python
def test_uuid_and_station_models_are_frozen_and_repr_safe():
    station = KorailStation(
        code="0001",
        name="서울",
        raw={"secret": "station-raw-secret"},
    )
    uuid = UuidResponse(
        verification_code="uuid-secret",
        raw={"mutMrkVrfCd": "uuid-secret"},
    )
    response = StationDataResponse(stations=(station,))
    assert is_dataclass(UuidResponse)
    assert is_dataclass(KorailStation)
    assert is_dataclass(StationDataResponse)
    assert "uuid-secret" not in repr(uuid)
    assert "station-raw-secret" not in repr(station)
    with pytest.raises(FrozenInstanceError):
        response.stations = ()
```

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py tests/test_models.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit Task 1**

```bash
git add src/korail_mobile_api/models.py src/korail_mobile_api/payloads.py src/korail_mobile_api/parsers.py tests/fixtures/uuid_success.json tests/fixtures/maas_station_data.json tests/test_uuid_maas_read_apis.py tests/test_models.py
git commit -m "feat: add korail uuid and maas station models"
```

---

### Task 2: Exact Routes And Envelope-Aware POST Transport

**Files:**

- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/http.py`
- Modify: `tests/test_http.py`

**Interfaces:**

- Consumes: `KORAIL_READ_ONLY_ROUTES`, `BaseKorailResponse`, and existing strict `post_form()` behavior.
- Produces: a 14-route registry and `post_form(..., require_envelope: bool = True)`.

- [ ] **Step 1: Add failing exact-route and transport tests**

Extend the accepted route parametrization in `tests/test_http.py` with:

```python
("GET", "/ebizcross/getUUID.do"),
("POST", "/ebizmaas/EbizMaasStationList.do"),
```

Change the exact route assertion to:

```python
def test_read_only_route_registry_has_exact_expanded_count():
    assert len(KORAIL_READ_ONLY_ROUTES) == 14
```

Append:

```python
def test_post_form_can_accept_one_envelope_free_object_without_weakening_default():
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"stns": {"stn": []}})
        return httpx.Response(200, json={"stns": {"stn": []}})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    relaxed = client.post_form(
        "/ebizmaas/EbizMaasStationList.do",
        {"addSrvDvCd": "M10"},
        include_common=False,
        require_envelope=False,
    )
    assert relaxed.raw == {"stns": {"stn": []}}
    with pytest.raises(KorailProtocolError, match="envelope"):
        client.post_form(
            "/ebizmaas/EbizMaasStationList.do",
            {"addSrvDvCd": "M10"},
            include_common=False,
        )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/ebizcross/getUUID.do"),
        ("GET", "/ebizmaas/EbizMaasStationList.do"),
        ("GET", "/ebizcross/%67etUUID.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do/extra"),
    ],
)
def test_uuid_maas_route_bypasses_are_rejected(method, path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route(method, path)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/ebizcross/getUUID.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do"),
    ],
)
def test_uuid_maas_routes_never_generate_dynapath(method, path):
    provider_called = False

    def provider(_context):
        nonlocal provider_called
        provider_called = True
        return "must-not-be-used"

    def handler(request: httpx.Request) -> httpx.Response:
        assert DYNAPATH_HEADER_NAME not in request.headers
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "API.I00000",
                "h_msg_txt": "Success",
                "strResult": "SUCC",
                "mutMrkVrfCd": "fixture-code",
            },
        )

    client = KorailHttpClient(
        KorailConfig(
            dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
        transport=httpx.MockTransport(handler),
    )
    if method == "GET":
        client.get_json(path)
    else:
        client.post_form(path, {"addSrvDvCd": "M10"}, include_common=False)
    assert provider_called is False
```

- [ ] **Step 2: Run route/transport tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_http.py -q
```

Expected: failures show the two routes are absent, the count is 12, and `post_form()` does not accept `require_envelope`.

- [ ] **Step 3: Add exactly two routes**

Add to `KORAIL_READ_ONLY_ROUTES` in `src/korail_mobile_api/safety.py`:

```python
("GET", "/ebizcross/getUUID.do"),
("POST", "/ebizmaas/EbizMaasStationList.do"),
```

Do not modify `DYNAPATH_ALLOWLIST_PATHS`.

- [ ] **Step 4: Add default-strict envelope handling to POST**

Change `KorailHttpClient.post_form()` in `src/korail_mobile_api/http.py` to accept:

```python
def post_form(
    self,
    path: str,
    data: Mapping[str, Any] | None = None,
    *,
    include_common: bool = True,
    raise_on_fail: bool = True,
    require_envelope: bool = True,
) -> BaseKorailResponse:
```

Replace its final unconditional `parse_base_response()` return with:

```python
        if not require_envelope:
            if not isinstance(payload, dict):
                raise KorailProtocolError(
                    "KORAIL response must be a JSON object"
                )
            if all(
                name in payload
                for name in ("h_msg_cd", "h_msg_txt", "strResult")
            ):
                return parse_base_response(
                    payload,
                    raise_on_fail=raise_on_fail,
                )
            return BaseKorailResponse(raw=payload)
        return parse_base_response(payload, raise_on_fail=raise_on_fail)
```

- [ ] **Step 5: Run route/transport tests and verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_http.py -q
```

Expected: all HTTP tests pass; existing callers remain strict.

- [ ] **Step 6: Commit Task 2**

```bash
git add src/korail_mobile_api/safety.py src/korail_mobile_api/http.py tests/test_http.py
git commit -m "feat: allow exact korail uuid and maas routes"
```

---

### Task 3: Public Client, Exports, And Redaction

**Files:**

- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Modify: `src/korail_mobile_api/redaction.py`
- Modify: `tests/test_uuid_maas_read_apis.py`
- Modify: `tests/test_public_contract.py`
- Modify: `tests/test_redaction_safety.py`

**Interfaces:**

- Consumes: Task 1 parsers/builders and Task 2 transport/routes.
- Produces: `KorailClient.get_uuid()` and `KorailClient.get_maas_station_data()` plus root exports.

- [ ] **Step 1: Add failing exact-request and validation tests**

Append to `tests/test_uuid_maas_read_apis.py`:

```python
from urllib.parse import parse_qs

import httpx

from korail_mobile_api import KorailClient, KorailConfig


def test_client_sends_exact_uuid_and_maas_requests(load_json_fixture):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/ebizcross/getUUID.do":
            return httpx.Response(
                200,
                json=load_json_fixture("uuid_success.json"),
            )
        if request.url.path == "/ebizmaas/EbizMaasStationList.do":
            return httpx.Response(
                200,
                json=load_json_fixture("maas_station_data.json"),
            )
        raise AssertionError(request.url.path)

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    try:
        uuid = client.get_uuid()
        stations = client.get_maas_station_data("M10")
    finally:
        client.close()
    assert uuid.verification_code == "fixture-verification-code"
    assert len(stations.stations) == 2
    assert captured[0].method == "GET"
    assert captured[0].url.path == "/ebizcross/getUUID.do"
    assert captured[0].url.query == b""
    assert captured[1].method == "POST"
    assert captured[1].url.path == "/ebizmaas/EbizMaasStationList.do"
    assert parse_qs(captured[1].content.decode()) == {"addSrvDvCd": ["M10"]}


@pytest.mark.parametrize("value", [None, "", "   ", 10, False])
def test_client_rejects_invalid_maas_code_before_io(value):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(ValueError, match="additional_service_code"):
            client.get_maas_station_data(value)
    finally:
        client.close()
    assert called is False
```

Extend the method set and signatures in `tests/test_public_contract.py`:

```python
assert methods == {
    "clear_session",
    "close",
    "get_app_data",
    "get_common_code",
    "get_maas_station_data",
    "get_notice",
    "get_station_data",
    "get_station_info",
    "get_ticket_list",
    "get_train_calendar",
    "get_train_schedule",
    "get_transfer_stations",
    "get_uuid",
    "login",
    "logout",
    "search_trains",
}


def test_uuid_maas_signatures_types_and_exports_are_stable():
    assert list(inspect.signature(KorailClient.get_uuid).parameters) == ["self"]
    assert list(
        inspect.signature(KorailClient.get_maas_station_data).parameters
    ) == ["self", "additional_service_code"]
    assert KorailClient.get_uuid.__annotations__["return"] is UuidResponse
    assert (
        KorailClient.get_maas_station_data.__annotations__["return"]
        is StationDataResponse
    )
    for name in ("UuidResponse", "KorailStation", "StationDataResponse"):
        assert getattr(korail_mobile_api, name)
```

Because `client.py` does not use postponed annotations, import `UuidResponse` and `StationDataResponse` in this test from `korail_mobile_api.models`.

- [ ] **Step 2: Add failing redaction tests**

Extend the sensitive-key parametrization and mapping test in `tests/test_redaction_safety.py` with `mutMrkVrfCd` and `verification_code`, then append:

```python
def test_uuid_verification_names_are_redacted_case_insensitively():
    value = {
        "mutMrkVrfCd": "server-secret",
        "VERIFICATION_CODE": "model-secret",
    }
    redacted = redact_mapping(value)
    assert redacted == {
        "mutMrkVrfCd": "[REDACTED]",
        "VERIFICATION_CODE": "[REDACTED]",
    }
    rendered = redact_text(
        'mutMrkVrfCd="server-secret" verification_code=model-secret'
    )
    assert "server-secret" not in rendered
    assert "model-secret" not in rendered
```

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py tests/test_public_contract.py tests/test_redaction_safety.py -q
```

Expected: failures show missing client methods/exports and unredacted verification names.

- [ ] **Step 4: Implement the public methods**

Add the new model, parser, and payload imports to `src/korail_mobile_api/client.py`, then add after `get_notice()`:

```python
    def get_uuid(self) -> UuidResponse:
        return self._run_read(
            lambda: parse_uuid_response(
                self.http.get_json("/ebizcross/getUUID.do")
            )
        )

    def get_maas_station_data(
        self,
        additional_service_code: str,
    ) -> StationDataResponse:
        form = build_maas_station_form(additional_service_code)
        return self._run_read(
            lambda: parse_station_data_response(
                self.http.post_form(
                    "/ebizmaas/EbizMaasStationList.do",
                    form,
                    include_common=False,
                    require_envelope=False,
                )
            )
        )
```

- [ ] **Step 5: Export models and redact verification keys**

Import and add these names to `__all__` in `src/korail_mobile_api/__init__.py`:

```python
KorailStation
StationDataResponse
UuidResponse
```

Add these exact keys to `SENSITIVE_KEYS` in `src/korail_mobile_api/redaction.py`:

```python
"mutMrkVrfCd",
"verification_code",
```

- [ ] **Step 6: Run focused tests and verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py tests/test_public_contract.py tests/test_redaction_safety.py -q
```

Expected: all selected tests pass.

- [ ] **Step 7: Commit Task 3**

```bash
git add src/korail_mobile_api/client.py src/korail_mobile_api/__init__.py src/korail_mobile_api/redaction.py tests/test_uuid_maas_read_apis.py tests/test_public_contract.py tests/test_redaction_safety.py
git commit -m "feat: expose korail uuid and maas station reads"
```

---

### Task 4: Bounded Live Summary And Documentation

**Files:**

- Modify: `src/korail_mobile_api/live.py`
- Modify: `tests/test_live.py`
- Modify: `tests/test_live_service.py`
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`

**Interfaces:**

- Consumes: both new public methods and the ignored optional `KORAIL_MAAS_SERVICE_CODE`.
- Produces: `uuidLoaded`, `maasStationTested`, and `maasStationCount` live fields without sensitive values.

- [ ] **Step 1: Extend the existing fake-client test and verify RED**

Parametrize `test_run_live_smoke_calls_every_current_read_without_raw_output` in `tests/test_live.py`:

```python
@pytest.mark.parametrize(
    ("maas_code", "maas_tested", "maas_count"),
    [(None, False, 0), ("M10", True, 1)],
)
def test_run_live_smoke_calls_every_current_read_without_raw_output(
    monkeypatch,
    maas_code,
    maas_tested,
    maas_count,
):
```

Add these methods to its `FakeClient`:

```python
        def get_uuid(self) -> UuidResponse:
            calls.append(("get_uuid",))
            return UuidResponse(
                h_msg_cd="API.I00000",
                str_result="SUCC",
                verification_code="uuid-secret",
                raw={"mutMrkVrfCd": "uuid-secret"},
            )

        def get_maas_station_data(
            self,
            additional_service_code: str,
        ) -> StationDataResponse:
            calls.append(("get_maas_station_data", additional_service_code))
            return StationDataResponse(
                stations=(KorailStation(code="0001", name="서울"),),
                raw={"stns": {"stn": [{"stn_cd": "0001", "stn_nm": "서울"}]}},
            )
```

Set or delete the environment inside the test:

```python
    if maas_code is None:
        monkeypatch.delenv("KORAIL_MAAS_SERVICE_CODE", raising=False)
    else:
        monkeypatch.setenv("KORAIL_MAAS_SERVICE_CODE", maas_code)
```

Add these expected result fields:

```python
"uuidLoaded": True,
"maasStationTested": maas_tested,
"maasStationCount": maas_count,
```

Require `get_uuid` before login. Require `get_maas_station_data` before login only when `maas_code` is present, and assert `uuid-secret`, `M10`, `mutMrkVrfCd`, and raw station data are absent from `repr(result)`.

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_live.py -q
```

Expected: the test fails because the live helper does not call or summarize the new reads.

- [ ] **Step 2: Implement bounded optional-MAAS live behavior**

In `run_live_smoke_from_env()` in `src/korail_mobile_api/live.py`, immediately after app-data and notice reads, add:

```python
        uuid = client.get_uuid()
        maas_service_code = os.environ.get("KORAIL_MAAS_SERVICE_CODE")
        maas_stations = (
            client.get_maas_station_data(maas_service_code)
            if maas_service_code
            else None
        )
```

Add to its returned mapping:

```python
"uuidLoaded": bool(uuid.verification_code),
"maasStationTested": maas_stations is not None,
"maasStationCount": (
    len(maas_stations.stations) if maas_stations is not None else 0
),
```

Do not return the code, service code, raw mapping, or station rows.

- [ ] **Step 3: Run live-helper tests and verify GREEN**

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_live.py -q
```

Expected: both supplied-code and absent-code branches pass.

- [ ] **Step 4: Lock the live-service completion assertions**

Import `os` in `tests/test_live_service.py` and add after the existing assertions:

```python
    assert result["uuidLoaded"] is True
    if os.environ.get("KORAIL_MAAS_SERVICE_CODE"):
        assert result["maasStationTested"] is True
        assert result["maasStationCount"] >= 0
    else:
        assert result["maasStationTested"] is False
        assert result["maasStationCount"] == 0
```

Run offline to confirm it remains an explicit skip:

```bash
env -u KORAIL_MOBILE_API_LIVE PYTHONPATH=src python3 -m pytest tests/test_live_service.py -q
```

Expected: one intentional live skip.

- [ ] **Step 5: Document the exact surface and pending gate**

Add a README section containing these exact facts:

```markdown
### UUID and MAAS station reads

`get_uuid()` performs the parameter-free account-neutral UUID read.
`get_maas_station_data(additional_service_code)` requires the service code that
the official app obtains dynamically; the library has no empty or fixed default.
Neither request uses DynaPath, and neither method starts a reservation or passes
the UUID value to SRT automatically.

Set `KORAIL_MAAS_SERVICE_CODE` only in the ignored live environment to include
the MAAS endpoint in bounded live verification. Without it, the helper reports
`maasStationTested=false` and performs no MAAS request.
```

Update `docs/IMPLEMENTATION_PROGRESS.md` at this stage to state that the two
methods, route count 14, and focused offline tests are implemented while the
complete suite, build/import, and bounded live gates remain pending. Task 5 will
replace those pending statements with actual evidence. Never record the UUID
value or service code.

- [ ] **Step 6: Commit Task 4**

```bash
git add src/korail_mobile_api/live.py tests/test_live.py tests/test_live_service.py README.md docs/IMPLEMENTATION_PROGRESS.md
git commit -m "docs: add korail uuid and maas live boundary"
```

---

### Task 5: Full Verification, Independent Review, And Live Gate

**Files:**

- Verify all changed files.
- Modify `docs/IMPLEMENTATION_PROGRESS.md` only if actual results differ from Task 4 wording.

**Interfaces:**

- Consumes: the complete implementation.
- Produces: fresh offline/build/import/static/live evidence and a clean handoff.

- [ ] **Step 1: Run the complete offline suite once**

Run:

```bash
env -u KORAIL_MOBILE_API_LIVE -u KORAIL_MEMBER_NO -u KORAIL_PASSWORD PYTHONPATH=src python3 -m pytest -q
```

Expected: all offline tests pass and only the explicitly opted-in live test skips.

- [ ] **Step 2: Build wheel and sdist once**

Run:

```bash
python3 -m build
```

Expected: one wheel and one sdist are created under `dist/` with exit code 0.

- [ ] **Step 3: Verify the built wheel in isolation**

Run:

```bash
tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
python3 -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --quiet --disable-pip-version-check dist/korail_mobile_api-0.1.0-py3-none-any.whl
"$tmpdir/venv/bin/python" - <<'PY'
from korail_mobile_api import KorailClient, KorailStation, StationDataResponse, UuidResponse
print(KorailClient.__name__, KorailStation.__name__, StationDataResponse.__name__, UuidResponse.__name__)
PY
```

Expected output names: `KorailClient KorailStation StationDataResponse UuidResponse`.

- [ ] **Step 4: Confirm static safety boundaries**

Run:

```bash
PYTHONPATH=src python3 - <<'PY'
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS
from korail_mobile_api.safety import KORAIL_READ_ONLY_ROUTES

assert len(KORAIL_READ_ONLY_ROUTES) == 14
assert ("GET", "/ebizcross/getUUID.do") in KORAIL_READ_ONLY_ROUTES
assert ("POST", "/ebizmaas/EbizMaasStationList.do") in KORAIL_READ_ONLY_ROUTES
assert "/ebizcross/getUUID.do" not in DYNAPATH_ALLOWLIST_PATHS
assert "/ebizmaas/EbizMaasStationList.do" not in DYNAPATH_ALLOWLIST_PATHS
print("routes=14 new_routes=2 dynapath_new_routes=0")
PY
```

- [ ] **Step 5: Request independent read-only review**

Ask a reviewer to compare the diff with the approved spec, focusing on exact
forms, `post_form()` default strictness, DynaPath non-use, redaction, raw-output
boundaries, public compatibility, and absence of mutation routes. Resolve every
finding before continuing.

- [ ] **Step 6: Run one bounded opted-in live verification**

Source the ignored local environment without printing it. Run only
`run_live_smoke_from_env()` and serialize its bounded mapping. Do not print
exceptions containing raw responses.

Required outcomes:

- `uuidLoaded == True` to complete the UUID gate.
- If `KORAIL_MAAS_SERVICE_CODE` exists, `maasStationTested == True` and a
  non-negative actual `maasStationCount` complete the MAAS gate.
- If it does not exist, `maasStationTested == False` and no MAAS request occurs;
  document this gate as pending without inventing a value.

- [ ] **Step 7: Record actual evidence and clean generated artifacts**

Update `docs/IMPLEMENTATION_PROGRESS.md` from actual command output. Remove
generated `dist/` and `build/`, run `git diff --check`, and confirm no ignored
credential file, UUID value, MAAS code, raw response, APK, or generated artifact
is staged.

- [ ] **Step 8: Commit only the evidence correction if needed**

```bash
git add docs/IMPLEMENTATION_PROGRESS.md
git commit -m "docs: record korail uuid maas verification"
```

Skip this commit when Task 4 already contains the exact final evidence.

## Final Verification Checklist

- [ ] Every production method was introduced after an observed failing test.
- [ ] The full offline suite passes with only the explicit live skip.
- [ ] Wheel/sdist build and isolated imports pass.
- [ ] The exact route count is 14 and the DynaPath route set is unchanged.
- [ ] UUID sends no parameters; MAAS sends only caller-supplied `addSrvDvCd`.
- [ ] Existing POST callers remain envelope-strict by default.
- [ ] Verification codes/raw mappings are hidden from repr, errors, logs, and live output.
- [ ] No mutation, menu, cross-package, or guessed-code behavior exists.
- [ ] UUID bounded live verification passes.
- [ ] MAAS live verification either passes with a private supplied code or is explicitly pending.
- [ ] Progress documentation matches actual evidence.

---

### Task 6: Correct The Live UUID Partial-Envelope Contract

**Files:**

- Modify: `tests/test_uuid_maas_read_apis.py`
- Modify: `src/korail_mobile_api/client.py`

**Interfaces:**

- Consumes: the existing default-strict `get_json(..., require_envelope=True)`
  transport and strict `parse_uuid_response()` verification-field validation.
- Produces: a UUID-only `require_envelope=False` call-site exception without any
  transport-default, POST, route, DynaPath, parser, model, or public-API change.

- [ ] **Step 1: Add the failing partial-envelope client regression test**

Append to `tests/test_uuid_maas_read_apis.py`:

```python
def test_client_uuid_accepts_live_evidenced_partial_common_envelope():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json={
                "strResult": "SUCC",
                "mutMrkVrfCd": "fixture-partial-code",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        result = client.get_uuid()
    finally:
        client.close()

    assert result.verification_code == "fixture-partial-code"
    assert result.raw["strResult"] == "SUCC"
    assert "fixture-partial-code" not in repr(result)
    assert len(captured) == 1
    assert captured[0].method == "GET"
    assert captured[0].url.path == "/ebizcross/getUUID.do"
    assert captured[0].url.query == b""
```

Run:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py -q
```

Expected RED: `KorailProtocolError` reports missing common-envelope fields.

- [ ] **Step 2: Apply the minimal UUID-only transport option**

Change only `KorailClient.get_uuid()`:

```python
def get_uuid(self) -> UuidResponse:
    return self._run_read(
        lambda: parse_uuid_response(
            self.http.get_json(
                "/ebizcross/getUUID.do",
                require_envelope=False,
            )
        )
    )
```

Do not change `KorailHttpClient`, `parse_uuid_response()`, route registration,
DynaPath settings, any POST call, or any public signature.

- [ ] **Step 3: Run the focused contract tests**

Run exactly:

```bash
PYTHONPATH=src python3 -m pytest tests/test_uuid_maas_read_apis.py tests/test_http.py tests/test_public_contract.py -q
```

Expected: all focused tests pass; default-strict transport and complete failure
envelopes remain covered.

- [ ] **Step 4: Commit the correction**

```bash
git add src/korail_mobile_api/client.py tests/test_uuid_maas_read_apis.py
git commit -m "fix: accept live korail uuid partial envelope"
```

---

### Task 7: Reverify And Record The Corrected Live UUID Contract

**Files:**

- Verify all changed files.
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`

**Interfaces:**

- Consumes: the Task 6 UUID-only correction and all prior KORAIL read-only work.
- Produces: fresh offline/build/import/static/review/live evidence, an explicit
  pending MAAS gate when no private code exists, and a clean handoff.

- [ ] **Step 1: Run final non-live gates on the corrected HEAD**

Run the complete offline suite once with live/credential variables removed,
then build wheel and sdist, install the wheel in a fresh venv, import
`KorailClient`, `UuidResponse`, `KorailStation`, and `StationDataResponse`, and
repeat the exact 14-route/two-new-route/no-new-DynaPath static assertions from
Task 5.

- [ ] **Step 2: Request independent read-only review**

Review the Task 6 diff against the approved live correction. Require the exact
no-parameter GET, UUID-only relaxed option, unchanged strict defaults and POST
behavior, non-empty verification validation, repr/redaction safety, and no
route/DynaPath/public-surface change. Resolve every finding before live.

- [ ] **Step 3: Run one bounded corrected live verification**

Source the ignored local environment silently and invoke only
`run_live_smoke_from_env()` once. Never print exceptions with raw data. Require
`uuidLoaded is True`. Because the current safe observation established that
`KORAIL_MAAS_SERVICE_CODE` is absent, require `maasStationTested is False` and
`maasStationCount == 0`; do not invent a code or call MAAS. Confirm the existing
bounded login/cache/station/calendar/train/schedule/transfer/ticket fields remain
valid without emitting raw data or secrets.

- [ ] **Step 4: Record evidence, clean artifacts, and commit**

Document the partial-envelope correction, actual offline/build/import/static
results, independent review, successful bounded UUID live result, and pending
MAAS live gate in `README.md` and `docs/IMPLEMENTATION_PROGRESS.md`. Do not record
the UUID value, raw mapping, credentials, cookies, identifiers, or service code.
Remove `dist/` and `build/`, run `git diff --check`, confirm only intended docs
are staged, and commit:

```bash
git add README.md docs/IMPLEMENTATION_PROGRESS.md
git commit -m "docs: record corrected korail uuid live result"
```
