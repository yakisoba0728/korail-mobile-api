# 문서 품질 갭 감사: `korail-apk-analysis.md` / `api-endpoints.md`

## 범위와 기준

- 대상 문서: `docs/korail-apk-analysis.md`, `docs/api-endpoints.md`
- 생성 산출물: `analysis/reports/api-endpoints.tsv`
- 대조 기준: 로컬 정적 산출물 `analysis/jadx/sources/`, `analysis/apktool/`
- 수행 제한: 운영 API 호출 없음. 동적 트래픽, 로그인, WebView 실행 검증 없음.

## 요약 결론

초기 문서는 APK의 네트워크 구조와 Retrofit 엔드포인트를 빠르게 파악하기에는 유용하지만, "재현 가능한 API 매뉴얼"로 쓰기에는 부족했다. 가장 큰 문제는 초기 `analysis/reports/api-endpoints.tsv`와 이를 기반으로 한 `docs/api-endpoints.md`가 `@Field(CONSTANT)` / `@Query(CONSTANT)` 형태의 파라미터를 일부 누락했다는 점이다. 통합 단계에서 추출기를 `@GET`/`@POST` annotation 기준으로 바꾸고 compile-time string constant를 resolve하도록 고쳐, `CashReceipt.java` 1개 entry와 상수 기반 field/query를 반영했다.

후속 재생성 기준 최종 수치는 Retrofit method entry `165`개, distinct HTTP+path `159`개, annotated interface `35`개다. `docs/korail-apk-analysis.md`의 Network Architecture 영역별 count 표는 업무 영역별 태깅이라 합계가 총 Retrofit row 수와 일치하도록 설계된 taxonomy가 아니다.

## 카운트 불일치와 용어 정리 필요

### 1. 총 endpoint 수 표현의 의미가 모호했음

초기 `docs/api-endpoints.md`와 `analysis/reports/api-endpoints.tsv` 기준 row 수는 164개였고, 중복 HTTP/path를 합치면 158개였다. 통합 단계에서 파일명이 `*Service.java`로 끝나지 않는 Retrofit interface `CashReceipt.java`를 포함하도록 수정하면서 최종 row 수는 165개, distinct HTTP/path는 159개가 됐다.

중복 HTTP/path:

| 중복 수 | HTTP | Path | Method |
|---:|---|---|---|
| 2 | GET | `/classes/com.korail.mobile.certification.ReservationList` | `CertificationService.applyDisabilityCertification`, `CertificationService.inquiryTicketRsv` |
| 2 | POST | `/classes/com.korail.mobile.certification.TicketReservation` | `CertificationService.reservation` overload 2개 |
| 2 | POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | `CertificationService.reservation` overload 2개 |
| 2 | POST | `/classes/com.korail.mobile.common.encrypt.do` | `CommonService.getEncrypt`, `CommonService.getKBPayEncrypt` |
| 2 | POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | `BusReservationService.reservationChange`, `ReservationCancelService.reservationChange` |
| 2 | POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `BusReservationService.reservationCancelCheck`, `ReservationCancelService.reservationCancelCheck` |

수정 제안:

- `Total Retrofit endpoints found` 같은 표현을 `Retrofit method entries: 165 / distinct HTTP+path: 159`처럼 분리한다.
- 같은 path를 공유하는 overload는 별도 "호출 시나리오"로 묶고, endpoint 자체 수와 Java method 수를 혼용하지 않는다.

### 2. `korail-apk-analysis.md`의 영역별 count 합계와 endpoint total 혼동

초기 Network Architecture 표의 Count 합계는 historical snapshot에서 `166`으로 기록되었고, 후속 통합 뒤 현재 표 기준 합계는 `167`이다. 이 값은 `165 method entries`와 비교 가능한 endpoint total이 아니라 cross-cutting service가 겹칠 수 있는 업무 태깅 수다.

수정 제안:

- 표가 "service별 중복 집계"인지 "업무 영역별 태깅 수"인지 명시한다.
- 한 endpoint가 여러 영역에 걸치는 경우 `overlap`으로 별도 표시하거나, 총계와 비교 가능한 단일 taxonomy로 재분류한다.

## Endpoint/Field 불일치 발견 사항

### 1. 상수 기반 annotation 파라미터 누락

`api-endpoints.tsv`는 `@Field("literal")`, `@Query("literal")`은 잡지만 `@Field(C1262b.DPT_DT)`, `@Field(OJrny.TRN_GP_CD)`, `@Query(Price2FareDao.Price2Fare.trnNoString)` 같은 상수 기반 annotation을 충분히 해석하지 못한다. 정적 스캔 기준 13개 service file, 35개 service method signature에서 상수 기반 annotation이 확인된다.

대표 상수 정의:

- `analysis/jadx/sources/b5/C1262b.java`: `DPT_DT="dptDt"`, `DPT_TM="dptTm"`, `ARV_RS_STN_CD="arvRsStnCd"`, `TRAIN_NO="txtGoTrnNo"`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OJrny.java`: `TRN_GP_CD="txtTrnGpCd"`, `TRN_NO="txtTrnNo"`, `JRNY_SQ_NO="txtJrnySqno"`, `JRNY_CNT="txtJrnyCnt"` 등
- `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`: `trnNoString="trnNo"`, `jrnySqnoString="jrnySqno"`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OSeat.java`: `PSRM_CL_CD="txtPsrmClCd"`, `SEAT_ATT_CD4="txtSeatAttCd4"`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/RPsg.java`: `PSG_CNT="psgCnt"`

### 2. 문서/TSV에서 누락된 주요 필드 예시

| Service.method | Path | TSV/문서 누락 필드 | 대조 source |
|---|---|---|---|
| `SeatMovieService.getRsvInquiry` | `/classes/com.korail.mobile.seatMovie.ScheduleView` | `txtTrnGpCd`, `txtGoTrnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java` |
| `SeatMovieService.getRsvLimousineInquiry` | `/classes/com.korail.mobile.seatMovie.LimousineScheduleView` | `txtTrnGpCd`, `txtGoTrnNo` | same |
| `SeatMovieService.getRsvProductInquiry` | `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | `txtTrnGpCd` | same |
| `BusReservationService.reservationList` | `/classes/com.korail.mobile.lmu.scdlQry.do` | `dptDt`, `arvRsStnCd`, `dptTm`, `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java` |
| `BusReservationService.reservationSeatList` | `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do` | `trnNo`, `arvRsStnCd` | same |
| `ReservationCancelService.reservationCancel` | `/classes/com.korail.mobile.reservationCancel.ReservationCancel` | `txtJrnySqno`, `txtJrnyCnt` | `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java` |
| `ReservationCancelService.reservationCancelCheck` | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `txtJrnySqno`, `txtJrnyCnt` | same |
| `ReservationCancelService.reservationChange` | `/classes/com.korail.mobile.reservation.reservationChange.do` | `psgCnt` | same |
| `ResearchService.getCarList` | `/classes/com.korail.mobile.research.TrainResearch` | `txtPsrmClCd`, `txtRunDt`, `txtDptDt`, `txtTrnClsfCd`, `txtTrnNo`, `txtDptRsStnCd`, `txtArvRsStnCd`, `txtDptStnRunOrdr`, `txtArvStnRunOrdr`, `txtTrnGpCd`, `txtTotPsgCnt` | `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java` |
| `ResearchService.getAssignScheduleView` | `/classes/com.korail.mobile.research.assignScheduleView.do` | `dptDt`, `dptTm` | same |
| `ResearchService.getSeatList` | `/classes/com.korail.mobile.research.TResidualSeatsResearch.do` | `trnNo`, `arvRsStnCd` | same |
| `ResearchService.getNCardSchedultView` | `/classes/com.korail.mobile.research.dcntCrdScheduleView.do` | `dptDt`, `dptTm` | same |
| `CommonService.getCommonCode` | `/classes/com.korail.mobile.common.code.do` | `code` list | `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonService.java` |
| `TicketService.deviceReset` | `/classes/com.korail.mobile.tk.dvcInfoInit.do` | `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java` |
| `TicketService.getSelfSeatChgInfo` | `/classes/com.korail.mobile.self.seatChgInfo.do` | `trnNo`, `arvRsStnCd` | same |
| `TicketService.gurdSmsSnd` | `/classes/com.korail.mobile.tk.gurdSmsSnd.do` | `jrnySqno` | same |
| `TicketService.selfCheckinCancel/info/possible/register` | `/classes/com.korail.mobile.checkin.*.do` | `jrnySqno` | same |
| `MyTicketService.requestUpgradeSeat` | `/classes/com.korail.mobile.myTicket.reqUpgradeSeat` | `jrnySqno`, `dptDt`, `dptTm`, `arvRsStnCd`, `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/MyTicketService.java` |
| `TrainsInfoService.getFresScar` | `/classes/com.korail.mobile.trn.fresScar.do` | `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java` |
| `TrainsInfoService.getPriceFare` | `/classes/com.korail.mobile.trainsInfo.TrainCharge` | `txtSeatAttCd4` | same |
| `TrainsInfoService.getSelectStationInfo` | `/classes/com.korail.mobile.qry.chtnStn.do` | `arvRsStnCd` | same |
| `TrainsInfoService.getTourTrainInfo` | `/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom` | `txtTrnGpCd` | same |
| `TrainsInfoService.getTrainSchedule` | `/classes/com.korail.mobile.research.actualTrainSchedule.do` | `trnNo` | same |
| `RefundService.returnTicket` | `/classes/com.korail.mobile.refunds.RefundsRequest` | `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java` |
| `DelayService.athnIsu` | `/classes/com.korail.mobile.dlay.athnIsu.do` | `trnNo` | `analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java` |
| `AddService.additionalService` | `/classes/com.korail.mobile.addService.reserve.do` | `jrnySqno` | `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java` |
| `PushService.callCrew` | `/classes/com.korail.mobile.push.callCrew.do` | `jrnySqno` | `analysis/jadx/sources/com/korail/talk/network/dao/push/PushService.java` |
| `CustService.mchdDcntTgt` | `/classes/com.korail.mobile.cust.mchdDcntTgt.do` | `dptDt` | `analysis/jadx/sources/com/korail/talk/network/dao/cust/CustService.java` |

수정 제안:

- endpoint generator가 annotation argument AST를 읽어 literal과 static final constant를 모두 resolve해야 한다.
- resolve 실패 시 `@Field(C1262b.DPT_DT)`처럼 원문 expression을 그대로 남기고, 별도 `unresolved_params` column을 둔다.
- `api-endpoints.md`에는 현재 `Return Type`과 `Source`가 들어 있다. `FormUrlEncoded`와 constant-resolution 상태는 `api-contracts.md`와 generated TSV를 함께 본다.

### 3. `FieldMap` / `QueryMap`이 "필드 미상"으로 남아 있음

현재 endpoint 추출 기준 `FieldMap` 또는 `QueryMap` row는 21개다. 문서에는 map 존재와 대표 schema를 표시했고, branch별 실제 wire key 조합은 각 flow report와 `api-contracts.md`에서 추적한다.

필수로 풀어야 하는 source:

- 예약 구형 map: `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OPsg.java`, `OSeat.java`, `OJrny.java`, `OSrcar.java`
- 예약 변경/신형 map: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RPsg.java`, `RJrny.java`, `RSeat.java`, `RSrcar.java`, `RDscp.java`, `ROrtg.java`
- 결제 map: `analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java`
- 운임 조회 map: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`, `Price2FareDao.java`
- 예약 요청 조합: `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java`

예: `PaymentMethod`는 `hidStlCrCrdNo{n}`, `hidVanPwd{n}`, `hidCrdVlidTrm{n}`, `hidIsmtMnthNum{n}`, `spayDvCd_1_1`, `spayCphdDatVal_1_1`, `spayDvCd_2_1`, `spayCphdDatVal_2_1` 등을 동적으로 만든다. 이 구조는 endpoint table 한 줄로는 설명되지 않는다.

### 4. 일부 path 표기가 그대로 source typo인지 정상화 대상인지 불명확

`TicketService.getMaasCancel`의 path는 source상 `/classes//com.korail.mobile.addService.cancelPay.do`로 slash가 두 개다. 문서에는 그대로 들어가 있지만, 이것이 서버에서 정상 수용되는 실제 path인지 Retrofit/서버에서 normalize되는지 설명이 없다.

수정 제안:

- "source literal path"와 "normalized display path"를 분리한다.
- 이 항목은 정적 분석만으로 runtime normalize 여부를 확정하지 않았다고 표시한다.

## 누락된 문서 카테고리

### 1. 응답 schema 문서

초기 문서는 request endpoint/field 중심이었다. 현재는 static DTO/getter 기반 response model catalog가 존재하지만, 실제 서버 JSON body, nullable/required 규칙, runtime-only 값은 아직 응답 샘플 없이 확정할 수 없다.

우선 문서화할 source:

- 공통: `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`
- 조회 응답: `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java`
- 예약 응답: `analysis/jadx/sources/com/korail/talk/network/response/certification/ReservationResponse.java`
- 티켓/환불/결제 DAO inner response classes: `analysis/jadx/sources/com/korail/talk/network/dao/**/**/*Dao.java`

문서에 필요한 항목:

- `h_msg_cd`, `h_msg_txt`, `strResult`의 공통 의미
- success/fail 판단 위치
- 리스트 필드명, nested object, `@SerializedName`/Gson annotation 기준 JSON key
- nullable/optional로 보이는 필드

### 2. 요청 field dictionary와 코드값 dictionary

문서에는 필드명이 나열되어 있지만 의미와 값 도메인이 거의 없다. 특히 아래 필드는 여러 흐름에서 중요하다.

- 열차/역: `txtGoStart`, `txtGoEnd`, `dptRsStnCd`, `arvRsStnCd`, `txtDptDt`, `txtDptTm`, `runDt`, `trnNo`
- 승객/좌석: `txtPsgFlg_1..5`, `txtSeatAttCd_2..4`, `psrmClCd`, `rqSeatAttCd`, `roomClsfCd`, `txtTotPsgCnt`
- 업무 구분: `txtMenuId`, `radJobId`, `txtJobDv`, `jobDvCd`, `ctlDvCd`, `qryDvCd`
- 결제: `hidInrecmnsGridcnt`, `hidStlMnsCd{n}`, `hidMnsStlAmt{n}`, `spayDvCd_*`, `lumpStlTgtNo`
- 환불/티켓: `tkRetPwd`, `ogtkSaleWctNo`, `ogtkSaleDd`, `ogtkSaleSqno`, `jrnySqno`

필드 의미는 service interface만으로 부족하므로 DAO execute method와 UI request setter 호출까지 추적해야 한다.

### 3. runtime default와 conditional field

현재 문서는 `Device`, `Version`, `Key`를 "usually"라고 표현하지만, endpoint별 예외를 체계적으로 표시하지 않는다. 예를 들어 `CommonService.authQRLocation`은 `Key`가 없고, `CommonService.getMaasStationList`는 `addSrvDvCd`만 보낸다. 반대로 `Sid`, `sidTest`, `x-dynapath-m-token`처럼 조건부 필드/헤더가 붙는 흐름은 별도 표가 필요하다.

우선 source:

- `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`
- `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java`
- `analysis/jadx/sources/S4/C0812l.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchCarListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchSeatListDao.java`

### 4. WebView/API bridge와 non-Retrofit URL inventory

`api-endpoints.md`는 Retrofit interface만 대상으로 한다. 하지만 실제 앱 연동 표면에는 WebView POST/GET, scheme bridge, SRT, external OAuth/identity/payment redirect가 있다. `korail-apk-analysis.md`에 설명은 있으나 별도 inventory가 없다.

우선 source:

- `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/EasyPayWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceWebViewActivity.java`
- `analysis/reports/url-strings.tsv`
- `analysis/apktool/AndroidManifest.xml`

필요 문서:

- intent extra `WEB_GET_URL`, `WEB_POST_URL`, `WEB_GET_PARAMETER`, `WEB_POST_PARAMETER`
- JavaScript interface method별 trust boundary
- `korailtalk://` scheme별 parameter
- SRT host/path 및 HTTP->HTTPS 치환 위치
- Kakao/Naver/mobile ID/payment redirect scheme

### 5. NetFunnel/DynaPath/Sid 보안 제어 흐름

현재 문서는 요약 수준이다. 매뉴얼에는 endpoint별 적용 조건이 필요하다.

우선 source:

- DynaPath header 조건: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java`
- DynaPath error handling: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java`
- `Sid` 생성: `analysis/jadx/sources/S4/C0812l.java`
- macro flag source: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java`, `analysis/jadx/sources/com/korail/talk/network/dao/common/CommonCodeDao.java`
- NetFunnel action id 사용처: `analysis/jadx/sources/com/korail/talk/**`에서 `act_` / `NetFunnel` 검색 결과

문서에 필요한 표:

- endpoint path
- 조건 flag
- 추가 header/field
- 실패 시 UI/exception 처리
- 정적 분석으로 확정 가능한 것과 runtime 검증 필요 항목

### 6. 로컬 데이터와 민감정보 저장 범위

`korail-apk-analysis.md`는 로컬 DB 모델을 요약하지만, comprehensive manual에는 저장 위치, DAO, 필드, 암호화 유틸, 보존/삭제 흐름이 필요하다.

우선 source:

- DB helper/model: `analysis/jadx/sources/com/korail/talk/database/**`
- 암호화 유틸: `analysis/jadx/sources/F4/a.java`
- 앱 초기화/쿠키: `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`
- 로그인 저장값: `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginDao.java`, 로그인 UI package

## 종합 매뉴얼 제안 구조

1. 분석 기준과 한계
   - APK hash, package/version/API version
   - 정적 분석 산출물 경로
   - live API 미수행, dynamic-only 항목 표시 규칙

2. 런타임 환경과 host 선택
   - `CONNECT_SERVER`, `SERVER_TYPE`, `getSSLHost()`
   - 운영/개발 host 표
   - network security config와 cleartext 예외

3. 네트워크 공통 레이어
   - Retrofit 1, `UrlConnectionClient`, timeout, Gson
   - `BaseRequest` 공통 필드와 endpoint별 예외
   - 쿠키/JSESSIONID/WebView 동기화
   - DynaPath, NetFunnel, Sid

4. Endpoint catalog
   - `method entry count`와 `distinct HTTP/path count` 분리
   - service별 endpoint table
   - columns: `Service`, `Java method`, `HTTP`, `Path source literal`, `Normalized path`, `Return type`, `FormUrlEncoded`, `Params`, `Map schema`, `Headers`, `Source file:line`
   - duplicate path/overload 묶음

5. Request schema dictionary
   - 공통 필드
   - 열차 조회 필드
   - 예약 구형 map (`OPsg`, `OSeat`, `OJrny`, `OSrcar`)
   - 예약 변경/신형 map (`RPsg`, `RJrny`, `RSeat`, `RSrcar`, `RDscp`, `ROrtg`)
   - 결제 `PaymentMethod`
   - 환불/티켓/승차변경/MAAS/패스/N카드/gifticket field group

6. Response schema dictionary
   - `BaseResponse`
   - 주요 response DTO별 JSON field
   - success/failure handling

7. 업무 흐름별 deep dive
   - startup/common-code/station data
   - login/session/autologin/password transform
   - train inquiry/seat/car/fare
   - reservation/member/non-member/PBEP
   - reservation change/cancel/wait
   - payment/card/easy pay/Toss/NaverPay/Payco/STBK
   - ticket list/self check-in/platform/gift/SMS
   - refund/delay/compensation/receipt
   - pass/NCard/mileage/XPoint/RailPlus
   - MAAS/add-on/cart/bus/SRT bridge

8. WebView and scheme bridge manual
   - WebView intent extras
   - JavaScript interface method table
   - scheme table
   - external host inventory

9. Local data/security notes
   - DB models and sensitive fields
   - encryption/key derivation
   - permissions/exported components
   - static-only caveats

10. Appendices
   - source file index
   - constant dictionary
   - generator methodology
   - unresolved/decompile warning list

## 우선 수정 작업 목록과 통합 반영 상태

1. Done: `analysis/reports/api-endpoints.tsv` 생성기를 수정해 constant annotation을 resolve했다.
2. Done: `docs/api-endpoints.md`를 재생성해 `165 method entries`, `159 distinct HTTP/path`를 함께 표시했다.
3. Partial: `FieldMap`/`QueryMap` row는 endpoint table에 표시했고, 상세 map schema source는 각 flow agent report와 `api-contracts.md`에서 추적한다.
4. Done: `korail-apk-analysis.md`의 Network Architecture count 표현을 수정하고 taxonomy 설명을 추가했다.
5. Done: `api-endpoints.md`에 return type과 source line을 추가했다.
6. Done: `docs/korail-apk-analysis.md`는 요약 문서로 유지하고, 상세 매뉴얼은 `docs/deep-dive/` 아래로 분리했다.
7. Done: WebView/non-Retrofit URL inventory를 `docs/deep-dive/webview-and-url-catalog.md`와 `18-nonretrofit-urls-resources-smali.md`에 작성했다.

## 인용해야 할 핵심 source 파일

- 공통 네트워크: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`, `BaseResponse.java`, `ExecuteDao.java`, `BaseDaoHelper.java`
- host/env: `analysis/jadx/sources/G4/a.java`, `analysis/jadx/sources/S4/z.java`, `analysis/jadx/sources/d5/EnumC5607a.java`
- Sid: `analysis/jadx/sources/S4/C0812l.java`
- service interfaces: `analysis/jadx/sources/com/korail/talk/network/dao/**/*Service.java`
- train inquiry: `analysis/jadx/sources/com/korail/talk/network/request/inquiry/RsvInquiryRequest.java`, `TrainInquiryRequest.java`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java`
- reservation: `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java`, `analysis/jadx/sources/com/korail/talk/network/data/reservation/**`
- payment: `analysis/jadx/sources/com/korail/talk/network/request/payment/PaymentMethod.java`, `analysis/jadx/sources/com/korail/talk/network/dao/payment/RsvPaymentDao.java`
- fare/price: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`, `Price2FareDao.java`
- login/session: `analysis/jadx/sources/com/korail/talk/network/dao/login/LoginDao.java`, `analysis/jadx/sources/com/korail/talk/application/KTApplication.java`
- WebView/scheme: `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java`, `IntegrationWebViewActivity.java`, `EasyPayWebViewActivity.java`
- manifest/security config: `analysis/apktool/AndroidManifest.xml`, `analysis/apktool/res/xml/network_security_config.xml`

## 잔여 불확실성

- 실제 서버가 double slash path를 normalize하는지, 일부 optional field를 생략해도 수용하는지는 정적 분석만으로 확정할 수 없다.
- `FieldMap`에 들어가는 모든 조합은 UI flow와 DAO execute method를 추가 추적해야 한다. 현재 감사는 대표 구조와 누락 범주를 식별한 수준이다.
- response schema는 static DTO/getter catalog로 보강되었다. 남은 작업은 실제 서버 JSON body, nullable/required 규칙, runtime-only 값 검증이다.

## 20-agent follow-up audit 보강

- follow-up audit 기준 현재 endpoint/문서 mirror는 `165` method entries, `159` distinct HTTP+path, `21` FieldMap/QueryMap rows로 정리한다.
- `api-endpoints.md`에는 `Return Type`과 `Source`가 들어 있으므로, 이전 “return_type/source 누락” 항목은 완료된 상태로 본다.
- response schema는 `17-response-models-exhaustive.md`와 `network-model-fields.md`로 보강되었다. 남은 gap은 실제 서버 응답 샘플, nullable/required, runtime-only field 검증이다.
- stale path scan 기준 오래된 임시 JADX 경로와 lowercase G6 package 참조는 정정 대상이며, 현재 문서에서는 canonical local analysis source path와 uppercase `G6` package 경로를 사용한다.
