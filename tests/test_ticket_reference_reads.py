from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError
from typing import Any, get_type_hints
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
import korail_mobile_api.read_models as read_models
import korail_mobile_api.read_payloads as read_payloads
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    DeliveryRecipientResponse,
    PbpAcceptanceSpecificationResponse,
    PlatformNumberResponse,
    RecentDeliveryHistoryResponse,
    TicketDuplicationCheckResponse,
)
from korail_mobile_api.read_parsers import (
    parse_delivery_recipient_response,
    parse_pbp_acceptance_specification_response,
    parse_platform_number_response,
    parse_recent_delivery_history_response,
    parse_ticket_duplication_check_response,
)
from korail_mobile_api.read_payloads import (
    OriginalTicketReference,
    TicketDuplicationCheckRequest,
    build_delivery_recipient_form,
    build_pbp_acceptance_specification_form,
    build_platform_number_form,
    build_recent_delivery_history_form,
    build_ticket_duplication_check_form,
)
from korail_mobile_api.redaction import redact_mapping, redact_text
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
)


R137_PATH = "/classes/com.korail.mobile.tk.dlvRcvCust.do"
R138_PATH = "/classes/com.korail.mobile.ticket.ticketDupCheck.do"
R146_PATH = "/classes/com.korail.mobile.tk.pbpAcepSpec.do"
R148_PATH = "/classes/com.korail.mobile.tk.plfNo.do"
R149_PATH = "/classes/com.korail.mobile.tk.rcntDlvHst.do"

NEW_ROUTES = {
    ("POST", R137_PATH),
    ("POST", R138_PATH),
    ("POST", R146_PATH),
    ("POST", R148_PATH),
    ("POST", R149_PATH),
}


def _reference(suffix: str = "1") -> OriginalTicketReference:
    return OriginalTicketReference(
        sale_window_no=f"WINDOW_SECRET_{suffix}",
        sale_date=f"SALE_DATE_SECRET_{suffix}",
        sale_sequence=f"SALE_SEQUENCE_SECRET_{suffix}",
        return_password=f"RETURN_PASSWORD_SECRET_{suffix}",
    )


def _success(**extra: Any) -> dict[str, Any]:
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": "SERVER_MESSAGE_SECRET",
        "strResult": "SUCC",
        **extra,
    }


def _responses() -> dict[str, dict[str, Any]]:
    return {
        R137_PATH: _success(
            acepCustMgNo="CUSTOMER_SECRET",
            acepCustNm="NAME_SECRET",
            acepCustTeln="PHONE_SECRET",
            mbCrdNo="CARD_SECRET",
        ),
        R138_PATH: _success(rsvCnt=2),
        R146_PATH: _success(
            tkList=[
                {
                    "pnrNo": "PNR_SECRET",
                    "saleDt": "SALE_DATE_SECRET",
                    "saleSqno": "SALE_SEQUENCE_SECRET",
                    "saleWctNo": "SALE_WINDOW_SECRET",
                    "tkRetPwd": "RETURN_PASSWORD_SECRET",
                    "jrnyList": [
                        {
                            "acepCustNm": "NAME_SECRET",
                            "acepCustTeln": "PHONE_SECRET",
                            "jrnyTpCd": "JOURNEY_TYPE_SECRET",
                            "mbDvNm": "MEMBER_DIVISION_SECRET",
                            "pbpAcepKndNm": "ACCEPTANCE_KIND_SECRET",
                            "pbpRsvNo": "RESERVATION_SECRET",
                            "regDt": "REGISTERED_DATE_SECRET",
                            "wdrwPsbFlg": "WITHDRAW_FLAG_SECRET",
                            "seatList": [
                                {
                                    "psgTpDvNm": "PASSENGER_SECRET",
                                    "psrmClCd": "ROOM_CODE_SECRET",
                                    "psrmClNm": "ROOM_NAME_SECRET",
                                    "scarNo": 3,
                                    "seatNo": "SEAT_SECRET",
                                }
                            ],
                        }
                    ],
                }
            ]
        ),
        R148_PATH: _success(
            tkList=[
                {
                    "saleDt": "SALE_DATE_SECRET",
                    "saleSqno": "SALE_SEQUENCE_SECRET",
                    "saleWctNo": "SALE_WINDOW_SECRET",
                    "tkRetNo": "TICKET_RETURN_SECRET",
                    "tkRetPwd": "RETURN_PASSWORD_SECRET",
                    "jrnyList": [{"plfNo": "PLATFORM_SECRET"}],
                }
            ]
        ),
        R149_PATH: _success(
            acepList=[
                {
                    "acepCustMgFlg": "CUSTOMER_FLAG_SECRET",
                    "acepCustMgNo": "CUSTOMER_SECRET",
                    "acepCustNm": "NAME_SECRET",
                    "acepCustTeln": "PHONE_SECRET",
                    "acepCustTeln2": "PHONE_2_SECRET",
                    "mbCrdNo": "CARD_SECRET",
                }
            ]
        ),
    }


def test_route_method_export_and_dynapath_boundaries_are_exact():
    assert len(KORAIL_READ_ONLY_ROUTES) == 60
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    assert len(DYNAPATH_ALLOWLIST_PATHS) == 6
    assert all(path not in DYNAPATH_ALLOWLIST_PATHS for _, path in NEW_ROUTES)

    expected_fields = {
        R137_PATH: {
            "Device",
            "Version",
            "Key",
            "saleWctNo",
            "saleDt",
            "saleSqno",
            "tkRetPwd",
        },
        R138_PATH: {"Device", "Version", "Key", "pnrNo"},
        R146_PATH: {"Device", "Version", "Key", "tkCnt", "tkRetNo"},
        R148_PATH: {"Device", "Version", "Key", "tkCnt", "tkRetNo"},
        R149_PATH: {"Device", "Version", "Key", "custMgNo"},
    }
    for path, fields in expected_fields.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == fields

    contracts = {
        "get_delivery_recipient": (
            ["self", "ticket"],
            {
                "ticket": OriginalTicketReference,
                "return": DeliveryRecipientResponse,
            },
        ),
        "check_ticket_duplication": (
            ["self", "request"],
            {
                "request": TicketDuplicationCheckRequest,
                "return": TicketDuplicationCheckResponse,
            },
        ),
        "get_pbp_acceptance_specifications": (
            ["self", "tickets"],
            {
                "tickets": tuple[OriginalTicketReference, ...],
                "return": PbpAcceptanceSpecificationResponse,
            },
        ),
        "get_platform_numbers": (
            ["self", "tickets"],
            {
                "tickets": tuple[OriginalTicketReference, ...],
                "return": PlatformNumberResponse,
            },
        ),
        "get_recent_delivery_history": (
            ["self"],
            {"return": RecentDeliveryHistoryResponse},
        ),
    }
    for method_name, (parameters, hints) in contracts.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == parameters
        assert get_type_hints(method) == hints

    public_methods = {
        name
        for name, value in inspect.getmembers(
            KorailClient,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    }
    assert len(public_methods) == 77

    expected_exports = {
        "TicketDuplicationCheckRequest": (
            read_payloads.TicketDuplicationCheckRequest
        ),
        "DeliveryRecipientResponse": read_models.DeliveryRecipientResponse,
        "TicketDuplicationCheckResponse": (
            read_models.TicketDuplicationCheckResponse
        ),
        "PbpAcceptanceSeat": read_models.PbpAcceptanceSeat,
        "PbpAcceptanceJourney": read_models.PbpAcceptanceJourney,
        "PbpAcceptanceTicket": read_models.PbpAcceptanceTicket,
        "PbpAcceptanceSpecificationResponse": (
            read_models.PbpAcceptanceSpecificationResponse
        ),
        "PlatformNumberJourney": read_models.PlatformNumberJourney,
        "PlatformNumberTicket": read_models.PlatformNumberTicket,
        "PlatformNumberResponse": read_models.PlatformNumberResponse,
        "RecentDeliveryRecipient": read_models.RecentDeliveryRecipient,
        "RecentDeliveryHistoryResponse": (
            read_models.RecentDeliveryHistoryResponse
        ),
    }
    for name, expected in expected_exports.items():
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is expected


def test_exact_builders_preserve_wire_order_duplicate_fields_and_count_types():
    first = _reference("1")
    second = _reference("2")
    assert build_delivery_recipient_form(first) == {
        "saleWctNo": first.sale_window_no,
        "saleDt": first.sale_date,
        "saleSqno": first.sale_sequence,
        "tkRetPwd": first.return_password,
    }
    pnr_request = TicketDuplicationCheckRequest("PNR_SECRET")
    assert build_ticket_duplication_check_form(pnr_request) == {
        "pnrNo": "PNR_SECRET"
    }
    assert build_pbp_acceptance_specification_form((first, second)) == (
        ("tkCnt", 2),
        (
            "tkRetNo",
            "WINDOW_SECRET_1-SALE_DATE_SECRET_1-"
            "SALE_SEQUENCE_SECRET_1-RETURN_PASSWORD_SECRET_1",
        ),
        (
            "tkRetNo",
            "WINDOW_SECRET_2-SALE_DATE_SECRET_2-"
            "SALE_SEQUENCE_SECRET_2-RETURN_PASSWORD_SECRET_2",
        ),
    )
    assert build_platform_number_form((first, second)) == (
        ("tkCnt", "2"),
        (
            "tkRetNo",
            "WINDOW_SECRET_1-SALE_DATE_SECRET_1-"
            "SALE_SEQUENCE_SECRET_1-RETURN_PASSWORD_SECRET_1",
        ),
        (
            "tkRetNo",
            "WINDOW_SECRET_2-SALE_DATE_SECRET_2-"
            "SALE_SEQUENCE_SECRET_2-RETURN_PASSWORD_SECRET_2",
        ),
    )
    assert build_recent_delivery_history_form("CUSTOMER_SECRET") == {
        "custMgNo": "CUSTOMER_SECRET"
    }


def test_request_provenance_is_exact_revalidated_and_repr_hidden():
    ticket = _reference()
    pnr = TicketDuplicationCheckRequest("PNR_SECRET")
    assert "SECRET" not in repr(ticket)
    assert "SECRET" not in repr(pnr)
    with pytest.raises(FrozenInstanceError):
        pnr.pnr_no = "CHANGED"

    class TicketSubclass(OriginalTicketReference):
        pass

    class PnrSubclass(TicketDuplicationCheckRequest):
        pass

    for invalid in ([], (), (ticket, object()), (TicketSubclass("W", "D", "S", "P"),)):
        with pytest.raises((TypeError, ValueError)):
            build_pbp_acceptance_specification_form(invalid)  # type: ignore[arg-type]
        with pytest.raises((TypeError, ValueError)):
            build_platform_number_form(invalid)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build_delivery_recipient_form(TicketSubclass("W", "D", "S", "P"))
    with pytest.raises(TypeError):
        build_ticket_duplication_check_form(PnrSubclass("PNR"))

    object.__setattr__(ticket, "return_password", "")
    with pytest.raises(ValueError):
        build_delivery_recipient_form(ticket)
    with pytest.raises(ValueError):
        build_platform_number_form((ticket,))
    object.__setattr__(pnr, "pnr_no", "")
    with pytest.raises(ValueError):
        build_ticket_duplication_check_form(pnr)


def test_ordered_safety_allows_only_exact_ticket_count_shapes():
    common = (("Device", "AD"), ("Version", "1"), ("Key", "K"))
    assert_read_only_request_fields(
        R146_PATH,
        (*common, ("tkCnt", 2), ("tkRetNo", "A"), ("tkRetNo", "B")),
    )
    assert_read_only_request_fields(
        R148_PATH,
        (*common, ("tkCnt", "2"), ("tkRetNo", "A"), ("tkRetNo", "B")),
    )
    invalid_by_path = {
        R146_PATH: (
            (*common, ("tkCnt", "2"), ("tkRetNo", "A"), ("tkRetNo", "B")),
            (*common, ("tkCnt", 1), ("tkRetNo", "A"), ("tkRetNo", "B")),
            (*common, ("tkCnt", True), ("tkRetNo", "A")),
            (*common, ("tkCnt", 0)),
            (*common, ("tkRetNo", "A"), ("tkCnt", 1)),
            (*common, ("tkCnt", 1), ("tkRetNo", "A"), ("Key", "again")),
        ),
        R148_PATH: (
            (*common, ("tkCnt", 2), ("tkRetNo", "A"), ("tkRetNo", "B")),
            (*common, ("tkCnt", "01"), ("tkRetNo", "A")),
            (*common, ("tkCnt", "2"), ("tkRetNo", "A")),
            (*common, ("tkCnt", ""), ("tkRetNo", "A")),
            (*common, ("tkCnt", "1"), ("tkRetNo", "A"), ("tkCnt", "1")),
        ),
    }
    for path, invalid_forms in invalid_by_path.items():
        for form in invalid_forms:
            with pytest.raises(KorailProtocolError):
                assert_read_only_request_fields(path, form)

    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(
            R137_PATH,
            (
                *common,
                ("saleWctNo", "W"),
                ("saleDt", "D"),
                ("saleSqno", "S"),
                ("tkRetPwd", "P"),
                ("tkRetPwd", "P2"),
            ),
        )


def test_strict_parsers_normalize_nullable_lists_and_return_frozen_models():
    responses = _responses()
    recipient = parse_delivery_recipient_response(responses[R137_PATH])
    duplicate = parse_ticket_duplication_check_response(responses[R138_PATH])
    acceptance = parse_pbp_acceptance_specification_response(
        responses[R146_PATH]
    )
    platform = parse_platform_number_response(responses[R148_PATH])
    history = parse_recent_delivery_history_response(responses[R149_PATH])

    assert recipient.acceptance_customer_name == "NAME_SECRET"
    assert duplicate.reservation_count == 2
    assert acceptance.tickets[0].journeys[0].seats[0].car_no == 3
    assert platform.tickets[0].journeys[0].platform_no == "PLATFORM_SECRET"
    assert history.recipients[0].acceptance_customer_phone_2 == "PHONE_2_SECRET"
    with pytest.raises(FrozenInstanceError):
        duplicate.reservation_count = 3

    for parser, list_key, attribute in (
        (parse_pbp_acceptance_specification_response, "tkList", "tickets"),
        (parse_platform_number_response, "tkList", "tickets"),
        (parse_recent_delivery_history_response, "acepList", "recipients"),
    ):
        assert getattr(parser(_success(**{list_key: None})), attribute) == ()
        assert getattr(parser(_success()), attribute) == ()


@pytest.mark.parametrize(("wire", "expected"), [(0, 0), ("0", 0), ("37", 37)])
def test_duplication_check_accepts_gson_coerced_rsv_count(wire, expected):
    # RV4-06: DuplicationCheckResponse.rsvCnt is Java `int`; Gson coerces a
    # quoted numeric string, so "0"/"37" parse like native ints.
    parsed = parse_ticket_duplication_check_response(_success(rsvCnt=wire))
    assert parsed.reservation_count == expected


@pytest.mark.parametrize(("wire", "expected"), [(3, 3), ("3", 3)])
def test_pbp_acceptance_accepts_gson_coerced_car_no(wire, expected):
    # RV4-06: PbpAcepSpecDao.Seat.scarNo is Java `int`; a quoted numeric string
    # is Gson-coerced, so it parses like a native int.
    raw = _responses()[R146_PATH]
    raw["tkList"][0]["jrnyList"][0]["seatList"][0]["scarNo"] = wire
    parsed = parse_pbp_acceptance_specification_response(raw)
    assert parsed.tickets[0].journeys[0].seats[0].car_no == expected


def test_parsers_reject_bad_envelopes_containers_rows_and_scalar_types():
    parsers = (
        parse_delivery_recipient_response,
        parse_ticket_duplication_check_response,
        parse_pbp_acceptance_specification_response,
        parse_platform_number_response,
        parse_recent_delivery_history_response,
    )
    for parser in parsers:
        with pytest.raises(KorailProtocolError):
            parser({"strResult": "SUCC"})
        with pytest.raises(KorailProtocolError):
            parser(_success(strResult="ERROR"))
        with pytest.raises(KorailAppError):
            parser(_success(h_msg_cd="FAIL.CODE", strResult="FAIL"))
        with pytest.raises(KorailAppError):
            parser(_success(h_msg_cd="WRC000288"))
        with pytest.raises(KorailSessionExpiredError):
            parser(_success(h_msg_cd="P058"))

    for value in (None, True, 2.0, "", "x"):
        with pytest.raises(KorailProtocolError):
            parse_ticket_duplication_check_response(_success(rsvCnt=value))
    for value in ({}, "rows", ["not-an-object"]):
        with pytest.raises(KorailProtocolError):
            parse_pbp_acceptance_specification_response(
                _success(tkList=value)
            )
        with pytest.raises(KorailProtocolError):
            parse_platform_number_response(_success(tkList=value))
    for value in ({}, "rows", ["not-an-object"]):
        with pytest.raises(KorailProtocolError):
            parse_recent_delivery_history_response(_success(acepList=value))

    malformed_acceptance = _responses()[R146_PATH]
    malformed_acceptance["tkList"][0]["jrnyList"][0]["seatList"][0][
        "scarNo"
    ] = True
    with pytest.raises(KorailProtocolError):
        parse_pbp_acceptance_specification_response(malformed_acceptance)
    malformed_platform = _responses()[R148_PATH]
    malformed_platform["tkList"][0]["jrnyList"] = {}
    with pytest.raises(KorailProtocolError):
        parse_platform_number_response(malformed_platform)


def test_sensitive_models_raw_mappings_and_text_are_repr_safe_and_redacted():
    parsed = [
        parse_delivery_recipient_response(_responses()[R137_PATH]),
        parse_ticket_duplication_check_response(_responses()[R138_PATH]),
        parse_pbp_acceptance_specification_response(_responses()[R146_PATH]),
        parse_platform_number_response(_responses()[R148_PATH]),
        parse_recent_delivery_history_response(_responses()[R149_PATH]),
    ]
    for value in parsed:
        assert "SECRET" not in repr(value)
        rendered = repr(redact_mapping({"response": value}))
        assert "SECRET" not in rendered

    raw = _responses()[R146_PATH]
    rendered_raw = repr(redact_mapping(raw))
    for secret in (
        "PNR_SECRET",
        "NAME_SECRET",
        "PHONE_SECRET",
        "RESERVATION_SECRET",
        "SEAT_SECRET",
        "RETURN_PASSWORD_SECRET",
    ):
        assert secret not in rendered_raw
    rendered_text = redact_text(
        "saleWctNo=SALE_WINDOW_SECRET saleDt=SALE_DATE_SECRET "
        "saleSqno=SALE_SEQUENCE_SECRET acepCustNm=NAME_SECRET "
        "acepCustTeln=PHONE_SECRET pbpRsvNo=RESERVATION_SECRET "
        "plfNo=PLATFORM_SECRET"
    )
    assert "SECRET" not in rendered_text

    assert redact_mapping({"rsvCnt": 37}) == {
        "rsvCnt": "[REDACTED]"
    }
    typed_count = TicketDuplicationCheckResponse(reservation_count=37)
    redacted_typed_count = redact_mapping({"response": typed_count})
    assert redacted_typed_count["response"]["reservation_count"] == (
        "[REDACTED]"
    )


def test_client_uses_one_shot_exact_forms_session_customer_and_no_dynapath():
    responses = _responses()
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
    client.session.current = KorailSession(
        jsessionid="SESSION_SECRET",
        customer_no="SESSION_CUSTOMER_SECRET",
    )
    ticket = _reference()
    operations = (
        lambda: client.get_delivery_recipient(ticket),
        lambda: client.check_ticket_duplication(
            TicketDuplicationCheckRequest("PNR_SECRET")
        ),
        lambda: client.get_pbp_acceptance_specifications((ticket,)),
        lambda: client.get_platform_numbers((ticket,)),
        client.get_recent_delivery_history,
    )
    results = [operation() for operation in operations]

    assert [type(value) for value in results] == [
        DeliveryRecipientResponse,
        TicketDuplicationCheckResponse,
        PbpAcceptanceSpecificationResponse,
        PlatformNumberResponse,
        RecentDeliveryHistoryResponse,
    ]
    assert len(requests) == 5
    assert provider_calls == []
    assert [request.url.path for request in requests] == list(responses)
    bodies = [
        parse_qsl(request.content.decode(), keep_blank_values=True)
        for request in requests
    ]
    common = [
        ("Device", config.device),
        ("Version", config.version),
        ("Key", config.key),
    ]
    assert bodies[0] == [
        *common,
        ("saleWctNo", ticket.sale_window_no),
        ("saleDt", ticket.sale_date),
        ("saleSqno", ticket.sale_sequence),
        ("tkRetPwd", ticket.return_password),
    ]
    assert bodies[1] == [*common, ("pnrNo", "PNR_SECRET")]
    assert bodies[2] == [
        *common,
        ("tkCnt", "1"),
        (
            "tkRetNo",
            "WINDOW_SECRET_1-SALE_DATE_SECRET_1-"
            "SALE_SEQUENCE_SECRET_1-RETURN_PASSWORD_SECRET_1",
        ),
    ]
    assert bodies[3] == bodies[2]
    assert bodies[4] == [
        *common,
        ("custMgNo", "SESSION_CUSTOMER_SECRET"),
    ]


def test_session_and_input_failures_stop_before_transport():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError("invalid calls must stop before transport")

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    ticket = _reference()
    operations = (
        lambda: client.get_delivery_recipient(ticket),
        lambda: client.check_ticket_duplication(
            TicketDuplicationCheckRequest("PNR_SECRET")
        ),
        lambda: client.get_pbp_acceptance_specifications((ticket,)),
        lambda: client.get_platform_numbers((ticket,)),
        client.get_recent_delivery_history,
    )
    for operation in operations:
        with pytest.raises(KorailAuthError):
            operation()
    assert requests == []

    client.session.current = KorailSession(jsessionid="SESSION_SECRET")
    with pytest.raises(KorailAuthError):
        client.get_recent_delivery_history()
    with pytest.raises(ValueError):
        client.get_pbp_acceptance_specifications(())
    with pytest.raises(TypeError):
        client.get_platform_numbers([ticket])  # type: ignore[arg-type]
    assert requests == []
