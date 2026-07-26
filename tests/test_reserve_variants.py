"""Offline tests for the seat-designated reservation job type.

Everything asserted here is read out of the decompiled app, not out of what the
builders happen to emit:

* ``txtJobId`` values -- ``C5/a.java:59`` ("1101") and ``C5/a.java:145``
  ("1103").
* the ``OSrcar`` key names, their journey-1 spellings and their 1-based seat
  index -- ``OSrcar.java:6-30`` and ``SeatSearchActivity.java:675-683``.
* that an ordinary hold sends none of them -- ``C5/a.java:118``
  (``getOSrcar().clear()``) plus the ``@FieldMap`` on
  ``CertificationService.java:52-54``.
* the seat-count rule -- ``SeatSearchActivity.java:902`` (done button enabled
  only while ``selectedSeatCount == G0()``) and ``:273-278`` (``G0()`` is
  ``txtTotPsgCnt``).

NOTHING here has been transmitted to the live server.
"""

from __future__ import annotations

import httpx
import pytest

from korail_mobile_api import (
    KorailClient,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailSeatAssignment,
    KorailSession,
    MutationConsent,
    MutationPreview,
    PhysicalSeat,
    SeatInventoryResponse,
    TrainSummary,
    KorailConfig,
)
from korail_mobile_api.mutation_payloads import (
    build_reservation_form,
    build_single_adult_reservation_form,
)


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


def test_job_type_values_are_the_apps_job_ids():
    assert KorailReservationJobType.IMMEDIATE.value == "1101"
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


def test_an_ordinary_hold_omits_every_osrcar_key():
    # C5/a.java:118 clears OSrcar, and an empty @FieldMap contributes no fields
    # at all -- so there is no txtSrcarCnt="0" on the wire. srtgo sends one
    # unconditionally; the app never does.
    form = build_reservation_form(
        KorailConfig(),
        _eligible_train(),
        job_type=KorailReservationJobType.IMMEDIATE,
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


def test_seats_are_refused_on_a_job_that_does_not_designate_them():
    with pytest.raises(KorailProtocolError):
        build_reservation_form(
            KorailConfig(),
            _eligible_train(),
            job_type=KorailReservationJobType.IMMEDIATE,
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


# --- client-level preview -----------------------------------------------------


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
