from __future__ import annotations

from dataclasses import replace

import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    CardPayment,
    KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    KorailConfig,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailSeatClass,
    PaidTicket,
    ReservationHoldResponse,
    ReservationJourney,
    TrainSummary,
)
from korail_mobile_api.mutation_payloads import (
    build_card_payment_form,
    build_refund_form,
    build_reservation_form,
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


# --- passenger mix and cabin class ------------------------------------------
#
# Expectations below are built from w4/a.java:49-73 (the eight rows and their
# fixed type/discount codes, in OPsg LinkedHashMap insertion order),
# m5/c.java:330 (the total is every counter summed) and K4/o.java:7-8 (the two
# cabin codes) -- NOT from what the builder happens to emit.


def _special_train() -> TrainSummary:
    # A 특실 hold is gated on the suite tab's own availability code
    # (a5/u.java:319 reads h_spe_rsv_cd for i9 != 0), so give the train one.
    return replace(_eligible_train(), special_reservation_code="11")


def test_default_passenger_mix_reproduces_the_single_adult_form_exactly():
    config = KorailConfig()
    train = _eligible_train()

    generalised = build_reservation_form(config, train)
    pinned = build_single_adult_reservation_form(config, train)

    assert generalised == pinned
    # KORAIL request field order is reproduced at insertion-order fidelity, so
    # equal contents are not enough: the key sequence has to match too.
    assert list(generalised) == list(pinned)


def test_explicit_one_adult_general_mix_reproduces_the_pinned_form_exactly():
    config = KorailConfig()
    train = _eligible_train()

    form = build_reservation_form(
        config,
        train,
        passengers=KorailPassengerCounts(adult=1),
        seat_class=KorailSeatClass.GENERAL,
    )
    pinned = build_single_adult_reservation_form(config, train)

    assert form == pinned
    assert list(form) == list(pinned)


@pytest.mark.parametrize(
    ("field_name", "row", "passenger_type", "discount_code"),
    [
        ("adult", 1, "1", "000"),
        ("teenager", 2, "1", "P11"),
        ("child", 3, "3", "000"),
        ("infant", 4, "3", "321"),
        ("senior", 5, "1", "131"),
        ("severe_disability", 6, "1", "111"),
        ("mild_disability", 7, "1", "112"),
        ("guide_dog", 8, "1", "173"),
    ],
)
def test_each_passenger_type_fills_its_own_app_row(
    field_name,
    row,
    passenger_type,
    discount_code,
):
    # One passenger of the type under test and nobody else, so the row it lands
    # in is unambiguous. Some of these mixes (a lone 동반유아, a lone 안내견)
    # are ones the app's picker would warn about; this asserts wire placement,
    # not that the mix is bookable.
    passengers = KorailPassengerCounts(**{"adult": 0, field_name: 1})

    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        passengers=passengers,
    )

    assert form[f"txtCompaCnt{row}"] == "1"
    assert form[f"txtPsgTpCd{row}"] == passenger_type
    assert form[f"txtDiscKndCd{row}"] == discount_code
    assert form["txtTotPsgCnt"] == "1"
    # Every other row still goes out, carrying zero.
    for other in range(1, 9):
        if other != row:
            assert form[f"txtCompaCnt{other}"] == "0"


def test_passenger_rows_keep_the_apps_field_order():
    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        passengers=KorailPassengerCounts(adult=2, child=1),
    )
    keys = list(form)
    block = keys[keys.index("txtTotPsgCnt") : keys.index("txtSeatAttCd1")]

    assert block == [
        "txtTotPsgCnt",
        "txtCompaCnt1",
        "txtPsgTpCd1",
        "txtDiscKndCd1",
        "txtCompaCnt2",
        "txtPsgTpCd2",
        "txtDiscKndCd2",
        "txtCompaCnt3",
        "txtPsgTpCd3",
        "txtDiscKndCd3",
        "txtCompaCnt4",
        "txtPsgTpCd4",
        "txtDiscKndCd4",
        "txtCompaCnt5",
        "txtPsgTpCd5",
        "txtDiscKndCd5",
        "txtCompaCnt6",
        "txtPsgTpCd6",
        "txtDiscKndCd6",
        "txtCompaCnt7",
        "txtPsgTpCd7",
        "txtDiscKndCd7",
        "txtCompaCnt8",
        "txtPsgTpCd8",
        "txtDiscKndCd8",
    ]


def test_mixed_booking_fills_every_row_it_names():
    passengers = KorailPassengerCounts(
        adult=2,
        teenager=1,
        child=1,
        infant=1,
        senior=1,
    )

    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        passengers=passengers,
    )

    assert [form[f"txtCompaCnt{row}"] for row in range(1, 9)] == [
        "2",
        "1",
        "1",
        "1",
        "1",
        "0",
        "0",
        "0",
    ]
    assert [form[f"txtPsgTpCd{row}"] for row in range(1, 9)] == [
        "1",
        "1",
        "3",
        "3",
        "1",
        "1",
        "1",
        "1",
    ]
    assert [form[f"txtDiscKndCd{row}"] for row in range(1, 9)] == [
        "000",
        "P11",
        "000",
        "321",
        "131",
        "111",
        "112",
        "173",
    ]
    assert form["txtTotPsgCnt"] == "6"


def test_total_passenger_count_includes_the_lap_infant_and_the_guide_dog():
    # m5/c.java:330 sums ALL eight counters into TOTAL_PERSON_COUNT --
    # CHILD_ACCOMPANY_COUNT (동반유아) and GUIDE_DOG_COUNT included -- and
    # w4/a.java:49 sends that number as txtTotPsgCnt. An infant is NOT excluded
    # from the seat count on this wire, whatever a lap infant means at the gate.
    passengers = KorailPassengerCounts(
        adult=1,
        infant=1,
        severe_disability=1,
        guide_dog=1,
    )

    assert passengers.total == 4

    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        passengers=passengers,
    )

    assert form["txtTotPsgCnt"] == "4"


def test_reservation_form_carries_no_discount_card_field_for_a_discounted_row():
    # OPsg declares exactly one card field, txtCardNo_ (OPsg.java:7), written
    # only by the separate N-card request (w4/a.java:101, discount kind "153").
    # korail2's txtCardCode_/txtCardNo_/txtCardPw_ trio (korail2.py:363-370)
    # and srtgo's (ktx.py:286-295) have no counterpart in the 경로/장애 rows,
    # which carry a count and a discount code and nothing else.
    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        passengers=KorailPassengerCounts(
            adult=1,
            senior=1,
            severe_disability=1,
            mild_disability=1,
        ),
    )

    assert not [
        key
        for key in form
        if key.startswith(("txtCardCode", "txtCardNo", "txtCardPw"))
    ]


def test_special_class_form_sends_the_apps_special_cabin_code():
    form = build_reservation_form(
        KorailConfig(),
        _special_train(),
        seat_class=KorailSeatClass.SPECIAL,
    )

    assert form["txtPsrmClCd1"] == "2"
    # Nothing else about the request moves with the cabin.
    assert form["txtStndFlg"] == "N"
    assert form["txtSeatAttCd4"] == "015"
    assert list(form) == list(
        build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    )


def test_seat_class_enum_holds_only_the_two_bookable_cabins():
    assert KorailSeatClass.GENERAL.value == "1"
    assert KorailSeatClass.SPECIAL.value == "2"
    assert [member.value for member in KorailSeatClass] == ["1", "2"]


def test_special_class_form_needs_the_special_cabin_to_be_available():
    # h_spe_rsv_cd is the code the suite tab checks (a5/u.java:319); a train
    # with general seats free but the suite sold out must not be held as 특실.
    train = replace(
        _eligible_train(),
        general_reservation_code="11",
        special_reservation_code="13",
    )

    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(), train, seat_class=KorailSeatClass.SPECIAL
        )


def test_general_class_form_ignores_the_special_cabins_availability():
    train = replace(_eligible_train(), special_reservation_code="13")

    form = build_reservation_form(KorailConfig(), train)

    assert form["txtPsrmClCd1"] == "1"


def test_reservation_form_rejects_an_unknown_seat_class():
    for seat_class in ("0", "3", "", None, 1):
        with pytest.raises(KorailProtocolError):
            build_reservation_form(
                KorailConfig(), _eligible_train(), seat_class=seat_class
            )


def test_reservation_form_rejects_a_foreign_passenger_counts_object():
    class LookalikeCounts:
        adult = 1
        teenager = 0
        child = 0
        infant = 0
        senior = 0
        severe_disability = 0
        mild_disability = 0
        guide_dog = 0
        total = 1

    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(), _eligible_train(), passengers=LookalikeCounts()
        )


def test_passenger_counts_default_to_one_adult():
    passengers = KorailPassengerCounts()

    assert passengers.adult == 1
    assert passengers.total == 1
    assert (
        passengers.teenager
        == passengers.child
        == passengers.infant
        == passengers.senior
        == passengers.severe_disability
        == passengers.mild_disability
        == passengers.guide_dog
        == 0
    )


def test_passenger_counts_reject_an_empty_mix():
    with pytest.raises(ValueError):
        KorailPassengerCounts(adult=0)


@pytest.mark.parametrize(
    "field_name",
    [
        "adult",
        "teenager",
        "child",
        "infant",
        "senior",
        "severe_disability",
        "mild_disability",
        "guide_dog",
    ],
)
def test_passenger_counts_reject_a_negative_count(field_name):
    with pytest.raises(ValueError):
        KorailPassengerCounts(**{"adult": 2, field_name: -1})


@pytest.mark.parametrize("value", [True, 1.0, "1", None])
def test_passenger_counts_reject_a_non_integer_count(value):
    with pytest.raises(ValueError):
        KorailPassengerCounts(adult=value)


def test_passenger_counts_allow_the_apps_maximum_mix():
    # m5/d.java:32-33 -- the picker the main booking flow uses -- caps the
    # total at 9, and m5/c.java:250-252 stops the plus button there.
    passengers = KorailPassengerCounts(adult=8, child=1)

    assert passengers.total == KORAIL_MAX_PASSENGERS_PER_RESERVATION == 9

    form = build_reservation_form(
        KorailConfig(), _eligible_train(), passengers=passengers
    )

    assert form["txtTotPsgCnt"] == "9"


def test_passenger_counts_reject_a_mix_over_the_apps_maximum():
    with pytest.raises(ValueError):
        KorailPassengerCounts(adult=9, child=1)
    with pytest.raises(ValueError):
        KorailPassengerCounts(adult=10)


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
