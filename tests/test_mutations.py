"""Offline domain contracts use only synthetic responses and block real network access."""

from __future__ import annotations

import ast
import copy
import json
from collections import defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api.client as client_module
import korail_mobile_api.mutation_payloads as payload_module
from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.constants import KorailReservationJobType as Job
from korail_mobile_api.constants import KorailSeatClass as Cabin
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import KorailApiError, KorailProtocolError, KorailSessionExpiredError
from korail_mobile_api.models import KorailSession, TrainSummary
from korail_mobile_api.mutation_models import (
    CardPayment,
    CartAddRequest,
    DiscountCardAdditionalUser,
    DiscountCardPurchaseRequest,
    DiscountCardSectionRequest,
    DiscountCardTicket,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
    ReservationJourney,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
)
from korail_mobile_api.mutation_parsers import parse_refund_ticket_response
from korail_mobile_api.read_models import (
    PbpAcceptanceJourney,
    PbpAcceptanceTicket,
    ProductDetailResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    SelfCheckInSeat,
    TrainScheduleItem,
)

COMMON = {"Device": "SYNTH-ANDROID", "Version": "SYNTH-706", "Key": "SYNTH-KEY", "lang": "SYNTH-LANG"}
BASE = {
    "strResult": "SUCC",
    "h_msg_cd": "SYNTH-SUCCESS",
    "h_msg_txt": "synthetic response",
    "extra": {"keep": [1, 2]},
}
ROOT = "/classes/com.korail.mobile."
PNR = "SYNTH-PNR-ONLY"


@pytest.fixture(autouse=True)
def fixed_card_month(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the card-expiry reference month. conftest.f8_block_sockets blocks the network."""
    monkeypatch.setattr(payload_module, "_current_year_month", lambda: 202609)


def train(second: bool = False, **changes: Any) -> TrainSummary:
    values = dict(
        train_no="90002" if second else "90001",
        train_group_code="100",
        train_class_code="0A",
        run_date="20991230",
        departure_date="20991230",
        departure_time="130000" if second else "100000",
        arrival_time="150000" if second else "120000",
        departure_station_code="9002" if second else "9001",
        arrival_station_code="9003" if second else "9002",
        departure_construction_order="003",
        arrival_construction_order="009",
        departure_run_order="002",
        arrival_run_order="007",
        seat_attribute_code="015",
        general_reservation_code="11",
        special_reservation_code="11",
        standing_reservation_code="13",
        merge_seat_application_flag="A",
        wait_reservation_flag=" 9",
    )
    values.update(changes)
    return TrainSummary(**values)


def hold(**changes: Any) -> ReservationHoldResponse:
    values = dict(
        str_result="SUCC",
        pnr_no=PNR,
        journey_count="0001",
        window_no="SYNTH-WINDOW",
        temporary_job_sequence_1="001234",
        temporary_job_sequence_2="005678",
        received_amount="1200",
        total_price="9900",
        journeys=(ReservationJourney(journey_sequence="0007", reservation_change_no="009"),),
    )
    values.update(changes)
    return ReservationHoldResponse(**values)


def card(**changes: Any) -> CardPayment:
    values = dict(card_number="0000000000000000", card_password="00", card_expire="9912", birthday="000000")
    values.update(changes)
    return CardPayment(**values)


def ticket() -> PaidTicket:
    return PaidTicket(
        PNR, "20991230", "SYNTH-ORIGINAL-WINDOW", "SYNTH-ORIGINAL-SEQ", "SYNTH-RETURN-PWD", "90001", "SYNTH-PBP"
    )


#: 앱은 환불 전에 항상 수수료를 조회합니다. 회차 코드가 없으면 첫 열차 번호만 더 실립니다.
COMMISSION = RefundCommissionResponse(str_result="SUCC")


def merge_rows(standing: bool = True) -> tuple[TrainScheduleItem, ...]:
    return (
        TrainScheduleItem(
            train_no="90001",
            arrival_station_code="9099",
            arrival_construction_order="004",
            arrival_run_order="003",
            general_reservation_code="13" if standing else "11",
            standing_reservation_code="11" if standing else "13",
        ),
        TrainScheduleItem(
            train_no="90001",
            arrival_station_code="9002",
            arrival_construction_order="009",
            arrival_run_order="007",
            general_reservation_code="11",
            standing_reservation_code="13",
        ),
    )


def hold_raw() -> dict[str, Any]:
    return {
        **copy.deepcopy(BASE),
        "h_pnr_no": PNR,
        "h_jrny_cnt": "0001",
        "h_wct_no": "SYNTH-WINDOW",
        "h_tmp_job_sqno1": "001234",
        "h_tmp_job_sqno2": "005678",
        "h_tot_rcvd_amt": "001200",
        "h_tot_prc": "9900",
        "jrny_infos": {
            "jrny_info": [
                {
                    "h_jrny_sqno": "0007",
                    "h_rsv_chg_no": "009",
                    "h_trn_no": "90001",
                    "seat_infos": {
                        "seat_info": [
                            {"h_seat_no": "1A", "h_rcvd_amt": "000700"},
                            {"h_seat_no": "1B", "h_rcvd_amt": 500},
                        ]
                    },
                }
            ]
        },
    }


def reservation_form(
    *, transfer: bool = False, job: str = "1101", stnd: str = "N", cabin2: str = "1"
) -> dict[str, Any]:
    """TicketReservationIn.java:80; TicketReservationInJrny.java:69; TrainScheduleViewModel.java:2932,3004."""
    result = {
        **COMMON,
        "txtMenuId": "11",
        "txtJobId": job,
        "hidFreeFlg": "N",
        "txtStndFlg": stnd,
        "txtTotPsgCnt": "1",
        "txtCompaCnt1": "1",
        "txtPsgTpCd1": "1",
        "txtDiscKndCd1": "000",
        "txtSeatAttCd1": "000",
        "txtSeatAttCd2": "000",
        "txtSeatAttCd3": "000",
        "txtSeatAttCd4": "015",
        "txtSeatAttCd5": "000",
        "txtJrnyCnt": "2" if transfer else "1",
    }
    rows = [("90001", "9001", "9002", "100000", "1")]
    if transfer:
        rows.append(("90002", "9002", "9003", "130000", cabin2))
        result["txtSeatAttCd4_1"] = "015"
    for i, (number, departure, arrival, time, cabin) in enumerate(rows, 1):
        row = {
            "txtJrnyTpCd": "14" if transfer else "11",
            "txtJrnySqno": f"{i:03}",
            "txtTrnNo": number,
            "txtTrnClsfCd": "0A",
            "txtTrnGpCd": "100",
            "txtRunDt": "20991230",
            "txtDptDt": "20991230",
            "txtDptTm": time,
            "txtDptRsStnCd": departure,
            "txtDptStnConsOrdr": "003",
            "txtDptStnRunOrdr": "002",
            "txtArvRsStnCd": arrival,
            "txtArvStnConsOrdr": "009",
            "txtArvStnRunOrdr": "007",
            "txtChgFlg": "N",
            "txtPsrmClCd": cabin,
        }
        result.update({f"{k}{i}": v for k, v in row.items()})
    return result


def payment_form(**changes: str) -> dict[str, Any]:
    """PayViewModel.java:6680-6684; PaymentMethodHelper.java:110-130 (protected defaults unresolved)."""
    return {
        **COMMON,
        "hidPnrNo": PNR,
        "hidWctNo": "SYNTH-WINDOW",
        "hidTmpJobSqno1": "001234",
        "hidTmpJobSqno2": "005678",
        "hidRsvChgNo": "009",
        "hidInrecmnsGridcnt": "1",
        "hidStlMnsSqno1": "1",
        "hidStlMnsCd1": "02",
        "hidMnsStlAmt1": "1200",
        "hidCrdInpWayCd1": "@",
        "hidStlCrCrdNo1": "0000000000000000",
        "hidVanPwd1": "00",
        "hidCrdVlidTrm1": "9912",
        "hidIsmtMnthNum1": "0",
        "hidAthnDvCd1": "J",
        "hidAthnVal1": "000000",
        "hiduserYn": "Y",
        **changes,
    }


def refund_form(**changes: str) -> dict[str, Any]:
    """MyTicketDetailViewModel.java:1521; RefundTicketIn.java:66."""
    return {
        **COMMON,
        "txtPnrNo": PNR,
        "h_orgtk_sale_dt": "20991230",
        "h_orgtk_sale_wct_no": "SYNTH-ORIGINAL-WINDOW",
        "h_orgtk_sale_sqno": "SYNTH-ORIGINAL-SEQ",
        "h_orgtk_ret_pwd": "SYNTH-RETURN-PWD",
        "h_mlg_stl": "N",
        "pbpAcepTgtFlg": "SYNTH-PBP",
        **changes,
    }


def verification_request() -> StationRefundVerificationRequest:
    return StationRefundVerificationRequest("SYNTH-CUSTOMER", "SYNTH-A", "SYNTH-B", "SYNTH-C", "SYNTH-D")


def verification_raw() -> dict[str, Any]:
    return {
        **copy.deepcopy(BASE),
        "rcvd_amt": "1200",
        "ret_amt": "1100",
        "ret_fee": "100",
        "poppMsg": "synthetic popup",
        "strMsg": "synthetic result",
        "orgtkinfo_list": [
            {
                "pnr_no": PNR,
                "ogtk_sale_dt": "20991230",
                "ogtk_sale_wct_no": "SYNTH-ORIGINAL-WINDOW",
                "ogtk_sale_sqno": "SYNTH-ORIGINAL-SEQ",
                "ogtk_ret_pwd": "SYNTH-RETURN-PWD",
                "tk_knd_cd": "SYNTH-KIND",
                "ret_dv_cd": "SYNTH-DIV",
                "ret_rsn_cd": "SYNTH-REASON",
            }
        ],
    }


def execution_request() -> StationRefundExecutionRequest:
    return StationRefundExecutionRequest(
        PNR,
        "20991230",
        "SYNTH-ORIGINAL-WINDOW",
        "SYNTH-ORIGINAL-SEQ",
        "SYNTH-RETURN-PWD",
        "SYNTH-DIV",
        "SYNTH-REASON",
        "SYNTH-KIND",
        "00000000000",
        "1100",
        "100",
        "SYNTH-CUSTOMER",
    )


def execution_form() -> dict[str, Any]:
    """StationTicketRefundResultViewModel.java:151-164: original ticket IDs and quoted amounts are echoed."""
    return {
        **COMMON,
        "pnrNo": PNR,
        "ogtkSaleDt": "20991230",
        "ogtkSaleWctNo": "SYNTH-ORIGINAL-WINDOW",
        "ogtkSaleSqno": "SYNTH-ORIGINAL-SEQ",
        "ogtkRetPwd": "SYNTH-RETURN-PWD",
        "retDvCd": "SYNTH-DIV",
        "retRsnCd": "SYNTH-REASON",
        "tkKndCd": "SYNTH-KIND",
        "custTeln": "00000000000",
        "retAmt": "1100",
        "retFee": "100",
        "acepCustNm": "SYNTH-CUSTOMER",
    }


def purchase_request() -> DiscountCardPurchaseRequest:
    return DiscountCardPurchaseRequest(
        "SYNTH-N-KIND",
        "SYNTH-CUSTOMER-NO",
        "20991230",
        "10",
        (
            DiscountCardSectionRequest("20991230", "90001", "9001", "9002"),
            DiscountCardSectionRequest("20991231", "90002", "9002", "9003", "14"),
        ),
        (DiscountCardAdditionalUser("SYNTH-SECOND-NO", "SYNTH-SECOND-NAME", "00000000000"),),
    )


def purchase_form() -> dict[str, Any]:
    """NCardInfoIn.java:29-39; NCardjrny.java:55. 검증 못 함: protected names/values remain unverified."""
    return {
        **COMMON,
        "dcntCrdKndMgNo": "SYNTH-N-KIND",
        "custMgNo": "SYNTH-CUSTOMER-NO",
        "vlidTrmStDt": "20991230",
        "usePsbTno": "10",
        "jrnyCnt": "2",
        "jrnyTpCd_1": "11",
        "runDt_1": "20991230",
        "trnNo_1": "90001",
        "dptRsStnCd_1": "9001",
        "arvRsStnCd_1": "9002",
        "jrnyTpCd_2": "14",
        "runDt_2": "20991231",
        "trnNo_2": "90002",
        "dptRsStnCd_2": "9002",
        "arvRsStnCd_2": "9003",
        "apdUsrCnt": "1",
        "custMgNo_1": "SYNTH-SECOND-NO",
        "apdCustName_1": "SYNTH-SECOND-NAME",
        "apdCustTeln_1": "00000000000",
    }


def recalc_request(**changes: Any) -> PriceRecalculationRequest:
    return PriceRecalculationRequest(
        PNR,
        (
            PriceRecalculationRow("1", "1", "000", "", "", ""),
            PriceRecalculationRow("3", "2", "SYNTH-OLD", "SYNTH-NEW", "SYNTH-CERT", "SYNTH-FAMILY"),
        ),
        **changes,
    )


def recalc_form(**changes: Any) -> dict[str, Any]:
    """NetworkApi.java:583-584: six repeated unnumbered lists preserve empty positions."""
    return {
        **COMMON,
        "hidPnrNo": PNR,
        "txtJobId": "1101",
        "txtPsgGridcnt": "2",
        "psg_tp_dv_cd": ["1", "3"],
        "psrm_cl_cd": ["1", "2"],
        "dcnt_knd_cd1": ["000", "SYNTH-OLD"],
        "hidDcntKndCd": ["", "SYNTH-NEW"],
        "hidDscpNo": ["", "SYNTH-CERT"],
        "hidFmlyNo": ["", "SYNTH-FAMILY"],
        **changes,
    }


def payment_raw() -> dict[str, Any]:
    return {
        **copy.deepcopy(BASE),
        "h_rsv_no": PNR,
        "h_tot_rcvd_amt": "1200",
        "h_im_flg": "SYNTH-IMAGE",
        "h_stl_amt": "1200",
        "tk_coupon_info": [{"h_coup_no": "SYNTH-COUPON", "extra_coupon": 1}],
        "tk_infos": {
            "tk_info": [
                {
                    "h_tk_sqno": "01",
                    "h_sale_dt": "20991230",
                    "h_sale_sqno": "SYNTH-ISSUE-SEQ",
                    "h_tk_ret_pwd": "SYNTH-PWD",
                    "h_tot_rcvd_amt": "1200",
                }
            ]
        },
        "stl_infos": {
            "stl_info": [{"h_stl_rlt": "SYNTH-DECLINED-LEG", "h_apv_tm": "123456", "h_stl_amt": "1200"}]
        },
        "tbl_seat_infos": {"tbl_seat_info": [{"h_seat_no": "1A", "extra_table": 1}]},
    }


@dataclass(frozen=True)
class Case:
    name: str
    invoke: Callable[[KorailClient], Any]
    method: str
    routes: tuple[str, ...]
    form: dict[str, Any]
    response: dict[str, Any]
    parser_name: str | None
    attributes: dict[str, Any]


def cases() -> list[Case]:
    reserve = "certification.TicketReservation"
    merge = {
        **reservation_form(job="1202", stnd="Y"),
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    nreserve = {**reservation_form(), "txtMenuId": "A2", "txtDiscKndCd1": "153", "txtCardNo_1": "SYNTH-N-CARD"}
    cancel = {**COMMON, "txtPnrNo": PNR, "txtJrnySqno": "0007", "txtJrnyCnt": "0001", "hidRsvChgNo": "009"}
    nraw = {
        **BASE,
        "lumpStlTgtNo": "SYNTH-LUMP",
        "dcntCrdStlTgtNo": "SYNTH-N-TARGET",
        "dcntCrdKndMgNo": "SYNTH-SERVER-KIND",
        "rcvdAmt": "1200",
        "stxAmt": "100",
        "taxtSplAmt": "1100",
        "usePsbTno": "10",
        "vlidTrmStDt": "20991230",
        "vlidTrmClsDt": "20991231",
    }
    return [
        Case(
            "reserve",
            lambda c: c.reserve(train()),
            "POST",
            (reserve,),
            reservation_form(),
            hold_raw(),
            "parse_reservation_hold_response",
            {"pnr_no": PNR, "received_amount": "1200", "total_price": "9900"},
        ),
        Case(
            "reserve_transfer",
            lambda c: c.reserve_transfer([train(), train(True)], seat_classes=(Cabin.GENERAL, Cabin.SPECIAL)),
            "POST",
            (reserve,),
            reservation_form(transfer=True, cabin2="2"),
            hold_raw(),
            "parse_reservation_hold_response",
            {"pnr_no": PNR},
        ),
        Case(
            "reserve_merge",
            lambda c: c.reserve_merge(train(), merge_rows()),
            "POST",
            (reserve,),
            merge,
            hold_raw(),
            "parse_reservation_hold_response",
            {"received_amount": "1200"},
        ),
        Case(
            "reserve_with_discount_card",
            lambda c: c.reserve_with_discount_card(train(), card_no="SYNTH-N-CARD"),
            "POST",
            (reserve,),
            nreserve,
            hold_raw(),
            "parse_reservation_hold_response",
            {"pnr_no": PNR},
        ),
        Case(
            "confirm_standby_hold",
            lambda c: c.confirm_standby_hold(
                hold(), allow_seat_class_change=True, sms_notify=True, phone_no="00000000000"
            ),
            "POST",
            ("reservationWait.ReservationWait",),
            {**COMMON, "txtPnrNo": PNR, "txtPsrmClChgFlg": "Y", "txtSmsSndFlg": "Y", "txtCpNo": "00000000000"},
            BASE,
            None,
            {},
        ),
        Case(
            "cancel_unpaid_hold",
            lambda c: c.cancel_unpaid_hold(hold()),
            "POST",
            ("reservationCancel.ReservationCancel", "reservationCancel.ReservationCancelChk"),
            cancel,
            BASE,
            None,
            {},
        ),
        Case(
            "cancel_product_reservation",
            lambda c: c.cancel_product_reservation(
                ProductDetailResponse(virtual_reservation_no="SYNTH-PRODUCT", goods_sequence="SYNTH-GOODS")
            ),
            "GET",
            ("product.ReservationCancel",),
            {**COMMON, "txtVrRsNo": "SYNTH-PRODUCT", "txtGdSqno": "SYNTH-GOODS"},
            {**BASE, "intgMsgCd": "SYNTH-INTEGRATED"},
            "parse_product_cancel_response",
            {"integrated_message_code": "SYNTH-INTEGRATED"},
        ),
        Case(
            "pay_with_card",
            lambda c: c.pay_with_card(hold(), card()),
            "POST",
            ("payment.ReservationPayment",),
            payment_form(),
            payment_raw(),
            "parse_reservation_payment_response",
            {"total_received_amount": "1200"},
        ),
        Case(
            "refund",
            lambda c: c.refund(ticket(), commission=COMMISSION),
            "POST",
            ("refunds.RefundsRequest",),
            refund_form(trnNo="90001"),
            {**BASE, "stlList": [{"stl_mns_cd": "02"}, {"stl_mns_cd": "SYNTH-SECOND"}]},
            "parse_refund_ticket_response",
            {"settlement_method_codes": ("02", "SYNTH-SECOND"), "settlement_list_is_null": False},
        ),
        Case(
            "verify_station_ticket_refund",
            lambda c: c.verify_station_ticket_refund(verification_request()),
            "POST",
            ("refunds.verifyOnlineRefunds",),
            {
                **COMMON,
                "strName": "SYNTH-CUSTOMER",
                "retNo1": "SYNTH-A",
                "retNo2": "SYNTH-B",
                "retNo3": "SYNTH-C",
                "retNo4": "SYNTH-D",
            },
            verification_raw(),
            "parse_station_refund_verification_response",
            {"refund_amount": "1100", "refund_fee": "100"},
        ),
        Case(
            "execute_station_ticket_refund",
            lambda c: c.execute_station_ticket_refund(execution_request()),
            "POST",
            ("refunds.executeOnlineRefunds",),
            execution_form(),
            {**BASE, "h_ret_dv_cd": "SYNTH-DIV"},
            "parse_station_refund_execution_response",
            {"refund_division_code": "SYNTH-DIV"},
        ),
        Case(
            "add_to_cart",
            lambda c: c.add_to_cart(CartAddRequest(PNR)),
            "POST",
            ("cart.addCartList",),
            {**COMMON, "hidPnrNo": PNR},
            {
                **BASE,
                "psgDiscAdd_infos": {
                    "psgDiscAdd_info": [{"h_psg_sqno": "01", "h_duty_ref_rcgn_ps_dv_cd": "SYNTH-DISC"}]
                },
            },
            "parse_cart_add_response",
            {},
        ),
        Case(
            "register_discount_card",
            lambda c: c.register_discount_card(purchase_request()),
            "POST",
            ("research.dcntCrdInfo.do",),
            purchase_form(),
            nraw,
            "parse_discount_card_purchase_response",
            {
                "lump_settlement_target_no": "SYNTH-LUMP",
                "registered_card_kind_management_no": "SYNTH-SERVER-KIND",
                "discount_card_settlement_target_no": "SYNTH-N-TARGET",
                "received_amount": "1200",
                "stx_amount": "100",
                "taxt_supply_amount": "1100",
                "usable_trip_count": "10",
                "validity_start_date": "20991230",
                "validity_end_date": "20991231",
            },
        ),
        Case(
            "extend_discount_card",
            lambda c: c.extend_discount_card(
                DiscountCardTicket(
                    "SYNTH-ORIGINAL-WINDOW", "20991230", "SYNTH-ORIGINAL-SEQ", "SYNTH-RETURN-PWD"
                )
            ),
            "POST",
            ("reservation.dcntCrdExtn.do",),
            {
                **COMMON,
                "saleWctNo": "SYNTH-ORIGINAL-WINDOW",
                "saleDd": "20991230",
                "saleSqno": "SYNTH-ORIGINAL-SEQ",
                "tkRetPwd": "SYNTH-RETURN-PWD",
            },
            BASE,
            None,
            {},
        ),
        Case(
            "recalculate_price",
            lambda c: c.recalculate_price(recalc_request()),
            "POST",
            ("certification.PriceReCalculation",),
            recalc_form(),
            hold_raw(),
            "parse_reservation_hold_response",
            {"pnr_no": PNR, "received_amount": "1200"},
        ),
        Case(
            "register_self_checkin",
            lambda c: c.register_self_checkin(CHECKIN_DETAIL, CHECKIN_SEAT),
            "POST",
            ("checkin.reg.do",),
            {
                **COMMON,
                "cpsNo": "SYNTH-CPS",
                "scarNo": "0017",
                "seatNo": "5A",
                "saleWctNo": "SYNTH-WINDOW",
                "saleDd": "1230",
                "saleSqno": "SYNTH-SEQ",
                "tkRetPwd": "SYNTH-PWD",
                "jrnySqno": "001",
            },
            {**BASE, "msgId": "SYNTH-MSG"},
            "parse_self_checkin_register_response",
            {"message_id": "SYNTH-MSG"},
        ),
        Case(
            "cancel_self_checkin",
            lambda c: c.cancel_self_checkin(CHECKIN_DETAIL),
            "POST",
            ("checkin.cnc.do",),
            {
                **COMMON,
                "saleWctNo": "SYNTH-WINDOW",
                "saleDt": "20991230",
                "saleSqno": "SYNTH-SEQ",
                "tkRetPwd": "SYNTH-PWD",
                "jrnySqno": "001",
            },
            BASE,
            "parse_self_checkin_cancel_response",
            {"message_id": None},
        ),
        Case(
            "retrieve_delivered_ticket",
            lambda c: c.retrieve_delivered_ticket(DELIVERED_TICKET),
            "POST",
            ("tk.pbpWdrw.do",),
            {**COMMON, "pbpCnt": "1", "pbpRsvNo": ["SYNTH-PBP"], "pnrNo": [PNR]},
            {**BASE, "prsList": [{"prsFlg": "Y"}]},
            "parse_delivered_ticket_retrieval_response",
            {"process_flags": ("Y",)},
        ),
    ]


CHECKIN_DETAIL = RefundTicketDetailResponse(
    sale_date="20991230",
    original_sale_date="1230",
    original_window_no="SYNTH-WINDOW",
    original_sale_sequence="SYNTH-SEQ",
    original_return_password="SYNTH-PWD",
    journeys=(RefundTicketJourney(journey_sequence="001"),),
)
CHECKIN_SEAT = SelfCheckInSeat(
    *("SYNTH-PNR", "002", "01", "20991230", "00101", "1", "0001", "5", "0020", "11", "100", "0017", "5A"),
    *("20991230100000", "20991230120000", "SYNTH-CPS"),
)
DELIVERED_TICKET = PbpAcceptanceTicket(
    pnr_no=PNR,
    sale_date="20991230",
    sale_sequence="SYNTH-SEQ",
    sale_window_no="SYNTH-WINDOW",
    return_password="SYNTH-PWD",
    journeys=(
        PbpAcceptanceJourney(
            acceptance_customer_name="SYNTH-NAME",
            acceptance_customer_phone="SYNTH-PHONE",
            journey_type_code="11",
            member_division_name="SYNTH-MEMBER",
            acceptance_kind_name="SYNTH-KIND",
            pbp_reservation_no="SYNTH-PBP",
            registered_date="20991229",
            withdrawal_possible_flag="Y",
            member_card_no="SYNTH-CARD",
        ),
    ),
)
CASES = cases()


def pairs(mapping: dict[str, Any]) -> dict[str, list[str]]:
    return {k: v if isinstance(v, list) else [v] for k, v in mapping.items()}


class Harness:
    def __init__(
        self, responses: list[Any], method: str, routes: tuple[str, ...], expected: dict[str, Any]
    ) -> None:
        self.seen: list[httpx.Request] = []
        self.expected = expected

        def handler(request: httpx.Request) -> httpx.Response:
            i = len(self.seen)
            self.seen.append(request)
            assert i < len(responses), "duplicate/unexpected transmission"
            assert request.url.host == "offline.invalid"
            assert request.method == method
            assert request.url.path == ROOT + routes[i]
            encoded = request.url.query.decode() if method == "GET" else request.content.decode()
            if method == "GET":
                assert request.content == b""
            else:
                assert request.url.query == b""
                assert request.headers["content-type"].startswith("application/x-www-form-urlencoded")
            actual: dict[str, list[str]] = defaultdict(list)
            for key, value in parse_qsl(encoded, keep_blank_values=True):
                actual[key].append(value)
            assert dict(actual) == pairs(expected)
            return httpx.Response(
                200,
                content=json.dumps(responses[i]).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )

        cfg = KorailConfig(
            base_url="https://offline.invalid",
            device=COMMON["Device"],
            version=COMMON["Version"],
            key=COMMON["Key"],
            lang=COMMON["lang"],
            netfunnel_enabled=False,
            dynapath=DynapathConfig(enabled=True, token_provider=lambda ctx: "SYNTHETIC-OFFLINE-NOT-A-TOKEN"),
        )
        self.client = KorailClient(cfg, transport=httpx.MockTransport(handler))
        self.client.session.current = KorailSession(jsessionid="SYNTH-SESSION", customer_no="SYNTH-CUSTOMER-NO")

    def close(self) -> None:
        self.client.close()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_each_public_method_entire_wire_form_and_parse(case: Case) -> None:
    """NetworkApi.java:192-193,266-267,336-337,519-520,583-584,603-604,615-620,631-640,752-753,799-800,811-812."""
    h = Harness([copy.deepcopy(case.response) for _ in case.routes], case.method, case.routes, case.form)
    try:
        result = case.invoke(h.client)
        assert result.raw == case.response
        assert result.str_result == "SUCC"
        assert result.h_msg_cd == "SYNTH-SUCCESS"
        for attr, value in case.attributes.items():
            assert getattr(result, attr) == value
        if case.name == "add_to_cart":
            assert result.discount_additions[0].passenger_sequence_no == "01"
            assert result.discount_additions[0].duty_reference_recognition_division_code == "SYNTH-DISC"
        if case.name == "pay_with_card":
            assert (
                len(result.tickets)
                == len(result.settlements)
                == len(result.coupons)
                == len(result.table_seats)
                == 1
            )
            assert result.tickets[0].raw == case.response["tk_infos"]["tk_info"][0]
            assert (
                result.settlements[0].raw["h_stl_rlt"] == "SYNTH-DECLINED-LEG"
            )  # Do not collapse partial results into success.
        if case.name == "verify_station_ticket_refund":
            assert result.original_tickets[0].pnr_no == PNR
            assert result.original_tickets[0].original_sale_window_no == "SYNTH-ORIGINAL-WINDOW"
        assert len(h.seen) == len(case.routes)
    finally:
        h.close()


PARSED_CASES = [c for c in CASES if c.parser_name is not None]


@pytest.mark.parametrize("case", PARSED_CASES, ids=lambda c: c.name)
@pytest.mark.parametrize("kind", ["protocol", "unexpected"])
def test_parser_failure_retains_whole_response_and_never_retries(
    case: Case, kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """checks/BEHAVIOR.md / ACCEPTANCE G9: full response survives a post-commit parse error, including GET product cancellation."""
    partial = {"synthetic_partial": "only-one-row"}

    def broken(raw: dict[str, Any]) -> Any:
        if kind == "protocol":
            error = KorailProtocolError("synthetic parser failure")
            error.raw = partial
            raise error
        raise ValueError("synthetic unexpected parser failure")

    monkeypatch.setattr(client_module, case.parser_name, broken)
    h = Harness([copy.deepcopy(case.response)], case.method, case.routes[:1], case.form)
    try:
        with pytest.raises(KorailProtocolError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == case.response
        if kind == "protocol":
            assert caught.value.parser_raw == partial
        else:
            assert isinstance(caught.value.__cause__, ValueError)
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize(
    "first_result,stops",
    [("FAIL", True), ("SUCC", False), ("SYNTH-UNKNOWN", False), (None, False), ("", False)],
)
def test_cancel_two_stage_non_fail_policy(first_result: Any, stops: bool) -> None:
    """MyReservationViewModel.smali:5589,5707,6284; CommonOut.smali:2493-2560.
    FAIL literal is observed, not decrypted."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    responses = [
        {**BASE, "strResult": first_result, "h_msg_cd": "SYNTH-FIRST"},
        {**BASE, "h_msg_cd": "SYNTH-FINAL"},
    ]
    h = Harness(responses, "POST", case.routes, case.form)
    try:
        if stops:
            with pytest.raises(KorailApiError) as caught:
                case.invoke(h.client)
            assert caught.value.raw == responses[0]
            assert len(h.seen) == 1
        else:
            result = case.invoke(h.client)
            assert len(h.seen) == 2
            assert result.h_msg_cd == "SYNTH-FINAL"
    finally:
        h.close()


def test_cancel_skip_check_and_echo_padding() -> None:
    """ReservationCancelChkIn.java:53; MyReservationViewModel.java:1557,1566."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    expected = {**case.form, "txtJrnyCnt": "0002"}
    h = Harness([BASE], "POST", (case.routes[-1],), expected)
    try:
        h.client.cancel_unpaid_hold(hold(journey_count="0002"), check_first=False)
        assert len(h.seen) == 1
    finally:
        h.close()


def test_cancel_second_stage_failure_is_not_retried() -> None:
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    failure = {**BASE, "strResult": "FAIL", "h_msg_cd": "SYNTH-SECOND-FAIL"}
    h = Harness([BASE, failure], "POST", case.routes, case.form)
    try:
        with pytest.raises(KorailApiError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == failure
        assert len(h.seen) == 2
    finally:
        h.close()


@pytest.mark.parametrize("standing", [False, True])
def test_merge_exact_four_overrides(standing: bool) -> None:
    """ReservationMergeViewModel.smali:7671-7774 mask=0x7ffef; TicketReservationIn.java:486 (zero-based bits 4,19,20,21)."""
    first = reservation_form(job="1202")
    merged = {
        **first,
        "txtStndFlg": "Y" if standing else "N",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    changed = {key for key in first.keys() | merged.keys() if first.get(key) != merged.get(key)}
    assert changed == ({"txtStndFlg"} if standing else set()) | {
        "txtMidRsStnCd",
        "txtMidStnConsOrdr",
        "txtMidStnRunOrdr",
    }
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    try:
        h.client.reserve_merge(train(), merge_rows(standing))
        assert len(h.seen) == 1  # no hidden first hold/cancellation/inquiry
    finally:
        h.close()


@pytest.mark.parametrize("settle_mileage", [False, True])
def test_refund_sends_the_refund_screen_form(settle_mileage: bool) -> None:
    """RefundTicketViewModel$refundTicket$1.smali:854-868,1132-1180: commission echo, first train, location."""
    commission = RefundCommissionResponse(
        str_result="SUCC",
        ticket_return_times_division_code="SYNTH-TIMES",
        usable_mileage="400",
        refund_fee="00000000000400",
    )
    expected = refund_form(
        h_mlg_stl="Y" if settle_mileage else "N",
        tk_ret_tms_dv_cd="SYNTH-TIMES",
        trnNo="90001",
        latitude="0.0",
        longitude="0.0",
    )
    h = Harness([{**BASE, "stlList": None}], "POST", ("refunds.RefundsRequest",), expected)
    try:
        result = h.client.refund(
            ticket(), settle_mileage=settle_mileage, commission=commission, latitude="0.0", longitude="0.0"
        )
        assert result.settlement_list_is_null is True
        assert result.settlement_method_codes == ()
        assert len(h.seen) == 1  # commission is supplied, never fetched automatically
    finally:
        h.close()


def test_refund_requires_the_commission_lookup() -> None:
    """MyTicketDetailViewModel.java:300-358: both refund screens refund only after a successful commission
    lookup."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(TypeError, match="commission"):
            h.client.refund(ticket())  # type: ignore[call-arg]
        with pytest.raises(KorailProtocolError, match="commission response"):
            payload_module.build_refund_form(KorailConfig(), ticket(), settle_mileage=True)
        assert h.seen == []
    finally:
        h.close()


@pytest.mark.parametrize(
    ("usable", "fee"),
    [(None, "400"), ("399", "400"), ("", "00000000000400"), ("1,000", "400")],
)
def test_refund_pays_the_fee_with_mileage_only_when_the_app_would(usable: Any, fee: Any) -> None:
    """MyTicketDetailViewModel.java:1811-1823: mileage settlement needs the commission lookup and usable
    mileage >= fee; TextHelper.getInteger reads a missing or unparsable number as 0."""
    h = Harness([], "POST", (), {})
    try:
        commission = RefundCommissionResponse(str_result="SUCC", usable_mileage=usable, refund_fee=fee)
        with pytest.raises(KorailProtocolError, match="mileage is below the fee"):
            h.client.refund(ticket(), settle_mileage=True, commission=commission)
        assert h.seen == []
    finally:
        h.close()


@pytest.mark.parametrize("result", ["FAIL", "SYNTH-UNKNOWN", "", None])
def test_refund_rejects_non_succ_commission_before_http(result: Any) -> None:
    """RefundTicketViewModel$executeRefundCommission$2.smali:1045-1086 uses isSuccess; strict SUCC is retained money protection, not exact app equivalence."""
    commission_raw = {"strResult": result, "synthetic": "commission"}
    h = Harness([], "POST", (), {})
    try:
        commission = RefundCommissionResponse(str_result=result, raw=commission_raw)
        with pytest.raises(KorailProtocolError) as caught:
            h.client.refund(ticket(), commission=commission)
        assert caught.value.raw == commission_raw
        assert h.seen == []
    finally:
        h.close()


@pytest.mark.parametrize(
    "changes",
    [
        {"card_password": ""},
        {"card_password": "0"},
        {"card_password": "000"},
        {"birthday": "00000"},
        {"birthday": "0000000"},
        {"card_type": "S", "birthday": "000000"},
        {"card_expire": "9900"},
        {"card_expire": "9913"},
        {"card_expire": "2608"},
        {"card_expire": "202609"},
        {"card_expire": "AB12"},
        {"card_number": ""},
        {"card_number": "0000-0000"},
        {"card_number": "0" * 12},
        {"card_number": "0" * 17},
        {"card_password": "ab"},
        {"birthday": "abcdef"},
        {"installment": ""},
        {"installment": None},
        {"installment": 3},
        {"installment": "xyz"},
        {"installment": "123"},
    ],
)
def test_card_input_rejected_before_http(changes: dict[str, Any]) -> None:
    """PayViewModel.smali:53511-53710,53727-53863: password 2, auth 6/10, month/current yyyyMM."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError):
            h.client.pay_with_card(hold(), card(**changes))
        assert not h.seen
    finally:
        h.close()


@pytest.mark.parametrize("type_,auth", [("J", "000000"), ("S", "0000000000")])
def test_card_current_month_allowed_and_auth_type(type_: str, auth: str) -> None:
    """PayViewModel.java:16219-16243: expiration month is inclusive, auth length follows personal/company choice."""
    h = Harness(
        [BASE],
        "POST",
        ("payment.ReservationPayment",),
        payment_form(hidAthnDvCd1=type_, hidAthnVal1=auth, hidCrdVlidTrm1="2609"),
    )
    try:
        h.client.pay_with_card(hold(), card(card_type=type_, birthday=auth, card_expire="2609"))
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize(
    "changes",
    [
        {"pnr_no": ""},
        {"window_no": None},
        {"received_amount": None},
        {"received_amount": "-1"},
        {"str_result": "FAIL"},
    ],
)
def test_payment_identifiers_and_money_required_before_http(changes: dict[str, Any]) -> None:
    """PayViewModel.java:6680-6684; never substitute h_tot_prc for unknown received amount."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError):
            h.client.pay_with_card(hold(**changes), card())
        assert not h.seen
    finally:
        h.close()


@pytest.mark.parametrize("damage", ["mismatch", "journey-shape", "seat-shape", "pnr-shape"])
def test_real_hold_parse_failure_keeps_committed_identifiers(damage: str) -> None:
    """ReservationOut.java fields + retained library money consistency policy; no retry after server returns a PNR."""
    raw = hold_raw()
    if damage == "mismatch":
        raw["h_tot_rcvd_amt"] = "1201"
    elif damage == "journey-shape":
        raw["jrny_infos"] = []
    elif damage == "seat-shape":
        raw["jrny_infos"]["jrny_info"][0]["seat_infos"] = []
    else:
        raw["h_pnr_no"] = {"synthetic": "bad shape"}
    h = Harness([raw], "POST", ("certification.TicketReservation",), reservation_form())
    try:
        with pytest.raises(KorailProtocolError) as caught:
            h.client.reserve(train())
        assert caught.value.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize(
    "variant,expected",
    [("padded", "1200"), ("no-seats", "1200"), ("incomplete-seat", None), ("blank-zero", "1200")],
)
def test_received_amount_never_becomes_partial_sum(variant: str, expected: str | None) -> None:
    raw = hold_raw()
    if variant == "no-seats":
        raw.pop("jrny_infos")
    elif variant == "incomplete-seat":
        raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"][1].pop("h_rcvd_amt")
    elif variant == "blank-zero":
        raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"].append(
            {"h_seat_no": "", "h_rcvd_amt": "0"}
        )
    h = Harness([raw], "POST", ("certification.TicketReservation",), reservation_form())
    try:
        response = h.client.reserve(train())
        assert response.received_amount == expected
        assert response.raw == raw
    finally:
        h.close()


def test_station_actual_parse_failure_retains_full_raw() -> None:
    case = next(c for c in CASES if c.name == "verify_station_ticket_refund")
    raw = verification_raw()
    raw["orgtkinfo_list"][0]["pnr_no"] = []
    h = Harness([raw], "POST", case.routes, case.form)
    try:
        with pytest.raises(KorailProtocolError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()


def test_station_verification_no_commonout_envelope_and_conversion() -> None:
    """VerifyOnlineRefundsOut.java:29,64; StationTicketRefundResultViewModel.java:151-164."""
    case = next(c for c in CASES if c.name == "verify_station_ticket_refund")
    raw = verification_raw()
    raw.pop("strResult")
    h = Harness([raw, verification_raw()], "POST", case.routes * 2, case.form)
    try:
        result = case.invoke(h.client)
        assert result.str_result is None and result.raw == raw
        verified = case.invoke(h.client)
        request = StationRefundExecutionRequest.from_verification(
            verified, customer_phone="00000000000", customer_name="SYNTH-CUSTOMER"
        )
        assert request == execution_request()
    finally:
        h.close()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_session_expired_no_retry(case: Case) -> None:
    raw = {**BASE, "strResult": "FAIL", "h_msg_cd": "P058"}
    h = Harness([raw], case.method, case.routes[:1], case.form)
    try:
        with pytest.raises(KorailSessionExpiredError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == raw
        assert h.client.session.current is None
        assert len(h.seen) == 1
    finally:
        h.close()


def test_card_decline_is_response_not_success_not_retry() -> None:
    raw = {**payment_raw(), "strResult": "FAIL", "h_msg_cd": "SYNTH-DECLINE"}
    h = Harness([raw], "POST", ("payment.ReservationPayment",), payment_form())
    try:
        result = h.client.pay_with_card(hold(), card())
        assert result.str_result == "FAIL" and result.h_msg_cd == "SYNTH-DECLINE"
        assert len(result.tickets) == 1 and result.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()


def test_all_passenger_rows_and_combination_rules() -> None:
    """Passengers.java:731-766; PassengersBottomSheetKt.java:21124-21185; values not decrypted."""
    passengers = KorailPassengerCounts(1, 1, 1, 1, 1, 1, 1, 1)
    expected = reservation_form()
    expected["txtTotPsgCnt"] = "8"
    for i, (type_, discount) in enumerate(
        [
            ("1", "000"),
            ("1", "P11"),
            ("3", "000"),
            ("3", "321"),
            ("1", "131"),
            ("1", "111"),
            ("1", "112"),
            ("1", "173"),
        ],
        1,
    ):
        expected.update({f"txtCompaCnt{i}": "1", f"txtPsgTpCd{i}": type_, f"txtDiscKndCd{i}": discount})
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    try:
        h.client.reserve(train(), passengers=passengers)
    finally:
        h.close()


@pytest.mark.parametrize(
    "passengers",
    [
        KorailPassengerCounts(adult=0, infant=1),
        KorailPassengerCounts(adult=0, child=1, infant=1),
        KorailPassengerCounts(adult=1, guide_dog=1),
    ],
)
def test_invalid_passenger_combinations_before_http(passengers: KorailPassengerCounts) -> None:
    """PassengersBottomSheetKt.java:21124-21185: infant needs non-child/non-infant; guide dog <= disabled passengers."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError):
            h.client.reserve(train(), passengers=passengers)
        assert not h.seen
    finally:
        h.close()


def test_transfer_seat_and_attribute_indexing() -> None:
    """TicketReservationIn.java:80; TicketReservationInSrcar.java:51; TicketReservationInSrcarTrailing.java:52; TrainSeatMapViewModel.java:2108-2138."""
    expected = reservation_form(transfer=True, job="1103")
    expected.update(
        txtSeatAttCd4="021",
        txtSeatAttCd4_1="028",
        txtSrcarCnt="1",
        txtSrcarNo1="1",
        txtSeatNo1="1A",
        txtSrcarCnt1="1",
        txtSrcarNo1_1="2",
        txtSeatNo1_1="2B",
    )
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    try:
        h.client.reserve_transfer(
            [train(), train(True)],
            job_type=Job.SEAT_DESIGNATED,
            seats=[(KorailSeatAssignment(1, "1A"),), (KorailSeatAssignment(2, "2B"),)],
            seat_attribute_codes=["021", "028"],
        )
    finally:
        h.close()


def test_recalculation_parallel_empty_slots_and_nonmember_options() -> None:
    """NetworkApi.java:583-584; PriceReCalculationIn.java:38-41; PayViewModel.java:6167-6168."""
    expected = recalc_form(
        hiduserYn="N",
        hidCustNo="SYNTH-NONMEMBER",
        txtPsrmClCd1="2",
        txtSeatAttCd2="000",
        txtSeatAttCd4="015",
        txtSeatAttCd5="000",
    )
    h = Harness([hold_raw()], "POST", ("certification.PriceReCalculation",), expected)
    try:
        h.client.recalculate_price(
            recalc_request(
                non_member_no="SYNTH-NONMEMBER",
                cabin_class_code="2",
                seat_attribute_code_2="000",
                seat_attribute_code_4="015",
                seat_attribute_code_5="000",
            )
        )
    finally:
        h.close()


def test_standby_no_sms_omits_phone() -> None:
    """ReservationWaitViewModel.java:520-527: no phone when SMS is not selected."""
    expected = {**COMMON, "txtPnrNo": PNR, "txtPsrmClChgFlg": "N", "txtSmsSndFlg": "N"}
    h = Harness([BASE], "POST", ("reservationWait.ReservationWait",), expected)
    try:
        h.client.confirm_standby_hold(hold(), phone_no="IGNORED-SYNTHETIC")
    finally:
        h.close()


def test_unsupported_maas_has_no_incoming_import() -> None:
    """No runtime/type-checking import of the record-only module from production package files."""
    import korail_mobile_api

    root = Path(korail_mobile_api.__file__).parent
    incoming = []
    for source in root.glob("*.py"):
        if source.name == "_maas_unsupported.py":
            continue
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Import):
                targets = [n.name for n in node.names]
            elif isinstance(node, ast.ImportFrom):
                targets = [node.module or "", *(n.name for n in node.names)]
            else:
                continue
            if any("_maas_unsupported" in target for target in targets):
                incoming.append((source.name, node.lineno))
    assert incoming == []
    for name in ["get_maas_cancel_fee", "check_maas_cart_status", "cancel_unpaid_maas_item"]:
        assert not hasattr(KorailClient, name)


PAYMENT_SCALARS = {
    "reservation_no": "h_rsv_no",
    "settlement_approval_no": "h_stl_cd_apprv_no",
    "total_received_amount": "h_tot_rcvd_amt",
    "settlement_amount": "h_stl_amt",
    "total_settlement_amount": "h_tot_stl_amt",
    "customer_no": "h_cust_no",
    "member_card_no": "h_mb_crd_no",
    "buyer_name": "h_buy_name",
    "publication_start_no": "h_publ_start_no",
    "publication_end_no": "h_publ_end_no",
    "mixed_settlement_division": "h_mix_stl_dv",
    "cancellation_fee": "h_cnc_fee",
    "window_no": "h_wct_no",
    "settlement_count": "h_stl_cnt",
    "discount_card_count": "h_disc_card_cnt",
    "total_price": "h_tot_prc",
    "total_fare": "h_tot_fare",
    "total_discount_amount": "h_tot_disc_amt",
    "adult_count": "h_adult_cnt",
    "child_count": "h_child_cnt",
    "table_seat_count": "h_tbl_seat_cnt",
    "ticket_count": "h_tk_cnt",
    "settlement_type_code": "h_stl_tp_cd",
    "trade_division": "h_trade_gbn",
    "remark": "h_bigo",
    "survey_flag": "h_survey_flg",
    "survey_title": "h_survey_title",
    "survey_text": "h_survey_text",
    "survey_url": "h_survey_url",
    "image_ticket_flag": "h_im_flg",
}
PAYMENT_ROWS = {
    "tickets": (
        "tk_infos",
        "tk_info",
        {
            "ticket_sequence": "h_tk_sqno",
            "sale_date": "h_sale_dt",
            "sale_sequence": "h_sale_sqno",
            "return_password": "h_tk_ret_pwd",
            "return_no": "h_tk_ret_no",
            "recipient_name": "h_take_name",
            "discount_card_no": "h_disc_card_no",
            "ticket_price": "h_tk_prc",
            "ticket_fare": "h_tk_fare",
            "bz5_fare_discount_amount": "h_bz5_fare_disc_amt",
            "bz6_fare_discount_amount": "h_bz6_fare_disc_amt",
            "total_discount_amount": "h_tot_disc_amt",
            "total_received_amount": "h_tot_rcvd_amt",
            "standard_seat_price_fare": "h_std_seat_prc_fare",
        },
    ),
    "settlements": (
        "stl_infos",
        "stl_info",
        {
            "settlement_sequence": "h_stl_sqno",
            "settlement_type_code": "h_stl_tp_cd",
            "settlement_result": "h_stl_rlt",
            "transaction_division": "h_tr_gubun",
            "card_installment_count": "h_crd_stl_cnt",
            "installment_months": "h_inst_month",
            "settlement_amount": "h_stl_amt",
            "settlement_card_no": "h_stl_crd_no",
            "card_company_code": "h_crd_corp_cd",
            "card_company_name": "h_crd_corp_nm",
            "approval_date": "h_apv_dt",
            "approval_time": "h_apv_tm",
            "approval_no": "h_apv_no",
            "point_division": "h_xpoint_dv",
            "point_no": "h_xpoint_no",
            "point_approval_no": "h_xpoint_apv_no",
            "remnant_amount": "h_remnant_amt",
            "remote_point": "h_rmt_point",
        },
    ),
    "table_seats": (
        "tbl_seat_infos",
        "tbl_seat_info",
        {
            "room_class_name_1": "h_psrm_cl_cd_nm1",
            "car_no_1": "h_srcar_no1",
            "seat_no_start_1": "h_tbl_seat_no_sno_1",
            "seat_no_end_1": "h_tbl_seat_no_eno_1",
            "seat_count_1": "h_tbl_seat_cnt_1",
            "group_name_1": "h_sgr_nm_1",
            "room_class_name_2": "h_psrm_cl_cd_nm2",
            "car_no_2": "h_srcar_no2",
            "seat_no_start_2": "h_tbl_seat_no_sno_2",
            "seat_no_end_2": "h_tbl_seat_no_eno_2",
            "seat_count_2": "h_tbl_seat_cnt_2",
            "group_name_2": "h_sgr_nm_2",
        },
    ),
    "coupons": (
        "tk_coupon_info",
        None,
        {
            "certificate_password": "h_cert_pwd",
            "coupon_no": "h_coup_no",
            "management_close_date": "h_fdcert_mg_cls_dt",
            "management_start_date": "h_fdcert_mg_st_dt",
            "ticket_return_no": "h_tk_ret_no",
        },
    ),
}


@pytest.mark.parametrize("mode", ["strings", "integers", "malformed-optionals"])
def test_all_payment_model_fields_and_optional_masks(mode: str) -> None:
    """ReservationPaymentOut.java:84-208 all own fields have defaults; :90 aliases; TkInfo/StlInfo/TblSeatInfo/TkCouponInfo @SerialName."""
    raw = copy.deepcopy(BASE)

    def value(wire: str) -> Any:
        return (
            ("SYNTH-" + wire)
            if mode == "strings"
            else 123
            if mode == "integers"
            else {"synthetic": "malformed optional"}
        )

    raw.update({wire: value(wire) for wire in PAYMENT_SCALARS.values()})
    for parent, child, mapping in PAYMENT_ROWS.values():
        row = {wire: value(wire) for wire in mapping.values()}
        row["unmapped_synthetic"] = "preserved"
        raw[parent] = {child: [row]} if child else [row]
    h = Harness([raw], "POST", ("payment.ReservationPayment",), payment_form())
    try:
        result = h.client.pay_with_card(hold(), card())
        for attr, wire in PAYMENT_SCALARS.items():
            expected = "SYNTH-" + wire if mode == "strings" else "123" if mode == "integers" else None
            assert getattr(result, attr) == expected
        for collection, (parent, child, mapping) in PAYMENT_ROWS.items():
            parsed = getattr(result, collection)[0]
            source = raw[parent][child][0] if child else raw[parent][0]
            assert parsed.raw == source
            for attr, wire in mapping.items():
                expected = "SYNTH-" + wire if mode == "strings" else "123" if mode == "integers" else None
                assert getattr(parsed, attr) == expected
        assert result.raw == raw
    finally:
        h.close()


def test_standby_initial_form_is_not_standing_reservation() -> None:
    """TrainScheduleViewModel.java:2870-2874; retained 2026-09-16 observation separates WAIT from STAND."""
    expected = reservation_form(job="1102", stnd="N")
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    try:
        h.client.reserve(
            train(general_reservation_code="13", standing_reservation_code="11"), job_type=Job.STANDBY
        )
    finally:
        h.close()


class SequenceHarness(Harness):
    """Harness whose requests may differ: each exchange is (route, expected form, response)."""

    def __init__(self, exchanges: list[tuple[str, dict[str, Any], Any]]) -> None:
        super().__init__([], "POST", (), {})
        self.client.close()
        self.seen = []

        def handler(request: httpx.Request) -> httpx.Response:
            i = len(self.seen)
            self.seen.append(request)
            assert i < len(exchanges), "duplicate/unexpected transmission"
            route, expected, response = exchanges[i]
            assert request.url.path == ROOT + route
            actual: dict[str, list[str]] = defaultdict(list)
            for key, value in parse_qsl(request.content.decode(), keep_blank_values=True):
                actual[key].append(value)
            assert dict(actual) == pairs(expected)
            return httpx.Response(200, json=response)

        cfg = self.client.config
        self.client = KorailClient(cfg, transport=httpx.MockTransport(handler))
        self.client.session.current = KorailSession(jsessionid="SYNTH-SESSION", customer_no="SYNTH-CUSTOMER-NO")


RECALC = ("certification.PriceReCalculation", recalc_form(), hold_raw())
CART_FORM = {**COMMON, "hidPnrNo": PNR}


@pytest.mark.parametrize("cart_result", ["SUCC", "FAIL"])
def test_recalculation_can_add_the_pnr_to_the_cart_like_the_app(cart_result: str) -> None:
    """PayViewModel.java:14428-14436: after a successful recalculation a logged-in app adds the PNR to the cart
    and keeps the recalculated amount even if that fails (executeAddCart only alerts)."""
    cart = {**BASE, "strResult": cart_result, "h_msg_cd": "SYNTH-CART"}
    h = SequenceHarness([RECALC, ("cart.addCartList", CART_FORM, cart)])
    try:
        result = h.client.recalculate_price(recalc_request(), add_to_cart=True)
        assert result.received_amount == "1200"
        assert result.cart_addition is not None
        assert (result.cart_addition.str_result, result.cart_addition.h_msg_cd) == (cart_result, "SYNTH-CART")
        assert len(h.seen) == 2
    finally:
        h.close()


def test_recalculation_adds_nothing_to_the_cart_by_default_or_after_a_failure() -> None:
    h = SequenceHarness([RECALC])
    try:
        assert h.client.recalculate_price(recalc_request()).cart_addition is None
        assert len(h.seen) == 1
    finally:
        h.close()
    failed = {**hold_raw(), "strResult": "FAIL", "h_msg_cd": "ERR930202", "h_msg_txt": "SYNTH"}
    h = SequenceHarness([("certification.PriceReCalculation", recalc_form(), failed)])
    try:
        with pytest.raises(KorailApiError):
            h.client.recalculate_price(recalc_request(), add_to_cart=True)
        assert len(h.seen) == 1
    finally:
        h.close()


def test_recalculation_rows_come_from_the_first_journey_seats_like_the_app() -> None:
    """PayViewModel.java:5518,16856-16863: one row per first-journey seat copying type, cabin and current
    discount, dcnt_reld_no as hidDscpNo; :17469 refuses when the counts differ."""

    def seats(*rows: tuple[str, str, str, str]) -> dict[str, Any]:
        keys = ("h_psg_tp_cd", "h_psrm_cl_cd", "h_dcnt_knd_cd1", "dcnt_reld_no")
        return {"seat_infos": {"seat_info": [dict(zip(keys, row, strict=True)) for row in rows]}}

    journeys = (
        ReservationJourney(raw=seats(("1", "1", "000", ""), ("3", "2", "SYNTH-OLD", "SYNTH-CERT"))),
        ReservationJourney(raw=seats(("9", "9", "SYNTH-SECOND-LEG", ""))),
    )
    held = hold(journeys=journeys)
    assert PriceRecalculationRequest.for_hold(held, ["", "SYNTH-NEW"]) == PriceRecalculationRequest(
        PNR,
        (
            PriceRecalculationRow("1", "1", "000", "", ""),
            PriceRecalculationRow("3", "2", "SYNTH-OLD", "SYNTH-NEW", "SYNTH-CERT"),
        ),
    )
    with pytest.raises(KorailProtocolError, match="one requested code per seat"):
        PriceRecalculationRequest.for_hold(held, ["SYNTH-NEW"])
    with pytest.raises(KorailProtocolError, match="sequence"):
        PriceRecalculationRequest.for_hold(held, "SYNTH-NEW")
    with pytest.raises(KorailProtocolError, match="first-journey seat rows"):
        PriceRecalculationRequest.for_hold(hold(), ["SYNTH-NEW"])
    with pytest.raises(KorailProtocolError, match="successful hold"):
        PriceRecalculationRequest.for_hold(hold(journeys=journeys, str_result="FAIL"), ["", "SYNTH-NEW"])


@pytest.mark.parametrize(
    "value,expected", [(1, "1"), (True, None), ({"code": "1"}, None), (["1"], None), (1.5, None)]
)
def test_recalculation_rows_read_only_strings_and_json_integers(value: Any, expected: str | None) -> None:
    """ReservationOutSeatInfo.java:80-109: String getters; a JSON integer is its string, anything else is
    refused."""
    seat = {"h_psg_tp_cd": value, "h_psrm_cl_cd": "1", "h_dcnt_knd_cd1": "000", "dcnt_reld_no": None}
    held = hold(journeys=(ReservationJourney(raw={"seat_infos": {"seat_info": [seat]}}),))
    if expected is None:
        with pytest.raises(KorailProtocolError, match="h_psg_tp_cd"):
            PriceRecalculationRequest.for_hold(held, ["SYNTH-NEW"])
    else:
        request = PriceRecalculationRequest.for_hold(held, ["SYNTH-NEW"])
        assert request.rows == (PriceRecalculationRow(expected, "1", "000", "SYNTH-NEW", ""),)


def test_recalculation_form_keeps_the_retrofit_field_order() -> None:
    """NetworkApi.java:584; RequestFactory.java:89-101: the FieldMap, including the four scalars, comes first
    and the six @Field lists follow in declaration order."""
    h = Harness([hold_raw()], "POST", ("certification.PriceReCalculation",), recalc_form(txtPsrmClCd1="2"))
    try:
        h.client.recalculate_price(recalc_request(cabin_class_code="2"))
        keys = [key for key, _ in parse_qsl(h.seen[0].content.decode(), keep_blank_values=True)]
    finally:
        h.close()
    lists = ("psg_tp_dv_cd", "psrm_cl_cd", "dcnt_knd_cd1", "hidDscpNo", "hidDcntKndCd", "hidFmlyNo")
    assert keys[-12:] == [key for key in lists for _ in range(2)]
    assert "txtPsrmClCd1" in keys[:-12]


APP_HEAD = "Device Version Key lang txtMenuId txtJobId hidFreeFlg txtStndFlg txtTotPsgCnt".split()
APP_SEAT_ATTRIBUTES = "txtSeatAttCd1 txtSeatAttCd2 txtSeatAttCd3 txtSeatAttCd4 txtSeatAttCd5".split()
APP_ADULT = "txtCompaCnt1 txtPsgTpCd1 txtDiscKndCd1".split()
APP_JOURNEY = (
    "txtJrnyTpCd txtJrnySqno txtTrnNo txtTrnClsfCd txtTrnGpCd txtRunDt txtDptDt txtDptTm txtDptRsStnCd "
    "txtDptStnConsOrdr txtDptStnRunOrdr txtArvRsStnCd txtArvStnConsOrdr txtArvStnRunOrdr txtChgFlg txtPsrmClCd"
).split()


def app_journey(number: int) -> list[str]:
    return [f"{key}{number}" for key in APP_JOURNEY]


@pytest.mark.parametrize(
    "name,expected",
    [
        ("reserve", [*APP_HEAD, *APP_SEAT_ATTRIBUTES, "txtJrnyCnt", *APP_ADULT, *app_journey(1)]),
        (
            "reserve_transfer",
            [
                *APP_HEAD,
                *APP_SEAT_ATTRIBUTES,
                "txtSeatAttCd4_1",
                "txtJrnyCnt",
                *APP_ADULT,
                *app_journey(1),
                *app_journey(2),
            ],
        ),
        (
            "reserve_merge",
            [
                *APP_HEAD,
                *APP_SEAT_ATTRIBUTES,
                "txtJrnyCnt",
                *APP_ADULT,
                *app_journey(1),
                *"txtMidRsStnCd txtMidStnConsOrdr txtMidStnRunOrdr".split(),
            ],
        ),
        (
            "reserve_with_discount_card",
            [*APP_HEAD, *APP_SEAT_ATTRIBUTES, "txtJrnyCnt", *APP_ADULT, "txtCardNo_1", *app_journey(1)],
        ),
        (
            "refund",
            "txtPnrNo h_orgtk_sale_dt h_orgtk_sale_wct_no h_orgtk_sale_sqno h_orgtk_ret_pwd h_mlg_stl trnNo "
            "pbpAcepTgtFlg Device Version Key lang".split(),
        ),
    ],
)
def test_mutation_forms_follow_the_app_dto_order(name: str, expected: list[str]) -> None:
    """TicketReservationIn.java:80; TicketReservationInPassengerInfo.java:55; TicketReservationInJrny.java:69;
    RefundTicketIn.java:66: the app flattens each DTO in declaration order (NetworkService.java:15335-15392)."""
    case = next(c for c in CASES if c.name == name)
    h = Harness([copy.deepcopy(case.response)], case.method, case.routes[:1], case.form)
    try:
        case.invoke(h.client)
        keys = [key for key, _ in parse_qsl(h.seen[0].content.decode(), keep_blank_values=True)]
    finally:
        h.close()
    assert keys == expected


def test_seat_designated_transfer_and_full_refund_forms_follow_the_app_dto_order() -> None:
    """TicketReservationIn.java:80 (two seat counts before the lists, trailing seats last);
    RefundTicketIn.java:66 (tk_ret_tms_dv_cd, trnNo, pbpAcepTgtFlg, latitude, longitude, then the common
    fields)."""
    config = KorailConfig(base_url="https://offline.invalid", lang=COMMON["lang"])
    form = payload_module.build_transfer_reservation_form(
        config,
        [train(), train(True)],
        job_type=Job.SEAT_DESIGNATED,
        seats=((KorailSeatAssignment(3, "SYNTH-5A"),), (KorailSeatAssignment(4, "SYNTH-6B"),)),
    )
    assert list(form) == [
        *APP_HEAD[:6],
        "txtGdNo",
        *APP_HEAD[6:],
        *APP_SEAT_ATTRIBUTES,
        *"txtSeatAttCd4_1 txtJrnyCnt txtSrcarCnt txtSrcarCnt1".split(),
        *APP_ADULT,
        *app_journey(1),
        *app_journey(2),
        *"txtSrcarNo1 txtSeatNo1 txtSrcarNo1_1 txtSeatNo1_1".split(),
    ]
    commission = RefundCommissionResponse(str_result="SUCC", ticket_return_times_division_code="SYNTH-TMS")
    refund = payload_module.build_refund_form(
        config, ticket(), commission=commission, latitude="37.5", longitude="127.0"
    )
    assert list(refund) == (
        "txtPnrNo h_orgtk_sale_dt h_orgtk_sale_wct_no h_orgtk_sale_sqno h_orgtk_ret_pwd h_mlg_stl "
        "tk_ret_tms_dv_cd "
        "trnNo pbpAcepTgtFlg latitude longitude Device Version Key lang".split()
    )


def test_retrieval_sends_the_pair_after_the_count_and_needs_a_journey() -> None:
    """NetworkApi.java:642-644: FieldMap (common, pbpCnt) then @Field pbpRsvNo, pnrNo;
    DeliveredTicketViewModel.java:283."""
    case = next(c for c in CASES if c.name == "retrieve_delivered_ticket")
    h = Harness([case.response], case.method, case.routes, case.form)
    try:
        case.invoke(h.client)
        keys = [key for key, _ in parse_qsl(h.seen[0].content.decode(), keep_blank_values=True)]
        assert keys[-3:] == ["pbpCnt", "pbpRsvNo", "pnrNo"]
        with pytest.raises(KorailProtocolError, match="first journey"):
            h.client.retrieve_delivered_ticket(replace(DELIVERED_TICKET, journeys=()))
        with pytest.raises(KorailProtocolError):
            h.client.register_self_checkin(CHECKIN_DETAIL, object())  # type: ignore[arg-type]
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize(
    "name,response",
    [
        ("retrieve_delivered_ticket", BASE),
        ("retrieve_delivered_ticket", {**BASE, "prsList": [{}]}),
        ("register_self_checkin", BASE),
    ],
)
def test_checkin_and_retrieval_required_response_keys(name: str, response: dict[str, Any]) -> None:
    """RetrieveTicketOut.java:54-59, Prs.java:46-50, SelfCheckInRegisterOut.java:47-52: required keys; the
    whole response
    stays on .raw and nothing is re-sent."""
    case = next(c for c in CASES if c.name == name)
    h = Harness([response], case.method, case.routes, case.form)
    try:
        with pytest.raises(KorailProtocolError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == response and len(h.seen) == 1
    finally:
        h.close()


def test_mutation_parser_keeps_the_whole_response_when_called_directly() -> None:
    """RefundTicketOut.java:48-53; StlList.java:46-55: a bad settlement row fails with the whole response on
    .raw and the row on .parser_raw, directly and through the client."""
    row = {"stl_mns_cd": True}
    raw = {**BASE, "stlList": [row]}
    with pytest.raises(KorailProtocolError) as caught:
        parse_refund_ticket_response(raw)
    assert caught.value.raw is raw and caught.value.parser_raw is row
    h = Harness([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    try:
        with pytest.raises(KorailProtocolError) as caught:
            h.client.refund(ticket(), commission=COMMISSION)
        assert caught.value.raw == raw and caught.value.parser_raw == row
    finally:
        h.close()


def test_standby_holds_are_not_payable() -> None:
    """TrainScheduleViewModel.java:5096-5101; ReservationWaitViewModel.java:1155-1160: WAIT saves options, never
    pays."""
    row = train(general_reservation_code="13", standing_reservation_code="11")
    expected = reservation_form(job="1102")
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    try:
        result = h.client.reserve(row, job_type=Job.STANDBY)
        assert result.payable is False
        with pytest.raises(KorailProtocolError, match="standby"):
            h.client.pay_with_card(result, card())
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize("amount", ["0", "00000000000"])
def test_zero_amount_hold_is_not_card_paid(amount: str) -> None:
    """PayViewModel.java:15572,18144: the app builds no card request when nothing is owed."""
    h = Harness([], "POST", ("payment.ReservationPayment",), {})
    try:
        with pytest.raises(KorailProtocolError, match="zero-amount"):
            h.client.pay_with_card(hold(received_amount=amount), card())
        assert h.seen == []
    finally:
        h.close()


def test_transfer_standby_hold_is_not_payable() -> None:
    expected = reservation_form(transfer=True, job="1102")
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    try:
        assert h.client.reserve_transfer([train(), train(True)], job_type=Job.STANDBY).payable is False
    finally:
        h.close()


def test_merge_first_and_follow_up_holds_stay_payable() -> None:
    """ReservationMergeViewModel.java:2094-2107: the merge screen's pay button pays the held reservation."""
    first = Harness(
        [hold_raw()], "POST", ("certification.TicketReservation",), reservation_form(job="1202", stnd="N")
    )
    try:
        assert first.client.reserve(train(), job_type=Job.MERGE_STANDING).payable is True
    finally:
        first.close()
    merged = {
        **reservation_form(job="1202"),
        "txtStndFlg": "Y",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    follow_up = Harness([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    try:
        assert follow_up.client.reserve_merge(train(), merge_rows()).payable is True
    finally:
        follow_up.close()
    assert hold().payable is True


def test_standing_only_row_is_not_booked_as_immediate() -> None:
    """TrainScheduleOutTrainInfo.java:2810-2885: STAND is decided only after protected suspend/wait/merge
    checks, so 13/11 alone cannot tell whether the app would send a standing-only hold."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError, match="available general seat"):
            h.client.reserve(train(general_reservation_code="13", standing_reservation_code="11"))
        assert not h.seen
    finally:
        h.close()


@pytest.mark.parametrize(
    "legs",
    [
        pytest.param([train(True), train()], id="reversed"),
        pytest.param([train(), train()], id="same-train"),
        pytest.param(
            [train(arrival_date="20991230"), train(True, departure_time="110000")], id="departs-before-arrival"
        ),
    ],
)
def test_transfer_legs_must_be_distinct_and_in_boarding_order(legs: list[TrainSummary]) -> None:
    """TrainScheduleViewModel.java:2952-2968 builds the form from one transfer search pair only."""
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError, match="different trains|boarding order"):
            h.client.reserve_transfer(legs)
        assert not h.seen
    finally:
        h.close()


def test_merge_rows_with_the_same_run_date_are_accepted() -> None:
    rows = tuple(TrainScheduleItem(**{**row.__dict__, "run_date": "20991230"}) for row in merge_rows())
    merged = {
        **reservation_form(job="1202"),
        "txtStndFlg": "Y",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    h = Harness([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    try:
        h.client.reserve_merge(train(), rows)
        assert len(h.seen) == 1
    finally:
        h.close()


def test_mutation_parsers_read_integer_envelope_fields_as_strings() -> None:
    from korail_mobile_api.mutation_parsers import parse_reservation_hold_response

    raw = {**hold_raw(), "h_msg_cd": 0, "h_msg_txt": 7}
    result = parse_reservation_hold_response(raw)
    assert (result.h_msg_cd, result.h_msg_txt) == ("0", "7")


def test_merge_rows_from_another_run_date_are_rejected() -> None:
    first, second = merge_rows()
    rows = (first, TrainScheduleItem(**{**second.__dict__, "run_date": "20991231"}))
    h = Harness([], "POST", (), {})
    try:
        with pytest.raises(KorailProtocolError, match="run_date"):
            h.client.reserve_merge(train(), rows)
        assert not h.seen
    finally:
        h.close()


@pytest.mark.parametrize(
    "case",
    [
        c
        for c in CASES
        if c.name in {"reserve", "reserve_transfer", "reserve_with_discount_card", "pay_with_card"}
    ],
    ids=lambda c: c.name,
)
def test_queue_handoff_one_operation_not_retry(case: Case) -> None:
    """Client gate boundary only. NetFunnel SDK protocol belongs to session 5 and checks/netfunnel_offline.py."""
    calls: list[str] = []

    class Queue:
        def run(self, gate: str, send: Callable[[], Any]) -> Any:
            calls.append(gate)
            return send()

        def close(self) -> None:
            pass

    h = Harness([case.response], case.method, case.routes, case.form)
    h.client.netfunnel = Queue()
    try:
        case.invoke(h.client)
        assert calls == ["pay" if case.name == "pay_with_card" else "reserve"]
        assert len(h.seen) == 1
    finally:
        h.close()


def test_numeric_zero_identifiers_are_echoed_without_repadding() -> None:
    """PayViewModel.java:6680-6684; 2026-09-21 numeric-String compatibility is separate from padding recovery."""
    expected = payment_form(hidTmpJobSqno1="0", hidTmpJobSqno2="42", hidRsvChgNo="0")
    h = Harness([BASE], "POST", ("payment.ReservationPayment",), expected)
    try:
        h.client.pay_with_card(
            hold(
                temporary_job_sequence_1="0",
                temporary_job_sequence_2="42",
                journeys=(ReservationJourney(journey_sequence="1", reservation_change_no="0"),),
            ),
            card(),
        )
    finally:
        h.close()


def test_successful_hold_does_not_mean_successful_payment() -> None:
    """ReservationPaymentOut.java:90: top-level result and per-settlement result stay independent."""
    raw = {**payment_raw(), "strResult": "SUCC"}
    h = Harness([raw], "POST", ("payment.ReservationPayment",), payment_form())
    try:
        result = h.client.pay_with_card(hold(), card())
        assert result.str_result == "SUCC"
        assert result.settlements[0].settlement_result == "SYNTH-DECLINED-LEG"
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_invalid_envelope_keeps_entire_response_before_domain_parser(case: Case) -> None:
    """Shared transport must preserve the returned PNR even if strResult has an invalid type; no retry."""
    raw = {**case.response, "strResult": ["SYNTH-INVALID-TYPE"], "h_pnr_no": PNR}
    h = Harness([raw], case.method, case.routes[:1], case.form)
    try:
        with pytest.raises(KorailProtocolError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize("payload", [[{"h_pnr_no": PNR}], "synthetic-not-an-object", 123, None])
def test_non_object_json_keeps_raw(payload: Any) -> None:
    h = Harness([payload], "POST", ("certification.TicketReservation",), reservation_form())
    try:
        with pytest.raises(KorailProtocolError) as caught:
            h.client.reserve(train())
        assert caught.value.raw == payload
        assert len(h.seen) == 1
    finally:
        h.close()


def test_invalid_json_retains_original_body_without_retry() -> None:
    raw_text = '{"synthetic_partial_pnr":"SYNTH-PNR-ONLY",'
    count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal count
        count += 1
        return httpx.Response(200, text=raw_text)

    config = KorailConfig(
        base_url="https://offline.invalid",
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_provider=lambda ctx: "SYNTHETIC-NOT-A-TOKEN"),
    )
    c = KorailClient(config, transport=httpx.MockTransport(handler))
    c.session.current = KorailSession(jsessionid="SYNTH-SESSION")
    try:
        with pytest.raises(KorailProtocolError) as caught:
            c.reserve(train())
        assert caught.value.raw == raw_text.encode("utf-8")
        assert count == 1
    finally:
        c.close()


@pytest.mark.parametrize(
    "shape",
    [
        "missing",
        {},
        "bad-list",
        [None],
        [1],
        [[]],
        [{}],
        [{"stl_mns_cd": None}],
        [{"stl_mns_cd": []}],
        [{"stl_mns_cd": {}}],
        [{"stl_mns_cd": True}],
    ],
)
def test_refund_required_settlement_mask_does_not_silently_drop_data(shape: Any) -> None:
    """RefundTicketOut.java:48-53 required mask 0x8; StlList.java:46-55 required mask 0x1/non-null String."""
    raw = copy.deepcopy(BASE)
    if shape != "missing":
        raw["stlList"] = shape
    h = Harness([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    try:
        with pytest.raises(KorailProtocolError) as caught:
            h.client.refund(ticket(), commission=COMMISSION)
        assert caught.value.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()


@pytest.mark.parametrize(
    "rows,codes,is_null",
    [
        (None, (), True),
        ([], (), False),
        ([{"stl_mns_cd": ""}], ("",), False),
        ([{"stl_mns_cd": 2}], ("2",), False),
    ],
)
def test_refund_required_but_nullable_list_and_integer_string_compatibility(
    rows: Any, codes: tuple[str, ...], is_null: bool
) -> None:
    """RefundTicketOut.java:48-58 distinguishes missing from explicit null; StlList.java:46-55; 2026-09-21 String/int policy."""
    raw = {**BASE, "stlList": rows}
    h = Harness([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    try:
        result = h.client.refund(ticket(), commission=COMMISSION)
        assert result.settlement_method_codes == codes
        assert result.settlement_list_is_null is is_null
        assert result.raw == raw
    finally:
        h.close()


def test_actual_first_and_merge_requests_differ_only_at_four_fields() -> None:
    """ReservationMergeViewModel.smali:7671-7774; original request copied, not two new short journeys."""
    first_expected = reservation_form(job="1202")
    h = Harness([hold_raw(), hold_raw()], "POST", ("certification.TicketReservation",) * 2, first_expected)
    try:
        h.client.reserve(train(), job_type=Job.MERGE_STANDING)
        h.expected.update(txtStndFlg="Y", txtMidRsStnCd="9099", txtMidStnConsOrdr="004", txtMidStnRunOrdr="003")
        h.client.reserve_merge(train(), merge_rows())
        actual_first = dict(parse_qsl(h.seen[0].content.decode(), keep_blank_values=True))
        actual_second = dict(parse_qsl(h.seen[1].content.decode(), keep_blank_values=True))
        changed = {
            k for k in actual_first.keys() | actual_second.keys() if actual_first.get(k) != actual_second.get(k)
        }
        assert changed == {"txtStndFlg", "txtMidRsStnCd", "txtMidStnConsOrdr", "txtMidStnRunOrdr"}
    finally:
        h.close()


def test_hold_response_is_actual_source_of_payment_identifiers_and_amount() -> None:
    """PayViewModel.java:6680-6684: reservation response, not initial request or ticket face price, supplies payment identifiers."""
    h = Harness(
        [hold_raw(), payment_raw()],
        "POST",
        ("certification.TicketReservation", "payment.ReservationPayment"),
        reservation_form(),
    )
    try:
        response = h.client.reserve(train())
        assert response.temporary_job_sequence_1 == "001234"
        assert response.temporary_job_sequence_2 == "005678"
        assert response.journeys[0].reservation_change_no == "009"
        h.expected.clear()
        h.expected.update(payment_form())
        result = h.client.pay_with_card(response, card())
        assert result.total_received_amount == "1200"
        assert len(h.seen) == 2
    finally:
        h.close()


def test_cancel_first_stage_common_envelope_failures_stop() -> None:
    """First-stage handling is not literally FAIL-only: a missing required strResult is transport policy.
    A success envelope carrying WRC000288 is not a failure (CommonOut.java:426-463)."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    raw = copy.deepcopy(BASE)
    raw.pop("strResult")
    h = Harness([raw], "POST", case.routes[:1], case.form)
    try:
        with pytest.raises(KorailApiError) as caught:
            case.invoke(h.client)
        assert caught.value.raw == raw
        assert len(h.seen) == 1
    finally:
        h.close()
