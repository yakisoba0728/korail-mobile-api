# KORAIL APK Static Analysis

분석 대상은 `korail.apk`이며, APK SHA-256은 `0b7ee8ae78e0e54df8577f09bfbbb150d113245f6cc834c0d20e81f0bcf5c088`이다. 정적 분석 기준 앱 패키지는 `com.korail.talk`, 버전은 `6.5.0`, versionCode는 `60500002`, API version은 `250601003`, flavor는 `product`, build type은 `release`다.

이 문서는 APK를 로컬에서 unpack/decompile한 결과를 근거로 작성했다. 생성 산출물은 `analysis/` 아래에 있으며 git에서는 제외했다. 전체 Retrofit API 목록은 [api-endpoints.md](api-endpoints.md)에 별도 정리했다. 요청/응답 field-level 계약과 하위 흐름별 상세 분석은 [deep-dive/README.md](deep-dive/README.md), [deep-dive/api-contracts.md](deep-dive/api-contracts.md), [deep-dive/agent-reports/](deep-dive/agent-reports/)에 둔다.

## 분석 산출물

- Raw APK extract: `analysis/raw/`
- apktool decode: `analysis/apktool/`
- JADX source/resource decode: `analysis/jadx/`
- Generated API report: `analysis/reports/api-endpoints.tsv`, `analysis/reports/api-endpoints.md`
- Checked-in API inventory: [api-endpoints.md](api-endpoints.md)
- Checked-in API contract catalog: [deep-dive/api-contracts.md](deep-dive/api-contracts.md)
- Checked-in network model field catalog: [deep-dive/network-model-fields.md](deep-dive/network-model-fields.md)
- Checked-in WebView/URL/local storage catalogs: [deep-dive/webview-and-url-catalog.md](deep-dive/webview-and-url-catalog.md), [deep-dive/local-storage-catalog.md](deep-dive/local-storage-catalog.md)

JADX는 전체 처리 중 일부 라이브러리/복잡 제어흐름에서 decompile warning을 냈다. 주요 네트워크 레이어와 `com.korail.talk.network.*` 패키지는 Java-like source로 확인했고, 필요 시 `analysis/apktool/smali*`가 fallback 근거다.

## APK 메타데이터

- minSdk: `24`
- targetSdk: `35`
- compileSdk: `35`
- application class: `com.korail.talk.application.KTApplication`
- network security config: `@xml/network_security_config`
- Play source stamp SHA-256: `3257d599a49d2c961a471ca9843f59d341a405884583fc087df4237b733bbd6d`

주요 권한은 `INTERNET`, network/wifi state, fine/coarse location, camera, record audio, call phone, notifications, media image read, Bluetooth, FCM receive, advertising ID 계열이다. `allowBackup=false`다.

Exported activity 중 API/웹 연동과 관련 있는 항목은 `IntroActivity`, `LoginActivity`, `NavigationActivity`, `DataActivity`, `PaymentActivity`, `RailPlusActivity`, `IntegrationWebViewActivity`, `TrainServiceWebViewActivity`, `GovernmentCertificationActivity`, `BixbyReservationActivity`, `MaumAIWebViewActivity` 등이다. 외부 scheme은 `korailtalk://navigation`, `korailtalk://member_info`, `korailtalk://approve`, Kakao OAuth scheme, mobile ID scheme을 포함한다.

## Host and Environment

서버 선택은 `G4.a.CONNECT_SERVER = "3"` -> `d5.EnumC5607a.REAL`로 해석된다. 따라서 이 APK의 기본 Retrofit/Web host는 다음과 같다.

- Main API/Web host: `https://smart.letskorail.com`
- Multi-language web host: `https://www.korail.com`
- Push host: `smart.letskorail.com`
- NetFunnel host: `nf.letskorail.com:443`
- SRT web reservation host: `https://eapp.srail.kr/`

개발/스테이징 분기는 코드상 남아 있다: `mobiledev.letskorail.com`, `dev2.letskorail.com`, `dev3.letskorail.com`, `dev5.letskorail.com`, `smartbeta.letskorail.com`.

`network_security_config.xml`은 cleartext를 일부 도메인에 허용한다: `1.255.59.22`, `bot-dev-lb-100453984-927a54b5c9cb.kr-gov.lb.naverncp.com`, `teapp.srail.kr`, `app.srail.kr`. SRT WebView 로직은 `http://teapp.srail.kr`/`http://app.srail.kr`를 HTTPS로 치환한다.

## Network Architecture

앱 내부 API는 대부분 Retrofit 1 기반이다.

- `ExecuteDao.getDefaultRestAdapterBuilder()`가 `GsonConverter`, `UrlConnectionClient`, 60초 connect/read timeout을 설정한다.
- `ExecuteDao.getRestAdapterBuilder()`가 endpoint를 `S4.z.getSSLHost()`로 설정한다.
- 모든 DAO는 `BaseDao`를 상속하고 `BaseDaoHelper.HttpTask`가 `AsyncTask`에서 `executeDao()`를 호출한다.
- 공통 요청값은 `BaseRequest` 생성자에서 설정된다: `Device=AD`, `Version=250601003`, `Key=korail1234567890`.
- 공통 응답은 `BaseResponse`의 `h_msg_cd`, `h_msg_txt`, `strResult`를 사용한다.

정적 추출 기준 Retrofit method entry는 총 165개다. Distinct HTTP+path pair는 159개이며, 동일 path에 대해 overload/업무 시나리오가 나뉘는 항목이 있다. 분포는 `POST` 136개, `GET` 29개이며, 35개 annotated interface에 걸쳐 있다. 주요 그룹은 다음과 같다. 아래 표는 업무 영역별 태깅이므로 cross-cutting service가 겹칠 수 있고, 합계가 총 method entry 수와 일치하도록 설계한 taxonomy는 아니다.

| Area | Service | Count |
|---|---|---:|
| Booking/search | `SeatMovieService`, `ResearchService`, `TrainsInfoService`, `CalendarService` | 21 |
| Reservation | `CertificationService`, `ReservationService`, `ReservationCancelService`, `ReservationWaitService` | 20 |
| Payment/pay providers | `PaymentService`, `PayService`, `PassService`, `PassCardService`, `XPointService`, `MileageService`, `CashReceipt` | 34 |
| Ticket/refund | `TicketService`, `MyTicketService`, `RefundService`, `CompensateService`, `DelayService` | 39 |
| Login/account/common | `LoginService`, `CommonService`, `NFilterService`, `CustService`, `RailPlusService` | 21 |
| Product/MAAS/gift/add-ons | `ProductService`, `AddService`, `CartService`, `GifticketService`, `GiftInfoService`, `BusReservationService` | 23 |
| Cache/push/receipt | `CacheService`, `PushService`, `ReceiptService`, `IndependentService` | 9 |

모든 endpoint, HTTP method, Java method, 파라미터명은 [api-endpoints.md](api-endpoints.md)에 있다.

## Core Flows

### Startup and Common Code

`KTApplication` initializes cookies, NetFunnel defaults, typefaces, volatile QR folders, notification channels, database helper, and Kakao SDK. `IntroActivity` initializes DynaPath and calls common-code APIs. 서버의 common-code 응답 중 `isMacroEnable` 값이 `Y`이면 `I4.a.IS_MACRO_ACTIVE`가 true가 된다.

`CommonService`는 공통 코드, 역 정보, 암호화/복호화 helper, MAAS 메뉴/역 목록, QR 위치 인증, cookie UUID를 제공한다. 주요 endpoint는 `/classes/com.korail.mobile.common.code.do`, `/classes/com.korail.mobile.common.stationdata`, `/classes/com.korail.mobile.common.encrypt.do`, `/classes/com.korail.mobile.common.decrypt.do`, `/ebizcross/getUUID.do`다.

### Login and Session

로그인은 `LoginService.login()` -> `/classes/com.korail.mobile.login.Login`으로 수행된다. 필드는 `txtMemberNo`, `txtPwd`, `txtInputFlg`, `checkValidPw`, `custId`, `etrPath`, `idx`다.

`LoginDao.executeDao()`는 로그인 성공 후 `KTApplication.setSessionId()`를 호출한다. 앱은 Java `CookieManager`에서 `JSESSIONID`를 찾고 Android WebView `CookieManager`에 `smart.letskorail.com` 기준으로 쿠키를 설정한다. 즉 Retrofit/UrlConnection 세션과 WebView 세션을 동기화한다.

자동 로그인은 `KEY_LOGIN_TYPE`, `KEY_LOGIN_ID`, `KEY_LOGIN_PW`, `LOGIN_DATA`를 SharedPreferences에서 읽는다. 저장된 ID/PW는 `F4.a`의 AES/ECB/PKCS5Padding으로 Android ID 기반 16바이트 키를 만들어 복호화한다. 실제 로그인 전 비밀번호는 common-code의 `pwdAESCphd` 플래그에 따라 AES/CBC/PKCS5Padding 후 Base64 또는 단순 Base64로 보낸다.

### Train Inquiry

열차 조회는 `SeatMovieService`가 중심이다.

- 일반 조회: `/classes/com.korail.mobile.seatMovie.ScheduleView`
- 리무진 연동 조회: `/classes/com.korail.mobile.seatMovie.LimousineScheduleView`
- 상품/특가 조회: `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`

`TrainInquiryDao`는 `TrainInquiryRequest`를 받아 `Sid`, menu/job, 열차그룹/번호, 출발/도착역, 승차일/시간, 승객 수 플래그, 좌석 속성, SRT/왕복/재조회/페이징 관련 필드를 전송한다. `Sid`는 `S4.C0812l.getSid()`에서 고정 키 `2485dd54d9deaa36`으로 `AD + timestamp`를 AES/CBC 암호화해 생성한다.

### Reservation

일반 예약은 `ReservationDao`가 `CertificationService`의 overload된 `reservation()` 메서드를 호출한다.

- 회원 예약: `/classes/com.korail.mobile.certification.TicketReservation`
- 비회원 예약: `/classes/com.korail.mobile.nonMember.NonMemTicket`

`ReservationRequest`는 PNR, menu/job id, goods id, free flag, standing flag, PBEP info, 비회원 이름/휴대폰/비밀번호를 포함한다. 여정/승객/좌석/객차 데이터는 `OPsg`, `OSeat`, `OJrny`, `OSrcar` map 객체로 FieldMap 전송된다. 비회원 예약 제한 로직은 menu id `41`, job id `1102`, 특실 좌석 요청, `isNotNonMemberShow` 플래그를 검사한다.

### Payment

예약 결제는 `PaymentService.payment()` -> `/classes/com.korail.mobile.payment.ReservationPayment`다. 기본 필드는 `hidPnrNo`, `hidWctNo`, `hidTmpJobSqno1`, `hidTmpJobSqno2`, `hidRsvChgNo`이고, 결제수단 상세는 `PaymentMethod` FieldMap으로 들어간다.

`PaymentMethod`는 카드, 간편결제, 포인트, 후불/선불 관련 field key를 동적으로 만든다. 예: `hidStlCrCrdNo{n}`, `hidVanPwd{n}`, `hidCrdVlidTrm{n}`, `hidIsmtMnthNum{n}`, `spayDvCd_1_1`, `spayCphdDatVal_1_1`, `hidPontCrdPwd{n}`.

간편결제/외부결제는 `PayService`에 분리되어 있으며 NaverPay, Payco, Samsung/Monimo pay data validation, Toss auto payment key 생성/조회/처리, STBK account 관련 endpoint를 포함한다. WebView 기반 결제는 `EasyPayWebViewActivity`가 approve scheme을 처리한다.

### Ticket, Refund, Check-in

티켓 목록은 `MyTicketService.getTicketList()` -> `/classes/com.korail.mobile.myTicket.MyTicketList`다. TicketService는 self check-in, 승차권 중복확인, 플랫폼 번호, 전달/수령자, 문자 전송, 좌석변경, MAAS 취소/상세를 처리한다.

환불은 `RefundService`가 담당한다.

- 환불 가능/원권 검증: `/classes/com.korail.mobile.refunds.verifyOnlineRefunds`
- 환불 수수료 조회: `/classes/com.korail.mobile.refunds.CommissionView`
- 티켓 상세 조회: `/classes/com.korail.mobile.refunds.SelTicketInfo`
- 환불 요청: `/classes/com.korail.mobile.refunds.RefundsRequest`
- 온라인 환불 실행: `/classes/com.korail.mobile.refunds.executeOnlineRefunds`

환불 요청에는 PNR, 원권 발매일/창구/일련번호/반환비밀번호, 마일리지 결제 여부, 환불 회차 구분, 열차번호, PBP 대상 여부, 위치 좌표가 포함될 수 있다.

### WebView and Scheme Bridge

`BaseWebViewActivity`는 공통 WebView wrapper다. JavaScript, DOM storage, geolocation, multiple windows, third-party cookies를 활성화하고 User-Agent에 `korailtalk AppVersion/6.5.0`을 추가한다. JavaScript interface 이름은 `korailtalk`다.

Bridge methods는 `appBack`, `windowClose`, `login`, `sessionExpired`, `showLoadingDialog`, `hideLoadingDialog`, `sendCalendar`, `certificationIdSuccess`, `certificationPwSuccess`, `goPayment`, `changeLanguage`, `goHome`, `refreshCustTrip`, `moveToTrainTime`, `identityVerificationSuccess`, `goMaasPayment`, `goSelectFromDate`, `goSelectToDate`, `cartlist`, `nonmember`, `nonmemberResult` 등을 노출한다.

WebView URL 로딩은 `WEB_GET_URL`/`WEB_POST_URL`와 `WEB_GET_PARAMETER`/`WEB_POST_PARAMETER` intent extra를 조합한다. 기본값으로 `Device=AD&Version=250601003&Key=korail1234567890`가 붙는다. SRT web reserve의 경우 JSON body POST도 별도 처리하며 응답 body 내 `http://*.srail.kr` 링크를 HTTPS로 치환한다.

`IntegrationWebViewActivity`는 `korailtalk://productTrainSearch`, `korailtalk://payment`, `korailtalk://login`, `korailtalk://supermove`를 해석한다. `supermove`는 SRT에서 받은 검색 조건을 `ReceiveSRTData`로 만들어 `IntroActivity`에 전달한다.

### Anti-automation and Queueing

NetFunnel은 `nf.letskorail.com:443`, service id `service_1`로 초기화된다. Action id는 일반 조회 `act_8`, 성수기 `act_8_2`, 예약 `act_14`, 결제 `act_18`, 예약내역 `act_21`, 환불 `act_22`, 상품 `act_6`, 테스트 `act_4`가 보인다.

DynaPath는 macro 방어용으로 보인다. `isMacroEnable=Y`일 때 다음 endpoint URL에 `x-dynapath-m-token` header를 추가한다.

- `/classes/com.korail.mobile.certification.TicketReservation`
- `/classes/com.korail.mobile.nonMember.NonMemTicket`
- `/classes/com.korail.mobile.seatMovie.ScheduleView`
- `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
- `/classes/com.korail.mobile.trn.prcFare.do`
- `/classes/com.korail.mobile.login.Login`

403 Forbidden 응답에 `DynaPath-Result` header가 있고 값이 음수이면 body JSON의 `message`를 macro dialog message로 표시한다.

## Local Data Handling

앱은 ORMLite 기반 로컬 DB 모델을 사용한다. 확인된 모델은 `CreditCard`, `FavoriteStation`, `ZRecentStation`, `StationData`, `TicketDetail`, `SMSData`, `MainPopupData`, `IssueList`, `DoNotLookAgain`이다.

관심 지점:

- Favorite card는 `CreditCard.cardNumber`, `cardValidateMonth`, `cardValidateYear`, `businessNum`, `cardType`, `cardNickname`를 저장한다.
- UI 조회 시 card number는 `F4.a.decryptAES(context, creditCard.getCardNumber())`로 복호화된다.
- `F4.a`의 AES key는 Android ID에서 파생한 16바이트 값이다.
- Ticket cache는 PNR와 ticket detail 문자열을 저장한다.
- SMS data는 PNR와 phone number를 저장한다.

정적 분석만으로 DB 파일명/권한/Keystore 사용 여부까지 확정하지는 않았다. 실제 저장 파일과 암호화 적용 범위는 기기 실행 후 `/data/data/com.korail.talk/` 검증이 필요하다.

## Third-party and External Integrations

- Kakao SDK: OAuth/link/user SDK, Kakao app key는 resource string에서 초기화.
- Naver login/request API: `https://openapi.naver.com/v1/nid/me`.
- Google/Firebase/FCM/Ads/Auth.
- NHN/Naver login SDK.
- H2O SmartAlimi push/service module.
- Maum AI voice/chat assets and gRPC/protobuf resources.
- SRT app/web integration via `eapp.srail.kr`, `app.srail.kr`, `teapp.srail.kr`, and package query `kr.co.srail.newapp`.
- External informational links: `www.korail.com`, `info.korail.com`, `gis.korail.com`, `blog.naver.com/korailblog`, `m.lost112.go.kr`.

## Security Notes

이 문서는 정적 분석 결과이며 운영 서비스 호출, 인증 우회, NetFunnel/DynaPath 우회는 수행하지 않았다.

- API key `korail1234567890`는 앱에 내장된 클라이언트 식별자 성격이며 단독 인증 수단으로 보이지 않는다.
- 세션은 서버 `JSESSIONID`에 의존하고, 앱은 로그인 후 WebView 쿠키로 동기화한다.
- 로그인 저장값과 favorite card 값은 앱 자체 AES 유틸로 보호되지만, 키 유도는 Android ID 기반이다.
- WebView bridge가 넓고 JavaScript/multiple window/third-party cookie가 활성화되어 있으므로, WebView에 로드되는 URL 신뢰 경계가 중요하다.
- cleartext 허용 도메인이 제한적으로 존재한다. SRT URL은 코드상 HTTPS 치환이 있지만 network security config는 일부 cleartext를 허용한다.
- 민감 endpoint 일부는 DynaPath token이 켜질 수 있고, 예약/결제/환불 흐름은 NetFunnel queue와 결합된다.

## Residual Gaps

- 동적 트래픽 캡처를 하지 않았기 때문에 실제 서버 feature flag, cookie lifecycle, runtime-only redirect, TLS/certificate details는 미확인이다.
- APK Signature Scheme v2/v3 cert는 현재 로컬 `keytool -jarfile`로 확인되지 않았다. APK hash와 Play stamp hash는 기록했다.
- 일부 UI/라이브러리 클래스는 JADX 경고가 있었으나, API inventory는 Retrofit annotation과 smali fallback으로 재검증 가능하다.
- ProGuard/R8로 일부 패키지가 난독화되어 유틸리티 클래스의 원래 이름은 복원되지 않았다.
