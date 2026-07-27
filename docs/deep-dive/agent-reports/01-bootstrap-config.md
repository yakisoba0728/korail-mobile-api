# 01. 부트스트랩/설정/매니페스트 분석

## 분석 범위와 원칙

- 사용한 로컬 아티팩트: `analysis/jadx/sources`, `analysis/apktool`, `analysis/raw`
- 라이브 KORAIL/SRT 서비스 호출은 수행하지 않았다.
- 응답/요청 데이터는 로컬 코드의 Retrofit annotation, DTO 필드, 리소스 문자열, 매니페스트 메타데이터에서 확인 가능한 범위로만 기술했다.
- JADX 난독화/디컴파일 결과라 일부 클래스명은 원본과 다를 수 있다. 예: `G4.a`, `K4.g`, `S4.z`.

### 벤더 키 표기

이 문서는 KORAIL 앱이 자기 것으로 들고 있는 **제3자 SDK 자격증명**(Google/Firebase API
key·app id, Kakao app key, AdMob app id)을 **필드 이름과 위치로만** 기록한다.
값 자체는 이 클라이언트가 쓰지도, 필요로 하지도 않으므로 저장소 본문에서도 git 히스토리에서도
제거했고, 그 자리에는 `<KORAIL-APP-…-REDACTED>` 자리표시자만 남는다. 즉 자리표시자는
"여기에 그 이름의 값이 있었다"는 뜻이고, 실제 값은 APK 사본에서만 읽을 수 있다.
예외가 하나 있다: `gcm_defaultSenderId`(=`303574505999`)는 자격증명이 아니라 Firebase
**프로젝트 번호**라서 의도적으로 그대로 둔다. 빠뜨린 것이 아니다.

## APK/빌드 메타데이터

### APK 식별자와 SDK

- `analysis/apktool/apktool.yml`
  - `apkFileName`: `korail.apk`
  - `minSdkVersion`: `24`
  - `targetSdkVersion`: `35`
  - `versionCode`: `60500002`
  - `versionName`: `6.5.0`
- `analysis/apktool/AndroidManifest.xml`
  - `package`: `com.korail.talk`
  - `compileSdkVersion`: `35`
  - `compileSdkVersionCodename`: `15`
  - `platformBuildVersionCode`: `35`
  - `platformBuildVersionName`: `15`
  - Play 배포 스탬프 메타데이터:
    - `com.android.stamp.source=https://play.google.com/store`
    - `com.android.stamp.type=STAMP_TYPE_DISTRIBUTION_APK`
    - `com.android.vending.splits.required=true`
    - `com.android.vending.derived.apk.id=3`
- `analysis/raw/stamp-cert-sha256`, `analysis/apktool/original/stamp-cert-sha256`
  - APK 스탬프 인증서 해시가 별도 파일로 포함되어 있다. 본 보고서에서는 값 해석/검증은 수행하지 않았다.

### 앱 BuildConfig 상수

- 소스: `analysis/jadx/sources/G4/a.java`
- 클래스: `G4.a`
- 주요 상수:
  - `APPLICATION_ID = "com.korail.talk"`
  - `BUILD_TYPE = "release"`
  - `DEBUG = false`
  - `FLAVOR = "product"`
  - `VERSION_CODE = 60500002`
  - `VERSION_NAME = "6.5.0"`
  - `API_VERSION = "250601003"`
  - `CONNECT_SERVER = "3"`
  - `IS_DEBUG_LOG = false`
  - `IS_CALL_CREW_TEST = false`
  - `IS_LIMOUSINE_TEST = false`
  - `IS_OLD_MAIN_ACTIVITY = false`
  - `IS_ONE_STORE = false`
  - `IS_TICKET_DIM = true`
- 런타임 파급:
  - `analysis/jadx/sources/I4/a.java`가 `G4.a`의 boolean 값을 전역 플래그로 복사한다.
  - `I4.a.IS_DEBUG_LOG=false`이므로 Retrofit 로그 레벨은 기본적으로 `NONE`이다.
  - `I4.a.IS_MACRO_ACTIVE=false`로 시작하지만, `IntroActivity`의 공통코드 응답 처리에서 서버 제공값 `isMacroEnable`이 `"Y"`이면 true로 변경된다.

## AndroidManifest 핵심 설정

### Application

- 소스: `analysis/apktool/AndroidManifest.xml`
- `<application>` 핵심 속성:
  - `android:name="com.korail.talk.application.KTApplication"`
  - `android:allowBackup="false"`
  - `android:largeHeap="true"`
  - `android:hardwareAccelerated="true"`
  - `android:networkSecurityConfig="@xml/network_security_config"`
  - `android:extractNativeLibs="false"`
  - `android:appComponentFactory="androidx.core.app.CoreComponentFactory"`
  - `android:label="@string/app_name"`이며 `analysis/apktool/res/values/strings.xml`의 `app_name`은 `코레일톡`
- 런타임 의미:
  - 프로세스 시작 시 `KTApplication.onCreate()`가 앱 전역 초기화를 수행한다.
  - 네트워크 보안 정책은 앱 전체의 플랫폼 cleartext 허용 대상에 영향을 준다.
  - `allowBackup=false`로 Android 백업 대상에서 제외된다.

### 권한

- 소스: `analysis/apktool/AndroidManifest.xml`
- 자체 signature 권한:
  - `com.korail.talk.BroadcastPermission` (`protectionLevel="signature"`)
  - `com.korail.talk.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` (`protectionLevel="signature"`)
- 주요 Android/Google 권한:
  - 네트워크/상태: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`
  - 알림/백그라운드: `WAKE_LOCK`, `VIBRATE`, `FOREGROUND_SERVICE`, `POST_NOTIFICATIONS`
  - 위치: `ACCESS_LOCATION`, `ACCESS_FINE_LOCATION`, `ACCESS_COARSE_LOCATION`
  - 저장소/미디어: `READ_EXTERNAL_STORAGE`(`maxSdkVersion=32`), `WRITE_EXTERNAL_STORAGE`(`maxSdkVersion=29`), `READ_MEDIA_IMAGES`, `READ_MEDIA_VISUAL_USER_SELECTED`
  - 카메라/음성/전화/블루투스: `CAMERA`, `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS`, `CALL_PHONE`, `BLUETOOTH`, `BLUETOOTH_CONNECT`, `READ_PHONE_STATE`
  - 광고/Privacy Sandbox: `com.google.android.gms.permission.AD_ID`, `ACCESS_ADSERVICES_AD_ID`, `ACCESS_ADSERVICES_ATTRIBUTION`, `ACCESS_ADSERVICES_TOPICS`
  - 푸시: `com.google.android.c2dm.permission.RECEIVE`
  - 다운로드: `DOWNLOAD_WITHOUT_NOTIFICATION`
- 런타임 확인:
  - `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java`의 권한 흐름은 `E.requestRequiredPermissions()` / `E.grantRequiredPermissions()` 호출로 분리되어 있어, 실제 요청 권한 목록 산정은 `E` 클래스 추가 분석이 필요하다.

## network_security_config

- 소스: `analysis/apktool/res/xml/network_security_config.xml`
- 정책:
  - `<domain-config cleartextTrafficPermitted="true">`
  - cleartext 허용 도메인:
    - `1.255.59.22`
    - `bot-dev-lb-100453984-927a54b5c9cb.kr-gov.lb.naverncp.com`
    - `teapp.srail.kr`
    - `app.srail.kr`
- 런타임 의미:
  - Android 플랫폼 네트워크 보안 정책상 위 호스트는 HTTP cleartext가 허용된다.
  - 앱 자체 KORAIL 기본 호스트는 `https://`를 사용하도록 상수화되어 있으나, SRT 관련 `teapp.srail.kr`/`app.srail.kr`은 cleartext 허용 목록에 포함되어 있다.
- 확인 한계:
  - 본 범위에서는 위 호스트로 실제 HTTP 요청을 하는 호출 경로까지 전수 매핑하지 않았다.
  - 인증서 pinning 또는 OkHttp `CertificatePinner` 설정은 이 범위의 확인 결과 명확히 식별되지 않았다.

## 앱 부트스트랩

### `KTApplication.onCreate()`

- 소스: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`
- 클래스/메서드:
  - `com.korail.talk.application.KTApplication extends G0.b`
  - `onCreate()`
  - 내부 호출 순서: `d()` -> `g()` -> `e()` -> `b()` -> `a()` -> `KakaoSdk.init(...)`
- 동작:
  - `d()`
    - `f28872a = this`로 전역 Application singleton 설정
    - `c()` 호출: `f()`와 `i()` 실행
    - `h()` 호출
    - `J4.b.init(getApplicationContext())`로 ORMLite DB helper 초기화
  - `f()`
    - `java.net.CookieManager` 생성
    - `CookiePolicy.ACCEPT_ALL`
    - `CookieHandler.setDefault(cookieManager)`
  - `h()`
    - `System.setProperty("http.keepAlive", "false")`
  - `g()`
    - NetFunnel 기본 인스턴스(`T6.h.getDefaultInstance()`) 설정
    - `protocol = Constants.SCHEME` (`com.kakao.sdk.common.Constants.SCHEME`, 일반적으로 `https`)
    - `host = "nf.letskorail.com"`
    - `port = U.DEFAULT_PORT_SSL`
    - `serviceID = K4.g.NETFUNNEL_SERVER_ID = "service_1"`
    - `actionID = K4.g.NETFUNNEL_ACTION_ID = "act_8"`
    - `timeout = 3`
  - `e()`
    - `b5.C1261a.getInstance().createTypeface(getApplicationContext())`로 앱 폰트/타입페이스 초기화
  - `b()`
    - `K4.a.VOLATILITY_FOLDER`, `K4.a.QR_FOLDER`에 해당하는 앱 폴더 삭제
  - `a()`
    - Android 8.0 이상에서 알림 채널 2개 생성
    - `"com.korail.talkemergency"` / `"긴급공지"` / importance 4
    - `G4.a.APPLICATION_ID` (`"com.korail.talk"`) / `"일반공지"` / importance 4
  - `KakaoSdk.init(this, getString(G4.j.kakao_app_key))`
    - `analysis/apktool/res/values/strings.xml`의 `kakao_app_key` 문자열 리소스를 사용
      (값 자체는 앱 벤더의 자격증명이라 이 저장소에 싣지 않는다 — 문서 첫머리의 "벤더 키 표기" 참조)
- 데이터 송수신:
  - `KTApplication.onCreate()` 자체에서 확인되는 직접 KORAIL API 호출은 없다.
  - NetFunnel 설정은 이후 `T6.g.BEGIN(...)` 호출 시 `nf.letskorail.com`으로 대기열/제어 요청을 수행할 기반 설정으로 보인다. 실제 NetFunnel wire format은 SDK 내부 난독화와 추가 분석이 필요하다.
  - Kakao SDK 초기화는 앱 키를 SDK에 전달한다. 이 시점의 네트워크 송신 여부는 로컬 코드만으로 확정하지 않았다.

### 쿠키 처리

- 소스: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`
- 메서드:
  - `clearCookie()`
  - `getCookie()`
  - `setSessionId()`
- 동작:
  - Java `CookieHandler` 기본값은 `CookiePolicy.ACCEPT_ALL`이다.
  - `getCookie()`는 기본 `CookieManager`의 쿠키 중 이름이 `JSESSIONID`인 값을 찾아 `"JSESSIONID=<value>"` 문자열로 반환한다.
  - `setSessionId()`는 Android WebView `CookieManager`에 `z.getSSLHost()` 도메인으로 `JSESSIONID`를 세팅하고 flush한다.
- 데이터:
  - 식별 가능한 데이터는 `JSESSIONID` 세션 쿠키 이름과 값이다.
  - 쿠키 값의 실제 내용/발급 응답은 로컬 아티팩트에 없다.

### 로컬 DB 초기화

- 소스:
  - `analysis/jadx/sources/J4/b.java`
  - `analysis/jadx/sources/J4/a.java`
- 클래스/메서드:
  - `J4.b.init(Context)`
  - `J4.a extends OrmLiteSqliteOpenHelper`
- 동작:
  - DB 파일명: `korailtalk.sqlite`
  - DB version: `15`
  - 생성 테이블 모델:
    - `StationData`
    - `FavoriteStation`
    - `CreditCard`
    - `IssueList`
    - `TicketDetail`
    - `ZRecentStation`
    - `MainPopupData`
    - `DoNotLookAgain`
    - `SMSData`
- 데이터:
  - 로컬 저장 데이터에는 역 정보, 즐겨찾기, 카드 정보, 티켓 상세, 최근 구간, 팝업, SMS 데이터가 포함될 수 있다.
  - 테이블 컬럼 전체와 암호화 여부는 각 model 클래스 추가 분석이 필요하다.

## 호스트/환경 선택

### 환경 enum과 빌드 상수

- 소스:
  - `analysis/jadx/sources/G4/a.java`
  - `analysis/jadx/sources/d5/EnumC5607a.java`
  - `analysis/jadx/sources/K4/g.java`
  - `analysis/jadx/sources/S4/z.java`
- 상수/메서드:
  - `G4.a.CONNECT_SERVER = "3"`
  - `EnumC5607a`: `DEV("0")`, `STAGING("1")`, `TEST("2")`, `REAL("3")`
  - `K4.g.SERVER_TYPE = EnumC5607a.fromCode("3")`
- 결론:
  - 이 APK는 런타임 기본 서버 타입이 `REAL`이다.

### 기본 API/Web 호스트

- 소스: `analysis/jadx/sources/S4/z.java`
- 메서드:
  - `getSSLHost()`
  - `getWebHost()`
  - `getPushAddress()`
  - `getMultiLangWebHost()`
- `SERVER_TYPE=REAL`일 때:
  - `getSSLHost()` -> `https://smart.letskorail.com`
  - `getWebHost()` -> `https://smart.letskorail.com`
  - `getPushAddress()` -> `smart.letskorail.com`
  - `getMultiLangWebHost()` -> `https://www.korail.com`
- 다른 환경 분기:
  - `TEST` -> `https://dev3.letskorail.com`
  - `STAGING` -> `https://dev2.letskorail.com`
  - `DEV` -> `https://mobiledev.letskorail.com`
  - 다국어는 `REAL`/`STAGING`이면 `https://www.korail.com`, 그 외는 `https://dev5.letskorail.com`

### 주요 URL 상수

- 소스: `analysis/jadx/sources/K4/g.java`
- 상수:
  - `COMMON_PARAMETER = "Device=AD&Version=250601003&Key=korail1234567890"`
  - `SECURE_PROTOCOL = "https://"`
  - `FIND_ALL_URL = "https://www.korail.com/ticket/membership/findMember"`
  - `NAVER_REQUEST_API = "https://openapi.naver.com/v1/nid/me"`
  - `TRAIN_MAP_URL = "https://gis.korail.com/korailTalk/entrance"`
  - `PRIVACY_URL = "https://info.korail.com/info/contents.do?key=2812"`
  - `SRT_WEB_ORG = "eapp"`
  - `SRT_WEB_TEST = "teapp"`
  - `SRT_WEB_RESERVATION_URL = "https://eapp.srail.kr/"` (`SERVER_TYPE != DEV`)
  - `NETFUNNEL_SERVER_ID = "service_1"`
  - `NETFUNNEL_ACTION_ID = "act_8"`
  - `NETFUNNEL_ACTION_ID_PEAKSEASON = "act_8_2"`
  - `NETFUNNEL_ACTION_PAY_ID = "act_18"`
  - `NETFUNNEL_ACTION_PRODUCT_ID = "act_6"`
  - `NETFUNNEL_ACTION_REFUND_ID = "act_22"`
  - `NETFUNNEL_ACTION_RESERVED_ID = "act_21"`
  - `NETFUNNEL_ACTION_RESERVE_ID = "act_14"`
  - `NETFUNNEL_ACTION_TEST_ID = "act_4"`
- 런타임 의미:
  - 앱 API 호출은 대부분 Retrofit endpoint `z.getSSLHost()`에 상대 경로를 붙이는 방식이다.
  - 웹뷰/외부 브라우저용 URL은 `z.getWebHost()` 또는 별도 절대 URL 상수에서 구성된다.

## 네트워크 클라이언트/공통 요청

### Retrofit 구성

- 소스: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java`
- 클래스/메서드:
  - `com.korail.talk.network.ExecuteDao.getDefaultRestAdapterBuilder()`
  - `getRestAdapterBuilder()`
  - `getService(Class<T>)`
- 동작:
  - Retrofit 1.x `RestAdapter.Builder` 사용
  - Gson converter 사용: `new GsonConverter(new e().create())`
  - 기본 endpoint: `S4.z.getSSLHost()`
  - `UrlConnectionClient.openConnection(Request)` override
  - connect timeout/read timeout: 각 `60000ms`
  - 로그 레벨: `I4.a.IS_DEBUG_LOG ? FULL : NONE`
- 데이터:
  - 모든 기본 DAO 호출은 `https://smart.letskorail.com` 기준 상대 경로로 요청된다.
  - `I4.a.IS_MACRO_ACTIVE=true`이고 URL이 특정 예약/로그인/운임 경로 중 하나를 포함하면 `x-dynapath-m-token` 헤더가 추가된다.

### 공통 BaseRequest/BaseResponse

- 소스:
  - `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`
  - `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`
- 요청 기본 필드:
  - `Device = "AD"`
  - `Version = "250601003"`
  - `Key = "korail1234567890"`
- 응답 기본 필드:
  - `strResult`
  - `h_msg_cd` -> `hMsgCd`
  - `h_msg_txt` -> `hMsgTxt`
  - 성공/실패 문자열 상수: `SUCCESS = "SUCC"`, `FAIL = "FAIL"`
- 주의:
  - 이 값은 로컬 코드에서 고정된 식별/버전/키 파라미터다. 실제 서버 응답 내용은 분석 대상에 없다.

### 공통 서비스 예시

- 소스: `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java`
- 식별 가능한 endpoint/필드:
  - `POST /classes/com.korail.mobile.common.code.do`
    - 필드: `Device`, `Version`, `Key`, `code`, `deviceWidth`, `deviceHeight`, `departDate`, `arrivalDate`, `holidayYn`, `OSVersion`
  - `POST /classes/com.korail.mobile.common.encrypt.do`
    - 필드: `Device`, `Version`, `Key`, `type`, `values`
  - `POST /classes/com.korail.mobile.common.decrypt.do`
    - 필드: `Device`, `Version`, `Key`, `type`, `values`
  - `GET /classes/com.korail.mobile.common.stationdata`
  - `GET /classes/com.korail.mobile.common.stationinfo`
    - query: `Device`
  - `GET /ebizcross/getUUID.do`
- 응답 DTO:
  - `EncryptDao.EncryptResponse.encValueList[].encValue`
  - `DecryptDao.DecryptResponse.decValueList[].decValue`
  - `CommonCodeDao.CommonCodeResponse`는 메뉴/팝업/로그인/결제 노출/매크로 플래그 등 다수의 로컬 설정 데이터를 포함한다.

## IntroActivity 초기 부트스트랩

- 소스: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java`
- 클래스/메서드:
  - `com.korail.talk.ui.intro.IntroActivity.onCreate(Bundle)`
  - `n0()`, `H0()`, `E0()`, `q0()`, `r0()`, `p0()`, `onReceive(IBaseDao)`
- 흐름:
  - `onCreate()`
    - `setContentView(G4.h.activity_intro)`
    - `DynaPathMobileSDK.Companion.initialize(getApplication())` 호출
    - intro image/text 설정 후 권한/Google Play Services/서비스 체크 흐름 진입
  - `n0()`
    - 필수 권한이 허용되어 있으면 `H0()`, 아니면 권한 다이얼로그
  - `H0()`
    - Google Play Services 사용 가능 확인
    - 조건 충족 시 쿠키 삭제, 로그인 상태 false, 편의설정 업데이트 플래그 저장 후 `E0()`
  - `E0()`
    - `SERVER_TYPE == STAGING`이면 서비스 체크 없이 `r0()`
    - 그 외는 `q0()`로 `ServiceCheckDao` 실행
  - `r0()`
    - `CommonCodeDao.CommonCodeRequest` 생성
    - 요청 코드 목록에 `IMAGE_DOWN_LOAD_DATA`, `MENU_RAILPOINT`, `MAIN_POPUP`, `IS_NAVER_SHOW`, `KORAIL_BOSS`, `BUY_NOW`, `LOST_ARTICLE`, `EASY_PAY`, `ATHN`, `VIEW_VISIBILITY`, `MENU_BIZ`, `POINT`, `DATA`, `LOGIN`, `REPORT`, `HOLIDAY_POPUP`, `MAAS_TEST`, `LIMOUSINE_MAIN_MSG` 등을 추가
    - Android 8 미만이면 `DEVICE_OREO`도 추가
    - `OSVersion = Build.VERSION.SDK_INT`
  - `onReceive()`의 `dao_common_code`
    - 공통코드 응답의 메뉴/로그인/결제/팝업/기능노출/보고 데이터 등을 SharedPreferences에 JSON 문자열로 저장
    - main popup 정보를 로컬 DB `MainPopupData`에 저장/삭제
    - `I4.a.IS_AUTO_REFRESH_ACTIVE`를 응답 `data.autoRefresh == "Y"`로 설정
    - `I4.a.IS_MACRO_ACTIVE`를 응답 `data.isMacroEnable == "Y"`로 설정
    - 이후 `p0()`로 `AppDataDao` 실행
  - `dao_app_data`
    - `KEY_RAIL_PLUS_CARD_INFO`, `DISABILITY_CERTIFICATION_MSG`, `KEY_LIMOUSINE_MSG` 저장
    - `version.NEWDVERSION`과 현재 `G4.a.VERSION_NAME`을 비교하여 강제/선택 업데이트 다이얼로그 또는 다음 단계로 이동
- 데이터:
  - 공통코드 요청은 앱 버전/키/기기구분과 코드 목록, 화면 크기, 날짜, OS 버전을 전송한다.
  - 공통코드 응답은 로컬 설정/노출 제어/팝업/로그인/결제 옵션/매크로 활성 여부 등을 포함한다. 실제 응답값은 로컬 아티팩트에 없다.

## Anti-macro/DynaPath

- 소스:
  - `analysis/jadx/sources/kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java`
  - `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java`
  - `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java`
- 초기화:
  - `IntroActivity.onCreate()`에서 `DynaPathMobileSDK.Companion.initialize(getApplication())`
  - 실패 시 `DynaPathException` code/message를 debug log로 기록
- 토큰 생성/전송:
  - `ExecuteDao.openConnection(Request)`에서 `I4.a.IS_MACRO_ACTIVE`가 true일 때 특정 URL 포함 여부 확인
  - 대상 URL fragment:
    - `/classes/com.korail.mobile.certification.TicketReservation`
    - `/classes/com.korail.mobile.nonMember.NonMemTicket`
    - `/classes/com.korail.mobile.seatMovie.ScheduleView`
    - `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
    - `/classes/com.korail.mobile.trn.prcFare.do`
    - `/classes/com.korail.mobile.login.Login`
  - 매칭 시 `DynaPathMobileSDK.Companion.generate()` 결과를 `x-dynapath-m-token` 요청 헤더로 추가
- 응답 처리:
  - `BaseDaoHelper.HttpTask`에서 `RetrofitError`가 `403 Forbidden`이고 응답 헤더 `DynaPath-Result`가 존재하며 값이 음수이면 body를 문자열로 읽는다.
  - body JSON에 `message`가 있으면 DAO의 `setMacroShowDialog(message)`에 저장한다.
- 확인 한계:
  - DynaPath 토큰 내부 구조, 암호 알고리즘, 서버 검증 프로토콜은 난독화된 SDK 내부 추가 분석이 필요하다.

## Exported 컴포넌트와 딥링크

### Exported activity

- 소스: `analysis/apktool/AndroidManifest.xml`
- 외부 노출 activity:
  - `com.korail.talk.ui.intro.IntroActivity`
    - `MAIN`/`LAUNCHER`
  - `com.korail.talk.ui.login.member.LoginActivity`
  - `com.kakao.sdk.auth.AuthCodeHandlerActivity`
    - scheme = 고정 접두 `kakao` + `kakao_app_key`, host = `oauth`
  - `com.korail.talk.ui.mypage.MyPageActivity`
  - `com.korail.talk.ui.scheme.NavigationActivity`
    - `korailtalk://navigation`
  - `com.korail.talk.ui.scheme.DataActivity`
    - `korailtalk://member_info`
  - `com.korail.talk.ui.payment.PaymentActivity`
    - `korailtalk://approve`
  - `com.korail.talk.ui.railPlus.RailPlusActivity`
    - `korailtalk://railpluscardinfo`
  - `com.korail.talk.ui.setting.MultiLanguageActivity`
  - `com.korail.talk.ui.extraproduct.ExtraProductListActivity`
  - `com.korail.talk.ui.web.IntegrationWebViewActivity`
  - `com.korail.talk.ui.web.MaumAIWebViewActivity`
    - intent-filter action: `android.intent.action.PHONE_STATE`, `android.intent.action.NEW_OUTGOING_CALL`
  - `com.korail.talk.ui.web.ExtraProductWebViewActivity`
  - `com.korail.talk.ui.web.TrainServiceWebViewActivity`
  - `com.korail.talk.ui.certification.GovernmentCertificationActivity`
  - `com.korail.talk.ui.reservation.BixbyReservationActivity`
  - `com.korail.talk.test.NetfunnelTestActivity`
    - action `MAIN`, launcher category 없음
  - `com.nhn.android.naverlogin.ui.OAuthCustomTabActivity`
    - `naver3rdpartylogin://authorize/`
  - `com.code1system.code1cardscanlib.activities.CamActivity`
- 확인 한계:
  - filter 없이 exported된 Activity는 외부 앱이 명시적 Intent로 실행 가능하다. 각 Activity의 인증/입력 검증 여부는 별도 클래스별 분석이 필요하다.

### `korailtalk://navigation`

- 소스:
  - `analysis/apktool/AndroidManifest.xml`
  - `analysis/jadx/sources/com/korail/talk/ui/scheme/NavigationActivity.java`
  - `analysis/jadx/sources/S4/y.java`
- 클래스/메서드:
  - `NavigationActivity.onCreate(Bundle)`
  - `S4.y.getNavigationBundle(Uri)`
  - `S4.y.getClassNm(Uri)`
- 동작:
  - URI query parameter 전체를 순회하여 `view`를 제외한 값을 `Bundle`에 문자열로 복사한다.
  - `view` 값으로 대상 Activity를 선택한다.
  - Intent extras가 있으면 navigation bundle에 병합한다.
  - `C0815o.navigation(getApplicationContext(), targetClass, bundle)` 호출 후 finish한다.
- 식별 가능한 `view` 라우팅:
  - `booking` -> `MainBookingActivity`
  - `ticket` -> `TicketListActivity`
  - `memberCard` -> `MemberCardActivity`
  - `web` -> `IntegrationWebViewActivity`
  - `discountCoupon` -> `DiscountCouponActivity`
  - `delayDiscountCoupon` -> `DelayDiscountCouponActivity`
  - `mileage` -> `MileageHistoryActivity`
  - `seasonTicket` -> `CommutationBookingActivity`
  - `periodSeasonTicket` -> `PeriodCommutationBookingActivity`
  - `reservation` -> `BixbyReservationActivity`
  - `discountMenuList` -> `NewDiscountMenuActivity`
  - `tripMenuList` -> `NewTripMenuActivity`
  - `pushHistory` -> `PushHistoryActivity`
  - `bookedTicket` -> `ReservedTicketActivity`
  - `bookedTrip` -> `TripBookingListActivity`
  - `offlineTikcetReturn` -> `OfflineTicketReturnActivity` (`Tikcet` 오타 그대로)
  - `accumulatingMilege`, `tourReserved`, `ticketRefund`, `offlineTicketRefund`, `togetherMileage`, `tourMenuList` -> `AccumulatingKTXMileageActivity`
  - `mainBannerStation_Init` -> `MainBookingActivity`
- 데이터:
  - 외부 URI의 query parameter가 대상 Activity extras로 전달될 수 있다.
  - 각 target Activity가 어떤 key를 소비하는지는 별도 분석 필요.

### `korailtalk://member_info`

- 소스:
  - `analysis/apktool/AndroidManifest.xml`
  - `analysis/jadx/sources/com/korail/talk/ui/scheme/DataActivity.java`
  - `analysis/jadx/sources/com/korail/talk/network/dao/common/EncryptDao.java`
  - `analysis/apktool/res/values/strings.xml`
- 클래스/메서드:
  - `DataActivity.onCreate(Bundle)`
  - `DataActivity.g0()`
  - `DataActivity.onReceive(IBaseDao)`
  - `DataActivity.sendLoginData(String)`
- 동작:
  - `H.getString(...)`/`H.getBoolean(...)`으로 로컬 저장 로그인 설정을 읽는다.
    - `KEY_LOGIN_TYPE`
    - `KEY_LOGIN_ID`
    - `KEY_LOGIN_PW`
    - `KEY_AUTO_LOGIN`
    - `KEY_MEMBER_NUM`
  - `F4.a.decryptAES(...)`로 저장된 로그인 ID/PW를 조건부 복호화한다.
  - JSON 생성:
    - `loginType`
    - `loginId` (`KEY_MEMBER_NUM` 또는 `KEY_AUTO_LOGIN`이면 복호화 ID, 아니면 빈 문자열)
    - `loginPw` (`KEY_AUTO_LOGIN`이면 복호화 PW, 아니면 빈 문자열)
    - `isAutoLogin`
    - `isSaveMemberNumber`
  - JSON 문자열을 `F4.a.encryptBase64(...)`로 base64 암호화/인코딩한 뒤 `EncryptDao`로 서버 암호화 요청을 보낸다.
  - `EncryptDao` 요청:
    - endpoint: `POST /classes/com.korail.mobile.common.encrypt.do`
    - fields: `Device`, `Version`, `Key`, `type="1"`, `values=[base64LoginJson]`
  - `EncryptDao.EncryptResponse.encValueList[0].encValue`를 수신하면 외부 URI 실행:
    - 리소스 `data_login_scheme = "korailtalklite://member_info?value=%1$s"`
    - `korailtalklite://member_info?value=<encValue>`
    - flags: `872415232`
- 데이터:
  - 로컬 저장 로그인 타입/회원번호/비밀번호 보존 여부/자동로그인 여부가 암호화되어 외부 `korailtalklite` scheme으로 전달된다.
  - 실제 `encValue` 값과 서버 암호화 응답 구조의 전체 내용은 로컬 아티팩트에 없다.

### `korailtalk://approve`

- 소스:
  - `analysis/apktool/AndroidManifest.xml`
  - `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java`
  - `analysis/jadx/sources/S4/D.java`
  - `analysis/apktool/res/values/strings.xml`
- 클래스/메서드:
  - `PaymentActivity.onCreate(Bundle)`
  - `PaymentActivity.onNewIntent(Intent)`
  - `S4.D.isApproveScheme(Context, Intent/Uri)`
- 동작:
  - `S4.D.isApproveScheme()`은 URI의 `scheme://authority`가 리소스 `korailtalk_scheme_approve = "korailtalk://approve"`와 같은지 비교한다.
  - `PaymentActivity.onCreate()`에서 approve scheme으로 직접 시작된 경우:
    - `K4.g.SERVER_TYPE == DEV`일 때만 `onNewIntent(getIntent())` 처리
    - 현재 APK는 `SERVER_TYPE=REAL`이므로 direct approve launch는 `finish()`
  - 기존 결제 화면의 `singleTask` 재진입 `onNewIntent()`에서는 approve URI query parameter 전체를 Bundle에 복사한다.
  - query key가 `otcNo`이면 공백을 `"+"`로 치환한다.
  - 현재 Fragment가 `b6.AbstractC1269e`이면 `setEasyPaymentData(bundle)` 호출
- 관련 리소스:
  - `payment_scheme = "korailtalk://approve?type=%1$s&bankCode=%2$s&password=%3$s"`
  - `payment_monimo_scheme = "monimopay://?xid=%1$s&mrcType=KRT&callbackUrl=korailtalk://approve?type=monimopay"`
- 데이터:
  - 결제 콜백 query parameter 전체가 결제 Fragment로 전달된다.
  - 로컬 리소스 기준으로 `type`, `bankCode`, `password`, `otcNo` 등이 식별된다.
  - 결제 승인 서버 응답 자체는 이 deeplink만으로 확인되지 않는다.

### `korailtalk://railpluscardinfo`

- 소스:
  - `analysis/apktool/AndroidManifest.xml`
  - `analysis/jadx/sources/com/korail/talk/ui/railPlus/RailPlusActivity.java`
  - `analysis/jadx/sources/com/korail/talk/network/dao/common/DecryptDao.java`
  - `analysis/jadx/sources/com/korail/talk/network/dao/railplus/AutoChargeDao.java`
  - `analysis/jadx/sources/com/korail/talk/network/dao/railplus/RailPlusService.java`
- 클래스/메서드:
  - `RailPlusActivity.onNewIntent(Intent)`
  - `RailPlusActivity.v0(String, String...)`
  - `RailPlusActivity.u0(String, String)`
- 동작:
  - `onCreate()`에서 외부 RailPlus 앱 실행 intent를 준비한다.
    - 리소스 `payment_rail_plus_cardinfo_scheme = "railplus://cardinfo"`
    - target package: `com.mic.set.hce.railpluscardserviceandroid`
  - `onNewIntent()`에서 URI query parameter `RET_CODE` 확인
    - `"000000"`이면 `BALANCE`, `CARD_NO`를 사용
    - `BALANCE`로 화면 금액 표시
    - `CARD_NO`를 `DecryptDao`로 복호화 요청
    - 실패 시 `RET_MSG`를 다이얼로그에 표시 후 종료
  - `DecryptDao` 요청:
    - endpoint: `POST /classes/com.korail.mobile.common.decrypt.do`
    - fields: `Device`, `Version`, `Key`, `type="1"`, `values=[CARD_NO]`
  - 복호화 응답 `decValueList[0].decValue`를 `AutoChargeDao`에 전달
  - `AutoChargeDao` 요청:
    - endpoint: `GET /classes/com.korail.mobile.railplus.autoCharge.do`
    - query: `Device`, `Version`, `Key`, `jobDvCd`, `prepCrdNo`
  - `AutoChargeResponse.psbFlg == "Y"`이면 자동충전 체크박스 on
- 데이터:
  - 외부 RailPlus 앱에서 `RET_CODE`, `RET_MSG`, `BALANCE`, `CARD_NO`를 받는다.
  - 카드번호는 먼저 서버 복호화 요청 후 자동충전 조회/설정 요청의 `prepCrdNo`로 사용된다.
  - `psbFlg` 외 응답 세부값은 로컬 DTO에 없다.

### OAuth 딥링크

- Kakao
  - manifest: `com.kakao.sdk.auth.AuthCodeHandlerActivity`
  - scheme/host: scheme 은 고정 접두 `kakao` 에 `kakao_app_key` 를 이어붙인 것, host 는 `oauth`
    (Kakao SDK 규칙. 키 값은 싣지 않으므로 완성된 리터럴은 적지 않는다)
  - app key: `analysis/apktool/res/values/strings.xml`의 `kakao_app_key`
  - SDK 버전 후보: `analysis/jadx/sources/com/kakao/sdk/v2/*/BuildConfig.java`에서 `2.11.0` 또는 일부 `2.6.0`
- Naver
  - manifest: `com.nhn.android.naverlogin.ui.OAuthCustomTabActivity`
  - scheme/host/path: `naver3rdpartylogin://authorize/`
  - 관련 API 상수: `K4.g.NAVER_REQUEST_API = "https://openapi.naver.com/v1/nid/me"`
- 확인 한계:
  - OAuth authorize/token 교환 파라미터 전체는 각 SDK 내부/로그인 클래스 추가 분석이 필요하다.

## Exported service/receiver/provider

### Exported service

- 소스: `analysis/apktool/AndroidManifest.xml`
- 목록:
  - `com.h2osystech.smartalimi.servicealimi.MessageManager`
    - action: `com.h2osystech.smartalimi.servicealimi.MessageManager`
  - `com.h2osystech.smartalimi.servicealimi.fcm.FCMListenerServiceHandler`
    - action: `com.google.firebase.MESSAGING_EVENT`
  - `androidx.work.impl.background.systemjob.SystemJobService`
    - permission: `android.permission.BIND_JOB_SERVICE`
  - `com.google.android.gms.auth.api.signin.RevocationBoundService`
    - permission: `com.google.android.gms.auth.api.signin.permission.REVOCATION_NOTIFICATION`
    - `visibleToInstantApps="true"`
- `MessageManager` 런타임:
  - 소스: `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/MessageManager.java`
  - `onCreate()`에서 `SharedData`의 `noticeEnv`, `UserInfo`를 읽어 `Const`에 설정한다.
  - 읽는 값:
    - `PushType`, `ipaddress`, `AppType`, `UserID`, `UserPW`, `EnableLog`, `logLevel`, `gcmToken`, `GCMCallbackMode`, `OnebyOne`
  - `Const.brokerPushType != 0`이면 자기 자신 서비스 intent를 만들고, Android 8 이상에서는 `AlimiInterface.autoLogin()` 경로로 진입한다.
  - `onStartCommand()`는 intent type이 `BuildConfig.FLAVOR + Const.SERVICE_START_INTENTNAME`인지 확인한다. SmartAlimi `BuildConfig.FLAVOR`는 `korail`이다.
- `FCMListenerServiceHandler` 런타임:
  - 소스: `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/fcm/FCMListenerServiceHandler.java`
  - `onMessageReceived(z)`
    - FCM data payload를 파싱한다.
    - 필드: `Subject`, `Content`, `Date`, `Seq`, `TimeStamp`, `SenderID`, `Param`, `MsgType`, `BizName`, `badge`
    - 저장 사용자 ID가 없으면 처리 중단
    - 네트워크 상태에 따라 서버에서 새 메시지를 가져오거나 payload를 로컬 삽입/알림 처리
  - `onNewToken(String)`
    - token을 `SharedData(UserInfo, gcmToken)`에 저장
    - `Const.setGcmRegID(str)`
    - `alimiInterface.registToken()`
- 데이터:
  - FCM data payload에는 제목/내용/날짜/시퀀스/발신자/파라미터/업무명/배지 등이 포함된다.
  - token 등록 시 실제 등록 endpoint/요청 본문은 `AlimiInterface`/SmartAlimi 모듈 추가 분석 필요.

### Exported receiver

- 소스: `analysis/apktool/AndroidManifest.xml`
- 목록:
  - `com.korail.talk.provider.WidgetProvider`
    - action: `android.appwidget.action.APPWIDGET_UPDATE`
  - `com.korail.talk.receiver.PushBroadcastReceiver`
    - action: `com.korail.talk.NewMsgReceiver`
    - permission: `com.korail.talk.BroadcastPermission`
  - `com.h2osystech.smartalimi.servicealimi.RestartReceiver`
    - action: `RestartReceiver.serviceRestart`
  - `androidx.work.impl.diagnostics.DiagnosticsReceiver`
    - action: `androidx.work.diagnostics.REQUEST_DIAGNOSTICS`
    - permission: `android.permission.DUMP`
  - `com.google.firebase.iid.FirebaseInstanceIdReceiver`
    - action: `com.google.android.c2dm.intent.RECEIVE`
    - permission: `com.google.android.c2dm.permission.SEND`
  - `androidx.profileinstaller.ProfileInstallReceiver`
    - actions: profile install/skip/save/benchmark
    - permission: `android.permission.DUMP`
- `RestartReceiver` 런타임:
  - 소스: `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/RestartReceiver.java`
  - action이 `RestartReceiver.serviceRestart`이면 `MessageManager` service intent를 만들고 extra `Const.SERVICE_START_INTENTNAME=2`로 startService한다.

### Provider

- 소스: `analysis/apktool/AndroidManifest.xml`
- 명시 provider:
  - `androidx.core.content.FileProvider`
    - authorities: `com.korail.talk.fileprovider`
    - exported: `false`
    - grantUriPermissions: `true`
    - paths: `analysis/apktool/res/xml/provider_paths.xml`
      - `<external-cache-path name="storage/emulated/0" path="/" />`
      - `<external-path name="storage/emulated/0" path="/" />`
    - 의미: provider는 non-exported지만 앱이 grant한 URI는 외부 앱 접근 가능하다. path가 외부 저장소 루트를 넓게 포함한다.
  - `com.h2osystech.smartalimi.servicealimimodule.DataProvider`
    - authorities: `@string/authorities`
    - `analysis/apktool/res/values/strings.xml`: `com.h2osystech.smartalimi.ServiceAlimiData.korail`
    - exported: `false`
  - `com.google.android.gms.ads.MobileAdsInitProvider`
    - authorities: `com.korail.talk.mobileadsinitprovider`
    - exported: `false`
    - initOrder: `100`
  - `androidx.startup.InitializationProvider`
    - authorities: `com.korail.talk.androidx-startup`
    - exported: `false`
    - metadata: WorkManager/ProfileInstaller initializer
  - `com.squareup.picasso.PicassoProvider`
    - authorities: `com.korail.talk.com.squareup.picasso`
    - exported: `false`
  - `com.google.firebase.provider.FirebaseInitProvider`
    - authorities: `com.korail.talk.firebaseinitprovider`
    - exported: `false`
    - initOrder: `100`

## Third-party SDK 초기화/메타데이터

### Kakao SDK

- 코드 초기화: `KTApplication.onCreate()`의 `KakaoSdk.init(this, getString(j.kakao_app_key))`
- manifest metadata: `com.kakao.sdk.AppKey=@string/kakao_app_key`
- 리소스: `kakao_app_key` (값 비공개 — 「벤더 키 표기」)
- OAuth callback activity: `com.kakao.sdk.auth.AuthCodeHandlerActivity`
- 데이터:
  - 앱 키와 OAuth redirect scheme이 SDK에 사용된다.
  - 로그인 토큰/사용자 정보 요청은 관련 로그인 클래스 추가 분석 필요.

### Firebase/FCM

- manifest:
  - `firebase_messaging_auto_init_enabled=false`
  - `firebase_analytics_collection_enabled=false`
  - `com.google.firebase.provider.FirebaseInitProvider`
  - `com.google.firebase.messaging.FirebaseMessagingService`
  - `com.google.firebase.components.ComponentDiscoveryService`
  - registrar:
    - `FirebaseMessagingRegistrar`
    - `firebase.iid.Registrar`
    - `TransportRegistrar`
    - `FirebaseInstallationsRegistrar`
- 리소스:
  - `google_app_id` (값 비공개 — 「벤더 키 표기」)
  - `gcm_defaultSenderId=303574505999`
  - `firebase_database_url` = `https://<프로젝트 id>.firebaseio.com` 형태 (프로젝트 id 비공개 — 「벤더 키 표기」)
- raw properties:
  - `analysis/raw/firebase-common.properties`: `19.3.0`
  - `analysis/raw/firebase-components.properties`: `16.0.0`
  - `analysis/raw/firebase-iid.properties`: `21.0.0`
  - `analysis/raw/firebase-datatransport.properties`: `17.0.3`
  - `analysis/raw/firebase-installations-interop.properties`: `16.0.0`
- 런타임:
  - Firebase provider는 앱 시작 시 FirebaseApp 초기화를 수행할 수 있다.
  - FCM 자동 초기화는 manifest상 false이나, `FCMAdapter.getToken()`은 명시적으로 `FirebaseMessaging.getInstance().getToken()`을 호출한다.
  - `FCMListenerServiceHandler`는 FCM data payload와 token 갱신을 SmartAlimi 모듈에 전달한다.

### Google Mobile Ads / AdServices

- manifest:
  - metadata `com.google.android.gms.ads.APPLICATION_ID` 존재 (AdMob app id, 값 비공개 — 「벤더 키 표기」)
  - provider `com.google.android.gms.ads.MobileAdsInitProvider`
  - service `com.google.android.gms.ads.AdService`
  - activity `com.google.android.gms.ads.AdActivity`
  - property `android.adservices.AD_SERVICES_CONFIG=@xml/gma_ad_services_config`
- raw properties:
  - `analysis/raw/play-services-ads.properties`: `23.2.0`
  - `analysis/raw/play-services-ads-identifier.properties`: `18.0.0`
- AdServices config:
  - 소스: `analysis/apktool/res/xml/gma_ad_services_config.xml`
  - `<attribution allowAllToAccess="true" />`
  - `<topics allowAllToAccess="true" />`
- 데이터:
  - 광고 SDK가 광고 ID/Topics/Attribution API를 사용할 수 있는 manifest/permission 구성이 있다.
  - 실제 광고 요청 단위 ID와 요청 payload는 광고 호출부 추가 분석 필요.

### WorkManager / AndroidX Startup / ProfileInstaller

- manifest:
  - `androidx.startup.InitializationProvider`
  - metadata:
    - `androidx.work.WorkManagerInitializer`
    - `androidx.profileinstaller.ProfileInstallerInitializer`
  - WorkManager system alarm/job/foreground services와 constraint receivers
  - Diagnostics/ProfileInstall receiver 일부는 `android.permission.DUMP` 보호
- 데이터:
  - WorkManager 작업 정의는 본 범위에서 식별하지 않았다.

### SmartAlimi / H2O SysTech Push

- manifest:
  - `com.h2osystech.smartalimi.servicealimimodule.DataProvider`
  - `com.h2osystech.smartalimi.servicealimi.MessageManager`
  - `com.h2osystech.smartalimi.servicealimi.fcm.FCMListenerServiceHandler`
  - `com.h2osystech.smartalimi.servicealimi.RestartReceiver`
- BuildConfig:
  - `analysis/jadx/sources/com/h2osystech/smartalimi/servicealimi/BuildConfig.java`
  - `BUILD_TYPE=release`
  - `DEBUG=false`
  - `FLAVOR=korail`
  - `VERSION_NAME=1.8.4`
- 데이터:
  - SharedData에서 broker IP/AppType/UserID/UserPW/gcmToken 등을 읽는다.
  - FCM payload 또는 broker poll 결과로 메시지 저장/알림 표시를 수행한다.

### DynaPath

- 초기화: `IntroActivity.onCreate()`
- 토큰 헤더: `x-dynapath-m-token`
- 활성화 플래그: `I4.a.IS_MACRO_ACTIVE`, 공통코드 응답 `data.isMacroEnable`
- 데이터:
  - SDK initialize는 application context와 환경/기기 상태 추정값을 내부 생성자에 전달한다.
  - 토큰 payload 내부는 로컬 코드만으로 식별 불가.

### Naver OAuth

- manifest callback: `naver3rdpartylogin://authorize/`
- API 상수: `K4.g.NAVER_REQUEST_API`
- 코드 근거:
  - `analysis/jadx/sources/c5/C1309b.java`에서 `OAuthLogin.showDevelopersLog(I4.a.IS_DEBUG_LOG)` 호출이 확인된다.
- 데이터:
  - 사용자 프로필 조회 endpoint는 식별되지만, client id/secret 및 OAuth request 전체 파라미터는 추가 분석 필요.

### Code1 card scan / camera

- manifest:
  - `com.code1system.code1cardscanlib.activities.CamActivity` exported true
- raw assets:
  - `analysis/raw/assets/code1ocr.lic`
  - `analysis/raw/assets/cardscan.txt`
- 데이터:
  - 카드 스캔 라이브러리와 OCR license asset이 포함된다.
  - 스캔 결과를 어느 Activity/DAO가 소비하는지는 결제/카드 등록 흐름 추가 분석 필요.

## 패키지 visibility queries

- 소스: `analysis/apktool/AndroidManifest.xml`
- 식별된 조회 대상:
  - 결제/인증/간편결제/포인트/백신/정부ID/외부 앱:
    - `com.nhnent.payapp`
    - `com.ssg.serviceapp.android.egiftcertificate`
    - `com.kakao.talk`
    - `com.nhn.android.search`
    - `kr.go.mobileid`
    - `kr.go.mobileid.tbe`
    - `com.samsung.android.spay`
    - `com.samsung.android.spaylite`
    - `com.lge.lgpay`
    - `com.shcard.smartpay`
    - `kvp.jjy.MispAndroid320`
    - `com.lottemembers.android`
    - `com.ahnlab.v3mobileplus`
    - `kr.go.gfido.m`
    - `com.RLP.railpolice`
    - `com.kbcard.cxh.appcard`
    - `net.ib.android.smcard`
  - 루팅 탐지 후보:
    - `com.noshufou.android.su`
    - `com.noshufou.android.su.elite`
    - `eu.chainfire.supersu`
    - `com.koushikdutta.superuser`
    - `com.thirdparty.superuser`
    - `com.yellowes.su`
    - `com.topjohnwu.magisk`
    - `com.kingroot.kinguser`
    - `com.kingo.root`
    - `com.smedialink.oneclickroot`
    - `com.zhiqupk.root.global`
    - `com.alephzain.framaroot`
  - Kakao 변형:
    - `com.kakao.talk.alpha`
    - `com.kakao.talk.sandbox`
    - `com.kakao.onetalk`
  - intent queries:
    - 임의 scheme/host `VIEW`
    - `mobileid`, `tmobileid` verify
    - CameraX vendor action
    - `https` browsable
    - CustomTabsService
- 런타임 의미:
  - Android 11+ package visibility 제한 하에서 위 패키지/intent resolve가 가능하도록 선언되어 있다.
  - 실제 루팅 탐지/앱 설치 유도 로직은 `G.playApp`, 보안/결제 흐름 추가 분석 필요.

## 확인된 주요 요청/응답 데이터 요약

| 위치 | 요청 데이터 | 응답 데이터 | 비고 |
| --- | --- | --- | --- |
| `BaseRequest` | `Device=AD`, `Version=250601003`, `Key=korail1234567890` | 공통 응답 `strResult`, `h_msg_cd`, `h_msg_txt` | 대부분 DAO의 기본 파라미터 |
| `CommonService.getCommonCode` | code list, 화면 크기, 출발/도착일, 휴일 여부, OSVersion | 메뉴/팝업/로그인/결제/매크로/노출 설정 DTO | Intro bootstrap에서 로컬 저장 |
| `EncryptDao` | `type`, `values[]` | `encValueList[].encValue` | `DataActivity`가 로그인 JSON을 암호화 요청 |
| `DecryptDao` | `type`, `values[]` | `decValueList[].decValue` | RailPlus 카드번호 복호화 등에 사용 |
| `RailPlusService.getAutoCharge` | `jobDvCd`, `prepCrdNo` + 공통값 | `psbFlg` | 자동충전 가능/상태 플래그 |
| `FCMListenerServiceHandler` | FCM data payload 수신 | 로컬 MSGVo 변환/알림 또는 broker fetch | 서버 응답이 아니라 push payload |
| `PaymentActivity.onNewIntent` | `korailtalk://approve` query 전체 | 결제 Fragment `setEasyPaymentData(Bundle)` | direct REAL launch는 종료 |

## Open gaps

- `G0.b` Application superclass의 동작은 본 보고서에서 상세 분석하지 않았다.
- `C0815o.navigation(...)`, 각 target Activity의 extras 검증/권한 체크는 별도 deep dive가 필요하다.
- `DataActivity`가 외부로 전달하는 `korailtalklite://member_info`의 수신 앱/패키지 검증 여부는 이 APK 내부만으로 확정할 수 없다.
- `PaymentActivity`의 결제 Fragment(`b6.AbstractC1269e` 하위 클래스)별 easy payment callback 소비 방식은 추가 분석이 필요하다.
- SmartAlimi `AlimiInterface`의 token 등록, broker 통신 endpoint, 인증 방식은 본 범위에서 완전히 추적하지 않았다.
- NetFunnel SDK(`T6.*`)의 실제 요청 URL/path/body와 응답 파싱은 난독화되어 있어 별도 분석이 필요하다.
- Firebase/Google Ads SDK provider 초기화가 실제로 언제 어떤 네트워크 요청을 보내는지는 SDK 내부 조건과 런타임 환경에 의존한다. 로컬 manifest/코드로는 가능한 초기화 경로만 확인했다.
- `network_security_config`에 cleartext 허용된 SRT/개발 호스트가 실제 코드 경로에서 HTTP로 사용되는지는 추가 전수 검색/동적 확인이 필요하다. 본 작업에서는 라이브 호출을 하지 않았다.
- exported true이지만 intent-filter가 없는 Activity들의 외부 시작 입력 검증은 각 Activity별 추가 분석이 필요하다.

## 20-agent follow-up audit 보강

- Manifest metadata에는 split/runtime 초기화 단서도 포함된다. 확인된 값은 `requiredSplitTypes=base__abi,base__density`, `com.android.vending.splits=@xml/splits0`, optional uses-library `org.apache.http.legacy`, `androidx.camera.extensions.impl`, `android.ext.adservices`, `com.google.android.gms.version`, CameraX `MetadataHolderService.DEFAULT_CONFIG_PROVIDER`, DataTransport `CctBackendFactory`다.
- `KTApplication`의 superclass gap은 닫을 수 있다. `G0.b.attachBaseContext()`는 legacy MultiDex 설치용 `G0.a.install(this)`를 호출하며, bootstrap network/config side effect는 확인되지 않았다.
- SRT cleartext caveat은 더 좁게 봐야 한다. 예약 상수는 HTTPS이고 `BaseWebViewActivity`는 `http://*.srail.kr` main-frame URL 및 `http://teapp.srail.kr`, `http://app.srail.kr` body link를 HTTPS로 치환한다. 다만 SDK/runtime 생성 subresource URL은 정적 분석만으로 배제할 수 없다.
