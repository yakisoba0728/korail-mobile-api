# 09. TicketService / MyTicketService 딥다이브

## 범위와 전제

이 문서는 `korail.apk`를 로컬에서 정적으로 decompile한 결과만 근거로 작성했다. 운영 서버 호출, 계정 로그인, 런타임 응답 캡처는 수행하지 않았다. 따라서 아래의 응답 필드는 실제 서버 샘플이 아니라 앱 DTO/DAO 클래스에 선언된 역직렬화 필드다.

주요 분석 범위는 `TicketService`, `MyTicketService`, 승차권 목록/상세/캐시, 셀프 체크인, 중복 승차권 확인, 플랫폼 번호, 보호자 안심 SMS, 승차권 변경/취소, `TicketService` 안의 MAAS 부가서비스 API다. 승차권 상세는 `TicketService`가 아니라 `RefundService.getTicketDetail()`의 `SelTicketInfo`를 `TicketListActivity`가 호출하므로 인접 필수 범위로 포함했다. 예약 취소/예약 변경 API는 `ReservationCancelService`에 있어 별도 인접 범위로 구분했다.

공통 요청 필드는 `BaseRequest` 생성자에서 `Device=AD`, `Version=250601003`, `Key=korail1234567890`로 채워진다. 공통 응답은 `BaseResponse`의 `h_msg_cd`, `h_msg_txt`, `strResult`를 갖는다.

근거:

- `analysis/jadx/sources/com/korail/talk/network/BaseRequest.java`
- `analysis/jadx/sources/com/korail/talk/network/BaseResponse.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/MyTicketService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java`
- `docs/api-endpoints.md`

## Endpoint Inventory

### MyTicketService

| Method | Path | Java method | Request fields | Response class / declared fields |
|---|---|---|---|---|
| `POST` | `/classes/com.korail.mobile.myTicket.MyTicketList` | `getTicketList` | `Device`, `Version`, `Key`, `txtDeviceId`, `txtIndex`, `h_page_no`, `h_abrd_dt_from`, `h_abrd_dt_to`, `hiduserYn`, `hidName`, `hidTeleNo`, `hidPwd`, `tsRsStnCd` | `TicketListResponse`: `reservation_list[]` -> `ReservationList.ticket_list[]` -> `TicketList.train_info[]` -> `TrainInfo` fields listed below |
| `GET` | `/classes/com.korail.mobile.myTicket.reqUpgradeSeat` | `requestUpgradeSeat` | `Device`, `Version`, `Key`, `ogtkSaleDd`, `ogtkSaleWctNo`, `ogtkSaleSqno`, `ogtkRetPwd`, `jrnyTpCd`, `jrnySqno`, `dptDt`, `dptStnConsOrdr`, `dptStnRunOrdr`, `dptRsStnCd`, `dptTm`, `arvDt`, `arvStnConsOrdr`, `arvStnRunOrdr`, `arvRsStnCd`, `arvTm`, `trnNo`, `runDt`, `trnGpCd`, `roomClsfCd`, `scarNo`, `seatNo`, `rqSeatAttCd` | `SpecialRoomUpgradeResponse`: `jrnys[].lumpStlTgtNo`, `ticketInfo.custNm`, `ticketInfo.scnIndcAmt`, `ticketInfo.totFare` |
| `GET` | `/classes/com.korail.mobile.myTicket.procUpgradeSeat` | `procUpgrade` | `Device`, `Version`, `Key`, `totTxnAmt`, `totCncRetAmt`, `totCncRetFee`, `feeProyStlSqno`, `lumpStlTgtNo`, `mnsGridcnt`, `stlMnsSqno`, `stlMnsCd`, `mnsStlAmt`, `crdInpWayCd`, `ismtMnthNum`, `pontDvCd`, `pontInpDvCd`, `prepCrdTxnBfAmt`, `prepCrdTxnAftAmt` | `BaseResponse` |

`TicketListDao.TrainInfo` 응답 필드:

- 식별/원권: `h_pnr_no`, `h_orgtk_wct_no`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_rsv_chg_tno`, `h_tk_sqno`, `pbpRsvNo`
- 열차/여정: `h_run_dt`, `h_trn_no`, `h_trn_clsf_cd`, `h_trn_clsf_nm`, `h_dpt_dt`, `h_dpt_tm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`, `h_arv_dt`, `h_arv_tm`, `h_arv_rs_stn_cd`, `h_arv_rs_stn_nm`, `h_jrny_sqno`
- 좌석/승객/금액: `h_srcar_no`, `h_seat_no`, `h_seat_no_end`, `h_seat_cnt`, `h_psrm_cl_cd`, `h_psg_tp_cd`, `h_rcvd_amt`, `h_abrd_ps_nm`, `h_buy_ps_nm`, `h_sgr_nm_1`, `h_sgr_nm_2`
- 상태/기능 플래그: `h_tk_knd_cd`, `h_tk_knd_nm`, `h_pbp_acep_tgt_flg`, `dvcInfoSmnsFlg`, `apdUsrFlg`, `cmtrVlidFlg`, `runClsFlg`, `srtStnFlg`, `stpvFlg`, `trnSpsFlg`

근거:

- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/MyTicketService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeProcessDao.java`
- `analysis/jadx/sources/com/korail/talk/network/request/myTicket/PushUpdateRequest.java`

### TicketService

| Method | Path | Java method | Request fields | Response class / declared fields |
|---|---|---|---|---|
| `POST` | `/classes/com.korail.mobile.tk.dvcInfoInit.do` | `deviceReset` | `Device`, `Version`, `Key`, `teln`, `custNm`, `nonMbPwd`, `stlbTrnClsfCd`, `dptDttm`, `latitude`, `longitude`, `trnNo` | `BaseResponse` |
| `POST` | `/classes/com.korail.mobile.tk.dlvRcvCust.do` | `dlvRcvCust` | `Device`, `Version`, `Key`, `saleWctNo`, `saleDt`, `saleSqno`, `tkRetPwd` | `DlvRcvCustwResponse`: `acepCustMgNo`, `acepCustNm`, `acepCustTeln`, `mbCrdNo` |
| `POST` | `/classes/com.korail.mobile.ticket.ticketDupCheck.do` | `duplicationCheck` | `Device`, `Version`, `Key`, `pnrNo` | `DuplicationCheckResponse`: `rsvCnt` |
| `POST` | `/classes//com.korail.mobile.addService.cancelPay.do` | `getMaasCancel` | `Device`, `Version`, `custMgNo`, `lumpStlTgtNo` | `BaseResponse`; `Key` 없음 |
| `POST` | `/classes/com.korail.mobile.addService.coptCnc.do` | `getMaasServiceCancel` | `Device`, `Version`, `pnrNo`, `cncTgtCnt`, `cncAddSrvReqNo`, `cncRetFee` | `BaseResponse`; `Key` 없음 |
| `POST` | `/classes/com.korail.mobile.maas.cncFee.do` | `getMaasServiceCancelFee` | `Device`, `Version`, `Key`, `addSrvReqNo`, `addSrvDvCd`, `coptEntRsvNo` | `MaasServiceCancelFeeResponse`: `cncRetFee` |
| `POST` | `/classes/com.korail.mobile.copt.gdReqQry.do` | `getMaasServiceDetailList` | `Device`, `Version`, `qryDtFrom`, `qryDtTo` | `MaasServivceDetailResponse`: `addSrvList[]` with fields below; `Key` 없음 |
| `POST` | `/classes/com.korail.mobile.self.seatChgInfo.do` | `getSelfSeatChgInfo` | `Device`, `Version`, `Key`, `runDt`, `trnNo`, `dptRsStnCd`, `arvRsStnCd`, `psrmClCd` | `CallSelfSeatChgInfoResponse`: fields below |
| `POST` | `/classes/com.korail.mobile.reservation.tripChgDate.do` | `getTripChgDate` | `Device`, `Version`, `Key`, `tripChgDate` | `TripChgInfoDaoResponse`: `tripChgDate`, `lastRunDt`, `tripChgDates[]` |
| `POST` | `/classes/com.korail.mobile.tk.gurdSmsSnd.do` | `gurdSmsSnd` | `Device`, `Version`, `Key`, `pnrNo`, `jrnySqno`, `rcvPsHndyTeln` | `BaseResponse` |
| `POST` | `/classes/com.korail.mobile.tk.pbpAcepSpec.do` | `pbpAcepSpec` | `Device`, `Version`, `Key`, `tkCnt`, `tkRetNo[]` | `PbpAcepSpecResponse`: `tkList[]` with `pnrNo`, `saleDt`, `saleSqno`, `saleWctNo`, `tkRetPwd`, `jrnyList[]`; `jrnyList` has `acepCustNm`, `acepCustTeln`, `jrnyTpCd`, `mbDvNm`, `pbpAcepKndNm`, `pbpRsvNo`, `regDt`, `wdrwPsbFlg`, `seatList[]`; `seatList` has `psgTpDvNm`, `psrmClCd`, `psrmClNm`, `scarNo`, `seatNo` |
| `POST` | `/classes/com.korail.mobile.tk.pbpWdrw.do` | `pbpTkWdrw` | `Device`, `Version`, `Key`, `pbpCnt`, `pbpRsvNo[]`, `pnrNo[]` | `BaseResponse` |
| `POST` | `/classes/com.korail.mobile.tk.plfNo.do` | `plfNo` | `Device`, `Version`, `Key`, `tkCnt`, `tkRetNo[]` | `PlfNoResponse`: `tkList[]` with `saleDt`, `saleSqno`, `saleWctNo`, `tkRetNo`, `tkRetPwd`, `jrnyList[].plfNo` |
| `POST` | `/classes/com.korail.mobile.tk.rcntDlvHst.do` | `rcntDlvHst` | `Device`, `Version`, `Key`, `custMgNo` | `RcntDlvHstResponse`: `acepList[]` with `acepCustMgFlg`, `acepCustMgNo`, `acepCustNm`, `acepCustTeln`, `acepCustTeln2`, `mbCrdNo` |
| `POST` | `/classes/com.korail.mobile.checkin.cnc.do` | `selfCheckinCancel` | `Device`, `Version`, `Key`, `saleWctNo`, `saleDt`, `saleSqno`, `tkRetPwd`, `jrnySqno` | `BaseResponse` |
| `POST` | `/classes/com.korail.mobile.checkin.info.do` | `selfCheckinInfo` | `Device`, `Version`, `Key`, `saleWctNo`, `saleDt`, `saleSqno`, `tkRetPwd`, `jrnySqno` | `SelfCheckinInfoResponse`: fields below |
| `POST` | `/classes/com.korail.mobile.checkin.psbFlg.do` | `selfCheckinPossible` | `Device`, `Version`, `Key`, `qrcode`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`, `jrnySqno` | `SelfCheckinPossibleResponse`: `consList[]` with fields below |
| `POST` | `/classes/com.korail.mobile.checkin.reg.do` | `selfCheckinRegister` | `Device`, `Version`, `Key`, `cpsNo`, `scarNo`, `seatNo`, `saleWctNo`, `saleDd`, `saleSqno`, `tkRetPwd`, `jrnySqno` | `BaseResponse` |
| `POST` | `/classes/com.korail.mobile.ticket.tripChgHndgCnc.do` | `ticketChangeCancel` | `Device`, `Version`, `Key`, `lumpStlCnt`, FieldMap `lumpStlTgtNo_{index}` | `BaseResponse` |

`MaasServiceDetailListDao.AddSrvItem` 응답 필드:

- `addSrvDvCd`, `addSrvGdCd`, `addSrvId`, `addSrvMrkEntId`, `addSrvMrkEntNm`, `addSrvNm`, `addSrvPrgSttCd`, `addSrvReqNo`, `cgPsRefAtclCont`, `coptEntRsvNo`, `dlivPsbClsTm`, `dlivPsbStTm`, `leadMsgCont1`, `leadMsgCont2`, `pnrNo`, `reqDt`, `reqQnty`, `rsvSpecUrl`, `utlClsDt`, `utlStDt`

`CallSelfSeatChgInfoResponse` 응답 필드:

- 상위: `runDt`, `trnNo`, `trnClsfCd`, `trnClsfNm`, `trnGpCd`, `trnGpNm`, `exsDptStnRunOrdr`, `exsArvStnRunOrdr`, `chgBfDptStnConsOrdr`, `chgBfArvStnConsOrdr`, `gnrmRsvPsbCd`, `sprmRsvPsbCd`
- `chgRsnList[]`: `frcSaleRsnCont`, `qryCode`, `qryOrdr`
- `chgStnList[]`: `dptDt`, `dptTm`, `dptRsStnCd`, `dptRsStnNm`, `dptStnConsOrdr`, `dptStnRunOrdr`, `arvDt`, `arvTm`, `gnrmRestSeatNum`, `sprmRestSeatNum`

`SelfCheckinInfoResponse` 응답 필드:

- `pnrNo`, `jrnySqno`, `runDt`, `trnNo`, `stlbTrnClsfNm`, `scarNo`, `seatNo`, `asgnSqno`
- `dptDttm`, `dptRsStnCd`, `dptRsStnNm`, `dptStnConsOrdr`, `dptTmQb`
- `arvDttm`, `arvRsStnCd`, `arvRsStnNm`, `arvStnConsOrdr`, `arvTmQb`
- 체크인 상태/시간: `chcknDvCd`, `chcknSqno`, `chcknDt`, `chcknTm`, `chcknCncDt`, `chcknCncTm`

`SelfCheckinPossibleDao.ConsList` 응답 필드:

- `pnrNo`, `jrnySqno`, `runDt`, `trnNo`, `trnGpCd`, `tkKndCd`, `asgnSqno`, `cpsNo`, `scarNo`, `seatNo`
- `dptDttm`, `dptRsStnCd`, `dptStnConsOrdr`, `arvDttm`, `arvRsStnCd`, `arvStnConsOrdr`

근거:

- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/DeviceResetDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/DlvRcvCustDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinRegisterDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`

### 인접 상세/환불/예약 변경 API

| Service | Method | Path | Java method | Request fields | Response class / declared fields |
|---|---|---|---|---|---|
| `RefundService` | `POST` | `/classes/com.korail.mobile.refunds.SelTicketInfo` | `getTicketDetail` | `Device`, `Version`, `Key`, `h_orgtk_ret_sale_dt`, `h_orgtk_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_purchase_history` | `TicketDetailResponse`: 상세 필드 아래 참조 |
| `RefundService` | `POST` | `/classes/com.korail.mobile.refunds.RefundsRequest` | `returnTicket` | `Device`, `Version`, `Key`, `txtPnrNo`, `h_orgtk_sale_dt`, `h_orgtk_sale_wct_no`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_mlg_stl`, `tk_ret_tms_dv_cd`, `trnNo`, `pbpAcepTgtFlg`, `latitude`, `longitude` | `RefundResponse` |
| `ReservationCancelService` | `POST` | `/classes/com.korail.mobile.reservationCancel.ReservationCancelChk` | `reservationCancelCheck` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` | `BaseResponse` |
| `ReservationCancelService` | `POST` | `/classes/com.korail.mobile.reservationCancel.ReservationCancel` | `reservationCancel` | `Device`, `Version`, `Key`, `txtPnrNo`, `txtJrnySqno`, `txtJrnyCnt`, `hidRsvChgNo` | `BaseResponse` |
| `ReservationCancelService` | `POST` | `/classes/com.korail.mobile.reservation.reservationChange.do` | `reservationChange` | `Device`, `Version`, `Key`, `pnrNo`, `chgTno`, `totPrnb`, `stndFlg`, `evntWctFlg`, `wctHndgCncDvCd`, `lrgCrgFlg`, `psgCnt`, `RJrny`, `RSrcar`, `RSeat`, `RPsg`, `RDscp` FieldMaps | `ReservationChangeResponse`: `jrnyList[]`; `JrnyInfo.lumpStlTgtNo` |

`TicketDetailResponse` 주요 응답 필드:

- 원권/승차권: `h_pnr_no`, `h_orgtk_wct_no`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`, `h_sale_dt`, `h_sale_tm`, `h_wct_nm`, `h_tk_knd_cd`, `h_tk_knd_nm`, `h_schd_tk_knd_cd`, `h_qrcode`
- 금액/환불/상태: `h_tot_fare_amt`, `h_tot_disc_amt`, `h_tot_rcvd_amt`, `retPsbFlg`, `h_ret_flg`, `h_dlay_flg`, `h_dlay_tk_flg`, `h_trn_running_flg`, `mlgSaveFlg`
- 기능 플래그: `gurdSmsFlg`, `seatAppPsbFlg`, `stndAppPsbFlg`, `tripChgFlg`, `stnLeadFlg`, `addSrvFlg`, `addSrvCancel`, `whchSrvReqPsbFlg`, `whchSrvRcpFlg`, `pbpAcepPsbFlg`, `pbpAcepPsQryFlg`, `h_pbp_acep_tgt_flg`, `limousineRsvPsbFlg`
- 부가 정보: `parkingLotUrl`, `ticketTimeBgColor`, `cstmzPhrase`, `h_abrd_ps_nm`, `h_abrd_ps_sex`, `h_compa_nm`, `h_compa_brth`, `s_brth`, `h_dscp_no`, `h_dtour`
- `ticket_infos.ticket_info[]`: `h_jrny_sqno`, `h_jrny_tp_cd`, `h_trn_no`, `h_trn_gp_cd`, `h_trn_clsf_cd`, `h_trn_clsf_nm`, `h_dpt_dt`, `h_dpt_tm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`, `h_arv_dt`, `h_arv_tm`, `h_arv_rs_stn_cd`, `h_arv_rs_stn_nm`, `h_psrm_cl_cd`, `h_psrm_cl_nm`, `h_plf_no`, `h_menu_actv_flg`, `h_sr_include_yn`, `h_itx_sixed_yn`, `h_dvd_anx_dv_cd`, `cabFaclLead`, `vrBnrUrl`, `tk_seat_info[]`
- `tk_seat_info[]`: `h_srcar_no`, `h_seat_no`, `h_seat_att_cd_2`, `h_seat_att_cd_4`, `h_chckn_stt_cd`, `h_psg_tp_cd`, `h_psg_tp_nm`, `h_dcnt_knd_cd`, `h_dcnt_knd_nm`, `h_buy_ps_nm`, `h_sgr_nm`
- 중첩 목록: `cmpa_info[]`, `psgNmList[]`, `dtlList[]`, `dcnt_crd_info.appSegList[]`, `addSrvList.pnrList[]`, `limousine`

근거:

- `analysis/jadx/sources/com/korail/talk/network/dao/refund/RefundService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/refund/TicketDetailDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationCancelService.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/reservationCancel/RsvCancelCheckDao.java`

## Caller Flows

### 승차권 목록 및 상세 로딩

`TicketListActivity`는 광고 ID 콜백 이후 `TicketListDao`를 만들고 `MyTicketService.getTicketList()`를 호출한다. 요청값은 `txtDeviceId=<광고 ID>`, `txtIndex=1`, `h_page_no=1`, `h_abrd_dt_from/to=""`가 기본이다. 비회원이면 `hiduserYn=N`, `hidName`, `hidTeleNo`, `hidPwd`를 채우고, 회원이면 `hiduserYn=Y`만 설정한다.

목록 응답을 받으면 `TicketListActivity.onReceive()`가 먼저 `IssueList`와 `TicketDetail` 로컬 캐시를 삭제한다. 회원 로그인 상태이고 저장된 로그인 ID가 복호화 가능하면 전체 목록 응답 JSON을 AES 암호화해서 `IssueList`에 저장한다. 이후 `H4.a.getReorderTicketList("1", reservation_list)`로 목록을 재정렬하고, 각 `ReservationList.ticket_list[index]`에 대해 순차적으로 `TicketDetailDao`를 호출한다.

상세 조회는 `RefundService.getTicketDetail()`이다. `TicketListActivity.o1()`은 목록의 첫 `TrainInfo`에서 `h_orgtk_wct_no`, `h_orgtk_ret_sale_dt`, `h_orgtk_sale_sqno`, `h_orgtk_ret_pwd`를 꺼내 `TicketDetailRequest`에 넣고 `h_purchase_history=N`으로 호출한다. 한 PNR의 모든 ticket detail을 모은 뒤 JSON 배열로 직렬화하고, AES 암호화 후 `TicketDetail(pnrNo, ticketDetail)`로 저장한다.

모든 상세 조회가 끝나면 현재 목록 PNR 목록을 기준으로 `SMSData` 테이블을 정리한다. 코드상 `deleteSMSData(list)`는 전달된 PNR 목록에 없는 저장 번호를 삭제하는 방식이다. 이후 UI를 갱신하고, 회원이면 MAAS 상세 목록을 추가 조회한다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/h4/a.java`
- `analysis/jadx/sources/j4/b.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/refund/TicketDetailDao.java`

### 로컬 캐시 복호화 경로

오프라인/캐시성 표시용 helper는 `H4.a.decryptIssueDetailListData(context, pnrNo)`다. 이 함수는 `J4.b.getTicketDetailByPnrNo(pnrNo)`로 `TicketDetail` 레코드를 가져오고, `ticketDetail` 문자열을 `F4.a.decryptAES()`로 복호화한 뒤 `TicketDetailResponse[]`로 JSON 역직렬화한다. 목록 캐시는 `IssueList.issueList`를 같은 방식으로 복호화해서 `TicketListResponse`로 복원한다.

로컬 DB 모델은 다음과 같다.

| Model | DB fields | 용도 |
|---|---|---|
| `TicketDetail` | `id` generated, `pnrNo`, `ticketDetail` | PNR별 상세 응답 JSON 배열을 AES 암호문으로 저장 |
| `SMSData` | `pnrNo` id, `phoneNumber` | 보호자 안심 SMS 수신번호를 AES 암호문으로 저장 |

근거:

- `analysis/jadx/sources/com/korail/talk/database/model/TicketDetail.java`
- `analysis/jadx/sources/com/korail/talk/database/model/SMSData.java`
- `analysis/jadx/sources/h4/a.java`
- `analysis/jadx/sources/j4/b.java`

### 보호자 안심 SMS

`TicketListActivity.moveToGuardianReliefSMS(index)`는 목록의 첫 `TrainInfo`에서 `h_pnr_no`, `h_jrny_sqno`를 읽는다. 먼저 `SMSData(pnrNo)`로 저장된 번호가 있는지 조회한다.

- 저장 번호가 있으면 AES 복호화한 번호를 `GuardianReliefSmsRequest.rcvPsHndyTeln`에 넣어 즉시 `TicketService.gurdSmsSnd()`를 호출한다.
- 저장 번호가 없으면 `GuardianReliefSmsActivity`로 `SMS_DATA`, `SMS_REQUEST` intent extra를 넘긴다. Activity는 전화번호 10자리 이상과 개인정보 동의 체크가 모두 만족될 때 전송 버튼을 활성화한다.
- 전송 성공 시 `GuardianReliefSmsActivity.onReceive()`는 입력 전화번호를 AES 암호화해 `SMSData.phoneNumber`에 저장한 뒤 서버 메시지 텍스트를 다이얼로그로 보여준다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/service/sms/GuardianReliefSmsActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/GuardianReliefSmsDao.java`
- `analysis/jadx/sources/com/korail/talk/database/model/SMSData.java`

### 플랫폼 번호 갱신

`TicketListActivity.onClickUpdatePlatform()`은 선택한 `TicketDetailResponse`에서 원권번호를 `wctNo-saleDt-saleSqno-retPwd` 형태로 만들고, `PlfNoRequest.tkCnt`와 `tkRetNo[]`에 담아 `TicketService.plfNo()`를 호출한다. 응답은 `PlfNoResponse.tkList[].jrnyList[].plfNo` 구조다. Activity는 응답을 어댑터의 `updatePlatform()`에 넘겨 UI를 갱신한다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`

### 셀프 체크인

`TicketSelfCheckinStatusActivity`는 승차권 화면에서 원권번호와 여정번호를 intent extra로 받아 동작한다. 상태 상수는 다음과 같이 고정되어 있다.

| Constant | Value | UI 의미 |
|---|---:|---|
| `CHECKIN_STATUS_NOT_USE` | `01` | 미사용, 시작 버튼 표시 |
| `CHECKIN_STATUS_USING` | `05` | 사용중, 취소 버튼 및 체크인 정보 표시 |
| `CHECKIN_STATUS_CANCEL` | `06` | 취소됨, 재등록 버튼 비활성 |
| `CHECKIN_STATUS_EXCEED` | `14` | 초과 상태 상수만 선언됨; 현재 Activity 분기에서는 별도 UI 분기 없음 |

흐름:

1. `SELF_CHECKIN_STATUS=05`이면 `selfCheckinInfo()`를 호출해 객차/좌석/열차/구간/티켓번호를 표시한다.
2. 미사용 상태에서 시작 버튼을 누르면 ZXing 기반 `TicketSelfCheckinQRScanActivity`를 실행한다.
3. QR scan 결과 문자열을 `qrcode`로 `selfCheckinPossible()`에 보낸다.
4. 응답의 `consList[0]`에서 `cpsNo`, `scarNo`, `seatNo`를 받아 확인 다이얼로그를 표시한다.
5. 확인하면 `selfCheckinRegister(cpsNo, scarNo, seatNo, saleWctNo, saleDd, saleSqno, tkRetPwd, jrnySqno)`를 호출하고 성공 시 Activity를 종료한다.
6. 사용중 상태에서 취소를 선택하면 확인 다이얼로그 후 `selfCheckinCancel()`을 호출하고 성공 시 종료한다.

주의할 점: `TicketSelfCheckinStatusActivity.z0()`은 로그에 `this.f30345q`를 먼저 출력한 뒤 scan 결과를 대입한다. 기능상 호출에는 대입 후 값이 쓰이지만, 로그 문자열은 이전 값일 수 있다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketSelfCheckinStatusActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketSelfCheckinQRScanActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinRegisterDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/SelfCheckinCancelDao.java`

### 중복 승차권 확인

`TicketDuplicationCheckDao`는 `PaymentActivity`에서 결제 시작 전 호출된다. `PaymentActivity.A0()`는 `ReservationResponse`가 있고 결제 유형이 `PAYMENT_TICKET_CHANGE`가 아닌 경우 `pnrNo`로 `TicketService.duplicationCheck()`를 실행한다. `ReservationResponse`가 없거나 결제 유형이 `PAYMENT_TICKET_CHANGE`이면 중복 확인을 건너뛰며, 이 분기에서 `PAYMENT_MAAS`는 `z0()` 결제 진행 호출 없이 반환된다.

`DuplicationCheckResponse.rsvCnt > 0`이면 `payment_duplication_msg` 다이얼로그를 표시한다. `rsvCnt == 0`이면 실제 결제 진행 함수 `z0()`으로 이동한다. 정적 코드상 `rsvCnt`의 서버 의미는 "중복 예약/승차권 수"로만 추론 가능하며, 실제 메시지/서버 응답 본문은 캡처하지 않았다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/payment/PaymentActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java`

### 장치 정보 초기화

`TicketListActivity`는 특정 사용자 동작에서 `DeviceResetDao`를 호출한다. 비회원이면 `teln`, `custNm`, `nonMbPwd`를 채운다. 티켓 종류 코드가 `13`, `81`이 아니면 위치 매니저의 마지막 위치를 읽어 `latitude`, `longitude`, `dptDttm=runDt+dptTm`, `trnNo`를 추가한다. 응답을 받으면 DAO를 취소하고 승차권 목록을 다시 로드하는 흐름으로 이어진다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/DeviceResetDao.java`

### MAAS 부가서비스

승차권 상세 로딩 후 회원 상태이면 `TicketListActivity.k1()`이 `MaasServiceDetailListDao`를 호출한다. 요청 객체를 만들지만 `qryDtFrom`, `qryDtTo`는 해당 호출 지점에서 세팅하지 않는다. 응답의 `addSrvList`가 있으면 MAAS 서비스 목록 UI에 붙는다.

취소 흐름은 두 단계다.

1. `getMaasServiceCancelFee(addSrvReqNo, addSrvDvCd, coptEntRsvNo)`로 취소 수수료 `cncRetFee`를 조회한다.
2. 사용자 확인 후 `getMaasServiceCancel(pnrNo, cncTgtCnt, cncAddSrvReqNo, cncRetFee)`를 호출한다.

`getMaasCancel(custMgNo, lumpStlTgtNo)`도 `TicketService`에 존재하지만, 이번 범위에서 확인한 `TicketListActivity`의 MAAS 서비스 취소 흐름은 `MaasServiceCancelFeeDao`와 `MaasServiceCancelDao` 중심이다. `rsvSpecUrl`이 있는 MAAS 내역은 `IntegrationWebViewActivity`에 `WEB_GET_URL`로 넘겨 상세 웹을 열 수 있고, 영수증은 `ExtraProductWebViewActivity`에 `PRODUCT_MAAS_RECEIPT_URL`과 POST parameter를 넘긴다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasServiceCancelDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/MaasCancelDao.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/MaasAddReservationActivity.java`

### 승차권 변경/좌석 변경

`TicketService.getTripChgDate()`는 `TCBookingActivity`에서 승차권 변경 가능 날짜 정보를 조회하는 데 사용된다. 응답은 `tripChgDates[]`, `lastRunDt`를 가진다.

`TicketService.getSelfSeatChgInfo()`는 `TCSOptionsActivity`에서 호출한다. 요청은 현재 승차권의 운행일, 열차번호, 출발/도착역 코드, 객실 등급을 기반으로 한다. 응답의 `chgRsnList`는 변경 사유 선택지, `chgStnList`는 변경 가능한 출발역/시간과 잔여석 정보를 제공한다. 사용자가 옵션을 선택하면 `SeatSearchActivity`로 `TYPE_TCSO_SEAT_CHANGE`, `SEAT_SEARCH_REQUEST`, 기존 `TICKET_RESPONSE`, `START_STATION_DTO`를 넘긴다. 실제 변경 예약은 이후 좌석조회/예약 흐름에서 처리된다.

`TicketService.ticketChangeCancel()`은 `TCCancelDao`가 감싼다. 요청은 `lumpStlCnt`와 `lumpStlTgtNo_{index}` FieldMap이다. 코드상 이 API는 승차권 변경 처리 취소(`tripChgHndgCnc`) 성격이며, 일반 예약 취소(`ReservationCancel`)나 환불(`RefundsRequest`)과 구분해야 한다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/booking/change/TCBookingActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/change/TCSOptionsActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/ticket/TCCancelDao.java`

### 특실 업그레이드

특실 업그레이드는 `MyTicketService`에 있다. `SpecialRoomUpgradeActivity`는 push payload `MSGVo.param` JSON의 짧은 key를 `PushUpdateRequest`로 변환한다. 예를 들어 `a/b/c/d`는 원권 발매일/창구/일련번호/반환비밀번호로, `e/f`는 여정 유형/번호로, `g~r`은 출도착/열차 정보로 매핑된다. `trnGpCd`는 코드에서 `"100"`으로 고정한다.

사용자는 두 경로 중 하나를 선택한다.

- 좌석 선택: `SeatSearchActivity(TYPE_PUSH)`로 이동하고, 선택 결과의 `tss_srcar_no`, `tss_seat_no`를 `requestUpgradeSeat()`에 넣는다.
- 랜덤 좌석: `scarNo=""`, `seatNo=""`, `rqSeatAttCd=AFTER_DEPARTURE`로 `requestUpgradeSeat()`를 호출한다.

`requestUpgradeSeat()` 성공으로 간주하는 메시지 코드는 `IRT000000`, `MRT200105`다. 응답의 `ticketInfo.scnIndcAmt`, `ticketInfo.totFare`, `jrnys[0].lumpStlTgtNo`로 `procUpgrade()` 결제/차감 요청을 만든다. 이때 `stlMnsCd=12`, `pontDvCd=1`, `pontInpDvCd=1`, `mnsGridcnt=1`, `stlMnsSqno=1`, `ismtMnthNum=0` 등이 코드에서 고정된다. `procUpgrade()` 응답 코드가 `WRTP20000`이면 변경 완료 다이얼로그 후 `navigation_ticket` URI로 승차권 목록을 연다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeProcessDao.java`
- `analysis/jadx/sources/com/korail/talk/network/request/myTicket/PushUpdateRequest.java`

## 중요 상태 머신과 플래그

### 목록/상세 로딩 상태

`TicketListActivity`는 목록을 받은 뒤 상세를 중첩 루프로 순차 조회한다.

- `f30320n`: 현재 `ReservationList` index
- `f30321o`: 현재 reservation 안의 `ticket_list` index
- `f30329w`: 현재 PNR의 상세 응답 목록
- `f30328v`: 모든 PNR의 상세 응답 목록

목록 응답 코드가 `P114`이면 별도 메시지 처리 후 상세 조회로 가지 않는다. 이 코드의 정확한 서버 의미는 정적 분석만으로 확정하지 않았다.

### 셀프 체크인 상태

셀프 체크인 UI는 intent extra `SELF_CHECKIN_STATUS`와 위 상수 4개로 분기한다. 실제 체크인 좌석 상태는 상세 응답의 `TicketSeatInfo.h_chckn_stt_cd`에도 들어오지만, `TicketSelfCheckinStatusActivity`는 전달받은 `SELF_CHECKIN_STATUS`로 초기 UI를 결정한다.

### 기능 플래그

`TicketDetailResponse`와 `TicketListDao.TrainInfo`에는 UI 기능 노출을 제어하는 플래그가 많다. 정적 분석으로 확인한 주요 플래그는 다음이다.

| Field | 확인된 사용 맥락 |
|---|---|
| `gurdSmsFlg` | 보호자 안심 SMS 노출 가능 여부로 추정; 실제 버튼 노출 로직은 adapter/fragment에서 소비 |
| `seatAppPsbFlg`, `stndAppPsbFlg` | 좌석 지정/입석 관련 가능 여부 |
| `tripChgFlg` | 승차권 변경 가능 여부 |
| `retPsbFlg`, `h_ret_flg` | 반환/환불 가능 여부 |
| `addSrvFlg`, `addSrvCancel` | 부가서비스 존재/취소 가능 여부 |
| `pbpAcepPsbFlg`, `pbpAcepPsQryFlg`, `h_pbp_acep_tgt_flg` | 전달받은 승차권/PBP 수락/조회/대상 여부 |
| `limousineRsvPsbFlg` | 리무진 예약 가능 여부 |
| `h_trn_running_flg` | 열차 운행 상태 관련 플래그 |
| `dvcInfoSmnsFlg` | 장치 정보 초기화/소환 관련 플래그로 보이나 정확한 서버 의미는 미확정 |
| `runClsFlg`, `stpvFlg`, `trnSpsFlg`, `srtStnFlg`, `cmtrVlidFlg`, `apdUsrFlg` | 목록 UI의 열차 상태/특수 여정/통근권/부가 사용자 관련 플래그 |

실제 서버 값의 의미표는 APK 안에 명시적 enum으로 존재하지 않는 항목이 많아, 위 설명은 필드명과 소비 맥락에 근거한 제한적 해석이다.

근거:

- `analysis/jadx/sources/com/korail/talk/network/dao/myTicket/TicketListDao.java`
- `analysis/jadx/sources/com/korail/talk/network/dao/refund/TicketDetailDao.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/a.java`

## Local DB / Cache Effects

| Event | Local effect |
|---|---|
| 승차권 목록 응답 수신 | `IssueList` 전체 삭제, `TicketDetail` 전체 삭제 |
| 회원 목록 응답 수신 및 로그인 ID 복호화 가능 | `TicketListResponse` 전체 JSON을 AES 암호화해 `IssueList.issueList`에 저장 |
| 각 PNR 상세 조회 완료 | `TicketDetailResponse[]` JSON을 AES 암호화해 `TicketDetail(pnrNo, ticketDetail)`에 저장 |
| 전체 상세 조회 완료 | 현재 목록 PNR에 없는 `SMSData` 레코드 삭제 |
| 보호자 안심 SMS 신규 번호 전송 성공 | 입력 전화번호 AES 암호화 후 `SMSData(pnrNo, phoneNumber)` insert |
| 캐시 복원 | `IssueList.issueList`, `TicketDetail.ticketDetail`, `SMSData.phoneNumber`를 `F4.a.decryptAES()`로 복호화 |

주의: `insertTicketDetail()`과 `insertSMSData()`는 create 호출이며, 코드상 update/upsert가 아니다. 목록 로딩 시 `TicketDetail`은 선삭제 후 재삽입하므로 중복 가능성이 낮다. `SMSData`는 `pnrNo`가 id인 모델이므로 동일 PNR 재삽입 실패 가능성은 ORMLite 예외 처리에 맡겨진다.

근거:

- `analysis/jadx/sources/j4/b.java`
- `analysis/jadx/sources/h4/a.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/service/sms/GuardianReliefSmsActivity.java`
- `analysis/jadx/sources/com/korail/talk/database/model/TicketDetail.java`
- `analysis/jadx/sources/com/korail/talk/database/model/SMSData.java`

## WebView / App Handoff

승차권 영역은 Retrofit 호출 후 여러 화면/웹뷰로 handoff한다.

| Handoff | Trigger / data | Target |
|---|---|---|
| MAAS 예약 상세 URL | `AddSrvItem.rsvSpecUrl` | `IntegrationWebViewActivity` with `WEB_GET_URL` |
| MAAS 영수증 | `PRODUCT_MAAS_RECEIPT_URL`, `addSrvReqNo`, PNR 여부에 따른 POST parameter | `ExtraProductWebViewActivity` |
| MAAS 추가 예약 | `PARAM_MAAS_ADD_SRV_REQ_NO` | `MaasAddReservationActivity`; 내부에서 상품 URL을 `WEB_POST_URL`로 열 수 있음 |
| SRT 환승/연계 예약 | `SRT_WEB_RESERVATION_URL + "web/reserve"`, JSON body | `IntegrationWebViewActivity` with `WEB_POST_JSON_BODY`, `IS_SRT_WEB_RESERVE=true` |
| 열차 서비스/안내 | `WEB_POST_URL`, `WEB_POST_URL_2` 또는 `TRAIN_INFO` | `TrainServiceWebViewActivity`, `TrainServiceInfoWebViewActivity` |
| 승무원 호출 | 원권번호, 여정번호, 자유석 여부 | `CallCrewActivity` |
| 보호자 안심 SMS 번호 입력 | `SMS_DATA`, `SMS_REQUEST` | `GuardianReliefSmsActivity` |
| 셀프 체크인 | 원권번호, 여정번호, 상태값 | `TicketSelfCheckinStatusActivity`; QR scan은 `TicketSelfCheckinQRScanActivity` |
| 특실 업그레이드 좌석 선택 | `TYPE_PUSH`, `SEAT_SEARCH_REQUEST` | `SeatSearchActivity` |
| 특실 업그레이드 완료 | `navigation_ticket` URI | 승차권 목록 navigation |
| 변경 결제 | `PAYMENT_TYPE`, `PAYMENT_REQUEST`, `COMMON_RESERVATION_RESPONSE` | `PaymentActivity` |

`BaseWebViewActivity`는 `WEB_GET_URL`/`WEB_POST_URL`, `WEB_GET_PARAMETER`/`WEB_POST_PARAMETER`, `WEB_POST_JSON_BODY`를 처리하고 기본 파라미터를 붙일 수 있다. 이 딥다이브 범위의 WebView handoff는 대부분 URL/POST extra를 넘기는 방식이며, `TicketService` 응답 자체가 WebView HTML을 직접 반환하는 구조는 확인하지 못했다.

근거:

- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/TicketListActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/confirm/MaasAddReservationActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/push/SpecialRoomUpgradeActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/ticket/change/TCSOptionsActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/BaseWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceWebViewActivity.java`
- `analysis/jadx/sources/com/korail/talk/ui/web/TrainServiceInfoWebViewActivity.java`

## 검증 한계

- 서버 응답 샘플을 만들거나 호출하지 않았다. 위 필드는 정적 DTO 정의와 호출부만 근거로 한다.
- 일부 플래그의 정확한 서버 값 의미는 앱에 명시 enum/주석이 없어 필드명과 UI 분기로만 제한적으로 해석했다.
- `TicketService`의 MAAS 결제 전체 취소 `getMaasCancel()`은 인터페이스/DAO는 확인했지만, 이번 범위의 주요 `TicketListActivity` 흐름에서는 서비스 취소 수수료 조회/취소가 중심이었다.
- `docs/api-endpoints.md`의 자동 추출 표는 상수 기반 `@Field` 일부를 생략해 보일 수 있어, 최종 request field는 서비스 인터페이스 원문을 우선했다.
