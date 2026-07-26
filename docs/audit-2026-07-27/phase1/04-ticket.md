# 04 — 예약대기·승차권 조회 (reservationWait / ticket / myTicket) 대조 감사

담당 영역: `network/dao/reservationWait/`, `network/dao/ticket/`(+`ticket/change/`), `network/dao/myTicket/`
대상 라이브러리: `src/korail_mobile_api/`
방법: jadx 전수 정독 + smali 확인(디코드 실패 지점: `DeviceResetDao` 호출부) + `docs/` 기존 감사 기록 교차검증 + 라이브 실측 기록(`docs/api-status-by-service.md`) 대조.

## 0. 집계

Retrofit 서비스 인터페이스 메서드 기준(내가 담당하는 3개 서비스):

| 서비스 | 메서드 수 |
|---|---:|
| `ReservationWaitService` | 1 |
| `MyTicketService` | 3 |
| `TicketService` | 19 |
| **합계** | **23** |

- **완전/정상 구현: 8개**
- **부분 구현(응답 파싱 누락 등): 1개** (`getTicketList`)
- **의도된 제외(문서 근거 있음, `info`): 9개** — self check-in 4개, MAAS 부가서비스 취소 3개, 특실 업그레이드 2개
- **근거 없이 비어있음(`missing`): 5개** — `deviceReset`, `getSelfSeatChgInfo`, `gurdSmsSnd`, `pbpTkWdrw`, `ticketChangeCancel`

## 1. 기능 전체 목록

| # | 기능 | 엔드포인트 | 앱 근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|---|
| 1 | 예약대기 신청(좌석등급변경/SMS동의) | `POST reservationWait.ReservationWait` | `RsvWaitDao.java:61-70`, `ReservationWaitService.java:10-12` | `client.py:1595-1659 confirm_standby_hold`, `mutation_payloads.py:1127-1208 build_standby_wait_form` | 있음 (완전) |
| 2 | 내 승차권/구매이력 목록 | `POST myTicket.MyTicketList` | `TicketListDao.java:376-380`, `MyTicketService.java:15-18` | `client.py:1487-1510 get_ticket_list`, `payloads.py:384-409 build_ticket_list_form` | **부분** (요청은 맞음, 응답 미파싱) |
| 3 | 특실 업그레이드 견적 조회 | `GET myTicket.reqUpgradeSeat` | `SpecialRoomUpgradeDao.java` | 없음 | **info**(문서화된 제외) |
| 4 | 특실 업그레이드 결제 처리 | `GET myTicket.procUpgradeSeat` | `SpecialRoomUpgradeProcessDao.java` | 없음 | **info**(문서화된 제외) |
| 5 | 기기정보(승차권 열람기기) 초기화 | `POST tk.dvcInfoInit.do` | `DeviceResetDao.java`; 호출부는 jadx 미복호화, smali `TicketListActivity.smali:5355-5735`로 확인 | 없음 | **missing** |
| 6 | 배송수령고객정보 조회(N카드 배송) | `POST tk.dlvRcvCust.do` | `DlvRcvCustDao.java:75-83` | `client.py:1029`, `payloads.py`, `read_parsers.py:2143-2189` | 있음 (완전) |
| 7 | 보호자 안심 문자 발송 | `POST tk.gurdSmsSnd.do` | `GuardianReliefSmsDao.java`, 호출부 `GuardianReliefSmsActivity.java:52-58` | 없음 | **missing** |
| 8 | MAAS 부가서비스 결제 전체취소 | `POST addService.cancelPay.do`(경로에 `//` 이중슬래시 원문) | `MaasCancelDao.java` | 없음 | **info**(문서화된 제외) |
| 9 | MAAS 부가서비스 개별취소 | `POST addService.coptCnc.do` | `MaasServiceCancelDao.java` | 없음 | **info**(문서화된 제외) |
| 10 | MAAS 부가서비스 취소수수료 조회 | `POST maas.cncFee.do` | `MaasServiceCancelFeeDao.java` | 없음 | **info**(문서화된 제외) |
| 11 | MAAS 부가서비스 내역 조회 | `POST copt.gdReqQry.do` | `MaasServiceDetailListDao.java:150-163` | `client.py:939-956 get_maas_service_detail_list`, `read_models.py:774-802`(20필드 1:1 일치) | 있음 (완전) |
| 12 | 자율 좌석/열차 변경 옵션 조회 | `POST self.seatChgInfo.do` | `CallSelfSeatChgInfoDao.java:213-226` | 없음 | **missing** |
| 13 | 승차권 변경 가능일 조회 | `POST reservation.tripChgDate.do` | `TripChgInfoDao.java:44-52` | `client.py:966`, `read_models.py:805-810`(3필드 일치) | 있음 (완전) |
| 14 | 승차권 대리인 인수사양 조회(PBP) | `POST tk.pbpAcepSpec.do` | `PbpAcepSpecDao.java:206-213` | `client.py:1061`, `read_models.py:945-960` | 있음 (완전) |
| 15 | 승차권 대리인 인수 철회(PBP) | `POST tk.pbpWdrw.do` | `PbpTkWdrwDao.java:52-59`, 호출부 `DeliveredActivity.java` | 없음 | **missing** |
| 16 | 승강장 번호 갱신 | `POST tk.plfNo.do` | `UpdatePlatformDao.java:90-96` | `client.py:1077`, `read_models.py:962-...` | 있음 (완전) |
| 17 | 최근 배송/수령인 이력 조회 | `POST tk.rcntDlvHst.do` | `RecentDeliveryHistoryDao.java:72-80` | `client.py:1096`, `read_parsers.py:2184-2189` | 있음 (완전) |
| 18 | 셀프 체크인 취소 | `POST checkin.cnc.do` | `SelfCheckinCancelDao.java` | 없음 | **info**(README 명시: "Check-in ... Not implemented in this version") |
| 19 | 셀프 체크인 정보 조회 | `POST checkin.info.do` | `SelfCheckinInfoDao.java` | 없음 | **info** |
| 20 | 셀프 체크인 가능여부(QR) | `POST checkin.psbFlg.do` | `SelfCheckinPossibleDao.java` | 없음 | **info** |
| 21 | 셀프 체크인 등록 | `POST checkin.reg.do` | `SelfCheckinRegisterDao.java` | 없음 | **info** |
| 22 | 승차권 변경 처리 취소(묶음결제대상 롤백) | `POST ticket.tripChgHndgCnc.do` | `TCCancelDao.java:36-41`, 호출부 `a6/x.java`, `DReservationConfirmActivity.java` | 없음 | **missing** |
| 23 | 승차권 중복확인 | `POST ticket.ticketDupCheck.do` | `TicketDuplicationCheckDao.java:39-45` | `client.py:1038-1052`, `read_parsers.py:2209-2220`(int 강제형변환 코멘트 포함) | 있음 (완전) |

## 2. 문제 항목 상세

### 2.1 [K4-01] `getTicketList` — 응답이 구조화되지 않음 (요청은 정확)

**분류**: partial · **심각도**: medium

앱의 `TicketListDao.TicketListResponse`는 `reservation_list[] -> ticket_list[] -> train_info[]` 3단 중첩 구조이고, `TrainInfo`는 43개 필드(`h_pnr_no`, `h_trn_no`, `h_dpt_dt`, `h_seat_no`, `h_rcvd_amt`, `dvcInfoSmnsFlg`, `cmtrVlidFlg`, `apdUsrFlg`, `pbpRsvNo` 등)를 선언한다(`TicketListDao.java:14-374`). 이 서비스 메서드의 반환형은 `BaseResponse`가 아니라 앱이 명시적으로 선언한 리치 서브클래스다 — `예약대기(rsvWait)`처럼 앱 스스로 bare `BaseResponse`를 반환하는 엔드포인트와는 다르다.

라이브러리의 `get_ticket_list()`(`client.py:1487-1510`)는 `self.http.post_form(...)`을 그대로 반환하며, 별도 파서를 거치지 않는다. `post_form`(`http.py:153`)이 만드는 값은 `parse_base_response`가 만드는 순수 `BaseKorailResponse`(`h_msg_cd`/`h_msg_txt`/`str_result`/`raw` 4필드뿐, `models.py:20-25`)다. `read_models.py`/`read_parsers.py` 전체를 검색해도 `reservation_list`/`ticket_list`/`train_info`에 대응하는 dataclass나 파서가 전혀 없다. 즉 `TrainInfo`의 43개 필드는 `response.raw`를 호출자가 직접 뒤지는 것 외에는 접근 방법이 없다.

이 라이브러리의 다른 모든 read 엔드포인트(`get_maas_service_detail_list`, `get_trip_change_dates`, `pbpAcepSpec`, `plfNo`, `rcntDlvHst`, `dlvRcvCust` 등 — 본 감사에서 확인한 것만 6개)는 앱의 응답 클래스 구조를 그대로 typed dataclass로 반영하고 있어, `get_ticket_list`만 이 패턴에서 벗어나 있다.

**빈 결과 처리는 정상임을 확인**(오탐 방지 차 명시): `docs/api-status-by-service.md:332`의 2026-07-09 라이브 실측 기록은 `getTicketList`가 빈 목록일 때 `strResult=성공` 상태로 `h_msg_cd=WRT300005`("조회자료가 없습니다")를 반환함을 보여준다. `http.py:33-58 parse_base_response`는 `str_result=="FAIL"`이거나 `h_msg_cd=="WRC000288"`일 때만 예외를 던지므로, 이 빈 결과 케이스는 예외 없이 정상적으로 `BaseKorailResponse`를 반환한다 — 앱의 `BaseActivity.java:620/629`("FAIL이 아닌 미인식 코드는 성공으로 처리") 동작과 일치한다. 따라서 "빈 목록 조회 시 예외가 난다"는 결함은 **없다**.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java:14-149`(구조), `:151-374`(TrainInfo 43필드), `:376-380`(executeDao)
- 라이브러리: `src/korail_mobile_api/client.py:1487-1510`, `src/korail_mobile_api/models.py:20-25`, `src/korail_mobile_api/read_models.py`(1행도 매칭 없음), `src/korail_mobile_api/read_parsers.py`(1행도 매칭 없음)

**제안**: `TicketListResponse`/`ReservationList`/`TicketListEntry`/`TicketListTrainInfo` dataclass와 파서를 `read_models.py`/`read_parsers.py`에 추가하고 `get_ticket_list`가 이를 반환하도록 한다.

---

### 2.2 [K4-02] `build_ticket_list_form` mode="2"(구매이력)에서 날짜 범위가 앱이 절대 보내지 않는 형태로 생략 가능

**분류**: incorrect · **심각도**: medium

`build_ticket_list_form`(`payloads.py:384-409`)은 `boarding_date_from`/`boarding_date_to`를 기본값 `""`(빈 문자열)로 두고, `mode="2"`(구매이력)일 때도 이 값이 비어있어도 그대로 요청을 만든다.

앱 쪽에서 `txtIndex="2"`를 보내는 유일한 호출부는 `TicketPurchaseHistoryActivity.N0()`(`:272-291`)이며, 이 메서드는 항상 사용자가 선택한 실제 날짜 두 개(`str`, `str2`)를 `sethAbrdDtFrom`/`sethAbrdDtTo`에 채워서 호출한다. 두 개의 콜체인(`O0->Q0->N0`, `P0->L0->N0`, `:295-323`) 모두 날짜 선택 UI(및 `ticket_history_max` 다이얼로그로 범위 상한 검사)를 거친 뒤에만 `N0`를 호출하므로, **앱은 `txtIndex="2"`와 빈 `h_abrd_dt_from`/`h_abrd_dt_to`의 조합을 한 번도 만들지 않는다.**

`get_ticket_list(mode="2")`를 날짜 없이 호출하면 앱이 한 번도 만든 적 없는 조합이 서버로 나간다 — 서버가 이를 어떻게 처리하는지는 미검증. 함수 docstring(`payloads.py:396-397`)은 이미 "history mode additionally carries h_abrd_dt_from/h_abrd_dt_to boarding-date bounds"라고 스스로 명시하면서도 코드는 이를 강제하지 않는다.

(참고: `docs/deep-dive/impl-audit-reverify3-2026-07-22.md:33`의 기존 결함 RV3-03 — `txtIndex`에 페이지 번호를 넣던 문제 — 은 현재 코드에서 `mode`/`page_no`가 분리되어 있어 **이미 수정된 것으로 확인**. 아래는 그와 무관한 별개의 신규 결함이다.)

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java:272-291`(N0, 날짜 항상 채움), `:295-323`(두 호출 경로 모두 날짜 선택 후 호출)
- 라이브러리: `src/korail_mobile_api/payloads.py:384-409`

**제안**: `mode == TICKET_LIST_MODE_HISTORY`일 때 `boarding_date_from`/`boarding_date_to`가 비어 있으면 `KorailProtocolError`를 던지거나, 최소한 docstring에 "미검증 조합"임을 명시.

---

### 2.3 [K4-03] `ticketChangeCancel`(`tripChgHndgCnc.do`) 미구현 — 계획된 취소/롤백 플로우(Flow B)의 일부가 빠짐

**분류**: missing · **심각도**: medium

`docs/RELEASE_GAP_PLAN.md:300-326`의 "Flow B — Cancel/change-rollback"은 4개 라우트(`ReservationCancel`, `ReservationCancelChk`, `ticket.tripChgHndgCnc.do`, `product.ReservationCancel`)로 명시적으로 계획되었고 "core mutation endpoint count: 27 (…B:4…)"로 카운트에 포함되어 있다. `ReservationCancelChk`는 실제로 구현되어 있다(`client.py:1859`, `cancel_unpaid_hold`). 그러나 `TCCancelDao`가 감싸는 `ticketChangeCancel`(`TicketService.java:98`, `lumpStlCnt` + `lumpStlTgtNo_{index}` FieldMap)은 라이브러리 전체에서 문자열 한 번도 등장하지 않는다 — README의 "미구현과 이유" 목록에도, `RELEASE_GAP_PLAN.md`의 "Out of core v1(documented, deferred)" 목록(MAAS 취소/특실 업그레이드/선물 등을 나열)에도 이 라우트는 이름으로 등장하지 않는다. 즉 **계획은 됐지만 구현되지 않았고, 그 사실이 문서화되지도 않은** 항목이다.

앱에서 이 DAO는 승차권 변경(`change/`) 플로우 전용이 아니라 `DReservationConfirmActivity.java`와 `a6/x.java`에서도 호출되는데, 이는 "묶음결제대상(`lumpStlTgtNo`)"을 취소하는 좀 더 범용적인 롤백 호출로 보인다(정확한 트리거 조건은 스코프 밖). 자율 좌석/열차 변경 발견 단계(`getSelfSeatChgInfo`, 아래 K4-04)도 미구현이므로, 현재 라이브러리로는 self 승차권 변경을 시작할 방법도, 시작했다가 되돌릴(rollback) 방법도 없다.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TCCancelDao.java:9-41`, 호출부 `a6/x.java:109-110`, `com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java`
- 계획 문서: `docs/RELEASE_GAP_PLAN.md:300-326`(Flow B, 4개 라우트로 카운트), `:450`("Core mutation endpoint count: 27")
- 라이브러리: 전체 검색 결과 없음(`grep -rn "tripChgHndgCnc\|lumpStlTgtNo_\|TCCancel" src/` 0 hit)

---

### 2.4 [K4-04] `getSelfSeatChgInfo`(`self.seatChgInfo.do`) 미구현 — 자율 좌석/열차 변경 옵션 조회 (read gap G6, 미해소)

**분류**: missing · **심각도**: low

`CallSelfSeatChgInfoDao`(`self.seatChgInfo.do`)는 현재 승차권의 운행일/열차번호/출발·도착역/객실등급을 보내 변경 가능한 사유 목록(`chgRsnList`)과 변경 가능한 출발역/시간/잔여석(`chgStnList`)을 받는 **읽기** 호출이다(`CallSelfSeatChgInfoDao.java:64-131`, 호출부 `TCSOptionsActivity.java`). `docs/RELEASE_GAP_PLAN.md:133`이 이를 "G6 | self.seatChgInfo.do | ... | Read; not ported"로 명시적으로 읽기-갭 목록에 올려두었으나, `CHANGELOG.md`/`docs/IMPLEMENTATION_PROGRESS.md`에 이후 포팅되었다는 기록이 없고 라이브러리 소스에도 대응 코드가 없다. 이 라우트는 **읽기 전용**이라 README의 "destructive ticket operations. Not implemented"에도 해당하지 않는, 이름으로 특정되지 않은 채 방치된 read 갭이다.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java:64-131`, `:213-226`(executeDao)
- 계획 문서: `docs/RELEASE_GAP_PLAN.md:133`("G6", "Read; not ported")
- 라이브러리: 없음 (`grep -rn "seatChgInfo\|SelfSeatChg" src/` 0 hit)

---

### 2.5 [K4-05] `gurdSmsSnd`(보호자 안심 문자) 미구현

**분류**: missing · **심각도**: low

`GuardianReliefSmsDao`(`tk.gurdSmsSnd.do`)는 `pnrNo`/`jrnySqno`/수신자 휴대폰번호(`rcvPsHndyTeln`)를 보내 여정 정보를 보호자에게 SMS로 전송하는 기능이다(`GuardianReliefSmsDao.java:44-52`, 호출부 `GuardianReliefSmsActivity.java:52-58`). README의 "미구현과 이유" 목록, `RELEASE_GAP_PLAN.md`의 "Out of core v1" 목록 어디에도 이름으로 등장하지 않으며, 상태를 바꾸는("destructive") 승차권 조작도 아니어서 README의 포괄 문구에도 자연스럽게 들어맞지 않는다. 라이브러리 전체에 `gurdSmsSnd`/`GuardianRelief`/`rcvPsHndyTeln` 문자열이 전혀 없다.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/GuardianReliefSmsDao.java:1-56`
- 라이브러리: 없음

---

### 2.6 [K4-06] `pbpTkWdrw`(승차권 대리인수 철회) 미구현 — 조회(`pbpAcepSpec`)만 구현되고 취소는 없음

**분류**: partial(기능군 기준) / missing(엔드포인트 기준) · **심각도**: low

`PbpTkWdrwDao`(`tk.pbpWdrw.do`)는 대리인에게 전달된 승차권 인수를 철회하는 상태변경 호출이다(`PbpTkWdrwDao.java:9-59`, `pbpCnt`/`pbpRsvNo[]`/`pnrNo[]`, 호출부 `DeliveredActivity.java`). 짝을 이루는 조회 호출 `pbpAcepSpec`(K4 목록 #14)은 라이브러리에 정상 구현되어 있으나, 철회(쓰기) 쪽은 라이브러리 전체에서 문자열이 전혀 등장하지 않는다. README/`RELEASE_GAP_PLAN.md`의 명시적 제외 목록에도 이름으로 없다.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/PbpTkWdrwDao.java:9-59`, 호출부 `DeliveredActivity.java`
- 라이브러리: 없음

---

### 2.7 [K4-07] `deviceReset`(승차권 열람기기 초기화) 미구현 — 주의: jadx 호출부 디코드 실패, smali로 확인

**분류**: missing · **심각도**: low

`DeviceResetDao`(`tk.dvcInfoInit.do`)는 "기기정보를 초기화 하시면 해당 휴대폰에서만 승차권을 확인하실 수 있습니다"(`res/values/strings.xml:1895`, `ticket_reset_confirm`) 확인 다이얼로그 뒤에 호출되는, 특정 승차권의 모바일 열람 기기 바인딩을 초기화하는 기능이다. **jadx는 호출부(`TicketListActivity.g1(int)`, `:825-831`)를 "Method not decompiled"로 표시**하지만, `TicketListActivity.smali:5355-5735`에서 `DeviceResetDao`/`DeviceResetRequest` 생성과 `setTeln`/`setCustNm`/`setNonMbPwd`/`setStlbTrnClsfCd`/`setLatitude`/`setLongitude`/`setDptDttm`/`setTrnNo` 호출을 실제로 확인했다 — 죽은 코드가 아니라 실사용 경로다. 라이브러리에는 `dvcInfoInit`/`stlbTrnClsfCd`(다른 맥락에서만 재사용)/`deviceReset` 어디에도 대응 코드가 없다.

이 기능은 `teln`/`custNm`/`nonMbPwd`(비회원 인증 3종 세트)를 요청 필드로 갖는데, 이는 아래 K4-08(비회원 필드 공백)과 같은 근본 원인(라이브러리가 비회원 세션을 전혀 모델링하지 않음)과 연결된다.

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/DeviceResetDao.java:1-100`; 호출부 jadx `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:825-831`(미복호화, `UnsupportedOperationException` 스텁); smali `analysis/apktool/smali/com/korail/talk/ui/ticket/confirm/TicketListActivity.smali:5355-5735`(실사용 확인)
- 라이브러리: 없음

---

### 2.8 [K4-08] `build_ticket_list_form`이 비회원 전용 필드(`hidName`/`hidTeleNo`/`hidPwd`)를 보내지 않음 — 라이브러리 전체의 회원 전용 설계 반영

**분류**: missing(단, 이 엔드포인트 국지적 결함이 아님) · **심각도**: low/info

앱의 `getTicketList` 요청은 비회원 세션일 때 `hiduserYn="N"` + `hidName`/`hidTeleNo`/`hidPwd`(비회원 이름/전화/비밀번호)를 채우고, 회원 세션일 때는 `hiduserYn="Y"`만 보낸다(`TicketListActivity.java:942-950`, `TicketPurchaseHistoryActivity.java:280-288`, 두 호출부 동일 패턴). `build_ticket_list_form`(`payloads.py:384-409`)은 `hiduserYn="Y"`만 무조건 보내고 비회원 3필드를 아예 파라미터로 받지 않는다.

이는 이 엔드포인트만의 문제가 아니라 **라이브러리 전체가 비회원(비로그인, 이름+전화+비밀번호 인증) 세션을 모델링하지 않는** 설계에서 비롯된다 — `session.py`에는 `JSESSIONID` 기반 회원 세션 상태만 있고 비회원 신원을 담는 필드가 없다(전역 검색 결과 `hidName`/`hidTeleNo`/`hidPwd` 문자열이 `src/` 전체에 0건). `MEMORY.md`의 개시범위 기록도 이메일(회원) 로그인만 언급한다. README/`RELEASE_GAP_PLAN.md`는 "정기권 구매"·"단체예약"처럼 비회원 지원 제외를 명시적으로 선언하지는 않았지만, 시스템 전반에 일관되게 나타나는 설계이므로 이 항목 하나만 "국지적 결함"으로 보고하기보다 **범위 결정 사항으로 사용자에게 확인이 필요한 항목**으로 남긴다.

(참고: `tsRsStnCd` 필드는 이 finding에서 제외했다 — `setTsRsStnCd`가 `TicketListDao.java` 선언부 외에는 앱의 어느 호출부에서도 호출되지 않아, 현재 앱 버전 자체에서 죽은 필드로 확인됨. 라이브러리가 이를 보내지 않는 것은 결함이 아니라 앱과 일치하는 동작이다.)

**근거**:
- 앱: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:936-954`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketPurchaseHistoryActivity.java:272-291`
- 라이브러리: `src/korail_mobile_api/payloads.py:384-409`, `session.py`(비회원 상태 없음 확인)
- `tsRsStnCd` 죽은 필드 확인: `grep -rln "setTsRsStnCd" analysis/` → 선언 파일(`TicketListDao.java`/`.smali`)만 나오고 호출부는 0건

---

## 3. 확인했으나 문제 없음(오탐 방지 기록)

- **`getTicketList` 빈 결과 처리**: 예외 없이 정상 반환됨을 라이브 실측 문서로 확인(§2.1 참조). "high" 등급 결함 가설을 세웠으나 기각.
- **RV3-03(`txtIndex`/페이지 혼용)**: 기존에 지적된 결함이나 현재 코드(`payloads.py:380-409`)에서 `mode`와 `page_no`가 분리되어 **이미 수정됨**을 확인. 재보고하지 않음.
- **`pbpAcepSpec`/`duplicationCheck`의 Java `int` 필드**(`Seat.scarNo`, `DuplicationCheckResponse.rsvCnt`) — Gson이 따옴표 있는 숫자 문자열도 강제형변환한다는 점까지 라이브러리 주석(`read_parsers.py:2212-2217`, `:2256-2257`)에 명시되어 있고 정확히 처리됨. 폼필드(FormUrlEncoded)로 보내는 `tkCnt`/`pbpCnt`(앱은 Java `int`, 라이브러리는 Python `str`/`int`→`str`)도 와이어 상 동일한 문자열로 직렬화되므로 타입 불일치 결함 아님.
- **`ReservationWaitService.rsvWait` 요청 필드 순서/타입**: `RsvWaitDao.executeDao()`의 인자 순서(`Device, Version, Key, txtPnrNo, txtPsrmClChgFlg, txtSmsSndFlg, txtCpNo`)와 `build_standby_wait_form`(`mutation_payloads.py:1197-1208`)의 필드 삽입 순서가 정확히 일치. `txtCpNo`를 SMS 미동의 시 키 자체를 생략하는 것도 앱의 null-getter → Retrofit 필드 생략과 정확히 일치(`mutation_payloads.py:1151-1154`).
- **`MaasServiceDetailListDao.AddSrvItem`(20필드) ↔ `MaasServiceDetail`**: 1:1 완전 매칭 확인(`read_models.py:774-796`).
- **`TripChgInfoDaoResponse`(`lastRunDt`/`tripChgDate`/`tripChgDates`) ↔ `TripChangeDateResponse`**: 3필드 모두 일치(`read_models.py:805-810`).
- **예약대기 안전게이트**: `KORAIL_MUTATION_ROUTES`/`KORAIL_MUTATION_ROUTE_CATEGORIES`(`safety.py:205-293`)에 `reservationWait.ReservationWait`가 `"reserve"` 카테고리로 정확히 등록되어 있고, 왜 별도 카테고리가 아닌지에 대한 근거도 앱 흐름(`ui/inquiry/rir/orr/a.java:222-225`)과 함께 문서화됨. 게이트 우회 경로 없음.

## 4. 참고: 문서화된 의도적 제외 목록(defect 아님, 재확인만)

- **셀프 체크인 4종**(`checkin.info/psbFlg/reg/cnc.do`): README §"무엇이 구현되지 않았는가" — "Check-in, membership mutation, point/mileage mutation, and destructive ticket operations. Not implemented in this version." 및 `docs/RELEASE_GAP_PLAN.md:421-427`("Excluded domain today (EXCLUDED_API_DOMAINS)")로 명시. 사용자 지시의 "의도적으로 제외된 범위" 원칙에 따라 `info`로만 기록.
- **MAAS 부가서비스 취소 3종**(`cancelPay.do`/`coptCnc.do`/`cncFee.do`): `docs/RELEASE_GAP_PLAN.md:440-448` "Out of core v1 (documented, deferred)" 목록에 라우트명까지 정확히 나열. `info`.
- **특실 업그레이드 2종**(`reqUpgradeSeat`/`procUpgradeSeat`): 위 같은 목록에 "upgrade procUpgrade" 명시, `reqUpgradeSeat`는 읽기갭 목록 G7에서 "procUpgrade의 짝"으로 함께 유예됨. `info`.

## 5. 검증 한계

- 서버 실측은 `docs/api-status-by-service.md`에 기록된 2026-07-09/14/15 스냅샷만 인용했고, 본 세션에서 별도 라이브 호출은 하지 않았다(읽기 전용 지시 준수).
- `MaasCancelDao`(`getMaasCancel`)의 실제 호출 조건은 `docs/deep-dive/agent-reports/09-ticket-my-ticket.md:403`도 "이번 범위에서 확인한 흐름은 취소수수료조회/취소 중심"이라며 불확실성을 남겨두었다 — 이 감사에서도 정확한 트리거를 추가로 확인하지 못했다.
- `TCCancelDao`가 `DReservationConfirmActivity`/`a6/x.java`에서 정확히 어떤 조건에 호출되는지(승차권 변경 롤백 전용인지, 더 범용적인 묶음결제 취소인지)는 스코프 밖이라 완전히 규명하지 못했다. K4-03의 결함 판정(엔드포인트 부재)에는 영향 없음.
