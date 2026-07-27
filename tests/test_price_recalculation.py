from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.consent import (
    MUTATION_CATEGORIES,
    MutationConsent,
    MutationPreview,
    require_mutation_consent,
)
from korail_mobile_api.constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
    MutationNotAllowedError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.mutation_models import (
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
)
from korail_mobile_api.mutation_payloads import build_price_recalculation_form
from korail_mobile_api.redaction import SENSITIVE_KEYS, redact_payload
from korail_mobile_api.safety import (
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


ROUTE = "/classes/com.korail.mobile.certification.PriceReCalculation"

OTHER_CATEGORIES = (
    "reserve",
    "payment",
    "cancel",
    "refund",
    "discount_card",
)
OTHER_FLAGS = (
    "allow_reserve",
    "allow_payment",
    "allow_cancel",
    "allow_refund",
    "allow_discount_card",
)

ALLOWED = MutationConsent(allow_price_recalculation=True, dry_run=False)
DRY_RUN = MutationConsent(allow_price_recalculation=True)

# The six @Field names of getDiscountPrice that carry a List<String>, in the
# order CertificationService.java:35-37 declares them.
LIST_FIELDS = (
    "psg_tp_dv_cd",
    "hidDcntKndCd",
    "dcnt_knd_cd1",
    "hidDscpNo",
    "psrm_cl_cd",
    "hidFmlyNo",
)


def _row(**overrides: object) -> PriceRecalculationRow:
    fields: dict[str, object] = {
        "passenger_type_code": "1",
        "room_class_code": "1",
        "discount_kind_code": "000",
    }
    fields.update(overrides)
    return PriceRecalculationRow(**fields)  # type: ignore[arg-type]


def _request(**overrides: object) -> PriceRecalculationRequest:
    fields: dict[str, object] = {
        "pnr_no": "SYNTHETIC_PNR",
        "rows": (_row(), _row(passenger_type_code="3")),
    }
    fields.update(overrides)
    return PriceRecalculationRequest(**fields)  # type: ignore[arg-type]


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


# --- consent category -------------------------------------------------------


def test_price_recalculation_is_its_own_consent_category():
    assert "price_recalculation" in MUTATION_CATEGORIES
    assert len(MUTATION_CATEGORIES) == 7
    # A default consent grants it no more than it grants anything else.
    assert MutationConsent().allow_price_recalculation is False
    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(MutationConsent(), "price_recalculation")
    # ...and no other category's opt-in unlocks it. allow_payment is the one
    # that matters most: a consent to settle a quoted amount must not also
    # authorise rewriting what that amount is.
    for other in OTHER_FLAGS:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(**{other: True}),
                "price_recalculation",
            )
    require_mutation_consent(
        MutationConsent(allow_price_recalculation=True),
        "price_recalculation",
    )
    # ...and it unlocks nothing else.
    for category in OTHER_CATEGORIES:
        with pytest.raises(MutationNotAllowedError):
            require_mutation_consent(
                MutationConsent(allow_price_recalculation=True),
                category,
            )


def test_route_is_a_mutation_route_owned_by_that_category():
    assert ("POST", ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("GET", ROUTE) not in KORAIL_MUTATION_ROUTES
    assert len(KORAIL_MUTATION_ROUTES) == 9
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[ROUTE] == "price_recalculation"
    assert_mutation_route("POST", ROUTE)
    assert_mutation_route_category(ROUTE, "price_recalculation")
    # A consent for another category can never be redirected onto this route.
    for wrong in OTHER_CATEGORIES:
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(ROUTE, wrong)
    # The read-only guarantee stays intact.
    assert ("POST", ROUTE) not in KORAIL_READ_ONLY_ROUTES
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", ROUTE)


def test_category_carries_no_card_and_never_reaches_the_card_gate():
    # The form has no PAN: its fourteen @Fields are a PNR, a job id, a member
    # flag/number, a row count and six code/number lists
    # (CertificationService.java:35-37). It must therefore NOT be registered
    # as card-bearing, or the payment gate would demand a card kind it has no
    # card for.
    assert "price_recalculation" not in KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    assert KORAIL_CARD_BEARING_MUTATION_CATEGORIES <= set(MUTATION_CATEGORIES)


# --- the form ---------------------------------------------------------------


def test_member_form_is_the_twelve_fields_retrofit_would_send():
    form = build_price_recalculation_form(KorailConfig(), _request())
    # hiduserYn/hidCustNo are absent: k2() writes them only for a non-member
    # (a6/C1042B.java:290-293) and Retrofit omits a null @Field entirely.
    assert set(form) == {
        "Device",
        "Version",
        "Key",
        "hidPnrNo",
        "txtJobId",
        "txtPsgGridcnt",
        *LIST_FIELDS,
    }
    assert form["hidPnrNo"] == "SYNTHETIC_PNR"
    assert form["txtJobId"] == "1101"
    assert form["txtPsgGridcnt"] == "2"


def test_non_member_form_adds_exactly_the_two_member_fields():
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(non_member_no="SYNTHETIC_NONMEMBER"),
    )
    assert set(form) == {
        "Device",
        "Version",
        "Key",
        "hidPnrNo",
        "txtJobId",
        "hiduserYn",
        "hidCustNo",
        "txtPsgGridcnt",
        *LIST_FIELDS,
    }
    # The pair is written together, and the flag is the literal "N".
    assert form["hiduserYn"] == "N"
    assert form["hidCustNo"] == "SYNTHETIC_NONMEMBER"


def test_the_six_lists_are_index_aligned_one_row_per_seat():
    rows = (
        _row(
            passenger_type_code="1",
            room_class_code="1",
            discount_kind_code="000",
            requested_discount_code="151",
            certificate_no="SYNTHETIC_COUPON",
            family_sequence_no="",
        ),
        _row(
            passenger_type_code="3",
            room_class_code="2",
            discount_kind_code="321",
            requested_discount_code="",
            certificate_no="",
            family_sequence_no="SYNTHETIC_FMLY",
        ),
        _row(
            passenger_type_code="1",
            room_class_code="1",
            discount_kind_code="432",
            requested_discount_code="",
            certificate_no="",
            family_sequence_no="",
        ),
    )
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(rows=rows),
    )
    # Column by column, in row order: this is exactly what k2()'s single loop
    # over the DiscountPriceParams[] appends (a6/C1042B.java:275-283).
    assert form["psg_tp_dv_cd"] == ["1", "3", "1"]
    assert form["hidDcntKndCd"] == ["151", "", ""]
    assert form["dcnt_knd_cd1"] == ["000", "321", "432"]
    assert form["hidDscpNo"] == ["SYNTHETIC_COUPON", "", ""]
    assert form["psrm_cl_cd"] == ["1", "2", "1"]
    assert form["hidFmlyNo"] == ["", "SYNTHETIC_FMLY", ""]
    # Every list has one entry per row, and txtPsgGridcnt says how many.
    assert form["txtPsgGridcnt"] == "3"
    for name in LIST_FIELDS:
        assert len(form[name]) == len(rows)


def test_lists_go_out_as_repeated_keys_not_indexed_ones():
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(rows=(_row(), _row(passenger_type_code="3"))),
    )
    body = httpx.Request("POST", "https://example.invalid/x", data=form).read()
    pairs = parse_qsl(body.decode(), keep_blank_values=True)
    # The name repeats verbatim: RequestBuilder.smali:1537-1601 iterates the
    # Iterable and calls addField(v3, element) with v3 -- the field name --
    # loop-invariant. No "[]", no index suffix, no JSON.
    assert [value for name, value in pairs if name == "psg_tp_dv_cd"] == [
        "1",
        "3",
    ]
    for name in LIST_FIELDS:
        assert sum(1 for key, _ in pairs if key == name) == 2
        assert f"{name}[]" not in body.decode()
        assert f"{name}1=" not in body.decode()
        assert f"{name}_1=" not in body.decode()
    # ...and the scalars stay scalar.
    for name in ("Device", "Version", "Key", "hidPnrNo", "txtJobId"):
        assert sum(1 for key, _ in pairs if key == name) == 1


def test_row_count_and_grid_count_cannot_disagree():
    for count in (1, 2, KORAIL_MAX_PASSENGERS_PER_RESERVATION):
        form = build_price_recalculation_form(
            KorailConfig(),
            _request(rows=tuple(_row() for _ in range(count))),
        )
        assert form["txtPsgGridcnt"] == str(count)
        for name in LIST_FIELDS:
            assert len(form[name]) == count


@pytest.mark.parametrize(
    "request_obj",
    [
        # Not the exact request type.
        "not a request",
        None,
        # No rows, and more rows than a reservation can hold.
        _request(rows=()),
        _request(
            rows=tuple(
                _row()
                for _ in range(KORAIL_MAX_PASSENGERS_PER_RESERVATION + 1)
            )
        ),
        # An empty PNR.
        _request(pnr_no=""),
        _request(pnr_no="   "),
        # A non-member number that is present but blank.
        _request(non_member_no=""),
        # Not the exact row type.
        _request(rows=("not a row",)),
        # None in any of the six: Retrofit DROPS a null list element
        # (RequestBuilder.smali:1559-1571), shortening one key against the
        # other five and re-pairing every later row.
        _request(rows=(_row(passenger_type_code=None),)),
        _request(rows=(_row(room_class_code=None),)),
        _request(rows=(_row(discount_kind_code=None),)),
        _request(rows=(_row(requested_discount_code=None),)),
        _request(rows=(_row(certificate_no=None),)),
        _request(rows=(_row(family_sequence_no=None),)),
        # A non-string is equally unsendable.
        _request(rows=(_row(passenger_type_code=1),)),
        # The three copied off the seat may not be blank.
        _request(rows=(_row(passenger_type_code=""),)),
        _request(rows=(_row(room_class_code=""),)),
        _request(rows=(_row(discount_kind_code=""),)),
        # 군장병 never travels in hidDcntKndCd: makeDiscountParams moves it to
        # dcnt_knd_cd1 and blanks this field (S4/D.java:181-183).
        _request(rows=(_row(requested_discount_code="432"),)),
        # An integrated 국가유공자 discount must clear dcnt_knd_cd1 to "000"
        # (S4/D.java:184-186 via T4/a.java:51-53 -> T4/b.java:46,62).
        _request(
            rows=(
                _row(
                    requested_discount_code="151",
                    certificate_no="5100001",
                    discount_kind_code="202",
                ),
            )
        ),
        _request(
            rows=(
                _row(
                    requested_discount_code="152",
                    certificate_no="5100001",
                    discount_kind_code="202",
                ),
            )
        ),
    ],
)
def test_unsendable_shapes_are_refused(request_obj: object):
    with pytest.raises(KorailProtocolError):
        build_price_recalculation_form(KorailConfig(), request_obj)


def test_the_merit_rule_only_fires_on_the_combination_that_earns_it():
    # "151" with a certificate that is NOT a 51-prefixed one is an ordinary
    # coupon row, and keeps the seat's existing discount code.
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(
            rows=(
                _row(
                    requested_discount_code="151",
                    certificate_no="9900001",
                    discount_kind_code="202",
                ),
            )
        ),
    )
    assert form["dcnt_knd_cd1"] == ["202"]
    # ...and a 51-prefixed certificate under a non-merit discount kind is not
    # an integrated merit discount either.
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(
            rows=(
                _row(
                    requested_discount_code="401",
                    certificate_no="5100001",
                    discount_kind_code="202",
                ),
            )
        ),
    )
    assert form["dcnt_knd_cd1"] == ["202"]
    # The combination that does earn it is accepted when it clears the code.
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(
            rows=(
                _row(
                    requested_discount_code="152",
                    certificate_no="5100001",
                    discount_kind_code="000",
                ),
            )
        ),
    )
    assert form["dcnt_knd_cd1"] == ["000"]


# --- redaction --------------------------------------------------------------


def test_every_credential_bearing_key_of_this_form_is_redacted():
    for key in ("hidPnrNo", "hidCustNo", "hidDscpNo", "hidFmlyNo", "psrm_cl_cd"):
        assert key.casefold() in SENSITIVE_KEYS
    form = build_price_recalculation_form(
        KorailConfig(),
        _request(
            non_member_no="SYNTHETIC_NONMEMBER",
            rows=(
                _row(certificate_no="SYNTHETIC_COUPON"),
                _row(family_sequence_no="SYNTHETIC_FMLY"),
            ),
        ),
    )
    redacted = redact_payload(form)
    rendered = str(redacted)
    for secret in (
        "SYNTHETIC_PNR",
        "SYNTHETIC_NONMEMBER",
        "SYNTHETIC_COUPON",
        "SYNTHETIC_FMLY",
    ):
        assert secret not in rendered
    # A list value stays a list of the same length, so the preview still shows
    # the wire shape rather than a Python repr of it. The length is not a
    # secret: it is txtPsgGridcnt, which travels in the clear beside it.
    assert redacted["hidDscpNo"] == ["[REDACTED]", "[REDACTED]"]
    assert redacted["psg_tp_dv_cd"] == ["1", "1"]
    assert redacted["txtPsgGridcnt"] == "2"


def test_a_secret_inside_a_list_cannot_hide_behind_the_brackets():
    # The failure this guards: str(["4111111111111111"]) used to be redacted as
    # one opaque string, so a value that CARD_RE would have masked survived
    # because it sat inside a list's quotes.
    redacted = redact_payload({"psg_tp_dv_cd": ["4111111111111111", "1"]})
    assert "4111111111111111" not in str(redacted)
    assert redacted["psg_tp_dv_cd"][1] == "1"


# --- the client method ------------------------------------------------------


def test_default_consent_previews_and_sends_nothing():
    client = _client(_refuse)
    try:
        preview = client.recalculate_price(
            _request(
                non_member_no="SYNTHETIC_NONMEMBER",
                rows=(_row(certificate_no="SYNTHETIC_COUPON"),),
            ),
            consent=DRY_RUN,
        )
        assert type(preview) is MutationPreview
        assert preview.category == "price_recalculation"
        assert preview.method == "POST"
        assert preview.route == ROUTE
        rendered = str(preview.payload)
        for secret in (
            "SYNTHETIC_PNR",
            "SYNTHETIC_NONMEMBER",
            "SYNTHETIC_COUPON",
        ):
            assert secret not in rendered
    finally:
        client.close()


def test_method_refuses_without_the_matching_consent():
    client = _client(_refuse)
    try:
        for consent in (
            None,
            MutationConsent(),
            MutationConsent(allow_reserve=True, dry_run=False),
            # The reuse that would have been dangerous.
            MutationConsent(allow_payment=True, dry_run=False),
            MutationConsent(allow_discount_card=True, dry_run=False),
        ):
            with pytest.raises(MutationNotAllowedError):
                client.recalculate_price(_request(), consent=consent)
    finally:
        client.close()


def test_method_requires_a_session_even_with_consent():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.recalculate_price(_request(), consent=DRY_RUN)
        with pytest.raises(KorailAuthError):
            client.recalculate_price(_request(), consent=ALLOWED)
    finally:
        client.close()


def test_an_acknowledged_send_transmits_the_repeated_key_body():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "정상처리되었습니다",
                "strResult": "SUCC",
                "h_pnr_no": "SYNTHETIC_PNR",
                "h_jrny_cnt": "1",
                "h_tot_frei": "60000",
                "h_tot_prc": "60000",
                "h_tot_rcvd_amt": "48000",
            },
        )

    client = _client(handler)
    try:
        repriced = client.recalculate_price(
            _request(rows=(_row(), _row(passenger_type_code="3"))),
            consent=ALLOWED,
        )
    finally:
        client.close()

    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == ROUTE
    pairs = parse_qsl(seen[0].read().decode(), keep_blank_values=True)
    assert [value for name, value in pairs if name == "psg_tp_dv_cd"] == [
        "1",
        "3",
    ]
    assert dict(pairs)["txtPsgGridcnt"] == "2"
    assert dict(pairs)["txtJobId"] == "1101"

    # The response is the app's ReservationResponse -- the same type a hold
    # returns -- so the re-priced amount arrives in received_amount.
    assert type(repriced) is ReservationHoldResponse
    assert repriced.received_amount == "48000"
    assert repriced.total_price == "60000"


def test_transport_gate_refuses_this_route_under_any_other_category():
    client = _client(_refuse)
    try:
        for category in OTHER_CATEGORIES:
            with pytest.raises(KorailProtocolError):
                client.http.post_mutation_form(
                    ROUTE,
                    {},
                    consent=MutationConsent(
                        allow_reserve=True,
                        allow_payment=True,
                        allow_cancel=True,
                        allow_refund=True,
                        allow_discount_card=True,
                        dry_run=False,
                    ),
                    category=category,
                )
        # ...and a dry-run consent never reaches the wire even with the right
        # category.
        with pytest.raises(MutationNotAllowedError):
            client.http.post_mutation_form(
                ROUTE,
                {},
                consent=DRY_RUN,
                category="price_recalculation",
            )
    finally:
        client.close()


# --- exports and live-path exclusion ----------------------------------------


def test_models_are_exported():
    for name in ("PriceRecalculationRequest", "PriceRecalculationRow"):
        assert hasattr(korail_mobile_api, name)
        assert name in korail_mobile_api.__all__


def test_no_live_path_reaches_this_category():
    root = Path(korail_mobile_api.__file__).parents[2]
    for relative in (
        "src/korail_mobile_api/live.py",
        "tests/test_live.py",
        "tests/test_live_service.py",
        "tests/test_mutation_live_paths.py",
        "scripts/reserve_pay_refund_roundtrip.py",
    ):
        source = (root / relative).read_text(encoding="utf-8")
        for name in (
            "recalculate_price",
            "allow_price_recalculation",
            "PriceReCalculation",
        ):
            assert name not in source, f"{relative} reaches {name}"
