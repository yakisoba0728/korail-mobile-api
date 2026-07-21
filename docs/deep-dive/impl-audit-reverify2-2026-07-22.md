# Korail Client Implementation Audit — Re-verify (Round 2) — 2026-07-22

**Target app:** `com.korail.talk` v6.5.0 (decompiled ground truth under `analysis/jadx` + `analysis/apktool`)
**Under audit:** the read-only Python client in `src/korail_mobile_api/`
**Author:** FABLE
**Ground-truth rule:** the decompiled Korail app is authoritative. Where a client test bakes in a divergence, the test is treated as wrong, not the app; where `srtgo` diverges from the decompile, the decompile wins.

This is the **second adversarial re-verify** pass over the scoped sub-audits (auth/session/crypto, common-station, search-schedule, seat-fare-traininfo, ticket-reservation-read, account-pass-maas-limousine, safety-transport). Every candidate divergence was re-checked against the decompile (and, where relevant, apktool smali / fixtures) before being counted. Findings that did not survive that check are listed under [Rejected / non-bugs](#rejected--non-bugs) and are **not** counted as real. Each entry carries both-sides `file:line` citations: where our client diverges, and where the app proves the correct behavior.

## Headline

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 0 |
| Low | 3 |
| **Total real divergences** | **3** |

All three surviving divergences are **Low** and are **content / value** divergences on peripheral or common-path-invisible fields — none is a wrong route, wrong HTTP method, wrong envelope, or wrong field *name*. Two are over-strict-parser risks that only bite on server responses no fixture has yet exhibited; one is a provable telemetry-value stub. A compliant server accepts every affected request today.

Relative to the previous re-verify ([`impl-audit-reverify-2026-07-22.md`](impl-audit-reverify-2026-07-22.md)): the **DynaPath `rt` stub** is re-confirmed (RV2-01 ≡ prior RV-01). The prior RV-02 (phone-auth continuation POST forwarding the raw envelope) is **demoted to a non-bug** this round — the continuation path is a rare additional-auth WebView flow and extra `x-www-form-urlencoded` params are typically harmless, so it is recorded as an observation, not a counted divergence. Two **new** lows surfaced: an over-strict train-calendar parser (common-station) and hardcoded seat-attribute / goods-number params in the two seat-map builders (search-schedule).

---

## Prioritized bug table (High → Low)

| # | Severity | Area | Our ref | Ground-truth ref | Description | Fix |
|---|---|---|---|---|---|---|
| RV2-01 | Low | DynaPath token — `rt` (request-timing) field | `src/korail_mobile_api/dynapath.py:303` | `analysis/jadx/sources/B/C1229b.java:76-91,114-127` (with `DynaPathMobileSDK.java:33-35`) | The DynaPath token's `rt` field is hardcoded to the single literal `"0"`. In the app, `DynaPathMobileSDK.generate()` calls `C1229b.a(now)` immediately before building the token, pushing a delta onto the `recentTimestamp` deque: on the first request `delta = now − app_start_ts` (`= it`), thereafter the inter-request delta; the token then emits that real delta as `rt` (and may emit multiple `rt=` values). Our token emits `it`=app_start and `ts`=now (which differ) yet `rt=0`, i.e. it claims 0 ms elapsed while `ts − it` is large. A server-side DynaPath validator cross-checking `rt` against `ts`/`it` could flag the token as inconsistent. Bounded impact: this token attaches only to the 6 allowlisted paths (incl. login) AND only when DynaPath is enabled — off by default in our client, and gated behind `IS_MACRO_ACTIVE` (hardcoded `false`) in the app, so the app never sends it by default. This is a **deliberate simplification** (test named `..._fixed_rt_reference`; `DynapathTokenSettings` intentionally rejects `recent_request_deltas`) — a known trade-off, reported only because it is a provable value divergence. | If exact fidelity is wanted, track request timestamps and emit `rt` = `(now − previous_ts)`, or `(now − app_start_ts)` on the first call, supporting up to 5 values to match `C1229b.a(long)`. Otherwise document that `rt` is a fixed stub and that the app never sends the token by default (`IS_MACRO_ACTIVE=false`). |
| RV2-02 | Low | `schedule.runDt` calendar parser — over-strict field/list requirements | `src/korail_mobile_api/parsers.py:466-538` (`bizDdStgCd` 484-488, `dayDvCd` 489-493; non-empty list guard 466-470) | `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:68-70` (`isPeakSeason` = `N.notNullEqual(bizDdStgCd,"5")`), `:44-82` (`BOOL_YES.equals(...)` null-safe flag accessors), `:101-103` (`getRunningCalendarList` tolerates empty) | `parse_train_calendar_response` requires every `RunningCalendar` field (incl. `bizDdStgCd`, `dayDvCd`, and all `*TrnOpFlg` flags) to be a present non-null string via `_typed_required_string`, and requires `runningCalendar` itself to be a **non-empty** list via `_typed_required_non_empty_list`. The decompiled DTO treats several as nullable/optional: `isPeakSeason()` uses `N.notNullEqual(bizDdStgCd,"5")` (explicit null-guard), and the `*TrnOpFlg` accessors use `BOOL_YES.equals(this.xTrnOpFlg)` (null-safe, returns false), so the app tolerates null/absent values our parser rejects; `dayDvCd` has no accessor at all in the DAO. A production calendar where any of these is null/absent (or an empty `runningCalendar`, e.g. no bookable dates) raises `KorailProtocolError` and fails the whole calendar read, though the app renders it fine. The model `TrainCalendarDay` already declares these as `str | None`, so only the parser is inconsistently strict. | Parse `bizDdStgCd`, `dayDvCd`, `saleDdDvCd` and the `*TrnOpFlg` fields with `_typed_optional_string` (keep `hldyDvCd` required — `isHoliday()` calls `this.hldyDvCd.isEmpty()` with no null-guard), and use `_typed_required_list` instead of `_typed_required_non_empty_list` for `runningCalendar`. |
| RV2-03 | Low | `TrainResearch` (getCarList) / `TResidualSeatsResearch` (getSeatList) — hardcoded seat-attribute & goods-no. | `src/korail_mobile_api/payloads.py:116` (`build_seat_car_form` 116-117; `build_seat_inventory_form` 146,150) | `analysis/jadx/sources/x4/b.java:19` (`setTxtSeatAttCd(trainInfo.getH_seat_att_cd())`), `:23` (`setTxtGdNo(trainInfo.getTxtGdNo())`) | `build_seat_car_form` hardcodes `txtSeatAttCd="015"` and `txtGdNo=""`; `build_seat_inventory_form` hardcodes `seatAttCd="015"` and `gdNo=""`. The app derives both from the **selected train row**, not constants: the shared `SeatSearchRequest` (feeding both getCarList and getSeatList) sets `txtSeatAttCd = trainInfo.getH_seat_att_cd()` and `txtGdNo = trainInfo.getTxtGdNo()`. Our `TrainSummary` already parses `seat_attribute_code` from `h_seat_att_cd` (`models.py:393`) but ignores it here. For the standard general-class KTX/ITX this read client targets, `h_seat_att_cd="015"` and `txtGdNo` is empty (fixture `schedule_view_success.json` shows both null), so no observable divergence on the common path; it diverges only for trains whose general seat-attribute code ≠ `015` or for product/goods trains (which this read client does not search). Hence Low, but a provable param-value divergence. | Pass the train's own values instead of constants: `txtSeatAttCd`/`seatAttCd` = `train.seat_attribute_code` (`h_seat_att_cd`) and `txtGdNo`/`gdNo` = the train's `txtGdNo` (capture `h_`/`txtGdNo` into `TrainSummary`), falling back to `"015"`/`""` only when absent. |

---

## Detailed findings

### RV2-01 — DynaPath token hardcodes `rt="0"` (Low)

- **Our ref:** `src/korail_mobile_api/dynapath.py:303` — `("rt", "0")` in the token field list.
- **Ground-truth ref:** `analysis/jadx/sources/B/C1229b.java:76-91` (delta computation) and `:114-127` (`rt` serialization); `analysis/jadx/sources/.../DynaPathMobileSDK.java:33-35` (`generate()` calls `C1229b.a(now)` immediately before building the token).

`DynaPathMobileSDK.generate()` primes the SDK with `C1229b.a(System.currentTimeMillis())` right before assembling the token. `C1229b.a(long)` computes a delta — on the first request `now − app_start_ts` (equal to the token's own `it`), thereafter the inter-request delta — and pushes it onto the `recentTimestamp` deque, which serializes (up to 5 entries) as one or more `rt=` values. Our token emits `it`=app_start and `ts`=now, which **differ** by a large amount, yet emits `rt=0`, asserting zero elapsed time. A server-side validator that cross-checks `rt` against `ts − it` could flag the token as internally inconsistent.

**Impact / caveat.** The token attaches only to the 6 allowlisted DynaPath paths (including login) **and** only when DynaPath is enabled. DynaPath is **off by default** in our client, and in the app it is gated behind `IS_MACRO_ACTIVE` (hardcoded `false`), so the app never emits this token in the default build. This finding is a **deliberate simplification**, not an oversight: the reference test is literally named `..._fixed_rt_reference`, and `DynapathTokenSettings` intentionally rejects `recent_request_deltas`. It is reported solely because it is a provable value divergence from the decompiled SDK.

**Fix.** For exact fidelity, track request timestamps and emit `rt = (now − previous_ts)`, or `(now − app_start_ts)` on the first call, supporting up to 5 values to mirror `C1229b.a(long)`. Otherwise document that `rt` is a fixed stub and that the app never sends the token by default (`IS_MACRO_ACTIVE=false`).

### RV2-02 — `schedule.runDt` calendar parser is stricter than the app's tolerant DTO (Low)

- **Our ref:** `src/korail_mobile_api/parsers.py:466-538` — `bizDdStgCd` at `484-488`, `dayDvCd` at `489-493`, the non-empty-list guard at `466-470`.
- **Ground-truth ref:** `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:68-70` (`isPeakSeason()` = `N.notNullEqual(this.bizDdStgCd,"5")`, explicit null-guard); `:44-82` (all `*TrnOpFlg` accessors use `BOOL_YES.equals(this.xTrnOpFlg)`, null-safe → false); `:101-103` (`getRunningCalendarList` tolerates empty).

`parse_train_calendar_response` requires every `RunningCalendar` field — including `bizDdStgCd`, `dayDvCd`, and all `*TrnOpFlg` flags — to be a present non-null string via `_typed_required_string`, and requires `runningCalendar` to be a **non-empty** list via `_typed_required_non_empty_list`. The decompiled DAO is tolerant: `isPeakSeason()` null-guards `bizDdStgCd`, the flag accessors are null-safe (absent → `false`), and `dayDvCd` has no accessor at all. So a production calendar where any of these is null/absent — or an empty `runningCalendar` (e.g. a window with no bookable dates) — would raise `KorailProtocolError` and fail the **entire** calendar read, even though the app renders the same payload fine. The model `TrainCalendarDay` already declares all these fields as `str | None`; only the parser is inconsistently strict.

**Fix.** Parse `bizDdStgCd`, `dayDvCd`, `saleDdDvCd` and the `*TrnOpFlg` fields with `_typed_optional_string`, and use `_typed_required_list` instead of `_typed_required_non_empty_list` for `runningCalendar`. Keep `hldyDvCd` **required** — `isHoliday()` calls `this.hldyDvCd.isEmpty()` with no null-guard, so the app itself would NPE on a null `hldyDvCd`, making strictness correct there.

### RV2-03 — Seat-map builders hardcode `seatAttCd`/`gdNo` instead of using the train row (Low)

- **Our ref:** `src/korail_mobile_api/payloads.py:116-117` (`build_seat_car_form`: `txtSeatAttCd="015"`, `txtGdNo=""`) and `:146,150` (`build_seat_inventory_form`: `seatAttCd="015"`, `gdNo=""`).
- **Ground-truth ref:** `analysis/jadx/sources/x4/b.java:19` (`setTxtSeatAttCd(trainInfo.getH_seat_att_cd())`) and `:23` (`setTxtGdNo(trainInfo.getTxtGdNo())`) — the shared `SeatSearchRequest` feeds both `getCarList` and `getSeatList`.

Both seat-map builders bake in `015` / empty for the seat-attribute code and goods number. The app derives both from the **selected train row** on a single `SeatSearchRequest` object shared across the car-list and seat-inventory calls. Our `TrainSummary` already parses `seat_attribute_code` from `h_seat_att_cd` (`models.py:393`) but the builders ignore it.

**Scope / caveat.** For the general-class KTX/ITX trains this read client targets, `h_seat_att_cd` is `015` and `txtGdNo` is empty — fixture `schedule_view_success.json` shows both `h_seat_att_cd`/`txtGdNo` as null — so there is **no observable divergence on the common path**. It diverges only for trains whose general seat-attribute code is not `015`, or for product/goods trains (which this read client does not search). That common-path invisibility is why it is Low, but it remains a provable param-value divergence.

**Fix.** Pass the train's own values instead of constants: `txtSeatAttCd`/`seatAttCd` = `train.seat_attribute_code` (`h_seat_att_cd`), and `txtGdNo`/`gdNo` = the train's `txtGdNo` (capture `h_`/`txtGdNo` into `TrainSummary`), falling back to `"015"`/`""` only when the source is absent.

---

## Verified correct

Areas that were audited and **confirmed to match ground truth** (recorded so the clean surface is on record, not just the divergences):

**auth-session-crypto** — All auth/session/crypto/DynaPath routes, param names, envelope, success codes, and cookie/`JSESSIONID` handling are correct, cross-checked against `LoginService`/`LoginDao`/`LogoutDao`, `S4/C0812l` (`getSid`/`encryptAES`), `F4/a` (base64), the `B/C1229b` + `l1`/`AbstractC5980b`/`AbstractC5987i`/`C5979a` DynaPath stack, `ExecuteDao`/`BaseDaoHelper`, `BaseRequest`/`BaseResponse`, and `CommonCodeDao.Login` (with `srtgo` `ktx.py` as a secondary reference). Both AES constructions are correct. The two recently-fixed items — DynaPath `v1.0.3` (`sv`/`st`/`ai`/`as`) and the GET `login.Logout` with no envelope — verify correct. The only provable divergence in the group is the deliberate `rt="0"` stub (RV2-01).

**common-station** — Almost entirely faithful. Payload builders (`build_common_code_form`/`build_cache_query`, the `Device` query for `stationinfo`), the station-data/info + app-data/notice cache parsers, the models, and the safety allowlist all match `CommonService`/`CacheService`/`CalendarService` and the `*Dao` DTOs plus the `IntroActivity` bootstrap. The one reportable divergence is the over-strict `schedule.runDt` calendar parser (RV2-02).

**search-schedule** — Highly faithful to the decompiled DAOs. Routes, methods, param names/values, and response mappings for the ScheduleView + seat car/seat inventory research endpoints match. The only provable param-value divergence is the hardcoded `seatAttCd`/`gdNo` in the two seat-map builders (RV2-03).

**seat-fare-traininfo** — **No provable wire divergences** — independently confirms the prior re-verify. Every obfuscated constant in `TrainsInfoService`/`ResearchService`/`ReservationService` was resolved (`trnNoString='trnNo'`, `SEAT_ATT_CD4='txtSeatAttCd4'`, `TRN_GP_CD='txtTrnGpCd'`, `ARV_RS_STN_CD='arvRsStnCd'`, `DPT_DT`/`DPT_TM`) and cross-checked against the real callers (`PriceFareActivity`, `a5/u.java`, `SeatSearchActivity`, `TrainServiceInfoWebViewActivity`, `DirectInquiryActivity`). Two `Key`-omitted behaviors are handled correctly: `actualTrainSchedule` omits `Key` (our client uses `include_common=False`), and the seat DAOs' trailing `sidTest @Field` is null on the production (REAL) server, so omitting it is correct.

**ticket-reservation-read** — No provable wire-level divergence exists in any **implemented** endpoint of the group; the client faithfully mirrors the decompiled DAOs on param names, order, routes, and methods. The one candidate finding (receipt `sale_date` naming trap) was **rejected** — see below.

**account-pass-maas-limousine** — **No provable divergences.** Every payload builder, response parser, model, route, HTTP method (GET vs POST), and per-route field allowlist matches the decompiled DAOs under `network/dao`. Constant-backed field names were fully resolved (`OJrny.TRN_GP_CD`, `C1262b.DPT_DT`/`DPT_TM`/`ARV_RS_STN_CD`/`TRAIN_NO`, `Price2Fare.trnNoString`, `RPsg.PSG_CNT`) and all matched; hardcoded values (`medDvCd='03'`, `regSqno='0'`, gift `qryVal='E'` + `qryDvCd` A/C/F, `jobDvCd` a/b/c, Y/N flags) were each confirmed against the app's actual setter calls.

**safety-transport** — **No provable divergences.** `KORAIL_READ_ONLY_ROUTES` + `KORAIL_EXACT_REQUEST_FIELDS` + `KORAIL_EXACT_REQUEST_FIELD_ORDERS`, the `http.py` transport/envelope, the absence of `netfunnel.py`, and the `BaseRequest` envelope all check out. Several contracts look narrower than the raw Retrofit `@Field` set, but this is **correct** — Retrofit omits null `@Field`/`@Query` params, so the client pins the actual wire request. Each such case was verified at the real call site: `gdMenuLt` (→ only `Device`/`Version`), `gdLst` (3 flows never set the 3 extra fields), `prcFare` (`trnCnt` killed by a no-op setter, confirmed in smali), `sidTest` (null unless non-REAL server).

---

## Rejected / non-bugs

### Overturned this round (submitted, re-verified as NOT a bug)

| Finding | Our ref | Ground-truth ref | Why rejected |
|---|---|---|---|
| `receipt.ReceiptInfo` `sale_date` naming trap | `src/korail_mobile_api/client.py:566`; `read_payloads.py:475-492` (`:482`) | `analysis/jadx/sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:402` (`setH_orgtk_sale_dt(getH_orgtk_ret_sale_dt())`) | The factual observation is **true and confirmed** — the app populates the wire field `h_orgtk_sale_dt` from the ticket's `h_orgtk_ret_sale_dt` (and `h_orgtk_tk_ret_pwd` from `getH_orgtk_ret_pwd()`). But our code is **not wrong**: it emits the correct wire field **name**, order, route, and method — no wire divergence. The `sale_date` param is a pass-through string; the client never *sources* the value, so it cannot emit a wrong one — value-sourcing is caller responsibility, exactly as in the app. There is no typed trap in our own surface: `get_ticket_list` (`client.py:1046`) returns a bare `BaseKorailResponse` with no `h_orgtk_sale_dt` attribute to mis-grab, and the only typed original-ticket date we expose (`DelayDiscountTicket.original_sale_date`) is already correctly mapped from `h_orgtk_ret_sale_dt` (`read_parsers.py:664`). At most a docstring/param-rename ergonomics nicety (the finding's own fix says "rename/document"); self-rated Low; the finding concedes "the wire field NAME is correct". The repo's own audit already logged it as "docstring clarification, not a bug" (`docs/deep-dive/impl-audit-2026-07-22.md:90`). |

### Demoted from the prior re-verify (now a non-bug)

- **Phone-auth continuation POST field set** (prior RV-02). The app re-serializes the **typed** `LoginDao.LoginResponse` (schema fields only; Gson drops server-extra fields and nulls) at `S4/u.java:34`, whereas `session.py:46-49` iterates the **raw** response dict — so our continuation POST could carry extra server-sent fields the app would drop. Marginal: the continuation path is a rare additional-auth (WebView) flow and extra `x-www-form-urlencoded` params are typically harmless. Recorded as an observation, **not counted** as a divergence this round.

### Deliberate non-bugs (correct-by-design; not counted)

- **`parse_base_response` fail-fast on `strResult=='FAIL'`** (`http.py:38-42`) runs before `_login` inspects `strRedirectUrl`. If a redirect/continuation response ever carried `strResult=='FAIL'` it would surface as `KorailAuthError` instead of `KorailAuthContinuationRequired`. No fixture/evidence shows the redirect response uses `strResult=='FAIL'` (additional-auth is a success-with-continuation), so this is **unproven** and not reported.
- **Login form field order** — `idx` emitted before `custId`/`etrPath` differs from the Java `@Field` order; irrelevant for `x-www-form-urlencoded`.
- **`srtgo` divergences we correctly do NOT copy** — `srtgo` posts logout to `com.korail.mobile.common.logout` and adds `Sid` to login; our client follows the decompile (`login.Logout`, no `Sid` on login).
- **`get_common_code(code="")` default** sends `code=[""]` (an empty `code=` field) which the app never does — harmless and only on the zero-arg default; the real bootstrap path (`session.get_login_crypto_info`) sends the full code list.
- **`train_no.zfill(5)`** in `build_seat_car_form`/`build_seat_inventory_form` technically differs from the app's raw `h_trn_no` (`x4/b.java:13`, `a5/u.java:296`), but the server returns `h_trn_no` already 5-digit zero-padded (`'00123'` in fixtures; `srtgo` stores it raw), so no observable divergence.
- **Curated response subsets** — several parsers intentionally expose a subset of response fields while preserving the full row under `raw` (e.g. trip-menu `ContentInfo` drops `cmtrKndCd`/`passType`/`passData`; pass menu keeps them). Deliberate design, not a mis-parse.
- **`isArrow` boolean `@Field`** (`ResearchService.java:59`, `BusReservationService.java:33`) — `safety.py:698` rejects value types outside `{str,int}` and Python `bool` is not `type` `int`, so a Python `bool` would be rejected; but the app sends `isArrow` as the string `'true'`/`'false'` on the wire, so the client must pass a string — consistent with the app. Payloads-layer concern, no wire divergence.
- **`login.Logout` allowlisted with no caller** — an unused-but-correct allowlist entry. Likewise the extra order variant for `copt.gdReqQry.do` (`('Device','Version')` only, `safety.py:451`) sends no wrong request because the form builder decides the payload. Not reportable.
- **Dead / harmless mappings** — several optional `TrainSummary` fields map to keys absent from `RsvInquiryResponse.TrainInfo` (`h_car_tp_cd`, `h_trn_gp_nm`, `h_std_rest_seat_cnt`, `h_fst_rest_seat_cnt`, `h_rsv_wait_ps_cnt`) and always resolve to `None`. `get_rsv_product_inquiry` builder `_build_product_train_inquiry_form` (`seatMovie.ScheduleViewSpecial`) has correct `@Field` names but is **unreachable dead code** — no client method/route invokes it, so it cannot emit a wrong request.

### Forward-compat / robustness notes (unproven; not counted)

Strictness gaps where our parser is stricter than the app's tolerant Gson model, but **no fixture/evidence shows the server ever omits/null-encodes the field** — flagged as forward-compat risk only:

- `parse_seat_inventory_response` marks `intg_msg`/`intg_msg_cd`/`vz_msg_dv_cd` required (`parsers.py:1018-1026`) while `SearchSeatListDao.Seat` declares them nullable `String`.
- `parse_train_schedule_response` requires `dlayList` as a list and `runDt1`/`trnNo1` non-empty (`parsers.py:555-559,698-716`) while `TrainServiceInfoWebViewActivity.java:194` tolerates a null `dlayList`. All seat/schedule fixtures carry full valid values.
- `parse_reservation_history_response` accepts only `h_msg_cd 'P100'` as the empty/no-results code (`read_parsers.py:1058-1063`), whereas `srtgo` treats `{P100, WRG000000, WRD000061, WRT300005}` as no-results for the same `ReservationView` call (`ktx.py:500-501,964-993`) and this repo's own test asserts `WRG000000='조회 결과 없음'` (`test_http.py:206`). If an empty-reservation member gets a non-`P100` no-results code, `get_reservation_history` would raise `KorailAppError` instead of returning `[]`. Worth confirming against a live empty response and widening `accepted_empty_codes` if needed.

### Coverage gaps (unimplemented, therefore un-auditable — not divergences)

- **N-card / discount-card endpoints** — `getNCardHistory` (`ticket.dcntCrdUseQry.do`), `getNCardSchedultView` (`research.dcntCrdScheduleView.do`), `dcntCrdInfo`/`dcntCrdExtn` are **not implemented** anywhere in `src/` (a grep for `dcntcrd`/`ncard`/`discount-card` returns nothing). No request builder, route, or parser — nothing to audit.
- **`refunds.SelTicketInfo` / `getTicketDetail`** — not implemented (POST with `h_orgtk_ret_sale_dt`/`h_orgtk_wct_no`/`h_orgtk_sale_sqno`/`h_orgtk_ret_pwd`/`h_purchase_history`, `RefundService.java:23-25`); `srtgo` uses it (`ktx.py:167,949`) to expand per-ticket seat info. Documented as intentional in `docs/deep-dive/full-api-analysis-2026-07-20.md:2829-2832`.
- **`certification.ReservationList` / `inquiryTicketRsv`** — not implemented (GET `Device`/`Version`/`Key`/`hidPnrNo`, `CertificationService.java:45-46`); `srtgo` uses it as the per-PNR reservation seat lookup (`ktx.py:170,1002`). This is a **distinct** endpoint from the implemented `product.ReservationList` — do not confuse them.
- **Points / mileage reads** — the app exposes `xPoint` DAOs (`KorailPointInquiryDao`, `MileageInquiryDao`, `PointInquiryDao`, `LPointDao`, `OKCashbagCertDao`) and mileage DAOs (`AcpnMlgSpecDao` at `mileage.acpnMlgSpec.do`, `AcpnMlgNotiDao`), but none has a client counterpart — no `get_*` method, payload, or parser. Absence, not divergence; the one group area with no coverage to audit.
- **Stale fixture** — `tests/fixtures/train_calendar.json` uses the model key `days` (not the wire key `runningCalendar`) and is fed to no parser; the calendar parser is exercised by `raw_typed_train_calendar.json`.
