# 05. 열차 조회/운행일정/요금/좌석도 정적 분석

분석 범위는 APK decompile 산출물 `analysis/jadx/sources` 기준의 `SeatMovieService`, `TrainInquiryDao`, `CalendarService`/`TrainCalendarDao`, `TrainsInfoService`, 그리고 `ResearchService` 중 열차 조회/검색/스케줄/요금/좌석도에 직접 연결되는 부분이다. 실제 운영 서버 호출이나 동적 트래픽 캡처는 수행하지 않았다. 따라서 응답 필드의 실제 값, 코드값 의미, 서버 검증 규칙은 소스에서 명시된 경우를 제외하고 모두 **unknown**으로 둔다.

## 공통 네트워크 규칙

- Retrofit 1 기반이며, `ExecuteDao.getRestAdapterBuilder()`가 `S4.z.getSSLHost()`를 endpoint로 사용한다. 연결/읽기 timeout은 각각 60초다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:18-24`, `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:59-64`.
- 공통 request 기본값은 `BaseRequest` 생성자에서 `Device=AD`, `Version=250601003`, `Key=korail1234567890`로 채워진다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:6-18`.
- 공통 response 필드는 `BaseResponse.h_msg_cd`, `BaseResponse.h_msg_txt`, `BaseResponse.strResult`다. 성공/실패 문자열 상수는 `SUCC`/`FAIL`이지만, 각 endpoint가 실제로 어떤 값을 반환하는지는 **unknown**이다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:7-30`.
- DAO 실행은 `BaseDaoHelper.HttpTask`가 `executeDao()`를 호출하고, 응답 후 `onIntegrationResult()`로 UI에 전달한다. `NetfunnelDao`가 붙어 있으면 응답 후 NetFunnel dialog를 닫고 runner를 실행한다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:43-47`, `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101-109`, `analysis/jadx/sources/com/korail/talk/network/NetfunnelDao.java:23-45`.

## Sid 생성

`Sid`는 클라이언트에서 매 호출 시 생성된다.

- 생성 함수: `S4.C0812l.getSid()`
- 평문: `"AD" + 현재 epoch milliseconds`
- key: `2485dd54d9deaa36`
- 알고리즘: `AES/CBC/PKCS5Padding`
- IV: key 문자열의 앞 16자, 이 APK에서는 key 전체와 동일한 16자
- 출력: Android `Base64.encode(..., 0)` 결과 문자열
- 실패 시 빈 문자열

근거: `analysis/jadx/sources/S4/C0812l.java:18-23`, `analysis/jadx/sources/S4/C0812l.java:43-49`.

`Sid`가 붙는 in-scope endpoint는 일반 열차 조회, 리무진 열차 조회, 좌석도 객차 목록, 좌석도 좌석 목록이다. `ScheduleViewSpecial`은 DynaPath 대상 URL이지만 Retrofit signature에는 `Sid` 필드가 없다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20-22`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/ProductTrainInquiryDao.java:10-13`.

## NetFunnel 및 DynaPath

### NetFunnel

상수는 `service_1`, 일반 조회 `act_8`, 성수기 조회 `act_8_2`, 상품 조회 `act_6`, 예약 `act_14`, 결제 `act_18` 등으로 정의되어 있다. 근거: `analysis/jadx/sources/K4/g.java:43-51`.

열차 조회 화면의 공통 controller는 일반/상품/4인동반석 조회에서 날짜가 성수기이면 `act_8_2`, 상품 요청이면 `act_6`, 그 외에는 `act_8`을 선택해 `T6.g.BEGIN()`을 호출한다. NetFunnel 완료 후 `TrainInquiryDao` 또는 `ProductTrainInquiryDao`를 실행한다. 근거: `analysis/jadx/sources/B5/c.java:101-113`, `analysis/jadx/sources/B5/c.java:430-450`.

메인 화면의 “간편구매” 흐름도 출발일 기준 성수기 여부로 `act_8`/`act_8_2`를 선택한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:745-762`, `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java:319-331`.

좌석도 객차/좌석 목록, 운행일정, 요금 조회는 현재 확인한 UI 호출 경로에서 별도 NetFunnel 시작 코드가 보이지 않는다. 실제 서버 또는 다른 진입점의 큐 적용 여부는 **unknown**이다.

### DynaPath

`I4.a.IS_MACRO_ACTIVE`가 true이면 `ExecuteDao`가 URL substring을 검사해 `x-dynapath-m-token` header를 추가한다. in-scope 대상은 다음이다.

- `/classes/com.korail.mobile.seatMovie.ScheduleView`
- `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
- `/classes/com.korail.mobile.trn.prcFare.do`

`LimousineScheduleView`, `TrainResearch`, `TResidualSeatsResearch`, `TrainCharge`, `actualTrainSchedule`, `schedule.runDt`는 정적 URL 목록에 포함되지 않았다. 근거: `analysis/jadx/sources/com/korail/talk/network/ExecuteDao.java:25-48`.

403 Forbidden 응답에서 `DynaPath-Result` header가 있고 값이 음수이면 body JSON의 `message`를 macro dialog message로 저장한다. 실제 message 값은 **unknown**이다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:54-91`.

## UI/DAO 전체 흐름

1. `IntroActivity` 시작 중 `TrainCalendarDao`를 호출해 운행 가능일 calendar를 가져오고 `C0805e.makeAvailableDatesFactory()`에 전달한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:457-460`, `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java:781-783`.
2. 메인 예약 화면은 `U4.b.getRsvInquiryRequest()`로 `TrainInquiryRequest[]`를 만든다. 왕복이면 2개, 편도면 1개다. 신 UI는 인접역 조회, SRT 포함, 왕복 여부, 회원번호를 추가한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/MainBookingActivity.java:764-785`.
3. 구 메인 화면은 동일 helper를 쓰며 SRT intent 데이터가 있으면 `txtGoTrnNo`를 지정한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/booking/mainBooking/OldMainBookingActivity.java:339-373`.
4. 상품/특가 예약 화면은 `ProductTrainInquiryRequest`를 만들고 `txtGdNo`를 추가한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java:138-143`.
5. 리무진 연계 화면은 `TrainInquiryRequest`를 만들지만 DAO는 `LimousineTrainInquiryDao` 경로를 사용한다. request assembly는 동일 helper를 사용한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/limousine/RenewalLimousineActivity.java:228-235`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/LimousineTrainInquiryDao.java:11-14`.
6. 열차 조회 결과 화면 controller는 NetFunnel 완료 후 request 타입이 `ProductTrainInquiryRequest`이면 `ProductTrainInquiryDao`, 아니면 `TrainInquiryDao`를 실행한다. 근거: `analysis/jadx/sources/B5/c.java:101-113`.
7. 결과 화면에서 운임 버튼은 `PriceFareActivity`로 이동하고 `Price2FareDao`를 호출한다. 단일 여정은 한 열차의 필드를 그대로 넣고, 환승은 두 열차의 필드를 comma-join 한다. 근거: `analysis/jadx/sources/A5/u.java:276-283`, `analysis/jadx/sources/com/korail/talk/ui/price/PriceFareActivity.java:54-76`, `analysis/jadx/sources/com/korail/talk/ui/price/PriceFareActivity.java:79-99`.
8. 결과 화면에서 열차 운행정보 버튼은 `TrainServiceInfoWebViewActivity`로 이동하고 `TrainScheduleDao`를 호출한다. 열차번호는 5자리 zero-padding한다. 근거: `analysis/jadx/sources/A5/u.java:286-289`, `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java:143-151`.
9. 좌석도는 `SeatSearchActivity`가 intent의 `SeatSearchRequest`를 받아 먼저 `SearchCarListDao`, 객차 선택 후 `SearchSeatListDao`를 호출한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:349-354`, `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:621-625`, `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:201-213`.

## 요청 조립 및 검증/변환

### `U4.b.getRsvInquiryRequest()` 기본 조립

`RsvInquiryRequest` 공통 필드는 다음 방식으로 채워진다.

- `txtMenuId`: 호출자가 넘긴 menu id. 일반 메인은 `"11"`, 상품은 `"41"` 등이다. 실제 메뉴 의미는 일부만 소스상 추정 가능하며 전체 의미는 **unknown**.
- `radJobId`: 호출자가 넘긴 job id. 직접/환승 구분 또는 예약 작업 코드로 보이나 실제 서버 의미는 **unknown**.
- `selGoTrain`, `txtTrnGpCd`: `O.getTrainGroupCode(context)`.
- `txtSeatAttCd_2`: `K4.l.DEFAULT.getCode()`.
- `txtSeatAttCd_3`: `K4.n.DEFAULT.getCode()`.
- `txtSeatAttCd_4`: 호출자가 넘긴 seat type.
- `txtGoStart`, `txtGoEnd`: 첫 번째 request는 출발역/도착역, 두 번째 request는 왕복용으로 역을 뒤집는다.
- `txtGoAbrdDt`, `txtGoHour`: 선택일이 오늘보다 과거이면 오늘로 보정하고, 아니면 선택일을 사용한다. `CalendarData`가 직접 넘어오면 그 값을 우선 사용한다.
- `txtPsgFlg_1`: 성인 + 청소년 + 안내견
- `txtPsgFlg_2`: 어린이 + 유아동반
- `txtPsgFlg_3`: 경로
- `txtPsgFlg_4`: 중증장애
- `txtPsgFlg_5`: 경증장애
- 내부 client-only 보조값: `adultCount`, `totalCount`

근거: `analysis/jadx/sources/U4/b.java:110-183`.

### 조회 페이징/다음 조회

`RsvInquiryRequest.setNextStartTime()`은 마지막 열차의 `h_chg_trn_seq`가 직접 여정 코드와 같으면 마지막 열차의 `h_dpt_tm`, 아니면 끝에서 두 번째 열차의 `h_dpt_tm`을 다음 조회 시작시각으로 설정한다. 실제 서버 페이지 토큰 의미는 **unknown**이다. 근거: `analysis/jadx/sources/com/korail/talk/network/request/inquiry/RsvInquiryRequest.java:164-172`.

결과 화면 controller는 스크롤 끝, 다음/이전 동작 등에서 `qryStNo`, `qryStTrnNo`, `qryStTrnNo2`, `pgPrCnt`를 조정한다. 근거: `analysis/jadx/sources/B5/c.java:180-199`.

### 좌석도 선택 검증

- 좌석도 대상 여부는 결과 열차의 `h_rd_seat_map_flg` 문자와 일반/특실 예약 코드로 판단한다. `h_rd_seat_map_flg`의 실제 값 의미는 `N` 외에는 **unknown**이다. 근거: `analysis/jadx/sources/A5/u.java:315-330`.
- 좌석도 화면은 `SearchCarListDao` 응답의 추천 객차 `h_rcmd_srcar_no`를 기본 선택하고, 기존 좌석변경 문맥에서는 기존 객차가 목록에 있으면 우선한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:220-244`.
- 좌석 목록에서 `sale_psb_flg == "Y"`인 좌석만 enabled 처리한다. `etc_seat_att_cd != "000"`은 빈칸, `rq_seat_att_cd == "999"`는 방향 화살표로 처리한다. 근거: `analysis/jadx/sources/X4/a.java:8-18`, `analysis/jadx/sources/l6/f.java:30-37`, `analysis/jadx/sources/l6/f.java:44-80`.
- 선택 가능 최대 좌석 수는 일반적으로 총 승객 수이고, 온돌 좌석 속성이면 6으로 고정한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:273-278`.
- 선택 완료 버튼은 선택 수가 요구 수와 같을 때만 enabled 된다. 근거: `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:877-907`.
- 완료 시 caller type에 따라 `tss_srcar_no`/`tss_seat_no`, `RSrcar`, `OSrcar` map으로 객차/좌석번호를 반환한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:648-691`.

## Endpoint 상세

### 1. 일반 열차 조회

- Service: `SeatMovieService.getRsvInquiry`
- HTTP: `POST /classes/com.korail.mobile.seatMovie.ScheduleView`
- Request encoding: form-url-encoded fields
- Response: `RsvInquiryResponse`
- DynaPath: involved when macro flag is active
- NetFunnel: UI flow에서 `act_8` 또는 `act_8_2`
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12-14`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java:11-14`

Request fields:

| Field | Source getter / assembly | Notes |
|---|---|---|
| `Device` | `getDevice()` | 기본 `AD` |
| `Version` | `getVersion()` | 기본 `250601003` |
| `Sid` | `C0812l.getSid()` | AES/Base64 Sid |
| `txtMenuId` | `getTxtMenuId()` | 일반 메인 `"11"` 확인, 기타 의미 unknown |
| `radJobId` | `getRadJobId()` | job/직통환승 관련 코드, 실제 의미 unknown |
| `selGoTrain` | `getSelGoTrain()` | 열차군 필터 |
| `trnGpCd` | `getTxtTrnGpCd()` | 열차그룹 코드 |
| `trainNo` | `getTxtGoTrnNo()` | SRT 연동 시 지정 가능 |
| `txtGoStart` | `getTxtGoStart()` | 출발역명 |
| `txtGoEnd` | `getTxtGoEnd()` | 도착역명 |
| `txtGoAbrdDt` | `getTxtGoAbrdDt()` | `yyyyMMdd` 형식으로 보임 |
| `txtGoHour` | `getTxtGoHour()` | `HHmmss` 형식으로 보임 |
| `txtPsgFlg_1` | `getTxtPsgFlg_1()` | 성인+청소년+안내견 |
| `txtPsgFlg_2` | `getTxtPsgFlg_2()` | 어린이+유아동반 |
| `txtPsgFlg_3` | `getTxtPsgFlg_3()` | 경로 |
| `txtPsgFlg_4` | `getTxtPsgFlg_4()` | 중증장애 |
| `txtPsgFlg_5` | `getTxtPsgFlg_5()` | 경증장애 |
| `txtSeatAttCd_2` | `getTxtSeatAttCd_2()` | 좌석속성 2, 기본값 코드 의미 unknown |
| `txtSeatAttCd_3` | `getTxtSeatAttCd_3()` | 좌석속성 3, 기본값 코드 의미 unknown |
| `txtSeatAttCd_4` | `getTxtSeatAttCd_4()` | 사용자 seat type |
| `txtJobDv` | `getTxtJobDv()` | train inquiry extra, meaning unknown |
| `etrPath` | `getEtrPath()` | 유입 경로로 추정, meaning unknown |
| `tkDptDt` | `getTkDptDt()` | ticket-change/search context, meaning unknown |
| `tkDptTm` | `getTkDptTm()` | ticket-change/search context, meaning unknown |
| `tkTrnNo` | `getTkTrnNo()` | ticket-change/search context, meaning unknown |
| `ebizCrossCheck` | `getEbizCrossCheck()` | null이면 `N` |
| `srtCheckYn` | `getSrtCheckYn()` | null이면 `N` |
| `rtYn` | `getRtYn()` | 왕복이면 `Y`, null이면 `N` |
| `adjStnScdlOfrFlg` | `getAdjStnScdlOfrFlg()` | 인접역/특정 옵션. null이면 `N`, UI에서 `Y` 또는 `S` 가능 |
| `mbCrdNo` | `getMbCrdNo()` | 회원번호 |
| `tkPsrmClCd` | `getTkPsrmClCd()` | meaning unknown |
| `tkRcvdAmt` | `getTkRcvdAmt()` | meaning unknown |
| `qryDvCd` | `getQryDvCd()` | 페이징/조회구분, meaning unknown |
| `qryStNo` | `getQryStNo()` | 페이징/시작번호, meaning unknown |
| `qryStTrnNo` | `getQryStTrnNo()` | 페이징/열차번호, meaning unknown |
| `qryStTrnNo2` | `getQryStTrnNo2()` | 환승 페이징 보조, meaning unknown |
| `pgPrCnt` | `getPgPrCnt()` | page count, meaning unknown |
| `chtnCnt` | `getChtnCnt()` | 환승역 선택 시 `"1"` 설정 |
| `chtnRsStnCd1` | `getChtnRsStnCd()` | 환승역 코드 |
| `trnGpCnt` | `getTrnGpCnt()` | 환승 열차그룹 count, meaning unknown |
| `trnGpCd1` | `getTrnGpCd()` | 환승 열차그룹 코드 |

Response fields are `RsvInquiryResponse` plus common `BaseResponse`.

- Top-level: `h_ectb_trn_no_next`, `h_gd_no`, `h_next_pg_flg`, `h_notice_msg`, `h_prcd_trn_no_next`, `h_qry_st_no_next`, `h_rslt_cnt`, `h_trn_no_next`, `trn_infos`. 실제 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:8-18`, `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:471-504`.
- `trn_infos`: `h_merge_rsv_psb_flg`, `trn_info[]`. 실제 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:455-468`.
- `TrainInfo`: 출도착/운행/좌석/요금/예약가능/지연/할인/팝업 관련 다수 필드. 필드명은 `h_dpt_rs_stn_cd`, `h_arv_rs_stn_cd`, `h_dpt_dt`, `h_dpt_tm`, `h_run_dt`, `h_trn_no`, `h_trn_gp_cd`, `h_trn_clsf_cd`, `h_gen_rsv_cd`, `h_spe_rsv_cd`, `h_stnd_rsv_cd`, `h_free_sracar_cnt`, `h_rcvd_amt`, `h_rcvd_fare`, `h_rd_seat_map_flg`, `rcmdGdList`, `txtGdNo`, `totPsgCnt` 등이다. 실제 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:65-130`.
- `RcmdGdList`: `dcntAmt`, `dcntSurRt`, `famtPctDvCd`, `gdNm`, `gdNo`, `rcvdFare`, `rcvdPrc`, `rcvdPrc2`. 실제 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:19-63`.

### 2. 리무진 연계 열차 조회

- Service: `SeatMovieService.getRsvLimousineInquiry`
- HTTP: `POST /classes/com.korail.mobile.seatMovie.LimousineScheduleView`
- Response: `RsvInquiryResponse`
- DynaPath: static URL 목록에는 없음
- NetFunnel: 공통 조회 controller 경로를 쓰는지 실제 화면 연결은 일부만 확인, 적용 여부 **unknown**
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:16-18`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/LimousineTrainInquiryDao.java:11-14`

Request fields:

`Device`, `Version`, `Sid`, `txtMenuId`, `radJobId`, `txtJobDv`, `selGoTrain`, `trnGpCd`, `trainNo`, `txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, `txtPsgFlg_1` through `txtPsgFlg_5`, `txtSeatAttCd_2`, `txtSeatAttCd_3`, `txtSeatAttCd_4`, `ebizCrossCheck`, `srtCheckYn`, `rtYn`.

Response schema is the same `RsvInquiryResponse`; actual values are **unknown**.

### 3. 상품/특가 열차 조회

- Service: `SeatMovieService.getRsvProductInquiry`
- HTTP: `POST /classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
- Response: `RsvInquiryResponse`
- DynaPath: involved when macro flag is active
- NetFunnel: 상품 조회 `act_6`
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20-22`, `analysis/jadx/sources/com/korail/talk/network/dao/seatMovie/ProductTrainInquiryDao.java:10-13`

Request fields:

`Device`, `Version`, `txtMenuId`, `radJobId`, `selGoTrain`, `trnGpCd`, `txtGoStart`, `txtGoEnd`, `txtGoAbrdDt`, `txtGoHour`, `txtPsgFlg_1` through `txtPsgFlg_5`, `txtSeatAttCd_2`, `txtSeatAttCd_3`, `txtSeatAttCd_4`, `txtGdNo`, `qryDvCd`, `qryStNo`, `qryStTrnNo`, `qryStTrnNo2`, `pgPrCnt`, `chtnCnt`, `chtnRsStnCd1`, `trnGpCnt`, `trnGpCd1`.

`txtGdNo`는 상품 예약 화면에서 `ProductTrainInquiryRequest.setTxtGdNo()`로 설정한다. 실제 상품 번호 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/request/inquiry/ProductTrainInquiryRequest.java:6-15`, `analysis/jadx/sources/com/korail/talk/ui/booking/discountBooking/goods/DiscountGoodsBookingActivity.java:138-143`.

Response schema is `RsvInquiryResponse`; actual values are **unknown**.

### 4. 열차 운행 달력

- Service: `CalendarService.getTrainCalendar`
- HTTP: `GET /classes/com.korail.mobile.schedule.runDt`
- Request fields: 없음
- Response: `TrainCalendarDao.TrainCalendarResponse`
- DynaPath/NetFunnel: 없음
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/schedule/CalendarService.java:7-9`, `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:106-118`

Response fields:

- `runningCalendar[]`
- `RunningCalendar`: `aTrnOpFlg`, `bizDdStgCd`, `dTrnOpFlg`, `dayDvCd`, `gTrnOpFlg`, `hldyDvCd`, `oTrnOpFlg`, `runDt`, `sTrnOpFlg`, `saleDdDvCd`, `vTrnOpFlg`, `xTrnOpFlg`

Client transformations:

- `isForSaleDate()`는 `saleDdDvCd == "5"` 또는 `saleDdDvCd == StbkAcntDao.ACCOUNT_REGISTER`이면 true다. `ACCOUNT_REGISTER` 실제 문자열은 이 문서 범위에서 추적하지 않아 **unknown**이다.
- `isPeakSeason()`은 `bizDdStgCd == "5"`로 판단한다.
- 각 관광열차 가능 여부는 해당 `*TrnOpFlg == "Y"`로 판단한다.
- `isHoliday()`는 `hldyDvCd`가 empty가 아니면 true다.

근거: `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:13-31`, `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:44-82`, `analysis/jadx/sources/com/korail/talk/network/dao/schedule/TrainCalendarDao.java:101-103`.

### 5. 자유석 객차 안내

- Service: `TrainsInfoService.getFresScar`
- HTTP: `POST /classes/com.korail.mobile.trn.fresScar.do`
- Response: `FresScarDao.FresScarResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:20-22`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/FresScarDao.java:92-96`

Request fields: `Device`, `Version`, `Key`, `runDt`, `trnNo`, `dptStnConsOrdr`, `arvStnConsOrdr`, `dptStnRunOrdr`, `arvStnRunOrdr`.

Caller flow: 결과 화면에서 특정 열차의 자유석/객차 안내를 누르면 `TrainInfo`의 `h_run_dt`, `h_trn_no`, 출도착 구성/운행순서를 request에 복사한다. 근거: `analysis/jadx/sources/A5/u.java:292-302`.

Response fields: `fresCont`, `fresScarNo`, `fresTtl`. 실제 값은 **unknown**. UI는 `fresScarNo`를 기본 내용으로 보여주고, 특정 버튼 동작 시 `fresTtl`/`fresCont`를 추가 표시한다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/FresScarDao.java:71-89`, `analysis/jadx/sources/A5/u.java:909-927`.

### 6. 선택 열차 운임 재조회

- Service: `TrainsInfoService.getPrice2Fare`
- HTTP: `POST /classes/com.korail.mobile.trn.prcFare.do`
- Response: `Price2FareDao.Price2FareResponse`
- DynaPath: involved when macro flag is active
- NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:24-26`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:190-194`

Request fields:

- Fixed fields: `Device`, `Version`, `Key`, `txtMenuId`, `chtnDvCd`, `trnCnt`
- FieldMap `Price2FareParams`: `trnGpCd`, `stlbTrnClsfCd`, `dptRsStnCd`, `arvRsStnCd`, `runDt`, `trnNo`, `gdNo`, `rqSeatAttCd`

Caller transformations:

- 단일 여정은 첫 열차의 field를 그대로 넣는다.
- 환승은 두 열차의 `dptRsStnCd`, `arvRsStnCd`, `runDt`, `trnNo`, `gdNo`, `rqSeatAttCd`, `trnGpCd`, `stlbTrnClsfCd`를 comma-separated string으로 조립한다.
- `Price2FareRequest.setTrnCnt(String str)`는 decompiled Java 기준 `this.trnCnt = this.trnCnt;`라서 setter 인자가 저장되지 않는다. 이것이 decompiler artifact인지 실제 bytecode 동작인지는 **unknown**이며, 정적 Java-like source 기준으로는 `trnCnt`가 null일 수 있다.

근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:81-125`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:127-177`, `analysis/jadx/sources/com/korail/talk/ui/price/PriceFareActivity.java:54-99`.

Response fields:

- `prcList[]`
- `Price2Fare`: `jrnySqno`, `psrmClNm`, `rcvdFare`, `rcvdPrc`, `sumAmt`, `trnNo`

실제 금액/운임 값은 **unknown**. UI는 `psrmClNm`별 map을 만들고 `rcvdPrc`, `rcvdFare`, `sumAmt` 등을 fare dialog에 넣는다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:15-79`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:179-187`, `analysis/jadx/sources/com/korail/talk/ui/price/PriceFareActivity.java:111-139`.

### 7. 열차 요금표 조회

- Service: `TrainsInfoService.getPriceFare`
- HTTP: `POST /classes/com.korail.mobile.trainsInfo.TrainCharge`
- Response: `PriceFareDao.PriceFareResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:28-30`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java:179-183`

Request fields:

- Fixed fields: `Device`, `Version`, `Key`, `txtMenuId`, `txtRtnDvCd`, `txtChtrDvCd1`, `txtSeatAttCd4`
- FieldMap `PriceFareParams`: `txtTrnClsfCd1`, `txtDptRsStnCd1`, `txtArvRsStnCd1`, `txtRunDt1`, `txtTrnNo1`, `txtTrnGpCd1`, 또는 index 1일 때 `_1` suffix가 붙은 `txtTrnClsfCd1_1`, `txtDptRsStnCd1_1`, `txtArvRsStnCd1_1`, `txtRunDt1_1`, `txtTrnNo1_1`, `txtTrnGpCd1_1`.

Response fields:

- `prc_fare_list.jrny_info[].prc_fare[]`
- `PriceFare`: `h_psg_tp_nm`, `h_psrm_cl_nm`, `h_rg_rcvd_amt`

정적 검색 기준 `new PriceFareDao` 직접 UI 호출은 확인되지 않았다. endpoint와 DAO는 존재하지만 현재 APK UI에서의 진입 조건은 **unknown**이다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java:14-33`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java:35-75`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/PriceFareDao.java:146-177`.

### 8. 환승 가능역 조회

- Service: `TrainsInfoService.getSelectStationInfo`
- HTTP: `POST /classes/com.korail.mobile.qry.chtnStn.do`
- Response: `TrainSelectStationDao.TrainSelectStationResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:32-34`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java:67-71`

Request fields: `Device`, `Version`, `Key`, `dptRsStnCd`, `arvRsStnCd`.

Caller flow: `L4.h` transfer selector dialog가 출발/도착 station code로 request를 만들고 실행한다. 응답을 받은 뒤 synthetic option `TrainSelectStationDao.getAllTransferStationInfo()`를 첫 항목에 추가한다. 이 synthetic option의 기본값은 `chtnRsStnCd=""`, `chtnRsStnNm="전체"`다. 근거: `analysis/jadx/sources/L4/h.java:289-310`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java:47-65`.

Response fields: `chtnList[]`, 각 `TransferStationInfo`는 `chtnRsStnCd`, `chtnRsStnNm`. 서버가 반환하는 실제 역 목록/코드는 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java:36-61`.

### 9. 관광열차 특실/좌석 부가정보

- Service: `TrainsInfoService.getTourTrainInfo`
- HTTP: `POST /classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom`
- Response: `TourTrainInfoDao.TourTrainInfoResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:36-38`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java:124-128`

Request fields sent to server: `Device`, `Version`, `Key`, `trnGpCd`.

Caller flow: `IntegrationWebViewActivity`가 URI query에서 `trnGpCd`, `type`, `startStation`, `endStation`, `jobDv`를 읽지만, 서버에는 `trnGpCd`만 보낸다. 나머지는 응답 후 `DiscountTourTrainBookingActivity` intent extra로 전달된다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java:130-159`.

Response fields:

- `seat_infos.seat_info[]`
- `SeatInfo`: `h_seat_att_cd`, `seat_add_infos`
- `SeatAddInfos.seat_add_info[]`
- `SeatAddInfo.h_psg_num`

실제 좌석속성 코드와 인원값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java:13-60`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java:113-121`.

### 10. 실제 열차 운행 스케줄/지연 정보

- Service: `TrainsInfoService.getTrainSchedule`
- HTTP: `POST /classes/com.korail.mobile.research.actualTrainSchedule.do`
- Response: `TrainScheduleDao.TrainScheduleResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:40-42`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java:157-161`

Request fields: `Device`, `Version`, `runDt`, `trnNo`. 특이하게 `Key`를 보내지 않는다. UI caller는 `TrainInfo.h_run_dt`와 zero-padded 5자리 `h_trn_no`를 사용한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java:143-151`.

Response fields:

- Top-level: `dlayDtlRsnCont`, `dlayList[]`, `msgCont`, `runDt1`, `runSegOrdr`, `trnDptFlg`, `trnNo1`
- `TimeInfo`: `actArvDlayTnum`, `actArvDt`, `actArvTm`, `actDptDt`, `actDptTm`, `arvDt`, `arvTm`, `dptDt`, `dptTm`, `expnArvDlayTnum`, `expnDptDlayTnum`, `rgulFlg`, `saodFlg`, `stopStnNm`

UI transformations:

- 응답 `runDt1`, `trnNo1`, `dlayList`로 화면 제목/날짜/정차역 타임라인을 만든다.
- `rgulFlg == "Y"`이면 무정차/미정차 station marker로 보인다.
- `saodFlg`는 타임라인 병합/표시 로직에서 사용된다.
- 실제 지연 사유/시간 값은 **unknown**.

근거: `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java:12-90`, `analysis/jadx/sources/com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java:116-155`, `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java:185-220`, `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java:385-405`.

### 11. 좌석배정 가능 열차 스케줄 조회

- Service: `ResearchService.getAssignScheduleView`
- HTTP: `POST /classes/com.korail.mobile.research.assignScheduleView.do`
- Response: `SeatAssignScheduleViewDao.SeatAssignScheduleViewResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:31-33`, `analysis/jadx/sources/com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java:165-169`

Request fields: `Device`, `Version`, `Key`, `menuId`, `dptDt`, `dptTm`, `dptRsStnNm`, `arvRsStnNm`, `trnGpCd`, `psrmClCd`, `seatAttCd1`, `psgNum1`, `stlbDturDvNm1`, `dirtChtnDvCd`, `chtnArvRsStnNm`.

Caller assembly: `U4.b.getSeatAssignScheduleViewRequest()`는 ticket detail과 seat assign data에서 menu/train/seat/passenger 정보를 조합한다. 선택일이 오늘보다 과거면 오늘로 보정한다. 직접/환승 여부는 ticket_info size가 1이면 직접, 2이면 환승으로 설정한다. 근거: `analysis/jadx/sources/U4/b.java:87-107`.

Response fields: `h_next_pg_flg`, `trn_infos` (`RsvInquiryResponse.TrainInfos`). 실제 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java:149-162`.

Pagination: `setNextStartTime()`은 일반 조회와 동일하게 결과 열차의 출발시각으로 다음 시작시각을 설정한다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java:114-122`.

### 12. 좌석도 객차 목록

- Service: `ResearchService.getCarList`
- HTTP: `POST /classes/com.korail.mobile.research.TrainResearch`
- Response: `SearchCarListDao.SearchCarListResponse`
- DynaPath: static URL 목록에는 없음
- NetFunnel: 좌석도 화면 호출 경로에서 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:35-37`, `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchCarListDao.java:84-88`

Request fields:

`Device`, `Version`, `Key`, `Sid`, `txtMenuId`, `psrmClCd`, `runDt`, `dptDt`, `trnClsfCd`, `trnNo`, `dptRsStnCd`, `arvRsStnCd`, `dptStnRunOrdr`, `arvStnRunOrdr`, `trnGpCd`, `totPsgCnt`, `txtSeatAttCd`, `txtGdNo`, `sidTest`.

`sidTest`는 `SERVER_TYPE == REAL`이면 null, 아니면 `"Y"`다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchCarListDao.java:84-88`.

Request class fields are `SeatSearchRequest`: `ctlDvCd`, `trnClsfNm`, `txtArvRsStnCd`, `txtArvStnRunOrdr`, `txtDptDt`, `txtDptRsStnCd`, `txtDptStnRunOrdr`, `txtGdNo`, `txtMenuId`, `txtPsrmClCd`, `txtRunDt`, `txtSeatAttCd`, `txtSrcarNo`, `txtTotPsgCnt`, `txtTrnClsfCd`, `txtTrnGpCd`, `txtTrnNo`. 근거: `analysis/jadx/sources/com/korail/talk/network/request/research/SeatSearchRequest.java:7-25`.

Response fields:

- Top-level: `h_rcmd_srcar_no`, `h_trn_no`, `srcar_infos`
- `srcar_infos.srcar_info[]`
- `CarInfo`: `h_psrm_cl_nm`, `h_rest_seat_cnt`, `h_srcar_no`, `seatAttInfos`
- `SeatAttInfo`: `seatAttNm`

실제 객차번호/잔여석/속성명 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchCarListDao.java:15-82`.

### 13. 좌석도 좌석 목록

- Service: `ResearchService.getSeatList`
- HTTP: `POST /classes/com.korail.mobile.research.TResidualSeatsResearch.do`
- Response: `SearchSeatListDao.SearchSeatListResponse`
- DynaPath: static URL 목록에는 없음
- NetFunnel: 좌석도 화면 호출 경로에서 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:57-59`, `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchSeatListDao.java:133-137`

Request fields:

`Device`, `Version`, `Key`, `trnClsfCd`, `trnGpCd`, `runDt`, `trnNo`, `srcarNo`, `psrmClCd`, `dptRsStnCd`, `arvRsStnCd`, `seatAttCd`, `dptStnRunOrdr`, `arvStnRunOrdr`, `totPsgCnt`, `gdNo`, `isArrow`, `Sid`, `sidTest`, `ctlDvCd`.

DAO hard-codes `isArrow=true`, generates fresh `Sid`, and uses `sidTest=null` on REAL or `"Y"` otherwise. `ctlDvCd` is null-normalized to empty string by `SeatSearchActivity` before request. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchSeatListDao.java:133-137`, `analysis/jadx/sources/com/korail/talk/ui/seat/SeatSearchActivity.java:201-213`.

Response fields:

- Top-level: `layout_type`, `seatList[]`, `seat_ary_cd`, `seat_remain_count`, `seat_total_count`, `vrBnrUrl`, `windowList[]`
- `Seat`: `dir_seat_att_cd`, `etc_seat_att_cd`, `floor`, `intg_msg`, `intg_msg_cd`, `rq_seat_att_cd`, `sale_psb_flg`, `seat_no`, `seat_spec`, `sqr_no`, `vz_msg_dv_cd`
- `Window`: `cls_loc_rt`, `st_loc_rt`

실제 좌석번호/좌석속성/VR URL/메시지 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/SearchSeatListDao.java:15-131`.

UI transformations:

- `layout_type`은 0, 1, 2, 그 외에 따라 3열/4열/6좌석 set layout을 선택한다.
- `seat_ary_cd`는 row column 계산에 integer로 파싱하고 실패 시 4를 사용한다.
- `windowList`의 `st_loc_rt`, `cls_loc_rt`는 양쪽 창문 view height/margin 계산에 사용된다.
- `vz_msg_dv_cd == "M"`이면 안내 dialog 후 선택, `"Q"`이면 확인 dialog 후 선택으로 보인다. 실제 메시지 의미는 **unknown**.

근거: `analysis/jadx/sources/com/korail/talk/ui/seat/a.java:95-105`, `analysis/jadx/sources/com/korail/talk/ui/seat/a.java:136-198`, `analysis/jadx/sources/com/korail/talk/ui/seat/a.java:227-248`, `analysis/jadx/sources/com/korail/talk/ui/seat/a.java:251-290`.

### 14. 병합/연결 좌석 조회

- Service: `ResearchService.getMergeSeatsInquiry`
- HTTP: `POST /classes/com.korail.mobile.research.mergeSeatsC.do`
- Response: `MergeSeatInquiryDao.MergeSeatInquiryResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:47-49`, `analysis/jadx/sources/com/korail/talk/network/dao/research/MergeSeatInquiryDao.java:148-152`

Request fields:

`Device`, `Version`, `Key`, `abrdDt`, `runDt`, `trnNo`, `dptRsStnNm`, `arvRsStnNm`, `selRsStnNm`, `psrmClCd`, `seatAttCd`, `totPsgNum`.

Caller assembly:

- `DirectInquiryActivity.g3()`가 예약용 `OJrny`, `OSeat`, `OPsg`에서 필드를 조립한다.
- `abrdDt`와 `runDt`는 출발일+출발시각 문자열로 만들어진다.
- `trnNo`는 integer parse 후 5자리 zero-padding한다.
- 출발/도착 역명은 station code에서 station name으로 변환한다.

근거: `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:350-370`.

Response fields:

- `midStnList[]`: 실제 decompiled field는 `public List<MidStnList.MidStationInfo> midStnList`
- `trn_infos`: `RsvInquiryResponse.TrainInfos`
- `MidStationInfo`: `rsStnCd`, `rsStnNm`, `runOrdr`

실제 중간역/열차 값은 **unknown**. UI는 `midStnList`로 연결역 선택 dialog를 표시하고, `trn_infos`는 dialog train info로 전달한다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/MergeSeatInquiryDao.java:100-146`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/rir/orr/DirectInquiryActivity.java:543-560`.

### 15. N카드 할인 열차 스케줄 조회

- Service: `ResearchService.getNCardSchedultView`
- HTTP: `GET /classes/com.korail.mobile.research.dcntCrdScheduleView.do`
- Response: `NCardInquiryDao.NCardInquiryResponse`
- DynaPath/NetFunnel: 없음 확인
- Source: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:54-55`, `analysis/jadx/sources/com/korail/talk/network/dao/research/NCardInquiryDao.java:238-242`

이 endpoint는 일반 열차 조회와 별도 상품인 N카드 스케줄 조회지만, 열차 스케줄 검색 결과를 반환하므로 범위에 포함했다.

Query fields:

`Device`, `Version`, `Key`, `dptDt`, `dptRsStnNm`, `arvRsStnNm`, `dptTm`, `trnGpCd`, `dirtChtnDvCd`, `dcntCrdKndCd`, `dcntCrdKndMgNo`, `useTrmDno`, `usePsbTno`, `qryPgNo`.

Caller assembly:

- `U4.b.getNCardInquiryRequest()`는 오늘 날짜, `000000`, 출도착 역명, 전체 열차그룹, 직접 여정 코드를 기본 설정한다.
- discount type number가 `B2N18120402` 또는 `B2N18120403`이면 `dcntCrdKndCd="B2N"`, 아니면 `"MMM"`으로 설정한다. 실제 코드 의미는 **unknown**.
- Section inquiry screen은 section별로 `qryPgNo`를 1부터 증가시키고, 응답 `fllwPgExt == "Y"`이면 같은 section 다음 페이지를 계속 호출한다.

근거: `analysis/jadx/sources/U4/b.java:52-80`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java:308-317`, `analysis/jadx/sources/com/korail/talk/ui/inquiry/SectionNCardInquiryActivity.java:392-424`.

Response fields:

- `fllwPgExt`
- `trnScdlList[]`
- `TrainInfo`: `arvRsStnCd`, `arvRsStnNm`, `arvStnConsOrdr`, `cmtrPrc`, `dirtChtnDvCd`, `dptRsStnCd`, `dptRsStnNm`, `dptStnConsOrdr`, `dturCd`, `dturNm`, `routCd`, `runDt`, `stationInfo`, `stationStringInfo`, `trnGpCd`, `trnNo`

실제 운임 `cmtrPrc`, 우회/노선 코드, pagination 값은 **unknown**. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/NCardInquiryDao.java:128-236`.

## 범위에서 제외한 ResearchService 항목

아래 endpoint는 `ResearchService`에 있으나 이 문서 범위의 열차 조회/스케줄/요금/좌석도 핵심 흐름에서 제외했다.

- `getCmtrInfo`: 정기권/commuter 정보
- `getCustTripInfo`: 편의설정
- `getNCardHistory`, `setNCardExtension`, `setNCardReservation`: N카드 이력/연장/구매
- `getTicketOriginalInquiry`: 좌석변경 원권 조회와 연결될 수 있으나 열차 검색 endpoint가 아니라 ticket 원권 조회

근거: `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:39-45`, `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:51-52`, `analysis/jadx/sources/com/korail/talk/network/dao/research/ResearchService.java:61-70`.

## 20-agent follow-up audit 보강

- `StbkAcntDao.ACCOUNT_REGISTER`는 확인된 값이 `"4"`다. `isForSaleDate()`는 `saleDdDvCd=="5"` 또는 `"4"`일 때 true다.
- `RsvInquiryResponse.TrainInfo`는 기존 요약보다 넓다. exhaustive catalog 기준 주요 필드는 운행/역/시간, 좌석/실, 할인/요금, 우회/지연, 대기예약, 추천상품까지 포함하며 `rcmdGdList`, `totPsgCnt`, `txtGdNo`도 함께 노출된다. 전체 필드 열거는 `17-response-models-exhaustive.md`의 `response.seatMovie.RsvInquiryResponse` 섹션을 canonical source로 둔다.
- query/search 쪽 Sid는 `S4.C0812l.getSid()` 결과를 쓰며, DynaPath header와 별개인 AES/CBC 기반 파라미터다.
