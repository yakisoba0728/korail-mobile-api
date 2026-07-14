# KORAIL Successful Read Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add eleven public, typed, repr-safe KORAIL reads covering all previously successful but unimplemented endpoints plus the existing service-status cache route.

**Architecture:** Keep `KorailClient`, `KorailHttpClient`, and the fail-closed route boundary as integration points. Put the new immutable models, exact request builders, and parsers into `read_models.py`, `read_payloads.py`, and `read_parsers.py`, then re-export the public types. Add ten routes and exact final query/form field contracts while leaving the DynaPath algorithm and allowlist unchanged.

**Tech Stack:** Python 3.11+, dataclasses, httpx, pytest, setuptools/build.

## Global Constraints

- Implement the approved design in `docs/superpowers/specs/2026-07-14-korail-successful-read-expansion-design.md` exactly.
- Add eleven public methods and ten route tuples; `KORAIL_READ_ONLY_ROUTES` must contain exactly twenty-five entries.
- Do not add reservation, payment, refund, cancellation, check-in, member mutation, point/mileage mutation, push/SMS, or other side-effect routes.
- Explicitly disable DynaPath on all eleven reads. Do not modify `DYNAPATH_ALLOWLIST_PATHS` or the token generator.
- Use synthetic fixtures only. Do not issue live requests or retain production response text.
- Raw mappings and sensitive identifiers remain caller-accessible but excluded from `repr()`.
- Accept only the evidenced empty-result codes `WRG000000` for coupons and `P100` for reservation history.
- Follow red-green-refactor. Observe every new production behavior fail before implementing it.
- Perform one whole-feature review after all implementation families are complete, then one consolidated fix pass.

## File Structure

- Create `src/korail_mobile_api/read_models.py` for all new frozen public models.
- Create `src/korail_mobile_api/read_payloads.py` for exact validated request builders.
- Create `src/korail_mobile_api/read_parsers.py` for typed response parsing.
- Create `tests/test_successful_read_expansion.py` for the consolidated feature contract.
- Create one sanitized fixture per response family under `tests/fixtures/`.
- Modify `src/korail_mobile_api/safety.py`, `http.py`, `client.py`, and `__init__.py` only at their existing integration boundaries.
- Modify public contract, transport, redaction, README, and progress tests/documents without reorganizing unrelated code.

---

### Task 1: Implement all eleven reads as one TDD feature

**Files:**
- Create: `src/korail_mobile_api/read_models.py`
- Create: `src/korail_mobile_api/read_payloads.py`
- Create: `src/korail_mobile_api/read_parsers.py`
- Create: `tests/test_successful_read_expansion.py`
- Create: `tests/fixtures/service_status_success.json`
- Create: `tests/fixtures/cart_list_success.json`
- Create: `tests/fixtures/deposit_banks_success.json`
- Create: `tests/fixtures/delay_discount_tickets_success.json`
- Create: `tests/fixtures/discount_coupons_success.json`
- Create: `tests/fixtures/pass_availability_success.json`
- Create: `tests/fixtures/trip_menu_success.json`
- Create: `tests/fixtures/product_reservations_success.json`
- Create: `tests/fixtures/product_detail_success.json`
- Create: `tests/fixtures/ticket_receipt_success.json`
- Create: `tests/fixtures/reservation_history_success.json`
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/http.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Modify: `tests/test_http.py`
- Modify: `tests/test_public_contract.py`
- Modify: `tests/test_redaction_safety.py`

**Interfaces:**
- Consumes: `KorailHttpClient.get_json()`, `KorailHttpClient.post_form()`, `KorailClient._run_read()`, `KorailSessionClient.current`, `BaseKorailResponse`, and existing typed errors.
- Produces: the eleven methods and eleven response types defined by the approved design; exact GET/POST safety-field contracts; `routes=25`.

- [ ] **Step 1: Write one consolidated failing public/request/safety test file**

Create the test file around these exact method and route tables:

```python
PUBLIC_METHODS = {
    "get_service_status": ["self", "timestamp_ms"],
    "get_cart_list": ["self", "pnr_no", "additional_service_request_no"],
    "get_deposit_banks": ["self"],
    "get_delay_discount_tickets": ["self", "departure_date_to"],
    "get_discount_coupons": ["self", "page_no", "pnr_no"],
    "get_pass_available_dates": ["self", "kind_code", "period_code", "age_code"],
    "get_trip_menu": ["self"],
    "get_product_reservations": ["self", "page_no", "page_size"],
    "get_product_detail": ["self", "reservation_no", "reservation_sequence"],
    "get_ticket_receipt": [
        "self", "sale_date", "window_no", "sale_sequence", "return_password"
    ],
    "get_reservation_history": ["self"],
}

NEW_ROUTES = {
    ("POST", "/classes/com.korail.mobile.cart.showCartList"),
    ("POST", "/classes/com.korail.mobile.dlay.dptnBank.do"),
    ("POST", "/classes/com.korail.mobile.passCard.DelayDiscountView"),
    ("POST", "/classes/com.korail.mobile.passCard.CouponView"),
    ("POST", "/classes/com.korail.mobile.pass.passInfoList"),
    ("POST", "/classes/com.korail.mobile.pass.trGdMenuLt.do"),
    ("GET", "/classes/com.korail.mobile.product.ReservationList"),
    ("GET", "/classes/com.korail.mobile.product.ReservationDetail"),
    ("POST", "/classes/com.korail.mobile.receipt.ReceiptInfo"),
    ("GET", "/classes/com.korail.mobile.reservation.ReservationView"),
}

EXACT_FIELDS = {
    "/file/CACHE/MobileService.cache": {"timeStamp"},
    "/classes/com.korail.mobile.cart.showCartList": {
        "Device", "Version", "Key", "pnrNo", "addSrvReqNo"
    },
    "/classes/com.korail.mobile.dlay.dptnBank.do": {"Device", "Version", "Key"},
    "/classes/com.korail.mobile.passCard.DelayDiscountView": {
        "Device", "Version", "Key", "dptDtTo"
    },
    "/classes/com.korail.mobile.passCard.CouponView": {
        "Device", "Version", "Key", "txtSelPage", "pnrNo"
    },
    "/classes/com.korail.mobile.pass.passInfoList": {
        "Device", "Version", "Key", "txtCmtrKndCd", "txtCmtrUtlTrmCd",
        "txtCmtrUtlAgeCd"
    },
    "/classes/com.korail.mobile.pass.trGdMenuLt.do": {"Device", "Version"},
    "/classes/com.korail.mobile.product.ReservationList": {
        "Device", "Version", "Key", "txtSelPage", "txtCntPerPage"
    },
    "/classes/com.korail.mobile.product.ReservationDetail": {
        "Device", "Version", "Key", "txtVrRsNo", "txtVrRsvSqNo"
    },
    "/classes/com.korail.mobile.receipt.ReceiptInfo": {
        "Device", "Version", "Key", "h_orgtk_sale_dt", "h_orgtk_wct_no",
        "h_orgtk_sale_sqno", "h_orgtk_tk_ret_pwd"
    },
    "/classes/com.korail.mobile.reservation.ReservationView": {
        "Device", "Version", "Key"
    },
}
```

Tests must assert:

```python
def test_successful_read_routes_have_exact_final_fields():
    assert len(KORAIL_READ_ONLY_ROUTES) == 25
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    for path, fields in EXACT_FIELDS.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == fields

def test_new_public_methods_have_exact_signatures_and_return_hints():
    for name, parameters in PUBLIC_METHODS.items():
        method = getattr(KorailClient, name)
        assert list(inspect.signature(method).parameters) == parameters
        assert get_type_hints(method)["return"].__module__ == "korail_mobile_api.read_models"
```

Add parameterized request tests with `httpx.MockTransport` that assert exact
method, path, final query/form mapping, one request, no DynaPath header, and no
adjacent request for all eleven methods. Add pre-I/O validation tests for:

```python
INVALID_CALLS = (
    ("get_service_status", (True,)),
    ("get_delay_discount_tickets", ("２０２６０７１４",)),
    ("get_discount_coupons", (0, "")),
    ("get_pass_available_dates", ("", "P", "A")),
    ("get_product_reservations", (1, 0)),
    ("get_product_detail", ("", "1")),
    ("get_ticket_receipt", ("20260714", "", "1", "pw")),
)
```

Authenticated-method tests must assert `KorailAuthError` and zero transport
calls before login. Account-neutral methods must be callable without a session.

- [ ] **Step 2: Run the consolidated contract tests and verify RED**

Run:

```bash
pytest -q tests/test_successful_read_expansion.py tests/test_http.py tests/test_public_contract.py tests/test_redaction_safety.py
```

Expected: failures for missing `read_models`, public methods, ten routes, exact
query validation, and fixtures. Fix only test import/setup mistakes until those
are the observed reasons.

- [ ] **Step 3: Implement exact payload and transport safety infrastructure**

Create request builders with these exact signatures:

```python
def build_service_status_query(timestamp_ms: int | None = None) -> dict[str, str]
def build_cart_list_form(pnr_no: str = "", additional_service_request_no: str = "") -> dict[str, str]
def build_delay_discount_ticket_form(departure_date_to: str) -> dict[str, str]
def build_discount_coupon_form(page_no: int = 1, pnr_no: str = "") -> dict[str, str]
def build_pass_availability_form(kind_code: str, period_code: str, age_code: str) -> dict[str, str]
def build_trip_menu_form(config: KorailConfig) -> dict[str, str]
def build_product_reservations_query(page_no: int = 1, page_size: int = 20) -> dict[str, str]
def build_product_detail_query(reservation_no: str, reservation_sequence: str) -> dict[str, str]
def build_ticket_receipt_form(sale_date: str, window_no: str, sale_sequence: str, return_password: str) -> dict[str, str]
```

Use these validation helpers and exact rules:

```python
def _positive_int(value: int, name: str) -> str:
    if type(value) is not int or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return str(value)

def _required_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value

def _ascii_date(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 8 or any(ch < "0" or ch > "9" for ch in value):
        raise ValueError(f"{name} must use ASCII YYYYMMDD")
    return value
```

In `safety.py`, add the ten exact route tuples and one combined mapping named
`KORAIL_EXACT_REQUEST_FIELDS` containing the eleven paths and field sets from
Step 1. Replace the form-only assertion with:

```python
def assert_read_only_request_fields(path: str, values: Mapping[str, Any]) -> None:
    allowed = KORAIL_EXACT_REQUEST_FIELDS.get(urlsplit(path).path)
    if allowed is None:
        return
    if set(values) != allowed:
        raise KorailProtocolError("KORAIL request fields must exactly match the registered read-only contract")
    if any(type(value) not in {str, int} for value in values.values()):
        raise KorailProtocolError("KORAIL request values must be scalar strings or integers")
```

Call it from `post_form()` and `get_json()` after common-field composition and
before transport. Existing MAAS menu exact-field tests must continue passing.
Preserve `KORAIL_EXACT_FORM_FIELDS` as a compatibility alias for existing
imports while using the combined mapping internally. Do not change DynaPath
code or constants.

- [ ] **Step 4: Run request/safety tests and verify GREEN for the boundary**

Run:

```bash
pytest -q tests/test_http.py tests/test_successful_read_expansion.py -k 'payload or request or route or field or dynapath or validation or auth'
```

Expected: request builders, validation, route count, exact field sets, auth
preconditions, and no-DynaPath tests pass. Parser/model tests remain RED.

- [ ] **Step 5: Add synthetic fixtures and failing parser/model/redaction tests**

Each fixture must contain `h_msg_cd`, `h_msg_txt`, and `strResult` plus only
synthetic values. Use the exact wrapper keys below:

```python
FIXTURE_WRAPPERS = {
    "cart_list_success.json": ("cart_infos", "cart_info"),
    "deposit_banks_success.json": ("dptnBank", None),
    "delay_discount_tickets_success.json": ("disc_infos", "disc_info"),
    "discount_coupons_success.json": ("coupon_infos", "coupon_info"),
    "pass_availability_success.json": ("pass_info", "ticket_info", "wct_info"),
    "trip_menu_success.json": ("menuList", None),
    "product_reservations_success.json": ("mainInfo", "entity"),
    "product_detail_success.json": ("mainInfo", "entityOne"),
    "ticket_receipt_success.json": ("receipt_infos", "receipt_info"),
    "reservation_history_success.json": ("jrny_infos", "jrny_info"),
}
```

Tests must cover all public fields from the design, tuple immutability, raw
identity, nested wrapper normalization, and sensitive repr exclusion. Explicit
secret sentinels must include:

```python
SECRET_SENTINELS = {
    "SYNTHETIC-PNR-SECRET",
    "SYNTHETIC-RETURN-PASSWORD",
    "SYNTHETIC-CARD-NUMBER",
    "SYNTHETIC-ACCOUNT-NUMBER",
    "SYNTHETIC-APPROVAL-NUMBER",
    "SYNTHETIC-RESERVATION-NUMBER",
    "SYNTHETIC-RAW-SECRET",
}
```

Assert none appears in `repr(response)` or `repr(item)`, while each remains
accessible through its typed field or `raw` mapping. Add wrong-type cases for
wrapper, list, item, and numeric values; accept integer and ASCII-decimal string
numeric inputs but reject booleans and non-decimal strings.

Add route-specific empty-result tests:

```python
def test_coupon_no_data_is_typed_empty():
    result = parse_discount_coupon_response({
        "h_msg_cd": "WRG000000", "h_msg_txt": "no data", "strResult": "FAIL"
    })
    assert result.items == ()

def test_history_no_data_is_typed_empty():
    result = parse_reservation_history_response({
        "h_msg_cd": "P100", "h_msg_txt": "no data", "strResult": "FAIL"
    })
    assert result.items == ()
```

- [ ] **Step 6: Run parser/model tests and verify RED**

Run:

```bash
pytest -q tests/test_successful_read_expansion.py tests/test_redaction_safety.py -k 'parse or model or repr or empty or numeric'
```

Expected: failures for missing response/item dataclasses and parser functions.

- [ ] **Step 7: Implement models, parsers, client methods, and exports**

Create every model named in the design. All dataclasses use `frozen=True`; raw
and these sensitive fields use `field(default=None, repr=False)` or an
equivalent required repr-hidden declaration:

```python
SENSITIVE_FIELDS = {
    "partner_reservation_no", "pnr_no", "lump_sum_target_no", "customer_no",
    "virtual_reservation_no", "original_sale_date", "window_no",
    "sale_sequence", "return_password", "coupon_no", "url", "image",
    "member_card_no", "account_no", "approval_no", "card_no", "point_no",
}
```

Implement these parser entry points:

```python
def parse_service_status_response(raw: Mapping[str, Any]) -> ServiceStatusResponse
def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse
def parse_deposit_bank_response(raw: Mapping[str, Any]) -> DepositBankListResponse
def parse_delay_discount_ticket_response(raw: Mapping[str, Any]) -> DelayDiscountTicketListResponse
def parse_discount_coupon_response(raw: Mapping[str, Any]) -> DiscountCouponListResponse
def parse_pass_availability_response(raw: Mapping[str, Any]) -> PassAvailabilityResponse
def parse_trip_menu_response(raw: Mapping[str, Any]) -> TripMenuResponse
def parse_product_reservation_list_response(raw: Mapping[str, Any]) -> ProductReservationListResponse
def parse_product_detail_response(raw: Mapping[str, Any]) -> ProductDetailResponse
def parse_ticket_receipt_response(raw: Mapping[str, Any]) -> TicketReceiptResponse
def parse_reservation_history_response(raw: Mapping[str, Any]) -> ReservationHistoryResponse
```

Use shared private helpers for mapping/list/string/integer validation. Parse
only the fields listed in the approved design and preserve every source mapping
as repr-hidden raw. Flatten reservation-history train lists while keeping the
original hierarchy only in response raw.

Implement the eleven exact `KorailClient` signatures from the design. For each
authenticated method, call one `_require_session()` helper before payload
construction. Each method must pass `include_dynapath=False`; trip menu passes
`include_common=False`; product/history GET calls pass `include_common=True`;
other common-field POST calls use the existing default. For coupon/history,
call HTTP with `raise_on_fail=False` so the focused parser can admit only the
two evidenced empty codes. Each method issues exactly one HTTP request and
returns its focused parser result.

Export all item and response types from `korail_mobile_api.__init__`. Update the
exact public-method set in `tests/test_public_contract.py` from seventeen to
twenty-eight methods.

- [ ] **Step 8: Run the consolidated feature gate and verify GREEN**

Run:

```bash
pytest -q tests/test_successful_read_expansion.py tests/test_http.py tests/test_public_contract.py tests/test_redaction_safety.py tests/test_client_read_apis.py tests/test_cache_read_apis.py tests/test_uuid_maas_read_apis.py
```

Expected: all selected tests pass with no live-service execution.

- [ ] **Step 9: Commit the complete implementation feature**

Stage only the new feature source, fixtures, and tests, then commit:

```bash
git commit -m "feat: add verified korail read APIs"
```

### Task 2: Document, review once, fix once, and verify the complete feature

**Files:**
- Modify: `README.md`
- Modify: `docs/api-status-by-service.md`
- Modify: `docs/library-build-guide.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`
- Modify: `/Users/yakisoba/Documents/GitHub/NEXT_SESSION_PROMPT.md`
- Modify: implementation/test files only when the final review identifies a confirmed issue

**Interfaces:**
- Consumes: the committed Task 1 implementation and actual verification output.
- Produces: canonical documentation, one reviewed final implementation, package artifacts verified in temporary paths, and a clean repository.

- [ ] **Step 1: Write failing documentation/public-surface assertions**

Extend `tests/test_readme.py` to require every new public method name, the
twenty-five-route statement, no-live-replay statement, and a minimal example
that obtains a product detail only from caller-owned identifiers. In the same
file, add a status-document assertion that requires current counts `25 success
/ 8 failure / 132 unexecuted` and package coverage `25 routes` without
rewriting historical runtime results.

- [ ] **Step 2: Run documentation tests and verify RED**

Run:

```bash
pytest -q tests/test_readme.py tests/test_public_contract.py
```

Expected: README/progress coverage assertions fail because documentation has
not yet been updated.

- [ ] **Step 3: Update README and canonical progress documents**

Document:

```text
11 new methods
25 exact login/read routes
no new DynaPath route
no live replay
typed empty results for WRG000000 and P100
caller-owned identifiers only
reservation/payment/mutation routes remain excluded
```

Correct `docs/library-build-guide.md` from stale `24 / 8 / 133` to `25 / 8 /
132`. In `docs/api-status-by-service.md`, preserve runtime status and add package
coverage notes. Record only actual test/build/import/review output in
`docs/IMPLEMENTATION_PROGRESS.md` and the shared handoff.

- [ ] **Step 4: Run the full offline and package verification gates**

Run the full suite once:

```bash
pytest -q
```

Expected: all offline tests pass and only `tests/test_live_service.py` is
skipped because no opt-in is set.

Build once into a temporary directory, install the wheel into a fresh temporary
virtual environment, change outside the repository, and import
`KorailClient` plus all eleven new response types. Confirm:

```text
routes=25
public_methods=28
wheel import path contains site-packages
```

Run `git diff --check` and a static excluded-route scan across `src/` and
scripts. Do not invoke the live helper.

- [ ] **Step 5: Perform one final whole-feature review and one fix pass**

Review the full diff from the design commit through current HEAD for:

```text
exact method/path/field contracts
authentication boundaries
empty-result policy
parser shape validation
repr/error redaction
DynaPath non-regression
mutation route exclusion
public API/type consistency
documentation accuracy
```

Apply all confirmed Critical and Important findings in one consolidated TDD fix
pass. Add a failing regression test for every code behavior fix, run it RED,
implement the fix, and run the focused gate GREEN. Do not perform per-family
review loops.

- [ ] **Step 6: Re-run the final evidence gate after review fixes**

Run `pytest -q`, the exact `routes=25` and `public_methods=28` checks,
`git diff --check`, excluded-route scan, and package build/isolated import if a
source or packaging file changed during the fix pass. Record the fresh output;
do not reuse pre-fix results.

- [ ] **Step 7: Commit final review fixes and documentation**

Use one fix commit when needed:

```bash
git commit -m "fix: harden verified korail reads"
```

Then stage documentation and commit:

```bash
git commit -m "docs: record korail read expansion"
```

Finish with a clean tracked worktree, no generated `dist/`, `build/`,
`*.egg-info`, temporary virtual environment, or captured response artifact.
