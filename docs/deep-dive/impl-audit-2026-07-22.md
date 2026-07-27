# Korail Client Implementation Audit — 2026-07-22

**Target app:** `com.korail.talk` v6.5.0 (decompiled ground truth under `analysis/jadx` + `analysis/apktool`)
**Under audit:** the read-only Python client in `src/korail_mobile_api/`
**Author:** FABLE
**Ground-truth rule:** the decompiled Korail app is authoritative; where a client test bakes in a divergence, the test is treated as wrong, not the app.

This audit consolidates seven scoped sub-audits (auth/session/crypto, common-station, search-schedule, seat-fare-traininfo, ticket-reservation-read, account-pass-maas-limousine, safety-transport). Each finding carries both-sides `file:line` citations: where our client diverges, and where the app proves the correct behavior.

**Evidence style.** The decompiled app is a third party's copyrighted work and is not redistributed here (`analysis/` is untracked). So findings cite it by `file:line` and *describe* what was observed there — the fields, the routes, the control flow — instead of pasting its Java or smali. The citation is what makes a claim checkable: anyone who decompiles the same APK build can open the same line. Wire-level names (route paths, `@Field`/`@Query` keys, constant values) are quoted as short literals because they are the interface the client must match, and the client would be unusable without them.

## Headline

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 2 |
| Low | 2 |
| **Total real divergences** | **4** |

One additional finding (`prcFare` missing `trnCnt`) was submitted by one sub-audit but **overturned during consolidation** — direct decompile evidence proves the app never sends `trnCnt`, so the client's omission is correct. It is documented under [Rejected / non-bugs](#rejected--non-bugs), not counted above.

No High-severity divergences were found: every route, HTTP method, envelope constant, and request field *name/value* in scope matches the app. The four confirmed divergences are all about **presence** (fields we send that the app omits, or response fields we require that the app's model does not define) — not wrong values.

---

## Prioritized bug table (High → Low)

| # | Severity | Area | Our ref | Ground-truth ref | Description | Fix |
|---|---|---|---|---|---|---|
| AUD-01 | Medium | DynaPath token — `rt` timing field | `src/korail_mobile_api/dynapath.py:303` | `analysis/jadx/.../kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java:34`; `B/C1229b.java:76-91,114-127` | Token payload hardcodes `("rt","0")`. The SDK always calls `C1229b.a(currentTimeMillis)` before building the token, appending a delta (`ts − previousTs`, first-call `previousTs = app_start_ts`) that serializes as `rt`. The app never emits `rt=0`; it emits `rt=<ts − app_start_ts>` then accumulates up to 5 deltas. `rt` is precisely the anti-automation timing signal, so our constant encodes a different token body. | On a cold token emit `rt = str(ts − int(app_start_ts))`; support accumulating up to 5 deltas for multi-request sessions instead of a fixed `"0"`. |
| AUD-02 | Medium | `actualTrainSchedule` (train-delay) response parser | `src/korail_mobile_api/parsers.py:554` | `analysis/jadx/.../trainsInfo/TrainScheduleDao.java:12-90` (`TimeInfo`); smali `TrainScheduleDao$TimeInfo.smali:18-44` | `parse_train_schedule_response` marks `stopRsStnCd` (station_code, :554), `stnConsOrdr` (station_construction_order, :566) and `runOrdr` (run_order, :572) as **required, non-empty**. The app's `TimeInfo` model declares only `stopStnNm` among station fields (plus time/delay fields) — no `stopRsStnCd`, `stnConsOrdr`, or `runOrdr`. A response conforming to the app contract makes our parser raise `KorailProtocolError` per stop, breaking `get_train_schedule()`. Independently flagged by two sub-audits (search-schedule, seat-fare-traininfo). | Downgrade the three fields to `_typed_optional_string` (keep `stopStnNm` required); reconsider the `dlayList` non-empty requirement so a valid empty delay list does not raise. Re-validate against a captured SUCC response. |
| AUD-03 | Low | Login POST — empty `custId` / `etrPath` | `src/korail_mobile_api/session.py:149-150` | `analysis/jadx/sources/k5/b.java:102-113`; `.../dao/login/LoginService.java:17-19` | `login()` defaults `cust_id=""`/`etr_path=""`; the `None`-filter in `_login` drops only `None`, so the wire body carries `custId=&etrPath=`. The app's member login (`k5/b.java` `B0`) leaves `custId`/`etrPath` null, so Retrofit's `@Field` omits them entirely — the app sends **neither** field, we send **both** as empty. (The client's own test asserts their presence, baking in the divergence.) | Default `cust_id`/`etr_path` to `None` so the existing filter drops them; emit `custId`/`etrPath` only when a real value is supplied (EasyLogin / booking-entry paths). Fix the test accordingly. |
| AUD-04 | Low | `common.code.do` payload — empty `departDate`/`arrivalDate`/`holidayYn` | `src/korail_mobile_api/payloads.py:229-231` | `analysis/jadx/.../ui/intro/IntroActivity.java:336-363`; `analysis/jadx/sources/retrofit/RequestBuilder.java:316-335` | `build_common_code_form` always emits `departDate=''`, `arrivalDate=''`, `holidayYn=''`. On the intro/login bootstrap fetch these `@Field`s are null in `CommonCodeRequest` (`IntroActivity` never calls their setters), and Retrofit 1 skips null `@Field` values, so the app omits all three keys. We send three params the app does not. Path is used by `session.get_login_crypto_info` and `get_common_code()`. Impact ~nil (server lenient) but a provable wire divergence. | Include `departDate`/`arrivalDate`/`holidayYn` only when a real value is supplied (drop when empty); optionally expose them as params for holiday-lookup callers that do set them. |

---

## Detailed findings

### AUD-01 — DynaPath token hardcodes `rt=0` (Medium)

- **Our ref:** `src/korail_mobile_api/dynapath.py:303` — `("rt", "0")` in the token field list.
- **Ground-truth ref:** `analysis/jadx/sources/kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java:34` (`generate()` always calls `c1229b.a(System.currentTimeMillis())` immediately before building the token); `analysis/jadx/sources/B/C1229b.java:76-91` (delta computation) and `:114-127` (`ts`/`rt` serialization).

`C1229b.a(long)` computes `delta = currentMillis − previousTs`. On the first request `previousTs` falls back to the app-start timestamp (`f12263h`), so the first delta is `ts − app_start_ts` — a positive number, never `0`. Deltas accumulate in a deque that `C1229b.a()` serializes as `rt` (up to 5 accumulated values). Thus the app emits `rt=<ts − app_start_ts>` on the first macro request and grows the list on subsequent ones; it **never** emits `rt=0`. Our fixed `rt=0` encodes a structurally different token body, and `rt` is exactly the anti-automation timing signal the SDK exists to carry.

**Note on intent:** this looks deliberate in our codebase (tests named `*_fixed_rt_reference`; `DynapathTokenSettings` raises on `recent_request_deltas`). It is still a divergence from the decompiled SDK, hence reported. **Mitigating context:** the app only attaches the DynaPath token when `IS_MACRO_ACTIVE` (`ExecuteDao.java:26`); ordinary app traffic sends no token, and our client default `dynapath.enabled=False` matches that — so this only bites if a caller turns DynaPath on.

**Fix:** on a cold token emit `rt = str(ts − int(app_start_ts))` (matching `a(long)` first-call semantics); ideally support accumulating up to 5 deltas across a multi-request session rather than a fixed `"0"`.

### AUD-02 — `actualTrainSchedule` parser requires fields absent from the app model (Medium)

- **Our ref:** `src/korail_mobile_api/parsers.py:554` (`station_code`←`stopRsStnCd`), `:566` (`station_construction_order`←`stnConsOrdr`), `:572` (`run_order`←`runOrdr`) — all `_typed_required_string(non_empty=True)`.
- **Ground-truth ref:** `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java:12-90` — `TimeInfo` (the item type of `dlayList`, returned by `TrainsInfoService.getTrainSchedule`) declares only `stopStnNm` among station fields, plus time/delay fields (`actArvDt/Tm`, `actDptDt/Tm`, `arvDt/Tm`, `dptDt/Tm`, `actArvDlayTnum`, `expnArvDlayTnum`, `expnDptDlayTnum`, `rgulFlg`, `saodFlg`). Confirmed in smali `TrainScheduleDao$TimeInfo.smali:18-44`. No `stopRsStnCd`, `stnConsOrdr`, or `runOrdr`.

The app's own model never reads a stop station code / construction order / run order. If a real SUCC response omits these (as the model implies), `get_train_schedule()` raises `KorailProtocolError` for every stop. The existing fixture `tests/fixtures/raw_typed_train_schedule.json` was hand-fabricated to include these keys, so it masks the risk; `docs/api-status-by-service.md:541` shows the endpoint was never validated against a real SUCC body (only the `EVZ000048` "train does not exist" error).

**Confidence caveat:** Gson silently ignores unmodeled JSON fields, so their *absence on the wire* is strongly implied by the model but not 100% capturable from the decompile alone. The **schema divergence is proven** regardless: we require fields the app's model does not define, which is strictly riskier than the app contract.

**Independent confirmation:** raised separately by the search-schedule audit and the seat-fare-traininfo audit (same `ourRef`, same three fields) — consolidated here as one finding.

**Fix:** make `station_code`, `station_construction_order`, `run_order` optional via `_typed_optional_string` (keep `station_name`/`stopStnNm` required). Reconsider the `_typed_required_non_empty_list('dlayList')` so a valid-but-empty delay list does not raise. Re-validate against a captured successful response.

### AUD-03 — Login POST sends empty `custId` / `etrPath` (Low)

- **Our ref:** `src/korail_mobile_api/session.py:149-150` — form maps `"custId": cust_id`, `"etrPath": etr_path`; `login()` defaults both to `""`, and the filter at `session.py:155` keeps empty strings (drops only `None`).
- **Ground-truth ref:** `analysis/jadx/sources/k5/b.java:102-113` (member login `B0` sets only `loginId`, `loginPw`, `loginType`, `checkValidPw`, `idx`); `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17-19` (`@Field` params, null-omitted by Retrofit).

The app leaves `custId`/`etrPath` null on normal member login, so Retrofit omits both. Our wire body carries `custId=&etrPath=`. Functional impact is negligible (empty vs absent optional fields), but it is a provable divergence, and the client's `test_login_infers_email_input_flag_and_omits_unset_optional_fields` even asserts their presence — the test encodes the bug.

**Fix:** default `cust_id`/`etr_path` to `None` so the existing `None`-filter drops them, matching Retrofit's null omission; emit `custId`/`etrPath` only when a real value is supplied (EasyLogin / booking-entry flows). Update the test to expect their absence.

### AUD-04 — `common.code.do` sends empty `departDate`/`arrivalDate`/`holidayYn` (Low)

- **Our ref:** `src/korail_mobile_api/payloads.py:229-231` — `build_common_code_form` hardcodes `"departDate": ""`, `"arrivalDate": ""`, `"holidayYn": ""`.
- **Ground-truth ref:** `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:336-363` (the intro/bootstrap fetch calls only `setCodeList`/`setOSVersion`/`setDeviceWidth`/`setDeviceHeight` — never `setDepartDate`/`setArrivalDate`/`setHolidayYn`); `analysis/jadx/sources/retrofit/RequestBuilder.java:316-335` (case 8: `if (obj != null)` guards `formBody.addField`, so null `@Field`s are skipped).

For the bootstrap fetch those three params are null in `CommonCodeRequest`, so the app omits the keys entirely; we send three empty-string params. This path backs both the login bootstrap (`session.get_login_crypto_info`) and the public `get_common_code()` helper. Impact is almost certainly nil (the server is lenient — srtgo's login succeeds sending only `code`), but it is a provable presence divergence.

**Fix:** include `departDate`/`arrivalDate`/`holidayYn` only when a real value is supplied (drop the keys when empty); optionally expose them as parameters for holiday-lookup callers that legitimately set them.

---

## Verified correct

The following were audited against the decompiled DAOs/services/constant classes and confirmed to match on route, HTTP method, request field names/values, envelope handling, and response parsing. No divergences beyond those listed above.

- **auth-session-crypto** — `crypto.py` (password transform + `Sid`), `dynapath.py` token *structure* (v1.0.3), `session.py` (login/logout/session/crypto bootstrap), `http.py` envelope + cookies, and the safety route table. Ground truth: `LoginDao`/`LogoutDao`/`LoginService`, `S4/C0812l`, `F4/a`, `B/C1229b` + `kr.scripters.dynapath` SDK, `l1/AbstractC5980b` + `C5979a`, `CommonService`/`CommonCodeDao`, `BaseRequest`, `KTApplication`, `S4/u`. (Two divergences: AUD-01, AUD-03.)
- **common-station** — `common.code.do`, `stationinfo`, `stationdata`, `MobileService.cache`, and `schedule.runDt` calendar (payload builders, parsers, models). All field names/routes/methods/constants match the decompiled DAOs/smali. (One divergence: AUD-04.)
- **search-schedule** — every endpoint in `ResearchService` / `SeatMovieService` / `CalendarService` verified clean. (The `actualTrainSchedule` parser issue belongs to `TrainsInfoService`; see AUD-02.)
- **seat-fare-traininfo** — `fresScar`, `prcFare` (`getPrice2Fare`), `chtnStn`, seat DAOs, and `seatMovie.ScheduleView` (the "seat page", implemented as `client.search_trains`) verified. `build_price_fare_quote_form` sends `txtMenuId` + `chtnDvCd` + the comma-joined `Price2FareParams`, matching the app once `trnCnt` is understood to be app-omitted (see Rejected). (One divergence: AUD-02.)
- **ticket-reservation-read** — all in-scope reads match the decompiled DAOs on route, method, request fields, and response parsing. **No divergences.** `get_ticket_receipt` sends the correct field name (`h_orgtk_sale_dt`), though callers must pass the ticket's *return* sale date per `TicketReceiptActivity.java:402` (docstring clarification, not a bug).
- **account-pass-maas-limousine** — ~28 in-scope reads (account/next-reads, pass schedule, MaaS/cart, limousine, points/mileage) verified against the Retrofit DAOs, with wire-constant values confirmed (e.g. `C1262b.TRAIN_NO='txtGoTrnNo'`, `DPT_DT='dptDt'`, `ARV_RS_STN_CD='arvRsStnCd'`, `OJrny.TRN_GP_CD='txtTrnGpCd'`, `RPsg.PSG_CNT='psgCnt'`, `K4.d DIRECT/TRANSFER='1'/'2'`) and caller literals (`medDvCd='03'`, `regSqno='0'`, `qryVal='E'`). **No divergences.**
- **safety-transport** — the full allowlist contract verified against Retrofit service interfaces, DAO `executeDao` bodies, the `b5.C1262b`/`OJrny`/`OSeat`/`OPsg`/`RPsg`/`Price2Fare` constant classes, `BaseRequest`/`BaseResponse`, and `RequestBuilder` null-handling. Every allowlisted route exists with the correct method; every `KORAIL_EXACT_REQUEST_FIELDS` set matches the actual wire field set. **No divergences.** Korail's bundled NetFunnel is confirmed UI-only/vestigial (never attaches a queue token to API requests); the client correctly wires none. DynaPath is the real per-request mechanism (`ExecuteDao.java:47` sets `x-dynapath-m-token`; `BaseDaoHelper.java:59` reads `DynaPath-Result`), and `constants.py:34 DYNAPATH_HEADER_NAME` matches.

---

## Rejected / non-bugs

### REJECTED — `prcFare` "missing `trnCnt`" is a false positive (overturned during consolidation)

One sub-audit (seat-fare-traininfo) reported that `build_price_fare_quote_form` omits a "required" top-level `trnCnt` field and proposed inserting `("trnCnt", str(len(request.legs)))` at `read_payloads.py:991` plus updating the safety scaffolds. **This is refuted by direct decompile evidence and is NOT a bug — applying the fix would introduce a divergence.**

- **Our ref:** `src/korail_mobile_api/read_payloads.py:989-991` (emits `txtMenuId` + `chtnDvCd` + `Price2FareParams`, no `trnCnt`).
- **Ground-truth ref:** `analysis/jadx/.../trainsInfo/Price2FareDao.java:170-172` and smali `Price2FareDao$Price2FareRequest.smali:149-162`.

The `@Field("trnCnt")` param does exist on `TrainsInfoService.getPrice2Fare` (`TrainsInfoService.java:26`) and `PriceFareActivity.java:64` does call `setTrnCnt(...)` — which is what the sub-audit saw. But the setter is a **self-assignment no-op**.

What the decompile shows, described rather than reproduced (third-party app code; see "Evidence style" below):

- **Java (`Price2FareDao.java:170-172`).** The one-statement body of `setTrnCnt(String)` assigns the *field* to itself. The parameter is never referenced on the right-hand side, so it is discarded.
- **Smali (`Price2FareDao$Price2FareRequest.smali:149-162`).** The same three instructions confirm it at bytecode level and rule out a decompiler artefact: the method loads the existing `trnCnt` field into the register that held the incoming argument (`iget-object` into `p1`), stores that register straight back into the same field (`iput-object` from `p1`), and returns. Overwriting the parameter register before it is used is why the argument cannot reach the field.

Either way the incoming value is read over by the field's own value before being written back, so `trnCnt` stays `null` no matter what the caller passes. Retrofit's `@Field` skips null values (`RequestBuilder.java` case 8), so **the app never transmits `trnCnt`**. The client's omission is therefore correct, and adding the field would make us diverge. This conclusion is independently corroborated inside the provided findings by the **account-pass-maas-limousine** notes ("`setTrnCnt` is a decompiled no-op … the app never actually sends `trnCnt`") and the **safety-transport** notes ("`trnCnt` [nulled by the app's own self-assignment bug in `Price2FareDao.setTrnCnt`]"). The current `KORAIL_EXACT_REQUEST_FIELDS`/`_FIELD_ORDERS` entries for `trn.prcFare.do`, which omit `trnCnt`, are **correct as-is**.

### Deliberate / benign observations (not divergences)

These were considered and intentionally not filed as bugs:

- **DynaPath random-text alphabet.** Client uses `A-Z0-9` (36 chars) vs the app's `a-zA-Z0-9` (62 chars, `C1229b.java:164`). The 4 random chars are opaque to the server and ours is a strict subset, so the token stays structurally valid. Not a functional divergence.
- **DynaPath only on macro traffic.** The app attaches the token only when `IS_MACRO_ACTIVE` (`ExecuteDao.java:26`); normal traffic sends none, matching our default `dynapath.enabled=False`. (Context for AUD-01, which only manifests when DynaPath is enabled.)
- **Login continuation/redirect post-data source.** The app re-serializes the `LoginResponse` Gson model (declared, non-null fields only); `build_login_authentication_post_data` forwards all raw response keys. Differs only when the server returns undeclared keys, the target is a web-form POST, and the flow is rarely hit — low impact.
- **`infer_login_input_flag` heuristic.** Content-based inference vs the app's explicit tab selection; a 10/11-digit membership number starting with `01` could be misclassified as phone (`'4'`). Callers can override via `input_flag` — a documented heuristic limitation, not a wire divergence.
- **Passenger-type breakdown.** `build_train_search_form` sends `txtPsgFlg_1=passengers`, `_2.._5=0`, whereas the app splits adult/teenager/guide-dog vs child vs senior vs disabled tiers (`U4.b.getRsvInquiryRequest:173-177`). Correct for an adults-only read client; only limits passenger-type breakdowns.
- **Hardcoded seat class/attribute.** `build_seat_car_form`/`build_seat_inventory_form` fix `psrmClCd='1'` and `seatAttCd='015'` (general class / general seat), matching the srtgo reference. A deliberate scope limitation, not a wire divergence.
- **Safety allowlist permissiveness.** `gift.gdLst.do` permits a 5-field order variant the app never emits, and `copt.gdMenuLt.do` is restricted to `{Device,Version}`. Neither causes a wrong/malformed request — harmless permissiveness / coverage limitation.
- **Not-implemented reads (no divergence — absent code cannot send wrong data):** `refunds.SelTicketInfo`, `certification.ReservationList` (distinct from our correctly-implemented `product.ReservationList`), `TrainsInfoService.getPriceFare` (`TrainCharge`), `getTourTrainInfo` (`TourTrainSpecialRoom`), and the `dcntCrd*`/NCard endpoints. Candidates for future work; none is a current bug.

### Empirically-derived empty-code classifications (flagged, not bugs)

Two response empty-code mappings are not backed by DAO-level ground truth (no server fixtures): discount-coupon treats `WRG000000` as empty-success (`read_parsers.py:689`), and reservation-history treats `P100` as empty (`read_parsers.py:1060`). `parse_pass_schedule_response` raising `KorailAppError` on `WRG000000` is **consistent** with the app, which classifies `WRG000000` as FAIL internally (routes to `onReceiveError`, only suppressing the dialog). Recorded so maintainers know this is the one area derived empirically rather than from the decompile.

---

## Methodology note

- **Ground truth** is the decompiled app (`analysis/jadx` for readability, `analysis/apktool` smali for byte-level confirmation of ambiguous cases such as the `setTrnCnt` no-op). Where a client test asserts a behavior that contradicts the app, the test is treated as encoding the bug (AUD-03, AUD-04).
- **No captured raw JSON responses** exist under `analysis/raw` — only the extracted APK. Response-shape claims (AUD-02) therefore rest on the app's Gson DAO models as the contract. Gson silently drops unmodeled fields, so a model's silence about a field strongly implies but cannot 100% prove its wire absence; each such caveat is stated inline.
- **Retrofit null-omission** (`RequestBuilder.java`: null `@Field`/`@FieldMap`/`@Query` values are skipped) is the crux of three findings — it is why the app omits fields our client sends as empty strings (AUD-03, AUD-04), and why the `trnCnt` no-op setter results in the app never sending that field (Rejected).
