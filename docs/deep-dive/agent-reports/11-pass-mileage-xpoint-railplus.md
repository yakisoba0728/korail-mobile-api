# 11. 패스, 마일리지, XPoint, RailPlus 정적 분석

## 분석 기준과 주의

- 분석 대상은 로컬 `analysis/jadx/sources`의 JADX 산출물과 `analysis/reports/api-endpoints.tsv`이다. 네트워크 호출, 서버 응답 확인, 동적 트래픽 캡처는 하지 않았다.
- 공통 요청 필드는 `BaseRequest` 생성자가 채운다: `Device=AD`, `Version=250601003`, `Key=korail1234567890`. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`.
- 공통 응답 베이스는 `BaseResponse`의 `h_msg_cd`, `h_msg_txt`, `strResult`이다. 근거: `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`.
- 아래 "응답 필드"는 코드에 선언된 Java 클래스/필드명만 적었다. 실제 서버 응답값, 예시 payload, 성공/실패 코드 값은 조작하지 않았다.

## 핵심 파일

| 영역 | 주요 파일 |
|---|---|
| Pass API | `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassService.java` |
| Pass DAO | `PassReservationDao.java`, `PassPaymentDao.java`, `CommRsvInquiryDao.java`, `CommReservationDao.java`, `CommPaymentDao.java`, `EnableDateDao.java`, `DiscountMenuDao.java`, `TripMenuDao.java` |
| Pass UI | `ui/booking/discountBooking/pass/APassBookingActivity.java`, `NewAPassBookingActivity.java`, `GangneungPassBookingActivity.java`, `ui/booking/discountBooking/commutation/CommutationBookingActivity.java`, `PeriodCommutationBookingActivity.java`, `ui/inquiry/CommutationInquiryActivity.java`, `ui/reservation/confirm/activity/CReservationConfirmActivity.java`, `ui/payment/PaymentActivity.java` |
| PassCard API/DAO | `analysis/jadx/sources/com/korail/talk/network/dao/passCard/PassCardService.java`, `DCCouponListDao.java`, `DCCouponCertDao.java`, `DelayTicketListDao.java`, `DelayTicketAddDao.java`, `DCEmployeeCouponCertDao.java` |
| Mileage API/DAO/UI | `network/dao/mileage/MileageService.java`, `AcpnMlgSpecDao.java`, `AcpnMlgSaveDao.java`, `AcpnMlgNotiDao.java`, `ui/mileage/*.java` |
| XPoint API/DAO/payment | `network/dao/xPoint/XPointService.java`, `MileageInquiryDao.java`, `KorailPointInquiryDao.java`, `PointInquiryDao.java`, `OKCashbagCertDao.java`, `LPointDao.java`, `analysis/jadx/sources/B6/AbstractC1269e.java`, `analysis/jadx/sources/V4/a.java` |
| RailPlus | `network/dao/railplus/RailPlusService.java`, `AutoChargeDao.java`, `ui/railPlus/RailPlusActivity.java`, `analysis/jadx/sources/S4/C0804d.java`, `analysis/jadx/sources/B6/AbstractC1269e.java` |

## PassService 엔드포인트

근거: `analysis/jadx/sources/com/korail/talk/network/dao/pass/PassService.java`, `analysis/reports/api-endpoints.tsv`.

| 목적 | HTTP | Path | Java method | 요청 필드 |
|---|---|---|---|---|
| 정기승차권 결제 발행 | POST | `/classes/com.korail.mobile.pass.passPayIssue` | `commPayment` | `Device`, `Version`, `Key`, `hidPayAmount`, `commPaymentMap` FieldMap, `PaymentMethod` FieldMap |
| 정기승차권 예약 | POST | `/classes/com.korail.mobile.pass.passReserve` | `commReservation` | `hidCmtrKndCd`, `hidCmtrUtlTrmCd`, `hidCmtrUtlTrmNm`, `hidCmtrUtlAgeCd`, `hidUseOpenDt`, `hidAppDptStnCd`, `hidAppDptStnNm`, `hidAppArvStnCd`, `hidAppArvStnNm`, `hidChtrnStnCd`, `hidChtrnStnNm`, `hidTrnNo1`, `hidTrnNo2`, `hidTrnGpCd1`, `hidTrnGpCd2`, `hidDtour1`, `hidDtour2` |
| 정기승차권 열차 후보 조회 | POST | `/classes/com.korail.mobile.pass.passScheduleInfoList` | `getCommRsvInquiry` | `selGoTrain`, `selGoAbrdDt`, `txtGoHour`, `radChgTrnDvCd`, `txtCmtrKndCd`, `txtCmtrUtlTrmCd`, `txtCmtrUtlAgeCd`, `txtSelPage`, `txtCntPerPage`, `txtGoStart`, `txtGoEnd`, `txtWkndUseFlg` |
| 사용 가능 개시일/창구 정보 조회 | POST | `/classes/com.korail.mobile.pass.passInfoList` | `getEnableDate` | `txtCmtrKndCd`, `txtCmtrUtlTrmCd`, `txtCmtrUtlAgeCd` |
| 할인/패스 메뉴 | POST | `/classes/com.korail.mobile.pass.passMenu.do` | `passMenu` | `menuNo` |
| 일반 패스 결제 발행 | POST | `/classes/com.korail.mobile.pass.passOtrPayIssue` | `passPayment` | `hidPayAmount`, `h_rcvd_prc`, `hidWctNo`, `passPaymentMap` FieldMap, `PaymentMethod` FieldMap |
| 일반 패스 예약 | POST | `/classes/com.korail.mobile.pass.passOtrReserve` | `passReservation` | `hidCmtrKndCd`, `hidCmtrUtlTrmCd`, `hidCmtrUtlAgeCd`, `hidUseOpenDt` |
| 여행/패스 메뉴 | POST | `/classes/com.korail.mobile.pass.trGdMenuLt.do` | `tripMenu` | `Device`, `Version` |

## Pass 응답 클래스와 필드

- `EnableDateDao.EnableDateResponse`: `pass_info`, `ticket_info`, `wct_info`.
  - `PassInfo`: `h_use_open_dt`.
  - `Ticket_info`: `h_ise_dt2`.
  - `WctInfo`: `eng_cd_val`, `kor_cd_val`.
  - 근거: `analysis/jadx/sources/com/korail/talk/network/dao/pass/EnableDateDao.java`.
- `PassReservationDao.PassReservationResponse`: `main_info`.
  - `MainInfo`: `h_cmtr_dv_cd`, `h_cmtr_knd_cd`, `h_cmtr_utl_age_cd`, `h_cmtr_utl_trm_cd`, `h_disc_cert_sqno`, `h_fmps_cert_no`, `h_rcvd_amt`, `h_use_cls_dt`, `h_use_open_dt`, `h_use_psb_dno`.
  - 근거: `PassReservationDao.java`.
- `PassPaymentDao.PassPaymentResponse`: `main_info`.
  - `MainInfo`: `h_pnr_no`.
  - 근거: `PassPaymentDao.java`.
- `CommRsvInquiryDao.CommRsvInquiryResponse`: `schedule_info`.
  - `ScheduleInfoList`: `train_list`.
  - `TrainList`: `h_arv_rs_stn_cd`, `h_arv_rs_stn_nm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`, `h_dtour`, `h_schd_prc`, `h_trn_gp_cd`, `h_trn_no`.
  - 근거: `CommRsvInquiryDao.java`.
- `CommReservationDao.CommReservationResponse`: `h_guide`, `main_info`.
  - `MainInfo` 주요 필드: 출발/도착/환승역 코드와 이름, `h_trn_no_1`, `h_trn_no_2`, `h_trn_gp_cd`, `h_cmtr_knd_cd`, `h_cmtr_utl_trm_cd`, `h_use_open_dt`, `h_use_cls_dt`, `h_rcvd_amt`, `h_rcvd_prc`, `h_rcvd_fare`, `h_otm_rcvd_amt`, `h_cust_no`, `h_cust_nm`, `h_psg_tp_cd`, `h_psrm_cl_cd`, `h_holiday_flg`, `h_rsv_trm_dup`, `mStationInfo`, `mUserNames`, `isIncludeHoliday`.
  - 근거: `CommReservationDao.java`.
- `CommPaymentDao.CommPaymentResponse`: `main_info`.
  - `main_info` 타입은 `PassPaymentDao.MainInfo`로 선언되어 있고, `h_pnr_no`를 읽는다.
  - 근거: `CommPaymentDao.java`.
- `DiscountMenuDao.DiscountMenuResponse`: `list`.
  - `DiscountMenu`: `id`, `parentId`, `title`, `type`, `detailType`, `enable`, `information`, `agree`, `isExpand`, `trnGpCd`, `repSegDpt`, `repSegArv`, `goodsData`, `passData`, `webData`.
  - `PassMainInfo`: `h_cmtr_knd_cd`, `h_select_station`, `pass_ageinfo`, `pass_periodinfo`.
  - `PassAgeInfo`: `h_cmtr_utl_age_cd`, `h_comn_cd_nm`, `h_min_age`, `h_max_age`.
  - `PassPeriodInfo`: `h_cmtr_utl_trm_cd`, `h_comn_cd_nm`.
  - `WebData`: `url`.
  - 근거: `DiscountMenuDao.java`.
- `TripMenuDao.TripMenuResponse`: `menuList`, `poppMsg`.
  - `TripMenu`: `menuTitle`, `menuType`, `menuDetail`, `menuBtn`, `menuUrl`, `contCount`, `contList`.
  - `ContentInfo`: `contTitle`, `contDetail`, `contImage`, `contUrl`, `detailType`, `passActive`, `passAgree`, `passType`, `cmtrKndCd`, `passInfo`, `passData`.
  - 근거: `TripMenuDao.java`.

## Pass 구매/사용/취소 흐름

### 일반 패스 구매

1. `APassBookingActivity`, `NewAPassBookingActivity`, `GangneungPassBookingActivity`는 메뉴 데이터에서 `PassMainInfo`를 읽고 기간/연령 선택값을 구성한다. 진입 데이터는 `DISCOUNT_MENU_DATA` 또는 `TRIP_MENU_CONTENT_INFO` intent extra다. 근거: `APassBookingActivity.java`, `NewAPassBookingActivity.java`, `GangneungPassBookingActivity.java`.
2. 구매 가능일 확인은 `EnableDateDao.EnableDateRequest`에 `txtCmtrKndCd`, `txtCmtrUtlTrmCd`, `txtCmtrUtlAgeCd`를 넣어 `passInfoList`로 호출한다. 응답의 `pass_info`가 비어 있으면 구매 불가 다이얼로그를 표시한다. 근거: `APassBookingActivity.java`, `NewAPassBookingActivity.java`, `EnableDateDao.java`.
3. 구매 확정 전 `PassReservationDao.PassReservationRequest`를 만든다. 필드는 `hidCmtrKndCd`, `hidCmtrUtlAgeCd`, `hidCmtrUtlTrmCd`, `hidUseOpenDt`다. 근거: `APassBookingActivity.java`, `NewAPassBookingActivity.java`, `PassReservationDao.java`.
4. `dao_pass_reservation` 수신 후 `main_info`를 `A.convertObjectToMap(main_info)`로 FieldMap화하고 `PassPaymentDao.PassPaymentRequest`를 만든다. 동반자 정보가 있으면 `h_cmpa_cnt`, `h_cmpa_nm_{i}`, `h_cmpa_btdt_{i}`, `h_cmpa_sex_dv_cd_{i}`가 추가된다. 근거: `APassBookingActivity.java`, `NewAPassBookingActivity.java`.
5. 결제 화면으로 `PAYMENT_REQUEST`, `RECEIVED_AMOUNT`, `DISCOUNT_AMOUNT=0`, `PAYMENT_TYPE` intent extra를 전달한다. 근거: `APassBookingActivity.java`, `NewAPassBookingActivity.java`, `PaymentActivity.java`.
6. `PaymentActivity`는 `isPassPaymentRequest()`에서 `PassPaymentDao.PassPaymentRequest` 여부를 구분한다. 실제 결제 FieldMap은 `PaymentMethod`와 `PassPaymentRequest.passPaymentMap`이 `PassService.passPayment`로 합쳐진다. 근거: `PaymentActivity.java`, `PassPaymentDao.java`, `PassService.java`.

### 정기승차권/commutation 구매

1. `CommutationBookingActivity`와 `PeriodCommutationBookingActivity`가 `CommRsvInquiryDao.CommRsvInquiryRequest`를 만들고 `COMMUTATION_REQUEST` extra로 `CommutationInquiryActivity`에 넘긴다. 정기/기간 여부는 `IS_PERIOD_COMMUTATION` extra다. 근거: `CommutationBookingActivity.java`, `PeriodCommutationBookingActivity.java`.
2. `CommutationInquiryActivity.v0()`가 `passScheduleInfoList`를 호출한다. `txtSelPage=1`, `txtCntPerPage=""`를 설정하고 `WRG000000` 에러 메시지는 다이얼로그 생략 대상으로 등록한다. 근거: `CommutationInquiryActivity.java`.
3. 사용자가 후보를 선택하면 `CommReservationRequest`가 생성된다. 선택한 `train_list`에서 출발/도착역, 환승역, 열차번호, 열차그룹, 우회 여부(`hidDtour1/2`)가 채워진다. 근거: `CommutationInquiryActivity.java`, `CommRsvInquiryDao.java`.
4. `commReservation` 응답에 `h_guide`가 있으면 안내 다이얼로그 후 계속 진행한다. 이후 `main_info`에 화면 표시용 `mStationInfo`, `mUserNames`, `isIncludeHoliday`를 추가하고 `CommPaymentDao.CommPaymentRequest`를 만든다. 근거: `CommutationInquiryActivity.java`, `CommReservationDao.java`.
5. `CReservationData`는 `reservationType=COMMUTATION`, `paymentType=PAYMENT_DEFAULT`, `paymentRequest`, `mainInfo`를 들고 `CReservationConfirmActivity`로 이동한다. 근거: `CommutationInquiryActivity.java`, `analysis/jadx/sources/com/korail/talk/data/reservation/CReservationData.java`.
6. `CReservationConfirmActivity`에서 약관 체크 후 `PaymentActivity`로 `PAYMENT_REQUEST`, `IS_POINT_STEP=true`, `RECEIVED_AMOUNT=mainInfo.h_rcvd_amt`, `DISCOUNT_AMOUNT=0`을 넘긴다. 근거: `CReservationConfirmActivity.java`.
7. `PaymentActivity`는 정기승차권 결제를 별도 판별하는 `isCommPaymentRequest()`를 가진다. 근거: `PaymentActivity.java`.

### 사용/조회

- 발권 후 패스/정기권은 티켓 목록의 별도 탭과 카드 UI에서 처리된다. `TicketListActivity`는 `IS_COMMUTATION_PASS_TICKET` extra를 읽고 탭 라벨에 `commutation_pass_ticket`을 사용하며, `TicketListDao.ReservationList.cmtrVlidFlg`가 정기권 유효성 관련 필드로 선언되어 있다. 근거: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`, `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java`.
- 패스/정기권의 "사용"에 해당하는 별도 `PassService` endpoint는 정적 분석 범위에서 확인되지 않았다. 티켓 목록/표시/반환 계열 공통 DAO와 UI에서 처리되는 것으로 보이나, 실제 검표/사용 상태 전환 서버 응답은 이 문서에서 추정하지 않는다.

### 취소/환불

- `PassService`에는 취소 전용 method가 없다. 발권 후 반환은 공통 `RefundService.returnTicket` 경로를 사용한다.
- `RefundService.returnTicket` path는 `/classes/com.korail.mobile.refunds.RefundsRequest`이고 요청 필드는 `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_sale_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_mlg_stl`, `tk_ret_tms_dv_cd`, `trnNo`, `pbpAcepTgtFlg`, `latitude`, `longitude`다. 근거: `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java`, `RefundDao.java`.
- `RefundDao.RefundResponse`는 `stlList`를 가지고, 각 `StlList`에는 `stl_mns_cd`가 있다. RailPlus 결제수단 코드 `13`이 반환 목록에 있으면 RailPlus 동기화 브로드캐스트를 보낸다. 근거: `RefundDao.java`, `TicketReturnActivity.java`, `S4/C0804d.java`.

## PassCardService: 할인쿠폰/지연할인권

근거: `analysis/jadx/sources/com/korail/talk/network/dao/passCard/PassCardService.java`.

| 목적 | HTTP | Path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|---|
| 지연할인권 직접 등록 | POST | `/classes/com.korail.mobile.passCard.DelayDiscountCheck` | `addDelayTicket` | `h_dlay_disc_cnt`, `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd` | `BaseResponse` |
| 할인쿠폰 인증/등록 | POST | `/classes/com.korail.mobile.passCard.DiscountCheck` | `certDCCoupon` | `txtCertNo`, `txtCertPwd` | `BaseResponse` |
| 지연할인권 목록 | POST | `/classes/com.korail.mobile.passCard.DelayDiscountView` | `getDelayTicketList` | `dptDtTo` | `DelayTicketListResponse` |
| 할인쿠폰 목록 | POST | `/classes/com.korail.mobile.passCard.CouponView` | `getDiscountCoupon` | `txtSelPage`, `pnrNo` | `DCCouponListResponse` |

응답 필드:

- `DCCouponListDao.DCCouponListResponse`: `coupon_infos`, `h_page_no`, `h_tot_page_cnt`.
  - `CouponInfos.coupon_info`: `List<DiscountCoupon>`.
  - `DiscountCoupon`: `h_cpn_no`, `h_disc_rt_amt_dv_cd`, `h_fdcert_mg_cls_dt`, `h_inwk_fare_disc_rt_amt`, `h_inwk_prc_disc_rt_amt`, `h_wknd_fare_disc_rt_amt`, `h_wknd_prc_disc_rt_amt`, `h_rmk_1_cont`, `h_rmk_2_cont`, `h_rmk_3_cont`, `guide`, `mIndex`.
  - `isMore()`는 `h_page_no < h_tot_page_cnt`일 때 다음 페이지가 있다고 판단한다.
  - 근거: `DCCouponListDao.java`.
- `DCCouponCertDao.DCCouponCertRequest`: `txtCertNo`, `txtCertPwd`, `couponInputViewIndex`. 응답은 `BaseResponse`만 사용한다. 근거: `DCCouponCertDao.java`.
- `DCEmployeeCouponCertDao`는 `DCCouponCertDao`를 상속하고 DAO id만 `dao_employee_cert_coupon`으로 바꾼다. 근거: `DCEmployeeCouponCertDao.java`.
- `DelayTicketListDao.DelayTicketListResponse`: `disc_infos`.
  - `DiscInfos.disc_info`: `List<DelayCoupon>`.
  - `DelayCoupon`: `h_dlay_fare`, `h_orgtk_ret_pwd`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_wct_no`, `h_use_psb_dt`, `mIndex`.
  - 근거: `DelayTicketListDao.java`.
- `DelayTicketAddDao.DelayTicketAddRequest`: `h_dlay_disc_cnt`, `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `delayCouponInputViewIndex`. 응답은 `BaseResponse`만 사용한다. 근거: `DelayTicketAddDao.java`.

UI 흐름:

- 할인쿠폰 목록은 `DiscountCouponActivity`가 `DCCouponListDao`를 호출하고 `txtSelPage` 기반으로 페이지를 누적한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/menu/DiscountCouponActivity.java`.
- 지연할인권 목록은 `DelayDiscountCouponActivity`가 `DelayTicketListDao`를 호출한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/menu/DelayDiscountCouponActivity.java`.
- 결제 화면에서는 `PaymentActivity.makeDiscountCouponEntries()`와 `makeDelayCouponEntries()`가 DAO 응답 객체를 UI 선택 항목으로 바꾼다. 직접 입력 항목도 추가한다. 근거: `PaymentActivity.java`.

## MileageService: 사후/동반자 마일리지 적립

근거: `analysis/jadx/sources/com/korail/talk/network/dao/mileage/MileageService.java`.

| 목적 | HTTP | Path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|---|
| 동반자에게 적립 안내 | POST | `/classes/com.korail.mobile.mileage.acpnMlgNoti.do` | `acpnMlgNoti` | `saleWctNo`, `saleDt`, `saleSqno`, `retPwd`, `rcvPsHndyTeln` | `BaseResponse` |
| 동반자/사후 적립 저장 | POST | `/classes/com.korail.mobile.mileage.acpnMlgSave.do` | `acpnMlgSave` | `rsvMbCrdNo`, `custNm`, `mlgAcmMbCrdNo`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd` | `BaseResponse` |
| PNR별 적립 대상 상세 | POST | `/classes/com.korail.mobile.mileage.acpnMlgSpec.do` | `acpnMlgSpec` | `pnrNo` | `AcpnMlgSpecResponse` |

응답 필드:

- `AcpnMlgSpecDao.AcpnMlgSpecResponse`: `tkList`.
  - `Ticket`: `mbCrdNo`, `rsvPsHndyTeln`, `rsvPsNm`, `saleDt`, `saleSqno`, `saleWctNo`, `tkRetPwd`, `jrnyList`.
  - `Jrny`: `jrnySqno`, `jrnyTpCd`, `psrmClCd`, `psrmClNm`, `seatList`.
  - `Seat`: `mlgSaveFlg`, `mlgSaveTgt`, `psgTpDvCd`, `psgTpDvNm`, `scarNo`, `seatNo`, `seatSpec`.
  - 근거: `AcpnMlgSpecDao.java`.
- `AcpnMlgSaveDao`와 `AcpnMlgNotiDao`는 `BaseResponse`만 사용한다. 근거: `AcpnMlgSaveDao.java`, `AcpnMlgNotiDao.java`.

마일리지 적립 흐름:

- `CompanionMileageDetailActivity`는 `TICKET_PNR_NUMBER` extra를 읽고 `AcpnMlgSpecDao`로 PNR별 티켓/좌석 목록을 조회한다. `mlgSaveFlg=Y` 여부로 이미 적립된 항목 표시/동작을 구분한다. 근거: `ui/mileage/CompanionMileageDetailActivity.java`.
- `CompanionMileageRequestActivity`는 선택된 `COMPANION_MILEAGE_DATA` 티켓을 받아 예약자 카드번호(`rsvMbCrdNo`), 적립 대상 회원번호(`mlgAcmMbCrdNo`), 이름(`custNm`), 원권 번호 조각을 `AcpnMlgSaveRequest`에 넣는다. 근거: `CompanionMileageRequestActivity.java`.
- `CompanionMileageInformActivity`는 같은 티켓 객체에서 원권 정보를 읽고 수신자 휴대폰 `rcvPsHndyTeln`을 입력받아 `AcpnMlgNotiDao`를 호출한다. 근거: `CompanionMileageInformActivity.java`.
- `AccumulatingKTXMileageActivity`는 직접 입력 화면이다. 회원번호/휴대폰/이메일로 `MemberCertDao` 검증 후, 반환번호 조각(`saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`)과 예약자/적립자 정보를 `AcpnMlgSaveDao`에 넣는다. 근거: `AccumulatingKTXMileageActivity.java`.

## XPointService: 마일리지 조회와 외부 포인트

근거: `analysis/jadx/sources/com/korail/talk/network/dao/xPoint/XPointService.java`.

| 목적 | HTTP | Path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|---|
| OK캐쉬백 휴대폰 인증 | POST | `/classes/com.korail.mobile.xPoint.OkCashbagCertView` | `certifyOKCashbag` | `cp_no` | `BaseResponse` |
| 코레일 포인트/쿠폰 요약 | POST | `/classes/com.korail.mobile.xPoint.MyXPointView` | `getKorailPoint` | `point_dv_cd` | `KorailPointInquiryResponse` |
| L.Point 인증/조회 | POST | `/classes/com.korail.mobile.mlg.lpotAthn.do` | `getLPoint` | `pontPwd` | `LPointInquiryResponse` |
| 마일리지 내역 조회 | POST | `/classes/com.korail.mobile.mlg.amtSpec.do` | `getMileage` | `pontTpVal`, `qryDvVal`, `qryStDt`, `qryClsDt`, `pgPrCnt`, `nowPgNo` | `MileageInquiryResponse` |
| 포인트 조회 | POST | `/classes/com.korail.mobile.xPoint.XPointView` | `getPoint` | `inp_dv_cd`, `point_dv_cd`, `xpoint_no`, `xpoint_pwd`, `stl_crd_valid_trm` | `PointInquiryResponse` |

응답 필드:

- `KorailPointInquiryDao.KorailPointInquiryResponse`: `h_korail_point`, `h_disc_coup_cnt`, `h_delay_cnt`, `h_cntc_chn_cont1`, `h_cp_athn_flg`, `h_emil_athn_flg`, `h_hdcp_flg`, `h_logn_tp_cd1`, `h_logn_tp_cd2`, `h_logn_tp_cd4`, `h_logn_tp_cd5`, `h_cust_lead_flg_nm`, `h_subt_dcs_cl_cd`, `h_subt_dcs_cl_nm`. `executeDao()`는 `point_dv_cd`를 `"0"`으로 고정한다. 근거: `KorailPointInquiryDao.java`.
- `MileageInquiryDao.MileageInquiryResponse`: `delPontValNum`, `ktxMlgInfo`, `pgCnt`, `railNowSavePontValNum1`, `totAcmRailPontValNum1`, `totAvlAfltPontValNum`, `totAvlRailPontValNum`, `totAvlRailPontValNum1`, `totUseRailPontValNum1`, `specList`.
  - `SpecList`: `dptDt`, `mlgAcmDvCdNm`, `pontAmt`, `pontDvNm`, `rcpDvNm`, `savePontValNum`, `stlAmt`.
  - 근거: `MileageInquiryDao.java`.
- `PointInquiryDao.PointInquiryResponse`: `h_avl_point`, `h_corp_use_point`, `h_join_point`, `h_korail_point`, `h_point`. 근거: `PointInquiryDao.java`.
- `LPointDao.LPointInquiryResponse`: `custRcgnNoVal`, `extrPontAmt`, `prsCnqeVal`, `pwdErrTno`. 요청 클래스에는 `custRcgnNoVal`, `jobDvCd`, `pontPwd`가 있지만 service 호출에는 `pontPwd`만 전달된다. 근거: `LPointDao.java`, `XPointService.java`.
- `OKCashbagCertDao.OKCashbagCertRequest`: `cpNo`. 응답은 `BaseResponse`만 사용한다. 근거: `OKCashbagCertDao.java`.

마일리지 조회 흐름:

- `MileageHistoryActivity.R0()`는 `MileageInquiryRequest`에 `pontTpVal`, `qryDvVal`, 조회 시작/종료일, `pgPrCnt=20`, `nowPgNo`를 넣어 `getMileage`를 호출한다. 응답 수신 시 총 사용 가능 KTX/Samsung KTX 마일리지, 가맹 포인트, 소멸 예정 포인트, 페이지 수, `specList`를 화면 모델에 반영한다. 근거: `ui/mileage/MileageHistoryActivity.java`.
- `MyPageActivity`와 `MemberCardActivity`는 `KorailPointInquiryDao`를 호출해 회원카드/마이페이지의 코레일 포인트, 할인쿠폰 수, 지연할인 수, 휴대폰/이메일 인증 여부를 갱신한다. 근거: `ui/mypage/MyPageActivity.java`, `ui/setting/memberCard/MemberCardActivity.java`.

포인트/마일리지 결제 사용 흐름:

- 결제 fragment 계층인 `analysis/jadx/sources/B6/AbstractC1269e.java`는 `KTXMileageView`, Rail Point, Woori, City, OKCashbag, L.Point, Gifticket view의 action listener를 등록한다.
- KTX 마일리지 조회는 `PointInquiryRequest.pointDvCd="0"`으로 `PointInquiryDao`를 호출한다. 응답에서 `h_korail_point`와 `h_corp_use_point`를 각각 KTX 마일리지와 Samsung KTX 마일리지로 보관한다. 근거: `AbstractC1269e.java`, `PointInquiryDao.java`.
- `KTXMileageView`는 `queryBtn`, `applyBtn`, `allApplyBtn`을 통해 `onRequestQuery(0)`, `onRequestApply(0)`, `onRequestAllApply(0)`를 호출한다. 입력 포인트는 `INPUT_POINT`, 가능 포인트는 `ENABLE_POINT`, 적용 포인트는 `USE_POINT` 번들 키로 전달된다. 근거: `view/payment/point/KTXMileageView.java`.
- 적용 규칙은 코드상 최소 100포인트, 100단위 사용, 결제 잔액 초과 불가로 검사된다. Samsung KTX 마일리지는 일반 KTX 마일리지 부족분을 채우는 방식으로 `useingKTXMileage`, `useingKTXSamsungMileage`에 분리된다. 근거: `AbstractC1269e.java`.
- `V4.a.getPointRequest()`가 실제 결제 FieldMap을 만든다. KTX 마일리지는 `hidStlMnsCd{n}=12`, `hidCrdInpWayCd{n}=P`, `hidPontDvCd{n}=0` 또는 Samsung 분리 시 `4`, `hidPontInpDvCd{n}=1`, `hidPontCrdPwd{n}=****`, `hidMnsStlAmt{n}`로 들어간다. 근거: `analysis/jadx/sources/V4/a.java`, `PaymentMethod.java`.
- 다른 포인트 구분도 같은 `PointInquiryDao`/`PaymentMethod` 체계를 공유한다: Rail point `pointType=1`, Woori `2`, City `3`, OKCashbag `5` 계열, L.Point `4` 계열, Gifticket `6`. 정확한 외부 서비스 의미는 코드명과 UI명 기준으로만 적었다. 근거: `V4/a.java`, `AbstractC1269e.java`.

## RailPlusService와 외부 Rail+ 앱 연동

API:

| 목적 | HTTP | Path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|---|
| RailPlus KTX 자동충전 조회/등록/해지 | GET | `/classes/com.korail.mobile.railplus.autoCharge.do` | `getAutoCharge` | Query `Device`, `Version`, `Key`, `jobDvCd`, `prepCrdNo` | `AutoChargeResponse` |

근거: `analysis/jadx/sources/com/korail/talk/network/dao/railplus/RailPlusService.java`, `AutoChargeDao.java`.

응답 필드:

- `AutoChargeDao.AutoChargeResponse`: `psbFlg`.
- `AutoChargeDao.AutoChargeRequest`: `jobDvCd`, `prepCrdNo`.

RailPlusActivity 흐름:

1. `RailPlusActivity.onCreate()`는 화면 초기화 후 `y0()`를 호출한다.
2. `y0()`는 외부 패키지 `com.mic.set.hce.railpluscardserviceandroid`로 `payment_rail_plus_cardinfo_scheme` intent를 실행한다. 앱 미설치/실패 안내를 위한 `PlayAppData`도 구성한다.
3. 외부 앱이 deep link로 돌아오면 `onNewIntent()`가 `RET_CODE`를 확인한다. `RET_CODE=000000`일 때 `BALANCE`를 표시하고 `CARD_NO`를 `DecryptDao`에 넘긴 뒤, 복호화 결과를 `AutoChargeDao.prepCrdNo`로 사용한다.
4. 최초 조회 job은 `"R"`로 보이며, 응답 `psbFlg=="Y"`이면 자동충전 체크박스를 켠다.
5. 체크박스 변경 시 등록/해지 job code를 만들고, 확인 다이얼로그 후 다시 카드번호 복호화와 `AutoChargeDao` 호출을 수행한다. 성공 시 등록/해지 토스트를 띄우고, 오류 시 체크 상태를 롤백한다.

근거: `analysis/jadx/sources/com/korail/talk/ui/railPlus/RailPlusActivity.java`, `network/dao/common/DecryptDao.java`, `AutoChargeDao.java`.

RailPlus 결제와 외부 handoff:

- 결제 fragment의 `A1()`는 외부 RailPlus 앱으로 `payment_rail_plus_scheme` intent를 실행한다. 인자는 결제금액과 회원번호다. 근거: `analysis/jadx/sources/B6/AbstractC1269e.java`.
- ZeroPay/RailPlus 계열도 같은 외부 패키지로 scheme을 실행한다. `setEasyPaymentData()`는 `type=railplus` 또는 `type=railplus_zeropay`이고 `RET_CODE=000000`일 때 결제 데이터를 내부 결제 처리로 넘긴다. `railplus_zeropay`는 `ZERO_PAY_QR_TOKEN` 앞에 코드 문자열을 덧붙인 뒤 처리한다. 근거: `AbstractC1269e.java`.
- `V4.a.getEasyRequest()`에서 `type=railplus`는 `hidStlMnsCd1=13`, `hidMnsStlAmt1=PAYMENT_AMOUNT`, `hidCrdInpWayCd1=@`, `hidStlCrCrdNo1=CARD_NO`, `spayDvCd_1_1=00`으로 결제 FieldMap을 만든다. `type=railplus_zeropay`는 `hidStlMnsCd1`을 현금성 간편결제 코드로 두고 `spayDvCd_1_1=04`, `spayCphdDatVal_1_1=ZERO_PAY_QR_TOKEN`을 넣는다. 근거: `analysis/jadx/sources/V4/a.java`, `PaymentMethod.java`.
- 환불/부가서비스 반환 뒤 결제수단 코드 `13`이 포함되면 `C0804d.syncRailPlus()`가 `korail.mobilerailplus.syncreload` 브로드캐스트를 보낸다. 근거: `TicketReturnActivity.java`, `ui/ticket/ticketReturn/a.java`, `ui/ticket/confirm/TicketListActivity.java`, `S4/C0804d.java`.

## 로컬 저장/상태 변화

- 이 범위에서 확인된 영속 저장은 RailPlus 카드 안내 문자열이다. `IntroActivity`는 앱 데이터 응답의 `railplus_cardinfo`를 SharedPreferences 키 `KEY_RAIL_PLUS_CARD_INFO`에 저장한다. 근거: `analysis/jadx/sources/com/korail/talk/ui/intro/IntroActivity.java`, `network/dao/cache/AppDataDao.java`, `analysis/jadx/sources/S4/H.java`.
- Pass 구매 흐름의 `PAYMENT_REQUEST`, `RESERVATION_DATA`, `COMMUTATION_REQUEST`, `COMPANION_MILEAGE_DATA`, `TICKET_PNR_NUMBER` 등은 `Intent` extra로 Activity 간 전달되는 일시 상태다. 해당 객체들은 `Serializable` 요청/응답 모델을 담지만, 이 범위의 코드에서 직접 SharedPreferences/DB에 저장하는 흐름은 확인되지 않았다.
- 마일리지 조회/적립 화면은 입력값과 응답 리스트를 Activity 필드/ListView adapter에 보관한다. 이 범위에서 마일리지 내역/적립 요청 자체를 로컬 DB에 저장하는 코드는 확인되지 않았다.
- XPoint/포인트 결제 상태는 `AbstractC1269e` 내부 결제 상태 객체와 `KTXMileageView` 번들(`USE_POINT`)에 보관되고, 최종 결제 요청 시 `PaymentMethod` FieldMap으로 합쳐진다. 별도 영속 저장은 확인되지 않았다.
- RailPlus 외부 앱 동기화는 로컬 저장이 아니라 Android broadcast side effect다: action `korail.mobilerailplus.syncreload`. 근거: `S4/C0804d.java`.

## Web/외부 handoff 정리

- Pass 메뉴 모델에는 `DiscountMenuDao.WebData.url`, `TripMenuDao.ContentInfo.contUrl`, `TripMenuDao.TripMenu.menuUrl`이 있어 서버 메뉴가 웹 URL을 내려줄 수 있는 구조다. 이 문서 범위의 정적 분석만으로 실제 URL 값은 확정하지 않는다. 근거: `DiscountMenuDao.java`, `TripMenuDao.java`.
- 결제 handoff는 `EasyPayWebViewActivity`와 외부 앱 scheme이 혼재한다. `AbstractC1269e.C1()/D1()`은 `WEB_GET_URL` extra로 `EasyPayWebViewActivity`를 띄우고, RailPlus/ZeroPay는 외부 패키지 `com.mic.set.hce.railpluscardserviceandroid` intent를 사용한다. 근거: `AbstractC1269e.java`, `ui/web/EasyPayWebViewActivity.java`.
- RailPlusActivity는 외부 앱에서 돌아온 URI query `RET_CODE`, `RET_MSG`, `BALANCE`, `CARD_NO`를 읽는다. 이 값의 실제 예시는 정적 코드에 없으므로 문서화하지 않는다. 근거: `RailPlusActivity.java`.

## 미확인/비추정 항목

- 실제 서버 응답 payload, 메시지 코드, 오류 코드별 의미는 정적 코드만으로 확정하지 않았다.
- 패스/정기권의 사용 처리에 대응하는 별도 `PassService` endpoint는 확인되지 않았다. 티켓 목록/표시 모델에서 패스 타입을 다루는 것은 확인되지만, 서버 상태 전환은 추정하지 않는다.
- `jobDvCd`의 사람이 읽는 명칭은 일부 상수명이 난독화되어 있어 코드상 값 흐름만 기록했다.
