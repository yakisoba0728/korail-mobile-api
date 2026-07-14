# KORAIL Live Seat Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the existing general-room KORAIL car and physical-seat read chain compatible with the sanitized production shapes observed on 2026-07-15, and make its bounded evidence helper choose an app-eligible train without widening the read-only boundary.

**Architecture:** Preserve the two existing public methods and exact request routes. Normalize only documented non-negative integer wire fields, model the two search-row fields needed for the app's normal general-room eligibility predicate, and treat absent optional seat metadata plus empty attribute/window collections conservatively. Keep live evidence bounded to one login, one search, one car-list request, and one seat-list request.

**Tech Stack:** Python 3.11+, frozen dataclasses, `httpx`, `pytest`, synthetic JSON fixtures.

## Global Constraints

- Do not add or call reservation, seat-selection, seat-hold, payment, refund, cancellation, check-in, membership, point, mileage, callback, WebView, or external URL routes.
- Keep the exact car route `/classes/com.korail.mobile.research.TrainResearch` and seat route `/classes/com.korail.mobile.research.TResidualSeatsResearch.do` unchanged.
- Keep `include_common=False` and `include_dynapath=False` for both inventory requests, with one fresh Sid per request and no retry or fallback request.
- Accept non-negative JSON integers and ASCII-decimal strings for documented numeric inventory fields; reject booleans, signs, whitespace, non-ASCII digits, decimal points, and negative values.
- Treat a missing or null seat `floor` as `None`; reject every other non-string value.
- Treat missing/null car containers as an empty typed car result, while rejecting a present container or row collection of the wrong type.
- Select the first normal-search general-class row for which `h_gen_rsv_cd` is neither `12` nor `13` and `h_rd_seat_map_flg` is absent/empty or its first character is not `N`.
- Do not print, commit, or persist raw live mappings, response messages, credentials, cookies, session identifiers, Sids, train/car/seat identifiers, dates, station values, URLs, or exception messages.
- Use synthetic fixture values only; no production response body or identifier may enter a fixture or test.
- Preserve every existing public method signature and exact transport allowlist.

---

### Task 1: Production-Compatible General-Room Seat Chain

**Files:**
- Create: `tests/fixtures/seat_car_list_live_shape.json`
- Create: `tests/fixtures/seat_inventory_live_shape.json`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `scripts/capture_seat_inventory_evidence.py`
- Modify: `tests/test_models.py`
- Modify: `tests/test_seat_inventory_reads.py`

**Interfaces:**
- Consumes: `TrainSummary.from_raw(raw)`, `parse_seat_car_list_response(response)`, `parse_seat_inventory_response(response)`, and `capture_evidence()`.
- Produces: `TrainSummary.seat_map_flag: str | None`, `TrainSummary.general_reservation_code: str | None`, `PhysicalSeat.floor: str | None`, and `_first_eligible_general_seat_train(trains) -> TrainSummary | None`.

- [ ] **Step 1: Add sanitized live-shape fixtures and failing parser/model tests**

Create a car fixture whose envelope is synthetic but whose numeric types match production:

```json
{"h_msg_cd":"IRG000000","h_msg_txt":"synthetic","strResult":"SUCC","h_rcmd_srcar_no":"2","h_trn_no":"00001","srcar_infos":{"srcar_info":[{"h_psrm_cl_nm":"Synthetic General","h_rest_seat_cnt":"3","h_srcar_no":"2","seatAttInfos":[]}]}}
```

Create a seat fixture with integer top-level counts, one synthetic seat that omits `floor`, and an empty `windowList`:

```json
{"h_msg_cd":"IRG000000","h_msg_txt":"synthetic","strResult":"SUCC","layout_type":3,"seat_ary_cd":"SYNTHETIC","seat_remain_count":1,"seat_total_count":1,"seatList":[{"dir_seat_att_cd":"SYNTHETIC","etc_seat_att_cd":"SYNTHETIC","intg_msg":"synthetic","intg_msg_cd":"SYNTHETIC","rq_seat_att_cd":"015","sale_psb_flg":"Y","seat_no":"SYNTHETIC-SEAT","seat_spec":"SYNTHETIC","sqr_no":"1","vz_msg_dv_cd":"SYNTHETIC"}],"vrBnrUrl":null,"windowList":[]}
```

Add tests with these assertions:

```python
def test_live_shape_car_decimal_strings_are_normalized(load_json_fixture):
    parsed = parse_seat_car_list_response(
        _base(load_json_fixture("seat_car_list_live_shape.json"))
    )
    assert parsed.recommended_car_no == 2
    assert parsed.cars[0].car_no == 2
    assert parsed.cars[0].remaining_seat_count == 3
    assert parsed.cars[0].attributes == ()


def test_live_shape_missing_floor_and_empty_windows_are_typed(load_json_fixture):
    parsed = parse_seat_inventory_response(
        _base(load_json_fixture("seat_inventory_live_shape.json"))
    )
    assert parsed.seats[0].floor is None
    assert parsed.windows == ()
```

Add parameterized rejection coverage for `True`, `-1`, `"-1"`, `" 1"`, `"1 "`, `"1.0"`, `"１"`, and `""` in each normalized numeric position. Add model coverage proving `TrainSummary.from_raw()` exposes `h_rd_seat_map_flg` and `h_gen_rsv_cd` without reading `raw`.

- [ ] **Step 2: Run the focused parser/model tests and verify RED**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q \
  tests/test_models.py \
  tests/test_seat_inventory_reads.py -k 'live_shape or decimal_strings or missing_floor or seat_map_flag or general_reservation_code'
```

Expected: failures show the current strict integer parser rejects decimal strings, `PhysicalSeat.floor` cannot represent missing metadata, and `TrainSummary` lacks the eligibility fields.

- [ ] **Step 3: Implement minimal model and parser normalization**

Extend the frozen models at the existing field/mapping boundaries:

```python
# TrainSummary fields, immediately after arrival_run_order
seat_map_flag: str | None = None
general_reservation_code: str | None = None

# TrainSummary.from_raw keyword arguments, immediately before raw=raw
seat_map_flag=raw.get("h_rd_seat_map_flg"),
general_reservation_code=raw.get("h_gen_rsv_cd"),

# PhysicalSeat field replacement
floor: str | None
```

Replace the inventory integer helpers with one strict normalizer used by required and optional fields:

```python
def _inventory_integer_value(value: object, key: str) -> int:
    if type(value) is int:
        parsed = value
    elif isinstance(value, str) and value and all("0" <= char <= "9" for char in value):
        parsed = int(value)
    else:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a non-negative integer or ASCII-decimal string"
        )
    if parsed < 0:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must not be negative"
        )
    return parsed
```

Required fields call the normalizer. Optional numeric fields return `None` when the key is missing or its value is null, otherwise call the normalizer. Add an optional string reader that returns `None` for missing/null and rejects other non-strings, and use it for `floor`, `h_trn_no`, and `vrBnrUrl`.

For the car container, implement this exact shape policy:

```python
container = raw.get("srcar_infos")
if container is None:
    rows = []
elif isinstance(container, Mapping):
    rows_value = container.get("srcar_info")
    if rows_value is None:
        rows = []
    elif isinstance(rows_value, list):
        rows = rows_value
    else:
        raise KorailProtocolError("KORAIL seat inventory field srcar_info must be a list or null")
else:
    raise KorailProtocolError("KORAIL seat inventory field srcar_infos must be an object or null")
```

- [ ] **Step 4: Run parser/model tests and verify GREEN**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_models.py tests/test_seat_inventory_reads.py
```

Expected: all selected files pass with no warnings.

- [ ] **Step 5: Add failing eligibility and evidence-semantics tests**

Add this helper contract to tests before production code:

```python
def test_first_eligible_general_train_skips_app_ineligible_rows():
    blocked_by_map = TrainSummary(
        train_no="1", seat_map_flag="N", general_reservation_code="11"
    )
    blocked_by_code = TrainSummary(
        train_no="2", seat_map_flag="Y", general_reservation_code="12"
    )
    eligible = TrainSummary(
        train_no="3", seat_map_flag="Y", general_reservation_code="11"
    )
    assert evidence._first_eligible_general_seat_train(
        [blocked_by_map, blocked_by_code, eligible]
    ) is eligible
```

Also prove absent/empty/short non-`N` map flags are eligible, reservation codes `12` and `13` are not, and a list without an eligible row returns `None`. Update the fake client so an `ineligible_trains` scenario makes `capture_evidence()` stop before `get_seat_cars()` with fixed status `no_eligible_train` and sufficiency `insufficient_no_eligible_train`.

Change the existing empty-field expectations so:

```python
@pytest.mark.parametrize("scenario", ["empty_attributes", "empty_windows"])
def test_evidence_accepts_valid_empty_optional_collections(configured_evidence, scenario):
    configured_evidence.scenario = scenario
    result = evidence.capture_evidence()
    assert result["status"] == "completed"
    assert result["sufficiency"] == "sufficient"


def test_evidence_still_requires_at_least_one_physical_seat(configured_evidence):
    configured_evidence.scenario = "empty_seats"
    result = evidence.capture_evidence()
    assert result["fields"]["physical_seat_fields_typed"] is False
    assert result["sufficiency"] == "insufficient_fields"
```

Add a fake seat with `floor=None` and assert `_physical_seat_fields_typed()` accepts it.

- [ ] **Step 6: Run the evidence tests and verify RED**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_seat_inventory_reads.py -k 'eligible_general or ineligible_trains or empty_optional_collections or physical_seat_fields'
```

Expected: failures show that the selector does not exist, `capture_evidence()` still chooses index zero, and empty attributes/windows are currently marked insufficient.

- [ ] **Step 7: Implement eligibility selection and corrected evidence predicates**

Add:

```python
def _first_eligible_general_seat_train(
    trains: Sequence[TrainSummary],
) -> TrainSummary | None:
    for train in trains:
        if train.general_reservation_code in {"12", "13"}:
            continue
        flag = train.seat_map_flag
        if flag and flag[0] == "N":
            continue
        return train
    return None
```

Use it immediately after the bounded train count. If it returns `None`, stop with `no_eligible_train` / `insufficient_no_eligible_train` and do not increment the car-list counter.

Make `_car_fields_typed()` require at least one typed car but not a non-empty attribute tuple. Make `_window_fields_typed()` use `all(...)` so an empty tuple is valid. Make `_physical_seat_fields_typed()` accept `floor is None or isinstance(floor, str)` while retaining the non-empty-seat requirement and every other string check.

- [ ] **Step 8: Run focused and full offline gates**

Run:

```bash
PYTHONPATH="$PWD/src" pytest -q tests/test_models.py tests/test_seat_inventory_reads.py
PYTHONPATH="$PWD/src" pytest -q -m "not live"
git diff --check
```

Expected: focused tests pass; full gate passes with exactly the explicit live test deselected; `git diff --check` is silent.

- [ ] **Step 9: Commit the reviewed offline implementation**

```bash
git add \
  docs/superpowers/plans/2026-07-15-korail-live-seat-hardening.md \
  src/korail_mobile_api/models.py \
  src/korail_mobile_api/parsers.py \
  scripts/capture_seat_inventory_evidence.py \
  tests/fixtures/seat_car_list_live_shape.json \
  tests/fixtures/seat_inventory_live_shape.json \
  tests/test_models.py \
  tests/test_seat_inventory_reads.py
git commit -m "fix: harden korail live seat parsing"
```
