# Pass schedule candidate read

`KorailClient.get_pass_schedule()` exposes the static read-only contract for
`POST /classes/com.korail.mobile.pass.passScheduleInfoList`. The request is a
closed, frozen `PassScheduleRequest`; every train, route, date, page, and pass
value is caller-supplied. No runtime pass or menu code is hardcoded.

The exact form contains `Device`, `Version`, `Key`, `selGoTrain`,
`selGoAbrdDt`, `txtGoHour`, `radChgTrnDvCd`, `txtCmtrKndCd`,
`txtCmtrUtlTrmCd`, `txtCmtrUtlAgeCd`, `txtSelPage`, `txtCntPerPage`,
`txtGoStart`, `txtGoEnd`, and `txtWkndUseFlg`. The client issues one POST,
disables DynaPath for this route, and accepts only a full envelope whose
`strResult` is exactly `SUCC`.

The response types only project the statically evidenced
`schedule_info[].train_list` fields: `h_arv_rs_stn_cd`,
`h_arv_rs_stn_nm`, `h_dpt_rs_stn_cd`, `h_dpt_rs_stn_nm`, `h_dtour`,
`h_schd_prc`, `h_trn_gp_cd`, and `h_trn_no`. Collections are immutable and
request/response values are hidden from repr output.

The server session requirement is unverified. This route is not
account-neutral: the package applies a conservative client-side safety gate
that requires an authenticated session. Validate live only after login, and
do not reinterpret that client policy as evidence of the server's own
session rule.

This surface stops at candidate lookup. It does not expose the neighboring
pass reservation or payment calls, and it never selects, reserves, holds, or
pays for a candidate.

## Static evidence

- `PassService.java:27-29` fixes the POST path and all 15 transmitted fields.
- `CommRsvInquiryDao.java:207-208` confirms the exact execute order. Although
  its in-memory request type also carries `txtCmtrUtlTrmNm`, that field is not
  passed to the Retrofit method and is therefore deliberately absent here.
- `CommRsvInquiryDao.java:137-200` fixes the nested response wrappers and the
  eight projected train fields.
- `CommutationInquiryActivity.java:178-186` shows this read before the
  separate candidate-selection reservation flow. The package implements only
  the read.
