"""Three read-only routes surfaced by comparing against reference clients.

R150 ``certification.ReservationList`` (GET), R151 ``refunds.CommissionView``
(POST) and R152 ``refunds.SelTicketInfo`` (POST).

VERIFICATION STATUS. All three routes were exercised once against the live
server on an account holding zero reservations. Every route was ACCEPTED — HTTP
200, no DynaPath rejection — and each returned a distinct application-level
error for the deliberately-invalid arguments it was given. Those error bodies
are live-verified and are pinned in ``test_live_verified_shapes.py``. The
SUCCESS bodies are NOT verified: producing one needs a real paid/held ticket,
which cannot be created here (reserve and pay are out of scope for this
increment). The success-shape cases below are therefore built from the APK's
DAO declarations plus synthetic values and are labelled as such — they pin what
the app says the response is, not what the server was seen to send.
"""

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
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    TicketReservationDetailResponse,
)
from korail_mobile_api.read_parsers import (
    parse_refund_commission_response,
    parse_refund_ticket_detail_response,
    parse_ticket_reservation_detail_response,
)
from korail_mobile_api.read_payloads import (
    OriginalTicketReference,
    RefundCompanion,
    TicketReservationDetailRequest,
    build_refund_commission_form,
    build_refund_ticket_detail_form,
    build_ticket_reservation_detail_query,
)
from korail_mobile_api.redaction import redact_mapping, redact_text
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
)

R150_PATH = "/classes/com.korail.mobile.certification.ReservationList"
R151_PATH = "/classes/com.korail.mobile.refunds.CommissionView"
R152_PATH = "/classes/com.korail.mobile.refunds.SelTicketInfo"

NEW_ROUTES = {
    ("GET", R150_PATH),
    ("POST", R151_PATH),
    ("POST", R152_PATH),
}

REFUND_MUTATION_PATH = "/classes/com.korail.mobile.refunds.RefundsRequest"


def _ticket() -> OriginalTicketReference:
    return OriginalTicketReference(
        sale_window_no="WINDOW_SECRET",
        sale_date="SALE_DATE_SECRET",
        sale_sequence="SALE_SEQUENCE_SECRET",
        return_password="RETURN_PASSWORD_SECRET",
    )


def _success(**extra: Any) -> dict[str, Any]:
    return {
        "h_msg_cd": "SYNTHETIC.OK",
        "h_msg_txt": "SERVER_MESSAGE_SECRET",
        "strResult": "SUCC",
        **extra,
    }


def _reservation_detail_body() -> dict[str, Any]:
    """SYNTHETIC. Shape from ``ReservationResponse`` (:8-41, :296-313)."""
    return _success(
        h_pnr_no="PNR_SECRET",
        h_wct_no="WINDOW_SECRET",
        h_jrny_cnt="1",
        h_tot_fare="59800",
        h_tot_prc="59800",
        h_tot_dcnt_amt="0",
        h_tot_rcvd_amt="59800",
        h_payment_flg="Y",
        jrny_infos={
            "jrny_info": [
                {
                    "h_jrny_sqno": "001",
                    "h_jrny_tp_cd": "11",
                    "h_rsv_chg_no": "RESERVATION_CHANGE_SECRET",
                    "h_dpt_dt": "20260801",
                    "h_dpt_tm": "080000",
                    "h_arv_tm": "104300",
                    "h_dpt_rs_stn_nm": "DEPARTURE_SECRET",
                    "h_arv_rs_stn_nm": "ARRIVAL_SECRET",
                    "h_trn_no": "TRAIN_SECRET",
                    "h_trn_clsf_nm": "KTX",
                    "seat_infos": {
                        "seat_info": [
                            {
                                "h_srcar_no": "CAR_SECRET",
                                "h_seat_no": "SEAT_SECRET",
                                "h_psrm_cl_cd": "ROOM_CODE_SECRET",
                                "h_psrm_cl_nm": "ROOM_NAME_SECRET",
                                "h_psg_tp_cd": "1",
                                "h_rcvd_amt": "59800",
                                "h_seat_prc": "59800",
                                "h_seat_fare": "59800",
                                "h_sgr_nm": "SEAT_GROUP_SECRET",
                            }
                        ]
                    },
                }
            ]
        },
    )


def _refund_commission_body() -> dict[str, Any]:
    """SYNTHETIC. Shape from ``RefundCommissionDao`` (:70-77)."""
    return _success(
        ret_amt="59800",
        ret_fee="0",
        prg_psb_flg="Y",
        tk_ret_tms_dv_cd="1",
        use_psb_mlg_num="0",
        h_msg_cd2="SYNTHETIC.NOTICE",
        h_msg_txt2="SECONDARY_MESSAGE_SECRET",
    )


def _refund_ticket_detail_body() -> dict[str, Any]:
    """SYNTHETIC. Shape from ``TicketDetailDao`` (:227-281, :502-660)."""
    return _success(
        h_pnr_no="PNR_SECRET",
        h_sale_dt="20260701",
        h_sale_tm="120000",
        h_wct_nm="WINDOW_NAME_SECRET",
        h_orgtk_ret_sale_dt="ORIGINAL_SALE_DATE_SECRET",
        h_orgtk_wct_no="ORIGINAL_WINDOW_SECRET",
        h_orgtk_sale_sqno="ORIGINAL_SEQUENCE_SECRET",
        h_orgtk_ret_pwd="ORIGINAL_PASSWORD_SECRET",
        h_tk_knd_cd="01",
        h_tk_knd_nm="일반승차권",
        retPsbFlg="Y",
        h_ret_flg="N",
        h_tot_fare_amt="59800",
        h_tot_disc_amt="0",
        h_tot_rcvd_amt="59800",
        h_trn_running_flg="N",
        h_compa_nm="COMPANION_SECRET",
        h_compa_brth="COMPANION_BIRTH_SECRET",
        ticket_infos={
            "ticket_info": [
                {
                    "h_jrny_sqno": "001",
                    "h_jrny_tp_cd": "11",
                    "h_dpt_dt": "20260801",
                    "h_dpt_tm": "080000",
                    "h_dpt_rs_stn_nm": "DEPARTURE_SECRET",
                    "h_arv_dt": "20260801",
                    "h_arv_tm": "104300",
                    "h_arv_rs_stn_nm": "ARRIVAL_SECRET",
                    "h_trn_no": "TRAIN_SECRET",
                    "h_trn_clsf_nm": "KTX",
                    "h_psrm_cl_nm": "ROOM_NAME_SECRET",
                    "h_plf_no": "PLATFORM_SECRET",
                    "tk_seat_info": [
                        {
                            "h_srcar_no": "CAR_SECRET",
                            "h_seat_no": "SEAT_SECRET",
                            "h_buy_ps_nm": "BUYER_SECRET",
                            "h_chckn_stt_cd": "N",
                            "h_dcnt_knd_cd": "000",
                            "h_dcnt_knd_nm": "없음",
                            "h_psg_tp_cd": "1",
                            "h_psg_tp_nm": "어른",
                            "h_sgr_nm": "SEAT_GROUP_SECRET",
                        }
                    ],
                }
            ]
        },
    )


def _responses() -> dict[str, dict[str, Any]]:
    return {
        R150_PATH: _reservation_detail_body(),
        R151_PATH: _refund_commission_body(),
        R152_PATH: _refund_ticket_detail_body(),
    }


def test_routes_fields_exports_and_signatures_are_exact():
    assert len(KORAIL_READ_ONLY_ROUTES) == 54
    assert NEW_ROUTES <= KORAIL_READ_ONLY_ROUTES
    assert len(DYNAPATH_ALLOWLIST_PATHS) == 6
    assert all(path not in DYNAPATH_ALLOWLIST_PATHS for _, path in NEW_ROUTES)

    # These three are reads. The refund MUTATION route is a different path and
    # stays out of the read-only allowlist; adding a refund pre-check must not
    # smuggle the refund itself onto the read path.
    assert ("POST", REFUND_MUTATION_PATH) in KORAIL_MUTATION_ROUTES
    assert ("POST", REFUND_MUTATION_PATH) not in KORAIL_READ_ONLY_ROUTES
    assert REFUND_MUTATION_PATH not in KORAIL_EXACT_REQUEST_FIELDS
    assert not (NEW_ROUTES & KORAIL_MUTATION_ROUTES)

    expected_fields = {
        # CertificationService.java:45-46 (inquiryTicketRsv) -- the READ
        # overload only.
        R150_PATH: {"Device", "Version", "Key", "hidPnrNo"},
        # RefundService.java:19-21
        R151_PATH: {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_comp_nm",
            "h_comp_cert_no",
        },
        # RefundService.java:23-25 -- h_purchase_history included, contra srtgo.
        R152_PATH: {
            "Device",
            "Version",
            "Key",
            "h_orgtk_ret_sale_dt",
            "h_orgtk_wct_no",
            "h_orgtk_sale_sqno",
            "h_orgtk_ret_pwd",
            "h_purchase_history",
        },
    }
    for path, fields in expected_fields.items():
        assert KORAIL_EXACT_REQUEST_FIELDS[path] == fields

    contracts = {
        "get_ticket_reservation_detail": (
            ["self", "request"],
            {
                "request": TicketReservationDetailRequest,
                "return": TicketReservationDetailResponse,
            },
        ),
        "get_refund_commission": (
            ["self", "ticket", "companion"],
            {
                "ticket": OriginalTicketReference,
                "companion": RefundCompanion,
                "return": RefundCommissionResponse,
            },
        ),
        "get_refund_ticket_detail": (
            ["self", "ticket", "from_purchase_history"],
            {
                "ticket": OriginalTicketReference,
                "from_purchase_history": bool,
                "return": RefundTicketDetailResponse,
            },
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
    assert len(public_methods) == 61

    expected_exports = {
        "TicketReservationDetailRequest": (
            read_payloads.TicketReservationDetailRequest
        ),
        "RefundCompanion": read_payloads.RefundCompanion,
        "TicketReservationDetailResponse": (
            read_models.TicketReservationDetailResponse
        ),
        "ReservationDetailJourney": read_models.ReservationDetailJourney,
        "ReservationSeatDetail": read_models.ReservationSeatDetail,
        "RefundCommissionResponse": read_models.RefundCommissionResponse,
        "RefundTicketDetailResponse": read_models.RefundTicketDetailResponse,
        "RefundTicketJourney": read_models.RefundTicketJourney,
        "RefundTicketSeat": read_models.RefundTicketSeat,
    }
    for name, expected in expected_exports.items():
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is expected


def test_certification_route_pins_the_read_overload_not_the_write_one():
    """The write overload's request shape must be unreachable on this path.

    ``CertificationService.java`` declares TWO methods on
    ``certification.ReservationList``: ``inquiryTicketRsv`` (:45-46), the read
    ported here, and ``applyDisabilityCertification`` (:22), which adds
    ``txtPsgDisc0019Cnt`` plus six ``@QueryMap``s to apply a disability
    certificate to a held reservation. The exact-field pin is what keeps the
    second one off the wire.
    """
    common = {"Device": "AD", "Version": "1", "Key": "K"}
    assert_read_only_request_fields(R150_PATH, {**common, "hidPnrNo": "PNR"})

    write_overload_shapes = (
        # The declared extra @Query of applyDisabilityCertification.
        {**common, "hidPnrNo": "PNR", "txtPsgDisc0019Cnt": 1},
        # A @QueryMap entry of any name.
        {**common, "hidPnrNo": "PNR", "txtPsgDisc0019Cnt": 1, "hidDcntKndCd": "1"},
        {**common, "hidPnrNo": "PNR", "psg_tp_dv_cd": "1"},
        {**common, "hidPnrNo": "PNR", "hidDscpNo": "1"},
        # ...and the read overload with its one meaningful field missing.
        dict(common),
    )
    for shape in write_overload_shapes:
        with pytest.raises(KorailProtocolError):
            assert_read_only_request_fields(R150_PATH, shape)

    # The builder cannot express the write shape either: it emits exactly one
    # field and nothing accepts extra keyword arguments.
    assert build_ticket_reservation_detail_query(
        TicketReservationDetailRequest("PNR_SECRET")
    ) == {"hidPnrNo": "PNR_SECRET"}


def test_builders_emit_the_apps_exact_field_sets():
    ticket = _ticket()
    assert build_refund_commission_form(ticket) == {
        "h_orgtk_ret_sale_dt": ticket.sale_date,
        "h_orgtk_wct_no": ticket.sale_window_no,
        "h_orgtk_sale_sqno": ticket.sale_sequence,
        "h_orgtk_ret_pwd": ticket.return_password,
        # A ticket with no companion still transmits both, empty.
        "h_comp_nm": "",
        "h_comp_cert_no": "",
    }
    assert build_refund_commission_form(
        ticket,
        RefundCompanion(name="COMPANION_SECRET", certificate_no="BIRTH_SECRET"),
    ) == {
        "h_orgtk_ret_sale_dt": ticket.sale_date,
        "h_orgtk_wct_no": ticket.sale_window_no,
        "h_orgtk_sale_sqno": ticket.sale_sequence,
        "h_orgtk_ret_pwd": ticket.return_password,
        "h_comp_nm": "COMPANION_SECRET",
        "h_comp_cert_no": "BIRTH_SECRET",
    }

    # srtgo sends this as a GET and omits h_purchase_history (ktx.py:791-800).
    # The app declares POST with the flag, and every app call site sets it, so
    # the field is ALWAYS present and is exactly "Y" or "N".
    assert build_refund_ticket_detail_form(ticket)["h_purchase_history"] == "N"
    assert (
        build_refund_ticket_detail_form(ticket, from_purchase_history=True)[
            "h_purchase_history"
        ]
        == "Y"
    )
    assert set(build_refund_ticket_detail_form(ticket)) == {
        "h_orgtk_ret_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
        "h_purchase_history",
    }


def test_request_provenance_is_exact_revalidated_and_repr_hidden():
    request = TicketReservationDetailRequest("PNR_SECRET")
    companion = RefundCompanion("COMPANION_SECRET", "BIRTH_SECRET")
    assert "SECRET" not in repr(request)
    assert "SECRET" not in repr(companion)
    with pytest.raises(FrozenInstanceError):
        request.pnr_no = "CHANGED"

    class PnrSubclass(TicketReservationDetailRequest):
        pass

    class CompanionSubclass(RefundCompanion):
        pass

    class TicketSubclass(OriginalTicketReference):
        pass

    with pytest.raises(TypeError):
        build_ticket_reservation_detail_query(PnrSubclass("PNR"))
    with pytest.raises(TypeError):
        build_refund_commission_form(_ticket(), CompanionSubclass())
    with pytest.raises(TypeError):
        build_refund_commission_form(TicketSubclass("W", "D", "S", "P"))
    with pytest.raises(TypeError):
        build_refund_ticket_detail_form(TicketSubclass("W", "D", "S", "P"))
    with pytest.raises(TypeError):
        build_refund_ticket_detail_form(_ticket(), from_purchase_history=1)

    with pytest.raises(ValueError):
        TicketReservationDetailRequest("")
    with pytest.raises(ValueError):
        RefundCompanion(name=None)  # type: ignore[arg-type]

    object.__setattr__(request, "pnr_no", "")
    with pytest.raises(ValueError):
        build_ticket_reservation_detail_query(request)

    ticket = _ticket()
    object.__setattr__(ticket, "return_password", "")
    with pytest.raises(ValueError):
        build_refund_commission_form(ticket)
    with pytest.raises(ValueError):
        build_refund_ticket_detail_form(ticket)


def test_parsers_map_the_apk_declared_success_shapes():
    """SYNTHETIC success shapes -- APK-declared, NOT observed live.

    See the module docstring: the live pass could not produce a success body
    because the account holds no ticket. These assertions pin the app's DAO
    declaration, which is the only evidence available for the success path.
    """
    responses = _responses()

    detail = parse_ticket_reservation_detail_response(responses[R150_PATH])
    assert detail.window_no == "WINDOW_SECRET"
    assert detail.total_received_amount == "59800"
    seat = detail.journeys[0].seats[0]
    assert seat.car_no == "CAR_SECRET"
    assert seat.seat_no == "SEAT_SECRET"
    assert seat.room_class_name == "ROOM_NAME_SECRET"
    assert seat.received_amount == "59800"
    assert seat.seat_price == "59800"
    # The app declares the passenger type as a CODE on this row; there is no
    # h_psg_tp_dv_nm anywhere in the decompiled app, so nothing is mapped from
    # that name and an unmapped key would still be reachable through `raw`.
    assert seat.passenger_type_code == "1"
    assert not hasattr(seat, "passenger_type_name")
    assert "h_psg_tp_dv_nm" not in seat.raw

    commission = parse_refund_commission_response(responses[R151_PATH])
    assert commission.refund_amount == "59800"
    assert commission.refund_fee == "0"
    assert commission.proceed_possible_flag == "Y"
    assert commission.secondary_message_code == "SYNTHETIC.NOTICE"

    ticket_detail = parse_refund_ticket_detail_response(responses[R152_PATH])
    assert ticket_detail.refund_possible_flag == "Y"
    assert ticket_detail.total_received_amount == "59800"
    # These two are exactly what the app feeds into the CommissionView request.
    assert ticket_detail.companion_name == "COMPANION_SECRET"
    assert ticket_detail.companion_birth_date == "COMPANION_BIRTH_SECRET"
    assert build_refund_commission_form(
        _ticket(),
        RefundCompanion(
            name=ticket_detail.companion_name,
            certificate_no=ticket_detail.companion_birth_date,
        ),
    )["h_comp_nm"] == "COMPANION_SECRET"
    assert ticket_detail.journeys[0].seats[0].buyer_name == "BUYER_SECRET"

    for value in (detail, commission, ticket_detail):
        with pytest.raises(FrozenInstanceError):
            value.h_msg_cd = "CHANGED"


def test_parsers_normalize_absent_and_null_containers():
    for parser, attribute in (
        (parse_ticket_reservation_detail_response, "journeys"),
        (parse_refund_ticket_detail_response, "journeys"),
    ):
        assert getattr(parser(_success()), attribute) == ()
    assert (
        parse_ticket_reservation_detail_response(
            _success(jrny_infos=None)
        ).journeys
        == ()
    )
    assert (
        parse_ticket_reservation_detail_response(
            _success(jrny_infos={"jrny_info": None})
        ).journeys
        == ()
    )
    assert (
        parse_refund_ticket_detail_response(
            _success(ticket_infos={"ticket_info": None})
        ).journeys
        == ()
    )
    # A journey with no seat container yields an empty seat tuple, not a crash.
    journeys = parse_ticket_reservation_detail_response(
        _success(jrny_infos={"jrny_info": [{"h_jrny_sqno": "001"}]})
    ).journeys
    assert journeys[0].seats == ()
    assert parse_refund_commission_response(_success()).refund_amount is None


def test_parsers_reject_bad_envelopes_containers_and_scalar_types():
    parsers = (
        parse_ticket_reservation_detail_response,
        parse_refund_commission_response,
        parse_refund_ticket_detail_response,
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

    for value in ([], "rows", 3):
        with pytest.raises(KorailProtocolError):
            parse_ticket_reservation_detail_response(_success(jrny_infos=value))
        with pytest.raises(KorailProtocolError):
            parse_refund_ticket_detail_response(_success(ticket_infos=value))
    for value in ({}, "rows", ["not-an-object"]):
        with pytest.raises(KorailProtocolError):
            parse_ticket_reservation_detail_response(
                _success(jrny_infos={"jrny_info": value})
            )
        with pytest.raises(KorailProtocolError):
            parse_refund_ticket_detail_response(
                _success(ticket_infos={"ticket_info": value})
            )

    for value in (3, True, ["x"], {"a": 1}):
        with pytest.raises(KorailProtocolError):
            parse_refund_commission_response(_success(ret_amt=value))
        with pytest.raises(KorailProtocolError):
            parse_ticket_reservation_detail_response(_success(h_wct_no=value))
        with pytest.raises(KorailProtocolError):
            parse_refund_ticket_detail_response(_success(retPsbFlg=value))

    malformed = _reservation_detail_body()
    malformed["jrny_infos"]["jrny_info"][0]["seat_infos"] = ["not-an-object"]
    with pytest.raises(KorailProtocolError):
        parse_ticket_reservation_detail_response(malformed)
    malformed_seat = _refund_ticket_detail_body()
    malformed_seat["ticket_infos"]["ticket_info"][0]["tk_seat_info"] = "rows"
    with pytest.raises(KorailProtocolError):
        parse_refund_ticket_detail_response(malformed_seat)


def test_sensitive_identities_are_repr_safe_and_redacted():
    parsed = [
        parse_ticket_reservation_detail_response(_responses()[R150_PATH]),
        parse_refund_commission_response(_responses()[R151_PATH]),
        parse_refund_ticket_detail_response(_responses()[R152_PATH]),
    ]
    for value in parsed:
        assert "SECRET" not in repr(value)

    rendered = repr(redact_mapping(_responses()[R150_PATH]))
    for secret in (
        "PNR_SECRET",
        "WINDOW_SECRET",
        "CAR_SECRET",
        "SEAT_SECRET",
        "SEAT_GROUP_SECRET",
    ):
        assert secret not in rendered

    rendered_ticket = repr(redact_mapping(_responses()[R152_PATH]))
    for secret in (
        "PNR_SECRET",
        "ORIGINAL_WINDOW_SECRET",
        "ORIGINAL_SEQUENCE_SECRET",
        "ORIGINAL_PASSWORD_SECRET",
        "BUYER_SECRET",
        "COMPANION_SECRET",
        "COMPANION_BIRTH_SECRET",
        "WINDOW_NAME_SECRET",
        "PLATFORM_SECRET",
    ):
        assert secret not in rendered_ticket

    # The three request field sets must not leak through a text log either.
    rendered_text = redact_text(
        "hidPnrNo=PNR_SECRET h_orgtk_ret_sale_dt=SALE_DATE_SECRET "
        "h_orgtk_wct_no=WINDOW_SECRET h_orgtk_sale_sqno=SEQUENCE_SECRET "
        "h_orgtk_ret_pwd=PASSWORD_SECRET h_comp_nm=COMPANION_SECRET "
        "h_comp_cert_no=BIRTH_SECRET h_purchase_history=Y"
    )
    assert "SECRET" not in rendered_text

    typed = redact_mapping({"response": parsed[2]})["response"]
    for attribute in (
        "companion_name",
        "companion_birth_date",
        "original_window_no",
        "original_return_password",
    ):
        assert typed[attribute] == "[REDACTED]"


def test_client_sends_the_apps_exact_wire_shapes_without_dynapath():
    responses = _responses()
    requests: list[httpx.Request] = []

    def provider(context: Any) -> str:
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
    ticket = _ticket()
    results = [
        client.get_ticket_reservation_detail(
            TicketReservationDetailRequest("PNR_SECRET")
        ),
        client.get_refund_commission(
            ticket,
            RefundCompanion("COMPANION_SECRET", "BIRTH_SECRET"),
        ),
        client.get_refund_ticket_detail(ticket, from_purchase_history=True),
    ]
    assert [type(value) for value in results] == [
        TicketReservationDetailResponse,
        RefundCommissionResponse,
        RefundTicketDetailResponse,
    ]
    assert [request.method for request in requests] == ["GET", "POST", "POST"]
    assert [request.url.path for request in requests] == [
        R150_PATH,
        R151_PATH,
        R152_PATH,
    ]
    common = [
        ("Device", config.device),
        ("Version", config.version),
        ("Key", config.key),
    ]
    assert parse_qsl(requests[0].url.query.decode(), keep_blank_values=True) == [
        *common,
        ("hidPnrNo", "PNR_SECRET"),
    ]
    assert requests[0].content == b""
    bodies = [
        parse_qsl(request.content.decode(), keep_blank_values=True)
        for request in requests[1:]
    ]
    assert bodies[0] == [
        *common,
        ("h_orgtk_ret_sale_dt", ticket.sale_date),
        ("h_orgtk_wct_no", ticket.sale_window_no),
        ("h_orgtk_sale_sqno", ticket.sale_sequence),
        ("h_orgtk_ret_pwd", ticket.return_password),
        ("h_comp_nm", "COMPANION_SECRET"),
        ("h_comp_cert_no", "BIRTH_SECRET"),
    ]
    assert bodies[1] == [
        *common,
        ("h_orgtk_ret_sale_dt", ticket.sale_date),
        ("h_orgtk_wct_no", ticket.sale_window_no),
        ("h_orgtk_sale_sqno", ticket.sale_sequence),
        ("h_orgtk_ret_pwd", ticket.return_password),
        ("h_purchase_history", "Y"),
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
    ticket = _ticket()
    operations = (
        lambda: client.get_ticket_reservation_detail(
            TicketReservationDetailRequest("PNR_SECRET")
        ),
        lambda: client.get_refund_commission(ticket),
        lambda: client.get_refund_ticket_detail(ticket),
    )
    for operation in operations:
        with pytest.raises(KorailAuthError):
            operation()
    assert requests == []

    client.session.current = KorailSession(jsessionid="SESSION_SECRET")
    with pytest.raises(TypeError):
        client.get_refund_commission(("W", "D", "S", "P"))  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        client.get_refund_ticket_detail(ticket, from_purchase_history="Y")  # type: ignore[arg-type]
    assert requests == []
