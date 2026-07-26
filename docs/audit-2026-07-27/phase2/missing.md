# 2차 검토 — 누락 렌즈 (Phase 2 / missing)

대상: `/Users/yakisoba/Documents/GitHub/korail-mobile-api`
렌즈: **앱에는 있는데 라이브러리에 아예 없는 기능/엔드포인트/파라미터**
방법: 1차 8개 보고서를 읽되 신뢰하지 않고, 앱 API 표면을 **독립 재추출**해서 라이브러리와 대조.

---

## 0. 독립 재추출 결과 (숫자의 출처)

앱 표면은 jadx 로 한 번, apktool smali 로 한 번, **서로 독립적으로** 뽑아 diff 했다.

| 산출 | 값 | 근거 |
|---|---|---|
| Retrofit 어노테이션 메서드 선언 (jadx) | **165** | `analysis/jadx/sources/com/korail/talk/network/dao/**/*Service.java` + `CashReceipt.java` + `AddService.java` 의 `@POST/@GET` 개수 |
| Retrofit 어노테이션 메서드 선언 (smali) | **165** | `analysis/apktool/smali*/com/korail/**` 의 `.annotation runtime Lretrofit/http/(POST\|GET);` |
| 유니크 경로 (jadx) | **159** | 위에서 경로만 유니크화 |
| 유니크 경로 (smali) | **159** | 동일 |
| jadx ↔ smali 경로 집합 | **완전 일치 (diff 무출력)** | 즉 jadx 가 뭉갠 엔드포인트는 없다 |
| 라이브러리가 실제로 전송 가능한 경로 | **66** (read 58 + mutation 8) | `safety.py:69` `KORAIL_READ_ONLY_ROUTES`, `safety.py:205` `KORAIL_MUTATION_ROUTES` |
| 앱에만 있는 경로 | **93** | 위 두 집합의 차집합 |

> **주의 — 1차/기존 문서가 쓰는 "구현" 판정 방식과 다르다.**
> `src/` 를 문자열 grep 하면 라이브러리 경로가 64개로 나오는데, 그건 docstring·주석에 적힌 경로까지 세는 값이라
> 틀리다. 반대로 `/file/CACHE/*.cache`, `/ebizcross/getUUID.do`, `/ebizmaas/EbizMaasStationList.do` 5개는
> `com.korail.mobile` 을 포함하지 않아 grep 에서 빠진다. **경계는 grep 이 아니라
> `safety.py` 의 두 frozenset 이다** — 거기 없으면 `assert_read_only_route`/`assert_mutation_route` 가
> 전송을 거부한다(`safety.py:1319-1352`). 이 보고서의 66 은 그 두 집합에서 뽑은 값이다.

### 0.1 엔드포인트 수준에서 1차가 놓친 것은 **없다**

앱-only 93경로 각각에 대해 1차 8개 보고서 전문을 기계적으로 검색했다. 매칭 키는
**`com.korail.mobile.` 를 벗긴 전체 꼬리**(예: `addService.reserve.do`, `pass.passOtrReserve`)이고,
비-`/classes/` 경로 3개(`/ebizcross/getUUID.do` 등)는 전체 리터럴로 맞췄다. **짧은 메서드명 fallback은
쓰지 않았다** — `reserve`/`update`/`code` 같은 토막은 아무 보고서에나 걸려 커버리지를 부풀린다.
이 엄격 기준으로도 **미언급 0건**이다. 즉 "엔드포인트가 통째로 빠졌는데 아무도 못 봤다"는 사례는 없다.
1차의 8분할은 `network/dao/` 34개 하위 패키지를 빠짐없이 덮었다.

또한 `docs/api-status-by-service.md`(실측 기록, 165행)를 교차검사한 결과 **"라이브 프로브 성공했는데
라이브러리에 없는" 엔드포인트는 0건**이다(미구현 중 실측된 4건은 전부 `실패`:
`compensate.ticketList.do`, `delay.ticketList.do`, `gift.gdUseSpec.do`, `nFilter.createKey.do`).

**그래서 이 보고서의 무게는 엔드포인트가 아니라 "구현된 66경로 안쪽의 파라미터·변형 누락"에 있다.**
그 층은 1차가 슬라이스로 나눠 본 탓에 오히려 사각이 생겼다.

---

## 1. 1차가 놓친 것 (NEW)

### P2MIS-01 — 열차조회에 **승객 유형 조합**을 실을 수 없다 (missing, medium)

앱은 `seatMovie.ScheduleView` 에 승객을 **5개 버킷**으로 나눠 보낸다.
`u4/b.java:110-121, 173-177` 이 유일한 조립 지점이고, 매핑은 다음과 같다.

```
u4/b.java:173  txtPsgFlg_1 = ADULT_COUNT + TEENAGER_COUNT + GUIDE_DOG_COUNT   (어른/청소년/안내견)
u4/b.java:174  txtPsgFlg_2 = CHILD_COUNT + CHILD_ACCOMPANY_COUNT              (어린이/동반유아)
u4/b.java:175  txtPsgFlg_3 = SENIOR_COUNT                                     (경로)
u4/b.java:176  txtPsgFlg_4 = HIGH_DISABLE_COUNT                               (중증장애)
u4/b.java:177  txtPsgFlg_5 = LOW_DISABLE_COUNT                                (경증장애)
```

라이브러리는 `payloads.py:298-302` 에서

```python
"txtPsgFlg_1": str(query.passengers),
"txtPsgFlg_2": "0", "txtPsgFlg_3": "0", "txtPsgFlg_4": "0", "txtPsgFlg_5": "0",
```

로 **1번 버킷에 전부 몰아넣고 2~5를 상수 "0"** 으로 고정한다. 공개 질의 모델
`TrainSearchQuery`(`models.py:270-277`)에는 승객 유형 필드 자체가 없다(`passengers: int` 하나).

**왜 결함인가 — 라이브러리 자신이 이미 반대로 하고 있다.**
- 예약 쪽: `KorailPassengerCounts`(`mutation_models.py:11-48`)가 8종 승객
  (adult/teenager/child/infant/senior/severe_disability/mild_disability/guide_dog)을 완비하고
  `mutation_payloads.py:76-91 _PASSENGER_ROWS` 로 `txtCompaCnt{n}`/`txtPsgTpCd{n}`/`txtDiscKndCd{n}` 을 전송한다.
- 리무진 쪽: `limousine_payloads.py:144-148` 은 **같은 5개 버킷을 전부 파라미터로 노출**한다
  (`passenger_group_1_count`, `passenger_group_2_count`, `senior_count`,
  `severe_disability_count`, `mild_disability_count`). 이것이 유일한 정상 대조군 — 공개돼 있고
  파라미터화돼 있다.
- (참고, 대조군 아님) `read_payloads.py:1501-1522` 의 여행상품 변형도 5슬롯을 채우지만
  `adult→_1`, `child→_2` 로 단순 매핑해 앱의 합산 규칙(`adult+teenager+guide_dog`,
  `child+infant`)을 재현하지 못하고, 게다가 비공개 사문 코드다(§2 P2MIS-05).

즉 **일반 열차조회(txtMenuId="11")만** 이 능력이 없다. 결과적으로
"어른2+경로2"로 **예약은 할 수 있는데 그 조합의 잔여석/운임을 조회할 수단이 없다.**

**참고 — 잘못된 요청이 나가는 것은 아니다.** 현재 폼은 실서버에서 성공한다
(`docs/api-status-by-service.md:515` — `getRsvInquiry` 성공, "기존 safe search 10 rows").
이것은 오작동이 아니라 **표현할 수 없는 조합**의 문제다.

**기존 문서에 등재된 적 없음(확인함)**: `RELEASE_GAP_PLAN.md` 에 `TrainSearchQuery`/`search_trains`
언급 0건. `docs/deep-dive/impl-audit-reverify*.md` 의 관련 항목(RV2-03 등)은 전부
`TrainResearch`/`TResidualSeatsResearch` 의 **다른 필드**(`txtSeatAttCd`, 언더스코어 없음)에 대한 것이고,
`RELEASE_GAP_PLAN.md:101,599` 는 **예약 폼**의 `txtSeatAttCd4` 다. 조회 폼의 `_2/_3/_4` 와
`txtPsgFlg_2~5` 를 다룬 문서는 없다.

**왜 1차가 못 봤나 (경계 사각지대)** — `02-search.md:19-22` 가 `seatMovie/` 를
"내 담당 4개 디렉터리 밖 … **범위 외 — 미검증**"이라고 명시적으로 제외했고,
`08-core.md:76` 은 `SeatMovieService — 2/3 구현` 으로 **경로 존재 여부만** 세고 필드 대조는 하지 않았다.
정확히 두 슬라이스 사이로 빠졌다.

- 앱 근거: `analysis/jadx/sources/u4/b.java:110-121`, `:173-177`;
  `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12`
- 라이브러리 근거: `src/korail_mobile_api/payloads.py:298-302`,
  `src/korail_mobile_api/models.py:270-277`
- 수정 방향: `TrainSearchQuery` 에 5버킷(또는 `KorailPassengerCounts` 재사용 + `u4/b.java:173-177` 합산 규칙)을 추가.

---

### P2MIS-02 — 열차조회 **좌석 옵션 3종(방향/위치/속성)** 이 상수로 못박혀 있다 (missing, medium)

앱은 조회 화면에서 세 개의 좌석 옵션을 서버로 보낸다. 각 코드표는 enum 에 그대로 있다.

| 폼 필드 | 의미 | 앱이 보낼 수 있는 값 | 근거 |
|---|---|---|---|
| `txtSeatAttCd_2` | 좌석방향 | `000` 모든방향 / `009` 순방향 / `010` 역방향 | `K4/l.java:5-7` |
| `txtSeatAttCd_3` | 좌석위치 | `000` 모든위치 / `011` 1인석 / `012` 창측 / `013` 내측 | `K4/n.java:5-8` |
| `txtSeatAttCd_4` | 좌석속성 | `003` 자유석, `033` 입석, `051` 정기권좌석선택, `052` 대피도우미, `015` 일반석, `019` 유아동반, `021` 수동휠체어석, `028` 전동휠체어석, `018` 2층석, `032` 자전거, `020` 노인석, `029` 장애인석, `031` 노트북 — **13종** | `K4/p.java:5-17` |

실제 세터 호출: `u4/b.java:144-146`(`setTxtSeatAttCd_2(l.DEFAULT)`, `setTxtSeatAttCd_3(n.DEFAULT)`,
`setTxtSeatAttCd_4(str3)` — **str3 은 호출자 인자**), `u4/b.java:83-84`(짧은 오버로드가
`p.DEFAULT.getCode()`=`"015"` 를 넘기는 것이 전부 — 즉 `015` 는 **기본값이지 고정값이 아니다**),
`b5/c.java:235` (`setTxtSeatAttCd_4(pVar.getCode())` — 사용자가 고른 enum 코드를 그대로),
`b5/c.java:170` (대피도우미 `052`).

라이브러리는 `payloads.py:303-305` 에서 세 값을 전부 리터럴로 고정한다.

```python
"txtSeatAttCd_2": "000",
"txtSeatAttCd_3": "000",
"txtSeatAttCd_4": "015",
```

→ **자유석(003)·입석(033)·휠체어석(021/028)·2층석(018)·자전거(032)·유아동반(019) 조회 불가**,
창측/내측/순방향/역방향 필터 불가.

**여기서도 라이브러리는 이미 방법을 안다**: `limousine_payloads.py:149-151` 은 세 값을 전부
파라미터(`direction_seat_attribute_code`/`location_seat_attribute_code`/`room_seat_attribute_code`)로 노출하고,
`read_payloads.py:1523-1525` 도 `txtSeatAttCd_4` 를 `request.seat_attribute_code` 로 받는다.
안전 계층도 이 세 필드를 이미 정당한 와이어 필드로 인정한다 —
`safety.py:910-940`(**`LimousineScheduleView`** 핀)이 `txtPsgFlg_1~5` 와 `txtSeatAttCd_2/_3/_4` 를
모두 허용 집합에 담고 있다. `ScheduleView` 자체는 핀이 아예 없으므로(→ P2MIS-03)
필드를 뚫는 데 안전 계층 쪽 장애물도 없다.

**1차 관계 및 심각도 근거**: `03-reserve.md:145` (K3-06) 은 **예약** 폼의 `txtSeatAttCd4{i}` 가
자유석 `003` 을 반영하지 못하고 `015` 고정인 문제를 risk/low 로 잡았다. 같은 코드표·같은 상수의
병이 **조회** 폼에도 있는데 조회는 아무도 안 봤다 — 1차는 이 결함의 절반만 봤다.
**조회 쪽을 medium 으로 한 이유**: 예약 폼의 `txtSeatAttCd4` 는 *도달 가능한 필드에 잘못된 기본값*이라
호출자가 우회할 여지가 있지만, 조회 폼은 **파라미터 자체가 존재하지 않아** 어떤 호출자도 값을 바꿀 수 없고,
열차조회는 이후 모든 흐름(좌석도→예약→결제)의 진입점이라 여기서 걸러진 열차는 하위 흐름에서 복구할 수 없다.
`03-reserve.md` 와 심각도가 갈리는 것은 같은 근본원인의 서로 다른 도달성 때문이다.

- 앱 근거: `analysis/jadx/sources/K4/p.java:5-17`, `K4/l.java:5-7`, `K4/n.java:5-8`,
  `analysis/jadx/sources/u4/b.java:83-84`, `:144-146`, `analysis/jadx/sources/b5/c.java:170`, `:235`
- 라이브러리 근거: `src/korail_mobile_api/payloads.py:303-305` (+ 대조군 `limousine_payloads.py:149-151`)
- 수정 방향: `TrainSearchQuery` 에 좌석 옵션 3필드 추가, 기본값은 현재 상수 유지.

---

### P2MIS-03 — `KORAIL_EXACT_REQUEST_FIELDS` 미등록 read 라우트 13개는 **Mapping 입력에 한해 필드 검증이 통째로 생략**된다 (risk, low)

`assert_read_only_request_fields` 는 핀이 없으면 **아무 검사도 안 하고 즉시 반환**한다.

```
safety.py:1384  allowed = KORAIL_EXACT_REQUEST_FIELDS.get(route_path)
safety.py:1385  if allowed is None:
safety.py:1386      return
```

**범위 한정**: 이 구멍은 `data` 가 `Mapping` 일 때만이다. 순서있는 시퀀스(`Sequence[tuple]`)로 들어오면
조기 반환 **앞**에서 `if route_path not in KORAIL_EXACT_REQUEST_FIELD_ORDERS: raise`
(`safety.py:1376-1378`)가 먼저 걸러 거부한다. 그런데 구현된 read 라우트 대부분은 Mapping 을 쓴다
(`post_form` 의 `ordered` 분기는 `KORAIL_EXACT_REQUEST_FIELD_ORDERS` 등록 경로 전용).

Mapping 경로에서 조기 반환 뒤에 있는 검사가 전부 건너뛰어진다:
- 필드 집합 일치 (`safety.py:1411-1418`)
- **중복 키 금지** (`safety.py:1388-1395`)
- **스칼라 값 타입 강제** (`safety.py:1427-1430`, `str|int` 외 거부)

구현된 66경로 중 핀이 있는 것은 45개, **없는 것이 21개**다. 그중 mutation 8개는
의도된 설계이므로 제외한다(`http.py:241` docstring "no read-only field allowlist applies",
`tests/test_reference_derived_reads.py:239` 가 그 부재를 테스트로 못박음).
남는 **read 라우트 13개**가 문제다:

```
common.code.do · common.stationdata · common.stationinfo · login.Login
myTicket.MyTicketList · qry.chtnStn.do · research.actualTrainSchedule.do
schedule.runDt · seatMovie.ScheduleView
/ebizcross/getUUID.do · /ebizmaas/EbizMaasStationList.do
/file/CACHE/prdMobilePlusMain.cache · /file/CACHE/prdMobilePlusNotice.cache
```

**가장 구체적인 사례 — `common.code.do` 는 현재 검증기로는 구조적으로 핀을 걸 수 없다.**
이 경로의 폼(`payloads.py:362-377`)은 `"code"` 에 **리스트**를, `deviceWidth`/`deviceHeight`/`OSVersion`
에 **int** 를 싣는다. 핀을 걸면 `safety.py:1427-1430` 의 스칼라 검사(`type(value) not in {str,int}`)가
리스트 값을 거부해 정상 요청이 막힌다. 앱도 같은 모양이다(`CommonService.java:30`
`@Field(Constants.CODE) List<String>`). 즉 이 라우트가 미등록인 것은 게으름이 아니라
**검증기 자체가 반복키를 pin-able 하게 표현하지 못하는 한계**다 — 검증기 확장 없이는 못 고친다.

무파라미터 4개(`stationdata`, `runDt`, `getUUID`, cache 2개 중 하나)는 실질 위험이 없다.
나머지 문제는 **형태가 뚜렷한 5개**다 — 특히
`myTicket.MyTicketList`(앱 선언에 비회원 PII 필드 `hidName`/`hidTeleNo`/`hidPwd` 가 있음,
`MyTicketService.java:18`)와 `seatMovie.ScheduleView`(41필드, `SeatMovieService.java:12`)는
핀이 있었다면 그 필드들이 나갈 수 없었을 경로다.

**현재 잘못 나가는 요청은 없다**(각 빌더가 올바른 부분집합을 만든다). 다만 `safety.py:63-68` 이
"`KORAIL_EXACT_REQUEST_FIELDS` 가 write 오버로드 형태를 못 나가게 막는다"는 논리를 명시적으로 세워 둔 이상,
그 논리가 read 라우트의 22%(13/58)에는 적용되지 않는다는 사실은 기록돼야 한다.

1차 8개 보고서 어디에도 이 항목은 없다(`EXACT_REQUEST_FIELDS` 언급은 `01-auth.md:59,205` 두 곳뿐이고
둘 다 `certification.ReservationList` 단일 경로 이야기다). 슬라이스 단위로 보면 절대 안 보이는,
전 라우트를 한 번에 세어야만 보이는 항목이다.

- 앱 근거: `.../myTicket/MyTicketService.java:18`, `.../seatMovie/SeatMovieService.java:12`
  (핀이 있었다면 배제됐을 필드들이 선언돼 있음)
- 라이브러리 근거: `src/korail_mobile_api/safety.py:1376-1378`(ordered 선검사),
  `:1384-1386`(Mapping 조기 반환), `:694-1112`(45개 핀), `:69-203`(58개 read 라우트),
  `payloads.py:362-377`(`common.code.do` 리스트/int 값)
- 수정 방향: 형태가 고정된 read 라우트(`MyTicketList`, `chtnStn.do`, `actualTrainSchedule.do`,
  `stationinfo`, `EbizMaasStationList.do`)부터 핀 추가. `ScheduleView`(옵셔널 다수)는
  `KORAIL_OPTIONAL_REQUEST_FIELDS` 로 표현 가능. `common.code.do` 는 검증기가
  리스트 값을 허용하도록 확장해야 핀 가능.

---

## 2. 1차가 틀리게 봤거나 근거가 부족한 것 (CORRECTION)

### P2MIS-04 — 취소 1단계 `reservationCancel.ReservationCancel`: 결론은 1차가 맞으나 **근거로 든 경로가 하나뿐**이고 docstring 은 여전히 틀렸다 (doc-drift, low)

`06-cancel.md:62-72` 는 이 엔드포인트 미구현을 "검증된 의도적 단순화"로 판정하며
`a6/x.java:190-207`(다이얼로그 경로) 하나만 인용했다. 실측 근거
(`docs/MUTATION_HANDOFF.md:21` — cancel(unpaid hold) live-verified)는 내가 직접 확인했고 결론 자체는 동의한다.

다만 1차가 못 본 **두 번째 호출 변형**이 있다. 자동 재예약 경로에서는 다이얼로그 없이
두 호출이 **무조건 연속**된다:

```
DirectInquiryActivity.java:227-238  d3() → AutoRsvCancelDao      (POST reservationCancel.ReservationCancel)
DirectInquiryActivity.java:568-569  if (dao_auto_rsv_cancel == id) e3(...)   ← 성공 콜백에서 즉시
DirectInquiryActivity.java:240-250  e3() → AutoRsvCancelCheckDao (POST reservationCancel.ReservationCancelChk)
```

장바구니 경로도 순서는 같다: `BasketTicketActivity.java:348-356`(1단계) →
`:774-781` 확인 다이얼로그(`common_reservation_cancel_message` = "예약된 승차권을 취소하시겠습니까?",
`res/values/strings.xml:377`) → `:469-472`→`:359-367`(2단계) →
`:793-799` 완료 다이얼로그(`common_reservation_cancel_complete_message` = "예약이 취소되었습니다.",
`strings.xml:376`). **앱에는 `ReservationCancelChk` 단독 호출 변형이 존재하지 않는다.**

그런데 라이브러리 docstring 두 곳은 두 호출 전부를 `cancel_unpaid_hold` 가 하는 것처럼 서술한다:

```
client.py:1798-1800  "the app cancels the standing hold before re-booking
                      (DirectInquiryActivity.java:227-250 -- ReservationCancel then
                      ReservationCancelChk). That is :meth:`cancel_unpaid_hold`"
constants.py:247-248  "Confirming cancels the standing hold -- ReservationCancel then
                      ReservationCancelChk"
```

`cancel_unpaid_hold`(`client.py:1838-1876`)는 `ReservationCancelChk` **하나만** 보낸다. 그리고
`ReservationCancel` 은 `KORAIL_MUTATION_ROUTES` 에 없으므로 애초에 전송이 불가능하다.
읽는 사람은 "이 메서드가 앱과 동일한 2단계를 밟는다"고 오해하게 된다.

- 앱 근거: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:227-250, 568-569`;
  `.../ui/menu/BasketTicketActivity.java:348-367, 469-472, 774-799`;
  `.../network/dao/reservationCancel/ReservationCancelService.java:15-21`
- 라이브러리 근거: `src/korail_mobile_api/client.py:1798-1800, 1838-1876`,
  `src/korail_mobile_api/constants.py:247-248`, `safety.py:205-234`(allowlist 에 1단계 없음)
- 수정 방향: docstring 을 "앱은 2단계지만 이 메서드는 실측으로 확인된 2단계째만 보낸다"로 정정.

---

### P2MIS-05 — `seatMovie.ScheduleViewSpecial` 은 "보류"가 아니라 **전송 불가**다 (partial, low)

`08-core.md:140` (K8-05)는 "파서/페이로드는 완성, 공개 API 배선은 테스트로 고정된 의도적 보류"로 적었다.
한 단계 더 확인하면 이 경로는 `KORAIL_READ_ONLY_ROUTES` 에도 **없다** — 배선을 뚫어도
`assert_read_only_route`(`safety.py:1327-1331`)가 막는다. "배선만 하면 되는 상태"가 아니라
allowlist 추가까지 필요하다. 같은 패턴이 하나 더 있다: `_build_product_train_inquiry_form`
(`read_payloads.py:1465-1533`, `ScheduleView` 의 `txtMenuId="41"` 여행상품 변형)은 완성돼 있으나
`src/` 어디서도 호출되지 않고 `tests/test_next_variant_reads.py:109-110` 이
`KorailClient` 에 없다는 것을 테스트로 못박고 있다(의도적 비공개).

- 앱 근거: `.../seatMovie/SeatMovieService.java:20`(ScheduleViewSpecial),
  `.../seatMovie/ProductTrainInquiryDao.java:8`
- 라이브러리 근거: `src/korail_mobile_api/safety.py:69-203`(두 경로 모두 부재),
  `read_payloads.py:1465`, `tests/test_next_variant_reads.py:109-110`

---

## 3. 교차확인만 하고 넘어간 것 (1차 판정에 동의, 재작성 안 함)

전량 재확인했고 **1차 판정과 다른 결론이 나오지 않았다.** 근거만 남긴다.

| 항목 | 재확인 방법 | 결과 |
|---|---|---|
| DynaPath 적용 대상 6경로 | `ExecuteDao.java:27` 의 `String[] strArr` vs `constants.py:421-429` | **완전 일치**. 단 그중 `nonMember.NonMemTicket`·`seatMovie.ScheduleViewSpecial` 2개는 라이브러리가 미구현이라 사문 조항 |
| `BaseRequest` 3상수 | `BaseRequest.java:7-9` (`AD`/`korail1234567890`/`250601003`) vs `constants.py:4-6` | 일치 |
| Device/Version/Key/Sid 봉투 | 구현된 66경로 전부에 대해 앱 `@Field` 선언 ↔ 라이브러리 핀 자동 대조 | **불일치 0건**. `gdMenuLt`/`gdReqQry`/`trGdMenuLt` 의 `Key` 부재, `ScheduleView`/`LimousineScheduleView`/`TrainResearch` 의 `Sid` 존재까지 정확히 반영돼 있음 |
| `@FieldMap`/`@QueryMap` 을 가진 구현 경로 | 12개 추출 후 개별 확인 | 전부 기존 판정과 동일 (`prcFare.do` 의 `Price2FareParams` 는 단일 열차 맵, 다구간 아님) |
| `List<String>` 반복키 경로 | `cmtrInfo.do`, `common.code.do`, `gdMenuLt.do`, `pbpAcepSpec.do`, `plfNo.do`, `PriceReCalculation` | 라이브러리가 `_COMMUTER_INFO_PATH`/`_REPEATED_TICKET_REFERENCE_PATHS`(`safety.py:1230-1237`)로 처리. `common.code.do` 는 핀이 없어 검사 자체가 생략(→ P2MIS-03) |
| `isArrow` boolean | `BusReservationService.java:31`, `ResearchService.java:57` 은 `boolean`; 앱은 `true`/`false` 리터럴 | 라이브러리 `payloads.py:215`, `limousine_payloads.py:119` 가 `"true"`/`"false"` 문자열 — Retrofit 와 동일 와이어. **타입 불일치 아님** |
| `trn.prcFare.do` 의 `trnCnt` 부재 | `Price2FareDao.java:170-172` `setTrnCnt(String str){ this.trnCnt = this.trnCnt; }` — **앱 자체 자기대입 버그**로 항상 null | 라이브러리 생략이 정답 |
| `myTicket.MyTicketList` 의 `tsRsStnCd` | 앱 전체에서 `setTsRsStnCd` 호출 0건 | 생략이 정답 |
| `copt.gdMenuLt.do` 승차권 스코프 변형 | `AdditionalServiceActivity.java:157-166`(pnrNo+tkRetNo), `MaasAddReservationActivity.java:69-74`(addSrvReqNo) 는 실재 | 다만 과거 감사 3회가 이미 "비결함(라이브러리는 base 브랜치만 구현)"으로 판정 — `docs/deep-dive/impl-audit-reverify4-2026-07-22.md:120` 등. **info 로만 유지** |
| NetFunnel 미배선 | 앱은 `setNetfunnelDao` 를 3곳에서만 호출(`b5/c.java:112` 열차조회, `c5/a.java:184` 예약, `ReservedTicketActivity.java:306` 예약승차권목록) | 라이브러리는 `KorailNetFunnelClient` 를 **의도적으로 독립**시켜 두었고 README:160-187 이 그 이유와 사용법을 명시. 결함 아님 |
| mutation 게이트 구멍 | `post_form`↔`post_mutation_form`↔`get_mutation_query` 3경로 전수 + `assert_mutation_route_category` | **구멍 없음**. read 경로는 mutation 라우트를 거부하고 그 역도 성립. 카드 보유 카테고리는 집합 멤버십으로 검사(`http.py:277-287`) |
| 앱-only 93경로 각각의 1차 커버리지 | 8개 보고서 전문 기계 검색 | **미언급 0건** |
| 실측 성공했는데 미구현인 경로 | `docs/api-status-by-service.md` 165행 파싱 | **0건** |

의도된 제외로 재확인한 것(결함 아님): 정기권(통근패스) 구매(`pass.passReserve`/`passPayIssue`,
`PassService.java:19-25`), 단체예약, 셀프체크인 4종, MAAS 부가서비스 취소 3종, PG WebView 결제 준비 7종,
`onepass.login.do`(WebView URL — API 아님, `MyPageActivity.java:543`).

---

## 4. 숫자 정합 (다른 단계와 대조할 때 읽을 것)

- `app_functions_extracted = 159` = **유니크 경로 수**. 어노테이션 메서드 선언은 165개지만
  오버로드(`certification.TicketReservation`×2, `nonMember.NonMemTicket`×2,
  `certification.ReservationList`×2, `common.encrypt.do`×2, `reservationCancel.ReservationCancelChk`×2 등)가
  같은 경로로 접히면서 159가 된다. jadx·smali 양쪽에서 동일하게 재현됨.
- `implemented_count = 66` = `safety.py` 의 `KORAIL_READ_ONLY_ROUTES`(58) + `KORAIL_MUTATION_ROUTES`(8)
  의 유니크 경로 수. "라이브러리가 실제로 전송할 수 있는" 것의 정의를 이 두 frozenset 으로 잡았다.
  docstring 언급이나 파서 존재만으로는 세지 않았다(그래서 `ScheduleViewSpecial` 은 미구현으로 셈).
- 1차 슬라이스 합계와 직접 더해 비교하지 말 것 — 1차는 슬라이스마다 "메서드", "엔드포인트",
  "기능" 을 섞어 셌다.

## 5. 요약

- 엔드포인트 수준: 1차 8분할은 앱 표면 159경로를 빠짐없이 덮었다. **누락 렌즈로 새로 나온 엔드포인트는 없다.**
- 파라미터 수준: **구현된 경로 안쪽**에서 3건이 새로 나왔다. 그중 2건(P2MIS-01, P2MIS-02)은
  가장 많이 쓰이는 `seatMovie.ScheduleView` 에 몰려 있고, 원인은 `02-search` 가 이 패키지를 명시적으로
  범위 밖으로 선언하고 `08-core` 는 경로 존재만 센 **슬라이스 경계 사각지대**다.
- 두 건 모두 라이브러리가 이미 리무진/여행상품/예약 쪽에서 **같은 필드를 올바르게 다루고 있어**,
  코드를 새로 발명할 필요 없이 기존 패턴을 일반 열차조회에 이식하면 된다.
- critical/high 없음. 안전 게이트 우회, 카드정보 유출, 잘못된 금전 이동 경로는 발견하지 못했다.
