"""Offline tests for the two non-default reservation job types.

Everything asserted here is read out of the decompiled app, not out of what the
builders happen to emit:

* ``txtJobId`` values -- ``C5/a.java:59`` ("1101"),
  ``DirectInquiryActivity.java:434`` ("1102"), ``C5/a.java:145`` ("1103").
* the ``OSrcar`` key names, their journey-1 spellings and their 1-based seat
  index -- ``OSrcar.java:6-30`` and ``SeatSearchActivity.java:675-683``.
* that an ordinary hold sends none of them -- ``C5/a.java:118``
  (``getOSrcar().clear()``) plus the ``@FieldMap`` on
  ``CertificationService.java:52-54``.
* the seat-count rule -- ``SeatSearchActivity.java:902`` (done button enabled
  only while ``selectedSeatCount == G0()``) and ``:273-278`` (``G0()`` is
  ``txtTotPsgCnt``).
* standby eligibility -- ``analysis/apktool/smali/U4/a.smali:1250-1290`` and
  ``:1969-1981``, ``a5/k.java:120-126``, ``a5/u.java:371``.
* standby being members-only -- ``ReservationRequest.java:105-119`` via
  ``BaseActivity.java:350``.
* the follow-up call's fields -- ``ReservationWaitService.java:10-12`` and
  ``ReservationWaitActivity.java:147-155, 213-228``.

NOTHING here has been transmitted to the live server.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import httpx
import pytest

from korail_mobile_api import (
    KORAIL_STANDBY_HOLD_MESSAGE_CODE,
    KORAIL_STANDBY_WAIT_FLAG,
    KorailClient,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailSeatAssignment,
    KorailSeatClass,
    KorailSession,
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    PhysicalSeat,
    ReservationHoldResponse,
    SeatInventoryResponse,
    TrainSummary,
    KorailConfig,
)
from korail_mobile_api.errors import KorailAuthError
from korail_mobile_api.mutation_payloads import (
    build_reservation_form,
    build_single_adult_reservation_form,
    build_standby_wait_form,
)
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


RESERVATION_WAIT_PATH = "/classes/com.korail.mobile.reservationWait.ReservationWait"

# The OSrcar key prefixes a seat-designated hold adds, and an ordinary hold must
# never carry. OSrcar.java:7-12 declares exactly these six names (three for
# journey 1, three for journey 2); this package books one journey.
OSRCAR_PREFIXES = ("txtSrcarCnt", "txtSrcarNo", "txtSeatNo")


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


def _sold_out_standby_train() -> TrainSummary:
    """What the operator will actually meet: 매진 but standby-eligible.

    ``h_gen_rsv_cd="13"`` is 매진 (``U4/a.smali`` compares against "13" to write
    the 매진 label), and ``h_wait_rsv_flg=" 9"`` is the flag that turns the
    예약대기 button on.
    """
    return replace(
        _eligible_train(),
        general_reservation_code="13",
        wait_reservation_flag=KORAIL_STANDBY_WAIT_FLAG,
    )


def _standby_eligible_train() -> TrainSummary:
    """Standby-eligible AND bookable, so the two job ids stay comparable."""
    return replace(
        _eligible_train(),
        wait_reservation_flag=KORAIL_STANDBY_WAIT_FLAG,
    )


def _seat(seat_no: str, *, sale_possible: str = "Y") -> PhysicalSeat:
    return PhysicalSeat(
        seat_no=seat_no,
        sale_possible=sale_possible,
        direction_code="SYNTHETIC",
        other_attribute_code="SYNTHETIC",
        requested_attribute_code="015",
        floor=None,
        # Deliberately different from seat_no: the wire value is seat_no, and
        # seat_spec is only the label SeatSearchActivity.java:894 renders.
        specification="5A",
        sequence_no="1",
        message_code="SYNTHETIC",
        message="synthetic",
        visual_message_division_code="SYNTHETIC",
    )


def _inventory(*seats: PhysicalSeat, car_no: int | None = 4) -> SeatInventoryResponse:
    return SeatInventoryResponse(
        h_msg_cd="IRG000000",
        h_msg_txt="synthetic",
        str_result="SUCC",
        raw={},
        layout_type=3,
        arrangement_code="SYNTHETIC",
        remaining_count=len(seats),
        total_count=len(seats),
        seats=tuple(seats),
        windows=(),
        car_no=car_no,
    )


def _standby_hold(
    *,
    h_msg_cd: str = KORAIL_STANDBY_HOLD_MESSAGE_CODE,
    str_result: str = "SUCC",
    pnr_no: str | None = "SYNTHETIC_PNR",
) -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd=h_msg_cd,
        h_msg_txt="synthetic",
        str_result=str_result,
        raw={},
        pnr_no=pnr_no,
        journey_count="0001",
    )


def _logged_in_no_network_client() -> KorailClient:
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError(
            f"a dry run must not send a request (saw {request.method} "
            f"{request.url.path})"
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client


# --- job ids -----------------------------------------------------------------


def test_job_type_values_are_the_apps_three_job_ids():
    assert KorailReservationJobType.IMMEDIATE.value == "1101"
    assert KorailReservationJobType.STANDBY.value == "1102"
    assert KorailReservationJobType.SEAT_DESIGNATED.value == "1103"


def test_default_job_type_reproduces_the_pinned_single_adult_form_exactly():
    config = KorailConfig()
    train = _eligible_train()

    defaulted = build_reservation_form(config, train)
    explicit = build_reservation_form(
        config,
        train,
        job_type=KorailReservationJobType.IMMEDIATE,
    )
    pinned = build_single_adult_reservation_form(config, train)

    assert defaulted == explicit == pinned
    assert list(defaulted) == list(explicit) == list(pinned)


def test_unknown_job_type_is_refused_before_anything_is_built():
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            _eligible_train(),
            job_type="1202",  # type: ignore[arg-type]
        )


# --- A. seat-designated (1103) wire keys -------------------------------------


def _designated_form(
    *,
    passengers: KorailPassengerCounts,
    seats: tuple[KorailSeatAssignment, ...],
    train: TrainSummary | None = None,
) -> dict[str, str]:
    return build_reservation_form(
        KorailConfig(),
        train or _eligible_train(),
        passengers=passengers,
        job_type=KorailReservationJobType.SEAT_DESIGNATED,
        seats=seats,
    )


def test_seat_designated_form_adds_exactly_the_apps_osrcar_keys():
    config = KorailConfig()
    train = _eligible_train()
    passengers = KorailPassengerCounts(adult=2)
    seats = (
        KorailSeatAssignment(car_no=4, seat_no="5A"),
        KorailSeatAssignment(car_no=4, seat_no="5B"),
    )

    ordinary = build_reservation_form(config, train, passengers=passengers)
    designated = _designated_form(passengers=passengers, seats=seats)

    # Everything but the job id and the OSrcar map is identical.
    added = set(designated) - set(ordinary)
    assert added == {
        "txtSrcarCnt",
        "txtSrcarNo1",
        "txtSeatNo1",
        "txtSrcarNo2",
        "txtSeatNo2",
    }
    assert not set(ordinary) - set(designated)
    assert designated["txtJobId"] == "1103"
    assert ordinary["txtJobId"] == "1101"
    assert {
        key: value
        for key, value in designated.items()
        if key not in added and key != "txtJobId"
    } == {
        key: value for key, value in ordinary.items() if key != "txtJobId"
    }
    # The values, spelled out: txtSrcarCnt is the SEAT count
    # (SeatSearchActivity.java:676 sends selectedSeatList.size()), and the pairs
    # are (car, seat) in selection order.
    assert designated["txtSrcarCnt"] == "2"
    assert designated["txtSrcarNo1"] == "4"
    assert designated["txtSeatNo1"] == "5A"
    assert designated["txtSrcarNo2"] == "4"
    assert designated["txtSeatNo2"] == "5B"


def test_seat_designated_keys_follow_the_journey_keys_in_wire_order():
    # OSrcar is the last @FieldMap on the Retrofit call
    # (CertificationService.java:52-54), so no OSrcar key may precede the
    # journey block's final field.
    designated = _designated_form(
        passengers=KorailPassengerCounts(adult=1),
        seats=(KorailSeatAssignment(car_no=4, seat_no="5A"),),
    )
    keys = list(designated)
    assert keys[-4:] == [
        "txtChgFlg1",
        "txtSrcarCnt",
        "txtSrcarNo1",
        "txtSeatNo1",
    ]


def test_seat_designated_seat_index_starts_at_one():
    designated = _designated_form(
        passengers=KorailPassengerCounts(adult=3),
        seats=(
            KorailSeatAssignment(car_no=4, seat_no="5A"),
            KorailSeatAssignment(car_no=4, seat_no="5B"),
            KorailSeatAssignment(car_no=4, seat_no="5C"),
        ),
    )
    assert "txtSrcarNo0" not in designated
    assert "txtSeatNo0" not in designated
    assert {"txtSrcarNo1", "txtSrcarNo2", "txtSrcarNo3"} <= set(designated)
    assert {"txtSeatNo1", "txtSeatNo2", "txtSeatNo3"} <= set(designated)
    assert "txtSrcarNo4" not in designated
    # The count is the number of seats, not the number of distinct cars: all
    # three seats share car 4 and the count is still "3".
    assert designated["txtSrcarCnt"] == "3"


def test_seat_designated_count_is_seats_not_cars_across_cars():
    designated = _designated_form(
        passengers=KorailPassengerCounts(adult=2),
        seats=(
            KorailSeatAssignment(car_no=4, seat_no="5A"),
            KorailSeatAssignment(car_no=7, seat_no="1A"),
        ),
    )
    assert designated["txtSrcarCnt"] == "2"
    assert designated["txtSrcarNo1"] == "4"
    assert designated["txtSrcarNo2"] == "7"


def test_journey_two_osrcar_spellings_are_never_emitted():
    # OSrcar.java:8,10,12 spell journey 2 as txtSeatNo1_/txtSrcarCnt1/
    # txtSrcarNo1_. This package books exactly one journey (txtJrnyCnt="1"), so
    # those must never appear.
    designated = _designated_form(
        passengers=KorailPassengerCounts(adult=1),
        seats=(KorailSeatAssignment(car_no=4, seat_no="5A"),),
    )
    assert "txtSrcarCnt1" not in designated
    assert not any(key.startswith("txtSrcarNo1_") for key in designated)
    assert not any(key.startswith("txtSeatNo1_") for key in designated)


@pytest.mark.parametrize(
    "job_type",
    [KorailReservationJobType.IMMEDIATE, KorailReservationJobType.STANDBY],
)
def test_non_designated_jobs_omit_every_osrcar_key(job_type):
    # C5/a.java:118 clears OSrcar, and an empty @FieldMap contributes no fields
    # at all -- so there is no txtSrcarCnt="0" on the wire. srtgo sends one
    # unconditionally; the app never does.
    form = build_reservation_form(
        KorailConfig(),
        _standby_eligible_train(),
        job_type=job_type,
    )
    assert not [
        key
        for key in form
        if any(key.startswith(prefix) for prefix in OSRCAR_PREFIXES)
    ]
    assert "txtSrcarCnt" not in form


# --- A. seat count vs passenger count ----------------------------------------


@pytest.mark.parametrize(
    ("passengers", "seat_count"),
    [
        (KorailPassengerCounts(adult=2), 1),  # short: a half-booked hold
        (KorailPassengerCounts(adult=1), 2),  # long
        (KorailPassengerCounts(adult=1), 0),  # empty list
        (KorailPassengerCounts(adult=2, infant=1), 2),  # 동반유아 counts too
    ],
)
def test_seat_designated_rejects_a_seat_count_that_is_not_the_passenger_total(
    passengers,
    seat_count,
):
    seats = tuple(
        KorailSeatAssignment(car_no=4, seat_no=f"5{chr(ord('A') + index)}")
        for index in range(seat_count)
    )
    with pytest.raises(KorailProtocolError):
        _designated_form(passengers=passengers, seats=seats)


def test_seat_designated_counts_every_passenger_row_including_infants():
    # G0() is txtTotPsgCnt (SeatSearchActivity.java:277), and txtTotPsgCnt is
    # every counter summed, 동반유아 and 안내견 included (m5/c.java:330).
    passengers = KorailPassengerCounts(adult=2, infant=1)
    seats = tuple(
        KorailSeatAssignment(car_no=4, seat_no=f"5{letter}")
        for letter in ("A", "B", "C")
    )
    form = _designated_form(passengers=passengers, seats=seats)
    assert form["txtTotPsgCnt"] == "3"
    assert form["txtSrcarCnt"] == "3"


def test_seat_designated_rejects_the_same_seat_twice():
    with pytest.raises(KorailProtocolError):
        _designated_form(
            passengers=KorailPassengerCounts(adult=2),
            seats=(
                KorailSeatAssignment(car_no=4, seat_no="5A"),
                KorailSeatAssignment(car_no=4, seat_no="5A"),
            ),
        )


def test_seat_designated_without_seats_is_refused():
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            _eligible_train(),
            job_type=KorailReservationJobType.SEAT_DESIGNATED,
        )


@pytest.mark.parametrize(
    "job_type",
    [KorailReservationJobType.IMMEDIATE, KorailReservationJobType.STANDBY],
)
def test_seats_are_refused_on_a_job_that_does_not_designate_them(job_type):
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            _standby_eligible_train(),
            job_type=job_type,
            seats=(KorailSeatAssignment(car_no=4, seat_no="5A"),),
        )


def test_seat_designated_refuses_a_foreign_seat_value():
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            _eligible_train(),
            job_type=KorailReservationJobType.SEAT_DESIGNATED,
            seats=[("4", "5A")],  # type: ignore[list-item]
        )


# --- A. the identifiers come from the seat-inventory reads -------------------


def test_seat_assignment_takes_both_identifiers_from_an_inventory_read():
    seat = _seat("SYNTHETIC-SEAT-01")
    inventory = _inventory(seat, car_no=4)

    assignment = KorailSeatAssignment.from_inventory(inventory, seat)

    # scar_no -> SeatInventoryResponse.car_no, seat_no -> PhysicalSeat.seat_no.
    assert assignment.car_no == inventory.car_no == 4
    assert assignment.seat_no == seat.seat_no == "SYNTHETIC-SEAT-01"
    # NOT the human label the app renders.
    assert assignment.seat_no != seat.specification

    form = _designated_form(
        passengers=KorailPassengerCounts(adult=1),
        seats=(assignment,),
    )
    assert form["txtSrcarNo1"] == "4"
    assert form["txtSeatNo1"] == "SYNTHETIC-SEAT-01"


def test_seat_assignment_refuses_a_seat_the_read_marked_unsellable():
    seat = _seat("SYNTHETIC-SEAT-02", sale_possible="N")
    inventory = _inventory(seat)
    with pytest.raises(ValueError):
        KorailSeatAssignment.from_inventory(inventory, seat)


def test_seat_assignment_refuses_a_seat_from_another_car():
    inventory = _inventory(_seat("SYNTHETIC-SEAT-01"))
    with pytest.raises(ValueError):
        KorailSeatAssignment.from_inventory(
            inventory,
            _seat("SYNTHETIC-SEAT-99"),
        )


def test_seat_assignment_refuses_an_inventory_without_a_car_number():
    seat = _seat("SYNTHETIC-SEAT-01")
    with pytest.raises(ValueError):
        KorailSeatAssignment.from_inventory(_inventory(seat, car_no=None), seat)


@pytest.mark.parametrize(
    ("car_no", "seat_no"),
    [
        (0, "5A"),
        (-1, "5A"),
        (True, "5A"),
        ("4", "5A"),
        (4, ""),
        (4, "5 A"),
        (4, "5\nA"),
        (4, "5Å"),
        (4, 5),
    ],
)
def test_seat_assignment_rejects_an_unusable_identifier(car_no, seat_no):
    with pytest.raises(ValueError):
        KorailSeatAssignment(car_no=car_no, seat_no=seat_no)


# --- client-level previews for both variants ---------------------------------


def test_reserve_seat_designated_dry_run_previews_the_osrcar_keys_redacted():
    client = _logged_in_no_network_client()
    preview = client.reserve(
        _eligible_train(),
        consent=MutationConsent(allow_reserve=True),
        passengers=KorailPassengerCounts(adult=2),
        job_type=KorailReservationJobType.SEAT_DESIGNATED,
        seats=(
            KorailSeatAssignment(car_no=4, seat_no="5A"),
            KorailSeatAssignment(car_no=4, seat_no="5B"),
        ),
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "reserve"
    assert preview.route.endswith("certification.TicketReservation")
    assert preview.payload["txtJobId"] == "1103"
    assert preview.payload["txtSrcarCnt"] == "2"
    # The seat identity is PII-adjacent and redacted like every other seat read.
    assert preview.payload["txtSrcarNo1"] == "[REDACTED]"
    assert preview.payload["txtSeatNo1"] == "[REDACTED]"


def test_reserve_with_no_job_type_is_unchanged_at_the_client_surface():
    client = _logged_in_no_network_client()
    train = _eligible_train()
    consent = MutationConsent(allow_reserve=True)

    defaulted = client.reserve(train, consent=consent)
    explicit = client.reserve(
        train,
        consent=consent,
        job_type=KorailReservationJobType.IMMEDIATE,
        seats=None,
    )
    assert isinstance(defaulted, MutationPreview)
    assert isinstance(explicit, MutationPreview)
    assert defaulted.payload == explicit.payload
    assert list(defaulted.payload) == list(explicit.payload)
    assert defaulted.payload["txtJobId"] == "1101"


# --- B. standby (1102) -------------------------------------------------------


def test_standby_changes_only_the_job_id_on_an_otherwise_bookable_train():
    config = KorailConfig()
    train = _standby_eligible_train()

    immediate = build_reservation_form(config, train)
    standby = build_reservation_form(
        config,
        train,
        job_type=KorailReservationJobType.STANDBY,
    )

    assert standby["txtJobId"] == "1102"
    assert list(standby) == list(immediate)
    assert {key: value for key, value in standby.items() if key != "txtJobId"} == {
        key: value for key, value in immediate.items() if key != "txtJobId"
    }


def test_standby_is_usable_on_a_sold_out_train_that_refuses_an_ordinary_hold():
    config = KorailConfig()
    train = _sold_out_standby_train()

    # The whole point: 매진, so the ordinary hold is refused...
    with pytest.raises(KorailProtocolError):
        build_reservation_form(config, train)

    # ...and standby is not.
    standby = build_reservation_form(
        config,
        train,
        job_type=KorailReservationJobType.STANDBY,
    )
    assert standby["txtJobId"] == "1102"


@pytest.mark.parametrize(
    "flag",
    [None, "", "9", "0", " 0", "-2", "N", "Y", "9 ", "  9"],
)
def test_standby_requires_the_apps_exact_wait_flag(flag):
    # smali/U4/a.smali:1262 compares against the literal " 9" and nothing else.
    # korail2.py:196-199's -2 / 0 have no support anywhere in this app.
    train = replace(_sold_out_standby_train(), wait_reservation_flag=flag)
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            train,
            job_type=KorailReservationJobType.STANDBY,
        )


def test_the_wait_flag_constant_is_the_two_character_literal():
    assert KORAIL_STANDBY_WAIT_FLAG == " 9"
    assert len(KORAIL_STANDBY_WAIT_FLAG) == 2


def test_standby_is_general_cabin_only():
    # U4.a.b() writes the "wait" bundle flag on the standard-cabin bundle only
    # (smali/U4/a.smali:1969-1981), and a5/u.java:371 requires the selected tab
    # to be K4.o.GENERAL.
    train = replace(
        _sold_out_standby_train(),
        special_reservation_code="11",
    )
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            train,
            job_type=KorailReservationJobType.STANDBY,
            seat_class=KorailSeatClass.SPECIAL,
        )


@pytest.mark.parametrize(
    ("general", "standing", "expected"),
    [
        ("13", "11", "Y"),  # 매진 + 입석 open -> the app sends "Y"
        ("13", "13", "N"),
        ("13", None, "N"),
        ("11", "11", "N"),  # not 매진, so not a standing request
    ],
)
def test_standby_computes_the_standing_flag_the_way_the_app_does(
    general,
    standing,
    expected,
):
    # S4/J.java:83-84's isStndSeat, fed into the request at c5/b.java:69.
    train = replace(
        _sold_out_standby_train(),
        general_reservation_code=general,
        standing_reservation_code=standing,
    )
    form = build_reservation_form(
        KorailConfig(),
        train,
        job_type=KorailReservationJobType.STANDBY,
    )
    assert form["txtStndFlg"] == expected


def test_an_ordinary_hold_still_pins_the_standing_flag_to_no():
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    assert form["txtStndFlg"] == "N"


def test_standby_works_with_a_passenger_mix_and_keeps_the_cabin_code():
    form = build_reservation_form(
        KorailConfig(),
        _sold_out_standby_train(),
        passengers=KorailPassengerCounts(adult=2, child=1),
        job_type=KorailReservationJobType.STANDBY,
    )
    assert form["txtTotPsgCnt"] == "3"
    assert form["txtCompaCnt1"] == "2"
    assert form["txtCompaCnt3"] == "1"
    assert form["txtPsrmClCd1"] == KorailSeatClass.GENERAL.value


def test_standby_is_members_only_and_carries_no_non_member_identity():
    # ReservationRequest.java:110-113 makes isNonmemberNotEnable() true for
    # "1102", and BaseActivity.java:350 passes its negation as "may this
    # request be retried as a non-member". So a standby request is never a
    # non-member request, and the three non-member @Fields
    # (CertificationService.java:49-50: txtCustNm / txtCpNo / txtCustPw) are
    # not part of its form.
    form = build_reservation_form(
        KorailConfig(),
        _sold_out_standby_train(),
        job_type=KorailReservationJobType.STANDBY,
    )
    assert "txtCustNm" not in form
    assert "txtCpNo" not in form
    assert "txtCustPw" not in form


def test_standby_reserve_requires_a_logged_in_member_session():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no request may be sent")

    client = KorailClient(transport=httpx.MockTransport(handler))
    with pytest.raises(KorailAuthError):
        client.reserve(
            _sold_out_standby_train(),
            consent=MutationConsent(allow_reserve=True),
            job_type=KorailReservationJobType.STANDBY,
        )


# --- B. the 예약대기 follow-up call ------------------------------------------


def test_standby_wait_form_matches_the_app_contract_exactly():
    form = build_standby_wait_form(
        KorailConfig(),
        _standby_hold(),
        allow_seat_class_change=True,
        sms_notify=True,
        phone_no="01012345678",
    )
    assert form == {
        "Device": "AD",
        "Version": "250601003",
        "Key": "korail1234567890",
        "txtPnrNo": "SYNTHETIC_PNR",
        "txtPsrmClChgFlg": "Y",
        "txtSmsSndFlg": "Y",
        "txtCpNo": "01012345678",
    }
    # RsvWaitDao.executeDao() passes them in exactly this order.
    assert list(form) == [
        "Device",
        "Version",
        "Key",
        "txtPnrNo",
        "txtPsrmClChgFlg",
        "txtSmsSndFlg",
        "txtCpNo",
    ]


def test_standby_wait_form_defaults_to_both_boxes_unchecked_and_no_phone():
    form = build_standby_wait_form(KorailConfig(), _standby_hold())
    assert form["txtPsrmClChgFlg"] == "N"
    assert form["txtSmsSndFlg"] == "N"
    # ReservationWaitActivity.java:220-227 only ever sets PHONE_NO when the SMS
    # box is checked; the getter then returns null and Retrofit omits the field.
    assert "txtCpNo" not in form


@pytest.mark.parametrize(
    "phone_no",
    [None, "", "010123456", "0101234567890", "010-1234-5678", "01O12345678"],
)
def test_standby_wait_form_requires_a_ten_or_eleven_digit_phone_for_sms(phone_no):
    with pytest.raises(KorailProtocolError):
        build_standby_wait_form(
            KorailConfig(),
            _standby_hold(),
            sms_notify=True,
            phone_no=phone_no,
        )


def test_standby_wait_form_refuses_a_phone_number_it_would_silently_drop():
    with pytest.raises(KorailProtocolError):
        build_standby_wait_form(
            KorailConfig(),
            _standby_hold(),
            sms_notify=False,
            phone_no="01012345678",
        )


@pytest.mark.parametrize(
    "hold",
    [
        _standby_hold(str_result="FAIL"),
        _standby_hold(pnr_no=None),
        _standby_hold(pnr_no="   "),
    ],
)
def test_standby_wait_form_requires_a_successful_hold_with_a_pnr(hold):
    with pytest.raises(KorailProtocolError):
        build_standby_wait_form(KorailConfig(), hold)


@pytest.mark.parametrize(
    "h_msg_cd",
    [KORAIL_STANDBY_HOLD_MESSAGE_CODE, "WRR664296", "IRR000018", None],
)
def test_standby_wait_form_never_treats_an_advisory_code_as_failure(h_msg_cd):
    # A hold that came back SUCC with a PNR is a real hold whatever advisory
    # code rode along -- WRR664296 (weekend discount notice) was observed live
    # on a perfectly cancelable reservation.
    form = build_standby_wait_form(
        KorailConfig(),
        _standby_hold(h_msg_cd=h_msg_cd),
    )
    assert form["txtPnrNo"] == "SYNTHETIC_PNR"


def test_standby_hold_message_code_constant_is_the_apps_routing_code():
    assert KORAIL_STANDBY_HOLD_MESSAGE_CODE == "IRR000014"


# --- B. gating of the follow-up call -----------------------------------------


def test_reservation_wait_is_a_gated_reserve_category_mutation_route():
    assert ("POST", RESERVATION_WAIT_PATH) in KORAIL_MUTATION_ROUTES
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[RESERVATION_WAIT_PATH] == "reserve"
    assert ("POST", RESERVATION_WAIT_PATH) not in KORAIL_READ_ONLY_ROUTES
    # It is a mutation route, so the READ path refuses it outright...
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", RESERVATION_WAIT_PATH)
    # ...the mutation path accepts it...
    assert_mutation_route("POST", RESERVATION_WAIT_PATH)
    assert_mutation_route_category(RESERVATION_WAIT_PATH, "reserve")
    # ...and a consent for a different category cannot be pointed at it.
    for category in ("payment", "cancel", "refund"):
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(RESERVATION_WAIT_PATH, category)


def test_confirm_standby_hold_is_denied_without_a_reserve_consent():
    client = _logged_in_no_network_client()
    for consent in (MutationConsent(), None, MutationConsent(allow_cancel=True)):
        with pytest.raises(MutationNotAllowedError):
            client.confirm_standby_hold(
                _standby_hold(),
                consent=consent,  # type: ignore[arg-type]
            )


def test_confirm_standby_hold_requires_an_authenticated_session():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no request may be sent")

    client = KorailClient(transport=httpx.MockTransport(handler))
    with pytest.raises(KorailAuthError):
        client.confirm_standby_hold(
            _standby_hold(),
            consent=MutationConsent(allow_reserve=True),
        )


def test_confirm_standby_hold_dry_run_previews_without_sending():
    client = _logged_in_no_network_client()
    preview = client.confirm_standby_hold(
        _standby_hold(),
        consent=MutationConsent(allow_reserve=True),
        sms_notify=True,
        phone_no="01012345678",
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "reserve"
    assert preview.method == "POST"
    assert preview.route == RESERVATION_WAIT_PATH
    assert preview.note == "dry-run: not sent"
    assert preview.payload["txtSmsSndFlg"] == "Y"
    assert preview.payload["txtPsrmClChgFlg"] == "N"
    # The PNR and the phone number never survive into a preview.
    assert preview.payload["txtPnrNo"] == "[REDACTED]"
    assert preview.payload["txtCpNo"] == "[REDACTED]"
    assert "01012345678" not in str(preview.payload)


def test_reserve_standby_dry_run_previews_the_standby_job_id():
    client = _logged_in_no_network_client()
    preview = client.reserve(
        _sold_out_standby_train(),
        consent=MutationConsent(allow_reserve=True),
        job_type=KorailReservationJobType.STANDBY,
    )
    assert isinstance(preview, MutationPreview)
    assert preview.payload["txtJobId"] == "1102"
    assert "txtSrcarCnt" not in preview.payload


# --- documentation contract -------------------------------------------------


def test_docs_record_the_live_verification_of_both_variants():
    """Pin what the 2026-07-26 runs established, and the trap they exposed.

    This replaces an assertion that neither variant was live-verified. That
    claim was true when written and is now false, so the pin moves to the new
    facts rather than being deleted: a reader must still be able to tell what
    was actually exercised, and must still be warned that a booked seat is
    compared by ``seat_spec`` and not by ``seat_no``.
    """
    root = Path(__file__).parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    handoff = (root / "docs" / "MUTATION_HANDOFF.md").read_text(encoding="utf-8")
    combined = f"{readme}\n{changelog}\n{handoff}"

    # The confirmation codes each variant actually returned.
    assert "IRR000014" in combined
    assert "IRZ000003" in combined
    # The seat-identifier trap: seat_no is sent, seat_spec is echoed back.
    for doc in (readme, changelog, handoff):
        assert "seat_spec" in doc
    assert "2026-07-26" in combined
    # Nothing may claim the variants are unverified any more.
    for stale in (
        "Neither variant has been live-verified",
        "Neither new variant has been live-verified",
    ):
        assert stale not in combined

    for claim in (
        "KorailReservationJobType",
        "KorailSeatAssignment",
        "confirm_standby_hold",
        "txtSrcarCnt",
        "members-only",
        "ERR299943",
        "WRR664296",
    ):
        assert claim in combined
