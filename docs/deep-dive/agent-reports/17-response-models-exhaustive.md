# 17. 응답 모델 필드 카탈로그

정적 로컬 분석 기준 문서다. 운영 API 호출은 하지 않았고, `analysis/jadx/sources`의 JADX Java-like source와 Retrofit service annotation을 근거로 했다.

## 범위와 해석

- 분석 대상: `com.korail.talk.network.dao.*`, `com.korail.talk.network.response.*`, `com.korail.talk.network.data.*` 중 응답 객체로 쓰이는 모델.
- 수록 기준: `BaseResponse` 및 그 하위 클래스 112개, 그리고 `network/response`의 top-level payload 모델 5개.
- 요청 모델은 service annotation의 `@Field`/`@Query`로 이미 명확한 경우가 많아 별도 endpoint inventory를 우선 참조한다. 이 문서는 응답 body의 Java 필드, 중첩 payload, getter/setter를 중심으로 정리한다.
- JSON 이름 annotation은 `S3.c` (`value()`, `alternate()`)를 `@c(...)`로 표기했다. annotation이 없으면 Gson은 기본적으로 Java 필드명을 JSON key 후보로 사용한다.
- `BaseResponse` 상속 클래스는 공통 상속 필드 `hMsgCd`, `hMsgTxt`, `strResult`를 항상 포함한다. 각 클래스 표에는 해당 클래스가 직접 선언한 필드만 적었다.
- endpoint/caller는 Retrofit 반환형과 DAO source에서 정적으로 추적 가능한 경우만 기재했다. 반환형 매핑이 없으면 `미확인`으로 표시했다.

## 공통 기반 모델

### `BaseResponse`

- 소스: `com/korail/talk/network/BaseResponse.java:7`
- 상속/구현: implements `Serializable`
- 용도: 거의 모든 Retrofit 응답의 공통 header/result envelope.

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `hMsgCd` | `String` | `@c("h_msg_cd")` | `gethMsgCd()` |
| `hMsgTxt` | `String` | `@c("h_msg_txt")` | `gethMsgTxt()` |
| `strResult` | `String` | `@c("strResult")` | `getStrResult()` |

## 응답 클래스 상세

### `dao.addService.AdditionalServiceDao.AdditionalServiceResponse`

- 소스: `com/korail/talk/network/dao/addService/AdditionalServiceDao.java:128`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `AddService.additionalService()` POST `/classes/com.korail.mobile.addService.reserve.do`; service `com/korail/talk/network/dao/addService/AddService.java`; caller `com/korail/talk/network/dao/addService/AdditionalServiceDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `outrec2` | `List<OutRec2>` | - | `getOutrec2()` |

### `dao.addService.ExtraProductListDao.ExtraProductListResponse`

- 소스: `com/korail/talk/network/dao/addService/ExtraProductListDao.java:27`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `AddService.getExtraProductList()` POST `/classes/com.korail.mobile.addService.reserveList.do`; service `com/korail/talk/network/dao/addService/AddService.java`; caller `com/korail/talk/network/dao/addService/ExtraProductListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `pnrList` | `List<ExtraProductInfo>` | - | `getPnrList()` |

### `dao.addService.HelpSrvCustDao.HelpSrvCustResponse`

- 소스: `com/korail/talk/network/dao/addService/HelpSrvCustDao.java:123`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `AddService.helpSrvCust()` POST `/classes/com.korail.mobile.addSrv.helpSrvCust.do`; service `com/korail/talk/network/dao/addService/AddService.java`; caller `com/korail/talk/network/dao/addService/HelpSrvCustDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `reqSpecList` | `List<ReqSpec>` | - | `getReqSpecList()` |

### `dao.addService.HelpSrvTkDao.HelpSrvTkDaoResponse`

- 소스: `com/korail/talk/network/dao/addService/HelpSrvTkDao.java:44`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `AddService.helpSrvTk()` POST `/classes/com.korail.mobile.addSrv.helpSrvTk.do`; service `com/korail/talk/network/dao/addService/AddService.java`; caller `com/korail/talk/network/dao/addService/HelpSrvTkDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `helpSrvList` | `List<helpSrv>` | - | `getHelpSrvList()` |

### `dao.cache.AppDataDao.AppDataResponse`

- 소스: `com/korail/talk/network/dao/cache/AppDataDao.java:12`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CacheService.getAppData()` GET `/file/CACHE/prdMobilePlusMain.cache`; service `com/korail/talk/network/dao/cache/CacheService.java`; caller `com/korail/talk/network/dao/cache/AppDataDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `disability_certification_msg` | `String` | - | `getDisability_certification_msg()` |
| `forSeatIntg` | `String` | - | `getForSeatIntg()` |
| `limousine` | `String` | `@c("airportBusMsg")` | `getLimousine()` |
| `railplus_cardinfo` | `String` | - | `getRailPlusCardInfo()` |
| `version` | `Version` | - | `getVersion()` |

### `dao.cache.NoticeDao.NoticeResponse`

- 소스: `com/korail/talk/network/dao/cache/NoticeDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CacheService.getNotice()` GET `/file/CACHE/prdMobilePlusNotice.cache`; service `com/korail/talk/network/dao/cache/CacheService.java`; caller `com/korail/talk/network/dao/cache/NoticeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `bbrdId` | `String` | - | `getBbrdId()`, `getNoticePostData()` |
| `ptwtSqno` | `String` | - | `getNoticePostData()`, `getPtwtSqno()` |
| `ptwtTtl` | `String` | - | `getPtwtTtl()` |

### `dao.cart.CartListDao.CartListResponse`

- 소스: `com/korail/talk/network/dao/cart/CartListDao.java:296`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CartService.getCartList()` POST `/classes/com.korail.mobile.cart.showCartList`; service `com/korail/talk/network/dao/cart/CartService.java`; caller `com/korail/talk/network/dao/cart/CartListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `cart_infos` | `CartInfos` | - | `getCart_infos()` |

### `dao.certification.BusReservationListDao.BusInquiryResponse`

- 소스: `com/korail/talk/network/dao/certification/BusReservationListDao.java:107`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `BusReservationService.reservationList()` POST `/classes/com.korail.mobile.lmu.scdlQry.do`; service `com/korail/talk/network/dao/certification/BusReservationService.java`; caller `com/korail/talk/network/dao/certification/BusReservationListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fllwPgExt` | `String` | - | `getFllwPgExt()`, `setFllwPgExt()` |
| `lgtmShtmDvCd` | `String` | - | `getLgtmShtmDvCd()`, `setLgtmShtmDvCd()` |
| `trainList` | `ArrayList<BusList>` | - | `getTrainList()`, `setTrainList()` |

### `dao.certification.BusReservationSeatListDao.SeatListResponse`

- 소스: `com/korail/talk/network/dao/certification/BusReservationSeatListDao.java:238`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `BusReservationService.reservationSeatList()` POST `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do`; service `com/korail/talk/network/dao/certification/BusReservationService.java`; caller `com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `car_tp_cd` | `String` | - | `getCar_tp_cd()` |
| `scar_no` | `String` | - | `getScar_no()` |
| `seatList` | `ArrayList<SeatList>` | - | `getSeat()` |
| `seat_ary_cd` | `String` | - | `getSeat_ary_cd()` |
| `up_dn_dv_cd` | `String` | - | `getUp_dn_dv_cd()` |

### `dao.certification.CongresspersonCertDao.CongresspersonCertResponse`

- 소스: `com/korail/talk/network/dao/certification/CongresspersonCertDao.java:52`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CertificationService.certCongressperson()` GET `/classes/com.korail.mobile.certification.assemblyCert`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/CongresspersonCertDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `freeDiscCertNo` | `String` | - | `getfreeDiscCertNo()` |

### `dao.certification.DisabledCertificationDao.DisabledCertificationResponse`

- 소스: `com/korail/talk/network/dao/certification/DisabledCertificationDao.java:43`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CertificationService.disabledCertification()` GET `/classes/com.korail.mobile.certification.disabled.do`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/DisabledCertificationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `btdt` | `String` | - | `getBtdt()` |
| `certificate` | `String` | - | `getCertificate()` |
| `hdcpTpCd` | `String` | - | `getHdcpTpCd()` |
| `subtDcsClCd` | `String` | - | `getSubtDcsClCd()` |

### `dao.certification.GovernmentCertificationStep1Dao.GovernmentCertificationResponse`

- 소스: `com/korail/talk/network/dao/certification/GovernmentCertificationStep1Dao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CertificationService.govermentCertification1()` GET `/classes/com.korail.mobile.pbep.toknCre.do`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/GovernmentCertificationStep1Dao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `app` | `String` | - | `getApp()` |
| `csrfToken` | `String` | - | `getCsrfToken()` |

### `dao.certification.GovernmentCertificationStep2Dao.GovernmentCertificationStep2Response`

- 소스: `com/korail/talk/network/dao/certification/GovernmentCertificationStep2Dao.java:25`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CertificationService.govermentCertification2()` GET `/classes/com.korail.mobile.pbep.sttChck.do`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/GovernmentCertificationStep2Dao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `code` | `String` | - | `getCode()` |
| `message` | `String` | - | `getMessage()` |
| `pbepInfo` | `String` | - | `getPbepInfo()` |
| `result` | `String` | - | `getResult()` |
| `txCompleteCode` | `String` | - | `getTxCompleteCode()` |

### `dao.certification.MeritCertDao.MeritCertResponse`

- 소스: `com/korail/talk/network/dao/certification/MeritCertDao.java:61`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CertificationService.certMerit()` POST `/classes/com.korail.mobile.certification.MeritCert`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/MeritCertDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_free_acm_use_tno` | `String` | - | `getH_free_acm_use_tno()`, `setH_free_acm_use_tno()` |
| `h_free_disc_cert_no` | `String` | - | `getH_free_disc_cert_no()`, `setH_free_disc_cert_no()` |
| `h_free_psb_tno` | `String` | - | `getH_free_psb_tno()`, `setH_free_psb_tno()` |

### `dao.common.CommonCodeDao.CommonCodeResponse`

- 소스: `com/korail/talk/network/dao/common/CommonCodeDao.java:192`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getCommonCode()` POST `/classes/com.korail.mobile.common.code.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/CommonCodeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `accepts` | `List<Accept>` | `@c(CommonCodeDao.STBK_ACCEPT)` -> `app.stbk.accept` | `getAccepts()` |
| `athn` | `Athn` | `@c(CommonCodeDao.ATHN)` -> `app.hndy.athn` | `getAthn()` |
| `buyNow` | `BuyNow` | `@c(CommonCodeDao.BUY_NOW)` -> `app.menu.buynow` | `getBuyNow()` |
| `data` | `Data` | `@c(CommonCodeDao.DATA)` -> `app.var.data` | `getData()` |
| `deviceOreo` | `DeviceOSPopUp` | `@c(CommonCodeDao.DEVICE_OREO)` -> `app.device.oreo` | `getDeviceOreo()` |
| `easyPay` | `EasyPay` | `@c(CommonCodeDao.EASY_PAY)` -> `app.event.easyPay` | `getEasyPay()` |
| `holidayPopup` | `HolidayPopup` | `@c(CommonCodeDao.HOLIDAY_POPUP)` -> `app.holiday.popup` | `getHolidayPopup()` |
| `imageDownLoadData` | `ImageDownLoadData` | `@c(CommonCodeDao.IMAGE_DOWN_LOAD_DATA)` -> `app.display.image` | `getImageDownLoadData()` |
| `isEasyLoginShow` | `EasyLogin` | `@c(CommonCodeDao.IS_NAVER_SHOW)` -> `app.easyLogin.isShow` | `getEasyLoginShow()` |
| `korailBoss` | `KorailBoss` | `@c(CommonCodeDao.KORAIL_BOSS)` -> `app.korail.boss` | `getKorailBoss()` |
| `limousine` | `String` | `@c(CommonCodeDao.LIMOUSINE_MSG)` -> `app.limousine.airportBusMsg` | `getLimousineMsg()` |
| `limousineMainMsg` | `String` | `@c(CommonCodeDao.LIMOUSINE_MAIN_MSG)` -> `app.limousine.mainMsg` | `getLimousineMainMsg()` |
| `login` | `Login` | `@c(CommonCodeDao.LOGIN)` -> `app.login.cphd` | `getLogin()` |
| `lostArticle` | `LostArticle` | `@c(CommonCodeDao.LOST_ARTICLE)` -> `app.menu.lost112` | `getLostArticle()` |
| `maasTest` | `String` | `@c(CommonCodeDao.MAAS_TEST)` -> `app.MaaS.test` | `getMaasTest()` |
| `mainPopup` | `MainPopup` | `@c(CommonCodeDao.MAIN_POPUP)` -> `app.main.popup` | `getMainPopup()` |
| `menuBiz` | `MenuBiz` | `@c(CommonCodeDao.MENU_BIZ)` -> `app.menu.biz` | `getMenuBiz()` |
| `menuRailPoint` | `MenuRailPoint` | `@c(CommonCodeDao.MENU_RAILPOINT)` -> `app.menu.railpoint` | `getMenuRailPoint()` |
| `periodCommutationData` | `PeriodCommutationData` | `@c(CommonCodeDao.PERIOD_COMMUTATION_DATA)` -> `app.periodCommutation.data` | `getPeriodCommutationData()` |
| `pointData` | `Point` | `@c(CommonCodeDao.POINT)` -> `app.event.point` | `getPoint()` |
| `report` | `Report` | `@c(CommonCodeDao.REPORT)` -> `app.illegal.report` | `getReport()` |
| `stationCd` | `List<String>` | `@c(CommonCodeDao.STATION_CD)` -> `app.limousine.stationCd` | `getStationCd()` |
| `stationNm` | `List<String>` | `@c(CommonCodeDao.STATION_NM)` -> `app.limousine.stationNm` | `getStationNm()` |
| `viewVisibility` | `ViewVisibility` | `@c(CommonCodeDao.VIEW_VISIBILITY)` -> `app.view.visibility` | `getViewVisibility()` |

### `dao.common.CookieDao.RsvWaitResponse`

- 소스: `com/korail/talk/network/dao/common/CookieDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.ckValue()` GET `/ebizcross/getUUID.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/CookieDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mutMrkVrfCd` | `String` | - | `getMutMrkVrfCd()` |

### `dao.common.DecryptDao.DecryptResponse`

- 소스: `com/korail/talk/network/dao/common/DecryptDao.java:53`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getDecrypt()` POST `/classes/com.korail.mobile.common.decrypt.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/DecryptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `decValueList` | `List<DecryptValueList>` | - | `getDecValueList()` |

### `dao.common.EncryptDao.EncryptResponse`

- 소스: `com/korail/talk/network/dao/common/EncryptDao.java:35`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getEncrypt()` POST `/classes/com.korail.mobile.common.encrypt.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/EncryptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `encValueList` | `List<EncryptValueList>` | - | `getEncValueList()` |

### `dao.common.KBPayEncryptDao.KBpayEncryptResponse`

- 소스: `com/korail/talk/network/dao/common/KBPayEncryptDao.java:36`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getKBPayEncrypt()` POST `/classes/com.korail.mobile.common.encrypt.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/KBPayEncryptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `BIZ_NUM` | `String` | - | `getBIZ_NUM()` |
| `CHANNEL_ID` | `String` | - | `getCHANNEL_ID()` |
| `PURCHASE_PRODUCT_INFO` | `String` | - | `getPURCHASE_PRODUCT_INFO()` |
| `REQ_DATE_TIME` | `String` | - | `getREQ_DATE_TIME()` |
| `SELLER_NAME` | `String` | - | `getSELLER_NAME()` |
| `SELLER_NUM` | `String` | - | `getSELLER_NUM()` |
| `encValueList` | `List<EncryptDao.EncryptValueList>` | - | `getEncValueList()` |

### `dao.common.MaasMenuListDao.MaasMenuListResponse`

- 소스: `com/korail/talk/network/dao/common/MaasMenuListDao.java:13`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getMaasMenuList()` POST `/classes/com.korail.mobile.copt.gdMenuLt.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/MaasMenuListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `aBggTrsfRbtUrl` | `String` | - | `getaBggTrsfRbtUrl()` |
| `aBisInfoUrl` | `String` | - | `getaBisInfoUrl()` |
| `aElevatorUrl` | `String` | - | `getaElevatorUrl()` |
| `aParkingLotUrl` | `String` | - | `getaParkingLotUrl()` |
| `dElevatorUrl` | `String` | - | `getdElevatorUrl()` |
| `dLeadNaviUrl` | `String` | - | `getdLeadNaviUrl()` |
| `dParkingLotUrl` | `String` | - | `getdParkingLotUrl()` |
| `menuList` | `List<Menu>` | - | `getMenuList()` |

### `dao.common.SeedEncryptDao.SeedEncryptResponse`

- 소스: `com/korail/talk/network/dao/common/SeedEncryptDao.java:37`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.seedEncrypt()` POST `/classes/com.korail.mobile.shinhan.Encrypt.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/SeedEncryptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `encValueList` | `List<EncValueList>` | - | `getEncValueList()` |

### `dao.common.StationDataDao.StationDataResponse`

- 소스: `com/korail/talk/network/dao/common/StationDataDao.java:126`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getMaasStationList()` POST `/ebizmaas/EbizMaasStationList.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/MaasStationListDao.java`
- `CommonService.getStationData()` GET `/classes/com.korail.mobile.common.stationdata`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/StationDataDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `stns` | `STNs` | - | `getStns()` |

### `dao.common.StationInfoDao.StationInfoResponse`

- 소스: `com/korail/talk/network/dao/common/StationInfoDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.getStationInfo()` GET `/classes/com.korail.mobile.common.stationinfo`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/StationInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `count` | `int` | - | `getCount()` |
| `map_version` | `String` | - | `getMap_version()` |

### `dao.common.authQRLocationDao.QRLocationResponse`

- 소스: `com/korail/talk/network/dao/common/authQRLocationDao.java:43`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CommonService.authQRLocation()` POST `/classes/com.korail.mobile.qr.bchTripSv.do`; service `com/korail/talk/network/dao/common/CommonService.java`; caller `com/korail/talk/network/dao/common/authQRLocationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `jobScsFlg` | `String` | - | `getJobScsFlg()` |

### `dao.cust.MchdDcntTgtDao.MchdDcntTgtResponse`

- 소스: `com/korail/talk/network/dao/cust/MchdDcntTgtDao.java:80`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `CustService.mchdDcntTgt()` POST `/classes/com.korail.mobile.cust.mchdDcntTgt.do`; service `com/korail/talk/network/dao/cust/CustService.java`; caller `com/korail/talk/network/dao/cust/MchdDcntTgtDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fmlyList` | `List<Fmly>` | - | `getFmlyList()` |

### `dao.delay.CashRfnDao.CashRfnResponse`

- 소스: `com/korail/talk/network/dao/delay/CashRfnDao.java:115`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `DelayService.cashRfn()` POST `/classes/com.korail.mobile.dlay.cashRfn.do`; service `com/korail/talk/network/dao/delay/DelayService.java`; caller `com/korail/talk/network/dao/delay/CashRfnDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `rfnAmt` | `String` | - | `getRfnAmt()` |

### `dao.delay.DelayCertificateDao.DelayCertificateResponse`

- 소스: `com/korail/talk/network/dao/delay/DelayCertificateDao.java:71`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `DelayService.athnIsu()` POST `/classes/com.korail.mobile.dlay.athnIsu.do`; service `com/korail/talk/network/dao/delay/DelayService.java`; caller `com/korail/talk/network/dao/delay/DelayCertificateDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `dlayList` | `List<DelayInfo>` | - | `getDlayList()` |

### `dao.delay.DelayPNRQueryDao.DelayPNRQueryResponse`

- 소스: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java:86`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `DelayService.executeDelayPNRQuery()` POST `/classes/com.korail.mobile.delay.pnrQry.do`; service `com/korail/talk/network/dao/delay/DelayService.java`; caller `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mainList` | `List<Main>` | - | `getMain()` |

### `dao.delay.DelayReturnReceiptDao.DelayReturnReceiptResponse`

- 소스: `com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java:52`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `DelayService.dealyReturnReceipt()` POST `/classes/com.korail.mobile.dlay.pymtRcet.do`; service `com/korail/talk/network/dao/delay/DelayService.java`; caller `com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `dlayFarePymtMtdNm` | `String` | - | `getDlayFarePymtMtdNm()` |
| `dlayFareRetAmt` | `String` | - | `getDlayFareRetAmt()` |
| `retDt` | `String` | - | `getRetDt()` |

### `dao.giftInfo.TicketPresentDao.TicketPresentResponse`

- 소스: `com/korail/talk/network/dao/giftInfo/TicketPresentDao.java:160`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `GiftInfoService.presentTicket()` POST `/classes/com.korail.mobile.giftInfo.GiftSend`; service `com/korail/talk/network/dao/giftInfo/GiftInfoService.java`; caller `com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `chgePbpRsvNo` | `String` | - | `getChgePbpRsvNo()` |

### `dao.gifticket.GifticketBookingDao.GifticketBookingResponse`

- 소스: `com/korail/talk/network/dao/gifticket/GifticketBookingDao.java:61`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `GifticketService.bookingGifticket()` POST `/classes/com.korail.mobile.gift.gdRsv.do`; service `com/korail/talk/network/dao/gifticket/GifticketService.java`; caller `com/korail/talk/network/dao/gifticket/GifticketBookingDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `lumpStlTgtNo` | `String` | - | `getLumpStlTgtNo()` |
| `prsCnqeVal` | `String` | - | `getPrsCnqeVal()` |
| `rcvdAmt` | `String` | - | `getRcvdAmt()` |

### `dao.gifticket.GifticketHistoryDao.GifticketHistoryResponse`

- 소스: `com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java:68`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `GifticketService.historyGifticket()` POST `/classes/com.korail.mobile.gift.gdUseSpec.do`; service `com/korail/talk/network/dao/gifticket/GifticketService.java`; caller `com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fllwQryFlg` | `String` | - | - |
| `qryCnt` | `String` | - | - |
| `txnList` | `List<GifticketDetailData>` | - | `getTxnList()` |

### `dao.gifticket.GifticketListDao.GifticketListResponse`

- 소스: `com/korail/talk/network/dao/gifticket/GifticketListDao.java:156`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `GifticketService.getGifticketList()` POST `/classes/com.korail.mobile.gift.gdLst.do`; service `com/korail/talk/network/dao/gifticket/GifticketService.java`; caller `com/korail/talk/network/dao/gifticket/GifticketListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `gdList` | `List<GifticketInfo>` | - | `getGifticketInfoList()` |
| `qryCnt` | `String` | - | - |
| `qryNumNext` | `String` | - | - |

### `dao.gifticket.GifticketReturnDao.GifticketReturnResponse`

- 소스: `com/korail/talk/network/dao/gifticket/GifticketReturnDao.java:25`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `GifticketService.returnGifticket()` POST `/classes/com.korail.mobile.gift.gdRet.do`; service `com/korail/talk/network/dao/gifticket/GifticketService.java`; caller `com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `prsFlg` | `String` | - | `getPrsFlg()` |

### `dao.login.LoginDao.LoginResponse`

- 소스: `com/korail/talk/network/dao/login/LoginDao.java:80`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `LoginService.login()` POST `/classes/com.korail.mobile.login.Login`; service `com/korail/talk/network/dao/login/LoginService.java`; caller `com/korail/talk/network/dao/login/LoginDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `coupClsFlg` | `String` | - | `getCoupClsFlg()` |
| `dlayDscpInfo` | `String` | - | `getDlayDscpInfo()` |
| `encryptCustNo` | `String` | - | `getEncryptCustNo()` |
| `encryptHMbCrdNo` | `String` | - | `getEncryptHMbCrdNo()` |
| `encryptMbCrdNo` | `String` | - | `getEncryptMbCrdNo()` |
| `intgFlg` | `String` | - | `getIntgFlg()` |
| `intgMsgTxt` | `String` | - | `getIntgMsgTxt()` |
| `intgUrl` | `String` | - | `getIntgUrl()` |
| `notiTpCd` | `String` | - | `getNotiTpCd()` |
| `strAthnFlg5` | `String` | - | `getStrAthnFlg5()`, `setStrAthnFlg5()` |
| `strAthnFlg7` | `String` | - | `getStrAthnFlg7()` |
| `strBtdt` | `String` | - | `getStrBtdt()` |
| `strCpNo` | `String` | - | `getStrCpNo()` |
| `strCustClCd` | `String` | - | `getStrCustClCd()` |
| `strCustDvCd` | `String` | - | `getStrCustDvCd()` |
| `strCustLeadFlg` | `String` | - | `getStrCustLeadFlg()` |
| `strCustMgSrtCd` | `String` | - | `getStrCustMgSrtCd()` |
| `strCustNm` | `String` | - | `getStrCustNm()` |
| `strCustNo` | `String` | - | `getStrCustNo()` |
| `strCustSrtCd` | `String` | - | `getStrCustSrtCd()` |
| `strEmailAdr` | `String` | - | `getStrEmailAdr()` |
| `strHdcpFlg` | `String` | - | `getStrHdcpFlg()` |
| `strHdcpTpCd` | `String` | - | `getStrHdcpTpCd()` |
| `strHdcpTpCdNm` | `String` | - | `getStrHdcpTpCdNm()` |
| `strLognTpCd6` | `String` | - | `getStrLognTpCd6()` |
| `strMbCrdNo` | `String` | - | `getStrMbCrdNo()` |
| `strRedirectUrl` | `String` | - | `getStrRedirectUrl()` |
| `strSubtDcsClCd` | `String` | - | `getStrSubtDcsClCd()` |
| `strYouthAgrFlg` | `String` | - | `getStrYouthAgrFlg()` |

### `dao.login.MemberCertDao.MemberCertResponse`

- 소스: `com/korail/talk/network/dao/login/MemberCertDao.java:61`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `LoginService.certMember()` POST `/classes/com.korail.mobile.login.userCheck`; service `com/korail/talk/network/dao/login/LoginService.java`; caller `com/korail/talk/network/dao/login/MemberCertDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mbCrdNo` | `String` | - | `getMbCrdNo()` |
| `strCustNo` | `String` | - | `getStrCustNo()` |

### `dao.mileage.AcpnMlgSpecDao.AcpnMlgSpecResponse`

- 소스: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java:27`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `MileageService.acpnMlgSpec()` POST `/classes/com.korail.mobile.mileage.acpnMlgSpec.do`; service `com/korail/talk/network/dao/mileage/MileageService.java`; caller `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `tkList` | `List<Ticket>` | - | `getTkList()` |

### `dao.myTicket.SpecialRoomUpgradeDao.SpecialRoomUpgradeResponse`

- 소스: `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java:22`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `MyTicketService.requestUpgradeSeat()` GET `/classes/com.korail.mobile.myTicket.reqUpgradeSeat`; service `com/korail/talk/network/dao/myTicket/MyTicketService.java`; caller `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `jrnys` | `List<Jrnys>` | - | `getJrnys()` |
| `ticketInfo` | `TicketInfo` | - | `getTicketInfo()` |

### `dao.myTicket.TicketListDao.TicketListResponse`

- 소스: `com/korail/talk/network/dao/myTicket/TicketListDao.java:139`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `MyTicketService.getTicketList()` POST `/classes/com.korail.mobile.myTicket.MyTicketList`; service `com/korail/talk/network/dao/myTicket/MyTicketService.java`; caller `com/korail/talk/network/dao/myTicket/TicketListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `reservation_list` | `List<ReservationList>` | - | `getReservation_list()` |

### `dao.nFilter.NFilterCreateKeyDao.NFilterCreateKeyResponse`

- 소스: `com/korail/talk/network/dao/nFilter/NFilterCreateKeyDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `NFilterService.createKey()` POST `/classes/com.korail.mobile.nFilter.createKey.do`; service `com/korail/talk/network/dao/nFilter/NFilterService.java`; caller `com/korail/talk/network/dao/nFilter/NFilterCreateKeyDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `publicKey` | `String` | - | `getPublicKey()` |

### `dao.pass.CommPaymentDao.CommPaymentResponse`

- 소스: `com/korail/talk/network/dao/pass/CommPaymentDao.java:53`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.commPayment()` POST `/classes/com.korail.mobile.pass.passPayIssue`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/CommPaymentDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `main_info` | `PassPaymentDao.MainInfo` | - | `getMain_info()` |

### `dao.pass.CommReservationDao.CommReservationResponse`

- 소스: `com/korail/talk/network/dao/pass/CommReservationDao.java:179`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: `MainInfo`(57 fields)
- `PassService.commReservation()` POST `/classes/com.korail.mobile.pass.passReserve`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/CommReservationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_guide` | `String` | - | `getH_guide()` |
| `main_info` | `MainInfo` | - | `getMain_info()` |

중첩 payload:

- `MainInfo` (implements `Serializable`; source line 183): `h_age`:`String` {getH_age()}; `h_app_arv_rs_stn_cd`:`String` {getH_app_arv_rs_stn_cd()}; `h_app_arv_rs_stn_nm`:`String` {getH_app_arv_rs_stn_nm()}; `h_app_dpt_rs_stn_cd`:`String` {getH_app_dpt_rs_stn_cd()}; `h_app_dpt_rs_stn_nm`:`String` {getH_app_dpt_rs_stn_nm()}; `h_arv_stn_cons_ordr_1`:`String` {getH_arv_stn_cons_ordr_1()}; `h_arv_stn_cons_ordr_2`:`String` {getH_arv_stn_cons_ordr_2()}; `h_arv_tm`:`String` {getH_arv_tm()}; `h_chg_mg_dv_cd`:`String` {getH_chg_mg_dv_cd()}; `h_chg_mg_no`:`String` {getH_chg_mg_no()}; `h_chtrn_rs_stn_cd`:`String` {getH_chtrn_rs_stn_cd()}; `h_chtrn_rs_stn_nm`:`String` {getH_chtrn_rs_stn_nm()}; `h_cmtr_knd_cd`:`String` {getH_cmtr_knd_cd()}; `h_cmtr_srt_cd`:`String` {getH_cmtr_srt_cd()}; `h_cmtr_utl_age_cd`:`String` {getH_cmtr_utl_age_cd()}; `h_cmtr_utl_trm_cd`:`String` {getH_cmtr_utl_trm_cd()}; `h_cmtr_utl_trm_nm`:`String` {getH_cmtr_utl_trm_nm()}; `h_cust_nm`:`String` {getH_cust_nm()}; `h_cust_no`:`String` {getH_cust_no()}; `h_dpt_stn_cons_ordr_1`:`String` {getH_dpt_stn_cons_ordr_1()}; `h_dpt_stn_cons_ordr_2`:`String` {getH_dpt_stn_cons_ordr_2()}; `h_dpt_tm`:`String` {getH_dpt_tm()}; `h_dtour1`:`String` {getH_dtour1()}; `h_dtour2`:`String` {getH_dtour2()}; `h_exs_ln_acm_dst`:`String` {getH_exs_ln_acm_dst()}; `h_holiday_cls_dt`:`String` {getH_holiday_cls_dt()}; `h_holiday_flg`:`String` {getH_holiday_flg()}; `h_holiday_st_dt`:`String` {getH_holiday_st_dt()}; `h_new_ln_acm_dst`:`String` {getH_new_ln_acm_dst()}; `h_otm_rcvd_amt`:`String` {getH_otm_rcvd_amt()}; `h_prc_cl_cd_1`:`String` {getH_prc_cl_cd_1()}; `h_prc_cl_cd_2`:`String` {getH_prc_cl_cd_2()}; `h_psg_tp_cd`:`String` {getH_psg_tp_cd()}; `h_psrm_cl_cd`:`String` {getH_psrm_cl_cd()}; `h_rcvd_amt`:`String` {getH_rcvd_amt()}; `h_rcvd_fare`:`String` {getH_rcvd_fare()}; `h_rcvd_prc`:`String` {getH_rcvd_prc()}; `h_rout_cd_1`:`String` {getH_rout_cd_1()}; `h_rout_cd_2`:`String` {getH_rout_cd_2()}; `h_rsv_trm_dup`:`String` {getH_rsv_trm_dup()}; `h_schd_trvl_dv_cd`:`String` {getH_schd_trvl_dv_cd()}; `h_stx_amt`:`String` {getH_stx_amt()}; `h_taxt_spl_prce`:`String` {getH_taxt_spl_prce()}; `h_trn_clsf_cd_1`:`String` {getH_trn_clsf_cd_1()}; `h_trn_clsf_cd_2`:`String` {getH_trn_clsf_cd_2()}; `h_trn_gp_cd`:`String` {getH_trn_gp_cd()}; `h_trn_no_1`:`String` {getH_trn_no_1()}; `h_trn_no_2`:`String` {getH_trn_no_2()}; `h_und_dv_cd_1`:`String` {getH_und_dv_cd_1()}; `h_und_dv_cd_2`:`String` {getH_und_dv_cd_2()}; `h_use_cls_dt`:`String` {getH_use_cls_dt()}; `h_use_open_dt`:`String` {getH_use_open_dt()}; `h_use_psb_dno`:`String` {getH_use_psb_dno()}; `h_use_psb_tno`:`String` {getH_use_psb_tno()}; `isIncludeHoliday`:`boolean` {isIncludeHoliday(),setIncludeHoliday()}; `mStationInfo`:`String` {getStationInfo(),setStationInfo()}; `mUserNames`:`String` {getUserNames(),setUserNames()}

### `dao.pass.CommRsvInquiryDao.CommRsvInquiryResponse`

- 소스: `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java:135`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: `ScheduleInfoList`(1 fields)
- `PassService.getCommRsvInquiry()` POST `/classes/com.korail.mobile.pass.passScheduleInfoList`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `schedule_info` | `List<ScheduleInfoList>` | - | `getSchedule_info()` |

중첩 payload:

- `ScheduleInfoList` (없음; source line 138): `train_list`:`List<TrainList>` {getTrain_list()}

### `dao.pass.DiscountMenuDao.DiscountMenuResponse`

- 소스: `com/korail/talk/network/dao/pass/DiscountMenuDao.java:134`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.passMenu()` POST `/classes/com.korail.mobile.pass.passMenu.do`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `list` | `List<DiscountMenu>` | - | `getList()` |

### `dao.pass.EnableDateDao.EnableDateResponse`

- 소스: `com/korail/talk/network/dao/pass/EnableDateDao.java:44`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.getEnableDate()` POST `/classes/com.korail.mobile.pass.passInfoList`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/EnableDateDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `pass_info` | `List<PassInfo>` | - | `getPass_info()` |
| `ticket_info` | `List<Ticket_info>` | - | `getTicket_info()` |
| `wct_info` | `List<WctInfo>` | - | `getWct_info()` |

### `dao.pass.PassPaymentDao.PassPaymentResponse`

- 소스: `com/korail/talk/network/dao/pass/PassPaymentDao.java:86`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.passPayment()` POST `/classes/com.korail.mobile.pass.passOtrPayIssue`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/PassPaymentDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `main_info` | `MainInfo` | - | `getMain_info()` |

### `dao.pass.PassReservationDao.PassReservationResponse`

- 소스: `com/korail/talk/network/dao/pass/PassReservationDao.java:148`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.passReservation()` POST `/classes/com.korail.mobile.pass.passOtrReserve`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/PassReservationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `main_info` | `MainInfo` | - | `getMain_info()` |

### `dao.pass.TripMenuDao.TripMenuResponse`

- 소스: `com/korail/talk/network/dao/pass/TripMenuDao.java:117`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassService.tripMenu()` POST `/classes/com.korail.mobile.pass.trGdMenuLt.do`; service `com/korail/talk/network/dao/pass/PassService.java`; caller `com/korail/talk/network/dao/pass/TripMenuDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `menuList` | `List<TripMenu>` | - | `getList()` |
| `poppMsg` | `String` | - | `getPoppMsg()`, `setPoppMsg()` |

### `dao.passCard.DCCouponListDao.DCCouponListResponse`

- 소스: `com/korail/talk/network/dao/passCard/DCCouponListDao.java:47`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassCardService.getDiscountCoupon()` POST `/classes/com.korail.mobile.passCard.CouponView`; service `com/korail/talk/network/dao/passCard/PassCardService.java`; caller `com/korail/talk/network/dao/passCard/DCCouponListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `coupon_infos` | `CouponInfos` | - | `getCoupon_infos()` |
| `h_page_no` | `String` | - | `getH_page_no()` |
| `h_tot_page_cnt` | `String` | - | `getH_tot_page_cnt()` |

### `dao.passCard.DelayTicketListDao.DelayTicketListResponse`

- 소스: `com/korail/talk/network/dao/passCard/DelayTicketListDao.java:87`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PassCardService.getDelayTicketList()` POST `/classes/com.korail.mobile.passCard.DelayDiscountView`; service `com/korail/talk/network/dao/passCard/PassCardService.java`; caller `com/korail/talk/network/dao/passCard/DelayTicketListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `disc_infos` | `DiscInfos` | - | `getDisc_infos()` |

### `dao.pay.NaverPayRsvDao.NaverPayRsvResponse`

- 소스: `com/korail/talk/network/dao/pay/NaverPayRsvDao.java:34`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.naverPayMoneyRsv()` POST `/classes/com.korail.mobile.pay.naverPayMoneyRsv.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/NaverPayMoneyRsvDao.java`
- `PayService.naverPayRsv()` POST `/classes/com.korail.mobile.pay.naverPayRsv.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/NaverPayRsvDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `stlScnUrl` | `String` | - | `getStlScnUrl()` |

### `dao.pay.PaycoDao.PaycoPaymentResponse`

- 소스: `com/korail/talk/network/dao/pay/PaycoDao.java:45`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.getPaycoResult()` POST `/classes/com.korail.mobile.payment.reserve.payco.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/PaycoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `recvData` | `RecvData` | - | `getRecvData()` |

### `dao.pay.SpayCphdDatValDao.SpayCphdDatValResponse`

- 소스: `com/korail/talk/network/dao/pay/SpayCphdDatValDao.java:62`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.getSpayCphdDatVal()` POST `/classes/com.korail.mobile.pay.spayCphdDatVal.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/SpayCphdDatValDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `spayCphdDatVal` | `String` | - | `getSpayCphdDatVal()` |
| `stlCrCrdNo` | `String` | - | `getStlCrCrdNo()` |

### `dao.pay.SpayCphdDatValMonimoDao.SpayCphdDatValMonimoResponse`

- 소스: `com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java:26`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.getSpayCphdDatValMonimo()` POST `/classes/com.korail.mobile.pay.monimoDecrypt.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `stlCrCrdNo` | `String` | - | `getStlCrCrdNo()` |

### `dao.pay.SpayOdrNoDao.SpayOdrNoResponse`

- 소스: `com/korail/talk/network/dao/pay/SpayOdrNoDao.java:84`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.getSpayOdrNo()` POST `/classes/com.korail.mobile.pay.spayOrdNo.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/SpayOdrNoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fllwScnAppUrlAdr` | `String` | - | `getFllwScnAppUrlAdr()` |
| `prprNo` | `String` | - | `getPrprNo()` |
| `spayTid` | `String` | - | `getSpayTid()` |

### `dao.pay.StbkAcntDao.StbkAcntResponse`

- 소스: `com/korail/talk/network/dao/pay/StbkAcntDao.java:76`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.stbkAcnt()` POST `/classes/com.korail.mobile.pay.stbkAcnt.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/StbkAcntDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `custNm` | `String` | - | `getCustNm()` |
| `stbkTxnNo` | `String` | - | `getStbkTxnNo()` |

### `dao.pay.StbkRegBankDao.StbkRegBankResponse`

- 소스: `com/korail/talk/network/dao/pay/StbkRegBankDao.java:59`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.stbkRegBank()` POST `/classes/com.korail.mobile.pay.stbkRegBank.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/StbkRegBankDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `regList` | `List<Reg>` | - | `getRegList()` |
| `regPsbList` | `List<RegPsb>` | - | `getRegPsbLists()` |

### `dao.pay.TossAutoCreateDao.TossAutoCResponse`

- 소스: `com/korail/talk/network/dao/pay/TossAutoCreateDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.tossautoC()` POST `/classes/com.korail.mobile.pay.tossautoC.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/TossAutoCreateDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `billingKey` | `String` | - | `getBillingKey()` |
| `checkoutAndroidUri` | `String` | - | `getCheckoutAndroidUri()` |
| `checkoutIosUri` | `String` | - | `getCheckoutIosUri()` |
| `checkoutUri` | `String` | - | `getCheckoutUri()` |

### `dao.pay.TossAutoStlKeyQryDao.StlKeyQryResponse`

- 소스: `com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java:77`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PayService.stlKeyQry()` POST `/classes/com.korail.mobile.pay.stlKeyQry.do`; service `com/korail/talk/network/dao/pay/PayService.java`; caller `com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `spayList` | `List<SimplePayInfo>` | - | `getSpayList()` |

### `dao.payment.RsvPaymentDao.RsvPaymentResponse`

- 소스: `com/korail/talk/network/dao/payment/RsvPaymentDao.java:79`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PaymentService.payment()` POST `/classes/com.korail.mobile.payment.ReservationPayment`; service `com/korail/talk/network/dao/payment/PaymentService.java`; caller `com/korail/talk/network/dao/payment/RsvPaymentDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_im_flg` | `String` | - | `getH_im_flg()` |
| `tk_coupon_info` | `List<TkCouponInfo>` | - | `getTk_coupon_info()` |

### `dao.product.ProductDetailDao.ProductDetailResponse`

- 소스: `com/korail/talk/network/dao/product/ProductDetailDao.java:47`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ProductService.getProductDetail()` GET `/classes/com.korail.mobile.product.ReservationDetail`; service `com/korail/talk/network/dao/product/ProductService.java`; caller `com/korail/talk/network/dao/product/ProductDetailDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mainInfo` | `ProductInfo` | - | `getMainInfo()` |

### `dao.product.ProductListDao.ProductListResponse`

- 소스: `com/korail/talk/network/dao/product/ProductListDao.java:52`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ProductService.getProductList()` GET `/classes/com.korail.mobile.product.ReservationList`; service `com/korail/talk/network/dao/product/ProductService.java`; caller `com/korail/talk/network/dao/product/ProductListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mainInfo` | `MainInfo` | - | `getMainInfo()` |

### `dao.product.ProductPaymentCheckDao.ProductPaymentCheckResponse`

- 소스: `com/korail/talk/network/dao/product/ProductPaymentCheckDao.java:50`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ProductService.paymentCheck()` GET `/classes/com.korail.mobile.product.payInfo`; service `com/korail/talk/network/dao/product/ProductService.java`; caller `com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mainInfo` | `MainInfo` | - | `getMainInfo()` |

### `dao.push.CallCrewRequestListDao.CallCrewListResponse`

- 소스: `com/korail/talk/network/dao/push/CallCrewRequestListDao.java:26`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PushService.callCrewRequestList()` GET `/classes/com.korail.mobile.push.crwCallRq.do`; service `com/korail/talk/network/dao/push/PushService.java`; caller `com/korail/talk/network/dao/push/CallCrewRequestListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `prsList` | `List<PrsList>` | - | `getPrsist()` |

### `dao.push.CmtrKndMenuDao.CmtrKndMenuResponse`

- 소스: `com/korail/talk/network/dao/push/CmtrKndMenuDao.java:26`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PushService.cmtrKndPassMenu()` GET `/classes/com.korail.mobile.push.cmtrKnd.do`; service `com/korail/talk/network/dao/push/PushService.java`; caller `com/korail/talk/network/dao/push/CmtrKndMenuDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `afterDay` | `String` | - | `getAfterDay()` |
| `agree` | `String` | - | `getAgree()` |
| `information` | `String` | - | `getInformation()` |
| `passData` | `DiscountMenuDao.PassMainInfo` | - | `getPassData()` |
| `title` | `String` | - | `getTitle()` |

### `dao.push.PushUpdateDao.PushUpdateResponse`

- 소스: `com/korail/talk/network/dao/push/PushUpdateDao.java:80`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `PushService.pushUpdate()` GET `/classes/com.korail.mobile.push.update`; service `com/korail/talk/network/dao/push/PushService.java`; caller `com/korail/talk/network/dao/push/PushUpdateDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `arvUsrInpTnum` | `String` | - | `getArvUsrInpTnum()` |
| `dptUsrInpTnum` | `String` | - | `getDptUsrInpTnum()` |
| `prs_cnqe_msg_cd` | `String` | - | `getPrs_cnqe_msg_cd()` |
| `tnsm_flg1` | `String` | - | `getTnsm_flg1()` |
| `tnsm_flg2` | `String` | - | `getTnsm_flg2()` |
| `tnsm_flg3` | `String` | - | `getTnsm_flg3()` |
| `tnsm_flg4` | `String` | - | `getTnsm_flg4()` |

### `dao.railplus.AutoChargeDao.AutoChargeResponse`

- 소스: `com/korail/talk/network/dao/railplus/AutoChargeDao.java:34`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `RailPlusService.getAutoCharge()` GET `/classes/com.korail.mobile.railplus.autoCharge.do`; service `com/korail/talk/network/dao/railplus/RailPlusService.java`; caller `com/korail/talk/network/dao/railplus/AutoChargeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `psbFlg` | `String` | - | `getPsbFlg()` |

### `dao.receipt.ReceiptDao.ReceiptResponse`

- 소스: `com/korail/talk/network/dao/receipt/ReceiptDao.java:231`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ReceiptService.getTicketReceipt()` POST `/classes/com.korail.mobile.receipt.ReceiptInfo`; service `com/korail/talk/network/dao/receipt/ReceiptService.java`; caller `com/korail/talk/network/dao/receipt/ReceiptDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `receipt_infos` | `ReceiptInfos` | - | `getReceipt_infos()` |

### `dao.refund.RefundCommissionDao.RefundCommissionResponse`

- 소스: `com/korail/talk/network/dao/refund/RefundCommissionDao.java:70`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `RefundService.getTicketCommission()` POST `/classes/com.korail.mobile.refunds.CommissionView`; service `com/korail/talk/network/dao/refund/RefundService.java`; caller `com/korail/talk/network/dao/refund/RefundCommissionDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_msg_cd2` | `String` | - | `getH_msg_cd2()` |
| `h_msg_txt2` | `String` | - | `getH_msg_txt2()` |
| `prg_psb_flg` | `String` | - | `getPrg_psb_flg()` |
| `ret_amt` | `String` | - | `getRet_amt()` |
| `ret_fee` | `String` | - | `getRet_fee()` |
| `tk_ret_tms_dv_cd` | `String` | - | `getTk_ret_tms_dv_cd()` |
| `use_psb_mlg_num` | `String` | - | `getUse_psb_mlg_num()` |

### `dao.refund.RefundDao.RefundResponse`

- 소스: `com/korail/talk/network/dao/refund/RefundDao.java:117`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `RefundService.returnTicket()` POST `/classes/com.korail.mobile.refunds.RefundsRequest`; service `com/korail/talk/network/dao/refund/RefundService.java`; caller `com/korail/talk/network/dao/refund/RefundDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `stlList` | `List<StlList>` | - | `getStlList()` |

### `dao.refund.RefundExecuteTicketRefundDao.RefundExecuteTicketRefundResponse`

- 소스: `com/korail/talk/network/dao/refund/RefundExecuteTicketRefundDao.java:124`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `RefundService.executeOnlineRefunds()` POST `/classes/com.korail.mobile.refunds.executeOnlineRefunds`; service `com/korail/talk/network/dao/refund/RefundService.java`; caller `com/korail/talk/network/dao/refund/RefundExecuteTicketRefundDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_ret_dv_cd` | `String` | - | `getH_ret_dv_cd()` |

### `dao.refund.RefundVerifyTicketDao.RefundVerifyTicketResponse`

- 소스: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java:63`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: `JrnyInfo`(8 fields), `Orgtkinfo`(9 fields), `SeatInfo`(3 fields)
- `RefundService.verifyOnlineRefunds()` POST `/classes/com.korail.mobile.refunds.verifyOnlineRefunds`; service `com/korail/talk/network/dao/refund/RefundService.java`; caller `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `orgtkinfo_list` | `ArrayList<Orgtkinfo>` | - | `getOrgTkInfos()` |
| `poppMsg` | `String` | - | `getPopMsg()` |
| `rcvd_amt` | `String` | - | `getRcvd_amt()` |
| `ret_amt` | `String` | - | `getRet_amt()` |
| `ret_fee` | `String` | - | `getRet_fee()` |

중첩 payload:

- `JrnyInfo` (implements `Serializable`; source line 70): `arv_rs_stn_cd`:`String` {getArv_rs_stn_cd()}; `arv_tm`:`String`; `dpt_dt`:`String` {getDpt_dt()}; `dpt_rs_stn_cd`:`String` {getDpt_rs_stn_cd()}; `dpt_tm`:`String` {getDpt_tm()}; `seatinfo_list`:`ArrayList<SeatInfo>` {getSeatinfo_list()}; `trn_gp_cd`:`String` {getTrn_gp_cd()}; `trn_no`:`String` {getTrn_no()}
- `Orgtkinfo` (implements `Serializable`; source line 116): `jrnyinfo_list`:`ArrayList<JrnyInfo>` {getJrnyinfo_list()}; `ogtk_ret_pwd`:`String` {getOgtk_ret_pwd()}; `ogtk_sale_dt`:`String` {getOgtk_sale_dt()}; `ogtk_sale_sqno`:`String` {getOgtk_sale_sqno()}; `ogtk_sale_wct_no`:`String` {getOgtk_sale_wct_no()}; `prnNo`:`String` {getPrnNo()}; `ret_dv_cd`:`String` {getRet_dv_cd()}; `ret_rsn_cd`:`String` {getRet_rsn_cd()}; `tk_knd_cd`:`String` {getTk_knd_cd()}
- `SeatInfo` (implements `Serializable`; source line 167): `psrm_cl_nm`:`String` {getPsrm_cl_nm()}; `scar_no`:`String` {getScar_no()}; `seat_no`:`String` {getSeat_no()}

### `dao.refund.TicketDetailDao.TicketDetailResponse`

- 소스: `com/korail/talk/network/dao/refund/TicketDetailDao.java:226`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `RefundService.getTicketDetail()` POST `/classes/com.korail.mobile.refunds.SelTicketInfo`; service `com/korail/talk/network/dao/refund/RefundService.java`; caller `com/korail/talk/network/dao/refund/TicketDetailDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `addSrvCancel` | `String` | - | `getAddSrvCancel()` |
| `addSrvFlg` | `String` | - | `getAddSrvFlg()` |
| `addSrvList` | `AddSrvList` | - | `getAddSrvList()` |
| `cmpa_info` | `List<CompanionInfo>` | - | `getCmpa_info()` |
| `cstmzPhrase` | `String` | - | `getCstmzPhrase()` |
| `dcnt_crd_info` | `DiscountCardInfo` | - | `getDcnt_crd_info()` |
| `dtlList` | `List<DelayInfo>` | - | `getDtlList()` |
| `gurdSmsFlg` | `String` | - | `getGurdSmsFlg()` |
| `h_abrd_ps_nm` | `String` | - | `getH_abrd_ps_nm()` |
| `h_abrd_ps_sex` | `String` | - | `getH_abrd_ps_sex()` |
| `h_cmtr_utl_trm_age_cd` | `String` | - | `getH_cmtr_utl_trm_age_cd()` |
| `h_cmtr_utl_trm_cd_nm` | `String` | - | `getH_cmtr_utl_trm_cd_nm()` |
| `h_compa_brth` | `String` | - | `getH_compa_brth()` |
| `h_compa_nm` | `String` | - | `getH_compa_nm()` |
| `h_dlay_flg` | `String` | - | `getH_dlay_flg()` |
| `h_dlay_tk_flg` | `String` | - | `getH_dlay_tk_flg()` |
| `h_dscp_no` | `String` | - | `getH_dscp_no()` |
| `h_dtour` | `String` | - | `getH_dtour()` |
| `h_orgtk_ret_pwd` | `String` | - | `getH_orgtk_ret_pwd()` |
| `h_orgtk_ret_sale_dt` | `String` | - | `getH_orgtk_ret_sale_dt()` |
| `h_orgtk_sale_sqno` | `String` | - | `getH_orgtk_sale_sqno()` |
| `h_orgtk_wct_no` | `String` | - | `getH_orgtk_wct_no()` |
| `h_pbp_acep_tgt_flg` | `String` | - | `getH_pbp_acep_tgt_flg()`, `setH_pbp_acep_tgt_flg()` |
| `h_pnr_no` | `String` | - | `getH_pnr_no()` |
| `h_qrcode` | `String` | - | `getH_qrcode()` |
| `h_ret_flg` | `String` | - | `getH_ret_flg()` |
| `h_sale_dt` | `String` | - | `getH_sale_dt()` |
| `h_sale_tm` | `String` | - | `getH_sale_tm()` |
| `h_schd_tk_knd_cd` | `String` | - | `getH_schd_tk_knd_cd()` |
| `h_tk_knd_cd` | `String` | - | `getH_tk_knd_cd()` |
| `h_tk_knd_nm` | `String` | - | `getH_tk_knd_nm()` |
| `h_tot_disc_amt` | `String` | - | `getH_tot_disc_amt()` |
| `h_tot_fare_amt` | `String` | - | `getH_tot_fare_amt()` |
| `h_tot_rcvd_amt` | `String` | - | `getH_tot_rcvd_amt()` |
| `h_trn_running_flg` | `String` | - | `getH_trn_running_flg()` |
| `h_wct_nm` | `String` | - | `getH_wct_nm()` |
| `limousine` | `Limousine` | - | `getLimousine()` |
| `limousineRsvPsbFlg` | `String` | - | `getLimousineRsvPsbFlg()` |
| `mlgSaveFlg` | `String` | - | `getMlgSaveFlg()` |
| `parkingLotUrl` | `String` | - | `getParkingLotUrl()` |
| `pbpAcepPsQryFlg` | `String` | - | `getPbpAcepPsQryFl()` |
| `pbpAcepPsbFlg` | `String` | - | `getPbpAcepPsbFlg()` |
| `psgNmList` | `List<FamilyInfo>` | - | `getPsgNmList()` |
| `retPsbFlg` | `String` | - | `getRetPsbFlg()` |
| `s_brth` | `String` | - | `getS_brth()` |
| `seatAppPsbFlg` | `String` | - | `getSeatAppPsbFlg()` |
| `stnLeadFlg` | `String` | - | `getStnLeadFlg()` |
| `stndAppPsbFlg` | `String` | - | `getStndAppPsbFlg()` |
| `ticketTimeBgColor` | `String` | - | `getTicketTimeBgColor()` |
| `ticket_infos` | `TicketInfos` | - | `getTicket_infos()` |
| `tripChgFlg` | `String` | - | `getTripChgFlg()` |
| `whchSrvRcpFlg` | `String` | - | `getWhchSrvRcpFlg()` |
| `whchSrvReqPsbFlg` | `String` | - | `getWhchSrvReqPsbFlg()` |

### `dao.research.CmtrInfoDao.CmtrInfoResponse`

- 소스: `com/korail/talk/network/dao/research/CmtrInfoDao.java:110`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getCmtrInfo()` POST `/classes/com.korail.mobile.research.cmtrInfo.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/CmtrInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `addSrvGdFlg` | `String` | - | `getAddSrvGdFlg()` |
| `avlPrnbFrom` | `int` | - | `getAvlPrnbFrom()` |
| `avlPrnbTo` | `int` | - | `getAvlPrnbTo()` |
| `cmpaFlg` | `String` | - | `getCmpaFlg()` |
| `cmtrKndCd` | `String` | - | `getCmtrKndCd()` |
| `cmtrUtlAgeCd` | `String` | - | `getCmtrUtlAgeCd()` |
| `menuId` | `String` | - | `getMenuId()` |
| `poppMsg` | `String` | - | `getPoppMsg()` |
| `prmoMsg` | `String` | - | `getPrmoMsg()` |
| `prmoUrl` | `String` | - | `getPrmoUrl()` |
| `psgList` | `List<Psg>` | - | `getPsgList()` |
| `seatAttCd1` | `String` | - | `getSeatAttCd1()` |

### `dao.research.ConvenienceSettingDao.ConvenienceSettingResponse`

- 소스: `com/korail/talk/network/dao/research/ConvenienceSettingDao.java:45`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getCustTripInfo()` POST `/classes/com.korail.mobile.research.custTripInfo.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/ConvenienceSettingDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `mainList` | `List<CustTripInfo>` | - | `getMainList()` |

### `dao.research.MergeSeatInquiryDao.MergeSeatInquiryResponse`

- 소스: `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java:99`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getMergeSeatsInquiry()` POST `/classes/com.korail.mobile.research.mergeSeatsC.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `midStnList` | `List<MidStnList.MidStationInfo>` | - | `getMidStnList()` |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | - | `getTrnInfos()` |

### `dao.research.NCardHistoryDao.NCardHistoryResponse`

- 소스: `com/korail/talk/network/dao/research/NCardHistoryDao.java:77`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getNCardHistory()` GET `/classes/com.korail.mobile.ticket.dcntCrdUseQry.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/NCardHistoryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `tkUseList` | `List<NCardHistoryInfo>` | - | `getTkUseList()` |

### `dao.research.NCardInquiryDao.NCardInquiryResponse`

- 소스: `com/korail/talk/network/dao/research/NCardInquiryDao.java:127`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getNCardSchedultView()` GET `/classes/com.korail.mobile.research.dcntCrdScheduleView.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/NCardInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fllwPgExt` | `String` | - | `getFllwPgExt()` |
| `trnScdlList` | `List<TrainInfo>` | - | `getTrnScdlList()` |

### `dao.research.NCardReservationDao.NCardReservationResponse`

- 소스: `com/korail/talk/network/dao/research/NCardReservationDao.java:126`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `ResearchService.setNCardReservation()` POST `/classes/com.korail.mobile.research.dcntCrdInfo.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/NCardReservationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `lumpStlTgtNo` | `String` | - | `getLumpStlTgtNo()` |
| `mStationInfo` | `String` | - | `getStationInfo()`, `setStationInfo()` |
| `mUserNames` | `String` | - | `getUserNames()`, `setUserNames()` |
| `rcvdAmt` | `String` | - | `getRcvdAmt()` |
| `usePsbTno` | `String` | - | `getUsePsbTno()` |
| `vlidTrmClsDt` | `String` | - | `getVlidTrmClsDt()` |
| `vlidTrmStDt` | `String` | - | `getVlidTrmStDt()` |

### `dao.research.OgTkInquiryDao.OgTkInquiryResponse`

- 소스: `com/korail/talk/network/dao/research/OgTkInquiryDao.java:37`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getTicketOriginalInquiry()` POST `/classes/com.korail.mobile.research.tripChgOgtk.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/OgTkInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `orgTkList` | `List<OrgTk>` | - | `getOrgTkList()` |

### `dao.research.SearchCarListDao.SearchCarListResponse`

- 소스: `com/korail/talk/network/dao/research/SearchCarListDao.java:51`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getCarList()` POST `/classes/com.korail.mobile.research.TrainResearch`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/SearchCarListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_rcmd_srcar_no` | `int` | - | `getHRcmdSrcarNo()` |
| `h_trn_no` | `String` | - | `getHTrnNo()` |
| `srcar_infos` | `CarInfos` | - | `getSrcar_infos()` |

### `dao.research.SearchSeatListDao.SearchSeatListResponse`

- 소스: `com/korail/talk/network/dao/research/SearchSeatListDao.java:14`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getSeatList()` POST `/classes/com.korail.mobile.research.TResidualSeatsResearch.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/SearchSeatListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `layout_type` | `int` | - | `getLayout_type()` |
| `seatList` | `List<Seat>` | - | `getSeatList()` |
| `seat_ary_cd` | `String` | - | `getSeat_ary_cd()` |
| `seat_remain_count` | `int` | - | `getSeat_remain_count()` |
| `seat_total_count` | `int` | - | `getSeat_total_count()` |
| `vrBnrUrl` | `String` | - | `getVrBnrUrl()` |
| `windowList` | `List<Window>` | - | `getWindowList()` |

### `dao.research.SeatAssignScheduleViewDao.SeatAssignScheduleViewResponse`

- 소스: `com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java:148`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ResearchService.getAssignScheduleView()` POST `/classes/com.korail.mobile.research.assignScheduleView.do`; service `com/korail/talk/network/dao/research/ResearchService.java`; caller `com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_next_pg_flg` | `String` | - | `getH_next_pg_flg()` |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | - | `getTrn_infos()` |

### `dao.reservation.TicketRsvHistoryDao.TicketRsvHistoryResponse`

- 소스: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java:33`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `ReservationService.getRsvHistory()` GET `/classes/com.korail.mobile.reservation.ReservationView`; service `com/korail/talk/network/dao/reservation/ReservationService.java`; caller `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `jrny_infos` | `JrnyInfos` | - | `getJrny_infos()` |

### `dao.reservationCancel.ReservationChangeDao.ReservationChangeResponse`

- 소스: `com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java:150`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `BusReservationService.reservationChange()` POST `/classes/com.korail.mobile.reservation.reservationChange.do`; service `com/korail/talk/network/dao/certification/BusReservationService.java`; caller caller 미확인
- `ReservationCancelService.reservationChange()` POST `/classes/com.korail.mobile.reservation.reservationChange.do`; service `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java`; caller `com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `jrnyList` | `List<JrnyInfo>` | - | `getJrnyList()` |

### `dao.schedule.TrainCalendarDao.TrainCalendarResponse`

- 소스: `com/korail/talk/network/dao/schedule/TrainCalendarDao.java:12`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: `RunningCalendar`(14 fields)
- `CalendarService.getTrainCalendar()` GET `/classes/com.korail.mobile.schedule.runDt`; service `com/korail/talk/network/dao/schedule/CalendarService.java`; caller `com/korail/talk/network/dao/schedule/TrainCalendarDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `runningCalendar` | `List<RunningCalendar>` | - | `getRunningCalendarList()` |

중첩 payload:

- `RunningCalendar` (implements `Comparable<RunningCalendar>`; source line 15): `aTrnOpFlg`:`String` {isATrainAvailable()}; `bizDdStgCd`:`String` {getBizDdStgCd(),isPeakSeason(),setBizDdStgCd()}; `dTrnOpFlg`:`String` {isDMZTrainAvailable()}; `dayDvCd`:`String`; `gTrnOpFlg`:`String` {isGTrainAvailable()}; `hldyDvCd`:`String` {isHoliday()}; `oTrnOpFlg`:`String` {isOTrainAvailable()}; `runDt`:`String` {getDateStr()}; `sTrnOpFlg`:`String` {isSTrainAvailable()}; `saleDdDvCd`:`String` {isForSaleDate()}; `vTrnOpFlg`:`String` {isVTrainAvailable()}; `xTrnOpFlg`:`String` {isXTrainAvailable()}; `str`:`String` {setBizDdStgCd()}; `0`:`return`

### `dao.ticket.DlvRcvCustDao.DlvRcvCustwResponse`

- 소스: `com/korail/talk/network/dao/ticket/DlvRcvCustDao.java:52`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.dlvRcvCust()` POST `/classes/com.korail.mobile.tk.dlvRcvCust.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/DlvRcvCustDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `acepCustMgNo` | `String` | - | `getAcepCustMgNo()` |
| `acepCustNm` | `String` | - | `getAcepCustNm()` |
| `acepCustTeln` | `String` | - | `getAcepCustTeln()` |
| `mbCrdNo` | `String` | - | `getMbCrdNo()` |

### `dao.ticket.MaasServiceCancelFeeDao.MaasServiceCancelFeeResponse`

- 소스: `com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java:43`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.getMaasServiceCancelFee()` POST `/classes/com.korail.mobile.maas.cncFee.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `cncRetFee` | `String` | - | `getCncRetFee()`, `setCncRetFee()` |

### `dao.ticket.MaasServiceDetailListDao.MaasServivceDetailResponse`

- 소스: `com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java:142`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.getMaasServiceDetailList()` POST `/classes/com.korail.mobile.copt.gdReqQry.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `addSrvList` | `List<AddSrvItem>` | - | `getAddSrvList()` |

### `dao.ticket.PbpAcepSpecDao.PbpAcepSpecResponse`

- 소스: `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java:86`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.pbpAcepSpec()` POST `/classes/com.korail.mobile.tk.pbpAcepSpec.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `tkList` | `List<Tk>` | - | `getTkList()` |

### `dao.ticket.RecentDeliveryHistoryDao.RcntDlvHstResponse`

- 소스: `com/korail/talk/network/dao/ticket/RecentDeliveryHistoryDao.java:63`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.rcntDlvHst()` POST `/classes/com.korail.mobile.tk.rcntDlvHst.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/RecentDeliveryHistoryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `acepList` | `List<Acep>` | - | `getAcepList()` |

### `dao.ticket.SelfCheckinInfoDao.SelfCheckinInfoResponse`

- 소스: `com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.selfCheckinInfo()` POST `/classes/com.korail.mobile.checkin.info.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `arvDttm` | `String` | - | `getArvDttm()`, `setArvDttm()` |
| `arvRsStnCd` | `String` | - | `getArvRsStnCd()`, `setArvRsStnCd()` |
| `arvRsStnNm` | `String` | - | `getArvRsStnNm()`, `setArvRsStnNm()` |
| `arvStnConsOrdr` | `String` | - | `getArvStnConsOrdr()`, `setArvStnConsOrdr()` |
| `arvTmQb` | `String` | - | `getArvTmQb()`, `setArvTmQb()` |
| `asgnSqno` | `String` | - | `getAsgnSqno()`, `setAsgnSqno()` |
| `chcknCncDt` | `String` | - | `getChcknCncDt()`, `setChcknCncDt()` |
| `chcknCncTm` | `String` | - | `getChcknCncTm()`, `setChcknCncTm()` |
| `chcknDt` | `String` | - | `getChcknDt()`, `setChcknDt()` |
| `chcknDvCd` | `String` | - | `getChcknDvCd()`, `setChcknDvCd()` |
| `chcknSqno` | `String` | - | `getChcknSqno()`, `setChcknSqno()` |
| `chcknTm` | `String` | - | `getChcknTm()`, `setChcknTm()` |
| `dptDttm` | `String` | - | `getDptDttm()`, `setDptDttm()` |
| `dptRsStnCd` | `String` | - | `getDptRsStnCd()`, `setDptRsStnCd()` |
| `dptRsStnNm` | `String` | - | `getDptRsStnNm()`, `setDptRsStnNm()` |
| `dptStnConsOrdr` | `String` | - | `getDptStnConsOrdr()`, `setDptStnConsOrdr()` |
| `dptTmQb` | `String` | - | `getDptTmQb()`, `setDptTmQb()` |
| `jrnySqno` | `String` | - | `getJrnySqno()`, `setJrnySqno()` |
| `pnrNo` | `String` | - | `getPnrNo()`, `setPnrNo()` |
| `runDt` | `String` | - | `getRunDt()`, `setRunDt()` |
| `scarNo` | `String` | - | `getScarNo()`, `setScarNo()` |
| `seatNo` | `String` | - | `getSeatNo()`, `setSeatNo()` |
| `stlbTrnClsfNm` | `String` | - | `getStlbTrnClsfNm()`, `setStlbTrnClsfNm()` |
| `trnNo` | `String` | - | `getTrnNo()`, `setTrnNo()` |

### `dao.ticket.SelfCheckinPossibleDao.SelfCheckinPossibleResponse`

- 소스: `com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java:157`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.selfCheckinPossible()` POST `/classes/com.korail.mobile.checkin.psbFlg.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `consList` | `List<ConsList>` | - | `getConsList()` |

### `dao.ticket.TicketDuplicationCheckDao.DuplicationCheckResponse`

- 소스: `com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java:25`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.duplicationCheck()` POST `/classes/com.korail.mobile.ticket.ticketDupCheck.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `rsvCnt` | `int` | - | `getRsvCnt()` |

### `dao.ticket.UpdatePlatformDao.PlfNoResponse`

- 소스: `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java:48`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TicketService.plfNo()` POST `/classes/com.korail.mobile.tk.plfNo.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `tkList` | `List<TkList>` | - | `getAcepList()` |

### `dao.ticket.change.CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse`

- 소스: `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java:64`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `TicketService.getSelfSeatChgInfo()` POST `/classes/com.korail.mobile.self.seatChgInfo.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `chgBfArvStnConsOrdr` | `String` | - | `getChgBfArvStnConsOrdr()` |
| `chgBfDptStnConsOrdr` | `String` | - | `getChgBfDptStnConsOrdr()` |
| `chgRsnList` | `List<ChgRsnList>` | - | `getChgRsnList()` |
| `chgStnList` | `List<ChgStnList>` | - | `getChgStnList()` |
| `exsArvStnRunOrdr` | `String` | - | `getExsArvStnRunOrdr()` |
| `exsDptStnRunOrdr` | `String` | - | `getExsDptStnRunOrdr()` |
| `gnrmRsvPsbCd` | `String` | - | `getGnrmRsvPsbCd()` |
| `runDt` | `String` | - | `getRunDt()` |
| `sprmRsvPsbCd` | `String` | - | `getSprmRsvPsbCd()` |
| `trnClsfCd` | `String` | - | `getTrnClsfCd()` |
| `trnClsfNm` | `String` | - | `getTrnClsfNm()` |
| `trnGpCd` | `String` | - | `getTrnGpCd()` |
| `trnGpNm` | `String` | - | `getTrnGpNm()` |
| `trnNo` | `String` | - | `getTrnNo()` |

### `dao.ticket.change.TripChgInfoDao.TripChgInfoDaoResponse`

- 소스: `com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java:28`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: -
- `TicketService.getTripChgDate()` POST `/classes/com.korail.mobile.reservation.tripChgDate.do`; service `com/korail/talk/network/dao/ticket/TicketService.java`; caller `com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `lastRunDt` | `String` | - | `getLastRunDt()` |
| `tripChgDate` | `String` | - | - |
| `tripChgDates` | `List<String>` | - | `getTripChgDates()` |

### `dao.trainsInfo.FresScarDao.FresScarResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/FresScarDao.java:70`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TrainsInfoService.getFresScar()` POST `/classes/com.korail.mobile.trn.fresScar.do`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/FresScarDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `fresCont` | `String` | - | `getFresCont()` |
| `fresScarNo` | `String` | - | `getFresScarNo()` |
| `fresTtl` | `String` | - | `getFresTtl()` |

### `dao.trainsInfo.Price2FareDao.Price2FareResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java:178`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TrainsInfoService.getPrice2Fare()` POST `/classes/com.korail.mobile.trn.prcFare.do`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `prcList` | `List<Price2Fare>` | - | `getPrcList()` |

### `dao.trainsInfo.PriceFareDao.PriceFareResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java:145`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: `PrcFareList`(1 fields)
- `TrainsInfoService.getPriceFare()` POST `/classes/com.korail.mobile.trainsInfo.TrainCharge`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `prc_fare_list` | `PrcFareList` | - | `getPrc_fare_list()` |

중첩 payload:

- `PrcFareList` (없음; source line 148): `jrny_info`:`List<JrnyInfo>` {getJrny_info()}

### `dao.trainsInfo.TourTrainInfoDao.TourTrainInfoResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java:112`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TrainsInfoService.getTourTrainInfo()` POST `/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `seat_infos` | `SeatInfos` | - | `getSeat_infos()` |

### `dao.trainsInfo.TrainScheduleDao.TrainScheduleResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java:115`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TrainsInfoService.getTrainSchedule()` POST `/classes/com.korail.mobile.research.actualTrainSchedule.do`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `dlayDtlRsnCont` | `String` | - | `getDlayDtlRsnCont()` |
| `dlayList` | `List<TimeInfo>` | - | `getDlayList()` |
| `msgCont` | `String` | - | `getMsgCont()` |
| `runDt1` | `String` | - | `getRunDt1()` |
| `runSegOrdr` | `String` | - | `getRunSegOrdr()` |
| `trnDptFlg` | `String` | - | `getTrnDptFlg()` |
| `trnNo1` | `String` | - | `getTranNo1()` |

### `dao.trainsInfo.TrainSelectStationDao.TrainSelectStationResponse`

- 소스: `com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java:35`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `TrainsInfoService.getSelectStationInfo()` POST `/classes/com.korail.mobile.qry.chtnStn.do`; service `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java`; caller `com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `chtnList` | `List<TransferStationInfo>` | - | `getChtnList()` |

### `dao.xPoint.KorailPointInquiryDao.KorailPointInquiryResponse`

- 소스: `com/korail/talk/network/dao/xPoint/KorailPointInquiryDao.java:10`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `XPointService.getKorailPoint()` POST `/classes/com.korail.mobile.xPoint.MyXPointView`; service `com/korail/talk/network/dao/xPoint/XPointService.java`; caller `com/korail/talk/network/dao/xPoint/KorailPointInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_cntc_chn_cont1` | `String` | - | `getH_cntc_chn_cont1()` |
| `h_cp_athn_flg` | `String` | - | `getH_cp_athn_flg()` |
| `h_cust_lead_flg_nm` | `String` | - | `getH_cust_lead_flg_nm()` |
| `h_delay_cnt` | `String` | - | `getH_delay_cnt()` |
| `h_disc_coup_cnt` | `String` | - | `getH_disc_coup_cnt()` |
| `h_emil_athn_flg` | `String` | - | `getH_emil_athn_flg()` |
| `h_hdcp_flg` | `String` | - | `getH_hdcp_flg()` |
| `h_korail_point` | `String` | - | `getH_korail_point()` |
| `h_logn_tp_cd1` | `String` | - | `getH_logn_tp_cd1()` |
| `h_logn_tp_cd2` | `String` | - | `getH_logn_tp_cd2()` |
| `h_logn_tp_cd4` | `String` | - | `getH_logn_tp_cd4()` |
| `h_logn_tp_cd5` | `String` | - | `getH_logn_tp_cd5()` |
| `h_subt_dcs_cl_cd` | `String` | - | `getH_subt_dcs_cl_cd()` |
| `h_subt_dcs_cl_nm` | `String` | - | `getH_subt_dcs_cl_nm()` |

### `dao.xPoint.LPointDao.LPointInquiryResponse`

- 소스: `com/korail/talk/network/dao/xPoint/LPointDao.java:43`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `XPointService.getLPoint()` POST `/classes/com.korail.mobile.mlg.lpotAthn.do`; service `com/korail/talk/network/dao/xPoint/XPointService.java`; caller `com/korail/talk/network/dao/xPoint/LPointDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `custRcgnNoVal` | `String` | - | `getCustRcgnNoVal()` |
| `extrPontAmt` | `String` | - | `getExtrPontAmt()` |
| `prsCnqeVal` | `String` | - | `getPrsCnqeVal()` |
| `pwdErrTno` | `String` | - | `getPwdErrTno()` |

### `dao.xPoint.MileageInquiryDao.MileageInquiryResponse`

- 소스: `com/korail/talk/network/dao/xPoint/MileageInquiryDao.java:71`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `XPointService.getMileage()` POST `/classes/com.korail.mobile.mlg.amtSpec.do`; service `com/korail/talk/network/dao/xPoint/XPointService.java`; caller `com/korail/talk/network/dao/xPoint/MileageInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `delPontValNum` | `String` | - | `getDelPontValNum()` |
| `ktxMlgInfo` | `String` | - | `getKtxMlgInfo()` |
| `pgCnt` | `String` | - | `getPgCnt()` |
| `railNowSavePontValNum1` | `String` | - | `getrailNowSavePontValNum1()` |
| `specList` | `List<SpecList>` | - | `getSpecList()` |
| `totAcmRailPontValNum1` | `String` | - | `gettotAcmRailPontValNum1()` |
| `totAvlAfltPontValNum` | `String` | - | `getTotAvlAfltPontValNum()` |
| `totAvlRailPontValNum` | `String` | - | `getTotAvlRailPontValNum()` |
| `totAvlRailPontValNum1` | `String` | - | `gettotAvlRailPontValNum1()` |
| `totUseRailPontValNum1` | `String` | - | `gettotUseRailPontValNum1()` |

### `dao.xPoint.PointInquiryDao.PointInquiryResponse`

- 소스: `com/korail/talk/network/dao/xPoint/PointInquiryDao.java:61`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: -
- `XPointService.getPoint()` POST `/classes/com.korail.mobile.xPoint.XPointView`; service `com/korail/talk/network/dao/xPoint/XPointService.java`; caller `com/korail/talk/network/dao/xPoint/PointInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_avl_point` | `int` | - | `getH_avl_point()` |
| `h_corp_use_point` | `int` | - | `geth_corp_use_point()` |
| `h_join_point` | `int` | - | `getH_join_point()` |
| `h_korail_point` | `int` | - | `getH_korail_point()` |
| `h_point` | `int` | - | `getH_point()` |

### `data.addService.ExtraProductInfo`

- 소스: `com/korail/talk/network/data/addService/ExtraProductInfo.java:10`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: `AddSrvInfo`(19 fields)
- endpoint mapping: **미확인** (Retrofit service 반환형으로 추적되지 않음)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `addSrvList` | `List<AddSrvInfo>` | - | `getAddSrvList()` |
| `arvDt` | `String` | - | `getArvDt()` |
| `arvRsStnCd` | `String` | - | `getArvRsStnCd()` |
| `arvTm` | `String` | - | `getArvTm()` |
| `dptDt` | `String` | - | `getDptDt()` |
| `dptRsStnCd` | `String` | - | `getDptRsStnCd()` |
| `dptTm` | `String` | - | `getDptTm()` |
| `jrnySqno` | `String` | - | `getJrnySqno()` |
| `pnrNo` | `String` | - | `getPnrNo()` |

중첩 payload:

- `AddSrvInfo` (implements `Serializable`; source line 20): `addSrvDvCd`:`String` {getAddSrvDvCd()}; `addSrvMrkEntId`:`String` {getAddSrvMrkEntId()}; `addSrvMrkEntNm`:`String` {getAddSrvMrkEntNm()}; `addSrvNm`:`String` {getAddSrvNm()}; `addSrvPrgSttCd`:`String` {getAddSrvPrgSttCd()}; `addSrvReqNo`:`String` {getAddSrvReqNo()}; `addSrvUtlAmt`:`String` {getAddSrvUtlAmt()}; `cgPsRefAtclCont`:`String` {getCgPsRefAtclCont()}; `coptEntRsvNo`:`String` {getCoptEntRsvNo()}; `imgPath`:`String` {getImgPath()}; `leadMsgCont1`:`String` {getLeadMsgCont1()}; `leadMsgCont2`:`String` {getLeadMsgCont2()}; `leadTeln`:`String` {getLeadTeln()}; `reqDt`:`String` {getReqDt()}; `reqQnty`:`String` {getReqQnty()}; `reservationUrl`:`String` {getReservationUrl()}; `shopMapImgPath`:`String` {getShopMapImgPath()}; `spvsRsStnCd`:`String` {getSpvsRsStnCd()}; `spvsRsStnCdNm`:`String` {getSpvsRsStnCdNm()}

### `response.certification.ReservationResponse`

- 소스: `com/korail/talk/network/response/certification/ReservationResponse.java:8`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: `Dfpy`(4 fields), `JrnyInfo`(23 fields), `JrnyInfos`(1 fields), `PsgDiscAddInfo`(2 fields), `PsgDiscAddInfos`(1 fields), `PsgInfo`(10 fields), `PsgInfos`(1 fields), `SeatInfo`(17 fields), `SeatInfos`(1 fields), `StopStn`(1 fields), `TK`(1 fields)
- `CertificationService.getDiscountPrice()` POST `/classes/com.korail.mobile.certification.PriceReCalculation`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/DiscountPriceDao.java`
- `CertificationService.inquiryTicketRsv()` GET `/classes/com.korail.mobile.certification.ReservationList`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/TicketRsvInquiryDao.java`
- `CertificationService.reservation()` POST `/classes/com.korail.mobile.nonMember.NonMemTicket`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/BixbyReservationDao.java`, `com/korail/talk/network/dao/certification/ReservationDao.java`
- `CertificationService.reservation()` POST `/classes/com.korail.mobile.certification.TicketReservation`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/BixbyReservationDao.java`, `com/korail/talk/network/dao/certification/ReservationDao.java`
- `CertificationService.reservation()` POST `/classes/com.korail.mobile.nonMember.NonMemTicket`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/BixbyReservationDao.java`, `com/korail/talk/network/dao/certification/ReservationDao.java`
- `CertificationService.reservation()` POST `/classes/com.korail.mobile.certification.TicketReservation`; service `com/korail/talk/network/dao/certification/CertificationService.java`; caller `com/korail/talk/network/dao/certification/BixbyReservationDao.java`, `com/korail/talk/network/dao/certification/ReservationDao.java`
- `ReservationService.getTicketChangeReservation()` POST `/classes/com.korail.mobile.reservation.tripChgPrsC.do`; service `com/korail/talk/network/dao/reservation/ReservationService.java`; caller `com/korail/talk/network/dao/reservation/TCReservationDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `dfpyList` | `List<Dfpy>` | - | `getDfpyList()` |
| `h_add_srv_flg` | `String` | - | `getH_add_srv_flg()` |
| `h_cust_mg_no` | `String` | - | `getH_cust_mg_no()` |
| `h_fmly_info_cfm_flg` | `String` | - | `getH_fmly_info_cfm_flg()` |
| `h_hdcp_ctfc_num` | `int` | - | `getH_hdcp_ctfc_num()` |
| `h_ise_psb_dt` | `String` | - | `getH_ise_psb_dt()`, `setH_ise_psb_dt()` |
| `h_ise_psb_tm` | `String` | - | `getH_ise_psb_tm()`, `setH_ise_psb_tm()` |
| `h_jrny_cnt` | `String` | - | `getH_jrny_cnt()` |
| `h_msg_mndry` | `String` | - | `getH_msg_mndry()` |
| `h_msg_txt5` | `String` | - | `getH_msg_txt5()` |
| `h_ntisu_lmt` | `String` | - | `getH_ntisu_lmt()` |
| `h_ntisu_lmt_dt` | `String` | - | `getH_ntisu_lmt_dt()` |
| `h_ntisu_lmt_tm` | `String` | - | `getH_ntisu_lmt_tm()` |
| `h_pay_limit_msg` | `String` | - | `getPayLimitMsg()` |
| `h_payment_flg` | `String` | - | `getH_payment_flg()`, `setH_payment_flg()` |
| `h_payment_msg` | `String` | - | `getH_payment_msg()`, `setH_payment_msg()` |
| `h_pnr_no` | `String` | - | `getH_pnr_no()` |
| `h_pre_stl_tgt_flg` | `String` | - | `getH_pre_stl_tgt_flg()` |
| `h_sprm_fare` | `String` | - | `getH_sprm_fare()` |
| `h_tmp_job_sqno1` | `String` | - | `getH_tmp_job_sqno1()` |
| `h_tmp_job_sqno2` | `String` | - | `getH_tmp_job_sqno2()` |
| `h_tot_dcnt_amt` | `String` | - | `getH_tot_dcnt_amt()` |
| `h_tot_fare` | `String` | - | `getH_tot_fare()` |
| `h_tot_prc` | `String` | - | `getH_tot_prc()` |
| `h_tot_rcvd_amt` | `String` | - | `getH_tot_rcvd_amt()` |
| `h_wct_no` | `String` | - | `getH_wct_no()` |
| `jrny_infos` | `JrnyInfos` | - | `getJrny_infos()` |
| `ogtkRcvdAmt` | `int` | - | `getOgtkRcvdAmt()` |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | - | `getPsgDiscAdd_infos()`, `setPsgDiscAdd_infos()` |
| `psg_infos` | `PsgInfos` | - | `getPsg_infos()` |
| `scnIndcAmt` | `int` | - | `getScnIndcAmt()` |
| `stopStnList` | `List<StopStn>` | - | `getStopStnList()` |
| `tkList` | `List<TK>` | - | `getTkList()` |
| `totRetAmt` | `int` | - | `getTotRetAmt()` |

중첩 payload:

- `Dfpy` (implements `Serializable`; source line 43): `dfpyNo`:`String` {getDfpyNo()}; `dfpySrtCd`:`String` {getDfpySrtCd()}; `dscpMgNo`:`String` {getDscpMgNo()}; `stlAmt`:`int` {getStlAmt()}
- `JrnyInfo` (implements `Serializable`; source line 69): `h_arv_rs_stn_cd`:`String` {getH_arv_rs_stn_cd()}; `h_arv_rs_stn_nm`:`String` {getH_arv_rs_stn_nm()}; `h_arv_stn_cons_ordr`:`String` {getH_arv_stn_cons_ordr()}; `h_arv_tm`:`String` {getH_arv_tm()}; `h_dpt_dt`:`String` {getH_dpt_dt()}; `h_dpt_rs_stn_cd`:`String` {getH_dpt_rs_stn_cd()}; `h_dpt_rs_stn_nm`:`String` {getH_dpt_rs_stn_nm()}; `h_dpt_stn_cons_ordr`:`String` {getH_dpt_stn_cons_ordr()}; `h_dpt_tm`:`String` {getH_dpt_tm()}; `h_fres_cnt`:`int` {getH_fres_cnt()}; `h_jrny_sqno`:`String` {getH_jrny_sqno()}; `h_jrny_tp_cd`:`String` {getH_jrny_tp_cd()}; `h_rsv_chg_no`:`String` {getH_rsv_chg_no()}; `h_seat_cnt`:`int` {getH_seat_cnt()}; `h_stlb_trn_clsf_cd`:`String` {getH_stlb_trn_clsf_cd()}; `h_tot_seat_cnt`:`int` {getH_tot_seat_cnt()}; `h_tot_stnd_cnt`:`int` {getH_tot_stnd_cnt()}; `h_trn_clsf_cd`:`String` {getH_trn_clsf_cd()}; `h_trn_clsf_nm`:`String` {getH_trn_clsf_nm()}; `h_trn_gp_cd`:`String` {getH_trn_gp_cd()}; `h_trn_no`:`String` {getH_trn_no()}; `lumpStlTgtNo`:`String` {getLumpStlTgtNo()}; `seat_infos`:`SeatInfos` {getSeat_infos()}
- `JrnyInfos` (implements `Serializable`; source line 190): `jrny_info`:`List<JrnyInfo>` {getJrny_info()}
- `PsgDiscAddInfo` (implements `Serializable`; source line 201): `h_duty_ref_rcgn_ps_dv_cd`:`String` {getH_duty_ref_rcgn_ps_dv_cd()}; `h_psg_sqno`:`int` {getH_psg_sqno()}
- `PsgDiscAddInfos` (implements `Serializable`; source line 217): `psgDiscAdd_info`:`List<PsgDiscAddInfo>` {getPsgDiscAdd_info()}
- `PsgInfo` (implements `Serializable`; source line 228): `dlayOgtkRetPwd`:`String` {getDlayOgtkRetPwd()}; `dlayOgtkSaleDt`:`String` {getDlayOgtkSaleDt()}; `dlayOgtkSaleSqno`:`String` {getDlayOgtkSaleSqno()}; `dlayOgtkWctNo`:`String` {getDlayOgtkWctNo()}; `h_dcnt_knd_cd`:`String` {getH_dcnt_knd_cd()}; `h_dcnt_knd_cd2`:`String` {getH_dcnt_knd_cd2()}; `h_dcsp_no`:`String` {getH_dcsp_no()}; `h_dcsp_no2`:`String` {getH_dcsp_no2()}; `h_psg_info_per_prnb`:`String` {getH_psg_info_per_prnb()}; `h_psg_tp_cd`:`String` {getH_psg_tp_cd()}
- `PsgInfos` (implements `Serializable`; source line 284): `psg_info`:`List<PsgInfo>` {getPsgInfos()}
- `SeatInfo` (implements `Serializable`; source line 295): `dcnt_reld_no`:`String` {getDcnt_reld_no()}; `h_dcnt_knd_cd1`:`String` {getH_dcnt_knd_cd1()}; `h_dcnt_knd_cd2`:`String` {getH_dcnt_knd_cd2()}; `h_dcnt_knd_cd3`:`String` {getH_dcnt_knd_cd3()}; `h_dcnt_knd_cd4`:`String` {getH_dcnt_knd_cd4()}; `h_dcnt_knd_cd5`:`String` {getH_dcnt_knd_cd5()}; `h_dir_seat_att_cd`:`String` {getH_dir_seat_att_cd()}; `h_psg_tp_cd`:`String` {getH_psg_tp_cd()}; `h_psrm_cl_cd`:`String` {getH_psrm_cl_cd()}; `h_psrm_cl_nm`:`String` {getH_psrm_cl_nm()}; `h_rcvd_amt`:`String` {getH_rcvd_amt()}; `h_rq_seat_att_cd`:`String` {getH_rq_seat_att_cd()}; `h_seat_fare`:`String` {getH_seat_fare()}; `h_seat_no`:`String` {getH_seat_no()}; `h_seat_prc`:`String` {getH_seat_prc()}; `h_sgr_nm`:`String` {getH_sgr_nm()}; `h_srcar_no`:`String` {getH_srcar_no()}
- `SeatInfos` (implements `Serializable`; source line 386): `seat_info`:`List<SeatInfo>` {getSeat_info()}
- `StopStn` (implements `Serializable`; source line 397): `pnrNo`:`String` {getPnrNo()}
- `TK` (implements `Serializable`; source line 408): `saleWctNo`:`String` {getSaleWctNo()}

### `response.delay.RefundResponse`

- 소스: `com/korail/talk/network/response/delay/RefundResponse.java:9`
- 상속/구현: extends `BaseResponse`
- 중첩/관련 클래스: `StlList`(1 fields), `TicketList`(22 fields)
- endpoint mapping: **미확인** (Retrofit service 반환형으로 추적되지 않음)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `ticketList` | `List<TicketList>` | - | `getTicketList()` |
| `whlPgNum` | `int` | - | `getWhlPgNum()` |

중첩 payload:

- `StlList` (없음; source line 12): `stlMnsCd`:`String` {getStlMnsCd()}
- `TicketList` (없음; source line 23): `arvDt`:`String` {getArvDt()}; `arvRsStnNm`:`String` {getArvRsStnNm()}; `dlayFare`:`int` {getDlayFare()}; `dptRsStnNm`:`String` {getDptRsStnNm()}; `jrnyOrdr`:`String` {getJrnyOrdr()}; `jrnyStpTkFlg`:`String` {getJrnyStpTkFlg()}; `jrnyTpCd`:`String` {getJrnyTpCd()}; `rcVdAmt`:`int` {getRcVdAmt()}; `rcvdAmt`:`int` {getRcvdAmt()}; `refundAmount`:`String` {getRefundAmount(),setRefundAmount()}; `refundInfo`:`String` {getRefundInfo(),setRefundInfo()}; `refundJrny`:`String` {getRefundJrny(),setRefundJrny()}; `saleDd`:`String` {getSaleDd()}; `saleSqNo`:`String` {getSaleSqNo()}; `saleWctNo`:`String` {getSaleWctNo()}; `stlList`:`List<StlList>` {getStlList()}; `stlbTrnClsfNm`:`String` {getStlbTrnClsfNm()}; `tkRetPwd`:`String` {getTkRetPwd()}; `trnNo`:`int` {getTrnNo()}; `trnRunStpCpstAmt`:`int` {getTrnRunStpCpstAmt()}; `trnStpRsStnCd`:`String` {getTrnStpRsStnCd()}; `trnStpRsStnCdNm`:`String` {getTrnStpRsStnCdNm()}

### `response.research.Cmpn`

- 소스: `com/korail/talk/network/response/research/Cmpn.java:4`
- 상속/구현: 없음
- 중첩/관련 클래스: -
- 직접 endpoint mapping: 없음 (상위 응답의 payload 모델)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `cmpaNum` | `String` | - | `getCmpaNum()` |
| `custNm` | `String` | - | `getCustNm()` |
| `dcntAmt` | `String` | - | `getDcntAmt()` |
| `dcntKndCd` | `String` | - | `getDcntKndCd()` |
| `dcntKndCd2` | `String` | - | `getDcntKndCd2()` |
| `dcntRt` | `String` | - | `getDcntRt()` |
| `dlayOgtkRetPwd` | `String` | - | `getDlayOgtkRetPwd()` |
| `dlayOgtkSaleDt` | `String` | - | `getDlayOgtkSaleDt()` |
| `dlayOgtkSaleSqno` | `String` | - | `getDlayOgtkSaleSqno()` |
| `dlayOgtkWctNo` | `String` | - | `getDlayOgtkWctNo()` |
| `dscpNo` | `String` | - | `getDscpNo()` |
| `dscpNo2` | `String` | - | `getDscpNo2()` |
| `dscpNo3` | `String` | - | `getDscpNo3()` |
| `psgTpDvCd` | `String` | - | `getPsgTpDvCd()` |
| `psrmClCd` | `String` | - | `getPsrmClCd()` |
| `saleFlrVal` | `String` | - | `getSaleFlrVal()` |

### `response.research.Jrny`

- 소스: `com/korail/talk/network/response/research/Jrny.java:6`
- 상속/구현: 없음
- 중첩/관련 클래스: -
- 직접 endpoint mapping: 없음 (상위 응답의 payload 모델)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `alcStdrDvCd` | `String` | - | `getAlcStdrDvCd()` |
| `arvDt` | `String` | - | `getArvDt()` |
| `arvRsStnCd` | `String` | - | `getArvRsStnCd()` |
| `arvRsStnNm` | `String` | - | `getArvRsStnNm()` |
| `arvStnConsOrdr` | `String` | - | `getArvStnConsOrdr()` |
| `arvTm` | `String` | - | `getArvTm()` |
| `cndnDcntGdFlg` | `String` | - | `getCndnDcntGdFlg()` |
| `cndnDcntKndCd` | `String` | - | `getCndnDcntKndCd()` |
| `cndnDcntWdrwFlg` | `String` | - | `getCndnDcntWdrwFlg()` |
| `custNm` | `String` | - | `getCustNm()` |
| `dptDt` | `String` | - | `getDptDt()` |
| `dptRsStnCd` | `String` | - | `getDptRsStnCd()` |
| `dptRsStnNm` | `String` | - | `getDptRsStnNm()` |
| `dptStnConsOrdr` | `String` | - | `getDptStnConsOrdr()` |
| `dptTm` | `String` | - | `getDptTm()` |
| `gdMrkFlg` | `String` | - | `getGdMrkFlg()` |
| `gdNo` | `String` | - | `getGdNo()` |
| `genChgAllwFlg` | `String` | - | `getGenChgAllwFlg()` |
| `hmtkFlg` | `String` | - | `getHmtkFlg()` |
| `intgSaleFlg` | `String` | - | `getIntgSaleFlg()` |
| `jrnyOrdr` | `String` | - | `getJrnyOrdr()` |
| `jrnySqno` | `String` | - | `getJrnySqno()` |
| `jrnyTpCd` | `String` | - | `getJrnyTpCd()` |
| `mbCrdNo` | `String` | - | `getMbCrdNo()` |
| `medDvCd` | `String` | - | `getMedDvCd()` |
| `psgNm` | `String` | - | `getPsgNm()` |
| `saleFlrVal` | `String` | - | `getSaleFlrVal()` |
| `seatList` | `List<Seat>` | - | `getSeatList()` |
| `snglTkFlg` | `String` | - | `getSnglTkFlg()` |
| `totSeatNum` | `String` | - | `getTotSeatNum()` |
| `totStndNum` | `String` | - | `getTotStndNum()` |
| `trnGpCd` | `String` | - | `getTrnGpCd()` |
| `trnNo` | `String` | - | `getTrnNo()` |

### `response.research.OrgTk`

- 소스: `com/korail/talk/network/response/research/OrgTk.java:6`
- 상속/구현: 없음
- 중첩/관련 클래스: -
- 직접 endpoint mapping: 없음 (상위 응답의 payload 모델)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `adulCnt` | `String` | - | `getAdulCnt()` |
| `chgSaleTno` | `String` | - | `getChgSaleTno()` |
| `chilCnt` | `String` | - | `getChilCnt()` |
| `cmpnList` | `List<Cmpn>` | - | `getCmpnList()` |
| `dfpyRcvdAmt` | `String` | - | `getDfpyRcvdAmt()` |
| `dfpyRcvdFare` | `String` | - | `getDfpyRcvdFare()` |
| `dfpyRcvdPrc` | `String` | - | `getDfpyRcvdPrc()` |
| `frcSaleRsnCont` | `String` | - | `getFrcSaleRsnCont()` |
| `grpDcntCnt` | `String` | - | `getGrpDcntCnt()` |
| `jrnyList` | `List<Jrny>` | - | `getJrnyList()` |
| `mbCrdNo` | `String` | - | `getMbCrdNo()` |
| `ogtkRetPwd` | `String` | - | `getOgtkRetPwd()` |
| `ogtkSaleDt` | `String` | - | `getOgtkSaleDt()` |
| `ogtkSaleSqno` | `String` | - | `getOgtkSaleSqno()` |
| `ogtkSaleWctNo` | `String` | - | `getOgtkSaleWctNo()` |
| `pnrNo` | `String` | - | `getPnrNo()` |
| `psgTpDvCd` | `String` | - | `getPsgTpDvCd()` |
| `rcvdAmt` | `String` | - | `getRcvdAmt()` |
| `rcvdFare` | `String` | - | `getRcvdFare()` |
| `rcvdPrc` | `String` | - | `getRcvdPrc()` |
| `saleFlrVal` | `String` | - | `getSaleFlrVal()` |
| `smsSndFlg` | `String` | - | `getSmsSndFlg()` |
| `stlList` | `List<Stl>` | - | `getStlList()` |
| `tkKndCd` | `String` | - | `getTkKndCd()` |

### `response.research.Seat`

- 소스: `com/korail/talk/network/response/research/Seat.java:4`
- 상속/구현: 없음
- 중첩/관련 클래스: -
- 직접 endpoint mapping: 없음 (상위 응답의 payload 모델)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `addSeatAttCd` | `String` | - | `getAddSeatAttCd()` |
| `asgnSqno` | `String` | - | `getAsgnSqno()` |
| `dcntKndCdNm1` | `String` | - | `getDcntKndCdNm1()` |
| `dcntKndCdNm2` | `String` | - | `getDcntKndCdNm2()` |
| `dfpyFlg` | `String` | - | `getDfpyFlg()` |
| `dfpyRcvdFare` | `String` | - | `getDfpyRcvdFare()` |
| `dfpyRcvdPrc` | `String` | - | `getDfpyRcvdPrc()` |
| `dirSeatAttCd` | `String` | - | `getDirSeatAttCd()` |
| `etcSeatAttCd` | `String` | - | `getEtcSeatAttCd()` |
| `locSeatAttCd` | `String` | - | `getLocSeatAttCd()` |
| `prtDcntKndCd` | `String` | - | `getPrtDcntKndCd()` |
| `psgSqno` | `String` | - | `getPsgSqno()` |
| `psgTpDvCd` | `String` | - | `getPsgTpDvCd()` |
| `psrmClCd` | `String` | - | `getPsrmClCd()` |
| `rcvdFare` | `String` | - | `getRcvdFare()` |
| `rcvdPrc` | `String` | - | `getRcvdPrc()` |
| `rqSeatAttCd` | `String` | - | `getRqSeatAttCd()` |
| `saleFlrVal` | `String` | - | `getSaleFlrVal()` |
| `scarNo` | `String` | - | `getScarNo()` |
| `seatNo` | `String` | - | `getSeatNo()` |
| `seatNum` | `String` | - | `getSeatNum()` |
| `smkSeatAttCd` | `String` | - | `getSmkSeatAttCd()` |

### `response.research.Stl`

- 소스: `com/korail/talk/network/response/research/Stl.java:4`
- 상속/구현: 없음
- 중첩/관련 클래스: -
- 직접 endpoint mapping: 없음 (상위 응답의 payload 모델)

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `apvNo` | `String` | - | `getApvNo()` |
| `ismtMnthNum` | `String` | - | `getIsmtMnthNum()` |
| `prepCrdKndCd` | `String` | - | `getPrepCrdKndCd()` |
| `prepCrdNo` | `String` | - | `getPrepCrdNo()` |
| `retFee` | `String` | - | `getRetFee()` |
| `saleFlrVal` | `String` | - | `getSaleFlrVal()` |
| `stlAmt` | `String` | - | `getStlAmt()` |
| `stlBankCd` | `String` | - | `getStlBankCd()` |
| `stlCrdNo` | `String` | - | `getStlCrdNo()` |
| `stlMnsCd` | `String` | - | `getStlMnsCd()` |
| `stlNo` | `String` | - | `getStlNo()` |
| `stlSqno` | `String` | - | `getStlSqno()` |

### `response.seatMovie.RsvInquiryResponse`

- 소스: `com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java:8`
- 상속/구현: extends `BaseResponse`, implements `Serializable`
- 중첩/관련 클래스: `RcmdGdList`(8 fields), `TrainInfo`(64 fields), `TrainInfos`(2 fields)
- `SeatMovieService.getRsvInquiry()` POST `/classes/com.korail.mobile.seatMovie.ScheduleView`; service `com/korail/talk/network/dao/seatMovie/SeatMovieService.java`; caller `com/korail/talk/network/dao/seatMovie/TrainInquiryDao.java`
- `SeatMovieService.getRsvLimousineInquiry()` POST `/classes/com.korail.mobile.seatMovie.LimousineScheduleView`; service `com/korail/talk/network/dao/seatMovie/SeatMovieService.java`; caller `com/korail/talk/network/dao/seatMovie/LimousineTrainInquiryDao.java`
- `SeatMovieService.getRsvProductInquiry()` POST `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`; service `com/korail/talk/network/dao/seatMovie/SeatMovieService.java`; caller `com/korail/talk/network/dao/seatMovie/ProductTrainInquiryDao.java`

직접 필드:

| 필드 | 타입 | JSON annotation | getter/setter |
|---|---|---|---|
| `h_ectb_trn_no_next` | `String` | - | `getH_ectb_trn_no_next()` |
| `h_gd_no` | `String` | - | `getH_gd_no()` |
| `h_next_pg_flg` | `String` | - | `getH_next_pg_flg()` |
| `h_notice_msg` | `String` | - | `getH_notice_msg()` |
| `h_prcd_trn_no_next` | `String` | - | `getH_prcd_trn_no_next()` |
| `h_qry_st_no_next` | `String` | - | `getH_qry_st_no_next()` |
| `h_rslt_cnt` | `String` | - | `getH_rslt_cnt()` |
| `h_trn_no_next` | `String` | - | `getH_trn_no_next()` |
| `trn_infos` | `TrainInfos` | - | `getTrn_infos()` |

중첩 payload:

- `RcmdGdList` (implements `Serializable`; source line 18): `dcntAmt`:`String` {getDcntAmt()}; `dcntSurRt`:`String` {getDcntSurRt()}; `famtPctDvCd`:`String` {getFamtPctDvCd()}; `gdNm`:`String` {getGdNm()}; `gdNo`:`String` {getGdNo()}; `rcvdFare`:`String` {getRcvdFare()}; `rcvdPrc`:`String` {getRcvdPrc()}; `rcvdPrc2`:`String` {getRcvdPrc2()}
- `TrainInfo` (implements `Serializable`; source line 64): `dturViaPopp`:`String` {getdturViaPopp(),setdturViaPopp()}; `elevDmgCtrl`:`String` {getElevDmgCtrl()}; `h_arv_dt`:`String` {getH_arv_dt()}; `h_arv_rs_stn_cd`:`String` {getH_arv_rs_stn_cd(),setH_arv_rs_stn_cd()}; `h_arv_rs_stn_nm`:`String` {getH_arv_rs_stn_nm(),setH_arv_rs_stn_nm()}; `h_arv_stn_cons_ordr`:`String` {getH_arv_stn_cons_ordr()}; `h_arv_stn_run_ordr`:`String` {getH_arv_stn_run_ordr(),setH_arv_stn_run_ordr()}; `h_arv_tm`:`String` {getH_arv_tm()}; `h_car_tp_nm`:`String` {getH_car_tp_nm()}; `h_chg_trn_dv_cd`:`String` {getH_chg_trn_dv_cd()}; `h_chg_trn_seq`:`String` {getH_chg_trn_seq()}; `h_cnec_trfc_nd_hm`:`String` {getH_cnec_trfc_nd_hm()}; `h_cnec_trfc_psb_flg`:`String` {getH_cnec_trfc_psb_flg()}; `h_cnec_trfc_rcvd_prc`:`String` {getH_cnec_trfc_rcvd_prc()}; `h_dlay_sale_flg`:`String` {getH_dlay_sale_flg()}; `h_dpt_dt`:`String` {getH_dpt_dt(),setH_dpt_dt()}; `h_dpt_rs_stn_cd`:`String` {getH_dpt_rs_stn_cd(),setH_dpt_rs_stn_cd()}; `h_dpt_rs_stn_nm`:`String` {getH_dpt_rs_stn_nm(),setH_dpt_rs_stn_nm()}; `h_dpt_stn_cons_ordr`:`String` {getH_dpt_stn_cons_ordr()}; `h_dpt_stn_run_ordr`:`String` {getH_dpt_stn_run_ordr(),setH_dpt_stn_run_ordr()}; `h_dpt_tm`:`String` {getH_dpt_tm()}; `h_dtour_flg`:`String` {getH_dtour_flg()}; `h_dtour_txt`:`String` {getDtourTxt()}; `h_expct_dlay_hr`:`String` {getH_expct_dlay_hr()}; `h_expn_dpt_dlay_tnum`:`String` {getH_expn_dpt_dlay_tnum()}; `h_free_rsv_cd`:`String` {getH_free_rsv_cd()}; `h_free_sracar_cnt`:`String` {getH_free_sracar_cnt()}; `h_gen_psrm_cl_nm`:`String` {getH_gen_psrm_cl_nm()}; `h_gen_rsv_cd`:`String` {getH_gen_rsv_cd()}; `h_gen_rsv_cd2`:`String` {getH_gen_rsv_cd2()}; `h_info_txt`:`String` {getH_info_txt()}; `h_jrny_rsv_cd`:`String` {getH_jrny_rsv_cd()}; `h_jrny_rsv_nm`:`String` {getH_jrny_rsv_nm()}; `h_nonstop_msg`:`String` {getH_nonstop_msg()}; `h_nonstop_msg_txt`:`String` {getH_nonstop_msg_txt()}; `h_popup_msg`:`String` {getH_popup_msg()}; `h_rcvd_amt`:`String` {getH_rcvd_amt()}; `h_rcvd_fare`:`String` {getH_rcvd_fare()}; `h_rcvd_prc2`:`String`; `h_rd_seat_map_flg`:`String` {getH_rd_seat_map_flg()}; `h_rsv_psb_nm`:`String` {getH_rsv_psb_nm()}; `h_run_dt`:`String` {getH_run_dt(),setH_run_dt()}; `h_run_tm`:`String` {getH_run_tm()}; `h_seat_att_cd`:`String` {getH_seat_att_cd(),setH_seat_att_cd()}; `h_smns_trn_flg`:`String` {getH_smns_trn_flg(),setH_smns_trn_flg()}; `h_spe_disc_rt`:`String` {getH_spe_disc_rt()}; `h_spe_psrm_cl_nm`:`String` {getH_spe_psrm_cl_nm()}; `h_spe_rsv_cd`:`String` {getH_spe_rsv_cd()}; `h_spe_rsv_cd2`:`String` {getH_spe_rsv_cd2()}; `h_spe_rsv_psb_nm`:`String` {getH_spe_rsv_psb_nm()}; `h_station_popup_msg`:`String` {getH_station_popup_msg()}; `h_stnd_rsv_cd`:`String` {getH_stnd_rsv_cd()}; `h_train_disc_gen_rt`:`String` {getH_train_disc_gen_rt()}; `h_train_disc_origin_rt`:`String` {getH_train_disc_origin_rt()}; `h_trn_clsf_cd`:`String` {getH_trn_clsf_cd(),setH_trn_clsf_cd()}; `h_trn_clsf_nm`:`String` {getH_trn_clsf_nm(),setH_trn_clsf_nm()}; `h_trn_gp_cd`:`String` {getH_trn_gp_cd(),setH_trn_gp_cd()}; `h_trn_no`:`String` {getH_trn_no(),setH_trn_no()}; `h_use_tim_care_atcl_cont`:`String` {getH_use_tim_care_atcl_cont()}; `h_wait_rsv_flg`:`String` {getH_wait_rsv_flg()}; `h_yms_apl_flg`:`String` {getH_yms_apl_flg()}; `rcmdGdList`:`List<RcmdGdList>` {getRcmdGdList()}; `totPsgCnt`:`int` {getTotPsgCnt(),setTotPsgCnt()}; `txtGdNo`:`String` {getTxtGdNo(),setTxtGdNo()}
- `TrainInfos` (없음; source line 454): `h_merge_rsv_psb_flg`:`String` {getH_merge_rsv_psb_flg()}; `trn_info`:`List<TrainInfo>` {getTrn_info()}

## Endpoint 미확인 응답 클래스

- `data.addService.ExtraProductInfo`: `com/korail/talk/network/data/addService/ExtraProductInfo.java:10`
- `response.delay.RefundResponse`: `com/korail/talk/network/response/delay/RefundResponse.java:9`

## 20-agent follow-up audit 보강

다음 response class는 endpoint mapping이 확인되었으나 본 보고서의 최초 생성본에 누락되었으므로 별도 보강 항목으로 둔다.

### `CompensateRefundListResponse`

- 소스: `analysis/jadx/sources/com/korail/talk/network/dao/compensate/CompensateRefundListDao.java:45`
- API contract: `docs/deep-dive/api-contracts.md`의 `/classes/com.korail.mobile.compensate.ticketList.do`
- 용도: 운행중지 보상 목록 조회 response. `CompensateService.executeCompensateRefundList()`의 return model이다.

### `DelayRefundListResponse`

- 소스: `analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayRefundListDao.java:45`
- API contract: `docs/deep-dive/api-contracts.md`의 `/classes/com.korail.mobile.delay.ticketList.do`
- 용도: 지연 보상 목록 조회 response. `DelayService.executeDelayRefundList()`의 return model이다.

### `DptnBankResponse`

- 소스: `analysis/jadx/sources/com/korail/talk/network/dao/delay/DptnBankDao.java:29`
- API contract: `docs/deep-dive/api-contracts.md`의 `/classes/com.korail.mobile.dlay.dptnBank.do`
- 용도: 지연보상 입금은행 목록 response. `dptnBank[]` 하위에 은행 코드/명칭 model을 가진다.

### `SeatAssignReservationResponse`

- 소스: `analysis/jadx/sources/com/korail/talk/network/dao/reservation/SeatAssignReservationDao.java:131`
- API contract: `docs/deep-dive/api-contracts.md`의 `/classes/com.korail.mobile.reservation.seatAssign.do`
- 용도: seat assignment reservation response. `ReservationResponse` 계열과 함께 신형 `RJrny`/`RSrcar`/`RSeat`/`RPsg`/`ROrtg` FieldMap flow에서 사용된다.

추가 정정:

- 기존 `data.addService.ExtraProductInfo`의 `arrayList` 행은 model field가 아니라 `getAddSrvList()` 내부 local variable이므로 제거했다.
- 일부 legacy generated source line reference는 inner class 선언부 기준으로 한 줄 낮을 수 있다. 고위험 endpoint 검증 시에는 `analysis/jadx/sources` 원문과 `docs/deep-dive/network-model-fields.md`를 함께 확인한다.
- `response.delay.RefundResponse`는 missing concrete return model들의 superclass 성격이다. `api-contracts.md`의 duplicate `RefundResponse` 표기는 `returnTicket`의 `RefundDao.RefundResponse`와 delay refund superclass가 섞일 수 있으므로 사용처별 DAO 소스를 우선한다.
- `ReservationResponse` endpoint mapping은 2개 path에 4개 overload가 있다. `CertificationService.java:48,52,56,60`을 함께 봐야 한다.
- `MaasMenuListResponse` source에는 package-private URL field가 있어 TSV/API catalog에서 빠질 수 있다.

## 검증 메모

- `rg "class .*extends BaseResponse" analysis/jadx/sources/com/korail/talk/network` 결과와 parser 수량을 대조했다.
- `rg "@c\(" analysis/jadx/sources/com/korail/talk/network`로 JSON-name annotation 사용 위치를 확인했다.
- Retrofit endpoint mapping은 `*Service.java`의 `@GET`/`@POST`와 반환형을 기준으로 생성했다.
- 정적 분석 한계: JADX decompile artifact이므로 일부 이름은 원본과 다를 수 있고, 런타임 reflection/dynamic parsing으로만 연결되는 endpoint는 미확인으로 남긴다.
