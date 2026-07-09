# UI 플로우 to API 맵

대상 APK는 `korail.apk`의 JADX 디컴파일 산출물(`analysis/jadx/sources`)이다. 이 문서는 정적 로컬 분석만으로 작성했으며, 실제 네트워크 호출이나 동적 실행 검증은 수행하지 않았다. `com.korail.talk` 앱 고유 `ViewModel` 클래스는 확인되지 않았고, 화면 상태와 흐름 제어는 주로 `Activity`/`Fragment`, 보조 presenter/helper 클래스, DAO 요청 객체가 담당한다.

## 공통 네트워크 실행 계약

- 모든 `BaseRequest` 파생 요청은 생성자에서 `Device=AD`, `Version=250601003`, `Key=korail1234567890`를 기본값으로 가진다. [source: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:6-18`]
- `BaseActivity.executeDao(iBaseDao, base)`는 DAO에 현재 화면(`IBase`)과 결과 콜백(`IBaseResult`)을 주입한 뒤 `BaseDaoHelper.executeDao()`로 넘긴다. [source: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:730-736`]
- `BaseDaoHelper.HttpTask`는 `AsyncTask.doInBackground()`에서 `mDao.executeDao()`를 호출해 응답을 저장하고, `onPostExecute()`에서 NetFunnel runner를 실행한 뒤 `onIntegrationResult(iBaseDao, exception)`을 호출한다. [source: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:43-47`, `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101-110`]
- `BaseActivity.onIntegrationResult()`는 공통 실패 코드/세션/매크로 오류를 먼저 해석한다. 정상일 때 `base.onReceive(iBaseDao)`, 오류일 때 `base.onReceiveError(iBaseDao, error)`로 화면별 callback을 분기한다. [source: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:599-649`]
- Retrofit 1 `RestAdapter`는 Gson converter, `UrlConnectionClient`, 60초 connect/read timeout을 사용한다. `IS_MACRO_ACTIVE`가 켜져 있으면 로그인/열차조회/예약/요금조회 URL에 `x-dynapath-m-token`을 붙인다. [source: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-60`]

## 1. Startup / 공통 데이터 부트스트랩

### Call graph

```text
KTApplication.onCreate()
  -> CookieManager/NetFunnel/DB/typeface/temp-folder/notification/Kakao 초기화

IntroActivity.onCreate()
  -> 권한/Google Play 확인
  -> ServiceCheckDao
  -> CommonCodeDao
  -> AppDataDao
  -> NoticeDao
  -> TrainCalendarDao
  -> StationInfoDao
  -> 필요 시 StationDataDao
  -> auto-login 또는 MainBookingActivity/OldMainBookingActivity
```

### Source methods and request construction

- `KTApplication.onCreate()`는 Java `CookieManager`, NetFunnel host `nf.letskorail.com`, ORMLite helper, volatile/QR 폴더 삭제, notification channel, Kakao SDK를 초기화한다. [source: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:61-86`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:118-127`]
- `IntroActivity.q0()`는 `ServiceCheckDao`를 실행한다. 성공 callback에서 `r0()`로 common-code 요청으로 넘어간다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:398-436`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:684-689`]
- `IntroActivity.r0()`는 `CommonCodeDao.CommonCodeRequest`에 화면 폭/높이, OS version, code list(`app.display.image`, `app.login.cphd`, `app.var.data`, `app.event.easyPay`, `app.MaaS.test` 등)를 채워 `/classes/com.korail.mobile.common.code.do`로 보낸다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:402-436`, `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java:30-32`]
- 캐시/캘린더 API는 `MobileService.cache`, `prdMobilePlusMain.cache`, `prdMobilePlusNotice.cache`, `/classes/com.korail.mobile.schedule.runDt`이다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cache/CacheService.java:10-18`, `analysis/jadx/sources/com/korail/talk/network/dao/schedule/CalendarService.java:7-9`]
- 역 정보는 `/classes/com.korail.mobile.common.stationinfo`로 버전/개수를 확인하고, 변경 필요 시 `/classes/com.korail.mobile.common.stationdata`를 받아 로컬 `StationData` DB에 저장한다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:127-147`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:502-511`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:786-800`, `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java:54-58`]

### Response handling and navigation

- common-code 응답은 `SharedPreferences` 성격의 `H.put*` 저장소에 메뉴/팝업/간편로그인/결제옵션/로그인 암호화 정책/매크로 플래그를 저장한다. `isMacroEnable=Y`이면 `I4.a.IS_MACRO_ACTIVE`가 true가 된다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:692-742`]
- 앱 데이터 응답은 강제/선택 업데이트 여부를 검사하고, 통과하면 공지, 캘린더, 역정보 순서로 진행한다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:745-783`]
- 모든 초기 데이터가 준비되면 `KEY_AUTO_LOGIN`이 true인 경우 `BaseActivity.I()` 경유 자동 로그인으로, 아니면 `w0()`로 메인 예약 화면으로 이동한다. `w0()`는 외부 navigation extras, `POPUP_DATA`, `POPUP_COUPON`, SRT `PARAM` JSON을 `MainBookingActivity` 또는 `OldMainBookingActivity`에 그대로 전달한다. [source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:463-499`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:786-795`]

## 2. Login / 세션 동기화

### Call graph

```text
LoginActivity
  -> login tab Fragment(K5.b)
    -> btn_login/onEditorAction
    -> LoginDao or AutoLoginDao or EasyLoginDao
      -> LoginService.login("/classes/com.korail.mobile.login.Login")
      -> KTApplication.setSessionId()
    -> K5.b.onReceive()
      -> SharedPreferences 암호화 저장
      -> LoginActivity.successLogin(...)
      -> caller BaseActivity.onActivityResult(104)
```

### Intent extras and UI branches

- `LoginActivity`는 `IS_DRAWER_LOGIN`, `WEB_POST_URL`, `WEB_POST_PARAMETER` 존재 여부를 읽는다. 후자는 자동 로그인/웹 인증 후 복귀 흐름 판별에 사용된다. [source: `analysis/jadx/sources/com/korail/talk/ui/login/member/LoginActivity.java:109-124`]
- 로그인 화면은 세 개 fragment를 tab으로 구성한다. `K5.b`는 현재 tab index를 `txtInputFlg` 값으로 변환한다: 0번은 계정/회원번호, 1번은 비밀번호 변경형, 2번은 다른 로그인 타입이다. [source: `analysis/jadx/sources/com/korail/talk/ui/login/member/LoginActivity.java:66-89`, `analysis/jadx/sources/k5/b.java:119-122`]
- 비회원 버튼은 `IS_RESERVATION_DAO` extra를 `NonMemberRegisterActivity`로 전달하거나, common-code의 AnyID URL을 `IntegrationWebViewActivity`에 `WEB_GET_URL`, `WEB_GET_PARAMETER=type=reserv|search&Version=250601003`로 연다. [source: `analysis/jadx/sources/k5/b.java:374-395`]

### Request construction and API

- 일반 로그인 버튼은 `K5.b.B0("Y")`에서 `LoginDao.LoginRequest`를 만들고 `txtMemberNo`, `txtPwd`, `txtInputFlg`, `checkValidPw`, `idx`를 채운다. 비밀번호는 common-code `LOGIN_DATA.pwdAESCphd`가 `Y`이면 서버 제공 key로 AES 암호화 후 Base64, 아니면 평문 Base64이다. [source: `analysis/jadx/sources/k5/b.java:102-113`, `analysis/jadx/sources/k5/b.java:124-140`]
- 자동 로그인은 저장된 `KEY_LOGIN_ID`, `KEY_LOGIN_PW`를 앱 AES 유틸로 복호화한 뒤 같은 암호화 정책을 적용한다. [source: `analysis/jadx/sources/k5/b.java:211-224`, `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:385-401`]
- `LoginDao.executeDao()`는 `LoginService.login()`을 호출한다. Retrofit field는 `Device`, `Version`, `Key`, `txtMemberNo`, `txtPwd`, `txtInputFlg`, `checkValidPw`, `custId`, `etrPath`, `idx`이고 endpoint는 `/classes/com.korail.mobile.login.Login`이다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginDao.java:236-242`, `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginService.java:17-19`]
- 로그인 직후 `KTApplication.setSessionId()`가 Java `CookieManager`의 `JSESSIONID`를 WebView `CookieManager`로 복사한다. 즉 Retrofit/UrlConnection 세션과 WebView 세션이 연결된다. [source: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:99-115`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java:129-132`]

### Response handling and navigation

- `K5.b.onReceive()`는 로그인/자동로그인/간편로그인 DAO 응답을 공통 처리한다. 성공 코드가 아니고 `strRedirectUrl`이 있으면 `IntegrationWebViewActivity`로 인증 웹뷰를 열고, 성공이면 로그인 타입/회원번호 저장 여부/자동로그인 여부/암호화된 ID/PW/고객번호를 저장한다. [source: `analysis/jadx/sources/k5/b.java:441-474`]
- popup data 또는 coupon flag가 있으면 result intent에 `POPUP_DATA`, `POPUP_COUPON`, `POPUP_COUPON_NAME`을 담아 반환한다. 일반 성공은 `LoginActivity.successLogin()`이 `IS_DRAWER_LOGIN` extra를 붙여 `setResult(RESULT_OK)` 후 종료한다. [source: `analysis/jadx/sources/k5/b.java:475-488`, `analysis/jadx/sources/com/korail/talk/ui/login/member/LoginActivity.java:312-325`]
- 호출 측 `BaseActivity.onActivityResult(104)`는 `IS_NON_MEMBER_LOGIN`, `IS_DRAWER_LOGIN`, popup extras를 판독해 `onNonMemberLoginSuccess()`, `onDrawerLoginSuccess()`, `onLoginSuccess()`로 분기한다. [source: `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:493-527`]

## 3. Search / 열차 조회

### Call graph

```text
MainBookingActivity search button
  -> X0()/Y0()/t1(bundle)
  -> U0(...) builds TrainInquiryRequest[]
  -> V0() builds ReservationRequest
  -> DirectInquiryActivity or TransferInquiryActivity
    -> B5.c.L0() clone/select request
    -> B5.c.s2()
      -> NetFunnel BEGIN
      -> TrainInquiryDao or ProductTrainInquiryDao
      -> SeatMovieService.ScheduleView
    -> response train list -> bundle conversion -> RecyclerView
```

### Intent extras and request construction

- `MainBookingActivity.t1()` creates an intent to `DirectInquiryActivity` or `TransferInquiryActivity`. It sends `IS_DIRECT`, `IS_TRANSFER`, `SEAT_OPTION_INDEX`, `SEAT_OPTION_CODE`, transfer station extras, `RESERVATION_TYPE`, optional `RESERVATION_RESPONSE`, `MENU_TYPE`, `INQUIRY_REQUEST`, and `RESERVATION_REQUEST`. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:1008-1042`]
- `INQUIRY_REQUEST` is a `TrainInquiryRequest[]`. `U0()` creates one request for 편도 or two for 왕복, delegates base population to `U4.b.getRsvInquiryRequest(...)`, then sets adjacent-station search flag, SRT/eBizCross flag, round-trip flag, and member card number. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:764-787`]
- `MainBookingActivity.z1()` can prefill route/date/time from SRT/external extras `srtDep`, `srtArv`, `srtDt`, `srtTm`; station codes are converted to station names via local station DB. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:1118-1164`]
- Inquiry activity base `B5.c.L0()` reads `RESERVATION_TYPE`, clones `INQUIRY_REQUEST[0]` or `[1]`, sets `qryDvCd=1`, paging fields, and transfer-selected fields (`TRANSFER_CHTNRSSTNCD`, `TRANSFER_TRNGPCD`, `IS_SELECT_TRANSFER`) when present. [source: `analysis/jadx/sources/b5/c.java:130-160`]

### DAO/API and transformations

- `B5.c.s2()` decides whether to run direct DAO immediately or through NetFunnel. Product inquiry uses product action id, peak season uses peak action id, otherwise normal train inquiry action id. After NetFunnel callback, it chooses `ProductTrainInquiryDao` for `ProductTrainInquiryRequest`, otherwise `TrainInquiryDao`, attaches the selected `RsvInquiryRequest`, suppresses default error dialog, and executes. [source: `analysis/jadx/sources/b5/c.java:76-114`, `analysis/jadx/sources/b5/c.java:430-451`]
- `TrainInquiryDao.executeDao()` maps request fields to `SeatMovieService.getRsvInquiry(...)`. It adds `Sid=C0812l.getSid()` and sends menu/job id, train group/no, departure/arrival station, date/hour, passenger flags, seat attributes, SRT/eBiz/round-trip flags, paging and transfer fields. [source: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java:10-15`]
- Retrofit endpoint is `POST /classes/com.korail.mobile.seatMovie.ScheduleView`; product inquiry uses `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`, limousine uses `/classes/com.korail.mobile.seatMovie.LimousineScheduleView`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:11-22`]
- `RsvInquiryRequest` carries the canonical field set: `txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, `txtPsgFlg_1..5`, `txtSeatAttCd_2..4`, `radJobId`, `selGoTrain`, paging and transfer fields. [source: `analysis/jadx/sources/com/korail/talk/network/request/inquiry/RsvInquiryRequest.java:10-39`, `analysis/jadx/sources/com/korail/talk/network/request/inquiry/RsvInquiryRequest.java:152-260`]

### Response handling and navigation

- `DirectInquiryActivity.onCreate()` calls `m2()`, UI setup, and immediately `s2()` to execute the first inquiry. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:503-512`]
- Inquiry results are converted to UI bundles by `A5.k.P0()`: direct train results become one bundle per train; transfer results become a bundle containing two train bundle entries. [source: `analysis/jadx/sources/A5/k.java:142-173`]
- Selecting an item updates `f234l`, extracts train bundle data, calls `N0(E0())` to apply the selected train into the reservation request, and may trigger transfer/SRT handling. [source: `analysis/jadx/sources/A5/u.java:930-950`]
- Error code `S134` opens a dialog that can route to limousine flow or login; other train inquiry errors show the message and re-enable empty-state UI. [source: `analysis/jadx/sources/b5/c.java:400-428`]

## 4. Reservation / 예매

### Call graph

```text
DirectInquiryActivity user selects/book train
  -> N0(E0()) mutates ReservationRequest maps
  -> K0()/f3(reservationRequest)
  -> ReservationDao
    -> CertificationService.TicketReservation or NonMemTicket
  -> A5.k/a.onReceive()
    -> discount/disability/waiting/round-trip handling
    -> PaymentActivity or next return-leg search
```

### Request construction

- `MainBookingActivity.V0()` creates a base `ReservationRequest` from passenger UI data. Inquiry screens mutate that object with selected train/seat/journey maps. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:789-791`]
- `DirectInquiryActivity.f3()` sets `ReservationDao`, hides specific reservation error codes from default dialog (`WRR800029`, `ERR911531`, `ERR911051`), sets `notNonMemberShow` according to reservation type/transfer, and executes. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:338-348`]
- `ReservationRequest` combines scalar fields (`pnrNo`, `txtMenuId`, `txtJobId`, `txtGdNo`, `hidFreeFlg`, `txtStndFlg`, non-member customer fields, `pbepInfo`) with four FieldMap maps: `OPsg`, `OSeat`, `OJrny`, `OSrcar`. [source: `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java:13-29`, `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java:77-91`]
- Non-member reservation can be suppressed for menu id `41`, job id `1102`, special-room seat attributes, or `isNotNonMemberShow`. [source: `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java:105-119`]
- `OJrny` is a map of dynamic field names such as `txtJrnyCnt`, `txtJrnySqno{n}`, `txtDptRsStnCd{n}`, `txtArvRsStnCd{n}`, `txtDptDt{n}`, `txtDptTm{n}`, `txtTrnNo{n}`, `txtTrnGpCd{n}`. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OJrny.java:6-28`, `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OJrny.java:69-107`]

### DAO/API

- `ReservationDao.executeDao()` chooses non-member API when `txtCustNm` and `txtCpNo` are present, otherwise member API. Member endpoint is `POST /classes/com.korail.mobile.certification.TicketReservation`; non-member endpoint is `POST /classes/com.korail.mobile.nonMember.NonMemTicket`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/ReservationDao.java:12-18`, `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java:48-54`]

### Response handling and navigation

- `A5.k.onReceiveError()` handles reservation errors. Specific no-seat/session-like errors can navigate to `ReservedTicketActivity` or retry selection; otherwise default error handling applies. [source: `analysis/jadx/sources/A5/k.java:200-222`]
- `com.korail.talk.ui.inquiry.rir.orr.a.O0()` handles successful `ReservationResponse`: disability discount entries route to `DisabilityCertificationActivity` with `RESERVATION_DATA`; `IRR000014` routes to `ReservationWaitActivity`; logged-in users go through `L2()`, non-members through `M2()`. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/a.java:212-231`]
- Round-trip going-leg success stores `f239q` and asks the user to continue; it adjusts the return-leg inquiry date/time based on arrival time, switches `RESERVATION_TYPE` to incoming, and runs the second search. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/a.java:76-98`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/a.java:176-182`]
- Normal final reservation success calls `z2(reservationResponse)` in the inherited confirmation path. On the main/simple-buy path, `MainBookingActivity.s1()` builds `RsvPaymentRequest` from `h_pnr_no`, `h_wct_no`, temp job sequence numbers, first journey `h_rsv_chg_no`, then starts `PaymentActivity` with `PNR_NO_LIST`, `PAYMENT_TYPE`, `PAYMENT_REQUEST`, `COMMON_RESERVATION_RESPONSE`, and `IS_POINT_STEP`. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:980-996`]

## 5. Payment / 결제

### Call graph

```text
PaymentActivity.onCreate()
  -> reads PNR_NO_LIST, PAYMENT_TYPE, PAYMENT_REQUEST, COMMON_RESERVATION_RESPONSE
  -> TicketDuplicationCheckDao when reservation response exists
  -> payment fragment(AbstractC1269e)
    -> builds PaymentMethod FieldMap
    -> RsvPaymentDao / CommPaymentDao / PassPaymentDao / IntgStlDao
      -> payment service endpoint
    -> success callback -> ticket list or caller-specific result
```

### Intent extras and setup

- `PaymentActivity` stores `PNR_NO_LIST`, `PAYMENT_TYPE`, `PAYMENT_REQUEST`, `COMMON_RESERVATION_RESPONSE`, amount/discount fields, point-step flags, travel-package flags, etc. `onCreate()` also handles approve scheme intents for external payment return. [source: `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:168-190`, `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:586-629`]
- If a reservation response is present and this is not ticket-change payment, `A0()` first runs `TicketDuplicationCheckDao` with `pnrNo`. If duplicated tickets exist, a dialog lets the user go to `TicketListActivity`; otherwise it proceeds to payment UI. [source: `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:113-131`, `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:632-649`]

### Request construction and API

- `AbstractC1269e.k1(paymentMethod)` sets `hiduserYn=N` and non-member number for non-members, otherwise `hiduserYn=Y`. It dispatches by `IPaymentRequest` type: `RsvPaymentDao`, `IntgStlDao`, `CommPaymentDao`, or pass/cart variants. [source: `analysis/jadx/sources/B6/AbstractC1269e.java:714-749`]
- `PaymentMethod` is a `LinkedHashMap<String,String>` FieldMap. It dynamically writes keys such as `hidStlCrCrdNo{n}`, `hidVanPwd{n}`, `hidCrdVlidTrm{n}`, `hidIsmtMnthNum{n}`, `hidPontCrdPwd{n}`, `spayDvCd_1_1`, `spayCphdDatVal_1_1`, `hiduserYn`, `hidMbCrdNo`. [source: `analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java:6-31`, `analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java:32-139`]
- `RsvPaymentDao.RsvPaymentRequest` carries `hidPnrNo`, `hidWctNo`, `hidTmpJobSqno1`, `hidTmpJobSqno2`, `hidRsvChgNo`, and the `PaymentMethod` map. [source: `analysis/jadx/sources/com/korail/talk/network/dao/payment/RsvPaymentDao.java:15-78`]
- `RsvPaymentDao.executeDao()` calls `POST /classes/com.korail.mobile.payment.ReservationPayment` via `PaymentService.payment(...)`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/payment/RsvPaymentDao.java:127-137`, `analysis/jadx/sources/com/korail/talk/network/dao/payment/PaymentService.java:11-14`]

### Response handling and navigation

- Payment fragment `onReceive()` handles point/gifticket lookup responses and final payment responses. For `dao_rsv_payment`, `dao_comm_payment`, `dao_pass_payment`, `dao_cart_payment`, it syncs RailPlus for certain payment methods, handles easy-payment follow-up for methods `03`, `10`, `16`, then calls either `B1(...)` or `P1(...)` when image-ticket flag `h_im_flg=Y`. [source: `analysis/jadx/sources/B6/AbstractC1269e.java:1122-1217`]
- `PaymentActivity` can navigate to `TicketListActivity` after duplicate detection or payment completion; travel package payments navigate to `TripBookingListActivity` in the same branch. [source: `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:147-153`]

## 6. Ticket / 승차권 조회 및 상세

### Call graph

```text
TicketListActivity.onCreate()
  -> advertising id / SSAID resolution
  -> TicketListDao
    -> MyTicketService.MyTicketList
  -> TicketDetailDao per ticket
    -> RefundService.SelTicketInfo
  -> local IssueList/TicketDetail/SMSData refresh
  -> ticket actions: return, receipt, seat change, delivery, self check-in
```

### Request construction and API

- `TicketListActivity.x1(deviceId)` builds `TicketListDao.TicketListRequest`: `txtDeviceId`, `txtIndex=1`, `h_page_no=1`, empty date range, and member/non-member identity. Non-member sends `hiduserYn=N`, `hidName`, `hidTeleNo`, `hidPwd`; member sends `hiduserYn=Y`. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:961-984`]
- `TicketListDao.executeDao()` maps the request to `MyTicketService.getTicketList(...)`, endpoint `POST /classes/com.korail.mobile.myTicket.MyTicketList`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java:376-386`, `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/MyTicketService.java:15-18`]
- For every returned ticket, `TicketListActivity.o1()` builds `TicketDetailDao.TicketDetailRequest` from original ticket fields `h_orgtk_wct_no`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, plus `h_purchase_history=N`, then calls ticket detail API. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:944-959`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:23-25`]

### Response handling and navigation

- On ticket list response, the activity clears local issue/ticket detail caches, handles `P114` no-ticket message, caches encrypted issue list for logged-in users, reorders ticket list, then chains ticket-detail requests. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1416-1454`]
- On ticket detail response, it accumulates detail rows for each reservation, deletes stale SMS data by PNR, calls `setList()`, and loads MAAS detail for logged-in users. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1455-1496`]
- Return action opens `TicketReturnActivity` or `LimousineReturnActivity` with `TICKET_RESPONSE`, filtering out non-returnable seat type 20. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1288-1298`]
- Ticket seat change opens `TCSActivity` with `TICKET_RESPONSE` and `TICKET_TRAIN_RESPONSE`. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1301-1313`]

## 7. Refund / 반환

### Call graph

```text
TicketListActivity inline return OR TicketReturnActivity
  -> RefundCommissionDao
    -> RefundService.CommissionView
  -> user confirmation / before-departure policy branch
  -> RefundDao
    -> RefundService.RefundsRequest
  -> RailPlus sync if stl_mns_cd == 13
  -> completion dialog -> ticket list refresh/finish
```

### Request construction and API

- Inline return in `TicketListActivity.n1()` builds `RefundCommissionRequest` from first train/ticket detail original-ticket fields and companion name/birth fields. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:926-941`]
- `TicketReturnActivity` base class method `H0()` does the same per selected ticket in `TICKET_RESPONSE`. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:343-360`]
- `RefundCommissionDao.executeDao()` calls `POST /classes/com.korail.mobile.refunds.CommissionView` with `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_comp_nm`, `h_comp_cert_no`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundCommissionDao.java:112-122`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:19-21`]
- `TicketListActivity.r1()` and `TicketReturnActivity.J0()` build `RefundDao.RefundRequest` with `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, mileage settlement flag, return-timing division code, train number, PBP flag, and optional latitude/longitude. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:990-1002`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:370-404`]
- `RefundDao.executeDao()` calls `POST /classes/com.korail.mobile.refunds.RefundsRequest`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundDao.java:140-151`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:27-29`]

### Response handling and navigation

- Commission response codes `WRT800078` and `WRT800179` show repurchase/return choice dialogs; otherwise the refund confirmation UI proceeds. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1498-1519`]
- Dedicated return activity accumulates commission responses for all selected tickets, then either shows before-departure dialog or executes refund. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:473-491`]
- Refund response `stlList` is scanned for settlement method `13`; if found, RailPlus sync is invoked. Then a completion dialog is shown. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1521-1539`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:493-517`]

## 8. Pass / 정기권·패스

### Call graph

```text
APassBookingActivity / NewAPassBookingActivity / GangneungPassBookingActivity
  -> DiscountMenu/EnableDate/CmtrInfo setup
  -> PassReservationDao
    -> PassService.passOtrReserve
  -> PassPaymentDao.PassPaymentRequest
  -> PaymentActivity

CommutationInquiryActivity
  -> CommRsvInquiryDao
    -> passScheduleInfoList
  -> CommReservationDao
    -> passReserve
  -> CReservationConfirmActivity
  -> CommPaymentDao via PaymentActivity
```

### Pass reservation request

- `APassBookingActivity.H0()` builds `PassReservationDao.PassReservationRequest` with `hidCmtrKndCd`, `hidCmtrUtlAgeCd`, `hidCmtrUtlTrmCd`, `hidUseOpenDt` from selected pass kind/age/period/open date and executes `PassReservationDao`. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java:156-176`]
- `PassReservationDao.executeDao()` calls `PassService.passReservation(...)`, endpoint `POST /classes/com.korail.mobile.pass.passOtrReserve`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassReservationDao.java:160-170`, `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassService.java:43-45`]
- On `dao_pass_reservation`, the activity converts response `MainInfo` to a map for `PassPaymentRequest`, copies received amount, companion fields (`h_cmpa_cnt`, `h_cmpa_nm_i`, `h_cmpa_btdt_i`, `h_cmpa_sex_dv_cd_i`), optional `hidWctNo`, then starts `PaymentActivity` with `PAYMENT_REQUEST`, `RECEIVED_AMOUNT`, `DISCOUNT_AMOUNT=0`, and `DISABLE_DISCOUNT_POINT` for certain pass kind. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java:279-287`, `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/pass/APassBookingActivity.java:538-560`]

### Commutation inquiry/reservation

- `CommutationInquiryActivity.v0()` sends `CommRsvInquiryDao` with schedule query request fields such as selected page/count and suppresses `WRG000000`. `PassService.getCommRsvInquiry()` endpoint is `POST /classes/com.korail.mobile.pass.passScheduleInfoList`. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/CommutationInquiryActivity.java:178-186`, `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassService.java:27-29`]
- Selecting a schedule calls `u0(index)`, which builds `CommReservationRequest`. It copies commutation kind/period/age/open date, station display info, and each train leg’s departure/arrival station, train no, train group, detour, and transfer station fields. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/CommutationInquiryActivity.java:172-221`]
- `PassService.commReservation()` endpoint is `POST /classes/com.korail.mobile.pass.passReserve`; payment uses `POST /classes/com.korail.mobile.pass.passPayIssue`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassService.java:19-25`]
- On commutation reservation success, `CommutationInquiryActivity.z0()` converts response `main_info` to `CommPaymentRequest`, packages it into `CReservationData`, adds reservation notice messages, and opens `CReservationConfirmActivity`. [source: `analysis/jadx/sources/com/korail/talk/ui/inquiry/CommutationInquiryActivity.java:235-259`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/CommutationInquiryActivity.java:284-304`]

## 9. WebView / 웹 연동 및 scheme bridge

### Call graph

```text
IntegrationWebViewActivity.onCreate()
  -> BaseWebViewActivity.d1(JS bridge, cache mode)
  -> WebViewClient/ChromeClient setup
  -> BaseWebViewActivity.V0()
    -> WEB_POST_JSON_BODY JSON POST, or
    -> WEB_POST_URL postUrl, or
    -> WEB_GET_URL loadUrl
  -> JS interface callbacks or shouldOverrideUrlLoading scheme handling
  -> native DAO / Activity navigation
```

### Intent extras and load behavior

- WebView entry supports `WEB_POST_URL`, `WEB_GET_URL`, `WEB_POST_PARAMETER`, `WEB_GET_PARAMETER`, `WEB_POST_JSON_BODY`, `IS_SRT_WEB_RESERVE`, `IS_WEB_DEFAULT_PARAMETER`, `IS_MAAS_URL`, `IS_MAP_VIEW`, `IS_SCREEN_FULL`. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1008-1060`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:182-199`]
- `V0()` adds `K4.g.COMMON_PARAMETER` by default, appends caller parameters, then uses `postUrl()` for POST or `loadUrl()` for GET. If `IS_SRT_WEB_RESERVE` and `WEB_POST_JSON_BODY` are present, it performs manual JSON POST on a background thread. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1008-1060`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:830-919`]
- SRT web reserve responses and redirects normalize `http://*.srail.kr` to HTTPS, and Set-Cookie headers are copied into Android WebView cookies. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:921-957`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:959-975`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:997-1005`]
- WebView setup enables JavaScript, geolocation, DOM storage, multiple windows, mixed-content compatibility mode, third-party cookies, and appends `korailtalk AppVersion/{version}` to the user agent. The JavaScript interface is registered under `K4.g.PUSH_APPTYPE` (the app type string used by the service). [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:928-936`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:1097-1133`]

### JavaScript bridge callbacks

- `BaseWebViewActivity.c` exposes `@JavascriptInterface` methods including `appBack`, `windowClose`, `login`, `certificationIdSuccess`, `certificationPwSuccess`, `goPayment`, `goMaasPayment`, `moveToTrainTime`, `identityVerificationSuccess`, `nonmember`, `nonmemberResult`, `cartlist`, loading dialog controls, language/home/refresh callbacks. Each method posts a numeric message to the activity handler. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:303-445`, `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:480-502`]
- Native-to-web callback uses `K0(JSONObject)`: it extracts `callback`, removes it from JSON, and calls either `javascript:callback()` or `javascript:callback('{json}')`. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:977-990`]

### Scheme handling and native outcomes

- `IntegrationWebViewActivity` overrides URL loading. For `korailtalk://productTrainSearch`, it parses `trnGpCd`, `type`, `startStation`, `endStation`, `jobDv`, then executes `TourTrainInfoDao`; response opens `DiscountTourTrainBookingActivity` with tour train data and route extras. [source: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:47-65`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:130-159`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:253-261`]
- `korailtalk://payment` parses `strVrRsNo`, `strGdSqno`, calls `ProductPaymentCheckDao`, then starts `PaymentActivity` with an integrated-settlement request, amount, selected count, point-step flag, and `IS_TRAVEL_PACKAGES=true`. [source: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:119-128`, `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:167-180`]
- `korailtalk://login` delegates to native login. `korailtalk://supermove` maps query parameters (`txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, passenger flags, seat attributes, train group/menu id) into `ReceiveSRTData`, serializes it as `PARAM`, and restarts `IntroActivity`; startup then forwards it to `MainBookingActivity`. [source: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:63-91`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:480-486`]
- OnePass WebView scheme handling extracts `userKey` from the return URI, returns it to `LoginActivity`, and finishes; unsupported app intent schemes can open installed apps or Google Play. [source: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java:724-758`, `analysis/jadx/sources/com/korail/talk/ui/login/member/LoginActivity.java:246-253`]

## 요약: 주요 UI -> DAO/API 매핑

| Flow | UI anchor | Request/DAO | API endpoint | Primary callback outcome |
|---|---|---|---|---|
| Startup | `IntroActivity` | `ServiceCheckDao`, `CommonCodeDao`, `AppDataDao`, `NoticeDao`, `TrainCalendarDao`, `StationInfoDao`, `StationDataDao` | cache/common/calendar/station endpoints | common-code 저장, station DB 갱신, auto-login 또는 main 이동 |
| Login | `LoginActivity`, `K5.b` | `LoginDao`, `AutoLoginDao`, `EasyLoginDao` | `/classes/com.korail.mobile.login.Login` | 세션 쿠키 WebView 동기화, encrypted prefs 저장, caller result |
| Search | `MainBookingActivity`, `DirectInquiryActivity` | `TrainInquiryDao`, `ProductTrainInquiryDao` | `/classes/com.korail.mobile.seatMovie.ScheduleView` | train response -> UI bundles -> train selection |
| Reservation | `DirectInquiryActivity`/base inquiry classes | `ReservationDao`, `LReservationDao` | `/classes/com.korail.mobile.certification.TicketReservation`, `/classes/com.korail.mobile.nonMember.NonMemTicket` | disability/wait/round-trip/payment 분기 |
| Payment | `PaymentActivity`, `AbstractC1269e` | `RsvPaymentDao` plus pass/product variants | `/classes/com.korail.mobile.payment.ReservationPayment` | RailPlus/easy-pay 후처리, ticket list/trip list 이동 |
| Ticket | `TicketListActivity` | `TicketListDao`, `TicketDetailDao` | `/classes/com.korail.mobile.myTicket.MyTicketList`, `/classes/com.korail.mobile.refunds.SelTicketInfo` | local ticket cache rebuild, action screens |
| Refund | `TicketListActivity`, `TicketReturnActivity` | `RefundCommissionDao`, `RefundDao` | `/classes/com.korail.mobile.refunds.CommissionView`, `/classes/com.korail.mobile.refunds.RefundsRequest` | commission dialog, RailPlus sync, completion dialog |
| Pass | `APassBookingActivity`, `CommutationInquiryActivity` | `PassReservationDao`, `CommRsvInquiryDao`, `CommReservationDao`, `PassPaymentDao`, `CommPaymentDao` | `/classes/com.korail.mobile.pass.*` | pass/commutation confirmation then payment |
| WebView | `BaseWebViewActivity`, `IntegrationWebViewActivity` | URL extras, JS bridge, `ProductPaymentCheckDao`, `TourTrainInfoDao` | Web URLs plus product/tour APIs | native payment/tour/login/SRT search navigation |

## 20-agent follow-up audit 보강

- Payment row는 endpoint별로 더 세분화해야 한다. `RsvPaymentDao -> /classes/com.korail.mobile.payment.ReservationPayment`, `CommPaymentDao -> /classes/com.korail.mobile.pass.passPayIssue`, `PassPaymentDao -> /classes/com.korail.mobile.pass.passOtrPayIssue`, `IntgStlDao -> /classes/com.korail.mobile.pay.intgStl.do`다. `IntgStlDao.getId()`는 `dao_cart_payment`를 반환한다.
- Search row에서 product inquiry는 `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`을 사용한다. normal/product는 `InquiryDao` 계열 callback id `dao_train_inquiry`를 공유한다.
- Refund callback id는 `dao_ticket_commition`과 `dao_ticket_return`으로 구분된다.
- 공통 callback contract는 `com.korail.talk.view.base.a.executeDao()`를 쓰는 fragment caller도 포함해야 한다. 이 경우 `base.onReceive()`가 `K5.b`, `AbstractC1269e` 같은 fragment로 도착한다.
- 표에 없는 core flow도 별도 coverage 대상이다: PayService provider handoff(08), delay/compensation/reservation-cancel(10), XPoint/mileage/RailPlus(11), product/cart/add-service/gifticket/bus(12).
