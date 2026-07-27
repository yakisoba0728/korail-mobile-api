# Korail Talk 3차 검증 (verifier-2) — 21건 판정

저장소: korail-mobile-api (이 저장소)
방법: 인용된 file:line 을 전부 직접 열어 확인. 상수 주장은 apktool smali 로 재확인.
마스킹·타입 주장은 `sys.path.insert(0,'src')` 로 in-process 실측(저장소 무수정, git 무조작).

판정 요약: **CONFIRMED 10 / PARTIAL 6 / REFUTED 4 / UNVERIFIABLE 1** (합 21)

- CONFIRMED(10): K3-07, K5-01, K6-02, P2MIS-04, P2SAF-01, P2SAF-09, P2CRO-01,
  P2CRO-13, P2CRO-03, P2CRO-14
- PARTIAL(6): K1-05, K4-03, K4-05, K6-06, P2SAF-04, P2SAF-06
- REFUTED(4): K8-05, K8-07, P2INC-02, P2INC-05
- UNVERIFIABLE(1): T-1

심각도 교정: K6-02 high 유지 / P2CRO-01 high→medium / P2CRO-13 medium→low /
K4-03 medium→info / K4-05 low→info / K6-06 low→info / P2SAF-04 medium→info /
P2SAF-06 low→info / K8-05·K8-07·P2INC-02·P2INC-05 → info(결함 아님)

---

## K1-05 — PARTIAL (low)

- **라이브러리 확인:** `src/korail_mobile_api/session.py:63-69` `infer_login_input_flag` —
  `"@"` 포함 시 EMAIL, `digits == login_id and digits.startswith("01") and
  len(digits) in {10, 11}` 이면 PHONE, 그 외 MEMBER_NO. 인용 정확.
- **앱 확인:** `analysis/jadx/sources/k5/b.java:119-122` `D0()` =
  `selectedTabPosition != 0 ? != 1 ? != 2 ? "" : "2" : CHANGE_PASSWORD : ACCOUNT_REGISTER`.
  `com/korail/talk/network/dao/pay/StbkAcntDao.java:11,14` → ACCOUNT_REGISTER="4",
  CHANGE_PASSWORD="5". 탭 0/1/2 → "4"(휴대폰)/"5"(이메일)/"2"(회원번호). 앱은 추론하지 않음.
  `k5/c.java:19-21` `J0()` = `LengthFilter(10)` + `setInputType(2)`. 인용 정확.
- **판정 근거:** 메커니즘(값 공간 겹침 가능성)은 확정. 그러나 결함 성립의 핵심 전제
  ―「01로 시작하는 10자리 회원번호가 실제로 채번되는가」― 는 서버 정책이며 APK에 없다.
  주장 본문도 확인불가라 명시. 완화: `client.py:284-297` `login(..., input_flag: str|None
  = None)` 로 호출자가 명시하면 추론이 아예 호출되지 않는다.
→ 코드 사실 확인, 결함성 미확정. **PARTIAL / low**

## T-1 — UNVERIFIABLE (low)

제목·앱근거·라이브러리근거·주장이 모두 문자열 `"test"`. 열어볼 파일도 줄도 없다.
통제용 카나리로 판단하며, 없는 결함을 지어내지 않는다. **UNVERIFIABLE**

## K3-07 — CONFIRMED (low)

- `mutation_payloads.py:1211-1270` `build_unpaid_reservation_cancel_form`:
  `legs = int(journey_count)` 후 거부조건은 `legs < 1` 뿐. `:1223-1230` 주석이
  “The count is ECHOED, not fixed at one … 환승 hold carries two journeys, and refusing it
  here would leave a live transfer reservation with no way to release it — the orphaned
  hold this whole subsystem exists to prevent.” 라고 2구간 허용을 **명시적 설계**로 못박음.
- `client.py:1853-1876` `cancel_unpaid_hold` 본문에 leg 검사 없음.
- 반대로 서술하는 곳:
  - `client.py:1842` `"""Cancel a fresh, unpaid **single-journey** reservation hold.`
  - `client.py:1846` “``build_unpaid_reservation_cancel_form`` requires ``hold`` to be one
    successful (``SUCC``) **single-journey** hold with a PNR” ← 빌더가 실제로 요구하지
    않는 제약을 요구한다고 단언. 내부 모순.
  - `client.py:1732` (`reserve_transfer`) “:meth:`cancel_unpaid_hold` currently accepts
    single-journey holds only, so a live transfer hold cannot be released through this client.”
- 인용 `client.py:1836`은 어긋남(메서드 def 부근). 1842/1846/1732 은 정확.
→ 구현이 문서보다 관대하고 docstring 2곳이 정반대. 사용자가 환승 홀드를 취소 불가로
  오판할 여지. 동작 영향 없음. **CONFIRMED / low**

## K4-03 — PARTIAL (info)

- **앱 확인(실재):** `dao/ticket/TCCancelDao.java:10-46` — `LUMP_STL_TGT_NO="lumpStlTgtNo_"`(:13),
  `setLumpStlTgtNo(int,String)`(:32-34), `executeDao → ticketService.ticketChangeCancel(...)`(:36-41).
  `dao/ticket/TicketService.java:98-100` `@POST("/classes/com.korail.mobile.ticket.tripChgHndgCnc.do")`.
  호출부 `a6/x.java:108-116` `K0()`, `DReservationConfirmActivity.java:282-290`
  `executeTicketChangeCancel`.
- **라이브러리 확인:** `src/`·`tests/` 전체에서 `tripChgHndgCnc`/`TCCancel` **0건**. 미구현 맞음.
- **그러나 “계획됐지만 구현도 제외 문서화도 안 된 유일한 항목”은 거짓:**
  - `docs/RELEASE_GAP_PLAN.md:867` P4 미체크 항목이 `reservationChange`/`tripChgPrsC`/
    `tripChgHndgCnc` 를 묶어 남겨두었다. 승차권 변경 체인(`tripChgOgtk→tripChgDate→
    tripChgPrsC→tripChgHndgCnc`) **전체가 미구현**이고 이 라우트는 그 일부다.
  - 같은 Flow B 표(`:322-326`)의 `reservationCancel.ReservationCancel`(1단계)도 `src/` 0건이며
    `:640-651`에서 **의도적 생략**임을 명시. `product.ReservationCancel`(GET,
    `txtVrRsNo`/`txtGdSqno`)도 `txtGdSqno` grep 0건으로 미구현.
    → Flow B 4라우트 중 3개가 없다. “이 라우트만 빠졌다”가 성립하지 않는다.
  - 문서화 부재도 거짓: `docs/api-status-by-service.md:544`(“미실행 / 운영 상태 변경 가능”),
    `docs/api-endpoints.md:364`, `docs/deep-dive/full-api-analysis-2026-07-20.md:676`.
  - `README.md:350-351` “Check-in, membership mutation, point/mileage mutation, and
    **destructive ticket operations.** Not implemented in this version.” 가 포괄한다고 읽힌다.
→ 미구현은 사실, 프레이밍과 medium 심각도는 성립하지 않음. **PARTIAL / info**

## K4-05 — PARTIAL (info)

- **앱 확인(실재):** `dao/ticket/GuardianReliefSmsDao.java:9-56` (pnrNo/jrnySqno/rcvPsHndyTeln),
  `dao/ticket/TicketService.java:62-64` `@POST("/classes/com.korail.mobile.tk.gurdSmsSnd.do")`.
- **라이브러리 확인:** `src/`·`tests/` **0건**. 미구현 맞음.
- **“어디에도 이름으로 없다”는 거짓:**
  - `docs/api-status-by-service.md:535` 가 이름·경로·설명(“보호자 안심 SMS 발송”)과 함께
    상태 “미실행 / **운영 상태 변경 가능**” 으로 등재.
  - `docs/deep-dive/cross-validation-2026-07-21.md:311` 이 `tk.gurdSmsSnd.do` 를 srtgo에 없는
    **mutation/hidden endpoint** 목록에 이름으로 나열.
  - `docs/RELEASE_GAP_PLAN.md:452` “Full remaining write catalog ≈30 more”.
- **성격:** 제3자 휴대폰번호로 여정정보 SMS를 실제 발송하는 **부수효과 있는 write**다.
  “상태를 파괴하는 조작이 아니라 순수 누락”이라는 근거는 약하다.
→ 라우트 부재는 사실, “문서화되지 않은 순수 누락”은 거짓. **PARTIAL / info**

## K5-01 — CONFIRMED (medium 유지)

- **앱 확인:** `dao/receipt/ReceiptDao.java:11-40` `class CashReceiptInfo`
  {`h_apv_mtd_nm`, `h_athn_dmn_rcgn_no`, `h_cash_rcet_apv_no`, `h_cash_rcet_txn_dv_cd`,
  `h_tot_apv_amt:int`} + `:43-44` `ReceiptInfo.cash_rcet_info: List<CashReceiptInfo>` +
  `:74-76` `getCash_rcet_info()`. 인용 정확.
- **라이브러리 확인:** `read_models.py:184-213` `TicketReceipt` — 현금영수증 대응 필드 0개
  (`payments: tuple[ReceiptPayment, ...]` 만 존재).
  `read_parsers.py:1013-1140` `parse_ticket_receipt_response` — `_optional_list(item,
  "stl_info", ...)`(:1027) 만 순회. `src/` 전체 `cash_rcet` grep **0건**.
- 완화: `read_parsers.py:1136` `raw=item` 으로 원본 보존 → 데이터 유실·크래시 없음.
- 심각도: `stl_info`(8필드 dataclass)와 **같은 레벨의 중첩 리스트 구조체 전체**에
  대응 모델이 없다. 브리프의 medium 정의(“필드가 빠져 일부 응답을 못 읽는다”)에 정확히
  해당한다. `raw` 보존은 이 저장소의 거의 모든 파서에 공통이므로 등급 하향 사유가 아니다.
→ **CONFIRMED / medium**

## K6-02 — CONFIRMED (high 유지)

- **앱 확인(결정적):** `ui/ticket/ticketReturn/a.java:362-404` `J0(String r9)` 의 실제 세팅 —
  - `r5.setH_mlg_stl(r9)` ← 인자. `I0()`(:361-363) = `J0("N")`;
    `Q0(dialog, i9)`(:385-390) 에서 `i9==102` → `J0("Y")`.
    `P0`(:359-380) / `R0`(:392-411) 이 `prg_psb_flg.equals("M") &&
    use_psb_mlg_num >= getCommissionAmount(...)` 일 때만 "Y" 경로를 연다. → **동적**
  - `r5.setTk_ret_tms_dv_cd(refundCommissionResponse.getTk_ret_tms_dv_cd())` → **동적(에코)**
  - `r5.setPbpAcepTgtFlg(r3.getH_pbp_acep_tgt_flg())` → **동적** (주장에 없는 세 번째 필드)
- **상수 smali 재확인:** `analysis/apktool/smali/I4/a.smali:7`
  `.field public static final AFTER_DEPARTURE:Ljava/lang/String; = "15"`,
  `:9` `BEFORE_DEPARTURE ... = "21"` — jadx `I4/a.java:5-6` 과 일치.
  단 앱은 이 상수로 값을 **선택**하는 게 아니라 수수료 응답값을 에코한다
  (상수의 사용처는 `a.java:280`, `:519` 의 흐름/표시 판단). 주장의 서술 메커니즘은
  약간 다르나 “동적으로 보낸다”는 결론은 옳다.
- **라이브러리 확인:** `mutation_payloads.py:1450-1460` —
  `"h_mlg_stl": "N"`, `"tk_ret_tms_dv_cd": "21"`, `"pbpAcepTgtFlg": "N"` 무조건 고정,
  override 파라미터 없음. `client.py:2011-2047` `refund(ticket: PaidTicket)` 외 입력 없음.
- **값을 이미 읽어옴이 증명됨:** `read_parsers.py:2627-2636` `_REFUND_COMMISSION_FIELDS` 에
  `prg_psb_flg`/`tk_ret_tms_dv_cd`/`use_psb_mlg_num` 전부 매핑.
- **영향:** 출발후 환불, 마일리지 정산 대상 환불, PBP 대상 티켓에서 서버로 틀린 값이 간다.
  `refund()` 는 실서버 성공 봉투가 없는 유일 금전경로(`docs/verification-record.md:53`,
  `docs/MUTATION_HANDOFF.md:22`)라 회귀 안전망도 없다.
→ **CONFIRMED / high (유지)**. 주장보다 오히려 넓다 — 버려지는 값은 3필드다.

## K6-06 — PARTIAL (info)

- **앱 확인:** `dao/refund/RefundDao.java:118-138` `RefundResponse.stlList`,
  `:129-137` `class StlList { private String stl_mns_cd; }`.
  `ticketReturn/a.java:525-527` 가 `((RefundResponse) getResponse()).getStlList()` 를 순회.
- **라이브러리 확인:** `http.py:222-316` `post_mutation_form` — 마지막 줄 `:316`
  `return parse_base_response(payload, raise_on_fail=raise_on_fail)`.
  전용 stlList 파서 없음. 여기까지는 사실.
- **그러나 “호출자가 알 방법이 없다”는 거짓:** `parse_base_response`(`http.py:33`) 가 만드는
  `BaseKorailResponse` 는 `raw` 를 보존하므로 `response.raw["stlList"]` 로 접근 가능하다.
  또 주장이 인용한 `http.py:222-230` 은 반환부가 아니라 시그니처/docstring 이다.
→ 구조화 미제공은 사실, 접근 불가는 거짓. **PARTIAL / info**

## K8-05 — REFUTED (info)

- **앱 확인:** `dao/seatMovie/SeatMovieService.java:20-22`
  `@POST("/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial")` → `getRsvProductInquiry`.
  `constants.py:425-426` DYNAPATH_ALLOWLIST_PATHS 에 ScheduleView / ScheduleViewSpecial 둘 다 존재
  (DynaPath 6경로 주장 확인).
- **라이브러리 확인:** `read_payloads.py:1309-1519` (`_ProductTrainInquiryContinuation`,
  `_ProductTrainInquiryRequest`, 검증·연속조회 완비), `read_parsers.py:2436-2515`,
  `read_models.py:1097-1102` 존재. `ScheduleViewSpecial` 은 `safety.py`/`client.py`/`__init__.py`
  에 grep **0건** → 미배선 확인.
- **의도성 확인(결정적):** `tests/test_next_variant_reads.py:104-110`
  `test_route_and_holdback_boundary_is_exact` 가
  `assert not hasattr(KorailClient, "get_product_train_inquiry")` 와
  `assert not hasattr(korail_mobile_api, "ProductTrainInquiryRequest")` 로 미배선을 **명시적으로 고정**.
→ 인용 사실은 전부 정확하나, 테스트로 고정된 **의도된 보류**이므로 결함이 아니다.
  브리프의 “의도된 설계를 결함이라 한 주장은 REFUTED” 규칙 적용. **REFUTED / info**

## K8-07 — REFUTED (info)

- 파일 실재 확인: `network/response/research/{Cmpn,Jrny,OrgTk,Seat,Stl}.java`,
  `network/response/delay/RefundResponse.java`,
  `network/data/reservation/{RDscp,RJrny,ROrtg,RPsg,RSeat,RSrcar}.java` + `old/`.
- `src/` 에 `getTicketOriginalInquiry`/`OgTkInquiry` grep **0건** — 주장대로다.
- 그러나 이 항목은 **결함을 주장하지 않는다.** “담당 슬라이스 밖이라 필드 전수대조를
  생략했다”는 자기 신고이며, 생략 자체는 코드나 문서의 결함이 아니다.
→ 결함 아님. **REFUTED / info**

## P2MIS-04 — CONFIRMED (low)

- **앱 확인:**
  - `ui/inquiry/rir/orr/DirectInquiryActivity.java:227-238` `d3()` → `AutoRsvCancelDao`
    (`AutoRsvCancelDao.java:8` `extends RsvCancelDao`; `RsvCancelDao.java:63-68` →
    `reservationCancelService.reservationCancel(...)`;
    `ReservationCancelService.java:15-16` `@POST(".../reservationCancel.ReservationCancel")`).
  - `:240-250` `e3()` → `AutoRsvCancelCheckDao`(`:8` `extends RsvCancelCheckDao`;
    `RsvCancelCheckDao.java:55-57` → `reservationCancelCheck(...)`;
    `ReservationCancelService.java:19-20` `.../ReservationCancelChk`).
  - `:568-570` `onReceive`: `if (G4.f.dao_auto_rsv_cancel == id) { e3(...); return; }`
    — **다이얼로그 없이 즉시 2단계.** 1차가 못 본 변형이 실재함을 확인.
- **라이브러리 확인:** `client.py:1798-1800` “the app cancels the standing hold before
  re-booking (``DirectInquiryActivity.java:227-250`` -- ReservationCancel then
  ReservationCancelChk). **That is :meth:`cancel_unpaid_hold`**” ↔ `client.py:1859` 는
  `ReservationCancelChk` 하나만 POST. `safety.py:228`/`:284` allowlist 에도 Chk 만
  (`src/` 전체에 `reservationCancel.ReservationCancel` 리터럴 부재).
  `constants.py:247-248` 동일 서술.
→ docstring 이 앱의 2단계를 이 메서드에 귀속시켜 오해를 유발하는 것은 사실.
  동작 영향 없음(전송 시퀀스 자체는 P2INC-02 참조). **CONFIRMED / low**

## P2INC-02 — REFUTED (info)

- **사실관계는 맞다.** 앱의 취소 진입점 전부가 1단계 → 2단계 순서를 밟는다:
  - `DReservationConfirmActivity.java:269-279` `executeRsvCancel`(RsvCancelDao) →
    `:408-422` `onReceive(dao_rsv_cancel)` → 연계예약이면 즉시, 아니면 확인 다이얼로그 후
    `D0()`(`:118-127`, RsvCancelCheckDao).
  - `ReservedTicketActivity.java:281-291`/`:292-301`, `BasketTicketActivity.java:349-358`/`:360-369`,
    `LimousineSelectSeatActivity.java:320-330`/`:331-340`, `a6/x.java:97-106`/`:190-197`,
    `DirectInquiryActivity.java:227-250`,`:568-570`.
  - 라이브러리는 `client.py:1859` Chk 하나뿐. `src/` 전체에 1단계 리터럴 없음.
- **그러나 결함이 아니다:**
  - **의도적·문서화된 결정:** `docs/RELEASE_GAP_PLAN.md:640-651`
    “**CORRECTION** … the working client cancels with a **single `ReservationCancelChk` call**
    — step 1 `ReservationCancel` is skipped … Treat single-call as the primary path”;
    `:844-846` “cancel (**single `ReservationCancelChk` primary**, keep 2-step as fallback
    pending live check)”.
  - **실서버 검증됨:** `docs/verification-record.md:955-960` — 병합예약 입석 홀드를 단독 Chk 로
    취소, `IRG000000`, 계정 `P100` 복귀, 결제 없음.
    `docs/MUTATION_HANDOFF.md:21` “cancel (unpaid hold) ✅ implemented, **live-verified**”.
  - 주장은 `RELEASE_GAP_PLAN.md:640-646` 의 “Chk 가 COMMIT” 근거가 srtgo 계보라고 깎아내리지만,
    라이브에서 단독 Chk 가 실제로 성공한 봉투가 있으므로 계보 근거의 강도와 무관하게
    프로토콜이 통한다는 것은 이미 입증됐다.
→ 앱과 다른(더 짧은) 시퀀스이나 **검증된 의도적 단순화**. **REFUTED / info**

## P2INC-05 — REFUTED (info)

- **앱 확인(결정적):** `ui/ticket/ticketReturn/a.java:376-395` (jadx가 raw smali 로 덤프한
  `J0` 본문) —
  ```
  if (isNotNull(f30572r) && isNotNull(f30572r.getLocation())) {
      r2 = String.valueOf(location.getLatitude());
      r1 = String.valueOf(location.getLongitude());
  } else {                       // L40
      r2 = "";  r1 = r2;
  }
  ...
  r5.setLatitude(r2);  r5.setLongitude(r1);
  ```
  → **빈 문자열 폴백은 앱 자신의 분기다.** 위치 제공자가 없을 때 앱이 실제로 `""` 를 보낸다.
  따라서 라이브러리의 `latitude=""`/`longitude=""` 는 “앱이 보내는 두 shape 중 어느 쪽도
  아닌 값”이 아니라, 앱의 **GPS 미획득 shape 그 자체**다. 주장의 핵심 결론이 무너진다.
- **두 번째 호출부에 대한 사실은 맞다:** `ui/ticket/confirm/TicketListActivity.java:960-971`
  `r1(String)` 은 txtPnrNo/h_orgtk_sale_dt/h_orgtk_wct_no/h_orgtk_sale_sqno/h_orgtk_ret_pwd/
  h_mlg_stl/pbpAcepTgtFlg 만 세팅 → Retrofit 이 tk_ret_tms_dv_cd/trnNo/latitude/longitude 를
  드롭한다. 라이브러리는 `mutation_payloads.py:1456-1459` 로 항상 채운다.
  그러나 앱이 두 shape 를 모두 보내는 이상, 그중 하나(ticketReturn 14필드 경로)를
  필드집합 단위로 재현하는 것은 결함이 아니다.
- 실질 문제(고정값 전송)는 K6-02 에서 이미 CONFIRMED 로 다뤘다.
→ **REFUTED / info**

## P2SAF-01 — CONFIRMED (medium)

- **앱 확인:** `dao/research/NCardReservationDao.java:16` `APD_CUST_NAME = "apdCustName_"`,
  `:29` `CUST_MG_NO = "custMgNo_"`, `:30` `APD_CUST_TEL = "apdCustTeln_"`,
  `:66-72` `setApdCustName/setApdCustTel` → `apdUsrInfo.put(prefix + i9, str)`,
  `:122-124` `setCustMgNo(int, String)` → `apdUsrInfo.put("custMgNo_" + i9, str)`.
  라우트 `dao/research/ResearchService.java` `setNCardReservation(..., @FieldMap, @FieldMap)`.
- **라이브러리 확인:** `mutation_payloads.py:1568` `form[f"custMgNo_{index}"]`,
  `:1572` `form[f"apdCustName_{index}"]`, `:1576` `form[f"apdCustTeln_{index}"]`.
  `redaction.py:340` `sensitive = name.casefold() in SENSITIVE_KEYS` — **정확일치만**.
  `:29 custMgNo`, `:32 acepCustNm`, `:33 acepCustTeln` 등 무인덱스 철자만 등재.
  **대비:** `:154-161` `txtSrcarNo{1..N}`/`txtSeatNo{1..N}`, `:194-197` `txtCardNo_{1..N}` 은
  “SENSITIVE_KEYS is matched exactly” 라는 이유를 주석에 달고 **인덱스 전개로 등재**돼 있다.
  같은 판단이 여기만 적용되지 않았다.
- **실측(in-process, 저장소 무수정):**
  ```
  redact_payload({'custMgNo_1':'1234567890','apdCustTeln_1':'01012345678',
                  'apdCustName_1':'홍길동','custMgNo':'1234567890'})
  → {'custMgNo_1':'1234567890', 'apdCustTeln_1':'01012345678',
     'apdCustName_1':'홍길동', 'custMgNo':'[REDACTED]'}
  ```
  인덱스 붙은 3개 전부 평문 통과. 11자리 전화번호는 CARD_RE(13~19자리)에도 안 걸린다.
- **깨지는 문서:** `README.md:209-211` “forced through ``redact_payload`` on construction,
  so it can never hold a raw card number, PNR **or other identity** even if you built it from
  real values.” `consent.py:127-131` `MutationPreview.__post_init__`.
- 심각도: 카드 PAN 이 아니고 호출자가 이미 보유한 동반자 PII 라 critical 은 아니나,
  실명+휴대폰+고객관리번호가 dry_run 기본 프리뷰(로그/UI 노출 대상)에 한 묶음으로 남아
  그 자체로 재식별 가능하다. **CONFIRMED / medium**

## P2SAF-04 — PARTIAL (info)

- **사실 확인은 전부 통과:** `safety.py:295` “The consent categories whose forms carry a card
  number in the clear”, `:317` `KORAIL_CARD_BEARING_MUTATION_CATEGORIES = frozenset({"payment"})`;
  `mutation_payloads.py:1704` `rebuilt["txtCardNo_1"] = ...card_no`;
  `client.py:2207` `require_mutation_consent(consent, "reserve")`,
  `:2220`/`:2229-2231` `category="reserve"` (프리뷰·전송 모두);
  `w4/a.java:93` `getNCardReservationRequest`, `:100` `setDiscKndCd(1, "153")`,
  `:101` `setCardNo(1, ticketDetailResponse.getDcnt_crd_info().getH_dcnt_crd_no())`;
  `dao/certification/CertificationService.java:52-54` `certification.TicketReservation`;
  `tests/test_real_card_payment.py:198-219` 가 (payment 포함 / MUTATION_CATEGORIES 부분집합 /
  GET 카테고리와 교집합 공집합) 세 방향만 검사 — 역방향 완전성 검사 부재도 사실.
- **그러나 안전게이트의 구멍이 아니다:**
  - `txtCardNo_1` 이 나르는 값은 결제 PAN 이 아니라 **할인카드(N카드) 번호**(`h_dcnt_crd_no`)다.
    이 세트가 먹이는 게이트(`http.py:276-291`)는 `fake_card_only` XOR `real_card_acknowledged`,
    즉 “비과금 테스트카드냐 진짜 돈이 나가는 카드냐”를 강제하는 장치이며 에러 문구도
    “**the PAN** is transmitted in the clear” 라고 결제 PAN 을 지목한다. 선불 잔여횟수를
    소진하는 N카드에는 이 이분법 자체가 성립하지 않는다.
  - 프리뷰 마스킹 구멍 없음: `redaction.py:194-197` 이 `txtCardNo_{1..N}` 전개 등재.
  - 주장자 본인이 세 가지 완화조건을 나열하고 medium 으로 낮춰 잡았다.
→ 관찰(정의가 reserve 도 포괄, 완전성 테스트 부재)은 정확하나 게이트가 뚫린 것은 아니고
  주석 문구의 포괄범위 문제다. **PARTIAL / info**

## P2SAF-06 — PARTIAL (info)

- **확인:** `client.py:1898-1903` `pay_with_fake_card` —
  `require_mutation_consent(consent, "payment")` 후 `if not consent.fake_card_only: raise`
  하나뿐. `client.py:1971-1984` `pay_with_card` — `real_card_acknowledged` 와
  `fake_card_only` 양쪽 검사. `http.py:276-284` 전송게이트가 둘 다 True 를 모순으로 거부.
  → `MutationConsent(allow_payment=True, fake_card_only=True, real_card_acknowledged=True,
  dry_run=True)` 는 pay_with_fake_card 의 자체검사를 통과하고 dry_run 이라 전송게이트에
  도달하지 않은 채 정상 프리뷰를 반환한다. 비대칭은 실재한다.
- **그러나 의도된 계층화다:** `http.py:269-273` 주석이 명시 — “Keyed on MEMBERSHIP of the
  card-bearing set rather than on the single literal ‘payment’ … **This keeps the invariant at
  the layer that actually sends, not only in the public payment methods.**”
  그리고 fail-safe: `dry_run=False` 로 바꾸는 순간 반드시 `MutationNotAllowedError`.
  돈이 움직이는 경로가 열리지 않는다.
→ 형제 메서드 간 검사 강도 차이는 사실이나 게이트 우회가 아니고 문서화된 설계.
  **PARTIAL / info**

## P2SAF-09 — CONFIRMED (low)

- **앱 확인:** `dao/certification/CertificationService.java:35-37` —
  `@POST("/classes/com.korail.mobile.certification.PriceReCalculation")` `getDiscountPrice(...)`
  의 마지막 6개 인자가 `@Field(...) List<String>` (psg_tp_dv_cd, hidDcntKndCd, dcnt_knd_cd1,
  hidDscpNo, psrm_cl_cd, hidFmlyNo). Retrofit 이 같은 키를 반복 방출하므로 리스트 값은 정당.
- **라이브러리 확인:** `consent.py:127` `payload: Mapping[str, str]`;
  `redaction.py:320-322` `def redact_payload(...) -> dict[str, str | list[str]]`;
  `mutation_payloads.py:1858` `form: dict[str, str | list[str]]`.
- **실측:** `MutationPreview(..., payload={'hidDscpNo':['A','B']}).payload['hidDscpNo']`
  → `<class 'list'>` (값 `['[REDACTED]','[REDACTED]']`).
→ 타입 주석 불일치 확정. 타입체커 사용자에게만 영향, 동작 무관. **CONFIRMED / low**

## P2CRO-01 — CONFIRMED (high → medium 하향)

- **앱 확인, 독립 2곳:**
  - `ui/ticket/ticketReturn/a.java:412-413` `r5.setH_orgtk_sale_dt(r3.getH_sale_dt())`
  - `ui/ticket/confirm/TicketListActivity.java:965`
    `refundRequest.setH_orgtk_sale_dt(ticketDetailResponse.getH_sale_dt())`
- **대비(같은 화면의 읽기들):**
  - `TicketListActivity.java:904` `refundCommissionRequest.setH_orgtk_ret_sale_dt(h_orgtk_ret_sale_dt)`
  - `ticketReturn/a.java:352` `setH_orgtk_ret_sale_dt(ticketDetailResponse.getH_orgtk_ret_sale_dt())`
  - `ui/ticket/receipt/TicketReceiptActivity.java:402`
    `receiptRequest.setH_orgtk_sale_dt(this.f30462k.getH_orgtk_ret_sale_dt())`
    ← **영수증 라우트만이 “같은 값을 다르게 표기”한다.**
  트리 전체 grep(`setH_orgtk_sale_dt|setH_orgtk_ret_sale_dt`)으로 위가 전부임을 확인.
- **라이브러리 확인:** `read_parsers.py:2681` `"sale_date": "h_sale_dt"`,
  `:2684` `"original_sale_date": "h_orgtk_ret_sale_dt"`;
  `mutation_models.py:337` `sale_date: str = field(repr=False)  # h_orgtk_sale_dt`,
  `:319-321` docstring “the PNR plus **the original-ticket sale window/date/sequence** and
  return password” ← 4개 중 sale_date 만 원표값이 아닌데 한 묶음으로 서술.
  `mutation_payloads.py:1450` `"h_orgtk_sale_dt": ticket.sale_date`.
- **주장 중 한 갈래는 무너진다:** `read_payloads.py:1619-1621` docstring 은
  “NOT the ``h_orgtk_sale_dt`` **the receipt read** uses” 라고 스스로 영수증 읽기로 한정한다.
  환불 폼에 대해 아무 말도 하지 않으므로 “환불에는 거짓”이라는 지적은 과녁을 벗어난다.
  또 `TicketReceiptActivity.java:402` 로 그 서술은 실제로 참임을 확인했다.
- **완화:** 필드명 `sale_date` 는 `RefundTicketDetail.sale_date`(=h_sale_dt)와 일치해 올바르고,
  주석 `# h_orgtk_sale_dt` 는 **와이어 필드명**으로서는 정확하다
  (`dao/refund/RefundService.java:28` `@Field("h_orgtk_sale_dt")`).
  `PaidTicket` 을 자동 조립하는 헬퍼가 없어(생성처는 tests 2곳뿐) 코드가 스스로 잘못 채우지 않는다.
→ docstring 산문이 함정을 만드는 것은 사실이고 변경/재발권 이력 티켓에서 조용히 어긋날 수
  있으나, 잘못된 값은 호출자가 직접 넣어야 발생한다. **CONFIRMED / corrected: medium**

## P2CRO-13 — CONFIRMED (medium → low 하향)

- **앱 확인:** `dao/payment/PaymentService.java:12-14` `@Field("hidRsvChgNo")`;
  `V4/b.java:41` `setHidRsvChgNo(reservationResponse.getJrny_infos().getJrny_info().get(0)
  .getH_rsv_chg_no())` — 예약별로 달라지는 상태값.
- **라이브러리 확인:** `mutation_payloads.py:1398`
  `"hidRsvChgNo": _echoed_reservation_change_no(hold)` 로 전송.
  `redaction.py` — `:24 hidPnrNo`, `:141 hidWctNo`, `:142-143 hidTmpJobSqno1/2` 는 등재,
  읽기 철자 `:112 h_rsv_chg_no` 도 등재. **`hidRsvChgNo` 만 grep 0건.**
- **실측:** `redact_payload({'hidRsvChgNo':'017','hidPnrNo':'1234'})`
  → `{'hidRsvChgNo':'017', 'hidPnrNo':'[REDACTED]'}`. 형제 필드와 비대칭 확정.
  CARD_RE 는 PAN 패턴만 잡으므로 백스톱이 되지 않는 것도 맞다.
- **심각도 하향 근거:** 이 값은 3자리 예약변경 차수 카운터(통상 "000")로 엔트로피가 사실상
  없고 단독으로 재식별·도용에 쓸 수 없다. 같은 값의 읽기 철자는 이미 마스킹되므로
  **마스킹 정책의 일관성 결함**이지 자격증명 유출이 아니다.
→ **CONFIRMED / corrected: low**

## P2CRO-03 — CONFIRMED (low)

- **앱 확인:** `network/response/seatMovie/RsvInquiryResponse.java:12`
  `private String h_notice_msg;` (최상위 9필드 중 하나 — h_ectb_trn_no_next, h_gd_no,
  h_next_pg_flg, h_notice_msg, h_prcd_trn_no_next, h_qry_st_no_next, h_rslt_cnt,
  h_trn_no_next, trn_infos).
  `dao/seatMovie/SeatMovieService.java:12-14`(ScheduleView), `:16-18`(LimousineScheduleView),
  `:20-22`(ScheduleViewSpecial) — **셋 다 같은 DTO 를 반환한다.**
- **라이브러리 확인:** `parsers.py:257-276` `parse_train_search_metadata` 에 `h_notice_msg`
  부재(`parsers.py` 전체 grep 0건). 대비: `read_parsers.py:2503-2506`(특가상품 조회),
  `limousine_parsers.py:388-390`(리무진) 은 동일 키를 읽는다.
  → 같은 DTO 를 쓰는 세 라우트 중 둘만 읽으므로 설계 스타일이 아니라 누락이다.
- 완화: `parsers.py:275` `raw=dict(raw)` 로 보존, 크래시 없음. 단일 스칼라 필드.
→ **CONFIRMED / low**

## P2CRO-14 — CONFIRMED (low)

- **smali 재확인(상수는 smali 가 authoritative):**
  `analysis/apktool/smali/K4/h.smali:40-64` —
  ```
  new-instance v0, LK4/h;
  const-string v1, "일시불"     # 일시불
  const-string v2, "0"
  const-string v3, "INS_0"
  const/4 v4, 0x0
  invoke-direct {v0, v3, v4, v1, v2}, LK4/h;-><init>(...)
  sput-object v0, LK4/h;->INS_0:LK4/h;
  ```
  **일시불 코드는 한 자리 `"0"`.** jadx `K4/h.java:7` `INS_0("일시불", "0")` 와 일치.
- **앱 전송부:** `V4/a.java:32`
  `paymentMethod.setHidIsmtMnthNum(1, creditCardData.getInstallmentType())`.
- **라이브러리 확인:** `mutation_models.py:311`
  `installment: str = "00"  # months; "00" = lump sum`;
  `mutation_payloads.py:1407` `"hidIsmtMnthNum1": card.installment`.
- 나머지 코드(2/3/4/5/6/12/24)는 자릿수 문제 없음 — 명시 지정 시 정확 전송.
→ 기본값만 앱과 1바이트 불일치. 서버가 정수 파싱하면 기능 영향 없음.
  “앱과 바이트 단위 일치” 설계원칙 위반. **CONFIRMED / low**

---

## 검증 중 발견한 부수 사실 (판정 대상 아님, 기록용)

1. `mutation_payloads.py:1458` `"pbpAcepTgtFlg": "N"` 고정 ↔ 앱은 **두 호출부 모두**
   `h_pbp_acep_tgt_flg` 를 동적으로 전송한다(`ticketReturn/a.java:404`,
   `TicketListActivity.java:971`). K6-02 와 동종이나 어느 주장도 제기하지 않은 세 번째 필드.
2. `mutation_payloads.py:1451` `"h_orgtk_sale_wct_no"` 는 **정확하다.** DAO 필드명은
   `h_orgtk_wct_no`(`RefundDao.java:18`)지만 실제 와이어 `@Field` 이름은
   `RefundService.java:28` 에서 `h_orgtk_sale_wct_no` 다. 오탐 소지가 있어 기록한다.
3. `analysis/apktool/smali/` 는 macOS 대소문자 무시 파일시스템 때문에 `I4/` 와 `i4/` 가
   충돌할 수 있다. `I4/a.smali` 는 정상 확인됐으나, 유사 패키지명 상수 확인 시
   `grep -rn` 으로 트리 전체를 훑어 실제 매치 파일을 확인하는 편이 안전하다.
