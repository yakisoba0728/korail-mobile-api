# Phase 2 — 안전·일관성 렌즈 (2차 독립 재확인)

대상: `korail-mobile-api` (이 저장소)
렌즈: 안전 게이트의 구멍 / 킬스위치·라우트 정합 / 카드·PII 마스킹 우회 경로 / 공개 API 표면 일관성
방법: 1차 8건 보고서를 읽되 재사용하지 않고, 세트·게이트를 **기계적으로 재계산**한 뒤
앱 근거는 jadx 원본 파일을 직접 열어 확인. 라이브러리 docstring의 인용은 **감사 대상**이므로
근거로 쓰지 않음(모두 원본에서 재확인).

저장소는 읽기 전용으로 다루었다. 검증 스크립트는 모두 `/tmp`에서 `PYTHONDONTWRITEBYTECODE=1`로
실행했고, 초기에 실수로 생성된 `src/korail_mobile_api/__pycache__` 는 즉시 삭제해 원상복구했다.

---

## 0. 카운팅 규칙 (이 렌즈의 분모)

이 렌즈는 도메인 슬라이스가 아니므로 "엔드포인트 개수"라는 분모를 공유하지 않는다.
대신 **안전 경계가 통제해야 하는 프로토콜 표면**을 분모로 삼는다:

| 표면 | 개수 | 근거 |
|---|---|---|
| 뮤테이션 라우트 | 8 | `safety.py:205-274` `KORAIL_MUTATION_ROUTES` |
| 읽기 전용 라우트 | 58 | `safety.py:69-182` `KORAIL_READ_ONLY_ROUTES` |
| NetFunnel opcode | 3 | `safety.py:380-384` `KORAIL_NETFUNNEL_QUERY_CONTRACTS` |
| **합계** | **69** | |

- `app_functions_extracted = 69`
- `implemented_count = 66` — 뮤테이션 8 + 읽기 58은 전송 경로로 도달 가능.
  NetFunnel 3개 opcode는 구현·테스트되어 있으나 **`KorailClient` 어느 경로에도 배선되지 않음**
  (P2SAF-07), 그래서 "구현됨"에서 제외했다.

또한 공개 뮤테이션 메서드 12개를 전수 정합 검사했다(§2).

---

## 1. 기계적 세트 검사 결과 (직접 재계산)

`/tmp`에서 `korail_mobile_api.safety` / `.consent` 를 로드해 계산:

```
mutation routes: 8 / distinct paths: 8
routes-not-in-categories: {}          ← 대칭차 공집합
categories-not-in-routes: {}          ← 대칭차 공집합
category w/o route:        {}         ← consent 플래그 6개 전부 라우트 소유
route category w/o consent flag: {}   ← 라우트 카테고리 6개 전부 플래그 존재
read-only routes: 58 / distinct paths: 58
tuple intersection RO ∩ MUT:  frozenset()
PATH-level overlap RO ∩ MUT:  set()   ← 메서드 무시해도 겹치는 경로 없음
ORDERS keys not in EXACT:   set()
OPTIONAL keys not in EXACT: set()
GET mutation routes: {reservation.dcntCrdExtn.do} → category 'discount_card'
card-bearing categories: {'payment'}
```

→ **킬스위치 카테고리 ↔ 라우트 매핑은 전단사이고 구멍이 없다.** 읽기 allowlist와 뮤테이션
allowlist는 경로 레벨에서도 겹치지 않으므로, 읽기 전송 경로(`post_form`/`get_json`)로
뮤테이션 라우트에 도달할 방법은 없다. 이 부분은 1차 어느 슬라이스도 기계적으로 확인하지 않았고,
**결과는 깨끗하다**(P2SAF-13로 기록).

단, 다음 하나는 깨끗하지 않다:

```
READ-ONLY ROUTES WITH NO EXACT FIELD CONTRACT: 13 / 58
```

→ P2SAF-03.

---

## 2. 4중 카테고리 정합 검사 (1차가 하지 않은 것)

`client.py` 를 AST로 파싱해, 뮤테이션 메서드마다 카테고리 문자열이 나타나는 **네 곳**을 뽑아
`KORAIL_MUTATION_ROUTE_CATEGORIES[route]` 와 대조했다. 네 곳:
① `require_mutation_consent(consent, X)` ② `MutationPreview(category=X)`
③ 전송 경로 `category=X` kwarg ④ 라우트가 소유한 카테고리.

②는 **전송 게이트가 재검사하지 않는 유일한 지점**이다 — 여기가 틀리면 호출자가 "무엇을
승인하는가"를 잘못 표시받는데 아무도 잡지 못한다.

| 메서드 | ① | ② | ③ | ④ | 결과 |
|---|---|---|---|---|---|
| reserve | reserve | reserve | reserve | reserve | OK |
| confirm_standby_hold | reserve | reserve | reserve | reserve | OK |
| reserve_transfer | reserve | reserve | reserve | reserve | OK |
| reserve_merge | reserve | reserve | reserve | reserve | OK |
| cancel_unpaid_hold | cancel | cancel | cancel | cancel | OK |
| pay_with_fake_card | payment | payment | payment | payment | OK |
| pay_with_card | payment | payment | payment | payment | OK |
| refund | refund | refund | refund | refund | OK |
| register_discount_card | discount_card | discount_card | discount_card | discount_card | OK |
| extend_discount_card | discount_card | discount_card(GET) | discount_card | discount_card | OK |
| reserve_with_discount_card | reserve | reserve | reserve | reserve | OK |
| recalculate_price | price_recalculation | price_recalculation | price_recalculation | price_recalculation | OK |

**12/12 정합. 프리뷰의 `method` 문자열도 라우트의 등록 메서드와 일치**
(`extend_discount_card` 만 `"GET"`, 나머지 `"POST"`).

---

## 3. 1차가 **놓친** 것

> **심각도 정합 안내.** P2SAF-01 / P2SAF-02 / 그리고 1차 K5-02(`hidRsvChgNo`)는 **완전히
> 동일한 결함류**다 — `SENSITIVE_KEYS` 가 정확 일치로만 매칭하는데 철자 하나가 빠져 있고,
> 그 결과 `README.md:209-211` 의 "can never" 보증이 깨진다. 따라서 셋 다 **medium** 으로
> 통일했다. 이 과제의 심각도 기준상 `critical` 은 "카드정보가 샌다", `high` 는 "실서버에서
> 실패하거나 잘못된 결과를 낸다"인데, 프리뷰 PII 노출은 결제카드도 아니고 서버 동작을 바꾸지도
> 않는다. P2SAF-01이 셋 중 가장 나쁜 사례인 이유(단일 식별자 파편이 아니라 실명+휴대폰+
> 고객관리번호가 한 묶음으로 재식별 가능)는 해당 항목 본문에 적었다.

### P2SAF-01 [risk / medium] `register_discount_card` 프리뷰가 동반자 PII를 평문 노출

앱은 N카드 구매 시 동반 사용자를 **인덱스가 붙은 키**로 보낸다:

- `analysis/jadx/sources/com/korail/talk/network/dao/research/NCardReservationDao.java:16`
  `public static final String APD_CUST_NAME = "apdCustName_";`
- `:29` `private final String CUST_MG_NO = "custMgNo_";`
- `:30` `private final String APD_CUST_TEL = "apdCustTeln_";`
- 세 상수 이름이 전부 `_` 로 끝나는 것이 이미 인덱스 접미의 증거이고,
  `:67`(이름) / `:71`(전화) / `:123`(고객관리번호) 세 곳에서 각각 그 접두에 1부터의
  일련번호를 이어붙여 동반자 정보 맵에 넣는다. (앱 소스 문장은 타사 저작물이라
  옮기지 않고 위치와 동작만 적는다.)
- 라우트 선언: `dao/research/ResearchService.java:68-70` — Retrofit 메서드
  `setNCardReservation` 이 `@FieldMap` 두 개를 받는다(그중 하나가 위 동반자 맵).

라이브러리는 그대로 재현한다:
`src/korail_mobile_api/mutation_payloads.py:1568` `form[f"custMgNo_{index}"] = ...`,
`:1572` `form[f"apdCustName_{index}"]`, `:1576` `form[f"apdCustTeln_{index}"]`.

그런데 `SENSITIVE_KEYS` 는 **정확 일치(casefold)** 로만 매칭한다
(`redaction.py:340` `sensitive = name.casefold() in SENSITIVE_KEYS`). 세트에는
`"custMgNo"`(`redaction.py:29`), `"acepCustNm"`(`:32`), `"acepCustTeln"`(`:33`) 이 있으나
**인덱스가 붙은 철자는 하나도 없다**. 같은 파일이 `txtCardNo_1..9`, `txtSrcarNo1..9`,
`txtSeatNo1..9` 는 인덱스 전개로 등재해 둔 것(`redaction.py:154-161, 194-197`)과 대비된다.

실측(`/tmp`, 라이브러리 로드):

```python
redact_payload({"custMgNo_1":"1234567890","apdCustTeln_1":"01012345678",
                "apdCustName_1":"홍길동"})
# → {'custMgNo_1': '1234567890', 'apdCustTeln_1': '01012345678', 'apdCustName_1': '홍길동'}
```

세 값 모두 **그대로** 프리뷰에 남는다. 전화번호는 11자리라 `CARD_RE`(13~19자리)에도 걸리지 않는다.
`MutationPreview.__post_init__`(`consent.py:131`)이 `redact_payload` 를 통과시키므로,
`dry_run=True`(기본값) 호출이 만들어 낸 프리뷰 객체 안에 고객관리번호·실명·휴대폰번호가
평문으로 보존된다.

이것은 **문서화된 보증을 깬다**:
- `README.md:209-211` — "The preview's payload is forced through `redact_payload` on
  construction, so it can never hold a raw card number, PNR or **other identity** even if you
  built it from real values."
- `SECURITY.md` — "each returns a redacted preview".

1차 K7(정기권·패스·포인트)은 N카드 구매를 다루지 않았고, K5(결제)는 `payment` 카테고리만 봤다.
슬라이스 경계에 정확히 걸려 아무도 보지 않은 지점이다.

**셋 중 가장 나쁜 사례인 이유**: `saleDd`(날짜 파편)나 `hidRsvChgNo`(예약변경번호)와 달리
여기서 새는 것은 **실명 + 휴대폰번호 + 고객관리번호가 한 행에 묶인** 개인정보다. 세 값이
함께 있으면 그 자체로 특정 개인을 재식별한다. 게다가 이 세 값의 의미상 동일한 다른 철자
(`acepCustNm` / `acepCustTeln` / `custMgNo`)는 **이미 세트에 등재되어 있다** — 즉 이 코드베이스는
"이 값들은 가려야 한다"고 이미 판단했고, 인덱스 접미사 하나 때문에 그 판단이 무효화된 것이다.

**수정 방향**: `SENSITIVE_KEYS` 에 `custMgNo_{1..N}` / `apdCustName_{1..N}` /
`apdCustTeln_{1..N}` 를 인덱스 전개로 추가하거나, `redact_payload` 를 `키_숫자` 접미 정규화
매칭으로 바꾼다(후자가 근본적).

---

### P2SAF-02 [risk / medium] `extend_discount_card` 프리뷰가 4부분 자격증명 중 `saleDd` 만 노출

앱 선언(`analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:65-66`).
디컴파일 소스는 타사 저작물이라 옮겨 싣지 않고, 관측한 **와이어 계약**만 적는다 —
해당 줄의 Retrofit 메서드(`setNCardExtension`)는 `GET
/classes/com.korail.mobile.reservation.dcntCrdExtn.do` 를 선언하고, 공통 `Device` 외에
`@Query` 키 네 개를 이 순서로 받는다:

| # | `@Query` 키 | 클라이언트 대응 필드 (`DiscountCardTicket`) |
|---:|---|---|
| 1 | `saleWctNo` | `sale_window_no` |
| 2 | `saleDd` | `sale_date` (다른 라우트에서는 `saleDt` 철자) |
| 3 | `saleSqno` | `sale_sequence` |
| 4 | `tkRetPwd` | `return_password` |

`saleWctNo + saleDd + saleSqno + tkRetPwd` 는 승차권을 식별·인증하는 **한 덩어리 bearer
자격증명**이다(같은 4개조로 환불·영수증·승무원호출이 모두 동작한다).

라이브러리(`mutation_payloads.py:1614-1630`)는 4개를 정확히 보낸다. 그러나 `SENSITIVE_KEYS`는
`"saleWctNo"`(`redaction.py:26`), `"saleSqno"`(`:28`), `"tkRetPwd"`(`:31`)는 등재하고
**`saleDd` 는 등재하지 않았다** — 같은 값의 다른 철자 `"saleDt"`(`:27`)만 있다.

실측:
```python
redact_payload({"saleWctNo":"0221","saleDd":"20260101","saleSqno":"0001","tkRetPwd":"1234"})
# → {'saleWctNo':'[REDACTED]','saleDd':'20260101','saleSqno':'[REDACTED]','tkRetPwd':'[REDACTED]'}
```

한 자격증명의 4분의 3만 가려지는 것은 마스킹 정책의 자기모순이다. 1차 어느 슬라이스도
`discount_card` 카테고리의 프리뷰를 검사하지 않았다.

**수정 방향**: `SENSITIVE_KEYS` 에 `"saleDd"` 추가.

---

### P2SAF-03 [risk / medium] 읽기 라우트 58개 중 13개는 필드 계약이 아예 없어 임의 필드·비스칼라 값이 통과

`assert_read_only_request_fields` 는 `safety.py:1384-1386` 에서

```python
allowed = KORAIL_EXACT_REQUEST_FIELDS.get(route_path)
if allowed is None:
    return          # ← 중복검사·형태검사·값타입검사 모두 건너뜀
```

즉 계약이 없는 라우트는 **필드 이름 검증도, `safety.py:1427-1430`의 "값은 str/int만" 검사도**
받지 않는다. 재계산 결과 계약 없는 읽기 라우트는 13개:

```
/classes/com.korail.mobile.login.Login          ← 자격증명 전송 라우트
/classes/com.korail.mobile.myTicket.MyTicketList
/classes/com.korail.mobile.common.code.do
/classes/com.korail.mobile.common.stationdata
/classes/com.korail.mobile.common.stationinfo
/classes/com.korail.mobile.qry.chtnStn.do
/classes/com.korail.mobile.research.actualTrainSchedule.do
/classes/com.korail.mobile.schedule.runDt
/classes/com.korail.mobile.seatMovie.ScheduleView
/ebizcross/getUUID.do
/ebizmaas/EbizMaasStationList.do
/file/CACHE/prdMobilePlusMain.cache
/file/CACHE/prdMobilePlusNotice.cache
```

실측:
```python
A("/classes/com.korail.mobile.login.Login",
  {"Device":"AD","evil_field":{"nested":"dict"},"txtPwd":object()})
# → 통과 (예외 없음)
A("/classes/com.korail.mobile.dlay.dptnBank.do", {"Device":"AD","Version":"1","Key":"k","evil":"x"})
# → KorailProtocolError
```

왜 이것이 안전 문제인가: `safety.py:62-68` 이 세운 방어 논리가 바로 **필드 고정으로 오버로드를
막는다**는 것이다 —

> "NOTE on certification.ReservationList: that path carries TWO Retrofit overloads … 
> KORAIL_EXACT_REQUEST_FIELDS pins the read overload's exact four fields, so the write
> overload's shape can never be emitted through this route."

앱에서 실제로 확인했다(`dao/certification/CertificationService.java:22-23` 쓰기 오버로드
`applyDisabilityCertification`, `:45-46` 읽기 오버로드 `inquiryTicketRsv`). 그 방어는 계약이
있는 45개 라우트에만 존재하고, 위 13개에는 **원리적으로 존재하지 않는다**. 앱 전체 Retrofit 선언을
훑어 경로 중복을 조사한 결과 위 13개에는 현재 쓰기 오버로드가 없어 즉시 악용 가능한 경로는 아니지만,
allowlist가 표방하는 보증이 라우트마다 다르다는 사실 자체가 결함이다.

`login.Login` 이 포함된 것이 특히 나쁘다 — 이 라우트는 회원번호와 변환된 비밀번호를 나른다.

**수정 방향**: 13개 라우트에 `KORAIL_EXACT_REQUEST_FIELDS` 항목을 추가하고, `allowed is None`
분기를 "미등록 라우트는 거부"로 뒤집는다(또는 최소한 값 타입 검사는 조기 return 앞으로 옮긴다).

#### P2SAF-03b — 그리고 더 날카로운 쪽: **뮤테이션 라우트 8개는 8/8 전부 필드 미고정**

`safety.py:62-68` 의 오버로드 방어 논리를 뮤테이션 쪽에 적용하면 상황이 더 나쁘다.
앱 전체 Retrofit 선언에서 경로가 2회 이상 선언된 것을 뽑아 직접 열어 본 결과:

```
2 POST /classes/com.korail.mobile.certification.TicketReservation   ← 뮤테이션 라우트
2 POST /classes/com.korail.mobile.reservationCancel.ReservationCancelChk ← 뮤테이션 라우트
2 POST /classes/com.korail.mobile.nonMember.NonMemTicket
2 POST /classes/com.korail.mobile.reservation.reservationChange.do
2 POST /classes/com.korail.mobile.common.encrypt.do
2 GET  /classes/com.korail.mobile.certification.ReservationList
```

`certification.TicketReservation` 은 **진짜 서로 다른 두 오버로드**다
(`dao/certification/CertificationService.java:52-54`: `pbepInfo` + `@FieldMap` 4개 /
`:60-62`: `Device/Version/Key` + `@FieldMap` 1개). `nonMember.NonMemTicket` 도 마찬가지
(`:48-50` / `:56-58`).
(`ReservationCancelChk` 2건은 `ReservationCancelService.java:19-21` 과
`BusReservationService.java:19-21` 의 동일 시그니처 중복 선언이라 오버로드가 아니다.)

그런데 `post_mutation_form` 은 설계상 **필드 검증을 전혀 하지 않는다** — `http.py:240-241`:
> "``data`` is sent verbatim (the reservation/cancel builders already include the common
> Device/Version/Key fields); **no read-only field allowlist applies.**"

즉 `KORAIL_EXACT_REQUEST_FIELDS` 에 뮤테이션 경로는 0건이고(재계산으로 확인:
"field contracts for paths not in either allowlist: []" 이며 뮤테이션 8개 중 등재된 것 없음),
읽기 쪽 45개 라우트가 받는 형태 검증을 **돈이 움직이는 8개 라우트는 하나도 받지 않는다.**
PAN을 나르는 `payment.ReservationPayment` 도 포함된다.

이것은 의도된 설계이며(빌더가 폼을 만들므로 외부 주입 경로가 없다) 즉시 악용 가능한 결함은
아니다. 그러나 방어 강도가 **경계의 덜 위험한 쪽에서 더 강하다**는 역전이고,
`safety.py:62-68` 이 세운 "필드 고정으로 오버로드를 막는다"는 원칙이 실제 오버로드가 존재하는
유일한 뮤테이션 라우트에는 적용되지 않는다는 뜻이다. `KorailHttpClient` 는 공개 API이므로
호출자가 직접 `post_mutation_form(route, 임의폼, consent=..., category=...)` 을 부를 수 있고,
그때 폼 형태를 검증하는 것은 아무것도 없다.

**수정 방향**: 뮤테이션 8개 라우트에도 `KORAIL_EXACT_REQUEST_FIELDS` 상당의 계약을 등재하고
`post_mutation_form` 이 전송 직전에 검사하게 한다(빌더 산출물은 통과하므로 기존 동작 불변).

---

### P2SAF-04 [risk / medium] `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 가 자기 정의를 만족하는 카테고리를 누락 — 그리고 그 완전성을 검사하는 테스트가 없다

`safety.py:295` 의 정의는 명시적이다: **"The consent categories whose forms carry a card number
in the clear."** 멤버는 `{"payment"}` 하나뿐이다(`safety.py:317`).

그런데 앱은 N카드 예약을 **평범한 예약 라우트**로 처리하고, 그 폼에 카드번호를 싣는다:

- `analysis/jadx/sources/w4/a.java:93` `getNCardReservationRequest(...)`
- `w4/a.java:100` `oPsg.setDiscKndCd(1, "153");`
- `w4/a.java:101` `oPsg.setCardNo(1, ticketDetailResponse.getDcnt_crd_info().getH_dcnt_crd_no());`
- `com/korail/talk/network/data/reservation/old/OPsg.java` `CARD_NO = "txtCardNo_"`,
  `setCardNo(int, String) { put(CARD_NO + i9, str); }`
- 라우트: `dao/certification/CertificationService.java:52-54` `certification.TicketReservation`

라이브러리도 동일하게 구현한다 — `mutation_payloads.py:1704`
`rebuilt["txtCardNo_1"] = ...`, `client.py:2207` `require_mutation_consent(consent, "reserve")`,
`client.py:2226-2228` `category="reserve"`.

라이브러리 자신이 이 번호를 어떻게 평가하는지는 `redaction.py:179-183` 에 적혀 있다:
"h_dcnt_crd_no is a bearer credential in the strongest sense this API has: … anyone holding it
can spend someone else's card."

**핵심 주장(이것 하나만 성립하면 된다)**: 세트가 스스로 내린 정의 —
"카드번호를 평문으로 나르는 폼을 가진 consent 카테고리" — 를 **`reserve` 도 만족하는데
멤버가 아니다.** 문서와 코드 중 하나가 틀렸다.

그리고 그 완전성을 검사하는 테스트가 없다. `tests/test_real_card_payment.py:203-219` 는
- `"payment" in KORAIL_CARD_BEARING_MUTATION_CATEGORIES` (포함 방향)
- `⊆ set(MUTATION_CATEGORIES)` (부분집합)
- GET 라우트 카테고리와 교집합 공집합

세 가지만 본다. **"카드번호를 나르는 폼을 가진 카테고리가 빠짐없이 들어있는가"라는 반대 방향은
아무도 검사하지 않는다.** 세트의 가치는 바로 그 방향에 있는데(주석 `safety.py:305-308`:
"A second card-bearing category would otherwise reach the wire past a gate that reads
`category == "payment"` and quietly says no"), 정작 그 시나리오를 막을 검사가 없다.

**과장하지 않기 위한 단서 세 가지**:
1. **프리뷰 마스킹에는 구멍이 없다.** `txtCardNo_1` 은 `redaction.py:194-197` 에 등재되어 있다.
   이것은 유출이 아니라 **게이트 범위(scope)** 결함이다.
2. 호출자는 `card_no` 를 `reserve_with_discount_card` 라는 이름의 메서드에 **직접 넘겨야** 한다.
   consent만으로 자동으로 벌어지는 일이 아니다.
3. `payment` 게이트가 막는 것은 "실제 돈이 움직인다"는 선언이고, N카드는 선불 잔여횟수 소진이라
   성격이 완전히 같지 않다.

이 셋 때문에 critical이 아니라 medium이다.

**수정 방향**: (a) `reserve` 를 세트에 넣고(기본 consent는 `fake_card_only=True`라 통과하므로
기존 호출자 동작 불변), 또는 (b) 세트 이름/주석을 "PAN(결제카드)을 나르는 카테고리"로 좁히고
N카드용 별도 문장을 둔다. 어느 쪽이든 폼 키 → 카테고리 역인덱스를 만들어 테스트로 고정할 것.

---

### P2SAF-05 [risk / medium] 로그인 응답의 회원 PII 철자가 `SENSITIVE_KEYS` 에 전무

앱의 로그인 응답 DTO(`analysis/jadx/sources/com/korail/talk/network/dao/login/LoginDao.java`)는
다음 필드를 담는다: `:84 encryptCustNo`, `:93 strBtdt`(생년월일), `:94 strCpNo`(휴대폰),
`:99 strCustNm`(실명), `:100 strCustNo`, `:102 strEmailAdr`, `:107 strMbCrdNo`(회원카드번호).

라이브러리는 이 응답 전체를 두 곳에 평문 보존한다:
- `session.py:243-249` `KorailSession(..., raw=response.raw)`
- `session.py:216-225` `KorailAuthContinuationRequired(..., post_data=..., raw=response.raw)`
  — `build_login_authentication_post_data`(`session.py:76-94`)가
  `KORAIL_LOGIN_CONTINUATION_FIELDS`(`session.py:29-60`, 위 필드 전부 포함)를
  `key=value&...` 문자열로 직렬화한다. 이 문자열은 `self.pending` 에 세션 클라이언트가 보관한다
  (`session.py:167`).

그런데 `SENSITIVE_KEYS` 에는 `strCpNo` / `strCustNm` / `strBtdt` / `strEmailAdr` /
`strMbCrdNo` / `strCustNo` / `encryptCustNo` 가 **하나도 없다**. 반면 같은 회원카드번호의
다른 철자 `"mbCrdNo"` 는 `redaction.py:35` 에 등재되어 있고, `session.py:232-235` 는 두 철자를
**둘 다** 읽는다:

```python
member_card_no = str(response.raw.get("mbCrdNo") or response.raw.get("strMbCrdNo") or "") or None
```

즉 **같은 값이 어느 철자로 오느냐에 따라 마스킹되기도 하고 안 되기도 한다.**
공개 마스킹 헬퍼 `redact_mapping`(`__init__.py:156,495`)을 `session.raw` 에 적용해도
휴대폰·실명·생년월일·이메일은 그대로 나온다.

현재 라이브러리 스스로 이 값을 로그로 흘리지는 않으므로 활성 유출은 아니다(그래서 high가 아님).
그러나 `SECURITY.md` 가 "Do not disclose credentials, cookies, tokens, PNRs, raw responses…"
라고 요구하면서 정작 raw 응답을 위생처리할 공개 수단이 이 필드들을 덮지 않는다.

**수정 방향**: `KORAIL_LOGIN_CONTINUATION_FIELDS` 중 PII 성격 필드를 `SENSITIVE_KEYS` 에 등재.

---

### P2SAF-06 [risk / low] `pay_with_fake_card` 와 `pay_with_card` 의 consent 검사 비대칭

- `client.py:1899-1903` — `pay_with_fake_card` 는 `fake_card_only` **만** 검사.
- `client.py:1972-1984` — `pay_with_card` 는 `real_card_acknowledged` 와 `fake_card_only`
  **양쪽** 을 검사.
- `http.py:276-291` — 전송 게이트는 "둘 다 True"를 모순으로 거부.

따라서 `MutationConsent(allow_payment=True, fake_card_only=True,
real_card_acknowledged=True, dry_run=True)` — 전송 게이트가 **모순이라고 거부하는 바로 그
consent** — 는 `pay_with_fake_card` 의 자체 검사를 통과하고, `dry_run=True`이므로
전송 게이트에 **도달하지 않은 채** 정상 프리뷰를 반환한다. 실측 확인함.

돈이 움직이지 않으므로 fail-safe이고 심각도는 low다. 문제는 일관성이다: 호출자는 "이 consent로
실행하면 되겠구나"라는 잘못된 신호를 프리뷰에서 받고, `dry_run=False` 로 바꾸는 순간
`MutationNotAllowedError` 를 만난다. 형제 메서드가 같은 불변식을 다른 강도로 검사한다.

**수정 방향**: `pay_with_fake_card` 에 `if consent.real_card_acknowledged: raise` 를 추가하거나,
모순 검사를 두 메서드가 공유하는 헬퍼로 올린다.

---

### P2SAF-07 [risk / low] NetFunnel 대기열이 `KorailClient` 어디에도 배선되지 않음

앱은 액션별로 분리된 큐를 통과한다
(`analysis/jadx/sources/K4/g.java:43-50`):

```
act_8 / act_8_2 (조회·성수기조회), act_6 (상품), act_14 (예약),
act_18 (결제), act_21 (예약승차권), act_22 (환불), act_4 (테스트)
```

라이브러리의 `netfunnel.py`(934줄)는 이 8개를 상수로 갖고 있고 opcode 3종·노드 리다이렉션까지
구현·테스트되어 있다. 그러나 `client.py` 와 `http.py` 에는 `netfunnel` 참조가 **0건**이다
(grep 확인). `KorailConfig.netfunnel_enabled` 기본값은 `False`(`config.py:57`).

즉 `client.reserve(..., dry_run=False)` 는 앱이 반드시 통과하는 `act_14` 큐를 건너뛰고
`certification.TicketReservation` 을 바로 친다.

이것은 `config.py:35-56` 에 근거와 함께 **의도적으로 기록된 설계**다(모든 실측 호출이 토큰 없이
성공했고, 켜면 매 호출에 왕복 1회와 3초 타임아웃이 붙는다). 그래서 결함이 아니라 리스크로
기록한다. 다만 이 패키지가 "앱과 동일한 wire"를 표방하는 가운데 **뮤테이션 경로가 앱과 다른
유일한 지점**이고, 서버가 계측을 켜는 순간(성수기 등) 조용히 거부당할 지점이라는 사실은
남겨 둘 가치가 있다. `slot()` 컨텍스트 매니저를 뮤테이션 메서드가 opt-in으로 감쌀 수 있게
배선해 두는 것이 최소 개선이다.

---

### P2SAF-08 [doc-drift / medium] README·SECURITY의 "프리뷰는 절대 신원을 담지 않는다" 주장이 반증됨

`README.md:209-211`:
> "The preview's payload is forced through `redact_payload` on construction, so it can never
> hold a raw card number, PNR or other identity even if you built it from real values."

`SECURITY.md`: "each returns a redacted preview".

반증 3건:
- P2SAF-01 `custMgNo_1` / `apdCustName_1` / `apdCustTeln_1` (실명·휴대폰·고객관리번호)
- P2SAF-02 `saleDd`
- 1차 K5-02 가 이미 찾은 `hidRsvChgNo` (교차확인함 — `redaction.py` 에
  `h_rsv_chg_no` / `reservation_change_no` 는 있으나 `hidRsvChgNo` 는 없음;
  `mutation_payloads.py:1398` 이 카드결제 폼에 넣는다)

"can never"는 현재 코드가 지탱하지 못하는 강한 주장이다. 코드를 고치거나 문장을 약화해야 한다.

---

### P2SAF-09 [partial / low] `MutationPreview.payload` 타입 주석과 실제 값 타입 불일치

`consent.py:127` `payload: Mapping[str, str]` /
`redaction.py:321` `def redact_payload(...) -> dict[str, str | list[str]]`.

`recalculate_price` 는 정당하게 리스트 값을 만든다 — 앱 선언
`dao/certification/CertificationService.java:37` 의 마지막 6개 인자가 `List<String>` 이고
Retrofit이 같은 키를 반복 방출하기 때문이다. 실측:

```python
MutationPreview(..., payload={"hidDscpNo":["A","B"]}).payload["hidDscpNo"]
# → list, 주석은 str 이라고 말한다
```

타입 체커를 쓰는 소비자에게만 영향. 동작에는 지장 없음.

---

### P2SAF-10 [partial / low] 뮤테이션 반환형이 제각각 — 1차 K6-06은 이 구조적 비일관의 증상

| 메서드 | 반환형 |
|---|---|
| reserve / reserve_transfer / reserve_merge / reserve_with_discount_card | `ReservationHoldResponse` (관대 파싱 폴백 있음) |
| recalculate_price | `ReservationHoldResponse` (엄격 파싱) |
| register_discount_card | `DiscountCardPurchaseResponse` |
| pay_with_fake_card / pay_with_card | `ReservationPaymentResponse` |
| **cancel_unpaid_hold** | `BaseKorailResponse` (원시) |
| **confirm_standby_hold** | `BaseKorailResponse` (원시) |
| **refund** | `BaseKorailResponse` (원시) |
| **extend_discount_card** | `BaseKorailResponse` (원시) |

`client.py:1841, 1603, 2016, 2118`.

같은 게이트·같은 전송 경로를 쓰는 12개 메서드 중 4개만 파싱 모델이 없다. 1차 06-cancel 의
K6-06(`stlList[].stl_mns_cd` 미파싱)은 독립 결함이 아니라 **`refund` 가 원시 envelope만
돌려주기 때문에 발생하는 증상**이다 — `refund` 에 응답 모델이 있었다면 그 필드는 모델 정의
단계에서 잡혔을 것이다. 같은 논리로 `cancel_unpaid_hold`(취소 성공/부분성공 구분),
`extend_discount_card`(연장 결과·비용)도 호출자가 `raw` dict를 직접 파야 한다.

돈이 움직이는 카테고리(`refund`)가 파싱되지 않는 쪽에 있다는 점이 특히 아쉽다.

---

### P2SAF-11 [risk / low] DynaPath 403 판별의 경로 제한 — 1차 K8-06 교차확인 (확인 결과: 1차가 옳음)

`http.py:69-73` 은 `response.status_code == 403 and path in DYNAPATH_ALLOWLIST_PATHS and
dynapath_rejected` 세 조건을 모두 요구한다.

앱을 직접 확인했다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:59-90`
은 응답 헤더를 순회하며 `DynaPath-Result` 를 찾고 값이 음수면 body의 `message` 를
`setMacroShowDialog` 로 넘긴다 — **경로 조건도 상태코드 조건도 없다**.

토큰이 붙는 경로는 확실히 6개로 제한된다(`ExecuteDao.java:27`, 라이브러리
`constants.py:421-430` 과 정확히 일치 — 재확인함). 그러나 **거부를 인지하는 범위**는 앱이
더 넓다. 서버가 allowlist 밖 경로에 이 헤더를 붙여 403을 주면 라이브러리는
`KorailDynaPathError` 대신 밋밋한 `KorailTransportError` 를 던진다. 1차 판단이 맞다.

한 가지 덧붙일 것: `ExecuteDao.java:35` 는 `request.getUrl().contains(str)` — **부분 문자열**
매칭이다. 라이브러리 `http.py:127` 은 `if path not in dynapath.allowlist_paths` — 정확 일치.
라이브러리 쪽이 더 좁고, 이 방향의 차이는 안전한 쪽이다.

---

### P2SAF-12 [doc-drift / medium] `reserve_transfer` 가 "환승 홀드는 이 클라이언트로 해제 불가"라고 **잘못** 안내 — 고아 PNR을 유발하는 문서 결함

1차 03-reserve 의 K3-07(`cancel_unpaid_hold` docstring이 "단일 여정만"이라 반대로 서술)을
판정하기 위해 빌더를 직접 읽었다. **1차가 옳다**, 그리고 안전 영향은 1차가 매긴
low보다 크다.

빌더는 다구간 홀드를 **명시적으로 허용**한다 (`mutation_payloads.py:1230-1249`):

```python
journey_count = response.journey_count
legs = None
if isinstance(journey_count, str) and journey_count.strip().isdigit():
    legs = int(journey_count)
if (... or legs is None or legs < 1):      # ← legs != 1 이 아니라 legs < 1
    raise KorailProtocolError(...)
...
"txtJrnyCnt": str(legs),                   # ← 고정 "1" 이 아니라 에코
```

그 위 주석(`:1223-1229`)이 이유까지 못박아 두었다: 환승 홀드를 거부하면 "would leave a live
transfer reservation with **no way to release it** -- the orphaned hold this whole subsystem
exists to prevent."

그런데 세 곳의 문서가 정반대를 말한다:
- `client.py:1842` — "Cancel a fresh, unpaid **single-journey** reservation hold."
- `client.py:1845-1847` — "`build_unpaid_reservation_cancel_form` requires `hold` to be one
  successful (SUCC) **single-journey** hold with a PNR"
- `client.py:1731-1733` (`reserve_transfer`) — "note that `cancel_unpaid_hold` currently accepts
  **single-journey holds only, so a live transfer hold cannot be released through this client**."
- `mutation_payloads.py:1265-1266` — "This builder is the fresh-**single-journey**-hold flow"

**왜 low가 아니라 medium인가.** 앞의 두 개는 단순 drift다. 그러나 `client.py:1731-1733` 은
`reserve_transfer` 의 docstring이고, `reserve_transfer` 는 **실제 좌석을 잡는 메서드**다.
운영자는 홀드를 만들기 직전에 이 문장을 읽고 "이건 해제할 수 없구나"라고 알게 된다.
그 결과 (a) 라이브 환승 홀드를 아예 시도하지 않거나, (b) 시도했다가 해제를 포기하고
**살아 있는 PNR을 방치**한다. 실제로는 `cancel_unpaid_hold(hold, consent=...)` 를 그대로
부르면 해제된다. 즉 이 문장은 자신이 경고하는 바로 그 사고(고아 홀드)를 **유발하는 방향으로**
틀려 있다 — 코드가 막으려고 설계된 실패를 문서가 되살린다.

1차 K3-07은 `cancel_unpaid_hold` 쪽 두 문장만 지적했고 `reserve_transfer` 쪽은 언급하지 않았다.
이 렌즈에서 추가하는 것은 그 부분과, 심각도 재평가다.

**수정 방향**: 네 문장 모두 "단일 여정" → "여정 수를 에코하며 환승(2구간) 홀드도 해제 가능"으로
정정. 특히 `client.py:1731-1733` 은 즉시 고칠 것.

---

### P2SAF-13 [info] 교차확인 클린 — 게이트 핵심 불변식은 구멍 없음

1차가 기계적으로 확인하지 않은 것들을 재계산했고, 다음은 **깨끗하다**:

1. 뮤테이션 라우트 8 ↔ 카테고리 매핑 8 대칭차 공집합.
2. consent 플래그 6 ↔ 라우트 카테고리 6 전단사. 라우트 없는 카테고리도, 플래그 없는 카테고리도 없음.
3. 읽기 allowlist ∩ 뮤테이션 allowlist = 공집합. **경로 레벨**에서도 공집합(메서드만 바꿔
   읽기 경로로 뮤테이션에 도달하는 우회 없음).
4. GET 뮤테이션 라우트는 1개뿐이고 그 카테고리(`discount_card`)는 카드보유 카테고리와 교집합 없음
   → `get_mutation_query` 에 카드 분기가 없는 것이 현재로선 정당(단 P2SAF-04 참조).
5. `KORAIL_EXACT_REQUEST_FIELD_ORDERS` / `KORAIL_OPTIONAL_REQUEST_FIELDS` 의 키는 모두
   `KORAIL_EXACT_REQUEST_FIELDS` 의 부분집합 — 고아 항목 없음.
6. 12개 뮤테이션 메서드 4중 카테고리 정합 12/12 (§2).
7. `post_mutation_form` / `get_mutation_query` 이외에 뮤테이션 라우트로 전송하는 코드 경로 없음
   (grep으로 전 소스 확인).
8. `parse_base_response`(`http.py:37-42`)의 P058 세션만료는 `raise_on_fail=False` 여도
   반드시 raise → 결제 경로(`raise_on_fail=False`)에서도 세션만료가 조용히 성공으로 오인되지 않음.
9. **뮤테이션 쪽 필드 고정 여부를 검사했고, 의도적으로 부재함을 확인했다** — `http.py:240-241`
   이 명시적으로 "no read-only field allowlist applies" 라고 선언한다. 결과는 P2SAF-03b.

---

### P2SAF-14 [info] `redact_value` 가 공개 API에 없어 응답 모델을 마스킹할 수단이 없음

`__init__.py:156` 은 `redact_mapping` 과 `redact_payload` 만 export한다(`:495-496`).
그런데 dataclass와 중첩 구조를 처리할 수 있는 유일한 함수는 `redact_value`
(`redaction.py:290-309`)이고 이것은 공개되지 않는다. 이 라이브러리 응답은 전부 dataclass이므로,
`SECURITY.md` 가 요구하는 "raw 응답을 공유 전 위생처리하라"를 사용자가 수행할 공개 수단이
실질적으로 없다(`redact_mapping(resp.raw)` 은 dict에만 동작하고 P2SAF-05의 철자들을 놓친다).

---

### P2SAF-15 [info] `logout` 은 서버측 상태변경인데 읽기 allowlist에 등재

`GET /classes/com.korail.mobile.login.Logout` 이 `KORAIL_READ_ONLY_ROUTES`(`safety.py:76`)에
있다. 앱 근거 `dao/login/LoginService.java:29-30` (`@GET`, 무인자).
`safety.py:56-60` 이 이 예외를 명시적으로 기록해 두었고, 세션 무효화는 파괴적이지 않으며
`session.py:252-268` 은 실패를 삼키고 로컬 세션을 항상 정리한다. **의도된 설계로 판단**하며
결함으로 올리지 않는다. 다만 "읽기 전용 allowlist"라는 이름이 58개 중 1개에 대해 문자 그대로
참이 아니라는 점만 기록한다.

---

## 4. 1차가 **틀리게 본** 것

**반증된 1차 주장은 없다.** 다만 심각도를 **올려야 할** 것이 하나 있다(K3-07 → P2SAF-12).

| 1차 항목 | 재확인 결과 |
|---|---|
| **K3-07** `cancel_unpaid_hold` docstring 이 "단일 여정만"이라 반대로 서술 | **1차가 옳다.** 빌더(`mutation_payloads.py:1230-1249`)는 `legs < 1` 만 거부하고 `txtJrnyCnt` 를 에코하므로 환승 홀드도 해제된다. **그러나 1차가 놓친 부분이 있다** — 같은 오류가 `reserve_transfer` docstring(`client.py:1731-1733`)에도 있고, 거기서는 "환승 홀드는 해제 불가"라고 운영자에게 **작업 지침으로** 전달되어 고아 PNR을 유발한다. 심각도 low → **medium** 으로 재평가. → P2SAF-12 |
| K5-02 `hidRsvChgNo` 미마스킹 | **확인** — `mutation_payloads.py:1398` 이 넣고 `redaction.py` 에 없음. 같은 결함류가 2건 더 있음(P2SAF-01/02) |
| K8-06 DynaPath 403 경로 제한 | **확인** — `BaseDaoHelper.java:59-90` 에 경로/상태코드 조건 없음. → P2SAF-11 |
| K6-02/K6-03 `build_refund_form` 고정값 | 폼 자체는 재확인하지 않음(1차 슬라이스). 다만 `refund` 가 원시 envelope만 돌려준다는 구조 문제는 P2SAF-10으로 별도 기록 |
| K6-06 `stl_mns_cd` 미파싱 | **확인, 단 독립 결함이 아님** — `refund` 가 응답 모델 없이 `BaseKorailResponse` 를 돌려주기 때문에 생기는 증상. → P2SAF-10 |
| K1-03 `EXCLUDED_API_DOMAINS` 의 `"reservation"` 라벨 drift | **확인** — `safety.py:41-52` 는 `reservation`/`payment`/`refund` 를 여전히 제외 도메인으로 나열하는데 셋 다 구현되어 있다. 주석(`:37-40`)이 "이 세트는 documentary이고 아무것도 dispatch하지 않는다"고 스스로 무력화하므로 안전 영향은 없다. 1차 판단(low/doc-drift)에 동의 |
| K7-01 `mileage.acpnMlgSpec.do` 누락 | 검증 범위 밖(도메인 슬라이스). 이견 없음 |

## 5. 의도된 제외 재확인 (결함 아님)

- 정기권(통근패스) 구매 — `safety.py:264-272` 에 제거 사유와 함께 기록. `KORAIL_MUTATION_ROUTES`
  에 `pass.passReserve` / `passPayIssue` 없음을 재계산으로 확인.
- 단체예약 — 라우트 없음.
- 포인트/마일리지 쓰기, 회원탈퇴, 체크인, push-sms(`push.callCrew.do`) —
  `EXCLUDED_API_DOMAINS`(`safety.py:41-52`). `PushService.java` 를 직접 열어
  `callCrew.do`(실제 승무원 호출)와 `crwCallRq.do`(목록 조회)가 다른 엔드포인트임을 확인했고,
  라이브러리가 등재한 것은 조회 쪽뿐이다 — **분류 정확**.
- `dry_run` 기본 True, consent 기본 전부 False, 카드 마스킹 — 설계.

## 6. 확인하지 못한 것

- 실서버 동작 일체(라이브 호출 없음).
- smali 대조는 상수·오버로드 확인에 필요한 범위에서만 수행했다. 이 렌즈의 발견은 대부분
  라이브러리 측 세트/게이트 계산이라 jadx의 제어흐름 왜곡에 영향받지 않는다.
  단 P2SAF-04의 `w4/a.java:100-101` 과 P2SAF-01의 `NCardReservationDao.java:67,71,123` 은
  jadx만으로 읽었다(단순 `put(상수 + 인덱스, 값)` 이라 왜곡 여지가 낮다고 판단).
- `custMgNo_N`/`apdCustName_N`/`apdCustTeln_N` 를 실제로 채우는 v6.5.0 호출부는 찾지 못했다
  (라이브러리도 같은 사실을 기록). 따라서 P2SAF-01은 "라이브러리가 만들 수 있는 프리뷰"의
  결함이며, 앱이 그 경로를 쓰는지는 별개다. 프리뷰는 앱 호출부와 무관하게 생성되므로
  결함 성립에는 영향이 없다.
