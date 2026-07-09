# KORAIL APK API Endpoint Inventory

Source APK: `korail.apk` (`com.korail.talk` 6.5.0, API version `250601003`).

Base runtime host for this release: `https://smart.letskorail.com` (`CONNECT_SERVER="3"` -> `REAL`). All paths below are relative to that host unless stated otherwise. Common form/query fields are usually `Device=AD`, `Version=250601003`, and `Key=korail1234567890`.

Total Retrofit method entries found: **165** across **35** annotated interfaces. Distinct HTTP+path pairs: **159**.

| Interface | Entries | Methods | Source |
|---|---:|---|---|
| `AddService` | 5 | POST:5 | `com/korail/talk/network/dao/addService/AddService.java` |
| `BusReservationService` | 4 | POST:4 | `com/korail/talk/network/dao/certification/BusReservationService.java` |
| `CacheService` | 3 | GET:3 | `com/korail/talk/network/dao/cache/CacheService.java` |
| `CalendarService` | 1 | GET:1 | `com/korail/talk/network/dao/schedule/CalendarService.java` |
| `CartService` | 3 | POST:3 | `com/korail/talk/network/dao/cart/CartService.java` |
| `CashReceipt` | 1 | POST:1 | `com/korail/talk/network/dao/cashReceipt/CashReceipt.java` |
| `CertificationService` | 12 | GET:6, POST:6 | `com/korail/talk/network/dao/certification/CertificationService.java` |
| `CommonService` | 11 | GET:3, POST:8 | `com/korail/talk/network/dao/common/CommonService.java` |
| `CompensateService` | 3 | POST:3 | `com/korail/talk/network/dao/compensate/CompensateService.java` |
| `CustService` | 1 | POST:1 | `com/korail/talk/network/dao/cust/CustService.java` |
| `DelayService` | 9 | POST:9 | `com/korail/talk/network/dao/delay/DelayService.java` |
| `GiftInfoService` | 1 | POST:1 | `com/korail/talk/network/dao/giftInfo/GiftInfoService.java` |
| `GifticketService` | 4 | POST:4 | `com/korail/talk/network/dao/gifticket/GifticketService.java` |
| `IndependentService` | 1 | POST:1 | `com/korail/talk/network/dao/independent/IndependentService.java` |
| `LoginService` | 7 | GET:1, POST:6 | `com/korail/talk/network/dao/login/LoginService.java` |
| `MileageService` | 3 | POST:3 | `com/korail/talk/network/dao/mileage/MileageService.java` |
| `MyTicketService` | 3 | GET:2, POST:1 | `com/korail/talk/network/dao/myTicket/MyTicketService.java` |
| `NFilterService` | 1 | POST:1 | `com/korail/talk/network/dao/nFilter/NFilterService.java` |
| `PassCardService` | 4 | POST:4 | `com/korail/talk/network/dao/passCard/PassCardService.java` |
| `PassService` | 8 | POST:8 | `com/korail/talk/network/dao/pass/PassService.java` |
| `PayService` | 12 | POST:12 | `com/korail/talk/network/dao/pay/PayService.java` |
| `PaymentService` | 1 | POST:1 | `com/korail/talk/network/dao/payment/PaymentService.java` |
| `ProductService` | 4 | GET:4 | `com/korail/talk/network/dao/product/ProductService.java` |
| `PushService` | 4 | GET:4 | `com/korail/talk/network/dao/push/PushService.java` |
| `RailPlusService` | 1 | GET:1 | `com/korail/talk/network/dao/railplus/RailPlusService.java` |
| `ReceiptService` | 1 | POST:1 | `com/korail/talk/network/dao/receipt/ReceiptService.java` |
| `RefundService` | 5 | POST:5 | `com/korail/talk/network/dao/refund/RefundService.java` |
| `ResearchService` | 11 | GET:3, POST:8 | `com/korail/talk/network/dao/research/ResearchService.java` |
| `ReservationCancelService` | 3 | POST:3 | `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java` |
| `ReservationService` | 4 | GET:1, POST:3 | `com/korail/talk/network/dao/reservation/ReservationService.java` |
| `ReservationWaitService` | 1 | POST:1 | `com/korail/talk/network/dao/reservationWait/ReservationWaitService.java` |
| `SeatMovieService` | 3 | POST:3 | `com/korail/talk/network/dao/seatMovie/SeatMovieService.java` |
| `TicketService` | 19 | POST:19 | `com/korail/talk/network/dao/ticket/TicketService.java` |
| `TrainsInfoService` | 6 | POST:6 | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java` |
| `XPointService` | 5 | POST:5 | `com/korail/talk/network/dao/xPoint/XPointService.java` |

## AddService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.addService.reserve.do` | `additionalService` | `AdditionalServiceDao.AdditionalServiceResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:jrnySqno, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:jobDvCd, Field:addSrvId, Field:reqQnty, Field:helpSrvTgtCnt, Field:rcpSqno, Field:cncTgtCnt, Field:addSrvReqNo | `com/korail/talk/network/dao/addService/AddService.java:16` |
| POST | `/classes/com.korail.mobile.addService.buyConfirm.do` | `dealCarBuy` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:addSrvCnt, Field:addSrvReqNo | `com/korail/talk/network/dao/addService/AddService.java:20` |
| POST | `/classes/com.korail.mobile.addService.reserveList.do` | `getExtraProductList` | `ExtraProductListDao.ExtraProductListResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo | `com/korail/talk/network/dao/addService/AddService.java:24` |
| POST | `/classes/com.korail.mobile.addSrv.helpSrvCust.do` | `helpSrvCust` | `HelpSrvCustDao.HelpSrvCustResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:reqCnt, Field:reqAddSrvDvCd, Field:reqAddRcpSrvCd, Field:reqCustNm, Field:reqCntcChnCont, Field:qryDvCd, Field:addSrvDvCd, Field:rcpSqno | `com/korail/talk/network/dao/addService/AddService.java:28` |
| POST | `/classes/com.korail.mobile.addSrv.helpSrvTk.do` | `helpSrvTk` | `HelpSrvTkDao.HelpSrvTkDaoResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno | `com/korail/talk/network/dao/addService/AddService.java:32` |

## BusReservationService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `reservationCancelCheck` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:txtPnrNo, Field:txtJrnySqno, Field:txtJrnyCnt, Field:hidRsvChgNo | `com/korail/talk/network/dao/certification/BusReservationService.java:19` |
| POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | `reservationChange` | `ReservationChangeDao.ReservationChangeResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:chgTno, Field:totPrnb, Field:stndFlg, Field:evntWctFlg, Field:wctHndgCncDvCd, Field:lrgCrgFlg, Field:psgCnt, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/certification/BusReservationService.java:23` |
| POST | `/classes/com.korail.mobile.lmu.scdlQry.do` | `reservationList` | `BusReservationListDao.BusInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:dptDt, Field:dptRsStnCd, Field:arvRsStnCd, Field:tmGpCd, Field:psrmClCd, Field:dptTm, Field:trnNo, Field:seatAttCd, Field:rsvSaleDvCd | `com/korail/talk/network/dao/certification/BusReservationService.java:27` |
| POST | `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do` | `reservationSeatList` | `BusReservationSeatListDao.SeatListResponse` | Field:Device, Field:Version, Field:Key, Field:trnClsfCd, Field:trnGpCd, Field:runDt, Field:trnNo, Field:srcarNo, Field:psrmClCd, Field:dptRsStnCd, Field:arvRsStnCd, Field:seatAttCd, Field:dptStnRunOrdr, Field:arvStnRunOrdr, Field:totPsgCnt, Field:gdNo, Field:isArrow | `com/korail/talk/network/dao/certification/BusReservationService.java:31` |

## CacheService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/file/CACHE/MobileService.cache` | `checkService` | `BaseResponse` | Query:timeStamp | `com/korail/talk/network/dao/cache/CacheService.java:11` |
| GET | `/file/CACHE/prdMobilePlusMain.cache` | `getAppData` | `AppDataDao.AppDataResponse` | Query:timeStamp | `com/korail/talk/network/dao/cache/CacheService.java:14` |
| GET | `/file/CACHE/prdMobilePlusNotice.cache` | `getNotice` | `NoticeDao.NoticeResponse` | Query:timeStamp | `com/korail/talk/network/dao/cache/CacheService.java:17` |

## CalendarService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.schedule.runDt` | `getTrainCalendar` | `TrainCalendarDao.TrainCalendarResponse` |  | `com/korail/talk/network/dao/schedule/CalendarService.java:8` |

## CartService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.cart.addCartList` | `addCart` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:hidPnrNo | `com/korail/talk/network/dao/cart/CartService.java:11` |
| POST | `/classes/com.korail.mobile.cart.showCartList` | `getCartList` | `CartListDao.CartListResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:addSrvReqNo | `com/korail/talk/network/dao/cart/CartService.java:15` |
| POST | `/classes/com.korail.mobile.maas.rsvStt.do` | `verifyMaasStatus` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:addSrvDvCd, Field:addSrvReqNo, Field:coptEntRsvNo, Field:lumpStlTgtNo | `com/korail/talk/network/dao/cart/CartService.java:19` |

## CashReceipt

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.cashReceipt.issue.do` | `issue` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:cashRcetTxnDvCd, Field:vltIsuFlg, Field:cashRcetAthnMtdCd, Field:athnDmnRcgnNo, Field:apvCnt, FieldMap | `com/korail/talk/network/dao/cashReceipt/CashReceipt.java:12` |

## CertificationService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.certification.ReservationList` | `applyDisabilityCertification` | `BaseResponse` | Query:Device, Query:Version, Query:Key, Query:hidPnrNo, Query:txtPsgDisc0019Cnt, QueryMap, QueryMap, QueryMap, QueryMap, QueryMap, QueryMap | `com/korail/talk/network/dao/certification/CertificationService.java:22` |
| GET | `/classes/com.korail.mobile.certification.assemblyCert` | `certCongressperson` | `CongresspersonCertDao.CongresspersonCertResponse` | Query:Device, Query:Version, Query:Key, Query:freeDiscCertNo, Query:certNo, Query:abrdDt | `com/korail/talk/network/dao/certification/CertificationService.java:25` |
| POST | `/classes/com.korail.mobile.certification.MeritCert` | `certMerit` | `MeritCertDao.MeritCertResponse` | Field:Device, Field:Version, Field:Key, Field:txtFreeDiscCertNo, Field:txtAcptPwd, Field:txtJuminNo7, Field:txtAbrdDt | `com/korail/talk/network/dao/certification/CertificationService.java:28` |
| GET | `/classes/com.korail.mobile.certification.disabled.do` | `disabledCertification` | `DisabledCertificationDao.DisabledCertificationResponse` | Query:Device, Query:Version, Query:Key, Query:regNum, Query:hdcpGrade | `com/korail/talk/network/dao/certification/CertificationService.java:32` |
| POST | `/classes/com.korail.mobile.certification.PriceReCalculation` | `getDiscountPrice` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, Field:hidPnrNo, Field:txtJobId, Field:hiduserYn, Field:hidCustNo, Field:txtPsgGridcnt, Field:psg_tp_dv_cd, Field:hidDcntKndCd, Field:dcnt_knd_cd1, Field:hidDscpNo, Field:psrm_cl_cd, Field:hidFmlyNo | `com/korail/talk/network/dao/certification/CertificationService.java:35` |
| GET | `/classes/com.korail.mobile.pbep.toknCre.do` | `govermentCertification1` | `GovernmentCertificationStep1Dao.GovernmentCertificationResponse` | Query:Device, Query:Version | `com/korail/talk/network/dao/certification/CertificationService.java:39` |
| GET | `/classes/com.korail.mobile.pbep.sttChck.do` | `govermentCertification2` | `GovernmentCertificationStep2Dao.GovernmentCertificationStep2Response` | Query:Device, Query:Version, Query:csrfToken | `com/korail/talk/network/dao/certification/CertificationService.java:42` |
| GET | `/classes/com.korail.mobile.certification.ReservationList` | `inquiryTicketRsv` | `ReservationResponse` | Query:Device, Query:Version, Query:Key, Query:hidPnrNo | `com/korail/talk/network/dao/certification/CertificationService.java:45` |
| POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | `reservation` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:txtMenuId, Field:txtJobId, Field:txtGdNo, Field:hidFreeFlg, Field:txtStndFlg, Field:txtCustNm, Field:txtCpNo, Field:txtCustPw, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/certification/CertificationService.java:48` |
| POST | `/classes/com.korail.mobile.certification.TicketReservation` | `reservation` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:txtMenuId, Field:txtJobId, Field:txtGdNo, Field:hidFreeFlg, Field:txtStndFlg, Field:pbepInfo, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/certification/CertificationService.java:52` |
| POST | `/classes/com.korail.mobile.nonMember.NonMemTicket` | `reservation` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, Field:txtCustNm, Field:txtCpNo, Field:txtCustPw, FieldMap | `com/korail/talk/network/dao/certification/CertificationService.java:56` |
| POST | `/classes/com.korail.mobile.certification.TicketReservation` | `reservation` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, FieldMap | `com/korail/talk/network/dao/certification/CertificationService.java:60` |

## CommonService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.qr.bchTripSv.do` | `authQRLocation` | `authQRLocationDao.QRLocationResponse` | Field:Device, Field:Version, Field:qrcode, Field:latitude, Field:longitude | `com/korail/talk/network/dao/common/CommonService.java:23` |
| GET | `/ebizcross/getUUID.do` | `ckValue` | `CookieDao.RsvWaitResponse` |  | `com/korail/talk/network/dao/common/CommonService.java:27` |
| POST | `/classes/com.korail.mobile.common.code.do` | `getCommonCode` | `CommonCodeDao.CommonCodeResponse` | Field:Device, Field:Version, Field:Key, Field:code, Field:deviceWidth, Field:deviceHeight, Field:departDate, Field:arrivalDate, Field:holidayYn, Field:OSVersion | `com/korail/talk/network/dao/common/CommonService.java:30` |
| POST | `/classes/com.korail.mobile.common.decrypt.do` | `getDecrypt` | `DecryptDao.DecryptResponse` | Field:Device, Field:Version, Field:Key, Field:type, Field:values | `com/korail/talk/network/dao/common/CommonService.java:34` |
| POST | `/classes/com.korail.mobile.common.encrypt.do` | `getEncrypt` | `EncryptDao.EncryptResponse` | Field:Device, Field:Version, Field:Key, Field:type, Field:values | `com/korail/talk/network/dao/common/CommonService.java:38` |
| POST | `/classes/com.korail.mobile.common.encrypt.do` | `getKBPayEncrypt` | `KBPayEncryptDao.KBpayEncryptResponse` | Field:Device, Field:Version, Field:Key, Field:type, Field:values | `com/korail/talk/network/dao/common/CommonService.java:42` |
| POST | `/classes/com.korail.mobile.copt.gdMenuLt.do` | `getMaasMenuList` | `MaasMenuListDao.MaasMenuListResponse` | Field:Device, Field:Version, Field:pnrNo, Field:tkRetNo, Field:addSrvReqNo | `com/korail/talk/network/dao/common/CommonService.java:46` |
| POST | `/ebizmaas/EbizMaasStationList.do` | `getMaasStationList` | `StationDataDao.StationDataResponse` | Field:addSrvDvCd | `com/korail/talk/network/dao/common/CommonService.java:50` |
| GET | `/classes/com.korail.mobile.common.stationdata` | `getStationData` | `StationDataDao.StationDataResponse` |  | `com/korail/talk/network/dao/common/CommonService.java:54` |
| GET | `/classes/com.korail.mobile.common.stationinfo` | `getStationInfo` | `StationInfoDao.StationInfoResponse` | Query:Device | `com/korail/talk/network/dao/common/CommonService.java:57` |
| POST | `/classes/com.korail.mobile.shinhan.Encrypt.do` | `seedEncrypt` | `SeedEncryptDao.SeedEncryptResponse` | Field:Device, Field:Version, Field:Key, Field:value | `com/korail/talk/network/dao/common/CommonService.java:60` |

## CompensateService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.compensate.ticketReturn.do` | `executeCompensateRefund` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, Field:trnStpRsStnCd, Field:jrnyStpTkFlg, Field:ogTkSaleWctNo, Field:ogTkSaleDd, Field:ogTkSaleSqNo, Field:ogTkRetPwd | `com/korail/talk/network/dao/compensate/CompensateService.java:12` |
| POST | `/classes/com.korail.mobile.compensate.ticketDetail.do` | `executeCompensateRefundDetail` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, Field:trnStpRsStnCd, Field:jrnyStpTkFlg, Field:ogTkSaleWctNo, Field:ogTkSaleDd, Field:ogTkSaleSqNo, Field:ogTkRetPwd | `com/korail/talk/network/dao/compensate/CompensateService.java:16` |
| POST | `/classes/com.korail.mobile.compensate.ticketList.do` | `executeCompensateRefundList` | `CompensateRefundListDao.CompensateRefundListResponse` | Field:Device, Field:Version, Field:Key, Field:nowPgNo, Field:dptDtFrom, Field:dptDtTo | `com/korail/talk/network/dao/compensate/CompensateService.java:20` |

## CustService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.cust.mchdDcntTgt.do` | `mchdDcntTgt` | `MchdDcntTgtDao.MchdDcntTgtResponse` | Field:Device, Field:Version, Field:Key, Field:dptDt | `com/korail/talk/network/dao/cust/CustService.java:11` |

## DelayService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.dlay.athnIsu.do` | `athnIsu` | `DelayCertificateDao.DelayCertificateResponse` | Field:Device, Field:Version, Field:Key, Field:ogtkSaleWctNo, Field:ogtkSaleDd, Field:ogtkSaleSqno, Field:ogtkRetPwd, Field:runDt, Field:trnNo | `com/korail/talk/network/dao/delay/DelayService.java:18` |
| POST | `/classes/com.korail.mobile.dlay.cashRfn.do` | `cashRfn` | `CashRfnDao.CashRfnResponse` | Field:Device, Field:Version, Field:Key, Field:dmnPrsDvCd, Field:saleWctNo, Field:saleDd, Field:saleSqno, Field:tkRetPwd, Field:dptnBankCd, Field:dptnAcntNo, Field:custNm, Field:custTeln, Field:rmk1Cont | `com/korail/talk/network/dao/delay/DelayService.java:22` |
| POST | `/classes/com.korail.mobile.dlay.pymtRcet.do` | `dealyReturnReceipt` | `DelayReturnReceiptDao.DelayReturnReceiptResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDd, Field:saleSqno, Field:tkRetPwd | `com/korail/talk/network/dao/delay/DelayService.java:26` |
| POST | `/classes/com.korail.mobile.dlay.dptnBank.do` | `dptnBank` | `DptnBankDao.DptnBankResponse` | Field:Device, Field:Version, Field:Key | `com/korail/talk/network/dao/delay/DelayService.java:30` |
| POST | `/classes/com.korail.mobile.delay.acptPrs.do` | `executeDelayPNRAccept` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:jobDvCd, Field:pnrCnt, Field:pnrNo, Field:ogtkWctNo | `com/korail/talk/network/dao/delay/DelayService.java:34` |
| POST | `/classes/com.korail.mobile.delay.pnrQry.do` | `executeDelayPNRQuery` | `DelayPNRQueryDao.DelayPNRQueryResponse` | Field:Device, Field:Version, Field:Key, Field:jobDvCd, Field:pnrCnt, Field:pnrNo, Field:ogtkWctNo | `com/korail/talk/network/dao/delay/DelayService.java:38` |
| POST | `/classes/com.korail.mobile.delay.ticketReturn.do` | `executeDelayRefund` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:dlayFarePymtMtdCd, Field:tkCnt, Field:ogTkSaleWctNo, Field:ogTkSaleDd, Field:ogTkSaleSqNo, Field:ogTkRetPwd | `com/korail/talk/network/dao/delay/DelayService.java:42` |
| POST | `/classes/com.korail.mobile.delay.ticketDetail.do` | `executeDelayRefundDetail` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, Field:ogTkSaleWctNo, Field:ogTkSaleDd, Field:ogTkSaleSqNo, Field:ogTkRetPwd | `com/korail/talk/network/dao/delay/DelayService.java:46` |
| POST | `/classes/com.korail.mobile.delay.ticketList.do` | `executeDelayRefundList` | `DelayRefundListDao.DelayRefundListResponse` | Field:Device, Field:Version, Field:Key, Field:nowPgNo, Field:dptDtFrom, Field:dptDtTo | `com/korail/talk/network/dao/delay/DelayService.java:50` |

## GiftInfoService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.giftInfo.GiftSend` | `presentTicket` | `TicketPresentDao.TicketPresentResponse` | Field:Device, Field:Version, Field:Key, Field:hidAcepPsNm, Field:hidAcepPsTeln, Field:hidPbpAcepPsMbFlg, Field:hidPbpAcepPsCustMgNo, Field:hidPnrNo, Field:hidTotNewStlAmt, Field:hidRsvChgNo, Field:hidInfoInpDvCd, Field:hidSaleCnt, Field:hidAcepPwd, FieldMap | `com/korail/talk/network/dao/giftInfo/GiftInfoService.java:12` |

## GifticketService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.gift.gdRsv.do` | `bookingGifticket` | `GifticketBookingDao.GifticketBookingResponse` | Field:Device, Field:Version, Field:Key, Field:itmCnt, Field:mrkAmt_1, Field:prnbCnt, Field:mbCrdNo_1, Field:gdUtlPsNm_1 | `com/korail/talk/network/dao/gifticket/GifticketService.java:13` |
| POST | `/classes/com.korail.mobile.gift.gdLst.do` | `getGifticketList` | `GifticketListDao.GifticketListResponse` | Field:Device, Field:Version, Field:Key, Field:qryDvCd, Field:qryVal, Field:abrdDtFrom, Field:abrdDtTo, Field:usePsbFlg, Field:qryNumNext, Field:fllwQryFlg, Field:trnOprBzDvCd | `com/korail/talk/network/dao/gifticket/GifticketService.java:17` |
| POST | `/classes/com.korail.mobile.gift.gdUseSpec.do` | `historyGifticket` | `GifticketHistoryDao.GifticketHistoryResponse` | Field:Device, Field:Version, Field:Key, Field:tkId | `com/korail/talk/network/dao/gifticket/GifticketService.java:21` |
| POST | `/classes/com.korail.mobile.gift.gdRet.do` | `returnGifticket` | `GifticketReturnDao.GifticketReturnResponse` | Field:Device, Field:Version, Field:Key, Field:tkId | `com/korail/talk/network/dao/gifticket/GifticketService.java:25` |

## IndependentService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.login.poppCfmRec.do` | `registerUserInfo` | `BaseResponse` | Field:Device, Field:Version, Field:Key, FieldMap | `com/korail/talk/network/dao/independent/IndependentService.java:12` |

## LoginService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.login.userCheck` | `certMember` | `MemberCertDao.MemberCertResponse` | Field:Device, Field:Version, Field:Key, Field:txtAcptPsNm, Field:acept, Field:txtCpNo, Field:memNum, Field:txtEmailNo | `com/korail/talk/network/dao/login/LoginService.java:13` |
| POST | `/classes/com.korail.mobile.login.Login` | `login` | `LoginDao.LoginResponse` | Field:Device, Field:Version, Field:Key, Field:txtMemberNo, Field:txtPwd, Field:txtInputFlg, Field:checkValidPw, Field:custId, Field:etrPath, Field:idx | `com/korail/talk/network/dao/login/LoginService.java:17` |
| POST | `/classes/com.korail.mobile.login.loginAthnReg.do` | `loginAthnReg` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:lognTpCd, Field:custId | `com/korail/talk/network/dao/login/LoginService.java:21` |
| POST | `/classes/com.korail.mobile.login.loginAthnRmv.do` | `loginAthnRmv` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:srvQryDvVal, Field:lognTpCd | `com/korail/talk/network/dao/login/LoginService.java:25` |
| GET | `/classes/com.korail.mobile.login.Logout` | `logout` | `BaseResponse` |  | `com/korail/talk/network/dao/login/LoginService.java:29` |
| POST | `/classes/com.korail.mobile.login.joinCfm.do` | `memberCheck` | `BaseResponse` | Field:Device, Field:Version, Field:hmpgPwd, Field:custNm | `com/korail/talk/network/dao/login/LoginService.java:32` |
| POST | `/classes/com.korail.mobile.login.mbSced.do` | `memberDrop` | `BaseResponse` | Field:Device, Field:Version | `com/korail/talk/network/dao/login/LoginService.java:36` |

## MileageService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.mileage.acpnMlgNoti.do` | `acpnMlgNoti` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:retPwd, Field:rcvPsHndyTeln | `com/korail/talk/network/dao/mileage/MileageService.java:11` |
| POST | `/classes/com.korail.mobile.mileage.acpnMlgSave.do` | `acpnMlgSave` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:rsvMbCrdNo, Field:custNm, Field:mlgAcmMbCrdNo, Field:saleWctNo, Field:saleDd, Field:saleSqno, Field:tkRetPwd | `com/korail/talk/network/dao/mileage/MileageService.java:15` |
| POST | `/classes/com.korail.mobile.mileage.acpnMlgSpec.do` | `acpnMlgSpec` | `AcpnMlgSpecDao.AcpnMlgSpecResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo | `com/korail/talk/network/dao/mileage/MileageService.java:19` |

## MyTicketService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.myTicket.MyTicketList` | `getTicketList` | `TicketListDao.TicketListResponse` | Field:Device, Field:Version, Field:Key, Field:txtDeviceId, Field:txtIndex, Field:h_page_no, Field:h_abrd_dt_from, Field:h_abrd_dt_to, Field:hiduserYn, Field:hidName, Field:hidTeleNo, Field:hidPwd, Field:tsRsStnCd | `com/korail/talk/network/dao/myTicket/MyTicketService.java:16` |
| GET | `/classes/com.korail.mobile.myTicket.procUpgradeSeat` | `procUpgrade` | `BaseResponse` | Query:Device, Query:Version, Query:Key, Query:totTxnAmt, Query:totCncRetAmt, Query:totCncRetFee, Query:feeProyStlSqno, Query:lumpStlTgtNo, Query:mnsGridcnt, Query:stlMnsSqno, Query:stlMnsCd, Query:mnsStlAmt, Query:crdInpWayCd, Query:ismtMnthNum, Query:pontDvCd, Query:pontInpDvCd, Query:prepCrdTxnBfAmt, Query:prepCrdTxnAftAmt | `com/korail/talk/network/dao/myTicket/MyTicketService.java:20` |
| GET | `/classes/com.korail.mobile.myTicket.reqUpgradeSeat` | `requestUpgradeSeat` | `SpecialRoomUpgradeDao.SpecialRoomUpgradeResponse` | Query:Device, Query:Version, Query:Key, Query:ogtkSaleDd, Query:ogtkSaleWctNo, Query:ogtkSaleSqno, Query:ogtkRetPwd, Query:jrnyTpCd, Query:jrnySqno, Query:dptDt, Query:dptStnConsOrdr, Query:dptStnRunOrdr, Query:dptRsStnCd, Query:dptTm, Query:arvDt, Query:arvStnConsOrdr, Query:arvStnRunOrdr, Query:arvRsStnCd, Query:arvTm, Query:trnNo, Query:runDt, Query:trnGpCd, Query:roomClsfCd, Query:scarNo, Query:seatNo, Query:rqSeatAttCd | `com/korail/talk/network/dao/myTicket/MyTicketService.java:23` |

## NFilterService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.nFilter.createKey.do` | `createKey` | `NFilterCreateKeyDao.NFilterCreateKeyResponse` | Field:Device, Field:Version, Field:Key | `com/korail/talk/network/dao/nFilter/NFilterService.java:10` |

## PassCardService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.passCard.DelayDiscountCheck` | `addDelayTicket` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:h_dlay_disc_cnt, Field:h_orgtk_ret_sale_dt, Field:h_orgtk_wct_no, Field:h_orgtk_sale_sqno, Field:h_orgtk_ret_pwd | `com/korail/talk/network/dao/passCard/PassCardService.java:12` |
| POST | `/classes/com.korail.mobile.passCard.DiscountCheck` | `certDCCoupon` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:txtCertNo, Field:txtCertPwd | `com/korail/talk/network/dao/passCard/PassCardService.java:16` |
| POST | `/classes/com.korail.mobile.passCard.DelayDiscountView` | `getDelayTicketList` | `DelayTicketListDao.DelayTicketListResponse` | Field:Device, Field:Version, Field:Key, Field:dptDtTo | `com/korail/talk/network/dao/passCard/PassCardService.java:20` |
| POST | `/classes/com.korail.mobile.passCard.CouponView` | `getDiscountCoupon` | `DCCouponListDao.DCCouponListResponse` | Field:Device, Field:Version, Field:Key, Field:txtSelPage, Field:pnrNo | `com/korail/talk/network/dao/passCard/PassCardService.java:24` |

## PassService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.pass.passPayIssue` | `commPayment` | `CommPaymentDao.CommPaymentResponse` | Field:Device, Field:Version, Field:Key, Field:hidPayAmount, FieldMap, FieldMap | `com/korail/talk/network/dao/pass/PassService.java:19` |
| POST | `/classes/com.korail.mobile.pass.passReserve` | `commReservation` | `CommReservationDao.CommReservationResponse` | Field:Device, Field:Version, Field:Key, Field:hidCmtrKndCd, Field:hidCmtrUtlTrmCd, Field:hidCmtrUtlTrmNm, Field:hidCmtrUtlAgeCd, Field:hidUseOpenDt, Field:hidAppDptStnCd, Field:hidAppDptStnNm, Field:hidAppArvStnCd, Field:hidAppArvStnNm, Field:hidChtrnStnCd, Field:hidChtrnStnNm, Field:hidTrnNo1, Field:hidTrnNo2, Field:hidTrnGpCd1, Field:hidTrnGpCd2, Field:hidDtour1, Field:hidDtour2 | `com/korail/talk/network/dao/pass/PassService.java:23` |
| POST | `/classes/com.korail.mobile.pass.passScheduleInfoList` | `getCommRsvInquiry` | `CommRsvInquiryDao.CommRsvInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:selGoTrain, Field:selGoAbrdDt, Field:txtGoHour, Field:radChgTrnDvCd, Field:txtCmtrKndCd, Field:txtCmtrUtlTrmCd, Field:txtCmtrUtlAgeCd, Field:txtSelPage, Field:txtCntPerPage, Field:txtGoStart, Field:txtGoEnd, Field:txtWkndUseFlg | `com/korail/talk/network/dao/pass/PassService.java:27` |
| POST | `/classes/com.korail.mobile.pass.passInfoList` | `getEnableDate` | `EnableDateDao.EnableDateResponse` | Field:Device, Field:Version, Field:Key, Field:txtCmtrKndCd, Field:txtCmtrUtlTrmCd, Field:txtCmtrUtlAgeCd | `com/korail/talk/network/dao/pass/PassService.java:31` |
| POST | `/classes/com.korail.mobile.pass.passMenu.do` | `passMenu` | `DiscountMenuDao.DiscountMenuResponse` | Field:Device, Field:Version, Field:Key, Field:menuNo | `com/korail/talk/network/dao/pass/PassService.java:35` |
| POST | `/classes/com.korail.mobile.pass.passOtrPayIssue` | `passPayment` | `PassPaymentDao.PassPaymentResponse` | Field:Device, Field:Version, Field:Key, Field:hidPayAmount, Field:h_rcvd_prc, Field:hidWctNo, FieldMap, FieldMap | `com/korail/talk/network/dao/pass/PassService.java:39` |
| POST | `/classes/com.korail.mobile.pass.passOtrReserve` | `passReservation` | `PassReservationDao.PassReservationResponse` | Field:Device, Field:Version, Field:Key, Field:hidCmtrKndCd, Field:hidCmtrUtlTrmCd, Field:hidCmtrUtlAgeCd, Field:hidUseOpenDt | `com/korail/talk/network/dao/pass/PassService.java:43` |
| POST | `/classes/com.korail.mobile.pass.trGdMenuLt.do` | `tripMenu` | `TripMenuDao.TripMenuResponse` | Field:Device, Field:Version | `com/korail/talk/network/dao/pass/PassService.java:47` |

## PayService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.payment.reserve.payco.do` | `getPaycoResult` | `PaycoDao.PaycoPaymentResponse` | Field:Device, Field:Version, Field:Key, Field:ticketPrice, Field:ticketName | `com/korail/talk/network/dao/pay/PayService.java:22` |
| POST | `/classes/com.korail.mobile.pay.spayCphdDatVal.do` | `getSpayCphdDatVal` | `SpayCphdDatValDao.SpayCphdDatValResponse` | Field:Device, Field:Version, Field:Key, Field:spayDvCd, Field:data | `com/korail/talk/network/dao/pay/PayService.java:26` |
| POST | `/classes/com.korail.mobile.pay.monimoDecrypt.do` | `getSpayCphdDatValMonimo` | `SpayCphdDatValMonimoDao.SpayCphdDatValMonimoResponse` | Field:Device, Field:Version, Field:Key, Field:otcNo | `com/korail/talk/network/dao/pay/PayService.java:30` |
| POST | `/classes/com.korail.mobile.pay.spayOrdNo.do` | `getSpayOdrNo` | `SpayOdrNoDao.SpayOdrNoResponse` | Field:Device, Field:Version, Field:Key, Field:spayDvCd, Field:totTxnAmt, Field:tgtCnt, Field:encTotTxnAmt, Field:idx, Field:lumpStlTgtNo | `com/korail/talk/network/dao/pay/PayService.java:34` |
| POST | `/classes/com.korail.mobile.pay.intgStl.do` | `intgStl` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:ctlDvCd, Field:stlPrsJobId, Field:cart_LumpStlTgtNo, FieldMap | `com/korail/talk/network/dao/pay/PayService.java:38` |
| POST | `/classes/com.korail.mobile.pay.naverPayMoneyRsv.do` | `naverPayMoneyRsv` | `NaverPayRsvDao.NaverPayRsvResponse` | Field:Device, Field:Version, Field:Key, Field:productCount, Field:productAmount | `com/korail/talk/network/dao/pay/PayService.java:42` |
| POST | `/classes/com.korail.mobile.pay.naverPayRsv.do` | `naverPayRsv` | `NaverPayRsvDao.NaverPayRsvResponse` | Field:Device, Field:Version, Field:Key, Field:productCount, Field:productAmount | `com/korail/talk/network/dao/pay/PayService.java:46` |
| POST | `/classes/com.korail.mobile.pay.stbkAcnt.do` | `stbkAcnt` | `StbkAcntDao.StbkAcntResponse` | Field:Device, Field:Version, Field:Key, Field:stlBankCd, Field:jobDvCd, Field:acntNo, Field:custCpNo, Field:stbkTxnNo, Field:stlApvPwd | `com/korail/talk/network/dao/pay/PayService.java:50` |
| POST | `/classes/com.korail.mobile.pay.stbkRegBank.do` | `stbkRegBank` | `StbkRegBankDao.StbkRegBankResponse` | Field:Device, Field:Version, Field:Key | `com/korail/talk/network/dao/pay/PayService.java:54` |
| POST | `/classes/com.korail.mobile.pay.stlKeyPrs.do` | `stlKeyPrs` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:jobDvCd, Field:spayDvCd, Field:spayStlKeyVal, Field:stlBankCd, Field:acntNo, Field:binNo | `com/korail/talk/network/dao/pay/PayService.java:58` |
| POST | `/classes/com.korail.mobile.pay.stlKeyQry.do` | `stlKeyQry` | `TossAutoStlKeyQryDao.StlKeyQryResponse` | Field:Device, Field:Version, Field:Key, Field:spayDvCd | `com/korail/talk/network/dao/pay/PayService.java:62` |
| POST | `/classes/com.korail.mobile.pay.tossautoC.do` | `tossautoC` | `TossAutoCreateDao.TossAutoCResponse` | Field:Device, Field:Version, Field:Key | `com/korail/talk/network/dao/pay/PayService.java:66` |

## PaymentService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.payment.ReservationPayment` | `payment` | `RsvPaymentDao.RsvPaymentResponse` | Field:Device, Field:Version, Field:Key, Field:hidPnrNo, Field:hidWctNo, Field:hidTmpJobSqno1, Field:hidTmpJobSqno2, Field:hidRsvChgNo, FieldMap | `com/korail/talk/network/dao/payment/PaymentService.java:12` |

## ProductService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.product.ReservationDetail` | `getProductDetail` | `ProductDetailDao.ProductDetailResponse` | Query:Device, Query:Version, Query:Key, Query:txtVrRsNo, Query:txtVrRsvSqNo | `com/korail/talk/network/dao/product/ProductService.java:12` |
| GET | `/classes/com.korail.mobile.product.ReservationList` | `getProductList` | `ProductListDao.ProductListResponse` | Query:Device, Query:Version, Query:Key, Query:txtSelPage, Query:txtCntPerPage | `com/korail/talk/network/dao/product/ProductService.java:15` |
| GET | `/classes/com.korail.mobile.product.payInfo` | `paymentCheck` | `ProductPaymentCheckDao.ProductPaymentCheckResponse` | Query:Device, Query:Version, Query:Key, Query:txtVrRsNo, Query:txtRsvGdSqno | `com/korail/talk/network/dao/product/ProductService.java:18` |
| GET | `/classes/com.korail.mobile.product.ReservationCancel` | `productCancel` | `BaseResponse` | Query:Device, Query:Version, Query:Key, Query:txtVrRsNo, Query:txtGdSqno | `com/korail/talk/network/dao/product/ProductService.java:21` |

## PushService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.push.callCrew.do` | `callCrew` | `BaseResponse` | Query:Device, Query:Version, Query:Key, Query:pnrNo, Query:jrnySqno, Query:saleWctNo, Query:saleDt, Query:saleSqno, Query:tkRetPwd, Query:sndSqno, Query:coutMsgDvCd, Query:intgMsgCd1, Query:intgMsgCd2, Query:intgMsgCd3, Query:intgMsgCd4, Query:intgMsgCd5, Query:intgMsgCd6, Query:intgMsgCd7, Query:intgMsgCd8, Query:intgMsgCd9, Query:intgMsgCd10, Query:intgMsgCont | `com/korail/talk/network/dao/push/PushService.java:13` |
| GET | `/classes/com.korail.mobile.push.crwCallRq.do` | `callCrewRequestList` | `CallCrewRequestListDao.CallCrewListResponse` | Query:Device, Query:Version, Query:Key, Query:qryDvCd | `com/korail/talk/network/dao/push/PushService.java:16` |
| GET | `/classes/com.korail.mobile.push.cmtrKnd.do` | `cmtrKndPassMenu` | `CmtrKndMenuDao.CmtrKndMenuResponse` | Query:Device, Query:Version, Query:Key, Query:cmtrKndCd | `com/korail/talk/network/dao/push/PushService.java:19` |
| GET | `/classes/com.korail.mobile.push.update` | `pushUpdate` | `PushUpdateDao.PushUpdateResponse` | Query:Device, Query:Version, Query:job_dv_cd, Query:tnsm_flg1, Query:tnsm_flg2, Query:tnsm_flg3, Query:tnsm_flg4, Query:dptUsrInpTnum, Query:arvUsrInpTnum | `com/korail/talk/network/dao/push/PushService.java:22` |

## RailPlusService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| GET | `/classes/com.korail.mobile.railplus.autoCharge.do` | `getAutoCharge` | `AutoChargeDao.AutoChargeResponse` | Query:Device, Query:Version, Query:Key, Query:jobDvCd, Query:prepCrdNo | `com/korail/talk/network/dao/railplus/RailPlusService.java:9` |

## ReceiptService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.receipt.ReceiptInfo` | `getTicketReceipt` | `ReceiptDao.ReceiptResponse` | Field:Device, Field:Version, Field:Key, Field:h_orgtk_sale_dt, Field:h_orgtk_wct_no, Field:h_orgtk_sale_sqno, Field:h_orgtk_tk_ret_pwd | `com/korail/talk/network/dao/receipt/ReceiptService.java:10` |

## RefundService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.refunds.executeOnlineRefunds` | `executeOnlineRefunds` | `RefundExecuteTicketRefundDao.RefundExecuteTicketRefundResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:tkKndCd, Field:retDvCd, Field:retRsnCd, Field:ogtkSaleDt, Field:ogtkSaleWctNo, Field:ogtkSaleSqno, Field:ogtkRetPwd, Field:retAmt, Field:retFee, Field:custTeln, Field:acepCustNm | `com/korail/talk/network/dao/refund/RefundService.java:15` |
| POST | `/classes/com.korail.mobile.refunds.CommissionView` | `getTicketCommission` | `RefundCommissionDao.RefundCommissionResponse` | Field:Device, Field:Version, Field:Key, Field:h_orgtk_ret_sale_dt, Field:h_orgtk_wct_no, Field:h_orgtk_sale_sqno, Field:h_orgtk_ret_pwd, Field:h_comp_nm, Field:h_comp_cert_no | `com/korail/talk/network/dao/refund/RefundService.java:19` |
| POST | `/classes/com.korail.mobile.refunds.SelTicketInfo` | `getTicketDetail` | `TicketDetailDao.TicketDetailResponse` | Field:Device, Field:Version, Field:Key, Field:h_orgtk_ret_sale_dt, Field:h_orgtk_wct_no, Field:h_orgtk_sale_sqno, Field:h_orgtk_ret_pwd, Field:h_purchase_history | `com/korail/talk/network/dao/refund/RefundService.java:23` |
| POST | `/classes/com.korail.mobile.refunds.RefundsRequest` | `returnTicket` | `RefundDao.RefundResponse` | Field:Device, Field:Version, Field:Key, Field:txtPnrNo, Field:h_orgtk_sale_dt, Field:h_orgtk_sale_wct_no, Field:h_orgtk_sale_sqno, Field:h_orgtk_ret_pwd, Field:h_mlg_stl, Field:tk_ret_tms_dv_cd, Field:trnNo, Field:pbpAcepTgtFlg, Field:latitude, Field:longitude | `com/korail/talk/network/dao/refund/RefundService.java:27` |
| POST | `/classes/com.korail.mobile.refunds.verifyOnlineRefunds` | `verifyOnlineRefunds` | `RefundVerifyTicketDao.RefundVerifyTicketResponse` | Field:Device, Field:Version, Field:Key, Field:retNo1, Field:retNo2, Field:retNo3, Field:retNo4, Field:strName | `com/korail/talk/network/dao/refund/RefundService.java:31` |

## ResearchService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.research.assignScheduleView.do` | `getAssignScheduleView` | `SeatAssignScheduleViewDao.SeatAssignScheduleViewResponse` | Field:Device, Field:Version, Field:Key, Field:menuId, Field:dptDt, Field:dptTm, Field:dptRsStnNm, Field:arvRsStnNm, Field:trnGpCd, Field:psrmClCd, Field:seatAttCd1, Field:psgNum1, Field:stlbDturDvNm1, Field:dirtChtnDvCd, Field:chtnArvRsStnNm | `com/korail/talk/network/dao/research/ResearchService.java:31` |
| POST | `/classes/com.korail.mobile.research.TrainResearch` | `getCarList` | `SearchCarListDao.SearchCarListResponse` | Field:Device, Field:Version, Field:Key, Field:Sid, Field:txtMenuId, Field:txtPsrmClCd, Field:txtRunDt, Field:txtDptDt, Field:txtTrnClsfCd, Field:txtTrnNo, Field:txtDptRsStnCd, Field:txtArvRsStnCd, Field:txtDptStnRunOrdr, Field:txtArvStnRunOrdr, Field:txtTrnGpCd, Field:txtTotPsgCnt, Field:txtSeatAttCd, Field:txtGdNo, Field:sidTest | `com/korail/talk/network/dao/research/ResearchService.java:35` |
| POST | `/classes/com.korail.mobile.research.cmtrInfo.do` | `getCmtrInfo` | `CmtrInfoDao.CmtrInfoResponse` | Field:Device, Field:Version, Field:Key, Field:jobDvCd, Field:cmtrKndCd, Field:psgCnt, Field:cmtrUtlAgeCd, Field:psgPrnb, Field:ogtkSaleWctNo, Field:ogtkSaleDd, Field:ogtkSaleSqno, Field:ogtkRetPwd, Field:inquiryType | `com/korail/talk/network/dao/research/ResearchService.java:39` |
| POST | `/classes/com.korail.mobile.research.custTripInfo.do` | `getCustTripInfo` | `ConvenienceSettingDao.ConvenienceSettingResponse` | Field:Device, Field:Version, Field:Key, Field:custMgNo, Field:medDvCd, Field:regSqno | `com/korail/talk/network/dao/research/ResearchService.java:43` |
| POST | `/classes/com.korail.mobile.research.mergeSeatsC.do` | `getMergeSeatsInquiry` | `MergeSeatInquiryDao.MergeSeatInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:abrdDt, Field:runDt, Field:trnNo, Field:dptRsStnNm, Field:arvRsStnNm, Field:selRsStnNm, Field:psrmClCd, Field:seatAttCd, Field:totPsgNum | `com/korail/talk/network/dao/research/ResearchService.java:47` |
| GET | `/classes/com.korail.mobile.ticket.dcntCrdUseQry.do` | `getNCardHistory` | `NCardHistoryDao.NCardHistoryResponse` | Query:Device, Query:Version, Query:Key, Query:dcntCrdNo | `com/korail/talk/network/dao/research/ResearchService.java:51` |
| GET | `/classes/com.korail.mobile.research.dcntCrdScheduleView.do` | `getNCardSchedultView` | `NCardInquiryDao.NCardInquiryResponse` | Query:Device, Query:Version, Query:Key, Query:dptDt, Query:dptRsStnNm, Query:arvRsStnNm, Query:dptTm, Query:trnGpCd, Query:dirtChtnDvCd, Query:dcntCrdKndCd, Query:dcntCrdKndMgNo, Query:useTrmDno, Query:usePsbTno, Query:qryPgNo | `com/korail/talk/network/dao/research/ResearchService.java:54` |
| POST | `/classes/com.korail.mobile.research.TResidualSeatsResearch.do` | `getSeatList` | `SearchSeatListDao.SearchSeatListResponse` | Field:Device, Field:Version, Field:Key, Field:trnClsfCd, Field:trnGpCd, Field:runDt, Field:trnNo, Field:srcarNo, Field:psrmClCd, Field:dptRsStnCd, Field:arvRsStnCd, Field:seatAttCd, Field:dptStnRunOrdr, Field:arvStnRunOrdr, Field:totPsgCnt, Field:gdNo, Field:isArrow, Field:Sid, Field:sidTest, Field:ctlDvCd | `com/korail/talk/network/dao/research/ResearchService.java:57` |
| POST | `/classes/com.korail.mobile.research.tripChgOgtk.do` | `getTicketOriginalInquiry` | `OgTkInquiryDao.OgTkInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, FieldMap | `com/korail/talk/network/dao/research/ResearchService.java:61` |
| GET | `/classes/com.korail.mobile.reservation.dcntCrdExtn.do` | `setNCardExtension` | `BaseResponse` | Query:Device, Query:Version, Query:Key, Query:saleWctNo, Query:saleDd, Query:saleSqno, Query:tkRetPwd | `com/korail/talk/network/dao/research/ResearchService.java:65` |
| POST | `/classes/com.korail.mobile.research.dcntCrdInfo.do` | `setNCardReservation` | `NCardReservationDao.NCardReservationResponse` | Field:Device, Field:Version, Field:Key, Field:dcntCrdKndMgNo, Field:custMgNo, Field:vlidTrmStDt, Field:usePsbTno, FieldMap, FieldMap | `com/korail/talk/network/dao/research/ResearchService.java:68` |

## ReservationCancelService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancel` | `reservationCancel` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:txtPnrNo, Field:txtJrnySqno, Field:txtJrnyCnt, Field:hidRsvChgNo | `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:15` |
| POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `reservationCancelCheck` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:txtPnrNo, Field:txtJrnySqno, Field:txtJrnyCnt, Field:hidRsvChgNo | `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:19` |
| POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | `reservationChange` | `ReservationChangeDao.ReservationChangeResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:chgTno, Field:totPrnb, Field:stndFlg, Field:evntWctFlg, Field:wctHndgCncDvCd, Field:lrgCrgFlg, Field:psgCnt, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:23` |

## ReservationService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservation.guideSeatCnd.do` | `getGuideSeatCnd` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:rqSeatAttCd | `com/korail/talk/network/dao/reservation/ReservationService.java:17` |
| GET | `/classes/com.korail.mobile.reservation.ReservationView` | `getRsvHistory` | `TicketRsvHistoryDao.TicketRsvHistoryResponse` | Query:Device, Query:Version, Query:Key | `com/korail/talk/network/dao/reservation/ReservationService.java:21` |
| POST | `/classes/com.korail.mobile.reservation.tripChgPrsC.do` | `getTicketChangeReservation` | `ReservationResponse` | Field:Device, Field:Version, Field:Key, Field:trvlKndCd, Field:totPrnb, Field:isePrnb, Field:stndSeatFlg, Field:intgTktIseFlg, Field:prcFareReCalcFlg, Field:tmpJobSqno, Field:alcSeatDmnPsDvCd, Field:jrny2Cnt, Field:psg2Cnt, Field:ctlDvCd, Field:frcSaleRsnCont, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/reservation/ReservationService.java:24` |
| POST | `/classes/com.korail.mobile.reservation.seatAssign.do` | `setSeatAssignReservation` | `SeatAssignReservationDao.SeatAssignReservationResponse` | Field:Device, Field:Version, Field:Key, Field:menuId, Field:custMgNo, Field:totPrnb, Field:stndFlg, Field:rqScarNum, FieldMap, FieldMap, FieldMap, FieldMap, FieldMap | `com/korail/talk/network/dao/reservation/ReservationService.java:28` |

## ReservationWaitService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.reservationWait.ReservationWait` | `rsvWait` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:txtPnrNo, Field:txtPsrmClChgFlg, Field:txtSmsSndFlg, Field:txtCpNo | `com/korail/talk/network/dao/reservationWait/ReservationWaitService.java:10` |

## SeatMovieService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.seatMovie.ScheduleView` | `getRsvInquiry` | `RsvInquiryResponse` | Field:Device, Field:Version, Field:Sid, Field:txtMenuId, Field:radJobId, Field:selGoTrain, Field:txtTrnGpCd, Field:txtGoTrnNo, Field:txtGoStart, Field:txtGoEnd, Field:txtGoAbrdDt, Field:txtGoHour, Field:txtPsgFlg_1, Field:txtPsgFlg_2, Field:txtPsgFlg_3, Field:txtPsgFlg_4, Field:txtPsgFlg_5, Field:txtSeatAttCd_2, Field:txtSeatAttCd_3, Field:txtSeatAttCd_4, Field:txtJobDv, Field:etrPath, Field:tkDptDt, Field:tkDptTm, Field:tkTrnNo, Field:ebizCrossCheck, Field:srtCheckYn, Field:rtYn, Field:adjStnScdlOfrFlg, Field:mbCrdNo, Field:tkPsrmClCd, Field:tkRcvdAmt, Field:qryDvCd, Field:qryStNo, Field:qryStTrnNo, Field:qryStTrnNo2, Field:pgPrCnt, Field:chtnCnt, Field:chtnRsStnCd1, Field:trnGpCnt, Field:trnGpCd1 | `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:12` |
| POST | `/classes/com.korail.mobile.seatMovie.LimousineScheduleView` | `getRsvLimousineInquiry` | `RsvInquiryResponse` | Field:Device, Field:Version, Field:Sid, Field:txtMenuId, Field:radJobId, Field:txtJobDv, Field:selGoTrain, Field:txtTrnGpCd, Field:txtGoTrnNo, Field:txtGoStart, Field:txtGoEnd, Field:txtGoAbrdDt, Field:txtGoHour, Field:txtPsgFlg_1, Field:txtPsgFlg_2, Field:txtPsgFlg_3, Field:txtPsgFlg_4, Field:txtPsgFlg_5, Field:txtSeatAttCd_2, Field:txtSeatAttCd_3, Field:txtSeatAttCd_4, Field:ebizCrossCheck, Field:srtCheckYn, Field:rtYn | `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:16` |
| POST | `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial` | `getRsvProductInquiry` | `RsvInquiryResponse` | Field:Device, Field:Version, Field:txtMenuId, Field:radJobId, Field:selGoTrain, Field:txtTrnGpCd, Field:txtGoStart, Field:txtGoEnd, Field:txtGoAbrdDt, Field:txtGoHour, Field:txtPsgFlg_1, Field:txtPsgFlg_2, Field:txtPsgFlg_3, Field:txtPsgFlg_4, Field:txtPsgFlg_5, Field:txtSeatAttCd_2, Field:txtSeatAttCd_3, Field:txtSeatAttCd_4, Field:txtGdNo, Field:qryDvCd, Field:qryStNo, Field:qryStTrnNo, Field:qryStTrnNo2, Field:pgPrCnt, Field:chtnCnt, Field:chtnRsStnCd1, Field:trnGpCnt, Field:trnGpCd1 | `com/korail/talk/network/dao/seatMovie/SeatMovieService.java:20` |

## TicketService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.tk.dvcInfoInit.do` | `deviceReset` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:teln, Field:custNm, Field:nonMbPwd, Field:stlbTrnClsfCd, Field:dptDttm, Field:latitude, Field:longitude, Field:trnNo | `com/korail/talk/network/dao/ticket/TicketService.java:26` |
| POST | `/classes/com.korail.mobile.tk.dlvRcvCust.do` | `dlvRcvCust` | `DlvRcvCustDao.DlvRcvCustwResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:tkRetPwd | `com/korail/talk/network/dao/ticket/TicketService.java:30` |
| POST | `/classes/com.korail.mobile.ticket.ticketDupCheck.do` | `duplicationCheck` | `TicketDuplicationCheckDao.DuplicationCheckResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo | `com/korail/talk/network/dao/ticket/TicketService.java:34` |
| POST | `/classes//com.korail.mobile.addService.cancelPay.do` | `getMaasCancel` | `BaseResponse` | Field:Device, Field:Version, Field:custMgNo, Field:lumpStlTgtNo | `com/korail/talk/network/dao/ticket/TicketService.java:38` |
| POST | `/classes/com.korail.mobile.addService.coptCnc.do` | `getMaasServiceCancel` | `BaseResponse` | Field:Device, Field:Version, Field:pnrNo, Field:cncTgtCnt, Field:cncAddSrvReqNo, Field:cncRetFee | `com/korail/talk/network/dao/ticket/TicketService.java:42` |
| POST | `/classes/com.korail.mobile.maas.cncFee.do` | `getMaasServiceCancelFee` | `MaasServiceCancelFeeDao.MaasServiceCancelFeeResponse` | Field:Device, Field:Version, Field:Key, Field:addSrvReqNo, Field:addSrvDvCd, Field:coptEntRsvNo | `com/korail/talk/network/dao/ticket/TicketService.java:46` |
| POST | `/classes/com.korail.mobile.copt.gdReqQry.do` | `getMaasServiceDetailList` | `MaasServiceDetailListDao.MaasServivceDetailResponse` | Field:Device, Field:Version, Field:qryDtFrom, Field:qryDtTo | `com/korail/talk/network/dao/ticket/TicketService.java:50` |
| POST | `/classes/com.korail.mobile.self.seatChgInfo.do` | `getSelfSeatChgInfo` | `CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse` | Field:Device, Field:Version, Field:Key, Field:runDt, Field:trnNo, Field:dptRsStnCd, Field:arvRsStnCd, Field:psrmClCd | `com/korail/talk/network/dao/ticket/TicketService.java:54` |
| POST | `/classes/com.korail.mobile.reservation.tripChgDate.do` | `getTripChgDate` | `TripChgInfoDao.TripChgInfoDaoResponse` | Field:Device, Field:Version, Field:Key, Field:tripChgDate | `com/korail/talk/network/dao/ticket/TicketService.java:58` |
| POST | `/classes/com.korail.mobile.tk.gurdSmsSnd.do` | `gurdSmsSnd` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:pnrNo, Field:jrnySqno, Field:rcvPsHndyTeln | `com/korail/talk/network/dao/ticket/TicketService.java:62` |
| POST | `/classes/com.korail.mobile.tk.pbpAcepSpec.do` | `pbpAcepSpec` | `PbpAcepSpecDao.PbpAcepSpecResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, Field:tkRetNo | `com/korail/talk/network/dao/ticket/TicketService.java:66` |
| POST | `/classes/com.korail.mobile.tk.pbpWdrw.do` | `pbpTkWdrw` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:pbpCnt, Field:pbpRsvNo, Field:pnrNo | `com/korail/talk/network/dao/ticket/TicketService.java:70` |
| POST | `/classes/com.korail.mobile.tk.plfNo.do` | `plfNo` | `UpdatePlatformDao.PlfNoResponse` | Field:Device, Field:Version, Field:Key, Field:tkCnt, Field:tkRetNo | `com/korail/talk/network/dao/ticket/TicketService.java:74` |
| POST | `/classes/com.korail.mobile.tk.rcntDlvHst.do` | `rcntDlvHst` | `RecentDeliveryHistoryDao.RcntDlvHstResponse` | Field:Device, Field:Version, Field:Key, Field:custMgNo | `com/korail/talk/network/dao/ticket/TicketService.java:78` |
| POST | `/classes/com.korail.mobile.checkin.cnc.do` | `selfCheckinCancel` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:tkRetPwd, Field:jrnySqno | `com/korail/talk/network/dao/ticket/TicketService.java:82` |
| POST | `/classes/com.korail.mobile.checkin.info.do` | `selfCheckinInfo` | `SelfCheckinInfoDao.SelfCheckinInfoResponse` | Field:Device, Field:Version, Field:Key, Field:saleWctNo, Field:saleDt, Field:saleSqno, Field:tkRetPwd, Field:jrnySqno | `com/korail/talk/network/dao/ticket/TicketService.java:86` |
| POST | `/classes/com.korail.mobile.checkin.psbFlg.do` | `selfCheckinPossible` | `SelfCheckinPossibleDao.SelfCheckinPossibleResponse` | Field:Device, Field:Version, Field:Key, Field:qrcode, Field:saleWctNo, Field:saleDd, Field:saleSqno, Field:tkRetPwd, Field:jrnySqno | `com/korail/talk/network/dao/ticket/TicketService.java:90` |
| POST | `/classes/com.korail.mobile.checkin.reg.do` | `selfCheckinRegister` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:cpsNo, Field:scarNo, Field:seatNo, Field:saleWctNo, Field:saleDd, Field:saleSqno, Field:tkRetPwd, Field:jrnySqno | `com/korail/talk/network/dao/ticket/TicketService.java:94` |
| POST | `/classes/com.korail.mobile.ticket.tripChgHndgCnc.do` | `ticketChangeCancel` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:lumpStlCnt, FieldMap | `com/korail/talk/network/dao/ticket/TicketService.java:98` |

## TrainsInfoService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.trn.fresScar.do` | `getFresScar` | `FresScarDao.FresScarResponse` | Field:Device, Field:Version, Field:Key, Field:runDt, Field:trnNo, Field:dptStnConsOrdr, Field:arvStnConsOrdr, Field:dptStnRunOrdr, Field:arvStnRunOrdr | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:20` |
| POST | `/classes/com.korail.mobile.trn.prcFare.do` | `getPrice2Fare` | `Price2FareDao.Price2FareResponse` | Field:Device, Field:Version, Field:Key, Field:txtMenuId, Field:chtnDvCd, Field:trnCnt, FieldMap | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:24` |
| POST | `/classes/com.korail.mobile.trainsInfo.TrainCharge` | `getPriceFare` | `PriceFareDao.PriceFareResponse` | Field:Device, Field:Version, Field:Key, Field:txtMenuId, Field:txtRtnDvCd, Field:txtChtrDvCd1, Field:txtSeatAttCd4, FieldMap | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:28` |
| POST | `/classes/com.korail.mobile.qry.chtnStn.do` | `getSelectStationInfo` | `TrainSelectStationDao.TrainSelectStationResponse` | Field:Device, Field:Version, Field:Key, Field:dptRsStnCd, Field:arvRsStnCd | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:32` |
| POST | `/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom` | `getTourTrainInfo` | `TourTrainInfoDao.TourTrainInfoResponse` | Field:Device, Field:Version, Field:Key, Field:txtTrnGpCd | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:36` |
| POST | `/classes/com.korail.mobile.research.actualTrainSchedule.do` | `getTrainSchedule` | `TrainScheduleDao.TrainScheduleResponse` | Field:Device, Field:Version, Field:runDt, Field:trnNo | `com/korail/talk/network/dao/trainsInfo/TrainsInfoService.java:40` |

## XPointService

| HTTP | Path | Java Method | Return Type | Parameters | Source |
|---|---|---|---|---|---|
| POST | `/classes/com.korail.mobile.xPoint.OkCashbagCertView` | `certifyOKCashbag` | `BaseResponse` | Field:Device, Field:Version, Field:Key, Field:cp_no | `com/korail/talk/network/dao/xPoint/XPointService.java:14` |
| POST | `/classes/com.korail.mobile.xPoint.MyXPointView` | `getKorailPoint` | `KorailPointInquiryDao.KorailPointInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:point_dv_cd | `com/korail/talk/network/dao/xPoint/XPointService.java:18` |
| POST | `/classes/com.korail.mobile.mlg.lpotAthn.do` | `getLPoint` | `LPointDao.LPointInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:pontPwd | `com/korail/talk/network/dao/xPoint/XPointService.java:22` |
| POST | `/classes/com.korail.mobile.mlg.amtSpec.do` | `getMileage` | `MileageInquiryDao.MileageInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:pontTpVal, Field:qryDvVal, Field:qryStDt, Field:qryClsDt, Field:pgPrCnt, Field:nowPgNo | `com/korail/talk/network/dao/xPoint/XPointService.java:26` |
| POST | `/classes/com.korail.mobile.xPoint.XPointView` | `getPoint` | `PointInquiryDao.PointInquiryResponse` | Field:Device, Field:Version, Field:Key, Field:inp_dv_cd, Field:point_dv_cd, Field:xpoint_no, Field:xpoint_pwd, Field:stl_crd_valid_trm | `com/korail/talk/network/dao/xPoint/XPointService.java:30` |
