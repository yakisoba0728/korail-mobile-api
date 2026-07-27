"""비회원 오프라인(역창구 발권) 승차권 반환 — offline tests.

Covers ``refunds.verifyOnlineRefunds`` and ``refunds.executeOnlineRefunds``
(``RefundService.java:31-33`` and ``:15-17``) plus the non-member session model
they depend on. Nothing here sends: every client is built on a MockTransport
whose handler fails the test if it is ever reached.

The most important assertions in this file are the redaction ones. Not one of
the values this flow carries is caught by a value-shaped regex — the 16-digit
반환번호 arrives split 5/4/5/2 so ``CARD_RE`` never sees 13 consecutive digits,
the phone number is 11 digits, and the requester's name is a name. Key-based
redaction is the ONLY thing between them and a preview, so the tests search the
rendered preview for the raw strings rather than trusting that a key maps to
``[REDACTED]``.
"""

from __future__ import annotations

import httpx
import pytest

from korail_mobile_api import (
    KorailAuthError,
    KorailClient,
    KorailConfig,
    KorailNonMemberSession,
    KorailProtocolError,
    KorailSession,
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    OfflineRefundExecuteResponse,
    OfflineRefundReturnNumber,
    OfflineRefundVerifyResponse,
    parse_offline_refund_execute_response,
    parse_offline_refund_verify_response,
    require_mutation_consent,
)
from korail_mobile_api.mutation_payloads import (
    build_offline_refund_execute_form,
    build_offline_refund_verify_form,
)
from korail_mobile_api.redaction import (
    SENSITIVE_KEYS,
    is_sensitive_key,
    redact_payload,
    redact_value,
)
from korail_mobile_api.safety import (
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


VERIFY_ROUTE = "/classes/com.korail.mobile.refunds.verifyOnlineRefunds"
EXECUTE_ROUTE = "/classes/com.korail.mobile.refunds.executeOnlineRefunds"
MEMBER_REFUND_ROUTE = "/classes/com.korail.mobile.refunds.RefundsRequest"

# Obviously-synthetic stand-ins. Each is a value that MUST NOT survive into a
# preview, and each is distinctive enough to find by substring search.
FAKE_RETURN_SEGMENTS = ("54321", "9876", "13579", "24")
FAKE_TICKET_NUMBER = "5432198761357924"
FAKE_NAME = "SYNTHETIC_REQUESTER_NAME"
FAKE_PHONE = "01099998888"
FAKE_NON_MEMBER_PASSWORD = "SYNTHETIC_NONMEMBER_PWD"
FAKE_PNR = "SYNTHETIC_PNR_REFERENCE"
FAKE_RETURN_PASSWORD = "SYNTHETIC_RETURN_PWD"
FAKE_WINDOW_NO = "SYNTHETIC_WCT_NO"
FAKE_SALE_SEQUENCE = "SYNTHETIC_SALE_SQNO"
FAKE_SALE_DATE = "20990101"


def _refuse(request: httpx.Request) -> httpx.Response:  # pragma: no cover
    raise AssertionError(
        f"nothing may be sent: {request.method} {request.url.path}"
    )


def _client() -> KorailClient:
    return KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )


def _non_member_client() -> KorailClient:
    client = _client()
    client.begin_non_member(
        FAKE_NAME,
        FAKE_PHONE,
        password=FAKE_NON_MEMBER_PASSWORD,
    )
    return client


def _return_number() -> OfflineRefundReturnNumber:
    return OfflineRefundReturnNumber(*FAKE_RETURN_SEGMENTS)


def _verify_raw() -> dict[str, object]:
    """A synthetic ``verifyOnlineRefunds`` body, shaped from the DAO alone.

    ``RefundVerifyTicketDao.java:64-171``. No live capture of this route
    exists, which is exactly why the fixture is inline and labelled.
    """
    return {
        "h_msg_cd": "IRZ000001",
        "h_msg_txt": "정상처리되었습니다",
        "strResult": "SUCC",
        "rcvd_amt": "47500",
        "ret_amt": "43000",
        "ret_fee": "4500",
        "poppMsg": "",
        "orgtkinfo_list": [
            {
                "prnNo": FAKE_PNR,
                "ogtk_sale_dt": FAKE_SALE_DATE,
                "ogtk_sale_wct_no": FAKE_WINDOW_NO,
                "ogtk_sale_sqno": FAKE_SALE_SEQUENCE,
                "ogtk_ret_pwd": FAKE_RETURN_PASSWORD,
                "tk_knd_cd": "01",
                "ret_dv_cd": "01",
                "ret_rsn_cd": "011",
                "jrnyinfo_list": [
                    {
                        "dpt_dt": "20990101",
                        "dpt_tm": "100700",
                        "arv_tm": "102400",
                        "dpt_rs_stn_cd": "0001",
                        "arv_rs_stn_cd": "0501",
                        "trn_gp_cd": "100",
                        "trn_no": "00209",
                        "seatinfo_list": [
                            {
                                "psrm_cl_nm": "일반실",
                                "scar_no": "3",
                                "seat_no": "11A",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _verified() -> OfflineRefundVerifyResponse:
    return parse_offline_refund_verify_response(_verify_raw())


# --- the non-member session model --------------------------------------------


def test_non_member_session_is_a_distinct_type_with_no_jsessionid():
    non_member = KorailNonMemberSession(
        non_member_name=FAKE_NAME,
        non_member_phone=FAKE_PHONE,
    )
    # A different type, not a flag on KorailSession -- and structurally
    # different: there is no cookie to hold, because there is no login.
    assert not isinstance(non_member, KorailSession)
    assert not hasattr(non_member, "jsessionid")
    assert not hasattr(non_member, "member_no")
    assert non_member.non_member_password is None
    # Every field is repr=False: a repr of a held identity is a PII leak.
    rendered = repr(non_member)
    for secret in (FAKE_NAME, FAKE_PHONE):
        assert secret not in rendered


def test_non_member_session_refuses_an_empty_identity():
    for kwargs in (
        {"non_member_name": "", "non_member_phone": FAKE_PHONE},
        {"non_member_name": FAKE_NAME, "non_member_phone": "  "},
        {"non_member_name": None, "non_member_phone": FAKE_PHONE},
        {
            "non_member_name": FAKE_NAME,
            "non_member_phone": FAKE_PHONE,
            "non_member_password": "",
        },
    ):
        with pytest.raises(KorailProtocolError):
            KorailNonMemberSession(**kwargs)  # type: ignore[arg-type]


def test_non_member_state_transitions_never_touch_the_member_slot():
    client = _client()
    assert client.session.current is None
    assert client.session.non_member is None

    held = client.begin_non_member(FAKE_NAME, FAKE_PHONE)
    assert client.session.non_member is held
    assert isinstance(held, KorailNonMemberSession)
    # Holding a non-member identity does NOT produce a member session.
    assert client.session.current is None

    client.end_non_member()
    assert client.session.non_member is None
    assert client.session.current is None


def test_a_member_session_and_a_non_member_identity_are_mutually_exclusive():
    client = _client()
    client.session.current = KorailSession(jsessionid="SYNTHETIC_SESSION")
    # Direction 1: cannot hold a non-member identity while logged in.
    with pytest.raises(KorailAuthError):
        client.begin_non_member(FAKE_NAME, FAKE_PHONE)
    assert client.session.non_member is None

    # Direction 2: clearing the session drops the held identity too, which is
    # what makes login() (which opens with clear_session) exclusive for free.
    client.session.current = None
    client.begin_non_member(FAKE_NAME, FAKE_PHONE)
    client.clear_session()
    assert client.session.non_member is None
    assert client.session.current is None


def test_logout_drops_the_held_non_member_identity():
    client = _client()
    client.begin_non_member(FAKE_NAME, FAKE_PHONE)
    # No member session, so logout makes no request and simply clears.
    client.logout()
    assert client.session.non_member is None


# --- route <-> category binding ----------------------------------------------


def test_both_routes_are_refund_category_mutation_routes():
    for route in (VERIFY_ROUTE, EXECUTE_ROUTE):
        assert ("POST", route) in KORAIL_MUTATION_ROUTES
        assert ("GET", route) not in KORAIL_MUTATION_ROUTES
        assert ("POST", route) not in KORAIL_READ_ONLY_ROUTES
        # The same category as the member refund: same act, same money.
        assert KORAIL_MUTATION_ROUTE_CATEGORIES[route] == "refund"
        assert_mutation_route("POST", route)
        assert_mutation_route_category(route, "refund")
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[MEMBER_REFUND_ROUTE] == "refund"
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)


def test_no_other_consent_category_can_be_redirected_onto_these_routes():
    for route in (VERIFY_ROUTE, EXECUTE_ROUTE):
        for wrong in (
            "reserve",
            "payment",
            "cancel",
            "discount_card",
            "price_recalculation",
        ):
            with pytest.raises(KorailProtocolError):
                assert_mutation_route_category(route, wrong)
        # ...and a refund consent cannot be redirected onto another route.
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(
                "/classes/com.korail.mobile.payment.ReservationPayment",
                "refund",
            )


def test_the_read_only_path_still_refuses_both_routes():
    for route in (VERIFY_ROUTE, EXECUTE_ROUTE):
        for method in ("POST", "GET"):
            with pytest.raises(KorailProtocolError):
                assert_read_only_route(method, route)


def test_no_new_consent_category_and_no_card_bearing_change():
    from korail_mobile_api.consent import MUTATION_CATEGORIES

    assert len(MUTATION_CATEGORIES) == 6
    assert "refund" in MUTATION_CATEGORIES
    # Neither form carries a card number, so the card gate is untouched.
    assert KORAIL_CARD_BEARING_MUTATION_CATEGORIES == frozenset({"payment"})
    assert "refund" not in KORAIL_CARD_BEARING_MUTATION_CATEGORIES


# --- consent refusal: four ways, zero requests --------------------------------


@pytest.mark.parametrize(
    "consent",
    [
        None,
        MutationConsent(),
        MutationConsent(allow_reserve=True, allow_cancel=True),
        MutationConsent(allow_payment=True, allow_discount_card=True),
    ],
    ids=["none", "default-denies-all", "reserve+cancel", "payment+card"],
)
def test_both_methods_refuse_every_non_refund_consent_and_send_nothing(consent):
    client = _non_member_client()
    with pytest.raises(MutationNotAllowedError):
        client.verify_offline_refund_ticket(
            _return_number(),
            consent=consent,  # type: ignore[arg-type]
        )
    with pytest.raises(MutationNotAllowedError):
        client.execute_offline_refund(
            _verified(),
            consent=consent,  # type: ignore[arg-type]
        )
    # The MockTransport handler raises on any request, so reaching here at all
    # proves nothing was sent. Assert the gate ordering too: consent is checked
    # before the identity precondition and before the form is built.
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(consent, "refund")  # type: ignore[arg-type]


def test_consent_is_checked_before_the_non_member_precondition():
    # No held identity AND no consent -> the CONSENT error, not the auth one.
    client = _client()
    with pytest.raises(MutationNotAllowedError):
        client.verify_offline_refund_ticket(
            _return_number(),
            consent=MutationConsent(),
        )


def test_the_transmit_gate_refuses_a_dry_run_consent():
    client = _non_member_client()
    for route, form in (
        (
            VERIFY_ROUTE,
            build_offline_refund_verify_form(
                client.config,
                _return_number(),
                requester_name=FAKE_NAME,
            ),
        ),
        (
            EXECUTE_ROUTE,
            build_offline_refund_execute_form(
                client.config,
                _verified(),
                requester_name=FAKE_NAME,
                requester_phone=FAKE_PHONE,
            ),
        ),
    ):
        with pytest.raises(MutationNotAllowedError):
            client.http.post_mutation_form(
                route,
                form,
                consent=MutationConsent(allow_refund=True),
                category="refund",
            )


# --- the non-member precondition ---------------------------------------------


def test_both_methods_require_a_held_non_member_identity():
    client = _client()
    consent = MutationConsent(allow_refund=True)
    with pytest.raises(KorailAuthError) as verify_error:
        client.verify_offline_refund_ticket(_return_number(), consent=consent)
    assert "begin_non_member" in str(verify_error.value)
    with pytest.raises(KorailAuthError):
        client.execute_offline_refund(_verified(), consent=consent)


def test_both_methods_refuse_to_run_under_a_member_session():
    # The point of the guard: a logged-in caller reaching for the offline path
    # has reached for the wrong method, and refund() is the right one.
    client = _client()
    client.session.non_member = KorailNonMemberSession(
        non_member_name=FAKE_NAME,
        non_member_phone=FAKE_PHONE,
    )
    client.session.current = KorailSession(jsessionid="SYNTHETIC_SESSION")
    consent = MutationConsent(allow_refund=True)
    with pytest.raises(KorailAuthError) as error:
        client.verify_offline_refund_ticket(_return_number(), consent=consent)
    assert "refund()" in str(error.value)
    with pytest.raises(KorailAuthError):
        client.execute_offline_refund(_verified(), consent=consent)


# --- the return number --------------------------------------------------------


def test_return_number_segment_lengths_match_the_apps_own_integers():
    # res/values/integers.xml:29-32, enforced by s5/c.java:85.
    assert OfflineRefundReturnNumber.SEGMENT_LENGTHS == (5, 4, 5, 2)
    assert sum(OfflineRefundReturnNumber.SEGMENT_LENGTHS) == 16


def test_return_number_rejects_wrong_lengths_and_non_digits():
    for segments in (
        ("5432", "9876", "13579", "24"),
        ("54321", "98765", "13579", "24"),
        ("54321", "9876", "13579", "245"),
        ("54321", "9876", "13579", ""),
        ("5432A", "9876", "13579", "24"),
    ):
        with pytest.raises(KorailProtocolError):
            OfflineRefundReturnNumber(*segments)


def test_return_number_splits_a_printed_16_digit_number():
    plain = OfflineRefundReturnNumber.from_ticket_number(FAKE_TICKET_NUMBER)
    assert (
        plain.return_no_1,
        plain.return_no_2,
        plain.return_no_3,
        plain.return_no_4,
    ) == FAKE_RETURN_SEGMENTS
    # The app re-joins the four boxes with "-" for display (s5/c.java:197,
    # z5/e.java:83), so that spelling round-trips.
    dashed = "-".join(FAKE_RETURN_SEGMENTS)
    assert OfflineRefundReturnNumber.from_ticket_number(dashed) == plain
    for bad in ("543219876135792", "54321987613579244", "not-a-number"):
        with pytest.raises(KorailProtocolError):
            OfflineRefundReturnNumber.from_ticket_number(bad)


# --- form field contracts -----------------------------------------------------


def test_verify_form_is_exactly_the_retrofit_signature_in_order():
    # RefundService.java:31-33 / RefundService.smali:273-320.
    form = build_offline_refund_verify_form(
        KorailConfig(),
        _return_number(),
        requester_name=FAKE_NAME,
    )
    assert list(form) == [
        "Device",
        "Version",
        "Key",
        "retNo1",
        "retNo2",
        "retNo3",
        "retNo4",
        "strName",
    ]
    assert form["retNo1"] == FAKE_RETURN_SEGMENTS[0]
    assert form["retNo2"] == FAKE_RETURN_SEGMENTS[1]
    assert form["retNo3"] == FAKE_RETURN_SEGMENTS[2]
    assert form["retNo4"] == FAKE_RETURN_SEGMENTS[3]
    assert form["strName"] == FAKE_NAME
    # The phone number is collected by the same screen but NOT sent here.
    assert FAKE_PHONE not in form.values()


def test_execute_form_is_exactly_the_retrofit_signature_in_order():
    # RefundService.java:15-17 / RefundService.smali:1-90.
    form = build_offline_refund_execute_form(
        KorailConfig(),
        _verified(),
        requester_name=FAKE_NAME,
        requester_phone=FAKE_PHONE,
    )
    assert list(form) == [
        "Device",
        "Version",
        "Key",
        "pnrNo",
        "tkKndCd",
        "retDvCd",
        "retRsnCd",
        "ogtkSaleDt",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "retAmt",
        "retFee",
        "custTeln",
        "acepCustNm",
    ]
    # The crossed pair: acepCustNm is the NAME (the app stores it under the
    # bundle key "CUSTOMER_NUMBER", s5/h.java:105,122) and custTeln the phone.
    assert form["acepCustNm"] == FAKE_NAME
    assert form["custTeln"] == FAKE_PHONE
    # Nine values come straight off the verify response (s5/h.java:114-125).
    assert form["pnrNo"] == FAKE_PNR
    assert form["ogtkSaleDt"] == FAKE_SALE_DATE
    assert form["ogtkSaleWctNo"] == FAKE_WINDOW_NO
    assert form["ogtkSaleSqno"] == FAKE_SALE_SEQUENCE
    assert form["ogtkRetPwd"] == FAKE_RETURN_PASSWORD
    assert form["retAmt"] == "43000"
    assert form["retFee"] == "4500"
    assert form["tkKndCd"] == "01"
    assert form["retDvCd"] == "01"
    assert form["retRsnCd"] == "011"


def test_the_builders_refuse_the_wrong_input_types_and_blank_identities():
    config = KorailConfig()
    with pytest.raises(KorailProtocolError):
        build_offline_refund_verify_form(
            config,
            "5432198761357924",  # type: ignore[arg-type]
            requester_name=FAKE_NAME,
        )
    for blank in ("", "   ", None):
        with pytest.raises(KorailProtocolError):
            build_offline_refund_verify_form(
                config,
                _return_number(),
                requester_name=blank,  # type: ignore[arg-type]
            )
    with pytest.raises(KorailProtocolError):
        build_offline_refund_execute_form(
            config,
            _verify_raw(),  # type: ignore[arg-type]
            requester_name=FAKE_NAME,
            requester_phone=FAKE_PHONE,
        )
    for blank in ("", "   ", None):
        with pytest.raises(KorailProtocolError):
            build_offline_refund_execute_form(
                config,
                _verified(),
                requester_name=FAKE_NAME,
                requester_phone=blank,  # type: ignore[arg-type]
            )


def test_execute_refuses_a_verification_that_did_not_resolve_one_ticket():
    empty = parse_offline_refund_verify_response(
        {**_verify_raw(), "orgtkinfo_list": []}
    )
    raw = _verify_raw()
    two = parse_offline_refund_verify_response(
        {**raw, "orgtkinfo_list": list(raw["orgtkinfo_list"]) * 2}  # type: ignore[arg-type]
    )
    for verified in (empty, two):
        with pytest.raises(KorailProtocolError):
            build_offline_refund_execute_form(
                KorailConfig(),
                verified,
                requester_name=FAKE_NAME,
                requester_phone=FAKE_PHONE,
            )


def test_execute_refuses_a_verification_missing_any_identity_part():
    raw = _verify_raw()
    for key in (
        "prnNo",
        "ogtk_sale_dt",
        "ogtk_sale_wct_no",
        "ogtk_sale_sqno",
        "ogtk_ret_pwd",
        "tk_knd_cd",
        "ret_dv_cd",
        "ret_rsn_cd",
    ):
        ticket = {**raw["orgtkinfo_list"][0]}  # type: ignore[index]
        ticket.pop(key)
        verified = parse_offline_refund_verify_response(
            {**raw, "orgtkinfo_list": [ticket]}
        )
        with pytest.raises(KorailProtocolError) as error:
            build_offline_refund_execute_form(
                KorailConfig(),
                verified,
                requester_name=FAKE_NAME,
                requester_phone=FAKE_PHONE,
            )
        assert "missing verified fields" in str(error.value)


# --- parsers ------------------------------------------------------------------


def test_verify_response_parses_the_nested_ticket_journey_and_seat_rows():
    verified = _verified()
    assert isinstance(verified, OfflineRefundVerifyResponse)
    assert verified.received_amount == "47500"
    assert verified.refund_amount == "43000"
    assert verified.refund_fee == "4500"
    assert verified.popup_message == ""
    assert len(verified.tickets) == 1
    ticket = verified.tickets[0]
    # prnNo (P-r-n) on the way in becomes pnrNo (P-n-r) on the way out.
    assert ticket.pnr_no == FAKE_PNR
    assert ticket.original_return_password == FAKE_RETURN_PASSWORD
    assert len(ticket.journeys) == 1
    journey = ticket.journeys[0]
    assert journey.train_no == "00209"
    assert journey.departure_station_code == "0001"
    assert len(journey.seats) == 1
    assert journey.seats[0].car_no == "3"
    assert journey.seats[0].seat_no == "11A"
    assert journey.seats[0].room_class_name == "일반실"


def test_verify_response_tolerates_absent_lists_and_rejects_wrong_shapes():
    raw = _verify_raw()
    raw.pop("orgtkinfo_list")
    assert parse_offline_refund_verify_response(raw).tickets == ()
    for broken in (
        {**_verify_raw(), "orgtkinfo_list": {"a": 1}},
        {**_verify_raw(), "orgtkinfo_list": ["not-an-object"]},
    ):
        with pytest.raises(KorailProtocolError):
            parse_offline_refund_verify_response(broken)


def test_execute_response_distinguishes_completed_from_accepted():
    envelope = {
        "h_msg_cd": "IRZ000001",
        "h_msg_txt": "정상처리되었습니다",
        "strResult": "SUCC",
    }
    completed = parse_offline_refund_execute_response(
        {**envelope, "h_ret_dv_cd": "02"}
    )
    assert isinstance(completed, OfflineRefundExecuteResponse)
    assert completed.return_division_code == "02"
    assert completed.is_refund_completed is True
    accepted = parse_offline_refund_execute_response(
        {**envelope, "h_ret_dv_cd": "01"}
    )
    assert accepted.is_refund_completed is False
    assert parse_offline_refund_execute_response(envelope).is_refund_completed is False


# --- the send path (synthetic transport) --------------------------------------


def _recording_client(body: dict[str, object]):
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, json=body)

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.begin_non_member(FAKE_NAME, FAKE_PHONE)
    return client, sent


def test_a_non_dry_run_verify_posts_the_form_and_parses_the_reply():
    client, sent = _recording_client(_verify_raw())
    verified = client.verify_offline_refund_ticket(
        _return_number(),
        consent=MutationConsent(allow_refund=True, dry_run=False),
    )
    assert isinstance(verified, OfflineRefundVerifyResponse)
    assert verified.tickets[0].original_return_password == FAKE_RETURN_PASSWORD
    assert len(sent) == 1
    request = sent[0]
    assert request.method == "POST"
    assert request.url.path == VERIFY_ROUTE
    body = request.content.decode()
    assert "retNo1=" in body and "strName=" in body


def test_a_non_dry_run_execute_posts_the_form_and_parses_the_reply():
    client, sent = _recording_client(
        {
            "h_msg_cd": "IRZ000001",
            "h_msg_txt": "정상처리되었습니다",
            "strResult": "SUCC",
            "h_ret_dv_cd": "02",
        }
    )
    result = client.execute_offline_refund(
        _verified(),
        consent=MutationConsent(allow_refund=True, dry_run=False),
    )
    assert isinstance(result, OfflineRefundExecuteResponse)
    assert result.is_refund_completed is True
    assert len(sent) == 1
    assert sent[0].url.path == EXECUTE_ROUTE
    body = sent[0].content.decode()
    assert "acepCustNm=" in body and "custTeln=" in body


# --- redaction: the load-bearing tests ----------------------------------------


def test_every_new_wire_key_and_model_attribute_is_registered():
    for key in (
        "retNo1",
        "retNo2",
        "retNo3",
        "retNo4",
        "retNo",
        "strName",
        "custTeln",
        "acepCustNm",
        "pnrNo",
        "ogtkSaleDt",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "prnNo",
        "ogtk_sale_dt",
        "ogtk_sale_wct_no",
        "ogtk_sale_sqno",
        "ogtk_ret_pwd",
        "scar_no",
        "seat_no",
        "psrm_cl_nm",
        "non_member_name",
        "non_member_phone",
        "non_member_password",
        "return_no_1",
        "return_no_2",
        "return_no_3",
        "return_no_4",
        "pnr_no",
        "original_sale_date",
        "original_window_no",
        "original_sale_sequence",
        "original_return_password",
        "car_no",
        "room_class_name",
    ):
        assert is_sensitive_key(key), key
        assert is_sensitive_key(key.upper()), key
    # The base catches an index the enumeration does not reach.
    assert is_sensitive_key("retNo9")
    assert is_sensitive_key("return_no_9")
    # ...and the enumerated spellings are in the literal set too, which is what
    # the free-text regex matches on (the base alone would not catch "retNo1=").
    for key in ("retno1", "retno2", "retno3", "retno4"):
        assert key in SENSITIVE_KEYS


def test_the_verify_preview_leaks_no_identity_in_plaintext():
    client = _non_member_client()
    preview = client.verify_offline_refund_ticket(
        _return_number(),
        consent=MutationConsent(allow_refund=True),
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "refund"
    assert preview.method == "POST"
    assert preview.route == VERIFY_ROUTE
    assert preview.note == "dry-run: not sent"
    for key in ("retNo1", "retNo2", "retNo3", "retNo4", "strName"):
        assert preview.payload[key] == "[REDACTED]"
    # The real check: not one raw value survives anywhere in the rendering.
    rendered = f"{preview!r} {preview.payload!r}"
    for secret in (*FAKE_RETURN_SEGMENTS, FAKE_NAME, FAKE_TICKET_NUMBER):
        assert secret not in rendered
    # Non-secret envelope fields are still readable, so the preview is useful.
    assert preview.payload["Device"] != "[REDACTED]"


def test_the_execute_preview_leaks_no_identity_in_plaintext():
    client = _non_member_client()
    preview = client.execute_offline_refund(
        _verified(),
        consent=MutationConsent(allow_refund=True),
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "refund"
    assert preview.route == EXECUTE_ROUTE
    for key in (
        "pnrNo",
        "ogtkSaleDt",
        "ogtkSaleWctNo",
        "ogtkSaleSqno",
        "ogtkRetPwd",
        "custTeln",
        "acepCustNm",
    ):
        assert preview.payload[key] == "[REDACTED]"
    rendered = f"{preview!r} {preview.payload!r}"
    for secret in (
        FAKE_PNR,
        FAKE_NAME,
        FAKE_PHONE,
        FAKE_RETURN_PASSWORD,
        FAKE_WINDOW_NO,
        FAKE_SALE_SEQUENCE,
        FAKE_SALE_DATE,
    ):
        assert secret not in rendered
    # The amounts stay readable: they are what a caller must check before
    # authorising a real refund, and they identify nobody.
    assert preview.payload["retAmt"] == "43000"
    assert preview.payload["retFee"] == "4500"


def test_the_probe_regexes_would_not_have_caught_any_of_this():
    # Why key-based redaction is load-bearing here rather than belt-and-braces:
    # with the keys renamed to something unregistered, every value survives.
    disguised = redact_payload(
        {
            "a": FAKE_RETURN_SEGMENTS[0],
            "b": FAKE_RETURN_SEGMENTS[1],
            "c": FAKE_RETURN_SEGMENTS[2],
            "d": FAKE_RETURN_SEGMENTS[3],
            "e": FAKE_NAME,
            "f": FAKE_PHONE,
        }
    )
    assert list(disguised.values()) == [
        FAKE_RETURN_SEGMENTS[0],
        FAKE_RETURN_SEGMENTS[1],
        FAKE_RETURN_SEGMENTS[2],
        FAKE_RETURN_SEGMENTS[3],
        FAKE_NAME,
        FAKE_PHONE,
    ]


def test_the_parsed_verify_response_and_held_identity_redact_by_attribute():
    # redact_value walks dataclasses by field name, so the parsed credential
    # and the held identity are both masked without any special-casing.
    redacted = redact_value(_verified())
    rendered = repr(redacted)
    for secret in (
        FAKE_PNR,
        FAKE_RETURN_PASSWORD,
        FAKE_WINDOW_NO,
        FAKE_SALE_SEQUENCE,
    ):
        assert secret not in rendered
    # ...including the raw envelope the response carries alongside.
    for wire_key in ("prnNo", "ogtk_ret_pwd", "ogtk_sale_wct_no"):
        assert wire_key in rendered

    identity = redact_value(
        KorailNonMemberSession(
            non_member_name=FAKE_NAME,
            non_member_phone=FAKE_PHONE,
            non_member_password=FAKE_NON_MEMBER_PASSWORD,
        )
    )
    assert identity == {
        "non_member_name": "[REDACTED]",
        "non_member_phone": "[REDACTED]",
        "non_member_password": "[REDACTED]",
    }


def test_free_text_containing_the_new_keys_is_redacted():
    # Not the same guarantee as redact_payload: this is the path a log line or
    # an exception message takes, where the key is text rather than a mapping
    # key. It is why the four indexed spellings are in SENSITIVE_KEYS
    # literally and not only as a base -- SENSITIVE_KEY_VALUE_RE ends each
    # alternative with (?![\w-]), so a bare "retNo" would not match "retNo1=".
    from korail_mobile_api.redaction import redact_text

    pairs = {
        "retNo1": FAKE_RETURN_SEGMENTS[0],
        "retNo2": FAKE_RETURN_SEGMENTS[1],
        "retNo3": FAKE_RETURN_SEGMENTS[2],
        "retNo4": FAKE_RETURN_SEGMENTS[3],
        "strName": FAKE_NAME,
        "custTeln": FAKE_PHONE,
        "ogtkRetPwd": FAKE_RETURN_PASSWORD,
        "prnNo": FAKE_PNR,
        "ogtkSaleWctNo": FAKE_WINDOW_NO,
        "non_member_phone": FAKE_PHONE,
    }
    line = ", ".join(f"{key}={value}" for key, value in pairs.items())
    redacted = redact_text(line)
    for secret in (
        *FAKE_RETURN_SEGMENTS,
        FAKE_NAME,
        FAKE_PHONE,
        FAKE_RETURN_PASSWORD,
        FAKE_PNR,
        FAKE_WINDOW_NO,
    ):
        assert secret not in redacted
    assert redacted.count("[REDACTED]") == len(pairs)
    # Each key itself survives, so a redacted line is still diagnosable.
    for key in pairs:
        assert f"{key}=[REDACTED]" in redacted
