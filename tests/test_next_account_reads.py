from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from typing import Any, get_type_hints
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    CustomerTripInfoResponse,
    MaasServiceDetailListResponse,
    MultiChildDiscountTargetResponse,
    TourTrainInfoResponse,
    TripChangeDateResponse,
)
from korail_mobile_api.read_parsers import (
    parse_customer_trip_info_response,
    parse_maas_service_detail_list_response,
    parse_multi_child_discount_target_response,
    parse_tour_train_info_response,
    parse_trip_change_date_response,
)
from korail_mobile_api.read_payloads import (
    MaasServiceDetailQuery,
    build_customer_trip_info_form,
    build_maas_service_detail_form,
    build_multi_child_discount_target_form,
    build_trip_change_date_form,
)
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


R13_PATH = "/classes/com.korail.mobile.cust.mchdDcntTgt.do"
R32_PATH = "/classes/com.korail.mobile.research.custTripInfo.do"
R43_PATH = "/classes/com.korail.mobile.copt.gdReqQry.do"
R45_PATH = "/classes/com.korail.mobile.reservation.tripChgDate.do"
R54_PATH = "/classes/com.korail.mobile.trainsInfo.TourTrainSpecialRoom"

NEW_ROUTES = {
    ("POST", R13_PATH),
    ("POST", R32_PATH),
    ("POST", R43_PATH),
    ("POST", R45_PATH),
}

R13_FIELDS = (
    "btdt",
    "custFmlyNm",
    "dcntKndCd",
    "fmlySqno",
    "psgTpCd",
    "psgTpNm",
    "psrmClCd",
    "rqDcntKndCd",
)
R13_ATTRS = (
    "birth_date",
    "customer_family_name",
    "discount_kind_code",
    "family_sequence",
    "passenger_type_code",
    "passenger_type_name",
    "room_class_code",
    "requested_discount_kind_code",
)
R32_FIELDS = (
    "addSeatAttCd",
    "adltHdcpPrnb",
    "adulCnt",
    "arvStnCd",
    "arvStnNm",
    "babyAcpnPrnb",
    "chgDttm",
    "chgUsrId",
    "chilCnt",
    "chldHdcpPrnb",
    "custMgNo",
    "dayCd",
    "dirSeatAttGpCd",
    "dirtChtnDvCd",
    "dptStnCd",
    "dptStnNm",
    "ectbTrnDptTm",
    "edrPrnb",
    "inclFlg",
    "jobStHr",
    "locSeatAttGpCd",
    "medDvCd",
    "psrmClCd",
    "ptwtTtl",
    "regDttm",
    "regSqno",
    "regUsrId",
    "tripDno",
    "trnClsfCd",
    "trnCnecFlg",
    "trnGpCd",
    "utlDno",
)
R32_ATTRS = (
    "additional_seat_attribute_code",
    "adult_disabled_person_count",
    "adult_count",
    "arrival_station_code",
    "arrival_station_name",
    "baby_accompanying_person_count",
    "changed_at",
    "changed_by",
    "child_count",
    "child_disabled_person_count",
    "customer_management_no",
    "day_code",
    "direction_seat_attribute_group_code",
    "direct_transfer_division_code",
    "departure_station_code",
    "departure_station_name",
    "early_train_departure_time",
    "elderly_person_count",
    "included_flag",
    "job_start_hour",
    "location_seat_attribute_group_code",
    "media_division_code",
    "room_class_code",
    "passenger_total",
    "registered_at",
    "registration_sequence",
    "registered_by",
    "trip_day_no",
    "train_classification_code",
    "train_connection_flag",
    "train_group_code",
    "usage_day_no",
)
R43_FIELDS = (
    "addSrvDvCd",
    "addSrvGdCd",
    "addSrvId",
    "addSrvMrkEntId",
    "addSrvMrkEntNm",
    "addSrvNm",
    "addSrvPrgSttCd",
    "addSrvReqNo",
    "cgPsRefAtclCont",
    "coptEntRsvNo",
    "dlivPsbClsTm",
    "dlivPsbStTm",
    "leadMsgCont1",
    "leadMsgCont2",
    "pnrNo",
    "reqDt",
    "reqQnty",
    "rsvSpecUrl",
    "utlClsDt",
    "utlStDt",
)
R43_ATTRS = (
    "additional_service_division_code",
    "additional_service_goods_code",
    "additional_service_id",
    "marketing_entity_id",
    "marketing_entity_name",
    "additional_service_name",
    "progress_status_code",
    "request_no",
    "passenger_reference_content",
    "partner_reservation_no",
    "delivery_close_time",
    "delivery_start_time",
    "lead_message_1",
    "lead_message_2",
    "pnr_no",
    "request_date",
    "request_quantity",
    "reservation_specification_url",
    "usage_close_date",
    "usage_start_date",
)


def _success(**extra: Any) -> dict[str, Any]:
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": "synthetic success",
        "strResult": "SUCC",
        **extra,
    }


def _session(*, customer_no: str | None = "SYNTHETIC_CUSTOMER_NO") -> KorailSession:
    return KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        member_card_no="SYNTHETIC_MEMBER_CARD_NO",
        customer_no=customer_no,
    )


def _recording_client(
    responses: dict[str, dict[str, Any]],
) -> tuple[KorailClient, list[httpx.Request], list[Any]]:
    requests: list[httpx.Request] = []
    provider_calls: list[Any] = []

    def provider(context: Any) -> str:
        provider_calls.append(context)
        raise AssertionError("DynaPath provider must not be invoked")

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=responses[request.url.path])

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=provider,
            allowlist_paths=frozenset(responses),
        )
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    client.session.current = _session()
    return client, requests, provider_calls


def test_new_routes_and_public_contract_are_exact():
    assert len(KORAIL_READ_ONLY_ROUTES) == 58
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    assert ("POST", R54_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert not hasattr(KorailClient, "get_tour_train_info")
    assert not hasattr(korail_mobile_api.read_payloads, "build_tour_train_info_form")

    expected_fields = {
        R13_PATH: {"Device", "Version", "Key", "dptDt"},
        R32_PATH: {
            "Device",
            "Version",
            "Key",
            "custMgNo",
            "medDvCd",
            "regSqno",
        },
        R43_PATH: {"Device", "Version", "qryDtFrom", "qryDtTo"},
        R45_PATH: {"Device", "Version", "Key", "tripChgDate"},
    }
    for path, names in expected_fields.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == names

    contracts = {
        "get_multi_child_discount_targets": (
            ["self", "departure_date"],
            {"departure_date": str, "return": MultiChildDiscountTargetResponse},
        ),
        "get_customer_trip_info": (
            ["self"],
            {"return": CustomerTripInfoResponse},
        ),
        "get_maas_service_details": (
            ["self", "query"],
            {
                "query": MaasServiceDetailQuery | None,
                "return": MaasServiceDetailListResponse,
            },
        ),
        "get_trip_change_dates": (
            ["self", "departure_date"],
            {"departure_date": str, "return": TripChangeDateResponse},
        ),
    }
    for method_name, (parameters, hints) in contracts.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == parameters
        assert get_type_hints(method) == hints
    assert inspect.signature(KorailClient.get_maas_service_details).parameters[
        "query"
    ].default is None

    for name in (
        "MultiChildDiscountTarget",
        "MultiChildDiscountTargetResponse",
        "CustomerTripInfo",
        "CustomerTripInfoResponse",
        "MaasServiceDetailQuery",
        "MaasServiceDetail",
        "MaasServiceDetailListResponse",
        "TripChangeDateResponse",
    ):
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name)
    assert "TourTrainInfoResponse" not in korail_mobile_api.__all__


def test_new_safety_contracts_reject_wrong_order_and_allow_both_maas_shapes():
    valid_orders = {
        R13_PATH: ("Device", "Version", "Key", "dptDt"),
        R32_PATH: (
            "Device",
            "Version",
            "Key",
            "custMgNo",
            "medDvCd",
            "regSqno",
        ),
        R45_PATH: ("Device", "Version", "Key", "tripChgDate"),
    }
    for path, names in valid_orders.items():
        values = {name: "value" for name in names}
        assert_read_only_request_fields(path, values)
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(
                path,
                {name: "value" for name in reversed(names)},
            )

    assert_read_only_request_fields(
        R43_PATH,
        {"Device": "AD", "Version": "1"},
    )
    assert_read_only_request_fields(
        R43_PATH,
        {
            "Device": "AD",
            "Version": "1",
            "qryDtFrom": "20990101",
            "qryDtTo": "20990201",
        },
    )
    for invalid in (
        {"Version": "1", "Device": "AD"},
        {"Device": "AD", "Version": "1", "qryDtFrom": "20990101"},
        {
            "Device": "AD",
            "Version": "1",
            "qryDtTo": "20990201",
            "qryDtFrom": "20990101",
        },
    ):
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(R43_PATH, invalid)


def test_payload_builders_emit_only_closed_wire_fields():
    config = KorailConfig()
    current = MaasServiceDetailQuery.current()
    history = MaasServiceDetailQuery.history("20990101", "20990401")
    assert build_multi_child_discount_target_form("20990101") == {
        "dptDt": "20990101"
    }
    assert build_customer_trip_info_form("CUSTOMER") == {
        "custMgNo": "CUSTOMER",
        "medDvCd": "03",
        "regSqno": "0",
    }
    assert build_maas_service_detail_form(config, current) == {
        "Device": config.device,
        "Version": config.version,
    }
    assert build_maas_service_detail_form(config, history) == {
        "Device": config.device,
        "Version": config.version,
        "qryDtFrom": "20990101",
        "qryDtTo": "20990401",
    }
    assert build_trip_change_date_form("20990101") == {
        "tripChgDate": "20990101"
    }
    assert is_dataclass(current)
    assert current == MaasServiceDetailQuery.current()
    with pytest.raises(FrozenInstanceError):
        current.start_date = "20990101"
    assert "20990101" not in repr(history)


def test_maas_builder_rejects_query_subclasses_even_when_init_is_bypassed():
    class UnsafeQuery(MaasServiceDetailQuery):
        def __post_init__(self) -> None:
            pass

    query = UnsafeQuery(start_date="not-a-date", end_date=None)

    with pytest.raises(TypeError, match="exact MaasServiceDetailQuery"):
        build_maas_service_detail_form(KorailConfig(), query)


@pytest.mark.parametrize(
    ("start_date", "end_date"),
    [
        ("20990101", None),
        ("２０９９０１０１", "20990201"),
        ("20990230", "20990301"),
        ("20990201", "20990131"),
        ("20990131", "20990501"),
    ],
)
def test_maas_builder_revalidates_mutated_exact_queries(
    start_date,
    end_date,
):
    query = MaasServiceDetailQuery.current()
    object.__setattr__(query, "start_date", start_date)
    object.__setattr__(query, "end_date", end_date)

    with pytest.raises(ValueError):
        build_maas_service_detail_form(KorailConfig(), query)


@pytest.mark.parametrize(
    ("fixture_name", "parser", "response_type", "collection_name", "wire", "attrs"),
    [
        (
            "mchd_discount_targets_success.json",
            parse_multi_child_discount_target_response,
            MultiChildDiscountTargetResponse,
            "targets",
            R13_FIELDS,
            R13_ATTRS,
        ),
        (
            "customer_trip_info_success.json",
            parse_customer_trip_info_response,
            CustomerTripInfoResponse,
            "trips",
            R32_FIELDS,
            R32_ATTRS,
        ),
        (
            "maas_service_detail_list_success.json",
            parse_maas_service_detail_list_response,
            MaasServiceDetailListResponse,
            "details",
            R43_FIELDS,
            R43_ATTRS,
        ),
    ],
)
def test_list_parsers_preserve_every_exact_nullable_string(
    load_json_fixture,
    fixture_name,
    parser,
    response_type,
    collection_name,
    wire,
    attrs,
):
    raw = load_json_fixture(fixture_name)
    result = parser(raw)

    assert isinstance(result, response_type)
    assert result.raw is raw
    items = getattr(result, collection_name)
    assert len(items) == 1
    item = items[0]
    assert item.raw is raw[
        {
            "targets": "fmlyList",
            "trips": "mainList",
            "details": "addSrvList",
        }[collection_name]
    ][0]
    for wire_name, attr_name in zip(wire, attrs, strict=True):
        expected = raw[
            {
                "targets": "fmlyList",
                "trips": "mainList",
                "details": "addSrvList",
            }[collection_name]
        ][0][wire_name]
        assert getattr(item, attr_name) == expected


def test_trip_change_parser_normalizes_optional_values(load_json_fixture):
    raw = load_json_fixture("trip_change_dates_success.json")
    result = parse_trip_change_date_response(raw)
    assert result.last_run_date == "20991231"
    assert result.trip_change_date == "20990101"
    assert result.trip_change_dates == ("20990101", "20990102")
    assert result.raw is raw

    nullable = _success(
        lastRunDt=None,
        tripChgDate=None,
        tripChgDates=None,
    )
    result = parse_trip_change_date_response(nullable)
    assert result.last_run_date is None
    assert result.trip_change_date is None
    assert result.trip_change_dates == ()


def test_tour_train_parser_is_typed_but_transport_is_held_back(load_json_fixture):
    raw = load_json_fixture("tour_train_info_success.json")
    result = parse_tour_train_info_response(raw)
    assert isinstance(result, TourTrainInfoResponse)
    assert len(result.seat_infos) == 1
    assert result.seat_infos[0].seat_attribute_code == "SYNTHETIC_SEAT_ATTRIBUTE"
    assert result.seat_infos[0].additional_infos[0].passenger_count == 2
    assert result.raw is raw

    for nullable in (
        _success(seat_infos=None),
        _success(seat_infos={"seat_info": None}),
        _success(
            seat_infos={
                "seat_info": [
                    {"h_seat_att_cd": None, "seat_add_infos": None},
                    {
                        "h_seat_att_cd": None,
                        "seat_add_infos": {"seat_add_info": None},
                    },
                ]
            }
        ),
    ):
        parsed = parse_tour_train_info_response(nullable)
        if nullable["seat_infos"] is None or not nullable["seat_infos"].get("seat_info"):
            assert parsed.seat_infos == ()
        else:
            assert all(item.additional_infos == () for item in parsed.seat_infos)

    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", R54_PATH)


@pytest.mark.parametrize(
    ("parser", "container", "row_fields"),
    [
        (parse_multi_child_discount_target_response, "fmlyList", R13_FIELDS),
        (parse_customer_trip_info_response, "mainList", R32_FIELDS),
        (parse_maas_service_detail_list_response, "addSrvList", R43_FIELDS),
    ],
)
def test_list_parsers_normalize_null_and_reject_bad_containers_rows_and_scalars(
    parser,
    container,
    row_fields,
):
    assert not fields(parser(_success(**{container: None})))[-1].repr
    parsed = parser(_success(**{container: None}))
    collection = (
        parsed.targets
        if container == "fmlyList"
        else parsed.trips
        if container == "mainList"
        else parsed.details
    )
    assert collection == ()
    for bad in ({}, "bad", 1, True):
        with pytest.raises(KorailProtocolError):
            parser(_success(**{container: bad}))
    for bad_row in (None, "bad", 1, []):
        with pytest.raises(KorailProtocolError):
            parser(_success(**{container: [bad_row]}))
    for field_name in row_fields:
        with pytest.raises(KorailProtocolError, match=field_name):
            parser(
                _success(
                    **{
                        container: [
                            {name: None for name in row_fields}
                            | {field_name: 1}
                        ]
                    }
                )
            )


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        (_success(tripChgDates="bad"), "tripChgDates"),
        (_success(tripChgDates=[None]), "tripChgDates"),
        (_success(tripChgDates=[1]), "tripChgDates"),
        (_success(lastRunDt=1), "lastRunDt"),
        (_success(tripChgDate=[]), "tripChgDate"),
    ],
)
def test_trip_change_parser_rejects_malformed_values(raw, match):
    with pytest.raises(KorailProtocolError, match=match):
        parse_trip_change_date_response(raw)


@pytest.mark.parametrize(
    "payload",
    [
        _success(seat_infos="bad"),
        _success(seat_infos={"seat_info": {}}),
        _success(seat_infos={"seat_info": [None]}),
        _success(seat_infos={"seat_info": [{"h_seat_att_cd": 1}]}),
        _success(
            seat_infos={
                "seat_info": [{"seat_add_infos": {"seat_add_info": {}}}]
            }
        ),
        _success(
            seat_infos={
                "seat_info": [
                    {"seat_add_infos": {"seat_add_info": [None]}}
                ]
            }
        ),
    ],
)
def test_tour_train_parser_rejects_bad_container_shapes(payload):
    with pytest.raises(KorailProtocolError):
        parse_tour_train_info_response(payload)


def _tour_train_with_passenger_count(passenger_count):
    return _success(
        seat_infos={
            "seat_info": [
                {
                    "h_seat_att_cd": None,
                    "seat_add_infos": {
                        "seat_add_info": [{"h_psg_num": passenger_count}]
                    },
                }
            ]
        }
    )


@pytest.mark.parametrize("passenger_count", [True, 2.0, None, "", "x"])
def test_tour_train_passenger_count_rejects_non_numeric(passenger_count):
    raw = _tour_train_with_passenger_count(passenger_count)
    with pytest.raises(KorailProtocolError, match="h_psg_num"):
        parse_tour_train_info_response(raw)


@pytest.mark.parametrize(
    ("wire", "expected"),
    [(2, 2), ("2", 2), ("0", 0)],
)
def test_tour_train_passenger_count_accepts_gson_coerced_string(wire, expected):
    # RV4-05: TourTrainInfoDao.SeatAddInfo.h_psg_num is Java `int`; the
    # h_-prefixed backend serializes such ints as quoted strings and Gson
    # coerces them, so a quoted-string count parses like a native int.
    raw = _tour_train_with_passenger_count(wire)
    parsed = parse_tour_train_info_response(raw)
    assert parsed.seat_infos[0].additional_infos[0].passenger_count == expected


PARSERS = (
    parse_multi_child_discount_target_response,
    parse_customer_trip_info_response,
    parse_maas_service_detail_list_response,
    parse_trip_change_date_response,
    parse_tour_train_info_response,
)


@pytest.mark.parametrize("parser", PARSERS)
@pytest.mark.parametrize("raw", [None, [], "bad", 1])
def test_all_parsers_reject_non_object_top_levels(parser, raw):
    with pytest.raises(KorailProtocolError):
        parser(raw)


@pytest.mark.parametrize("parser", PARSERS)
@pytest.mark.parametrize("result", ["SUCCESS", "succ", "UNKNOWN", None, 1, {}])
def test_all_parsers_require_exact_succ(parser, result):
    with pytest.raises(KorailProtocolError):
        parser(
            {
                "h_msg_cd": "SYNTHETIC.OK",
                "h_msg_txt": "synthetic",
                "strResult": result,
            }
        )


@pytest.mark.parametrize("parser", PARSERS)
@pytest.mark.parametrize("missing", ["h_msg_cd", "h_msg_txt", "strResult"])
def test_all_parsers_require_each_envelope_member(parser, missing):
    raw = _success()
    raw.pop(missing)
    with pytest.raises(KorailProtocolError, match=missing):
        parser(raw)


@pytest.mark.parametrize("parser", PARSERS)
@pytest.mark.parametrize("field", ["h_msg_cd", "h_msg_txt"])
def test_all_parsers_accept_null_optional_envelope_strings(parser, field):
    raw = _success()
    raw[field] = None
    assert parser(raw).str_result == "SUCC"


@pytest.mark.parametrize("parser", PARSERS)
@pytest.mark.parametrize("field", ["h_msg_cd", "h_msg_txt", "strResult"])
@pytest.mark.parametrize("bad", [1, {}, []])
def test_all_parsers_reject_bad_envelope_scalar_types(parser, field, bad):
    raw = _success()
    raw[field] = bad
    with pytest.raises(KorailProtocolError, match=field):
        parser(raw)


@pytest.mark.parametrize("parser", PARSERS)
def test_all_parsers_preserve_common_typed_failures(parser):
    with pytest.raises(KorailSessionExpiredError):
        parser(
            {
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic session expired",
                "strResult": "FAIL",
            }
        )
    for code in ("SYNTHETIC.FAIL", "WRC000288"):
        with pytest.raises(KorailAppError):
            parser(
                {
                    "h_msg_cd": code,
                    "h_msg_txt": "synthetic application failure",
                    "strResult": "FAIL",
                }
            )


def test_four_public_reads_emit_exact_ordered_bodies_once_without_dynapath(
    load_json_fixture,
):
    responses = {
        R13_PATH: load_json_fixture("mchd_discount_targets_success.json"),
        R32_PATH: load_json_fixture("customer_trip_info_success.json"),
        R43_PATH: load_json_fixture("maas_service_detail_list_success.json"),
        R45_PATH: load_json_fixture("trip_change_dates_success.json"),
    }
    client, requests, provider_calls = _recording_client(responses)
    config = client.config
    try:
        client.get_multi_child_discount_targets("20990101")
        client.get_customer_trip_info()
        client.get_maas_service_details()
        client.get_maas_service_details(
            MaasServiceDetailQuery.history("20990101", "20990401")
        )
        client.get_trip_change_dates("20990101")
    finally:
        client.close()

    assert [request.url.path for request in requests] == [
        R13_PATH,
        R32_PATH,
        R43_PATH,
        R43_PATH,
        R45_PATH,
    ]
    assert [parse_qsl(request.content.decode(), keep_blank_values=True) for request in requests] == [
        [
            ("Device", config.device),
            ("Version", config.version),
            ("Key", config.key),
            ("dptDt", "20990101"),
        ],
        [
            ("Device", config.device),
            ("Version", config.version),
            ("Key", config.key),
            ("custMgNo", "SYNTHETIC_CUSTOMER_NO"),
            ("medDvCd", "03"),
            ("regSqno", "0"),
        ],
        [("Device", config.device), ("Version", config.version)],
        [
            ("Device", config.device),
            ("Version", config.version),
            ("qryDtFrom", "20990101"),
            ("qryDtTo", "20990401"),
        ],
        [
            ("Device", config.device),
            ("Version", config.version),
            ("Key", config.key),
            ("tripChgDate", "20990101"),
        ],
    ]
    assert all(request.method == "POST" for request in requests)
    assert all("x-dynapath-m-token" not in request.headers for request in requests)
    assert provider_calls == []


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("get_multi_child_discount_targets", ("20990101",)),
        ("get_customer_trip_info", ()),
        ("get_maas_service_details", ()),
        ("get_trip_change_dates", ("20990101",)),
    ],
)
def test_all_public_account_reads_require_session_before_transport(method_name, args):
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(KorailAuthError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 0


def test_customer_trip_info_never_falls_back_to_member_or_card_number():
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = _session(customer_no=None)
    try:
        with pytest.raises(KorailAuthError, match="customer"):
            client.get_customer_trip_info()
    finally:
        client.close()
    assert calls == 0


def test_false_maas_query_is_not_silently_treated_as_current():
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = _session()
    try:
        with pytest.raises(TypeError, match="exact MaasServiceDetailQuery"):
            client.get_maas_service_details(False)
    finally:
        client.close()
    assert calls == 0


@pytest.mark.parametrize(
    ("method_name", "args"),
    [
        ("get_multi_child_discount_targets", ("2099010",)),
        ("get_multi_child_discount_targets", ("２０９９０１０１",)),
        ("get_multi_child_discount_targets", (20990101,)),
        ("get_trip_change_dates", ("2099-01-01",)),
        ("get_trip_change_dates", ("２０９９０１０１",)),
        ("get_trip_change_dates", (None,)),
    ],
)
def test_invalid_scalar_arguments_fail_before_dynapath_and_transport(method_name, args):
    calls = 0
    provider_calls = 0

    def provider(_: Any) -> str:
        nonlocal provider_calls
        provider_calls += 1
        raise AssertionError("provider must not be called")

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(
                enabled=True,
                token_provider=provider,
                allowlist_paths=frozenset({R13_PATH, R45_PATH}),
            )
        ),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = _session()
    try:
        with pytest.raises(ValueError):
            getattr(client, method_name)(*args)
    finally:
        client.close()
    assert calls == 0
    assert provider_calls == 0


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("2099010", "20990201"),
        ("２０９９０１０１", "20990201"),
        ("20990101", "2099-02-01"),
        ("20990201", "20990131"),
        ("20990131", "20990501"),
        ("20991130", "21000301"),
        (None, "20990201"),
    ],
)
def test_maas_history_rejects_bad_reversed_or_over_three_month_ranges(start, end):
    with pytest.raises(ValueError):
        MaasServiceDetailQuery.history(start, end)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("20990131", "20990430"),
        ("20991130", "21000228"),
        ("21040229", "21040529"),
    ],
)
def test_maas_history_accepts_at_most_three_calendar_months(start, end):
    query = MaasServiceDetailQuery.history(start, end)
    assert query.start_date == start
    assert query.end_date == end


def test_login_extracts_only_str_customer_number_and_repr_hides_it():
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if request.url.path == "/file/CACHE/MobileService.cache":
            return httpx.Response(200, json=_success())
        if request.url.path == "/classes/com.korail.mobile.common.code.do":
            return httpx.Response(200, json=_success(idx="", key="", pwdAESCphd="N"))
        if request.url.path == "/classes/com.korail.mobile.login.Login":
            return httpx.Response(
                200,
                json={
                    "h_msg_cd": "IRZ000001",
                    "h_msg_txt": "synthetic login",
                    "strResult": "SUCC",
                    "strCustNo": "SYNTHETIC_CUSTOMER_NO",
                    "mbCrdNo": "SYNTHETIC_MEMBER_CARD_NO",
                },
                headers={"Set-Cookie": "JSESSIONID=SYNTHETIC_SESSION; Path=/"},
            )
        raise AssertionError(request.url.path)

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        session = client.login("SYNTHETIC_MEMBER_NO", "synthetic-password")
    finally:
        client.close()

    assert session.customer_no == "SYNTHETIC_CUSTOMER_NO"
    rendered = repr(session)
    for secret in (
        "SYNTHETIC_CUSTOMER_NO",
        "SYNTHETIC_MEMBER_NO",
        "SYNTHETIC_MEMBER_CARD_NO",
        "SYNTHETIC_SESSION",
    ):
        assert secret not in rendered
    assert calls == [
        "/file/CACHE/MobileService.cache",
        "/classes/com.korail.mobile.common.code.do",
        "/classes/com.korail.mobile.login.Login",
    ]


def test_sensitive_models_and_raw_values_are_repr_hidden(load_json_fixture):
    models = (
        parse_multi_child_discount_target_response(
            load_json_fixture("mchd_discount_targets_success.json")
        ),
        parse_customer_trip_info_response(
            load_json_fixture("customer_trip_info_success.json")
        ),
        parse_maas_service_detail_list_response(
            load_json_fixture("maas_service_detail_list_success.json")
        ),
        parse_trip_change_date_response(
            load_json_fixture("trip_change_dates_success.json")
        ),
        parse_tour_train_info_response(
            load_json_fixture("tour_train_info_success.json")
        ),
    )
    rendered = " ".join(repr(model) for model in models)
    for secret in (
        "SYNTHETIC_RAW_SECRET",
        "SYNTHETIC_custMgNo",
        "SYNTHETIC_pnrNo",
        "SYNTHETIC_rsvSpecUrl",
        "SYNTHETIC_SEAT_ATTRIBUTE",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    "response_type",
    [
        MultiChildDiscountTargetResponse,
        CustomerTripInfoResponse,
        MaasServiceDetailListResponse,
        TripChangeDateResponse,
        TourTrainInfoResponse,
    ],
)
def test_new_response_free_text_is_repr_hidden(response_type):
    secret = "SYNTHETIC_RESPONSE_FREE_TEXT_SECRET"

    response = response_type(h_msg_txt=secret)

    assert secret not in repr(response)


def test_session_expiry_clears_current_session(load_json_fixture):
    client, requests, _ = _recording_client(
        {
            R13_PATH: {
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic session expired",
                "strResult": "FAIL",
            }
        }
    )
    try:
        with pytest.raises(KorailSessionExpiredError):
            client.get_multi_child_discount_targets("20990101")
        assert client.session.current is None
    finally:
        client.close()
    assert len(requests) == 1


def test_non_dynapath_http_and_json_failures_remain_typed():
    def http_error(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="synthetic unavailable")

    client = KorailClient(transport=httpx.MockTransport(http_error))
    client.session.current = _session()
    try:
        with pytest.raises(KorailTransportError):
            client.get_trip_change_dates("20990101")
    finally:
        client.close()

    def invalid_json(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    client = KorailClient(transport=httpx.MockTransport(invalid_json))
    client.session.current = _session()
    try:
        with pytest.raises(KorailProtocolError, match="JSON"):
            client.get_trip_change_dates("20990101")
    finally:
        client.close()
