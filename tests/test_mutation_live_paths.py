"""Offline contract tests for the live mutation send paths.

These exercise `reserve(dry_run=False)`, `cancel_unpaid_hold(dry_run=False)`,
and the double-gated `KorailHttpClient.post_mutation_form` against an
`httpx.MockTransport` that records requests and returns synthetic envelopes.
No real network, no real credentials, no real card. They prove that a live
mutation goes ONLY to the evidenced mutation route, only with a non-dry-run
consent that opts into the category, and that the read-only path still refuses
every mutation route.
"""

from __future__ import annotations

import httpx
import pytest

from korail_mobile_api import (
    BaseKorailResponse,
    CardPayment,
    KorailClient,
    KorailConfig,
    KorailMutationNotAllowedError,
    KorailProtocolError,
    KorailSession,
    MutationConsent,
    MutationPreview,
    PaidTicket,
    ReservationHoldResponse,
    ReservationPaymentResponse,
    TrainSummary,
)
from korail_mobile_api.mutation_payloads import (
    build_card_payment_form,
    build_single_adult_reservation_form,
)


RESERVE_ROUTE = "/classes/com.korail.mobile.certification.TicketReservation"
CANCEL_ROUTE = (
    "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk"
)
PAYMENT_ROUTE = "/classes/com.korail.mobile.payment.ReservationPayment"

# Synthetic, non-secret placeholders.
SYNTHETIC_PNR = "SYNTHETIC_PNR_REFERENCE"

_HOLD_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRR000000",
    "h_msg_txt": "success",
    "h_pnr_no": SYNTHETIC_PNR,
    "h_jrny_cnt": "1",
    "h_wct_no": "SYNTHETIC_WINDOW",
    "h_tmp_job_sqno1": "SYNTHETIC_JOB_1",
    "h_tmp_job_sqno2": "SYNTHETIC_JOB_2",
    "h_payment_flg": "Y",
    "h_tot_prc": "8400",
    # Display total and settled total deliberately differ, so a builder that
    # regressed to h_tot_prc would be caught rather than silently pass.
    "h_tot_rcvd_amt": "7560",
    # h_rsv_chg_no deliberately NOT "000", so a payment builder that regressed
    # to the constant fallback would be caught. The second journey carries a
    # different one to pin the app's .get(0) indexing (V4/b.java:41).
    "jrny_infos": {
        "jrny_info": [
            {"h_jrny_sqno": "0001", "h_rsv_chg_no": "001"},
            {"h_jrny_sqno": "0002", "h_rsv_chg_no": "019"},
        ]
    },
}

_CANCEL_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRP000000",
    "h_msg_txt": "cancelled",
}


def _eligible_train() -> TrainSummary:
    return TrainSummary(
        train_no="00209",
        train_group_code="100",
        departure_station_code="0001",
        arrival_station_code="0501",
        departure_date="20990101",
        departure_time="100700",
        arrival_time="102400",
        run_date="20990101",
        train_class_code="00",
        departure_run_order="1",
        arrival_run_order="2",
        general_reservation_code="11",
        departure_construction_order="1",
        arrival_construction_order="2",
        seat_attribute_code="015",
    )


class _Recorder:
    """A MockTransport handler that records requests and replies by path."""

    def __init__(self, replies: dict[str, dict]) -> None:
        self.replies = replies
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        reply = self.replies.get(request.url.path)
        if reply is None:  # pragma: no cover - guards test wiring mistakes
            raise AssertionError(f"unexpected request to {request.url.path}")
        return httpx.Response(200, json=reply)


def _client_with(replies: dict[str, dict]) -> tuple[KorailClient, _Recorder]:
    recorder = _Recorder(replies)
    client = KorailClient(transport=httpx.MockTransport(recorder))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client, recorder


def _live(**allow: bool) -> MutationConsent:
    return MutationConsent(dry_run=False, **allow)


# --- reserve(dry_run=False) live send --------------------------------------


def test_reserve_live_posts_to_reservation_route_and_returns_hold():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    hold = client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert isinstance(hold, ReservationHoldResponse)
    assert hold.str_result == "SUCC"
    assert hold.pnr_no == SYNTHETIC_PNR
    assert hold.journey_count == "1"
    # Exactly one request, and it went to the mutation route via POST.
    assert len(recorder.requests) == 1
    assert recorder.requests[0].method == "POST"
    assert recorder.requests[0].url.path == RESERVE_ROUTE


def test_reserve_live_still_requires_matching_consent():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    # dry_run=False but no allow_reserve: denied before any send.
    with pytest.raises(KorailMutationNotAllowedError):
        client.reserve(_eligible_train(), consent=_live(allow_cancel=True))
    assert recorder.requests == []


def test_reserve_live_raises_app_error_on_fail_envelope_and_holds_nothing():
    client, recorder = _client_with(
        {
            RESERVE_ROUTE: {
                "strResult": "FAIL",
                "h_msg_cd": "WRC000288",
                "h_msg_txt": "no seat",
            }
        }
    )
    from korail_mobile_api import KorailAppError

    with pytest.raises(KorailAppError):
        client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert len(recorder.requests) == 1


# --- cancel_unpaid_hold ------------------------------------------------------


def _hold() -> ReservationHoldResponse:
    from korail_mobile_api.mutation_parsers import (
        parse_reservation_hold_response,
    )

    return parse_reservation_hold_response(dict(_HOLD_SUCCESS))


def test_cancel_dry_run_returns_redacted_preview_without_sending():
    client, recorder = _client_with({})
    preview = client.cancel_unpaid_hold(
        _hold(), consent=MutationConsent(allow_cancel=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "cancel"
    assert preview.route == CANCEL_ROUTE
    # PNR is redacted in the preview payload; nothing was sent.
    assert preview.payload["txtPnrNo"] == "[REDACTED]"
    assert recorder.requests == []


def test_cancel_live_posts_to_cancel_route():
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    result = client.cancel_unpaid_hold(_hold(), consent=_live(allow_cancel=True))
    assert isinstance(result, BaseKorailResponse)
    assert result.str_result == "SUCC"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == CANCEL_ROUTE


def test_cancel_requires_matching_consent_and_session():
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    with pytest.raises(KorailMutationNotAllowedError):
        client.cancel_unpaid_hold(_hold(), consent=MutationConsent())
    assert recorder.requests == []

    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({CANCEL_ROUTE: _CANCEL_SUCCESS}))
    )
    from korail_mobile_api import KorailAuthError

    with pytest.raises(KorailAuthError):
        logged_out.cancel_unpaid_hold(
            _hold(), consent=_live(allow_cancel=True)
        )


# --- post_mutation_form double-gate -----------------------------------------


def test_post_mutation_form_refuses_a_non_mutation_route():
    client, recorder = _client_with({})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    # A read route (or any non-mutation route) is rejected by assert_mutation_route.
    with pytest.raises(KorailProtocolError):
        client.http.post_mutation_form(
            "/classes/com.korail.mobile.myTicket.MyTicketList",
            form,
            consent=_live(allow_reserve=True),
            category="reserve",
        )
    assert recorder.requests == []


def test_post_mutation_form_refuses_none_and_unknown_category():
    client, recorder = _client_with({RESERVE_ROUTE: _HOLD_SUCCESS})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    with pytest.raises(KorailMutationNotAllowedError):
        client.http.post_mutation_form(
            RESERVE_ROUTE, form, consent=None, category="reserve"  # type: ignore[arg-type]
        )
    with pytest.raises(KorailMutationNotAllowedError):
        client.http.post_mutation_form(
            RESERVE_ROUTE,
            form,
            consent=_live(allow_reserve=True),
            category="checkin",
        )
    assert recorder.requests == []


def test_reserve_returns_cancelable_hold_even_if_optional_field_malformed():
    # The server created a real hold (PNR present) but an unrelated optional
    # field is malformed, so strict parsing would raise. reserve must still
    # return a hold carrying the PNR + journey count so it can be auto-cancelled.
    malformed = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        "h_msg_txt": "success",
        "h_pnr_no": SYNTHETIC_PNR,
        "h_jrny_cnt": "1",
        # An OBJECT where a scalar belongs. A bare int would no longer do: the
        # parser now normalises a JSON number, because KORAIL genuinely sends
        # one. This has to be a shape the parser still rejects, or the test
        # stops exercising the fallback it is named for.
        "h_tot_prc": {"amount": 8400},
    }
    client, _recorder = _client_with({RESERVE_ROUTE: malformed})
    hold = client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert isinstance(hold, ReservationHoldResponse)
    assert hold.pnr_no == SYNTHETIC_PNR
    assert hold.journey_count == "1"
    assert hold.str_result == "SUCC"
    # And that recovered hold is acceptable to cancel_unpaid_hold.
    client2, _recorder2 = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    result = client2.cancel_unpaid_hold(hold, consent=_live(allow_cancel=True))
    assert result.str_result == "SUCC"


def test_reserve_recovers_a_hold_whose_pnr_arrived_as_a_json_number():
    # The last-ditch fallback must apply the same string-or-number tolerance the
    # parser does. A PNR is 15 decimal digits; if one ever arrives unquoted
    # alongside a genuinely malformed field, discarding it would orphan a real
    # hold -- the exact outcome this fallback exists to prevent.
    malformed = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        "h_msg_txt": "success",
        "h_pnr_no": 399999999999999,
        "h_jrny_cnt": 1,
        "h_tot_prc": {"amount": 8400},
    }
    client, _ = _client_with({RESERVE_ROUTE: malformed})
    hold = client.reserve(_eligible_train(), consent=_live(allow_reserve=True))
    assert hold.pnr_no == "399999999999999"
    assert hold.journey_count == "1"
    client2, _ = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    assert (
        client2.cancel_unpaid_hold(
            hold, consent=_live(allow_cancel=True)
        ).str_result
        == "SUCC"
    )


def test_reserve_reraises_when_no_pnr_returned():
    # A malformed response with NO PNR means no hold to orphan: re-raise.
    no_pnr = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        # A missing envelope field triggers the strict-parse failure; no
        # h_pnr_no is present, so there is no hold to protect.
        "h_tot_prc": {"amount": 8400},
    }
    client, _ = _client_with({RESERVE_ROUTE: no_pnr})
    with pytest.raises(KorailProtocolError):
        client.reserve(_eligible_train(), consent=_live(allow_reserve=True))


def test_post_mutation_form_rejects_category_route_mismatch():
    # A consent/category for one route cannot be used to POST another route.
    client, recorder = _client_with({CANCEL_ROUTE: _CANCEL_SUCCESS})
    form = build_single_adult_reservation_form(KorailConfig(), _eligible_train())
    with pytest.raises(KorailProtocolError):
        client.http.post_mutation_form(
            CANCEL_ROUTE,  # cancel route ...
            form,
            consent=_live(allow_reserve=True),
            category="reserve",  # ... but a reserve category
        )
    assert recorder.requests == []


def _paid_hold() -> ReservationHoldResponse:
    return ReservationHoldResponse(
        h_msg_cd="IRR000018",
        str_result="SUCC",
        raw={},
        pnr_no=SYNTHETIC_PNR,
        journey_count="0001",
        window_no="SYNTHETIC_WCT",
        temporary_job_sequence_1="SYNTHETIC_JOB_1",
        temporary_job_sequence_2="SYNTHETIC_JOB_2",
        total_price="8400",
        received_amount="7560",
    )


def _fake_card() -> CardPayment:
    return CardPayment(
        card_number="0000000000000000",
        card_password="00",
        card_expire="2612",
        birthday="900101",
    )


_PAYMENT_DECLINE = {
    "strResult": "FAIL",
    "h_msg_cd": "WRC000123",
    "h_msg_txt": "card declined",
}


def test_pay_dry_run_preview_redacts_card_and_sends_nothing():
    client, recorder = _client_with({})
    preview = client.pay_with_fake_card(
        _paid_hold(), _fake_card(), consent=MutationConsent(allow_payment=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "payment"
    assert preview.route == PAYMENT_ROUTE
    # Raw PAN, card secrets, and reservation identity are never present.
    for key in (
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        "hidAthnVal1",
        "hidAthnDvCd1",
        "hidIsmtMnthNum1",
        "hidPnrNo",
        "hidWctNo",
        "hidTmpJobSqno1",
        "hidTmpJobSqno2",
    ):
        assert preview.payload[key] == "[REDACTED]", key
    joined = "".join(preview.payload.values())
    for secret in ("0000000000000000", "2612", "900101", SYNTHETIC_PNR):
        assert secret not in joined, secret
    assert recorder.requests == []


def test_payment_form_from_a_parsed_hold_carries_that_holds_reservation_state():
    # End to end from the reserve response the server actually returned: the
    # temporary job sequences and the settled amount both come off the parsed
    # hold, not from constants baked into the builder.
    form = build_card_payment_form(KorailConfig(), _hold(), _fake_card())
    assert form["hidTmpJobSqno1"] == _HOLD_SUCCESS["h_tmp_job_sqno1"]
    assert form["hidTmpJobSqno2"] == _HOLD_SUCCESS["h_tmp_job_sqno2"]
    assert form["hidMnsStlAmt1"] == _HOLD_SUCCESS["h_tot_rcvd_amt"]
    assert form["hidMnsStlAmt1"] != _HOLD_SUCCESS["h_tot_prc"]
    # hidRsvChgNo comes off the FIRST journey of the parsed response
    # (V4/b.java:41 indexes .get(0)), not the constant and not the second row.
    journeys = _HOLD_SUCCESS["jrny_infos"]["jrny_info"]
    assert form["hidRsvChgNo"] == journeys[0]["h_rsv_chg_no"]
    assert form["hidRsvChgNo"] != journeys[1]["h_rsv_chg_no"]
    assert form["hidRsvChgNo"] != "000"


def test_cancel_form_from_a_parsed_hold_keeps_the_apps_fixed_change_no():
    # Same parsed hold, opposite decision: the app's fresh-hold cancel flows
    # hardcode "000" even holding the ReservationResponse
    # (DReservationConfirmActivity.java:270-279,
    # ReservationWaitActivity.java:118-128, a6/x.java:97-106), so the parsed
    # change number must not reach the cancel wire.
    from korail_mobile_api.mutation_payloads import (
        build_unpaid_reservation_cancel_form,
    )

    hold = _hold()
    assert hold.journeys[0].reservation_change_no == "001"
    form = build_unpaid_reservation_cancel_form(KorailConfig(), hold)
    assert form["hidRsvChgNo"] == "000"


def test_post_mutation_form_refuses_real_card_payment_at_the_send_gate():
    # Defense-in-depth: even a hand-assembled low-level call cannot transmit a
    # payment with fake_card_only disabled. The transport gate itself refuses.
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_DECLINE})
    form = build_card_payment_form(KorailConfig(), _paid_hold(), _fake_card())
    with pytest.raises(KorailMutationNotAllowedError):
        client.http.post_mutation_form(
            PAYMENT_ROUTE,
            form,
            consent=MutationConsent(
                allow_payment=True, dry_run=False, fake_card_only=False
            ),
            category="payment",
        )
    assert recorder.requests == []


def test_pay_live_posts_to_payment_route_and_returns_decline_without_raising():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_DECLINE})
    result = client.pay_with_fake_card(
        _paid_hold(),
        _fake_card(),
        consent=MutationConsent(allow_payment=True, dry_run=False),
    )
    # A decline is a FAIL envelope; pay must NOT raise, so the caller sees it.
    assert isinstance(result, ReservationPaymentResponse)
    assert result.str_result == "FAIL"
    assert result.h_msg_cd == "WRC000123"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == PAYMENT_ROUTE


def test_pay_requires_payment_consent_and_refuses_real_card_mode():
    client, recorder = _client_with({PAYMENT_ROUTE: _PAYMENT_DECLINE})
    # Wrong category consent -> denied.
    with pytest.raises(KorailMutationNotAllowedError):
        client.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(allow_reserve=True, dry_run=False),
        )
    # payment allowed but fake_card_only disabled -> refused (no real cards).
    with pytest.raises(KorailMutationNotAllowedError):
        client.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(
                allow_payment=True, dry_run=False, fake_card_only=False
            ),
        )
    assert recorder.requests == []


def test_pay_requires_authenticated_session():
    from korail_mobile_api import KorailAuthError

    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({PAYMENT_ROUTE: _PAYMENT_DECLINE}))
    )
    with pytest.raises(KorailAuthError):
        logged_out.pay_with_fake_card(
            _paid_hold(),
            _fake_card(),
            consent=MutationConsent(allow_payment=True, dry_run=False),
        )


REFUND_ROUTE = "/classes/com.korail.mobile.refunds.RefundsRequest"

_REFUND_SUCCESS = {
    "strResult": "SUCC",
    "h_msg_cd": "IRG000000",
    "h_msg_txt": "refunded",
}


def _paid_ticket() -> PaidTicket:
    return PaidTicket(
        pnr_no=SYNTHETIC_PNR,
        sale_date="20260725",
        sale_window_no="SYNTHETIC_WCT",
        sale_sequence="0001",
        return_password="SYNTHETIC_RETPWD",
        train_no="00209",
    )


def test_refund_dry_run_preview_redacts_ticket_identity_without_sending():
    client, recorder = _client_with({})
    preview = client.refund(
        _paid_ticket(), consent=MutationConsent(allow_refund=True)
    )
    assert isinstance(preview, MutationPreview)
    assert preview.category == "refund"
    assert preview.route == REFUND_ROUTE
    for key in (
        "txtPnrNo",
        "h_orgtk_sale_dt",
        "h_orgtk_sale_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
    ):
        assert preview.payload[key] == "[REDACTED]", key
    joined = "".join(preview.payload.values())
    for secret in (SYNTHETIC_PNR, "SYNTHETIC_RETPWD", "SYNTHETIC_WCT"):
        assert secret not in joined, secret
    assert recorder.requests == []


def test_refund_live_posts_to_refund_route():
    client, recorder = _client_with({REFUND_ROUTE: _REFUND_SUCCESS})
    result = client.refund(
        _paid_ticket(),
        consent=MutationConsent(allow_refund=True, dry_run=False),
    )
    assert isinstance(result, BaseKorailResponse)
    assert result.str_result == "SUCC"
    assert len(recorder.requests) == 1
    assert recorder.requests[0].url.path == REFUND_ROUTE


def test_refund_requires_matching_consent_and_session():
    client, recorder = _client_with({REFUND_ROUTE: _REFUND_SUCCESS})
    with pytest.raises(KorailMutationNotAllowedError):
        client.refund(_paid_ticket(), consent=MutationConsent(allow_cancel=True))
    assert recorder.requests == []

    from korail_mobile_api import KorailAuthError

    logged_out = KorailClient(
        transport=httpx.MockTransport(_Recorder({REFUND_ROUTE: _REFUND_SUCCESS}))
    )
    with pytest.raises(KorailAuthError):
        logged_out.refund(
            _paid_ticket(),
            consent=MutationConsent(allow_refund=True, dry_run=False),
        )


def test_read_only_post_form_still_refuses_mutation_routes():
    # The enduring guarantee: the read-only send path rejects mutation routes,
    # so a mutation can only ever leave through post_mutation_form.
    client, _ = _client_with({})
    for route in (RESERVE_ROUTE, CANCEL_ROUTE, PAYMENT_ROUTE, REFUND_ROUTE):
        with pytest.raises(KorailProtocolError):
            client.http.post_form(route, {"x": "1"})


# --- reserve -> auto-cancel round trip (offline model of the live flow) ------


def test_reserve_then_auto_cancel_round_trip_offline():
    client, recorder = _client_with(
        {RESERVE_ROUTE: _HOLD_SUCCESS, CANCEL_ROUTE: _CANCEL_SUCCESS}
    )
    consent = _live(allow_reserve=True, allow_cancel=True)
    hold = client.reserve(_eligible_train(), consent=consent)
    assert isinstance(hold, ReservationHoldResponse)
    cancel = client.cancel_unpaid_hold(hold, consent=consent)
    assert cancel.str_result == "SUCC"
    assert [r.url.path for r in recorder.requests] == [
        RESERVE_ROUTE,
        CANCEL_ROUTE,
    ]
