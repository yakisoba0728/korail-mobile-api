"""Offline domain contracts use only synthetic responses and block real network access."""

from __future__ import annotations

import copy
import logging
from contextlib import closing
from dataclasses import dataclass, replace
from typing import Any, Callable
from urllib.parse import parse_qs, parse_qsl

import httpx
import pytest

import korail_mobile_api._domains.payments.forms as payload_module
import korail_mobile_api.client as client_module
from korail_mobile_api import (
    CardPayment,
    CartAddRequest,
    DynapathConfig,
    HoldReference,
    KorailPassengerCounts,
    KorailSeatAssignment,
    KorailSession,
    OriginalTicketReference,
    PaidTicket,
    PbpAcceptanceJourney,
    PbpAcceptanceTicket,
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ProductDetailResponse,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    ReservationHoldResponse,
    ReservationJourney,
    SelfCheckInSeat,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
    TrainScheduleItem,
    TrainSummary,
)
from korail_mobile_api._domains.payments.parsers import parse_refund_ticket_response
from korail_mobile_api._domains.reservations.forms import build_transfer_reservation_form
from korail_mobile_api._domains.reservations.parsers import parse_reservation_hold_response
from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.constants import KorailReservationJobType as Job
from korail_mobile_api.constants import KorailSeatClass as Cabin
from korail_mobile_api.errors import (
    KorailApiError,
    KorailInvalidInputError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.facade import ReservationResource

COMMON = {
    "Device": "SYNTH-ANDROID",
    "Version": "SYNTH-706",
    "AppVersion": "7.0.8",
    "Key": "SYNTH-KEY",
    "lang": "SYNTH-LANG",
}
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


@pytest.mark.parametrize("card_type, birthday", [("J", "000101"), ("S", "0000000000")])
def test_card_representations_hide_fields_without_changing_payment(
    caplog: pytest.LogCaptureFixture, card_type: str, birthday: str
) -> None:
    payment = card(card_type=card_type, birthday=birthday)
    logging.getLogger(__name__).warning("card=%r", payment)
    assert repr(payment) == str(payment) == repr(replace(payment)) == "CardPayment()"
    assert repr([payment]) == "[CardPayment()]"
    assert caplog.records[-1].getMessage() == "card=CardPayment()"
    form = payload_module.build_card_payment_form(KorailConfig(), hold(), payment)
    assert form["hidStlCrCrdNo1"] == payment.card_number
    assert form["hidVanPwd1"] == payment.card_password
    assert form["hidCrdVlidTrm1"] == payment.card_expire
    assert form["hidAthnVal1"] == birthday and form["hidAthnDvCd1"] == card_type
    assert replace(payment) == payment


class _UnrenderableCardField:
    def __repr__(self) -> str:
        raise AssertionError("card output must not evaluate malformed field representations")

    def __eq__(self, other: object) -> bool:
        return other == "J"


@pytest.mark.parametrize(
    "field", ["card_number", "card_password", "card_expire", "birthday", "installment", "card_type"]
)
def test_card_rejects_unvalidated_fields_without_evaluating_them(field: str) -> None:
    """Construction validates the format; a non-string value (even one equal to "J") is never rendered."""
    with pytest.raises(KorailInvalidInputError):
        card(**{field: _UnrenderableCardField()})


@pytest.mark.parametrize("field", ["card_number", "card_password", "card_expire", "birthday", "installment"])
def test_card_rejects_malformed_strings_without_echoing_them(field: str) -> None:
    with pytest.raises(KorailInvalidInputError) as caught:
        card(**{field: "SYNTHETIC-PRIVATE\nVALUE"})
    assert "SYNTHETIC-PRIVATE" not in str(caught.value) and "SYNTHETIC-PRIVATE" not in repr(caught.value)


def ticket() -> PaidTicket:
    return PaidTicket(
        PNR,
        "20991230",
        "SYNTH-ORIGINAL-WINDOW",
        "SYNTH-ORIGINAL-SEQ",
        "SYNTH-RETURN-PWD",
        "90001",
        "SYNTH-PBP",
        return_sale_date="1229",
    )


def bound_commission(**changes: Any) -> RefundCommissionResponse:
    """A real lookup under a separate MockTransport keeps mutation request counts isolated.

    Same-client lookup/mutation integration and mismatches are covered in test_refund_binding.py.
    """
    config = KorailConfig(base_url="https://offline.invalid", netfunnel_enabled=False, disable_dynapath=True)
    with closing(
        KorailClient(
            config, transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"strResult": "SUCC"}))
        )
    ) as client:
        client.session.current = KorailSession(jsessionid="SYNTH-SESSION")
        result = client.get_refund_fee(
            OriginalTicketReference("SYNTH-ORIGINAL-WINDOW", "1229", "SYNTH-ORIGINAL-SEQ", "SYNTH-RETURN-PWD")
        )
    return replace(result, **changes)


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
    """TicketReservationIn.java:80; TicketReservationInJrny.java:69; TrainScheduleViewModel.java:2932,3004.

    TicketReservationIn.java:96-100: unset seat attributes have protected defaults, so 000 is the observed value.
    TrainScheduleOutTrainInfo.java:1631,3683: the app echoes txtJrnySqno; 001/002 are observed values.
    NetworkService.java:15350,15366: arrays are flattened with 1-based indexes."""
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
    """PayViewModel.java:6680-6684 (hidTmpJobSqno1/2 echo :6682-6683, hidRsvChgNo :6684);
    PaymentMethodHelper.java:110-130 (protected defaults unresolved); the numbered suffix 1 follows
    PaymentMethod.java:672-694 and ReservationPaymentInStlInfo.java:33. INS_0's value is protected
    (PaymentDefine.java:152-164,185-189,207-210; default choice InstallmentViewModel.java:55,94-96).
    hiduserYn splits on login (PayViewModel.java:6600-6604; FPayViewModel.java:772-778); both constants are
    protected."""
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
    """MyTicketDetailViewModel.java:1521 fills only these fields (the detail's pbpAcepTgtFlg; the foreign route
    uses a protected constant, FTicketDetailViewModel.java:634); the protected ctlDvCd is omitted, not guessed
    (MyTicketDetailViewModel.java:1811-1858; RefundTicketIn.java:66)."""
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
    """NetworkApi.java:582-584: six repeated unnumbered lists preserve empty positions (a None element would be
    dropped, ParameterHandler.java:18-31, and misalign the lists); PayViewModel.java:6142-6171,
    PriceReCalculationIn.java:31-41. txtJobId's job id is protected (ReservationJobId.java:20,42-45)."""
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
    return [
        # ReservationOut.java:49,400-409,444-448: deadline date/time, h_tot_fare (meaning unknown) and the displayed
        # h_tot_prc; PayViewModel.java:11297-11307,11314-11318 sums h_tot_rcvd_amt and shows h_tot_prc.
        # ReservationOutJrnyInfo.java:86,305,361: h_arv_dt and h_jrny_sqno, absent from observed reserve responses.
        # TrainScheduleViewModel.java:2914-2930,6773-6781: seat attribute is explicit -> train row -> default, and a
        # STANDBY hold is never card-paid.
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
        # TrainScheduleViewModel.java:2937-3004: the transfer overload; both legs pass isTransfer=true (:2968) and
        # TrainScheduleOutTrainInfo.java:3674-3683 picks the journey type. TicketReservationIn.java:34-37,80: one PNR
        # carries both legs in boarding order.
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
        # ReservationMergeViewModel.java:1352,1556: the follow-up hold may be a separate PNR; the caller cancels the
        # first hold.
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
        # NetworkApi.java:752-753: the general reservation route; TicketReservationInPassengerInfo.java:55,105: the
        # per-passenger txtCardNo_.
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
        # ReservationWaitApplyUiData.java:85; ReservationWaitViewModel.java:503-513: SMS joins the three phone parts
        # and checks 11 digits. ReservationWaitViewModel.java:68-80: only the existing standby hold's options are saved.
        Case(
            "set_standby_options",
            lambda c: c.set_standby_options(
                hold(), allow_seat_class_change=True, sms_notify=True, phone_no="00000000000"
            ),
            "POST",
            ("reservationWait.ReservationWait",),
            {**COMMON, "txtPnrNo": PNR, "txtPsrmClChgFlg": "Y", "txtSmsSndFlg": "Y", "txtCpNo": "00000000000"},
            BASE,
            None,
            {},
        ),
        # ReservationCancelChkIn.java:29-32,53: four own fields; the journey count is echoed from the response
        # (ReservationWaitViewModel.java:398; MyReservationViewModel.java:1557; PayViewModel.java:4686).
        # MyReservationViewModel.java:1557,1566,1720-1745: check first, then cancel; a failed check does not cancel.
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
        # ProductCancelIn.java:67-70: txtVrRsNo/txtGdSqno both come from get_product_detail
        # (ProductReservationListScreenKt.java:1252-1253, MyTicketDetailViewModel.java:3290). The same GET cancels an
        # unpaid product and refunds a paid one (MyTicketDetailViewModel.java:1183-1192,3271-3291).
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
            lambda c: c.refund(ticket(), commission=bound_commission()),
            "POST",
            ("refunds.RefundsRequest",),
            refund_form(trnNo="90001"),
            {**BASE, "stlList": [{"stl_mns_cd": "02"}, {"stl_mns_cd": "SYNTH-SECOND"}]},
            "parse_refund_ticket_response",
            {"settlement_method_codes": ("02", "SYNTH-SECOND"), "settlement_list_is_null": False},
        ),
        Case(
            "check_station_ticket_refund",
            lambda c: c.check_station_ticket_refund(verification_request()),
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
        # ExecuteOnlineRefundsIn.java:60: the twelve keys in this order.
        Case(
            "refund_station_ticket",
            lambda c: c.refund_station_ticket(execution_request()),
            "POST",
            ("refunds.executeOnlineRefunds",),
            execution_form(),
            {**BASE, "h_ret_dv_cd": "SYNTH-DIV"},
            "parse_station_refund_execution_response",
            {"refund_division_code": "SYNTH-DIV"},
        ),
        # AddCartListIn.java:25-30,79; NetworkApi.java:265-267: only hidPnrNo besides CommonIn.
        # AddCartListOut.java:76; PsgDiscAddInfos.java:81; PsgDiscAddInfo.java:81,85: response keys.
        # NetworkApi.java:266-267; AddCartListIn.java:52; AddCartListOut.java:24-25,76: psgDiscAdd_infos.psgDiscAdd_info
        # is read as discount_additions.
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
        # NetworkApi.java:518-520 (POST despite the name); keys from NCardExtensionIn.java:31-34 property names.
        Case(
            "extend_discount_card",
            lambda c: c.extend_discount_card(
                OriginalTicketReference(
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
        # SelfCheckInInfoViewModel.java:224-225; SelfCheckInRegisterIn.java:59: seat fields from the seat row,
        # jrnySqno and saleDd from the detail. SelfCheckInRegisterOut.java:47-52: msgId required, nullable.
        # Route: NetworkApi.java:682-684.
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
        # SelfCheckInResultViewModel.java:111-112; SelfCheckInCancelIn.java:53: the info fields.
        # SelfCheckInCancelOut.java:50-56: msgId optional. Route: NetworkApi.java:288-290.
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
            "recall_delivered_ticket",
            lambda c: c.recall_delivered_ticket(DELIVERED_TICKET),
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


@pytest.fixture
def mutation_client(scripted_client_factory):
    """Keep independent wire goldens while sharing transport recording and cleanup."""
    config = KorailConfig(
        base_url="https://offline.invalid",
        device=COMMON["Device"],
        version=COMMON["Version"],
        key=COMMON["Key"],
        lang=COMMON["lang"],
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_provider=lambda ctx: "SYNTHETIC-OFFLINE-NOT-A-TOKEN"),
    )
    session = KorailSession(jsessionid="SYNTH-SESSION", customer_no="SYNTH-CUSTOMER-NO")

    def make(responses, method, routes, expected):
        def reply(request):
            i = len(requests) - 1
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
            form = expected[i] if isinstance(expected, list) else expected
            assert parse_qs(encoded, keep_blank_values=True) == pairs(form)
            return responses[i]

        client, requests, _ = scripted_client_factory([reply] * len(responses), config=config, session=session)
        return client, requests

    return make


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_each_public_method_entire_wire_form_and_parse(mutation_client, case: Case) -> None:
    """NetworkApi.java:192-193,266-267,336-337,519-520,583-584,603-604,615-620,631-640,752-753,799-800,811-812."""
    client, requests = mutation_client(
        [copy.deepcopy(case.response) for _ in case.routes], case.method, case.routes, case.form
    )
    result = case.invoke(client)
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
        # Do not collapse partial results into success.
        assert result.settlements[0].raw["h_stl_rlt"] == "SYNTH-DECLINED-LEG"
    if case.name == "check_station_ticket_refund":
        assert result.original_tickets[0].pnr_no == PNR
        assert result.original_tickets[0].original_sale_window_no == "SYNTH-ORIGINAL-WINDOW"
    assert len(requests) == len(case.routes)


PARSED_CASES = [c for c in CASES if c.parser_name is not None]


@pytest.mark.parametrize("case", PARSED_CASES, ids=lambda c: c.name)
@pytest.mark.parametrize("kind", ["protocol", "unexpected"])
def test_parser_failure_retains_whole_response_and_never_retries(
    mutation_client, case: Case, kind: str, monkeypatch: pytest.MonkeyPatch
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
    client, requests = mutation_client([copy.deepcopy(case.response)], case.method, case.routes[:1], case.form)
    with pytest.raises(KorailProtocolError) as caught:
        case.invoke(client)
    assert caught.value.raw == case.response
    if kind == "protocol":
        assert caught.value.parser_raw == partial
    else:
        assert isinstance(caught.value.__cause__, ValueError)
    assert len(requests) == 1
    # 3.0: the response arrived, so the failure is marked as sent; only state-changing calls get the note.
    assert caught.value.request_sent is True
    notes = getattr(caught.value, "__notes__", [])
    assert any("may have processed" in note for note in notes) is (case.name != "check_station_ticket_refund")


@pytest.mark.parametrize(
    "first_result,stops",
    [("FAIL", True), ("SUCC", False), ("SYNTH-UNKNOWN", False), (None, False), ("", False)],
)
def test_cancel_two_stage_non_fail_policy(mutation_client, first_result: Any, stops: bool) -> None:
    """MyReservationViewModel.smali:5589,5707,6284; CommonOut.smali:2493-2560.
    FAIL literal is observed, not decrypted."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    responses = [
        {**BASE, "strResult": first_result, "h_msg_cd": "SYNTH-FIRST"},
        {**BASE, "h_msg_cd": "SYNTH-FINAL"},
    ]
    client, requests = mutation_client(responses, "POST", case.routes, case.form)
    if stops:
        with pytest.raises(KorailApiError) as caught:
            case.invoke(client)
        assert caught.value.raw == responses[0]
        assert len(requests) == 1
    else:
        result = case.invoke(client)
        assert len(requests) == 2
        assert result.h_msg_cd == "SYNTH-FINAL"


def test_cancel_skip_check_and_echo_padding(mutation_client) -> None:
    """ReservationCancelChkIn.java:53; MyReservationViewModel.java:1557,1566."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    expected = {**case.form, "txtJrnyCnt": "0002"}
    client, requests = mutation_client([BASE], "POST", (case.routes[-1],), expected)
    client.cancel_unpaid_hold(hold(journey_count="0002"), check_first=False)
    assert len(requests) == 1


@pytest.mark.parametrize("journeys", [True, False], ids=["first-journey", "fallbacks"])
def test_cancel_by_reference_sends_the_hold_bytes(mutation_client, journeys: bool) -> None:
    """3.0 HoldReference: the hold, hold.reference and HoldReference.from_raw(raw) cancel with one identical form,
    including the 0001/000 fallbacks; from_raw also reads a raw whose hold parse failed (D4)."""
    raw = hold_raw() if journeys else {**hold_raw(), "jrny_infos": None}
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    expected = case.form if journeys else {**case.form, "txtJrnySqno": "0001", "hidRsvChgNo": "000"}
    parsed = parse_reservation_hold_response(raw)
    unparseable = {**raw, "h_wct_no": ["not", "a", "string"]}
    with pytest.raises(KorailProtocolError):
        parse_reservation_hold_response(unparseable)
    assert HoldReference.from_raw(unparseable) == HoldReference.from_raw(raw) == parsed.reference
    sent = []
    for target in (parsed, parsed.reference, HoldReference.from_raw(unparseable)):
        client, requests = mutation_client([BASE], "POST", (case.routes[-1],), expected)
        client.cancel_unpaid_hold(target, check_first=False)
        sent.append(requests[0].content)
    assert sent[0] == sent[1] == sent[2]


def test_hold_reference_needs_a_pnr_and_journey_count() -> None:
    raw = hold_raw()
    for key in ("h_pnr_no", "h_jrny_cnt"):
        with pytest.raises(KorailProtocolError, match="h_pnr_no and h_jrny_cnt") as caught:
            HoldReference.from_raw({**raw, key: None})
        assert caught.value.raw == {**raw, key: None}
    with pytest.raises(KorailInvalidInputError, match="PNR and a journey count"):
        _ = hold(journey_count=None).reference


def test_cancel_second_stage_failure_is_not_retried(mutation_client) -> None:
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    failure = {**BASE, "strResult": "FAIL", "h_msg_cd": "SYNTH-SECOND-FAIL"}
    client, requests = mutation_client([BASE, failure], "POST", case.routes, case.form)
    with pytest.raises(KorailApiError) as caught:
        case.invoke(client)
    assert caught.value.raw == failure
    assert len(requests) == 2


@pytest.mark.parametrize("standing", [False, True])
def test_merge_exact_four_overrides(mutation_client, standing: bool) -> None:
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
    client, requests = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    client.reserve_merge(train(), merge_rows(standing))
    assert len(requests) == 1  # no hidden first hold/cancellation/inquiry


@pytest.mark.parametrize("settle_mileage", [False, True])
def test_refund_sends_the_refund_screen_form(mutation_client, settle_mileage: bool) -> None:
    """RefundTicketViewModel$refundTicket$1.smali:854-868,1132-1180: commission echo, first train, location."""
    commission = bound_commission(
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
    client, requests = mutation_client(
        [{**BASE, "stlList": None}], "POST", ("refunds.RefundsRequest",), expected
    )
    result = client.refund(
        ticket(), settle_mileage=settle_mileage, commission=commission, latitude="0.0", longitude="0.0"
    )
    assert result.settlement_list_is_null is True
    assert result.settlement_method_codes == ()
    assert len(requests) == 1  # commission is supplied, never fetched automatically


def test_refund_requires_the_commission_lookup(mutation_client) -> None:
    """MyTicketDetailViewModel.java:300-358: both refund screens refund only after a successful commission
    lookup."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(TypeError, match="commission"):
        client.refund(ticket())  # type: ignore[call-arg]
    # 빈 값을 명시해도 수수료 조회를 건너뛸 수 없습니다.
    for missing in (None, {"strResult": "SUCC"}):
        with pytest.raises(KorailInvalidInputError, match="get_refund_fee"):
            client.refund(ticket(), commission=missing)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="commission"):
        payload_module.build_refund_form(KorailConfig(), ticket(), settle_mileage=True)  # type: ignore[call-arg]
    with pytest.raises(KorailInvalidInputError, match="get_refund_fee response"):
        payload_module.build_refund_form(KorailConfig(), ticket(), settle_mileage=True, commission=None)  # type: ignore[arg-type]
    assert requests == []


@pytest.mark.parametrize(
    ("usable", "fee"),
    [(None, "400"), ("399", "400"), ("", "00000000000400"), ("1,000", "400")],
)
def test_refund_pays_the_fee_with_mileage_only_when_the_app_would(
    mutation_client, usable: Any, fee: Any
) -> None:
    """MyTicketDetailViewModel.java:1811-1823: mileage settlement needs the commission lookup and usable
    mileage >= fee (the refund screen compares the fee total, RefundTicketViewModel.java:924-942; the protected
    proceed-flag comparison is not reproduced); TextHelper.getInteger reads a missing or unparsable number as 0."""
    client, requests = mutation_client([], "POST", (), {})
    commission = bound_commission(str_result="SUCC", usable_mileage=usable, refund_fee=fee)
    with pytest.raises(KorailProtocolError, match="mileage is below the fee"):
        client.refund(ticket(), settle_mileage=True, commission=commission)
    assert requests == []


@pytest.mark.parametrize("result", ["FAIL", "SYNTH-UNKNOWN", "", None])
def test_refund_rejects_non_succ_commission_before_http(mutation_client, result: Any) -> None:
    """RefundTicketViewModel$executeRefundCommission$2.smali:1045-1086 uses isSuccess; strict SUCC is retained money protection, not exact app equivalence."""
    commission_raw = {"strResult": result, "synthetic": "commission"}
    client, requests = mutation_client([], "POST", (), {})
    commission = RefundCommissionResponse(str_result=result, raw=commission_raw)
    with pytest.raises(KorailProtocolError) as caught:
        client.refund(ticket(), commission=commission)
    assert caught.value.raw == commission_raw
    assert requests == []


_PASSWORD = "first two card password digits"
_AUTH = "authentication value must be 6 or 10 digits"
_EXPIRY = "has expired or has an invalid month"
_EXPIRE_SHAPE = "card_expire must be YYMM digits"
_NUMBER = "card number must be 13 to 16 digits"
_INSTALLMENT = "installment must be one or two digits"


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"card_password": ""}, _PASSWORD),
        ({"card_password": "0"}, _PASSWORD),
        ({"card_password": "000"}, _PASSWORD),
        ({"birthday": "00000"}, _AUTH),
        ({"birthday": "0000000"}, _AUTH),
        ({"card_type": "S", "birthday": "000000"}, _AUTH),
        ({"card_expire": "9900"}, _EXPIRY),
        ({"card_expire": "9913"}, _EXPIRY),
        ({"card_expire": "2608"}, _EXPIRY),
        ({"card_expire": "202609"}, _EXPIRE_SHAPE),
        ({"card_expire": "AB12"}, _EXPIRE_SHAPE),
        ({"card_number": ""}, _NUMBER),
        ({"card_number": "0000-0000"}, _NUMBER),
        ({"card_number": "0" * 12}, _NUMBER),
        ({"card_number": "0" * 17}, _NUMBER),
        ({"card_number": "０" * 16}, _NUMBER),
        ({"card_password": "ab"}, _PASSWORD),
        ({"birthday": "abcdef"}, _AUTH),
        ({"installment": ""}, _INSTALLMENT),
        ({"installment": None}, _INSTALLMENT),
        ({"installment": 3}, _INSTALLMENT),
        ({"installment": "xyz"}, _INSTALLMENT),
        ({"installment": "123"}, _INSTALLMENT),
    ],
)
def test_card_input_rejected_before_http(mutation_client, changes: dict[str, Any], message: str) -> None:
    """PayViewModel.java:16196-16243; PayViewModel.smali:53511-53710,53727-53863: password 2, auth 6/10,
    month/current yyyyMM. The app checks the first three number groups' lengths and the fourth's minimum,
    but those lengths are protected, so the SDK only checks 13-16 ASCII digits. Format errors raise when the
    CardPayment is built; the expiry against the current month is checked when the payment is built."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailInvalidInputError, match=message):
        client.pay_with_card(hold(), card(**changes))
    assert not requests


@pytest.mark.parametrize("type_,auth", [("J", "000000"), ("S", "0000000000")])
def test_card_current_month_allowed_and_auth_type(mutation_client, type_: str, auth: str) -> None:
    """PayViewModel.java:16219-16243: expiration month is inclusive, auth length follows personal/company choice."""
    client, requests = mutation_client(
        [BASE],
        "POST",
        ("payment.ReservationPayment",),
        payment_form(hidAthnDvCd1=type_, hidAthnVal1=auth, hidCrdVlidTrm1="2609"),
    )
    client.pay_with_card(hold(), card(card_type=type_, birthday=auth, card_expire="2609"))
    assert len(requests) == 1


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
def test_payment_identifiers_and_money_required_before_http(mutation_client, changes: dict[str, Any]) -> None:
    """PayViewModel.java:6680-6684; the charge is received_amount, never h_tot_prc
    (PayViewModel.java:11027-11028,11303-11307)."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailProtocolError):
        client.pay_with_card(hold(**changes), card())
    assert not requests


@pytest.mark.parametrize("damage", ["mismatch", "journey-shape", "seat-shape", "pnr-shape"])
def test_real_hold_parse_failure_keeps_committed_identifiers(mutation_client, damage: str) -> None:
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
    client, requests = mutation_client([raw], "POST", ("certification.TicketReservation",), reservation_form())
    with pytest.raises(KorailProtocolError) as caught:
        client.reserve(train())
    assert caught.value.raw == raw
    assert len(requests) == 1
    assert caught.value.request_sent is True
    assert any("may have processed" in note for note in caught.value.__notes__)


@pytest.mark.parametrize(
    "variant,expected",
    [("padded", "1200"), ("no-seats", "1200"), ("incomplete-seat", None), ("blank-zero", "1200")],
)
def test_received_amount_never_becomes_partial_sum(mutation_client, variant: str, expected: str | None) -> None:
    """PayViewModel.java:11297-11307 sums h_tot_rcvd_amt; the numbered hidMnsStlAmt link is protected
    (PaymentMethodHelper.java:113,211), so the seat-sum policy is the library's."""
    raw = hold_raw()
    if variant == "no-seats":
        raw.pop("jrny_infos")
    elif variant == "incomplete-seat":
        raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"][1].pop("h_rcvd_amt")
    elif variant == "blank-zero":
        raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"].append(
            {"h_seat_no": "", "h_rcvd_amt": "0"}
        )
    client, _ = mutation_client([raw], "POST", ("certification.TicketReservation",), reservation_form())
    response = client.reserve(train())
    assert response.received_amount == expected
    assert response.raw == raw


def test_station_actual_parse_failure_retains_full_raw(mutation_client) -> None:
    case = next(c for c in CASES if c.name == "check_station_ticket_refund")
    raw = verification_raw()
    raw["orgtkinfo_list"][0]["pnr_no"] = []
    client, requests = mutation_client([raw], "POST", case.routes, case.form)
    with pytest.raises(KorailProtocolError) as caught:
        case.invoke(client)
    assert caught.value.raw == raw
    assert len(requests) == 1


def test_station_verification_no_commonout_envelope_and_conversion(mutation_client) -> None:
    """VerifyOnlineRefundsOut.java:29,64; StationTicketRefundResultViewModel.java:151-164."""
    case = next(c for c in CASES if c.name == "check_station_ticket_refund")
    raw = verification_raw()
    raw.pop("strResult")
    client, _ = mutation_client([raw, verification_raw()], "POST", case.routes * 2, case.form)
    result = case.invoke(client)
    assert result.str_result is None and result.raw == raw
    verified = case.invoke(client)
    request = StationRefundExecutionRequest.from_verification(
        verified, customer_phone="00000000000", customer_name="SYNTH-CUSTOMER"
    )
    assert request == execution_request()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_session_expired_no_retry(mutation_client, case: Case) -> None:
    raw = {**BASE, "strResult": "FAIL", "h_msg_cd": "P058"}
    client, requests = mutation_client([raw], case.method, case.routes[:1], case.form)
    with pytest.raises(KorailSessionExpiredError) as caught:
        case.invoke(client)
    assert caught.value.raw == raw
    assert client.session.current is None
    assert len(requests) == 1


@pytest.mark.parametrize("result_code,message_code", [("FAIL", "SYNTH-DECLINE"), ("SUCC", "SYNTH-SUCCESS")])
def test_payment_result_and_nested_settlement_stay_independent(
    mutation_client, result_code, message_code
) -> None:
    """ReservationPaymentOut.java:90: neither a successful hold nor envelope approves every settlement."""
    raw = {**payment_raw(), "strResult": result_code, "h_msg_cd": message_code}
    client, requests = mutation_client([raw], "POST", ("payment.ReservationPayment",), payment_form())
    result = client.pay_with_card(hold(), card())
    assert result.str_result == result_code and result.h_msg_cd == message_code
    assert len(result.tickets) == 1 and result.raw == raw
    assert result.settlements[0].settlement_result == "SYNTH-DECLINED-LEG"
    assert len(requests) == 1


def test_all_passenger_rows_and_combination_rules(mutation_client) -> None:
    """PassengerType.basicList() has seven types; ReqDiscount values confirmed by 7.0.8 literal recovery.
    Passengers.java:48,610-616,743-753: the total counts every type and zero rows are skipped before indexing."""
    passengers = KorailPassengerCounts(
        adult=1, child=1, infant=1, senior=1, severe_disability=1, mild_disability=1, guide_dog=1
    )
    expected = reservation_form()
    expected["txtTotPsgCnt"] = "7"
    for i, (type_, discount) in enumerate(
        [
            ("1", "000"),
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
    client, _ = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    client.reserve(train(), passengers=passengers)


@pytest.mark.parametrize("transfer", [False, True], ids=["direct", "transfer"])
def test_child_only_reservation_uses_request_discount_and_first_row(mutation_client, transfer: bool) -> None:
    """ReqDiscount.CHILD is 000; the issued-ticket ResDiscount.CHILD code 201 is not sent here."""
    expected = reservation_form(transfer=transfer)
    expected["txtPsgTpCd1"] = "3"
    client, requests = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    passengers = KorailPassengerCounts(adult=0, child=1)
    if transfer:
        client.reserve_transfer([train(), train(True)], passengers=passengers)
    else:
        client.reserve(train(), passengers=passengers)
    assert len(requests) == 1


@pytest.mark.parametrize(
    "passengers",
    [KorailPassengerCounts(adult=0, teenager=1), KorailPassengerCounts(adult=1, teenager=1)],
    ids=["teenager-only", "adult-and-teenager"],
)
@pytest.mark.parametrize("job_type", list(Job))
@pytest.mark.parametrize("transfer", [False, True], ids=["direct", "transfer"])
def test_teenager_reservation_rejected_before_queue_or_http(
    f8_client_factory: Callable[..., KorailClient],
    passengers: KorailPassengerCounts,
    job_type: Job,
    transfer: bool,
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        raise AssertionError("unsupported passengers must not contact the queue or reservation server")

    client = f8_client_factory(handler)
    seats = (
        tuple(KorailSeatAssignment(1, f"{i + 1}A") for i in range(passengers.total))
        if job_type is Job.SEAT_DESIGNATED
        else None
    )
    with pytest.raises(KorailProtocolError, match=r"teenager.*P11"):
        if transfer:
            client.reserve_transfer(
                [train(), train(True)],
                passengers=passengers,
                job_type=job_type,
                seats=[seats, seats] if seats is not None else None,
            )
        else:
            client.reserve(train(), passengers=passengers, job_type=job_type, seats=seats)
    assert not seen


@pytest.mark.parametrize("via_facade", [False, True], ids=["merge-follow-up", "facade"])
@pytest.mark.parametrize(
    "passengers",
    [KorailPassengerCounts(adult=0, teenager=1), KorailPassengerCounts(adult=1, teenager=1)],
    ids=["teenager-only", "adult-and-teenager"],
)
def test_teenager_merge_and_facade_reservations_rejected_before_http(
    f8_client_factory: Callable[..., KorailClient], passengers: KorailPassengerCounts, via_facade: bool
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        raise AssertionError("unsupported passengers must not contact the server")

    client = f8_client_factory(handler)
    with pytest.raises(KorailProtocolError, match=r"teenager.*P11"):
        if via_facade:
            ReservationResource(client).create(train(), passengers=passengers)
        else:
            client.reserve_merge(train(), merge_rows(), passengers=passengers)
    assert not seen


@pytest.mark.parametrize(
    "passengers",
    [
        KorailPassengerCounts(adult=0, infant=1),
        KorailPassengerCounts(adult=0, child=1, infant=1),
        KorailPassengerCounts(adult=1, guide_dog=1),
    ],
)
def test_invalid_passenger_combinations_before_http(mutation_client, passengers: KorailPassengerCounts) -> None:
    """PassengersBottomSheetKt.java:20715-20729,21124-21185 (warningPassengerType): infant needs non-child/non-infant;
    guide dog <= disabled passengers."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailProtocolError):
        client.reserve(train(), passengers=passengers)
    assert not requests


def test_transfer_seat_and_attribute_indexing(mutation_client) -> None:
    """TicketReservationIn.java:80; TicketReservationInSrcar.java:51; TicketReservationInSrcarTrailing.java:52; TrainSeatMapViewModel.java:2108-2138.

    TrainSeatMapViewModel.java:2210,2289: the chosen car and getSeatNo are copied, with the SEAT job only.
    TicketReservationInSrcar.java:81-88; TicketReservationInSrcarTrailing.java:86-89: leading/trailing seat keys.
    TrainScheduleViewModel.java:2914-2930,2982-2999: explicit seat attribute, then the row's, then the default."""
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
    client, _ = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    client.reserve_transfer(
        [train(), train(True)],
        job_type=Job.SEAT_DESIGNATED,
        seats=[(KorailSeatAssignment(1, "1A"),), (KorailSeatAssignment(2, "2B"),)],
        seat_attribute_codes=["021", "028"],
    )


def test_recalculation_parallel_empty_slots_and_nonmember_options(mutation_client) -> None:
    """NetworkApi.java:583-584; PriceReCalculationIn.java:38-41,114-133 (the four scalar keys are guessed from
    attribute names; PriceReCalculationIn$$serializer.java:44-47 is protected); non-member hiduserYn/hidCustNo:
    PriceReCalculationIn.java:32,34,114-129, PayViewModel.java:6167-6168 (smali :11764-11805,11834-11850; the
    key and N literal are protected)."""
    expected = recalc_form(
        hiduserYn="N",
        hidCustNo="SYNTH-NONMEMBER",
        txtPsrmClCd1="2",
        txtSeatAttCd2="000",
        txtSeatAttCd4="015",
        txtSeatAttCd5="000",
    )
    client, _ = mutation_client([hold_raw()], "POST", ("certification.PriceReCalculation",), expected)
    client.recalculate_price(
        recalc_request(
            non_member_no="SYNTH-NONMEMBER",
            cabin_class_code="2",
            seat_attribute_code_2="000",
            seat_attribute_code_4="015",
            seat_attribute_code_5="000",
        )
    )


def test_standby_no_sms_omits_phone(mutation_client) -> None:
    """ReservationWaitViewModel.java:520-527: no phone when SMS is not selected."""
    expected = {**COMMON, "txtPnrNo": PNR, "txtPsrmClChgFlg": "N", "txtSmsSndFlg": "N"}
    client, _ = mutation_client([BASE], "POST", ("reservationWait.ReservationWait",), expected)
    client.set_standby_options(hold(), phone_no="IGNORED-SYNTHETIC")


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
def test_all_payment_model_fields_and_optional_masks(mutation_client, mode: str) -> None:
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
    client, _ = mutation_client([raw], "POST", ("payment.ReservationPayment",), payment_form())
    result = client.pay_with_card(hold(), card())
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


RECALC_ROUTE = "certification.PriceReCalculation"
CART_FORM = {**COMMON, "hidPnrNo": PNR}


def test_recalculation_sends_one_request_and_the_caller_adds_the_cart(mutation_client) -> None:
    """PayViewModel.java:14428-14436: after a successful recalculation a logged-in app adds the PNR to the cart.
    3.0 removed recalculate_price(add_to_cart=); the caller sends that second request with add_to_cart."""
    cart = {**BASE, "h_msg_cd": "SYNTH-CART"}
    client, requests = mutation_client(
        [hold_raw(), cart], "POST", (RECALC_ROUTE, "cart.addCartList"), [recalc_form(), CART_FORM]
    )
    recalculated = client.recalculate_price(recalc_request())
    assert recalculated.received_amount == "1200" and len(requests) == 1
    assert recalculated.pnr_no is not None
    assert client.add_to_cart(CartAddRequest(recalculated.pnr_no)).h_msg_cd == "SYNTH-CART"
    assert len(requests) == 2


def test_recalculation_rows_come_from_the_first_journey_seats_like_the_app() -> None:
    """PayViewModel.java:5518,16856-16863: one row per first-journey seat copying type, cabin and current
    discount (:16858), dcnt_reld_no as hidDscpNo; :17469 refuses when the counts differ."""

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
    # 2.6.2: recalculating a standby hold returned a payable hold, bypassing the card-payment block.
    with pytest.raises(KorailProtocolError, match="standby"):
        PriceRecalculationRequest.for_hold(hold(journeys=journeys, payable=False), ["", "SYNTH-NEW"])


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


def test_recalculation_form_keeps_the_retrofit_field_order(mutation_client) -> None:
    """NetworkApi.java:584; RequestFactory.java:89-101: the FieldMap, including the four scalars, comes first
    and the six @Field lists follow in declaration order."""
    client, requests = mutation_client(
        [hold_raw()], "POST", ("certification.PriceReCalculation",), recalc_form(txtPsrmClCd1="2")
    )
    client.recalculate_price(recalc_request(cabin_class_code="2"))
    keys = [key for key, _ in parse_qsl(requests[0].content.decode(), keep_blank_values=True)]
    lists = ("psg_tp_dv_cd", "psrm_cl_cd", "dcnt_knd_cd1", "hidDscpNo", "hidDcntKndCd", "hidFmlyNo")
    assert keys[-12:] == [key for key in lists for _ in range(2)]
    assert "txtPsrmClCd1" in keys[:-12]


APP_HEAD = "Device Version AppVersion Key lang txtMenuId txtJobId hidFreeFlg txtStndFlg txtTotPsgCnt".split()
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
            "Device Version AppVersion Key lang txtPnrNo h_orgtk_sale_dt h_orgtk_sale_wct_no h_orgtk_sale_sqno "
            "h_orgtk_ret_pwd h_mlg_stl trnNo pbpAcepTgtFlg".split(),
        ),
    ],
)
def test_mutation_forms_follow_the_app_dto_order(mutation_client, name: str, expected: list[str]) -> None:
    """TicketReservationIn.java:80; TicketReservationInPassengerInfo.java:55; TicketReservationInJrny.java:69;
    RefundTicketIn.write$Self in 7.0.10 encodes CommonIn first, unlike constructor argument order."""
    case = next(c for c in CASES if c.name == name)
    client, requests = mutation_client([copy.deepcopy(case.response)], case.method, case.routes[:1], case.form)
    case.invoke(client)
    keys = [key for key, _ in parse_qsl(requests[0].content.decode(), keep_blank_values=True)]
    assert keys == expected


def test_seat_designated_transfer_and_full_refund_forms_follow_the_app_dto_order() -> None:
    """TicketReservationIn.java:80 (two seat counts before the lists, trailing seats last);
    RefundTicketIn.write$Self (common fields first, then own identity and optional fields)."""
    config = KorailConfig(base_url="https://offline.invalid", lang=COMMON["lang"])
    form = build_transfer_reservation_form(
        config,
        [train(), train(True)],
        job_type=Job.SEAT_DESIGNATED,
        seats=((KorailSeatAssignment(3, "SYNTH-5A"),), (KorailSeatAssignment(4, "SYNTH-6B"),)),
    )
    assert list(form) == [
        *APP_HEAD[:7],
        "txtGdNo",
        *APP_HEAD[7:],
        *APP_SEAT_ATTRIBUTES,
        *"txtSeatAttCd4_1 txtJrnyCnt txtSrcarCnt txtSrcarCnt1".split(),
        *APP_ADULT,
        *app_journey(1),
        *app_journey(2),
        *"txtSrcarNo1 txtSeatNo1 txtSrcarNo1_1 txtSeatNo1_1".split(),
    ]
    commission = bound_commission(str_result="SUCC", ticket_return_times_division_code="SYNTH-TMS")
    refund = payload_module.build_refund_form(
        config, ticket(), commission=commission, latitude="37.5", longitude="127.0"
    )
    assert list(refund) == (
        "Device Version AppVersion Key lang txtPnrNo h_orgtk_sale_dt h_orgtk_sale_wct_no h_orgtk_sale_sqno h_orgtk_ret_pwd h_mlg_stl "
        "tk_ret_tms_dv_cd "
        "trnNo pbpAcepTgtFlg latitude longitude".split()
    )


def test_retrieval_sends_the_pair_after_the_count_and_needs_a_journey(mutation_client) -> None:
    """NetworkApi.java:642-644: FieldMap (common, pbpCnt) then @Field pbpRsvNo, pnrNo;
    DeliveredTicketViewModel.java:185-205,283: one call per ticket grouped by the first journey's pbpRsvNo."""
    case = next(c for c in CASES if c.name == "recall_delivered_ticket")
    client, requests = mutation_client([case.response], case.method, case.routes, case.form)
    case.invoke(client)
    keys = [key for key, _ in parse_qsl(requests[0].content.decode(), keep_blank_values=True)]
    assert keys[-3:] == ["pbpCnt", "pbpRsvNo", "pnrNo"]
    with pytest.raises(KorailProtocolError, match="first journey"):
        client.recall_delivered_ticket(replace(DELIVERED_TICKET, journeys=()))
    with pytest.raises(KorailProtocolError):
        client.register_self_checkin(CHECKIN_DETAIL, object())  # type: ignore[arg-type]
    assert len(requests) == 1


@pytest.mark.parametrize(
    "name,response",
    [
        ("recall_delivered_ticket", BASE),
        ("recall_delivered_ticket", {**BASE, "prsList": [{}]}),
        ("register_self_checkin", BASE),
    ],
)
def test_checkin_and_retrieval_required_response_keys(
    mutation_client, name: str, response: dict[str, Any]
) -> None:
    """RetrieveTicketOut.java:54-59, Prs.java:46-50, SelfCheckInRegisterOut.java:47-52: required keys; the
    whole response
    stays on .raw and nothing is re-sent."""
    case = next(c for c in CASES if c.name == name)
    client, requests = mutation_client([response], case.method, case.routes, case.form)
    with pytest.raises(KorailProtocolError) as caught:
        case.invoke(client)
    assert caught.value.raw == response and len(requests) == 1


def test_mutation_parser_keeps_the_whole_response_when_called_directly(mutation_client) -> None:
    """RefundTicketOut.java:48-53; StlList.java:46-55: a bad settlement row fails with the whole response on
    .raw and the row on .parser_raw, directly and through the client."""
    row = {"stl_mns_cd": True}
    raw = {**BASE, "stlList": [row]}
    with pytest.raises(KorailProtocolError) as caught:
        parse_refund_ticket_response(raw)
    assert caught.value.raw is raw and caught.value.parser_raw is row
    client, _ = mutation_client([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    with pytest.raises(KorailProtocolError) as caught:
        client.refund(ticket(), commission=bound_commission())
    assert caught.value.raw == raw and caught.value.parser_raw == row


@pytest.mark.parametrize("transfer", [False, True], ids=["direct", "transfer"])
def test_standby_holds_are_not_payable(mutation_client, transfer: bool) -> None:
    """TrainScheduleViewModel.java:5096-5101; ReservationWaitViewModel.java:1155-1160: WAIT saves options, never
    pays. TrainScheduleOutTrainInfo.java:3587-3625: 특실 has no WAIT state."""
    row = train() if transfer else train(general_reservation_code="13", standing_reservation_code="11")
    expected = reservation_form(transfer=transfer, job="1102", stnd="N")
    client, requests = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    result = (
        client.reserve_transfer([row, train(True)], job_type=Job.STANDBY)
        if transfer
        else client.reserve(row, job_type=Job.STANDBY)
    )
    assert result.payable is False
    with pytest.raises(KorailProtocolError, match="standby"):
        client.pay_with_card(result, card())
    assert len(requests) == 1


@pytest.mark.parametrize("amount", ["0", "00000000000"])
def test_zero_amount_hold_is_not_card_paid(mutation_client, amount: str) -> None:
    """PayViewModel.java:15572,18144: the app builds no card request when nothing is owed and issues the
    ticket without a payment method (:5148), a path the library does not implement."""
    client, requests = mutation_client([], "POST", ("payment.ReservationPayment",), {})
    with pytest.raises(KorailProtocolError, match="zero-amount"):
        client.pay_with_card(hold(received_amount=amount), card())
    assert requests == []


def test_merge_first_and_follow_up_holds_stay_payable(mutation_client) -> None:
    """ReservationMergeViewModel.java:2094-2107: the merge screen's pay button pays the held reservation."""
    first_client, _ = mutation_client(
        [hold_raw()], "POST", ("certification.TicketReservation",), reservation_form(job="1202", stnd="N")
    )
    assert first_client.reserve(train(), job_type=Job.MERGE_STANDING).payable is True
    merged = {
        **reservation_form(job="1202"),
        "txtStndFlg": "Y",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    follow_up_client, _ = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    assert follow_up_client.reserve_merge(train(), merge_rows()).payable is True
    assert hold().payable is True


def test_merge_reservation_takes_no_job_type(mutation_client) -> None:
    """2.6.2: other job types were sent with the merge standing flag and came back as payable holds.
    3.0 removed the parameter; the merge follow-up is always MERGE_STANDING."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(TypeError, match="job_type"):
        client.reserve_merge(train(), merge_rows(), job_type=Job.STANDBY)  # type: ignore[call-arg]
    assert not requests


def test_standing_only_row_is_not_booked_as_immediate(mutation_client) -> None:
    """TrainScheduleOutTrainInfo.java:2810-2885: STAND is decided only after protected suspend/wait/merge
    checks, so 13/11 alone cannot tell whether the app would send a standing-only hold."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailProtocolError, match="available general seat"):
        client.reserve(train(general_reservation_code="13", standing_reservation_code="11"))
    assert not requests


@pytest.mark.parametrize(
    "call, match",
    [
        pytest.param(
            lambda c: c.reserve(train(), passengers=1), "exact KorailPassengerCounts", id="passengers"
        ),
        pytest.param(lambda c: KorailPassengerCounts(adult=-1), "non-negative", id="passenger-count"),
        pytest.param(lambda c: c.reserve(train(general_reservation_code="13")), "general seat", id="general"),
        pytest.param(
            lambda c: c.reserve(train(special_reservation_code="13"), seat_class=Cabin.SPECIAL),
            "special seat",
            id="special",
        ),
        pytest.param(
            lambda c: c.reserve(train(wait_reservation_flag="N"), job_type=Job.STANDBY),
            "h_wait_rsv_flg",
            id="wait",
        ),
        pytest.param(lambda c: c.cancel_unpaid_hold(hold(journey_count="0000")), "unpaid hold", id="cancel"),
        pytest.param(lambda c: c.set_standby_options(hold(), sms_notify=True), "11-digit", id="standby-sms"),
    ],
)
def test_reservation_input_faults_raise_invalid_input_before_http(mutation_client, call, match: str) -> None:
    """Pre-request rejections are KorailInvalidInputError, still a KorailProtocolError. The seat and waiting-list
    checks are TrainSummary.has_general_seat/has_special_seat/has_waiting_list."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailInvalidInputError, match=match):
        call(client)
    assert not requests


@pytest.mark.parametrize("standing_leg", [None, 0, 1])
def test_transfer_standing_flag_is_the_or_of_its_legs(mutation_client, standing_leg: int | None) -> None:
    """TrainScheduleViewModel.java:2961-2967,3004 ORs the per-leg check; TrainScheduleOutTrainInfo.java:2881-2889
    and TrainScheduleViewModel.java:2870-2874: 일반실 sold out (13) with standing available (11)."""
    legs = [train(), train(True)]
    if standing_leg is not None:
        legs[standing_leg] = replace(
            legs[standing_leg], general_reservation_code="13", standing_reservation_code="11"
        )
    expected = reservation_form(transfer=True, job="1202", stnd="N" if standing_leg is None else "Y")
    client, requests = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), expected)
    client.reserve_transfer(legs, job_type=Job.MERGE_STANDING)
    assert len(requests) == 1


@pytest.mark.parametrize("journey_count, sent", [(" 1", "1"), ("0002\t", "0002"), ("0001", "0001")])
def test_cancel_sends_the_journey_count_it_validated(mutation_client, journey_count: str, sent: str) -> None:
    """The check stripped the value but the form sent it unstripped (" 1" went out as txtJrnyCnt=+1).
    Zero padding is echoed as received (MyReservationViewModel.java:1557)."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    client, requests = mutation_client([BASE], "POST", (case.routes[-1],), {**case.form, "txtJrnyCnt": sent})
    client.cancel_unpaid_hold(hold(journey_count=journey_count), check_first=False)
    assert len(requests) == 1


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
def test_transfer_legs_must_be_distinct_and_in_boarding_order(
    mutation_client, legs: list[TrainSummary]
) -> None:
    """TrainScheduleViewModel.java:2952-2968 builds the form from one transfer search pair only."""
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailProtocolError, match="different trains|boarding order"):
        client.reserve_transfer(legs)
    assert not requests


def test_merge_rows_with_the_same_run_date_are_accepted(mutation_client) -> None:
    rows = tuple(TrainScheduleItem(**{**row.__dict__, "run_date": "20991230"}) for row in merge_rows())
    merged = {
        **reservation_form(job="1202"),
        "txtStndFlg": "Y",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    client, requests = mutation_client([hold_raw()], "POST", ("certification.TicketReservation",), merged)
    client.reserve_merge(train(), rows)
    assert len(requests) == 1


def test_mutation_parsers_read_integer_envelope_fields_as_strings() -> None:
    from korail_mobile_api._domains.reservations.parsers import parse_reservation_hold_response

    raw = {**hold_raw(), "h_msg_cd": 0, "h_msg_txt": 7}
    result = parse_reservation_hold_response(raw)
    assert (result.h_msg_cd, result.h_msg_txt) == ("0", "7")


def test_merge_rows_from_another_run_date_are_rejected(mutation_client) -> None:
    first, second = merge_rows()
    rows = (first, TrainScheduleItem(**{**second.__dict__, "run_date": "20991231"}))
    client, requests = mutation_client([], "POST", (), {})
    with pytest.raises(KorailProtocolError, match="run_date"):
        client.reserve_merge(train(), rows)
    assert not requests


@pytest.mark.parametrize(
    "case",
    [
        c
        for c in CASES
        if c.name in {"reserve", "reserve_transfer", "reserve_with_discount_card", "pay_with_card"}
    ],
    ids=lambda c: c.name,
)
def test_queue_handoff_one_operation_not_retry(mutation_client, case: Case) -> None:
    """Client gate boundary only. NetFunnel SDK protocol belongs to session 5 and checks/netfunnel_offline.py."""
    calls: list[str] = []

    class Queue:
        def run(self, gate: str, send: Callable[[], Any]) -> Any:
            calls.append(gate)
            return send()

        def close(self) -> None:
            pass

    client, requests = mutation_client([case.response], case.method, case.routes, case.form)
    client.netfunnel = Queue()
    case.invoke(client)
    assert calls == ["pay" if case.name == "pay_with_card" else "reserve"]
    assert len(requests) == 1


def test_numeric_zero_identifiers_are_echoed_without_repadding(mutation_client) -> None:
    """PayViewModel.java:6680-6684; 2026-09-21 numeric-String compatibility is separate from padding recovery."""
    expected = payment_form(hidTmpJobSqno1="0", hidTmpJobSqno2="42", hidRsvChgNo="0")
    client, _ = mutation_client([BASE], "POST", ("payment.ReservationPayment",), expected)
    client.pay_with_card(
        hold(
            temporary_job_sequence_1="0",
            temporary_job_sequence_2="42",
            journeys=(ReservationJourney(journey_sequence="1", reservation_change_no="0"),),
        ),
        card(),
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_invalid_envelope_keeps_entire_response_before_domain_parser(mutation_client, case: Case) -> None:
    """Shared transport must preserve the returned PNR even if strResult has an invalid type; no retry."""
    raw = {**case.response, "strResult": ["SYNTH-INVALID-TYPE"], "h_pnr_no": PNR}
    client, requests = mutation_client([raw], case.method, case.routes[:1], case.form)
    with pytest.raises(KorailProtocolError) as caught:
        case.invoke(client)
    assert caught.value.raw == raw
    assert len(requests) == 1


@pytest.mark.parametrize("payload", [[{"h_pnr_no": PNR}], "synthetic-not-an-object", 123, None])
def test_non_object_json_keeps_raw(mutation_client, payload: Any) -> None:
    client, requests = mutation_client(
        [payload], "POST", ("certification.TicketReservation",), reservation_form()
    )
    with pytest.raises(KorailProtocolError) as caught:
        client.reserve(train())
    assert caught.value.raw == payload
    assert len(requests) == 1


def test_invalid_json_retains_original_body_without_retry(scripted_client_factory) -> None:
    raw_text = '{"synthetic_partial_pnr":"SYNTH-PNR-ONLY",'
    config = KorailConfig(
        base_url="https://offline.invalid",
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_provider=lambda ctx: "SYNTHETIC-NOT-A-TOKEN"),
    )
    client, requests, _ = scripted_client_factory(
        [httpx.Response(200, text=raw_text)], config=config, session=KorailSession(jsessionid="SYNTH-SESSION")
    )
    with pytest.raises(KorailProtocolError) as caught:
        client.reserve(train())
    assert caught.value.raw == raw_text.encode("utf-8")
    assert len(requests) == 1


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
def test_refund_required_settlement_mask_does_not_silently_drop_data(mutation_client, shape: Any) -> None:
    """RefundTicketOut.java:48-53 required mask 0x8; StlList.java:46-55 required mask 0x1/non-null String."""
    raw = copy.deepcopy(BASE)
    if shape != "missing":
        raw["stlList"] = shape
    client, requests = mutation_client([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    with pytest.raises(KorailProtocolError) as caught:
        client.refund(ticket(), commission=bound_commission())
    assert caught.value.raw == raw
    assert len(requests) == 1


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
    mutation_client, rows: Any, codes: tuple[str, ...], is_null: bool
) -> None:
    """RefundTicketOut.java:48-58 distinguishes missing from explicit null; StlList.java:46-55; 2026-09-21 String/int policy."""
    raw = {**BASE, "stlList": rows}
    client, _ = mutation_client([raw], "POST", ("refunds.RefundsRequest",), refund_form(trnNo="90001"))
    result = client.refund(ticket(), commission=bound_commission())
    assert result.settlement_method_codes == codes
    assert result.settlement_list_is_null is is_null
    assert result.raw == raw


def test_actual_first_and_merge_requests_differ_only_at_four_fields(mutation_client) -> None:
    """ReservationMergeViewModel.smali:7671-7774; original request copied, not two new short journeys."""
    first_expected = reservation_form(job="1202")
    merged = {
        **first_expected,
        "txtStndFlg": "Y",
        "txtMidRsStnCd": "9099",
        "txtMidStnConsOrdr": "004",
        "txtMidStnRunOrdr": "003",
    }
    client, requests = mutation_client(
        [hold_raw(), hold_raw()], "POST", ("certification.TicketReservation",) * 2, [first_expected, merged]
    )
    client.reserve(train(), job_type=Job.MERGE_STANDING)
    client.reserve_merge(train(), merge_rows())
    actual_first = dict(parse_qsl(requests[0].content.decode(), keep_blank_values=True))
    actual_second = dict(parse_qsl(requests[1].content.decode(), keep_blank_values=True))
    changed = {
        k for k in actual_first.keys() | actual_second.keys() if actual_first.get(k) != actual_second.get(k)
    }
    assert changed == {"txtStndFlg", "txtMidRsStnCd", "txtMidStnConsOrdr", "txtMidStnRunOrdr"}


def test_hold_response_is_actual_source_of_payment_identifiers_and_amount(mutation_client) -> None:
    """PayViewModel.java:6680-6684: reservation response, not initial request or ticket face price, supplies payment identifiers."""
    client, requests = mutation_client(
        [hold_raw(), payment_raw()],
        "POST",
        ("certification.TicketReservation", "payment.ReservationPayment"),
        [reservation_form(), payment_form()],
    )
    response = client.reserve(train())
    assert response.temporary_job_sequence_1 == "001234"
    assert response.temporary_job_sequence_2 == "005678"
    assert response.journeys[0].reservation_change_no == "009"
    result = client.pay_with_card(response, card())
    assert result.total_received_amount == "1200"
    assert len(requests) == 2


def test_cancel_first_stage_common_envelope_failures_stop(mutation_client) -> None:
    """First-stage handling is not literally FAIL-only: a missing required strResult is transport policy.
    A success envelope carrying WRC000288 is not a failure (CommonOut.java:426-463)."""
    case = next(c for c in CASES if c.name == "cancel_unpaid_hold")
    raw = copy.deepcopy(BASE)
    raw.pop("strResult")
    client, requests = mutation_client([raw], "POST", case.routes[:1], case.form)
    with pytest.raises(KorailApiError) as caught:
        case.invoke(client)
    assert caught.value.raw == raw
    assert len(requests) == 1


@pytest.mark.parametrize("key", ["h_psg_tp_cd", "h_psrm_cl_cd", "h_dcnt_knd_cd1", "dcnt_reld_no"])
def test_recalculation_from_hold_keeps_raw_on_oversized_integer(key: str) -> None:
    """ReservationOutSeatInfo.java:80–109 declares strings; conversion errors must preserve the hold."""
    import sys

    from korail_mobile_api import (
        KorailProtocolError,
        PriceRecalculationRequest,
        ReservationHoldResponse,
        ReservationJourney,
    )

    seat = {key: 10**700}
    journey_raw = {"seat_infos": {"seat_info": [seat]}}
    raw = {"strResult": "SUCC", "synthetic_journey": journey_raw}
    hold = ReservationHoldResponse(
        str_result="SUCC",
        pnr_no="SYNTHETIC-PNR",
        journeys=(ReservationJourney(raw=journey_raw),),
        raw=raw,
    )
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        with pytest.raises(KorailProtocolError) as error:
            PriceRecalculationRequest.for_hold(hold, ["SYNTHETIC-DISCOUNT"])
        assert error.value.raw is raw
        assert error.value.parser_raw is seat
        assert isinstance(error.value.__cause__, ValueError)
    finally:
        sys.set_int_max_str_digits(previous)


def test_documented_recovery_cancels_a_hold_whose_response_failed_to_parse(scripted_client_factory) -> None:
    """docs/guide/errors.md#unparsed-hold: the PNR survives in raw and a hand-built hold cancels it."""
    config = KorailConfig(base_url="https://offline.invalid", netfunnel_enabled=False, disable_dynapath=True)
    unparsable = hold_raw()
    unparsable["h_tot_rcvd_amt"] = "009999"
    client, requests, _ = scripted_client_factory(
        [unparsable, {**BASE}, {**BASE}], config=config, session=KorailSession(jsessionid="SYNTH-SESSION")
    )
    with pytest.raises(KorailProtocolError) as caught:
        client.reserve(train())
    raw = caught.value.raw
    assert isinstance(raw, dict)
    pending = ReservationHoldResponse(
        str_result="SUCC", pnr_no=str(raw.get("h_pnr_no") or ""), journey_count=str(raw.get("h_jrny_cnt") or "")
    )
    client.cancel_unpaid_hold(pending)
    cancel = dict(parse_qsl(requests[-1].content.decode()))
    assert [request.url.path.rsplit(".", 1)[-1] for request in requests] == [
        "TicketReservation",
        "ReservationCancel",
        "ReservationCancelChk",
    ]
    assert (cancel["txtPnrNo"], cancel["txtJrnyCnt"]) == (PNR, "0001")
