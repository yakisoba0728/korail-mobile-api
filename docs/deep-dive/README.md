# KORAIL APK Deep-Dive Manual

이 디렉터리는 `korail.apk`를 정적 분석해 API, 요청/응답 모델, WebView bridge, 로컬 저장소, 보안/대기열 로직을 최대한 분해한 상세 문서 묶음이다. 운영 서버 호출, 로그인 시도, 인증 우회, NetFunnel/DynaPath 우회는 수행하지 않았다.

## 분석 방식

1. APK hash와 manifest/build metadata를 확인했다.
2. `unzip`, `apktool`, `jadx`로 raw resource, smali, Java-like source를 생성했다.
3. Retrofit annotation을 전체 스캔했다. 파일명이 `*Service.java`가 아닌 `CashReceipt.java`도 포함하기 위해 `@GET`/`@POST` annotation 자체를 기준으로 재추출했다.
4. `@Field("literal")`/`@Query("literal")`뿐 아니라 `@Field(CONSTANT)`/`@Query(CONSTANT)` 형태도 compile-time string constant를 resolve했다.
5. request/response class field는 decompiled Java field와 Gson annotation 기준으로 카탈로그화했다.
6. WebView JavaScript interface, URL/scheme 문자열, SharedPreferences literal key, ORMLite DB model을 별도 기계 추출했다.
7. 20개 병렬 에이전트 보고서를 업무 영역별 상세 분석으로 관리한다. 라이브러리 구현용 요약은 `../library-build-guide.md`에 별도 정리한다.

## 핵심 수치

- Retrofit method entries: `165`
- Distinct HTTP+path pairs: `159`
- Annotated interfaces: `35`
- HTTP method mix: `POST 136`, `GET 29`
- Network request/response model fields: `2,566`
- WebView `@JavascriptInterface` methods: `26`
- URL/scheme/API-like string rows: `179`
- ORMLite DB field rows: `63`
- SharedPreferences literal key rows: `645`
- Parallel agent reports: `20`

## 읽는 순서

1. [../korail-apk-analysis.md](../korail-apk-analysis.md): APK 전체 구조와 핵심 flow 요약.
2. [../api-endpoints.md](../api-endpoints.md): 모든 Retrofit method entry의 HTTP method/path/request parameter/return type.
3. [api-contracts.md](api-contracts.md): endpoint별 request parameter와 response model field를 함께 보는 계약서.
4. [network-model-fields.md](network-model-fields.md): 네트워크 request/response/model field 전체 카탈로그.
5. [webview-and-url-catalog.md](webview-and-url-catalog.md): WebView bridge method, hardcoded URL/scheme/path inventory.
6. [local-storage-catalog.md](local-storage-catalog.md): ORMLite DB model과 SharedPreferences literal key inventory.
7. [agent-reports/](agent-reports/): 업무 영역별 세부 로직, caller flow, FieldMap/QueryMap, callback/error 처리.

## 에이전트 보고서

| No | Report | Scope |
|---:|---|---|
| 01 | [bootstrap-config](agent-reports/01-bootstrap-config.md) | APK metadata, manifest, bootstrap, host/config, permissions, SDK init |
| 02 | [network-core](agent-reports/02-network-core.md) | BaseRequest/BaseResponse/BaseDao/ExecuteDao/BaseDaoHelper, cookies, errors |
| 03 | [login-account-nfilter](agent-reports/03-login-account-nfilter.md) | Login/account/non-member access, auto-login, NFilter, password handling |
| 04 | [common-station-crypto](agent-reports/04-common-station-crypto.md) | CommonService, station data, encrypt/decrypt helpers, crypto utilities |
| 05 | [train-search-schedule](agent-reports/05-train-search-schedule.md) | Train inquiry, schedule, fare, Sid, seat/search maps |
| 06 | [reservation-certification](agent-reports/06-reservation-certification.md) | Reservation, certification, discount, FieldMap reconstruction |
| 07 | [payment-core-receipt](agent-reports/07-payment-core-receipt.md) | ReservationPayment, PaymentMethod, receipt/cash receipt |
| 08 | [pay-providers](agent-reports/08-pay-providers.md) | Payco/NaverPay/Toss/Samsung/Monimo/STBK provider flows |
| 09 | [ticket-my-ticket](agent-reports/09-ticket-my-ticket.md) | TicketService, MyTicketService, check-in, SMS, platform, MAAS ticket |
| 10 | [refund-delay-compensate-cancel](agent-reports/10-refund-delay-compensate-cancel.md) | Refund, delay, compensate, reservation cancel/change |
| 11 | [pass-mileage-xpoint-railplus](agent-reports/11-pass-mileage-xpoint-railplus.md) | Pass, pass card, mileage, XPoint, RailPlus |
| 12 | [products-cart-addons-gifts-bus](agent-reports/12-products-cart-addons-gifts-bus.md) | Product, cart, add-on services, gifts, bus reservation |
| 13 | [webview-bridges-schemes](agent-reports/13-webview-bridges-schemes.md) | WebView settings, JS bridge, schemes, SRT/government/payment handoff |
| 14 | [push-notification-background](agent-reports/14-push-notification-background.md) | PushService, FCM/SmartAlimi, receivers/services, notification routing |
| 15 | [local-storage-db-prefs-crypto](agent-reports/15-local-storage-db-prefs-crypto.md) | DB helpers/models, prefs, local AES, cache/migration/privacy notes |
| 16 | [antiautomation-queue-security](agent-reports/16-antiautomation-queue-security.md) | NetFunnel, DynaPath, Sid, security-sensitive endpoints, network security |
| 17 | [response-models-exhaustive](agent-reports/17-response-models-exhaustive.md) | Response envelope/model classes and endpoint/caller mapping |
| 18 | [nonretrofit-urls-resources-smali](agent-reports/18-nonretrofit-urls-resources-smali.md) | Non-Retrofit URLs, resources/assets, smali fallback, external intents |
| 19 | [ui-flow-to-api-map](agent-reports/19-ui-flow-to-api-map.md) | UI event -> DAO/service -> response callback -> navigation maps |
| 20 | [doc-quality-gap-audit](agent-reports/20-doc-quality-gap-audit.md) | Documentation gaps, count terminology, generator issues, next improvements |

## 라이브러리 구현용 문서

| Report | Scope |
|---|---|
| [library-build-guide](../library-build-guide.md) | 라이브러리 모듈 분리, 공통 런타임 계약, 안전 가드, 숨은 surface 요약 |
| [api-status-by-service](../api-status-by-service.md) | 실제 안전 테스트 기준 endpoint별 성공/실패/미실행 상태 |

## Cross-Cutting Facts

- Base runtime host는 `https://smart.letskorail.com`이고, release config는 `CONNECT_SERVER="3"` -> `REAL`이다.
- 공통 request 값은 대체로 `Device=AD`, `Version=250601003`, `Key=korail1234567890`이다. 일부 endpoint는 `Key`가 없거나 WebView/외부 host 흐름이다.
- 공통 response envelope는 `h_msg_cd`, `h_msg_txt`, `strResult`다. 실제 서버 value와 nullable/optional 여부는 정적 분석만으로 확정하지 않았다.
- 로그인 성공 후 Java `CookieManager`의 `JSESSIONID`를 WebView `CookieManager`로 동기화한다.
- `Sid`는 일부 조회/좌석/운임 흐름에서 앱 로컬 AES/CBC helper로 생성된다.
- DynaPath macro 방어 header `x-dynapath-m-token`은 설정 flag가 켜진 경우 일부 민감 endpoint에만 추가된다.
- NetFunnel은 조회/예약/결제/환불 등 주요 flow의 gate/callback으로 연결된다.
- WebView bridge는 `window.korailtalk`로 노출되며, exported WebView activity와 URL extra trust boundary가 중요하다.
- 로컬 DB/Prefs에는 즐겨찾기 역, 최근 역, favorite card, ticket cache, login/user 식별자 성격 값이 저장된다. 일부 값은 앱 로컬 AES helper로 처리된다.

## 한계

- 실제 운영 응답 body sample, 세션 만료 lifecycle, redirect, feature flag 값은 캡처하지 않았다.
- 서버가 field를 필수/선택으로 검증하는 규칙은 정적 코드만으로 확정할 수 없다.
- 일부 `FieldMap`/`QueryMap`은 map 생성 class에서 key를 재구성했지만, runtime branch별 누락/추가 field는 앱 실행 없이는 완전 확정이 어렵다.
- JADX decompile warning이 있었으므로, 의심 항목은 `analysis/apktool/smali*`로 fallback 검증해야 한다.
