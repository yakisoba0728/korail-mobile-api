# KORAIL Seat Inventory Reads Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add two strictly bounded authenticated KORAIL read APIs for general-class car and seat inventory, then perform one sanitized live verification.

**Architecture:** Closed payload builders derive server-owned train fields from `TrainSummary`, safety registers exact production forms, and two client methods issue one DynaPath-disabled POST each. Frozen repr-safe models and route-specific parsers expose documented response structure; a separate live script emits counts and booleans only.

**Tech Stack:** Python 3.11+, dataclasses, httpx through existing transport, pytest, existing Sid generator and release verifier.

## Global Constraints

- Add only `POST /classes/com.korail.mobile.research.TrainResearch` and `POST /classes/com.korail.mobile.research.TResidualSeatsResearch.do`.
- Production omits `sidTest`; each request generates one fresh `Sid`.
- Both calls use `include_common=False` and `include_dynapath=False`, including under custom DynaPath allowlists.
- Fix menu `11`, room class `1`, seat attribute `015`, product number `""`, `isArrow="true"`, and control division `""`.
- No generic route/field escape hatch; no seat selection/hold, reservation, payment, cancellation, refund, or URL following.
- Validate before Sid generation and I/O; each public method issues exactly one request.
- Models are frozen and repr-safe; unknown documented codes remain strings without invented enum meaning.
- Set package version to `0.2.0`.

---

### Task 1: Typed car and seat inventory reads

**Files:**
- Create: `tests/fixtures/seat_car_list_success.json`
- Create: `tests/fixtures/seat_inventory_success.json`
- Create: `tests/test_seat_inventory_reads.py`
- Create: `scripts/capture_seat_inventory_evidence.py`
- Modify: `tests/test_public_contract.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/payloads.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `src/korail_mobile_api/safety.py`
- Modify: `src/korail_mobile_api/client.py`
- Modify: `src/korail_mobile_api/__init__.py`
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`

**Interfaces:**
- Consumes: `TrainSummary`, `KorailConfig`, `generate_sid`, `KorailHttpClient.post_form`, `BaseKorailResponse`.
- Produces: `SeatAttribute`, `SeatCar`, `SeatCarListResponse`, `PhysicalSeat`, `SeatWindow`, `SeatInventoryResponse`; `build_seat_car_form`, `build_seat_inventory_form`; `parse_seat_car_list_response`, `parse_seat_inventory_response`; `KorailClient.get_seat_cars`, `KorailClient.get_seat_inventory`.

- [ ] **Step 1: Write synthetic fixtures and failing model/parser tests**

The car fixture must contain the base envelope, recommended car, train number,
`srcar_infos.srcar_info[]`, and nested `seatAttInfos[]`. The seat fixture must
contain layout/count metadata, two seats with all eleven documented string
fields, two windows, and an inert synthetic URL. Use synthetic identifiers only.

Tests import all six new public types and both parsers, assert frozen dataclasses,
tuple collections, documented values, hidden raw/message/seat/train/URL repr,
unknown-code preservation, and failures for malformed containers, wrong scalar
types, negative counts, non-finite ratios, duplicate car numbers, duplicate seat
numbers, and `remaining_count > total_count`. Do not assert list length equals
`total_count`.

- [ ] **Step 2: Write failing payload, safety, and client tests**

Construct a complete synthetic `TrainSummary` with:

```python
TrainSummary(
    train_no="123",
    train_group_code="100",
    departure_station_code="0001",
    arrival_station_code="0020",
    departure_date="20260714",
    run_date="20260714",
    train_class_code="00",
    departure_run_order="000001",
    arrival_run_order="000010",
)
```

Assert the car form has exactly the 18 fields and the seat form exactly the 19
fields listed in the approved spec, with `sidTest` absent. Assert fixed values,
five-character `train.train_no.zfill(5)` in `txtTrnNo`/`trnNo`, and one
caller-provided Sid per builder. Reject bool/out-of-range passenger counts,
non-positive/bool car number, missing train fields, non-ASCII numeric/date/order
values, and malformed codes before calling a patched Sid generator or transport.

Safety tests must prove only the two exact POST forms pass, while missing/extra
fields, GET, duplicate prepared fields, wrong origins, and adjacent mutation
paths fail before DynaPath/token generation or I/O. Client tests assert session
required, fresh Sid per method, exactly one POST, `include_common=False`,
`include_dynapath=False`, and correct parser return type.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_seat_inventory_reads.py
```

Expected: import/attribute failures for the new interfaces.

- [ ] **Step 4: Implement append-only train fields and frozen models**

Append to `TrainSummary` and `from_raw`:

```python
run_date: str | None = None                 # h_run_dt / runDt
train_class_code: str | None = None         # h_trn_clsf_cd / trnClsfCd
departure_run_order: str | None = None      # h_dpt_stn_run_ordr / dptStnRunOrdr
arrival_run_order: str | None = None        # h_arv_stn_run_ordr / arvStnRunOrdr
```

Implement the six frozen response types exactly as the spec. Use `repr=False`
for raw mappings, messages, seat/train identifiers, and URLs. Keep existing
constructors backward-compatible through defaults.

- [ ] **Step 5: Implement closed builders and strict parsers**

Builders must use direct Retrofit field names for the car route and the exact
unprefixed seat-route names from the spec. Validate all train fields as nonempty
ASCII digit strings with documented lengths where existing tests establish
them; use `train.train_no.zfill(5)` consistently with existing KORAIL train
requests. Insert one supplied Sid and never generate it inside the builder.

Add one shared `validate_seat_inventory_inputs(train, passenger_count, *,
car_no=None) -> None` helper. Client methods call it before `generate_sid`;
builders call it again defensively before returning the closed form. Thus every
caller-controlled validation failure is proven to occur before Sid generation
and transport, without placeholder Sid values or duplicate network work.

Parsers consume `BaseKorailResponse.raw`, validate every documented container
and scalar, build tuple collections, reject duplicates and impossible counts,
preserve unknown codes, and never dereference `vrBnrUrl`.

- [ ] **Step 6: Register exact safety contracts and client methods**

Add only the two method/path pairs. Register exactly:

```text
Car: Device Version Key Sid txtMenuId txtPsrmClCd txtRunDt txtDptDt
     txtTrnClsfCd txtTrnNo txtDptRsStnCd txtArvRsStnCd
     txtDptStnRunOrdr txtArvStnRunOrdr txtTrnGpCd txtTotPsgCnt
     txtSeatAttCd txtGdNo
Seat: Device Version Key trnClsfCd trnGpCd runDt trnNo srcarNo psrmClCd
      dptRsStnCd arvRsStnCd seatAttCd dptStnRunOrdr arvStnRunOrdr
      totPsgCnt gdNo isArrow Sid ctlDvCd
```

Client methods call `_require_session`, call `validate_seat_inventory_inputs`
before `generate_sid`, create one fresh Sid, build the form, POST once with both
inclusion flags false, and parse the response. Export all new public types.
Update public-contract tests so the exact method set and type hints include both
methods.

- [ ] **Step 7: Run focused tests and verify GREEN**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_seat_inventory_reads.py tests/test_http.py tests/test_public_contract.py tests/test_models.py
```

Expected: all selected tests pass and no live I/O occurs.

- [ ] **Step 8: Add the separately opted-in evidence script**

Implement a script that requires `KORAIL_MOBILE_API_LIVE=1`, reads existing env
configuration, and performs at most one login, one train search, one car call,
and one seat call for the first car. It must not call broad `run_live_smoke`.
The safe JSON output contains only fixed statuses, operation call counts,
`train_count`, `car_count`, `seat_count`, `window_count`, booleans for documented
field/type presence, and a sufficiency enum. Counts cap at 10,000. It catches
errors by operation and suppresses exception text, raw mappings, messages,
identifiers, Sid, tokens, cookies, URLs, dates, and station values. It atomically
writes only after a credential/token/card/URL secret scan and closes the client.

Add script tests with a mocked client for every stop point, exact call budgets,
no retry, no broad helper, safe serialization, overwrite protection, AST import
boundaries, and client cleanup.

- [ ] **Step 9: Update version/docs and run the full offline release gate**

Set `project.version="0.2.0"`; update README, changelog, and progress with the
two read-only methods, fixed general-class scope, DynaPath-disabled boundary,
and live gate. Do not claim live success yet.

Run:

```bash
KORAIL_MOBILE_API_LIVE=1 PYTHONPATH="$PWD/src" pytest -q -m "not live"
python3 -m build --wheel --sdist --outdir /tmp/korail-seat-inventory-dist .
python3 scripts/verify_distribution.py /tmp/korail-seat-inventory-dist/*.whl /tmp/korail-seat-inventory-dist/*.tar.gz
git diff --check
```

Expected: full offline suite passes with one live test deselected and version
`0.2.0` artifacts verify. Remove `/tmp/korail-seat-inventory-dist` afterward.

- [ ] **Step 10: Commit the offline implementation**

```bash
git add src tests scripts pyproject.toml README.md CHANGELOG.md docs/IMPLEMENTATION_PROGRESS.md
git commit -m "feat: add korail seat inventory reads"
```

- [ ] **Step 11: Run the authorized bounded live gate**

Source the parent ignored env without printing it and run only the new script:

```bash
set -a
source /Users/yakisoba/Documents/GitHub/korail-mobile-api/.local-live-smoke.env
set +a
KORAIL_MOBILE_API_LIVE=1 PYTHONPATH="$PWD/src" python3 scripts/capture_seat_inventory_evidence.py --output /tmp/korail-seat-inventory-result.json --force
```

Inspect only the sanitized result. Record fixed status, call counts, bounded
counts, and sufficiency in progress documentation; never record field values or
identifiers. Delete the `/tmp` report.

- [ ] **Step 12: Verify and commit the live result**

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_seat_inventory_reads.py
git diff --check
git add docs/IMPLEMENTATION_PROGRESS.md
git commit -m "docs: record korail seat inventory verification"
```

Return exact commits, RED/GREEN/full-suite evidence, distribution result, safe
live call counts/status, and any blocker. Do not broaden scope if the server
rejects the static contract.
