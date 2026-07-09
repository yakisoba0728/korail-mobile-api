# 14. 푸시 알림 / 백그라운드 동작 심층 분석

분석 기준: `korail.apk`의 정적 디컴파일 산출물(`analysis/jadx`, `analysis/apktool`)만 사용했다. 네트워크 호출은 실행하지 않았으므로 서버가 런타임에 추가로 내려주는 필드, 값의 의미, 실패 상세는 코드에 명시된 것 외에는 `unknown`으로 둔다.

## 1. 핵심 결론

- 앱 자체 REST 푸시 API는 Retrofit `PushService`에 4개 GET 엔드포인트로 모여 있다: 승무원 호출, 승무원 호출 문구 목록, 정기권/통근권 push 메뉴, 푸시 설정 조회/갱신. 공통 `BaseRequest` 기본값은 `Device=AD`, `Version=250601003`, `Key=korail1234567890`이다. 단, `/classes/com.korail.mobile.push.update` 메서드는 `Key`를 보내지 않는다. [analysis/jadx/sources/com/korail/talk/network/dao/push/PushService.java:12](../../../analysis/jadx/sources/com/korail/talk/network/dao/push/PushService.java), [analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:6](../../../analysis/jadx/sources/com/korail/talk/network/BaseRequest.java)
- 실제 FCM 수신은 앱 클래스가 아니라 H2O SmartAlimi SDK의 `FCMListenerServiceHandler`가 처리한다. FCM data payload를 `MSGVo`로 파싱하고, 온라인이면 SmartBroker에서 새 메시지를 다시 당겨오며, 실패/오프라인이면 FCM payload 자체를 DB에 저장한 뒤 앱 브로드캐스트로 넘긴다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java:14](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java:257](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java)
- 알림 표시는 `com.korail.talk.receiver.PushBroadcastReceiver`가 담당한다. `NotiManager`가 `com.korail.talk.NewMsgReceiver` 브로드캐스트를 보내고, 리시버는 notification channel 생성, badge 갱신, `PendingIntent` 생성, notification id `1002` 게시를 수행한다. `notiType == 9`는 표시하지 않는다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java:20](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java), [analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java:83](../../../analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java)
- 알림 클릭은 `MSGVo.taskName`을 숫자로 해석해 `korailtalk://navigation?...` deeplink로 보낸다. `MSGVo.url`이 있으면 `Param.isExternalBrowser == "Y"`일 때 외부 URL을 열고, 아니면 `korailtalk://navigation?view=web` + `WEB_POST_URL=https://smart.letskorail.com{url}`로 내부 WebView를 연다. [analysis/jadx/sources/S4/C0815o.java:43](../../../analysis/jadx/sources/S4/C0815o.java), [analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java:32](../../../analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java)

## 2. Manifest 컴포넌트와 권한

### 권한

| 항목 | 선언 | 용도/관찰 |
|---|---|---|
| custom signature permission | `com.korail.talk.BroadcastPermission`, `protectionLevel=signature` | SmartAlimi가 Android O 이상에서 앱 브로드캐스트를 보낼 때 `context.getPackageName() + ".BroadcastPermission"`을 사용한다. [analysis/apktool/AndroidManifest.xml:5](../../../analysis/apktool/AndroidManifest.xml), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java:18](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java) |
| push/broadcast | `android.permission.WAKE_LOCK`, `android.permission.VIBRATE`, `android.permission.POST_NOTIFICATIONS`, `com.google.android.c2dm.permission.RECEIVE` | wake lock, 알림/진동, Android 13+ 알림 권한, FCM 수신. [analysis/apktool/AndroidManifest.xml:7](../../../analysis/apktool/AndroidManifest.xml) |
| background | `android.permission.FOREGROUND_SERVICE`, `android.permission.ACCESS_NETWORK_STATE`, `android.permission.ACCESS_WIFI_STATE` | SmartAlimi 네트워크 상태 확인/서비스 유지에 사용 가능한 선언. 실제 `MessageManager`는 일반 `Service`이며 foreground notification 생성은 보이지 않는다. [analysis/apktool/AndroidManifest.xml:9](../../../analysis/apktool/AndroidManifest.xml) |
| device identifiers | `android.permission.READ_PHONE_STATE` | `Const.getDeviceId()`가 `TelephonyManager.getDeviceId()`를 호출하지만, 이 분석 범위의 푸시 등록 패킷에는 `getDeviceId()` 호출이 직접 쓰이지 않는다. [analysis/apktool/AndroidManifest.xml:95](../../../analysis/apktool/AndroidManifest.xml), [analysis/jadx/sources/com/h2osystech/smartalimi/common/Const.java:166](../../../analysis/jadx/sources/com/h2osystech/smartalimi/common/Const.java) |

### 선언된 서비스/리시버/프로바이더

| 컴포넌트 | exported | intent/action | 역할 |
|---|---:|---|---|
| `com.korail.talk.receiver.PushBroadcastReceiver` | true | `com.korail.talk.NewMsgReceiver`, permission `com.korail.talk.BroadcastPermission` | SmartAlimi의 앱 내부 새 메시지 브로드캐스트 수신 후 알림 표시. [analysis/apktool/AndroidManifest.xml:319](../../../analysis/apktool/AndroidManifest.xml) |
| `com.h2osystech.smartalimi.servicealimimodule.DataProvider` | false | authority `@string/authorities` | SmartAlimi DB/provider. [analysis/apktool/AndroidManifest.xml:318](../../../analysis/apktool/AndroidManifest.xml) |
| `com.h2osystech.smartalimi.servicealimi.MessageManager` | true | `com.h2osystech.smartalimi.servicealimi.MessageManager` | AIDL binder service, SmartBroker login/autoLogin/reconnect. [analysis/apktool/AndroidManifest.xml:329](../../../analysis/apktool/AndroidManifest.xml), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java:15](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java) |
| `com.h2osystech.smartalimi.servicealimi.fcm.FCMListenerServiceHandler` | true | `com.google.firebase.MESSAGING_EVENT` | 앱의 실제 FCM service handler. [analysis/apktool/AndroidManifest.xml:334](../../../analysis/apktool/AndroidManifest.xml) |
| `com.h2osystech.smartalimi.servicealimi.RestartReceiver` | true | `RestartReceiver.serviceRestart` | AlarmManager 재기동/reconnect 루프. [analysis/apktool/AndroidManifest.xml:324](../../../analysis/apktool/AndroidManifest.xml), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java:13](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java) |
| Firebase library components | mixed | `FirebaseMessagingService`, `FirebaseInstanceIdReceiver`, `FirebaseInitProvider`, `ComponentDiscoveryService` | Firebase Messaging SDK 구성요소. 앱 메타데이터에서 `firebase_messaging_auto_init_enabled=false`, `firebase_analytics_collection_enabled=false`. [analysis/apktool/AndroidManifest.xml:339](../../../analysis/apktool/AndroidManifest.xml), [analysis/apktool/AndroidManifest.xml:402](../../../analysis/apktool/AndroidManifest.xml) |

## 3. PushService REST API

기본 런타임 REST host는 기존 분석 기준 `https://smart.letskorail.com`이며, 아래 path는 host 상대 경로다. 이 host 선택 로직은 `S4.z.getSSLHost()/getWebHost()`와 `K4.g.SERVER_TYPE=fromCode("3")`에서 확인된다. [analysis/jadx/sources/S4/z.java:46](../../../analysis/jadx/sources/S4/z.java), [analysis/jadx/sources/K4/g.java:89](../../../analysis/jadx/sources/K4/g.java)

### 3.1 `/classes/com.korail.mobile.push.callCrew.do`

- Method: `GET`
- Java method: `PushService.callCrew(...)`
- Request query fields:
  - 공통: `Device`, `Version`, `Key`
  - 승차권/여정: `pnrNo`, `jrnySqno`, `saleWctNo`, `saleDt`, `saleSqno`, `tkRetPwd`
  - 호출 메시지: `sndSqno`, `coutMsgDvCd`, `intgMsgCd1` ... `intgMsgCd10`, `intgMsgCont`
- Request class: `CallCrewDao.CallCrewDaoRequest`
- Response class: `BaseResponse`
  - `h_msg_cd` -> `hMsgCd`
  - `h_msg_txt` -> `hMsgTxt`
  - `strResult` -> `strResult`
  - 그 외 서버 출력: unknown
- UI flow:
  - `TicketListActivity.gotoCallCrew()`가 승차권에서 `pnrNo`, `jrnySqno`, 원권 판매역/일자/일련번호/반환비밀번호를 채워 `CALL_CREW` extra로 `CallCrewActivity`를 연다. [analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1115](../../../analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java)
  - `CallCrewActivity`는 문구 목록에서 하나만 선택하게 하고 `coutMsgDvCd="C"`, 선택 문구 `intgMsgCd1`, 직접입력/자유석 입력을 `"{etc}, {freeSeat}"` 형태의 `intgMsgCont`로 보낸다. [analysis/jadx/sources/com/korail/talk/ui/mtit/CallCrewActivity.java:220](../../../analysis/jadx/sources/com/korail/talk/ui/mtit/CallCrewActivity.java)

### 3.2 `/classes/com.korail.mobile.push.crwCallRq.do`

- Method: `GET`
- Java method: `PushService.callCrewRequestList(...)`
- Request query fields: `Device`, `Version`, `Key`, `qryDvCd`
- Request class: `CallCrewRequestListDao.CallCrewDaoListRequest`
  - `CallCrewActivity.A0()`는 request를 생성만 하고 `qryDvCd`를 세팅하지 않는다. 기본값/서버 처리 의미는 unknown. [analysis/jadx/sources/com/korail/talk/ui/mtit/CallCrewActivity.java:165](../../../analysis/jadx/sources/com/korail/talk/ui/mtit/CallCrewActivity.java)
- Response class: `CallCrewRequestListDao.CallCrewListResponse`
  - BaseResponse 공통 필드
  - `prsList`: `List<PrsList>`
  - `PrsList.intgMsgCd`
  - `PrsList.prsCont`
  - 그 외 서버 출력: unknown

### 3.3 `/classes/com.korail.mobile.push.cmtrKnd.do`

- Method: `GET`
- Java method: `PushService.cmtrKndPassMenu(...)`
- Request query fields: `Device`, `Version`, `Key`, `cmtrKndCd`
- Request class: `CmtrKndMenuDao.CmtrKndMenuRequest`
- Response class: `CmtrKndMenuDao.CmtrKndMenuResponse`
  - BaseResponse 공통 필드
  - `afterDay`
  - `agree`
  - `information`
  - `passData`: `DiscountMenuDao.PassMainInfo`
  - `title`
  - 그 외 `passData` 내부 서버 출력: 이 문서 범위에서는 unknown
- 사용처: 통근/정기권 booking flow에서 JSON `CMTR_KND_CD`를 읽어 조회하고 응답을 `DiscountMenuDao.DiscountMenu`로 변환한다. [analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/commutation/a.java:137](../../../analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/commutation/a.java)

### 3.4 `/classes/com.korail.mobile.push.update`

- Method: `GET`
- Java method: `PushService.pushUpdate(...)`
- Request query fields:
  - `Device`
  - `Version`
  - `job_dv_cd`: 조회/기본값 생성/수정 구분으로 보인다. 코드상 `"R"` 조회, `"U"` 수정, `CashRfnDao.f28877I` 값은 decompiler 상수명만 확인되며 실제 문자열은 이 문서에서 unknown.
  - `tnsm_flg1`
  - `tnsm_flg2`
  - `tnsm_flg3`
  - `tnsm_flg4`
  - `dptUsrInpTnum`
  - `arvUsrInpTnum`
- 주의: `PushService.pushUpdate()`는 `Key` query를 선언하지 않는다. `PushUpdateRequest`가 `BaseRequest`를 상속하지만 `executeDao()`에서 `getKey()`를 전달하지 않는다. [analysis/jadx/sources/com/korail/talk/network/dao/push/PushUpdateDao.java:122](../../../analysis/jadx/sources/com/korail/talk/network/dao/push/PushUpdateDao.java)
- Request class: `PushUpdateDao.PushUpdateRequest`
- Response class: `PushUpdateDao.PushUpdateResponse`
  - BaseResponse 공통 필드
  - `prs_cnqe_msg_cd`
  - `tnsm_flg1`, `tnsm_flg2`, `tnsm_flg3`, `tnsm_flg4`
  - `dptUsrInpTnum`, `arvUsrInpTnum`
  - 그 외 서버 출력: unknown
- UI flow:
  - 로그인 성공 후 고객번호가 바뀌면 `BaseActivity`가 `job_dv_cd="R"`로 호출해 "푸시 DB 기본값 생성 요청"을 수행한다. [analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:136](../../../analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java)
  - `PushSettingActivity` 초기 진입은 `job_dv_cd="R"` 조회, 토글/시간 변경은 `job_dv_cd="U"`로 갱신한다. [analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java:197](../../../analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java)
  - 화면 해석: `tnsm_flg1`은 기본 알림 switch, `tnsm_flg4`는 이벤트/공지 switch, `tnsm_flg2`는 출발 전 알림 인덱스, `tnsm_flg3`는 도착 전 알림 인덱스, `dptUsrInpTnum`/`arvUsrInpTnum`은 사용자 입력 분 단위 시간이다. [analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java:133](../../../analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java)
  - `prs_cnqe_msg_cd == "WRB000032"`이면 조회 후 추가 갱신 호출로 fallback한다. 이 코드의 서버 의미는 unknown. [analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java:279](../../../analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java)

## 4. 특실 업그레이드 푸시 관련 API

특실 업그레이드 푸시는 `MSGVo.taskName` 라우팅으로 `SpecialRoomUpgradeActivity`에 도달할 수 있고, activity는 `MSGVo.param` JSON의 짧은 키(`a` ... `t`)를 승차권 변경 request로 해석한다. [analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java:103](../../../analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java)

### 4.1 `/classes/com.korail.mobile.myTicket.reqUpgradeSeat`

- Method: `GET`
- Java method: `MyTicketService.requestUpgradeSeat(...)`
- Request query fields:
  - 공통: `Device`, `Version`, `Key`
  - 원권: `ogtkSaleDd`, `ogtkSaleWctNo`, `ogtkSaleSqno`, `ogtkRetPwd`
  - 여정: `jrnyTpCd`, `jrnySqno`, `dptDt`, `dptStnConsOrdr`, `dptStnRunOrdr`, `dptRsStnCd`, `dptTm`, `arvDt`, `arvStnConsOrdr`, `arvStnRunOrdr`, `arvRsStnCd`, `arvTm`, `trnNo`, `runDt`, `trnGpCd`
  - 좌석: `roomClsfCd`, `scarNo`, `seatNo`, `rqSeatAttCd`
- Request class: `com.korail.talk.network.request.myTicket.PushUpdateRequest`
- `MSGVo.param` 매핑:
  - `a` -> `ogtkSaleDd`
  - `b` -> `ogtkSaleWctNo`
  - `c` -> `ogtkSaleSqno`
  - `d` -> `ogtkRetPwd`
  - `e` -> `jrnyTpCd`
  - `f` -> `jrnySqno`
  - `g` -> `dptDt`
  - `h` -> `dptStnConsOrdr`
  - `i` -> `dptStnRunOrdr`
  - `j` -> `dptRsStnCd`
  - `k` -> `dptTm`
  - `l` -> `arvDt`
  - `m` -> `arvStnConsOrdr`
  - `n` -> `arvStnRunOrdr`
  - `o` -> `arvRsStnCd`
  - `p` -> `arvTm`
  - `q` -> `trnNo`
  - `r` -> `runDt`
  - `t` -> `roomClsfCd`
  - `trnGpCd`는 activity에서 `"100"`으로 고정한다.
- Response class: `SpecialRoomUpgradeDao.SpecialRoomUpgradeResponse`
  - BaseResponse 공통 필드
  - `ticketInfo.custNm`
  - `ticketInfo.scnIndcAmt`
  - `ticketInfo.totFare`
  - `jrnys[].lumpStlTgtNo`
  - 그 외 서버 출력: unknown

### 4.2 `/classes/com.korail.mobile.myTicket.procUpgradeSeat`

- Method: `GET`
- Java method: `MyTicketService.procUpgrade(...)`
- Request query fields:
  - 공통: `Device`, `Version`, `Key`
  - 결제/마일리지 처리: `totTxnAmt`, `totCncRetAmt`, `totCncRetFee`, `feeProyStlSqno`, `lumpStlTgtNo`, `mnsGridcnt`, `stlMnsSqno`, `stlMnsCd`, `mnsStlAmt`, `crdInpWayCd`, `ismtMnthNum`, `pontDvCd`, `pontInpDvCd`, `prepCrdTxnBfAmt`, `prepCrdTxnAftAmt`
- Request class: `SpecialRoomUpgradeProcessDao.SpecialRoomUpgradeProcessRequest`
- Response class: `BaseResponse`
  - 성공 판정: activity는 `hMsgCd == "WRTP20000"`이면 완료로 처리한다.
  - 그 외 서버 출력: unknown
- Activity 기본 세팅:
  - `totCncRetAmt="0"`, `totCncRetFee="0"`, `mnsGridcnt="1"`, `stlMnsSqno="1"`, `stlMnsCd="12"`, `crdInpWayCd="@"`, `ismtMnthNum="0"`, `pontDvCd="1"`, `pontInpDvCd="1"`, `feeProyStlSqno="0"`, `prepCrdTxnAftAmt="0"`, `prepCrdTxnBfAmt="0"`로 채운다. [analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java:69](../../../analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java)

## 5. 앱 업데이트 확인

- 앱 설정의 버전 화면은 push token과 별개로 cache API를 사용한다.
- Endpoint: `GET /file/CACHE/prdMobilePlusMain.cache`
- Query: `timeStamp`
- Java method: `CacheService.getAppData(timeStamp)`
- Response class: `AppDataDao.AppDataResponse`
  - BaseResponse 공통 필드
  - `version.NEWDVERSION`
  - `version.AMESSAGE`
  - `disability_certification_msg`
  - `forSeatIntg`
  - `airportBusMsg` -> `limousine`
  - `railplus_cardinfo`
  - 그 외 서버 출력: unknown
- `VersionActivity`는 `version.NEWDVERSION`와 현재 앱 버전명을 비교해 업데이트 버튼을 보이고, 버튼 클릭 시 `G.moveToGooglePlay(context, packageName)`를 호출한다. Google Play URL 구성은 이 문서 범위에서 추가 분석하지 않았다. [analysis/jadx/sources/com/korail/talk/network/dao/cache/CacheService.java:14](../../../analysis/jadx/sources/com/korail/talk/network/dao/cache/CacheService.java), [analysis/jadx/sources/com/korail/talk/ui/setting/VersionActivity.java:34](../../../analysis/jadx/sources/com/korail/talk/ui/setting/VersionActivity.java)

## 6. H2O SmartAlimi / FCM 토큰 등록

### 6.1 앱이 SmartAlimi에 로그인하는 지점

- `b5.g.bindService()`가 `MessageManager`에 bind한다. 연결 후 `SmartAgentInterface`를 얻어 다음 값을 설정한다. [analysis/jadx/sources/b5/g.java:116](../../../analysis/jadx/sources/b5/g.java)
  - `enableLog(I4.a.IS_DEBUG_LOG)`
  - `setAppType(K4.g.PUSH_APPTYPE)` -> `"korailtalk"`
  - `setServerIPPort(z.getPushAddress(), K4.g.PUSH_PORT)` -> product 기준 `smart.letskorail.com`, port `"3101"`
  - `setPhoneNumber("")`
  - `setBedgeCountPackage(context.getPackageName() + ".IntroActivity")`
  - `setLogin(h.getInstance().getCustNo(), "1", 1)`
- `K4.g`의 push 상수: `PUSH_APPTYPE="korailtalk"`, `PUSH_REAL="smart.letskorail.com"`, `PUSH_STAGING="smartbeta.letskorail.com"`, `PUSH_DEV="dev.letskorail.com"`, `PUSH_PORT="3101"`. [analysis/jadx/sources/K4/g.java:67](../../../analysis/jadx/sources/K4/g.java)

### 6.2 FCM token 획득/저장

- `FCMAdapter.getToken()`은 `FirebaseMessaging.getInstance().getToken()`으로 비동기 토큰을 얻고 최대 8회, 500ms 간격으로 기다린다.
- 토큰이 있으면 `SharedData.setSharedData(context, "UserInfo", "gcmToken", token)` 및 `Const.setGcmRegID(token)`에 저장한다.
- `FCMListenerServiceHandler.onNewToken(token)`도 로그인된 `UserID`가 있으면 같은 저장을 수행하고 `alimiInterface.registToken()`을 호출한다.
- 저장 위치:
  - SharedPreferences name: `UserInfo`
  - key: `gcmToken`
  - process memory: `Const.gcmRegID`
- 서버 등록 실패/성공의 상세 서버 응답 필드 중 코드가 파싱하는 값 외는 unknown. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMAdapter.java:17](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMAdapter.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java:98](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SharedData.java:53](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SharedData.java)

### 6.3 SmartBroker 토큰 등록 패킷

`AlimiInterface.setLogin()` -> `loginProc()` -> `SmartBrokerAdapter.registPush(userId, userPw)` 흐름이다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java:761](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java:568](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java)

`REGIST_PUSH2` request payload는 고정폭 문자열로 구성된다.

| 순서 | 값 | 길이/형태 | 출처 |
|---:|---|---|---|
| 1 | `userId` | `%-32s` | `h.getInstance().getCustNo()` 또는 `UserInfo/UserID` |
| 2 | `userPw` | `%-128s` | 앱 호출은 `"1"`, 없으면 userId |
| 3 | timestamp | `%-14s` | `Const.DateTime()` |
| 4 | channel/type | `%1s` | `"A"` |
| 5 | FCM token | `%-256s` | `Const.getGcmRegID()` / `UserInfo/gcmToken` |
| 6 | app type | `%-32s` | `Const.brokerAppType`, 앱은 `"korailtalk"` |
| 7 | phone | `%-20s` | `Const.getPhoneNum(context)`, 없으면 코드 기본값 사용 |
| 8 | login flag | `%1s` | `Const.LOGINFLAG` |
| 9 | reserved? | `%02d` | `0` |
| 10 | reserved? | `%02d` | `0` |
| 11 | SDK version | `%-2s` | `CommonUtil.getSDKVersion()` |
| 12 | OS version | `%-6s` | `CommonUtil.getOSVersion()` |
| 13 | model | `%-24s` | `CommonUtil.getModel()` |
| 14 | locale region | `%-2s` | `CommonUtil.getLocaleRegion(context)` |
| 15 | boot time | `%-14s` | `CommonUtil.getBootTime()` |
| 16 | app version | `%-6s` | `CommonUtil.getAppVersion(context)` |
| 17 | network | `%-4s` | `CommonUtil.getConnectedNetwork(context)` |

`REGIST_PUSH2` response parser extracts only:

- `code`: bytes 0-31
- `rtn_cd`: byte 32, success code `0`
- `rtn_msg`: bytes 33-112
- `push_type`: byte 113, saved to `UserInfo/PushType`
- `log_level`: byte 114, saved to `noticeEnv/logLevel`
- `id_multiuse`: byte 115, parsed but not used in the observed code path
- 그 외 서버 출력: unknown

[analysis/jadx/sources/com/h2osystech/smartalimi/common/ConstructGetPacket.java:127](../../../analysis/jadx/sources/com/h2osystech/smartalimi/common/ConstructGetPacket.java)

## 7. 메시지 수신 / 백그라운드 흐름

### 7.1 FCM data payload 처리 경로

1. Android delivers `com.google.firebase.MESSAGING_EVENT` to `FCMListenerServiceHandler`.
2. `onMessageReceived()` logs `zVar.getData()`, creates `AlimiInterface` if needed, and returns early if `UserInfo/UserID` is empty.
3. It reads `badge` from FCM data and locks on static `messageLock`.
4. If offline, it parses the FCM data payload into `MSGVo`, inserts DB, and broadcasts notification.
5. If online, it calls `getNewMessageAndNoti(true, badge)` to pull messages from SmartBroker. If this returns `-1`, it falls back to parsing the FCM payload and broadcasting it.

필수/관찰된 FCM data key:

| FCM key | MSGVo field | Notes |
|---|---|---|
| `Subject` | `title` | Required for parser success |
| `Content` | `content` | Nullable in code |
| `Date` | `date` and `uniqSeq` part | Required |
| `Seq` | `seq` and `uniqSeq` part | Required |
| `TimeStamp` | `timeStamp` and `uniqSeq` part | Required |
| `SenderID` | `sender` | Nullable |
| `Param` | `param` | JSON string for deeplink/special flows |
| `MsgType` | `receiver` | Naming is SDK-specific |
| `BizName` | `taskName` | App treats this as numeric message/task id |
| `badge` | broadcast extra `badge` | Parsed with `Integer.parseInt(...trim())` |

파서 성공 조건은 `Subject`, `Seq`, `Date`, `TimeStamp`가 non-null인 것이다. 이 FCM 파서는 `notiType`을 직접 세팅하지 않으므로, 이후 알림 타입은 helper 파싱 결과에 따라 `-1`/기본값일 수 있다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java:19](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java)

### 7.2 SmartBroker pull 경로

`AlimiInterface.getNewMessageAndNoti(true, badge)`:

1. Requires online network and initialized SmartBroker.
2. Calls `SmartBrokerAdapter.getNewMessageLimit()`.
3. `getNewMessageLimit()` calls `GET_NEW_MSG_CNT2`, caps count at 50, then calls `GET_NEW_MSG2`.
4. `GET_NEW_MSG2` response is parsed into `MSGVo` list by `ConstructGetPacket.getMsgData2()`.
5. Each message is inserted into `push.db` table `tb_{LOGINID}` via `DBAdapter.insertMsg2()`.
6. Receipts are sent with `receipt2(userID, messageList, gcmRegID)`.
7. Notification broadcast is sent immediately when `Const.isOnebyOne` is true; otherwise the latest message is batched through `notiStart()` timer.

SmartBroker request/response protocol은 Retrofit HTTP가 아니라 `ERBAPIs.erbcall` 위의 native/binary 호출이다. 관찰된 operation은 `REGIST_PUSH2`, `GET_NEW_MSG_CNT2`, `GET_NEW_MSG2`, `GET_MSG_ALL2`, `GET_PUSH_ONOFF`, `PUSH_ONOFF`, `LOGOUT`이다. 파싱 필드 외 서버 출력은 unknown이다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java:149](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java:528](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java)

### 7.3 로컬 DB 스키마

Database는 `push.db`, version은 `2`다. 사용자별 table은 `tb_{LOGINID}`이며, dot은 `__0x02`로 escape되고 decompiler sentinel string은 `__0x01`로 escape된다. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/DBAdapter.java:18](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/DBAdapter.java)

컬럼:

- `uniseq` primary key
- `seq`
- `timestamp`
- `datetime`
- `readYn`
- `receiver`
- `sender`
- `title`
- `msgType`
- `content`
- `url`
- `attachfilecnt`
- `attachfile`
- `downfilePath`
- `notiType`
- `taskName`
- `receiveTime`
- `reserved1` (used for `MSGVo.param`)

`insertMsg2()` writes `MSGVo.param` to `reserved1`. `getAllMsg()` reads `reserved1` back into `MSGVo.param`. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/DBAdapter.java:241](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/DBAdapter.java)

## 8. 브로드캐스트 / 알림 표시 흐름

### 8.1 SmartAlimi에서 앱으로 전달되는 broadcast extras

`NotiManager.executeReceiver(...)` sends:

- action: `context.getPackageName() + ".NewMsgReceiver"` -> `com.korail.talk.NewMsgReceiver`
- permission on Android O+: `context.getPackageName() + ".BroadcastPermission"` -> `com.korail.talk.BroadcastPermission`
- extras:
  - `r.CATEGORY_MESSAGE`: `MSGVo` Parcelable. Decompiler symbol is AndroidX `NotificationCompat.CATEGORY_MESSAGE`; exact string literal is not shown in app source.
  - `notiType`: integer
  - `uniseq`: string
  - optional `badge`: integer
  - optional `getNewMsgStartEnd`: string
- error broadcast action: `com.korail.talk.GCM_Error_Receiver`, extras `errorNo`, `gcm`; 이 범위의 manifest에서 대응 앱 receiver 선언은 확인되지 않아 처리는 unknown이다.

[analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java:20](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java)

### 8.2 `PushBroadcastReceiver`

`onReceive()`:

- calls `super.onReceive()`
- requires `intent.hasExtra(r.CATEGORY_MESSAGE)`
- reads `MSGVo`, `param`, `notiType`, numeric `taskName`, and `badge`
- calls `Const.updateBadgetCount(context, badge)`
- prints bundle data
- if `notiType != 9`, calls internal notification builder

Notification builder:

- `NotificationManager.cancelAll()` first.
- For Android O+:
  - normal channel: id `com.korail.talk` (`G4.a.APPLICATION_ID`), name `일반공지`, importance `4`, badge disabled.
  - emergency channel: id `com.korail.talkemergency`, name `긴급공지`, importance `4`, badge enabled.
- Channel choice:
  - if SDK < 26 or `badge <= 0`: normal channel.
  - if SDK >= 26 and `badge > 0`: emergency channel.
- Notification:
  - small icon `ic_carrier`
  - large icon `ic_launcher`
  - title `MSGVo.title`
  - text/bigText `MSGVo.content`
  - ticker `MSGVo.date`
  - sound default notification sound
  - priority `2`
  - number `badge`
  - auto cancel true
  - notification id `1002`
- Wake lock: `PowerManager.newWakeLock(805306374, contextClassName).acquire(3000L)`.

Channel creation also happens at app startup in `KTApplication.onCreate()` for the same two channel ids. [analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java:53](../../../analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java), [analysis/jadx/sources/com/korail/talk/application/KTApplication.java:35](../../../analysis/jadx/sources/com/korail/talk/application/KTApplication.java)

## 9. 알림 클릭 deeplink / intent extras

### 9.1 PendingIntent 생성

`PushBroadcastReceiver.e(MSGVo)` builds the click intent:

1. `C0815o.getPushIntent(context, Integer.parseInt(MSGVo.taskName))` creates an `ACTION_VIEW` intent with a `korailtalk://navigation?...` URI.
2. If `MSGVo.url` is empty:
   - add extra `msg_vo` = `MSGVo`.
3. If `MSGVo.url` is non-empty:
   - parse `new JSONObject(MSGVo.param).optString("isExternalBrowser")`.
   - if `"Y"`: `intent.setData(Uri.parse(url))`, `FLAG_ACTIVITY_NEW_TASK`.
   - else: `intent.setData(korailtalk://navigation?view=web)` and add `WEB_POST_URL = z.getWebHost() + url`.
4. PendingIntent: `PendingIntent.getActivity(context, 0, intent, 201326592)`. The numeric flags correspond to immutable/update-current style flags on modern Android; exact symbolic names are not present in decompiled source.

[analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java:32](../../../analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java)

`PushPopupActivity` implements the same behavior for popup-confirm flows: confirm opens `getPushIntent(...)`, empty URL passes `msg_vo`, external browser opens URL outside, internal URL uses `navigation_web_view` with `WEB_POST_URL`. [analysis/jadx/sources/com/korail/talk/ui/push/PushPopupActivity.java:27](../../../analysis/jadx/sources/com/korail/talk/ui/push/PushPopupActivity.java)

### 9.2 `taskName` / `messageId` routing

`C0815o.getPushIntent()` maps numeric task ids to navigation URIs:

| taskName | deeplink |
|---:|---|
| `5` | `korailtalk://navigation?view=pushHistory` |
| `12`, `13`, `14`, `17`, `19`, `24`, `25`, `26` | `korailtalk://navigation?view=ticket` |
| `20` | `korailtalk://navigation?view=pushHistory` |
| `21` | `korailtalk://navigation?view=discountCoupon` |
| `22` | `korailtalk://navigation?view=delayDiscountCoupon` |
| `27` | `korailtalk://navigation?view=mileage` |
| `50` | `korailtalk://navigation?view=seasonTicket` |
| `51` | `korailtalk://navigation?view=periodSeasonTicket` |
| default | `korailtalk://navigation?view=booking` |

String resources define these URIs. `NavigationActivity` is exported for `korailtalk://navigation`, and `S4.y.getClassNm()` maps `view` to concrete activity classes. [analysis/jadx/sources/S4/C0815o.java:43](../../../analysis/jadx/sources/S4/C0815o.java), [analysis/jadx/resources/res/values/strings.xml:1006](../../../analysis/jadx/resources/res/values/strings.xml), [analysis/apktool/AndroidManifest.xml:180](../../../analysis/apktool/AndroidManifest.xml), [analysis/jadx/sources/S4/y.java:26](../../../analysis/jadx/sources/S4/y.java)

`PushHistoryActivity` has a narrower historical-list mapping:

- `21` -> `DiscountCouponActivity`
- `22` -> `DelayDiscountCouponActivity`
- `12`, `13`, `14`, `24`, `25`, `26`, `35`, `36` -> `TicketListActivity`
- default -> `MainBookingActivity`
- `20` has special "타임체인지" handling: `MSGVo.param` JSON/array is parsed into original-ticket inquiry data, then ticket-change flow is launched with `TIME_CHANGE_EVENT=true`.

[analysis/jadx/sources/com/korail/talk/ui/push/PushHistoryActivity.java:364](../../../analysis/jadx/sources/com/korail/talk/ui/push/PushHistoryActivity.java), [analysis/jadx/sources/com/korail/talk/ui/push/PushHistoryActivity.java:448](../../../analysis/jadx/sources/com/korail/talk/ui/push/PushHistoryActivity.java)

### 9.3 Manifest에 선언된 deeplink activity

- `korailtalk://navigation` -> `NavigationActivity`, exported true, `singleTask`, excludes recents.
- `korailtalk://member_info` -> `DataActivity`, exported true, `singleInstance`.
- `korailtalk://approve` -> `PaymentActivity`, exported true.
- `korailtalk://railpluscardinfo` -> `RailPlusActivity`, exported true.

[analysis/apktool/AndroidManifest.xml:180](../../../analysis/apktool/AndroidManifest.xml), [analysis/apktool/AndroidManifest.xml:188](../../../analysis/apktool/AndroidManifest.xml), [analysis/apktool/AndroidManifest.xml:196](../../../analysis/apktool/AndroidManifest.xml), [analysis/apktool/AndroidManifest.xml:206](../../../analysis/apktool/AndroidManifest.xml)

## 10. Receiver/service lifecycle과 백그라운드 동작

- `MessageManager.onCreate()` loads `UserInfo` and `noticeEnv` values into `Const`, creates `AlimiInterface`, and for non-public push type (`brokerPushType != 0`) starts/auto-logins broker handling. On Android O+ it avoids `startService` self-start and calls `autoLogin()` directly if not bound. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java:60](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java)
- `MessageManager.onStartCommand()` handles `intent.getType()=="korailstartStatus"` and extra `startStatus`:
  - `0`: bootcompleted-style autoLogin.
  - `99`: public push type only, `getNewMessageAndNoti(true)`.
  - `2`: alarm/retry path. Acquires a partial wake lock, checks session, reconnects with backoff, then schedules another restart alarm.
  - It returns `super.onStartCommand(intent, 1, 1)` in the observed paths; exact restart mode constant is not explicit in decompiled source. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java:103](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java)
- `AlimiInterface.registerRestartAlarm(true)` schedules `RestartReceiver.serviceRestart` with `AlarmManager.setExactAndAllowWhileIdle(..., now + 180000, pendingIntent)`, so retry cadence is 3 minutes before additional backoff logic. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java:622](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java)
- `RestartReceiver` receives the alarm and starts `MessageManager` with type `korailstartStatus`, extra `startStatus=2`. On Android O+ it first checks whether `MessageManager` is already running and returns if not running. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java:27](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java)
- `NetworkStatusReceiver` is dynamically registered for `CONNECTIVITY_CHANGE` and `WIFI_STATE_CHANGE` when private/hybrid push is enabled. On network restoration it can call `getNewMessageAndNoti(true)` for Android O+. [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java:592](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NetworkStatusReceiver.java:46](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NetworkStatusReceiver.java)

## 11. 식별자 / 저장 키 요약

| 분류 | 이름 | 출처/저장 위치 | 비고 |
|---|---|---|---|
| REST app id | `Device=AD` | `BaseRequest` | 거의 모든 Retrofit request 공통 |
| REST API version | `Version=250601003` | `BaseRequest`, `K4.g.COMMON_PARAMETER` | 앱 분석 문서의 API version과 일치 |
| REST key | `Key=korail1234567890` | `BaseRequest` | `/push.update`에는 전달되지 않음 |
| FCM token | `gcmToken` | SharedPreferences `UserInfo/gcmToken` | `Const.gcmRegID`에도 복사 |
| SmartBroker user id | `UserID` | `UserInfo/UserID`, `Const.userID` | 앱은 고객번호 `custNo`로 로그인 |
| SmartBroker user pw | `UserPW` | `UserInfo/UserPW`, `Const.userPW` | 앱 호출은 `"1"` |
| SmartBroker host | `ipaddress` | `noticeEnv/ipaddress` | product: `smart.letskorail.com` |
| SmartBroker port | `port` | `noticeEnv/port` | `"3101"` |
| SmartBroker app type | `AppType` | `noticeEnv/AppType` | `"korailtalk"` |
| push type | `PushType` | `UserInfo/PushType` | `0` public, `1` private, `2` hybrid |
| notification on/off | `NoticeOnOff` | `noticeEnv/NoticeOnOff` | `setPushOnOff()` 저장 |
| message DB table id | `LOGINID` | `Const.userID` 기반 | `tb_{LOGINID}` |
| badge main activity | `mainActivity` | `noticeEnv/mainActivity` | 앱은 `com.korail.talk.IntroActivity` 문자열을 저장 |

[analysis/jadx/sources/com/h2osystech/smartalimi/common/Const.java:18](../../../analysis/jadx/sources/com/h2osystech/smartalimi/common/Const.java), [analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java:551](../../../analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java)

## 12. 출처 파일 색인

- `analysis/apktool/AndroidManifest.xml`
- `analysis/jadx/resources/res/values/strings.xml`
- `analysis/jadx/sources/K4/g.java`
- `analysis/jadx/sources/S4/C0815o.java`
- `analysis/jadx/sources/S4/y.java`
- `analysis/jadx/sources/S4/z.java`
- `analysis/jadx/sources/b5/g.java`
- `analysis/jadx/sources/b5/h.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/aidllib/MSGVo.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/common/Const.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/common/ConstructGetPacket.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/AlimiInterface.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NetworkStatusReceiver.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/NotiManager.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMAdapter.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/DBAdapter.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SharedData.java`
- `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimimodule/SmartBrokerAdapter.java`
- `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/cache/AppDataDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/cache/CacheService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/MyTicketService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeProcessDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/push/CallCrewDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/push/CallCrewRequestListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/push/CmtrKndMenuDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/push/PushService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/push/PushUpdateDao.java`
- `analysis/jadx/sources/com/korail/talk/network/request/myTicket/PushUpdateRequest.java`
- `analysis/jadx/sources/com/korail/talk/receiver/PushBroadcastReceiver.java`
- `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/commutation/a.java`
- `analysis/jadx/sources/com/korail/talk/ui/mtit/CallCrewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/push/PushHistoryActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/push/PushPopupActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/setting/PushSettingActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/setting/VersionActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java`

## 20-agent follow-up audit 보강

- WorkManager component는 library manifest를 통해 존재한다(`SystemJobService`, diagnostics receiver). 하지만 Korail/SmartAlimi push flow에서 직접 worker enqueue path는 확인되지 않았다.
- exported component caveat: `MessageManager`는 exported/no-permission AIDL binder이고, `RestartReceiver`와 `FCMListenerServiceHandler`도 exported다. `PushBroadcastReceiver`는 exported지만 signature permission으로 보호된다.
- notification channel badge 결론은 “시도/선언”으로만 둔다. receiver는 normal false/emergency true를 시도하지만, `KTApplication`이 같은 channel을 `setShowBadge` 없이 먼저 만들 수 있어 최종 badge 보장은 런타임 상태에 의존한다.
- `SpecialRoomUpgradeActivity`는 activity와 `msg_vo` extra는 확인되지만 push routing에서 정적 entrypoint가 확인되지 않았다.
- `CashRfnDao.f28877I`는 unknown이 아니라 `"I"`다.
- `PushHistoryActivity.P0()`는 type `22`를 mapping하지만, list click normal route는 `25`, `21`, `35`, `36` 중심이고 time-change/URL path가 별도로 override한다.
