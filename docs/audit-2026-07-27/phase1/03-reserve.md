# K3 — 예약(일반·장바구니·환승·병합) 영역 감사 보고서

담당 범위: `network/dao/reservation/`, `network/dao/cart/`, `network/dao/independent/`,
`network/data/reservation/`(new `R*` + `old/O*`) 전부. 이 범위의 실제 "일반예약" 생성 로직은
파일 위치상 `network/dao/certification/ReservationDao.java` +
`network/request/reservation/ReservationRequest.java`에 있지만, 그 요청 바디는 전적으로
`network/data/reservation/old/O*`(내 담당) 필드맵이므로 함께 감사했다. 마찬가지로
`network/dao/reservationWait/`(예약대기 확정)도 `reserve(job_type=STANDBY)`의 후속 호출이라
가볍게 검증했다. `network/dao/reservationCancel/`, `network/dao/certification/`의 나머지
(할인/인증 DAO들), `network/dao/research/`(N카드 등)는 타 에이전트 영역으로 보고 깊이 들어가지
않았다.

## 0. 방법

1. jadx 소스에서 담당 폴더 전 파일을 읽고 Retrofit 인터페이스의 필드명·타입·엔드포인트를 추출.
2. 의심스러운 상수·분기(자유석 판정, standby 플래그, 병합 저널타입 코드 등)는 apktool smali로
   재확인 — jadx가 렌더링을 뭉갠 지점(`U4/a.java`가 스텁인 것 등)이 실제로 있었다.
3. `src/korail_mobile_api/mutation_payloads.py`, `mutation_models.py`, `mutation_parsers.py`,
   `client.py`, `constants.py`, `read_payloads.py`/`read_models.py`(가드/일부 read 겸용 엔드포인트)
   와 1:1 대조.
4. `docs/RELEASE_GAP_PLAN.md`, `docs/api-status-by-service.md`, `docs/deep-dive/agent-reports/06-*.md`
   를 대조해 "이미 알려진 갭"과 "이번에 새로 발견한 것"을 구분.

## 1. 기능 전체 목록

### 1.1 담당 폴더 리터럴 범위 (`dao/reservation`, `dao/cart`, `dao/independent`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 좌석속성 안내조회 (guideSeatCnd) | POST `reservation.guideSeatCnd.do` | `ReservationService.java:17-19` | `read_payloads.py:246-251`(`build_guide_seat_condition_form`), `client.py:856-868`(`get_guide_seat_condition`) | 있음 (일치) |
| 2 | 예약내역 조회 (ReservationView) | GET `reservation.ReservationView` | `ReservationService.java:21-22`, `TicketRsvHistoryDao.java` | `client.py:828-838`(`get_reservation_history`), `read_parsers.py:1143-1225` | 있음 (일치, 일부 필드만 명명 승격·나머지는 `raw`로 보존) |
| 3 | 승차권 변경 예약생성 (tripChgPrsC) | POST `reservation.tripChgPrsC.do` | `ReservationService.java:24-26`, `TCReservationDao.java` 전체 | 없음 | **없음 (K3-03)** — `docs/RELEASE_GAP_PLAN.md:278`에 이미 추적됨 |
| 4 | 좌석지정(업그레이드) 예약 (seatAssign) | POST `reservation.seatAssign.do` | `ReservationService.java:28-30`, `SeatAssignReservationDao.java` | 없음 | **없음 (K3-04)** — 실사용처는 정기권/G-Pass/A-Pass류 뿐(`SeatAssignBookingActivity.java:121-173`, `:148-150`의 `setGeneralTicket`은 공백), `RELEASE_GAP_PLAN.md:276`에 추적됨 |
| 5 | 장바구니 담기 (addCartList) | POST `cart.addCartList` | `CartService.java:11-13`, `AddCartDao.java`, `AddProductDao.java` | 없음 | **없음 (K3-01)** |
| 6 | 장바구니 목록조회 (showCartList) | POST `cart.showCartList` | `CartService.java:15-17`, `CartListDao.java` | `read_payloads.py:377-387`(`build_cart_list_form`), `client.py:450-469`(`get_cart_list`), `read_parsers.py:647-701` | 있음 (일치) |
| 7 | MAAS 예약상태 확인 (rsvStt) | POST `maas.rsvStt.do` | `CartService.java:19-21`, `VerifyMaasStatusDao.java` | 없음 | **없음 (K3-02)** |
| 8 | 팝업확인 기록 (poppCfmRec) | POST `login.poppCfmRec.do` | `IndependentService.java:12-14` | 없음 | 범위밖(info) — 예약과 무관한 전역 팝업-ack 텔레메트리. `S4/k$a`(스몰리)가 앱 전역(로그인/메뉴 등)에서 호출, 예약 도메인 데이터 없음. "누락"으로 세지 않음 |

### 1.2 밀접 연관 — 실제 "일반·환승·병합" 예약 생성 로직 (`dao/certification/ReservationDao` + `data/reservation/old/O*`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 9 | 일반예약 (직통, 1101/1103) | POST `certification.TicketReservation` | `CertificationService.java:52-54`, `ReservationDao.java`, `c5/a.java:52-119`(`N0`) | `mutation_payloads.py:151-212`(`build_reservation_form`), `client.py:1512-1593`(`reserve`) | 있음 (필드·상수 다수 재검증 완료, 아래 §2 참고) |
| 10 | 환승예약 (2구간, 동일 엔드포인트) | 상동 | `c5/a.java:52-119`, `OJrny.java`/`OSeat.java`/`OSrcar.java`의 `i==1?...` 분기 | `mutation_payloads.py:214-291`(`build_transfer_reservation_form`), `client.py:1691-1763`(`reserve_transfer`) | 있음 (환승 저널타입 `"14"` smali로 재확인 완료) |
| 11 | 병합예약 (입석+좌석, 1202 hold + 2차 병합폼) | 상동 | `DirectInquiryActivity.smali:5573-6010`(2차), `a5/u.java:346-397`(1차 게이팅) | `mutation_payloads.py:294-479`(`build_merge_reservation_form`), `client.py:1765-`(`reserve_merge`) | 있음 (`"21"/"22"` 저널타입, `txtStndFlg="Y"` 고정, `arvTm_2` 미기록, `txtPsrmClCd2` 카피 — 전부 smali로 직접 재확인 완료) |
| 12 | 예약대기 확정 (2차 호출) | POST `reservationWait.ReservationWait` | `ReservationWaitService.java:10-12`, `RsvWaitDao.java` | `mutation_payloads.py:1127-1208`(`build_standby_wait_form`), `client.py:1595-1659`(`confirm_standby_hold`) | 있음 (필드 순서·SMS 조건부 전화번호 생략까지 일치) |
| 13 | 미결제 예약취소 | POST `reservationCancel.ReservationCancelChk` | `DReservationConfirmActivity.java:269-279` 등 다수 호출부 | `mutation_payloads.py:1211-1270`, `client.py:1836-1876`(`cancel_unpaid_hold`) | 있음, 단 **문서 불일치 (K3-07)** |
| 14 | 운임 재계산 (할인 변경) | POST `certification.PriceReCalculation` | `CertificationService.java:35-37`, `a6/C1042B.java:265-296` | `mutation_payloads.py:1744-1876`(`build_price_recalculation_form`) | **부분 (K3-05)** — 비회원 `hidCustNo` 소스 미노출 |

## 2. 정밀 재검증한 상수/분기 (문제 없음, 근거만 기록)

이 항목들은 라이브러리 docstring이 이미 file:line을 인용하고 있었지만, 지침("jadx가 이상하면
smali로 확인")에 따라 **직접 smali를 읽어 재확인**했다. 전부 일치했다:

- `KORAIL_DIRECT_JOURNEY_TYPE_CODE="11"` / `KORAIL_TRANSFER_JOURNEY_TYPE_CODE="14"` —
  `smali/K4/e.smali:36-84`에서 직접 확인 (`"직통"/"11"`, `"환승"/"14"`).
- `KORAIL_MERGE_LEADING/TRAILING_JOURNEY_TYPE_CODE="21"/"22"` —
  `smali/K4/e.smali:88-140`에서 직접 확인 (`"병합 선행"/"21"`, `"병합 후행"/"22"`).
- `KORAIL_STANDBY_WAIT_FLAG=" 9"`(앞에 공백) —
  `smali/U4/a.smali:1250-1256` `const-string v6, " 9"` 직접 확인. jadx는 이 메서드를
  스텁으로만 렌더링(`U4/a.java`)하므로 smali 확인이 필수였던 지점.
- `_PASSENGER_ROWS` 8행의 `psgTpCd`/`discKndCd` 값 — `w4/a.java:46-73`(`a()` 메서드)와
  1:1 바이트 일치.
- `txtSeatAttCd1/2/3/5="000"`, 좌석1 `txtSeatAttCd4="015"` — `K4/q.DISABLE`, `K4/l.DEFAULT`,
  `K4/n.DEFAULT`, `K4/m.DISABLE`가 전부 코드값 `"000"`, `K4/p.DEFAULT`가 `"015"`임을
  `K4/q.java`,`K4/l.java`,`K4/n.java`,`K4/m.java`,`K4/p.java`에서 직접 확인.
- 병합 2차 호출의 `txtStndFlg="Y"` 고정, `txtPsrmClCd2` 카피(+GENERAL 폴백), `arvTm_2` 미기록 —
  `smali/.../DirectInquiryActivity.smali:5873-5990` 및 전체 파일 `setArvTm` grep(0건)으로 확인.
- `KORAIL_MERGE_SEAT_FLAGS_BY_CABIN`(`{"1":{"A","G"}, "2":{"A","S"}}`) — `S4/J.java:61-63`
  `isMixedSeat` 불리언식을 손으로 전개해 검증 (GENERAL→{A,G}, SPECIAL→{A,S} 도출 일치).

## 3. 발견된 문제 (findings 상세)

### K3-01 — 장바구니 담기(`cart.addCartList`) 뮤테이션 완전 부재 [missing/medium]

앱: `CartService.java:11-13`(`addCart`), `AddCartDao.java`(필드: `Device`,`Version`,`Key`,
`hidPnrNo`), `AddProductDao.java`(같은 요청, id만 다름). 예약을 만든 뒤 "장바구니에 담기"를
누르면 이 엔드포인트로 `hidPnrNo`만 보낸다.

라이브러리: `src/korail_mobile_api/` 전체에서 `addCartList`/`add_cart`/`AddCart` 매칭 0건
(client.py, safety.py, read_payloads.py, mutation_payloads.py 전수 grep 확인). `get_cart_list`
(목록조회)만 있고 담기(mutation) 자체가 없어 "장바구니" 워크플로가 읽기 전용으로 끝난다.
`docs/api-status-by-service.md:180`에 "미실행"으로 이미 카탈로그화는 되어 있음(숨겨진 문제는
아님) — 다만 실제 파이썬 코드에는 전혀 없다.

### K3-02 — MAAS 예약상태 확인(`maas.rsvStt.do`) 부재 [missing/low]

앱: `CartService.java:19-21`(`verifyMaasStatus`), `VerifyMaasStatusDao.java`(필드:
`addSrvDvCd`,`addSrvReqNo`,`coptEntRsvNo`,`lumpStlTgtNo`). 장바구니 화면에서 MAAS 연계상품
결제 전 상태 확인에 쓰인다(`ui/menu/BasketTicketActivity.java`가 호출).

라이브러리: 전체 grep 0건. `docs/api-status-by-service.md:182`에 "미실행"으로 이미
추적되어 있음.

### K3-03 — 승차권 변경 예약생성(`reservation.tripChgPrsC.do`) 부재 [missing/low]

앱: `ReservationService.java:24-26`(`getTicketChangeReservation`), `TCReservationDao.java`
전체(요청 필드: `trvlKndCd`,`totPrnb`,`isePrnb`,`stndSeatFlg`,`intgTktIseFlg`,
`prcFareReCalcFlg`,`tmpJobSqno`,`alcSeatDmnPsDvCd`,`jrny2Cnt`,`psg2Cnt`,`ctlDvCd`,
`frcSaleRsnCont` + `RJrny`/`RSrcar`/`RSeat`/`RPsg`/`ROrtg`/`RDscp` 맵 6개). 화면 타이틀은
`res/values/strings.xml:432` `"승차권 변경"` — 기존 결제된 승차권의 열차/좌석을 바꾸는 별개
기능이며, 사용자가 명시 제외한 "정기권 구매/단체예약"과는 무관한 정상 범위 기능이다.

라이브러리: 전체 grep 0건 (`tripChgPrsC`,`TCReservation`,`trvlKndCd`,`jrny2Cnt`,`psg2Cnt`
전부 무매칭). `docs/RELEASE_GAP_PLAN.md:278,867`에 이미 추적된 갭 — 신규 발견은 아니고
확인 사살.

### K3-04 — 좌석지정/업그레이드 예약(`reservation.seatAssign.do`) 부재, 단 실사용범위는 좁음 [missing/low]

앱: `ReservationService.java:28-30`(`setSeatAssignReservation`), `SeatAssignReservationDao.java`
(필드: `menuId`,`custMgNo`,`totPrnb`,`stndFlg`,`rqScarNum` + `RJrny`/`RSrcar`/`RSeat`/`RPsg`/
`ROrtg` 맵 5개). 호출부를 추적한 결과(`SeatAssignBookingActivity.java:84-189`) 이 DAO는
**정기권(통근열차)/G-Pass/A-Pass류 좌석선택 화면에서만** 만들어진다 —
`setCommutationTicket`(:121-132), `setGPassTicket`(:134-146), `setPassTicket`(:165-174) 전부
`W4.a.getSeatAssignReservationRequest(...)`를 호출해 이 DAO로 가는 반면, N카드는
`getNCardReservationRequest`로 **일반 `ReservationDao`**를 타고(이미 구현됨), 일반승차권
분기인 `setGeneralTicket`(:148-150)은 **본문이 비어있다**(현재 앱 버전에서 미배선). 즉
seatAssign.do는 일반 예약 흐름과 무관하며, 사용자가 명시적으로 제외한 "정기권(통근패스)"류에
사실상 한정된다.

라이브러리: 전체 grep 0건. `docs/RELEASE_GAP_PLAN.md:276`에 이미 추적됨. **판단**: "정기권
구매" 자체는 제외 대상이지만 이 DAO의 재현여부는 결정하지 않았으므로 missing으로 보고하되,
실사용 범위가 좁다는 사실을 함께 기록 — orchestrator가 제외범위 해당여부를 최종 판단하도록.

### K3-05 — 비회원 운임재계산용 `h_cust_mg_no`가 `ReservationHoldResponse`에 노출되지 않음 [partial/medium]

앱: `network/response/certification/ReservationResponse.java:11`(`private String
h_cust_mg_no;`), `:428-430`(`getH_cust_mg_no()`). 실제 소비처를 추적하면
`ui/inquiry/rir/orr/a.java:172`에서
`h.getInstance().setNonMemberNumber(reservationResponse.getH_cust_mg_no())` — 예약(hold)
응답의 이 필드가 비회원 세션 번호로 저장되고, 이후 `CertificationService.java:35-37`
(`getDiscountPrice`)의 `hidCustNo` 필드로 재전송된다
(`DiscountPriceDao.java:14,33,76-77`).

라이브러리: `mutation_models.py:228-262`의 `ReservationHoldResponse`에 `h_cust_mg_no`/
`non_member_no` 필드가 없고, `mutation_parsers.py:135-274`의 `parse_reservation_hold_response`
도 이 키를 읽지 않는다. 반면 `mutation_payloads.py:1497,1861-1871`의
`build_price_recalculation_form`/`PriceRecalculationRequest.non_member_no`는 이 값을
**호출자가 어디선가 구해서** 넣어야 하는데, 라이브러리 어디에도 그 출처(hold 응답의
`h_cust_mg_no`)를 이름 붙여 꺼내는 코드가 없다. `BaseKorailResponse.raw`(원본 dict)에는
남아있어 데이터 자체가 유실되진 않지만(`models.py:21-25`), 문서화되지 않은 raw 키 이름을
추측해야 하므로 비회원 운임재계산 플로우가 사실상 발견 불가능하다. `build_price_recalculation_form`
자체가 이미 "NOT VERIFIED"로 표시된 영역이라 심각도는 medium으로 낮춤.

### K3-06 — 좌석속성 `txtSeatAttCd4{i}`가 자유석(`"003"`)을 반영하지 않고 항상 `"015"` 고정 [risk/low]

앱: `c5/a.java:85-96`이 매 leg마다 `S4.J.isFreeSeat(cabin, h_gen_rsv_cd, h_free_rsv_cd)`가
참이면 `oSeat.setSeatAttCd4(i, K4.p.NORMAL_FREE.getCode())`(`"003"`)을, 아니면 `t2()`
(탐색요청의 `txtSeatAttCd_4`, 이 라이브러리가 항상 `"015"`로 보내는 값)를 쓴다.
`S4/J.java:57-59`: `isFreeSeat(cabin,genCd,freeCd) = GENERAL.equals(cabin) && "13".equals(genCd)
&& "11".equals(freeCd)` — 즉 **일반실이 매진(`"13"`)이면서 자유석 재고가 열려있으면(`"11"`)**
`"003"`을 보낸다.

라이브러리: `mutation_payloads.py:836-854`(`_build_journey_reservation_form`)는 leg마다
무조건 `_seat_attribute_key(journey)`에 `"015"`만 대입하고 `train.free_reservation_code`
(`models.py:343`에 파싱되어 있음에도)를 전혀 참조하지 않는다. 다만 이 코드는
`IMMEDIATE`/`SEAT_DESIGNATED`에는 `general_reservation_code=="11"`을 사전에 강제하므로
(`mutation_payloads.py:989-992`) `isFreeSeat`의 전제(`genCd=="13"`)와 구조적으로 양립할 수
없어 이 두 경로에서는 실질적으로 도달 불가능하다. 문제가 남는 곳은 `STANDBY`와
`MERGE_STANDING`인데, 이 둘은 라이브러리가 **의도적으로** `general_reservation_code=="11"`
검사를 생략한다(`mutation_payloads.py:936-976`의 주석대로 "매진이 정상"이므로). 즉 대기예약
또는 병합대상 열차가 동시에 `h_free_rsv_cd=="11"`인 경우 앱은 `"003"`을 보내는데 라이브러리는
`"015"`를 보낸다 — 두 job type 모두 이미 "NOT live-verified"로 문서화된 영역이라 심각도는
낮게 잡았지만, 실제 KTX/새마을 등 자유석 운영 열차에서 대기예약을 걸 경우 재현 가능한 필드값
불일치다. `docs/deep-dive/agent-reports/06-reservation-certification.md`에도 이 분기는
언급되어 있지 않아(§`txtSeatAttCd4` 검색 결과 자유석 조건부 분기 없음) 이번에 새로 발견한
사항으로 판단.

### K3-07 — `cancel_unpaid_hold`가 실제로는 2구간(환승) 홀드도 취소 가능한데 docstring 두 곳이 "단일 여정만"이라 반대로 서술 [doc-drift/low]

앱: 해당없음 — 라이브러리 내부 문서 불일치이며 앱 근거 대조 항목이 아니다.

라이브러리: `mutation_payloads.py:1211-1270`(`build_unpaid_reservation_cancel_form`)의
docstring 자체가 "The count is ECHOED, not fixed at one... A 환승 hold carries two journeys,
and refusing it here would leave a live transfer reservation with no way to release it"라고
명시하고, 구현도 `response.journey_count`를 그대로 `txtJrnyCnt`로 보내며 `legs>=1`만
요구한다(`legs==1` 강제 없음). 그런데 `client.py:1836,1842,1846`의 `cancel_unpaid_hold`
자체 docstring은 "Cancel a fresh, unpaid **single-journey** reservation hold" /
"requires hold to be one successful (SUCC) **single-journey** hold"라고 반대로 서술하고,
`client.py:1691,1731-1733`의 `reserve_transfer` docstring도 "note that
`cancel_unpaid_hold` currently accepts single-journey holds only, so a live transfer hold
cannot be released through this client"라고 재차 단정한다. `cancel_unpaid_hold`의 실제
구현(`client.py:1853-1875`)에는 leg 수를 검사/제한하는 코드가 전혀 없으므로, 이 두 docstring은
자신이 호출하는 `build_unpaid_reservation_cancel_form`의 실제 동작과 모순된다. 기능 결함은
아니지만(오히려 구현이 문서보다 더 관대함), 사용자가 이 문서를 믿고 "환승 홀드는 취소 못 함"
이라 오판해 실환경에서 미결제 홀드를 방치할 위험이 있다.

## 4. 확인했으나 문제 없음으로 판단한 항목 (참고)

- 비회원 예약 경로(`ReservationRequest.isNonmemberNotEnable`, `nonMember.NonMemTicket`
  오버로드) — 라이브러리는 모든 뮤테이션에 로그인 세션을 강제하므로(`client.py:1566-1569` 등)
  비회원 분기 자체가 구조적으로 도달 불가. 앱과의 "차이"이긴 하나 안전설계이지 결함이 아님.
- `KorailPassengerCounts`의 카드번호 필드 부재(`txtCardCode_`/`txtCardPw_` 미전송) —
  `OPsg.java:7-10`에 그런 필드가 애초에 없음을 확인, 라이브러리가 맞고 srtgo/korail2 쪽이
  구버전 프로토콜을 반영한 것.
- `KORAIL_MAX_JOURNEY_LEGS=2`, `KORAIL_MAX_PASSENGERS_PER_RESERVATION=9`,
  `KORAIL_MAX_DISCOUNT_CARD_SECTIONS=3` — 근거로 인용된 `OSeat.java:32-35`/`OSrcar.java:21-30`
  의 `i==1?...:...` 2진 분기, `m5/*.java` 피커 상한 등 실제로 그 값들과 일치함을 코드로 확인.
- `TicketRsvHistoryDao` 응답 중 `h_ise_psb_tm`/`h_ntisu_lmt_dt`/`h_ntisu_lmt_tm`/
  `h_ntisu_psb_dt`/`h_payment_msg`가 `ReservationHistoryTrain`에 명명 승격되지 않음 —
  다만 `raw=train`으로 전체 원본이 보존되고, 이는 이 라이브러리 전반의 일관된 설계 패턴이라
  결함으로 보고하지 않음(K3-05와 달리 이쪽은 소비 경로가 문서화된 필수 입력이 아님).

## 5. 결론

내 담당 영역은 전반적으로 **매우 정밀하게 구현**되어 있다. 특히 예약 생성 핵심 로직
(일반/환승/병합, 8개 승객행, 5개 좌석속성 상수, standby 플래그 `" 9"`, 병합 저널타입
`"21"/"22"`)은 smali 직접 대조까지 전부 일치했다. 발견된 문제는 (a) 이미 문서상
추적되어 있던 4개 미구현 엔드포인트(장바구니 담기, MAAS 상태확인, 승차권변경, 좌석지정업그레이드)를
재확인, (b) 새로 발견한 비회원 운임재계산 소스 필드 누락 1건, (c) 자유석 좌석속성 코드
미반영 엣지케이스 1건, (d) 문서 자기모순 1건이다. critical/high 등급 결함은 없었다.
