from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from typing import get_type_hints
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.parsers import (
    parse_train_rows,
    parse_train_search_metadata,
)
from korail_mobile_api.read_models import (
    CommuterInfoResponse,
    CommuterPassengerOption,
    GiftTicketListResponse,
    PassGoodsInfo,
    PassMenuItem,
    PassMenuData,
    PassPassengerInfos,
    PriceFareQuoteResponse,
    ProductTrainInquiryResponse,
)
from korail_mobile_api.read_parsers import (
    _PRODUCT_RECOMMENDATION_FIELDS,
    _PRODUCT_TRAIN_FIELDS,
    parse_commuter_info_response,
    parse_gift_ticket_list_response,
    parse_price_fare_quote_response,
    parse_product_train_inquiry_response,
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
    _ProductPassengerGroups,
    _ProductTrainInquiryContinuation,
    _ProductTrainInquiryRequest,
    _ProductTransferContext,
    _build_product_train_inquiry_form,
    build_commuter_info_form,
    build_gift_ticket_list_form,
    build_price_fare_quote_form,
)
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
    assert_read_only_route,
)


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
    assert len(KORAIL_READ_ONLY_ROUTES) == 51
    assert {("POST", R17_PATH), ("POST", R31_PATH), ("POST", R52_PATH)} <= KORAIL_READ_ONLY_ROUTES
    assert ("POST", R39_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert not hasattr(KorailClient, "get_product_train_inquiry")
    assert not hasattr(korail_mobile_api, "ProductTrainInquiryRequest")


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
        ("psgPrnb", "1"),
        ("psgPrnb", "2"),
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


def test_r52_one_and_two_leg_forms_omit_train_count():
    direct = build_price_fare_quote_form(
        PriceFareQuoteRequest(legs=(_leg(),))
    )
    transfer = build_price_fare_quote_form(
        PriceFareQuoteRequest(legs=(_leg("1"), _leg("2")))
    )
    assert direct[:2] == (("txtMenuId", "11"), ("chtnDvCd", "1"))
    assert transfer[:2] == (("txtMenuId", "11"), ("chtnDvCd", "2"))
    assert ("dptRsStnCd", "D1,D2") in transfer
    assert all(name != "trnCnt" for name, _ in direct + transfer)
    assert transfer == (
        ("txtMenuId", "11"),
        ("chtnDvCd", "2"),
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
    # Regression: the request used to require metadata.menu_id, parsed from
    # "h_menu_id" -- a key with ZERO hits across jadx and smali. Every request
    # built from an actually-parsed search response therefore raised, and
    # get_price_fare_quote was unreachable; only hand-forged
    # TrainSearchMetadata(menu_id="11") objects in this file kept it green.
    # This test drives the request from parsed server data only.
    raw = load_json_fixture("raw_typed_train_search.json")
    metadata = parse_train_search_metadata(raw)
    train = parse_train_rows(raw)[0]
    assert not hasattr(metadata, "menu_id")

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
        ("psgPrnb", "1"),
        ("psgPrnb", "2"),
    ]


def test_public_signatures_and_exports_are_closed():
    contracts = {
        "get_gift_ticket_list": GiftTicketListResponse,
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
    for held_back in (
        "ProductTrainInquiryRequest",
        "ProductTrainInquiryResponse",
    ):
        assert held_back not in korail_mobile_api.__all__
        assert not hasattr(korail_mobile_api, held_back)


def test_exact_safety_shapes_and_holdback_are_closed():
    assert R39_PATH in DYNAPATH_ALLOWLIST_PATHS
    assert R39_PATH not in KORAIL_EXACT_REQUEST_FIELDS
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", R39_PATH)

    assert_read_only_request_fields(
        R17_PATH,
        (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("qryDvCd", "F"),
            ("qryVal", "E"),
        ),
    )
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
            ("psgPrnb", "1"),
            ("psgPrnb", "2"),
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
            ("psgPrnb", "1"),
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


def test_r17_p058_clears_session_and_invalid_json_is_protocol_error():
    responses = [
        httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "expired",
                "strResult": "FAIL",
            },
        ),
        httpx.Response(200, content=b"not-json"),
    ]

    def handler(_):
        return responses.pop(0)

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="SYNTHETIC")
    with pytest.raises(KorailSessionExpiredError):
        client.get_gift_ticket_list(GiftTicketPaymentEligibilityRequest())
    assert client.session.current is None
    client.session.current = KorailSession(jsessionid="SYNTHETIC")
    with pytest.raises(KorailProtocolError):
        client.get_gift_ticket_list(GiftTicketPaymentEligibilityRequest())


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


def _product_item() -> PassMenuItem:
    return PassMenuItem(
        train_group_code="109",
        goods_data=PassGoodsInfo(
            h_cnd_flg_disc_no="SECRET_PRODUCT",
            psg_infos=PassPassengerInfos(h_min_cnt="1", h_max_cnt="9"),
        ),
    )


def _product_request(
    *,
    transfer=False,
    continuation=None,
) -> _ProductTrainInquiryRequest:
    context = (
        _ProductTransferContext("TRANSFER_STATION", "100")
        if transfer
        else None
    )
    return _ProductTrainInquiryRequest(
        product=_product_item(),
        departure_station_code="START",
        arrival_station_code="END",
        departure_date="20990101",
        departure_time="120000",
        passengers=_ProductPassengerGroups(1, 0, 0, 0, 0),
        transfer=context,
        continuation=continuation,
    )


def test_r39_offline_builder_is_exact_and_has_no_transport_surface():
    config = KorailConfig()
    initial = _build_product_train_inquiry_form(config, _product_request())
    direct_source = ProductTrainInquiryResponse(
        next_query_station_no="DIRECT_QUERY_STATION",
        result_count="7",
        next_train_no="DIRECT_NEXT_TRAIN",
    )
    direct_continuation = _ProductTrainInquiryContinuation.direct(
        direct_source
    )
    direct = _build_product_train_inquiry_form(
        config,
        _product_request(continuation=direct_continuation),
    )
    transfer_source = ProductTrainInquiryResponse(
        next_query_station_no="TRANSFER_QUERY_STATION",
        result_count="8",
        preceding_train_no_next="TRANSFER_PRECEDING_TRAIN",
        early_train_no_next="TRANSFER_EARLY_TRAIN",
    )
    transfer_continuation = _ProductTrainInquiryContinuation.transfer(
        transfer_source
    )
    transfer = _build_product_train_inquiry_form(
        config,
        _product_request(
            transfer=True,
            continuation=transfer_continuation,
        ),
    )
    common = (
        ("Device", config.device),
        ("Version", config.version),
        ("txtMenuId", "41"),
        ("radJobId", "1"),
        ("selGoTrain", "109"),
        ("txtTrnGpCd", "109"),
        ("txtGoStart", "START"),
        ("txtGoEnd", "END"),
        ("txtGoAbrdDt", "20990101"),
        ("txtGoHour", "120000"),
        ("txtPsgFlg_1", "1"),
        ("txtPsgFlg_2", "0"),
        ("txtPsgFlg_3", "0"),
        ("txtPsgFlg_4", "0"),
        ("txtPsgFlg_5", "0"),
        ("txtSeatAttCd_2", "000"),
        ("txtSeatAttCd_3", "000"),
        ("txtSeatAttCd_4", "015"),
        ("txtGdNo", "SECRET_PRODUCT"),
        ("qryDvCd", "1"),
    )
    assert initial == common + (
        ("qryStNo", "0"),
        ("qryStTrnNo", "00000"),
        ("qryStTrnNo2", ""),
        ("pgPrCnt", "10"),
    )
    assert direct == common + (
        ("qryStNo", "DIRECT_QUERY_STATION"),
        ("qryStTrnNo", "DIRECT_NEXT_TRAIN"),
        ("qryStTrnNo2", ""),
        ("pgPrCnt", "7"),
    )
    assert transfer == (
        *common[:3],
        ("radJobId", "2"),
        *common[4:],
        ("qryStNo", "TRANSFER_QUERY_STATION"),
        ("qryStTrnNo", "TRANSFER_PRECEDING_TRAIN"),
        ("qryStTrnNo2", "TRANSFER_EARLY_TRAIN"),
        ("pgPrCnt", "8"),
        ("chtnCnt", "1"),
        ("chtnRsStnCd1", "TRANSFER_STATION"),
        ("trnGpCnt", "1"),
        ("trnGpCd1", "100"),
    )
    for form in (initial, direct, transfer):
        assert all(name not in {"Key", "Sid"} for name, _ in form)
        assert ("qryDvCd", "1") in form
    assert "DIRECT_QUERY_STATION" not in repr(direct_continuation)
    assert "TRANSFER_QUERY_STATION" not in repr(transfer_continuation)
    assert "SECRET_PRODUCT" not in repr(_product_request())


def test_r39_continuation_requires_exact_complete_response_provenance():
    with pytest.raises(TypeError):
        _ProductTrainInquiryContinuation.direct(object())

    class UnsafeResponse(ProductTrainInquiryResponse):
        pass

    with pytest.raises(TypeError):
        _ProductTrainInquiryContinuation.direct(
            UnsafeResponse(
                next_query_station_no="Q",
                result_count="1",
                next_train_no="T",
            )
        )

    for source in (
        ProductTrainInquiryResponse(
            next_query_station_no=None,
            result_count="1",
            next_train_no="T",
        ),
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count=None,
            next_train_no="T",
        ),
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count="1",
            next_train_no=None,
        ),
    ):
        with pytest.raises(ValueError):
            _ProductTrainInquiryContinuation.direct(source)

    for source in (
        ProductTrainInquiryResponse(
            next_query_station_no=None,
            result_count="1",
            preceding_train_no_next="P",
            early_train_no_next="E",
        ),
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count=None,
            preceding_train_no_next="P",
            early_train_no_next="E",
        ),
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count="1",
            preceding_train_no_next=None,
            early_train_no_next="E",
        ),
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count="1",
            preceding_train_no_next="P",
            early_train_no_next=None,
        ),
    ):
        with pytest.raises(ValueError):
            _ProductTrainInquiryContinuation.transfer(source)

    source = ProductTrainInquiryResponse(
        next_query_station_no="Q",
        result_count="1",
        next_train_no="T",
    )
    continuation = _ProductTrainInquiryContinuation.direct(source)
    object.__setattr__(source, "next_train_no", None)
    with pytest.raises(ValueError):
        _build_product_train_inquiry_form(
            KorailConfig(),
            _product_request(continuation=continuation),
        )


def test_r39_continuation_mode_must_match_selected_request_mode():
    direct = _ProductTrainInquiryContinuation.direct(
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count="1",
            next_train_no="T",
        )
    )
    transfer = _ProductTrainInquiryContinuation.transfer(
        ProductTrainInquiryResponse(
            next_query_station_no="Q",
            result_count="1",
            preceding_train_no_next="P",
            early_train_no_next="E",
        )
    )
    with pytest.raises(ValueError):
        _build_product_train_inquiry_form(
            KorailConfig(),
            _product_request(continuation=transfer),
        )
    with pytest.raises(ValueError):
        _build_product_train_inquiry_form(
            KorailConfig(),
            _product_request(transfer=True, continuation=direct),
        )


def test_r39_offline_parser_preserves_nested_shape_and_errors(load_json_fixture):
    raw = load_json_fixture("product_train_inquiry_success.json")
    response = parse_product_train_inquiry_response(raw)
    assert isinstance(response, ProductTrainInquiryResponse)
    assert response.raw is raw
    assert response.merge_reservation_possible_flag == "N"
    assert len(response.trains) == 1
    train = response.trains[0]
    train_raw = raw["trn_infos"]["trn_info"][0]
    assert train.raw is train_raw
    for attribute, wire_name in _PRODUCT_TRAIN_FIELDS.items():
        assert getattr(train, attribute) == train_raw[wire_name]
    assert train.total_passenger_count == 1
    assert train.train_no == "SYNTHETIC_H_TRN_NO"
    assert train.recommendations[0].goods_no == "SYNTHETIC_GDNO"
    recommendation = train.recommendations[0]
    assert recommendation.raw is train_raw["rcmdGdList"][0]
    for attribute, wire_name in _PRODUCT_RECOMMENDATION_FIELDS.items():
        assert getattr(recommendation, attribute) == recommendation.raw[wire_name]
    assert "SYNTHETIC_H_TRN_NO" not in repr(response)

    nullable = parse_product_train_inquiry_response(
        {
            "h_msg_cd": None,
            "h_msg_txt": None,
            "strResult": "SUCC",
            "trn_infos": None,
        }
    )
    assert nullable.trains == ()
    assert nullable.merge_reservation_possible_flag is None
    with pytest.raises(KorailProtocolError):
        parse_product_train_inquiry_response(
            {
                **raw,
                "trn_infos": {
                    **raw["trn_infos"],
                    "trn_info": [
                        {**raw["trn_infos"]["trn_info"][0], "totPsgCnt": True}
                    ],
                },
            }
        )
    for malformed in (
        {**raw, "trn_infos": []},
        {
            **raw,
            "trn_infos": {
                **raw["trn_infos"],
                "trn_info": ["bad"],
            },
        },
        {
            **raw,
            "trn_infos": {
                **raw["trn_infos"],
                "trn_info": [
                    {**train_raw, "h_trn_no": 1}
                ],
            },
        },
        {
            **raw,
            "trn_infos": {
                **raw["trn_infos"],
                "trn_info": [
                    {**train_raw, "rcmdGdList": ["bad"]}
                ],
            },
        },
    ):
        with pytest.raises(KorailProtocolError):
            parse_product_train_inquiry_response(malformed)
    with pytest.raises(KorailAppError) as caught:
        parse_product_train_inquiry_response(
            {
                "h_msg_cd": "S134",
                "h_msg_txt": "pnrNo=SECRET_PRODUCT_FAILURE",
                "strResult": "FAIL",
            }
        )
    assert caught.value.code == "S134"
    assert "SECRET_PRODUCT_FAILURE" not in repr(caught.value)


def test_r17_404_is_one_transport_error_without_dynapath_or_retry():
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
    with pytest.raises(KorailTransportError):
        client.get_gift_ticket_list(GiftTicketPaymentEligibilityRequest())
    assert len(calls) == 1
    assert provider_calls == []


def test_r17_client_emits_exact_history_and_payment_sequences(load_json_fixture):
    requests = []
    raw = load_json_fixture("gifticket_list_success.json")

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=raw)

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="SYNTHETIC")
    client.get_gift_ticket_list(
        GiftTicketHistoryRequest.sent("20990101", "20991231")
    )
    client.get_gift_ticket_list(GiftTicketPaymentEligibilityRequest())
    common = [
        ("Device", client.config.device),
        ("Version", client.config.version),
        ("Key", client.config.key),
    ]
    assert parse_qsl(
        requests[0].content.decode(), keep_blank_values=True
    ) == common + [
        ("qryDvCd", "A"),
        ("qryVal", "E"),
        ("abrdDtFrom", "20990101"),
        ("abrdDtTo", "20991231"),
        ("usePsbFlg", ""),
    ]
    assert parse_qsl(
        requests[1].content.decode(), keep_blank_values=True
    ) == common + [("qryDvCd", "F"), ("qryVal", "E")]


def test_r17_and_r31_require_session_before_transport():
    called = False

    def handler(_):
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailAuthError):
        client.get_gift_ticket_list(GiftTicketPaymentEligibilityRequest())
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
    assert all(name != "trnCnt" for name, _ in fields)


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
