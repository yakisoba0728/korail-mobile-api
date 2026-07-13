# KORAIL Python Package Implementation Progress

Last updated: 2026-07-13 KST

## Current State

- The read-only public API stabilization phase is complete.
- The cache-read expansion implementation, offline tests, package build, and
  isolated import are complete, including bounded live verification.
- The fixed `rt=0` DynaPath replacement and empty advertising-ID default are
  committed on `main`.

## Implemented Public Operations

- Login and local logout/session clearing
- Common-code lookup
- Account-neutral app-main cache lookup
- Account-neutral notice cache lookup
- Station information and station-data lookup
- Train calendar lookup
- Train search with station-code resolution
- Actual train schedule lookup
- Transfer-station lookup
- Ticket-list lookup
- Fixed `rt=0` DynaPath generation and exact-path attachment

The transport currently allows 12 exact read/login routes. Reservation,
payment, cancellation, refund, check-in, member mutation, and point/mileage
mutation routes are not callable.

## Verification

- Offline tests: `197 passed, 1 skipped`
- Wheel and sdist build: passed after the cache expansion
- Fresh-venv wheel install/import: passed for `KorailClient`,
  `AppDataResponse`, `AppVersionInfo`, and `NoticeResponse`
- Cache parser, exact-route, timestamp, malformed-response, public-contract,
  pre-login ordering, raw-output, and fixed-RT DynaPath tests: passed
- The official bounded live helper completed successfully with the promoted
  fixed `rt=0` engine: app-data and notice caches loaded, login succeeded,
  common code returned `API.I00000`, 281 stations loaded, the calendar returned
  33 days, and train search returned 10 rows
- Schedule and transfer reads returned `IRZ000001`; the member ticket-list
  request used `txtDeviceId=""` and returned `WRT300005`

The local credential file remains ignored and is not tracked. No credential,
cookie, session token, or generated DynaPath token is stored in the repository.

## Analysis Inventory Versus Implementation

- APK inventory: 165 Retrofit method entries, 159 distinct HTTP/path pairs
- Previously live-successful inventory entries: 24
- Currently implemented underlying routes: 12
- Therefore the complete APK endpoint inventory is not yet implemented

Previously successful read candidates still outside the package include UUID
lookup, product and reservation history, cart lookup, delay bank data, pass
information, discount/delay coupons, receipt lookup, and MAAS station data.
Some require valid ticket, reservation, or account state.

## Next Required Step

Keep the stored login-success device profile local and ignored. Expand only
previously evidenced read-only APIs in small TDD batches. Update the exact route
registry, request builder, parser/model, offline fixtures, public exports, and
opt-in live smoke together. Keep mutation APIs out of scope.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
