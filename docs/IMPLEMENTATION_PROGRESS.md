# KORAIL Python Package Implementation Progress

Last updated: 2026-07-13 KST

## Current State

- The read-only public API stabilization phase is complete.
- The cache-read expansion implementation, offline tests, package build, and
  isolated import are complete, including bounded live verification.
- The fixed `rt=0` DynaPath replacement and empty advertising-ID default are
  committed on `main`.
- The account-neutral UUID and optional MAAS station read methods, their bounded
  live summaries, and focused offline tests are implemented.
- The UUID-specific partial-envelope correction is complete: `get_uuid()` alone
  changed in that correction to route-specific relaxed common-envelope
  decoding. Pre-existing relaxed cache and station callers remain unchanged,
  as do strict transport defaults and existing strict callers.
- The complete suite, package build, isolated import, static safety checks,
  independent review, and corrected bounded UUID live gate are complete.
- The optional MAAS live gate remains pending because no caller-owned private
  service code was available; no MAAS request was made.

## Implemented Public Operations

- Login and local logout/session clearing
- Common-code lookup
- Account-neutral app-main cache lookup
- Account-neutral notice cache lookup
- Account-neutral UUID lookup
- MAAS station-data lookup with a caller-supplied dynamic service code
- Station information and station-data lookup
- Train calendar lookup
- Train search with station-code resolution
- Actual train schedule lookup
- Transfer-station lookup
- Ticket-list lookup
- Fixed `rt=0` DynaPath generation and exact-path attachment

The transport currently allows 14 exact read/login routes. Reservation,
payment, cancellation, refund, check-in, member mutation, and point/mileage
mutation routes are not callable.

## Verification

- Focused offline UUID/MAAS route, request, parser, model, redaction, public
  contract, and bounded live-helper tests are implemented.
- Task 4 live-helper tests pass for both the absent-code and supplied-code
  branches; the live-service test remains an explicit offline skip.
- Complete offline suite on corrected HEAD: `242 passed, 1 skipped`; the only
  skip was the explicit live-service opt-in.
- Package verification: one wheel and one source distribution built
  successfully; a fresh virtual environment installed the wheel and imported
  `KorailClient`, `UuidResponse`, `KorailStation`, and `StationDataResponse`.
- Static safety verification: 14 registered routes, both UUID/MAAS routes
  present, and neither new route in the DynaPath allowlist.
- Independent Task 6 review: spec pass and quality pass, with no findings.
- Independent review confirmed the UUID-only correction changed no routes,
  DynaPath behavior or allowlist, existing POST/default behavior, or public API
  surface.
- Final cleanup removed generated package/build artifacts and the temporary
  isolated-install environment; the normal Git working tree was clean.
- Corrected bounded live verification: `appDataLoaded=true`,
  `noticeLoaded=true`, `uuidLoaded=true`, `loggedIn=true`,
  `commonCode=API.I00000`, `stationInfoLoaded=true`, `stationDataCount=281`,
  `calendarCode=API.I00000`, `trainCount=10`,
  `scheduleCode=IRZ000001`, `transferCode=IRZ000001`, and
  `ticketCode=WRT300005`.
- MAAS was not called: the ignored live environment contained no private
  service code, so the bounded result was `maasStationTested=false` and
  `maasStationCount=0`. The MAAS live gate remains pending.
- Historical context: the first pre-correction live attempt stopped at UUID
  envelope validation. The resulting correction was limited to UUID's
  live-evidenced partial envelope; no sensitive value or raw response was
  recorded.

The local credential file remains ignored and is not tracked. No credential,
cookie, session token, or generated DynaPath token is stored in the repository.

## Analysis Inventory Versus Implementation

- APK inventory: 165 Retrofit method entries, 159 distinct HTTP/path pairs
- Previously live-successful inventory entries: 24
- Currently implemented underlying routes: 14
- Therefore the complete APK endpoint inventory is not yet implemented

Previously successful read candidates still outside the package include product
and reservation history, cart lookup, delay bank data, pass information,
discount/delay coupons, and receipt lookup. Some require valid ticket,
reservation, or account state.

## Next Required Step

Complete the optional bounded MAAS live gate only when a legitimate,
caller-owned private service code is supplied through the ignored environment.
Do not invent or persist a code. Keep all local credentials and
runtime-sensitive values ignored and out of documentation.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
