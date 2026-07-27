# K8 — 부가서비스·공통·방어계층 (addService / common / cache / push / seatMovie / HTTP layer) 감사

감사자: K8 (phase1) · 대상 저장소: `korail-mobile-api` (이 저장소)
라이브러리: `src/korail_mobile_api/` · 앱 근거: `analysis/jadx/sources/com/korail/talk/network/`

## 0. 범위와 카운팅 규칙

담당 5개 Retrofit 인터페이스 (`network/dao/<domain>/<Domain>Service.java`)를 전수 열거해 분모로 삼는다:

| 인터페이스 | 파일 | 메서드 수 |
|---|---|---:|
| `AddService` | `network/dao/addService/AddService.java` | 5 |
| `CommonService` | `network/dao/common/CommonService.java` | 11 |
| `CacheService` | `network/dao/cache/CacheService.java` | 3 |
| `PushService` | `network/dao/push/PushService.java` | 4 |
| `SeatMovieService` | `network/dao/seatMovie/SeatMovieService.java` | 3 |
| **합계** | | **26** |

(`getEncrypt`/`getKBPayEncrypt`는 같은 URL `common.encrypt.do`를 공유하므로 고유 경로는 25개.)

**세는 법**: "구현됨"은 `client.py`의 public 메서드에서 해당 경로로 실제 HTTP 호출까지 도달 가능한 경우만 카운트한다. private 헬퍼(`_build_*`, `_Product...`)가 존재해도 `client.py`에서 호출되지 않으면 "미도달"로 센다.

- 구현·도달 가능: **13/26**
- 결여: AddService 5개 전부, Common 크립토/QR 클러스터 5개(`getEncrypt`/`getDecrypt`/`getKBPayEncrypt`/`seedEncrypt`/`authQRLocation`), Push `callCrew`·`pushUpdate` 2개, SeatMovie `getRsvProductInquiry`(ScheduleViewSpecial) 1개 = 13개
- 13 + 13 = 26 ✓

**감사 범위의 정직한 한계** (지시사항 규칙 2·조언자 지적 반영): `network/data/reservation/`(구 O* 5개 파일: OJrny·OPsg·OSeat·OSrcar·OWait, 신 R* 6개 파일: RJrny·RPsg·RSeat·RSrcar·RDscp·ROrtg), `network/response/research/*`(Cmpn·Jrny·OrgTk·Seat·Stl), `network/response/delay/RefundResponse.java`, `network/request/payment/*`, `network/request/research/SeatSearchRequest.java`, `network/request/myTicket/PushUpdateRequest.java`, `network/data/certification/DiscountPriceParams.java`는 파일 경로상 내 담당 폴더(`network/data/`, `network/request/`, `network/response/`)에 있지만, **이들을 실제로 호출하는 DAO/Service는 내 5개 서비스 밖**(`ResearchService`, `DelayService`, `dao/reservation/`, `dao/reservationCancel/`, `dao/refund/` 등)에 있다. 이 파일들은 표로 존재를 기록하되, 필드 단위 전수대조는 하지 않았다(다른 에이전트 영역과 중복·월권 방지). `OJrny`/`RJrny`만 대표로 열어 구조(문자열 전용 LinkedHashMap, `txt`/밑줄 접미사 컨벤션 차이)를 확인했고 `OPsg`/`OSeat`/`OSrcar`/`OWait`/`RPsg`/`RSeat`/`RSrcar`/`RDscp`는 열지 않았다. 예약 폼(`build_reservation_form` 등)에서 이 명명 규칙이 실제로 재현되고 있음은 `mutation_payloads.py`의 `trnNo_{i}`/`dptRsStnCd_{i}` 사용으로 간접 확인했다.

---

## 1. 기능 전체 목록

### 1.1 AddService (부가서비스) — 5/5 결여

| 기능 | 엔드포인트 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|
| 부가서비스 예약/취소 신청 | `POST /classes/com.korail.mobile.addService.reserve.do` | `AddService.java:16-18` | 없음 | **없음** |
| 특송(딜카) 구매확정 | `POST /classes/com.korail.mobile.addService.buyConfirm.do` | `AddService.java:20-22` | 없음 | **없음** |
| 부가서비스 예약목록 조회 | `POST /classes/com.korail.mobile.addService.reserveList.do` | `AddService.java:24-26` | 없음 | **없음** |
| 도움서비스 고객정보 신청/조회 | `POST /classes/com.korail.mobile.addSrv.helpSrvCust.do` | `AddService.java:28-30` | 없음 | **없음** |
| 도움서비스 승차권 조회 | `POST /classes/com.korail.mobile.addSrv.helpSrvTk.do` | `AddService.java:32-34` | 없음 | **없음** |

### 1.2 CommonService (공통) — 6/11 구현

| 기능 | 엔드포인트 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|
| QR 승차위치 인증 | `POST /classes/com.korail.mobile.qr.bchTripSv.do` | `CommonService.java:23-25` | 없음 | **없음** |
| UUID/쿠키 조회 | `GET /ebizcross/getUUID.do` | `CommonService.java:27-28` | `client.py:1225` (`ckValue`류) | 있음 |
| 공통코드 조회(버전체크/매크로 플래그 포함) | `POST /classes/com.korail.mobile.common.code.do` | `CommonService.java:30-32` | `client.py:1184 get_common_code`, `payloads.py:354 build_common_code_form` | 있음 |
| 서버측 복호화 | `POST /classes/com.korail.mobile.common.decrypt.do` | `CommonService.java:34-36` | 없음 | **없음** |
| 서버측 암호화(공통) | `POST /classes/com.korail.mobile.common.encrypt.do` | `CommonService.java:38-40` | 없음 | **없음** |
| 서버측 암호화(KB Pay) | `POST /classes/com.korail.mobile.common.encrypt.do`(같은 URL, 다른 응답형) | `CommonService.java:42-44` | 없음 | **없음** |
| MAAS 메뉴 목록 | `POST /classes/com.korail.mobile.copt.gdMenuLt.do` | `CommonService.java:46-48` | `client.py:1237` | 있음 |
| MAAS 역 목록 | `POST /ebizmaas/EbizMaasStationList.do` | `CommonService.java:50-52` | `client.py:1245 get_maas_station_data` | 있음 |
| 전체 역 데이터 | `GET /classes/com.korail.mobile.common.stationdata` | `CommonService.java:54-55` | `client.py:1273 get_station_data`, `parsers.py:378` | 있음 (필드 전수 일치) |
| 역 정보(개수/지도버전) | `GET /classes/com.korail.mobile.common.stationinfo` | `CommonService.java:57-58` | `client.py:1262 get_station_info`, `parsers.py:431` | 있음 (필드 일치) |
| SEED(신한) 암호화 | `POST /classes/com.korail.mobile.shinhan.Encrypt.do` | `CommonService.java:60-62` | 없음 | **없음** |

### 1.3 CacheService (캐시/버전체크) — 3/3 구현

| 기능 | 엔드포인트 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|
| 서비스 상태 캐시 확인 | `GET /file/CACHE/MobileService.cache` | `CacheService.java:11-12` | `session.py:117 check_service` | 있음 |
| 앱 데이터/버전체크 캐시 | `GET /file/CACHE/prdMobilePlusMain.cache` | `CacheService.java:14-15` | `client.py:1193 get_app_data`, `parsers.py:141` | 있음 (`AMESSAGE`/`NEWDVERSION` 포함 전 필드 일치) |
| 공지 캐시 | `GET /file/CACHE/prdMobilePlusNotice.cache` | `CacheService.java:17-18` | `client.py:1207 get_notice`, `parsers.py:170` | 있음 (필드 일치) |

### 1.4 PushService (푸시/승무원호출) — 2/4 구현

| 기능 | 엔드포인트 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|
| 승무원 호출(실제 발신) | `GET /classes/com.korail.mobile.push.callCrew.do` | `PushService.java:13-14` | 없음 | **없음** |
| 승무원 호출 사유 목록 조회 | `GET /classes/com.korail.mobile.push.crwCallRq.do` | `PushService.java:16-17` | `client.py:741`, `read_parsers.py:612 parse_crew_request_list_response` | 있음 (필드 일치) |
| 통근/정기권 종류 메뉴 조회 | `GET /classes/com.korail.mobile.push.cmtrKnd.do` | `PushService.java:19-20` | `client.py:757`, `read_parsers.py:591` | 있음 (필드 일치; 정기권 "구매"가 아닌 메뉴 조회라 제외범위 아님) |
| 푸시 알림 설정 갱신 | `GET /classes/com.korail.mobile.push.update` | `PushService.java:22-23` | 없음 | **없음** |

### 1.5 SeatMovieService (열차/리무진 조회) — 2/3 구현

| 기능 | 엔드포인트 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|---|
| 열차 조회(직통/환승) | `POST /classes/com.korail.mobile.seatMovie.ScheduleView` | `SeatMovieService.java:12-14` | `client.py:1292 search_trains` 등, `payloads.py:239-338` | 있음 (필드·기본값·순서까지 상세 일치, smali 인용 다수) |
| 리무진 열차 조회 | `POST /classes/com.korail.mobile.seatMovie.LimousineScheduleView` | `SeatMovieService.java:16-18` | `client.py:416`, `limousine_payloads.py` | 있음 |
| 특가상품 열차 조회 | `POST /classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | `SeatMovieService.java:20-22` | `read_payloads.py:1465 _build_product_train_inquiry_form` 등(비공개, 미배선) | **부분 (의도적 보류, 테스트로 고정됨)** — §3.4 |

### 1.6 HTTP 계층 / 방어계층 공통 요소

| 요소 | 앱근거 | 라이브러리 대응 | 상태 |
|---|---|---|---|
| 공통 요청 필드 기본값 (`Device="AD"`, `Version="250601003"`, `Key="korail1234567890"`) | `BaseRequest.java:7-18` | `constants.py:4-6` | 있음, 정확 일치 |
| 공통 응답 포장(`strResult`/`h_msg_cd`/`h_msg_txt`) | `BaseResponse.java:8-18` | `models.py BaseKorailResponse`, `http.py:33-58 parse_base_response` | 있음, `P058`/`WRC000288`/`FAIL` 게이트까지 일치 |
| DynaPath 토큰 발급 조건(매크로 URL 6종 + `IS_MACRO_ACTIVE`) | `ExecuteDao.java:18-57`, `I4/a.java:14`, `IntroActivity.java:663` | `dynapath.py`, `constants.py:421-430 DYNAPATH_ALLOWLIST_PATHS`(6개 문자열 정확 일치), `http.py:123-151 _dynapath_headers`(정확 일치 predicate) | 있음 |
| DynaPath 거부 판별(`DynaPath-Result` 헤더) | `BaseDaoHelper.java:54-92` | `http.py:61-82 _raise_for_status`, `errors.py:47-93 KorailDynaPathError` | **있음, 단 경로제한 이슈** — §3.5 |
| NetFunnel opcode/파라미터(5002/5003/5004/5101/5105/5106) | `T6/c.java:6-11`, `T6/d.java` | `netfunnel.py`(오퍼레이션 매핑·opcode enum) | 있음 (본 세션에서 로직 자체는 재검증 생략 — 기존 감사에서 라이브 확증됨) |
| 역 데이터(전국역) 파싱 | `StationDataDao.java:11-136` | `parsers.py:378-428` | 있음, `STN` 10개 필드 전부 일치 (`popupType` int 포함) |

---

## 2. 통계

- **앱에서 추출한 기능/엔드포인트**: 26 (5개 서비스 인터페이스의 Retrofit 메서드 전수)
- **라이브러리에 올바르게 구현된 개수**: 13
- 결여 13개 중 1개(`ScheduleViewSpecial`)는 데이터/파서 계층까지 완성되어 있으나 공개 API 배선만 의도적으로 보류된 상태이며, 테스트(`tests/test_next_variant_reads.py:105-110`)가 그 보류 경계를 명시적으로 고정하고 있어 "버그"가 아니라 "테스트로 봉인된 보류"로 분류했다.
- 나머지 12개는 순수 결여(코드 자체가 없음): AddService 5개, Common 크립토 4개(`getEncrypt`/`getDecrypt`/`getKBPayEncrypt`/`seedEncrypt`), QR 1개(`authQRLocation`), Push 2개(`callCrew`/`pushUpdate`).

---

## 3. 문제 항목 상세

### 3.1 [K8-01] AddService 인터페이스 5개 엔드포인트 전부 미구현

- **분류**: missing / **심각도**: medium
- **앱 근거**: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java:16-34` (5개 `@POST` 선언), 각각 `AdditionalServiceDao.java`(부가서비스 예약, `jobDvCd`/`addSrvId`/`reqQnty`(int)/`helpSrvTgtCnt`(int)/`rcpSqno`(List)/`cncTgtCnt`(int)/`addSrvReqNo`(List) 등 14필드), `DealCarBuyDao.java:12-13`(`addSrvCnt`int/`addSrvReqNo`List), `ExtraProductListDao.java`, `HelpSrvCustDao.java`, `HelpSrvTkDao.java`. 응답 DTO `ExtraProductInfo.java`(`network/data/addService/ExtraProductInfo.java:11-161`, `addSrvList[]` 18필드)도 이 클러스터에 종속.
- **라이브러리 근거**: 없음 — `grep -rn "addService\.\|addSrv\.\|dealCarBuy\|HelpSrv" src/korail_mobile_api/*.py` 매치 0건. `docs/api-status-by-service.md:135-139`, `docs/api-endpoints.md:51-55`에는 5개 다 카탈로그화되어 있으나 라이브러리 코드에는 옮겨지지 않았다.
- **상세**: 부가서비스(휠체어/도움서비스 신청, 특송 구매확정, 부가서비스 예약목록 조회) 관련 5개 엔드포인트가 문서화(추출)만 되어 있고 payload 빌더·파서·`client.py` 메서드가 전혀 없다. `docs/deep-dive/cross-validation-2026-07-21.md:311`도 이 클러스터를 "srtgo에 없는 별도 엔드포인트"로 기록만 하고 구현하지 않았다고 명시. 정기권/단체예약처럼 사용자가 명시적으로 뺀 범위가 아니므로 "의도된 제외"로 분류하지 않았다.
- **제안**: 우선순위는 낮다(핵심 예매/결제/취소 흐름이 아님). 구현 시 `helpSrvCust`/`helpSrvTk`는 읽기 전용으로, `additionalService`/`dealCarBuy`는 mutation 게이트(consent) 대상으로 분류해야 한다.

### 3.2 [K8-02] Common 서버측 카드/값 암호화 클러스터(getEncrypt/getDecrypt/getKBPayEncrypt/seedEncrypt) 미구현 — 단, 실제로 불필요할 가능성이 높음

- **분류**: missing / **심각도**: info
- **앱 근거**: `CommonService.java:34-44`(`getEncrypt`/`getDecrypt`/`getKBPayEncrypt`), `CommonService.java:60-62`(`seedEncrypt`); 호출부 `B6/AbstractC1269e.java:656-661,766-770`(결제 화면에서 KB Pay/신한 SEED 암호화 호출).
- **라이브러리 근거**: 없음 — `grep -rn "getEncrypt|getDecrypt|getKBPayEncrypt|seedEncrypt" src/korail_mobile_api/*.py` 매치 0건.
- **상세**: `docs/RELEASE_GAP_PLAN.md:379-387`에 이미 정리되어 있듯, smali 재검증 결과 결제 시 카드 PAN은 이 서버측 암호화 엔드포인트를 거치지 않고 `hidStlCrCrdNo1`에 **평문으로** 실린다(`v4/a.java:29`, `srtgo_plus/srtgo/ktx.py:1044`와 동일 패턴). 즉 현재 라이브러리가 구현한 결제 경로(`mutation_payloads.py`)는 이 크립토 왕복 없이도 앱과 동일하게 동작한다. 4개 엔드포인트는 "존재하되 이 라이브러리가 구현한 결제 플로우에는 불필요"로 보이며, 미구현이 결제 정확성에 영향을 주지 않는다.
- **제안**: 정보성 기록으로 충분. 향후 KB Pay/신한 간편결제 자체를 새 결제수단으로 추가하려면 그때 재검토.

### 3.3 [K8-03] QR 승차위치 인증(`authQRLocation`) 미구현

- **분류**: missing / **심각도**: low
- **앱 근거**: `CommonService.java:23-25` — `POST /classes/com.korail.mobile.qr.bchTripSv.do`, 필드 `Device`/`Version`/`qrcode`/`latitude`/`longitude`; `authQRLocationDao.java:11-53`, 응답 `jobScsFlg`.
- **라이브러리 근거**: 없음.
- **상세**: 열차 내 QR 코드 스캔 위치 인증(탑승 확인용으로 추정)이며 다른 어떤 흐름도 이 값에 의존하지 않는다. 핵심 예매/취소/조회 기능과 무관한 부가 기능.
- **제안**: 낮은 우선순위. 구현 시 위치정보 필드이므로 redaction 대상 검토 필요.

### 3.4 [K8-04] Push 클러스터: 승무원 실호출(`callCrew`)과 푸시 알림 설정(`pushUpdate`) 미구현

- **분류**: missing / **심각도**: medium
- **앱 근거**: `PushService.java:13-14`(`callCrew`, 22개 필드 — `intgMsgCd1~10`/`intgMsgCont`/`sndSqno`/`coutMsgDvCd` 등, `CallCrewDao.java:12-186`), `PushService.java:22-23`(`pushUpdate`, `PushUpdateDao.java:12-142`, `job_dv_cd`/`tnsm_flg1~4`/`dptUsrInpTnum`/`arvUsrInpTnum`).
- **라이브러리 근거**: 없음 — `grep -n "push.callCrew.do|push\\.update" src/korail_mobile_api/*.py` 매치 0건. 대조적으로 같은 인터페이스의 읽기 전용 메서드 2개(`callCrewRequestList`→`client.py:741`, `cmtrKndPassMenu`→`client.py:757`)는 필드까지 정확히 구현되어 있다.
- **상세**: "호출 사유 목록 조회"(읽기)는 구현했지만 그 사유를 골라 실제로 승무원을 호출하는 액션(`callCrew`, `intgMsgCd1..10`으로 사유코드 최대 10개 + 자유 메시지 `intgMsgCont` 전송)이 빠져 있어, 이 기능은 "조회는 되지만 실행은 안 되는" 반쪽 상태다. `pushUpdate`(지연 알림 등 푸시 수신 플래그 갱신)도 대응 없음.
- **제안**: `callCrew`는 세션/PNR 종속 mutation류 액션이라 consent 게이트 대상. `pushUpdate`는 설정 변경이라 별도 안전 검토 필요.

### 3.5 [K8-05] `ScheduleViewSpecial`(특가상품 열차조회) — 파서/페이로드는 완성, 공개 API 배선은 테스트로 고정된 의도적 보류

- **분류**: partial / **심각도**: info
- **앱 근거**: `SeatMovieService.java:20-22`(`getRsvProductInquiry`), `constants.py:425-426`·`ExecuteDao.java:27`을 통해 이 URL이 DynaPath 매크로 방지 6개 경로 중 하나임이 확인됨(즉 앱 입장에서는 민감한 엔드포인트).
- **라이브러리 근거**: `read_payloads.py:1308-1519`(`_ProductTrainInquiryContinuation`, `_ProductTrainInquiryRequest`, `_build_product_train_inquiry_form` — validation·continuation까지 완비), `read_parsers.py:2436-2491`(`parse_product_train_inquiry_response`), `read_models.py:1097`(`ProductTrainInquiryResponse`) 모두 존재하지만 전부 앞에 `_`가 붙어 비공개이거나(`_Product...`) `client.py`/`__init__.py`에서 전혀 참조되지 않는다(`grep -n "ScheduleViewSpecial|_build_product_train_inquiry_form|ProductTrainInquiry" src/korail_mobile_api/client.py` 매치 0건). `safety.py`의 `KORAIL_READ_ONLY_ROUTES`에도 `("POST", ".../ScheduleViewSpecial")`는 등록되어 있지 않다(`grep -n "ScheduleViewSpecial" src/korail_mobile_api/safety.py` 매치 0건) — 즉 저수준 API로 직접 호출을 시도해도 `assert_read_only_route`(`safety.py:1319-1330`)가 `KorailProtocolError`로 막는다.
- **왜 "버그"가 아닌가**: `tests/test_next_variant_reads.py:105-110`의 `test_route_and_holdback_boundary_is_exact`가 `assert ("POST", R39_PATH) not in KORAIL_READ_ONLY_ROUTES`, `assert not hasattr(KorailClient, "get_product_train_inquiry")`, `assert not hasattr(korail_mobile_api, "ProductTrainInquiryRequest")`를 명시적으로 단언한다. 즉 이 미배선은 실수가 아니라 테스트로 봉인된 설계 결정("holdback")이다. 업스트림 의존성(`PassMenuItem`/`PassGoodsInfo`)은 `client.py:716 get_pass_menu`를 통해 공개적으로 획득 가능하므로, 이 클러스터가 다른 미구현 기능에 막혀서 못 낸 것도 아니다 — 순수하게 검증 신뢰도 미달 등의 이유로 보류된 것으로 보인다(근거 문서에서 사유 자체는 확인하지 못함 — "확인불가").
- **제안**: 결함으로 취급하지 말 것. 다만 사용자가 "특가상품 열차조회"가 필요해지는 시점에는 이미 구현이 90% 되어 있으므로 `client.py`에 배선 메서드 하나 추가 + `safety.py` 라우트 등록 + 테스트 갱신만 하면 될 것으로 보인다.

### 3.6 [K8-06] `DynaPath-Result` 403 판별에 라이브러리가 앱에 없는 경로 제한을 추가함 (미검증 리스크)

- **분류**: risk / **심각도**: low
- **앱 근거**: `BaseDaoHelper.java:54-92` — `HttpTask.doInBackground`의 catch 블록은 `RetrofitError` 메시지에 `"403"`과(대소문자 무관) `"forbidden"`이 모두 포함되어 있고, 응답 헤더 중 이름이 정확히 `"DynaPath-Result"`인 것이 있으며 그 값이 정수로 파싱해 0 미만이면 매크로 거부로 처리한다. **이 조건에는 요청 경로(URL)에 대한 제약이 전혀 없다** — 6개 매크로 경로가 아닌 다른 경로에서 403 + 해당 헤더가 오더라도 동일하게 처리된다.
- **라이브러리 근거**: `http.py:61-82 _raise_for_status` — `response.status_code == 403 and path in DYNAPATH_ALLOWLIST_PATHS and dynapath_rejected` 세 조건을 **모두** 요구한다(`http.py:69-73`). `path in DYNAPATH_ALLOWLIST_PATHS`는 앱에 없는 추가 제약이다.
- **상세**: 실제로 서버가 6개 매크로경로 밖에서 음수 `DynaPath-Result`를 내려주는지는 APK만으로는 확인할 수 없다(서버측 동작이라 정적 분석 범위 밖) — 이 점은 "확인불가"로 남긴다. 다만 만약 그런 상황이 실제로 벌어지면, 라이브러리는 `KorailDynaPathError`(매크로 거부, 재시도 무의미) 대신 `KorailTransportError`(일반 전송 오류, 재시도 가능해 보임)로 오분류하게 되어 호출자가 무의미한 재시도를 반복할 수 있다.
- **제안**: `path in DYNAPATH_ALLOWLIST_PATHS` 조건을 제거하거나, 최소한 이 제약이 앱 동작이 아니라 라이브러리의 보수적 선택이라는 점을 `KorailDynaPathError`/`_raise_for_status` 근처 주석에 명시할 것.

### 3.7 [K8-07] (정보) 내 폴더 안에 있으나 타 도메인 DAO가 소비하는 데이터 구조

- **분류**: doc-drift(경계 기록용) / **심각도**: info
- **앱 근거**: `network/response/research/{Cmpn,Jrny,OrgTk,Seat,Stl}.java`는 `network/dao/research/OgTkInquiryDao.java`(`ResearchService`)가 소비; `network/response/delay/RefundResponse.java`는 `network/dao/delay/DelayRefundListDao.java`·`network/dao/compensate/CompensateRefundListDao.java`(`DelayService`)가 소비; `network/data/reservation/`(구·신 O*/R* 12개 파일)는 `network/dao/reservation/`·`network/dao/reservationCancel/`·`network/dao/research/NCardReservationDao.java`가 소비. 이들 DAO/Service는 내 담당 5개 인터페이스(AddService/CommonService/CacheService/PushService/SeatMovieService)에 속하지 않는다.
- **라이브러리 근거**: 일부는 이미 구현되어 있는 것으로 보인다(`mutation_payloads.py`가 `trnNo_{i}`/`dptRsStnCd_{i}` R-접미사 컨벤션을 사용 — `mutation_payloads.py:1550-1555`). `getTicketOriginalInquiry`(OgTkInquiryDao) 경로 자체는 `grep -rn "getTicketOriginalInquiry|ticketOriginalInquiry" src/korail_mobile_api/*.py`로 확인 시 매치 없음.
- **상세**: 파일이 내 지정 폴더(`network/data/`, `network/response/`) 안에 있다는 이유만으로 필드 단위 전수 검증은 하지 않았다 — 실질적 소유(DAO 구현) 주체가 다른 에이전트 담당 영역이기 때문이며, 중복 검증/월권을 피하기 위해 존재만 기록한다.
- **제안**: 다른 에이전트(예약/취소, 지연배상, 조회) 보고서와 교차 확인해서 사각지대가 없는지 확인할 것.

---

## 4. 확인했으나 문제없음(요약, findings에는 미포함)

- `BaseRequest`/`BaseResponse` 공통 필드 3종 + 2종 — 정확 일치.
- DynaPath 토큰 발급 조건 6개 경로 문자열 — `constants.py:421-430`과 `ExecuteDao.java:27` **정확 일치**(이전 세션에서 문제였던 논스 알파벳 36자 이슈는 이미 62자로 수정 완료 확인, `dynapath.py:24-26`).
- `IS_MACRO_ACTIVE` 서버제어 킬스위치(`I4/a.java:14`, `IntroActivity.java:663`) — 라이브러리는 `errors.py:47-82` 독스트링에서 이 메커니즘을 정확히 서술하고 "서버가 코드로 매크로를 알리지 않는다"는 점까지 반영해 별도 예외 타입을 만들지 않기로 한 설계를 확인. 게이트 자체를 강제하는 로직은 없으나(`DynapathConfig.enabled` 수동 플래그), 이는 라이브러리 사용자가 명시적으로 켜야 하는 안전한 기본값(`enabled=False`)이라 문제 아님.
- `StationDataDao`/`StationInfoDao`/`MaasStationListDao`/`CookieDao` — 필드 전수 일치.
- `CommonCodeDao`(공통코드, 버전체크/휴일팝업/이지페이 등 25개+ 중첩 DTO) — `getCommonCode` 호출 자체는 구현되어 있으나 응답 파싱은 원시 `BaseKorailResponse`만 반환(`client.py:1184-1189`, 타입 세분화 없음). 이는 "일부 필드만 못 읽는" 정도가 아니라 애초에 타입 파서를 만들지 않은 설계 선택으로 보여 findings에 넣지 않았다(호출자가 `.raw`로 전 필드 접근 가능).
- `TrainInquiryDao`/`ProductTrainInquiryRequest`/`RsvInquiryRequest` 필드 전체 — `search_trains`/`search_transfer_trains`에서 기본값(`"N"`/`"000"`/`"015"` 등)까지 smali 인용과 함께 정확 재현됨.
- `AppDataDao`/`NoticeDao`/`ServiceCheckDao` — 필드 전수 일치.
- NetFunnel opcode enum(`T6/c.java`) 및 `d.java`의 5101 전용 `sid`/`aid` 전송 — 기존 세션에서 라이브 확증된 부분이라 이번엔 opcode 상수만 재대조(일치), 심층 로직 재검증은 생략.
- 예약 요청 데이터 구조(`RJrny` 등)의 `_` 접미사 컨벤션이 `mutation_payloads.py`에 반영되어 있음을 확인(내 dao 스코프 밖이라 전수는 아님).

## 5. 확인 못한 것 (정직하게 기록)

- `OPsg`/`OSeat`/`OSrcar`/`OWait`(구), `RPsg`/`RSeat`/`RSrcar`/`RDscp`/`ROrtg`(신) 9개 데이터 클래스는 파일을 열지 않았다.
- `network/request/payment/{IPaymentRequest,PaymentMethod}.java`, `network/request/research/SeatSearchRequest.java`, `network/request/myTicket/PushUpdateRequest.java`, `network/data/certification/DiscountPriceParams.java`는 구조만 훑고 라이브러리 대조는 하지 않았다(타 도메인 DAO 소비 확인 후 스코프 밖으로 판단).
- NetFunnel의 URL 파라미터 순서·타임아웃 계산·`i.java`/`h.java` 세부 로직은 기존 세션에서 "충실 확인됨"으로 기록되어 있어 이번 세션에서 재검증하지 않았다(조언에 따름).
- 서버가 실제로 6개 매크로경로 밖에서 `DynaPath-Result` 음수 헤더를 내려주는지는 정적 분석으로 확인 불가.
