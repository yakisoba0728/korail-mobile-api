# KORAIL Public API Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every currently exposed KORAIL read-only client method match the observed app and live-server contracts without adding new endpoint methods.

**Architecture:** Keep `KorailClient` as the facade, but route every request through an explicit read-only policy and typed response classifier. Keep login and DynaPath state per client instance, move endpoint form construction and response normalization into focused helpers, and preserve existing method signatures and `raw` access.

**Tech Stack:** Python 3.11+, `httpx>=0.27,<1`, `cryptography>=42,<47`, frozen dataclasses, `pytest>=8,<10`, setuptools.

## Global Constraints

- Work from the current working tree; inspect and preserve all pre-existing uncommitted KORAIL changes.
- Do not revert files changed by another worker. Stage and commit only the paths named by the current task.
- Keep Python support at `>=3.11` and add no runtime dependency.
- Do not add reservation, payment, cancellation, refund, check-in, member mutation, or other state-changing endpoint methods.
- Keep all existing public method names and ordinary calling forms.
- Keep `raw` result access, but prevent raw data and credentials from appearing in logs or object representations.
- Default tests must be offline and must use `httpx.MockTransport`.
- Live credentials and device identity values come only from ignored environment files.
- DynaPath may run only on its documented URL allowlist; the HTTP safety allowlist remains narrower and read-only.
- A valid application failure must raise a typed exception, never an empty successful result.
- Follow TDD: add one focused failing test, confirm the expected failure, implement the minimum behavior, rerun the focused test, then run the affected suite.

---

## File Structure

Files created by this plan:

- `src/korail_mobile_api/payloads.py`: exact request builders for train search, actual schedule, and ticket list.
- `src/korail_mobile_api/parsers.py`: station-catalog and nested train-response normalization.
- `tests/test_public_contract.py`: final public surface and safety invariants.
- `tests/test_live_service.py`: explicitly opted-in live read-only gate.

Existing files modified by this plan:

- `src/korail_mobile_api/__init__.py`: export the completed exception and model contract.
- `src/korail_mobile_api/client.py`: orchestrate helpers without embedding protocol details.
- `src/korail_mobile_api/config.py`: hold caller-provided advertising/device configuration.
- `src/korail_mobile_api/crypto.py`: reproduce Android Base64 flags exactly.
- `src/korail_mobile_api/dynapath.py`: validate runtime settings and retain request-delta state.
- `src/korail_mobile_api/errors.py`: expose transport, protocol, app, auth, expiry, and DynaPath errors.
- `src/korail_mobile_api/http.py`: enforce routes and classify HTTP/application responses.
- `src/korail_mobile_api/live.py`: construct live configuration without probe defaults and exercise safe reads.
- `src/korail_mobile_api/models.py`: hide sensitive fields from `repr` and preserve station names.
- `src/korail_mobile_api/redaction.py`: recursively redact mappings, sequences, dataclasses, text, and URLs.
- `src/korail_mobile_api/safety.py`: define the exact read-only route registry.
- `src/korail_mobile_api/session.py`: make login a commit/rollback transaction with pending continuation state.
- `tests/fixtures/schedule_view_success.json`: use the observed nested train-list shape.
- `tests/fixtures/station_data.json`: contain both stations required by resolver tests.
- `tests/test_client_read_apis.py`, `tests/test_crypto.py`, `tests/test_dynapath.py`, `tests/test_http.py`, `tests/test_live.py`, `tests/test_models.py`, `tests/test_redaction_safety.py`, `tests/test_session.py`: lock each corrected contract.
- `README.md`: document explicit device configuration and the safe live gate.

---

### Task 1: Typed Errors, Recursive Redaction, And Safe Model Representations

**Files:**
- Modify: `src/korail_mobile_api/errors.py`
- Modify: `src/korail_mobile_api/redaction.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Test: `tests/test_models.py`
- Test: `tests/test_redaction_safety.py`

**Interfaces:**
- Consumes: existing `KorailApiError`, dataclass models, and `redact_mapping()`.
- Produces: `KorailSessionExpiredError`, `KorailDynaPathError`, `redact_value(value, *, key=None) -> Any`, `redact_url(value: str) -> str`, and sensitive dataclass fields excluded from `repr`.

- [ ] **Step 1: Add failing hierarchy, recursive-redaction, URL, and repr tests**

Add these focused tests:

```python
from korail_mobile_api.errors import (
    KorailApiError,
    KorailAuthError,
    KorailDynaPathError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import BaseKorailResponse, KorailSession
from korail_mobile_api.redaction import redact_mapping, redact_url


def test_completed_error_hierarchy_is_public():
    assert issubclass(KorailSessionExpiredError, KorailAuthError)
    assert issubclass(KorailDynaPathError, KorailApiError)


def test_redaction_is_recursive_case_insensitive_and_url_safe():
    value = {
        "outer": [{"TXTPWD": "secret", "url": "https://host/path?JSESSIONID=abc&safe=1"}],
    }
    redacted = redact_mapping(value)
    assert redacted["outer"][0]["TXTPWD"] == "[REDACTED]"
    assert "abc" not in redacted["outer"][0]["url"]
    assert "safe=1" in redacted["outer"][0]["url"]
    assert "token-value" not in redact_url("https://host/path?x-dynapath-m-token=token-value")


def test_sensitive_model_fields_do_not_appear_in_repr():
    session = KorailSession(jsessionid="cookie-secret", member_no="member-secret", raw={"txtPwd": "pw"})
    response = BaseKorailResponse(raw={"JSESSIONID": "cookie-secret"})
    assert "cookie-secret" not in repr(session)
    assert "member-secret" not in repr(session)
    assert "cookie-secret" not in repr(response)
```

- [ ] **Step 2: Run the focused tests and confirm the contract is missing**

Run: `pytest tests/test_models.py tests/test_redaction_safety.py -q`

Expected: FAIL because the new exception classes and recursive/URL redaction are not implemented and dataclass `repr` still includes sensitive fields.

- [ ] **Step 3: Implement recursive redaction**

Replace the redaction implementation with these public helpers:

```python
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


SENSITIVE_KEYS = frozenset(
    key.casefold()
    for key in {
        "txtMemberNo",
        "txtPwd",
        "password",
        "JSESSIONID",
        "Cookie",
        "Set-Cookie",
        "pnrNo",
        "hidPnrNo",
        "tkRetPwd",
        "x-dynapath-m-token",
    }
)
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
SESSION_RE = re.compile(r"(?i)(JSESSIONID=)[^&;\s]+")


def redact_text(value: str) -> str:
    return SESSION_RE.sub(r"\1[REDACTED]", CARD_RE.sub("[REDACTED_CARD]", value))


def redact_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return redact_text(value)
    query = [
        (key, "[REDACTED]" if key.casefold() in SENSITIVE_KEYS else redact_text(item))
        for key, item in parse_qsl(parsed.query, keep_blank_values=True)
    ]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


def redact_value(value: Any, *, key: str | None = None) -> Any:
    if key is not None and key.casefold() in SENSITIVE_KEYS:
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {item_key: redact_value(item, key=str(item_key)) for item_key, item in value.items()}
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: redact_value(getattr(value, field.name), key=field.name) for field in fields(value)}
    if isinstance(value, str):
        return redact_url(value)
    return value


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    return {key: redact_value(value, key=str(key)) for key, value in data.items()}
```

- [ ] **Step 4: Implement the completed error hierarchy and safe messages**

Keep the existing base classes and add/replace these definitions in `errors.py`:

```python
from .redaction import redact_text


class KorailSessionExpiredError(KorailAuthError):
    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(f"{code or 'P058'}: {redact_text(message or 'KORAIL session expired')}")


class KorailDynaPathError(KorailApiError):
    def __init__(self, message: str | None = None, *, raw: object | None = None) -> None:
        self.raw = raw
        super().__init__(redact_text(message or "KORAIL DynaPath request rejected"))


class KorailAuthContinuationRequired(KorailAuthError):
    def __init__(self, redirect_url: str, post_data: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.post_data = post_data
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")


class KorailAppError(KorailApiError):
    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip())
```

Export `KorailAppError`, `KorailTransportError`, `KorailSessionExpiredError`, and `KorailDynaPathError` from `__init__.py` without removing existing exports.

- [ ] **Step 5: Hide sensitive/raw dataclass fields from repr**

Change the relevant model fields as follows:

```python
@dataclass(frozen=True)
class KorailSession:
    jsessionid: str | None = field(default=None, repr=False)
    member_no: str | None = field(default=None, repr=False)
    member_card_no: str | None = field(default=None, repr=False)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class BaseKorailResponse:
    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
```

Use these exact remaining fields without changing equality or caller access:

```python
class TrainSummary:
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


class TrainSearchResult:
    raw: dict[str, Any] = field(default_factory=dict, repr=False)
```

- [ ] **Step 6: Run focused and model suites**

Run: `pytest tests/test_models.py tests/test_redaction_safety.py -q`

Expected: PASS.

- [ ] **Step 7: Commit only Task 1 files**

```bash
git add src/korail_mobile_api/errors.py src/korail_mobile_api/redaction.py src/korail_mobile_api/models.py src/korail_mobile_api/__init__.py tests/test_models.py tests/test_redaction_safety.py
git commit -m "fix: harden korail errors and redaction"
```

---

### Task 2: Explicit Read-Only Routes And Response Classification

**Files:**
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/http.py`
- Test: `tests/test_http.py`

**Interfaces:**
- Consumes: Task 1 exception classes and `DYNAPATH_ALLOWLIST_PATHS`.
- Produces: `KORAIL_READ_ONLY_ROUTES`, `assert_read_only_route(method: str, path: str) -> None`, P058 classification, and DynaPath-aware HTTP 403 handling.

- [ ] **Step 1: Add failing route and classifier tests**

```python
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/file/CACHE/MobileService.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("GET", "/classes/com.korail.mobile.common.stationinfo"),
        ("GET", "/classes/com.korail.mobile.common.stationdata"),
        ("GET", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        ("POST", "/classes/com.korail.mobile.research.actualTrainSchedule.do"),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketList"),
    ],
)
def test_read_only_route_registry_accepts_current_public_requests(method, path):
    assert_read_only_route(method, path)


@pytest.mark.parametrize(
    "path",
    [
        "/classes/com.korail.mobile.login.mbSced.do",
        "/classes/com.korail.mobile.certification.TicketReservation",
        "https://evil.example/classes/com.korail.mobile.common.code.do",
    ],
)
def test_route_registry_rejects_mutation_and_absolute_paths_before_io(path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", path)


def test_p058_is_always_session_expired_even_when_failure_opt_out_is_requested():
    with pytest.raises(KorailSessionExpiredError):
        parse_base_response(
            {"h_msg_cd": "P058", "h_msg_txt": "logged out", "strResult": "FAIL"},
            raise_on_fail=False,
        )


def test_allowlisted_403_is_classified_as_dynapath_error(load_json_fixture):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json=load_json_fixture("dynapath_403.json"),
            headers={"DynaPath-Result": "-1"},
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailDynaPathError, match="macro protection"):
        client.post_form("/classes/com.korail.mobile.login.Login")
```

Update existing generic `/classes/example.do` HTTP tests to use `/classes/com.korail.mobile.common.code.do` or another registered path.

- [ ] **Step 2: Run the focused HTTP tests**

Run: `pytest tests/test_http.py -q`

Expected: FAIL because safety is still substring-based and P058/403 have no dedicated classification.

- [ ] **Step 3: Replace the safety blocklist with an exact registry**

```python
from urllib.parse import urlsplit

from .errors import KorailProtocolError


KORAIL_READ_ONLY_ROUTES = frozenset(
    {
        ("GET", "/file/CACHE/MobileService.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("GET", "/classes/com.korail.mobile.common.stationinfo"),
        ("GET", "/classes/com.korail.mobile.common.stationdata"),
        ("GET", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        ("POST", "/classes/com.korail.mobile.research.actualTrainSchedule.do"),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketList"),
    }
)


def assert_read_only_route(method: str, path: str) -> None:
    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise KorailProtocolError(f"KORAIL request target is not a registered relative path: {parsed.path}")
    route = (method.upper(), parsed.path)
    if route not in KORAIL_READ_ONLY_ROUTES:
        raise KorailProtocolError(f"KORAIL request route is not allowed: {route[0]} {route[1]}")
```

Keep `EXCLUDED_API_DOMAINS` as a compatibility export, but do not use it as the enforcement mechanism.

- [ ] **Step 4: Classify P058, DynaPath 403, and transport errors**

Update `parse_base_response` and add a status helper:

```python
def parse_base_response(data: Any, *, raise_on_fail: bool = True) -> BaseKorailResponse:
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    response = BaseKorailResponse.from_raw(data)
    if response.h_msg_cd == "P058":
        raise KorailSessionExpiredError(response.h_msg_cd, response.h_msg_txt, raw=data)
    if raise_on_fail and response.str_result == "FAIL":
        raise KorailAppError(response.h_msg_cd, response.h_msg_txt, raw=data)
    return response


def _raise_for_status(response: httpx.Response, *, path: str) -> None:
    dynapath_result = response.headers.get("DynaPath-Result")
    try:
        dynapath_rejected = dynapath_result is not None and int(dynapath_result) < 0
    except ValueError:
        dynapath_rejected = False
    if response.status_code == 403 and path in DYNAPATH_ALLOWLIST_PATHS and dynapath_rejected:
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        message = payload.get("message") if isinstance(payload, dict) else None
        raise KorailDynaPathError(str(message or "KORAIL DynaPath request rejected"), raw=payload)
    if response.is_error:
        raise KorailTransportError(
            f"KORAIL HTTP {response.status_code} for {response.request.method} {response.request.url.path}"
        )
```

Call `assert_read_only_route("POST", path)` or `assert_read_only_route("GET", path)` before any header generation or network I/O. Replace `response.raise_for_status()` with `_raise_for_status(response, path=path)`.

When `require_envelope=False`, call `parse_base_response` if all three envelope keys are present; otherwise return the raw object wrapper. This preserves raw station payloads while still classifying a real failure envelope.

- [ ] **Step 5: Run HTTP and safety tests**

Run: `pytest tests/test_http.py tests/test_redaction_safety.py -q`

Expected: PASS, and every rejected route leaves the mock handler uncalled.

- [ ] **Step 6: Commit only Task 2 files**

```bash
git add src/korail_mobile_api/safety.py src/korail_mobile_api/http.py tests/test_http.py
git commit -m "fix: enforce korail read only transport"
```

---

### Task 3: Android Crypto Parity And Transactional Login

**Files:**
- Modify: `src/korail_mobile_api/crypto.py`
- Modify: `src/korail_mobile_api/session.py`
- Test: `tests/test_crypto.py`
- Test: `tests/test_session.py`

**Interfaces:**
- Consumes: Task 1 error classes and Task 2 classified HTTP client.
- Produces: Android `Base64.DEFAULT` parity for AES/Sid, `KorailSessionClient.pending`, and all-or-nothing login state.

- [ ] **Step 1: Add failing crypto parity tests**

```python
def test_aes_login_transform_preserves_android_default_newline_before_outer_base64():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="Y")
    assert transform_login_password("pw123", info) == "ZkpkU2JycXlJSzYyeGNxcSsxdUNmUT09Cg=="


def test_sid_uses_android_base64_default():
    assert generate_sid(epoch_ms=1712345678901) == "rIPj+3cmqQgizSSxkiLJuA==\n"
```

- [ ] **Step 2: Add failing login rollback and pending-state tests**

```python
def test_failed_relogin_clears_old_session_and_cookies(load_json_fixture):
    client = make_success_then_failure_client(load_json_fixture)
    client.login("member1", "pw123")
    with pytest.raises(KorailAuthError):
        client.login("member2", "bad")
    assert client.session.current is None
    assert client.session.pending is None
    assert "JSESSIONID" not in client.http.cookies


def test_continuation_keeps_only_pending_state_and_new_cookie():
    client = make_continuation_client()
    with pytest.raises(KorailAuthContinuationRequired) as exc_info:
        client.login("user@example.com", "pw123")
    assert client.session.current is None
    assert client.session.pending is exc_info.value
    assert client.http.cookies.get("JSESSIONID") == "session-cont"
    client.clear_session()
    assert client.session.pending is None
    assert "JSESSIONID" not in client.http.cookies
```

Add these deterministic helpers:

```python
def make_success_then_failure_client(load_json_fixture):
    login_attempt = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal login_attempt
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            login_attempt += 1
            if login_attempt == 1:
                return httpx.Response(
                    200,
                    json=load_json_fixture("login_success.json"),
                    headers={"Set-Cookie": "JSESSIONID=first-session; Path=/; HttpOnly"},
                )
            return httpx.Response(
                200,
                json={"h_msg_cd": "AUTH_FAIL", "h_msg_txt": "bad credentials", "strResult": "FAIL"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))


def make_continuation_client():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == SERVICE_CHECK_PATH:
            return service_check_response()
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(
                200,
                json={"h_msg_cd": "API.I00000", "h_msg_txt": "Success", "strResult": "SUCC", "pwdAESCphd": "N"},
            )
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "S201",
                    "h_msg_txt": "additional auth",
                    "strResult": "SUCC",
                    "strRedirectUrl": "/classes/com.korail.mobile.onepass.login.do",
                },
                headers={"Set-Cookie": "JSESSIONID=session-cont; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
```

- [ ] **Step 3: Run focused crypto and session tests**

Run: `pytest tests/test_crypto.py tests/test_session.py -q`

Expected: FAIL because AES/Sid use no-wrap Base64 and KORAIL login does not clear old state or expose pending continuation state.

- [ ] **Step 4: Correct the two Base64 flag boundaries**

Replace the AES and Sid return paths:

```python
def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    if info.pwd_aes_cphd == "Y":
        key = _validate_login_crypto_key(info)
        iv = key[:16]
        try:
            encrypted = _android_base64_default(_aes_cbc_pkcs7_encrypt(password.encode("utf-8"), key, iv))
        except ValueError as exc:
            raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV") from exc
        return _base64_no_wrap(encrypted.encode("utf-8"))
    return _base64_no_wrap(password.encode("utf-8"))


def generate_sid(*, epoch_ms: int | None = None) -> str:
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    encrypted = _aes_cbc_pkcs7_encrypt(f"AD{timestamp}".encode("utf-8"), SID_KEY, SID_KEY)
    return _android_base64_default(encrypted)
```

- [ ] **Step 5: Make login commit or roll back atomically**

Initialize `pending` and wrap the existing login body:

```python
class KorailSessionClient:
    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None
        self.pending: KorailAuthContinuationRequired | None = None

    def login(
        self,
        member_no: str,
        password: str,
        *,
        input_flag: str | None = None,
        check_valid_pw: str = "Y",
        cust_id: str | None = "",
        etr_path: str | None = "",
    ) -> KorailSession:
        self.clear_session()
        try:
            return self._login(
                member_no,
                password,
                input_flag=input_flag,
                check_valid_pw=check_valid_pw,
                cust_id=cust_id,
                etr_path=etr_path,
            )
        except KorailAuthContinuationRequired as exc:
            self.pending = exc
            raise
        except Exception:
            self.clear_session()
            raise

    def clear_session(self) -> None:
        self.http.cookies.clear()
        self.current = None
        self.pending = None
```

Add the complete private login body:

```python
def _login(
    self,
    member_no: str,
    password: str,
    *,
    input_flag: str | None,
    check_valid_pw: str,
    cust_id: str | None,
    etr_path: str | None,
) -> KorailSession:
    self.check_service()
    crypto_info = self.get_login_crypto_info()
    transformed = transform_login_password(password, crypto_info)
    resolved_input_flag = input_flag or infer_login_input_flag(member_no)
    form = {
        "txtMemberNo": member_no,
        "txtPwd": transformed,
        "txtInputFlg": resolved_input_flag,
        "checkValidPw": check_valid_pw,
        "idx": crypto_info.idx or None,
        "custId": cust_id,
        "etrPath": etr_path,
    }
    try:
        response = self.http.post_form(
            "/classes/com.korail.mobile.login.Login",
            {name: value for name, value in form.items() if value is not None},
        )
    except KorailAppError as exc:
        raise KorailAuthError(exc.message or "KORAIL login failed") from exc
    if not is_login_success_code(response.h_msg_cd):
        redirect_url = response.raw.get("strRedirectUrl")
        if redirect_url:
            raise KorailAuthContinuationRequired(
                str(redirect_url),
                build_login_authentication_post_data(
                    login_id=member_no,
                    input_flag=resolved_input_flag,
                    response_raw=response.raw,
                    cust_id=cust_id,
                ),
                raw=response.raw,
            )
        raise KorailAuthError(
            f"{response.h_msg_cd or 'UNKNOWN'}: "
            f"{response.h_msg_txt or 'KORAIL login did not complete'}"
        )
    jsessionid = self.http.cookies.get("JSESSIONID")
    if not jsessionid:
        raise KorailAuthError("KORAIL login did not return a usable session")
    member_card_no = str(
        response.raw.get("mbCrdNo") or response.raw.get("strMbCrdNo") or ""
    ) or None
    self.current = KorailSession(
        jsessionid=jsessionid,
        member_no=member_no,
        member_card_no=member_card_no,
        raw=response.raw,
    )
    return self.current
```

- [ ] **Step 6: Update existing expected encrypted values and run tests**

Change the AES login-body expectation in `tests/test_session.py` to:

```python
assert "txtPwd=ZkpkU2JycXlJSzYyeGNxcSsxdUNmUT09Cg%3D%3D" in captured["body"]
```

Run: `pytest tests/test_crypto.py tests/test_session.py -q`

Expected: PASS.

- [ ] **Step 7: Commit only Task 3 files**

```bash
git add src/korail_mobile_api/crypto.py src/korail_mobile_api/session.py tests/test_crypto.py tests/test_session.py
git commit -m "fix: make korail login transactional"
```

---

### Task 4: Stateful DynaPath Wiring And Explicit Live Device Settings

**Files:**
- Modify: `src/korail_mobile_api/dynapath.py`
- Modify: `src/korail_mobile_api/http.py`
- Modify: `src/korail_mobile_api/live.py`
- Modify: `src/korail_mobile_api/config.py`
- Test: `tests/test_dynapath.py`
- Test: `tests/test_http.py`
- Test: `tests/test_live.py`

**Interfaces:**
- Consumes: existing `DynapathTokenGenerator` and caller-provided `DynapathTokenSettings`.
- Produces: validated settings, one generator per `KorailHttpClient`, exact-path allowlisting, and `build_config_from_env()` with no probe defaults.

- [ ] **Step 1: Add failing configuration and multi-request HTTP tests**

```python
def test_enabled_dynapath_requires_exactly_one_token_source():
    with pytest.raises(ValueError, match="exactly one"):
        DynapathConfig(enabled=True)
    with pytest.raises(ValueError, match="exactly one"):
        DynapathConfig(
            enabled=True,
            token_provider=lambda _context: "token",
            token_settings=make_settings(),
        )


def test_http_reuses_one_stateful_generator_across_requests():
    timestamps = iter([1712345600100, 1712345600250])
    random_texts = iter(["A1B2", "C3D4"])
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.headers[DYNAPATH_HEADER_NAME])
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    settings = replace(make_settings(), app_start_ts="1712345600000")
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_settings=settings,
            timestamp_ms_provider=lambda: next(timestamps),
            random_text_provider=lambda: next(random_texts),
        )
    )
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form("/classes/com.korail.mobile.login.Login")
    client.post_form("/classes/com.korail.mobile.login.Login")
    assert captured == [
        generate_dynapath_token(
            replace(settings, recent_request_deltas=(100,)),
            timestamp_ms=1712345600100,
            random_text="A1B2",
        ),
        generate_dynapath_token(
            replace(settings, recent_request_deltas=(100, 150)),
            timestamp_ms=1712345600250,
            random_text="C3D4",
        ),
    ]


def test_dynapath_generator_is_per_client_and_survives_logout():
    config = KorailConfig(
        dynapath=DynapathConfig(enabled=True, token_settings=make_settings())
    )
    first = KorailClient(config, transport=httpx.MockTransport(success_handler))
    second = KorailClient(config, transport=httpx.MockTransport(success_handler))
    first_generator = first.http._dynapath_generator
    assert first_generator is not None
    assert first_generator is not second.http._dynapath_generator
    first.logout()
    assert first.http._dynapath_generator is first_generator


def test_dynapath_allowlist_uses_exact_path():
    called = False

    def provider(_context):
        nonlocal called
        called = True
        return "token"

    config = KorailConfig(
        dynapath=DynapathConfig(enabled=True, token_provider=provider)
    )
    client = KorailHttpClient(config, transport=httpx.MockTransport(success_handler))
    with pytest.raises(KorailProtocolError):
        client.post_form("/classes/com.korail.mobile.login.Login.suffix")
    assert called is False
```

Define:

```python
def success_handler(_: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"},
    )
```

- [ ] **Step 2: Add failing live-config tests that prohibit probe fallback**

```python
def test_build_config_from_env_requires_device_identity(monkeypatch):
    for name in (
        "KORAIL_DYNAPATH_DEVICE_ID",
        "KORAIL_DYNAPATH_OS_VERSION",
        "KORAIL_DYNAPATH_DEVICE_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="KORAIL_DYNAPATH_DEVICE_ID"):
        live.build_config_from_env()


def test_build_config_from_env_builds_sdk_settings(monkeypatch):
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.setattr(live.time, "time", lambda: 1712345600.0)
    config = live.build_config_from_env()
    assert config.dynapath.token_provider is None
    assert config.dynapath.token_settings.device_id == "device-1"
    assert config.dynapath.token_settings.app_start_ts == "1712345600000"
    assert config.dynapath.token_settings.sdk_version == "v1.0.3"
```

- [ ] **Step 3: Run focused DynaPath and live tests**

Run: `pytest tests/test_dynapath.py tests/test_http.py tests/test_live.py -q`

Expected: FAIL because `KorailHttpClient` calls the stateless token function per request and live config still constructs the probe provider.

- [ ] **Step 4: Validate token settings and token-source selection**

Add:

```python
@dataclass(frozen=True)
class DynapathTokenSettings:
    device_id: str
    as_value: str
    app_start_ts: str
    os_version: str
    device_model: str
    app_id: str = KORAIL_DYNAPATH_APP_ID
    os_type: str = KORAIL_DYNAPATH_OS_TYPE
    sdk_version: str = KORAIL_DYNAPATH_SDK_VERSION
    table_index: int = DYNAPATH_TABLE_INDEX
    table: str = field(default_factory=lambda: generate_dynapath_encoding_table(DYNAPATH_TABLE_INDEX))
    i8: int = DYNAPATH_DEFAULT_I8
    i9: int = DYNAPATH_DEFAULT_I9
    i10: int = DYNAPATH_DEFAULT_I10
    secure_user: bool = False
    debug: bool = False
    emulator: bool = False
    hooked: bool = False
    recent_request_deltas: tuple[int, ...] = (0,)

    def __post_init__(self) -> None:
        for name in ("device_id", "as_value", "app_start_ts", "os_version", "device_model"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"DynaPath {name} must be provided")
        int(self.app_start_ts)


@dataclass(frozen=True)
class DynapathConfig:
    enabled: bool = False
    token_provider: DynapathTokenProvider | None = None
    token_settings: DynapathTokenSettings | None = None
    timestamp_ms_provider: TimestampMsProvider | None = None
    random_text_provider: RandomTextProvider | None = None
    header_name: str = DYNAPATH_HEADER_NAME
    allowlist_paths: frozenset[str] = DYNAPATH_ALLOWLIST_PATHS
    device_name: str = KORAIL_DEFAULT_DEVICE_NAME
    os_version: str = KORAIL_DEFAULT_OS_VERSION

    def __post_init__(self) -> None:
        if self.enabled and (self.token_provider is None) == (self.token_settings is None):
            raise ValueError("enabled DynaPath requires exactly one token provider or token settings")
```

- [ ] **Step 5: Construct and reuse the stateful generator in the HTTP client**

In `KorailHttpClient.__init__`:

```python
self._dynapath_generator = (
    DynapathTokenGenerator(
        config.dynapath.token_settings,
        timestamp_ms_provider=config.dynapath.timestamp_ms_provider,
        random_text_provider=config.dynapath.random_text_provider,
    )
    if config.dynapath.token_settings is not None
    else None
)
```

In `_dynapath_headers`, compare `path` by exact membership in `dynapath.allowlist_paths`. Use `dynapath.token_provider(context)` for the compatibility provider branch and `self._dynapath_generator(context)` for settings. Remove direct per-request calls to `generate_dynapath_token`.

- [ ] **Step 6: Build live settings only from caller environment**

Add `import time` and implement:

```python
def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    settings = DynapathTokenSettings(
        device_id=device_id,
        as_value=os.environ.get("KORAIL_DYNAPATH_AS_VALUE", KORAIL_DYNAPATH_AS_VALUE),
        app_start_ts=str(int(time.time() * 1000)),
        os_version=os_version,
        device_model=device_model,
    )
    dynapath = DynapathConfig(
        enabled=True,
        token_settings=settings,
        device_name=device_model,
        os_version=os_version,
    )
    return KorailConfig(
        base_url=os.environ.get("KORAIL_BASE_URL", "https://smart.letskorail.com:443"),
        user_agent=os.environ.get(
            "KORAIL_USER_AGENT",
            f"Dalvik/2.1.0 (Linux; U; Android {os_version}; {device_model})",
        ),
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", "1440")),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", "3088")),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", "33")),
        dynapath=dynapath,
    )
```

- [ ] **Step 7: Run DynaPath, HTTP, and live helper tests**

Run: `pytest tests/test_dynapath.py tests/test_http.py tests/test_live.py -q`

Expected: PASS. Existing legacy probe generation tests remain valid, but no live default uses the probe provider.

- [ ] **Step 8: Commit only Task 4 files**

```bash
git add src/korail_mobile_api/dynapath.py src/korail_mobile_api/http.py src/korail_mobile_api/live.py src/korail_mobile_api/config.py tests/test_dynapath.py tests/test_http.py tests/test_live.py
git commit -m "fix: keep korail dynapath runtime state"
```

---

### Task 5: Station Resolution, Exact Search Payload, And Nested Train Parsing

**Files:**
- Create: `src/korail_mobile_api/payloads.py`
- Create: `src/korail_mobile_api/parsers.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `tests/fixtures/station_data.json`
- Modify: `tests/fixtures/schedule_view_success.json`
- Test: `tests/test_client_read_apis.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: `KorailConfig`, `TrainSearchQuery`, `TrainSummary.from_raw`, and Task 3 `generate_sid()`.
- Produces: `build_train_search_form(config: KorailConfig, query: TrainSearchQuery, *, departure_name: str, arrival_name: str, sid: str, member_card_no: str | None = None) -> dict[str, str]`, `parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]`, `resolve_station_name(reference: str, names: Mapping[str, str]) -> str`, `parse_train_rows(raw: Mapping[str, Any]) -> list[TrainSummary]`, and station-name fields on `TrainSummary`.

- [ ] **Step 1: Replace synthetic fixtures with observed nested data**

Set `station_data.json` to:

```json
{"stns":{"stn":[{"stn_cd":"0001","stn_nm":"서울"},{"stn_cd":"0020","stn_nm":"부산"}]}}
```

Set `schedule_view_success.json` to:

```json
{"h_msg_cd":"IRG000000","h_msg_txt":"정상처리되었습니다","strResult":"SUCC","trn_infos":{"h_merge_rsv_psb_flg":"N","trn_info":[{"h_trn_no":"00123","h_trn_gp_cd":"100","h_dpt_rs_stn_cd":"0001","h_dpt_rs_stn_nm":"서울","h_arv_rs_stn_cd":"0020","h_arv_rs_stn_nm":"부산","h_dpt_dt":"20260710","h_dpt_tm":"060000","h_arv_tm":"083000"}]}}
```

- [ ] **Step 2: Add failing station, payload, and nested parser tests**

```python
def test_search_resolves_codes_to_names_and_parses_nested_rows(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.seatMovie.ScheduleView": "schedule_view_success.json",
        },
    )
    result = client.search_trains(
        TrainSearchQuery("0001", "0020", "20260710", departure_time="060000")
    )
    search_request = captured[1]
    assert "txtGoStart=%EC%84%9C%EC%9A%B8" in search_request["body"]
    assert "txtGoEnd=%EB%B6%80%EC%82%B0" in search_request["body"]
    assert "Device=AD" in search_request["body"]
    assert "Version=250601003" in search_request["body"]
    assert "Key=" not in search_request["body"]
    assert result.trains[0].train_no == "00123"
    assert result.trains[0].departure_station_name == "서울"


def test_search_accepts_names_without_station_catalog_request(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.seatMovie.ScheduleView": "schedule_view_success.json"},
    )
    client.search_trains(TrainSearchQuery("서울", "부산", "20260710"))
    assert [request["path"] for request in captured] == [
        "/classes/com.korail.mobile.seatMovie.ScheduleView"
    ]
```

- [ ] **Step 3: Run the focused search tests**

Run: `pytest tests/test_client_read_apis.py::test_search_resolves_codes_to_names_and_parses_nested_rows tests/test_client_read_apis.py::test_search_accepts_names_without_station_catalog_request -q`

Expected: FAIL because codes are posted directly and `trn_infos` is treated as a list.

- [ ] **Step 4: Implement station and train parsers**

Create `parsers.py`:

```python
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import TrainSummary


def parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]:
    container = raw.get("stns")
    rows = container.get("stn") if isinstance(container, Mapping) else None
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    names = {
        str(row.get("stn_cd")): str(row.get("stn_nm"))
        for row in rows
        if isinstance(row, Mapping) and row.get("stn_cd") and row.get("stn_nm")
    }
    if not names:
        raise KorailProtocolError("KORAIL station data did not contain usable stations")
    return names


def resolve_station_name(reference: str, names: Mapping[str, str]) -> str:
    value = reference.strip()
    if not value:
        raise KorailProtocolError("KORAIL station reference must not be empty")
    if not value.isdigit():
        return value
    try:
        return names[value]
    except KeyError as exc:
        raise KorailProtocolError(f"KORAIL station code is unknown: {value}") from exc


def parse_train_rows(raw: Mapping[str, Any]) -> list[TrainSummary]:
    container = raw.get("trn_infos")
    if isinstance(container, Mapping):
        rows = container.get("trn_info", [])
    elif isinstance(container, list):
        rows = container
    elif container is None:
        rows = []
    else:
        raise KorailProtocolError("KORAIL train response had invalid trn_infos")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL train response missing trn_infos.trn_info list")
    return [TrainSummary.from_raw(dict(row)) for row in rows if isinstance(row, Mapping)]
```

- [ ] **Step 5: Implement the exact search form builder**

Create `payloads.py` with:

```python
from .config import KorailConfig
from .models import TrainSearchQuery


def build_train_search_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    sid: str,
    member_card_no: str | None = None,
) -> dict[str, str]:
    form = {
        "Device": config.device,
        "Version": config.version,
        "Sid": sid,
        "txtMenuId": "11",
        "radJobId": "1",
        "selGoTrain": query.train_group_code,
        "txtTrnGpCd": query.train_group_code,
        "txtGoStart": departure_name,
        "txtGoEnd": arrival_name,
        "txtGoAbrdDt": query.departure_date,
        "txtGoHour": query.departure_time,
        "txtPsgFlg_1": str(query.passengers),
        "txtPsgFlg_2": "0",
        "txtPsgFlg_3": "0",
        "txtPsgFlg_4": "0",
        "txtPsgFlg_5": "0",
        "txtSeatAttCd_2": "000",
        "txtSeatAttCd_3": "000",
        "txtSeatAttCd_4": "015",
        "ebizCrossCheck": "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    return form
```

- [ ] **Step 6: Wire lazy station resolution and nested parsing into the client**

Initialize `self._station_names: dict[str, str] | None = None`. Add:

```python
def _resolve_station_reference(self, reference: str) -> str:
    if not reference.strip().isdigit():
        return resolve_station_name(reference, {})
    if self._station_names is None:
        self._station_names = parse_station_name_map(self.get_station_data().raw)
    return resolve_station_name(reference, self._station_names)
```

Replace `search_trains` with:

```python
def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
    departure_name = self._resolve_station_reference(query.departure_station_code)
    arrival_name = self._resolve_station_reference(query.arrival_station_code)
    current = self.session.current
    form = build_train_search_form(
        self.config,
        query,
        departure_name=departure_name,
        arrival_name=arrival_name,
        sid=generate_sid(),
        member_card_no=current.member_card_no if current else None,
    )
    response = self.http.post_form(
        "/classes/com.korail.mobile.seatMovie.ScheduleView",
        form,
        include_common=False,
    )
    return TrainSearchResult(
        trains=parse_train_rows(response.raw),
        response=response,
        raw=response.raw,
    )
```

Nullable Retrofit fields not set by the app remain absent from the form rather than being serialized as empty strings.

Add these optional fields to `TrainSummary` and populate them in `from_raw`:

```python
departure_station_name: str | None = None
arrival_station_name: str | None = None
```

Use `h_dpt_rs_stn_nm`/`dptRsStnNm` and `h_arv_rs_stn_nm`/`arvRsStnNm` as their source keys.

Use these exact `from_raw` assignments:

```python
departure_station_name=raw.get("h_dpt_rs_stn_nm") or raw.get("dptRsStnNm"),
arrival_station_name=raw.get("h_arv_rs_stn_nm") or raw.get("arvRsStnNm"),
```

- [ ] **Step 7: Run search and model tests**

Run: `pytest tests/test_client_read_apis.py tests/test_models.py -q`

Expected: PASS.

- [ ] **Step 8: Commit only Task 5 files**

```bash
git add src/korail_mobile_api/payloads.py src/korail_mobile_api/parsers.py src/korail_mobile_api/client.py src/korail_mobile_api/models.py tests/fixtures/station_data.json tests/fixtures/schedule_view_success.json tests/test_client_read_apis.py tests/test_models.py
git commit -m "fix: align korail train search contract"
```

---

### Task 6: Common, Station, Calendar, Schedule, Transfer, And Ticket Forms

**Files:**
- Modify: `src/korail_mobile_api/config.py`
- Modify: `src/korail_mobile_api/payloads.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/session.py`
- Test: `tests/test_client_read_apis.py`
- Test: `tests/test_models.py`
- Test: `tests/test_session.py`

**Interfaces:**
- Consumes: Task 5 payload module and `KorailSessionClient.current`.
- Produces: `build_common_code_form(config, code)`, `build_train_schedule_form(config, run_date, train_no)`, `build_ticket_list_form(config, page_no)`, exact endpoint-specific query sets, and complete failure-raising read methods.

- [ ] **Step 1: Add failing schedule, ticket, and failure-propagation tests**

First extend the existing test helper without changing its capture behavior:

```python
def make_client(load_json_fixture, paths, *, config: KorailConfig | None = None):
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(
            {
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query.decode(),
                "body": request.content.decode(),
            }
        )
        fixture = paths.get(request.url.path)
        if fixture is None:
            raise AssertionError(f"unexpected path {request.url.path}")
        return httpx.Response(200, json=load_json_fixture(fixture))

    return KorailClient(config or KorailConfig(), transport=httpx.MockTransport(handler)), captured
```

```python
def test_train_schedule_sends_device_and_version_without_key(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.research.actualTrainSchedule.do": "train_schedule_success.json"},
    )
    client.get_train_schedule("20260710", "123")
    body = captured[0]["body"]
    assert "Device=AD" in body
    assert "Version=250601003" in body
    assert "Key=" not in body
    assert "trnNo=00123" in body


def test_common_station_and_calendar_use_exact_endpoint_fields(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.code.do": "common_code_login_crypto_n.json",
            "/classes/com.korail.mobile.common.stationinfo": "station_info.json",
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.schedule.runDt": "train_calendar.json",
        },
    )
    client.get_common_code("login")
    client.get_station_info()
    client.get_station_data()
    client.get_train_calendar()
    common_body = parse_qs(captured[0]["body"])
    assert common_body["Device"] == ["AD"]
    assert common_body["Version"] == ["250601003"]
    assert common_body["Key"] == ["korail1234567890"]
    assert common_body["deviceWidth"] == ["1080"]
    assert common_body["deviceHeight"] == ["2400"]
    assert common_body["OSVersion"] == ["35"]
    assert captured[1]["query"] == "Device=AD"
    assert captured[2]["query"] == ""
    assert captured[3]["query"] == ""


def test_ticket_list_sends_complete_member_form(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.myTicket.MyTicketList": "ticket_list_empty.json"},
        config=KorailConfig(advertising_id="ad-id"),
    )
    client.session.current = KorailSession(jsessionid="session", member_no="member")
    client.get_ticket_list()
    body = captured[0]["body"]
    for expected in (
        "txtDeviceId=ad-id",
        "txtIndex=1",
        "h_page_no=1",
        "h_abrd_dt_from=",
        "h_abrd_dt_to=",
        "hiduserYn=Y",
    ):
        assert expected in body
    for nonmember_only in ("hidName", "hidTeleNo", "hidPwd", "tsRsStnCd"):
        assert nonmember_only not in body


def test_public_read_method_raises_application_failure():
    client = client_returning_failure_for("/classes/com.korail.mobile.schedule.runDt")
    with pytest.raises(KorailAppError):
        client.get_train_calendar()


def test_session_expiry_clears_client_state_before_raising():
    client = client_returning_failure_for(
        "/classes/com.korail.mobile.schedule.runDt",
        code="P058",
    )
    client.session.current = KorailSession(jsessionid="stale", member_no="member")
    client.http.cookies.set("JSESSIONID", "stale")
    with pytest.raises(KorailSessionExpiredError):
        client.get_train_calendar()
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies
```

Import `parse_qs` from `urllib.parse` for the exact common-code body assertions.

- [ ] **Step 2: Run focused endpoint tests**

Run: `pytest tests/test_client_read_apis.py -q`

Expected: FAIL because schedule omits `Device`/`Version`, ticket form is abbreviated, and public read methods suppress application failures.

- [ ] **Step 3: Add caller-provided advertising ID and request builders**

Append to `KorailConfig`:

```python
advertising_id: str | None = None
```

Add to `payloads.py`:

```python
def build_train_schedule_form(config: KorailConfig, run_date: str, train_no: str) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(config: KorailConfig, code: str | list[str]) -> dict[str, object]:
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "code": [code] if isinstance(code, str) else code,
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
        "departDate": "",
        "arrivalDate": "",
        "holidayYn": "",
        "OSVersion": config.android_sdk_int,
    }


def build_ticket_list_form(config: KorailConfig, page_no: int) -> dict[str, str]:
    if not config.advertising_id:
        raise KorailProtocolError("KORAIL advertising_id is required for ticket list")
    page = max(1, page_no)
    return {
        "txtDeviceId": config.advertising_id,
        "txtIndex": str(page),
        "h_page_no": str(page),
        "h_abrd_dt_from": "",
        "h_abrd_dt_to": "",
        "hiduserYn": "Y",
    }
```

- [ ] **Step 4: Use exact forms and stop suppressing failures**

Update methods, including the exact no-query station/calendar contracts. Add this client helper and route every public read operation through it:

```python
T = TypeVar("T")


def _run_read(self, operation: Callable[[], T]) -> T:
    try:
        return operation()
    except KorailSessionExpiredError:
        self.clear_session()
        raise


def get_common_code(self, code: str = "") -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            build_common_code_form(self.config, code),
            include_common=False,
        )
    )


def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.get_json(
            "/classes/com.korail.mobile.common.stationinfo",
            {"Device": device},
            require_envelope=False,
        )
    )


def get_station_data(self) -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.get_json(
            "/classes/com.korail.mobile.common.stationdata",
            require_envelope=False,
        )
    )


def get_train_calendar(self) -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.get_json("/classes/com.korail.mobile.schedule.runDt")
    )


def get_train_schedule(self, run_date: str, train_no: str) -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.post_form(
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
            build_train_schedule_form(self.config, run_date, train_no),
            include_common=False,
        )
    )


def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
    if self.session.current is None:
        raise KorailAuthError("KORAIL ticket list requires an authenticated session")
    return self._run_read(
        lambda: self.http.post_form(
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            build_ticket_list_form(self.config, page_no),
        )
    )
```

Import `Callable` and `TypeVar`. Replace the Task 5 search method with the wrapper plus private body below, and replace transfer with its wrapped request:

```python
def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
    return self._run_read(lambda: self._search_trains(query))


def _search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
    departure_name = self._resolve_station_reference(query.departure_station_code)
    arrival_name = self._resolve_station_reference(query.arrival_station_code)
    current = self.session.current
    form = build_train_search_form(
        self.config,
        query,
        departure_name=departure_name,
        arrival_name=arrival_name,
        sid=generate_sid(),
        member_card_no=current.member_card_no if current else None,
    )
    response = self.http.post_form(
        "/classes/com.korail.mobile.seatMovie.ScheduleView",
        form,
        include_common=False,
    )
    return TrainSearchResult(
        trains=parse_train_rows(response.raw),
        response=response,
        raw=response.raw,
    )


def get_transfer_stations(
    self,
    departure_station_code: str,
    arrival_station_code: str,
) -> BaseKorailResponse:
    return self._run_read(
        lambda: self.http.post_form(
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {
                "dptRsStnCd": departure_station_code,
                "arvRsStnCd": arrival_station_code,
            },
        )
    )
```

Remove `raise_on_fail=False` from every public read method. Keep `require_envelope=False` only for the evidenced raw station endpoints. The transfer method uses normal common fields (`Device`, `Version`, `Key`).

Use the shared common-code builder in the login bootstrap:

```python
response = self.http.post_form(
    "/classes/com.korail.mobile.common.code.do",
    build_common_code_form(self.http.config, list(KORAIL_COMMON_CODE_BOOTSTRAP_CODES)),
    include_common=False,
)
```

- [ ] **Step 5: Run all read API and HTTP tests**

Run: `pytest tests/test_client_read_apis.py tests/test_http.py tests/test_models.py tests/test_session.py -q`

Expected: PASS.

- [ ] **Step 6: Commit only Task 6 files**

```bash
git add src/korail_mobile_api/config.py src/korail_mobile_api/payloads.py src/korail_mobile_api/client.py src/korail_mobile_api/session.py tests/test_client_read_apis.py tests/test_models.py tests/test_session.py
git commit -m "fix: complete korail read request forms"
```

---

### Task 7: Safe Full Live Smoke And User Documentation

**Files:**
- Modify: `src/korail_mobile_api/live.py`
- Modify: `tests/test_live.py`
- Create: `tests/test_live_service.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: all stabilized public methods and environment-built configuration.
- Produces: `run_live_smoke_from_env() -> dict[str, Any]` covering every current read-only method without returning raw personal data.

- [ ] **Step 1: Add a failing fake-client smoke contract**

Replace the narrow test with this deterministic fake:

```python
def test_run_live_smoke_calls_every_current_read_without_raw_output(monkeypatch):
    import korail_mobile_api.live as live

    calls: list[tuple[object, ...]] = []
    ok = BaseKorailResponse(
        h_msg_cd="IRG000000",
        h_msg_txt="OK",
        str_result="SUCC",
        raw={},
    )
    train = TrainSummary(
        train_no="00123",
        departure_date="20260710",
        departure_station_code="0001",
        arrival_station_code="0020",
    )

    class FakeClient:
        def __init__(self, _config):
            calls.append(("init",))

        def login(self, member_no: str, password: str) -> KorailSession:
            calls.append(("login", member_no, password))
            return KorailSession(jsessionid="session", member_no=member_no)

        def get_common_code(self, code: str = "") -> BaseKorailResponse:
            calls.append(("get_common_code", code))
            return BaseKorailResponse(h_msg_cd="API.I00000", str_result="SUCC", raw={})

        def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
            calls.append(("get_station_info", device))
            return BaseKorailResponse(raw={"map_version": "1"})

        def get_station_data(self) -> BaseKorailResponse:
            calls.append(("get_station_data",))
            return BaseKorailResponse(
                raw={"stns": {"stn": [{"stn_cd": "0001"}, {"stn_cd": "0020"}]}}
            )

        def get_train_calendar(self) -> BaseKorailResponse:
            calls.append(("get_train_calendar",))
            return BaseKorailResponse(
                h_msg_cd="IRG000000",
                str_result="SUCC",
                raw={"days": [{"runDt": "20260710"}]},
            )

        def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
            calls.append(("search_trains", query.departure_station_code, query.arrival_station_code))
            return TrainSearchResult(trains=[train], response=ok, raw={})

        def get_train_schedule(self, run_date: str, train_no: str) -> BaseKorailResponse:
            calls.append(("get_train_schedule", run_date, train_no))
            return BaseKorailResponse(h_msg_cd="API.I00000", str_result="SUCC", raw={})

        def get_transfer_stations(self, departure: str, arrival: str) -> BaseKorailResponse:
            calls.append(("get_transfer_stations", departure, arrival))
            return ok

        def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
            calls.append(("get_ticket_list", page_no))
            return BaseKorailResponse(h_msg_cd="WRT300005", str_result="SUCC", raw={})

        def close(self) -> None:
            calls.append(("close",))

    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "password")
    monkeypatch.setattr(live, "KorailClient", FakeClient)
    monkeypatch.setattr(live, "build_config_from_env", KorailConfig)
    result = live.run_live_smoke_from_env()

    assert result == {
        "loggedIn": True,
        "commonCode": "API.I00000",
        "stationInfoLoaded": True,
        "stationDataCount": 2,
        "calendarCode": "IRG000000",
        "trainCount": 1,
        "scheduleCode": "API.I00000",
        "transferCode": "IRG000000",
        "ticketCode": "WRT300005",
    }
    assert "password" not in repr(result).lower()
    assert "raw" not in result
    assert [call[0] for call in calls] == [
        "init",
        "login",
        "get_common_code",
        "get_station_info",
        "get_station_data",
        "get_train_calendar",
        "search_trains",
        "get_train_schedule",
        "get_transfer_stations",
        "get_ticket_list",
        "close",
    ]
```

Import `KorailConfig`, `TrainSearchQuery`, `TrainSearchResult`, and `TrainSummary` for this test.

Update the successful `build_config_from_env` unit test from Task 4 with:

```python
monkeypatch.setenv("KORAIL_ADVERTISING_ID", "ad-id")
assert config.advertising_id == "ad-id"
```

- [ ] **Step 2: Run the live-helper unit test**

Run: `pytest tests/test_live.py -q`

Expected: FAIL because the helper currently calls only station data and calendar.

- [ ] **Step 3: Expand the helper without returning raw content**

Use this orchestration:

```python
def run_live_smoke_from_env() -> dict[str, Any]:
    if not live_enabled():
        raise RuntimeError("Set KORAIL_MOBILE_API_LIVE=1 to run live smoke")
    member_no, password = read_credentials_from_env()
    client = KorailClient(build_config_from_env())
    try:
        session = client.login(member_no, password)
        common = client.get_common_code("")
        station_info = client.get_station_info()
        station_data = client.get_station_data()
        calendar = client.get_train_calendar()
        days = calendar.raw.get("days") if isinstance(calendar.raw.get("days"), list) else []
        departure_date = os.environ.get("KORAIL_TEST_DATE") or (
            str(days[0].get("runDt")) if days and isinstance(days[0], dict) else ""
        )
        if not departure_date:
            raise RuntimeError("KORAIL_TEST_DATE is required when the calendar has no run date")
        query = TrainSearchQuery(
            departure_station_code=os.environ.get("KORAIL_DEPARTURE_STATION", "서울"),
            arrival_station_code=os.environ.get("KORAIL_ARRIVAL_STATION", "부산"),
            departure_date=departure_date,
            departure_time=os.environ.get("KORAIL_DEPARTURE_TIME", "060000"),
        )
        search = client.search_trains(query)
        schedule = (
            client.get_train_schedule(
                search.trains[0].departure_date or departure_date,
                search.trains[0].train_no,
            )
            if search.trains
            else None
        )
        transfer = client.get_transfer_stations(
            os.environ.get("KORAIL_DEPARTURE_STATION_CODE", "0001"),
            os.environ.get("KORAIL_ARRIVAL_STATION_CODE", "0020"),
        )
        tickets = client.get_ticket_list()
        stations = (station_data.raw.get("stns") or {}).get("stn")
        return {
            "loggedIn": bool(session.jsessionid),
            "commonCode": common.h_msg_cd,
            "stationInfoLoaded": bool(station_info.raw),
            "stationDataCount": len(stations) if isinstance(stations, list) else 0,
            "calendarCode": calendar.h_msg_cd,
            "trainCount": len(search.trains),
            "scheduleCode": schedule.h_msg_cd if schedule else None,
            "transferCode": transfer.h_msg_cd,
            "ticketCode": tickets.h_msg_cd,
        }
    finally:
        client.close()
```

Import `TrainSearchQuery` and set `advertising_id=_required_env("KORAIL_ADVERTISING_ID")` in `build_config_from_env()` so the live ticket request never invents an advertising ID.

- [ ] **Step 4: Add an explicitly skipped-by-default live test**

Create:

```python
import pytest

from korail_mobile_api.live import live_enabled, run_live_smoke_from_env


pytestmark = pytest.mark.live


def test_read_only_live_smoke():
    if not live_enabled():
        pytest.skip("KORAIL live smoke requires explicit opt-in")
    result = run_live_smoke_from_env()
    assert result["loggedIn"] is True
    assert result["stationDataCount"] > 0
    assert result["trainCount"] >= 0
    assert "raw" not in result
```

- [ ] **Step 5: Update README with required device values and safe output**

Document this environment contract:

```bash
export KORAIL_MOBILE_API_LIVE=1
export KORAIL_MEMBER_NO="<member-id>"
export KORAIL_PASSWORD="<password>"
export KORAIL_DYNAPATH_DEVICE_ID="<android-id>"
export KORAIL_DYNAPATH_OS_VERSION="<android-version>"
export KORAIL_DYNAPATH_DEVICE_MODEL="<device-model>"
export KORAIL_ADVERTISING_ID="<advertising-id>"
python3 -c "from korail_mobile_api.live import run_live_smoke_from_env; print(run_live_smoke_from_env())"
```

State that probe exports remain compatibility helpers but are not live defaults, and that the helper emits only status codes and bounded counts.

- [ ] **Step 6: Run offline live-helper tests**

Run: `pytest tests/test_live.py tests/test_live_service.py -q`

Expected: PASS with the service test skipped unless explicit live opt-in exists.

- [ ] **Step 7: Commit only Task 7 files**

```bash
git add src/korail_mobile_api/live.py tests/test_live.py tests/test_live_service.py README.md
git commit -m "test: cover korail read only live flow"
```

---

### Task 8: Public Surface, Build, And Isolated Import Gate

**Files:**
- Create: `tests/test_public_contract.py`
- Modify: `src/korail_mobile_api/__init__.py`

**Interfaces:**
- Consumes: every stabilized class and method from Tasks 1-7.
- Produces: a regression gate that prevents accidental endpoint expansion or loss of public error/model exports.

- [ ] **Step 1: Add the final public-contract test**

```python
import inspect

import korail_mobile_api
from korail_mobile_api import KorailClient


def test_client_public_method_set_is_stable():
    methods = {
        name
        for name, value in inspect.getmembers(KorailClient, predicate=inspect.isfunction)
        if not name.startswith("_")
    }
    assert methods == {
        "clear_session",
        "close",
        "get_common_code",
        "get_station_data",
        "get_station_info",
        "get_ticket_list",
        "get_train_calendar",
        "get_train_schedule",
        "get_transfer_stations",
        "login",
        "logout",
        "search_trains",
    }


def test_completed_errors_are_exported():
    assert korail_mobile_api.KorailSessionExpiredError
    assert korail_mobile_api.KorailDynaPathError
    assert korail_mobile_api.KorailTransportError
    assert korail_mobile_api.KorailAppError


def test_login_and_ticket_signatures_remain_compatible():
    assert list(inspect.signature(KorailClient.login).parameters) == [
        "self",
        "member_no",
        "password",
        "input_flag",
        "check_valid_pw",
        "cust_id",
        "etr_path",
    ]
    assert list(inspect.signature(KorailClient.get_ticket_list).parameters) == ["self", "page_no"]
```

- [ ] **Step 2: Run the public-contract test**

Run: `pytest tests/test_public_contract.py -q`

Expected: PASS after adding any missing Task 1 error exports to `__init__.py`.

- [ ] **Step 3: Run the complete offline suite**

Run: `pytest -q`

Expected: PASS with only the explicitly disabled live test skipped.

- [ ] **Step 4: Build wheel and sdist**

Run: `python3 -m build`

Expected: exit 0 and fresh `dist/korail_mobile_api-0.1.0-py3-none-any.whl` plus source archive.

- [ ] **Step 5: Verify isolated installation and imports**

```bash
VERIFY_DIR="$(mktemp -d)"
python3 -m venv "$VERIFY_DIR/venv"
"$VERIFY_DIR/venv/bin/pip" install --quiet dist/korail_mobile_api-0.1.0-py3-none-any.whl
"$VERIFY_DIR/venv/bin/python" -c "from korail_mobile_api import KorailClient, KorailDynaPathError, KorailSessionExpiredError; print(KorailClient.__name__)"
rm -rf "$VERIFY_DIR"
```

Expected output: `KorailClient`.

- [ ] **Step 6: Run the opted-in live gate**

Load the ignored `.local-live-smoke.env` in the shell without printing it, then run:

```bash
pytest -m live tests/test_live_service.py -q
```

Expected: PASS. If the server rejects a request, the test must report the typed transport, auth, session, app, or DynaPath error; do not weaken the assertion into a fabricated success.

- [ ] **Step 7: Confirm no mutation route or secret was added**

Run: `git diff HEAD^ -- src tests README.md | rg -n "TicketReservation|NonMemTicket|payment|refund|memberDrop|act_19"`

Expected: no newly callable mutation endpoint. Documentation/safety references are acceptable only when they explicitly describe rejection.

- [ ] **Step 8: Commit the final contract gate**

```bash
git add tests/test_public_contract.py src/korail_mobile_api/__init__.py
git commit -m "test: lock korail public api contract"
```

---

## Final Verification Checklist

- [ ] `pytest -q` passes.
- [ ] `python3 -m build` succeeds.
- [ ] The built wheel imports in a fresh virtual environment.
- [ ] `pytest -m live tests/test_live_service.py -q` passes with ignored local credentials.
- [ ] Every `KorailClient` request is present in `KORAIL_READ_ONLY_ROUTES`.
- [ ] No mutation endpoint is present in the HTTP route registry.
- [ ] Failed login leaves no old `current` session or cookie.
- [ ] Additional authentication leaves `current=None` and an explicit pending state.
- [ ] Two DynaPath requests use one generator and a rolling delta queue.
- [ ] Search sends station names and parses `trn_infos.trn_info[]`.
- [ ] Schedule sends `Device` and `Version` without `Key`.
- [ ] Ticket list sends the full evidenced member form.
- [ ] No credential, cookie, DynaPath token, PNR, or raw account response appears in test output.
