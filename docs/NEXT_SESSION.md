# Current KORAIL Package Handoff

Last updated: 2026-07-15 KST

## Head and base evidence

The internal release-readiness baseline is based on
`259553bbb930c51d8bc28d1144baa49d17372e3c`. Compare that base's
`docs/IMPLEMENTATION_PROGRESS.md` with the same file at current `HEAD`: the
release work changed package metadata, artifact checks, CI, and documentation.
The current branch additionally registers three statically evidenced P0
menu/reference reads; it changes no credential or live-smoke behavior.

The current implementation evidence establishes:

- 50 routes at the exact login/read transport boundary.
- 53 public methods on `KorailClient`.
- A historical reviewed offline gate of `1246 passed, 1 deselected`; the fresh
  P0 live-evidence documentation gate reports `1247 passed, 1 deselected`. In
  both gates, the deselected test is the explicitly opted-in live-service test.
- Current service inventory of 32 successful, 10 failed, and 123 unexecuted
  routes; the total remains 165. Historical pre-revalidation inventory was 28
  successful, 9 failed, and 128 unexecuted.
- No callable reservation, payment, cancellation, refund, check-in, membership,
  or other mutation route.

The four P0 train routes were initially implemented from static APK evidence
and synthetic fixtures: free-seat car guidance, guide-seat conditions,
seat-assignment schedules, and merged-seat inquiry. They use frozen closed
request objects, exact POST forms, strict typed parsers, and repr-hidden
identifiers/free text/raw mappings. That implementation step added no live
call, DynaPath route, Java-name method alias, `TrainSummary` convenience chain,
fallback, or adjacent mutation.

A later bounded authenticated revalidation made 28 requests and received 28
responses, with 25 successful operations, one expected typed application
failure, and three input-dependent skips. Deposit-bank and trip-menu reads
succeeded after login. R30 `getFresScar` returned exact `strResult="SUCC"` and
parsed successfully. R33 `getGuideSeatCnd` returned a full `FAIL` application
envelope for the server-supplied seat attribute, surfaced as `KorailAppError`,
and was not retried. R37 `getAssignScheduleView` and R51
`getMergeSeatsInquiry` remain static-only and unexecuted. Offline raw replay
yielded 27 parsed responses, one expected `KorailAppError`, and zero unexpected
failures. No raw response value, credential, or server-supplied seat attribute
was recorded.

## Fixed/account-shaped reads and R54 holdback

R13, R32, R43, and R45 now provide exact one-shot authenticated reads. R32
retains `strCustNo` from login as a repr-hidden `customer_no` and fails closed
when it is absent; neither member nor card numbers are substituted. R43 has
only the no-date current form or a complete, ordered, maximum-three-calendar-
month history range, and never sends `Key`. Every new route forces DynaPath
off and validates before transport.

R54 remains parser/model-only static support. Do not add a public method,
safety route, or raw string discriminator until train-group provenance or a
finite domain is evidenced. Historically, the implementation tranche itself
made no live request, credential access, `.env` read, or raw response capture.
Its pre-revalidation inventory was 28 successful, 9 failed, and 128 unexecuted
out of 165, and no mutation boundary expanded.

## Bounded next-safe read evidence

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

## Tagged variants and transport holdbacks

R17, R31, and R52 are implemented as the three remaining public reads in the
seven-read static-contract tranche. R17 has only sent/received history and
payment-eligibility tags, requires a session, disables DynaPath, and preserves
the known HTTP 404 as a single typed transport error with no retry or fallback.
R31 has only jobs `a`, `b`, and `c`, preserves the exact grouped repeated form
order, hides original-ticket data from repr, and uses a uniform conservative
session guard. R52 accepts typed metadata plus one or two exact legs, omits
`trnCnt`, does not force a session, and retains existing conditional DynaPath.

R39 has internal exact request construction and full synthetic parser/model
coverage only. Do not add a client method or route until the normal NetFunnel
`service_1` / `act_6` gate is separately implemented and reviewed. R54 remains
held for unresolved train-group provenance. The DynaPath allowlist is
unchanged. Historically, this implementation tranche made no live call, read
no credentials or `.env`, retained no secure raw, and added no mutation route;
the later bounded read-only evidence above changed only inventory evidence.

## Ticket-reference static reads

R137, R138, R146, R148, and R149 are implemented as five authenticated,
one-shot, DynaPath-disabled reads. R137 and the two repeated-ticket routes use
only exact repr-hidden `OriginalTicketReference` values. R138 uses a closed
repr-hidden PNR request. R146 and R148 preserve repeated `tkRetNo` order and
enforce exact count equality with their distinct integer and decimal-string
`tkCnt` contracts. R149 derives `custMgNo` only from login `customer_no`.

The implementation was static-only: no live I/O, credentials, secure raw
response, retry, fallback, adjacent mutation, or DynaPath route was used. At
implementation completion, the pre-R149 inventory was 31 successful, 10
failed, and 124 unexecuted out of 165. The current boundary is 50 exact
login/read routes and 53 public methods, while the DynaPath allowlist remains
six paths.

The ticket-reference implementation itself used no live I/O and added no
mutation capability.

A later bounded authenticated read-only revalidation used an empty advertising
ID, made one successful login call, confirmed logged-in state and
customer-number presence, and called only R149 once. R149 succeeded with one
row and was not retried; R137, R138, R146, and R148 made zero calls. No
mutation, raw response, PII, credential, or server message was retained.
Current inventory is 32 successful, 10 failed, and 123 unexecuted out of 165.
Keep R137, R138, R146, and R148 unexecuted until a separately reviewed
caller-owned ticket/PNR evidence plan exists.

## Completed read package

The successful-read expansion is complete. Eleven public read methods were
added with frozen typed models, exact payloads, strict parsing, synthetic
fixtures, and no adjacent or fallback requests. Independent review findings
were corrected before the historical `435 passed, 1 skipped` baseline. A
bounded 2026-07-15 replay parsed five methods, stopped four at
`KorailProtocolError`, and skipped product detail plus ticket receipt because
no owned identifiers were returned. Later sanitized evidence resolved the
cart, delay-discount, and product-reservation result-only success shapes. Pass
availability remains the only unresolved live parser shape and must not be
guessed from the fixed status-only summary.

The earlier cache, DynaPath, UUID, generic MAAS menu, and MAAS station phases
are also complete at current `HEAD`. The release-readiness change does not
repeat production traffic and does not alter their established contracts.

The static P0 menu/reference increment adds `get_pass_menu()`,
`get_crew_request_list()`, and `get_commuter_kind_menu()` with exact fields,
required caller-supplied runtime discriminator codes, frozen typed responses,
and synthetic fixtures. The routes are session-unverified; any live
verification must start only after login. No live call was made. The similarly named
`/classes/com.korail.mobile.push.callCrew.do` mutation remains unregistered and
has no public client method.

The static-only limousine increment adds three one-request read wrappers for
R04, R05, and R38. Closed request dataclasses require caller-supplied
service/menu/schedule/train/car identifiers; no live discriminator values are
embedded. All three exact paths force DynaPath off, require no authenticated
session from the reviewed caller evidence, and expose no seat selection,
booking, hold, or mutation. No live call or credential read was performed for
this increment. Exact concrete query types are required; subclasses are
rejected before Sid generation or transport.

R20 pass-schedule candidate lookup is implemented from static evidence. It
uses a frozen caller-supplied request, the exact 15-field form, one
DynaPath-disabled POST, strict full-envelope `SUCC` parsing, and frozen models
for `schedule_info[].train_list`. The server session requirement remains
unverified; the client applies a conservative authenticated-session gate and
the route is not classified as account-neutral. No live request was made for
this increment, and reservation/payment endpoints remain excluded.

The `0.2.0` typed seat-inventory increment adds two authenticated,
DynaPath-disabled reads with closed general-room forms, strict frozen response
models, and pre-Sid validation. Its offline contract and sanitized four-step
evidence helper are implemented. A bounded structural run received
`IRG000000`/`SUCC` from both routes with 5 cars and 75 seat rows, while
retaining no raw values or identifiers. That run proved that floor may be
absent, windows may be empty, and repeated seat labels are valid; the parser
now preserves every row. A later post-fix confirmation stopped at the
service-status preflight before login transport and therefore made no search,
car-list, or seat-list call. The final combined run later logged in and again
returned 5 cars and 75 seat rows, with zero windows.

Use [docs/RELEASE.md](RELEASE.md) for the internal-only offline test, build,
distribution verifier, fresh-wheel install, and cleanup gate.

## Historical analysis map

The static APK inventory remains historical evidence rather than a statement
that every discovered endpoint is implemented. Its committed entry points are:

- [README.md](../README.md)
- [docs/korail-apk-analysis.md](korail-apk-analysis.md)
- [docs/api-endpoints.md](api-endpoints.md)
- [docs/deep-dive/README.md](deep-dive/README.md)
- [docs/deep-dive/api-contracts.md](deep-dive/api-contracts.md)
- [docs/deep-dive/network-model-fields.md](deep-dive/network-model-fields.md)

The original APK and generated `analysis/` trees remain ignored local
artifacts. They are not inputs to the internal release gate.

## Next candidates

1. Internal release preparation is completed by this handoff; rerun
   [docs/RELEASE.md](RELEASE.md) whenever package contents change.
2. Do not bypass the service-status preflight. A future bounded confirmation,
   if separately authorized while the service is available, must remain
   outside the broad live smoke.
3. Before changing pass-date parsing, capture only a separately reviewed
   sanitized field/type shape; the current evidence contains an exception class
   but no response structure for that remaining endpoint.
4. Any new KORAIL read requires separate sanitized evidence, a concrete design,
   offline contract tests, and an independent safety review.
5. Validate R20 only in a separately reviewed bounded run after login. Supply
   menu/pass codes from prior server responses or the caller; do not hardcode
   them and do not continue into reservation or payment.
6. Mutation endpoints remain excluded unless a separate safety design and
   explicit authorization establish a new scope.
7. A public release remains blocked by the four items listed in
   [docs/RELEASE.md](RELEASE.md).

Do not run live KORAIL requests as part of release verification. Do not load or
inspect local credentials, APKs, caches, generated analysis, or raw production
data.
