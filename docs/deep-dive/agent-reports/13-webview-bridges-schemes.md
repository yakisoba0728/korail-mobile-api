# 13. WebView 브리지와 Scheme 처리 분석

## 분석 범위와 전제

이 문서는 로컬 정적 분석만으로 작성했다. 라이브 네트워크 호출, 앱 실행, 외부 서비스 접속은 수행하지 않았다.

분석 대상은 `BaseWebViewActivity`, `IntegrationWebViewActivity`, `EasyPayWebViewActivity`, `TrainServiceWebViewActivity`, `GovernmentCertificationActivity`, `MaumAIWebViewActivity`, JavaScript interface, WebView 설정, URL 로딩, intent extra, scheme 처리, SRT 연동이다.

주요 근거 파일:

- `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/MaumAIWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/certification/GovernmentCertificationActivity.java`
- `analysis/jadx/sources/ai/maum/m2u/cdk/CdkNative.java`
- `analysis/jadx/sources/ai/maum/m2u/cdk/JavaScriptReceiver.java`

## Manifest 노출면

`BaseWebViewActivity`와 `EasyPayWebViewActivity`는 `android:exported="false"`다. 반면 `IntegrationWebViewActivity`, `MaumAIWebViewActivity`, `TrainServiceWebViewActivity`, `GovernmentCertificationActivity`는 `android:exported="true"`로 선언되어 있다. `MaumAIWebViewActivity`는 `PHONE_STATE`, `NEW_OUTGOING_CALL` intent-filter도 가진다. 근거: `analysis/jadx/resources/AndroidManifest.xml:190-191`, `643-651`, `663-678`, `710-714`.

보안 경계 관점에서 중요한 점은 `IntegrationWebViewActivity`와 `TrainServiceWebViewActivity`가 exported 상태이면서 intent extra의 URL을 WebView에 직접 로드하는 구조라는 것이다. 코드상 activity 내부에서 URL host allowlist를 확인하는 로직은 보이지 않는다. 앱 내부 caller가 정상 URL을 넣는다는 가정에 강하게 의존한다.

## 공통 WebView 래퍼: BaseWebViewActivity

### JavaScript interface 등록

`BaseWebViewActivity.d1(Object obj, boolean z9)`가 WebView를 초기화하고 `addJavascriptInterface(obj, g.PUSH_APPTYPE)`를 호출한다. `g.PUSH_APPTYPE`는 `"korailtalk"`이므로 웹 페이지에서는 `window.korailtalk` 객체로 네이티브 브리지를 호출한다. 근거: `BaseWebViewActivity.java:1097-1104`, `K4/g.java:67`.

각 activity의 등록 객체:

- `IntegrationWebViewActivity`: `new BaseWebViewActivity.c()`를 `korailtalk`로 등록한다. 근거: `IntegrationWebViewActivity.java:194-199`.
- `EasyPayWebViewActivity`: `new BaseWebViewActivity.c()`를 `korailtalk`로 등록한다. 근거: `EasyPayWebViewActivity.java:57-66`.
- `TrainServiceWebViewActivity`: `new BaseWebViewActivity.c()`를 `korailtalk`로 등록한다. 근거: `TrainServiceWebViewActivity.java:51-55`.
- `MaumAIWebViewActivity`: `new BaseWebViewActivity.c()`를 `korailtalk`로 등록하고, 별도로 Maum SDK가 `m2uWebViewNative`를 추가 등록한다. 근거: `MaumAIWebViewActivity.java:137-140`, `CdkNative.java:464-469`.

### `korailtalk` bridge method 목록

아래 method는 `BaseWebViewActivity.c`의 `@JavascriptInterface`다. 모두 웹에서 앱으로 들어오는 호출면이다. 근거: `BaseWebViewActivity.java:299-503`.

| JavaScript method/signature | 앱으로 들어오는 데이터 | 네이티브 동작/앱 밖으로 나가는 데이터 |
| --- | --- | --- |
| `void appBack(String str)` | 문자열 인자 사용 안 함 | handler `APP_BACK(1)`로 뒤로가기 실행 |
| `void cartlist()` | 없음 | `BasketTicketActivity` 이동 후 `RESULT_OK` |
| `void certificationIdSuccess(String str)` | 사용자 ID 문자열 | `setResult(8)`와 extra `USER_ID=str` 후 종료 |
| `void certificationPwSuccess(String str)` | 사용자 PW 문자열 | `setResult(9)`와 extra `USER_PW=str` 후 종료 |
| `void changeLanguage(String str)` | 언어 타입 문자열 | SharedPreferences 성격의 `IS_MULTI_LANGUAGE_TYPE` 저장 |
| `void clearHistory()` | 없음 | WebView history 삭제 |
| `void fn_webViewOpenRsult(String str)` | 문자열 | 로그만 남김 |
| `void fn_webViewSeatSetResult(String str)` | 좌석 선택 JSON 문자열 예상 | Toast 표시, JSON parse 시도. parse 결과는 저장하지 않음 |
| `void goHome()` | 없음 | `MainBookingActivity` 이동 |
| `void goMaasPayment(String str)` | 상품/예약 번호 성격 문자열 | `PaymentActivity`로 `PAYMENT_MAAS`, `PRODUCT_NO=str`, `PNR_NO_LIST=[str]` 전달 |
| `void goPayment(String str)` | 상품/예약 번호 성격 문자열 | `PaymentActivity`로 `PAYMENT_PRODUCT`, `PRODUCT_NO=str`, `PNR_NO_LIST=[str]` 전달 |
| `void goSelectFromDate()` | 없음 | `RESULT_OK`, `MAAS_RESELECT_DATE_CODE=MAAS_SERVICE_RENTCAR_RENT_DATE`; 필요 시 `MAAS_RENTCAR_UI` 재전달 |
| `void goSelectToDate()` | 없음 | `RESULT_OK`, `MAAS_RESELECT_DATE_CODE=MAAS_SERVICE_RENTCAR_RETURN_DATE`; 필요 시 `MAAS_RENTCAR_UI` 재전달 |
| `void hideLoadingDialog(String str)` | 문자열 인자 사용 안 함 | 로딩 dismiss |
| `void identityVerificationSuccess(String str)` | 본인확인 결과 JSON/문자열 | `setResult(16)`, extra `IDENTITY_VERIFICATION_SUCCESS=str` |
| `void login(String str)` | 인증 결과 문자열 | `setResult(3)`, extra `USER_AUTHENTICATION=str` 후 종료 |
| `void moveToTrainTime(String str)` | `RsvInquiryResponse.TrainInfo` JSON 문자열 | JSON을 `TrainInfo`로 변환해 `TrainServiceInfoWebViewActivity`에 `TRAIN_INFO`로 전달 |
| `void nonmember()` | 없음 | `setResult(RESULT_OK)`와 intent type `"31"` 후 종료 |
| `void nonmemberResult(String str, String str2, String str3)` | 세 문자열 | `str;str2;str3`로 합쳐 extra `"32"`에 넣고 intent type `"32"` 반환 |
| `void refreshCustTrip()` | 없음 | `CONVENIENCE_SETTING_UPDATE=true` 저장 |
| `void sendCalendar(String str)` | JSON 문자열, `callback` 포함 가능 | 날짜 선택 dialog 실행. 선택 후 `K0()`로 JS callback 호출 |
| `void sessionExpired(String str)` | JSON 문자열, `callback` 포함 가능 | 자동 로그인 여부에 따라 로그인 이동 또는 재로그인. 로그인 성공 시 `K0()`로 callback |
| `void setTitle(String str)` | 제목 문자열 | 앱 title 변경 |
| `void showLoadingDialog(String str)` | 문자열 인자 사용 안 함 | 로딩 표시 |
| `void showToast(String str)` | Toast 메시지 | Toast 표시 |
| `void windowClose()` | 없음 | activity 종료 |

앱에서 웹으로 되돌려 보내는 공통 callback은 `K0(JSONObject)`다. JSON의 `callback` 값을 함수명으로 꺼내 제거한 뒤, 인자가 없으면 `javascript:callback()`, 남은 JSON이 있으면 `javascript:callback('JSON문자열')` 형태로 `loadUrl()`을 호출한다. 근거: `BaseWebViewActivity.java:977-991`.

### WebView 설정

공통 설정은 다음과 같다. 근거: `BaseWebViewActivity.java:1097-1133`.

- hardware layer 사용: `setLayerType(2, null)`
- horizontal scroll bar 비활성화
- JavaScript 활성화: `setJavaScriptEnabled(true)`
- geolocation 활성화: `setGeolocationEnabled(true)`
- database, DOM storage 활성화
- form data 저장 비활성화
- built-in zoom 활성화, display zoom control 비활성화
- overview/wide viewport 활성화
- multiple windows 활성화: `setSupportMultipleWindows(true)`
- text zoom 100
- mixed content mode `2`
- User-Agent 뒤에 `korailtalk AppVersion/<VERSION_NAME>` 추가

Geolocation prompt는 origin 검증 없이 `callback.invoke(str, true, false)`로 허용한다. 근거: `BaseWebViewActivity.java:136-144`.

새 창은 `WebChromeClient.onCreateWindow()`에서 별도 `WebView`를 dialog에 만들며, 이 child WebView도 JavaScript와 multiple window를 켠다. 다만 child WebView에는 `korailtalk` bridge를 추가하지 않는다. 근거: `BaseWebViewActivity.java:588-615`.

### URL 로딩과 POST/GET body 조립

기본 공통 파라미터는 `Device=AD&Version=250601003&Key=korail1234567890`이다. 근거: `K4/g.java:11`.

`V0()`가 일반 WebView 로딩 진입점이다. 근거: `BaseWebViewActivity.java:1008-1061`.

- `IS_SRT_WEB_RESERVE=true`이고 `WEB_POST_JSON_BODY`가 있으면 특수 JSON POST 경로로 간다.
- 일반 경로에서는 URL을 `WEB_POST_URL` 우선, 없으면 `WEB_GET_URL`에서 읽는다.
- parameter는 `WEB_POST_PARAMETER` 우선, 없으면 `WEB_GET_PARAMETER`에서 읽는다.
- `IS_WEB_DEFAULT_PARAMETER`가 기본값 `true`이면 공통 파라미터를 앞에 붙인다.
- `WEB_POST_URL`이 있으면 `postUrl(url, bodyBytes)`로 form-style body를 보낸다.
- `WEB_GET_URL`이면 `loadUrl(url + "?" + params)`로 GET query를 붙인다.
- `IS_MAAS_URL=true`인 GET은 기존 URL에 `?`가 있으면 `&params`, 없으면 `?params`를 붙인다.

`W0(String str)`는 강제 POST helper다. 대상 URL은 인자로 받고, body는 항상 공통 파라미터와 intent parameter를 조립해 `postUrl()`로 보낸다. `TrainServiceWebViewActivity`가 탭 전환 시 이 메서드를 사용한다. 근거: `BaseWebViewActivity.java:1063-1088`, `TrainServiceWebViewActivity.java:71-79`.

주의할 점: `V0()`는 내부 상태 `f30591r`에 `url + "?" + originalParam`을 저장하지만 실제 POST body에는 공통 파라미터를 포함한 `sb`를 사용한다. 즉 화면 상태/뒤로가기 비교용 URL 문자열과 실제 POST body가 다를 수 있다. 근거: `BaseWebViewActivity.java:1029-1049`.

### 공통 scheme 처리

`BaseWebViewActivity.e.shouldOverrideUrlLoading(WebView,String)`는 먼저 SRT HTTPS 보정 `U0()`을 수행한 뒤 `C0804d.isShouldOverrideUrlLoading()`에 위임한다. 근거: `BaseWebViewActivity.java:692-698`.

`C0804d.isShouldOverrideUrlLoading()` 정책:

- `javascript`, `about:blank`, `http`, `https`는 WebView가 계속 처리하도록 `false` 반환
- `tel:`은 전화 intent
- `market:`은 Play Store 이동
- `intent:`는 `G.playApp()`
- `korailtalk://stnLeadNavi?stnCd=...`는 역 안내 앱 intent로 변환
- 그 외 non-http(s) scheme은 `true` 반환하지만 별도 처리 없이 차단 성격으로 끝남

근거: `S4/C0804d.java:120-137`.

`WebResourceRequest` overload는 main frame에서 `U0()`만 처리하고 나머지는 `super.shouldOverrideUrlLoading()`으로 넘긴다. 근거: `BaseWebViewActivity.java:708-716`. 따라서 Android/WebView 버전에 따라 non-http(s) scheme 처리 경로가 String overload와 다르게 보일 수 있다.

## IntegrationWebViewActivity

### 초기화와 intent extra

`onCreate()`는 `activity_integration_webview`를 세팅하고, `MAAS_INFO` 또는 `MAAS_POPUP_IMAGE`가 있으면 dialog를 띄운다. `IS_SCREEN_FULL=true`이면 title app bar를 숨기고 drawer를 잠근다. 이후 `korailtalk` bridge, 커스텀 WebViewClient, WebChromeClient를 등록하고 `V0()`로 URL을 로드한다. 근거: `IntegrationWebViewActivity.java:109-117`, `182-200`, `242-250`.

받는 주요 extra:

- `WEB_POST_URL`, `WEB_GET_URL`
- `WEB_POST_PARAMETER`, `WEB_GET_PARAMETER`
- `WEB_POST_JSON_BODY`
- `IS_SRT_WEB_RESERVE`
- `IS_WEB_DEFAULT_PARAMETER`
- `IS_MAAS_URL`
- `IS_SCREEN_FULL`
- `IS_CLOSE_VIEW`
- `MAAS_INFO`, `MAAS_POPUP_IMAGE`
- `MAAS_RENTCAR_UI`

### `korailtalk://` scheme 처리

`IntegrationWebViewActivity.b.shouldOverrideUrlLoading()`는 공통 처리 후 `korailtalk` scheme의 authority를 직접 해석한다. 근거: `IntegrationWebViewActivity.java:47-106`.

| Scheme | Query/body | 네이티브 동작 |
| --- | --- | --- |
| `korailtalk://productTrainSearch` | `trnGpCd`, `type`, `startStation`, `endStation`, `jobDv` | `TourTrainInfoDao` 요청 후 성공 시 `DiscountTourTrainBookingActivity`로 이동. 전달 extra: `TITLE_NAME`, `TRN_GP_CD`, `START_STN`, `ARRIVAL_STN`, `JOB_DV`, `TOUR_TRAIN_DATA`. 근거: `IntegrationWebViewActivity.java:61-62`, `130-160`. |
| `korailtalk://payment` | `strVrRsNo`, `strGdSqno` | `ProductPaymentCheckDao` 요청 후 `PaymentActivity`로 이동. 전달 extra: `PAYMENT_TYPE=PAYMENT_DEFAULT`, `PAYMENT_REQUEST`, `IS_POINT_STEP=true`, `SELECTED_ITEM_COUNT=1`, `RECEIVED_AMOUNT`, `DISCOUNT_AMOUNT=0`, `IS_TRAVEL_PACKAGES=true`. 근거: `IntegrationWebViewActivity.java:63-64`, `119-128`, `167-180`. |
| `korailtalk://login` | 없음 | 로그인 화면 이동. 근거: `IntegrationWebViewActivity.java:65-66`. |
| `korailtalk://supermove` | SRT 검색 조건 query | `ReceiveSRTData`를 채워 JSON으로 `IntroActivity` extra `PARAM`에 전달하고 `603979776` flags를 추가. 근거: `IntegrationWebViewActivity.java:67-91`. |

`supermove`가 수집하는 query parameter는 `txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, `txtPsgFlg_1`~`txtPsgFlg_6`, `txtSeatAttCd_2`~`txtSeatAttCd_4`, `selGotrain`, `trnGpCd`, `txtMenuId`다. `ReceiveSRTData` 필드는 이 값을 보관하고 승객 수, 역, 달력 정보 계산 helper를 가진다. 근거: `IntegrationWebViewActivity.java:70-89`, `ReceiveSRTData.java:8-149`.

`tmobileid` 또는 `mobileid` scheme은 외부 앱으로 `ACTION_VIEW`를 시도하고, 앱이 없으면 Toast를 표시한다. 근거: `IntegrationWebViewActivity.java:93-101`.

### 뒤로가기와 화면 종료

SRT Web reserve 모드에서는 `N0()`가 true이며, WebView history가 있으면 back, 없으면 home navigation 후 종료한다. 일반 모드에서는 현재 URL이 최초 URL(`f30609w`)을 포함하고 `IS_CLOSE_VIEW`가 아니면 두 번 back 종료 토스트를 사용한다. 다국어 URL의 특정 path에서는 최초 URL로 다시 POST한다. 근거: `IntegrationWebViewActivity.java:217-240`.

## EasyPayWebViewActivity

### 초기화와 URL 로딩

`EasyPayWebViewActivity`는 공통 `korailtalk` bridge와 전용 WebViewClient를 등록하지만 `V0()`를 쓰지 않는다. `WEB_GET_URL`을 그대로 `loadUrl()`한다. 따라서 `COMMON_PARAMETER` 자동 추가나 `WEB_POST_PARAMETER` 처리가 이 activity에는 적용되지 않는다. 근거: `EasyPayWebViewActivity.java:57-66`.

추가 설정:

- `setMixedContentMode(0)`
- WebView cookie 허용
- third-party cookie 허용

근거: `EasyPayWebViewActivity.java:61-64`.

대표 caller:

- 일반 결제 fragment는 `EasyPayWebViewActivity`에 `WEB_GET_URL`을 넣고 startActivity/startActivityForResult 한다. 예: `stbkAcntStlR.do?...&trPrice=...`, `bcUsrAthnR.do?...&payAmt=...&insMmNum=...`. 근거: `B6/AbstractC1269e.java:284-293`, `369-379`.
- Toss auto 설정도 `WEB_GET_URL`만 넘긴다. 근거: `TossAutoSettingActivity.java:154-158`.

### approve/payment scheme 처리

전용 WebViewClient는 공통 scheme 처리 후 다음을 추가 처리한다. 근거: `EasyPayWebViewActivity.java:25-50`.

- `korailtalk://approve` 여부는 `D.isApproveScheme()`로 검사한다. 이 함수는 `uri.getScheme() + "://" + uri.getAuthority()`가 string resource `korailtalk://approve`와 같은지 본다. 근거: `S4/D.java:239-240`, `strings.xml:805-807`.
- approve scheme의 `type`이 `tossauto`가 아니면 동일 URL을 `ACTION_VIEW` intent로 다시 외부 dispatch한다. flags는 `603979776`.
- `type=tossauto`이고 `strResult=SUCCESS`이면 `RESULT_OK`, `strResult=FAIL`이면 `RESULT_CANCELED` 후 종료한다.
- Naver scheme이면 `G.playApp()`로 외부 앱 실행을 시도한다.

관련 payment scheme resource:

- `monimopay://?xid=%1$s&mrcType=KRT&callbackUrl=korailtalk://approve?type=monimopay`
- `korailtalk://approve?type=%1$s&bankCode=%2$s&password=%3$s`

근거: `strings.xml:1176-1177`, `1217`.

## TrainServiceWebViewActivity

`TrainServiceWebViewActivity`는 열차 서비스/시설 정보용 2-tab WebView다. `WEB_POST_URL`을 1번 탭 URL, `WEB_POST_URL_2`를 2번 탭 URL로 받는다. `WEB_POST_URL_2`가 없으면 tab click listener를 제거한다. 근거: `TrainServiceWebViewActivity.java:26-43`.

초기 로딩과 탭 전환은 모두 `W0(url)`을 사용한다. 즉 실제 요청은 POST이고 body는 항상 `COMMON_PARAMETER`와 intent의 `WEB_POST_PARAMETER` 또는 `WEB_GET_PARAMETER`를 조합한 값이다. caller 예시는 `TicketListActivity.moveToTrainFacility(String str, String str2)`가 두 URL을 각각 extra로 넣는 흐름이다. 근거: `TrainServiceWebViewActivity.java:51-55`, `71-79`, `TicketListActivity.java:1330-1334`.

`d1(new BaseWebViewActivity.c(), true)`로 초기화하므로 cache mode는 `LOAD_DEFAULT(-1)`이고 `f30590q=true`가 되어 destroy 시 cache clear를 건너뛴다. 근거: `BaseWebViewActivity.java:1108-1115`, `1185-1195`.

## GovernmentCertificationActivity

이 activity는 WebView가 아니라 정부/모바일 신분증 앱과 앱 간 인증 scheme을 중계한다.

입력 extra:

- `JOURNEY_INFO`: 화면에 표시할 여정 정보 문자열. `DirectInquiryActivity`가 출발일, 열차그룹/번호, 출발/도착역, 시간 정보를 조립해 전달한다. 근거: `GovernmentCertificationActivity.java:50-57`, `DirectInquiryActivity.java:470-492`.

Step 1:

- 버튼 클릭 시 `GovernmentCertificationStep1Dao`를 실행한다. 근거: `GovernmentCertificationActivity.java:73-77`, `96-101`.
- endpoint는 `GET /classes/com.korail.mobile.pbep.toknCre.do`이고 query는 `Device`, `Version`이다. 응답은 `csrfToken`, `app` 문자열을 가진다. 근거: `CertificationService.java:39-40`, `GovernmentCertificationStep1Dao.java:11-24`, `60-65`.

외부 scheme 생성:

- 응답 `app` JSON에서 `sp_did`, `service_code`, `callback_url`, `nonce`, `encrypt_type`, `sessionId`를 꺼낸다.
- `bmc://verify_vp?appName=korailtalk&type=VERIFY&spDid=...&serviceCode=...&callBackUrl=...&nonce=...&encryptType=...&sessionId=...` 형태로 만든다.
- `Intent("kr.go.id.bmc.VERIFY_VP", Uri.parse(...))`를 `startActivityForResult(..., 100)`로 실행한다.

근거: `GovernmentCertificationActivity.java:141-165`, `strings.xml:805`.

Step 2:

- 외부 인증 activity 결과가 requestCode `100`, result `RESULT_OK`, data query `result=true`이면 Step 2 DAO를 실행한다. 근거: `GovernmentCertificationActivity.java:87-93`.
- endpoint는 `GET /classes/com.korail.mobile.pbep.sttChck.do`이고 query는 `Device`, `Version`, `csrfToken`이다. 근거: `CertificationService.java:42-43`, `GovernmentCertificationStep2Dao.java:57-62`.
- 응답의 `pbepInfo`를 저장하고 확인 버튼을 활성화한다. 확인 버튼 클릭 시 `setResult(RESULT_OK)`와 extra `PBEP_INFO=pbepInfo`를 caller에 반환한다. 근거: `GovernmentCertificationActivity.java:107-110`, `125-137`.

## MaumAIWebViewActivity와 `m2uWebViewNative`

### 초기화 흐름

`MaumAIWebViewActivity`는 `IntegrationWebViewActivity` 레이아웃을 사용한다. `MAAS_INFO`, `MAAS_POPUP_IMAGE`, `IS_SCREEN_FULL` 처리 방식은 Integration과 유사하다. 근거: `MaumAIWebViewActivity.java:105-141`, `197-208`.

`onResume()`에서 `RECORD_AUDIO`, `MODIFY_AUDIO_SETTINGS` 권한을 확인하고 허용되면 `V0()`로 WebView를 로드한다. 그 뒤 `CdkNative(K(), webView, f30621w)`를 생성한다. `CdkNative` 생성자는 `initWebView()`에서 `m2uWebViewNative` bridge를 추가하고 `initUrl`을 로드한다. 근거: `MaumAIWebViewActivity.java:252-259`, `CdkNative.java:367-369`, `464-469`, `978-990`.

주의: `f30621w`는 권한 허용 callback 안에서 `V0()` 호출 후 `f30591r.toString()`로 설정된다. 하지만 `CdkNative` 객체는 `onCreate()` 말미에서 생성되므로, 정적 코드상 생성 시점의 `initUrl`이 null일 가능성이 있다. JADX 결과만으로 런타임 순서 보정 여부는 확인되지 않는다. 근거: `MaumAIWebViewActivity.java:63-67`, `197-208`.

### `m2uWebViewNative` bridge method 목록

Maum SDK의 `JavaScriptReceiver`가 `m2uWebViewNative`로 등록된다. 근거: `CdkNative.java:464-469`.

| JavaScript method/signature | 웹에서 앱으로 들어오는 데이터 | 네이티브 동작/웹으로 나가는 데이터 |
| --- | --- | --- |
| `void closeMicrophone()` | 없음 | gRPC 초기화 시 microphone close |
| `void closeSpeaker()` | 없음 | gRPC 초기화 시 speaker close |
| `String getPhoneNumber()` | 없음 | `TelephonyManager.getLine1Number()`에서 `+82`를 `0`으로 치환한 전화번호 반환. 실패 시 `""` |
| `void openMicrophone(String str)` | microphone parameter JSON/문자열 | gRPC 초기화 시 microphone open |
| `void sendEvent(String str)` | protobuf JSON 형태의 EventStream 문자열 | `Map.EventStream`으로 merge 후 gRPC event stream 전송. 특정 speech/stream operation이면 microphone start/timer 처리 |
| `void setMapSetting(String str)` | map setting JSON/문자열 | SDK map setting 저장 |

근거: `JavaScriptReceiver.java:25-95`.

Maum SDK는 앱에서 웹으로도 여러 JavaScript callback을 호출한다. 예: `receiveError(...)`, `receiveCompleted(...)`, `receiveStreamingDirective(...)`, `receiveException(...)`, `receiveDirective(...)`, `notifyPong(...)`, `notifyMicrophoneStatus(...)`, `onScreenLockChanged(...)`, `onPause()`, `onResume()`, `notifySpeakerStatus(...)`, `sendStreamingEvent(...)`. 근거: `CdkNative.java:139`, `202`, `233`, `238`, `275`, `343`, `687`, `734`, `774`, `816`, `820`, `828`, `836`.

## SRT Web reserve 연동

### SRT URL

`SRT_WEB_RESERVATION_URL`는 `https://` + server type별 `eapp` 또는 `teapp` + `.srail.kr/`로 구성된다. 현재 상수 구성상 DEV가 아니면 `https://eapp.srail.kr/`다. Web reserve caller는 여기에 `web/reserve`를 붙인다. 근거: `K4/g.java:73-78`, `116-120`.

### JSON POST 로딩

SRT reserve는 `IntegrationWebViewActivity`를 열면서 다음 extra를 넣는다.

- `WEB_POST_URL = g.SRT_WEB_RESERVATION_URL + "web/reserve"`
- `WEB_POST_JSON_BODY = <SRT reserve JSON>`
- `IS_SRT_WEB_RESERVE = true`
- `IS_WEB_DEFAULT_PARAMETER = false`

근거: `DirectInquiryActivity.java:388-395`, `TransferInquiryActivity.java:122-129`, `TicketListActivity.java:1046-1053`.

`BaseWebViewActivity.V0()`는 이 조합을 감지해 `X0(url, body)`를 호출한다. `X0()`/`S0()`는 별도 thread에서 `HttpURLConnection`을 열고:

- method를 POST로 설정
- connect/read timeout 60초
- `Content-Type: application/json; charset=utf-8`
- `Accept: text/html,application/json,*/*`
- UTF-8 JSON body를 fixed length로 write
- 응답 code가 400 이상이면 error stream, 아니면 input stream을 읽음
- `Set-Cookie` header를 Android WebView `CookieManager`에 반영
- 최종 URL과 HTML body 안의 `http://teapp.srail.kr`, `http://app.srail.kr`을 HTTPS로 치환
- `/webapp/` URL이면 `loadUrl(finalUrl)`, 아니면 `loadDataWithBaseURL(finalUrl, body, mime, "UTF-8", null)`

근거: `BaseWebViewActivity.java:910-919`, `830-875`, `921-926`, `955-974`, `807-823`.

### SRT JSON body 필드

직통 SRT reserve JSON은 `DirectInquiryActivity.b3()`가 만든다. top-level 필드:

- `reserveType`: `"reserve"` 또는 seat map이면 `"seatmap"`
- `mutMrkVrfCd`
- `radJobId`
- `dptRstnCd`
- `arvRsStnCd`
- `goStart`, `goEnd`
- `dptDt`, `dptTm`
- `psgFlg1`~`psgFlg6`
- `seatAttCd`
- `trnGpCd`
- `trainList`

`trainList` entry 필드:

- `chtnDvCd`, `chtnTrnOrdrNo`
- `trnNo`, `trnGpCd`, `trnGpNm`
- `stlbTrnClsfCd`, `stlbTrnClsfNm`
- `runDt`, `dptDt`, `dptTm`, `arvDt`, `arvTm`
- `dptRsStnCd`, `arvRsStnCd`
- `dptStnConsOrdr`, `arvStnConsOrdr`, `dptStnRunOrdr`, `arvStnRunOrdr`
- `seatAttCd`, `rsvPsbFlg`, `ticketType`, `psrmClCd`, `totPrnb`, `goStart`, `goEnd`

근거: `DirectInquiryActivity.java:167-189`, `192-224`.

환승 SRT reserve JSON은 `TransferInquiryActivity.S2()`가 만든다. top-level은 직통과 유사하지만 `dptRsStnCd`, `arvRsStnCd`, `goStart`, `goEnd`, `dptDt`, `dptTm`, 승객 플래그, `seatAttCd`, `trnGpCd="300"`, `trainList`를 사용한다. `trainList` entry는 `R2()`가 만든다. 근거: `TransferInquiryActivity.java:40-73`, `76-106`.

티켓 목록에서 SRT 예약을 이어가는 경우도 같은 `IntegrationWebViewActivity` JSON POST 경로를 사용한다. `TicketListActivity.d1()`는 `reserveType="reserve"`, `mutMrkVrfCd`, `radJobId`, 출도착/승객/좌석/열차 그룹, `trainList`를 만든다. 근거: `TicketListActivity.java:728-757`, `1038-1053`.

### SRT에서 Korail 앱으로 되돌아오는 `supermove`

SRT 웹이 `korailtalk://supermove?...`를 호출하면 `IntegrationWebViewActivity`가 query를 `ReceiveSRTData`로 변환하고 `IntroActivity`로 넘긴다. `IntroActivity`는 extra `PARAM` JSON을 다시 `ReceiveSRTData`로 파싱해 `data_from_SRT`로 전달한다. 근거: `IntegrationWebViewActivity.java:67-91`, `IntroActivity.java:471-485`.

## 세션과 쿠키 동작

앱 application singleton은 Java `java.net.CookieManager`를 만들고 `CookiePolicy.ACCEPT_ALL`로 설정한다. 근거: `KTApplication.java:72-75`.

로그인 DAO는 로그인 API 호출 직후 `KTApplication.getInstance().setSessionId()`를 호출한다. `setSessionId()`는 Java CookieStore에서 `JSESSIONID`를 찾아 Android WebView `CookieManager`에 `z.getSSLHost()` 기준으로 `JSESSIONID=value`를 설정하고 flush한다. 근거: `LoginDao.java:236-242`, `KTApplication.java:105-115`, `129-131`, `S4/z.java:46-53`.

SRT JSON POST는 WebView 자체의 network stack이 아니라 `HttpURLConnection`으로 먼저 호출한다. 이때 응답 `Set-Cookie` header를 Android WebView cookie jar에 수동으로 복사한다. 근거: `BaseWebViewActivity.java:959-974`.

EasyPay와 SRT 특수 경로는 third-party cookie를 명시적으로 허용한다. EasyPay 근거: `EasyPayWebViewActivity.java:61-64`. SRT 특수 경로 근거: `BaseWebViewActivity.java:928-936`.

앱 logout/초기화 성격의 `clearCookie()`는 Android WebView cookie를 모두 지우고 Java CookieManager를 재초기화한다. 근거: `KTApplication.java:99-103`.

## 보안 경계 메모

- `addJavascriptInterface`는 로드된 모든 페이지 origin에 `korailtalk` 객체를 제공한다. URL host allowlist가 WebView wrapper에 없으므로, intent extra로 임의 URL이 들어올 수 있는 exported activity에서는 bridge 노출 범위가 핵심 위험면이다. 근거: `BaseWebViewActivity.java:1103`, `AndroidManifest.xml:643-665`.
- `korailtalk` bridge에는 결제 이동, 로그인 결과 반환, 본인확인 결과 반환, 앱 종료, 외부 activity 이동, preferences 변경, Toast 표시 등이 포함된다. 웹 컨텐츠가 신뢰된 origin이라는 전제가 필요하다. 근거: `BaseWebViewActivity.java:303-503`.
- `GovernmentCertificationActivity`는 exported이고 `JOURNEY_INFO`를 받아 화면에 표시한 뒤 외부 `bmc://verify_vp`/`kr.go.id.bmc.VERIFY_VP` flow를 시작한다. 실제 인증 서버 token은 DAO에서 받아오지만, activity entry 자체는 외부 호출 가능하다. 근거: `AndroidManifest.xml:674-678`, `GovernmentCertificationActivity.java:50-57`, `141-165`.
- default `WebChromeClient` 경로의 `GeolocationPermissions`는 prompt origin별 판단 없이 허용한다. 다만 주요 WebView activity는 별도 `BaseWebViewActivity.d` client로 교체되므로, 자동 허용은 default client가 남는 경로로 한정한다. 위치 권한 자체는 Android permission에 따르겠지만, WebView origin boundary는 계속 핵심 확인 지점이다. 근거: `BaseWebViewActivity.java:140-144`.
- file chooser는 `GET_CONTENT */*`를 허용한다. 웹 origin이 파일 선택 UI를 열 수 있고 결과 URI가 WebView로 돌아간다. 근거: `BaseWebViewActivity.java:656-668`.
- mixed content mode가 공통 설정에서 `2`, EasyPay에서 `0`으로 설정된다. 상수 의미는 SDK별 API 값에 의존하지만, 결제/WebView별 mixed content 정책이 서로 다르다. 근거: `BaseWebViewActivity.java:1128`, `EasyPayWebViewActivity.java:61`.
- network security config는 `teapp.srail.kr`, `app.srail.kr` 등에 cleartext를 허용한다. SRT WebView 코드는 HTTP SRT URL을 HTTPS로 치환하지만, 앱 전체 network policy에는 cleartext 허용 도메인이 남아 있다. 근거: `network_security_config.xml:3-11`, `BaseWebViewActivity.java:921-926`, `955-956`.
- Maum `m2uWebViewNative.getPhoneNumber()`는 전화번호를 웹에 반환한다. Android/통신사 환경에 따라 빈 문자열일 수 있지만, WebView origin 신뢰가 중요하다. 근거: `JavaScriptReceiver.java:43-50`.

## 20-agent follow-up audit 보강

- MaumAI init order는 `onCreate()`에서 `CdkNative(K(), webView, f30621w)`가 먼저 만들어지고, permission callback이 `f30621w`를 이후 설정하는 구조다. `CdkNative.initWebView()`가 `m2uWebViewNative` 등록과 `initUrl` load를 intended URL 설정보다 먼저 실행할 수 있다.
- exported surface에는 `ExtraProductWebViewActivity`도 포함한다. 이 activity는 `BaseWebViewActivity`를 상속하고 `korailtalk` bridge를 등록하며 `V0()`을 호출한다.
- scheme handler는 overload별 기능 차이가 있다. `korailtalk://payment`, `supermove`, `approve`, Naver 등 activity-specific handler는 String overload에 있고, `WebResourceRequest` path는 SRT HTTPS correction 중심이다.
- Maum callback은 bare global 함수가 아니라 `javaScript:<notifyObjectPrefix>.…` 형태로 emit될 수 있다.
