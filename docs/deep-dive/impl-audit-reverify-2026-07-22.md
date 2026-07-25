# Korail Client Implementation Audit — Re-verify — 2026-07-22

**Target app:** `com.korail.talk` v6.5.0 (decompiled ground truth under `analysis/jadx` + `analysis/apktool`)
**Under audit:** the read-only Python client in `src/korail_mobile_api/`
**Author:** FABLE
**Ground-truth rule:** the decompiled Korail app is authoritative. Where a client test bakes in a divergence, the test is treated as wrong, not the app; where `srtgo` diverges from the decompile, the decompile wins.

This is the **adversarial re-verify** pass over the seven scoped sub-audits (auth/session/crypto, common-station, search-schedule, seat-fare-traininfo, ticket-reservation-read, account-pass-maas-limousine, safety-transport). Every candidate divergence was re-checked against the decompile (and, where relevant, apktool smali) before being counted. Findings that did not survive that check are listed under [Rejected / non-bugs](#rejected--non-bugs) and are **not** counted as real. Each entry carries both-sides `file:line` citations: where our client diverges, and where the app proves the correct behavior.

## Headline

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 0 |
| Low | 2 |
| **Total real divergences** | **2** |

Both confirmed divergences live in **peripheral / telemetry paths** of the auth-session-crypto group, and both have **unproven server impact** — a compliant server would still accept the affected request. Six sub-audit submissions were **overturned during re-verify** (one each in search-schedule, seat-fare-traininfo, safety-transport; two in ticket-reservation-read) — direct decompile or smali evidence proves our client already matches the app. They are documented under [Rejected / non-bugs](#rejected--non-bugs), not counted above. Two groups (common-station, account-pass-maas-limousine) were clean.

No High- or Medium-severity divergences survived. Every route, HTTP method, envelope constant, and request field *name/value* in scope matches the app; the two confirmed lows are about **content** (a hardcoded telemetry value, and an over-broad field set forwarded on one continuation POST), not wrong routing or wrong values on any audited request.

---

## Prioritized bug table (High → Low)

| # | Severity | Area | Our ref | Ground-truth ref | Description | Fix |
|---|---|---|---|---|---|---|
| RV-01 | Low | DynaPath token — `rt` timing field | `src/korail_mobile_api/dynapath.py:303` | `analysis/jadx/sources/B/C1229b.java:76-127` (with `DynaPathMobileSDK.java:33-35`) | The DynaPath token payload hardcodes `rt` to the literal `"0"`. In the real SDK `rt` is the deque of inter-request timing deltas: `DynaPathMobileSDK.generate()` calls `c1229b.a(System.currentTimeMillis())` immediately before building the token, and `C1229b.a(long)` computes `delta = j9 − (f12264i ?? f12263h)` and appends it to the deque. On the first/typical token that delta is `firstCallTime − appStartTime` — a positive value, **never 0** — emitted as `rt=<delta>`. Our `0` never matches what the app would send. Impact is uncertain: `rt` is anti-abuse timing telemetry and is **not** part of key derivation (`dyn_key = sv+rand+ts` uses `ts`, not `rt`), so a server that only structurally decodes the token would still accept it — but a heuristic that inspects `rt` plausibility could flag `rt=0`. | Model `rt` as at least one realistic positive delta (e.g. `ts − app_start_ts`) instead of the constant `"0"`, or make it caller-supplied; ideally emit the deque of up to 5 deltas as repeated `rt=` values to mirror `C1229b.a()`. |
| RV-02 | Low | Login phone-auth continuation POST — over-broad field set | `src/korail_mobile_api/session.py:46-49` | `analysis/jadx/sources/S4/u.java:33-44` | `build_login_authentication_post_data()` iterates the **full raw server JSON** (`response.raw`), appending every key except `strResult`/`h_msg_txt` to the phone-auth continuation POST body. The app instead serializes the **typed** `LoginDao.LoginResponse` via Gson (`q.toJson(loginResponse)`) and iterates that, so it forwards only the ~30 declared `LoginResponse` fields (plus `h_msg_cd`) and drops null fields. If the login response carries JSON keys beyond the `LoginResponse` schema, our continuation POST forwards extra params the app would omit. Scope: the phone-auth (`strAthnFlg`/`strRedirectUrl`) continuation flow only; the `callLogin`/`memId`/`inputFlg` prefix and the skip-set (`strResult`, `h_msg_txt`) are correct, and downstream web-endpoint impact is unproven. | Restrict the iterated fields to the known `LoginResponse` schema (`LoginDao.LoginResponse` fields) rather than the entire raw envelope, to exactly mirror `q.toJson(loginResponse)`. |

---

## Detailed findings

### RV-01 — DynaPath token hardcodes `rt=0` (Low)

- **Our ref:** `src/korail_mobile_api/dynapath.py:303` — `("rt", "0")` in the token field list.
- **Ground-truth ref:** `analysis/jadx/sources/B/C1229b.java:76-91` (delta computation) and `:119-127` (`rt` serialization); `analysis/jadx/sources/kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java:33-35` (`generate()` calls `c1229b.a(System.currentTimeMillis())` immediately before building the token).

`C1229b.a(long j9)` computes `delta = j9 − (f12264i ?? f12263h)`; on the first request the previous-timestamp field falls back to the app-start timestamp, so the first delta is `firstCallTime − appStartTime` — positive, never `0` — and is appended to a deque that serializes (up to 5 entries) as `rt`. `DynaPathMobileSDK.generate()` always primes this with `c1229b.a(currentTimeMillis)` right before assembling the token, so the app emits `rt=<positive delta>` on the first macro request and grows the list on subsequent ones. It **never** emits `rt=0`; our fixed constant encodes a different token body.

**Impact / caveat:** `rt` is anti-abuse *timing* telemetry and is **not** part of the token key derivation — `dyn_key = sv + rand + ts` consumes `ts`, not `rt`. A server that only structurally decodes the token would still accept ours. The realistic risk is a server-side heuristic that inspects `rt` for plausibility, where a constant `rt=0` is an obvious tell. This is a real content divergence from the decompiled SDK; the uncertain server reaction is why it is Low, not higher.

**Fix:** on a cold token emit `rt = str(ts − int(app_start_ts))` (matching `a(long)` first-call semantics), or make `rt` caller-supplied; ideally accumulate up to 5 deltas across a multi-request session and emit them as repeated `rt=` values, mirroring `C1229b.a()`.

### RV-02 — Phone-auth continuation POST forwards the whole raw envelope (Low)

- **Our ref:** `src/korail_mobile_api/session.py:46-49` — `build_login_authentication_post_data()` iterates `response.raw` and appends every key except `strResult`/`h_msg_txt`.
- **Ground-truth ref:** `analysis/jadx/sources/S4/u.java:33-44` — the app builds the continuation body from `q.toJson(loginResponse)` (a serialized `LoginDao.LoginResponse`), then iterates that JSON object.

Because the app serializes the **typed** `LoginResponse` object, only the ~30 declared fields (plus `h_msg_cd`) can appear, and Gson drops null fields. Our client iterates the **raw** server envelope, so any JSON key the server returns beyond the `LoginResponse` schema is forwarded as an extra param on the continuation POST. The prefix (`callLogin`/`memId`/`inputFlg`) and the skip-set (`strResult`, `h_msg_txt`) already match the app; only the *source* of the iterated fields diverges.

**Scope / caveat:** this affects only the phone-auth (`strAthnFlg`/`strRedirectUrl`) continuation flow. Whether the downstream web endpoint rejects or ignores extra params is unproven — hence Low. The divergence in *what set of fields is forwarded* is the provable defect.

**Fix:** restrict the iterated fields to the known `LoginResponse` schema (the `LoginDao.LoginResponse` fields) rather than the entire raw envelope, exactly mirroring `q.toJson(loginResponse)`.

---

## Verified correct

Areas that were audited and **confirmed to match ground truth** (reported here so the clean surface is on record, not just the divergences):

**auth-session-crypto** — The just-landed DynaPath and logout changes are correct: header name, 6-path allowlist, envelope field order/values, `sv=v1.0.3`, `i8=161`/`i9=30`/`i10=2`, table index 1, prime table, prefix, and the encoder all match ground truth. Logout is GET with no params and correctly **off** the DynaPath allowlist. Password crypto (`C0812l`/`F4.a`), `Sid`, and login-success detection via `h_msg_cd ∈ {IRZ000001, S200}` (not `strResult=='SUCC'`) are correct.

**common-station** — No wire divergences. `common.code.do`, `stationinfo`, `stationdata`, `MobileService.cache`, and `schedule.runDt` all match the decompiled DAOs (`CommonService`/`CalendarService`/`CacheService` + the `CommonCode`/`StationInfo`/`StationData`/`TrainCalendar`/`AppData`/`Notice` DAOs) and the `CommonCodeRequest` caller in `IntroActivity`: routes, HTTP methods, param names/values, response field maps, and safety classification all correct.

**search-schedule** — Request routes, methods, param names/values, and response field mappings for the ScheduleView + seat car/seat inventory research endpoints match ground truth; safety classification correct.

**seat-fare-traininfo** — `TrainsInfoService` (`fresScar`, `prcFare`, `TrainCharge`, `chtnStn`, `TourTrainSpecialRoom`, `actualTrainSchedule`) and the seat research DAOs (`TrainResearch`/`SearchCarList`, `TResidualSeatsResearch`/`SearchSeatList`) match. `prcFare` correctly sends `chtnDvCd=str(len(legs))` and comma-joined FieldMap keys, matching `PriceFareActivity`.

**ticket-reservation-read** — A well-audited group with no divergences. `MyTicketList`, `receipt.ReceiptInfo`, `ticketDupCheck`, `ReservationView`, `product.ReservationList`, `dlvRcvCust`, `pbpAcepSpec`, `plfNo`, `rcntDlvHst` all match their DAOs on request forms, HTTP methods, routes, `tkRetNo` construction, response field maps, and safety classification. Our client correctly follows the decompile where `srtgo` does not (POST `MyTicketList` / GET `ReservationView`; real `txtDeviceId` = advertising ID / SSAID).

**account-pass-maas-limousine** — No divergences. Every in-scope route, method (POST vs GET), `Key`/`Sid` presence, request field name+value, and response field map matches the decompiled Retrofit services and DAO models. Confirmed points: `tripMenu`/MaaS `gdReqQry`/`LimousineScheduleView` correctly omit `Key`; MaaS `current` mode omits `qryDtFrom`/`qryDtTo`; limousine `service_code → tmGpCd` vs seat/schedule `trnGpCd`/`txtTrnGpCd`; `custTripInfo`'s `reqSqno → regSqno` wire name with `medDvCd='03'`/`regSqno='0'`; product-detail wire name `txtVrRsNo`.

**safety-transport** — App version `250601003` confirmed (`BaseRequest.java:9,16` == `constants.py:3`). All GET/POST methods across the 55 allowlisted routes match the DAO annotations; every constant-based `@Field` name resolves. **NetFunnel:** the app contains NHN NetFunnel as a client-side waiting-room, but it injects nothing into any Korail API request (the success callback fires the identical DAO with the same request object; `NetfunnelDao.runRunner` only dismisses loading dialogs; no inquiry/reserve `@Field` set carries a NetFunnel token/header/cookie) — so our omission changes only queueing UX, and our client is contract-correct. **DynaPath** (`x-dynapath-m-token`) is correctly wired with the sensitive-endpoint allowlist, distinct from NetFunnel. `login.Login` (POST) / `login.Logout` (GET) are correctly in the read allowlist as session management, not booking/payment mutations.

---

## Rejected / non-bugs

### Overturned sub-audit submissions (re-verified as NOT bugs)

Each of these was submitted by a sub-audit and **overturned** with direct decompile/smali/fixture evidence. Both-sides citations retained.

| Finding | Our ref | Ground-truth ref | Why rejected |
|---|---|---|---|
| `TrainSummary.total_passenger_count` parsed strict-int (`totPsgCnt`) | `src/korail_mobile_api/models.py:457` (helper `288-297`) | `analysis/jadx/.../seatMovie/RsvInquiryResponse.java:128` (`private int totPsgCnt`) | The "server quotes int fields" premise does not transfer to `totPsgCnt`. The string-serialization proof (`h_srcar_no="2"`, `h_rest_seat_cnt="3"`) is entirely about **`h_`-prefixed** legacy fields; `totPsgCnt` is non-`h_`. All three fixtures that contain it serialize a native JSON int (`raw_typed_train_search.json:55=4`, `product_train_inquiry_success.json:79=1`, `limousine_schedule_view_success.json:91=2`) — three independent endpoints, unanimous. App treats it as int; our client treats it as int. At most a defensive-hardening suggestion, not a divergence. |
| `prcFare` (`Price2Fare`) missing `trnCnt` field | `src/korail_mobile_api/read_payloads.py:991` | `analysis/jadx/.../trainsInfo/TrainsInfoService.java:26` (`@Field("trnCnt")`) | The app never sends `trnCnt`. Smali proves `setTrnCnt` is a self-assignment **no-op** (`Price2FareDao$Price2FareRequest.smali:149-161`: `iget trnCnt→p1` then `iput p1→trnCnt`, discarding the arg — contrast `setChtnDvCd:116` which stores it). The field stays null, `getTrnCnt()` returns null, and Retrofit 1.x (`RequestBuilder` `pswitch_4`, `if-eqz` on null) skips `addField`. Real app omits `trnCnt` on the wire exactly like our client — **zero divergence**. Applying the suggested fix would *create* a divergence. `chtnDvCd=str(len(legs))` is the only count field on the wire and is correct. |
| `ticketDupCheck.rsvCnt` parsed strict-int (`_required_json_integer`) | `src/korail_mobile_api/read_parsers.py:1921` | `analysis/jadx/.../ticket/TicketDuplicationCheckDao.java:27` (`int rsvCnt`) | Declared type matches (int↔int). Strictness is **deliberate and tested**: `tests/test_ticket_reference_reads.py:427-429` asserts `rsvCnt="2"` (quoted) must raise `KorailProtocolError`; the canonical fixture models it as native int (`rsvCnt=2`, test line 96). No fixture captures this field's wire type; the leniency argument is generalized from unrelated (`h_`-prefixed) fields. Intentional design choice among three int helpers, not a defect. |
| `pbpAcepSpec` seat `scarNo` parsed strict-int (`_required_json_integer`) | `src/korail_mobile_api/read_parsers.py:1962` | `analysis/jadx/.../ticket/PbpAcepSpecDao.java:102` (`int scarNo`) | Declared type matches (int↔int). Covered by tests: `test_ticket_reference_reads.py:441-446` asserts a non-int `scarNo` raises; canonical fixture models it as native int (`scarNo:3`, test line 120). No fixture captures the wire type; leniency generalized from unrelated fields. Switching to `_optional_integer` is a discretionary robustness preference the author deliberately declined — matches the declared int type and fixtures. Intentional, not wrong. |
| `copt.gdMenuLt.do` exact-field contract narrowing | `src/korail_mobile_api/safety.py:189` | `analysis/jadx/.../common/CommonService.java:48` (`@Field` Device, Version, pnrNo, tkRetNo, addSrvReqNo) | Our client implements only the **base (non-PNR)** variant: `build_maas_menu_form` returns exactly `{Device,Version}` and `get_maas_menu_list` posts with `include_common=False`, matching the app's base branch `getMaasMenuList(device,version,null,null,null)` (Retrofit omits the nulls). `assert_read_only_request_fields` is an exact-match allowlist applied to what we *actually send*, so `{Device,Version}` is correct and never wrongly rejects a legitimate request. No src path ever sends `pnrNo`/`tkRetNo`/`addSrvReqNo` to this route (the PNR-scoped variant is out of scope). Widening to a single frozenset would *break* the base path. Contract correctly has no `Key`. At most a scope/doc note. |

### Deliberate non-bugs (correct-by-design; not counted)

- ~~**DynaPath random-text alphabet** — ours is uppercase+digits vs the app's lower+upper+digits (`C1229b.java:164`); `rand` is random and only feeds key derivation, so any ASCII subset yields a valid token. No wire impact.~~ **Overturned 2026-07-26 and fixed** (`fix/apk-fidelity`): the client now uses the app's 62-character set. "No wire impact" was wrong — `rand` is embedded in `dyn_key = "v1.0.3+RAND+ts"`, which is encoded as `encoded_key` and **transmitted** as part of the token, so the nonce is recoverable by anyone holding the (public, static) table. A 36-character subset makes roughly 89% of genuine app nonces impossible for this client to emit, which is a per-request fingerprint even if the server never validates the value.
- **`pwdAESCphd` comparison** — the app is case-sensitive (`'Y'.equals`) while `get_login_crypto_info` upper-cases the value (`session.py:93`); harmless since the server returns uppercase `Y`/`N`.
- **Login POST field order** — `idx` emitted before `custId`/`etrPath` differs from the `@Field` order; form params are order-independent.
- **`member_card_no` lookup** — tries a non-existent `mbCrdNo` key before the real `strMbCrdNo` (`session.py:181-183`); the fallback resolves correctly.
- **`check_service` timeStamp type** — passed as a raw int (`session.py:76`) while `build_service_status_query`/`build_cache_query` pass `str(...)`; httpx serializes both identically. Cosmetic.
- **FresScar `trnNo`** — our `.zfill(5)` is idempotent on the already-5-digit `h_trn_no`; identical wire output.
- **Dead `@Field`s our client correctly omits** — `gift.gdLst.do` `qryNumNext`/`fllwQryFlg`/`trnOprBzDvCd` are declared but no app caller ever sets them (always null, never sent).

### Forward-compat / robustness notes (unproven; not counted)

These are strictness gaps where our parser is *stricter* than the app's tolerant Gson model, but **no evidence shows the server ever omits/null-encodes the field** (all fixtures include valid values). Flagged only as forward-compat risk:

- `parse_station_info_response` requires `map_version` (nullable Java String, `parsers.py:453-458`) and `count` (Gson would default absent int to 0, `parsers.py:448-452`).
- `parse_seat_inventory` marks `intg_msg`/`intg_msg_cd`/`vz_msg_dv_cd` required (`parsers.py:1018-1026`); nullable String in `SearchSeatListDao.Seat`.
- `parse_limousine_seat_inventory_response` uses `_required_list('seatList')` while `BusReservationSeatListDao.SeatListResponse.seatList` is a nullable `ArrayList`.

### Coverage gaps (unimplemented, therefore un-auditable — not divergences)

- **N-card schedule endpoints** — `ResearchService.getNCardSchedultView` (`dcntCrdScheduleView.do`), `getNCardHistory` (`dcntCrdUseQry.do`), and the write-side `setNCardReservation`/`setNCardExtension` are not implemented; no routes/builders exist. Nothing sent, nothing to audit.
- **`refunds.SelTicketInfo`** — not implemented. Flag for whoever adds it: it uses **different** request field names than `receipt.ReceiptInfo` — `h_orgtk_ret_sale_dt` (not `h_orgtk_sale_dt`), `h_orgtk_ret_pwd` (not `h_orgtk_tk_ret_pwd`), plus an extra `h_purchase_history` (the app sends `'N'`, `TicketListActivity.java:926`). Do not copy the receipt form.
- **Points / mileage read** — the app has `xPoint`/`LPointDao` + mileage DAOs, but no client builder/parser/model exists. Absence, not divergence.
- **`TrainCharge`** (`PriceFareDao`, `com.korail.mobile.trainsInfo.TrainCharge`) — a separate fare endpoint our client does not implement. Unimplemented, not buggy.
- **`parse_product_train_inquiry_response` / `_build_product_train_inquiry_form`** — exist but are not wired to any public client method (no POST to `ScheduleViewSpecial`), so they cannot emit a wrong request today; their field names nonetheless match the app.
- **Seat class limitation** — `build_seat_car_form`/`build_seat_inventory_form` hardcode `psrmClCd`/`txtPsrmClCd='1'` and `seatAttCd`/`txtSeatAttCd='015'`, so only general-class enumeration is possible (never special class `'2'`). The values sent are valid — a functional limitation, not a protocol divergence.
- **`ScheduleView` field set is ungated by design** — intentionally not in `KORAIL_EXACT_REQUEST_FIELDS` (`assert_read_only_request_fields` returns early when `allowed is None`), since passenger flags and optional `mbCrdNo` vary.
- **`arc02012` / `get_seat_page`** (from the task brief) appear nowhere in our repo or the decompiled sources; interpreted as the seat car/seat inventory research endpoints, which were audited.
