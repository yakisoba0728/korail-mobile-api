# K5 — 결제·영수증 감사 보고서

담당 영역: `network/dao/pay/*` (13), `network/dao/payment/*`, `network/dao/cashReceipt/*`,
`network/dao/receipt/*`, `network/dao/railplus/*` — 앱 v6.5.0 디컴파일 vs
`src/korail_mobile_api/` 라이브러리.

읽기 전용 감사. 저장소 파일은 수정하지 않았다.

---

## 0. 요약

- 담당 영역의 Retrofit 엔드포인트 **16개**를 전수 추출했다
  (`PayService` 12, `PaymentService` 1, `CashReceipt` 1, `ReceiptService` 1,
  `RailPlusService` 1).
- 라이브러리가 실제로 구현한 것은 **결제 실행(`payment.ReservationPayment`,
  단일 카드 결제만)** 과 **영수증 조회(`receipt.ReceiptInfo`)** 2개뿐이다.
  나머지 14개(간편결제/포인트/계좌이체/통합결제/현금영수증 발급/RailPlus
  자동충전)는 전혀 구현되어 있지 않다 — 다만 이는 `docs/RELEASE_GAP_PLAN.md`에
  "PG WebView 리디렉션이 필요해 헤드리스 라이브러리 범위 밖"이라고 명시적으로
  문서화된 결정이며, `docs/api-status-by-service.md`도 동일하게 12/1/1개 모두
  "미실행"으로 정확히 반영하고 있다. 조용히 빠진 것이 아니라 문서화된 축소
  범위이므로 defect로 보고하지 않고 info 로만 남긴다.
- 구현된 두 영역에서 실제 결함 3건을 확인했다:
  1. **영수증 응답의 `cash_rcet_info`(현금영수증 정보 리스트) 파싱 누락** — medium.
  2. **카드결제 미리보기(`MutationPreview`)에서 `hidRsvChgNo` 가 마스킹
     목록에서 빠져 평문으로 노출됨** — 결제 경로의 레드액션 정밀 점검에서
     발견, medium.
  3. **`CardPayment.installment` 기본값 `"00"` 이 앱이 실제로 보내는 일시불
     코드 `"0"`(smali `K4/h.smali` 확인)과 다름** — low, 기능 영향은 거의 없음.
- 단일 카드결제 자체(`hidStlCrCrdNo1` 등 카드 필드 7종, PNR/윈도/잡시퀀스 에코,
  `hiduserYn`, settlement 상수 `02`/`@`/`1`)는 필드명·상수값 모두 smali/jadx와
  1:1로 정확히 일치했고, 카드 PAN·CVC·유효기간·생년월일 마스킹도 정확하다.
  안전 게이트(consent 이중 게이트, fake/real 카드 배타 검증, 카드소지 카테고리
  allowlist)에서 우회 경로는 발견하지 못했다.

---

## 1. 앱 기능 전체 목록

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 예약결제 실행(카드/포인트/간편결제/후불 통합 FieldMap) | `POST /classes/com.korail.mobile.payment.ReservationPayment` | `PaymentService.java:12-14`, `RsvPaymentDao.java:127-137` | `client.pay_with_card`/`pay_with_fake_card` (`client.py:1877-2009`), `build_card_payment_form` (`mutation_payloads.py:1317-1413`) | **부분구현** (카드 단독 결제만; 포인트/간편결제/복합·후불 결제 미구현) — 상세 §2.1 |
| 2 | Payco 결제 준비 | `POST …payment.reserve.payco.do` | `PayService.java:22-24`, `PaycoDao.java` | 없음 | **없음** (PG WebView, 문서화된 제외) |
| 3 | 간편결제 데이터 검증(Shinhan 등) | `POST …pay.spayCphdDatVal.do` | `PayService.java:26-28`, `SpayCphdDatValDao.java` | 없음 | **없음** (문서화된 제외) |
| 4 | Monimo 결제 데이터 복호화 | `POST …pay.monimoDecrypt.do` | `PayService.java:30-32`, `SpayCphdDatValMonimoDao.java` | 없음 | **없음** (문서화된 제외) |
| 5 | 간편결제 주문번호 발급 | `POST …pay.spayOrdNo.do` | `PayService.java:34-36`, `SpayOdrNoDao.java` | 없음 | **없음** (문서화된 제외) |
| 6 | 통합결제(장바구니/복수상품) | `POST …pay.intgStl.do` | `PayService.java:38-40`, `IntgStlDao.java` | 없음 | **없음** (문서화된 제외, `RELEASE_GAP_PLAN.md:358`) |
| 7 | 네이버페이 머니 예약 | `POST …pay.naverPayMoneyRsv.do` | `PayService.java:42-44`, `NaverPayMoneyRsvDao.java` | 없음 | **없음** (문서화된 제외) |
| 8 | 네이버페이 예약 | `POST …pay.naverPayRsv.do` | `PayService.java:46-48`, `NaverPayRsvDao.java` | 없음 | **없음** (문서화된 제외) |
| 9 | 세틀뱅크 계좌 인증/결제 | `POST …pay.stbkAcnt.do` | `PayService.java:50-52`, `StbkAcntDao.java` | 없음 | **없음** (문서화된 제외) |
| 10 | 세틀뱅크 등록은행 조회 | `POST …pay.stbkRegBank.do` | `PayService.java:54-56`, `StbkRegBankDao.java` | 없음 | **없음** (문서화된 제외) |
| 11 | 간편결제 결제키 등록/처리 | `POST …pay.stlKeyPrs.do` | `PayService.java:58-60`, `TossAutoStlKeyPrsDao.java` | 없음 | **없음** (문서화된 제외) |
| 12 | 간편결제 결제키 조회 | `POST …pay.stlKeyQry.do` | `PayService.java:62-64`, `TossAutoStlKeyQryDao.java` | 없음 | **없음** (문서화된 제외) |
| 13 | Toss 자동결제 생성 | `POST …pay.tossautoC.do` | `PayService.java:66-68`, `TossAutoCreateDao.java` | 없음 | **없음** (문서화된 제외) |
| 14 | 현금영수증 발급 | `POST …cashReceipt.issue.do` | `CashReceipt.java:12-14`, `CashReceiptIssueDao.java` | 없음 | **없음** (문서에는 등장하나 미구현, §3 참고) |
| 15 | 승차권 영수증 조회 | `POST …receipt.ReceiptInfo` | `ReceiptService.java:10-12`, `ReceiptDao.java` | `client.get_ticket_receipt` (`client.py:805-828`) | **부분구현** — `stl_info`(결제수단별 상세)는 완전 매칭, `cash_rcet_info`(현금영수증 정보) 미파싱, 상세 §2.2 |
| 16 | RailPlus 자동충전 가능여부 조회 | `GET …railplus.autoCharge.do` | `RailPlusService.java:9-10`, `AutoChargeDao.java` | 없음 | **없음** (읽기전용 갭 목록에 문서화됨, `RELEASE_GAP_PLAN.md:145`) |

구현/부분구현 2건, 문서화된 미구현 14건. "있는 것"(문제 없이 정확히 구현된
부분) 개수는 별도 집계하지 않고 아래 §2 에서 부분구현 2건의 세부 필드
단위로 정확/부정확을 나눈다.

---

## 2. 구현된 두 엔드포인트의 필드 단위 대조

### 2.1 `payment.ReservationPayment` — 단일 카드결제

**요청 구조 (앱, `PaymentService.java:12-14` + `PaymentMethod.java` + `v4/a.java:21-55`):**

```
hidPnrNo, hidWctNo, hidTmpJobSqno1, hidTmpJobSqno2, hidRsvChgNo   ← PaymentService 직접 파라미터
+ @FieldMap PaymentMethod:
  hidInrecmnsGridcnt, hidStlMnsSqno{n}, hidStlMnsCd{n}, hidMnsStlAmt{n}, hidCrdInpWayCd{n}
  카드: hidStlCrCrdNo{n}, hidVanPwd{n}, hidCrdVlidTrm{n}, hidIsmtMnthNum{n}, hidAthnDvCd{n}, hidAthnVal{n}
  (+ 신한 전용 shStlCrCrdNo{n}/shCrdVlidTrm{n})
  포인트: hidPontDvCd{n}, hidPontInpDvCd{n}, hidPontCrdPwd{n}
  회원: hiduserYn, hidMbCrdNo
  간편결제: spayDvCd_{n}_1, spayCphdDatVal_{n}_1, stSpayGridcnt_{n}
  후불(국회의원 등): hidDscpMgNo{n}, hidDfpyDscpNo{n}, hidDfpySrtCd{n}
```

`v4/a.java`(`getCardRequest`/`getEasyRequest`/`getPointRequest`/`getCongressRequest`)가
`hidStlMnsCd` 값에 따라 이 맵을 분기 생성한다:
`"02"`=카드, `"03"`=후불(국회의원), `"12"`=포인트(KORAIL/철도/우리모아/OK캐시백),
`"13"`=RailPlus, `"14"`=간편결제류(세틀뱅크 등, `spayDvCd`로 세분화).
일반 카드결제(`getCardRequest`, `AbstractC1269e.java:403-411`)는 **포인트를
전혀 안 쓰는 경우가 아니면 카드(1행) + 포인트(2행, 필요시 3행까지)를 함께
보내는 복합결제**이고, 라이브러리가 재현하는 것은 포인트 미사용(pointType
`"-1"`) 케이스의 카드 단일행뿐이다.

**라이브러리 구현 (`mutation_payloads.py:1317-1413` `build_card_payment_form`):**

| 앱 필드 (wire key) | 값/상수 (앱, smali/jadx 확인) | 라이브러리 값 | 일치 여부 |
|---|---|---|---|
| `hidPnrNo` | hold의 PNR | `hold.pnr_no` | ✅ |
| `hidWctNo` | hold의 window_no | `hold.window_no` | ✅ |
| `hidTmpJobSqno1`/`2` | hold 에코, null이면 Retrofit이 필드 자체를 생략 | `_echoed_job_sequence`, 결측 시 `"000000"` (기존 srtgo/자체 값 유지, null 재현은 불가하다고 명시) | ✅ (문서화된 한계) |
| `hidRsvChgNo` | 첫 journey의 `h_rsv_chg_no` 에코, 없으면 앱 자체 상수 `"000"` | `_echoed_reservation_change_no`, 결측 시 `"000"` | ✅ |
| `hidInrecmnsGridcnt` | `"1"` (단일행) | `"1"` | ✅ |
| `hidStlMnsSqno1` | `"1"` | `"1"` | ✅ |
| `hidStlMnsCd1` | `"02"` (카드) | `"02"` | ✅ |
| `hidMnsStlAmt1` | `getReceivedAmount()` (표시금액이 아닌 실결제액) | `hold.received_amount` | ✅ (docstring이 `h_tot_prc`와의 차이를 정확히 근거와 함께 설명) |
| `hidCrdInpWayCd1` | `"@"` | `"@"` | ✅ |
| `hidStlCrCrdNo1` | PAN 평문 | `card.card_number` (digit-only 검증) | ✅ |
| `hidVanPwd1` | 카드 비번 앞 2자리 | `card.card_password` | ✅ |
| `hidCrdVlidTrm1` | `YY+MM` (`CreditCardData.getCrdVlidTrm()`) | `card.card_expire` (YYMM) | ✅ |
| `hidIsmtMnthNum1` | `K4.h` enum code: `"0"`,`"2"`,`"3"`,`"4"`,`"5"`,`"6"`,`"12"`,`"24"` (smali `K4/h.smali:44-260` 확인) | 기본값 `"00"` | ❌ **불일치** — §3.3 |
| `hidAthnDvCd1` | `"J"`(개인)/`"S"`(법인), `AbstractC1269e.java:881-884` | `card.card_type` 기본 `"J"` | ✅ |
| `hidAthnVal1` | 개인 생년월일(YYMMDD) 또는 법인 사업자번호 | `card.birthday` | ✅ |
| `hiduserYn` | 회원 `"Y"` / 비회원 `"N"`(+`hidMbCrdNo`), `AbstractC1269e.java:710-716` | 항상 `"Y"` | ✅ (라이브러리 전체가 회원 세션 전용이라 비회원 분기는 애초에 도달 불가 — `client.py:1553-1557` 참고) |
| `hidMbCrdNo` | 비회원 번호 (비회원일 때만) | 미전송 | ✅ (위와 동일한 이유로 무해) |

**결론:** 카드 단독 결제 경로는 필드명·상수값이 정확하다. 실제 앱 동작(카드+
포인트 복합, 간편결제, 후불) 중 이 라이브러리가 커버하는 것은 "포인트 미사용
카드 단독 결제" 부분집합뿐이며, `CardPayment`/`build_card_payment_form`
docstring이 이 범위 제한을 스스로 명시하고 있다 (의도된 축소, defect 아님).
유일한 실결함은 §3.3 의 `installment` 기본값.

### 2.2 `receipt.ReceiptInfo` — 승차권 영수증 조회

요청측 4필드(`h_orgtk_sale_dt`/`h_orgtk_wct_no`/`h_orgtk_sale_sqno`/
`h_orgtk_tk_ret_pwd`)는 `build_ticket_receipt_form`(`read_payloads.py:474-491`)과
`ReceiptService.java:10-12` 가 이름·개수 정확히 일치. `safety.py:756-764` 의
읽기전용 필드 allowlist도 동일하게 4개 정확히 등록.

응답측 `ReceiptDao.ReceiptInfo`(23개 스칼라 필드 + `stl_info`/`cash_rcet_info`
2개 리스트)를 `parse_ticket_receipt_response`(`read_parsers.py:1013-1140`)와
대조한 결과:

- 23개 스칼라 필드 전부 이름·타입(`int`/`String`) 일치 확인 (예:
  `h_ismt_mnth_num`→`installment_months:int`, `h_stl_amt`→`amount:int`,
  나머지 문자열 필드 모두 문자열로 파싱).
- `stl_info`(결제수단별 정산 내역, `h_stl_way_nm`/`h_apv_dt`/`h_ismt_mnth_num`/
  `h_stl_amt`/`h_acnt_no`/`h_apv_no`/`h_stl_crd_no`/`h_xpot_no` 8필드) →
  `ReceiptPayment` 8필드 전부 정확히 매핑.
- **`cash_rcet_info`(현금영수증 정보 리스트, `h_apv_mtd_nm`/
  `h_athn_dmn_rcgn_no`/`h_cash_rcet_apv_no`/`h_cash_rcet_txn_dv_cd`/
  `h_tot_apv_amt`, `ReceiptDao.java:12-41`) 는 `TicketReceipt` 데이터클래스에
  대응 필드가 전혀 없고 파서도 이를 순회하지 않는다** — §3.1.

---

## 3. 결함 상세

### 3.1 [K5-01] 영수증 응답의 현금영수증 정보(`cash_rcet_info`) 파싱 누락

- **분류**: missing (partial 성격 — raw 딕셔너리에는 남아있으나 타입 필드 없음)
- **심각도**: medium
- **앱 근거**: `analysis/jadx/sources/com/korail/talk/network/dao/receipt/ReceiptDao.java:12-41`
  (`CashReceiptInfo` 클래스: `h_apv_mtd_nm`, `h_athn_dmn_rcgn_no`,
  `h_cash_rcet_apv_no`, `h_cash_rcet_txn_dv_cd`, `h_tot_apv_amt:int`) 와
  `:44,74-76` (`ReceiptInfo.cash_rcet_info: List<CashReceiptInfo>`,
  `getCash_rcet_info()`).
- **라이브러리 근거**: `src/korail_mobile_api/read_models.py:184-213`
  (`TicketReceipt` 데이터클래스에 `cash_rcet_info`/`CashReceiptPayment` 류 필드
  없음), `src/korail_mobile_api/read_parsers.py:1013-1140`
  (`parse_ticket_receipt_response` 가 `stl_info`만 순회하고 `cash_rcet_info`
  키는 참조하지 않음 — `item`(=raw row)에는 값이 그대로 남아 있어 `.raw`로는
  접근 가능하나 타입 필드는 없음).
- **내용**: 현금영수증이 발급된 승차권의 영수증을 조회하면 서버는
  `cash_rcet_info` 리스트(발급 방법명, 인증번호, 승인번호, 거래구분코드,
  승인금액)를 함께 내려준다. 라이브러리는 같은 응답의 `stl_info`(카드/계좌
  등 일반 결제수단)는 `ReceiptPayment` 리스트로 정확히 파싱하면서
  `cash_rcet_info`는 대응 타입이 아예 없어 구조화된 접근이 불가능하다.
  `raw=item`에 원본 딕셔너리가 남아 있으므로 데이터 자체가 유실되진
  않지만("영수증 5건 조회 성공" 라이브 기록이 있는 `docs/api-status-by-service.md:442`
  참고), 현금영수증이 발급된 케이스만 사일런트하게 비어보이는(`raw`를 직접
  파봐야 하는) 응답이 된다.
- **수정 방향**: `CashReceiptInfo`(app) 5필드에 대응하는
  `ReceiptCashPayment` 류 dataclass를 추가하고 `stl_info`와 동일한 패턴으로
  `cash_rcet_info` 리스트를 파싱해 `TicketReceipt.cash_receipts` 로 노출.

### 3.2 [K5-02] 카드결제 미리보기에서 `hidRsvChgNo` 가 마스킹되지 않고 평문 노출

- **분류**: risk
- **심각도**: medium
- **앱 근거**: `analysis/jadx/sources/com/korail/talk/network/dao/payment/PaymentService.java:12-14`
  (`@Field("hidRsvChgNo")`), 값의 출처는 `V4/b.java:41` 등
  (`RELEASE_GAP_PLAN.md:1331-1338`가 인용)이 예약별로 달라지는 진짜
  reservation-change 시퀀스임을 보여줌 — 항상 상수가 아니다.
- **라이브러리 근거**:
  - `src/korail_mobile_api/mutation_payloads.py:1306-1398`
    (`_echoed_reservation_change_no` 가 hold의 첫 journey
    `reservation_change_no` 를 그대로 echo, 결측시에만 `"000"`),
  - `src/korail_mobile_api/redaction.py:12-230` (`SENSITIVE_KEYS`
    프로즌셋에 `hidRsvChgNo` 없음 — `hidPnrNo`(24행), `hidWctNo`(141행),
    `hidTmpJobSqno1`/`hidTmpJobSqno2`(142-143행)는 모두 등재되어 있으나
    같은 결제 폼의 형제 필드인 `hidRsvChgNo`만 누락),
  - `src/korail_mobile_api/consent.py:114-131` (`MutationPreview.__post_init__`
    이 `redact_payload`를 통해서만 마스킹하므로, allowlist에 없는 키는
    `MutationPreview.payload`에 원문 그대로 남음),
  - 테스트로도 확인됨: `tests/test_mutation_payloads.py:136,209,227,254`가
    `hidRsvChgNo`에 `"SYNTHETIC_CHG_NO"`/`"001"`/`"002"` 같은 실제 예약별
    값이 들어갈 수 있음을 보여주는 반면, `tests/test_real_card_payment.py:355-390`
    (`test_pay_with_card_dry_run_redacts_the_pan_and_sends_nothing`)의
    `_hold()` 픽스처는 `journeys=()` (기본값)라서 `hidRsvChgNo`가 항상 상수
    `"000"`이 되어 이 결함을 우연히 은폐하고 있음 — `hidRsvChgNo`는 해당
    테스트의 redacted-key 목록(366-377행)에도, `tests/test_redaction_safety.py:127-188`의
    파라미터화 목록에도 없음.
- **내용**: `pay_with_card`/`pay_with_fake_card`의 docstring은 각각
  "`dry_run=True`이면 카드와 신원(identity) 필드가 redact 된 `MutationPreview`를
  반환한다"고 명시한다(`client.py:1890-1891`, `1956-1957`). 그러나 실제
  구현에서는 `hidPnrNo`/`hidWctNo`/`hidTmpJobSqno1`/`hidTmpJobSqno2` 는
  마스킹되지만 같은 신원 튜플의 다섯 번째 필드인 `hidRsvChgNo`는 그렇지
  않다. 예약이 이미 변경 이력을 가지고 있어 hold 응답의
  `h_rsv_chg_no`가 `"000"`이 아닌 실제 값을 담고 있는 경우, 그 값이
  dry-run 미리보기(로그/UI에 노출될 수 있는 대상)에 평문으로 남는다.
  PNR 자체는 마스킹되어 있어 이 값 단독으로는 즉시 악용 가능성이 크지
  않지만, 이 라이브러리의 redaction 철학(형제 필드 전부를 예외 없이
  마스킹)과 문서가 약속한 동작에는 명백히 어긋나는 구멍이다.
- **수정 방향**: `redaction.SENSITIVE_KEYS`에 `"hidRsvChgNo"`를 추가하고,
  `test_pay_with_card_dry_run_redacts_the_pan_and_sends_nothing` 계열
  테스트가 `journeys`에 실제 값이 채워진 hold로도 이 필드를 검증하도록
  보강.

### 3.3 [K5-03] `CardPayment.installment` 기본값이 앱의 일시불 상수와 다름

- **분류**: incorrect
- **심각도**: low (기능 영향은 사실상 없음 — 서버가 정수로 파싱한다면 `"00"`과
  `"0"`은 동일하게 해석될 가능성이 높음; 다만 "확인된 앱 값과 바이트 단위로
  일치"를 표방하는 라이브러리 설계 원칙에는 어긋남)
- **앱 근거**: `analysis/apktool/smali/K4/h.smali:40-64`
  (`INS_0` enum 상수 생성자 호출에서 코드 문자열 리터럴이 `const-string v2, "0"`
  — 단일 문자 `"0"`), jadx 소스로도 동일하게 확인
  (`analysis/jadx/sources/K4/h.java:7` `INS_0("일시불", "0")`).
  이 코드는 `V4/a.java:238-264`(`getInstallmentType`)의 기본(default) 분기
  결과이자, 카드결제 빌더 `V4/a.java:32`
  (`paymentMethod.setHidAthnDvCd(1, creditCardData.getCreditCardType())`
  바로 위 줄 `setHidIsmtMnthNum(1, creditCardData.getInstallmentType())`)가
  `hidIsmtMnthNum1`로 그대로 전송하는 값이다.
- **라이브러리 근거**: `src/korail_mobile_api/mutation_models.py:311`
  (`installment: str = "00"  # months; "00" = lump sum`),
  `src/korail_mobile_api/mutation_payloads.py:1407`
  (`"hidIsmtMnthNum1": card.installment`).
- **내용**: 라이브러리의 `CardPayment` 기본값과 docstring은 일시불 코드를
  `"00"`(두 자리)이라고 명시하지만, smali로 확인한 앱의 실제 일시불 코드는
  `"0"`(한 자리)이다. 나머지 할부 코드(`"2"`,`"3"`,`"4"`,`"5"`,`"6"`,`"12"`,`"24"`)는
  자릿수 문제가 없어 호출자가 명시적으로 지정하면 정확히 전송되지만,
  기본값(아무 것도 지정하지 않은 일시불 결제)만 앱이 실제로 보내는 문자열과
  다르다.
- **수정 방향**: 기본값을 `"0"`으로 변경하고 docstring 주석의 "00" 표기를
  정정. (서버가 실제로 `"00"`을 거부하는지는 실서버 확인이 필요하나, 문서상
  "앱과 바이트 단위로 일치"를 표방하는 이상 이 드리프트 자체가 결함.)

---

## 4. Info — 문서화된 범위 밖 항목 (defect 아님)

`docs/RELEASE_GAP_PLAN.md:337-390` 과 `docs/api-status-by-service.md:112-116,
191`이 다음을 명시적으로 범위 밖으로 규정하고 있고 라이브러리 구현도 이와
정확히 일치한다 (조용한 누락이 아니라 문서화된 축소):

- **간편결제 전체**(Payco/네이버페이/카카오페이/토스페이/삼성페이 계열/
  Shinhan Fan Pay/Paybooc/KB Pay/모니모/제로페이/세틀뱅크) — PG WebView
  리디렉션이 필요해 "헤드리스 라이브러리 범위 밖이며 명시적으로 미지원이어야
  한다"고 `RELEASE_GAP_PLAN.md:388-390`가 못박음. `v4/a.java:69-236`
  (`getEasyRequest`)에서 확인한 `spayDvCd` 카탈로그(`"00"`=RailPlus,
  `"02"`/`"07"`=Payco, `"03"`/`"10"`=세틀뱅크, `"04"`=제로페이,
  `"08"`/`"09"`=카카오페이, `"11"`=Paybooc, `"12"`/`"13"`=토스페이,
  `"16"`=네이버페이, `"19"`=모니모)는 전부 라이브러리에 대응물이 없다.
- **포인트 결제/복합결제**(카드+포인트, KORAIL/철도/우리모아/OK캐시백 4종
  포인트 원장, `V4/a.java:266-345` `getPointRequest`) — `CardPayment`는
  포인트 행을 만들지 않는다. 카드 단독 결제만 지원.
- **후불(국회의원 등) 결제**(`hidStlMnsCd="03"`, `V4/a.java:57-67`
  `getCongressRequest`) — 미구현.
- **통합결제(`pay.intgStl.do`, 장바구니/복수상품 정산)** — 미구현,
  `RELEASE_GAP_PLAN.md:358`에 라우트/파라미터까지 문서화되어 있으나 구현
  대상에서 제외.
- **현금영수증 발급(`cashReceipt.issue.do`)** — 결제 성공 후 앱이 자동
  발화하는 후속 호출(`RELEASE_GAP_PLAN.md:334,366`)이지만 라이브러리에는
  이 카테고리에 대응하는 `MutationConsent` 카테고리 자체가 없다
  (`consent.py`의 6개 카테고리: reserve/payment/cancel/refund/
  discount_card/price_recalculation 중 cashReceipt 없음). 다른 간편결제
  항목처럼 "PG WebView라서 범위 밖"이라는 구체적 근거 문장은 찾지 못했으나,
  `docs/api-status-by-service.md:191`도 "결제/간편결제/포인트/금전성 API"
  사유로 미실행 처리했고, 프로젝트 메모리(`release-scope-decisions.md`)가
  기록한 "mutation 포함 범위 결정"에도 이 카테고리는 들어있지 않다 — 의도된
  축소로 보이나 cashReceipt만은 "PG WebView 필요" 근거가 간편결제만큼
  명시적이지 않아 완전히 확인되지는 않았다(확인불가에 가까운 info).
- **RailPlus 자동충전 조회(`railplus.autoCharge.do`)** — 읽기전용 갭 목록
  G-시리즈 옆에 "도메인 게이트 선택적 읽기"로 명시적으로 나열됨
  (`RELEASE_GAP_PLAN.md:141-148`).
- **세틀뱅크 계좌 등록/조회/인증**(`stbkAcnt`/`stbkRegBank`/`stlKeyPrs`/
  `stlKeyQry`) — 간편결제 카탈로그의 일부로 함께 범위 밖 처리.
- **Toss 자동결제 생성/키 발급**(`tossautoC`, `stlKeyPrs`/`stlKeyQry`의
  Toss 부분) — 위와 동일.

이 항목들은 findings에 포함하지 않았다(사용자 지침의 "의도적으로 제외된
범위"에 준하는 문서화된 결정이며, 정기권/단체예약처럼 명시적으로 나열되진
않았지만 동일한 성격).

---

## 5. 안전장치(카드정보 취급) 점검 결과 — 결함 없음 확인된 부분

- `redaction.py:232` `CARD_RE`(13~19자리 연속 숫자 패턴)가 어떤 키 아래에서든
  PAN을 백스톱으로 마스킹 — 카드 필드 목록에서 실수로 빠진 키가 있어도
  숫자 나열 자체는 걸린다는 점에서 §3.2 발견의 실질 위험도를 낮춘다
  (다만 `hidRsvChgNo` 값은 숫자 PAN이 아니므로 이 백스톱에 걸리지 않는다).
- `http.py:222-298` `post_mutation_form`이 결제 전송의 유일한 통로이고,
  `KORAIL_CARD_BEARING_MUTATION_CATEGORIES = frozenset({"payment"})`
  (`safety.py:317`)를 매개로 `fake_card_only`/`real_card_acknowledged`
  상호배타 검증이 이중(공개 메서드 + 전송 게이트)으로 걸려 있다. 우회 경로는
  찾지 못했다.
- `assert_mutation_route_category`(`safety.py:320-338`)가 카테고리-라우트
  고정 매핑을 강제해, `payment` 컨센트로 다른 라우트를 태울 수 없다.
- 카드 필드 7종(`hidStlCrCrdNo1`/`hidVanPwd1`/`hidCrdVlidTrm1`/
  `hidAthnVal1`/`hidAthnDvCd1`/`hidIsmtMnthNum1`/`hidCrdInpWayCd1`)은
  `SENSITIVE_KEYS`에 정확히 등재되어 있고 테스트(`test_real_card_payment.py:366-389`)로
  PAN 앞 6자리/뒤 4자리까지 미리보기에 남지 않음을 확인한다.

---

## 6. 확인 방법 메모

- jadx는 상수 리터럴을 대체로 정확히 보존했으나, `installment` 코드값
  (§3.3)은 지침에 따라 smali(`K4/h.smali`)로 교차 확인해 jadx 표기와 값이
  같음을 재확인했다.
- 응답 파서 대조는 `ReceiptDao.java`의 모든 getter를 `read_parsers.py:1013-1140`
  라인 단위로 1:1 대조했다.
- 결제 폼 대조는 `PaymentMethod.java`의 모든 필드 상수와 `v4/a.java`의 모든
  호출 분기(카드/간편결제/포인트/후불)를 추적한 뒤
  `mutation_payloads.py:1317-1413`과 대조했다.
- 레드액션 점검은 `redaction.py`의 `SENSITIVE_KEYS` 전체를 결제 폼이 실제로
  방출하는 키 목록과 하나씩 대조하는 방식으로 진행했다(§3.2의 근거).
