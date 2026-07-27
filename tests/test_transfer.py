"""Offline tests for 환승 — searching two-leg itineraries and booking them.

Everything asserted here was read out of the decompiled app, never out of what
the builders happen to emit:

* the two itinerary codes -- ``K4/d.java:5-6``, ``DIRECT_SQ_NO("직통", "1")`` and
  ``TRANSFER_SQ_NO("환승", "2")``, cross-checked in
  ``analysis/apktool/smali/K4/d.smali:36,64``.
* the two journey-type codes -- ``K4/e.java:6-7``, read from bytecode at
  ``analysis/apktool/smali/K4/e.smali:40`` (DIRECT ``"11"``) and ``:68``
  (TRANSFER ``"14"``) because jadx renders the second as an unrelated
  same-valued constant.
* the journey block -- ``C5/a.java:52-119`` (``N0``), a loop over the train
  array: ``:55`` derives ``txtJrnyCnt`` from the array LENGTH, ``:57`` writes at
  ``i + 1``, ``:60`` keys ``txtJrnyTpCd`` on the LENGTH and ``:61`` keys
  ``txtJrnySqno`` on the INDEX. The two differing ternaries were re-read as
  ``analysis/apktool/smali/C5/a.smali:306-338`` and ``:343``.
* the sequence-number formatting -- ``S4/O.java:19-21`` into
  ``S4/N.java:32-38``, ``DecimalFormat("000")``.
* the field names -- ``OJrny.java:6-27`` (note ``arvTm_`` rather than
  ``txtArvTm``), ``OSeat.java:7-35`` and ``OSrcar.java:6-30``.
* two legs and no more -- ``OSeat.java:32-35`` and ``OSrcar.java:21-30`` both
  split on ``i == 1`` alone, ``ReservationRequest.java:114-117`` reads back
  exactly the two seat slots, ``a5/k.java:108-110`` and ``:156-170`` build
  pairs, ``a5/u.java:252-253`` carries two slots with the second nullable.
* the search re-query -- ``DirectInquiryActivity.java:615-624`` (``WRD000061``
  and nothing else) into ``:284-296`` (``setRadJobId(TRANSFER_SQ_NO)`` and
  nothing else), confirmed at
  ``analysis/apktool/smali/…/DirectInquiryActivity.smali:1677-1689``.
* the response shape -- a flat ``trn_infos.trn_info`` list paired positionally,
  ``a5/k.java:156-170``; ``h_chg_trn_seq`` as the server's copy of that
  position, ``u4/a.java:111-131`` and ``RsvInquiryRequest.java:164-172``.
* standby not composing -- ``a5/k.java:120-127`` (``G0()`` returns false for a
  non-direct result) and ``DirectInquiryActivity.java:434`` (the app's only
  ``txtJobId="1102"``).

NOTHING here has been transmitted to the live server. No transfer form built by
this package has ever reached KORAIL.
"""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_MAX_JOURNEY_LEGS,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KorailClient,
    KorailConfig,
    KorailNoDirectTrainError,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailSeatAssignment,
    KorailSeatClass,
    KorailSession,
    MutationConsent,
    MutationPreview,
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
    TransferItinerary,
    TransferSearchResult,
)
from korail_mobile_api.models import pair_transfer_itineraries
from korail_mobile_api.constants import (
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KORAIL_STANDBY_WAIT_FLAG,
    KORAIL_TRANSFER_JOURNEY_TYPE_CODE,
)
from korail_mobile_api.mutation_payloads import (
    build_reservation_form,
    build_single_adult_reservation_form,
    build_transfer_reservation_form,
)
from korail_mobile_api.payloads import build_train_search_form


# The sixteen per-leg OJrny keys, unsuffixed, in C5/a.java:62-76's write order.
# Fifteen carry the journey number as a plain suffix; arvTm_ is the one the app
# spells with an underscore (OJrny.java:12, 40-42).
JOURNEY_FIELDS: tuple[str, ...] = (
    "txtJrnyTpCd",
    "txtJrnySqno",
    "txtTrnNo",
    "txtTrnClsfCd",
    "txtTrnGpCd",
    "txtRunDt",
    "txtDptDt",
    "txtDptTm",
    "arvTm_",
    "txtDptRsStnCd",
    "txtDptStnConsOrdr",
    "txtDptStnRunOrdr",
    "txtArvRsStnCd",
    "txtArvStnConsOrdr",
    "txtArvStnRunOrdr",
    "txtChgFlg",
)

# What build_single_adult_reservation_form has emitted since the live
# 2026-07-24/25 reserve -> cancel round trip, in order. Generalising the builder
# to a sequence of legs must not move, add or drop one of these.
PINNED_SINGLE_LEG_KEYS: tuple[str, ...] = (
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
)


def _first_leg() -> TrainSummary:
    """서울 -> 대전 on a run that is bookable in both cabins."""
    return TrainSummary(
        train_no="00209",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0501",
        departure_date="20990101",
        departure_time="100700",
        arrival_time="112400",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="7",
        general_reservation_code="11",
        special_reservation_code="11",
        departure_construction_order="1",
        arrival_construction_order="7",
        seat_attribute_code="015",
        change_train_sequence=KORAIL_DIRECT_ITINERARY_CODE,
    )


def _second_leg() -> TrainSummary:
    """대전 -> 여수엑스포, the connecting run."""
    return TrainSummary(
        train_no="01513",
        train_group_code="100",
        departure_station_code="0501",
        arrival_station_code="0723",
        departure_date="20990101",
        departure_time="120500",
        arrival_time="143800",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="4",
        arrival_run_order="19",
        general_reservation_code="11",
        special_reservation_code="11",
        departure_construction_order="4",
        arrival_construction_order="19",
        seat_attribute_code="015",
        change_train_sequence=KORAIL_TRANSFER_ITINERARY_CODE,
    )


def _legs() -> tuple[TrainSummary, TrainSummary]:
    return (_first_leg(), _second_leg())


def _logged_in_no_network_client() -> KorailClient:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError(
            f"a dry run must not send a request (saw {request.method} "
            f"{request.url.path})"
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client


# --- the enum values, read from bytecode ------------------------------------


def test_itinerary_and_journey_type_codes_are_the_apps_enum_values():
    # K4/d.smali:36 / :64 -- the 직통/환승 sequence pair.
    assert KORAIL_DIRECT_ITINERARY_CODE == "1"
    assert KORAIL_TRANSFER_ITINERARY_CODE == "2"
    # K4/e.smali:40 / :68 -- the journey-type pair. NOT "1"/"2", and TRANSFER is
    # "14" rather than the "12" a reader guessing from DIRECT="11" would expect.
    assert KORAIL_DIRECT_JOURNEY_TYPE_CODE == "11"
    assert KORAIL_TRANSFER_JOURNEY_TYPE_CODE == "14"
    assert KORAIL_TRANSFER_JOURNEY_TYPE_CODE != KORAIL_TRANSFER_ITINERARY_CODE
    # a5/k.java:108-110, OSeat.java:32-35, OSrcar.java:21-30.
    assert KORAIL_MAX_JOURNEY_LEGS == 2


# --- the single-leg form is untouched ---------------------------------------


def test_single_leg_reservation_form_is_byte_for_byte_what_it_was():
    config = KorailConfig()
    train = _first_leg()

    form = build_single_adult_reservation_form(config, train)

    assert tuple(form) == PINNED_SINGLE_LEG_KEYS
    # txtJrnyCnt is DIRECT_SQ_NO, and it is DIRECT_SQ_NO because the leg count
    # is 1 (C5/a.java:55), not because anything asked for a direct booking.
    assert form["txtJrnyCnt"] == KORAIL_DIRECT_ITINERARY_CODE == "1"
    assert form["txtJrnyTpCd1"] == KORAIL_DIRECT_JOURNEY_TYPE_CODE == "11"
    assert form["txtJrnySqno1"] == "001"
    assert build_reservation_form(config, train) == form
    assert tuple(build_reservation_form(config, train)) == PINNED_SINGLE_LEG_KEYS


def test_single_leg_form_carries_no_journey_two_key_of_any_spelling():
    form = build_single_adult_reservation_form(KorailConfig(), _first_leg())

    for field in JOURNEY_FIELDS:
        assert f"{field}1" in form
        assert f"{field}2" not in form
    # OSeat.java:34 and OSrcar.java:22,27,16 -- the journey-2 spellings.
    assert "txtSeatAttCd4_1" not in form
    assert "txtPsrmClCd2" not in form
    assert "txtSrcarCnt1" not in form
    assert not any(key.startswith("txtSrcarNo1_") for key in form)
    assert not any(key.startswith("txtSeatNo1_") for key in form)


# --- the two-leg journey block ----------------------------------------------


def test_transfer_form_repeats_the_journey_block_once_per_leg():
    form = build_transfer_reservation_form(KorailConfig(), _legs())

    for journey in (1, 2):
        for field in JOURNEY_FIELDS:
            assert f"{field}{journey}" in form, f"{field}{journey}"
    # 1-based: the loop writes at i + 1 (C5/a.java:57), so there is no journey 0
    # and no journey 3.
    for field in JOURNEY_FIELDS:
        assert f"{field}0" not in form
        assert f"{field}3" not in form


def test_transfer_journey_count_follows_the_leg_count():
    config = KorailConfig()
    first, second = _legs()

    assert (
        build_reservation_form(config, first)["txtJrnyCnt"]
        == KORAIL_DIRECT_ITINERARY_CODE
    )
    assert (
        build_transfer_reservation_form(config, (first, second))["txtJrnyCnt"]
        == KORAIL_TRANSFER_ITINERARY_CODE
    )


def test_both_legs_carry_the_transfer_journey_type_code():
    # C5/a.java:60 evaluates (length == 1 ? DIRECT : TRANSFER) inside the loop
    # but tests the array LENGTH, so leg 1 is not left as a direct leg.
    form = build_transfer_reservation_form(KorailConfig(), _legs())

    assert form["txtJrnyTpCd1"] == KORAIL_TRANSFER_JOURNEY_TYPE_CODE == "14"
    assert form["txtJrnyTpCd2"] == KORAIL_TRANSFER_JOURNEY_TYPE_CODE == "14"
    assert KORAIL_DIRECT_JOURNEY_TYPE_CODE not in {
        form["txtJrnyTpCd1"],
        form["txtJrnyTpCd2"],
    }


def test_journey_sequence_numbers_key_on_the_index_and_are_zero_padded():
    # C5/a.java:61 keys on the INDEX -- the one place the app differs from the
    # line above it -- and S4/O.getSequenceNo runs the code through
    # DecimalFormat("000").
    form = build_transfer_reservation_form(KorailConfig(), _legs())

    assert form["txtJrnySqno1"] == "001"
    assert form["txtJrnySqno2"] == "002"


def test_transfer_journey_values_come_from_the_matching_leg():
    first, second = _legs()

    form = build_transfer_reservation_form(KorailConfig(), (first, second))

    assert form["txtTrnNo1"] == first.train_no
    assert form["txtDptRsStnCd1"] == first.departure_station_code
    assert form["txtArvRsStnCd1"] == first.arrival_station_code
    assert form["txtDptTm1"] == first.departure_time
    assert form["arvTm_1"] == first.arrival_time
    assert form["txtDptStnConsOrdr1"] == first.departure_construction_order
    assert form["txtArvStnRunOrdr1"] == first.arrival_run_order

    assert form["txtTrnNo2"] == second.train_no
    assert form["txtDptRsStnCd2"] == second.departure_station_code
    assert form["txtArvRsStnCd2"] == second.arrival_station_code
    assert form["txtDptTm2"] == second.departure_time
    assert form["arvTm_2"] == second.arrival_time
    assert form["txtDptStnConsOrdr2"] == second.departure_construction_order
    assert form["txtArvStnRunOrdr2"] == second.arrival_run_order
    # The transfer station is stated twice, once as each leg's endpoint, and the
    # app sends no field of its own for it.
    assert form["txtArvRsStnCd1"] == form["txtDptRsStnCd2"]
    assert form["txtChgFlg1"] == form["txtChgFlg2"] == "N"


def test_transfer_form_is_the_single_leg_form_plus_exactly_the_journey_two_keys():
    config = KorailConfig()
    first, second = _legs()

    single = build_reservation_form(config, first)
    transfer = build_transfer_reservation_form(config, (first, second))

    added = set(transfer) - set(single)
    assert added == {
        # OSeat's journey-2 pair (OSeat.java:34, 16-18).
        "txtSeatAttCd4_1",
        "txtPsrmClCd2",
    } | {f"{field}2" for field in JOURNEY_FIELDS}
    assert not set(single) - set(transfer)
    # Only txtJrnyCnt and the two journey-type codes change value; every other
    # shared key is identical, because nothing else is leg-count dependent.
    changed = {
        key
        for key in single
        if single[key] != transfer[key]
    }
    assert changed == {"txtJrnyCnt", "txtJrnyTpCd1"}


def test_transfer_key_order_is_the_apps_map_order():
    form = build_transfer_reservation_form(KorailConfig(), _legs())
    keys = list(form)

    # OSeat is a LinkedHashMap and ReservationRequest.setOSeat is a putAll
    # (ReservationRequest.java:165-167), so re-putting journey 1's keys keeps
    # their position and journey 2's land after txtPsrmClCd1.
    assert keys[keys.index("txtSeatAttCd5") + 1 :][:3] == [
        "txtPsrmClCd1",
        "txtSeatAttCd4_1",
        "txtPsrmClCd2",
    ]
    # OPsg, OSeat, OJrny, OSrcar is the @FieldMap order the DAO passes
    # (ReservationDao.java:17 into CertificationService.java:52-54), so the
    # whole OSeat block precedes txtJrnyCnt.
    assert keys.index("txtPsrmClCd2") < keys.index("txtJrnyCnt")
    # Within OJrny: the count, then all sixteen of journey 1, then all sixteen
    # of journey 2 (C5/a.java:54-76).
    assert keys[keys.index("txtJrnyCnt") + 1 :] == [
        f"{field}1" for field in JOURNEY_FIELDS
    ] + [f"{field}2" for field in JOURNEY_FIELDS]


# --- the leg count is refused, not silently truncated ------------------------


@pytest.mark.parametrize("count", [0, 1, 3, 4])
def test_transfer_reservation_refuses_any_leg_count_but_two(count):
    legs = (_first_leg(), _second_leg(), _first_leg(), _second_leg())[:count]

    with pytest.raises(KorailProtocolError) as excinfo:
        build_transfer_reservation_form(KorailConfig(), legs)

    assert "2 legs" in str(excinfo.value)


def test_a_third_leg_would_collide_rather_than_extend():
    # Why the refusal above is a refusal and not a limitation: the app's key
    # selectors are two-way. A journey-3 write lands on journey 2's key.
    from korail_mobile_api.mutation_payloads import (
        _seat_attribute_key,
        _srcar_count_key,
        _srcar_no_key,
        _seat_no_key,
    )

    assert _seat_attribute_key(1) == "txtSeatAttCd4"
    assert _seat_attribute_key(2) == _seat_attribute_key(3) == "txtSeatAttCd4_1"
    assert _srcar_count_key(1) == "txtSrcarCnt"
    assert _srcar_count_key(2) == _srcar_count_key(3) == "txtSrcarCnt1"
    assert _srcar_no_key(1, 1) == "txtSrcarNo1"
    assert _srcar_no_key(2, 1) == _srcar_no_key(3, 1) == "txtSrcarNo1_1"
    assert _seat_no_key(1, 1) == "txtSeatNo1"
    assert _seat_no_key(2, 1) == _seat_no_key(3, 1) == "txtSeatNo1_1"


def test_transfer_reservation_requires_exact_train_summaries():
    with pytest.raises(KorailProtocolError):
        build_transfer_reservation_form(
            KorailConfig(),
            (_first_leg(), {"train_no": "01513"}),
        )
    with pytest.raises(KorailProtocolError):
        build_transfer_reservation_form(KorailConfig(), "not a sequence")


def test_every_leg_must_be_bookable_not_just_the_first():
    first, second = _legs()
    sold_out = replace(second, general_reservation_code="13")

    with pytest.raises(KorailProtocolError, match="available general seat"):
        build_transfer_reservation_form(KorailConfig(), (first, sold_out))


# --- what composes ----------------------------------------------------------


def test_passenger_mix_is_per_booking_not_per_leg():
    # OPsg is built once on the booking-options screen (w4/a.java:47-74) and N0
    # never touches it, so a transfer carries exactly one set of eight rows.
    form = build_transfer_reservation_form(
        KorailConfig(),
        _legs(),
        passengers=KorailPassengerCounts(adult=2, child=1),
    )

    assert form["txtTotPsgCnt"] == "3"
    assert form["txtCompaCnt1"] == "2"
    assert form["txtCompaCnt3"] == "1"
    assert "txtCompaCnt1_1" not in form
    assert "txtTotPsgCnt2" not in form


def test_cabin_class_is_per_leg():
    # C5/a.java:59 reads the cabin with the leg index and :97 writes
    # txtPsrmClCd{i} from it, so the two legs need not match.
    mixed = build_transfer_reservation_form(
        KorailConfig(),
        _legs(),
        seat_classes=(KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL),
    )

    assert mixed["txtPsrmClCd1"] == "1"
    assert mixed["txtPsrmClCd2"] == "2"


def test_one_cabin_class_applies_to_both_legs():
    config = KorailConfig()
    legs = _legs()

    single = build_transfer_reservation_form(
        config,
        legs,
        seat_classes=KorailSeatClass.SPECIAL,
    )
    spelled = build_transfer_reservation_form(
        config,
        legs,
        seat_classes=(KorailSeatClass.SPECIAL, KorailSeatClass.SPECIAL),
    )

    assert single == spelled
    assert single["txtPsrmClCd1"] == single["txtPsrmClCd2"] == "2"


def test_cabin_class_count_must_match_the_leg_count():
    with pytest.raises(KorailProtocolError, match="one cabin class per leg"):
        build_transfer_reservation_form(
            KorailConfig(),
            _legs(),
            seat_classes=(
                KorailSeatClass.GENERAL,
                KorailSeatClass.SPECIAL,
                KorailSeatClass.GENERAL,
            ),
        )


def test_seat_designation_is_per_leg_with_the_apps_journey_two_spellings():
    # C5/a.java:120-133 opens the picker per journey index and passes it as
    # TRAIN_INDEX; SeatSearchActivity.java:675-682 writes
    # setSrcarCnt(TRAIN_INDEX + 1, …); OSrcar.java:21-30 spells journey 2 apart.
    form = build_transfer_reservation_form(
        KorailConfig(),
        _legs(),
        passengers=KorailPassengerCounts(adult=2),
        job_type=KorailReservationJobType.SEAT_DESIGNATED,
        seats=(
            (
                KorailSeatAssignment(car_no=4, seat_no="5A"),
                KorailSeatAssignment(car_no=4, seat_no="5B"),
            ),
            (
                KorailSeatAssignment(car_no=7, seat_no="1A"),
                KorailSeatAssignment(car_no=7, seat_no="1B"),
            ),
        ),
    )

    assert form["txtJobId"] == "1103"
    assert form["txtSrcarCnt"] == "2"
    assert form["txtSrcarNo1"] == "4"
    assert form["txtSeatNo1"] == "5A"
    assert form["txtSrcarNo2"] == "4"
    assert form["txtSeatNo2"] == "5B"
    assert form["txtSrcarCnt1"] == "2"
    assert form["txtSrcarNo1_1"] == "7"
    assert form["txtSeatNo1_1"] == "1A"
    assert form["txtSrcarNo1_2"] == "7"
    assert form["txtSeatNo1_2"] == "1B"
    # OSrcar is the last @FieldMap, so nothing of it precedes the journey block.
    keys = list(form)
    assert keys.index("txtChgFlg2") < keys.index("txtSrcarCnt")


def test_seat_designation_needs_one_seat_per_passenger_on_every_leg():
    with pytest.raises(KorailProtocolError, match="one seat per"):
        build_transfer_reservation_form(
            KorailConfig(),
            _legs(),
            passengers=KorailPassengerCounts(adult=2),
            job_type=KorailReservationJobType.SEAT_DESIGNATED,
            seats=(
                (
                    KorailSeatAssignment(car_no=4, seat_no="5A"),
                    KorailSeatAssignment(car_no=4, seat_no="5B"),
                ),
                (KorailSeatAssignment(car_no=7, seat_no="1A"),),
            ),
        )


def test_seat_designation_needs_one_seat_list_per_leg():
    with pytest.raises(KorailProtocolError, match="one seat list per"):
        build_transfer_reservation_form(
            KorailConfig(),
            _legs(),
            job_type=KorailReservationJobType.SEAT_DESIGNATED,
            seats=((KorailSeatAssignment(car_no=4, seat_no="5A"),),),
        )


def test_non_designated_transfer_carries_no_osrcar_key():
    form = build_transfer_reservation_form(KorailConfig(), _legs())

    assert not any(
        key.startswith(prefix)
        for prefix in ("txtSrcarCnt", "txtSrcarNo", "txtSeatNo")
        for key in form
    )


def test_standing_flag_is_computed_per_itinerary_and_is_always_n_here():
    """``txtStndFlg`` on a transfer, and why it cannot come out ``"Y"``.

    ``C5/a.java:78-82`` makes the flag a property of the whole booking: leg 1
    assigns it and every later leg overwrites it only while it still reads
    ``"N"``, so one standing leg would make the itinerary standing. But
    ``S4/J.java:83-85``'s ``isStndSeat`` needs a leg whose general seats are
    매진 (``"13"``), and a 매진 leg is not bookable in the first place -- the
    app's ``U1()`` walks **every** leg of the selected itinerary
    (``a5/u.java:346-355`` over ``u4/a.java:103-105``'s full bundle list) and
    disables the 예약 button outright when any of them reads 매진 or 좌석부족
    (``a5/u.java:388-393``). The only job that tolerates 매진 is 예약대기, and
    that one does not exist for a transfer at all. So ``"Y"`` is unreachable
    here, and this pins that rather than leaving it implied.
    """
    first, second = _legs()
    sold_out_but_standing = replace(
        second,
        general_reservation_code="13",
        standing_reservation_code="11",
    )

    with pytest.raises(KorailProtocolError, match="available general seat"):
        build_transfer_reservation_form(
            KorailConfig(),
            (first, sold_out_but_standing),
        )

    assert build_transfer_reservation_form(
        KorailConfig(),
        (first, second),
    )["txtStndFlg"] == "N"


# --- what does not compose ---------------------------------------------------


def test_standby_is_refused_for_a_transfer_itinerary():
    # Two independent gates in the app: a5/k.java:120-127 returns false from the
    # standby check for any non-direct result, and the only setJobId("1102") is
    # DirectInquiryActivity.java:434, on a screen TransferInquiryActivity
    # overrides away.
    legs = tuple(
        replace(leg, wait_reservation_flag=KORAIL_STANDBY_WAIT_FLAG)
        for leg in _legs()
    )

    with pytest.raises(KorailProtocolError) as excinfo:
        build_transfer_reservation_form(
            KorailConfig(),
            legs,
            job_type=KorailReservationJobType.STANDBY,
        )

    message = str(excinfo.value)
    assert "직통" in message
    assert "a5/k.java:120-127" in message


def test_standby_still_works_for_a_single_leg():
    # The refusal above must be about the leg count and nothing else.
    form = build_reservation_form(
        KorailConfig(),
        replace(
            _first_leg(),
            general_reservation_code="13",
            wait_reservation_flag=KORAIL_STANDBY_WAIT_FLAG,
        ),
        job_type=KorailReservationJobType.STANDBY,
    )

    assert form["txtJobId"] == "1102"
    assert form["txtJrnyCnt"] == KORAIL_DIRECT_ITINERARY_CODE


# --- the search side ---------------------------------------------------------


def _search_form(*, transfer: bool, **kwargs) -> dict[str, str]:
    return build_train_search_form(
        KorailConfig(),
        TrainSearchQuery("0001", "0723", "20990101"),
        departure_name="서울",
        arrival_name="여수엑스포",
        sid="SYNTHETIC_SID",
        transfer=transfer,
        **kwargs,
    )


def test_transfer_search_moves_exactly_one_field():
    direct = _search_form(transfer=False)
    transfer = _search_form(transfer=True)

    assert list(direct) == list(transfer)
    assert {
        key for key in direct if direct[key] != transfer[key]
    } == {"radJobId"}
    assert direct["radJobId"] == KORAIL_DIRECT_ITINERARY_CODE == "1"
    assert transfer["radJobId"] == KORAIL_TRANSFER_ITINERARY_CODE == "2"


def test_transfer_search_sends_no_pinned_transfer_station_fields():
    # b5/c.java:154-160 sets chtnCnt/chtnRsStnCd1/trnGpCnt/trnGpCd1 only behind
    # the TRANSFER_CHTNRSSTNCD intent extra, a screen this client does not drive.
    transfer = _search_form(transfer=True)

    for key in ("chtnCnt", "chtnRsStnCd1", "trnGpCnt", "trnGpCd1"):
        assert key not in transfer


def test_direct_continuation_still_sends_the_empty_second_train_cursor():
    form = _search_form(
        transfer=False,
        continuation=TrainSearchContinuation(
            query_station_no="12",
            query_train_no="00777",
            page_count="10",
        ),
    )

    assert form["qryStTrnNo"] == "00777"
    assert form["qryStTrnNo2"] == ""


def test_transfer_continuation_sends_both_train_cursors():
    form = _search_form(
        transfer=True,
        continuation=TrainSearchContinuation(
            query_station_no="12",
            query_train_no="00777",
            page_count="10",
            query_train_no2="01513",
        ),
    )

    assert form["qryStTrnNo"] == "00777"
    assert form["qryStTrnNo2"] == "01513"


# --- the response shape ------------------------------------------------------


def test_itineraries_are_consecutive_pairs_of_a_flat_list():
    first, second = _legs()
    third = replace(first, train_no="00301")
    fourth = replace(second, train_no="01601")

    itineraries = pair_transfer_itineraries([first, second, third, fourth])

    assert len(itineraries) == 2
    assert itineraries[0] == TransferItinerary(first=first, second=second)
    assert itineraries[1] == TransferItinerary(first=third, second=fourth)
    assert itineraries[0].legs == (first, second)


def test_a_trailing_unpaired_row_is_dropped_the_way_the_app_drops_it():
    # a5/k.java:156-170 appends only on i % 2 == 1, so an odd tail never becomes
    # a bookable half-itinerary.
    first, second = _legs()

    assert pair_transfer_itineraries([first, second, replace(first, train_no="00301")]) == [
        TransferItinerary(first=first, second=second)
    ]
    assert pair_transfer_itineraries([first]) == []
    assert pair_transfer_itineraries([]) == []


def test_a_misaligned_sequence_marker_is_refused():
    first, second = _legs()
    both_second = replace(first, change_train_sequence=KORAIL_TRANSFER_ITINERARY_CODE)

    with pytest.raises(KorailProtocolError, match="h_chg_trn_seq"):
        pair_transfer_itineraries([both_second, second])


def test_absent_sequence_markers_are_accepted():
    # DirectInquiryActivity.java:194-195 and TransferInquiryActivity.java:44
    # both default a null marker from the row's position, so the app tolerates
    # its absence and so does this.
    first, second = (
        replace(leg, change_train_sequence=None) for leg in _legs()
    )

    assert pair_transfer_itineraries([first, second]) == [
        TransferItinerary(first=first, second=second)
    ]


def test_transfer_station_is_reported_only_when_the_legs_agree():
    first, second = _legs()

    assert TransferItinerary(first, second).transfer_station_code == "0501"
    # a5/u.java:947-956 prints two labels when they differ, so this is a real
    # itinerary shape rather than a parse failure.
    assert (
        TransferItinerary(
            first,
            replace(second, departure_station_code="0502"),
        ).transfer_station_code
        is None
    )


def test_transfer_next_page_prefers_the_transfer_cursor_pair():
    from korail_mobile_api import TrainSearchMetadata

    metadata = TrainSearchMetadata(
        next_page_flag="Y",
        next_query_station_no="12",
        next_train_no="00777",
        next_preceding_train_no="00888",
        next_connecting_train_no="00999",
        result_count="10",
    )
    result = TransferSearchResult(
        itineraries=[],
        trains=[],
        response=_envelope(),
        metadata=metadata,
    )

    cursor = result.next_page()
    assert cursor is not None
    assert cursor.query_station_no == "12"
    # setSelectTransferPages OVERWRITES qryStTrnNo with h_prcd_trn_no_next
    # (RsvInquiryRequest.java:212-215), so h_trn_no_next loses.
    assert cursor.query_train_no == "00888"
    assert cursor.query_train_no2 == "00999"


def test_transfer_next_page_falls_back_when_either_cursor_is_missing():
    from korail_mobile_api import TrainSearchMetadata

    # b5/c.java:192-194 requires BOTH non-empty before it overwrites.
    result = TransferSearchResult(
        itineraries=[],
        trains=[],
        response=_envelope(),
        metadata=TrainSearchMetadata(
            next_page_flag="Y",
            next_query_station_no="12",
            next_train_no="00777",
            next_preceding_train_no="00888",
            next_connecting_train_no="",
            result_count="10",
        ),
    )

    cursor = result.next_page()
    assert cursor is not None
    assert cursor.query_train_no == "00777"
    assert cursor.query_train_no2 == ""


def test_transfer_next_page_stops_on_the_apps_own_flag():
    from korail_mobile_api import TrainSearchMetadata

    result = TransferSearchResult(
        itineraries=[],
        trains=[],
        response=_envelope(),
        metadata=TrainSearchMetadata(
            next_page_flag="N",
            next_query_station_no="12",
            next_train_no="00777",
            result_count="10",
        ),
    )

    assert result.next_page() is None


def _envelope():
    from korail_mobile_api import BaseKorailResponse

    return BaseKorailResponse(
        h_msg_cd="IRG000000",
        h_msg_txt="synthetic",
        str_result="SUCC",
        raw={},
    )


# --- the client --------------------------------------------------------------


def _schedule_view_body(*rows: dict[str, str], next_page: str = "N") -> dict:
    return {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "synthetic",
        "strResult": "SUCC",
        "h_next_pg_flg": next_page,
        "trn_infos": {"trn_info": list(rows)},
    }


def _row(train_no: str, sequence: str, departure: str, arrival: str) -> dict:
    return {
        "h_trn_no": train_no,
        "h_trn_gp_cd": "100",
        "h_dpt_rs_stn_cd": departure,
        "h_arv_rs_stn_cd": arrival,
        "h_dpt_dt": "20990101",
        "h_dpt_tm": "100700",
        "h_arv_tm": "112400",
        "h_chg_trn_seq": sequence,
    }


TRANSFER_ROWS = (
    _row("00209", KORAIL_DIRECT_ITINERARY_CODE, "0001", "0501"),
    _row("01513", KORAIL_TRANSFER_ITINERARY_CODE, "0501", "0723"),
)

SCHEDULE_VIEW = "/classes/com.korail.mobile.seatMovie.ScheduleView"


def _capturing_client(responder):
    captured: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(
            {
                "path": request.url.path,
                "body": request.content.decode(),
            }
        )
        return responder(len(captured) - 1)

    return (
        KorailClient(KorailConfig(), transport=httpx.MockTransport(handler)),
        captured,
    )


def test_search_transfer_trains_posts_radjobid_two_and_pairs_the_rows():
    client, captured = _capturing_client(
        lambda index: httpx.Response(
            200,
            json=_schedule_view_body(*TRANSFER_ROWS),
        )
    )

    result = client.search_transfer_trains(
        TrainSearchQuery("서울", "여수엑스포", "20990101")
    )

    assert isinstance(result, TransferSearchResult)
    assert captured[0]["path"] == SCHEDULE_VIEW
    assert parse_qs(captured[0]["body"])["radJobId"] == ["2"]
    assert len(result.trains) == 2
    assert len(result.itineraries) == 1
    itinerary = result.itineraries[0]
    assert itinerary.first.train_no == "00209"
    assert itinerary.second.train_no == "01513"
    assert itinerary.transfer_station_code == "0501"


def test_direct_search_still_posts_radjobid_one():
    client, captured = _capturing_client(
        lambda index: httpx.Response(200, json=_schedule_view_body())
    )

    client.search_trains(TrainSearchQuery("서울", "여수엑스포", "20990101"))

    assert parse_qs(captured[0]["body"])["radJobId"] == ["1"]


def test_fallback_reissues_as_transfer_on_wrd000061_only():
    def responder(index: int) -> httpx.Response:
        if index == 0:
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "WRD000061",
                    "h_msg_txt": "직통열차가 없습니다.",
                    "strResult": "FAIL",
                },
            )
        return httpx.Response(200, json=_schedule_view_body(*TRANSFER_ROWS))

    client, captured = _capturing_client(responder)

    result = client.search_trains_with_transfer_fallback(
        TrainSearchQuery("서울", "여수엑스포", "20990101")
    )

    assert isinstance(result, TransferSearchResult)
    assert len(captured) == 2
    assert parse_qs(captured[0]["body"])["radJobId"] == ["1"]
    assert parse_qs(captured[1]["body"])["radJobId"] == ["2"]
    # DirectInquiryActivity.java:284-296 changes radJobId and nothing else.
    first = parse_qs(captured[0]["body"])
    second = parse_qs(captured[1]["body"])
    first.pop("radJobId")
    second.pop("radJobId")
    first.pop("Sid", None)
    second.pop("Sid", None)
    assert first == second


def test_fallback_returns_the_direct_result_when_there_is_one():
    client, captured = _capturing_client(
        lambda index: httpx.Response(
            200,
            json=_schedule_view_body(
                _row("00209", "", "0001", "0723"),
            ),
        )
    )

    result = client.search_trains_with_transfer_fallback(
        TrainSearchQuery("서울", "여수엑스포", "20990101")
    )

    assert isinstance(result, TrainSearchResult)
    assert len(captured) == 1


def test_fallback_does_not_swallow_any_other_failure():
    client, captured = _capturing_client(
        lambda index: httpx.Response(
            200,
            json={
                "h_msg_cd": "WRD000091",
                "h_msg_txt": "synthetic",
                "strResult": "FAIL",
            },
        )
    )

    with pytest.raises(Exception) as excinfo:
        client.search_trains_with_transfer_fallback(
            TrainSearchQuery("서울", "여수엑스포", "20990101")
        )

    assert not isinstance(excinfo.value, KorailNoDirectTrainError)
    assert len(captured) == 1


def test_reserve_transfer_previews_the_two_leg_form_without_sending():
    client = _logged_in_no_network_client()

    preview = client.reserve_transfer(
        _legs(),
        consent=MutationConsent(allow_reserve=True),
    )

    assert isinstance(preview, MutationPreview)
    assert preview.category == "reserve"
    assert preview.route == (
        "/classes/com.korail.mobile.certification.TicketReservation"
    )
    assert preview.payload["txtJrnyCnt"] == "2"
    assert preview.payload["txtJrnyTpCd2"] == "14"
    assert preview.payload["txtJrnySqno2"] == "002"


def test_reserve_transfer_needs_reserve_consent():
    from korail_mobile_api import KorailMutationNotAllowedError

    client = _logged_in_no_network_client()

    with pytest.raises(KorailMutationNotAllowedError):
        client.reserve_transfer(_legs(), consent=MutationConsent())


def test_reserve_transfer_needs_a_session():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("must not send")

    from korail_mobile_api.errors import KorailAuthError

    client = KorailClient(transport=httpx.MockTransport(handler))

    with pytest.raises(KorailAuthError):
        client.reserve_transfer(
            _legs(),
            consent=MutationConsent(allow_reserve=True),
        )


def test_single_leg_rejection_messages_are_unchanged():
    """Generalising the builder must not reword what an existing caller sees.

    ``build_reservation_form`` is now a one-leg call into a leg-sequence core,
    and the core's own messages talk about legs. The single-leg entry point
    keeps the sentences it has always raised.
    """
    with pytest.raises(
        KorailProtocolError,
        match=r"^KORAIL reservation requires an exact TrainSummary$",
    ):
        build_reservation_form(KorailConfig(), {"train_no": "00209"})
    with pytest.raises(
        KorailProtocolError,
        match=r"^KORAIL reservation requires an exact KorailPassengerCounts$",
    ):
        build_reservation_form(
            KorailConfig(),
            _first_leg(),
            passengers={"adult": 1},
        )


def test_cancel_accepts_a_two_journey_transfer_hold_and_echoes_its_count():
    """A 환승 hold must be cancelable, and the count is echoed not fixed.

    The app's own cancel of a just-created hold keeps txtJrnySqno and
    hidRsvChgNo constant but passes the hold's h_jrny_cnt straight through
    (DReservationConfirmActivity.java:269-278). Rejecting a two-journey hold
    here would leave a live transfer reservation with no way to release it.
    """
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.mutation_models import ReservationHoldResponse
    from korail_mobile_api.mutation_payloads import (
        build_unpaid_reservation_cancel_form,
    )

    config = KorailConfig()
    for raw_count, expected in (("2", "2"), ("0002", "2"), ("1", "1"), ("0001", "1")):
        hold = ReservationHoldResponse(
            h_msg_cd="IRR000018",
            h_msg_txt="",
            str_result="SUCC",
            raw={},
            pnr_no="399999999999999",
            journey_count=raw_count,
        )
        form = build_unpaid_reservation_cancel_form(config, hold)
        assert form["txtJrnyCnt"] == expected, raw_count
        # These two stay constant for a freshly created hold, whatever the legs.
        assert form["txtJrnySqno"] == "0001"
        assert form["hidRsvChgNo"] == "000"


def test_cancel_still_refuses_a_hold_with_no_usable_journey_count():
    from korail_mobile_api.config import KorailConfig
    from korail_mobile_api.errors import KorailProtocolError
    from korail_mobile_api.mutation_models import ReservationHoldResponse
    from korail_mobile_api.mutation_payloads import (
        build_unpaid_reservation_cancel_form,
    )

    config = KorailConfig()
    for bad in ("", "   ", "0", "abc", None):
        hold = ReservationHoldResponse(
            h_msg_cd="IRR000018",
            h_msg_txt="",
            str_result="SUCC",
            raw={},
            pnr_no="399999999999999",
            journey_count=bad,
        )
        with pytest.raises(KorailProtocolError):
            build_unpaid_reservation_cancel_form(config, hold)
