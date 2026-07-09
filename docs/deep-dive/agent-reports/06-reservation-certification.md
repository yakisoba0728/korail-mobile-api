# 예약/인증 API 정적 분석 보고서

분석 범위는 `CertificationService`, `ReservationService`, `ReservationRequest`, `ReservationDao`, 비회원 예약, 인증/할인 엔드포인트, 예약대기, 그리고 인증/예약과 연결되는 리무진/버스 예약 흐름이다. 이 문서는 APK 디컴파일 산출물만 근거로 작성했으며 운영 서비스 호출이나 live response 캡처는 수행하지 않았다.

## 근거 소스

- `analysis/jadx/sources/com/korail/talk/network/dao/certification/CertificationService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/ReservationDao.java`
- `analysis/jadx/sources/com/korail/talk/network/request/reservation/ReservationRequest.java`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OPsg.java`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OSeat.java`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OJrny.java`
- `analysis/jadx/sources/com/korail/talk/network/data/reservation/old/OSrcar.java`
- `analysis/jadx/sources/com/korail/talk/network/response/certification/ReservationResponse.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/*Certification*Dao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/DiscountPriceDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservation/ReservationService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationWait/RsvWaitDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationWait/ReservationWaitService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`
- `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/a.java`
- `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/certification/GovernmentCertificationActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/certification/DisabilityCertificationActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java`
- `analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java`
- `docs/api-endpoints.md`

## 공통 요청/응답 규칙

모든 `BaseRequest` 파생 요청은 생성자에서 다음 값을 기본 세팅한다.

| 필드 | 값 | 근거 |
|---|---|---|
| `Device` | `AD` | `BaseRequest.ANDROID` |
| `Version` | `250601003` | `BaseRequest.VERSION` |
| `Key` | `korail1234567890` | `BaseRequest.APP_KEY` |

공통 응답 베이스는 `BaseResponse`이다.

| 필드 | 의미 |
|---|---|
| `strResult` | 성공/실패 문자열. 코드에는 `SUCC`, `FAIL` 상수가 있다. |
| `h_msg_cd` | 서버 메시지 코드. 앱 분기에서 오류/예약대기/특수 상태 판정에 사용한다. |
| `h_msg_txt` | 서버 메시지 텍스트. 앱은 일부 화면에서 `<br>`을 줄바꿈으로 치환한다. |

`BaseDaoHelper.HttpTask`는 `AsyncTask`에서 `executeDao()`를 호출하고 응답을 `BaseActivity.onIntegrationResult()`로 전달한다. `RetrofitError` 중 403 Forbidden이고 `DynaPath-Result` 헤더가 음수이면 body JSON의 `message`를 macro dialog 메시지로 저장한다. `BaseActivity.onIntegrationResult()`는 `FAIL`, `WRC000288`, `P058`, `SUPDATE`, `SEMGTK` 등을 공통 오류 또는 특수 상태로 처리한 뒤 `onReceive()` 또는 `onReceiveError()`를 호출한다.

## CertificationService 엔드포인트

`CertificationService`는 인증, 할인 재계산, 일반/비회원 예약을 함께 가진다.

| HTTP | Path | Java method | 요청 구조 | 응답 |
|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.certification.ReservationList` | `applyDisabilityCertification` | Query: `Device`, `Version`, `Key`, `hidPnrNo`, `txtPsgDisc0019Cnt`, `QueryMap` 6개 | `BaseResponse` |
| GET | `/classes/com.korail.mobile.certification.assemblyCert` | `certCongressperson` | Query: `Device`, `Version`, `Key`, `freeDiscCertNo`, `certNo`, `abrdDt` | `CongresspersonCertResponse` |
| POST | `/classes/com.korail.mobile.certification.MeritCert` | `certMerit` | Form: `Device`, `Version`, `Key`, `txtFreeDiscCertNo`, `txtAcptPwd`, `txtJuminNo7`, `txtAbrdDt` | `MeritCertResponse` |
| GET | `/classes/com.korail.mobile.certification.disabled.do` | `disabledCertification` | Query: `Device`, `Version`, `Key`, `regNum`, `hdcpGrade` | `DisabledCertificationResponse` |
| POST | `/classes/com.korail.mobile.certification.PriceReCalculation` | `getDiscountPrice` | Form: `Device`, `Version`, `Key`, `hidPnrNo`, `txtJobId`, `hiduserYn`, `hidCustNo`, `txtPsgGridcnt`, list fields | `ReservationResponse` |
| GET | `/classes/com.korail.mobile.pbep.toknCre.do` | `govermentCertification1` | Query: `Device`, `Version` | `GovernmentCertificationResponse` |
| GET | `/classes/com.korail.mobile.pbep.sttChck.do` | `govermentCertification2` | Query: `Device`, `Version`, `csrfToken` | `GovernmentCertificationStep2Response` |
| GET | `/classes/com.korail.mobile.certification.ReservationList` | `inquiryTicketRsv` | Query: `Device`, `Version`, `Key`, `hidPnrNo` | `ReservationResponse` |
| POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | `reservation` | 비회원 상세 예약 form + `OPsg`, `OSeat`, `OJrny`, `OSrcar` FieldMap | `ReservationResponse` |
| POST | `/classes/com.korail.mobile.certification.TicketReservation` | `reservation` | 회원 상세 예약 form + `pbepInfo` + `OPsg`, `OSeat`, `OJrny`, `OSrcar` FieldMap | `ReservationResponse` |
| POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | `reservation` | 비회원 Bixby/simple form: `Device`, `Version`, `Key`, `txtCustNm`, `txtCpNo`, `txtCustPw`, `FieldMap data` | `ReservationResponse` |
| POST | `/classes/com.korail.mobile.certification.TicketReservation` | `reservation` | 회원 Bixby/simple form: `Device`, `Version`, `Key`, `FieldMap data` | `ReservationResponse` |

주의: `ReservationList`는 장애인 할인 적용과 예약 조회가 같은 path를 공유하지만 Java method와 파라미터가 다르다.

## ReservationService 엔드포인트

`ReservationService`는 기존 예약 목록, 좌석 조건, 좌석 지정 예약, 승차권 변경 예약을 담당한다.

| HTTP | Path | Java method | 요청 구조 | 응답 |
|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservation.guideSeatCnd.do` | `getGuideSeatCnd` | Form: `Device`, `Version`, `Key`, `rqSeatAttCd` | `BaseResponse` |
| GET | `/classes/com.korail.mobile.reservation.ReservationView` | `getRsvHistory` | Query: `Device`, `Version`, `Key` | `TicketRsvHistoryResponse` |
| POST | `/classes/com.korail.mobile.reservation.tripChgPrsC.do` | `getTicketChangeReservation` | Form: `trvlKndCd`, `totPrnb`, `isePrnb`, `stndSeatFlg`, `intgTktIseFlg`, `prcFareReCalcFlg`, `tmpJobSqno`, `alcSeatDmnPsDvCd`, `jrny2Cnt`, `psg2Cnt`, `ctlDvCd`, `frcSaleRsnCont`, `RJrny`, `RSrcar`, `RSeat`, `RPsg`, `ROrtg`, `RDscp` | `ReservationResponse` |
| POST | `/classes/com.korail.mobile.reservation.seatAssign.do` | `setSeatAssignReservation` | Form: `menuId`, `custMgNo`, `totPrnb`, `stndFlg`, `rqScarNum`, `RJrny`, `RSrcar`, `RSeat`, `RPsg`, `ROrtg` | `SeatAssignReservationResponse extends ReservationResponse` |

`RJrny`, `RSrcar`, `RSeat`, `RPsg`, `ROrtg`, `RDscp`는 신형 예약/변경용 FieldMap이며 old `O*` 구조와 키 prefix가 다르다. 이 보고서의 주 대상인 `ReservationRequest` 예약은 old `OPsg/OSeat/OJrny/OSrcar`를 사용한다.

## ReservationRequest와 ReservationDao

`ReservationRequest` 필드는 Retrofit form field명과 거의 1:1 대응한다.

| Java field/getter | 전송 field | 설명 |
|---|---|---|
| `pnrNo` / `getPnrNo()` | `pnrNo` | 기존 PNR이 있는 후속/연계 예약에서 사용된다. 신규 일반 예약에서는 null 가능성이 있다. |
| `txtMenuId` / `getMenuId()` | `txtMenuId` | 메뉴/상품 구분. 기본 빌더는 `"11"`을 사용한다. |
| `txtJobId` / `getJobId()` | `txtJobId` | 예약 작업 구분. 기본 예약은 `"1101"`, 예약대기는 `"1102"`, 입석+좌석 클릭 분기는 `"1202"`를 세팅한다. |
| `txtGdNo` / `getGdNo()` | `txtGdNo` | 상품/할인 goods id. 일반 기본값은 빈 문자열로 구성된다. |
| `hidFreeFlg` / `getHidFreeFlg()` | `hidFreeFlg` | 무료/무임 여부 플래그. 기본 예약 빌더는 `"N"`을 세팅한다. |
| `txtStndFlg` / `getStndFlg()` | `txtStndFlg` | 입석 포함 여부. 기본 `"N"`, 입석+좌석 재구성 시 `"Y"`. |
| `pbepInfo` / `getPbepInfo()` | `pbepInfo` | 공무원/정부 인증 step2 결과. 회원 예약 endpoint에만 명시 field로 들어간다. |
| `txtCustNm` / `getCustNm()` | `txtCustNm` | 비회원 이름. |
| `txtCpNo` / `getCpNo()` | `txtCpNo` | 비회원 휴대폰 번호. |
| `txtCustPw` / `getCustPw()` | `txtCustPw` | 비회원 예약 비밀번호. |
| `oPsg` | FieldMap | 승객 수/유형/할인/카드 번호. |
| `oSeat` | FieldMap | 좌석 속성/실 등급. |
| `oJrny` | FieldMap | 여정/열차/역/시간. |
| `oSrcar` | FieldMap | 선택 객차/좌석. |
| `isNotNonMemberShow` | 전송 안 함 | 비회원 예약 UI/가능 여부 판단에 쓰는 내부 플래그. |

`ReservationDao.executeDao()`의 분기는 단순하다.

- `custNm`과 `cpNo`가 모두 있으면 `/classes/com.korail.mobile.nonMember.NonMemTicket` 오버로드를 호출한다.
- 둘 중 하나라도 비어 있으면 `/classes/com.korail.mobile.certification.TicketReservation` 오버로드를 호출한다.
- 비회원 상세 예약 호출에는 `txtCustPw`도 같이 전송하지만 분기 조건에는 `txtCustPw` null 여부가 포함되지 않는다.
- 회원 예약 호출에는 비회원 식별값 대신 `pbepInfo`가 들어간다.

`BixbyReservationDao`는 별도 simple overload를 사용한다. 이 경우 `custNm`, `cpNo`, `custPw`가 모두 있으면 비회원 simple endpoint를 호출하고, 아니면 회원 simple endpoint를 호출한다.

## OPsg FieldMap 구조

근거: `network/data/reservation/old/OPsg.java`, `W4/a.java`, `TicketListActivity.java`.

| Setter | 생성 key | 값 예시/규칙 |
|---|---|---|
| `setTotPsgCnt(v)` | `txtTotPsgCnt` | 전체 승객 수 문자열. |
| `setCompaCnt(i, v)` | `txtCompaCnt{i}` | 승객 그룹별 인원 수. |
| `setPsgTpCd(i, v)` | `txtPsgTpCd{i}` | 승객 유형. 기본 빌더에서 성인/청소년/노인/장애인/안내견은 `"1"`, 어린이/동반유아는 `"3"`. |
| `setDiscKndCd(i, v)` | `txtDiscKndCd{i}` | 할인종류. 기본 성인/어린이 `"000"`, 청소년 `"P11"`, 동반유아 `"321"`, 경로 `"131"`, 중증장애 `"111"`, 경증장애 `"112"`, 안내견 `"173"`. |
| `setCardNo(i, v)` | `txtCardNo_{i}` | N카드 등 할인카드 번호. |

기본 승객 빌더(`W4.a`)는 최대 8개 그룹을 고정 순서로 채운다.

| i | 그룹 | `txtPsgTpCd{i}` | `txtDiscKndCd{i}` |
|---:|---|---|---|
| 1 | 성인 | `1` | `000` |
| 2 | 청소년 | `1` | `P11` |
| 3 | 어린이 | `3` | `000` |
| 4 | 동반유아 | `3` | `321` |
| 5 | 경로 | `1` | `131` |
| 6 | 중증장애 | `1` | `111` |
| 7 | 경증장애 | `1` | `112` |
| 8 | 안내견 | `1` | `173` |

리무진 연계 재예약에서는 티켓 좌석의 `h_psg_tp_cd`를 세어 성인(`"1"`)과 어린이(`"3"`) 두 그룹만 만들고 할인은 모두 `"000"`으로 둔다.

## OSeat FieldMap 구조

근거: `network/data/reservation/old/OSeat.java`, `W4/a.java`, `ReservationRequest.java`.

| Setter | 생성 key | 설명 |
|---|---|---|
| `setPsrmClCd(i, v)` | `txtPsrmClCd{i}` | 객실 등급. 기본 빌더는 1번 여정에 일반실 코드를 세팅한다. |
| `setSeatAttCd1(v)` | `txtSeatAttCd1` | 흡연/장애 관련 좌석 속성. 기본 빌더는 disabled/default 계열 코드를 넣는다. |
| `setSeatAttCd2(v)` | `txtSeatAttCd2` | 방향 속성. |
| `setSeatAttCd3(v)` | `txtSeatAttCd3` | 위치 속성. |
| `setSeatAttCd4(1, v)` | `txtSeatAttCd4` | 요청 좌석 속성. |
| `setSeatAttCd4(n != 1, v)` | `txtSeatAttCd4_1` | 2번째 여정 또는 병합 예약 쪽 요청 좌석 속성. |
| `setSeatAttCd5(v)` | `txtSeatAttCd5` | 기타 좌석 속성. |

`ReservationRequest.isNonmemberNotEnable()`은 `txtSeatAttCd4` 또는 `txtSeatAttCd4_1`이 특실 계열이면 비회원 예약 불가로 판단한다. 실제 특실 판정 값은 `S4.J.isSpecialRoom()` 내부 로직에 위임되어 있어 이 문서에서는 특정 코드값을 새로 추정하지 않는다.

## OJrny FieldMap 구조

근거: `network/data/reservation/old/OJrny.java`, `DirectInquiryActivity.java`, `LimousineActivity.java`, `LimousineSelectSeatActivity.java`.

| Setter | 생성 key | 설명 |
|---|---|---|
| `setJrnyCnt(v)` | `txtJrnyCnt` | 여정 수. `K4.d.DIRECT_SQ_NO`는 `"1"`, `TRANSFER_SQ_NO`는 `"2"`. |
| `setJrnySqNo(i, v)` | `txtJrnySqno{i}` | 여정 순번. 앱은 `O.getSequenceNo(...)`로 만든다. |
| `setJrnyTpCd(i, v)` | `txtJrnyTpCd{i}` | 여정 유형. `DIRECT`는 `"11"`, 병합/입석+좌석 선후행은 코드 enum을 사용한다. |
| `setTrnNo(i, v)` | `txtTrnNo{i}` | 열차 번호. |
| `setTrnClsfCd(i, v)` | `txtTrnClsfCd{i}` | 열차 분류. 리무진 흐름은 `"98"`을 사용한다. |
| `setTrnGpCd(i, v)` | `txtTrnGpCd{i}` | 열차 그룹. 리무진 흐름은 `K4.s.LIMOUSINE.getCode()`를 사용한다. |
| `setRunDt(i, v)` | `txtRunDt{i}` | 운행일. |
| `setDptDt(i, v)` | `txtDptDt{i}` | 출발일. |
| `setDptTm(i, v)` | `txtDptTm{i}` | 출발시각. |
| `setDptRsStnCd(i, v)` | `txtDptRsStnCd{i}` | 출발역 코드. |
| `setDptStnConsOrdr(i, v)` | `txtDptStnConsOrdr{i}` | 출발역 구성 순서. |
| `setDptStnRunOrdr(i, v)` | `txtDptStnRunOrdr{i}` | 출발역 운행 순서. |
| `setArvRsStnCd(i, v)` | `txtArvRsStnCd{i}` | 도착역 코드. |
| `setArvStnConsOrdr(i, v)` | `txtArvStnConsOrdr{i}` | 도착역 구성 순서. |
| `setArvStnRunOrdr(i, v)` | `txtArvStnRunOrdr{i}` | 도착역 운행 순서. |
| `setArvTm(i, v)` | `arvTm_{i}` | 도착시각. |
| `setChgFlg(i, v)` | `txtChgFlg{i}` | 변경 여부. 입석+좌석 재구성 시 `"N"`. |
| `setSrcarCnt(v)` | `txtSrcarCnt` | 선택 좌석 수. `LimousineSelectSeatActivity`가 선택 좌석 수를 넣는다. |
| `setSrcarNo(i, v)` | `txtSrcarNo{i}` | 선택 객차 번호. |
| `setSeatNo(i, v)` | `txtSeatNo{i}` | 선택 좌석 번호. |

리무진 예약은 일반 여정에 다음 값을 강제로 넣는다.

- `txtJrnyCnt=1`
- `txtJrnyTpCd1=11`
- `txtTrnGpCd1=K4.s.LIMOUSINE`
- `txtTrnClsfCd1=98`
- 출발역은 일부 흐름에서 `0501`로 고정된다.

## OSrcar FieldMap 구조

근거: `network/data/reservation/old/OSrcar.java`, `ui/inquiry/rir/orr/a.java`.

| Setter | 생성 key | 설명 |
|---|---|---|
| `setSrcarCnt(1, v)` | `txtSrcarCnt` | 1번 여정 선택 객차/좌석 수. |
| `setSrcarCnt(n != 1, v)` | `txtSrcarCnt1` | 2번 여정 선택 객차/좌석 수. |
| `setSrcarNo(1, j, v)` | `txtSrcarNo{j}` | 1번 여정 j번째 선택 객차 번호. |
| `setSrcarNo(n != 1, j, v)` | `txtSrcarNo1_{j}` | 2번 여정 j번째 선택 객차 번호. |
| `setSeatNo(1, j, v)` | `txtSeatNo{j}` | 1번 여정 j번째 선택 좌석 번호. |
| `setSeatNo(n != 1, j, v)` | `txtSeatNo1_{j}` | 2번 여정 j번째 선택 좌석 번호. |

선택 좌석 검증 로직은 `OSrcar`가 비어 있으면 그대로 예약을 진행한다. 비어 있지 않은데 `txtSrcarCnt`와 `txtSrcarCnt1` 중 한쪽만 있는 상태면 선택 좌석 경고 다이얼로그를 표시한 뒤 사용자가 확인하면 선택을 초기화하고 예약을 진행한다.

## 할인/인증 DAO와 응답 필드

### 장애인 인증 확인

`DisabledCertificationDao` -> `CertificationService.disabledCertification()`

요청:

- `regNum`: 주민등록번호 입력값.
- `hdcpGrade`: `ReservationResponse.PsgDiscAddInfo.h_duty_ref_rcgn_ps_dv_cd`에서 온 장애/인정 구분 코드.
- `position`: 네트워크 전송 필드는 아니고 UI row 위치 추적용.

응답 `DisabledCertificationResponse`:

- `btdt`
- `certificate`
- `hdcpTpCd`
- `subtDcsClCd`
- 공통 `h_msg_cd`, `h_msg_txt`, `strResult`

성공 시 UI는 해당 row에 `BIRTH_DAY=btdt`, `SUITABILITY_RATING_CODE=subtDcsClCd`, `CERTIFICATION_MESSAGE=h_msg_txt`를 저장한다. 실패 시 row 상태만 실패로 바꾼다.

### 장애인 할인 적용

`ApplyDisabilityCertificationDao` -> `CertificationService.applyDisabilityCertification()`

요청:

- `hidPnrNo`
- `txtPsgDisc0019Cnt`
- `txtPsgDisc0019Sqno_{i}`: 승객 순번. 타입은 `Integer`.
- `txtJobDvCd0019_{i}`: 코드상 `"1"`로 세팅.
- `txtPsgDisc0019PsDvCd_{i}`: 장애/인정 구분 코드.
- `txtPsgDisc0019CustNm_{i}`: 코드상 빈 문자열로 세팅.
- `txtPsgDisc0019Birth_{i}`: 장애인 인증 응답의 `btdt`.
- `txtPsgDisc0019Grade_{i}`: 장애인 인증 응답의 `subtDcsClCd`.

정적 코드상 `DisabilityCertificationActivity.t0()`에는 `txtJobDvCd0019` map에 birth/grade key를 put하는 디컴파일 결과가 보인다. 실제 의도는 별도 map인 `txtPsgDisc0019Birth`, `txtPsgDisc0019Grade`로 넘기는 구조이지만, 이 문서는 디컴파일된 코드와 DAO 필드 구조를 구분해 기록한다.

### 국가유공자/무임 인증

`MeritCertDao` -> `CertificationService.certMerit()`

요청:

- `txtFreeDiscCertNo`
- `txtAcptPwd`
- `txtJuminNo7`
- `txtAbrdDt`

응답 `MeritCertResponse`:

- `h_free_acm_use_tno`
- `h_free_disc_cert_no`
- `h_free_psb_tno`
- 공통 응답 필드

### 국회의원 인증

`CongresspersonCertDao` -> `CertificationService.certCongressperson()`

요청:

- `freeDiscCertNo`
- `certNo`
- `abrdDt`
- `viewIndex`: UI 추적용이며 전송되지 않는다.

응답 `CongresspersonCertResponse`:

- `freeDiscCertNo`
- 공통 응답 필드

### 정부/공무원 PBEP 인증

`GovernmentCertificationActivity`에서 2단계로 수행한다.

1. `GovernmentCertificationStep1Dao` -> `/classes/com.korail.mobile.pbep.toknCre.do`
   - Query: `Device`, `Version`
   - 응답: `app`, `csrfToken`
   - `app` JSON에서 `sp_did`, `service_code`, `callback_url`, `nonce`, `encrypt_type`, `sessionId`를 읽어 `bmc://verify_vp?...` URI를 만들고 `kr.go.id.bmc.VERIFY_VP` intent를 실행한다.
2. 외부 앱 결과 `result=true`이면 `GovernmentCertificationStep2Dao` -> `/classes/com.korail.mobile.pbep.sttChck.do`
   - Query: `Device`, `Version`, `csrfToken`
   - 응답: `code`, `message`, `result`, `txCompleteCode`, `pbepInfo`
   - 성공 수신 시 `pbepInfo`를 저장하고 확인 버튼을 활성화한다.

`DirectInquiryActivity`는 공무원 인증이 필요한 조건에서 `GovernmentCertificationActivity`를 띄운 뒤, 결과 intent의 `PBEP_INFO`를 `ReservationRequest.pbepInfo`에 넣어 회원 예약 endpoint로 보낸다.

### 할인 금액 재계산

`DiscountPriceDao` -> `/classes/com.korail.mobile.certification.PriceReCalculation`

요청:

- `hidPnrNo`
- `txtJobId`
- `hiduserYn`
- `hidCustNo`
- `txtPsgGridcnt`
- list field: `psg_tp_dv_cd`
- list field: `hidDcntKndCd`
- list field: `dcnt_knd_cd1`
- list field: `hidDscpNo`
- list field: `psrm_cl_cd`
- list field: `hidFmlyNo`

`DiscountPriceParams`는 한 승객/행 단위의 `psg_tp_dv_cd`, `hidDcntKndCd`, `dcnt_knd_cd1`, `hidDscpNo`, `psrm_cl_cd`, `hidFmlyNo` 값을 담는 데이터 객체다. Retrofit 1의 `@Field List<String>`가 같은 field명을 반복 form field로 직렬화하는 구조로 해석된다.

응답은 `ReservationResponse`이며 실제 서버 응답 예시는 이 문서에서 만들지 않는다.

## ReservationResponse 필드

`ReservationResponse extends BaseResponse`.

상위 필드:

| 필드 | 사용처/의미 |
|---|---|
| `h_pnr_no` | 예약 PNR. 결제, 예약취소, 예약대기, 리무진 연계에 사용. |
| `h_jrny_cnt` | 여정 수. 예약취소/예약대기/리무진 후속 처리에 사용. |
| `h_wct_no` | 결제 요청의 `wctNo`. |
| `h_tmp_job_sqno1`, `h_tmp_job_sqno2` | 결제 요청 job sequence. |
| `h_payment_flg`, `h_payment_msg`, `h_pay_limit_msg` | 결제 가능/안내 메시지. |
| `h_tot_fare`, `h_tot_prc`, `h_tot_rcvd_amt`, `h_tot_dcnt_amt`, `h_sprm_fare` | 운임/금액/할인 관련 필드. |
| `h_ntisu_lmt`, `h_ntisu_lmt_dt`, `h_ntisu_lmt_tm` | 발권/미발권 제한 관련 필드. |
| `h_ise_psb_dt`, `h_ise_psb_tm` | 발권 가능 일시 계열. |
| `h_add_srv_flg` | 부가서비스 여부. 예약 확인 화면에서 추가 서비스 흐름 분기에 사용. |
| `h_cust_mg_no` | 비회원 예약 후 `nonMemberNumber`로 저장. |
| `h_pre_stl_tgt_flg` | 선결제/사전결제 대상 플래그로 보이는 필드. |
| `h_fmly_info_cfm_flg` | 가족 정보 확인 플래그. |
| `h_hdcp_ctfc_num` | 장애 인증 수. |
| `h_msg_mndry`, `h_msg_txt5` | 추가 메시지 필드. |
| `ogtkRcvdAmt`, `scnIndcAmt`, `totRetAmt` | 원권/화면 표시/반환 금액 계열 정수 필드. |

중첩 구조:

- `jrny_infos.jrny_info[]`
  - `h_jrny_sqno`, `h_jrny_tp_cd`, `h_rsv_chg_no`
  - `h_dpt_dt`, `h_dpt_tm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`, `h_dpt_stn_cons_ordr`
  - `h_arv_tm`, `h_arv_rs_stn_cd`, `h_arv_rs_stn_nm`, `h_arv_stn_cons_ordr`
  - `h_trn_no`, `h_trn_clsf_cd`, `h_trn_clsf_nm`, `h_stlb_trn_clsf_cd`, `h_trn_gp_cd`
  - `h_seat_cnt`, `h_tot_seat_cnt`, `h_tot_stnd_cnt`, `h_fres_cnt`
  - `lumpStlTgtNo`
  - `seat_infos`
- `seat_infos.seat_info[]`
  - `h_srcar_no`, `h_seat_no`, `h_sgr_nm`
  - `h_psrm_cl_cd`, `h_psrm_cl_nm`
  - `h_rq_seat_att_cd`, `h_dir_seat_att_cd`
  - `h_psg_tp_cd`
  - `h_seat_fare`, `h_seat_prc`, `h_rcvd_amt`
  - `h_dcnt_knd_cd1` ... `h_dcnt_knd_cd5`
  - `dcnt_reld_no`
- `psg_infos.psg_info[]`
  - `h_psg_tp_cd`, `h_psg_info_per_prnb`
  - `h_dcnt_knd_cd`, `h_dcnt_knd_cd2`
  - `h_dcsp_no`, `h_dcsp_no2`
  - `dlayOgtkWctNo`, `dlayOgtkSaleDt`, `dlayOgtkSaleSqno`, `dlayOgtkRetPwd`
- `psgDiscAdd_infos.psgDiscAdd_info[]`
  - `h_psg_sqno`
  - `h_duty_ref_rcgn_ps_dv_cd`
  - 이 목록이 비어 있지 않으면 장애인 인증 화면으로 이동한다.
- `dfpyList[]`
  - `dfpyNo`, `dfpySrtCd`, `dscpMgNo`, `stlAmt`
- `stopStnList[]`
  - `pnrNo`
- `tkList[]`
  - `saleWctNo`

## 예약 로직 규칙

### 기본 예약 생성

`W4.a.getOReservationRequest()`는 기본 예약 요청을 만든다.

- `txtMenuId`: 기본 `"11"`.
- `txtJobId`: `"1101"`.
- `hidFreeFlg`: `"N"`.
- `txtStndFlg`: `"N"`.
- `txtGdNo`: 기본 빈 문자열.
- `OPsg`: 승객 그룹별 인원/유형/할인 코드를 고정 순서로 채움.
- `OSeat`: 좌석 속성 1~5와 `txtPsrmClCd1`을 채움.
- 여정(`OJrny`)은 조회 화면이나 리무진 화면에서 출발/도착/열차 정보를 추가로 채운다.

### 예약 버튼 분기

`DirectInquiryActivity`:

- 일반 예약 버튼은 현재 `txtJobId`를 유지한다. 버튼 tag가 `"1202"`이면 `txtJobId="1202"`로 바꾸고 입석+좌석 예약으로 처리한다.
- 예약대기 버튼은 `txtJobId="1102"`를 세팅하고 NetFunnel `service_1` / `act_14`를 거쳐 예약 요청을 수행한다.
- 공무원 PBEP 인증 조건이 만족되면 예약 전 `GovernmentCertificationActivity`를 먼저 띄우고, 결과 `PBEP_INFO`를 `ReservationRequest.pbepInfo`에 저장한다.

NetFunnel 상수:

| 상수 | 값 | 사용 |
|---|---|---|
| `NETFUNNEL_SERVER_ID` | `service_1` | NetFunnel service id |
| `NETFUNNEL_ACTION_RESERVE_ID` | `act_14` | 예약/예약대기 시작 전 사용 |
| `NETFUNNEL_ACTION_PAY_ID` | `act_18` | 결제 |
| `NETFUNNEL_ACTION_RESERVED_ID` | `act_21` | 예약 내역 |

### 비회원 예약 제한

`ReservationRequest.isNonmemberNotEnable()`은 true 조건을 네 가지로 둔다.

- `txtMenuId == "41"`
- `txtJobId == "1102"`
- `txtSeatAttCd4` 또는 `txtSeatAttCd4_1`이 `J.isSpecialRoom()` 기준 특실
- 내부 플래그 `isNotNonMemberShow == true`

`DirectInquiryActivity.f3()`는 예약 실행 직전 `isNotNonMemberShow`를 `C0() == RSV_GOING || F0()`으로 세팅한다. 즉 왕복 가는편 또는 리무진 연계 흐름에서는 비회원 표시/허용이 제한될 수 있다.

### 예약 응답 후 분기

`ui/inquiry/rir/orr/a.java`의 `O0(ReservationResponse)`:

- `psgDiscAdd_infos.psgDiscAdd_info`가 비어 있지 않으면 `DisabilityCertificationActivity`로 이동한다.
- `h_msg_cd == "IRR000014"`이면 `ReservationWaitActivity`로 이동한다.
- 로그인 상태이면 `L2()`로 예약 확인/왕복/리무진 연계 분기를 탄다.
- 비로그인 상태이면 `h_cust_mg_no`를 비회원 번호로 저장하고 예약 확인으로 이동한다.

`L2()`:

- 현재 여정이 `RSV_GOING`이면 가는편 예약 성공 dialog 후 오는편 조회로 넘어간다.
- 현재 여정이 `RSV_INCOMING`이거나 응답 여정이 리무진이면 예약 확인으로 이동하고 일부 경우 현재 화면을 종료한다.
- 리무진 연계가 아니고 `h_msg_cd == "IRT800005"`이면 서버 메시지를 dialog로 보여준 뒤 확인 시 예약 확인으로 이동한다.
- 리무진 연계이면 기존 예약 응답의 `h_pnr_no`를 넣고 `txtJobId="1101"`, `hidFreeFlg="N"`, `txtStndFlg="N"`, `OJrny.txtTrnClsfCd1="98"`, `OJrny.txtTrnGpCd1=LIMOUSINE`으로 새 `LReservationDao` 요청을 수행한다.

### 예약 오류 처리

`DirectInquiryActivity.f3()`와 `a.E2()`는 다음 메시지 코드를 기본 오류 dialog에서 숨김 목록에 넣는다.

- `WRR800029`
- `ERR911531`
- `ERR911051`

상위 `A5.k.onReceiveError()`는 예약 계열 DAO(`dao_reservation`, `dao_l_reservation`, `dao_seat_assign_reservation`)에서 다음을 별도 처리한다.

- `WRR800029`, `ERR911531`, `ERR911051`: 서버 오류 메시지로 확인 dialog 표시.
- `ERR911081`: 좌석 불가 시간 안내 dialog 표시.

Base 공통 오류:

- `FAIL` 또는 `WRC000288`: `h_msg_txt` 기반 오류.
- `P058`: 자동 로그인 여부에 따라 로그인 관련 예외 클래스로 처리.
- `SUPDATE`: 업데이트 dialog.
- `SEMGTK`: 공통 오류 예외 처리.
- 403 + `DynaPath-Result < 0`: body JSON `message`를 macro dialog로 표시.

## 예약대기

`ReservationWaitService.rsvWait()`:

| HTTP | Path | 요청 field | 응답 |
|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservationWait.ReservationWait` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtPsrmClChgFlg`, `txtSmsSndFlg`, `txtCpNo` | `BaseResponse` |

`ReservationWaitActivity` 진입 조건은 예약 응답 `h_msg_cd == "IRR000014"`이다.

요청 생성:

- `txtPnrNo`: `ReservationResponse.h_pnr_no`
- `txtPsrmClChgFlg`: UI의 “객실등급 변경 동의” 체크 여부. 체크 시 `"Y"`, 미체크 시 `"N"`.
- `txtSmsSndFlg`: SMS 알림 체크 여부. 체크 시 `"Y"`, 미체크 시 `"N"`.
- `txtCpNo`: SMS 체크 시 입력된 휴대폰 번호 3칸을 이어 붙인 값. 길이가 10 미만이면 요청하지 않고 경고 dialog를 표시한다.

취소 관련:

- 예약대기 화면의 취소 버튼은 `RsvCancelDao`로 `ReservationCancel`을 호출한다.
- `txtJrnySqno`는 `"0001"`, `hidRsvChgNo`는 `"000"`으로 세팅한다.
- 취소 응답 후 `RsvCancelCheckDao`로 `ReservationCancelChk`를 호출해 완료 dialog를 표시한다.

예약대기 성공 시 원래 `ReservationResponse`를 `DReservationConfirmActivity`로 넘기고 대기 안내 메시지를 붙인다. live response 본문은 정적으로 확인할 수 없어 예시를 작성하지 않았다.

## 버스/리무진 예약 연계

이 APK의 `BusReservationService`는 패키지상 certification 아래에 있으나 기능은 리무진/버스 좌석 조회와 변경/취소 확인에 가깝다.

### BusReservationService 엔드포인트

| HTTP | Path | Java method | 요청 field | 응답 |
|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `reservationCancelCheck` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` | `BaseResponse` |
| POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | `reservationChange` | `Device`, `Version`, `Key`, `pnrNo`, `chgTno`, `totPrnb`, `stndFlg`, `evntWctFlg`, `wctHndgCncDvCd`, `lrgCrgFlg`, `psgCnt`, `RJrny`, `RSrcar`, `RSeat`, `RPsg`, `RDscp` | `ReservationChangeResponse` |
| POST | `/classes/com.korail.mobile.lmu.scdlQry.do` | `reservationList` | `Device`, `Version`, `Key`, `dptDt`, `dptRsStnCd`, `arvRsStnCd`, `tmGpCd`, `psrmClCd`, `dptTm`, `trnNo`, `seatAttCd`, `rsvSaleDvCd` | `BusInquiryResponse` |
| POST | `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do` | `reservationSeatList` | `Device`, `Version`, `Key`, `trnClsfCd`, `trnGpCd`, `runDt`, `trnNo`, `srcarNo`, `psrmClCd`, `dptRsStnCd`, `arvRsStnCd`, `seatAttCd`, `dptStnRunOrdr`, `arvStnRunOrdr`, `totPsgCnt`, `gdNo`, `isArrow` | `SeatListResponse` |

`BusReservationListDao.executeDao()`의 디컴파일 결과는 `reservationList()`를 한 번 호출한 뒤 같은 호출을 다시 return한다. 이 문서는 정적 디컴파일 결과만 기록하며 실제 런타임 중복 호출 여부는 네트워크 캡처 없이 단정하지 않는다.

### BusInquiryResponse

- `fllwPgExt`
- `lgtmShtmDvCd`
- `trainList[]`
  - `dptDt`, `dptTm`, `dptRsStnCd`, `dptStnRunOrdr`
  - `arvDt`, `arvTm`, `arvRsStnCd`, `arvStnRunOrdr`
  - `runDt`
  - `trnNo`, `trnGpCd`, `trnOrdNo`, `stlbTrnClsfCd`
  - `gnrmRestSeatNum`, `sprmRestSeatNum`, `restFresNum`, `restStndNum`
  - `chtnDvCd`, `ocurDlayTnum`, `ymsAplFlg`

### SeatListResponse

- `car_tp_cd`
- `scar_no`
- `seat_ary_cd`
- `up_dn_dv_cd`
- `seatList[]`
  - `seat_no`, `sqr_no`, `seat_spec`
  - `rq_seat_att_cd`, `dir_seat_att_cd`, `etc_seat_att_cd`
  - `sale_psb_flg`
  - `intg_msg`, `intg_msg_cd`, `vz_msg_dv_cd`
  - UI 내부 상태: `isDisable`, `isSelected`

### 리무진 예약 요청

`LimousineActivity`와 `LimousineSelectSeatActivity`는 `LReservationDao extends ReservationDao`를 사용한다. 따라서 최종 예약 호출은 `CertificationService.TicketReservation` 또는 `NonMemTicket` 분기를 그대로 탄다.

`LimousineActivity.D0()`:

- `W4.a.getOReservationRequest()`로 기본 `ReservationRequest`를 만든다.
- `OJrny`에 `txtJrnyCnt=1`, `txtJrnyTpCd1=11`, `txtTrnGpCd1=LIMOUSINE`, `txtTrnClsfCd1=98`, `txtDptRsStnCd1=0501`, 도착역/일자/시간을 넣는다.
- `LReservationDao`로 예약한다.

`LimousineSelectSeatActivity.y0()`:

- 좌석 조회는 `BusReservationSeatListDao`로 수행한다.
- 선택 좌석 예약 시 `OJrny`에 열차번호, 운행일, 출발/도착역 순서, `txtSrcarCnt`, `txtSrcarNo{i}`, `txtSeatNo{i}`를 추가한다.
- `srcarNo`는 선택 좌석별 `"0001"`로 세팅한다.
- 예약 성공 후 수수료 안내 dialog를 보여주고 결제로 이동하거나 취소를 수행한다.

리무진 결제 이동 시 `ReservationResponse`에서 다음 값을 `RsvPaymentRequest`로 옮긴다.

- `hidPnrNo = h_pnr_no`
- `wctNo = h_wct_no`
- `jobSqNo1 = h_tmp_job_sqno1`
- `jobSqNo2 = h_tmp_job_sqno2`
- `hidRsvChgNo = jrny_infos.jrny_info[0].h_rsv_chg_no`

## 콜백/화면 흐름 요약

| 단계 | 클래스 | 콜백/메서드 | 동작 |
|---|---|---|---|
| DAO 실행 | `BaseActivity.executeDao()` | `BaseDaoHelper.executeDao()` | DAO에 base/result callback을 설정하고 `AsyncTask` 실행. |
| 네트워크 호출 | `BaseDaoHelper.HttpTask` | `doInBackground()` | `iBaseDao.executeDao()` 호출, `RetrofitError`/DynaPath 처리. |
| 공통 결과 | `BaseActivity` | `onIntegrationResult()` | 공통 오류 판정 후 `base.onReceive()` 또는 `base.onReceiveError()`. |
| 일반 예약 결과 | `C5.a` / `A5.k` 계열 | `onReceive()` | `dao_reservation`, `dao_l_reservation`, `dao_seat_assign_reservation`를 `ReservationResponse`로 처리. |
| 장애인 인증 필요 | `ui/inquiry/rir/orr/a.O0()` | `startActivityForResult(..., 112)` | `DisabilityCertificationActivity` 호출. |
| 장애인 인증 완료 | `A5.k.onActivityResult()` | request code `112` | 원 예약 응답을 다시 `O0()` 경로로 처리. |
| 정부 인증 완료 | `DirectInquiryActivity.onActivityResult()` | request code `129` | `PBEP_INFO`를 `ReservationRequest.pbepInfo`에 저장. |
| 예약대기 필요 | `ui/inquiry/rir/orr/a.O0()` | `h_msg_cd == IRR000014` | `ReservationWaitActivity` 호출. |
| 리무진 좌석 조회 | `LimousineSelectSeatActivity.onReceive()` | `dao_bus_reservation_seat_list` | 좌석 목록 UI 갱신. |
| 리무진 예약 성공 | `Limousine*Activity.onReceive()` | `dao_l_reservation` | 수수료 안내 후 결제 이동 또는 예약취소. |

## 정적 분석 한계

- 서버가 실제로 반환하는 JSON 예시는 확인하지 않았다.
- 필드 의미는 Java field명, setter/getter명, UI 사용처에서 추론 가능한 범위까지만 적었다.
- 난독화된 enum/유틸의 일부 값은 코드에서 직접 확인된 값만 기록했다.
- Retrofit 1의 list field 직렬화 방식은 라이브 트래픽 없이 코드 구조 기준으로만 해석했다.

## 20-agent follow-up audit 보강

- 근거 소스에는 `docs/deep-dive/api-contracts.md`도 포함한다. endpoint별 request/return type mirror는 해당 문서를 canonical generated contract로 둔다.
- normal direct/transfer train-to-`ReservationRequest` mapper로 `analysis/jadx/sources/C5/a.java`를 추가한다. `C5.a.N0()`는 `OJrny`와 `OSeat`를 채우고 `OSrcar`를 비우는 경로를 만든다.
- 비회원 일반 예약 flow는 `moveToLogin(... !isNonmemberNotEnable ...)` 이후 `onNonMemberLoginSuccess()`가 request를 clone하고 `x2()`에서 `txtCustNm`, `txtCpNo`, `txtCustPw`를 채운다.
- `PBEP_INFO`는 `onActivityResult()`에서 저장되고, 다음 회원 예약 호출의 `pbepInfo` 필드로 포함된다.
