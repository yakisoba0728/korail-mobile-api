# Common/Station/Crypto API 딥다이브

## 분석 기준

- 정적 로컬 분석만 수행했다. 네트워크 호출, 서버 응답 재현, 샘플 응답 생성은 하지 않았다.
- endpoint, request parameter, response field는 JADX 디컴파일 Java 클래스의 Retrofit annotation, DAO request/response 내부 클래스, getter/setter, 호출처를 기준으로 정리했다.
- `BaseResponse` 공통 필드 `h_msg_cd`, `h_msg_txt`, `strResult`는 모든 `BaseResponse` 상속 응답에서 공통적으로 역직렬화될 수 있다.
- `BaseRequest` 기본값은 생성자에서 자동 설정된다.
  - `Device`: `AD`
  - `Version`: `250601003`
  - `Key`: `korail1234567890`

## 주요 소스 경로

| 영역 | 소스 |
|---|---|
| Retrofit service | `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java` |
| 공통 요청/응답 base | `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`, `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java` |
| 공통 코드 DAO | `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonCodeDao.java` |
| 역 데이터/역 버전 DAO | `analysis/jadx/sources/com/korail/talk/network/dao/common/StationDataDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/StationInfoDao.java` |
| MAAS 역/메뉴 DAO | `analysis/jadx/sources/com/korail/talk/network/dao/common/MaasStationListDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/MaasMenuListDao.java` |
| 암호화 helper API DAO | `analysis/jadx/sources/com/korail/talk/network/dao/common/EncryptDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/DecryptDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/KBPayEncryptDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/SeedEncryptDao.java` |
| cookie UUID/QR 위치 DAO | `analysis/jadx/sources/com/korail/talk/network/dao/common/CookieDao.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/authQRLocationDao.java` |
| 로컬 암호화 유틸 | `analysis/jadx/sources/S4/C0812l.java`, `analysis/jadx/sources/F4/a.java` |
| 역 DB 모델/cache | `analysis/jadx/sources/com/korail/talk/database/model/StationData.java`, `analysis/jadx/sources/J4/b.java`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java` |

## Endpoint 요약

| 기능 | Method | Path | DAO response class | 주요 호출처 |
|---|---:|---|---|---|
| QR 위치 인증 | POST | `/classes/com.korail.mobile.qr.bchTripSv.do` | `authQRLocationDao.QRLocationResponse` | `TripQrAuthActivity` |
| cookie UUID | GET | `/ebizcross/getUUID.do` | `CookieDao.RsvWaitResponse` | SRT 직통/환승 조회 화면 |
| 공통 코드 | POST | `/classes/com.korail.mobile.common.code.do` | `CommonCodeDao.CommonCodeResponse` | `IntroActivity`, 약관/정기권/리무진 화면 |
| 서버 복호화 helper | POST | `/classes/com.korail.mobile.common.decrypt.do` | `DecryptDao.DecryptResponse` | `RailPlusActivity` |
| 서버 암호화 helper | POST | `/classes/com.korail.mobile.common.encrypt.do` | `EncryptDao.EncryptResponse` | `DataActivity` |
| KBPay 암호화 helper | POST | `/classes/com.korail.mobile.common.encrypt.do` | `KBPayEncryptDao.KBpayEncryptResponse` | 결제 base `B6/AbstractC1269e.java` |
| MAAS 메뉴 | POST | `/classes/com.korail.mobile.copt.gdMenuLt.do` | `MaasMenuListDao.MaasMenuListResponse` | 메인 예약, 부가서비스, MAAS 추가예약 |
| MAAS 역 목록 | POST | `/ebizmaas/EbizMaasStationList.do` | `StationDataDao.StationDataResponse` | `MaasSelectStationActivity` |
| 전체 역 데이터 | GET | `/classes/com.korail.mobile.common.stationdata` | `StationDataDao.StationDataResponse` | `IntroActivity` |
| 역 데이터 버전/개수 | GET | `/classes/com.korail.mobile.common.stationinfo` | `StationInfoDao.StationInfoResponse` | `IntroActivity` |
| 신한/SEED 암호화 helper | POST | `/classes/com.korail.mobile.shinhan.Encrypt.do` | `SeedEncryptDao.SeedEncryptResponse` | 결제 base `B6/AbstractC1269e.java` |

## 공통 코드 API

### `POST /classes/com.korail.mobile.common.code.do`

- service: `CommonService.getCommonCode(...)`
- DAO: `CommonCodeDao`
- request class: `CommonCodeDao.CommonCodeRequest extends BaseRequest`
- request parameters:
  - `Device`: `BaseRequest.getDevice()`, 기본 `AD`
  - `Version`: `BaseRequest.getVersion()`, 기본 `250601003`
  - `Key`: `BaseRequest.getKey()`, 기본 `korail1234567890`
  - `code`: `List<String> codeList`
  - `deviceWidth`: `int deviceWidth`
  - `deviceHeight`: `int deviceHeight`
  - `departDate`: `String departDate`
  - `arrivalDate`: `String arrivalDate`
  - `holidayYn`: `String holidayYn`
  - `OSVersion`: `int OSVersion`
- `CommonCodeRequest`에 `easyPayType` 필드/getter/setter가 있지만 Retrofit method parameter에는 포함되지 않는다.

### 요청 코드 값

`CommonCodeDao`에 정의된 코드 상수:

| 상수 | 값 |
|---|---|
| `ANYID` | `app.login.anyid` |
| `ATHN` | `app.hndy.athn` |
| `BUY_NOW` | `app.menu.buynow` |
| `DATA` | `app.var.data` |
| `DEVICE_OREO` | `app.device.oreo` |
| `EASY_PAY` | `app.event.easyPay` |
| `HOLIDAY_POPUP` | `app.holiday.popup` |
| `IMAGE_DOWN_LOAD_DATA` | `app.display.image` |
| `IS_NAVER_SHOW` | `app.easyLogin.isShow` |
| `KORAIL_BOSS` | `app.korail.boss` |
| `LIMOUSINE_MAIN_MSG` | `app.limousine.mainMsg` |
| `LIMOUSINE_MSG` | `app.limousine.airportBusMsg` |
| `LOGIN` | `app.login.cphd` |
| `LOST_ARTICLE` | `app.menu.lost112` |
| `MAAS_TEST` | `app.MaaS.test` |
| `MAIN_POPUP` | `app.main.popup` |
| `MENU_BIZ` | `app.menu.biz` |
| `MENU_RAILPOINT` | `app.menu.railpoint` |
| `PERIOD_COMMUTATION_DATA` | `app.periodCommutation.data` |
| `POINT` | `app.event.point` |
| `REPORT` | `app.illegal.report` |
| `STATION_CD` | `app.limousine.stationCd` |
| `STATION_NM` | `app.limousine.stationNm` |
| `STBK_ACCEPT` | `app.stbk.accept` |
| `VIEW_VISIBILITY` | `app.view.visibility` |

`IntroActivity.r0()`는 초기 구동 시 `IMAGE_DOWN_LOAD_DATA`, `MENU_RAILPOINT`, `MAIN_POPUP`, `IS_NAVER_SHOW`, `KORAIL_BOSS`, `BUY_NOW`, `LOST_ARTICLE`, `EASY_PAY`, `ATHN`, `VIEW_VISIBILITY`, `MENU_BIZ`, `POINT`, `DATA`, `LOGIN`, `REPORT`, `HOLIDAY_POPUP`, `MAAS_TEST`, `LIMOUSINE_MAIN_MSG`를 요청한다. Android SDK가 26 미만이면 `DEVICE_OREO`도 추가한다.

### 추론 응답 필드/classes

응답 class는 `CommonCodeDao.CommonCodeResponse extends BaseResponse`이며, Gson annotation `@S3.c(...)`로 서버 key와 매핑된다.

| 응답 key | Java field/class | 확인된 하위 필드 |
|---|---|---|
| `app.stbk.accept` | `List<Accept> accepts` | `isCheck`, `linkUrl`, `message` |
| `app.hndy.athn` | `Athn athn` | `athnBtn`, `cncBtn`, `isApply`, `message`, `title` |
| `app.menu.buynow` | `BuyNow buyNow` | `isApply`, `menuTitle` |
| `app.var.data` | `Data data` | `anyid`, `anyidUrl`, `anyidhm`, `autoRefresh`, `csChatBot`, `isMacroEnable`, `isSrHistoryEnable`, `knDelivery`, `knParkingLot`, `lotteglogisURL`, `newTabUI1`, `newTabUI2`, `srHistoryUrl`, `suspendMode` |
| `app.device.oreo` | `DeviceOSPopUp deviceOreo` | `isDeploymentStop`, `message`, `title` |
| `app.event.easyPay` | `EasyPay easyPay` | `tab`, `List<EasyPayData> list` |
| `app.event.easyPay` list item | `EasyPayData` | `displayType`, `isEnable`, `isNeedLogin`, `linkTitle`, `linkType`, `linkUrl`, `payTitle`, `payType` |
| `app.holiday.popup` | `HolidayPopup holidayPopup` | `popup`, `popupAlt`, `popupImg`, `popupSchema`, `popupUrl`, `subUrl` |
| `app.display.image` | `ImageDownLoadData imageDownLoadData` | `applyDate`, `fileSize`, `isApply`, `subUrl`, `textColor`, `url` |
| `app.easyLogin.isShow` | `EasyLogin isEasyLoginShow` | `isGoogleShow`, `isKakaoShow`, `isNaverShow`, `isOnepassShow` |
| `app.korail.boss` | `KorailBoss korailBoss` | `name`, `terms` |
| `app.limousine.airportBusMsg` | `String limousine` | 문자열 |
| `app.limousine.mainMsg` | `String limousineMainMsg` | 문자열 |
| `app.login.cphd` | `Login login` | `idx`, `key`, `pwdAESCphd` |
| `app.menu.lost112` | `LostArticle lostArticle` | `isApply`, `linkUrl`, `menuTitle` |
| `app.MaaS.test` | `String maasTest` | 문자열 |
| `app.main.popup` | `MainPopup mainPopup` | `buttonType`, `checkType`, `clsBtn`, `imageUrl`, `isExternalBrowser`, `isShow`, `linkTitle`, `linkUrl`, `message`, `noticeId`, `size`, `title`, `voice` |
| `app.menu.biz` | `MenuBiz menuBiz` | `isApply`, `linkUrl`, `title` |
| `app.menu.railpoint` | `MenuRailPoint menuRailPoint` | `appScheme`, `installUrl`, `isApply`, `menuTitle` |
| `app.periodCommutation.data` | `PeriodCommutationData periodCommutationData` | `periodCd`, `periodNm` |
| `app.event.point` | `Point pointData` | `List<PointData> list` |
| `app.event.point` list item | `PointData` | `isEnable`, `isNeedLogin`, `linkTitle`, `linkType`, `linkUrl`, `pointTitle`, `pointType` |
| `app.illegal.report` | `Report report` | `enable`, `title`, `url` |
| `app.limousine.stationCd` | `List<String> stationCd` | 문자열 목록 |
| `app.limousine.stationNm` | `List<String> stationNm` | 문자열 목록 |
| `app.view.visibility` | `ViewVisibility viewVisibility` | `acpnMlgLead`, `acpnMlgSave`, `centralInlandMap`, `checkIn`, `crmNty`, `dlfeCashRfn`, `giftTicket`, `hearingImpaired`, `hearingImpairedExps`, `mbSced`, `mbilPbepAthn`, `wheelchair` |

### 소비처

- `IntroActivity`:
  - 초기 구동 service check 후 공통 코드를 요청한다.
  - 응답의 대부분을 `S4.H` preference에 JSON 문자열로 저장한다: `MENU_RAIL_POINT`, `EASY_LOGIN`, `KORAIL_BOSS`, `LOST_ARTICLE`, `EASY_PAY_OPTION`, `HOLIDAY_POPUP_DATA`, `ATHN`, `VIEW_VISIBILITY`, `MENU_BIZ`, `POINT_PAY_OPTION`, `VAR_DATA`, `LOGIN_DATA`, `REPORT_DATA`, `OREO_DATA`, `KEY_LIMOUSINE_MAIN_MSG`.
  - `BuyNow.isApply`는 `CONVENIENCE_SETTING_VISIBLE` boolean으로 저장한다.
  - `MainPopup`은 `MainPopupData` DB row로 변환해 `J4.b`에 저장한다.
  - `Data.autoRefresh`, `Data.isMacroEnable`은 `I4.a.IS_AUTO_REFRESH_ACTIVE`, `I4.a.IS_MACRO_ACTIVE`에 반영한다.
- `BaseActivity.L()`과 `S4.C0812l.getAmountEncrypt()`:
  - `LOGIN_DATA`의 `CommonCodeDao.Login` 값을 읽고 `pwdAESCphd == "Y"`이면 `login.key`로 AES/CBC 암호화 후 Base64를 한 번 더 적용한다.
- 추가 호출처:
  - `StbkAcceptTermsActivity`: `STBK_ACCEPT` 약관.
  - `PeriodCommutationBookingActivity`: `PERIOD_COMMUTATION_DATA`.
  - `LimousineActivity`, `RenewalLimousineActivity`: 리무진 메시지/역 코드/역명.

## 역 데이터 API

### `GET /classes/com.korail.mobile.common.stationinfo`

- service: `CommonService.getStationInfo(@Query("Device"))`
- DAO: `StationInfoDao`
- request parameters:
  - query `Device`: `new BaseRequest().getDevice()`, 기본 `AD`
- response class: `StationInfoDao.StationInfoResponse extends BaseResponse`
- 추론 응답 필드:
  - `count`: `int`
  - `map_version`: `String`
- 소비처:
  - `IntroActivity.u0()`에서 호출한다.
  - `IntroActivity.x0()`는 `map_version`을 정수로 파싱하고, local preference `MAP_VERSION`, 로컬 DB 역 목록 크기와 비교한다.
  - 조건 `local MAP_VERSION != 0 && count == local station size && remote map_version <= local MAP_VERSION`이면 역 데이터 다운로드를 생략한다.
  - 갱신 필요 시 `MAP_VERSION`을 저장하고 `/stationdata`를 호출한다.

### `GET /classes/com.korail.mobile.common.stationdata`

- service: `CommonService.getStationData()`
- DAO: `StationDataDao`
- request parameters: 없음
- response class: `StationDataDao.StationDataResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - `StationDataResponse.stns`: `StationDataDao.STNs`
  - `STNs.stn`: `List<StationDataDao.STN>`
  - `STN` fields:
    - `group`
    - `latitude`
    - `longitude`
    - `major`
    - `popupLinkTitle`
    - `popupLinkUrl`
    - `popupMessage`
    - `popupType`
    - `stn_cd`
    - `stn_nm`
- 소비처:
  - `IntroActivity.t0()`에서 호출한다.
  - `IntroActivity.d` AsyncTask가 응답 `STN` 목록을 `com.korail.talk.database.model.StationData`로 변환한다.
  - 변환 매핑:
    - `STN.stn_cd` -> `StationData.stnCd`
    - `STN.stn_nm` -> `StationData.stnNm`
    - `STN.longitude` -> `StationData.longitude`
    - `STN.latitude` -> `StationData.latitude`
    - `STN.group` -> `StationData.group`
    - `STN.major` -> `StationData.major`
    - `STN.popupType` -> `StationData.popupType`
    - `STN.popupMessage` -> `StationData.popupMessage`
    - `STN.popupLinkTitle` -> `StationData.popupLinkTitle`
    - `STN.popupLinkUrl` -> `StationData.popupLinkUrl`
  - 저장 전 `J4.b.deleteAllStationList()`를 호출하고, 각 역을 `J4.b.insertStationList()`로 저장한다.
  - 저장된 `StationData`는 `J4.b.getStationDataByName()`, `getStationDataByCode()`, `getAllStationList()`를 통해 예약 메인, 좌석 조회, 역 검색, 근처 역 계산 등에 넓게 사용된다.
- local DB model:
  - `analysis/jadx/sources/com/korail/talk/database/model/StationData.java`
  - ORMLite `@DatabaseField` 필드: `id`, `stnCd`, `stnNm`, `latitude`, `longitude`, `group`, `major`, `popupType`, `popupMessage`, `popupLinkTitle`, `popupLinkUrl`, `doNotLookADay`, `doNotLookAgain`.

### `POST /ebizmaas/EbizMaasStationList.do`

- service: `CommonService.getMaasStationList(@Field("addSrvDvCd"))`
- DAO wrapper: `MaasStationListDao`
- request class: `MaasStationListDao.MaasStationListRequest extends BaseRequest`
- request parameters:
  - `addSrvDvCd`: `String`
  - `Device`, `Version`, `Key`는 `MaasStationListRequest`에 존재하지만 Retrofit method에는 전달되지 않는다.
- response class:
  - `CommonService` method return type은 `StationDataDao.StationDataResponse`이다.
  - 즉 응답 구조는 `/stationdata`와 동일하게 `stns.stn[]` 및 `STN` 필드를 사용한다.
- 소비처:
  - `MaasSelectStationActivity.t0(String)`이 intent extra에서 받은 MAAS 서비스 구분 코드를 `addSrvDvCd`로 설정해 호출한다.
  - `MaasSelectStationActivity.onReceive()`는 `StationDataResponse.getStns().getStn()`을 `MaasStationSearch.setStationList()`에 전달하고 `refreshList()`를 호출한다.
  - `MaasStationSearch`는 `StationDataDao.STN`/`STNSetter`를 `DistanceStationData`로 변환해 MAAS 역 검색 UI에 사용한다.

## MAAS 메뉴 API

### `POST /classes/com.korail.mobile.copt.gdMenuLt.do`

- service: `CommonService.getMaasMenuList(...)`
- DAO: `MaasMenuListDao`
- request class: `MaasMenuListDao.MaasMenuRequest extends BaseRequest`
- request parameters:
  - `Device`: `BaseRequest.getDevice()`, 기본 `AD`
  - `Version`: `BaseRequest.getVersion()`, 기본 `250601003`
  - `pnrNo`: `String`
  - `tkRetNo`: `List<String>` / `ArrayList<String>`
  - `addSrvReqNo`: `String`
  - `Key`는 request base에는 있으나 Retrofit method parameter에는 없다.
- request variant:
  - `MaasMenuListDao.executeDao()`에서 request가 `MaasMenuRequest`가 아니면 `BaseRequest`의 `Device`, `Version`만 전달하고 `pnrNo`, `tkRetNo`, `addSrvReqNo`는 `null`로 호출한다.
- response class: `MaasMenuListDao.MaasMenuListResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - top-level:
    - `menuList`: `List<MaasMenuListDao.Menu>`
    - `dElevatorUrl`
    - `dLeadNaviUrl`
    - `dParkingLotUrl`
    - `aElevatorUrl`
    - `aBisInfoUrl`
    - `aParkingLotUrl`
    - `aBggTrsfRbtUrl`
  - `Menu` fields:
    - `active`
    - `addSrvDvCd`
    - `appData`
    - `iconOff`
    - `iconOn`
    - `info`
    - `login`
    - `name`
    - `poppImg`
    - `type`
    - `url`
- 소비처:
  - `MainBookingActivity.S0()`:
    - `new BaseRequest()`만 설정해 메뉴 목록을 가져온다.
    - `onReceive()`에서 `menuList`를 grid adapter에 설정한다.
  - `AdditionalServiceActivity.t0()`:
    - `pnrNo`와 단일 `tkRetNo` 목록을 설정해 승차권 기반 부가서비스 메뉴를 조회한다.
    - `onReceive()`에서 `menuList`를 표시하고, 출발/도착 관련 URL들을 버튼 tag로 저장한다.
  - `MaasAddReservationActivity.u0()`:
    - `addSrvReqNo`를 설정해 MAAS 추가예약 메뉴를 조회한다.
    - `onReceive()`에서 `menuList`를 grid adapter에 설정한다.

## 암호화/복호화 서버 helper API

### `POST /classes/com.korail.mobile.common.encrypt.do` - 일반 encrypt

- service: `CommonService.getEncrypt(...)`
- DAO: `EncryptDao`
- request class: `EncryptDao.EncryptRequest extends BaseRequest`
- request parameters:
  - `Device`: 기본 `AD`
  - `Version`: 기본 `250601003`
  - `Key`: 기본 `korail1234567890`
  - `type`: `String`
  - `values`: `List<String>`
- response class: `EncryptDao.EncryptResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - `encValueList`: `List<EncryptDao.EncryptValueList>`
  - `EncryptValueList.encValue`: `String`
- 소비처:
  - `DataActivity.g0()`:
    - 로컬 저장 login id/password를 `F4.a.decryptAES()`로 복호화한다.
    - JSON 객체에 `loginType`, `loginId`, `loginPw`, `isAutoLogin`, `isSaveMemberNumber`를 넣는다.
    - JSON 문자열을 `F4.a.encryptBase64()`로 Base64 처리한다.
    - `EncryptRequest.type = "1"`, `values = [base64Json]`로 서버 helper를 호출한다.
  - `DataActivity.onReceive()`:
    - 응답 `encValueList[0].encValue`를 app scheme `data_login_scheme`에 넣어 외부 intent로 전달한다.
- 서버 암호화 알고리즘:
  - 로컬 코드에는 `/common.encrypt.do`의 서버 내부 알고리즘, key, IV가 없다.
  - 앱이 보내는 것은 `type`과 `values`이며, 암호문은 서버 응답 `encValue`로만 소비된다.

### `POST /classes/com.korail.mobile.common.decrypt.do`

- service: `CommonService.getDecrypt(...)`
- DAO: `DecryptDao`
- request class: `DecryptDao.DecryptRequest extends BaseRequest`
- request parameters:
  - `Device`: 기본 `AD`
  - `Version`: 기본 `250601003`
  - `Key`: 기본 `korail1234567890`
  - `type`: `String`
  - `values`: `List<String>`
- `DecryptRequest` 추가 local-only fields:
  - `easyPayType`
  - `mAutoChargeRequestType`
  - 이 두 필드는 Retrofit parameter로 전달되지 않고 호출처에서 후속 처리를 위해 request 객체에 보존된다.
- response class: `DecryptDao.DecryptResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - `decValueList`: `List<DecryptDao.DecryptValueList>`
  - `DecryptValueList.decValue`: `String`
- 소비처:
  - `RailPlusActivity.v0()`:
    - `type = "1"`, `values = [CARD_NO]`, `mAutoChargeRequestType`를 설정해 호출한다.
  - `RailPlusActivity.onReceive()`:
    - `decValueList[0].decValue`를 `AutoChargeRequest.prepCrdNo`로 넣고 자동충전 조회/신청/해지 API를 호출한다.
- 서버 복호화 알고리즘:
  - 로컬 코드에는 `/common.decrypt.do`의 서버 내부 알고리즘, key, IV가 없다.

### `POST /classes/com.korail.mobile.common.encrypt.do` - KBPay encrypt

- service: `CommonService.getKBPayEncrypt(...)`
- DAO: `KBPayEncryptDao`
- request class: `KBPayEncryptDao.KBpayEncryptRequest extends BaseRequest`
- request parameters:
  - `Device`: 기본 `AD`
  - `Version`: 기본 `250601003`
  - `Key`: 기본 `korail1234567890`
  - `type`: `String`
  - `values`: `List<String>`
- response class: `KBPayEncryptDao.KBpayEncryptResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - `BIZ_NUM`
  - `CHANNEL_ID`
  - `PURCHASE_PRODUCT_INFO`
  - `REQ_DATE_TIME`
  - `SELLER_NAME`
  - `SELLER_NUM`
  - `encValueList`: `List<EncryptDao.EncryptValueList>`
- 소비처:
  - 결제 base `B6/AbstractC1269e.e1(String...)`:
    - `type = "K"`로 설정하고 전달 인자들을 `values` 목록으로 보낸다.
  - `B6/AbstractC1269e.onReceive()`:
    - 응답 top-level KBPay merchant metadata와 `encValueList[0]`, `encValueList[1]`을 `payment_kb_pay_scheme` 문자열에 결합한다.
    - 결합한 scheme을 URL encode한 뒤 패키지 `com.kbcard.cxh.appcard`로 실행한다.
- 서버 암호화 알고리즘:
  - local APK에는 KBPay용 서버 helper 내부 알고리즘, key, IV가 없다.
  - 일반 `EncryptDao`와 같은 endpoint path를 사용하지만 return class가 KBPay 전용 metadata를 더 포함한다.

### `POST /classes/com.korail.mobile.shinhan.Encrypt.do`

- service: `CommonService.seedEncrypt(...)`
- DAO: `SeedEncryptDao`
- request class: `SeedEncryptDao.SeedEncryptRequest extends BaseRequest`
- request parameters:
  - `Device`: 기본 `AD`
  - `Version`: 기본 `250601003`
  - `Key`: 기본 `korail1234567890`
  - `value`: `List<String>`
- response class: `SeedEncryptDao.SeedEncryptResponse extends BaseResponse`
- 추론 응답 필드/classes:
  - `encValueList`: `List<SeedEncryptDao.EncValueList>`
  - `EncValueList.encValue`: `String`
- 소비처:
  - 결제 base `B6/AbstractC1269e.m1(String...)`:
    - 전달 인자들을 `value` 목록으로 넣어 호출한다.
  - `B6/AbstractC1269e.onReceive()`:
    - 응답 `encValueList[0]`, `encValueList[1]`을 `payment_shinhanfan_scheme`에 넣고 패키지 `com.shcard.smartpay`를 실행한다.
- 서버 암호화 알고리즘:
  - class 이름과 path는 `shinhan.Encrypt`, DAO 이름은 `SeedEncryptDao`지만, 로컬 코드에 SEED 알고리즘 구현이나 key/IV는 없다.
  - 앱은 서버가 반환한 `encValue`만 scheme payload로 사용한다.

## 로컬 암호화 유틸

### `S4.C0812l`

소스: `analysis/jadx/sources/S4/C0812l.java`

#### `encryptAES(String key, String plaintext)`

- algorithm/transformation: `AES/CBC/PKCS5Padding`
- key:
  - `new SecretKeySpec(key.getBytes(), "AES")`
  - 호출자가 넘긴 문자열 전체 byte를 AES key로 사용한다.
  - 코드상 검증은 없으나 AES key 길이 요구상 실제 호출 key는 16/24/32 bytes여야 한다.
- IV derivation:
  - `key.substring(0, 16)`의 bytes를 `IvParameterSpec`으로 사용한다.
- plaintext encoding:
  - `plaintext.getBytes("UTF-8")`
- output:
  - Android `Base64.encode(..., 0)` 결과를 UTF-8 문자열로 반환한다.
  - flag `0`은 Android `Base64.DEFAULT` 동작이다.
- decrypt 함수는 이 class에 없다.

#### `getSid()`

- `encryptAES("2485dd54d9deaa36", "AD" + new Date().getTime())`
- key: literal `2485dd54d9deaa36`
- IV: key 앞 16자이므로 동일하게 `2485dd54d9deaa36`
- plaintext prefix: `BaseRequest.ANDROID`, 즉 `AD`
- 소비처:
  - 기존 분석에서 열차 조회류 request의 `Sid` 생성에 쓰이는 것으로 확인된다.

#### `getAmountEncrypt(CommonCodeDao.Login login, String value)`

- `login.getPwdAESCphd() == "Y"`:
  - `encryptAES(login.getKey(), value)` 실행
  - 그 결과 문자열을 `F4.a.encryptBase64()`로 다시 Base64 처리한다.
- 그 외:
  - 평문 `value`를 `F4.a.encryptBase64()`만 적용한다.
- 동일한 로직이 `BaseActivity.L(String)`에도 구현되어 로그인 password 전송 전 처리에 사용된다.

### `F4.a`

소스: `analysis/jadx/sources/F4/a.java`

#### key derivation

- private `a(Context)`:
  - `Settings.Secure.getString(context.getContentResolver(), "android_id")` 값을 읽는다.
  - `UUID.nameUUIDFromBytes(android_id.getBytes("UTF-8")).toString()`을 만든다.
  - 이 UUID 문자열의 UTF-8 bytes를 `Arrays.copyOf(..., 16)`으로 16 bytes로 자른다.
- 결과를 AES key로 사용한다.
- IV는 없다. ECB mode다.

#### `encryptAES(Context, String)`

- algorithm/transformation: `AES/ECB/PKCS5Padding`
- key: 위 key derivation 결과 16 bytes
- plaintext encoding: `UTF8`
- output: `Base64.encode(ciphertext, 0)` 결과를 UTF-8 문자열로 반환한다.

#### `decryptAES(Context, String)`

- algorithm/transformation: `AES/ECB/PKCS5PADDING`
- key: 위 key derivation 결과 16 bytes
- input: Base64 문자열을 `Base64.decode(str.getBytes("UTF-8"), 0)`로 decode
- output: UTF-8 평문 문자열

#### `encryptBase64(String)` / `decryptBase64(String)`

- `encryptBase64`: `Base64.encodeToString(str.getBytes("UTF-8"), 2)`
- `decryptBase64`: `Base64.decode(str, 2)` 후 문자열 생성
- flag `2`는 Android `Base64.NO_WRAP`이다.

#### 주요 소비처

- 로그인/자동 로그인 저장값:
  - `BaseActivity.G()`가 `KEY_LOGIN_ID`, `KEY_LOGIN_PW`를 `F4.a.decryptAES()`로 복호화해 로그인 request에 사용한다.
  - `DataActivity.g0()`도 동일 저장값을 복호화한 후 서버 encrypt helper로 전달한다.
- 승차권/민감 local cache:
  - `TicketListActivity`가 승차권 상세/목록 JSON을 `F4.a.encryptAES()`로 저장하고 복호화 helper에서 다시 읽는다.
- 설정/카드/보훈번호:
  - `favoriteCards` 설정 화면이 카드 별칭, 카드번호, 유효기간, 카드유형, 사업자번호 등을 `F4.a.encryptAES()`로 저장하고 `decryptAES()`로 표시한다.
  - `VeteransNoSettingActivity`, `NationalMeritPersonDiscount`가 보훈번호를 로컬 AES로 저장/조회한다.
- Guardian Relief SMS:
  - `GuardianReliefSmsActivity`가 전화번호를 `F4.a.encryptAES()`로 저장한다.

### 기타 관련 local hash utility

- `S4.C0813m`에는 파일 cache 임시명 생성을 위한 MD5 helper가 있다.
- `getMD5File()`에서 파일명을 `MD5(originalName) + ".tmp"`로 바꾸는 용도이며, API request 암호화/복호화와 직접 연결된 증거는 없다.

## Cookie UUID API

### `GET /ebizcross/getUUID.do`

- service: `CommonService.ckValue()`
- DAO: `CookieDao`
- request parameters: 없음
- response class: `CookieDao.RsvWaitResponse extends BaseResponse`
- 추론 응답 필드:
  - `mutMrkVrfCd`: `String`
- DAO local state:
  - `CookieDao.isWeb`: boolean, 기본 `false`
  - `setWeb(true)`로 호출처가 web/app 분기를 표시한다. 서버 parameter가 아니다.
- 소비처:
  - `DirectInquiryActivity`:
    - 사용자가 SRT web/app 이동을 선택할 때 호출한다.
    - `isWeb == true`이면 `mutMrkVrfCd`를 web 경로로 넘긴다.
    - app 경로이면 `C1262b.getInstance().setMutMrkVrfCd(mutMrkVrfCd)`로 저장한 뒤 SRT app intent 흐름을 진행한다.
  - `TransferInquiryActivity`:
    - `mutMrkVrfCd`를 `C1262b` singleton에 저장하고 SRT 환승 흐름에 사용한다.
- 이름상 UUID endpoint지만 로컬 응답 field명은 `mutMrkVrfCd`로 확인된다. 실제 cookie/header 설정 여부나 값 형식은 로컬 코드만으로 확정할 수 없다.

## QR 위치 인증 API

### `POST /classes/com.korail.mobile.qr.bchTripSv.do`

- service: `CommonService.authQRLocation(...)`
- DAO: `authQRLocationDao`
- request class: `authQRLocationDao.QRLocationRequest extends BaseRequest`
- request parameters:
  - `Device`: 기본 `AD`
  - `Version`: 기본 `250601003`
  - `qrcode`: `String`
  - `latitude`: `String`
  - `longitude`: `String`
  - `Key`는 request base에는 있으나 Retrofit method parameter에는 없다.
- response class: `authQRLocationDao.QRLocationResponse extends BaseResponse`
- 추론 응답 필드:
  - `jobScsFlg`: `String`
  - 공통 `h_msg_txt`: UI dialog에 표시된다.
- 소비처:
  - `TripQrAuthActivity`:
    - location manager에서 마지막 위치를 읽어 위도/경도를 문자열로 넣는다. 위치가 없으면 빈 문자열을 보낸다.
    - QR 값은 activity field `f29593j`에서 request `qrcode`로 들어간다.
    - 응답 수신 시 `gethMsgTxt()`를 dialog content로 보여준다.

## 확인 불가/주의 사항

- 서버 helper endpoint(`/common.encrypt.do`, `/common.decrypt.do`, `/shinhan.Encrypt.do`)의 실제 암호화 알고리즘, 서버 key, 서버 IV는 APK 로컬 코드에 없다.
- `StationDataResponse`, `CommonCodeResponse` 등은 Java field와 getter 기준의 추론 schema다. 실제 서버가 항상 모든 필드를 내려주는지는 이 분석만으로 확정할 수 없다.
- `BaseResponse`의 `h_msg_cd`, `h_msg_txt`, `strResult`는 상속 구조상 공통 필드로 존재하지만, endpoint별 사용 여부는 호출처마다 다르다.
- `CommonService.getMaasStationList()`는 `StationDataDao.StationDataResponse`를 반환하므로 MAAS station 전용 response class가 따로 보이지 않는다. `MaasStationListDao`는 request wrapper 역할만 한다.
