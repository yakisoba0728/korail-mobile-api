# K6 — 취소·환불·보상·지연 감사 보고서

범위: `network/dao/reservationCancel/`, `network/dao/refund/`,
`network/dao/compensate/`, `network/dao/delay/` (jadx) 전체와
`src/korail_mobile_api/` 대응 구현. apktool smali는 필드명이 jadx와 이미
1:1 일치하는 곳(모든 `@Field` 애노테이션 문자열)은 별도 재확인하지 않았고,
분기/상수가 문제되는 지점(취소 2단계, refund 하드코딩 값)은 기존
cross-validation 문서(`docs/deep-dive/cross-validation-2026-07-21.md`)의
smali 근거를 인용해 교차검증했다. 이 문서는 2026-07-21 감사에서 이미
smali(`a6/x.java:190-207`, `I4/a.java:5-6` 등)까지 확인했으므로 중복 재확인은
생략하고 인용으로 대체했다.

## 1. 앱 기능 전체 목록

### 1.1 ReservationCancelService (`network/dao/reservationCancel/`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 예약취소 1단계(initiate) | `POST reservationCancel.ReservationCancel` | `ReservationCancelService.java:15-17` | 없음(의도적, 아래 참고) | 정보 |
| 2 | 예약취소 2단계(commit) | `POST reservationCancel.ReservationCancelChk` | `ReservationCancelService.java:19-21`, `RsvCancelCheckDao.java:11-64` | `client.py:1836-1875 cancel_unpaid_hold`, `mutation_payloads.py:1211-1270 build_unpaid_reservation_cancel_form`, `safety.py:228,284` | 있음 (live-verified) |
| 3 | 대기예약 자동취소 1/2단계 | 동일 엔드포인트, `AutoRsvCancelDao`/`AutoRsvCancelCheckDao` | `AutoRsvCancelDao.java:8-29`, `AutoRsvCancelCheckDao.java:8-29` | 위 #2와 와이어 동일(필드·엔드포인트 동일, TrainInfo는 로컬 상태) | 있음(공유) |
| 4 | 예약 인원 변경 | `POST reservation.reservationChange.do` | `ReservationCancelService.java:23-25`, `ReservationChangeDao.java` | 없음 | 없음 (문서화된 제외) |

### 1.2 RefundService (`network/dao/refund/`)

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 5 | 환불대상 티켓 상세조회 | `POST refunds.SelTicketInfo` | `RefundService.java:23-25`, `TicketDetailDao.java:227-499` | `client.py:1155-1178 get_refund_ticket_detail`, `read_payloads.py:1635-1662`, `read_parsers.py:2679-2807` | 있음(부분 — §3.3) |
| 6 | 환불 수수료/가능여부 조회 | `POST refunds.CommissionView` | `RefundService.java:19-21`, `RefundCommissionDao.java:9-116` | `client.py:1131-1153 get_refund_commission`, `read_payloads.py:1612-1632`, `read_parsers.py:2627-2649` | 있음 |
| 7 | 일반 승차권 환불 실행 | `POST refunds.RefundsRequest` | `RefundService.java:27-29`, `RefundDao.java:9-146` | `client.py:2011-2046 refund`, `mutation_payloads.py:1416-1462 build_refund_form` | 있음(값 결함 — §3.1/3.2) |
| 8 | 반환번호 검증(오프라인) | `POST refunds.verifyOnlineRefunds` | `RefundService.java:31-33`, `RefundVerifyTicketDao.java:11-224` | 없음 | 없음 (§3.4) |
| 9 | 반환번호 환불 실행(오프라인) | `POST refunds.executeOnlineRefunds` | `RefundService.java:15-17`, `RefundExecuteTicketRefundDao.java:9-147` | 없음 | 없음 (§3.4) |

### 1.3 CompensateService (`network/dao/compensate/`) — 운행중지 보상

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 10 | 운행중지 보상 목록 | `POST compensate.ticketList.do` | `CompensateService.java:20-22`, `CompensateRefundListDao.java` | 없음 | 없음 (문서화된 제외) |
| 11 | 운행중지 보상 상세/검증 | `POST compensate.ticketDetail.do` | `CompensateService.java:16-18`, `CompensateRefundCheckDao.java` | 없음 | 없음 (문서화된 제외) |
| 12 | 운행중지 보상 실행 | `POST compensate.ticketReturn.do` | `CompensateService.java:12-14`, `CompensateRefundDao.java` | 없음 | 없음 (문서화된 제외) |

### 1.4 DelayService (`network/dao/delay/`) — 지연 보상/증명/계좌환불

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 13 | 지연증명 발급 | `POST dlay.athnIsu.do` | `DelayService.java:18-20`, `DelayCertificateDao.java` | 없음 | 없음 (문서화된 제외) |
| 14 | 지연 현금/계좌 환불 | `POST dlay.cashRfn.do` | `DelayService.java:22-24`, `CashRfnDao.java` | 없음 | 없음 (문서화된 제외) |
| 15 | 지연 반환영수증 | `POST dlay.pymtRcet.do` | `DelayService.java:26-28`, `DelayReturnReceiptDao.java` | 없음 | 없음 (문서화된 제외) |
| 16 | 입금은행 목록 | `POST dlay.dptnBank.do` | `DelayService.java:30-32`, `DptnBankDao.java` | 없음 | 없음 (문서화된 제외) |
| 17 | 지연동의 PNR 조회 | `POST delay.pnrQry.do` | `DelayService.java:38-40`, `DelayPNRQueryDao.java` | 없음 | 없음 (문서화된 제외) |
| 18 | 지연동의 PNR 접수 | `POST delay.acptPrs.do` | `DelayService.java:34-36`, `DelayPNRAcceptDao.java` | 없음 | 없음 (문서화된 제외) |
| 19 | 지연 보상 목록 | `POST delay.ticketList.do` | `DelayService.java:50-52`, `DelayRefundListDao.java` | 없음 | 없음 (문서화된 제외) |
| 20 | 지연 보상 상세/검증 | `POST delay.ticketDetail.do` | `DelayService.java:46-48`, `DelayRefundCheckDao.java` | 없음 | 없음 (문서화된 제외) |
| 21 | 지연 보상 실행 | `POST delay.ticketReturn.do` | `DelayService.java:42-44`, `DelayRefundDao.java` | 없음 | 없음 (문서화된 제외) |

참고: 라이브러리의 `get_delay_discount_tickets`(`client.py:482-495`, `DelayDiscountTicketListResponse`)는 **다른 기능**이다. 이것은 지연으로 적립된 **지연할인권(쿠폰)** 조회이고, 위 #13-21의 "지연 보상금/현금환불 청구"와는 별개 도메인이다(app 근거: `PassCardService`/`h_delay_cnt` 계열, `read_models.py:64-76,547-548`). 혼동하지 않도록 표에서 제외했다.

집계: 위 표의 순수 엔드포인트 21개 중 my-scope 패키지(`ReservationCancelService`, `RefundService`, `CompensateService`, `DelayService`)에 실제로 선언된 것은 20개(#1-3은 와이어상 2개 엔드포인트를 공유하므로 실제 유니크 엔드포인트는 19개: ReservationCancel, ReservationCancelChk, reservationChange, SelTicketInfo, CommissionView, RefundsRequest, verifyOnlineRefunds, executeOnlineRefunds, compensate×3, delay×9). 구현됨: **4개**(#2/AutoCancel 포함, #5, #6, #7) — 이 중 #5는 응답 필드 다수 누락(부분), #7은 값 결함 2건(§3.1/3.2)을 가진 채로 "구현됨"으로 카운트했다.

## 2. 의도적/검증된 설계이며 결함이 아닌 것

- **취소 1단계(`ReservationCancel`) 생략.** 앱은 확인 다이얼로그 앞뒤로
  `ReservationCancel`(initiate) → `ReservationCancelChk`(commit) 2단계를
  밟지만(`a6/x.java:190-207`, cross-val §4 — `docs/deep-dive/cross-validation-2026-07-21.md:237`),
  `ReservationCancelChk` 자체가 커밋 단계이지 자격조회가 아니라는 것이
  smali까지 확인되어 있고, 라이브러리는 `ReservationCancelChk` 단일 호출만
  `KORAIL_MUTATION_ROUTES`에 올려 두었다(`safety.py:284`). 2026-07-25
  실서버 reserve→cancel 왕복에서 이 단일호출로 성공을 확인했다
  (`docs/MUTATION_HANDOFF.md:21`, `mutation_payloads.py:1109-1114`). 결함
  아님 — 검증된 의도적 단순화.
- **compensate/delay 보상금 청구 11개 엔드포인트 미구현은 결함이 아니라
  문서화된 v1 범위 제외**다(`docs/RELEASE_GAP_PLAN.md:444`: "Out of core v1
  (documented, deferred)... delay/compensate refunds (11 endpoints,
  analysis §3.10)"; TODO 체크리스트 `docs/RELEASE_GAP_PLAN.md:865-866`도
  미완료로 남아 있음을 보여준다). §4 K6-04에 정보성 항목으로만 기록한다.
- **`reservationChange`(예약 인원 변경) 미구현도 동일하게 문서화된 이연
  항목**이다(`docs/RELEASE_GAP_PLAN.md:867` 체크리스트, `:1012` "the full
  tripChg change flow, `reservation.reservationChange.do`... — most are
  already in §3/§5 scope"). §4 K6-05.
- **범위 밖 참고**: `ticket.tripChgHndgCnc.do`(TCCancelDao, 여정변경 롤백
  전용 취소)와 `product.ReservationCancel`(여행상품 취소, GET, 이름만
  같은 별개 엔드포인트)은 `network/dao/ticket/`, `network/dao/product/`
  소속이라 이 감사 범위(`reservationCancel/refund/compensate/delay`) 밖이다
  (`analysis/jadx/sources/com/korail/talk/network/dao/ticket/TCCancelDao.java`;
  `docs/RELEASE_GAP_PLAN.md:302-303,318`). 별도 담당 에이전트가 다룰 항목으로
  보고 findings에는 넣지 않았다.

## 3. 결함 상세

### 3.1 K6-01 (missing, high) — 오프라인 반환번호 환불(verify/execute) 전체 미구현

`refunds.verifyOnlineRefunds`(`RefundService.java:31-33`,
`RefundVerifyTicketDao.java:13-62`, 필드 `retNo1..4`,`strName`)와
`refunds.executeOnlineRefunds`(`RefundService.java:15-17`,
`RefundExecuteTicketRefundDao.java:11-108`, 필드 `pnrNo`,`tkKndCd`,
`retDvCd`,`retRsnCd`,`ogtkSaleDt`,`ogtkSaleWctNo`,`ogtkSaleSqno`,
`ogtkRetPwd`,`retAmt`,`retFee`,`custTeln`,`acepCustNm`)로 구성된, 회원 로그인
없이 반환번호 4분할 + 신청자명으로 처리하는 별도 환불 플로우가 앱에 존재한다
(`S5/c.java:64-95,172-208`, `S5/h.java:50-127,183-193`).

라이브러리 `src/korail_mobile_api/`에는 `verifyOnlineRefunds`,
`executeOnlineRefunds`, `retNo1`, `acepCustNm`, `retDvCd`, `RefundVerify`,
`RefundExecuteTicket`, `OnlineRefund` 등 관련 문자열이 전혀 없다(`grep -rl`
전수 조사, 0건). `client.py`에도 대응 메서드가 없다.

이것은 "의도적 제외"가 아니라 **프로젝트 자신의 계획에 포함되어 있었지만
미완료로 남은 항목**이다: `docs/RELEASE_GAP_PLAN.md:392-406`이 이 두
엔드포인트를 "Flow D — Refund"의 일부로 상세 스펙까지 적어 두었고,
`:450`의 "Core mutation endpoint count: 27 (A:7, B:4, C:10, **D:5**, E:4)"에서
Flow D의 5개 엔드포인트(`SelTicketInfo`,`CommissionView`,`RefundsRequest`,
`verifyOnlineRefunds`,`executeOnlineRefunds`)를 전부 v1 코어 범위로
카운트했다. `:865-866`의 TODO 체크리스트("Refund online... + offline
(`verify`→`execute`); dry-run + fixtures only in v1")도 미체크 상태다.
즉 계획에는 있었으나 구현에서 3/5(SelTicketInfo, CommissionView,
RefundsRequest)만 만들어지고 오프라인 2개가 누락됐다.

- 앱 근거: `RefundService.java:15-17,31-33`; `S5/c.java:64-208`; `S5/h.java:50-193`
- 라이브러리 근거: 없음 (`src/korail_mobile_api/*.py` 전수 grep 0건)
- 제안: `verify_offline_refund`/`execute_offline_refund` (가칭) 폼빌더+파서+
  클라이언트 메서드 추가. mutation route allowlist에도 추가 필요.

### 3.2 K6-02 (incorrect, high) — `build_refund_form`이 서버에서 받은 값을 무시하고 고정값을 보낸다

앱은 `RefundsRequest` 실행 전에 `CommissionView`를 호출해 받은
`tk_ret_tms_dv_cd`(출발전 `"21"`/출발후 `"15"`, `I4/a.java:5-6`)와
`prg_psb_flg`(마일리지 정산 분기 트리거, `=="M"`이면 사용여부를 재질문)를
그대로 실제 환불 요청에 반영한다(`ticketReturn/a.java:180-199,203-229,
362-404,427-428`). `RefundDao.java:9,24,52,56,108,130,140`도
`tk_ret_tms_dv_cd`와 `h_mlg_stl`을 별개 setter가 있는 가변 필드로 선언한다.

라이브러리는 이 두 값을 **이미 자신이 읽어올 수 있음에도** 실제 환불
전송에 반영하지 않는다:

- `get_refund_commission()`이 `RefundCommissionResponse.
  ticket_return_times_division_code`(=`tk_ret_tms_dv_cd`)와
  `.proceed_possible_flag`(=`prg_psb_flg`), `.usable_mileage`
  (=`use_psb_mlg_num`)를 정확히 파싱해서 caller에게 돌려준다
  (`read_models.py:1183-1204`, `read_parsers.py:2627-2649`).
- 그런데 `build_refund_form(config, ticket)`은 이 값을 받는 파라미터가
  전혀 없고, `"tk_ret_tms_dv_cd": "21"`, `"h_mlg_stl": "N"`을 무조건
  하드코딩한다(`mutation_payloads.py:1416-1462`, 특히 `:1454-1455`).
  `refund()`(`client.py:2011-2046`)도 `ticket: PaidTicket` 외 다른
  입력을 받지 않으므로 caller가 override할 방법이 없다.

즉 출발 후 환불(`tk_ret_tms_dv_cd`가 실제로는 `"15"`여야 하는 경우)이나
마일리지 정산 대상 환불(`prg_psb_flg=="M"`이고 가용 마일리지가 수수료
이상이라 `h_mlg_stl="Y"`를 보내야 하는 경우)에 라이브러리는 항상
"출발 전, 마일리지 미사용"에 해당하는 값만 보낸다. 서버가 이 필드를
클라이언트가 보낸 그대로 신뢰하는지, 자체 재계산해 무시하는지는
정적분석만으로 확정할 수 없다(`docs/deep-dive/cross-validation-2026-07-21.md:274,420`
가 이미 미확인으로 남겨둔 질문). 그러나 "라이브러리가 이미 올바른 값을
읽어오고도 실제 전송에서 버린다"는 사실 자체는 서버 동작과 무관하게
확정적인 결함이다.

- 앱 근거: `ticketReturn/a.java:180-199,203-229,362-404,427-428`;
  `RefundDao.java:9,24,52,56,108,130,140`; `I4/a.java:5-6`
- 라이브러리 근거: `mutation_payloads.py:1416-1462`(특히 1454-1455, 하드코딩);
  `read_models.py:1183-1204`, `read_parsers.py:2627-2649`(값이 이미 파싱됨을 증명);
  `client.py:2011-2046`(override 경로 없음)
- 제안: `build_refund_form`/`refund()`에 `ticket_return_times_division_code`,
  `use_mileage: bool` 같은 선택 인자를 추가하고, 미지정 시에만 현재 기본값을
  유지하도록 변경.

### 3.3 K6-03 (missing+incorrect, high) — `pbpAcepTgtFlg`: 원본 필드 자체가 파싱되지 않고, 전송값은 항상 `"N"` 고정

`h_pbp_acep_tgt_flg`는 `refunds.SelTicketInfo` 응답(`TicketDetailDao.java:250,
373-374,497-498`)의 실제 필드이고, 앱은 이것을 그대로
`RefundsRequest.pbpAcepTgtFlg`로 복사한다
(`ticketReturn/a.java:430-431`: `setPbpAcepTgtFlg(ticketDetail.
getH_pbp_acep_tgt_flg())`). `RefundDao.java`의 `executeDao()`가 굳이
`t.e("PbpAcepTgtFlg : " + refundRequest.getPbpAcepTgtFlg())`로 디버그
로그를 남기는 것으로 보아(`RefundDao.java:132`), 앱 개발자도 이 필드를
따로 신경 써서 다뤘던 흔적이 있다.

라이브러리 쪽은 이중으로 비어 있다:

1. `RefundTicketDetailResponse`/`_REFUND_TICKET_DETAIL_FIELDS`
   (`read_parsers.py:2679-2698`)에 `h_pbp_acep_tgt_flg`가 없다 — 즉
   `get_refund_ticket_detail()`을 호출해도 이 값을 읽을 방법이 아예 없다.
   같은 이유로 환불/지연/부가서비스 판단에 쓰이는 `h_dlay_flg`,
   `h_dlay_tk_flg`(`TicketDetailDao.java:242-243,341-347`), `mlgSaveFlg`
   (`:266,437-439`), `addSrvFlg`, `addSrvCancel`(`:228-229,285-291`)도 함께
   빠져 있다.
2. `build_refund_form`은 `"pbpAcepTgtFlg": "N"`을 무조건 고정한다
   (`mutation_payloads.py:1457`).

PBP 대상 티켓(`h_pbp_acep_tgt_flg=="Y"`)을 환불할 경우 라이브러리는 이를
감지할 수도, 올바른 값을 보낼 수도 없다. §3.2와 원인이 다르므로(값 자체를
읽어올 방법이 없음 vs 읽어오고도 버림) 별개 결함으로 분리했다.

- 앱 근거: `TicketDetailDao.java:250,373-374,497-498`;
  `ticketReturn/a.java:430-431`; `RefundDao.java:132`(디버그 로그)
- 라이브러리 근거: `read_parsers.py:2679-2698`(필드 매핑 부재);
  `mutation_payloads.py:1457`(고정 `"N"`)
- 제안: `_REFUND_TICKET_DETAIL_FIELDS`에 `pbp_acceptance_target_flag:
  "h_pbp_acep_tgt_flg"`(및 delay/addSrv 플래그) 추가, `build_refund_form`에
  override 인자 추가.

### 3.4 K6-04 (info) — 운행중지 보상(Compensate) + 지연 보상금 청구(Delay refund) 11개 엔드포인트 전체 미구현

`CompensateService`(3개: 목록/상세검증/실행)와 `DelayService`의 보상/증명/
계좌환불 계열(9개: `athnIsu`,`cashRfn`,`pymtRcet`,`dptnBank`,`pnrQry`,
`acptPrs`,`ticketList`,`ticketDetail`,`ticketReturn`) 총 11개 엔드포인트가
라이브러리에 전혀 없다. 이는 §2에서 설명한 대로
`docs/RELEASE_GAP_PLAN.md:444`에 "Out of core v1 (documented, deferred)"로
명시된 항목이라 **결함이 아니라 정보성 기록**으로만 남긴다. 세부
엔드포인트/필드는 §1.3-1.4 표 참고.

- 앱 근거: §1.3-1.4 표
- 라이브러리 근거: 없음 (문서상 의도적 제외, `docs/RELEASE_GAP_PLAN.md:444,865-866`)

### 3.5 K6-05 (info) — 예약 인원 변경(`reservationChange`) 미구현

`reservation.reservationChange.do`(`ReservationCancelService.java:23-25`,
`ReservationChangeDao.java`)도 라이브러리에 없다. `docs/RELEASE_GAP_PLAN.md:867`
체크리스트("`reservationChange`/`tripChgPrsC`/`tripChgHndgCnc` with `R*` maps")가
미체크 상태이고 `:1012`에도 이연 항목으로 명시되어 있어 문서화된 이연으로
분류한다.

- 앱 근거: `ReservationCancelService.java:23-25`; `ReservationChangeDao.java:1-60`
- 라이브러리 근거: 없음 (문서상 이연, `docs/RELEASE_GAP_PLAN.md:867,1012`)

### 3.6 K6-06 (low) — 환불 실행 응답의 `stlList[].stl_mns_cd` 미파싱

앱은 `RefundsRequest` 실행 응답의 `stlList` 안에 결제수단코드 `"13"`이
있으면 RailPlus 동기화를 수행한다(`RefundDao.java:118-138`;
`ticketReturn/a.java:493-525`). 라이브러리의 `refund()`는
`post_mutation_form()`을 통해 전송하는데, 이 메서드는 항상 필드 없는
평범한 `BaseKorailResponse`만 반환한다(`http.py:222-230`) — `stlList`나
`stl_mns_cd`를 파싱하는 경로가 없다. RailPlus 연동은 앱 로컬 부수효과라
헤드리스 라이브러리에 필수는 아니지만, 환불이 어떤 결제수단으로 정산됐는지
호출자가 알 방법이 없다는 점에서 낮은 심각도의 부분 구현으로 기록한다.

- 앱 근거: `RefundDao.java:118-138`; `ticketReturn/a.java:493-525`
- 라이브러리 근거: `http.py:222-230`(제네릭 `BaseKorailResponse`만 반환)

## 4. 검증 메모

- `RsvCancelDao`/`RsvCancelCheckDao`/`AutoRsvCancelDao`/`AutoRsvCancelCheckDao`,
  `RefundService.java`, `RefundCommissionDao.java`, `RefundDao.java`,
  `RefundVerifyTicketDao.java`, `RefundExecuteTicketRefundDao.java`,
  `TicketDetailDao.java`(응답 클래스 전체, ~50 getter), `CompensateService.java`
  +3개 DAO, `DelayService.java` +9개 DAO를 모두 원문 그대로 읽고 `@Field`
  문자열을 라이브러리 폼빌더/파서 딕셔너리와 1:1 대조했다. `OJrny.JRNY_CNT`/
  `JRNY_SQ_NO`, `Price2Fare.trnNoString` 등 상수 참조 필드는 정의부까지
  따라가 실제 와이어 문자열(`"txtJrnyCnt"`,`"txtJrnySqno"`,`"trnNo"`)을
  확인했다. PNR 필드명은 `txtPnrNo`(P-n-r)로 취소·환불 양쪽 모두 일치하며,
  과거 이력에 언급된 `txtPrnNo` 오타는 앱 소스 어디에도 없다(재확인, 0건 —
  `docs/deep-dive/cross-validation-2026-07-21.md:236`과 일치).
- 취소 2단계 관련 smali 근거(`a6/x.java:190-207`)와 실서버 검증
  (2026-07-25)은 문서를 통해 인용했고 별도 smali 재확인은 생략했다 — 이미
  2026-07-21/25 세션에서 확정된 사실이며 본 감사에서 이를 재검증할 신규
  방법이 없기 때문이다(정적 코드는 동일).
- compensate/delay 11개 엔드포인트는 라이브러리에 대응이 전혀 없어
  "라이브러리 근거"가 원천적으로 없다 — 확인불가가 아니라 명확한 부재이므로
  missing(§3.4에서는 info로 하향, 문서화된 제외이기 때문)로 분류했다.
