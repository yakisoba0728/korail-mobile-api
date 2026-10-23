"""Optional convenience behavior keeps original responses and mutation request budgets."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from datetime import datetime
from typing import Any
from unittest.mock import Mock

import pytest
from conftest import synthetic_config, wire_form, wire_pairs

from korail_mobile_api import (
    BaseKorailResponse,
    HoldReference,
    Korail,
    KorailInvalidInputError,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailReserveOption,
    KorailSeatAssignment,
    KorailSeatClass,
    ReservationHoldResponse,
    ReservationResource,
    TrainSearchMetadata,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
)


def _train(**changes: Any) -> TrainSummary:
    return replace(
        TrainSummary(
            train_no="90001",
            train_group_code="100",
            train_class_code="0A",
            run_date="20990102",
            departure_station_code="9901",
            arrival_station_code="9903",
            departure_construction_order="003",
            arrival_construction_order="009",
            departure_run_order="002",
            arrival_run_order="007",
            train_class_name="KTX",
            departure_station_name="출발시험역",
            arrival_station_name="도착시험역",
            departure_date="20990102",
            departure_time="090000",
            arrival_date="20990102",
            arrival_time="123000",
            general_reservation_code="11",
            special_reservation_code="13",
            wait_reservation_flag="0",
        ),
        **changes,
    )


@pytest.fixture
def korail() -> Iterator[Korail]:
    with Korail(synthetic_config(netfunnel_enabled=False), validate_stations=False) as value:
        yield value


@pytest.mark.parametrize(
    "include_no_seats, include_waiting_list, expected",
    [
        (True, False, ["1", "2", "3", "4", "5"]),
        (True, True, ["1", "2", "3", "4", "5"]),
        (False, False, ["1", "2"]),
        (False, True, ["1", "2", "3"]),
    ],
)
def test_filters_are_optional_and_keep_source_response(
    monkeypatch: pytest.MonkeyPatch,
    korail: Korail,
    include_no_seats: bool,
    include_waiting_list: bool,
    expected: list[str],
) -> None:
    trains = [
        _train(train_no="1"),
        _train(train_no="2", general_reservation_code="13", special_reservation_code="11"),
        _train(train_no="3", general_reservation_code="13", wait_reservation_flag=" 9"),
        _train(train_no="4", general_reservation_code="13"),
        _train(train_no="5", general_reservation_code=None, special_reservation_code=None),
    ]
    raw: dict[str, object] = {"extra": {"preserved": True}}
    original = TrainSearchResult(
        trains=trains, response=BaseKorailResponse(str_result="SUCC", raw=raw), raw=raw
    )
    search = Mock(return_value=original)
    monkeypatch.setattr(korail.client, "search_trains", search)
    result = korail.trains.search(
        "출발시험역",
        "도착시험역",
        depart_after=datetime(2099, 1, 2),
        include_no_seats=include_no_seats,
        include_waiting_list=include_waiting_list,
    )
    assert [train.train_no for train in result.trains] == expected
    assert result.raw is raw and result.response is original.response and result.metadata is original.metadata
    assert original.trains is trains and len(original.trains) == 5 and search.call_count == 1
    assert result.unfiltered_trains is (None if include_no_seats else trains)
    if include_no_seats:
        assert result is original


@pytest.mark.parametrize("page", ["sold-out", "available", "empty"])
def test_filter_preserves_cursor_and_last_server_departure(
    monkeypatch: pytest.MonkeyPatch, korail: Korail, page: str
) -> None:
    first = _train(general_reservation_code="11" if page == "available" else "13")
    last = _train(train_no="90002", general_reservation_code="13", departure_time="230000")
    original = TrainSearchResult(
        trains=[] if page == "empty" else [first, last],
        response=BaseKorailResponse(str_result="SUCC"),
        metadata=TrainSearchMetadata(next_page_flag="Y", next_query_station_no="0001", next_train_no="90002"),
    )
    monkeypatch.setattr(korail.client, "search_trains", lambda *args, **kwargs: original)
    result = korail.trains.search(
        "출발시험역", "도착시험역", depart_after=datetime(2099, 1, 2), include_no_seats=False
    )
    assert result.trains == ([first] if page == "available" else [])
    query = TrainSearchQuery(
        departure_station="출발시험역",
        arrival_station="도착시험역",
        departure_date="20990102",
        departure_time="000000",
    )
    if page == "empty":
        assert result.next_page() is None
        assert result.next_query_from_last_departure(query) is None
    else:
        assert result.next_page() == original.next_page() and result.next_page() is not None
        assert result.next_query_from_last_departure(query) == replace(query, departure_time="230000")


@pytest.mark.parametrize("field", ["include_no_seats", "include_waiting_list"])
@pytest.mark.parametrize("value", [1, "False", None])
def test_invalid_filter_is_rejected_before_search(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid filters must not send requests")

    with Korail(synthetic_config(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "list_stations", unexpected)
        monkeypatch.setattr(korail.client, "search_trains", unexpected)
        with pytest.raises(TypeError, match="must be bool"):
            korail.trains.search("출발", "도착", **{field: value})


@pytest.mark.parametrize("option", list(KorailReserveOption))
@pytest.mark.parametrize("general, special", [(False, False), (True, False), (False, True), (True, True)])
def test_cabin_option_matrix_sends_at_most_one_reservation(
    monkeypatch: pytest.MonkeyPatch, korail: Korail, option: KorailReserveOption, general: bool, special: bool
) -> None:
    train = _train(
        general_reservation_code="11" if general else "13", special_reservation_code="11" if special else "13"
    )
    hold = ReservationHoldResponse(str_result="SUCC", pnr_no="SYNTHETIC-PNR")
    counts = KorailPassengerCounts(adult=2)
    calls: list[dict[str, object]] = []

    def reserve(actual: TrainSummary, **kwargs: object) -> ReservationHoldResponse:
        assert actual is train
        calls.append(kwargs)
        return hold

    allowed = general or special
    if option is KorailReserveOption.GENERAL_ONLY:
        allowed, expected = general, KorailSeatClass.GENERAL
    elif option is KorailReserveOption.SPECIAL_ONLY:
        allowed, expected = special, KorailSeatClass.SPECIAL
    elif option is KorailReserveOption.GENERAL_FIRST:
        expected = KorailSeatClass.GENERAL if general else KorailSeatClass.SPECIAL
    else:
        expected = KorailSeatClass.SPECIAL if special else KorailSeatClass.GENERAL
    monkeypatch.setattr(korail.client, "reserve", reserve)
    if allowed:
        assert korail.reservations.create(train, option=option, passengers=counts) is hold
        assert calls == [
            {
                "passengers": counts,
                "seat_class": expected,
                "job_type": KorailReservationJobType.IMMEDIATE,
                "seats": None,
                "seat_attribute_code": None,
            }
        ]
    else:
        with pytest.raises(KorailProtocolError, match="available seat"):
            korail.reservations.create(train, option=option)
        assert calls == []


def test_option_does_not_retry_a_server_failure(monkeypatch: pytest.MonkeyPatch, korail: Korail) -> None:
    decline = Mock(side_effect=KorailProtocolError("synthetic server refusal"))
    monkeypatch.setattr(korail.client, "reserve", decline)
    with pytest.raises(KorailProtocolError, match="server refusal"):
        korail.reservations.create(
            _train(special_reservation_code="11"), option=KorailReserveOption.GENERAL_FIRST
        )
    decline.assert_called_once()
    assert decline.call_args.kwargs["seat_class"] is KorailSeatClass.GENERAL


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"seat_class": KorailSeatClass.GENERAL}, ValueError),
        ({"job_type": KorailReservationJobType.STANDBY}, ValueError),
        ({"job_type": KorailReservationJobType.MERGE_STANDING}, ValueError),
        ({"option": "GENERAL_FIRST"}, TypeError),
    ],
)
def test_conflicting_options_never_reserve(
    monkeypatch: pytest.MonkeyPatch, korail: Korail, kwargs: dict[str, object], error: type[Exception]
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid options must not reserve")

    monkeypatch.setattr(korail.client, "reserve", unexpected)
    with pytest.raises(error):
        korail.reservations.create(_train(), **{"option": KorailReserveOption.GENERAL_FIRST, **kwargs})


def test_option_does_not_convert_sold_out_to_waiting(monkeypatch: pytest.MonkeyPatch, korail: Korail) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("a waiting flag must not trigger automatic reservation")

    monkeypatch.setattr(korail.client, "reserve", unexpected)
    with pytest.raises(KorailProtocolError, match="available seat"):
        korail.reservations.create(
            _train(general_reservation_code="13", wait_reservation_flag=" 9"),
            option=KorailReserveOption.GENERAL_FIRST,
        )


@pytest.mark.parametrize("seat_class", [None, KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL])
def test_default_and_explicit_cabin_behavior_remain(
    monkeypatch: pytest.MonkeyPatch, korail: Korail, seat_class: KorailSeatClass | None
) -> None:
    hold = ReservationHoldResponse(str_result="SUCC")
    reserve = Mock(return_value=hold)
    monkeypatch.setattr(korail.client, "reserve", reserve)
    assert korail.reservations.create(_train(), seat_class=seat_class) is hold
    reserve.assert_called_once()
    assert reserve.call_args.kwargs["seat_class"] is (
        KorailSeatClass.GENERAL if seat_class is None else seat_class
    )


@pytest.mark.parametrize("container", [tuple, list])
def test_create_designated_seats_forwards_existing_wire_options_once(
    scripted_client_factory, f8_logged_in_session, container
):
    raw = {"strResult": "SUCC", "h_pnr_no": "SYNTHETIC-PNR"}
    client, requests, pending = scripted_client_factory(
        [raw],
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    result = ReservationResource(client).create(
        _train(special_reservation_code="11"),
        passengers=KorailPassengerCounts(adult=2),
        seat_class=KorailSeatClass.SPECIAL,
        job_type=KorailReservationJobType.SEAT_DESIGNATED,
        seats=container(
            [KorailSeatAssignment(car_no=2, seat_no="01A"), KorailSeatAssignment(car_no=3, seat_no="02B")]
        ),
        seat_attribute_code="031",
    )
    assert result.raw == raw and len(requests) == 1 and pending == []
    form = wire_form(requests[0])
    assert {key: form[key] for key in ("txtJobId", "txtPsrmClCd1", "txtSeatAttCd4", "txtTotPsgCnt")} == {
        "txtJobId": ["1103"],
        "txtPsrmClCd1": ["2"],
        "txtSeatAttCd4": ["031"],
        "txtTotPsgCnt": ["2"],
    }
    assert [
        (key, value) for key, value in wire_pairs(requests[0]) if key.startswith(("txtSrcar", "txtSeatNo"))
    ] == [
        ("txtSrcarCnt", "2"),
        ("txtSrcarNo1", "2"),
        ("txtSeatNo1", "01A"),
        ("txtSrcarNo2", "3"),
        ("txtSeatNo2", "02B"),
    ]


def test_create_keeps_option_selection_with_an_explicit_seat_attribute(
    scripted_client_factory, f8_logged_in_session
):
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC"}],
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    ReservationResource(client).create(
        _train(general_reservation_code="13", special_reservation_code="11"),
        option=KorailReserveOption.GENERAL_FIRST,
        seat_attribute_code="031",
    )
    form = wire_form(requests[0])
    assert form["txtJobId"] == ["1101"] and form["txtPsrmClCd1"] == ["2"] and form["txtSeatAttCd4"] == ["031"]
    assert "txtSrcarCnt" not in form and len(requests) == 1 and pending == []


@pytest.mark.parametrize("option", [None, KorailReserveOption.GENERAL_FIRST])
def test_create_does_not_infer_a_designated_job_from_seats(
    scripted_client_factory, f8_logged_in_session, option
):
    client, requests, _ = scripted_client_factory(
        [], config=synthetic_config(netfunnel_enabled=False), session=f8_logged_in_session
    )
    with pytest.raises(KorailInvalidInputError, match="seat-designated"):
        ReservationResource(client).create(
            _train(), option=option, seats=[KorailSeatAssignment(car_no=1, seat_no="01A")]
        )
    assert requests == []


@pytest.mark.parametrize("target", ["hold", "reference", "recovered"])
@pytest.mark.parametrize("check_first", [None, True, False])
def test_cancel_supports_hold_recovery_and_explicit_check_budget(
    scripted_client_factory, f8_logged_in_session, target, check_first
):
    reference = HoldReference(pnr_no="SYNTHETIC-PNR", journey_count="0002")
    targets = {
        "hold": ReservationHoldResponse(str_result="SUCC", pnr_no="SYNTHETIC-PNR", journey_count="0002"),
        "reference": reference,
        "recovered": HoldReference.from_raw(
            {"h_pnr_no": "SYNTHETIC-PNR", "h_jrny_cnt": "0002", "h_wct_no": []}
        ),
    }
    budget = 1 if check_first is False else 2
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC"}] * budget,
        config=synthetic_config(netfunnel_enabled=False, disable_dynapath=True),
        session=f8_logged_in_session,
    )
    resource = ReservationResource(client)
    result = (
        resource.cancel(targets[target])
        if check_first is None
        else resource.cancel(targets[target], check_first=check_first)
    )
    assert result.str_result == "SUCC" and len(requests) == budget and pending == []
    assert [request.url.path.rsplit(".", 1)[-1] for request in requests] == (
        ["ReservationCancel", "ReservationCancelChk"] if budget == 2 else ["ReservationCancelChk"]
    )
    for request in requests:
        assert wire_pairs(request)[-4:] == [
            ("txtPnrNo", "SYNTHETIC-PNR"),
            ("txtJrnySqno", "0001"),
            ("txtJrnyCnt", "0002"),
            ("hidRsvChgNo", "000"),
        ]


@pytest.mark.parametrize(
    "general, special, waiting, expected",
    [
        ("11", "13", "0", (True, False, True, False)),
        ("13", "11", " 9", (False, True, True, True)),
        ("13", "13", "9", (False, False, False, False)),
        (None, None, None, (False, False, False, False)),
        ("FUTURE", "FUTURE", "FUTURE", (False, False, False, False)),
        ("13", "13", "0", (False, False, False, False)),
    ],
)
def test_availability_uses_only_known_codes(
    general: str | None, special: str | None, waiting: str | None, expected: tuple[bool, ...]
) -> None:
    train = _train(
        general_reservation_code=general, special_reservation_code=special, wait_reservation_flag=waiting
    )
    assert (
        train.has_general_seat(),
        train.has_special_seat(),
        train.has_seat(),
        train.has_waiting_list(),
    ) == expected
    assert not TrainSummary.from_raw({"h_trn_no": "1", "h_wait_rsv_flg": 9}).has_waiting_list()


@pytest.mark.parametrize(
    "arrival_date, arrival_time, minutes, text",
    [
        ("20990102", "090000", 0, "0분"),
        ("20990102", "094500", 45, "45분"),
        ("20990102", "100000", 60, "1시간"),
        ("20990102", "123000", 210, "3시간 30분"),
        ("20990103", "013000", 990, "16시간 30분"),
        ("20990104", "100000", 2940, "49시간"),
    ],
)
def test_duration_uses_actual_dates(arrival_date: str, arrival_time: str, minutes: int, text: str) -> None:
    train = _train(arrival_date=arrival_date, arrival_time=arrival_time)
    assert train.duration_minutes == minutes and train.duration_text == text


@pytest.mark.parametrize(
    "changes",
    [
        {"arrival_date": None},
        {"departure_date": None},
        {"arrival_time": None},
        {"departure_time": None},
        {"arrival_date": "20990230"},
        {"arrival_time": "250000"},
        {"arrival_time": "90000"},
        {"departure_time": "０９００００"},
        {"arrival_date": "20990101"},
        {"arrival_time": "080000"},
    ],
)
def test_invalid_duration_is_unknown_not_inferred(changes: dict[str, str | None]) -> None:
    train = _train(**changes)
    assert train.duration_minutes is None and train.duration_text is None


def test_summary_has_no_raw_data() -> None:
    assert _train(raw={"sensitive": "SYNTHETIC-PRIVATE"}).summary() == (
        "[KTX 90001] 2099-01-02 09:00~2099-01-02 12:30 출발시험역~도착시험역 (3시간 30분)"
    )
    assert TrainSummary(train_no="1").summary() == "[열차 1] ?~? ?~?"


def test_find_delegates_to_one_direct_hold_lookup(monkeypatch: pytest.MonkeyPatch, korail: Korail) -> None:
    hold = ReservationHoldResponse(str_result="SUCC", pnr_no="SYNTHETIC-PNR")
    find = Mock(return_value=hold)
    monkeypatch.setattr(korail.client, "get_reservation_hold", find)
    assert korail.reservations.get("SYNTHETIC-PNR") is hold
    find.assert_called_once_with("SYNTHETIC-PNR")
