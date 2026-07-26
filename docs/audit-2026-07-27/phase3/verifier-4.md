# 코레일톡 3차 검증 (반증 담당) — verifier-4

대상: `/Users/yakisoba/Documents/GitHub/korail-mobile-api`
방법: 인용된 file:line 을 전부 직접 열어 확인. 상수·분기·필드명은 apktool smali 로 재확인.
읽기 전용 준수: 저장소 파일 수정/생성 없음, git 상태 변경 없음.
(`python3 -c` 임포트로 `src/korail_mobile_api/__pycache__` 가 갱신될 수 있으나 소스는 미변경.)

**요약: CONFIRMED 14 / PARTIAL 4 / REFUTED 3 (총 21)**
심각도 하향 8건, 상향 0건.

---

## K1-03 — CONFIRMED (low)

`safety.py:17` 은 이 집합을 "the subject areas this package will **not build a send
path for**", `:38-40` 은 "records which areas were considered and **declined**" 라고
정의한다. 그런데 `:43,44,45` 의 `reservation`/`payment`/`refund` 셋 다 실제 전송 경로를
가진다 — `safety.py:208` TicketReservation, `:224` payment.ReservationPayment,
`:234` refunds.RefundsRequest, `:249` **reservation**.dcntCrdExtn.do(도메인 세그먼트가
문자 그대로 `reservation`). client.py:1570/1740/1812/2212(reserve 계열), :2016(refund) 확인.

집합이 inert 하다는 주석은 사실이다: `grep EXCLUDED_API_DOMAINS src/` → safety.py 와
`__init__.py:269,485` 재수출뿐, http.py 0건. `tests/test_http.py:321-348` 이 통과하는
이유는 이 집합이 아니라 해당 경로가 `KORAIL_READ_ONLY_ROUTES` 에 없기 때문이다.

`safety.py:19-24` 는 정확히 같은 이유로 `points-mileage` → `points-mileage-write` 로
라벨을 좁힌 전례를 남겨놨는데 세 도메인에는 같은 처리를 하지 않았다.
기능 결함 아님, 내부 문서 드리프트 → low 유지.

## K3-05 — CONFIRMED (medium → **low**)

앱 근거 정확. `ReservationResponse.java:11` 필드, `:428-430` `getH_cust_mg_no()`,
`ui/inquiry/rir/orr/a.java:172` `h.getInstance().setNonMemberNumber(...getH_cust_mg_no())`.
소비처도 확인: `a6/C1042B.java:290-293`
`if (hVar.isNonMember()) { setHiduserYn("N"); setHidCustNo(hVar.getNonMemberNumber()); }`.

라이브러리 근거도 정확. `mutation_models.py:229-262` 에 대응 필드 없음,
`mutation_parsers.py:135-273` 이 h_cust_mg_no 를 읽지 않음(`grep cust_mg_no src/` 0건),
`mutation_models.py:511-517` 의 `non_member_no` docstring 은 앱 근거만 적고 값의 출처를
안 적는다.

**하향 근거 둘:**
1. `mutation_parsers.py:125-132 _base_fields` 가 `raw` 를 그대로 보존하므로 값 자체는 남는다.
2. 이 라이브러리에 비회원 세션이 없다. `session.py:189-198` 로그인 폼은
   `txtMemberNo/txtPwd/txtInputFlg` 회원 하나뿐이고, `client.py:1554-1557` 이
   "every mutation here needs a logged-in member session and the non-member booking
   route is not reachable at all" 라고 명시한다. `recalculate_price` 도 세션 없으면
   `KorailAuthError`. 즉 `non_member_no` 는 "발견하기 어려운" 게 아니라 **현재 도달
   불가능한** 파라미터다. 어떤 도달 가능한 호출도 영향받지 않음 → low.

(참고, 범위 밖: `B6/AbstractC1269e.java:714` 가 같은 값을 결제폼 `setHidMbCrdNo` 에도
쓴다. 비회원 지원을 열 때 같은 근본원인이 결제까지 번진다.)

## K3-02 — CONFIRMED (low)

`network/dao/cart/CartService.java:19-21` `verifyMaasStatus`,
`@POST /classes/com.korail.mobile.maas.rsvStt.do`, 필드
`addSrvDvCd/addSrvReqNo/coptEntRsvNo/lumpStlTgtNo` — 인용과 정확히 일치.
`VerifyMaasStatusDao.java:11-60` 요청 DTO 확인.
라이브러리 `grep -i maas src/` → MaasMenu/MaasStation/MaasServiceDetail 만,
rsvStt/verifyMaasStatus 0건. `docs/api-status-by-service.md:182` 에 '미실행' 추적됨.
미구현 사실 확인, 구현 기능의 오작동은 아님 → low 유지.

## K4-02 — CONFIRMED (medium → **low**)

앱: `TicketPurchaseHistoryActivity.java:272-291` `N0()` 가 `:277 setTxtIndex("2")` 와
`:279-280 sethAbrdDtFrom(str)/sethAbrdDtTo(str2)` 를 **항상** 채운다.
`N0` 호출부는 `:319-321 Q0()` 하나뿐이고 그 진입점 `O0`(:295)/`P0`(:308)의 인자는
`:365`, `:372`, `:719` 세 곳 전부 `this.f30417r.format(this.f30401E/F.getTime())` —
날짜선택기 값이다. 빈 문자열 경로 없음. 주장 그대로.

**추가 확인(주장이 안 다룬 반대 사례):** mode="1" 쪽 `TicketListActivity.java:939-941` 은
`sethAbrdDtFrom("")`/`sethAbrdDtTo("")` 를 **명시적으로** 보낸다. 따라서 라이브러리의
기본값 `""`(payloads.py:388-389)은 기본 mode 에서는 앱과 바이트 단위로 일치한다.

라이브러리 `payloads.py:384-409` 는 mode 값만 검사하고 날짜를 강제하지 않으며
docstring `:395-397` 은 "history mode additionally carries ... bounds" 라고 쓴다.
`client.py:1487-1510 get_ticket_list` 도 그대로 통과시킨다.

**하향 근거:** 라이브러리가 스스로 잘못된 폼을 만들지 않는다. 호출자가 mode="2" 를
날짜 없이 넘길 때만 생기는 입력검증 공백이다 → "low: 견고성·일관성 문제, 동작에는
지장 없음" → low.

(범위 밖 관찰: 라이브러리는 `hiduserYn:"Y"` 고정이고 앱의 비회원 분기
`setHidName/setHidTeleNo/setHidPwd`(TicketPurchaseHistoryActivity.java:282-286)를 아예
모델링하지 않는다 — K4-08 계열.)

## K4-07 — CONFIRMED (low)

`TicketService.java:28` `deviceReset` 11개 `@Field`
(teln/custNm/nonMbPwd/stlbTrnClsfCd/dptDttm/latitude/longitude/trnNo),
smali `TicketService.smali:7` 로도 확인. `DeviceResetDao.java:9-93` 전체 확인.

jadx 호출부가 스텁이라는 지적도 사실이며 smali 로 실사용 확정:
`TicketListActivity.smali:5315 .method private g1(I)V` 안에서
`:5355 new-instance DeviceResetDao`, `:5368 DeviceResetRequest.<init>`,
setter 8개 — `:5401 setTeln`, `:5414 setCustNm`, `:5427 setNonMbPwd`,
`:5500 setStlbTrnClsfCd`, `:5669 setLatitude`, `:5674 setLongitude`,
`:5722 setDptDttm`, `:5735 setTrnNo`. jadx 의 "Method not decompiled" 스텁이 바로 그
`g1(int)` 이다 — 주장의 근거가 정확했다.
`res/values/strings.xml:1895 ticket_reset_confirm` 존재 확인. 라이브러리 grep 0건.
미구현 mutation 엔드포인트 → low 유지.

## K5-03 — CONFIRMED (low)

smali 로 상수 전수 확인 (`analysis/apktool/smali/K4/h.smali`, `<clinit>`):
`:44-52` INS_0 = `일시불`/**`"0"`**, `:72-80` `"2"`, `:100-108` `"3"`,
`:128-136` `"4"`, `:156-164` `"5"`, `:184-192` `"6"`, `:212-220` `"12"`,
`:240-248` `"24"`. jadx 가 `StbkAcntDao.ACCOUNT_REGISTER/CHANGE_PASSWORD` 심볼로
뭉갠 4·5 도 smali 에서 리터럴로 확인 — "나머지 코드는 자릿수 문제 없음"이 성립.

전송 경로: `AbstractC1269e.java:886 setInstallmentType(V4.a.getInstallmentType(...))`
→ `v4/a.java:238-263` 이 `h.INS_*.getCode()` 반환 → `v4/a.java:32
setHidIsmtMnthNum(1, creditCardData.getInstallmentType())` → 키는
`PaymentMethod.java:17,61` (`PaymentMethod.smali:157,561`) 이 `"hidIsmtMnthNum"+i` 로 조립.
가공 없음.

**반증 시도 결과(모두 기각):** `v4/a.smali:1176` 의 `"00"` 은 `setSpayDvCd` 용으로 무관.
`AbstractC1269e.java:259,289` 의 `"00"` 은 `bcUsrAthnR.do?insMmNum=` **WebView URL**
(payType "11"/"8", 간편결제 PG)에서만 나오며 `hidIsmtMnthNum1` 이 아니다.
따라서 이 필드에 한해 앱의 일시불 값은 `"0"` 이 맞다.

라이브러리 `mutation_models.py:311 installment: str = "00"` →
`mutation_payloads.py:1407 "hidIsmtMnthNum1": card.installment`. 상수 드리프트 확정.
서버 정수 파싱이면 무해하고 실패 증거는 없음 → low 유지.

## K6-04 — PARTIAL (info)

엔드포인트 목록 자체는 정확하다: `CompensateService.java:12-22` 3개,
`DelayService.java:18-52` **9개**.

**그러나 "라이브러리근거: 없음 — grep 0건" 은 사실과 다르다.** `dlay.dptnBank.do` 는
**이미 구현되어 있다**: `safety.py:91` 라우트 등록, `safety.py:700` 필드 계약,
`client.py:476` 호출, `read_parsers.py:709-716` 입금은행 파서.
따라서 미구현은 9개가 아니라 8개, 합계 12가 아니라 **11** 이고,
그 11이 정확히 `docs/RELEASE_GAP_PLAN.md:440-444`
"Out of core v1 (documented, deferred) ... delay/compensate refunds (**11 endpoints**,
analysis §3.10)" 의 수다. 주장이 dptnBank 를 미구현 쪽에 넣어 이연 문서와 어긋나는
수치를 만들었다.

"결함 아님, 문서화된 이연" 이라는 결론 자체는 유효 → PARTIAL/info.

## K8-01 — CONFIRMED (medium → **low**)

`AddService.java:16-34` 5개 `@POST` 전부 확인:
`addService.reserve.do`(additionalService), `addService.buyConfirm.do`(dealCarBuy),
`addService.reserveList.do`(getExtraProductList), `addSrv.helpSrvCust.do`(helpSrvCust),
`addSrv.helpSrvTk.do`(helpSrvTk). 라이브러리 grep 0건.
`docs/api-status-by-service.md:131-139` 에 카탈로그만 있고 5개 모두 '미실행'.
`RELEASE_GAP_PLAN.md:442` 의 이연 목록은 `addService.cancelPay.do`/`coptCnc.do`/
`maas.cncFee.do` 만 이름을 대므로 이 5개가 명시적 이연 대상이 아니라는 지적도 맞다.

**하향 근거:** 5개 중 3개는 쓰기(예약/신청/구매확정)로 v1 쓰기 범위 밖임이 분명하고,
나머지 2개(`reserveList.do`, `addSrv.helpSrvTk.do`)는 순수 읽기 갭이다.
어느 쪽도 **구현된** 기능을 실패시키지 않으므로 rubric 의 medium(조건부 실패/필드 누락)에
해당하지 않는다 → low.

## K8-02 — CONFIRMED (info)

`CommonService.java:33-35 getDecrypt`, `:37-39 getEncrypt`, `:41-43 getKBPayEncrypt`,
`:60-62 seedEncrypt` 확인. 호출부도 확인:
`B6/AbstractC1269e.java:656-661 e1()` = KBPayEncrypt(payType `"11"`),
`:766-770 m1()` = seedEncrypt(payType `"2"`) — **둘 다 간편결제/웹뷰 PG 분기**이지
표준 카드결제 경로가 아니다.

표준 카드결제는 `v4/a.java:29 setHidStlCrCrdNo(1, creditCardData.getCardNumber())` 평문이고
라이브러리 `mutation_payloads.py:1404 "hidStlCrCrdNo1": card.card_number` 도 평문 —
동일하다. `RELEASE_GAP_PLAN.md:378-387` 의 "CORRECTION ... the working client sends the
**raw PAN** directly in `hidStlCrCrdNo1` with **no encrypt step**" 확인.
결제 정확성 무영향, 참고 기록 → info 유지.

## P2MIS-02 — PARTIAL (medium → **low**)

코드표는 정확하다: `K4/p.java:5-17`(13종, DEFAULT="015", 003 자유석 / 033 입석 /
021·028 휠체어 / 018 2층석 / 032 자전거), `K4/l.java:5-7`(000/009/010),
`K4/n.java:5-8`(000/011/012/013).

**`_2`/`_3` 주장은 반증된다.** 주장이 인용한 그 빌더가 앱에서도 두 값을 하드코딩한다.
smali 확정 — `analysis/apktool/smali/U4/b.smali:711-731`:
`sget-object LK4/l;->DEFAULT` → `getCode()` → `setTxtSeatAttCd_2`,
`sget-object LK4/n;->DEFAULT` → `getCode()` → `setTxtSeatAttCd_3`.
`setTxtSeatAttCd_2/_3` 의 앱 전체 호출부는 이 두 줄과 SRT 연동 WebView
(`ui/web/IntegrationWebViewActivity.java:83-84`, 별개 클래스 `ReceiveSRTData` 의 동명
setter)뿐이다. 즉 `payloads.py:303-304` 의 `"000"` 은 조회 폼에서 앱과 바이트 단위로
일치한다 — 결함 아님.

**`_4` 부분만 성립한다.** `U4/b.smali:735 setTxtSeatAttCd_4(v3)` — v3 은 호출자 인자다.
짧은 오버로드(`u4/b.java:83-84`)만 `p.DEFAULT`("015")를 넘기고,
`MainBookingActivity.java:768` 은 사용자가 고른 `str2` 를,
`b5/c.java:170,235` 는 `p.EVACUATION_HELPER.getCode()` / `pVar.getCode()` 를 넘긴다.
라이브러리는 `payloads.py:305 "015"` 리터럴이고 `TrainSearchQuery`(models.py:269-277)에
대응 필드가 없다. 대조군도 사실: `limousine_payloads.py:149-151` 셋 다 파라미터화,
`safety.py:931-933` LimousineScheduleView 핀에 세 필드 포함.

**하향 근거:** 라이브러리가 보내는 값은 앱의 기본값과 동일하므로 "잘못된 값을 보낸다"가
아니라 "선택지 하나가 미노출"이다. 주장의 "여기서 걸러진 열차는 하위에서 복구 불가"는
근거 제시가 없는 추정이다 → low.

## P2INC-08 — CONFIRMED (high 유지)

앱 근거 smali 로 확정 —
`analysis/apktool/smali/com/korail/talk/ui/ticket/ticketReturn/a.smali:3141-3155`:
`RefundCommissionDao$RefundCommissionResponse;->getTk_ret_tms_dv_cd()` →
`RefundDao$RefundRequest;->setTk_ret_tms_dv_cd()`; `:3161-3165`
`TicketDetailDao$TicketDetailResponse;->getH_pbp_acep_tgt_flg()` → `setPbpAcepTgtFlg()`.
둘 다 서버 응답 에코가 맞다. Retrofit 선언 `RefundService.java:29` 14개 `@Field` 확인.

라이브러리 `mutation_payloads.py:1455 "tk_ret_tms_dv_cd": "21"`, `:1457
"pbpAcepTgtFlg": "N"` 고정. `PaidTicket` 에 두 값을 주입할 필드도 없다 — 핵심 주장 성립.

**저장소 자체 문서가 이미 이 결함을 적어놨다:**
`docs/deep-dive/cross-validation-2026-07-21.md:238` — "srtgo HARDCODES '21' …
우리 앱은 CommissionView 응답에서 동적으로 가져온다. `BEFORE_DEPARTURE='21'`,
`AFTER_DEPARTURE='15'`(`I4/a.java:5-6`). srtgo 의 '21' 은 출발 전 환불에만 맞다."
`:239` — "pbpAcepTgtFlg … 티켓마다 Y/N 일 수 있다."

**하향을 검토했다가 기각했다 (high 유지).** srtgo 가 `"21"` 을 상수로 쓰며 동작한다는
사실은 **출발 전 환불에 대해서만** 유효하다 — 같은 문서 `:238` 이 명시적으로
"srtgo 의 '21' 은 출발 전 환불에만 맞다"고 적는다. 그리고 라이브러리 어디에도 출발
상태를 가리는 장치가 없다: `client.py:2011-2049 refund()` 는 consent·세션만 확인하고
`build_refund_form`(`mutation_payloads.py:1416-1462`)의 검증은 5개 문자열 비어있음
검사뿐이다. 출발 후 환불은 예외적 조건이 아니라 정상 사용자 시나리오이므로,
`dry_run=False` 인 돈 경로가 알려진 오답 상수를 무경고로 전송한다 →
rubric 의 "잘못된 결과를 낸다"(high)에 해당. 유지.

주장의 부분 오류 하나: "호출자가 올바른 값을 구할 방법 자체가 없음"은 절반만 맞다.
   `tk_ret_tms_dv_cd` 는 `read_parsers.py:2627-2631 _REFUND_COMMISSION_FIELDS` 가
   `ticket_return_times_division_code` 로 **파싱한다**
   (`tests/test_reference_derived_reads.py:158` 픽스처는 그 값이 `"1"` 이다 — "21"이
   아닌 값이 실재함을 라이브러리 자신의 테스트가 보여준다).
   미노출은 `h_pbp_acep_tgt_flg` 하나뿐(src grep 0건).

## P2INC-10 — CONFIRMED (medium → **low**)

실측:
```
redact_payload({'hidRsvChgNo':'007','hidPnrNo':'PNR1','hidStlCrCrdNo1':'4111111111111111'})
 -> {'hidRsvChgNo': '007', 'hidPnrNo': '[REDACTED]', 'hidStlCrCrdNo1': '[REDACTED]'}
```
`redaction.py:12-14` 가 `SENSITIVE_KEYS` 를 casefold 로 정규화하고 `:332,343` 이
**정확 일치** 매칭을 한다. 집합에 `hidPnrNo`(:24), `hidWctNo`/`hidTmpJobSqno1`/
`hidTmpJobSqno2`(:141-143), `h_rsv_chg_no`(:111), `reservation_change_no`(:65) 는
있으나 `hidRsvChgNo` 는 파일 전체 0건. 삽입 지점 `mutation_payloads.py:1398`,
게이트 `consent.py:131 object.__setattr__(self,"payload",redact_payload(...))`,
`client.py:1890-1891, 1956-1957` docstring 확인. `redact_text` 의 CARD_RE 는 13–19자리만
잡으므로 짧은 시퀀스는 통과한다.

**하향 근거:** 값의 정체는 예약 변경 회차 시퀀스이고
`mutation_payloads.py:1306-1314 _echoed_reservation_change_no` 가 값이 없으면 `"000"` 로
떨어지는 준상수다. 같은 폼의 PNR·창구번호·작업시퀀스는 모두 마스킹되므로 이 값 단독의
신원 식별력은 사실상 없다. P2SAF-08 의 실명·휴대폰과 같은 medium 에 두는 것은 과대평가
→ low.

## P2INC-06 — REFUTED (info)

사실관계는 전부 맞다. `grep -rIl "P100" analysis/` = **0 파일**(jadx+smali+res+assets).
대조군 확인: `WRG000000` 은 `smali/g6.1/c.smali`·`g6.1/a.smali` 등 4파일,
`P114` 는 `TicketPurchaseHistoryActivity.smali`·`TicketListActivity.smali` 에 존재.
공통 디스패처 `L4/h.smali:855` 의 `"FAIL"` 분기도 존재.
라이브러리 `read_parsers.py:1143-1149 accepted_empty_codes=frozenset({"P100"})`,
`errors.py:478-480 NO_RESULT_CODES` 확인.

**그러나 결함이 아니다.**
1. 이 프로젝트 자신의 규칙("번들에 없다 ≠ 프로토콜에 없다")에 정면으로 걸린다.
   Gson 은 미선언 코드/필드를 무시하므로 APK 0건은 서버가 P100 을 보내지 않는다는
   증거가 아니다.
2. 주장의 권고(문서화)는 **이미 충족되어 있다**: `errors.py:478-480` 이
   "`WRG000000`/`P114` are APK-attested as empty-view states; `P100`/`WRT300005` are
   **live-observed only**" 라고 명시한다. 근거 등급이 코드 주석에 이미 구분돼 있다.
3. `accepted_empty_codes` 는 오류를 삼키는 장치가 아니라 예약이력 응답을 "빈 결과"로
   해석하는 좁은 스위치다.

주장 스스로도 결함 단정을 피했다. 결함 아님 → REFUTED/info.

## P2SAF-03 — CONFIRMED (medium → **low**)

실측 재계산이 주장의 13개 목록과 **완전히 일치**한다:
```
58 routes; 45 with contract; 13 without —
  login.Login, myTicket.MyTicketList, common.code.do, common.stationdata,
  common.stationinfo, qry.chtnStn.do, research.actualTrainSchedule.do,
  schedule.runDt, seatMovie.ScheduleView, /ebizcross/getUUID.do,
  /ebizmaas/EbizMaasStationList.do, /file/CACHE/prdMobilePlusMain.cache,
  /file/CACHE/prdMobilePlusNotice.cache
assert_read_only_request_fields("/classes/com.korail.mobile.login.Login",
  {"Device":"AD","evil_field":{"nested":"dict"},"txtPwd":object()}) -> 예외 없음
assert_read_only_request_fields(".../dlay.dptnBank.do", {...evil...}) -> KorailProtocolError
```
`safety.py:1384-1386` 의 `allowed = ...get(route_path); if allowed is None: return` 이
`:1427-1430` 값타입 검사(`type(value) not in {str,int}`)보다 앞서므로 둘 다 스킵되는 것도
확인. 앱 근거 `CertificationService.java:22-23`(쓰기) vs `:45-46`(읽기) 두 오버로드 확인.

**하향 근거 — 게이트 우회가 아니다.**
라우트 allowlist 자체는 58개로 여전히 강제된다(`http.py:173,184,407`).
`safety.py:62-68` 의 방어 서술은 `certification.ReservationList` **한 라우트**에 한정된
문장이고 그 라우트는 계약이 있는 45개 쪽이며 `safety.py:1028-1030` 4필드 핀으로 정확히
참이다 — 주장이 이 주석을 전체 보증으로 일반화한 부분은 과장이다. 계약이 없는 13개
경로에 쓰기 오버로드가 공유되는 사례도 없다. 74개 공개 메서드는 전부 내부 빌더로 폼을
만들므로 임의 필드 유입 경로는 사용자가 `http.post_form` 을 직접 부르는 경우뿐이다.
심층방어의 비균질성 → low.

## P2SAF-08 — CONFIRMED (medium)

실측:
```
custMgNo_1    C123          <- 그대로 노출
apdCustName_1 홍길동         <- 그대로 노출 (실명)
apdCustTeln_1 01011112222   <- 그대로 노출 (휴대폰)
saleDd        20260101      <- 그대로 노출
hidRsvChgNo   007           <- 그대로 노출
hidPnrNo      [REDACTED]
custMgNo      [REDACTED]
saleDt        [REDACTED]
hidStlCrCrdNo1 [REDACTED]
```
삽입 지점 확인: `mutation_payloads.py:1568 custMgNo_{index}`, `:1572 apdCustName_{index}`,
`:1576 apdCustTeln_{index}` (`build_discount_card_purchase_form` →
`client.register_discount_card` 로 **도달 가능**), `:1618 saleDd`, `:1398 hidRsvChgNo`.
원인은 정확일치 매칭 + 철자 누락: 집합에 `custMgNo`·`saleDt` 는 있으나 `custMgNo_1`·
`saleDd` 는 없다(`grep "custMgNo_\|apdCustName\|apdCustTeln\|saleDd" redaction.py` 0건).
한글 이름·11자리 번호는 `CARD_RE`(13–19자리)도 못 잡는다.

`README.md:209-211` "forced through `redact_payload` on construction, so it **can never**
hold a raw card number, PNR or other identity" — 카드번호와 PNR 은 실제로 마스킹되지만
**실명·휴대폰번호·고객관리번호가 평문으로 남으므로 "other identity" 부분이 반증된다.**

**단, SECURITY.md 는 반증되지 않는다.** `SECURITY.md:20` 은 "each returns a redacted
preview" 라고만 하고 `consent.py:131` 이 실제로 `redact_payload` 를 태우므로 문장은
문자 그대로 참이다. 주장의 SECURITY.md 다리는 성립하지 않는다.
README 한 문장의 과잉 보증 + 실 PII 노출 → medium 유지.

## P2SAF-10 — PARTIAL (low)

반환형 분포는 정확하다. inspect 실측 결과 consent 파라미터를 가진 public 메서드 12개 중
bare 4개: `client.py:1603 confirm_standby_hold`, `:1841 cancel_unpaid_hold`,
`:2016 refund`, `:2118 extend_discount_card` → `MutationPreview | BaseKorailResponse`.
나머지 8개는 타입 모델(Hold 5, Payment 2, DiscountCardPurchase 1).

**그러나 "4개가 하나의 구조적 결함"이라는 프레이밍은 반증된다.** 앱 DAO 반환형을 넷 다
확인한 결과 **3개는 앱과 정확히 일치**한다:
- `ReservationCancelService.java:21` `BaseResponse reservationCancelCheck(...)` — bare
- `ReservationWaitService.java:12` `BaseResponse rsvWait(...)` — bare
- `ResearchService.java:66` `BaseResponse setNCardExtension(...)` — bare
  (주장은 `:65` 라 했으나 실제 `:66`)
앱 DAO 에 파싱할 필드 자체가 없으므로 모델이 없는 것이 정상이고, 따라서
"cancel_unpaid_hold / extend_discount_card 호출자가 raw dict 를 직접 파야 한다"는 서술은
파낼 것이 없으므로 성립하지 않는다.

**유일한 실제 갭은 refund 다.** `RefundService.java:29` 는
`RefundDao.RefundResponse returnTicket(...)` 타입 응답이고
`RefundDao.java:118-127 RefundResponse{List<StlList> stlList}`, `:129-138
StlList{stl_mns_cd}` 로 구조가 선언되어 있는데 라이브러리는 `stlList`/`stl_mns_cd` 를
grep 0건으로 전혀 파싱하지 않는다. 즉 1차 K6-06 은 유효하고, 이 주장은 새 결함이 아니라
K6-06 의 재서술에 오탐 3건을 얹은 것이다 → PARTIAL/low.

## P2SAF-14 — REFUTED (info)

표면 사실은 맞다: `__init__.py:156` 은 `redact_mapping, redact_payload` 만 임포트하고
`:495-496` 만 `__all__` 에 있다. `redact_value` 는 `redaction.py:290-309`.

**그러나 "응답 dataclass 를 마스킹할 공개 수단이 사실상 없다"는 결론은 반증된다.**
1. `redaction.py` 는 언더스코어 없는 **공개 모듈**이고 `redact_value` 도 언더스코어 없는
   공개 함수다. `from korail_mobile_api.redaction import redact_value` 가 그대로 동작한다
   (실행 확인). `__all__` 은 `import *` 에만 영향을 준다.
2. 주장의 "공개된 redact_mapping 은 dict 에만 동작한다"는 **틀렸다**.
   `redaction.py:341-345` 가 각 값을 `redact_value` 에 위임하고 `redact_value` 는
   `:302-306` 에서 dataclass 를 재귀 처리한다. 실측:
   `redact_mapping({'r': dc})` → `{'r': {'hidPnrNo':'[REDACTED]','txtPwd':'[REDACTED]',
   'ok':'fine'}}` — `redact_value(dc)` 와 **동일 결과**.
3. 두 함수는 같은 `SENSITIVE_KEYS` 를 쓰므로 `redact_value` 를 `__all__` 에 넣어도
   P2SAF-05 류의 철자 누락은 하나도 해결되지 않는다 — 인과 논리 자체가 성립하지 않는다.
4. `SECURITY.md:7-9` 는 "Remove or replace those values before sharing" 이라는 **보고자
   대상 지침**일 뿐 라이브러리에 특정 API 를 요구하지 않는다.
→ REFUTED/info.

## P2CRO-02 — CONFIRMED (medium → **low**)

앱 근거 확인: `RsvInquiryResponse.java:9-17` 최상위 필드는 정확히 9개
(h_ectb_trn_no_next, h_gd_no, h_next_pg_flg, h_notice_msg, h_prcd_trn_no_next,
h_qry_st_no_next, h_rslt_cnt, h_trn_no_next, trn_infos).
`grep -rIl` 실측 (analysis/ 전체 = jadx+smali+res+assets):
```
strJobId          0 files      h_notice_msg   3 files
h_seat_cnt_first  0 files      h_menu_id      0 files
h_seat_cnt_second 0 files
txtGoHour_first   0 files
```
라이브러리 `parsers.py:259,271,272,273` 이 그 네 키를 읽고 `models.py:584,600-602` 에
필드로 둔다. 바로 옆 `models.py:580-583` 은 `h_menu_id` 를 "zero hits across the whole
decompiled app" 를 이유로 **제외**했다 — 동일 기준의 비일관 적용 확인.
반대로 실재하는 `h_notice_msg` 는 `TrainSearchMetadata` 에 없다(라이브러리는 다른
라우트에서만 읽는다: `read_parsers.py:2505`, `limousine_parsers.py:390`).
픽스처 `tests/fixtures/raw_typed_train_search.json:5,11,13`(+h_seat_cnt_second)이 네 키를
`"SYNTHETIC-…"` 로 채우고 `tests/test_raw_typed_core.py:650,658-662` 가 그 값을 단언하므로
"테스트 통과 = 파서가 자기가 읽도록 쓰인 키를 읽는다"만 증명한다는 지적도 성립.
provenance 도 확인: `grep -rn strJobId docs/` 0건 — P100 처럼 "live-observed only"
라는 실측 기록조차 없다.

**하향 근거:** 파싱이 전부 optional 이라 실서버에 없으면 조용히 `None` 이고 크래시가
없다. Gson 규칙상 "앱에 0건"이 "서버가 안 보낸다"의 증명도 아니다. 실질 피해는 다음
감사자 오독 위험(테스트 신호 오염) → low.

## P2CRO-06 — PARTIAL (medium → **low**)

실측 `inspect` 로 `KorailClient` 공개 메서드 = **74**.
74 로 적은 문서: `README.md:79`, `docs/api-status-by-service.md:18`,
`docs/verification-record.md:21`, `docs/IMPLEMENTATION_PROGRESS.md:148`.
stale 문장 확인: `IMPLEMENTATION_PROGRESS.md:312` "The **current** package boundary is
58 exact routes and 72 public methods", `:758` "The **current** implementation evidence
establishes 58 routes … and 72 public methods on `KorailClient`" — 같은 파일 내 자기모순.
`tests/test_readme.py:219 assert "72 public methods" in progress` 도 인용대로.
무의미 단언도 확인: `"75"` 는 `IMPLEMENTATION_PROGRESS.md` 에 5회(대부분 "75 seat rows"),
`"two"` 는 `verification-record.md` 에 다수 등장 → `:221`, `:78` 은 사실상 무검사.

**그러나 한 귀결이 과장이다.** `"72 public methods"` 는 같은 파일에 **3회** 나오고
`:234` 는 과거 구현 단계를 나열한 불릿("The transport now allows 58 exact login/read
routes and the client exposes 72 public methods. No new route was added…")이다.
따라서 `:312`/`:758` 만 74 로 고쳐도 `test_readme.py:219` 는 **여전히 통과한다** —
"누가 문서를 74로 고치면 테스트가 깨진다"는 부분 수정에는 성립하지 않는다.
실제 상태는 주장이 스스로 인용한 그 전력 그대로다: 핀이 과거 수치 문장에 걸려 무력화된
상태(= 현재 수치를 74로 고쳐도 아무것도 잡지 못하고, 완전 정리는 막는다).
헤드라인은 성립, 인과 귀결 하나가 과장 → PARTIAL/low.

## P2CRO-08 — CONFIRMED (low)

`safety.py` 라우트 집합과 `docs/RELEASE_GAP_PLAN.md:126-148` 을 스크립트로 전항목 대조:

닫힌 것 (문서는 미구현이라 적음):
- G2 `research.dcntCrdScheduleView.do` → `safety.py:177-180`
- G3 `ticket.dcntCrdUseQry.do` → `safety.py:176`
- G11 `login.Logout` → `safety.py:76`. 문서(`:137`)는 "client.logout() only clears the
  local cookie jar … server session never invalidated" 라 적지만
  `session.py:252-268` 이 실제로 `get_json("/classes/com.korail.mobile.login.Logout",
  include_common=False, raise_on_fail=False)` 를 발행한다.
- G12 `certification.ReservationList` → 라우트 등록 + `safety.py:1028-1030` 읽기 오버로드
  4필드 핀(`safety.py:62-68` 주석이 이를 설명)
- 부가: `xPoint.MyXPointView`(`safety.py:168`), `mlg.amtSpec.do`(`:169`)

여전히 미구현 (문서대로, 각 0건): G1 ScheduleViewSpecial, G4 tripChgOgtk,
G5 TourTrainSpecialRoom, G6 self.seatChgInfo.do, G7 myTicket.reqUpgradeSeat,
G8 maas.cncFee.do, G9 product.payInfo, G10 gift.gdUseSpec.do, `xPoint.XPointView`,
`railplus.autoCharge.do`, `checkin.info.do`.

주장 그대로. 1차가 자기 슬라이스 밖(G11/G12)을 확인하지 않고 "G2/G3 두 항목에
국한된다"고 단정한 것도 사실 → CONFIRMED/low(순수 문서 대 구현 드리프트).

## P2CRO-10 — REFUTED (info) — *"결함 없음"이라는 주장이 맞다*

이 항목은 스스로 "[결함아님·긍정결과]" 라고 밝혔고, 독립 재확인 결과 **결함이 없다**.
REFUTED 는 "주장의 검증이 틀렸다"가 아니라 "여기에 고칠 결함이 없다"는 뜻이다.

- opcode 6종: `T6/c.java:5-11`(None 0, CHK_ENTER 5002, ALIVE_NOTICE 5003,
  SET_COMPLETE 5004, GET_TID_CHK_ENTER 5101, INIT 5105, STOP 5106) ==
  `constants.py:412-417 KorailNetFunnelOpcode`.
- 액션 8종 **smali 재확인** `analysis/apktool/smali/K4/g.smali:76-94`:
  `act_8 / act_8_2 / act_18 / act_6 / act_22 / act_21 / act_14 / act_4`,
  `NETFUNNEL_SERVER_ID = "service_1"` — `constants.py:356-393` 과 값·주석 전부 일치.
- 성수기 분기: `MainBookingActivity.java:749`
  `C0805e.isPeakSeason(calendar) ? NETFUNNEL_ACTION_ID_PEAKSEASON : NETFUNNEL_ACTION_ID`
  == `netfunnel.py:899-920 inquiry_action`.
- `T6/g.java:179 ALIVE()` 정적 진입점은 `com/korail/**` 전체에서 호출 0건 확인
  (`grep -rn "ALIVE(" analysis/jadx/sources/com/korail/` 무결과). 5003 미구현은 정당.
- `act_22`(환불)는 어디서도 쓰이지 않으며 `netfunnel.py:888-896`
  `KORAIL_NETFUNNEL_GATED_OPERATIONS` 에도 없다 — 앱과 동일하게 환불에 큐 게이트가 없다.

→ 고칠 것 없음. REFUTED/info.
