from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import Any, get_type_hints
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api import read_models, read_parsers, read_payloads
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession, TrainSummary
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


FREE_SEAT_PATH = "/classes/com.korail.mobile.trn.fresScar.do"
GUIDE_SEAT_PATH = (
    "/classes/com.korail.mobile.reservation.guideSeatCnd.do"
)
ASSIGNMENT_PATH = (
    "/classes/com.korail.mobile.research.assignScheduleView.do"
)
MERGE_SEATS_PATH = (
    "/classes/com.korail.mobile.research.mergeSeatsC.do"
)

NEW_ROUTES = {
    ("POST", FREE_SEAT_PATH),
    ("POST", GUIDE_SEAT_PATH),
    ("POST", ASSIGNMENT_PATH),
    ("POST", MERGE_SEATS_PATH),
}

EXACT_FIELDS = {
    FREE_SEAT_PATH: {
        "Device",
        "Version",
        "Key",
        "runDt",
        "trnNo",
        "dptStnConsOrdr",
        "arvStnConsOrdr",
        "dptStnRunOrdr",
        "arvStnRunOrdr",
    },
    GUIDE_SEAT_PATH: {
        "Device",
        "Version",
        "Key",
        "rqSeatAttCd",
    },
    ASSIGNMENT_PATH: {
        "Device",
        "Version",
        "Key",
        "menuId",
        "dptDt",
        "dptTm",
        "dptRsStnNm",
        "arvRsStnNm",
        "trnGpCd",
        "psrmClCd",
        "seatAttCd1",
        "psgNum1",
        "stlbDturDvNm1",
        "dirtChtnDvCd",
        "chtnArvRsStnNm",
    },
    MERGE_SEATS_PATH: {
        "Device",
        "Version",
        "Key",
        "abrdDt",
        "runDt",
        "trnNo",
        "dptRsStnNm",
        "arvRsStnNm",
        "selRsStnNm",
        "psrmClCd",
        "seatAttCd",
        "totPsgNum",
    },
}

REQUEST_NAMES = (
    "FreeSeatCarRequest",
    "GuideSeatConditionRequest",
    "SeatAssignmentScheduleRequest",
    "MergeSeatsInquiryRequest",
)
MODEL_NAMES = (
    "FreeSeatCarResponse",
    "GuideSeatConditionResponse",
    "TrainScheduleItem",
    "SeatAssignmentScheduleResponse",
    "IntermediateStation",
    "MergeSeatsInquiryResponse",
)
PARSER_NAMES = (
    "parse_free_seat_car_response",
    "parse_guide_seat_condition_response",
    "parse_seat_assignment_schedule_response",
    "parse_merge_seats_inquiry_response",
)


def _require(module: Any, name: str) -> Any:
    value = getattr(module, name, None)
    assert value is not None, f"missing P0 read API symbol: {name}"
    return value


def _request(name: str, **values: Any) -> Any:
    return _require(read_payloads, name)(**values)


def _free_seat_request(**overrides: Any) -> Any:
    values = {
        "run_date": "20990101",
        "train_no": "123",
        "departure_construction_order": "000001",
        "arrival_construction_order": "000010",
        "departure_run_order": "000002",
        "arrival_run_order": "000009",
    }
    values.update(overrides)
    return _request("FreeSeatCarRequest", **values)


def _guide_seat_request(**overrides: Any) -> Any:
    values = {"seat_attribute_code": "052"}
    values.update(overrides)
    return _request("GuideSeatConditionRequest", **values)


def _assignment_request(**overrides: Any) -> Any:
    values = {
        "menu_id": "91",
        "departure_date": "20990101",
        "departure_time": "010203",
        "departure_station_name": "synthetic-origin-request-secret",
        "arrival_station_name": "synthetic-destination-request-secret",
        "train_group_code": "109",
        "room_class_code": "9",
        "seat_attribute_code": "051",
        "passenger_count": 2,
        "standing_detour_division_name": (
            "synthetic-standing-detour-request-secret"
        ),
        "transfer_type_code": "1",
        "connection_arrival_station_name": "",
    }
    values.update(overrides)
    return _request("SeatAssignmentScheduleRequest", **values)


def _merge_request(**overrides: Any) -> Any:
    values = {
        "boarding_datetime": "20990101010203",
        "run_datetime": "20990101010203",
        "train_no": "123",
        "departure_station_name": "synthetic-merge-origin-request-secret",
        "arrival_station_name": (
            "synthetic-merge-destination-request-secret"
        ),
        "selected_station_name": (
            "synthetic-selected-station-request-secret"
        ),
        "room_class_code": "1",
        "seat_attribute_code": "015",
        "passenger_count": 2,
    }
    values.update(overrides)
    return _request("MergeSeatsInquiryRequest", **values)


def _success_envelope(**extra: Any) -> dict[str, Any]:
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": "synthetic-envelope-secret",
        "strResult": "SUCC",
        **extra,
    }


def test_public_symbols_and_request_object_method_signatures_are_exact():
    for name in REQUEST_NAMES:
        request_type = _require(read_payloads, name)
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is request_type
    for name in MODEL_NAMES:
        model_type = _require(read_models, name)
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is model_type

    contracts = {
        "get_free_seat_car_info": (
            "FreeSeatCarRequest",
            "FreeSeatCarResponse",
        ),
        "get_guide_seat_condition": (
            "GuideSeatConditionRequest",
            "GuideSeatConditionResponse",
        ),
        "get_seat_assignment_schedule": (
            "SeatAssignmentScheduleRequest",
            "SeatAssignmentScheduleResponse",
        ),
        "get_merge_seats_inquiry": (
            "MergeSeatsInquiryRequest",
            "MergeSeatsInquiryResponse",
        ),
    }
    for method_name, (request_name, response_name) in contracts.items():
        method = _require(KorailClient, method_name)
        signature = inspect.signature(method)
        assert list(signature.parameters) == ["self", "request"]
        assert signature.parameters["request"].default is (
            inspect.Parameter.empty
        )
        hints = get_type_hints(method)
        assert hints == {
            "request": _require(read_payloads, request_name),
            "return": _require(read_models, response_name),
        }


def test_java_route_names_are_not_duplicate_client_aliases():
    for java_name in (
        "getFresScar",
        "getGuideSeatCnd",
        "getAssignScheduleView",
        "getMergeSeatsInquiry",
    ):
        assert not hasattr(KorailClient, java_name)
    for convenience_name in (
        "to_free_seat_car_request",
        "to_seat_assignment_schedule_request",
        "to_merge_seats_inquiry_request",
    ):
        assert not hasattr(TrainSummary, convenience_name)


def test_request_types_are_frozen_closed_and_repr_safe():
    requests = (
        _free_seat_request(),
        _guide_seat_request(),
        _assignment_request(),
        _merge_request(),
    )
    assert all(is_dataclass(request) for request in requests)
    for request in requests:
        first = fields(request)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(request, first, getattr(request, first))
        assert not hasattr(request, "extra_fields")

    rendered = " ".join(repr(request) for request in requests)
    for secret in (
        "20990101",
        "000001",
        "052",
        "synthetic-origin-request-secret",
        "synthetic-standing-detour-request-secret",
        "synthetic-selected-station-request-secret",
    ):
        assert secret not in rendered


def test_closed_builders_emit_only_exact_apk_field_names():
    cases = (
        (
            "build_free_seat_car_form",
            _free_seat_request(),
            {
                "runDt": "20990101",
                "trnNo": "00123",
                "dptStnConsOrdr": "000001",
                "arvStnConsOrdr": "000010",
                "dptStnRunOrdr": "000002",
                "arvStnRunOrdr": "000009",
            },
        ),
        (
            "build_guide_seat_condition_form",
            _guide_seat_request(),
            {"rqSeatAttCd": "052"},
        ),
        (
            "build_seat_assignment_schedule_form",
            _assignment_request(),
            {
                "menuId": "91",
                "dptDt": "20990101",
                "dptTm": "010203",
                "dptRsStnNm": "synthetic-origin-request-secret",
                "arvRsStnNm": "synthetic-destination-request-secret",
                "trnGpCd": "109",
                "psrmClCd": "9",
                "seatAttCd1": "051",
                "psgNum1": "2",
                "stlbDturDvNm1": (
                    "synthetic-standing-detour-request-secret"
                ),
                "dirtChtnDvCd": "1",
                "chtnArvRsStnNm": "",
            },
        ),
        (
            "build_merge_seats_inquiry_form",
            _merge_request(),
            {
                "abrdDt": "20990101010203",
                "runDt": "20990101010203",
                "trnNo": "00123",
                "dptRsStnNm": "synthetic-merge-origin-request-secret",
                "arvRsStnNm": (
                    "synthetic-merge-destination-request-secret"
                ),
                "selRsStnNm": (
                    "synthetic-selected-station-request-secret"
                ),
                "psrmClCd": "1",
                "seatAttCd": "015",
                "totPsgNum": "2",
            },
        ),
    )
    for builder_name, request, expected in cases:
        builder = _require(read_payloads, builder_name)
        assert builder(request) == expected
        assert all(type(value) is str for value in expected.values())


@pytest.mark.parametrize(
    ("factory", "overrides"),
    (
        (_free_seat_request, {"run_date": "２０９９０１０１"}),
        (_free_seat_request, {"train_no": "12A"}),
        (_free_seat_request, {"departure_run_order": ""}),
        (_guide_seat_request, {"seat_attribute_code": ""}),
        (_guide_seat_request, {"seat_attribute_code": 52}),
        (_assignment_request, {"departure_date": "2099010"}),
        (_assignment_request, {"departure_time": "0102A3"}),
        (_assignment_request, {"departure_station_name": ""}),
        (_assignment_request, {"passenger_count": True}),
        (_assignment_request, {"passenger_count": 0}),
        (_assignment_request, {"passenger_count": 10}),
        (_assignment_request, {"transfer_type_code": "3"}),
        (
            _assignment_request,
            {"connection_arrival_station_name": None},
        ),
        (_merge_request, {"boarding_datetime": "2099010101020"}),
        (_merge_request, {"run_datetime": "２０９９０１０１０１０２０３"}),
        (_merge_request, {"train_no": "123456"}),
        (_merge_request, {"selected_station_name": ""}),
        (_merge_request, {"passenger_count": True}),
        (_merge_request, {"passenger_count": 0}),
        (_merge_request, {"passenger_count": 10}),
    ),
)
def test_invalid_request_values_are_rejected(factory, overrides):
    with pytest.raises(ValueError):
        factory(**overrides)


def test_response_models_are_frozen_and_parsers_map_synthetic_fields(
    load_json_fixture,
):
    free_raw = load_json_fixture("free_seat_car_success.json")
    guide_raw = load_json_fixture("guide_seat_condition_success.json")
    assignment_raw = load_json_fixture(
        "seat_assignment_schedule_success.json"
    )
    merge_raw = load_json_fixture("merge_seats_inquiry_success.json")

    free = _require(
        read_parsers, "parse_free_seat_car_response"
    )(free_raw)
    guide = _require(
        read_parsers, "parse_guide_seat_condition_response"
    )(guide_raw)
    assignment = _require(
        read_parsers, "parse_seat_assignment_schedule_response"
    )(assignment_raw)
    merge = _require(
        read_parsers, "parse_merge_seats_inquiry_response"
    )(merge_raw)

    assert type(free) is _require(read_models, "FreeSeatCarResponse")
    assert free.title == "synthetic-free-seat-title-secret"
    assert free.car_no == "SYNTHETIC-CAR-SECRET"
    assert free.content == "synthetic-free-seat-content-secret"
    assert free.raw is free_raw

    assert type(guide) is _require(
        read_models, "GuideSeatConditionResponse"
    )
    assert guide.h_msg_cd == "S137"
    assert guide.h_msg_txt == "synthetic-guide-message-secret"
    assert guide.raw is guide_raw

    assert type(assignment) is _require(
        read_models, "SeatAssignmentScheduleResponse"
    )
    assert assignment.next_page_flag == "Y"
    assert assignment.merge_reservation_possible_flag == (
        "SYNTHETIC-MERGE-FLAG"
    )
    assert isinstance(assignment.trains, tuple)
    assert len(assignment.trains) == 1
    train = assignment.trains[0]
    assert type(train) is _require(read_models, "TrainScheduleItem")
    assert train.train_no == "99001"
    assert train.train_group_code == "109"
    assert train.train_class_code == "SYNTHETIC-CLASS-CODE"
    assert train.train_class_name == "synthetic-class-name-secret"
    assert train.run_date == "20990101"
    assert train.departure_date == "20990101"
    assert train.departure_time == "010203"
    assert train.arrival_date == "20990101"
    assert train.arrival_time == "040506"
    assert train.departure_station_code == "SYNTHETIC-ORIGIN-CODE"
    assert train.departure_station_name == (
        "synthetic-origin-name-secret"
    )
    assert train.arrival_station_code == "SYNTHETIC-DESTINATION-CODE"
    assert train.arrival_station_name == (
        "synthetic-destination-name-secret"
    )
    assert train.departure_construction_order == "000001"
    assert train.arrival_construction_order == "000010"
    assert train.departure_run_order == "000002"
    assert train.arrival_run_order == "000009"
    assert train.car_type_name == "synthetic-car-type-secret"
    assert train.general_room_name == "synthetic-general-room-secret"
    assert train.special_room_name == "synthetic-special-room-secret"
    assert train.general_reservation_code == "SYNTHETIC-GENERAL-CODE"
    assert train.special_reservation_code == "SYNTHETIC-SPECIAL-CODE"
    assert train.free_seat_reservation_code == "SYNTHETIC-FREE-CODE"
    assert train.standing_reservation_code == "SYNTHETIC-STANDING-CODE"
    assert train.seat_map_flag == "SYNTHETIC-SEAT-MAP-FLAG"
    assert train.delay_sale_flag == "SYNTHETIC-DELAY-FLAG"
    assert train.wait_reservation_flag == "SYNTHETIC-WAIT-FLAG"
    assert train.reservation_possible_name == (
        "synthetic-reservation-possible-secret"
    )
    assert train.special_reservation_possible_name == (
        "synthetic-special-possible-secret"
    )
    assert train.info_text == "synthetic-info-text-secret"
    assert train.popup_message == "synthetic-popup-message-secret"
    assert train.raw is assignment_raw["trn_infos"]["trn_info"][0]

    assert type(merge) is _require(
        read_models, "MergeSeatsInquiryResponse"
    )
    assert merge.merge_reservation_possible_flag == (
        "SYNTHETIC-MERGE-POSSIBLE"
    )
    assert isinstance(merge.intermediate_stations, tuple)
    assert isinstance(merge.trains, tuple)
    assert len(merge.intermediate_stations) == 1
    station = merge.intermediate_stations[0]
    assert type(station) is _require(read_models, "IntermediateStation")
    assert station.code == "SYNTHETIC-MID-STATION-CODE"
    assert station.name == "synthetic-mid-station-name-secret"
    assert station.run_order == "000005"
    assert station.raw is merge_raw["midStnList"][0]
    assert merge.trains[0].train_no == "99002"
    assert merge.raw is merge_raw

    for instance in (free, guide, assignment, train, merge, station):
        assert is_dataclass(instance)
        first = fields(instance)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(instance, first, getattr(instance, first))


def test_response_reprs_hide_identifiers_free_text_and_raw(
    load_json_fixture,
):
    parsed = (
        _require(read_parsers, "parse_free_seat_car_response")(
            load_json_fixture("free_seat_car_success.json")
        ),
        _require(read_parsers, "parse_guide_seat_condition_response")(
            load_json_fixture("guide_seat_condition_success.json")
        ),
        _require(
            read_parsers, "parse_seat_assignment_schedule_response"
        )(load_json_fixture("seat_assignment_schedule_success.json")),
        _require(read_parsers, "parse_merge_seats_inquiry_response")(
            load_json_fixture("merge_seats_inquiry_success.json")
        ),
    )
    rendered = " ".join(
        [repr(item) for item in parsed]
        + [
            repr(parsed[2].trains[0]),
            repr(parsed[3].trains[0]),
            repr(parsed[3].intermediate_stations[0]),
        ]
    )
    for secret in (
        "synthetic-free-seat-envelope-secret",
        "synthetic-free-seat-content-secret",
        "SYNTHETIC-CAR-SECRET",
        "synthetic-free-seat-title-secret",
        "synthetic-free-seat-raw-secret",
        "synthetic-guide-message-secret",
        "synthetic-guide-raw-secret",
        "99001",
        "synthetic-origin-name-secret",
        "synthetic-info-text-secret",
        "synthetic-assignment-row-raw-secret",
        "SYNTHETIC-MID-STATION-CODE",
        "synthetic-mid-station-name-secret",
        "synthetic-merge-train-raw-secret",
    ):
        assert secret not in rendered


@pytest.mark.parametrize("parser_name", PARSER_NAMES)
def test_route_parsers_preserve_strict_envelope_and_error_handling(
    parser_name,
):
    parser = _require(read_parsers, parser_name)
    with pytest.raises(KorailProtocolError):
        parser({"h_msg_cd": "SYNTHETIC.OK", "h_msg_txt": None})
    with pytest.raises(KorailProtocolError):
        parser(
            {
                "h_msg_cd": "SYNTHETIC.OK",
                "h_msg_txt": 7,
                "strResult": "SUCC",
            }
        )
    with pytest.raises(KorailAppError):
        parser(
            {
                "h_msg_cd": "SYNTHETIC.FAIL",
                "h_msg_txt": "synthetic failure",
                "strResult": "FAIL",
            }
        )
    with pytest.raises(KorailSessionExpiredError):
        parser(
            {
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic expiry",
                "strResult": "FAIL",
            }
        )
    with pytest.raises(KorailAppError):
        parser(
            {
                "h_msg_cd": "WRC000288",
                "h_msg_txt": "synthetic WRC failure",
                "strResult": "SUCC",
            }
        )


@pytest.mark.parametrize("parser_name", PARSER_NAMES)
@pytest.mark.parametrize("str_result", (None, "", "ERROR", "SUCCESS"))
def test_new_route_parsers_require_exact_succ_result(
    parser_name,
    str_result,
):
    parser = _require(read_parsers, parser_name)
    with pytest.raises(KorailProtocolError):
        parser(
            {
                "h_msg_cd": "SYNTHETIC.OK",
                "h_msg_txt": None,
                "strResult": str_result,
            }
        )


@pytest.mark.parametrize(
    ("parser_name", "raw"),
    (
        (
            "parse_free_seat_car_response",
            _success_envelope(fresTtl=7),
        ),
        (
            "parse_seat_assignment_schedule_response",
            _success_envelope(trn_infos=[]),
        ),
        (
            "parse_seat_assignment_schedule_response",
            _success_envelope(trn_infos={"trn_info": ["not-an-object"]}),
        ),
        (
            "parse_seat_assignment_schedule_response",
            _success_envelope(
                trn_infos={"trn_info": [{"h_trn_no": 99001}]}
            ),
        ),
        (
            "parse_merge_seats_inquiry_response",
            _success_envelope(midStnList={}),
        ),
        (
            "parse_merge_seats_inquiry_response",
            _success_envelope(midStnList=["not-an-object"]),
        ),
        (
            "parse_merge_seats_inquiry_response",
            _success_envelope(midStnList=[{"runOrdr": True}]),
        ),
    ),
)
def test_route_parsers_reject_malformed_documented_shapes(parser_name, raw):
    with pytest.raises(KorailProtocolError):
        _require(read_parsers, parser_name)(raw)


def test_null_documented_optional_containers_parse_as_empty_tuples():
    assignment = _require(
        read_parsers, "parse_seat_assignment_schedule_response"
    )(
        _success_envelope(
            h_next_pg_flg=None,
            trn_infos=None,
        )
    )
    merge = _require(
        read_parsers, "parse_merge_seats_inquiry_response"
    )(
        _success_envelope(
            midStnList=None,
            trn_infos=None,
        )
    )
    assert assignment.trains == ()
    assert assignment.next_page_flag is None
    assert assignment.merge_reservation_possible_flag is None
    assert merge.intermediate_stations == ()
    assert merge.trains == ()
    assert merge.merge_reservation_possible_flag is None


def test_safety_registry_has_only_exact_new_read_contracts():
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    assert len(KORAIL_READ_ONLY_ROUTES) == 31
    for path, expected_fields in EXACT_FIELDS.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == frozenset(
            expected_fields
        )
        values = {field: "synthetic" for field in expected_fields}
        assert_read_only_request_fields(path, values)
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(
                path,
                {**values, "unexpected": "blocked"},
            )
        missing = dict(values)
        missing.pop(next(iter(expected_fields)))
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(path, missing)
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("GET", path)

    for mutation in (
        "/classes/com.korail.mobile.reservation.seatAssign.do",
        "/classes/com.korail.mobile.reservation.TicketReservation",
        "/classes/com.korail.mobile.nonMember.NonMemTicket",
        "/classes/com.korail.mobile.reservation.reservationChange.do",
    ):
        assert ("POST", mutation) not in KORAIL_READ_ONLY_ROUTES
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("POST", mutation)


def test_client_methods_post_one_exact_form_without_auth_or_dynapath(
    load_json_fixture,
):
    fixtures = {
        FREE_SEAT_PATH: "free_seat_car_success.json",
        GUIDE_SEAT_PATH: "guide_seat_condition_success.json",
        ASSIGNMENT_PATH: "seat_assignment_schedule_success.json",
        MERGE_SEATS_PATH: "merge_seats_inquiry_success.json",
    }
    calls: list[httpx.Request] = []
    token_contexts = []

    def token_provider(context):
        token_contexts.append(context)
        return "must-not-be-used"

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json=load_json_fixture(fixtures[request.url.path]),
        )

    config = KorailConfig(
        device="SYNTHETIC-DEVICE",
        version="SYNTHETIC-VERSION",
        key="SYNTHETIC-KEY",
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset(fixtures),
        ),
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    assert client.session.current is None
    try:
        results = (
            client.get_free_seat_car_info(_free_seat_request()),
            client.get_guide_seat_condition(_guide_seat_request()),
            client.get_seat_assignment_schedule(_assignment_request()),
            client.get_merge_seats_inquiry(_merge_request()),
        )
    finally:
        client.close()

    assert [type(result) for result in results] == [
        _require(read_models, "FreeSeatCarResponse"),
        _require(read_models, "GuideSeatConditionResponse"),
        _require(read_models, "SeatAssignmentScheduleResponse"),
        _require(read_models, "MergeSeatsInquiryResponse"),
    ]
    assert len(calls) == 4
    assert [request.method for request in calls] == ["POST"] * 4
    assert [request.url.path for request in calls] == [
        FREE_SEAT_PATH,
        GUIDE_SEAT_PATH,
        ASSIGNMENT_PATH,
        MERGE_SEATS_PATH,
    ]
    assert all(request.url.query == b"" for request in calls)
    assert all(
        set(
            parse_qs(
                request.content.decode(),
                keep_blank_values=True,
            )
        )
        == EXACT_FIELDS[request.url.path]
        for request in calls
    )
    assert all(
        all(
            len(values) == 1
            for values in parse_qs(
                request.content.decode(),
                keep_blank_values=True,
            ).values()
        )
        for request in calls
    )
    assert token_contexts == []
    assert all(
        "x-dynapath-m-token" not in request.headers for request in calls
    )


@pytest.mark.parametrize(
    ("method_name", "request_factory"),
    (
        ("get_free_seat_car_info", _free_seat_request),
        ("get_guide_seat_condition", _guide_seat_request),
        ("get_seat_assignment_schedule", _assignment_request),
        ("get_merge_seats_inquiry", _merge_request),
    ),
)
def test_p058_from_every_new_read_clears_existing_session(
    method_name,
    request_factory,
):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic expiry",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session-secret",
        member_no="synthetic-member-secret",
    )
    client.http.cookies.set("JSESSIONID", "synthetic-session-secret")
    try:
        with pytest.raises(KorailSessionExpiredError):
            _require(client, method_name)(request_factory())
    finally:
        client.close()
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies


@pytest.mark.parametrize(
    ("method_name", "wrong_request_factory"),
    (
        ("get_free_seat_car_info", _guide_seat_request),
        ("get_guide_seat_condition", _free_seat_request),
        ("get_seat_assignment_schedule", _merge_request),
        ("get_merge_seats_inquiry", _assignment_request),
    ),
)
def test_client_rejects_wrong_request_type_before_transport(
    method_name,
    wrong_request_factory,
):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not run")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TypeError):
            _require(client, method_name)(wrong_request_factory())
    finally:
        client.close()
    assert calls == 0
