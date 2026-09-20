# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path
from typing import get_args
from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from _helpers import make_authenticated_client as _client
from _helpers import refuse_transport as _refuse
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from korail_mobile_api.errors import (
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.mutation_models import (
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
)
from korail_mobile_api.mutation_payloads import build_price_recalculation_form
from korail_mobile_api.redaction import SENSITIVE_KEYS, redact_payload
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    MutationCategory,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


ROUTE = "/classes/com.korail.mobile.certification.PriceReCalculation"

# Every other category, read from MutationCategory so one added later is
# covered by the isolation tests below without editing them.
OTHER_CATEGORIES = tuple(
    category
    for category in get_args(MutationCategory)
    if category != "price_recalculation"
)

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


def test_route_is_a_mutation_route_owned_by_that_category():
    assert ("POST", ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("GET", ROUTE) not in KORAIL_MUTATION_ROUTES
    assert KORAIL_MUTATION_ROUTES.isdisjoint(KORAIL_READ_ONLY_ROUTES)
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[ROUTE] == "price_recalculation"
    assert_mutation_route("POST", ROUTE)
    assert_mutation_route_category(ROUTE, "price_recalculation")
    # A category declared for another route can never be redirected onto this one.
    for wrong in OTHER_CATEGORIES:
        with pytest.raises(KorailProtocolError):
            assert_mutation_route_category(ROUTE, wrong)
    # The read-only guarantee stays intact.
    assert ("POST", ROUTE) not in KORAIL_READ_ONLY_ROUTES
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", ROUTE)


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


def test_method_requires_a_session():
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(_refuse),
    )
    try:
        with pytest.raises(KorailAuthError):
            client.recalculate_price(_request())
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
                    category=category,
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
    # Every script, not one: each is an operator tool that talks to the live
    # server, and any of them could gain a call.
    scripts = sorted((root / "scripts").glob("*.py"))
    assert scripts, "no scripts found; the scan would pass on nothing"
    for path in (
        root / "src/korail_mobile_api/live.py",
        root / "tests/test_live.py",
        root / "tests/test_live_service.py",
        root / "tests/test_mutation_live_paths.py",
        *scripts,
    ):
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        for name in (
            "recalculate_price",
            "allow_price_recalculation",
            "PriceReCalculation",
        ):
            assert name not in source, f"{relative} reaches {name}"


_SESSION_EXPIRED = {
    "strResult": "FAIL",
    "h_msg_cd": "P058",
    "h_msg_txt": "session expired",
}


def test_an_expired_session_on_recalculate_price_clears_the_client_before_raising():
    # The same pin as test_mutation_live_paths.py's parametrized P058 test,
    # for recalculate_price: one request out, no session or cookie left after P058.
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_SESSION_EXPIRED)

    client = _client(handler)
    client.http.cookies.set(
        "JSESSIONID", "synthetic-secret", domain="smart.letskorail.com"
    )
    try:
        with pytest.raises(KorailSessionExpiredError):
            client.recalculate_price(_request())
    finally:
        client.close()
    assert len(seen) == 1
    assert client.session.current is None
    assert not client.http.cookies


def test_an_unparseable_recalculation_raises_even_with_a_pnr():
    # The reserve methods fall back to a PNR-only hold when a live answer will
    # not parse, because a new hold must never be lost. A recalculation makes
    # no hold and its caller already has the PNR, so a failure stays a failure
    # here instead of coming back as a hold with no fare.
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "ok",
                "strResult": "SUCC",
                "h_pnr_no": "SYNTHETIC_PNR",
                "h_jrny_cnt": "1",
                "h_tot_prc": {"amount": 60000},
            },
        )

    client = _client(handler)
    try:
        with pytest.raises(KorailProtocolError):
            client.recalculate_price(_request())
    finally:
        client.close()


def test_the_repricing_form_names_a_blank_pnr():
    request = _request()
    object.__setattr__(request, "pnr_no", " ")
    with pytest.raises(
        KorailProtocolError,
        match=r"^KORAIL price recalculation requires a non-empty pnr_no$",
    ):
        build_price_recalculation_form(KorailConfig(), request)
