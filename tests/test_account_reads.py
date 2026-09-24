"""KORAIL 7.0.6 account-read contract tests; synthetic/offline only.

Apply changes.patch to 291e01c, then PYTHONPATH=src pytest -q tests/test_account_reads.py.
Wire fixtures are literal independent examples, not output from the builders under test.
A property-name fixture does not prove a protected serializer descriptor or live success.
CommonIn.java:35,70,220,350; NetworkService.java:15320-15427.
"""

from __future__ import annotations

import socket
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, is_dataclass, replace
from dataclasses import fields as dataclass_fields
from typing import Any
from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import read_models as m
from korail_mobile_api import read_payloads as p
from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.errors import KorailProtocolError, KorailSessionExpiredError
from korail_mobile_api.models import KorailSession

PREFIX = "/classes/com.korail.mobile."
COMMON = [("Device", "TEST-DEVICE"), ("Version", "TEST-VERSION"), ("Key", "TEST-KEY")]
DATE = "20300102"
STAMP = 1_800_000_000_125
REFERENCE = p.OriginalTicketReference("TEST-WINDOW", "0102", "TEST-SEQUENCE", "TEST-RETURN")
FULL_REFERENCE = replace(REFERENCE, sale_date=DATE)
SECOND_REFERENCE = replace(FULL_REFERENCE, sale_sequence="TEST-SEQUENCE-2")
PASS_DATA = m.PassMenuData(commuter_kind_code="TEST-KIND")


def success(**fields: Any) -> dict[str, Any]:
    return {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "SYNTHETIC", **fields}


RECEIPT_STRINGS = (
    "h_abrd_dt",
    "h_dpt_rs_stn_nm",
    "h_dpt_tm",
    "h_arv_rs_stn_nm",
    "h_arv_tm",
    "h_cmtr_knd_cd",
    "h_jrny_tp_cd",
    "h_prt_disc_knd_nm",
    "h_prt_disc_knd_cd",
    "h_prt_type",
    "h_psrm_cl_nm",
    "h_tk_knd_cd",
    "h_tk_knd_nm",
    "h_tk_stt_cd",
    "h_trn_clsf_cd",
    "h_trn_clsf_nm",
    "h_trn_gp_cd",
    "h_trn_no",
    "h_stl_mb_crd_no",
)
RECEIPT_INTS = (
    "h_psg_type1_cnt",
    "h_psg_type2_cnt",
    "h_psg_type3_cnt",
    "h_rcvd_amt",
    "h_crd_ret_amt",
    "h_ret_fee",
    "h_ret_rcvd_amt",
    "h_xpoint_ret_amt",
)
PAYMENT_STRINGS = ("h_stl_way_nm", "h_apv_dt", "h_acnt_no", "h_apv_no", "h_stl_crd_no", "h_xpot_no")
PAYMENT_INTS = ("h_ismt_mnth_num", "h_stl_amt")
CASH_STRINGS = ("h_apv_mtd_nm", "h_athn_dmn_rcgn_no", "h_cash_rcet_apv_no", "h_cash_rcet_txn_dv_cd")
PAYMENT = {**dict.fromkeys(PAYMENT_STRINGS, "TEST"), "h_ismt_mnth_num": 0, "h_stl_amt": 1200}
CASH = {**dict.fromkeys(CASH_STRINGS, "TEST"), "h_tot_apv_amt": 1200}
RECEIPT = {
    **dict.fromkeys(RECEIPT_STRINGS, "TEST"),
    **dict.fromkeys(RECEIPT_INTS, 0),
    "h_rcvd_amt": 1200,
    "stl_info": [PAYMENT],
    "cash_rcet_info": [CASH],
}
RECEIPT_BODY = success(receipt_infos={"receipt_info": [RECEIPT]})
RECIPIENT_KEYS = ("acepCustMgNo", "acepCustNm", "acepCustTeln", "mbCrdNo")
RECENT_KEYS = ("acepCustMgFlg", "acepCustMgNo", "acepCustNm", "acepCustTeln", "acepCustTeln2", "mbCrdNo")
PBP_TICKET_KEYS = ("pnrNo", "saleDt", "saleSqno", "saleWctNo", "tkRetPwd")
PBP_JOURNEY_KEYS = (
    "acepCustNm",
    "acepCustTeln",
    "jrnyTpCd",
    "mbDvNm",
    "pbpAcepKndNm",
    "pbpRsvNo",
    "regDt",
    "wdrwPsbFlg",
    "mbCrdNo",
)
PBP_SEAT_KEYS = ("psgTpDvNm", "psrmClCd", "psrmClNm", "seatNo")
PBP_SEAT = {**dict.fromkeys(PBP_SEAT_KEYS, "TEST"), "scarNo": 2}
PBP_JOURNEY = {**dict.fromkeys(PBP_JOURNEY_KEYS, "TEST"), "seatList": [PBP_SEAT]}
PBP_TICKET = {**dict.fromkeys(PBP_TICKET_KEYS, "TEST"), "jrnyList": [PBP_JOURNEY]}
PBP_BODY = success(tkList=[PBP_TICKET])
RECENT_BODY = success(acepList=[dict.fromkeys(RECENT_KEYS, "TEST")], chgePbpRsvNo="TEST-CHANGED")


@dataclass(frozen=True)
class Case:
    method: str
    route: str
    kwargs: dict[str, Any]
    fields: tuple[tuple[str, str], ...]
    response: dict[str, Any]
    checks: tuple[tuple[str, Any], ...]
    source: str
    verb: str = "POST"
    query: bool = False
    common_lang: bool = True


def case(
    method: str,
    route: str,
    kwargs: dict[str, Any],
    fields: dict[str, str] | tuple[tuple[str, str], ...],
    response: dict[str, Any],
    checks: tuple[tuple[str, Any], ...],
    source: str,
    **options: Any,
) -> Case:
    return Case(
        method,
        route,
        kwargs,
        tuple(fields.items()) if isinstance(fields, dict) else fields,
        response,
        checks,
        source,
        **options,
    )


CASES = [
    case(
        "get_cart_list",
        "cart.showCartList",
        {"pnr_no": "TEST-PNR", "additional_service_request_no": "TEST-SERVICE"},
        {"pnrNo": "TEST-PNR", "addSrvReqNo": "TEST-SERVICE"},
        success(cart_infos={"cart_info": [{"h_pnr_no": "TEST-PNR", "h_rcvd_amt": "001200"}]}),
        (("items.0.pnr_no", "TEST-PNR"), ("items.0.received_amount", "001200")),
        "NetworkApi.java:691-692; CartListIn.java:51",
    ),
    case(
        "get_deposit_banks",
        "dlay.dptnBank.do",
        {},
        {},
        success(dptnBank=[{"dptnBankCd": "TEST-CODE", "dptnBankNm": "TEST-BANK"}]),
        (("items.0.code", "TEST-CODE"), ("items.0.display_name", "TEST-BANK")),
        "NetworkApi.java:392-393; DptnBank.java:46-58",
        common_lang=False,
    ),
    case(
        "get_delay_discount_tickets",
        "passCard.DelayDiscountView",
        {"departure_date_to": DATE},
        {"h_page_no": DATE},
        success(disc_infos={"disc_info": [{"h_dlay_fare": "001200"}]}),
        (("items.0.fare", "001200"),),
        "NetworkApi.java:352-353; DelayDiscountViewIn.java:50,77",
        query=True,
    ),
    case(
        "get_discount_coupons",
        "passCard.CouponView",
        {"page_no": 2, "pnr_no": "TEST-PNR"},
        {"txtSelPage": "2", "pnrNo": "TEST-PNR"},
        success(coupon_infos={"coupon_info": [{"h_cpn_no": "TEST-COUPON", "h_fdcert_mg_cls_dt": DATE}]}),
        (("items.0.coupon_no", "TEST-COUPON"), ("items.0.expiration_date", DATE)),
        "NetworkApi.java:328-329; CouponIn.java:52",
    ),
    case(
        "get_korail_point_summary",
        "xPoint.MyXPointView",
        {},
        {"point_dv_cd": "0"},
        success(h_korail_point="001200"),
        (("korail_point", "001200"),),
        "NetworkApi.java:515-516; MyXPointViewIn.java:49",
    ),
    case(
        "get_mileage_history",
        "mlg.amtSpec.do",
        {"request": p.MileageHistoryRequest(DATE, "20300203", page_no=2)},
        {
            "pontTpVal": "1",
            "qryDvVal": "0",
            "qryStDt": DATE,
            "qryClsDt": "20300203",
            "pgPrCnt": "20",
            "nowPgNo": "2",
        },
        success(specList=[{"dptDt": DATE, "pontAmt": "001200"}], pgCnt="0002"),
        (("entries.0.departure_date", DATE), ("entries.0.point_amount", "001200")),
        "NetworkApi.java:274-275; AmtSpecIn.java:57",
    ),
    case(
        "get_discount_card_usage_history",
        "ticket.dcntCrdUseQry.do",
        {"card_no": "TEST-NCARD"},
        {"dcntCrdNo": "TEST-NCARD"},
        success(tkUseList=[{"custNm": "TEST-PERSON", "runDt1": DATE}]),
        (("items.0.passenger_name", "TEST-PERSON"), ("items.0.run_date", DATE)),
        "NetworkApi.java:218-219; NCardHistoryIn.java:50; 검증 못 함",
    ),
    case(
        "get_discount_card_schedule",
        "research.dcntCrdScheduleView.do",
        {
            "request": p.DiscountCardScheduleRequest(
                "TEST-MANAGEMENT",
                "TEST-FROM",
                "TEST-TO",
                DATE,
                usable_trip_count="2",
                usage_period_days="30",
                page_no="3",
            )
        },
        {
            "dptDt": DATE,
            "dptRsStnNm": "TEST-FROM",
            "arvRsStnNm": "TEST-TO",
            "dptTm": "000000",
            "trnGpCd": "109",
            "dirtChtnDvCd": "1",
            "dcntCrdKndCd": "MMM",
            "dcntCrdKndMgNo": "TEST-MANAGEMENT",
            "usePsbTno": "2",
            "useTrmDno": "30",
            "qryPgNo": "3",
        },
        success(trnScdlList=[{"trnNo": "00999", "runDt": DATE}]),
        (("trains.0.train_no", "00999"), ("trains.0.run_date", DATE)),
        "NetworkApi.java:340-341; NCardScheduleIn.java:61; 검증 못 함",
    ),
    case(
        "get_pass_available_dates",
        "pass.passInfoList",
        {"kind_code": "TEST-KIND", "period_code": "TEST-PERIOD", "age_code": "TEST-AGE"},
        {"txtCmtrKndCd": "TEST-KIND", "txtCmtrUtlTrmCd": "TEST-PERIOD", "txtCmtrUtlAgeCd": "TEST-AGE"},
        success(
            pass_info=[{"h_use_open_dt": DATE, "h_pnr_no": "TEST-PNR", "h_item_sqno": "0001"}],
            ticket_info=[{"h_ise_dt2": DATE}],
            wct_info=[{"eng_cd_val": "TEST-CODE", "kor_cd_val": "TEST-OFFICE"}],
        ),
        (("open_dates", (DATE,)), ("pass_info.0.pnr_no", "TEST-PNR"), ("offices.0.code", "TEST-CODE")),
        "NetworkApi.java:543-544; PassInfoListIn.java:57",
    ),
    case(
        "get_pass_schedule",
        "pass.passScheduleInfoList",
        {
            "request": p.PassScheduleRequest(
                "TEST-TRAIN",
                DATE,
                "120000",
                "TEST-TRANSFER",
                "TEST-KIND",
                "TEST-PERIOD",
                "TEST-AGE",
                "2",
                "3",
                "TEST-FROM",
                "TEST-TO",
                "TEST-WEEKEND",
            )
        },
        {
            "selGoTrain": "TEST-TRAIN",
            "selGoAbrdDt": DATE,
            "txtGoHour": "120000",
            "radChgTrnDvCd": "TEST-TRANSFER",
            "txtCmtrKndCd": "TEST-KIND",
            "txtCmtrUtlTrmCd": "TEST-PERIOD",
            "txtCmtrUtlAgeCd": "TEST-AGE",
            "txtSelPage": "2",
            "txtCntPerPage": "3",
            "txtGoStart": "TEST-FROM",
            "txtGoEnd": "TEST-TO",
            "txtWkndUseFlg": "TEST-WEEKEND",
        },
        success(schedule_info=[{"train_list": [{"h_trn_no": "00999"}]}]),
        (("schedules.0.trains.0.train_no", "00999"),),
        "NetworkApi.java:563-564; PassScheduleInfoListIn.java:63",
    ),
    case(
        "get_trip_menu",
        "pass.trGdMenuLt.do",
        {},
        {"timeStamp": str(STAMP)},
        success(
            menuList=[
                {
                    "menuTitle": "TEST-MENU",
                    "contCount": "1",
                    "contList": [
                        {"contTitle": "TEST-CONTENT", "passData": {"h_seiect_station": "TEST-STATION"}}
                    ],
                }
            ]
        ),
        (
            ("items.0.title", "TEST-MENU"),
            ("items.0.contents.0.title", "TEST-CONTENT"),
            ("items.0.contents.0.pass_data.station_selection", "TEST-STATION"),
        ),
        "NetworkApi.java:768-769; TrGdMenuLtIn.java:50",
    ),
    case(
        "get_pass_menu",
        "pass.passMenu.do",
        {"menu_no": "TEST-MENU"},
        {"menuNo": "TEST-MENU"},
        success(
            list=[
                {
                    "title": "TEST-PASS",
                    "passData": {"h_cmtr_knd_cd": "TEST-KIND", "h_select_station": "TEST-STATION"},
                    "webData": {"url": "https://offline.invalid/test"},
                }
            ]
        ),
        (
            ("items.0.title", "TEST-PASS"),
            ("items.0.pass_data.commuter_kind_code", "TEST-KIND"),
            ("items.0.pass_data.station_selection", "TEST-STATION"),
        ),
        "NetworkApi.java:547-548; PassMenuIn.java:52",
    ),
    case(
        "get_crew_request_list",
        "push.crwCallRq.do",
        {},
        {"timeStamp": str(STAMP)},
        success(prsList=[{"intgMsgCd": "TEST-CODE", "prsCont": "TEST-REASON"}]),
        (("items.0.message_code", "TEST-CODE"), ("items.0.content", "TEST-REASON")),
        "NetworkService.java:3952-3955; CommonIn.java:350; CrewCallCommonIn.java:50",
    ),
    case(
        "get_commuter_kind_menu",
        "push.cmtrKnd.do",
        {"commuter_kind_code": "TEST-KIND"},
        {"cmtrKndCd": "TEST-KIND"},
        success(title="TEST-TITLE", passData={"h_cmtr_knd_cd": "TEST-KIND"}),
        (("title", "TEST-TITLE"), ("pass_data.commuter_kind_code", "TEST-KIND")),
        "PushService.java:16-17",
        verb="GET",
        query=True,
        common_lang=False,
    ),
    case(
        "get_commuter_info",
        "research.cmtrInfo.do",
        {"request": p.CommuterInitialRequest(PASS_DATA)},
        {"jobDvCd": "a", "cmtrKndCd": "TEST-KIND", "psgCnt": "0"},
        success(
            psgList=[
                {
                    "cmtrUtlAgeCd": "TEST-AGE",
                    "comnCdNm": "TEST-AGE-NAME",
                    "custAgeFrom": "0000",
                    "custAgeTo": "0099",
                    "psgPrnbFrom": "0000",
                    "psgPrnbTo": "0002",
                }
            ],
            avlPrnbTo="0002",
        ),
        (
            ("passenger_options.0.commuter_usage_age_code", "TEST-AGE"),
            ("passenger_options.0.customer_age_to", 99),
            ("available_passenger_count_to", 2),
        ),
        "NetworkApi.java:199-200; CommutationInfoIn.java:64",
    ),
    case(
        "get_product_reservations",
        "product.ReservationList",
        {
            "page_no": 2,
            "page_size": 3,
            "reservation_status_code": "TEST-RSV",
            "payment_status_code": "TEST-PAY",
        },
        {"txtSelPage": "2", "txtCntPerPage": "3", "txtRsvSttCd": "TEST-RSV", "txtStlSttCd": "TEST-PAY"},
        success(mainInfo={"strTotCnt": "0001", "entity": [{"strVrRsvNo": "TEST-RSV", "strVrRsvSqno": "0002"}]}),
        (
            ("items.0.virtual_reservation_no", "TEST-RSV"),
            ("items.0.reservation_sequence", "0002"),
            ("total_count", 1),
        ),
        "NetworkApi.java:224-225; ProductListIn.java:56",
        verb="GET",
        query=True,
    ),
    case(
        "get_product_detail",
        "product.ReservationDetail",
        {"reservation_no": "TEST-RSV", "reservation_sequence": "0002"},
        {"txtVrRsNo": "TEST-RSV", "txtVrRsvSqNo": "0002"},
        success(
            mainInfo={
                "strGdNm": "TEST-PRODUCT",
                "strCncRetAmt": "001200",
                "entityOne": [{"strGdConsItmNm": "TEST-ITEM"}],
            }
        ),
        (
            ("product_name", "TEST-PRODUCT"),
            ("cancellation_amount", "001200"),
            ("included_item_names", ("TEST-ITEM",)),
        ),
        "NetworkApi.java:221-222; ProductDetailIn.java:53",
        verb="GET",
        query=True,
    ),
    case(
        "get_ticket_receipt",
        "receipt.ReceiptInfo",
        {
            "sale_date": "0102",
            "window_no": "TEST-WINDOW",
            "sale_sequence": "TEST-SEQUENCE",
            "return_password": "TEST-RETURN",
            "txt_index": "TEST-INDEX",
        },
        {
            "h_orgtk_sale_dt": "0102",
            "h_orgtk_wct_no": "TEST-WINDOW",
            "h_orgtk_sale_sqno": "TEST-SEQUENCE",
            "h_orgtk_tk_ret_pwd": "TEST-RETURN",
            "txtIndex": "TEST-INDEX",
        },
        RECEIPT_BODY,
        (
            ("items.0.received_amount", 1200),
            ("items.0.payments.0.amount", 1200),
            ("items.0.cash_receipts.0.total_approved_amount", 1200),
        ),
        "NetworkApi.java:748-749; ReceiptInfo.java:87; StlInfo.java:55; CashReceiptInfo.java:52",
    ),
    case(
        "get_reservation_history",
        "reservation.ReservationView",
        {},
        {"timeStamp": "0"},
        success(
            jrny_infos={
                "jrny_info": [{"train_infos": {"train_info": [{"h_pnr_no": "TEST-PNR", "h_trn_no": "00999"}]}}]
            }
        ),
        (("journeys.0.trains.0.pnr_no", "TEST-PNR"), ("items.0.train_no", "00999")),
        "NetworkApi.java:635-636; ReservationViewIn.java:50-65",
    ),
    case(
        "get_seat_assignment_schedule",
        "research.assignScheduleView.do",
        {
            "request": p.SeatAssignmentScheduleRequest(
                "TEST-MENU",
                DATE,
                "120000",
                "TEST-FROM",
                "TEST-TO",
                "TEST-GROUP",
                "TEST-ROOM",
                "TEST-SEAT",
                2,
                "TEST-DETOUR",
                "TEST-TRANSFER",
                "TEST-CONNECTION",
            )
        },
        {
            "menuId": "TEST-MENU",
            "dptDt": DATE,
            "dptTm": "120000",
            "dptRsStnNm": "TEST-FROM",
            "arvRsStnNm": "TEST-TO",
            "trnGpCd": "TEST-GROUP",
            "psrmClCd": "TEST-ROOM",
            "dirtChtnDvCd": "TEST-TRANSFER",
            "chtnArvRsStnNm": "TEST-CONNECTION",
            "seatAttCd1": "TEST-SEAT",
            "psgNum1": "1",
            "stlbDturDvNm1": "TEST-DETOUR",
            "seatAttCd2": "TEST-SEAT",
            "psgNum2": "1",
            "stlbDturDvNm2": "TEST-DETOUR",
        },
        success(trn_infos={"trn_info": [{"h_trn_no": "00999"}]}, h_next_pg_flg="Y"),
        (("trains.0.train_no", "00999"), ("next_page_flag", "Y")),
        "NetworkApi.java:278-279; AssignScheduleIn.java:63; dated 2026-09-22 slot observation",
    ),
    case(
        "get_multi_child_discount_targets",
        "cust.mchdDcntTgt.do",
        {"departure_date": DATE},
        {"dptDt": DATE},
        success(fmlyList=[{"custFmlyNm": "TEST-PERSON", "fmlySqno": "0002"}]),
        (("targets.0.customer_family_name", "TEST-PERSON"), ("targets.0.family_sequence", "0002")),
        "NetworkApi.java:491-492; MchdDcntTgtIn.java:51",
    ),
    case(
        "get_customer_trip_info",
        "research.custTripInfo.do",
        {},
        {"custMgNo": "TEST-CUSTOMER", "medDvCd": "03", "regSqno": "0"},
        success(mainList=[{"dptStnNm": "TEST-FROM", "adulCnt": "0002"}]),
        (("trips.0.departure_station_name", "TEST-FROM"), ("trips.0.adult_count", "0002")),
        "NetworkApi.java:332-333; CustTripInfoOut.java:51-63",
    ),
    case(
        "get_trip_change_dates",
        "reservation.tripChgDate.do",
        {"departure_date": DATE},
        {"tripChgDate": DATE},
        success(tripChgDates=[DATE, "20300103"], lastRunDt="20300103"),
        (("trip_change_dates", (DATE, "20300103")), ("last_run_date", "20300103")),
        "NetworkApi.java:238-239; TipChgDateInquiryOut.java:53-64",
        verb="GET",
        query=True,
    ),
    case(
        "get_delivery_recipient",
        "tk.dlvRcvCust.do",
        {"ticket": FULL_REFERENCE},
        {"saleWctNo": "TEST-WINDOW", "saleDt": DATE, "saleSqno": "TEST-SEQUENCE", "tkRetPwd": "TEST-RETURN"},
        success(**dict.fromkeys(RECIPIENT_KEYS, "TEST")),
        (("acceptance_customer_management_no", "TEST"), ("member_card_no", "TEST")),
        "NetworkApi.java:372-373; DeliveryRcvCustOut.java:51; 검증 못 함",
    ),
    case(
        "check_ticket_duplication",
        "ticket.ticketDupCheck.do",
        {"request": p.TicketDuplicationCheckRequest("TEST-PNR")},
        {"pnrNo": "TEST-PNR"},
        success(rsvCnt="0002"),
        (("reservation_count", "0002"),),
        "NetworkApi.java:744-745; TicketDupCheckIn.java:51",
    ),
    case(
        "get_pbp_acceptance_specifications",
        "tk.pbpAcepSpec.do",
        {"tickets": (FULL_REFERENCE, SECOND_REFERENCE)},
        (
            ("tkCnt", "2"),
            ("tkRetNo", f"TEST-WINDOW-{DATE}-TEST-SEQUENCE-TEST-RETURN"),
            ("tkRetNo", f"TEST-WINDOW-{DATE}-TEST-SEQUENCE-2-TEST-RETURN"),
        ),
        PBP_BODY,
        (("tickets.0.journeys.0.seats.0.car_no", 2), ("tickets.0.pnr_no", "TEST")),
        "NetworkApi.java:368-369; DeliveredTicketOut.java:50; Tk.java:54; Jrny.java:60; Seat.java:53",
    ),
    case(
        "get_original_ticket_inquiry",
        "research.tripChgOgtk.do",
        {"tickets": (REFERENCE, replace(REFERENCE, sale_sequence="TEST-SEQUENCE-2"))},
        (
            ("tkCnt", "2"),
            ("ogtkSaleWctNo_1", "TEST-WINDOW"),
            ("ogtkSaleDd_1", "0102"),
            ("ogtkSaleSqno_1", "TEST-SEQUENCE"),
            ("ogtkRetPwd_1", "TEST-RETURN"),
            ("ogtkSaleWctNo_2", "TEST-WINDOW"),
            ("ogtkSaleDd_2", "0102"),
            ("ogtkSaleSqno_2", "TEST-SEQUENCE-2"),
            ("ogtkRetPwd_2", "TEST-RETURN"),
        ),
        success(
            orgTkList=[
                {
                    "pnrNo": "TEST-PNR",
                    "jrnyList": [{"trnNo": "00999", "seatList": [{"seatNo": "TEST-SEAT", "scarNo": "0002"}]}],
                }
            ]
        ),
        (("tickets.0.pnr_no", "TEST-PNR"), ("tickets.0.journeys.0.seats.0.car_no", "0002")),
        "NetworkApi.java:235-236; OgTicketInquiryIn.java:53; ChangeOrtkInfo.java:52",
    ),
    case(
        "get_self_seat_change_info",
        "self.seatChgInfo.do",
        {"request": p.SelfSeatChangeInfoRequest(DATE, "00999", "TEST-FROM", "TEST-TO", "1")},
        {"runDt": DATE, "trnNo": "00999", "dptRsStnCd": "TEST-FROM", "arvRsStnCd": "TEST-TO", "psrmClCd": "1"},
        success(
            trnNo="00999", chgStnList=[{"dptRsStnNm": "TEST-STATION"}], chgRsnList=[{"qryCode": "TEST-REASON"}]
        ),
        (
            ("train_no", "00999"),
            ("stations.0.departure_station_name", "TEST-STATION"),
            ("reasons.0.query_code", "TEST-REASON"),
        ),
        "NetworkApi.java:807-808; SeatAvailabilityIn.java:55",
    ),
    case(
        "get_recent_delivery_history",
        "tk.rcntDlvHst.do",
        {},
        {"custMgNo": "TEST-CUSTOMER"},
        RECENT_BODY,
        (
            ("recipients.0.acceptance_customer_name", "TEST"),
            ("changed_acceptance_reservation_no", "TEST-CHANGED"),
        ),
        "NetworkApi.java:595-596; RecentDeliveryHistoryOut.java:51-63; DeliveryHistoryData.java:52",
    ),
    case(
        "get_ticket_reservation_detail",
        "certification.ReservationList",
        {"request": p.TicketReservationDetailRequest("TEST-PNR")},
        {"hidPnrNo": "TEST-PNR"},
        success(
            h_pnr_no="TEST-PNR",
            jrny_infos={
                "jrny_info": [
                    {
                        "h_arv_dt": DATE,
                        "seat_infos": {"seat_info": [{"h_seat_no": "TEST-SEAT", "h_tot_disc_amt": "001200"}]},
                    }
                ]
            },
        ),
        (
            ("pnr_no", "TEST-PNR"),
            ("journeys.0.arrival_date", DATE),
            ("journeys.0.seats.0.total_discount_amount", "001200"),
        ),
        "NetworkApi.java:423-424; TicketRsvInquiryIn.java:51",
    ),
    case(
        "get_refund_commission",
        "refunds.CommissionView",
        {"ticket": REFERENCE, "companion": p.RefundCompanion("TEST-COMPANION", "TEST-CERTIFICATE")},
        {
            "h_orgtk_ret_sale_dt": "0102",
            "h_orgtk_wct_no": "TEST-WINDOW",
            "h_orgtk_sale_sqno": "TEST-SEQUENCE",
            "h_orgtk_ret_pwd": "TEST-RETURN",
            "h_comp_nm": "TEST-COMPANION",
            "h_comp_cert_no": "TEST-CERTIFICATE",
        },
        success(ret_amt="001200", ret_fee="0000", prg_psb_flg="Y"),
        (("refund_amount", "001200"), ("refund_fee", "0000"), ("proceed_possible_flag", "Y")),
        "NetworkApi.java:599-600; RefundCommissionIn.java:59",
    ),
    case(
        "get_refund_ticket_detail",
        "refunds.SelTicketInfo",
        {"ticket": REFERENCE, "from_purchase_history": True, "txt_index": "TEST-INDEX"},
        {
            "h_orgtk_ret_sale_dt": "0102",
            "h_orgtk_wct_no": "TEST-WINDOW",
            "h_orgtk_sale_sqno": "TEST-SEQUENCE",
            "h_orgtk_ret_pwd": "TEST-RETURN",
            "h_purchase_history": "Y",
            "txtIndex": "TEST-INDEX",
        },
        success(
            h_pnr_no="TEST-PNR",
            ticket_infos={"ticket_info": [{"h_trn_no": "00999", "tk_seat_info": [{"h_seat_no": "TEST-SEAT"}]}]},
            h_qrcode="TEST-QR",
        ),
        (
            ("pnr_no", "TEST-PNR"),
            ("journeys.0.train_no", "00999"),
            ("journeys.0.seats.0.seat_no", "TEST-SEAT"),
            ("qr_code", "TEST-QR"),
        ),
        "NetworkApi.java:407-408; TicketDetailIn.java:57",
    ),
    case(
        "get_ticket_list",
        "myTicket.MyTicketNewList.do",
        {"page_no": 3, "mode": "2", "boarding_date_from": DATE, "boarding_date_to": "20300203"},
        {
            "txtDeviceId": "TEST-ADVERTISING",
            "txtIndex": "2",
            "h_page_no": "3",
            "h_abrd_dt_from": DATE,
            "h_abrd_dt_to": "20300203",
            "hiduserYn": "Y",
        },
        success(
            pnr_list=[
                {
                    "ticket_list": [
                        {
                            "h_pnr_no": "TEST-PNR",
                            "h_orgtk_ret_sale_dt": "0102",
                            "jrn_info": [{"h_trn_no": "00999", "h_seat_no": "TEST-SEAT"}],
                        }
                    ]
                }
            ]
        ),
        (
            ("reservations.0.tickets.0.pnr_no", "TEST-PNR"),
            ("reservations.0.tickets.0.return_sale_date", "0102"),
            ("reservations.0.tickets.0.trains.0.train_no", "00999"),
        ),
        "NetworkApi.java:511-512; MyTicketListIn.java:62",
    ),
]
BY_NAME = {c.method: c for c in CASES}


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """SESSION_CONTEXT.md §3: sockets/DNS denied even when transport configuration regresses."""

    def denied(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("OFFLINE ONLY: socket access is forbidden")

    for attr in ("connect", "connect_ex", "sendto", "sendmsg"):
        if hasattr(socket.socket, attr):
            monkeypatch.setattr(socket.socket, attr, denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(socket, "getaddrinfo", denied)
    monkeypatch.setattr(p.time, "time", lambda: STAMP / 1000)


@pytest.fixture
def make_client():
    """NetworkService.java:15320-15427: observe the encoded request, not just the builder."""
    clients = []

    def make(response: dict[str, Any], *, lang: str | None = "TEST-LANG", **config_changes: Any):
        calls: list[httpx.Request] = []

        def handle(request: httpx.Request) -> httpx.Response:
            assert request.url.host == "offline.invalid"
            calls.append(request)
            return httpx.Response(200, json=response)

        config = KorailConfig(
            base_url="https://offline.invalid",
            device="TEST-DEVICE",
            version="TEST-VERSION",
            key="TEST-KEY",
            advertising_id="TEST-ADVERTISING",
            lang=lang,
            netfunnel_enabled=False,
            disable_dynapath=True,
            **config_changes,
        )
        client = KorailClient(config, transport=httpx.MockTransport(handle))
        client.session.current = KorailSession(
            jsessionid="TEST-SESSION", customer_no="TEST-CUSTOMER", member_card_no="TEST-MEMBER"
        )
        clients.append(client)
        return client, calls

    yield make
    for client in clients:
        client.close()


def typed_strings(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if is_dataclass(obj) and not isinstance(obj, type):
        return [
            v
            for f in dataclass_fields(obj)
            if f.name not in {"raw", "detail_raw"}
            for v in typed_strings(getattr(obj, f.name))
        ]
    if isinstance(obj, (tuple, list)):
        return [v for item in obj for v in typed_strings(item)]
    return []


def attr_path(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = obj[int(part)] if part.isdecimal() else getattr(obj, part)
    return obj


def wire_pairs(request: httpx.Request, query: bool = False) -> list[tuple[str, str]]:
    data = request.url.query if query else request.content
    return parse_qsl(data.decode("utf-8"), keep_blank_values=True)


@pytest.mark.parametrize("entry", CASES, ids=lambda c: c.method)
@pytest.mark.parametrize("lang", [None, "TEST-LANG", ""])
def test_account_read_contract(entry: Case, lang: str | None, make_client) -> None:
    """NetworkApi.java:199-808; per-route Java/DTO locations are in each Case.source.

    PushService.java:16-17 and NetworkService.java:15320-15427 distinguish direct
    parameters, QueryMap, and FieldMap. The fixtures lock protected assumptions,
    but do not promote them to recovered constants or live confirmation.
    """
    payload = deepcopy(entry.response)
    payload["synthetic_unknown"] = {"nested": ["PRESERVE", 7]}
    client, calls = make_client(payload, lang=lang)
    result = getattr(client, entry.method)(**entry.kwargs)
    assert len(calls) == 1, entry.source
    request = calls[0]
    assert (request.method, request.url.path) == (entry.verb, PREFIX + entry.route)
    common = COMMON + ([("lang", lang)] if lang and entry.common_lang else [])
    assert Counter(wire_pairs(request, entry.query)) == Counter(common + list(entry.fields)), entry.source
    if entry.query:
        assert request.content == b""
    else:
        assert request.url.query == b""
    if entry.verb == "POST":
        assert request.headers["content-type"].startswith("application/x-www-form-urlencoded")
    assert result.raw == payload
    for path, expected in entry.checks:
        assert attr_path(result, path) == expected, (entry.method, path, entry.source)
    if entry.method == "get_pbp_acceptance_specifications":
        assert [v for k, v in wire_pairs(request) if k == "tkRetNo"] == [
            v for k, v in entry.fields if k == "tkRetNo"
        ]


# (method, path to object containing required fields, required keys).
# These literal masks follow the generated constructors, not Python implementation.
REQUIRED_GROUPS = [
    ("get_deposit_banks", ("dptnBank", 0), ("dptnBankCd", "dptnBankNm")),  # DptnBank.java:46 mask 3
    ("get_customer_trip_info", (), ("mainList",)),  # CustTripInfoOut.java:51 mask 8
    ("get_trip_change_dates", (), ("tripChgDates",)),  # TipChgDateInquiryOut.java:53 mask 16
    ("get_recent_delivery_history", ("acepList", 0), RECENT_KEYS),  # DeliveryHistoryData.java:52 mask 63
    ("get_delivery_recipient", (), RECIPIENT_KEYS),  # DeliveryRcvCustOut.java:51 mask 120
    ("get_pbp_acceptance_specifications", (), ("tkList",)),  # DeliveredTicketOut.java:50 mask 8
    ("get_pbp_acceptance_specifications", ("tkList", 0), (*PBP_TICKET_KEYS, "jrnyList")),  # Tk.java:54 mask 63
    (
        "get_pbp_acceptance_specifications",
        ("tkList", 0, "jrnyList", 0),
        (*PBP_JOURNEY_KEYS, "seatList"),
    ),  # Jrny.java:60 mask 1023
    (
        "get_pbp_acceptance_specifications",
        ("tkList", 0, "jrnyList", 0, "seatList", 0),
        (*PBP_SEAT_KEYS, "scarNo"),
    ),  # Seat.java:53 mask 31
    ("get_ticket_receipt", (), ("receipt_infos",)),  # TicketReceiptOut.java:47 mask 8
    ("get_ticket_receipt", ("receipt_infos",), ("receipt_info",)),  # ReceiptInfos.java:49 mask 1
    (
        "get_ticket_receipt",
        ("receipt_infos", "receipt_info", 0),
        (*RECEIPT_STRINGS, *RECEIPT_INTS, "stl_info", "cash_rcet_info"),
    ),  # ReceiptInfo.java:87 mask 536870911
    (
        "get_ticket_receipt",
        ("receipt_infos", "receipt_info", 0, "stl_info", 0),
        (*PAYMENT_STRINGS, *PAYMENT_INTS),
    ),  # StlInfo.java:55 mask 255
    (
        "get_ticket_receipt",
        ("receipt_infos", "receipt_info", 0, "cash_rcet_info", 0),
        (*CASH_STRINGS, "h_tot_apv_amt"),
    ),  # CashReceiptInfo.java:52 mask 31
]
MISSING_CASES = [(name, path, key) for name, path, keys in REQUIRED_GROUPS for key in keys]


def node_at(data: Any, path: tuple[str | int, ...]) -> Any:
    for key in path:
        data = data[key]
    return data


@pytest.mark.parametrize("name,path,key", MISSING_CASES, ids=lambda v: str(v))
def test_required_missing_preserves_entire_response(name, path, key, make_client) -> None:
    """DptnBank.java:46; CustTripInfoOut.java:51; RecentDeliveryHistoryOut.java:51;
    TicketReceiptOut.java:47; ReceiptInfo.java:87; DeliveredTicketOut.java:50; Seat.java:53.
    """
    entry = BY_NAME[name]
    payload = deepcopy(entry.response)
    del node_at(payload, path)[key]
    payload["synthetic_unknown"] = {"other": [1, "TEST"]}
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, name)(**entry.kwargs)
    assert error.value.raw == payload
    if hasattr(error.value, "parser_raw"):
        assert error.value.parser_raw is not error.value.raw


@pytest.mark.parametrize(
    "name,path,key", [r for r in MISSING_CASES if not (r[0] == "get_recent_delivery_history" and r[1] == ())]
)
def test_required_nonnullable_null_rejected(name, path, key, make_client) -> None:
    """ReceiptInfo.java:87-156; Seat.java:53-70; DptnBank.java:46-58: non-null fields."""
    entry = BY_NAME[name]
    payload = deepcopy(entry.response)
    node_at(payload, path)[key] = None
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, name)(**entry.kwargs)
    assert error.value.raw == payload


@pytest.mark.parametrize("key", ("acepList", "chgePbpRsvNo"))
def test_recent_required_nullable_is_not_missing(key, make_client) -> None:
    """RecentDeliveryHistoryOut.java:51-63: mask 24 with nullable List and String."""
    payload = deepcopy(RECENT_BODY)
    payload[key] = None
    client, _ = make_client(payload)
    result = client.get_recent_delivery_history()
    assert result.raw == payload
    assert (
        (result.recipients == ()) if key == "acepList" else (result.changed_acceptance_reservation_no is None)
    )


@pytest.mark.parametrize(
    "name,path,key",
    [
        (name, path, key)
        for name, path, keys in REQUIRED_GROUPS
        for key in keys
        if isinstance(node_at(BY_NAME[name].response, path)[key], str)
    ],
)
def test_required_string_accepts_json_integer(name, path, key, make_client) -> None:
    """Seat.java:53; DptnBank.java:46; ReceiptInfo.java:87; SESSION_CONTEXT.md §3.6 (2026-09-21)."""
    entry = BY_NAME[name]
    payload = deepcopy(entry.response)
    node_at(payload, path)[key] = 17
    client, _ = make_client(payload)
    result = getattr(client, name)(**entry.kwargs)
    assert result.raw == payload
    assert "17" in typed_strings(result), (name, path, key)


@pytest.mark.parametrize("value", [True, 1.25, {}, []])
def test_required_string_wrong_type_preserves_raw(value, make_client) -> None:
    """Seat.java:53-59: mandatory strings; integer compatibility does not admit bool/float/objects."""
    payload = deepcopy(PBP_BODY)
    payload["tkList"][0]["jrnyList"][0]["seatList"][0]["seatNo"] = value
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        client.get_pbp_acceptance_specifications((FULL_REFERENCE,))
    assert error.value.raw == payload


def test_trip_date_string_array_integer_compatibility(make_client) -> None:
    """TipChgDateInquiryOut.java:28-30,53-64; String members follow §3.6 integer normalization."""
    payload = success(tripChgDates=[20300102, "20300103"])
    client, _ = make_client(payload)
    assert client.get_trip_change_dates(DATE).trip_change_dates == (DATE, "20300103")


@pytest.mark.parametrize("bad", [None, {}, "20300102", [None], [True], [1.5], [{}]])
def test_trip_dates_wrong_structure(bad, make_client) -> None:
    """TipChgDateInquiryOut.java:53-64: required non-null List<String>."""
    payload = success(tripChgDates=bad)
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        client.get_trip_change_dates(DATE)
    assert error.value.raw == payload


@pytest.mark.parametrize("key,bad", [("mainList", [1]), ("mainList", {}), ("mainList", "TEST")])
def test_customer_required_list_structure(key, bad, make_client) -> None:
    """CustTripInfoOut.java:51-63: List<CustTripInfo> rather than an arbitrary scalar/list."""
    payload = success(**{key: bad})
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        client.get_customer_trip_info()
    assert error.value.raw == payload


@pytest.mark.parametrize(
    "key,bad", [("acepList", [None]), ("acepList", {}), ("chgePbpRsvNo", []), ("chgePbpRsvNo", True)]
)
def test_recent_top_level_keys_are_lenient(key, bad, make_client) -> None:
    """RecentDeliveryHistoryOut.java:51-63 marks both keys required, but the 2026-09-24 live response
    carried acepList without chgePbpRsvNo, so both are read as optional."""
    payload = deepcopy(RECENT_BODY)
    payload[key] = bad
    client, _ = make_client(payload)
    result = client.get_recent_delivery_history()
    assert result.raw == payload
    assert (
        (result.recipients == ()) if key == "acepList" else (result.changed_acceptance_reservation_no is None)
    )


@pytest.mark.parametrize("key", ("acepList", "chgePbpRsvNo"))
def test_recent_top_level_keys_may_be_absent(key, make_client) -> None:
    """2026-09-24 live: chgePbpRsvNo was absent from a successful response."""
    payload = deepcopy(RECENT_BODY)
    del payload[key]
    client, _ = make_client(payload)
    result = client.get_recent_delivery_history()
    assert result.raw == payload


@pytest.mark.parametrize(
    "entry",
    [
        c
        for c in CASES
        if c.method
        not in {
            "get_ticket_receipt",
            "get_customer_trip_info",
            "get_trip_change_dates",
            "get_delivery_recipient",
            "get_pbp_acceptance_specifications",
            "get_recent_delivery_history",
        }
    ],
    ids=lambda c: c.method,
)
def test_optional_payload_missing_is_not_required(entry, make_client) -> None:
    """CommonOut.java:360-378 and optional synthetic constructor masks in the Case's response DTO."""
    payload = success(synthetic_unknown=[1, "TEST"])
    client, _ = make_client(payload)
    result = getattr(client, entry.method)(**entry.kwargs)
    assert result.raw == payload


def test_optional_invalid_values_remain_raw(make_client) -> None:
    """RefundCommissionOut.java:62: optional scalars are tolerant, not newly mandatory."""
    payload = success(ret_amt={}, ret_fee=True, synthetic_unknown=[7])
    client, _ = make_client(payload)
    result = client.get_refund_commission(REFERENCE)
    assert result.refund_amount is None and result.refund_fee is None
    assert result.raw == payload


@pytest.mark.parametrize(
    "entry,kwargs,expected",
    [
        (BY_NAME["get_cart_list"], {}, {}),
        (BY_NAME["get_discount_coupons"], {}, {"txtSelPage": "1"}),
        (BY_NAME["get_product_reservations"], {}, {"txtSelPage": "1", "txtCntPerPage": "20"}),
        (BY_NAME["get_product_detail"], {"reservation_no": "TEST-RSV"}, {"txtVrRsNo": "TEST-RSV"}),
        (
            BY_NAME["get_refund_commission"],
            {"ticket": REFERENCE},
            {
                "h_orgtk_ret_sale_dt": "0102",
                "h_orgtk_wct_no": "TEST-WINDOW",
                "h_orgtk_sale_sqno": "TEST-SEQUENCE",
                "h_orgtk_ret_pwd": "TEST-RETURN",
            },
        ),
        (
            BY_NAME["get_self_seat_change_info"],
            {"request": p.SelfSeatChangeInfoRequest(DATE, "00999", "TEST-FROM", "TEST-TO")},
            {"runDt": DATE, "trnNo": "00999", "dptRsStnCd": "TEST-FROM", "arvRsStnCd": "TEST-TO"},
        ),
        (
            BY_NAME["get_ticket_list"],
            {},
            {"txtDeviceId": "TEST-ADVERTISING", "txtIndex": "1", "h_page_no": "1", "hiduserYn": "Y"},
        ),
    ],
)
def test_default_empty_optional_request_fields_are_omitted(entry, kwargs, expected, make_client) -> None:
    """NetworkService.java:15335-15344; MyTicketListIn.java:62: no fabricated type discriminator."""
    client, calls = make_client(deepcopy(entry.response), lang=None)
    getattr(client, entry.method)(**kwargs)
    assert Counter(wire_pairs(calls[0], entry.query)) == Counter(COMMON + list(expected.items()))
    assert "type" not in dict(wire_pairs(calls[0], entry.query))


@pytest.mark.parametrize(
    "method,kwargs,query",
    [
        ("get_deposit_banks", {}, False),
        ("get_commuter_kind_menu", {"commuter_kind_code": "TEST-KIND"}, True),
    ],
)
def test_direct_field_and_query_keep_empty_common_values(method, kwargs, query, make_client) -> None:
    """NetworkApi.java:392-393; PushService.java:16-17: explicit @Field/@Query bypass flattening."""
    client, calls = make_client(deepcopy(BY_NAME[method].response))
    object.__setattr__(client.config, "key", "")
    getattr(client, method)(**kwargs)
    assert ("Key", "") in wire_pairs(calls[0], query)
    assert "lang" not in dict(wire_pairs(calls[0], query))


def test_commuter_passengers_repeat_age_per_person(make_client) -> None:
    """CommutationInfoIn.java:31,38,64; NetworkService.java:15345-15355.

    Intentional discrepancy: 2026-09-24 observation requires this primitive array
    key. Do not remove it just because the generic app flattener skips primitives.
    """
    source = m.CommuterInfoResponse(
        passenger_options=(
            m.CommuterPassengerOption(commuter_usage_age_code="TEST-AGE-A"),
            m.CommuterPassengerOption(commuter_usage_age_code="TEST-AGE-B"),
        )
    )
    request = p.CommuterPassengerRequest.from_response(PASS_DATA, source, (2, 1))
    client, calls = make_client(deepcopy(BY_NAME["get_commuter_info"].response), lang=None)
    client.get_commuter_info(request)
    assert wire_pairs(calls[0]) == COMMON + [
        ("jobDvCd", "b"),
        ("cmtrKndCd", "TEST-KIND"),
        ("psgCnt", "3"),
        ("cmtrUtlAgeCd", "TEST-AGE-A"),
        ("cmtrUtlAgeCd", "TEST-AGE-A"),
        ("cmtrUtlAgeCd", "TEST-AGE-B"),
    ]


def test_commuter_original_ticket_stage(make_client) -> None:
    """CommutationInfoIn.java:64; SeatAssignViewModel.java:291: original-ticket query only."""
    client, calls = make_client(deepcopy(BY_NAME["get_commuter_info"].response), lang=None)
    client.get_commuter_info(p.CommuterTicketInquiryRequest(REFERENCE, "1"))
    assert wire_pairs(calls[0]) == COMMON + [
        ("jobDvCd", "c"),
        ("psgCnt", "0"),
        ("ogtkSaleWctNo", "TEST-WINDOW"),
        ("ogtkSaleDd", "0102"),
        ("ogtkSaleSqno", "TEST-SEQUENCE"),
        ("ogtkRetPwd", "TEST-RETURN"),
        ("inquiryType", "1"),
    ]


@pytest.mark.parametrize(
    "method,code,kwargs",
    [
        ("get_discount_coupons", "WRG000000", {}),
        ("get_pass_schedule", "WRG000000", BY_NAME["get_pass_schedule"].kwargs),
        ("get_reservation_history", "P100", {}),
    ],
)
def test_known_empty_failures_are_not_successful_rows(method, code, kwargs, make_client) -> None:
    """CouponOut.java:55; PassScheduleInfoListOut.java:55; ReservationViewOut.java:64; dated empty-result observations."""
    payload = {"strResult": "FAIL", "h_msg_cd": code, "h_msg_txt": "SYNTHETIC EMPTY"}
    client, _ = make_client(payload)
    result = getattr(client, method)(**kwargs)
    assert result.raw == payload and result.str_result == "FAIL"


@pytest.mark.parametrize("entry", CASES, ids=lambda c: c.method)
def test_p058_never_parsed_as_account_result(entry, make_client) -> None:
    """CommonOut.java:426-438; SESSION_CONTEXT.md §3: P058 remains session expiry."""
    payload = {"strResult": "FAIL", "h_msg_cd": "P058", "h_msg_txt": "SYNTHETIC EXPIRED"}
    client, calls = make_client(payload)
    with pytest.raises(KorailSessionExpiredError) as error:
        getattr(client, entry.method)(**entry.kwargs)
    assert error.value.raw == payload
    assert len(calls) == 1
    assert client.session.current is None


def test_required_method_set_is_exact() -> None:
    """33 explicitly enumerated methods: no case silently substitutes a different read."""
    expected = set(
        "get_cart_list get_deposit_banks get_delay_discount_tickets get_discount_coupons get_korail_point_summary get_mileage_history get_discount_card_usage_history get_discount_card_schedule get_pass_available_dates get_pass_schedule get_trip_menu get_pass_menu get_crew_request_list get_commuter_kind_menu get_commuter_info get_product_reservations get_product_detail get_ticket_receipt get_reservation_history get_seat_assignment_schedule get_multi_child_discount_targets get_customer_trip_info get_trip_change_dates get_delivery_recipient check_ticket_duplication get_pbp_acceptance_specifications get_original_ticket_inquiry get_self_seat_change_info get_recent_delivery_history get_ticket_reservation_detail get_refund_commission get_refund_ticket_detail get_ticket_list".split()
    )
    assert set(BY_NAME) == expected and len(CASES) == 33


def test_socket_guard_active() -> None:
    """SESSION_CONTEXT.md §3.1: fail locally before even a DNS lookup."""
    with pytest.raises(AssertionError, match="OFFLINE ONLY"):
        socket.create_connection(("offline.invalid", 443))


@pytest.mark.parametrize(
    "name", ["get_discount_card_usage_history", "get_discount_card_schedule", "get_delivery_recipient"]
)
def test_ncard_live_status_is_not_promoted(name) -> None:
    """SESSION_CONTEXT.md §3.10; the three N-card read docstrings keep 검증 못 함."""
    assert "검증 못 함" in (getattr(KorailClient, name).__doc__ or "")


def test_mode_one_explicit_dates_are_not_silently_erased(make_client) -> None:
    """MyTicketListIn.java:62; builder preserves explicit dates regardless of txtIndex."""
    client, calls = make_client(success(pnr_list=[]), lang=None)
    client.get_ticket_list(mode="1", boarding_date_from=DATE, boarding_date_to="20300103")
    form = dict(wire_pairs(calls[0]))
    assert form["h_abrd_dt_from"] == DATE and form["h_abrd_dt_to"] == "20300103"


def test_required_integer_retains_zero_padding_only_in_raw(make_client) -> None:
    """ReceiptInfo.java:87; StlInfo.java:55: Kotlin Int normalizes a quoted decimal."""
    payload = deepcopy(RECEIPT_BODY)
    payload["receipt_infos"]["receipt_info"][0]["h_rcvd_amt"] = "001200"
    client, _ = make_client(payload)
    result = client.get_ticket_receipt(**BY_NAME["get_ticket_receipt"].kwargs)
    assert result.items[0].received_amount == 1200
    assert result.raw == payload


@pytest.mark.parametrize(("wire", "expected"), [("-1200", -1200), ("-0", 0)])
def test_required_integer_accepts_a_leading_minus_like_kotlinx(wire, expected, make_client) -> None:
    """JsonReader.java:575-640: a quoted Int may start with '-'."""
    payload = deepcopy(RECEIPT_BODY)
    payload["receipt_infos"]["receipt_info"][0]["h_rcvd_amt"] = wire
    client, _ = make_client(payload)
    assert (
        client.get_ticket_receipt(**BY_NAME["get_ticket_receipt"].kwargs).items[0].received_amount == expected
    )


@pytest.mark.parametrize("wire", ["-", "--1", "1-", "1e3", "+1"])
def test_required_integer_still_rejects_other_signed_shapes(wire, make_client) -> None:
    payload = deepcopy(RECEIPT_BODY)
    payload["receipt_infos"]["receipt_info"][0]["h_rcvd_amt"] = wire
    client, _ = make_client(payload)
    with pytest.raises(KorailProtocolError):
        client.get_ticket_receipt(**BY_NAME["get_ticket_receipt"].kwargs)


@pytest.mark.parametrize("method", ["get_pbp_acceptance_specifications", "get_original_ticket_inquiry"])
def test_ticket_reference_list_is_sent_like_a_tuple(method, make_client) -> None:
    entry = BY_NAME[method]
    client, calls = make_client(entry.response)
    getattr(client, method)(**entry.kwargs)
    getattr(client, method)(**{**entry.kwargs, "tickets": list(entry.kwargs["tickets"])})
    assert calls[0].content == calls[1].content
    with pytest.raises(KorailProtocolError):
        getattr(client, method)(**{**entry.kwargs, "tickets": "not-a-sequence-of-references"})


def test_coupon_discount_values_keep_their_field(make_client) -> None:
    """CouponOutInfo.java:63: all 13 fields are optional, so each value keeps its own attribute."""
    weekday = {"h_cpn_no": "TEST-WEEKDAY", "h_disc_rt_amt_dv_cd": "1", "h_inwk_fare_disc_rt_amt": 10}
    weekend = {"h_cpn_no": "TEST-WEEKEND", "h_disc_rt_amt_dv_cd": "1", "h_wknd_fare_disc_rt_amt": "10"}
    payload = success(coupon_infos={"coupon_info": [weekday, weekend]})
    client, _ = make_client(payload)
    first, second = client.get_discount_coupons(**BY_NAME["get_discount_coupons"].kwargs).items
    assert (first.weekday_fare_discount, first.weekend_fare_discount) == ("10", None)
    assert (second.weekday_fare_discount, second.weekend_fare_discount) == (None, "10")
    assert first.discount_rate_amount_division_code == second.discount_rate_amount_division_code == "1"


@pytest.mark.parametrize("entry", CASES, ids=lambda c: c.method)
def test_integer_envelope_fields_are_read_as_strings(entry, make_client) -> None:
    """2026-09-21 observation: JSON integers in String fields. http.parse_base_response and the read parsers
    share _parsing._envelope, so a transport-accepted envelope is not rejected again by the parser."""
    payload = deepcopy(entry.response)
    payload["h_msg_cd"] = 0
    payload["h_msg_txt"] = 7
    client, calls = make_client(payload)
    result = getattr(client, entry.method)(**entry.kwargs)
    assert (result.h_msg_cd, result.h_msg_txt) == ("0", "7")
    assert result.raw == payload
    assert len(calls) == 1


@pytest.mark.parametrize("entry", CASES, ids=lambda c: c.method)
@pytest.mark.parametrize("field", ("strResult", "h_msg_cd", "h_msg_txt"))
def test_malformed_envelope_preserves_entire_response(entry, field, make_client) -> None:
    """SESSION_CONTEXT.md §3.6; _parsing.py:41-53 and http.py:parse_base_response.

    The existing envelope rejection policy is not changed. The full JSON must
    survive an HTTP-layer rejection before the domain parser is called.
    """
    payload = deepcopy(entry.response)
    payload[field] = {"SYNTHETIC": [1, 2]}
    payload["synthetic_unknown"] = "PRESERVE"
    client, calls = make_client(payload)
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, entry.method)(**entry.kwargs)
    assert error.value.raw == payload
    assert len(calls) == 1
