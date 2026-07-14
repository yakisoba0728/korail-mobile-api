# KORAIL Python Package Implementation Progress

Last updated: 2026-07-14 KST

## Current State

- The read-only public API stabilization phase is complete.
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
- The transport now allows 25 exact login/read routes and the client exposes
  28 public methods. No new route was added to the DynaPath allowlist.
- No live replay was performed for this expansion. The preceding bounded UUID
  and MAAS evidence remains historical context and was not repeated.

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
- Account-neutral service-status and deposit-bank lookup
- Account-neutral pass available-date and trip-menu lookup
- Authenticated cart, delay-discount, and discount-coupon lookup
- Authenticated product reservation list and caller-owned product detail lookup
- Authenticated ticket receipt and reservation-history lookup

The transport currently allows 25 exact read/login routes. Reservation,
payment, cancellation, refund, check-in, member mutation, and point/mileage
mutation routes are not callable.

## Verification

- Focused offline UUID/MAAS route, request, parser, model, redaction, public
  contract, and bounded live-helper tests are implemented.
- The successful-read expansion's consolidated request, parser, redaction,
  public-contract, and existing read regression gate reported `367 passed`.
- The expanded tests cover exact method/path/fields, validation before I/O,
  local authentication boundaries, session-expiry clearing, typed empty
  `WRG000000` and `P100` results, wrapper and numeric shape validation, raw
  identity, immutable tuples, and sensitive repr exclusion.
- Live-helper tests cover server-discovered code, explicit override, and no
  eligible menu branches; the live-service test remains an explicit offline
  skip unless the caller opts in.
- Current complete offline suite: `427 passed, 1 skipped`; the only skip was
  the explicit live-service opt-in.
- Package verification: one wheel and one source distribution built
  successfully in temporary paths; a fresh temporary virtual environment
  installed the wheel and imported `KorailClient` plus all 11 new response
  types from `site-packages`. The installed wheel reported `routes=25` and
  `public_methods=28`.
- Static safety verification: 25 registered routes. UUID, MAAS menu, MAAS
  station, and all 11 expansion calls explicitly disable DynaPath even under a
  custom allowlist.
- The final static source scan inspected 27 literal `get_json`/`post_form`
  targets across `src/` (and `scripts/` when present) and reported zero
  excluded mutation calls and zero excluded mutation routes. `git diff
  --check` passed.
- The implementation self-check found all 22 new dataclasses frozen, all raw
  and sensitive fields repr-hidden, and the pre-existing DynaPath code and
  constants unchanged. No confirmed Critical or Important implementation
  concern remained; the separate independent integration review is not
  represented as part of this implementation check.
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
- Live-successful inventory entries: 25
- Currently implemented exact login/read routes: 25
- Therefore the complete APK endpoint inventory is not yet implemented

All recorded successful read entries now have an exact package route. The
remaining APK inventory is outside this read expansion and includes unverified
or state-changing operations.

## Next Required Step

No required work remains in the successful-read expansion. Any additional
reservation-linked route requires its own safety review and caller-owned data;
do not infer or persist identifiers. Keep all local credentials and
runtime-sensitive values ignored and out of documentation.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
