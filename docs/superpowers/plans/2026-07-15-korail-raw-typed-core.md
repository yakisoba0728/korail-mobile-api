# KORAIL Raw-Backed Typed Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote the structurally evidenced seat, station, calendar, schedule, transfer, and train-search response fields into immutable, repr-safe public models without changing any request or route semantics.

**Architecture:** Extend the existing `models.py` dataclasses only by appending defaulted fields, add strict shape adapters to `parsers.py`, and have the five already-public client reads return those typed responses. Keep every response/nested raw mapping behind `repr=False`; keep codes, URLs, messages, dates, train numbers, and station identifiers out of repr where they could disclose caller/server data.

**Tech Stack:** Python 3.11+, frozen dataclasses, `Mapping`, httpx mocked transport, pytest.

## Global Constraints

- Use only `/tmp/korail-success-gap-analysis.md` and committed source/static documentation as evidence.
- Do not read `.env`, capture bodies, or any credential source; do not issue network requests.
- Fixtures and values added by this plan must be unmistakably synthetic.
- Do not add an endpoint, route, client method, payload field, builder option, or fallback request.
- Preserve existing positional constructor order by appending every new field with a default.
- Preserve the first eight positional `TrainSummary` parameters exactly.
- Preserve existing request bodies and signatures exactly.
- All raw mappings use `repr=False`; codes and free text called out by the evidence remain repr-hidden.
- Follow red-green-refactor and record the focused failing and passing commands.

---

### Task 1: Promote seat response metadata

**Files:**
- Modify: `tests/fixtures/seat_car_list_success.json`
- Modify: `tests/fixtures/seat_inventory_success.json`
- Modify: `tests/test_seat_inventory_reads.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/parsers.py`

**Interfaces:**
- Consumes: `BaseKorailResponse`, `_inventory_required_string()`, `_inventory_optional_string()`, `_inventory_required_int()`, `_inventory_optional_int()`.
- Produces: `SeatAttribute.code`, `SeatCar.room_class_code`, `SeatCar.total_seat_count`, `SeatCarListResponse.train_class_code`, `SeatCarListResponse.train_group_code`, `SeatInventoryResponse.car_type_code`, `SeatInventoryResponse.car_no`, and `SeatInventoryResponse.up_down_division_code`.

- [ ] **Step 1: Add failing shape, compatibility, and repr tests**

Add synthetic keys `seatAttCd`, `h_psrm_cl_cd`, `h_seat_cnt`, `h_trn_clsf_cd`, `h_trn_gp_cd`, `car_tp_cd`, `scar_no`, and `up_dn_dv_cd` to the existing synthetic fixtures. Assert parsing exposes the descriptive public fields, codes do not appear in repr, count/cardinality relationships are valid, and these legacy prefixes are unchanged:

```python
assert list(inspect.signature(SeatAttribute).parameters)[:1] == ["name"]
assert list(inspect.signature(SeatCar).parameters)[:4] == [
    "car_no", "room_class_name", "remaining_seat_count", "attributes"
]
assert list(inspect.signature(SeatCarListResponse).parameters)[-3:] == [
    "cars", "train_class_code", "train_group_code"
]
assert list(inspect.signature(SeatInventoryResponse).parameters)[-3:] == [
    "car_type_code", "car_no", "up_down_division_code"
]
```

- [ ] **Step 2: Verify focused RED**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_seat_inventory_reads.py -k 'server_metadata or positional_metadata or metadata_repr'
```

Expected: fail because the appended fields do not exist.

- [ ] **Step 3: Add the minimal model/parser implementation**

Append defaulted fields in `models.py`:

```python
@dataclass(frozen=True)
class SeatAttribute:
    name: str
    code: str | None = field(default=None, repr=False)

@dataclass(frozen=True)
class SeatCar:
    car_no: int
    room_class_name: str
    remaining_seat_count: int
    attributes: tuple[SeatAttribute, ...]
    room_class_code: str | None = field(default=None, repr=False)
    total_seat_count: int | None = None
```

Append response codes with `repr=False`, normalize `h_seat_cnt` and `scar_no` with the existing strict non-negative ASCII-decimal helper, and reject `remaining_seat_count > total_seat_count` when the total is present. Do not change a payload builder.

- [ ] **Step 4: Verify seat GREEN**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_seat_inventory_reads.py tests/test_models.py tests/test_public_contract.py
```

Expected: pass with all legacy seat constructors and request tests unchanged.

---

### Task 2: Type station, calendar, schedule, and transfer responses

**Files:**
- Create: `tests/fixtures/raw_typed_station_info.json`
- Create: `tests/fixtures/raw_typed_station_data.json`
- Create: `tests/fixtures/raw_typed_train_calendar.json`
- Create: `tests/fixtures/raw_typed_train_schedule.json`
- Create: `tests/fixtures/raw_typed_transfer_stations.json`
- Create: `tests/test_raw_typed_core.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `src/korail_mobile_api/client.py`

**Interfaces:**
- Consumes: existing `BaseKorailResponse`, `StationDataResponse`, `KorailStation`, client paths/forms, and `parse_station_data_response()`.
- Produces: `StationInfoResponse`, expanded `KorailStation`, `TrainCalendarDay`, `TrainCalendarResponse`, `TrainScheduleStop`, `TrainScheduleResponse`, `TransferStation`, and `TransferStationListResponse`.

- [ ] **Step 1: Add sanitized fixtures and failing parser/client tests**

Use only placeholder values such as `SYNTHETIC-STATION-CODE`, `SYNTHETIC-RUN-DATE`, and `synthetic-message-secret`. Test these exact containers and server keys:

```python
STATION_INFO_KEYS = {"count", "map_version"}
STATION_KEYS = {
    "stn_cd", "stn_nm", "longitude", "latitude", "group", "major",
    "popupType", "popupMessage", "popupLinkTitle", "popupLinkUrl",
}
CALENDAR_KEYS = {
    "runDt", "bizDdStgCd", "dayDvCd", "hldyDvCd", "saleDdDvCd",
    "aTrnOpFlg", "dTrnOpFlg", "gTrnOpFlg", "oTrnOpFlg", "sTrnOpFlg",
    "vTrnOpFlg", "xTrnOpFlg",
}
SCHEDULE_STOP_KEYS = {
    "stopRsStnCd", "stopStnNm", "stnConsOrdr", "runOrdr", "actArvDt",
    "actArvTm", "actDptDt", "actDptTm", "arvDt", "arvTm", "dptDt",
    "dptTm", "actArvDlayTnum", "expnArvDlayTnum",
    "expnDptDlayTnum", "rgulFlg", "saodFlg",
}
TRANSFER_KEYS = {"chtnRsStnCd", "chtnRsStnNm"}
```

Assert malformed object/list/item/scalar shapes raise `KorailProtocolError`, tuples are immutable, raw mappings and popup/schedule message markers are absent from repr, and mocked calls keep the same method/path/query/form while returning the new response type.

- [ ] **Step 2: Verify typed-read RED**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_raw_typed_core.py -k 'station or calendar or schedule or transfer'
```

Expected: collection fails on missing model/parser imports; after import wiring is corrected, tests fail on the still-generic client returns.

- [ ] **Step 3: Implement models and strict parsers**

Append station fields after the existing `raw` positional slot:

```python
group: str | None = None
major: str | None = None
popup_type: int | None = None
popup_message: str | None = field(default=None, repr=False)
popup_link_title: str | None = field(default=None, repr=False)
popup_link_url: str | None = field(default=None, repr=False)
```

Calendar rows expose `run_date`, the four day classification codes, and seven operation flags. Schedule rows expose planned/actual times, stop station, construction/run order, delay fields, and regular/service flags; top-level schedule message fields are repr-hidden. Transfer rows expose `station_code` and `station_name`, with `station_code` repr-hidden. Every nested type stores a copied raw mapping with `repr=False` and `compare=False`.

Add parser entry points:

```python
def parse_station_info_response(response: BaseKorailResponse) -> StationInfoResponse
def parse_train_calendar_response(response: BaseKorailResponse) -> TrainCalendarResponse
def parse_train_schedule_response(response: BaseKorailResponse) -> TrainScheduleResponse
def parse_transfer_station_list_response(response: BaseKorailResponse) -> TransferStationListResponse
```

- [ ] **Step 4: Wire only existing client methods to the typed parsers**

Change return annotations and parsing for `get_station_info`, `get_station_data`, `get_train_calendar`, `get_train_schedule`, and `get_transfer_stations`. Preserve signatures, routes, flags, and payload mappings byte-for-byte.

- [ ] **Step 5: Verify typed-read GREEN**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_raw_typed_core.py tests/test_client_read_apis.py tests/test_uuid_maas_read_apis.py
```

Expected: pass; normal and MAAS station rows share `StationDataResponse`, with coordinate/extra fields optional.

---

### Task 3: Promote search metadata and safe follow-on train fields

**Files:**
- Create: `tests/fixtures/raw_typed_train_search.json`
- Modify: `tests/test_raw_typed_core.py`
- Modify: `src/korail_mobile_api/models.py`
- Modify: `src/korail_mobile_api/parsers.py`
- Modify: `src/korail_mobile_api/client.py`

**Interfaces:**
- Consumes: `TrainSummary.from_raw()`, `parse_train_rows()`, and the existing `TrainSearchResult(trains, response, raw)` constructor order.
- Produces: `TrainSearchMetadata`; appended train construction, seat/car/class/group, reservation availability, free-car count, and total-passenger fields.

- [ ] **Step 1: Add failing search shape and compatibility tests**

Use named captured keys only: response `h_menu_id`, `strJobId`, `h_gd_no`, `h_next_pg_flg`, `h_qry_st_no_next`, `h_trn_no_next`, `h_rslt_cnt`, `h_seat_cnt_first`, `h_seat_cnt_second`, `txtGoHour_first`; row `h_dpt_stn_cons_ordr`, `h_arv_stn_cons_ordr`, `h_seat_att_cd`, `h_car_tp_cd`, `h_car_tp_nm`, `h_trn_clsf_nm`, `h_trn_gp_nm`, `h_gen_psrm_cl_nm`, `h_spe_psrm_cl_nm`, `h_gen_rsv_cd`, `h_gen_rsv_cd2`, `h_spe_rsv_cd`, `h_spe_rsv_cd2`, `h_free_rsv_cd`, `h_stnd_rsv_cd`, `h_rsv_psb_nm`, `h_spe_rsv_psb_nm`, `h_rd_seat_map_flg`, `h_wait_rsv_flg`, `h_std_rest_seat_cnt`, `h_fst_rest_seat_cnt`, `h_free_sracar_cnt`, `h_rsv_wait_ps_cnt`, and `totPsgCnt`.

Assert:

```python
assert list(inspect.signature(TrainSummary).parameters)[:8] == [
    "train_no", "train_group_code", "departure_station_code",
    "arrival_station_code", "departure_date", "departure_time",
    "arrival_time", "raw",
]
assert list(inspect.signature(TrainSearchResult).parameters)[:3] == [
    "trains", "response", "raw"
]
```

Test a null `h_spe_rsv_cd`, reject non-string values for the four captured row count fields, preserve their strings without arithmetic or numeric inference, and ensure raw/code/message sentinel values are absent from repr.

- [ ] **Step 2: Verify search RED**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_raw_typed_core.py -k 'train_search or train_summary'
```

Expected: fail because `TrainSearchMetadata` and appended train fields do not exist.

- [ ] **Step 3: Implement the minimal promotion**

Add a frozen `TrainSearchMetadata` with repr-hidden `menu_id`, `job_id`, `product_no`, next-query/train identifiers, raw mapping, and optional server-string count metadata. Keep paging flags/count strings visible. Append `metadata` with a default factory after `TrainSearchResult.raw`.

Append all row fields after `general_reservation_code`. Preserve server codes and the observed `h_std_rest_seat_cnt`, `h_fst_rest_seat_cnt`, `h_free_sracar_cnt`, and `h_rsv_wait_ps_cnt` counts as optional strings without summing or numeric coercion. Preserve the named response metadata as optional strings as observed. Map a present non-string nullable field to `KorailProtocolError` rather than coercing it; keep static-only `totPsgCnt` as its existing integer concept when present.

Add `parse_train_search_metadata()` and populate it in `_search_trains()` without changing the request.

- [ ] **Step 4: Verify search GREEN**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_raw_typed_core.py tests/test_models.py tests/test_client_read_apis.py tests/test_seat_inventory_reads.py
```

Expected: pass, including every old constructor and payload assertion.

---

### Task 4: Publish and verify the cohesive contract

**Files:**
- Modify: `src/korail_mobile_api/__init__.py`
- Modify: `tests/test_public_contract.py`
- Modify: `tests/test_readme.py`
- Modify: `README.md`
- Modify: `docs/IMPLEMENTATION_PROGRESS.md`

**Interfaces:**
- Consumes: every new model and changed client annotation from Tasks 1-3.
- Produces: package-root imports and `__all__` entries for all new public models, plus accurate scope/compatibility documentation.

- [ ] **Step 1: Add failing export/signature/docs tests**

Assert all eight new names are package-root exports, existing five method parameter lists are unchanged, return hints are typed, all new dataclasses are frozen, and README states that request semantics remain fixed while server-derived response fields are now typed.

- [ ] **Step 2: Verify publication RED**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_public_contract.py tests/test_readme.py -k 'typed_core or station or calendar or schedule or transfer or search'
```

Expected: fail on missing exports/docs text.

- [ ] **Step 3: Add exports and concise documentation**

Export `StationInfoResponse`, `TrainCalendarDay`, `TrainCalendarResponse`, `TrainScheduleStop`, `TrainScheduleResponse`, `TransferStation`, `TransferStationListResponse`, and `TrainSearchMetadata`. Document typed fields, repr-hidden raw/code/free-text policy, constructor compatibility, and explicitly unchanged request semantics.

- [ ] **Step 4: Run focused and full verification**

Run:

```bash
PYTHONPATH=src pytest -q tests/test_raw_typed_core.py tests/test_seat_inventory_reads.py tests/test_client_read_apis.py tests/test_models.py tests/test_public_contract.py tests/test_readme.py
PYTHONPATH=src pytest -q -m 'not live'
git diff --check
git status --short
```

Expected: all focused tests pass; full non-live suite has zero failures; diff check is clean; only scoped source/tests/fixtures/docs plus this plan are modified.

- [ ] **Step 5: Commit the isolated branch**

```bash
git add docs/superpowers/plans/2026-07-15-korail-raw-typed-core.md \
  src/korail_mobile_api/models.py src/korail_mobile_api/parsers.py \
  src/korail_mobile_api/client.py src/korail_mobile_api/__init__.py \
  tests/test_raw_typed_core.py tests/test_seat_inventory_reads.py \
  tests/test_public_contract.py tests/test_readme.py tests/fixtures/raw_typed_*.json \
  tests/fixtures/seat_car_list_success.json tests/fixtures/seat_inventory_success.json \
  README.md docs/IMPLEMENTATION_PROGRESS.md
git commit -m "feat: promote raw-backed typed read models"
```

## Self-Review

- Spec coverage: all three requested model tranches, existing client return typing, exports, fixtures, docs, repr safety, positional compatibility, focused RED/GREEN, full non-live verification, and commit are covered.
- Scope guard: no route, endpoint, method, payload builder, request signature, or live helper is added or changed.
- Placeholder scan: the plan contains no deferred implementation step; every parser/model/key/command is named.
- Type consistency: `StationDataResponse` remains shared by normal and MAAS station methods; all new collection fields are tuples; every numeric normalization uses the existing strict ASCII-decimal philosophy.
