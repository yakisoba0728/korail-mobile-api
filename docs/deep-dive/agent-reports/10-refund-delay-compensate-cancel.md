# 10. 환불/지연/보상/예약취소 정적 분석

분석 범위는 `RefundService`, `DelayService`, `CompensateService`, `ReservationCancelService`와 관련 DAO, 응답 모델, UI Activity/Fragment이다. 모든 내용은 로컬 JADX 산출물 기준 정적 분석이며, 운영 서버 호출/동적 캡처를 하지 않았으므로 실제 서버 응답 예시, 서버 내부 판정, 운영 feature flag, 런타임 NetFunnel 대기 결과는 미확인이다. 공통 요청 필드는 `BaseRequest` 생성자가 `Device=AD`, `Version=250601003`, `Key=korail1234567890`로 채운다 (`analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:7-18`). 공통 응답 필드는 `BaseResponse`의 `strResult`, `h_msg_cd`, `h_msg_txt`이다 (`analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:7-30`).

## 1. 공통 실행/오류 처리

- DAO 실행은 `BaseDaoHelper.HttpTask`가 백그라운드에서 `executeDao()`를 호출하고, 성공/실패를 `onIntegrationResult()`로 전달한다 (`analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:41-47`, `analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:101-109`).
- HTTP 403 Forbidden이고 `DynaPath-Result` 헤더가 음수이면 응답 body JSON의 `message`를 `macroShowDialog`로 저장한다 (`analysis/jadx/sources/com/korail/talk/network/BaseDaoHelper.java:54-91`). 이후 `BaseActivity.onIntegrationResult()`가 이 메시지를 다이얼로그로 표시한다 (`analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:632-634`).
- `strResult=FAIL` 또는 `h_msg_cd=WRC000288`는 일반 오류로 처리되고, `h_msg_txt`가 없으면 `"알수없는 오류가 발생하였습니다."`가 사용된다 (`analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:620-627`). 오류 다이얼로그는 `isNotShowDialog()`와 `getErrorMsgCdNotShowDialog()`에 의해 생략될 수 있다 (`analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:326-344`).
- `WRG000000`은 지연/운행중지 보상 목록 조회 DAO에서 숨김 오류 코드로 등록된다 (`analysis/jadx/sources/G6/C5683c.java:74-83`, `analysis/jadx/sources/G6/C5681a.java:58-67`).

## 2. NetFunnel

- NetFunnel 기본 서버는 앱 시작 시 `nf.letskorail.com:443`, service id `service_1`, 기본 action `act_8`로 설정된다 (`analysis/jadx/sources/com/korail/talk/application/KTApplication.java:78-85`). 상수로는 환불 `act_22`, 예약내역 `act_21`, 예약 `act_14`, 결제 `act_18` 등이 존재한다 (`analysis/jadx/sources/K4/g.java:43-51`).
- 이 범위에서 실제로 확인되는 NetFunnel 적용은 예약내역 조회 화면이다. `ReservedTicketActivity`가 `NETFUNNEL_ACTION_RESERVED_ID(act_21)`로 `BEGIN()`을 호출하고, 예약내역 DAO에 `NetfunnelDao`를 연결한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:303-307`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:545-554`).
- 환불 action 상수 `act_22`는 존재하지만, 본 범위의 `RefundDao`, `DelayRefundDao`, `CompensateRefundDao`, `ReservationCancelDao` 호출부에서 `act_22`로 `BEGIN()` 또는 `setNetfunnelDao()`를 연결하는 코드는 확인되지 않았다. 따라서 정적 분석상 "상수 존재"까지만 확정하고, 환불 실호출의 NetFunnel 적용 여부는 미확인으로 둔다 (`analysis/jadx/sources/K4/g.java:47`, `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:104-106`).

## 3. RefundService: 일반/온라인 환불

### 3.1 엔드포인트와 요청 필드

| 흐름 | HTTP path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|
| 온라인 환불 검증 | `/classes/com.korail.mobile.refunds.verifyOnlineRefunds` | `verifyOnlineRefunds` | `Device`, `Version`, `Key`, `retNo1`, `retNo2`, `retNo3`, `retNo4`, `strName` | `RefundVerifyTicketResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:31-33`) |
| 환불 수수료 조회 | `/classes/com.korail.mobile.refunds.CommissionView` | `getTicketCommission` | `Device`, `Version`, `Key`, `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_comp_nm`, `h_comp_cert_no` | `RefundCommissionResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:19-21`) |
| 티켓 상세 조회 | `/classes/com.korail.mobile.refunds.SelTicketInfo` | `getTicketDetail` | `Device`, `Version`, `Key`, `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_purchase_history` | `TicketDetailResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:23-25`) |
| 일반 티켓 반환 | `/classes/com.korail.mobile.refunds.RefundsRequest` | `returnTicket` | `Device`, `Version`, `Key`, `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_sale_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_mlg_stl`, `tk_ret_tms_dv_cd`, `trnNo`, `pbpAcepTgtFlg`, `latitude`, `longitude` | `RefundResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:27-29`) |
| 온라인 환불 실행 | `/classes/com.korail.mobile.refunds.executeOnlineRefunds` | `executeOnlineRefunds` | `Device`, `Version`, `Key`, `pnrNo`, `tkKndCd`, `retDvCd`, `retRsnCd`, `ogtkSaleDt`, `ogtkSaleWctNo`, `ogtkSaleSqno`, `ogtkRetPwd`, `retAmt`, `retFee`, `custTeln`, `acepCustNm` | `RefundExecuteTicketRefundResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java:15-17`) |

### 3.2 응답 클래스/필드

- `RefundCommissionResponse`는 `h_msg_cd2`, `h_msg_txt2`, `prg_psb_flg`, `ret_amt`, `ret_fee`, `tk_ret_tms_dv_cd`, `use_psb_mlg_num`을 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundCommissionDao.java:71-109`).
- `RefundDao.RefundResponse`는 `stlList`를 갖고, 각 항목은 `stl_mns_cd`만 getter로 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundDao.java:118-138`).
- `RefundVerifyTicketResponse`는 `orgtkinfo_list`, `poppMsg`, `rcvd_amt`, `ret_amt`, `ret_fee`를 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java:64-70`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java:192-210`). 원권 항목은 `prnNo`, `tk_knd_cd`, `ret_dv_cd`, `ret_rsn_cd`, 원권 발매/반환 키, 여정 목록을 제공한다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java:117-166`).
- `RefundExecuteTicketRefundResponse`는 `h_ret_dv_cd`만 추가 필드로 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundExecuteTicketRefundDao.java:125-133`).
- `TicketDetailResponse`는 환불/지연/부가서비스 판단에 쓰이는 `h_pnr_no`, `h_orgtk_*`, `h_ret_flg`, `h_dlay_flg`, `h_dlay_tk_flg`, `h_pbp_acep_tgt_flg`, `retPsbFlg`, `mlgSaveFlg`, `addSrvFlg`, `addSrvCancel`, `ticket_infos`, `dtlList` 등을 갖는다 (`analysis/jadx/sources/com/korail/talk/network/dao/refund/TicketDetailDao.java:227-280`, `analysis/jadx/sources/com/korail/talk/network/dao/refund/TicketDetailDao.java:341-494`).

### 3.3 일반 티켓 반환 흐름과 규칙

- 반환 버튼 클릭 시 수수료 응답 목록을 초기화하고, 선택된 티켓이 있으면 수수료 조회를 순차 실행한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:416-431`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:343-360`).
- 수수료 조회 요청은 `TicketDetailResponse`의 `h_orgtk_wct_no`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, 동반자명/생년값 `h_compa_nm`, `h_compa_brth`를 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:349-358`).
- 마지막 수수료 응답의 `tk_ret_tms_dv_cd`가 `BEFORE_DEPARTURE`이면 바로 확인 다이얼로그로 가고, 그렇지 않으면 위치 권한/GPS 확인 뒤 반환 확인을 진행한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:472-490`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:111-140`).
- 출발 전 또는 티켓 종류 `h_tk_knd_cd=13`이면 일반 확인 다이얼로그를 사용하고, 그 외에는 체크박스 동의가 있는 확인 다이얼로그를 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:271-295`).
- 수수료 응답 코드 `WRT800078`은 재구매/반환 선택 다이얼로그로 분기하고, `WRT800179`는 취소/반환완료 선택 다이얼로그로 분기한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:298-315`). 티켓 목록 화면도 동일 코드들을 별도 분기한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1498-1518`).
- `prg_psb_flg=M`이고 `use_psb_mlg_num`이 전체 수수료 이상이면 마일리지 수수료 사용 여부를 다시 묻고, 사용 선택 시 `h_mlg_stl=Y`, 미사용 또는 조건 불충족 시 `h_mlg_stl=N`으로 `RefundsRequest`를 보낸다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:180-199`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:203-229`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:362-404`).
- 실제 `RefundRequest`는 PNR, 원권 발매일/창구/일련번호/반환비밀번호, `tk_ret_tms_dv_cd`, 열차번호, `h_pbp_acep_tgt_flg`, 위도/경도를 담는다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:370-404`).
- 반환 응답 `stlList` 안에 결제수단 코드 `13`이 있으면 RailPlus 동기화를 수행한다. 성공 콜백과 일부 오류 콜백 모두에서 이 동기화가 보인다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:493-525`, `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1521-1538`).

### 3.4 온라인/오프라인 반환번호 환불 흐름

- `OfflineTicketReturnActivity`는 안내 fragment, 입력 fragment, 요청 fragment를 전환하는 컨테이너 역할을 한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/offline/OfflineTicketReturnActivity.java:15-60`).
- 입력 fragment는 반환번호 4분할 필드와 신청자명/전화번호가 모두 채워져야 버튼을 활성화하고, 확인 후 `verifyOnlineRefunds`를 호출한다 (`analysis/jadx/sources/S5/c.java:64-74`, `analysis/jadx/sources/S5/c.java:76-95`, `analysis/jadx/sources/S5/c.java:172-182`).
- 검증 응답에 `poppMsg`가 있으면 메시지 다이얼로그를 표시한 뒤 요청 fragment로 이동하고, 없으면 바로 요청 fragment로 이동한다 (`analysis/jadx/sources/S5/c.java:193-208`).
- 요청 fragment는 검증 응답의 원권 정보와 금액을 화면에 표시하고, 동의 체크박스가 켜져야 실행 버튼을 활성화한다 (`analysis/jadx/sources/S5/h.java:50-98`, `analysis/jadx/sources/S5/h.java:160-175`).
- `executeOnlineRefunds` 요청은 검증 응답의 원권 발매/반환 키, PNR, 티켓종류, 반환구분, 반환사유, 반환금액/수수료와 입력 fragment에서 받은 신청자명/전화번호를 사용한다 (`analysis/jadx/sources/S5/h.java:111-127`).
- 실행 응답의 `h_ret_dv_cd`가 `"02"`이면 완료 메시지, 그 외에는 성공 메시지로 분기한다 (`analysis/jadx/sources/S5/h.java:183-193`).

## 4. DelayService: 지연 보상/증명/현금환불

### 4.1 엔드포인트와 요청 필드

| 흐름 | HTTP path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|
| 지연증명 발급 | `/classes/com.korail.mobile.dlay.athnIsu.do` | `athnIsu` | `Device`, `Version`, `Key`, `ogtkSaleWctNo`, `ogtkSaleDd`, `ogtkSaleSqno`, `ogtkRetPwd`, `runDt`, `trnNo` | `DelayCertificateResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:18-20`) |
| 지연 현금/계좌 환불 | `/classes/com.korail.mobile.dlay.cashRfn.do` | `cashRfn` | `Device`, `Version`, `Key`, `dmnPrsDvCd`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`, `dptnBankCd`, `dptnAcntNo`, `custNm`, `custTeln`, `rmk1Cont` | `CashRfnResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:22-24`) |
| 지연 반환 영수증 | `/classes/com.korail.mobile.dlay.pymtRcet.do` | `dealyReturnReceipt` | `Device`, `Version`, `Key`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd` | `DelayReturnReceiptResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:26-28`) |
| 입금은행 목록 | `/classes/com.korail.mobile.dlay.dptnBank.do` | `dptnBank` | `Device`, `Version`, `Key` | `DptnBankResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:30-32`) |
| 지연 PNR 조회 | `/classes/com.korail.mobile.delay.pnrQry.do` | `executeDelayPNRQuery` | `Device`, `Version`, `Key`, `jobDvCd`, `pnrCnt`, `pnrNo[]`, `ogtkWctNo[]` | `DelayPNRQueryResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:38-40`) |
| 지연 PNR 접수 | `/classes/com.korail.mobile.delay.acptPrs.do` | `executeDelayPNRAccept` | `Device`, `Version`, `Key`, `jobDvCd`, `pnrCnt`, `pnrNo[]`, `ogtkWctNo[]` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:34-36`) |
| 지연 보상 목록 | `/classes/com.korail.mobile.delay.ticketList.do` | `executeDelayRefundList` | `Device`, `Version`, `Key`, `nowPgNo`, `dptDtFrom`, `dptDtTo` | `DelayRefundListResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:50-52`) |
| 지연 보상 상세/검증 | `/classes/com.korail.mobile.delay.ticketDetail.do` | `executeDelayRefundDetail` | `Device`, `Version`, `Key`, `tkCnt`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:46-48`) |
| 지연 보상 실행 | `/classes/com.korail.mobile.delay.ticketReturn.do` | `executeDelayRefund` | `Device`, `Version`, `Key`, `dlayFarePymtMtdCd`, `tkCnt`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayService.java:42-44`) |

### 4.2 응답 클래스/필드

- 지연/운행중지 목록 공통 응답 `network.response.delay.RefundResponse`는 `ticketList`와 `whlPgNum`을 갖는다 (`analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:9-12`, `analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:156-162`).
- `TicketList`는 `saleWctNo`, `saleDd`, `saleSqNo`, `tkRetPwd`, 역/일자/열차/금액 필드, `stlList`, `trnStpRsStnCd`, `jrnyStpTkFlg`, `trnRunStpCpstAmt`, `dlayFare`, `rcvdAmt` 등을 노출한다 (`analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:24-47`, `analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:51-153`).
- `TicketList.getReturnNo()`는 `saleWctNo + saleDd + 정수화된 saleSqNo + tkRetPwd`를 조합한다 (`analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:99-101`).
- `DelayCertificateResponse`는 `dlayList`를 갖고, 각 `DelayInfo`는 `runDay`, `runDt`, `trnNo`, 출도착역, `dlayArvFlg`, `trnDlayTm`을 제공한다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayCertificateDao.java:72-127`).
- `CashRfnResponse`는 `rfnAmt`를 추가로 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/CashRfnDao.java:116-124`). `DptnBankResponse`는 `dptnBankCd`, `dptnBankNm` 목록을 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DptnBankDao.java:13-37`). `DelayReturnReceiptResponse`는 `dlayFarePymtMtdNm`, `dlayFareRetAmt`, `retDt`를 노출한다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java:53-71`).
- `DelayPNRQueryResponse`는 `mainList`를 갖고, 각 PNR 항목은 `pnrNo`와 `dlayList`를 제공한다. 지연 항목은 `dlayAcptFlg`, `jrnyOrdr`, `jrnyTpCd`, `runDt`, `trnNo`를 제공한다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayPNRQueryDao.java:14-43`, `analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayPNRQueryDao.java:87-112`).

### 4.3 지연 보상 탭 규칙

- `RefundActivity`는 두 탭으로 구성되고, 첫 탭은 지연 보상 `C5683c`, 둘째 탭은 운행중지 보상 `C5681a`이다 (`analysis/jadx/sources/com/korail/talk/ui/refund/RefundActivity.java:29-41`).
- 목록 조회 기간은 선택한 `yyyyMM`에 `"01"`을 붙인 값을 시작일로 만들고, 종료일은 `yyyyMM31`이지만 오늘보다 미래이면 오늘 날짜로 보정한다 (`analysis/jadx/sources/G6/C5683c.java:67-83`, `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketSelfCheckinStatusActivity.java:38-42`).
- 목록 UI는 같은 반환번호(`getReturnNo`)가 연속되면 한 건으로 병합하고, 결제수단 표시는 `stlList`가 비면 기타, 2개 이상이면 혼합, 단일 `stlMnsCd=02`이면 신용카드, 그 외는 마일리지로 표시한다 (`analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:182-184`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:288-326`).
- 체크박스 선택 항목이 하나 이상일 때만 보상 신청 버튼이 활성화된다 (`analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:166-174`).
- 지연 보상 신청 버튼은 지급수단 선택 라디오 다이얼로그를 열지만, 실제 실행 요청에는 `dlayFarePymtMtdCd`가 고정값 `"01"`로 설정된다 (`analysis/jadx/sources/G6/C5683c.java:124-135`, `analysis/jadx/sources/G6/C5683c.java:52-63`, `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketSelfCheckinStatusActivity.java:38-42`). 라디오 선택값 `i10`은 현재 코드에서 요청 필드에 반영되지 않는다 (`analysis/jadx/sources/G6/C5683c.java:41-45`, `analysis/jadx/sources/G6/C5683c.java:86-108`).
- 지연 보상은 선택된 각 티켓의 `saleWctNo`, `saleDd`, `saleSqNo`, `tkRetPwd`를 배열로 모아 상세/검증 API를 호출하고, 성공 콜백에서 같은 값으로 실행 API를 호출한다 (`analysis/jadx/sources/G6/C5683c.java:86-108`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:388-397`).
- 지연 보상 실행 성공 후 `dlayFarePymtMtdCd`가 `"01"`이면 `refund_delay_success_msg2`, 그 외이면 `refund_delay_success_msg1`를 보여주고 목록을 다시 조회한다 (`analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:392-403`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:186-200`).

### 4.4 지연증명/영수증/계좌환불

- 지연증명 화면은 `TicketDetailResponse`의 원권 창구/발매일/일련번호/반환비밀번호로 `athnIsu`를 호출한다. `runDt`와 `trnNo` 필드는 DAO에는 있으나 해당 Activity에서 설정하지 않는다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:37-46`, `analysis/jadx/sources/com/korail/talk/network/dao/delay/DelayCertificateDao.java:12-19`).
- 지연증명 응답이 1건이면 바로 문구를 만들고, 2건 이상이면 `dlayArvFlg=Y`인 항목만 문구에 포함한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:61-82`).
- 지연증명은 화면 bitmap을 임시 receipt 파일로 저장해 이메일 전송 또는 모바일팩스 인텐트로 전달한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:52-58`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:144-152`).
- 지연 반환 영수증은 `TicketDetailResponse`의 원권 키로 `pymtRcet`를 호출하고, 응답의 지급수단명/반환일/반환액을 화면에 표시한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:40-49`, `analysis/jadx/sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:68-72`).
- 지연 계좌환불 화면은 시작 시 입금은행 목록을 조회하고 드롭다운에 은행명을 넣는다 (`analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:104-109`, `analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:200-217`).
- `CashRfnDao`의 `dmnPrsDvCd`는 코드상 `"A"`, `"B"`, `"I"` 세 값으로 쓰인다 (`analysis/jadx/sources/com/korail/talk/network/dao/delay/CashRfnDao.java:11-18`). 화면에서는 `"A"`가 승차권 조회, `"B"`가 계좌 조회, `"I"`가 환불 신청에 사용된다 (`analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:155-179`).
- `"B"` 또는 `"I"` 요청에는 은행코드와 계좌번호가 추가되고, `"I"` 요청에는 연락처도 추가된다 (`analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:84-101`).
- 개인정보 동의 체크박스가 켜져야 환불 신청 버튼이 활성화된다 (`analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:150-153`).

## 5. CompensateService: 운행중지 보상

### 5.1 엔드포인트와 요청 필드

| 흐름 | HTTP path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|
| 운행중지 보상 목록 | `/classes/com.korail.mobile.compensate.ticketList.do` | `executeCompensateRefundList` | `Device`, `Version`, `Key`, `nowPgNo`, `dptDtFrom`, `dptDtTo` | `CompensateRefundListResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/compensate/CompensateService.java:20-22`) |
| 운행중지 보상 상세/검증 | `/classes/com.korail.mobile.compensate.ticketDetail.do` | `executeCompensateRefundDetail` | `Device`, `Version`, `Key`, `tkCnt`, `trnStpRsStnCd[]`, `jrnyStpTkFlg[]`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/compensate/CompensateService.java:16-18`) |
| 운행중지 보상 실행 | `/classes/com.korail.mobile.compensate.ticketReturn.do` | `executeCompensateRefund` | 상세/검증과 동일 | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/compensate/CompensateService.java:12-14`) |

### 5.2 응답과 UI 규칙

- 운행중지 목록 응답은 지연 보상과 동일하게 `network.response.delay.RefundResponse`를 상속하므로 `ticketList`, `whlPgNum`, `TicketList` 필드 구조를 공유한다 (`analysis/jadx/sources/com/korail/talk/network/dao/compensate/CompensateRefundListDao.java:45-54`, `analysis/jadx/sources/com/korail/talk/network/response/delay/RefundResponse.java:9-47`).
- 운행중지 탭은 라벨을 운임반환/교환권 성격으로 표시한다 (`analysis/jadx/sources/G6/C5681a.java:27-29`).
- 목록 기간 산정, 미래 종료일 보정, `WRG000000` 숨김 오류 코드는 지연 탭과 동일한 패턴이다 (`analysis/jadx/sources/G6/C5681a.java:51-67`).
- 선택 항목의 `trnStpRsStnCd`, `jrnyStpTkFlg`, 원권 창구/발매일/일련번호/반환비밀번호를 배열로 모아 상세/검증 API를 호출한다 (`analysis/jadx/sources/G6/C5681a.java:70-98`).
- 상세/검증 성공 콜백은 같은 배열을 실행 요청으로 복사해 `executeCompensateRefund`를 호출한다 (`analysis/jadx/sources/G6/C5681a.java:35-48`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:410-418`).
- 실행 성공 후 완료 다이얼로그를 표시하고 선택/목록 데이터를 초기화한 뒤 재조회한다 (`analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:406-419`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:194-200`).

## 6. ReservationCancelService: 예약 취소/취소 확인/예약 변경

### 6.1 엔드포인트와 요청 필드

| 흐름 | HTTP path | Java method | 요청 필드 | 응답 |
|---|---|---|---|---|
| 예약 취소 1단계 | `/classes/com.korail.mobile.reservationCancel.ReservationCancel` | `reservationCancel` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:15-17`) |
| 예약 취소 확인/완료 | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `reservationCancelCheck` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` | `BaseResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:19-21`) |
| 예약 인원 변경 | `/classes/com.korail.mobile.reservation.reservationChange.do` | `reservationChange` | `Device`, `Version`, `Key`, `pnrNo`, `chgTno`, `totPrnb`, `stndFlg`, `evntWctFlg`, `wctHndgCncDvCd`, `lrgCrgFlg`, `psgCnt`, `RJrny`, `RSrcar`, `RSeat`, `RPsg`, `RDscp` FieldMap | `ReservationChangeResponse` (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java:23-25`) |

### 6.2 DAO/응답 클래스

- `RsvCancelRequest`와 `RsvCancelCheckRequest`는 `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo`를 가진다 (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelDao.java:12-60`, `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelCheckDao.java:11-50`).
- `AutoRsvCancelDao`와 `AutoRsvCancelCheckDao`는 일반 요청을 상속하면서 `RsvInquiryResponse.TrainInfos trainInfo`만 추가하고, endpoint 자체는 부모 DAO와 같다 (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/AutoRsvCancelDao.java:8-29`, `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/AutoRsvCancelCheckDao.java:8-29`).
- `ReservationChangeResponse`는 `jrnyList`를 갖고, 각 `JrnyInfo`는 `lumpStlTgtNo`를 제공한다 (`analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java:17-26`, `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java:151-159`).

### 6.3 예약 취소 2단계 규칙

- 여러 화면에서 예약 취소 요청은 먼저 `ReservationCancel`을 호출한 뒤, 성공 콜백에서 확인 다이얼로그를 띄우고 사용자가 확인하면 `ReservationCancelChk`를 호출하는 2단계 패턴이다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:280-299`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:583-599`; `analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java:118-145`, `analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java:250-264`).
- 일반 예약 확인 화면의 취소 요청은 PNR, 여정수, `txtJrnySqno="0001"`, `hidRsvChgNo="000"`을 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java:269-278`).
- 예약 확인 화면에서 `ReservationCancel` 성공 후 연계예약이면 바로 `ReservationCancelChk`를 호출하고, 비연계예약이면 사용자 확인 다이얼로그 후 `ReservationCancelChk`를 호출한다 (`analysis/jadx/sources/com/korail/talk/ui/reservation/confirm/activity/DReservationConfirmActivity.java:403-430`).
- 예약 대기 화면도 취소 버튼에서 `ReservationCancel`을 호출하고, 성공 콜백의 확인 다이얼로그 후 `ReservationCancelChk`를 호출한다 (`analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java:118-145`, `analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java:205-207`, `analysis/jadx/sources/com/korail/talk/ui/reservation/ReservationWaitActivity.java:250-264`).
- 예약내역 화면은 예약내역 조회에 NetFunnel `act_21`을 사용하고, 취소 완료 후 목록 데이터를 비운 뒤 예약내역을 재조회한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:303-307`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:393-397`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:583-599`).
- 장바구니 화면도 `ReservationCancel` 후 확인 다이얼로그, `ReservationCancelChk` 후 완료 다이얼로그와 장바구니 재조회 패턴을 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java:347-368`, `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java:468-483`, `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java:774-799`).

### 6.4 예약 변경 규칙

- 예약 변경 화면은 PNR로 예약 상세를 조회한 뒤 승객 수 편집 UI를 초기화한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java:127-134`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java:170-176`).
- 승객 수가 기존과 같거나 총 인원이 0이면 변경 버튼을 비활성화한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java:59-72`).
- `ReservationChangeRequest`는 기존 예약의 PNR와 첫 여정의 `h_rsv_chg_no`를 `chgTno`로 쓰고, `stndFlg`, `evntWctFlg`, `wctHndgCncDvCd`, `lrgCrgFlg`를 모두 `"N"`으로 설정한다 (`analysis/jadx/sources/w4/a.java:120-137`).
- 변경 요청은 기존 여정의 여정순번, 여정유형, 열차번호, 운행일, 열차그룹, 출도착역, 좌석등급/좌석속성 등을 `RJrny`, `RSrcar`, `RSeat` FieldMap으로 구성한다 (`analysis/jadx/sources/w4/a.java:139-160`).
- 변경 성공 후 응답의 첫 `lumpStlTgtNo`로 통합결제 요청을 만들고, 최종 `dao_cart_payment` 성공 시 완료 다이얼로그 후 Activity result를 성공으로 종료한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java:111-119`, `analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketChangeActivity.java:178-193`).

## 7. 로컬 부작용 정리

- 일반 승차권 환불 성공 후 settlement code `13`이 있으면 RailPlus 동기화를 수행한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:493-525`, `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1521-1527`).
- 티켓 목록 화면에서 환불 후 로컬 `SMSData`를 PNR 기준으로 삭제하고 목록을 갱신한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1480-1495`).
- 지연증명 발급 화면은 증명서 view를 임시 이미지 파일로 저장해 메일/팩스 전송 인텐트에 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:52-58`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:144-152`).
- 지연/운행중지 보상 성공 후 fragment는 선택 목록을 비우고 버튼을 비활성화한 뒤 목록을 재조회한다 (`analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:186-200`).
- 예약내역/장바구니 취소 완료 후 각각 예약내역 또는 장바구니를 재조회한다 (`analysis/jadx/sources/com/korail/talk/ui/menu/ReservedTicketActivity.java:393-397`, `analysis/jadx/sources/com/korail/talk/ui/menu/BasketTicketActivity.java:475-483`).

## 8. 미확인 항목

- 서버가 각 코드(`WRT800078`, `WRT800179`, `WRG000000`, `h_ret_dv_cd=02`, `prg_psb_flg=M`)를 어떤 조건에서 반환하는지는 클라이언트 코드만으로 확정할 수 없다. 클라이언트는 해당 코드 수신 후의 분기만 보여준다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:298-315`, `analysis/jadx/sources/S5/h.java:183-193`, `analysis/jadx/sources/G6/C5683c.java:74-83`).
- `act_22` 환불 NetFunnel 상수는 확인되지만, 이 분석 범위에서 환불 DAO에 연결된 실행 경로는 확인되지 않았다. 운영 서버 또는 난독화된 다른 경유 호출에서 적용되는지는 미확인이다 (`analysis/jadx/sources/K4/g.java:47`, `analysis/jadx/sources/com/korail/talk/network/BaseDao.java:104-106`).
- 실제 응답 payload 예시, 금액 계산식, 환불 가능 여부의 서버 판정 기준, 계좌 검증 결과 문구는 정적 분석만으로 알 수 없으므로 unknown으로 남긴다 (`analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:7-30`).

## 9. 담당 범위 API 문서화 산출물

이 섹션은 `RefundService`, `DelayService`, `CompensateService`만 대상으로 한 라이브러리 문서화 초안이다. 근거는 로컬 JADX/정적 산출물과 기존 상태표이며, 이 보강 과정에서 운영 KORAIL 서버/API 호출과 credential 사용은 하지 않았다. 모든 form 요청은 `BaseRequest`가 기본 `Device`, `Version`, `Key` 값을 채운다 (`analysis/jadx/sources/com/korail/talk/network/BaseRequest.java:7-18`). 공통 응답 envelope은 `strResult`, `h_msg_cd`, `h_msg_txt`이다 (`analysis/jadx/sources/com/korail/talk/network/BaseResponse.java:7-30`).

위험도 표기는 `낮음=조회/목록`, `중간=실권/개인정보/증빙 필요 또는 금전성 사전조회`, `높음=환불/보상/접수/계좌환불 등 운영 상태나 금전 흐름을 바꿀 수 있음`으로 구분한다. 기존 성공/실패 상태는 `docs/api-status-by-service.md` 기준이다.

### 9.1 RefundService method matrix

| Method | HTTP/path | Request params | Response DTO shape | 위험도 | 기존 상태 | Signature 초안 |
|---|---|---|---|---|---|---|
| `executeOnlineRefunds` | `POST /classes/com.korail.mobile.refunds.executeOnlineRefunds` | `pnrNo`, `tkKndCd`, `retDvCd`, `retRsnCd`, `ogtkSaleDt`, `ogtkSaleWctNo`, `ogtkSaleSqno`, `ogtkRetPwd`, `retAmt`, `retFee`, `custTeln`, `acepCustNm` plus common | `BaseResponse` + `h_ret_dv_cd` | 높음: 반환번호 환불 실행 | 미실행: 운영 상태 변경 가능 | `executeOnlineRefund(params): Promise<RefundExecuteOnlineResponse>` |
| `getTicketCommission` | `POST /classes/com.korail.mobile.refunds.CommissionView` | `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_comp_nm`, `h_comp_cert_no` plus common | `BaseResponse` + `ret_amt`, `ret_fee`, `tk_ret_tms_dv_cd`, `prg_psb_flg`, `use_psb_mlg_num`, secondary message fields | 중간: 환불 전 금전성 사전조회 | 미실행: 운영 상태 변경 가능 | `getRefundCommission(params): Promise<RefundCommissionResponse>` |
| `getTicketDetail` | `POST /classes/com.korail.mobile.refunds.SelTicketInfo` | `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_purchase_history` plus common | `BaseResponse` + 원권/PNR/반환가능/지연/부가서비스/티켓 상세 fields | 중간: 실권 상세 필요 | 미실행: 운영 상태 변경 가능 | `getRefundTicketDetail(params): Promise<TicketDetailResponse>` |
| `returnTicket` | `POST /classes/com.korail.mobile.refunds.RefundsRequest` | `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_sale_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_mlg_stl`, `tk_ret_tms_dv_cd`, `trnNo`, `pbpAcepTgtFlg`, `latitude`, `longitude` plus common | `BaseResponse` + `stlList[].stl_mns_cd` | 높음: 승차권 환불 실행 | 미실행: 운영 상태 변경 가능 | `returnTicket(params): Promise<RefundReturnResponse>` |
| `verifyOnlineRefunds` | `POST /classes/com.korail.mobile.refunds.verifyOnlineRefunds` | `retNo1`, `retNo2`, `retNo3`, `retNo4`, `strName` plus common | `BaseResponse` + `orgtkinfo_list[]`, `poppMsg`, `rcvd_amt`, `ret_amt`, `ret_fee` | 중간: 반환번호/신청자 검증 | 미실행: 운영 상태 변경 가능 | `verifyOnlineRefund(params): Promise<RefundVerifyTicketResponse>` |

Endpoint/field 근거는 `RefundService.java:15-33`, DAO request/execute mapping은 `RefundExecuteTicketRefundDao.java:11-140`, `RefundCommissionDao.java:11-116`, `TicketDetailDao.java:227-500`, `RefundDao.java:13-145`, `RefundVerifyTicketDao.java:13-217`이다.

일반 환불 흐름은 티켓 상세 원권 키로 수수료를 조회한 뒤, `WRT800078`/`WRT800179` 분기 또는 수수료 확인 다이얼로그를 거쳐 `RefundsRequest`를 실행한다. 전용 반환 화면은 선택 티켓별로 `CommissionView`를 순차 호출하고, `tk_ret_tms_dv_cd`, 마일리지 수수료 사용 여부, 위치정보를 `RefundsRequest`에 반영한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:343-404`, `analysis/jadx/sources/com/korail/talk/ui/ticket/ticketReturn/a.java:472-517`). 티켓 목록 inline 반환은 같은 `CommissionView`/`RefundsRequest`를 쓰지만 `tk_ret_tms_dv_cd`, `trnNo`, `latitude`, `longitude`를 채우지 않는 경로가 있다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:926-1002`, `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java:1498-1538`).

온라인 반환번호 환불은 입력 fragment가 반환번호 4분할과 신청자명으로 `verifyOnlineRefunds`를 호출하고, 검증 응답의 원권/금액/사유 값을 그대로 `executeOnlineRefunds` 요청에 복사한다. 실행 응답의 `h_ret_dv_cd == "02"`이면 완료 문구, 그 외에는 성공 문구로 분기한다 (`analysis/jadx/sources/S5/c.java:64-73`, `analysis/jadx/sources/S5/c.java:193-208`, `analysis/jadx/sources/S5/h.java:111-127`, `analysis/jadx/sources/S5/h.java:183-193`).

### 9.2 DelayService method matrix

| Method | HTTP/path | Request params | Response DTO shape | 위험도 | 기존 상태 | Signature 초안 |
|---|---|---|---|---|---|---|
| `athnIsu` | `POST /classes/com.korail.mobile.dlay.athnIsu.do` | `ogtkSaleWctNo`, `ogtkSaleDd`, `ogtkSaleSqno`, `ogtkRetPwd`, `runDt`, `trnNo` plus common | `BaseResponse` + `dlayList[]` | 중간: 실권 기반 지연증명 발급/조회 | 미실행: PNR/티켓 실데이터 필요 | `issueDelayCertificate(params): Promise<DelayCertificateResponse>` |
| `cashRfn` | `POST /classes/com.korail.mobile.dlay.cashRfn.do` | `dmnPrsDvCd`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`, `dptnBankCd`, `dptnAcntNo`, `custNm`, `custTeln`, `rmk1Cont` plus common | `BaseResponse` + `rfnAmt` | 높음 when `dmnPrsDvCd=I`; `A`/`B`는 조회/계좌검증 | 미실행: 운영 상태 변경 가능 | `requestDelayCashRefund(params): Promise<CashRefundResponse>` |
| `dealyReturnReceipt` | `POST /classes/com.korail.mobile.dlay.pymtRcet.do` | `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd` plus common | `BaseResponse` + `dlayFarePymtMtdNm`, `dlayFareRetAmt`, `retDt` | 중간: 실권 영수증 조회 | 미실행: 운영 상태 변경 가능 | `getDelayReturnReceipt(params): Promise<DelayReturnReceiptResponse>` |
| `dptnBank` | `POST /classes/com.korail.mobile.dlay.dptnBank.do` | common only | `BaseResponse` + `dptnBank[].dptnBankCd/dptnBankNm` | 낮음: 은행 목록 조회 | 성공: `API.I00000 Success` | `listDelayDepositBanks(): Promise<DptnBankResponse>` |
| `executeDelayPNRAccept` | `POST /classes/com.korail.mobile.delay.acptPrs.do` | `jobDvCd`, `pnrCnt`, `pnrNo[]`, `ogtkWctNo[]` plus common | `BaseResponse` only | 높음: 지연 동의/접수 처리 | 미실행: 운영 상태 변경 가능 | `acceptDelayedPnrs(params): Promise<BaseResponse>` |
| `executeDelayPNRQuery` | `POST /classes/com.korail.mobile.delay.pnrQry.do` | `jobDvCd`, `pnrCnt`, `pnrNo[]`, `ogtkWctNo[]` plus common | `BaseResponse` + `mainList[].pnrNo/dlayList[]` | 중간: PNR 기반 지연동의 대상 조회 | 미실행: PNR/티켓 실데이터 필요 | `queryDelayedPnrs(params): Promise<DelayPnrQueryResponse>` |
| `executeDelayRefund` | `POST /classes/com.korail.mobile.delay.ticketReturn.do` | `dlayFarePymtMtdCd`, `tkCnt`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` plus common | `BaseResponse` only | 높음: 지연 보상/환불 실행 | 미실행: 운영 상태 변경 가능 | `executeDelayRefund(params): Promise<BaseResponse>` |
| `executeDelayRefundDetail` | `POST /classes/com.korail.mobile.delay.ticketDetail.do` | `tkCnt`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` plus common | `BaseResponse` only | 중간-높음: 실행 직전 검증 | 미실행: 운영 상태 변경 가능 | `checkDelayRefund(params): Promise<BaseResponse>` |
| `executeDelayRefundList` | `POST /classes/com.korail.mobile.delay.ticketList.do` | `nowPgNo`, `dptDtFrom`, `dptDtTo` plus common | `BaseResponse` + `ticketList[]`, `whlPgNum` | 낮음-중간: 보상 대상 목록 조회 | 실패: `WRG000000 조회 결과가 없습니다.` | `listDelayRefundTickets(params): Promise<DelayRefundListResponse>` |

Endpoint/field 근거는 `DelayService.java:18-52`, DTO/DAO 근거는 `DelayCertificateDao.java:12-133`, `CashRfnDao.java:11-131`, `DelayReturnReceiptDao.java:11-78`, `DptnBankDao.java:13-44`, `DelayPNRQueryDao.java:10-118`, `DelayPNRAcceptDao.java:10-60`, `DelayRefundCheckDao.java:12-67`, `DelayRefundDao.java:12-76`, `DelayRefundListDao.java:12-54`이다.

지연 보상 탭은 월 단위 기간으로 `executeDelayRefundList`를 조회하고, 선택된 티켓의 원권 키 배열로 `executeDelayRefundDetail`을 먼저 호출한 뒤 성공 콜백에서 `executeDelayRefund`를 실행한다. 요청의 `dlayFarePymtMtdCd`는 UI 라디오 선택과 별개로 `"01"`에 해당하는 상수를 고정 세팅한다 (`analysis/jadx/sources/G6/C5683c.java:52-63`, `analysis/jadx/sources/G6/C5683c.java:67-107`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:382-403`).

지연증명 흐름은 `TicketDetailResponse`의 원권 창구/발매일/일련번호/반환비밀번호만 세팅해 `athnIsu`를 호출한다. DAO에는 `runDt`, `trnNo` 필드가 있지만 해당 Activity 경로에서는 세팅하지 않는다. 응답은 `dlayList` 1건이면 바로 문구화하고, 2건 이상이면 `dlayArvFlg=Y`인 항목만 포함한다. 이후 화면 bitmap을 임시 receipt 파일로 저장해 메일/팩스 공유에 사용한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:37-45`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:61-82`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:52-58`, `analysis/jadx/sources/com/korail/talk/ui/ticket/history/TicketDelayCertificateActivity.java:144-152`).

지연 계좌환불은 화면 진입 시 `dptnBank`로 은행 목록을 받고, `cashRfn`의 `dmnPrsDvCd`를 `"A"`(승차권 조회), `"B"`(계좌 조회), `"I"`(환불 신청)로 바꿔 재사용한다. `"B"`/`"I"`에는 은행코드와 계좌번호가 들어가고, `"I"`에는 연락처도 추가된다 (`analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:84-101`, `analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:155-179`, `analysis/jadx/sources/com/korail/talk/ui/menu/delay/DelayAccountRefundActivity.java:200-235`). 지연 반환 영수증은 `TicketDetailResponse` 원권 키로 `dealyReturnReceipt`를 호출하고 지급수단명/반환일/반환액을 표시한다 (`analysis/jadx/sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:40-48`, `analysis/jadx/sources/com/korail/talk/ui/ticket/receipt/DelayReturnReceiptActivity.java:68-72`).

결제 흐름의 지연 동의는 `PaymentActivity`가 `executeDelayPNRQuery`를 호출해 `dlayAcptFlg=Y`인 PNR을 찾고, 사용자가 동의하면 같은 PNR 목록으로 `executeDelayPNRAccept`를 보낸다. 일반 결제는 `jobDvCd="0"`, 승차권 변경 결제는 `jobDvCd="1"`과 `ogtkWctNo[]`를 포함한다 (`analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:277-347`, `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:350-368`, `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java:632-665`).

### 9.3 CompensateService method matrix

| Method | HTTP/path | Request params | Response DTO shape | 위험도 | 기존 상태 | Signature 초안 |
|---|---|---|---|---|---|---|
| `executeCompensateRefund` | `POST /classes/com.korail.mobile.compensate.ticketReturn.do` | `tkCnt`, `trnStpRsStnCd[]`, `jrnyStpTkFlg[]`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` plus common | `BaseResponse` only | 높음: 운행중지 보상 실행 | 미실행: 운영 상태 변경 가능 | `executeCompensateRefund(params): Promise<BaseResponse>` |
| `executeCompensateRefundDetail` | `POST /classes/com.korail.mobile.compensate.ticketDetail.do` | `tkCnt`, `trnStpRsStnCd[]`, `jrnyStpTkFlg[]`, `ogTkSaleWctNo[]`, `ogTkSaleDd[]`, `ogTkSaleSqNo[]`, `ogTkRetPwd[]` plus common | `BaseResponse` only | 중간-높음: 실행 직전 검증 | 미실행: 운영 상태 변경 가능 | `checkCompensateRefund(params): Promise<BaseResponse>` |
| `executeCompensateRefundList` | `POST /classes/com.korail.mobile.compensate.ticketList.do` | `nowPgNo`, `dptDtFrom`, `dptDtTo` plus common | `BaseResponse` + `ticketList[]`, `whlPgNum` | 낮음-중간: 운행중지 보상 대상 목록 조회 | 실패: `WRG000000 조회 결과가 없습니다.` | `listCompensateRefundTickets(params): Promise<CompensateRefundListResponse>` |

Endpoint/field 근거는 `CompensateService.java:12-22`, DAO 근거는 `CompensateRefundDao.java:12-85`, `CompensateRefundCheckDao.java:12-85`, `CompensateRefundListDao.java:12-54`이다. 운행중지 보상 flow는 목록 조회 후 선택 티켓에서 `trnStpRsStnCd`, `jrnyStpTkFlg`, 원권 키 배열을 만들고, `executeCompensateRefundDetail` 성공 콜백에서 같은 배열을 `executeCompensateRefund`로 복사한다. 성공 후 완료 다이얼로그를 표시하고 선택/목록을 초기화한 뒤 재조회한다 (`analysis/jadx/sources/G6/C5681a.java:35-48`, `analysis/jadx/sources/G6/C5681a.java:51-98`, `analysis/jadx/sources/G6/ViewOnClickListenerC5686f.java:406-419`).

### 9.4 Reusable DTO shape draft

```ts
type KorailBaseResponse = {
  strResult?: "SUCC" | "FAIL" | string;
  h_msg_cd?: string;
  h_msg_txt?: string;
};

type RefundCommissionResponse = KorailBaseResponse & {
  ret_amt?: string;
  ret_fee?: string;
  tk_ret_tms_dv_cd?: string;
  prg_psb_flg?: string;
  use_psb_mlg_num?: string;
  h_msg_cd2?: string;
  h_msg_txt2?: string;
};

type RefundReturnResponse = KorailBaseResponse & {
  stlList?: Array<{ stl_mns_cd?: string }>;
};

type RefundVerifyTicketResponse = KorailBaseResponse & {
  poppMsg?: string;
  rcvd_amt?: string;
  ret_amt?: string;
  ret_fee?: string;
  orgtkinfo_list?: Array<{
    prnNo?: string;
    tk_knd_cd?: string;
    ret_dv_cd?: string;
    ret_rsn_cd?: string;
    ogtk_sale_dt?: string;
    ogtk_sale_wct_no?: string;
    ogtk_sale_sqno?: string;
    ogtk_ret_pwd?: string;
    jrnyinfo_list?: Array<{
      dpt_dt?: string;
      dpt_tm?: string;
      arv_tm?: string;
      dpt_rs_stn_cd?: string;
      arv_rs_stn_cd?: string;
      trn_gp_cd?: string;
      trn_no?: string;
      seatinfo_list?: Array<{ scar_no?: string; psrm_cl_nm?: string; seat_no?: string }>;
    }>;
  }>;
};

type RefundExecuteOnlineResponse = KorailBaseResponse & { h_ret_dv_cd?: string };

type TicketDetailResponse = KorailBaseResponse & {
  h_pnr_no?: string;
  h_sale_dt?: string;
  h_orgtk_wct_no?: string;
  h_orgtk_ret_sale_dt?: string;
  h_orgtk_sale_sqno?: string;
  h_orgtk_ret_pwd?: string;
  h_ret_flg?: string;
  h_dlay_flg?: string;
  h_dlay_tk_flg?: string;
  h_pbp_acep_tgt_flg?: string;
  h_tk_knd_cd?: string;
  retPsbFlg?: string;
  mlgSaveFlg?: string;
  addSrvFlg?: string;
  addSrvCancel?: string;
  ticket_infos?: unknown;
  dtlList?: Array<Record<string, string | undefined>>;
};

type DelayCertificateResponse = KorailBaseResponse & {
  dlayList?: Array<{
    runDay?: string;
    runDt?: string;
    trnNo?: string;
    dptRsStnCd?: string;
    arvRsStnCd?: string;
    arvRsStnNm?: string;
    dlayArvFlg?: string;
    trnDlayTm?: string;
  }>;
};

type CashRefundResponse = KorailBaseResponse & { rfnAmt?: string };
type DelayReturnReceiptResponse = KorailBaseResponse & {
  dlayFarePymtMtdNm?: string;
  dlayFareRetAmt?: string;
  retDt?: string;
};
type DptnBankResponse = KorailBaseResponse & {
  dptnBank?: Array<{ dptnBankCd?: string; dptnBankNm?: string }>;
};
type DelayPnrQueryResponse = KorailBaseResponse & {
  mainList?: Array<{ pnrNo?: string; dlayList?: Array<{ dlayAcptFlg?: string; jrnyOrdr?: string; jrnyTpCd?: string; runDt?: string; trnNo?: string }> }>;
};
type DelayOrCompensateRefundListResponse = KorailBaseResponse & {
  whlPgNum?: number;
  ticketList?: Array<{
    saleWctNo?: string;
    saleDd?: string;
    saleSqNo?: string;
    tkRetPwd?: string;
    dptRsStnNm?: string;
    arvRsStnNm?: string;
    arvDt?: string;
    trnNo?: number;
    stlbTrnClsfNm?: string;
    stlList?: Array<{ stlMnsCd?: string }>;
    dlayFare?: number;
    rcvdAmt?: number;
    rcVdAmt?: number;
    trnRunStpCpstAmt?: number;
    trnStpRsStnCd?: string;
    jrnyStpTkFlg?: string;
  }>;
};
```

## 20-agent follow-up audit 보강

- `TicketListActivity`도 일반 환불 caller다. 이 경로는 `RefundCommissionDao`와 `RefundDao`를 호출하지만 request에 `tk_ret_tms_dv_cd`, `trnNo`, `latitude`, `longitude`를 채우지 않는다.
- RailPlus sync는 일반 환불 성공 path에서 두 caller 모두 확인된다. error-path sync는 `ticketReturn/a.java`에서만 관찰되고, `TicketListActivity` error path에서는 확인되지 않았다.
- 지연동의 payment flow는 `PaymentActivity`가 delay PNR query를 `jobDvCd="0"`으로 보내며, ticket-change payment일 때만 `jobDvCd="1"` 및 `ogtkWctNo`를 포함한다. delayed PNR prompt 뒤 accept API가 호출된다.
- 예약 취소 caller에는 `DirectInquiryActivity`의 `AutoRsvCancelDao`도 포함한다. limousine flow도 동일 cancel/check endpoint를 사용한다.
- reservation change request의 `RPsg`/`RDscp` FieldMap에는 승객/할인 코드 조합이 포함되며 확인된 discount code로 `321`, `131`, `111`, `112`가 있다.
- ticket-change rollback/cancel은 `DReservationConfirmActivity`가 `/classes/com.korail.mobile.ticket.tripChgHndgCnc.do`의 `TCCancelDao`를 사용한다. 일반 `ReservationCancelService` cancel과 구분해야 한다.
