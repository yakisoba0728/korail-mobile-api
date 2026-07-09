# 02. 네트워크 코어 아키텍처

## 분석 범위와 근거

이 문서는 로컬 디컴파일 산출물(`analysis/jadx/sources`)만 근거로 KORAIL Talk APK의 공통 네트워크 레이어를 정리한다. 운영 서비스 호출, 동적 트래픽 캡처, 런타임 응답 본문 추정은 수행하지 않았다. 따라서 아래 내용은 앱 코드가 요청을 조립하고 응답을 라우팅하는 방식에 대한 정적 분석이며, 서버가 실제로 반환하는 업무별 payload 형태는 발명하지 않는다.

주요 근거 파일은 다음과 같다.

| 영역 | 근거 |
|---|---|
| 공통 요청/응답 모델 | `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`, `BaseResponse.java` |
| DAO 공통 상태 | `analysis/jadx/sources/com/korail/talk/network/BaseDao.java`, `IBase*.java` |
| Retrofit 클라이언트 구성 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java`, `analysis/jadx/sources/retrofit/*` |
| 비동기 실행/오류 처리 | `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java`, `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java` |
| 쿠키/세션 전파 | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`, `network/dao/login/LoginDao.java` |
| DynaPath | `ExecuteDao.java`, `IntroActivity.java`, `kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java` |
| NetFunnel | `KTApplication.java`, `K4/g.java`, `T6/g.java`, `network/NetfunnelDao.java` |

## 전체 구조

앱의 내부 API 레이어는 Retrofit 1.x 스타일이다. 각 업무 DAO는 `BaseDao`를 상속하고, `BaseDao`는 `ExecuteDao`를 상속해 Retrofit 서비스 생성 기능을 공유한다. 호출자는 `BaseActivity` 또는 이를 감싼 Fragment base class를 통해 DAO를 실행한다.

핵심 흐름은 다음과 같다.

1. 화면이 업무별 `*Dao` 객체와 `BaseRequest` 하위 요청 객체를 만든다.
2. 화면이 `dao.setRequest(request)` 후 `executeDao(dao)`를 호출한다.
3. `BaseActivity.executeDao()`가 DAO에 callback owner(`IBase`)와 결과 라우터(`IBaseResult`)를 설정한다.
4. `BaseDaoHelper.HttpTask`가 `AsyncTask`로 `dao.executeDao()`를 백그라운드에서 호출한다.
5. DAO의 `executeDao()`는 `getService(Service.class)`로 Retrofit service proxy를 만들고, service interface의 `@GET/@POST` 메서드를 동기 호출한다.
6. 성공 또는 공통 오류 판정 후 `BaseActivity.onIntegrationResult()`가 최종적으로 `base.onReceive(dao)` 또는 `base.onReceiveError(dao, error)`를 호출한다.

근거:

- `BaseDao`는 `BaseRequest`, `BaseResponse`, `IBase`, `IBaseResult`, 로딩/다이얼로그/NetFunnel 상태를 보관한다. `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:7`
- `BaseActivity.executeDao(IBaseDao, IBase)`는 `setBase()`, `setINetworkResult()` 후 helper에 위임한다. `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:730`
- `BaseDaoHelper.HttpTask.doInBackground()`는 `Thread.sleep(100L)` 후 `this.mDao.setResponse(this.mDao.executeDao())`를 수행한다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:43`

## 공통 요청 필드

`BaseRequest`가 모든 공통 요청 객체의 기반이다. 생성자에서 다음 세 값을 기본값으로 세팅한다.

| 필드 | 값 | 의미 |
|---|---|---|
| `Device` | `AD` | Android 클라이언트 식별값 |
| `Version` | `250601003` | 앱/API 버전 상수 |
| `Key` | `korail1234567890` | 앱 내장 key 값 |

근거: `BaseRequest.ANDROID`, `APP_KEY`, `VERSION` 상수와 생성자 기본 세팅은 `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:7` 및 `:14`에 있다.

주의할 점은 모든 endpoint가 항상 세 필드를 모두 받는 것은 아니라는 점이다. 예를 들어 `CommonService.getStationData()`는 인자가 없고, `CommonService.authQRLocation()`은 `Device`, `Version`만 넘기며 `Key`를 넘기지 않는다. 반면 로그인, 예약, 결제 등 대부분의 form endpoint는 `Device`, `Version`, `Key`를 `@Field`로 받는다. `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java:23`, `:30`, `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17`

추가로 반복되는 요청 패턴은 다음과 같다.

| 패턴 | 설명 | 근거 |
|---|---|---|
| `@Field` form 필드 | `@FormUrlEncoded`가 붙은 POST에서 요청 body form field로 들어간다. | `retrofit/RequestBuilder.java:316` |
| `@FieldMap` | 승객/여정/좌석 등 반복 grid 데이터를 Map으로 펼친다. | `CertificationService.reservation(...)`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:48` |
| `@Query`/`@QueryMap` | GET URL query string으로 들어간다. | `retrofit/RequestBuilder.java:276`, `:299` |
| `Sid` | 열차 조회 계열에서 `BaseRequest`가 아니라 DAO가 별도로 `C0812l.getSid()`를 넣는다. | `TrainInquiryDao.executeDao()`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java:11` |

## 공통 응답 필드

`BaseResponse`는 모든 공통 응답 판정의 기준이 되는 세 필드를 가진다.

| Java getter | JSON 필드명 | 용도 |
|---|---|---|
| `getStrResult()` | `strResult` | 성공/실패 문자열. 상수로 `SUCC`, `FAIL`이 정의되어 있다. |
| `gethMsgCd()` | `h_msg_cd` | 서버 메시지 코드. 공통 오류 라우팅과 화면별 분기에서 사용된다. |
| `gethMsgTxt()` | `h_msg_txt` | 사용자 표시 메시지 또는 오류 메시지로 사용된다. |

근거: `BaseResponse`는 `SUCCESS="SUCC"`, `FAIL="FAIL"`을 정의하고, Gson field annotation으로 `h_msg_cd`, `h_msg_txt`, `strResult`를 매핑한다. `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:8`

업무별 응답 클래스는 대부분 `BaseResponse`를 상속해 추가 필드를 붙인다. 예: 예약 응답 `ReservationResponse`, 열차 조회 응답 `RsvInquiryResponse`, 환불 응답 `RefundResponse` 등이 `extends BaseResponse`로 선언되어 있다. 이 문서는 런타임 payload를 추정하지 않고, 공통 판정 필드만 다룬다.

## Retrofit annotation 동작

서비스 인터페이스는 `@GET`, `@POST`, `@FormUrlEncoded`, `@Field`, `@FieldMap`, `@Query`, `@QueryMap` 중심으로 작성되어 있다.

Retrofit 1.x 구현은 메서드 annotation을 읽어 HTTP method와 상대 path를 저장한다. 한 메서드에 HTTP method annotation은 하나만 허용되며, `@FormUrlEncoded`는 body가 있는 HTTP method에서만 허용된다. `analysis/jadx/sources/retrofit/RestMethodInfo.java:128`, `:170`, `:184`

요청 조립은 `RequestBuilder`가 담당한다.

- endpoint base URL 뒤에 service method의 상대 URL을 붙인다. `analysis/jadx/sources/retrofit/RequestBuilder.java:220`
- `@Query`와 `@QueryMap`은 URL query string으로 추가된다. `analysis/jadx/sources/retrofit/RequestBuilder.java:276`, `:299`, `:411`
- `@Field`와 `@FieldMap`은 `FormUrlEncodedTypedOutput`에 추가된다. `analysis/jadx/sources/retrofit/RequestBuilder.java:160`, `:316`, `:337`
- `@Header` 인자는 request header로 추가된다. `analysis/jadx/sources/retrofit/RequestBuilder.java:311`
- `@Body` 객체는 converter를 통해 body로 변환된다. `analysis/jadx/sources/retrofit/RequestBuilder.java:375`

앱 service 예시:

- `LoginService.login()`은 `/classes/com.korail.mobile.login.Login`에 `Device`, `Version`, `Key`, `txtMemberNo`, `txtPwd`, `txtInputFlg`, `checkValidPw`, `custId`, `etrPath`, `idx`를 form field로 보낸다. `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17`
- `CertificationService.reservation()`은 회원/비회원 예약 endpoint를 overload하며, `FieldMap`으로 승객/좌석/여정/객차 map을 함께 보낸다. `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:48`
- `CommonService.getCommonCode()`는 공통코드 요청에서 `Device`, `Version`, `Key`, code list, 화면 크기, 날짜, OS version을 form field로 보낸다. `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java:30`

## Retrofit 클라이언트와 타임아웃

`ExecuteDao.getDefaultRestAdapterBuilder()`는 모든 DAO의 Retrofit builder 공통 설정이다.

| 설정 | 값/동작 | 근거 |
|---|---|---|
| Log level | `I4.a.IS_DEBUG_LOG`이면 `FULL`, 아니면 `NONE` | `ExecuteDao.java:18` |
| Converter | `new GsonConverter(new e().create())` | `ExecuteDao.java:19` |
| Client | 익명 `UrlConnectionClient` subclass | `ExecuteDao.java:19` |
| Connect timeout | `60000` ms | `ExecuteDao.java:23` |
| Read timeout | `60000` ms | `ExecuteDao.java:24` |
| Endpoint | `S4.z.getSSLHost()` | `ExecuteDao.java:59` |

Retrofit에 포함된 기본 `UrlConnectionClient`도 connect/read timeout을 갖지만, 앱은 이를 subclass의 `openConnection()`에서 60초로 덮어쓴다. 기본 client가 request method, headers, content type, content length를 `HttpURLConnection`에 적용하는 근거는 `analysis/jadx/sources/retrofit/client/UrlConnectionClient.java:47` 및 `:61`에 있다.

Gson converter는 response body를 `InputStreamReader`로 읽어 `gson.fromJson(reader, type)`으로 역직렬화한다. `analysis/jadx/sources/retrofit/converter/GsonConverter.java:53`

## 호스트와 코어 hardcoded endpoint

기본 API host는 `ExecuteDao.getRestAdapterBuilder()`가 `S4.z.getSSLHost()`를 endpoint로 설정해 결정된다. `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:59`

빌드 상수 `CONNECT_SERVER="3"`은 `K4.g.SERVER_TYPE = EnumC5607a.fromCode("3")`로 이어지고, `S4.z.getSSLHost()`는 `REAL`일 때 `https://smart.letskorail.com`을 반환한다. `analysis/jadx/sources/G4/a.java:8`, `analysis/jadx/sources/K4/g.java:89`, `analysis/jadx/sources/S4/z.java:46`

코어 네트워크 코드가 직접 하드코딩한 endpoint/host 목록은 다음으로 제한해 확인했다.

### API/Web host 선택

| 용도 | 코드상 값 |
|---|---|
| REAL API/Web | `https://smart.letskorail.com` |
| TEST API/Web | `https://dev3.letskorail.com` |
| STAGING API/Web | `https://dev2.letskorail.com` |
| DEV fallback API/Web | `https://mobiledev.letskorail.com` |
| REAL/STAGING multi-language web | `https://www.korail.com` |
| non-real push 일부 | `dev.letskorail.com`, `smartbeta.letskorail.com` |

근거: `S4.z.getSSLHost()`, `getWebHost()`, `getMultiLangWebHost()`, `getPushAddress()`는 `analysis/jadx/sources/S4/z.java:36` 및 `:41`, `:46`, `:51`에 있다.

### DynaPath header 주입 대상 path

`ExecuteDao.openConnection()`은 `I4.a.IS_MACRO_ACTIVE`가 true일 때 요청 URL이 아래 path를 포함하는지 검사하고, 일치하면 `x-dynapath-m-token` 헤더를 주입한다.

| Path |
|---|
| `/classes/com.korail.mobile.certification.TicketReservation` |
| `/classes/com.korail.mobile.nonMember.NonMemTicket` |
| `/classes/com.korail.mobile.seatMovie.ScheduleView` |
| `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` |
| `/classes/com.korail.mobile.trn.prcFare.do` |
| `/classes/com.korail.mobile.login.Login` |

근거: path 배열과 `setRequestProperty("x-dynapath-m-token", token)`은 `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:25`부터 `:48`에 있다.

### NetFunnel host/action id

| 구분 | 값 |
|---|---|
| protocol | `https` |
| host | `nf.letskorail.com` |
| port | `443` |
| service id | `service_1` |
| 일반 조회 action | `act_8` |
| 성수기 조회 action | `act_8_2` |
| 예약 action | `act_14` |
| 결제 action | `act_18` |
| 예약내역 action | `act_21` |
| 환불 action | `act_22` |
| 상품 action | `act_6` |
| 테스트 action | `act_4` |

근거: 앱 초기화의 NetFunnel 기본 host/port/service/action 설정은 `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78`부터 `:85`, action id 상수는 `analysis/jadx/sources/K4/g.java:43`부터 `:51`에 있다.

개별 업무 API endpoint 전체 목록은 service interface가 하드코딩하지만, 이 코어 보고서에는 재열거하지 않는다. 전체 Retrofit endpoint inventory는 `docs/api-endpoints.md`에 정리되어 있다.

## CookieManager와 JSESSIONID 전파

앱 시작 시 `KTApplication`은 Java 표준 `CookieManager`를 만들고 `CookiePolicy.ACCEPT_ALL`을 설정한 뒤 `CookieHandler.setDefault(cookieManager)`로 등록한다. Retrofit의 `UrlConnectionClient`는 `HttpURLConnection`을 사용하므로 이 기본 `CookieHandler`가 네이티브 HTTP 쿠키 저장소 역할을 한다. 근거: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:72`

로그인 성공 경로는 다음과 같다.

1. `LoginDao.executeDao()`가 `LoginService.login()`을 호출한다.
2. 로그인 service 호출 후 `KTApplication.getInstance().setSessionId()`를 호출한다.
3. `KTApplication.getCookie()`가 기본 `CookieHandler`의 cookie store에서 이름이 `JSESSIONID`인 쿠키를 찾는다.
4. `setSessionId()`가 Android WebView `CookieManager`에 `z.getSSLHost()` 기준으로 `JSESSIONID=<value>`를 설정하고 `flush()`한다.

근거:

- `LoginDao.executeDao()`의 login 호출과 `setSessionId()` 호출: `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginDao.java:236`
- `KTApplication.getCookie()`의 `JSESSIONID` 검색: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:105`
- WebView cookie store에 설정: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:129`

즉 Retrofit/`HttpURLConnection` 로그인에서 받은 `JSESSIONID`가 WebView 세션으로 복사되는 방향의 동기화가 명시되어 있다. 반대로 WebView 쿠키를 Java `CookieHandler`로 되돌리는 공통 경로는 이 코어 코드에서는 확인되지 않았다.

WebView 계열은 별도로 Android WebView `CookieManager`를 활성화한다. `BaseWebViewActivity.Z0()`는 cookie와 third-party cookie를 허용하고, 일부 JSON POST WebView 흐름은 `Set-Cookie` 응답 헤더를 WebView cookie store에 직접 반영한다. `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:928`, `:959`

## DynaPath header injection hook

DynaPath는 두 단계로 연결된다.

1. `IntroActivity.onCreate()`가 `DynaPathMobileSDK.Companion.initialize(getApplication())`를 호출한다. `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:657`
2. 공통코드 응답 처리 중 `isMacroEnable` 값이 `Y`이면 `I4.a.IS_MACRO_ACTIVE`를 true로 설정한다. 기본값은 false다. `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:740`, `analysis/jadx/sources/I4/a.java:13`

이후 모든 Retrofit 요청은 `ExecuteDao`의 `UrlConnectionClient.openConnection()` hook을 거친다. hook은 macro 활성화 상태와 요청 URL path를 검사한 뒤, 대상 path에 한해 `DynaPathMobileSDK.Companion.generate()`로 token을 생성하고 `x-dynapath-m-token` request header를 세팅한다. `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:25`

DynaPath SDK의 `generate()`는 SDK가 초기화되지 않았거나 token 생성 객체가 없으면 `DynaPathException`을 던진다. 앱 hook은 이 예외를 잡아 로그만 남기고 요청 자체는 계속 반환한다. `analysis/jadx/sources/kr/scripters/dynapath/sdk/android/DynaPathMobileSDK.java:21`, `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:44`

## 오류 응답 처리

오류 처리는 크게 transport/Retrofit 예외, DynaPath 403 응답, 서버 공통 응답 코드 판정으로 나뉜다.

### RetrofitError와 DynaPath 403

`BaseDaoHelper.HttpTask.doInBackground()`는 `RetrofitError`를 잡으면 기본적으로 `R4.b` 예외 객체를 만든다. `R4.b`의 기본 메시지는 네트워크 연결 상태 안내 문구다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:50`, `analysis/jadx/sources/R4/b.java:4`

특수 처리:

- Retrofit error message에 `403`과 `forbidden`이 포함되면 response header를 순회한다.
- header 이름이 `DynaPath-Result`이고 값이 음수이면 error body를 문자열로 읽는다.
- 읽은 body를 JSON으로 파싱하고 `message` 필드가 있으면 그 값을 `dao.setMacroShowDialog()`에 저장한다.
- 이 경우 즉시 DAO를 반환해 이후 UI 단계에서 macro dialog로 처리되게 한다.

근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:54`부터 `:91`

이 문서는 실제 403 body 형태를 예시로 만들지 않는다. 코드가 `message` 키를 찾는다는 사실만 확인했다.

### BaseResponse 기반 공통 판정

`BaseActivity.onIntegrationResult()`는 Retrofit 예외가 없으면 `dao.getResponse()`에서 `strResult`, `h_msg_cd`, `h_msg_txt`를 읽어 공통 오류를 판정한다. 핵심 규칙은 다음과 같다.

| 조건 | 처리 |
|---|---|
| check service/train calendar에서 `strResult=FAIL` 또는 `h_msg_cd=SEMGTK` | `R4.b`로 처리 |
| `h_msg_cd=P058` | 자동 로그인 설정에 따라 `R4.d` 또는 `R4.c`로 처리 |
| `h_msg_cd=SUPDATE` | 업데이트 dialog 표시 |
| `h_msg_cd=WRC000288` 또는 `strResult=FAIL` | `h_msg_txt`를 일반 오류 메시지로 사용. `<br>`은 줄바꿈으로 치환 |
| 오류가 없다고 판단 | `base.onReceive(dao)` 호출 |
| 일반 오류 | dialog 처리 후 `base.onReceiveError(dao, error)` 호출 |

근거: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:599`부터 `:649`

오류 dialog 표시 여부는 DAO 상태로 조절된다.

- `dao.setNotShowDialog(true)`면 공통 오류 dialog를 표시하지 않는다.
- `dao.setErrorMsgCdNotShowDialog(code)` 또는 list로 등록된 `h_msg_cd`는 dialog를 생략한다.
- `dao.setFinishView(true)`는 오류 dialog 버튼 후 화면 종료 여부에 영향을 준다.

근거: `BaseDao`의 상태 필드/메서드는 `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:13`, `:80`, `:84`, `:108`, `:123`; dialog 생략 로직은 `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:326`에 있다.

### Null response 관련 주의

일반 `BaseActivity.onIntegrationResult()`는 먼저 `BaseResponse response = iBaseDao.getResponse();` 후 바로 getter를 호출한다. 위젯용 `WidgetService`/`WidgetReceiver`에도 response null 체크 분기는 보이지만, 그 전에 이미 `response.getStrResult()`와 `response.gethMsgCd()`를 호출한다. 따라서 Retrofit 예외가 `aVar`로 전달되는 일반 실패는 별도 경로로 처리되지만, DAO가 null response를 정상 경로로 넣는 경우에는 Activity/위젯 공통으로 NPE 가능성이 남는다. 근거: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:604`, `analysis/jadx/sources/com/korail/talk/provider/WidgetService.java:164`

## 호출자가 callback을 받는 방식

공통 callback 인터페이스는 세 개다.

| 인터페이스 | 핵심 메서드 |
|---|---|
| `IBase` | `executeDao`, `executeRetryDao`, `isFinishing`, `onCancelDao`, `onReceive`, `onReceiveError` |
| `IBaseDao` | `executeDao`, request/response getter/setter, dialog/NetFunnel 상태 getter/setter |
| `IBaseResult` | `onIntegrationResult(IBaseDao, R4.a)` |

근거: `analysis/jadx/sources/com/korail/talk/network/IBase.java:6`, `IBaseDao.java:6`, `IBaseResult.java:6`

일반 Activity 경로:

1. 화면이 `BaseActivity.executeDao(dao)`를 호출한다.
2. `BaseActivity`가 DAO의 `base`를 화면 자신 또는 Fragment로 설정하고, `INetworkResult`를 `BaseActivity` 자신으로 설정한다.
3. `BaseDaoHelper`가 네트워크 작업 완료 후 `dao.getINetworkResult().onIntegrationResult(dao, exception)`을 호출한다.
4. `BaseActivity.onIntegrationResult()`가 공통 오류를 처리한 뒤, 원래 callback owner인 `dao.getBase()`에 `onReceive()` 또는 `onReceiveError()`를 호출한다.

근거: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:730`, `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101`, `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:639`

Fragment 경로는 `com.korail.talk.view.base.a`가 `IBase`를 구현하고, 내부에서 host `BaseActivity.executeDao(dao, this)`로 위임한다. 따라서 최종 callback은 Fragment의 `onReceive()`/`onReceiveError()` override로 돌아간다. `analysis/jadx/sources/com/korail/talk/view/base/a.java:41`, `:156`, `:216`

위젯 경로는 Activity 없이 `WidgetService`/`WidgetReceiver`가 직접 `IBase`와 `IBaseResult`를 구현한다. 이 경우도 `setBase(this)`, `setINetworkResult(this)` 후 `BaseDaoHelper`에 위임하는 동일한 형태다. `analysis/jadx/sources/com/korail/talk/provider/WidgetService.java:117`, `analysis/jadx/sources/com/korail/talk/provider/WidgetReceiver.java:114`

## NetFunnel callback hook

NetFunnel은 코어 Retrofit client에 자동 삽입되는 header 방식이 아니라, 화면 코드가 NetFunnel `BEGIN()`을 먼저 호출하고 callback에서 실제 DAO 실행을 이어가는 구조다.

초기화:

- `KTApplication.g()`가 protocol `https`, host `nf.letskorail.com`, port `443`, service id `service_1`, 기본 action id `act_8`, timeout `3`을 설정한다. `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78`
- action id 상수는 `K4.g`에 있다. `analysis/jadx/sources/K4/g.java:43`

실행:

- `T6.g.BEGIN(serviceId, actionId, listener1, listener2)`는 전역 instance의 service/action을 세팅하고 listener 두 개를 등록한 뒤 `Begin()`을 호출한다. `analysis/jadx/sources/T6/g.java:185`
- `Begin()`은 bypass가 아니면 별도 thread를 시작한다. thread는 `GET_TID_CHK_ENTER`, `CHK_ENTER`, TTL sleep/continue interval을 반복하고 상태를 listener와 handler에 전달한다. `analysis/jadx/sources/T6/g.java:57`, `:328`
- listener callback signature는 `netfunnelMessage(g, d)`다. `analysis/jadx/sources/T6/g.java:171`

후처리:

- DAO에 `NetfunnelDao`가 연결되어 있으면 `BaseDaoHelper.onPostExecute()`가 공통 결과 callback 전에 `netfunnelDao.runRunner()`를 호출한다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:105`
- `NetfunnelDao.runRunner()`는 main `Handler`에 post하여 NetFunnel dialog를 닫고, loading dialog를 닫고, `T6.g.END()`를 호출한 뒤 선택적으로 runner를 실행한다. `analysis/jadx/sources/com/korail/talk/network/NetfunnelDao.java:23`

예시:

- 예약내역 화면은 `TicketRsvHistoryDao`에 `new NetfunnelDao(...)`를 연결하고 실행한다. `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:302`
- 메인 예매 화면은 성수기 여부에 따라 `act_8` 또는 `act_8_2`를 선택해 `T6.g.BEGIN()`을 호출한다. `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:745`

## 취소와 생명주기 정리

`BaseDaoHelper`는 실행 중인 `HttpTask`를 하나 보관한다.

- `executeDao()`는 새 `HttpTask`를 만들고 `execute()`한다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:142`
- `onCancelDao()`는 task가 있으면 `cancel(true)` 후 loading dialog를 닫는다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:149`
- `onDestroy()`는 cancel, task null 처리, dialog dismiss/null 처리를 수행한다. `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:157`
- `BaseActivity.onDestroy()`는 helper의 `onDestroy()`를 호출한다. `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:584`

단, `AsyncTask.cancel(true)`가 이미 시작된 `dao.executeDao()` 내부의 `HttpURLConnection` 호출을 즉시 중단한다는 별도 보장은 이 코드만으로는 확인되지 않는다. 코어 코드는 취소 상태 확인보다 로딩 UI 정리와 helper 참조 정리에 초점을 둔다.

## 핵심 관찰

- 네트워크 공통 계층은 `BaseRequest`/`BaseResponse`를 얇게 두고, 업무별 DAO가 Retrofit service 메서드 호출 인자를 직접 펼치는 구조다.
- 공통 요청값은 `Device=AD`, `Version=250601003`, `Key=korail1234567890`이지만 endpoint마다 `Key` 포함 여부가 다르다.
- 공통 응답 판정은 `strResult`, `h_msg_cd`, `h_msg_txt` 세 필드에 강하게 의존한다.
- Retrofit client는 Gson + `HttpURLConnection` 기반이며 앱이 connect/read timeout을 60초로 강제한다.
- 로그인 후 Java `CookieHandler`의 `JSESSIONID`를 Android WebView `CookieManager`로 복사해 native API 세션과 WebView 세션을 연결한다.
- DynaPath는 모든 요청에 붙는 것이 아니라 서버 플래그와 특정 path 배열 조건을 통과한 요청에만 `x-dynapath-m-token`을 붙인다.
- NetFunnel은 Retrofit interceptor가 아니라 화면 레벨의 선행 queue/callback hook이며, 일부 DAO 완료 후 `NetfunnelDao`가 dialog 종료와 `T6.g.END()`를 수행한다.

## 20-agent follow-up audit 보강

- 오류 callback은 공통적으로 `base.onReceiveError()`로 수렴한다고 보면 안 된다. `R4.b`, `R4.c`, `R4.d`는 dialog/login/session flow에서 소비되고, generic `R4.a`만 기본 error callback으로 떨어진다. 특수하게 `dao_verify_maas_status`의 `S198`은 `base.onReceiveError(iBaseDao, null)`을 직접 호출한다.
- DynaPath 403에서 `DynaPath-Result`가 음수이면 `mException=R4.b`와 `macroShowDialog`가 저장되고 response가 비어 있을 수 있다. `BaseActivity`가 macro dialog를 표시하고 exception을 지운 뒤 null response DAO를 `base.onReceive(dao)`로 넘길 수 있어, 실제 null 처리 여부는 화면별 gap이다. 403 body가 malformed/non-JSON이면 `RuntimeException`으로 재던져진다.
- NetFunnel message callback은 `N4.e`가 `g.e.netfunnelMessage()`로 dialog/progress를 갱신하고, 실제 업무 재개는 화면의 `Handler.handleMessage()` overload에서 이어진다. `BaseDaoHelper`는 `NetfunnelDao.runRunner()` 호출 직후 `onIntegrationResult()`를 부르지만, `runRunner()` 자체가 `Handler`에 일을 post하므로 정리는 비동기다.
- 네트워크 lifecycle 세부값: 앱은 `http.keepAlive=false`를 설정한다. `clearCookie()`는 WebView cookie를 제거하고 Java `CookieManager`를 새로 만든다. `setSessionId()`에는 null guard가 없다. endpoint URL은 default builder가 아니라 `getRestAdapterBuilder()` 호출 때 결정된다. `BaseDao.isPending()`은 loading show/dismiss 제어값이고 `executeDao()` 실행 여부를 막는 값은 아니다.
