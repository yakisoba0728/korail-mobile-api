# Korail 감사 3차 검증 — verifier-1 (21건)

작성 2026-07-27. 저장소는 읽기 전용으로만 접근(수정·git 상태변경 없음).
모든 근거를 직접 열어 확인했다. 상수 주장은 smali 로 재확인했다.

## 요약표

| ID | 원심각도 | 판정 | 교정심각도 |
|--|--|--|--|
| K1-02 | missing/low | CONFIRMED | low |
| K1-04 | missing/info | PARTIAL | info |
| K3-06 | risk/low | CONFIRMED | low |
| K3-04 | missing/low | PARTIAL | info |
| K4-04 | missing/low | CONFIRMED | info |
| K4-08 | missing/low | CONFIRMED | low |
| K6-01 | missing/high | CONFIRMED | low |
| K6-05 | missing/info | CONFIRMED | info |
| K8-04 | missing/medium | PARTIAL | info |
| K8-03 | missing/low | CONFIRMED | info |
| P2MIS-03 | risk/low | CONFIRMED | info |
| P2INC-01 | risk/medium | CONFIRMED | low |
| P2INC-04 | incorrect/low | CONFIRMED | info |
| P2INC-03 | doc-drift/info | CONFIRMED | info |
| P2SAF-03b | risk/medium | REFUTED | info |
| P2SAF-12 | doc-drift/medium | CONFIRMED | low |
| P2SAF-11 | risk/low | PARTIAL | low |
| P2SAF-15 | risk/info | REFUTED | info |
| P2CRO-04 | risk/medium | CONFIRMED | low |
| P2CRO-15 | unverifiable/medium | UNVERIFIABLE | low |
| P2CRO-09 | doc-drift/low | CONFIRMED | info |

판정 규칙: CONFIRMED = 실제 갭/불일치이고 결함으로 보고할 값이 있음.
PARTIAL = 사실관계는 맞으나 "결함/미확인" 프레이밍이 무너짐.
REFUTED = 결함이 아님(주장 스스로 비결함이라 결론낸 기록 포함).
UNVERIFIABLE = 근거로 결론을 낼 수 없음.

---

## K1-02 — 간편(소셜) 로그인 wire-shape 재현 불가 → **CONFIRMED (low)**

앱 (직접 확인):
- `analysis/jadx/sources/k5/b.java:236-243` `executeEasyLogin(str,str2,str3)` 는
  `setLoginType(str)`/`setCustId(str2)`/`setCheckValidPw(str3)` 만 설정. loginId/loginPw/idx 미설정.
- **주장이 놓친 중요한 사실**: DTO 필드 `loginType` 의 wire 이름은 `txtInputFlg` 다.
  `network/dao/login/LoginDao.java:240` 이
  `login(getDevice(),getVersion(),getKey(),getLoginId(),getLoginPw(),getLoginType(),
  getCheckValidPw(),getCustId(),getEtrPath(),getIdx())` 로 위치인자 호출하고,
  `network/dao/login/LoginService.java:17-18` 의 6번째 `@Field` 가 `txtInputFlg` 다.
  → 앱 간편로그인 wire = `Device/Version/Key/txtInputFlg=<K|N|G|D>/checkValidPw/custId`.
  (P2INC-03 이 경고한 "DTO 필드명 ≠ wire 이름" 함정의 또 다른 사례.)
- `S4/u.java:126-128` isEasyLoginType 확인. `R1/x.java:34` `MAX_AD_CONTENT_RATING_G="G"` 확인.
  `f28874D="D"` 는 `network/dao/addService/HelpSrvCustDao.java:19` 에 있다
  (주장은 `dao/cust/` 로 적었다 — 경로 오기, 값은 정확).

라이브러리 (직접 확인):
- `src/korail_mobile_api/session.py:146-153` — `login(member_no, password, *, ...)`, 둘 다 필수 위치인자.
- `session.py:193-201` form 은 항상 `txtMemberNo`/`txtPwd` 를 채우고, 필터는
  `{k:v for k,v in form.items() if v is not None}` (`:203-206`) 이라 **빈 문자열도 전송된다**.
- `session.py:186` `input_flag or infer_login_input_flag(member_no)`, `:63-70` 의 infer 는
  email/phone/memberNo 3종만 반환 → "K"/"N"/"G"/"D" 를 명시 지정하지 않으면 나올 수 없다.

결론: 필드-부재 vs 필드-존재-빈값의 차이가 실재하고, 소셜연동 계정 재로그인 경로가 없다.
미구현 기능이며 기존 경로를 망가뜨리지 않으므로 low 유지.

---

## K1-04 — certification 8건 미구현 → **PARTIAL (info)**

앱 (직접 확인, 전부 존재): `dao/certification/CertificationService.java:22-23`
(applyDisabilityCertification), `:25-26`(certCongressperson), `:28-30`(certMerit,
`txtJuminNo7` 평문 필드 실재 확인), `:32-33`(disabledCertification), `:39-40`/`:42-43`
(govermentCertification1/2), `:48-50`·`:56-58`(nonMember.NonMemTicket 오버로드 2개).
`dao/certification/BusReservationService.java:23-25`(reservationChange).
라이브러리: 해당 경로 송신 코드 0건 (grep 확인).

**주장이 무너지는 지점** — 주장은 "의도적 제외인지 단순 누락인지 확인불가"라고 했다.
그러나 `README.md:326-331` 이 정확히 이 6건을 명시적으로 제외 선언한다:
> "**Identity-document submission.** The welfare certification routes
> (`certification.disabled.do`, `MeritCert`, `assemblyCert`, `pbep.*`) each transmit a
> 주민등록번호 fragment or a government certificate number and *register* an entitlement
> against the account. Shipping an unverifiable identity-document submitter was judged
> worse than not having one."

`applyDisabilityCertification` 도 같은 경로의 read 오버로드만 등재하고 write 형태를
핀으로 막았다고 `safety.py:62-68`, `read_payloads.py:1556-1567` 가 명시.
남는 것은 nonMember 예약과 reservationChange 뿐이며 후자는 K6-05 와 중복이고
`docs/RELEASE_GAP_PLAN.md:277, :867, :1011-1012` 에 이연 기록이 있다.
→ 사실은 맞으나 "확인불가" 결론이 성립하지 않는다. PARTIAL / info.

---

## K3-06 — STANDBY/MERGE_STANDING 자유석 '003' 미반영 → **CONFIRMED (low)**

앱:
- `analysis/jadx/sources/c5/a.java:86-96` —
  `if (J.isFreeSeat(selectSeatTypeCode, h_gen_rsv_cd, h_free_rsv_cd))
   { oSeat.setSeatAttCd4(i10, p.NORMAL_FREE.getCode()); } else { ... t2() ... }`
- `analysis/jadx/sources/S4/J.java:57-59` —
  `isFreeSeat = o.GENERAL.getCode().equals(str) && "13".equals(str2) && "11".equals(str3)`
- **smali 재확인**: `analysis/apktool/smali/K4/p.smali:50-87` — `<clinit>` 의 첫 enum 이
  `const-string v1,"NORMAL_FREE"` / `const-string v3,"자유석"` / `const-string v4,"003"`
  → `sput-object v7, LK4/p;->NORMAL_FREE`. **'003' 확정** (jadx 단독 근거 아님).

라이브러리:
- `src/korail_mobile_api/mutation_payloads.py:836-848` `_seat_attribute_key(1): "015"` 하드코딩,
  `:855-859` 2번째 leg 도 `"015"` 하드코딩. 파일 전체 `free_reservation_code` 참조 **0건**.
- `src/korail_mobile_api/models.py:343` 에 필드 존재, `:456` 에서 파싱됨 → 값은 있는데 안 쓴다.
- 도달성 확인: `mutation_payloads.py:936-951` STANDBY 는 `h_gen_rsv_cd` 검사를 주석까지 달아
  명시적으로 생략(`:950-951` "Deliberately NO h_gen_rsv_cd check"), `:956-975` MERGE_STANDING 도 동일.
  `:988-991` 의 `general_reservation_code != "11"` 거부는 두 경로에 도달하지 않는다.
  STANDBY 는 `:938-943` 에서 GENERAL 캐빈을 강제하므로 isFreeSeat 의 GENERAL 전제도 충족.
  → `h_gen_rsv_cd="13"` && `h_free_rsv_cd="11"` 인 대기가능 열차에서 앱 '003' vs 라이브러리 '015'.

보강: 라이브러리는 형제 함수 `isStndSeat` 는 `mutation_payloads.py:1085-1102` 로 충실히 이식했다.
즉 같은 `S4/J.java` 의 두 판정 중 하나만 이식된 비대칭이다. 두 경로 모두 live 미검증이라 low 유지.

---

## K3-04 — reservation.seatAssign.do 미구현 → **PARTIAL (info)**

앱: `ui/booking/seatAssign/SeatAssignBookingActivity.java:120-132`(setCommutationTicket),
`:134-146`(setGPassTicket), `:167-176`(setPassTicket) 이 모두
`W4.a.getSeatAssignReservationRequest(...)` 경유. `:148-150` setGeneralTicket 본문 공백.
**smali 재확인**: `analysis/apktool/smali/com/korail/talk/ui/booking/seatAssign/
SeatAssignBookingActivity$b.smali:697-701` — `.method public setGeneralTicket(I)V / .locals 0 /
return-void` → 진짜 빈 메서드(jadx 아티팩트 아님).
`:152-163` setNCCardTicket 은 `getNCardReservationRequest` 로 가고 이건 라이브러리에 구현돼 있다
(`mutation_payloads.py:1655, :1674` 가 그 호출부를 인용).

라이브러리: 송신 경로 0건. `tests/test_p0_read_endpoints.py:682-690` 이 이 경로를
read allowlist 밖으로 못박음. `docs/RELEASE_GAP_PLAN.md:276`, `:1011` 이연 기록.

→ 사실 전부 참이지만 살아있는 호출부가 전부 정기권/G-Pass/A-Pass 좌석지정이고
문서화된 이연 항목이다. 사용자가 제외한 정기권·패스 제품군 안이라 "결함" 프레이밍이 서지 않는다.
PARTIAL / info.

---

## K4-04 — self.seatChgInfo.do 미구현 → **CONFIRMED (info)**

라이브러리: `src/` 전체 `seatChgInfo`/`SelfSeatChg` **0건**(직접 grep).
`docs/RELEASE_GAP_PLAN.md:133` — `| G6 | self.seatChgInfo.do | POST | Self seat-change info
(options/stations) | TicketService.java:54 | Read; not ported |` 확인.
CHANGELOG / IMPLEMENTATION_PROGRESS 에 포팅 기록 0건.
README 의 제외 목록(`:322-354`)에도 해당 없음 — 읽기 전용이라 "destructive ticket operations"
문구에 걸리지 않는다는 주장의 논리는 성립.

주장 중 **틀린 부분**: "이름으로 특정되지 않은 채 방치된 갭" — RELEASE_GAP_PLAN:133 에
이름·경로·사유가 명시돼 있다. 실제 손상은 없으므로 low → info.

---

## K4-08 — build_ticket_list_form 비회원 필드 미전송 → **CONFIRMED (low)**

앱: `ui/ticket/confirm/TicketListActivity.java:942-950` —
`if (hVar.isNonMember()) { setHiduserYn("N"); setHidName(...); setHidTeleNo(...);
setHidPwd(...); } else { setHiduserYn("Y"); }` 직접 확인.
Retrofit 선언: `network/dao/myTicket/MyTicketService.java:18` 에 `hidName/hidTeleNo/hidPwd/
tsRsStnCd` 가 실제 `@Field` 로 존재 확인.
라이브러리: `src/korail_mobile_api/payloads.py:405-411` — `"hiduserYn": "Y"` 고정,
비회원 3필드 파라미터 자체가 없음. `src/` 전체 `hidName`/`hidTeleNo`/`hidPwd` **0건**.
README 제외 목록에 비회원 세션 항목 없음 → 명시적 제외로 볼 근거 없음. low 유지.

---

## K6-01 — 오프라인 반환번호 환불 미구현 → **CONFIRMED, high → low**

라이브러리: `verifyOnlineRefunds`/`executeOnlineRefunds`/`retNo1`/`retDvCd` 전부 `src/` **0건**.
**주장의 grep 목록 중 `acepCustNm` 은 오류** — `src/korail_mobile_api/redaction.py:32` 에 실재한다
(마스킹 키로만 등재, 송신 경로는 없음). 결론은 바뀌지 않는다.
계획 근거 확인: `docs/RELEASE_GAP_PLAN.md:400-402` 표에 두 라우트, `:449-450`
"Core mutation endpoint count: 27 (A:7, B:4, C:10, **D:5**, E:4)", `:865-866` 체크리스트 미체크.

**심각도 정정 사유**:
1. 그 체크리스트 항목(`:865-866`)은 online refund 와 offline refund 를 **한 줄에 묶어** 두었고,
   online refund 는 이미 구현돼 있다(`client.py:2029` refund + `safety.py` 라우트).
   즉 체크박스 미체크는 미구현의 증거가 아니라 문서 갱신 누락이다.
2. 이 감사 기준의 high 는 "실서버에서 실패하거나 잘못된 결과를 낸다"인데, 순수 미구현은
   잘못 나가는 요청을 만들지 않는다.
3. 비로그인 종이승차권 환불은 K4-08 과 같은 뿌리(회원전용 세션 모델) 밖의 기능이다.
→ low.

---

## K6-05 — 예약 인원 변경(reservationChange) 미구현 → **CONFIRMED (info)**

앱: 라우트·필드는 정확하나 **인용 위치가 틀렸다**. `reservation.reservationChange.do` 를
선언하는 것은 `ReservationCancelService.java` 가 아니라
`dao/certification/BusReservationService.java:23-25` 다 (`pnrNo/chgTno/totPrnb/stndFlg/
evntWctFlg/wctHndgCncDvCd/lrgCrgFlg/psgCnt` + `@FieldMap×5` — 필드 목록은 주장대로 정확).
`ReservationChangeDao` 는 `dao/reservationCancel` 패키지에 있으나 서비스 인터페이스가 아니다.
라이브러리 0건. `docs/RELEASE_GAP_PLAN.md:277, :867, :1012` 이연 기록 확인.
주장 스스로 "결함이 아니라 참고용 기록"이라 결론냈고 나도 동의한다.
info 등급의 정확한 기록(사실·심각도 모두 맞음)이므로 CONFIRMED / info 로 둔다 —
K4-04(같은 성격의 추적된 미포팅 갭)와 동일 취급.

---

## K8-04 — callCrew + pushUpdate 미구현 → **PARTIAL (info)**

앱: `dao/push/PushService.java:13-14` callCrew(22 `@Query`), `:16-17` callCrewRequestList,
`:19-20` cmtrKndPassMenu, `:22-23` pushUpdate(`job_dv_cd`/`tnsm_flg1~4`/`dptUsrInpTnum`/
`arvUsrInpTnum`) — 전부 직접 확인.
라이브러리: `client.py:741` `push.crwCallRq.do`, `:757` `push.cmtrKnd.do` 구현 확인.
`push.callCrew.do` / `push.update` 0건.

**주장이 무너지는 지점** — callCrew 는 `README.md:344-347` 이 명시적으로 제외 선언한다:
> "**The crew-call submission.** `/classes/com.korail.mobile.push.callCrew.do` is the
> state-changing sibling of the crew-request read and remains excluded from the transport
> allowlist and the public client. Reading crew request options never submits a crew call."

`tests/test_p0_menu_reads.py:64` 도 `CALL_CREW_MUTATION_PATH not in KORAIL_EXACT_REQUEST_FIELDS`
로 부재를 테스트로 못박았다. 즉 "반쪽 기능"이 아니라 **의도된 설계**다.
남는 것은 pushUpdate 하나뿐이고 이것도 알림 수신플래그 갱신이라 핵심 흐름 무관.
→ PARTIAL / info.

---

## K8-03 — authQRLocation(qr.bchTripSv.do) 미구현 → **CONFIRMED (info)**

앱: `dao/common/CommonService.java:23-25` —
`@POST("/classes/com.korail.mobile.qr.bchTripSv.do") @FormUrlEncoded
authQRLocationDao.QRLocationResponse authQRLocation(Device, Version, qrcode, latitude, longitude)`
확인. 라이브러리 0건.
주장 스스로 "다른 흐름이 이 값에 의존하지 않는다"고 했고 맞다. 실제 갭이지만 무해 → info.

---

## P2MIS-03 — 핀 없는 read 라우트 13개 → **CONFIRMED (info)**

**기계적으로 재계산해 주장의 숫자를 그대로 재현했다** (`python3` 로 safety 모듈 로드):
```
pins(KORAIL_EXACT_REQUEST_FIELDS) = 45
read routes = 58, mutation routes = 8   → 총 66
read paths without pin = 13
mutation paths without pin = 8
```
핀 없는 read 13개: `common.code.do`, `common.stationdata`, `common.stationinfo`,
`login.Login`, `myTicket.MyTicketList`, `qry.chtnStn.do`, `research.actualTrainSchedule.do`,
`schedule.runDt`, `seatMovie.ScheduleView`, `/ebizcross/getUUID.do`,
`/ebizmaas/EbizMaasStationList.do`, `/file/CACHE/prdMobilePlusMain.cache`,
`/file/CACHE/prdMobilePlusNotice.cache`.

코드 확인: `safety.py:1384-1386` `allowed = KORAIL_EXACT_REQUEST_FIELDS.get(route_path);
if allowed is None: return` — 이후의 중복키(`:1387-1394`), 집합(`:1413-1420`),
스칼라 타입(`:1427-1430`) 검사가 전부 건너뛰어진다.
범위 한정도 맞다: 순서있는 시퀀스 입력은 `:1376-1379` 가 조기 반환보다 **먼저** 거부한다.
`common.code.do` 가 리스트+int 를 싣는다는 것도 확인 — 앱 `dao/common/CommonService.java:30-32`
가 `@Field(Constants.CODE) List<String>`, `deviceWidth/deviceHeight/OSVersion` 을 `int` 로
선언하고, `payloads.py:366` `"code": [code] if isinstance(code,str) else code`,
`:376 form["OSVersion"] = config.android_sdk_int` (`config.py:31` int) 이 그대로 대응.
`myTicket.MyTicketList`(비회원 PII 3필드 보유)와 `seatMovie.ScheduleView`(41필드)도 확인.

**심각도 하향 사유**: 1차 방어선(`assert_read_only_route` + 라우트 allowlist)은 이 13개에도
그대로 걸린다. 핀은 2차 형태검증이고, 현재 모든 요청은 핀된 빌더가 만든다 — 주장 스스로
"현재 잘못 나가는 요청은 없다"고 인정. 게이트에 구멍이 난 것이 아니라 하드닝 계층의
커버리지가 78%(45/58)라는 기록이다. low → info.

---

## P2INC-01 — hidMnsStlAmt1 출처 우선순위 역전 → **CONFIRMED, medium → low**

앱 체인 (직접 추적, 전부 확인):
- `ui/payment/PaymentActivity.java:168-203` `G0()` — `:169` `if (isReservationResponseNull())`
  일 때만 `getIntent().getIntExtra("RECEIVED_AMOUNT", -1)`. 아니면 `:183-199` 좌석행에서
  `Σ(h_seat_prc+h_seat_fare) − Σ((h_seat_prc+h_seat_fare)−h_rcvd_amt)`. **h_tot_rcvd_amt 미참조.**
- `:553-555` `isReservationResponseNull() { return C0804d.isNull(this.f29867n); }`
  (f29867n = "RESERVATION" extra).
- `ui/menu/BasketTicketActivity.java:637-641` — `putInt("RECEIVED_AMOUNT",
  parseInt(getH_tot_rcvd_amt()))` **와 동시에** `putSerializable("RESERVATION", ...)`
  → PaymentActivity 에서 f29867n 이 non-null 이 되어 `:170` 분기가 죽는다.
  reservationResponse 가 null 인 else 가지(`:642-645`)는 `h_tot_rcvd_amt` 가 아니라
  번들의 `h_rcvd_amt` 문자열을 쓴다. → 앱에 h_tot_rcvd_amt 가 결제금액으로 가는 살아있는 경로 없음.
- 전송: `B6/AbstractC1269e.java:405-406` `bundle.putString("PAYMENT_AMOUNT",
  String.valueOf(getReceivedAmount()))` → `V4/a.java:27`
  `setHidMnsStlAmt(1, bundle.getString("PAYMENT_AMOUNT"))`.
  (`hidMnsStlAmt1` 리터럴이 analysis/ 전체에 0건인 이유는 PaymentMethod 가 인덱스를 붙여
  키를 조립하기 때문이다 — 주장의 체인 자체는 옳다.)

라이브러리: `mutation_parsers.py:83-85` `total = _optional_string(raw,"h_tot_rcvd_amt")`;
숫자면 즉시 return. 좌석 합산(`:87-121`)은 폴백. `mutation_payloads.py:1402
"hidMnsStlAmt1": amount`.

**심각도 하향 사유**: (a) 두 값이 실제로 어긋난 사례가 저장소·문서 어디에도 없다
(fixture 전부 합성 — 주장 스스로 인정). (b) 두 값 모두 서버가 같은 예약에 대해 준 금액이고
`mutation_parsers.py:70-79` 주석이 앱 근거로 등가를 논증한다. 구체적 실패 조건을
제시하지 못하므로 medium(특정 조건에서 실패) 기준을 충족하지 않는다 → low.
다만 "앱이 일부러 무시하는 필드를 우선한다"는 방향성 자체는 실재하므로 CONFIRMED.

---

## P2INC-04 — txtJrnyCnt 제로패딩 손실 → **CONFIRMED, low → info**

앱: `ui/reservation/confirm/activity/DReservationConfirmActivity.java` 의 `executeRsvCancel`
가 `setTxtJrnyCnt(reservationResponse.getH_jrny_cnt())` 로 원본 그대로 에코.
라이브러리: `mutation_payloads.py:1230-1233` `legs = int(journey_count)`,
`:1245` `"txtJrnyCnt": str(legs)` → `"0001"` → `"1"`. 사실 확인.

**심각도 하향 사유** (실측 반증):
1. `docs/verification-record.md:955-960` — 라이브 reserve → cancel 왕복에서 취소가
   `IRG000000` 으로 성공. 즉 무패딩 `"1"` 을 서버가 수용했다.
2. 예약 생성 폼에서는 **앱 자신이** `txtJrnyCnt` 를 `trainInfoArr.length` 로 만들어
   `"1"`/`"2"` 무패딩으로 보낸다 (`docs/verification-record.md:683`, `C5/a.java:55`).
   같은 필드명을 서버가 무패딩으로 받는다는 앱 자체 증거다.
관측된 실패 조건이 없고 반대 증거가 두 건 있으므로 info.

---

## P2INC-03 — 자기 오탐 철회 기록 → **CONFIRMED (info)**

인용 근거를 전부 재확인했고 전부 사실이다:
- `analysis/apktool/smali/com/korail/talk/network/dao/research/
  ConvenienceSettingDao$ConvenienceSettingRequest.smali:22` `.field private reqSqno:Ljava/lang/String;`
  vs wire 이름은 `regSqno` — `dao/research/ResearchService.java:44` (getCustTripInfo,
  주장은 :45 로 적었으나 실제 44행). 라이브러리 `read_payloads.py:797-802`
  `{custMgNo, medDvCd:"03", regSqno:"0"}` 및 `safety.py:943-945` 핀 정확.
- `analysis/apktool/smali/com/korail/talk/network/dao/trainsInfo/
  Price2FareDao$Price2FareRequest.smali:149-162` — `setTrnCnt` 가
  `iget-object p1, ...->trnCnt` → `iput-object p1, ...->trnCnt` 자기대입. **실제 no-op 확정**
  (디컴파일 아티팩트 아님). 따라서 `trnCnt` 는 항상 null → Retrofit 드롭 → 라이브러리가
  안 보내는 것이 옳다.
인용 사실이 전부 참이고 심각도(info, 방법론 기록)도 정확하므로 CONFIRMED / info.
(교훈은 유효하다: K1-02 에서 같은 함정을 또 확인했다 — `loginType` DTO 필드의 wire 이름은
`txtInputFlg` 다. **반드시 Retrofit annotation 값으로 grep 해야 한다.**)

---

## P2SAF-03b — 뮤테이션 8개 라우트 필드 미고정 → **REFUTED (info)**

사실관계는 전부 맞다 (기계 확인):
- 뮤테이션 라우트 8개 중 `KORAIL_EXACT_REQUEST_FIELDS` 에 등재된 것 **0개**.
- `dao/certification/CertificationService.java:52-54` / `:60-62` 가 실제로
  `certification.TicketReservation` 의 서로 다른 두 오버로드,
  `:48-50` / `:56-58` 이 `nonMember.NonMemTicket` 의 두 오버로드 — 확인.
- `http.py:239-241` "``data`` is sent verbatim … no read-only field allowlist applies." 확인.

**그러나 결함이 아니다.**
1. 명시적·문서화된 설계다. `http.py:235-241` docstring 이 "double-gated" 라고 계약을 적었고,
   `tests/test_reference_derived_reads.py:239` 가 `REFUND_MUTATION_PATH not in
   KORAIL_EXACT_REQUEST_FIELDS` 로 **부재를 테스트로 못박았다**.
2. 1차 게이트는 그대로 살아 있다: `http.py:250-255` 가 `require_mutation_consent(consent,
   category)` 와 `consent.dry_run is False` 를 강제하고 `assert_mutation_route` 로 대상을
   8개로 제한한다. 카드 라우트는 `KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 로 한 겹 더 걸린다.
   즉 **게이트를 우회하는 경로가 아니다.**
3. read 경로가 뮤테이션 라우트로 새지 않는 것도 직접 확인했다 — `http.py:164`
   `post_form` 첫 줄이 `assert_read_only_route("POST", path)`, `http.py:401`
   `get_json` 이 `assert_read_only_route("GET", path)`, `http.py:184` 가 조립 완료된
   폼 전체에 `assert_read_only_request_fields` 를 건다. 뮤테이션 8경로와
   `KORAIL_READ_ONLY_ROUTES` 58경로는 교집합 0(기계 확인)이므로
   docstring 의 "The read-only path still refuses these routes" 는 코드와 일치한다.
4. 주장 스스로 "빌더 경유 경로만 쓰면 문제되지 않으므로 즉시 악용 결함은 아니다"라고 인정.
consent 를 이미 가진 호출자가 폼을 임의로 짤 수 있다는 것은 이 API 의 계약이지 구멍이 아니다.
"의도된 안전설계를 결함이라 한 주장" → REFUTED / info.

---

## P2SAF-12 — reserve_transfer docstring 오안내 → **CONFIRMED, medium → low**

라이브러리 (직접 확인):
- `mutation_payloads.py:1230-1240` 거부 조건은 `legs is None or legs < 1` — **다구간 홀드를 허용한다.**
  `:1219-1228` 주석이 "A 환승 hold carries two journeys, and refusing it here would leave a live
  transfer reservation with no way to release it" 라고 이유까지 명시.
- 그런데 `client.py:1731-1733` docstring: "note that :meth:`cancel_unpaid_hold` currently
  accepts single-journey holds only, so a live transfer hold cannot be released through this
  client." → **코드와 정반대.**
- `client.py:1840-1846` `cancel_unpaid_hold` docstring 도 "single-journey reservation hold" /
  "requires ``hold`` to be one successful (``SUCC``) single-journey hold" 로 같은 오류.
- **1·2차가 짚지 않은 세 번째 위치**: `docs/verification-record.md:844-853` 도 여전히
  "It requires a hold whose `h_jrny_cnt` is numerically one, so a two-journey hold is refused
  before a form is built" 라고 적고 "the fix … was reported rather than made" 라고 한다.
  실제로는 수정이 들어갔고 문서 3곳이 남았다.

앱 근거(`DReservationConfirmActivity` 가 `getH_jrny_cnt()` 를 에코)도 확인 — 빌더가 옳고 문서가 틀렸다.

**심각도**: 같은 문단(`client.py` 및 `README.md:311-315`, `verification-record.md:852-854`)이
"do not send one unless you are prepared to cancel it in the KORAIL app or on the website"
라는 폴백 지침을 함께 준다. 코드는 정상 동작하고 운영자에게 대체 해제수단이 안내돼 있으므로
고아 PNR 이 실제로 방치될 경로는 좁다. medium → low (1차의 low 판단이 옳았다).

---

## P2SAF-11 — DynaPath 403 판별 범위 → **PARTIAL (low)**

사실관계 확인:
- `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:59-90` — RetrofitError 의
  응답 헤더를 순회하며 `"DynaPath-Result"` 이름이면 값이 음수인지만 본다. 경로 조건·상태코드
  조건 없음. 확인.
- `src/korail_mobile_api/http.py:68-72` — `response.status_code == 403 and path in
  DYNAPATH_ALLOWLIST_PATHS and dynapath_rejected`. 확인. 아니면 `:83-87` 밋밋한
  `KorailTransportError`.
- `constants.py:420-430` 6경로, `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`
  의 `String[] strArr = {...}` 6개와 정확히 일치 확인. `:35` `request.getUrl().contains(str)`
  부분일치 vs `http.py:127-128` 정확일치도 확인 — 라이브러리가 더 좁고 안전한 방향.

**주장이 약해지는 지점 (주장의 피해 메커니즘이 성립하지 않음)**:
1. `src/korail_mobile_api/http.py` 전체에 **재시도 로직이 없다**(`grep -n "retry"` 0건).
   "재시도가 무의미한 차단을 일시적 오류로 오인" 이라는 피해는 라이브러리 안에서 발생하지 않는다.
2. 토큰을 붙이는 쪽도 앱·라이브러리 모두 같은 6경로다(ExecuteDao.java:27). 서버가 그 밖의
   경로에 DynaPath-Result 를 실을 근거가 없어 가정적이다.
3. 주장이 언급하지 않은 두 번째 협소화가 하나 더 있다: 라이브러리는 `status_code == 403` 을
   요구하는데 앱은 상태코드를 아예 보지 않는다. 즉 allowlist 경로 안에서도 비-403 응답에
   헤더가 실리면 라이브러리는 놓친다 — 이쪽이 오히려 더 구체적인 협소화다.
사실은 맞고 개선 여지도 있으나 주장이 제시한 피해가 성립하지 않으므로 PARTIAL / low.

---

## P2SAF-15 — logout 이 읽기 allowlist 에 등재 → **REFUTED (info, 결함 아님)**

- 앱 `dao/login/LoginService.java:29-30` `@GET("/classes/com.korail.mobile.login.Logout")
  BaseResponse logout();` 무인자 확인.
- `safety.py:76` 등재 확인. 사유는 `safety.py:53-60` 에 "two of the entries are session routes
  rather than reads: the login POST and the server-side logout GET (cookie-authenticated,
  zero parameters, not a mutation)" 로 명시돼 있음.
- `session.py:251-268` 실패를 삼키고(`except KorailApiError: pass`) 항상 `clear_session()`.
- 추가 확인: `tests/test_http.py:393` 이 `KORAIL_EXACT_REQUEST_FIELDS[logout_path] ==
  frozenset()` 로 "인자 0개"를 테스트로 못박았다.
REFUTED 근거는 "주장자가 결함이 아니라고 했으니까"가 아니라 **설계가 문서·테스트로
명시돼 있기 때문**이다: `safety.py:53-60` 이 예외 사유를 근거와 함께 기록했고,
`tests/test_http.py:393` 이 인자 0개를 못박았으며, `session.py:251-268` 이 실패를 삼켜
로컬 세션을 항상 정리한다. 제목이 주장하는 "서버측 상태변경인데 읽기 allowlist 등재"는
의도된 안전설계에 대한 지적이므로 결함 아님 = REFUTED.

---

## P2CRO-04 — 미리보기에서 saleDd 만 마스킹 누락 → **CONFIRMED, medium → low**

라이브러리 (직접 확인):
- `mutation_payloads.py:1612-1630` — `extend_discount_card` 쿼리가
  `saleWctNo` / **`saleDd`** / `saleSqno` / `tkRetPwd` 4개를 싣는다.
- `redaction.py:12-14` `SENSITIVE_KEYS = frozenset(key.casefold() for key in {...})`,
  매칭은 `:280`, `:291`, `:340` 모두 `key.casefold() in SENSITIVE_KEYS` — **정확 일치**.
- `grep -n "saleDd\|saleDt" redaction.py` → `27: "saleDt"` **한 줄뿐. `saleDd` 없음.**
  형제 3개는 등재: `tkRetPwd`(:25), `saleWctNo`(:26), `saleSqno`(:28).
  같은 값의 다른 철자 `sale_date`(:71), `h_orgtk_sale_dt`(:126)는 등재돼 있어 구멍이 더 잘 숨는다.
- `tests/test_discount_card_mutations.py:267-271` 은 `SYNTHETIC_PWD` 부재만 확인 → 통과.

앱 근거 (직접 확인):
- `ui/ticket/confirm/TicketListActivity.java:1066-1073` `NCardExtension()` 이
  `setSaleWctNo(h_orgtk_wct_no)` / `setSaleDd(h_orgtk_ret_sale_dt)` /
  `setSaleSqno(h_orgtk_sale_sqno)` / `setTkRetPwd(h_orgtk_ret_pwd)` 로 4분할 조립.
- `ui/ticket/receipt/TicketReceiptActivity.java:431`
  `H4.a.getReturnNumberWithDash(getH_orgtk_wct_no(), getH_orgtk_ret_sale_dt(),
  getH_orgtk_sale_sqno(), getH_orgtk_ret_pwd())` — 네 값이 곧 인쇄되는 반환번호. 확인.

**심각도 하향 사유**: 나머지 3조각(창구번호·발매일련번호·반환비밀번호)은 전부 마스킹되므로
미리보기 로그만으로 반환번호를 복원할 수 없다. 새는 것은 4조각 중 엔트로피가 가장 낮은
발매일자 하나다. 카드정보 유출(critical)도 아니고 기능 실패(high/medium)도 아니다 → low.
단 마스킹 목록의 정확일치 특성 때문에 wire 철자 하나만 빠져도 구멍이 생긴다는 지적은
그대로 유효하고 수정 가치가 있다.

---

## P2CRO-15 — actualTrainSchedule 파서 wire key 16개 APK 0건 → **UNVERIFIABLE (low)**

기계 확인:
- `analysis/apktool/smali/com/korail/talk/network/dao/trainsInfo/
  TrainScheduleDao$TrainScheduleResponse.smali` 의 `.field` 는 실제로 7개
  (`dlayDtlRsnCont, dlayList, msgCont, runDt1, runSegOrdr, trnDptFlg, trnNo1`; `this$0` 제외).
  `TrainScheduleDao$TimeInfo.smali` 는 14개
  (`actArvDlayTnum, actArvDt, actArvTm, actDptDt, actDptTm, arvDt, arvTm, dptDt, dptTm,
  expnArvDlayTnum, expnDptDlayTnum, rgulFlg, saodFlg, stopStnNm`). **주장의 7/14 카운트 정확.**
- 인용된 키들을 `analysis/` 전체(jadx+smali+res+assets)에 대해 재검색한 결과
  `stopRsStnCd, stnConsOrdr, dlayFareRetDvCd, dlaySoloOprFlg, dturDrvDlayTnum,
  dlayStnConsOrdr, routNm, saleRgulFlg, tmnRsStnCd, trnAttCd, upDnDvCd, orgRsStnCd`
  **전부 0파일**. 파서 위치도 `parsers.py:591`(stopRsStnCd) 등으로 인용과 일치.

**그러나 결론을 낼 수 없다**: Gson 은 미선언 키를 무시하므로 APK 부재가 wire 부재를
증명하지 않는다(이 프로젝트가 반복해 밟은 "번들에 없다 ≠ 프로토콜에 없다" 함정).
또 문제의 키들은 전부 `optional(...)`/`_typed_optional_string` 으로 읽혀 없으면 None 이
될 뿐 파싱이 실패하지 않는다. 실측 응답 캡처가 없는 한 판정 불가.
심각도는 medium → low (기능 실패 경로가 없다). 1차 판정(unverifiable)에 동의.

---

## P2CRO-09 — EXCLUDED_API_DOMAINS 문서 드리프트 → **CONFIRMED (info)**

- `safety.py:41-51` — `EXCLUDED_API_DOMAINS` 에 `"reservation", "payment", "refund"` 포함 확인.
- `consent.py:33-40` `MUTATION_CATEGORIES = ("reserve","payment","cancel","refund",
  "discount_card","price_recalculation")` 확인.
- 정식 게이트 확인: `client.py:1565` `require_mutation_consent(consent, "reserve")`,
  `:1898` `require_mutation_consent(consent, "payment")`,
  `:2029` `require_mutation_consent(consent, "refund")`.
- 무해성도 확인: `safety.py:37-40` 주석이 "This set is documentary: nothing dispatches on it,
  and the actual boundary is KORAIL_READ_ONLY_ROUTES plus KORAIL_MUTATION_ROUTES."
- 나머지 5개(`check-in, member-drop, push-sms, points-mileage-write,
  dynapath-token-generation`)는 실제 배제 상태가 맞다(README:344-353, 각 경로 grep 0건).
기능 영향 0, 문서 오해 유발만 있음 → low → info. 1차 K1-03 이 1개만 지적했다는 지적도 맞다.
