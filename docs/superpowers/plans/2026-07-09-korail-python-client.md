# KORAIL Python Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first installable `korail-mobile-api` Python package with login and safe read/query APIs.

**Architecture:** The package uses a thin `httpx` transport wrapper, dataclass models, explicit parser functions, and a `KorailClient` facade. KORAIL-specific crypto, `Sid`, and DynaPath boundaries stay isolated from the public facade. Dangerous mutation endpoints are not implemented as public methods or stubs.

**Tech Stack:** Python 3.11+, `httpx`, `cryptography`, standard-library `dataclasses`, `pytest`.

## Global Constraints

- Distribution package name: `korail-mobile-api`.
- Python import package: `korail_mobile_api`.
- Runtime dependencies: `httpx` and `cryptography`.
- Test dependency: `pytest`.
- Package layout: `src/korail_mobile_api/`.
- MVP includes login and safe read/query APIs only.
- Reservation, payment, refund, check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this version.
- Dangerous endpoints must not appear as public stub methods in this version.
- Default tests must be offline and non-destructive.
- Live smoke must require `KORAIL_MOBILE_API_LIVE=1` and credentials from environment variables.
- Live smoke must only perform login and read/query calls.
- Live smoke must never call reservation, payment, refund, check-in, or membership mutation endpoints.
- Live smoke must not persist raw responses inside the repository.
- Runtime defaults: base host `https://smart.letskorail.com`, common fields `Device=AD`, `Version=250601003`, `Key=korail1234567890`, form encoding `application/x-www-form-urlencoded; charset=UTF-8`, and 60 second timeout.
- Response envelope fields are `h_msg_cd`, `h_msg_txt`, and `strResult`.
- DynaPath token generation is opaque and not implemented.

---

## File Structure

Create:

```text
pyproject.toml
src/korail_mobile_api/__init__.py
src/korail_mobile_api/client.py
src/korail_mobile_api/config.py
src/korail_mobile_api/crypto.py
src/korail_mobile_api/errors.py
src/korail_mobile_api/http.py
src/korail_mobile_api/live.py
src/korail_mobile_api/models.py
src/korail_mobile_api/redaction.py
src/korail_mobile_api/safety.py
src/korail_mobile_api/session.py
tests/conftest.py
tests/fixtures/common_code_login_crypto_n.json
tests/fixtures/common_code_login_crypto_y.json
tests/fixtures/dynapath_403.json
tests/fixtures/login_success.json
tests/fixtures/reservation_history_empty.json
tests/fixtures/schedule_view_success.json
tests/fixtures/station_data.json
tests/fixtures/station_info.json
tests/fixtures/ticket_list_empty.json
tests/fixtures/train_calendar.json
tests/test_client_read_apis.py
tests/test_crypto.py
tests/test_http.py
tests/test_live.py
tests/test_models.py
tests/test_redaction_safety.py
tests/test_session.py
```

Do not create modules or methods for excluded destructive domains.

---

### Task 1: Package Scaffold And Metadata

**Files:**
- Create: `pyproject.toml`
- Create: `src/korail_mobile_api/__init__.py`
- Create: `src/korail_mobile_api/config.py`
- Create: `src/korail_mobile_api/errors.py`
- Create: `src/korail_mobile_api/models.py`
- Create: `tests/test_models.py`

**Interfaces:**
- Produces: `KorailConfig`, exported package symbols, base exception classes, and initial dataclasses used by later tasks.

- [ ] **Step 1: Write failing metadata/import tests**

Create `tests/test_models.py`:

```python
from dataclasses import is_dataclass

import korail_mobile_api
from korail_mobile_api import KorailConfig
from korail_mobile_api.errors import KorailApiError, KorailAuthError, KorailProtocolError
from korail_mobile_api.models import KorailSession, TrainSearchQuery, TrainSearchResult, TrainSummary


def test_public_exports_are_available():
    assert korail_mobile_api.KorailConfig is KorailConfig
    assert issubclass(KorailAuthError, KorailApiError)
    assert issubclass(KorailProtocolError, KorailApiError)


def test_core_models_are_dataclasses():
    assert is_dataclass(KorailConfig)
    assert is_dataclass(KorailSession)
    assert is_dataclass(TrainSearchQuery)
    assert is_dataclass(TrainSummary)
    assert is_dataclass(TrainSearchResult)


def test_config_defaults_match_design():
    config = KorailConfig()
    assert config.base_url == "https://smart.letskorail.com"
    assert config.device == "AD"
    assert config.version == "250601003"
    assert config.key == "korail1234567890"
    assert config.timeout == 60.0
    assert config.live_env_var == "KORAIL_MOBILE_API_LIVE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'korail_mobile_api'`.

- [ ] **Step 3: Add package metadata and initial code**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "korail-mobile-api"
version = "0.1.0"
description = "Python client for documented KORAIL mobile app read APIs"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27,<1",
  "cryptography>=42,<47",
]

[project.optional-dependencies]
test = [
  "pytest>=8,<10",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]
markers = [
  "live: tests that call live KORAIL services and require explicit opt-in",
]
```

Create `src/korail_mobile_api/errors.py`:

```python
class KorailApiError(Exception):
    """Base error for KORAIL client failures."""


class KorailTransportError(KorailApiError):
    """HTTP transport failed before an app-level response was parsed."""


class KorailProtocolError(KorailApiError):
    """The server response did not match the documented protocol."""


class KorailAuthError(KorailApiError):
    """Login or session authentication failed."""


class KorailAppError(KorailApiError):
    """The server returned an app-level failure response."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(f"{code or 'UNKNOWN'}: {message or ''}".strip())
```

Create `src/korail_mobile_api/config.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class KorailConfig:
    base_url: str = "https://smart.letskorail.com"
    device: str = "AD"
    version: str = "250601003"
    key: str = "korail1234567890"
    timeout: float = 60.0
    user_agent: str = "korail-mobile-api/0.1.0"
    live_env_var: str = "KORAIL_MOBILE_API_LIVE"
```

Create `src/korail_mobile_api/models.py`:

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class KorailSession:
    jsessionid: str | None = None
    member_no: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BaseKorailResponse:
    h_msg_cd: str | None = None
    h_msg_txt: str | None = None
    str_result: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LoginCryptoInfo:
    idx: str = ""
    key: str = ""
    pwd_aes_cphd: str = "N"


@dataclass(frozen=True)
class TrainSearchQuery:
    departure_station_code: str
    arrival_station_code: str
    departure_date: str
    departure_time: str = "000000"
    passengers: int = 1
    train_group_code: str = "109"
    include_srt: bool = False


@dataclass(frozen=True)
class TrainSummary:
    train_no: str
    train_group_code: str | None = None
    departure_station_code: str | None = None
    arrival_station_code: str | None = None
    departure_date: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TrainSearchResult:
    trains: list[TrainSummary]
    response: BaseKorailResponse
    raw: dict[str, Any] = field(default_factory=dict)
```

Create `src/korail_mobile_api/client.py` with the initial class needed by import smoke tests:

```python
from .config import KorailConfig


class KorailClient:
    def __init__(self, config: KorailConfig | None = None) -> None:
        self.config = config or KorailConfig()
```

Create `src/korail_mobile_api/__init__.py`:

```python
from .client import KorailClient
from .config import KorailConfig
from .errors import KorailApiError, KorailAuthError, KorailProtocolError
from .models import KorailSession, TrainSearchQuery, TrainSearchResult, TrainSummary

__all__ = [
    "KorailApiError",
    "KorailAuthError",
    "KorailClient",
    "KorailConfig",
    "KorailProtocolError",
    "KorailSession",
    "TrainSearchQuery",
    "TrainSearchResult",
    "TrainSummary",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/korail_mobile_api tests/test_models.py
git commit -m "feat: scaffold korail python package"
```

---

### Task 2: HTTP, Parsing, Redaction, And Safety Core

**Files:**
- Create: `src/korail_mobile_api/http.py`
- Create: `src/korail_mobile_api/redaction.py`
- Create: `src/korail_mobile_api/safety.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/dynapath_403.json`
- Modify: `src/korail_mobile_api/models.py`
- Test: `tests/test_http.py`
- Test: `tests/test_redaction_safety.py`

**Interfaces:**
- Consumes: `KorailConfig`, `BaseKorailResponse`, `KorailAppError`, `KorailProtocolError`.
- Produces: `KorailHttpClient`, `parse_base_response()`, `redact_mapping()`, `EXCLUDED_API_DOMAINS`.

- [ ] **Step 1: Write failing HTTP and safety tests**

Create `tests/conftest.py`:

```python
import json
from pathlib import Path


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_json_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
```

Create `tests/fixtures/dynapath_403.json`:

```json
{"message": "macro protection message"}
```

Create `tests/test_http.py`:

```python
import httpx

from korail_mobile_api import KorailConfig
from korail_mobile_api.errors import KorailAppError, KorailProtocolError
from korail_mobile_api.http import KorailHttpClient, parse_base_response


def test_post_form_adds_common_fields_and_form_encoding():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers["content-type"]
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.post_form("/classes/example.do", {"custom": "value"})

    assert captured["url"] == "https://smart.letskorail.com/classes/example.do"
    assert captured["content_type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    assert "Device=AD" in captured["body"]
    assert "Version=250601003" in captured["body"]
    assert "Key=korail1234567890" in captured["body"]
    assert "custom=value" in captured["body"]
    assert response.h_msg_cd == "IRG000000"


def test_parse_base_response_raises_app_error_for_fail():
    try:
        parse_base_response({"h_msg_cd": "WRG000000", "h_msg_txt": "조회 결과 없음", "strResult": "FAIL"})
    except KorailAppError as exc:
        assert exc.code == "WRG000000"
        assert "조회 결과 없음" in str(exc)
    else:
        raise AssertionError("KorailAppError was not raised")


def test_parse_base_response_requires_dict():
    try:
        parse_base_response(["not", "a", "dict"])
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")
```

Create `tests/test_redaction_safety.py`:

```python
from korail_mobile_api.redaction import redact_mapping, redact_text
from korail_mobile_api.safety import EXCLUDED_API_DOMAINS


def test_redact_mapping_masks_sensitive_values():
    data = {
        "txtMemberNo": "1234567890",
        "txtPwd": "secret-password",
        "JSESSIONID": "abc",
        "pnrNo": "123456789012",
        "safe": "value",
    }
    redacted = redact_mapping(data)
    assert redacted["txtMemberNo"] == "[REDACTED]"
    assert redacted["txtPwd"] == "[REDACTED]"
    assert redacted["JSESSIONID"] == "[REDACTED]"
    assert redacted["pnrNo"] == "[REDACTED]"
    assert redacted["safe"] == "value"


def test_redact_text_masks_card_like_values():
    assert "411111" not in redact_text("card 4111-1111-1111-1111")


def test_safety_excludes_dangerous_domains_without_stub_apis():
    assert "reservation" in EXCLUDED_API_DOMAINS
    assert "payment" in EXCLUDED_API_DOMAINS
    assert "refund" in EXCLUDED_API_DOMAINS
    assert "check-in" in EXCLUDED_API_DOMAINS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_http.py tests/test_redaction_safety.py -q`

Expected: FAIL because modules are missing.

- [ ] **Step 3: Implement HTTP, parsing, redaction, and safety**

Modify `src/korail_mobile_api/models.py` to add aliases:

```python
    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "BaseKorailResponse":
        return cls(
            h_msg_cd=raw.get("h_msg_cd"),
            h_msg_txt=raw.get("h_msg_txt"),
            str_result=raw.get("strResult"),
            raw=raw,
        )
```

Create `src/korail_mobile_api/http.py`:

```python
from typing import Any, Mapping

import httpx

from .config import KorailConfig
from .errors import KorailAppError, KorailProtocolError, KorailTransportError
from .models import BaseKorailResponse


def parse_base_response(data: Any, *, raise_on_fail: bool = True) -> BaseKorailResponse:
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    response = BaseKorailResponse.from_raw(data)
    if raise_on_fail and response.str_result == "FAIL":
        raise KorailAppError(response.h_msg_cd, response.h_msg_txt, raw=data)
    return response


class KorailHttpClient:
    def __init__(self, config: KorailConfig, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"User-Agent": config.user_agent},
            transport=transport,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    def close(self) -> None:
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        return {"Device": self.config.device, "Version": self.config.version, "Key": self.config.key}

    def post_form(
        self,
        path: str,
        data: Mapping[str, Any] | None = None,
        *,
        include_common: bool = True,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        form: dict[str, Any] = {}
        if include_common:
            form.update(self.common_fields())
        if data:
            form.update(data)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        try:
            response = self._client.post(path, data=form, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KorailTransportError(str(exc)) from exc
        return parse_base_response(response.json(), raise_on_fail=raise_on_fail)

    def get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        include_common: bool = False,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        if params:
            query.update(params)
        try:
            response = self._client.get(path, params=query)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KorailTransportError(str(exc)) from exc
        return parse_base_response(response.json(), raise_on_fail=raise_on_fail)
```

Create `src/korail_mobile_api/redaction.py`:

```python
from collections.abc import Mapping
import re
from typing import Any

SENSITIVE_KEYS = {
    "txtMemberNo",
    "txtPwd",
    "password",
    "JSESSIONID",
    "Cookie",
    "Set-Cookie",
    "pnrNo",
    "hidPnrNo",
    "tkRetPwd",
}

CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def redact_text(value: str) -> str:
    return CARD_RE.sub("[REDACTED_CARD]", value)


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        else:
            redacted[key] = value
    return redacted
```

Create `src/korail_mobile_api/safety.py`:

```python
EXCLUDED_API_DOMAINS = frozenset(
    {
        "reservation",
        "payment",
        "refund",
        "check-in",
        "member-drop",
        "push-sms",
        "points-mileage",
        "dynapath-token-generation",
    }
)

SAFETY_DEFAULTS = {
    "조회성 API": "실제 호출 허용 가능. 단, 계정/티켓 개인정보 로그 마스킹",
    "예약 생성/취소/변경": "기본 비활성화. 명시적 opt-in과 dry-run marker 필요",
    "결제/포인트/현금영수증 발급": "기본 비활성화. 테스트 카드라도 운영 PG endpoint 직접 호출 금지",
    "환불/반환/체크인/회원탈퇴": "기본 비활성화. 별도 confirmation token 필요",
    "PNR/발권번호/N카드 기반 API": "실제 값 없으면 schema-only 테스트만 수행",
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_http.py tests/test_redaction_safety.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/korail_mobile_api tests/conftest.py tests/fixtures/dynapath_403.json tests/test_http.py tests/test_redaction_safety.py
git commit -m "feat: add korail http and safety core"
```

---

### Task 3: Crypto And Session Login

**Files:**
- Create: `src/korail_mobile_api/crypto.py`
- Create: `src/korail_mobile_api/session.py`
- Create: `tests/fixtures/common_code_login_crypto_n.json`
- Create: `tests/fixtures/common_code_login_crypto_y.json`
- Create: `tests/fixtures/login_success.json`
- Test: `tests/test_crypto.py`
- Test: `tests/test_session.py`
- Modify: `src/korail_mobile_api/client.py`

**Interfaces:**
- Consumes: `KorailHttpClient`, `LoginCryptoInfo`, `KorailSession`.
- Produces: `transform_login_password()`, `generate_sid()`, `KorailSessionClient.login()`, `KorailClient.login()`.

- [ ] **Step 1: Write failing crypto and session tests**

Create `tests/fixtures/common_code_login_crypto_n.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","idx":"IDX-N","key":"1234567890abcdef","pwdAESCphd":"N"}
```

Create `tests/fixtures/common_code_login_crypto_y.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","idx":"IDX-Y","key":"1234567890abcdef","pwdAESCphd":"Y"}
```

Create `tests/fixtures/login_success.json`:

```json
{"h_msg_cd":"IRZ000001","h_msg_txt":"정상적으로 조회 되었습니다.","strResult":"SUCC","custNm":"TEST"}
```

Create `tests/test_crypto.py`:

```python
from korail_mobile_api.crypto import generate_sid, transform_login_password
from korail_mobile_api.models import LoginCryptoInfo


def test_transform_login_password_base64_only():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="N")
    assert transform_login_password("pw123", info) == "cHcxMjM="


def test_transform_login_password_aes_is_deterministic_and_not_plaintext():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="Y")
    first = transform_login_password("pw123", info)
    second = transform_login_password("pw123", info)
    assert first == second
    assert first != "pw123"
    assert first != "cHcxMjM="


def test_generate_sid_is_deterministic_with_epoch_ms():
    sid = generate_sid(epoch_ms=1710000000000)
    assert isinstance(sid, str)
    assert sid == generate_sid(epoch_ms=1710000000000)
    assert sid != generate_sid(epoch_ms=1710000000001)
```

Create `tests/test_session.py`:

```python
import httpx

from korail_mobile_api import KorailClient, KorailConfig


def test_login_posts_transformed_password_and_tracks_cookie(load_json_fixture):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=load_json_fixture("common_code_login_crypto_n.json"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            captured["body"] = request.content.decode()
            return httpx.Response(
                200,
                json=load_json_fixture("login_success.json"),
                headers={"Set-Cookie": "JSESSIONID=session-123; Path=/; HttpOnly"},
            )
        raise AssertionError(f"unexpected path {request.url.path}")

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    session = client.login("member1", "pw123")

    assert "txtMemberNo=member1" in captured["body"]
    assert "txtPwd=cHcxMjM%3D" in captured["body"]
    assert "txtInputFlg=2" in captured["body"]
    assert session.jsessionid == "session-123"
    assert session.member_no == "member1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_crypto.py tests/test_session.py -q`

Expected: FAIL because crypto/session implementation is missing.

- [ ] **Step 3: Implement crypto and session**

Create `src/korail_mobile_api/crypto.py`:

```python
from __future__ import annotations

import base64
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .models import LoginCryptoInfo

SID_KEY = b"2485dd54d9deaa36"


def _aes_cbc_pkcs7_encrypt_to_base64(plaintext: bytes, key: bytes, iv: bytes) -> str:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    if info.pwd_aes_cphd == "Y":
        key = info.key.encode("utf-8")[:16]
        encrypted = _aes_cbc_pkcs7_encrypt_to_base64(password.encode("utf-8"), key, key)
        return base64.b64encode(encrypted.encode("utf-8")).decode("ascii")
    return base64.b64encode(password.encode("utf-8")).decode("ascii")


def generate_sid(*, epoch_ms: int | None = None) -> str:
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    return _aes_cbc_pkcs7_encrypt_to_base64(f"AD{timestamp}".encode("utf-8"), SID_KEY, SID_KEY)
```

Create `src/korail_mobile_api/session.py`:

```python
from __future__ import annotations

from .crypto import transform_login_password
from .errors import KorailAuthError
from .http import KorailHttpClient
from .models import KorailSession, LoginCryptoInfo


class KorailSessionClient:
    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http
        self.current: KorailSession | None = None

    def get_login_crypto_info(self) -> LoginCryptoInfo:
        response = self.http.post_form(
            "/classes/com.korail.mobile.common.code.do",
            {"code": "login"},
            raise_on_fail=False,
        )
        raw = response.raw
        return LoginCryptoInfo(
            idx=str(raw.get("idx") or ""),
            key=str(raw.get("key") or ""),
            pwd_aes_cphd=str(raw.get("pwdAESCphd") or "N"),
        )

    def login(self, member_no: str, password: str, *, input_flag: str = "2") -> KorailSession:
        crypto_info = self.get_login_crypto_info()
        transformed = transform_login_password(password, crypto_info)
        response = self.http.post_form(
            "/classes/com.korail.mobile.login.Login",
            {
                "txtMemberNo": member_no,
                "txtPwd": transformed,
                "txtInputFlg": input_flag,
                "checkValidPw": "",
                "custId": "",
                "etrPath": "",
                "idx": crypto_info.idx,
            },
            raise_on_fail=False,
        )
        if response.str_result == "FAIL":
            raise KorailAuthError(response.h_msg_txt or "KORAIL login failed")
        jsessionid = self.http.cookies.get("JSESSIONID")
        self.current = KorailSession(jsessionid=jsessionid, member_no=member_no, raw=response.raw)
        return self.current

    def clear_session(self) -> None:
        self.http.cookies.clear()
        self.current = None
```

Modify `src/korail_mobile_api/client.py`:

```python
import httpx

from .config import KorailConfig
from .http import KorailHttpClient
from .models import KorailSession
from .session import KorailSessionClient


class KorailClient:
    def __init__(self, config: KorailConfig | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)

    def close(self) -> None:
        self.http.close()

    def login(self, member_no: str, password: str, *, input_flag: str = "2") -> KorailSession:
        return self.session.login(member_no, password, input_flag=input_flag)

    def clear_session(self) -> None:
        self.session.clear_session()

    def logout(self) -> None:
        self.clear_session()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_crypto.py tests/test_session.py -q`

Expected: PASS.

- [ ] **Step 5: Run existing tests**

Run: `pytest tests/test_models.py tests/test_http.py tests/test_redaction_safety.py tests/test_crypto.py tests/test_session.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/korail_mobile_api tests/fixtures/common_code_login_crypto_n.json tests/fixtures/common_code_login_crypto_y.json tests/fixtures/login_success.json tests/test_crypto.py tests/test_session.py
git commit -m "feat: add korail login session support"
```

---

### Task 4: Read-Only Client APIs

**Files:**
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/http.py`
- Modify: `src/korail_mobile_api/models.py`
- Create: `tests/fixtures/reservation_history_empty.json`
- Create: `tests/fixtures/schedule_view_success.json`
- Create: `tests/fixtures/station_data.json`
- Create: `tests/fixtures/station_info.json`
- Create: `tests/fixtures/ticket_list_empty.json`
- Create: `tests/fixtures/train_calendar.json`
- Test: `tests/test_client_read_apis.py`

**Interfaces:**
- Consumes: `KorailClient`, `KorailHttpClient`, `TrainSearchQuery`.
- Produces: public read methods listed in the design spec.

- [ ] **Step 1: Write failing read API tests**

Create simple fixture JSON files:

`tests/fixtures/station_data.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","stations":[{"stnCd":"0001","stnNm":"서울"}]}
```

`tests/fixtures/station_info.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","stationInfo":[{"stnCd":"0001","stnNm":"서울"}]}
```

`tests/fixtures/train_calendar.json`:

```json
{"h_msg_cd":"API.I00000","h_msg_txt":"Success","strResult":"SUCC","days":[{"runDt":"20260710"}]}
```

`tests/fixtures/schedule_view_success.json`:

```json
{"h_msg_cd":"IRG000000","h_msg_txt":"정상처리되었습니다","strResult":"SUCC","trn_infos":[{"h_trn_no":"00123","h_trn_gp_cd":"100","h_dpt_rs_stn_cd":"0001","h_arv_rs_stn_cd":"0020","h_dpt_dt":"20260710","h_dpt_tm":"060000","h_arv_tm":"083000"}]}
```

`tests/fixtures/reservation_history_empty.json`:

```json
{"h_msg_cd":"P100","h_msg_txt":"검색된 데이터가 없습니다.","strResult":"SUCC","reservations":[]}
```

`tests/fixtures/ticket_list_empty.json`:

```json
{"h_msg_cd":"WRT300005","h_msg_txt":"조회자료가 없습니다.","strResult":"SUCC","tickets":[]}
```

Create `tests/test_client_read_apis.py`:

```python
import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.models import TrainSearchQuery


def make_client(load_json_fixture, paths):
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append((request.method, request.url.path, request.content.decode()))
        fixture = paths.get(request.url.path)
        if fixture is None:
            raise AssertionError(f"unexpected path {request.url.path}")
        return httpx.Response(200, json=load_json_fixture(fixture))

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler)), captured


def test_station_and_calendar_read_methods(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.common.stationinfo": "station_info.json",
            "/classes/com.korail.mobile.schedule.runDt": "train_calendar.json",
            "/classes/com.korail.mobile.common.code.do": "common_code_login_crypto_n.json",
        },
    )

    assert client.get_station_data().raw["stations"][0]["stnNm"] == "서울"
    assert client.get_station_info().raw["stationInfo"][0]["stnCd"] == "0001"
    assert client.get_train_calendar().raw["days"][0]["runDt"] == "20260710"
    assert client.get_common_code("login").raw["idx"] == "IDX-N"
    assert any(path == "/classes/com.korail.mobile.common.code.do" for _, path, _ in captured)


def test_search_trains_maps_rows(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.seatMovie.ScheduleView": "schedule_view_success.json"},
    )

    result = client.search_trains(
        TrainSearchQuery(
            departure_station_code="0001",
            arrival_station_code="0020",
            departure_date="20260710",
            departure_time="060000",
        )
    )

    assert result.response.h_msg_cd == "IRG000000"
    assert result.trains[0].train_no == "00123"
    posted_body = captured[0][2]
    assert "Sid=" in posted_body
    assert "txtGoStart=0001" in posted_body
    assert "txtGoEnd=0020" in posted_body


def test_history_and_ticket_list_are_read_only(load_json_fixture):
    client, _ = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.reservation.ReservationView": "reservation_history_empty.json",
            "/classes/com.korail.mobile.myTicket.MyTicketList": "ticket_list_empty.json",
        },
    )

    assert client.get_reservation_history().raw["reservations"] == []
    assert client.get_ticket_list().raw["tickets"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client_read_apis.py -q`

Expected: FAIL because read methods are missing.

- [ ] **Step 3: Implement read-only methods**

Do not modify `src/korail_mobile_api/http.py` in this step. Task 2 already defines `KorailHttpClient.get_json(self, path: str, params: Mapping[str, Any] | None = None, *, include_common: bool = True, raise_on_fail: bool = True)` and `KorailHttpClient.post_form(self, path: str, data: Mapping[str, Any], *, include_common: bool = True, raise_on_fail: bool = True)`; the client methods below must pass `raise_on_fail=False` for read endpoints whose empty-success responses do not use a normal success envelope.

Modify `src/korail_mobile_api/models.py` to add `TrainSummary.from_raw`:

```python
    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "TrainSummary":
        return cls(
            train_no=str(raw.get("h_trn_no") or raw.get("trnNo") or ""),
            train_group_code=raw.get("h_trn_gp_cd") or raw.get("trnGpCd"),
            departure_station_code=raw.get("h_dpt_rs_stn_cd") or raw.get("dptRsStnCd"),
            arrival_station_code=raw.get("h_arv_rs_stn_cd") or raw.get("arvRsStnCd"),
            departure_date=raw.get("h_dpt_dt") or raw.get("dptDt"),
            departure_time=raw.get("h_dpt_tm") or raw.get("dptTm"),
            arrival_time=raw.get("h_arv_tm") or raw.get("arvTm"),
            raw=raw,
        )
```

Modify `src/korail_mobile_api/client.py`:

```python
from .crypto import generate_sid
from .http import parse_base_response
from .models import BaseKorailResponse, TrainSearchQuery, TrainSearchResult, TrainSummary

    def get_common_code(self, code: str = "") -> BaseKorailResponse:
        return self.http.post_form("/classes/com.korail.mobile.common.code.do", {"code": code}, raise_on_fail=False)

    def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
        return self.http.get_json("/classes/com.korail.mobile.common.stationinfo", {"Device": device}, raise_on_fail=False)

    def get_station_data(self) -> BaseKorailResponse:
        return self.http.get_json("/classes/com.korail.mobile.common.stationdata", raise_on_fail=False)

    def get_train_calendar(self) -> BaseKorailResponse:
        return self.http.get_json("/classes/com.korail.mobile.schedule.runDt", raise_on_fail=False)

    def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
        response = self.http.post_form(
            "/classes/com.korail.mobile.seatMovie.ScheduleView",
            {
                "Sid": generate_sid(),
                "txtMenuId": "11",
                "radJobId": "1",
                "selGoTrain": query.train_group_code,
                "txtTrnGpCd": query.train_group_code,
                "txtGoTrnNo": "",
                "txtGoStart": query.departure_station_code,
                "txtGoEnd": query.arrival_station_code,
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
                "txtJobDv": "",
                "etrPath": "",
                "srtCheckYn": "Y" if query.include_srt else "N",
            },
            raise_on_fail=False,
        )
        rows = response.raw.get("trn_infos") or response.raw.get("trnInfos") or []
        trains = [TrainSummary.from_raw(row) for row in rows if isinstance(row, dict)]
        return TrainSearchResult(trains=trains, response=response, raw=response.raw)

    def get_train_schedule(self, run_date: str, train_no: str) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
            {"runDt": run_date, "trnNo": train_no},
            include_common=False,
            raise_on_fail=False,
        )

    def get_transfer_stations(self, departure_station_code: str, arrival_station_code: str) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {"dptRsStnCd": departure_station_code, "arvRsStnCd": arrival_station_code},
            raise_on_fail=False,
        )

    def get_reservation_history(self) -> BaseKorailResponse:
        return self.http.get_json("/classes/com.korail.mobile.reservation.ReservationView", include_common=True, raise_on_fail=False)

    def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
        return self.http.post_form(
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            {"txtIndex": str(page_no), "h_page_no": str(page_no)},
            raise_on_fail=False,
        )
```

- [ ] **Step 4: Run read API tests**

Run: `pytest tests/test_client_read_apis.py -q`

Expected: PASS.

- [ ] **Step 5: Run all tests**

Run: `pytest -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/korail_mobile_api tests/fixtures tests/test_client_read_apis.py
git commit -m "feat: add korail read api facade"
```

---

### Task 5: Live Smoke Boundary And Documentation

**Files:**
- Create: `src/korail_mobile_api/live.py`
- Create: `tests/test_live.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `KorailClient`, `KorailConfig`.
- Produces: `run_live_smoke_from_env()` and user-facing docs for safe live execution.

- [ ] **Step 1: Write failing live boundary tests**

Create `tests/test_live.py`:

```python
import os

from korail_mobile_api.live import live_enabled, read_credentials_from_env


def test_live_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KORAIL_MOBILE_API_LIVE", raising=False)
    assert live_enabled() is False


def test_live_enabled_only_with_explicit_flag(monkeypatch):
    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    assert live_enabled() is True


def test_credentials_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "pw")
    assert read_credentials_from_env() == ("member", "pw")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_live.py -q`

Expected: FAIL because `live.py` is missing.

- [ ] **Step 3: Implement live boundary**

Create `src/korail_mobile_api/live.py`:

```python
from __future__ import annotations

import os
from typing import Any

from .client import KorailClient
from .config import KorailConfig


def live_enabled() -> bool:
    return os.environ.get("KORAIL_MOBILE_API_LIVE") == "1"


def read_credentials_from_env() -> tuple[str, str]:
    member_no = os.environ.get("KORAIL_MEMBER_NO")
    password = os.environ.get("KORAIL_PASSWORD")
    if not member_no or not password:
        raise RuntimeError("KORAIL_MEMBER_NO and KORAIL_PASSWORD are required for live smoke")
    return member_no, password


def run_live_smoke_from_env() -> dict[str, Any]:
    if not live_enabled():
        raise RuntimeError("Set KORAIL_MOBILE_API_LIVE=1 to run live smoke")
    member_no, password = read_credentials_from_env()
    client = KorailClient(KorailConfig())
    try:
        session = client.login(member_no, password)
        station_data = client.get_station_data()
        calendar = client.get_train_calendar()
        return {
            "loggedIn": bool(session.jsessionid),
            "stationDataCode": station_data.h_msg_cd,
            "calendarCode": calendar.h_msg_cd,
        }
    finally:
        client.close()
```

Modify `README.md` by adding:

```markdown
## Python Package MVP

This repository now contains an installable Python client package under `src/korail_mobile_api`.

Default tests are offline:

```bash
pip install -e ".[test]"
pytest
```

Live smoke is opt-in and limited to login plus read/query calls:

```bash
export KORAIL_MOBILE_API_LIVE=1
export KORAIL_MEMBER_NO="<member-no>"
export KORAIL_PASSWORD="<password>"
python -c "from korail_mobile_api.live import run_live_smoke_from_env; print(run_live_smoke_from_env())"
```

Reservation, payment, refund, check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this package version.
```

- [ ] **Step 4: Run live boundary tests**

Run: `pytest tests/test_live.py -q`

Expected: PASS.

- [ ] **Step 5: Run full verification**

Run:

```bash
pytest -q
python -c "from korail_mobile_api import KorailClient, KorailConfig; print(KorailClient(KorailConfig()).config.base_url)"
```

Expected: all tests PASS and command prints `https://smart.letskorail.com`.

- [ ] **Step 6: Commit**

```bash
git add README.md src/korail_mobile_api/live.py tests/test_live.py
git commit -m "feat: add korail live smoke boundary"
```
