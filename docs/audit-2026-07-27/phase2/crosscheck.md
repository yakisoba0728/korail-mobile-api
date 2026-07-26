# Phase 2 — 교차검증 렌즈 (2차 독립 재확인)

감사자: Phase-2 (교차검증 렌즈) · 대상: `/Users/yakisoba/Documents/GitHub/korail-mobile-api`
방법: 1차 8건 보고서를 읽되 신뢰하지 않고, **문서(README/docs/CHANGELOG) ↔ 테스트 ↔ 라이브러리 코드 ↔ 앱(jadx+smali)**
네 축을 기계적으로 대조. 저장소는 읽기 전용으로만 접근했다(수정/생성 0건, git 조작 0건).
산출물은 이 파일 하나뿐이며 저장소 밖에 있다.

---

## 0. 먼저: 전수 카운트를 독립적으로 재산정했다

1차 8명의 "추출 개수" 합은 174였는데, 이는 각자 자기 슬라이스에서 **하나의 Retrofit 메서드를
여러 행으로 쪼갠**(login 3행, ReservationList 2행 등) 결과다. 앱의 실제 Retrofit 표면을
직접 세면 다음과 같다.

```
$ for f in analysis/jadx/sources/com/korail/talk/network/dao/*/*.java;
    do grep -cE '^\s*@(GET|POST)\(' "$f"; done | 합계
→ 35개 인터페이스(34개 *Service* + cashReceipt/CashReceipt.java) 합계 165개
```

- **앱 Retrofit 메서드 전수 = 165** (`docs/api-endpoints.md:7`의 "165 across 35 annotated
  interfaces"와 일치, 서비스별 소계도 `docs/api-status-by-service.md:92-126` 표와 35/35 전부 일치).
  → **이 두 문서의 수치는 정확하다**(1차가 검증하지 않은 부분, 이번에 확인).
- 고유 HTTP+path 쌍 = **159** (`docs/api-endpoints.md:7`).
- **라이브러리가 실제로 도달 가능한 경로 = 66** (`KORAIL_READ_ONLY_ROUTES` 58 + `KORAIL_MUTATION_ROUTES` 8).
  66개 전부가 159개 앱 경로 집합의 부분집합임을 스크립트로 확인했다(고아 경로 0건).
- `KorailClient` 공개 메서드 = **74** (`inspect` 실측), `tests/test_public_contract.py:25-108`의
  핀 집합과 정확히 일치.

즉 구현 커버리지는 **66/159 경로 (41.5%)**. 이 숫자는 어떤 문서에도 없다.

전체 테스트: `pytest -q -m "not live"` → **2228 passed, 1 deselected** (초록불 상태에서 감사).

---

## 1. 1차가 못 본 것 (신규)

### P2CRO-01 — [high] `PaidTicket.sale_date`는 "원표 판매일"이 아니라 "현재 판매일"이다. 모델 주석과 docstring이 반대로 안내한다

앱은 환불 폼의 `h_orgtk_sale_dt`에 **`TicketDetailResponse.h_sale_dt`**(현재 승차권의 판매일)를 넣는다.
두 개의 독립 호출부에서 동일하다:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:412-413`
  → `r5.setH_orgtk_sale_dt(r3.getH_sale_dt())` (r3 = `TicketDetailDao$TicketDetailResponse`)
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:965`
  → `refundRequest.setH_orgtk_sale_dt(ticketDetailResponse.getH_sale_dt());`

반면 **같은 도메인의 읽기 3종은 전혀 다른 값**을 쓴다:

- 수수료 조회 `refunds.CommissionView` → `h_orgtk_ret_sale_dt` ← `TrainInfo.getH_orgtk_ret_sale_dt()`
  (`TicketListActivity.java:899,904`)
- 상세 조회 `refunds.SelTicketInfo` → `h_orgtk_ret_sale_dt` ← 동일 (`TicketListActivity.java:917,922`)
- 영수증 `receipt.ReceiptInfo` → 필드명은 `h_orgtk_sale_dt`지만 값은
  `getH_orgtk_ret_sale_dt()` (`TicketReceiptActivity.java:402`)

라이브러리:
- `src/korail_mobile_api/mutation_models.py:337` — `sale_date: str = field(repr=False)  # h_orgtk_sale_dt`
- `mutation_models.py:319-321` — docstring "the PNR plus the **original-ticket** sale window/date/sequence
  and return password ... These come from a settled ticket (e.g. a ticket-list row, or
  `get_refund_ticket_detail()`)"
- `read_payloads.py:1620-1622` — `build_refund_commission_form` docstring이
  "the sale-date field is `h_orgtk_ret_sale_dt` here, NOT the `h_orgtk_sale_dt` the receipt read uses —
  **the two routes spell the same value differently**"라고 단언

그 단언은 영수증↔수수료 두 경로에 대해서는 **참**이지만, 세 번째 경로인 **환불에서는 거짓**이다.
환불만 같은 철자(`h_orgtk_sale_dt`)로 **다른 값**(`h_sale_dt`)을 보낸다.

`read_parsers.py:2679-2698`은 두 값을 모두 노출한다(`sale_date`←`h_sale_dt` `:2681`,
`original_sale_date`←`h_orgtk_ret_sale_dt` `:2684`). 그런데 `PaidTicket`의 docstring이 "original-ticket sale
date"라고 하고 필드 주석이 `# h_orgtk_sale_dt`라고 하니, 호출자는 자연스럽게
`detail.original_sale_date`(=`h_orgtk_ret_sale_dt`) 또는 수수료 조회에 쓴
`OriginalTicketReference.sale_date`를 그대로 재사용한다. **변경/재발권 이력이 있는 승차권에서
두 값은 다르고, 그 경우 환불이 잘못된 4분할 식별자로 나간다.**

미변경 승차권에서는 두 값이 일치하므로 조용히 통과하고, `refund()`는 실서버 성공 봉투가 없는
(`docs/verification-record.md:53`) 금전 경로다 — 정확히 "언젠가 조용히 실패할" 형태.

- 앱 근거: `ticketReturn/a.java:412-413`, `TicketListActivity.java:965`(환불) vs
  `TicketListActivity.java:899,917`, `TicketReceiptActivity.java:402`(읽기 3종)
- 라이브러리 근거: `mutation_models.py:319-321,337`, `read_payloads.py:1620-1622`,
  `read_parsers.py:2679-2698`, `mutation_payloads.py:1450`
- 수정: `PaidTicket.sale_date` 주석/독스트링을 "`h_sale_dt`(현재 판매일), `original_sale_date`가
  **아님**"으로 정정하고, `RefundTicketDetailResponse` → `PaidTicket` 변환 헬퍼를 제공.
  `build_refund_commission_form`의 "same value" 문장도 정정.

### P2CRO-02 — [medium] `TrainSearchMetadata`가 APK 어디에도 없는 wire key 4개를 읽고, 픽스처가 그것을 SYNTHETIC 값으로 못 박아 테스트가 아무것도 검증하지 않는다

`parse_train_search_metadata`(`parsers.py:257-276`)가 `seatMovie.ScheduleView` 응답에서 읽는 키 중
다음 4개는 **jadx + apktool smali + res + assets 전체에서 0건**이다:

```
$ grep -rIl "strJobId"        analysis/  → 0 files
$ grep -rIl "h_seat_cnt_first"  analysis/ → 0 files
$ grep -rIl "h_seat_cnt_second" analysis/ → 0 files
$ grep -rIl "txtGoHour_first"   analysis/ → 0 files
```

앱의 `RsvInquiryResponse`(ScheduleView 응답 DTO) 최상위 필드는 정확히 9개다
(`analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:9-17`):
`h_ectb_trn_no_next, h_gd_no, h_next_pg_flg, h_notice_msg, h_prcd_trn_no_next, h_qry_st_no_next,
h_rslt_cnt, h_trn_no_next, trn_infos`.

라이브러리는 이 중 8개를 읽고 **`h_notice_msg`만 빠뜨린 채**, 존재하지 않는 4개를 추가로 읽는다
(`models.py:584,599,600,601`의 `job_id / first_seat_count / second_seat_count / first_departure_time`).

**왜 이것이 "지금까지 아무도 못 본" 상태로 남았는가**: `tests/fixtures/raw_typed_train_search.json`이
네 키를 전부 `"SYNTHETIC-JOB-ID"` 같은 값으로 넣어두고,
`tests/test_raw_typed_core.py:639-660`이 `assert metadata.job_id == "SYNTHETIC-JOB-ID"`로 단언한다.
이 테스트는 "파서가 자기가 읽도록 쓰인 키를 읽는다"만 증명한다 — 앱/서버 근거는 0이다.
같은 함수의 바로 위 주석(`models.py:580-583`, `test_raw_typed_core.py:648-649`)은
`h_menu_id`에 대해 "zero hits across the whole decompiled app"이라는 기준을 명시적으로 적용해
필드를 **뺐는데**, 같은 기준을 이 4개에는 적용하지 않았다.

1차 K2(TSF-02)는 `actualTrainSchedule.do`에서 같은 패턴을 찾았지만,
**핵심 live-verified 읽기인 열차검색(ScheduleView)에서는 놓쳤다**. 1차 K8은 이 엔드포인트를
"필드·기본값·순서까지 상세 일치"로 판정했다(요청만 봤고 응답 메타데이터는 안 봄).

- 앱 근거: `network/response/seatMovie/RsvInquiryResponse.java:9-17`; 위 grep 4건 0 hit
- 라이브러리 근거: `parsers.py:259,271,272,273`, `models.py:584,599-601`
- 픽스처/테스트 근거: `tests/fixtures/raw_typed_train_search.json`, `tests/test_raw_typed_core.py:639-660`
- 수정: 4개 필드에 "APK 미확인(unevidenced)" 주석을 달거나 제거하고 `raw`로만 접근시킬 것.
  `h_notice_msg`는 반대로 추가할 것(§P2CRO-03).

### P2CRO-03 — [low] 열차검색 응답이 실제로 선언하는 `h_notice_msg`를 라이브러리만 안 읽는다

`RsvInquiryResponse.h_notice_msg`(`network/response/seatMovie/RsvInquiryResponse.java:12`)는 앱이 선언한 최상위 필드인데
`parse_train_search_metadata`가 읽지 않는다. 흥미롭게도 **같은 라이브러리의 다른 두 파서는 읽는다**
(`read_parsers.py:2505`의 특가상품 열차조회, `limousine_parsers.py:390`의 리무진 조회) —
셋 다 동일한 `RsvInquiryResponse` 계열을 파싱하므로 이건 스타일이 아니라 누락이다.
`raw`에는 남으므로 데이터 유실은 없다.

- 앱 근거: `network/response/seatMovie/RsvInquiryResponse.java:12`
- 라이브러리 근거: `parsers.py:257-276`(부재) vs `read_parsers.py:2505`, `limousine_parsers.py:390`(존재)

### P2CRO-04 — [medium] `extend_discount_card` dry-run 미리보기에서 N카드 자격증명 4분할 중 `saleDd`만 평문으로 남는다

`build_discount_card_extension_query`(`mutation_payloads.py:1583-1631`)는 docstring이
스스로 "the card ticket's **four-part credential**"이라 부르는 값 4개를 보낸다:
`saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`.
`redaction.SENSITIVE_KEYS`에는 `tkRetPwd`(`redaction.py:25`), `saleWctNo`(`:26`), `saleSqno`(`:28`)가 있으나
**`saleDd`는 없다**(같은 값의 다른 철자인 `sale_date`(`:71`), `h_orgtk_sale_dt`(`:126`)는 등재되어 있다).

실측 재현:

```
form:    {'Device':'AD','Version':'250601003','Key':'korail1234567890',
          'saleWctNo':'WCT1','saleDd':'20260810','saleSqno':'SEQ1','tkRetPwd':'PWD1'}
preview: {... 'saleWctNo':'[REDACTED]','saleDd':'20260810',
          'saleSqno':'[REDACTED]','tkRetPwd':'[REDACTED]'}
```

`SENSITIVE_KEYS`는 정확 일치 매칭이므로 wire 철자 하나만 빠져도 구멍이 된다.
**그리고 이 값은 무해한 날짜가 아니다**: `TicketReceiptActivity.java:431`의
`H4.a.getReturnNumberWithDash(h_orgtk_wct_no, h_orgtk_ret_sale_dt, h_orgtk_sale_sqno, h_orgtk_ret_pwd)`가
보여주듯 이 네 값이 곧 인쇄된 **반환번호**이고, `TicketListActivity.java:1070`이
`setSaleDd(trainInfo.getH_orgtk_ret_sale_dt())`로 그 두 번째 조각을 `saleDd`에 넣는다.
즉 미리보기에 남는 것은 bearer 자격증명의 1/4 조각이다.
이는 1차 K5-02(`hidRsvChgNo`)와 **완전히 같은 결함류의 두 번째 사례**이며, 1차 어느 슬라이스도
찾지 못했다(K7 담당은 `dcntCrdExtn.do`를 "있음"으로만 처리, K5는 결제 폼만 대조).
`tests/test_discount_card_mutations.py:267-271`의 미리보기 테스트는 `SYNTHETIC_PWD`만 확인해
이 구멍을 그대로 통과시킨다.

- 앱 근거: `ResearchService.java:65-66`(7개 `@Query`), `TicketListActivity.java:1067-1072`
- 라이브러리 근거: `mutation_payloads.py:1618`(`saleDd`), `redaction.py:13-230`(`saleDd` 부재),
  `consent.py:130-131`(`redact_payload` 경유만 마스킹), `tests/test_discount_card_mutations.py:267-271`
- 수정: `SENSITIVE_KEYS`에 `"saleDd"` 추가 + 미리보기 테스트에 판매일 단언 추가.

### P2CRO-05 — [medium] `get_maas_menu_list()`가 앱의 3개 변형 중 1개만 재현 가능하다 (PNR/승차권 스코프 조회 도달 불가)

앱의 `copt.gdMenuLt.do`는 `@Field("Device"), ("Version"), ("pnrNo"), ("tkRetNo") List, ("addSrvReqNo")`
5필드다(`CommonService.java:46-48`). 실제 호출부는 **3가지**:

1. 무필터 — `MainBookingActivity.java:737-740` (`new BaseRequest()`)
2. `addSrvReqNo` — `MaasAddReservationActivity.java:69-74`
3. `pnrNo` + `tkRetNo[]` — `AdditionalServiceActivity.java:157-166`

라이브러리 `KORAIL_EXACT_REQUEST_FIELDS['/classes/com.korail.mobile.copt.gdMenuLt.do']`는
`frozenset({'Device','Version'})`뿐이고, `client.get_maas_menu_list()`(`client.py:1232-1245`)도
파라미터를 받지 않는다. 즉 **"이 PNR/승차권에 붙일 수 있는 MAAS 부가서비스 메뉴"** 조회
(앱에서 가장 실용적인 변형)는 저수준 API로도 불가능하다 — `assert_read_only_request_fields`가
막는다.

1차 K8은 이 엔드포인트를 표에서 그냥 "있음"으로 처리했다.

- 앱 근거: `CommonService.java:46-48`; `MainBookingActivity.java:737-740`;
  `MaasAddReservationActivity.java:69-74`; `AdditionalServiceActivity.java:157-166`
- 라이브러리 근거: `safety.py` `KORAIL_EXACT_REQUEST_FIELDS`(2필드), `client.py:1232-1245`

### P2CRO-06 — [medium] 테스트가 **틀린 수치를 강제**한다 — `tests/test_readme.py:219`가 stale "72 public methods"를 요구

```python
# tests/test_readme.py:216-221
progress = PROGRESS.read_text(encoding="utf-8")
assert "58 exact login/read routes" in progress
assert "72 public methods" in progress          # ← 실제는 74
assert "- Live-successful inventory entries: 32" in progress
assert "75" in progress                          # ← 사실상 아무것도 검사하지 않음
```

실제 `KorailClient` 공개 메서드는 **74**개(`inspect` 실측, `tests/test_public_contract.py:25-108`의
핀도 74개). README(`:79`), `docs/api-status-by-service.md:18`, `docs/verification-record.md:21`,
`docs/IMPLEMENTATION_PROGRESS.md:148` 전부 74라고 쓴다. 그런데 같은
`IMPLEMENTATION_PROGRESS.md`가 **:312**("The **current** package boundary is 58 exact routes and
72 public methods")와 **:757**("The **current** implementation evidence establishes 58 routes ...
and 72 public methods")에서 72라고 쓰고, **테스트가 그 stale 문장을 존재 필수 조건으로 못 박는다.**
누가 문서를 74로 고치면 테스트가 깨진다.

이 저장소는 과거 "72 public methods 핀이 과거 수치 문장에 걸려 무력화된" 전력이 있는데,
지금은 그보다 나쁜 상태다 — 핀이 **틀린 값을 지키고 있다**.

같은 함수의 `assert "75" in progress`는 문서 어디에나 있는 두 글자라 아무 의미가 없고,
`tests/test_readme.py:78`의 `assert "two" in text`도 동일하다.

- 라이브러리/문서 근거: `tests/test_readme.py:216-221,78`;
  `docs/IMPLEMENTATION_PROGRESS.md:148`(74) vs `:312,:757`(72); README.md:79(74)
- 앱 근거: 없음(문서·테스트 내부 문제)

### P2CRO-07 — [low] "현재 인벤토리"를 주장하는 두 문서가 서로 다른 숫자를 말하고, 핀은 하나만 걸려 있다

- `docs/api-status-by-service.md:11-15` → 성공 32 / 실패 **13** / 미실행 **120** / 전체 165
  (`tests/test_readme.py:88-91`이 이 네 줄을 정확히 핀)
- `docs/IMPLEMENTATION_PROGRESS.md:311` → "**current** inventory is 32 successful, **10** failed,
  and **123** unexecuted" (핀 없음)

둘 다 합이 165라 자체 모순은 없지만 서로 모순이며, 어느 쪽이 진짜 "현재"인지 문서만으로는
판정 불가다. 핀이 한쪽에만 걸려 있어 드리프트가 CI에 보이지 않는다.

### P2CRO-08 — [low] `RELEASE_GAP_PLAN.md`의 읽기 갭 표 G1–G12 중 **4개**가 이미 닫혔다 (1차는 2개만 발견)

스크립트로 G1–G12 + 부가 목록을 `KORAIL_READ_ONLY_ROUTES ∪ KORAIL_MUTATION_ROUTES`와 대조:

| 행 | 경로 | 문서 상태 | 실측 |
|---|---|---|---|
| G2 | `research.dcntCrdScheduleView.do` | "not ported" | **구현됨** (1차 TSF-06가 발견) |
| G3 | `ticket.dcntCrdUseQry.do` | "Not ported" | **구현됨** (1차 TSF-06가 발견) |
| G11 | `login.Logout` | "client.logout() only clears the local cookie jar ... server session never invalidated" | **구현됨** — `("GET", ".../login.Logout")`이 read-only 라우트에 등록, `session.py:252-268`이 실제 GET 발행 (**1차 미발견**) |
| G12 | `certification.ReservationList` (read overload) | "port the read overload only" | **구현됨** — 라우트 등록 + `KORAIL_EXACT_REQUEST_FIELDS`가 read 4필드 pin (**1차 미발견**) |
| 부가 | `xPoint.MyXPointView`, `mlg.amtSpec.do` | "excluded-domain reads" | **구현됨** (`safety.py:19-23` 주석은 이미 범위 축소를 반영, GAP_PLAN만 미갱신) |

G1/G4/G5/G6/G7/G8/G9/G10, `xPoint.XPointView`, `railplus.autoCharge.do`는 문서대로 실제 미구현임을 확인.

### P2CRO-09 — [low] `EXCLUDED_API_DOMAINS`가 실제로 구현된 3개 도메인을 "declined"로 기록한다 (1차 K1-03은 1개만 지적)

`safety.py:41-51`의 집합은 `"reservation"`, `"payment"`, `"refund"`를 포함하는데, 셋 다
`MUTATION_CATEGORIES`(`consent.py:33-40`)의 정식 카테고리이고 각각 라우트·클라이언트 메서드·
consent 게이트가 완비되어 있다(`client.py:1565,1898,2029`). 주석 자체가
"records which areas were **considered and declined**"라고 하므로 현재 구현 상태와 정면으로
모순된다. `"check-in"`, `"member-drop"`, `"push-sms"`, `"points-mileage-write"`,
`"dynapath-token-generation"`은 실제로 제외 상태가 맞다. 주석이 "nothing dispatches on it"이라
기능 영향은 없다.

### P2CRO-10 — [info] NetFunnel: 1차 K8이 "재검증 생략"한 영역을 독립 확인 — 결함 없음

1차 K8은 `netfunnel.py`(934행)를 "기존 감사에서 라이브 확증됨"이라며 opcode 상수만 대조하고
로직 재검증을 생략했다. 이번에 직접 확인했다:

- opcode 6종(`T6/c.java:5-11`)과 `KorailNetFunnelOpcode` 일치.
- 액션 8종(`K4/g.java:43-51`, smali `K4/g.smali:77-93`으로 값 재확인)과
  `constants.py:356-393` 일치. 성수기 분기(`MainBookingActivity.java:749`
  `isPeakSeason ? act_8_2 : act_8`)도 `inquiry_action()`이 정확히 재현.
- **5003 `AliveNotice` 미구현은 결함이 아니다**: `T6/g.java:145,181,313`의 ALIVE 경로는
  `g.ALIVE()` 정적 진입점을 통해서만 도달하는데, `com/korail/**` 전체에서 `ALIVE()` 호출부가
  **0건**이다(호출되는 것은 `BEGIN`/`BEGIN1`/`END`뿐 —
  `DirectInquiryActivity.java:442,469,499`, `MainBookingActivity.java:759`,
  `ReservedTicketActivity.java:553`, `NetfunnelDao.java:40`). 앱과 일치.
- 노드 리다이렉션(`T6/d.java:17-19` `makeURL`) 재현 여부도 확인 — `netfunnel.py:683-712`가
  `token.node`로 5002/5004를 보낸다. 일치.
- `act_22`(환불)가 어디서도 안 쓰인다는 주석도 확인 — 환불 경로에 큐 게이트 없음. 일치.

### P2CRO-11 — [info] 45개 `KORAIL_EXACT_REQUEST_FIELDS` 핀 전수를 앱 Retrofit 애너테이션과 기계 대조 — 불일치 0건

smali에서 문자열 상수 맵(146개 클래스)을 추출해 `@Field(OJrny.RUN_DT)` 같은 **상수 참조까지
해석**한 뒤, 45개 핀 전부를 앱 시그니처와 양방향 대조했다.

- 핀에는 있으나 앱에 없는 필드: **0건**
  (1차 통과 후 남은 8건은 전부 상수 참조 미해석이었고, `C1262b.{DPT_DT,DPT_TM,ARV_RS_STN_CD,TRAIN_NO}`
  = `dptDt/dptTm/arvRsStnCd/txtGoTrnNo`로 확인되어 전부 정확히 일치. `trn.prcFare.do`의 8개는
  `@FieldMap` 경유.)
- 앱에는 있으나 핀에 없는 필드: 6경로 — 전부 근거 있음
  (`txtPsgDisc0019Cnt`=write 오버로드 의도적 차단, `sidTest`=앱 디버그 필드,
  `qryNumNext/fllwQryFlg/trnOprBzDvCd`=앱 자신도 안 채움, `trnCnt`=앱 자체 자기대입 버그,
  `pnrNo/tkRetNo/addSrvReqNo`=**P2CRO-05로 별도 보고**).

즉 요청 필드 표면은 매우 견고하다. 결함은 요청이 아니라 **응답 파서(§P2CRO-02/03)와
레드액션(§P2CRO-04)** 쪽에 몰려 있다.

---

## 2. 1차를 교차확인한 것 (동의 / 근거 보강)

### P2CRO-12 — [high] 환불 폼 3개 값 하드코딩 — 1차 K6-02/K6-03에 **동의**, 앱 근거 보강

`build_refund_form`(`mutation_payloads.py:1446-1461`)이 `tk_ret_tms_dv_cd="21"`, `h_mlg_stl="N"`,
`pbpAcepTgtFlg="N"`을 무조건 보낸다. 앱은 셋 다 **서버 응답에서 받아 그대로 되보낸다**
(`ticketReturn/a.java:420,427-428,430-431`, jadx가 바이트코드로 덤프한 구간을 직접 읽음):

```
r5.setH_mlg_stl(r9)                                  # r9 = J0(String) 인자, "Y"/"N" 분기
... getTk_ret_tms_dv_cd() → r5.setTk_ret_tms_dv_cd(r9)   # CommissionView 응답에서
r3.getH_pbp_acep_tgt_flg() → r5.setPbpAcepTgtFlg(r9)     # SelTicketInfo 응답에서
```

`I4/a.java:5-6`이 `AFTER_DEPARTURE="15"`, `BEFORE_DEPARTURE="21"`(직접 확인). `h_mlg_stl="Y"` 분기는
`ticketReturn/a.java:185-190`(`prg_psb_flg=="M" && use_psb_mlg_num >= 수수료`)에서 결정된다.
라이브러리는 `get_refund_commission()`이 세 값 중 둘을 이미 파싱해두고도
(`read_models.py:1183-1204`) 전송에서 버린다. `h_pbp_acep_tgt_flg`는 아예 파싱조차 안 한다
(`read_parsers.py:2679-2698`). **1차 판정 유지, 심각도 high 유지.**

### P2CRO-13 — [medium] `hidRsvChgNo` 미마스킹 — 1차 K5-02에 **동의**, 재현 확인

`redaction.SENSITIVE_KEYS`에 `h_rsv_chg_no`와 `reservation_change_no`는 있으나
wire 철자 `hidRsvChgNo`가 없어 결제 dry-run 미리보기에 평문으로 남는다
(`mutation_payloads.py:1398`, `redaction.py:13-230`). `tests/test_real_card_payment.py`의
`_hold()` 픽스처가 `journeys=()`라 항상 상수 `"000"`이 되어 결함을 은폐한다는 1차 지적도 확인.
§P2CRO-04(`saleDd`)와 함께 **"형제 필드 중 하나만 wire 철자가 빠지는" 동일 결함류가 2건**이므로,
개별 키 추가가 아니라 *뮤테이션 빌더가 방출하는 전 키 집합 ↔ SENSITIVE_KEYS 차집합*을 검사하는
테스트를 추가하는 편이 옳다(이번 감사에서 그 차집합 스크립트로 두 건을 다 잡았다).

### P2CRO-14 — [low] 할부 일시불 기본값 `"00"` vs 앱 `"0"` — 1차 K5-03에 **동의**, smali 재확인

`analysis/apktool/smali/K4/h.smali:44-52`에서 `INS_0("일시불", const-string v2, "0")` 직접 확인
(jadx `K4/h.java:7`과 일치). `CreditCardData.getInstallmentType()`이 이 코드를 그대로
`hidIsmtMnthNum1`로 전송(`V4/a.java:31`). 라이브러리는 `mutation_models.py:311`에서 `"00"`.
서버가 정수 파싱하면 무해하지만 "앱과 바이트 단위 일치"를 표방하는 설계에는 어긋난다.

### P2CRO-15 — [medium] `actualTrainSchedule.do` 응답 22필드 무근거 — 1차 K2(TSF-02)에 **동의**, 기계적으로 재확인

`parsers.py`의 wire key 중 APK 전체(jadx+smali)에서 0건인 것을 자동 추출한 결과, 1차가 손으로
찾은 목록과 정확히 일치했다: `stopRsStnCd`(:592), `stnConsOrdr`(:603), `dlayFareRetDvCd`(:658),
`dlayFareRetDvCdNm`(:663), `dlaySoloOprFlg`(:668), `dturDrvDlayTnum`(:673),
`dlayStnConsOrdr`(:711), `msgCd`(:713), `orgRsStnCd`(:716), `orgRsStnNm`(:717), `routNm`(:719),
`saleRgulFlg`(:727), `tmnRsStnCd`(:729), `tmnRsStnNm`(:730), `trnAttCd`(:731), `upDnDvCd`(:740).
동일 스캔이 §P2CRO-02의 4건을 추가로 잡아냈다 — **같은 결함류가 두 파서에 걸쳐 있다.**

---

## 3. 1차가 틀리게 본 것

이번 감사에서 **1차 판정을 뒤집을 만한 오판은 발견하지 못했다.** 다만 다음 두 가지는
"과소평가"로 분류한다.

1. **K1-03 (`EXCLUDED_API_DOMAINS` 드리프트)** — 1차는 `"reservation"` 한 항목만 지적했으나
   실제로는 `"payment"`, `"refund"`도 같은 문제다(§P2CRO-09).
2. **TSF-06 (`RELEASE_GAP_PLAN` 드리프트)** — 1차는 G2/G3 두 건이라고 명시했으나
   실제로는 G11/G12까지 4건 + 부가목록 2건이다(§P2CRO-08). 1차 K2는 "G4/G5/G9는 문서와 실측이
   일치함을 확인했으므로 이 드리프트는 G2/G3 두 항목에 국한된다"고 **범위를 단정**했는데,
   자기 슬라이스 밖의 G11/G12를 확인하지 않고 내린 결론이었다.

또한 1차 K5가 `hidTmpJobSqno1/2`의 `"000000"` 폴백을 "✅ 문서화된 한계"로 통과시킨 반면, 같은
"필드 부재 vs 빈/기본값" 문제를 1차 K1은 K1-02(간편로그인)에서 결함으로 보고했다 — 두 슬라이스가
같은 현상에 다른 잣대를 썼다. 이번 감사의 판단으로는 `hidTmpJobSqno`는 `mutation_payloads.py:1276-1283`이
근거와 함께 이유를 적어두었고 앱도 hold 응답을 그대로 에코하므로 폴백이 발동할 실제 조건이
관측된 바 없어 **K5 쪽 판단(결함 아님)이 타당**하다. 별도 finding으로 올리지 않는다.

---

## 4. 확인했으나 문제없음 (오탐 방지 기록)

- **환불 폼의 `h_orgtk_sale_wct_no` 철자.** 앱 DTO 세터는 `setH_orgtk_wct_no`인데 Retrofit
  `@Field`는 `h_orgtk_sale_wct_no`다(`RefundService.java:27-29`, smali
  `RefundService.smali:222`로 재확인). 라이브러리가 애너테이션 쪽을 쓰고 있어 **정확**하다.
  DTO 필드명만 보면 오판하기 쉬운 함정인데 통과했다.
- **환불 폼의 `latitude`/`longitude` 빈 문자열.** 앱도 `Location`이 null이면 `""`를 보낸다
  (`ticketReturn/a.java:384-396`, `L40:` 분기가 두 값을 `""`로 둔다). 앱이 도달 가능한 shape이므로 결함 아님.
- **`redact_payload`의 리스트 처리.** `certification.PriceReCalculation`의 6개 반복키가
  리스트로 나가는데 원소 단위로 마스킹된다(`redaction.py:318-347`, 실측 확인). 결함 아님.
- **`build_price_recalculation_form`의 필드 순서와 비회원 분기.** `a6/C1042B.java:264-297`
  (`k2()`)와 1:1 대조 — 6개 리스트 순서, `txtJobId="1101"`, `isNonMember()` 시에만
  `hiduserYn="N"`+`hidCustNo`. **완전 일치.**
- **`certification.TicketReservation` 오버로드 2종.** 회원 경로는 `pbepInfo`를 포함하지만
  (`CertificationService.java:52-54`, `ReservationDao.java:17`), `pbepInfo`는 세종시
  공무원 인증 완료 시에만 채워진다(`DirectInquiryActivity.java:416`). 일반 회원은 null →
  Retrofit이 드롭. 라이브러리 미전송은 **정확**.
- **결제 폼의 `hiduserYn="Y"` 고정 / `hidMbCrdNo` 미전송.** `B6/AbstractC1269e.java:405-411`
  (`k1()`)가 `isNonMember()`일 때만 `"N"`+`hidMbCrdNo`. 회원 전용 라이브러리에서는 정확.
- **`mutation_payloads.py`의 인덱스 접미사 키**(`hidStlMnsCd1`, `txtCardNo_1`, `arvTm_1`,
  `txtPsrmClCd2` 등)가 APK 문자열 검색에 안 잡히는 것은 앱이 런타임에
  `setHidStlMnsCd(1, ...)`로 조립하기 때문 — 정상.
- **로그인 상수** `Device="AD"/Version="250601003"/Key="korail1234567890"`,
  로그인 성공코드 `{IRZ000001, S200}`, 로그인 타입 `2/4/5` — 1차 K1 검증 결과를 재확인.

---

## 5. 종합

- 앱 Retrofit 표면 **165**개(고유 경로 159), 라이브러리 도달 가능 **66**경로 (41.5%).
- **critical 없음.** 안전게이트(consent 2중, dry_run 기본, 카드 배타검증, 라우트↔카테고리
  교차검사, mutation 전용 송신경로)에 우회 구멍은 이번에도 찾지 못했다.
- 가장 위험한 것은 **금전 경로의 조용한 의미 불일치** 2건(P2CRO-01 환불 판매일,
  P2CRO-12 환불 3필드 하드코딩)이며 둘 다 `refund()`에 몰려 있다 — 실서버 성공 봉투가
  없는 유일한 금전 경로다.
- 이 프로젝트의 구조적 약점은 **"합성 픽스처 + 자기확인 테스트"**다. P2CRO-02가 그
  전형이고, P2CRO-06(테스트가 stale 수치를 강제)이 그 극단이다. 요청 필드 표면은
  기계 대조에서 완전무결(P2CRO-11)이었던 반면 응답 파서·레드액션·문서 수치는 반복적으로
  드리프트한다 — **핀이 걸려 있는 곳은 정확하고, 안 걸린 곳은 예외 없이 어긋나 있다.**
  권고: (a) 뮤테이션 빌더 방출 키 ↔ `SENSITIVE_KEYS` 차집합 테스트,
  (b) 파서 wire key ↔ APK grep 0건 검사(CI에 넣기 어렵다면 주석 규약),
  (c) `"72 public methods"` 같은 수치 단언은 문서 문자열이 아니라 `inspect`로 세어 비교.
