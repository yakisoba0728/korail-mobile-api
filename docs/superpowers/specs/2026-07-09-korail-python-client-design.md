# KORAIL Python Client Library Design

Date: 2026-07-09

## Goal

Create the first Python package scaffold and login/read-only API client for the KORAIL mobile API analysis repository.

The package must be shaped to match the future SRT package, while keeping KORAIL-specific protocol details isolated inside this repository.

## Fixed Decisions

- Distribution package name: `korail-mobile-api`
- Python import package: `korail_mobile_api`
- Runtime stack: `httpx`, `dataclasses`, `pytest`
- Package layout: `src/korail_mobile_api/`
- MVP includes login and safe read/query APIs only.
- Reservation, payment, refund, check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this version.
- Dangerous endpoints must not appear as public stub methods in this version.
- Default tests must be offline and non-destructive.
- Live smoke must require credentials and an explicit live opt-in environment variable.

## Source Evidence

Primary source documents:

- `README.md`
- `docs/library-build-guide.md`
- `docs/api-status-by-service.md`
- `docs/deep-dive/README.md`
- `docs/deep-dive/api-contracts.md`
- `docs/deep-dive/agent-reports/02-network-core.md`
- `docs/deep-dive/agent-reports/03-login-account-nfilter.md`
- `docs/deep-dive/agent-reports/04-common-station-crypto.md`
- `docs/deep-dive/agent-reports/05-train-search-schedule.md`
- `docs/deep-dive/agent-reports/16-antiautomation-queue-security.md`

The final endpoint inventory is `165` Retrofit method entries and `159` distinct HTTP+path pairs. Do not use stale `164`/`158` counts from historical audit text.

## Package Structure

Create this structure:

```text
pyproject.toml
src/korail_mobile_api/
  __init__.py
  client.py
  config.py
  crypto.py
  errors.py
  http.py
  live.py
  models.py
  redaction.py
  safety.py
  session.py
tests/
  fixtures/
  test_*.py
```

File responsibilities:

- `client.py`: public `KorailClient` facade.
- `config.py`: `KorailConfig` dataclass with host, app version, client key, timeout, user agent, and live-test options.
- `http.py`: thin `httpx.Client` wrapper with form/query helpers, common fields, cookies, timeout, and `MockTransport` injection.
- `session.py`: login/logout/session state helpers and `JSESSIONID` tracking.
- `crypto.py`: login password transform and `Sid` generation.
- `models.py`: dataclass request/response/result models with `raw: dict` escape hatches.
- `errors.py`: transport, protocol, app-level, authentication, and parsing exceptions.
- `redaction.py`: masking helpers for credentials, cookies, PNR/ticket identifiers, card-like values, and raw response text.
- `safety.py`: constants and documentation helpers for excluded dangerous domains. It must not expose callable destructive API stubs.
- `live.py`: optional live smoke helpers, excluded from default tests.

## Public API

Expose from `korail_mobile_api.__init__`:

```python
from .client import KorailClient
from .config import KorailConfig
from .errors import KorailApiError, KorailAuthError, KorailProtocolError
from .models import (
    KorailSession,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
)
```

MVP public methods on `KorailClient`:

- `login(member_no: str, password: str, *, input_flag: str = "2") -> KorailSession`
- `logout() -> None`
- `clear_session() -> None`
- `get_common_code(code: str = "")`
- `get_station_info(device: str = "AD")`
- `get_station_data()`
- `get_train_calendar()`
- `search_trains(query: TrainSearchQuery) -> TrainSearchResult`
- `get_train_schedule(run_date: str, train_no: str)`
- `get_transfer_stations(departure_station_code: str, arrival_station_code: str)`
- `get_reservation_history()`
- `get_ticket_list(page_no: int = 0)`

Receipt lookup may be added only if it can be kept read-only and fixture-backed without requiring real ticket identifiers in the repository. If real PNR/ticket identifiers are required, keep it out of MVP.

Do not add public methods for:

- reservation create/change/cancel/wait
- payment or payment-provider flows
- cash receipt issue
- refund or return
- check-in register/cancel
- member drop
- push/SMS sending
- point, mileage, or RailPlus mutation
- DynaPath bypass/token generation

## Runtime Contract

Defaults:

- Base host: `https://smart.letskorail.com`
- Common fields: `Device=AD`, `Version=250601003`, `Key=korail1234567890`
- Form encoding: `application/x-www-form-urlencoded; charset=UTF-8`
- Timeout: 60 seconds connect/read equivalent
- Response envelope: `h_msg_cd`, `h_msg_txt`, `strResult`

Login:

- Endpoint: `POST /classes/com.korail.mobile.login.Login`
- Fields include `txtMemberNo`, transformed `txtPwd`, `txtInputFlg`, `checkValidPw`, `custId`, `etrPath`, and `idx`.
- Password transform uses common-code login metadata:
  - if `pwdAESCphd == "Y"`, use AES/CBC/PKCS5Padding with IV `key[:16]`, then outer Base64;
  - otherwise use Base64 password only.
- Store session cookies in `httpx` cookie state. Android WebView cookie mirroring is out of scope.

Train inquiry:

- `Sid` is separate from DynaPath.
- `Sid` is AES/CBC over `"AD" + epoch_ms` using key/IV `2485dd54d9deaa36`, then Base64.
- DynaPath is an optional header-provider boundary only. SDK token generation is opaque and not implemented.

## Safety Requirements

Copy these KORAIL safety defaults into implementation docs/tests:

| 분류 | 기본 동작 |
|---|---|
| 조회성 API | 실제 호출 허용 가능. 단, 계정/티켓 개인정보 로그 마스킹 |
| 예약 생성/취소/변경 | 기본 비활성화. 명시적 opt-in과 dry-run marker 필요 |
| 결제/포인트/현금영수증 발급 | 기본 비활성화. 테스트 카드라도 운영 PG endpoint 직접 호출 금지 |
| 환불/반환/체크인/회원탈퇴 | 기본 비활성화. 별도 confirmation token 필요 |
| PNR/발권번호/N카드 기반 API | 실제 값 없으면 schema-only 테스트만 수행 |

For this MVP, the excluded categories are not implemented at all.

## Test Strategy

Default command:

```bash
pytest
```

Default tests must not access the network.

Use `httpx.MockTransport` for:

- common field injection
- form/query encoding
- cookie persistence
- login success/failure
- login password transform for `pwdAESCphd=Y` and `pwdAESCphd=N`
- deterministic `Sid` generation with frozen time
- base envelope parsing
- app-level failure mapping
- train search parsing
- station/common/cache parsing
- reservation history empty response
- ticket list empty response
- redaction of member id, password, cookies, PNR/ticket identifiers, card-like values, and raw response text
- DynaPath 403 parsing as a protocol error message, without implementing token generation

Suggested sanitized fixtures:

- `common_code_login_crypto_y.json`
- `common_code_login_crypto_n.json`
- `station_info.json`
- `station_data.json`
- `train_calendar.json`
- `login_success.json`
- `schedule_view_success.json`
- `reservation_history_empty.json`
- `ticket_list_empty.json`
- `dynapath_403.json`

Live tests:

- Must be marked `pytest.mark.live`.
- Must require `KORAIL_MOBILE_API_LIVE=1`.
- Must require credentials from environment variables.
- Must only perform login and read/query calls.
- Must never call reservation, payment, refund, check-in, or membership mutation endpoints.
- Must not persist raw responses inside the repository.

## Agent Execution Model

Implementation will be delegated by task to subagents.

Worker ownership:

- KORAIL workers may edit only files under `korail-mobile-api`.
- Workers must not modify SRT files.
- Each task must have a disjoint or clearly owned write set.
- Reviewers check both spec compliance and code quality after each task.

The orchestrator keeps cross-repo consistency for public API naming, package structure, test policy, and live opt-in behavior.

## Risks And Open Gaps

- The repository currently has no Python scaffold or `pyproject.toml`.
- Runtime response samples, required/optional server validation rules, redirects, session expiry, and feature flags remain unknown.
- Some `FieldMap`/`QueryMap` flows need further schema work before high-level wrappers.
- DynaPath token generation is SDK-opaque and intentionally out of scope.
- Receipt APIs may require real ticket identifiers; keep them out of MVP unless offline-safe fixtures and API semantics are clear.
