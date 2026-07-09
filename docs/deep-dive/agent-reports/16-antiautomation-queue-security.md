# 안티오토메이션/대기열 보안 정적 분석 보고서

## 분석 범위와 기준

이 문서는 APK 디컴파일 산출물 기준의 정적 분석이다. 운영 서버 호출, 동적 트래픽 캡처, NetFunnel/DynaPath 우회 검증은 수행하지 않았다. 목적은 클라이언트에 관찰되는 대기열, 매크로 탐지 토큰, 보안 민감 엔드포인트, 네트워크 보안 설정, WebView 신뢰 경계를 구조적으로 정리하는 것이다.

주요 근거는 `analysis/jadx/sources`와 `analysis/jadx/resources` 아래의 디컴파일 Java/XML이다. 디컴파일러가 난독화된 클래스명과 일부 제어 흐름을 원본과 다르게 표현할 수 있으므로, 아래 내용은 "클라이언트에서 관찰 가능한 방어 동작"으로 한정한다.

## 핵심 결론

- 앱 시작 시 `KTApplication`이 NetFunnel 기본 속성을 `https`, `nf.letskorail.com`, SSL 기본 포트, `service_1`, `act_8`, timeout `3`으로 설정한다. 근거: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78-86`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:119-126`.
- DynaPath SDK는 `IntroActivity.onCreate()`에서 초기화되고, 서버 공통 코드 응답의 `isMacroEnable`이 `Y`일 때만 `I4.a.IS_MACRO_ACTIVE`가 켜진다. 근거: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:657-665`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:691-742`, `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonCodeDao.java:367-407`.
- DynaPath 토큰 헤더는 모든 요청에 붙지 않는다. `ExecuteDao`의 URL 부분 문자열 목록에 매칭되는 6개 경로에 한해 `x-dynapath-m-token`을 생성해 설정한다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-56`.
- NetFunnel은 Retrofit/HTTP 계층의 범용 인터셉터가 아니라 예약/조회/결제/예약내역 등 UI 플로우별 `T6.g.BEGIN(service_1, act_*)` 호출로 진입한다. DAO 완료 뒤 `BaseDaoHelper`가 연결된 `NetfunnelDao.runRunner()`를 호출하고, 이 안에서 다이얼로그 종료와 `T6.g.END()`가 수행된다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101-109`, `analysis/jadx/sources/com/korail/talk/network/NetfunnelDao.java:23-45`.
- 루트/변조 차단 로직은 명확히 관찰되지 않았다. 다만 Android manifest `queries`에는 여러 루팅 앱 패키지명이 선언되어 있어 Android 11+ 패키지 가시성을 열어둔 흔적이 있다. 근거: `analysis/jadx/resources/AndroidManifest.xml:80-110`. 실제 `PackageManager` 기반 탐지/차단 호출은 본 범위 검색에서 확인되지 않았다.
- API 기본 호스트는 `https://smart.letskorail.com` 계열이며, 앱 자체의 Retrofit 경로는 기본 플랫폼 TLS를 사용한다. 별도 인증서 핀닝 또는 커스텀 trust-all 구현은 코레일 앱 소유 패키지에서 확인되지 않았다. 근거: `analysis/jadx/sources/S4/z.java:46-54`, `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-64`.
- `network_security_config`는 특정 도메인/IP에 cleartext를 허용한다. WebView SRT 예약 흐름에는 `http://*.srail.kr` 링크를 HTTPS로 치환하는 보조 로직이 있으나, 네트워크 보안 설정상 일부 cleartext 허용 표면은 남아 있다. 근거: `analysis/jadx/resources/res/xml/network_security_config.xml:1-12`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:921-935`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:955-956`.

## 초기화 흐름

### 앱 전역 초기화

`KTApplication.onCreate()`는 내부 초기화 `d()`, NetFunnel 설정 `g()`, 폰트/임시폴더/알림 채널/Kakao SDK 초기화를 순차 수행한다. `d()`는 앱 인스턴스 저장, 쿠키 매니저 초기화, HTTP keep-alive 비활성화, DB/helper 초기화를 포함한다. 근거: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:56-66`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:72-76`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:92-94`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:119-126`.

NetFunnel 기본 속성은 `T6.h.getDefaultInstance()`에 설정된다.

| 항목 | 값 | 근거 |
|---|---:|---|
| protocol | `https` | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78-82` |
| host | `nf.letskorail.com` | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78-82` |
| port | SSL 기본 포트 | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78-83` |
| service id | `service_1` | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:83`, `analysis/jadx/sources/K4/g.java:43-51` |
| default action id | `act_8` | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:84`, `analysis/jadx/sources/K4/g.java:43-51` |
| timeout | `3` | `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:85` |

### DynaPath 초기화와 매크로 플래그

`IntroActivity.onCreate()`는 `DynaPathMobileSDK.Companion.initialize(getApplication())`를 호출하고, 예외 발생 시 코드와 메시지를 로그에 남긴다. 이후 공통 코드 DAO 응답을 처리하는 `onReceive()`에서 `commonCodeResponse.getData().getIsMacroEnable()` 값이 `Y`이면 `I4.a.IS_MACRO_ACTIVE`를 true로 설정한다. 기본값은 false이다. 근거: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:657-665`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:691-742`, `analysis/jadx/sources/I4/a.java:7-15`.

이 구조상 DynaPath 헤더 부착은 클라이언트 단독 결정이 아니라, 서버가 내려주는 common-code feature flag에 종속된다. 공통 코드 응답 데이터 모델에는 `isMacroEnable` 필드와 getter가 있다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonCodeDao.java:367-407`.

## Retrofit/HTTP 요청 흐름

모든 DAO는 `BaseDao`/`ExecuteDao` 계층을 통해 Retrofit 서비스를 만든다. `ExecuteDao.getDefaultRestAdapterBuilder()`는 Gson converter와 `UrlConnectionClient`를 설정하고, `openConnection()`에서 연결/읽기 timeout을 각각 60초로 둔다. endpoint는 `z.getSSLHost()`로 설정된다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-24`, `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:59-64`, `analysis/jadx/sources/S4/z.java:46-54`.

기본 요청 필드는 `BaseRequest`에서 `Device=AD`, `Version=250601003`, `Key=korail1234567890`로 초기화된다. WebView 기본 파라미터도 같은 값의 문자열 상수를 사용한다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:6-18`, `analysis/jadx/sources/K4/g.java:11`.

응답 공통 필드는 `strResult`, `h_msg_cd`, `h_msg_txt`이다. `BaseActivity.onIntegrationResult()`는 `FAIL`, 특정 메시지 코드, 매크로 다이얼로그 메시지 등을 기준으로 정상 수신/오류 다이얼로그/오류 콜백을 분기한다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:7-30`, `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:599-649`.

## DynaPath 토큰 헤더 흐름

`ExecuteDao.openConnection()`의 흐름은 다음과 같다.

1. Retrofit 요청 URL을 받는다.
2. timeout을 설정한다.
3. `I4.a.IS_MACRO_ACTIVE`가 true인지 확인한다.
4. 하드코딩된 6개 경로 중 하나가 `request.getUrl().contains(...)`로 매칭되는지 확인한다.
5. 매칭 시 `DynaPathMobileSDK.Companion.generate()`로 토큰을 생성한다.
6. 생성 성공 시 `x-dynapath-m-token` 요청 헤더를 설정한다.
7. DynaPath 예외가 발생하면 코드와 메시지를 로그에 남기고 요청 자체는 계속 반환한다.

근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:21-55`.

헤더명은 `x-dynapath-m-token`이다. 토큰 값 생성 방식은 SDK 내부에 위임되어 있으며, 디컴파일된 앱 코드에는 토큰 포맷이나 검증 로직이 없다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:43-50`.

### DynaPath 헤더 부착 대상

| 메서드 | 경로 | 기능 추정 | 근거 |
|---|---|---|---|
| POST | `/classes/com.korail.mobile.certification.TicketReservation` | 회원/인증 기반 승차권 예약 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:52-62` |
| POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | 비회원 승차권 처리/예약 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:48-58` |
| POST | `/classes/com.korail.mobile.seatMovie.ScheduleView` | 열차 조회/좌석 관련 조회 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12-14` |
| POST | `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | 상품/특수 조회 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20-22` |
| POST | `/classes/com.korail.mobile.trn.prcFare.do` | 운임 계산 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:24-26` |
| POST | `/classes/com.korail.mobile.login.Login` | 로그인 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17-19` |

관찰 가능한 제한점: 이 목록은 문자열 포함 매칭이므로 클라이언트 코드 기준으로는 위 경로에만 헤더가 붙는다. 서버가 다른 엔드포인트에서 DynaPath를 별도 요구하는지는 정적 분석만으로 확인할 수 없다.

## DynaPath 오류/본문 파싱

`BaseDaoHelper.HttpTask.doInBackground()`는 Retrofit 실행 중 `RetrofitError`를 잡는다. 오류 메시지에 `403`과 `forbidden`이 포함되면 응답 헤더를 순회하고, `DynaPath-Result` 헤더가 존재하며 정수값이 0보다 작으면 응답 body를 문자열로 읽는다. body JSON에 `message` 필드가 있으면 해당 값을 `mDao.setMacroShowDialog()`에 저장한다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:50-91`.

UI 표시 단계는 `BaseActivity.onIntegrationResult()`에서 처리된다. 네트워크 예외가 있고 `macroShowDialog`가 비어 있지 않으면 일반 오류 대신 다이얼로그에 macro 메시지를 표시하고 오류 객체를 null로 바꾼다. 근거: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:599-649`.

주의할 점은 body가 JSON이 아니거나 `message` 파싱이 실패하면 `RuntimeException`이 던져질 수 있다는 점이다. 이는 방어 흐름의 사용자 표시 견고성 측면에서 관찰되는 한계이며, 서버 정책 자체의 우회 가능성을 의미하지 않는다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:80-89`.

## NetFunnel 대기열 제어 흐름

NetFunnel action id는 `K4.g`에 상수화되어 있다.

| 상수 | 값 | 의미/호출 표면 |
|---|---:|---|
| `NETFUNNEL_SERVER_ID` | `service_1` | 공통 service id |
| `NETFUNNEL_ACTION_ID` | `act_8` | 일반 열차 조회/기본 action |
| `NETFUNNEL_ACTION_ID_PEAKSEASON` | `act_8_2` | 성수기 조회 |
| `NETFUNNEL_ACTION_RESERVE_ID` | `act_14` | 예약 실행 |
| `NETFUNNEL_ACTION_PAY_ID` | `act_18` | 결제 |
| `NETFUNNEL_ACTION_RESERVED_ID` | `act_21` | 예약내역 |
| `NETFUNNEL_ACTION_REFUND_ID` | `act_22` | 환불 상수는 존재하나 Java 호출 지점은 본 검색에서 확인되지 않음 |
| `NETFUNNEL_ACTION_PRODUCT_ID` | `act_6` | 상품/특수 조회 |
| `NETFUNNEL_ACTION_TEST_ID` | `act_4` | 테스트 상수 |

근거: `analysis/jadx/sources/K4/g.java:43-51`.

### 주요 호출 지점

| action | 호출 지점 | 동작 |
|---|---|---|
| `act_8` / `act_8_2` | `MainBookingActivity.T0()` | 간편구매 날짜가 성수기인지에 따라 일반/성수기 action 선택 후 `BEGIN` 호출 |
| `act_8` / `act_8_2` / `act_6` | `b5.c.s2()` | 일반/상품/4인동반석 조회에서 상품 요청이면 `act_6`, 아니면 성수기 여부에 따라 `act_8_2` 또는 `act_8` |
| `act_14` | `DirectInquiryActivity` | 예약대기/일반예약/공무원 인증 전 예약 진입에서 `BEGIN` 호출 |
| `act_18` | `B6.C1270f`, `B6.AbstractC1269e` | 결제 버튼/결제 단계에서 `BEGIN` 호출 |
| `act_21` | `ReservedTicketActivity.onCreate()` | 예약내역 화면 초기 로딩에서 `BEGIN` 호출 |
| `act_8` | `NetfunnelTestActivity` | 테스트 액티비티에서 반복 호출 |

근거: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:745-762`, `analysis/jadx/sources/b5/c.java:430-450`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:430-499`, `analysis/jadx/sources/B6/C1270f.java:223-232`, `analysis/jadx/sources/B6/AbstractC1269e.java:1095-1107`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:535-554`, `analysis/jadx/sources/com/korail/talk/test/NetfunnelTestActivity.java:50-55`.

### DAO 완료 후 종료 처리

`BaseDao`는 선택적으로 `NetfunnelDao`를 보관한다. `BaseDaoHelper.HttpTask.onPostExecute()`는 DAO에 연결된 NetFunnel DAO가 있으면 `runRunner()`를 호출한다. `runRunner()`는 NetFunnel 다이얼로그와 로딩 다이얼로그를 닫고 `T6.g.END()`를 호출한 뒤 후속 `Runnable`을 실행한다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:15-16`, `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:39-42`, `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:104-106`, `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101-109`, `analysis/jadx/sources/com/korail/talk/network/NetfunnelDao.java:23-45`.

이 구조는 대기열이 특정 업무 플로우의 사용자 동작 앞단에 결합되어 있음을 보여준다. Retrofit 계층에서 action id를 자동 주입하는 범용 로직은 관찰되지 않았다.

## 보호/민감 엔드포인트 목록

아래 목록은 클라이언트에서 직접 확인된 DynaPath 또는 NetFunnel 관련 보호 표면과, 같은 플로우에서 민감도가 높은 예약/결제/환불/인증 API를 정리한 것이다. "보호 관찰" 열은 클라이언트 코드에서 확인된 방어 결합만 뜻한다.

| 영역 | 엔드포인트 | 보호 관찰 | 근거 |
|---|---|---|---|
| 로그인 | `POST /classes/com.korail.mobile.login.Login` | DynaPath 헤더 대상 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17-19` |
| 회원 인증 등록/삭제 | `POST /classes/com.korail.mobile.login.loginAthnReg.do`, `POST /classes/com.korail.mobile.login.loginAthnRmv.do` | 민감 인증 API이나 DynaPath 목록에는 없음 | `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:21-27` |
| 조회 | `POST /classes/com.korail.mobile.seatMovie.ScheduleView` | DynaPath 헤더 대상, NetFunnel `act_8`/`act_8_2` 플로우와 연관 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12-14`, `analysis/jadx/sources/b5/c.java:430-450` |
| 상품 조회 | `POST /classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | DynaPath 헤더 대상, NetFunnel `act_6` 플로우와 연관 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20-22`, `analysis/jadx/sources/b5/c.java:439-450` |
| 운임 | `POST /classes/com.korail.mobile.trn.prcFare.do` | DynaPath 헤더 대상 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:24-26` |
| 예약 | `POST /classes/com.korail.mobile.certification.TicketReservation` | DynaPath 헤더 대상, 예약 플로우 NetFunnel `act_14`와 연관 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:52-62`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:430-499` |
| 비회원 예약/발권 | `POST /classes/com.korail.mobile.nonMember.NonMemTicket` | DynaPath 헤더 대상 | `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:27`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:48-58` |
| 좌석배정/예약변경 | `POST /classes/com.korail.mobile.reservation.seatAssign.do`, `POST /classes/com.korail.mobile.reservation.tripChgPrsC.do` | 민감 예약 API이나 DynaPath 목록에는 없음 | `analysis/jadx/sources/com/korail/talk/network/dao/reservation/ReservationService.java:24-30` |
| 예약내역 | `GET /classes/com.korail.mobile.reservation.ReservationView` | NetFunnel `act_21` 화면 플로우와 연관 | `analysis/jadx/sources/com/korail/talk/network/dao/reservation/ReservationService.java:21-22`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:535-554` |
| 결제 | `POST /classes/com.korail.mobile.payment.ReservationPayment` | NetFunnel `act_18` 결제 플로우와 연관 | `analysis/jadx/sources/com/korail/talk/network/dao/payment/PaymentService.java:12-14`, `analysis/jadx/sources/B6/C1270f.java:223-232`, `analysis/jadx/sources/B6/AbstractC1269e.java:1095-1107` |
| 간편/외부결제 | `POST /classes/com.korail.mobile.pay.*` 계열 | 결제 민감 API이나 NetFunnel 결합은 결제 UI 플로우 단위로 관찰 | `analysis/jadx/sources/com/korail/talk/network/dao/pay/PayService.java:22-67`, `analysis/jadx/sources/B6/AbstractC1269e.java:1095-1107` |
| 환불 | `POST /classes/com.korail.mobile.refunds.*` 계열 | `act_22` 상수는 존재하나 Java `BEGIN` 호출 지점은 본 검색에서 확인되지 않음 | `analysis/jadx/sources/K4/g.java:47`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:15-33` |
| 정부/공공 인증 | `GET /classes/com.korail.mobile.pbep.toknCre.do`, `GET /classes/com.korail.mobile.pbep.sttChck.do` | CSRF/token 상태 확인 API로 보이나 DynaPath 목록에는 없음 | `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:39-43` |

## 루트/디버그/변조 체크 관찰

### 관찰된 항목

- Manifest `queries`에 `com.noshufou.android.su`, `eu.chainfire.supersu`, `com.topjohnwu.magisk`, `com.kingroot.kinguser`, `com.kingo.root` 등 루팅 관련 패키지명이 선언되어 있다. 이는 Android 11 이상에서 해당 패키지 조회 가능성을 열어두는 선언이다. 근거: `analysis/jadx/resources/AndroidManifest.xml:80-110`.
- 앱 manifest에는 `android:allowBackup="false"`와 `android:networkSecurityConfig="@xml/network_security_config"`가 있다. 명시적 `android:debuggable` 속성은 관찰되지 않았다. 근거: `analysis/jadx/resources/AndroidManifest.xml:138-148`.
- 디버그 로그 플래그 `I4.a.IS_DEBUG_LOG`는 빌드 상수 `G4.a.IS_DEBUG_LOG`에서 온다. WebView 디버깅은 이 플래그가 true일 때도 `setWebContentsDebuggingEnabled(false)`로 설정된다. 근거: `analysis/jadx/sources/I4/a.java:7-15`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1097-1106`.

### 관찰되지 않은 항목

본 범위의 정적 검색에서 다음은 확인되지 않았다.

- 루팅 앱 패키지 조회 결과를 이용해 앱 기능을 차단하는 명확한 코드 경로
- `su` 바이너리, Magisk, Xposed, Frida 등 런타임 아티팩트 탐지 로직
- Play Integrity/SafetyNet 기반 무결성 검증 호출
- 앱 서명/해시를 런타임에 비교해 변조를 차단하는 명확한 코드 경로

이는 "존재하지 않음"의 증명이 아니라, 디컴파일 산출물과 키워드 기반 정적 추적에서 명확한 방어 제어 흐름이 관찰되지 않았다는 의미다.

## TLS와 네트워크 보안 설정

API/Web 호스트 선택은 `S4.z`에서 서버 타입에 따라 `https://smart.letskorail.com`, 테스트/스테이징/개발 호스트로 분기한다. 실서비스 타입의 API/Web 기본 호스트는 HTTPS이다. 근거: `analysis/jadx/sources/S4/z.java:36-54`.

`ExecuteDao`는 Retrofit `UrlConnectionClient`를 사용하며 endpoint를 `z.getSSLHost()`로 설정한다. 코레일 앱 소유 패키지에서 별도 `CertificatePinner`, 커스텀 `HostnameVerifier`, trust-all `X509TrustManager` 설정은 확인되지 않았다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-64`.

`network_security_config.xml`은 다음 대상에 cleartext를 허용한다.

| 대상 | includeSubdomains | 근거 |
|---|---:|---|
| `1.255.59.22` | true | `analysis/jadx/resources/res/xml/network_security_config.xml:3-5` |
| `bot-dev-lb-100453984-927a54b5c9cb.kr-gov.lb.naverncp.com` | true | `analysis/jadx/resources/res/xml/network_security_config.xml:6-7` |
| `teapp.srail.kr` | true | `analysis/jadx/resources/res/xml/network_security_config.xml:8-9` |
| `app.srail.kr` | true | `analysis/jadx/resources/res/xml/network_security_config.xml:10-11` |

SRT 예약 URL은 상수 생성 시 `https://eapp.srail.kr/` 또는 개발용 `https://teapp.srail.kr/` 형태로 만들어진다. 근거: `analysis/jadx/sources/K4/g.java:76-78`, `analysis/jadx/sources/K4/g.java:116-120`. WebView SRT 예약 모드에서는 `http://*.srail.kr` URL을 `https://`로 바꾸는 `Y0()` 및 응답 문자열 치환 `b1()`이 있다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:921-926`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:955-956`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:997-1005`.

보안상 의미는 두 가지다. 첫째, 주 API는 HTTPS를 기본으로 한다. 둘째, 앱 설정은 일부 cleartext 목적지를 예외 허용하므로, 해당 목적지와 WebView 로드 URL의 신뢰 경계를 별도로 관리해야 한다.

## WebView 보안 자세

`BaseWebViewActivity`는 공통 WebView wrapper다. 기본 초기화에서 다음을 설정한다.

- JavaScript 활성화
- geolocation 활성화
- database/DOM storage 활성화
- form data 저장 비활성화
- User-Agent에 `korailtalk AppVersion/<version>` 추가
- multiple window 지원
- mixed content mode `2`
- `korailtalk` 이름의 JavaScript interface 등록
- third-party cookie 허용은 별도 `Z0()` 및 결제/Onepass WebView에서 명시

근거: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1097-1133`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:928-935`, `analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java:57-66`, `analysis/jadx/sources/com/korail/talk/ui/web/OnepassWebViewActivity.java:106-120`.

JavaScript bridge는 `BaseWebViewActivity.c`에 구현되어 있고, 앱 뒤로가기, 장바구니 이동, 인증 성공, 결제 이동, 로그인, 열차시간 이동, 세션 만료, 캘린더, 로딩 표시, 토스트, 창 닫기 등 앱 내부 상태 전환을 메시지로 전달한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:299-498`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:147-296`.

`IntegrationWebViewActivity`는 `korailtalk://productTrainSearch`, `korailtalk://payment`, `korailtalk://login`, `korailtalk://supermove`를 해석한다. 일부 scheme은 결제 화면, 로그인, Intro/SRT 이동으로 이어진다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:47-106`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:119-141`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:167-179`.

WebView URL 로드는 intent extra `WEB_GET_URL`/`WEB_POST_URL` 및 `WEB_GET_PARAMETER`/`WEB_POST_PARAMETER`를 조합한다. 기본값으로 공통 파라미터가 붙고, POST면 `postUrl()`, GET이면 query string을 붙인 `loadUrl()`을 사용한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1008-1060`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1063-1088`.

보안 자세의 핵심은 WebView에 로드되는 URL의 신뢰성이다. JavaScript, bridge, multiple window, third-party cookie, geolocation이 활성화되어 있으므로, 신뢰되지 않은 웹 콘텐츠가 이 wrapper에 들어오지 않도록 호출부에서 URL 출처와 scheme을 제한하는 것이 중요하다. 이 문서는 우회 절차를 제공하지 않으며, 관찰된 신뢰 경계만 기록한다.

## 관찰 가능한 한계

- 서버 정책은 정적 APK만으로 확정할 수 없다. `isMacroEnable`, DynaPath 서버 검증, NetFunnel 서버 응답, 실제 rate limit/차단 정책은 운영 응답에 의존한다.
- DynaPath 토큰 값의 내부 생성 로직은 SDK에 캡슐화되어 있어 앱 코드에서 포맷/수명/서명 방식을 확인할 수 없다.
- NetFunnel 라이브러리 내부 프로토콜(`T6.*`)은 난독화되어 있고, 본 문서는 앱이 어떤 action id로 언제 `BEGIN`/`END`를 호출하는지에 집중한다.
- `act_22` 환불 action 상수는 존재하지만 Java 호출 지점은 확인되지 않았다. smali나 런타임 분기, 난독화로 인해 누락되었을 가능성은 배제하지 않는다.
- 루팅 패키지 `queries` 선언은 확인되지만, 이를 사용하는 차단 로직은 확인되지 않았다. 패키지 가시성 선언만으로 루트 탐지가 수행된다고 결론낼 수 없다.
- TLS 인증서 핀닝 부재는 클라이언트 정적 관찰이다. 서버 측 mTLS, WAF, DynaPath/NetFunnel 서버 검증, 세션 정책은 별도 영역이다.
- WebView 보안 평가는 로드 URL의 실제 출처와 서버 콘텐츠 보안 정책을 알 수 없어, 클라이언트 설정과 bridge 표면 중심으로 제한된다.

## 방어 관점 요약

클라이언트는 예약/조회/결제처럼 트래픽 집중과 자동화 가능성이 큰 구간에 두 층의 제어를 둔다. NetFunnel은 사용자가 특정 업무 플로우에 진입할 때 대기열 action id를 적용하는 UI 플로우 방어이고, DynaPath는 서버 feature flag가 켜진 상태에서 일부 민감 API 요청에 매크로 탐지 토큰 헤더를 붙이는 HTTP 요청 방어다.

방어 효과는 최종적으로 서버 검증에 달려 있다. 클라이언트 코드에서 확인되는 역할은 초기화, feature flag 반영, 헤더 부착, 403/DynaPath 오류 메시지 표시, NetFunnel 시작/종료 UI 제어다. 따라서 운영 방어 검토 시에는 서버가 위 action id와 토큰 헤더를 어떤 정책으로 검증하는지, DynaPath 대상 외 민감 API가 별도 서버 통제를 갖는지, WebView 로드 URL이 신뢰된 출처로 제한되는지를 함께 확인해야 한다.

## 20-agent follow-up audit 보강

- `NetfunnelTestActivity`는 release manifest에서도 exported true와 MAIN intent-filter를 가진다. 버튼 동작은 `BEGIN(service_1, act_8, ...)`를 100회 반복하는 테스트 성격이라 외부 explicit intent entry risk로 별도 표시해야 한다.
- Sid는 `BaseRequest` default field가 아니다. 조회/좌석 DAO가 `S4.C0812l.getSid()`를 호출하며, `AD` + timestamp를 key `2485dd54d9deaa36`로 AES/CBC 처리하는 값이다. DynaPath header와 별개다.
- pay endpoint coverage에는 `/classes/com.korail.mobile.payment.reserve.payco.do`와 `/classes/com.korail.mobile.pay.*` 계열을 함께 둔다.
- debug token logging path가 있다. `ExecuteDao`는 token 생성 뒤 debug log에 값을 남길 수 있으며, release `IS_DEBUG_LOG=false` 전제에서는 출력되지 않지만 debug/log variant에서는 민감 token 노출 가능성이 있다.
