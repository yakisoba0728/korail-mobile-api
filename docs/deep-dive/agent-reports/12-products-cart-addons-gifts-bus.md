# 12. 상품/장바구니/부가서비스/기프티켓/버스 심층 분석

분석 범위: `ProductService`, `CartService`, `AddService`, `GifticketService`, `GiftInfoService`, `BusReservationService`, `IndependentService` 및 직접 연결되는 DAO/model/UI 호출부. 분석은 `analysis/jadx/sources`의 디컴파일 소스 정적 분석만 사용했다. 실제 운영 서버가 내려주는 코드값의 의미, 필수/선택 여부, 값 도메인은 APK 안에서 확인되는 경우만 적고, 그 외는 미확인으로 둔다.

## 공통 규칙

- 모든 DAO request는 `BaseRequest`를 상속하며 생성자에서 `Device=AD`, `Version=250601003`, `Key=korail1234567890`를 기본 설정한다. [source: `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`:6-18]
- 공통 응답 `BaseResponse` 필드는 `h_msg_cd`, `h_msg_txt`, `strResult`이고 성공/실패 문자열 상수는 `SUCC`, `FAIL`이다. [source: `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`:7-18]
- Retrofit 1 스타일이다. `@GET`은 `@Query`, `@POST`는 `@FormUrlEncoded` + `@Field`/`@FieldMap`을 사용한다.
- 정적 분석상 client-side validation은 UI에서 주로 “선택 여부”, “목록 비어 있음”, “취소 확인 dialog” 수준으로 수행된다. 서버 필수값/정합성 검증은 endpoint가 담당하는 것으로 보이며 APK에서 정확한 규칙은 확인되지 않는다.

## Endpoint 전체 목록

| Service | Method | Path | DAO/request | Response |
|---|---:|---|---|---|
| `ProductService` | GET | `/classes/com.korail.mobile.product.ReservationList` | `ProductListDao.ProductListRequest` | `ProductListResponse` |
| `ProductService` | GET | `/classes/com.korail.mobile.product.ReservationDetail` | `ProductDetailDao.ProductDetailRequest` | `ProductDetailResponse` |
| `ProductService` | GET | `/classes/com.korail.mobile.product.payInfo` | `ProductPaymentCheckDao.ProductPaymentCheckRequest` | `ProductPaymentCheckResponse` |
| `ProductService` | GET | `/classes/com.korail.mobile.product.ReservationCancel` | `ProductCancelDao.ProductCancelRequest` | `BaseResponse` |
| `CartService` | POST | `/classes/com.korail.mobile.cart.addCartList` | `AddCartDao.AddCartRequest`, `AddProductDao` | `BaseResponse` |
| `CartService` | POST | `/classes/com.korail.mobile.cart.showCartList` | `CartListDao.CartListRequest` | `CartListResponse` |
| `CartService` | POST | `/classes/com.korail.mobile.maas.rsvStt.do` | `VerifyMaasStatusDao.VerifyMaasStatusRequest` | `BaseResponse` |
| `AddService` | POST | `/classes/com.korail.mobile.addService.reserve.do` | `AdditionalServiceDao.AdditionalServiceRequest` | `AdditionalServiceResponse` |
| `AddService` | POST | `/classes/com.korail.mobile.addService.buyConfirm.do` | `DealCarBuyDao.DealCarBuyRequest` | `BaseResponse` |
| `AddService` | POST | `/classes/com.korail.mobile.addService.reserveList.do` | `ExtraProductListDao.ExtraProductListRequest` | `ExtraProductListResponse` |
| `AddService` | POST | `/classes/com.korail.mobile.addSrv.helpSrvCust.do` | `HelpSrvCustDao.HelpSrvCustRequest` | `HelpSrvCustResponse` |
| `AddService` | POST | `/classes/com.korail.mobile.addSrv.helpSrvTk.do` | `HelpSrvTkDao.HelpSrvTkDaoRequest` | `HelpSrvTkDaoResponse` |
| `GifticketService` | POST | `/classes/com.korail.mobile.gift.gdRsv.do` | `GifticketBookingDao.GifticketBookingRequest` | `GifticketBookingResponse` |
| `GifticketService` | POST | `/classes/com.korail.mobile.gift.gdLst.do` | `GifticketListDao.GifticketListRequest` | `GifticketListResponse` |
| `GifticketService` | POST | `/classes/com.korail.mobile.gift.gdUseSpec.do` | `GifticketHistoryDao.GifticketHistoryRequest` | `GifticketHistoryResponse` |
| `GifticketService` | POST | `/classes/com.korail.mobile.gift.gdRet.do` | `GifticketReturnDao.GifticketReturnRequest` | `GifticketReturnResponse` |
| `GiftInfoService` | POST | `/classes/com.korail.mobile.giftInfo.GiftSend` | `TicketPresentDao.TicketPresentRequest` | `TicketPresentResponse` |
| `BusReservationService` | POST | `/classes/com.korail.mobile.lmu.scdlQry.do` | `BusReservationListDao.BusInquiryRequest` | `BusInquiryResponse` |
| `BusReservationService` | POST | `/classes/com.korail.mobile.lms.TResidualSeatsResearch.do` | `BusReservationSeatListDao.BusSeatListRequest` | `SeatListResponse` |
| `BusReservationService` | POST | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | 선언만 확인, 실제 DAO는 `ReservationCancelService` 사용 | `BaseResponse` |
| `BusReservationService` | POST | `/classes/com.korail.mobile.reservation.reservationChange.do` | 선언만 확인, 실제 DAO는 `ReservationCancelService` 사용 | `ReservationChangeResponse` |
| `IndependentService` | POST | `/classes/com.korail.mobile.login.poppCfmRec.do` | direct service call with `FieldMap` | `BaseResponse` |

서비스 선언 근거: `ProductService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductService.java`:11-22], `CartService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartService.java`:10-21], `AddService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:15-34], `GifticketService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketService.java`:12-27], `GiftInfoService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/giftInfo/GiftInfoService.java`:11-14], `BusReservationService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`:18-33], `IndependentService` [source: `analysis/jadx/sources/com/korail/talk/network/dao/independent/IndependentService.java`:11-14].

## ProductService

### 1. 예약 상품 목록

- Endpoint: `GET /classes/com.korail.mobile.product.ReservationList`
- Request fields: `Device`, `Version`, `Key`, `txtSelPage`, `txtCntPerPage`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductService.java`:15-16]
- Request class: `ProductListDao.ProductListRequest`
  - `txtSelPage:int`
  - `txtCntPerPage:int`
  - DAO는 request getter 값을 그대로 service에 넘긴다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductListDao.java`:29-50,100-104]
- Response class: `ProductListDao.ProductListResponse`
  - 공통 `BaseResponse` 필드
  - `mainInfo: MainInfo`
  - `MainInfo.strTotCnt`
  - `MainInfo.entity: List<ReservationProduct>`
  - `ReservationProduct.strGdNm`
  - `ReservationProduct.strRsvSttCd`
  - `ReservationProduct.strRsvSttNm`
  - `ReservationProduct.strStlDlnDt`
  - `ReservationProduct.strStlSttCd: EnumC5608b`
  - `ReservationProduct.strVrRsvNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductListDao.java`:13-27,53-98]
- Caller flow:
  - `TripBookingListActivity.u0()`가 현재 페이지를 1 증가시키고 `txtCntPerPage=10`으로 요청한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java`:141-149]
  - 응답의 `strTotCnt`로 총 페이지를 계산하고 각 `ReservationProduct`를 화면 bundle로 변환한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java`:235-250]
  - 취소 상태 문구가 포함된 항목은 상세 이동 전에 취소된 예약 dialog를 보여준다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java`:224-230]
- Validation/unknown:
  - `strRsvSttCd` 중 `0`, `07`, `08`, `09`, `10`은 상세 화면 버튼 enabled 여부 계산에서 false로 처리된다. 코드 의미는 APK만으로 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java`:152-154]

### 2. 예약 상품 상세

- Endpoint: `GET /classes/com.korail.mobile.product.ReservationDetail`
- Request fields: `Device`, `Version`, `Key`, `txtVrRsNo`, `txtVrRsvSqNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductService.java`:12-13]
- Request class: `ProductDetailDao.ProductDetailRequest`
  - `txtVrRsvNo`
  - `txtVrRsvSqNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductDetailDao.java`:24-45]
- Response class: `ProductDetailDao.ProductDetailResponse`
  - 공통 `BaseResponse` 필드
  - `mainInfo: ProductInfo`
  - `ProductInfo.entityOne: List<EntityOne>`
  - `ProductInfo.strCncDlnDt`, `strCncRetAmt`, `strCncRetFee`
  - `ProductInfo.strGdNm`, `strGdSqno`, `strInt11`
  - `ProductInfo.strRcvdAmt`, `strRsvSttNm`, `strStlSttCd`
  - `ProductInfo.strTotStlAmt`, `strUtlTrmCont`, `strVrRsvNo`
  - `EntityOne.strGdConsItmNm` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductDetailDao.java`:13-22,48-128]
- Caller flow:
  - 목록 화면이 `VR_RSV_NO`, `VR_RSV_SQ_NO`, `PAYMENT_STATE`, `RSV_STT_CD`를 상세 화면으로 전달한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingListActivity.java`:178-187]
  - 상세 화면은 intent 값을 읽고 `ProductDetailDao`를 실행한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:67-72,116-123,194-205]
  - 응답에서 `strGdSqno`를 저장해 취소 요청에 사용하고, 상품명/구성항목/이용기간/취소기한/금액/상태를 표시한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:133-155,212-216]

### 3. 결제 정보 확인

- Endpoint: `GET /classes/com.korail.mobile.product.payInfo`
- Request fields: `Device`, `Version`, `Key`, `txtVrRsNo`, `txtRsvGdSqno`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductService.java`:18-19]
- Request class: `ProductPaymentCheckDao.ProductPaymentCheckRequest`
  - `txtVrRsNo`
  - `txtRsvGdSqno` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`:27-49]
- Response class: `ProductPaymentCheckDao.ProductPaymentCheckResponse`
  - 공통 `BaseResponse` 필드
  - `mainInfo.strLumpStlTgtNo`
  - `mainInfo.strMrkAmtSum:int` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`:11-25,51-59]
- Caller flow:
  - 상세 화면에서 결제 상태가 특정 enum(`EnumC5608b.f31449`)이면 voucher webview로 이동하고, 그 외에는 `paymentCheck` 후 `PaymentActivity`를 연다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:157-175,178-191]
  - `IntegrationWebViewActivity`도 URL query의 `strVrRsNo`, `strGdSqno`를 파싱해 동일한 결제 확인을 호출할 수 있다. [source: `analysis/jadx/sources/com/korail/talk/ui/web/IntegrationWebViewActivity.java`:120-128]
  - 결제 handoff는 `strLumpStlTgtNo`로 `IntgStlRequest`를 만들고 `RECEIVED_AMOUNT=strMrkAmtSum`, `IS_TRAVEL_PACKAGES=true`를 넘기는 방식이다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:157-169]
- External handoff:
  - Voucher는 `K4.g.VOUCHER_URL`에 `txtVrRsvNo=<예약번호>`를 post parameter로 붙여 `IntegrationWebViewActivity`로 이동한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:171-175]

### 4. 예약 상품 취소

- Endpoint: `GET /classes/com.korail.mobile.product.ReservationCancel`
- Request fields: `Device`, `Version`, `Key`, `txtVrRsNo`, `txtGdSqno`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductService.java`:21-22]
- Request class: `ProductCancelDao.ProductCancelRequest`
  - `txtVrRsNo`
  - `txtGdSqno` [source: `analysis/jadx/sources/com/korail/talk/network/dao/product/ProductCancelDao.java`:11-33]
- Response class: `BaseResponse`.
- Caller flow:
  - 상세 화면은 취소 버튼에서 확인 dialog를 띄운 뒤 `ProductCancelDao`를 실행한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:57-64,85-91,127-130]
  - 성공 시 `setResult(-1)` 후 종료해 목록이 새로고침될 수 있게 한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:219-224]

## CartService

### 1. 장바구니 추가 / 상품 구매 web handoff 전 등록

- Endpoint: `POST /classes/com.korail.mobile.cart.addCartList`
- Request fields: `Device`, `Version`, `Key`, `hidPnrNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartService.java`:11-13]
- Request class: `AddCartDao.AddCartRequest`
  - `hidPnrNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/AddCartDao.java`:11-23]
- Response class: `BaseResponse`.
- DAO behavior:
  - `AddCartDao`는 `dao_add_cart`.
  - `AddProductDao`는 `AddCartDao`를 상속하고 endpoint는 같지만 DAO id만 `dao_add_product`로 바꾼다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/AddProductDao.java`:6-10]
- Caller flow:
  - 예약 확인 화면에서 오른쪽 버튼 tag `1`이면 `executeAddCart()`, 왼쪽 버튼 tag `0`이면 `executeAddProduct()`를 호출한다. 둘 다 PNR을 `hidPnrNo`로 보낸다. [source: `analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java`:250-265,320-375]
  - `dao_add_cart` 성공 시 PNR 배열을 `BasketTicketActivity`로 넘긴다. 연계 예약이면 두 번째 예약도 추가한다. [source: `analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java`:442-454]
  - `dao_add_product` 성공 시 `ExtraProductWebViewActivity`로 이동하며 `WEB_POST_URL=PRODUCT_URL`, `WEB_POST_PARAMETER=pnrNo=<hidPnrNo>`를 넣는다. [source: `analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java`:456-463]
- External handoff:
  - `PRODUCT_URL`은 `webHost + /ebizprd/EbizPrdSrvcListView.do`, post data prefix는 `pnrNo=`다. [source: `analysis/jadx/sources/K4/g.java`:60-66,107-109]

### 2. 장바구니 조회

- Endpoint: `POST /classes/com.korail.mobile.cart.showCartList`
- Request fields: `Device`, `Version`, `Key`, `pnrNo`, `addSrvReqNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartService.java`:15-17]
- Request class: `CartListDao.CartListRequest`
  - `pnrNo`
  - `addSrvReqNo`
  - `getPnrNo()`는 null이면 빈 문자열을 반환한다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartListDao.java`:273-295]
- Response class: `CartListDao.CartListResponse`
  - 공통 `BaseResponse` 필드
  - `cart_infos.cart_info: List<CartInfo>`
  - `CartInfo.addSrvDvCd`, `coptEntRsvNo`
  - `CartInfo.h_add_srv_mrk_ent_id`, `h_add_srv_mrk_ent_nm`
  - `CartInfo.h_cust_no`, `h_dpt_dt`, `h_filler`, `h_fld_stl_dv`
  - `CartInfo.h_gd_nm`, `h_item_dv_cd`, `h_item_dv_nm`, `h_item_sqno`
  - `CartInfo.h_jrny_sqno`, `h_jrny_tp_cd`, `h_lump_stl_tgt_no`
  - `CartInfo.h_pnr_no`, `h_rcvd_amt`, `h_rsv_rcp_dt`, `h_spvs_rs_stn_cd`
  - `CartInfo.h_stl_extns_tno`, `h_stl_lmt_tm`, `h_stl_mns_allw_val`
  - `CartInfo.h_tk_cnt:int`, `h_vr_rsv_no`
  - `CartInfo.utlClsTm`, `utlStDt`, `utlStTm` [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartListDao.java`:13-151,262-306]
- Caller flow:
  - `BasketTicketActivity`는 빈 request로 전체 장바구니를 조회한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:335-339]
  - 응답 중 `h_item_dv_cd`가 `0`, `3`, 또는 `StbkAcntDao.CHANGE_PASSWORD`인 항목만 화면 목록에 남긴다. 실제 코드값 의미는 APK에서 일부만 UI 이름으로 추정 가능하며 서버 의미는 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:753-768]
  - 각 `CartInfo`는 결제/취소 bundle로 변환되고 `LUMP_STL_TGT_NO`, `H_VR_RSV_NO`, `ADD_SRV_DV_CD`, `COPT_ENT_RSV_NO`, `custMgNo` 등이 이후 MAAS 검증/취소/결제에 쓰인다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:557-606]
  - 결제 fragment `C1270f`는 PNR 기반 조회 후 `CartInfo` 목록으로 통합결제 request를 만들고, `C1271g`는 `addSrvReqNo` 기반 조회를 지원한다. [source: `analysis/jadx/sources/B6/C1270f.java`:119-126,236-244], [source: `analysis/jadx/sources/B6/C1271g.java`:58-65,156-174]
- Validation:
  - 결제 버튼 클릭 시 선택된 항목이 없으면 `cart_select_message` dialog를 띄우고 호출하지 않는다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:706-733]

### 3. MAAS 예약 상태 검증

- Endpoint: `POST /classes/com.korail.mobile.maas.rsvStt.do`
- Request fields: `Device`, `Version`, `Key`, `addSrvDvCd`, `addSrvReqNo`, `coptEntRsvNo`, `lumpStlTgtNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/CartService.java`:19-21]
- Request class: `VerifyMaasStatusDao.VerifyMaasStatusRequest`
  - `addSrvDvCd`
  - `addSrvReqNo`
  - `coptEntRsvNo`
  - `lumpStlTgtNo`
  - `seletedPos:int`는 request field가 아니라 UI 복귀용 내부 상태다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/cart/VerifyMaasStatusDao.java`:11-59]
- Response class: `BaseResponse`.
- Caller flow:
  - 장바구니 결제 전 선택 항목 중 MAAS 상품의 `ADD_SRV_DV_CD`, `H_VR_RSV_NO`, `COPT_ENT_RSV_NO`, `LUMP_STL_TGT_NO`를 comma-join해서 검증한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:490-537]
  - 검증 성공 시 `J0()`로 결제 화면을 연다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:799-802]
  - 오류 응답에서 `h_msg_cd == S198`이면 서버 메시지를 보여주고 목록을 새로 조회한다. `S198`의 실제 의미는 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:806-818]

## AddService

### 1. 부가서비스 예약/취소

- Endpoint: `POST /classes/com.korail.mobile.addService.reserve.do`
- Request fields: `Device`, `Version`, `Key`, `pnrNo`, `jrnySqno`, `saleWctNo`, `saleDt`, `saleSqno`, `jobDvCd`, `addSrvId`, `reqQnty`, `helpSrvTgtCnt`, `rcpSqno`, `cncTgtCnt`, `addSrvReqNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:16-18]
- Request class: `AdditionalServiceDao.AdditionalServiceRequest`
  - `JOB_CODE_NEW = "N"`
  - `JOB_CODE_CANCEL = "C"`
  - `pnrNo`, `jrnySqno`
  - `saleWctNo`, `saleDt`, `saleSqno`
  - `jobDbCd` getter가 service field `jobDvCd`에 매핑된다. 명칭 불일치가 있으나 전달 값은 `getJobDbCd()`다.
  - `addSrvId`, `reqQnty:int`, `helpSrvTgtCnt:int`
  - `rcpSqno:ArrayList<String>`
  - `cncTgtCnt:int`
  - `addSrvReqNo:ArrayList<String>` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AdditionalServiceDao.java`:13-127,151-155]
- Response class: `AdditionalServiceDao.AdditionalServiceResponse`
  - 공통 `BaseResponse` 필드
  - `outrec2: List<OutRec2>`
  - `OutRec2.stlMnsCd` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AdditionalServiceDao.java`:129-149]
- Caller flow:
  - 추가상품 상세 화면 취소는 `jobDbCd="C"`, `cncTgtCnt=1`, `addSrvReqNo=[선택 addSrvReqNo]`, `pnrNo`, `jrnySqno`만 채워 호출한다. [source: `analysis/jadx/sources/com/korail/talk/ui/extraproduct/ExtraProductDetailActivity.java`:85-97]
  - 승차권 반환 화면에서 선택된 추가서비스들을 취소할 때 `jobDbCd="C"`, `jrnySqno="0"`, `cncTgtCnt=선택수`, `addSrvReqNo=list`로 호출한다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java`:318-340]
  - 반환 화면은 응답 `outrec2.stlMnsCd == "13"`이면 Rail Plus 동기화를 호출한다. `"13"`의 서버 의미는 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java`:403-414]
- Validation:
  - 취소 전 UI 선택 상태와 확인 dialog가 존재한다. endpoint의 서버 필수값/취소 가능 상태 검증은 미확인.

### 2. 부가서비스 구매 확정

- Endpoint: `POST /classes/com.korail.mobile.addService.buyConfirm.do`
- Request fields: `Device`, `Version`, `Key`, `addSrvCnt`, `addSrvReqNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:20-22]
- Request class: `DealCarBuyDao.DealCarBuyRequest`
  - `addSrvCnt:int`
  - `addSrvReqNo:ArrayList<String>` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/DealCarBuyDao.java`:10-40]
- Response class: `BaseResponse`.
- Caller flow:
  - 결제 fragment는 장바구니 응답에서 추가서비스 금액과 요청번호 목록을 계산한다. [source: `analysis/jadx/sources/B6/C1270f.java`:148-166], [source: `analysis/jadx/sources/B6/C1271g.java`:77-89]
  - `C1270f`는 결제 버튼 클릭 후 NetFunnel pay action을 거치며, `C1271g`는 통합결제 대상 lump target이 비어 있으면 바로 `buyConfirm`를 호출한다. [source: `analysis/jadx/sources/B6/C1270f.java`:217-233], [source: `analysis/jadx/sources/B6/C1271g.java`:141-152]
  - 결제 성공 후 추가서비스 요청번호가 있으면 다시 `buyConfirm`를 호출한다. [source: `analysis/jadx/sources/B6/C1271g.java`:156-166]

### 3. 부가서비스 예약 목록

- Endpoint: `POST /classes/com.korail.mobile.addService.reserveList.do`
- Request fields: `Device`, `Version`, `Key`, `pnrNo`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:24-26]
- Request class: `ExtraProductListDao.ExtraProductListRequest`
  - `pnrNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/ExtraProductListDao.java`:13-25]
- Response class: `ExtraProductListDao.ExtraProductListResponse`
  - 공통 `BaseResponse` 필드
  - `pnrList: List<ExtraProductInfo>` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/ExtraProductListDao.java`:28-36]
- `ExtraProductInfo` fields:
  - `pnrNo`, `jrnySqno`
  - `dptDt`, `dptTm`, `dptRsStnCd`
  - `arvDt`, `arvTm`, `arvRsStnCd`
  - `addSrvList: List<AddSrvInfo>`; null이면 빈 `ArrayList`로 보정한다. [source: `analysis/jadx/sources/com/korail/talk/network/data/addService/ExtraProductInfo.java`:10-20,122-129]
- `AddSrvInfo` fields:
  - `addSrvDvCd`, `addSrvMrkEntId`, `addSrvMrkEntNm`, `addSrvNm`
  - `addSrvPrgSttCd`, `addSrvReqNo`, `addSrvUtlAmt`
  - `cgPsRefAtclCont`, `coptEntRsvNo`, `imgPath`
  - `leadMsgCont1`, `leadMsgCont2`, `leadTeln`
  - `reqDt`, `reqQnty`, `reservationUrl`, `shopMapImgPath`
  - `spvsRsStnCd`, `spvsRsStnCdNm` [source: `analysis/jadx/sources/com/korail/talk/network/data/addService/ExtraProductInfo.java`:21-120]
- Caller flow:
  - `ExtraProductListActivity`는 PNR로 목록을 조회한다. 응답이 null/empty이면 “추가상품이 존재하지 않는다” dialog를 보여준다. [source: `analysis/jadx/sources/com/korail/talk/ui/extraproduct/ExtraProductListActivity.java`:635-645,698-715]
  - `reservationUrl`이 있으면 앱 내부 webview 대신 `IntegrationWebViewActivity`로 URL을 열고, 없으면 `ExtraProductDetailActivity`로 `AddSrvInfo`, PNR, `jrnySqno`를 넘긴다. [source: `analysis/jadx/sources/com/korail/talk/ui/extraproduct/ExtraProductListActivity.java`:681-695]
  - 승차권 반환 화면도 PNR로 추가서비스 목록을 조회해 반환 대상 목록에 붙인다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/TicketReturnActivity.java`:390-400]

### 4. 도움서비스 고객 신청/조회

- Endpoint: `POST /classes/com.korail.mobile.addSrv.helpSrvCust.do`
- Request fields: `Device`, `Version`, `Key`, `saleWctNo`, `saleDt`, `saleSqno`, `reqCnt`, `reqAddSrvDvCd`, `reqAddRcpSrvCd`, `reqCustNm`, `reqCntcChnCont`, `qryDvCd`, `addSrvDvCd`, `rcpSqno`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:28-30]
- Request class: `HelpSrvCustDao.HelpSrvCustRequest`
  - constants: `A`, `D`
  - `saleWctNo`, `saleDt`, `saleSqno`
  - `reqCnt:int`
  - `reqAddSrvDvCd: List<String>`
  - `reqAddRcpSrvCd: List<String>`
  - `reqCustNm: List<String>`
  - `reqCntcChnCont: List<String>`
  - `qryDvCd`, `addSrvDvCd`, `rcpSqno` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/HelpSrvCustDao.java`:13-122]
- Response class: `HelpSrvCustDao.HelpSrvCustResponse`
  - 공통 `BaseResponse` 필드
  - `reqSpecList: List<ReqSpec>`
  - `ReqSpec.addRcpSrvCd`, `addSrvDvCd`, `custNm`, `custTeln`, `rcpSqno` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/HelpSrvCustDao.java`:124-164]
- Caller flow:
  - 휠체어/도움서비스 화면에서 신청/이력 조회에 사용된다. 호출부는 `WheelchairRequestActivity`, `WheelchairHistoryActivity`에 있다. [source: `analysis/jadx/sources/com/korail/talk/ui/service/wheelchair/WheelchairRequestActivity.java`:81-106], [source: `analysis/jadx/sources/com/korail/talk/ui/service/wheelchair/WheelchairHistoryActivity.java`:161-218]

### 5. 도움서비스 승차권 조회

- Endpoint: `POST /classes/com.korail.mobile.addSrv.helpSrvTk.do`
- Request fields: `Device`, `Version`, `Key`, `saleWctNo`, `saleDt`, `saleSqno`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/AddService.java`:32-34]
- Request class: `HelpSrvTkDao.HelpSrvTkDaoRequest`
  - `saleWctNo`, `saleDt`, `saleSqno` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/HelpSrvTkDao.java`:12-43]
- Response class: `HelpSrvTkDao.HelpSrvTkDaoResponse`
  - 공통 `BaseResponse` 필드
  - `helpSrvList: List<helpSrv>`
  - `helpSrv.addSrvReqNo`, `addSrvSpotCont`, `arvEpctTm`, `jrnyInfo300`, `leadMsgCont`
  - `helpSrv.helpSrvTgtList: List<helpSrvTgt>`
  - `helpSrvTgt.custNm`, `custTeln` [source: `analysis/jadx/sources/com/korail/talk/network/dao/addService/HelpSrvTkDao.java`:45-106]
- Caller flow:
  - `WheelchairConfirmActivity`가 매표정보로 도움서비스 승차권을 조회하고, 응답의 첫 고객 정보를 표시/취소 요청에 활용한다. [source: `analysis/jadx/sources/com/korail/talk/ui/service/wheelchair/WheelchairConfirmActivity.java`:64-88,146-163]

## MAAS 관련 취소 handoff

이 절은 범위 내 `CartService`/장바구니 흐름에서 이어지는 related DAO다. endpoint 자체는 `TicketService`에 선언되어 있다.

- `POST /classes//com.korail.mobile.addService.cancelPay.do`
  - DAO: `MaasCancelDao`
  - Request: `Device`, `Version`, `custMgNo`, `lumpStlTgtNo`
  - Response: `BaseResponse`
  - 장바구니 화면에서 MAAS 서비스 취소 확인 후 호출한다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java`:38-40], [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasCancelDao.java`:11-45], [source: `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java`:689-695]
- `POST /classes/com.korail.mobile.maas.cncFee.do`
  - DAO: `MaasServiceCancelFeeDao`
  - Request: `Device`, `Version`, `Key`, `addSrvReqNo`, `addSrvDvCd`, `coptEntRsvNo`
  - Response: `MaasServiceCancelFeeResponse.cncRetFee`
  - `TicketListActivity.moveToMaasServiceCancel()`이 add service item에서 request를 만든다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java`:46-48], [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`:11-68], [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`:1188-1195]
- `POST /classes/com.korail.mobile.addService.coptCnc.do`
  - DAO: `MaasServiceCancelDao`
  - Request: `Device`, `Version`, `pnrNo`, `cncTgtCnt`, `cncAddSrvReqNo`, `cncRetFee`
  - Response: `BaseResponse`
  - 취소 수수료 응답을 dialog에 표시한 뒤 확인하면 `cncTgtCnt="0001"`, `cncAddSrvReqNo`, `cncRetFee`로 호출한다. 정적 분석상 `pnrNo`는 이 flow에서 별도 set이 보이지 않는다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java`:42-44], [source: `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelDao.java`:11-62], [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`:403-410,1576-1598]

## GifticketService

### 1. 기프티켓 예약

- Endpoint: `POST /classes/com.korail.mobile.gift.gdRsv.do`
- Request fields: `Device`, `Version`, `Key`, `itmCnt`, `mrkAmt_1`, `prnbCnt`, `mbCrdNo_1`, `gdUtlPsNm_1`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketService.java`:13-15]
- Request class: `GifticketBookingDao.GifticketBookingRequest`
  - `itmCnt`
  - `mrkAmt`
  - `prnbCnt`
  - `mbCrdNo`
  - `gdUtlPsNm` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketBookingDao.java`:11-60]
- Response class: `GifticketBookingDao.GifticketBookingResponse`
  - 공통 `BaseResponse` 필드
  - `lumpStlTgtNo`
  - `prsCnqeVal`
  - `rcvdAmt` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketBookingDao.java`:62-81]
- Caller flow:
  - `GifticketBookingActivity`는 “나에게 선물”이면 로그인 회원번호/이름, 아니면 입력된 수신자 정보를 사용한다.
  - 현재 구현은 `itmCnt="1"`, `prnbCnt="1"`, 선택 금액을 `mrkAmt`, 회원번호를 `mbCrdNo`, 이용자명을 `gdUtlPsNm`으로 보낸다. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/gifticket/GifticketBookingActivity.java`:93-106]
  - 성공 시 `lumpStlTgtNo`로 통합결제 request를 만들고 `RECEIVED_AMOUNT=rcvdAmt`를 `PaymentActivity`에 넘긴다. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/gifticket/GifticketBookingActivity.java`:127-135,273-282]
- Validation:
  - 결제 전 회원 인증 endpoint(`MemberCertDao`)를 별도로 호출할 수 있다. 기프티켓 endpoint 자체의 서버 검증 규칙은 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/booking/gifticket/GifticketBookingActivity.java`:109-124,273-279]

### 2. 기프티켓 목록

- Endpoint: `POST /classes/com.korail.mobile.gift.gdLst.do`
- Request fields: `Device`, `Version`, `Key`, `qryDvCd`, `qryVal`, `abrdDtFrom`, `abrdDtTo`, `usePsbFlg`, `qryNumNext`, `fllwQryFlg`, `trnOprBzDvCd`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketService.java`:17-19]
- Request class: `GifticketListDao.GifticketListRequest`
  - `qryDvCd`, `qryVal`
  - `abrdDtFrom`, `abrdDtTo`
  - `usePsbFlg`
  - `qryNumNext`, `fllwQryFlg`
  - `trnOprBzDvCd` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketListDao.java`:79-155]
- Response class: `GifticketListDao.GifticketListResponse`
  - 공통 `BaseResponse` 필드
  - `gdList: List<GifticketInfo>`
  - `qryCnt`
  - `qryNumNext`
  - getter는 `gdList`만 노출한다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketListDao.java`:157-168]
- `GifticketInfo` fields:
  - `intgCustNm1`, `intgCustNm2`
  - `nowPontValNum`, `usePontValNum`
  - `rcvDt`, `retDt`, `retTm`
  - `retAmt`, `txnAmt`
  - `tkId`, `useClsDt`, `usePsbFlg` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketListDao.java`:13-77]
- Caller flow:
  - 받은 기프티켓 fragment는 `qryDvCd="C"`, `qryVal="E"`, `abrdDtFrom="20210101"`, `abrdDtTo="20211230"`, `usePsbFlg=""`로 조회한다. [source: `analysis/jadx/sources/B6/b.java`:265-274]
  - 보낸 기프티켓 fragment는 `qryDvCd="A"`, 나머지는 유사한 값으로 조회한다. [source: `analysis/jadx/sources/B6/f.java`:178-188]
  - 날짜 범위가 코드에 하드코딩되어 있으나 실제 운영 의도는 APK만으로 미확인이다.

### 3. 기프티켓 사용 내역

- Endpoint: `POST /classes/com.korail.mobile.gift.gdUseSpec.do`
- Request fields: `Device`, `Version`, `Key`, `tkId`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketService.java`:21-23]
- Request class: `GifticketHistoryDao.GifticketHistoryRequest`
  - `tkId`
  - `qryNum` 필드는 request class에 있으나 service method에는 전달되지 않는다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`:49-67,82-86]
- Response class: `GifticketHistoryDao.GifticketHistoryResponse`
  - 공통 `BaseResponse` 필드
  - `fllwQryFlg`
  - `qryCnt`
  - `txnList: List<GifticketDetailData>`
  - `GifticketDetailData.dataDvCd`, `rmkCont`, `stlNo`, `stlSqno`, `txnAmt`, `txnDt` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`:13-47,69-80]
- Caller flow:
  - 상세 화면은 intent의 `GIFTICKET_ID`를 `tkId`로 보내고 `txnList`를 표시한다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/history/gifticket/GifticketHistoryDetailActivity.java`:101-107,127-145]

### 4. 기프티켓 반환

- Endpoint: `POST /classes/com.korail.mobile.gift.gdRet.do`
- Request fields: `Device`, `Version`, `Key`, `tkId`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketService.java`:25-27]
- Request class: `GifticketReturnDao.GifticketReturnRequest`
  - `tkId` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`:11-24]
- Response class: `GifticketReturnDao.GifticketReturnResponse`
  - 공통 `BaseResponse` 필드
  - `prsFlg` [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`:26-35]
- Caller flow:
  - 받은 기프티켓 fragment에서 선택한 `tkId`로 반환 요청을 만들고, 성공 시 반환 완료 dialog를 보여준다. [source: `analysis/jadx/sources/B6/b.java`:217-224,295-308]
- Static discrepancy:
  - `GifticketReturnDao.getId()`가 정적 분석상 `dao_gifticket_reservation`을 반환한다. 그러나 caller는 `dao_gifticket_return`을 기다린다. 실제 앱에서 정상 동작한다면 디컴파일/난독화 영향일 가능성이 있으나, APK 소스 기준으로는 불일치가 존재한다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`:37-47], [source: `analysis/jadx/sources/B6/b.java`:295-302]

## GiftInfoService

### 승차권 선물/전달

- Endpoint: `POST /classes/com.korail.mobile.giftInfo.GiftSend`
- Request fields: `Device`, `Version`, `Key`, `hidAcepPsNm`, `hidAcepPsTeln`, `hidPbpAcepPsMbFlg`, `hidPbpAcepPsCustMgNo`, `hidPnrNo`, `hidTotNewStlAmt`, `hidRsvChgNo`, `hidInfoInpDvCd`, `hidSaleCnt`, `hidAcepPwd`, plus dynamic `FieldMap`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/giftInfo/GiftInfoService.java`:12-14]
- Request class: `TicketPresentDao.TicketPresentRequest`
  - constants: `DEFAULT_HID_INFO_INP_DV_CD="O"`, `KAKAO_HID_INFO_INP_DV_CD="K"`, `SMS_HID_INFO_INP_DV_CD="S"`
  - `hidAcepPsNm`, `hidAcepPsTeln`, `hidAcepPwd`
  - `hidInfoInpDvCd`
  - `hidPbpAcepPsCustMgNo`, `hidPbpAcepPsMbFlg`
  - `hidPnrNo`, `hidRsvChgNo`, `hidSaleCnt`, `hidTotNewStlAmt`
  - `ticketPresentParams: Map<String,String>` [source: `analysis/jadx/sources/com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`:12-16,59-159]
- Dynamic `FieldMap` keys:
  - `hidSaleWctNo`, `hidSaleDt`, `hidSaleSqno`, `hidtkRetPwd`
  - index가 `0`이면 suffix 없이, 그 외에는 key 뒤에 index를 붙인다. 예: `hidSaleWctNo2`, `hidtkRetPwd2`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`:17-57]
- Response class: `TicketPresentDao.TicketPresentResponse`
  - 공통 `BaseResponse` 필드
  - `chgePbpRsvNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`:161-169]
- Caller flow:
  - `TicketDeliveryListActivity`가 기본 request와 판매번호/반환비밀번호 FieldMap을 구성한다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/delivery/TicketDeliveryListActivity.java`:314-321]
  - `DeliveryActivity`는 전달 방식에 따라 request를 보강한다.
  - 기타 전달은 전달 방식 코드(`str`), 이름, 전화번호를 직접 넣고 회원 flag `N`, 회원관리번호 빈 값으로 보낸다. [source: `analysis/jadx/sources/com/korail/talk/ui/delivery/DeliveryActivity.java`:171-181]
  - 회원 전달은 `hidInfoInpDvCd="O"`, 회원 flag `Y`, 회원관리번호를 채운다. [source: `analysis/jadx/sources/com/korail/talk/ui/delivery/DeliveryActivity.java`:184-194]
  - 비회원 전달은 `hidInfoInpDvCd="O"`, 회원 flag `N`, 수락 비밀번호 `hidAcepPwd`를 채운다. [source: `analysis/jadx/sources/com/korail/talk/ui/delivery/DeliveryActivity.java`:197-208]
  - 성공 시 Kakao 방식(`hidInfoInpDvCd="K"`) 여부에 따라 완료 dialog 내용을 바꾼다. [source: `analysis/jadx/sources/com/korail/talk/ui/delivery/DeliveryActivity.java`:225-243]
- External handoff:
  - Kakao link result 관련 비동기 처리 코드가 같은 activity에 존재하나, `GiftSend` endpoint 자체의 외부 서버 handoff 상세는 이 범위에서 확인되지 않는다.

## BusReservationService 및 버스 예약/취소

### 1. 버스/리무진 목록 조회

- Endpoint: `POST /classes/com.korail.mobile.lmu.scdlQry.do`
- Request fields: `Device`, `Version`, `Key`, `dptDt`, `dptRsStnCd`, `arvRsStnCd`, `tmGpCd`, `psrmClCd`, `dptTm`, `trnNo`, `seatAttCd`, `rsvSaleDvCd`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`:27-29]
- Request class: `BusReservationListDao.BusInquiryRequest`
  - `dptDt`, `dptRsStnCd`, `arvRsStnCd`, `dptTm`
  - `trnGpCd`
  - `psrmClCd`
  - `trnNo`
  - `seatAttCd`
  - `rsvSaleDvCd`
  - `mReservationResponse` local field [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationListDao.java`:12-106]
- Response class: `BusReservationListDao.BusInquiryResponse`
  - 공통 `BaseResponse` 필드
  - `fllwPgExt`
  - `lgtmShtmDvCd`
  - `trainList: ArrayList<BusList>`
  - `BusList.arvDt`, `arvRsStnCd`, `arvStnRunOrdr`, `arvTm`
  - `BusList.chtnDvCd`
  - `BusList.dptDt`, `dptRsStnCd`, `dptStnRunOrdr`, `dptTm`
  - `BusList.gnrmRestSeatNum`, `sprmRestSeatNum`, `restFresNum`, `restStndNum`
  - `BusList.ocurDlayTnum`, `runDt`, `stlbTrnClsfCd`
  - `BusList.trnGpCd`, `trnNo`, `trnOrdNo`, `ymsAplFlg` [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationListDao.java`:108-325]
- Caller flow:
  - `LimousineListActivity`가 intent의 선택일/시간/조회 bundle/승객수를 받아 request를 구성한다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineListActivity.java`:267-281]
  - 조회 request에는 선택된 날짜, 출발/도착역, 열차그룹, 객실등급, 출발시각, 열차번호, 좌석속성, 예약판매구분을 그대로 넣는다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineListActivity.java`:221-235]
  - 응답 `trainList`가 null이면 빈 목록으로 대체하고 adapter에 연결한다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineListActivity.java`:160-170]
- Static note:
  - `BusReservationListDao.executeDao()`는 동일한 `reservationList()`를 한 번 호출하고 결과를 버린 뒤 다시 호출해 반환한다. 실제 서버에는 중복 요청이 나갈 수 있는 코드 형태다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationListDao.java`:327-333]

### 2. 버스/리무진 좌석 조회

- Endpoint: `POST /classes/com.korail.mobile.lms.TResidualSeatsResearch.do`
- Request fields: `Device`, `Version`, `Key`, `trnClsfCd`, `trnGpCd`, `runDt`, `trnNo`, `srcarNo`, `psrmClCd`, `dptRsStnCd`, `arvRsStnCd`, `seatAttCd`, `dptStnRunOrdr`, `arvStnRunOrdr`, `totPsgCnt`, `gdNo`, `isArrow`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`:31-33]
- Request class: `BusReservationSeatListDao.BusSeatListRequest`
  - `trnClsfCd`, `trnGpCd`, `runDt`, `trnNo`
  - `srcarNo`, `psrmClCd`
  - `dptRsStnCd`, `arvRsStnCd`
  - `seatAttCd`
  - `dptStnRunOrdr`, `arvStnRunOrdr`
  - `totPsgCnt`
  - `gdNo`
  - `isArrow:boolean`
  - `mReservationResponse` local field [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`:12-159]
- Response class: `BusReservationSeatListDao.SeatListResponse`
  - 공통 `BaseResponse` 필드
  - `car_tp_cd`, `scar_no`, `seat_ary_cd`, `up_dn_dv_cd`
  - `seatList: ArrayList<SeatList>`
  - `SeatList.dir_seat_att_cd`, `etc_seat_att_cd`, `rq_seat_att_cd`
  - `SeatList.intg_msg`, `intg_msg_cd`
  - `SeatList.sale_psb_flg`, `seat_no`, `seat_spec`, `sqr_no`, `vz_msg_dv_cd`
  - local UI flags: `isDisable`, `isSelected` [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`:161-268]
- Caller flow:
  - `LimousineSelectSeatActivity`는 `trnClsfCd="98"`, `srcarNo="0001"`, `gdNo=""`, `isArrow=false`를 고정하고 나머지는 목록 선택/intent 값으로 채운다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`:298-317]
  - 결제 버튼은 선택 좌석 수(`f29445G`)가 승객수(`f29458s`)와 같을 때만 예약을 진행한다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`:391-397]
  - 버스 예약 생성은 `BusReservationService`가 아니라 일반 `LReservationDao`를 통해 `ReservationRequest`를 구성한다. `OJrny`에 `trnClsfCd="98"`, `trnGpCd=LIMOUSINE`, 출발역 `0501`, 선택 좌석 번호들을 넣는다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`:341-372]

### 3. 버스 예약 취소 확인 / 실제 취소

- `BusReservationService`에는 `POST /classes/com.korail.mobile.reservationCancel.ReservationCancelChk` 선언이 있다. 필드는 `Device`, `Version`, `Key`, `txtPnrNo`, `jrnySqno`, `jrnyCnt`, `hidRsvChgNo`다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`:19-21]
- 실제 DAO 호출은 `RsvCancelCheckDao`가 `ReservationCancelService.reservationCancelCheck()`로 수행한다. request class 필드는 `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo`이고 response는 `BaseResponse`다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelCheckDao.java`:11-57], [source: `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java`:19-21]
- 실제 취소 endpoint는 `ReservationCancelService`의 `POST /classes/com.korail.mobile.reservationCancel.ReservationCancel`이며, `BusReservationService`에는 선언되어 있지 않다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java`:15-17]
- Caller flow:
  - 리무진 좌석 선택 화면은 예약 후 `onResume()`에서 `RsvCancelDao`를 호출해 예약 취소를 수행하고, 성공하면 곧바로 `RsvCancelCheckDao`로 취소 확인을 호출한다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`:319-339,439-467]
  - `RsvCancelDao` request는 `txtPnrNo`, `txtJrnyCnt`, `txtJrnySqno="0001"`, `hidRsvChgNo="000"`로 구성된다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineSelectSeatActivity.java`:319-327]

### 4. 예약 변경 선언

- `BusReservationService`에는 `POST /classes/com.korail.mobile.reservation.reservationChange.do` 선언이 있다. 필드는 `Device`, `Version`, `Key`, `pnrNo`, `chgTno`, `totPrnb`, `stndFlg`, `evntWctFlg`, `wctHndgCncDvCd`, `lrgCrgFlg`, `psgCnt`, 그리고 5개 `FieldMap`이다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/certification/BusReservationService.java`:23-25]
- 실제 `ReservationChangeDao`는 `ReservationCancelService.reservationChange()`를 사용한다. [source: `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`:162-166]
- Response class: `ReservationChangeDao.ReservationChangeResponse`
  - 공통 `BaseResponse` 필드
  - `jrnyList: List<JrnyInfo>`
  - `JrnyInfo.lumpStlTgtNo` [source: `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`:17-26,151-160]
- Dynamic FieldMap key rules:
  - `RJrny`: `jrnyCnt`, `jrnySqno_#`, `jrnyTpCd_#`, `trnNo_#`, `runDt_#`, `stlbTrnClsfCd_#`, `trnGpCd_#`, `dptDt_#`, `dptTm_#`, `dptRsStnCd_#`, `dptStnConsOrdr_#`, `dptStnRunOrdr_#`, `arvRsStnCd_#`, `arvStnConsOrdr_#`, `arvStnRunOrdr_#`, `arvDt_#`, `arvTm_#`, `chgFlg_#`. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RJrny.java`:6-97]
  - `RSrcar`: `scarCnt_#`, `srcarCnt_#`, `scarNo_#_#`, `seatNo_#_#`. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RSrcar.java`:6-26]
  - `RSeat`: `seatCnt_#`, `seatPsrmClCd_#_#`, `rqSeatAttCd_#_#`, `dirSeatAttCd_#_#`, `etcSeatAttCd_#_#`, `locSeatAttCd_#_#`, `roomClsfCd_#_#`, `smkSeatAttCd_#_#`. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RSeat.java`:6-47]
  - `RPsg`: `psgCnt`, `psgInfoPerPrnb_#`, `psgTpDvCd_#`. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RPsg.java`:6-21]
  - `RDscp`: `dscpCnt_#`, `dcntKndCd_#_#`, `dscpNo_#_#`, 지연 원권 관련 `dlayOgtk*` key. [source: `analysis/jadx/sources/com/korail/talk/network/data/reservation/RDscp.java`:6-45]
- Caller flow:
  - `ReservedTicketChangeActivity`가 `ReservationChangeDao`를 실행하고 응답의 첫 `lumpStlTgtNo`로 통합결제를 이어간다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java`:121-125,170-193]
  - request builder는 기존 예약의 여정/좌석 정보를 복사하고 성인/어린이/동반유아/경로/장애 할인별 passenger/discount map을 만든다. [source: `analysis/jadx/sources/w4/a.java`:120-241]

## IndependentService

### 로그인 팝업 확인 기록

- Endpoint: `POST /classes/com.korail.mobile.login.poppCfmRec.do`
- Request fields: `Device`, `Version`, `Key`, plus dynamic `FieldMap`. [source: `analysis/jadx/sources/com/korail/talk/network/dao/independent/IndependentService.java`:11-14]
- Response class: `BaseResponse`.
- Caller flow:
  - `S4.C0811k.a` AsyncTask가 `ExecuteDao().getService(IndependentService.class)`로 service를 직접 얻어 호출한다. [source: `analysis/jadx/sources/S4/C0811k.java`:35-54]
  - `FieldMap`의 `notiTpCd`가 `MC`, `MM`, `MS` 중 하나일 때만 서버에 보낸다. 그 외 값이면 아무 호출도 하지 않는다. [source: `analysis/jadx/sources/S4/C0811k.java`:49-53]
  - 이 direct call은 DAO wrapper/getId가 없고 loading/error handling도 일반 `BaseDao` 흐름을 타지 않는다.
- Unknown:
  - `FieldMap` 전체 key set은 호출부에서 전달되는 map에 의존한다. 이 파일 범위에서 `notiTpCd` 외 key 의미는 확인되지 않는다.

## 외부 WebView/Handoff 요약

- 상품/부가서비스 web 구매: `ExtraProductWebViewActivity` 또는 `IntegrationWebViewActivity`로 `PRODUCT_URL` + `pnrNo=<PNR>`를 넘긴다. [source: `analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java`:456-463], [source: `analysis/jadx/sources/K4/g.java`:60-66,107-109]
- 추가서비스 목록 item의 `reservationUrl`이 있으면 해당 URL을 `IntegrationWebViewActivity`에 `WEB_POST_URL`로 전달한다. 실제 URL/서버 데이터는 응답값이라 미확인이다. [source: `analysis/jadx/sources/com/korail/talk/ui/extraproduct/ExtraProductListActivity.java`:681-688]
- 상품 voucher: `VOUCHER_URL`에 `txtVrRsvNo=<예약번호>`를 붙여 webview로 이동한다. [source: `analysis/jadx/sources/com/korail/talk/ui/menu/tripbooking/TripBookingDetailActivity.java`:171-175]
- MAAS 상세 URL: `rsvSpecUrl`이 있으면 `IntegrationWebViewActivity`에 `WEB_GET_URL`, `IS_MAAS_URL=true`로 연다. [source: `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`:1197-1205]
- 리무진 안내/수수료 안내는 web constants를 사용해 `IntegrationWebViewActivity`로 넘기지만, 예약/취소 API 본문 데이터와는 별도다. [source: `analysis/jadx/sources/com/korail/talk/ui/limousine/LimousineListActivity.java`:250-264]

## 정적 분석 한계

- 실제 서버 응답 예시, 오류 코드 의미, enum 값 의미는 APK 안에서 매핑되는 일부 UI 분기 외에는 확인되지 않는다.
- Retrofit/Gson 매핑은 필드명 기반으로 보이며, 별도 `@c` annotation이 없는 대부분의 inner class는 Java field name이 JSON key로 쓰인다고 추정된다. 서버의 실제 key alias는 미확인이다.
- `BusReservationService`의 취소확인/예약변경 선언은 존재하지만, 실제 DAO는 `ReservationCancelService`를 사용한다. 따라서 문서에는 “서비스 선언”과 “실제 caller flow”를 분리했다.
- `GifticketReturnDao.getId()`와 caller가 기대하는 id가 불일치한다. 정적 분석 결과로 기록하되, 실제 런타임 동작 여부는 확인하지 않았다.
