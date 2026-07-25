# KORAIL Mobile API Library Build Guide

이 문서는 `korail.apk` 정적 분석 결과와 제한적 실제 호출 결과를 라이브러리 구현 관점으로 묶은 메인 문서다. 임시 조사 리포트의 핵심 내용은 이 파일과 `api-status-by-service.md`로 흡수했다.

## Primary References

| 문서 | 역할 |
|---|---|
| [`korail-apk-analysis.md`](korail-apk-analysis.md) | APK 전체 구조, 네트워크/로그인/보안/결제/WebView 요약 |
| [`api-endpoints.md`](api-endpoints.md) | 165개 Retrofit endpoint의 HTTP method, path, parameter, return type 목록 |
| [`api-status-by-service.md`](api-status-by-service.md) | 서비스별 endpoint, 역할, 실제 테스트 성공/실패/미실행 상태 |
| [`deep-dive/api-contracts.md`](deep-dive/api-contracts.md) | endpoint별 request parameter와 response DTO field 계약 |
| [`deep-dive/network-model-fields.md`](deep-dive/network-model-fields.md) | 요청/응답/model field 전체 카탈로그 |
| [`deep-dive/webview-and-url-catalog.md`](deep-dive/webview-and-url-catalog.md) | Retrofit 밖 WebView URL, scheme, API-like path 목록 |
| [`deep-dive/local-storage-catalog.md`](deep-dive/local-storage-catalog.md) | SharedPreferences, DB, 로컬 crypto 저장 구조 |
| [`deep-dive/agent-reports/`](deep-dive/agent-reports/) | 업무 영역별 caller flow, FieldMap/QueryMap, callback/error 처리 |

## Current Inventory

| 항목 | 값 |
|---|---:|
| Retrofit method entries | 165 |
| Distinct HTTP+path pairs | 159 |
| Annotated service interfaces | 35 |
| HTTP method mix | POST 136 / GET 29 |
| Runtime test status | 성공 32 / 실패 13 / 미실행 120 |

## Runtime Contract

| 항목 | 구현 지침 |
|---|---|
| Base host | `https://smart.letskorail.com` |
| HTTP stack | APK의 KORAIL DAO 경로는 Retrofit 1 `RestAdapter` + `UrlConnectionClient` 기반 |
| Timeout | connect/read 모두 60초 |
| Encoding | `GET`은 query string, `POST + @FormUrlEncoded`는 `application/x-www-form-urlencoded; charset=UTF-8` |
| 공통 request fields | 대부분 `Device=AD`, `Version=<앱/API 버전>`, `Key=<앱 공통 field>`를 form/query field로 보냄 |
| 공통 response envelope | `h_msg_cd`, `h_msg_txt`, `strResult` |
| 성공/실패 문자열 | 앱 상수 기준 `SUCC`, `FAIL` |
| 세션 | 로그인 후 `JSESSIONID` cookie 기반. 앱은 Java CookieManager와 WebView CookieManager를 동기화 |
| 로그인 암호화 | common-code 응답의 `idx`, `key`, `pwdAESCphd` 설정에 따라 비밀번호를 AES/CBC 또는 Base64 계열로 전송 |
| `Sid` | 일부 조회/좌석/운임 요청에서 `AD + timestamp`를 AES/CBC로 만든 별도 field |
| DynaPath | macro flag가 켜진 경우 allowlist path에 `x-dynapath-m-token` header 추가 |
| NetFunnel | HTTP interceptor가 아니라 화면 flow의 선행 queue/callback. 조회/예약/결제/환불 쪽에 연결 |

## DynaPath Allowlist

| Path |
|---|
| `/classes/com.korail.mobile.certification.TicketReservation` |
| `/classes/com.korail.mobile.nonMember.NonMemTicket` |
| `/classes/com.korail.mobile.seatMovie.ScheduleView` |
| `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` |
| `/classes/com.korail.mobile.trn.prcFare.do` |
| `/classes/com.korail.mobile.login.Login` |

## Suggested Library Modules

| 모듈 | 포함 service | 책임 |
|---|---|---|
| `KorailHttpClient` | 공통 | base URL, cookie jar, timeout, form/query encoding, DynaPath header hook |
| `KorailSession` | `LoginService`, `NFilterService` | login state, cookies, member metadata, session expiry handling |
| `KorailCrypto` | 공통 | login password encryption, `Sid` generation, local helper wrappers |
| `CommonApi` | `CacheService`, `CommonService`, `CalendarService` | common-code, station data, config/cache, encrypt/decrypt helper |
| `SearchApi` | `SeatMovieService`, `ResearchService`, `TrainsInfoService` | train inquiry, schedule, fare, seat map, train/car info |
| `TicketApi` | `MyTicketService`, `ReceiptService` | read-only ticket, purchase-history, and receipt retrieval only |
| `AncillaryApi` | pass, mileage, XPoint, RailPlus, product, push | read-only secondary-product, balance, status, and catalog views only |

This guide was written for the read-only build and its mutation policy is
recorded here as the historical baseline: reservation, payment, refund,
cancellation, issuance, check-in, and other mutation endpoint facts in this
guide were historical, non-implementable evidence, and
no flag, no dry-run marker, and no confirmation token
authorized mutation on its own. Any mutation interface requires a separate
safety design, new evidence, independent review, and explicit user
authorization.

That authorization has since been given for four categories only. The shipped
client now has consent-gated `reserve`, `cancel_unpaid_hold`,
`pay_with_fake_card`, and `refund` methods, which send only through a dedicated
gated path and only with an explicit non-preview consent (see `README.md` and
`docs/MUTATION_HANDOFF.md`). Every other mutation endpoint listed in this guide
is still unimplemented and still governed by the baseline policy above.

## Service Runtime Status

| Service | 총 | 성공 | 실패 | 미실행 |
|---|---:|---:|---:|---:|
| `AddService` | 5 | 0 | 0 | 5 |
| `BusReservationService` | 4 | 0 | 0 | 4 |
| `CacheService` | 3 | 3 | 0 | 0 |
| `CalendarService` | 1 | 1 | 0 | 0 |
| `CartService` | 3 | 1 | 0 | 2 |
| `CashReceipt` | 1 | 0 | 0 | 1 |
| `CertificationService` | 12 | 0 | 1 | 11 |
| `CommonService` | 11 | 6 | 0 | 5 |
| `CompensateService` | 3 | 0 | 1 | 2 |
| `CustService` | 1 | 0 | 1 | 0 |
| `DelayService` | 9 | 1 | 1 | 7 |
| `GiftInfoService` | 1 | 0 | 0 | 1 |
| `GifticketService` | 4 | 0 | 2 | 2 |
| `IndependentService` | 1 | 0 | 0 | 1 |
| `LoginService` | 7 | 1 | 0 | 6 |
| `MileageService` | 3 | 0 | 0 | 3 |
| `MyTicketService` | 3 | 1 | 0 | 2 |
| `NFilterService` | 1 | 0 | 1 | 0 |
| `PassCardService` | 4 | 2 | 0 | 2 |
| `PassService` | 8 | 2 | 1 | 5 |
| `PayService` | 12 | 0 | 0 | 12 |
| `PaymentService` | 1 | 0 | 0 | 1 |
| `ProductService` | 4 | 2 | 0 | 2 |
| `PushService` | 4 | 0 | 0 | 4 |
| `RailPlusService` | 1 | 0 | 0 | 1 |
| `ReceiptService` | 1 | 1 | 0 | 0 |
| `RefundService` | 5 | 0 | 2 | 3 |
| `ResearchService` | 11 | 3 | 2 | 6 |
| `ReservationCancelService` | 3 | 0 | 0 | 3 |
| `ReservationService` | 4 | 1 | 1 | 2 |
| `ReservationWaitService` | 1 | 0 | 0 | 1 |
| `SeatMovieService` | 3 | 1 | 0 | 2 |
| `TicketService` | 19 | 3 | 0 | 16 |
| `TrainsInfoService` | 6 | 3 | 0 | 3 |
| `XPointService` | 5 | 0 | 0 | 5 |

The historical pre-revalidation 28/9/128 counts reflected one bounded
authenticated run that made 28 requests and received 28 responses: 25
successful operations, one expected typed application failure, and three
input-dependent skips. Deposit-bank and trip-menu reads succeeded after login.
R30 `getFresScar` returned exact
`strResult="SUCC"` and parsed successfully; R33 `getGuideSeatCnd` returned a
full `FAIL` application envelope for the server-supplied seat attribute,
surfaced as `KorailAppError`, and was not retried. R37
`getAssignScheduleView` and R51 `getMergeSeatsInquiry` remain static-only and
unexecuted. Offline raw replay yielded 27 parsed responses, one expected
`KorailAppError`, and zero unexpected failures.

A later bounded authenticated read-only revalidation used an empty advertising
ID, logged in once, and confirmed that the repr-hidden `customer_no` was
available. R13 made one request, returned `WRC800029`, surfaced as
`KorailAppError` and was not retried. R32 succeeded with 0 rows, current-form
R43 succeeded with 0 rows, R45 succeeded with 15 rows, and the existing safe
train search succeeded with 10 rows. R52 made zero requests and was recorded
as `skipped_no_typed_leg`; R17, R31, R39, and R54 were not called. No mutation
route was called, and no credential, identifier, or raw response value was
retained. The pre-R149 inventory was 31 successful, 10 failed, and 124
unexecuted entries out of 165.

A later bounded authenticated read-only revalidation used an empty
advertising ID, made one successful login call, confirmed logged-in state and
customer-number presence, and called only R149 once. R149 succeeded with one
row and was not retried; R137, R138, R146, and R148 made zero calls. No
mutation, raw response, PII, credential, or server message was retained.
Current inventory is 32 successful, 10 failed, and 123 unexecuted out of 165.

## Runtime Failure Notes

| Service | Method | Path | Result |
|---|---|---|---|
| `CompensateService` | `executeCompensateRefundList` | `/classes/com.korail.mobile.compensate.ticketList.do` | `WRG000000` 조회 결과 없음 |
| `CustService` | `mchdDcntTgt` | `/classes/com.korail.mobile.cust.mchdDcntTgt.do` | `WRC800029`; `KorailAppError`, 재시도 없음 |
| `DelayService` | `executeDelayRefundList` | `/classes/com.korail.mobile.delay.ticketList.do` | `WRG000000` 조회 결과 없음 |
| `GifticketService` | `getGifticketList` | `/classes/com.korail.mobile.gift.gdLst.do` | HTTP 404 |
| `GifticketService` | `historyGifticket` | `/classes/com.korail.mobile.gift.gdUseSpec.do` | HTTP 404 |
| `NFilterService` | `createKey` | `/classes/com.korail.mobile.nFilter.createKey.do` | HTTP 404 |
| `PassService` | `passMenu` | `/classes/com.korail.mobile.pass.passMenu.do` | `menuNo Error` |
| `ResearchService` | `getNCardHistory` | `/classes/com.korail.mobile.ticket.dcntCrdUseQry.do` | 입력값 오류 `dcntCrdNo` |
| `ResearchService` | `getNCardSchedultView` | `/classes/com.korail.mobile.research.dcntCrdScheduleView.do` | 입력값 오류 `dcntCrdKndCd` |
| `ReservationService` | `getGuideSeatCnd` | `/classes/com.korail.mobile.reservation.guideSeatCnd.do` | server-supplied seat attribute produced a full `FAIL` application envelope surfaced as `KorailAppError`; no retry |

## Safety Defaults

| 분류 | 기본 동작 |
|---|---|
| 조회성 API | 실제 호출 허용 가능. 단, 계정/티켓 개인정보 로그 마스킹 |
| 예약/취소/결제/환불 mutation endpoint | consent gate를 통해서만 구현·호출. 기본값은 전송 없는 preview이며, 결제는 비청구 test card만 허용 |
| 그 밖의 모든 mutation endpoint | 현재 라이브러리에서 구현하거나 호출하지 않으며, 위의 비허용 정책을 예외 없이 적용 |
| PNR/발권번호/N카드 기반 API | 실제 값 없으면 schema-only 테스트만 수행 |

## Hidden/Non-Retrofit Surface

| 종류 | 발견 내용 | 라이브러리 영향 |
|---|---|---|
| DynaPath SDK | `kr.scripters.dynapath.sdk.android` 패키지와 `x-dynapath-m-token` hook | 로그인/조회/예약 일부 요청의 header provider로 분리 |
| NetFunnel | `nf.letskorail.com`, `service_1`, action id 계열 | UI flow 수준 gate로 추상화 |
| H2O SmartAlimi | `com.h2osystech.smartalimi` FCM/push SDK | push API와 실제 FCM 수신은 별도 |
| Kakao SDK | OAuth/deeplink | API core에는 비필수, 외부 인증 flow에서만 필요 |
| Naver OAuth | `naver3rdpartylogin://authorize` | NaverPay/Naver login handoff 구분 필요 |
| Google/Firebase/Ads | FCM, Ads, Play Services 패키지 | core API client에는 불필요 |
| Card scan | `com.code1system.code1cardscanlib` | 카드 입력 UI 보조. 결제 API와 분리 |
| Maum AI / WebView bridge | `korailtalk://approve`, `korailtalk://navigation`, 외부 결제/인증 URL | payment/provider flow는 HTTP API + WebView callback 조합 |

## Non-Retrofit Endpoint Candidates

Retrofit annotation 기준 165개 endpoint는 `analysis/reports/api-endpoints.tsv`, `docs/api-endpoints.md`, JADX source가 서로 일치한다. 별도 문자열 감사에서 TSV 밖 `/classes/com.korail.mobile.*` 후보는 다음 5개다. 이들은 WebView, 외부 인증, 결제 callback 성격으로 보이며 core Retrofit client와 분리해서 다룬다.

| Candidate path | 추정 영역 |
|---|---|
| `/classes/com.korail.mobile.certification.MCertify.do` | 모바일 인증/WebView |
| `/classes/com.korail.mobile.mypage.mCertify.do` | 마이페이지 인증/WebView |
| `/classes/com.korail.mobile.onepass.login.do` | Onepass WebView login |
| `/classes/com.korail.mobile.pay.stbkAcntStlR.do` | STBK 계좌 결제 결과/WebView |
| `/classes/com.korail.mobile.pay.bcUsrAthnR.do` | BC 사용자 인증 결과/WebView |

## Implementation Order

1. `KorailHttpClient`, response envelope parser, typed error model을 먼저 만든다.
2. `CommonApi.getCommonCode`, station/cache/config 조회를 구현해 기본 통신을 검증한다.
3. 로그인은 common-code 기반 암호화와 cookie persistence까지 하나의 integration test로 묶는다.
4. 열차 조회, 구매이력, 영수증처럼 현재 성공한 조회성 API부터 typed wrapper를 만든다.
5. Do not expose mutation methods or DTO stubs beyond the four authorized consent-gated ones (reserve, unpaid-hold cancel, fake-card payment, refund). Any further interface requires a separate safety design, new evidence, independent review, and explicit user authorization.
6. WebView/provider/NetFunnel/DynaPath는 core API와 분리해 optional adapter로 둔다.
