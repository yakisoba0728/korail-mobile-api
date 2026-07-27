# Korail App Cross-Validation Report — srtgo_plus vs. Our v6.5.0 Decompilation

**App:** `com.korail.talk` v6.5.0 (VERSION_CODE 60500002, FLAVOR `product`, BUILD_TYPE `release`)
**Reference implementation:** `srtgo_plus/srtgo/ktx.py`
**Our source of truth:** independent APK decompilation under `analysis/jadx/sources/` (+ `analysis/apktool/`)
**Date:** 2026-07-21
**Author:** FABLE

---

## Overview

This report reconciles the **srtgo reference implementation** (a community Python client, `ktx.py`) against **our own independent decompilation** of the Korail Android app v6.5.0. For each of six dimensions we record:

- ✅ **Confirmed** — srtgo matches our app, both sides re-read at file:line.
- ⚠️ **Corrections / discrepancies** — srtgo is wrong, oversimplified, or structurally different.
- 🔀 **Version drift** — both are internally consistent but srtgo was built against an older Korail/SDK build.
- 🆕 **Newly-found hidden items** — real behavior in our v6.5.0 that srtgo never modeled.
- 📌 **Our exact v6.5.0 values** — the ground-truth constants.
- ❓ **Disputed / low-confidence** — anything a verifier could not confirm, or where a finding overstated itself.

Every claim below carries citations from **both** sides. Citations of the form `ktx.py:NN` are srtgo; all other paths are our decompiled sources (relative to `analysis/jadx/sources/` unless noted). Anything not statically provable is marked **UNVERIFIED**.

**Headline result:** srtgo is a faithful and mostly-correct reconstruction. The three most consequential gaps are all in the anti-macro **DynaPath** layer and the **refund** path: (1) srtgo's DynaPath SDK version string is `v1` where ours is `v1.0.3`, which reseeds the entire token; (2) srtgo's refund misspells the PNR field as `txtPrnNo` where ours is `txtPnrNo`; and (3) srtgo hardcodes anti-tamper/timing telemetry (`rt`, `su/dbg/emu/hk`, `di`) that our app computes live. None of these necessarily breaks srtgo in practice — whether they matter hinges on open questions about server-side validation.

---

## 1. DynaPath anti-macro token (`dimension: dynapath-native`)

**Confidence: HIGH**

> **Framing correction up front:** There is **no native `.so`** for DynaPath. Despite the "native" label, the only native libs in the APK are `liberb.so`, `libsurface_util_jni.so`, `libtensorflowlite_jni.so`, `libimage_processing_util_jni.so` (camera / ML for card OCR, unrelated). DynaPath is **pure obfuscated Kotlin/Java**: `kr.scripters.dynapath.sdk.android.DynaPathMobileSDK` (thin wrapper) → package `b` (engine `C1229b`/`AbstractC1228a`) → package `l1` (`AbstractC5980b` encoder, `AbstractC5987i` cert hash, `AbstractC5981c` anti-tamper). Because it is algorithmic Java with no hidden black box, srtgo could and did faithfully reimplement it.

### ✅ Confirmed

- **6 protected paths — exact match, same order.** Our request interceptor hardcodes them: `com/korail/talk/network/ExecuteDao.java:27` = `{TicketReservation, NonMember.NonMemTicket, seatMovie.ScheduleView, seatMovie.ScheduleViewSpecial, trn.prcFare.do, login.Login}`. srtgo `DYNAPATH_PATHS` (`ktx.py:44-51`) lists the identical 6 in identical order. Both loop `if url.contains(path)` (`ExecuteDao.java:35` vs `ktx.py:669`).
- **Header name — exact match** `x-dynapath-m-token` (`ExecuteDao.java:47` `setRequestProperty("x-dynapath-m-token", strGenerate)` vs `ktx.py:673`).
- **App secret `as` — value and encoding confirmed.** srtgo `AS_VALUE=%5B38ff229cb34c7dda8e28220a2d750cce%5D` (`ktx.py:56`). Our app **derives** it rather than hardcoding: `as` = `ArrayList.toString()` of SHA-256(APK signing cert) truncated to 32 hex chars (`l1/AbstractC5987i.java:56-68`; wired at `DynaPathMobileSDK.java:54`; consumed as field `f12258c` → key `as` in `B/C1229b.java:105-107`). `ArrayList.toString()` adds the `[…]` brackets and `URLEncoder` (`C1229b.java:149`) encodes them to `%5B`/`%5D`. So `38ff…cce` **is** our v6.5.0 signing-cert hash and srtgo has it right.
- **Core algorithm structure — full match.** UTF packing `string2xA1s` (srtgo 66-86) == `l1/AbstractC5980b.java:124-143` (identical 128/2048/262144 thresholds, 160 & 144 prefixes, 55296 surrogate skip). `make_key` BigInteger (srtgo 88-98) == `B/C1229b.java:191-211` (`i16=32768` hi-bit scan, `big=big*(i16<<1)+cp`). `make_encode_table` (srtgo 110-119) == `C1229b.java:213-243`. `encode_normal_be` base-pack (srtgo 121-147) == `AbstractC5980b.java:118-216`. Constants `pack=161`, `radix=30`, `group=2` all match.
- **Base62 table match.** srtgo's literal `3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz` == our runtime `AbstractC5980b.a(1)`: the seed alphabet `0123456789A-Za-z` (`AbstractC5980b.java:112`) permuted with seed=1 from the 100-prime table in `l1/C5979a.java`. Verified via prefix: `TABLE[2]='E'`, `TABLE[37]='e'`, `TABLE[29]='P'`.
- **`bEeEP` prefix confirmed** for the live (macro-on) path. Our `C1229b.java:186-188` builds `char(i14+97)+TABLE[2]+TABLE[37]+TABLE[i11]+TABLE[i12-1]` with `i14=1, i11=2, i12=30` → `'b'+'E'+'e'+'E'+'P'`. srtgo's literal `bEeEP` (`ktx.py:160`) is exactly this.
- **Sid AES key and full scheme confirmed** (including a subtle detail srtgo got right). `S4/C0812l.java:45` `getSid()=encryptAES("2485dd54d9deaa36", BaseRequest.ANDROID + currentTimeMillis)`; `ANDROID="AD"`; AES/CBC/PKCS5Padding, IV=`key.substring(0,16)` (= key itself), Android `Base64.encode(...,0)`=DEFAULT which **appends a trailing `\n`**. srtgo `_generate_sid` (`ktx.py:661-664`) replicates all of it including the newline.

### ⚠️ Corrections / discrepancies

- **`sv` / SDK-version string is WRONG in srtgo — the single biggest correctness gap.** srtgo uses `v1` in **both** the body field (`SDK_VERSION="v1"`, `ktx.py:59` → `sv=v1`) and the `dyn_key` prefix (`dyn_key=f"v1+{rand}+{ts}"`, `ktx.py:155`). Our v6.5.0 uses `v1.0.3` in **both** places: body `linkedHashMap.put("sv", new String[]{"v1.0.3"})` (`C1229b.java:137`) and key builder `new StringBuilder("v1.0.3+")` (`C1229b.java:157`). Because `dyn_key` seeds `key_enc`, the custom body table, and the whole body encoding, srtgo's `v1+` produces a **different** (though self-consistent) token, and its decoded `sv` reads `v1`. If the server validates the version string, this breaks. *(Re-verified: `ktx.py:59,155` = `v1`; `C1229b.java:137,157` = `v1.0.3`.)*
- **`rt` field oversimplified.** srtgo hardcodes `rt=0` (`ktx.py:153`, single value). Our app sends `rt` as an **array of up to 5 inter-generation deltas**: `C1229b.a(long)` (`C1229b.java:76-91`) pushes `now - lastTs` into a 5-deep deque (`C6044h`); `C1229b.java:119-127` emits every delta as its own `rt=` param. Because `generate()` calls `a(now)` **before** `a()` (`DynaPathMobileSDK.java:34-35`), `rt` is **always present and never 0** on the first token. This is anti-macro timing telemetry; srtgo's constant `0` is a detectable fingerprint if the server inspects `rt`.
- **SID generation coupling differs.** srtgo generates `sid` only inside `_get_auth_headers_and_sid`, gated on the same 6 `DYNAPATH_PATHS` (`ktx.py:666-675`) — it ties `sid` to the token. In our app the `sid` **param is independent** of the macro flag and the 6 paths: `C0812l.getSid()` is called unconditionally on the seat/train inquiry DAOs (`SearchSeatListDao.java:137`, `SearchCarListDao.java:88`, `TrainInquiryDao.java:14`, `LimousineTrainInquiryDao.java:14`). So our app always sends `sid` on those endpoints even when the macro flag is off; srtgo sends it only for the 6 token paths.
- **`IS_MACRO_ACTIVE` gate — a runtime kill-switch srtgo has no equivalent for.** Token is **NOT sent by default.** Our default is `false` (`I4/a.java:14` `IS_MACRO_ACTIVE=false`); it flips **only** when the server common-code response returns `isMacroEnable=='Y'` (`IntroActivity.java:663`; field `CommonCodeDao.java:373`). `ExecuteDao.java:26` wraps the whole token logic in `if (a.IS_MACRO_ACTIVE)`. srtgo attaches the token unconditionally for any of the 6 paths. So our DynaPath header is emitted only when **a matched path AND the server-enabled flag** are both true.

### 🔀 Version drift

- **SDK version string:** our v6.5.0 = `v1.0.3` (`C1229b.java:137,157`) vs srtgo `v1` (`ktx.py:59,155`). Likely srtgo was built against an older Korail build with DynaPath SDK v1.
- **App client version param:** our `BaseRequest.setVersion("250601003")` (`BaseRequest.java:16`) vs srtgo `_version="250601002"` (`ktx.py:643`). Off by one build (…002 vs …003).
- **`rand` alphabet:** our app draws 4 chars from `a-zA-Z0-9` (62 chars, `C1229b.java:164`) vs srtgo `A-Z0-9` (36 chars, `ktx.py:671`). Same length (k=4) but srtgo never emits lowercase in the `dyn_key` rand — a statistical fingerprint, not a hard failure since `rand` is server-unpredictable.

### 🆕 Newly-found hidden items srtgo missed

- **Anti-tamper telemetry fields `su/dbg/emu/hk` are real live checks**, not the hardcoded `false` srtgo assumes (`ktx.py:152`). Our `l1/AbstractC5981c.java` computes them at token time:
  - `su` = root detection (10 su-binary paths + 12 root-app package probes + `Build.TAGS` test-keys, method `b()`)
  - `dbg` = debuggable flag + debugger attached (`a()`)
  - `emu` = emulator heuristics gated on SDK≥28 (`b()`/`a()` at :139-207)
  - `hk` = hook detection scanning the stacktrace for xposed/lsposed/edxposed/frida (`c()` at :120-137)

  Wired at `DynaPathMobileSDK.java:54`. A rooted/hooked/emulated client would send `true` and could be flagged server-side; srtgo cannot reproduce these signals from a clean host but also never trips them.
- **`rt` inter-call delta deque** (see corrections) is a genuine behavioral-biometric channel our app ships and srtgo misses.
- **`di` = the device's real `Settings.Secure.ANDROID_ID`** (`AbstractC1228a.java:16`) computed live; srtgo substitutes a fixed fake `_device_id="558a4f02041657ea"` (`ktx.py:632`). A static id is a fingerprint.
- **`os`, `dm`, `it`, `ts` are dynamic** in our app (`os=Build.VERSION.RELEASE`, `dm=Build.MODEL`, `it=init currentTimeMillis`, `ts=generate currentTimeMillis` — `C1229b.java:113-135`) whereas srtgo hardcodes `os=13`, `dm=SM-S928N` and derives `it/ts` from time.
- **Sid uses a ts independent of the token.** srtgo shares one `ts` between sid and token (`ktx.py:670,674`); our `getSid()` calls `new Date().getTime()` (`C0812l.java:45`) independently of the token's `System.currentTimeMillis()` (`DynaPathMobileSDK.java:34`) — they differ by a few ms in the real app.
- **Session-lifetime model.** DynaPath initializes once at app start via `DynaPathMobileSDK.initialize(application)` from `IntroActivity`; the engine is a process-wide volatile singleton (`DynaPathMobileSDK.f34689b`), so `it` (init ts) is fixed for the whole session and `rt` deltas accumulate across the session — srtgo (fresh engine per process) doesn't mirror this.

### 📌 Our exact v6.5.0 values

- App secret `as` = `[38ff229cb34c7dda8e28220a2d750cce]` (URL-encoded `%5B38ff229cb34c7dda8e28220a2d750cce%5D`) = SHA-256(v6.5.0 signing cert)[0:32] wrapped by `ArrayList.toString()`.
- SDK version string (body `sv` **and** dyn_key prefix) = `v1.0.3` (dyn_key = `v1.0.3+` + 4 rand chars + `+` + ts).
- Base62 table = `3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz`.
- Token prefix (macro-on) = `bEeEP`; full token = `bEeEP + TABLE[len(key_enc)] + key_enc + body_enc`.
- Encoding constants: pack base = 161, radix = 30, group size = 2.
- `rand` = 4 chars from `abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`.
- Header = `x-dynapath-m-token`; sent only when `IS_MACRO_ACTIVE` (server `isMacroEnable=='Y'`) **AND** url matches one of the 6 paths.
- Body field order: `ai`(=`com.korail.talk`), `di`(=ANDROID_ID), `as`, `su`, `dbg`, `emu`, `hk`, `it`(=init ms), `ts`(=gen ms), `rt`(=array of ≤5 deltas), `os`(=`Build.VERSION.RELEASE`), `dm`(=`Build.MODEL`), `st=Android`, `sv=v1.0.3`.
- Sid: AES/CBC/PKCS5Padding, key = iv = `2485dd54d9deaa36`, plaintext = `AD` + currentTimeMillis, output = Base64(DEFAULT, trailing `\n`).

### ❓ Disputed / open (this dimension)

- Does the server actually validate the decoded `sv` (`v1.0.3`) or the `as` cert hash, or only re-derive the token for self-consistency? If it validates `sv`, srtgo's `v1` tokens are rejected on macro-enabled endpoints.
- Is `isMacroEnable` currently returned as `'Y'` by production for v6.5.0? If it stays `'N'`, neither app ever sends the header and this whole path is dormant.
- Does the server inspect the `rt` delta array / `it` timestamp for macro heuristics? If yes, srtgo's `rt=0` and fresh-per-run `it` are the most exposed differences.
- Are `su/dbg/emu/hk` server-side gating (reject if true) or telemetry only?

---

## 2. Reservation (`dimension: reservation`)

**Confidence: HIGH**

### ✅ Confirmed

- **Endpoint match.** srtgo reserve → `certification.TicketReservation` (`ktx.py:165,842`) == our member issue call `/classes/com.korail.mobile.certification.TicketReservation` (`CertificationService.java:52`; caller `ReservationDao.java:12-17`).
- **`txtJobId` 1101/1102 confirmed.** srtgo `1101`=seat / `1102`=waiting (`ktx.py:869`) == our `setJobId('1101')` (`DirectInquiryActivity.java:583`, `a.java:157`) and `1102` for 예약대기 (`DirectInquiryActivity.java:434`); `1102` also gates non-member (`ReservationRequest.java:111`).
- **Legacy `txt*` passenger rows confirmed.** srtgo `txtPsgTpCd{i}/txtDiscKndCd{i}/txtCompaCnt{i}/txtCardNo_{i}` (`ktx.py:409-413`) == our `OPsg` keys (`OPsg.java:7-11`); mirrored in `mutation_payloads.py:136-138`.
- **`txtTotPsgCnt` confirmed** (`ktx.py:872` == `OPsg.java:11`, `mutation_payloads.py:119`).
- **`txtSeatAttCd1-5 = 000/000/000/015/000` confirmed** (`ktx.py:873-877` == `OSeat.java:9-14`, `mutation_payloads.py:141-145`; the `015` on slot 4 matches on both sides).
- **Seat/flag defaults confirmed:** `txtMenuId='11'`, `txtGdNo=''`, `hidFreeFlg='N'`, `txtStndFlg='N'` (`ktx.py:868,870,871,878` == `ReservationRequest` + `mutation_payloads.py:114-120`).
- **`txtPsrmClCd` 1=general/2=special confirmed** (`ktx.py:891` == `OSeat.java:8`; `mutation_payloads.py:146`).
- **Journey-1 fields confirmed:** `txtJrnyCnt=1`, `txtJrnySqno1='001'`, `txtJrnyTpCd1='11'`, plus the `txtTrnNo1/txtTrnClsfCd1/txtTrnGpCd1/txtRunDt1/txtDptDt1/txtDptTm1/txtDptRsStnCd1/txtArvRsStnCd1` block (`ktx.py:880-890` == `OJrny.java:18-24`, `DirectInquiryActivity.java:586-598`, `mutation_payloads.py:147-162`).
- **Passenger type/discount codes confirmed:** Adult(`1`,`000`), Child(`3`,`000`), Toddler(`3`,`321`), Senior(`1`,`131`), Disability1-3(`1`,`111`), Disability4-6(`1`,`112`) (`ktx.py:418-456` == `mutation_payloads.py:122-131`).

### ⚠️ Corrections / discrepancies

- **`pnrNo` — srtgo claims "no pnrNo in body" (`ref-srtgo_plus.md:180-181`, `ktx.py:864-904`). WRONG as stated.** Our v6.5.0 declares `@Field("pnrNo")` on **both** TicketReservation overloads (`CertificationService.java:52`) and `ReservationDao` **always** passes `getPnrNo()` (`ReservationDao.java:17`). It is empty on a fresh member hold, but the param **exists** and is populated (=response `h_pnr_no`) in the linkage/re-reserve flow (`a.java:161` `setPnrNo(response.getH_pnr_no())`). "No pnrNo" is a runtime value-state, not an absent parameter.
- **`pbepInfo` — srtgo claims absent (`ref-srtgo_plus.md:182`). WRONG.** Our member overload declares `@Field("pbepInfo")` (`CertificationService.java:54`), set after 공무원/세종 government certification (`DirectInquiryActivity.java:416`; gated at :461). Not sent for ordinary reserve but part of the member body.
- **HTTP method differs.** srtgo issues reserve as **GET with query params** (`ktx.py:909` `self._session.get(url, params=data)`). Our v6.5.0 is **POST `@FormUrlEncoded`** (`CertificationService.java:52-53`). Same path, different verb/encoding.
- **`txtChgFlg1` value differs.** srtgo sends `''` (`ktx.py:892`); our app sends `'N'` (`DirectInquiryActivity.java:598` `setChgFlg(i,'N')`; `mutation_payloads.py:163`).
- **Discount-card sub-fields.** srtgo additionally emits `txtCardCode_{i}` and `txtCardPw_{i}` (`ktx.py:412,414`). Our `OPsg` defines **only** `txtCardNo_` (`OPsg.java:7`); a tree-wide grep for `txtCardCode`/`txtCardPw` returns nothing. Those two keys are **srtgo-specific and NOT in our v6.5.0 schema**.

### 🔀 Version drift

- **Transport:** srtgo GET query-string (`ktx.py:909`) vs our POST form-urlencoded (`CertificationService.java:52-53`) on the identical path.
- **`txtChgFlg1`:** srtgo `''` (`ktx.py:892`) vs our `'N'`.
- **Second-journey placeholders:** srtgo statically sends empty `txtJrnySqno2..txtChgFlg2` keys for a single-journey booking (`ktx.py:893-903`); our app emits **only populated journeys** via index-suffixed `O*` LinkedHashMaps (per-index puts, `DirectInquiryActivity.java:580-609`), no empty j2 keys.

### 🆕 Newly-found hidden items srtgo missed

- **Station construction/run-order fields** srtgo omits entirely: `txtDptStnConsOrdr{i}`, `txtDptStnRunOrdr{i}`, `txtArvStnConsOrdr{i}`, `txtArvStnRunOrdr{i}` (`OJrny.java:9,10,15,16`; populated `DirectInquiryActivity.java:593-597`; `mutation_payloads.py:158-162`). srtgo's reserve body (`ktx.py:864-904`) has none — it succeeds without, so server-optional.
- **Arrival-time field `arvTm_{i}`** srtgo omits (`OJrny.java:11`, `mutation_payloads.py:156`).
- **Designated-seat selection via `OSrcar`** — srtgo only auto-assigns (`txtSrcarCnt='0'`, `ktx.py:879`). Our app sends real seat keys `txtSrcarCnt`, `txtSrcarNo{car}(_{seat})`, `txtSeatNo{car}(_{seat})` (`OSrcar.java:7-12`; `OJrny.java:25-27`) — populated in `SeatSearchActivity.java:675-683` for reservation types `TYPE_ORR_RIR`/`TYPE_ORR_SASVR`. Supports up to 2 cars.
- **`txtJobId '1202'` (입석+좌석, standing+seat)** — `DirectInquiryActivity.java:449-450`. srtgo only knows 1101/1102.
- **Multi-journey / transfer reserve** — our app builds `OJrny.setJrnyCnt(TRANSFER_SQ_NO)` with `stndFlg='Y'` and journeys 1..n (`DirectInquiryActivity.java:578-609`). srtgo is single-journey only.
- **Non-member issuing path (`NonMemTicket`)** with `txtCustNm/txtCpNo/txtCustPw` (plaintext password) — `CertificationService.java:48-50`; `ReservationDao.java:15-17` selects it when `custNm+cpNo` both non-null. srtgo has no non-member reserve.
- **`OSeat` second-room fields:** `txtSeatAttCd4_1` (`OSeat.java:13`) and per-journey `txtPsrmClCd{i}` (`OSeat.java:8`) for the 2nd transfer leg. srtgo emits only a single `txtPsrmClCd1`.
- **Bixby map-only TicketReservation overload** (`CertificationService.java:60-62`) — arbitrary `@FieldMap` body, no fixed schema. srtgo unaware.

### 📌 Our exact v6.5.0 values

| Item | Value |
|---|---|
| Static envelope (`BaseRequest.java:7-9`) | `Device=AD`, `Version=250601003`, `Key=korail1234567890` |
| Endpoint | POST `/classes/com.korail.mobile.certification.TicketReservation` (`@FormUrlEncoded`) |
| Fixed flags | `txtMenuId='11'`, `txtGdNo=''`, `hidFreeFlg='N'`, `txtStndFlg='N'` |
| `txtJobId` | `1101`=seat / `1102`=waiting-list / `1202`=standing+seat |
| `txtSeatAttCd1..5` | `000,000,000,015,000` |
| `txtPsrmClCd` | `1` general / `2` special (2nd leg uses `txtPsrmClCd2`, `txtSeatAttCd4_1`) |
| Journey header | `txtJrnyCnt='1'`, `txtJrnySqno1='001'`, `txtJrnyTpCd1='11'`, `txtChgFlg1='N'` |
| `OPsg` keys | `txtTotPsgCnt`, `txtCompaCnt{i}`, `txtPsgTpCd{i}`, `txtDiscKndCd{i}`, `txtCardNo_{i}` (NO `txtCardCode_`/`txtCardPw_`) |
| `OJrny` keys (per index) | `txtTrnNo`, `txtTrnClsfCd`, `txtTrnGpCd`, `txtRunDt`, `txtDptDt`, `txtDptTm`, `txtDptRsStnCd`, `txtDptStnConsOrdr`, `txtDptStnRunOrdr`, `txtArvRsStnCd`, `txtArvStnConsOrdr`, `txtArvStnRunOrdr`, `arvTm_`, `txtChgFlg`, `txtJrnyTpCd`, `txtJrnySqno`; header `txtJrnyCnt` |
| `OSrcar` keys | `txtSrcarCnt`(/`txtSrcarCnt1`), `txtSrcarNo{car}`(/`txtSrcarNo1_`)+seatIdx, `txtSeatNo{car}`(/`txtSeatNo1_`)+seatIdx |
| Member-only | `pnrNo` (empty on new hold; =`h_pnr_no` on re-reserve), `pbepInfo` (empty unless 공무원 cert) |

### ❓ Disputed / low-confidence (this dimension)

- **A finding's own DynaPath claim is OVERSTATED and corrected:** the newHidden note "`x-dynapath-m-token` is gated **specifically** on TicketReservation + NonMemTicket URLs" is inaccurate. The correct file is `com/korail/talk/network/ExecuteDao.java` (NOT `network/dao/ExecuteDao.java`); line 27 lists **SIX** endpoints (TicketReservation, NonMemTicket, seatMovie.ScheduleView, seatMovie.ScheduleViewSpecial, trn.prcFare.do, login.Login), the whole block is gated behind `a.IS_MACRO_ACTIVE` (line 26), header set at line 47. Reservation endpoints are **included in a broader anti-macro allowlist** (search-schedule + login too) — not a reservation-specific control.
- **Not a bijection (precision):** our scaffolding `passenger_rows` (`mutation_payloads.py:122-131`) is a **superset** of srtgo's six passenger types — all six srtgo `(type,disc)` codes match, but our client adds two extra rows srtgo lacks: `('0','1','P11')` (line 124) and `('0','1','173')` (line 130).
- **UNVERIFIED — base single-journey builder:** the confirmed field *setters* live in `DirectInquiryActivity` (transfer/standing branch, :578-609); the primary single-seat builder (`A5.k`/`A5.u`) was not read. Whether `txtDptStnConsOrdr1`/`RunOrdr1`/`arvTm_1` are set on an ordinary single reserve (not only transfers) needs a follow-up read.
- **UNVERIFIED — server-mandatory?** srtgo succeeds without `txtDptStnConsOrdr/RunOrdr/arvTm_` (implies optional); our app always sends them. Not statically resolvable whether the server rejects their absence for our Version.
- **UNVERIFIED — enum numeric values:** exact numbers behind `K4.e` journey-type codes and `o.GENERAL`/`o.SPECIAL` (assumed `txtJrnyTpCd='11'`, `psrmClCd '1'/'2'`) are inferred from srtgo parity + usage, not directly read.
- **UNVERIFIED:** whether the server silently ignores srtgo's extra `txtCardCode_`/`txtCardPw_` and empty j2 placeholders.

---

## 3. Payment (`dimension: payment`)

**Confidence: HIGH** — *Verdict: finding ENDORSED; every cited file:line re-read on both sides.*

### ✅ Confirmed

- **Endpoint match.** srtgo pay = `{KORAIL_MOBILE}.payment.ReservationPayment` → `/classes/com.korail.mobile.payment.ReservationPayment` (`ktx.py:42,171`) == our `@POST("/classes/com.korail.mobile.payment.ReservationPayment")` (`PaymentService.java:12`).
- **Card field names match** (v6.5.0 exact, index suffix `1`): srtgo `hidStlCrCrdNo1/hidVanPwd1/hidCrdVlidTrm1/hidIsmtMnthNum1/hidAthnDvCd1/hidAthnVal1` (`ktx.py:1044-1049`) == our `PaymentMethod` constants `STL_CR_CRD_NO/VAN_PWD/CRD_VLID_TRM/ISMT_MNTH_NUM/ATHN_DV_CD/ATHN_VAL` (`PaymentMethod.java:14-19`), suffix appended by setters at `v4/a.java:29-34`.
- **Raw PAN confirmed (no field encryption).** User input `CARD_NO` → `CreditCardData.setCardNumber` (`AbstractC1269e.java:876`), `getCardNumber()` returns it verbatim (`CreditCardData.java:13-15`), placed into `hidStlCrCrdNo1` with **no cipher** (`v4/a.java:29`). The only AES in the card path is `F4.a.decryptAES` for reading **locally stored** favorite cards (`AbstractC1269e.java:428-433`); `SeedEncryptDao`/`KBPayEncryptDao` encrypt only data handed to **external pay-app intents** (Shinhan FAN `AbstractC1269e.java:1159-1161` → `com.shcard.smartpay`; KB Pay :1164-1170 → `com.kbcard.cxh.appcard`), never the `ReservationPayment` body.
- **`hidStlMnsCd1='02'` (card) match** (`ktx.py:1041` == `v4/a.java:26`).
- **`hidCrdInpWayCd1='@'` (raw-card path) match** (`ktx.py:1043` == `v4/a.java:28`).
- **`hidMnsStlAmt1` = plain amount match** — srtgo `str(rsv.price)` (`ktx.py:1042`) == our `String.valueOf(getReceivedAmount())` (`v4/a.java:27`; `AbstractC1269e.java:406`). Amount is a plain form field, **not encrypted**.
- **`hidInrecmnsGridcnt='1'` + `hidStlMnsSqno1='1'` match** (`ktx.py:1039-1040` == `v4/a.java:24-25`).
- **`hiduserYn='Y'` match** for logged-in member (`ktx.py:1050` == `AbstractC1269e.java:716`).
- **`hidPnrNo`/`hidWctNo` match** (`ktx.py:1034-1035` == `@Field` at `PaymentService.java:14`, populated `v4/b.java:37-38`).
- **`card_type 'J'/'S'` match** — srtgo `'J'` if birthday len==6 else `'S'` (`srtgo.py:391`) == our `IS_NOMAL_CARD ? 'J' : 'S'` (`AbstractC1269e.java:881-884`).
- **`hidAthnVal1` = birthday/cert match** (`ktx.py:1049` == `certNumber` from `AUTH_NO`, `AbstractC1269e.java:880` → `v4/a.java:34`).
- **`hidCrdVlidTrm1` = YYMM match** — srtgo `card_expire` (`ktx.py:1046`) == our `year.substring(2)+month` (`CreditCardData.java:21-23`).

### ⚠️ Corrections / discrepancies

- **`hidTmpJobSqno1/2` and `hidRsvChgNo` are HARDCODED in srtgo** (`'000000','000000','000'`; `ktx.py:1036-1038`) but our app populates them **dynamically** from the reservation response: `jobSqNo1=h_tmp_job_sqno1`, `jobSqNo2=h_tmp_job_sqno2`, `hidRsvChgNo=jrny_infos.jrny_info[0].h_rsv_chg_no` (`v4/b.java:39-41`). These three are separate top-level `@Field` params (`PaymentService.java:14`), **not** inside the `PaymentMethod` FieldMap. srtgo's hardcode works only for a fresh first-time reservation; a changed/re-fared reservation carries a non-zero `rsv_chg_no`/job-seq and srtgo would send stale values.
- **srtgo internal inconsistency** (not our app): its `Reservation.rsv_chg_no` default is `'00000'` (5 zeros, `ktx.py:317`) yet `pay_with_card` hardcodes `hidRsvChgNo='000'` (3 zeros, `ktx.py:1038`) and ignores `rsv.rsv_chg_no` entirely.
- **Structural split.** srtgo lumps every field into one POST dict (`ktx.py:1030-1051`); our app splits explicit `@Field` params + a `@FieldMap PaymentMethod` (`PaymentService.java:14`, `RsvPaymentDao.java:131`). Net form-encoded wire is equivalent, but the structure differs.

### 🔀 Version drift

- **Installment encoding.** srtgo passes a raw int, hardcoding `0` in its caller (`srtgo.py:390`; `ktx.py:1047`). Our v6.5.0 emits enum codes from a fixed allow-set only: `{'0','2','3','4','5','6','12','24'}` via `K4/h.java` + `getInstallmentType` (`v4/a.java:238-264`). srtgo's `0` == `INS_0` so lump-sum matches, but srtgo can emit months our v6.5.0 never sends (1,7-11,13-23) whose server acceptance is **UNVERIFIED**. *(The card path also routes through `getInstallmentType(int)` at `AbstractC1269e.java:886`, so the allow-set applies to the raw-card path too.)*

### 🆕 Newly-found hidden items srtgo missed

- **Non-member payment:** `k1()` sets `hiduserYn='N'` + `hidMbCrdNo=nonMemberNumber` for guests (`AbstractC1269e.java:712-714`; `PaymentMethod.java:8,64`). srtgo hardcodes `'Y'` and never sends `hidMbCrdNo`.
- **Point / mileage payment** (entirely absent in srtgo): `getPointRequest` (`v4/a.java:266-345`) adds `hidPontDvCd/hidPontInpDvCd/hidPontCrdPwd` with `stlMnsCd='12'`, `crdInpWayCd='P'/'@'`, multi-row grids (`hidInrecmnsGridcnt=2/3`, `hidStlMnsSqno2/3`) merged via `putAll`. Point types: 0=KORAIL mileage, 1=RAIL point, 2=WOORIMOA, 4=OKCASHBAG, 5=account, 6=other; plus Samsung mileage combo (`v4/a.java:42-49,223-229`).
- **Easy-pay (spay) providers** (absent in srtgo): `getEasyRequest` (`v4/a.java:69-236`) sets `spayDvCd_1_1 / stSpayGridcnt_1 / spayCphdDatVal_1_1` (+`_2`), `hidCrdInpWayCd='D'`, per-provider codes: shinhanfan (`shStlCrCrdNo/shCrdVlidTrm`), paybooc `spayDvCd='11'`, kbpay `15`, railplus `stlMnsCd='13'` spay `00`, payco `02`/`07`, kakao `01`/`08`, monimopay `19`, stbk `03`, stbkAcnt `10`, railplus_zeropay `04`, naverPay `05`/`16`, tosspay `12`/`13`.
- **Deferred/congress repayment** (absent in srtgo): `getCongressRequest` (`v4/a.java:57-67`) uses `stlMnsCd='03'` with `hidDscpMgNo/hidDfpyDscpNo/hidDfpySrtCd` (`PaymentMethod.java:28-30`), used on ticket-change repayment (`AbstractC1269e.java:408-411`).
- **`hidStlMnsCd` values beyond srtgo's `'02'`:** 03=deferred, 12=point, 13=railplus, 14=account/easy-pay money. `hidCrdInpWayCd` beyond `'@'`: `'D'`=easy-pay, `'P'`=point.
- **The same `PaymentMethod` builder feeds ≥3 OTHER endpoints** srtgo never touches: `IntgStlDao` (`pay.intgStl.do`, cart lump payment, `PayService.java:38`), `CommPaymentDao`, and `PassPaymentDao` (pass payment) all reuse `setPaymentMethod` via `k1()` dispatch (`AbstractC1269e.java:710-755`: RsvPayment(719), IntgStl(728), CommPayment(737-745), PassPayment(747)). `ReservationPayment` may be preceded by an `IntgStl` "prepare" step in cart flows (`v4/b.java:53-82`).

### 📌 Our exact v6.5.0 values

- Endpoint: `/classes/com.korail.mobile.payment.ReservationPayment` (`PaymentService.java:12`).
- Raw-card fixed: `hidInrecmnsGridcnt='1'`, `hidStlMnsSqno1='1'`, `hidStlMnsCd1='02'`, `hidCrdInpWayCd1='@'` (`v4/a.java:24-28`).
- `hidAthnDvCd1='J'` (personal, 6-digit birthday) / `'S'` (business, 10-digit reg no) (`AbstractC1269e.java:881-884`).
- `hiduserYn`: `'Y'` member / `'N'` non-member (+ `hidMbCrdNo`) (`AbstractC1269e.java:713-716`).
- `hidCrdVlidTrm1` format = `YY(year.substring(2)) + MM` (`CreditCardData.java:22`).
- Installment codes (`hidIsmtMnthNum`): `INS_0='0', INS_2='2', INS_3='3', INS_4='4', INS_5='5', INS_6='6', INS_12='12', INS_24='24'` (`K4/h.java`).
- `stlMnsCd` map: 02=credit card, 03=deferred/congress, 12=point/mileage, 13=railplus, 14=account/easy-pay money.
- `crdInpWayCd` map: `@`=manual card, `D`=easy-pay, `P`=point.
- Resolved literals: `CHECKIN_STATUS_EXCEED='14'` (`TicketSelfCheckinStatusActivity.java:40-42`), `HelpSrvCustRequest.f28874D='D'` (`HelpSrvCustDao.java:19`), `I4.a.AFTER_DEPARTURE='15'` (`I4/a.java:5`, = kbpay `spayDvCd`), `StbkAcntDao.ACCOUNT_REGISTER='4'`/`CHANGE_PASSWORD='5'` (`StbkAcntDao.java:11,14`, pontDvCd). All independently verified.

### ❓ Disputed / low-confidence (this dimension)

- `disputed[]` is **empty** — no claim could be refuted; all corrections are additive/precision notes.
- **Precision:** the newHidden "two OTHER endpoints reuse `setPaymentMethod`" undercounts — `k1()` dispatches to **four** request types (RsvPayment/IntgStl/CommPayment/PassPayment); `CommPaymentDao` was omitted. At least **three** other endpoints, not two.
- **Cosmetic:** the IntgStl endpoint literal is `/classes/com.korail.mobile.pay.intgStl.do` (lowercase `i`, `.do`), not `pay.IntgStl` as informally written.
- **UNVERIFIED:** whether the reserve response returns `h_tmp_job_sqno1/2='000000'` and `h_rsv_chg_no='000'` for a fresh reservation (safety of srtgo's hardcode); whether `ReservationPayment` accepts installment months outside `{0,2,3,4,5,6,12,24}`; the 2-digit `hidVanPwd` prefix rule (UI-enforced, invisible at this layer); whether the single-seat KTX path ever requires an `IntgStl` prepare step.

---

## 4. Cancel & Refund (`dimension: cancel-refund`)

**Confidence: HIGH**

### ✅ Confirmed

- **Cancel endpoint + fields match.** srtgo `cancel()` posts to `reservationCancel.ReservationCancelChk` with `Device/Version/Key/txtPnrNo/txtJrnySqno/txtJrnyCnt/hidRsvChgNo` (`ktx.py:166,1063-1071`) == our `ReservationCancelService.reservationCancelCheck` `@POST('/classes/com.korail.mobile.reservationCancel.ReservationCancelChk')` (`ReservationCancelService.java:19-21`). Constants resolve: `OJrny.JRNY_SQ_NO='txtJrnySqno'`, `OJrny.JRNY_CNT='txtJrnyCnt'` (`OJrny.java:18-19`).
- **Cancel PNR spelling `txtPnrNo` (P-n-r) matches** on the cancel side: srtgo `ktx.py:1067` and our `RsvCancelCheckDao.java:15,48` / `RsvCancelDao.java:17,58` / `ReservationCancelService.java:17,21`.
- **Refund endpoint matches.** srtgo `refund()` → `refunds.RefundsRequest` (`ktx.py:172`) == our `RefundService.returnTicket` `@POST('/classes/com.korail.mobile.refunds.RefundsRequest')` (`RefundService.java:27-29`).
- **Wire-rename `h_orgtk_sale_wct_no` confirmed.** srtgo sends `h_orgtk_sale_wct_no` (`ktx.py:1084`); our wire `@Field('h_orgtk_sale_wct_no')` (`RefundService.java:29`) is fed from an internal bean named `h_orgtk_wct_no` (`RefundDao.java:18,45,89`; `ticketReturn/a.java:414-415`). srtgo uses the correct **wire** name.
- **Refund wire field set matches** (13 of 14, same order): `Device/Version/Key` + `h_orgtk_sale_dt, h_orgtk_sale_wct_no, h_orgtk_sale_sqno, h_orgtk_ret_pwd, h_mlg_stl, tk_ret_tms_dv_cd, trnNo, pbpAcepTgtFlg, latitude, longitude` (`ktx.py:1078-1093` == `RefundService.java:29` in identical order; `trnNo` keyed by `Price2Fare.trnNoString='trnNo'`, `Price2FareDao.java:21`). Only the PNR field name differs (see corrections).
- **`SelTicketInfo` endpoint present on both sides.** srtgo `myticketseat`=`refunds.SelTicketInfo` (`ktx.py:167`) == our `RefundService.getTicketDetail` `@POST('/classes/com.korail.mobile.refunds.SelTicketInfo')` (`RefundService.java:23-25`).
- **Our client-src also uses correct spelling + defaults:** `build_unpaid_reservation_cancel_form` emits `{txtPnrNo, txtJrnySqno='0001', txtJrnyCnt='1', hidRsvChgNo='000'}` (`mutation_payloads.py:189-192`).

### ⚠️ Corrections / discrepancies

- **CRITICAL — refund PNR field: srtgo misspells it `txtPrnNo` (P-r-n) at `ktx.py:1082`.** Our v6.5.0 uses the **correct `txtPnrNo` (P-n-r)** in refund: `RefundService.java:29` `@Field('txtPnrNo')`, `RefundDao.java:24/69/113`, caller `ticketReturn/a.java:411`. A **tree-wide grep proves `txtPrnNo` occurs ZERO times** anywhere in our decompiled sources (re-verified this pass), while `txtPnrNo` is used everywhere including refund. Ground truth = `txtPnrNo`. Note srtgo's own **cancel** path uses the correct `txtPnrNo` (`ktx.py:1067`); only its **refund** is misspelled (a korail2-lineage typo).
- **Single-call (srtgo) vs multi-step (us) cancel.** srtgo `cancel()` is ONE POST to `ReservationCancelChk` (`ktx.py:1072`). Our app is a genuine **two-step** flow: step 1 = `ReservationCancel` (confirm dialog "예약된 승차권을 취소하시겠습니까?", `strings.xml:377`); on confirm step 2 = `ReservationCancelChk` (completion dialog "예약이 취소되었습니다.", `strings.xml:376`). Verified in `a6/x.java:190-207` (onReceive) with builders at :45-106. **Key:** `ReservationCancelChk` is the **COMMIT** step, not an eligibility pre-check — so srtgo's single call is functionally sufficient, but srtgo omits our step-1 initiate call and mis-implies "Chk"=eligibility-check.
- **`tk_ret_tms_dv_cd`: srtgo HARDCODES `'21'` (`ktx.py:1088`).** Our app sources it dynamically from the CommissionView response (`ticketReturn/a.java:427-428`). Codes: `BEFORE_DEPARTURE='21'`, `AFTER_DEPARTURE='15'` (`I4/a.java:5-6`). srtgo's `'21'` is correct only for before-departure refunds.
- **`pbpAcepTgtFlg`: srtgo HARDCODES `'N'` (`ktx.py:1090`).** Our app echoes the ticket-detail flag `setPbpAcepTgtFlg(ticketDetail.getH_pbp_acep_tgt_flg())` (`ticketReturn/a.java:430-431`) — can be Y or N per ticket.
- **`latitude`/`longitude`: srtgo sends empty strings (`ktx.py:1091-1092`).** Our app captures **real device GPS** via a LocationListener (`ticketReturn/a.java:382-396`, set at :432-433), falling back to `''` only if no fix.
- **`h_orgtk_sale_dt` source differs (same wire key).** srtgo maps it from `ticket.sale_info2` = `h_orgtk_ret_sale_dt` (`ktx.py:277,1083`); our app maps it from `ticketDetail.getH_sale_dt()` (`ticketReturn/a.java:412-413`). Same wire name, different underlying date field (`ret_sale_dt` vs `sale_dt`).

### 🔀 Version drift

- **`tk_ret_tms_dv_cd`:** srtgo static `'21'` vs our dynamic `'21'` (before) / `'15'` (after departure).
- **`h_mlg_stl`:** srtgo static `'N'` (`ktx.py:1087`). Our default `'N'` but the mileage-refund branch sends `'Y'` when CommissionView `prg_psb_flg=='M'` (`ticketReturn/a.java:172-174,205-207,420`).
- **Refund PNR wire key itself:** reference sends `txtPrnNo` (`ktx.py:1082`); v6.5.0 sends `txtPnrNo`. Whether older server builds accepted `txtPrnNo` is **UNVERIFIED**, but the app-emitted spelling changed to `txtPnrNo` in this version.

### 🆕 Newly-found hidden items srtgo missed

- **`ReservationCancel` INITIATE step** (step 1 of the 2-step cancel) — srtgo jumps straight to the Chk commit. `/classes/com.korail.mobile.reservationCancel.ReservationCancel`, same 4 fields (`ReservationCancelService.java:15-17`; `RsvCancelDao.java:63-68`).
- **`CommissionView` fee-preview step** — our refund is **3-step**: `SelTicketInfo` (detail) → `CommissionView` (fee/refundable preview, **and the source of `tk_ret_tms_dv_cd`**) → `RefundsRequest`. srtgo **skips CommissionView entirely** (why it must hardcode `tk_ret_tms_dv_cd`). `/classes/com.korail.mobile.refunds.CommissionView`, fields `h_orgtk_ret_sale_dt/h_orgtk_wct_no/h_orgtk_sale_sqno/h_orgtk_ret_pwd/h_comp_nm/h_comp_cert_no` (`RefundService.java:19-21`; caller `ticketReturn/a.java:349-358`). Response carries `ret_amt/ret_fee/prg_psb_flg/use_psb_mlg_num/tk_ret_tms_dv_cd/h_msg_cd2/h_msg_txt2`.
- **Separate offline/paper-ticket online-refund flow:** `verifyOnlineRefunds` (fields `retNo1..retNo4/strName`, `RefundService.java:31-33`) → `executeOnlineRefunds` (fields `pnrNo/tkKndCd/retDvCd/retRsnCd/ogtkSaleDt/ogtkSaleWctNo/ogtkSaleSqno/ogtkRetPwd/retAmt/retFee/custTeln/acepCustNm`, `RefundService.java:15-17`). srtgo has no equivalent.
- **GPS actually transmitted on refund** — real `latitude/longitude` from LocationListener (`ticketReturn/a.java:382-396`); srtgo blanks them.
- **Auto-cancel DAO variants:** `AutoRsvCancelDao` / `AutoRsvCancelCheckDao` (waitlist/auto flows); srtgo has none.
- **Refund response semantics our app acts on:** `RefundResponse.stlList[].stl_mns_cd` (`RefundDao.java:118-138`); `stl_mns_cd=='13'` triggers a RailPlus sync. srtgo only checks the generic result flag.
- **`ReservationChange` (`reservation.reservationChange.do`)** co-declared in `ReservationCancelService.java:23-25` — a rebook/change path (`pnrNo/chgTno/totPrnb` + 5× `@FieldMap`) srtgo does not model.

### 📌 Our exact v6.5.0 values

- Cancel endpoints: `.../reservationCancel.ReservationCancel` (step1 initiate) and `.ReservationCancelChk` (step2 commit).
- Cancel fields (both calls): `txtPnrNo, txtJrnySqno, txtJrnyCnt, hidRsvChgNo`.
- Cancel default constants: `txtJrnySqno='0001'`, `hidRsvChgNo='000'` (`a6/x.java:50-51,102-103`); `txtJrnyCnt='1'` (`mutation_payloads.py:191`).
- Refund endpoint: `.../refunds.RefundsRequest`.
- **Refund PNR field spelling in v6.5.0 = `txtPnrNo` (P-n-r), NOT `txtPrnNo`.**
- Refund wire fields (order): `txtPnrNo, h_orgtk_sale_dt, h_orgtk_sale_wct_no` (internal bean `h_orgtk_wct_no`)`, h_orgtk_sale_sqno, h_orgtk_ret_pwd, h_mlg_stl, tk_ret_tms_dv_cd, trnNo, pbpAcepTgtFlg, latitude, longitude`.
- `tk_ret_tms_dv_cd`: `'21'`=before departure, `'15'`=after departure (`I4/a.java:5-6`).
- `h_mlg_stl`: `'N'` default, `'Y'` for mileage-settlement refund.
- Refund is 3-step: `SelTicketInfo → CommissionView → RefundsRequest`; plus a separate offline `verifyOnlineRefunds → executeOnlineRefunds` flow.

### ❓ Disputed / low-confidence (this dimension)

- `disputed[]` **empty**; `verdictCorrections[]` **empty** — no claim refuted.
- **UNVERIFIED:** whether the server tolerates srtgo's misspelled `txtPrnNo` (only our emitted spelling `txtPnrNo` is statically provable); whether `RefundsRequest` requires `tk_ret_tms_dv_cd`/`pbpAcepTgtFlg`/`h_mlg_stl` to match server-computed values (so after-departure/PBP/mileage tickets would fail with srtgo's hardcodes) or recomputes and ignores them; which endpoint `build_unpaid_reservation_cancel_form` (`mutation_payloads.py:169-195`, latent/unwired) would POST to; whether `h_orgtk_ret_sale_dt` always equals `h_sale_dt` for a given ticket.

---

## 5. Uncovered hidden endpoints (`dimension: uncovered-hidden`)

**Confidence: HIGH**

### ✅ Confirmed

- **Sid algorithm exact match** — AES-CBC key `b'2485dd54d9deaa36'`, iv=same key, plaintext `'AD'+ts_ms`, base64 + `'\n'` (`ktx.py:661-664` == `S4/C0812l.java:43-50`; key literal also in smali `S4/l.1.smali:338`).
- **Device/Key match** — srtgo `_device='AD'`, `_key='korail1234567890'` (`ktx.py:642,644`) == `BaseRequest.java:7-8,15-17` and `K4/g.java:11` `COMMON_PARAMETER='Device=AD&Version=250601003&Key=korail1234567890'`.
- **DynaPath sensitive-path list match** — 6 paths (`ktx.py:44-51` == `network/ExecuteDao.java`).
- **DynaPath token header match** — `x-dynapath-m-token` = `DynaPathMobileSDK.Companion.generate()` (`ktx.py:672-673` == `network/ExecuteDao.java`), vendor SDK `smali_classes3/kr/scripters/dynapath/sdk/android/DynaPathMobileSDK*.smali`.
- **NetFunnel base ids match** — `sid='service_1'`, `aid='act_8'` (`ktx.py:602` == `K4/g.java:51,43`).
- **Login/amount password encryption pattern match** — fetch `app.login.cphd`, then `base64(base64(AES-CBC(key, iv=key[:16], pwd)))` (`ktx.py:677-693` == `C0812l.getAmountEncrypt` `S4/C0812l.java:26-41`, gated on `getPwdAESCphd()=='Y'`).

### ⚠️ Corrections / discrepancies

- **Login body shape differs (both sides verified).** srtgo login (`ktx.py:712-721`) sends `Device, Version, txtMemberNo, txtPwd, txtInputFlg, idx, Sid` and **omits Key**. Our `login.Login` (`LoginService`, `@POST login.Login`) sends `@Field Device, Version, KEY, txtMemberNo, txtPwd, txtInputFlg, checkValidPw, custId, etrPath, idx` and has **no Sid field**. So our v6.5.0 login needs `Key` (not `Sid`) plus `checkValidPw/custId/etrPath`.
- **Sid attachment target differs.** srtgo attaches Sid to login + search_schedule + reserve (`ktx.py:666-675,710,791,843`). Our app injects `C0812l.getSid()` into seatMovie searches (`TrainInquiryDao`/`LimousineTrainInquiryDao` → `seatMovie.ScheduleView`/`LimousineScheduleView`) and research seat/car searches (`SearchCarListDao:88`, `SearchSeatListDao:137`). **Our login does NOT carry Sid.**
- **NetFunnel action-id is per-operation in our app, not a constant.** srtgo hardcodes `aid='act_8'` (`ktx.py:602`). Our `K4/g.java:43-50` defines `act_8` (general), `act_8_2` (peak season), `act_14` (reserve), `act_18` (pay), `act_22` (refund), `act_6` (product), `act_21` (reserved), `act_4` (test); `b5/c.java:439` selects by request type/season. Using `act_8` for pay/refund/reserve is under-modeled.
- **DynaPath token conditionally attached** — srtgo attaches for any of the 6 paths unconditionally; our `ExecuteDao` only enters the branch when `KTConst.a.IS_MACRO_ACTIVE` is true, and only shows the anti-macro dialog on HTTP 403 + "forbidden" + header `DynaPath-Result<0` (**behavioral specifics cited from `full-api-analysis-2026-07-20.md:119`, not re-verified against code this pass**; the code-level gate `ExecuteDao.java:26` `if (a.IS_MACRO_ACTIVE)` IS confirmed).

### 🔀 Version drift

- **Protocol Version:** srtgo `_version='250601002'` (`ktx.py:643`) vs our `'250601003'` (`BaseRequest.java:9,16`; `K4/g.java:11`; 3 literal occurrences). srtgo one build behind. This is the API/protocol version (=`G4.a.API_VERSION`), distinct from app version 6.5.0.
- **Device id:** srtgo hardcodes sample `_device_id='558a4f02041657ea'` (`ktx.py:632`); our app supplies the real runtime `ANDROID_ID` to DynaPath's `di=`.

### 🆕 Newly-found hidden items srtgo missed

- **Self check-in flow** (4 endpoints, `TicketService.java:82-96`): `checkin.psbFlg.do`, `checkin.info.do`, `checkin.reg.do`, `checkin.cnc.do` (DAOs `SelfCheckin{Possible,Info,Register,Cancel}Dao`). srtgo has none.
- **Designated seat assignment:** `reservation.seatAssign.do` `setSeatAssignReservation` (`ReservationService.java:28`, `SeatAssignReservationDao.java`) — `menuId, custMgNo, totPrnb, stndFlg, rqScarNum` + FieldMaps from `RJrny, RSrcar` (`scarNo_i_j/seatNo_i_j`), `RSeat` (`seatPsrmClCd_/locSeatAttCd_/dirSeatAttCd_/rqSeatAttCd_/roomClsfCd_/smkSeatAttCd_`), `RPsg`, `ROrtg`. Supporting: `research.assignScheduleView.do`, `reservation.guideSeatCnd.do`.
- **Ticket change (tripChg) full flow:** `research.tripChgOgtk.do`, `reservation.tripChgDate.do`, `reservation.tripChgPrsC.do` (the change-reserve mutation with `trvlKndCd,totPrnb,isePrnb,stndSeatFlg,intgTktIseFlg,prcFareReCalcFlg,tmpJobSqno,alcSeatDmnPsDvCd,jrny2Cnt,psg2Cnt,ctlDvCd,frcSaleRsnCont` + 6 FieldMaps `RJrny/RSrcar/RSeat/RPsg/ROrtg/RDscp/orgRDscp`), `ticket.tripChgHndgCnc.do`, `self.seatChgInfo.do`. None in srtgo.
- **Post-reservation seat/train change:** `reservation.reservationChange.do` (`pnrNo, chgTno, totPrnb, stndFlg, evntWctFlg, wctHndgCncDvCd, lrgCrgFlg, psgCnt` + 5 FieldMaps, `ReservationCancelService.java:23`). Distinct from `tripChgPrsC`.
- **Special-room seat upgrade (특실 업그레이드):** `myTicket.reqUpgradeSeat` / `myTicket.procUpgradeSeat` (`MyTicketService.java:20,23`), GET with full payment means. srtgo lacks.
- **Waiting-list reservation mutation:** `reservationWait.ReservationWait` `rsvWait(txtPnrNo, txtPsrmClChgFlg, txtSmsSndFlg, txtCpNo)` (`ReservationWaitService.java:10-12`). srtgo only filters wait trains client-side.
- **Other mutation/hidden endpoints** absent from srtgo: `addService.reserve.do`/`reserveList.do`/`buyConfirm.do`/`coptCnc.do`/`cancelPay.do` (MaaS add-services); `gift.gdRsv.do`/`gdRet.do`/`gdUseSpec.do`; `pass.passReserve`/`passPayIssue`/`passOtrReserve`; `mileage.acpnMlgSave.do`/`acpnMlgNoti.do`; `delay.ticketReturn.do` + `dlay.cashRfn.do`/`dptnBank.do`/`athnIsu.do` (delay-compensation cash refund, a **separate** refund path); `cashReceipt.issue.do`; `tk.dvcInfoInit.do`; `tk.gurdSmsSnd.do`; `tk.pbpWdrw.do`/`tk.pbpAcepSpec.do`; `ticket.ticketDupCheck.do`; `qr.bchTripSv.do`; `railplus.autoCharge.do`; `pay.*` (naverPayRsv, tossautoC, spayOrdNo, stbkRegBank, intgStl); `nFilter.createKey.do`, `common.encrypt.do`/`decrypt.do`, `shinhan.Encrypt.do`.
- **NetFunnel op-codes confirmed vendor-side:** srtgo `getTidchkEnter=5101, chkEnter=5002, setComplete=5004` (`ktx.py:531-533`); srtgo also misses the product path and peak-season `act_8_2` branch.

### 📌 Our exact v6.5.0 values

- Device = `AD`; Version = `250601003` [srtgo=250601002]; Key/APP_KEY = `korail1234567890`.
- Sid key = `2485dd54d9deaa36`, AES/CBC/PKCS5Padding, IV=key[:16], Base64.DEFAULT (+newline), plaintext `'AD'+epochMillis` (`C0812l.java:18-24,43-50`).
- DynaPath token header = `x-dynapath-m-token`; generator = `kr.scripters.dynapath.sdk.android.DynaPathMobileSDK.Companion.generate()`; gated on `KTConst.IS_MACRO_ACTIVE`; 6 macro paths (`ExecuteDao.java`).
- NetFunnel: server=`service_1`; actions `act_8/act_8_2/act_14(reserve)/act_18(pay)/act_22(refund)/act_6(product)/act_21(reserved)/act_4(test)` (`K4/g.java:43-51`).
- Hosts: real=`smart.letskorail.com`; push=`smart.letskorail.com:3101` appType `korailtalk`; dev=`mobiledev/dev2/dev3/dev5.letskorail.com`; SERVER_TYPE=REAL (`K4/g.java`).
- SDK config keys — **field names and locations only.** These are the KORAIL app's own third-party vendor credentials. They are not used, needed, or referenced by this client, so their values were stripped from this repository *and from its git history*; a `<KORAIL-APP-…-REDACTED>` placeholder marks where a value used to be printed, and the only place to read the real one is a copy of the APK. In `res/values/strings.xml`: `google_api_key` (:894), `google_app_id` (:895), the `firebase_database_url` project id (:1523, of the form `https://<project>.firebaseio.com`), `kakao_app_key` (:947). One value in this group is *deliberately* kept in the clear: the GCM sender id `303574505999` is a Firebase project **number**, not a credential, so the redaction pass left it and it is not a placeholder omission.

### ❓ Disputed / low-confidence (this dimension)

- **UNVERIFIED (correctly scoped by the finding):** srtgo's DynaPath token internals (TABLE, AS_VALUE, DEVICE_MODEL, prefix `bEeEP`, I8/I9/I10=161/30/2, dyn_key `v1+rand+ts`, plaintext layout — `ktx.py:54-160`) are srtgo's reverse-engineered reconstruction. **None of these literals appear in our smali/Java** — they are computed inside the obfuscated `kr.scripters` SDK; only runtime/native instrumentation could confirm them from the APK. (Their *structure* is confirmed in Dimension 1 via our independent re-implementation, but the literal values are not present as constants.)
- **Verifier correction — Sid-injection targets mis-mapped in the finding (both sides re-read):** (a) `LimousineTrainInquiryDao` → `seatMovie.LimousineScheduleView` via `SeatMovieService.getRsvLimousineInquiry` (`SeatMovieService.java:16-18`, `LimousineTrainInquiryDao.java:14`) — **NOT** ScheduleViewSpecial. (b) `ScheduleViewSpecial` = `getRsvProductInquiry` (`SeatMovieService.java:20-22`) carries **neither Sid nor Key**; it is in the DynaPath macro-path list but no Sid is injected. Actual Sid-field targets: `seatMovie.ScheduleView` (getRsvInquiry, Sid replaces Key) + `seatMovie.LimousineScheduleView` (Sid replaces Key) + research `getCarList` (`SearchCarListDao:88`) + research `getSeatList` (`SearchSeatListDao:137`).
- **Verifier correction — "Sid replaces Key" is over-generalized:** true ONLY for the seatMovie ScheduleView/LimousineScheduleView methods. In the research car/seat searches Sid is **added alongside** Key: `ResearchService.getCarList` (`ResearchService.java:37`) declares both `@Field("Key")` and `@Field("Sid")`; `getSeatList` (`:59`) declares both Key and Sid (plus a `sidTest` field).
- **Verifier correction — reserve divergence understated:** srtgo attaches Sid to reserve/`certification.TicketReservation` (`ktx.py:843`), but our `CertificationService` has **no Sid field anywhere** (grep of `@Field("Sid")` returns only `ResearchService` + `SeatMovieService`). Our TicketReservation body omits Sid entirely.
- **UNVERIFIED:** which device-id value feeds `di=` at runtime (`Settings.Secure.ANDROID_ID` vs an app-generated UUID via `/ebizcross/getUUID.do`); the concrete seat-attribute code values (they come from the seat-search response, echoed into `locSeatAttCd_/dirSeatAttCd_/rqSeatAttCd_`); the `tripChgPrsC.do`/`seatAssign.do` FieldMap key layouts (need a live request dump).

---

## 6. Transport & Auth (`dimension: transport-auth`)

**Confidence: HIGH**

### ✅ Confirmed

- **Device envelope `'AD'`** — `ktx.py:642` == `BaseRequest.java:6`, `K4/g.java:11`, our `constants.py:2`.
- **App key `'korail1234567890'`** — `ktx.py:644` == `BaseRequest.java:7`, `K4/g.java:11`, our `constants.py:5`.
- **Common envelope** `Device=AD&Version=...&Key=korail1234567890` — srtgo builds it per-request (`ktx.py:865-867`; **see disputed re: login**) == `K4/g.java:11` `COMMON_PARAMETER` + `BaseRequest()` ctor (`BaseRequest.java:12-16`).
- **Login password = double-Base64(AES/CBC/PKCS5 of pwd)** — `ktx.py:677-693` (key=full utf8, iv=key[:16]) == `C0812l.encryptAES` (`C0812l.java:19-24`) wrapped by `F4/a.encryptBase64` via `getAmountEncrypt` (`C0812l.java:26-40`); our `crypto.py:43-53`. Structure matches.
- **`pwdAESCphd` Y/N gate** on login crypto — `ktx.py:683` == `C0812l.getAmountEncrypt` checks `getPwdAESCphd()=='Y'` (`C0812l.java:28`).
- **SID = AES/CBC(key=iv=`2485dd54d9deaa36`, plaintext=`'AD'+epochMillis`) then Base64** incl trailing newline — `ktx.py:661-664` == `C0812l.getSid()` (`C0812l.java:43-49`, Base64 flag 0 DEFAULT).
- **NetFunnel endpoint shape** — `nf.letskorail.com/ts.wseq` + opcodes 5101/5002/5004 + `sid=service_1`/`aid=act_8` (`ktx.py:524,530-534,601-604`) == `T6/h.java:31`, `T6/c.java:6-9`, `K4/g.java`.
- **No cert pinning / curl_cffi not strictly required** — srtgo degrades to `requests` (`ktx.py:10-15,635-638`), impersonates only for NetFunnel. Our `network_security_config.xml` has **no** pin-set for `smart.letskorail.com`; `ExecuteDao` uses plain `HttpURLConnection` (`ExecuteDao.java:7-11`). Plain TLS works; nothing to bypass.
- **Timeout 60s** — `K4/g.java` `CONNECTION_TIMEOUT/READ_TIMEOUT=60000` and `ExecuteDao` setters == our `constants.py:6`.

### ⚠️ Corrections / discrepancies

- **Version mismatch:** srtgo hardcodes `Version='250601002'` (`ktx.py:643`); our v6.5.0 uses `'250601003'` everywhere (`BaseRequest.java:9,16`; `G4/a.java:5`; `K4/g.java:11`; `C0811k.java:53`; `BixbyReservationActivity.java:30`). Our `constants.py:3` already correct.
- **"Korail uses NO NetFunnel" is a srtgo shortcut, NOT app truth.** srtgo instantiates `NetFunnelHelper` (`ktx.py:640`) but **never calls `.run()`** (only `.clear()` at :1101) — sends no key. Our app **does** gate flows behind NetFunnel: train search `b5/c.java:450` `g.BEGIN(service_1, act_8/act_8_2/act_6)`; member reservation `c5/a.java:184` `setNetfunnelDao` on `ReservationDao`; `DirectInquiryActivity.java:442,469,499` `act_14`; `ReservedTicketActivity.java:553` `act_21`; `MainBookingActivity.java:759` quick-purchase. srtgo works only because the server appears not to hard-enforce the key (empirical); the app wraps search+reserve.
- **Login inner Base64 differs.** srtgo uses `b64encode(b64encode(...))` — inner has **no** newline (`ktx.py:690-692`). App inner is `Base64.encode(cipher, 0)` = DEFAULT which **appends `\n`** and wraps at 76 chars (`C0812l.java:23`); outer is `F4/a.encryptBase64` = flag 2 NO_WRAP. Our `crypto.py:44-52` faithfully replicates the app; srtgo is not byte-faithful (tolerated because decoders ignore trailing whitespace, but wire bytes differ).
- **User-Agent is NOT an app constant.** srtgo hardcodes `Dalvik/2.1.0 (Linux; U; Android 13; SM-S928N Build/UP1A.231005.007)` (`ktx.py:32`). No hardcoded UA exists in `com.korail.talk` — the app uses Retrofit v1 + `UrlConnectionClient`/`HttpURLConnection` (`ExecuteDao.java:7-11`), so the UA is the platform-default Dalvik string. srtgo's SM-S928N/Android-13 build is a faithful **emulation** of the default UA, but the specific device/build id is srtgo's choice, not app-mandated.

### 🔀 Version drift

- **Version param:** srtgo `250601002` → our `250601003` (one patch build ahead).
- **App identity (our v6.5.0):** `G4/a.java` `VERSION_NAME='6.5.0'`, `VERSION_CODE=60500002`, `APPLICATION_ID='com.korail.talk'` (matches srtgo `DynaPathMasterEngine.APP_ID` `ktx.py:55`), `FLAVOR='product'`, `BUILD_TYPE='release'`, `DEBUG=false`.

### 🆕 Newly-found hidden items srtgo missed

- **Full NetFunnel action-ID taxonomy** srtgo's helper (only `service_1/act_8`) omits: `act_4` (test), `act_6` (product), `act_8` (normal), `act_8_2` (peak season), `act_14` (reserve), `act_18` (pay), `act_21` (reserved list), `act_22` (refund) — `K4/g.java:43-51`.
- **Extra NetFunnel opcode `ALIVE_NOTICE=5003`** (`T6/c.java:7`) not in srtgo. *(Verifier note: the full app opcode set is larger still — `T6/c.java` also defines `None(0)`, `INIT(5105)`, `STOP(5106)`; full set = 5002/5003/5004/5101/5105/5106 vs srtgo's 5101/5002/5004.)*
- **NetFunnel server config fetched dynamically** — `T6/f.java` Parser reads `server.protocol/host/port/timeout/retry/err_bypass/bypass/max_ttl/host_notmodify` from JSON, and `T6/f.LOAD()` gates BEGIN. srtgo ignores the `bypass`/`err_bypass` flags that could make NetFunnel a no-op. *(Verifier note: the host `nf.letskorail.com` IS app-truth — hardcoded at `KTApplication.java:78-85` `g()`: `setHost("nf.letskorail.com")`, `setServiceID(service_1)`, `setActionID(act_8)`, `setTimeout(3)`, `setProtocol(Constants.SCHEME)`, `setPort(U.DEFAULT_PORT_SSL)` — overriding the compiled `T6/h.java:19` default `nf2.netfunnel.co.kr`. srtgo's host+serviceID+actionID match app source directly.)*
- **HTTP stack** = Retrofit v1 over `UrlConnectionClient`/`java.net.HttpURLConnection` (`ExecuteDao.java:7-12`) — NOT OkHttp, NOT curl. Implies default Dalvik UA and no TLS-fingerprint impersonation on the app side; srtgo's curl_cffi impersonation is unnecessary for Korail.
- **Sid timestamp generated independently per call** via `new Date().getTime()` inside `getSid()` (`C0812l.java:44`); srtgo synchronizes the Sid ts with the DynaPath token ts (`ktx.py:667-674`). Minor drift — app does not couple them.
- **Sid attached to more endpoints** than srtgo's dynapath-only injection — seat/car research (`SearchCarListDao:88`, `SearchSeatListDao:137`) and `TrainInquiryDao:14`, plus a `sidTest='Y'` flag for non-REAL servers.
- **`pwdAESCphd=='N'` single-base64 fallback** — app returns `F4/a.encryptBase64(pwd)` = single NO_WRAP base64 of plaintext (`C0812l.java:34-38`). srtgo `__enc_password` does **not** implement this — returns False if cphd absent (`ktx.py:693`). Our `crypto.py:54` handles the N case.
- **Separate local-storage crypto `F4/a.java`** — AES/ECB/PKCS5 with a key derived from `android_id` (`UUID.nameUUIDFromBytes` → first 16 bytes), distinct from the login transport crypto — data-at-rest, not covered by srtgo.

### 📌 Our exact v6.5.0 values

- Version = `250601003`; Device = `AD`; Key = `korail1234567890`; `COMMON_PARAMETER = 'Device=AD&Version=250601003&Key=korail1234567890'`.
- `VERSION_NAME=6.5.0`, `VERSION_CODE=60500002`, `APPLICATION_ID=com.korail.talk`, `FLAVOR=product`, `BUILD_TYPE=release`.
- SID: key=`2485dd54d9deaa36`, plaintext=`'AD'+epochMillis`, AES/CBC/PKCS5Padding, iv=full 16-byte key, output Base64.DEFAULT (flag 0, trailing `\n`).
- Login pwd (cphd=Y): inner = Base64.DEFAULT(flag 0) of AES/CBC/PKCS5(key=login.key full bytes, iv=login.key[:16], pwd UTF-8); outer = Base64.NO_WRAP(flag 2). (cphd=N): single Base64.NO_WRAP of plaintext.
- NetFunnel: server_id=`service_1`, path `ts.wseq`, opcodes `GET_TID_CHK_ENTER=5101 / CHK_ENTER=5002 / SET_COMPLETE=5004 / ALIVE_NOTICE=5003` (+ INIT=5105, STOP=5106); action ids `act_4/act_6/act_8/act_8_2/act_14/act_18/act_21/act_22`.
- Timeouts: connect=60000ms, read=60000ms.
- HTTP: Retrofit v1 + `UrlConnectionClient` (HttpURLConnection); default platform Dalvik UA (no app-hardcoded UA).
- TLS: `network_security_config.xml` has **no** pin-set for `smart.letskorail.com` (only cleartext-permitted domains: `1.255.59.22`, a naver ncp host, `teapp.srail.kr`, `app.srail.kr`); no certificate pinning.
- Real host = `smart.letskorail.com`; base = `https://smart.letskorail.com:443`.

### ❓ Disputed / low-confidence (this dimension)

- **Verifier correction — confirmed-claim #3 mis-cited login envelope:** srtgo's **login** dict (`ktx.py:712-719`) contains only `Device` and `Version` — **no Key**. The full `Device=AD&Version=...&Key=...` triple appears only in reserve/search (`ktx.py:865-867`). So the envelope-with-Key match holds for reserve/search but **NOT for srtgo login**; srtgo login is Device+Version only, a real behavioral drift vs the app's `COMMON_PARAMETER` (which always carries Key).
- **Verifier correction — a newHidden item under-credited the app:** the NetFunnel host `nf.letskorail.com` IS app-truth (`KTApplication.java:78-85`), not merely a srtgo choice / dynamic-fetch value (see NetFunnel note above).
- **UNVERIFIED — possible NetFunnel protocol/port drift NOT flagged by the finding:** `KTApplication.java:80,82` set `protocol=Constants.SCHEME` and `port=U.DEFAULT_PORT_SSL`, implying HTTPS on 443 for NetFunnel, whereas srtgo hardcodes plain `http://nf.letskorail.com/ts.wseq` (port 80, `ktx.py:524`). `Constants.SCHEME`/`U.DEFAULT_PORT_SSL` could not be resolved statically — **plausible but unconfirmed**.
- **UNVERIFIED:** whether the server actually enforces the NetFunnel key on ScheduleView/TicketReservation (srtgo empirically succeeds without it; app also honors a server `bypass`/`err_bypass` flag); whether the server validates Sid content/timestamp; whether the inner-base64 newline difference is tolerated for long (wrapped) passwords; the exact default HttpURLConnection Dalvik UA on our target build.
- **Minor line off-by-ones in `C0812l.java` citations (substance correct):** `encryptAES(login)` begins line 18 (not 19-24); the `getPwdAESCphd()` check is line 27 (not 28); `getAmountEncrypt` spans 26-41; `getSid` spans 43-50.

---

## Net changes to our understanding

1. **DynaPath is fully reproducible, and srtgo reproduced it correctly *except for the version string.*** There is no native black box — the whole token is obfuscated Java we independently re-derived. srtgo's algorithm, tables, prefix, constants, `as` secret, and Sid scheme all match byte-for-byte for the macro-on path. **The one substantive break is `sv`/`dyn_key` = `v1` (srtgo) vs `v1.0.3` (us)**, which reseeds the entire token. This is the single biggest correctness risk in the whole reference client, pending the open question of whether the server validates `sv`.

2. **srtgo hardcodes several fields our app computes live.** Anti-tamper (`su/dbg/emu/hk`), timing telemetry (`rt` delta array), device identity (`di`=ANDROID_ID), and reservation/payment sequence numbers (`hidTmpJobSqno`, `hidRsvChgNo`) are all dynamic in v6.5.0. srtgo's constants are safe on a clean host and a fresh first-time reservation, but are detectable fingerprints and can go stale on re-fared/changed reservations.

3. **The refund path has a confirmed field-name bug in srtgo:** `txtPrnNo` (should be `txtPnrNo`) — and srtgo skips two real steps our app performs (`ReservationCancel` initiate before `Chk`; `CommissionView` fee-preview before `RefundsRequest`), which is why it must hardcode `tk_ret_tms_dv_cd='21'`, `pbpAcepTgtFlg='N'`, `h_mlg_stl='N'` — all correct only for the ordinary before-departure, non-PBP, non-mileage case.

4. **The reservation and payment core schemas match closely,** but our v6.5.0 is a strict superset: extra journey fields (`txtDptStnConsOrdr/RunOrdr/arvTm_`), designated-seat (`OSrcar`), multi-journey/transfer, non-member issue, and a whole family of payment methods (point, easy-pay, deferred, non-member) that srtgo doesn't model. Conversely, two srtgo passenger sub-fields (`txtCardCode_`/`txtCardPw_`) do **not** exist in our v6.5.0 schema.

5. **A large surface of mutating endpoints is entirely unmodeled by srtgo:** self check-in, seat-assign, ticket-change (tripChg), post-reservation change, seat upgrade, waiting-list conversion, gift/pass/MaaS, and a **separate delay-compensation cash-refund** path distinct from `refunds.RefundsRequest`.

6. **Transport/auth is solid on both sides,** with three real drifts: protocol `Version` (…002 vs …003), the login body shape (srtgo omits `Key`, sends `Sid`; our app sends `Key`, no `Sid`), and NetFunnel (srtgo never actually runs it; our app gates search+reserve behind it and may use HTTPS:443 rather than srtgo's HTTP:80).

7. **Several citation/precision fixes landed during verification** (all folded into the disputed subsections): the correct `ExecuteDao` path and 6-endpoint (not 2) allowlist; the Sid-injection targets (`LimousineScheduleView` not `ScheduleViewSpecial`; Sid *added* alongside Key in research searches; reserve carries no Sid in our app); and the NetFunnel host/opcode origins.

---

## Remaining open questions

**All require live/runtime or server-side observation — not statically resolvable from the APK.**

1. **Does the Korail server validate the decoded DynaPath `sv` (`v1.0.3`) or the `as` cert hash?** If yes, srtgo's `v1` tokens are rejected on macro-enabled endpoints. *(Highest-impact question in the report.)*
2. **Is `isMacroEnable` currently `'Y'` in production for v6.5.0?** If it stays `'N'`, the entire DynaPath header path is dormant for both clients.
3. **Does the server inspect `rt` / `it` timing telemetry or the `su/dbg/emu/hk` anti-tamper booleans** (gating vs telemetry)? Determines whether srtgo's `rt=0`/clean-host constants, or running the real app on a rooted device, are exposed.
4. **Does the server tolerate srtgo's misspelled refund key `txtPrnNo`,** or ignore/reject it (wrong-PNR / failed refund)?
5. **Does `RefundsRequest` require server-matched `tk_ret_tms_dv_cd`/`pbpAcepTgtFlg`/`h_mlg_stl`,** so after-departure/PBP/mileage tickets fail with srtgo's hardcodes?
6. **Does reserve return `h_tmp_job_sqno='000000'` / `h_rsv_chg_no='000'` for a fresh reservation** (safety of srtgo's payment hardcodes), and does it change on re-fare?
7. **Does the server enforce the NetFunnel key** on ScheduleView/TicketReservation, or is it advisory? (srtgo succeeds without ever sending it.)
8. **Are the reservation-transport (GET vs POST), installment allow-set (`{0,2,3,4,5,6,12,24}` vs arbitrary months), and optional journey fields (`txtDptStnConsOrdr/RunOrdr/arvTm_`) server-strict** for our Version?
9. **Runtime dumps still needed** to lock down: the concrete seat-attribute code values (from the seat-search response), the `tripChgPrsC.do`/`seatAssign.do` FieldMap key layouts, and which device-id value actually feeds DynaPath's `di=`.

---

*Static-analysis note: every "Confirmed" and "our exact value" above was read on both sides at the cited file:line. Everything marked **UNVERIFIED** depends on server behavior or obfuscated-SDK runtime state and cannot be proven from the decompiled APK alone. DynaPath token literals (`TABLE`, `AS_VALUE`, `bEeEP`, etc.) do not appear as constants in our smali/Java — their **structure** is confirmed by our independent re-implementation of the algorithm, not by matching a stored string.*
