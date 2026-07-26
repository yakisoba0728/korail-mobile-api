# KORAIL Python Package Implementation Progress

Last updated: 2026-07-15 KST

## Current State

- Internal release preparation is complete at current `HEAD`: typed-package
  metadata, source-manifest contents, an archive verifier, Python 3.11-3.14
  offline CI, and internal release/security/changelog guidance are present.
  This preparation changed no runtime request, route, credential, or live
  behavior and made no live request.
- The read-only public API stabilization phase is complete.
- The current package boundary is 54 exact login/read routes and 61 public methods (56 login/read plus the consent-gated mutation methods `reserve`,
  `cancel_unpaid_hold`, `pay_with_fake_card`, `pay_with_card`, and `refund`,
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
  61 public methods. No new route was added to the six-path DynaPath allowlist.
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
but its missing normal NetFunnel `service_1` / `act_6` gate keeps it outside
both `KorailClient` and the read-only safety registry. R54 remains held for its
unresolved discriminator provenance. Across the complete seven-read tranche,
the boundary at that historical step was 45 routes and 48 public methods.
Historically, that
implementation step made no live request and its pre-revalidation inventory
was 28 successful, 9 failed, and 128 unexecuted out of 165; it also made no
credential access, `.env` read, secure-raw access, or mutation expansion. The
pre-R149 inventory was 31 successful, 10 failed, and 124 unexecuted entries out
of 165; current inventory is 32 successful, 10 failed, and 123 unexecuted. The
current package boundary is 54 exact routes and 61 public methods.

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
  `1778 passed, 1 deselected`; only the explicitly opted-in live-service test
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
login/read transport boundary and 61 public methods on `KorailClient`. The
read-only path exposes no callable mutation route; reservation, unpaid-cancel,
fake-card payment, acknowledged real-card payment, and refund are callable only
through the separate
consent-gated `post_mutation_form` path, while check-in, membership, and
point/mileage mutation routes remain not callable. The current service inventory is 32 successful, 10 failed,
and 123 unexecuted entries out of 165; the historical pre-revalidation inventory
was 28 successful, 9 failed, and 128 unexecuted.

The current reviewed offline gate reports `1778 passed, 1 deselected`; the
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
