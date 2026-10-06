"""Optional convenience behavior keeps original responses and mutation request budgets."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any

import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    Korail,
    KorailConfig,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailReservationJobType,
    KorailReserveOption,
    KorailSeatClass,
    ReservationHoldResponse,
    TrainSearchMetadata,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
)


def _train(**changes: Any) -> TrainSummary:
    return replace(
        TrainSummary(
            train_no="90001",
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
    monkeypatch: pytest.MonkeyPatch, include_no_seats: bool, include_waiting_list: bool, expected: list[str]
) -> None:
    trains = [
        _train(train_no="1"),
        _train(train_no="2", general_reservation_code="13", special_reservation_code="11"),
        _train(train_no="3", general_reservation_code="13", wait_reservation_flag=" 9"),
        _train(train_no="4", general_reservation_code="13"),
        _train(train_no="5", general_reservation_code=None, special_reservation_code=None),
    ]
    raw: dict[str, object] = {"extra": {"preserved": True}}
    original = TrainSearchResult(trains, BaseKorailResponse(str_result="SUCC", raw=raw), raw=raw)
    calls: list[TrainSearchQuery] = []

    def search(query: TrainSearchQuery, **kwargs: object) -> TrainSearchResult:
        calls.append(query)
        return original

    with Korail(KorailConfig(netfunnel_enabled=False), validate_stations=False) as korail:
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
    assert original.trains is trains and len(original.trains) == 5 and len(calls) == 1
    assert result.unfiltered_trains is (None if include_no_seats else trains)
    if include_no_seats:
        assert result is original


@pytest.mark.parametrize("empty_filtered", [True, False])
def test_filter_preserves_cursor_and_last_server_departure(
    monkeypatch: pytest.MonkeyPatch, empty_filtered: bool
) -> None:
    first = _train(general_reservation_code="13" if empty_filtered else "11")
    last = _train(train_no="90002", general_reservation_code="13", departure_time="230000")
    original = TrainSearchResult(
        [first, last],
        BaseKorailResponse(str_result="SUCC"),
        metadata=TrainSearchMetadata(next_page_flag="Y", next_query_station_no="0001", next_train_no="90002"),
    )
    with Korail(KorailConfig(netfunnel_enabled=False), validate_stations=False) as korail:
        monkeypatch.setattr(korail.client, "search_trains", lambda *args, **kwargs: original)
        result = korail.trains.search(
            "출발시험역", "도착시험역", depart_after=datetime(2099, 1, 2), include_no_seats=False
        )
    assert result.trains == ([] if empty_filtered else [first])
    assert result.next_page() == original.next_page() and result.next_page() is not None
    query = TrainSearchQuery("출발시험역", "도착시험역", "20990102", "000000")
    assert result.next_query_from_last_departure(query) == replace(query, departure_time="230000")


def test_empty_server_page_does_not_gain_a_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    original = TrainSearchResult(
        [],
        BaseKorailResponse(str_result="SUCC"),
        metadata=TrainSearchMetadata(next_page_flag="Y", next_query_station_no="0001", next_train_no="90002"),
    )
    with Korail(KorailConfig(netfunnel_enabled=False), validate_stations=False) as korail:
        monkeypatch.setattr(korail.client, "search_trains", lambda *args, **kwargs: original)
        result = korail.trains.search("출발", "도착", depart_after=datetime(2099, 1, 2), include_no_seats=False)
    assert result.next_page() is None
    assert result.next_query_from_last_departure(TrainSearchQuery("출발", "도착", "20990102", "000000")) is None


@pytest.mark.parametrize("field", ["include_no_seats", "include_waiting_list"])
@pytest.mark.parametrize("value", [1, "False", None])
def test_invalid_filter_is_rejected_before_search(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid filters must not send requests")

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "get_station_data", unexpected)
        monkeypatch.setattr(korail.client, "search_trains", unexpected)
        with pytest.raises(TypeError, match="must be bool"):
            korail.trains.search("출발", "도착", **{field: value})


@pytest.mark.parametrize("option", list(KorailReserveOption))
@pytest.mark.parametrize("general, special", [(False, False), (True, False), (False, True), (True, True)])
def test_cabin_option_matrix_sends_at_most_one_reservation(
    monkeypatch: pytest.MonkeyPatch, option: KorailReserveOption, general: bool, special: bool
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
    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "reserve", reserve)
        if allowed:
            assert korail.reservations.create(train, option=option, passengers=counts) is hold
            assert calls == [
                {"passengers": counts, "seat_class": expected, "job_type": KorailReservationJobType.IMMEDIATE}
            ]
        else:
            with pytest.raises(KorailProtocolError, match="available seat"):
                korail.reservations.create(train, option=option)
            assert calls == []


def test_option_does_not_retry_a_server_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[KorailSeatClass] = []

    def decline(
        train: TrainSummary, *, seat_class: KorailSeatClass, **kwargs: object
    ) -> ReservationHoldResponse:
        calls.append(seat_class)
        raise KorailProtocolError("synthetic server refusal")

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "reserve", decline)
        with pytest.raises(KorailProtocolError, match="server refusal"):
            korail.reservations.create(
                _train(special_reservation_code="11"), option=KorailReserveOption.GENERAL_FIRST
            )
    assert calls == [KorailSeatClass.GENERAL]


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
    monkeypatch: pytest.MonkeyPatch, kwargs: dict[str, object], error: type[Exception]
) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("invalid options must not reserve")

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "reserve", unexpected)
        with pytest.raises(error):
            korail.reservations.create(_train(), **{"option": KorailReserveOption.GENERAL_FIRST, **kwargs})


def test_option_does_not_convert_sold_out_to_waiting(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*args: object, **kwargs: object) -> None:
        raise AssertionError("a waiting flag must not trigger automatic reservation")

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "reserve", unexpected)
        with pytest.raises(KorailProtocolError, match="available seat"):
            korail.reservations.create(
                _train(general_reservation_code="13", wait_reservation_flag=" 9"),
                option=KorailReserveOption.GENERAL_FIRST,
            )


@pytest.mark.parametrize("seat_class", [None, KorailSeatClass.GENERAL, KorailSeatClass.SPECIAL])
def test_default_and_explicit_cabin_behavior_remain(
    monkeypatch: pytest.MonkeyPatch, seat_class: KorailSeatClass | None
) -> None:
    calls: list[dict[str, object]] = []
    hold = ReservationHoldResponse(str_result="SUCC")

    def reserve(*args: object, **kwargs: object) -> ReservationHoldResponse:
        calls.append(kwargs)
        return hold

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "reserve", reserve)
        assert korail.reservations.create(_train(), seat_class=seat_class) is hold
    assert calls[0]["seat_class"] is (KorailSeatClass.GENERAL if seat_class is None else seat_class)


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
    assert TrainSummary("1").summary() == "[열차 1] ?~? ?~?"


def test_find_delegates_to_one_direct_hold_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    hold = ReservationHoldResponse(str_result="SUCC", pnr_no="SYNTHETIC-PNR")

    def find(pnr_no: str) -> ReservationHoldResponse:
        calls.append(pnr_no)
        return hold

    with Korail(KorailConfig(netfunnel_enabled=False)) as korail:
        monkeypatch.setattr(korail.client, "get_reservation_hold", find)
        assert korail.reservations.find("SYNTHETIC-PNR") is hold
    assert calls == ["SYNTHETIC-PNR"]
