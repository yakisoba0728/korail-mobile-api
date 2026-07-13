# KORAIL Python Package Implementation Progress

Last updated: 2026-07-13 KST

## Current State

- The read-only public API stabilization phase is complete.
- The cache-read expansion implementation, offline tests, package build, and
  isolated import are complete, but the phase remains pending its required
  bounded live verification.
- The fixed `rt=0` DynaPath replacement is committed on its isolated feature
  branch, and the original main worktree remains untouched.
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
- The promoted fixed `rt=0` engine completed bounded live login and train-search
  requests without a DynaPath rejection. The same run returned valid common
  code, 281 stations, a 33-day calendar, 10 train rows, schedule, and transfer
  responses
- A member ticket-list request with `txtDeviceId=""` returned `WRT300005` and
  `SUCC`, so an advertising ID is no longer a client or live-preflight
  requirement
- Full helper completion remains pending because the live app-data and notice
  cache responses omit the common response envelope that the current cache
  client requires. This cache contract mismatch is independent of DynaPath and
  advertising-ID handling

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

Keep the stored login-success device profile local and ignored. Align the two
cache readers with the observed envelope-free live responses before rerunning
the full bounded live helper. Do not mark the cache-read expansion phase
complete or begin another KORAIL expansion batch until that verification passes
without exposing raw or sensitive data.

After that gate passes, expand only previously evidenced read-only APIs in
small TDD batches. Update the exact route registry, request builder,
parser/model, offline fixtures, public exports, and opt-in live smoke together.
Keep mutation APIs out of scope.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
