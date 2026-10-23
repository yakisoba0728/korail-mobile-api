"""New read conveniences reuse public clients and the shared offline transport fixtures."""

from __future__ import annotations

from collections import UserList
from dataclasses import replace
from datetime import date, datetime, timezone

import httpx
import pytest
from conftest import synthetic_config, wire_form, wire_pairs

from korail_mobile_api import (
    AirportBusResource,
    AirportBusSchedule,
    AirportBusSeatInventoryQuery,
    AirportBusStop,
    BaseKorailResponse,
    DynapathTokenSettings,
    Korail,
    KorailAuthError,
    KorailConfig,
    KorailInvalidInputError,
    KorailNoResultsError,
    KorailPassengerCounts,
    KorailProtocolError,
    KorailSession,
    KorailTransportError,
    MembershipResource,
    OriginalTicketReference,
    PaidTicket,
    PriceFareLeg,
    PriceRecalculationRequest,
    RefundCompanion,
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
    StationResource,
    TicketListTicket,
    TrainResource,
    TrainSummary,
)

MOMENT = datetime(2099, 1, 2, 9)


@pytest.fixture
def config() -> KorailConfig:
    return synthetic_config(netfunnel_enabled=False, disable_dynapath=True)


def _row(number: str, time: str = "100000", **fields: object) -> dict[str, object]:
    return {
        "h_trn_no": number,
        "h_dpt_dt": "20990102",
        "h_dpt_tm": time,
        "h_dpt_rs_stn_cd": "9901",
        "h_arv_rs_stn_cd": "9903",
        "h_gen_rsv_cd": "11",
        **fields,
    }


def _page(*rows: dict[str, object], **fields: object) -> dict[str, object]:
    return {"strResult": "SUCC", "trn_infos": {"trn_info": list(rows)}, **fields}


def test_new_resources_do_not_request_during_construction(config):
    with Korail(config) as korail:
        assert isinstance(korail.membership, MembershipResource)
        assert isinstance(korail.airport_bus, AirportBusResource)


_STATION_REFUND = {
    "pnr_no": "SYNTHETIC-PNR",
    "original_sale_date": "20990102",
    "original_sale_window_no": "0001",
    "original_sale_sequence": "0001",
    "original_return_password": "SYNTHETIC-HIDDEN-PASSWORD",
    "refund_division_code": "1",
    "refund_reason_code": "1",
    "ticket_kind_code": "1",
    "customer_phone": "SYNTHETIC-HIDDEN-PHONE",
    "refund_amount": "1000",
    "refund_fee": "0",
    "customer_name": "SYNTHETIC-HIDDEN-NAME",
}


@pytest.mark.parametrize(
    "model, attribute",
    [
        (KorailSession(jsessionid="SYNTHETIC-HIDDEN-COOKIE"), "jsessionid"),
        (KorailSession(raw={"debug": "SYNTHETIC-HIDDEN-RAW"}), "raw"),
        (BaseKorailResponse(raw={"debug": "SYNTHETIC-HIDDEN-RAW"}), "raw"),
        (
            PaidTicket(
                pnr_no="SYNTHETIC-PNR",
                sale_date="20990102",
                sale_window_no="0001",
                sale_sequence="0001",
                return_password="SYNTHETIC-HIDDEN-RETURN",
            ),
            "return_password",
        ),
        (
            OriginalTicketReference(
                sale_window_no="0001",
                sale_date="0102",
                sale_sequence="0001",
                return_password="SYNTHETIC-HIDDEN-RETURN",
            ),
            "return_password",
        ),
        (RefundCompanion(name="SYNTHETIC-HIDDEN-NAME"), "name"),
        (RefundCompanion(certificate_no="SYNTHETIC-HIDDEN-BIRTH"), "certificate_no"),
        (
            StationRefundVerificationRequest(
                customer_name="SYNTHETIC-HIDDEN-NAME",
                return_no_1="1",
                return_no_2="2",
                return_no_3="3",
                return_no_4="4",
            ),
            "customer_name",
        ),
        *(
            (StationRefundExecutionRequest(**_STATION_REFUND), name)
            for name in ("original_return_password", "customer_phone", "customer_name")
        ),
        (
            PriceRecalculationRequest(pnr_no="SYNTHETIC-PNR", non_member_no="SYNTHETIC-HIDDEN-NO"),
            "non_member_no",
        ),
        (KorailConfig(advertising_id="SYNTHETIC-HIDDEN-AD-ID"), "advertising_id"),
        (
            DynapathTokenSettings(
                device_id="SYNTHETIC-HIDDEN-DEVICE",
                as_value="SYNTHETIC",
                app_start_ts="1",
                os_version="16",
                device_model="SYNTHETIC",
            ),
            "device_id",
        ),
    ],
)
def test_caller_secrets_are_hidden_from_debug_representations(model, attribute):
    """3.0 hides caller-supplied secrets and raw from repr; the attribute itself keeps the real value."""
    value = getattr(model, attribute)
    marker = value["debug"] if attribute == "raw" else value
    assert marker.startswith("SYNTHETIC-HIDDEN")
    assert marker not in repr(model) and marker not in str(model)


_SALE_TICKET = TicketListTicket(
    sale_window_no="0001",
    sale_date="20990102",
    return_sale_date="1231",
    sale_sequence="0007",
    return_password="SYNTHETIC-RETURN",
)


def test_sale_ticket_factory_keeps_full_sale_date_and_return_factory_meaning(
    scripted_client_factory, config, f8_logged_in_session
):
    reference = OriginalTicketReference.from_sale_ticket(_SALE_TICKET)
    assert reference == OriginalTicketReference(
        sale_window_no="0001", sale_date="20990102", sale_sequence="0007", return_password="SYNTHETIC-RETURN"
    )
    assert OriginalTicketReference.from_ticket(_SALE_TICKET) == replace(reference, sale_date="1231")
    assert replace(reference, sale_date="manual-date").sale_date == "manual-date"
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC", "tkList": []}], config=config, session=f8_logged_in_session
    )
    client.list_pbp_acceptances([reference, reference])
    assert wire_pairs(requests[0])[-3:] == [
        ("tkCnt", "2"),
        ("tkRetNo", "0001-20990102-0007-SYNTHETIC-RETURN"),
        ("tkRetNo", "0001-20990102-0007-SYNTHETIC-RETURN"),
    ]
    assert len(requests) == 1 and pending == []


@pytest.mark.parametrize(
    "changes",
    [
        {"sale_date": None},
        {"sale_date": ""},
        {"sale_date": "0102"},
        {"sale_date": "２０９９０１０２"},
        {"sale_window_no": None},
        {"sale_sequence": " "},
        {"return_password": None},
    ],
)
def test_sale_ticket_factory_rejects_missing_identity_or_non_full_sale_date(changes):
    with pytest.raises(KorailInvalidInputError):
        OriginalTicketReference.from_sale_ticket(replace(_SALE_TICKET, **changes))


def test_sale_ticket_factory_does_not_require_a_return_date_or_accept_another_model():
    assert OriginalTicketReference.from_sale_ticket(replace(_SALE_TICKET, return_sale_date=None)).sale_date == (
        "20990102"
    )
    with pytest.raises(KorailInvalidInputError, match="TicketListTicket"):
        OriginalTicketReference.from_sale_ticket(object())


@pytest.mark.parametrize("goods", [None, "", "SYNTHETIC-GOODS"])
def test_fare_factory_copies_identifiers_without_guessing(goods):
    train = TrainSummary(
        train_no="00007",
        train_group_code="101",
        train_class_code="00",
        run_date="20990101",
        departure_date="20990102",
        departure_station_code="9901",
        arrival_station_code="9903",
        seat_attribute_code="031",
        goods_no=goods,
    )
    assert PriceFareLeg.from_train(train) == PriceFareLeg(
        departure_station_code="9901",
        arrival_station_code="9903",
        run_date="20990101",
        train_no="00007",
        requested_seat_attribute_code="031",
        train_group_code="101",
        train_class_code="00",
        goods_no=goods or None,
    )


@pytest.mark.parametrize(
    "field",
    [
        "train_no",
        "departure_station_code",
        "arrival_station_code",
        "run_date",
        "seat_attribute_code",
        "train_group_code",
        "train_class_code",
    ],
)
@pytest.mark.parametrize("value", [None, "", " ", "bad,field", True])
def test_fare_factory_rejects_missing_or_invalid_identity(field, value):
    values = dict(
        train_no="00007",
        departure_station_code="9901",
        arrival_station_code="9903",
        run_date="20990102",
        seat_attribute_code="015",
        train_group_code="101",
        train_class_code="00",
    )
    values[field] = value
    with pytest.raises(KorailProtocolError):
        PriceFareLeg.from_train(TrainSummary(**values))


def test_fare_factory_rejects_wrong_model():
    with pytest.raises(KorailProtocolError, match="TrainSummary"):
        PriceFareLeg.from_train(object())


@pytest.mark.parametrize("goods", [False, 0, " ", "bad,field"])
def test_fare_factory_does_not_normalize_invalid_goods_to_missing(goods):
    train = TrainSummary(
        train_no="00007",
        train_group_code="101",
        train_class_code="00",
        run_date="20990102",
        departure_station_code="9901",
        arrival_station_code="9903",
        seat_attribute_code="015",
        goods_no=goods,
    )
    with pytest.raises(KorailProtocolError):
        PriceFareLeg.from_train(train)


@pytest.mark.parametrize("max_pages", [0, 21, True, "2", None])
def test_iterator_validates_budget_without_requests(scripted_client_factory, config, max_pages):
    client, requests, _ = scripted_client_factory([], config=config)
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    with pytest.raises(KorailInvalidInputError, match="max_pages"):
        list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=max_pages))
    assert requests == []


@pytest.mark.parametrize("use_cursor", [False, True])
def test_iterator_is_lazy_bounded_and_preserves_search_options(scripted_client_factory, config, use_cursor):
    cursor = {"h_next_pg_flg": "Y", "h_qry_st_no_next": "9901", "h_trn_no_next": "00007"} if use_cursor else {}
    client, requests, pending = scripted_client_factory(
        [
            _page(_row("00007"), **cursor),
            _page(_row("00007"), _row("00008", "110000")),
        ],
        config=config,
    )
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    iterator = trains.iter_search(
        "출발",
        "도착",
        depart_after=MOMENT,
        max_pages=2,
        passengers=KorailPassengerCounts(adult=2, child=1),
        include_nearby_stations=True,
    )
    assert requests == []
    assert next(iterator).train_no == "00007" and len(requests) == 1
    assert [train.train_no for train in iterator] == ["00008"]
    assert len(requests) == 2 and pending == []
    forms = [wire_form(request) for request in requests]
    for form in forms:
        assert form["txtPsgFlg_1"] == ["2"] and form["txtPsgFlg_2"] == ["1"]
        assert form["adjStnScdlOfrFlg"] == ["Y"]
    assert forms[0]["txtGoHour"] == ["090000"]
    if use_cursor:
        assert forms[1]["qryStTrnNo"] == ["00007"] and forms[1]["txtGoHour"] == ["090000"]
    else:
        assert forms[1]["txtGoHour"] == ["100000"] and "qryStTrnNo" not in forms[1]


def test_iterator_uses_unfiltered_page_and_composite_identity(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory(
        [
            _page(_row("00007", "100000", h_gen_rsv_cd="13")),
            _page(_row("00007", "110000"), _row("00007", "110000", h_dpt_rs_stn_cd="9902"), h_next_pg_flg="N"),
        ],
        config=config,
    )
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    found = list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=4, include_no_seats=False))
    assert [(train.train_no, train.departure_station_code) for train in found] == [
        ("00007", "9901"),
        ("00007", "9902"),
    ]
    assert wire_form(requests[1])["txtGoHour"] == ["100000"]
    assert len(requests) == 2


@pytest.mark.parametrize(
    "second",
    [
        _page(),
        _page(_row("00007")),
        _page(_row("00008", "100000")),
        _page(_row("00008", "bad-time")),
        {"strResult": "FAIL", "h_msg_cd": "WRG000000"},
    ],
)
def test_iterator_stops_on_empty_duplicate_or_nonadvancing_page(scripted_client_factory, config, second):
    client, requests, _ = scripted_client_factory([_page(_row("00007")), second], config=config)
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=5))
    assert len(requests) == 2


def test_iterator_does_not_repeat_cursor(scripted_client_factory, config):
    cursor = {"h_next_pg_flg": "Y", "h_qry_st_no_next": "9901", "h_trn_no_next": "00007"}
    client, requests, _ = scripted_client_factory(
        [
            _page(_row("00007"), **cursor),
            _page(_row("00008", "110000"), **cursor),
        ],
        config=config,
    )
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    assert len(list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=5))) == 2
    assert len(requests) == 2


def test_iterator_keeps_sparse_rows_without_guessing_their_identity(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory(
        [
            _page({"h_trn_no": "00007", "h_info_txt": "first"}, {"h_trn_no": "00007", "h_info_txt": "second"}),
        ],
        config=config,
    )
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    found = list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=3))
    assert len(found) == 2 and len(requests) == 1


@pytest.mark.parametrize(
    "reply, error",
    [
        ({"strResult": "FAIL", "h_msg_cd": "WRG000000"}, KorailNoResultsError),
        (httpx.ConnectError("synthetic failure"), KorailTransportError),
    ],
)
def test_iterator_first_failure_is_not_silenced(scripted_client_factory, config, reply, error):
    client, requests, _ = scripted_client_factory([reply], config=config)
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    with pytest.raises(error):
        list(trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=3))
    assert len(requests) == 1


def test_iterator_preserves_yielded_rows_and_does_not_retry(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory(
        [
            _page(_row("00007")),
            httpx.ReadTimeout("synthetic later failure"),
        ],
        config=config,
    )
    iterator = TrainResource(client, StationResource(client), validate_stations=False).iter_search(
        "출발",
        "도착",
        depart_after=MOMENT,
        max_pages=3,
    )
    assert next(iterator).train_no == "00007"
    with pytest.raises(KorailTransportError):
        next(iterator)
    assert len(requests) == 2


def test_iterator_keeps_queue_entry_and_release_for_every_page(f8_client_factory):
    events = []

    def handler(request):
        if request.url.host == "queue.example.invalid":
            opcode = request.url.params["opcode"]
            events.append(opcode)
            return httpx.Response(200, text="200:key=SYNTHETIC-QUEUE")
        events.append("search")
        page = events.count("search")
        return httpx.Response(200, json=_page(_row(f"0000{page}", f"{9 + page:02d}0000")))

    client = f8_client_factory(handler, logged_in=False)
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    iterator = trains.iter_search("출발", "도착", depart_after=MOMENT, max_pages=2)
    assert next(iterator).train_no == "00001"
    assert events == ["5101", "search", "5004"]
    assert [train.train_no for train in iterator] == ["00002"]
    assert events == ["5101", "search", "5004"] * 2


def test_iterator_keeps_original_query_after_long_queue_wait(scripted_client_factory, config, monkeypatch):
    from korail_mobile_api import facade

    minute = [0]

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2099, 1, 2, 0, minute[0], tzinfo=timezone.utc).astimezone(tz)

    def first(request):
        minute[0] = 2
        return _page(_row("00007"), h_next_pg_flg="Y", h_qry_st_no_next="9901", h_trn_no_next="00007")

    monkeypatch.setattr(facade, "datetime", Clock)
    client, requests, _ = scripted_client_factory(
        [first, _page(_row("00008"), h_next_pg_flg="N")], config=config
    )
    trains = TrainResource(client, StationResource(client), validate_stations=False)
    assert len(list(trains.iter_search("출발", "도착", max_pages=2))) == 2
    assert [wire_form(request)["txtGoHour"] for request in requests] == [["090000"], ["090000"]]


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"end_date": date(2099, 1, 31)}, ("20990101", "20990131")),
        (
            {"start_date": date(2099, 1, 1), "end_date": datetime(2099, 1, 2, 15, tzinfo=timezone.utc)},
            ("20990101", "20990103"),
        ),
        ({"start_date": datetime(2099, 1, 1, 23), "end_date": date(2099, 1, 3)}, ("20990101", "20990103")),
    ],
)
def test_membership_dates_and_original_response(
    scripted_client_factory, config, f8_logged_in_session, kwargs, expected
):
    raw = {"strResult": "SUCC", "totAvlRailPoint": "00042", "extra": "preserved"}
    client, requests, _ = scripted_client_factory([raw], config=config, session=f8_logged_in_session)
    response = MembershipResource(client).mileage(**kwargs, ledger="2", movement="1", page_no=2)
    assert response.raw == raw
    form = wire_form(requests[0])
    assert (form["qryStDt"][0], form["qryClsDt"][0]) == expected
    assert form["pontTpVal"] == ["2"] and form["qryDvVal"] == ["1"] and form["nowPgNo"] == ["2"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start_date": "20990101"},
        {"end_date": 1},
        {"start_date": date(2099, 1, 3), "end_date": date(2099, 1, 1)},
        {"ledger": "bad"},
        {"movement": "bad"},
        {"page_no": True},
    ],
)
def test_membership_invalid_inputs_never_send(scripted_client_factory, config, f8_logged_in_session, kwargs):
    client, requests, _ = scripted_client_factory([], config=config, session=f8_logged_in_session)
    with pytest.raises((TypeError, KorailProtocolError)):
        MembershipResource(client).mileage(**kwargs)
    assert requests == []


def test_membership_default_range_uses_today_kst(
    scripted_client_factory, config, f8_logged_in_session, monkeypatch
):
    from korail_mobile_api import facade

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2099, 1, 31, 2, tzinfo=timezone.utc).astimezone(tz)

    monkeypatch.setattr(facade, "datetime", Clock)
    client, requests, _ = scripted_client_factory(
        [{"strResult": "SUCC"}], config=config, session=f8_logged_in_session
    )
    MembershipResource(client).mileage()
    form = wire_form(requests[0])
    assert form["qryStDt"] == ["20990101"] and form["qryClsDt"] == ["20990131"]


def test_membership_explicit_early_dates_do_not_compute_default_range(
    scripted_client_factory, config, f8_logged_in_session
):
    client, requests, _ = scripted_client_factory(
        [{"strResult": "SUCC"}], config=config, session=f8_logged_in_session
    )
    membership = MembershipResource(client)
    membership.mileage(start_date=date.min, end_date=date.min)
    form = wire_form(requests[0])
    assert form["qryStDt"] == form["qryClsDt"] == ["00010101"]
    with pytest.raises(KorailInvalidInputError, match="30-day"):
        membership.mileage(end_date=date.min)
    assert len(requests) == 1


def test_membership_coupons_preserve_page_and_pnr(scripted_client_factory, config, f8_logged_in_session):
    client, requests, _ = scripted_client_factory(
        [{"strResult": "SUCC"}], config=config, session=f8_logged_in_session
    )
    assert MembershipResource(client).coupons(page_no=2, pnr_no="SYNTHETIC-PNR").items == ()
    form = wire_form(requests[0])
    assert form["txtSelPage"] == ["2"] and form["pnrNo"] == ["SYNTHETIC-PNR"]


def _stops(**changes: object) -> dict[str, object]:
    return {
        "strResult": "SUCC",
        "app.limousine.stationNm": ["시험출발", "시험도착"],
        "app.limousine.stationCd": ["9901", "9903"],
        **changes,
    }


def test_bus_stop_cache_refresh_and_name_search(scripted_client_factory, config):
    client, requests, pending = scripted_client_factory(
        [
            _stops(),
            {"strResult": "SUCC", "trainList": [], "extra": "kept"},
            _stops(),
        ],
        config=config,
    )
    bus = AirportBusResource(client)
    assert bus.stops() == (
        AirportBusStop(code="9901", name="시험출발"),
        AirportBusStop(code="9903", name="시험도착"),
    )
    assert bus.stops() is bus.stops() and len(requests) == 1
    result = bus.search(" 시험출발 ", "9903", service_code="980", depart_after=MOMENT)
    assert result.raw["extra"] == "kept" and result.schedules == ()
    form = wire_form(requests[1])
    assert form["dptRsStnCd"] == ["9901"] and form["arvRsStnCd"] == ["9903"]
    assert form["dptDt"] == ["20990102"] and form["dptTm"] == ["090000"]
    assert "rsvSaleDvCd" not in form
    assert wire_form(requests[0])["code"] == [
        "app.limousine.stationNm",
        "app.limousine.stationCd",
    ]
    bus.stops(refresh=True)
    assert len(requests) == 3 and pending == []


@pytest.mark.parametrize(
    "changes",
    [
        {"app.limousine.stationCd": []},
        {"app.limousine.stationNm": None},
        {"app.limousine.stationCd": [True, "9903"]},
        {"app.limousine.stationNm": ["", "시험도착"]},
        {"app.limousine.stationCd": ["9901", "9901"]},
        {"app.limousine.stationNm": ["중복", "중복"]},
    ],
)
def test_bad_bus_catalog_keeps_full_raw_and_is_not_cached(scripted_client_factory, config, changes):
    raw = _stops(**changes, extra={"preserved": True})
    client, requests, _ = scripted_client_factory([raw, _stops()], config=config)
    bus = AirportBusResource(client)
    with pytest.raises(KorailProtocolError) as raised:
        bus.stops()
    assert raised.value.raw == raw
    assert len(bus.stops()) == 2 and len(requests) == 2


def test_unknown_bus_stop_does_not_send_schedule(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory([_stops()], config=config)
    with pytest.raises(KorailInvalidInputError, match="정류장"):
        AirportBusResource(client).search("없는 정류장", "시험도착", service_code="980", depart_after=MOMENT)
    assert len(requests) == 1 and requests[0].url.path.endswith("common.code.do")


def test_ambiguous_bus_name_or_code_does_not_pick_the_first_match(scripted_client_factory, config):
    raw = _stops(**{"app.limousine.stationNm": ["9903", "시험도착"]})
    client, requests, _ = scripted_client_factory([raw], config=config)
    with pytest.raises(KorailInvalidInputError, match="구분"):
        AirportBusResource(client).search("9903", "시험도착", service_code="980", depart_after=MOMENT)
    assert len(requests) == 1 and requests[0].url.path.endswith("common.code.do")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"service_code": ""},
        {"departure": None},
        {"arrival": " "},
        {"reservation_sale_division_code": None},
        {"depart_after": datetime(2000, 1, 1)},
    ],
)
def test_invalid_bus_search_never_fetches_catalog(scripted_client_factory, config, kwargs):
    client, requests, _ = scripted_client_factory([], config=config)
    args = {
        "departure": "시험출발",
        "arrival": "시험도착",
        "service_code": "980",
        "depart_after": MOMENT,
        **kwargs,
    }
    with pytest.raises((KorailProtocolError, ValueError)):
        AirportBusResource(client).search(**args)
    assert requests == []


def test_failed_refresh_keeps_last_valid_bus_catalog(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory(
        [_stops(), _stops(**{"app.limousine.stationCd": []})], config=config
    )
    bus = AirportBusResource(client)
    original = bus.stops()
    with pytest.raises(KorailProtocolError):
        bus.stops(refresh=True)
    assert bus.stops() is original and len(requests) == 2


def test_bus_seats_copy_schedule_identifiers(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory(
        [{"strResult": "SUCC", "seatList": [], "extra": "kept"}], config=config
    )
    schedule = AirportBusSchedule(
        settlement_train_class_code="98",
        train_group_code="980",
        run_date="20990102",
        train_no="00007",
        departure_station_code="9901",
        arrival_station_code="9903",
        departure_run_order="001",
        arrival_run_order="002",
    )
    result = AirportBusResource(client).seats(schedule, passenger_count=2)
    assert result.raw["extra"] == "kept" and result.seats == ()
    form = wire_form(requests[0])
    assert form["trnNo"] == ["00007"] and form["srcarNo"] == ["0001"]
    assert form["dptStnRunOrdr"] == ["001"] and form["arvStnRunOrdr"] == ["002"]
    assert form["totPsgCnt"] == ["2"] and form["isArrow"] == ["false"] and "gdNo" not in form


def test_incomplete_bus_schedule_never_sends(scripted_client_factory, config):
    client, requests, _ = scripted_client_factory([], config=config)
    with pytest.raises(KorailProtocolError, match="train_class_code"):
        AirportBusResource(client).seats(AirportBusSchedule())
    assert requests == []


@pytest.mark.parametrize("count", [0, -1, 10, True, "1"])
def test_invalid_bus_passenger_count_never_sends(scripted_client_factory, config, count):
    client, requests, _ = scripted_client_factory([], config=config)
    with pytest.raises(KorailProtocolError, match="passenger_count"):
        AirportBusResource(client).seats(AirportBusSchedule(), passenger_count=count)
    assert requests == []


@pytest.fixture
def bus_seat_query():
    return AirportBusSeatInventoryQuery(
        train_class_code="98",
        service_code="980",
        run_date="20990102",
        train_no="00007",
        car_no="0001",
        room_class_code="1",
        departure_station_code="9901",
        arrival_station_code="9903",
        seat_attribute_code="015",
        departure_run_order="001",
        arrival_run_order="002",
        passenger_count=-1,
    )


@pytest.mark.parametrize("product_no", [False, 1, 1.5, b"product", [], {}])
def test_bus_product_number_rejects_non_text_before_send(
    scripted_client_factory, config, bus_seat_query, product_no
):
    client, requests, _ = scripted_client_factory([], config=config)
    with pytest.raises(KorailInvalidInputError, match="product_no") as raised:
        client.get_airport_bus_seat_inventory(replace(bus_seat_query, product_no=product_no))
    assert requests == [] and raised.value.request_sent is None


@pytest.mark.parametrize("product_no", [None, "", " ", "SYNTHETIC-PRODUCT"])
def test_bus_product_number_keeps_optional_text_and_low_level_count_policy(
    scripted_client_factory, config, bus_seat_query, product_no
):
    client, requests, pending = scripted_client_factory([{"strResult": "SUCC", "seatList": []}], config=config)
    client.get_airport_bus_seat_inventory(replace(bus_seat_query, product_no=product_no))
    form = wire_form(requests[0])
    assert form["totPsgCnt"] == ["-1"] and form["isArrow"] == ["false"]
    assert form.get("gdNo") == (None if product_no in (None, "") else [product_no])
    assert len(requests) == 1 and pending == []


@pytest.mark.parametrize("kind", ["generator", "dict", "set", "int"])
@pytest.mark.parametrize("authenticated", [False, True])
def test_ticket_maas_requires_a_sequence_without_consuming_unsupported_iterables(
    scripted_client_factory, config, f8_logged_in_session, kind, authenticated
):
    numbers = {
        "generator": (number for number in ("SYNTHETIC-A", "SYNTHETIC-B")),
        "dict": {"SYNTHETIC-A": "ignored"},
        "set": {"SYNTHETIC-A"},
        "int": 1,
    }[kind]
    client, requests, _ = scripted_client_factory(
        [{"strResult": "SUCC"}], config=config, session=f8_logged_in_session if authenticated else None
    )
    with pytest.raises(KorailInvalidInputError if authenticated else KorailAuthError) as raised:
        client.list_maas_menus(pnr_no="SYNTHETIC-PNR", ticket_return_numbers=numbers)
    assert requests == [] and raised.value.request_sent is None
    if kind == "generator":
        assert list(numbers) == ["SYNTHETIC-A", "SYNTHETIC-B"]


@pytest.mark.parametrize("container", [list, tuple, UserList])
def test_ticket_maas_sequences_preserve_return_number_order_and_repeats(
    scripted_client_factory, config, f8_logged_in_session, container
):
    client, requests, pending = scripted_client_factory(
        [{"strResult": "SUCC"}], config=config, session=f8_logged_in_session
    )
    client.list_maas_menus(
        pnr_no="SYNTHETIC-PNR", ticket_return_numbers=container(["SYNTHETIC-A", "SYNTHETIC-A", "SYNTHETIC-B"])
    )
    assert wire_pairs(requests[0])[-4:] == [
        ("pnrNo", "SYNTHETIC-PNR"),
        ("tkRetNo", "SYNTHETIC-A"),
        ("tkRetNo", "SYNTHETIC-A"),
        ("tkRetNo", "SYNTHETIC-B"),
    ]
    assert len(requests) == 1 and pending == []
