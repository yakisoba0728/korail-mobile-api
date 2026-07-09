# Network Request/Response Model Field Catalog

Generated from `analysis/jadx/sources/com/korail/talk/network`; field rows: **2566**.

This is a static schema catalog from Java fields and Gson annotations. Actual server values were not fetched.

## `BaseDao`

- Source: `com/korail/talk/network/BaseDao.java`
- Extends: `ExecuteDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mBaseRequest` | `BaseRequest` | `` | 8 |
| `mBaseResponse` | `BaseResponse` | `` | 9 |
| `mIBase` | `IBase` | `` | 10 |
| `mIBaseResult` | `IBaseResult` | `` | 11 |
| `mIsNotShowDialog` | `boolean` | `` | 12 |
| `mIsViewFinish` | `boolean` | `` | 13 |
| `mIsCancelable` | `boolean` | `` | 14 |
| `mMacroErrorMsg` | `String` | `` | 15 |
| `mErrorMsgCdList` | `List<String>` | `` | 17 |

## `BaseDaoHelper`

- Source: `com/korail/talk/network/BaseDaoHelper.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mHttpTask` | `HttpTask` | `` | 22 |
| `mDao` | `IBaseDao` | `` | 25 |

## `BaseRequest`

- Source: `com/korail/talk/network/BaseRequest.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ANDROID` | `String` | `` | 7 |
| `APP_KEY` | `String` | `` | 8 |
| `VERSION` | `String` | `` | 9 |
| `device` | `String` | `` | 10 |
| `key` | `String` | `` | 11 |
| `version` | `String` | `` | 12 |

## `BaseResponse`

- Source: `com/korail/talk/network/BaseResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `FAIL` | `String` | `` | 8 |
| `SUCCESS` | `String` | `` | 9 |
| `hMsgCd` | `String` | `h_msg_cd` | 12 |
| `hMsgTxt` | `String` | `h_msg_txt` | 15 |
| `strResult` | `String` | `strResult` | 18 |

## `NetfunnelDao`

- Source: `com/korail/talk/network/NetfunnelDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mHandler` | `Handler` | `` | 12 |
| `mRunner` | `Runnable` | `` | 14 |

## `AdditionalServiceRequest`

- Source: `com/korail/talk/network/dao/addService/AdditionalServiceDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `JOB_CODE_CANCEL` | `String` | `` | 14 |
| `JOB_CODE_NEW` | `String` | `` | 15 |
| `addSrvId` | `String` | `` | 16 |
| `addSrvReqNo` | `ArrayList<String>` | `` | 17 |
| `cncTgtCnt` | `int` | `` | 18 |
| `helpSrvTgtCnt` | `int` | `` | 19 |
| `jobDbCd` | `String` | `` | 20 |
| `jrnySqno` | `String` | `` | 21 |
| `pnrNo` | `String` | `` | 22 |
| `rcpSqno` | `ArrayList<String>` | `` | 23 |
| `reqQnty` | `int` | `` | 24 |
| `saleDt` | `String` | `` | 25 |
| `saleSqno` | `String` | `` | 26 |
| `saleWctNo` | `String` | `` | 27 |

## `AdditionalServiceResponse`

- Source: `com/korail/talk/network/dao/addService/AdditionalServiceDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `outrec2` | `List<OutRec2>` | `` | 130 |

## `OutRec2`

- Source: `com/korail/talk/network/dao/addService/AdditionalServiceDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stlMnsCd` | `String` | `` | 141 |

## `DealCarBuyRequest`

- Source: `com/korail/talk/network/dao/addService/DealCarBuyDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvCnt` | `int` | `` | 13 |
| `addSrvReqNo` | `ArrayList<String>` | `` | 14 |

## `ExtraProductListRequest`

- Source: `com/korail/talk/network/dao/addService/ExtraProductListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrNo` | `String` | `` | 14 |

## `ExtraProductListResponse`

- Source: `com/korail/talk/network/dao/addService/ExtraProductListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrList` | `List<ExtraProductInfo>` | `` | 29 |

## `HelpSrvCustRequest`

- Source: `com/korail/talk/network/dao/addService/HelpSrvCustDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `f28873A` | `String` | `` | 16 |
| `f28874D` | `String` | `` | 19 |
| `addSrvDvCd` | `String` | `` | 20 |
| `qryDvCd` | `String` | `` | 21 |
| `rcpSqno` | `String` | `` | 22 |
| `reqAddRcpSrvCd` | `List<String>` | `` | 23 |
| `reqAddSrvDvCd` | `List<String>` | `` | 24 |
| `reqCnt` | `int` | `` | 25 |
| `reqCntcChnCont` | `List<String>` | `` | 26 |
| `reqCustNm` | `List<String>` | `` | 27 |
| `saleDt` | `String` | `` | 28 |
| `saleSqno` | `String` | `` | 29 |
| `saleWctNo` | `String` | `` | 30 |

## `HelpSrvCustResponse`

- Source: `com/korail/talk/network/dao/addService/HelpSrvCustDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `reqSpecList` | `List<ReqSpec>` | `` | 125 |

## `ReqSpec`

- Source: `com/korail/talk/network/dao/addService/HelpSrvCustDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addRcpSrvCd` | `String` | `` | 136 |
| `addSrvDvCd` | `String` | `` | 137 |
| `custNm` | `String` | `` | 138 |
| `custTeln` | `String` | `` | 139 |
| `rcpSqno` | `String` | `` | 140 |

## `HelpSrvTkDaoRequest`

- Source: `com/korail/talk/network/dao/addService/HelpSrvTkDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `saleDt` | `String` | `` | 13 |
| `saleSqno` | `String` | `` | 14 |
| `saleWctNo` | `String` | `` | 15 |

## `HelpSrvTkDaoResponse`

- Source: `com/korail/talk/network/dao/addService/HelpSrvTkDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `helpSrvList` | `List<helpSrv>` | `` | 46 |

## `helpSrv`

- Source: `com/korail/talk/network/dao/addService/HelpSrvTkDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvReqNo` | `String` | `` | 57 |
| `addSrvSpotCont` | `String` | `` | 58 |
| `arvEpctTm` | `String` | `` | 59 |
| `helpSrvTgtList` | `List<helpSrvTgt>` | `` | 60 |
| `jrnyInfo300` | `String` | `` | 61 |
| `leadMsgCont` | `String` | `` | 62 |

## `helpSrvTgt`

- Source: `com/korail/talk/network/dao/addService/HelpSrvTkDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 93 |
| `custTeln` | `String` | `` | 94 |

## `AppDataDao`

- Source: `com/korail/talk/network/dao/cache/AppDataDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mIsPending` | `boolean` | `` | 11 |

## `AppDataResponse`

- Source: `com/korail/talk/network/dao/cache/AppDataDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `disability_certification_msg` | `String` | `` | 14 |
| `forSeatIntg` | `String` | `` | 15 |
| `limousine` | `String` | `airportBusMsg` | 18 |
| `railplus_cardinfo` | `String` | `` | 19 |
| `version` | `Version` | `` | 20 |

## `Version`

- Source: `com/korail/talk/network/dao/cache/AppDataDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `AMESSAGE` | `String` | `` | 47 |
| `NEWDVERSION` | `String` | `` | 48 |

## `NoticeResponse`

- Source: `com/korail/talk/network/dao/cache/NoticeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `bbrdId` | `String` | `` | 12 |
| `ptwtSqno` | `String` | `` | 13 |
| `ptwtTtl` | `String` | `` | 14 |

## `AddCartRequest`

- Source: `com/korail/talk/network/dao/cart/AddCartDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidPnrNo` | `String` | `` | 12 |

## `CartInfo`

- Source: `com/korail/talk/network/dao/cart/CartListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 14 |
| `coptEntRsvNo` | `String` | `` | 15 |
| `h_add_srv_mrk_ent_id` | `String` | `` | 16 |
| `h_add_srv_mrk_ent_nm` | `String` | `` | 17 |
| `h_cust_no` | `String` | `` | 18 |
| `h_dpt_dt` | `String` | `` | 19 |
| `h_filler` | `String` | `` | 20 |
| `h_fld_stl_dv` | `String` | `` | 21 |
| `h_gd_nm` | `String` | `` | 22 |
| `h_item_dv_cd` | `String` | `` | 23 |
| `h_item_dv_nm` | `String` | `` | 24 |
| `h_item_sqno` | `String` | `` | 25 |
| `h_jrny_sqno` | `String` | `` | 26 |
| `h_jrny_tp_cd` | `String` | `` | 27 |
| `h_lump_stl_tgt_no` | `String` | `` | 28 |
| `h_pnr_no` | `String` | `` | 29 |
| `h_rcvd_amt` | `String` | `` | 30 |
| `h_rsv_rcp_dt` | `String` | `` | 31 |
| `h_spvs_rs_stn_cd` | `String` | `` | 32 |
| `h_stl_extns_tno` | `String` | `` | 33 |
| `h_stl_lmt_tm` | `String` | `` | 34 |
| `h_stl_mns_allw_val` | `String` | `` | 35 |
| `h_tk_cnt` | `int` | `` | 36 |
| `h_vr_rsv_no` | `String` | `` | 37 |
| `utlClsTm` | `String` | `` | 38 |
| `utlStDt` | `String` | `` | 39 |
| `utlStTm` | `String` | `` | 40 |

## `CartInfos`

- Source: `com/korail/talk/network/dao/cart/CartListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cart_info` | `List<CartInfo>` | `` | 263 |

## `CartListRequest`

- Source: `com/korail/talk/network/dao/cart/CartListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvReqNo` | `String` | `` | 274 |
| `pnrNo` | `String` | `` | 275 |

## `CartListResponse`

- Source: `com/korail/talk/network/dao/cart/CartListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cart_infos` | `CartInfos` | `` | 298 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/cart/CartListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_abrd_dt_from` | `String` | `` | 309 |
| `h_abrd_dt_to` | `String` | `` | 310 |
| `h_cg_ps_id` | `String` | `` | 311 |
| `h_cust_no` | `String` | `` | 312 |
| `h_dv_cd` | `String` | `` | 313 |
| `h_filler` | `String` | `` | 314 |
| `h_intSelectPageNo` | `String` | `` | 315 |
| `h_job_id` | `String` | `` | 316 |
| `h_msg_cd` | `String` | `` | 317 |
| `h_page_no` | `String` | `` | 318 |
| `h_row_cnt` | `String` | `` | 319 |
| `h_spbk_whl_cnt` | `String` | `` | 320 |
| `h_stl_scsn_flg` | `String` | `` | 321 |
| `h_tot_page_cnt` | `String` | `` | 322 |
| `h_ver_no` | `String` | `` | 323 |
| `h_wct_no` | `String` | `` | 324 |
| `h_work_dt` | `String` | `` | 325 |
| `h_work_tm` | `String` | `` | 326 |

## `VerifyMaasStatusRequest`

- Source: `com/korail/talk/network/dao/cart/VerifyMaasStatusDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 12 |
| `addSrvReqNo` | `String` | `` | 13 |
| `coptEntRsvNo` | `String` | `` | 14 |
| `lumpStlTgtNo` | `String` | `` | 15 |
| `seletedPos` | `int` | `` | 16 |

## `CashReceiptIssueRequest`

- Source: `com/korail/talk/network/dao/cashReceipt/CashReceiptIssueDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `apvCnt` | `int` | `` | 13 |
| `athnDmnRcgnNo` | `String` | `` | 14 |
| `cashRcetAthnMtdCd` | `String` | `` | 15 |
| `cashRcetTxnDvCd` | `String` | `` | 16 |
| `lumpStlTgtNo` | `HashMap<String, String>` | `` | 17 |
| `vltIsuFlg` | `String` | `` | 18 |

## `ApplyDisabilityCertificationDaoRequest`

- Source: `com/korail/talk/network/dao/certification/ApplyDisabilityCertificationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidPnrNo` | `String` | `` | 13 |
| `txtJobDvCd0019` | `HashMap<String, String>` | `` | 14 |
| `txtPsgDisc0019Birth` | `HashMap<String, String>` | `` | 15 |
| `txtPsgDisc0019Cnt` | `int` | `` | 16 |
| `txtPsgDisc0019CustNm` | `HashMap<String, String>` | `` | 17 |
| `txtPsgDisc0019Grade` | `HashMap<String, String>` | `` | 18 |
| `txtPsgDisc0019PsDvCd` | `HashMap<String, String>` | `` | 19 |
| `txtPsgDisc0019Sqno` | `HashMap<String, Integer>` | `` | 20 |

## `BixbyReservationRequest`

- Source: `com/korail/talk/network/dao/certification/BixbyReservationDao.java`
- Extends: `ReservationRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `data` | `HashMap<String, String>` | `` | 13 |

## `BusInquiryRequest`

- Source: `com/korail/talk/network/dao/certification/BusReservationListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 13 |
| `dptDt` | `String` | `` | 14 |
| `dptRsStnCd` | `String` | `` | 15 |
| `dptTm` | `String` | `` | 16 |
| `mReservationResponse` | `BusInquiryResponse` | `` | 17 |
| `psrmClCd` | `String` | `` | 18 |
| `rsvSaleDvCd` | `String` | `` | 19 |
| `seatAttCd` | `String` | `` | 20 |
| `trnGpCd` | `String` | `` | 21 |
| `trnNo` | `String` | `` | 22 |

## `BusInquiryResponse`

- Source: `com/korail/talk/network/dao/certification/BusReservationListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fllwPgExt` | `String` | `` | 109 |
| `lgtmShtmDvCd` | `String` | `` | 110 |
| `trainList` | `ArrayList<BusList>` | `` | 111 |

## `BusList`

- Source: `com/korail/talk/network/dao/certification/BusReservationListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDt` | `String` | `` | 142 |
| `arvRsStnCd` | `String` | `` | 143 |
| `arvStnRunOrdr` | `String` | `` | 144 |
| `arvTm` | `String` | `` | 145 |
| `chtnDvCd` | `String` | `` | 146 |
| `dptDt` | `String` | `` | 147 |
| `dptRsStnCd` | `String` | `` | 148 |
| `dptStnRunOrdr` | `String` | `` | 149 |
| `dptTm` | `String` | `` | 150 |
| `gnrmRestSeatNum` | `String` | `` | 151 |
| `ocurDlayTnum` | `String` | `` | 152 |
| `restFresNum` | `String` | `` | 153 |
| `restStndNum` | `String` | `` | 154 |
| `runDt` | `String` | `` | 155 |
| `sprmRestSeatNum` | `String` | `` | 156 |
| `stlbTrnClsfCd` | `String` | `` | 157 |
| `trnGpCd` | `String` | `` | 158 |
| `trnNo` | `String` | `` | 159 |
| `trnOrdNo` | `String` | `` | 160 |
| `ymsAplFlg` | `String` | `` | 161 |

## `BusSeatListRequest`

- Source: `com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 13 |
| `arvStnRunOrdr` | `String` | `` | 14 |
| `dptRsStnCd` | `String` | `` | 15 |
| `dptStnRunOrdr` | `String` | `` | 16 |
| `gdNo` | `String` | `` | 17 |
| `isArrow` | `boolean` | `` | 18 |
| `mReservationResponse` | `SeatListResponse` | `` | 19 |
| `psrmClCd` | `String` | `` | 20 |
| `runDt` | `String` | `` | 21 |
| `seatAttCd` | `String` | `` | 22 |
| `srcarNo` | `String` | `` | 23 |
| `totPsgCnt` | `String` | `` | 24 |
| `trnClsfCd` | `String` | `` | 25 |
| `trnGpCd` | `String` | `` | 26 |
| `trnNo` | `String` | `` | 27 |

## `SeatList`

- Source: `com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dir_seat_att_cd` | `String` | `` | 162 |
| `etc_seat_att_cd` | `String` | `` | 163 |
| `intg_msg` | `String` | `` | 164 |
| `intg_msg_cd` | `String` | `` | 165 |
| `isDisable` | `boolean` | `` | 166 |
| `isSelected` | `boolean` | `` | 167 |
| `rq_seat_att_cd` | `String` | `` | 168 |
| `sale_psb_flg` | `String` | `` | 169 |
| `seat_no` | `String` | `` | 170 |
| `seat_spec` | `String` | `` | 171 |
| `sqr_no` | `String` | `` | 172 |
| `vz_msg_dv_cd` | `String` | `` | 173 |

## `SeatListResponse`

- Source: `com/korail/talk/network/dao/certification/BusReservationSeatListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `car_tp_cd` | `String` | `` | 240 |
| `scar_no` | `String` | `` | 241 |
| `seatList` | `ArrayList<SeatList>` | `` | 242 |
| `seat_ary_cd` | `String` | `` | 243 |
| `up_dn_dv_cd` | `String` | `` | 244 |

## `CongresspersonCertRequest`

- Source: `com/korail/talk/network/dao/certification/CongresspersonCertDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `abrdDt` | `String` | `` | 12 |
| `certNo` | `String` | `` | 13 |
| `freeDiscCertNo` | `String` | `` | 14 |
| `viewIndex` | `int` | `` | 15 |

## `CongresspersonCertResponse`

- Source: `com/korail/talk/network/dao/certification/CongresspersonCertDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `freeDiscCertNo` | `String` | `` | 54 |

## `DisabledCertificationRequest`

- Source: `com/korail/talk/network/dao/certification/DisabledCertificationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hdcpGrade` | `String` | `` | 12 |
| `position` | `int` | `` | 13 |
| `regNum` | `String` | `` | 14 |

## `DisabledCertificationResponse`

- Source: `com/korail/talk/network/dao/certification/DisabledCertificationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `btdt` | `String` | `` | 45 |
| `certificate` | `String` | `` | 46 |
| `hdcpTpCd` | `String` | `` | 47 |
| `subtDcsClCd` | `String` | `` | 48 |

## `DiscountPriceRequest`

- Source: `com/korail/talk/network/dao/certification/DiscountPriceDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dcnt_knd_cd1` | `List<String>` | `` | 13 |
| `hidCustNo` | `String` | `` | 14 |
| `hidDcntKndCd` | `List<String>` | `` | 15 |
| `hidDscpNo` | `List<String>` | `` | 16 |
| `hidFmlyNo` | `List<String>` | `` | 17 |
| `hidPnrNo` | `String` | `` | 18 |
| `hiduserYn` | `String` | `` | 19 |
| `psg_tp_dv_cd` | `List<String>` | `` | 20 |
| `psrm_cl_cd` | `List<String>` | `` | 21 |
| `txtJobId` | `String` | `` | 22 |
| `txtPsgGridcnt` | `String` | `` | 23 |

## `GovernmentCertificationResponse`

- Source: `com/korail/talk/network/dao/certification/GovernmentCertificationStep1Dao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `app` | `String` | `` | 12 |
| `csrfToken` | `String` | `` | 13 |

## `GovernmentCertificationStep1Request`

- Source: `com/korail/talk/network/dao/certification/GovernmentCertificationStep1Dao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hdcpGrade` | `String` | `` | 28 |
| `position` | `int` | `` | 29 |
| `regNum` | `String` | `` | 30 |

## `GovernmentCertificationStep2Request`

- Source: `com/korail/talk/network/dao/certification/GovernmentCertificationStep2Dao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `csrfToken` | `String` | `` | 12 |

## `GovernmentCertificationStep2Response`

- Source: `com/korail/talk/network/dao/certification/GovernmentCertificationStep2Dao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `code` | `String` | `` | 27 |
| `message` | `String` | `` | 28 |
| `pbepInfo` | `String` | `` | 29 |
| `result` | `String` | `` | 30 |
| `txCompleteCode` | `String` | `` | 31 |

## `MeritCertRequest`

- Source: `com/korail/talk/network/dao/certification/MeritCertDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtAbrdDt` | `String` | `` | 12 |
| `txtAcptPwd` | `String` | `` | 13 |
| `txtFreeDiscCertNo` | `String` | `` | 14 |
| `txtJuminNo7` | `String` | `` | 15 |
| `viewIndex` | `int` | `` | 16 |

## `MeritCertResponse`

- Source: `com/korail/talk/network/dao/certification/MeritCertDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_free_acm_use_tno` | `String` | `` | 63 |
| `h_free_disc_cert_no` | `String` | `` | 64 |
| `h_free_psb_tno` | `String` | `` | 65 |

## `TicketRsvInquiryRequest`

- Source: `com/korail/talk/network/dao/certification/TicketRsvInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidPnrNo` | `String` | `` | 12 |

## `Accept`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isCheck` | `String` | `` | 42 |
| `linkUrl` | `String` | `` | 43 |
| `message` | `String` | `` | 44 |

## `Athn`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `athnBtn` | `String` | `` | 63 |
| `cncBtn` | `String` | `` | 64 |
| `isApply` | `String` | `` | 65 |
| `message` | `String` | `` | 66 |
| `title` | `String` | `` | 67 |

## `BuyNow`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isApply` | `String` | `` | 94 |
| `menuTitle` | `String` | `` | 95 |

## `CommonCodeDao`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ANYID` | `String` | `` | 14 |
| `ATHN` | `String` | `` | 15 |
| `BUY_NOW` | `String` | `` | 16 |
| `DATA` | `String` | `` | 17 |
| `DEVICE_OREO` | `String` | `` | 18 |
| `EASY_PAY` | `String` | `` | 19 |
| `HOLIDAY_POPUP` | `String` | `` | 20 |
| `IMAGE_DOWN_LOAD_DATA` | `String` | `` | 21 |
| `IS_NAVER_SHOW` | `String` | `` | 22 |
| `KORAIL_BOSS` | `String` | `` | 23 |
| `LIMOUSINE_MAIN_MSG` | `String` | `` | 24 |
| `LIMOUSINE_MSG` | `String` | `` | 25 |
| `LOGIN` | `String` | `` | 26 |
| `LOST_ARTICLE` | `String` | `` | 27 |
| `MAAS_TEST` | `String` | `` | 28 |
| `MAIN_POPUP` | `String` | `` | 29 |
| `MENU_BIZ` | `String` | `` | 30 |
| `MENU_RAILPOINT` | `String` | `` | 31 |
| `PERIOD_COMMUTATION_DATA` | `String` | `` | 32 |
| `POINT` | `String` | `` | 33 |
| `REPORT` | `String` | `` | 34 |
| `STATION_CD` | `String` | `` | 35 |
| `STATION_NM` | `String` | `` | 36 |
| `STBK_ACCEPT` | `String` | `` | 37 |
| `VIEW_VISIBILITY` | `String` | `` | 38 |
| `mIsPending` | `boolean` | `` | 39 |

## `CommonCodeRequest`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `OSVersion` | `int` | `` | 110 |
| `arrivalDate` | `String` | `` | 111 |
| `codeList` | `List<String>` | `` | 112 |
| `departDate` | `String` | `` | 113 |
| `deviceHeight` | `int` | `` | 114 |
| `deviceWidth` | `int` | `` | 115 |
| `easyPayType` | `String` | `` | 116 |
| `holidayYn` | `String` | `` | 117 |

## `CommonCodeResponse`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `accepts` | `List<Accept>` | `` | 196 |
| `athn` | `Athn` | `` | 199 |
| `buyNow` | `BuyNow` | `` | 202 |
| `data` | `Data` | `` | 205 |
| `deviceOreo` | `DeviceOSPopUp` | `` | 208 |
| `easyPay` | `EasyPay` | `` | 211 |
| `holidayPopup` | `HolidayPopup` | `` | 214 |
| `imageDownLoadData` | `ImageDownLoadData` | `` | 217 |
| `isEasyLoginShow` | `EasyLogin` | `` | 220 |
| `korailBoss` | `KorailBoss` | `` | 223 |
| `limousine` | `String` | `` | 226 |
| `limousineMainMsg` | `String` | `` | 229 |
| `login` | `Login` | `` | 232 |
| `lostArticle` | `LostArticle` | `` | 235 |
| `maasTest` | `String` | `` | 238 |
| `mainPopup` | `MainPopup` | `` | 241 |
| `menuBiz` | `MenuBiz` | `` | 244 |
| `menuRailPoint` | `MenuRailPoint` | `` | 247 |
| `periodCommutationData` | `PeriodCommutationData` | `` | 250 |
| `pointData` | `Point` | `` | 253 |
| `report` | `Report` | `` | 256 |
| `stationCd` | `List<String>` | `` | 259 |
| `stationNm` | `List<String>` | `` | 262 |
| `viewVisibility` | `ViewVisibility` | `` | 265 |

## `Data`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `anyid` | `String` | `` | 368 |
| `anyidUrl` | `String` | `` | 369 |
| `anyidhm` | `String` | `` | 370 |
| `autoRefresh` | `String` | `` | 371 |
| `csChatBot` | `String` | `` | 372 |
| `isMacroEnable` | `String` | `` | 373 |
| `isSrHistoryEnable` | `String` | `` | 374 |
| `knDelivery` | `String` | `` | 375 |
| `knParkingLot` | `String` | `` | 376 |
| `lotteglogisURL` | `String` | `` | 377 |
| `newTabUI1` | `String` | `` | 378 |
| `newTabUI2` | `String` | `` | 379 |
| `srHistoryUrl` | `String` | `` | 380 |
| `suspendMode` | `String` | `` | 381 |

## `DeviceOSPopUp`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isDeploymentStop` | `String` | `` | 448 |
| `message` | `String` | `` | 449 |
| `title` | `String` | `` | 450 |

## `EasyLogin`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isGoogleShow` | `String` | `` | 469 |
| `isKakaoShow` | `String` | `` | 470 |
| `isNaverShow` | `String` | `` | 471 |
| `isOnepassShow` | `String` | `` | 472 |

## `EasyPay`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `list` | `List<EasyPayData>` | `` | 495 |
| `tab` | `int` | `` | 496 |

## `EasyPayData`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `displayType` | `String` | `` | 511 |
| `isEnable` | `String` | `` | 512 |
| `isNeedLogin` | `String` | `` | 513 |
| `linkTitle` | `String` | `` | 514 |
| `linkType` | `String` | `` | 515 |
| `linkUrl` | `String` | `` | 516 |
| `payTitle` | `String` | `` | 517 |
| `payType` | `String` | `` | 518 |

## `HolidayPopup`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `popup` | `String` | `` | 557 |
| `popupAlt` | `String` | `` | 558 |
| `popupImg` | `String` | `` | 559 |
| `popupSchema` | `String` | `` | 560 |
| `popupUrl` | `String` | `` | 561 |
| `subUrl` | `String` | `` | 562 |

## `ImageDownLoadData`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `applyDate` | `String` | `` | 617 |
| `fileSize` | `long` | `` | 618 |
| `isApply` | `String` | `` | 619 |
| `subUrl` | `String` | `` | 620 |
| `textColor` | `String` | `` | 621 |
| `url` | `String` | `` | 622 |

## `KorailBoss`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `name` | `String` | `` | 653 |
| `terms` | `String` | `` | 654 |

## `Login`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `idx` | `String` | `` | 669 |
| `key` | `String` | `` | 670 |
| `pwdAESCphd` | `String` | `` | 671 |

## `LostArticle`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isApply` | `String` | `` | 690 |
| `linkUrl` | `String` | `` | 691 |
| `menuTitle` | `String` | `` | 692 |

## `MainPopup`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `buttonType` | `String` | `` | 711 |
| `checkType` | `int` | `` | 712 |
| `clsBtn` | `String` | `` | 713 |
| `imageUrl` | `String` | `` | 714 |
| `isExternalBrowser` | `String` | `` | 715 |
| `isShow` | `String` | `` | 716 |
| `linkTitle` | `String` | `` | 717 |
| `linkUrl` | `String` | `` | 718 |
| `message` | `String` | `` | 719 |
| `noticeId` | `int` | `` | 720 |
| `size` | `String` | `` | 721 |
| `title` | `String` | `` | 722 |
| `voice` | `String` | `` | 723 |

## `MenuBiz`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isApply` | `String` | `` | 782 |
| `linkUrl` | `String` | `` | 783 |
| `title` | `String` | `` | 784 |

## `MenuRailPoint`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `appScheme` | `String` | `` | 803 |
| `installUrl` | `String` | `` | 804 |
| `isApply` | `String` | `` | 805 |
| `menuTitle` | `String` | `` | 806 |

## `PeriodCommutationData`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `periodCd` | `String` | `` | 829 |
| `periodNm` | `String` | `` | 830 |

## `Point`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `list` | `List<PointData>` | `` | 845 |

## `PointData`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isEnable` | `String` | `` | 856 |
| `isNeedLogin` | `String` | `` | 857 |
| `linkTitle` | `String` | `` | 858 |
| `linkType` | `String` | `` | 859 |
| `linkUrl` | `String` | `` | 860 |
| `pointTitle` | `String` | `` | 861 |
| `pointType` | `String` | `` | 862 |

## `Report`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `enable` | `String` | `` | 897 |
| `title` | `String` | `` | 898 |
| `url` | `String` | `` | 899 |

## `ViewVisibility`

- Source: `com/korail/talk/network/dao/common/CommonCodeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acpnMlgLead` | `String` | `` | 918 |
| `acpnMlgSave` | `String` | `` | 919 |
| `centralInlandMap` | `String` | `` | 920 |
| `checkIn` | `String` | `` | 921 |
| `crmNty` | `String` | `` | 922 |
| `dlfeCashRfn` | `String` | `` | 923 |
| `giftTicket` | `String` | `` | 924 |
| `hearingImpaired` | `String` | `` | 925 |
| `hearingImpairedExps` | `String` | `` | 926 |
| `mbSced` | `String` | `` | 927 |
| `mbilPbepAthn` | `String` | `` | 928 |
| `wheelchair` | `String` | `` | 929 |

## `RsvWaitResponse`

- Source: `com/korail/talk/network/dao/common/CookieDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mutMrkVrfCd` | `String` | `` | 12 |

## `DecryptRequest`

- Source: `com/korail/talk/network/dao/common/DecryptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `easyPayType` | `String` | `` | 13 |
| `mAutoChargeRequestType` | `String` | `` | 14 |
| `type` | `String` | `` | 15 |
| `valueList` | `List<String>` | `` | 16 |

## `DecryptResponse`

- Source: `com/korail/talk/network/dao/common/DecryptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `decValueList` | `List<DecryptValueList>` | `` | 55 |

## `DecryptValueList`

- Source: `com/korail/talk/network/dao/common/DecryptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `decValue` | `String` | `` | 66 |

## `EncryptRequest`

- Source: `com/korail/talk/network/dao/common/EncryptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `type` | `String` | `` | 13 |
| `valueList` | `List<String>` | `` | 14 |

## `EncryptResponse`

- Source: `com/korail/talk/network/dao/common/EncryptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `encValueList` | `List<EncryptValueList>` | `` | 37 |

## `EncryptValueList`

- Source: `com/korail/talk/network/dao/common/EncryptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `encValue` | `String` | `` | 48 |

## `KBpayEncryptRequest`

- Source: `com/korail/talk/network/dao/common/KBPayEncryptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `type` | `String` | `` | 14 |
| `valueList` | `List<String>` | `` | 15 |

## `KBpayEncryptResponse`

- Source: `com/korail/talk/network/dao/common/KBPayEncryptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `BIZ_NUM` | `String` | `` | 38 |
| `CHANNEL_ID` | `String` | `` | 39 |
| `PURCHASE_PRODUCT_INFO` | `String` | `` | 40 |
| `REQ_DATE_TIME` | `String` | `` | 41 |
| `SELLER_NAME` | `String` | `` | 42 |
| `SELLER_NUM` | `String` | `` | 43 |
| `encValueList` | `List<EncryptDao.EncryptValueList>` | `` | 44 |

## `MaasMenuListResponse`

- Source: `com/korail/talk/network/dao/common/MaasMenuListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `menuList` | `List<Menu>` | `` | 22 |

## `MaasMenuRequest`

- Source: `com/korail/talk/network/dao/common/MaasMenuListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvReqNo` | `String` | `` | 61 |
| `pnrNo` | `String` | `` | 62 |
| `tkRetNo` | `ArrayList<String>` | `` | 63 |

## `Menu`

- Source: `com/korail/talk/network/dao/common/MaasMenuListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `active` | `String` | `` | 94 |
| `addSrvDvCd` | `String` | `` | 95 |
| `appData` | `String` | `` | 96 |
| `iconOff` | `String` | `` | 97 |
| `iconOn` | `String` | `` | 98 |
| `info` | `String` | `` | 99 |
| `login` | `String` | `` | 100 |
| `name` | `String` | `` | 101 |
| `poppImg` | `String` | `` | 102 |
| `type` | `String` | `` | 103 |
| `url` | `String` | `` | 104 |

## `MaasStationListRequest`

- Source: `com/korail/talk/network/dao/common/MaasStationListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 12 |

## `EncValueList`

- Source: `com/korail/talk/network/dao/common/SeedEncryptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `encValue` | `String` | `` | 13 |

## `SeedEncryptRequest`

- Source: `com/korail/talk/network/dao/common/SeedEncryptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mValueList` | `List<String>` | `` | 24 |

## `SeedEncryptResponse`

- Source: `com/korail/talk/network/dao/common/SeedEncryptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `encValueList` | `List<EncValueList>` | `` | 39 |

## `STN`

- Source: `com/korail/talk/network/dao/common/StationDataDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `group` | `String` | `` | 12 |
| `latitude` | `String` | `` | 13 |
| `longitude` | `String` | `` | 14 |
| `major` | `String` | `` | 15 |
| `popupLinkTitle` | `String` | `` | 16 |
| `popupLinkUrl` | `String` | `` | 17 |
| `popupMessage` | `String` | `` | 18 |
| `popupType` | `int` | `` | 19 |
| `stn_cd` | `String` | `` | 20 |
| `stn_nm` | `String` | `` | 21 |

## `STNSetter`

- Source: `com/korail/talk/network/dao/common/StationDataDao.java`
- Extends: `STN`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `setterType` | `int` | `` | 65 |

## `STNs`

- Source: `com/korail/talk/network/dao/common/StationDataDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stn` | `List<STN>` | `` | 117 |

## `StationDataResponse`

- Source: `com/korail/talk/network/dao/common/StationDataDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stns` | `STNs` | `` | 128 |

## `StationInfoResponse`

- Source: `com/korail/talk/network/dao/common/StationInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `count` | `int` | `` | 12 |
| `map_version` | `String` | `` | 13 |

## `QRLocationRequest`

- Source: `com/korail/talk/network/dao/common/authQRLocationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `latitude` | `String` | `` | 12 |
| `longitude` | `String` | `` | 13 |
| `qrcode` | `String` | `` | 14 |

## `QRLocationResponse`

- Source: `com/korail/talk/network/dao/common/authQRLocationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jobScsFlg` | `String` | `` | 45 |

## `CompensateRefundCheckRequest`

- Source: `com/korail/talk/network/dao/compensate/CompensateRefundCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyStpTkFlg` | `List<String>` | `` | 13 |
| `ogTkRetPwd` | `List<String>` | `` | 14 |
| `ogTkSaleDd` | `List<String>` | `` | 15 |
| `ogTkSaleSqNo` | `List<String>` | `` | 16 |
| `ogTkSaleWctNo` | `List<String>` | `` | 17 |
| `tkCnt` | `int` | `` | 18 |
| `trnStpRsStnCd` | `List<String>` | `` | 19 |

## `CompensateRefundRequest`

- Source: `com/korail/talk/network/dao/compensate/CompensateRefundDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyStpTkFlg` | `List<String>` | `` | 13 |
| `ogTkRetPwd` | `List<String>` | `` | 14 |
| `ogTkSaleDd` | `List<String>` | `` | 15 |
| `ogTkSaleSqNo` | `List<String>` | `` | 16 |
| `ogTkSaleWctNo` | `List<String>` | `` | 17 |
| `tkCnt` | `int` | `` | 18 |
| `trnStpRsStnCd` | `List<String>` | `` | 19 |

## `CompensateRefundListRequest`

- Source: `com/korail/talk/network/dao/compensate/CompensateRefundListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptDtFrom` | `String` | `` | 13 |
| `dptDtTo` | `String` | `` | 14 |
| `nowPgNo` | `int` | `` | 15 |

## `Fmly`

- Source: `com/korail/talk/network/dao/cust/MchdDcntTgtDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `btdt` | `String` | `` | 13 |
| `custFmlyNm` | `String` | `` | 14 |
| `dcntKndCd` | `String` | `` | 15 |
| `fmlySqno` | `String` | `` | 16 |
| `psgTpCd` | `String` | `` | 17 |
| `psgTpNm` | `String` | `` | 18 |
| `psrmClCd` | `String` | `` | 19 |
| `rqDcntKndCd` | `String` | `` | 20 |

## `MchdDcntTgtRequest`

- Source: `com/korail/talk/network/dao/cust/MchdDcntTgtDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptDt` | `String` | `` | 67 |

## `MchdDcntTgtResponse`

- Source: `com/korail/talk/network/dao/cust/MchdDcntTgtDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fmlyList` | `List<Fmly>` | `` | 82 |

## `CashRfnDao`

- Source: `com/korail/talk/network/dao/delay/CashRfnDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `f28875A` | `String` | `` | 12 |
| `f28876B` | `String` | `` | 15 |
| `f28877I` | `String` | `` | 18 |

## `CashRfnRequest`

- Source: `com/korail/talk/network/dao/delay/CashRfnDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 21 |
| `custTeln` | `String` | `` | 22 |
| `dmnPrsDvCd` | `String` | `` | 23 |
| `dptnAcntNo` | `String` | `` | 24 |
| `dptnBankCd` | `String` | `` | 25 |
| `rmk1Cont` | `String` | `` | 26 |
| `saleDd` | `String` | `` | 27 |
| `saleSqno` | `String` | `` | 28 |
| `saleWctNo` | `String` | `` | 29 |
| `tkRetPwd` | `String` | `` | 30 |

## `CashRfnResponse`

- Source: `com/korail/talk/network/dao/delay/CashRfnDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `rfnAmt` | `String` | `` | 117 |

## `DelayCertificateRequest`

- Source: `com/korail/talk/network/dao/delay/DelayCertificateDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ogTkRetPwd` | `String` | `` | 13 |
| `ogTkSaleDd` | `String` | `` | 14 |
| `ogTkSaleSqNo` | `String` | `` | 15 |
| `ogTkSaleWctNo` | `String` | `` | 16 |
| `runDt` | `String` | `` | 17 |
| `trnNo` | `String` | `` | 18 |

## `DelayCertificateResponse`

- Source: `com/korail/talk/network/dao/delay/DelayCertificateDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayList` | `List<DelayInfo>` | `` | 73 |

## `DelayInfo`

- Source: `com/korail/talk/network/dao/delay/DelayCertificateDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 84 |
| `arvRsStnNm` | `String` | `` | 85 |
| `dlayArvFlg` | `String` | `` | 86 |
| `dptRsStnCd` | `String` | `` | 87 |
| `runDay` | `String` | `` | 88 |
| `runDt` | `String` | `` | 89 |
| `trnDlayTm` | `String` | `` | 90 |
| `trnNo` | `String` | `` | 91 |

## `DelayPNRAcceptDao`

- Source: `com/korail/talk/network/dao/delay/DelayPNRAcceptDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `JOB_DV_CD_RESERVATION` | `String` | `` | 11 |
| `JOB_DV_CD_TICKET_CHANGE` | `String` | `` | 12 |

## `DelayPNRAcceptRequest`

- Source: `com/korail/talk/network/dao/delay/DelayPNRAcceptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jobDvCd` | `String` | `` | 15 |
| `ogtkWctNo` | `List<String>` | `` | 16 |
| `pnrCnt` | `int` | `` | 17 |
| `pnrList` | `List<String>` | `` | 18 |

## `Delay`

- Source: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayAcptFlg` | `String` | `` | 15 |
| `jrnyOrdr` | `String` | `` | 16 |
| `jrnyTpCd` | `String` | `` | 17 |
| `runDt` | `String` | `` | 18 |
| `trnNo` | `String` | `` | 19 |

## `DelayPNRQueryDao`

- Source: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `JOB_DV_CD_RESERVATION` | `String` | `` | 11 |
| `JOB_DV_CD_TICKET_CHANGE` | `String` | `` | 12 |

## `DelayPNRQueryRequest`

- Source: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jobDvCd` | `String` | `` | 46 |
| `ogtkWctNoList` | `List<String>` | `` | 47 |
| `pnrCnt` | `int` | `` | 48 |
| `pnrList` | `List<String>` | `` | 49 |

## `DelayPNRQueryResponse`

- Source: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mainList` | `List<Main>` | `` | 88 |

## `Main`

- Source: `com/korail/talk/network/dao/delay/DelayPNRQueryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayList` | `List<Delay>` | `` | 99 |
| `pnrNo` | `String` | `` | 100 |

## `DelayRefundCheckRequest`

- Source: `com/korail/talk/network/dao/delay/DelayRefundCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ogTkRetPwd` | `List<String>` | `` | 13 |
| `ogTkSaleDd` | `List<String>` | `` | 14 |
| `ogTkSaleSqNo` | `List<String>` | `` | 15 |
| `ogTkSaleWctNo` | `List<String>` | `` | 16 |
| `tkCnt` | `int` | `` | 17 |

## `DelayRefundRequest`

- Source: `com/korail/talk/network/dao/delay/DelayRefundDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayFarePymtMtdCd` | `String` | `` | 13 |
| `ogTkRetPwd` | `List<String>` | `` | 14 |
| `ogTkSaleDd` | `List<String>` | `` | 15 |
| `ogTkSaleSqNo` | `List<String>` | `` | 16 |
| `ogTkSaleWctNo` | `List<String>` | `` | 17 |
| `tkCnt` | `int` | `` | 18 |

## `DelayRefundListRequest`

- Source: `com/korail/talk/network/dao/delay/DelayRefundListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptDtFrom` | `String` | `` | 13 |
| `dptDtTo` | `String` | `` | 14 |
| `nowPgNo` | `int` | `` | 15 |

## `DelayReturnReceiptRequest`

- Source: `com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `saleDd` | `String` | `` | 12 |
| `saleSqno` | `String` | `` | 13 |
| `saleWctNo` | `String` | `` | 14 |
| `tkRetPwd` | `String` | `` | 15 |

## `DelayReturnReceiptResponse`

- Source: `com/korail/talk/network/dao/delay/DelayReturnReceiptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayFarePymtMtdNm` | `String` | `` | 54 |
| `dlayFareRetAmt` | `String` | `` | 55 |
| `retDt` | `String` | `` | 56 |

## `DptnBank`

- Source: `com/korail/talk/network/dao/delay/DptnBankDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptnBankCd` | `String` | `` | 14 |
| `dptnBankNm` | `String` | `` | 15 |

## `DptnBankResponse`

- Source: `com/korail/talk/network/dao/delay/DptnBankDao.java`
- Extends: `RefundResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptnBank` | `List<DptnBank>` | `` | 30 |

## `TicketPresentDao`

- Source: `com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `DEFAULT_HID_INFO_INP_DV_CD` | `String` | `` | 13 |
| `KAKAO_HID_INFO_INP_DV_CD` | `String` | `` | 14 |
| `SMS_HID_INFO_INP_DV_CD` | `String` | `` | 15 |
| `SALE_WCT_NO` | `String` | `` | 18 |
| `SALE_DT` | `String` | `` | 19 |
| `SALE_SQ_NO` | `String` | `` | 20 |
| `SALE_RETURN_PWD` | `String` | `` | 21 |

## `TicketPresentRequest`

- Source: `com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidAcepPsNm` | `String` | `` | 60 |
| `hidAcepPsTeln` | `String` | `` | 61 |
| `hidAcepPwd` | `String` | `` | 62 |
| `hidInfoInpDvCd` | `String` | `` | 63 |
| `hidPbpAcepPsCustMgNo` | `String` | `` | 64 |
| `hidPbpAcepPsMbFlg` | `String` | `` | 65 |
| `hidPnrNo` | `String` | `` | 66 |
| `hidRsvChgNo` | `String` | `` | 67 |
| `hidSaleCnt` | `String` | `` | 68 |
| `hidTotNewStlAmt` | `String` | `` | 69 |
| `ticketPresentParams` | `TicketPresentParams` | `` | 70 |

## `TicketPresentResponse`

- Source: `com/korail/talk/network/dao/giftInfo/TicketPresentDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chgePbpRsvNo` | `String` | `` | 162 |

## `GifticketBookingRequest`

- Source: `com/korail/talk/network/dao/gifticket/GifticketBookingDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `gdUtlPsNm` | `String` | `` | 12 |
| `itmCnt` | `String` | `` | 13 |
| `mbCrdNo` | `String` | `` | 14 |
| `mrkAmt` | `String` | `` | 15 |
| `prnbCnt` | `String` | `` | 16 |

## `GifticketBookingResponse`

- Source: `com/korail/talk/network/dao/gifticket/GifticketBookingDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `lumpStlTgtNo` | `String` | `` | 63 |
| `prsCnqeVal` | `String` | `` | 64 |
| `rcvdAmt` | `String` | `` | 65 |

## `GifticketDetailData`

- Source: `com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dataDvCd` | `String` | `` | 14 |
| `rmkCont` | `String` | `` | 15 |
| `stlNo` | `String` | `` | 16 |
| `stlSqno` | `String` | `` | 17 |
| `txnAmt` | `String` | `` | 18 |
| `txnDt` | `String` | `` | 19 |

## `GifticketHistoryRequest`

- Source: `com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `qryNum` | `String` | `` | 50 |
| `tkId` | `String` | `` | 51 |

## `GifticketHistoryResponse`

- Source: `com/korail/talk/network/dao/gifticket/GifticketHistoryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fllwQryFlg` | `String` | `` | 70 |
| `qryCnt` | `String` | `` | 71 |
| `txnList` | `List<GifticketDetailData>` | `` | 72 |

## `GifticketInfo`

- Source: `com/korail/talk/network/dao/gifticket/GifticketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `intgCustNm1` | `String` | `` | 14 |
| `intgCustNm2` | `String` | `` | 15 |
| `nowPontValNum` | `String` | `` | 16 |
| `rcvDt` | `String` | `` | 17 |
| `retAmt` | `String` | `` | 18 |
| `retDt` | `String` | `` | 19 |
| `retTm` | `String` | `` | 20 |
| `tkId` | `String` | `` | 21 |
| `txnAmt` | `String` | `` | 22 |
| `useClsDt` | `String` | `` | 23 |
| `usePontValNum` | `String` | `` | 24 |
| `usePsbFlg` | `String` | `` | 25 |

## `GifticketListRequest`

- Source: `com/korail/talk/network/dao/gifticket/GifticketListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `abrdDtFrom` | `String` | `` | 80 |
| `abrdDtTo` | `String` | `` | 81 |
| `fllwQryFlg` | `String` | `` | 82 |
| `qryDvCd` | `String` | `` | 83 |
| `qryNumNext` | `String` | `` | 84 |
| `qryVal` | `String` | `` | 85 |
| `trnOprBzDvCd` | `String` | `` | 86 |
| `usePsbFlg` | `String` | `` | 87 |

## `GifticketListResponse`

- Source: `com/korail/talk/network/dao/gifticket/GifticketListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `gdList` | `List<GifticketInfo>` | `` | 158 |
| `qryCnt` | `String` | `` | 159 |
| `qryNumNext` | `String` | `` | 160 |

## `GifticketReturnRequest`

- Source: `com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkId` | `String` | `` | 12 |

## `GifticketReturnResponse`

- Source: `com/korail/talk/network/dao/gifticket/GifticketReturnDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `prsFlg` | `String` | `` | 27 |

## `AutoLoginDao`

- Source: `com/korail/talk/network/dao/login/AutoLoginDao.java`
- Extends: `LoginDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mIsPending` | `boolean` | `` | 7 |

## `LoginAthnRegRequest`

- Source: `com/korail/talk/network/dao/login/LoginAthnRegDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custId` | `String` | `` | 12 |
| `lognTpCd` | `String` | `` | 13 |

## `LoginAthnRmvRequest`

- Source: `com/korail/talk/network/dao/login/LoginAthnRmvDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `lognTpCd` | `String` | `` | 12 |
| `srvQryDvVal` | `String` | `` | 13 |

## `LoginRequest`

- Source: `com/korail/talk/network/dao/login/LoginDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `checkValidPw` | `String` | `` | 13 |
| `custId` | `String` | `` | 14 |
| `etrPath` | `String` | `` | 15 |
| `idx` | `String` | `` | 16 |
| `loginId` | `String` | `` | 17 |
| `loginPw` | `String` | `` | 18 |
| `loginType` | `String` | `` | 19 |

## `LoginResponse`

- Source: `com/korail/talk/network/dao/login/LoginDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `coupClsFlg` | `String` | `` | 82 |
| `dlayDscpInfo` | `String` | `` | 83 |
| `encryptCustNo` | `String` | `` | 84 |
| `encryptHMbCrdNo` | `String` | `` | 85 |
| `encryptMbCrdNo` | `String` | `` | 86 |
| `intgFlg` | `String` | `` | 87 |
| `intgMsgTxt` | `String` | `` | 88 |
| `intgUrl` | `String` | `` | 89 |
| `notiTpCd` | `String` | `` | 90 |
| `strAthnFlg5` | `String` | `` | 91 |
| `strAthnFlg7` | `String` | `` | 92 |
| `strBtdt` | `String` | `` | 93 |
| `strCpNo` | `String` | `` | 94 |
| `strCustClCd` | `String` | `` | 95 |
| `strCustDvCd` | `String` | `` | 96 |
| `strCustLeadFlg` | `String` | `` | 97 |
| `strCustMgSrtCd` | `String` | `` | 98 |
| `strCustNm` | `String` | `` | 99 |
| `strCustNo` | `String` | `` | 100 |
| `strCustSrtCd` | `String` | `` | 101 |
| `strEmailAdr` | `String` | `` | 102 |
| `strHdcpFlg` | `String` | `` | 103 |
| `strHdcpTpCd` | `String` | `` | 104 |
| `strHdcpTpCdNm` | `String` | `` | 105 |
| `strLognTpCd6` | `String` | `` | 106 |
| `strMbCrdNo` | `String` | `` | 107 |
| `strRedirectUrl` | `String` | `` | 108 |
| `strSubtDcsClCd` | `String` | `` | 109 |
| `strYouthAgrFlg` | `String` | `` | 110 |

## `MemberCertRequest`

- Source: `com/korail/talk/network/dao/login/MemberCertDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acept` | `String` | `` | 12 |
| `memNum` | `String` | `` | 13 |
| `txtAcptPsNm` | `String` | `` | 14 |
| `txtCpNo` | `String` | `` | 15 |
| `txtEmailNo` | `String` | `` | 16 |

## `MemberCertResponse`

- Source: `com/korail/talk/network/dao/login/MemberCertDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mbCrdNo` | `String` | `` | 63 |
| `strCustNo` | `String` | `` | 64 |

## `MemberCheckRequest`

- Source: `com/korail/talk/network/dao/login/MemberCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 12 |
| `hmpgPwd` | `String` | `` | 13 |

## `AcpnMlgNotiRequest`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgNotiDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `rcvPsHndyTeln` | `String` | `` | 12 |
| `retPwd` | `String` | `` | 13 |
| `saleDt` | `String` | `` | 14 |
| `saleSqno` | `String` | `` | 15 |
| `saleWctNo` | `String` | `` | 16 |

## `AcpnMlgSaveRequest`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSaveDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 12 |
| `mlgAcmMbCrdNo` | `String` | `` | 13 |
| `rsvMbCrdNo` | `String` | `` | 14 |
| `saleDd` | `String` | `` | 15 |
| `saleSqno` | `String` | `` | 16 |
| `saleWctNo` | `String` | `` | 17 |
| `tkRetPwd` | `String` | `` | 18 |

## `AcpnMlgSpecRequest`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrNo` | `String` | `` | 14 |

## `AcpnMlgSpecResponse`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkList` | `List<Ticket>` | `` | 29 |

## `Jrny`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqno` | `String` | `` | 40 |
| `jrnyTpCd` | `String` | `` | 41 |
| `psrmClCd` | `String` | `` | 42 |
| `psrmClNm` | `String` | `` | 43 |
| `seatList` | `List<Seat>` | `` | 44 |

## `Seat`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mlgSaveFlg` | `String` | `` | 71 |
| `mlgSaveTgt` | `String` | `` | 72 |
| `psgTpDvCd` | `String` | `` | 73 |
| `psgTpDvNm` | `String` | `` | 74 |
| `scarNo` | `String` | `` | 75 |
| `seatNo` | `String` | `` | 76 |
| `seatSpec` | `String` | `` | 77 |

## `Ticket`

- Source: `com/korail/talk/network/dao/mileage/AcpnMlgSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyList` | `List<Jrny>` | `` | 112 |
| `mbCrdNo` | `String` | `` | 113 |
| `rsvPsHndyTeln` | `String` | `` | 114 |
| `rsvPsNm` | `String` | `` | 115 |
| `saleDt` | `String` | `` | 116 |
| `saleSqno` | `String` | `` | 117 |
| `saleWctNo` | `String` | `` | 118 |
| `tkRetPwd` | `String` | `` | 119 |

## `Jrnys`

- Source: `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `lumpStlTgtNo` | `String` | `` | 13 |

## `SpecialRoomUpgradeResponse`

- Source: `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnys` | `List<Jrnys>` | `` | 24 |
| `ticketInfo` | `TicketInfo` | `` | 25 |

## `TicketInfo`

- Source: `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 40 |
| `scnIndcAmt` | `String` | `` | 41 |
| `totFare` | `String` | `` | 42 |

## `SpecialRoomUpgradeProcessRequest`

- Source: `com/korail/talk/network/dao/myTicket/SpecialRoomUpgradeProcessDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `crdInpWayCd` | `String` | `` | 12 |
| `feeProyStlSqno` | `String` | `` | 13 |
| `ismtMnthNum` | `String` | `` | 14 |
| `lumpStlTgtNo` | `String` | `` | 15 |
| `mnsGridcnt` | `String` | `` | 16 |
| `mnsStlAmt` | `String` | `` | 17 |
| `pontDvCd` | `String` | `` | 18 |
| `pontInpDvCd` | `String` | `` | 19 |
| `prepCrdTxnAftAmt` | `String` | `` | 20 |
| `prepCrdTxnBfAmt` | `String` | `` | 21 |
| `stlMnsCd` | `String` | `` | 22 |
| `stlMnsSqno` | `String` | `` | 23 |
| `totCncRetAmt` | `String` | `` | 24 |
| `totCncRetFee` | `String` | `` | 25 |
| `totTxnAmt` | `String` | `` | 26 |

## `ReservationList`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ticket_list` | `List<TicketList>` | `` | 15 |

## `TicketList`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `train_info` | `List<TrainInfo>` | `` | 30 |

## `TicketListDao`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `isPending` | `boolean` | `` | 12 |

## `TicketListRequest`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hAbrdDtFrom` | `String` | `` | 45 |
| `hAbrdDtTo` | `String` | `` | 46 |
| `hPageNo` | `String` | `` | 47 |
| `hidName` | `String` | `` | 48 |
| `hidPwd` | `String` | `` | 49 |
| `hidTeleNo` | `String` | `` | 50 |
| `hiduserYn` | `String` | `` | 51 |
| `tsRsStnCd` | `String` | `` | 52 |
| `txtDeviceId` | `String` | `` | 53 |
| `txtIndex` | `String` | `` | 54 |

## `TicketListResponse`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `reservation_list` | `List<ReservationList>` | `` | 141 |

## `TrainInfo`

- Source: `com/korail/talk/network/dao/myTicket/TicketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `apdUsrFlg` | `String` | `` | 152 |
| `cmtrVlidFlg` | `String` | `` | 153 |
| `dvcInfoSmnsFlg` | `String` | `` | 154 |
| `h_abrd_ps_nm` | `String` | `` | 155 |
| `h_arv_dt` | `String` | `` | 156 |
| `h_arv_rs_stn_cd` | `String` | `` | 157 |
| `h_arv_rs_stn_nm` | `String` | `` | 158 |
| `h_arv_tm` | `String` | `` | 159 |
| `h_buy_ps_nm` | `String` | `` | 160 |
| `h_dpt_dt` | `String` | `` | 161 |
| `h_dpt_rs_stn_cd` | `String` | `` | 162 |
| `h_dpt_rs_stn_nm` | `String` | `` | 163 |
| `h_dpt_tm` | `String` | `` | 164 |
| `h_jrny_sqno` | `String` | `` | 165 |
| `h_orgtk_ret_pwd` | `String` | `` | 166 |
| `h_orgtk_ret_sale_dt` | `String` | `` | 167 |
| `h_orgtk_sale_dt` | `String` | `` | 168 |
| `h_orgtk_sale_sqno` | `String` | `` | 169 |
| `h_orgtk_wct_no` | `String` | `` | 170 |
| `h_pbp_acep_tgt_flg` | `String` | `` | 171 |
| `h_pnr_no` | `String` | `` | 172 |
| `h_psg_tp_cd` | `String` | `` | 173 |
| `h_psrm_cl_cd` | `String` | `` | 174 |
| `h_rcvd_amt` | `String` | `` | 175 |
| `h_rsv_chg_tno` | `String` | `` | 176 |
| `h_run_dt` | `String` | `` | 177 |
| `h_seat_cnt` | `String` | `` | 178 |
| `h_seat_no` | `String` | `` | 179 |
| `h_seat_no_end` | `String` | `` | 180 |
| `h_sgr_nm_1` | `String` | `` | 181 |
| `h_sgr_nm_2` | `String` | `` | 182 |
| `h_srcar_no` | `String` | `` | 183 |
| `h_tk_knd_cd` | `String` | `` | 184 |
| `h_tk_knd_nm` | `String` | `` | 185 |
| `h_tk_sqno` | `String` | `` | 186 |
| `h_trn_clsf_cd` | `String` | `` | 187 |
| `h_trn_clsf_nm` | `String` | `` | 188 |
| `h_trn_no` | `String` | `` | 189 |
| `pbpRsvNo` | `String` | `` | 190 |
| `runClsFlg` | `String` | `` | 191 |
| `srtStnFlg` | `String` | `` | 192 |
| `stpvFlg` | `String` | `` | 193 |
| `trnSpsFlg` | `String` | `` | 194 |

## `NFilterCreateKeyResponse`

- Source: `com/korail/talk/network/dao/nFilter/NFilterCreateKeyDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `publicKey` | `String` | `` | 12 |

## `CommPaymentRequest`

- Source: `com/korail/talk/network/dao/pass/CommPaymentDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `commPaymentMap` | `Map<String, String>` | `` | 17 |
| `hidPayAmount` | `String` | `` | 18 |
| `paymentMethod` | `PaymentMethod` | `` | 19 |

## `CommPaymentResponse`

- Source: `com/korail/talk/network/dao/pass/CommPaymentDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `main_info` | `PassPaymentDao.MainInfo` | `` | 55 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/pass/CommPaymentDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_pnr_no` | `String` | `` | 66 |

## `CommReservationRequest`

- Source: `com/korail/talk/network/dao/pass/CommReservationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidAppArvStnCd` | `String` | `` | 13 |
| `hidAppArvStnNm` | `String` | `` | 14 |
| `hidAppDptStnCd` | `String` | `` | 15 |
| `hidAppDptStnNm` | `String` | `` | 16 |
| `hidChtrnStnCd` | `String` | `` | 17 |
| `hidChtrnStnNm` | `String` | `` | 18 |
| `hidCmtrKndCd` | `String` | `` | 19 |
| `hidCmtrUtlAgeCd` | `String` | `` | 20 |
| `hidCmtrUtlTrmCd` | `String` | `` | 21 |
| `hidCmtrUtlTrmNm` | `String` | `` | 22 |
| `hidDtour1` | `String` | `` | 23 |
| `hidDtour2` | `String` | `` | 24 |
| `hidTrnGpCd1` | `String` | `` | 25 |
| `hidTrnGpCd2` | `String` | `` | 26 |
| `hidTrnNo1` | `String` | `` | 27 |
| `hidTrnNo2` | `String` | `` | 28 |
| `hidUseOpenDt` | `String` | `` | 29 |
| `stationInfo` | `String` | `` | 30 |

## `CommReservationResponse`

- Source: `com/korail/talk/network/dao/pass/CommReservationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_guide` | `String` | `` | 181 |
| `main_info` | `MainInfo` | `` | 182 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/pass/CommReservationDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_age` | `String` | `` | 185 |
| `h_app_arv_rs_stn_cd` | `String` | `` | 186 |
| `h_app_arv_rs_stn_nm` | `String` | `` | 187 |
| `h_app_dpt_rs_stn_cd` | `String` | `` | 188 |
| `h_app_dpt_rs_stn_nm` | `String` | `` | 189 |
| `h_arv_stn_cons_ordr_1` | `String` | `` | 190 |
| `h_arv_stn_cons_ordr_2` | `String` | `` | 191 |
| `h_arv_tm` | `String` | `` | 192 |
| `h_chg_mg_dv_cd` | `String` | `` | 193 |
| `h_chg_mg_no` | `String` | `` | 194 |
| `h_chtrn_rs_stn_cd` | `String` | `` | 195 |
| `h_chtrn_rs_stn_nm` | `String` | `` | 196 |
| `h_cmtr_knd_cd` | `String` | `` | 197 |
| `h_cmtr_srt_cd` | `String` | `` | 198 |
| `h_cmtr_utl_age_cd` | `String` | `` | 199 |
| `h_cmtr_utl_trm_cd` | `String` | `` | 200 |
| `h_cmtr_utl_trm_nm` | `String` | `` | 201 |
| `h_cust_nm` | `String` | `` | 202 |
| `h_cust_no` | `String` | `` | 203 |
| `h_dpt_stn_cons_ordr_1` | `String` | `` | 204 |
| `h_dpt_stn_cons_ordr_2` | `String` | `` | 205 |
| `h_dpt_tm` | `String` | `` | 206 |
| `h_dtour1` | `String` | `` | 207 |
| `h_dtour2` | `String` | `` | 208 |
| `h_exs_ln_acm_dst` | `String` | `` | 209 |
| `h_holiday_cls_dt` | `String` | `` | 210 |
| `h_holiday_flg` | `String` | `` | 211 |
| `h_holiday_st_dt` | `String` | `` | 212 |
| `h_new_ln_acm_dst` | `String` | `` | 213 |
| `h_otm_rcvd_amt` | `String` | `` | 214 |
| `h_prc_cl_cd_1` | `String` | `` | 215 |
| `h_prc_cl_cd_2` | `String` | `` | 216 |
| `h_psg_tp_cd` | `String` | `` | 217 |
| `h_psrm_cl_cd` | `String` | `` | 218 |
| `h_rcvd_amt` | `String` | `` | 219 |
| `h_rcvd_fare` | `String` | `` | 220 |
| `h_rcvd_prc` | `String` | `` | 221 |
| `h_rout_cd_1` | `String` | `` | 222 |
| `h_rout_cd_2` | `String` | `` | 223 |
| `h_rsv_trm_dup` | `String` | `` | 224 |
| `h_schd_trvl_dv_cd` | `String` | `` | 225 |
| `h_stx_amt` | `String` | `` | 226 |
| `h_taxt_spl_prce` | `String` | `` | 227 |
| `h_trn_clsf_cd_1` | `String` | `` | 228 |
| `h_trn_clsf_cd_2` | `String` | `` | 229 |
| `h_trn_gp_cd` | `String` | `` | 230 |
| `h_trn_no_1` | `String` | `` | 231 |
| `h_trn_no_2` | `String` | `` | 232 |
| `h_und_dv_cd_1` | `String` | `` | 233 |
| `h_und_dv_cd_2` | `String` | `` | 234 |
| `h_use_cls_dt` | `String` | `` | 235 |
| `h_use_open_dt` | `String` | `` | 236 |
| `h_use_psb_dno` | `String` | `` | 237 |
| `h_use_psb_tno` | `String` | `` | 238 |
| `isIncludeHoliday` | `boolean` | `` | 239 |
| `mStationInfo` | `String` | `` | 240 |
| `mUserNames` | `String` | `` | 241 |

## `CommRsvInquiryRequest`

- Source: `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `radChgTrnDvCd` | `String` | `` | 14 |
| `selGoAbrdDt` | `String` | `` | 15 |
| `selGoTrain` | `String` | `` | 16 |
| `txtCmtrKndCd` | `String` | `` | 17 |
| `txtCmtrUtlAgeCd` | `String` | `` | 18 |
| `txtCmtrUtlTrmCd` | `String` | `` | 19 |
| `txtCmtrUtlTrmNm` | `String` | `` | 20 |
| `txtCntPerPage` | `String` | `` | 21 |
| `txtGoEnd` | `String` | `` | 22 |
| `txtGoHour` | `String` | `` | 23 |
| `txtGoStart` | `String` | `` | 24 |
| `txtSelPage` | `String` | `` | 25 |
| `txtWkndUseFlg` | `String` | `` | 26 |

## `CommRsvInquiryResponse`

- Source: `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `schedule_info` | `List<ScheduleInfoList>` | `` | 137 |

## `ScheduleInfoList`

- Source: `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `train_list` | `List<TrainList>` | `` | 140 |

## `TrainList`

- Source: `com/korail/talk/network/dao/pass/CommRsvInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_arv_rs_stn_cd` | `String` | `` | 159 |
| `h_arv_rs_stn_nm` | `String` | `` | 160 |
| `h_dpt_rs_stn_cd` | `String` | `` | 161 |
| `h_dpt_rs_stn_nm` | `String` | `` | 162 |
| `h_dtour` | `String` | `` | 163 |
| `h_schd_prc` | `String` | `` | 164 |
| `h_trn_gp_cd` | `String` | `` | 165 |
| `h_trn_no` | `String` | `` | 166 |

## `DiscountMenu`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `afterDay` | `int` | `` | 17 |
| `agree` | `String` | `` | 18 |
| `detailType` | `String` | `` | 19 |
| `dtlDsc` | `String` | `` | 20 |
| `enable` | `String` | `` | 21 |
| `goodsData` | `GoodInfo` | `` | 22 |
| `id` | `String` | `` | 23 |
| `information` | `String` | `` | 24 |
| `isExpand` | `String` | `` | 25 |
| `parentId` | `String` | `` | 26 |
| `passData` | `PassMainInfo` | `` | 27 |
| `repSegArv` | `String` | `` | 28 |
| `repSegDpt` | `String` | `` | 29 |
| `title` | `String` | `` | 30 |
| `trnGpCd` | `String` | `` | 31 |
| `type` | `String` | `` | 32 |
| `webData` | `WebData` | `` | 33 |

## `DiscountMenuRequest`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `menuNo` | `String` | `` | 121 |

## `DiscountMenuResponse`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `list` | `List<DiscountMenu>` | `` | 136 |

## `GoodInfo`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cnd_flg_disc_no` | `String` | `` | 147 |
| `psg_infos` | `PsgInfos` | `` | 148 |

## `PassAgeInfo`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cmtr_utl_age_cd` | `String` | `` | 163 |
| `h_comn_cd_nm` | `String` | `` | 164 |
| `h_max_age` | `String` | `` | 165 |
| `h_min_age` | `String` | `` | 166 |

## `PassMainInfo`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cmtr_knd_cd` | `String` | `` | 189 |
| `h_select_station` | `String` | `` | 190 |
| `pass_ageinfo` | `List<PassAgeInfo>` | `` | 191 |
| `pass_periodinfo` | `List<PassPeriodInfo>` | `` | 192 |

## `PassPeriodInfo`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cmtr_utl_trm_cd` | `String` | `` | 215 |
| `h_comn_cd_nm` | `String` | `` | 216 |

## `PsgInfo`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cls_prnb` | `int` | `` | 231 |
| `h_dcnt_knd_cd` | `String` | `` | 232 |
| `h_st_prnb` | `int` | `` | 233 |

## `PsgInfos`

- Source: `com/korail/talk/network/dao/pass/DiscountMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_chtn_allw_flg` | `String` | `` | 252 |
| `h_max_cnt` | `String` | `` | 253 |
| `h_min_cnt` | `String` | `` | 254 |
| `psg_info` | `List<PsgInfo>` | `` | 255 |

## `EnableDateRequest`

- Source: `com/korail/talk/network/dao/pass/EnableDateDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtCmtrKndCd` | `String` | `` | 13 |
| `txtCmtrUtlAgeCd` | `String` | `` | 14 |
| `txtCmtrUtlTrmCd` | `String` | `` | 15 |

## `EnableDateResponse`

- Source: `com/korail/talk/network/dao/pass/EnableDateDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pass_info` | `List<PassInfo>` | `` | 46 |
| `ticket_info` | `List<Ticket_info>` | `` | 47 |
| `wct_info` | `List<WctInfo>` | `` | 48 |

## `PassInfo`

- Source: `com/korail/talk/network/dao/pass/EnableDateDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_use_open_dt` | `String` | `` | 67 |

## `Ticket_info`

- Source: `com/korail/talk/network/dao/pass/EnableDateDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_ise_dt2` | `String` | `` | 78 |

## `WctInfo`

- Source: `com/korail/talk/network/dao/pass/EnableDateDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `eng_cd_val` | `String` | `` | 89 |
| `kor_cd_val` | `String` | `` | 90 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/pass/PassPaymentDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_pnr_no` | `String` | `` | 17 |

## `PassPaymentRequest`

- Source: `com/korail/talk/network/dao/pass/PassPaymentDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_rcvd_prc` | `String` | `` | 28 |
| `hidPayAmount` | `String` | `` | 29 |
| `hidWctNo` | `String` | `` | 30 |
| `passPaymentMap` | `Map<String, String>` | `` | 31 |
| `paymentMethod` | `PaymentMethod` | `` | 32 |

## `PassPaymentResponse`

- Source: `com/korail/talk/network/dao/pass/PassPaymentDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `main_info` | `MainInfo` | `` | 88 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/pass/PassReservationDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cmtr_dv_cd` | `String` | `` | 12 |
| `h_cmtr_knd_cd` | `String` | `` | 13 |
| `h_cmtr_utl_age_cd` | `String` | `` | 14 |
| `h_cmtr_utl_trm_cd` | `String` | `` | 15 |
| `h_disc_cert_sqno` | `String` | `` | 16 |
| `h_fmps_cert_no` | `String` | `` | 17 |
| `h_rcvd_amt` | `String` | `` | 18 |
| `h_use_cls_dt` | `String` | `` | 19 |
| `h_use_open_dt` | `String` | `` | 20 |
| `h_use_psb_dno` | `String` | `` | 21 |

## `PassReservationRequest`

- Source: `com/korail/talk/network/dao/pass/PassReservationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidCmtrKndCd` | `String` | `` | 108 |
| `hidCmtrUtlAgeCd` | `String` | `` | 109 |
| `hidCmtrUtlTrmCd` | `String` | `` | 110 |
| `hidUseOpenDt` | `String` | `` | 111 |

## `PassReservationResponse`

- Source: `com/korail/talk/network/dao/pass/PassReservationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `main_info` | `MainInfo` | `` | 150 |

## `ContentInfo`

- Source: `com/korail/talk/network/dao/pass/TripMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cmtrKndCd` | `String` | `` | 17 |
| `contDetail` | `String` | `` | 18 |
| `contImage` | `String` | `` | 19 |
| `contTitle` | `String` | `` | 20 |
| `contUrl` | `String` | `` | 21 |
| `detailType` | `String` | `` | 22 |
| `passActive` | `String` | `` | 23 |
| `passAgree` | `String` | `` | 24 |
| `passData` | `DiscountMenuDao.PassMainInfo` | `` | 25 |
| `passInfo` | `String` | `` | 26 |
| `passType` | `String` | `` | 27 |

## `TripMenu`

- Source: `com/korail/talk/network/dao/pass/TripMenuDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `contCount` | `String` | `` | 78 |
| `contList` | `List<ContentInfo>` | `` | 79 |
| `menuBtn` | `String` | `` | 80 |
| `menuDetail` | `String` | `` | 81 |
| `menuTitle` | `String` | `` | 82 |
| `menuType` | `String` | `` | 83 |
| `menuUrl` | `String` | `` | 84 |

## `TripMenuResponse`

- Source: `com/korail/talk/network/dao/pass/TripMenuDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `menuList` | `List<TripMenu>` | `` | 119 |
| `poppMsg` | `String` | `` | 120 |

## `DCCouponCertRequest`

- Source: `com/korail/talk/network/dao/passCard/DCCouponCertDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `couponInputViewIndex` | `int` | `` | 12 |
| `txtCertNo` | `String` | `` | 13 |
| `txtCertPwd` | `String` | `` | 14 |

## `CouponInfos`

- Source: `com/korail/talk/network/dao/passCard/DCCouponListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `coupon_info` | `List<DiscountCoupon>` | `` | 14 |

## `DCCouponListRequest`

- Source: `com/korail/talk/network/dao/passCard/DCCouponListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnr` | `String` | `` | 25 |
| `txtSelPage` | `String` | `` | 26 |

## `DCCouponListResponse`

- Source: `com/korail/talk/network/dao/passCard/DCCouponListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `coupon_infos` | `CouponInfos` | `` | 49 |
| `h_page_no` | `String` | `` | 50 |
| `h_tot_page_cnt` | `String` | `` | 51 |

## `DiscountCoupon`

- Source: `com/korail/talk/network/dao/passCard/DCCouponListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `guide` | `String` | `` | 70 |
| `h_cpn_no` | `String` | `` | 71 |
| `h_disc_rt_amt_dv_cd` | `String` | `` | 72 |
| `h_fdcert_mg_cls_dt` | `String` | `` | 73 |
| `h_inwk_fare_disc_rt_amt` | `String` | `` | 74 |
| `h_inwk_prc_disc_rt_amt` | `String` | `` | 75 |
| `h_rmk_1_cont` | `String` | `` | 76 |
| `h_rmk_2_cont` | `String` | `` | 77 |
| `h_rmk_3_cont` | `String` | `` | 78 |
| `h_wknd_fare_disc_rt_amt` | `String` | `` | 79 |
| `h_wknd_prc_disc_rt_amt` | `String` | `` | 80 |
| `mIndex` | `int` | `` | 81 |

## `DelayTicketAddRequest`

- Source: `com/korail/talk/network/dao/passCard/DelayTicketAddDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `delayCouponInputViewIndex` | `int` | `` | 12 |
| `h_dlay_disc_cnt` | `String` | `` | 13 |
| `h_orgtk_ret_pwd` | `String` | `` | 14 |
| `h_orgtk_ret_sale_dt` | `String` | `` | 15 |
| `h_orgtk_sale_sqno` | `String` | `` | 16 |
| `h_orgtk_wct_no` | `String` | `` | 17 |

## `DelayCoupon`

- Source: `com/korail/talk/network/dao/passCard/DelayTicketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_dlay_fare` | `String` | `` | 13 |
| `h_orgtk_ret_pwd` | `String` | `` | 14 |
| `h_orgtk_ret_sale_dt` | `String` | `` | 15 |
| `h_orgtk_sale_sqno` | `String` | `` | 16 |
| `h_orgtk_wct_no` | `String` | `` | 17 |
| `h_use_psb_dt` | `String` | `` | 18 |
| `mIndex` | `int` | `` | 19 |

## `DelayTicketListRequest`

- Source: `com/korail/talk/network/dao/passCard/DelayTicketListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptDtTo` | `String` | `` | 74 |

## `DelayTicketListResponse`

- Source: `com/korail/talk/network/dao/passCard/DelayTicketListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `disc_infos` | `DiscInfos` | `` | 89 |

## `DiscInfos`

- Source: `com/korail/talk/network/dao/passCard/DelayTicketListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `disc_info` | `List<DelayCoupon>` | `` | 100 |

## `IntgStlRequest`

- Source: `com/korail/talk/network/dao/pay/IntgStlDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cart_LumpStlTgtNo` | `String` | `` | 15 |
| `ctlDvCd` | `String` | `` | 16 |
| `hidRsvChgNo` | `String` | `` | 17 |
| `paymentMethod` | `PaymentMethod` | `` | 18 |
| `stlPrsJobId` | `String` | `` | 19 |

## `NaverPayMoneyRsvRequest`

- Source: `com/korail/talk/network/dao/pay/NaverPayMoneyRsvDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `productAmount` | `int` | `` | 12 |
| `productCount` | `int` | `` | 13 |

## `NaverPayRsvRequest`

- Source: `com/korail/talk/network/dao/pay/NaverPayRsvDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `productAmount` | `int` | `` | 12 |
| `productCount` | `int` | `` | 13 |

## `NaverPayRsvResponse`

- Source: `com/korail/talk/network/dao/pay/NaverPayRsvDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stlScnUrl` | `String` | `` | 36 |

## `PayCoBridgeInfo`

- Source: `com/korail/talk/network/dao/pay/PaycoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `orderSheetUrl` | `String` | `` | 12 |

## `PaycoPaymentRequest`

- Source: `com/korail/talk/network/dao/pay/PaycoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ticketName` | `String` | `` | 23 |
| `ticketPrice` | `String` | `` | 24 |

## `PaycoPaymentResponse`

- Source: `com/korail/talk/network/dao/pay/PaycoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `recvData` | `RecvData` | `` | 47 |

## `RecvData`

- Source: `com/korail/talk/network/dao/pay/PaycoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `result` | `PayCoBridgeInfo` | `` | 58 |

## `SpayCphdDatValRequest`

- Source: `com/korail/talk/network/dao/pay/SpayCphdDatValDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `data` | `ArrayList<String>` | `` | 13 |
| `mainPgCode` | `String` | `` | 14 |
| `paymentMethodType` | `String` | `` | 15 |
| `spayDvCd` | `String` | `` | 16 |
| `type` | `String` | `` | 17 |

## `SpayCphdDatValResponse`

- Source: `com/korail/talk/network/dao/pay/SpayCphdDatValDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `spayCphdDatVal` | `String` | `` | 64 |
| `stlCrCrdNo` | `String` | `` | 65 |

## `SpayCphdDatValMonimoRequest`

- Source: `com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `otcNo` | `String` | `` | 13 |

## `SpayCphdDatValMonimoResponse`

- Source: `com/korail/talk/network/dao/pay/SpayCphdDatValMonimoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stlCrCrdNo` | `String` | `` | 28 |

## `SpayOdrNoRequest`

- Source: `com/korail/talk/network/dao/pay/SpayOdrNoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `encTotTxnAmt` | `String` | `` | 13 |
| `idx` | `String` | `` | 14 |
| `isMonimo` | `Boolean` | `` | 15 |
| `lumpStlTgtNo` | `ArrayList<String>` | `` | 16 |
| `spayDvCd` | `String` | `` | 17 |
| `tgtCnt` | `String` | `` | 18 |
| `totTxnAmt` | `String` | `` | 19 |

## `SpayOdrNoResponse`

- Source: `com/korail/talk/network/dao/pay/SpayOdrNoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fllwScnAppUrlAdr` | `String` | `` | 86 |
| `prprNo` | `String` | `` | 87 |
| `spayTid` | `String` | `` | 88 |

## `StbkAcntDao`

- Source: `com/korail/talk/network/dao/pay/StbkAcntDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ACCOUNT_NAME_CHECK` | `String` | `` | 10 |
| `ACCOUNT_REGISTER` | `String` | `` | 11 |
| `ARS_CERTIFICATION` | `String` | `` | 12 |
| `ARS_RESULT_CONFIRM` | `String` | `` | 13 |
| `CHANGE_PASSWORD` | `String` | `` | 14 |
| `DELETE_ACCOUNT` | `String` | `` | 15 |

## `StbkAcntRequest`

- Source: `com/korail/talk/network/dao/pay/StbkAcntDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acntNo` | `String` | `` | 18 |
| `custCpNo` | `String` | `` | 19 |
| `jobDvCd` | `String` | `` | 20 |
| `stbkTxnNo` | `String` | `` | 21 |
| `stlApvPwd` | `String` | `` | 22 |
| `stlBankCd` | `String` | `` | 23 |

## `StbkAcntResponse`

- Source: `com/korail/talk/network/dao/pay/StbkAcntDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 78 |
| `stbkTxnNo` | `String` | `` | 79 |

## `Reg`

- Source: `com/korail/talk/network/dao/pay/StbkRegBankDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acntNo` | `String` | `` | 14 |
| `imageUrl` | `String` | `` | 15 |
| `isPay` | `String` | `` | 16 |
| `pwdErrMsg` | `String` | `` | 17 |
| `stlBankCd` | `String` | `` | 18 |

## `RegPsb`

- Source: `com/korail/talk/network/dao/pay/StbkRegBankDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `imageUrl` | `String` | `` | 45 |
| `stlBankCd` | `String` | `` | 46 |

## `StbkRegBankResponse`

- Source: `com/korail/talk/network/dao/pay/StbkRegBankDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `regList` | `List<Reg>` | `` | 61 |
| `regPsbList` | `List<RegPsb>` | `` | 62 |

## `TossAutoCResponse`

- Source: `com/korail/talk/network/dao/pay/TossAutoCreateDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `billingKey` | `String` | `` | 12 |
| `checkoutAndroidUri` | `String` | `` | 13 |
| `checkoutIosUri` | `String` | `` | 14 |
| `checkoutUri` | `String` | `` | 15 |

## `StlKeyPrsRequest`

- Source: `com/korail/talk/network/dao/pay/TossAutoStlKeyPrsDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acntNo` | `String` | `` | 12 |
| `binNo` | `String` | `` | 13 |
| `jobDvCd` | `String` | `` | 14 |
| `spayDvCd` | `String` | `` | 15 |
| `spayStlKeyVal` | `String` | `` | 16 |
| `stlBankCd` | `String` | `` | 17 |

## `SimplePayInfo`

- Source: `com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acntNo` | `String` | `` | 13 |
| `binNo` | `String` | `` | 14 |
| `imageUrl` | `String` | `` | 15 |
| `pwdErrTno` | `String` | `` | 16 |
| `spayDvCd` | `String` | `` | 17 |
| `spayStlKeyVal` | `String` | `` | 18 |
| `stlBankCd` | `String` | `` | 19 |
| `stlBankNm` | `String` | `` | 20 |
| `stlCrdCoCd` | `String` | `` | 21 |

## `StlKeyQryRequest`

- Source: `com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `spayDvCd` | `String` | `` | 64 |

## `StlKeyQryResponse`

- Source: `com/korail/talk/network/dao/pay/TossAutoStlKeyQryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `spayList` | `List<SimplePayInfo>` | `` | 79 |

## `RsvPaymentRequest`

- Source: `com/korail/talk/network/dao/payment/RsvPaymentDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidPnrNo` | `String` | `` | 16 |
| `hidRsvChgNo` | `String` | `` | 17 |
| `jobSqNo1` | `String` | `` | 18 |
| `jobSqNo2` | `String` | `` | 19 |
| `paymentMethod` | `PaymentMethod` | `` | 20 |
| `wctNo` | `String` | `` | 21 |

## `RsvPaymentResponse`

- Source: `com/korail/talk/network/dao/payment/RsvPaymentDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_im_flg` | `String` | `` | 81 |
| `tk_coupon_info` | `List<TkCouponInfo>` | `` | 82 |

## `TkCouponInfo`

- Source: `com/korail/talk/network/dao/payment/RsvPaymentDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cert_pwd` | `String` | `` | 97 |
| `h_coup_no` | `String` | `` | 98 |
| `h_fdcert_mg_cls_dt` | `String` | `` | 99 |
| `h_fdcert_mg_st_dt` | `String` | `` | 100 |
| `h_tk_ret_no` | `String` | `` | 101 |

## `ProductCancelRequest`

- Source: `com/korail/talk/network/dao/product/ProductCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtGdSqno` | `String` | `` | 12 |
| `txtVrRsNo` | `String` | `` | 13 |

## `EntityOne`

- Source: `com/korail/talk/network/dao/product/ProductDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `strGdConsItmNm` | `String` | `` | 14 |

## `ProductDetailRequest`

- Source: `com/korail/talk/network/dao/product/ProductDetailDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtVrRsvNo` | `String` | `` | 25 |
| `txtVrRsvSqNo` | `String` | `` | 26 |

## `ProductDetailResponse`

- Source: `com/korail/talk/network/dao/product/ProductDetailDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mainInfo` | `ProductInfo` | `` | 49 |

## `ProductInfo`

- Source: `com/korail/talk/network/dao/product/ProductDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `entityOne` | `List<EntityOne>` | `` | 60 |
| `strCncDlnDt` | `String` | `` | 61 |
| `strCncRetAmt` | `String` | `` | 62 |
| `strCncRetFee` | `String` | `` | 63 |
| `strGdNm` | `String` | `` | 64 |
| `strGdSqno` | `String` | `` | 65 |
| `strInt11` | `String` | `` | 66 |
| `strRcvdAmt` | `String` | `` | 67 |
| `strRsvSttNm` | `String` | `` | 68 |
| `strStlSttCd` | `EnumC5608b` | `` | 69 |
| `strTotStlAmt` | `String` | `` | 70 |
| `strUtlTrmCont` | `String` | `` | 71 |
| `strVrRsvNo` | `String` | `` | 72 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/product/ProductListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `entity` | `List<ReservationProduct>` | `` | 14 |
| `strTotCnt` | `String` | `` | 15 |

## `ProductListRequest`

- Source: `com/korail/talk/network/dao/product/ProductListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtCntPerPage` | `int` | `` | 30 |
| `txtSelPage` | `int` | `` | 31 |

## `ProductListResponse`

- Source: `com/korail/talk/network/dao/product/ProductListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mainInfo` | `MainInfo` | `` | 54 |

## `ReservationProduct`

- Source: `com/korail/talk/network/dao/product/ProductListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `strGdNm` | `String` | `` | 65 |
| `strRsvSttCd` | `String` | `` | 66 |
| `strRsvSttNm` | `String` | `` | 67 |
| `strStlDlnDt` | `String` | `` | 68 |
| `strStlSttCd` | `EnumC5608b` | `` | 69 |
| `strVrRsvNo` | `String` | `` | 70 |

## `MainInfo`

- Source: `com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `strLumpStlTgtNo` | `String` | `` | 12 |
| `strMrkAmtSum` | `int` | `` | 13 |

## `ProductPaymentCheckRequest`

- Source: `com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtRsvGdSqno` | `String` | `` | 28 |
| `txtVrRsNo` | `String` | `` | 29 |

## `ProductPaymentCheckResponse`

- Source: `com/korail/talk/network/dao/product/ProductPaymentCheckDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mainInfo` | `MainInfo` | `` | 52 |

## `CallCrewDaoRequest`

- Source: `com/korail/talk/network/dao/push/CallCrewDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `coutMsgDvCd` | `String` | `` | 13 |
| `intgMsgCd1` | `String` | `` | 14 |
| `intgMsgCd10` | `String` | `` | 15 |
| `intgMsgCd2` | `String` | `` | 16 |
| `intgMsgCd3` | `String` | `` | 17 |
| `intgMsgCd4` | `String` | `` | 18 |
| `intgMsgCd5` | `String` | `` | 19 |
| `intgMsgCd6` | `String` | `` | 20 |
| `intgMsgCd7` | `String` | `` | 21 |
| `intgMsgCd8` | `String` | `` | 22 |
| `intgMsgCd9` | `String` | `` | 23 |
| `intgMsgCont` | `String` | `` | 24 |
| `jrnySqno` | `String` | `` | 25 |
| `pnrNo` | `String` | `` | 26 |
| `saleDt` | `String` | `` | 27 |
| `saleSqno` | `String` | `` | 28 |
| `saleWctNo` | `String` | `` | 29 |
| `sndSqno` | `String` | `` | 30 |
| `tkRetPwd` | `String` | `` | 31 |

## `CallCrewDaoListRequest`

- Source: `com/korail/talk/network/dao/push/CallCrewRequestListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `qryDvCd` | `String` | `` | 13 |

## `CallCrewListResponse`

- Source: `com/korail/talk/network/dao/push/CallCrewRequestListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `prsList` | `List<PrsList>` | `` | 28 |

## `PrsList`

- Source: `com/korail/talk/network/dao/push/CallCrewRequestListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `intgMsgCd` | `String` | `` | 39 |
| `prsCont` | `String` | `` | 40 |

## `CmtrKndMenuRequest`

- Source: `com/korail/talk/network/dao/push/CmtrKndMenuDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cmtrKndCd` | `String` | `` | 13 |

## `CmtrKndMenuResponse`

- Source: `com/korail/talk/network/dao/push/CmtrKndMenuDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `afterDay` | `String` | `` | 28 |
| `agree` | `String` | `` | 29 |
| `information` | `String` | `` | 30 |
| `passData` | `DiscountMenuDao.PassMainInfo` | `` | 31 |
| `title` | `String` | `` | 32 |

## `PushUpdateDao`

- Source: `com/korail/talk/network/dao/push/PushUpdateDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mIsPending` | `boolean` | `` | 10 |

## `PushUpdateRequest`

- Source: `com/korail/talk/network/dao/push/PushUpdateDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvUsrInpTnum` | `String` | `` | 13 |
| `dptUsrInpTnum` | `String` | `` | 14 |
| `job_dv_cd` | `String` | `` | 15 |
| `tnsm_flg1` | `String` | `` | 16 |
| `tnsm_flg2` | `String` | `` | 17 |
| `tnsm_flg3` | `String` | `` | 18 |
| `tnsm_flg4` | `String` | `` | 19 |

## `PushUpdateResponse`

- Source: `com/korail/talk/network/dao/push/PushUpdateDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvUsrInpTnum` | `String` | `` | 82 |
| `dptUsrInpTnum` | `String` | `` | 83 |
| `prs_cnqe_msg_cd` | `String` | `` | 84 |
| `tnsm_flg1` | `String` | `` | 85 |
| `tnsm_flg2` | `String` | `` | 86 |
| `tnsm_flg3` | `String` | `` | 87 |
| `tnsm_flg4` | `String` | `` | 88 |

## `AutoChargeRequest`

- Source: `com/korail/talk/network/dao/railplus/AutoChargeDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jobDvCd` | `String` | `` | 12 |
| `prepCrdNo` | `String` | `` | 13 |

## `AutoChargeResponse`

- Source: `com/korail/talk/network/dao/railplus/AutoChargeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psbFlg` | `String` | `` | 36 |

## `CashReceiptInfo`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_apv_mtd_nm` | `String` | `` | 13 |
| `h_athn_dmn_rcgn_no` | `String` | `` | 14 |
| `h_cash_rcet_apv_no` | `String` | `` | 15 |
| `h_cash_rcet_txn_dv_cd` | `String` | `` | 16 |
| `h_tot_apv_amt` | `int` | `` | 17 |

## `ReceiptInfo`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cash_rcet_info` | `List<CashReceiptInfo>` | `` | 44 |
| `h_abrd_dt` | `String` | `` | 45 |
| `h_arv_rs_stn_nm` | `String` | `` | 46 |
| `h_arv_tm` | `String` | `` | 47 |
| `h_cmtr_knd_cd` | `String` | `` | 48 |
| `h_crd_ret_amt` | `int` | `` | 49 |
| `h_dpt_rs_stn_nm` | `String` | `` | 50 |
| `h_dpt_tm` | `String` | `` | 51 |
| `h_jrny_tp_cd` | `String` | `` | 52 |
| `h_prt_disc_knd_nm` | `String` | `` | 53 |
| `h_prt_type` | `String` | `` | 54 |
| `h_psg_type1_cnt` | `int` | `` | 55 |
| `h_psg_type2_cnt` | `int` | `` | 56 |
| `h_psg_type3_cnt` | `int` | `` | 57 |
| `h_psrm_cl_nm` | `String` | `` | 58 |
| `h_rcvd_amt` | `int` | `` | 59 |
| `h_ret_fee` | `int` | `` | 60 |
| `h_ret_rcvd_amt` | `int` | `` | 61 |
| `h_stl_mb_crd_no` | `String` | `` | 62 |
| `h_tk_knd_cd` | `String` | `` | 63 |
| `h_tk_stt_cd` | `String` | `` | 64 |
| `h_trn_clsf_cd` | `String` | `` | 65 |
| `h_trn_clsf_nm` | `String` | `` | 66 |
| `h_trn_no` | `String` | `` | 67 |
| `h_xpoint_ret_amt` | `int` | `` | 68 |
| `stl_info` | `List<StlInfo>` | `` | 69 |

## `ReceiptInfos`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `receipt_info` | `List<ReceiptInfo>` | `` | 180 |

## `ReceiptRequest`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_orgtk_sale_dt` | `String` | `` | 191 |
| `h_orgtk_sale_sqno` | `String` | `` | 192 |
| `h_orgtk_tk_ret_pwd` | `String` | `` | 193 |
| `h_orgtk_wct_no` | `String` | `` | 194 |

## `ReceiptResponse`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `receipt_infos` | `ReceiptInfos` | `` | 233 |

## `StlInfo`

- Source: `com/korail/talk/network/dao/receipt/ReceiptDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_acnt_no` | `String` | `` | 244 |
| `h_apv_dt` | `String` | `` | 245 |
| `h_apv_no` | `String` | `` | 246 |
| `h_ismt_mnth_num` | `int` | `` | 247 |
| `h_stl_amt` | `int` | `` | 248 |
| `h_stl_crd_no` | `String` | `` | 249 |
| `h_stl_way_nm` | `String` | `` | 250 |
| `h_xpot_no` | `String` | `` | 251 |

## `RefundCommissionRequest`

- Source: `com/korail/talk/network/dao/refund/RefundCommissionDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_comp_cert_no` | `String` | `` | 12 |
| `h_comp_nm` | `String` | `` | 13 |
| `h_orgtk_ret_pwd` | `String` | `` | 14 |
| `h_orgtk_ret_sale_dt` | `String` | `` | 15 |
| `h_orgtk_sale_sqno` | `String` | `` | 16 |
| `h_orgtk_wct_no` | `String` | `` | 17 |

## `RefundCommissionResponse`

- Source: `com/korail/talk/network/dao/refund/RefundCommissionDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_msg_cd2` | `String` | `` | 72 |
| `h_msg_txt2` | `String` | `` | 73 |
| `prg_psb_flg` | `String` | `` | 74 |
| `ret_amt` | `String` | `` | 75 |
| `ret_fee` | `String` | `` | 76 |
| `tk_ret_tms_dv_cd` | `String` | `` | 77 |
| `use_psb_mlg_num` | `String` | `` | 78 |

## `RefundRequest`

- Source: `com/korail/talk/network/dao/refund/RefundDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_mlg_stl` | `String` | `` | 14 |
| `h_orgtk_ret_pwd` | `String` | `` | 15 |
| `h_orgtk_sale_dt` | `String` | `` | 16 |
| `h_orgtk_sale_sqno` | `String` | `` | 17 |
| `h_orgtk_wct_no` | `String` | `` | 18 |
| `latitude` | `String` | `` | 19 |
| `longitude` | `String` | `` | 20 |
| `pbpAcepTgtFlg` | `String` | `` | 21 |
| `tk_ret_tms_dv_cd` | `String` | `` | 22 |
| `trnNo` | `String` | `` | 23 |
| `txtPnrNo` | `String` | `` | 24 |

## `RefundResponse`

- Source: `com/korail/talk/network/dao/refund/RefundDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stlList` | `List<StlList>` | `` | 119 |

## `StlList`

- Source: `com/korail/talk/network/dao/refund/RefundDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stl_mns_cd` | `String` | `` | 130 |

## `RefundExecuteTicketRefundRequest`

- Source: `com/korail/talk/network/dao/refund/RefundExecuteTicketRefundDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acepCustNm` | `String` | `` | 12 |
| `custTeln` | `String` | `` | 13 |
| `ogtkRetPwd` | `String` | `` | 14 |
| `ogtkSaleDt` | `String` | `` | 15 |
| `ogtkSaleSqno` | `String` | `` | 16 |
| `ogtkSaleWctNo` | `String` | `` | 17 |
| `pnrNo` | `String` | `` | 18 |
| `retAmt` | `String` | `` | 19 |
| `retDvCd` | `String` | `` | 20 |
| `retFee` | `String` | `` | 21 |
| `retRsnCd` | `String` | `` | 22 |
| `tkKndCd` | `String` | `` | 23 |

## `RefundExecuteTicketRefundResponse`

- Source: `com/korail/talk/network/dao/refund/RefundExecuteTicketRefundDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_ret_dv_cd` | `String` | `` | 126 |

## `JrnyInfo`

- Source: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arv_rs_stn_cd` | `String` | `` | 72 |
| `arv_tm` | `String` | `` | 73 |
| `dpt_dt` | `String` | `` | 74 |
| `dpt_rs_stn_cd` | `String` | `` | 75 |
| `dpt_tm` | `String` | `` | 76 |
| `seatinfo_list` | `ArrayList<SeatInfo>` | `` | 77 |
| `trn_gp_cd` | `String` | `` | 78 |
| `trn_no` | `String` | `` | 79 |

## `Orgtkinfo`

- Source: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyinfo_list` | `ArrayList<JrnyInfo>` | `` | 118 |
| `ogtk_ret_pwd` | `String` | `` | 119 |
| `ogtk_sale_dt` | `String` | `` | 120 |
| `ogtk_sale_sqno` | `String` | `` | 121 |
| `ogtk_sale_wct_no` | `String` | `` | 122 |
| `prnNo` | `String` | `` | 123 |
| `ret_dv_cd` | `String` | `` | 124 |
| `ret_rsn_cd` | `String` | `` | 125 |
| `tk_knd_cd` | `String` | `` | 126 |

## `RefundVerifyTicketRequest`

- Source: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `retNo1` | `String` | `` | 14 |
| `retNo2` | `String` | `` | 15 |
| `retNo3` | `String` | `` | 16 |
| `retNo4` | `String` | `` | 17 |
| `strName` | `String` | `` | 18 |

## `RefundVerifyTicketResponse`

- Source: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `orgtkinfo_list` | `ArrayList<Orgtkinfo>` | `` | 65 |
| `poppMsg` | `String` | `` | 66 |
| `rcvd_amt` | `String` | `` | 67 |
| `ret_amt` | `String` | `` | 68 |
| `ret_fee` | `String` | `` | 69 |

## `SeatInfo`

- Source: `com/korail/talk/network/dao/refund/RefundVerifyTicketDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psrm_cl_nm` | `String` | `` | 169 |
| `scar_no` | `String` | `` | 170 |
| `seat_no` | `String` | `` | 171 |

## `AddSrvList`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrList` | `List<ExtraProductInfo>` | `` | 15 |

## `AppSegInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnNm` | `String` | `` | 26 |
| `dcntCrdAplSegSqno` | `String` | `` | 27 |
| `dptRsStnNm` | `String` | `` | 28 |
| `jrnySqno` | `String` | `` | 29 |
| `jrnyTpCd` | `String` | `` | 30 |
| `stlbDturDvNm` | `String` | `` | 31 |
| `trnGpCd` | `String` | `` | 32 |

## `CompanionInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cmpa_btdt` | `String` | `` | 67 |
| `h_cmpa_nm` | `String` | `` | 68 |
| `h_cmpa_sex_dv_cd` | `String` | `` | 69 |

## `DelayInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `actArvDlayTnum` | `String` | `` | 88 |
| `actDptDlayTnum` | `String` | `` | 89 |
| `expnArvDlayTnum` | `String` | `` | 90 |
| `expnDptDlayTnum` | `String` | `` | 91 |
| `orgTmnRsStnNm1` | `String` | `` | 92 |
| `orgTmnRsStnNm2` | `String` | `` | 93 |

## `DiscountCardInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `appSegList` | `List<AppSegInfo>` | `` | 124 |
| `h_dcnt_crd_no` | `String` | `` | 125 |

## `FamilyInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psgNm` | `String` | `` | 145 |

## `Limousine`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `abrdSpot` | `String` | `` | 156 |
| `guide` | `String` | `` | 157 |
| `runTm` | `String` | `` | 158 |

## `TicketDetailRequest`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_purchase_history` | `String` | `` | 177 |
| `retPwd` | `String` | `` | 178 |
| `saleDt` | `String` | `` | 179 |
| `saleSqNo` | `String` | `` | 180 |
| `wctNo` | `String` | `` | 181 |

## `TicketDetailResponse`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvCancel` | `String` | `` | 228 |
| `addSrvFlg` | `String` | `` | 229 |
| `addSrvList` | `AddSrvList` | `` | 230 |
| `cmpa_info` | `List<CompanionInfo>` | `` | 231 |
| `cstmzPhrase` | `String` | `` | 232 |
| `dcnt_crd_info` | `DiscountCardInfo` | `` | 233 |
| `dtlList` | `List<DelayInfo>` | `` | 234 |
| `gurdSmsFlg` | `String` | `` | 235 |
| `h_abrd_ps_nm` | `String` | `` | 236 |
| `h_abrd_ps_sex` | `String` | `` | 237 |
| `h_cmtr_utl_trm_age_cd` | `String` | `` | 238 |
| `h_cmtr_utl_trm_cd_nm` | `String` | `` | 239 |
| `h_compa_brth` | `String` | `` | 240 |
| `h_compa_nm` | `String` | `` | 241 |
| `h_dlay_flg` | `String` | `` | 242 |
| `h_dlay_tk_flg` | `String` | `` | 243 |
| `h_dscp_no` | `String` | `` | 244 |
| `h_dtour` | `String` | `` | 245 |
| `h_orgtk_ret_pwd` | `String` | `` | 246 |
| `h_orgtk_ret_sale_dt` | `String` | `` | 247 |
| `h_orgtk_sale_sqno` | `String` | `` | 248 |
| `h_orgtk_wct_no` | `String` | `` | 249 |
| `h_pbp_acep_tgt_flg` | `String` | `` | 250 |
| `h_pnr_no` | `String` | `` | 251 |
| `h_qrcode` | `String` | `` | 252 |
| `h_ret_flg` | `String` | `` | 253 |
| `h_sale_dt` | `String` | `` | 254 |
| `h_sale_tm` | `String` | `` | 255 |
| `h_schd_tk_knd_cd` | `String` | `` | 256 |
| `h_tk_knd_cd` | `String` | `` | 257 |
| `h_tk_knd_nm` | `String` | `` | 258 |
| `h_tot_disc_amt` | `String` | `` | 259 |
| `h_tot_fare_amt` | `String` | `` | 260 |
| `h_tot_rcvd_amt` | `String` | `` | 261 |
| `h_trn_running_flg` | `String` | `` | 262 |
| `h_wct_nm` | `String` | `` | 263 |
| `limousine` | `Limousine` | `` | 264 |
| `limousineRsvPsbFlg` | `String` | `` | 265 |
| `mlgSaveFlg` | `String` | `` | 266 |
| `parkingLotUrl` | `String` | `` | 267 |
| `pbpAcepPsQryFlg` | `String` | `` | 268 |
| `pbpAcepPsbFlg` | `String` | `` | 269 |
| `psgNmList` | `List<FamilyInfo>` | `` | 270 |
| `retPsbFlg` | `String` | `` | 271 |
| `s_brth` | `String` | `` | 272 |
| `seatAppPsbFlg` | `String` | `` | 273 |
| `stnLeadFlg` | `String` | `` | 274 |
| `stndAppPsbFlg` | `String` | `` | 275 |
| `ticketTimeBgColor` | `String` | `` | 276 |
| `ticket_infos` | `TicketInfos` | `` | 277 |
| `tripChgFlg` | `String` | `` | 278 |
| `whchSrvRcpFlg` | `String` | `` | 279 |
| `whchSrvReqPsbFlg` | `String` | `` | 280 |

## `TicketInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cabFaclLead` | `String` | `` | 503 |
| `h_arv_dt` | `String` | `` | 504 |
| `h_arv_rs_stn_cd` | `String` | `` | 505 |
| `h_arv_rs_stn_nm` | `String` | `` | 506 |
| `h_arv_tm` | `String` | `` | 507 |
| `h_ddck_scar_no` | `String` | `` | 508 |
| `h_dpt_dt` | `String` | `` | 509 |
| `h_dpt_rs_stn_cd` | `String` | `` | 510 |
| `h_dpt_rs_stn_nm` | `String` | `` | 511 |
| `h_dpt_tm` | `String` | `` | 512 |
| `h_dvd_anx_dv_cd` | `String` | `` | 513 |
| `h_itx_sixed_yn` | `String` | `` | 514 |
| `h_jrny_sqno` | `String` | `` | 515 |
| `h_jrny_tp_cd` | `String` | `` | 516 |
| `h_menu_actv_flg` | `String` | `` | 517 |
| `h_plf_no` | `String` | `` | 518 |
| `h_psrm_cl_cd` | `String` | `` | 519 |
| `h_psrm_cl_nm` | `String` | `` | 520 |
| `h_sr_include_yn` | `String` | `` | 521 |
| `h_trn_clsf_cd` | `String` | `` | 522 |
| `h_trn_clsf_nm` | `String` | `` | 523 |
| `h_trn_gp_cd` | `String` | `` | 524 |
| `h_trn_no` | `String` | `` | 525 |
| `tk_seat_info` | `List<TicketSeatInfo>` | `` | 526 |
| `vrBnrUrl` | `String` | `` | 527 |

## `TicketInfos`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ticket_info` | `List<TicketInfo>` | `` | 634 |

## `TicketSeatInfo`

- Source: `com/korail/talk/network/dao/refund/TicketDetailDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_buy_ps_nm` | `String` | `` | 645 |
| `h_chckn_stt_cd` | `String` | `` | 646 |
| `h_dcnt_knd_cd` | `String` | `` | 647 |
| `h_dcnt_knd_nm` | `String` | `` | 648 |
| `h_psg_tp_cd` | `String` | `` | 649 |
| `h_psg_tp_nm` | `String` | `` | 650 |
| `h_seat_att_cd_2` | `String` | `` | 651 |
| `h_seat_att_cd_4` | `String` | `` | 652 |
| `h_seat_no` | `String` | `` | 653 |
| `h_sgr_nm` | `String` | `` | 654 |
| `h_srcar_no` | `String` | `` | 655 |

## `CmtrInfoRequest`

- Source: `com/korail/talk/network/dao/research/CmtrInfoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `JOB_DV_CD_A` | `String` | `` | 13 |
| `JOB_DV_CD_B` | `String` | `` | 14 |
| `JOB_DV_CD_C` | `String` | `` | 15 |
| `cmtrKndCd` | `String` | `` | 16 |
| `cmtrUtlAgeCd` | `List<String>` | `` | 17 |
| `inquiryType` | `String` | `` | 18 |
| `jobDvCd` | `String` | `` | 19 |
| `ogtkRetPwd` | `String` | `` | 20 |
| `ogtkSaleDd` | `String` | `` | 21 |
| `ogtkSaleSqno` | `String` | `` | 22 |
| `ogtkSaleWctNo` | `String` | `` | 23 |
| `psgCnt` | `int` | `` | 24 |
| `psgPrnb` | `List<Integer>` | `` | 25 |

## `CmtrInfoResponse`

- Source: `com/korail/talk/network/dao/research/CmtrInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvGdFlg` | `String` | `` | 112 |
| `avlPrnbFrom` | `int` | `` | 113 |
| `avlPrnbTo` | `int` | `` | 114 |
| `cmpaFlg` | `String` | `` | 115 |
| `cmtrKndCd` | `String` | `` | 116 |
| `cmtrUtlAgeCd` | `String` | `` | 117 |
| `menuId` | `String` | `` | 118 |
| `poppMsg` | `String` | `` | 119 |
| `prmoMsg` | `String` | `` | 120 |
| `prmoUrl` | `String` | `` | 121 |
| `psgList` | `List<Psg>` | `` | 122 |
| `seatAttCd1` | `String` | `` | 123 |

## `Psg`

- Source: `com/korail/talk/network/dao/research/CmtrInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cmtrUtlAgeCd` | `String` | `` | 178 |
| `comnCdNm` | `String` | `` | 179 |
| `psgPrnbFrom` | `int` | `` | 180 |
| `psgPrnbTo` | `int` | `` | 181 |

## `ConvenienceSettingRequest`

- Source: `com/korail/talk/network/dao/research/ConvenienceSettingDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custMgNo` | `String` | `` | 14 |
| `medDvCd` | `String` | `` | 15 |
| `reqSqno` | `String` | `` | 16 |

## `ConvenienceSettingResponse`

- Source: `com/korail/talk/network/dao/research/ConvenienceSettingDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mainList` | `List<CustTripInfo>` | `` | 47 |

## `CustTripInfo`

- Source: `com/korail/talk/network/dao/research/ConvenienceSettingDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSeatAttCd` | `String` | `` | 58 |
| `adltHdcpPrnb` | `String` | `` | 59 |
| `adulCnt` | `String` | `` | 60 |
| `arvStnCd` | `String` | `` | 61 |
| `arvStnNm` | `String` | `` | 62 |
| `babyAcpnPrnb` | `String` | `` | 63 |
| `chgDttm` | `String` | `` | 64 |
| `chgUsrId` | `String` | `` | 65 |
| `chilCnt` | `String` | `` | 66 |
| `chldHdcpPrnb` | `String` | `` | 67 |
| `custMgNo` | `String` | `` | 68 |
| `dayCd` | `String` | `` | 69 |
| `dirSeatAttGpCd` | `String` | `` | 70 |
| `dirtChtnDvCd` | `String` | `` | 71 |
| `dptStnCd` | `String` | `` | 72 |
| `dptStnNm` | `String` | `` | 73 |
| `ectbTrnDptTm` | `String` | `` | 74 |
| `edrPrnb` | `String` | `` | 75 |
| `inclFlg` | `String` | `` | 76 |
| `jobStHr` | `String` | `` | 77 |
| `locSeatAttGpCd` | `String` | `` | 78 |
| `medDvCd` | `String` | `` | 79 |
| `psrmClCd` | `String` | `` | 80 |
| `ptwtTtl` | `String` | `` | 81 |
| `regDttm` | `String` | `` | 82 |
| `regSqno` | `String` | `` | 83 |
| `regUsrId` | `String` | `` | 84 |
| `tripDno` | `String` | `` | 85 |
| `trnClsfCd` | `String` | `` | 86 |
| `trnCnecFlg` | `String` | `` | 87 |
| `trnGpCd` | `String` | `` | 88 |
| `utlDno` | `String` | `` | 89 |

## `MergeSeatInquiryRequest`

- Source: `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `abrdDt` | `String` | `` | 14 |
| `arvRsStnNm` | `String` | `` | 15 |
| `dptRsStnNm` | `String` | `` | 16 |
| `psrmClCd` | `String` | `` | 17 |
| `runtDt` | `String` | `` | 18 |
| `seatAttCd` | `String` | `` | 19 |
| `selRsStnNm` | `String` | `` | 20 |
| `totPsgNum` | `String` | `` | 21 |
| `trnNo` | `String` | `` | 22 |

## `MergeSeatInquiryResponse`

- Source: `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `midStnList` | `List<MidStnList.MidStationInfo>` | `` | 101 |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | `` | 102 |

## `MidStationInfo`

- Source: `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `rsStnCd` | `String` | `` | 120 |
| `rsStnNm` | `String` | `` | 121 |
| `runOrdr` | `String` | `` | 122 |

## `MidStnList`

- Source: `com/korail/talk/network/dao/research/MergeSeatInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `midStationInfo` | `List<MidStationInfo>` | `` | 117 |

## `NCardExtensionRequest`

- Source: `com/korail/talk/network/dao/research/NCardExtensionDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `saleDd` | `String` | `` | 13 |
| `saleSqno` | `String` | `` | 14 |
| `saleWctNo` | `String` | `` | 15 |
| `tkRetPwd` | `String` | `` | 16 |

## `NCardHistoryInfo`

- Source: `com/korail/talk/network/dao/research/NCardHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `apdUsrFlg` | `String` | `` | 13 |
| `arvStnNm` | `String` | `` | 14 |
| `custNm` | `String` | `` | 15 |
| `dptStnNm` | `String` | `` | 16 |
| `runDt1` | `String` | `` | 17 |

## `NCardHistoryRequest`

- Source: `com/korail/talk/network/dao/research/NCardHistoryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dcntCrdNo` | `String` | `` | 64 |

## `NCardHistoryResponse`

- Source: `com/korail/talk/network/dao/research/NCardHistoryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkUseList` | `List<NCardHistoryInfo>` | `` | 79 |

## `NCardInquiryRequest`

- Source: `com/korail/talk/network/dao/research/NCardInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnNm` | `String` | `` | 15 |
| `dcntCrdKndCd` | `String` | `` | 16 |
| `dcntCrdKndMgNo` | `String` | `` | 17 |
| `dirtChtnDvCd` | `String` | `` | 18 |
| `dptDt` | `String` | `` | 19 |
| `dptRsStnNm` | `String` | `` | 20 |
| `dptTm` | `String` | `` | 21 |
| `qryPgNo` | `String` | `` | 22 |
| `sectionNo` | `int` | `` | 23 |
| `trnGpCd` | `String` | `` | 24 |
| `usePsbTno` | `String` | `` | 25 |
| `useTrmDno` | `String` | `` | 26 |

## `NCardInquiryResponse`

- Source: `com/korail/talk/network/dao/research/NCardInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fllwPgExt` | `String` | `` | 129 |
| `trnScdlList` | `List<TrainInfo>` | `` | 130 |

## `TrainInfo`

- Source: `com/korail/talk/network/dao/research/NCardInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 145 |
| `arvRsStnNm` | `String` | `` | 146 |
| `arvStnConsOrdr` | `String` | `` | 147 |
| `cmtrPrc` | `String` | `` | 148 |
| `dirtChtnDvCd` | `String` | `` | 149 |
| `dptRsStnCd` | `String` | `` | 150 |
| `dptRsStnNm` | `String` | `` | 151 |
| `dptStnConsOrdr` | `String` | `` | 152 |
| `dturCd` | `String` | `` | 153 |
| `dturNm` | `String` | `` | 154 |
| `routCd` | `String` | `` | 155 |
| `runDt` | `String` | `` | 156 |
| `stationInfo` | `Spanned` | `` | 157 |
| `stationStringInfo` | `String` | `` | 158 |
| `trnGpCd` | `String` | `` | 159 |
| `trnNo` | `String` | `` | 160 |

## `NCardReservationRequest`

- Source: `com/korail/talk/network/dao/research/NCardReservationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `APD_CUST_NAME` | `String` | `` | 16 |
| `CUSTOM_STATION_INFO` | `String` | `` | 17 |
| `custMgNo` | `String` | `` | 18 |
| `dcntCrdKndMgNo` | `String` | `` | 19 |
| `usePsbTno` | `String` | `` | 20 |
| `vlidTrmStDt` | `String` | `` | 21 |
| `JRNY_CNT` | `String` | `` | 22 |
| `JRNY_TP_CD` | `String` | `` | 23 |
| `RUN_DT` | `String` | `` | 24 |
| `TRN_NO` | `String` | `` | 25 |
| `DPT_RS_STN_CD` | `String` | `` | 26 |
| `ARV_RS_STN_CD` | `String` | `` | 27 |
| `APD_USR_CNT` | `String` | `` | 28 |
| `CUST_MG_NO` | `String` | `` | 29 |
| `APD_CUST_TEL` | `String` | `` | 30 |
| `jrnyInfo` | `HashMap<String, String>` | `` | 31 |
| `apdUsrInfo` | `HashMap<String, String>` | `` | 32 |
| `mCustomData` | `HashMap<String, String>` | `` | 33 |

## `NCardReservationResponse`

- Source: `com/korail/talk/network/dao/research/NCardReservationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `lumpStlTgtNo` | `String` | `` | 128 |
| `mStationInfo` | `String` | `` | 129 |
| `mUserNames` | `String` | `` | 130 |
| `rcvdAmt` | `String` | `` | 131 |
| `usePsbTno` | `String` | `` | 132 |
| `vlidTrmClsDt` | `String` | `` | 133 |
| `vlidTrmStDt` | `String` | `` | 134 |

## `OgTkInquiryRequest`

- Source: `com/korail/talk/network/dao/research/OgTkInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ogTkData` | `HashMap<String, String>` | `` | 15 |
| `tkCnt` | `int` | `` | 16 |

## `OgTkInquiryResponse`

- Source: `com/korail/talk/network/dao/research/OgTkInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `orgTkList` | `List<OrgTk>` | `` | 39 |

## `CarInfo`

- Source: `com/korail/talk/network/dao/research/SearchCarListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_psrm_cl_nm` | `String` | `` | 16 |
| `h_rest_seat_cnt` | `int` | `` | 17 |
| `h_srcar_no` | `int` | `` | 18 |
| `seatAttInfos` | `List<SeatAttInfo>` | `` | 19 |

## `CarInfos`

- Source: `com/korail/talk/network/dao/research/SearchCarListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `srcar_info` | `List<CarInfo>` | `` | 42 |

## `SearchCarListResponse`

- Source: `com/korail/talk/network/dao/research/SearchCarListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_rcmd_srcar_no` | `int` | `` | 53 |
| `h_trn_no` | `String` | `` | 54 |
| `srcar_infos` | `CarInfos` | `` | 55 |

## `SeatAttInfo`

- Source: `com/korail/talk/network/dao/research/SearchCarListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `seatAttNm` | `String` | `` | 74 |

## `SearchSeatListResponse`

- Source: `com/korail/talk/network/dao/research/SearchSeatListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `layout_type` | `int` | `` | 16 |
| `seatList` | `List<Seat>` | `` | 17 |
| `seat_ary_cd` | `String` | `` | 18 |
| `seat_remain_count` | `int` | `` | 19 |
| `seat_total_count` | `int` | `` | 20 |
| `vrBnrUrl` | `String` | `` | 21 |
| `windowList` | `List<Window>` | `` | 22 |

## `Seat`

- Source: `com/korail/talk/network/dao/research/SearchSeatListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dir_seat_att_cd` | `String` | `` | 57 |
| `etc_seat_att_cd` | `String` | `` | 58 |
| `floor` | `String` | `` | 59 |
| `intg_msg` | `String` | `` | 60 |
| `intg_msg_cd` | `String` | `` | 61 |
| `rq_seat_att_cd` | `String` | `` | 62 |
| `sale_psb_flg` | `String` | `` | 63 |
| `seat_no` | `String` | `` | 64 |
| `seat_spec` | `String` | `` | 65 |
| `sqr_no` | `String` | `` | 66 |
| `vz_msg_dv_cd` | `String` | `` | 67 |

## `Window`

- Source: `com/korail/talk/network/dao/research/SearchSeatListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cls_loc_rt` | `float` | `` | 118 |
| `st_loc_rt` | `float` | `` | 119 |

## `SeatAssignScheduleViewRequest`

- Source: `com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnNm` | `String` | `` | 16 |
| `chtnArvRsStnNm` | `String` | `` | 17 |
| `dirtChtnDvCd` | `String` | `` | 18 |
| `dptDt` | `String` | `` | 19 |
| `dptRsStnNm` | `String` | `` | 20 |
| `dptTm` | `String` | `` | 21 |
| `menuId` | `String` | `` | 22 |
| `psgNum1` | `int` | `` | 23 |
| `psrmClCd` | `String` | `` | 24 |
| `seatAttCd1` | `String` | `` | 25 |
| `stlbDturDvNm1` | `String` | `` | 26 |
| `stlbDturDvNm2` | `String` | `` | 27 |
| `trnGpCd` | `String` | `` | 28 |
| `trnNo` | `String` | `` | 29 |

## `SeatAssignScheduleViewResponse`

- Source: `com/korail/talk/network/dao/research/SeatAssignScheduleViewDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_next_pg_flg` | `String` | `` | 150 |
| `trn_infos` | `RsvInquiryResponse.TrainInfos` | `` | 151 |

## `GudieSeatCndRequest`

- Source: `com/korail/talk/network/dao/reservation/GuideSeatCndDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `rqSeatAttCd` | `String` | `` | 12 |

## `SeatAssignReservationRequest`

- Source: `com/korail/talk/network/dao/reservation/SeatAssignReservationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custMgNo` | `String` | `` | 20 |
| `menuId` | `String` | `` | 21 |
| `rqScarNum` | `String` | `` | 22 |
| `stndFlg` | `String` | `` | 23 |
| `totPrnb` | `String` | `` | 24 |
| `rJrny` | `RJrny` | `` | 25 |
| `rSrcar` | `RSrcar` | `` | 26 |
| `rSeat` | `RSeat` | `` | 27 |
| `rPsg` | `RPsg` | `` | 28 |
| `rOrtg` | `ROrtg` | `` | 29 |

## `TCReservationRequest`

- Source: `com/korail/talk/network/dao/reservation/TCReservationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `alcSeatDmnPsDvCd` | `String` | `` | 19 |
| `ctlDvCd` | `String` | `` | 20 |
| `frcSaleRsnCont` | `String` | `` | 21 |
| `intgTktIseFlg` | `String` | `` | 22 |
| `isePrnb` | `String` | `` | 23 |
| `jrny2Cnt` | `String` | `` | 24 |
| `prcFareReCalcFlg` | `String` | `` | 25 |
| `psg2Cnt` | `String` | `` | 26 |
| `stndSeatFlg` | `String` | `` | 27 |
| `tmpJobSqno` | `String` | `` | 28 |
| `totPrnb` | `String` | `` | 29 |
| `trvlKndCd` | `String` | `` | 30 |
| `rJrny` | `RJrny` | `` | 31 |
| `rSrcar` | `RSrcar` | `` | 32 |
| `rSeat` | `RSeat` | `` | 33 |
| `rPsg` | `RPsg` | `` | 34 |
| `rOrtg` | `ROrtg` | `` | 35 |
| `orgRDcp` | `RDscp` | `` | 36 |
| `rDscp` | `RDscp` | `` | 37 |

## `JrnyInfo`

- Source: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `train_infos` | `TrainInfos` | `` | 13 |

## `JrnyInfos`

- Source: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrny_info` | `List<JrnyInfo>` | `` | 24 |

## `TicketRsvHistoryResponse`

- Source: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrny_infos` | `JrnyInfos` | `` | 35 |

## `TrainInfo`

- Source: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_acpt_ps_flg` | `String` | `` | 46 |
| `h_arv_rs_stn_nm` | `String` | `` | 47 |
| `h_arv_tm` | `String` | `` | 48 |
| `h_dpt_rs_stn_nm` | `String` | `` | 49 |
| `h_dpt_tm` | `String` | `` | 50 |
| `h_ise_psb_tm` | `String` | `` | 51 |
| `h_ntisu_lmt_dt` | `String` | `` | 52 |
| `h_ntisu_lmt_tm` | `String` | `` | 53 |
| `h_ntisu_psb_dt` | `String` | `` | 54 |
| `h_payment_flg` | `String` | `` | 55 |
| `h_payment_msg` | `String` | `` | 56 |
| `h_pnr_no` | `String` | `` | 57 |
| `h_rsv_tp_cd` | `String` | `` | 58 |
| `h_run_dt` | `String` | `` | 59 |
| `h_stl_flg` | `String` | `` | 60 |
| `h_tot_seat_cnt` | `int` | `` | 61 |
| `h_tot_stnd_cnt` | `int` | `` | 62 |
| `h_trn_clsf_cd` | `String` | `` | 63 |
| `h_trn_clsf_nm` | `String` | `` | 64 |
| `h_trn_no` | `String` | `` | 65 |

## `TrainInfos`

- Source: `com/korail/talk/network/dao/reservation/TicketRsvHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `train_info` | `List<TrainInfo>` | `` | 152 |

## `AutoRsvCancelCheckRequest`

- Source: `com/korail/talk/network/dao/reservationCancel/AutoRsvCancelCheckDao.java`
- Extends: `RsvCancelCheckDao.RsvCancelCheckRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `trainInfo` | `RsvInquiryResponse.TrainInfos` | `` | 11 |

## `AutoRsvCancelRequest`

- Source: `com/korail/talk/network/dao/reservationCancel/AutoRsvCancelDao.java`
- Extends: `RsvCancelDao.RsvCancelRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `trainInfo` | `RsvInquiryResponse.TrainInfos` | `` | 11 |

## `ReservationChangeRequest`

- Source: `com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chgTno` | `String` | `` | 29 |
| `evntWctFlg` | `String` | `` | 30 |
| `lrgCrgFlg` | `String` | `` | 31 |
| `pnrNo` | `String` | `` | 32 |
| `psgCnt` | `String` | `` | 33 |
| `stndFlg` | `String` | `` | 34 |
| `totPrnb` | `String` | `` | 35 |
| `wctHndgCncDvCd` | `String` | `` | 36 |
| `rJrny` | `RJrny` | `` | 37 |
| `rSrcar` | `RSrcar` | `` | 38 |
| `rSeat` | `RSeat` | `` | 39 |
| `rPsg` | `RPsg` | `` | 40 |
| `rDscp` | `RDscp` | `` | 41 |

## `ReservationChangeResponse`

- Source: `com/korail/talk/network/dao/reservationCancel/ReservationChangeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyList` | `List<JrnyInfo>` | `` | 152 |

## `RsvCancelCheckRequest`

- Source: `com/korail/talk/network/dao/reservationCancel/RsvCancelCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidRsvChgNo` | `String` | `` | 12 |
| `txtJrnyCnt` | `String` | `` | 13 |
| `txtJrnySqno` | `String` | `` | 14 |
| `txtPnrNo` | `String` | `` | 15 |

## `RsvCancelRequest`

- Source: `com/korail/talk/network/dao/reservationCancel/RsvCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidRsvChgNo` | `String` | `` | 13 |
| `mReservationResponse` | `ReservationResponse` | `` | 14 |
| `txtJrnyCnt` | `String` | `` | 15 |
| `txtJrnySqno` | `String` | `` | 16 |
| `txtPnrNo` | `String` | `` | 17 |

## `RsvWaitRequest`

- Source: `com/korail/talk/network/dao/reservationWait/RsvWaitDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mReservationResponse` | `ReservationResponse` | `` | 13 |
| `txtCpNo` | `String` | `` | 14 |
| `txtPnrNo` | `String` | `` | 15 |
| `txtPsrmClChgFlg` | `String` | `` | 16 |
| `txtSmsSndFlg` | `String` | `` | 17 |

## `RunningCalendar`

- Source: `com/korail/talk/network/dao/schedule/TrainCalendarDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `BOOL_NO` | `String` | `` | 17 |
| `BOOL_YES` | `String` | `` | 18 |
| `PEAK_SEASON_BIZ_DD_STG_CD` | `String` | `` | 19 |
| `aTrnOpFlg` | `String` | `` | 20 |
| `bizDdStgCd` | `String` | `` | 21 |
| `dTrnOpFlg` | `String` | `` | 22 |
| `dayDvCd` | `String` | `` | 23 |
| `gTrnOpFlg` | `String` | `` | 24 |
| `hldyDvCd` | `String` | `` | 25 |
| `oTrnOpFlg` | `String` | `` | 26 |
| `runDt` | `String` | `` | 27 |
| `sTrnOpFlg` | `String` | `` | 28 |
| `saleDdDvCd` | `String` | `` | 29 |
| `vTrnOpFlg` | `String` | `` | 30 |
| `xTrnOpFlg` | `String` | `` | 31 |

## `TrainCalendarResponse`

- Source: `com/korail/talk/network/dao/schedule/TrainCalendarDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `runningCalendar` | `List<RunningCalendar>` | `` | 14 |

## `DeviceResetRequest`

- Source: `com/korail/talk/network/dao/ticket/DeviceResetDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custNm` | `String` | `` | 12 |
| `dptDttm` | `String` | `` | 13 |
| `latitude` | `String` | `` | 14 |
| `longitude` | `String` | `` | 15 |
| `nonMbPwd` | `String` | `` | 16 |
| `stlbTrnClsfCd` | `String` | `` | 17 |
| `teln` | `String` | `` | 18 |
| `trnNo` | `String` | `` | 19 |

## `DlvRcvCustwRequest`

- Source: `com/korail/talk/network/dao/ticket/DlvRcvCustDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `saleDt` | `String` | `` | 12 |
| `saleSqno` | `String` | `` | 13 |
| `saleWctNo` | `String` | `` | 14 |
| `tkRetPwd` | `String` | `` | 15 |

## `DlvRcvCustwResponse`

- Source: `com/korail/talk/network/dao/ticket/DlvRcvCustDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acepCustMgNo` | `String` | `` | 54 |
| `acepCustNm` | `String` | `` | 55 |
| `acepCustTeln` | `String` | `` | 56 |
| `mbCrdNo` | `String` | `` | 57 |

## `GuardianReliefSmsRequest`

- Source: `com/korail/talk/network/dao/ticket/GuardianReliefSmsDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqno` | `String` | `` | 13 |
| `pnrNo` | `String` | `` | 14 |
| `rcvPsHndyTeln` | `String` | `` | 15 |

## `MaasCancelRequest`

- Source: `com/korail/talk/network/dao/ticket/MaasCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custMgNo` | `String` | `` | 12 |
| `lumpStlTgtNo` | `String` | `` | 13 |

## `MaasServiceCancelRequest`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cncAddSrvReqNo` | `String` | `` | 12 |
| `cncRetFee` | `String` | `` | 13 |
| `cncTgtCnt` | `String` | `` | 14 |
| `pnrNo` | `String` | `` | 15 |

## `MaasServiceCancelFeeRequest`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 12 |
| `addSrvReqNo` | `String` | `` | 13 |
| `coptEntRsvNo` | `String` | `` | 14 |

## `MaasServiceCancelFeeResponse`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceCancelFeeDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cncRetFee` | `String` | `` | 45 |

## `AddSrvItem`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 14 |
| `addSrvGdCd` | `String` | `` | 15 |
| `addSrvId` | `String` | `` | 16 |
| `addSrvMrkEntId` | `String` | `` | 17 |
| `addSrvMrkEntNm` | `String` | `` | 18 |
| `addSrvNm` | `String` | `` | 19 |
| `addSrvPrgSttCd` | `String` | `` | 20 |
| `addSrvReqNo` | `String` | `` | 21 |
| `cgPsRefAtclCont` | `String` | `` | 22 |
| `coptEntRsvNo` | `String` | `` | 23 |
| `dlivPsbClsTm` | `String` | `` | 24 |
| `dlivPsbStTm` | `String` | `` | 25 |
| `leadMsgCont1` | `String` | `` | 26 |
| `leadMsgCont2` | `String` | `` | 27 |
| `pnrNo` | `String` | `` | 28 |
| `reqDt` | `String` | `` | 29 |
| `reqQnty` | `String` | `` | 30 |
| `rsvSpecUrl` | `String` | `` | 31 |
| `utlClsDt` | `String` | `` | 32 |
| `utlStDt` | `String` | `` | 33 |

## `MaasServivceDetailRequest`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `qryDtFrom` | `String` | `` | 120 |
| `qryDtTo` | `String` | `` | 121 |

## `MaasServivceDetailResponse`

- Source: `com/korail/talk/network/dao/ticket/MaasServiceDetailListDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvList` | `List<AddSrvItem>` | `` | 144 |

## `Jrny`

- Source: `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acepCustNm` | `String` | `` | 13 |
| `acepCustTeln` | `String` | `` | 14 |
| `jrnyTpCd` | `String` | `` | 15 |
| `mbDvNm` | `String` | `` | 16 |
| `pbpAcepKndNm` | `String` | `` | 17 |
| `pbpRsvNo` | `String` | `` | 18 |
| `regDt` | `String` | `` | 19 |
| `seatList` | `List<Seat>` | `` | 20 |
| `wdrwPsbFlg` | `String` | `` | 21 |

## `PbpAcepSpecResponse`

- Source: `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkList` | `List<Tk>` | `` | 88 |

## `Seat`

- Source: `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psgTpDvNm` | `String` | `` | 99 |
| `psrmClCd` | `String` | `` | 100 |
| `psrmClNm` | `String` | `` | 101 |
| `scarNo` | `int` | `` | 102 |
| `seatNo` | `String` | `` | 103 |

## `Tk`

- Source: `com/korail/talk/network/dao/ticket/PbpAcepSpecDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyList` | `List<Jrny>` | `` | 130 |
| `pnrNo` | `String` | `` | 131 |
| `saleDt` | `String` | `` | 132 |
| `saleSqno` | `String` | `` | 133 |
| `saleWctNo` | `String` | `` | 134 |
| `tkRetPwd` | `String` | `` | 135 |

## `PbpTkWdrwRequest`

- Source: `com/korail/talk/network/dao/ticket/PbpTkWdrwDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pbpCnt` | `int` | `` | 13 |
| `pbpRsvNo` | `List<String>` | `` | 14 |
| `pnrNo` | `List<String>` | `` | 15 |
| `position` | `int` | `` | 16 |

## `Acep`

- Source: `com/korail/talk/network/dao/ticket/RecentDeliveryHistoryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acepCustMgFlg` | `String` | `` | 14 |
| `acepCustMgNo` | `String` | `` | 15 |
| `acepCustNm` | `String` | `` | 16 |
| `acepCustTeln` | `String` | `` | 17 |
| `acepCustTeln2` | `String` | `` | 18 |
| `mbCrdNo` | `String` | `` | 19 |

## `RcntDlvHstResponse`

- Source: `com/korail/talk/network/dao/ticket/RecentDeliveryHistoryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `acepList` | `List<Acep>` | `` | 65 |

## `SelfCheckinCancelRequest`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqno` | `String` | `` | 12 |
| `saleDt` | `String` | `` | 13 |
| `saleSqno` | `String` | `` | 14 |
| `saleWctNo` | `String` | `` | 15 |
| `tkRetPwd` | `String` | `` | 16 |

## `SelfCheckinInfoResponse`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDttm` | `String` | `` | 12 |
| `arvRsStnCd` | `String` | `` | 13 |
| `arvRsStnNm` | `String` | `` | 14 |
| `arvStnConsOrdr` | `String` | `` | 15 |
| `arvTmQb` | `String` | `` | 16 |
| `asgnSqno` | `String` | `` | 17 |
| `chcknCncDt` | `String` | `` | 18 |
| `chcknCncTm` | `String` | `` | 19 |
| `chcknDt` | `String` | `` | 20 |
| `chcknDvCd` | `String` | `` | 21 |
| `chcknSqno` | `String` | `` | 22 |
| `chcknTm` | `String` | `` | 23 |
| `dptDttm` | `String` | `` | 24 |
| `dptRsStnCd` | `String` | `` | 25 |
| `dptRsStnNm` | `String` | `` | 26 |
| `dptStnConsOrdr` | `String` | `` | 27 |
| `dptTmQb` | `String` | `` | 28 |
| `jrnySqno` | `String` | `` | 29 |
| `pnrNo` | `String` | `` | 30 |
| `runDt` | `String` | `` | 31 |
| `scarNo` | `String` | `` | 32 |
| `seatNo` | `String` | `` | 33 |
| `stlbTrnClsfNm` | `String` | `` | 34 |
| `trnNo` | `String` | `` | 35 |

## `SelfCheckinPossibleRequest`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinInfoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqno` | `String` | `` | 234 |
| `qrcode` | `String` | `` | 235 |
| `saleDt` | `String` | `` | 236 |
| `saleSqno` | `String` | `` | 237 |
| `saleWctNo` | `String` | `` | 238 |
| `tkRetPwd` | `String` | `` | 239 |

## `ConsList`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDttm` | `String` | `` | 13 |
| `arvRsStnCd` | `String` | `` | 14 |
| `arvStnConsOrdr` | `String` | `` | 15 |
| `asgnSqno` | `String` | `` | 16 |
| `cpsNo` | `String` | `` | 17 |
| `dptDttm` | `String` | `` | 18 |
| `dptRsStnCd` | `String` | `` | 19 |
| `dptStnConsOrdr` | `String` | `` | 20 |
| `jrnySqno` | `String` | `` | 21 |
| `pnrNo` | `String` | `` | 22 |
| `runDt` | `String` | `` | 23 |
| `scarNo` | `String` | `` | 24 |
| `seatNo` | `String` | `` | 25 |
| `tkKndCd` | `String` | `` | 26 |
| `trnGpCd` | `String` | `` | 27 |
| `trnNo` | `String` | `` | 28 |

## `SelfCheckinPossibleRequest`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqno` | `String` | `` | 99 |
| `qrcode` | `String` | `` | 100 |
| `saleDd` | `String` | `` | 101 |
| `saleSqno` | `String` | `` | 102 |
| `saleWctNo` | `String` | `` | 103 |
| `tkRetPwd` | `String` | `` | 104 |

## `SelfCheckinPossibleResponse`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinPossibleDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `consList` | `List<ConsList>` | `` | 159 |

## `SelfCheckinRegisterRequest`

- Source: `com/korail/talk/network/dao/ticket/SelfCheckinRegisterDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cpsNo` | `String` | `` | 12 |
| `jrnySqno` | `String` | `` | 13 |
| `saleDd` | `String` | `` | 14 |
| `saleSqno` | `String` | `` | 15 |
| `saleWctNo` | `String` | `` | 16 |
| `scarNo` | `String` | `` | 17 |
| `seatNo` | `String` | `` | 18 |
| `tkRetPwd` | `String` | `` | 19 |

## `TCCancelRequest`

- Source: `com/korail/talk/network/dao/ticket/TCCancelDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `LUMP_STL_TGT_NO` | `String` | `` | 13 |
| `hashMap` | `HashMap<String, String>` | `` | 14 |
| `lumpStlCnt` | `String` | `` | 15 |

## `DuplicationCheckRequest`

- Source: `com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrNo` | `String` | `` | 12 |

## `DuplicationCheckResponse`

- Source: `com/korail/talk/network/dao/ticket/TicketDuplicationCheckDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `rsvCnt` | `int` | `` | 27 |

## `JrnyList`

- Source: `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `plfNo` | `String` | `` | 15 |

## `PlfNoRequest`

- Source: `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkCnt` | `String` | `` | 26 |
| `tkRetNo` | `ArrayList<String>` | `` | 27 |

## `PlfNoResponse`

- Source: `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tkList` | `List<TkList>` | `` | 50 |

## `TkList`

- Source: `com/korail/talk/network/dao/ticket/UpdatePlatformDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnyList` | `List<JrnyList>` | `` | 61 |
| `saleDt` | `String` | `` | 62 |
| `saleSqno` | `String` | `` | 63 |
| `saleWctNo` | `String` | `` | 64 |
| `tkRetNo` | `String` | `` | 65 |
| `tkRetPwd` | `String` | `` | 66 |

## `CallSelfSeatChgInfoDaoRequest`

- Source: `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 15 |
| `dptRsStnCd` | `String` | `` | 16 |
| `psrmClCd` | `String` | `` | 17 |
| `runDt` | `String` | `` | 18 |
| `trnNo` | `String` | `` | 19 |

## `CallSelfSeatChgInfoResponse`

- Source: `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chgBfArvStnConsOrdr` | `String` | `` | 66 |
| `chgBfDptStnConsOrdr` | `String` | `` | 67 |
| `chgRsnList` | `List<ChgRsnList>` | `` | 68 |
| `chgStnList` | `List<ChgStnList>` | `` | 69 |
| `exsArvStnRunOrdr` | `String` | `` | 70 |
| `exsDptStnRunOrdr` | `String` | `` | 71 |
| `gnrmRsvPsbCd` | `String` | `` | 72 |
| `runDt` | `String` | `` | 73 |
| `sprmRsvPsbCd` | `String` | `` | 74 |
| `trnClsfCd` | `String` | `` | 75 |
| `trnClsfNm` | `String` | `` | 76 |
| `trnGpCd` | `String` | `` | 77 |
| `trnGpNm` | `String` | `` | 78 |
| `trnNo` | `String` | `` | 79 |

## `ChgRsnList`

- Source: `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `frcSaleRsnCont` | `String` | `` | 142 |
| `qryCode` | `String` | `` | 143 |
| `qryOrdr` | `String` | `` | 144 |

## `ChgStnList`

- Source: `com/korail/talk/network/dao/ticket/change/CallSelfSeatChgInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDt` | `String` | `` | 163 |
| `arvTm` | `String` | `` | 164 |
| `dptDt` | `String` | `` | 165 |
| `dptRsStnCd` | `String` | `` | 166 |
| `dptRsStnNm` | `String` | `` | 167 |
| `dptStnConsOrdr` | `String` | `` | 168 |
| `dptStnRunOrdr` | `String` | `` | 169 |
| `dptTm` | `String` | `` | 170 |
| `gnrmRestSeatNum` | `String` | `` | 171 |
| `sprmRestSeatNum` | `String` | `` | 172 |

## `StartStationDto`

- Source: `com/korail/talk/network/dao/ticket/change/StartStationDto.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDt` | `String` | `` | 7 |
| `arvTm` | `String` | `` | 8 |
| `chgBfArvStnConsOrdr` | `String` | `` | 9 |
| `chgBfDptStnConsOrdr` | `String` | `` | 10 |
| `dptDt` | `String` | `` | 11 |
| `dptRsStnCd` | `String` | `` | 12 |
| `dptRsStnNm` | `String` | `` | 13 |
| `dptStnConsOrdr` | `String` | `` | 14 |
| `dptStnRunOrdr` | `String` | `` | 15 |
| `dptTm` | `String` | `` | 16 |
| `exsArvStnRunOrdr` | `String` | `` | 17 |
| `exsDptStnRunOrdr` | `String` | `` | 18 |
| `gnrmRestSeatNum` | `String` | `` | 19 |
| `reasonCode` | `String` | `` | 20 |
| `runDt` | `String` | `` | 21 |
| `seatClass` | `String` | `` | 22 |
| `sprmRestSeatNum` | `String` | `` | 23 |
| `trnClsfCd` | `String` | `` | 24 |
| `trnClsfNm` | `String` | `` | 25 |
| `trnGpCd` | `String` | `` | 26 |
| `trnGpNm` | `String` | `` | 27 |
| `trnNo` | `String` | `` | 28 |

## `TripChgInfoDaoRequest`

- Source: `com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `tripChgDate` | `String` | `` | 15 |

## `TripChgInfoDaoResponse`

- Source: `com/korail/talk/network/dao/ticket/change/TripChgInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `lastRunDt` | `String` | `` | 30 |
| `tripChgDate` | `String` | `` | 31 |
| `tripChgDates` | `List<String>` | `` | 32 |

## `FresScarRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/FresScarDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvStnConsOrdr` | `String` | `` | 12 |
| `arvStnRunOrdr` | `String` | `` | 13 |
| `dptStnConsOrdr` | `String` | `` | 14 |
| `dptStnRunOrdr` | `String` | `` | 15 |
| `runDt` | `String` | `` | 16 |
| `trnNo` | `String` | `` | 17 |

## `FresScarResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/FresScarDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `fresCont` | `String` | `` | 72 |
| `fresScarNo` | `String` | `` | 73 |
| `fresTtl` | `String` | `` | 74 |

## `Price2Fare`

- Source: `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrnySqnoString` | `String` | `` | 16 |
| `psrmClNmString` | `String` | `` | 17 |
| `rcvdFareString` | `String` | `` | 18 |
| `rcvdPrcString` | `String` | `` | 19 |
| `sumAmtString` | `String` | `` | 20 |
| `trnNoString` | `String` | `` | 21 |
| `jrnySqno` | `String` | `` | 22 |
| `psrmClNm` | `String` | `` | 23 |
| `rcvdFare` | `String` | `` | 24 |
| `rcvdPrc` | `String` | `` | 25 |
| `sumAmt` | `String` | `` | 26 |
| `trnNo` | `String` | `` | 27 |

## `Price2FareDao`

- Source: `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `trnGpCd` | `String` | `` | 82 |
| `stlbTrnClsfCd` | `String` | `` | 83 |
| `dptRsStnCd` | `String` | `` | 84 |
| `arvRsStnCd` | `String` | `` | 85 |
| `runDt` | `String` | `` | 86 |
| `trnNo` | `String` | `` | 87 |
| `gdNo` | `String` | `` | 88 |
| `rqSeatAttCd` | `String` | `` | 89 |

## `Price2FareRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chtnDvCd` | `String` | `` | 128 |
| `mSelectIndex` | `int` | `` | 129 |
| `mTrainInfo` | `RsvInquiryResponse.TrainInfo[]` | `` | 130 |
| `price2FareParams` | `Price2FareParams` | `` | 131 |
| `trnCnt` | `String` | `` | 132 |
| `txtMenuId` | `String` | `` | 133 |

## `Price2FareResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/Price2FareDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `prcList` | `List<Price2Fare>` | `` | 180 |

## `JrnyInfo`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `prc_fare` | `List<PriceFare>` | `` | 153 |

## `PrcFareList`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrny_info` | `List<JrnyInfo>` | `` | 150 |

## `PriceFare`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_psg_tp_nm` | `String` | `` | 15 |
| `h_psrm_cl_nm` | `String` | `` | 16 |
| `h_rg_rcvd_amt` | `String` | `` | 17 |

## `PriceFareDao`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`
- Extends: `BaseDao`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `TRN_CLSF_CD1` | `String` | `` | 36 |
| `DPT_RS_STN_CD1` | `String` | `` | 37 |
| `ARV_RS_STN_CD1` | `String` | `` | 38 |
| `RUN_DT1` | `String` | `` | 39 |
| `TRN_NO1` | `String` | `` | 40 |
| `TRN_GP_CD1` | `String` | `` | 41 |
| `TRN_CLSF_CD1_1` | `String` | `` | 42 |
| `DPT_RS_STN_CD1_1` | `String` | `` | 43 |
| `ARV_RS_STN_CD1_1` | `String` | `` | 44 |
| `RUN_DT1_1` | `String` | `` | 45 |
| `TRN_NO1_1` | `String` | `` | 46 |
| `TRN_GP_CD1_1` | `String` | `` | 47 |

## `PriceFareRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `mSelectIndex` | `int` | `` | 78 |
| `mTrainInfo` | `RsvInquiryResponse.TrainInfo` | `` | 79 |
| `priceFareParams` | `PriceFareParams` | `` | 80 |
| `txtChtrDvCd1` | `String` | `` | 81 |
| `txtMenuId` | `String` | `` | 82 |
| `txtRtnDvCd` | `String` | `` | 83 |
| `txtSeatAttCd4` | `String` | `` | 84 |

## `PriceFareResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/PriceFareDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `prc_fare_list` | `PrcFareList` | `` | 147 |

## `SeatAddInfo`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_psg_num` | `int` | `` | 14 |

## `SeatAddInfos`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `seat_add_info` | `List<SeatAddInfo>` | `` | 25 |

## `SeatInfo`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_seat_att_cd` | `String` | `` | 36 |
| `seat_add_infos` | `SeatAddInfos` | `` | 37 |

## `SeatInfos`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `seat_info` | `List<SeatInfo>` | `` | 52 |

## `TourTrainInfoRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arrivalStn` | `String` | `` | 63 |
| `jobDv` | `String` | `` | 64 |
| `startStn` | `String` | `` | 65 |
| `title` | `String` | `` | 66 |
| `txtTrnGpCd` | `String` | `` | 67 |

## `TourTrainInfoResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/TourTrainInfoDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `seat_infos` | `SeatInfos` | `` | 114 |

## `TimeInfo`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `actArvDlayTnum` | `int` | `` | 13 |
| `actArvDt` | `String` | `` | 14 |
| `actArvTm` | `String` | `` | 15 |
| `actDptDt` | `String` | `` | 16 |
| `actDptTm` | `String` | `` | 17 |
| `arvDt` | `String` | `` | 18 |
| `arvTm` | `String` | `` | 19 |
| `dptDt` | `String` | `` | 20 |
| `dptTm` | `String` | `` | 21 |
| `expnArvDlayTnum` | `String` | `` | 22 |
| `expnDptDlayTnum` | `String` | `` | 23 |
| `rgulFlg` | `String` | `` | 24 |
| `saodFlg` | `String` | `` | 25 |
| `stopStnNm` | `String` | `` | 26 |

## `TrainScheduleRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtRunDt` | `String` | `` | 93 |
| `txtTrnNo` | `String` | `` | 94 |

## `TrainScheduleResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainScheduleDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayDtlRsnCont` | `String` | `` | 117 |
| `dlayList` | `List<TimeInfo>` | `` | 118 |
| `msgCont` | `String` | `` | 119 |
| `runDt1` | `String` | `` | 120 |
| `runSegOrdr` | `String` | `` | 121 |
| `trnDptFlg` | `String` | `` | 122 |
| `trnNo1` | `String` | `` | 123 |

## `TrainSelectStationRequest`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvRsStnCd` | `String` | `` | 13 |
| `dptRsStnCd` | `String` | `` | 14 |

## `TrainSelectStationResponse`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chtnList` | `List<TransferStationInfo>` | `` | 37 |

## `TransferStationInfo`

- Source: `com/korail/talk/network/dao/trainsInfo/TrainSelectStationDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `chtnRsStnCd` | `String` | `` | 48 |
| `chtnRsStnNm` | `String` | `` | 49 |

## `KorailPointInquiryResponse`

- Source: `com/korail/talk/network/dao/xPoint/KorailPointInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_cntc_chn_cont1` | `String` | `` | 12 |
| `h_cp_athn_flg` | `String` | `` | 13 |
| `h_cust_lead_flg_nm` | `String` | `` | 14 |
| `h_delay_cnt` | `String` | `` | 15 |
| `h_disc_coup_cnt` | `String` | `` | 16 |
| `h_emil_athn_flg` | `String` | `` | 17 |
| `h_hdcp_flg` | `String` | `` | 18 |
| `h_korail_point` | `String` | `` | 19 |
| `h_logn_tp_cd1` | `String` | `` | 20 |
| `h_logn_tp_cd2` | `String` | `` | 21 |
| `h_logn_tp_cd4` | `String` | `` | 22 |
| `h_logn_tp_cd5` | `String` | `` | 23 |
| `h_subt_dcs_cl_cd` | `String` | `` | 24 |
| `h_subt_dcs_cl_nm` | `String` | `` | 25 |

## `LPointInquiryRequest`

- Source: `com/korail/talk/network/dao/xPoint/LPointDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custRcgnNoVal` | `String` | `` | 12 |
| `jobDvCd` | `String` | `` | 13 |
| `pontPwd` | `String` | `` | 14 |

## `LPointInquiryResponse`

- Source: `com/korail/talk/network/dao/xPoint/LPointDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `custRcgnNoVal` | `String` | `` | 45 |
| `extrPontAmt` | `String` | `` | 46 |
| `prsCnqeVal` | `String` | `` | 47 |
| `pwdErrTno` | `String` | `` | 48 |

## `MileageInquiryRequest`

- Source: `com/korail/talk/network/dao/xPoint/MileageInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `nowPgNo` | `String` | `` | 13 |
| `pgPrCnt` | `String` | `` | 14 |
| `pontTpVal` | `String` | `` | 15 |
| `qryClsDt` | `String` | `` | 16 |
| `qryDvVal` | `String` | `` | 17 |
| `qryStDt` | `String` | `` | 18 |

## `MileageInquiryResponse`

- Source: `com/korail/talk/network/dao/xPoint/MileageInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `delPontValNum` | `String` | `` | 73 |
| `ktxMlgInfo` | `String` | `` | 74 |
| `pgCnt` | `String` | `` | 75 |
| `railNowSavePontValNum1` | `String` | `` | 76 |
| `specList` | `List<SpecList>` | `` | 77 |
| `totAcmRailPontValNum1` | `String` | `` | 78 |
| `totAvlAfltPontValNum` | `String` | `` | 79 |
| `totAvlRailPontValNum` | `String` | `` | 80 |
| `totAvlRailPontValNum1` | `String` | `` | 81 |
| `totUseRailPontValNum1` | `String` | `` | 82 |

## `SpecList`

- Source: `com/korail/talk/network/dao/xPoint/MileageInquiryDao.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dptDt` | `String` | `` | 129 |
| `mlgAcmDvCdNm` | `String` | `` | 130 |
| `pontAmt` | `String` | `` | 131 |
| `pontDvNm` | `String` | `` | 132 |
| `rcpDvNm` | `String` | `` | 133 |
| `savePontValNum` | `String` | `` | 134 |
| `stlAmt` | `String` | `` | 135 |

## `OKCashbagCertRequest`

- Source: `com/korail/talk/network/dao/xPoint/OKCashbagCertDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cpNo` | `String` | `` | 12 |

## `PointInquiryRequest`

- Source: `com/korail/talk/network/dao/xPoint/PointInquiryDao.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `inpDvCd` | `String` | `` | 12 |
| `pointDvCd` | `String` | `` | 13 |
| `stlCrdValidTrm` | `String` | `` | 14 |
| `xpointNo` | `String` | `` | 15 |
| `xpointPwd` | `String` | `` | 16 |

## `PointInquiryResponse`

- Source: `com/korail/talk/network/dao/xPoint/PointInquiryDao.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_avl_point` | `int` | `` | 63 |
| `h_corp_use_point` | `int` | `` | 64 |
| `h_join_point` | `int` | `` | 65 |
| `h_korail_point` | `int` | `` | 66 |
| `h_point` | `int` | `` | 67 |

## `AddSrvInfo`

- Source: `com/korail/talk/network/data/addService/ExtraProductInfo.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvDvCd` | `String` | `` | 22 |
| `addSrvMrkEntId` | `String` | `` | 23 |
| `addSrvMrkEntNm` | `String` | `` | 24 |
| `addSrvNm` | `String` | `` | 25 |
| `addSrvPrgSttCd` | `String` | `` | 26 |
| `addSrvReqNo` | `String` | `` | 27 |
| `addSrvUtlAmt` | `String` | `` | 28 |
| `cgPsRefAtclCont` | `String` | `` | 29 |
| `coptEntRsvNo` | `String` | `` | 30 |
| `imgPath` | `String` | `` | 31 |
| `leadMsgCont1` | `String` | `` | 32 |
| `leadMsgCont2` | `String` | `` | 33 |
| `leadTeln` | `String` | `` | 34 |
| `reqDt` | `String` | `` | 35 |
| `reqQnty` | `String` | `` | 36 |
| `reservationUrl` | `String` | `` | 37 |
| `shopMapImgPath` | `String` | `` | 38 |
| `spvsRsStnCd` | `String` | `` | 39 |
| `spvsRsStnCdNm` | `String` | `` | 40 |

## `ExtraProductInfo`

- Source: `com/korail/talk/network/data/addService/ExtraProductInfo.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSrvList` | `List<AddSrvInfo>` | `` | 11 |
| `arvDt` | `String` | `` | 12 |
| `arvRsStnCd` | `String` | `` | 13 |
| `arvTm` | `String` | `` | 14 |
| `dptDt` | `String` | `` | 15 |
| `dptRsStnCd` | `String` | `` | 16 |
| `dptTm` | `String` | `` | 17 |
| `jrnySqno` | `String` | `` | 18 |
| `pnrNo` | `String` | `` | 19 |

## `DiscountPriceParams`

- Source: `com/korail/talk/network/data/certification/DiscountPriceParams.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dcnt_knd_cd1` | `String` | `` | 5 |
| `hidDcntKndCd` | `String` | `` | 6 |
| `hidDscpNo` | `String` | `` | 7 |
| `hidFmlyNo` | `String` | `` | 8 |
| `psg_tp_dv_cd` | `String` | `` | 9 |
| `psrm_cl_cd` | `String` | `` | 10 |

## `ProductTrainInquiryRequest`

- Source: `com/korail/talk/network/request/inquiry/ProductTrainInquiryRequest.java`
- Extends: `RsvInquiryRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `txtGdNo` | `String` | `` | 7 |

## `RsvInquiryRequest`

- Source: `com/korail/talk/network/request/inquiry/RsvInquiryRequest.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `adultCount` | `int` | `` | 11 |
| `chtnCnt` | `String` | `` | 12 |
| `chtnRsStnCd1` | `String` | `` | 13 |
| `pgPrCnt` | `String` | `` | 14 |
| `qryDvCd` | `String` | `` | 15 |
| `qryStNo` | `String` | `` | 16 |
| `qryStTrnNo` | `String` | `` | 17 |
| `qryStTrnNo2` | `String` | `` | 18 |
| `radJobId` | `String` | `` | 19 |
| `selGoTrain` | `String` | `` | 20 |
| `totalCount` | `int` | `` | 21 |
| `trnGpCd1` | `String` | `` | 22 |
| `trnGpCnt` | `String` | `` | 23 |
| `txtGoAbrdDt` | `String` | `` | 24 |
| `txtGoEnd` | `String` | `` | 25 |
| `txtGoHour` | `String` | `` | 26 |
| `txtGoStart` | `String` | `` | 27 |
| `txtGoTrnNo` | `String` | `` | 28 |
| `txtMenuId` | `String` | `` | 29 |
| `txtPsgFlg_1` | `String` | `` | 30 |
| `txtPsgFlg_2` | `String` | `` | 31 |
| `txtPsgFlg_3` | `String` | `` | 32 |
| `txtPsgFlg_4` | `String` | `` | 33 |
| `txtPsgFlg_5` | `String` | `` | 34 |
| `txtSeatAttCd_2` | `String` | `` | 35 |
| `txtSeatAttCd_3` | `String` | `` | 36 |
| `txtSeatAttCd_4` | `String` | `` | 37 |
| `txtTrnGpCd` | `String` | `` | 38 |

## `TrainInquiryRequest`

- Source: `com/korail/talk/network/request/inquiry/TrainInquiryRequest.java`
- Extends: `RsvInquiryRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `adjStnScdlOfrFlg` | `String` | `` | 8 |
| `ebizCrossCheck` | `String` | `` | 9 |
| `etrPath` | `String` | `` | 10 |
| `mbCrdNo` | `String` | `` | 11 |
| `pgPrCnt` | `String` | `` | 12 |
| `qryDvCd` | `String` | `` | 13 |
| `qryStNo` | `String` | `` | 14 |
| `qryStTrnNo` | `String` | `` | 15 |
| `rtYn` | `String` | `` | 16 |
| `srtCheckYn` | `String` | `` | 17 |
| `tkDptDt` | `String` | `` | 18 |
| `tkDptTm` | `String` | `` | 19 |
| `tkPsrmClCd` | `String` | `` | 20 |
| `tkRcvdAmt` | `String` | `` | 21 |
| `tkTrnNo` | `String` | `` | 22 |
| `txtJobDv` | `String` | `` | 23 |

## `PushUpdateRequest`

- Source: `com/korail/talk/network/request/myTicket/PushUpdateRequest.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDt` | `String` | `` | 7 |
| `arvRsStnCd` | `String` | `` | 8 |
| `arvStnConsOrdr` | `String` | `` | 9 |
| `arvStnRunOrdr` | `String` | `` | 10 |
| `arvTm` | `String` | `` | 11 |
| `dptDt` | `String` | `` | 12 |
| `dptRsStnCd` | `String` | `` | 13 |
| `dptStnConsOrdr` | `String` | `` | 14 |
| `dptStnRunOrdr` | `String` | `` | 15 |
| `dptTm` | `String` | `` | 16 |
| `jrnySqno` | `String` | `` | 17 |
| `jrnyTpCd` | `String` | `` | 18 |
| `ogtkRetPwd` | `String` | `` | 19 |
| `ogtkSaleDd` | `String` | `` | 20 |
| `ogtkSaleSqno` | `String` | `` | 21 |
| `ogtkSaleWctNo` | `String` | `` | 22 |
| `roomClsfCd` | `String` | `` | 23 |
| `rqSeatAttCd` | `String` | `` | 24 |
| `runDt` | `String` | `` | 25 |
| `scarNo` | `String` | `` | 26 |
| `seatNo` | `String` | `` | 27 |
| `trnGpCd` | `String` | `` | 28 |
| `trnNo` | `String` | `` | 29 |

## `SeatSearchRequest`

- Source: `com/korail/talk/network/request/research/SeatSearchRequest.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ctlDvCd` | `String` | `` | 8 |
| `trnClsfNm` | `String` | `` | 9 |
| `txtArvRsStnCd` | `String` | `` | 10 |
| `txtArvStnRunOrdr` | `String` | `` | 11 |
| `txtDptDt` | `String` | `` | 12 |
| `txtDptRsStnCd` | `String` | `` | 13 |
| `txtDptStnRunOrdr` | `String` | `` | 14 |
| `txtGdNo` | `String` | `` | 15 |
| `txtMenuId` | `String` | `` | 16 |
| `txtPsrmClCd` | `String` | `` | 17 |
| `txtRunDt` | `String` | `` | 18 |
| `txtSeatAttCd` | `String` | `` | 19 |
| `txtSrcarNo` | `int` | `` | 20 |
| `txtTotPsgCnt` | `int` | `` | 21 |
| `txtTrnClsfCd` | `String` | `` | 22 |
| `txtTrnGpCd` | `String` | `` | 23 |
| `txtTrnNo` | `String` | `` | 24 |

## `ReservationRequest`

- Source: `com/korail/talk/network/request/reservation/ReservationRequest.java`
- Extends: `BaseRequest`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `hidFreeFlg` | `String` | `` | 14 |
| `isNotNonMemberShow` | `boolean` | `` | 15 |
| `pbepInfo` | `String` | `` | 16 |
| `pnrNo` | `String` | `` | 17 |
| `txtCpNo` | `String` | `` | 18 |
| `txtCustNm` | `String` | `` | 19 |
| `txtCustPw` | `String` | `` | 20 |
| `txtGdNo` | `String` | `` | 21 |
| `txtJobId` | `String` | `` | 22 |
| `txtMenuId` | `String` | `` | 23 |
| `txtStndFlg` | `String` | `` | 24 |
| `oPsg` | `OPsg` | `` | 25 |
| `oSeat` | `OSeat` | `` | 26 |
| `oJrny` | `OJrny` | `` | 27 |
| `oSrcar` | `OSrcar` | `` | 28 |

## `Dfpy`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dfpyNo` | `String` | `` | 45 |
| `dfpySrtCd` | `String` | `` | 46 |
| `dscpMgNo` | `String` | `` | 47 |
| `stlAmt` | `int` | `` | 48 |

## `JrnyInfo`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_arv_rs_stn_cd` | `String` | `` | 71 |
| `h_arv_rs_stn_nm` | `String` | `` | 72 |
| `h_arv_stn_cons_ordr` | `String` | `` | 73 |
| `h_arv_tm` | `String` | `` | 74 |
| `h_dpt_dt` | `String` | `` | 75 |
| `h_dpt_rs_stn_cd` | `String` | `` | 76 |
| `h_dpt_rs_stn_nm` | `String` | `` | 77 |
| `h_dpt_stn_cons_ordr` | `String` | `` | 78 |
| `h_dpt_tm` | `String` | `` | 79 |
| `h_fres_cnt` | `int` | `` | 80 |
| `h_jrny_sqno` | `String` | `` | 81 |
| `h_jrny_tp_cd` | `String` | `` | 82 |
| `h_rsv_chg_no` | `String` | `` | 83 |
| `h_seat_cnt` | `int` | `` | 84 |
| `h_stlb_trn_clsf_cd` | `String` | `` | 85 |
| `h_tot_seat_cnt` | `int` | `` | 86 |
| `h_tot_stnd_cnt` | `int` | `` | 87 |
| `h_trn_clsf_cd` | `String` | `` | 88 |
| `h_trn_clsf_nm` | `String` | `` | 89 |
| `h_trn_gp_cd` | `String` | `` | 90 |
| `h_trn_no` | `String` | `` | 91 |
| `lumpStlTgtNo` | `String` | `` | 92 |
| `seat_infos` | `SeatInfos` | `` | 93 |

## `JrnyInfos`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `jrny_info` | `List<JrnyInfo>` | `` | 192 |

## `PsgDiscAddInfo`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_duty_ref_rcgn_ps_dv_cd` | `String` | `` | 203 |
| `h_psg_sqno` | `int` | `` | 204 |

## `PsgDiscAddInfos`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psgDiscAdd_info` | `List<PsgDiscAddInfo>` | `` | 219 |

## `PsgInfo`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dlayOgtkRetPwd` | `String` | `` | 230 |
| `dlayOgtkSaleDt` | `String` | `` | 231 |
| `dlayOgtkSaleSqno` | `String` | `` | 232 |
| `dlayOgtkWctNo` | `String` | `` | 233 |
| `h_dcnt_knd_cd` | `String` | `` | 234 |
| `h_dcnt_knd_cd2` | `String` | `` | 235 |
| `h_dcsp_no` | `String` | `` | 236 |
| `h_dcsp_no2` | `String` | `` | 237 |
| `h_psg_info_per_prnb` | `String` | `` | 238 |
| `h_psg_tp_cd` | `String` | `` | 239 |

## `PsgInfos`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `psg_info` | `List<PsgInfo>` | `` | 286 |

## `ReservationResponse`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dfpyList` | `List<Dfpy>` | `` | 9 |
| `h_add_srv_flg` | `String` | `` | 10 |
| `h_cust_mg_no` | `String` | `` | 11 |
| `h_fmly_info_cfm_flg` | `String` | `` | 12 |
| `h_hdcp_ctfc_num` | `int` | `` | 13 |
| `h_ise_psb_dt` | `String` | `` | 14 |
| `h_ise_psb_tm` | `String` | `` | 15 |
| `h_jrny_cnt` | `String` | `` | 16 |
| `h_msg_mndry` | `String` | `` | 17 |
| `h_msg_txt5` | `String` | `` | 18 |
| `h_ntisu_lmt` | `String` | `` | 19 |
| `h_ntisu_lmt_dt` | `String` | `` | 20 |
| `h_ntisu_lmt_tm` | `String` | `` | 21 |
| `h_pay_limit_msg` | `String` | `` | 22 |
| `h_payment_flg` | `String` | `` | 23 |
| `h_payment_msg` | `String` | `` | 24 |
| `h_pnr_no` | `String` | `` | 25 |
| `h_pre_stl_tgt_flg` | `String` | `` | 26 |
| `h_sprm_fare` | `String` | `` | 27 |
| `h_tmp_job_sqno1` | `String` | `` | 28 |
| `h_tmp_job_sqno2` | `String` | `` | 29 |
| `h_tot_dcnt_amt` | `String` | `` | 30 |
| `h_tot_fare` | `String` | `` | 31 |
| `h_tot_prc` | `String` | `` | 32 |
| `h_tot_rcvd_amt` | `String` | `` | 33 |
| `h_wct_no` | `String` | `` | 34 |
| `jrny_infos` | `JrnyInfos` | `` | 35 |
| `ogtkRcvdAmt` | `int` | `` | 36 |
| `psgDiscAdd_infos` | `PsgDiscAddInfos` | `` | 37 |
| `psg_infos` | `PsgInfos` | `` | 38 |
| `scnIndcAmt` | `int` | `` | 39 |
| `stopStnList` | `List<StopStn>` | `` | 40 |
| `tkList` | `List<TK>` | `` | 41 |
| `totRetAmt` | `int` | `` | 42 |

## `SeatInfo`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dcnt_reld_no` | `String` | `` | 297 |
| `h_dcnt_knd_cd1` | `String` | `` | 298 |
| `h_dcnt_knd_cd2` | `String` | `` | 299 |
| `h_dcnt_knd_cd3` | `String` | `` | 300 |
| `h_dcnt_knd_cd4` | `String` | `` | 301 |
| `h_dcnt_knd_cd5` | `String` | `` | 302 |
| `h_dir_seat_att_cd` | `String` | `` | 303 |
| `h_psg_tp_cd` | `String` | `` | 304 |
| `h_psrm_cl_cd` | `String` | `` | 305 |
| `h_psrm_cl_nm` | `String` | `` | 306 |
| `h_rcvd_amt` | `String` | `` | 307 |
| `h_rq_seat_att_cd` | `String` | `` | 308 |
| `h_seat_fare` | `String` | `` | 309 |
| `h_seat_no` | `String` | `` | 310 |
| `h_seat_prc` | `String` | `` | 311 |
| `h_sgr_nm` | `String` | `` | 312 |
| `h_srcar_no` | `String` | `` | 313 |

## `SeatInfos`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `seat_info` | `List<SeatInfo>` | `` | 388 |

## `StopStn`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `pnrNo` | `String` | `` | 399 |

## `TK`

- Source: `com/korail/talk/network/response/certification/ReservationResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `saleWctNo` | `String` | `` | 410 |

## `RefundResponse`

- Source: `com/korail/talk/network/response/delay/RefundResponse.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `ticketList` | `List<TicketList>` | `` | 10 |
| `whlPgNum` | `int` | `` | 11 |

## `StlList`

- Source: `com/korail/talk/network/response/delay/RefundResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `stlMnsCd` | `String` | `` | 14 |

## `TicketList`

- Source: `com/korail/talk/network/response/delay/RefundResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `arvDt` | `String` | `` | 25 |
| `arvRsStnNm` | `String` | `` | 26 |
| `dlayFare` | `int` | `` | 27 |
| `dptRsStnNm` | `String` | `` | 28 |
| `jrnyOrdr` | `String` | `` | 29 |
| `jrnyStpTkFlg` | `String` | `` | 30 |
| `jrnyTpCd` | `String` | `` | 31 |
| `rcVdAmt` | `int` | `` | 32 |
| `rcvdAmt` | `int` | `` | 33 |
| `refundAmount` | `String` | `` | 34 |
| `refundInfo` | `String` | `` | 35 |
| `refundJrny` | `String` | `` | 36 |
| `saleDd` | `String` | `` | 37 |
| `saleSqNo` | `String` | `` | 38 |
| `saleWctNo` | `String` | `` | 39 |
| `stlList` | `List<StlList>` | `` | 40 |
| `stlbTrnClsfNm` | `String` | `` | 41 |
| `tkRetPwd` | `String` | `` | 42 |
| `trnNo` | `int` | `` | 43 |
| `trnRunStpCpstAmt` | `int` | `` | 44 |
| `trnStpRsStnCd` | `String` | `` | 45 |
| `trnStpRsStnCdNm` | `String` | `` | 46 |

## `Cmpn`

- Source: `com/korail/talk/network/response/research/Cmpn.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `cmpaNum` | `String` | `` | 5 |
| `custNm` | `String` | `` | 6 |
| `dcntAmt` | `String` | `` | 7 |
| `dcntKndCd` | `String` | `` | 8 |
| `dcntKndCd2` | `String` | `` | 9 |
| `dcntRt` | `String` | `` | 10 |
| `dlayOgtkRetPwd` | `String` | `` | 11 |
| `dlayOgtkSaleDt` | `String` | `` | 12 |
| `dlayOgtkSaleSqno` | `String` | `` | 13 |
| `dlayOgtkWctNo` | `String` | `` | 14 |
| `dscpNo` | `String` | `` | 15 |
| `dscpNo2` | `String` | `` | 16 |
| `dscpNo3` | `String` | `` | 17 |
| `psgTpDvCd` | `String` | `` | 18 |
| `psrmClCd` | `String` | `` | 19 |
| `saleFlrVal` | `String` | `` | 20 |

## `Jrny`

- Source: `com/korail/talk/network/response/research/Jrny.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `alcStdrDvCd` | `String` | `` | 7 |
| `arvDt` | `String` | `` | 8 |
| `arvRsStnCd` | `String` | `` | 9 |
| `arvRsStnNm` | `String` | `` | 10 |
| `arvStnConsOrdr` | `String` | `` | 11 |
| `arvTm` | `String` | `` | 12 |
| `cndnDcntGdFlg` | `String` | `` | 13 |
| `cndnDcntKndCd` | `String` | `` | 14 |
| `cndnDcntWdrwFlg` | `String` | `` | 15 |
| `custNm` | `String` | `` | 16 |
| `dptDt` | `String` | `` | 17 |
| `dptRsStnCd` | `String` | `` | 18 |
| `dptRsStnNm` | `String` | `` | 19 |
| `dptStnConsOrdr` | `String` | `` | 20 |
| `dptTm` | `String` | `` | 21 |
| `gdMrkFlg` | `String` | `` | 22 |
| `gdNo` | `String` | `` | 23 |
| `genChgAllwFlg` | `String` | `` | 24 |
| `hmtkFlg` | `String` | `` | 25 |
| `intgSaleFlg` | `String` | `` | 26 |
| `jrnyOrdr` | `String` | `` | 27 |
| `jrnySqno` | `String` | `` | 28 |
| `jrnyTpCd` | `String` | `` | 29 |
| `mbCrdNo` | `String` | `` | 30 |
| `medDvCd` | `String` | `` | 31 |
| `psgNm` | `String` | `` | 32 |
| `saleFlrVal` | `String` | `` | 33 |
| `seatList` | `List<Seat>` | `` | 34 |
| `snglTkFlg` | `String` | `` | 35 |
| `totSeatNum` | `String` | `` | 36 |
| `totStndNum` | `String` | `` | 37 |
| `trnGpCd` | `String` | `` | 38 |
| `trnNo` | `String` | `` | 39 |

## `OrgTk`

- Source: `com/korail/talk/network/response/research/OrgTk.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `adulCnt` | `String` | `` | 7 |
| `chgSaleTno` | `String` | `` | 8 |
| `chilCnt` | `String` | `` | 9 |
| `cmpnList` | `List<Cmpn>` | `` | 10 |
| `dfpyRcvdAmt` | `String` | `` | 11 |
| `dfpyRcvdFare` | `String` | `` | 12 |
| `dfpyRcvdPrc` | `String` | `` | 13 |
| `frcSaleRsnCont` | `String` | `` | 14 |
| `grpDcntCnt` | `String` | `` | 15 |
| `jrnyList` | `List<Jrny>` | `` | 16 |
| `mbCrdNo` | `String` | `` | 17 |
| `ogtkRetPwd` | `String` | `` | 18 |
| `ogtkSaleDt` | `String` | `` | 19 |
| `ogtkSaleSqno` | `String` | `` | 20 |
| `ogtkSaleWctNo` | `String` | `` | 21 |
| `pnrNo` | `String` | `` | 22 |
| `psgTpDvCd` | `String` | `` | 23 |
| `rcvdAmt` | `String` | `` | 24 |
| `rcvdFare` | `String` | `` | 25 |
| `rcvdPrc` | `String` | `` | 26 |
| `saleFlrVal` | `String` | `` | 27 |
| `smsSndFlg` | `String` | `` | 28 |
| `stlList` | `List<Stl>` | `` | 29 |
| `tkKndCd` | `String` | `` | 30 |

## `Seat`

- Source: `com/korail/talk/network/response/research/Seat.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `addSeatAttCd` | `String` | `` | 5 |
| `asgnSqno` | `String` | `` | 6 |
| `dcntKndCdNm1` | `String` | `` | 7 |
| `dcntKndCdNm2` | `String` | `` | 8 |
| `dfpyFlg` | `String` | `` | 9 |
| `dfpyRcvdFare` | `String` | `` | 10 |
| `dfpyRcvdPrc` | `String` | `` | 11 |
| `dirSeatAttCd` | `String` | `` | 12 |
| `etcSeatAttCd` | `String` | `` | 13 |
| `locSeatAttCd` | `String` | `` | 14 |
| `prtDcntKndCd` | `String` | `` | 15 |
| `psgSqno` | `String` | `` | 16 |
| `psgTpDvCd` | `String` | `` | 17 |
| `psrmClCd` | `String` | `` | 18 |
| `rcvdFare` | `String` | `` | 19 |
| `rcvdPrc` | `String` | `` | 20 |
| `rqSeatAttCd` | `String` | `` | 21 |
| `saleFlrVal` | `String` | `` | 22 |
| `scarNo` | `String` | `` | 23 |
| `seatNo` | `String` | `` | 24 |
| `seatNum` | `String` | `` | 25 |
| `smkSeatAttCd` | `String` | `` | 26 |

## `Stl`

- Source: `com/korail/talk/network/response/research/Stl.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `apvNo` | `String` | `` | 5 |
| `ismtMnthNum` | `String` | `` | 6 |
| `prepCrdKndCd` | `String` | `` | 7 |
| `prepCrdNo` | `String` | `` | 8 |
| `retFee` | `String` | `` | 9 |
| `saleFlrVal` | `String` | `` | 10 |
| `stlAmt` | `String` | `` | 11 |
| `stlBankCd` | `String` | `` | 12 |
| `stlCrdNo` | `String` | `` | 13 |
| `stlMnsCd` | `String` | `` | 14 |
| `stlNo` | `String` | `` | 15 |
| `stlSqno` | `String` | `` | 16 |

## `RcmdGdList`

- Source: `com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dcntAmt` | `String` | `` | 20 |
| `dcntSurRt` | `String` | `` | 21 |
| `famtPctDvCd` | `String` | `` | 22 |
| `gdNm` | `String` | `` | 23 |
| `gdNo` | `String` | `` | 24 |
| `rcvdFare` | `String` | `` | 25 |
| `rcvdPrc` | `String` | `` | 26 |
| `rcvdPrc2` | `String` | `` | 27 |

## `RsvInquiryResponse`

- Source: `com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java`
- Extends: `BaseResponse`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_ectb_trn_no_next` | `String` | `` | 9 |
| `h_gd_no` | `String` | `` | 10 |
| `h_next_pg_flg` | `String` | `` | 11 |
| `h_notice_msg` | `String` | `` | 12 |
| `h_prcd_trn_no_next` | `String` | `` | 13 |
| `h_qry_st_no_next` | `String` | `` | 14 |
| `h_rslt_cnt` | `String` | `` | 15 |
| `h_trn_no_next` | `String` | `` | 16 |
| `trn_infos` | `TrainInfos` | `` | 17 |

## `TrainInfo`

- Source: `com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `dturViaPopp` | `String` | `` | 66 |
| `elevDmgCtrl` | `String` | `` | 67 |
| `h_arv_dt` | `String` | `` | 68 |
| `h_arv_rs_stn_cd` | `String` | `` | 69 |
| `h_arv_rs_stn_nm` | `String` | `` | 70 |
| `h_arv_stn_cons_ordr` | `String` | `` | 71 |
| `h_arv_stn_run_ordr` | `String` | `` | 72 |
| `h_arv_tm` | `String` | `` | 73 |
| `h_car_tp_nm` | `String` | `` | 74 |
| `h_chg_trn_dv_cd` | `String` | `` | 75 |
| `h_chg_trn_seq` | `String` | `` | 76 |
| `h_cnec_trfc_nd_hm` | `String` | `` | 77 |
| `h_cnec_trfc_psb_flg` | `String` | `` | 78 |
| `h_cnec_trfc_rcvd_prc` | `String` | `` | 79 |
| `h_dlay_sale_flg` | `String` | `` | 80 |
| `h_dpt_dt` | `String` | `` | 81 |
| `h_dpt_rs_stn_cd` | `String` | `` | 82 |
| `h_dpt_rs_stn_nm` | `String` | `` | 83 |
| `h_dpt_stn_cons_ordr` | `String` | `` | 84 |
| `h_dpt_stn_run_ordr` | `String` | `` | 85 |
| `h_dpt_tm` | `String` | `` | 86 |
| `h_dtour_flg` | `String` | `` | 87 |
| `h_dtour_txt` | `String` | `` | 88 |
| `h_expct_dlay_hr` | `String` | `` | 89 |
| `h_expn_dpt_dlay_tnum` | `String` | `` | 90 |
| `h_free_rsv_cd` | `String` | `` | 91 |
| `h_free_sracar_cnt` | `String` | `` | 92 |
| `h_gen_psrm_cl_nm` | `String` | `` | 93 |
| `h_gen_rsv_cd` | `String` | `` | 94 |
| `h_gen_rsv_cd2` | `String` | `` | 95 |
| `h_info_txt` | `String` | `` | 96 |
| `h_jrny_rsv_cd` | `String` | `` | 97 |
| `h_jrny_rsv_nm` | `String` | `` | 98 |
| `h_nonstop_msg` | `String` | `` | 99 |
| `h_nonstop_msg_txt` | `String` | `` | 100 |
| `h_popup_msg` | `String` | `` | 101 |
| `h_rcvd_amt` | `String` | `` | 102 |
| `h_rcvd_fare` | `String` | `` | 103 |
| `h_rcvd_prc2` | `String` | `` | 104 |
| `h_rd_seat_map_flg` | `String` | `` | 105 |
| `h_rsv_psb_nm` | `String` | `` | 106 |
| `h_run_dt` | `String` | `` | 107 |
| `h_run_tm` | `String` | `` | 108 |
| `h_seat_att_cd` | `String` | `` | 109 |
| `h_smns_trn_flg` | `String` | `` | 110 |
| `h_spe_disc_rt` | `String` | `` | 111 |
| `h_spe_psrm_cl_nm` | `String` | `` | 112 |
| `h_spe_rsv_cd` | `String` | `` | 113 |
| `h_spe_rsv_cd2` | `String` | `` | 114 |
| `h_spe_rsv_psb_nm` | `String` | `` | 115 |
| `h_station_popup_msg` | `String` | `` | 116 |
| `h_stnd_rsv_cd` | `String` | `` | 117 |
| `h_train_disc_gen_rt` | `String` | `` | 118 |
| `h_train_disc_origin_rt` | `String` | `` | 119 |
| `h_trn_clsf_cd` | `String` | `` | 120 |
| `h_trn_clsf_nm` | `String` | `` | 121 |
| `h_trn_gp_cd` | `String` | `` | 122 |
| `h_trn_no` | `String` | `` | 123 |
| `h_use_tim_care_atcl_cont` | `String` | `` | 124 |
| `h_wait_rsv_flg` | `String` | `` | 125 |
| `h_yms_apl_flg` | `String` | `` | 126 |
| `rcmdGdList` | `List<RcmdGdList>` | `` | 127 |
| `totPsgCnt` | `int` | `` | 128 |
| `txtGdNo` | `String` | `` | 129 |

## `TrainInfos`

- Source: `com/korail/talk/network/response/seatMovie/RsvInquiryResponse.java`

| Field | Type | Serialized/JSON Name | Line |
|---|---|---|---:|
| `h_merge_rsv_psb_flg` | `String` | `` | 456 |
| `trn_info` | `List<TrainInfo>` | `` | 457 |
