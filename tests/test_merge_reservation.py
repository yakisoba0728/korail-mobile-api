"""Offline tests for 병합예약 — ONE train split at a mid station, two journeys.

병합 is not a transfer and not a third case of ``C5/a.java``'s journey loop. It
is one physical train sold as two journeys so its halves can be seated
differently (좌석+좌석 or 좌석+입석), and it is built somewhere else entirely.
Everything asserted here was read out of the decompiled app:

* the two journey-type codes -- ``K4/e``'s ``STANDING_SEAT_1("병합 선행")`` and
  ``STANDING_SEAT_2("병합 후행")``, read from bytecode at
  ``analysis/apktool/smali/K4/e.smali:31-55`` (``"21"`` and ``"22"``) because
  jadx renders BOTH of them, and ``TRANSFER``, as unrelated same-valued
  constants.
* merge eligibility -- ``S4/J.java:61-63``'s ``isMixedSeat(cabin,
  h_yms_apl_flg)``, fed per search row by ``a5/u.java:378-380`` and consumed at
  ``:394-397``, where the booking button becomes 입석+좌석 예매
  (``res/values/strings.xml:425``) with tag ``"1202"``.
* the first hold -- ``DirectInquiryActivity.java:448-451``, which reads that tag
  and sets ``txtJobId="1202"`` on the otherwise untouched direct form.
* the server's offer to merge -- the literal ``<중간연결역 변경>``
  (``res/values/strings.xml:2018``) arrives inside KORAIL's own reservation
  message (``S4/x.java:93-109`` copies ``h_msg_mndry``/``h_msg_txt5``
  verbatim), the confirm screen makes it tappable through the span table at
  ``res/values/arrays.xml:421-438`` (``K6/C5956a.java:74-77``), and tapping it
  is ``setResult(RESULT_OK)`` + ``finish`` (``i6/ActivityC5799a.java:70-73``)
  back to the requestCode-119 caller (``C5/a.java:239``).
* the 연결역 list -- ``research.mergeSeatsC.do``
  (``ResearchService.java:47-49``), requested at
  ``DirectInquiryActivity.java:350-372`` and already implemented here as
  ``KorailClient.get_merge_seats_inquiry``.
* the second hold -- ``DirectInquiryActivity.java:576-601``, re-read as
  ``analysis/apktool/smali/…/DirectInquiryActivity.smali:5580-6010``:
  ``txtJrnyCnt="2"`` before the loop (``:5598``), ``txtJrnyTpCd`` keyed on the
  loop INDEX (``if-nez v2`` at ``:5641``), ``txtJobId`` back to ``"1101"``
  (``:5636``), ``txtStndFlg`` pinned ``"Y"`` (``:5891``), leg 2's cabin copied
  from ``txtPsrmClCd1`` (``:5926-5983``), and no ``setArvTm`` anywhere.

NOTHING here has been transmitted to the live server.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from korail_mobile_api import (
    KORAIL_MAX_JOURNEY_LEGS,
    KORAIL_MERGE_SEAT_FLAGS_BY_CABIN,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KorailClient,
    KorailConfig,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailSeatClass,
    KorailSession,
    MutationConsent,
    MutationPreview,
    TrainScheduleItem,
    TrainSummary,
)
from korail_mobile_api.constants import (
    KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE,
    KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE,
    KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
)
from korail_mobile_api.mutation_payloads import (
    build_merge_reservation_form,
    build_reservation_form,
    build_single_adult_reservation_form,
    is_merge_eligible,
)


def _config() -> KorailConfig:
    return KorailConfig()


def _standing_hold_train() -> TrainSummary:
    """서울 -> 부산 on a row the app would label 입석+좌석 예매."""
    return TrainSummary(
        train_no="00043",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0020",
        departure_date="20990101",
        departure_time="060000",
        arrival_time="083500",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="9",
        departure_construction_order="1",
        arrival_construction_order="9",
        general_reservation_code="11",
        special_reservation_code="11",
        seat_attribute_code="015",
        merge_seat_application_flag="G",
    )


def _leading_leg() -> TrainScheduleItem:
    """서울 -> 대전 on the same train, the 선행 half."""
    return TrainScheduleItem(
        train_no="00043",
        train_group_code="100",
        train_class_code="00",
        run_date="20990101",
        departure_date="20990101",
        departure_time="060000",
        arrival_time="070500",
        departure_station_code="0001",
        arrival_station_code="0010",
        departure_construction_order="1",
        arrival_construction_order="4",
        departure_run_order="1",
        arrival_run_order="4",
    )


def _trailing_leg() -> TrainScheduleItem:
    """대전 -> 부산 on the same train, the 후행 half."""
    return TrainScheduleItem(
        train_no="00043",
        train_group_code="100",
        train_class_code="00",
        run_date="20990101",
        departure_date="20990101",
        departure_time="070500",
        arrival_time="083500",
        departure_station_code="0010",
        arrival_station_code="0020",
        departure_construction_order="4",
        arrival_construction_order="9",
        departure_run_order="4",
        arrival_run_order="9",
    )


def _merge_form(**kwargs) -> dict[str, str]:
    return build_merge_reservation_form(
        _config(),
        _standing_hold_train(),
        (_leading_leg(), _trailing_leg()),
        **kwargs,
    )


# ---------------------------------------------------------------------------
# The enum, resolved from bytecode rather than from jadx.


def test_merge_journey_type_codes_are_the_smali_values() -> None:
    assert KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE == "21"
    assert KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE == "22"
    # And they are not the transfer code, which is what a "병합 is a transfer"
    # reading would have produced.
    assert KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE != (
        KORAIL_TRANSFER_JOURNEY_TYPE_CODE
    )
    assert KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE != (
        KORAIL_TRANSFER_JOURNEY_TYPE_CODE
    )


def test_merge_standing_job_id_is_1202() -> None:
    assert KorailReservationJobType.MERGE_STANDING.value == "1202"


# ---------------------------------------------------------------------------
# Eligibility: S4/J.java:61-63, evaluated per cabin.


@pytest.mark.parametrize(
    ("flag", "cabin", "expected"),
    [
        ("A", KorailSeatClass.GENERAL, True),
        ("G", KorailSeatClass.GENERAL, True),
        ("S", KorailSeatClass.GENERAL, False),
        ("M", KorailSeatClass.GENERAL, False),
        ("N", KorailSeatClass.GENERAL, False),
        ("A", KorailSeatClass.SPECIAL, True),
        ("S", KorailSeatClass.SPECIAL, True),
        ("G", KorailSeatClass.SPECIAL, False),
        # The "M" arm of the ternary only ever reaches `"G".equals("M")`, so a
        # 특실 request on an "M" row is NOT merge-eligible.
        ("M", KorailSeatClass.SPECIAL, False),
        (None, KorailSeatClass.GENERAL, False),
    ],
)
def test_is_merge_eligible_matches_ismixedseat(
    flag: str | None,
    cabin: KorailSeatClass,
    expected: bool,
) -> None:
    train = replace(
        _standing_hold_train(),
        merge_seat_application_flag=flag,
    )
    assert is_merge_eligible(train, seat_class=cabin) is expected


def test_merge_flag_table_is_the_two_evidenced_sets() -> None:
    assert KORAIL_MERGE_SEAT_FLAGS_BY_CABIN == {
        "1": frozenset({"A", "G"}),
        "2": frozenset({"A", "S"}),
    }


def test_train_summary_parses_the_yms_flag() -> None:
    train = TrainSummary.from_raw({"h_trn_no": "00043", "h_yms_apl_flg": "A"})
    assert train.merge_seat_application_flag == "A"


# ---------------------------------------------------------------------------
# The first hold: "1202" is the ordinary direct form with one field changed.


def test_merge_standing_hold_is_the_direct_form_with_a_different_job_id(
) -> None:
    train = _standing_hold_train()
    ordinary = build_single_adult_reservation_form(_config(), train)
    standing = build_reservation_form(
        _config(),
        train,
        job_type=KorailReservationJobType.MERGE_STANDING,
    )
    assert list(standing) == list(ordinary)
    differences = {
        key: (ordinary[key], standing[key])
        for key in ordinary
        if ordinary[key] != standing[key]
    }
    assert differences == {"txtJobId": ("1101", "1202")}


def test_merge_standing_hold_needs_a_merge_eligible_row() -> None:
    train = replace(
        _standing_hold_train(),
        merge_seat_application_flag="N",
    )
    with pytest.raises(KorailProtocolError, match="h_yms_apl_flg"):
        build_reservation_form(
            _config(),
            train,
            job_type=KorailReservationJobType.MERGE_STANDING,
        )


def test_merge_standing_hold_is_direct_only() -> None:
    from korail_mobile_api.mutation_payloads import (
        build_transfer_reservation_form,
    )

    train = _standing_hold_train()
    with pytest.raises(KorailProtocolError, match="1202"):
        build_transfer_reservation_form(
            _config(),
            (train, replace(train, train_no="00045")),
            job_type=KorailReservationJobType.MERGE_STANDING,
        )


def test_adding_the_job_type_left_the_other_three_alone() -> None:
    assert [member.value for member in KorailReservationJobType] == [
        "1101",
        "1102",
        "1103",
        "1202",
    ]
    # A merge-eligible row still builds the byte-identical "1101" form it built
    # before "1202" existed: the new eligibility gate is reached only for
    # MERGE_STANDING.
    train = _standing_hold_train()
    assert build_reservation_form(
        _config(),
        train,
    ) == build_single_adult_reservation_form(_config(), train)
    # ...and a row with NO merge flag at all is still an ordinary bookable
    # "1101", i.e. the gate did not become a new precondition for everyone.
    plain = replace(train, merge_seat_application_flag=None)
    assert build_single_adult_reservation_form(_config(), plain)["txtJobId"] == (
        "1101"
    )


# ---------------------------------------------------------------------------
# The second hold: the merged form itself.


# The merged form's keys, in the order the app's LinkedHashMaps produce them:
# the standing hold's own order with journey 2's block appended, and NO arvTm_2.
PINNED_MERGE_KEYS: tuple[str, ...] = (
    "Device",
    "Version",
    "Key",
    "txtMenuId",
    "txtJobId",
    "txtGdNo",
    "hidFreeFlg",
    "txtStndFlg",
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
    "txtSeatAttCd1",
    "txtSeatAttCd2",
    "txtSeatAttCd3",
    "txtSeatAttCd4",
    "txtSeatAttCd5",
    "txtPsrmClCd1",
    "txtSeatAttCd4_1",
    "txtPsrmClCd2",
    "txtJrnyCnt",
    "txtJrnyTpCd1",
    "txtJrnySqno1",
    "txtTrnNo1",
    "txtTrnClsfCd1",
    "txtTrnGpCd1",
    "txtRunDt1",
    "txtDptDt1",
    "txtDptTm1",
    "arvTm_1",
    "txtDptRsStnCd1",
    "txtDptStnConsOrdr1",
    "txtDptStnRunOrdr1",
    "txtArvRsStnCd1",
    "txtArvStnConsOrdr1",
    "txtArvStnRunOrdr1",
    "txtChgFlg1",
    "txtJrnyTpCd2",
    "txtJrnySqno2",
    "txtTrnNo2",
    "txtTrnClsfCd2",
    "txtTrnGpCd2",
    "txtRunDt2",
    "txtDptDt2",
    "txtDptTm2",
    "txtDptRsStnCd2",
    "txtDptStnConsOrdr2",
    "txtDptStnRunOrdr2",
    "txtArvRsStnCd2",
    "txtArvStnConsOrdr2",
    "txtArvStnRunOrdr2",
    "txtChgFlg2",
)


def test_merge_form_key_order_is_pinned() -> None:
    assert tuple(_merge_form()) == PINNED_MERGE_KEYS


def test_merge_form_has_no_second_arrival_time() -> None:
    # The merge loop never calls setArvTm (no such call in
    # smali/…/DirectInquiryActivity.smali:5730-6010), so leg 2 has none at all
    # and leg 1 keeps the standing hold's -- the WHOLE ROUTE's arrival time.
    form = _merge_form()
    assert "arvTm_2" not in form
    assert form["arvTm_1"] == _standing_hold_train().arrival_time
    assert form["arvTm_1"] != _leading_leg().arrival_time


def test_merge_journey_types_differ_per_leg() -> None:
    form = _merge_form()
    assert form["txtJrnyTpCd1"] == KORAIL_MERGE_LEADING_JOURNEY_TYPE_CODE
    assert form["txtJrnyTpCd2"] == KORAIL_MERGE_TRAILING_JOURNEY_TYPE_CODE
    # Which is exactly what a 환승 does NOT do: both of its legs carry "14".
    assert form["txtJrnyTpCd1"] != form["txtJrnyTpCd2"]


def test_merge_form_scalars() -> None:
    form = _merge_form()
    assert form["txtJobId"] == KorailReservationJobType.IMMEDIATE.value
    assert form["txtStndFlg"] == "Y"
    assert form["txtJrnyCnt"] == KORAIL_TRANSFER_ITINERARY_CODE
    assert form["txtJrnySqno1"] == "001"
    assert form["txtJrnySqno2"] == "002"
    assert form["txtMenuId"] == "11"
    assert form["txtGdNo"] == ""
    assert form["hidFreeFlg"] == "N"
    assert form["txtChgFlg1"] == "N"
    assert form["txtChgFlg2"] == "N"


def test_merge_standing_flag_is_pinned_not_derived() -> None:
    # A row whose general seats are open would derive txtStndFlg="N" through
    # isStndSeat; the merge loop pins "Y" regardless (smali:5887-5891).
    assert _merge_form()["txtStndFlg"] == "Y"
    assert (
        build_single_adult_reservation_form(
            _config(),
            _standing_hold_train(),
        )["txtStndFlg"]
        == "N"
    )


def test_merge_second_cabin_is_copied_from_the_first() -> None:
    for cabin in (KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL):
        form = _merge_form(seat_class=cabin)
        assert form["txtPsrmClCd1"] == cabin.value
        assert form["txtPsrmClCd2"] == cabin.value
    # And there is no per-leg cabin parameter to pass, unlike a 환승.
    with pytest.raises(TypeError):
        _merge_form(seat_classes=(KorailSeatClass.GENERAL,))


def test_merge_form_carries_the_passenger_mix_unchanged() -> None:
    form = _merge_form(
        passengers=KorailPassengerCounts(adult=2, child=1),
    )
    assert form["txtTotPsgCnt"] == "3"
    assert form["txtCompaCnt1"] == "2"
    assert form["txtCompaCnt3"] == "1"


def test_merge_form_carries_no_seat_designation_keys() -> None:
    assert not [key for key in _merge_form() if key.startswith("txtSrcar")]
    assert not [key for key in _merge_form() if key.startswith("txtSeatNo")]


def test_merge_legs_must_be_the_same_train() -> None:
    with pytest.raises(KorailProtocolError, match="ONE train"):
        build_merge_reservation_form(
            _config(),
            _standing_hold_train(),
            (_leading_leg(), replace(_trailing_leg(), train_no="00045")),
        )


def test_merge_needs_exactly_two_legs() -> None:
    for legs in ((_leading_leg(),), (_leading_leg(),) * 3):
        with pytest.raises(KorailProtocolError, match="exactly"):
            build_merge_reservation_form(
                _config(),
                _standing_hold_train(),
                legs,
            )
    assert KORAIL_MAX_JOURNEY_LEGS == 2


def test_merge_refuses_wrong_leg_types() -> None:
    with pytest.raises(KorailProtocolError, match="TrainScheduleItem"):
        build_merge_reservation_form(
            _config(),
            _standing_hold_train(),
            (_standing_hold_train(), _standing_hold_train()),
        )
    with pytest.raises(KorailProtocolError, match="TrainSummary"):
        build_merge_reservation_form(
            _config(),
            _leading_leg(),
            (_leading_leg(), _trailing_leg()),
        )


def test_merge_refuses_a_hold_train_without_an_arrival_time() -> None:
    with pytest.raises(KorailProtocolError, match="arrival_time"):
        build_merge_reservation_form(
            _config(),
            replace(_standing_hold_train(), arrival_time=None),
            (_leading_leg(), _trailing_leg()),
        )


# ---------------------------------------------------------------------------
# The client method: same route, same category, dry-run by default.


def _client() -> KorailClient:
    client = KorailClient(_config())
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client


def test_reserve_merge_is_denied_without_consent() -> None:
    from korail_mobile_api import KorailMutationNotAllowedError

    client = _client()
    try:
        with pytest.raises(KorailMutationNotAllowedError):
            client.reserve_merge(
                _standing_hold_train(),
                (_leading_leg(), _trailing_leg()),
                consent=MutationConsent(),
            )
        with pytest.raises(KorailMutationNotAllowedError):
            client.reserve_merge(
                _standing_hold_train(),
                (_leading_leg(), _trailing_leg()),
                consent=MutationConsent(allow_cancel=True),
            )
    finally:
        client.close()


def test_reserve_merge_dry_run_previews_the_reserve_route() -> None:
    client = _client()
    try:
        preview = client.reserve_merge(
            _standing_hold_train(),
            (_leading_leg(), _trailing_leg()),
            consent=MutationConsent(allow_reserve=True),
        )
    finally:
        client.close()
    assert type(preview) is MutationPreview
    assert preview.category == "reserve"
    assert preview.method == "POST"
    assert preview.route == (
        "/classes/com.korail.mobile.certification.TicketReservation"
    )
    assert preview.note == "dry-run: not sent"
    assert preview.payload["txtJrnyTpCd1"] == "21"
    assert preview.payload["txtJrnyTpCd2"] == "22"
