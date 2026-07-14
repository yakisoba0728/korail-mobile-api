# KORAIL Python Package Implementation Progress

Last updated: 2026-07-14 KST

## Current State

- Internal release preparation is complete at current `HEAD`: typed-package
  metadata, source-manifest contents, an archive verifier, Python 3.11-3.14
  offline CI, and internal release/security/changelog guidance are present.
  This preparation changed no runtime request, route, credential, or live
  behavior and made no live request.
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
- The `0.2.0` seat-inventory increment implements typed authenticated car and
  physical-seat reads for the fixed main-menu/general-room contract. Both
  exact POST routes validate before Sid generation, issue one request, and
  force DynaPath off. The banner URL is inert and never followed.
- A separate evidence command enforces a four-operation ceiling and writes only
  fixed statuses, 0/1 call counters, bounded counts, type-presence booleans, and
  a sufficiency category after a secret scan. It is not part of broad live
  smoke, and no seat-inventory live result is claimed before its bounded gate.
- The one independent final whole-feature review is complete. Its two Important
  findings were fixed together, and no Critical or Important finding remains
  open.
- The transport now allows 27 exact login/read routes and the client exposes
  30 public methods. No new route was added to the DynaPath allowlist.
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
- Authenticated general-room car-list and physical-seat inventory lookup

The transport currently allows 27 exact read/login routes. Reservation,
payment, cancellation, refund, check-in, member mutation, and point/mileage
mutation routes are not callable.

## Verification

- Seat-inventory TDD RED: the focused test command stopped during collection on
  the missing `PhysicalSeat` public interface, as expected before production
  code existed.
- Seat-inventory focused GREEN: `142 passed`; the cross-cutting seat, HTTP,
  public-contract, and legacy-model gate reports `263 passed`. All tests are
  synthetic or mocked and perform no live I/O.
- The full `0.2.0` offline release gate reports `725 passed, 1 deselected in
  0.66s`; only the explicitly opted-in live-service test was deselected.
- Python 3.14 built `korail_mobile_api-0.2.0-py3-none-any.whl` and
  `korail_mobile_api-0.2.0.tar.gz` in a temporary directory. The distribution
  verifier accepted both artifacts, `git diff --check` passed, and all
  generated build, metadata, and temporary distribution paths were removed.
- The bounded seat-inventory live gate remains the only pending verification
  at this point in the recorded sequence.
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
- Live-successful inventory entries: 25
- Currently implemented exact login/read routes: 27
- Therefore the complete APK endpoint inventory is not yet implemented

All recorded successful read entries now have an exact package route. The
remaining APK inventory is outside this read expansion and includes unverified
or state-changing operations.

## Next Required Step

The full offline `0.2.0` release and distribution gate is complete. Execute
only the separately authorized bounded seat-inventory evidence command. Record
only its fixed status, four operation counts, bounded counts, and sufficiency;
do not retry or broaden a rejected static contract. Any additional
reservation-linked route requires its own safety review and caller-owned data.
Keep all local credentials and runtime-sensitive values ignored and out of
documentation.

See the shared [next-session prompt](../../NEXT_SESSION_PROMPT.md) for the
combined KORAIL/SRT orchestration instructions.
