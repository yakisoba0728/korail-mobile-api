from __future__ import annotations

import inspect
from collections.abc import Iterator, Mapping
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from pathlib import Path
from typing import Any, get_type_hints
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api
import korail_mobile_api.client as client_module
from korail_mobile_api import (
    KorailClient,
    KorailConfig,
    LimousineRecommendedProduct,
    LimousineSchedule,
    LimousineScheduleQuery,
    LimousineScheduleResponse,
    LimousineScheduleViewQuery,
    LimousineScheduleViewResponse,
    LimousineScheduleViewTrain,
    LimousineSeat,
    LimousineSeatInventoryQuery,
    LimousineSeatInventoryResponse,
)
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.limousine_parsers import (
    parse_limousine_schedule_response,
    parse_limousine_schedule_view_response,
    parse_limousine_seat_inventory_response,
)
from korail_mobile_api.limousine_payloads import (
    build_limousine_schedule_form,
    build_limousine_schedule_view_form,
    build_limousine_seat_inventory_form,
)
from korail_mobile_api.models import BaseKorailResponse, KorailSession
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


SCHEDULE_PATH = "/classes/com.korail.mobile.lmu.scdlQry.do"
SEAT_PATH = "/classes/com.korail.mobile.lms.TResidualSeatsResearch.do"
VIEW_PATH = "/classes/com.korail.mobile.seatMovie.LimousineScheduleView"

SCHEDULE_FIELDS = frozenset(
    {
        "Device",
        "Version",
        "Key",
        "dptDt",
        "dptRsStnCd",
        "arvRsStnCd",
        "tmGpCd",
        "psrmClCd",
        "dptTm",
        "trnNo",
        "seatAttCd",
        "rsvSaleDvCd",
    }
)
SEAT_FIELDS = frozenset(
    {
        "Device",
        "Version",
        "Key",
        "trnClsfCd",
        "trnGpCd",
        "runDt",
        "trnNo",
        "srcarNo",
        "psrmClCd",
        "dptRsStnCd",
        "arvRsStnCd",
        "seatAttCd",
        "dptStnRunOrdr",
        "arvStnRunOrdr",
        "totPsgCnt",
        "gdNo",
        "isArrow",
    }
)
VIEW_FIELDS = frozenset(
    {
        "Device",
        "Version",
        "Sid",
        "txtMenuId",
        "radJobId",
        "txtJobDv",
        "selGoTrain",
        "txtTrnGpCd",
        "txtGoTrnNo",
        "txtGoStart",
        "txtGoEnd",
        "txtGoAbrdDt",
        "txtGoHour",
        "txtPsgFlg_1",
        "txtPsgFlg_2",
        "txtPsgFlg_3",
        "txtPsgFlg_4",
        "txtPsgFlg_5",
        "txtSeatAttCd_2",
        "txtSeatAttCd_3",
        "txtSeatAttCd_4",
        "ebizCrossCheck",
        "srtCheckYn",
        "rtYn",
    }
)


class _ScheduleQueryValidationBypass(LimousineScheduleQuery):
    def __post_init__(self) -> None:
        pass


class _SeatQueryValidationBypass(LimousineSeatInventoryQuery):
    def __post_init__(self) -> None:
        pass


class _ViewQueryValidationBypass(LimousineScheduleViewQuery):
    def __post_init__(self) -> None:
        pass


@pytest.fixture
def schedule_query() -> LimousineScheduleQuery:
    return LimousineScheduleQuery(
        departure_date="20991231",
        departure_station_code="9001",
        arrival_station_code="9002",
        service_code="777",
        room_class_code="8",
        departure_time="220000",
        train_no="",
        seat_attribute_code="",
        reservation_sale_division_code="SYNTHETIC-SALE",
    )


@pytest.fixture
def seat_query() -> LimousineSeatInventoryQuery:
    return LimousineSeatInventoryQuery(
        train_class_code="77",
        service_code="777",
        run_date="20991231",
        train_no="54321",
        car_no="0007",
        room_class_code="8",
        departure_station_code="9001",
        arrival_station_code="9002",
        seat_attribute_code="888",
        departure_run_order="000123",
        arrival_run_order="000456",
        passenger_count=2,
        product_no="",
        is_arrow=False,
    )


@pytest.fixture
def view_query() -> LimousineScheduleViewQuery:
    return LimousineScheduleViewQuery(
        menu_id="77",
        job_id="2",
        job_division="SYNTHETIC-JOB-DIVISION",
        service_code="777",
        train_no="",
        departure_station_name="Synthetic Departure",
        arrival_station_name="Synthetic Arrival",
        departure_date="20991231",
        departure_time="220000",
        passenger_group_1_count=1,
        passenger_group_2_count=1,
        senior_count=0,
        severe_disability_count=0,
        mild_disability_count=0,
        direction_seat_attribute_code="111",
        location_seat_attribute_code="222",
        room_seat_attribute_code="333",
        ebiz_cross_check=False,
        srt_check=True,
        round_trip=False,
    )


def _base(raw: dict[str, Any]) -> BaseKorailResponse:
    return BaseKorailResponse.from_raw(raw)


def test_public_queries_and_response_models_are_frozen_and_exported(
    schedule_query,
    seat_query,
    view_query,
):
    instances = (
        schedule_query,
        seat_query,
        view_query,
        LimousineSchedule(),
        LimousineScheduleResponse(),
        LimousineSeat(),
        LimousineSeatInventoryResponse(),
        LimousineRecommendedProduct(),
        LimousineScheduleViewTrain(),
        LimousineScheduleViewResponse(),
    )
    expected_names = {type(instance).__name__ for instance in instances}
    assert all(is_dataclass(instance) for instance in instances)
    for instance in instances:
        first_field = fields(instance)[0]
        with pytest.raises(FrozenInstanceError):
            setattr(instance, first_field.name, getattr(instance, first_field.name))
    assert expected_names <= set(korail_mobile_api.__all__)
    for name in expected_names:
        assert getattr(korail_mobile_api, name) is globals()[name]


def test_query_reprs_hide_every_runtime_identifier_and_free_text(
    schedule_query,
    seat_query,
    view_query,
):
    rendered = f"{schedule_query!r} {seat_query!r} {view_query!r}"
    for secret in (
        "20991231",
        "9001",
        "9002",
        "777",
        "54321",
        "0007",
        "SYNTHETIC-SALE",
        "SYNTHETIC-JOB-DIVISION",
        "Synthetic Departure",
        "Synthetic Arrival",
    ):
        assert secret not in rendered


def test_closed_queries_reject_unknown_fields(schedule_query):
    values = {
        field.name: getattr(schedule_query, field.name)
        for field in fields(schedule_query)
    }
    values["arbitrary_wire_field"] = "must-not-pass"
    with pytest.raises(TypeError):
        LimousineScheduleQuery(**values)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("departure_date", "2099-12-31"),
        ("departure_date", "２０９９１２３１"),
        ("departure_station_code", "90A1"),
        ("arrival_station_code", "９００２"),
        ("service_code", ""),
        ("service_code", "77A"),
        ("room_class_code", ""),
        ("departure_time", "22:00:00"),
        ("train_no", "12A"),
        ("seat_attribute_code", "  "),
        ("reservation_sale_division_code", ""),
    ],
)
def test_schedule_query_rejects_malformed_runtime_values(
    schedule_query,
    field_name,
    value,
):
    with pytest.raises((TypeError, ValueError), match=field_name):
        replace(schedule_query, **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("train_class_code", "7A"),
        ("service_code", "７７７"),
        ("run_date", "2099-12-31"),
        ("train_no", ""),
        ("car_no", ""),
        ("car_no", "7A"),
        ("room_class_code", ""),
        ("departure_station_code", "901"),
        ("arrival_station_code", "90020"),
        ("seat_attribute_code", "88A"),
        ("departure_run_order", "123"),
        ("arrival_run_order", "１２３４５６"),
        ("passenger_count", True),
        ("passenger_count", 0),
        ("passenger_count", 10),
        ("product_no", "   "),
        ("is_arrow", "false"),
    ],
)
def test_seat_query_rejects_malformed_runtime_values(
    seat_query,
    field_name,
    value,
):
    with pytest.raises((TypeError, ValueError), match=field_name):
        replace(seat_query, **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("menu_id", ""),
        ("menu_id", "7A"),
        ("job_id", ""),
        ("job_division", "   "),
        ("service_code", "77A"),
        ("train_no", "５４３２１"),
        ("departure_station_name", ""),
        ("arrival_station_name", "   "),
        ("departure_date", "2099-12-31"),
        ("departure_time", "2200"),
        ("passenger_group_1_count", True),
        ("passenger_group_2_count", -1),
        ("senior_count", 10),
        ("direction_seat_attribute_code", "11A"),
        ("location_seat_attribute_code", "２２２"),
        ("room_seat_attribute_code", ""),
        ("ebiz_cross_check", "N"),
        ("srt_check", 0),
        ("round_trip", "false"),
    ],
)
def test_schedule_view_query_rejects_malformed_runtime_values(
    view_query,
    field_name,
    value,
):
    with pytest.raises((TypeError, ValueError), match=field_name):
        replace(view_query, **{field_name: value})


def test_schedule_view_query_requires_at_least_one_passenger(view_query):
    with pytest.raises(ValueError, match="passenger"):
        replace(
            view_query,
            passenger_group_1_count=0,
            passenger_group_2_count=0,
            senior_count=0,
            severe_disability_count=0,
            mild_disability_count=0,
        )


def test_builders_emit_only_exact_retrofit_fields_and_caller_values(
    schedule_query,
    seat_query,
    view_query,
):
    config = KorailConfig()
    schedule = build_limousine_schedule_form(config, schedule_query)
    seat = build_limousine_seat_inventory_form(config, seat_query)
    view = build_limousine_schedule_view_form(
        config,
        view_query,
        sid="synthetic-fresh-sid",
    )

    assert set(schedule) == SCHEDULE_FIELDS
    assert schedule == {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "dptDt": "20991231",
        "dptRsStnCd": "9001",
        "arvRsStnCd": "9002",
        "tmGpCd": "777",
        "psrmClCd": "8",
        "dptTm": "220000",
        "trnNo": "",
        "seatAttCd": "",
        "rsvSaleDvCd": "SYNTHETIC-SALE",
    }
    assert set(seat) == SEAT_FIELDS
    assert seat == {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "trnClsfCd": "77",
        "trnGpCd": "777",
        "runDt": "20991231",
        "trnNo": "54321",
        "srcarNo": "0007",
        "psrmClCd": "8",
        "dptRsStnCd": "9001",
        "arvRsStnCd": "9002",
        "seatAttCd": "888",
        "dptStnRunOrdr": "000123",
        "arvStnRunOrdr": "000456",
        "totPsgCnt": "2",
        "gdNo": "",
        "isArrow": "false",
    }
    assert set(view) == VIEW_FIELDS
    assert view == {
        "Device": config.device,
        "Version": config.version,
        "Sid": "synthetic-fresh-sid",
        "txtMenuId": "77",
        "radJobId": "2",
        "txtJobDv": "SYNTHETIC-JOB-DIVISION",
        "selGoTrain": "777",
        "txtTrnGpCd": "777",
        "txtGoTrnNo": "",
        "txtGoStart": "Synthetic Departure",
        "txtGoEnd": "Synthetic Arrival",
        "txtGoAbrdDt": "20991231",
        "txtGoHour": "220000",
        "txtPsgFlg_1": "1",
        "txtPsgFlg_2": "1",
        "txtPsgFlg_3": "0",
        "txtPsgFlg_4": "0",
        "txtPsgFlg_5": "0",
        "txtSeatAttCd_2": "111",
        "txtSeatAttCd_3": "222",
        "txtSeatAttCd_4": "333",
        "ebizCrossCheck": "N",
        "srtCheckYn": "Y",
        "rtYn": "N",
    }


def test_builders_preserve_statically_empty_optional_limousine_fields(
    seat_query,
    view_query,
):
    seat = build_limousine_seat_inventory_form(
        KorailConfig(),
        replace(seat_query, seat_attribute_code=""),
    )
    view = build_limousine_schedule_view_form(
        KorailConfig(),
        replace(view_query, job_division=""),
        sid="synthetic-fresh-sid",
    )
    assert seat["seatAttCd"] == ""
    assert view["txtJobDv"] == ""


@pytest.mark.parametrize("sid", ["", "   ", None, 1])
def test_schedule_view_builder_rejects_invalid_sid(view_query, sid):
    with pytest.raises((TypeError, ValueError), match="sid"):
        build_limousine_schedule_view_form(
            KorailConfig(),
            view_query,
            sid=sid,
        )


@pytest.mark.parametrize(
    (
        "fixture_name",
        "bypass_type",
        "invalid_field",
        "invalid_value",
        "builder",
        "method_name",
    ),
    [
        (
            "schedule_query",
            _ScheduleQueryValidationBypass,
            "departure_date",
            "invalid-date",
            build_limousine_schedule_form,
            "get_limousine_schedules",
        ),
        (
            "seat_query",
            _SeatQueryValidationBypass,
            "passenger_count",
            0,
            build_limousine_seat_inventory_form,
            "get_limousine_seat_inventory",
        ),
        (
            "view_query",
            _ViewQueryValidationBypass,
            "menu_id",
            "invalid-menu",
            build_limousine_schedule_view_form,
            "get_limousine_schedule_view",
        ),
    ],
)
def test_query_subclass_cannot_bypass_builder_or_reach_transport(
    request,
    monkeypatch,
    fixture_name,
    bypass_type,
    invalid_field,
    invalid_value,
    builder,
    method_name,
):
    base_query = request.getfixturevalue(fixture_name)
    values = {
        model_field.name: getattr(base_query, model_field.name)
        for model_field in fields(base_query)
    }
    values[invalid_field] = invalid_value
    bypass_query = bypass_type(**values)
    builder_kwargs = (
        {"sid": "synthetic-fresh-sid"}
        if method_name == "get_limousine_schedule_view"
        else {}
    )

    with pytest.raises(TypeError, match=type(base_query).__name__):
        builder(KorailConfig(), bypass_query, **builder_kwargs)

    sid_calls = 0
    transport_calls = 0

    def fake_sid() -> str:
        nonlocal sid_calls
        sid_calls += 1
        return "synthetic-client-sid"

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TypeError, match=type(base_query).__name__):
            getattr(client, method_name)(bypass_query)
    finally:
        client.close()
    assert sid_calls == 0
    assert transport_calls == 0


def test_schedule_parser_maps_every_static_bus_field_and_hides_sensitive_repr(
    load_json_fixture,
):
    raw = load_json_fixture("limousine_schedule_success.json")
    result = parse_limousine_schedule_response(_base(raw))
    assert result.following_page_extension == "SYNTHETIC-FOLLOW"
    assert result.long_short_division_code == "SYNTHETIC-LENGTH-DIVISION"
    assert isinstance(result.schedules, tuple)
    assert len(result.schedules) == 1
    schedule = result.schedules[0]
    assert schedule.arrival_date == "20991231"
    assert schedule.arrival_station_code == "9002"
    assert schedule.arrival_run_order == "000456"
    assert schedule.arrival_time == "235959"
    assert schedule.transfer_division_code == "SYNTHETIC-TRANSFER"
    assert schedule.departure_date == "20991231"
    assert schedule.departure_station_code == "9001"
    assert schedule.departure_run_order == "000123"
    assert schedule.departure_time == "220000"
    assert schedule.general_remaining_seat_count == "12"
    assert schedule.delay_minutes == "0"
    assert schedule.free_remaining_seat_count == "2"
    assert schedule.standing_remaining_seat_count == "3"
    assert schedule.run_date == "20991231"
    assert schedule.special_remaining_seat_count == "4"
    assert schedule.train_class_code == "77"
    assert schedule.service_code == "777"
    assert schedule.train_no == "54321"
    assert schedule.train_order_no == "SYNTHETIC-ORDER"
    assert schedule.yms_application_flag == "SYNTHETIC-YMS"
    assert result.raw is raw
    rendered = f"{result!r} {schedule!r}"
    for secret in (
        "synthetic-schedule-envelope-secret",
        "SYNTHETIC-FOLLOW",
        "synthetic-schedule-raw-secret",
        "synthetic-schedule-response-raw-secret",
        "54321",
        "9001",
        "9002",
    ):
        assert secret not in rendered


def test_seat_parser_maps_static_inventory_and_hides_ids_messages_and_raw(
    load_json_fixture,
):
    raw = load_json_fixture("limousine_seat_inventory_success.json")
    result = parse_limousine_seat_inventory_response(_base(raw))
    assert result.car_type_code == "SYNTHETIC-CAR-TYPE"
    assert result.car_no == "0007"
    assert result.seat_arrangement_code == "SYNTHETIC-ARRANGEMENT"
    assert result.up_down_division_code == "SYNTHETIC-DIRECTION"
    assert isinstance(result.seats, tuple)
    assert len(result.seats) == 2
    seat = result.seats[0]
    assert seat.direction_attribute_code == "SYNTHETIC-DIRECTION-ATTRIBUTE"
    assert seat.other_attribute_code == "SYNTHETIC-OTHER-ATTRIBUTE"
    assert seat.integrated_message == "synthetic-seat-message-secret"
    assert seat.integrated_message_code == "SYNTHETIC-MESSAGE-CODE"
    assert seat.requested_attribute_code == "SYNTHETIC-REQUESTED-ATTRIBUTE"
    assert seat.sale_possible_flag == "Y"
    assert seat.seat_no == "SYNTHETIC-SEAT-01"
    assert seat.specification == "SYNTHETIC-SPECIFICATION"
    assert seat.sequence_no == "SYNTHETIC-SEQUENCE-01"
    assert seat.visual_message_division_code == "SYNTHETIC-VISUAL-CODE"
    assert result.raw is raw
    rendered = f"{result!r} {seat!r}"
    for secret in (
        "synthetic-seat-envelope-secret",
        "synthetic-seat-message-secret",
        "SYNTHETIC-SEAT-01",
        "0007",
        "synthetic-seat-row-raw-secret",
        "synthetic-seat-response-raw-secret",
    ):
        assert secret not in rendered


def test_schedule_view_parser_maps_static_paging_train_and_product_fields(
    load_json_fixture,
):
    raw = load_json_fixture("limousine_schedule_view_success.json")
    result = parse_limousine_schedule_view_response(_base(raw))
    assert result.next_ectb_train_no == "SYNTHETIC-NEXT-ECTB"
    assert result.goods_no == "SYNTHETIC-GOODS-ID"
    assert result.next_page_flag == "SYNTHETIC-NEXT-PAGE"
    assert result.notice_message == "synthetic-view-notice-secret"
    assert result.next_preceding_train_no == "SYNTHETIC-NEXT-PRECEDING"
    assert result.next_query_station_no == "SYNTHETIC-NEXT-QUERY-STATION"
    assert result.result_count == "1"
    assert result.next_train_no == "SYNTHETIC-NEXT-TRAIN"
    assert result.merge_reservation_possible_flag == "SYNTHETIC-MERGE-FLAG"
    assert isinstance(result.schedules, tuple)
    train = result.schedules[0]
    assert train.departure_station_code == "9001"
    assert train.departure_station_name == "Synthetic Departure"
    assert train.departure_run_order == "000123"
    assert train.arrival_station_code == "9002"
    assert train.arrival_station_name == "Synthetic Arrival"
    assert train.arrival_run_order == "000456"
    assert train.run_date == "20991231"
    assert train.train_class_code == "77"
    assert train.train_class_name == "Synthetic Train Class"
    assert train.service_code == "777"
    assert train.train_no == "54321"
    assert train.seat_attribute_code == "333"
    assert train.total_passenger_count == 2
    assert isinstance(train.recommended_products, tuple)
    product = train.recommended_products[0]
    assert product.goods_no == "SYNTHETIC-PRODUCT-ID"
    assert product.goods_name == "Synthetic Product Name"
    assert product.discount_amount == "SYNTHETIC-DISCOUNT-AMOUNT"
    assert result.raw is raw
    rendered = f"{result!r} {train!r} {product!r}"
    for secret in (
        "synthetic-view-envelope-secret",
        "synthetic-view-notice-secret",
        "Synthetic Departure",
        "Synthetic Arrival",
        "54321",
        "SYNTHETIC-PRODUCT-ID",
        "synthetic-product-raw-secret",
        "synthetic-view-row-raw-secret",
        "synthetic-view-response-raw-secret",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    ("fixture", "mutate", "parser"),
    [
        (
            "limousine_schedule_success.json",
            lambda raw: raw.__setitem__("trainList", {}),
            parse_limousine_schedule_response,
        ),
        (
            "limousine_schedule_success.json",
            lambda raw: raw["trainList"].__setitem__(0, "not-an-object"),
            parse_limousine_schedule_response,
        ),
        (
            "limousine_schedule_success.json",
            lambda raw: raw["trainList"][0].__setitem__("trnNo", 1),
            parse_limousine_schedule_response,
        ),
        (
            "limousine_seat_inventory_success.json",
            lambda raw: raw.__setitem__("seatList", None),
            parse_limousine_seat_inventory_response,
        ),
        (
            "limousine_seat_inventory_success.json",
            lambda raw: raw["seatList"].__setitem__(0, []),
            parse_limousine_seat_inventory_response,
        ),
        (
            "limousine_seat_inventory_success.json",
            lambda raw: raw["seatList"][0].__setitem__("seat_no", 1),
            parse_limousine_seat_inventory_response,
        ),
        (
            "limousine_schedule_view_success.json",
            lambda raw: raw.__setitem__("trn_infos", []),
            parse_limousine_schedule_view_response,
        ),
        (
            "limousine_schedule_view_success.json",
            lambda raw: raw["trn_infos"].__setitem__("trn_info", {}),
            parse_limousine_schedule_view_response,
        ),
        (
            "limousine_schedule_view_success.json",
            lambda raw: raw["trn_infos"]["trn_info"][0].__setitem__(
                "h_trn_no", 1
            ),
            parse_limousine_schedule_view_response,
        ),
        (
            "limousine_schedule_view_success.json",
            lambda raw: raw["trn_infos"]["trn_info"][0].__setitem__(
                "totPsgCnt", True
            ),
            parse_limousine_schedule_view_response,
        ),
        (
            "limousine_schedule_view_success.json",
            lambda raw: raw["trn_infos"]["trn_info"][0][
                "rcmdGdList"
            ][0].__setitem__("gdNo", 1),
            parse_limousine_schedule_view_response,
        ),
    ],
)
def test_parsers_reject_malformed_documented_containers_and_scalars(
    load_json_fixture,
    fixture,
    mutate,
    parser,
):
    raw = load_json_fixture(fixture)
    mutate(raw)
    with pytest.raises(KorailProtocolError):
        parser(_base(raw))


def test_schedule_parsers_accept_statically_nullable_empty_containers(
    load_json_fixture,
):
    schedule_raw = load_json_fixture("limousine_schedule_success.json")
    schedule_raw["trainList"] = None
    view_raw = load_json_fixture("limousine_schedule_view_success.json")
    view_raw["trn_infos"] = None
    assert parse_limousine_schedule_response(_base(schedule_raw)).schedules == ()
    assert parse_limousine_schedule_view_response(_base(view_raw)).schedules == ()


def test_safety_registers_only_the_three_exact_new_post_contracts():
    assert len(KORAIL_READ_ONLY_ROUTES) == 38
    expected = {
        SCHEDULE_PATH: SCHEDULE_FIELDS,
        SEAT_PATH: SEAT_FIELDS,
        VIEW_PATH: VIEW_FIELDS,
    }
    for path, request_fields in expected.items():
        assert ("POST", path) in KORAIL_READ_ONLY_ROUTES
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == request_fields
        assert_read_only_route("POST", path)
        assert_read_only_request_fields(
            path,
            {name: "" for name in request_fields},
        )


@pytest.mark.parametrize(
    ("path", "request_fields"),
    [
        (SCHEDULE_PATH, SCHEDULE_FIELDS),
        (SEAT_PATH, SEAT_FIELDS),
        (VIEW_PATH, VIEW_FIELDS),
    ],
)
def test_limousine_safety_rejects_missing_and_extra_fields(
    path,
    request_fields,
):
    missing = {name: "" for name in request_fields - {next(iter(request_fields))}}
    extra = {name: "" for name in request_fields}
    extra["arbitraryMutationField"] = "must-not-pass"
    with pytest.raises(KorailProtocolError, match="exactly"):
        assert_read_only_request_fields(path, missing)
    with pytest.raises(KorailProtocolError, match="exactly"):
        assert_read_only_request_fields(path, extra)


class _DuplicateFieldMapping(Mapping[str, str]):
    def __init__(self, values: dict[str, str], duplicate: str) -> None:
        self._values = values
        self._keys = [*values, duplicate]

    def __getitem__(self, key: str) -> str:
        return self._values[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)


@pytest.mark.parametrize(
    ("path", "request_fields"),
    [
        (SCHEDULE_PATH, SCHEDULE_FIELDS),
        (SEAT_PATH, SEAT_FIELDS),
        (VIEW_PATH, VIEW_FIELDS),
    ],
)
def test_limousine_safety_rejects_duplicate_prepared_fields(
    path,
    request_fields,
):
    values = {name: "" for name in request_fields}
    duplicate = _DuplicateFieldMapping(values, next(iter(request_fields)))
    with pytest.raises(KorailProtocolError, match="duplicate"):
        assert_read_only_request_fields(path, duplicate)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", SCHEDULE_PATH),
        ("GET", SEAT_PATH),
        ("GET", VIEW_PATH),
        ("POST", "/classes/com.korail.mobile.lmu.scdlQry"),
        ("POST", "/classes/com.korail.mobile.lms.TResidualSeatsResearch"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"),
        ("POST", "/classes/com.korail.mobile.certification.TicketReservation"),
        ("POST", "/classes/com.korail.mobile.reservation.seatAssign.do"),
        ("POST", "/classes/com.korail.mobile.reservation.ReservationPayment"),
    ],
)
def test_limousine_safety_rejects_wrong_methods_and_adjacent_routes(
    method,
    path,
):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route(method, path)


def test_limousine_methods_have_closed_public_signatures_and_hints():
    expected = {
        "get_limousine_schedules": (
            LimousineScheduleQuery,
            LimousineScheduleResponse,
        ),
        "get_limousine_seat_inventory": (
            LimousineSeatInventoryQuery,
            LimousineSeatInventoryResponse,
        ),
        "get_limousine_schedule_view": (
            LimousineScheduleViewQuery,
            LimousineScheduleViewResponse,
        ),
    }
    for method_name, (query_type, response_type) in expected.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == ["self", "query"]
        assert get_type_hints(method) == {
            "query": query_type,
            "return": response_type,
        }


def test_limousine_methods_post_once_without_session_or_dynapath(
    schedule_query,
    seat_query,
    view_query,
    load_json_fixture,
    monkeypatch,
):
    requests: list[httpx.Request] = []
    token_contexts = []
    generated_sids: list[str] = []
    payloads = {
        SCHEDULE_PATH: load_json_fixture("limousine_schedule_success.json"),
        SEAT_PATH: load_json_fixture("limousine_seat_inventory_success.json"),
        VIEW_PATH: load_json_fixture("limousine_schedule_view_success.json"),
    }

    def fake_sid() -> str:
        generated_sids.append("synthetic-client-sid")
        return "synthetic-client-sid"

    def token_provider(context):
        token_contexts.append(context)
        raise AssertionError("DynaPath must not run")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payloads[request.url.path])

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset(payloads),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    assert client.session.current is None
    try:
        schedules = client.get_limousine_schedules(schedule_query)
        seats = client.get_limousine_seat_inventory(seat_query)
        view = client.get_limousine_schedule_view(view_query)
    finally:
        client.close()

    assert type(schedules) is LimousineScheduleResponse
    assert type(seats) is LimousineSeatInventoryResponse
    assert type(view) is LimousineScheduleViewResponse
    assert generated_sids == ["synthetic-client-sid"]
    assert len(requests) == 3
    assert [request.method for request in requests] == ["POST"] * 3
    assert [request.url.path for request in requests] == [
        SCHEDULE_PATH,
        SEAT_PATH,
        VIEW_PATH,
    ]
    assert all(request.url.query == b"" for request in requests)
    prepared = [
        parse_qs(request.content.decode(), keep_blank_values=True)
        for request in requests
    ]
    assert [set(form) for form in prepared] == [
        SCHEDULE_FIELDS,
        SEAT_FIELDS,
        VIEW_FIELDS,
    ]
    assert prepared[0]["tmGpCd"] == ["777"]
    assert prepared[1]["trnClsfCd"] == ["77"]
    assert prepared[1]["srcarNo"] == ["0007"]
    assert prepared[2]["txtMenuId"] == ["77"]
    assert prepared[2]["selGoTrain"] == ["777"]
    assert prepared[2]["Sid"] == ["synthetic-client-sid"]
    assert all(len(values) == 1 for form in prepared for values in form.values())
    assert token_contexts == []
    assert all("x-dynapath-m-token" not in request.headers for request in requests)


@pytest.mark.parametrize(
    "method_name",
    [
        "get_limousine_schedules",
        "get_limousine_seat_inventory",
        "get_limousine_schedule_view",
    ],
)
def test_invalid_query_types_fail_before_sid_dynapath_or_transport(
    method_name,
    monkeypatch,
):
    sid_calls = 0
    token_calls = 0
    transport_calls = 0

    def fake_sid() -> str:
        nonlocal sid_calls
        sid_calls += 1
        raise AssertionError("Sid must not be generated")

    def token_provider(_):
        nonlocal token_calls
        token_calls += 1
        raise AssertionError("DynaPath must not run")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({SCHEDULE_PATH, SEAT_PATH, VIEW_PATH}),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(TypeError, match="query"):
            getattr(client, method_name)(object())
    finally:
        client.close()
    assert sid_calls == 0
    assert token_calls == 0
    assert transport_calls == 0


@pytest.mark.parametrize(
    ("method_name", "fixture_name"),
    [
        ("get_limousine_schedules", "schedule_query"),
        ("get_limousine_seat_inventory", "seat_query"),
        ("get_limousine_schedule_view", "view_query"),
    ],
)
def test_session_expiry_clears_existing_session_without_retry(
    request,
    method_name,
    fixture_name,
):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic-session-message-secret",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session-secret",
        member_no="synthetic-member-secret",
    )
    try:
        with pytest.raises(KorailSessionExpiredError):
            getattr(client, method_name)(request.getfixturevalue(fixture_name))
        assert client.session.current is None
    finally:
        client.close()
    assert calls == 1


def test_application_failure_is_not_retried_or_misclassified(schedule_query):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC.FAIL",
                "h_msg_txt": "synthetic-app-message-secret",
                "strResult": "FAIL",
            },
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAppError):
            client.get_limousine_schedules(schedule_query)
    finally:
        client.close()
    assert calls == 1


def test_current_docs_describe_static_only_limousine_boundary():
    root = Path(__file__).parents[1]
    readme = (root / "README.md").read_text(encoding="utf-8")
    progress = (root / "docs" / "IMPLEMENTATION_PROGRESS.md").read_text(
        encoding="utf-8"
    )
    combined = f"{readme}\n{progress}"
    for method in (
        "get_limousine_schedules(",
        "get_limousine_seat_inventory(",
        "get_limousine_schedule_view(",
    ):
        assert method in combined
    assert "38 exact" in combined
    assert "41 public methods" in combined
    assert "caller-supplied service" in combined
    assert "DynaPath" in combined
    assert "No live" in combined
