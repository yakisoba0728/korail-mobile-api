# KORAIL Python Package Implementation Progress

Last updated: 2026-07-15 KST

## Current State

- Internal release preparation is complete at current `HEAD`: typed-package
  metadata, source-manifest contents, an archive verifier, Python 3.11-3.14
  offline CI, and internal release/security/changelog guidance are present.
  This preparation changed no runtime request, route, credential, or live
  behavior and made no live request.
- The read-only public API stabilization phase is complete.
- The current package boundary is 54 exact login/read routes and 65 public methods (58 login/read plus the consent-gated mutation methods `reserve`,
  `reserve_transfer`, `confirm_standby_hold`, `cancel_unpaid_hold`, `pay_with_fake_card`, `pay_with_card`, and `refund`,
  which return a
  redacted preview by default and send a live state change only with a
  `dry_run=False` matching-category consent via the double-gated
  `post_mutation_form`; `pay_with_fake_card` also requires `fake_card_only` and
  still sends only test cards, while `pay_with_card` requires
  `real_card_acknowledged=True` together with `fake_card_only=False` and is the
  only path that can move real money.
  reserve/cancel/pay were verified live; `pay_with_card` and `refund` have no
  live-verified success envelope). Current service inventory is 32 successful, 10 failed, and 123
  unexecuted entries out of 165.
- The cache-read expansion implementation, offline tests, package build, and
  isolated import are complete, including bounded live verification.
- The fixed `rt=0` DynaPath replacement and empty advertising-ID default are
  committed on `main`.
- The account-neutral UUID, generic MAAS menu, and MAAS station read methods,
  their bounded live summaries, and focused offline tests are implemented.
- The UUID-specific partial-envelope correction is complete: `get_uuid()` alone
  changed in that correction to route-specific relaxed common-envelope
  decoding. Pre-existing relaxed cache and station callers remain unchanged,
  as do strict transport defaults and existing strict callers.
- Generic MAAS menu discovery replaces the former requirement to supply or
  invent a fixed service code. The environment value remains an explicit
  override only.
- Eleven successful-read expansion methods are implemented with frozen models,
  strict parsers, exact payload builders, synthetic fixtures, and no adjacent
  or fallback requests.
- Three additional session-unverified P0 menu/reference methods are implemented
  from static APK evidence and synthetic fixtures: pass menu,
  commuter-kind menu, and crew request options. Their runtime discriminator
  codes are required caller inputs; any live verification starts only after
  login, and the separate state-changing crew-call route remains excluded.
- The `0.2.0` seat-inventory increment implements typed authenticated car and
  physical-seat reads for the fixed main-menu/general-room contract. Both
  exact POST routes validate before Sid generation, issue one request, and
  force DynaPath off. The banner URL is inert and never followed.
- The raw-backed typed response core promotes `StationInfoResponse`,
  `TrainCalendarResponse`, `TrainScheduleResponse`,
  `TransferStationListResponse`, and `TrainSearchMetadata`, while normal
  station data continues to use `StationDataResponse`. Seat and train response
  metadata uses appended, defaulted fields so established positional
  constructors remain compatible. Client call parameters remain unchanged;
  return annotations for five existing read methods are narrowed to typed
  responses. Existing routes and request payload semantics remain unchanged;
  raw mappings remain `repr=False`.
  No capture value, raw body, credential source, or network call
  was used by this increment.
- Three static-only limousine P0 reads implement the exact R04, R05, and R38
  POST contracts. Their frozen query dataclasses require caller-supplied
  service/menu/schedule/train/car identifiers; no live discriminator is
  hardcoded. Every method issues one DynaPath-disabled request and exposes no
  seat selection, hold, reservation, or mutation. Exact concrete query types
  are required and their validators run non-virtually before Sid generation
  or transport. No live call was made.
- A separate evidence command enforces a four-operation ceiling and writes only
  fixed statuses, 0/1 call counters, bounded counts, type-presence booleans, and
  a sufficiency category after a secret scan. It is not part of broad live
  smoke. Bounded live structural evidence now covers both seat-inventory read
  routes without retaining raw response values or identifiers.
- Four P0 train reads were initially implemented from static APK contracts and
  synthetic fixtures: free-seat car guidance, guide-seat conditions,
  seat-assignment schedules, and merged-seat inquiry. Each accepts one frozen
  closed request object, issues one exact POST with DynaPath forced off, and
  returns frozen typed output with identifiers, server free text, and raw
  mappings repr-hidden. That implementation step added no live request or
  `TrainSummary` convenience chain.
- A later bounded authenticated revalidation made 28 requests and received 28
  responses, producing 25 successful operations, one expected typed
  application failure, and three input-dependent skips. Deposit-bank and
  trip-menu reads succeeded after login. R30 `getFresScar` returned exact
  `strResult="SUCC"` and parsed successfully. R33 `getGuideSeatCnd` returned a
  full `FAIL` application envelope for the server-supplied seat attribute,
  surfaced as `KorailAppError`, and was not retried. R37
  `getAssignScheduleView` and R51 `getMergeSeatsInquiry` remain static-only and
  unexecuted. Offline raw replay yielded 27 parsed responses, one expected
  `KorailAppError`, and zero unexpected failures.
- The consolidated final review is complete. Its two Important and one Minor
  KORAIL findings were fixed together; re-review found no remaining Critical,
  Important, or Minor issue.
- The static R20 pass-schedule candidate read is implemented with a closed
  caller-supplied request, one exact DynaPath-disabled POST, strict full
  `SUCC` parsing, and frozen repr-safe models for all eight evidenced train
  fields. The server session rule remains unverified, so a conservative
  client-side login gate remains until a bounded after-login validation.
- The transport now allows 54 exact login/read routes and the client exposes
  65 public methods. No new route was added to the six-path DynaPath allowlist.
- A bounded 2026-07-15 one-session replay exercised the eleven-method expansion
  without raw output. Five wrappers parsed successfully, four stopped at
  `KorailProtocolError`, and two identifier-dependent reads were not issued
  because no caller-owned identifiers were available. Later sanitized
  shape-only evidence resolved cart, delay-discount, and product-reservation
  list envelopes without weakening the remaining strict routes. The same
  evidence established finite ASCII decimal strings for seat-window ratios.

## Fixed and account-shaped read tranche

R13, R32, R43, and R45 are implemented as four conservative authenticated
reads with exact ordered forms and no DynaPath invocation:

- `/classes/com.korail.mobile.cust.mchdDcntTgt.do`
- `/classes/com.korail.mobile.research.custTripInfo.do`
- `/classes/com.korail.mobile.copt.gdReqQry.do`
- `/classes/com.korail.mobile.reservation.tripChgDate.do`

R32 uses only the repr-hidden login response `strCustNo`, with no member-number
or member-card fallback. R43 supports only the current `Device`/`Version` form
or a two-date history form bounded to three calendar months; both forms omit
`Key`. All four validate before their single transport call and require a
local session.

R54 has a strict internal nested response model/parser, but its unresolved
train-group provenance keeps transport unavailable. There is no public client
method, safety route, or raw-string request builder. Historically, the
implementation tranche itself used no live request, credentials, `.env`, or
raw capture and added no mutation capability. Its pre-revalidation inventory
was 28 successful, 9 failed, and 128 unexecuted entries out of 165.

### Bounded next-safe read revalidation

A later bounded authenticated read-only revalidation used an empty advertising
ID, logged in once, and confirmed that the repr-hidden `customer_no` was
available. R13 made one request, returned `WRC800029`, surfaced as
`KorailAppError` and was not retried. R32 succeeded with 0 rows, current-form
R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the existing safe
train search succeeded with 10 rows. R52 made zero requests and was recorded
as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not called. No mutation
route was called, and no credential, identifier, or raw response value was
retained. At that pre-R149 point, inventory was 31 successful, 10 failed, and
124 unexecuted entries out of 165.

## Tagged variants, ordered repeated forms, and fare quote

R17, R31, and R52 add three public static-contract reads. R17 accepts only the
two dated history tags and the reduced payment-eligibility tag, requires a
session, disables DynaPath, and retains its known HTTP-404 status as one typed
transport failure without retry or fallback. R31 accepts only jobs `a`, `b`,
and `c`; its ordered form transport preserves the grouped repeated
`cmtrUtlAgeCd` fields followed by grouped repeated `psgPrnb` fields, while the
ticket reference and all server free text remain repr-hidden. The public R31
wrapper conservatively requires a session.

R52 accepts only one or two exact `PriceFareLeg` values plus `menu_id`, which
defaults to the app's client-side constant `"11"` (`a5/k.java:92-94`); it no
longer sources that value from `TrainSearchMetadata`, because the response key
that field was parsed from (`h_menu_id`) does not exist in the app. It derives
its transfer division, preserves leg
order in comma-joined columns, and intentionally omits `trnCnt`. It forces no
local session and uses only the existing conditional DynaPath behavior; the
DynaPath allowlist is unchanged.

R39 has full synthetic response parsing and an internal exact request builder,
but remains outside both `KorailClient` and the read-only safety registry. Its
NetFunnel `service_1` / `act_6` gate was the reason recorded here and is no
longer missing — see the NetFunnel section below — so what holds R39 back now is
its unregistered route, not the queue. R54 remains held for its
unresolved discriminator provenance. Across the complete seven-read tranche,
the boundary at that historical step was 45 routes and 48 public methods.
Historically, that
implementation step made no live request and its pre-revalidation inventory
was 28 successful, 9 failed, and 128 unexecuted out of 165; it also made no
credential access, `.env` read, secure-raw access, or mutation expansion. The
pre-R149 inventory was 31 successful, 10 failed, and 124 unexecuted entries out
of 165; current inventory is 32 successful, 10 failed, and 123 unexecuted. The
current package boundary is 54 exact routes and 65 public methods.

## Ticket-reference static read tranche

R137, R138, R146, R148, and R149 add five conservative authenticated reads.
R137 reuses one exact repr-hidden `OriginalTicketReference`; R138 accepts only
one exact repr-hidden PNR request object. R146 and R148 accept only a nonempty
exact tuple of exact ticket references, derive each repeated `tkRetNo` from its
four components in order, and require exact count equality with R146's JSON
integer-style form value or R148's canonical decimal-string form value. R149
derives `custMgNo` solely from the repr-hidden login `customer_no`.

All five routes validate before transport, issue at most one request, require a
local session, force DynaPath off, and parse only a full exact `SUCC` envelope.
The nested models and raw mappings are repr-safe and redaction-covered. This
implementation used only static APK evidence plus synthetic/mock tests: no
live I/O, credential access, secure raw capture, retry, fallback, adjacent
mutation, or DynaPath expansion occurred. At implementation completion, the
pre-R149 inventory was 31 successful, 10 failed, and 124 unexecuted out of
165; the boundary is 54 exact routes and 61 public methods, with six DynaPath
allowlist paths.

The ticket-reference implementation itself used no live I/O and added no
mutation capability.

A later bounded authenticated read-only revalidation used an empty advertising
ID, made one successful login call, confirmed logged-in state and
customer-number presence, and called only R149 once. R149 succeeded with one
row and was not retried; R137, R138, R146, and R148 made zero calls. No
mutation, raw response, PII, credential, or server message was retained.
Current inventory is 32 successful, 10 failed, and 123 unexecuted out of 165.

## Implemented Public Operations

- Login and local logout/session clearing
- Common-code lookup
- Account-neutral app-main cache lookup
- Account-neutral notice cache lookup
- Account-neutral UUID lookup
- Generic account-neutral MAAS menu lookup
- MAAS station-data lookup with a caller-supplied dynamic service code
- Station information and station-data lookup
- Train calendar lookup
- Train search with station-code resolution
- Actual train schedule lookup
- Transfer-station lookup
- Ticket-list lookup
- Fixed `rt=0` DynaPath generation and exact-path attachment
- Account-neutral service-status and pass available-date lookup
- Authenticated deposit-bank and trip-menu lookup
- Session-unverified pass-menu, commuter-kind-menu, and crew-request-option
  lookup; any live verification requires prior login
- Authenticated cart, delay-discount, and discount-coupon lookup
- Authenticated product reservation list and caller-owned product detail lookup
- Authenticated ticket receipt and reservation-history lookup
- Authenticated general-room car-list and physical-seat inventory lookup
- Account-neutral free-seat car and guide-seat-condition lookup through closed
  request objects
- Account-neutral seat-assignment schedule and merged-seat inquiry through
  closed request objects
- Static-only limousine schedule-list, seat-inventory, and schedule-view lookup
- Client-gated pass-schedule candidate lookup with caller-supplied runtime
  values; no pass reservation or payment operation
- Consent-gated reservation hold for an arbitrary passenger mix
  (`KorailPassengerCounts`: 어른, 청소년, 어린이, 동반유아, 경로, 1~3급 장애,
  4~6급 장애, 안내견) in either cabin (`KorailSeatClass`: 일반실 / 특실). Both
  `reserve` parameters are keyword-only and default to one adult in a general
  seat, which reproduces the previously sent form exactly. `txtTotPsgCnt` is
  every row summed, the 동반유아 and the 안내견 included, as the app computes
  it; the mix is capped at `KORAIL_MAX_PASSENGERS_PER_RESERVATION` (9). Only
  the one-adult general-seat form is live-verified; the multi-passenger and
  특실 wire shapes are static-evidenced and have never been transmitted
- Consent-gated 환승 (transfer) search and reservation — `search_transfer_trains`,
  `search_trains_with_transfer_fallback` and `reserve_transfer`. **Implemented
  and NOT live-verified**: no transfer search and no transfer hold built by this
  package has reached KORAIL. The transfer query is the direct query with
  `radJobId="2"` and nothing else changed (`DirectInquiryActivity.java:284-296`);
  the response is the same flat `trn_infos.trn_info` list paired positionally
  into two-leg itineraries (`a5/k.java:156-170`). The reservation form is the
  existing one with the sixteen-key journey block repeated, `txtJrnyCnt="2"`,
  `txtJrnyTpCd` = `14` on **both** legs and `txtJrnySqno` = `001`/`002`
  (`C5/a.java:52-119`, the journey-type and sequence ternaries re-read from
  bytecode at `smali/C5/a.smali:306-338` and `:343` because they key on
  different things). Two legs is the app's ceiling, not this package's:
  `OSeat.java:32-35` and `OSrcar.java:21-30` both split on "journey 1 or not",
  so a third leg would overwrite leg 2. The single-leg call is byte-for-byte
  unchanged, key order included. Passenger mix composes per booking, cabin class
  and 좌석지정 compose per leg, and 예약대기 (`1102`) is refused because the app
  gates it twice (`a5/k.java:120-127`, `DirectInquiryActivity.java:434`)
- Known gap, deliberately not closed here: `cancel_unpaid_hold` accepts a hold
  whose `h_jrny_cnt` is numerically one, so it cannot release a two-journey
  transfer hold. The app has no such restriction:
  `DReservationConfirmActivity.java:269-278` forwards `getH_jrny_cnt()` verbatim
  as `txtJrnyCnt` beside the same fixed
  `txtJrnySqno="0001"`/`hidRsvChgNo="000"`, so the fix is to forward the hold's
  own count. It touches the cancel path, which was out of scope for
  the transfer change, and it blocks a clean live reserve → cancel round trip
  for a transfer until it lands

The read-only transport (`post_form`/`get_json`) refuses every mutation route
and allows 54 exact read/login routes. The reservation, unpaid-cancel, payment,
and refund routes are callable only through the separate consent-gated send path
(`post_mutation_form`, `dry_run=False`); check-in, member mutation, and
point/mileage mutation routes remain not callable.

Pure offline parsers now cover the evidenced reservation-hold and reservation-
payment response shapes, including nested journey/coupon rows and recursive
redaction of PNR, window, temporary-job, change, certificate, coupon, and ticket
handoff fields. They add no client route. In one authorized bounded check, a
single unpaid direct reservation was created and both cancellation steps
completed once; reservation history was empty before and after. The check made
no payment request and printed or persisted no raw response or identifier.

## Verification

- Static-only P0 TDD RED: the focused endpoint/public-contract command reported
  `48 failed, 10 passed`, with failures rooted in the absent four request
  types, builders, parsers, response models, methods, and route contracts.
- Static-only P0 focused GREEN: `58 passed`. The neighboring HTTP,
  successful-read, and seat-inventory regression suites report `419 passed`.
  All inputs and responses are synthetic or mocked; no live I/O ran.
- Independent-review envelope RED: the four new parsers accepted each of
  `None`, empty, `ERROR`, and `SUCCESS`, producing `16 failed, 48 passed`.
  Route-selected strict-envelope GREEN is `64 passed`: only exact `SUCC`
  succeeds, while existing `FAIL`, `P058`, and `WRC000288` behavior remains.
- P0 menu/reference TDD recorded focused RED failures for the absent route
  contracts, payload builders, typed parsers, public methods, exports, and
  documentation. Focused GREEN reports `56 passed` for the runtime/public
  contract gate, using only mock transport and synthetic fixtures.
- Limousine-read TDD RED: the focused contract command stopped during
  collection on the missing limousine public models/module before production
  code existed.
- Limousine validator-hardening RED: all three synthetic query subclasses
  reached their public builders without the expected `TypeError`. The targeted
  GREEN reports `3 passed` and also proves no Sid generation or transport.
- Limousine-read focused GREEN: `552 passed`; the limousine, public-contract,
  README, HTTP, session, successful-read, and seat-inventory tests are wholly
  synthetic or mocked and perform no live I/O.
- Seat-inventory TDD RED: the focused test command stopped during collection on
  the missing `PhysicalSeat` public interface, as expected before production
  code existed.
- Seat-inventory focused GREEN: `150 passed`; the cross-cutting seat, HTTP,
  public-contract, and legacy-model gate reports `271 passed`. All tests are
  synthetic or mocked and perform no live I/O.
- Pass-schedule TDD RED reported 33 expected missing-contract failures. Its
  focused GREEN reports `33 passed` with no live I/O.
- Integrated review found that three P0 menu and three limousine parsers could
  accept non-`SUCC` success-shaped envelopes. All six now require exact
  `strResult=SUCC`. Retained raw replay parsed 24 responses, preserved two
  expected pre-login `P058` responses, and reported zero unexpected failures;
  it also confirmed ASCII decimal strings for station popup types and actual
  arrival delay counts.
- The current full offline release gate reports
  `2090 passed, 1 deselected`; only the explicitly opted-in live-service test
  is deselected. Historically the same gate reported `1246 passed, 1 deselected`
  before the P0 live-evidence documentation contract test and
  `1247 passed, 1 deselected` directly after it.
- Python 3.14 built `korail_mobile_api-0.2.0-py3-none-any.whl` and
  `korail_mobile_api-0.2.0.tar.gz` in a temporary directory. The distribution
  verifier accepted both artifacts, `git diff --check` passed, and all
  generated build, metadata, and temporary distribution paths were removed.
- Bounded seat-inventory structural result: the eligible search contained 10
  rows, the car route returned `IRG000000`/`SUCC` with 5 cars, and the seat
  route returned `IRG000000`/`SUCC` with 75 seat rows. Every documented field
  type matched. Live data also proved that `floor` may be absent, windows may
  be empty, and non-empty seat labels may repeat; the parser now accepts those
  shapes while preserving row order and cardinality. The run persisted no raw
  mapping, response message, identifier, date, station value, Sid, credential,
  cookie, token, URL, or exception text.
- A post-fix evidence-helper confirmation later stopped at the service-status
  preflight before the login POST. Its search, car-list, and seat-list counts
  were all zero. A combined read gate observed the same preflight state and
  made no endpoint calls, so no rapid retry or bypass was attempted.
- The final 2026-07-15 combined gate later logged in successfully with an empty
  advertising ID. The seat chain again returned 10 eligible search rows, 5
  cars, 75 seats, and zero windows. Of the eleven expansion reads, service
  status, deposit banks (56 rows), discount coupons (typed empty), trip menu (5
  rows), and reservation history (typed empty) parsed successfully. Cart,
  delay-discount tickets, pass available dates, and product reservations ended
  in `KorailProtocolError`; product detail and ticket receipt were not called
  without owned identifiers. Only fixed statuses and bounded counts were
  emitted, and the session was closed after this single combined run.
- Fresh internal release gate: the focused contract test reported `1 passed`;
  the complete offline suite reported `436 passed, 1 skipped in 0.30s`, with
  only the explicit live-service opt-in skipped.
- Python 3.14 built `korail_mobile_api-0.1.0-py3-none-any.whl` and
  `korail_mobile_api-0.1.0.tar.gz` in a temporary artifact directory. The
  distribution verifier accepted both, including `py.typed`, metadata,
  required source documents, and forbidden-member checks.
- A fresh temporary virtual environment installed the wheel and imported
  `KorailClient` from `site-packages` outside both source worktrees. All
  temporary paths plus generated `build/`, `dist/`, and `src/*.egg-info`
  directories were removed.
- Focused offline UUID/MAAS route, request, parser, model, redaction, public
  contract, and bounded live-helper tests are implemented.
- Historical pre-review evidence: the successful-read expansion's consolidated
  request, parser, redaction, public-contract, and existing read regression
  gate reported `367 passed`.
- The expanded tests cover exact method/path/fields, validation before I/O,
  local authentication boundaries, session-expiry clearing, typed empty
  `WRG000000` and `P100` results, wrapper and numeric shape validation, raw
  identity, immutable tuples, and sensitive repr exclusion.
- Live-helper tests cover server-discovered code, explicit override, and no
  eligible menu branches; the live-service test remains an explicit offline
  skip unless the caller opts in.
- Historical pre-review complete-suite evidence: `427 passed, 1 skipped`.
- Fresh post-fix complete offline suite: `435 passed, 1 skipped in 0.27s`; the
  only skip was the explicit live-service opt-in.
- Fresh package verification: one wheel and one source distribution built
  successfully in temporary paths; a fresh temporary virtual environment
  installed the wheel and imported `KorailClient` plus all 11 new response
  types from `site-packages`. The installed wheel reported `routes=25`,
  `public_methods=28`, and `response_types=11`.
- Static safety verification: 25 registered routes. UUID, MAAS menu, MAAS
  station, and all 11 expansion calls explicitly disable DynaPath even under a
  custom allowlist.
- The fresh final static scan reported `request_literals=27` and
  `excluded_mutation_routes=0`. `git diff --check a331d63..HEAD` passed, and
  the DynaPath implementation and constants remained unchanged.
- The implementation self-check found all 22 new dataclasses frozen, all raw
  and sensitive fields repr-hidden, and the pre-existing DynaPath code and
  constants unchanged.
- The independent final whole-feature review reported Critical 0, Important 2,
  and Minor 0. Both Important findings were fixed together in `6b25341`: the
  central redaction boundary now covers the missing typed/trip-menu keys, and
  reservation history stores its flattened tuple in `items`. Focused post-fix
  coverage reported `192 passed`, and no Critical or Important finding remains
  open.
- Independent Task 6 review: spec pass and quality pass, with no findings.
- Independent review confirmed the UUID-only correction changed no routes,
  DynaPath behavior or allowlist, existing POST/default behavior, or public API
  surface.
- Final whole-feature hardening added a default-preserving per-request DynaPath
  opt-out for UUID and MAAS. Custom-allowlist regressions prove neither call can
  generate or attach a token, while the token engine and default allowlist are
  unchanged. The earlier package build, isolated imports, and `14/2/0` static
  boundary were reverified after that fix.
- Final cleanup removed generated package/build artifacts, ignored package
  metadata, and the temporary isolated-install environment; the normal Git
  working tree was clean.
- Corrected bounded live verification: `appDataLoaded=true`,
  `noticeLoaded=true`, `uuidLoaded=true`, `loggedIn=true`,
  `commonCode=API.I00000`, `stationInfoLoaded=true`, `stationDataCount=281`,
  `calendarCode=API.I00000`, `trainCount=10`,
  `scheduleCode=IRZ000001`, `transferCode=IRZ000001`, and
  `ticketCode=WRT300005`.
- Bounded MAAS live verification used no fixed code: the generic strict-envelope
  response contained 11 menus, 4 matched the app's active station-selection
  routing, and the first eligible server-provided `addSrvDvCd` produced 101
  stations in one station-list request. The code, names, URLs, and raw response
  were not printed or persisted.
- Historical context: the first pre-correction live attempt stopped at UUID
  envelope validation. The resulting correction was limited to UUID's
  live-evidenced partial envelope; no sensitive value or raw response was
  recorded.

The local credential file remains ignored and is not tracked. No credential,
cookie, session token, or generated DynaPath token is stored in the repository.

## NetFunnel virtual waiting room

Status: **implemented, off by default, and partly live-confirmed (2026-07-26).**
Probing on that date ran the protocol against `nf.letskorail.com` and settled
the inferences recorded below: the response shape is the native SDK's
`<code>:<params>`, the entry sequence is `5101` → `5002` → gated call → `5004`,
and the queue is a **pool of hosts** rather than one. The slot-release path was
exercised end to end.

**The `201` queued path is still NOT live-exercised.** The server was not
queueing — `5101` answered `nwait=0` and admitted us at once — so the polling
loop, the ttl sleep and the two bounds are covered by fixtures only. That is the
same standing as the sibling SRT client's polling path. The handshake should be
read as verified; the wait, as built-and-unproven.

What the APK establishes, with the file and line for each constant:

| Fact | Evidence |
| --- | --- |
| Front-door host `nf.letskorail.com`, https, port 443, timeout 3s | `com/korail/talk/application/KTApplication.java:79-85` |
| Follow-up opcodes go to the `ip`/`port` the previous reply named | `T6/d.java:17-19` (`makeURL`), gated on `host_notmodify`, which is `false` at `T6/h.java:43` (`isHostNotmodify()` at `:134-135`) and never set by `KTApplication`; `T6/i.java:50-53` reads `ip`/`port` into that host/port |
| Path `/ts.wseq` | `T6/h.java:31` (held in the field whose getter is named `getQuery`), used as the path by `U6/c.java:26-33` |
| Service id `service_1` | `K4/g.java` `NETFUNNEL_SERVER_ID` |
| Action ids `act_8` / `act_8_2` / `act_14` / `act_18` / `act_22` / `act_6` / `act_21` / `act_4` | `K4/g.java:43-51` |
| Opcodes 5002 / 5003 / 5004 / 5101 / 5105 / 5106 | `T6/c.java:6-11` — identical to SRT's |
| Status codes 200/201/202/300/301/302/303/502 | `T6/a.java`, and `analysis/apktool/smali/T6/a.smali` where jadx substituted unrelated named constants: `0xc8`–`0xca` at :510-574, `0x12c`–`0x12f` at :228-281, `0x1f6` at :319 |
| Request parameters and their order | `T6/d.java:99-101` (5101), `:54-55` (5002), `:78-79` (5004), rendered in `addParam` order by `U6/a.java:180-185` |
| ttl clamp 1..30 | `T6/i.java:175-181` with `max_ttl` 30 from `T6/h.java:40`, asked for at `T6/g.java:462` |
| Release runs on both paths | `NetfunnelDao.java:41` called from `BaseDaoHelper.java:105-107` (`onPostExecute`) |

One thing the APK gets **wrong about the live server**, found by the 2026-07-26
probe and now the shape of `acquire()`:

| Request | Live answer |
| --- | --- |
| `5101` `sid=service_1&aid=act_8` | `200:key=<252 chars>&nwait=0&nnext=0&tps=0.000000&ttl=0&ip=…` |
| `5004` with that key | `503:msg="Wrong Server ID"` — also with `sid`/`aid` re-attached |
| `5002` with that key | `200:key=<a different, shorter key>&…` |
| `5004` with the `5002` key | `200:key=&nwait=0&…&chk_enter_cnt=0&…` |

The `5101` key is a **ticket to enter**, not a completable session; only what
`chkEnter` issues can be released, and each step's key supersedes the previous
one. Read literally, `T6/g.java`'s poll loop leaves on any non-`201` status
(the smali fall-through at `T6/g$a.smali:243-247` → `:282` → `:892` is a
`return`), so the app sends no `5002` after a `200` from `5101` and completes
with the ticket. The live server overrides that reading, and the `5002` stays
unconditional because `5101` → `5002` → `5004` is the only sequence ever seen to
release cleanly. `T6/d.java` does corroborate the supersession — one response
object overwritten at `:61` and `:107`, with `Complete()` sending whatever key
arrived last (`:79`).

### The queue is a pool of nodes (diagnosed live, 2026-07-26)

`nf.letskorail.com` is a **front door** that load-balances the entry call. The
node it lands on is the only one that can complete the session, and every reply
names that node in its `ip`/`port`. This client declined to follow the naming and
sent every opcode to the front door, so slot release failed
**non-deterministically, about half the time** — five acquire-then-release
cycles:

```
acquire said ip=rnf12.letskorail.com  -> release 503
acquire said ip=rnf12.letskorail.com  -> release 503
acquire said ip=rnf13.letskorail.com  -> release 503
acquire said ip=rnf14.letskorail.com  -> release 200
acquire said ip=rnf13.letskorail.com  -> release 200
```

and the controlled pair:

```
acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
  release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
  release via rnf13.letskorail.com -> 200:key=&nwait=0&…
```

**`Wrong Server ID` is literal, and that is worth writing down**, because the
message reads like a credential or parameter complaint and is neither: the front
door does not own a session a queue node issued. The releases that appeared to
work were the balancer happening to land back on the owning node — the same
reason the same key sometimes released fine. The cost of staying pinned was
leaking roughly half of every slot taken, i.e. the behaviour NetFunnel exists to
prevent.

Which host each opcode goes to:

| opcode | host | why |
| --- | --- | --- |
| `5101` `getTidChkEnter` | the front door, `nf.letskorail.com` | it is the call the front door balances, and there is no previous reply to name a node |
| `5002` `chkEnter` | the node the previous reply named | the session belongs to that node |
| `5004` `setComplete` | the node that issued the session | anyone else answers `503:msg="Wrong Server ID"` |

The node rides on `KorailNetFunnelToken.node` and supersedes exactly as the key
does: a reply that names no node leaves the last one in force, and a bypass has
neither a session nor a node.

**The redirect is constrained, not trusted.** The rule sits in `safety.py` beside
the origin assertions (`korail_netfunnel_node_url`,
`assert_korail_netfunnel_node_origin`, `assert_korail_netfunnel_opcode_origin`),
not in the client, and admits only `rnf<1-99>.letskorail.com` — lowercase, no
leading zero, matched as whole labels — or the front door itself, `https` on port
`443` and no other port. Anything outside it is a **hard error**, never a silent
fall-back to the front door: falling back quietly is what produced the flaky
release, because it converts "this reply is lying to us" into "this slot leaked",
and a leaked slot is unobservable. `assert_korail_netfunnel_origin` still refuses
a node — it guards the configured origin and the entry call — so widening one
guard cannot widen the other. `follow_redirects` stays `False`; an HTTP `30x` is
a different mechanism. The canonical-origin guarantee for `smart.letskorail.com`
is untouched by all of this.

`503` is refused rather than accepted next to the `502` we do accept: treating
"Wrong Server ID" as a release is how the slot leaks unnoticed. The exception
message names both causes — an unexchanged ticket, or the wrong node.

Two premises did not survive the APK and were stopped rather than forced.

1. **The wire dialect.** `nf.letskorail.com` serves both KORAIL and SRT, but the
   two apps embed different client SDKs for the one STCLab product. SRT is a
   WebView over `netfunnel.js` and sends `nfid`, `prefix`, `js=yes` and a
   trailing epoch millisecond; `korail.apk` embeds the native Android SDK (the
   `T6`/`U6` packages) and sends none of them. Consequently `sid`/`aid` ride on
   `5101` only — not on `5002`, which is where the JavaScript dialect puts them
   — and `ttl` is never returned to the server at all, being read purely to
   decide how long to sleep. The `js=yes` distinction that cost the SRT work real
   debugging simply has no application here.
2. **The response shape.** `T6/i.java:36-43` reads everything before the first
   `:` as the status code, so the reply must be `<code>:<params>`. The JS
   dialect's `<rtype>:<code>:<params>` would parse as code `5002` and yield no
   key, i.e. the app itself could not read it. This was the one inference in the
   subsystem with no live confirmation; the 2026-07-26 probe **confirmed it** —
   every reply above arrived in exactly that form. `parse_netfunnel_body` still
   rejects a `NetFunnel.gRtype=…` body and names that possibility in its error,
   now as a diagnosis for a server that changed rather than as a hedge.

The third premise held and is worth restating because it determines the design:
**no Retrofit interface in the app carries a NetFunnel key parameter.** The
queue gates the call rather than parameterising it, so `KorailNetFunnelClient`
is a standalone client on its own host and every mutation and read still sends
exactly the body it sent before.

Deliberate divergences from the app, both narrowing:

- The app polls indefinitely (`T6/g.java:449`) behind a dialog a human can
  close. We bound the wait at 20 polls and 60 seconds, whichever comes first, and
  add no retry logic anywhere.
- The app follows the `ip`/`port` naming to any host at all. We follow it only
  into the pool rule above, and refuse anything else outright — the redirection
  is admitted because the queue needs it, not because the response is trusted.
  (This entry used to read "we pin the origin instead; a response must not choose
  where the next request goes." That was the right instinct and the wrong
  outcome: it leaked about half our slots. The instinct now lives in the rule.)
- `aliveNotice` (5003), `init` (5105) and `stop` (5106) are declared as constants
  and rejected by the request guard. The first keeps a popup alive that this
  library never renders; the other two are administrative and the app's own SDK
  refuses them without touching the network (`T6/d.java:115-121`).

`act_8_2` is the reason the subsystem exists at all. `b5/c.java:439`,
`MainBookingActivity.java:749` and `OldMainBookingActivity.java:321` choose it
over `act_8` when the departure date is a peak-season date, and a separate
action is a separate queue on the server. `S4/C0805e.java:116-121` answers
`isPeakSeason` from the 열차운행달력 the app has already downloaded — the same
response `get_train_calendar()` reads — so the choice is a lookup, not a
calendar rule this package reimplements. `inquiry_action(peak_season=...)` takes
the flag for that reason.

`KORAIL_READ_ONLY_ROUTES` remains 54 app routes with `/ts.wseq` outside it, so
the read path cannot reach the queue and the queue client cannot reach
`smart.letskorail.com` — neither the front door nor any pool node changes that.

## Analysis Inventory Versus Implementation

- APK inventory: 165 Retrofit method entries, 159 distinct HTTP/path pairs
- Live-successful inventory entries: 32
- Currently implemented exact login/read routes: 50
- Therefore the complete APK endpoint inventory is not yet implemented

All recorded successful read entries now have an exact package route. The
remaining APK inventory is outside this read expansion and includes unverified
or state-changing operations.

## Package Handoff Summary

This section consolidates the current-package handoff facts that were previously
tracked in the removed session-handoff note; their outcomes are preserved here,
in the CHANGELOG, and under `docs/superpowers/specs/`.

The current implementation evidence establishes 54 routes at the exact
login/read transport boundary and 65 public methods on `KorailClient`. The
read-only path exposes no callable mutation route; reservation, unpaid-cancel,
fake-card payment, acknowledged real-card payment, and refund are callable only
through the separate
consent-gated `post_mutation_form` path, while check-in, membership, and
point/mileage mutation routes remain not callable. The current service inventory is 32 successful, 10 failed,
and 123 unexecuted entries out of 165; the historical pre-revalidation inventory
was 28 successful, 9 failed, and 128 unexecuted.

App-level failures are now classified on `h_msg_cd` rather than surfacing as one
undifferentiated `KorailAppError`. The taxonomy is a pure refinement: every new
type subclasses the one it replaces, `code`/`message`/`raw` remain on all of
them, and `classify_app_error` is called only where a `KorailAppError` was
already being raised (`src/korail_mobile_api/http.py:46`,
`src/korail_mobile_api/read_parsers.py:141`), so it never introduces a failure
the server did not declare. Failure is still decided by `strResult` plus the
app's own `WRC000288`, matching the app, whose dispatcher passes any
unrecognised code on a non-`FAIL` response through to `onReceive()` as a success
(`analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:629`) — which
is why the live-observed `WRR664296` warning stays a successful reservation. See
the error-taxonomy table in `README.md` for which exception means retry is
pointless, which means re-login, and which means the request was fine and there
was simply nothing there. `IRT010110` (srtgo's second sold-out code) and
srtgo_plus's `MACRO` substring rule are recorded as third-party-attested only
and deliberately not encoded; the anti-macro refusal on this app is the
`DynaPath-Result` header, already carried by `KorailDynaPathError`.

The current reviewed offline gate reports `2090 passed, 1 deselected`; the
historical gates were `1246 passed, 1 deselected` and, after the P0
live-evidence documentation coverage, `1247 passed, 1 deselected`. In every one
of those gates, the deselected test is the explicitly opted-in live-service
test.

The bounded seat-inventory structural run returned `IRG000000`/`SUCC` with 5
cars and 75 seat rows while retaining no raw values; a later post-fix
confirmation stopped at the service-status preflight before login transport and
therefore made no search, car-list, or seat-list call.

Use [docs/RELEASE.md](RELEASE.md) for the internal-only offline test, build,
distribution verifier, fresh-wheel install, and cleanup gate. A public release
remains blocked by the four items listed there.

## Next Required Step

The typed seat-inventory contract now has repeated bounded live structural
evidence for both read routes, including finite ASCII decimal-string window
ratios. Pass availability still has no body in the current shape-only capture;
obtain separately reviewed evidence before changing that parser. Do not infer
raw response structure from exception classes. Any additional
reservation-linked route requires its own safety review and caller-owned data.
Keep all local credentials and runtime-sensitive values ignored and out of
documentation.
