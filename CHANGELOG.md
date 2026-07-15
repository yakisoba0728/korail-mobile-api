# Changelog

## Unreleased

- Added five authenticated, one-shot ticket-reference reads for delivery
  recipient details, ticket-duplication count, PBP acceptance specifications,
  platform numbers, and recent delivery history. The exact static contracts
  accept only repr-hidden typed ticket/PNR provenance, preserve repeated
  `tkRetNo` order with exact count equality, derive recent-history `custMgNo`
  only from the login session, and force DynaPath off. No live request was
  made; inventory remains 31 successful, 10 failed, and 124 unexecuted out of
  165. The package boundary is now 50 read/login routes and 53 public methods,
  with the DynaPath allowlist unchanged at six paths.
- Recorded a bounded authenticated read-only revalidation that used an empty
  advertising ID, logged in once, and confirmed that the repr-hidden
  `customer_no` was available. R13 made one request, returned `WRC800029`,
  surfaced as `KorailAppError` and was not retried. R32 succeeded with 0 rows,
  current-form R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the
  existing safe train search succeeded with 10 rows. R52 made zero requests
  and was recorded as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not
  called. No mutation route was called, and no credential, identifier, or raw
  response value was retained. Current service inventory is 31 successful, 10
  failed, and 124 unexecuted entries out of 165.
- Added closed tagged public reads for gift-ticket list modes, commuter jobs
  `a`/`b`/`c`, and one/two-leg fare quotes. Exact ordered forms preserve R31
  duplicate fields and intentionally omit R52 `trnCnt`; only R52 uses the
  pre-existing conditional DynaPath path.
- Kept R17's known HTTP 404 as a one-request `KorailTransportError` with no
  retry, fallback, or alternate path. R17 and R31 require a local session;
  R52 does not invent one.
- Added strict synthetic response models/parsers plus an internal exact
  request builder for R39, while leaving its NetFunnel `service_1` / `act_6`
  route unavailable. R54 also remains transport-held. At that historical,
  pre-revalidation implementation step, the DynaPath allowlist and live
  inventory remained unchanged, no live call was made, and no mutation
  capability was added. The current boundary is 50 read/login routes and 53
  public methods.
- Added four authenticated fixed/account-shaped reads for multi-child discount
  targets, login-customer trip information, current or bounded-history MaaS
  service details, and trip-change date lookup. Their exact routes and ordered
  forms are DynaPath-disabled and validation occurs before transport.
- Retained login `strCustNo` as a repr-hidden session customer number for the
  customer-trip request; member and member-card identifiers are not fallbacks.
- Added strict synthetic parsers and frozen repr-safe models for R13, R32,
  R43, and R45. R54 tour-train response parsing is static-contract support
  only: no client method, safety route, or raw-string request builder exists.
- Historically, the fixed/account-shaped implementation step itself made no
  live request, credential read, raw capture, or mutation expansion. Its
  pre-revalidation inventory was 28 successful, 9 failed, and 128 unexecuted
  entries; that intermediate callable package boundary was 42 read/login
  routes and 45 public methods. The current boundary is 50 routes and 53 public
  methods, with 31 successful, 10 failed, and 124 unexecuted inventory entries.
- Ran a bounded revalidation of the P0 read surface in an authenticated 28-request,
  28-response run with 25 successful operations, one expected typed
  application failure, and three input-dependent skips. Deposit-bank and
  trip-menu reads succeeded after login; R30 `getFresScar` returned exact
  `strResult="SUCC"` and parsed, while R33 `getGuideSeatCnd` returned a full
  `FAIL` application envelope for the server-supplied seat attribute and
  surfaced as the expected typed application failure without a retry
  (`KorailAppError`). R37 and R51 remained unexecuted. Offline raw replay
  yielded 27 parsed responses, one expected `KorailAppError`, and zero
  unexpected failures.
- Initially added four typed P0 train reads from static APK evidence for
  free-seat car guidance, guide-seat conditions, seat-assignment schedules,
  and merged-seat inquiry.
- Initial implementation added frozen closed request objects, exact POST field
  allowlists, strict response parsers, repr-hidden identifiers/free text/raw
  mappings, and synthetic-only fixtures; that implementation step added no
  live call or DynaPath route.
- Kept the Java Retrofit names as documentation aliases only and deliberately
  omitted `TrainSummary` convenience chaining and every adjacent mutation.
- Tightened only these four route parsers to require exact `strResult=SUCC`
  after preserving the existing `FAIL`, `P058`, and `WRC000288` errors.
- Added typed session-unverified pass-menu, commuter-kind-menu, and
  crew-request option reads with caller-required runtime discriminator codes;
  any live verification starts only after login.
- Registered only the three statically evidenced exact read contracts; the
  separate state-changing crew-call route remains excluded.
- Added frozen repr-safe models, strict parsers, synthetic fixtures, and
  offline route, request, error, export, and documentation coverage.
- Added three static-evidenced limousine schedule and seat-inventory reads with
  closed caller-supplied query dataclasses, exact POST allowlists, typed
  repr-safe parsers, one-shot session/error handling, and DynaPath disabled.
- Added no live service/menu/train/car constants, seat selection, hold,
  reservation, payment, cancellation, or other mutation capability; the new
  contracts are covered by synthetic fixtures only.
- Reject limousine query subclasses and invoke each concrete dataclass
  validator non-virtually before Sid generation or transport.
- Require exact `strResult=SUCC` for all P0 menu and limousine typed parsers.
- Normalize live-evidenced JSON integer and ASCII decimal-string station popup
  types and actual arrival delay counts without accepting broader coercions.

## 0.2.0 - 2026-07-14

- Added the static R20 pass-schedule candidate read with a closed
  caller-supplied request, exact DynaPath-disabled form, strict `SUCC` parser,
  and frozen repr-safe nested train models. A conservative login gate remains
  while the server session requirement is unverified; reservation and payment
  calls stay excluded.
- Added authenticated typed car-list and physical-seat inventory reads for the
  fixed main-menu/general-room contract.
- Registered only the two exact read-only POST forms, with validation before
  Sid generation or transport and DynaPath disabled on both routes.
- Added frozen repr-safe response models, strict synthetic-fixture parsers, and
  a separately opted-in bounded evidence command that persists sanitized
  statuses, call counts, bounded counts, and type-presence booleans only.
- Accepted live-evidenced missing floor values, empty window collections, and
  repeated seat labels, plus statically evidenced empty car containers and
  strict numeric strings, while preserving response order.

## 0.1.0 - 2026-07-14

- Prepared the existing installable, typed, read-only KORAIL mobile API client
  for reproducible internal builds and offline verification.
- Retained the 25-route safety boundary and its 28 public client methods;
  mutation operations remain excluded.
