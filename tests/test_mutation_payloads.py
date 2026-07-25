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
    ReservationJourney,
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
        temporary_job_sequence_1="SYNTHETIC_JOB_1",
        temporary_job_sequence_2="SYNTHETIC_JOB_2",
        total_price="8400",
        received_amount="7560",
        # Deliberately NOT "000": a builder that regressed to the constant would
        # otherwise pass against a fixture whose value happened to match the
        # fallback.
        journeys=(
            ReservationJourney(
                journey_sequence="0001",
                reservation_change_no="SYNTHETIC_CHG_NO",
            ),
        ),
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
        "hidTmpJobSqno1": "SYNTHETIC_JOB_1",
        "hidTmpJobSqno2": "SYNTHETIC_JOB_2",
        "hidRsvChgNo": "SYNTHETIC_CHG_NO",
        "hidInrecmnsGridcnt": "1",
        "hidStlMnsSqno1": "1",
        "hidStlMnsCd1": "02",
        "hidMnsStlAmt1": "7560",
        "hidCrdInpWayCd1": "@",
        "hidStlCrCrdNo1": "0000000000000000",
        "hidVanPwd1": "00",
        "hidCrdVlidTrm1": "2612",
        "hidIsmtMnthNum1": "00",
        "hidAthnDvCd1": "J",
        "hidAthnVal1": "900101",
        "hiduserYn": "Y",
    }


def test_card_payment_form_settles_the_received_amount_not_the_display_total():
    # AbstractC1269e.java:406 puts String.valueOf(getReceivedAmount()) into
    # PAYMENT_AMOUNT and V4/a.java:27 sets that as hidMnsStlAmt1.
    # PaymentActivity.java:174 assigns h_tot_prc to mTotPrc, which only
    # getmTotPrc() (:497) reads, for the UI.
    hold = _paid_hold()
    assert hold.total_price != hold.received_amount
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidMnsStlAmt1"] == hold.received_amount
    assert form["hidMnsStlAmt1"] != hold.total_price


def test_card_payment_form_echoes_the_holds_temporary_job_sequences():
    # V4/b.java:39-40 does setJobSqNo1(response.getH_tmp_job_sqno1()) and
    # likewise for 2; RsvPaymentDao.executeDao() (:129-131) passes those into
    # PaymentService.payment's @Field("hidTmpJobSqno1"/"2")
    # (PaymentService.java:14). They are reservation state, not a constant.
    hold = replace(
        _paid_hold(),
        temporary_job_sequence_1="000123",
        temporary_job_sequence_2="000456",
    )
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidTmpJobSqno1"] == "000123"
    assert form["hidTmpJobSqno2"] == "000456"


@pytest.mark.parametrize("missing", [None, "", "   "])
def test_card_payment_form_falls_back_when_the_hold_withheld_a_sequence(missing):
    # The app would forward the null and Retrofit would omit the @Field; this
    # client cannot reproduce that without a conditional field, so "000000" --
    # the value it has always sent, and the value srtgo hardcodes -- stays as
    # the explicit last resort.
    hold = replace(
        _paid_hold(),
        temporary_job_sequence_1=missing,
        temporary_job_sequence_2=missing,
    )
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidTmpJobSqno1"] == "000000"
    assert form["hidTmpJobSqno2"] == "000000"


def test_card_payment_form_echoes_the_holds_reservation_change_no():
    # V4/b.java:41 does setHidRsvChgNo(response.getJrny_infos()
    # .getJrny_info().get(0).getH_rsv_chg_no()), handed to
    # PaymentService.payment's @Field("hidRsvChgNo") (PaymentService.java:14).
    # Per-reservation state, not a protocol constant.
    hold = replace(
        _paid_hold(),
        journeys=(
            ReservationJourney(
                journey_sequence="0001", reservation_change_no="001"
            ),
        ),
    )
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidRsvChgNo"] == "001"


def test_card_payment_form_takes_the_first_journeys_reservation_change_no():
    # The app indexes .get(0) specifically, so a later journey's change number
    # must never win.
    hold = replace(
        _paid_hold(),
        journeys=(
            ReservationJourney(
                journey_sequence="0001", reservation_change_no="002"
            ),
            ReservationJourney(
                journey_sequence="0002", reservation_change_no="017"
            ),
        ),
    )
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidRsvChgNo"] == "002"


@pytest.mark.parametrize(
    "journeys",
    [
        (),  # no journey rows at all
        (ReservationJourney(journey_sequence="0001"),),  # None
        (
            ReservationJourney(
                journey_sequence="0001", reservation_change_no=""
            ),
        ),
        (
            ReservationJourney(
                journey_sequence="0001", reservation_change_no="   "
            ),
        ),
    ],
)
def test_card_payment_form_falls_back_when_the_hold_omits_the_change_no(journeys):
    # The app dereferences .get(0) unguarded and would forward a null for
    # Retrofit to drop; neither shape is reproducible without a conditional
    # field, so "000" -- what this builder has always sent -- is the documented
    # last resort.
    hold = replace(_paid_hold(), journeys=journeys)
    form = build_card_payment_form(KorailConfig(), hold, _fake_card())
    assert form["hidRsvChgNo"] == "000"


def test_card_payment_form_refuses_a_hold_that_carries_only_a_display_total():
    # Substituting h_tot_prc when the received amount is unknown is precisely
    # the defect this replaced, so the builder must refuse instead.
    hold = replace(_paid_hold(), received_amount=None)
    assert hold.total_price == "8400"
    with pytest.raises(KorailProtocolError):
        build_card_payment_form(KorailConfig(), hold, _fake_card())


@pytest.mark.parametrize(
    "hold",
    [
        ReservationHoldResponse(),  # no PNR / not SUCC
        ReservationHoldResponse(
            str_result="SUCC", pnr_no="P", window_no="W", received_amount="abc"
        ),  # non-numeric amount
        ReservationHoldResponse(
            str_result="SUCC", pnr_no="P", received_amount="8400"
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


def test_unpaid_reservation_cancel_form_sends_the_apps_fixed_change_no():
    # Deliberately NOT the payment builder's echo. Every app flow that cancels a
    # just-created hold from its ReservationResponse hardcodes "000" next to the
    # same fixed txtJrnySqno="0001": DReservationConfirmActivity.java:270-279
    # (executeRsvCancel reads getH_pnr_no()/getH_jrny_cnt() off the response,
    # even keeps the object, and still sets "000"),
    # ReservationWaitActivity.java:118-128, a6/x.java:97-106,
    # LimousineActivity.java:134-143, LimousineSelectSeatActivity.java:325.
    # Only the reservation-list screens pass a row's real change number, and
    # they pass that row's h_jrny_sqno too. So a hold carrying a change number
    # must NOT leak it into the cancel form.
    response = ReservationHoldResponse(
        h_msg_cd="IRR000018",
        h_msg_txt="success",
        str_result="SUCC",
        raw={},
        pnr_no="SYNTHETIC_PNR_REFERENCE",
        journey_count="0001",
        journeys=(
            ReservationJourney(
                journey_sequence="0001", reservation_change_no="017"
            ),
        ),
    )
    form = build_unpaid_reservation_cancel_form(KorailConfig(), response)
    assert form["hidRsvChgNo"] == "000"
    assert form["txtJrnySqno"] == "0001"
    # The payment builder, on the same hold, does echo it -- the two paths
    # diverge on purpose.
    assert response.journeys[0].reservation_change_no == "017"


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
