# KORAIL Cache Read Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this whole plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. One implementation agent owns this entire repository plan; do not dispatch implementation subtasks.

**Goal:** Add typed, account-neutral reads for the evidenced KORAIL app-main and notice cache endpoints while preserving the stabilized public contract and safety boundaries.

**Architecture:** Keep `KorailClient` as the facade and reuse `KorailHttpClient.get_json()` for canonical-origin, exact-route, JSON, envelope, and application-error classification. Put timestamp query construction in `payloads.py`, specialized normalization in `parsers.py`, frozen repr-safe types in `models.py`, and expose only bounded booleans through the live helper. Do not alter DynaPath state or its compatibility allowlist.

**Tech Stack:** Python 3.11+, `httpx>=0.27,<1`, `cryptography>=42,<47`, frozen dataclasses, `pytest>=8,<10`, setuptools.

## Global Constraints

- Work directly in the intentional dirty tree at `/Users/yakisoba/Documents/GitHub/korail-mobile-api`; never reset, discard, stash, or overwrite unrelated changes.
- Do not create a worktree and do not commit, stage, push, or open a pull request unless the user explicitly requests it.
- Follow TDD for each task: add a focused failing test, run it and observe the expected failure, implement the minimum behavior, rerun the focused test, then run the affected suite.
- Add only `GET /file/CACHE/prdMobilePlusMain.cache` and `GET /file/CACHE/prdMobilePlusNotice.cache`.
- Never add or call reservation, payment, cancellation, refund, check-in, member/point/mileage mutation, or other state-changing APIs.
- Keep `https://smart.letskorail.com` as the only accepted origin and preserve exact method/path enforcement before I/O.
- Preserve the per-client stateful DynaPath generator, rolling delta queue, token-source validation, and current DynaPath allowlist exactly.
- Raw responses remain caller-accessible but stay excluded from repr, logs, live output, and progress-document examples.
- Default tests remain offline and use `httpx.MockTransport`; live calls require the existing explicit opt-in and ignored local environment file.
- Keep Python support at `>=3.11` and add no runtime dependency.

---

## File Structure

Files created by this plan:

- `tests/fixtures/cache_app_data_success.json`: sanitized typed app-cache response.
- `tests/fixtures/cache_notice_success.json`: sanitized typed notice-cache response.
- `tests/test_cache_read_apis.py`: cache query, parser, and client orchestration contracts.

Existing files modified by this plan:

- `src/korail_mobile_api/models.py`: add `AppVersionInfo`, `AppDataResponse`, and `NoticeResponse`.
- `src/korail_mobile_api/parsers.py`: normalize validated cache responses and reject malformed known fields.
- `src/korail_mobile_api/payloads.py`: build and validate `timeStamp` queries.
- `src/korail_mobile_api/safety.py`: add exactly two GET routes.
- `src/korail_mobile_api/client.py`: expose `get_app_data()` and `get_notice()`.
- `src/korail_mobile_api/__init__.py`: export the three new types.
- `src/korail_mobile_api/live.py`: perform both cache reads before login and emit two booleans.
- `tests/test_http.py`: lock exact allowlist additions and bypass rejection.
- `tests/test_models.py`: lock new types and repr behavior.
- `tests/test_public_contract.py`: lock the expanded method set/signatures/exports.
- `tests/test_live.py`: lock pre-login cache calls and bounded output.
- `README.md`: document the two account-neutral reads.
- `docs/IMPLEMENTATION_PROGRESS.md`: record final verified state and the next safe candidate batch.

---

### Task 1: Frozen Cache Models And Strict Parsers

**Files:**

- Create: `tests/fixtures/cache_app_data_success.json`
- Create: `tests/fixtures/cache_notice_success.json`
- Create: `tests/test_cache_read_apis.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `tests/test_models.py`

**Interfaces:**

- Consumes: `BaseKorailResponse`, `KorailProtocolError`, and the existing JSON fixture loader.
- Produces: `AppVersionInfo`, `AppDataResponse`, `NoticeResponse`, `parse_app_data_response(response)`, and `parse_notice_response(response)`.

- [ ] **Step 1: Add sanitized response fixtures**

Create `tests/fixtures/cache_app_data_success.json` with:

```json
{
  "h_msg_cd": "S000",
  "h_msg_txt": "",
  "strResult": "SUCC",
  "disability_certification_msg": "synthetic certification guidance",
  "forSeatIntg": "Y",
  "airportBusMsg": "synthetic airport bus guidance",
  "railplus_cardinfo": "synthetic railplus guidance",
  "version": {
    "AMESSAGE": "synthetic update guidance",
    "NEWDVERSION": "999999999"
  },
  "unknownField": "preserved"
}
```

Create `tests/fixtures/cache_notice_success.json` with:

```json
{
  "h_msg_cd": "S000",
  "h_msg_txt": "",
  "strResult": "SUCC",
  "bbrdId": "SYNTHETIC",
  "ptwtSqno": "1",
  "ptwtTtl": "Synthetic notice",
  "unknownField": "preserved"
}
```

- [ ] **Step 2: Add failing model and parser tests**

Add imports and these tests to `tests/test_cache_read_apis.py`:

```python
import pytest

from korail_mobile_api.errors import KorailAppError, KorailProtocolError
from korail_mobile_api.models import BaseKorailResponse
from korail_mobile_api.parsers import (
    parse_app_data_response,
    parse_notice_response,
)


def test_app_data_parser_returns_typed_known_fields_and_preserves_raw(load_json_fixture):
    raw = load_json_fixture("cache_app_data_success.json")
    result = parse_app_data_response(BaseKorailResponse.from_raw(raw))
    assert result.disability_certification_msg == "synthetic certification guidance"
    assert result.for_seat_intg == "Y"
    assert result.airport_bus_msg == "synthetic airport bus guidance"
    assert result.railplus_cardinfo == "synthetic railplus guidance"
    assert result.version.message == "synthetic update guidance"
    assert result.version.new_version == "999999999"
    assert result.raw["unknownField"] == "preserved"
    assert "unknownField" not in repr(result)


def test_notice_parser_returns_typed_known_fields_and_preserves_raw(load_json_fixture):
    raw = load_json_fixture("cache_notice_success.json")
    result = parse_notice_response(BaseKorailResponse.from_raw(raw))
    assert result.board_id == "SYNTHETIC"
    assert result.post_sequence == "1"
    assert result.post_title == "Synthetic notice"
    assert result.raw["unknownField"] == "preserved"
    assert "unknownField" not in repr(result)


@pytest.mark.parametrize(
    ("parser", "field", "value"),
    [
        (parse_app_data_response, "version", []),
        (parse_app_data_response, "forSeatIntg", 1),
        (parse_notice_response, "ptwtTtl", {"bad": "shape"}),
    ],
)
def test_cache_parsers_reject_malformed_known_fields(parser, field, value):
    raw = {"h_msg_cd": "S000", "h_msg_txt": "", "strResult": "SUCC", field: value}
    with pytest.raises(KorailProtocolError):
        parser(BaseKorailResponse.from_raw(raw))
```

Add to `tests/test_models.py`:

```python
def test_cache_response_models_are_frozen_dataclasses():
    from dataclasses import is_dataclass
    from korail_mobile_api.models import AppDataResponse, AppVersionInfo, NoticeResponse

    assert is_dataclass(AppVersionInfo)
    assert is_dataclass(AppDataResponse)
    assert is_dataclass(NoticeResponse)
```

- [ ] **Step 3: Run focused tests and confirm the missing contract**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_models.py -q
```

Expected: collection fails because the new models and parser functions do not exist.

- [ ] **Step 4: Add the frozen models**

Add to `src/korail_mobile_api/models.py` after `BaseKorailResponse`:

```python
@dataclass(frozen=True)
class AppVersionInfo:
    message: str | None = None
    new_version: str | None = None


@dataclass(frozen=True)
class AppDataResponse(BaseKorailResponse):
    disability_certification_msg: str | None = None
    for_seat_intg: str | None = None
    airport_bus_msg: str | None = None
    railplus_cardinfo: str | None = None
    version: AppVersionInfo | None = None


@dataclass(frozen=True)
class NoticeResponse(BaseKorailResponse):
    board_id: str | None = None
    post_sequence: str | None = None
    post_title: str | None = None
```

- [ ] **Step 5: Add strict parser helpers**

Update the model imports in `src/korail_mobile_api/parsers.py`, then add:

```python
def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(f"KORAIL cache field {key} must be a string or null")
    return value


def parse_app_data_response(response: BaseKorailResponse) -> AppDataResponse:
    raw = response.raw
    version_raw = raw.get("version")
    if version_raw is not None and not isinstance(version_raw, dict):
        raise KorailProtocolError("KORAIL cache field version must be an object or null")
    version = None
    if isinstance(version_raw, dict):
        version = AppVersionInfo(
            message=_optional_string(version_raw, "AMESSAGE"),
            new_version=_optional_string(version_raw, "NEWDVERSION"),
        )
    return AppDataResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        disability_certification_msg=_optional_string(raw, "disability_certification_msg"),
        for_seat_intg=_optional_string(raw, "forSeatIntg"),
        airport_bus_msg=_optional_string(raw, "airportBusMsg"),
        railplus_cardinfo=_optional_string(raw, "railplus_cardinfo"),
        version=version,
    )


def parse_notice_response(response: BaseKorailResponse) -> NoticeResponse:
    raw = response.raw
    return NoticeResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        board_id=_optional_string(raw, "bbrdId"),
        post_sequence=_optional_string(raw, "ptwtSqno"),
        post_title=_optional_string(raw, "ptwtTtl"),
    )
```

- [ ] **Step 6: Run the focused parser/model tests**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_models.py -q
```

Expected: all new parser/model tests pass.

- [ ] **Step 7: Review the Task 1 diff without staging or committing**

Run:

```bash
git diff -- src/korail_mobile_api/models.py src/korail_mobile_api/parsers.py tests/test_models.py
git status --short tests/fixtures/cache_app_data_success.json tests/fixtures/cache_notice_success.json tests/test_cache_read_apis.py
```

Expected: only Task 1 additions are visible; leave them unstaged and uncommitted.

---

### Task 2: Timestamp Query And Exact Route Policy

**Files:**

- Modify: `src/korail_mobile_api/payloads.py`
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `tests/test_cache_read_apis.py`
- Modify: `tests/test_http.py`

**Interfaces:**

- Consumes: Python `time.time()` and existing `assert_read_only_route()`.
- Produces: `build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]` and a 12-route KORAIL registry.

- [ ] **Step 1: Add failing timestamp and route tests**

Add to `tests/test_cache_read_apis.py`:

```python
@pytest.mark.parametrize("value", [-1, True, 1.5, "1000"])
def test_cache_query_rejects_invalid_timestamp_before_io(value):
    from korail_mobile_api.payloads import build_cache_query

    with pytest.raises(ValueError):
        build_cache_query(value)


def test_cache_query_uses_explicit_timestamp():
    from korail_mobile_api.payloads import build_cache_query

    assert build_cache_query(1234567890) == {"timeStamp": "1234567890"}


def test_cache_query_uses_current_epoch_milliseconds(monkeypatch):
    from korail_mobile_api import payloads

    monkeypatch.setattr(payloads.time, "time", lambda: 1234.567)
    assert payloads.build_cache_query() == {"timeStamp": "1234567"}
```

Add the two exact GET paths to the accepted-route parameterization in `tests/test_http.py`, and add neighboring path/wrong-method rejection assertions:

```python
@pytest.mark.parametrize(
    "path",
    [
        "/file/CACHE/prdMobilePlusMain.cache.bak",
        "/file/CACHE/prdMobilePlusNotice.cache/extra",
    ],
)
def test_neighboring_cache_routes_are_rejected(path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("GET", path)


@pytest.mark.parametrize(
    "path",
    [
        "/file/CACHE/prdMobilePlusMain.cache",
        "/file/CACHE/prdMobilePlusNotice.cache",
    ],
)
def test_cache_routes_reject_post(path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", path)
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_http.py -q
```

Expected: failures because `build_cache_query()` and the two routes are missing.

- [ ] **Step 3: Implement exact timestamp construction**

Add `import time` to `src/korail_mobile_api/payloads.py`, then add:

```python
def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    if timestamp_ms is not None and (type(timestamp_ms) is not int or timestamp_ms < 0):
        raise ValueError("timestamp_ms must be a non-negative integer or None")
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}
```

- [ ] **Step 4: Add only the two exact routes**

Add to `KORAIL_READ_ONLY_ROUTES` in `src/korail_mobile_api/safety.py`:

```python
("GET", "/file/CACHE/prdMobilePlusMain.cache"),
("GET", "/file/CACHE/prdMobilePlusNotice.cache"),
```

Do not change `DYNAPATH_ALLOWLIST_PATHS`.

- [ ] **Step 5: Run the focused timestamp and safety tests**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_http.py tests/test_dynapath.py -q
```

Expected: all pass, including unchanged DynaPath tests.

- [ ] **Step 6: Review the Task 2 diff without staging or committing**

Run:

```bash
git diff -- src/korail_mobile_api/payloads.py src/korail_mobile_api/safety.py tests/test_cache_read_apis.py tests/test_http.py
```

Expected: timestamp validation plus exactly two allowlisted routes; no other path or DynaPath change.

---

### Task 3: Client Methods, Public Types, And Transport Contracts

**Files:**

- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Modify: `tests/test_cache_read_apis.py`
- Modify: `tests/test_public_contract.py`

**Interfaces:**

- Consumes: `build_cache_query()`, `parse_app_data_response()`, `parse_notice_response()`, and `KorailHttpClient.get_json()`.
- Produces: `KorailClient.get_app_data(timestamp_ms=None) -> AppDataResponse` and `KorailClient.get_notice(timestamp_ms=None) -> NoticeResponse`.

- [ ] **Step 1: Add failing exact-request tests**

Add to `tests/test_cache_read_apis.py`:

```python
from urllib.parse import parse_qs

import httpx

from korail_mobile_api import KorailClient


@pytest.mark.parametrize(
    ("method_name", "path", "fixture_name"),
    [
        ("get_app_data", "/file/CACHE/prdMobilePlusMain.cache", "cache_app_data_success.json"),
        ("get_notice", "/file/CACHE/prdMobilePlusNotice.cache", "cache_notice_success.json"),
    ],
)
def test_cache_client_methods_use_exact_account_neutral_get(
    method_name, path, fixture_name, load_json_fixture
):
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=load_json_fixture(fixture_name))

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        result = getattr(client, method_name)(1234567890)
    finally:
        client.close()
    assert seen[0].method == "GET"
    assert seen[0].url.path == path
    assert parse_qs(seen[0].url.query.decode()) == {"timeStamp": ["1234567890"]}
    assert "x-dynapath-m-token" not in seen[0].headers
    assert result.h_msg_cd == "S000"


def test_cache_client_propagates_typed_application_failure():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"h_msg_cd": "E001", "h_msg_txt": "failed", "strResult": "FAIL"})

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAppError):
            client.get_notice(1)
    finally:
        client.close()
```

Update `tests/test_public_contract.py` so the expected public set also contains `get_app_data` and `get_notice`, then add:

```python
def test_cache_method_signatures_and_types_are_public():
    assert list(inspect.signature(KorailClient.get_app_data).parameters) == ["self", "timestamp_ms"]
    assert list(inspect.signature(KorailClient.get_notice).parameters) == ["self", "timestamp_ms"]
    for name in ("AppDataResponse", "AppVersionInfo", "NoticeResponse"):
        assert getattr(korail_mobile_api, name)
```

- [ ] **Step 2: Run focused tests and confirm the methods are absent**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_public_contract.py -q
```

Expected: failures because the client methods and public exports do not exist.

- [ ] **Step 3: Implement the two client methods**

Update imports in `src/korail_mobile_api/client.py`, then add after `get_common_code()`:

```python
def get_app_data(self, timestamp_ms: int | None = None) -> AppDataResponse:
    return self._run_read(
        lambda: parse_app_data_response(
            self.http.get_json(
                "/file/CACHE/prdMobilePlusMain.cache",
                build_cache_query(timestamp_ms),
            )
        )
    )


def get_notice(self, timestamp_ms: int | None = None) -> NoticeResponse:
    return self._run_read(
        lambda: parse_notice_response(
            self.http.get_json(
                "/file/CACHE/prdMobilePlusNotice.cache",
                build_cache_query(timestamp_ms),
            )
        )
    )
```

Import `AppDataResponse`, `NoticeResponse`, `parse_app_data_response`, `parse_notice_response`, and `build_cache_query` from their focused modules.

- [ ] **Step 4: Export the completed model contract**

Add `AppDataResponse`, `AppVersionInfo`, and `NoticeResponse` to the imports and `__all__` list in `src/korail_mobile_api/__init__.py`. Do not remove or rename existing exports.

- [ ] **Step 5: Run client, public-contract, HTTP, and session suites**

Run:

```bash
python3 -m pytest tests/test_cache_read_apis.py tests/test_public_contract.py tests/test_http.py tests/test_session.py -q
```

Expected: all pass with the expanded public method set.

- [ ] **Step 6: Review the Task 3 diff without staging or committing**

Run:

```bash
git diff -- src/korail_mobile_api/client.py src/korail_mobile_api/__init__.py tests/test_cache_read_apis.py tests/test_public_contract.py
```

Expected: exactly two account-neutral methods and three new exports; no login, ticket, or mutation changes.

---

### Task 4: Bounded Live Flow And User Documentation

**Files:**

- Modify: `src/korail_mobile_api/live.py`
- Modify: `tests/test_live.py`
- Modify: `README.md`

**Interfaces:**

- Consumes: the two new client methods and the existing live environment gate.
- Produces: live keys `appDataLoaded: bool` and `noticeLoaded: bool`, with both requests executed before login.

- [ ] **Step 1: Extend the failing fake-client live contract**

Update the fake/mock setup in `tests/test_live.py` so `get_app_data()` and `get_notice()` return typed responses, then assert:

```python
assert result["appDataLoaded"] is True
assert result["noticeLoaded"] is True
assert list(result).index("appDataLoaded") < list(result).index("loggedIn")
assert "raw" not in result
assert "title" not in repr(result).lower()
client.get_app_data.assert_called_once_with()
client.get_notice.assert_called_once_with()
```

Also use a side-effect list to assert the two cache calls occur before `login`.

- [ ] **Step 2: Run the focused live-helper test and confirm failure**

Run:

```bash
python3 -m pytest tests/test_live.py -q
```

Expected: failure because the cache calls and result keys are absent.

- [ ] **Step 3: Extend the live helper with bounded pre-login reads**

In `run_live_smoke_from_env()` immediately after client construction and before `client.login(...)`, add:

```python
app_data = client.get_app_data()
notice = client.get_notice()
```

Add these entries before `loggedIn` in the returned mapping:

```python
"appDataLoaded": bool(app_data.raw),
"noticeLoaded": bool(notice.raw),
```

Do not return any known field value or `raw` object.

- [ ] **Step 4: Document the expanded safe surface**

Update `README.md` to list `get_app_data()` and `get_notice()` as account-neutral cache reads, state their exact paths, and state that live output contains only booleans/counts. Keep all existing credential, advertising-ID, DynaPath, and mutation exclusions intact.

- [ ] **Step 5: Run live-helper, README, and redaction tests**

Run:

```bash
python3 -m pytest tests/test_live.py tests/test_readme.py tests/test_redaction_safety.py -q
```

Expected: all pass without running the opted-in service test.

- [ ] **Step 6: Review the Task 4 diff without staging or committing**

Run:

```bash
git diff -- src/korail_mobile_api/live.py tests/test_live.py README.md
```

Expected: two pre-login reads, two boolean keys, and read-only documentation only.

---

### Task 5: Full Verification, Independent Review, And Progress Handoff

**Files:**

- Modify: `docs/IMPLEMENTATION_PROGRESS.md`
- Verify: all files named in Tasks 1-4.

**Interfaces:**

- Consumes: the completed expansion and the existing package/live tooling.
- Produces: verified build artifacts, isolated import evidence, bounded live evidence, and an updated uncommitted handoff.

- [ ] **Step 1: Run the complete offline suite**

Run:

```bash
python3 -m pytest -q
```

Expected: exit 0; only `tests/test_live_service.py` is skipped without explicit live opt-in.

- [ ] **Step 2: Build wheel and sdist**

Run:

```bash
python3 -m build
```

Expected: exit 0 with a newly built wheel and source archive under `dist/`.

- [ ] **Step 3: Verify an isolated wheel import**

Run:

```bash
VERIFY_DIR="$(mktemp -d)"
python3 -m venv "$VERIFY_DIR/venv"
"$VERIFY_DIR/venv/bin/pip" install --quiet dist/korail_mobile_api-0.1.0-py3-none-any.whl
"$VERIFY_DIR/venv/bin/python" -c "from korail_mobile_api import AppDataResponse, AppVersionInfo, KorailClient, NoticeResponse; print(KorailClient.__name__)"
rm -rf "$VERIFY_DIR"
```

Expected output: `KorailClient`.

- [ ] **Step 4: Confirm the safety boundary statically**

Run:

```bash
python3 - <<'PY'
from korail_mobile_api.safety import KORAIL_READ_ONLY_ROUTES
assert len(KORAIL_READ_ONLY_ROUTES) == 12
assert ("GET", "/file/CACHE/prdMobilePlusMain.cache") in KORAIL_READ_ONLY_ROUTES
assert ("GET", "/file/CACHE/prdMobilePlusNotice.cache") in KORAIL_READ_ONLY_ROUTES
print("12 read/login routes")
PY
rg -n "TicketReservation|NonMemTicket|prcFare|reservation|payment|refund|check-in" src/korail_mobile_api/client.py src/korail_mobile_api/live.py
```

Expected: route assertion prints `12 read/login routes`; the search finds no newly callable mutation path in the client/live facade. Existing compatibility constants elsewhere are not callable routes.

- [ ] **Step 5: Request independent read-only review**

Provide the approved design, this plan, `git diff`, and fresh test output to a reviewer that must not edit files. Require review of spec coverage, exact route/payload behavior, typed errors, repr/redaction, DynaPath non-regression, live output, and forbidden domains. If findings are valid, the same KORAIL implementation agent fixes them and reruns the affected and full suites.

- [ ] **Step 6: Run bounded opted-in live verification**

Load the existing ignored `.local-live-smoke.env` without printing it, then run:

```bash
pytest -m live tests/test_live_service.py -q
```

Expected: pass with the two new cache reads returning only `appDataLoaded` and `noticeLoaded` metadata through the helper. A server rejection remains a typed failure; do not weaken it into an empty success. If live credentials/configuration are unavailable, report the live gate as not run rather than claiming success.

- [ ] **Step 7: Update the progress document from actual evidence**

Update `docs/IMPLEMENTATION_PROGRESS.md` with the actual offline count, build/import result, route count 12, bounded live result or explicit not-run reason, the two new public methods, DynaPath non-regression, and remaining evidenced read-only candidates. Do not include credentials, device identifiers, raw cache values, notice titles, cookies, or tokens.

- [ ] **Step 8: Perform the final uncommitted-tree review**

Run:

```bash
git diff --check
git status --short
git diff --stat
```

Expected: no whitespace errors, all intentional pre-existing and new changes remain visible, nothing is staged, and no commit has been created.

## Final Verification Checklist

- [ ] `python3 -m pytest -q` passes with only the explicitly disabled live test skipped.
- [ ] Wheel and sdist build successfully.
- [ ] The built wheel imports `AppDataResponse`, `AppVersionInfo`, `KorailClient`, and `NoticeResponse` in isolation.
- [ ] The exact HTTP route count is 12 and no mutation route is callable.
- [ ] Both cache methods send only `timeStamp` and use no session/member field or DynaPath header.
- [ ] Malformed known fields and application failures remain typed failures.
- [ ] Raw cache data is caller-accessible but absent from repr, logs, exceptions, and live output.
- [ ] Existing stateful DynaPath tests pass unchanged.
- [ ] Independent read-only review has no unresolved finding.
- [ ] Bounded live verification passes or is explicitly reported as not run.
- [ ] `docs/IMPLEMENTATION_PROGRESS.md` reflects actual evidence.
- [ ] No file is staged or committed.
