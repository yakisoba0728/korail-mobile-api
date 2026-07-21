# KORAIL Mobile API — Release & Mutation Gap Plan

Status: planning document (no code changes, no live calls). Drives the
read-completion + full-mutation implementation.

- Target library: `korail-mobile-api` (`src/korail_mobile_api/`), currently `0.2.0`
  (`pyproject.toml:7`).
- Target app: `com.korail.talk` v6.5.0, API version `250601003`, host
  `https://smart.letskorail.com` (Retrofit 1.x over `HttpURLConnection`).
- Authoritative source: `docs/deep-dive/full-api-analysis-2026-07-20.md` (§ refs
  below are into that file), cross-checked against `docs/api-endpoints.md`,
  `docs/api-status-by-service.md`, decompiled `analysis/jadx/sources/…`.
  Corrections in this doc are reconciled against
  `docs/deep-dive/cross-validation-2026-07-21.md` (srtgo reference vs our
  decompiled v6.5.0 — see Revision 2).
- Scope decision (user): extend beyond read-only to full mutation — reservation
  creation, seat assignment, payment, refund, cancel/change, check-in. A later
  implementation phase authorizes live testing up to state changes using the
  gitignored `.env` credentials (the stored email login →
  `IRZ000001`); card payment tested with FAKE PANs (expected rejection); any test
  reservation must be auto-cancelled. Credentials never committed.

---

## 1. Current state

### 1.1 What the client is today

- **Read-only by construction.** Every outbound request passes through
  `assert_read_only_route()` (`safety.py:618-629`) and
  `assert_read_only_request_fields()` (`safety.py:632-699`), invoked
  unconditionally from `KorailHttpClient.post_form` (`http.py:149,169`) and
  `get_json` (`http.py:218,224`). A `(method, path)` outside
  `KORAIL_READ_ONLY_ROUTES` raises `KorailProtocolError`.
- **Route surface: 50 exact login/read routes** (`KORAIL_READ_ONLY_ROUTES`,
  `safety.py:22-108`; verified `len == 50`). **Field surface: 37 exact-field
  contracts** (`KORAIL_EXACT_REQUEST_FIELDS`, `safety.py:112-438`; `len == 37`),
  plus pinned field *orders* for 8 routes (`KORAIL_EXACT_REQUEST_FIELD_ORDERS`,
  `safety.py:441-526`) with bespoke repeated-field validators for `cmtrInfo.do`,
  `tk.pbpAcepSpec.do`, `tk.plfNo.do` (`safety.py:537-593`).
- **Public API: ~53 methods** on `KorailClient` (`client.py:190-1057`) covering
  login + reads across auth, cache, station, calendar, search, seat inventory,
  fare, reservation-history reads, tickets, pass, limousine, MaaS, delivery, and
  discount reads. Mapped 1:1 to the catalog in analysis §8.2 (`…:2610-2653`).
- **Crypto.** Login password wire cipher `base64_nowrap(base64_default(
  AES-CBC-PKCS5(pw, key=login.key, iv=key[:16])))` (`crypto.py:41-52`) — matches
  analysis §2.3 (`…:278`). `Sid` = `AndroidBase64(AES-CBC(SID_KEY, "AD"+ts))`
  (`crypto.py:55-62`).
- **DynaPath.** Full token engine (`dynapath.py`), header `x-dynapath-m-token`
  (`constants.py:34`), 6-path allowlist (`constants.py:35-44`). Default
  `DynapathConfig.enabled=False` (`dynapath.py:160`); reads force it off.
  **CORRECTION (2026-07-21, srtgo ref):** a working client
  (`srtgo_plus/srtgo/ktx.py:666-675`) sends `x-dynapath-m-token` on **all 6**
  protected paths **always** (no macro flag), and the token-generation algorithm
  is now fully known and reproducible (`DynaPathMasterEngine`, `ktx.py:54-160`:
  device fingerprint + ts + nonce → app secret `[38ff229cb34c7dda8e28220a2d750cce]`
  + 62-char custom alphabet + key-derived permutation → base161→base30 →
  `bEeEP…`). So "default OFF" is a policy knob, not a limitation — reproduction is
  **FEASIBLE**. See §5 item 10 and the 2026-07-21 revision.
  **QUALIFIED (2026-07-21, cross-validation vs our decompiled v6.5.0):** the
  algorithm *structure* is confirmed against our own code, but srtgo's SDK-version
  string `v1` is **stale** — our app uses `v1.0.3` (`C1229b.java:137,157`) in both
  the body `sv` field and the `dyn_key` prefix, and since that string reseeds the
  whole token, the version (and any per-version constants) MUST come from our app,
  not srtgo. srtgo's `v1` mints a self-consistent but **invalid** token if the
  server validates `sv`. See Revision 2.
- **Session.** `KorailSessionClient` (`session.py`) does service preflight →
  `common.code.do` crypto bootstrap → `login.Login`; auth is the `JSESSIONID`
  cookie held by the `httpx.Client` jar (`session.py:176-197`). Email/phone/
  member-no input-flag inference at `session.py:23-29`; success codes
  `{IRZ000001, S200}` at `session.py:17`.
- **Redaction.** Central `redact_text/redact_mapping/redact_value`
  (`redaction.py`) with a large `SENSITIVE_KEYS` set (`redaction.py:10-126`),
  card regex (`redaction.py:127`), session regex (`redaction.py:128`); wired into
  every error via `KorailApiError.__init__` (`errors.py:7-13`).

### 1.2 What mutation scaffolding already exists (and how far it goes)

Partial, offline-only, **not wired to any HTTP call**:

- **Models** (`mutation_models.py`, 58 lines): `ReservationJourney`,
  `ReservationHoldResponse` (captures `pnr_no`, `window_no`,
  `temporary_job_sequence_1/2`, `payment_flag`, `total_fare/price`, journeys —
  `mutation_models.py:26-38`), `ReservationPaymentCoupon`,
  `ReservationPaymentResponse` (`mutation_models.py:41-59`).
- **Parsers** (`mutation_parsers.py`, 231 lines): `parse_reservation_hold_response`
  (`:48-168`) and `parse_reservation_payment_response` (`:171-231`) — strict
  `SUCC`-envelope, nested `jrny_infos.jrny_info` / `tk_coupon_info` rows.
- **Payloads** (`mutation_payloads.py`, 195 lines): `build_single_adult_
  reservation_form` (`:45-166`) builds a flattened member `TicketReservation`
  body for a single adult on one leg (fixed passenger-row template,
  `txtSeatAttCd4` pinned to `015`); `build_unpaid_reservation_cancel_form`
  (`:169-195`) builds the cancel body from a fresh successful hold.
- **Exports** wired into public API (`__init__.py:84-93,305-323`).
- **Tests** exist for the two builders (`tests/test_mutation_payloads.py`) and the
  two parsers (`tests/test_mutation_response_parsers.py`).
- **DynaPath allowlist already includes** `certification.TicketReservation` and
  `nonMember.NonMemTicket` (`constants.py:37-38`) — token support is pre-staged.

**Coverage of the scaffolding:** reservation *hold* (member, 1 adult, 1 leg) +
*unpaid cancel* form/parsers only. No payment builder, no seat-assign, no
change/refund/check-in, no route wiring, no state machine, no NetFunnel, no
per-call gate. Confirmed by analysis §8.5 items 3–4 (`…:2807-2818`).

**Inventory today:** 165 Retrofit method entries / 159 distinct HTTP+path pairs
(`docs/api-endpoints.md:7`); live status 32 success / 10 fail / 123 unexecuted
(`docs/api-status-by-service.md:9-14`).

---

## 2. Read-only gaps (read-surface endpoints not yet implemented)

These are **read/lookup** endpoints (no operational state change) present in the
catalog but absent from `KORAIL_READ_ONLY_ROUTES` and `KorailClient`. Source =
analysis §8.4 (`…:2708-2790`) + `docs/api-endpoints.md`.

| # | Route | Method | Purpose | Decompiled ref | Why unimplemented |
|--|--|--|--|--|--|
| G1 | `seatMovie.ScheduleViewSpecial` | POST | Tour/product seat-availability search (관광열차) | `SeatMovieService.java:20`; analysis §3.3 | **Payload+parser already scaffolded** (`read_payloads.py:1059+`, `read_models.py:848` `ProductTrainInquiryResponse`) and path is in DynaPath allowlist (`constants.py:40`) but there is **no route entry and no client method** — dead/partial coverage (analysis §8.5.2, `…:2800`). NetFunnel `act_6` gates it (analysis §3.16.3, `…:1325`). |
| G2 | `research.dcntCrdScheduleView.do` | GET | N-card (할인카드) schedule view | `ResearchService.java:54` | N-card read family not ported |
| G3 | `ticket.dcntCrdUseQry.do` | GET | N-card usage history | `ResearchService.java:51` | Not ported |
| G4 | `research.tripChgOgtk.do` | POST | Original-ticket inquiry — **prerequisite read** for the 승차권 변경 chain | `ResearchService.java:61`; analysis §3.6 boundary (`…:687`) | Change-flow read not ported (needed before `tripChgPrsC`) |
| G5 | `trainsInfo.TourTrainSpecialRoom` | POST | Tour-train special-room info | `TrainsInfoService.java:36` | Not ported |
| G6 | `self.seatChgInfo.do` | POST | Self seat-change info (options/stations) | `TicketService.java:54` | Read; not ported |
| G7 | `myTicket.reqUpgradeSeat` | GET | Seat/special-room upgrade **quote** | `MyTicketService.java:23`; analysis §3.8 (`…:814`) | Read (quote), but carries `ogtkRetPwd` in query — port with redaction; `procUpgrade` is the paired write |
| G8 | `maas.cncFee.do` | POST | MaaS cancel-**fee quote** (feeds `coptCnc`) | `TicketService.java:46`; analysis §3.8 (`…:833`) | Cancel-flow read; prerequisite for MaaS cancel |
| G9 | `product.payInfo` | GET | Product reservation pay-info / lump-settlement target | `ProductService.java:18`; analysis §3.7.1 (`…:755`) | Pay-info read; prerequisite for product settlement |
| G10 | `gift.gdUseSpec.do` | POST | Gift-ticket usage history | `GifticketService.java:21` | Read; not ported (list `gdLst` is implemented) |
| G11 | `login.Logout` | GET | Server-side session invalidation | `LoginService.java:29`; analysis §8.5.1 (`…:2794`) | `client.logout()` only clears the local cookie jar (`client.py:222-223`); server session never invalidated. Borderline (idempotent session op) — treat as a **read/session** completion. |
| G12 | `certification.ReservationList` (`inquiryTicketRsv`) | GET | Single-reservation detail by `hidPnrNo` | `CertificationService.java:45`; analysis §3.5 (`…:626`) | Read overload of a path also used for a disability-cert write; port the read overload only |

Optional/excluded-domain reads (list for completeness, gate behind their domain
opt-in): `checkin.info.do` / `checkin.psbFlg.do` (check-in status/possibility —
reads inside the excluded check-in domain, analysis §3.8 `…:822,825`);
`xPoint.MyXPointView` / `xPoint.XPointView` / `mlg.amtSpec.do` (point balance
reads inside `points-mileage`, analysis §8.4 `…:2784`); `railplus.autoCharge.do`
(eligibility read, `…:2787`). `nFilter.createKey.do` and
`common.encrypt/decrypt/shinhan.Encrypt` are payment-crypto prep, folded into the
Payment flow (§3.C).

**Read-only gap count: 12 core read endpoints (G1–G12)**, plus ~7 domain-gated
optional reads.

---

## 3. Mutation additions (the write surface to add)

Full write catalog is ~60 endpoints; the **core mutation scope for v1**
(user-requested flows) is **27 endpoints across 5 flows**. Everything shares the
uniform transport (analysis §3.5–3.9): `@FormUrlEncoded` POST (GET where noted),
`Device=AD`/`Version=250601003`/`Key=korail1234567890`, TLS-only, no signing,
auth = `JSESSIONID` cookie; no body encryption/HMAC.

### Cross-cutting prerequisites (apply to every mutation flow)

- **Session / JSESSIONID.** All member mutations require a live login cookie
  (`session.py:176-197`). Non-member booking/refund uses name+phone+password
  instead of a cookie (analysis §3.5 `…:624`, §3.9 `…:868`).
- **NetFunnel virtual-waiting-room act keys** (analysis §1.9 `…:150`, §7.7
  `…:2508-2534`; host `nf.letskorail.com:443`, `serviceID=service_1`, opcodes
  `5101`/`5002`/`5003`/`SET_COMPLETE`, `T6/d.java:21-113`):
  - **⚠ CORRECTION (2026-07-21, srtgo ref) — Korail does NOT use NetFunnel at
    all; only SRT does.** A working client
    (`srtgo_plus/srtgo/ktx.py`) instantiates `NetFunnelHelper`
    (`ktx.py:640`) but **never calls `.run()`** on the Korail path, and sends **no
    `netfunnelKey`** in either the reserve body (`ktx.py:864-904`) or the pay body
    (`ktx.py:1030-1051`). Its NetFunnel helper only knows `sid="service_1",
    aid="act_8"` — there is **no `act_18` payment gate and no `act_14`/`act_6`
    gate** in it (`ktx.py:601-608`); `.run()` is only wired on the *SRT* side
    (`srt.py`, `netfunnelKey`). Korail reservation **and** payment succeed
    **without any queue token**. The `act_18`/`act_6` gates below were inferred
    from the decompiled *app*; the live-tool evidence says the Korail server
    accepts reserve/pay with no NetFunnel round-trip. **Downgrade this from a top
    risk / new subsystem to: NetFunnel client is NOT required for Korail
    reserve/pay/refund** (confirm on the single authorized live pass; keep only if
    a live call actually returns a queue-required error).
  - `act_8` booking/simple-purchase (default), `act_8_2` peak-season booking.
  - ~~**`act_18` gates the real pay calls**~~ (`ReservationPayment`, `intgStl`,
    `passPayIssue`, `passOtrPayIssue`) — `K4/g.java:45`, wired at
    `B6/AbstractC1269e.java:1046`, `B6/C1270f.java:232` (analysis §3.7 `…:724`).
    **Superseded:** not sent by the working client (see correction above); the pay
    POST carries no queue token (`ktx.py:1030-1051`).
  - `act_6` gates `ScheduleViewSpecial` tour-train inquiry (analysis §3.16.3
    `…:1325`) — needed for G1 (still app-inferred; not exercised by srtgo, which
    does not implement tour search).
  - `act_22` (refund) is **defined but unwired** in v6.5.0 (`K4/g.java:47`,
    analysis §3.9 `…:881`) → refund needs **no** NetFunnel gate.
  - Cancel/change/check-in domains attach **no** NetFunnel gate (analysis §3.6
    `…:707`, §3.8 `…:805`).
  - Revised implication: a NetFunnel client is **not** on the critical path for
    Korail reserve/pay/refund/cancel (the working reference does not use one). If
    G1 tour-search (`ScheduleViewSpecial`, `act_6`) is ever wired it may still need
    a gate, but that is optional/deferred, **not** the "single biggest new
    subsystem" this plan originally claimed. §39 R39
    (`docs/IMPLEMENTATION_PROGRESS.md:153`) hold-back on `service_1`/`act_6` no
    longer blocks the core reserve/pay flows.
- **DynaPath `x-dynapath-m-token` allowlist** (`constants.py:35-44`; analysis
  §3.5 `…:639`): only 6 paths accept the token — `TicketReservation`,
  `NonMemTicket`, `ScheduleView`, `ScheduleViewSpecial`, `trn.prcFare.do`,
  `login.Login`. In-app `IS_MACRO_ACTIVE=false` so the token is normally NOT
  sent; **decision required** — a headless client should default to NOT sending
  it (match app default) and expose an opt-in. No cancel/payment/refund/check-in
  path is in the allowlist.
  **UPDATE (2026-07-21, srtgo ref):** the same 6-path allowlist is confirmed
  (`srtgo_plus/srtgo/ktx.py:44-51`), but the working client sends the token on
  **all 6 paths always** (login/search/reserve), with no macro flag
  (`ktx.py:666-675`) — because it treats the token as required by current Korail
  anti-bot policy. The generation algorithm is reproducible (`ktx.py:54-160`), so
  the opt-in is implementable today. Keep the default OFF (safe), but plan to flip
  it on for live reserve if a token-less call is rejected.
  **CROSS-VALIDATION (2026-07-21):** the 6-path allowlist AND the
  `IS_MACRO_ACTIVE` gate are now confirmed against our decompiled code —
  `com/korail/talk/network/ExecuteDao.java:26-47` wraps the token in
  `if (a.IS_MACRO_ACTIVE)` over the exact 6 paths; the flag defaults `false` and
  flips only on server `isMacroEnable=='Y'`. So our app is **stricter** than srtgo
  (which attaches unconditionally). Reproducibility is confirmed in *structure*
  only — the SDK-version string must be our `v1.0.3`, not srtgo's stale `v1`
  (see Revision 2).
- **`Sid` token** (`crypto.py:55-62`): required by search (`ScheduleView`),
  car/seat research (`TrainResearch`, `TResidualSeatsResearch.do`) — the reads
  that *precede* a booking. The reservation POST itself carries no `Sid`.
- **Common-code prerequisites.** Login crypto (`app.login.cphd`) via
  `common.code.do` (`session.py:79-99`); the passenger/discount code tables
  (`psgTpDvCd`, `dcntKndCd`, seat-attribute codes) come from `common.code.do`
  and the search response — needed to build passenger/discount `@FieldMap`s.
- **Password AES / double-Base64** (`crypto.py:41-52`, analysis §2.3): reused for
  login; the **amount-tamper guard** `encTotTxnAmt` on `spayOrdNo` uses the same
  `AES-CBC(loginKey, iv=key[:16])` then default-Base64 (analysis §3.7.3 `…:780`,
  `S4/C0812l.java:18-41`) — a payment-only reuse of the same primitive.

### 3.A Flow A — Reservation / booking / seat-assign / change

State machine: `search (ScheduleView, act_8/Sid/DynaPath) → [car/seat research]
→ hold (TicketReservation|NonMemTicket) → pay (Flow C, act_18) → confirm`.
Unpaid hold auto-expires; cancel via Flow B.

| Route | Method | Key request params | Response model | Source |
|--|--|--|--|--|
| `certification.TicketReservation` (member hold) | POST | `pnrNo`(""), `txtMenuId`, `txtJobId`∈{1101,1102,1202}, `txtGdNo`, `hidFreeFlg`, `txtStndFlg`, `pbepInfo`; `@FieldMap×4` = legacy `OPsg`/`OSeat`/`OJrny`/`OSrcar` (`txt*` keys) | `ReservationResponse` → map to `ReservationHoldResponse` (`h_pnr_no`, `h_wct_no`, `h_tmp_job_sqno1/2`, `h_rsv_chg_no`, `h_payment_flg`, `h_tot_fare/prc`, `h_ntisu_lmt*`) | `CertificationService.java:52`; DAO `ReservationDao.java:12-18`; models analysis §4.5 (`…:1702-1746`) |
| `nonMember.NonMemTicket` (non-member hold) | POST | as above **+** `txtCustNm`, `txtCpNo`, `txtCustPw` (plaintext); no login cookie | `ReservationResponse` | `CertificationService.java:48`; analysis §3.5 (`…:624`) |
| `reservation.seatAssign.do` (seat assignment / upgrade booking) | POST | `menuId`∈{A1,A2}, `custMgNo`, `totPrnb`, `stndFlg`, `rqScarNum`; `@FieldMap×5` = new `RJrny`/`RSrcar`/`RSeat`/`RPsg`/`ROrtg` (`x_i`/`x_i_j` keys) | `SeatAssignReservationResponse` (empty subclass of `ReservationResponse`) | `ReservationService.java:28`; analysis §4.5 (`…:1750`) |
| `reservation.reservationChange.do` (예약변경) | POST | `pnrNo`, `chgTno`(=`h_rsv_chg_no`), `totPrnb`, `stndFlg`/`evntWctFlg`/`wctHndgCncDvCd`/`lrgCrgFlg`("N"), `psgCnt`; `@FieldMap×5` = `RJrny`/`RSrcar`/`RSeat`/`RPsg`/`RDscp` | `ReservationChangeResponse{jrnyList:[{lumpStlTgtNo}]}` | `ReservationCancelService.java:23`; analysis §3.6 (`…:674`), §4.6 (`…:1821-1843`) |
| `reservation.tripChgPrsC.do` (변경 예약 생성) | POST | `trvlKndCd`, `totPrnb`, `isePrnb`, `stndSeatFlg`, `intgTktIseFlg`, `prcFareReCalcFlg`, `tmpJobSqno`, `alcSeatDmnPsDvCd`, `jrny2Cnt`, `psg2Cnt`, `ctlDvCd`, `frcSaleRsnCont`; `@FieldMap×6` = `RJrny`/`RSrcar`/`RSeat`/`RPsg`/`ROrtg`/`RDscp` | `ReservationResponse` | `ReservationService.java:24`; analysis §3.6 (`…:686`) |
| `reservationWait.ReservationWait` (예약대기 등록) | POST | `txtPnrNo`, `txtPsrmClChgFlg`, `txtSmsSndFlg`, `txtCpNo` | `BaseResponse` | `ReservationWaitService.java:10` |
| `research.tripChgOgtk.do` (원권 조회 — prereq READ, see G4) | POST | `tkCnt:int`; `@FieldMap` original-ticket block | `OgTkInquiryResponse` | `ResearchService.java:61` |

FieldMap key catalog (build these carriers exactly): new-style `R*` keys at
analysis §4.5 (`…:1780-1787`) and §4.6 (`…:1856-1868`); legacy `O*` keys at §4.5
(`…:1795-1801`). Overload selection is client-side: `NonMemTicket` when both
`custNm`+`cpNo` set, else `TicketReservation` (analysis §3.5 `…:637`).

> **CORRECTION (2026-07-21, srtgo ref) — the working reserve body is simpler than
> the row above claims.** `srtgo_plus/srtgo/ktx.py:864-904` (fork) / `srtgo/srtgo/
> ktx.py:715-755` (orig) build a member `TicketReservation` hold that **omits
> `pnrNo` and `pbepInfo` entirely** and still succeeds. It uses the **legacy
> `txt*` passenger rows** (`txtPsgTpCd{i}`/`txtDiscKndCd{i}`/`txtCompaCnt{i}`,
> `ktx.py:906-907`) with `txtJobId="1101"` (seat) / `"1102"` (waitlist)
> (`ktx.py:869`) — no new-style `R*` (`x_i`) carrier at all. Seats are
> auto-assigned via `txtSrcarCnt="0"` (`ktx.py:879`); **designated-seat keys
> (`txtSrcarNo{i}`/`txtSeatNo{i}`) are NOT supported by srtgo** — that remains a
> genuine gap for us (see §5 items 3–4). So drop `pnrNo`/`pbepInfo` from the
> must-send set for a fresh member hold (verify on the live pass), but keep the
> designated-seat carrier as unresolved.

### 3.B Flow B — Cancel / change-rollback (unpaid)

**Two-step, ORDER MATTERS** (app-inferred): `ReservationCancel` (step 1, initiate)
→ `ReservationCancelChk` (step 2, confirm/complete). They take identical params
and both return `BaseResponse`; the ordering is verified in
`DReservationConfirmActivity.onReceive` (analysis §3.6 `…:699`).

> **CORRECTION (2026-07-21, srtgo ref) — the working client cancels with a SINGLE
> call.** `srtgo_plus/srtgo/ktx.py:1060-1075` posts **only**
> `reservationCancel.ReservationCancelChk` (step 1 `ReservationCancel` is
> **skipped**) with `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` — and
> those are read from the reservation response, not hardcoded (fallbacks
> `txtJrnySqno="001"`, `txtJrnyCnt="01"`, `hidRsvChgNo="00000"`, `ktx.py:315-317`
> — note the digit widths differ from the `"0001"`/`"000"` constants below). Treat
> the single-call path as the primary; verify whether the app's step-1 is
> actually required on the live pass.
> **CROSS-VALIDATION (2026-07-21):** verified against our code —
> `ReservationCancelChk` is the **COMMIT** step (not an eligibility pre-check); our
> step-1 `ReservationCancel` is an *initiate*, so srtgo's single call is
> functionally sufficient (`a6/x.java:190-207`; cross-val §4).

| Route | Method | Key params | Response | Source |
|--|--|--|--|--|
| `reservationCancel.ReservationCancel` | POST | `txtPnrNo`, `txtJrnySqno`("0001"), `txtJrnyCnt`, `hidRsvChgNo`("000") | `BaseResponse` | `ReservationCancelService.java:15`; analysis §4.6 (`…:1809`) |
| `reservationCancel.ReservationCancelChk` | POST | identical to above | `BaseResponse` | `ReservationCancelService.java:19` |
| `ticket.tripChgHndgCnc.do` (change-hold rollback) | POST | `lumpStlCnt`("1"); `@FieldMap` `lumpStlTgtNo_1..N` (from `jrny_info[0].lumpStlTgtNo`) | `BaseResponse` (fire-and-forget) | `TicketService.java:98`; analysis §3.6 (`…:706`) |
| `product.ReservationCancel` (여행상품 취소 — name-collision) | **GET** | `txtVrRsNo`, `txtGdSqno` | `BaseResponse` | `ProductService.java:21`; analysis §3.6 (`…:693`) |

Multi-leg / already-changed reservations pass `txtJrnySqno`/`hidRsvChgNo` as
variables, not the `"0001"`/`"000"` constants (analysis §3.6 `…:700`).

### 3.C Flow C — Payment (~~act_18 gated~~ NO NetFunnel gate for Korail)

State machine: `hold (Flow A) → [PG prep: encrypt card / order-no] →
ReservationPayment (or intgStl) w/ PaymentMethod map → [cashReceipt auto-fire] →
confirm coupons`.

> **CORRECTION (2026-07-21, srtgo ref).** The working client pays with a **single
> `payment.ReservationPayment` POST and NO NetFunnel/`act_18` token**
> (`srtgo_plus/srtgo/ktx.py:1017-1058`). It also sends the **raw PAN in the clear**
> — `hidStlCrCrdNo1` carries the plaintext card number with **no client-side
> encryption** and no `shinhan.Encrypt.do`/`common.encrypt.do` prep
> (`ktx.py:1044`). Confirmed card/control fields (`ktx.py:1030-1051`):
> `hidStlCrCrdNo1`/`hidVanPwd1`/`hidCrdVlidTrm1`/`hidAthnVal1`/`hidAthnDvCd1`/
> `hidIsmtMnthNum1` + `hidStlMnsCd1="02"` (card) / `hidCrdInpWayCd1="@"` /
> `hidStlMnsSqno1="1"` / `hidInrecmnsGridcnt="1"` / `hidMnsStlAmt1` (amount) /
> `hidPnrNo` / `hidWctNo` / `hidTmpJobSqno1/2` / `hidRsvChgNo` / `hiduserYn="Y"`.
> Because the PAN goes over the wire raw, **redaction of these keys is essential**
> (§4.6) and the fake-card / dry-run / never-persist / auto-cancel guards are
> **mandatory** (§4.4). The `encValue`-only assumption in the PG note below is a
> divergence from live behavior — see the annotated correction there.
> **CROSS-VALIDATION (2026-07-21):** all six card field names + the raw-PAN
> (no client cipher) behavior are now **verified against our decompiled code** —
> `PaymentMethod.java:14-19`, `v4/a.java:29-34` (cross-val §3 ✅), not just srtgo.

| Route | Method | Key params | Response | Source |
|--|--|--|--|--|
| `payment.ReservationPayment` (main pay) | POST | `hidPnrNo`, `hidWctNo`, `hidTmpJobSqno1`, `hidTmpJobSqno2`, `hidRsvChgNo`; `@FieldMap` `PaymentMethod` | `RsvPaymentResponse{h_im_flg, tk_coupon_info[]}` → `ReservationPaymentResponse` | `PaymentService.java:12`; analysis §3.7.1 (`…:732`) |
| `pay.intgStl.do` (cart/integrated settlement) | POST | `ctlDvCd`("3584"/"3582"), `stlPrsJobId`("0001"), `cart_LumpStlTgtNo`(`;`-joined); `@FieldMap` `PaymentMethod` | `BaseResponse` | `PayService.java:38`; analysis §3.7.1 (`…:733`) |
| `pass.passPayIssue` (정기권 결제) | POST | `hidPayAmount`; `@FieldMap` commPaymentMap + `PaymentMethod` | `CommPaymentResponse{main_info.h_pnr_no}` | `PassService.java:19` |
| `pass.passOtrPayIssue` (패스 결제) | POST | `hidPayAmount`, `h_rcvd_prc`, `hidWctNo`; `@FieldMap` passPaymentMap + `PaymentMethod` | `PassPaymentResponse{main_info.h_pnr_no}` | `PassService.java:39` |
| `common.encrypt.do` (card value encrypt) | POST | `type`, `values[]` | `EncryptResponse{encValueList[].encValue}` | `CommonService.java:38`; analysis §3.7.1 (`…:748`) |
| `common.decrypt.do` | POST | `type`, `values[]` | `DecryptResponse` | `CommonService.java:34` |
| `shinhan.Encrypt.do` (SEED card encrypt) | POST | `value[]` (**singular field name**) | `SeedEncryptResponse{encValueList[]}` | `CommonService.java:60`; analysis §3.7.3 (`…:789`) |
| `nFilter.createKey.do` (secure-keypad pubkey) | POST | BaseRequest only | `NFilterCreateKeyResponse{publicKey}` | `NFilterService.java:10` |
| `pay.spayOrdNo.do` (easy-pay order no) | POST | `spayDvCd`, `totTxnAmt`, `tgtCnt`, `encTotTxnAmt` (amount-tamper guard), `idx`, `lumpStlTgtNo[]` | `SpayOdrNoResponse{spayTid, prprNo, fllwScnAppUrlAdr}` | `PayService.java:34`; analysis §3.7.3 (`…:780`) |
| `cashReceipt.issue.do` (auto-fired post-pay) | POST | `cashRcetTxnDvCd`, `vltIsuFlg`("Y"/"N"), `cashRcetAthnMtdCd`, `athnDmnRcgnNo`, `apvCnt:int`; `@FieldMap` `lumpStlTgtNo_1..N` | `BaseResponse` | `CashReceipt.java:12`; analysis §3.7.3 (`…:786`) |

**`PaymentMethod` settlement body** (`@FieldMap`, `v4/a.java:21-345`, analysis
§3.7.2 `…:762-775`): row control `hidInrecmnsGridcnt`/`hidStlMnsSqno{n}`/
`hidStlMnsCd{n}`/`hidMnsStlAmt{n}`/`hidCrdInpWayCd{n}`; **card**
`hidStlCrCrdNo{n}`/`hidVanPwd{n}`/`hidCrdVlidTrm{n}`/`hidIsmtMnthNum{n}`/
`hidAthnDvCd{n}`/`hidAthnVal{n}` (+ Shinhan `shStlCrCrdNo{n}`/`shCrdVlidTrm{n}`);
point `hidPontDvCd{n}`/`hidPontInpDvCd{n}`/`hidPontCrdPwd{n}`; member
`hiduserYn`/`hidMbCrdNo`; easy-pay `spayDvCd_1_1`/`spayCphdDatVal_1_1`. Settlement
codes `hidStlMnsCd`: `02`=card, `03`=deferred, `12`=point, `13`=RailPlus,
`14`=account. The **fake-card test path** targets card settlement (`02`) with an
obviously-invalid PAN → server rejection, never a charge (see §4.4).

**PG note.** ~~Card PANs/passwords are encrypted **server-side** via
`shinhan.Encrypt.do`/`common.encrypt.do` before entering `PaymentMethod`
(analysis §3.7.3 `…:781`); the client never sends a raw PAN to the pay call — it
sends `encValue`.~~ **CORRECTION (2026-07-21, srtgo ref):** the working client
sends the **raw PAN** directly in `hidStlCrCrdNo1` with **no encrypt step**
(`srtgo_plus/srtgo/ktx.py:1044`) — the `encValue`-only assumption is not what the
live tool does. This makes it a real charge over the wire, which is exactly why
our safety model keeps fake-card-only + never-persist (§4.4). (Our own client may
still choose the encrypt path defensively, but the wire fields are confirmed raw.)
Easy-pay methods (`spayDvCd` catalog `…:775`) require a PG
WebView redirect (`getPaycoResult`, `tossautoC`) which is out of scope for a
headless library and must be explicitly unsupported.

### 3.D Flow D — Refund (no NetFunnel gate)

Two sub-flows (analysis §3.9 `…:874`):
- **Online (member):** `SelTicketInfo` (detail) → `CommissionView` (fee/
  refundable preview) → `RefundsRequest` (execute; sends GPS `latitude`/
  `longitude`).
- **Offline (paper, no login):** `verifyOnlineRefunds` → `executeOnlineRefunds`.

| Route | Method | Key params | Response | Source |
|--|--|--|--|--|
| `refunds.SelTicketInfo` | POST | `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_purchase_history` | `TicketDetailResponse` (~55 fields) | `RefundService.java:23` |
| `refunds.CommissionView` | POST | + `h_comp_nm`, `h_comp_cert_no` | `RefundCommissionResponse{ret_amt, ret_fee, prg_psb_flg,…}` | `RefundService.java:19` |
| `refunds.RefundsRequest` (execute) | POST | `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_sale_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_mlg_stl`, `tk_ret_tms_dv_cd`, `trnNo`, `pbpAcepTgtFlg`, `latitude`, `longitude` | `RefundResponse{stlList[{stl_mns_cd}]}` | `RefundService.java:27`; wire quirk §5 |
| `refunds.verifyOnlineRefunds` | POST | `retNo1..4`, `strName` | `RefundVerifyTicketResponse{ret_amt, ret_fee, rcvd_amt,…}` | `RefundService.java:31` |
| `refunds.executeOnlineRefunds` | POST | `pnrNo`, `tkKndCd`, `retDvCd`, `retRsnCd`, `ogtkSaleDt`, `ogtkSaleWctNo`, `ogtkSaleSqno`, `ogtkRetPwd`, `retAmt`, `retFee`, `custTeln`, `acepCustNm` | `RefundExecuteTicketRefundResponse{h_ret_dv_cd}` | `RefundService.java:15` |

> **CORRECTION (2026-07-21, srtgo ref).** The working client refunds with a
> **single `refunds.RefundsRequest` POST** — no `SelTicketInfo`/`CommissionView`
> preview in the refund call itself (`srtgo_plus/srtgo/ktx.py:1077-1097`).
> **Confirmed** the wire-rename `h_orgtk_sale_wct_no` (stored as wct_no, sent as
> `h_orgtk_sale_wct_no`, `ktx.py:1084`) and empty GPS `latitude`/`longitude`,
> `tk_ret_tms_dv_cd="21"`, `pbpAcepTgtFlg="N"`, `h_mlg_stl="N"` (`ktx.py:1078-1093`).
> **✅ RESOLVED (2026-07-21, cross-validation):** the `txtPrnNo` trap is closed —
> srtgo's `txtPrnNo` (P-**r**-n) is a **typo**. Our v6.5.0 uses `txtPnrNo` (P-n-r)
> in refund (`RefundService.java:29`, `RefundDao.java:24/69/113`,
> `ticketReturn/a.java:411`), and a tree-wide grep proves **`txtPrnNo` occurs ZERO
> times** anywhere in our sources (cross-val §4). Lock the refund contract on
> `txtPnrNo`; no live check needed for the field name.

### 3.E Flow E — Check-in (self)

State machine: `possible (psbFlg, QR) → register (reg) → [info] → cancel (cnc)`.
Excluded domain today (`EXCLUDED_API_DOMAINS`); no NetFunnel gate. **Note
(2026-07-21, srtgo ref):** srtgo/srtgo_plus does **not** implement check-in — no
reference data to confirm these shapes; remains a genuine gap (fixtures/dry-run
only).

| Route | Method | Key params | Response | Source |
|--|--|--|--|--|
| `checkin.psbFlg.do` (possibility, QR scan) | POST | `qrcode`, `saleWctNo`, **`saleDd`**, `saleSqno`, `tkRetPwd`, `jrnySqno` | `SelfCheckinPossibleResponse{consList[…]}` | `TicketService.java:90`; analysis §3.8 (`…:822`) |
| `checkin.reg.do` (register) | POST | `cpsNo`, `scarNo`, `seatNo`, `saleWctNo`, **`saleDd`**, `saleSqno`, `tkRetPwd`, `jrnySqno` | `BaseResponse` | `TicketService.java:94` |
| `checkin.info.do` (status — READ) | POST | `saleWctNo`, **`saleDt`**, `saleSqno`, `tkRetPwd`, `jrnySqno` | `SelfCheckinInfoResponse` (24 fields) | `TicketService.java:86` |
| `checkin.cnc.do` (cancel) | POST | `saleWctNo`, **`saleDt`**, `saleSqno`, `tkRetPwd`, `jrnySqno` | `BaseResponse` | `TicketService.java:82` |

**Trap:** `psbFlg`/`reg` use `saleDd`; `info`/`cnc` use `saleDt` — two distinct
request classes both named `SelfCheckinPossibleRequest` (analysis §3.8 `…:843`).
Field allowlist must encode this per-route difference exactly.

### Out of core v1 (documented, deferred)

MaaS add-service cancel (`addService.cancelPay.do` [double-slash bug],
`addService.coptCnc.do`, `maas.cncFee.do`), gift send/reserve
(`giftInfo.GiftSend`, `gift.gdRsv.do`, `gift.gdRet.do`), delay/compensate refunds
(11 endpoints, analysis §3.10), mileage/points writes (9, `points-mileage`),
member-drop (`login.mbSced.do`), account link/unlink, upgrade `procUpgrade`,
easy-pay PG WebView redirects, N-card writes. Keep in `EXCLUDED_API_DOMAINS`
until explicitly scoped.

**Core mutation endpoint count: 27** (A:7, B:4, C:10, D:5, E:4 — with G4/info
double-counted as read prereqs). Full remaining write catalog ≈30 more.

---

## 4. Safety-model redesign

Adding mutation invalidates the "everything is in a read-only whitelist"
premise. The redesign keeps the allowlist architecture but makes it
**tier-aware** and adds explicit consent gating. Concrete changes:

### 4.1 Route tiers replace the single read whitelist

- Keep `KORAIL_READ_ONLY_ROUTES` unchanged (50 routes).
- Add `KORAIL_MUTATION_ROUTES: frozenset[tuple[str,str]]` (the §3 routes) and
  `KORAIL_EXACT_MUTATION_FIELDS` / `..._FIELD_ORDERS` mirroring the read contracts
  (`safety.py:112-526`), including the check-in `saleDd`/`saleDt` split and the
  `PaymentMethod`/`R*`/`O*` repeated-field validators.
- Rename `assert_read_only_route` → `assert_allowed_route(method, path, *,
  allow_mutation: bool)` (`safety.py:618`). Logic: route must be in the read set;
  **or** in the mutation set **and** `allow_mutation is True`; else
  `KorailProtocolError`. `assert_read_only_request_fields` gains the mutation
  field maps.
- `http.post_form`/`get_json` (`http.py:138-254`) take `allow_mutation: bool =
  False` and only pass it through when the caller is a mutation method. Reads are
  unchanged and can never flip the flag.

### 4.2 Make `EXCLUDED_API_DOMAINS` real (it is currently inert)

Today `EXCLUDED_API_DOMAINS` (`safety.py:9-20`) is only defined and re-exported
(`__init__.py:181,317`) — **no enforcement path references it** (verified by
grep). Redesign:
- Every mutation route is tagged with a domain
  (`reservation`/`payment`/`refund`/`check-in`/…).
- A route in an excluded domain is rejected **even if** in
  `KORAIL_MUTATION_ROUTES`, unless that domain is explicitly enabled on the
  config. Default: all mutation domains excluded → the library is read-only out
  of the box exactly as today.

### 4.3 Explicit opt-in + per-call confirmation gate

- `KorailConfig` gains `mutations: MutationPolicy` (default all-off):
  `enabled_domains: frozenset[str] = frozenset()`, `dry_run: bool = True`,
  `require_confirm_token: bool = True`, `allow_dynapath_token: bool = False`.
- Each mutation method requires an explicit `confirm=ConfirmToken(...)` argument
  (a typed sentinel the caller must construct — not a bare bool) naming the
  route + PNR/target; missing/mismatched token raises before any I/O. Prevents
  accidental writes from generic call sites.
- **Dry-run mode** (default `True`): the mutation method builds + validates the
  form, runs the field allowlist, and returns a `PreparedRequest`
  (method/path/redacted body) **without sending**. Live send requires
  `dry_run=False` on the policy AND the confirm token AND the domain enabled AND
  `KORAIL_MOBILE_API_LIVE=1` (`live.py:17`).

### 4.4 Fake-card payment path that can never charge

> **REINFORCED (2026-07-21, srtgo ref).** The reference proves payment **really
> charges**: the working client sends the **raw PAN over the wire with no
> encryption** to `payment.ReservationPayment` (`srtgo_plus/srtgo/ktx.py:1044`),
> and the server accepts it with no NetFunnel gate. There is no client-side crypto
> barrier protecting against a real charge. Therefore the guards below —
> **fake-card-only, dry-run default, never-persist, auto-cancel** — are
> **MANDATORY**, not optional hardening.

- A `FakeCard` factory that only yields non-chargeable PANs (obviously-invalid /
  test BIN, Luhn-invalid) and refuses any input that looks like a real Luhn-valid
  16-digit PAN. Real card entry to a live payment is blocked at the type level
  (no public "raw PAN" parameter into `ReservationPayment`).
- Card values are (in our design) routed through the server-side encrypt endpoints
  (`shinhan.Encrypt.do`/`common.encrypt.do`) as a defensive choice. **Note
  (2026-07-21):** the live Korail server also accepts a **raw PAN** in
  `hidStlCrCrdNo1` (the working client sends it unencrypted, `srtgo_plus/srtgo/
  ktx.py:1044`) — so encryption is NOT a server-enforced barrier; the fake-card +
  never-persist rules are what actually prevent a charge, and redaction (§4.6)
  must assume the raw PAN can appear on the wire.
- **No card data is ever persisted**: no card field written to disk, cache, log,
  or the repo; `FakeCard` holds values only in memory for the single call.
- Easy-pay PG redirect flows are explicitly `NotSupported` (headless library
  cannot complete a PG WebView).

### 4.5 Auto-cancel of test reservations

- `client.reserve(...)` returns a `ReservationHold` context manager. On `__exit__`
  without a successful payment, it fires Flow B (`ReservationCancel` →
  `ReservationCancelChk`) using the hold's `pnr_no`/`journey_count`
  (`mutation_models.py:28-38`) — matching the app's unpaid-hold cleanup. A
  `client.cancel_unpaid(hold)` convenience wraps the two-step ordering.
- Live mutation tests always run inside this context so an interrupted test never
  leaves a live hold.

### 4.6 PII / card redaction extension

`redaction.py:SENSITIVE_KEYS` (`redaction.py:10-126`) covers reservation/hold
identifiers (`h_pnr_no`, `h_wct_no`, `h_tmp_job_sqno1/2`, `h_rsv_chg_no`,
`h_cert_pwd`, …) but **does NOT cover payment card fields** (verified: 0 matches
for `hidStlCrCrdNo`/`hidVanPwd`/`spayCphdDatVal`/`encTotTxnAmt`/`hidCrdVlidTrm`/
`shStlCrCrdNo`). Add all `PaymentMethod` card/point/easy-pay keys (§3.C),
`encTotTxnAmt`, `spayStlKeyVal`, `publicKey`, `encValue`, refund GPS
`latitude`/`longitude`, and non-member `txtCustPw`/`nonMbPwd`/`hidPwd` to the set.
`CARD_RE` (`redaction.py:127`) already masks bare PANs; the new keys mask the
encrypted/keyed variants that `CARD_RE` misses.

### 4.7 Origin lock unchanged

`assert_korail_origin` (`safety.py:596-615`) still pins scheme/host/port to
`https://smart.letskorail.com` for every request including mutations — no new
hosts. The NetFunnel client is a **separate** host (`nf.letskorail.com`) and must
get its own explicit origin assertion (queue tokens only, never carries PII).

---

## 5. Correctness & bugs (client vs decompiled truth)

Concrete discrepancies, each with file:line on both sides. Fix as part of the
relevant phase.

1. **`logout()` never invalidates the server session.** Client:
   `KorailClient.logout()` → `clear_session()` drops the local cookie jar only
   (`client.py:222-223,219-220`; `session.py:199-202`). Decompiled: a real `GET
   /classes/com.korail.mobile.login.Logout` exists (`LoginService.java:29`;
   `docs/api-endpoints.md:184`; analysis §8.5.1 `…:2794`) and the app calls it to
   invalidate server-side. → Add G11 and call it from `logout()`.

2. **`ScheduleViewSpecial` is scaffolded but unreachable.** Client:
   `_ProductTrainInquiryContinuation`/`ProductTrainInquiryResponse` +
   builder/parser exist (`read_payloads.py:1059+`, `read_models.py:848`) and the
   path is in `DYNAPATH_ALLOWLIST_PATHS` (`constants.py:40`), but there is **no
   route in `KORAIL_READ_ONLY_ROUTES`** and **no client method** — a call would be
   rejected at `safety.py:626`. Decompiled: live endpoint
   `SeatMovieService.java:20`, NetFunnel `act_6` (analysis §8.5.2 `…:2800`,
   §3.16.3 `…:1325`). → Wire G1 (needs the NetFunnel `act_6` gate).

3. **Reservation hold form omits `pnrNo` and `pbepInfo`.** Client:
   `build_single_adult_reservation_form` emits `txtMenuId/txtJobId/txtGdNo/
   hidFreeFlg/txtStndFlg/txtTotPsgCnt/…` (`mutation_payloads.py:111-165`) with
   **no `pnrNo` and no `pbepInfo`**. Decompiled: member `TicketReservation`
   `ReservationRequest` includes `pnrNo` and `pbepInfo` (`CertificationService.java:52`;
   analysis §4.5 `…:1706`; `docs/api-endpoints.md:107`). For a fresh hold `pnrNo`
   is `""` and `pbepInfo` is government-cert-only, but the exact field contract
   must include them or the server may reject the shape. → Verify against a live
   hold before trusting the current shape.
   **CORRECTION (2026-07-21, srtgo ref):** a working member hold
   (`srtgo_plus/srtgo/ktx.py:864-904`; `srtgo/srtgo/ktx.py:715-755`) **omits both
   `pnrNo` and `pbepInfo`** and still succeeds — so the current scaffolding's
   omission is likely **correct**, not a bug. Downgrade this item: keep them out of
   the fresh-member-hold body (confirm on the live pass); the load-bearing gap is
   item 4, not this.

4. **Reservation hold form has no `OSrcar` seat keys / no specific-seat path.**
   Client: `mutation_payloads.py` emits only `txtSeatAttCd1..5` and passenger
   rows — no `txtSrcarCnt`/`txtSrcarNo{i}`/`txtSeatNo{i}`. Decompiled: `OJrny`/
   `OSrcar` carry `txtSrcarCnt`/`txtSrcarNo{i}`/`txtSeatNo{i}` for
   specific-seat/auto-assign booking (analysis §4.5 `…:1795-1798`). Current
   scaffolding = general-seat auto-assign, single adult only; it is **not** a
   general booking builder. → Rebuild as `O*`/`R*` carriers per §3.A, not a
   fixed template.
   **CONFIRMED-STILL-A-GAP (2026-07-21, srtgo ref):** srtgo does **not** support
   designated seats either — it sends `txtSrcarCnt="0"` (auto-assign only) with no
   `txtSrcarNo{i}`/`txtSeatNo{i}` (`srtgo_plus/srtgo/ktx.py:879`). So the reference
   confirms the auto-assign body shape (legacy `txt*` rows,
   `txtPsgTpCd{i}`/`txtDiscKndCd{i}`/`txtCompaCnt{i}`, `ktx.py:906-907`) but gives
   **no** data on the designated-seat carrier — that part remains genuinely
   unresolved and must come from the app model / a live probe.

5. **`RefundsRequest` wire-param rename.** Decompiled: the WCT field is stored as
   `h_orgtk_wct_no` but serialized as `@Field("h_orgtk_sale_wct_no")`
   (`RefundService.java:29`; analysis §3.9 `…:878`). The refund builder must emit
   `h_orgtk_sale_wct_no` on the wire (off-by-name trap). Client: not yet
   implemented — encode correctly from the start.
   **CONFIRMED (2026-07-21, srtgo ref):** the working refund sends
   `h_orgtk_sale_wct_no` (`srtgo_plus/srtgo/ktx.py:1084`) — rename verified.
   **✅ RESOLVED (2026-07-21, cross-validation):** the earlier "`txtPrnNo` may be
   the real server field" trap is closed — it is a srtgo **typo**. Our v6.5.0 uses
   `txtPnrNo` (`RefundService.java:29`, `RefundDao.java:24/69/113`,
   `ticketReturn/a.java:411`); tree-wide grep = **ZERO** `txtPrnNo` (cross-val §4).
   Emit `txtPnrNo`; no live verification needed for the name.

6. **Redaction misses payment card fields** — see §4.6. Client:
   `redaction.py:10-126` has zero card-field coverage; adding payment without
   this leaks `hidStlCrCrdNo`/`hidVanPwd`/etc. into any error/log. Decompiled
   field names: analysis §3.7.2 (`…:764-769`).

7. **`EXCLUDED_API_DOMAINS` is inert.** Client: defined `safety.py:9-20`,
   re-exported `__init__.py:181,317`, **referenced by no enforcement code**
   (verified). It documents intent but blocks nothing at runtime — the only real
   guard is the route allowlist. → §4.2 makes it enforced.

8. **Single cancel builder does not model the two-step ordering.** Client:
   `build_unpaid_reservation_cancel_form` (`mutation_payloads.py:169`) builds one
   body used for both steps, with no ordering/step distinction and no wiring.
   Decompiled: `ReservationCancel` (step 1) **then** `ReservationCancelChk` (step
   2), verified ordering (analysis §3.6 `…:699`). → Model both calls + enforce
   order in Flow B.
   **CORRECTION (2026-07-21, srtgo ref):** the working client cancels with a
   **single `ReservationCancelChk` call** — step 1 `ReservationCancel` is skipped
   (`srtgo_plus/srtgo/ktx.py:1060-1075`). So the single-body builder may in fact be
   sufficient. Treat single-call as the primary path and verify whether the app's
   step-1 is actually required on the live pass (params `txtPnrNo`/`txtJrnySqno`/
   `txtJrnyCnt`/`hidRsvChgNo` read from the reservation response, fallbacks
   `001`/`01`/`00000`, `ktx.py:315-317` — digit widths differ from the plan's
   `0001`/`000`).

9. **Default User-Agent is non-app-like.** Client:
   `KORAIL_USER_AGENT="korail-mobile-api/0.2.0"` (`constants.py:6`), while
   `live.py:63-65` synthesizes a real `Dalvik/2.1.0 (…Android…)` UA only for the
   live smoke path. DynaPath-gated reservation/search calls may behave
   differently under a non-Dalvik UA. Decompiled UA context: analysis §1.4. →
   Decide a single app-faithful default before live mutation.
   **CONFIRMED value (2026-07-21, srtgo ref):** the working client uses
   `User-Agent: Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N Build/UP1A.231005.007)`
   (`srtgo_plus/srtgo/ktx.py:32`) plus `Host: smart.letskorail.com`,
   `Connection: Keep-Alive`, `Accept-Encoding: gzip` (`ktx.py:34-40`). Adopt this
   as the app-faithful default. **Version delta:** srtgo sends
   `Version=250601002` (`ktx.py:643`) vs our decompiled app `250601003` — one step
   older; both use `Device="AD"`, `Key="korail1234567890"`. Keep `250601003`
   (matches the analyzed app), but note the server accepts a slightly older
   version. **CROSS-VALIDATION (2026-07-21):** `250601003` re-confirmed in our
   code (`BaseRequest.java:9,16`, `K4/g.java:11`; cross-val §6).

10. **DynaPath token default for reservation.** `TicketReservation`/`NonMemTicket`
    are in the allowlist (`constants.py:37-38`) but the app sends the token only
    when `IS_MACRO_ACTIVE=true` (false in v6.5.0 — analysis §3.5 `…:639`). A
    headless client sending the token by default diverges from the app. → Default
    OFF (`MutationPolicy.allow_dynapath_token=False`), opt-in only.
    **CORRECTION (2026-07-21, srtgo ref):** a working client sends
    `x-dynapath-m-token` on **all 6** protected paths **always**, with no macro
    flag (`srtgo_plus/srtgo/ktx.py:666-675`), because current Korail anti-bot
    policy expects it. The token-generation **algorithm is now known and
    reproducible** — `DynaPathMasterEngine` (`ktx.py:54-160`): device fingerprint +
    ts + nonce → app secret `[38ff229cb34c7dda8e28220a2d750cce]` + 62-char custom
    alphabet + key-derived permutation → base161→base30 → `bEeEP…`. The `Sid`
    companion is also confirmed (`AES-CBC` key `2485dd54d9deaa36`, `ktx.py:661-664`).
    Mark DynaPath reproduction **FEASIBLE (algorithm in hand)**, not a blocker.
    Keep the default OFF for safety, but be ready to flip it on for live reserve if
    a token-less call is rejected.
    **QUALIFIED (2026-07-21, cross-validation vs decompiled v6.5.0):** the
    algorithm *structure* is confirmed against our own code (`B/C1229b.java`,
    `l1/AbstractC5980b.java`) and `as` is verified as our signing-cert hash — **but
    srtgo's SDK-version string `v1` is STALE.** Our app uses `v1.0.3` in both the
    body `sv` field and the `dyn_key` prefix (`C1229b.java:137,157`), and that
    string reseeds the entire token, so any reproduction MUST source the version
    (and per-version constants) from our app — srtgo's `v1` would mint an invalid
    token if the server validates `sv`. Our app also computes several body fields
    **live** that srtgo hardcodes — anti-tamper `su/dbg/emu/hk`
    (`l1/AbstractC5981c.java`), the `rt` timing-delta array, `di` =
    `Settings.Secure.ANDROID_ID` (`AbstractC1228a.java:16`), and dynamic
    `os`/`dm`/`it`/`ts` (`C1229b.java:113-135`) — so a hardcoded reproduction is
    fingerprintable. The `IS_MACRO_ACTIVE` gate + 6-path allowlist are confirmed
    in our code (`ExecuteDao.java:26-47`). See Revision 2.

(Items 3–4 were the load-bearing ones for a working booking. Post-srtgo-ref: item
3 is largely resolved — a working hold omits `pnrNo`/`pbepInfo` — so **item 4
(designated-seat carrier) is the remaining load-bearing gap**, unconfirmed by any
reference. Still verify both against a single authorized live hold before locking
the field contract.)

---

## 6. Testing strategy

### 6.1 Offline fixtures (no I/O) — extend the existing pattern

- Add strict-`SUCC` fixtures under `tests/fixtures/` for each new response:
  `reservation_hold_success.json` (member + non-member), `seat_assign_success`,
  `reservation_change_success`, `reservation_cancel_success`,
  `reservation_cancel_chk_success`, `reservation_payment_success` (+ coupons),
  `refund_commission_success`, `refund_ticket_detail_success`,
  `refund_execute_success`, `refund_verify_success`, `checkin_possible_success`,
  `checkin_info_success`, plus `*_fail` / `P058` / non-`SUCC` variants for the
  RED gate.
- Builder tests: exact form equality per route (as
  `tests/test_mutation_payloads.py:40-100` does today), including the `R*`/`O*`
  FieldMap flattening, the check-in `saleDd`/`saleDt` split, the
  `h_orgtk_sale_wct_no` rename (§5.5), and `PaymentMethod` card/point rows.
- Safety tests: mutation route rejected unless domain enabled + confirm token +
  `dry_run=False`; dry-run returns a `PreparedRequest` and sends nothing;
  excluded-domain route rejected even when in the mutation set; redaction masks
  every new card/PII key (§4.6).
- Transport tests via `httpx.MockTransport` (as `tests/test_http.py`): the
  mutation path attaches DynaPath only when opted in; NetFunnel gate is invoked
  for `act_18`/`act_6` and skipped elsewhere.
- Keep the whole offline suite green and CI-only (`pytest`, `live` marker
  deselected — `pyproject.toml:42-44`).

### 6.2 Live-smoke plan (authorized phase; ordered, idempotent, cleanup-guaranteed)

Gate all of this behind `KORAIL_MOBILE_API_LIVE=1` (`live.py:17`) + explicit
per-flow opt-in envs; credentials only from the gitignored `.env`
(`.gitignore:3`).

1. **Read-only live first** (already exercised — `run_live_smoke_from_env`,
   `live.py:74-174`): login with the email stored in `.env` → `IRZ000001`;
   confirm cache/search/schedule/reservation-history reads. Add G1/G4/G12 reads.
2. **Reservation hold (state change, no payment):** search → build a single-adult
   general-seat hold on a **far-future low-demand** train → `TicketReservation`
   → assert `h_pnr_no`, `h_payment_flg`. **Immediately** run Flow B
   (`ReservationCancel`→`ReservationCancelChk`) inside the auto-cancel context
   (§4.5). Verify reservation history empty before and after (matches the prior
   authorized bounded check, `docs/IMPLEMENTATION_PROGRESS.md:231-237`).
3. **Payment with FAKE card (expected rejection, no charge):** create a fresh
   hold → `ReservationPayment` with a `FakeCard` (invalid PAN via
   `common.encrypt.do`) → assert an application `FAIL`/rejection envelope
   (`KorailAppError`), **never** `SUCC`. Then auto-cancel the hold. No real PG
   redirect. Persist nothing.
4. **Cancel/change:** covered by 2–3; additionally a `tripChgDate`(read, already
   live) → `tripChgOgtk`(G4) dry-run of `reservationChange` (validate only) — no
   live change execution in v1 unless a disposable paid ticket exists.
5. **Refund / check-in:** dry-run + fixture only in v1 (both need a real
   paid/boarded ticket to exercise; do not fabricate). Live-execute deferred
   until a disposable real ticket is explicitly authorized.

**Safety/idempotency rules:** one request per step, no retries/fallbacks
(existing discipline, `docs/IMPLEMENTATION_PROGRESS.md:398-404`); every hold in an
auto-cancel context; assert emptiness pre/post; log only fixed statuses + bounded
counts, never raw bodies/identifiers/PANs; fail closed if cleanup fails.

---

## 7. Release readiness

- **Versioning.** `0.2.0` → `0.3.0` when mutation lands (minor; new public
  surface, back-compatible reads). Update `pyproject.toml:7` and
  `KORAIL_USER_AGENT` (`constants.py:6`) together. First fully-tested mutation
  release can target `1.0.0` once live flows A–C are verified.
- **CHANGELOG.** New top section documenting: mutation tiering, NetFunnel client,
  reservation/cancel/payment/refund/check-in methods, fake-card + auto-cancel
  safety, redaction extension, `logout()` network fix (`CHANGELOG.md:3`).
- **Docs.** Refresh `docs/IMPLEMENTATION_PROGRESS.md` (route/method counts,
  mutation status), `docs/api-status-by-service.md` (move executed writes out of
  "미실행"), `docs/api-endpoints.md` (mark implemented), and add a
  `docs/MUTATION_GUIDE.md` (consent model, fake-card, cleanup). Keep this plan as
  the driving doc.
- **Packaging.** Description in `pyproject.toml:8` currently says "read APIs" —
  update to reflect gated mutation. Keep `httpx`/`cryptography` deps
  (`pyproject.toml:23-26`); no runtime dep for NetFunnel needed (the reference
  shows Korail reserve/pay work without any NetFunnel client — see §3 correction).
  `Development Status` classifier `3 - Alpha` → `4 - Beta` at 0.3.0.
- **Licensing (2026-07-21, srtgo ref).** The reference sources are permissive —
  srtgo/srtgo_plus is **MIT**, korail2 (the KTX logic's ancestor) is **BSD-3** — so
  there is no copyleft transfer risk. We reference **factual request/response
  shapes only** (endpoint paths, field keys, body layout); we do **not** copy
  source verbatim — in particular the `DynaPathMasterEngine` must be
  **reimplemented independently**, not copied (`srtgo_plus/srtgo/ktx.py:54-160`).
  Our library currently has **no top-level `LICENSE` file and no pyproject license
  field** — **add a `LICENSE`** before release, and if any crypto/DynaPath logic is
  derived from BSD-3 sources, preserve the required attribution.
- **Public API surface.** Add to `__all__` (`__init__.py:183-347`): mutation
  methods, `MutationPolicy`, `ConfirmToken`, `FakeCard`, `ReservationHold`,
  `PreparedRequest`, new response/exception types, `NetFunnelClient`. Keep
  read exports stable.
- **README.** Add a prominent "Mutation is opt-in and off by default; live
  payment uses fake cards only" banner; document the consent/dry-run/auto-cancel
  workflow; keep the read quickstart first.
- **SECURITY.md.** Expand (`SECURITY.md`): never commit `.env`; card data never
  persisted; fake-card-only testing; PII redaction guarantees; origin lock; the
  library refuses real-charge paths. Note NetFunnel/DynaPath are anti-surge/
  anti-macro layers, not auth.

---

## 8. Phased roadmap

Each phase: concrete checkable tasks + risk rating. Prefer completing/aligning the
existing architecture over rewrites.

### P0 — Read completion (Risk: Low)
- [ ] Wire G1 `ScheduleViewSpecial` (route + method + reuse existing scaffolding)
      behind the new NetFunnel `act_6` gate (bug §5.2).
- [ ] Add reads G2–G12 (route, exact field contract, model, parser, method,
      fixtures, redaction) — pure reads, no consent gate.
- [ ] Fix `logout()` to call server `Logout` (bug §5.1, G11).
- [ ] Offline tests green; no new mutation capability.

### P1 — Safety-model rework + NetFunnel client (Risk: Medium)
- [ ] Implement route tiers, `KORAIL_MUTATION_ROUTES`, mutation field maps,
      `assert_allowed_route(allow_mutation=…)` (§4.1).
- [ ] Enforce `EXCLUDED_API_DOMAINS` (§4.2, bug §5.7); add `MutationPolicy`,
      `ConfirmToken`, `dry_run` (§4.3).
- [ ] Extend redaction to card/PII fields (§4.6, bug §5.6).
- [ ] ~~Build minimal `NetFunnelClient`~~ **DEPRIORITIZED (2026-07-21 rev):** the
      reference shows Korail reserve/pay/refund/cancel work with **no** NetFunnel;
      drop from the P1 critical path. Only revisit if a live call returns a
      queue-required error, or if G1 tour-search (`act_6`) is later scoped.
- [ ] All still read-only at runtime (defaults off); offline tests prove a
      mutation route is rejected without full opt-in.

### P2 — Reservation hold + cancel (Flows A/B), no payment (Risk: High)
- [ ] Rebuild reservation payload as `O*`/`R*` carriers (bugs §5.3–5.4; note the
      designated-seat carrier is the remaining gap — `pnrNo`/`pbepInfo` are not
      needed per 2026-07-21 rev); wire
      `TicketReservation`/`NonMemTicket`/`seatAssign`/`reservationWait` + cancel
      (**single `ReservationCancelChk` primary**, keep 2-step as fallback pending
      live check — §3.B, 2026-07-21 rev).
- [ ] `ReservationHold` auto-cancel context manager (§4.5).
- [ ] Authorized live: single far-future hold + immediate cancel; verify history
      empty pre/post; nothing persisted (§6.2 step 2).

### P3 — Payment with fake card (Flow C, ~~act_18~~ no NetFunnel gate) (Risk: High)
- [ ] `PaymentMethod` builder (card/point rows), `common.encrypt.do`/
      `shinhan.Encrypt.do`/`nFilter.createKey.do` helpers, `spayOrdNo`
      amount-guard reuse of the login cipher (§3.C).
- [ ] `FakeCard` (never-chargeable, blocks real Luhn PANs); no card persistence;
      easy-pay PG redirect = `NotSupported` (§4.4).
- [ ] Wire `ReservationPayment` with a confirm token (**no `act_18` NetFunnel
      gate** — 2026-07-21 rev; the reference pays with a single POST, no queue
      token).
- [ ] Authorized live: fresh hold → fake-card pay → assert rejection (never
      `SUCC`) → auto-cancel (§6.2 step 3).

### P4 — Refund / cancel-change / check-in (Flows D/E + change) (Risk: High)
- [ ] Refund online (`SelTicketInfo`→`CommissionView`→`RefundsRequest`, wire
      quirk §5.5) + offline (`verify`→`execute`); dry-run + fixtures only in v1.
- [ ] `reservationChange`/`tripChgPrsC`/`tripChgHndgCnc` with `R*` maps;
      `tripChgOgtk` read prereq (G4).
- [ ] Check-in `psbFlg`/`reg`/`info`/`cnc` with the `saleDd`/`saleDt` split
      (trap §3.E); dry-run + fixtures; live only against a disposable real ticket
      if separately authorized.

### P5 — Release prep (Risk: Low)
- [ ] Version bump 0.2.0→0.3.0 (→1.0.0 after A–C live-verified); CHANGELOG;
      docs (§7); README mutation banner; SECURITY expansion.
- [ ] Update `__all__`, packaging description/classifier; build wheel+sdist,
      isolated-install import check (as `docs/IMPLEMENTATION_PROGRESS.md:310-317`).
- [ ] Final review: no card data persisted, redaction complete, mutations
      default-off, credentials untracked (`.gitignore:3`).

---

## Revision 2026-07-21 — srtgo/srtgo_plus reference findings

Corrections applied inline above after static analysis of a **working** KTX
client (srtgo / srtgo_plus). Source of record: `docs/deep-dive/ref-srtgo_plus.md`;
code cited from `srtgo_plus/srtgo/ktx.py` and `srtgo/srtgo/ktx.py`. These override
app-only inferences where they conflict; each item is confirm-on-live-pass unless
marked confirmed.

- **NetFunnel is NOT needed for Korail** (§3 cross-cutting, §3.C header). Korail
  uses **no** NetFunnel at all — only SRT does. srtgo instantiates
  `NetFunnelHelper` (`ktx.py:640`) but never calls `.run()` and sends no
  `netfunnelKey` in the reserve (`:864-904`) or pay (`:1030-1051`) body; no
  `act_18` payment gate / `act_14` reserve gate exists (`:601-608`). Downgraded
  from "single biggest new subsystem" to **not required** for reserve/pay/refund.
- **DynaPath is FEASIBLE, not a blocker** (§1, §3 cross-cutting, §5 item 10). Token
  sent on all 6 paths always (`:666-675`); the generation algorithm is known and
  reproducible (`DynaPathMasterEngine`, `:54-160`; app secret
  `[38ff229cb34c7dda8e28220a2d750cce]`, 62-char alphabet, base161→base30 →
  `bEeEP…`). `Sid` confirmed (`AES-CBC` key `2485dd54d9deaa36`, `:661-664`).
  **→ QUALIFIED by Revision 2:** reproducibility holds for the algorithm
  *structure* only; srtgo's version string `v1` is stale — our app uses `v1.0.3`
  (`C1229b.java:137,157`), which must seed the token.
- **Reservation body correction** (§3.A, §5 items 3–4). Working member hold omits
  `pnrNo`/`pbepInfo` and uses legacy `txt*` passenger rows with
  `txtJobId=1101`(seat)/`1102`(waitlist) (`:864-904` / orig `:715-755`).
  Designated-seat (`txtSrcarNo`/`txtSeatNo`) is **not** supported by srtgo
  (auto-assign, `txtSrcarCnt="0"`) — remains our genuine gap.
- **Cancel is a single call** (§3.B, §5 item 8): only
  `reservationCancel.ReservationCancelChk` (`txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`,
  `hidRsvChgNo`), step-1 skipped (`:1060-1075`). Not the 2-step flow originally
  assumed.
- **`txtPrnNo` refund trap** (§3.D, §5 item 5): srtgo names the refund PNR field
  **`txtPrnNo`** (P-**r**-n, `:1082`), not `txtPnrNo` — flag for live verification.
  Wire-rename `h_orgtk_sale_wct_no` confirmed (`:1084`).
  **→ RESOLVED by Revision 2:** srtgo's `txtPrnNo` is a typo; our v6.5.0 uses
  `txtPnrNo` (tree-wide `txtPrnNo` = 0). No live check needed for the field name.
- **Payment card fields confirmed** (§3.C, §4.4/§4.6): `hidStlCrCrdNo1`/`hidVanPwd1`/
  `hidCrdVlidTrm1`/`hidAthnVal1`/`hidAthnDvCd1`/`hidIsmtMnthNum1` +
  `hidStlMnsCd1="02"`/`hidCrdInpWayCd1="@"`/`hidPnrNo`/`hidWctNo`/`hidMnsStlAmt1`
  (`:1030-1051`). **Raw PAN sent unencrypted** (`:1044`) → redaction essential;
  fake-card/dry-run/never-persist/auto-cancel **mandatory** (safety §4 reinforced).
- **Also:** UA `Dalvik/2.1.0 (… Android 13; SM-S928N …)` confirmed (`:32`);
  `Version=250601002` (srtgo) vs `250601003` (our app) delta noted (§5 item 9);
  check-in unimplemented by srtgo → still a gap (§3.E); licensing (MIT/BSD-3,
  permissive) → reference facts only, reimplement DynaPath, add a `LICENSE` (§7).

---

## Revision 2 (2026-07-21) — cross-validation vs decompiled v6.5.0

Second-pass corrections from `docs/deep-dive/cross-validation-2026-07-21.md`, which
re-checked the srtgo/srtgo_plus reference (treated as ground truth in the first
Revision above) against **our own decompiled `com.korail.talk` v6.5.0**
(`analysis/jadx/sources/…`, `analysis/apktool/`) — the real ground truth. Where the
first Revision trusted srtgo, this pass promotes claims we could re-read in our code
to **verified**, and *qualifies* the ones where srtgo turned out to be stale. Each
item cites the cross-validation doc **and** the decompiled file:line.

1. **DynaPath reproducibility is QUALIFIED — version drift (highest impact).** The
   token algorithm *structure* is confirmed against our code (UTF packing,
   `make_key`, encode tables, base62 alphabet, `bEeEP` prefix, pack=161/radix=30/
   group=2 — cross-val §1 ✅; `B/C1229b.java`, `l1/AbstractC5980b.java`), and the app
   secret `as` is verified as our v6.5.0 signing-cert hash. **BUT srtgo's SDK-version
   string `v1` is STALE — our app uses `v1.0.3`** in *both* the body `sv` field and
   the `dyn_key` prefix (`C1229b.java:137,157`; cross-val §1 ⚠/🔀). Because that
   string reseeds the whole token, a reproduction MUST take the version (and any
   per-version constants) from our app; srtgo's `v1` mints a self-consistent but
   **invalid** token if the server validates `sv`. Corrects the "algorithm in hand /
   reproducible" verdict in §1.1, §3 (cross-cutting), §5 item 10, and the first
   Revision's DynaPath bullet: FEASIBLE but **version-string-dependent on our app**,
   not on srtgo.
2. **Refund PNR field RESOLVED — `txtPnrNo`, definitively.** The earlier
   "⚠ `txtPrnNo` (P-r-n) trap — needs live verification" (§3.D, §5 item 5) is closed:
   srtgo's `txtPrnNo` is a **typo**. Our v6.5.0 uses `txtPnrNo` (P-n-r) in refund
   (`RefundService.java:29`, `RefundDao.java:24/69/113`, `ticketReturn/a.java:411`),
   and a tree-wide grep proves **`txtPrnNo` occurs ZERO times** anywhere in our
   sources (cross-val §4 ⚠ + 📌). Ground truth = `txtPnrNo`; no live check needed for
   the field name.
3. **Protocol Version re-confirmed = `250601003`** (`BaseRequest.java:9,16`,
   `K4/g.java:11`; cross-val §6 ⚠/🔀). srtgo's `250601002` is one build behind; keep
   our value (already used in the header/§3 envelope and §5 item 9).
4. **Confidence raised — verified against OUR decompiled code (not just srtgo):**
   - Reservation body needs **no `pnrNo`/`pbepInfo`** for a fresh member hold
     (cross-val §2; the params exist on the overload but stay empty — §3.A,
     §5 item 3).
   - **Cancel is a single call** to `ReservationCancelChk`, which is the **COMMIT**
     step (not an eligibility pre-check); our app's extra step-1 `ReservationCancel`
     is an *initiate* (cross-val §4 ⚠; `a6/x.java:190-207`) — §3.B, §5 item 8.
   - **Payment card field names** `hidStlCrCrdNo1/hidVanPwd1/hidCrdVlidTrm1/
     hidIsmtMnthNum1/hidAthnDvCd1/hidAthnVal1` match our `PaymentMethod` constants
     (`PaymentMethod.java:14-19`, `v4/a.java:29-34`), and the **raw PAN is
     unencrypted** on the wire (`v4/a.java:29`) — cross-val §3 ✅ (§3.C, §4.4).
   - **Sid** AES/CBC/PKCS5, key = iv, plaintext `"AD"+ms`, Base64.DEFAULT with
     trailing newline — confirmed at `S4/C0812l.java:43-50` (cross-val §1/§5/§6 ✅).
   - **6-path DynaPath allowlist + `IS_MACRO_ACTIVE` gate** confirmed:
     `ExecuteDao.java:26-47` wraps the token in `if (a.IS_MACRO_ACTIVE)` (default
     `false`, flips only on server `isMacroEnable=='Y'`) over the exact 6 paths
     (cross-val §1 ✅). NB our app is thus **stricter** than srtgo, which attaches the
     token unconditionally.
5. **~44 newly-found hidden items** the srtgo pass never modeled (tallied across the
   six 🆕 subsections of the cross-validation doc). Notable for us:
   - **Live device-fingerprint / anti-macro telemetry inside the DynaPath body** that
     srtgo hardcodes: anti-tamper `su/dbg/emu/hk` (root/debug/emulator/hook
     detection, `l1/AbstractC5981c.java`), `rt` = array of ≤5 inter-call timing
     deltas, `di` = the real `Settings.Secure.ANDROID_ID` (`AbstractC1228a.java:16`),
     and dynamic `os`/`dm`/`it`/`ts` (`C1229b.java:113-135`). A headless client that
     hardcodes these is fingerprintable server-side (cross-val §1 🆕).
   - **Uncaptured SDK secrets in `res/values/strings.xml`** relevant to device
     fingerprinting — `google_api_key`, `google_app_id`, the GCM sender id, the
     Firebase project id, and `kakao_app_key` (cross-val §5 📌; values deliberately
     NOT copied into this plan). Treat as sensitive; never embed in our client.
   - **Unmodeled mutation endpoints:** self check-in (4), `reservation.seatAssign.do`,
     the full tripChg change flow, `reservation.reservationChange.do`, special-room
     upgrade, waiting-list conversion, and a **separate delay-compensation cash
     refund** distinct from `refunds.RefundsRequest` (cross-val §5 🆕) — most are
     already in §3/§5 scope; the delay-comp refund is a fresh deferred item.
6. **Pointer:** the full six-dimension reconciliation (per-claim ✅/⚠/🔀/🆕/📌/❓
   labels, both-sides file:line, and the "Net changes / Remaining open questions"
   summary) lives in `docs/deep-dive/cross-validation-2026-07-21.md`.

---

### Appendix — anchor references

- Read allowlist / field contracts / origin lock: `safety.py:22-108,112-526,596-699`.
- Transport gates: `http.py:138-254`. Session/login: `session.py`. Crypto:
  `crypto.py:41-62`. DynaPath: `dynapath.py`, `constants.py:34-44`. Redaction:
  `redaction.py:10-127`. Live smoke: `live.py`.
- Mutation scaffolding: `mutation_models.py`, `mutation_parsers.py`,
  `mutation_payloads.py`; tests `tests/test_mutation_payloads.py`,
  `tests/test_mutation_response_parsers.py`.
- Authoritative decompiled analysis: `docs/deep-dive/full-api-analysis-2026-07-20.md`
  §3.5–3.10 (endpoints), §4.5–4.6 (booking/cancel DAOs), §7.7 (NetFunnel), §8.4–8.5
  (coverage/divergences). Endpoint inventory: `docs/api-endpoints.md`. Status:
  `docs/api-status-by-service.md`.
- **Working-client cross-check (2026-07-21):** `docs/deep-dive/ref-srtgo_plus.md`
  — static analysis of the srtgo/srtgo_plus KTX client (reserve/pay/cancel/refund
  request shapes, DynaPath/Sid, NetFunnel non-use). Cited code:
  `srtgo_plus/srtgo/ktx.py` (DynaPath engine `:54-160`; reserve `:864-904`; pay
  `:1030-1051`; cancel `:1060-1075`; refund `:1077-1097`) and `srtgo/srtgo/ktx.py`
  (original reserve `:715-755`). Drives the corrections annotated throughout §1,
  §3–§5 and the revision section below.
- **Cross-validation vs decompiled v6.5.0 (2026-07-21):**
  `docs/deep-dive/cross-validation-2026-07-21.md` — reconciles the srtgo reference
  against our own decompiled `com.korail.talk` v6.5.0 across six dimensions
  (DynaPath, reservation, payment, cancel/refund, uncovered-hidden, transport/auth)
  with per-claim ✅/⚠/🔀/🆕/📌/❓ labels and both-sides file:line. Ground truth for
  Revision 2.
