# 18. Retrofit 외 URL/리소스/Smali 문자열 분석

분석 대상은 `korail.apk` (`com.korail.talk` 6.5.0)이다. 이 문서는 Retrofit service interface의 `@GET`/`@POST` endpoint 목록을 제외하고, 코드 상수, WebView URL, 리소스 문자열, AndroidManifest scheme/query, assets/properties, smali fallback에서 확인한 URL/host/path/scheme을 정리한다. Retrofit endpoint 본문은 `docs/api-endpoints.md`를 기준으로 별도 범위로 본다.

분석은 정적 로컬 분석만 수행했다. 근거 경로는 임시 decode 산출물 기준으로 `jadx:sources/...`, `apktool:res/...`, `apktool:smali.../...` 형식으로 표기한다.

## 요약

| 분류 | 핵심 발견 |
|---|---|
| 운영/환경 host | 운영은 `https://smart.letskorail.com`, 다국어는 `https://www.korail.com`, SRT WebView는 `https://eapp.srail.kr/`, NetFunnel은 `nf.letskorail.com`으로 고정된다. dev/staging host 문자열도 코드에 남아 있다. |
| WebView/API-like path | `/ebizmk/*`, `/ebizprd/*`, `/returninfo/*`, `/classes/com.korail.mobile.onepass.login.do`, `/classes/com.korail.mobile.pay.stbkAcntStlR.do`, `/classes/com.korail.mobile.pay.bcUsrAthnR.do` 등 Retrofit 밖 WebView/브라우저 호출이 있다. |
| 외부/서드파티 | Naver OAuth/API, Kakao OAuth, Google/Firebase/Ads, SRT, Railbot, HappyTalk, Lotte Global Logistics, LOST112, GIS, RailPlus/Railpoint/rail police 앱 연동이 확인된다. |
| 앱 scheme | inbound `korailtalk://navigation`, `korailtalk://member_info`, `korailtalk://approve`, `korailtalk://railpluscardinfo`, Kakao/Naver OAuth callback이 manifest에 선언된다. outbound payment/app scheme도 다수 존재한다. |
| Smali fallback | JADX와 대체로 일치하지만 smali에서 `nf.letskorail.com`, `korailtalk://stnLeadNavi`, `content://com.h2osystech.smartalimi.ServiceAlimiData.korail`, `bmc://verify_vp?...`, STBK/BC WebView 결제 path를 재확인했다. |
| 미확정 | push payload URL, common-code의 `linkUrl`/`lotteglogisURL`, Payco/NaverPay/SamsungPay 후속 URL은 서버 응답 기반이므로 정적 분석만으로 전체 목적지와 파라미터 스키마를 확정할 수 없다. |

## 운영/환경 Host 및 공통 상수

| 값 | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `https://smart.letskorail.com` | 운영 API/Web host | `jadx:sources/S4/z.java:48`, `jadx:sources/K4/g.java:92` | Retrofit base URL 및 WebView URL 조합에 사용 | 내부 | `SERVER_TYPE = EnumC5607a.fromCode("3")`라 운영 REAL로 해석된다. |
| `https://www.korail.com` | 다국어 예약 Web host, 회원 찾기 | `jadx:sources/S4/z.java:38`, `jadx:sources/K4/g.java:16` | WebView GET/POST 또는 외부 브라우저 | 내부/계열 | `MULTI_LANGUAGE_URL = https://www.korail.com/global/`, `FIND_ALL_URL`도 동일 host. |
| `https://mobiledev.letskorail.com` | 개발 host fallback | `jadx:sources/S4/z.java:48` | 개발/비운영 endpoint | 내부 | 운영 빌드에서는 선택되지 않지만 문자열 잔존. |
| `https://dev2.letskorail.com` | staging host | `jadx:sources/S4/z.java:48` | staging endpoint | 내부 | `EnumC5607a.STAGING`일 때 사용. |
| `https://dev3.letskorail.com` | test host | `jadx:sources/S4/z.java:48` | test endpoint | 내부 | `EnumC5607a.TEST`일 때 사용. |
| `https://dev5.letskorail.com` | 다국어 test host | `jadx:sources/S4/z.java:38` | 다국어 test WebView | 내부 | REAL/STAGING이 아니면 다국어 host로 사용. |
| `smart.letskorail.com`, `smartbeta.letskorail.com`, `dev.letskorail.com`, port `3101` | H2O SmartAlimi push address | `jadx:sources/S4/z.java:43`, `jadx:sources/K4/g.java:66` | push 모듈 서버 접속 | 내부/벤더 연동 | 운영은 `smart.letskorail.com`; staging/test는 `smartbeta.letskorail.com`. |
| `nf.letskorail.com` | NetFunnel queue server | `apktool:smali/com/korail/talk/application/KTApplication.smali:321` | queue token/traffic control | 내부/벤더 | smali에서 직접 확인. service id는 `service_1`, action id는 `act_8`, `act_14`, `act_18` 등. |
| `https://eapp.srail.kr/` | SRT Web reservation | `jadx:sources/K4/g.java:130` | WebView/JSON POST 가능 | 외부/철도 계열 | DEV일 때는 `https://teapp.srail.kr/`. |
| `http://teapp.srail.kr`, `http://app.srail.kr` -> HTTPS 치환 | SRT cleartext 링크 보정 | `jadx:sources/com/korail/talk/ui/web/BaseWebViewActivity.java:956` | 응답 HTML 내부 링크 치환 | 외부/철도 계열 | `network_security_config`에는 cleartext 허용 도메인도 남아 있다. |
| `Device=AD&Version=250601003&Key=korail1234567890` | WebView/간편결제 공통 query | `jadx:sources/K4/g.java:10` | 앱 식별자, 버전, 공통 key 전송 | 내부 | Retrofit `BaseRequest`와 동일 계열의 공통 파라미터다. |

## KORAIL WebView/브라우저 URL

| URL/path | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `/ebizmk/member/mk_join_member.do` | 회원가입 WebView | `jadx:sources/K4/g.java:92` | 공통 파라미터 또는 WebView session/cookie | 내부 | `z.getWebHost()`와 조합. |
| `/ebizmk/member/mk_check_member.do` | 회원번호/ID 찾기 | `jadx:sources/K4/g.java:93` | 사용자 식별 입력을 WebView에서 처리 | 내부 | Web flow. |
| `/ebizmk/member/mk_pass_member.do` | 비밀번호 찾기 | `jadx:sources/K4/g.java:94` | 본인확인/비밀번호 재설정 데이터 | 내부 | Web flow. |
| `https://www.korail.com/ticket/membership/findMember` | 통합 회원 찾기 | `jadx:sources/K4/g.java:16` | 브라우저/WebView | 내부/계열 | 고정 absolute URL. |
| `/ebizmk/prd/main.do` | 관광/상품 메인 | `jadx:sources/K4/g.java:95` | 상품 조회 WebView | 내부 | `TOUR_PACKAGE_URL`. |
| `/ebizmk/notice/list_plus.do` | 공지 목록 | `jadx:sources/K4/g.java:96` | 공지 목록 수신 | 내부 | WebView. |
| `/ebizmk/notice/detail.do` | 공지 상세 | `jadx:sources/K4/g.java:97`, `jadx:sources/K4/g.java:103` | `bbrdId`, `ptwtSqno`, offset 등 | 내부 | 지연배상 안내와 QR 안내에서도 사용. |
| `/ebizmk/qna/list_plus.do` | 고객 안내/QNA | `jadx:sources/K4/g.java:98` | WebView | 내부 | `GUIDE_URL`. |
| `/ebizmk/prd/voucher.do` | 여행/상품권 | `jadx:sources/K4/g.java:99` | WebView | 내부 | `VOUCHER_URL`. |
| `/ebizmw/w_adv03105.do` | 제휴/광고/파트너 | `jadx:sources/K4/g.java:100` | WebView | 내부 | `PARTNER_URL`. |
| `/docs/hc/hc12200/cmtr_tos.html?tabId=1` | 정기권/통근권 안내 | `jadx:sources/K4/g.java:101` | 정적 HTML 수신 | 내부 | `CMTR_INFO_URL`. |
| `/returninfo/html/returnchginfo.html` | 승차권 반환수수료 안내 | `jadx:sources/K4/g.java:104`, `jadx:sources/com/korail/talk/view/base/BaseActivity.java:92` | WebView POST URL로 열림 | 내부 | `IS_CLOSE_VIEW=true`로 안내 화면 사용. |
| `/returninfo/html/returnchginfo.html?tabId=4` | 리무진 수수료 안내 | `jadx:sources/K4/g.java:105`, `jadx:sources/com/korail/talk/view/base/BaseActivity.java:92` | WebView | 내부 | 리무진 안내 링크. |
| `/returninfo/html/luggageinfo.html` | 유실물/수하물 안내 | `jadx:sources/K4/g.java:106` | 정적 HTML 수신 | 내부 | 앱 내 안내. |
| `/returninfo/html/ncard_guide01.html`, `ncard_guide02.html`, `ncard_guide03.html` | N카드 구매/주의/종합 안내 | `jadx:sources/K4/g.java:54`, `apktool:smali/k6.1/a$a.smali:48` 등 | 정적 HTML 수신 | 내부 | Java와 smali 모두 확인. |
| `/korail/com/mypage/preset/m_preset_list.do` | 위젯/즐겨찾기 편의설정 | `jadx:sources/K4/g.java:112`, `jadx:sources/com/korail/talk/provider/WidgetReceiver.java:171` | 로그인 상태일 때 WebView POST URL | 내부 | 위젯 favorite 클릭 시 사용. |
| `/ticket/guest/ktxService` | 이용약관/서비스 안내 | `jadx:sources/K4/g.java:114` | WebView | 내부/계열 | `TERMS_URL`. |
| `/docs/guide/chairinfo.html` | 휠체어/교통약자 안내 | `jadx:sources/K4/g.java:116` | 정적 HTML 수신 | 내부 | `WHEELCHAIR_TOOLS_URL`. |
| `/ebiztids/EbizTidsList.do` | TIDS 역/서비스 목록 | `jadx:sources/K4/g.java:117` | `dptRsStnCd` 파라미터 가능 | 내부 | `TIDS_PARAM = dptRsStnCd`. |
| `https://info.korail.com/info/contents.do?key=2812` | 개인정보처리방침 | `jadx:sources/K4/g.java:59`, `apktool:smali/X5/f$a.smali:73` | 외부 브라우저/WebView | 내부/계열 | `info.korail.com` 별도 host. |
| `https://smart.letskorail.com/ebizcom/event/tourist/EbizcomEvtTourWcus06701_detail.do?searchKeyword2=271` | 여행 QR 인증 위치 안내 | `jadx:sources/K4/g.java:84`, `apktool:smali/com/korail/talk/ui/menu/TripQrAuthActivity.smali:568` | 안내 페이지 수신 | 내부 | `TripQrAuthActivity`에서 사용. |
| `https://smart.letskorail.com/ebizmk/notice/detail.do?bbrdId=000000000031&ptwtSqno=363` | 여행 QR 인증 상품 안내 | `jadx:sources/K4/g.java:85`, `apktool:smali/com/korail/talk/ui/menu/TripQrAuthActivity.smali:611` | 공지 상세 수신 | 내부 | 고정 notice id. |

## Retrofit 외 API-like Path

| URL/path | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `/classes/com.korail.mobile.certification.MCertify.do` | 본인 인증 WebView | `jadx:sources/K4/g.java:111` | WebView에서 인증 데이터/세션 처리 | 내부 | Retrofit interface가 아닌 WebView URL 상수. |
| `/classes/com.korail.mobile.mypage.mCertify.do` | 마이페이지 휴대폰 인증 | `jadx:sources/K4/g.java:113` | 인증 입력/결과 | 내부 | WebView URL. |
| `/classes/com.korail.mobile.onepass.login.do` | OnePass 로그인/연동 WebView | `jadx:sources/com/korail/talk/ui/login/member/LoginActivity.java:219`, `jadx:sources/com/korail/talk/ui/mypage/MyPageActivity.java:543` | WebView GET; callback scheme에서 `userKey` 수신 | 내부 + 외부 인증앱 | `OnepassWebViewActivity`는 `kr.go.gfido.m` intent와 `intent://`를 처리. |
| `/classes/com.korail.mobile.pay.stbkAcntStlR.do?` | 세틀뱅크 내통장결제 WebView 결제 | `jadx:sources/B6/AbstractC1269e.java:171`, `apktool:smali/b6.1/e$a.smali:1065` | `Device`, `Version`, `Key`, `trPrice` 전송 | 내부/결제연동 | Retrofit interface에는 없는 WebView payment URL. |
| `/classes/com.korail.mobile.pay.bcUsrAthnR.do?` | BC 사용자 인증/결제 WebView | `jadx:sources/B6/AbstractC1269e.java:174`, `apktool:smali/b6.1/e$a.smali:1229` | `Device`, `Version`, `Key`, `payAmt`, `insMmNum` 전송 | 내부/결제연동 | installment month는 선택값 없으면 `00`. |
| push payload path + `z.getWebHost()` | push 알림 랜딩 WebView | `jadx:sources/com/korail/talk/receiver/PushBroadcastReceiver.java:32` | `MSGVo.url`이 내부 WebView URL로 조합됨; `param.isExternalBrowser=Y`면 외부 브라우저 | 내부/외부 동적 | 정적 문자열로 전체 path는 확정 불가. |
| 서버 응답 `easyPayData.linkUrl` | 간편결제 이벤트/안내 링크 | `jadx:sources/C6/d.java:162` | linkType이 외부/내부에 따라 외부 브라우저 또는 WebView | 내부/외부 동적 | common-code 응답에 의해 결정. |
| Payco `orderSheetUrl` | Payco 결제 sheet | `jadx:sources/B6/AbstractC1269e.java:1174` | 서버 응답 URL을 WebView로 로드 | 외부/결제 | 정확한 host/path는 런타임 응답 필요. |
| NaverPay `stlScnUrl` | NaverPay 결제 화면 | `jadx:sources/B6/AbstractC1269e.java:1189` | 서버 응답 URL을 WebView로 로드 | 외부/결제 | 정확한 URL은 런타임 응답 필요. |
| Samsung/Monimo `fllwScnAppUrlAdr` | Samsung Pay류 후속 결제 화면 | `jadx:sources/B6/AbstractC1269e.java:1180` | 서버 응답 URL 또는 app scheme 실행 | 외부/결제 | Monimo는 별도 app scheme 사용. |

## 지도, 위치, 고객지원, 안내 외부 URL

| URL/scheme | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `https://gis.korail.com/korailTalk/entrance` | 열차 지도/역 안내 WebView | `jadx:sources/K4/g.java:83`, `jadx:sources/com/korail/talk/ui/web/BaseWebViewActivity.java:899` | 지도 URL 로드, WebView location 사용 가능 | 내부/계열 | BaseWebView가 이 URL을 특수 처리. |
| `https://gis.korail.com/korailTalk/entrance?route=ticket&trnNo=...&stnCd=...&date=...&lon=...&lat=...` | 승차권 열차 위치/지도 | `jadx:sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java:415`, `apktool:smali/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.smali:3788` | 열차번호, 출발역코드, 날짜, 단말 위경도 전송 가능 | 내부/계열 | 위치 권한/last known location 사용. |
| `https://railbot.korail.com/#/chatbot`, `#/voiceChatbot` | KORAIL chatbot/voice chatbot | `jadx:sources/t5/e.java:80`, `apktool:smali/t5.1/e.smali:503` | `custMgNo`, `mbCrdNo`, `hdcpFlg`, `custClCd`, `custLeadFlg`, `theme` query 전송 | 내부/계열 | DEV는 `https://dev-railbot.korail.com/...`. |
| `https://customer.happytalk.io/public_v1/chat_v4/public_point?...&uid=%1$s` | 청각장애/고객상담 채팅 | `apktool:res/values/strings.xml:906`, `jadx:sources/X5/f.java:552`, `jadx:sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:853` | 암호화된 회원카드번호로 보이는 `uid` 전송 | 외부/상담 SaaS | 외부 브라우저 실행. |
| `letskorail.com/happy_talk/initChat.html` | WebView 내 해피톡 예외 처리 | `apktool:smali/com/korail/talk/ui/web/BaseWebViewActivity$f.smali:421` | URL override 예외 | 내부/상담 | smali에서 문자열 확인. |
| `https://m.lost112.go.kr/` | 경찰청 유실물 조회 | `jadx:sources/K4/g.java:32`, `jadx:sources/l4/p.java:48` | 외부 브라우저 | 외부/공공 | 분실물 안내. |
| `https://blog.naver.com/korailblog/223673675369?...` | 리무진 이용안내 블로그 | `jadx:sources/K4/g.java:31`, `apktool:smali/com/korail/talk/ui/limousine/LimousineActivity.smali:2007` | 외부 브라우저/WebView | 외부/네이버 | 여러 리무진 activity에서 반복 사용. |
| `https://www.lotteglogis.com/mobile/reservation/smallunmanned/index` | 철도택배/무인소형 예약 | `apktool:res/values/strings.xml:764`, `jadx:sources/X5/f.java:575` | 외부 브라우저 | 외부/제휴 | common-code `lotteglogisURL`이 있으면 서버 응답 URL로 override. |
| `https://www.hometax.go.kr` | 현금영수증 안내 문구 | `apktool:res/values/strings.xml:1780` | 텍스트 안내 | 외부/공공 | 직접 호출 근거는 확인하지 못함. |
| `tel:1588-7788`, `tel:1544-8787`, `tel:1588-7722` | 고객센터/환불/철도경찰 전화 | `apktool:res/values/strings.xml:1201`, `:1283`, `:1545`; `jadx:sources/S4/C0804d.java:128` | `ACTION_CALL`/전화 intent | 외부/전화망 | `CALL_PHONE` 권한 존재. |

## 다국어 및 SRT Web 연동

| 값 | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `https://www.korail.com/global/` | 다국어 예약 base | `jadx:sources/K4/g.java:107` | WebView | 내부/계열 | REAL/STAGING에서 사용. |
| `eng/ticket/reservation`, `chn/ticket/reservation`, `jpn/ticket/reservation`, `tw/ticket/reservation`, `id/ticket/reservation`, `th/ticket/reservation`, `vi/ticket/reservation` | 언어별 예약 path | `jadx:sources/K4/g.java:23-29` | WebView path segment | 내부/계열 | back navigation에서 `/ticket/reservation` 포함 여부를 검사. |
| `https://eapp.srail.kr/` | SRT 예약 WebView | `jadx:sources/K4/g.java:130` | WebView, JSON POST 가능 | 외부/철도 계열 | `BaseWebViewActivity.X0()`는 JSON body를 직접 POST. |
| `korailtalk://supermove?...` | SRT -> KORAIL 검색조건 전달 | `jadx:sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:58` | `txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, 승객 수, 좌석속성, 열차그룹, menu id 수신 | 내부 app scheme | SRT WebView에서 앱 화면으로 조건 전달. |

## 결제/외부 앱 Scheme

| scheme/template | 목적 | 소스 | 송수신 추정 | 내부/외부 | 대상 패키지/비고 |
|---|---|---|---|---|---|
| `korailtalk://approve?type=%1$s&bankCode=%2$s&password=%3$s` | 앱 내부 결제 callback, STBK 계좌 등록/비밀번호 변경 | `apktool:res/values/strings.xml:1445`, `jadx:sources/com/korail/talk/ui/stbk/StbkRegisterAccountListActivity.java:322` | `type`, `bankCode`, `password`, 또는 결제사별 query bundle 수신 | 내부 inbound | `PaymentActivity`가 manifest에서 `korailtalk://approve` 수신. 운영 빌드에서 cold-start approve intent는 바로 finish하고, 실행 중 `onNewIntent` callback이 주 경로로 보인다. |
| `monimopay://?xid=%1$s&mrcType=KRT&callbackUrl=korailtalk://approve?type=monimopay` | Monimo Pay 실행 | `apktool:res/values/strings.xml:1400`, `jadx:sources/B6/AbstractC1269e.java:1183` | `xid`/준비번호 전송, callback으로 `otcNo`, `card_code`, `otcIsAkDtm`, `cdno_id` 등 수신 | 외부/결제 | package `net.ib.android.smcard`. |
| `kb-screen://pay?movingScrenType=KBPayA2A&moveURL=%1$s` | KB Pay 실행 | `apktool:res/values/strings.xml:1383`, `jadx:sources/B6/AbstractC1269e.java:1168` | URL-encoded payload: `REQ_DATE_TIME`, `CHANNEL_ID`, 상품정보, 암호화 금액, 사업자번호, 가맹점명/번호, 할부개월 | 외부/결제 | package `com.kbcard.cxh.appcard`. |
| `shinhan-appcard://korail-otc?storename=%1$s&payamount=%2$s` | Shinhan FAN/appcard 실행 | `apktool:res/values/strings.xml:1451`, `jadx:sources/B6/AbstractC1269e.java:1161` | seed encrypt 결과값 2개를 storename/payamount로 전달 | 외부/결제 | package `com.shcard.smartpay`. |
| `railplus://payment?AMOUNT=%1$s&KORAIL_ID=%2$s` | RailPlus 결제 | `apktool:res/values/strings.xml:1439`, `jadx:sources/B6/AbstractC1269e.java:345` | 금액, KORAIL member id | 외부/결제 | package `com.mic.set.hce.railpluscardserviceandroid`. |
| `railplus://zeropay_payment?AMOUNT=%1$s&KORAIL_ID=%2$s` | RailPlus ZeroPay 결제 | `apktool:res/values/strings.xml:1493`, `jadx:sources/B6/AbstractC1269e.java:382` | 금액, member id | 외부/결제 | 동일 RailPlus package. |
| `railplus://cardinfo` | RailPlus 카드정보 | `apktool:res/values/strings.xml:1438`, `jadx:sources/com/korail/talk/ui/railPlus/RailPlusActivity.java:121` | 카드정보 앱 화면 실행 | 외부/결제/카드 | package `com.mic.set.hce.railpluscardserviceandroid`. |
| `railpointapp://default?cid=%1$s&cust_no=%2$s` | Railpoint 앱 실행 | `apktool:res/values/strings.xml:1524`, `jadx:sources/X5/f.java:453` | 암호화 회원카드번호, 암호화 고객번호 | 외부/멤버십 | package `com.railpoint`. |
| `krailwaypolice://crime.report?h_trn_no=%1$s&h_scar_no=%2$s&h_seat_no=%3$s&h_dpt_dt=%4$s&h_gff_dt=%5$s` | 철도경찰 신고 앱 | `apktool:res/values/strings.xml:1546`, `jadx:sources/Y4/Q.java:225` | 열차번호, 객차, 좌석, 출발/도착 일시 | 외부/공공 안전 | package `com.RLP.railpolice`; Play Store URL도 리소스에 존재. |
| `korail_app_link://userservice?servicetype=%1$s&stationtype=%2$s` | 역 안내/동선 안내 앱 | `apktool:res/values/strings.xml:1776`, `jadx:sources/S4/C0804d.java:134` | service type, `stnCd`에서 온 station type | 외부/제휴 | `korailtalk://stnLeadNavi?stnCd=...`를 받아 package `com.korail.futuretech.userservice`로 전달. |
| `market://details?id=...`, `https://play.google.com/store/apps/details?id=...`, `https://onesto.re/0000751454` | 앱 설치 fallback | `jadx:sources/S4/G.java:92`, `:96`, `:109` | package id | 외부/마켓 | OneStore flag가 있으면 OneStore URL 사용. |

## 로그인/인증/OAuth URL 및 Scheme

| 값 | 목적 | 소스 | 송수신 추정 | 내부/외부 | 비고 |
|---|---|---|---|---|---|
| `kakao<KORAIL-APP-KAKAO-APP-KEY-REDACTED>://oauth` | Kakao OAuth callback | `apktool:AndroidManifest.xml:131-136`, `apktool:res/values/strings.xml:947` | OAuth code/result | 외부/카카오 | `AuthCodeHandlerActivity` exported. |
| `naver3rdpartylogin://authorize/` | Naver OAuth callback | `apktool:AndroidManifest.xml:308-313` | OAuth result | 외부/네이버 | `OAuthCustomTabActivity` exported. |
| `https://nid.naver.com/oauth2.0/authorize?`, `/token?`, `/nidlogin.login?`, `/nidlogin.logout?` | Naver OAuth SDK | `apktool:smali/com/nhn/android/naverlogin/connection/gen/OAuthQueryGenerator.smali:286`, `:366`; `CommonLoginQuery.smali:22` | OAuth code/token/login/logout | 외부/네이버 | SDK 내부 문자열. |
| `https://openapi.naver.com/v1/nid/me` | Naver profile API | `jadx:sources/K4/g.java:42`, `apktool:smali/c5.1/b$c.smali:104` | access token으로 사용자 profile 수신 | 외부/네이버 | 앱 자체 상수로도 보관. |
| `bmc://verify_vp?appName=korailtalk&type=VERIFY&spDid=...` | 모바일 신분증 검증 | `jadx:sources/com/korail/talk/ui/certification/GovernmentCertificationActivity.java:147`, `apktool:smali/...GovernmentCertificationActivity.smali:617` | 서버 응답 `sp_did`, `service_code`, `callback_url`, `nonce`, `encrypt_type`, `sessionId` 전달 | 외부/공공 인증 | intent action `kr.go.id.bmc.VERIFY_VP`. |
| `mobileid`, `tmobileid` | 모바일 신분증 app scheme | `apktool:AndroidManifest.xml:52`, `:56`, `apktool:res/values/strings.xml:1085`, `:2005` | WebView에서 외부 앱으로 verify intent 실행 | 외부/공공 인증 | package query에도 선언. |
| `korailtalk://certify` | OnePass callback 판별 | `apktool:res/values/strings.xml:950`, `jadx:sources/S4/u.java:135` | `userKey` query 수신 | 내부 inbound | manifest 직접 선언은 확인되지 않으며 WebView callback 판별용으로 보인다. |
| `korailtalklite://member_info?value=%1$s` | 로그인 데이터 전달 | `apktool:res/values/strings.xml:495`, `jadx:sources/com/korail/talk/ui/scheme/DataActivity.java:77` | loginType, loginId, loginPw, auto-login flags를 JSON/Base64/common encrypt 후 전달 | 외부/동일 생태계 앱 추정 | `DataActivity`는 inbound `korailtalk://member_info` 후 이 scheme으로 재전송한다. |

## 내부 Navigation/Inbound Scheme

| scheme/path | 수신 Activity | 목적 | 소스 | 송수신 추정 | 비고 |
|---|---|---|---|---|---|
| `korailtalk://navigation?view=booking` | `NavigationActivity` | 예매 화면 이동 | `apktool:AndroidManifest.xml:181-186`, `apktool:res/values/strings.xml:1200` | `view` query와 intent extras | 위젯/리소스에서 사용. |
| `korailtalk://navigation?view=ticket` | `NavigationActivity` | 승차권 확인 | `apktool:res/values/strings.xml:1211`, `jadx:sources/com/korail/talk/provider/WidgetReceiver.java:182` | `view=ticket` | 위젯 check 클릭. |
| `korailtalk://navigation?view=web` | `NavigationActivity` | WebView 화면 이동 | `apktool:res/values/strings.xml:1217`, `jadx:sources/com/korail/talk/receiver/PushBroadcastReceiver.java:34` | push URL extra와 함께 사용 | push 내부 WebView fallback. |
| `korailtalk://navigation?view=banner`, `delayDiscountCoupon`, `discountCoupon`, `discountMenuList`, `memberCard`, `mileage`, `offlineTicketRefund`, `periodSeasonTicket`, `pushHistory`, `seasonTicket`, `ticketRefund`, `togetherMileage`, `tourMenuList`, `tourReserved` | `NavigationActivity` | 앱 내 각 메뉴 deep link | `apktool:res/values/strings.xml:1199-1215` | `view` query | `S4.y.getNavigationBundle()`/`getClassNm()`로 화면 매핑. |
| `korailtalk://member_info` | `DataActivity` | 로그인 정보 송신 trigger | `apktool:AndroidManifest.xml:189-194` | 저장 로그인 정보 복호화 후 `korailtalklite://member_info?value=...`로 송신 | exported, transparent activity. |
| `korailtalk://approve` | `PaymentActivity` | 외부 결제 callback | `apktool:AndroidManifest.xml:197-202`, `jadx:sources/com/korail/talk/ui/payment/PaymentActivity.java:665` | 모든 query를 bundle로 수집; `otcNo` 공백은 `+`로 보정 | 결제 fragment가 후속 처리. |
| `korailtalk://railpluscardinfo` | `RailPlusActivity` | RailPlus 카드정보 진입 | `apktool:AndroidManifest.xml:207-212` | 별도 query 없음 | exported. |
| `korailtalk://productTrainSearch?...` | `IntegrationWebViewActivity` WebView bridge | 관광열차 검색 이동 | `jadx:sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:48` | `trnGpCd`, `type`, `startStation`, `endStation`, `jobDv` | manifest inbound는 아니고 WebView URL override 경로. |
| `korailtalk://payment?strVrRsNo=...&strGdSqno=...` | `IntegrationWebViewActivity` WebView bridge | 여행상품 결제 이동 | `jadx:sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:50`, `:119` | `strVrRsNo`, `strGdSqno`로 `ProductPaymentCheckDao` 실행 | WebView 내부 bridge. |
| `korailtalk://login` | `IntegrationWebViewActivity` WebView bridge | 로그인 화면 이동 | `jadx:sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:52` | 없음 | WebView 내부 bridge. |
| `korailtalk://stnLeadNavi?stnCd=...` | `C0804d.isShouldOverrideUrlLoading()` | 역 안내 외부 앱으로 변환 | `apktool:smali/com/korail/talk/ui/ticket/service/AdditionalServiceActivity.smali:2463`, `jadx:sources/S4/C0804d.java:134` | `stnCd`를 `korail_app_link://userservice`에 반영 | smali로 literal 확인. |

## Manifest Package Queries 및 외부 Intent 가시성

| 패키지/intent | 목적 분류 | 소스 | 내부/외부 | 비고 |
|---|---|---|---|---|
| `com.nhnent.payapp` | 결제 | `apktool:AndroidManifest.xml:28` | 외부 | NHN Pay app 가시성. |
| `com.ssg.serviceapp.android.egiftcertificate` | 상품권/결제 | `apktool:AndroidManifest.xml:29` | 외부 | SSG e-gift certificate. |
| `com.kakao.talk`, `com.kakao.talk.alpha`, `com.kakao.talk.sandbox`, `com.kakao.onetalk` | Kakao login/share | `apktool:AndroidManifest.xml:30`, `:81-83` | 외부 | Kakao SDK package query. |
| `com.nhn.android.search` | Naver app login | `apktool:AndroidManifest.xml:31` | 외부 | Naver SDK download banner도 이 package 사용. |
| `kr.go.mobileid`, `kr.go.mobileid.tbe`, `kr.go.gfido.m` | 모바일 신분증/OnePass | `apktool:AndroidManifest.xml:32-33`, `:41` | 외부/공공 인증 | `mobileid`, `tmobileid`, `kr.go.gfido.m` intent 처리. |
| `com.samsung.android.spay`, `com.samsung.android.spaylite`, `com.lge.lgpay`, `com.shcard.smartpay`, `com.kbcard.cxh.appcard`, `net.ib.android.smcard` | 간편결제/appcard | `apktool:AndroidManifest.xml:34-37`, `:43-44` | 외부/결제 | Samsung/LG/Shinhan/KB/Monimo 계열. |
| `kvp.jjy.MispAndroid320`, `com.lottemembers.android`, `com.ahnlab.v3mobileplus` | 포인트/보안/결제 보조 | `apktool:AndroidManifest.xml:38-40` | 외부 | 정확한 런타임 호출 지점은 추가 동적 확인 필요. |
| `com.RLP.railpolice` | 철도경찰 신고 | `apktool:AndroidManifest.xml:42` | 외부/공공 안전 | railpolice scheme target. |
| `android.intent.action.VIEW` + `scheme="*"` + `host="*"` | 임의 VIEW intent query | `apktool:AndroidManifest.xml:45-49` | 외부 | Android 11+ package visibility를 넓게 열어둔다. |
| `verify` + `mobileid`, `verify` + `tmobileid` | 모바일 신분증 verify | `apktool:AndroidManifest.xml:50-57` | 외부/공공 인증 | scheme query. |
| `android.intent.action.VIEW` + `BROWSABLE` + `https` | HTTPS browser/custom tab 확인 | `apktool:AndroidManifest.xml:61-65` | 외부 | 외부 브라우저 가시성. |
| `android.support.customtabs.action.CustomTabsService` | Custom Tabs | `apktool:AndroidManifest.xml:67` | 외부 | Naver/Kakao/OAuth browser flow 관련. |
| `com.noshufou.android.su`, `eu.chainfire.supersu`, `com.topjohnwu.magisk` 등 root packages | root 탐지 | `apktool:AndroidManifest.xml:69-80` | 외부/보안 | package visibility로 설치 여부 확인 가능. |

## Resource/Assets/Properties

| 항목 | 값/내용 | 소스 | 목적 | 비고 |
|---|---|---|---|---|
| SmartAlimi provider authority | `com.h2osystech.smartalimi.ServiceAlimiData.korail` / `content://com.h2osystech.smartalimi.ServiceAlimiData.korail` | `apktool:res/values/strings.xml:57`, `apktool:smali_classes2/com/h2osystech/smartalimi/servicealimimodule/DataProvider.smali:27` | push/service alimi content provider | smali에서 content URI literal 확인. |
| Firebase database URL | `https://<KORAIL-APP-FIREBASE-PROJECT-REDACTED>.firebaseio.com` | `apktool:res/values/strings.xml:856` | Firebase config | API key/app id/storage bucket도 resource에 존재. |
| Google API/App config | `google_api_key`, `google_app_id`, `google_storage_bucket` | `apktool:res/values/strings.xml:894-897` | Google/Firebase SDK 초기화 | Android app config 값. |
| Kakao app key | `<KORAIL-APP-KAKAO-APP-KEY-REDACTED>` | `apktool:res/values/strings.xml:947` | Kakao SDK/OAuth callback scheme | manifest callback scheme과 동일. |
| `network_security_config.xml` | cleartext 허용: `1.255.59.22`, `bot-dev-lb-...naverncp.com`, `teapp.srail.kr`, `app.srail.kr` | `apktool:res/xml/network_security_config.xml:3-8` | 일부 cleartext 허용 | 코드에서는 SRT HTTP 링크를 HTTPS로 치환하지만 정책상 허용은 남아 있다. |
| Google/Ads/Firebase properties | `firebase-messaging 21.0.0`, `play-services-ads 23.2.0`, `play-services-auth 19.0.0` 등 | `apktool:unknown/*.properties` | SDK 버전 metadata | 직접 URL은 아니지만 외부 SDK 통신 근거. |
| Maum AI proto resources | `maum/m2u/*`, `google/api/*`, `io.grpc` service metadata | `apktool:unknown/maum/...`, `apktool:unknown/META-INF/services/io.grpc.*` | AI/chatbot gRPC/protobuf 모델 | host는 코드에서 Railbot Web URL로 확인, proto 자체에는 endpoint host 없음. |
| Assets | `gangneungPass.text`, `kt_01to13_reMix_ep40.tflite`, `map_01.png`-`map_07.png`, `cardscan.txt`, `code1ocr.lic`, font | `apktool:assets/*` | UI/ML/OCR/static map assets | `strings` scan 기준 URL literal은 발견되지 않음. |
| Library attribution URLs | RoundedImageView, ZXing, ORMLite, protobuf docs 등 | `apktool:res/values/strings.xml:952-968`, `jadx:resources/...` | OSS notice/metadata | 런타임 통신 목적 URL로 보지 않음. |

## Smali Fallback 확인 결과

| 문자열 | smali 소스 | JADX 상태 | 의미 |
|---|---|---|---|
| `nf.letskorail.com` | `apktool:smali/com/korail/talk/application/KTApplication.smali:321` | 일반 Java 검색에서는 상수 위치가 덜 명확 | NetFunnel host. |
| `content://com.h2osystech.smartalimi.ServiceAlimiData.korail` | `apktool:smali_classes2/com/h2osystech/smartalimi/servicealimimodule/DataProvider.smali:27` | resource authority와 결합 필요 | SmartAlimi content provider URI. |
| `/classes/com.korail.mobile.pay.stbkAcntStlR.do?` | `apktool:smali/b6.1/e$a.smali:1065`, `apktool:smali/b6.1/e.smali:87` | `jadx:sources/B6/AbstractC1269e.java`에서 확인됨 | STBK WebView 결제 URL. |
| `/classes/com.korail.mobile.pay.bcUsrAthnR.do?` | `apktool:smali/b6.1/e$a.smali:1229`, `apktool:smali/b6.1/e.smali:95` | `jadx:sources/B6/AbstractC1269e.java`에서 확인됨 | BC 인증/결제 WebView URL. |
| `korailtalk://stnLeadNavi` | `apktool:smali/com/korail/talk/ui/ticket/service/AdditionalServiceActivity.smali:2463` | Java에 contains check로 보임 | station guide 외부 앱 bridge. |
| `bmc://verify_vp?appName=` | `apktool:smali/com/korail/talk/ui/certification/GovernmentCertificationActivity.smali:617` | Java에서 동적 조립 확인 | 모바일 신분증 검증 app scheme. |
| `http://teapp.srail.kr`, `http://app.srail.kr` | `apktool:smali/com/korail/talk/ui/web/BaseWebViewActivity.smali:1554`, `:1570` | Java에서 HTTPS 치환 확인 | SRT 링크 보정. |
| `https://railbot.korail.com/#/chatbot`, `#/voiceChatbot` | `apktool:smali/t5.1/e.smali:503`, `:511` | Java에서 확인 | Railbot URL. |
| `https://blog.naver.com/korailblog/...` | `apktool:smali/com/korail/talk/ui/limousine/*.smali` | `K4.g`와 각 Activity에서 확인 | 리무진 안내. |

## 제3자 SDK/라이브러리 URL 노이즈 처리

아래는 APK에 포함되어 있으나 앱 도메인 로직보다 SDK 내부 통신/문서/테스트 문자열 성격이 강한 항목이다. 보고서 본문에는 목적별로 필요한 항목만 반영했다.

| 그룹 | 예시 | 판단 |
|---|---|---|
| Google Ads/AdMob | `googleads.g.doubleclick.net`, `pagead2.googlesyndication.com`, `adservice.google.com`, `imasdk.googleapis.com`, `admob-gmats.uc.r.appspot.com` | Google Mobile Ads SDK 내부 로더/진단/광고 URL. 앱의 KORAIL 업무 API로 분류하지 않음. |
| Google/Firebase docs/errors | `firebase.google.com/support/privacy/init-options`, `developers.google.com/...`, `g.co/dev/packagevisibility` | SDK 오류 메시지 또는 문서 URL. |
| Android/XML namespace | `http://schemas.android.com/apk/res/android`, `http://schemas.android.com/apk/res-auto` | XML namespace. 통신 URL 아님. |
| ORMLite/OSS notice | `ormlite.com`, GitHub/OSS links | license/notice. |
| H2O sample image | `http://upload.wikimedia.org/...JPEG_example...jpg` | SmartAlimi library utility/sample 문자열. 앱 업무 호출 근거 없음. |

## 열린 Gap

| Gap | 영향 | 후속 확인 방법 |
|---|---|---|
| push `MSGVo.url` | 내부 WebView path 또는 외부 브라우저 URL이 서버 payload로 결정된다. 정적 APK만으로 전체 URL 목록을 확정할 수 없다. | FCM/H2O push payload 샘플 또는 런타임 notification intent 캡처. |
| common-code 동적 URL | `easyPayData.linkUrl`, `lotteglogisURL`, 결제 이벤트 링크가 서버 응답으로 내려온다. | `/classes/com.korail.mobile.common.code.do` 응답 샘플 확인. |
| 외부 결제 후속 URL | Payco `orderSheetUrl`, NaverPay `stlScnUrl`, Samsung Pay `fllwScnAppUrlAdr`는 결제 API 응답 기반이다. | 결제 sandbox/운영 응답 캡처 없이 host/path 확정 불가. |
| WebView intent extra `WEB_GET_URL`/`WEB_POST_URL` | 여러 Activity가 intent extra로 임의 URL을 받아 WebView에 로드한다. 모든 caller의 동적 값은 정적 분석만으로 완전 열거하기 어렵다. | `WEB_GET_URL`, `WEB_POST_URL` runtime intent 생성 로그/트래픽 수집. |
| `korailtalk://approve` cold-start 처리 | 운영 REAL에서는 approve scheme으로 새로 열린 `PaymentActivity`가 즉시 finish한다. 실제 결제 callback은 기존 singleTask instance의 `onNewIntent` 경로로 보인다. | 실제 외부 결제 app callback lifecycle 확인. |
| package query 중 미사용/난독화 호출 | `kvp.jjy.MispAndroid320`, `com.lottemembers.android`, `com.ahnlab.v3mobileplus` 등은 manifest query로 확인되지만 직접 호출 지점은 일부 난독화/조건부 흐름일 수 있다. | package name 전체 `PackageManager` 호출 trace 또는 동적 UI flow 확인. |
| cleartext 허용 도메인 | 정책에는 SRT/test/naverncp cleartext가 허용되어 있지만 코드가 대부분 HTTPS 치환을 한다. 실제 HTTP 요청 여부는 미확인. | 네트워크 캡처 또는 WebView request log 확인. |
