# Phase 2 — 오구현(Incorrect) 렌즈 전체 표면 재검증

대상: `/Users/yakisoba/Documents/GitHub/korail-mobile-api`
렌즈: **라이브러리에 있긴 한데 틀린 것** (필드명, 값 타입, 상수값, 분기, 기본값, 파싱 키, 인코딩, 헤더, 엔드포인트 동일성)
방법: 1차 8개 보고서를 읽되 신뢰하지 않고, APK 전체를 **기계적 diff**로 독립 재구성한 뒤 라이브러리와 대조.

---

## 0. 방법 — 무엇을 기계적으로 돌렸는가

1차가 도메인별로 나뉘어 있어 **공유 코드/전역 불변식**에 구조적으로 눈이 멀어 있다고 판단하고,
전 표면을 한 번에 훑는 6개의 diff를 스크립트로 돌렸다. 스크립트는 저장소 밖
(`/private/tmp/.../scratchpad/*.py`)에만 썼고 저장소는 읽기만 했다.

| # | diff | 소스 | 결과 |
|---|---|---|---|
| A | **Retrofit 엔드포인트 전수 추출** — `smali*/**` 중 `Lretrofit/http/` 을 포함하는 모든 인터페이스에서 (verb, path, @Field/@Query 이름, 순서) 추출 | `analysis/apktool/smali*/` (annotation `value = "..."` 는 컴파일 상수가 **인라인**되어 있어 authoritative) | **165 Retrofit 메서드 / 159 고유 path** |
| B | **HTTP verb 대조** — `safety.py` 의 (verb, path) 66쌍 전부 vs 앱 | `safety.py:69-180`, `safety.py:222-260` | **불일치 0건** |
| C | **요청 필드 pin 대조** — `KORAIL_EXACT_REQUEST_FIELDS` 45개 route의 정확 필드집합 vs 앱 @Field/@Query 집합 | `safety.py:694-1111` | LIB-ONLY 발생 route **0건** (유일한 차이는 `trn.prcFare.do`의 @FieldMap 키 — 정상). APP-ONLY 는 전부 앱이 null 로 두어 Retrofit이 드롭하는 필드 |
| D | **응답 파싱 키 대조** — `*_parsers.py` / `*_models.py` 가 실제로 조회하는 키 537종을, `network/**` DTO 필드명 + `@SerializedName` 값 1,586+604종과 대조. 추가로 각 `parse_*` 함수의 키 소유 DTO 클러스터가 흩어지는지(=다른 DAO의 키를 훔쳐오는지) 검사 | `read_parsers.py`, `parsers.py`, `mutation_parsers.py`, `limousine_parsers.py` | 앱 DTO에 없는 키 **0건**(예외 5건은 라이브러리 내부 python 필드명). 타 DAO 키 오용 **0건** |
| E | **자바 원시타입 vs 파서 헬퍼 대조** — 앱이 `int/long/double` 로 선언한 필드를 라이브러리가 문자열 전용 헬퍼로 읽는가, 그 반대는? | `field_types.json` (103개 원시 필드) | **불일치 0건** |
| F | **필드 순서 대조** — `KORAIL_EXACT_REQUEST_FIELD_ORDERS` 12개 route의 고정 순서가 앱 Retrofit 파라미터 선언 순서의 subsequence 인가 | `safety.py:1119-1225` vs diff A의 순서 정보 | **불일치 0건**. `trn.prcFare.do` 만 형식상 걸렸는데 원인은 앱의 `trnCnt` no-op setter(§P2INC-03-2)였고 라이브러리가 옳다. `tk.pbpAcepSpec.do`/`tk.plfNo.do` 는 pin 이 의도적 빈 튜플(반복키 전용 검증) |

**이 여섯 개 diff의 결론: 이 라이브러리의 wire 이름/verb/파싱 키 표면은 사실상 무결하다.**
과거 `txtPrnNo/txtPnrNo` 류의 한 글자 오타는 **현재 한 건도 남아있지 않다**
(`build_refund_form` 은 `txtPnrNo` 로 정확하고, `RefundService.smali:210` 과 일치).

남은 결함은 전부 **이름이 아니라 값·출처·단계**에 있다. 아래가 그 목록이다.

**카운팅 규칙 (단위 통일: 둘 다 Retrofit 메서드)**: 분모 = `Lretrofit/http/` 어노테이션을
가진 모든 인터페이스의 abstract 메서드 **165개**(고유 path 159). 분자 = 라이브러리가 그 path 로
실제 전송하는 코드경로를 가진 앱 메서드 **68개**(고유 path 65 + 같은 path 의 오버로드 3).
"도달한다(reached) ≠ 옳다(correct)": 68개 중 아래 결함이 붙은 것이 7개다.
1차 8개 보고서의 숫자는 규칙이 서로 달라 **합산하지 않았다**.

---

## 1. 1차가 **놓친** 것 (NEW)

### P2INC-01 — 결제금액 `hidMnsStlAmt1` 의 출처 우선순위가 앱과 **뒤집혀** 있다 [risk / medium]

- **앱 근거**: `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:168-203`
  (`G0()`). 신규 홀드 결제 경로(=`isReservationResponseNull()` 이 **false**)에서 앱은
  `h_tot_rcvd_amt` 를 **읽지 않는다**. 좌석 행을 순회해
  `totalAmount = Σ(h_seat_prc + h_seat_fare)`,
  `discountAmount = Σ((h_seat_prc + h_seat_fare) − h_rcvd_amt)` 을 만들고
  `mReceivedAmount = totalAmount − discountAmount`(대수적으로 **Σ h_rcvd_amt**)를 쓴다
  (`:186-199`). `h_tot_rcvd_amt` 를 직접 쓰는 건 **다른 화면**인
  `ui/menu/BasketTicketActivity.java:638`(장바구니에서 재조회한 응답) 뿐이고,
  그 값은 `PaymentActivity` 의 `else` 분기
  (`getIntent().getIntExtra("RECEIVED_AMOUNT")`, `:170`)로만 들어온다.
  **결정적인 부분:** `BasketTicketActivity.V0()` 는 같은 Bundle 에
  `RECEIVED_AMOUNT`(=`h_tot_rcvd_amt`, `:638`)와 `RESERVATION`(=`ReservationResponse`,
  `:639`)을 **동시에** 넣는다. 그런데 `PaymentActivity.G0()` 는 `RESERVATION` 이 있으면
  (`isReservationResponseNull()==false`) `RECEIVED_AMOUNT` extra 를 **읽지 않는다**.
  즉 앱에는 `h_tot_rcvd_amt` 가 `hidMnsStlAmt1` 에 도달하는 살아있는 경로가 **하나도 없다**.
  최종 전송은 `B6/AbstractC1269e.java:406` → `V4/a.java:27`(`setHidMnsStlAmt(1, …)`).
- **라이브러리 근거**: `src/korail_mobile_api/mutation_parsers.py:83-86` —
  `total = _optional_string(raw, "h_tot_rcvd_amt", …)` 를 **먼저** 시도하고 그것이 숫자면
  즉시 반환, 좌석 합산(`:87-121`)은 **폴백**. `mutation_payloads.py:1402`
  (`"hidMnsStlAmt1": amount`), `mutation_models.py:256-261`.
- **상세**: 두 값이 항상 같다는 보장이 앱 안에 없다. 앱은 신규 홀드에서 서버가 준 총액 필드를
  **일부러 무시하고** 좌석 단위로 재계산한다. 서버의 `h_tot_rcvd_amt` 가 좌석합과 다른
  케이스(부가상품·수수료·마일리지 반영 시점 차이 등)가 단 한 번이라도 존재하면
  라이브러리는 앱과 **다른 금액으로 결제**한다. 저장소 fixture 중 실측 홀드 응답에
  `h_tot_rcvd_amt` 가 담긴 사례는 없다(전부 합성값). 1차 05-pay 는 `received_amount` 를
  "앱의 getReceivedAmount()" 로만 확인하고 **우선순위 역전**은 보지 않았다.
- **수정**: 좌석 합산을 1순위로, `h_tot_rcvd_amt` 를 폴백으로 뒤집고, 두 값이 모두 읽힐 때
  불일치하면 `KorailProtocolError` 로 거절.

### P2INC-02 — 홀드 취소가 앱의 2단계 중 **2단계만** 호출한다 (1단계 `ReservationCancel` 미구현) [risk / medium]

- **앱 근거**: 앱의 모든 취소 경로는 `RsvCancelDao`(→ `reservationCancel`,
  `/classes/com.korail.mobile.reservationCancel.ReservationCancel`)를 쓴다:
  `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelDao.java:65-67`;
  호출부 `ui/reservation/confirm/activity/DReservationConfirmActivity.java:269-279`
  (smali 재확인: `.../DReservationConfirmActivity.smali` `executeRsvCancel` 본문,
  `setTxtJrnySqno("0001")`/`setHidRsvChgNo("000")` const-string 확인),
  `ui/menu/ReservedTicketActivity.java:280-289`, `ui/menu/BasketTicketActivity.java:348-357`,
  `ui/limousine/LimousineSelectSeatActivity.java:319-328`.
  `RsvCancelCheckDao`(→ `ReservationCancelChk`)는 **그 다음 단계**다:
  병합예약 흐름이 그 순서를 그대로 드러낸다 —
  `ui/inquiry/rir/orr/DirectInquiryActivity.java:277` 가 `d3()`(=`AutoRsvCancelDao`,
  `:227-238`)를 먼저 실행하고, 그 응답 콜백 `:568-570` 에서 `e3()`(=`AutoRsvCancelCheckDao`,
  `:240-250`)를 실행한다. 두 인터페이스 선언은
  `network/dao/reservationCancel/ReservationCancelService.java:15,19`(필드 7개 동일).
- **라이브러리 근거**: `src/korail_mobile_api/client.py:1856-1874` — `route` 가
  `".../reservationCancel.ReservationCancelChk"` **하나뿐**. `safety.py:222-228` 의
  `KORAIL_MUTATION_ROUTES` 에도 `ReservationCancel` 은 없고, 전체 `src/` 에
  `com.korail.mobile.reservationCancel.ReservationCancel"` 리터럴이 존재하지 않는다.
- **상세**: `docs/RELEASE_GAP_PLAN.md:640-646,985-986` 은 "Chk 가 COMMIT 단계이고 1단계는
  생략 가능"이라고 **주장**하지만, 그 주장의 근거는 srtgo 계보(외부 구현)이지 이 앱이 아니다.
  이 앱은 1단계를 먼저 보낸다. 실측으로 단독 Chk 가 통했다는 기록은 있으므로
  (`docs/verification-record.md:960` — 병합 홀드 취소 `IRG000000`) 즉시 깨지는 결함은 아니다.
  다만 **앱과 다른 프로토콜 시퀀스**이고, 1차 06-cancel 은 이 엔드포인트 동일성 자체를
  질문하지 않았다.
- **수정**: 최소한 docstring/문서에서 "앱은 2단계"임을 명시하고, 단독 Chk 실패 시
  `ReservationCancel` → `ReservationCancelChk` 순으로 재시도하는 경로를 준비.

### P2INC-03 — (오탐 철회 + 함정 기록) DTO 필드명 ≠ wire 이름, 그리고 앱 자체의 no-op setter [info]

**이 항목은 원래 "라이브러리가 앱이 안 보내는 `regSqno` 를 보낸다"는 결함으로 적었다가
철회한 것이다.** 철회 사유와, 같은 함정 두 건을 기록한다. 향후 감사가 같은 오탐을 반복하지
않도록 남긴다.

1. **`regSqno` — 라이브러리가 맞다(오탐 철회).**
   `ConvenienceSettingRequest` 의 DTO 필드/세터 이름은 `reqSqno`(**q**)인데
   Retrofit wire 이름은 `regSqno`(**g**)다
   — `analysis/apktool/smali/com/korail/talk/network/dao/research/ConvenienceSettingDao$ConvenienceSettingRequest.smali:22`
   (`.field private reqSqno:Ljava/lang/String;`), `ConvenienceSettingDao.smali:106`
   (`getReqSqno()` → `@Field("regSqno")`, `ResearchService.java:45`).
   `setReqSqno("0")` 는 실제로 호출된다:
   `ui/booking/mainBooking/MainBookingActivity.smali:4920-4927`
   (`const-string v2, "0"` → `setReqSqno`), 동일 패턴
   `OldMainBookingActivity.smali:910`, `provider/WidgetService.smali:193`,
   `provider/WidgetReceiver.smali:261`.
   → `read_payloads.py:797-802` 의 `{"custMgNo", "medDvCd":"03", "regSqno":"0"}` 와
   `safety.py:943-945` 의 pin 은 **정확하다**. `tmGpCd`/`trnGpCd`(1차 22a)와 같은 계열의
   함정이며, DTO 필드명으로 grep 하면 오탐이 난다. **반드시 annotation 값으로 grep 할 것.**

2. **`trn.prcFare.do` 의 `trnCnt` — 앱의 setter 가 no-op 이라 필드가 나가지 않는다.**
   diff C 에서 유일하게 "APP-ONLY" 로 남은 필드였는데, 앱 자신의 버그다:
   `analysis/apktool/smali/com/korail/talk/network/dao/trainsInfo/Price2FareDao$Price2FareRequest.smali`
   의 `setTrnCnt` 본문이
   `iget-object p1, p0, …->trnCnt` → `iput-object p1, p0, …->trnCnt` — 인자를 버리고
   자기 자신을 다시 쓴다. `ui/price/PriceFareActivity.smali:357` 이 호출해도 필드는 `null`
   로 남아 Retrofit 이 드롭한다. jadx 는 이를 `this.trnCnt = this.trnCnt;`
   (`Price2FareDao.java:171`)로 렌더하는데 디컴파일 아티팩트가 아니라 **실제 바이트코드**다.
   → 라이브러리가 `trnCnt` 를 안 보내는 것이 **옳다**(`read_payloads.py` 의 prcFare 빌더).
   또한 `Price2FareParams`(`Price2FareDao.java:81-124`)가 인덱스 접미어 없는 평문 키
   (`runDt`, `trnNo`, `dptRsStnCd`, `arvRsStnCd`, `gdNo`, `rqSeatAttCd`, `trnGpCd`,
   `stlbTrnClsfCd`)를 쓰는 것도 라이브러리와 일치.

### P2INC-04 — 취소 폼이 서버가 준 `txtJrnyCnt` 의 **제로패딩을 벗겨서** 보낸다 [incorrect / low]

- **앱 근거**: `DReservationConfirmActivity.java:273`
  (`setTxtJrnyCnt(reservationResponse.getH_jrny_cnt())` — **그대로 echo**),
  smali 재확인 `.../DReservationConfirmActivity.smali` `executeRsvCancel`:
  `getH_jrny_cnt()` → `move-result-object v2` → `setTxtJrnyCnt(v2)` 사이에 어떤 변환도 없음.
  동일 패턴 `ui/menu/ReservedTicketActivity.java:228,284`,
  `ui/inquiry/rir/orr/DirectInquiryActivity.java:232,245`. 실측 홀드는
  `h_jrny_cnt="0001"` / `"0002"` 형태다(라이브러리 자신의 주석
  `mutation_payloads.py:1218-1222` 이 이를 인정).
- **라이브러리 근거**: `src/korail_mobile_api/mutation_payloads.py:1233,1249` —
  `legs = int(journey_count)` 후 `"txtJrnyCnt": str(legs)` → `"0001"` 이 `"1"` 로 바뀐다.
- **상세**: 폼 인코딩이라 타입은 문제가 안 되지만 **자릿수는 남는다**. 이 프로젝트가
  반복적으로 밟은 함정(문자열/숫자 폭 손실)의 정확한 사례. 실측으로는 통과한 이력이 있어
  low 로 둔다.
- **수정**: `journey_count` 를 검증만 하고 **원문 그대로** 실어 보낼 것.

### P2INC-05 — 환불 폼의 `latitude`/`longitude` 가 항상 `""`, 그리고 앱의 다른 환불 호출부는 4개 필드를 **아예 생략**한다 [incorrect / low]

- **앱 근거**: `analysis/apktool/smali/com/korail/talk/ui/ticket/ticketReturn/a.smali:3176,3181`
  의 인자 `v2`/`v1` 은 같은 메서드 앞부분(`~:2920-2980`)에서
  `Lb5/c;->getLocation()` → `Landroid/location/Location;->getLatitude()D` /
  `getLongitude()D` 를 `String.valueOf` 한 값이다. (위치가 없을 때의 `""` 폴백 분기는
  같은 메서드 안에 `const-string v2, ""` 로 보이지만 분기 조건까지 추적하지는 않았다 —
  이 항목의 내용은 "라이브러리가 앱의 **두 shape 중 어느 쪽도** 재현하지 않는다"이지
  폴백 조건이 아니다.)
  또한 **두 번째 환불 호출부** `ui/ticket/confirm/TicketListActivity.java:960-972`(`r1()`)
  는 `txtPnrNo`/`h_orgtk_*`/`h_mlg_stl`/`pbpAcepTgtFlg` 만 세팅하고
  `tk_ret_tms_dv_cd`·`trnNo`·`latitude`·`longitude` 는 **세터를 호출하지 않아** Retrofit 이
  네 필드를 전부 드롭한다(`RefundDao.java:executeDao` 가 null 을 그대로 전달).
- **라이브러리 근거**: `src/korail_mobile_api/mutation_payloads.py:1456-1459` —
  `"trnNo": ticket.train_no`, `"latitude": ""`, `"longitude": ""` 를 무조건 포함.
- **상세**: 앱이 실제로 보내는 두 가지 shape(위치 있는 14필드 / 10필드) 중 어느 쪽도 아니다.
  단독으로 결제를 깨뜨릴 가능성은 낮지만, 환불은 이 저장소가 이미 한 번 필드 문제로 깨진
  영역이라 기록한다. 1차 06-cancel 은 `tk_ret_tms_dv_cd`/`pbpAcepTgtFlg` 만 다뤘다.
- **수정**: `latitude`/`longitude` 를 옵셔널로 두고 미지정 시 키 자체를 생략.

### P2INC-06 — `parse_reservation_history_response` 의 `P100` 빈결과 허용에 APK 근거가 없다 [unverifiable / info]

- **앱 근거**: **없음.** `grep '"P100"' analysis/apktool/smali*/` 결과 0건.
  비교 대조군으로 같은 목적의 `WRG000000`(`g6.1/c.smali`, `g6.1/a.smali`),
  `P114`(`ui/ticket/confirm/TicketListActivity.smali`) 는 APK 에 존재한다.
  앱의 공통 디스패처(`L4/h.smali`)는 `strResult=="FAIL"` 이면 인식 못한 코드도
  오류 다이얼로그로 보낸다.
- **라이브러리 근거**: `src/korail_mobile_api/read_parsers.py:1146-1149`
  (`accepted_empty_codes=frozenset({"P100"})`), `errors.py:479-480`
  (`NO_RESULT_CODES` 에 `P100`, `WRT300005` — 주석이 "live-observed only" 라고 명시).
- **상세**: "번들에 없다 ≠ 프로토콜에 없다"는 이 프로젝트의 함정 규칙에 따라 **결함으로
  단정하지 않는다**. 다만 라이브러리는 이 코드에서 앱과 **반대로** 동작한다(앱: 오류 표시,
  라이브러리: 조용히 빈 결과). 실측 로그가 근거이므로 유지하되, "앱과 다른 동작"임을
  docstring 에 명시할 것을 권한다.

---

## 2. 1차와 **교차확인**된 것 (동일 결론, smali 로 재확인)

### P2INC-07 — `CardPayment.installment` 기본값 `"00"` 은 앱의 일시불 코드 `"0"` 과 다르다 [incorrect / medium]
*(1차 K5-03 = low. 나는 medium 을 주장한다.)*

- **앱 근거 (smali)**: `analysis/apktool/smali/K4/h.smali:44-52` —
  `INS_0` enum 생성자에 `const-string v2, "0"` (단일 문자). 나머지도 전부 무패딩
  (`:76 "2"`, `:104 "3"`, `:132 "4"`, `:160 "5"`, `:188 "6"`, `:216 "12"`, `:244 "24"`).
  이 값이 `V4/a.java:238-263`(`getInstallmentType` → `hVar.getCode()`)의 반환이며,
  `V4/a.java:32,84,98` 이 그대로 `setHidIsmtMnthNum(1, …)` 에 넣는다.
  APK 어디에서도 `hidIsmtMnthNum` 에 `"00"` 이 들어가는 경로가 없다.
- **라이브러리 근거**: `src/korail_mobile_api/mutation_models.py:311`
  (`installment: str = "00"`), `mutation_payloads.py:1407` (`"hidIsmtMnthNum1": card.installment`).
- **medium 인 이유**: (a) 돈이 움직이는 경로의 **기본값**이라 아무 것도 지정하지 않은
  모든 결제가 이 값을 탄다. (b) 저장소의 유일한 실서버 결제 시도는 **거절(fake card)** 이라
  이 필드가 서버에 수용되는지 검증된 적이 없다 — 즉 "서버가 정수로 파싱할 것"이라는
  1차의 완화 논거는 **미검증 가정**이다. (c) 앱과 바이트 일치를 표방하는 설계 원칙에 위배.
- **수정**: 기본값을 `"0"` 으로, docstring 주석도 정정.

### P2INC-08 — `build_refund_form` 의 `tk_ret_tms_dv_cd="21"`, `pbpAcepTgtFlg="N"` 고정 [incorrect / high]
*(1차 K6-02 / K6-03 과 동일 결론. smali 로 확정.)*

- **앱 근거 (smali)**: `analysis/apktool/smali/com/korail/talk/ui/ticket/ticketReturn/a.smali:3153`
  직전 — `RefundCommissionDao$RefundCommissionResponse;->getTk_ret_tms_dv_cd()` 의 반환을
  그대로 `setTk_ret_tms_dv_cd(...)` 에 넣는다(**서버 에코**). 같은 파일 `:3171` 직전 —
  `TicketDetailDao$TicketDetailResponse;->getH_pbp_acep_tgt_flg()` 를 그대로
  `setPbpAcepTgtFlg(...)` 에 넣는다. jadx 대조: `ui/ticket/confirm/TicketListActivity.java:970`
  도 `setPbpAcepTgtFlg(ticketDetailResponse.getH_pbp_acep_tgt_flg())`.
  Retrofit 선언은 `RefundService.smali:235,250`.
- **라이브러리 근거**: `src/korail_mobile_api/mutation_payloads.py:1455,1457`
  (`"tk_ret_tms_dv_cd": "21"`, `"pbpAcepTgtFlg": "N"`). 또한 `read_parsers.py` 의
  refund-detail 파서가 `h_pbp_acep_tgt_flg` 를 노출하지 않아 **호출자가 올바른 값을
  구할 방법조차 없다**(1차 K6-03 과 동일 관찰).
- **상세**: `tk_ret_tms_dv_cd` 는 수수료 조회(`refunds.CommissionView`) 응답이 정하는
  "환불 회차 구분"이며, `pbpAcepTgtFlg` 는 대리인수 대상 여부다. 둘 다 환불 금액·가능
  여부를 바꿀 수 있는 값이고 라이브러리는 두 값을 **서버 응답과 무관하게** 고정한다.
- **수정**: `get_ticket_commission` 응답에서 `tk_ret_tms_dv_cd` 를,
  `get_refund_ticket_detail` 응답에서 `h_pbp_acep_tgt_flg` 를 파싱해 `PaidTicket` 에 싣고 에코.

### P2INC-09 — `txtSeatAttCd4` 가 항상 `"015"` — 자유석 분기(`"003"`)를 재현하지 못한다 [partial / low]
*(1차 K3-06 과 동일. 분기 조건을 소스로 확정했다.)*

- **앱 근거**: `analysis/jadx/sources/C5/a.java:85-97` —
  `if (J.isFreeSeat(selectSeatTypeCode, h_gen_rsv_cd, h_free_rsv_cd))`
  → `oSeat.setSeatAttCd4(i, p.NORMAL_FREE.getCode())`; 아니면 2층석 예외
  (`h_seat_att_cd != null && t2()==SECOND_FLOOR && h_seat_att_cd != t2()` → `h_seat_att_cd`);
  아니면 `t2()`. 코드값은 `K4/p.java:5,9,13`
  (`NORMAL_FREE "003"`, `DEFAULT "015"`, `SECOND_FLOOR "018"`).
- **라이브러리 근거**: `src/korail_mobile_api/mutation_payloads.py:841,854`(직통/환승) · `:431,436`(병합)
  (`_seat_attribute_key(1): "015"`, `journey>=2` 도 `"015"` 고정; 키 생성은 `:575-577`).
- **상세**: 라이브러리가 검색 단계에서도 `txtSeatAttCd_4="015"` 로 고정
  (`payloads.py:305`)하므로 2층석 분기는 논리적으로 도달 불가 — 즉 **자유석 분기 하나만**
  재현 불가다. 자유석 예매 자체를 지원하지 않는 설계로 볼 수도 있으나 문서화된 제외는 아니다.

### P2INC-10 — 결제 dry-run 미리보기에서 `hidRsvChgNo` 가 마스킹되지 않는다 [risk / medium]
*(1차 K5-02 와 동일. 재확인.)*

- **앱 근거**: 값의 출처가 예약별로 다른 실제 시퀀스임 — `V4/b.java:41`
  (`getJrny_infos().getJrny_info().get(0).getH_rsv_chg_no()`),
  Retrofit 선언 `network/dao/payment/PaymentService.java:14` `@Field("hidRsvChgNo")`.
- **라이브러리 근거**: `src/korail_mobile_api/redaction.py:24,141,142,143` 에
  `hidPnrNo`/`hidWctNo`/`hidTmpJobSqno1`/`hidTmpJobSqno2` 는 있으나 **`hidRsvChgNo` 없음**
  (파일 전체 grep 0건). `consent.py:114-131` 이 `redact_payload` 만 태우므로
  allowlist 미등재 키는 `MutationPreview.payload` 에 평문으로 남는다.
  `client.py:1890-1891,1956-1957` docstring 은 "identity 필드가 redact 된다"고 약속한다.

---

## 3. 1차가 **틀리게 본 것** — 심각도 재평가

| 1차 항목 | 1차 판정 | 2차 판정 | 근거 |
|---|---|---|---|
| 05-pay **K5-03** (`installment "00"`) | incorrect / **low** ("서버가 정수로 파싱할 가능성이 높음") | incorrect / **medium** (P2INC-07) | 완화 논거가 미검증 가정이다. 실서버 결제는 fake-card 거절 1회뿐이라 이 필드의 수용 여부가 확인된 적이 없고, 이 값은 **기본값**이라 명시 지정 없는 모든 결제를 탄다 |
| 06-cancel **K6 슬라이스 전반** | 취소 엔드포인트 자체는 "있음"으로 통과 | 엔드포인트 **동일성 미검증** (P2INC-02) | 앱은 `ReservationCancel` → `ReservationCancelChk` 2단계. 라이브러리는 2단계만. 1차는 필드만 대조하고 DAO→Service 매핑을 따라가지 않았다 |
| 02-search **TSF-02** (`TrainSchedule` 응답 모델이 근거 없이 ~20필드 추가) | unverifiable / medium | **정정 불필요하나 재분류 권고: info** | diff D 결과 라이브러리가 실제로 *조회하는* 응답 키 537종 중 앱 DTO에 없는 것은 0건이다. 모델 필드가 많은 것과 없는 키를 읽는 것은 다른 문제이며, 후자는 발생하지 않는다 |
| 05-pay **K5-02** (`hidRsvChgNo` 미마스킹) | risk / medium | **동일 (medium)** | 재확인. 다만 카드정보 유출은 아니므로 critical 아님 |

---

## 4. 명시적 무결 확인 (negative results — 다음 감사에서 다시 안 파도 되는 것들)

아래는 **기계적으로 전수 확인해 문제 없음**을 확정한 항목이다.

- **verb/path 66쌍 전부 일치.** GET 를 POST 로 보내는 곳 없음 (`safety.py:69-180` vs diff A).
  특히 `product.ReservationList/Detail`, `push.crwCallRq.do`, `push.cmtrKnd.do`,
  `ticket.dcntCrdUseQry.do`, `research.dcntCrdScheduleView.do`,
  `certification.ReservationList`, `reservation.dcntCrdExtn.do` 는 모두 GET 으로 올바름.
- **`certification.ReservationList` 오버로드 방어 유효.** 앱의 write 오버로드
  `applyDisabilityCertification`(`CertificationService.smali:7`, `txtPsgDisc0019Cnt` + 6개
  @QueryMap)은 `safety.py:1028-1030` 의 4필드 pin(`Device,Version,Key,hidPnrNo`)에 의해
  이 경로로 나갈 수 없다 — read 오버로드 `inquiryTicketRsv`(`:358`) 필드와 정확히 일치.
- **공통 필드.** `Device="AD"`, `Version="250601003"`, `Key="korail1234567890"` —
  `analysis/apktool/smali/com/korail/talk/network/BaseRequest.smali:10,12,14` 와 일치
  (`constants.py:4-6`, `mutation_payloads.py:68-73`).
- **로그인 비밀번호 변환.** 앱 `k5/b.java:124-140` / `BaseActivity.java:145-161`
  = `F4.a.encryptBase64( C0812l.encryptAES(key, pw) )`, 여기서
  `encryptAES` = AES/CBC/PKCS5Padding, key=`login.key` 바이트, IV=`key.substring(0,16)`,
  `Base64.encode(..., 0 = DEFAULT)`; `encryptBase64` = `Base64.encodeToString(bytes, 2 = NO_WRAP)`
  (`S4/C0812l.java:18-24`, `F4/a.java:43-45`).
  라이브러리 `crypto.py:41-54` 가 이중 base64(DEFAULT→NO_WRAP)를 정확히 재현
  (`base64.encodebytes` = 76자 줄바꿈 + 말미 개행 = Android DEFAULT).
  `pwdAESCphd != "Y"` 분기도 NO_WRAP 단독으로 일치.
- **Sid.** `C0812l.getSid()` = `encryptAES("2485dd54d9deaa36", "AD"+millis)` →
  Base64 DEFAULT. `crypto.py:12,56-63` 일치(키=IV=`2485dd54d9deaa36`, prefix `"AD"`).
- **DynaPath.** 헤더명 `x-dynapath-m-token`(`network/ExecuteDao$1.smali:146`)과
  allowlist 6경로(`ExecuteDao.java:27`: TicketReservation, NonMemTicket, ScheduleView,
  ScheduleViewSpecial, trn.prcFare.do, login.Login)가 `constants.py:420-430` 과 **정확히 일치**.
- **예약 폼 상수 전수 확인** (smali `W4/a.smali` / jadx `C5/a.java`):
  8개 승객행 `(psgTpCd, discKndCd)` = `(1,000)(1,P11)(3,000)(3,321)(1,131)(1,111)(1,112)(1,173)`
  — `W4/a.smali:93-401` 과 `mutation_payloads.py:82-91` 일치.
  `txtSeatAttCd1/2/3/5 = "000"` (`K4/q.DISABLE`, `K4/l.DEFAULT`, `K4/n.DEFAULT`, `K4/m.DISABLE`),
  `txtJrnyTpCd` 직통 `"11"` / 환승 `"14"` / 병합 `"21","22"`
  (`analysis/apktool/smali/K4/e.smali:40,68,96,124`),
  `txtJrnySqno` = `DecimalFormat("000")` → `"001"/"002"` (`S4/O.java:19-21` → `S4/N.java:32-38`),
  키 스펠링 `arvTm_1`(밑줄), `txtCardNo_1`(밑줄), `txtSeatAttCd4`/`txtSeatAttCd4_1`,
  `txtSrcarCnt`/`txtSrcarCnt1`, `txtSrcarNo{n}`/`txtSrcarNo1_{n}`,
  `txtSeatNo{n}`/`txtSeatNo1_{n}` — `OJrny.java`, `OSeat.java`, `OSrcar.java`, `OPsg.java`
  와 전부 일치.
- **병합예약(2차 홀드) 4개 차이점 전부 일치.** `DirectInquiryActivity.java:576-601`
  (jrnyTpCd 21/22 = 루프 인덱스, stndFlg 고정 `"Y"`, txtPsrmClCd2 = txtPsrmClCd1 복사,
  `setArvTm` 호출 없음 → `arvTm_1` 이 이전 입석홀드 값으로 잔류) —
  `mutation_payloads.py:294-480` 이 네 가지를 모두 재현.
- **N카드 구매/예약.** `NCardReservationDao$NCardReservationRequest.smali` 의 키 11종
  (`jrnyCnt, jrnyTpCd_, runDt_, trnNo_, dptRsStnCd_, arvRsStnCd_, apdUsrCnt, custMgNo_,
  apdCustName_, apdCustTeln_`)이 `mutation_payloads.py:1473-1580` 과 완전 일치.
  N카드 예약의 `txtMenuId="A2"`(`SeatAssignBookingActivity.java:159`),
  `txtDiscKndCd1="153"`(`W4/a.java:99`), `txtCardNo_1`(`OPsg.CARD_NO="txtCardNo_"`) 일치.
- **결제 `PaymentMethod` 키 접미사 규칙.** `hidStlMnsCd1` 등 인덱스 접미어는
  `network/request/payment/PaymentMethod.java:29-96` 의 `put(BASE + i)` 규칙 그대로.
  `hidStlMnsCd1="02"`, `hidCrdInpWayCd1="@"`, `hidInrecmnsGridcnt="1"`,
  `hidStlMnsSqno1="1"`(`V4/a.java:24-28`), `hiduserYn="Y"`(회원, `B6/AbstractC1269e.java:713-717`)
  — 전부 일치.
- **좌석 조회 폼.** `getSeatList` 의 `isArrow` 는 앱이 리터럴 `true`
  (`SearchSeatListDao.java:137`), `sidTest` 는 REAL 서버에서 `null`(→드롭),
  `ctlDvCd` 는 일반 예매 경로에서 `""`(`ui/seat/SeatSearchActivity.java:207`) —
  라이브러리 `payloads.py:210-218` 과 일치.
- **`myTicket.MyTicketList` 의 `tsRsStnCd`.** 앱에 세터 호출부 없음 → 드롭. 라이브러리도 미전송.
- **공통코드 부트스트랩 18종.** `IntroActivity.smali:1015-1190` 과 일치.
  앱의 19번째 `app.device.oreo` 는 `Build.VERSION.SDK_INT < 26` 조건부(`:1158-1168`)이므로
  SDK 35 를 표방하는 이 라이브러리가 빼는 것이 **옳다**.
- **운임 재계산(`PriceReCalculation`).** 6개 병렬 리스트의 순서
  (`psg_tp_dv_cd, hidDcntKndCd, dcnt_knd_cd1, hidDscpNo, psrm_cl_cd, hidFmlyNo`)가
  `CertificationService.smali:250-275` 선언 순서와 일치. 반복키 인코딩 판단도 맞다.
- **응답 파싱 키 537종 전수.** 앱 DTO 밖의 키를 읽는 곳 0건, 다른 DAO 의 키를 잘못
  끌어다 쓰는 곳 0건, 자바 원시타입/문자열과 파서 헬퍼의 불일치 0건.

---

## 5. 요약 표

| id | 분류 | 심각도 | 한 줄 | 1차 |
|---|---|---|---|---|
| P2INC-01 | risk | medium | 결제금액 출처 우선순위가 앱과 반대(`h_tot_rcvd_amt` 우선) | **신규** |
| P2INC-02 | risk | medium | 취소가 앱의 2단계 중 2단계만 호출 (`ReservationCancel` 부재) | **신규** |
| P2INC-03 | info | info | (오탐 철회) `reqSqno`↔`regSqno` DTO/wire 이름 불일치 + 앱의 `setTrnCnt` no-op — 둘 다 라이브러리가 옳음 | **신규(함정 기록)** |
| P2INC-04 | incorrect | low | 취소 `txtJrnyCnt` 제로패딩 손실 (`"0001"`→`"1"`) | **신규** |
| P2INC-05 | incorrect | low | 환불 `latitude`/`longitude` 항상 `""`, 앱의 10필드 shape 미재현 | **신규** |
| P2INC-06 | unverifiable | info | `P100` 빈결과 허용에 APK 근거 없음(앱은 오류 처리) | **신규** |
| P2INC-07 | incorrect | medium | `installment` 기본값 `"00"` vs 앱 `"0"` | K5-03 (low→medium) |
| P2INC-08 | incorrect | high | 환불 `tk_ret_tms_dv_cd`/`pbpAcepTgtFlg` 고정값 | K6-02/K6-03 |
| P2INC-09 | partial | low | `txtSeatAttCd4` 항상 `"015"`, 자유석 `"003"` 미재현 | K3-06 |
| P2INC-10 | risk | medium | dry-run 미리보기에서 `hidRsvChgNo` 미마스킹 | K5-02 |
