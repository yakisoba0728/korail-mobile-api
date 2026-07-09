# 08. PayService 및 간편결제 Provider 연동 정적 분석

분석 범위는 `PayService`와 NaverPay, Payco, Toss 자동결제, `spayOrdNo` 기반 provider, Monimo, STBK, provider별 EasyPay WebView handoff 및 관련 request/response model이다. 본 문서는 APK에서 추출된 JADX/apktool 산출물을 근거로 한 정적 분석이며, 실제 서버 호출이나 응답 샘플 생성은 수행하지 않았다. 서버가 반환하는 구체 JSON 예시는 소스에 없으므로 작성하지 않는다.

## 1. 공통 전제

`PayService`는 Retrofit 1 스타일 interface이며 모든 endpoint가 `@POST` + `@FormUrlEncoded`이다. 각 method는 `Device`, `Version`, `Key`를 공통 field로 받는다. 이 값들은 `BaseRequest` 생성자에서 기본값 `AD`, `250601003`, `korail1234567890`으로 설정된다. 응답의 공통 superclass인 `BaseResponse`는 `strResult`, `h_msg_cd`, `h_msg_txt`를 가진다. [`PayService.java:21`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PayService.java), [`BaseRequest.java:6`](../../../analysis/jadx/sources/com/korail/talk/network/BaseRequest.java), [`BaseResponse.java:7`](../../../analysis/jadx/sources/com/korail/talk/network/BaseResponse.java)

EasyPay 승인 callback의 기준 scheme은 `korailtalk://approve`이다. `PaymentActivity`는 이 scheme에 대해 exported `VIEW` intent-filter를 가진 `singleTask` Activity이고, `onNewIntent()`에서 query parameter 전체를 `Bundle`로 복사해 현재 결제 fragment의 `setEasyPaymentData()`로 전달한다. [`AndroidManifest.xml:196`](../../../analysis/apktool/AndroidManifest.xml), [`D.java:239`](../../../analysis/jadx/sources/S4/D.java), [`PaymentActivity.java:611`](../../../analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java)

## 2. PayService endpoint 전체 목록

| Method | Endpoint | Request field | Response class | Provider/용도 |
|---|---|---|---|---|
| `getPaycoResult` | `/classes/com.korail.mobile.payment.reserve.payco.do` | `Device`, `Version`, `Key`, `ticketPrice`, `ticketName` | `PaycoDao.PaycoPaymentResponse` | Payco 주문서 URL 조회 |
| `getSpayCphdDatVal` | `/classes/com.korail.mobile.pay.spayCphdDatVal.do` | `Device`, `Version`, `Key`, `spayDvCd`, `data` | `SpayCphdDatValDao.SpayCphdDatValResponse` | Payco/Kakao/Paybooc 등 provider 승인값 검증/변환 |
| `getSpayCphdDatValMonimo` | `/classes/com.korail.mobile.pay.monimoDecrypt.do` | `Device`, `Version`, `Key`, `otcNo` | `SpayCphdDatValMonimoDao.SpayCphdDatValMonimoResponse` | Monimo OTC 복호/카드번호 조회 |
| `getSpayOdrNo` | `/classes/com.korail.mobile.pay.spayOrdNo.do` | `Device`, `Version`, `Key`, `spayDvCd`, `totTxnAmt`, `tgtCnt`, `encTotTxnAmt`, `idx`, `lumpStlTgtNo` | `SpayOdrNoDao.SpayOdrNoResponse` | `spayOrdNo` 기반 provider, Monimo, Toss 일반결제 사전 주문번호/연동 URL 생성 |
| `intgStl` | `/classes/com.korail.mobile.pay.intgStl.do` | `Device`, `Version`, `Key`, `ctlDvCd`, `stlPrsJobId`, `cart_LumpStlTgtNo`, `FieldMap` | `BaseResponse` | 장바구니/통합결제 처리 |
| `naverPayMoneyRsv` | `/classes/com.korail.mobile.pay.naverPayMoneyRsv.do` | `Device`, `Version`, `Key`, `productCount`, `productAmount` | `NaverPayRsvDao.NaverPayRsvResponse` | NaverPay Money 결제 화면 URL 조회 |
| `naverPayRsv` | `/classes/com.korail.mobile.pay.naverPayRsv.do` | `Device`, `Version`, `Key`, `productCount`, `productAmount` | `NaverPayRsvDao.NaverPayRsvResponse` | NaverPay 결제 화면 URL 조회 |
| `stbkAcnt` | `/classes/com.korail.mobile.pay.stbkAcnt.do` | `Device`, `Version`, `Key`, `stlBankCd`, `jobDvCd`, `acntNo`, `custCpNo`, `stbkTxnNo`, `stlApvPwd` | `StbkAcntDao.StbkAcntResponse` | STBK 계좌 확인/ARS/등록/비밀번호/삭제 |
| `stbkRegBank` | `/classes/com.korail.mobile.pay.stbkRegBank.do` | `Device`, `Version`, `Key` | `StbkRegBankDao.StbkRegBankResponse` | STBK 등록/등록가능 은행 목록 |
| `stlKeyPrs` | `/classes/com.korail.mobile.pay.stlKeyPrs.do` | `Device`, `Version`, `Key`, `jobDvCd`, `spayDvCd`, `spayStlKeyVal`, `stlBankCd`, `acntNo`, `binNo` | `BaseResponse` | Toss 자동결제 결제키 처리/삭제 |
| `stlKeyQry` | `/classes/com.korail.mobile.pay.stlKeyQry.do` | `Device`, `Version`, `Key`, `spayDvCd` | `TossAutoStlKeyQryDao.StlKeyQryResponse` | Toss 자동결제 결제키 조회 |
| `tossautoC` | `/classes/com.korail.mobile.pay.tossautoC.do` | `Device`, `Version`, `Key` | `TossAutoCreateDao.TossAutoCResponse` | Toss 자동결제 checkout 생성 |

근거: [`PayService.java:22`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PayService.java)

## 3. Request/Response model 상세

### 3.1 Payco

`PaycoPaymentRequest`는 `ticketPrice`, `ticketName`을 가진다. 결제 UI에서는 `ticketPrice=String.valueOf(getReceivedAmount())`, `ticketName="철도승차권"`으로 설정해 DAO를 실행한다. [`PaycoDao.java:22`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PaycoDao.java), [`AbstractC1269e.java:704`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

`PaycoPaymentResponse`는 `recvData`를 가지며, `recvData.result.orderSheetUrl`이 실제 Payco handoff URL이다. 응답은 `BaseResponse` 필드도 상속한다. UI는 이 URL을 그대로 `EasyPayWebViewActivity`에 `WEB_GET_URL` extra로 전달한다. [`PaycoDao.java:11`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PaycoDao.java), [`PaycoDao.java:46`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PaycoDao.java), [`AbstractC1269e.java:1236`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

Payco 승인 callback은 `type=payco`인 `korailtalk://approve` Bundle로 처리된다. `code`가 `"0"`일 때만 `spayCphdDatVal`을 호출한다. 이때 `spayDvCd="02"`이고 `data` list는 `reserveOrderNo`, `sellerOrderReferenceKey`, `paymentCertifyToken`, `cardBin` 순서로 채운다. 실패/취소에 대한 별도 dialog는 이 branch에 없고, `code != "0"`이면 return한다. [`AbstractC1269e.java:777`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`AbstractC1269e.java:1842`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

`spayCphdDatVal` 성공 후에는 `spaycphdDataVal`, `cardBin`, `mainPgCode`를 Bundle에 넣어 최종 `PaymentMethod` 생성으로 넘긴다. `PaymentMethod`에서는 `mainPgCode=="31"`이면 `spayDvCd="02"`, 아니면 `"07"`로 처리하고, `spayCphdDatVal_1_1`에 `spaycphdDataVal`을 넣는다. [`AbstractC1269e.java:1258`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`v4/a.java:126`](../../../analysis/jadx/sources/v4/a.java)

### 3.2 NaverPay / NaverPay Money

`NaverPayRsvRequest`와 `NaverPayMoneyRsvRequest`는 모두 `productAmount`, `productCount`를 가진다. UI는 각각 현재 수납금액과 선택 건수를 설정한다. 두 endpoint 모두 `NaverPayRsvResponse`를 반환하며 provider handoff 필드는 `stlScnUrl`이다. [`NaverPayRsvDao.java:11`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/NaverPayRsvDao.java), [`NaverPayMoneyRsvDao.java:11`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/NaverPayMoneyRsvDao.java), [`NaverPayRsvDao.java:35`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/NaverPayRsvDao.java)

NaverPay와 NaverPay Money 모두 `stlScnUrl`을 `EasyPayWebViewActivity`에 넘겨 WebView로 연다. WebView 내부에서 `nidlogin` scheme이 감지되면 `G.playApp(activity, url)`로 외부 앱 intent를 실행한다. `naver_scheme` resource 값은 `nidlogin`이다. [`AbstractC1269e.java:1250`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`EasyPayWebViewActivity.java:45`](../../../analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java), [`strings.xml:997`](../../../analysis/jadx/resources/res/values/strings.xml)

승인 callback은 `type=naverPay` 또는 `type=naverPayMoney`로 분기한다. `resultCode`가 대소문자 무시 `"Success"`이면 바로 최종 결제 Bundle로 넘긴다. `resultCode`가 존재하지만 성공이 아니면 `resultMessage`를 dialog로 표시한다. callback 자체에 `resultCode`가 없으면 아무 처리 없이 return한다. [`AbstractC1269e.java:1868`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

최종 `PaymentMethod` mapping은 NaverPay가 카드성 결제: `hidStlMnsCd1="02"`, `spayDvCd_1_1="05"`, `spayCphdDatVal_1_1=paymentId`; NaverPay Money가 현금성 결제: `hidStlMnsCd1="14"`, `spayDvCd_1_1="16"`, `spayCphdDatVal_1_1=paymentId`이다. decompiler 상수 `CHECKIN_STATUS_USING`은 `"05"`, `CHECKIN_STATUS_EXCEED`는 `"14"`이다. [`v4/a.java:187`](../../../analysis/jadx/sources/v4/a.java), [`TicketSelfCheckinStatusActivity.java:40`](../../../analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketSelfCheckinStatusActivity.java)

### 3.3 `spayOrdNo` provider / Monimo

`spayOrdNo` provider와 Monimo 계열은 두 단계로 보인다. 먼저 `spayOrdNo`로 사전 주문/연동값을 만들고, provider callback 후 `spayCphdDatVal` 또는 `monimoDecrypt`로 결제 데이터를 검증/복호한다.

`SpayOdrNoRequest` 필드는 `spayDvCd`, `totTxnAmt`, `tgtCnt`, `encTotTxnAmt`, `idx`, `lumpStlTgtNo`, 그리고 local-only flag로 보이는 `isMonimo`이다. 실제 service field에는 `isMonimo`가 없고, `spayDvCd`, `totTxnAmt`, `tgtCnt`, `encTotTxnAmt`, `idx`, `lumpStlTgtNo`가 전송된다. 응답은 `fllwScnAppUrlAdr`, `prprNo`, `spayTid`를 가진다. [`SpayOdrNoDao.java:12`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/SpayOdrNoDao.java), [`SpayOdrNoDao.java:85`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/SpayOdrNoDao.java), [`PayService.java:34`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/PayService.java)

UI의 `p1(spayDvCd)`는 결제금액, 로그인 데이터 기반 암호화 금액, `idx`, 필요 시 `lumpStlTgtNo` 목록을 채워 `spayOrdNo`를 실행한다. `spayDvCd=="19"`이면 Monimo flag를 true로 설정한다. 장바구니 통합결제는 `cart_LumpStlTgtNo`를 세미콜론으로 split해 target 목록으로 넣는다. [`AbstractC1269e.java:816`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

`spayOrdNo` 응답 처리에서 Monimo가 아니면 `fllwScnAppUrlAdr`을 WebView로 연다. Monimo이면 resource `payment_monimo_scheme`에 `prprNo`를 넣어 `monimopay://?xid={prprNo}&mrcType=KRT&callbackUrl=korailtalk://approve?type=monimopay`를 만들고 package `net.ib.android.smcard`로 `ACTION_VIEW` intent를 실행한다. [`AbstractC1269e.java:1240`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`strings.xml:1176`](../../../analysis/jadx/resources/res/values/strings.xml), [`G.java:74`](../../../analysis/jadx/sources/S4/G.java)

Monimo callback은 `type=monimopay`이고 `otcNo`가 있을 때만 처리된다. callback에서 `card_code`, `otcIsAkDtm`, `cdno_id`, `otcNo`를 보관한 뒤 `monimoDecrypt`를 호출한다. `SpayCphdDatValMonimoRequest`는 `otcNo`만 가지며, DAO 실행 시 공백을 `%2B`로 치환해 field로 보낸다. 응답은 `stlCrCrdNo`만 추가 필드로 가진다. [`AbstractC1269e.java:1914`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`SpayCphdDatValMonimoDao.java:12`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java), [`SpayCphdDatValMonimoDao.java:38`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java)

Monimo 복호 응답 처리 후 Bundle에는 `type=monimopay`, 복호된 카드번호로 보이는 `otcDesNo`, 그리고 callback/보관값을 조합한 provider 값이 들어간다. 최종 `PaymentMethod`는 `hidStlMnsCd1="02"`, `hidCrdInpWayCd1="D"`, `hidStlCrCrdNo1=otcDesNo`, installment, `spayDvCd_1_1="19"`, `spayCphdDatVal_1_1=tran_serial_num + xid + padded(otcIsAkDtm) + otcOriNo + card_code + padded(cdno_id)`로 구성한다. [`AbstractC1269e.java:1291`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`v4/a.java:151`](../../../analysis/jadx/sources/v4/a.java), [`HelpSrvCustDao.java:18`](../../../analysis/jadx/sources/com/korail/talk/network/dao/addService/HelpSrvCustDao.java)

### 3.4 Toss 일반결제 / Toss 자동결제

Toss 일반결제는 UI에서 `payType=="10"`일 때 `spayOrdNo`를 `spayDvCd="12"`로 호출한다. 응답의 `fllwScnAppUrlAdr`를 WebView로 열고, callback `type=tosspay` 또는 `type=tosspay_auto`가 들어오면 `spayTid`를 `spayOrdNo` 응답에서 보강한다. `strResult=="SUCC"`이면 최종 결제로 넘기고, 아니면 취소 로그만 남긴다. [`AbstractC1269e.java:280`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`AbstractC1269e.java:1240`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`AbstractC1269e.java:1902`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

Toss 자동결제 checkout 생성 endpoint는 `tossautoC`이다. request는 `BaseRequest` 공통 field만 전송한다. `TossAutoCResponse`는 `billingKey`, `checkoutAndroidUri`, `checkoutIosUri`, `checkoutUri`를 가진다. 결제 화면과 Toss 설정 화면 모두 `checkoutUri`를 `EasyPayWebViewActivity`에 넘기며 requestCode `131`로 결과를 받는다. [`TossAutoCreateDao.java:11`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/TossAutoCreateDao.java), [`AbstractC1269e.java:848`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`TossAutoSettingActivity.java:154`](../../../analysis/jadx/sources/com/korail/talk/ui/setting/tossAuto/TossAutoSettingActivity.java)

`EasyPayWebViewActivity`에서 approve scheme의 query `type=tossauto`는 특수 처리된다. `strResult=="SUCC"`이면 `setResult(RESULT_OK)` 후 finish, `strResult=="FAIL"`이면 `setResult(RESULT_CANCELED)` 후 finish한다. `type`이 `tossauto`가 아니면 approve URL을 그대로 `ACTION_VIEW` intent로 열어 `PaymentActivity` deep link로 넘긴다. [`EasyPayWebViewActivity.java:32`](../../../analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java)

Toss 자동결제 결제키 조회 endpoint는 `stlKeyQry`이고 request는 `spayDvCd` 하나를 추가한다. UI는 Toss 자동결제 조회 시 `spayDvCd="12"`를 사용한다. 응답 `StlKeyQryResponse.spayList`의 item인 `SimplePayInfo`는 `acntNo`, `binNo`, `imageUrl`, `pwdErrTno`, `spayDvCd`, `spayStlKeyVal`, `stlBankCd`, `stlBankNm`, `stlCrdCoCd`를 가진다. [`TossAutoStlKeyQryDao.java:12`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java), [`AbstractC1269e.java:854`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

Toss 설정 화면은 `stlKeyQry` 결과가 빈 목록이면 `tossautoC`로 신규 checkout을 생성하고, 목록이 있으면 화면에 표시한다. 사용자가 등록된 항목의 삭제/처리 버튼을 누르면 `stlKeyPrs`를 실행한다. `StlKeyPrsRequest` 필드는 `jobDvCd`, `spayDvCd`, `spayStlKeyVal`, `stlBankCd`, `acntNo`, `binNo`이며, 설정 화면에서는 `jobDvCd=StbkAcntDao.ACCOUNT_REGISTER("4")`를 넣고 있다. 응답은 `BaseResponse`만 사용한다. [`TossAutoSettingActivity.java:230`](../../../analysis/jadx/sources/com/korail/talk/ui/setting/tossAuto/TossAutoSettingActivity.java), [`TossAutoStlKeyPrsDao.java:11`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/TossAutoStlKeyPrsDao.java), [`StbkAcntDao.java:10`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkAcntDao.java)

최종 `PaymentMethod`에서 Toss는 `payMethod=="TOSS_MONEY"`이면 현금성으로 `hidStlMnsCd1="14"`, `spayDvCd_1_1="13"`을 사용하고, 아니면 카드성으로 `hidStlMnsCd1="02"`, `spayDvCd_1_1="12"`를 사용한다. `spayCphdDatVal_1_1`은 일반결제면 `"N"+spayTid`, 자동결제면 `"Y"+spayTid`이다. [`v4/a.java:203`](../../../analysis/jadx/sources/v4/a.java)

### 3.5 STBK

STBK 계좌 관련 endpoint는 `stbkRegBank`, `stbkAcnt`, 그리고 provider-specific WebView handoff인 `/classes/com.korail.mobile.pay.stbkAcntStlR.do?...`가 보인다. 마지막 URL은 `PayService` method가 아니라 UI에서 `z.getWebHost()`와 공통 parameter를 조합해 `EasyPayWebViewActivity`에 넘긴다. [`AbstractC1269e.java:284`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

`stbkRegBank`는 `BaseRequest`만 전송한다. 응답 `StbkRegBankResponse`는 `regList`, `regPsbList`를 가진다. `Reg` item은 `acntNo`, `imageUrl`, `isPay`, `pwdErrMsg`, `stlBankCd`이고, `RegPsb` item은 `imageUrl`, `stlBankCd`이다. 등록/결제 계좌 목록 화면은 `regList`를 표시하고 footer를 추가한다. [`StbkRegBankDao.java:13`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkRegBankDao.java), [`StbkRegBankDao.java:60`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkRegBankDao.java), [`StbkRegisterAccountListActivity.java:349`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkRegisterAccountListActivity.java)

`stbkAcnt`의 `jobDvCd` 상수는 `"1"` 계좌명 확인, `"2"` ARS 인증 요청, `"3"` ARS 결과 확인, `"4"` 계좌 등록, `"5"` 비밀번호 변경, `"9"` 계좌 삭제이다. request field는 `stlBankCd`, `jobDvCd`, `acntNo`, `custCpNo`, `stbkTxnNo`, `stlApvPwd`; 응답 추가 field는 `custNm`, `stbkTxnNo`이다. [`StbkAcntDao.java:10`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkAcntDao.java), [`StbkAcntDao.java:17`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkAcntDao.java), [`StbkAcntDao.java:77`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/StbkAcntDao.java)

STBK 등록 flow는 다음처럼 분리된다. 계좌 등록 화면은 `jobDvCd="1"`로 은행코드와 계좌번호를 보내고, 응답 `custNm`을 이름 입력란에 표시한다. ARS 인증 화면은 왼쪽 버튼에서 `jobDvCd="2"`와 휴대폰번호를 전송하고, 오른쪽 버튼에서 `jobDvCd="3"`과 `stbkTxnNo`를 전송한다. 결과 확인 후 비밀번호 등록 화면으로 이동한다. 비밀번호 등록은 `jobDvCd="4"` 또는 `"5"`와 6자리 승인 비밀번호를 보낸다. 삭제는 `jobDvCd="9"`와 저장된 승인 비밀번호를 보낸다. [`StbkRegisterAccountActivity.java:65`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkRegisterAccountActivity.java), [`StbkArsVerificationActivity.java:21`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkArsVerificationActivity.java), [`StbkPasswordRegisterActivity.java:180`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkPasswordRegisterActivity.java), [`StbkPasswordEnterActivity.java:114`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkPasswordEnterActivity.java)

STBK 결제 handoff는 두 종류다. 등록된 STBK 계좌/비밀번호 기반 결제는 `payment_scheme` resource `korailtalk://approve?type=%1$s&bankCode=%2$s&password=%3$s`를 `type=stbk`로 채워 `ACTION_VIEW`로 실행한다. 내통장결제는 `stbkAcntStlR.do` WebView URL을 열고 callback `type=stbkAcnt`를 처리한다. `type=stbkAcnt`에서 `url=="cancel"`이면 취소 로그만 남기고 return하며, 그 외에는 최종 결제로 넘긴다. [`StbkRegisterAccountListActivity.java:319`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkRegisterAccountListActivity.java), [`strings.xml:1217`](../../../analysis/jadx/resources/res/values/strings.xml), [`AbstractC1269e.java:1892`](../../../analysis/jadx/sources/B6/AbstractC1269e.java)

최종 `PaymentMethod` mapping은 `type=stbk`가 `spayDvCd_1_1="03"`, `spayCphdDatVal_1_1=bankCode`, `hidAthnVal1=password`; `type=stbkAcnt`가 `spayDvCd_1_1="10"`, `spayCphdDatVal_1_1=ordNo+authNo`이다. 두 경우 모두 현금성 결제수단 코드 `"14"`를 사용한다. [`v4/a.java:165`](../../../analysis/jadx/sources/v4/a.java)

## 4. EasyPay WebView handoff 및 승인 공통 흐름

`EasyPayWebViewActivity`는 `WEB_GET_URL` extra를 받아 WebView에 load한다. cookie와 third-party cookie를 허용하고 mixed content mode를 `0`으로 설정한다. activity 자체는 exported=false이다. [`EasyPayWebViewActivity.java:57`](../../../analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java), [`AndroidManifest.xml:253`](../../../analysis/apktool/AndroidManifest.xml)

URL override 시 superclass가 override하겠다고 판단한 URL에 대해 다음 처리를 한다.

- `korailtalk://approve`이고 `type!=tossauto`: `ACTION_VIEW` intent에 원 URL을 담아 실행한다. Manifest상 이 URL은 `PaymentActivity`로 들어간다.
- `korailtalk://approve`이고 `type=tossauto`: WebView activity 자체가 결과를 `RESULT_OK`/`RESULT_CANCELED`로 반환하고 종료한다.
- scheme이 `nidlogin`: `Intent.parseUri` 기반 `G.playApp()`로 외부 Naver 앱을 실행하거나 설치 페이지로 보낸다.

근거: [`EasyPayWebViewActivity.java:25`](../../../analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java), [`G.java:143`](../../../analysis/jadx/sources/S4/G.java)

`PaymentActivity.onNewIntent()`는 `otcNo` query parameter만 공백을 `+`로 되돌리는 보정을 한다. 이후 현재 fragment가 결제 fragment base class이면 `setEasyPaymentData(bundle)`로 전달한다. [`PaymentActivity.java:615`](../../../analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java)

## 5. 최종 결제 FieldMap 관련 모델

`IntgStlRequest`는 `IPaymentRequest`를 구현하며 `stlPrsJobId` 기본값을 `"0001"`로 설정하고 `PaymentMethod`를 FieldMap으로 보낸다. `getEasyPaymentMethod()`는 `spayDvCd_1_1` 값을 반환한다. [`IntgStlDao.java:14`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/IntgStlDao.java)

`PaymentMethod`는 `LinkedHashMap<String, String>`이며 provider별 결과가 동적 field key로 들어간다. 주요 key는 `hidStlMnsCd{n}`, `hidMnsStlAmt{n}`, `hidCrdInpWayCd{n}`, `hidStlCrCrdNo{n}`, `hidAthnVal{n}`, `spayDvCd_1_1`, `stSpayGridcnt_1`, `spayCphdDatVal_1_1` 등이다. [`PaymentMethod.java:6`](../../../analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java), [`PaymentMethod.java:116`](../../../analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java)

최종 결제 호출은 예약 결제 또는 통합결제 request의 성격에 따라 다른 DAO가 사용할 수 있지만, PayService 범위에서는 `intgStl`이 `PaymentMethod` FieldMap을 그대로 전송한다. [`IntgStlDao.java:72`](../../../analysis/jadx/sources/com/korail/talk/network/dao/pay/IntgStlDao.java)

## 6. 오류/취소 처리 요약

| Provider/flow | 성공 조건 | 실패/취소 처리 |
|---|---|---|
| Payco | callback `type=payco`, `code=="0"` 후 `spayCphdDatVal` 성공 처리 | `code!="0"`이면 별도 dialog 없이 return |
| NaverPay / Money | `resultCode` equals-ignore-case `Success` | `resultCode`가 있으면 `resultMessage` dialog, 없으면 return |
| Paybooc 계열 검증 flow | `strResult=="SUCC"` 후 `spayCphdDatVal` | `strResult=="FAIL"`이면 `msgTxt` dialog |
| STBK 내통장결제 | `type=stbkAcnt`이고 `url!="cancel"` | `url=="cancel"`이면 취소 로그 후 return |
| Toss 일반/자동 결제 callback | `strResult=="SUCC"` | 그 외는 등록/결제 취소 로그 후 return |
| Toss 자동결제 WebView 등록 | `type=tossauto`, `strResult=="SUCC"` -> `RESULT_OK` | `strResult=="FAIL"` -> `RESULT_CANCELED`; 설정 화면에서는 canceled이면 finish |
| RailPlus/ZeroPay 참고 flow | `RET_CODE=="000000"` | 아니면 `RET_MSG` dialog |
| Monimo | `type=monimopay`이며 `otcNo` 존재 후 `monimoDecrypt` | `otcNo` 없으면 추가 처리 없음 |

근거: [`AbstractC1269e.java:1828`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`EasyPayWebViewActivity.java:32`](../../../analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java), [`TossAutoSettingActivity.java:206`](../../../analysis/jadx/sources/com/korail/talk/ui/setting/tossAuto/TossAutoSettingActivity.java)

## 7. 확인된 provider URL/scheme/intent

| Provider | Source | Handoff |
|---|---|---|
| Payco | server response `recvData.result.orderSheetUrl` | `EasyPayWebViewActivity` `WEB_GET_URL` |
| NaverPay / Money | server response `stlScnUrl` | `EasyPayWebViewActivity` `WEB_GET_URL`; `nidlogin` scheme은 외부 앱 실행 |
| `spayOrdNo`/Toss 일반 | server response `fllwScnAppUrlAdr` from `spayOrdNo` | `EasyPayWebViewActivity` `WEB_GET_URL` |
| Monimo | resource `payment_monimo_scheme` | `monimopay://?xid={prprNo}&mrcType=KRT&callbackUrl=korailtalk://approve?type=monimopay`, package `net.ib.android.smcard` |
| STBK 내통장결제 | UI-assembled URL | `{webHost}/classes/com.korail.mobile.pay.stbkAcntStlR.do?{COMMON_PARAMETER}&trPrice={receivedAmount}` |
| STBK 계좌 비밀번호 결제 | resource `payment_scheme` | `korailtalk://approve?type=stbk&bankCode={stlBankCd}&password={password}` via `ACTION_VIEW` |
| Toss 자동결제 등록 | server response `checkoutUri` | `EasyPayWebViewActivity` `WEB_GET_URL`, result requestCode `131` |

근거: [`AbstractC1269e.java:370`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`AbstractC1269e.java:1236`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`AbstractC1269e.java:1240`](../../../analysis/jadx/sources/B6/AbstractC1269e.java), [`StbkRegisterAccountListActivity.java:319`](../../../analysis/jadx/sources/com/korail/talk/ui/stbk/StbkRegisterAccountListActivity.java), [`strings.xml:1176`](../../../analysis/jadx/resources/res/values/strings.xml)

## 20-agent follow-up audit 보강

- `spayOrdNo` launch branch를 Samsung Pay로 일반화하면 안 된다. 이 스코프에서 확인된 branch는 Kakao-like `spayDvCd="01"`, Monimo `"19"`, Toss normal `"12"`다. 별도 Samsung source가 확인되기 전까지는 `spayOrdNo` flow로 표기한다.
- Toss는 normal `spayOrdNo` flow와 auto saved-key flow가 분리된다. 저장된 one-click key가 있으면 `stlKeyQry.spayStlKeyVal`로 `tosspay_auto` bundle을 만들고, key가 없으면 checkout selection flow를 먼저 만든다.
- provider dispatch는 `payType` 기준으로 `3 -> Payco`, `6 -> naverPayRsv`, `12 -> naverPayMoneyRsv`, `13 -> Monimo`, `10 -> Toss normal`, `9 -> Toss auto saved key`, `5/7 -> STBK`로 분기한다.
- STBK 등록은 `regPsbList`가 약관 동의 이후 `StbkUnRegisterAccountListActivity`에서 소비된다. `StbkRegisterAccountActivity`는 먼저 `StbkArsCertificationActivity`를 열고, `jobDvCd="2"` 호출 뒤 `StbkArsVerificationActivity`로 넘어간다.
- `PaymentActivity`는 `singleTask`라 기존 task의 approve callback은 `onNewIntent()`에서 처리된다. fresh approve-scheme launch는 DEV branch가 아니면 `onCreate()`에서 종료되므로, production callback은 기존 task 전제를 가진다.
