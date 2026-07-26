from __future__ import annotations

from urllib.parse import parse_qsl, urlsplit

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailProtocolError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    DiscountCardScheduleResponse,
    DiscountCardUsageListResponse,
)
from korail_mobile_api.read_parsers import (
    parse_discount_card_schedule_response,
    parse_discount_card_usage_response,
)
from korail_mobile_api.read_payloads import (
    DiscountCardScheduleRequest,
    build_discount_card_schedule_query,
    build_discount_card_usage_query,
)
from korail_mobile_api.redaction import redact_mapping, redact_payload
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_MUTATION_ROUTES,
    KORAIL_OPTIONAL_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


USAGE_PATH = "/classes/com.korail.mobile.ticket.dcntCrdUseQry.do"
SCHEDULE_PATH = "/classes/com.korail.mobile.research.dcntCrdScheduleView.do"

# The two dcntCrd* routes this branch deliberately does NOT make reachable
# through the read-only transport (ResearchService.java:65-70).
WRITE_PATHS = (
    "/classes/com.korail.mobile.research.dcntCrdInfo.do",
    "/classes/com.korail.mobile.reservation.dcntCrdExtn.do",
)


def _envelope(**extra: object) -> dict[str, object]:
    return {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "정상처리되었습니다",
        "strResult": "SUCC",
        **extra,
    }


def _schedule_request(**overrides: object) -> DiscountCardScheduleRequest:
    fields: dict[str, object] = {
        "card_kind_management_no": "B2N23100501",
        "departure_station_name": "서울",
        "arrival_station_name": "부산",
        "departure_date": "20990101",
        "usable_trip_count": "10",
    }
    fields.update(overrides)
    return DiscountCardScheduleRequest(**fields)  # type: ignore[arg-type]


def _client(handler) -> KorailClient:
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        customer_no="SYNTHETIC_CUSTOMER_NO",
        raw={},
    )
    return client


def test_route_boundary_admits_the_two_reads_and_neither_write():
    assert len(KORAIL_READ_ONLY_ROUTES) == 58
    assert ("GET", USAGE_PATH) in KORAIL_READ_ONLY_ROUTES
    assert ("GET", SCHEDULE_PATH) in KORAIL_READ_ONLY_ROUTES
    for path in WRITE_PATHS:
        for method in ("GET", "POST"):
            assert (method, path) not in KORAIL_READ_ONLY_ROUTES
            assert (method, path) not in KORAIL_MUTATION_ROUTES
    # Both reads are GET-only; the app declares no POST overload for either
    # (ResearchService.java:51,54).
    assert ("POST", USAGE_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert ("POST", SCHEDULE_PATH) not in KORAIL_READ_ONLY_ROUTES
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", USAGE_PATH)
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("GET", WRITE_PATHS[1])


def test_usage_query_is_the_card_number_and_the_common_three():
    assert build_discount_card_usage_query("N123") == {"dcntCrdNo": "N123"}
    assert KORAIL_EXACT_REQUEST_FIELDS[USAGE_PATH] == frozenset(
        {"Device", "Version", "Key", "dcntCrdNo"}
    )
    with pytest.raises(ValueError):
        build_discount_card_usage_query("")
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            USAGE_PATH,
            {
                "Device": "AD",
                "Version": "v",
                "Key": "k",
                "dcntCrdNo": "N1",
                "extra": "x",
            },
        )


def test_schedule_query_matches_the_apk_builder_and_omits_the_two_nulls():
    # u4/b.java:52-65 -- the 1-section builder sets neither useTrmDno nor
    # qryPgNo, so neither leaves the device.
    query = build_discount_card_schedule_query(_schedule_request())
    assert query == {
        "dptDt": "20990101",
        "dptRsStnNm": "서울",
        "arvRsStnNm": "부산",
        "dptTm": "000000",
        "trnGpCd": "109",
        "dirtChtnDvCd": "1",
        "dcntCrdKndCd": "MMM",
        "dcntCrdKndMgNo": "B2N23100501",
        "usePsbTno": "10",
    }
    assert_read_only_request_fields(
        SCHEDULE_PATH,
        {"Device": "AD", "Version": "v", "Key": "k", **query},
    )
    assert KORAIL_OPTIONAL_REQUEST_FIELDS[SCHEDULE_PATH] == frozenset(
        {"useTrmDno", "qryPgNo"}
    )


def test_schedule_query_carries_period_and_page_when_supplied():
    query = build_discount_card_schedule_query(
        _schedule_request(usage_period_days="60", page_no="2")
    )
    assert query["useTrmDno"] == "60"
    assert query["qryPgNo"] == "2"
    assert_read_only_request_fields(
        SCHEDULE_PATH,
        {"Device": "AD", "Version": "v", "Key": "k", **query},
    )


def test_for_card_derives_the_kind_code_the_way_the_app_does():
    # u4/b.java:61 -- exactly two management numbers map to "B2N".
    for management_no in ("B2N18120402", "B2N18120403"):
        assert (
            DiscountCardScheduleRequest.for_card(
                management_no,
                departure_station_name="서울",
                arrival_station_name="부산",
                departure_date="20990101",
            ).card_kind_code
            == "B2N"
        )
    for management_no in ("B2N19060502", "B2N23100507", "B2N18120404"):
        assert (
            DiscountCardScheduleRequest.for_card(
                management_no,
                departure_station_name="서울",
                arrival_station_name="부산",
                departure_date="20990101",
            ).card_kind_code
            == "MMM"
        )


def test_schedule_builder_refuses_a_lookalike_request_object():
    class Lookalike(DiscountCardScheduleRequest):
        pass

    with pytest.raises(TypeError):
        build_discount_card_schedule_query(
            Lookalike(
                card_kind_management_no="B2N23100501",
                departure_station_name="서울",
                arrival_station_name="부산",
                departure_date="20990101",
            )
        )
    with pytest.raises(ValueError):
        build_discount_card_schedule_query(
            _schedule_request(departure_date="2099-01-01")
        )
    with pytest.raises(ValueError):
        build_discount_card_schedule_query(
            _schedule_request(departure_time="0000")
        )


def test_usage_parser_reads_the_ncard_history_dao_shape():
    parsed = parse_discount_card_usage_response(
        _envelope(
            tkUseList=[
                {
                    "custNm": "홍길동",
                    "dptStnNm": "서울",
                    "arvStnNm": "부산",
                    "runDt1": "20990101",
                    "apdUsrFlg": "Y",
                }
            ]
        )
    )
    assert type(parsed) is DiscountCardUsageListResponse
    assert len(parsed.items) == 1
    entry = parsed.items[0]
    assert entry.passenger_name == "홍길동"
    assert entry.departure_station_name == "서울"
    assert entry.arrival_station_name == "부산"
    assert entry.run_date == "20990101"
    assert entry.additional_user_flag == "Y"
    assert parse_discount_card_usage_response(_envelope()).items == ()


def test_schedule_parser_reads_the_ncard_inquiry_dao_shape():
    parsed = parse_discount_card_schedule_response(
        _envelope(
            fllwPgExt="Y",
            trnScdlList=[
                {
                    "trnNo": "00101",
                    "trnGpCd": "100",
                    "runDt": "20990101",
                    "dptRsStnCd": "0001",
                    "dptRsStnNm": "서울",
                    "arvRsStnCd": "0020",
                    "arvRsStnNm": "부산",
                    "dptStnConsOrdr": 1,
                    "arvStnConsOrdr": "000010",
                    "cmtrPrc": 59800,
                    "dirtChtnDvCd": "1",
                    "dturCd": "0",
                    "dturNm": "",
                    "routCd": "01",
                    "stationStringInfo": "서울-부산",
                }
            ],
        )
    )
    assert type(parsed) is DiscountCardScheduleResponse
    assert parsed.following_page_exists == "Y"
    train = parsed.trains[0]
    assert train.train_no == "00101"
    # A JSON number where the DAO declares a String is accepted, because Gson
    # coerces it in the app and this route has never been observed live.
    assert train.departure_station_order == "1"
    assert train.commuter_price == "59800"
    assert parse_discount_card_schedule_response(_envelope()).trains == ()


def test_parsers_refuse_a_non_success_or_malformed_body():
    # WRR000100 입력값 오류(dcntCrdNo) is what this route answered on
    # 2026-07-09 when it was probed without a card number
    # (docs/api-status-by-service.md:467). It is an application failure, not a
    # protocol one, so it must arrive as a KorailAppError.
    with pytest.raises(KorailAppError):
        parse_discount_card_usage_response(
            {
                "h_msg_cd": "WRR000100",
                "h_msg_txt": "입력값 오류",
                "strResult": "FAIL",
            }
        )
    with pytest.raises(KorailProtocolError):
        parse_discount_card_usage_response(_envelope(tkUseList=["nope"]))
    with pytest.raises(KorailProtocolError):
        parse_discount_card_schedule_response(
            _envelope(trnScdlList=[{"trnNo": ["nope"]}])
        )


def test_client_reads_send_exactly_the_registered_shapes():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == USAGE_PATH:
            return httpx.Response(200, json=_envelope(tkUseList=[]))
        return httpx.Response(200, json=_envelope(trnScdlList=[]))

    client = _client(handler)
    try:
        client.get_discount_card_usage_history("N123")
        client.get_discount_card_schedule(_schedule_request())
    finally:
        client.close()

    assert [request.method for request in seen] == ["GET", "GET"]
    usage = dict(parse_qsl(urlsplit(str(seen[0].url)).query))
    assert usage == {
        "Device": "AD",
        "Version": client.config.version,
        "Key": client.config.key,
        "dcntCrdNo": "N123",
    }
    schedule = dict(parse_qsl(urlsplit(str(seen[1].url)).query))
    assert set(schedule) == {
        "Device",
        "Version",
        "Key",
        "dptDt",
        "dptRsStnNm",
        "arvRsStnNm",
        "dptTm",
        "trnGpCd",
        "dirtChtnDvCd",
        "dcntCrdKndCd",
        "dcntCrdKndMgNo",
        "usePsbTno",
    }
    # DynaPath stays off: neither route is in the six-path allowlist.
    for request in seen:
        assert "x-dynapath-m-token" not in {
            name.lower() for name in request.headers
        }


def test_client_reads_require_a_session():
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("no request may be sent without a session")

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.get_discount_card_usage_history("N123")
        with pytest.raises(KorailAuthError):
            client.get_discount_card_schedule(_schedule_request())
    finally:
        client.close()


def test_the_card_number_is_redacted_everywhere_it_appears():
    redacted = redact_mapping({"dcntCrdNo": "N1234567890"})
    assert "N1234567890" not in str(redacted)
    redacted = redact_payload({"h_dcnt_crd_no": "N1234567890"})
    assert "N1234567890" not in str(redacted)
    redacted = redact_payload({"discount_card_no": "N1234567890"})
    assert "N1234567890" not in str(redacted)


def test_public_surface_exports_the_new_names():
    for name in (
        "DiscountCardScheduleRequest",
        "DiscountCardScheduleResponse",
        "DiscountCardScheduleTrain",
        "DiscountCardUsage",
        "DiscountCardUsageListResponse",
    ):
        assert name in korail_mobile_api.__all__
        assert hasattr(korail_mobile_api, name)
    assert hasattr(KorailClient, "get_discount_card_usage_history")
    assert hasattr(KorailClient, "get_discount_card_schedule")
    # Nothing on this branch adds a way to register or extend a card yet.
    assert not hasattr(KorailClient, "register_discount_card")
    assert not hasattr(KorailClient, "extend_discount_card")
