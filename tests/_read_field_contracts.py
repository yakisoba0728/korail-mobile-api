# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""읽기 전용 요청의 필드 이름·순서 계약 — 테스트 전용 픽스처.

이 모듈은 전송 경로에는 이제 없습니다. korail_mobile_api.safety 가 실제로 강제하는 것은
라우트 자체(assert_read_only_route)뿐이고, 어떤 필드 이름을 어떤 순서로 실어야 하는지는
여기 이 테스트 픽스처가 고정합니다(S3-safety-09, S3-safety-11, S3-safety-12,
S3-safety-13; 보고서 §3). 앱이 실제로 보내는 필드 집합·순서를 문서화한 회귀 고정
장치이며, 테스트 스위트가 직접 불러 씁니다.
"""

import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.safety import _are_name_value_pairs


_LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
_COMMON_CODE_PATH = "/classes/com.korail.mobile.common.code.do"
_SCHEDULE_VIEW_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.seatMovie.ScheduleView",
        "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial",
    }
)

# login.Login goes out in two shapes, and the union of their names is not a
# third one. The credential login (session._login) sends the member number and
# the transformed password, plus custId/etrPath/idx only when it has them; the
# social login (session.login_social) sends custId and no credentials at all.
# Each entry is (required, optional). KORAIL_EXACT_REQUEST_FIELDS carries the
# union, so the route is not skipped, and the checker holds a request to one
# shape at a time.
_ALTERNATIVE_REQUEST_FIELD_SHAPES: dict[
    str, tuple[tuple[frozenset[str], frozenset[str]], ...]
] = {
    _LOGIN_PATH: (
        (
            frozenset(
                {
                    "Device", "Version", "Key", "txtMemberNo", "txtPwd",
                    "txtInputFlg", "checkValidPw",
                }
            ),
            frozenset({"custId", "etrPath", "idx"}),
        ),
        (
            frozenset(
                {"Device", "Version", "Key", "txtInputFlg", "custId", "checkValidPw"}
            ),
            frozenset(),
        ),
    ),
}

#: The 17 fields shared by lms and research TResidualSeatsResearch.do.
_TRESIDUAL_SEATS_RESEARCH_FIELDS = frozenset(
    {
        "Device", "Version", "Key", "trnClsfCd", "trnGpCd", "runDt",
        "trnNo", "srcarNo", "psrmClCd", "dptRsStnCd", "arvRsStnCd",
        "seatAttCd", "dptStnRunOrdr", "arvStnRunOrdr", "totPsgCnt",
        "gdNo", "isArrow",
    }
)
#: The chtnRsStnCd1..32 connection-station block shared by both schedule views.
_CONNECTION_STATION_FIELDS = frozenset(f"chtnRsStnCd{index}" for index in range(1, 33))
#: ScheduleViewSpecial's exact field set.
_SCHEDULE_VIEW_SPECIAL_FIELDS = (
    frozenset(
        {
            "Device", "Version", "Key", "txtMenuId", "radJobId",
            "selGoTrain", "txtTrnGpCd", "txtGoStart", "txtGoEnd",
            "txtGoAbrdDt", "txtGoHour", "txtPsgFlg_1", "txtPsgFlg_2",
            "txtPsgFlg_3", "txtPsgFlg_4", "txtPsgFlg_5",
            "txtSeatAttCd_2", "txtSeatAttCd_3", "txtSeatAttCd_4",
            "ebizCrossCheck", "srtCheckYn", "rtYn",
            "adjStnScdlOfrFlg", "mbCrdNo", "qryDvCd", "qryStNo",
            "qryStTrnNo", "qryStTrnNo2", "pgPrCnt", "chtnCnt",
            "trnGpCnt", "trnGpCd1",
        }
    )
    | _CONNECTION_STATION_FIELDS
)
#: The optional fields both schedule views share.
_SCHEDULE_VIEW_OPTIONAL_FIELDS = (
    frozenset({"mbCrdNo", "chtnCnt", "trnGpCnt", "trnGpCd1"}) | _CONNECTION_STATION_FIELDS
)

KORAIL_EXACT_REQUEST_FIELDS: dict[str, frozenset[str]] = {
    "/file/CACHE/MobileService.cache": frozenset({"timeStamp"}),
    "/file/CACHE/prdMobilePlusMain.cache": frozenset({"timeStamp", "srtCheckYn"}),
    "/ebizcross/getUUID.do": frozenset(),
    "/classes/com.korail.mobile.common.stationinfo": frozenset(),
    "/classes/com.korail.mobile.common.stationdata": frozenset(),
    "/classes/com.korail.mobile.schedule.runDt": frozenset(
        {"Device", "Version", "Key", "timeStamp"}
    ),
    "/classes/com.korail.mobile.login.Logout": frozenset(
        {"Device", "Version", "Key", "timeStamp"}
    ),
    "/classes/com.korail.mobile.myTicket.MyTicketNewList.do": frozenset(
        {
            "Device", "Version", "Key", "txtDeviceId", "txtIndex",
            "h_page_no", "h_abrd_dt_from", "h_abrd_dt_to", "hiduserYn",
        }
    ),
    "/classes/com.korail.mobile.cart.showCartList": frozenset(
        {"Device", "Version", "Key", "pnrNo", "addSrvReqNo"}
    ),
    "/classes/com.korail.mobile.dlay.dptnBank.do": frozenset(
        {"Device", "Version", "Key"}
    ),
    "/classes/com.korail.mobile.passCard.DelayDiscountView": frozenset(
        {"Device", "Version", "Key", "h_page_no"}
    ),
    "/classes/com.korail.mobile.passCard.CouponView": frozenset(
        {"Device", "Version", "Key", "txtSelPage", "pnrNo"}
    ),
    "/classes/com.korail.mobile.pass.passInfoList": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "txtCmtrKndCd",
            "txtCmtrUtlTrmCd",
            "txtCmtrUtlAgeCd",
        }
    ),
    "/classes/com.korail.mobile.pass.passScheduleInfoList": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "selGoTrain",
            "selGoAbrdDt",
            "txtGoHour",
            "radChgTrnDvCd",
            "txtCmtrKndCd",
            "txtCmtrUtlTrmCd",
            "txtCmtrUtlAgeCd",
            "txtSelPage",
            "txtCntPerPage",
            "txtGoStart",
            "txtGoEnd",
            "txtWkndUseFlg",
        }
    ),
    "/classes/com.korail.mobile.pass.trGdMenuLt.do": frozenset(
        {"Device", "Version", "timeStamp"}
    ),
    "/classes/com.korail.mobile.pass.passMenu.do": frozenset(
        {"Device", "Version", "Key", "menuNo"}
    ),
    "/classes/com.korail.mobile.push.crwCallRq.do": frozenset(
        {"Device", "Version", "Key", "qryDvCd"}
    ),
    "/classes/com.korail.mobile.push.cmtrKnd.do": frozenset(
        {"Device", "Version", "Key", "cmtrKndCd"}
    ),
    "/classes/com.korail.mobile.product.ReservationList": frozenset(
        {
            "Device", "Version", "Key", "txtSelPage", "txtCntPerPage",
            "txtRsvSttCd", "txtStlSttCd",
        }
    ),
    "/classes/com.korail.mobile.product.ReservationDetail": frozenset(
        {"Device", "Version", "Key", "txtVrRsNo", "txtVrRsvSqNo"}
    ),
    "/classes/com.korail.mobile.receipt.ReceiptInfo": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_tk_ret_pwd",
            "txtIndex",
        }
    ),
    "/classes/com.korail.mobile.reservation.ReservationView": frozenset(
        {"Device", "Version", "Key", "timeStamp"}
    ),
    "/classes/com.korail.mobile.copt.gdMenuLt.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "lang",
            "timeStamp",
            "pnrNo",
            "tkRetNo",
            "addSrvReqNo",
        }
    ),
    "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial": _SCHEDULE_VIEW_SPECIAL_FIELDS,
    "/classes/com.korail.mobile.research.TrainResearch": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "Sid",
            "txtMenuId",
            "txtPsrmClCd",
            "txtRunDt",
            "txtDptDt",
            "txtDptTm",
            "txtTrnClsfCd",
            "txtTrnNo",
            "txtDptRsStnCd",
            "txtArvRsStnCd",
            "txtDptStnRunOrdr",
            "txtArvStnRunOrdr",
            "txtTrnGpCd",
            "txtTotPsgCnt",
            "txtSeatAttCd",
            "txtGdNo",
        }
    ),
    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do": (
        _TRESIDUAL_SEATS_RESEARCH_FIELDS | {"Sid", "ctlDvCd"}
    ),
    "/classes/com.korail.mobile.trn.fresScar.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "runDt",
            "trnNo",
            "dptStnConsOrdr",
            "arvStnConsOrdr",
            "dptStnRunOrdr",
            "arvStnRunOrdr",
        }
    ),
    "/classes/com.korail.mobile.reservation.guideSeatCnd.do": (
        frozenset({"Device", "Version", "Key", "rqSeatAttCd"})
    ),
    "/classes/com.korail.mobile.research.assignScheduleView.do": (
        frozenset(
            {
                "Device",
                "Version",
                "Key",
                "menuId",
                "dptDt",
                "dptTm",
                "dptRsStnNm",
                "arvRsStnNm",
                "trnGpCd",
                "psrmClCd",
                "seatAttCd1",
                "psgNum1",
                "stlbDturDvNm1",
                "dirtChtnDvCd",
                "chtnArvRsStnNm",
            }
        )
    ),
    "/classes/com.korail.mobile.research.mergeSeatsC.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "abrdDt",
            "runDt",
            "trnNo",
            "dptRsStnNm",
            "arvRsStnNm",
            "selRsStnNm",
            "psrmClCd",
            "seatAttCd",
            "totPsgNum",
        }
    ),
    "/classes/com.korail.mobile.lmu.scdlQry.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "dptDt",
            "dptRsStnCd",
            "arvRsStnCd",
            "trnGpCd",
            "psrmClCd",
            "dptTm",
            "trnNo",
            "seatAttCd",
            "rsvSaleDvCd",
        }
    ),
    "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do": (
        _TRESIDUAL_SEATS_RESEARCH_FIELDS
    ),
    "/classes/com.korail.mobile.cust.mchdDcntTgt.do": frozenset(
        {"Device", "Version", "Key", "dptDt"}
    ),
    "/classes/com.korail.mobile.research.custTripInfo.do": frozenset(
        {"Device", "Version", "Key", "custMgNo", "medDvCd", "regSqno"}
    ),
    "/classes/com.korail.mobile.copt.gdReqQry.do": frozenset(
        {"Device", "Version", "qryDtFrom", "qryDtTo"}
    ),
    "/classes/com.korail.mobile.reservation.tripChgDate.do": frozenset(
        {"Device", "Version", "Key", "tripChgDate"}
    ),
    "/classes/com.korail.mobile.research.cmtrInfo.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "cmtrKndCd",
            "psgCnt",
            "cmtrUtlAgeCd",
            "ogtkSaleWctNo",
            "ogtkSaleDd",
            "ogtkSaleSqno",
            "ogtkRetPwd",
            "inquiryType",
        }
    ),
    "/classes/com.korail.mobile.trn.prcFare.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "txtMenuId",
            "chtnDvCd",
            "trnCnt",
            "dptRsStnCd",
            "arvRsStnCd",
            "runDt",
            "trnNo",
            "gdNo",
            "rqSeatAttCd",
            "trnGpCd",
            "stlbTrnClsfCd",
        }
    ),
    "/classes/com.korail.mobile.tk.dlvRcvCust.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "saleWctNo",
            "saleDt",
            "saleSqno",
            "tkRetPwd",
        }
    ),
    "/classes/com.korail.mobile.ticket.ticketDupCheck.do": frozenset(
        {"Device", "Version", "Key", "pnrNo"}
    ),
    "/classes/com.korail.mobile.tk.pbpAcepSpec.do": frozenset(
        {"Device", "Version", "Key", "tkCnt", "tkRetNo"}
    ),
    "/classes/com.korail.mobile.tk.rcntDlvHst.do": frozenset(
        {"Device", "Version", "Key", "custMgNo"}
    ),
    # The READ overload only. CertificationService.java declares two methods on
    # this one path: inquiryTicketRsv (:45-46) with exactly these four @Query
    # fields, and applyDisabilityCertification (:22) which adds
    # txtPsgDisc0019Cnt and six @QueryMaps to apply a disability certificate to
    # a held reservation. Pinning the four-field set here means the write
    # overload's shape is rejected by assert_read_only_request_fields before it
    # can reach the wire, even though it shares the path.
    "/classes/com.korail.mobile.certification.ReservationList": frozenset(
        {"Device", "Version", "Key", "hidPnrNo"}
    ),
    "/classes/com.korail.mobile.refunds.CommissionView": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_comp_nm",
            "h_comp_cert_no",
        }
    ),
    # Same six identity fields plus h_purchase_history. srtgo calls this route
    # as a GET and omits h_purchase_history (ktx.py:791-800); the app declares
    # @POST @FormUrlEncoded with the full eight-field set
    # (RefundService.java:23-25) and every call site sets the flag
    # (TicketListActivity.java:926 "N", TicketPurchaseHistoryActivity.java:267
    # "Y"). The app wins.
    "/classes/com.korail.mobile.refunds.SelTicketInfo": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_purchase_history",
            "txtIndex",
        }
    ),
    # 마일리지/포인트 요약 (XPointService.java:18-20). point_dv_cd is not a
    # caller parameter: KorailPointInquiryDao.java:91 passes the literal "0" and
    # the DAO has no request class at all, so there is nothing else it can be.
    "/classes/com.korail.mobile.xPoint.MyXPointView": frozenset(
        {"Device", "Version", "Key", "point_dv_cd"}
    ),
    # 마일리지 적립/사용 내역 (XPointService.java:26-28).
    "/classes/com.korail.mobile.mlg.amtSpec.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "pontTpVal",
            "qryDvVal",
            "qryStDt",
            "qryClsDt",
            "pgPrCnt",
            "nowPgNo",
        }
    ),
    # 할인카드(N카드) 사용이력 (ResearchService.java:51-52). One identifier and
    # nothing else: the card number the ticket detail hands out as
    # dcnt_crd_info.h_dcnt_crd_no (Y4/C0907b.java:303 puts it in the intent
    # extra that TicketNCardHistoryActivity.java:137 reads straight into
    # setDcntCrdNo).
    "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do": frozenset(
        {"Device", "Version", "Key", "dcntCrdNo"}
    ),
    # 할인카드(N카드) 스케줄 조회 (ResearchService.java:54-55). Fourteen
    # @Query parameters, of which two are Retrofit-omittable -- see
    # KORAIL_OPTIONAL_REQUEST_FIELDS below.
    "/classes/com.korail.mobile.research.dcntCrdScheduleView.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "dptDt",
            "dptRsStnNm",
            "arvRsStnNm",
            "dptTm",
            "trnGpCd",
            "dirtChtnDvCd",
            "dcntCrdKndCd",
            "dcntCrdKndMgNo",
            "useTrmDno",
            "usePsbTno",
            "qryPgNo",
        }
    ),
    # 자율 좌석/열차 변경 옵션 조회 (TicketService.java:54-56, eight @Fields;
    # cross-checked against TicketService.smali:280-325). psrmClCd is
    # omittable -- see KORAIL_OPTIONAL_REQUEST_FIELDS below.
    "/classes/com.korail.mobile.self.seatChgInfo.do": frozenset(
        {
            "Device",
            "Version",
            "Key",
            "runDt",
            "trnNo",
            "dptRsStnCd",
            "arvRsStnCd",
            "psrmClCd",
        }
    ),
    # 원표(원승차권) 조회 (ResearchService.java:61-63). Only the four fixed
    # @Fields can be named here; the rest of the request is a @FieldMap whose
    # keys carry a row index, so the shape is pinned by
    # _is_original_ticket_field_order below rather than by this set. The entry
    # still has to exist: assert_read_only_request_fields returns without
    # validating anything at all when a path is absent from this mapping.
    "/classes/com.korail.mobile.research.tripChgOgtk.do": frozenset(
        {"Device", "Version", "Key", "tkCnt"}
    ),
    # The six below went out with whatever a caller put in until 2026-09-19;
    # each set is what its builder produces. login.Login's is the union of the
    # two shapes in _ALTERNATIVE_REQUEST_FIELD_SHAPES.
    _LOGIN_PATH: frozenset().union(
        *(
            required | optional
            for required, optional in _ALTERNATIVE_REQUEST_FIELD_SHAPES[_LOGIN_PATH]
        )
    ),
    # build_common_code_form. `code` is the one list value any read route may
    # carry -- see _is_common_code_list below.
    _COMMON_CODE_PATH: frozenset(
        {
            "Device", "Version", "Key", "code", "deviceWidth", "deviceHeight",
            "OSVersion", "departDate", "arrivalDate", "holidayYn",
        }
    ),
    # build_train_search_form: Sid and no Key, unlike ScheduleViewSpecial.
    "/classes/com.korail.mobile.seatMovie.ScheduleView": (
        (_SCHEDULE_VIEW_SPECIAL_FIELDS - {"Key"}) | {"Sid"}
    ),
    # KorailClient.get_transfer_stations; post_form adds the common three.
    "/classes/com.korail.mobile.qry.chtnStn.do": frozenset(
        {"Device", "Version", "Key", "dptRsStnCd", "arvRsStnCd"}
    ),
    # build_train_schedule_form: Device and Version, no Key.
    "/classes/com.korail.mobile.research.actualTrainSchedule.do": frozenset(
        {"Device", "Version", "runDt", "trnNo"}
    ),
    # build_maas_station_form: the one code and no common fields.
    "/ebizmaas/EbizMaasStationList.do": frozenset({"addSrvDvCd"}),
}

# Fields the app may legitimately OMIT from an otherwise-exact request. On the
# search-derived seat reads the app forwards trainInfo.getH_seat_att_cd() and
# trainInfo.getTxtGdNo() verbatim (x4/b.java:19,23) and Retrofit drops the
# @Field when it is null (ResearchService getCarList txtSeatAttCd:37/txtGdNo:37
# / getSeatList seatAttCd:59/gdNo:59), so a request without the seat-attribute
# code or goods number is contract-conformant. Every other field stays
# required, and no field outside the exact set is ever accepted.
KORAIL_OPTIONAL_REQUEST_FIELDS: dict[str, frozenset[str]] = {
    # The new main-cache model supplies a protected default for srtCheckYn;
    # its final serialization with encodeDefaults is not visible statically.
    "/file/CACHE/prdMobilePlusMain.cache": frozenset({"srtCheckYn"}),
    "/classes/com.korail.mobile.product.ReservationDetail": frozenset(
        {"txtVrRsvSqNo"}
    ),
    "/classes/com.korail.mobile.product.ReservationList": frozenset(
        {"txtRsvSttCd", "txtStlSttCd"}
    ),
    "/classes/com.korail.mobile.receipt.ReceiptInfo": frozenset({"txtIndex"}),
    "/classes/com.korail.mobile.refunds.SelTicketInfo": frozenset({"txtIndex"}),
    "/classes/com.korail.mobile.research.TrainResearch": frozenset(
        {"txtSeatAttCd", "txtGdNo"}
    ),
    "/classes/com.korail.mobile.research.mergeSeatsC.do": frozenset(
        {"selRsStnNm"}
    ),
    "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial": (
        _SCHEDULE_VIEW_OPTIONAL_FIELDS
        | {"qryStNo", "qryStTrnNo", "qryStTrnNo2", "pgPrCnt"}
    ),
    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do": (
        frozenset({"seatAttCd", "gdNo"})
    ),
    # build_common_code_form drops each of these when it is empty.
    _COMMON_CODE_PATH: frozenset({"departDate", "arrivalDate", "holidayYn"}),
    # build_train_search_form: mbCrdNo only when logged in with a card, and
    # the connection block only on a filtered transfer search. The paging
    # fields are always sent, unlike on ScheduleViewSpecial.
    "/classes/com.korail.mobile.seatMovie.ScheduleView": _SCHEDULE_VIEW_OPTIONAL_FIELDS,
    # The N-card schedule view's two never-set @Query parameters. NEITHER of
    # the app's two builders (u4/b.java:52-65 and :67-81) ever calls
    # setQryPgNo, so qryPgNo is always null and Retrofit drops it; and the
    # 1-section builder (:52-65) additionally never calls setUseTrmDno, so a
    # card bought by trip count rather than by period omits that one too. Both
    # are registered as omittable rather than pinned, because a request that
    # includes them is equally contract-conformant -- the response's
    # fllwPgExt/qryPgNo pair is how the app's other paged reads continue, and
    # this route declares the parameter even though v6.5.0 never fills it.
    "/classes/com.korail.mobile.research.dcntCrdScheduleView.do": frozenset(
        {"useTrmDno", "qryPgNo"}
    ),
    # 자율 좌석/열차 변경 옵션 조회's room class. TCSOptionsActivity.java:135-138
    # calls setPsrmClCd ONLY when the ticket's own h_psrm_cl_cd is 일반실 or
    # 특실 (K4/o.java:7-8 -> "1"/"2", cross-checked K4/o.smali:34-82); for any
    # other value the setter is never reached, the field stays null and
    # Retrofit drops it. A request that carries the code and one that omits it
    # are therefore both shapes the app itself emits.
    "/classes/com.korail.mobile.self.seatChgInfo.do": frozenset(
        {"psrmClCd"}
    ),
}

KORAIL_EXACT_REQUEST_FIELD_ORDERS = {
    "/classes/com.korail.mobile.copt.gdMenuLt.do": (
        ("Device", "Version", "timeStamp"),
    ),
    "/classes/com.korail.mobile.cust.mchdDcntTgt.do": (
        ("Device", "Version", "Key", "dptDt"),
    ),
    "/classes/com.korail.mobile.research.custTripInfo.do": (
        ("Device", "Version", "Key", "custMgNo", "medDvCd", "regSqno"),
    ),
    "/classes/com.korail.mobile.copt.gdReqQry.do": (
        ("Device", "Version"),
        ("Device", "Version", "qryDtFrom", "qryDtTo"),
    ),
    "/classes/com.korail.mobile.reservation.tripChgDate.do": (
        ("Device", "Version", "Key", "tripChgDate"),
    ),
    "/classes/com.korail.mobile.research.cmtrInfo.do": (
        (
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "cmtrKndCd",
            "psgCnt",
        ),
        (
            "Device",
            "Version",
            "Key",
            "jobDvCd",
            "psgCnt",
            "ogtkSaleWctNo",
            "ogtkSaleDd",
            "ogtkSaleSqno",
            "ogtkRetPwd",
            "inquiryType",
        ),
    ),
    "/classes/com.korail.mobile.trn.prcFare.do": (
        (
            "Device",
            "Version",
            "Key",
            "txtMenuId",
            "chtnDvCd",
            "trnCnt",
            "dptRsStnCd",
            "arvRsStnCd",
            "runDt",
            "trnNo",
            "gdNo",
            "rqSeatAttCd",
            "trnGpCd",
            "stlbTrnClsfCd",
        ),
    ),
    "/classes/com.korail.mobile.tk.dlvRcvCust.do": (
        (
            "Device",
            "Version",
            "Key",
            "saleWctNo",
            "saleDt",
            "saleSqno",
            "tkRetPwd",
        ),
    ),
    "/classes/com.korail.mobile.ticket.ticketDupCheck.do": (
        ("Device", "Version", "Key", "pnrNo"),
    ),
    "/classes/com.korail.mobile.tk.pbpAcepSpec.do": (),
    "/classes/com.korail.mobile.research.tripChgOgtk.do": (),
    "/classes/com.korail.mobile.tk.rcntDlvHst.do": (
        ("Device", "Version", "Key", "custMgNo"),
    ),
}


_COMMUTER_INFO_PATH = "/classes/com.korail.mobile.research.cmtrInfo.do"
_MAAS_MENU_PATH = "/classes/com.korail.mobile.copt.gdMenuLt.do"
_PBP_ACCEPTANCE_PATH = "/classes/com.korail.mobile.tk.pbpAcepSpec.do"
_REPEATED_TICKET_REFERENCE_PATHS = frozenset({_PBP_ACCEPTANCE_PATH})
_TRIP_CHANGE_ORIGINAL_TICKET_PATH = (
    "/classes/com.korail.mobile.research.tripChgOgtk.do"
)


def _is_maas_ticket_menu_field_order(names: tuple[str, ...]) -> bool:
    """Allow the APK's ticket menu FieldMap plus repeated tkRetNo fields."""
    if names[:3] != ("Device", "Version", "Key"):
        return False
    tail = names[3:]
    if tail[:1] == ("lang",):
        tail = tail[1:]
    if tail[:1] != ("pnrNo",):
        return False
    tail = tail[1:]
    if tail[-1:] == ("addSrvReqNo",):
        tail = tail[:-1]
    return 1 <= len(tail) <= 8 and all(name == "tkRetNo" for name in tail)
# The @FieldMap key prefixes of the 원표 lookup, in the order the app's own
# loops put them (TCBookingActivity.java:169-175, SeatSearchActivity.java:
# 605-611). Every prefix ends in an underscore in the constant itself --
# ROrtg.java:8-11, cross-checked ROrtg.smali:20-26 -- and the row number is
# appended directly, so the transmitted keys are ogtkSaleWctNo_1,
# ogtkSaleDd_1, ogtkSaleSqno_1, ogtkRetPwd_1, ...
_ORIGINAL_TICKET_FIELD_PREFIXES = (
    "ogtkSaleWctNo_",
    "ogtkSaleDd_",
    "ogtkSaleSqno_",
    "ogtkRetPwd_",
)


def _is_original_ticket_field_order(
    names: tuple[str, ...],
    scalar_pairs: tuple[tuple[str, Any], ...],
) -> bool:
    """원표 요청이 ``research.tripChgOgtk.do`` 의 문법에 맞는지.

    ``ResearchService.java:61-63``: 고정 @Field 넷 + @FieldMap (원표 한 장당 네 키,
    1부터 인덱스). ``tkCnt == N`` 을 요구하지 않음 — 앱 자신의 세 호출 지점이 서로
    다른 값을 보내므로(TCBookingActivity:179, PushHistoryActivity:357,
    SeatSearchActivity:615). 타입만 검사(smali 시그니처 ``I``).
    """
    prefix = ("Device", "Version", "Key", "tkCnt")
    if names[: len(prefix)] != prefix:
        return False
    if type(scalar_pairs[len(prefix) - 1][1]) is not int:
        return False
    remainder = names[len(prefix) :]
    group = len(_ORIGINAL_TICKET_FIELD_PREFIXES)
    if not remainder or len(remainder) % group:
        return False
    count = len(remainder) // group
    expected = tuple(
        f"{name}{index}"
        for index in range(1, count + 1)
        for name in _ORIGINAL_TICKET_FIELD_PREFIXES
    )
    if remainder != expected:
        return False
    return all(
        isinstance(value, str) and bool(value)
        for _, value in scalar_pairs[len(prefix) :]
    )


def _is_commuter_passenger_field_order(
    names: tuple[str, ...],
    scalar_pairs: tuple[tuple[str, str | int], ...],
) -> bool:
    prefix = (
        "Device",
        "Version",
        "Key",
        "jobDvCd",
        "cmtrKndCd",
        "psgCnt",
    )
    if names[: len(prefix)] != prefix:
        return False
    remainder = names[len(prefix) :]
    if not remainder:
        return False
    count = len(remainder)
    if remainder != (("cmtrUtlAgeCd",) * count):
        return False
    values = dict(scalar_pairs[: len(prefix)])
    return values.get("jobDvCd") == "b" and values.get("psgCnt") == str(count)


def _is_ticket_reference_field_order(
    route_path: str,
    names: tuple[str, ...],
    scalar_pairs: tuple[tuple[str, Any], ...],
) -> bool:
    prefix = ("Device", "Version", "Key", "tkCnt")
    if names[: len(prefix)] != prefix:
        return False
    remainder = names[len(prefix) :]
    if not remainder or remainder != (("tkRetNo",) * len(remainder)):
        return False
    count = scalar_pairs[len(prefix) - 1][1]
    if route_path != _PBP_ACCEPTANCE_PATH or type(count) is not int:
        return False
    return count == len(remainder) and all(
        isinstance(value, str) and bool(value)
        for _, value in scalar_pairs[len(prefix) :]
    )


def assert_read_only_request_fields(
    path: str,
    values: Mapping[str, Any] | Sequence[tuple[str, Any]],
) -> None:
    """읽기 요청이 그 라우트에 등록된 필드 이름만 싣도록 강제합니다.

    ``values`` 는 매핑이거나 순서 있는 ``(이름, 값)`` 쌍의 시퀀스입니다. 라우트가
    :data:`KORAIL_EXACT_REQUEST_FIELDS` 에 있으면 이름 집합이 정확히 일치해야 하고,
    :data:`KORAIL_OPTIONAL_REQUEST_FIELDS` 에 등록된 이름만 빠질 수 있습니다.
    :data:`KORAIL_EXACT_REQUEST_FIELD_ORDERS` 에 순서까지 등록된 라우트는 순서도
    검사합니다 — 승객·구간 행처럼 개수가 변하는 목록은 접두사와 반복 블록의 문법으로
    검사합니다.

    어긋나면 :class:`KorailProtocolError` 입니다. 앱이 보내지 않는 필드를 얹거나 보내는
    필드를 빠뜨린 요청은 전송 전에 막힙니다.
    """
    route_path = urlsplit(path).path
    if isinstance(values, Mapping):
        scalar_pairs = tuple(values.items())
    elif isinstance(values, Sequence) and not isinstance(
        values,
        (str, bytes, bytearray),
    ):
        scalar_pairs = tuple(values)
        if not _are_name_value_pairs(scalar_pairs):
            raise KorailProtocolError(
                "KORAIL ordered request fields must be scalar name/value pairs"
            )
        if route_path not in KORAIL_EXACT_REQUEST_FIELD_ORDERS:
            raise KorailProtocolError(
                "KORAIL ordered request fields are not registered for this route"
            )
    else:
        raise KorailProtocolError(
            "KORAIL request fields must be a mapping or ordered pair sequence"
        )
    allowed = KORAIL_EXACT_REQUEST_FIELDS.get(route_path)
    if allowed is None:
        return
    field_names = [name for name, _ in scalar_pairs]
    has_duplicates = len(field_names) != len(set(field_names))
    if has_duplicates and route_path not in {
        _COMMUTER_INFO_PATH,
        _MAAS_MENU_PATH,
        *_REPEATED_TICKET_REFERENCE_PATHS,
    }:
        raise KorailProtocolError(
            "KORAIL request fields must not contain duplicate names"
        )
    ordered_variants = KORAIL_EXACT_REQUEST_FIELD_ORDERS.get(
        route_path
    )
    if ordered_variants is not None:
        names = tuple(field_names)
        valid_shape = names in ordered_variants or (
            route_path == _MAAS_MENU_PATH
            and _is_maas_ticket_menu_field_order(names)
        ) or (
            route_path == _COMMUTER_INFO_PATH
            and _is_commuter_passenger_field_order(names, scalar_pairs)
        ) or (
            route_path in _REPEATED_TICKET_REFERENCE_PATHS
            and _is_ticket_reference_field_order(
                route_path,
                names,
                scalar_pairs,
            )
        ) or (
            route_path == _TRIP_CHANGE_ORIGINAL_TICKET_PATH
            and _is_original_ticket_field_order(names, scalar_pairs)
        )
    elif route_path in _ALTERNATIVE_REQUEST_FIELD_SHAPES:
        field_set = set(field_names)
        valid_shape = any(
            required <= field_set <= required | optional
            for required, optional in _ALTERNATIVE_REQUEST_FIELD_SHAPES[route_path]
        )
    else:
        # Every field must belong to the exact set, and every non-optional
        # field must be present. Optional fields (Retrofit null-omitted @Fields)
        # may be absent, but nothing outside `allowed` is ever accepted.
        optional = KORAIL_OPTIONAL_REQUEST_FIELDS.get(
            route_path, frozenset()
        )
        field_set = set(field_names)
        required = allowed - optional
        valid_shape = required <= field_set <= allowed
    if not valid_shape:
        raise KorailProtocolError(
            "KORAIL request fields must exactly match the registered "
            "read-only contract"
        )
    if route_path in _SCHEDULE_VIEW_PATHS:
        route_name = route_path.rsplit(".", 1)[-1]
        selected = [
            int(match.group(1))
            for name in field_names
            if (match := re.fullmatch(r"chtnRsStnCd(\d+)", name))
        ]
        values_by_name = dict(scalar_pairs)
        if selected:
            if selected != list(range(1, len(selected) + 1)) or (
                values_by_name.get("chtnCnt") != str(len(selected))
            ):
                raise KorailProtocolError(
                    f"KORAIL {route_name} connection stations must be numbered"
                )
        elif "chtnCnt" in values_by_name:
            raise KorailProtocolError(
                f"KORAIL {route_name} connection count requires stations"
            )
        if ("trnGpCd1" in values_by_name) != (
            values_by_name.get("trnGpCnt") == "1"
        ):
            raise KorailProtocolError(
                f"KORAIL {route_name} train-group count is inconsistent"
            )
    if any(
        type(value) not in {str, int}
        and not (
            route_path == _COMMON_CODE_PATH
            and name == "code"
            and _is_common_code_list(value)
        )
        for name, value in scalar_pairs
    ):
        raise KorailProtocolError(
            "KORAIL request values must be scalar strings or integers"
        )


def _is_common_code_list(value: object) -> bool:
    """common.code.do's ``code``: a non-empty list of strings.

    build_common_code_form always sends a list, and httpx writes it as one
    repeated ``code`` key per item. No other field on any read route takes a
    list.
    """
    return (
        type(value) is list
        and bool(value)
        and all(type(item) is str for item in value)
    )
