# KORAIL Seat Inventory Read Design

Status: Approved on 2026-07-14 for two authenticated read-only operations.

## Context and decision

All previously runtime-successful KORAIL reads are implemented. The next
bounded expansion is the app's car list and physical-seat inventory reads:

- `POST /classes/com.korail.mobile.research.TrainResearch`
- `POST /classes/com.korail.mobile.research.TResidualSeatsResearch.do`

Tracked Retrofit contracts and response classes define both shapes, but the
current positive safety registry correctly blocks them before I/O. No live call
was made during design. Implementation therefore proceeds from exact static
contracts and synthetic fixtures, followed by one bounded live verification.

Three approaches were considered: a generic raw route escape hatch, static
typed operations followed by a live gate, and postponing all work until an
unsafe direct request could be made. The narrow typed approach is selected. A
generic escape hatch is rejected, and the existing safety boundary must not be
bypassed.

## Public API

```python
def get_seat_cars(
    self,
    train: TrainSummary,
    *,
    passenger_count: int = 1,
) -> SeatCarListResponse: ...

def get_seat_inventory(
    self,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int = 1,
) -> SeatInventoryResponse: ...
```

Both methods require an authenticated session, validate all inputs before I/O,
and issue exactly one request. `passenger_count` is an integer from 1 through 9
and `car_no` is a positive integer. This first increment is fixed to the normal
main-menu/general-room contract: menu `"11"`, room class `"1"`, seat attribute
`"015"`, empty product number, and empty control-division code.

The methods consume server-owned fields from `TrainSummary`: run date,
departure date, train class/number/group, departure/arrival station codes, and
departure/arrival run orders. `TrainSummary` gains append-only optional
`run_date`, `train_class_code`, `departure_run_order`, and
`arrival_run_order` fields populated from the canonical documented `h_*`
response keys while retaining the raw mapping as repr-hidden evidence.
Missing or malformed required fields raise `KorailProtocolError` before Sid
generation or transport. No caller may supply arbitrary wire fields.

## Models

All new types are frozen dataclasses and exported from the package root:

```text
SeatAttribute(name: str)
SeatCar(car_no: int, room_class_name: str, remaining_seat_count: int,
        attributes: tuple[SeatAttribute, ...])
SeatCarListResponse(BaseKorailResponse, recommended_car_no: int | None,
                    train_no: str | None, cars: tuple[SeatCar, ...])
PhysicalSeat(seat_no: str, sale_possible: str, direction_code: str,
             other_attribute_code: str, requested_attribute_code: str,
             floor: str, specification: str, sequence_no: str,
             message_code: str, message: str, visual_message_division_code: str)
SeatWindow(start_location_ratio: float, close_location_ratio: float)
SeatInventoryResponse(BaseKorailResponse, layout_type: int,
                      arrangement_code: str, remaining_count: int,
                      total_count: int,
                      seats: tuple[PhysicalSeat, ...],
                      windows: tuple[SeatWindow, ...],
                      vr_banner_url: str | None)
```

Raw mappings, messages, seat numbers, train numbers, product values, and URLs
are `repr=False` wherever represented. Parsers preserve unknown string codes
verbatim instead of guessing enum meaning. They require documented container
types, reject booleans where integers are required, reject negative counts and
non-finite window ratios, and reject duplicate non-empty car or seat numbers.
An empty, structurally valid list is allowed. Count/list equality is not
required because the tracked contract does not prove whether the list contains
all seats or only displayable seats.

`vr_banner_url` is inert data only. The client never follows it.

## Exact production wire contracts

The canonical car-list transport names are the direct Retrofit `@Field` names
in `docs/deep-dive/api-contracts.md`, not the DAO report's shorthand names for
the request-object getters. Production omits `sidTest` because the app passes
null on REAL and Retrofit omits null form fields.

Car-list fields are exactly:

```text
Device Version Key Sid txtMenuId txtPsrmClCd txtRunDt txtDptDt
txtTrnClsfCd txtTrnNo txtDptRsStnCd txtArvRsStnCd
txtDptStnRunOrdr txtArvStnRunOrdr txtTrnGpCd txtTotPsgCnt
txtSeatAttCd txtGdNo
```

Seat-list fields are exactly:

```text
Device Version Key trnClsfCd trnGpCd runDt trnNo srcarNo psrmClCd
dptRsStnCd arvRsStnCd seatAttCd dptStnRunOrdr arvStnRunOrdr
totPsgCnt gdNo isArrow Sid ctlDvCd
```

`txtMenuId="11"`, `txtPsrmClCd`/`psrmClCd="1"`,
`txtSeatAttCd`/`seatAttCd="015"`, `txtGdNo`/`gdNo=""`,
`isArrow="true"`, and `ctlDvCd=""` are fixed. Production omits `sidTest`.
Each operation generates one fresh `Sid`. Both calls use
`include_common=False` and provide `Device`, `Version`, and `Key` explicitly.
The tracked app inventory says neither route belongs to the DynaPath static URL
list, so both calls set `include_dynapath=False` even under a custom allowlist.

The safety registry adds only these method/path pairs and their exact production
field sets. Missing, duplicate, or extra fields, wrong methods, wrong origins,
and adjacent reservation/selection routes fail before Sid generation, DynaPath,
or transport.

## Parsing and data flow

Closed payload builders translate validated `TrainSummary.raw` plus bounded
caller inputs to the exact forms. Client methods call `_require_session`, build
the form, make one POST through `KorailHttpClient`, and pass the raw mapping to
route-specific parsers.

The car parser consumes `srcar_infos.srcar_info[]` and nested
`seatAttInfos[]`. The seat parser consumes `seatList[]`, `windowList[]`, layout
metadata, counts, and the inert banner URL. Base envelope parsing and app-error
behavior remain unchanged. For seat inventory,
`0 <= remaining_count <= total_count`; list length is independent.

## Files and tests

- Modify `src/korail_mobile_api/models.py`, `payloads.py`, `parsers.py`,
  `safety.py`, `client.py`, and `__init__.py`.
- Set `project.version` in `pyproject.toml` to `0.2.0` and add the release note.
- Add `tests/fixtures/seat_car_list_success.json` and
  `tests/fixtures/seat_inventory_success.json` with synthetic values only.
- Add `tests/test_seat_inventory_reads.py` for models, parsers, builders,
  methods, exact prepared requests, zero-I/O validation, repr safety, and
  excluded-route regressions.
- Update README, changelog, progress, and the live helper's bounded result
  schema without adding these calls to the broad default release gate.
- Create `scripts/capture_seat_inventory_evidence.py` for the separately
  opted-in four-operation live gate; it outputs only the bounded safe result.

TDD must demonstrate RED before production changes. Focused tests cover every
documented field, malformed containers/types/counts, duplicates, empty lists,
unknown codes, URL inertness, exact call count, no DynaPath, and absence of
mutation routes. The full offline suite and distribution gate must remain green.

## Bounded live gate

After offline review, an explicitly opted-in helper may perform one login, the
minimum existing train search, one car-list call, and one seat-list call for the
first eligible car. It makes no retry of either inventory operation. Responses
remain memory-only; output is limited to call counts, booleans, bounded counts,
and field/type presence. It never prints or stores dates, station/train/car/seat
identifiers, account values, Sid, cookies, raw mappings, messages, or URLs.

Any contract mismatch stops the gate and returns a fixed failure category. The
gate never selects or holds a seat and never invokes reservation, payment,
cancellation, refund, external URL, or other mutation behavior.

## Version and acceptance

This backward-compatible public read expansion sets version `0.2.0`.
Acceptance requires exact static contracts, frozen repr-safe models, two
one-request methods, pre-I/O rejection coverage, focused and full offline tests,
distribution verification, independent review with no open Critical/Important
finding, and the bounded live result or an explicit safely observed blocker.
