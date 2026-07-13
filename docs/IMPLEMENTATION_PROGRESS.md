# KORAIL Python Package Implementation Progress

Last updated: 2026-07-13 KST

## Current State

- The read-only public API stabilization phase is complete.
- The cache-read expansion implementation, offline tests, package build, and
  isolated import are complete, but the phase remains pending its required
  bounded live verification.
- The implementation is present in the working tree but is not committed.
- Current HEAD: `d5ac440`.
- Do not reset or discard the existing working-tree changes.

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
- Stateful DynaPath generation and exact-path attachment

The transport currently allows 12 exact read/login routes. Reservation,
payment, cancellation, refund, check-in, member mutation, and point/mileage
mutation routes are not callable.

## Verification

- Offline tests: `195 passed, 1 skipped`
- Wheel and sdist build: passed after the cache expansion
- Fresh-venv wheel install/import: passed for `KorailClient`,
  `AppDataResponse`, `AppVersionInfo`, and `NoticeResponse`
- Cache parser, exact-route, timestamp, malformed-response, public-contract,
  pre-login ordering, raw-output, and DynaPath non-regression tests: passed
- Cache expansion bounded live verification: pending. The ignored environment
  now stores the device profile used by the previous `IRZ000001` login-success
  probe flow, but `KORAIL_ADVERTISING_ID` remains intentionally unset because
  it was not part of that login request. The full live-smoke preflight therefore
  still stops before client construction or network I/O and does not satisfy
  the approved live completion criterion
- Live login with the provided account: passed
- Live reads: common code, 281 stations, calendar, 10 train rows, schedule,
  transfer stations, and ticket list all returned valid responses
- Ticket list returned `WRT300005`, meaning there was no matching data. This
  read-only test used the source probe device ID as a temporary advertising ID;
  parity with a real device advertising ID remains unverified
- Stateful DynaPath generated tokens for login and train search and advanced
  its runtime delta state

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

Keep the stored login-success device profile local and ignored. Supply a real
caller-provided `KORAIL_ADVERTISING_ID` before rerunning the full bounded
live-smoke verification. Do not mark the cache-read expansion phase complete or
begin another KORAIL expansion batch until that verification passes without
exposing raw or sensitive data.

After that gate passes, expand only previously evidenced read-only APIs in
small TDD batches. Update the exact route registry, request builder,
parser/model, offline fixtures, public exports, and opt-in live smoke together.
Keep mutation APIs out of scope.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
