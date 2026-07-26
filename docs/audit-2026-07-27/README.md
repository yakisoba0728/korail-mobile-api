# 코레일톡(Korail Talk) ↔ korail-mobile-api 전수 감사 — 최종 종합

작성 2026-07-27 · 대상 저장소 `/Users/yakisoba/Documents/GitHub/korail-mobile-api`
앱 근거 `analysis/jadx/sources/`(가독) + `analysis/apktool/smali*/`(상수·제어흐름 authoritative)
라이브러리 근거 `src/korail_mobile_api/`

감사 파이프라인: 1차 8에이전트(영역 분할) → 2차 4에이전트(전체 재확인, 4개 렌즈) →
3차 4에이전트(반증 시도). 3차에 84건이 올라가 **72건 확정 / 10건 기각 / 1건 판정불가 /
1건 통제 카나리**로 정리됐다. 이 문서는 **살아남은 72건**만 종합한다.
기각된 10건은 §8에 이름만 남긴다(다시 살리지 말 것).

---

## 1. 한눈에

### 1.1 규모

| 지표 | 값 | 근거 |
|---|---:|---|
| 앱 API 카탈로그(고유 엔드포인트) | **165** | `docs/api-status-by-service.md:11-15` (저장소 자체 집계: 성공 32 / 실패 13 / 미실행 120) |
| 라이브러리가 전송 가능한 라우트 | **66** | 본 세션 기계 실측 — read 58 + mutation 8 (`safety.py` `KORAIL_READ_ONLY_ROUTES` / `KORAIL_MUTATION_ROUTES`) |
| 공개 클라이언트 메서드 | **74** | 본 세션 `inspect` 실측 (`client.KorailClient`) |
| 요청 필드 정확집합 핀(EXACT pin) | **45** 경로 | 본 세션 실측 (`safety.KORAIL_EXACT_REQUEST_FIELDS`) — read 58 중 13개는 핀 없음 |
| 1차 8슬라이스 추출 행 수 | 174 | **중복 포함 행 수이며 고유 엔드포인트 수가 아니다** (아래 주의) |

> **174를 총계로 쓰지 말 것.** 슬라이스 경계에서 같은 엔드포인트가 여러 번 세어졌다:
> `certification.TicketReservation`(01·03), `reservationCancel.ReservationCancelChk`(01·03·06),
> `certification.PriceReCalculation`(01·03), `reservationWait.ReservationWait`(03·04),
> 리무진 2건(01·08). 또 슬라이스마다 "구현" 판정 규칙이 달랐다(08-core는 `client.py`에서
> 실제 도달 가능한 것만, 05-pay는 16개 중 2개만). 따라서 구현 수도 합산하지 말고
> §2의 영역별 표로만 읽어야 한다. 신뢰할 수 있는 총계는 위 표의 165 / 66 / 74뿐이다.

### 1.2 확정 결함 72건 심각도 분포

| 심각도 | 건수 | 비고 |
|---|---:|---|
| critical | **0** | 안전게이트 우회·카드정보 유출 경로 없음 (§1.3) |
| high | **3** | 전부 **환불 에코 1개 루트**의 3중 발견 (K6-02 / P2INC-08 / P2CRO-12) |
| medium | **5** | K5-01, K6-03, P2SAF-01, P2SAF-08, P2CRO-01 |
| low | **38** | |
| info | **26** | 문서화된 이연·긍정결과·방법론 기록 등 결함 아닌 것 포함 |

**중복 제거하면 실제 루트는 훨씬 적다.** 72건 중:
- high 3건 = **환불 폼 에코 누락** 1루트 (+ medium K6-03이 같은 루트의 파서측)
- 마스킹 8건(K5-02·P2SAF-01·P2SAF-02·P2SAF-05·P2SAF-08·P2INC-10·P2CRO-04·P2CRO-13)
  = **`redaction.SENSITIVE_KEYS`의 완전일치 매칭 + 철자 누락** 1루트
- 할부 상수 3건(K5-03·P2INC-07·P2CRO-14) = 1루트
- 취소 docstring 3건(K3-07·P2MIS-04·P2SAF-12) = 1루트
- 자유석 좌석속성 2건(K3-06·P2INC-09) = 1루트
- 핀 없는 read 라우트 2건(P2MIS-03·P2SAF-03) = 1루트

### 1.3 critical 0건의 근거 (긍정 결과)

두 건의 **기계적 전수 검사**가 게이트에 구멍이 없음을 확인했다. 이것이 이 라이브러리를
신뢰할 수 있는 이유이므로 결함 목록보다 먼저 적는다.

- **P2SAF-13** — 안전게이트 핵심 불변식 8종을 저장소 밖에서 재계산: 뮤테이션 라우트 8 ↔
  카테고리 매핑 8 대칭차 공집합; consent 플래그 6 ↔ 라우트 카테고리 6 전단사;
  read(58) ∩ mutation 경로 레벨까지 공집합(메서드만 바꿔 우회 불가);
  ORDERS/OPTIONAL 키는 전부 EXACT의 부분집합(고아 0);
  `require_mutation_consent` 실호출 12건 ↔ `post_mutation_form` 11 + `get_mutation_query` 1 = 12 대응,
  다른 전송 경로 grep 0건; `P058`(세션만료)는 `raise_on_fail=False`여도 무조건 raise
  (`http.py:36-42`) → 결제 경로에서 세션만료가 성공으로 오인되지 않음.
- **P2CRO-11** — `KORAIL_EXACT_REQUEST_FIELDS` 45개 핀 전수를 앱 Retrofit 애너테이션과 기계 대조:
  **핀에는 있으나 앱에 없는 필드 0건**. 남은 8건은 전부 상수 참조 미해석이었고
  `C1262b.{DPT_DT,DPT_TM,ARV_RS_STN_CD,TRAIN_NO}`=`dptDt/dptTm/arvRsStnCd/txtGoTrnNo`로 해소.
  앱에는 있으나 핀에 없는 필드는 6경로뿐이며 전부 근거 있음(write 오버로드 차단, 디버그 필드,
  앱도 안 채우는 필드, 앱 자체 자기대입 버그 `trnCnt`, P2CRO-05로 별도 보고).

추가로 예약 생성 핵심 상수는 **smali로 직접 재확인**되어 전부 일치했다(03-reserve §2):
`K4/e.smali:36-140` 직통 `"11"`·환승 `"14"`·병합선행 `"21"`·병합후행 `"22"`,
`U4/a.smali:1250-1256` standby 플래그 `" 9"`(앞 공백, jadx는 이 메서드를 스텁으로 렌더),
`w4/a.java:46-73` 8개 승객행 `psgTpCd`/`discKndCd` 1:1 바이트 일치.

---

## 2. 있는 것 — 앱에 있고 라이브러리에 올바르게 구현된 기능

영역별 커버리지(1차 슬라이스 기준, 판정 규칙이 슬라이스마다 다르므로 합산 금지).

| 영역 | 앱 추출 | 구현 | 대표 구현 항목 |
|---|---:|---:|---|
| 01 인증·세션 (`login`,`cust`,`nFilter`,`certification`) | 25 | 10 | 수동/자동 로그인, 로그아웃, 다자녀 할인대상, 예약상세, 운임재계산, 회원 좌석 hold, 리무진 스케줄·잔여석, 홀드 취소확인 |
| 02 열차조회·시간표·운임 (`trainsInfo`,`schedule`,`research`,`product`) | 22 | 17 | 자유석 차량안내, 운임조회(prcFare), 환승역, 운행달력, 좌석배정 스케줄, 좌석도(객차/좌석), 통근열차정보, 여정편의설정, 병합좌석, N카드 사용내역·스케줄·구매·연장, 여행상품 목록·상세 |
| 03 예약(일반·장바구니·환승·병합) | 16 | 10 | 좌석속성 안내, 예약내역, 장바구니 목록, 일반/환승/병합 예약 생성, 예약대기 확정, 미결제 홀드 취소, 운임 재계산 |
| 04 예약대기·승차권 조회 | 23 | 8 | 예약대기 신청, 배송수령고객, MAAS 내역, 승차권 변경가능일, PBP 인수사양, 승강장번호, 최근배송이력, 승차권 중복확인 |
| 05 결제·영수증 | 16 | 2 | 카드 단독 결제(`payment.ReservationPayment`), 영수증 조회(`receipt.ReceiptInfo`) |
| 06 취소·환불·보상 | 21 | 4 | 홀드 취소(ReservationCancelChk), 환불대상 상세, 환불 수수료 조회, 환불 실행 |
| 07 정기권·패스·포인트·기프트 | 25 | 9 | 정기권 스케줄·발매가능일·메뉴, 트립메뉴, 지연할인권 목록, 할인쿠폰 목록, 코레일포인트 요약, 마일리지 내역, 기프티켓 목록 |
| 08 부가서비스·공통·방어계층 | 26 | 13 | 공통코드, UUID, MAAS 메뉴·역목록, 전체역·역정보, 3개 캐시, 승무원호출 사유목록, 통근종류 메뉴, 열차조회(ScheduleView), 리무진 조회 |

### 2.1 필드 단위로 "완전 일치"가 확인된 대표 사례

정확도를 판단할 근거이므로 남긴다(전부 1차에서 필드 전수 대조).

- **로그인**: 타입코드 `"2"/"4"/"5"`(smali `StbkAcntDao.smali:18,24`), 성공코드
  `{IRZ000001,S200}`(`S4/u.java:130-132`), 비밀번호 이중 인코딩(AES/CBC/PKCS5 + 이중 Base64,
  `S4/C0812l.java:18-24` + `F4/a.java:43-45` ↔ `crypto.py:41-52`),
  continuation POST 데이터 29필드 순서(`LoginDao.java:82-110` ↔ `session.py:76-94`).
- **공통 상수**: `Device="AD"`, `Version="250601003"`, `Key="korail1234567890"`
  (`BaseRequest.java:7,14` ↔ `constants.py:4-6`).
- **운행달력** 12/12 필드, **여정편의설정** `mainList[]` 31/31 필드,
  **N카드 스케줄** `trnScdlList[]` 15/15, **MAAS 상세** 20/20, **역데이터 STN** 10/10.
- **함정 회피 확인**: 리무진 스케줄의 wire 이름은 DTO 필드명 `trnGpCd`가 아니라
  `@Field("tmGpCd")`인데 `limousine_payloads.py:88`이 정확히 `tmGpCd`를 쓰고,
  좌석조회(`:107`)는 진짜 `trnGpCd`를 써서 둘을 구분한다.
  동일 계열 함정을 P2INC-03이 재확인: `ConvenienceSettingRequest`의 DTO 필드는 `reqSqno`인데
  wire는 `@Field("regSqno")` — 라이브러리(`read_payloads.py:797-802`)가 옳다.
- **앱 자체 버그까지 재현**: `Price2FareRequest.setTrnCnt`가 smali에서 `iget→iput` 자기대입
  no-op(`Price2FareDao$Price2FareRequest.smali:149-162`)이라 앱은 `trnCnt`를 절대 못 보낸다.
  라이브러리도 이 키를 만들지 않아 **일치**한다.
- **카드결제 필드 14종** 전부 일치(§4 K5-03의 `installment` 하나만 예외):
  `hidPnrNo/hidWctNo/hidTmpJobSqno1,2/hidRsvChgNo/hidInrecmnsGridcnt/hidStlMnsSqno1/
  hidStlMnsCd1="02"/hidMnsStlAmt1/hidCrdInpWayCd1="@"/hidStlCrCrdNo1/hidVanPwd1/
  hidCrdVlidTrm1/hidAthnDvCd1="J"/hidAthnVal1/hiduserYn="Y"`.

---

## 3. 없는 것 — 앱에 있는데 라이브러리에 없는 기능

### 3.1 문서화된 이연 (결함 아님 · 확인만)

| 묶음 | 개수 | 근거 |
|---|---:|---|
| 셀프 체크인 (`checkin.info/psbFlg/reg/cnc.do`) | 4 | `README` "Check-in … Not implemented", `RELEASE_GAP_PLAN.md:421-427` |
| MAAS 부가서비스 취소 (`addService.cancelPay.do`,`coptCnc.do`,`maas.cncFee.do`) | 3 | `RELEASE_GAP_PLAN.md:440-448` |
| 특실 업그레이드 (`reqUpgradeSeat`,`procUpgradeSeat`) | 2 | 동상 + G7 |
| 지연·운행중지 보상 (`compensate`×3, `delay`×8) | 11 | `RELEASE_GAP_PLAN.md:440-444` "delay/compensate refunds (11 endpoints)" — **K6-04 정정: `dlay.dptnBank.do`는 이미 구현됨**(`safety.py:91`, `client.py:476`, `read_parsers.py:709-716`)이라 미구현은 12가 아니라 11이고 그 11이 정확히 문서의 11이다 |
| PG WebView 간편결제·포인트·계좌·통합결제 | 14 | `RELEASE_GAP_PLAN.md:337-390` "헤드리스 라이브러리 범위 밖" (Payco/네이버/카카오/토스/삼성/신한/모니모/세틀뱅크/제로페이/Paybooc/KB Pay, `pay.intgStl.do`, 현금영수증 발급) |
| 회원관리 (`userCheck`,`loginAthnReg/Rmv`,`joinCfm`,`mbSced`) | 5 | K1-01 · `full-api-analysis-2026-07-20.md:2692-2696`, `RELEASE_GAP_PLAN.md:442-447` (`memberDrop`은 비가역 탈퇴라 배제가 안전모델과 일치) |
| 할인자격 인증 (장애인/국가유공자/국회의원/공공기관) | 6 | K1-04 · **`README.md:326-331`이 주민번호·증서번호 전송을 이유로 명시 제외 선언**, `applyDisabilityCertification`은 `safety.py:62-68` + `read_payloads.py:1556-1567` 핀으로 차단 |
| 기프티켓/선물 write (`gift.gdRsv/gdRet/gdUseSpec`, `giftInfo.GiftSend`) | 4 | `RELEASE_GAP_PLAN.md:137`(G10), `:441-448` |
| 포인트/마일리지 write, 외부제공자 비밀번호 조회 | 5 | `safety.py:17-35` `points-mileage-write` (`mlg.lpotAthn.do`·`xPoint.XPointView`는 응답에 `pwdErrTno` 오류횟수 카운터가 있어 잘못된 시도가 외부 계정 상태를 바꿈) |

### 3.2 계획됐으나 구현되지 않음 (실질 갭)

| 엔드포인트 | 왜 필요한가 | 난이도 | 근거 |
|---|---|---|---|
| `refunds.verifyOnlineRefunds` / `executeOnlineRefunds` | 회원 로그인 없이 반환번호 4분할+신청자명으로 하는 별도 환불 플로우. `RELEASE_GAP_PLAN.md:400-402,449-450`이 "Flow D — Refund"의 5개 중 2개로 v1 코어에 카운트했으나 3/5만 구현 | 중 (비회원 신원 모델 필요, §3.4와 같은 뿌리) | K6-01 · `RefundService.java:15-17,31-33`, `RefundVerifyTicketDao.java:13-62`, `RefundExecuteTicketRefundDao.java:11-108`, 호출부 `S5/c.java:64-208`·`S5/h.java:50-193` / src grep 0건 |
| `ticket.tripChgHndgCnc.do` | 승차권 변경 롤백(묶음결제 대상 취소). Flow B 4개 중 `ReservationCancelChk`만 구현되고 나머지 3개(`ReservationCancel` 의도적 생략, 이것, `product.ReservationCancel`) 부재 | 중 | K4-03 · `TCCancelDao.java:10-46`, `TicketService.java:98-100` / 문서 등재는 있음(`api-status-by-service.md:544`, `api-endpoints.md:364`), `RELEASE_GAP_PLAN.md:867` P4 미체크 |
| `cart.addCartList` | 장바구니 "담기". 현재 목록 조회만 있어 워크플로가 읽기전용으로 끝남 | 하 (`hidPnrNo` 1필드) | K3-01 · `CartService.java:11-13`, `AddCartDao.java` / `api-status-by-service.md:180` 미실행 등재 |
| `maas.rsvStt.do` | MAAS 연계상품 결제 전 상태확인 | 하 (4필드) | K3-02 · `CartService.java:19-21`, `VerifyMaasStatusDao.java:11-60` / `api-status-by-service.md:182` |
| `reservation.tripChgPrsC.do` | 결제완료 승차권의 열차·좌석 변경(예약 생성). 정기권/단체예약과 무관한 정상 범위 기능 | 상 (R* FieldMap 6개 + 선행 read `tripChgOgtk.do`) | K3-03 · `ReservationService.java:23-25`, `TCReservationDao.java` / `RELEASE_GAP_PLAN.md:278,867` |
| `reservation.reservationChange.do` | 예약 인원 변경 | 상 (R* FieldMap 5개) | K6-05 · `BusReservationService.java:23-25`(선언 위치 주의: `ReservationCancelService`가 아님), `ReservationChangeDao.java` / `RELEASE_GAP_PLAN.md:277,867,1012` |
| `push.update` | 푸시 수신 플래그 갱신. **K8-04 정정**: 같은 묶음의 `push.callCrew.do`는 `README.md:344-347`이 명시 제외하고 `tests/test_p0_menu_reads.py:64`가 부재를 테스트로 고정 — 실제 미문서 갭은 `pushUpdate` 하나뿐 | 하 | K8-04 · `PushService.java:22-23`, `PushUpdateDao.java:12-142` |
| AddService 5종 (`addService.reserve/buyConfirm/reserveList.do`, `addSrv.helpSrvCust/helpSrvTk.do`) | 휠체어·도움서비스 신청, 특송 구매확정, 부가서비스 목록. 3개는 write(v1 범위 밖), 2개는 read 갭 | 중 | K8-01 · `AddService.java:16-34` / `api-status-by-service.md:131-139` 전부 미실행 |
| `tk.gurdSmsSnd.do`, `tk.pbpWdrw.do`, `tk.dvcInfoInit.do` | 보호자 안심문자 발송 / PBP 인수 철회 / 열람기기 초기화. **전부 write**이고 8개 뮤테이션 allowlist 밖인 것이 설계와 일치 | 하~중 | K4-05(`api-status-by-service.md:535` 등재), K4-06(`:537`, `api-endpoints.md:357`), K4-07(jadx는 호출부 미복호화, smali `TicketListActivity.smali:5355-5735`로 실사용 확인) |
| `mileage.acpnMlgSpec.do` | 동반 마일리지 PNR별 내역(순수 조회, 비밀번호 없음). **K7-01 정정**: "문서 어디에도 없다"는 반증됨 — `api-status-by-service.md:323`이 사유("결제/포인트/금전성 API")까지 기재. 다만 `safety.py:24-28` 사유주석 5개·`tests/test_loyalty_reads.py:44-50` WITHHELD 5개·`RELEASE_GAP_PLAN` G1~G12에는 미등재 | 하 (요청 1필드) | `MileageService.java:19-21`, `AcpnMlgSpecDao.java` |

### 3.3 읽기 갭(G 시리즈) — 상태 정정 포함

`docs/RELEASE_GAP_PLAN.md:128-139`의 G1~G12를 라우트 집합과 전항목 기계 대조한 결과
(**P2CRO-08**), 문서가 낡았다:

- **이미 닫힌 갭 4 + 부가 2**: G2 `research.dcntCrdScheduleView.do`(`safety.py:177-180`),
  G3 `ticket.dcntCrdUseQry.do`(`:176`), G11 `login.Logout`(`:76` — 문서는 "로컬 쿠키만 지운다"고
  적었으나 `session.py:252-268`이 실제 서버 GET을 발행), G12 `certification.ReservationList`
  (+`safety.py:1028-1030` 4필드 핀), `xPoint.MyXPointView`(`:168`), `mlg.amtSpec.do`(`:169`).
- **문서대로 실제 미구현**: G1, G4 `research.tripChgOgtk.do`(승차권변경 선행 원표조회),
  G5 `trainsInfo.TourTrainSpecialRoom`(파서·모델만 있고 빌더·client 없음),
  G6 `self.seatChgInfo.do`(K4-04 — 자율 좌석/열차 변경 옵션, **읽기 전용**이라 README의
  "destructive ticket operations" 제외 문구에도 안 걸림), G7, G8, G9 `product.payInfo`,
  G10, `xPoint.XPointView`, `railplus.autoCharge.do`.

### 3.4 근본 원인 하나: 비회원 세션 미모델링

`hidName`/`hidTeleNo`/`hidPwd`가 `src/` 전체에 0건이고 `session.py`에 비회원 신원 상태가 없다.
이 하나가 여러 갭을 만든다: 승차권 목록의 비회원 3필드(K4-08),
`deviceReset`의 `teln/custNm/nonMbPwd`(K4-07), 오프라인 반환번호 환불(K6-01),
비회원 예약(`nonMember.NonMemTicket`), 비회원 운임재계산 `hidCustNo`의 출처(K3-05).
README/`RELEASE_GAP_PLAN`에 "비회원 미지원" 선언이 없으므로 **범위 결정이 필요한 항목**이다.

---

## 4. 수정이 필요한 것

교정 심각도 순. 3차에서 하향된 항목은 하향 사유를 함께 적는다(적지 않으면 다음 감사자가
다시 올린다).

---

### 4.1 [high · 루트 1개 / 발견 3회] 환불 폼이 서버 에코값 3개를 버리고 고정값을 보낸다

**ID**: K6-02(1차) · P2INC-08(2차 오구현렌즈) · P2CRO-12(2차 교차검증) — 동일 결함,
서로 다른 증거를 보탰다. **K6-03(medium)**이 같은 루트의 파서측 결함.

**앱 근거**
- `ui/ticket/ticketReturn/a.java:427-428` — `RefundCommissionResponse.getTk_ret_tms_dv_cd()`를
  그대로 `setTk_ret_tms_dv_cd()`로 에코
- `ui/ticket/ticketReturn/a.java:430-431` — `TicketDetailResponse.getH_pbp_acep_tgt_flg()`를
  그대로 `setPbpAcepTgtFlg()`로 에코
- `ui/ticket/ticketReturn/a.java:420` `setH_mlg_stl(r9)` — 인자는 `:185-190`의
  `prg_psb_flg=="M" && use_psb_mlg_num >= 수수료`로 결정(`I0()`="N", `Q0()` i9==102→"Y")
- **smali 확정**(P2INC-08): `apktool/smali/com/korail/talk/ui/ticket/ticketReturn/a.smali:3141-3155`
  및 `:3161-3165` — 에코에 변환 없음
- 상수: `I4/a.java:5-6` `BEFORE_DEPARTURE="21"` / `AFTER_DEPARTURE="15"`
  (smali `I4/a.smali:7,9` 재확인)
- 전송: `dao/refund/RefundService.java:29`(14 @Field), `dao/refund/RefundDao.java:145`
- 교차: `TicketListActivity.java:970`도 같은 에코

**라이브러리 근거**
- `mutation_payloads.py:1454` `"h_mlg_stl": "N"`, `:1455` `"tk_ret_tms_dv_cd": "21"`,
  `:1457` `"pbpAcepTgtFlg": "N"` — 전부 무조건 고정, override 인자 없음
- `client.py:2016-2046` `refund()`는 `PaidTicket` 외 입력을 받지 않음
- **값을 이미 읽어오고도 버린다는 증명**: `read_models.py:1183-1204` +
  `read_parsers.py:2627-2649`가 `ticket_return_times_division_code` /
  `proceed_possible_flag` / `usable_mileage`를 정확히 파싱한다
- **읽을 방법조차 없는 것**(K6-03): `read_parsers.py:2679-2698`
  `_REFUND_TICKET_DETAIL_FIELDS`에 `h_pbp_acep_tgt_flg` 매핑 없음(`src/` grep `pbp_acep` 0건).
  같은 이유로 `h_dlay_flg`·`h_dlay_tk_flg`(`dao/refund/TicketDetailDao.java:242-243`),
  `mlgSaveFlg`(`:266`), `addSrvFlg`/`addSrvCancel`(`:228-229`)도 함께 누락

**무엇이 틀렸나**: 출발 후 환불(`"15"`), 마일리지 정산 대상 환불(`"Y"`),
PBP 대상 승차권 환불(`"Y"`)에서 앱이 절대 만들지 않는 조합이 서버로 나간다.
서버가 이 필드를 신뢰하는지 재계산하는지는 미검증이지만, **읽어온 값을 버린다**는 사실 자체는
서버 동작과 무관하게 확정적이다. 게다가 `refund()`는 저장소에서 **실서버 성공 봉투가 없는
유일한 금전 경로**(`docs/verification-record.md:53`)라 회귀를 잡아줄 안전망도 없다.

**고치는 법**
1. `_REFUND_TICKET_DETAIL_FIELDS`에 `pbp_acceptance_target_flag: "h_pbp_acep_tgt_flg"`
   (및 delay/addSrv/mlgSave 플래그 5개) 추가
2. `build_refund_form`/`refund()`에 `ticket_return_times_division_code`,
   `use_mileage: bool`, `pbp_acceptance_target_flag` 선택 인자 추가.
   미지정 시에만 현재 기본값 유지
3. `get_refund_commission()` → `refund()` 값 전달 경로를 docstring에 명시

---

### 4.2 [medium] 프리뷰 마스킹이 실명·휴대폰·고객관리번호를 평문으로 남긴다

**ID**: P2SAF-01 (+ 문서 반증 P2SAF-08)

**앱 근거**: `dao/research/NCardReservationDao.java:16` `APD_CUST_NAME="apdCustName_"`,
`:29` `CUST_MG_NO="custMgNo_"`, `:30` `APD_CUST_TEL="apdCustTeln_"`,
`:66-72,:122-124` `apdUsrInfo.put(prefix + i9, str)`;
라우트 `dao/research/ResearchService.java:68-70`

**라이브러리 근거**: `mutation_payloads.py:1568` `form[f"custMgNo_{index}"]`,
`:1572` `apdCustName_{index}`, `:1576` `apdCustTeln_{index}`;
`redaction.py:340` `sensitive = name.casefold() in SENSITIVE_KEYS` (**완전 일치**);
`:29 "custMgNo"`, `:32 "acepCustNm"`, `:33 "acepCustTeln"`만 등재 — 인덱스 접미 철자는 0건;
`consent.py:131`

**실측**: `redact_payload({"custMgNo_1":"1234567890","apdCustTeln_1":"01012345678","apdCustName_1":"홍길동"})`
→ 세 값 모두 평문 통과. `custMgNo`(무인덱스)만 `[REDACTED]`.
한글 이름·11자리 번호는 `CARD_RE`(13~19자리)에도 안 걸린다.

**무엇이 틀렸나**: `dry_run=True`(기본값) 프리뷰 객체 안에 **실명+휴대폰+고객관리번호가
한 묶음**으로 보존되어 그 자체로 재식별 가능하다. 같은 파일이
`txtCardNo_1..9`/`txtSrcarNo1..9`/`txtSeatNo1..9`는 인덱스 전개로 등재해 둔 것
(`redaction.py:154-161,194-197`)과 대비된다. 의미상 동일한 다른 철자
(`acepCustNm`/`acepCustTeln`/`custMgNo`)는 이미 등재되어 있으므로,
**코드베이스가 이미 내린 판단이 접미사 하나 때문에 무효화**된 것이다.
`README.md:209-211`의 "forced through `redact_payload` … so it **can never** hold a raw
card number, PNR or other identity"를 깬다(P2SAF-08).

**고치는 법**: `redact_payload`를 `키_숫자` 접미 정규화 매칭으로 전환(근본적).
차선책은 세 키를 인덱스 전개로 등재. 아래 4.3·4.4와 **한 번에 닫힌다**.

---

### 4.3 [low · 같은 루트] 마스킹 철자 누락 3종

같은 완전일치 매칭 문제의 나머지 사례. 개별 심각도는 low지만 4.2와 묶어 한 번에 고쳐야 한다.

| 키 | 무엇인가 | 앱 근거 | 라이브러리 근거 | ID |
|---|---|---|---|---|
| `saleDd` | 반환번호 4분할 자격증명의 한 조각(판매일자). 나머지 3조각은 마스킹됨 | `ResearchService.java:65-66` @Query 4종; `TicketListActivity.java:1066-1073` 조립; `TicketReceiptActivity.java:431` `getReturnNumberWithDash(...)`가 인쇄된 반환번호 | `mutation_payloads.py:1618` 전송 / `redaction.py:25 tkRetPwd, :26 saleWctNo, :27 saleDt, :28 saleSqno` — **`saleDd` 없음**(같은 값의 다른 철자 `saleDt`는 있음). 테스트 `tests/test_discount_card_mutations.py:267-271`은 비밀번호만 확인해 통과 | P2SAF-02 · P2CRO-04 |
| `hidRsvChgNo` | 결제 폼 신원 튜플 5개 중 4개는 마스킹되는데 이것만 누락 | `dao/payment/PaymentService.java:12-14` @Field; 값 출처 `V4/b.java:41` `getJrny_infos()...getH_rsv_chg_no()` (예약별로 달라짐) | `mutation_payloads.py:1398` 삽입 / `redaction.py`에 `hidPnrNo:24`, `hidWctNo:141`, `hidTmpJobSqno1,2:142-143`, 읽기철자 `h_rsv_chg_no:111`, `reservation_change_no:65`는 있으나 `hidRsvChgNo` grep 0건. 테스트 `tests/test_real_card_payment.py:355-390`의 `_hold()`가 `journeys=()`라 값이 항상 상수 `"000"`이 되어 결함을 우연히 은폐 | K5-02 · P2INC-10 · P2CRO-13 |
| 로그인 응답 `str*` PII | `strCpNo`(휴대폰)/`strCustNm`(실명)/`strBtdt`(생년월일)/`strEmailAdr`/`strMbCrdNo`/`strCustNo`/`encryptCustNo` | `dao/login/LoginDao.java:84,93,94,99,100,102,107` | `session.py:29-58` `KORAIL_LOGIN_CONTINUATION_FIELDS`가 전부 열거, `:76-93`이 `key=value&`로 직렬화, `:216-224`가 그 문자열+raw를 `KorailAuthContinuationRequired`로 던지고 `:169` `self.pending`에 보관, `:248-254` `KorailSession(raw=response.raw)`로 전량 보존. `redaction.py:35`에는 `mbCrdNo`만 있고 `session.py:233-235`는 두 철자를 다 읽는다 → **같은 값이 어느 철자로 오느냐에 따라 마스킹 여부가 갈린다** | P2SAF-05 |

**하향 사유(참고)**: `saleDd`는 나머지 3/4가 마스킹돼 반환번호 복원 불가,
`hidRsvChgNo`는 3자리 예약변경 차수라 엔트로피가 사실상 없음,
로그인 PII는 능동 유출 경로 없음(호출자 본인 정보). 그래서 medium이 아닌 low다.
단 `SECURITY.md:7`이 "raw responses를 공개하지 말라"고 요구하면서 정작 위생처리 수단이
이 필드들을 덮지 않는다는 모순은 남는다.

---

### 4.4 [medium] 영수증 응답의 현금영수증 정보(`cash_rcet_info`) 미파싱

**ID**: K5-01

**앱 근거**: `dao/receipt/ReceiptDao.java:11-40` `class CashReceiptInfo`
(`h_apv_mtd_nm`, `h_athn_dmn_rcgn_no`, `h_cash_rcet_apv_no`, `h_cash_rcet_txn_dv_cd`,
`h_tot_apv_amt:int`), `:43-44` `cash_rcet_info: List<CashReceiptInfo>`, `:74-76` getter

**라이브러리 근거**: `read_models.py:184-213` `TicketReceipt`에 대응 필드 0개;
`read_parsers.py:1013-1140` `parse_ticket_receipt_response`가 `:1027`에서 `stl_info`만 순회;
`src/` 전체 `cash_rcet` grep 0건

**무엇이 틀렸나**: 같은 레벨의 `stl_info`(일반 결제수단)는 `ReceiptPayment` 8필드로 정확히
파싱되는데 `cash_rcet_info`만 대응 dataclass가 없다. `:1136` `raw=item`으로 원본은 보존되나
`stl_info`와 동급인 중첩 리스트 구조체 **전체**에 모델이 없어 구조화 판독이 불가능하고,
현금영수증이 발급된 영수증만 사일런트하게 비어 보인다.

**고치는 법**: `ReceiptCashPayment`(5필드) dataclass 추가 후 `stl_info`와 동일 패턴으로
`cash_rcet_info`를 순회해 `TicketReceipt.cash_receipts`로 노출.

---

### 4.5 [medium] `PaidTicket.sale_date` 문서가 반대로 되어 있어 변경이력 승차권 환불이 틀린 식별자로 나간다

**ID**: P2CRO-01 (원 high → **medium** 하향: 자동 오채움 코드 경로가 없어 **호출자 오용
조건부**이기 때문)

**앱 근거**: 환불 폼의 `h_orgtk_sale_dt`에는 **현재 승차권의 `h_sale_dt`**가 들어간다 —
`ui/ticket/ticketReturn/a.java:412-413` `r5.setH_orgtk_sale_dt(r3.getH_sale_dt())`,
`TicketListActivity.java:965` 동일(독립 2곳). 대비: 읽기 3종은 `h_orgtk_ret_sale_dt`를 쓴다
(`TicketListActivity.java:904`, `ticketReturn/a.java:352`,
`TicketReceiptActivity.java:402` `setH_orgtk_sale_dt(getH_orgtk_ret_sale_dt())`).

**라이브러리 근거**: `mutation_models.py:337` `sale_date: str = field(repr=False)  # h_orgtk_sale_dt`,
`:319-321` docstring "the original-ticket sale window/date/sequence";
`mutation_payloads.py:1450`; 대비 `read_parsers.py:2681`(`sale_date`←`h_sale_dt`),
`:2684`(`original_sale_date`←`h_orgtk_ret_sale_dt`)

**무엇이 틀렸나**: 필드명 `sale_date`와 wire명 주석은 정확한데 **docstring이 "원표 판매일"이라
서술**해, 호출자가 `detail.original_sale_date`나 수수료 조회에 쓴
`OriginalTicketReference.sale_date`를 그대로 재사용하도록 유도한다.
미변경 승차권에서는 두 값이 같아 조용히 통과하고, 변경/재발권 이력이 있으면 4분할 식별자가
어긋난다. 4.1과 마찬가지로 실서버 성공 봉투가 없는 경로다.

**고치는 법**: `PaidTicket.sale_date` docstring을 `h_sale_dt`로 정정하고
`RefundTicketDetailResponse` → `PaidTicket` 변환 헬퍼를 제공해 오용 자체를 차단.

---

### 4.6 [medium] README·SECURITY의 "프리뷰는 신원을 절대 담지 않는다"가 3건으로 반증됨

**ID**: P2SAF-08 — 4.2·4.3의 문서측 귀결. `README.md:209-211`의 "**can never** hold a raw
card number, PNR or other identity" 중 카드번호·PNR은 실제로 마스킹되지만 **identity 부분이
거짓**이다(실명·휴대폰·`saleDd`·`hidRsvChgNo`).
**고치는 법**: 4.2·4.3을 먼저 고치면 문장을 그대로 둘 수 있다. 고치지 않는다면
"등재된 키에 한해"로 약화해야 한다.

---

### 4.7 [low] 상수·기본값 드리프트

| 항목 | 앱 값 | 라이브러리 값 | 근거 | ID |
|---|---|---|---|---|
| 카드 일시불 할부코드 | `"0"` (한 자리) | `"00"` | smali `K4/h.smali:44-52` `INS_0` 생성자 `const-string v2, "0"`; 나머지 무패딩(`:76 "2"`, `:104 "3"`, `:132 "4"`, `:160 "5"`, `:188 "6"`, `:216 "12"`, `:244 "24"`). 전송 `V4/a.java:238-262 getInstallmentType()→getCode()` → `:32 setHidIsmtMnthNum(1,…)` → `PaymentMethod.java:60-61`이 키 조립. APK에 이 필드로 `"00"`이 가는 경로 없음 / `mutation_models.py:311`, `mutation_payloads.py:1407` | K5-03 · P2INC-07 · P2CRO-14 |
| 자유석 좌석속성 | `"003"`(`K4/p.smali:75 NORMAL_FREE`) 조건부 | 항상 `"015"` | `C5/a.java:85-97`: `S4/J.isFreeSeat(cabin,genCd,freeCd)` = `GENERAL && genCd=="13" && freeCd=="11"`이면 `"003"`. `S4/J.java:57-59` / `mutation_payloads.py:841,854`(직통·환승), `:431,436`(병합) 전부 `"015"` 고정, 파일 전체 `free_reservation_code` 참조 0건(`models.py:343`에 파싱은 됨) | K3-06 · P2INC-09 |
| 취소 폼 `txtJrnyCnt` 제로패딩 | `"0001"` 그대로 에코 | `"1"`로 벗겨짐 | `DReservationConfirmActivity.java:273` `setTxtJrnyCnt(response.getH_jrny_cnt())` / `mutation_payloads.py:1233 legs=int(...)`, `:1249 str(legs)` | P2INC-04 |

**할부코드 하향 사유**: 실패 관측이 없고 최악의 결과가 승인거절(금액 오류 아님)이라 low.
다만 **모든 기본 카드결제가 타는 경로**이고 저장소의 유일한 실서버 결제는 fake-card 거절이라
이 값의 서버 수용 여부가 검증된 적이 없다 — 4.2 작업과 함께 처리 권고.

**자유석 하향 사유**: `IMMEDIATE`/`SEAT_DESIGNATED`는 `general_reservation_code=="11"`을
사전 강제해 `isFreeSeat`(전제 `genCd=="13"`)와 구조적으로 양립 불가 → 도달 불가.
남는 것은 `STANDBY`/`MERGE_STANDING`(둘 다 `"11"` 검사를 의도적으로 생략,
`mutation_payloads.py:950-951,959-975`)이고 둘 다 live 미검증 영역이다.
2층석 분기(`"018"`)는 검색측도 `"015"`를 보내므로 논리적으로 도달 불가 —
재현 불가한 것은 자유석 분기 하나뿐이다.

**제로패딩 하향 사유**: 실측 반증 2건 — `docs/verification-record.md:955-960`의 라이브
reserve→cancel 왕복이 `IRG000000` 성공(무패딩 `"1"` 수용), 예약 생성 폼에서는 앱 자신이
`trainInfoArr.length`로 무패딩 전송(`C5/a.java:55`).

---

### 4.8 [low] 결제금액 출처 우선순위가 앱과 반대

**ID**: P2INC-01

**앱 근거**: `ui/payment/PaymentActivity.java:169` `if(isReservationResponseNull())`일 때만
`RECEIVED_AMOUNT` extra를 쓰고, 아니면 `:183-199`에서 좌석행으로 재계산
(Σ(`h_seat_prc`+`h_seat_fare`) − Σ((…)−`h_rcvd_amt`) = Σ `h_rcvd_amt`) — `h_tot_rcvd_amt` 미참조.
`ui/menu/BasketTicketActivity.java:637-641`이 `RECEIVED_AMOUNT`(=`h_tot_rcvd_amt`)와
`RESERVATION`을 같은 번들에 넣으므로 `:170` 분기가 죽는다 → **앱에는 `h_tot_rcvd_amt`가
`hidMnsStlAmt1`에 도달하는 살아있는 경로가 없다**. 전송 `B6/AbstractC1269e.java:405-406` → `V4/a.java:27`.

**라이브러리 근거**: `mutation_parsers.py:83-85`가 `h_tot_rcvd_amt`를 **먼저** 시도하고
숫자면 즉시 반환, 좌석 합산(`:87-121`)은 폴백. `mutation_payloads.py:1402`.

**무엇이 틀렸나**: 앱은 서버가 준 총액 필드를 일부러 무시하고 좌석 단위로 재계산한다.
두 값이 어긋나는 케이스(부가상품·수수료·마일리지 반영 시점)가 한 번이라도 존재하면
라이브러리는 앱과 다른 금액으로 결제한다. 저장소 fixture에 실측 `h_tot_rcvd_amt` 사례는 없다.

**고치는 법**: 좌석 합산을 1순위, `h_tot_rcvd_amt`를 폴백으로 뒤집고, 두 값이 모두 읽힐 때
불일치하면 `KorailProtocolError`로 거절.

---

### 4.9 [low] `cancel_unpaid_hold` docstring 4곳이 환승 홀드를 "해제 불가"라고 반대로 안내 — 고아 PNR 유발

**ID**: K3-07 · P2MIS-04 · P2SAF-12 (동일 루트, 3회 발견)

**라이브러리 근거**: `mutation_payloads.py:1230-1240`의 거부 조건은
`legs is None or legs < 1` **뿐**이고 `:1219-1228` 주석이 "The count is ECHOED, not fixed at
one … 환승 hold carries two journeys, and refusing it here would leave a live transfer
reservation with no way to release it"라고 **다구간 허용을 명시 설계**로 못박는다.
`client.py:1853-1876` 본문에도 leg 수 검사가 없다.
반대 서술 4곳: `client.py:1731-1733`(reserve_transfer), `:1842`, `:1845-1847`,
`docs/verification-record.md:844-853`(P2SAF-12가 새로 찾음).

**왜 low가 아니라 신경 써야 하나**: `reserve_transfer`는 **실제 좌석을 잡는 메서드**다.
운영자는 홀드 직전에 이 문장을 읽고 (a) 시도를 포기하거나 (b) 시도 후 해제를 포기해
살아 있는 PNR을 방치한다. 즉 **코드가 막으려고 설계한 사고(고아 홀드)를 되살리는 방향으로**
틀려 있다. (3차는 README:311-315가 "앱에서 취소하라"는 대안을 제시한다는 이유로 low 유지.)

**부수 정정(P2MIS-04)**: docstring은 앱의 2단계 취소
(`ReservationCancel` → `ReservationCancelChk`) 전부를 이 메서드에 귀속시키지만
실제로는 2단계째만 보낸다(`client.py:1798-1800` vs `:1859`, `safety.py:228` allowlist에
1단계 부재). 앱에는 `ReservationCancelChk` 단독 호출 변형이 없다 —
자동 재예약 경로는 다이얼로그 없이 두 호출을 무조건 연속한다
(`DirectInquiryActivity.java:227-238`, `:240-250`, `:568-570`).
단, 1단계 생략 자체는 실서버 검증된 의도적 단순화이므로 결함이 아니다
(`docs/MUTATION_HANDOFF.md:21`) — **docstring 문구만 고치면 된다**.

---

### 4.10 [low] 응답 파싱/노출 누락

| 항목 | 무엇이 안 보이나 | 앱 근거 | 라이브러리 근거 | ID |
|---|---|---|---|---|
| 승차권 목록 | `reservation_list[]→ticket_list[]→train_info[]` 43필드가 타입 노출 안 됨 | `dao/myTicket/TicketListDao.java:14-374` (앱이 명시적으로 리치 서브클래스 선언) | `client.py:1487-1509`가 `post_form` 결과를 그대로 반환, `read_models`/`read_parsers`에 대응 없음. **단 `.raw`로 전부 접근 가능**(`http.py:153-162,219`)이라 medium 아닌 low | K4-01 |
| 비회원 운임재계산 입력 | hold 응답의 `h_cust_mg_no` → `hidCustNo`의 출처가 이름 붙어 노출되지 않음 | `response/certification/ReservationResponse.java:11,428-430`; `ui/inquiry/rir/orr/a.java:172`; 소비처 `a6/C1042B.java:290-293` | `mutation_models.py:229-262`에 필드 없음, `mutation_parsers.py:135-273`이 안 읽음, `:511-517` docstring이 출처 미기재. 단 `_base_fields`가 raw 보존, 그리고 **비회원 세션 자체가 도달 불가**(`client.py:1554-1557`) | K3-05 |
| 환불 실행 응답 | `stlList[].stl_mns_cd`(정산 결제수단) | `dao/refund/RefundDao.java:118-138`; `ticketReturn/a.java:525-527`(`"13"`이면 RailPlus 동기화) | `http.py:316` `post_mutation_form`이 `parse_base_response`로 끝남. **단 `response.raw["stlList"]`로 접근 가능** — "알 방법이 없다"는 원 주장은 거짓 | K6-06 · P2SAF-10 |
| 열차검색 메타 | 앱이 실제 선언하는 `h_notice_msg`를 열차검색 파서만 안 읽음 | `response/seatMovie/RsvInquiryResponse.java:12` | `parsers.py:257-276`에 부재(파일 전체 grep 0건) vs 형제 파서 `read_parsers.py:2503-2506`·`limousine_parsers.py:388-390`은 같은 키를 읽음(셋 다 같은 DTO 반환) | P2CRO-03 |

**P2SAF-10 정정**: 뮤테이션 12개 중 bare 응답 4개(`client.py:1603,1841,2016,2118`) 중
3개는 **앱도 bare `BaseResponse`**라 정상이다(`ReservationCancelService.java:21`,
`ReservationWaitService.java:12`, `ResearchService.java:66`).
유일한 실제 갭은 `refund`뿐(`RefundService.java:29`가 `RefundDao.RefundResponse` 반환).

---

### 4.11 [low] 열차조회 표현력 갭 — 앱이 보낼 수 있는 조합을 라이브러리가 만들 수 없다

| 항목 | 앱 | 라이브러리 | ID |
|---|---|---|---|
| 승객 유형 5버킷 | `u4/b.java:110-121` 8종 카운터 → `:173-177` `_1`=성인+청소년+안내견, `_2`=어린이+동반유아, `_3`=경로, `_4`=중증장애, `_5`=경증장애 (`SeatMovieService.java:14`) | `payloads.py:298` `_1=str(query.passengers)`, `:299-302` `_2~_5` 상수 `"0"`; `models.py:270-277` `TrainSearchQuery`에 승객유형 필드 없음. **대조군**: 예약(`mutation_models.py:11-48` 8종)과 리무진(`limousine_payloads.py:144-148` 5버킷)은 올바름 | P2MIS-01 |
| 좌석속성 `txtSeatAttCd_4` | `U4/b.smali:735`는 호출자 인자, `MainBookingActivity.java:768`(사용자 선택)·`b5/c.java:170,235`가 `K4/p` enum 값 전달 (자유석 003 / 입석 033 / 휠체어 021·028 / 2층 018 / 자전거 032 …) | `payloads.py:305` `"015"` 리터럴, `TrainSearchQuery`에 필드 없음. **`_2`/`_3`은 반증됨** — `U4/b.smali:711-731`이 `K4/l.DEFAULT`/`K4/n.DEFAULT`를 넣으므로 앱도 하드코딩이고 `"000"`은 바이트 일치 | P2MIS-02 |
| MAAS 메뉴 필터 | `CommonService.java:46-48`이 `pnrNo`/`tkRetNo(List)`/`addSrvReqNo`를 받고 호출 3변형 존재(`MainBookingActivity.java:737-740` 무필터, `MaasAddReservationActivity.java:69-75`, `AdditionalServiceActivity.java:157-166`) | `safety.py:770-772` 핀이 `{Device,Version}` 2필드뿐이라 저수준 우회도 `assert_read_only_request_fields`가 차단; `client.py:1232-1243` 무인자 | P2CRO-05 |
| 좌석도 `ctlDvCd` | 일반 검색은 `""`, TCS(승차권변경) 흐름은 `"3584"`(`TCSOptionsActivity.java:506`) | `payloads.py:217` `""` 하드코딩 | (2차 미검증 — §6 참조) |

---

### 4.12 [low] 안전·견고성 하드닝

| 항목 | 내용 | 근거 | ID |
|---|---|---|---|
| 핀 없는 read 라우트 13개 | `safety.py:1384-1386` `allowed = ...get(route_path); if allowed is None: return` → 필드집합(`:1413-1420`)·중복키(`:1387-1394`)·스칼라타입(`:1427-1430`) 검사가 **전부** 생략. 실측 재현: `login.Login`에 `{"evil_field":{...},"txtPwd":object()}` → 예외 없음 (계약 있는 라우트는 `KorailProtocolError`). 대상: `login.Login`, `myTicket.MyTicketList`, `common.code.do`, `common.stationdata`, `common.stationinfo`, `qry.chtnStn.do`, `research.actualTrainSchedule.do`, `schedule.runDt`, `seatMovie.ScheduleView`, `/ebizcross/getUUID.do`, `/ebizmaas/EbizMaasStationList.do`, `prdMobilePlusMain.cache`, `prdMobilePlusNotice.cache` | **하향 사유**: 1차 게이트(`assert_read_only_route`, `http.py:164/401`)는 13개에도 그대로 걸리고 현재 잘못 나가는 요청이 없다 → 게이트 구멍이 아니라 하드닝 항목. 순서있는 시퀀스 입력은 `:1376-1379`가 먼저 거부하므로 Mapping 입력 한정 | P2MIS-03 · P2SAF-03 |
| 자유석 검색 `txtSeatAttCd_4` | 위 4.11과 동일 필드 | | |
| `MutationPreview.payload` 타입 주석 | `consent.py:127`은 `Mapping[str, str]`인데 실제 반환형은 `dict[str, str 또는 list[str]]`(`redaction.py:321`, `mutation_payloads.py:1858`). 실측: `payload={'hidDscpNo':['A','B']}` → list. 앱도 `CertificationService.java:35-37`에서 6개 `@Field List<String>`이라 리스트 값은 정당 | 타입체커 사용자만 영향 | P2SAF-09 |
| `build_ticket_list_form` mode=2 날짜 미강제 | 앱의 유일한 `txtIndex="2"` 호출부(`TicketPurchaseHistoryActivity.java:277-280`)는 항상 날짜 두 개를 채운다(진입점 `:365,:372,:719` 전부 포맷된 날짜). `payloads.py:384-409`는 mode만 검사하고 날짜 미강제 — docstring(`:395-397`)은 bounds를 명시하면서 코드로 강제하지 않는 모순. **mode=1의 `""`는 앱과 일치**(`TicketListActivity.java:939-941`이 명시 전송) | 라이브러리가 스스로 틀린 폼을 만들지는 않고 호출자가 날짜 없이 `mode="2"`를 넘길 때만 발생 | K4-02 |
| `infer_login_input_flag` 값공간 겹침 | `session.py:63-69`가 `"01"` 시작 10~11자리를 무조건 휴대폰(`"4"`)으로 추론. 앱은 추론하지 않고 탭 선택(`k5/b.java:119-122`), 회원번호 탭은 10자리 숫자(`k5/c.java:19-21`). "01로 시작하는 10자리 회원번호"의 존재 여부는 서버 채번정책이라 APK로 확인 불가 | 완화: `client.py:284-297` `login(input_flag=...)`로 추론 우회 가능 | K1-05 |
| 간편(소셜) 로그인 shape 재현 불가 | 앱은 `custId`만 보내고 `txtMemberNo`/`txtPwd`/`idx`는 **null → Retrofit이 필드째 드롭**(`k5/b.java:236-243`). 라이브러리는 항상 두 필드를 채운다(`session.py:193-206`, 필터가 `is not None`이라 빈 문자열도 전송). "필드 부재"와 "필드 존재+빈값"은 서버가 다르게 취급할 수 있는 별개 상태. 카카오/네이버/구글/Onepass 연동 계정의 재로그인 경로가 없다 | wire 이름 주의: `loginType`의 실제 필드명은 `txtInputFlg`(`LoginService.java:17-18`). 값 4종 `K/N/G/D`(`S4/u.java:126-128`, `R1/x.java:34`, `HelpSrvCustDao.java:19`) | K1-02 |
| NetFunnel 미배선 | 앱은 액션별 큐(`K4/g.java:43-50` act_8/8_2/6/14/18/21/22/4, `:51` `service_1`)를 통과하는데 `client.py`·`http.py`에 netfunnel 참조 0건. `netfunnel.py:838 slot()`은 테스트에서만 사용 | **의도된 설계**(`config.py:35-57`에 근거 장문 기록: 모든 실측 호출이 토큰 없이 성공, 켜면 매 호출 왕복+3초 타임아웃). 결함 아니라 리스크 — 서버가 계측을 켜는 순간(성수기) 조용히 거부될 지점 | P2SAF-07 |
| DynaPath 403 판별 협소 | 앱 `BaseDaoHelper.java:59-90`은 경로·상태코드 조건 없이 `DynaPath-Result` 음수만 본다. `http.py:68-72`는 403 + allowlist 6경로를 요구 | **하향**: `http.py`에 재시도 로직이 없어(grep 0건) 주장한 피해가 성립하지 않음. 토큰을 붙이는 쪽은 앱·라이브러리 모두 같은 6경로(`constants.py:420-430` ↔ `ExecuteDao.java:27`) | P2SAF-11 |
| consent 검사 비대칭 | `pay_with_fake_card`(`client.py:1898-1903`)는 `fake_card_only`만 검사, `pay_with_card`(`:1971-1984`)는 양쪽 검사. 모순 consent(둘 다 True)가 dry-run 프리뷰를 통과한 뒤 `dry_run=False`에서 `MutationNotAllowedError` | **문서화된 설계**: `http.py:269-284` 주석이 "keeps the invariant at the layer that actually sends"로 계층 배치를 명시. fail-safe이며 게이트 우회 아님 | P2SAF-06 |
| 카드보유 카테고리 완전성 테스트 부재 | `safety.py:295` 정의("forms carry a card number in the clear") vs `:317` `frozenset({"payment"})`. `reserve`도 `txtCardNo_1`을 싣는다(`mutation_payloads.py:1704`) | **게이트 구멍 아님**: 그 값은 결제 PAN이 아니라 N카드 번호(`h_dcnt_crd_no`, `w4/a.java:100-101`)이고 `http.py:276-291` 게이트는 PAN 이분법이라 비과금 선불카드엔 성립하지 않음. 마스킹도 `redaction.py:195`로 구멍 없음. 다만 역방향(카드번호 나르는 폼이 빠짐없이 등재됐는가) 검사는 실제로 없음 | P2SAF-04 |

---

### 4.13 [low/info] 문서 드리프트

| 항목 | 내용 | ID |
|---|---|---|
| 공개 메서드 수치 핀이 **낡은 값**을 지킨다 | 실측 74인데 `tests/test_readme.py:219`가 `"72 public methods"` 문자열의 존재를 필수조건으로 고정. 74로 적은 문서: `README.md:79`, `api-status-by-service.md:18`, `verification-record.md:21`, `IMPLEMENTATION_PROGRESS.md:148`. 낡은 현재형: `IMPLEMENTATION_PROGRESS.md:312,758`. 같은 함수의 `assert "75" in progress`(`:221`)와 `assert "two" in text`(`:78`)는 문서 아무데나 있는 문자열이라 사실상 무검사. **정정**: `"72 public methods"`는 같은 파일에 3회이고 `:234`는 과거 단계 불릿이므로 `:312/:758`만 고쳐도 테스트는 통과한다 | P2CRO-06 |
| 인벤토리 수치 두 문서 모순 | `api-status-by-service.md:9-15`(32/13/120/165) vs `IMPLEMENTATION_PROGRESS.md:311`("32 successful, 10 failed, 123 unexecuted"). **정정**: 핀은 양쪽 다 걸려 있다(`tests/test_readme.py:88-91` 및 `:523,:546`) — 즉 CI가 서로 모순되는 두 수치를 동시에 강제 중 | P2CRO-07 |
| `RELEASE_GAP_PLAN` G 표가 낡음 | 이미 닫힌 갭 4 + 부가 2를 열린 것으로 표시 (§3.3) | P2CRO-08 |
| `EXCLUDED_API_DOMAINS`가 구현된 도메인을 "declined"로 기록 | `safety.py:41-51`이 `reservation`/`payment`/`refund`를 배제 영역으로 적으나 셋 다 라우트·클라이언트·consent 카테고리 완비(`safety.py:208,224,234,249`; `client.py:1565,1898,2029`). 주석 스스로 "documentary: nothing dispatches on it"이라 기능 영향 0. 나머지 5개(check-in, member-drop, push-sms, points-mileage-write, dynapath-token-generation)는 실제 배제 맞음. `safety.py:19-24`가 같은 이유로 `points-mileage`→`points-mileage-write`로 좁힌 전례가 있는데 세 도메인엔 미적용 | K1-03 · P2CRO-09 |
| 열차검색 파서가 APK 0건 키 4개를 읽고 테스트가 자기확인 | `parsers.py:259,271,272,273`이 `strJobId`/`h_seat_cnt_first`/`h_seat_cnt_second`/`txtGoHour_first`를 읽는데 `grep -rIl` 실측 결과 `analysis/` 전체 **0 파일**. 앱 DTO(`RsvInquiryResponse.java:9-17`) 최상위는 정확히 9필드. 바로 옆 `models.py:580-583`은 `h_menu_id`를 "zero hits across the whole decompiled app"을 이유로 제외했는데 **동일 기준을 이 4개엔 미적용**. 픽스처 `tests/fixtures/raw_typed_train_search.json:5,11,13`이 `SYNTHETIC-…` 값을 넣고 `tests/test_raw_typed_core.py:650,658-662`가 그 값을 단언 → 테스트 통과는 "파서가 자기가 읽도록 쓰인 키를 읽는다"만 증명. 실재하는 `h_notice_msg`는 오히려 미노출(P2CRO-03) | P2CRO-02 |

---

## 5. 의도된 제외 — 결함 아님

사용자가 명시적으로 범위에서 뺀 항목. **결함으로 보고하지 않는다.**

- **정기권(통근패스) 구매** — 실제로 앱에 존재하며 라이브러리에 없음이 확인됐다:
  `pass.passPayIssue`(`PassService.java:19-21`, `CommPaymentDao.java`),
  `pass.passReserve`(`:23-25`, `CommReservationDao.java`),
  자유이용권 `pass.passOtrPayIssue`/`passOtrReserve`(`:39-45`).
  참고로 `IMPLEMENTATION_PROGRESS.md:78-89`에 2026-07-26 한 번 구현했다가 같은 날 제거한
  기록이 있다(환불 경로 없는 ₩150,000~250,000 결제 + `passPayIssue`는 앱 자체의
  `PaymentActivity.isCommPaymentRequest()` `instanceof` 버그로 영원히 도달 불가한 죽은 코드).
- **`reservation.seatAssign.do`(좌석지정/업그레이드 예약)** — K3-04. 살아있는 호출부가
  전부 정기권/G-Pass/A-Pass 좌석지정이다(`SeatAssignBookingActivity.java:120-132,134-146,167-176`).
  일반승차권 분기 `setGeneralTicket`(`:148-150`)은 **본문이 진짜 빈 메서드**
  (smali `SeatAssignBookingActivity$b.smali:697-701` `.locals 0 / return-void`),
  N카드 분기는 이미 구현된 일반 `ReservationDao` 경로로 간다.
  따라서 제외 제품군 안이며 "결함" 프레이밍이 성립하지 않는다.
- **단체예약** — 8개 슬라이스 전체에서 **단체예약 전용 엔드포인트를 발견하지 못했다.**
  발견되지 않았으므로 이 항목에는 대응 갭이 없다.

이 절과 §3.1(문서화된 이연)을 섞지 말 것. §3.1은 프로젝트가 스스로 미룬 것이고,
이 절은 사용자가 범위에서 뺀 것이다.

---

## 6. 판단 보류 — 근거 확인 불가로 남은 것

### 6.1 감사 자체의 커버리지 구멍 — K2 슬라이스(열차조회·시간표·운임)

1차 `02-search.md`(`trainsInfo`/`schedule`/`research`/`product`, 22개 엔드포인트)는 작성됐지만
오케스트레이터 커버리지 슬롯이 **통제 카나리("test: 추출 1 / 구현 1")로 채워져** 2·3차
검증 파이프라인을 타지 않았다(3차 verifier-2의 `T-1` 항목이 그 카나리다 — "제목·근거·주장이
모두 문자열 `test`"). 따라서 이 슬라이스의 자체 findings **TSF-01/03/04/05/07/08/09는
검증되지 않았다.** 다음 감사에서 반드시 재검증할 것:

| ID | 요지 | 상태 |
|---|---|---|
| TSF-01 | `TourTrainSpecialRoom` 파서·모델만 있고 빌더·client 없음(죽은 코드) | 미검증 (G5로 문서 추적됨) |
| TSF-03 | `trainsInfo.TrainCharge`는 **앱 자체가 안 쓰는 죽은 엔드포인트** → 미구현이 정답 | 미검증 (결함 아님 주장) |
| TSF-04 | `get_seat_cars`/`get_seat_inventory` 응답에 앱 DTO에 없는 옵셔널 필드 소수 | 미검증 (unverifiable) |
| TSF-05 | 좌석배정/병합좌석 응답에 좌석도 연쇄호출용 `h_seat_att_cd`/`txtGdNo`가 `raw`로만 | 미검증 |
| TSF-07 | `build_seat_inventory_form`의 `ctlDvCd`가 `""` 고정이라 TCS 변형 재현 불가 | 미검증 |
| TSF-08 | `research.tripChgOgtk.do` 미구현(G4) | 미검증 (§3.3에 반영) |
| TSF-09 | `product.payInfo`(G9), `product.ReservationCancel` 미구현 | 미검증 (§3.3에 반영) |

두 건은 2차에서 **독립 재발견**되어 검증을 통과했으므로 §4에 이미 반영돼 있다:
TSF-06(G2/G3 문서 드리프트) → **P2CRO-08**로 확대 확인(4건 닫힘),
TSF-02(`actualTrainSchedule` 응답 스키마 과다확장) → **P2CRO-15**로 재판정(아래).

### 6.2 P2CRO-15 — `actualTrainSchedule.do` 파서의 wire key 16개, APK 전체 0건

`parsers.py`의 `parse_train_schedule_response`가 읽는 최상위 15개 + stop 레벨 7개 중
16개가 앱 디컴파일 트리 전체에서 검색되지 않는다(앱 DTO는
`TrainScheduleDao$TrainScheduleResponse.smali` 7필드 + `$TimeInfo.smali` 14필드).
**그러나** Gson은 DTO에 선언되지 않은 JSON 키를 조용히 무시하므로 "앱 DTO에 없다"가
"서버 응답에도 없다"를 함의하지 않는다. 전부 옵셔널 파싱이라 크래시 없이 `None`이 될 뿐이다.
**실측 응답 캡처가 없는 한 판정 불가** → 3차 판정 UNVERIFIABLE(low).
동일 위험: `tests/fixtures/raw_typed_train_schedule.json`이 이 키들을 `SYNTHETIC-…`로 채워
테스트 초록불이 스키마 검증을 뜻하지 않는다.

### 6.3 개별 확인불가 항목

- **K1-05** — "01로 시작하는 10자리 회원번호"의 존재 여부는 KORAIL 채번 정책(서버)이라
  APK 정적분석으로 확인 불가. 메커니즘만 확정.
- **K6-02/P2INC-08** — 서버가 `tk_ret_tms_dv_cd`/`pbpAcepTgtFlg`를 클라이언트 값 그대로
  신뢰하는지 자체 재계산하는지 미확정
  (`docs/deep-dive/cross-validation-2026-07-21.md:274,420`이 이미 남겨둔 질문).
  **다만 "읽어온 값을 버린다"는 사실 자체는 서버 동작과 무관하게 확정적**이다.
- **P2SAF-11** — 서버가 DynaPath allowlist 6경로 밖에서 음수 `DynaPath-Result`를
  내려주는지는 서버측 동작이라 확인 불가.
- **`cashReceipt.issue.do`** — 다른 간편결제처럼 "PG WebView라서 범위 밖"이라는 구체적
  근거 문장을 찾지 못했다. `api-status-by-service.md:191`의 "결제/간편결제/포인트/금전성 API"
  사유만 있음.
- **`get_mileage_history`** 전체와 `get_korail_point_summary`의 `disability_flag` ↔ `ERR299943`
  상관관계는 라이브러리 자신이 "NOT LIVE-VERIFIED"/"가설"로 명시(`client.py:573`, `:534-538`).

---

## 7. 권고 작업 순서

순서 원칙: **잘못된 요청이 실제로 나가는 것 > 약속한 안전동작이 안 지켜지는 것 >
호출자를 오도하는 문서 > 미구현.** 미구현은 잘못된 요청을 만들 수 없다는 것이
3차의 반복 하향 논거이므로 맨 뒤다.

1. **환불 에코 3필드 + `h_pbp_acep_tgt_flg` 파서** (§4.1)
   유일한 금전 정확성 결함이고, `refund()`는 실서버 성공 봉투가 없어 안전망도 없다.
   `_REFUND_TICKET_DETAIL_FIELDS`에 6필드 추가 → `build_refund_form`에 override 3개 추가.

2. **`redact_payload`를 `키_숫자` 접미 정규화 매칭으로 전환** (§4.2·4.3·4.6)
   동시에 `saleDd`, `hidRsvChgNo`, 로그인 `str*` PII 7종을 `SENSITIVE_KEYS`에 등재.
   **8건이 한 번에 닫히고** `README.md:209-211`의 "can never" 문장이 참이 된다.
   같은 커밋에 뮤테이션 빌더 방출 키 ↔ `SENSITIVE_KEYS` 차집합 검사 테스트를 추가하고,
   결제 프리뷰 테스트를 `journeys`가 채워진 hold로 보강(현재 픽스처가 결함을 은폐 중).
   **함께 처리**: `CardPayment.installment` 기본값 `"00"`→`"0"` (§4.7) —
   모든 기본 카드결제가 타는 경로인데 서버 수용 여부가 검증된 적 없다.

3. **영수증 `cash_rcet_info` 파서 추가 + `PaidTicket.sale_date` docstring 정정** (§4.4·4.5)
   후자는 `RefundTicketDetailResponse`→`PaidTicket` 변환 헬퍼를 함께 제공해
   호출자 오용 자체를 막는 것이 핵심.

4. **`cancel_unpaid_hold` docstring 4곳 정정** (§4.9)
   `client.py:1731-1733`을 **먼저** — 이 문장 하나가 고아 PNR을 유발하는 방향으로 틀려 있다.
   함께 "앱은 2단계지만 이 메서드는 실측 확인된 2단계째만 보낸다"로 귀속도 정정.

5. **문서 수치 드리프트 정리** (§4.13)
   `IMPLEMENTATION_PROGRESS.md:312,758`의 72→74; 인벤토리 두 수치를 하나의 출처로 통일하고
   양쪽 핀 정리; `RELEASE_GAP_PLAN` G 표에서 닫힌 갭 6건 갱신;
   `EXCLUDED_API_DOMAINS`에서 reservation/payment/refund 제거 또는 재분류;
   수치 단언을 문서 문자열 대신 `inspect` 실측 비교로 교체(`"75"`/`"two"` 무의미 단언 제거).

6. **하드닝** (§4.12)
   핀 없는 read 13개에 필드 계약 등재(형태 고정된 것부터: `MyTicketList`, `chtnStn.do`,
   `actualTrainSchedule.do`, `stationinfo`, `EbizMaasStationList.do`;
   `ScheduleView`는 OPTIONAL 집합으로, `common.code.do`는 리스트/int 값을 다루도록 검증기 확장 후).
   `consent.py:127` 타입 주석 정정. §1.3의 불변식 8종과 45개 핀 대조 스크립트를 회귀 테스트로 승격.

7. **표현력 갭** (§4.11)
   `TrainSearchQuery`에 승객유형 5버킷(합산 규칙은 `u4/b.java:173-177`) + 좌석속성 `_4` 추가,
   MAAS 메뉴 핀에 `pnrNo`/`tkRetNo`/`addSrvReqNo` 추가.

8. **미구현 엔드포인트** (§3.2) — 우선순위 순:
   (a) 오프라인 반환번호 환불 verify/execute(계획에 있었고 3/5만 완성),
   (b) `cart.addCartList`·`maas.rsvStt.do`(각각 1~4필드, 난이도 하),
   (c) `mileage.acpnMlgSpec.do`·`self.seatChgInfo.do`(순수 read, 게이트 설계 불필요),
   (d) 승차권 변경 체인(`tripChgOgtk`→`tripChgPrsC`→`tripChgHndgCnc`, R* FieldMap 6개, 난이도 상),
   (e) AddService 5종, `push.update`.

9. **범위 결정 요청** (§3.4)
   비회원(비로그인, 이름+전화+비밀번호) 세션을 지원할 것인가.
   지원하면 `session.py`에 비회원 상태 추가 후 관련 엔드포인트 전체 재검토,
   미지원이면 README에 명시적으로 선언(현재는 선언이 없어 "의도된 제외"로 볼 근거가 없다).

10. **K2 슬라이스 재검증** (§6.1) — 감사 커버리지 구멍이므로 다음 라운드에서 반드시 채울 것.

---

## 8. 부록 A — 3차에서 기각된 10건 (다시 살리지 말 것)

| ID | 요지 | 기각 사유 |
|---|---|---|
| K8-05 | `ScheduleViewSpecial` 미배선 | 파서/페이로드 완성, 배선 보류가 `tests/test_next_variant_reads.py:104-110`으로 3층(라우트 수·클라이언트 메서드·공개 심볼) 고정된 의도적 holdback |
| K8-06 | DynaPath 403 판별에 경로제한 추가 | 라이브러리가 앱보다 좁은 방향이라 안전한 쪽 (P2SAF-11로 부분 승계) |
| K8-07 | 타 도메인 소비 파일 미검증 | 감사 경계 기록이지 결함 아님 |
| P2INC-02 | 홀드 취소 2단계 중 1단계 미호출 | 실서버 검증된 의도적 단순화 (`MUTATION_HANDOFF.md:21`) |
| P2INC-05 | 환불 폼 위경도 `""` + 4필드 항상 전송 | |
| P2INC-06 | `parse_reservation_history_response`의 P100 빈결과 허용 | |
| P2SAF-03b | 뮤테이션 8개 라우트 전부 필드 미고정 | `http.py:241` docstring이 "no read-only field allowlist applies"로 명시, 테스트가 부재를 고정 |
| P2SAF-14 | `redact_value`가 `__all__`에 없음 | |
| P2SAF-15 | `logout`(GET)이 읽기 allowlist에 등재 | 의도된 설계 |
| P2CRO-10 | NetFunnel 전 계층 독립 확인 | 긍정 결과(결함 없음) |

## 9. 부록 B — 확정 72건 색인

| ID | 심각도 | 판정 | 루트 클러스터 / 문서 위치 |
|---|---|---|---|
| K6-02 / P2INC-08 / P2CRO-12 | high×3 | C/C/C | 환불 에코 → §4.1 |
| K6-03 | medium | C | 환불 에코(파서측) → §4.1 |
| K5-01 | medium | C | 영수증 파싱 → §4.4 |
| P2SAF-01 | medium | C | 마스킹 → §4.2 |
| P2SAF-08 | medium | C | 마스킹(문서) → §4.6 |
| P2CRO-01 | medium | C | `sale_date` 문서 → §4.5 |
| K5-02 / P2INC-10 / P2CRO-13 | low×3 | C | 마스킹 `hidRsvChgNo` → §4.3 |
| P2SAF-02 / P2CRO-04 | low×2 | C | 마스킹 `saleDd` → §4.3 |
| P2SAF-05 | low | C | 마스킹 로그인 PII → §4.3 |
| K5-03 / P2INC-07 / P2CRO-14 | low×3 | C | 할부 상수 → §4.7 |
| K3-06 / P2INC-09 | low×2 | C | 자유석 `"003"` → §4.7 |
| P2INC-04 | info | C | `txtJrnyCnt` 패딩 → §4.7 |
| P2INC-01 | low | C | 결제금액 우선순위 → §4.8 |
| K3-07 / P2MIS-04 / P2SAF-12 | low×3 | C | 취소 docstring → §4.9 |
| K4-01 | low | C | 승차권목록 파싱 → §4.10 |
| K3-05 | low | C | `h_cust_mg_no` → §4.10 |
| K6-06 / P2SAF-10 | info/low | P/P | 환불 `stlList` → §4.10 |
| P2CRO-03 | low | C | `h_notice_msg` → §4.10 |
| P2MIS-01 / P2MIS-02 / P2CRO-05 | low×3 | C/P/C | 표현력 갭 → §4.11 |
| P2MIS-03 / P2SAF-03 | info/low | C | 핀 없는 read 13 → §4.12 |
| P2SAF-09 | low | C | 타입 주석 → §4.12 |
| K4-02 | low | C | mode=2 날짜 → §4.12 |
| K1-05 | low | P | 로그인 추론 → §4.12 |
| K1-02 | low | C | 간편로그인 shape → §4.12 |
| P2SAF-07 | info | C | NetFunnel 미배선 → §4.12 |
| P2SAF-11 | low | P | DynaPath 판별 → §4.12 |
| P2SAF-06 | info | P | consent 비대칭 → §4.12 |
| P2SAF-04 | info | P | 카드보유 카테고리 → §4.12 |
| P2CRO-06 / P2CRO-07 / P2CRO-08 | low×3 | C/P/C | 문서 수치 → §4.13 |
| K1-03 / P2CRO-09 | low/info | C | `EXCLUDED_API_DOMAINS` → §4.13 |
| P2CRO-02 | low | C | 합성 픽스처 → §4.13 |
| K6-01 | low | C | 오프라인 환불 미구현 → §3.2 |
| K4-03 | info | P | `tripChgHndgCnc` → §3.2 |
| K3-01 / K3-02 / K3-03 | info/low/info | C | 장바구니·MAAS·승차권변경 → §3.2 |
| K6-05 | info | C | `reservationChange` → §3.2 |
| K8-01 / K8-04 | low/info | C/P | AddService·push → §3.2 |
| K4-05 / K4-06 / K4-07 | info×2/low | P/P/C | SMS·PBP철회·기기초기화 → §3.2 |
| K7-01 | info | P | `acpnMlgSpec` → §3.2 |
| K4-04 | info | C | `seatChgInfo`(G6) → §3.3 |
| K4-08 | low | C | 비회원 필드 → §3.4 |
| K1-01 / K1-04 / K6-04 / K8-02 / K8-03 / P2MIS-05 | info×6 | C/P/P/C/C/P | 문서화된 이연·범위 밖 → §3.1 |
| K3-04 | info | P | 정기권 좌석지정 → §5 |
| P2INC-03 | info | C | 방법론 기록(오탐 철회) → §2.1 |
| P2SAF-13 / P2CRO-11 | info×2 | C | 긍정 결과(게이트 무결) → §1.3 |

판정: C = CONFIRMED, P = PARTIAL(사실은 성립하나 원 주장의 "미문서화/미인지" 프레이밍이 무너짐 —
§3·§4의 각 정정 문구를 반드시 함께 읽을 것).
