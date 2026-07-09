# 07. 결제 코어 및 영수증 정적 분석

분석 기준: `korail.apk`를 로컬에서 JADX로 디컴파일한 정적 소스. 운영 호출/동적 트래픽 캡처는 수행하지 않았다. 아래 `sources/...` 경로는 `/tmp/korail-mobile-api-jadx/sources` 기준이다. 런타임 서버 응답값, 외부 결제 앱/웹 콜백값, 세션 쿠키 값은 정적 분석만으로 확정하지 않고 `unknown`으로 둔다.

## 1. 코어 결제 엔드포인트

예약 결제의 코어 API는 `PaymentService.payment()` 하나다. Retrofit `POST`, `@FormUrlEncoded`이며 경로는 `/classes/com.korail.mobile.payment.ReservationPayment`이다. 고정 필드 `Device`, `Version`, `Key`, `hidPnrNo`, `hidWctNo`, `hidTmpJobSqno1`, `hidTmpJobSqno2`, `hidRsvChgNo` 뒤에 `PaymentMethod`가 `@FieldMap`으로 붙는다. [source: `sources/com/korail/talk/network/dao/payment/PaymentService.java:11-14`]

`Device=AD`, `Version=250601003`, `Key=korail1234567890` 기본값은 모든 `BaseRequest` 생성자에서 세팅된다. [source: `sources/com/korail/talk/network/BaseRequest.java:6-18`]

`RsvPaymentDao.executeDao()`는 `RsvPaymentRequest`에서 위 필드들을 꺼내 `PaymentService.payment()`에 그대로 전달한다. [source: `sources/com/korail/talk/network/dao/payment/RsvPaymentDao.java:127-131`]

| API | HTTP | 필드 |
|---|---|---|
| `/classes/com.korail.mobile.payment.ReservationPayment` | `POST form` | `Device`, `Version`, `Key`, `hidPnrNo`, `hidWctNo`, `hidTmpJobSqno1`, `hidTmpJobSqno2`, `hidRsvChgNo`, `PaymentMethod` FieldMap |

결제 화면 전에 호출되는 일부 `PayService` API는 외부/간편결제 준비값을 받아 최종 `PaymentMethod` FieldMap을 만들기 위한 보조 흐름이다. 코어 결제 완료는 여전히 위 `ReservationPayment` 호출로 수렴한다. 예: Payco order sheet URL, `spayCphdDatVal`, `spayOrdNo`, NaverPay URL, Monimo decrypt는 `PayService`에 정의된다. [source: `sources/com/korail/talk/network/dao/pay/PayService.java:21-68`]

## 2. RsvPaymentRequest 구성 흐름

예약 응답에서 `RsvPaymentRequest`를 만들 때 앱은 `ReservationResponse`의 `h_pnr_no`, `h_wct_no`, `h_tmp_job_sqno1`, `h_tmp_job_sqno2`, 첫 번째 여정의 `h_rsv_chg_no`를 각각 `hidPnrNo`, `wctNo`, `jobSqNo1`, `jobSqNo2`, `hidRsvChgNo`로 옮긴다. 공통 helper `V4.b.getRsvPaymentRequest()`도 같은 매핑을 한다. [source: `sources/V4/b.java:35-42`]

주요 caller:

| Caller | 동작 |
|---|---|
| `MainBookingActivity` | 예약 성공 후 `RsvPaymentRequest` 생성, `PNR_NO_LIST`, `PAYMENT_TYPE=PAYMENT_DEFAULT`, `PAYMENT_REQUEST`, `COMMON_RESERVATION_RESPONSE`, `IS_POINT_STEP`를 `PaymentActivity`에 전달한다. [source: `sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:992-1008`] |
| `OldMainBookingActivity` | 동일한 예약 결제 화면 진입 패턴을 사용한다. [source: `sources/com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java:499-515`] |
| `ReservedTicketActivity` | 예약 내역의 구매 가능 항목에서 `PaymentActivity`를 띄우며, 다자녀 플래그에 따라 `PAYMENT_MULTI_CHILD` 또는 `PAYMENT_DEFAULT`를 넣는다. [source: `sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:407-429`] |
| `TicketListActivity` | 일부 예약 응답(`dao_l_reservation`) 수신 후 결제 화면으로 이동한다. [source: `sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1511-1524`] |
| `LimousineActivity`, `LimousineSelectSeatActivity` | 리무진 예약 응답에서 동일 필드로 `RsvPaymentRequest`를 구성해 결제 화면으로 이동한다. [source: `sources/com/korail/talk/ui/limousine/LimousineActivity.java:184-195`, `sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java:175-186`] |

`PaymentActivity`는 intent extra에서 `PNR_NO_LIST`, `WCT_NO_LIST`, `PAYMENT_TYPE`, 금액 문자열, `PAYMENT_REQUEST`, `COMMON_RESERVATION_RESPONSE`, 포인트 단계 여부 등을 읽고 수령액/할인액을 계산한다. [source: `sources/com/korail/talk/ui/payment/PaymentActivity.java:206-243`]

결제 버튼 처리에서는 NetFunnel 결제 action id로 `T6.g.BEGIN(... NETFUNNEL_ACTION_PAY_ID ...)`를 실행한 뒤 실제 결제 Runnable을 진행한다. [source: `sources/b6/AbstractC1269e.java:1023-1047`]

## 3. PaymentMethod FieldMap 키

`PaymentMethod`는 `LinkedHashMap<String,String>`이며 setter가 실제 FieldMap key를 만든다. 숫자 인덱스가 붙는 키는 `hidStlMnsSqno1`, `hidStlMnsSqno2`처럼 접미사 숫자를 붙인다. [source: `sources/com/korail/talk/network/request/payment/PaymentMethod.java:6-139`]

공통 사용자 필드는 `k1()`에서 최종 결제 직전에 추가된다. 비회원이면 `hiduserYn=N`, `hidMbCrdNo=<비회원번호>`를 넣고, 회원이면 `hiduserYn=Y`를 넣는다. 비회원번호 값 자체는 런타임 세션값이므로 `unknown`이다. [source: `sources/b6/AbstractC1269e.java:710-717`]

### 3.1 일반 카드

`V4.a.getCardRequest()`는 카드 결제 row 1을 만든다. [source: `sources/V4/a.java:21-54`]

| 키 | 값 출처 |
|---|---|
| `hidInrecmnsGridcnt` | `"1"` |
| `hidStlMnsSqno1` | `"1"` |
| `hidStlMnsCd1` | `"02"` |
| `hidMnsStlAmt1` | `PAYMENT_AMOUNT` |
| `hidCrdInpWayCd1` | `"@"` |
| `hidStlCrCrdNo1` | 입력/저장 카드번호 |
| `hidVanPwd1` | 카드 비밀번호 |
| `hidCrdVlidTrm1` | `YYMM`; `CreditCardData.getCrdVlidTrm()`은 `year.substring(2)+month`를 반환한다. [source: `sources/com/korail/talk/data/CreditCardData.java:21-23`] |
| `hidIsmtMnthNum1` | 할부 코드 |
| `hidAthnDvCd1` | 개인/법인 구분: UI에서 일반카드면 `J`, 아니면 `S`. [source: `sources/b6/AbstractC1269e.java:874-887`] |
| `hidAthnVal1` | 인증번호/사업자번호 등 UI 입력값 |

카드 입력 검증은 번호, 유효기간, 비밀번호 등 `CreditCardView.validate()` 결과가 있으면 dialog를 띄우고 결제를 중단한다. [source: `sources/b6/AbstractC1269e.java:859-888`]

### 3.2 후불/할인 정산

승차권 변경 결제에서 `dfpyList`가 있으면 `getCongressRequest()`가 row 1을 만든다. [source: `sources/b6/AbstractC1269e.java:402-415`, `sources/V4/a.java:57-67`]

| 키 | 값 |
|---|---|
| `hidInrecmnsGridcnt` | `"1"` |
| `hidStlMnsSqno1` | `"1"` |
| `hidStlMnsCd1` | `"03"` |
| `hidMnsStlAmt1` | `dfpy.getStlAmt()` |
| `hidDscpMgNo1` | `dfpy.getDfpyNo()` |
| `hidDfpyDscpNo1` | `dfpy.getDscpMgNo()` |
| `hidDfpySrtCd1` | `dfpy.getDfpySrtCd()` |

### 3.3 포인트 단독/복합

포인트 단독 결제는 수령액이 0이고 포인트 타입이 선택된 경우 `N1()`에서 `getPointRequest()`를 호출한다. KTX 마일리지와 삼성 마일리지가 모두 있으면 row 1/2로 나누어 만든다. [source: `sources/b6/AbstractC1269e.java:462-476`]

`getPointRequest(index, pointData, fVar, splitType)`의 공통 키는 `hidInrecmnsGridcnt`, `hidStlMnsSqno{index}`, `hidMnsStlAmt{index}`다. 세부 타입별 키는 다음과 같다. [source: `sources/V4/a.java:266-345`]

| 포인트 타입 | 주요 키 |
|---|---|
| KTX 마일리지 `pointType=0` | `hidStlMnsCd{i}=12`, `hidCrdInpWayCd{i}=P`, `hidIsmtMnthNum{i}=0`, `hidPontDvCd{i}=0` 또는 삼성분 `5`, `hidPontInpDvCd{i}=1`, `hidPontCrdPwd{i}=****` |
| 레일포인트 `1` | `hidStlMnsCd{i}=12`, `hidCrdInpWayCd{i}=P`, `hidIsmtMnthNum{i}=0`, `hidPontDvCd{i}=1`, `hidPontInpDvCd{i}=1`, `hidPontCrdPwd{i}=****` |
| 우리모아 `2` | `hidStlMnsCd{i}=12`, `hidCrdInpWayCd{i}=@`, `hidStlCrCrdNo{i}`, `hidVanPwd{i}`, `hidCrdVlidTrm{i}`, `hidIsmtMnthNum{i}=0`, `hidPontDvCd{i}=2`, `hidPontInpDvCd{i}=3` |
| OK캐쉬백 `4` | `hidStlMnsCd{i}=12`, `hidCrdInpWayCd{i}=@`, `hidStlCrCrdNo{i}`, `hidPontDvCd{i}=4`, `hidPontInpDvCd{i}=4`, `hidPontCrdPwd{i}` |
| L.POINT `5` | `hidStlMnsCd{i}=14`, `hidCrdInpWayCd{i}=@`, `hidAthnVal{i}`, `stSpayGridcnt_1`/`stSpayGridcnt_2`, `spayDvCd_1_1`/`spayDvCd_2_1=09`, `spayCphdDatVal_1_1`/`spayCphdDatVal_2_1=<customerNo>` |
| 기프티켓 `6` | `hidStlMnsCd{i}=12`, `hidCrdInpWayCd{i}=@`, `hidIsmtMnthNum{i}=0`, `hidPontDvCd{i}=6`, `hidPontInpDvCd{i}=5`, `hidStlCrCrdNo{i}=<ticketId>` |
| City point `3` | 카드 결제 row에 `hidPontDvCd1=3`만 추가된다. [source: `sources/V4/a.java:35-38`] |

포인트 사용 검증은 포인트별 최소/단위/잔액/비밀번호 조건을 검사하고 실패 시 dialog 후 `Q1()`로 UI 상태를 되돌린다. [source: `sources/b6/AbstractC1269e.java:1304-1537`]

### 3.4 간편결제/외부결제

`getEasyRequest()`는 외부 앱/웹 콜백 Bundle과 포인트 상태를 받아 결제 row 1을 구성한다. 모든 타입은 먼저 `hidInrecmnsGridcnt=1`, `hidStlMnsSqno1=1`을 넣는다. [source: `sources/V4/a.java:69-75`]

| `bundle.type` | FieldMap 키 |
|---|---|
| `shinhanfan` | `hidStlMnsCd1=02`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=@`, `hidIsmtMnthNum1`, `hidAthnDvCd1=J`, `shStlCrCrdNo1=out_nm1`, `shCrdVlidTrm1=out_nm2`. [source: `sources/V4/a.java:76-90`] |
| `paybooc` | `hidStlMnsCd1=02`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `hidStlCrCrdNo1=pybcCardTknNo`, `hidCrdVlidTrm1=cardValdYymm`, `hidIsmtMnthNum1`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=11`, `spayCphdDatVal_1_1`. [source: `sources/V4/a.java:91-101`] |
| `kbpay` | `hidStlMnsCd1=02`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=@`, `hidIsmtMnthNum1`, `hidCrdVlidTrm1=VALID_TRM`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=15`, `spayCphdDatVal_1_1=OTC`. [source: `sources/V4/a.java:102-115`, `sources/I4/a.java:5`] |
| `railplus` | `hidStlMnsCd1=13`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=@`, `hidStlCrCrdNo1=CARD_NO`, `spayDvCd_1_1=00`. [source: `sources/V4/a.java:117-125`] |
| `payco` | `mainPgCode=31`이면 `hidStlMnsCd1=02`, `spayDvCd_1_1=02`; 아니면 `hidStlMnsCd1=14`, `spayDvCd_1_1=07`. 공통으로 `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `hidStlCrCrdNo1=cardBin`, `stSpayGridcnt_1=1`, `spayCphdDatVal_1_1`. [source: `sources/V4/a.java:126-140`] |
| `kakao` | `payment_method_type=MONEY`이면 `hidStlMnsCd1=14`, `spayDvCd_1_1=08`; 아니면 `hidStlMnsCd1=02`, `spayDvCd_1_1=01`. 공통으로 `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `hidStlCrCrdNo1=""`, `stSpayGridcnt_1=1`, `spayCphdDatVal_1_1`. [source: `sources/V4/a.java:141-150`] |
| `monimopay` | `hidStlMnsCd1=02`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `hidStlCrCrdNo1=otcDesNo`, `hidIsmtMnthNum1`, `spayDvCd_1_1=19`, `stSpayGridcnt_1=1`, `spayCphdDatVal_1_1`은 `tran_serial_num+xid+otcIsAkDtm padded+otcOriNo+card_code+cdno_id padded`. [source: `sources/V4/a.java:151-164`, `sources/V4/a.java:347-362`] |
| `stbk` | `hidStlMnsCd1=14`, `hidMnsStlAmt1`, `hidAthnVal1=password`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=03`, `spayCphdDatVal_1_1=bankCode`. [source: `sources/V4/a.java:165-172`] |
| `stbkAcnt` | `hidStlMnsCd1=14`, `hidMnsStlAmt1`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=10`, `spayCphdDatVal_1_1=ordNo+authNo`. [source: `sources/V4/a.java:173-179`] |
| `railplus_zeropay` | `hidStlMnsCd1=14`, `hidMnsStlAmt1`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=04`, `spayCphdDatVal_1_1=ZERO_PAY_QR_TOKEN`. 콜백 처리에서 token 앞에 `"01"`을 붙인다. [source: `sources/V4/a.java:180-186`, `sources/b6/AbstractC1269e.java:1771-1779`] |
| `naverPay` | `hidStlMnsCd1=02`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=05`, `spayCphdDatVal_1_1=paymentId`. [source: `sources/V4/a.java:187-194`] |
| `naverPayMoney` | `hidStlMnsCd1=14`, `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `stSpayGridcnt_1=1`, `spayDvCd_1_1=16`, `spayCphdDatVal_1_1=paymentId`. [source: `sources/V4/a.java:195-202`] |
| `tosspay`, `tosspay_auto` | `payMethod=TOSS_MONEY`이면 `hidStlMnsCd1=14`, `spayDvCd_1_1=13`; 아니면 `hidStlMnsCd1=02`, `spayDvCd_1_1=12`. 공통으로 `hidMnsStlAmt1`, `hidCrdInpWayCd1=D`, `hidStlCrCrdNo1=stlCrdNo`, `stSpayGridcnt_1=1`, `spayCphdDatVal_1_1=("N" 또는 "Y")+spayTid`. [source: `sources/V4/a.java:203-215`] |

간편결제에 포인트가 같이 선택되면 `getEasyRequest()` 마지막에서 `getPointRequest(2, ...)` 또는 `getPointRequest(2/3, ...)` 결과를 `putAll()`로 합친다. [source: `sources/V4/a.java:219-234`]

## 4. 결제 콜백 및 화면 흐름

`PaymentActivity`는 앱 approve scheme intent면 DEV에서만 `onNewIntent()`로 처리하고, 일반 release 흐름에서는 종료한다. 일반 `onNewIntent()`는 query parameter 전체를 Bundle로 만들고 `otcNo`의 space를 `+`로 보정한 뒤 현재 결제 fragment의 `setEasyPaymentData()`로 넘긴다. [source: `sources/com/korail/talk/ui/payment/PaymentActivity.java:639-681`]

`EasyPayWebViewActivity`는 WebView URL이 approve scheme이면 일반 approve는 VIEW intent로 앱을 다시 열고, `type=tossauto`는 `strResult=SUCC`면 `RESULT_OK`, `strResult=FAIL`이면 `RESULT_CANCELED`로 종료한다. Naver scheme은 외부 앱 실행으로 넘긴다. [source: `sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java:25-50`]

`setEasyPaymentData()`의 성공 조건:

| 타입 | 성공 조건/다음 단계 |
|---|---|
| `railplus`, `railplus_zeropay` | `RET_CODE=000000`이면 `K1()`로 FieldMap 생성, 아니면 `RET_MSG` dialog. [source: `sources/b6/AbstractC1269e.java:1767-1780`] |
| `payco` | `code=0`이면 `spayCphdDatVal` 검증 API 후 `K1()`. [source: `sources/b6/AbstractC1269e.java:1782-1788`, `sources/b6/AbstractC1269e.java:773-802`] |
| `kakao` | `pg_token` 존재 시 `spayCphdDatVal` 검증 API 후 `K1()`. [source: `sources/b6/AbstractC1269e.java:1789-1795`] |
| `paybooc` | `strResult=SUCC`이면 검증 API 후 `K1()`, `FAIL`이면 `msgTxt` dialog. [source: `sources/b6/AbstractC1269e.java:1796-1806`] |
| `naverPay`, `naverPayMoney` | `resultCode=Success`이면 `K1()`, 결과 코드가 있는데 실패면 `resultMessage` dialog. [source: `sources/b6/AbstractC1269e.java:1808-1829`] |
| `stbkAcnt` | `url=cancel`이면 중단, 아니면 `K1()`. [source: `sources/b6/AbstractC1269e.java:1832-1840`] |
| `tosspay`, `tosspay_auto` | `spayTid`를 이전 `spayOrdNo` 응답에서 보강하고 `strResult=SUCC`이면 `K1()`, 아니면 취소 로그 후 중단. [source: `sources/b6/AbstractC1269e.java:1842-1852`] |
| `monimopay` | `otcNo`가 있으면 Monimo decrypt API 후 `K1()`. [source: `sources/b6/AbstractC1269e.java:1854-1865`] |
| 기타 | 바로 `K1()` 호출. [source: `sources/b6/AbstractC1269e.java:1854-1856`] |

`K1()`은 Bundle에 `PAYMENT_AMOUNT`를 넣고 `V4.a.getEasyRequest()` 결과를 `k1()`로 넘긴다. [source: `sources/b6/AbstractC1269e.java:451-456`]

`k1()`은 `PaymentMethod`를 실제 DAO request에 붙이고 `RsvPaymentDao`, `IntgStlDao`, `CommPaymentDao`, `PassPaymentDao` 중 현재 `IPaymentRequest` 타입에 맞는 DAO를 실행한다. 이 문서의 코어 범위에서는 `RsvPaymentDao` 분기가 `ReservationPayment` 호출이다. [source: `sources/b6/AbstractC1269e.java:718-755`]

결제 성공 콜백에서 `dao_rsv_payment`, `dao_comm_payment`, `dao_pass_payment`, `dao_cart_payment`는 같은 블록으로 처리된다. `spayDvCd_1_1=00`이면 RailPlus 동기화를 호출한다. `spayDvCd_1_1=03`, `10`, `16`이면 현금영수증 발급 DAO를 이어서 호출한다. [source: `sources/b6/AbstractC1269e.java:1132-1140`]

`RsvPaymentDao` 응답이 `h_im_flg=Y`이면 이벤트/쿠폰 dialog를 시도하고, 아니면 후속 `B1()` 흐름으로 넘어간다. `B1()`은 JADX가 완전 복원하지 못해 정확한 화면 이동/결과 처리는 `unknown`으로 둔다. [source: `sources/b6/AbstractC1269e.java:1141-1157`, `sources/b6/AbstractC1269e.java:947-958`]

## 5. 응답 모델

모든 응답은 `BaseResponse`의 `strResult`, `h_msg_cd`, `h_msg_txt`를 공통으로 갖는다. [source: `sources/com/korail/talk/network/BaseResponse.java:7-30`]

`RsvPaymentResponse`:

| 클래스 | 필드 |
|---|---|
| `RsvPaymentDao.RsvPaymentResponse` | `h_im_flg`, `tk_coupon_info` |
| `RsvPaymentDao.TkCouponInfo` | `h_cert_pwd`, `h_coup_no`, `h_fdcert_mg_cls_dt`, `h_fdcert_mg_st_dt`, `h_tk_ret_no` |

[source: `sources/com/korail/talk/network/dao/payment/RsvPaymentDao.java:80-124`]

외부결제 준비 응답 중 코어 콜백에서 직접 쓰는 필드:

| 클래스 | 필드/사용 |
|---|---|
| `PaycoPaymentResponse.recvData.result.orderSheetUrl` | WebView URL로 로드. [source: `sources/com/korail/talk/network/dao/pay/PaycoDao.java:11-18`, `sources/b6/AbstractC1269e.java:1176-1178`] |
| `SpayOdrNoResponse` | `fllwScnAppUrlAdr`, `prprNo`, `spayTid`; WebView URL/Monimo app scheme/Toss `spayTid` 보강에 사용. [source: `sources/com/korail/talk/network/dao/pay/SpayOdrNoDao.java:85-103`, `sources/b6/AbstractC1269e.java:1180-1188`] |
| `SpayCphdDatValResponse` | `spayCphdDatVal`, `stlCrCrdNo`; 최종 Bundle로 옮긴 뒤 `K1()`. [source: `sources/com/korail/talk/network/dao/pay/SpayCphdDatValDao.java:63-76`, `sources/b6/AbstractC1269e.java:1198-1215`] |
| `NaverPayRsvResponse.stlScnUrl` | NaverPay/NaverPayMoney WebView URL. [source: `sources/com/korail/talk/network/dao/pay/NaverPayRsvDao.java:35-43`, `sources/b6/AbstractC1269e.java:1190-1196`] |

## 6. 영수증 API 및 모델

승차권 결제/환불 영수증 조회 API:

| API | HTTP | 필드 |
|---|---|---|
| `/classes/com.korail.mobile.receipt.ReceiptInfo` | `POST form` | `Device`, `Version`, `Key`, `h_orgtk_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_tk_ret_pwd` |

[source: `sources/com/korail/talk/network/dao/receipt/ReceiptService.java:9-12`]

`TicketReceiptActivity.u0()`는 `TicketDetailResponse`의 원권 반환번호 구성 필드 `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`를 위 request에 매핑한다. [source: `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:399-408`]

`ReceiptDao.ReceiptResponse` 구조:

| 클래스 | 필드 |
|---|---|
| `ReceiptResponse` | `receipt_infos` |
| `ReceiptInfos` | `receipt_info: List<ReceiptInfo>` |
| `ReceiptInfo` | `cash_rcet_info`, `stl_info`, `h_abrd_dt`, `h_dpt_rs_stn_nm`, `h_dpt_tm`, `h_arv_rs_stn_nm`, `h_arv_tm`, `h_jrny_tp_cd`, `h_prt_disc_knd_nm`, `h_prt_type`, `h_psg_type1_cnt`, `h_psg_type2_cnt`, `h_psg_type3_cnt`, `h_psrm_cl_nm`, `h_rcvd_amt`, `h_ret_fee`, `h_ret_rcvd_amt`, `h_stl_mb_crd_no`, `h_tk_knd_cd`, `h_tk_stt_cd`, `h_trn_clsf_cd`, `h_trn_clsf_nm`, `h_trn_no`, `h_crd_ret_amt`, `h_xpoint_ret_amt`, `h_cmtr_knd_cd` |
| `StlInfo` | `h_acnt_no`, `h_apv_dt`, `h_apv_no`, `h_ismt_mnth_num`, `h_stl_amt`, `h_stl_crd_no`, `h_stl_way_nm`, `h_xpot_no` |
| `CashReceiptInfo` | `h_apv_mtd_nm`, `h_athn_dmn_rcgn_no`, `h_cash_rcet_apv_no`, `h_cash_rcet_txn_dv_cd`, `h_tot_apv_amt` |

[source: `sources/com/korail/talk/network/dao/receipt/ReceiptDao.java:12-287`]

영수증 UI는 첫 번째 `ReceiptInfo`를 기준으로 제목/일자/구간/승객/총액/수수료/반환금액을 표시하고, 직통이면 전체 `stl_info`, 환승이면 앞 절반만 결제수단 목록으로 표시한다. [source: `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:287-359`]

`cash_rcet_info`가 있으면 현금영수증 버튼을 보이고 첫 항목을 `TicketStbkReceiptActivity` extra로 넘긴다. `TicketStbkReceiptActivity`는 네트워크 호출 없이 전달받은 `STBK_RECEIPT_*` extra를 표시한다. [source: `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:314-317`, `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:489-500`, `sources/com/korail/talk/ui/ticket/receipt/TicketStbkReceiptActivity.java:76-95`]

현금영수증 발급 API:

| API | HTTP | 필드 |
|---|---|---|
| `/classes/com.korail.mobile.cashReceipt.issue.do` | `POST form` | `Device`, `Version`, `Key`, `cashRcetTxnDvCd`, `vltIsuFlg`, `cashRcetAthnMtdCd`, `athnDmnRcgnNo`, `apvCnt`, FieldMap `lumpStlTgtNo_1..n` |

[source: `sources/com/korail/talk/network/dao/cashReceipt/CashReceipt.java:11-14`, `sources/com/korail/talk/network/dao/cashReceipt/CashReceiptIssueDao.java:12-76`]

발급 request는 `spayDvCd_1_1`이 `03`, `10`, `16`인 결제 성공 후 만들어진다. 사용자가 현금영수증 옵션을 체크하면 `vltIsuFlg=N`, 목적/인증방법/식별번호를 UI에서 넣고, 체크하지 않으면 `vltIsuFlg=Y`만 넣는다. 대상 번호는 `lumpStlTgtNo_1..n`으로 만든다. [source: `sources/b6/AbstractC1269e.java:603-642`]

지연반환 영수증 API:

| API | HTTP | 필드 | 응답 |
|---|---|---|---|
| `/classes/com.korail.mobile.dlay.pymtRcet.do` | `POST form` | `Device`, `Version`, `Key`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd` | `dlayFarePymtMtdNm`, `retDt`, `dlayFareRetAmt` |

[source: `sources/com/korail/talk/network/dao/delay/DelayService.java:26-28`, `sources/com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java:11-78`]

`DelayReturnReceiptActivity`는 같은 원권 필드에서 `saleDd`, `saleWctNo`, `saleSqno`, `tkRetPwd`를 세팅하고 응답의 결제방법명/반환일/반환금액을 표시한다. [source: `sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:40-49`, `sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:68-72`]

## 7. 로컬 저장 및 세션 영향

결제 request 자체는 `RsvPaymentRequest`/`PaymentMethod` 객체에 담겨 DAO 실행 시 전송된다. 이 분석 범위의 `PaymentMethod` 생성 코드에서 카드번호/비밀번호/콜백 token을 새로 영구 저장하는 동작은 확인되지 않았다. 단, 결제 UI는 저장 카드 목록을 로컬 DB에서 읽어 복호화해 표시한다. `CreditCard` DB 모델은 `cardNumber`, `cardValidateMonth`, `cardValidateYear`, `businessNum`, `cardType`, `cardNickname`을 가진다. [source: `sources/com/korail/talk/database/model/CreditCard.java:6-84`]

저장 카드 목록 조회는 `J4.b.getInstance().getCreditCardList()` 결과 중 닉네임/카드번호/월/년 복호화값이 비어 있지 않은 항목만 사용한다. [source: `sources/H4/a.java:22-24`, `sources/H4/a.java:58-66`]

`PaymentActivity`/fragment는 `EASY_PAY_OPTION` SharedPreferences JSON을 읽어 기본 결제 탭을 정하고, `LOGIN_DATA`에서 `idx`와 로그인 정보를 읽어 `spayOrdNo`의 `encTotTxnAmt`/`idx`를 만든다. 저장값의 실제 런타임 내용은 `unknown`이다. [source: `sources/b6/AbstractC1269e.java:479-485`, `sources/b6/AbstractC1269e.java:812-823`]

영수증 저장은 로컬 파일 시스템에 영향을 준다. 저장 버튼은 Android 10 이상에서 `MediaStore.Downloads`에 PNG를 만들고, 구버전에서는 공용 Downloads 폴더에 PNG 파일을 만든다. 이메일/팩스 공유는 volatile folder의 `RECEIPT_IMAGE_NM` 파일을 만들어 외부 앱 intent로 넘긴다. [source: `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:169-263`, `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:266-270`, `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:555-563`]

RailPlus 결제(`spayDvCd_1_1=00`)가 성공하면 `C0804d.syncRailPlus()`를 호출한다. 동기화가 어떤 로컬/원격 상태를 갱신하는지는 이 범위에서 추가 확인하지 않았으므로 세부 효과는 `unknown`이다. [source: `sources/b6/AbstractC1269e.java:1132-1137`]

## 8. 오류 처리

공통 네트워크 실행은 `BaseDaoHelper.HttpTask`가 `executeDao()`를 백그라운드에서 호출하고 응답/예외를 `onIntegrationResult()`로 넘긴다. Retrofit 403 Forbidden에 `DynaPath-Result` 음수 header가 있으면 body JSON의 `message`를 macro dialog 메시지로 저장한다. [source: `sources/com/korail/talk/network/BaseDaoHelper.java:41-96`]

공통 응답 판정은 `BaseActivity.onIntegrationResult()`가 담당한다. `strResult=FAIL` 또는 `h_msg_cd=WRC000288`이면 `h_msg_txt`를 dialog/error 메시지로 만들고 `onReceiveError()`로 넘긴다. `P058`은 자동로그인 여부에 따라 별도 로그인 예외로 처리한다. [source: `sources/com/korail/talk/view/base/BaseActivity.java:599-649`]

결제 코어 DAO(`dao_rsv_payment`)에 대한 fragment-local `onReceiveError()` 분기는 보이지 않는다. 따라서 `ReservationPayment` 실패는 위 공통 처리에 의존하는 것으로 판단된다. 반면 포인트 조회 실패는 각 포인트 UI의 가용 포인트를 0 또는 미적용 상태로 되돌리는 명시 처리가 있다. [source: `sources/b6/AbstractC1269e.java:1247-1302`]

`PaymentActivity` 자체의 명시 오류 처리는 결제 전 지연배상 PNR 조회/동의 쪽에만 있다. `h_msg_cd=WRZ000001`이면 메시지 dialog 후 결과를 `RESULT_OK`로 설정하고 화면을 닫는다. [source: `sources/com/korail/talk/ui/payment/PaymentActivity.java:705-736`]

간편결제 콜백 오류는 타입별로 일부만 dialog를 띄운다: RailPlus는 `RET_CODE != 000000`이면 `RET_MSG`, Paybooc는 `strResult=FAIL`이면 `msgTxt`, NaverPay/NaverPayMoney는 실패 resultCode가 있으면 `resultMessage`를 표시한다. Toss 결제 실패/취소와 stbkAcnt cancel은 로그 후 중단만 확인된다. [source: `sources/b6/AbstractC1269e.java:1767-1865`]

영수증 조회 화면에는 `dao_ticket_receipt` 전용 `onReceiveError()` override가 없다. 따라서 영수증 API 실패도 공통 오류 처리에 의존한다. 성공 시에만 `L0()`가 호출된다. [source: `sources/com/korail/talk/ui/ticket/receipt/TicketReceiptActivity.java:541-546`, `sources/com/korail/talk/view/base/BaseActivity.java:754-755`]

## 9. Unknowns

- 서버가 각 결제수단 코드(`hidStlMnsCd`, `spayDvCd`)를 실제로 어떻게 해석하는지는 APK 정적 분석만으로 확정할 수 없다.
- 외부 결제 앱/웹이 반환하는 `paymentId`, `spayTid`, `spayCphdDatVal`, `otcNo`, `ordNo`, `authNo`, 카드 token 등 런타임 값은 `unknown`이다.
- `B1()` 후속 화면 이동은 JADX가 완전히 복원하지 못했으므로 정확한 완료 화면/intent 결과는 `unknown`이다.
- RailPlus sync의 내부 상태 갱신 범위는 이 스코프에서 추적하지 않았다.
