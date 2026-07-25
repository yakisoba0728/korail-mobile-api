from __future__ import annotations

from dataclasses import replace

import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    CardPayment,
    KorailConfig,
    KorailProtocolError,
    PaidTicket,
    ReservationHoldResponse,
    TrainSummary,
)
from korail_mobile_api.mutation_payloads import (
    build_card_payment_form,
    build_refund_form,
    build_single_adult_reservation_form,
    build_unpaid_reservation_cancel_form,
)


def _paid_ticket() -> PaidTicket:
    return PaidTicket(
        pnr_no="SYNTHETIC_PNR",
        sale_date="20260725",
        sale_window_no="SYNTHETIC_WCT",
        sale_sequence="0001",
        return_password="SYNTHETIC_RETPWD",
        train_no="00209",
    )


def test_refund_form_matches_the_app_refund_contract():
    form = build_refund_form(KorailConfig(), _paid_ticket())
    assert form == {
        "Device": "AD",
        "Version": "250601003",
        "Key": "korail1234567890",
        "txtPnrNo": "SYNTHETIC_PNR",
        "h_orgtk_sale_dt": "20260725",
        "h_orgtk_sale_wct_no": "SYNTHETIC_WCT",
        "h_orgtk_sale_sqno": "0001",
        "h_orgtk_ret_pwd": "SYNTHETIC_RETPWD",
        "h_mlg_stl": "N",
        "tk_ret_tms_dv_cd": "21",
        "trnNo": "00209",
        "pbpAcepTgtFlg": "N",
        "latitude": "",
        "longitude": "",
    }


def test_refund_form_spells_the_pnr_field_the_way_the_app_declares_it():
    # RefundService.java:29 / RefundService.smali:212 declare
    # @Field("txtPnrNo"); srtgo's txtPrnNo (ktx.py:1082) is a lineage typo with
    # zero hits in the decompiled app. Retrofit @Field is exact-match, so the
    # typo would post a refund carrying no PNR at all.
    form = build_refund_form(KorailConfig(), _paid_ticket())
    assert form["txtPnrNo"] == "SYNTHETIC_PNR"
    assert "txtPrnNo" not in form
    cancel_form = build_unpaid_reservation_cancel_form(
        KorailConfig(), _paid_hold()
    )
    assert cancel_form["txtPnrNo"] == form["txtPnrNo"]


@pytest.mark.parametrize(
    "field_name",
    ["pnr_no", "sale_date", "sale_window_no", "sale_sequence", "return_password"],
)
def test_refund_form_rejects_missing_paid_ticket_identity(field_name):
    kwargs = {
        "pnr_no": "P",
        "sale_date": "20260725",
        "sale_window_no": "W",
        "sale_sequence": "1",
        "return_password": "R",
        "train_no": "00209",
    }
    kwargs[field_name] = ""
    with pytest.raises(KorailProtocolError):
        build_refund_form(KorailConfig(), PaidTicket(**kwargs))


def _paid_hold() -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd="IRR000018",
        h_msg_txt="ok",
        str_result="SUCC",
        raw={},
        pnr_no="SYNTHETIC_PNR",
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        total_price="8400",
    )


def _fake_card() -> CardPayment:
    return CardPayment(
        card_number="0000000000000000",
        card_password="00",
        card_expire="2612",
        birthday="900101",
    )


def test_card_payment_form_matches_the_app_pay_with_card_contract():
    form = build_card_payment_form(KorailConfig(), _paid_hold(), _fake_card())
    assert form == {
        "Device": "AD",
        "Version": "250601003",
        "Key": "korail1234567890",
        "hidPnrNo": "SYNTHETIC_PNR",
        "hidWctNo": "SYNTHETIC_WCT",
        "hidTmpJobSqno1": "000000",
        "hidTmpJobSqno2": "000000",
        "hidRsvChgNo": "000",
        "hidInrecmnsGridcnt": "1",
        "hidStlMnsSqno1": "1",
        "hidStlMnsCd1": "02",
        "hidMnsStlAmt1": "8400",
        "hidCrdInpWayCd1": "@",
        "hidStlCrCrdNo1": "0000000000000000",
        "hidVanPwd1": "00",
        "hidCrdVlidTrm1": "2612",
        "hidIsmtMnthNum1": "00",
        "hidAthnDvCd1": "J",
        "hidAthnVal1": "900101",
        "hiduserYn": "Y",
    }


@pytest.mark.parametrize(
    "hold",
    [
        ReservationHoldResponse(),  # no PNR / not SUCC
        ReservationHoldResponse(
            str_result="SUCC", pnr_no="P", window_no="W", total_price="abc"
        ),  # non-numeric amount
        ReservationHoldResponse(
            str_result="SUCC", pnr_no="P", total_price="8400"
        ),  # missing window number
    ],
)
def test_card_payment_form_rejects_holds_without_payment_identity(hold):
    with pytest.raises(KorailProtocolError):
        build_card_payment_form(KorailConfig(), hold, _fake_card())


def test_card_payment_form_rejects_non_digit_card_number():
    bad = CardPayment(
        card_number="4111-1111-1111-1111",
        card_password="00",
        card_expire="2612",
        birthday="900101",
    )
    with pytest.raises(KorailProtocolError):
        build_card_payment_form(KorailConfig(), _paid_hold(), bad)


def _eligible_train() -> TrainSummary:
    return TrainSummary(
        train_no="00209",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0501",
        departure_date="20990101",
        departure_time="100700",
        arrival_time="102400",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="2",
        general_reservation_code="11",
        departure_construction_order="1",
        arrival_construction_order="2",
        seat_attribute_code="015",
    )


def test_single_adult_reservation_form_matches_the_app_contract_exactly():
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())

    assert form == {
        "Device": "AD",
        "Version": "250601003",
        "Key": "korail1234567890",
        "txtMenuId": "11",
        "txtJobId": "1101",
        "txtGdNo": "",
        "hidFreeFlg": "N",
        "txtStndFlg": "N",
        "txtTotPsgCnt": "1",
        "txtCompaCnt1": "1",
        "txtPsgTpCd1": "1",
        "txtDiscKndCd1": "000",
        "txtCompaCnt2": "0",
        "txtPsgTpCd2": "1",
        "txtDiscKndCd2": "P11",
        "txtCompaCnt3": "0",
        "txtPsgTpCd3": "3",
        "txtDiscKndCd3": "000",
        "txtCompaCnt4": "0",
        "txtPsgTpCd4": "3",
        "txtDiscKndCd4": "321",
        "txtCompaCnt5": "0",
        "txtPsgTpCd5": "1",
        "txtDiscKndCd5": "131",
        "txtCompaCnt6": "0",
        "txtPsgTpCd6": "1",
        "txtDiscKndCd6": "111",
        "txtCompaCnt7": "0",
        "txtPsgTpCd7": "1",
        "txtDiscKndCd7": "112",
        "txtCompaCnt8": "0",
        "txtPsgTpCd8": "1",
        "txtDiscKndCd8": "173",
        "txtSeatAttCd1": "000",
        "txtSeatAttCd2": "000",
        "txtSeatAttCd3": "000",
        "txtSeatAttCd4": "015",
        "txtSeatAttCd5": "000",
        "txtPsrmClCd1": "1",
        "txtJrnyCnt": "1",
        "txtJrnyTpCd1": "11",
        "txtJrnySqno1": "001",
        "txtTrnNo1": "00209",
        "txtTrnClsfCd1": "00",
        "txtTrnGpCd1": "100",
        "txtRunDt1": "20990101",
        "txtDptDt1": "20990101",
        "txtDptTm1": "100700",
        "arvTm_1": "102400",
        "txtDptRsStnCd1": "0001",
        "txtDptStnConsOrdr1": "1",
        "txtDptStnRunOrdr1": "1",
        "txtArvRsStnCd1": "0501",
        "txtArvStnConsOrdr1": "2",
        "txtArvStnRunOrdr1": "2",
        "txtChgFlg1": "N",
    }


def test_single_adult_reservation_form_uses_the_apps_fixed_general_seat_attribute():
    train = replace(_eligible_train(), seat_attribute_code="017")

    form = build_single_adult_reservation_form(KorailConfig(), train)

    assert form["txtSeatAttCd4"] == "015"


@pytest.mark.parametrize(
    "train",
    [
        replace(_eligible_train(), general_reservation_code="12"),
        replace(_eligible_train(), arrival_run_order=None),
        replace(_eligible_train(), departure_date="2099-01-01"),
    ],
)
def test_single_adult_reservation_form_rejects_non_hold_safe_train_shapes(train):
    with pytest.raises(KorailProtocolError):
        build_single_adult_reservation_form(KorailConfig(), train)


def test_unpaid_reservation_cancel_form_uses_only_fresh_hold_identifiers():
    response = ReservationHoldResponse(
        h_msg_cd="SYNTHETIC_SUCCESS",
        h_msg_txt="success",
        str_result="SUCC",
        raw={},
        pnr_no="SYNTHETIC_PNR_REFERENCE",
        journey_count="1",
    )

    assert build_unpaid_reservation_cancel_form(KorailConfig(), response) == {
        "Device": "AD",
        "Version": "250601003",
        "Key": "korail1234567890",
        "txtPnrNo": "SYNTHETIC_PNR_REFERENCE",
        "txtJrnySqno": "0001",
        "txtJrnyCnt": "1",
        "hidRsvChgNo": "000",
    }


def test_unpaid_reservation_cancel_form_accepts_zero_padded_journey_count():
    # A live TicketReservation returns h_jrny_cnt="0001", not "1"; the cancel
    # form builder must accept the real single-journey value (evidenced live).
    response = ReservationHoldResponse(
        h_msg_cd="IRR000018",
        h_msg_txt="success",
        str_result="SUCC",
        raw={},
        pnr_no="SYNTHETIC_PNR_REFERENCE",
        journey_count="0001",
    )
    form = build_unpaid_reservation_cancel_form(KorailConfig(), response)
    assert form["txtPnrNo"] == "SYNTHETIC_PNR_REFERENCE"
    assert form["txtJrnyCnt"] == "1"
    assert form["txtJrnySqno"] == "0001"


@pytest.mark.parametrize(
    "response",
    [
        ReservationHoldResponse(),
        ReservationHoldResponse(pnr_no="SYNTHETIC_PNR_REFERENCE", journey_count="2"),
        ReservationHoldResponse(pnr_no="SYNTHETIC_PNR_REFERENCE", journey_count="0002"),
        ReservationHoldResponse(pnr_no="SYNTHETIC_PNR_REFERENCE", journey_count="1x"),
        BaseKorailResponse(),
    ],
)
def test_unpaid_reservation_cancel_form_rejects_non_fresh_hold_shapes(response):
    with pytest.raises(KorailProtocolError):
        build_unpaid_reservation_cancel_form(KorailConfig(), response)
