# Changelog

이 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 형식을 따르고,
이 프로젝트는 [유의적 버전](https://semver.org/lang/ko/)을 따른다.
1.0.0 이전 기록은 당시 형식·언어 그대로 보존한다.

## 1.0.0 - 2026-07-27

### Added

- Added: `scripts/README.md`. Three of the four committed scripts talk to the
  live server and one of them moves money, and until now nothing in the
  repository told a reader which was which; `capture_live_read_surface.py` was
  referenced only from test comments. The page states the rules that hold for
  all of them (two switches minimum, credentials from the environment only,
  pacing, import safety, run against your own account) and points at each
  script's own docstring for its variables rather than duplicating them.
- Added: `build_config_from_env` is exported from the package. It is the
  supported way to pin a **real** device identity —
  `KORAIL_DYNAPATH_DEVICE_ID` / `_OS_VERSION` / `_DEVICE_MODEL` — and the
  only way to get a device id stable across processes, since nothing here
  persists state. `read_credentials_from_env`, `live_enabled` and
  `run_live_smoke_from_env` stay unexported: the first would make this
  package assert an opinion about where a caller's credentials live, and the
  other two are this repository's own smoke scaffolding.
- Added: `tests/test_default_login_config.py`, which pins the three things
  that were wrong and are checkable offline — DynaPath enabled, an
  app-shaped UA, and the UA's handset agreeing with the token's — plus the
  per-instance device id. It asserts **nothing** about a login succeeding;
  that is not offline-checkable and is not claimed anywhere.
- Added: 장바구니 담기 as a consent-gated mutation —
  `KorailClient.add_to_cart`, `POST cart.addCartList`
  (`CartService.java:11-13`), with `CartAddRequest` and
  `build_cart_add_form`. One request field beyond the common three —
  `hidPnrNo` — confirmed against `AddCartDao.java:9-24` and, independently,
  `AddCartDao$AddCartRequest.smali` / `CartService.smali`. `get_cart_list`
  already read the cart; this is the write half. The DAO's response type is a
  bare `BaseResponse`, so `add_to_cart` returns the unparsed envelope rather
  than a dedicated response type, same as `extend_discount_card`.
  Live-verified 2026-07-27 by hand: a held PNR added cleanly, `SUCC` /
  `IRZ000002`, and the row read back out of `get_cart_list`. No script or
  test in this repository sends it.
- Added: a seventh mutation consent category, `"cart"`, with its own
  `MutationConsent.allow_cart` flag defaulting to `False`. Deliberately
  **not** a reuse of `"reserve"`: the hold this acts on already exists and
  the call creates and destroys nothing this package can observe. It carries
  no card number and so is not a member of
  `KORAIL_CARD_BEARING_MUTATION_CATEGORIES`.
- Added: two reads of the 승차권 변경 chain. The read-only boundary is now
  60 routes and `KorailClient` exposes 77 public methods — 64 login/read plus
  the thirteen consent-gated mutations.
  - `get_self_seat_change_info` — `POST self.seatChgInfo.do`
    (`TicketService.java:54-56`, `TicketService.smali:280-325`). Eight fields;
    `psrmClCd` is registered OPTIONAL because `TCSOptionsActivity.java:135-138`
    sets it only for 일반실 (`"1"`) or 특실 (`"2"`) (`K4/o.java:7-8`,
    `K4/o.smali:34-82`) and Retrofit drops it otherwise. `trnNo` is forwarded
    verbatim, not zero-padded: `:132` copies `h_trn_no` as-is.
  - `get_original_ticket_inquiry` — `POST research.tripChgOgtk.do`
    (`ResearchService.java:61-63`). The `@FieldMap` keys are
    `ROrtg.OGTK_SALE_WCT_NO`/`OGTK_SALE_DD`/`OGTK_SALE_SQ_NO`/`OGTK_RET_PWD`
    (`ROrtg.java:8-11`, `ROrtg.smali:20-26`), each already ending in `_`, with
    a 1-based row number appended — so `ogtkSaleWctNo_1`, `ogtkSaleDd_1`, and
    so on. Pinned by `_is_original_ticket_field_order` in `safety.py` rather
    than by a name set, since the key set grows with the ticket count.
    - **`tkCnt` is NOT pinned to the group count**, and it is sent as an
      `int` (`ResearchService.smali:613`, `I`) rather than the string the
      neighbouring `tk.plfNo.do` uses for the same name. The app disagrees
      with itself about the meaning: `TCBookingActivity.java:179` sends the
      passenger count, `PushHistoryActivity.java:357` the row count, and
      `SeatSearchActivity.java:615` a hardcoded `1` over `f29962H.size()`
      rows. A `tkCnt == N` check would reject two of the three.
    - **The indexed keys' ORDER is this package's choice.** The app hands
      Retrofit a `HashMap` (`OgTkInquiryDao.java:15,52`), so its wire order is
      unspecified, and its own call sites do not even insert in the same
      order. Grouping by ticket in `ROrtg` declaration order is deterministic.
- Added: 운임 재계산 as a consent-gated mutation —
  `KorailClient.recalculate_price`, `POST
  certification.PriceReCalculation` (`CertificationService.java:35-37`), with
  `PriceRecalculationRequest`/`PriceRecalculationRow` and
  `build_price_recalculation_form`. It re-prices an ALREADY HELD PNR after the
  payment screen's discount selection changes. Never transmitted; not
  live-enabled.
  - **The six parallel `List` `@Field`s pair by index, one row per seat.**
    `k2()` (`a6/C1042B.java:275-283`) is a single loop over one
    `DiscountPriceParams[]` appending one field of the same element to each of
    six `ArrayList`s, so element *i* of all six belongs to seat *i*. Verified
    in `smali/a6.1/B.smali` rather than taken from jadx. The 다자녀 variant
    (`a6/C1041A.java:57-80`) builds rows differently and calls the same `k2()`.
  - **They go out as repeated keys, not indexed ones.** Retrofit 1.x flattens
    an `Iterable` `@Field` with `addField(name, element)` in a loop where the
    name is loop-invariant (`RequestBuilder.smali:1537-1601`), so the body is
    `psg_tp_dv_cd=..&psg_tp_dv_cd=..` with no brackets or suffix. The builder
    returns list values; httpx encodes them identically and the mutation
    transmit gate needed no change.
  - `hiduserYn`/`hidCustNo` are sent only for a non-member
    (`a6/C1042B.java:290-293`); Retrofit omits a null `@Field`, so a member's
    form is twelve keys, not fourteen.
- Added: a sixth mutation consent category, `"price_recalculation"`, with
  `MutationConsent.allow_price_recalculation` (default `False`). Deliberately
  **not** a reuse of `"payment"`: a payment consent authorises settling an
  already-quoted amount, and this route rewrites the quote, so folding them
  together would let a consent to pay a sum authorise changing what the sum is.
- Added: 병합예약. `KorailClient.reserve_merge`,
  `build_merge_reservation_form`, `is_merge_eligible`,
  `KorailReservationJobType.MERGE_STANDING` (`"1202"`),
  `KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE` (`"21"`),
  `KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE` (`"22"`),
  `KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`, and
  `TrainSummary.merge_seat_application_flag` (`h_yms_apl_flg`).
  **병합 is ONE train split at a mid station so its two halves can be seated
  differently — not a transfer.** 좌석 연결역 선택 /
  "구간을 좌석+좌석 또는 좌석+입석으로 연결하여 이용하실 수 있습니다"
  (`res/values/strings.xml:702,577`). You board once.
  - The `K4/e` codes were resolved from bytecode
    (`analysis/apktool/smali/K4/e.smali:31-55`) because **three of its four
    members reach jadx as unrelated same-valued constants**: `TRANSFER` as
    `TicketSelfCheckinStatusActivity.CHECKIN_STATUS_EXCEED` and
    `STANDING_SEAT_1` as `I4.a.BEFORE_DEPARTURE`. 직통 `11`, 환승 `14`,
    병합 선행 `21`, 병합 후행 `22`.
  - 병합 is TWO holds. The first is the ordinary direct form with
    `txtJobId="1202"` and nothing else changed
    (`DirectInquiryActivity.java:448-451`, tag set at `a5/u.java:394-397`); the
    second replaces it with two journeys on the same train. Between them sits
    the server: KORAIL puts the literal `<중간연결역 변경>`
    (`strings.xml:2018`) in the first hold's own message text, and the confirm
    screen's span table (`res/values/arrays.xml:421-438`,
    `K6/C5956a.java:74-77`) turns that literal into the tap that starts the
    merge. The offer is KORAIL's, not the client's.
  - The merged form is built by `DirectInquiryActivity.java:576-601`, NOT by
    `C5/a.java`'s journey loop, and diverges from a 환승 in four ways, all
    re-read at `analysis/apktool/smali/…/DirectInquiryActivity.smali:5580-6010`:
    `txtJrnyTpCd{i}` keys on the loop INDEX so the legs differ (`21` then `22`)
    where a 환승's both read `14`; `txtStndFlg` is pinned `"Y"`; leg 2's cabin
    is copied from leg 1's rather than read per leg; and there is no
    `setArvTm` call at all, so `arvTm_2` does not exist and `arvTm_1` keeps the
    standing hold's WHOLE-ROUTE arrival time. That last one is why
    `build_merge_reservation_form` takes the standing hold's `TrainSummary`
    alongside the two split legs — the stale value is on the wire.
  - `reserve_merge` does NOT cancel the standing hold it replaces, although the
    app does. That cancel is `cancel_unpaid_hold` under the `"cancel"` consent;
    performing it inside a `"reserve"`-gated method would let a reserve consent
    release a live PNR.
  - Touches the reserve route because the feature is the reserve route: same
    path, same `"reserve"` category, one new `txtJobId` value and one new
    builder. Every existing call is byte-identical — a contract test rebuilds
    the live-verified one-adult form and compares it key by key.
  - **NEVER TRANSMITTED.** No form in this feature has reached KORAIL.
- Added: `KorailClient.reserve_with_discount_card` and
  `build_discount_card_reservation_form`, plus
  `KORAIL_DISCOUNT_CARD_DISCOUNT_CODE` (`"153"`) and
  `KORAIL_DISCOUNT_CARD_MENU_ID` (`"A2"`).
  **A reservation CAN carry a 할인카드, and it does so through the ORDINARY
  reserve route.** `w4/a.java:93-104` builds a plain `ReservationRequest`; its
  only caller, `SeatAssignBookingActivity.java:153-163`, hands it to
  `NCardDirectInquiryActivity`, whose base class POSTs it with a plain
  `ReservationDao` (`c5/b.java:128-138`) to
  `certification.TicketReservation` (`CertificationService.java:52-54`). There
  is no N카드 reservation endpoint; there is an N카드 passenger block.
- Added: 할인카드(N카드) 구매 and 기간연장 as consent-gated mutations —
  `KorailClient.register_discount_card` and
  `KorailClient.extend_discount_card`, plus `DiscountCardPurchaseRequest`,
  `DiscountCardSectionRequest`, `DiscountCardAdditionalUser`,
  `DiscountCardTicket`, `DiscountCardPurchaseResponse`,
  `parse_discount_card_purchase_response` and
  `KORAIL_MAX_DISCOUNT_CARD_SECTIONS` (`3`).
  **NEVER TRANSMITTED, and no live path in this repository can transmit them.**
- Added: a fifth mutation consent category, `"discount_card"`, with its own
  `MutationConsent.allow_discount_card` flag defaulting to `False`. It is
  additive: every consent written before it exists means exactly what it meant
  before. It is NOT a reuse of `"reserve"` — `research.dcntCrdInfo.do` buys a
  product rather than a seat, and nobody who opted into placing a train booking
  also opted into buying a discount card.
- Added: `KorailHttpClient.get_mutation_query`, the send path for a mutation
  the app performs as a GET. `reservation.dcntCrdExtn.do` is declared `@GET`
  with seven `@Query` parameters (`ResearchService.java:65-66`) and genuinely
  changes state. Registering it as a POST would have been less code and would
  have made the allowlist describe a request the app never sends; a mutation
  does not become safer by being mis-registered. Every gate of
  `post_mutation_form` applies unchanged — consent, the dry-run refusal,
  `assert_mutation_route` on the exact `(method, path)` pair, and the
  route/category cross-check.
  - `research.dcntCrdInfo.do` is a PURCHASE despite its name. It answers with
    `lumpStlTgtNo` and `rcvdAmt` (`NCardReservationDao.java:127-134`) and the
    app hands that target number to the payment screen
    (`SectionNCardInquiryActivity.java:213-257`), so what it creates is an
    unpaid purchase awaiting settlement.
  - Its two `@FieldMap`s are flattened with the DAO's own indexed key
    spellings (`NCardReservationDao.java:74-124`): `jrnyCnt` + `jrnyTpCd_N` /
    `runDt_N` / `trnNo_N` / `dptRsStnCd_N` / `arvRsStnCd_N`, and `apdUsrCnt` +
    `custMgNo_N` / `apdCustName_N` / `apdCustTeln_N`. `mCustomData` is
    deliberately absent — it is never passed to `executeDao` (`:180`) and never
    reaches the wire.
  - **Open, and the operator must settle it:** no v6.5.0 call site populates
    `jrnyInfo`/`apdUsrInfo`, only the setters that would. Whether a 1-section
    card must still send a section, and whether `apdUsrCnt` must be present as
    `"0"` rather than omitted for a 1인용 card, is unknown. `dcntCrdExtn.do`'s
    DAO response type is a bare `BaseResponse`, so a successful extension's
    reply — and its cost — is unknown too.
- Added: `RefundTicketDetailResponse.discount_card`, plus `DiscountCardOnTicket`
  and `DiscountCardSection`. No new route and no new method: `SelTicketInfo`
  already returns `TicketDetailDao.TicketDetailResponse`, which carries
  `dcnt_crd_info` (`dao/refund/TicketDetailDao.java:233`) whenever the "ticket"
  being read is itself a 할인카드. The package was already fetching that object
  and discarding it.
  - This is the entry point to everything else in the 할인카드 surface. The
    card number is the sole input to `get_discount_card_usage_history`, the
    section rows are where `get_discount_card_schedule`'s station NAMES come
    from, and `h_dcnt_crd_trm_extn_psb_flg` is the only thing that enables
    기간연장 in the app (`Y4/C0907b.java:301` → `Y4/Q.java:1013-1026`).
  - The section list's wire key is `appSegList` — the Java FIELD name
    (`TicketDetailDao.java:124`), which is what Gson serialises. The getter is
    spelled `getAppSeg_info()` and is NOT the wire name; taking the getter
    would have produced a parser that silently found no sections.
- Added: loyalty READS, and the welfare entitlement one of them exposes —
  `KorailClient.get_korail_point_summary` and
  `KorailClient.get_mileage_history`, plus `KorailPointSummaryResponse`,
  `MileageHistoryRequest`, `MileageHistoryEntry`, `MileageHistoryResponse` and
  the five `KORAIL_MILEAGE_*` selector constants. The read-only boundary is now
  58 routes.
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
- Added `refund` on the same gated send path. Its live send path is fully
  active code, not blocked, but it has never been exercised against the live
  server: a refund acts on a settled ticket, and this package's fake-card
  payment is always declined, so no paid ticket is produced here. Its request
  contract, gates, and redaction are covered by offline tests only, and it must
  be treated as unverified against the real service.
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
- Added closed tagged public reads for gift-ticket list modes, commuter jobs
  `a`/`b`/`c`, and one/two-leg fare quotes. Exact ordered forms preserve R31
  duplicate fields and intentionally omit R52 `trnCnt`; only R52 uses the
  pre-existing conditional DynaPath path.
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
- Added strict synthetic parsers and frozen repr-safe models for R13, R32,
  R43, and R45. R54 tour-train response parsing is static-contract support
  only: no client method, safety route, or raw-string request builder exists.
- Initially added four typed P0 train reads from static APK evidence for
  free-seat car guidance, guide-seat conditions, seat-assignment schedules,
  and merged-seat inquiry.
- Initial implementation added frozen closed request objects, exact POST field
  allowlists, strict response parsers, repr-hidden identifiers/free text/raw
  mappings, and synthetic-only fixtures; that implementation step added no
  live call or DynaPath route.
- Added typed session-unverified pass-menu, commuter-kind-menu, and
  crew-request option reads with caller-required runtime discriminator codes;
  any live verification starts only after login.
- Added frozen repr-safe models, strict parsers, synthetic fixtures, and
  offline route, request, error, export, and documentation coverage.
- Added three static-evidenced limousine schedule and seat-inventory reads with
  closed caller-supplied query dataclasses, exact POST allowlists, typed
  repr-safe parsers, one-shot session/error handling, and DynaPath disabled.
- **Added: this package is licensed.** `LICENSE` carries the Apache License
  2.0 verbatim, and `pyproject.toml` declares it in the PEP 639 SPDX form
  (`license = "Apache-2.0"`, `license-files = ["LICENSE", "NOTICE"]`) rather
  than the deprecated `license = {text = ...}` table, which setuptools now
  warns on and will reject outright from 2027-02-18. The build floor moved to
  `setuptools>=77` for the same reason: earlier versions ignore `license-files`
  silently, producing a wheel that claims a licence and ships no licence text.
  No `License ::` classifier accompanies it — PEP 639 makes the two mutually
  exclusive. `NOTICE` is declared alongside `LICENSE` rather than left at the
  repository root alone: Apache-2.0 §4(d) requires a redistributor to carry the
  attribution notices forward, and a wheel that omits the file makes that
  impossible. Both artifacts now carry both files.
- Added: owner and canonical-URL metadata. `authors` names `yakisoba0728` and
  a contact address — spelled in `pyproject.toml`, not repeated here, because
  `tests/test_readme.py` forbids a bare email address in the evidence
  documents and that gate is worth more than the duplication.
  `[project.urls]` pins Homepage, Repository, Issues and Changelog at
  `https://github.com/yakisoba0728/korail-mobile-api`.
- Added: `korail_mobile_api.__version__`, with a test asserting it equals
  `project.version`. Nothing in the build keeps a hand-written dunder and a
  hand-written TOML literal in step; that test is the only thing that does.
  It is deliberately absent from `__all__`.
- **Added: `tests/test_public_surface_rule.py`**, which is what stops the
  above from being undone by the next person with a convenient name to export.
  It holds no list of names — a hand-maintained name list is exactly what
  rots. It derives `__all__`'s expected contents from `__init__.py`'s import
  statements via `ast` (so dropping an `__all__` entry while leaving the
  import behind fails), refuses any name from a module not on a short
  module-level policy list, refuses `parse_*`/`pair_*` outright, walks the
  transitive closure of every public client method's annotations and requires
  each package-defined type in it to be exported, and requires every exported
  non-type to appear in a `DOMAIN_CONSTANTS` table with a written reason. The
  file is shared verbatim with the SRT package below a marked per-repository
  header.

### Changed

- **Changed: `scripts/reserve_pay_refund_roundtrip.py` no longer starts without
  a fare ceiling.** `KORAIL_MAX_FARE` was documented as "optional … strongly
  recommended", but it is the *only* thing that caps what the script charges:
  step (d) compares the amount owed against it and simply skips the comparison
  when it is unset. Nor does the train choice bound the cost — when neither a
  fare quote nor the search row's own price hint can be obtained, the script
  falls through to the first reservable train at whatever it costs. So an
  operator who followed the documented command without the variable was running
  an uncapped real-card charge. The requirement is enforced on the charging path
  only, before the card is read, before login and before any request; a
  malformed value now aborts there too instead of ~200 lines later. `--recover`
  is unaffected — neither of its branches charges anything.
- Changed: the docs no longer reproduce decompiled KORAIL app code. The one
  place that pasted a Java method body and its smali (`docs/deep-dive/
  impl-audit-2026-07-22.md`, the `setTrnCnt` self-assignment no-op) and the one
  that pasted a Retrofit interface declaration (`docs/audit-2026-07-27/phase2/
  safety.md`, `dcntCrdExtn.do`) now describe what was observed instead. Every
  `file:line` citation is kept, and so is the bytecode-level detail that ruled
  out a decompiler artefact — the change is to the form of the evidence, not its
  force. The audit doc states the rule it now follows: cite the third party's
  work by location, quote only the wire-level names the client must match.
- Changed: the two machine-generated catalogs followed the same rule instead of
  being exempted for being generated. A second sweep by CONTENT (not by fence
  tag) found ~660 more copied source lines than the fence scan did:
  `docs/deep-dive/local-storage-catalog.md` pasted the whole statement for each
  of 644 key rows, and `docs/deep-dive/webview-and-url-catalog.md` pasted 26
  method lines and 17 statement cells. Nothing evidential is lost — the storage
  catalog's Context column now names the access it always meant (`쓰기
  putString` / `읽기 getInt` / `존재 확인 containsKey`), derived mechanically
  from the statement it replaced; the WebView catalog's Signature column drops
  the body's opening brace, which is what made those rows source lines rather
  than signatures; and its route-annotation cells are untouched, because a
  route is interface the client must match. Key names, `file:line` and counts
  are unchanged, so every row is still checkable against the same APK.
- Changed: absolute paths in the docs no longer carry a local username. All 14
  were rewritten to repository-relative form, so no exemption list exists for a
  future leak to hide in. The one path that is not inside this repository — the
  `srtgo_plus` reference checkout — is described as a local checkout rather than
  given an invented upstream URL.
- Changed: the vendor-key placeholders left by the history rewrite now read as
  sentences. `<KORAIL-APP-…-REDACTED>` sites explain which field stood there and
  why the value is absent; `kakao<key>://oauth`, which had become a false
  literal, is written as the rule it always was (the scheme is `kakao` followed
  by the app key). `docs/RELEASE_GAP_PLAN.md` used to declare "values
  deliberately NOT copied into this plan" while pointing at a document that
  printed them — it now records that the contradiction is resolved, that the
  values are gone from the history as well as the tree, and that the one value
  still in the clear (the GCM sender id, a Firebase project *number*, not a
  credential) is retained on purpose rather than missed.
- **Changed (behaviour, and the reason for everything below): a bare
  `KorailClient()` can now log in.** It could not before, and the README's
  quickstart — `KorailClient()` then `login(...)` — was therefore false.
  Live-verified 2026-07-27: a default `KorailConfig()` sent
  `User-Agent: korail-mobile-api/0.2.0` with DynaPath disabled, and
  `login.Login` came back `**MACRO ERROR**` from the anti-automation check.
  The only configuration that logged in was `build_config_from_env`, which
  the README never mentioned and `__all__` did not export. The failure was
  hard to read because it is **disguised**: the server returns the macro
  rejection as "원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…",
  and because account-neutral reads keep succeeding under the same config,
  the symptom looks like a version gate rather than a client-shape problem —
  which it had already been misdiagnosed as once. Three defaults changed:
  - `KORAIL_USER_AGENT` is now the platform-default Dalvik string,
    `Dalvik/2.1.0 (Linux; U; Android 15; Android)`, instead of
    `korail-mobile-api/0.2.0`. The app hardcodes no UA — Retrofit v1 over
    `UrlConnectionClient`/`HttpURLConnection` (`ExecuteDao.java:7-11`) — so
    the platform string is what the server sees from the real app. It is
    **derived**, by a new `build_dalvik_user_agent`, from the same
    `KORAIL_DEFAULT_DEVICE_NAME` / `KORAIL_DEFAULT_ANDROID_OS_RELEASE` that
    the DynaPath token's `dm` and `os` carry, and `build_config_from_env`
    now calls the same builder: a UA claiming one handset while the token in
    the same request claims another is itself a signal, so the two cannot be
    spelled separately any more.
  - **DynaPath is enabled by default.** Every client now attaches
    `x-dynapath-m-token` to the six allowlisted paths where it previously
    attached none. Where a token is sent is unchanged; only whether one is.
    Opt out with `KorailConfig(dynapath=DynapathConfig())`.
    `DynapathConfig`'s own defaults are untouched — the enabled default and
    its token settings hang off `KorailConfig`'s field factory instead,
    because `DynapathConfig.__post_init__` requires exactly one of
    `token_provider`/`token_settings` and a defaulted `token_settings` would
    have made every `DynapathConfig(enabled=True, token_provider=fn)` a
    contradiction.
  - The default token settings generate their device identity **per
    `KorailConfig` instance**, via `generate_dynapath_device_id`. No fixed
    device id is baked into the package: `di` is the handset's
    `Settings.Secure.ANDROID_ID` (`AbstractC1228a.java:16`, emitted verbatim
    at `C1229b.java:103`), and an identifier shared by every installation of
    a library is exactly the bot signature the header exists to catch — the
    criticism this repository already levelled at srtgo's fixed
    `558a4f02041657ea`. It is `uuid.uuid4().hex[:16]`, matching ANDROID_ID's
    real 16-lowercase-hex shape, stable for the life of the config and not
    persisted. `app_start_ts` is the moment the config was built, which is
    what `AbstractC1228a.java:14` records.
- Changed: `EXCLUDED_API_DOMAINS` no longer contains `"points-mileage"`; it
  contains `"points-mileage-write"`. The old label excluded the whole loyalty
  area including its balance reads, which the user has now asked for. The new
  label names only what is still refused, and each refusal now has a reason
  rather than a category: `mlg.lpotAthn.do` and `xPoint.XPointView` take a
  user-supplied point PASSWORD and answer with `pwdErrTno`, a failure counter,
  so a wrong guess is a state change at the loyalty provider no matter what the
  screen title says; `xPoint.OkCashbagCertView`, `mileage.acpnMlgSave.do` and
  `mileage.acpnMlgNoti.do` are registration/accrual writes. A test pins that
  all five stay unreachable and that no other excluded domain moved.
  - **`xPoint.MyXPointView` is the account-entitlement read this project did
    not know it had.** Besides the point balance it carries `h_hdcp_flg`, and
    `MyPageActivity.java:206-212` reveals the entire 장애인 section on that
    flag alone, filling its two rows from `h_subt_dcs_cl_nm` (labelled 장애인증,
    `:353,393`) and `h_cust_lead_flg_nm` (labelled 보조견, `:355,394`). An
    account whose flag is not `"Y"` therefore holds neither registration —
    which is the shape of an explanation for the live `ERR299943`
    "예약할인이 지원되지 않습니다" that refused 1~3급 장애 + 안내견 on a
    byte-exact form (`docs/MUTATION_HANDOFF.md:172-179`). **Hypothesis, not
    finding**: it is what the app does with the flag, not an observed pairing.
  - `point_dv_cd` is not a caller parameter. `KorailPointInquiryDao.java:87-92`
    has no request class and passes the literal `"0"`, so the builder takes no
    arguments at all.
  - The mileage read's page size is the app's hardcoded `"20"`
    (`MileageHistoryActivity.java:274`) rather than an option, and `qryDvVal`
    is a dropdown INDEX rather than a code — `:566` assigns
    `Integer.toString(i9)` straight from `onItemSelected`, with the three
    entries declared 전체/적립/사용 at `:502`. The date window has no default
    because supplying one would put a clock in a payload builder; the app's own
    default is the "최근 3개월" branch at `:372-380`.
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
- The transmit gate now requires a payment consent to state exactly ONE card
  claim. Neither flag set is the original refusal, unchanged. BOTH set is
  refused as a contradiction: a consent that claims a test card while
  acknowledging a real charge is a caller bug, and paying on an ambiguous
  consent is the mistake the gate exists to prevent. The boundary is now 54
  exact login/read routes and 61 public methods; no new route was added.
- `ReservationSeatDetail` maps the passenger type from `h_psg_tp_cd`, which is
  what `ReservationResponse.SeatInfo` declares. The `h_psg_tp_dv_nm` that a
  reference client names does not appear anywhere in the decompiled app and was
  not observed live, so it is deliberately not mapped; an unmapped key stays
  reachable through `raw`.
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
- Kept R17's known HTTP 404 as a one-request `KorailTransportError` with no
  retry, fallback, or alternate path. R17 and R31 require a local session;
  R52 does not invent one.
- Retained login `strCustNo` as a repr-hidden session customer number for the
  customer-trip request; member and member-card identifiers are not fallbacks.
- Kept the Java Retrofit names as documentation aliases only and deliberately
  omitted `TrainSummary` convenience chaining and every adjacent mutation.
- Tightened only these four route parsers to require exact `strResult=SUCC`
  after preserving the existing `FAIL`, `P058`, and `WRC000288` errors.
- Reject limousine query subclasses and invoke each concrete dataclass
  validator non-virtually before Sid generation or transport.
- Require exact `strResult=SUCC` for all P0 menu and limousine typed parsers.
- Normalize live-evidenced JSON integer and ASCII decimal-string station popup
  types and actual arrival delay counts without accepting broader coercions.
- **Changed: `scripts/verify_distribution.py` now verifies this metadata
  instead of banning it.** The four headers a PEP 639 build emits —
  `License-Expression`, `License-File`, `Author-email`, `Project-URL` — moved
  out of the forbidden list and into exact-value checks derived from
  `pyproject.toml`, alongside the ones `Name`/`Version`/`Requires-Python`
  already had. Merely un-banning them would have left the licence and the
  owner as the only unchecked metadata in the artifacts. `License`,
  `Author` (bare), `Home-page`, `Download-URL`, `Maintainer` and
  `Maintainer-email` stay forbidden: no configuration here emits them, so
  their presence would mean something other than this pyproject wrote them.
  Both artifacts must additionally carry the declared licence file as a
  non-empty regular member — `dist-info/licenses/LICENSE` in the wheel, the
  sdist root in the tarball — because a metadata header naming a licence file
  is a claim about a file, not the file.
- Changed: `Development Status :: 3 - Alpha` → `5 - Production/Stable`.
- **Renamed (breaking): `MutationNotAllowedError` → `KorailMutationNotAllowedError`.**
  It was the only one of the twenty exception types without the package's
  prefix, and the sibling SRT package already spells its counterpart
  `SrtMutationNotAllowedError`. No alias is left behind: an alias added at
  1.0.0 is itself a permanent contract, and the whole point of doing this now
  is that the rename is still free.

### Fixed

- Corrected: `docs/RELEASE_GAP_PLAN.md` still carried, in its srtgo-corrections
  appendix, the withdrawn claim that "Korail uses **no** NetFunnel at all — only
  SRT does". The body of that document has said otherwise since 2026-07-26; the
  appendix now agrees with it. The corresponding "not yet implemented" notes on
  the `service_1` / `act_6` gate in `README.md` and
  `docs/IMPLEMENTATION_PROGRESS.md` were also stale and are corrected: the gate
  exists, and what still holds R39 back is its unregistered route.
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
- Corrected the NetFunnel claim in `docs/RELEASE_GAP_PLAN.md`. Saying Korail
  "does NOT use NetFunnel at all" was too strong: the app does wire the round
  trips. What is true is that no Retrofit request body carries a token field and
  our live calls succeed without one.

### Removed

- Removed: the 여행변경 (trip change) mutation chain and the `ticket_change`
  consent category with it — `change_trip_reservation`,
  `rollback_trip_change` and `change_reservation_passengers`, plus
  `MutationConsent.allow_ticket_change`. Built and withdrawn the same day.
  Exercising the chain needs a PAID ticket, charges a 변경수수료, and has no
  clean undo, so there was no way to verify it without spending money on a
  path whose rollback half was itself unverified. The two READS the chain
  starts from survived and are listed below; the analysis is kept in
  `docs/RELEASE_GAP_PLAN.md`. **Breaking** for anyone who took the
  intermediate commit.
- Removed: the 비회원 오프라인 반환 pair and the non-member session with it —
  `verify_offline_refund_ticket`, `execute_offline_refund`,
  `begin_non_member`, `end_non_member` and `KorailNonMemberSession`. Also
  built and withdrawn the same day, for the same kind of reason: the pair's
  premise is a PHYSICAL paper ticket whose printed 반환번호 the verify call
  consumes, so neither half could be exercised at all. The 반환번호 spellings
  stay registered in `redaction.py` on purpose — `research.tripChgOgtk.do`
  still carries the same four-part number, and a spelling dropped from the
  sensitive-key set is one that leaks the day something re-introduces it.
  **Breaking** on the same terms.
- **Removed (breaking, and the last chance to do it): 47 names left the
  top-level `__all__`, which went 263 → 216.** Every one of them is still
  importable from the module that defines it — this is a move, not a deletion,
  and `from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS` works
  exactly as it did. What changed is what the package *promises*: after 1.0.0
  an exported name cannot be withdrawn without breaking somebody, so the
  surface now holds only what a caller genuinely has to be able to name — the
  client, config and session; every type reachable from a public method's
  annotations; the errors; the consent types; and the domain values a caller
  passes in or compares a response against. What left, by category:
  - Transport-layer constants: the base URL, app key, API version, device
    geometry and SDK int, the NetFunnel URL/path/service-id/timeout, the
    DynaPath header name and allowlist, the bootstrap code list. Every one of
    these is already reachable as the default of a `KorailConfig` field, which
    is where a caller who wants to change one has to go anyway.
  - The DynaPath token machinery: `generate_dynapath_token`,
    `generate_dynapath_encoding_table`, `build_dynapath_prefix`,
    `DynapathTokenGenerator`, `DynapathRequestContext` and the five
    `KORAIL_DYNAPATH_*` identity constants. `DynapathConfig` and
    `DynapathTokenSettings` stay: they are `KorailConfig` field types.
  - The internal route and policy tables: `KORAIL_MUTATION_ROUTES`,
    `KORAIL_NETFUNNEL_ROUTES`, `KORAIL_CARD_BEARING_MUTATION_CATEGORIES`,
    `EXCLUDED_API_DOMAINS`, `KORAIL_NETFUNNEL_GATED_OPERATIONS`. The mutation
    route table is the contentious one — it reads as safety disclosure — but
    its counterpart `KORAIL_READ_ONLY_ROUTES` was never exported, and half a
    classification published is worse than a whole one in `safety.py`, where
    both now sit together.
  - The parsers the client already calls for you: `parse_base_response`,
    `parse_reservation_hold_response`, `parse_reservation_payment_response`,
    `parse_discount_card_purchase_response`, and `pair_transfer_itineraries`.
    Their *return* types are all still exported, which is the half a caller
    annotates with.
  - `redact_mapping` and `redact_payload`. `MutationPreview` runs the payload
    through redaction on construction, so nothing is lost by default; a caller
    who wants them for their own logging imports them, and the four other
    helpers they were separated from, from `korail_mobile_api.redaction`.

### Security

- Security: `ogtkRetPwd` and the rest of the 원표 반환번호 tuple are now
  redacted. `ogtkRetPwd` travels three ways — as a bare `@Field` on
  `research.cmtrInfo.do`'s 원표 branch, which this package has emitted since
  `build_commuter_info_form` was added, as indexed `@FieldMap` keys, and back
  as `OrgTk.ogtkRetPwd` — and none was masked before. `ogtkSaleWctNo`/`ogtkSaleDd`/`ogtkSaleSqno`/
  `ogtkSaleDt` are registered with it, since masking three quarters of a
  반환번호 leaves it reconstructable; `_index_stripped` covers every row index.
  Also registered: the 지연증명 tuple `Cmpn.dlayOgtk*` (`Cmpn.java:11-14`), the
  settlement rows' `stlCrdNo`/`prepCrdNo`/`apvNo` (`Stl.java:5-16`), and
  `lumpStlTgtNo` under both spellings, which the 할인카드 구매 mutation
  already returns. `cmpnList`/`stlList` are deliberately left unparsed and
  stay masked inside `raw`.
- Changed: `hidDscpNo`, `hidCustNo`, `hidFmlyNo` and `psrm_cl_cd` join
  `SENSITIVE_KEYS`. The first is a coupon/국가유공자 certificate number — the
  same `h_cpn_no` already redacted inbound — on the way out; the other three
  are a customer number, a family-member sequence and the underscore spelling
  of the already-redacted `psrmClCd`.
- Changed: `redact_payload` redacts a list value ELEMENTWISE and preserves its
  length, instead of collapsing it with `str()`. A form key can legitimately
  carry many values now, and stringifying the list hid every element from
  `redact_text` behind the list's own quotes.
- Changed: `txtCardNo_1..N` joins `SENSITIVE_KEYS`. The inbound spellings were
  redacted already; the outbound form key was not, and a dry-run preview of a
  carded hold printed a spendable card number in the clear. Caught by a test
  written for exactly that.
  - Exactly two things differ from the live-verified one-adult 일반실 form:
    the eight passenger rows collapse to `txtTotPsgCnt="1"`,
    `txtCompaCnt1="1"`, `txtPsgTpCd1="1"`, `txtDiscKndCd1="153"`,
    `txtCardNo_1=<card>` (`w4/a.java:96-101`), and `txtMenuId` becomes `"A2"`
    (`SeatAssignBookingActivity.java:159`). Everything else — journey block,
    seat block, `txtJobId`, `txtStndFlg`, `hidFreeFlg`, `txtGdNo` — is
    identical, because the app writes it with the same code
    (`c5/b.java:42-77`). The builder is written as a substitution INTO
    `build_reservation_form`'s output so that is true by construction, and a
    test compares both forms key by key, in order.
  - **`txtCardNo_1` carries a trailing underscore and its three neighbours do
    not** (`OPsg.java:7-10`). A hold spelled `txtCardNo1` would be a hold with
    a discount code and no card.
  - No `passengers` and no `seat_class` argument: the app offers neither, since
    `w4/a.java:97-98` hardcodes one passenger and `:88` pins 일반실.
  - Gated by the existing `"reserve"` consent, because it IS the reserve route.
    **NEVER TRANSMITTED**: no account this project can reach owns an N카드.
- Changed: `redact_payload` now masks `txtCpNo` and the indexed
  `txtSrcarNo{i}`/`txtSeatNo{i}` keys, so a mutation preview cannot expose the
  standby notification number or the designated seats. Car and seat identifiers
  were already redacted everywhere they are read back; these are the same two
  values on the way out.

### 알려진 제약과 넣지 않은 것

- Not added, and deliberately so: 특실 업그레이드's `myTicket.reqUpgradeSeat`
  (`MyTicketService.java:23-24`). It was briefly implemented as a read on the
  strength of its request — no amount, no payment means, no confirmation flag
  — but its RESPONSE mints a `lumpStlTgtNo` (`SpecialRoomUpgradeDao.java:
  13,19`) and `procUpgrade` takes that same 일괄결제대상번호 beside `stlMnsCd`
  / `crdInpWayCd` / `ismtMnthNum` / `mnsStlAmt` (`MyTicketService.java:21`).
  Producing the settlement target a payment then spends creates an unpaid
  purchase; it does not price one. That is the same reading this repository
  already applied to `research.dcntCrdInfo.do` ("Despite the 'Info' in its
  path this is a PURCHASE"), which is why that route lives in
  `KORAIL_MUTATION_ROUTES`. It is not registered as a mutation either: its
  paired write `procUpgradeSeat` is an intended deferral, and half a purchase
  chain would let a caller create settlement targets with no supported way to
  settle or abandon them. `tests/test_ticket_change_chain_reads.py` pins both
  halves out of both allowlists.
- Not shipping: 정기권 구매. The purchase pair (`pass.passReserve` /
  `pass.passPayIssue`) was implemented in this same unreleased cycle and removed
  again before release, so no `reserve_commuter_pass`, `pay_for_commuter_pass`,
  `CommuterPass*` type, `KORAIL_COMMUTER_PASS_PAYMENT_FIELDS`, `commuter_pass`
  consent category or `MutationConsent.allow_commuter_pass` exists. Nothing was
  ever transmitted, and no released version ever carried them.
  - **Why: it cannot be proven correct without spending unrecoverable money.**
    A 1개월 정기권 is roughly ₩150,000–₩250,000, and this package has neither a
    refund route nor a cancel route for one — `cancel_unpaid_hold` is the ticket
    cancel.
  - **And there is no capture to compare against**, because the shipped app
    cannot issue `passPayIssue` either:
    `PaymentActivity.isCommPaymentRequest()` tests
    `getIPaymentRequest() instanceof CommPaymentDao.CommPaymentResponse` — a
    Response type where a Request is required (`PaymentActivity.java:502-503`,
    bytecode at `smali/…/PaymentActivity.smali:3963-3980`) — so the test is
    always false and the DAO never runs. A form assembled from decompiled code
    with no capture and no affordable live call is a guess with references.
  - **The 정기권 READS are unaffected**: `get_pass_menu`,
    `get_pass_available_dates` and `get_pass_schedule` are unchanged.
  - **The knowledge is kept, not lost.** README's 정기권 section records the
    twenty `passReserve` fields and the loop that fills them, the one-train
    shape (`hidChtrnStnCd`/`Nm` sent as EMPTY STRINGS, `hidTrnNo2`/
    `hidTrnGpCd2`/`hidDtour2` ABSENT), both `passPayIssue` `@FieldMap`s and why
    both are populated by v6.5.0, the `hidPayAmount` chain, the
    `isCommPaymentRequest()` bug, why `passOtrReserve`/`passOtrPayIssue` are a
    different product (자유이용권: 내일로 / A-PASS / 강릉패스), and what
    reviving the feature would cost to prove.
  - `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` **stays** a named set, now holding
    `{"payment"}` again. It was introduced as its own behaviour-preserving
    change because `category == "payment"` asked the wrong question, not
    because it had two members, and it still carries the tested invariant that
    no card-bearing category owns a GET mutation route.
  - Changed: `h_cust_nm`, `usernames`, `h_chg_mg_no` and their model attribute
    names (`customer_name`, `user_names`, `change_management_no`) leave
    `SENSITIVE_KEYS`. Every one of them entered it for the pass payment form,
    and no surviving response, form or model in this package carries any of
    them — `h_cust_nm` and `h_chg_mg_no` appear in exactly one DAO in the whole
    APK, `CommReservationDao`, which nothing here parses any more. The
    pre-existing `h_cust_no` / `customer_no` entries are untouched.
- Known gap: **`cancel_unpaid_hold` cannot release a transfer hold.** It requires
  `h_jrny_cnt` to be numerically one. The app has no such restriction —
  `DReservationConfirmActivity.java:269-278` forwards `getH_jrny_cnt()` verbatim
  as `txtJrnyCnt` beside the same fixed `txtJrnySqno="0001"`/`hidRsvChgNo="000"`
  — so the fix is to forward the hold's own count instead of pinning `"1"`. That
  touches the cancel path, which was out of scope for the transfer change, so it
  is reported rather than made. A live transfer hold sent before it lands must be
  cancelled in the KORAIL app or on the website.
- Neither `pay_with_card` nor `refund` has a live-verified success envelope. No
  run recorded in this repository has settled a real payment or returned money;
  the docs now say so instead of saying a real charge is impossible.
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
- Registered only the three statically evidenced exact read contracts; the
  separate state-changing crew-call route remains excluded.
- Added no live service/menu/train/car constants, seat selection, hold,
  reservation, payment, cancellation, or other mutation capability; the new
  contracts are covered by synthetic fixtures only.

### 검증 기록

- Documented: two live observations from 2026-07-26 that are server rules, not
  package defects. `ERR299943 예약할인이 지원되지 않습니다` refused 청소년 alone
  and 1~3급 장애 + 안내견 while six other mixes were accepted; the code has zero
  hits anywhere in the decompiled APK and the forms matched the app exactly, so
  it is an account-entitlement rule. Separately, a hold returned
  `h_msg_cd = WRR664296` (weekend discount notice) and was still a real,
  cancelable reservation — success is `strResult = SUCC` plus a PNR, not
  `h_msg_cd == IRR000018`, and no code path treats a non-`IRR000018` code as
  failure.
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
- Recorded a bounded authenticated read-only revalidation with an empty
  advertising ID. It made one successful login call, confirmed logged-in state
  and customer-number presence, and called only R149 once. R149 succeeded with
  one row and was not retried; R137, R138, R146, and R148 made zero calls. No
  mutation, raw response, PII, credential, or server message was retained.
  Current inventory is 32 successful, 10 failed, and 123 unexecuted out of
  165.
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
