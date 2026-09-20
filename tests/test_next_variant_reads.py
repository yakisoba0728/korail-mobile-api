# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from typing import get_type_hints
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from _read_field_contracts import (
    KORAIL_EXACT_REQUEST_FIELDS,
    assert_read_only_request_fields,
)
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.parsers import (
    parse_train_rows,
    parse_train_search_metadata,
)
from korail_mobile_api.read_models import (
    CommuterInfoResponse,
    CommuterPassengerOption,
    PassMenuData,
    PriceFareQuoteResponse,
)
from korail_mobile_api.read_parsers import (
    parse_commuter_info_response,
    parse_gift_ticket_list_response,
    parse_price_fare_quote_response,
)
from korail_mobile_api.read_payloads import (
    CommuterInitialRequest,
    CommuterPassengerRequest,
    CommuterTicketInquiryRequest,
    GiftTicketHistoryRequest,
    GiftTicketPaymentEligibilityRequest,
    OriginalTicketReference,
    PriceFareLeg,
    PriceFareQuoteRequest,
    build_commuter_info_form,
    build_gift_ticket_list_form,
    build_price_fare_quote_form,
)
from korail_mobile_api.safety import KORAIL_READ_ONLY_ROUTES, assert_read_only_route


R17_PATH = "/classes/com.korail.mobile.gift.gdLst.do"
R31_PATH = "/classes/com.korail.mobile.research.cmtrInfo.do"
R39_PATH = "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"
R52_PATH = "/classes/com.korail.mobile.trn.prcFare.do"


def _pass_data() -> PassMenuData:
    return PassMenuData(commuter_kind_code="SYNTHETIC_KIND")


def _leg(suffix: str = "1") -> PriceFareLeg:
    return PriceFareLeg(
        departure_station_code=f"D{suffix}",
        arrival_station_code=f"A{suffix}",
        run_date=f"2099010{suffix}",
        train_no=f"0000{suffix}",
        goods_no=f"G{suffix}",
        requested_seat_attribute_code=f"S{suffix}",
        train_group_code=f"T{suffix}",
        standing_train_classification_code=f"C{suffix}",
    )


def _commuter_source(*age_codes: str) -> CommuterInfoResponse:
    return CommuterInfoResponse(
        passenger_options=tuple(
            CommuterPassengerOption(commuter_usage_age_code=code)
            for code in age_codes
        )
    )


def test_route_and_holdback_boundary_is_exact():
    assert {("POST", R31_PATH), ("POST", R52_PATH)} <= KORAIL_READ_ONLY_ROUTES
    assert ("POST", R17_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert not hasattr(KorailClient, "get_gift_ticket_list")
    assert ("POST", R39_PATH) in KORAIL_READ_ONLY_ROUTES


def test_r17_tagged_forms_preserve_blank_vs_omitted_fields():
    assert build_gift_ticket_list_form(
        GiftTicketHistoryRequest.sent("20990101", "20991231")
    ) == (
        ("qryDvCd", "A"),
        ("qryVal", "E"),
        ("abrdDtFrom", "20990101"),
        ("abrdDtTo", "20991231"),
        ("usePsbFlg", ""),
    )
    assert build_gift_ticket_list_form(
        GiftTicketHistoryRequest.received("20990101", "20991231")
    )[0] == ("qryDvCd", "C")
    assert build_gift_ticket_list_form(GiftTicketPaymentEligibilityRequest()) == (
        ("qryDvCd", "F"),
        ("qryVal", "E"),
    )


def test_r31_closed_variants_preserve_grouped_duplicates():
    initial = build_commuter_info_form(CommuterInitialRequest(_pass_data()))
    assert initial == (
        ("jobDvCd", "a"),
        ("cmtrKndCd", "SYNTHETIC_KIND"),
        ("psgCnt", "0"),
    )
    passenger = build_commuter_info_form(
        CommuterPassengerRequest.from_response(
            _pass_data(),
            _commuter_source("AGE1", "AGE2"),
            passenger_counts=(1, 2),
        )
    )
    assert passenger == (
        ("jobDvCd", "b"),
        ("cmtrKndCd", "SYNTHETIC_KIND"),
        ("psgCnt", "2"),
        ("cmtrUtlAgeCd", "AGE1"),
        ("cmtrUtlAgeCd", "AGE2"),
    )
    ticket = OriginalTicketReference("W", "20990101", "S", "P")
    assert build_commuter_info_form(
        CommuterTicketInquiryRequest(ticket, inquiry_type="1")
    ) == (
        ("jobDvCd", "c"),
        ("psgCnt", "0"),
        ("ogtkSaleWctNo", "W"),
        ("ogtkSaleDd", "20990101"),
        ("ogtkSaleSqno", "S"),
        ("ogtkRetPwd", "P"),
        ("inquiryType", "1"),
    )


def test_r52_one_and_two_leg_forms_include_train_count():
    direct = build_price_fare_quote_form(
        PriceFareQuoteRequest(legs=(_leg(),))
    )
    transfer = build_price_fare_quote_form(
        PriceFareQuoteRequest(legs=(_leg("1"), _leg("2")))
    )
    assert direct[:2] == (("txtMenuId", "11"), ("chtnDvCd", "1"))
    assert transfer[:2] == (("txtMenuId", "11"), ("chtnDvCd", "2"))
    assert ("dptRsStnCd", "D1,D2") in transfer
    assert ("trnCnt", "1") in direct
    assert ("trnCnt", "2") in transfer
    assert transfer == (
        ("txtMenuId", "11"),
        ("chtnDvCd", "2"),
        ("trnCnt", "2"),
        ("dptRsStnCd", "D1,D2"),
        ("arvRsStnCd", "A1,A2"),
        ("runDt", "20990101,20990102"),
        ("trnNo", "00001,00002"),
        ("gdNo", "G1,G2"),
        ("rqSeatAttCd", "S1,S2"),
        ("trnGpCd", "T1,T2"),
        ("stlbTrnClsfCd", "C1,C2"),
    )


def test_r52_quote_builds_from_a_real_parsed_search_response(load_json_fixture):
    # The 7.0.6 DTO declares h_menu_id, but this fixture omits it. A quote
    # request still uses its observed menu-code default.
    raw = load_json_fixture("raw_typed_train_search.json")
    metadata = parse_train_search_metadata(raw)
    train = parse_train_rows(raw)[0]
    assert metadata.menu_id is None

    form = build_price_fare_quote_form(
        PriceFareQuoteRequest(
            legs=(
                PriceFareLeg(
                    departure_station_code=train.departure_station_code,
                    arrival_station_code=train.arrival_station_code,
                    run_date=train.run_date,
                    train_no=train.train_no,
                    # b5/c.java:374 stamps the response's top-level h_gd_no onto
                    # every TrainInfo row before the price screen reads it.
                    goods_no=metadata.product_no,
                    requested_seat_attribute_code=train.seat_attribute_code,
                    train_group_code=train.train_group_code,
                    standing_train_classification_code=(
                        train.train_class_code
                    ),
                ),
            )
        )
    )
    # a5/k.java:92-94 returns "11"; a5/u.java:279 carries it as the MENU_ID
    # intent extra; PriceFareActivity.java:49,62 sets it on the request.
    assert form[0] == ("txtMenuId", "11")
    assert ("gdNo", "SYNTHETIC-PRODUCT-NO") in form
    assert ("trnNo", "SYNTHETIC-TRAIN-NO") in form


def test_r31_client_sends_duplicate_fields_in_wire_order():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC.OK",
                "h_msg_txt": "synthetic",
                "strResult": "SUCC",
                "avlPrnbFrom": 0,
                "avlPrnbTo": 0,
                "psgList": [],
            },
        )

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="SYNTHETIC")
    request = CommuterPassengerRequest.from_response(
        _pass_data(),
        _commuter_source("A1", "A2"),
        passenger_counts=(1, 2),
    )
    client.get_commuter_info(request)
    assert parse_qsl(requests[0].content.decode(), keep_blank_values=True) == [
        ("Device", client.config.device),
        ("Version", client.config.version),
        ("Key", client.config.key),
        ("jobDvCd", "b"),
        ("cmtrKndCd", "SYNTHETIC_KIND"),
        ("psgCnt", "2"),
        ("cmtrUtlAgeCd", "A1"),
        ("cmtrUtlAgeCd", "A2"),
    ]


def test_public_signatures_and_exports_are_closed():
    contracts = {
        "get_commuter_info": CommuterInfoResponse,
        "get_price_fare_quote": PriceFareQuoteResponse,
    }
    for method_name, response_type in contracts.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == ["self", "request"]
        assert get_type_hints(method)["return"] is response_type
    for name in (
        "GiftTicketHistoryRequest",
        "GiftTicketPaymentEligibilityRequest",
        "GiftTicketListResponse",
        "CommuterInitialRequest",
        "CommuterPassengerRequest",
        "CommuterTicketInquiryRequest",
        "OriginalTicketReference",
        "CommuterInfoResponse",
        "PriceFareLeg",
        "PriceFareQuoteRequest",
        "PriceFareQuoteResponse",
    ):
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name)


def test_exact_safety_shapes_and_holdback_are_closed():
    assert R39_PATH in DYNAPATH_ALLOWLIST_PATHS
    assert R39_PATH in KORAIL_EXACT_REQUEST_FIELDS
    assert_read_only_route("POST", R39_PATH)

    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", R17_PATH)
    assert_read_only_request_fields(
        R31_PATH,
        (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("jobDvCd", "b"),
            ("cmtrKndCd", "C"),
            ("psgCnt", "2"),
            ("cmtrUtlAgeCd", "A1"),
            ("cmtrUtlAgeCd", "A2"),
        ),
    )
    for invalid in (
        (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("jobDvCd", "b"),
            ("cmtrKndCd", "C"),
            ("psgCnt", "2"),
            ("cmtrUtlAgeCd", "A1"),
        ),
        (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("jobDvCd", "b"),
            ("cmtrKndCd", "C"),
            ("psgCnt", "1"),
            ("unexpected", "X"),
        ),
    ):
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(R31_PATH, invalid)


def test_tagged_request_validation_is_rechecked_at_builder_boundary():
    sent = GiftTicketHistoryRequest.sent("20990101", "20991231")
    with pytest.raises(FrozenInstanceError):
        sent.start_date = "20990102"
    assert "20990101" not in repr(sent)
    object.__setattr__(sent, "_query_division_code", "Z")
    with pytest.raises(ValueError):
        build_gift_ticket_list_form(sent)

    with pytest.raises(TypeError):
        build_gift_ticket_list_form(object())
    with pytest.raises(ValueError):
        GiftTicketHistoryRequest.sent("20990230", "20991231")
    with pytest.raises(ValueError):
        GiftTicketHistoryRequest.received("20991231", "20990101")


def test_commuter_request_provenance_lengths_and_repr_are_strict():
    source = _commuter_source("SECRET_AGE_1", "SECRET_AGE_2")
    request = CommuterPassengerRequest.from_response(
        _pass_data(),
        source,
        passenger_counts=(0, 2),
    )
    assert "SECRET" not in repr(request)
    with pytest.raises(ValueError):
        CommuterPassengerRequest.from_response(
            _pass_data(), source, passenger_counts=(1,)
        )
    with pytest.raises(TypeError):
        CommuterPassengerRequest.from_response(
            _pass_data(), source, passenger_counts=[1, 2]
        )
    with pytest.raises(ValueError):
        CommuterPassengerRequest.from_response(
            _pass_data(), source, passenger_counts=(True, 1)
        )
    with pytest.raises(ValueError):
        CommuterTicketInquiryRequest(
            OriginalTicketReference("W", "D", "S", "P"),
            inquiry_type="2",
        )
    reference = OriginalTicketReference(
        "SECRET_WINDOW",
        "SECRET_DATE",
        "SECRET_SEQUENCE",
        "SECRET_PASSWORD",
    )
    assert "SECRET" not in repr(reference)

    class UnsafePassData(PassMenuData):
        pass

    with pytest.raises(TypeError):
        build_commuter_info_form(
            CommuterInitialRequest(
                UnsafePassData(commuter_kind_code="UNSAFE")
            )
        )

    initial = CommuterInitialRequest(_pass_data())
    object.__setattr__(initial, "pass_data", object())
    with pytest.raises(TypeError):
        build_commuter_info_form(initial)


def test_price_fare_request_validates_typed_sources_and_no_raw_mapping():
    request = PriceFareQuoteRequest(legs=(_leg(),), menu_id="SECRET_MENU")
    assert "SECRET_MENU" not in repr(request)
    assert not hasattr(request, "raw")
    assert not hasattr(request.legs[0], "raw")
    with pytest.raises(ValueError):
        PriceFareQuoteRequest(legs=())
    with pytest.raises(ValueError):
        PriceFareQuoteRequest(legs=(_leg(), _leg(), _leg()))
    with pytest.raises(ValueError):
        PriceFareQuoteRequest(legs=(_leg(),), menu_id="")
    with pytest.raises(ValueError):
        PriceFareLeg(
            departure_station_code="D,1",
            arrival_station_code="A",
            run_date="20990101",
            train_no="1",
            goods_no="G",
            requested_seat_attribute_code="S",
            train_group_code="T",
            standing_train_classification_code="C",
        )


def test_r17_parser_preserves_all_fields_and_nullable_container(load_json_fixture):
    raw = load_json_fixture("gifticket_list_success.json")
    response = parse_gift_ticket_list_response(raw)
    assert response.raw is raw
    assert response.query_count == "1"
    assert response.next_query_no == "SYNTHETIC_NEXT"
    assert len(response.tickets) == 1
    assert response.tickets[0].ticket_id == "SYNTHETIC_TKID"
    assert "SYNTHETIC_TKID" not in repr(response)
    nullable = parse_gift_ticket_list_response(
        {
            "h_msg_cd": None,
            "h_msg_txt": None,
            "strResult": "SUCC",
            "gdList": None,
            "qryCnt": None,
            "qryNumNext": None,
        }
    )
    assert nullable.tickets == ()
    assert nullable.query_count is None
    with pytest.raises(KorailProtocolError):
        parse_gift_ticket_list_response(
            {**raw, "gdList": [{**raw["gdList"][0], "tkId": 1}]}
        )


@pytest.mark.parametrize(
    ("payload", "error_type"),
    [
        (
            {
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic session expired",
                "strResult": "FAIL",
            },
            KorailSessionExpiredError,
        ),
        (
            {
                "h_msg_cd": "SYNTHETIC.FAIL",
                "h_msg_txt": "synthetic failure",
                "strResult": "FAIL",
            },
            KorailAppError,
        ),
        (
            {
                "h_msg_cd": "WRC000288",
                "h_msg_txt": "synthetic warning",
                "strResult": "FAIL",
            },
            KorailAppError,
        ),
        (
            {
                "h_msg_cd": "SYNTHETIC.UNKNOWN",
                "h_msg_txt": "synthetic unknown",
                "strResult": "SUCCESS",
            },
            KorailProtocolError,
        ),
        (
            {
                "h_msg_cd": "SYNTHETIC.UNKNOWN",
                "h_msg_txt": "synthetic unknown",
                "strResult": "succ",
            },
            KorailProtocolError,
        ),
    ],
)
def test_r17_common_error_matrix_is_strict(payload, error_type):
    with pytest.raises(error_type):
        parse_gift_ticket_list_response(payload)


def test_r31_parser_requires_primitive_json_integers(load_json_fixture):
    raw = load_json_fixture("cmtr_info_success.json")
    response = parse_commuter_info_response(raw)
    assert response.raw is raw
    assert response.available_passenger_count_from == 1
    assert response.available_passenger_count_to == 4
    assert response.passenger_options[0].passenger_count_from == 1
    assert response.passenger_options[0].passenger_count_to == 2
    nullable = parse_commuter_info_response(
        {
            "h_msg_cd": None,
            "h_msg_txt": None,
            "strResult": "SUCC",
            "avlPrnbFrom": None,
            "avlPrnbTo": None,
            "psgList": None,
        }
    )
    assert nullable.available_passenger_count_from == 0
    assert nullable.available_passenger_count_to == 0
    assert nullable.passenger_options == ()
    for value in (True, 1.0, "1"):
        with pytest.raises(KorailProtocolError):
            parse_commuter_info_response({**raw, "avlPrnbFrom": value})


def test_r52_parser_preserves_response_order_and_nullable_rows(load_json_fixture):
    raw = load_json_fixture("price_2_fare_success.json")
    response = parse_price_fare_quote_response(raw)
    assert response.raw is raw
    assert [fare.journey_sequence for fare in response.fares] == [
        "1",
        "2",
        "1",
        "2",
    ]
    nullable = parse_price_fare_quote_response(
        {
            "h_msg_cd": None,
            "h_msg_txt": None,
            "strResult": "SUCC",
            "prcList": None,
        }
    )
    assert nullable.fares == ()
    with pytest.raises(KorailProtocolError):
        parse_price_fare_quote_response({**raw, "prcList": ["bad"]})


def test_removed_r17_fails_before_transport_or_dynapath():
    calls = []
    provider_calls = []

    def provider(context):
        provider_calls.append(context)
        raise AssertionError("R17 must not request DynaPath")

    def handler(request):
        calls.append(request)
        return httpx.Response(404, json={"message": "not found"})

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(jsessionid="SYNTHETIC")
    with pytest.raises(KorailProtocolError):
        client.http.post_form(R17_PATH, {"qryDvCd": "F", "qryVal": "E"})
    assert calls == []
    assert provider_calls == []


def test_r31_requires_session_before_transport():
    called = False

    def handler(_):
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailAuthError):
        client.get_commuter_info(CommuterInitialRequest(_pass_data()))
    assert called is False


def test_r52_uses_existing_conditional_dynapath_without_session(load_json_fixture):
    contexts = []
    requests = []
    raw = load_json_fixture("price_2_fare_success.json")

    def provider(context):
        contexts.append(context)
        return "SYNTHETIC_DYNAPATH"

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=raw)

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
        transport=httpx.MockTransport(handler),
    )
    result = client.get_price_fare_quote(
        PriceFareQuoteRequest(legs=(_leg(),))
    )
    assert len(result.fares) == 4
    assert len(contexts) == 1
    assert contexts[0].path == R52_PATH
    assert requests[0].headers[client.config.dynapath.header_name] == (
        "SYNTHETIC_DYNAPATH"
    )
    fields = parse_qsl(requests[0].content.decode(), keep_blank_values=True)
    assert fields[3:5] == [("txtMenuId", "11"), ("chtnDvCd", "1")]
    assert ("trnCnt", "1") in fields


def test_r52_dynapath_rejection_is_typed(load_json_fixture):
    raw = load_json_fixture("dynapath_403.json")

    def handler(_):
        return httpx.Response(
            403,
            headers={"DynaPath-Result": "-1"},
            json=raw,
        )

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(
                enabled=True,
                token_provider=lambda _: "TOKEN",
            )
        ),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailDynaPathError):
        client.get_price_fare_quote(
            PriceFareQuoteRequest(legs=(_leg(),))
        )
