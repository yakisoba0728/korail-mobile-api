"""Offline regressions for response shapes observed on the LIVE KORAIL server.

Every fixture and assertion here was derived from a real response captured by
``scripts/capture_live_read_surface.py`` against a real account, then redacted:
personal data is replaced with obviously-synthetic values while the SHAPE (which
keys exist, which are absent, how values are typed and padded) is preserved
exactly as the server sent it.

These cases exist because the pre-existing fixtures encoded a shape the live
server does not actually use, so the parsers passed offline and failed live.
"""

from __future__ import annotations

import copy

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    PassAvailabilityResponse,
    PassMenuResponse,
)
from korail_mobile_api.read_parsers import (
    parse_pass_availability_response,
    parse_pass_menu_response,
)
from korail_mobile_api.read_payloads import (
    OriginalTicketReference,
    TicketReservationDetailRequest,
)

PASS_MENU_PATH = "/classes/com.korail.mobile.pass.passMenu.do"
PASS_INFO_LIST_PATH = "/classes/com.korail.mobile.pass.passInfoList"
COMMUTER_KIND_MENU_PATH = "/classes/com.korail.mobile.push.cmtrKnd.do"
GUIDE_SEAT_CONDITION_PATH = (
    "/classes/com.korail.mobile.reservation.guideSeatCnd.do"
)


def _client(handler) -> KorailClient:
    return KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )


def _authenticated(client: KorailClient) -> None:
    client.session.current = KorailSession(
        jsessionid="synthetic-session-secret",
        member_no="synthetic-member-secret",
    )


# --------------------------------------------------------------------------
# pass.passMenu.do -- a live SUCCESS carries no h_msg_cd/h_msg_txt at all.
# --------------------------------------------------------------------------


def test_pass_menu_parses_live_result_only_success(load_json_fixture):
    raw = load_json_fixture("pass_menu_live_result_only_success.json")
    assert "h_msg_cd" not in raw
    assert "h_msg_txt" not in raw
    assert raw["strResult"] == "SUCC"

    result = parse_pass_menu_response(raw)

    assert isinstance(result, PassMenuResponse)
    assert result.h_msg_cd is None
    assert result.h_msg_txt is None
    assert result.str_result == "SUCC"
    assert len(result.items) == 2
    assert result.items[0].item_id == "SYNTHETIC-CATEGORY-ID"
    assert result.items[0].goods_data is None


def test_pass_menu_coerces_zero_padded_passenger_counts(load_json_fixture):
    raw = load_json_fixture("pass_menu_live_result_only_success.json")
    padded = raw["list"][1]["goodsData"]["psg_infos"]["psg_info"][0]
    assert padded["h_st_prnb"] == "000001"
    assert padded["h_cls_prnb"] == "000009"

    passenger = (
        parse_pass_menu_response(raw)
        .items[1]
        .goods_data.psg_infos.psg_info[0]
    )

    assert passenger.h_st_prnb == 1
    assert passenger.h_cls_prnb == 9


def test_pass_menu_still_rejects_a_result_only_failure(load_json_fixture):
    raw = copy.deepcopy(
        load_json_fixture("pass_menu_live_result_only_success.json")
    )
    raw["strResult"] = "FAIL"
    with pytest.raises(KorailProtocolError):
        parse_pass_menu_response(raw)


def test_get_pass_menu_accepts_the_live_success_body(load_json_fixture):
    body = load_json_fixture("pass_menu_live_result_only_success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == PASS_MENU_PATH
        return httpx.Response(200, json=body)

    client = _client(handler)
    _authenticated(client)
    result = client.get_pass_menu("1")
    assert isinstance(result, PassMenuResponse)
    assert len(result.items) == 2


def test_get_pass_menu_still_raises_on_an_expired_session():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "synthetic logout",
                "strResult": "FAIL",
            },
        )

    client = _client(handler)
    _authenticated(client)
    with pytest.raises(KorailSessionExpiredError):
        client.get_pass_menu("1")
    assert client.session.current is None


# --------------------------------------------------------------------------
# pass.passInfoList -- a live SUCCESS nests its code under main_info.
# --------------------------------------------------------------------------


def test_pass_available_dates_parses_live_nested_code_success(
    load_json_fixture,
):
    raw = load_json_fixture(
        "pass_available_dates_live_result_only_success.json"
    )
    assert "h_msg_cd" not in raw
    assert raw["main_info"]["h_msg_cd"] == "SYNTHETIC-NESTED-CODE"

    result = parse_pass_availability_response(raw)

    assert isinstance(result, PassAvailabilityResponse)
    assert result.h_msg_cd is None
    assert result.str_result == "SUCC"
    assert result.open_dates == ()
    assert result.ticket_issue_dates == ()
    assert len(result.offices) == 2
    assert result.offices[0].code == "SYNTHETIC-OFFICE-CODE"
    assert result.offices[0].display_name == "Synthetic Office"


def test_get_pass_available_dates_accepts_the_live_success_body(
    load_json_fixture,
):
    body = load_json_fixture(
        "pass_available_dates_live_result_only_success.json"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == PASS_INFO_LIST_PATH
        return httpx.Response(200, json=body)

    client = _client(handler)
    _authenticated(client)
    result = client.get_pass_available_dates("1", "1", "1")
    assert isinstance(result, PassAvailabilityResponse)
    assert len(result.offices) == 2


# --------------------------------------------------------------------------
# The three reference-derived reads -- LIVE-VERIFIED ERROR SHAPES.
#
# All three routes were called once against the live server on 2026-07-26 with
# an account holding zero reservations. Every one was ACCEPTED (HTTP 200, no
# DynaPath rejection, no transport error) and answered with a bare three-key
# FAIL envelope -- h_msg_cd / strResult / h_msg_txt and NOTHING else. The
# fixtures below are those bodies byte-for-byte; they carry no personal data,
# so nothing needed redacting.
#
# Each code proves the server parsed the field it complains about, which is the
# evidence that the request shapes are right:
#   WRG200018 입력값오류(PNR번호)      <- hidPnrNo was read and rejected
#   WRT100002 창구번호미입력,미승인창구 <- h_orgtk_wct_no was read and rejected
#   WRT100124 반환번호를 확인해주세요   <- the return-number tuple was read
#
# The SUCCESS bodies remain UNVERIFIED: producing one requires a real held or
# paid ticket, which this increment cannot create.
# --------------------------------------------------------------------------

TICKET_RESERVATION_DETAIL_PATH = (
    "/classes/com.korail.mobile.certification.ReservationList"
)
REFUND_COMMISSION_PATH = "/classes/com.korail.mobile.refunds.CommissionView"
REFUND_TICKET_DETAIL_PATH = "/classes/com.korail.mobile.refunds.SelTicketInfo"

_LIVE_ERROR_FIXTURES = (
    (
        "ticket_reservation_detail_live_unknown_pnr_fail.json",
        "WRG200018",
        "입력값오류(PNR번호)",
    ),
    (
        "refund_ticket_detail_live_unknown_ticket_fail.json",
        "WRT100002",
        "창구번호미입력,미승인창구",
    ),
    (
        "refund_commission_live_unknown_ticket_fail.json",
        "WRT100124",
        "반환번호를 확인해주세요",
    ),
)


@pytest.mark.parametrize(
    ("fixture_name", "code", "message"),
    _LIVE_ERROR_FIXTURES,
)
def test_reference_derived_reads_live_failures_are_bare_three_key_envelopes(
    load_json_fixture,
    fixture_name,
    code,
    message,
):
    raw = load_json_fixture(fixture_name)
    # The live FAIL body carries the envelope and nothing else -- no partial
    # payload, no empty containers to mistake for "no rows".
    assert sorted(raw) == ["h_msg_cd", "h_msg_txt", "strResult"]
    assert raw["strResult"] == "FAIL"
    assert raw["h_msg_cd"] == code
    assert raw["h_msg_txt"] == message


@pytest.mark.parametrize(
    ("path", "fixture_name", "code"),
    [
        (
            TICKET_RESERVATION_DETAIL_PATH,
            "ticket_reservation_detail_live_unknown_pnr_fail.json",
            "WRG200018",
        ),
        (
            REFUND_TICKET_DETAIL_PATH,
            "refund_ticket_detail_live_unknown_ticket_fail.json",
            "WRT100002",
        ),
        (
            REFUND_COMMISSION_PATH,
            "refund_commission_live_unknown_ticket_fail.json",
            "WRT100124",
        ),
    ],
)
def test_reference_derived_reads_surface_the_live_failure_as_korail_app_error(
    load_json_fixture,
    path,
    fixture_name,
    code,
):
    """The observed live behaviour, end to end through the client.

    Each call raised exactly this, with exactly this code, on the live pass.
    """
    body = load_json_fixture(fixture_name)

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == path
        return httpx.Response(200, json=body)

    client = _client(handler)
    _authenticated(client)
    client.session.current = KorailSession(
        jsessionid="synthetic-session-secret",
        member_no="synthetic-member-secret",
        customer_no="synthetic-customer-secret",
    )
    ticket = OriginalTicketReference(
        sale_window_no="synthetic-window",
        sale_date="20260101",
        sale_sequence="synthetic-sequence",
        return_password="synthetic-password",
    )
    operations = {
        TICKET_RESERVATION_DETAIL_PATH: lambda: (
            client.get_ticket_reservation_detail(
                TicketReservationDetailRequest("synthetic-pnr")
            )
        ),
        REFUND_TICKET_DETAIL_PATH: lambda: client.get_refund_ticket_detail(
            ticket
        ),
        REFUND_COMMISSION_PATH: lambda: client.get_refund_commission(ticket),
    }
    with pytest.raises(KorailAppError) as excinfo:
        operations[path]()
    assert excinfo.value.code == code
    # The account state that made these failures the only reachable shape.
    assert client.session.current is not None
