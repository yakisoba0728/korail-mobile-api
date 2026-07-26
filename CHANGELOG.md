# Changelog

## Unreleased

- Added: `reserve` reaches all three of the booking screen's job types through a
  keyword-only, defaulted `job_type` (`KorailReservationJobType`). The default
  is `IMMEDIATE` (`txtJobId="1101"`), the only value this package has ever sent,
  so every existing call is byte-for-byte unchanged.
  **Neither new variant has been live-verified; nothing here has transmitted a
  `1102` or a `1103`.**
  - `SEAT_DESIGNATED` (`"1103"`) books named seats. `seats` takes one
    `KorailSeatAssignment` per passenger, carrying exactly the two identifiers
    the existing seat reads return — `SeatCar.car_no` /
    `SeatInventoryResponse.car_no` and `PhysicalSeat.seat_no`, with
    `KorailSeatAssignment.from_inventory()` pairing them and refusing a seat the
    read marked unsellable. The form appends `txtSrcarCnt` (the *seat* count)
    then `txtSrcarNo{i}`/`txtSeatNo{i}` from index 1, after the journey block.
    An ordinary hold still sends none of those keys at all — the app clears its
    `OSrcar` map and an empty Retrofit `@FieldMap` contributes no fields, so
    srtgo's unconditional `txtSrcarCnt="0"` is a shape the app never produces.
    A seat list whose length is not the passenger total, or that names the same
    seat twice, is refused before anything is built: a partial seat list is how
    a half-booked hold happens.
  - `STANDBY` (`"1102"`) is 예약대기. Eligibility is not "sold out" — the app
    reads one field, the search row's `h_wait_rsv_flg`, and compares it to the
    two-character literal `" 9"` (leading space; exported as
    `KORAIL_STANDBY_WAIT_FLAG`), on the 일반실 tab only. That, and nothing
    else, enables its button; the availability code is never consulted. So
    standby skips the "seats available" check that `1101` enforces, requires
    the flag and the general cabin, and computes `txtStndFlg` from the app's
    own `isStndSeat` instead of pinning `"N"`. korail2 describes the field as
    `-2`/`9`/`0`; only the 9 has any support in this app. Standby is
    **members-only** — the app's request declares itself not-non-member-enabled
    for this job id — which this client satisfies structurally, since every
    mutation needs a logged-in member session.
- Added: `confirm_standby_hold`, the second call a standby booking needs. A
  `"1102"` hold comes back with `h_msg_cd = IRR000014`
  (`KORAIL_STANDBY_HOLD_MESSAGE_CODE`), the only code that opens the app's
  예약대기 screen; that screen then POSTs `reservationWait.ReservationWait` with
  `txtPsrmClChgFlg` (좌석등급 변경 동의) and `txtSmsSndFlg`/`txtCpNo`. The phone
  number is sent only when SMS is on, must be 10 or 11 digits, and is otherwise
  omitted entirely rather than sent empty — matching the app, where the field is
  null and Retrofit drops it. It is a state-changing call on an existing PNR, so
  it goes through the same double-gated mutation transport as everything else,
  and it deliberately shares the **`reserve` consent category** rather than
  introducing a new one: it completes the booking an `allow_reserve` consent
  authorised, moves no money and releases no seat, and a new category would mean
  a caller who opted into placing a standby booking could not finish placing it.
  `reservationWait.ReservationWait` is now a fifth mutation route; the read-only
  allowlist and its guarantee are untouched. Never live-run.
- Changed: `redact_payload` now masks `txtCpNo` and the indexed
  `txtSrcarNo{i}`/`txtSeatNo{i}` keys, so a mutation preview cannot expose the
  standby notification number or the designated seats. Car and seat identifiers
  were already redacted everywhere they are read back; these are the same two
  values on the way out.
- Documented: two live observations from 2026-07-26 that are server rules, not
  package defects. `ERR299943 예약할인이 지원되지 않습니다` refused 청소년 alone
  and 1~3급 장애 + 안내견 while six other mixes were accepted; the code has zero
  hits anywhere in the decompiled APK and the forms matched the app exactly, so
  it is an account-entitlement rule. Separately, a hold returned
  `h_msg_cd = WRR664296` (weekend discount notice) and was still a real,
  cancelable reservation — success is `strResult = SUCC` plus a PNR, not
  `h_msg_cd == IRR000018`, and no code path treats a non-`IRR000018` code as
  failure.
- Added: `reserve` books an arbitrary passenger mix in either cabin. It takes a
  `KorailPassengerCounts` — one field per row the app's request has always
  carried (어른, 청소년, 어린이, 동반유아, 경로, 1~3급 장애, 4~6급 장애,
  안내견) — and a `KorailSeatClass` (일반실 `"1"` / 특실 `"2"`). Both are
  keyword-only and default to one adult in a general seat, so an existing call
  sends the identical form, byte for byte and key for key. `txtTotPsgCnt` is
  every row summed, the lap infant and the guide dog included, because that is
  how the app computes `TOTAL_PERSON_COUNT`; the mix must be non-negative, hold
  at least one passenger, and stay within
  `KORAIL_MAX_PASSENGERS_PER_RESERVATION` (9, the cap the app's passenger
  picker enforces). No discount-card field accompanies a discounted row: the
  app's `OPsg` declares only `txtCardNo_`, written solely by the separate N-card
  request, and korail2's/srtgo's `txtCardCode_`/`txtCardPw_` appear nowhere in
  the decompiled app. A 특실 hold requires the train's special seats to be
  evidenced as available, not its general ones. Live-verified on 2026-07-26 by
  reserve->cancel round trips: two adults in a general seat (hold total
  119,600 = 2 x 59,800) and one adult in 특실 (read back as `h_psrm_cl_nm='특실'`,
  `h_rcvd_amt=83,700`). The 특실 hold also demonstrates why the payment amount
  must come from `h_tot_rcvd_amt`: its `h_tot_prc` reads `59,800`, so the old
  builder would have underpaid by 23,900 KRW. Other passenger types and mixes
  of types remain static-evidenced and have never been transmitted.
- Fixed: `scripts/reserve_pay_refund_roundtrip.py` masked the PNR it exists to
  print. Its console scrubber applied a 13–19 digit card-number pattern to
  arbitrary text, and a KORAIL PNR is 15 decimal digits, so a live run on
  2026-07-25 printed `LIVE HOLD CREATED   PNR [REDACTED_CARD]` and redacted the
  PNR inside the recovery command line as well — leaving a real unpaid hold with
  no identifier attached to it. The scrubber now substitutes the four card
  values it was actually handed, by exact value, and applies no digit-run
  pattern at all: a 15-digit run cannot be told from an Amex PAN by shape, and
  the PNR is the one value that must always reach the operator. `redact_payload`
  and the package's `CARD_RE` are unchanged; the generic pattern is right where
  it guards a mutation payload against a PAN under an unknown key.
- Fixed: `get_ticket_reservation_detail` rejected the live success body. Its
  success-shape handling was built from the APK's DAO declaration, which types
  every field as a Java `String`; the live server sends the seat row's
  `h_srcar_no` as a JSON number, so the first real hold produced
  `KorailProtocolError: ... h_srcar_no must be a string or null` — after the
  hold existed. This is the third live finding on the same seam (`h_jrny_cnt` =
  `"0001"`, `h_st_prnb`/`h_cls_prnb` = zero-padded strings for declared `int`s),
  so it is fixed systemically rather than field by field: every asserted scalar
  on `certification.ReservationList`, `refunds.CommissionView` and
  `refunds.SelTicketInfo` — response, journey and seat levels alike — now accepts
  a JSON string or a JSON number and normalises to the string the rest of the
  code expects. The app never noticed because Gson's `JsonReader.nextString()`
  coerces a number into a String. Genuinely wrong types are still refused: a
  bool, a float, a list or an object where a scalar belongs is a protocol error.
- Fixed: `parse_reservation_hold_response` could not read a hold back out of
  the reservation history — the documented recovery path when a PNR is lost. The
  history sends `h_jrny_cnt` as the JSON integer `1` while a reserve response
  sends the string `"0001"`, so the parser raised and the operator had to
  hand-build a hold to cancel a real reservation. Every scalar on the hold and
  payment parsers now accepts a JSON string or a JSON number and normalises to
  the string the form builders expect, so `1`, `"1"` and `"0001"` all reach
  `build_unpaid_reservation_cancel_form`, which already compared them
  numerically. The same tolerance covers the PNR, window number, job sequences
  and settlement amount, because those identify a hold that may already exist on
  the server and refusing one strands it;
  `KorailClient._hold_from_reservation_response`, the last-ditch fallback whose
  entire job is never to lose a PNR, normalises them too. Bools, floats, lists
  and objects are still protocol errors.
- `scripts/reserve_pay_refund_roundtrip.py` now orders its train choice by the
  search row's own price field when no fare quote can be built. A live
  ScheduleView row carries no goods number, so `trn.prcFare.do` usually cannot
  be built and the script reported `fare: UNKNOWN` and took the first reservable
  train. It still invents nothing: `KORAIL_TRAIN_NO` pins an exact train (and
  aborts before reserving if that train is not reservable), then the cheapest
  fare quote, then the cheapest by `h_rcvd_amt`/`h_rcvd_fare` — fields
  `RsvInquiryResponse.TrainInfo` declares — printed as
  `~N KRW (HINT from the search row, not a quote)` so it can never be read as
  the amount about to be charged, then the first reservable train with the same
  plain statement as before. The printed reason always names which branch ran.
  The authoritative amount is still the one read back and cross-checked before
  paying, and `KORAIL_MAX_FARE` is still the only ceiling on the charge.
- Real (chargeable) card payment is now possible, as an explicit, additive
  opt-in. `MutationConsent` gains `real_card_acknowledged` (default `False`):
  the caller's acknowledgement that a real, chargeable PAN will be transmitted
  in the clear and that money will actually move. Because it defaults to
  `False`, every consent written before it existed means exactly what it meant
  before and the default posture is unchanged — fake-card-only.
- Added `KorailClient.pay_with_card`, beside an unchanged `pay_with_fake_card`.
  The new method requires `real_card_acknowledged=True` AND
  `fake_card_only=False`; the old one still refuses anything but a test card,
  so its name keeps meaning what it says. Both build the same
  `build_card_payment_form` and leave through the same double-gated
  `post_mutation_form`, so a real payment cannot drift from the wire shape that
  was verified live. `pay_with_card` returns the parsed payment envelope rather
  than raising on a FAIL, because that envelope is the only record of what
  happened to the money and of whether the hold is still cancellable.
- The transmit gate now requires a payment consent to state exactly ONE card
  claim. Neither flag set is the original refusal, unchanged. BOTH set is
  refused as a contradiction: a consent that claims a test card while
  acknowledging a real charge is a caller bug, and paying on an ambiguous
  consent is the mistake the gate exists to prevent. The boundary is now 54
  exact login/read routes and 61 public methods; no new route was added.
- Added `scripts/reserve_pay_refund_roundtrip.py`, the operator script for one
  full reserve → pay → refund round trip on a real card. Three environment
  opt-ins are required (`KORAIL_MOBILE_API_LIVE=1`, `KORAIL_LIVE_MUTATION=1`,
  `KORAIL_LIVE_REAL_CHARGE=1`); the card is read from the environment only,
  never a file and never argv. It refuses to start unless the account holds
  zero reservations, prints the PNR the instant it exists, cross-checks the
  amount owed against an independent server read before paying, prints the
  refund amount and fee before refunding, and on any later failure prints an
  unmissable banner with the PNR, what is outstanding, and a runnable recovery
  command (`--recover` with `KORAIL_RECOVER_PNR`). The PAN, PIN digits, expiry
  and birthday are scrubbed from every output path including exception text;
  the PNR deliberately is not, because losing it is the worst outcome.
- Neither `pay_with_card` nor `refund` has a live-verified success envelope. No
  run recorded in this repository has settled a real payment or returned money;
  the docs now say so instead of saying a real charge is impossible.
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
