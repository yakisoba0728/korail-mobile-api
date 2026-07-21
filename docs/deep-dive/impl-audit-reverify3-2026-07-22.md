# Korail Client Implementation Audit — Re-verify (Round 3) — 2026-07-22

**Target app:** `com.korail.talk` v6.5.0 (decompiled ground truth under `analysis/jadx` + `analysis/apktool`)
**Under audit:** the read-only Python client in `src/korail_mobile_api/`
**Author:** FABLE
**Ground-truth rule:** the decompiled Korail app is authoritative. Where a client test bakes in a divergence, the test is treated as wrong, not the app; where `srtgo` / `srtgo_plus` diverges from the decompile, the decompile wins.

## Overview

This is the **third adversarial re-verify** pass (2026-07-22) over the scoped sub-audits — auth/session/crypto, common-station, search-schedule, seat-fare-traininfo, ticket-reservation-read, account-pass-maas-limousine, and safety-transport. Every candidate divergence was re-checked against the decompiled Retrofit DAOs (and, where relevant, apktool smali / fixtures / the `srtgo_plus` reference) before being counted. Findings that did **not** survive that check are listed under [Rejected / non-bugs](#rejected--non-bugs) and are **not** counted as real. Each surviving finding carries both-sides `file:line` citations: where our client diverges, and where the app proves the correct behavior.

**8 divergences survived verification: 3 Medium, 5 Low, 0 High.** None is a wrong route, wrong HTTP method, wrong envelope, or missing-required-field. The three Mediums are wrong param **values** that break a specific feature (SRT cross-listing, first-class seat reads, ticket pagination); the five Lows are over-strict parsers or peripheral value/field-set divergences a compliant server tolerates today.

## Headline

| Severity | Count |
|---|---|
| High | 0 |
| Medium | 3 |
| Low | 5 |
| **Total real divergences** | **8** |

Notable shifts from prior rounds: the **DynaPath `rt="0"` stub** (a counted Low in [`impl-audit-reverify2-2026-07-22.md`](impl-audit-reverify2-2026-07-22.md) as RV2-01) is **demoted to a non-bug** this round — re-verified as a deliberate, test-pinned, live-server-validated stateless simplification, not a defect. Conversely the **phone-auth continuation POST body** (an observation in Round 2) is **promoted to a counted Low** (RV3-08) after confirming the app serializes the typed `LoginResponse` (Gson null-omission) rather than the raw envelope our client forwards.

---

## Prioritized bug table (High → Low)

| # | Severity | Area | Our ref | Ground-truth ref | Description | Fix |
|---|---|---|---|---|---|---|
| RV3-01 | Medium | `ScheduleView` / `build_train_search_form` — `ebizCrossCheck` vs `srtCheckYn` coupling (include-SRT) | `src/korail_mobile_api/payloads.py:231` | `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:775` (`setEbizCrossCheck`) & `:776` (`setSrtCheckYn`); `analysis/jadx/sources/.../TrainInquiryRequest.java:97,133`; `TrainInquiryDao.java:14` | In the app both `ebizCrossCheck` and `srtCheckYn` are set from the **single** "include SRT" checkbox (`f29041T = cb_extra_option_srt`): `setEbizCrossCheck(checked?"Y":"N")` and `setSrtCheckYn(checked?"Y":"N")` — these are the only two call sites of those setters, so the pair is **always equal**, and `TrainInquiryDao` sends both. Our client hardcodes `ebizCrossCheck="N"` (`payloads.py:231`) while making `srtCheckYn` track `include_srt` (`:232`). With `include_srt=True` we emit `ebizCrossCheck="N", srtCheckYn="Y"` — a combination the app never produces. Since the server also keys SRT cross-listing off `ebizCrossCheck="Y"`, the `include_srt` feature likely does not work. | Couple the pair: `"ebizCrossCheck": "Y" if query.include_srt else "N"` so `ebizCrossCheck` always equals `srtCheckYn`, mirroring `MainBookingActivity`. |
| RV3-02 | Medium | seat-inventory (`research.TResidualSeatsResearch.do` / `get_seat_inventory`) — `psrmClCd` hardcoded | `src/korail_mobile_api/payloads.py:179` | `analysis/jadx/sources/x4/b.java:18` (`setTxtPsrmClCd(str2)`); `analysis/jadx/sources/c5/c.java:90` (reads `RSeat.SEAT_PSRM_CL_CD`) | `build_seat_inventory_form` hardcodes `psrmClCd="1"` (general / 일반실). The app derives `psrmClCd` from the user's selected reservation room class: `c5/c.java` reads `RSeat.SEAT_PSRM_CL_CD`, passes it into `X4.b.getSearchRequest(...)` → `setTxtPsrmClCd(str2)`, and `getSeatList` forwards it as `@Field("psrmClCd")` — value `"2"` for 특실 / first-class. So calling `get_seat_inventory()` on a first-class car sends `psrmClCd="1"` and returns wrong/empty seat-map data with no error. `ktx.py:891` likewise sends `"2"` for special seats. Our `SeatCar` model already carries `room_class_code` (`h_psrm_cl_cd`) but the builder ignores it. | Accept a `room_class_code` argument (or read the target car's `h_psrm_cl_cd`) and send `"1"`/`"2"` accordingly instead of the constant `"1"`. |
| RV3-03 | Medium | `MyTicketList` / `build_ticket_list_form` — `txtIndex` param value | `src/korail_mobile_api/payloads.py:280-292` (line 287: `"txtIndex": str(page)`) | `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:937-939` (`setTxtIndex("1")`); `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java:276-278` (`setTxtIndex("2")`); `MyTicketService.java:16-18` | `build_ticket_list_form` sets `txtIndex` to the page number, but in the app `txtIndex` is a fixed **list-mode / tab selector**, not a page index: `"1"` = current/active tickets, `"2"` = purchase history (구매이력). The page number is carried by `h_page_no` (hardcoded `"1"` at both call sites). Our client maps `page_no` into **both** `txtIndex` and `h_page_no`. Consequence: `get_ticket_list(2)` sends `txtIndex=2`, switching the server into purchase-history mode (which also expects `h_abrd_dt_from`/`h_abrd_dt_to` date ranges we send empty) instead of returning page 2; `get_ticket_list(3+)` sends an undefined `txtIndex`. The default `get_ticket_list()` (`page_no=0` → `txtIndex=1`) is correct only by coincidence, and the sole test covers only that default, masking the bug. | Set `txtIndex` to a fixed list-mode value (`"1"` for the current-ticket list this client targets) independent of pagination; keep only `h_page_no` varying with the page. For history support, expose an explicit mode param (`txtIndex="2"`) plus `h_abrd_dt_from`/`h_abrd_dt_to`. |
| RV3-04 | Low | seat-car-list (`research.TrainResearch` / `get_seat_cars`) — `txtPsrmClCd` hardcoded | `src/korail_mobile_api/payloads.py:141` | `analysis/jadx/sources/x4/b.java:18` (`setTxtPsrmClCd(str2)`); `analysis/jadx/sources/c5/c.java:90` | `build_seat_car_form` hardcodes `txtPsrmClCd="1"`. Same root cause as RV3-02: `X4.b.getSearchRequest` passes the selected room class (`str2`) into `setTxtPsrmClCd`, which `getCarList` sends as `@Field("txtPsrmClCd")` and can be `"2"` for first class. For a first-class train the returned car list is filtered to general class only. | Parameterize `txtPsrmClCd` (`"1"`/`"2"`) rather than pinning it to `"1"`. |
| RV3-05 | Low | `TrainResearch` (`get_seat_cars`) & `TResidualSeatsResearch` (`get_seat_inventory`) — `txtSeatAttCd`/`seatAttCd` substitution | `src/korail_mobile_api/payloads.py:112` | `analysis/jadx/sources/x4/b.java:19` (`setTxtSeatAttCd(trainInfo.getH_seat_att_cd())`); consumed by `SearchCarListDao.java:88` (`getCarList`) & `SearchSeatListDao.java:137` (`getSeatList`) | The app forwards the seat-attribute code verbatim from the selected train row: `setTxtSeatAttCd(trainInfo.getH_seat_att_cd())`. ScheduleView search rows carry a null `h_seat_att_cd` (confirmed by `fixtures/schedule_view_success.json` and the comment at `payloads.py:110-111`), so in the standard flow the app sends null → Retrofit **omits** `txtSeatAttCd`/`seatAttCd`. Our `_resolved_seat_attribute_code` substitutes `"015"` whenever the row code is empty (`payloads.py:108-112`), so `build_seat_car_form` (`:152`) and `build_seat_inventory_form` (`:182`) send `txtSeatAttCd="015"`/`seatAttCd="015"` where the app sends no field at all. Provable wire divergence on every seat read derived from a search; server impact uncertain (`"015"`=general seat may be treated as absent), hence Low. | Forward `train.seat_attribute_code` as-is and omit `txtSeatAttCd`/`seatAttCd` when it is empty/None, instead of substituting `"015"`. |
| RV3-06 | Low | `schedule.runDt` calendar parser — over-strict on the `runningCalendar` list | `src/korail_mobile_api/parsers.py:455` | `analysis/jadx/sources/S4/C0805e.java:124` (`if (C0804d.isNull(list) \|\| list.size() <= 0) { ...return; }`); `TrainCalendarDao.java:101-103` (nullable list field) | `parse_train_calendar_response` requires the top-level `runningCalendar` key to be present **and** a list, raising `KorailProtocolError` when absent or null (enforced by `test_raw_typed_core.py:180`). The app tolerates a null/absent list: `getRunningCalendarList()` returns a nullable `List`, and `makeAvailableDatesFactory` null-guards it — `if (isNull(list) \|\| list.size() <= 0) { log("Server did not give valid calendar!!"); return; }`. FAIL responses are handled separately (`l4/h.java:384`), so this null-guard also runs on SUCC responses. Thus on a SUCC response with a null/absent `runningCalendar` the app returns an empty calendar while our client throws. Impact low (success responses normally include the list) but the app's contract explicitly permits null. | Treat an absent/null `runningCalendar` as an empty day tuple (accept `None` and yield `days=()`) instead of raising, matching the app's null-guard. |
| RV3-07 | Low | `schedule.runDt` calendar parser — over-strict on per-row `runDt` | `src/korail_mobile_api/parsers.py:468` | `analysis/jadx/sources/S4/C0805e.java:147` (`String dateStr = runningCalendar.getDateStr()` gated behind `!TextUtils.isEmpty(dateStr)` at `:140`); `TrainCalendarDao.java:90-94` (`compareTo` null-guards) | `parse_train_calendar_response` makes each row's `runDt` required via `_typed_required_string`, raising when it is absent/null (`test_raw_typed_core.py:183`). The app tolerates a null `runDt` per row: `getDateStr()` returns the raw nullable field, and every consumer is null-safe — `compareTo()` guards null, and `makeAvailableDatesFactory` reads `dateStr` then gates use behind `!TextUtils.isEmpty(dateStr)` (`C0805e.java:140,147`), silently skipping null-date rows; `isHoliday()`/`isPeakSeason()` never touch `runDt`. So a row with a null `runDt` is skipped by the app but causes our client to reject the entire response. (`hldyDvCd` is correctly kept required — the app NPEs on null via `isHoliday()`'s `this.hldyDvCd.isEmpty()` at `TrainCalendarDao.java:61`.) | Make `run_date` optional (`_typed_optional_string`) so a null/absent `runDt` row does not abort the whole calendar parse, matching the app's null-tolerant iteration. |
| RV3-08 | Low | phone-auth continuation — `build_login_authentication_post_data()` forwards raw envelope | `src/korail_mobile_api/session.py:46-49` | `analysis/jadx/sources/S4/u.java:33-43` (`getLoginAuthenticationPostData` serializes typed `LoginResponse` via `q.toJson(...)`) | `build_login_authentication_post_data()` builds the continuation POST body by iterating the **raw** server-response dict (`response_raw.items()`), emitting every key (except `strResult`/`h_msg_txt`) with null coerced to empty string. The app (`S4/u.getLoginAuthenticationPostData`) instead serializes the **typed** `LoginDao.LoginResponse` via `q.toJson(loginResponse)` and iterates that JSONObject. Gson omits null fields and the DTO has a fixed declared field set, so the app emits only the ~29 declared non-null `LoginResponse` fields (plus `h_msg_cd`), whereas our version forwards any extra server fields and emits null-valued fields as `key=`. Different field set/values for the continuation redirect body. Only affects the rare phone-reauth continuation path (`KorailAuthContinuationRequired`), and the client does not itself POST this data (it hands it to the caller), so impact is limited and depends on redirect-endpoint tolerance. | Restrict the continuation body to the known `LoginResponse` field set and drop null/absent fields (mirror Gson null-omission), rather than forwarding the raw response verbatim. |

---

## Detailed findings

### RV3-01 — `include_srt` sends an `ebizCrossCheck`/`srtCheckYn` pair the app never produces (Medium)

- **Our ref:** `src/korail_mobile_api/payloads.py:231` (`ebizCrossCheck` hardcoded `"N"`) and `:232` (`srtCheckYn` tracks `include_srt`).
- **Ground-truth ref:** `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:775-776`; the only setter call sites are `TrainInquiryRequest.java:97,133`; sent by `TrainInquiryDao.java:14`.

Both fields derive from one UI control (`cb_extra_option_srt`), so the app always sends them **equal** (`Y/Y` or `N/N`; both default `"N"` when null). Our client can emit `N/Y`, which the app never does. Because the server also keys the SRT cross-list on `ebizCrossCheck="Y"`, the `include_srt` feature likely does not surface SRT trains. The `srtgo_plus` reference (`ktx.py`) never exercises `include_srt` (it leaves both `"N"`), so the decompile is authoritative for the coupling.

**Fix.** `"ebizCrossCheck": "Y" if query.include_srt else "N"`.

### RV3-02 — `get_seat_inventory` pins `psrmClCd="1"`, breaking first-class seat reads (Medium)

- **Our ref:** `src/korail_mobile_api/payloads.py:179`.
- **Ground-truth ref:** `analysis/jadx/sources/x4/b.java:18` (`setTxtPsrmClCd(str2)`) fed by the selected room class read at `analysis/jadx/sources/c5/c.java:90` (`RSeat.SEAT_PSRM_CL_CD`); forwarded by `getSeatList` as `@Field("psrmClCd")`.

For a 특실 (first-class) car the app sends `psrmClCd="2"`; our constant `"1"` returns wrong/empty seat-map data silently. The `SeatCar` model already carries `room_class_code` (`h_psrm_cl_cd`) and is ignored here. `ktx.py:891` corroborates `"2"` for special seats.

**Fix.** Parameterize by the target car's `h_psrm_cl_cd` (`"1"`/`"2"`).

### RV3-03 — `build_ticket_list_form` misuses `txtIndex` as a page index (Medium)

- **Our ref:** `src/korail_mobile_api/payloads.py:280-292` (line 287).
- **Ground-truth ref:** `TicketListActivity.java:937-939` (`setTxtIndex("1")`), `TicketPurchaseHistoryActivity.java:276-278` (`setTxtIndex("2")`), `MyTicketService.java:16-18`.

`txtIndex` is a list-mode tab (`"1"`=active, `"2"`=purchase history), not a page cursor; the page lives in `h_page_no`. Mapping `page_no` into `txtIndex` makes `get_ticket_list(2)` silently switch the server into history mode (needing `h_abrd_dt_from`/`h_abrd_dt_to` we leave empty), and `get_ticket_list(3+)` sends an undefined value. Only the default (`page_no=0`→`txtIndex=1`) happens to be correct, and the lone test covers only that default.

**Fix.** Fix `txtIndex="1"` for this client; vary only `h_page_no`. Expose history as an explicit mode if wanted.

### RV3-04 — `get_seat_cars` pins `txtPsrmClCd="1"` (Low)

- **Our ref:** `src/korail_mobile_api/payloads.py:141`.
- **Ground-truth ref:** `analysis/jadx/sources/x4/b.java:18`; `analysis/jadx/sources/c5/c.java:90`.

Same root cause as RV3-02 on the car-list read: `getCarList` forwards the selected room class as `@Field("txtPsrmClCd")`, which is `"2"` for first class. A first-class train's car list is filtered to general only.

**Fix.** Parameterize `txtPsrmClCd`.

### RV3-05 — Seat builders substitute `"015"` where the app omits `txtSeatAttCd`/`seatAttCd` (Low)

- **Our ref:** `src/korail_mobile_api/payloads.py:112` (`_resolved_seat_attribute_code`), consumed at `:152` (`build_seat_car_form`) and `:182` (`build_seat_inventory_form`).
- **Ground-truth ref:** `analysis/jadx/sources/x4/b.java:19` (`setTxtSeatAttCd(trainInfo.getH_seat_att_cd())`); consumed unmodified by `SearchCarListDao.java:88` and `SearchSeatListDao.java:137`.

ScheduleView rows carry a null `h_seat_att_cd` (fixture `schedule_view_success.json`), so Retrofit omits the field; our substitution sends `"015"` on every search-derived seat read. Server impact uncertain, hence Low, but it is a provable wire divergence.

**Fix.** Forward `train.seat_attribute_code` verbatim and omit the field when empty/None.

### RV3-06 — Calendar parser rejects a null/absent `runningCalendar` the app tolerates (Low)

- **Our ref:** `src/korail_mobile_api/parsers.py:455` (enforced by `test_raw_typed_core.py:180`).
- **Ground-truth ref:** `analysis/jadx/sources/S4/C0805e.java:124`; nullable list field at `TrainCalendarDao.java:101-103`.

`makeAvailableDatesFactory` null-guards the list (`isNull(list) || list.size() <= 0` → log + return) on SUCC responses (FAIL is handled at `l4/h.java:384`), so a SUCC with null/absent `runningCalendar` yields an empty calendar in the app but raises `KorailProtocolError` in our client.

**Fix.** Accept `None` and yield `days=()`.

### RV3-07 — Calendar parser rejects a null per-row `runDt` the app skips (Low)

- **Our ref:** `src/korail_mobile_api/parsers.py:468` (enforced by `test_raw_typed_core.py:183`).
- **Ground-truth ref:** `analysis/jadx/sources/S4/C0805e.java:147` (`getDateStr()` gated by `!TextUtils.isEmpty(dateStr)` at `:140`); `TrainCalendarDao.java:90-94` (`compareTo` null-guard).

The app silently skips rows with a null/empty `runDt`; our required-string parse aborts the whole response. `hldyDvCd` is correctly kept required (the app NPEs on null there at `TrainCalendarDao.java:61`).

**Fix.** Make `run_date` optional (`_typed_optional_string`).

### RV3-08 — Continuation POST body forwards the raw envelope instead of the typed `LoginResponse` (Low)

- **Our ref:** `src/korail_mobile_api/session.py:46-49`.
- **Ground-truth ref:** `analysis/jadx/sources/S4/u.java:33-43` (`getLoginAuthenticationPostData` → `q.toJson(loginResponse)`).

The app serializes the typed DTO (Gson omits nulls; fixed ~29-field set + `h_msg_cd`) and iterates that JSONObject. Our client iterates the raw response dict, forwarding any extra server fields and emitting null-valued fields as `key=`. Different field set/values on the rare `KorailAuthContinuationRequired` phone-reauth redirect body; the client only hands the data to the caller (does not POST it), so impact depends on redirect-endpoint tolerance.

**Fix.** Restrict to the known `LoginResponse` field set and drop null/absent fields (mirror Gson null-omission).

---

## Verified correct

The following were re-checked against the decompile and found faithful (no divergence counted):

- **auth-session-crypto.** Login (POST) and logout (GET) are both correctly registered read-only routes; logout is a params-less GET authenticated purely by `JSESSIONID`; login's field set is (correctly) unrestricted while logout is restricted to zero fields. The DynaPath token structure, tables, encoding, field order, and values are faithful to the SDK — the **only** DynaPath value differing from runtime is `rt` (see Rejected). On the login password, **our** client matches the decompiled app (double base64 with the inner Android newline preserved); `srtgo_plus` (`ktx.py`) is the one that diverges by omitting that newline — trust our implementation here. Ground truth: `LoginService.java`, `LoginDao.java`, `LogoutDao.java`, `S4/C0812l.java`, `F4/a.java` (`encryptBase64`/`NO_WRAP`), `ExecuteDao.java`, DynaPath SDK (`B/C1229b.java`, `DynaPathMobileSDK.java`, `l1/*`), `k5/b.java`, `S4/u.java`, `KTApplication.java`.
- **common-station.** Payload builders (`build_common_code_form`/`build_cache_query`, `build_service_status_query`), the remaining parsers (`parse_station_data_response`, `parse_station_info_response`, `parse_service_status_response`, `parse_app_data_response`, `parse_notice_response`), and the station/calendar models match `StationDataDao`, `StationInfoDao`, `TrainCalendarDao`, `ServiceCheckDao`/`CacheService`, `CommonCodeDao`/`CommonService`. The two counted bugs (RV3-06/07) are over-strictness, not wrong-data-sent. Non-bug notes: `tests/fixtures/train_calendar.json` is a stale legacy-shape artifact **not** fed to the parser (cleanup candidate, no runtime effect); FAIL responses for `dao_train_calendar`/`dao_check_service` surface as `KorailAppError` carrying the same `h_msg_cd`/`h_msg_txt` (soft-dialog in-app, not a data divergence); `get_common_code(code)` not exposing the `departDate`/`arrivalDate`/`holidayYn` holiday params is a feature gap, not a wire divergence.
- **search-schedule.** Verified against `ResearchService`/`SeatMovieService`/`CalendarService` DAOs and call sites; field names resolved via `C1262b`, `OJrny`, `OSeat`, `OPsg`, `Price2Fare`. `radJobId=1` and the ScheduleView param set are corroborated by `ktx.py`. `dcntCrd*` (N-card) endpoints are **not** implemented (nothing to diverge). Deliberate read-only simplifications (not bugs): `psrmClCd`/`txtPsrmClCd` hardcoded to general in the seat builders (also filed as RV3-02/04 where they cause a first-class miss); single `passengers` int → `txtPsgFlg_1`; `qryStTrnNo2=""` vs app-null in the direct ScheduleViewSpecial continuation.
- **seat-fare-traininfo.** Traps cleared: `prcFare` `trnCnt` — `Price2FareDao.setTrnCnt` is a no-op self-assignment so Retrofit omits `trnCnt`; our omission is **correct** (do not add it). `sidTest` — both `getCarList`/`getSeatList` pass `null` in production; correctly omitted. `actualTrainSchedule` is the only FOCUS endpoint that omits `Key`; handled correctly. Not implemented (no wire to audit): `TrainCharge`/`getPriceFare`; `TourTrainSpecialRoom`/`getTourTrainInfo` (parser+model exist but unwired/dead). Unproven-and-unfiled: strictness of `intg_msg`/`intg_msg_cd`/`vz_msg_dv_cd` requireds; `parse_transfer_station_list_response` requiring non-empty `chtnRsStnCd` (the empty-code "전체" row is added client-side by the app, so server-row strictness is fine).
- **ticket-reservation-read.** `refunds.SelTicketInfo` (`TicketDetailDao`) is **not** implemented — no divergence to audit; note its field names differ from `ReceiptInfo` (`h_orgtk_ret_pwd`/`h_orgtk_ret_sale_dt` vs `h_orgtk_tk_ret_pwd`/`h_orgtk_sale_dt`), and our implemented `ReceiptInfo` form uses the correct `ReceiptInfo` names. Unfiled robustness concerns (no ground-truth wire sample): strict `_required_json_integer` on `rsvCnt` (`read_parsers.py:1921`) and `scarNo` (`:1962`) could fail if the server returns them as strings (Korail often does; our `reservation_history` parser deliberately uses lenient `_optional_integer`); `parse_reservation_history_response` accepting only `P100` as empty (`:1058-1063`) vs the reference's `{P100, WRG000000, WRD000061, WRT300005}` (`ktx.py:501`) — the decompile does not pin ReservationView's empty code.
- **account-pass-maas-limousine.** **Zero** divergences. Every builder, parser, route, GET/POST method, and hardcoded value matches the v6.5.0 DAOs. Points/mileage reads are intentionally excluded (`safety.py:17` `EXCLUDED_API_DOMAINS` "points-mileage"; `SAFETY_DEFAULTS` gates the payment/point domain off). Subtleties handled correctly: limousine schedule `service_code→tmGpCd` vs seat-inventory `service_code→trnGpCd`; product detail wire name `txtVrRsNo` (not internal `txtVrRsvNo`); MaaS `gdReqQry` omits `Key` and supports both current/history date variants; commuter `jobDvCd b` `psgCnt == psgList.size()`; product-train-inquiry seat-attribute defaults `000/000`.
- **safety-transport.** `READ_ONLY_ROUTES` + `KORAIL_EXACT_REQUEST_FIELDS` + `KORAIL_EXACT_REQUEST_FIELD_ORDERS`, `http.py` transport, `BaseRequest`/`BaseResponse` envelope, and NetFunnel wiring all faithful. Correctly handles every null-omission subtlety (`sidTest`, `trnCnt`, `gdLst` extras), `Key` omissions, and no-`Key` routes. **NetFunnel clarification:** the app *does* have a NetFunnel waiting-room gate on the reservation seat-inquiry (`seatMovie.ScheduleView`, `act_8`), but it is **not** part of any request contract (no token field), so a read-only client correctly omits it (`ktx.py` bypasses it in practice). Edge left unfiled (no fixture): `l4/h.java:384` also treats `h_msg_cd=="SEMGTK"` as an error, which `parse_base_response` (`http.py:32-42`) does not special-case; only matters if a `SEMGTK` can arrive with `strResult != "FAIL"`.

---

## Rejected / non-bugs

These candidates were investigated and **rejected**; they are **not** counted as real divergences.

- **DynaPath `rt="0"` hardcoded** (`src/korail_mobile_api/dynapath.py:303`). **Rejected — intentional, not a defect.** The technical claim is accurate: `C1229b.a(long)` (`analysis/jadx/sources/B/C1229b.java:76-91`) computes `rt` as a delta deque, and on the first request emits `rt=(ts−it)`, never `0` for `it != ts`; `DynaPathMobileSDK.generate()` (`:33-36`) calls `a(now)` then `a()`. But `rt=0` is a deliberate, tested, live-server-validated **stateless** simplification: `test_token_settings_do_not_accept_request_history` and `test_dynapath_generator_has_no_cross_request_state` explicitly enforce no request-history/state, `test_generate_dynapath_token_matches_successful_fixed_rt_reference` pins a server-accepted token, and memory note `autonomous-session-2026-07-22.md:22` documents it as intentional (의도적) with fidelity improvement deferred as a design reversal. The finding itself concedes it is a server-tolerated simplification, not a functional break. (This reverses Round 2's RV2-01, which had counted it as a Low.)
- **`copt.gdMenuLt.do` field contract** (`src/korail_mobile_api/safety.py:189`). **Rejected — not a bug.** The claim that the single frozenset `{Device, Version}` "forbids the app's 5-field variant" does not make our code wrong. Ground truth: `CommonService.java:48` declares `getMaasMenuList` with 5 `@Field` params (`Device, Version, pnrNo, tkRetNo, addSrvReqNo`); `MaasMenuListDao.executeDao` (`:163`) has a path `getMaasMenuList(device, version, null, null, null)`. Under `@FormUrlEncoded`, null `@Field` values are omitted, so that path emits **exactly** `{Device, Version}` — a legitimate app request. Our `build_maas_menu_form` (`payloads.py:295-299`) returns exactly `{Device, Version}`, and the validator checks `set(field_names) == allowed` (`safety.py:692`), so it correctly passes what our client sends and never blocks any request our client makes. The 5-field PNR-scoped variant is simply a feature the read-only client does not implement; the contract accurately describes what we emit. The finding itself concedes "no wrong request is currently sent... coverage gap, not a wrong-request bug" and its own suggested fix is "leave as-is." Recorded as an optional coverage note only.
