"""Offline contract tests for the 승차권 변경 chain's three new reads.

* ``POST self.seatChgInfo.do``            (``TicketService.java:54-56``)
* ``POST research.tripChgOgtk.do``        (``ResearchService.java:61-63``)
* ``GET  myTicket.reqUpgradeSeat``        (``MyTicketService.java:23-24``)

Nothing here touches the network: every request is answered by an
``httpx.MockTransport`` handler, and every field name and constant asserted
below was read from the decompiled APK and re-checked in smali.
"""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints
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
    KorailProtocolError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    OriginalTicketInquiryResponse,
    SelfSeatChangeInfoResponse,
    SpecialRoomUpgradeQuoteResponse,
)
from korail_mobile_api.read_parsers import (
    parse_original_ticket_inquiry_response,
    parse_self_seat_change_info_response,
    parse_special_room_upgrade_quote_response,
)
from korail_mobile_api.read_payloads import (
    OriginalTicketReference,
    SelfSeatChangeInfoRequest,
    SpecialRoomUpgradeQuoteRequest,
    build_original_ticket_inquiry_form,
    build_self_seat_change_info_form,
    build_special_room_upgrade_quote_query,
)
from korail_mobile_api.redaction import (
    is_sensitive_key,
    redact_payload,
    redact_url,
    redact_value,
)
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_MUTATION_ROUTES,
    KORAIL_OPTIONAL_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
)


SEAT_CHANGE_PATH = "/classes/com.korail.mobile.self.seatChgInfo.do"
ORIGINAL_TICKET_PATH = "/classes/com.korail.mobile.research.tripChgOgtk.do"
UPGRADE_QUOTE_PATH = "/classes/com.korail.mobile.myTicket.reqUpgradeSeat"
# The purchase that follows the quote (MyTicketService.java:20-21). It must
# never become reachable through anything added here.
UPGRADE_PURCHASE_PATH = "/classes/com.korail.mobile.myTicket.procUpgradeSeat"

NEW_ROUTES = {
    ("POST", SEAT_CHANGE_PATH),
    ("POST", ORIGINAL_TICKET_PATH),
    ("GET", UPGRADE_QUOTE_PATH),
}


def _reference(suffix: str = "1") -> OriginalTicketReference:
    return OriginalTicketReference(
        sale_window_no=f"WINDOW_SECRET_{suffix}",
        sale_date=f"SALE_DATE_SECRET_{suffix}",
        sale_sequence=f"SALE_SEQUENCE_SECRET_{suffix}",
        return_password=f"RETURN_PASSWORD_SECRET_{suffix}",
    )


def _seat_change_request(
    room_class_code: str | None = "1",
) -> SelfSeatChangeInfoRequest:
    return SelfSeatChangeInfoRequest(
        run_date="20260801",
        train_no="00017",
        departure_station_code="0001",
        arrival_station_code="0015",
        room_class_code=room_class_code,
    )


def _upgrade_request(**overrides: Any) -> SpecialRoomUpgradeQuoteRequest:
    values: dict[str, Any] = {
        "original_ticket": _reference(),
        "journey_type_code": "1",
        "journey_sequence": "001",
        "departure_date": "20260801",
        "departure_construction_order": "000001",
        "departure_run_order": "000001",
        "departure_station_code": "0001",
        "departure_time": "070000",
        "arrival_date": "20260801",
        "arrival_construction_order": "000010",
        "arrival_run_order": "000010",
        "arrival_station_code": "0015",
        "arrival_time": "094500",
        "train_no": "00017",
        "run_date": "20260801",
        "room_classification_code": "1",
    }
    values.update(overrides)
    return SpecialRoomUpgradeQuoteRequest(**values)


def _success(**extra: Any) -> dict[str, Any]:
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": "SERVER_MESSAGE",
        "strResult": "SUCC",
        **extra,
    }


def _client(handler) -> KorailClient:
    def provider(*args: Any, **kwargs: Any) -> str:  # pragma: no cover
        raise AssertionError("DynaPath provider must not be invoked")

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(jsessionid="SESSION_SECRET")
    return client


# ---------------------------------------------------------------------------
# Route registration and boundary
# ---------------------------------------------------------------------------


def test_the_three_change_chain_routes_are_registered_reads_only():
    assert len(KORAIL_READ_ONLY_ROUTES) == 61
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    # The quote's paying sibling is in neither set, so no code path reaches it.
    assert ("GET", UPGRADE_PURCHASE_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert ("GET", UPGRADE_PURCHASE_PATH) not in KORAIL_MUTATION_ROUTES
    assert ("POST", UPGRADE_PURCHASE_PATH) not in KORAIL_MUTATION_ROUTES
    assert KORAIL_MUTATION_ROUTES.isdisjoint(NEW_ROUTES)
    # None of the three is a DynaPath-signed path.
    assert all(path not in DYNAPATH_ALLOWLIST_PATHS for _, path in NEW_ROUTES)


def test_exact_request_field_contracts_match_the_apk_declarations():
    # TicketService.java:54-56 / TicketService.smali:280-325.
    assert KORAIL_EXACT_REQUEST_FIELDS[SEAT_CHANGE_PATH] == {
        "Device",
        "Version",
        "Key",
        "runDt",
        "trnNo",
        "dptRsStnCd",
        "arvRsStnCd",
        "psrmClCd",
    }
    # ...of which only psrmClCd may be dropped (TCSOptionsActivity.java:135-138).
    assert KORAIL_OPTIONAL_REQUEST_FIELDS[SEAT_CHANGE_PATH] == {"psrmClCd"}

    # MyTicketService.java:23-24 / MyTicketService.smali:176-309. All 26 are
    # always sent, so nothing is optional here.
    assert KORAIL_EXACT_REQUEST_FIELDS[UPGRADE_QUOTE_PATH] == {
        "Device",
        "Version",
        "Key",
        "ogtkSaleDd",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "jrnyTpCd",
        "jrnySqno",
        "dptDt",
        "dptStnConsOrdr",
        "dptStnRunOrdr",
        "dptRsStnCd",
        "dptTm",
        "arvDt",
        "arvStnConsOrdr",
        "arvStnRunOrdr",
        "arvRsStnCd",
        "arvTm",
        "trnNo",
        "runDt",
        "trnGpCd",
        "roomClsfCd",
        "scarNo",
        "seatNo",
        "rqSeatAttCd",
    }
    assert len(KORAIL_EXACT_REQUEST_FIELDS[UPGRADE_QUOTE_PATH]) == 26
    assert UPGRADE_QUOTE_PATH not in KORAIL_OPTIONAL_REQUEST_FIELDS

    # ResearchService.java:61-63 — only the four fixed @Fields can be named.
    assert KORAIL_EXACT_REQUEST_FIELDS[ORIGINAL_TICKET_PATH] == {
        "Device",
        "Version",
        "Key",
        "tkCnt",
    }


def test_client_method_signatures_and_exports_are_exact():
    contracts = {
        "get_self_seat_change_info": (
            ["self", "request"],
            {
                "request": SelfSeatChangeInfoRequest,
                "return": SelfSeatChangeInfoResponse,
            },
        ),
        "get_special_room_upgrade_quote": (
            ["self", "request"],
            {
                "request": SpecialRoomUpgradeQuoteRequest,
                "return": SpecialRoomUpgradeQuoteResponse,
            },
        ),
        "get_original_ticket_inquiry": (
            ["self", "tickets", "ticket_count"],
            {
                "tickets": tuple[OriginalTicketReference, ...],
                "ticket_count": int | None,
                "return": OriginalTicketInquiryResponse,
            },
        ),
    }
    for method_name, (parameters, hints) in contracts.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == parameters
        assert get_type_hints(method) == hints

    for name in (
        "SelfSeatChangeInfoRequest",
        "SelfSeatChangeInfoResponse",
        "SelfSeatChangeStation",
        "SelfSeatChangeReason",
        "SpecialRoomUpgradeQuoteRequest",
        "SpecialRoomUpgradeQuoteResponse",
        "SpecialRoomUpgradeTicketInfo",
        "SpecialRoomUpgradeJourney",
        "OriginalTicket",
        "OriginalTicketInquiryResponse",
        "OriginalTicketJourney",
        "OriginalTicketSeat",
        "SELF_SEAT_CHANGE_ROOM_CLASS_CODES",
        "SPECIAL_ROOM_UPGRADE_QUOTE_OK_CODES",
    ):
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is not None


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def test_seat_change_form_is_the_apk_field_set_and_omits_a_null_room_class():
    with_class = build_self_seat_change_info_form(_seat_change_request("2"))
    assert with_class == {
        "runDt": "20260801",
        # NOT zero-padded here: TCSOptionsActivity.java:132 forwards h_trn_no
        # verbatim, unlike the seat-inventory builders.
        "trnNo": "00017",
        "dptRsStnCd": "0001",
        "arvRsStnCd": "0015",
        "psrmClCd": "2",
    }
    without_class = build_self_seat_change_info_form(
        _seat_change_request(None)
    )
    assert "psrmClCd" not in without_class
    # Both shapes clear the exact-field contract once the transport has added
    # the common three.
    for form in (with_class, without_class):
        assert_read_only_request_fields(
            SEAT_CHANGE_PATH,
            {"Device": "AD", "Version": "v", "Key": "k", **form},
        )


def test_seat_change_request_rejects_an_unevidenced_room_class():
    assert korail_mobile_api.SELF_SEAT_CHANGE_ROOM_CLASS_CODES == {"1", "2"}
    # K4/o.java:9 declares ALL ("전체", "9"), but TCSOptionsActivity's branch
    # never sends it.
    with pytest.raises(ValueError):
        _seat_change_request("9")
    with pytest.raises(ValueError):
        SelfSeatChangeInfoRequest(
            run_date="2026-08-01",
            train_no="00017",
            departure_station_code="0001",
            arrival_station_code="0015",
        )
    with pytest.raises(TypeError):
        build_self_seat_change_info_form({"runDt": "20260801"})


def test_upgrade_quote_query_matches_the_twenty_three_declared_parameters():
    query = build_special_room_upgrade_quote_query(_upgrade_request())
    assert query == {
        "ogtkSaleDd": "SALE_DATE_SECRET_1",
        "ogtkSaleWctNo": "WINDOW_SECRET_1",
        "ogtkSaleSqno": "SALE_SEQUENCE_SECRET_1",
        "ogtkRetPwd": "RETURN_PASSWORD_SECRET_1",
        "jrnyTpCd": "1",
        "jrnySqno": "001",
        "dptDt": "20260801",
        "dptStnConsOrdr": "000001",
        "dptStnRunOrdr": "000001",
        "dptRsStnCd": "0001",
        "dptTm": "070000",
        "arvDt": "20260801",
        "arvStnConsOrdr": "000010",
        "arvStnRunOrdr": "000010",
        "arvRsStnCd": "0015",
        "arvTm": "094500",
        "trnNo": "00017",
        "runDt": "20260801",
        # Hardcoded by the app (SpecialRoomUpgradeActivity.java:126) and
        # I4/a.AFTER_DEPARTURE = "15" (I4/a.smali:7).
        "trnGpCd": "100",
        "roomClsfCd": "1",
        "scarNo": "",
        "seatNo": "",
        "rqSeatAttCd": "15",
    }
    assert len(query) == 23
    assert_read_only_request_fields(
        UPGRADE_QUOTE_PATH,
        {"Device": "AD", "Version": "v", "Key": "k", **query},
    )
    with pytest.raises(TypeError):
        build_special_room_upgrade_quote_query(query)
    with pytest.raises(TypeError):
        _upgrade_request(original_ticket=("W", "D", "S", "P"))
    with pytest.raises(ValueError):
        _upgrade_request(departure_time="0700")


def test_original_ticket_form_indexes_groups_from_one_in_rortg_order():
    form = build_original_ticket_inquiry_form(
        (_reference("1"), _reference("2"))
    )
    assert form == (
        # int, not str: ResearchService.smali:613 declares tkCnt as I, while
        # the neighbouring tk.plfNo.do declares the same name as a String.
        ("tkCnt", 2),
        ("ogtkSaleWctNo_1", "WINDOW_SECRET_1"),
        ("ogtkSaleDd_1", "SALE_DATE_SECRET_1"),
        ("ogtkSaleSqno_1", "SALE_SEQUENCE_SECRET_1"),
        ("ogtkRetPwd_1", "RETURN_PASSWORD_SECRET_1"),
        ("ogtkSaleWctNo_2", "WINDOW_SECRET_2"),
        ("ogtkSaleDd_2", "SALE_DATE_SECRET_2"),
        ("ogtkSaleSqno_2", "SALE_SEQUENCE_SECRET_2"),
        ("ogtkRetPwd_2", "RETURN_PASSWORD_SECRET_2"),
    )
    assert type(form[0][1]) is int
    with pytest.raises(ValueError):
        build_original_ticket_inquiry_form(())
    with pytest.raises(TypeError):
        build_original_ticket_inquiry_form([_reference()])
    with pytest.raises(ValueError):
        build_original_ticket_inquiry_form((_reference(),), ticket_count=0)


def test_original_ticket_tkcnt_may_disagree_with_the_group_count():
    """The app itself disagrees; the contract must not over-pin.

    ``SeatSearchActivity.java:615`` hardcodes ``1`` while writing
    ``f29962H.size()`` rows and ``TCBookingActivity.java:179`` sends the
    passenger count, so requiring ``tkCnt == N`` would reject two of the app's
    own three call sites.
    """
    form = build_original_ticket_inquiry_form(
        (_reference("1"), _reference("2")),
        ticket_count=1,
    )
    assert form[0] == ("tkCnt", 1)
    assert_read_only_request_fields(
        ORIGINAL_TICKET_PATH,
        (("Device", "AD"), ("Version", "v"), ("Key", "k"), *form),
    )


def test_original_ticket_contract_rejects_malformed_indexed_shapes():
    prefix = (("Device", "AD"), ("Version", "v"), ("Key", "k"))
    good = build_original_ticket_inquiry_form((_reference(),))
    assert_read_only_request_fields(ORIGINAL_TICKET_PATH, (*prefix, *good))

    # tkCnt as a string is the exact string/number mismatch this route's smali
    # rules out.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (*prefix, ("tkCnt", "1"), *good[1:]),
        )
    # A group that starts at 2 rather than 1.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (
                *prefix,
                ("tkCnt", 1),
                ("ogtkSaleWctNo_2", "W"),
                ("ogtkSaleDd_2", "D"),
                ("ogtkSaleSqno_2", "S"),
                ("ogtkRetPwd_2", "P"),
            ),
        )
    # An incomplete group.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (*prefix, ("tkCnt", 1), *good[1:-1]),
        )
    # An unindexed extra field smuggled in beside the map.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (*prefix, *good, ("txtPnrNo", "PNR")),
        )
    # No tickets at all.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (*prefix, ("tkCnt", 1)),
        )
    # An empty credential value.
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            ORIGINAL_TICKET_PATH,
            (*prefix, ("tkCnt", 1), *good[1:-1], ("ogtkRetPwd_1", "")),
        )


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def test_seat_change_parser_reads_the_dao_shape_and_tolerates_numbers():
    parsed = parse_self_seat_change_info_response(
        _success(
            trnNo="00017",
            trnClsfCd="00",
            trnClsfNm="KTX",
            trnGpCd="100",
            trnGpNm="KTX",
            runDt="20260801",
            gnrmRsvPsbCd="Y",
            sprmRsvPsbCd="N",
            chgBfDptStnConsOrdr="000001",
            chgBfArvStnConsOrdr="000010",
            exsDptStnRunOrdr="000001",
            exsArvStnRunOrdr="000010",
            chgStnList=[
                {
                    "dptRsStnCd": "0001",
                    "dptRsStnNm": "서울",
                    "dptDt": "20260801",
                    "dptTm": "070000",
                    "arvDt": "20260801",
                    "arvTm": "094500",
                    "dptStnConsOrdr": "000001",
                    "dptStnRunOrdr": "000001",
                    # Sent as a bare JSON number, which Gson would have taken
                    # for the DAO's String.
                    "gnrmRestSeatNum": 12,
                    "sprmRestSeatNum": "003",
                }
            ],
            chgRsnList=[
                {
                    "qryCode": "01",
                    "qryOrdr": 1,
                    "frcSaleRsnCont": "좌석 변경",
                }
            ],
        )
    )
    assert type(parsed) is SelfSeatChangeInfoResponse
    assert parsed.train_no == "00017"
    assert parsed.general_reservation_possible_code == "Y"
    assert parsed.special_reservation_possible_code == "N"
    assert len(parsed.stations) == 1
    assert parsed.stations[0].general_remaining_seats == "12"
    assert parsed.stations[0].special_remaining_seats == "003"
    assert parsed.reasons[0].query_order == "1"
    assert parsed.reasons[0].reason_text == "좌석 변경"

    # Empty lists and a bare envelope are both fine.
    empty = parse_self_seat_change_info_response(_success())
    assert empty.stations == () and empty.reasons == ()

    with pytest.raises(KorailProtocolError):
        parse_self_seat_change_info_response("not a mapping")
    with pytest.raises(KorailAppError):
        parse_self_seat_change_info_response(
            {
                "h_msg_cd": "X",
                "h_msg_txt": "y",
                "strResult": "FAIL",
            }
        )
    with pytest.raises(KorailProtocolError):
        parse_self_seat_change_info_response(_success(chgStnList=["nope"]))


def test_upgrade_quote_parser_reads_the_price_and_the_settlement_target():
    parsed = parse_special_room_upgrade_quote_response(
        _success(
            ticketInfo={
                "custNm": "NAME_SECRET",
                # Integer.parseInt'd by the app, and seen both ways on the wire.
                "scnIndcAmt": 2400,
                "totFare": "59800",
            },
            jrnys=[{"lumpStlTgtNo": "TARGET_SECRET"}],
        )
    )
    assert type(parsed) is SpecialRoomUpgradeQuoteResponse
    assert parsed.ticket_info.screen_indicated_amount == "2400"
    assert parsed.ticket_info.total_fare == "59800"
    assert parsed.journeys[0].lump_settlement_target_no == "TARGET_SECRET"
    # The traveller's name is not promoted to a typed attribute.
    assert not hasattr(parsed.ticket_info, "customer_name")
    assert parsed.ticket_info.raw["custNm"] == "NAME_SECRET"
    # Neither secret may reach a repr.
    assert "TARGET_SECRET" not in repr(parsed)
    assert "NAME_SECRET" not in repr(parsed)

    missing = parse_special_room_upgrade_quote_response(_success())
    assert missing.ticket_info is None and missing.journeys == ()

    assert korail_mobile_api.SPECIAL_ROOM_UPGRADE_QUOTE_OK_CODES == {
        "IRT000000",
        "MRT200105",
    }
    with pytest.raises(KorailProtocolError):
        parse_special_room_upgrade_quote_response("not a mapping")
    with pytest.raises(KorailProtocolError):
        parse_special_room_upgrade_quote_response(_success(ticketInfo=[]))


def test_original_ticket_parser_reads_nested_journeys_and_seats():
    parsed = parse_original_ticket_inquiry_response(
        _success(
            orgTkList=[
                {
                    "pnrNo": "PNR_SECRET",
                    "tkKndCd": "01",
                    "ogtkSaleDt": "SALE_DATE_SECRET",
                    "ogtkSaleWctNo": "WINDOW_SECRET",
                    "ogtkSaleSqno": "SALE_SEQUENCE_SECRET",
                    "ogtkRetPwd": "RETURN_PASSWORD_SECRET",
                    "mbCrdNo": "MEMBER_CARD_SECRET",
                    "adulCnt": 1,
                    "chilCnt": "0",
                    "rcvdAmt": "59800",
                    "jrnyList": [
                        {
                            "jrnySqno": "001",
                            "jrnyTpCd": "1",
                            "trnNo": 17,
                            "trnGpCd": "100",
                            "dptDt": "20260801",
                            "dptTm": "070000",
                            "dptRsStnCd": "0001",
                            "dptRsStnNm": "서울",
                            "arvRsStnCd": "0015",
                            "psgNm": "NAME_SECRET",
                            "seatList": [
                                {
                                    "psgSqno": "1",
                                    "psrmClCd": "1",
                                    "scarNo": 3,
                                    "seatNo": "SEAT_SECRET",
                                    "rcvdFare": "59800",
                                }
                            ],
                        }
                    ],
                    # Left unparsed on purpose; still redacted inside raw.
                    "cmpnList": [{"dlayOgtkRetPwd": "DELAY_PWD_SECRET"}],
                    "stlList": [{"stlCrdNo": "CARD_SECRET"}],
                }
            ]
        )
    )
    assert type(parsed) is OriginalTicketInquiryResponse
    ticket = parsed.tickets[0]
    assert ticket.original_return_password == "RETURN_PASSWORD_SECRET"
    assert ticket.adult_count == "1"
    journey = ticket.journeys[0]
    assert journey.train_no == "17"
    assert journey.journey_sequence == "001"
    assert journey.seats[0].car_no == "3"
    assert journey.seats[0].seat_no == "SEAT_SECRET"
    for secret in (
        "RETURN_PASSWORD_SECRET",
        "PNR_SECRET",
        "SEAT_SECRET",
        "MEMBER_CARD_SECRET",
    ):
        assert secret not in repr(parsed)

    empty = parse_original_ticket_inquiry_response(_success())
    assert empty.tickets == ()

    with pytest.raises(KorailProtocolError):
        parse_original_ticket_inquiry_response("not a mapping")
    with pytest.raises(KorailProtocolError):
        parse_original_ticket_inquiry_response(_success(orgTkList=["nope"]))


# ---------------------------------------------------------------------------
# Redaction
# ---------------------------------------------------------------------------


def test_the_original_ticket_credential_is_redacted_in_every_spelling():
    # The bare @Query spelling the upgrade quote uses...
    assert is_sensitive_key("ogtkRetPwd")
    # ...the indexed @FieldMap spellings the 원표 lookup uses...
    for index in (1, 2, 9, 10):
        assert is_sensitive_key(f"ogtkRetPwd_{index}")
        assert is_sensitive_key(f"ogtkSaleWctNo_{index}")
        assert is_sensitive_key(f"ogtkSaleDd_{index}")
        assert is_sensitive_key(f"ogtkSaleSqno_{index}")
    # ...and the rest of the return-number tuple, which is worthless to mask
    # three quarters of.
    for key in (
        "ogtkSaleDd",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkSaleDt",
        "dlayOgtkRetPwd",
        "dlayOgtkSaleDt",
        "dlayOgtkSaleSqno",
        "dlayOgtkWctNo",
        "stlCrdNo",
        "prepCrdNo",
        "apvNo",
        "lumpStlTgtNo",
    ):
        assert is_sensitive_key(key), key
    # ...plus the model attribute names the parsers write them into.
    for attribute in (
        "original_return_password",
        "original_window_no",
        "original_sale_sequence",
        "original_sale_datetime",
        "lump_settlement_target_no",
    ):
        assert is_sensitive_key(attribute), attribute


def test_the_credential_never_survives_a_preview_of_either_request():
    form = dict(build_original_ticket_inquiry_form((_reference(),)))
    redacted_form = redact_payload(form)
    assert redacted_form["ogtkRetPwd_1"] == "[REDACTED]"
    assert redacted_form["ogtkSaleWctNo_1"] == "[REDACTED]"
    assert redacted_form["tkCnt"] == "1"

    # The upgrade quote is a GET, so the credential lands in a URL.
    query = build_special_room_upgrade_quote_query(_upgrade_request())
    url = httpx.URL(
        f"https://smart.letskorail.com{UPGRADE_QUOTE_PATH}",
        params=query,
    )
    redacted_url = redact_url(str(url))
    assert "RETURN_PASSWORD_SECRET_1" not in redacted_url
    assert "WINDOW_SECRET_1" not in redacted_url
    assert "SALE_SEQUENCE_SECRET_1" not in redacted_url
    assert "ogtkRetPwd=%5BREDACTED%5D" in redacted_url
    # A non-credential parameter still travels in the clear.
    assert "trnGpCd=100" in redacted_url


def test_the_credential_never_survives_a_parsed_response_either():
    parsed = parse_original_ticket_inquiry_response(
        _success(
            orgTkList=[
                {
                    "ogtkRetPwd": "RETURN_PASSWORD_SECRET",
                    "ogtkSaleWctNo": "WINDOW_SECRET",
                    "cmpnList": [{"dlayOgtkRetPwd": "DELAY_PWD_SECRET"}],
                    "stlList": [{"stlCrdNo": "CARD_SECRET", "apvNo": "APV"}],
                }
            ]
        )
    )
    redacted = redact_value(parsed)
    assert "RETURN_PASSWORD_SECRET" not in repr(redacted)
    assert "WINDOW_SECRET" not in repr(redacted)
    # ...including the parts left deliberately unparsed inside raw.
    assert "DELAY_PWD_SECRET" not in repr(redacted)
    assert "CARD_SECRET" not in repr(redacted)

    quote = parse_special_room_upgrade_quote_response(
        _success(jrnys=[{"lumpStlTgtNo": "TARGET_SECRET"}])
    )
    assert "TARGET_SECRET" not in repr(redact_value(quote))


# ---------------------------------------------------------------------------
# Client wiring
# ---------------------------------------------------------------------------


def test_client_sends_exactly_the_built_shapes_to_the_three_routes():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == UPGRADE_QUOTE_PATH:
            return httpx.Response(
                200,
                json=_success(
                    ticketInfo={"scnIndcAmt": "2400", "totFare": "59800"},
                    jrnys=[{"lumpStlTgtNo": "TARGET_SECRET"}],
                ),
            )
        if request.url.path == ORIGINAL_TICKET_PATH:
            return httpx.Response(
                200,
                json=_success(orgTkList=[{"pnrNo": "PNR_SECRET"}]),
            )
        return httpx.Response(
            200,
            json=_success(chgStnList=[{"dptRsStnCd": "0001"}]),
        )

    client = _client(handler)
    try:
        seat = client.get_self_seat_change_info(_seat_change_request())
        original = client.get_original_ticket_inquiry((_reference(),))
        quote = client.get_special_room_upgrade_quote(_upgrade_request())
    finally:
        client.close()

    assert type(seat) is SelfSeatChangeInfoResponse
    assert type(original) is OriginalTicketInquiryResponse
    assert type(quote) is SpecialRoomUpgradeQuoteResponse
    assert [request.method for request in seen] == ["POST", "POST", "GET"]
    assert [request.url.path for request in seen] == [
        SEAT_CHANGE_PATH,
        ORIGINAL_TICKET_PATH,
        UPGRADE_QUOTE_PATH,
    ]
    # No route signs a DynaPath header.
    assert all(
        "X-DynaPath-M-Token" not in request.headers for request in seen
    )

    seat_fields = parse_qsl(
        seen[0].content.decode("utf-8"),
        keep_blank_values=True,
    )
    assert dict(seat_fields)["psrmClCd"] == "1"
    assert dict(seat_fields)["trnNo"] == "00017"

    # The 원표 request keeps the builder's exact ORDER on the wire, which a
    # dict-valued form could not guarantee.
    original_fields = parse_qsl(
        seen[1].content.decode("utf-8"),
        keep_blank_values=True,
    )
    assert [name for name, _ in original_fields] == [
        "Device",
        "Version",
        "Key",
        "tkCnt",
        "ogtkSaleWctNo_1",
        "ogtkSaleDd_1",
        "ogtkSaleSqno_1",
        "ogtkRetPwd_1",
    ]
    assert dict(original_fields)["tkCnt"] == "1"

    quote_params = dict(parse_qsl(seen[2].url.query.decode("utf-8"),
                                  keep_blank_values=True))
    assert quote_params["ogtkRetPwd"] == "RETURN_PASSWORD_SECRET_1"
    assert quote_params["scarNo"] == "" and quote_params["seatNo"] == ""
    assert quote_params["rqSeatAttCd"] == "15"
    assert len(quote_params) == 26


def test_every_one_of_the_three_requires_a_session():
    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError("no request may leave without a session")

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    try:
        for call in (
            lambda: client.get_self_seat_change_info(_seat_change_request()),
            lambda: client.get_original_ticket_inquiry((_reference(),)),
            lambda: client.get_special_room_upgrade_quote(_upgrade_request()),
        ):
            with pytest.raises(KorailAuthError):
                call()
    finally:
        client.close()
