# KORAIL Mobile API

This repository provides an installable read-only Python package for the
evidenced KORAIL mobile API surface. It also retains the static
reverse-engineering report for `korail.apk`, Android package
`com.korail.talk` version `6.5.0`, as the package's historical evidence map.

The reviewed package boundary contains 37 routes and 40 public methods. The
current offline release gate is `1180 passed, 1 deselected`; the
deselected test is the explicitly opted-in live-service test.

The original APK and generated decompile directories are intentionally not
committed. Documentation, reproducible inventory output, client source, and
offline contract tests are committed.

## Quick Start

Start here:

1. [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) - high-level APK, host, network, flow, WebView, storage, and security summary.
2. [docs/api-endpoints.md](docs/api-endpoints.md) - complete Retrofit endpoint table.
3. [docs/deep-dive/README.md](docs/deep-dive/README.md) - deep-dive manual index and reading order.
4. [docs/NEXT_SESSION.md](docs/NEXT_SESSION.md) - current handoff state for the next analysis session.
5. [docs/RELEASE.md](docs/RELEASE.md) - internal-only test, build, distribution, and fresh-install gate.

Internal editable installation and offline verification:

```bash
python -m pip install -e ".[test]"
PYTHONPATH="$PWD/src" pytest -q
```

Release and handling documents:

- [docs/RELEASE.md](docs/RELEASE.md)
- [SECURITY.md](SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)

## Current Findings

- Package: `com.korail.talk`
- App version: `6.5.0`
- API version: `250601003`
- Runtime API/Web host: `https://smart.letskorail.com`
- Retrofit method entries: `165`
- Distinct HTTP+path pairs: `159`
- Annotated Retrofit interfaces: `35`
- HTTP methods: `POST 136`, `GET 29`
- Network request/response/model fields cataloged: `2,566`
- WebView JavaScript bridge methods cataloged: `26`
- Parallel deep-dive reports: `20`

## Documentation Map

Core documents:

- [docs/api-endpoints.md](docs/api-endpoints.md): method/path/request parameter/return type inventory.
- [docs/deep-dive/api-contracts.md](docs/deep-dive/api-contracts.md): endpoint-by-endpoint request and response field contract.
- [docs/deep-dive/network-model-fields.md](docs/deep-dive/network-model-fields.md): Java model field catalog from decompiled network classes.
- [docs/deep-dive/webview-and-url-catalog.md](docs/deep-dive/webview-and-url-catalog.md): WebView bridge, URL, scheme, and API-like path catalog.
- [docs/deep-dive/local-storage-catalog.md](docs/deep-dive/local-storage-catalog.md): ORMLite DB model and SharedPreferences key catalog.
- [docs/deep-dive/agent-reports/](docs/deep-dive/agent-reports/): 20 focused subsystem reports.

## Local Artifacts

Ignored local files/directories:

- `korail.apk`: source APK input, not committed.
- `analysis/`: generated `unzip`, `apktool`, `jadx`, and extraction reports, not committed.
- `.DS_Store`: macOS metadata.

Expected local artifact layout after analysis:

```text
analysis/raw/
analysis/apktool/
analysis/jadx/
analysis/reports/
analysis/generated/
```

## Reproducing Static Inputs

Install tools if missing:

```bash
brew install jadx apktool
```

Regenerate decompile artifacts from a local `korail.apk`:

```bash
rm -rf analysis
mkdir -p analysis/raw analysis/reports analysis/generated
unzip -q korail.apk -d analysis/raw
apktool d -f korail.apk -o analysis/apktool
jadx -d analysis/jadx --show-bad-code korail.apk
```

JADX may report decompilation warnings for some library/UI classes. The network layer under `com.korail.talk.network.*` was still readable for the committed documentation. Use `analysis/apktool/smali*` as fallback evidence when Java-like output is ambiguous.

## Scope and Limits

Static analysis remains the evidence source for the APK inventory. The Python
client additionally supports explicitly opted-in live login and read-only smoke
verification using caller-supplied credentials and device identity.

The project does not provide:

- Authentication bypass
- NetFunnel or DynaPath bypass
- Reservation, payment, cancellation, refund, check-in, or member mutation APIs
- General-purpose runtime WebView automation

Server response values, feature flags, redirect behavior, and server-side
nullable/required rules remain unknown unless evidenced by a controlled,
authorized live observation.

## Python Package MVP

This repository now contains an installable Python client package under `src/korail_mobile_api`.

Default tests are offline:

```bash
pip install -e ".[test]"
pytest
```

### Account-neutral cache reads

`KorailClient.get_app_data()` and `KorailClient.get_notice()` expose the two
evidenced account-neutral cache reads:

- `GET /file/CACHE/prdMobilePlusMain.cache`
- `GET /file/CACHE/prdMobilePlusNotice.cache`

Both methods can run before login and send only a `timeStamp` query parameter.
They return frozen typed responses while retaining the original mapping through
the repr-hidden `raw` field. Supplying `timestamp_ms` gives callers a
deterministic cache key; omitting it uses the current Unix epoch in
milliseconds.

### Successful read expansion

The package now exposes 11 new public read methods across the 27 exact login/read routes
registered by the transport boundary:

- Account-neutral: `get_service_status()` and `get_pass_available_dates()`.
- Authenticated account or reservation reads: `get_deposit_banks()`,
  `get_trip_menu()`, `get_cart_list()`,
  `get_delay_discount_tickets()`, `get_discount_coupons()`,
  `get_product_reservations()`, `get_product_detail()`,
  `get_ticket_receipt()`, and `get_reservation_history()`.

All requests use exact GET query or POST form field sets and issue one request
without a fallback. No new DynaPath route was added, and every method above
explicitly disables DynaPath. A bounded 2026-07-15 one-session replay called
only these read methods. Five methods parsed successfully: service status,
deposit banks, discount coupons, trip menu, and reservation history. The cart,
delay-discount, pass-available-date, and product-reservation reads reached
their response parsers but four stopped at `KorailProtocolError`; two
identifier-dependent calls were not issued because the account returned no
owned product or ticket identifiers. No raw response, identifier, message,
credential, cookie, or token was printed or persisted. Subsequent sanitized
shape-only analysis established endpoint-local result-only success envelopes
for cart, delay-discount, and product-reservation lists. Those three routes now
accept only that exact partial-success form while all strict-route, complete
failure, and complete session-expiry behavior stays unchanged. The available
capture did not contain a pass-availability body, so that contract is unchanged.

Deposit-bank and trip-menu reads require an authenticated session. Their
pre-login server responses were complete session-expiry envelopes, so both
public methods now fail locally before transport without a session and the
bounded smoke helper calls them only after its single login.

`WRG000000` from the coupon list and `P100` from reservation history are the
only evidenced no-data application codes converted to typed empty results.
Other failures retain the package's typed error behavior, including `P058`
session expiry and local session clearing.

Product, receipt, cart, and ticket reads accept only caller-owned identifiers.
For example, an already authenticated client can obtain one product detail
without deriving an identifier from another response or making an adjacent
request:

```python
def get_owned_product_detail(
    client,
    reservation_no,
    reservation_sequence,
):
    return client.get_product_detail(
        reservation_no=reservation_no,
        reservation_sequence=reservation_sequence,
    )
```

The reservation, payment, and mutation routes remain excluded. The package
does not create, change, cancel, pay for, refund, or check in a reservation as
part of any read.

### Static P0 menu and reference reads

Three session-unverified reference methods use static APK evidence and synthetic fixtures only:

- `get_pass_menu(menu_no)` sends one exact `POST` to
  `/classes/com.korail.mobile.pass.passMenu.do`.
- `get_crew_request_list(query_division_code)` sends one exact `GET` to
  `/classes/com.korail.mobile.push.crwCallRq.do`.
- `get_commuter_kind_menu(commuter_kind_code)` sends one exact `GET` to
  `/classes/com.korail.mobile.push.cmtrKnd.do`.

Each method requires its caller-supplied runtime discriminator and has no
default or library-selected code. Server-returned pass, period, age, and crew
option codes remain typed response data. All three requests use their exact
four-field contracts (`Device`, `Version`, `Key`, plus the discriminator),
issue no fallback request, and explicitly disable DynaPath. No live request or
raw response body was used to implement or verify this increment.

The current client has no local session precondition for these calls, but that
does not establish the live server's authentication requirement. Treat all
three as session-unverified and perform live verification only after login.

The similarly named `/classes/com.korail.mobile.push.callCrew.do` route is the
state-changing crew-call operation and remains excluded from the transport
allowlist and public client. Reading crew request options never submits a crew
call.

### Typed car and physical-seat inventory reads

Version `0.2.0` adds `get_seat_cars(train, *, passenger_count=1)` and
`get_seat_inventory(train, car_no, *, passenger_count=1)`. Both methods require
an authenticated session and consume only server-owned schedule fields already
present on `TrainSummary`. Caller counts and every required train field are
validated before Sid generation or transport.

This first increment is deliberately fixed to main menu `11`, general room
class `1`, seat attribute `015`, an empty product number, and an empty control
division. Each method generates one fresh Sid and issues one exact POST. The
forms omit `sidTest`, pass `Device`, `Version`, and `Key` explicitly, and force
`include_common=False` plus `include_dynapath=False`. No custom field map,
generic route escape hatch, seat selection, hold, or reservation action is
exposed.

The returned car, seat, and window collections are immutable tuples. Raw
mappings, response messages, train and seat identifiers, and the documented
banner URL are repr-hidden. The banner URL remains inert response data and is
never followed by the client.

### Raw-backed typed response core

The raw-backed typed response core now returns `StationInfoResponse`, the
existing `StationDataResponse`, `TrainCalendarResponse`,
`TrainScheduleResponse`, and `TransferStationListResponse` from the five
already-public reference and schedule reads. Calendar days, actual-schedule
stops, and transfer stations are frozen typed rows. Normal station data also
exposes optional group, major, coordinate, and popup metadata; popup messages,
titles, and URLs are repr-hidden.

`TrainSearchMetadata` promotes the response menu, job, product, paging, and
count strings. `TrainSummary` now promotes station construction orders,
seat-attribute and car-type fields, train class/group names, reservation
availability, and remaining-count metadata needed by safe follow-on reads.
The observed `h_std_rest_seat_cnt`, `h_fst_rest_seat_cnt`,
`h_free_sracar_cnt`, and `h_rsv_wait_ps_cnt` values remain optional strings;
the client does not sum, coerce, or infer numeric meaning from them.

For compatibility, existing constructor prefixes are preserved through
appended, defaulted fields. Client call parameters remain unchanged; return
annotations for five existing read methods are narrowed to typed responses.
Existing routes, methods, and request payload semantics remain unchanged.
Response and nested raw mappings remain `repr=False`, as do newly promoted
server identifiers, URLs, and free-text messages. This typing increment does
not use the promoted values to change the fixed seat request forms.

The separately opted-in evidence command is not part of the broad live smoke:

```bash
KORAIL_MOBILE_API_LIVE=1 PYTHONPATH="$PWD/src" \
  python3 scripts/capture_seat_inventory_evidence.py \
  --output /tmp/korail-seat-inventory-result.json --force
```

It permits at most one login operation, one minimum train search, one car-list
call, and one first-car seat-list call. Its atomically written JSON is limited
to fixed statuses, 0/1 operation counters, counts capped at 10,000, documented
field/type-presence booleans, and a sufficiency category. It suppresses raw
responses, messages, identifiers, dates, stations, credentials, session data,
Sid values, tokens, and URLs. A bounded live structural run selected the first
app-eligible general-room result and received `IRG000000`/`SUCC` from both
read routes: 5 cars and 75 seat rows. The response used the documented field
types, allowed a missing floor and an empty window collection, and contained
repeated seat labels; the client preserves those repeated rows and their
original order. The evidence retained no raw response, identifier, message,
station, date, credential, cookie, Sid, token, or URL. A later post-fix helper
confirmation stopped at the service-status preflight before login transport,
so it made no search, car-list, or seat-list request and was not rapidly
retried.

### Static-only P0 train reads

Four additional APK-evidenced read operations are exposed through closed,
frozen request objects. This increment is static-only: its contracts come from
the tracked Retrofit declarations, response DTOs, and direct APK call sites.
No live call was made, and all parser coverage uses synthetic fixtures.

| Public method | Frozen request | Documented APK name and exact route |
|---|---|---|
| `get_free_seat_car_info(request)` | `FreeSeatCarRequest` | `getFresScar`; `POST /classes/com.korail.mobile.trn.fresScar.do` |
| `get_guide_seat_condition(request)` | `GuideSeatConditionRequest` | `getGuideSeatCnd`; `POST /classes/com.korail.mobile.reservation.guideSeatCnd.do` |
| `get_seat_assignment_schedule(request)` | `SeatAssignmentScheduleRequest` | `getAssignScheduleView`; `POST /classes/com.korail.mobile.research.assignScheduleView.do` |
| `get_merge_seats_inquiry(request)` | `MergeSeatsInquiryRequest` | `getMergeSeatsInquiry`; `POST /classes/com.korail.mobile.research.mergeSeatsC.do` |

The Java names above are documentation aliases only; the client does not add
duplicate camelCase methods. Each public method accepts exactly its matching
request type, composes the documented form with `Device`, `Version`, and `Key`,
issues one POST, and forces `include_dynapath=False`. The forms cannot accept a
caller-supplied mapping or additional wire field. Date/time shapes, ASCII train
and order identifiers, transfer type, and passenger counts are validated
before transport.

These reads do not require a local authenticated-session precondition because
their requests contain no account, PNR, ticket, payment, or point identifier.
They require the full envelope and exact success value `strResult="SUCC"`.
Existing `FAIL`/`WRC000288` application errors remain typed failures, and a
server `P058` clears any existing local session before raising
`KorailSessionExpiredError`.

The schedule responses share an immutable `TrainScheduleItem` representation;
the merge response additionally exposes immutable intermediate stations. Raw
mappings, train/station/car identifiers, and server free text are repr-hidden.
This phase deliberately does not accept `TrainSummary` and adds no convenience
chaining from a search result, seat selection, reservation, fallback request,
or live helper call.

### Static-only limousine schedule and seat reads

Three additional P0 wrappers expose the APK's read-only limousine contracts:

- `get_limousine_schedules(query)` maps the direct schedule-list response.
- `get_limousine_seat_inventory(query)` maps the selected train/car seat list.
- `get_limousine_schedule_view(query)` maps the Sid-bearing schedule-view
  response and its typed train/product rows.

Each method accepts one frozen, closed request dataclass. The schedule and seat
queries require caller-supplied service, schedule, train, and car identifiers;
the schedule-view query additionally requires a caller-supplied menu and job
identifier. The package does not embed the APK's current limousine service,
menu, train-class, station, car, seat-attribute, or sale-division values.
Unknown wire fields cannot be supplied.

All three methods issue exactly one POST with the Retrofit-declared field set
and `include_common=False`. The first two forms explicitly carry `Device`,
`Version`, and the app `Key`; the schedule-view form carries `Device`,
`Version`, and one fresh `Sid`. None has a static authenticated-session
prerequisite in the reviewed caller flow, so a login is not required. Existing
session-expiry handling still clears an already-present local session on
`P058`. The three calls are DynaPath-disabled because none of their exact paths
appears in the APK DynaPath URL list.

Responses use frozen typed schedule, train, recommended-product, and
seat-inventory models. Identifiers, raw mappings, response/free-text messages,
and station names are repr-hidden. These methods expose no seat selection,
seat hold, booking, reservation, payment, cancellation, or fallback request.
No live call was made for this increment; its contract and parser evidence is
limited to exact APK/static sources plus synthetic fixtures.

### UUID and MAAS station reads

`get_uuid()` performs the parameter-free account-neutral UUID read.
`get_maas_menu_list()` performs the generic MAAS menu read used by the app's
main booking screen. It sends only `Device` and `Version`, parses the server's
`menuList[]`, and exposes each `menuList[].addSrvDvCd` as a repr-hidden
`additional_service_code`.
`get_maas_station_data(additional_service_code)` requires the service code that
the official app obtains dynamically. The library has no empty or fixed
service-code default.
None of these requests uses DynaPath, and none of these methods starts a
reservation or passes the UUID value to SRT automatically.

Controlled live evidence showed that the UUID success response can contain a
valid non-empty verification field with only a partial common envelope.
`get_uuid()` therefore opts into relaxed common-envelope decoding for this
request only. The transport default, existing POST behavior, and every other
caller's strict-envelope behavior remain unchanged.

Bounded live verification reads the menu first and selects at most one active
station-capable item using the app's `active` and `appData` routing rules.
`KORAIL_MAAS_SERVICE_CODE` remains an explicit override in the ignored live
environment; it is not a hardcoded service-code source. If no eligible item or
override exists, the helper reports `maasStationTested=false` and performs no
station-list request.

Live smoke is opt-in and limited to login plus read/query calls. DynaPath
device identity values must be supplied explicitly.
KORAIL_ADVERTISING_ID is optional and defaults to an empty string:

```bash
export KORAIL_MOBILE_API_LIVE=1
export KORAIL_MEMBER_NO="<member-id>"
export KORAIL_PASSWORD="<password>"
export KORAIL_DYNAPATH_DEVICE_ID="<android-id>"
export KORAIL_DYNAPATH_OS_VERSION="<android-version>"
export KORAIL_DYNAPATH_DEVICE_MODEL="<device-model>"
export KORAIL_ADVERTISING_ID=""
python3 -c "from korail_mobile_api.live import run_live_smoke_from_env; print(run_live_smoke_from_env())"
```

The helper performs both cache reads and the generic MAAS menu read before
login, then performs the session-coupled deposit-bank and trip-menu reads after
its single login. It emits only booleans, status codes, and bounded counts. Its
metadata is limited to fields such as `appDataLoaded`, `noticeLoaded`,
`maasMenuCount`, `depositBankCount`, and `tripMenuCount`; it does not return raw
account, session, ticket, station, menu, app-data, or notice response bodies.

For the successful-read expansion, the pre-review complete offline suite result
of `427 passed, 1 skipped` is historical. The independent final whole-feature
review reported Critical 0, Important 2, and Minor 0. Both Important findings
were fixed together in `6b25341`, with `192 passed` focused coverage; no open
Critical or Important finding remains. Fresh post-fix verification reported
`435 passed, 1 skipped`; the only skip was the explicit live-service opt-in.

A fresh isolated build produced one wheel and one source distribution, and a
temporary environment installed the wheel and imported `KorailClient` plus all
11 new response types from `site-packages`. The installed package reported
`routes=25`, `public_methods=28`, and `response_types=11`. A fresh static scan
reported `request_literals=27` and `excluded_mutation_routes=0`; the full
feature diff passed `git diff --check`, and the DynaPath files remained
unchanged.

Before this expansion, the corrected UUID contract's tracked Task 6 result was
`275 passed, 1 skipped`, 15 registered routes, and successful isolated imports
of `KorailClient`, `MaasMenuItem`, and `MaasMenuListResponse`. Independent Task
6 spec and quality reviews for that preceding UUID/station phase passed with no
findings.

Independent review confirmed the UUID-only correction changed no routes,
DynaPath behavior or allowlist, existing POST/default behavior, or public API
surface. Final cleanup removed generated package/build artifacts and the
temporary isolated-install environment; the normal Git working tree was clean.

The single corrected bounded live invocation succeeded with
`appDataLoaded=true`, `noticeLoaded=true`, `uuidLoaded=true`,
`loggedIn=true`, `commonCode=API.I00000`, `stationInfoLoaded=true`,
`stationDataCount=281`, `calendarCode=API.I00000`, `trainCount=10`,
`scheduleCode=IRZ000001`, `transferCode=IRZ000001`, and
`ticketCode=WRT300005`. A subsequent bounded MAAS check fetched 11 generic menu
items, identified 4 station-capable items using the app's routing fields, and
made one station-list request with the first server-provided code, returning
101 stations. No service code, menu name, URL, sensitive value, or raw response
is recorded here. An earlier pre-correction live attempt stopped at UUID
envelope validation, which led to the endpoint-specific partial-envelope
correction above.

DynaPath is supported for the documented allowlist paths. Runtime constants
such as `Device`, API version, app key, DynaPath header name, and allowlist paths
are importable from the package. Live smoke constructs `DynapathTokenSettings`
only from required caller-supplied environment values and fails before request
construction when any required identity value is missing.

The built-in generator follows the successful fixed `rt=0` contract: SDK version `v1`,
four uppercase-letter-or-digit random characters, and exactly one
`rt=0` field in each token payload. The app-start timestamp is captured once
when live configuration is built; request history is not accumulated. The raw
application-signature setting is form-encoded exactly once during token
construction.

When enabled, the client attaches `DYNAPATH_HEADER_NAME` only for the documented
DynaPath allowlist paths. Callers that need an external implementation may
still provide a custom `DynapathConfig.token_provider`; the package contains no
separate probe generator and does not retain request history. Login follows the
app sequence and treats only `IRZ000001` or `S200` as final success.

Reservation, payment, refund, check-in, membership mutation, point/mileage mutation, and destructive ticket operations are not implemented in this package version.
