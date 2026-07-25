# Changelog

## Unreleased

- Added three read-only routes found by comparing the package against four
  third-party reference clients (srtgo, srtgo_plus, ryanking13/SRT, korail2);
  all three are declared in our own decompiled APK. `get_ticket_reservation_detail`
  reads one held reservation back by PNR (`certification.ReservationList`,
  `CertificationService.java:45-46`), giving an independent view of `h_wct_no`
  and the per-seat `h_rcvd_amt` rows the payment form settles.
  `get_refund_commission` (`refunds.CommissionView`, `RefundService.java:19-21`)
  reports `ret_amt`/`ret_fee`/`prg_psb_flg`, and `get_refund_ticket_detail`
  (`refunds.SelTicketInfo`, `RefundService.java:23-25`) reports the refund
  target's ticket detail including `retPsbFlg`. Together the latter two are the
  "how much comes back and what is the fee" pre-check that `refund` has never
  had; none of the four reference clients implements either one. The boundary is
  now 54 exact login/read routes and 60 public methods.
- `certification.ReservationList` hosts a SECOND, write-flavoured Retrofit
  overload, `applyDisabilityCertification` (`CertificationService.java:22`),
  which applies a disability certificate to a held reservation. Only the read
  overload is ported, and the route's `KORAIL_EXACT_REQUEST_FIELDS` entry pins
  the read's exact four fields, so the write overload's wider shape
  (`txtPsgDisc0019Cnt` plus six `@QueryMap`s) is rejected before transmission
  even though it shares the path.
- `refunds.SelTicketInfo` is sent as the app declares it — POST, with
  `h_purchase_history` — not as srtgo sends it (`ktx.py:791-800` uses GET and
  drops the field). Every app call site sets the flag, "Y" from the
  purchase-history screen and "N" elsewhere.
- Verified all three against the live server in one paced read-only pass on an
  account holding zero reservations. Every route was ACCEPTED — HTTP 200, no
  DynaPath rejection — and each answered with a bare three-key FAIL envelope for
  the deliberately-invalid arguments it was given: `WRG200018` 입력값오류(PNR번호),
  `WRT100002` 창구번호미입력,미승인창구 and `WRT100124` 반환번호를 확인해주세요.
  Each code names the field the server parsed, which is what establishes the
  request shapes. Those bodies are pinned verbatim as offline regressions. The
  SUCCESS bodies remain UNVERIFIED and are covered only by APK-declared
  synthetic fixtures, because producing one needs a real held or paid ticket.
  No payment, refund, or reservation call was made and the account still holds
  zero reservations.
- `ReservationSeatDetail` maps the passenger type from `h_psg_tp_cd`, which is
  what `ReservationResponse.SeatInfo` declares. The `h_psg_tp_dv_nm` that a
  reference client names does not appear anywhere in the decompiled app and was
  not observed live, so it is deliberately not mapped; an unmapped key stays
  reachable through `raw`.
- Corrected the NetFunnel claim in `docs/RELEASE_GAP_PLAN.md`. Saying Korail
  "does NOT use NetFunnel at all" was too strong: the app does wire the round
  trips. What is true is that no Retrofit request body carries a token field and
  our live calls succeed without one.
- Added the consent and safety foundation for state-changing requests. Frozen
  `MutationConsent` (per-category `allow_*` default `False`, `dry_run` default
  `True`, `fake_card_only` default `True`) and frozen `MutationPreview` (whose
  payload is forced through `redact_payload` on construction, so a preview can
  never hold a raw PAN, PNR, or sale identity) live in `consent.py`. The route
  registry became tiered: `KORAIL_MUTATION_ROUTES` holds the four
  state-changing routes and is deliberately never added to
  `KORAIL_READ_ONLY_ROUTES`, while `KORAIL_MUTATION_ROUTE_CATEGORIES` and
  `assert_mutation_route_category` cross-check the caller's consent category
  against the route, so a consent for one category cannot post another
  category's route. Redaction was extended over the mutation fields, including
  the card number, PNR, original-ticket sale identity, return password,
  `txtPrnNo`, and `h_orgtk_sale_wct_no`.
- Added four consent-gated mutation methods: `reserve`, `cancel_unpaid_hold`,
  `pay_with_fake_card`, and `refund`. Each requires an authenticated session
  and a `MutationConsent` that opts into its own category, and each is denied
  with `MutationNotAllowedError` before anything is built otherwise. With the
  default `dry_run=True` a method validates its inputs and returns a redacted
  `MutationPreview` of the form that *would* be posted, sending nothing. Only a
  `dry_run=False` consent transmits, and only through `post_mutation_form`, the
  single send path that re-checks consent, refuses a `dry_run=True` consent,
  and asserts both the mutation route and its category. The read-only send path
  (`post_form`/`get_json`) still refuses every mutation route.
  `pay_with_fake_card` additionally refuses unless `fake_card_only` is set, at
  both the method and the send gate, because the payment form carries the card
  number in the clear; only a non-chargeable test card is supported.
- Verified `reserve`, `cancel_unpaid_hold`, and `pay_with_fake_card` end to end
  against the live server in a bounded authorized run: the hold returned
  `h_msg_cd=IRR000018`, the cancellation returned `h_msg_cd=IRG000000`, and the
  fake-card payment was declined with `strResult=FAIL` and `h_msg_cd=WRT200342`
  with no charge. The live hold response returned a zero-padded
  `h_jrny_cnt="0001"`, so `build_unpaid_reservation_cancel_form` now accepts any
  digit string equal to one; `reserve` also falls back to a minimal hold that
  still carries the PNR when strict parsing fails after the server has already
  created the hold, so a created hold can always be cancelled. Every round trip
  left reservation history at zero rows and no card was charged.
- Added `refund` on the same gated send path. Its live send path is fully
  active code, not blocked, but it has never been exercised against the live
  server: a refund acts on a settled ticket, and this package's fake-card
  payment is always declined, so no paid ticket is produced here. Its request
  contract, gates, and redaction are covered by offline tests only, and it must
  be treated as unverified against the real service.
- The package boundary is now 51 exact login/read routes and 57 public methods:
  53 audited login/read methods that transmit only read-only requests, plus the
  four consent-gated mutation methods. The four mutation routes are tracked in
  their own set and are never reachable from a read path.
- Made `logout()` invalidate the server session with a bare `GET`
  `login.Logout` before clearing local state, best-effort so it never fails on
  transport or an already-expired session. That cookie-authenticated,
  zero-parameter route joined the read-only allowlist, which is why the
  allowlist holds 51 routes rather than 50. Also corrected
  `KORAIL_DYNAPATH_SDK_VERSION` from `v1` to `v1.0.3` to match the decompiled
  app, since that constant seeds both the `sv` body field and the `dyn_key`.
- Recorded a bounded authenticated read-only revalidation with an empty
  advertising ID. It made one successful login call, confirmed logged-in state
  and customer-number presence, and called only R149 once. R149 succeeded with
  one row and was not retried; R137, R138, R146, and R148 made zero calls. No
  mutation, raw response, PII, credential, or server message was retained.
  Current inventory is 32 successful, 10 failed, and 123 unexecuted out of
  165.
- Added five authenticated, one-shot ticket-reference reads for delivery
  recipient details, ticket-duplication count, PBP acceptance specifications,
  platform numbers, and recent delivery history. The exact static contracts
  accept only repr-hidden typed ticket/PNR provenance, preserve repeated
  `tkRetNo` order with exact count equality, derive recent-history `custMgNo`
  only from the login session, and force DynaPath off. The implementation made
  no live request; the pre-R149 inventory was 31 successful, 10 failed, and
  124 unexecuted out of 165. The package boundary is now 51 read/login routes
  and 57 public methods, with the DynaPath allowlist unchanged at six paths.
  The ticket-reference implementation itself used no live I/O and added no
  mutation capability.
- Recorded a bounded authenticated read-only revalidation that used an empty
  advertising ID, logged in once, and confirmed that the repr-hidden
  `customer_no` was available. R13 made one request, returned `WRC800029`,
  surfaced as `KorailAppError` and was not retried. R32 succeeded with 0 rows,
  current-form R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the
  existing safe train search succeeded with 10 rows. R52 made zero requests
  and was recorded as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not
  called. No mutation route was called, and no credential, identifier, or raw
  response value was retained. At that pre-R149 point, inventory was 31
  successful, 10 failed, and 124 unexecuted entries out of 165.
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
  capability was added. The current boundary is 51 read/login routes and 57
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
  routes and 45 public methods. The current boundary is 51 routes and 57 public
  methods. At that pre-R149 point, inventory was 31 successful, 10 failed, and
  124 unexecuted entries.
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
