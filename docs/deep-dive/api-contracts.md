# KORAIL APK API Contracts

이 문서는 `analysis/reports/api-endpoints.tsv`와 `analysis/generated/network-model-fields.tsv`를 결합해 생성한 정적 API 계약서다. 실제 서버 호출은 하지 않았고, 응답 값 예시는 포함하지 않는다. 응답 필드는 APK decompile 결과의 Java model field 기준이다.

## 공통 전송 방식

- Base host: `https://smart.letskorail.com`
- 공통 request envelope: `BaseRequest` 생성자가 `Device=AD`, `Version=250601003`, `Key=korail1234567890`를 설정한다.
- Retrofit annotation 기준 `@FormUrlEncoded` POST는 form field로 전송한다. `GET`은 `@Query`/`@QueryMap`을 query string으로 전송한다.
- 공통 response envelope: `BaseResponse`는 `h_msg_cd`, `h_msg_txt`, `strResult`를 가진다. `SUCCESS` 값은 `SUCC`, `FAIL` 값은 `FAIL`로 선언돼 있다.
- `FieldMap`/`QueryMap`은 Java 코드에서 동적으로 조립되는 map이다. 이 문서에서는 annotation에 노출된 map 존재를 표시하고, 상세 key는 각 flow/agent report와 model catalog에서 추적한다.
- `@Field(CONSTANT)`/`@Query(CONSTANT)` 형태는 compile-time string constant를 resolve해 wire key를 표시한다. resolve 실패 항목은 `unresolved`로 표시되며, 현재 재추출 기준 unresolved는 0개다.
- 직접 field가 없는 response subclass는 parent response model field를 상속 schema로 표시한다.

- Retrofit method entries: **165**
- Distinct HTTP+path pairs: **159**
- Annotated interface count: **35**
- Method mix: `GET` 29, `POST` 136

## Endpoint Index

| Interface | Entries | Methods |
|---|---:|---|
| `AddService` | 5 | POST:5 |
| `BusReservationService` | 4 | POST:4 |
| `CacheService` | 3 | GET:3 |
| `CalendarService` | 1 | GET:1 |
| `CartService` | 3 | POST:3 |
| `CashReceipt` | 1 | POST:1 |
| `CertificationService` | 12 | GET:6, POST:6 |
| `CommonService` | 11 | GET:3, POST:8 |
| `CompensateService` | 3 | POST:3 |
| `CustService` | 1 | POST:1 |
| `DelayService` | 9 | POST:9 |
| `GiftInfoService` | 1 | POST:1 |
| `GifticketService` | 4 | POST:4 |
| `IndependentService` | 1 | POST:1 |
| `LoginService` | 7 | GET:1, POST:6 |
| `MileageService` | 3 | POST:3 |
| `MyTicketService` | 3 | GET:2, POST:1 |
| `NFilterService` | 1 | POST:1 |
| `PassCardService` | 4 | POST:4 |
| `PassService` | 8 | POST:8 |
| `PayService` | 12 | POST:12 |
| `PaymentService` | 1 | POST:1 |
| `ProductService` | 4 | GET:4 |
| `PushService` | 4 | GET:4 |
| `RailPlusService` | 1 | GET:1 |
| `ReceiptService` | 1 | POST:1 |
| `RefundService` | 5 | POST:5 |
| `ResearchService` | 11 | GET:3, POST:8 |
| `ReservationCancelService` | 3 | POST:3 |
| `ReservationService` | 4 | GET:1, POST:3 |
| `ReservationWaitService` | 1 | POST:1 |
| `SeatMovieService` | 3 | POST:3 |
| `TicketService` | 19 | POST:19 |
| `TrainsInfoService` | 6 | POST:6 |
| `XPointService` | 5 | POST:5 |

## `AddService`

### `additionalService`

- Request: `POST` `/classes/com.korail.mobile.addService.reserve.do`
- Source: `com/korail/talk/network/dao/addService/AddService.java:16`
- FormUrlEncoded: `Y`
- Return type: `AdditionalServiceDao.AdditionalServiceResponse` -> model `AdditionalServiceResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `jrnySqno` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `jobDvCd` |
| `Field` | `addSrvId` |
| `Field` | `reqQnty` |
| `Field` | `helpSrvTgtCnt` |
| `Field` | `rcpSqno` |
| `Field` | `cncTgtCnt` |
| `Field` | `addSrvReqNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `outrec2` | `List<OutRec2>` | `` | `AdditionalServiceResponse` |

### `dealCarBuy`

- Request: `POST` `/classes/com.korail.mobile.addService.buyConfirm.do`
- Source: `com/korail/talk/network/dao/addService/AddService.java:20`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `addSrvCnt` |
| `Field` | `addSrvReqNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getExtraProductList`

- Request: `POST` `/classes/com.korail.mobile.addService.reserveList.do`
- Source: `com/korail/talk/network/dao/addService/AddService.java:24`
- FormUrlEncoded: `Y`
- Return type: `ExtraProductListDao.ExtraProductListResponse` -> model `ExtraProductListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `pnrList` | `List<ExtraProductInfo>` | `` | `ExtraProductListResponse` |

### `helpSrvCust`

- Request: `POST` `/classes/com.korail.mobile.addSrv.helpSrvCust.do`
- Source: `com/korail/talk/network/dao/addService/AddService.java:28`
- FormUrlEncoded: `Y`
- Return type: `HelpSrvCustDao.HelpSrvCustResponse` -> model `HelpSrvCustResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `reqCnt` |
| `Field` | `reqAddSrvDvCd` |
| `Field` | `reqAddRcpSrvCd` |
| `Field` | `reqCustNm` |
| `Field` | `reqCntcChnCont` |
| `Field` | `qryDvCd` |
| `Field` | `addSrvDvCd` |
| `Field` | `rcpSqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `reqSpecList` | `List<ReqSpec>` | `` | `HelpSrvCustResponse` |

### `helpSrvTk`

- Request: `POST` `/classes/com.korail.mobile.addSrv.helpSrvTk.do`
- Source: `com/korail/talk/network/dao/addService/AddService.java:32`
- FormUrlEncoded: `Y`
- Return type: `HelpSrvTkDao.HelpSrvTkDaoResponse` -> model `HelpSrvTkDaoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `helpSrvList` | `List<helpSrv>` | `` | `HelpSrvTkDaoResponse` |

## `BusReservationService`

### `reservationCancelCheck`

- Request: `POST` `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk`
- Source: `com/korail/talk/network/dao/certification/BusReservationService.java:19`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtPnrNo` |
| `Field` | `txtJrnySqno` |
| `Field` | `txtJrnyCnt` |
| `Field` | `hidRsvChgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `reservationChange`

- Request: `POST` `/classes/com.korail.mobile.reservation.reservationChange.do`
- Source: `com/korail/talk/network/dao/certification/BusReservationService.java:23`
- FormUrlEncoded: `Y`
- Return type: `ReservationChangeDao.ReservationChangeResponse` -> model `ReservationChangeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `chgTno` |
| `Field` | `totPrnb` |
| `Field` | `stndFlg` |
| `Field` | `evntWctFlg` |
| `Field` | `wctHndgCncDvCd` |
| `Field` | `lrgCrgFlg` |
| `Field` | `psgCnt` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `jrnyList` | `List<JrnyInfo>` | `` | `ReservationChangeResponse` |

### `reservationList`

- Request: `POST` `/classes/com.korail.mobile.lmu.scdlQry.do`
- Source: `com/korail/talk/network/dao/certification/BusReservationService.java:27`
- FormUrlEncoded: `Y`
- Return type: `BusReservationListDao.BusInquiryResponse` -> model `BusInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dptDt` |
| `Field` | `dptRsStnCd` |
| `Field` | `arvRsStnCd` |
| `Field` | `tmGpCd` |
| `Field` | `psrmClCd` |
| `Field` | `dptTm` |
| `Field` | `trnNo` |
| `Field` | `seatAttCd` |
| `Field` | `rsvSaleDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fllwPgExt` | `String` | `` | `BusInquiryResponse` |
| `lgtmShtmDvCd` | `String` | `` | `BusInquiryResponse` |
| `trainList` | `ArrayList<BusList>` | `` | `BusInquiryResponse` |

### `reservationSeatList`

- Request: `POST` `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do`
- Source: `com/korail/talk/network/dao/certification/BusReservationService.java:31`
- FormUrlEncoded: `Y`
- Return type: `BusReservationSeatListDao.SeatListResponse` -> model `SeatListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `trnClsfCd` |
| `Field` | `trnGpCd` |
| `Field` | `runDt` |
| `Field` | `trnNo` |
| `Field` | `srcarNo` |
| `Field` | `psrmClCd` |
| `Field` | `dptRsStnCd` |
| `Field` | `arvRsStnCd` |
| `Field` | `seatAttCd` |
| `Field` | `dptStnRunOrdr` |
| `Field` | `arvStnRunOrdr` |
| `Field` | `totPsgCnt` |
| `Field` | `gdNo` |
| `Field` | `isArrow` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `car_tp_cd` | `String` | `` | `SeatListResponse` |
| `scar_no` | `String` | `` | `SeatListResponse` |
| `seatList` | `ArrayList<SeatList>` | `` | `SeatListResponse` |
| `seat_ary_cd` | `String` | `` | `SeatListResponse` |
| `up_dn_dv_cd` | `String` | `` | `SeatListResponse` |

## `CacheService`

### `checkService`

- Request: `GET` `/file/CACHE/MobileService.cache`
- Source: `com/korail/talk/network/dao/cache/CacheService.java:11`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `timeStamp` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getAppData`

- Request: `GET` `/file/CACHE/prdMobilePlusMain.cache`
- Source: `com/korail/talk/network/dao/cache/CacheService.java:14`
- FormUrlEncoded: `N`
- Return type: `AppDataDao.AppDataResponse` -> model `AppDataResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `timeStamp` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `disability_certification_msg` | `String` | `` | `AppDataResponse` |
| `forSeatIntg` | `String` | `` | `AppDataResponse` |
| `limousine` | `String` | `airportBusMsg` | `AppDataResponse` |
| `railplus_cardinfo` | `String` | `` | `AppDataResponse` |
| `version` | `Version` | `` | `AppDataResponse` |

### `getNotice`

- Request: `GET` `/file/CACHE/prdMobilePlusNotice.cache`
- Source: `com/korail/talk/network/dao/cache/CacheService.java:17`
- FormUrlEncoded: `N`
- Return type: `NoticeDao.NoticeResponse` -> model `NoticeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `timeStamp` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `bbrdId` | `String` | `` | `NoticeResponse` |
| `ptwtSqno` | `String` | `` | `NoticeResponse` |
| `ptwtTtl` | `String` | `` | `NoticeResponse` |

## `CalendarService`

### `getTrainCalendar`

- Request: `GET` `/classes/com.korail.mobile.schedule.runDt`
- Source: `com/korail/talk/network/dao/schedule/CalendarService.java:8`
- FormUrlEncoded: `N`
- Return type: `TrainCalendarDao.TrainCalendarResponse` -> model `TrainCalendarResponse`

Request parameters:
 none declared in service signature.

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `runningCalendar` | `List<RunningCalendar>` | `` | `TrainCalendarResponse` |

## `CartService`

### `addCart`

- Request: `POST` `/classes/com.korail.mobile.cart.addCartList`
- Source: `com/korail/talk/network/dao/cart/CartService.java:11`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidPnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getCartList`

- Request: `POST` `/classes/com.korail.mobile.cart.showCartList`
- Source: `com/korail/talk/network/dao/cart/CartService.java:15`
- FormUrlEncoded: `Y`
- Return type: `CartListDao.CartListResponse` -> model `CartListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `addSrvReqNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `cart_infos` | `CartInfos` | `` | `CartListResponse` |

### `verifyMaasStatus`

- Request: `POST` `/classes/com.korail.mobile.maas.rsvStt.do`
- Source: `com/korail/talk/network/dao/cart/CartService.java:19`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `addSrvDvCd` |
| `Field` | `addSrvReqNo` |
| `Field` | `coptEntRsvNo` |
| `Field` | `lumpStlTgtNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `CashReceipt`

### `issue`

- Request: `POST` `/classes/com.korail.mobile.cashReceipt.issue.do`
- Source: `com/korail/talk/network/dao/cashReceipt/CashReceipt.java:12`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `cashRcetTxnDvCd` |
| `Field` | `vltIsuFlg` |
| `Field` | `cashRcetAthnMtdCd` |
| `Field` | `athnDmnRcgnNo` |
| `Field` | `apvCnt` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `CertificationService`

### `applyDisabilityCertification`

- Request: `GET` `/classes/com.korail.mobile.certification.ReservationList`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:22`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `hidPnrNo` |
| `Query` | `txtPsgDisc0019Cnt` |
| `QueryMap` | dynamic map/body |
| `QueryMap` | dynamic map/body |
| `QueryMap` | dynamic map/body |
| `QueryMap` | dynamic map/body |
| `QueryMap` | dynamic map/body |
| `QueryMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `certCongressperson`

- Request: `GET` `/classes/com.korail.mobile.certification.assemblyCert`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:25`
- FormUrlEncoded: `N`
- Return type: `CongresspersonCertDao.CongresspersonCertResponse` -> model `CongresspersonCertResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `freeDiscCertNo` |
| `Query` | `certNo` |
| `Query` | `abrdDt` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `freeDiscCertNo` | `String` | `` | `CongresspersonCertResponse` |

### `certMerit`

- Request: `POST` `/classes/com.korail.mobile.certification.MeritCert`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:28`
- FormUrlEncoded: `Y`
- Return type: `MeritCertDao.MeritCertResponse` -> model `MeritCertResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtFreeDiscCertNo` |
| `Field` | `txtAcptPwd` |
| `Field` | `txtJuminNo7` |
| `Field` | `txtAbrdDt` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_free_acm_use_tno` | `String` | `` | `MeritCertResponse` |
| `h_free_disc_cert_no` | `String` | `` | `MeritCertResponse` |
| `h_free_psb_tno` | `String` | `` | `MeritCertResponse` |

### `disabledCertification`

- Request: `GET` `/classes/com.korail.mobile.certification.disabled.do`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:32`
- FormUrlEncoded: `N`
- Return type: `DisabledCertificationDao.DisabledCertificationResponse` -> model `DisabledCertificationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `regNum` |
| `Query` | `hdcpGrade` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `btdt` | `String` | `` | `DisabledCertificationResponse` |
| `certificate` | `String` | `` | `DisabledCertificationResponse` |
| `hdcpTpCd` | `String` | `` | `DisabledCertificationResponse` |
| `subtDcsClCd` | `String` | `` | `DisabledCertificationResponse` |

### `getDiscountPrice`

- Request: `POST` `/classes/com.korail.mobile.certification.PriceReCalculation`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:35`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidPnrNo` |
| `Field` | `txtJobId` |
| `Field` | `hiduserYn` |
| `Field` | `hidCustNo` |
| `Field` | `txtPsgGridcnt` |
| `Field` | `psg_tp_dv_cd` |
| `Field` | `hidDcntKndCd` |
| `Field` | `dcnt_knd_cd1` |
| `Field` | `hidDscpNo` |
| `Field` | `psrm_cl_cd` |
| `Field` | `hidFmlyNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `govermentCertification1`

- Request: `GET` `/classes/com.korail.mobile.pbep.toknCre.do`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:39`
- FormUrlEncoded: `N`
- Return type: `GovernmentCertificationStep1Dao.GovernmentCertificationResponse` -> model `GovernmentCertificationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `app` | `String` | `` | `GovernmentCertificationResponse` |
| `csrfToken` | `String` | `` | `GovernmentCertificationResponse` |

### `govermentCertification2`

- Request: `GET` `/classes/com.korail.mobile.pbep.sttChck.do`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:42`
- FormUrlEncoded: `N`
- Return type: `GovernmentCertificationStep2Dao.GovernmentCertificationStep2Response` -> model `GovernmentCertificationStep2Response`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `csrfToken` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `code` | `String` | `` | `GovernmentCertificationStep2Response` |
| `message` | `String` | `` | `GovernmentCertificationStep2Response` |
| `pbepInfo` | `String` | `` | `GovernmentCertificationStep2Response` |
| `result` | `String` | `` | `GovernmentCertificationStep2Response` |
| `txCompleteCode` | `String` | `` | `GovernmentCertificationStep2Response` |

### `inquiryTicketRsv`

- Request: `GET` `/classes/com.korail.mobile.certification.ReservationList`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:45`
- FormUrlEncoded: `N`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `hidPnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `reservation`

- Request: `POST` `/classes/com.korail.mobile.nonMember.NonMemTicket`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:48`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `txtMenuId` |
| `Field` | `txtJobId` |
| `Field` | `txtGdNo` |
| `Field` | `hidFreeFlg` |
| `Field` | `txtStndFlg` |
| `Field` | `txtCustNm` |
| `Field` | `txtCpNo` |
| `Field` | `txtCustPw` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `reservation`

- Request: `POST` `/classes/com.korail.mobile.certification.TicketReservation`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:52`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `txtMenuId` |
| `Field` | `txtJobId` |
| `Field` | `txtGdNo` |
| `Field` | `hidFreeFlg` |
| `Field` | `txtStndFlg` |
| `Field` | `pbepInfo` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `reservation`

- Request: `POST` `/classes/com.korail.mobile.nonMember.NonMemTicket`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:56`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtCustNm` |
| `Field` | `txtCpNo` |
| `Field` | `txtCustPw` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `reservation`

- Request: `POST` `/classes/com.korail.mobile.certification.TicketReservation`
- Source: `com/korail/talk/network/dao/certification/CertificationService.java:60`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

## `CommonService`

### `authQRLocation`

- Request: `POST` `/classes/com.korail.mobile.qr.bchTripSv.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:23`
- FormUrlEncoded: `Y`
- Return type: `authQRLocationDao.QRLocationResponse` -> model `QRLocationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `qrcode` |
| `Field` | `latitude` |
| `Field` | `longitude` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `jobScsFlg` | `String` | `` | `QRLocationResponse` |

### `ckValue`

- Request: `GET` `/ebizcross/getUUID.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:27`
- FormUrlEncoded: `N`
- Return type: `CookieDao.RsvWaitResponse` -> model `RsvWaitResponse`

Request parameters:
 none declared in service signature.

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mutMrkVrfCd` | `String` | `` | `RsvWaitResponse` |

### `getCommonCode`

- Request: `POST` `/classes/com.korail.mobile.common.code.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:30`
- FormUrlEncoded: `Y`
- Return type: `CommonCodeDao.CommonCodeResponse` -> model `CommonCodeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `code` |
| `Field` | `deviceWidth` |
| `Field` | `deviceHeight` |
| `Field` | `departDate` |
| `Field` | `arrivalDate` |
| `Field` | `holidayYn` |
| `Field` | `OSVersion` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `accepts` | `List<Accept>` | `` | `CommonCodeResponse` |
| `athn` | `Athn` | `` | `CommonCodeResponse` |
| `buyNow` | `BuyNow` | `` | `CommonCodeResponse` |
| `data` | `Data` | `` | `CommonCodeResponse` |
| `deviceOreo` | `DeviceOSPopUp` | `` | `CommonCodeResponse` |
| `easyPay` | `EasyPay` | `` | `CommonCodeResponse` |
| `holidayPopup` | `HolidayPopup` | `` | `CommonCodeResponse` |
| `imageDownLoadData` | `ImageDownLoadData` | `` | `CommonCodeResponse` |
| `isEasyLoginShow` | `EasyLogin` | `` | `CommonCodeResponse` |
| `korailBoss` | `KorailBoss` | `` | `CommonCodeResponse` |
| `limousine` | `String` | `` | `CommonCodeResponse` |
| `limousineMainMsg` | `String` | `` | `CommonCodeResponse` |
| `login` | `Login` | `` | `CommonCodeResponse` |
| `lostArticle` | `LostArticle` | `` | `CommonCodeResponse` |
| `maasTest` | `String` | `` | `CommonCodeResponse` |
| `mainPopup` | `MainPopup` | `` | `CommonCodeResponse` |
| `menuBiz` | `MenuBiz` | `` | `CommonCodeResponse` |
| `menuRailPoint` | `MenuRailPoint` | `` | `CommonCodeResponse` |
| `periodCommutationData` | `PeriodCommutationData` | `` | `CommonCodeResponse` |
| `pointData` | `Point` | `` | `CommonCodeResponse` |
| `report` | `Report` | `` | `CommonCodeResponse` |
| `stationCd` | `List<String>` | `` | `CommonCodeResponse` |
| `stationNm` | `List<String>` | `` | `CommonCodeResponse` |
| `viewVisibility` | `ViewVisibility` | `` | `CommonCodeResponse` |

### `getDecrypt`

- Request: `POST` `/classes/com.korail.mobile.common.decrypt.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:34`
- FormUrlEncoded: `Y`
- Return type: `DecryptDao.DecryptResponse` -> model `DecryptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `type` |
| `Field` | `values` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `decValueList` | `List<DecryptValueList>` | `` | `DecryptResponse` |

### `getEncrypt`

- Request: `POST` `/classes/com.korail.mobile.common.encrypt.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:38`
- FormUrlEncoded: `Y`
- Return type: `EncryptDao.EncryptResponse` -> model `EncryptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `type` |
| `Field` | `values` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `encValueList` | `List<EncryptValueList>` | `` | `EncryptResponse` |

### `getKBPayEncrypt`

- Request: `POST` `/classes/com.korail.mobile.common.encrypt.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:42`
- FormUrlEncoded: `Y`
- Return type: `KBPayEncryptDao.KBpayEncryptResponse` -> model `KBpayEncryptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `type` |
| `Field` | `values` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `BIZ_NUM` | `String` | `` | `KBpayEncryptResponse` |
| `CHANNEL_ID` | `String` | `` | `KBpayEncryptResponse` |
| `PURCHASE_PRODUCT_INFO` | `String` | `` | `KBpayEncryptResponse` |
| `REQ_DATE_TIME` | `String` | `` | `KBpayEncryptResponse` |
| `SELLER_NAME` | `String` | `` | `KBpayEncryptResponse` |
| `SELLER_NUM` | `String` | `` | `KBpayEncryptResponse` |
| `encValueList` | `List<EncryptDao.EncryptValueList>` | `` | `KBpayEncryptResponse` |

### `getMaasMenuList`

- Request: `POST` `/classes/com.korail.mobile.copt.gdMenuLt.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:46`
- FormUrlEncoded: `Y`
- Return type: `MaasMenuListDao.MaasMenuListResponse` -> model `MaasMenuListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `pnrNo` |
| `Field` | `tkRetNo` |
| `Field` | `addSrvReqNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `menuList` | `List<Menu>` | `` | `MaasMenuListResponse` |

### `getMaasStationList`

- Request: `POST` `/ebizmaas/EbizMaasStationList.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:50`
- FormUrlEncoded: `Y`
- Return type: `StationDataDao.StationDataResponse` -> model `StationDataResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `addSrvDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stns` | `STNs` | `` | `StationDataResponse` |

### `getStationData`

- Request: `GET` `/classes/com.korail.mobile.common.stationdata`
- Source: `com/korail/talk/network/dao/common/CommonService.java:54`
- FormUrlEncoded: `N`
- Return type: `StationDataDao.StationDataResponse` -> model `StationDataResponse`

Request parameters:
 none declared in service signature.

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stns` | `STNs` | `` | `StationDataResponse` |

### `getStationInfo`

- Request: `GET` `/classes/com.korail.mobile.common.stationinfo`
- Source: `com/korail/talk/network/dao/common/CommonService.java:57`
- FormUrlEncoded: `N`
- Return type: `StationInfoDao.StationInfoResponse` -> model `StationInfoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `count` | `int` | `` | `StationInfoResponse` |
| `map_version` | `String` | `` | `StationInfoResponse` |

### `seedEncrypt`

- Request: `POST` `/classes/com.korail.mobile.shinhan.Encrypt.do`
- Source: `com/korail/talk/network/dao/common/CommonService.java:60`
- FormUrlEncoded: `Y`
- Return type: `SeedEncryptDao.SeedEncryptResponse` -> model `SeedEncryptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `value` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `encValueList` | `List<EncValueList>` | `` | `SeedEncryptResponse` |

## `CompensateService`

### `executeCompensateRefund`

- Request: `POST` `/classes/com.korail.mobile.compensate.ticketReturn.do`
- Source: `com/korail/talk/network/dao/compensate/CompensateService.java:12`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `Field` | `trnStpRsStnCd` |
| `Field` | `jrnyStpTkFlg` |
| `Field` | `ogTkSaleWctNo` |
| `Field` | `ogTkSaleDd` |
| `Field` | `ogTkSaleSqNo` |
| `Field` | `ogTkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `executeCompensateRefundDetail`

- Request: `POST` `/classes/com.korail.mobile.compensate.ticketDetail.do`
- Source: `com/korail/talk/network/dao/compensate/CompensateService.java:16`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `Field` | `trnStpRsStnCd` |
| `Field` | `jrnyStpTkFlg` |
| `Field` | `ogTkSaleWctNo` |
| `Field` | `ogTkSaleDd` |
| `Field` | `ogTkSaleSqNo` |
| `Field` | `ogTkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `executeCompensateRefundList`

- Request: `POST` `/classes/com.korail.mobile.compensate.ticketList.do`
- Source: `com/korail/talk/network/dao/compensate/CompensateService.java:20`
- FormUrlEncoded: `Y`
- Return type: `CompensateRefundListDao.CompensateRefundListResponse` -> model `CompensateRefundListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `nowPgNo` |
| `Field` | `dptDtFrom` |
| `Field` | `dptDtTo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlList` | `List<StlList>` | `` | `RefundResponse` |
| `ticketList` | `List<TicketList>` | `` | `RefundResponse` |
| `whlPgNum` | `int` | `` | `RefundResponse` |

## `CustService`

### `mchdDcntTgt`

- Request: `POST` `/classes/com.korail.mobile.cust.mchdDcntTgt.do`
- Source: `com/korail/talk/network/dao/cust/CustService.java:11`
- FormUrlEncoded: `Y`
- Return type: `MchdDcntTgtDao.MchdDcntTgtResponse` -> model `MchdDcntTgtResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dptDt` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fmlyList` | `List<Fmly>` | `` | `MchdDcntTgtResponse` |

## `DelayService`

### `athnIsu`

- Request: `POST` `/classes/com.korail.mobile.dlay.athnIsu.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:18`
- FormUrlEncoded: `Y`
- Return type: `DelayCertificateDao.DelayCertificateResponse` -> model `DelayCertificateResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `ogtkSaleWctNo` |
| `Field` | `ogtkSaleDd` |
| `Field` | `ogtkSaleSqno` |
| `Field` | `ogtkRetPwd` |
| `Field` | `runDt` |
| `Field` | `trnNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dlayList` | `List<DelayInfo>` | `` | `DelayCertificateResponse` |

### `cashRfn`

- Request: `POST` `/classes/com.korail.mobile.dlay.cashRfn.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:22`
- FormUrlEncoded: `Y`
- Return type: `CashRfnDao.CashRfnResponse` -> model `CashRfnResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dmnPrsDvCd` |
| `Field` | `saleWctNo` |
| `Field` | `saleDd` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |
| `Field` | `dptnBankCd` |
| `Field` | `dptnAcntNo` |
| `Field` | `custNm` |
| `Field` | `custTeln` |
| `Field` | `rmk1Cont` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `rfnAmt` | `String` | `` | `CashRfnResponse` |

### `dealyReturnReceipt`

- Request: `POST` `/classes/com.korail.mobile.dlay.pymtRcet.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:26`
- FormUrlEncoded: `Y`
- Return type: `DelayReturnReceiptDao.DelayReturnReceiptResponse` -> model `DelayReturnReceiptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDd` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dlayFarePymtMtdNm` | `String` | `` | `DelayReturnReceiptResponse` |
| `dlayFareRetAmt` | `String` | `` | `DelayReturnReceiptResponse` |
| `retDt` | `String` | `` | `DelayReturnReceiptResponse` |

### `dptnBank`

- Request: `POST` `/classes/com.korail.mobile.dlay.dptnBank.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:30`
- FormUrlEncoded: `Y`
- Return type: `DptnBankDao.DptnBankResponse` -> model `DptnBankResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dptnBank` | `List<DptnBank>` | `` | `DptnBankResponse` |

### `executeDelayPNRAccept`

- Request: `POST` `/classes/com.korail.mobile.delay.acptPrs.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:34`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `jobDvCd` |
| `Field` | `pnrCnt` |
| `Field` | `pnrNo` |
| `Field` | `ogtkWctNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `executeDelayPNRQuery`

- Request: `POST` `/classes/com.korail.mobile.delay.pnrQry.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:38`
- FormUrlEncoded: `Y`
- Return type: `DelayPNRQueryDao.DelayPNRQueryResponse` -> model `DelayPNRQueryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `jobDvCd` |
| `Field` | `pnrCnt` |
| `Field` | `pnrNo` |
| `Field` | `ogtkWctNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mainList` | `List<Main>` | `` | `DelayPNRQueryResponse` |

### `executeDelayRefund`

- Request: `POST` `/classes/com.korail.mobile.delay.ticketReturn.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:42`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dlayFarePymtMtdCd` |
| `Field` | `tkCnt` |
| `Field` | `ogTkSaleWctNo` |
| `Field` | `ogTkSaleDd` |
| `Field` | `ogTkSaleSqNo` |
| `Field` | `ogTkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `executeDelayRefundDetail`

- Request: `POST` `/classes/com.korail.mobile.delay.ticketDetail.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:46`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `Field` | `ogTkSaleWctNo` |
| `Field` | `ogTkSaleDd` |
| `Field` | `ogTkSaleSqNo` |
| `Field` | `ogTkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `executeDelayRefundList`

- Request: `POST` `/classes/com.korail.mobile.delay.ticketList.do`
- Source: `com/korail/talk/network/dao/delay/DelayService.java:50`
- FormUrlEncoded: `Y`
- Return type: `DelayRefundListDao.DelayRefundListResponse` -> model `DelayRefundListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `nowPgNo` |
| `Field` | `dptDtFrom` |
| `Field` | `dptDtTo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlList` | `List<StlList>` | `` | `RefundResponse` |
| `ticketList` | `List<TicketList>` | `` | `RefundResponse` |
| `whlPgNum` | `int` | `` | `RefundResponse` |

## `GiftInfoService`

### `presentTicket`

- Request: `POST` `/classes/com.korail.mobile.giftInfo.GiftSend`
- Source: `com/korail/talk/network/dao/giftInfo/GiftInfoService.java:12`
- FormUrlEncoded: `Y`
- Return type: `TicketPresentDao.TicketPresentResponse` -> model `TicketPresentResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidAcepPsNm` |
| `Field` | `hidAcepPsTeln` |
| `Field` | `hidPbpAcepPsMbFlg` |
| `Field` | `hidPbpAcepPsCustMgNo` |
| `Field` | `hidPnrNo` |
| `Field` | `hidTotNewStlAmt` |
| `Field` | `hidRsvChgNo` |
| `Field` | `hidInfoInpDvCd` |
| `Field` | `hidSaleCnt` |
| `Field` | `hidAcepPwd` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `chgePbpRsvNo` | `String` | `` | `TicketPresentResponse` |

## `GifticketService`

### `bookingGifticket`

- Request: `POST` `/classes/com.korail.mobile.gift.gdRsv.do`
- Source: `com/korail/talk/network/dao/gifticket/GifticketService.java:13`
- FormUrlEncoded: `Y`
- Return type: `GifticketBookingDao.GifticketBookingResponse` -> model `GifticketBookingResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `itmCnt` |
| `Field` | `mrkAmt_1` |
| `Field` | `prnbCnt` |
| `Field` | `mbCrdNo_1` |
| `Field` | `gdUtlPsNm_1` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `lumpStlTgtNo` | `String` | `` | `GifticketBookingResponse` |
| `prsCnqeVal` | `String` | `` | `GifticketBookingResponse` |
| `rcvdAmt` | `String` | `` | `GifticketBookingResponse` |

### `getGifticketList`

- Request: `POST` `/classes/com.korail.mobile.gift.gdLst.do`
- Source: `com/korail/talk/network/dao/gifticket/GifticketService.java:17`
- FormUrlEncoded: `Y`
- Return type: `GifticketListDao.GifticketListResponse` -> model `GifticketListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `qryDvCd` |
| `Field` | `qryVal` |
| `Field` | `abrdDtFrom` |
| `Field` | `abrdDtTo` |
| `Field` | `usePsbFlg` |
| `Field` | `qryNumNext` |
| `Field` | `fllwQryFlg` |
| `Field` | `trnOprBzDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `gdList` | `List<GifticketInfo>` | `` | `GifticketListResponse` |
| `qryCnt` | `String` | `` | `GifticketListResponse` |
| `qryNumNext` | `String` | `` | `GifticketListResponse` |

### `historyGifticket`

- Request: `POST` `/classes/com.korail.mobile.gift.gdUseSpec.do`
- Source: `com/korail/talk/network/dao/gifticket/GifticketService.java:21`
- FormUrlEncoded: `Y`
- Return type: `GifticketHistoryDao.GifticketHistoryResponse` -> model `GifticketHistoryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkId` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fllwQryFlg` | `String` | `` | `GifticketHistoryResponse` |
| `qryCnt` | `String` | `` | `GifticketHistoryResponse` |
| `txnList` | `List<GifticketDetailData>` | `` | `GifticketHistoryResponse` |

### `returnGifticket`

- Request: `POST` `/classes/com.korail.mobile.gift.gdRet.do`
- Source: `com/korail/talk/network/dao/gifticket/GifticketService.java:25`
- FormUrlEncoded: `Y`
- Return type: `GifticketReturnDao.GifticketReturnResponse` -> model `GifticketReturnResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkId` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `prsFlg` | `String` | `` | `GifticketReturnResponse` |

## `IndependentService`

### `registerUserInfo`

- Request: `POST` `/classes/com.korail.mobile.login.poppCfmRec.do`
- Source: `com/korail/talk/network/dao/independent/IndependentService.java:12`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `LoginService`

### `certMember`

- Request: `POST` `/classes/com.korail.mobile.login.userCheck`
- Source: `com/korail/talk/network/dao/login/LoginService.java:13`
- FormUrlEncoded: `Y`
- Return type: `MemberCertDao.MemberCertResponse` -> model `MemberCertResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtAcptPsNm` |
| `Field` | `acept` |
| `Field` | `txtCpNo` |
| `Field` | `memNum` |
| `Field` | `txtEmailNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mbCrdNo` | `String` | `` | `MemberCertResponse` |
| `strCustNo` | `String` | `` | `MemberCertResponse` |

### `login`

- Request: `POST` `/classes/com.korail.mobile.login.Login`
- Source: `com/korail/talk/network/dao/login/LoginService.java:17`
- FormUrlEncoded: `Y`
- Return type: `LoginDao.LoginResponse` -> model `LoginResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtMemberNo` |
| `Field` | `txtPwd` |
| `Field` | `txtInputFlg` |
| `Field` | `checkValidPw` |
| `Field` | `custId` |
| `Field` | `etrPath` |
| `Field` | `idx` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `coupClsFlg` | `String` | `` | `LoginResponse` |
| `dlayDscpInfo` | `String` | `` | `LoginResponse` |
| `encryptCustNo` | `String` | `` | `LoginResponse` |
| `encryptHMbCrdNo` | `String` | `` | `LoginResponse` |
| `encryptMbCrdNo` | `String` | `` | `LoginResponse` |
| `intgFlg` | `String` | `` | `LoginResponse` |
| `intgMsgTxt` | `String` | `` | `LoginResponse` |
| `intgUrl` | `String` | `` | `LoginResponse` |
| `notiTpCd` | `String` | `` | `LoginResponse` |
| `strAthnFlg5` | `String` | `` | `LoginResponse` |
| `strAthnFlg7` | `String` | `` | `LoginResponse` |
| `strBtdt` | `String` | `` | `LoginResponse` |
| `strCpNo` | `String` | `` | `LoginResponse` |
| `strCustClCd` | `String` | `` | `LoginResponse` |
| `strCustDvCd` | `String` | `` | `LoginResponse` |
| `strCustLeadFlg` | `String` | `` | `LoginResponse` |
| `strCustMgSrtCd` | `String` | `` | `LoginResponse` |
| `strCustNm` | `String` | `` | `LoginResponse` |
| `strCustNo` | `String` | `` | `LoginResponse` |
| `strCustSrtCd` | `String` | `` | `LoginResponse` |
| `strEmailAdr` | `String` | `` | `LoginResponse` |
| `strHdcpFlg` | `String` | `` | `LoginResponse` |
| `strHdcpTpCd` | `String` | `` | `LoginResponse` |
| `strHdcpTpCdNm` | `String` | `` | `LoginResponse` |
| `strLognTpCd6` | `String` | `` | `LoginResponse` |
| `strMbCrdNo` | `String` | `` | `LoginResponse` |
| `strRedirectUrl` | `String` | `` | `LoginResponse` |
| `strSubtDcsClCd` | `String` | `` | `LoginResponse` |
| `strYouthAgrFlg` | `String` | `` | `LoginResponse` |

### `loginAthnReg`

- Request: `POST` `/classes/com.korail.mobile.login.loginAthnReg.do`
- Source: `com/korail/talk/network/dao/login/LoginService.java:21`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `lognTpCd` |
| `Field` | `custId` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `loginAthnRmv`

- Request: `POST` `/classes/com.korail.mobile.login.loginAthnRmv.do`
- Source: `com/korail/talk/network/dao/login/LoginService.java:25`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `srvQryDvVal` |
| `Field` | `lognTpCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `logout`

- Request: `GET` `/classes/com.korail.mobile.login.Logout`
- Source: `com/korail/talk/network/dao/login/LoginService.java:29`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:
 none declared in service signature.

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `memberCheck`

- Request: `POST` `/classes/com.korail.mobile.login.joinCfm.do`
- Source: `com/korail/talk/network/dao/login/LoginService.java:32`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `hmpgPwd` |
| `Field` | `custNm` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `memberDrop`

- Request: `POST` `/classes/com.korail.mobile.login.mbSced.do`
- Source: `com/korail/talk/network/dao/login/LoginService.java:36`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `MileageService`

### `acpnMlgNoti`

- Request: `POST` `/classes/com.korail.mobile.mileage.acpnMlgNoti.do`
- Source: `com/korail/talk/network/dao/mileage/MileageService.java:11`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `retPwd` |
| `Field` | `rcvPsHndyTeln` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `acpnMlgSave`

- Request: `POST` `/classes/com.korail.mobile.mileage.acpnMlgSave.do`
- Source: `com/korail/talk/network/dao/mileage/MileageService.java:15`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `rsvMbCrdNo` |
| `Field` | `custNm` |
| `Field` | `mlgAcmMbCrdNo` |
| `Field` | `saleWctNo` |
| `Field` | `saleDd` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `acpnMlgSpec`

- Request: `POST` `/classes/com.korail.mobile.mileage.acpnMlgSpec.do`
- Source: `com/korail/talk/network/dao/mileage/MileageService.java:19`
- FormUrlEncoded: `Y`
- Return type: `AcpnMlgSpecDao.AcpnMlgSpecResponse` -> model `AcpnMlgSpecResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `tkList` | `List<Ticket>` | `` | `AcpnMlgSpecResponse` |

## `MyTicketService`

### `getTicketList`

- Request: `POST` `/classes/com.korail.mobile.myTicket.MyTicketList`
- Source: `com/korail/talk/network/dao/myTicket/MyTicketService.java:16`
- FormUrlEncoded: `Y`
- Return type: `TicketListDao.TicketListResponse` -> model `TicketListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtDeviceId` |
| `Field` | `txtIndex` |
| `Field` | `h_page_no` |
| `Field` | `h_abrd_dt_from` |
| `Field` | `h_abrd_dt_to` |
| `Field` | `hiduserYn` |
| `Field` | `hidName` |
| `Field` | `hidTeleNo` |
| `Field` | `hidPwd` |
| `Field` | `tsRsStnCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `reservation_list` | `List<ReservationList>` | `` | `TicketListResponse` |

### `procUpgrade`

- Request: `GET` `/classes/com.korail.mobile.myTicket.procUpgradeSeat`
- Source: `com/korail/talk/network/dao/myTicket/MyTicketService.java:20`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `totTxnAmt` |
| `Query` | `totCncRetAmt` |
| `Query` | `totCncRetFee` |
| `Query` | `feeProyStlSqno` |
| `Query` | `lumpStlTgtNo` |
| `Query` | `mnsGridcnt` |
| `Query` | `stlMnsSqno` |
| `Query` | `stlMnsCd` |
| `Query` | `mnsStlAmt` |
| `Query` | `crdInpWayCd` |
| `Query` | `ismtMnthNum` |
| `Query` | `pontDvCd` |
| `Query` | `pontInpDvCd` |
| `Query` | `prepCrdTxnBfAmt` |
| `Query` | `prepCrdTxnAftAmt` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `requestUpgradeSeat`

- Request: `GET` `/classes/com.korail.mobile.myTicket.reqUpgradeSeat`
- Source: `com/korail/talk/network/dao/myTicket/MyTicketService.java:23`
- FormUrlEncoded: `N`
- Return type: `SpecialRoomUpgradeDao.SpecialRoomUpgradeResponse` -> model `SpecialRoomUpgradeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `ogtkSaleDd` |
| `Query` | `ogtkSaleWctNo` |
| `Query` | `ogtkSaleSqno` |
| `Query` | `ogtkRetPwd` |
| `Query` | `jrnyTpCd` |
| `Query` | `jrnySqno` |
| `Query` | `dptDt` |
| `Query` | `dptStnConsOrdr` |
| `Query` | `dptStnRunOrdr` |
| `Query` | `dptRsStnCd` |
| `Query` | `dptTm` |
| `Query` | `arvDt` |
| `Query` | `arvStnConsOrdr` |
| `Query` | `arvStnRunOrdr` |
| `Query` | `arvRsStnCd` |
| `Query` | `arvTm` |
| `Query` | `trnNo` |
| `Query` | `runDt` |
| `Query` | `trnGpCd` |
| `Query` | `roomClsfCd` |
| `Query` | `scarNo` |
| `Query` | `seatNo` |
| `Query` | `rqSeatAttCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `jrnys` | `List<Jrnys>` | `` | `SpecialRoomUpgradeResponse` |
| `ticketInfo` | `TicketInfo` | `` | `SpecialRoomUpgradeResponse` |

## `NFilterService`

### `createKey`

- Request: `POST` `/classes/com.korail.mobile.nFilter.createKey.do`
- Source: `com/korail/talk/network/dao/nFilter/NFilterService.java:10`
- FormUrlEncoded: `Y`
- Return type: `NFilterCreateKeyDao.NFilterCreateKeyResponse` -> model `NFilterCreateKeyResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `publicKey` | `String` | `` | `NFilterCreateKeyResponse` |

## `PassCardService`

### `addDelayTicket`

- Request: `POST` `/classes/com.korail.mobile.passCard.DelayDiscountCheck`
- Source: `com/korail/talk/network/dao/passCard/PassCardService.java:12`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `h_dlay_disc_cnt` |
| `Field` | `h_orgtk_ret_sale_dt` |
| `Field` | `h_orgtk_wct_no` |
| `Field` | `h_orgtk_sale_sqno` |
| `Field` | `h_orgtk_ret_pwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `certDCCoupon`

- Request: `POST` `/classes/com.korail.mobile.passCard.DiscountCheck`
- Source: `com/korail/talk/network/dao/passCard/PassCardService.java:16`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtCertNo` |
| `Field` | `txtCertPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getDelayTicketList`

- Request: `POST` `/classes/com.korail.mobile.passCard.DelayDiscountView`
- Source: `com/korail/talk/network/dao/passCard/PassCardService.java:20`
- FormUrlEncoded: `Y`
- Return type: `DelayTicketListDao.DelayTicketListResponse` -> model `DelayTicketListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dptDtTo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `disc_infos` | `DiscInfos` | `` | `DelayTicketListResponse` |

### `getDiscountCoupon`

- Request: `POST` `/classes/com.korail.mobile.passCard.CouponView`
- Source: `com/korail/talk/network/dao/passCard/PassCardService.java:24`
- FormUrlEncoded: `Y`
- Return type: `DCCouponListDao.DCCouponListResponse` -> model `DCCouponListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtSelPage` |
| `Field` | `pnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `coupon_infos` | `CouponInfos` | `` | `DCCouponListResponse` |
| `h_page_no` | `String` | `` | `DCCouponListResponse` |
| `h_tot_page_cnt` | `String` | `` | `DCCouponListResponse` |

## `PassService`

### `commPayment`

- Request: `POST` `/classes/com.korail.mobile.pass.passPayIssue`
- Source: `com/korail/talk/network/dao/pass/PassService.java:19`
- FormUrlEncoded: `Y`
- Return type: `CommPaymentDao.CommPaymentResponse` -> model `CommPaymentResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidPayAmount` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `main_info` | `PassPaymentDao.MainInfo` | `` | `CommPaymentResponse` |

### `commReservation`

- Request: `POST` `/classes/com.korail.mobile.pass.passReserve`
- Source: `com/korail/talk/network/dao/pass/PassService.java:23`
- FormUrlEncoded: `Y`
- Return type: `CommReservationDao.CommReservationResponse` -> model `CommReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidCmtrKndCd` |
| `Field` | `hidCmtrUtlTrmCd` |
| `Field` | `hidCmtrUtlTrmNm` |
| `Field` | `hidCmtrUtlAgeCd` |
| `Field` | `hidUseOpenDt` |
| `Field` | `hidAppDptStnCd` |
| `Field` | `hidAppDptStnNm` |
| `Field` | `hidAppArvStnCd` |
| `Field` | `hidAppArvStnNm` |
| `Field` | `hidChtrnStnCd` |
| `Field` | `hidChtrnStnNm` |
| `Field` | `hidTrnNo1` |
| `Field` | `hidTrnNo2` |
| `Field` | `hidTrnGpCd1` |
| `Field` | `hidTrnGpCd2` |
| `Field` | `hidDtour1` |
| `Field` | `hidDtour2` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_guide` | `String` | `` | `CommReservationResponse` |
| `main_info` | `MainInfo` | `` | `CommReservationResponse` |

### `getCommRsvInquiry`

- Request: `POST` `/classes/com.korail.mobile.pass.passScheduleInfoList`
- Source: `com/korail/talk/network/dao/pass/PassService.java:27`
- FormUrlEncoded: `Y`
- Return type: `CommRsvInquiryDao.CommRsvInquiryResponse` -> model `CommRsvInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `selGoTrain` |
| `Field` | `selGoAbrdDt` |
| `Field` | `txtGoHour` |
| `Field` | `radChgTrnDvCd` |
| `Field` | `txtCmtrKndCd` |
| `Field` | `txtCmtrUtlTrmCd` |
| `Field` | `txtCmtrUtlAgeCd` |
| `Field` | `txtSelPage` |
| `Field` | `txtCntPerPage` |
| `Field` | `txtGoStart` |
| `Field` | `txtGoEnd` |
| `Field` | `txtWkndUseFlg` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `schedule_info` | `List<ScheduleInfoList>` | `` | `CommRsvInquiryResponse` |

### `getEnableDate`

- Request: `POST` `/classes/com.korail.mobile.pass.passInfoList`
- Source: `com/korail/talk/network/dao/pass/PassService.java:31`
- FormUrlEncoded: `Y`
- Return type: `EnableDateDao.EnableDateResponse` -> model `EnableDateResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtCmtrKndCd` |
| `Field` | `txtCmtrUtlTrmCd` |
| `Field` | `txtCmtrUtlAgeCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `pass_info` | `List<PassInfo>` | `` | `EnableDateResponse` |
| `ticket_info` | `List<Ticket_info>` | `` | `EnableDateResponse` |
| `wct_info` | `List<WctInfo>` | `` | `EnableDateResponse` |

### `passMenu`

- Request: `POST` `/classes/com.korail.mobile.pass.passMenu.do`
- Source: `com/korail/talk/network/dao/pass/PassService.java:35`
- FormUrlEncoded: `Y`
- Return type: `DiscountMenuDao.DiscountMenuResponse` -> model `DiscountMenuResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `menuNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `list` | `List<DiscountMenu>` | `` | `DiscountMenuResponse` |

### `passPayment`

- Request: `POST` `/classes/com.korail.mobile.pass.passOtrPayIssue`
- Source: `com/korail/talk/network/dao/pass/PassService.java:39`
- FormUrlEncoded: `Y`
- Return type: `PassPaymentDao.PassPaymentResponse` -> model `PassPaymentResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidPayAmount` |
| `Field` | `h_rcvd_prc` |
| `Field` | `hidWctNo` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `main_info` | `MainInfo` | `` | `PassPaymentResponse` |

### `passReservation`

- Request: `POST` `/classes/com.korail.mobile.pass.passOtrReserve`
- Source: `com/korail/talk/network/dao/pass/PassService.java:43`
- FormUrlEncoded: `Y`
- Return type: `PassReservationDao.PassReservationResponse` -> model `PassReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidCmtrKndCd` |
| `Field` | `hidCmtrUtlTrmCd` |
| `Field` | `hidCmtrUtlAgeCd` |
| `Field` | `hidUseOpenDt` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `main_info` | `MainInfo` | `` | `PassReservationResponse` |

### `tripMenu`

- Request: `POST` `/classes/com.korail.mobile.pass.trGdMenuLt.do`
- Source: `com/korail/talk/network/dao/pass/PassService.java:47`
- FormUrlEncoded: `Y`
- Return type: `TripMenuDao.TripMenuResponse` -> model `TripMenuResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `menuList` | `List<TripMenu>` | `` | `TripMenuResponse` |
| `poppMsg` | `String` | `` | `TripMenuResponse` |

## `PayService`

### `getPaycoResult`

- Request: `POST` `/classes/com.korail.mobile.payment.reserve.payco.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:22`
- FormUrlEncoded: `Y`
- Return type: `PaycoDao.PaycoPaymentResponse` -> model `PaycoPaymentResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `ticketPrice` |
| `Field` | `ticketName` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `recvData` | `RecvData` | `` | `PaycoPaymentResponse` |

### `getSpayCphdDatVal`

- Request: `POST` `/classes/com.korail.mobile.pay.spayCphdDatVal.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:26`
- FormUrlEncoded: `Y`
- Return type: `SpayCphdDatValDao.SpayCphdDatValResponse` -> model `SpayCphdDatValResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `spayDvCd` |
| `Field` | `data` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `spayCphdDatVal` | `String` | `` | `SpayCphdDatValResponse` |
| `stlCrCrdNo` | `String` | `` | `SpayCphdDatValResponse` |

### `getSpayCphdDatValMonimo`

- Request: `POST` `/classes/com.korail.mobile.pay.monimoDecrypt.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:30`
- FormUrlEncoded: `Y`
- Return type: `SpayCphdDatValMonimoDao.SpayCphdDatValMonimoResponse` -> model `SpayCphdDatValMonimoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `otcNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlCrCrdNo` | `String` | `` | `SpayCphdDatValMonimoResponse` |

### `getSpayOdrNo`

- Request: `POST` `/classes/com.korail.mobile.pay.spayOrdNo.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:34`
- FormUrlEncoded: `Y`
- Return type: `SpayOdrNoDao.SpayOdrNoResponse` -> model `SpayOdrNoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `spayDvCd` |
| `Field` | `totTxnAmt` |
| `Field` | `tgtCnt` |
| `Field` | `encTotTxnAmt` |
| `Field` | `idx` |
| `Field` | `lumpStlTgtNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fllwScnAppUrlAdr` | `String` | `` | `SpayOdrNoResponse` |
| `prprNo` | `String` | `` | `SpayOdrNoResponse` |
| `spayTid` | `String` | `` | `SpayOdrNoResponse` |

### `intgStl`

- Request: `POST` `/classes/com.korail.mobile.pay.intgStl.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:38`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `ctlDvCd` |
| `Field` | `stlPrsJobId` |
| `Field` | `cart_LumpStlTgtNo` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `naverPayMoneyRsv`

- Request: `POST` `/classes/com.korail.mobile.pay.naverPayMoneyRsv.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:42`
- FormUrlEncoded: `Y`
- Return type: `NaverPayRsvDao.NaverPayRsvResponse` -> model `NaverPayRsvResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `productCount` |
| `Field` | `productAmount` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlScnUrl` | `String` | `` | `NaverPayRsvResponse` |

### `naverPayRsv`

- Request: `POST` `/classes/com.korail.mobile.pay.naverPayRsv.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:46`
- FormUrlEncoded: `Y`
- Return type: `NaverPayRsvDao.NaverPayRsvResponse` -> model `NaverPayRsvResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `productCount` |
| `Field` | `productAmount` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlScnUrl` | `String` | `` | `NaverPayRsvResponse` |

### `stbkAcnt`

- Request: `POST` `/classes/com.korail.mobile.pay.stbkAcnt.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:50`
- FormUrlEncoded: `Y`
- Return type: `StbkAcntDao.StbkAcntResponse` -> model `StbkAcntResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `stlBankCd` |
| `Field` | `jobDvCd` |
| `Field` | `acntNo` |
| `Field` | `custCpNo` |
| `Field` | `stbkTxnNo` |
| `Field` | `stlApvPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `custNm` | `String` | `` | `StbkAcntResponse` |
| `stbkTxnNo` | `String` | `` | `StbkAcntResponse` |

### `stbkRegBank`

- Request: `POST` `/classes/com.korail.mobile.pay.stbkRegBank.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:54`
- FormUrlEncoded: `Y`
- Return type: `StbkRegBankDao.StbkRegBankResponse` -> model `StbkRegBankResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `regList` | `List<Reg>` | `` | `StbkRegBankResponse` |
| `regPsbList` | `List<RegPsb>` | `` | `StbkRegBankResponse` |

### `stlKeyPrs`

- Request: `POST` `/classes/com.korail.mobile.pay.stlKeyPrs.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:58`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `jobDvCd` |
| `Field` | `spayDvCd` |
| `Field` | `spayStlKeyVal` |
| `Field` | `stlBankCd` |
| `Field` | `acntNo` |
| `Field` | `binNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `stlKeyQry`

- Request: `POST` `/classes/com.korail.mobile.pay.stlKeyQry.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:62`
- FormUrlEncoded: `Y`
- Return type: `TossAutoStlKeyQryDao.StlKeyQryResponse` -> model `StlKeyQryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `spayDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `spayList` | `List<SimplePayInfo>` | `` | `StlKeyQryResponse` |

### `tossautoC`

- Request: `POST` `/classes/com.korail.mobile.pay.tossautoC.do`
- Source: `com/korail/talk/network/dao/pay/PayService.java:66`
- FormUrlEncoded: `Y`
- Return type: `TossAutoCreateDao.TossAutoCResponse` -> model `TossAutoCResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `billingKey` | `String` | `` | `TossAutoCResponse` |
| `checkoutAndroidUri` | `String` | `` | `TossAutoCResponse` |
| `checkoutIosUri` | `String` | `` | `TossAutoCResponse` |
| `checkoutUri` | `String` | `` | `TossAutoCResponse` |

## `PaymentService`

### `payment`

- Request: `POST` `/classes/com.korail.mobile.payment.ReservationPayment`
- Source: `com/korail/talk/network/dao/payment/PaymentService.java:12`
- FormUrlEncoded: `Y`
- Return type: `RsvPaymentDao.RsvPaymentResponse` -> model `RsvPaymentResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `hidPnrNo` |
| `Field` | `hidWctNo` |
| `Field` | `hidTmpJobSqno1` |
| `Field` | `hidTmpJobSqno2` |
| `Field` | `hidRsvChgNo` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_im_flg` | `String` | `` | `RsvPaymentResponse` |
| `tk_coupon_info` | `List<TkCouponInfo>` | `` | `RsvPaymentResponse` |

## `ProductService`

### `getProductDetail`

- Request: `GET` `/classes/com.korail.mobile.product.ReservationDetail`
- Source: `com/korail/talk/network/dao/product/ProductService.java:12`
- FormUrlEncoded: `N`
- Return type: `ProductDetailDao.ProductDetailResponse` -> model `ProductDetailResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `txtVrRsNo` |
| `Query` | `txtVrRsvSqNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mainInfo` | `ProductInfo` | `` | `ProductDetailResponse` |

### `getProductList`

- Request: `GET` `/classes/com.korail.mobile.product.ReservationList`
- Source: `com/korail/talk/network/dao/product/ProductService.java:15`
- FormUrlEncoded: `N`
- Return type: `ProductListDao.ProductListResponse` -> model `ProductListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `txtSelPage` |
| `Query` | `txtCntPerPage` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mainInfo` | `MainInfo` | `` | `ProductListResponse` |

### `paymentCheck`

- Request: `GET` `/classes/com.korail.mobile.product.payInfo`
- Source: `com/korail/talk/network/dao/product/ProductService.java:18`
- FormUrlEncoded: `N`
- Return type: `ProductPaymentCheckDao.ProductPaymentCheckResponse` -> model `ProductPaymentCheckResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `txtVrRsNo` |
| `Query` | `txtRsvGdSqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mainInfo` | `MainInfo` | `` | `ProductPaymentCheckResponse` |

### `productCancel`

- Request: `GET` `/classes/com.korail.mobile.product.ReservationCancel`
- Source: `com/korail/talk/network/dao/product/ProductService.java:21`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `txtVrRsNo` |
| `Query` | `txtGdSqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `PushService`

### `callCrew`

- Request: `GET` `/classes/com.korail.mobile.push.callCrew.do`
- Source: `com/korail/talk/network/dao/push/PushService.java:13`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `pnrNo` |
| `Query` | `jrnySqno` |
| `Query` | `saleWctNo` |
| `Query` | `saleDt` |
| `Query` | `saleSqno` |
| `Query` | `tkRetPwd` |
| `Query` | `sndSqno` |
| `Query` | `coutMsgDvCd` |
| `Query` | `intgMsgCd1` |
| `Query` | `intgMsgCd2` |
| `Query` | `intgMsgCd3` |
| `Query` | `intgMsgCd4` |
| `Query` | `intgMsgCd5` |
| `Query` | `intgMsgCd6` |
| `Query` | `intgMsgCd7` |
| `Query` | `intgMsgCd8` |
| `Query` | `intgMsgCd9` |
| `Query` | `intgMsgCd10` |
| `Query` | `intgMsgCont` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `callCrewRequestList`

- Request: `GET` `/classes/com.korail.mobile.push.crwCallRq.do`
- Source: `com/korail/talk/network/dao/push/PushService.java:16`
- FormUrlEncoded: `N`
- Return type: `CallCrewRequestListDao.CallCrewListResponse` -> model `CallCrewListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `qryDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `prsList` | `List<PrsList>` | `` | `CallCrewListResponse` |

### `cmtrKndPassMenu`

- Request: `GET` `/classes/com.korail.mobile.push.cmtrKnd.do`
- Source: `com/korail/talk/network/dao/push/PushService.java:19`
- FormUrlEncoded: `N`
- Return type: `CmtrKndMenuDao.CmtrKndMenuResponse` -> model `CmtrKndMenuResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `cmtrKndCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `afterDay` | `String` | `` | `CmtrKndMenuResponse` |
| `agree` | `String` | `` | `CmtrKndMenuResponse` |
| `information` | `String` | `` | `CmtrKndMenuResponse` |
| `passData` | `DiscountMenuDao.PassMainInfo` | `` | `CmtrKndMenuResponse` |
| `title` | `String` | `` | `CmtrKndMenuResponse` |

### `pushUpdate`

- Request: `GET` `/classes/com.korail.mobile.push.update`
- Source: `com/korail/talk/network/dao/push/PushService.java:22`
- FormUrlEncoded: `N`
- Return type: `PushUpdateDao.PushUpdateResponse` -> model `PushUpdateResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `job_dv_cd` |
| `Query` | `tnsm_flg1` |
| `Query` | `tnsm_flg2` |
| `Query` | `tnsm_flg3` |
| `Query` | `tnsm_flg4` |
| `Query` | `dptUsrInpTnum` |
| `Query` | `arvUsrInpTnum` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `arvUsrInpTnum` | `String` | `` | `PushUpdateResponse` |
| `dptUsrInpTnum` | `String` | `` | `PushUpdateResponse` |
| `prs_cnqe_msg_cd` | `String` | `` | `PushUpdateResponse` |
| `tnsm_flg1` | `String` | `` | `PushUpdateResponse` |
| `tnsm_flg2` | `String` | `` | `PushUpdateResponse` |
| `tnsm_flg3` | `String` | `` | `PushUpdateResponse` |
| `tnsm_flg4` | `String` | `` | `PushUpdateResponse` |

## `RailPlusService`

### `getAutoCharge`

- Request: `GET` `/classes/com.korail.mobile.railplus.autoCharge.do`
- Source: `com/korail/talk/network/dao/railplus/RailPlusService.java:9`
- FormUrlEncoded: `N`
- Return type: `AutoChargeDao.AutoChargeResponse` -> model `AutoChargeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `jobDvCd` |
| `Query` | `prepCrdNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `psbFlg` | `String` | `` | `AutoChargeResponse` |

## `ReceiptService`

### `getTicketReceipt`

- Request: `POST` `/classes/com.korail.mobile.receipt.ReceiptInfo`
- Source: `com/korail/talk/network/dao/receipt/ReceiptService.java:10`
- FormUrlEncoded: `Y`
- Return type: `ReceiptDao.ReceiptResponse` -> model `ReceiptResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `h_orgtk_sale_dt` |
| `Field` | `h_orgtk_wct_no` |
| `Field` | `h_orgtk_sale_sqno` |
| `Field` | `h_orgtk_tk_ret_pwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `receipt_infos` | `ReceiptInfos` | `` | `ReceiptResponse` |

## `RefundService`

### `executeOnlineRefunds`

- Request: `POST` `/classes/com.korail.mobile.refunds.executeOnlineRefunds`
- Source: `com/korail/talk/network/dao/refund/RefundService.java:15`
- FormUrlEncoded: `Y`
- Return type: `RefundExecuteTicketRefundDao.RefundExecuteTicketRefundResponse` -> model `RefundExecuteTicketRefundResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `tkKndCd` |
| `Field` | `retDvCd` |
| `Field` | `retRsnCd` |
| `Field` | `ogtkSaleDt` |
| `Field` | `ogtkSaleWctNo` |
| `Field` | `ogtkSaleSqno` |
| `Field` | `ogtkRetPwd` |
| `Field` | `retAmt` |
| `Field` | `retFee` |
| `Field` | `custTeln` |
| `Field` | `acepCustNm` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_ret_dv_cd` | `String` | `` | `RefundExecuteTicketRefundResponse` |

### `getTicketCommission`

- Request: `POST` `/classes/com.korail.mobile.refunds.CommissionView`
- Source: `com/korail/talk/network/dao/refund/RefundService.java:19`
- FormUrlEncoded: `Y`
- Return type: `RefundCommissionDao.RefundCommissionResponse` -> model `RefundCommissionResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `h_orgtk_ret_sale_dt` |
| `Field` | `h_orgtk_wct_no` |
| `Field` | `h_orgtk_sale_sqno` |
| `Field` | `h_orgtk_ret_pwd` |
| `Field` | `h_comp_nm` |
| `Field` | `h_comp_cert_no` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_msg_cd2` | `String` | `` | `RefundCommissionResponse` |
| `h_msg_txt2` | `String` | `` | `RefundCommissionResponse` |
| `prg_psb_flg` | `String` | `` | `RefundCommissionResponse` |
| `ret_amt` | `String` | `` | `RefundCommissionResponse` |
| `ret_fee` | `String` | `` | `RefundCommissionResponse` |
| `tk_ret_tms_dv_cd` | `String` | `` | `RefundCommissionResponse` |
| `use_psb_mlg_num` | `String` | `` | `RefundCommissionResponse` |

### `getTicketDetail`

- Request: `POST` `/classes/com.korail.mobile.refunds.SelTicketInfo`
- Source: `com/korail/talk/network/dao/refund/RefundService.java:23`
- FormUrlEncoded: `Y`
- Return type: `TicketDetailDao.TicketDetailResponse` -> model `TicketDetailResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `h_orgtk_ret_sale_dt` |
| `Field` | `h_orgtk_wct_no` |
| `Field` | `h_orgtk_sale_sqno` |
| `Field` | `h_orgtk_ret_pwd` |
| `Field` | `h_purchase_history` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `addSrvCancel` | `String` | `` | `TicketDetailResponse` |
| `addSrvFlg` | `String` | `` | `TicketDetailResponse` |
| `addSrvList` | `AddSrvList` | `` | `TicketDetailResponse` |
| `cmpa_info` | `List<CompanionInfo>` | `` | `TicketDetailResponse` |
| `cstmzPhrase` | `String` | `` | `TicketDetailResponse` |
| `dcnt_crd_info` | `DiscountCardInfo` | `` | `TicketDetailResponse` |
| `dtlList` | `List<DelayInfo>` | `` | `TicketDetailResponse` |
| `gurdSmsFlg` | `String` | `` | `TicketDetailResponse` |
| `h_abrd_ps_nm` | `String` | `` | `TicketDetailResponse` |
| `h_abrd_ps_sex` | `String` | `` | `TicketDetailResponse` |
| `h_cmtr_utl_trm_age_cd` | `String` | `` | `TicketDetailResponse` |
| `h_cmtr_utl_trm_cd_nm` | `String` | `` | `TicketDetailResponse` |
| `h_compa_brth` | `String` | `` | `TicketDetailResponse` |
| `h_compa_nm` | `String` | `` | `TicketDetailResponse` |
| `h_dlay_flg` | `String` | `` | `TicketDetailResponse` |
| `h_dlay_tk_flg` | `String` | `` | `TicketDetailResponse` |
| `h_dscp_no` | `String` | `` | `TicketDetailResponse` |
| `h_dtour` | `String` | `` | `TicketDetailResponse` |
| `h_orgtk_ret_pwd` | `String` | `` | `TicketDetailResponse` |
| `h_orgtk_ret_sale_dt` | `String` | `` | `TicketDetailResponse` |
| `h_orgtk_sale_sqno` | `String` | `` | `TicketDetailResponse` |
| `h_orgtk_wct_no` | `String` | `` | `TicketDetailResponse` |
| `h_pbp_acep_tgt_flg` | `String` | `` | `TicketDetailResponse` |
| `h_pnr_no` | `String` | `` | `TicketDetailResponse` |
| `h_qrcode` | `String` | `` | `TicketDetailResponse` |
| `h_ret_flg` | `String` | `` | `TicketDetailResponse` |
| `h_sale_dt` | `String` | `` | `TicketDetailResponse` |
| `h_sale_tm` | `String` | `` | `TicketDetailResponse` |
| `h_schd_tk_knd_cd` | `String` | `` | `TicketDetailResponse` |
| `h_tk_knd_cd` | `String` | `` | `TicketDetailResponse` |
| `h_tk_knd_nm` | `String` | `` | `TicketDetailResponse` |
| `h_tot_disc_amt` | `String` | `` | `TicketDetailResponse` |
| `h_tot_fare_amt` | `String` | `` | `TicketDetailResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `TicketDetailResponse` |
| `h_trn_running_flg` | `String` | `` | `TicketDetailResponse` |
| `h_wct_nm` | `String` | `` | `TicketDetailResponse` |
| `limousine` | `Limousine` | `` | `TicketDetailResponse` |
| `limousineRsvPsbFlg` | `String` | `` | `TicketDetailResponse` |
| `mlgSaveFlg` | `String` | `` | `TicketDetailResponse` |
| `parkingLotUrl` | `String` | `` | `TicketDetailResponse` |
| `pbpAcepPsQryFlg` | `String` | `` | `TicketDetailResponse` |
| `pbpAcepPsbFlg` | `String` | `` | `TicketDetailResponse` |
| `psgNmList` | `List<FamilyInfo>` | `` | `TicketDetailResponse` |
| `retPsbFlg` | `String` | `` | `TicketDetailResponse` |
| `s_brth` | `String` | `` | `TicketDetailResponse` |
| `seatAppPsbFlg` | `String` | `` | `TicketDetailResponse` |
| `stnLeadFlg` | `String` | `` | `TicketDetailResponse` |
| `stndAppPsbFlg` | `String` | `` | `TicketDetailResponse` |
| `ticketTimeBgColor` | `String` | `` | `TicketDetailResponse` |
| `ticket_infos` | `TicketInfos` | `` | `TicketDetailResponse` |
| `tripChgFlg` | `String` | `` | `TicketDetailResponse` |
| `whchSrvRcpFlg` | `String` | `` | `TicketDetailResponse` |
| `whchSrvReqPsbFlg` | `String` | `` | `TicketDetailResponse` |

### `returnTicket`

- Request: `POST` `/classes/com.korail.mobile.refunds.RefundsRequest`
- Source: `com/korail/talk/network/dao/refund/RefundService.java:27`
- FormUrlEncoded: `Y`
- Return type: `RefundDao.RefundResponse` -> model `RefundResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtPnrNo` |
| `Field` | `h_orgtk_sale_dt` |
| `Field` | `h_orgtk_sale_wct_no` |
| `Field` | `h_orgtk_sale_sqno` |
| `Field` | `h_orgtk_ret_pwd` |
| `Field` | `h_mlg_stl` |
| `Field` | `tk_ret_tms_dv_cd` |
| `Field` | `trnNo` |
| `Field` | `pbpAcepTgtFlg` |
| `Field` | `latitude` |
| `Field` | `longitude` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `stlList` | `List<StlList>` | `` | `RefundResponse` |
| `ticketList` | `List<TicketList>` | `` | `RefundResponse` |
| `whlPgNum` | `int` | `` | `RefundResponse` |

### `verifyOnlineRefunds`

- Request: `POST` `/classes/com.korail.mobile.refunds.verifyOnlineRefunds`
- Source: `com/korail/talk/network/dao/refund/RefundService.java:31`
- FormUrlEncoded: `Y`
- Return type: `RefundVerifyTicketDao.RefundVerifyTicketResponse` -> model `RefundVerifyTicketResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `retNo1` |
| `Field` | `retNo2` |
| `Field` | `retNo3` |
| `Field` | `retNo4` |
| `Field` | `strName` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `orgtkinfo_list` | `ArrayList<Orgtkinfo>` | `` | `RefundVerifyTicketResponse` |
| `poppMsg` | `String` | `` | `RefundVerifyTicketResponse` |
| `rcvd_amt` | `String` | `` | `RefundVerifyTicketResponse` |
| `ret_amt` | `String` | `` | `RefundVerifyTicketResponse` |
| `ret_fee` | `String` | `` | `RefundVerifyTicketResponse` |

## `ResearchService`

### `getAssignScheduleView`

- Request: `POST` `/classes/com.korail.mobile.research.assignScheduleView.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:31`
- FormUrlEncoded: `Y`
- Return type: `SeatAssignScheduleViewDao.SeatAssignScheduleViewResponse` -> model `SeatAssignScheduleViewResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `menuId` |
| `Field` | `dptDt` |
| `Field` | `dptTm` |
| `Field` | `dptRsStnNm` |
| `Field` | `arvRsStnNm` |
| `Field` | `trnGpCd` |
| `Field` | `psrmClCd` |
| `Field` | `seatAttCd1` |
| `Field` | `psgNum1` |
| `Field` | `stlbDturDvNm1` |
| `Field` | `dirtChtnDvCd` |
| `Field` | `chtnArvRsStnNm` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_next_pg_flg` | `String` | `` | `SeatAssignScheduleViewResponse` |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | `` | `SeatAssignScheduleViewResponse` |

### `getCarList`

- Request: `POST` `/classes/com.korail.mobile.research.TrainResearch`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:35`
- FormUrlEncoded: `Y`
- Return type: `SearchCarListDao.SearchCarListResponse` -> model `SearchCarListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `Sid` |
| `Field` | `txtMenuId` |
| `Field` | `txtPsrmClCd` |
| `Field` | `txtRunDt` |
| `Field` | `txtDptDt` |
| `Field` | `txtTrnClsfCd` |
| `Field` | `txtTrnNo` |
| `Field` | `txtDptRsStnCd` |
| `Field` | `txtArvRsStnCd` |
| `Field` | `txtDptStnRunOrdr` |
| `Field` | `txtArvStnRunOrdr` |
| `Field` | `txtTrnGpCd` |
| `Field` | `txtTotPsgCnt` |
| `Field` | `txtSeatAttCd` |
| `Field` | `txtGdNo` |
| `Field` | `sidTest` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_rcmd_srcar_no` | `int` | `` | `SearchCarListResponse` |
| `h_trn_no` | `String` | `` | `SearchCarListResponse` |
| `srcar_infos` | `CarInfos` | `` | `SearchCarListResponse` |

### `getCmtrInfo`

- Request: `POST` `/classes/com.korail.mobile.research.cmtrInfo.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:39`
- FormUrlEncoded: `Y`
- Return type: `CmtrInfoDao.CmtrInfoResponse` -> model `CmtrInfoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `jobDvCd` |
| `Field` | `cmtrKndCd` |
| `Field` | `psgCnt` |
| `Field` | `cmtrUtlAgeCd` |
| `Field` | `psgPrnb` |
| `Field` | `ogtkSaleWctNo` |
| `Field` | `ogtkSaleDd` |
| `Field` | `ogtkSaleSqno` |
| `Field` | `ogtkRetPwd` |
| `Field` | `inquiryType` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `addSrvGdFlg` | `String` | `` | `CmtrInfoResponse` |
| `avlPrnbFrom` | `int` | `` | `CmtrInfoResponse` |
| `avlPrnbTo` | `int` | `` | `CmtrInfoResponse` |
| `cmpaFlg` | `String` | `` | `CmtrInfoResponse` |
| `cmtrKndCd` | `String` | `` | `CmtrInfoResponse` |
| `cmtrUtlAgeCd` | `String` | `` | `CmtrInfoResponse` |
| `menuId` | `String` | `` | `CmtrInfoResponse` |
| `poppMsg` | `String` | `` | `CmtrInfoResponse` |
| `prmoMsg` | `String` | `` | `CmtrInfoResponse` |
| `prmoUrl` | `String` | `` | `CmtrInfoResponse` |
| `psgList` | `List<Psg>` | `` | `CmtrInfoResponse` |
| `seatAttCd1` | `String` | `` | `CmtrInfoResponse` |

### `getCustTripInfo`

- Request: `POST` `/classes/com.korail.mobile.research.custTripInfo.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:43`
- FormUrlEncoded: `Y`
- Return type: `ConvenienceSettingDao.ConvenienceSettingResponse` -> model `ConvenienceSettingResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `custMgNo` |
| `Field` | `medDvCd` |
| `Field` | `regSqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `mainList` | `List<CustTripInfo>` | `` | `ConvenienceSettingResponse` |

### `getMergeSeatsInquiry`

- Request: `POST` `/classes/com.korail.mobile.research.mergeSeatsC.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:47`
- FormUrlEncoded: `Y`
- Return type: `MergeSeatInquiryDao.MergeSeatInquiryResponse` -> model `MergeSeatInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `abrdDt` |
| `Field` | `runDt` |
| `Field` | `trnNo` |
| `Field` | `dptRsStnNm` |
| `Field` | `arvRsStnNm` |
| `Field` | `selRsStnNm` |
| `Field` | `psrmClCd` |
| `Field` | `seatAttCd` |
| `Field` | `totPsgNum` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `midStnList` | `List<MidStnList.MidStationInfo>` | `` | `MergeSeatInquiryResponse` |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | `` | `MergeSeatInquiryResponse` |

### `getNCardHistory`

- Request: `GET` `/classes/com.korail.mobile.ticket.dcntCrdUseQry.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:51`
- FormUrlEncoded: `N`
- Return type: `NCardHistoryDao.NCardHistoryResponse` -> model `NCardHistoryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `dcntCrdNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `tkUseList` | `List<NCardHistoryInfo>` | `` | `NCardHistoryResponse` |

### `getNCardSchedultView`

- Request: `GET` `/classes/com.korail.mobile.research.dcntCrdScheduleView.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:54`
- FormUrlEncoded: `N`
- Return type: `NCardInquiryDao.NCardInquiryResponse` -> model `NCardInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `dptDt` |
| `Query` | `dptRsStnNm` |
| `Query` | `arvRsStnNm` |
| `Query` | `dptTm` |
| `Query` | `trnGpCd` |
| `Query` | `dirtChtnDvCd` |
| `Query` | `dcntCrdKndCd` |
| `Query` | `dcntCrdKndMgNo` |
| `Query` | `useTrmDno` |
| `Query` | `usePsbTno` |
| `Query` | `qryPgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fllwPgExt` | `String` | `` | `NCardInquiryResponse` |
| `trnScdlList` | `List<TrainInfo>` | `` | `NCardInquiryResponse` |

### `getSeatList`

- Request: `POST` `/classes/com.korail.mobile.research.TResidualSeatsResearch.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:57`
- FormUrlEncoded: `Y`
- Return type: `SearchSeatListDao.SearchSeatListResponse` -> model `SearchSeatListResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `trnClsfCd` |
| `Field` | `trnGpCd` |
| `Field` | `runDt` |
| `Field` | `trnNo` |
| `Field` | `srcarNo` |
| `Field` | `psrmClCd` |
| `Field` | `dptRsStnCd` |
| `Field` | `arvRsStnCd` |
| `Field` | `seatAttCd` |
| `Field` | `dptStnRunOrdr` |
| `Field` | `arvStnRunOrdr` |
| `Field` | `totPsgCnt` |
| `Field` | `gdNo` |
| `Field` | `isArrow` |
| `Field` | `Sid` |
| `Field` | `sidTest` |
| `Field` | `ctlDvCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `layout_type` | `int` | `` | `SearchSeatListResponse` |
| `seatList` | `List<Seat>` | `` | `SearchSeatListResponse` |
| `seat_ary_cd` | `String` | `` | `SearchSeatListResponse` |
| `seat_remain_count` | `int` | `` | `SearchSeatListResponse` |
| `seat_total_count` | `int` | `` | `SearchSeatListResponse` |
| `vrBnrUrl` | `String` | `` | `SearchSeatListResponse` |
| `windowList` | `List<Window>` | `` | `SearchSeatListResponse` |

### `getTicketOriginalInquiry`

- Request: `POST` `/classes/com.korail.mobile.research.tripChgOgtk.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:61`
- FormUrlEncoded: `Y`
- Return type: `OgTkInquiryDao.OgTkInquiryResponse` -> model `OgTkInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `orgTkList` | `List<OrgTk>` | `` | `OgTkInquiryResponse` |

### `setNCardExtension`

- Request: `GET` `/classes/com.korail.mobile.reservation.dcntCrdExtn.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:65`
- FormUrlEncoded: `N`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |
| `Query` | `saleWctNo` |
| `Query` | `saleDd` |
| `Query` | `saleSqno` |
| `Query` | `tkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `setNCardReservation`

- Request: `POST` `/classes/com.korail.mobile.research.dcntCrdInfo.do`
- Source: `com/korail/talk/network/dao/research/ResearchService.java:68`
- FormUrlEncoded: `Y`
- Return type: `NCardReservationDao.NCardReservationResponse` -> model `NCardReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dcntCrdKndMgNo` |
| `Field` | `custMgNo` |
| `Field` | `vlidTrmStDt` |
| `Field` | `usePsbTno` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `lumpStlTgtNo` | `String` | `` | `NCardReservationResponse` |
| `mStationInfo` | `String` | `` | `NCardReservationResponse` |
| `mUserNames` | `String` | `` | `NCardReservationResponse` |
| `rcvdAmt` | `String` | `` | `NCardReservationResponse` |
| `usePsbTno` | `String` | `` | `NCardReservationResponse` |
| `vlidTrmClsDt` | `String` | `` | `NCardReservationResponse` |
| `vlidTrmStDt` | `String` | `` | `NCardReservationResponse` |

## `ReservationCancelService`

### `reservationCancel`

- Request: `POST` `/classes/com.korail.mobile.reservationCancel.ReservationCancel`
- Source: `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:15`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtPnrNo` |
| `Field` | `txtJrnySqno` |
| `Field` | `txtJrnyCnt` |
| `Field` | `hidRsvChgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `reservationCancelCheck`

- Request: `POST` `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk`
- Source: `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:19`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtPnrNo` |
| `Field` | `txtJrnySqno` |
| `Field` | `txtJrnyCnt` |
| `Field` | `hidRsvChgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `reservationChange`

- Request: `POST` `/classes/com.korail.mobile.reservation.reservationChange.do`
- Source: `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:23`
- FormUrlEncoded: `Y`
- Return type: `ReservationChangeDao.ReservationChangeResponse` -> model `ReservationChangeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `chgTno` |
| `Field` | `totPrnb` |
| `Field` | `stndFlg` |
| `Field` | `evntWctFlg` |
| `Field` | `wctHndgCncDvCd` |
| `Field` | `lrgCrgFlg` |
| `Field` | `psgCnt` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `jrnyList` | `List<JrnyInfo>` | `` | `ReservationChangeResponse` |

## `ReservationService`

### `getGuideSeatCnd`

- Request: `POST` `/classes/com.korail.mobile.reservation.guideSeatCnd.do`
- Source: `com/korail/talk/network/dao/reservation/ReservationService.java:17`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `rqSeatAttCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getRsvHistory`

- Request: `GET` `/classes/com.korail.mobile.reservation.ReservationView`
- Source: `com/korail/talk/network/dao/reservation/ReservationService.java:21`
- FormUrlEncoded: `N`
- Return type: `TicketRsvHistoryDao.TicketRsvHistoryResponse` -> model `TicketRsvHistoryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Query` | `Device` |
| `Query` | `Version` |
| `Query` | `Key` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `TicketRsvHistoryResponse` |

### `getTicketChangeReservation`

- Request: `POST` `/classes/com.korail.mobile.reservation.tripChgPrsC.do`
- Source: `com/korail/talk/network/dao/reservation/ReservationService.java:24`
- FormUrlEncoded: `Y`
- Return type: `ReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `trvlKndCd` |
| `Field` | `totPrnb` |
| `Field` | `isePrnb` |
| `Field` | `stndSeatFlg` |
| `Field` | `intgTktIseFlg` |
| `Field` | `prcFareReCalcFlg` |
| `Field` | `tmpJobSqno` |
| `Field` | `alcSeatDmnPsDvCd` |
| `Field` | `jrny2Cnt` |
| `Field` | `psg2Cnt` |
| `Field` | `ctlDvCd` |
| `Field` | `frcSaleRsnCont` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

### `setSeatAssignReservation`

- Request: `POST` `/classes/com.korail.mobile.reservation.seatAssign.do`
- Source: `com/korail/talk/network/dao/reservation/ReservationService.java:28`
- FormUrlEncoded: `Y`
- Return type: `SeatAssignReservationDao.SeatAssignReservationResponse` -> model `SeatAssignReservationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `menuId` |
| `Field` | `custMgNo` |
| `Field` | `totPrnb` |
| `Field` | `stndFlg` |
| `Field` | `rqScarNum` |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dfpyList` | `List<Dfpy>` | `` | `ReservationResponse` |
| `h_add_srv_flg` | `String` | `` | `ReservationResponse` |
| `h_cust_mg_no` | `String` | `` | `ReservationResponse` |
| `h_fmly_info_cfm_flg` | `String` | `` | `ReservationResponse` |
| `h_hdcp_ctfc_num` | `int` | `` | `ReservationResponse` |
| `h_ise_psb_dt` | `String` | `` | `ReservationResponse` |
| `h_ise_psb_tm` | `String` | `` | `ReservationResponse` |
| `h_jrny_cnt` | `String` | `` | `ReservationResponse` |
| `h_msg_mndry` | `String` | `` | `ReservationResponse` |
| `h_msg_txt5` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_dt` | `String` | `` | `ReservationResponse` |
| `h_ntisu_lmt_tm` | `String` | `` | `ReservationResponse` |
| `h_pay_limit_msg` | `String` | `` | `ReservationResponse` |
| `h_payment_flg` | `String` | `` | `ReservationResponse` |
| `h_payment_msg` | `String` | `` | `ReservationResponse` |
| `h_pnr_no` | `String` | `` | `ReservationResponse` |
| `h_pre_stl_tgt_flg` | `String` | `` | `ReservationResponse` |
| `h_sprm_fare` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno1` | `String` | `` | `ReservationResponse` |
| `h_tmp_job_sqno2` | `String` | `` | `ReservationResponse` |
| `h_tot_dcnt_amt` | `String` | `` | `ReservationResponse` |
| `h_tot_fare` | `String` | `` | `ReservationResponse` |
| `h_tot_prc` | `String` | `` | `ReservationResponse` |
| `h_tot_rcvd_amt` | `String` | `` | `ReservationResponse` |
| `h_wct_no` | `String` | `` | `ReservationResponse` |
| `jrny_infos` | `JrnyInfos` | `` | `ReservationResponse` |
| `ogtkRcvdAmt` | `int` | `` | `ReservationResponse` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | `ReservationResponse` |
| `psg_infos` | `PsgInfos` | `` | `ReservationResponse` |
| `scnIndcAmt` | `int` | `` | `ReservationResponse` |
| `stopStnList` | `List<StopStn>` | `` | `ReservationResponse` |
| `tkList` | `List<TK>` | `` | `ReservationResponse` |
| `totRetAmt` | `int` | `` | `ReservationResponse` |

## `ReservationWaitService`

### `rsvWait`

- Request: `POST` `/classes/com.korail.mobile.reservationWait.ReservationWait`
- Source: `com/korail/talk/network/dao/reservationWait/ReservationWaitService.java:10`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtPnrNo` |
| `Field` | `txtPsrmClChgFlg` |
| `Field` | `txtSmsSndFlg` |
| `Field` | `txtCpNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `SeatMovieService`

### `getRsvInquiry`

- Request: `POST` `/classes/com.korail.mobile.seatMovie.ScheduleView`
- Source: `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12`
- FormUrlEncoded: `Y`
- Return type: `RsvInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Sid` |
| `Field` | `txtMenuId` |
| `Field` | `radJobId` |
| `Field` | `selGoTrain` |
| `Field` | `txtTrnGpCd` |
| `Field` | `txtGoTrnNo` |
| `Field` | `txtGoStart` |
| `Field` | `txtGoEnd` |
| `Field` | `txtGoAbrdDt` |
| `Field` | `txtGoHour` |
| `Field` | `txtPsgFlg_1` |
| `Field` | `txtPsgFlg_2` |
| `Field` | `txtPsgFlg_3` |
| `Field` | `txtPsgFlg_4` |
| `Field` | `txtPsgFlg_5` |
| `Field` | `txtSeatAttCd_2` |
| `Field` | `txtSeatAttCd_3` |
| `Field` | `txtSeatAttCd_4` |
| `Field` | `txtJobDv` |
| `Field` | `etrPath` |
| `Field` | `tkDptDt` |
| `Field` | `tkDptTm` |
| `Field` | `tkTrnNo` |
| `Field` | `ebizCrossCheck` |
| `Field` | `srtCheckYn` |
| `Field` | `rtYn` |
| `Field` | `adjStnScdlOfrFlg` |
| `Field` | `mbCrdNo` |
| `Field` | `tkPsrmClCd` |
| `Field` | `tkRcvdAmt` |
| `Field` | `qryDvCd` |
| `Field` | `qryStNo` |
| `Field` | `qryStTrnNo` |
| `Field` | `qryStTrnNo2` |
| `Field` | `pgPrCnt` |
| `Field` | `chtnCnt` |
| `Field` | `chtnRsStnCd1` |
| `Field` | `trnGpCnt` |
| `Field` | `trnGpCd1` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_ectb_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_gd_no` | `String` | `` | `RsvInquiryResponse` |
| `h_next_pg_flg` | `String` | `` | `RsvInquiryResponse` |
| `h_notice_msg` | `String` | `` | `RsvInquiryResponse` |
| `h_prcd_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_qry_st_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_rslt_cnt` | `String` | `` | `RsvInquiryResponse` |
| `h_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `trn_infos` | `TrainInfos` | `` | `RsvInquiryResponse` |

### `getRsvLimousineInquiry`

- Request: `POST` `/classes/com.korail.mobile.seatMovie.LimousineScheduleView`
- Source: `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:16`
- FormUrlEncoded: `Y`
- Return type: `RsvInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Sid` |
| `Field` | `txtMenuId` |
| `Field` | `radJobId` |
| `Field` | `txtJobDv` |
| `Field` | `selGoTrain` |
| `Field` | `txtTrnGpCd` |
| `Field` | `txtGoTrnNo` |
| `Field` | `txtGoStart` |
| `Field` | `txtGoEnd` |
| `Field` | `txtGoAbrdDt` |
| `Field` | `txtGoHour` |
| `Field` | `txtPsgFlg_1` |
| `Field` | `txtPsgFlg_2` |
| `Field` | `txtPsgFlg_3` |
| `Field` | `txtPsgFlg_4` |
| `Field` | `txtPsgFlg_5` |
| `Field` | `txtSeatAttCd_2` |
| `Field` | `txtSeatAttCd_3` |
| `Field` | `txtSeatAttCd_4` |
| `Field` | `ebizCrossCheck` |
| `Field` | `srtCheckYn` |
| `Field` | `rtYn` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_ectb_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_gd_no` | `String` | `` | `RsvInquiryResponse` |
| `h_next_pg_flg` | `String` | `` | `RsvInquiryResponse` |
| `h_notice_msg` | `String` | `` | `RsvInquiryResponse` |
| `h_prcd_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_qry_st_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_rslt_cnt` | `String` | `` | `RsvInquiryResponse` |
| `h_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `trn_infos` | `TrainInfos` | `` | `RsvInquiryResponse` |

### `getRsvProductInquiry`

- Request: `POST` `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
- Source: `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20`
- FormUrlEncoded: `Y`
- Return type: `RsvInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `txtMenuId` |
| `Field` | `radJobId` |
| `Field` | `selGoTrain` |
| `Field` | `txtTrnGpCd` |
| `Field` | `txtGoStart` |
| `Field` | `txtGoEnd` |
| `Field` | `txtGoAbrdDt` |
| `Field` | `txtGoHour` |
| `Field` | `txtPsgFlg_1` |
| `Field` | `txtPsgFlg_2` |
| `Field` | `txtPsgFlg_3` |
| `Field` | `txtPsgFlg_4` |
| `Field` | `txtPsgFlg_5` |
| `Field` | `txtSeatAttCd_2` |
| `Field` | `txtSeatAttCd_3` |
| `Field` | `txtSeatAttCd_4` |
| `Field` | `txtGdNo` |
| `Field` | `qryDvCd` |
| `Field` | `qryStNo` |
| `Field` | `qryStTrnNo` |
| `Field` | `qryStTrnNo2` |
| `Field` | `pgPrCnt` |
| `Field` | `chtnCnt` |
| `Field` | `chtnRsStnCd1` |
| `Field` | `trnGpCnt` |
| `Field` | `trnGpCd1` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_ectb_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_gd_no` | `String` | `` | `RsvInquiryResponse` |
| `h_next_pg_flg` | `String` | `` | `RsvInquiryResponse` |
| `h_notice_msg` | `String` | `` | `RsvInquiryResponse` |
| `h_prcd_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_qry_st_no_next` | `String` | `` | `RsvInquiryResponse` |
| `h_rslt_cnt` | `String` | `` | `RsvInquiryResponse` |
| `h_trn_no_next` | `String` | `` | `RsvInquiryResponse` |
| `trn_infos` | `TrainInfos` | `` | `RsvInquiryResponse` |

## `TicketService`

### `deviceReset`

- Request: `POST` `/classes/com.korail.mobile.tk.dvcInfoInit.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:26`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `teln` |
| `Field` | `custNm` |
| `Field` | `nonMbPwd` |
| `Field` | `stlbTrnClsfCd` |
| `Field` | `dptDttm` |
| `Field` | `latitude` |
| `Field` | `longitude` |
| `Field` | `trnNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `dlvRcvCust`

- Request: `POST` `/classes/com.korail.mobile.tk.dlvRcvCust.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:30`
- FormUrlEncoded: `Y`
- Return type: `DlvRcvCustDao.DlvRcvCustwResponse` -> model `DlvRcvCustwResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `acepCustMgNo` | `String` | `` | `DlvRcvCustwResponse` |
| `acepCustNm` | `String` | `` | `DlvRcvCustwResponse` |
| `acepCustTeln` | `String` | `` | `DlvRcvCustwResponse` |
| `mbCrdNo` | `String` | `` | `DlvRcvCustwResponse` |

### `duplicationCheck`

- Request: `POST` `/classes/com.korail.mobile.ticket.ticketDupCheck.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:34`
- FormUrlEncoded: `Y`
- Return type: `TicketDuplicationCheckDao.DuplicationCheckResponse` -> model `DuplicationCheckResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `rsvCnt` | `int` | `` | `DuplicationCheckResponse` |

### `getMaasCancel`

- Request: `POST` `/classes//com.korail.mobile.addService.cancelPay.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:38`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `custMgNo` |
| `Field` | `lumpStlTgtNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getMaasServiceCancel`

- Request: `POST` `/classes/com.korail.mobile.addService.coptCnc.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:42`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `pnrNo` |
| `Field` | `cncTgtCnt` |
| `Field` | `cncAddSrvReqNo` |
| `Field` | `cncRetFee` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getMaasServiceCancelFee`

- Request: `POST` `/classes/com.korail.mobile.maas.cncFee.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:46`
- FormUrlEncoded: `Y`
- Return type: `MaasServiceCancelFeeDao.MaasServiceCancelFeeResponse` -> model `MaasServiceCancelFeeResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `addSrvReqNo` |
| `Field` | `addSrvDvCd` |
| `Field` | `coptEntRsvNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `cncRetFee` | `String` | `` | `MaasServiceCancelFeeResponse` |

### `getMaasServiceDetailList`

- Request: `POST` `/classes/com.korail.mobile.copt.gdReqQry.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:50`
- FormUrlEncoded: `Y`
- Return type: `MaasServiceDetailListDao.MaasServivceDetailResponse` -> model `MaasServivceDetailResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `qryDtFrom` |
| `Field` | `qryDtTo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `addSrvList` | `List<AddSrvItem>` | `` | `MaasServivceDetailResponse` |

### `getSelfSeatChgInfo`

- Request: `POST` `/classes/com.korail.mobile.self.seatChgInfo.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:54`
- FormUrlEncoded: `Y`
- Return type: `CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse` -> model `CallSelfSeatChgInfoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `runDt` |
| `Field` | `trnNo` |
| `Field` | `dptRsStnCd` |
| `Field` | `arvRsStnCd` |
| `Field` | `psrmClCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `chgBfArvStnConsOrdr` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `chgBfDptStnConsOrdr` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `chgRsnList` | `List<ChgRsnList>` | `` | `CallSelfSeatChgInfoResponse` |
| `chgStnList` | `List<ChgStnList>` | `` | `CallSelfSeatChgInfoResponse` |
| `exsArvStnRunOrdr` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `exsDptStnRunOrdr` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `gnrmRsvPsbCd` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `runDt` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `sprmRsvPsbCd` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `trnClsfCd` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `trnClsfNm` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `trnGpCd` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `trnGpNm` | `String` | `` | `CallSelfSeatChgInfoResponse` |
| `trnNo` | `String` | `` | `CallSelfSeatChgInfoResponse` |

### `getTripChgDate`

- Request: `POST` `/classes/com.korail.mobile.reservation.tripChgDate.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:58`
- FormUrlEncoded: `Y`
- Return type: `TripChgInfoDao.TripChgInfoDaoResponse` -> model `TripChgInfoDaoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tripChgDate` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `lastRunDt` | `String` | `` | `TripChgInfoDaoResponse` |
| `tripChgDate` | `String` | `` | `TripChgInfoDaoResponse` |
| `tripChgDates` | `List<String>` | `` | `TripChgInfoDaoResponse` |

### `gurdSmsSnd`

- Request: `POST` `/classes/com.korail.mobile.tk.gurdSmsSnd.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:62`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pnrNo` |
| `Field` | `jrnySqno` |
| `Field` | `rcvPsHndyTeln` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `pbpAcepSpec`

- Request: `POST` `/classes/com.korail.mobile.tk.pbpAcepSpec.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:66`
- FormUrlEncoded: `Y`
- Return type: `PbpAcepSpecDao.PbpAcepSpecResponse` -> model `PbpAcepSpecResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `Field` | `tkRetNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `tkList` | `List<Tk>` | `` | `PbpAcepSpecResponse` |

### `pbpTkWdrw`

- Request: `POST` `/classes/com.korail.mobile.tk.pbpWdrw.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:70`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pbpCnt` |
| `Field` | `pbpRsvNo` |
| `Field` | `pnrNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `plfNo`

- Request: `POST` `/classes/com.korail.mobile.tk.plfNo.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:74`
- FormUrlEncoded: `Y`
- Return type: `UpdatePlatformDao.PlfNoResponse` -> model `PlfNoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `tkCnt` |
| `Field` | `tkRetNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `tkList` | `List<TkList>` | `` | `PlfNoResponse` |

### `rcntDlvHst`

- Request: `POST` `/classes/com.korail.mobile.tk.rcntDlvHst.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:78`
- FormUrlEncoded: `Y`
- Return type: `RecentDeliveryHistoryDao.RcntDlvHstResponse` -> model `RcntDlvHstResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `custMgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `acepList` | `List<Acep>` | `` | `RcntDlvHstResponse` |

### `selfCheckinCancel`

- Request: `POST` `/classes/com.korail.mobile.checkin.cnc.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:82`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |
| `Field` | `jrnySqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `selfCheckinInfo`

- Request: `POST` `/classes/com.korail.mobile.checkin.info.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:86`
- FormUrlEncoded: `Y`
- Return type: `SelfCheckinInfoDao.SelfCheckinInfoResponse` -> model `SelfCheckinInfoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `saleWctNo` |
| `Field` | `saleDt` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |
| `Field` | `jrnySqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `arvDttm` | `String` | `` | `SelfCheckinInfoResponse` |
| `arvRsStnCd` | `String` | `` | `SelfCheckinInfoResponse` |
| `arvRsStnNm` | `String` | `` | `SelfCheckinInfoResponse` |
| `arvStnConsOrdr` | `String` | `` | `SelfCheckinInfoResponse` |
| `arvTmQb` | `String` | `` | `SelfCheckinInfoResponse` |
| `asgnSqno` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknCncDt` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknCncTm` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknDt` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknDvCd` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknSqno` | `String` | `` | `SelfCheckinInfoResponse` |
| `chcknTm` | `String` | `` | `SelfCheckinInfoResponse` |
| `dptDttm` | `String` | `` | `SelfCheckinInfoResponse` |
| `dptRsStnCd` | `String` | `` | `SelfCheckinInfoResponse` |
| `dptRsStnNm` | `String` | `` | `SelfCheckinInfoResponse` |
| `dptStnConsOrdr` | `String` | `` | `SelfCheckinInfoResponse` |
| `dptTmQb` | `String` | `` | `SelfCheckinInfoResponse` |
| `jrnySqno` | `String` | `` | `SelfCheckinInfoResponse` |
| `pnrNo` | `String` | `` | `SelfCheckinInfoResponse` |
| `runDt` | `String` | `` | `SelfCheckinInfoResponse` |
| `scarNo` | `String` | `` | `SelfCheckinInfoResponse` |
| `seatNo` | `String` | `` | `SelfCheckinInfoResponse` |
| `stlbTrnClsfNm` | `String` | `` | `SelfCheckinInfoResponse` |
| `trnNo` | `String` | `` | `SelfCheckinInfoResponse` |

### `selfCheckinPossible`

- Request: `POST` `/classes/com.korail.mobile.checkin.psbFlg.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:90`
- FormUrlEncoded: `Y`
- Return type: `SelfCheckinPossibleDao.SelfCheckinPossibleResponse` -> model `SelfCheckinPossibleResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `qrcode` |
| `Field` | `saleWctNo` |
| `Field` | `saleDd` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |
| `Field` | `jrnySqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `consList` | `List<ConsList>` | `` | `SelfCheckinPossibleResponse` |

### `selfCheckinRegister`

- Request: `POST` `/classes/com.korail.mobile.checkin.reg.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:94`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `cpsNo` |
| `Field` | `scarNo` |
| `Field` | `seatNo` |
| `Field` | `saleWctNo` |
| `Field` | `saleDd` |
| `Field` | `saleSqno` |
| `Field` | `tkRetPwd` |
| `Field` | `jrnySqno` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `ticketChangeCancel`

- Request: `POST` `/classes/com.korail.mobile.ticket.tripChgHndgCnc.do`
- Source: `com/korail/talk/network/dao/ticket/TicketService.java:98`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `lumpStlCnt` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

## `TrainsInfoService`

### `getFresScar`

- Request: `POST` `/classes/com.korail.mobile.trn.fresScar.do`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:20`
- FormUrlEncoded: `Y`
- Return type: `FresScarDao.FresScarResponse` -> model `FresScarResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `runDt` |
| `Field` | `trnNo` |
| `Field` | `dptStnConsOrdr` |
| `Field` | `arvStnConsOrdr` |
| `Field` | `dptStnRunOrdr` |
| `Field` | `arvStnRunOrdr` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `fresCont` | `String` | `` | `FresScarResponse` |
| `fresScarNo` | `String` | `` | `FresScarResponse` |
| `fresTtl` | `String` | `` | `FresScarResponse` |

### `getPrice2Fare`

- Request: `POST` `/classes/com.korail.mobile.trn.prcFare.do`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:24`
- FormUrlEncoded: `Y`
- Return type: `Price2FareDao.Price2FareResponse` -> model `Price2FareResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtMenuId` |
| `Field` | `chtnDvCd` |
| `Field` | `trnCnt` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `prcList` | `List<Price2Fare>` | `` | `Price2FareResponse` |

### `getPriceFare`

- Request: `POST` `/classes/com.korail.mobile.trainsInfo.TrainCharge`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:28`
- FormUrlEncoded: `Y`
- Return type: `PriceFareDao.PriceFareResponse` -> model `PriceFareResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtMenuId` |
| `Field` | `txtRtnDvCd` |
| `Field` | `txtChtrDvCd1` |
| `Field` | `txtSeatAttCd4` |
| `FieldMap` | dynamic map/body |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `prc_fare_list` | `PrcFareList` | `` | `PriceFareResponse` |

### `getSelectStationInfo`

- Request: `POST` `/classes/com.korail.mobile.qry.chtnStn.do`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:32`
- FormUrlEncoded: `Y`
- Return type: `TrainSelectStationDao.TrainSelectStationResponse` -> model `TrainSelectStationResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `dptRsStnCd` |
| `Field` | `arvRsStnCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `chtnList` | `List<TransferStationInfo>` | `` | `TrainSelectStationResponse` |

### `getTourTrainInfo`

- Request: `POST` `/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:36`
- FormUrlEncoded: `Y`
- Return type: `TourTrainInfoDao.TourTrainInfoResponse` -> model `TourTrainInfoResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `txtTrnGpCd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `seat_infos` | `SeatInfos` | `` | `TourTrainInfoResponse` |

### `getTrainSchedule`

- Request: `POST` `/classes/com.korail.mobile.research.actualTrainSchedule.do`
- Source: `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:40`
- FormUrlEncoded: `Y`
- Return type: `TrainScheduleDao.TrainScheduleResponse` -> model `TrainScheduleResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `runDt` |
| `Field` | `trnNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `dlayDtlRsnCont` | `String` | `` | `TrainScheduleResponse` |
| `dlayList` | `List<TimeInfo>` | `` | `TrainScheduleResponse` |
| `msgCont` | `String` | `` | `TrainScheduleResponse` |
| `runDt1` | `String` | `` | `TrainScheduleResponse` |
| `runSegOrdr` | `String` | `` | `TrainScheduleResponse` |
| `trnDptFlg` | `String` | `` | `TrainScheduleResponse` |
| `trnNo1` | `String` | `` | `TrainScheduleResponse` |

## `XPointService`

### `certifyOKCashbag`

- Request: `POST` `/classes/com.korail.mobile.xPoint.OkCashbagCertView`
- Source: `com/korail/talk/network/dao/xPoint/XPointService.java:14`
- FormUrlEncoded: `Y`
- Return type: `BaseResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `cp_no` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |

### `getKorailPoint`

- Request: `POST` `/classes/com.korail.mobile.xPoint.MyXPointView`
- Source: `com/korail/talk/network/dao/xPoint/XPointService.java:18`
- FormUrlEncoded: `Y`
- Return type: `KorailPointInquiryDao.KorailPointInquiryResponse` -> model `KorailPointInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `point_dv_cd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_cntc_chn_cont1` | `String` | `` | `KorailPointInquiryResponse` |
| `h_cp_athn_flg` | `String` | `` | `KorailPointInquiryResponse` |
| `h_cust_lead_flg_nm` | `String` | `` | `KorailPointInquiryResponse` |
| `h_delay_cnt` | `String` | `` | `KorailPointInquiryResponse` |
| `h_disc_coup_cnt` | `String` | `` | `KorailPointInquiryResponse` |
| `h_emil_athn_flg` | `String` | `` | `KorailPointInquiryResponse` |
| `h_hdcp_flg` | `String` | `` | `KorailPointInquiryResponse` |
| `h_korail_point` | `String` | `` | `KorailPointInquiryResponse` |
| `h_logn_tp_cd1` | `String` | `` | `KorailPointInquiryResponse` |
| `h_logn_tp_cd2` | `String` | `` | `KorailPointInquiryResponse` |
| `h_logn_tp_cd4` | `String` | `` | `KorailPointInquiryResponse` |
| `h_logn_tp_cd5` | `String` | `` | `KorailPointInquiryResponse` |
| `h_subt_dcs_cl_cd` | `String` | `` | `KorailPointInquiryResponse` |
| `h_subt_dcs_cl_nm` | `String` | `` | `KorailPointInquiryResponse` |

### `getLPoint`

- Request: `POST` `/classes/com.korail.mobile.mlg.lpotAthn.do`
- Source: `com/korail/talk/network/dao/xPoint/XPointService.java:22`
- FormUrlEncoded: `Y`
- Return type: `LPointDao.LPointInquiryResponse` -> model `LPointInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pontPwd` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `custRcgnNoVal` | `String` | `` | `LPointInquiryResponse` |
| `extrPontAmt` | `String` | `` | `LPointInquiryResponse` |
| `prsCnqeVal` | `String` | `` | `LPointInquiryResponse` |
| `pwdErrTno` | `String` | `` | `LPointInquiryResponse` |

### `getMileage`

- Request: `POST` `/classes/com.korail.mobile.mlg.amtSpec.do`
- Source: `com/korail/talk/network/dao/xPoint/XPointService.java:26`
- FormUrlEncoded: `Y`
- Return type: `MileageInquiryDao.MileageInquiryResponse` -> model `MileageInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `pontTpVal` |
| `Field` | `qryDvVal` |
| `Field` | `qryStDt` |
| `Field` | `qryClsDt` |
| `Field` | `pgPrCnt` |
| `Field` | `nowPgNo` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `delPontValNum` | `String` | `` | `MileageInquiryResponse` |
| `ktxMlgInfo` | `String` | `` | `MileageInquiryResponse` |
| `pgCnt` | `String` | `` | `MileageInquiryResponse` |
| `railNowSavePontValNum1` | `String` | `` | `MileageInquiryResponse` |
| `specList` | `List<SpecList>` | `` | `MileageInquiryResponse` |
| `totAcmRailPontValNum1` | `String` | `` | `MileageInquiryResponse` |
| `totAvlAfltPontValNum` | `String` | `` | `MileageInquiryResponse` |
| `totAvlRailPontValNum` | `String` | `` | `MileageInquiryResponse` |
| `totAvlRailPontValNum1` | `String` | `` | `MileageInquiryResponse` |
| `totUseRailPontValNum1` | `String` | `` | `MileageInquiryResponse` |

### `getPoint`

- Request: `POST` `/classes/com.korail.mobile.xPoint.XPointView`
- Source: `com/korail/talk/network/dao/xPoint/XPointService.java:30`
- FormUrlEncoded: `Y`
- Return type: `PointInquiryDao.PointInquiryResponse` -> model `PointInquiryResponse`

Request parameters:

| Transport | Name |
|---|---|
| `Field` | `Device` |
| `Field` | `Version` |
| `Field` | `Key` |
| `Field` | `inp_dv_cd` |
| `Field` | `point_dv_cd` |
| `Field` | `xpoint_no` |
| `Field` | `xpoint_pwd` |
| `Field` | `stl_crd_valid_trm` |

Response fields visible in APK:

| Field | Type | JSON/Serialized Name | Declared In |
|---|---|---|---|
| `FAIL` | `String` | `` | `BaseResponse` |
| `SUCCESS` | `String` | `` | `BaseResponse` |
| `hMsgCd` | `String` | `h_msg_cd` | `BaseResponse` |
| `hMsgTxt` | `String` | `h_msg_txt` | `BaseResponse` |
| `strResult` | `String` | `strResult` | `BaseResponse` |
| `h_avl_point` | `int` | `` | `PointInquiryResponse` |
| `h_corp_use_point` | `int` | `` | `PointInquiryResponse` |
| `h_join_point` | `int` | `` | `PointInquiryResponse` |
| `h_korail_point` | `int` | `` | `PointInquiryResponse` |
| `h_point` | `int` | `` | `PointInquiryResponse` |
