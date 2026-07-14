from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import math
from collections.abc import Iterator, Mapping
from copy import deepcopy
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
    PhysicalSeat,
    SeatAttribute,
    SeatCar,
    SeatCarListResponse,
    SeatInventoryResponse,
    SeatWindow,
)
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
)
from korail_mobile_api.models import (
    BaseKorailResponse,
    KorailSession,
    TrainSearchResult,
    TrainSummary,
)
from korail_mobile_api.parsers import (
    parse_seat_car_list_response,
    parse_seat_inventory_response,
)
from korail_mobile_api.payloads import (
    build_seat_car_form,
    build_seat_inventory_form,
    validate_seat_inventory_inputs,
)
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


_EVIDENCE_PATH = (
    Path(__file__).parents[1]
    / "scripts"
    / "capture_seat_inventory_evidence.py"
)
_EVIDENCE_SPEC = importlib.util.spec_from_file_location(
    "capture_seat_inventory_evidence",
    _EVIDENCE_PATH,
)
assert _EVIDENCE_SPEC is not None and _EVIDENCE_SPEC.loader is not None
evidence = importlib.util.module_from_spec(_EVIDENCE_SPEC)
_EVIDENCE_SPEC.loader.exec_module(evidence)


CAR_PATH = "/classes/com.korail.mobile.research.TrainResearch"
SEAT_PATH = (
    "/classes/com.korail.mobile.research.TResidualSeatsResearch.do"
)
CAR_FIELDS = frozenset(
    {
        "Device",
        "Version",
        "Key",
        "Sid",
        "txtMenuId",
        "txtPsrmClCd",
        "txtRunDt",
        "txtDptDt",
        "txtTrnClsfCd",
        "txtTrnNo",
        "txtDptRsStnCd",
        "txtArvRsStnCd",
        "txtDptStnRunOrdr",
        "txtArvStnRunOrdr",
        "txtTrnGpCd",
        "txtTotPsgCnt",
        "txtSeatAttCd",
        "txtGdNo",
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
        "Sid",
        "ctlDvCd",
    }
)
SAFE_RESULT_KEYS = {
    "status",
    "calls",
    "train_count",
    "car_count",
    "seat_count",
    "window_count",
    "fields",
    "sufficiency",
}
SAFE_CALL_KEYS = {"login", "search", "car_list", "seat_list"}
SAFE_FIELD_KEYS = {
    "train_fields_present",
    "car_fields_typed",
    "seat_fields_typed",
    "physical_seat_fields_typed",
    "window_fields_typed",
    "banner_field_typed",
}


@pytest.fixture
def complete_train() -> TrainSummary:
    return TrainSummary(
        train_no="123",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0020",
        departure_date="20260714",
        run_date="20260714",
        train_class_code="00",
        departure_run_order="000001",
        arrival_run_order="000010",
    )


def _base(raw: dict[str, Any]) -> BaseKorailResponse:
    return BaseKorailResponse.from_raw(raw)


def _parse_car(raw: dict[str, Any]) -> SeatCarListResponse:
    return parse_seat_car_list_response(_base(raw))


def _parse_seat(raw: dict[str, Any]) -> SeatInventoryResponse:
    return parse_seat_inventory_response(_base(raw))


def test_new_public_models_are_frozen_dataclasses_and_exported():
    instances = (
        SeatAttribute(name="Synthetic attribute"),
        SeatCar(
            car_no=1,
            room_class_name="Synthetic room",
            remaining_seat_count=1,
            attributes=(),
        ),
        SeatCarListResponse(),
        PhysicalSeat(
            seat_no="synthetic-seat-secret",
            sale_possible="Y",
            direction_code="D",
            other_attribute_code="E",
            requested_attribute_code="R",
            floor="1",
            specification="S",
            sequence_no="1",
            message_code="M",
            message="synthetic-message-secret",
            visual_message_division_code="V",
        ),
        SeatWindow(start_location_ratio=0.1, close_location_ratio=0.2),
        SeatInventoryResponse(),
    )
    expected_names = {
        "SeatAttribute",
        "SeatCar",
        "SeatCarListResponse",
        "PhysicalSeat",
        "SeatWindow",
        "SeatInventoryResponse",
    }
    assert all(is_dataclass(instance) for instance in instances)
    for instance in instances:
        first_field = fields(instance)[0].name
        with pytest.raises(FrozenInstanceError):
            setattr(instance, first_field, getattr(instance, first_field))
    assert expected_names <= set(korail_mobile_api.__all__)
    assert {
        name: getattr(korail_mobile_api, name) for name in expected_names
    } == {
        "SeatAttribute": SeatAttribute,
        "SeatCar": SeatCar,
        "SeatCarListResponse": SeatCarListResponse,
        "PhysicalSeat": PhysicalSeat,
        "SeatWindow": SeatWindow,
        "SeatInventoryResponse": SeatInventoryResponse,
    }


def test_train_summary_appends_inventory_fields_and_parses_both_key_styles():
    raw = {
        "h_trn_no": "00123",
        "h_run_dt": "20260714",
        "h_trn_clsf_cd": "00",
        "h_dpt_stn_run_ordr": "000001",
        "h_arv_stn_run_ordr": "000010",
    }
    train = TrainSummary.from_raw(raw)
    alternate = TrainSummary.from_raw(
        {
            "trnNo": "00456",
            "runDt": "20260715",
            "trnClsfCd": "01",
            "dptStnRunOrdr": "000011",
            "arvStnRunOrdr": "000020",
        }
    )
    assert list(inspect.signature(TrainSummary).parameters)[-4:] == [
        "run_date",
        "train_class_code",
        "departure_run_order",
        "arrival_run_order",
    ]
    assert (
        train.run_date,
        train.train_class_code,
        train.departure_run_order,
        train.arrival_run_order,
    ) == ("20260714", "00", "000001", "000010")
    assert (
        alternate.run_date,
        alternate.train_class_code,
        alternate.departure_run_order,
        alternate.arrival_run_order,
    ) == ("20260715", "01", "000011", "000020")
    assert train.raw is raw


def test_car_parser_builds_tuples_and_hides_raw_message_and_train_identifiers(
    load_json_fixture,
):
    raw = load_json_fixture("seat_car_list_success.json")
    result = _parse_car(raw)
    assert result.h_msg_cd == "SYNTHETIC.OK"
    assert result.recommended_car_no == 2
    assert result.train_no == "99123"
    assert isinstance(result.cars, tuple)
    assert result.cars == (
        SeatCar(
            car_no=2,
            room_class_name="Synthetic General",
            remaining_seat_count=4,
            attributes=(
                SeatAttribute(name="Forward-facing"),
                SeatAttribute(name="Window-side"),
            ),
        ),
        SeatCar(
            car_no=3,
            room_class_name="Synthetic General",
            remaining_seat_count=0,
            attributes=(
                SeatAttribute(name="Synthetic unknown attribute"),
            ),
        ),
    )
    assert all(isinstance(car.attributes, tuple) for car in result.cars)
    rendered = repr(result)
    for secret in (
        "synthetic-car-message-secret",
        "99123",
        "synthetic-car-raw-secret",
    ):
        assert secret not in rendered


def test_seat_parser_maps_all_fields_preserves_unknown_codes_and_hides_secrets(
    load_json_fixture,
):
    raw = load_json_fixture("seat_inventory_success.json")
    result = _parse_seat(raw)
    assert result.layout_type == 7
    assert result.arrangement_code == "Z9-UNKNOWN"
    assert result.remaining_count == 1
    assert result.total_count == 8
    assert isinstance(result.seats, tuple)
    assert isinstance(result.windows, tuple)
    assert len(result.seats) == 2
    assert result.seats[0] == PhysicalSeat(
        seat_no="SYNTHETIC-SEAT-01",
        sale_possible="Y",
        direction_code="DIRECTION-UNKNOWN",
        other_attribute_code="OTHER-UNKNOWN",
        requested_attribute_code="REQUEST-UNKNOWN",
        floor="1",
        specification="SPEC-UNKNOWN",
        sequence_no="001",
        message_code="MESSAGE-UNKNOWN",
        message="synthetic-seat-message-secret",
        visual_message_division_code="VISUAL-UNKNOWN",
    )
    assert result.windows == (
        SeatWindow(start_location_ratio=0.125, close_location_ratio=0.375),
        SeatWindow(start_location_ratio=0.625, close_location_ratio=0.875),
    )
    assert result.vr_banner_url == (
        "https://example.invalid/inert-only?marker=synthetic-url-secret"
    )
    rendered = f"{result!r} {result.seats[0]!r}"
    for secret in (
        "synthetic-seat-envelope-message-secret",
        "synthetic-seat-message-secret",
        "SYNTHETIC-SEAT-01",
        "synthetic-url-secret",
        "synthetic-seat-raw-secret",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("srcar_infos"),
        lambda raw: raw.__setitem__("srcar_infos", []),
        lambda raw: raw["srcar_infos"].pop("srcar_info"),
        lambda raw: raw["srcar_infos"].__setitem__("srcar_info", {}),
        lambda raw: raw["srcar_infos"]["srcar_info"].__setitem__(0, []),
        lambda raw: raw["srcar_infos"]["srcar_info"][0].pop(
            "seatAttInfos"
        ),
        lambda raw: raw["srcar_infos"]["srcar_info"][0].__setitem__(
            "seatAttInfos", {}
        ),
        lambda raw: raw["srcar_infos"]["srcar_info"][0][
            "seatAttInfos"
        ].__setitem__(0, "not-an-object"),
    ],
)
def test_car_parser_rejects_malformed_containers(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("seat_car_list_success.json")
    mutation(raw)
    with pytest.raises(KorailProtocolError):
        _parse_car(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.__setitem__("h_rcmd_srcar_no", True),
        lambda raw: raw.__setitem__("h_rcmd_srcar_no", "2"),
        lambda raw: raw.__setitem__("h_trn_no", 99123),
        lambda raw: raw["srcar_infos"]["srcar_info"][0].__setitem__(
            "h_srcar_no", False
        ),
        lambda raw: raw["srcar_infos"]["srcar_info"][0].__setitem__(
            "h_psrm_cl_nm", 1
        ),
        lambda raw: raw["srcar_infos"]["srcar_info"][0].__setitem__(
            "h_rest_seat_cnt", "4"
        ),
        lambda raw: raw["srcar_infos"]["srcar_info"][0][
            "seatAttInfos"
        ][0].__setitem__("seatAttNm", 1),
    ],
)
def test_car_parser_rejects_wrong_scalar_types(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("seat_car_list_success.json")
    mutation(raw)
    with pytest.raises(KorailProtocolError):
        _parse_car(raw)


def test_car_parser_rejects_negative_counts_and_duplicate_car_numbers(
    load_json_fixture,
):
    negative = load_json_fixture("seat_car_list_success.json")
    negative["srcar_infos"]["srcar_info"][0]["h_rest_seat_cnt"] = -1
    duplicate = load_json_fixture("seat_car_list_success.json")
    duplicate["srcar_infos"]["srcar_info"][1]["h_srcar_no"] = 2
    with pytest.raises(KorailProtocolError, match="negative"):
        _parse_car(negative)
    with pytest.raises(KorailProtocolError, match="duplicate"):
        _parse_car(duplicate)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("seatList"),
        lambda raw: raw.__setitem__("seatList", {}),
        lambda raw: raw["seatList"].__setitem__(0, []),
        lambda raw: raw.pop("windowList"),
        lambda raw: raw.__setitem__("windowList", {}),
        lambda raw: raw["windowList"].__setitem__(0, []),
    ],
)
def test_seat_parser_rejects_malformed_containers(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("seat_inventory_success.json")
    mutation(raw)
    with pytest.raises(KorailProtocolError):
        _parse_seat(raw)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.__setitem__("layout_type", True),
        lambda raw: raw.__setitem__("seat_ary_cd", 7),
        lambda raw: raw.__setitem__("seat_remain_count", "1"),
        lambda raw: raw.__setitem__("seat_total_count", False),
        lambda raw: raw.__setitem__("vrBnrUrl", 1),
        lambda raw: raw["seatList"][0].__setitem__("sale_psb_flg", 1),
        lambda raw: raw["windowList"][0].__setitem__("st_loc_rt", "0.1"),
    ],
)
def test_seat_parser_rejects_wrong_scalar_types(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("seat_inventory_success.json")
    mutation(raw)
    with pytest.raises(KorailProtocolError):
        _parse_seat(raw)


@pytest.mark.parametrize(
    "field_name",
    [
        "dir_seat_att_cd",
        "etc_seat_att_cd",
        "floor",
        "intg_msg",
        "intg_msg_cd",
        "rq_seat_att_cd",
        "sale_psb_flg",
        "seat_no",
        "seat_spec",
        "sqr_no",
        "vz_msg_dv_cd",
    ],
)
def test_seat_parser_requires_every_documented_seat_string(
    load_json_fixture,
    field_name,
):
    wrong_type = load_json_fixture("seat_inventory_success.json")
    wrong_type["seatList"][0][field_name] = None
    missing = load_json_fixture("seat_inventory_success.json")
    missing["seatList"][0].pop(field_name)
    with pytest.raises(KorailProtocolError):
        _parse_seat(wrong_type)
    with pytest.raises(KorailProtocolError):
        _parse_seat(missing)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("seat_remain_count", -1),
        ("seat_total_count", -1),
    ],
)
def test_seat_parser_rejects_negative_counts(
    load_json_fixture,
    field_name,
    value,
):
    raw = load_json_fixture("seat_inventory_success.json")
    raw[field_name] = value
    with pytest.raises(KorailProtocolError, match="negative"):
        _parse_seat(raw)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_seat_parser_rejects_non_finite_window_ratios(
    load_json_fixture,
    value,
):
    raw = load_json_fixture("seat_inventory_success.json")
    raw["windowList"][0]["cls_loc_rt"] = value
    with pytest.raises(KorailProtocolError, match="finite"):
        _parse_seat(raw)


def test_seat_parser_rejects_duplicate_nonempty_seats_and_impossible_counts(
    load_json_fixture,
):
    duplicate = load_json_fixture("seat_inventory_success.json")
    duplicate["seatList"][1]["seat_no"] = "SYNTHETIC-SEAT-01"
    impossible = load_json_fixture("seat_inventory_success.json")
    impossible["seat_remain_count"] = 9
    with pytest.raises(KorailProtocolError, match="duplicate"):
        _parse_seat(duplicate)
    with pytest.raises(KorailProtocolError, match="remaining"):
        _parse_seat(impossible)


def test_seat_parser_allows_empty_lists_and_count_independent_list_length(
    load_json_fixture,
):
    empty = load_json_fixture("seat_inventory_success.json")
    empty["seatList"] = []
    empty["windowList"] = []
    empty["seat_remain_count"] = 0
    empty["seat_total_count"] = 0
    partial = load_json_fixture("seat_inventory_success.json")
    partial["seat_total_count"] = 99
    assert _parse_seat(empty).seats == ()
    assert _parse_seat(empty).windows == ()
    assert len(_parse_seat(partial).seats) == 2


def test_closed_payload_builders_emit_exact_forms_and_fixed_values(
    complete_train,
):
    config = KorailConfig()
    car = build_seat_car_form(
        config,
        complete_train,
        passenger_count=2,
        sid="caller-sid-car",
    )
    seat = build_seat_inventory_form(
        config,
        complete_train,
        car_no=4,
        passenger_count=3,
        sid="caller-sid-seat",
    )
    assert set(car) == CAR_FIELDS
    assert len(car) == 18
    assert "sidTest" not in car
    assert car == {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "Sid": "caller-sid-car",
        "txtMenuId": "11",
        "txtPsrmClCd": "1",
        "txtRunDt": "20260714",
        "txtDptDt": "20260714",
        "txtTrnClsfCd": "00",
        "txtTrnNo": "00123",
        "txtDptRsStnCd": "0001",
        "txtArvRsStnCd": "0020",
        "txtDptStnRunOrdr": "000001",
        "txtArvStnRunOrdr": "000010",
        "txtTrnGpCd": "100",
        "txtTotPsgCnt": "2",
        "txtSeatAttCd": "015",
        "txtGdNo": "",
    }
    assert set(seat) == SEAT_FIELDS
    assert len(seat) == 19
    assert "sidTest" not in seat
    assert seat == {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "trnClsfCd": "00",
        "trnGpCd": "100",
        "runDt": "20260714",
        "trnNo": "00123",
        "srcarNo": "4",
        "psrmClCd": "1",
        "dptRsStnCd": "0001",
        "arvRsStnCd": "0020",
        "seatAttCd": "015",
        "dptStnRunOrdr": "000001",
        "arvStnRunOrdr": "000010",
        "totPsgCnt": "3",
        "gdNo": "",
        "isArrow": "true",
        "Sid": "caller-sid-seat",
        "ctlDvCd": "",
    }


@pytest.mark.parametrize("passenger_count", [True, False, 0, 10, -1, 1.0])
def test_builders_reject_invalid_passenger_counts(
    complete_train,
    passenger_count,
):
    with pytest.raises(ValueError, match="passenger_count"):
        build_seat_car_form(
            KorailConfig(),
            complete_train,
            passenger_count=passenger_count,
            sid="synthetic-sid",
        )


@pytest.mark.parametrize("car_no", [True, False, 0, -1, 1.0, "1"])
def test_seat_builder_rejects_invalid_car_numbers(complete_train, car_no):
    with pytest.raises(ValueError, match="car_no"):
        build_seat_inventory_form(
            KorailConfig(),
            complete_train,
            car_no=car_no,
            passenger_count=1,
            sid="synthetic-sid",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("train_no", None),
        ("train_no", ""),
        ("train_no", "１２３"),
        ("train_no", "123456"),
        ("train_group_code", None),
        ("train_group_code", "10A"),
        ("train_group_code", "１０0"),
        ("departure_station_code", None),
        ("departure_station_code", "001A"),
        ("arrival_station_code", "００２０"),
        ("departure_date", None),
        ("departure_date", "2026-07-14"),
        ("run_date", "２０２６０７１４"),
        ("train_class_code", None),
        ("train_class_code", "0A"),
        ("departure_run_order", None),
        ("departure_run_order", "00001A"),
        ("arrival_run_order", "００００１０"),
    ],
)
def test_inventory_validation_rejects_missing_non_ascii_and_malformed_train_fields(
    complete_train,
    field_name,
    value,
):
    malformed = replace(complete_train, **{field_name: value})
    with pytest.raises(KorailProtocolError, match=field_name):
        validate_seat_inventory_inputs(malformed, 1)


def test_safety_registers_only_the_two_exact_new_post_contracts():
    assert len(KORAIL_READ_ONLY_ROUTES) == 27
    assert ("POST", CAR_PATH) in KORAIL_READ_ONLY_ROUTES
    assert ("POST", SEAT_PATH) in KORAIL_READ_ONLY_ROUTES
    assert KORAIL_EXACT_REQUEST_FIELDS[CAR_PATH] == CAR_FIELDS
    assert KORAIL_EXACT_REQUEST_FIELDS[SEAT_PATH] == SEAT_FIELDS
    assert_read_only_route("POST", CAR_PATH)
    assert_read_only_route("POST", SEAT_PATH)
    assert_read_only_request_fields(
        CAR_PATH,
        {name: "" for name in CAR_FIELDS},
    )
    assert_read_only_request_fields(
        SEAT_PATH,
        {name: "" for name in SEAT_FIELDS},
    )


@pytest.mark.parametrize(("path", "fields"), [(CAR_PATH, CAR_FIELDS), (SEAT_PATH, SEAT_FIELDS)])
def test_inventory_safety_rejects_missing_and_extra_fields(path, fields):
    missing = {name: "" for name in fields - {next(iter(fields))}}
    extra = {name: "" for name in fields}
    extra["sidTest"] = "must-not-pass"
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


@pytest.mark.parametrize(("path", "fields"), [(CAR_PATH, CAR_FIELDS), (SEAT_PATH, SEAT_FIELDS)])
def test_inventory_safety_rejects_duplicate_prepared_fields(path, fields):
    values = {name: "" for name in fields}
    duplicate = _DuplicateFieldMapping(values, next(iter(fields)))
    with pytest.raises(KorailProtocolError, match="duplicate"):
        assert_read_only_request_fields(path, duplicate)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", CAR_PATH),
        ("GET", SEAT_PATH),
        ("POST", "/classes/com.korail.mobile.research.TrainResearch.do"),
        (
            "POST",
            "/classes/com.korail.mobile.research.TResidualSeatsResearch",
        ),
        (
            "POST",
            "/classes/com.korail.mobile.research.selectSeat.do",
        ),
        (
            "POST",
            "/classes/com.korail.mobile.certification.TicketReservation",
        ),
    ],
)
def test_inventory_safety_rejects_wrong_methods_and_adjacent_routes(
    method,
    path,
):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route(method, path)


@pytest.mark.parametrize("path", [CAR_PATH, SEAT_PATH])
def test_invalid_inventory_forms_fail_before_dynapath_or_transport(path):
    transport_calls = 0
    token_calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    def token_provider(_):
        nonlocal token_calls
        token_calls += 1
        raise AssertionError("DynaPath must not run")

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({path}),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailProtocolError, match="fields"):
            client.http.post_form(
                path,
                {"Device": "AD"},
                include_common=False,
            )
    finally:
        client.close()
    assert token_calls == 0
    assert transport_calls == 0


@pytest.mark.parametrize("path", [CAR_PATH, SEAT_PATH])
def test_duplicate_inventory_forms_fail_before_dynapath_or_transport(path):
    transport_calls = 0
    token_calls = 0
    fields = KORAIL_EXACT_REQUEST_FIELDS[path]
    duplicate = _DuplicateFieldMapping(
        {name: "" for name in fields},
        next(iter(fields)),
    )

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    def token_provider(_):
        nonlocal token_calls
        token_calls += 1
        raise AssertionError("DynaPath must not run")

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({path}),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailProtocolError, match="duplicate"):
            client.http.post_form(
                path,
                duplicate,
                include_common=False,
            )
    finally:
        client.close()
    assert token_calls == 0
    assert transport_calls == 0


@pytest.mark.parametrize(
    "base_url",
    [
        "http://smart.letskorail.com",
        "https://evil.invalid",
        "https://smart.letskorail.com@evil.invalid",
        "https://smart.letskorail.com/other",
    ],
)
def test_wrong_inventory_origins_fail_before_token_or_transport(base_url):
    token_calls = 0
    transport_calls = 0

    def token_provider(_):
        nonlocal token_calls
        token_calls += 1
        return "must-not-run"

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    config = KorailConfig(
        base_url=base_url,
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({CAR_PATH, SEAT_PATH}),
        ),
    )
    with pytest.raises(KorailProtocolError, match="origin"):
        KorailClient(config, transport=httpx.MockTransport(handler))
    assert token_calls == 0
    assert transport_calls == 0


def test_inventory_methods_have_exact_public_signatures_and_hints():
    cars_signature = inspect.signature(KorailClient.get_seat_cars)
    seats_signature = inspect.signature(KorailClient.get_seat_inventory)
    assert list(cars_signature.parameters) == [
        "self",
        "train",
        "passenger_count",
    ]
    assert list(seats_signature.parameters) == [
        "self",
        "train",
        "car_no",
        "passenger_count",
    ]
    assert cars_signature.parameters["passenger_count"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert seats_signature.parameters["passenger_count"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert cars_signature.parameters["passenger_count"].default == 1
    assert seats_signature.parameters["passenger_count"].default == 1
    car_hints = get_type_hints(KorailClient.get_seat_cars)
    seat_hints = get_type_hints(KorailClient.get_seat_inventory)
    assert car_hints == {
        "train": TrainSummary,
        "passenger_count": int,
        "return": SeatCarListResponse,
    }
    assert seat_hints == {
        "train": TrainSummary,
        "car_no": int,
        "passenger_count": int,
        "return": SeatInventoryResponse,
    }


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("get_seat_cars", (TrainSummary("123"),)),
        ("get_seat_inventory", (TrainSummary("123"), 1)),
    ],
)
def test_inventory_methods_require_session_before_validation_and_io(
    method_name,
    args,
):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not run")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAuthError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 0


def test_inventory_methods_generate_fresh_sid_post_once_and_disable_dynapath(
    complete_train,
    load_json_fixture,
    monkeypatch,
):
    requests: list[httpx.Request] = []
    token_contexts = []
    generated: list[str] = []
    sid_values = iter(("fresh-car-sid", "fresh-seat-sid"))
    car_raw = load_json_fixture("seat_car_list_success.json")
    seat_raw = load_json_fixture("seat_inventory_success.json")

    def fake_sid() -> str:
        value = next(sid_values)
        generated.append(value)
        return value

    def token_provider(context):
        token_contexts.append(context)
        return "must-not-be-used"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = car_raw if request.url.path == CAR_PATH else seat_raw
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({CAR_PATH, SEAT_PATH}),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(
        jsessionid="synthetic-session",
        member_no="synthetic-member",
    )
    try:
        cars = client.get_seat_cars(complete_train, passenger_count=2)
        seats = client.get_seat_inventory(
            complete_train,
            2,
            passenger_count=2,
        )
    finally:
        client.close()

    assert type(cars) is SeatCarListResponse
    assert type(seats) is SeatInventoryResponse
    assert generated == ["fresh-car-sid", "fresh-seat-sid"]
    assert len(requests) == 2
    assert [request.method for request in requests] == ["POST", "POST"]
    assert [request.url.path for request in requests] == [CAR_PATH, SEAT_PATH]
    assert all(request.url.query == b"" for request in requests)
    car_form = parse_qs(
        requests[0].content.decode(),
        keep_blank_values=True,
    )
    seat_form = parse_qs(
        requests[1].content.decode(),
        keep_blank_values=True,
    )
    assert set(car_form) == CAR_FIELDS
    assert set(seat_form) == SEAT_FIELDS
    assert car_form["Sid"] == ["fresh-car-sid"]
    assert seat_form["Sid"] == ["fresh-seat-sid"]
    assert all(len(values) == 1 for values in car_form.values())
    assert all(len(values) == 1 for values in seat_form.values())
    assert token_contexts == []
    assert all("x-dynapath-m-token" not in request.headers for request in requests)


@pytest.mark.parametrize(
    ("method_name", "args", "kwargs"),
    [
        ("get_seat_cars", (), {"passenger_count": True}),
        ("get_seat_cars", (), {"passenger_count": 0}),
        ("get_seat_cars", (), {"passenger_count": 10}),
        ("get_seat_inventory", (True,), {}),
        ("get_seat_inventory", (0,), {}),
        ("get_seat_inventory", (-1,), {}),
    ],
)
def test_invalid_caller_counts_fail_before_sid_and_transport(
    complete_train,
    method_name,
    args,
    kwargs,
    monkeypatch,
):
    sid_calls = 0
    transport_calls = 0

    def fake_sid() -> str:
        nonlocal sid_calls
        sid_calls += 1
        raise AssertionError("Sid generation must not run")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-session")
    try:
        with pytest.raises(ValueError):
            getattr(client, method_name)(complete_train, *args, **kwargs)
    finally:
        client.close()
    assert sid_calls == 0
    assert transport_calls == 0


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("train_no", "１２３"),
        ("train_group_code", "10A"),
        ("departure_station_code", None),
        ("arrival_station_code", "002A"),
        ("departure_date", "2026071A"),
        ("run_date", None),
        ("train_class_code", "0A"),
        ("departure_run_order", "０００００１"),
        ("arrival_run_order", None),
    ],
)
def test_invalid_train_fields_fail_before_sid_and_transport(
    complete_train,
    field_name,
    value,
    monkeypatch,
):
    sid_calls = 0
    transport_calls = 0

    def fake_sid() -> str:
        nonlocal sid_calls
        sid_calls += 1
        raise AssertionError("Sid generation must not run")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal transport_calls
        transport_calls += 1
        raise AssertionError("transport must not run")

    monkeypatch.setattr(client_module, "generate_sid", fake_sid)
    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-session")
    malformed = replace(complete_train, **{field_name: value})
    try:
        with pytest.raises(KorailProtocolError, match=field_name):
            client.get_seat_cars(malformed)
    finally:
        client.close()
    assert sid_calls == 0
    assert transport_calls == 0


def test_client_inventory_methods_pass_both_disabled_inclusion_flags(
    complete_train,
    load_json_fixture,
    monkeypatch,
):
    calls: list[tuple[str, dict[str, str], dict[str, Any]]] = []
    responses = {
        CAR_PATH: _base(load_json_fixture("seat_car_list_success.json")),
        SEAT_PATH: _base(load_json_fixture("seat_inventory_success.json")),
    }

    def fake_post_form(path, data, **kwargs):
        calls.append((path, data, kwargs))
        return responses[path]

    monkeypatch.setattr(client_module, "generate_sid", lambda: "fresh-sid")
    client = KorailClient(
        transport=httpx.MockTransport(
            lambda _: pytest.fail("real transport must not run")
        )
    )
    client.session.current = KorailSession(jsessionid="synthetic-session")
    monkeypatch.setattr(client.http, "post_form", fake_post_form)
    try:
        client.get_seat_cars(complete_train)
        client.get_seat_inventory(complete_train, 2)
    finally:
        client.close()
    assert [call[0] for call in calls] == [CAR_PATH, SEAT_PATH]
    assert all(
        kwargs == {"include_common": False, "include_dynapath": False}
        for _, _, kwargs in calls
    )


class _EvidenceFakeClient:
    scenario = "completed"
    calls: list[str] = []
    train: TrainSummary

    def __init__(self, _config: KorailConfig) -> None:
        self.calls.append("init")
        if self.scenario == "init_failed":
            raise RuntimeError("synthetic-init-message-secret")

    def login(self, _member_no: str, _password: str) -> KorailSession:
        self.calls.append("login")
        if self.scenario == "login_failed":
            raise RuntimeError("synthetic-login-message-secret")
        return KorailSession(jsessionid="synthetic-session-secret")

    def search_trains(self, _query) -> TrainSearchResult:
        self.calls.append("search")
        if self.scenario == "search_failed":
            raise RuntimeError("synthetic-search-message-secret")
        trains = [] if self.scenario == "no_trains" else [self.train]
        return TrainSearchResult(
            trains=trains,
            response=BaseKorailResponse(),
            raw={"message": "synthetic-search-raw-secret"},
        )

    def get_seat_cars(
        self,
        _train: TrainSummary,
        *,
        passenger_count: int = 1,
    ) -> SeatCarListResponse:
        assert passenger_count == 1
        self.calls.append("car_list")
        if self.scenario == "car_list_failed":
            raise RuntimeError("synthetic-car-list-message-secret")
        cars = (
            ()
            if self.scenario == "no_cars"
            else (
                SeatCar(
                    car_no=7,
                    room_class_name="Synthetic General",
                    remaining_seat_count=1,
                    attributes=(SeatAttribute(name="Synthetic attribute"),),
                ),
            )
        )
        return SeatCarListResponse(
            recommended_car_no=7,
            train_no="synthetic-train-identifier-secret",
            cars=cars,
            raw={"message": "synthetic-car-raw-secret"},
        )

    def get_seat_inventory(
        self,
        _train: TrainSummary,
        car_no: int,
        *,
        passenger_count: int = 1,
    ) -> SeatInventoryResponse:
        assert car_no == 7
        assert passenger_count == 1
        self.calls.append("seat_list")
        if self.scenario == "seat_list_failed":
            raise RuntimeError("synthetic-seat-list-message-secret")
        return SeatInventoryResponse(
            layout_type=3,
            arrangement_code="UNKNOWN-CODE",
            remaining_count=1,
            total_count=9,
            seats=(
                PhysicalSeat(
                    seat_no="synthetic-seat-identifier-secret",
                    sale_possible="Y",
                    direction_code="UNKNOWN-DIRECTION",
                    other_attribute_code="UNKNOWN-OTHER",
                    requested_attribute_code="UNKNOWN-REQUEST",
                    floor="1",
                    specification="UNKNOWN-SPEC",
                    sequence_no="1",
                    message_code="UNKNOWN-MESSAGE",
                    message="synthetic-seat-message-secret",
                    visual_message_division_code="UNKNOWN-VISUAL",
                ),
            ),
            windows=(
                SeatWindow(
                    start_location_ratio=0.1,
                    close_location_ratio=0.2,
                ),
            ),
            vr_banner_url=(
                "https://example.invalid/?secret=synthetic-banner-secret"
            ),
            raw={"message": "synthetic-seat-raw-secret"},
        )

    def close(self) -> None:
        self.calls.append("close")
        if self.scenario == "close_failed":
            raise RuntimeError("synthetic-close-message-secret")


@pytest.fixture
def configured_evidence(monkeypatch, complete_train):
    _EvidenceFakeClient.calls = []
    _EvidenceFakeClient.scenario = "completed"
    _EvidenceFakeClient.train = complete_train
    monkeypatch.setattr(evidence, "KorailClient", _EvidenceFakeClient)
    monkeypatch.setattr(evidence, "live_enabled", lambda: True)
    monkeypatch.setattr(
        evidence,
        "read_credentials_from_env",
        lambda: ("synthetic-member-secret", "synthetic-password-secret"),
    )
    monkeypatch.setattr(evidence, "build_config_from_env", KorailConfig)
    monkeypatch.setenv("KORAIL_TEST_DATE", "20260714")
    monkeypatch.setenv("KORAIL_DEPARTURE_STATION", "Synthetic Departure")
    monkeypatch.setenv("KORAIL_ARRIVAL_STATION", "Synthetic Arrival")
    monkeypatch.setenv("KORAIL_DEPARTURE_TIME", "060000")
    return _EvidenceFakeClient


@pytest.mark.parametrize(
    (
        "scenario",
        "expected_status",
        "expected_sufficiency",
        "expected_calls",
        "client_calls",
    ),
    [
        (
            "login_failed",
            "login_failed",
            "insufficient_login",
            {"login": 1, "search": 0, "car_list": 0, "seat_list": 0},
            ["init", "login", "close"],
        ),
        (
            "search_failed",
            "search_failed",
            "insufficient_search",
            {"login": 1, "search": 1, "car_list": 0, "seat_list": 0},
            ["init", "login", "search", "close"],
        ),
        (
            "no_trains",
            "no_trains",
            "insufficient_no_trains",
            {"login": 1, "search": 1, "car_list": 0, "seat_list": 0},
            ["init", "login", "search", "close"],
        ),
        (
            "car_list_failed",
            "car_list_failed",
            "insufficient_car_list",
            {"login": 1, "search": 1, "car_list": 1, "seat_list": 0},
            ["init", "login", "search", "car_list", "close"],
        ),
        (
            "no_cars",
            "no_cars",
            "insufficient_no_cars",
            {"login": 1, "search": 1, "car_list": 1, "seat_list": 0},
            ["init", "login", "search", "car_list", "close"],
        ),
        (
            "seat_list_failed",
            "seat_list_failed",
            "insufficient_seat_list",
            {"login": 1, "search": 1, "car_list": 1, "seat_list": 1},
            [
                "init",
                "login",
                "search",
                "car_list",
                "seat_list",
                "close",
            ],
        ),
        (
            "completed",
            "completed",
            "sufficient",
            {"login": 1, "search": 1, "car_list": 1, "seat_list": 1},
            [
                "init",
                "login",
                "search",
                "car_list",
                "seat_list",
                "close",
            ],
        ),
    ],
)
def test_evidence_capture_stops_once_at_each_boundary_without_retry(
    configured_evidence,
    scenario,
    expected_status,
    expected_sufficiency,
    expected_calls,
    client_calls,
):
    configured_evidence.scenario = scenario
    result = evidence.capture_evidence()
    assert result["status"] == expected_status
    assert result["sufficiency"] == expected_sufficiency
    assert result["calls"] == expected_calls
    assert configured_evidence.calls == client_calls
    assert set(result) == SAFE_RESULT_KEYS
    assert set(result["calls"]) == SAFE_CALL_KEYS
    assert set(result["fields"]) == SAFE_FIELD_KEYS
    assert all(type(value) is bool for value in result["fields"].values())
    assert all(
        type(result[name]) is int and 0 <= result[name] <= 10_000
        for name in (
            "train_count",
            "car_count",
            "seat_count",
            "window_count",
        )
    )
    rendered = json.dumps(result, sort_keys=True)
    for secret in (
        "synthetic-member-secret",
        "synthetic-password-secret",
        "synthetic-session-secret",
        "synthetic-train-identifier-secret",
        "synthetic-seat-identifier-secret",
        "synthetic-banner-secret",
        "synthetic-message-secret",
        "Synthetic Departure",
        "Synthetic Arrival",
        "20260714",
        "060000",
        "example.invalid",
        "https://",
        "raw",
    ):
        assert secret not in rendered


def test_completed_evidence_contains_only_bounded_counts_and_type_presence(
    configured_evidence,
):
    result = evidence.capture_evidence()
    assert result == {
        "status": "completed",
        "calls": {
            "login": 1,
            "search": 1,
            "car_list": 1,
            "seat_list": 1,
        },
        "train_count": 1,
        "car_count": 1,
        "seat_count": 1,
        "window_count": 1,
        "fields": {
            "train_fields_present": True,
            "car_fields_typed": True,
            "seat_fields_typed": True,
            "physical_seat_fields_typed": True,
            "window_fields_typed": True,
            "banner_field_typed": True,
        },
        "sufficiency": "sufficient",
    }


def test_evidence_setup_failures_are_fixed_and_do_not_create_a_client(
    configured_evidence,
    monkeypatch,
):
    monkeypatch.setattr(evidence, "live_enabled", lambda: False)
    result = evidence.capture_evidence()
    assert result["status"] == "setup_failed"
    assert result["sufficiency"] == "insufficient_setup"
    assert result["calls"] == {
        "login": 0,
        "search": 0,
        "car_list": 0,
        "seat_list": 0,
    }
    assert configured_evidence.calls == []


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("KORAIL_DEPARTURE_STATION", "0001"),
        ("KORAIL_ARRIVAL_STATION", "0020"),
    ],
)
def test_evidence_rejects_numeric_station_references_before_client_creation(
    configured_evidence,
    monkeypatch,
    name,
    value,
):
    monkeypatch.setenv(name, value)
    result = evidence.capture_evidence()
    assert result["status"] == "setup_failed"
    assert result["calls"] == {
        "login": 0,
        "search": 0,
        "car_list": 0,
        "seat_list": 0,
    }
    assert configured_evidence.calls == []


@pytest.mark.parametrize("scenario", ["init_failed", "close_failed"])
def test_evidence_suppresses_client_lifecycle_exception_text(
    configured_evidence,
    scenario,
):
    configured_evidence.scenario = scenario
    result = evidence.capture_evidence()
    rendered = json.dumps(result, sort_keys=True)
    assert "synthetic-init-message-secret" not in rendered
    assert "synthetic-close-message-secret" not in rendered
    if scenario == "init_failed":
        assert result["status"] == "setup_failed"
        assert configured_evidence.calls == ["init"]
    else:
        assert result["status"] == "completed"
        assert configured_evidence.calls[-1] == "close"


def test_evidence_count_values_are_capped_at_ten_thousand(
    configured_evidence,
    complete_train,
    monkeypatch,
):
    physical = PhysicalSeat(
        seat_no="synthetic-seat",
        sale_possible="Y",
        direction_code="D",
        other_attribute_code="E",
        requested_attribute_code="R",
        floor="1",
        specification="S",
        sequence_no="1",
        message_code="M",
        message="synthetic-message",
        visual_message_division_code="V",
    )
    window = SeatWindow(0.1, 0.2)
    car = SeatCar(1, "Synthetic", 1, ())

    class ManyClient(_EvidenceFakeClient):
        def search_trains(self, _query):
            self.calls.append("search")
            return TrainSearchResult(
                trains=[complete_train] * 10_001,
                response=BaseKorailResponse(),
            )

        def get_seat_cars(self, _train, *, passenger_count=1):
            self.calls.append("car_list")
            return SeatCarListResponse(cars=(car,) * 10_001)

        def get_seat_inventory(
            self,
            _train,
            car_no,
            *,
            passenger_count=1,
        ):
            self.calls.append("seat_list")
            return SeatInventoryResponse(
                seats=(physical,) * 10_001,
                windows=(window,) * 10_001,
            )

    ManyClient.calls = []
    monkeypatch.setattr(evidence, "KorailClient", ManyClient)
    result = evidence.capture_evidence()
    assert result["train_count"] == 10_000
    assert result["car_count"] == 10_000
    assert result["seat_count"] == 10_000
    assert result["window_count"] == 10_000


def _safe_completed_result() -> dict[str, Any]:
    return {
        "status": "completed",
        "calls": {
            "login": 1,
            "search": 1,
            "car_list": 1,
            "seat_list": 1,
        },
        "train_count": 1,
        "car_count": 1,
        "seat_count": 1,
        "window_count": 1,
        "fields": {name: True for name in SAFE_FIELD_KEYS},
        "sufficiency": "sufficient",
    }


def test_evidence_writer_is_atomic_safe_and_protects_existing_output(
    tmp_path,
):
    output = tmp_path / "evidence.json"
    result = _safe_completed_result()
    evidence.write_evidence(output, result, force=False)
    assert json.loads(output.read_text(encoding="utf-8")) == result
    assert [path.name for path in tmp_path.iterdir()] == ["evidence.json"]
    output.write_text("preserve-existing", encoding="utf-8")
    with pytest.raises(FileExistsError):
        evidence.write_evidence(output, result, force=False)
    assert output.read_text(encoding="utf-8") == "preserve-existing"
    evidence.write_evidence(output, result, force=True)
    assert json.loads(output.read_text(encoding="utf-8")) == result


@pytest.mark.parametrize(
    "unsafe_change",
    [
        lambda result: result.__setitem__("raw", {"secret": "leak"}),
        lambda result: result.__setitem__(
            "status", "https://example.invalid/secret"
        ),
        lambda result: result["calls"].__setitem__("login", 2),
        lambda result: result.__setitem__("seat_count", 10_001),
    ],
)
def test_evidence_writer_rejects_unsafe_or_out_of_budget_results(
    tmp_path,
    unsafe_change,
):
    result = _safe_completed_result()
    unsafe_change(result)
    output = tmp_path / "unsafe.json"
    with pytest.raises(ValueError):
        evidence.write_evidence(output, result, force=False)
    assert not output.exists()


def test_evidence_script_has_narrow_import_and_operation_boundaries():
    source = Path(evidence.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".")[0])
            imported_names.update(alias.name for alias in node.names)
    assert imported_roots <= {
        "__future__",
        "argparse",
        "json",
        "math",
        "os",
        "pathlib",
        "tempfile",
        "typing",
        "korail_mobile_api",
    }
    assert "run_live_smoke" not in source
    assert "run_live_smoke_from_env" not in imported_names
    assert "requests" not in imported_roots
    assert "httpx" not in imported_roots
    called_attributes = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert {
        "login",
        "search_trains",
        "get_seat_cars",
        "get_seat_inventory",
        "close",
    } <= called_attributes
    forbidden_operations = {
        name
        for name in called_attributes
        if any(
            fragment in name.casefold()
            for fragment in (
                "reserve",
                "payment",
                "cancel",
                "refund",
                "select",
                "hold",
                "urlopen",
            )
        )
    }
    assert forbidden_operations == set()


def test_evidence_main_writes_only_the_sanitized_capture(
    tmp_path,
    monkeypatch,
):
    output = tmp_path / "result.json"
    result = _safe_completed_result()
    monkeypatch.setattr(evidence, "capture_evidence", lambda: result)
    assert evidence.main(["--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == result
