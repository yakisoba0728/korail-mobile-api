"""A reservation CAN carry a 할인카드, through the ordinary reserve route.

``w4/a.java:93-104`` builds a plain ``ReservationRequest``; its only caller,
``SeatAssignBookingActivity.java:153-163``, hands it to
``NCardDirectInquiryActivity``, whose base class POSTs it with a plain
``ReservationDao`` (``c5/b.java:128-138``) to
``certification.TicketReservation``. There is no N카드 reservation endpoint.

NOTHING here has been transmitted to the live server.
"""

from __future__ import annotations

import httpx
import pytest

from korail_mobile_api import (
    KorailClient,
    KorailConfig,
    KorailMutationNotAllowedError,
    KorailProtocolError,
    KorailSession,
    MutationConsent,
    MutationPreview,
    ReservationHoldResponse,
    TrainSummary,
)
from korail_mobile_api.constants import (
    KORAIL_DISCOUNT_CARD_DISCOUNT_CODE,
    KORAIL_DISCOUNT_CARD_MENU_ID,
)
from korail_mobile_api.errors import KorailAuthError
from korail_mobile_api.mutation_payloads import (
    build_discount_card_reservation_form,
    build_reservation_form,
)
from korail_mobile_api.safety import KORAIL_MUTATION_ROUTE_CATEGORIES


ROUTE = "/classes/com.korail.mobile.certification.TicketReservation"
CARD_NO = "SYNTHETICCARD0001"

# OPsg.java:7-10. Note the trailing underscore on CARD_NO and on nothing else.
CARD_KEY = "txtCardNo_1"


def _train() -> TrainSummary:
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


def _refuse(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"nothing may be sent: {request.method} {request.url}")


def test_only_the_passenger_block_and_the_menu_id_differ():
    ordinary = build_reservation_form(KorailConfig(), _train())
    carded = build_discount_card_reservation_form(
        KorailConfig(),
        _train(),
        card_no=CARD_NO,
    )
    added = {name: carded[name] for name in carded if name not in ordinary}
    removed = {name for name in ordinary if name not in carded}
    changed = {
        name
        for name in carded
        if name in ordinary and carded[name] != ordinary[name]
    }
    # w4/a.java:96-101 -- one row carrying the card, and nothing else new.
    assert added == {CARD_KEY: CARD_NO}
    # The other seven of the eight rows are gone; row 1 survives with new
    # values, which is why it shows up under `changed` rather than `removed`.
    assert removed == {
        f"{prefix}{index}"
        for prefix in ("txtCompaCnt", "txtPsgTpCd", "txtDiscKndCd")
        for index in range(2, 9)
    }
    # SeatAssignBookingActivity.java:159 -- "A2", not "11".
    assert changed == {"txtMenuId", "txtDiscKndCd1"}
    assert carded["txtMenuId"] == KORAIL_DISCOUNT_CARD_MENU_ID == "A2"
    assert carded["txtDiscKndCd1"] == KORAIL_DISCOUNT_CARD_DISCOUNT_CODE == "153"
    assert carded["txtTotPsgCnt"] == "1"
    assert carded["txtCompaCnt1"] == "1"
    assert carded["txtPsgTpCd1"] == "1"


def test_the_journey_and_seat_blocks_are_byte_identical_and_in_position():
    ordinary = build_reservation_form(KorailConfig(), _train())
    carded = build_discount_card_reservation_form(
        KorailConfig(),
        _train(),
        card_no=CARD_NO,
    )
    # c5/b.java:42-77 writes OJrny and OSeat for an N카드 hold with exactly the
    # code that writes them for an ordinary one, so every key from the seat
    # block onwards must match in value AND in order.
    def tail(form: dict[str, str]) -> list[tuple[str, str]]:
        names = list(form)
        start = names.index("txtSeatAttCd1")
        return [(name, form[name]) for name in names[start:]]

    assert tail(carded) == tail(ordinary)
    # ...and the head is untouched too, apart from the menu id.
    head_names = list(carded)[: list(carded).index("txtTotPsgCnt")]
    assert head_names == list(ordinary)[: list(ordinary).index("txtTotPsgCnt")]
    assert carded["txtJobId"] == ordinary["txtJobId"] == "1101"
    assert carded["txtStndFlg"] == ordinary["txtStndFlg"]
    assert carded["hidFreeFlg"] == ordinary["hidFreeFlg"]
    assert carded["txtGdNo"] == ordinary["txtGdNo"]
    assert carded["txtPsrmClCd1"] == "1"


def test_the_card_key_spelling_is_the_odd_one_out():
    carded = build_discount_card_reservation_form(
        KorailConfig(),
        _train(),
        card_no=CARD_NO,
    )
    # OPsg.CARD_NO is "txtCardNo_" WITH a trailing underscore while COMPA_CNT,
    # PSG_TP_CD and DISC_KND_CD have none (OPsg.java:7-10). Getting this wrong
    # would send a discounted hold with no card attached.
    assert CARD_KEY in carded
    assert "txtCardNo1" not in carded


def test_the_builder_refuses_an_empty_card():
    for card_no in ("", "   ", None, 1234):
        with pytest.raises(KorailProtocolError):
            build_discount_card_reservation_form(
                KorailConfig(),
                _train(),
                card_no=card_no,
            )


def test_it_is_a_reserve_and_is_gated_as_one():
    # Same route, so necessarily the same category: a discount card does not
    # make a reservation something other than a reservation.
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[ROUTE] == "reserve"
    client = _client(_refuse)
    try:
        for consent in (
            None,
            MutationConsent(),
            MutationConsent(allow_discount_card=True, dry_run=False),
            MutationConsent(allow_payment=True, dry_run=False),
        ):
            with pytest.raises(KorailMutationNotAllowedError):
                client.reserve_with_discount_card(
                    _train(),
                    card_no=CARD_NO,
                    consent=consent,
                )
        preview = client.reserve_with_discount_card(
            _train(),
            card_no=CARD_NO,
            consent=MutationConsent(allow_reserve=True),
        )
        assert type(preview) is MutationPreview
        assert preview.category == "reserve"
        assert preview.route == ROUTE
        assert CARD_NO not in str(preview.payload)
    finally:
        client.close()


def test_it_requires_a_session():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.reserve_with_discount_card(
                _train(),
                card_no=CARD_NO,
                consent=MutationConsent(allow_reserve=True),
            )
    finally:
        client.close()


def test_an_acknowledged_send_posts_the_card_row_to_the_reserve_route():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRR000018",
                "h_msg_txt": "예약이 완료되었습니다",
                "strResult": "SUCC",
                "h_pnr_no": "SYNTHETIC_PNR",
                "h_jrny_cnt": "0001",
                "h_wct_no": "0001",
                "h_tot_rcvd_amt": "20000",
            },
        )

    client = _client(handler)
    try:
        hold = client.reserve_with_discount_card(
            _train(),
            card_no=CARD_NO,
            consent=MutationConsent(allow_reserve=True, dry_run=False),
        )
    finally:
        client.close()

    assert type(hold) is ReservationHoldResponse
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == ROUTE
    body = seen[0].content.decode()
    assert f"{CARD_KEY}={CARD_NO}" in body
    assert "txtDiscKndCd1=153" in body
    assert "txtMenuId=A2" in body
    # No second passenger row leaked through.
    assert "txtCompaCnt2" not in body


def test_the_ordinary_reserve_path_is_completely_unchanged():
    # The whole point of building this by substitution: adding a discount-card
    # hold must not have moved a single byte of the live-verified form.
    expected_menu_id = "11"
    ordinary = build_reservation_form(KorailConfig(), _train())
    assert ordinary["txtMenuId"] == expected_menu_id
    assert CARD_KEY not in ordinary
    assert ordinary["txtDiscKndCd1"] == "000"
    assert [name for name in ordinary if name.startswith("txtCompaCnt")] == [
        f"txtCompaCnt{index}" for index in range(1, 9)
    ]


def test_the_outbound_card_key_is_redacted():
    # The card number is spendable: w4/a.java:100-101 books a discounted seat
    # with nothing but this key and the code "153". It must not survive into a
    # preview, a log line or an error message.
    from korail_mobile_api.redaction import redact_mapping, redact_payload

    form = build_discount_card_reservation_form(
        KorailConfig(),
        _train(),
        card_no=CARD_NO,
    )
    assert CARD_NO not in str(redact_payload(form))
    assert CARD_NO not in str(redact_mapping({CARD_KEY: CARD_NO}))
