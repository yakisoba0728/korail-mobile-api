# Changelog

## Unreleased

- Added: 할인카드(N카드) reads — `KorailClient.get_discount_card_usage_history`
  and `KorailClient.get_discount_card_schedule`, plus
  `DiscountCardScheduleRequest`, `DiscountCardUsage`,
  `DiscountCardUsageListResponse`, `DiscountCardScheduleTrain` and
  `DiscountCardScheduleResponse`. The read-only boundary is now 56 routes.
  **Implemented and NOT live-verified**: no account this project can reach owns
  an N카드, so both shapes come from the APK's DAOs rather than from an observed
  body.
  - `GET ticket.dcntCrdUseQry.do` (`ResearchService.java:51-52`) takes one
    identifier, `dcntCrdNo`, and the card number is never typed by a user: the
    N카드 ticket's own detail response carries it as
    `dcnt_crd_info.h_dcnt_crd_no`, which `Y4/C0907b.java:303` puts in an intent
    extra and `TicketNCardHistoryActivity.java:138,109` reads straight back into
    `setDcntCrdNo`. That number is now redacted everywhere it can appear.
  - `GET research.dcntCrdScheduleView.do` (`ResearchService.java:54-55`) is not
    an ordinary train search. An N카드 is sold against one to three fixed 구간,
    and this route answers "which trains on this 구간 does this card cover",
    which is why it is keyed by the card product rather than by station codes.
  - **Two of its fourteen `@Query` parameters are omitted, because the app omits
    them.** Neither builder (`u4/b.java:52-65`, `:67-81`) ever calls
    `setQryPgNo`, and the 1-section builder never calls `setUseTrmDno`, so
    Retrofit drops both nulls. They are registered in
    `KORAIL_OPTIONAL_REQUEST_FIELDS` rather than pinned, since a request that
    carries them is equally conformant — the response's `fllwPgExt` is the
    app's own paging signal (`SectionNCardInquiryActivity.java:406-408`).
  - `dcntCrdKndCd` has exactly two values in the whole app. `u4/b.java:60-61`
    sends `"B2N"` for the two original 1-section products (`B2N18120402`,
    `B2N18120403`) and `"MMM"` for everything else; `:76` hardcodes `"MMM"`.
    `DiscountCardScheduleRequest.for_card` reproduces that rule.
  - **No endpoint supplies the card product codes.** Every `dcntCrdKndMgNo` the
    app can send is a client-side literal (`NCard1SectionBookingActivity.java:28`,
    `NCard2SectionBookingActivity.java:34`, `NCard3SectionBookingActivity.java:28`,
    `q5/ViewOnClickListenerC6267a.java:73,76`), and `pass.passMenu.do` returns
    only a `detailType` string that selects an Activity, not a code list.
  - The two `dcntCrd*` routes that CHANGE state — `research.dcntCrdInfo.do` and
    `reservation.dcntCrdExtn.do` — are deliberately absent from the read-only
    allowlist and from `KORAIL_MUTATION_ROUTES`; a test pins their absence.

- Added: 환승 (transfer) search and reservation — `KorailClient.search_transfer_trains`,
  `KorailClient.search_trains_with_transfer_fallback` and
  `KorailClient.reserve_transfer`, plus `TransferItinerary`,
  `TransferSearchResult`, `pair_transfer_itineraries` and the four resolved
  codes `KORAIL_DIRECT_ITINERARY_CODE`/`KORAIL_TRANSFER_ITINERARY_CODE`
  (`"1"`/`"2"`), `KORAIL_DIRECT_JOURNEY_TYPE_CODE`/
  `KORAIL_TRANSFER_JOURNEY_TYPE_CODE` (`"11"`/`"14"`) and
  `KORAIL_MAX_JOURNEY_LEGS` (`2`). Reservation is no longer one-leg-only.
  **Implemented and NOT live-verified**: nothing here has been sent to KORAIL.
  - The app has one request builder for both cases. `C5/a.java:52-119` (`N0`) is
    a loop over the train array, and the array's **length** decides everything:
    `txtJrnyCnt` is `(length == 1 ? "1" : "2")` at `:55`, the loop writes at
    `i + 1` so journey indices are 1-based, and the sixteen `OJrny` keys repeat
    per leg. `build_reservation_form` is now a one-leg call into a leg-sequence
    core and `build_transfer_reservation_form` is the same core with two, so the
    **single-leg form is byte-for-byte what it was, key order included** — a
    contract test pins all 56 keys in order rather than trusting that.
  - Four codes were read from **bytecode**, not assumed. `K4/d` is `"1"`/`"2"`
    (`smali/K4/d.smali:36,64`) and does three unrelated jobs with the same two
    values — search `radJobId`, `txtJrnyCnt`, and the seed for `txtJrnySqno`.
    `K4/e` is **not** `"1"`/`"2"`: DIRECT is `"11"` (`smali/K4/e.smali:40`) and
    TRANSFER is `"14"` (`smali/K4/e.smali:68`), which jadx hides behind an
    unrelated same-valued constant. `S4/O.getSequenceNo` is `DecimalFormat("000")`, so the
    sequence numbers reach the wire as `"001"`/`"002"`.
  - **Both legs of a transfer carry `txtJrnyTpCd="14"`.** The ternary at
    `C5/a.java:60` sits inside the per-leg loop but tests the array *length*,
    while `:61` two lines below tests the loop *index*. Getting that backwards
    would send a form the app never sends, so both were re-read as
    `smali/C5/a.smali:306-338` (`array-length` re-evaluated every iteration) and
    `:343` (`if-nez v1`).
  - **Two legs is the app's ceiling, not a limitation chosen here.** The form has
    no journey-3 spelling: `OSeat.java:32-35` and `OSrcar.java:21-30` each split
    on "journey 1 or not", so a third leg would *overwrite* leg 2, and
    `ReservationRequest.java:114-117` reads back exactly two seat slots. Any
    other leg count is refused before a form is built.
  - The transfer **search** moves exactly one field. On `WRD000061` the app calls
    `setRadJobId(TRANSFER_SQ_NO.getCode())` on the request it already built and
    hands it on untouched (`DirectInquiryActivity.java:615-624` into
    `DirectInquiryActivity.java:284-296`, confirmed at
    `smali/…/DirectInquiryActivity.smali:1677-1689`).
    `chtnCnt`/`chtnRsStnCd1`/`trnGpCnt`/`trnGpCd1` are not part of it.
    `search_trains_with_transfer_fallback` reproduces the app's own flow and
    swallows `KorailNoDirectTrainError` and nothing else.
  - A transfer **response is not shaped differently**: the same flat
    `trn_infos.trn_info` list, paired positionally, rows 0/1 then 2/3, trailing
    odd row dropped (`a5/k.java:156-170`). `h_chg_trn_seq` is the server's copy
    of that position and is used as a consistency check, not as the pairing key.
    Paging gained the transfer half of the cursor —
    `TrainSearchContinuation.query_train_no2`, defaulting to `""` so a direct
    next page is unchanged.
  - Passenger mix composes **per booking** (`w4/a.java:47-74` builds `OPsg` once);
    cabin class and 좌석지정 compose **per leg** (`C5/a.java:59`/`:97` and
    `:120-133`). **예약대기 (`1102`) does not compose and is refused**: the app
    gates it twice, at `a5/k.java:120-127` (the standby check returns false for
    a non-direct result) and at `DirectInquiryActivity.java:434` (its only
    `setJobId("1102")`, on a screen `TransferInquiryActivity` overrides away).
- Known gap: **`cancel_unpaid_hold` cannot release a transfer hold.** It requires
  `h_jrny_cnt` to be numerically one. The app has no such restriction —
  `DReservationConfirmActivity.java:269-278` forwards `getH_jrny_cnt()` verbatim
  as `txtJrnyCnt` beside the same fixed `txtJrnySqno="0001"`/`hidRsvChgNo="000"`
  — so the fix is to forward the hold's own count instead of pinning `"1"`. That
  touches the cancel path, which was out of scope for the transfer change, so it
  is reported rather than made. A live transfer hold sent before it lands must be
  cancelled in the KORAIL app or on the website.
- Added: a NetFunnel virtual-waiting-room client, `KorailNetFunnelClient`, so a
  gated operation can wait its turn instead of failing.
  **Off by default, and partly live-confirmed on 2026-07-26.** Probing on that
  date ran the protocol against `nf.letskorail.com` and settled the standing
  inferences: the wire format is the native SDK's `<code>:<params>`, the entry
  sequence is `5101` → `5002` → gated call → `5004`, and the queue is a pool of
  hosts rather than one. The slot-release path was exercised end to end.
  **The 201 queued path is still NOT live-exercised**: the server was not
  queueing (`5101` answered `nwait=0`), so the polling loop, the ttl sleep and
  the two bounds remain covered by offline fixtures only, exactly as the
  sibling SRT client's polling path is.
  - **The queue is a POOL, and the session lives on one node of it — the second
    defect the probing exposed, and the one worth an explicit warning.**
    `nf.letskorail.com` is a *front door* that load-balances the entry call; the
    node it lands on is the only one that can complete the session, and every
    reply names that node in its `ip`/`port`. This client sent every opcode to
    the front door, so slot release failed **about half the time,
    non-deterministically** — five acquire-then-release cycles:

    ```
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf12.letskorail.com  -> release 503
    acquire said ip=rnf13.letskorail.com  -> release 503
    acquire said ip=rnf14.letskorail.com  -> release 200
    acquire said ip=rnf13.letskorail.com  -> release 200
    ```

    and the controlled pair that settles it:

    ```
    acquire on nf.letskorail.com (reply said ip=rnf13.letskorail.com)
      release via nf.letskorail.com    -> 503:msg="Wrong Server ID"
      release via rnf13.letskorail.com -> 200:key=&nwait=0&…
    ```

    **`Wrong Server ID` is literal**, and it will cost the next reader an hour
    if this is not written down: it reads like a credential or parameter
    complaint and is neither — the front door does not own a session a queue
    node issued. The releases that appeared to work were the balancer happening
    to land back on the owning node, which is also why the same key sometimes
    released fine. The app has always followed the naming: `T6/d.makeURL`
    (`T6/d.java:17-19`) rebuilds the URL from the previous reply's
    `getHost()`/`getPort()` unless `host_notmodify` is set, and that flag is
    `false` by default (`T6/h.java:43`, `isHostNotmodify()` at `:134-135`) and
    never set by `KTApplication`; `T6/i.java:50-53` is where `ip`/`port` are
    read. Declining it leaked roughly half of every slot taken, which is exactly
    the behaviour NetFunnel exists to prevent.
    So `5101` now goes to the front door while `5002` and `5004` go to the node
    that issued the session, the node rides on `KorailNetFunnelToken.node`, and
    it supersedes as the key does — a reply naming no node leaves the last one
    in force, and a bypass has neither a session nor a node.
  - **The redirect is constrained, not trusted.** A response choosing where the
    next request goes is what an origin guard exists to stop, so the naming is
    admitted only into the queue's own pool: `rnf<1-99>.letskorail.com`,
    lowercase, no leading zero, matched as whole labels, or the front door
    itself; `https` on port `443` and no other port, because the port is not
    followed on the server's say-so either. Anything outside the rule is a
    **hard error**, never a quiet fall-back to the front door — falling back
    silently is what produced the flaky release, since it turns "this reply is
    lying to us" into "this slot leaked", and a leaked slot makes no noise. The
    rule lives in `safety.py` beside the origin assertions rather than in the
    client, `assert_korail_netfunnel_origin` still refuses a node (it guards the
    configured origin and the entry call, so widening one guard cannot widen the
    other), `follow_redirects` stays `False`, and the canonical-origin guarantee
    for `smart.letskorail.com` is untouched.
  - **The `5101` key is a ticket, not a session — the first defect the probing
    exposed.** `acquire` originally returned the 5101 reply and `release` sent
    that key to `setComplete`, which the server refuses with
    `503:msg="Wrong Server ID"` every time, with or without `sid`/`aid`. Only a
    key `chkEnter` issued is completable, and it is a different, shorter one
    (252 characters became 104). So `acquire` now always performs the 5002,
    even when 5101 reported `nwait=0`, and **every step's key supersedes the
    one before it** — including each 201 poll, and including a 201 that echoes
    no key at all, where the last known key stays in force. A successful
    release answers `200:` with an *empty* `key=`, which parses as a release
    rather than as a truncated body. `503` is refused rather than accepted
    beside the `502` we do accept, and the keyless short-circuit in `release`
    is narrowed to a bypass (`300`), so no other token can skip the request
    silently. Note that `503` has **two** causes and the wire cannot tell them
    apart — an unexchanged ticket, or the wrong node — so the exception message
    names both.
  - **Read literally, the APK disagrees, and the live server wins.**
    `T6/g.java`'s poll loop leaves the moment the status is not Continue —
    `T6/g$a.smali:243-247` → `:282` → `:892` shows the fall-through is a
    `return` — so after a 200 from 5101 the app sends no 5002 and completes
    with the ticket. The `5002` stays unconditional anyway: `5101` → `5002` →
    `5004` is the only sequence ever seen to release cleanly, and whether the
    ticket would complete at its own node has never been probed. The APK does
    corroborate the supersession: one response object, overwritten at `:61` and
    `:107`, with `Complete()` sending whatever key arrived last (`:79`).
  - **KORAIL does not speak the JavaScript dialect, and this is the whole
    substance of the change.** `nf.letskorail.com` serves both apps, so the
    live-verified `srt-mobile-api` implementation was expected to be a template.
    It is not: SRT is a WebView over `netfunnel.js` and sends the browser
    dialect (`nfid`, `prefix`, `js=yes`, a trailing epoch), while `korail.apk`
    embeds STCLab's native Android SDK — the `T6`/`U6` packages — which sends
    none of it. The three requests are `5101` `opcode,sid,aid`
    (`T6/d.java:99-101`), `5002` `opcode,key` (`:54-55`) and `5004` `opcode,key`
    (`:78-79`), in that order, because `U6/a.java` renders the `addParam` list
    with `URLEncodedUtils.format`. So `sid`/`aid` ride on `5101` **only**, the
    opposite of the JS dialect; `ttl` is never sent back at all, being read only
    to decide how long to sleep (`T6/g.java:462`) and clamped to 30 seconds
    (`T6/h.java:40`) rather than the JS bundle's 5.
  - **The response shape was the one assumption no live run had checked, and it
    holds.** `T6/i.java:36-43` parses everything before the first `:` as the
    status code, so the reply must be `<code>:<params>` and not the JS
    dialect's `<rtype>:<code>:<params>` — feed the app the latter and it reads
    the code as 5002 and finds no key. Every 2026-07-26 reply arrived in exactly
    the native form. `parse_netfunnel_body` still rejects a `NetFunnel.gRtype=…`
    body and names that possibility in its error message, now as a diagnosis
    for a server that changed rather than as a hedge against our own guess.
  - **The key never rides on a KORAIL request.** No Retrofit interface in the
    app declares a `netfunnelKey`-shaped field on any route; the queue gates the
    call rather than parameterising it, which is why this is a separate client
    on a separate host and why reserve, pay, cancel and refund send exactly what
    they sent before.
  - **Off by default, enforced at construction.** `KorailConfig.
    netfunnel_enabled` is `False`, and `KorailNetFunnelClient` on a config
    without it raises before any socket exists. Enabling it adds a round trip
    and a failure mode to every gated operation and buys nothing until the
    server actually meters us. It is meant for peak season, which is why the app
    carries a separate peak-season inquiry queue (`act_8_2`) at all.
  - **The wait is bounded twice** — 20 polls and 60 seconds, whichever comes
    first. The app polls indefinitely (`T6/g.java:449`) behind a dialog a human
    can close; this library has none, and a queue is a wait rather than a retry.
    No retry logic was added.
  - **The slot is released on both paths**, as the app releases it from
    `BaseDaoHelper`'s `onPostExecute` (:105-107) whether or not the gated call
    raised. A failed release **raises** on the success path instead of being
    swallowed: the sibling repo bounded its key at 128 characters while real
    keys are 256, so every release was refused before it was sent and leaked
    every slot silently until a live run exposed it. The 2026-07-26 probe added
    two more real lengths — 252 from `5101` and 104 from `5002` — so the guard
    stays at 512 characters and is deliberately not tightened to any single
    observed length.
  - **Three exact query contracts are registered, not an allowlist loosened**,
    and the queue hosts have their own origin assertions — one for the front
    door and the entry call, a wider one for the pool, and a third that decides
    which of the two a given opcode gets. `KORAIL_READ_ONLY_ROUTES` is untouched
    at 54, so `post_form`/`get_json` can never reach `/ts.wseq`. `5003`, `5105`
    and `5106` are declared as constants and rejected by the guard.
- Corrected: `docs/RELEASE_GAP_PLAN.md` still carried, in its srtgo-corrections
  appendix, the withdrawn claim that "Korail uses **no** NetFunnel at all — only
  SRT does". The body of that document has said otherwise since 2026-07-26; the
  appendix now agrees with it. The corresponding "not yet implemented" notes on
  the `service_1` / `act_6` gate in `README.md` and
  `docs/IMPLEMENTATION_PROGRESS.md` were also stale and are corrected: the gate
  exists, and what still holds R39 back is its unregistered route.
- Added: server-side failures are classified on `h_msg_cd` instead of all
  arriving as one `KorailAppError`. New types — `KorailNoResultsError` (with
  `KorailNoDirectTrainError`), `KorailSoldOutError`,
  `KorailSeatUnavailableError`, `KorailReservationRefusedError`,
  `KorailInvalidRequestError`, `KorailNotEntitledError`,
  `KorailServiceUnavailableError`, `KorailAppUpdateRequiredError` — plus the
  exported `classify_app_error`. See the error-taxonomy table in README for
  which one means retry is pointless, which means re-login, and which means the
  request was fine and there was simply nothing there.
  - **Compatibility-preserving.** Every new type subclasses `KorailAppError`,
    so no existing `except` clause changes meaning, and `code`/`message`/`raw`
    stay on all of them so a caller can migrate incrementally.
  - **It never invents a failure.** Whether a response failed is still decided
    by `strResult` plus the app's own `WRC000288`; classification only picks
    which exception describes a failure that was already going to be raised.
    The app behaves the same way — any unrecognised code on a non-`FAIL`
    response goes to `onReceive()` as a success (`BaseActivity.java:629`) — so
    a warning attached to a success stays a success. `WRR664296`, which came
    back with `strResult=SUCC` and a real, cancelable PNR, is pinned by test,
    as are the APK's own success-side codes `IRR000014`, `IRT800005` and
    `WRS800036`.
  - **No retry logic was added.** The library still does not retry on its own
    initiative, and `reserve` is never retried, because a retried reserve is a
    duplicate booking.
  - Sold-out (`ERR211161`), the seat-specific refusals
    (`WRI411345`/`ERR911081`/`WRT800176`, for which the app offers automatic
    seat assignment rather than a dead end), the reserve refusals
    (`WRR800029`/`ERR911531`/`ERR911051`, which the app answers by navigating
    to the user's existing reservations), `WRD000061`, `WRG000000`, `P114`,
    `SEMGTK` and `SUPDATE` are all APK branches, cited file:line in each
    docstring. `P100`, `WRT300005`, `ERR299943`, `WRG200018`, `WRT100002` and
    `WRT100124` are this repository's live observations with zero APK hits and
    are labelled as such.
  - Anti-macro turned out not to be a code: `BaseDaoHelper.java:59-86` reads
    the `DynaPath-Result` header and shows the body's `message` instead of
    running the `h_msg_cd` ladder, so the existing `KorailDynaPathError` already
    is the anti-macro refusal. srtgo_plus's `MACRO` substring rule and srtgo's
    second sold-out code `IRT010110` are recorded as third-party-attested only
    and not encoded; a test asserts neither was adopted.
  - `[3]인증정보에 문제가 있습니다.` is deliberately left unclassified: no
    `h_msg_cd` was captured with it and the string is 0-hit in the APK, so
    classifying it would mean the Korean-text matching this change removes.

- Added: `reserve` reaches all three of the booking screen's job types through a
  keyword-only, defaulted `job_type` (`KorailReservationJobType`). The default
  is `IMMEDIATE` (`txtJobId="1101"`), the only value this package has ever sent,
  so every existing call is byte-for-byte unchanged.
  **Both variants were live-verified on 2026-07-26** by reserve -> read back
  -> cancel. `1103` booked the exact seats requested (compare the
  inventory's `seat_spec` to the detail's `h_seat_no`, not `seat_no`).
  `1102` on a sold-out train answered `IRR000014`, and
  `confirm_standby_hold` answered `IRZ000003`.
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
