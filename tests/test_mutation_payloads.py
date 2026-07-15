from __future__ import annotations

from dataclasses import replace

import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    KorailConfig,
    KorailProtocolError,
    ReservationHoldResponse,
    TrainSummary,
)
from korail_mobile_api.mutation_payloads import (
    build_single_adult_reservation_form,
    build_unpaid_reservation_cancel_form,
)


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


@pytest.mark.parametrize(
    "response",
    [
        ReservationHoldResponse(),
        ReservationHoldResponse(pnr_no="SYNTHETIC_PNR_REFERENCE", journey_count="2"),
        BaseKorailResponse(),
    ],
)
def test_unpaid_reservation_cancel_form_rejects_non_fresh_hold_shapes(response):
    with pytest.raises(KorailProtocolError):
        build_unpaid_reservation_cancel_form(KorailConfig(), response)
