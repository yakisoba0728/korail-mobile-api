"""Offline tests for 정기권 구매 — reserve, then settle.

A 정기권 is a route-bound season pass, bought in two calls, and both of them are
in the app's `PassService` rather than anywhere near the ticket routes:

* ``pass.passReserve`` (``PassService.java:23-25``), twenty ``@Field``s, filled
  by ``CommutationInquiryActivity.java:188-222`` (``w0``) from one schedule
  option's ``train_list``. It creates an UNPAID reservation whose ``main_info``
  carries the price in ``h_rcvd_amt``.
* ``pass.passPayIssue`` (``PassService.java:19-21``), ``hidPayAmount`` plus two
  ``@FieldMap``s, and **both maps are answered by v6.5.0**:
  ``CommutationInquiryActivity.java:242`` is
  ``setCommPaymentMap(A.convertObjectToMap(main_info))`` -- the whole reserve
  response reflected into a map by ``S4/A.java:18-27`` -- and
  ``B6/AbstractC1269e.java:736-744`` supplies the second, which is the SAME
  ``PaymentMethod`` a train payment sends (``V4/a.java:21-34``).

The amount chain, which is why ``hidPayAmount`` is not a caller argument:
``AbstractC1269e.java:740`` sends ``t1()``; ``t1()`` (``:1868``) is
``s1() + getDiscountAmount()``; ``s1()`` (``:1763``) is the ``RECEIVED_AMOUNT``
extra; and ``CReservationConfirmActivity.java:47-48`` sets that extra to
``Integer.parseInt(mainInfo.getH_rcvd_amt())`` with ``DISCOUNT_AMOUNT`` fixed at
``0``.

NOTHING here has been transmitted, and ``pay_for_commuter_pass`` is not
live-enabled from this repository.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from korail_mobile_api import (
    CardPayment,
    CommuterPassPurchaseRequest,
    CommuterPassReservation,
    CommuterPassReservationResponse,
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    KORAIL_MUTATION_ROUTES,
    KorailClient,
    KorailConfig,
    KorailProtocolError,
    KorailSession,
    MutationConsent,
    MutationNotAllowedError,
    MutationPreview,
    PassScheduleTrain,
    parse_commuter_pass_reservation_response,
)
from korail_mobile_api.consent import MUTATION_CATEGORIES
from korail_mobile_api.mutation_payloads import (
    KORAIL_COMMUTER_PASS_PAYMENT_FIELDS,
    build_commuter_pass_payment_form,
    build_commuter_pass_reservation_form,
)
from korail_mobile_api.redaction import SENSITIVE_KEYS
from korail_mobile_api.safety import KORAIL_MUTATION_ROUTE_CATEGORIES


RESERVE_ROUTE = "/classes/com.korail.mobile.pass.passReserve"
PAY_ROUTE = "/classes/com.korail.mobile.pass.passPayIssue"


def _config() -> KorailConfig:
    return KorailConfig()


def _first_train() -> PassScheduleTrain:
    return PassScheduleTrain(
        departure_station_code="0001",
        departure_station_name="서울",
        arrival_station_code="0501",
        arrival_station_name="대전",
        train_no="1001",
        train_group_code="109",
        detour_code="0",
    )


def _second_train() -> PassScheduleTrain:
    return PassScheduleTrain(
        departure_station_code="0501",
        departure_station_name="대전",
        arrival_station_code="0723",
        arrival_station_name="익산",
        train_no="1502",
        train_group_code="109",
        detour_code="1",
    )


def _request(**kwargs) -> CommuterPassPurchaseRequest:
    base = {
        "pass_kind_code": "1",
        "pass_period_code": "1",
        "pass_period_name": "1개월",
        "pass_age_code": "1",
        "use_open_date": "20990101",
        "trains": (_first_train(),),
    }
    base.update(kwargs)
    return CommuterPassPurchaseRequest(**base)


# The twenty fields of PassService.java:23-25, in declaration order.
DECLARED_RESERVE_FIELDS: tuple[str, ...] = (
    "Device",
    "Version",
    "Key",
    "hidCmtrKndCd",
    "hidCmtrUtlTrmCd",
    "hidCmtrUtlTrmNm",
    "hidCmtrUtlAgeCd",
    "hidUseOpenDt",
    "hidAppDptStnCd",
    "hidAppDptStnNm",
    "hidAppArvStnCd",
    "hidAppArvStnNm",
    "hidChtrnStnCd",
    "hidChtrnStnNm",
    "hidTrnNo1",
    "hidTrnNo2",
    "hidTrnGpCd1",
    "hidTrnGpCd2",
    "hidDtour1",
    "hidDtour2",
)


# ---------------------------------------------------------------------------
# The reserve form.


def test_two_train_reserve_form_covers_every_declared_field() -> None:
    form = build_commuter_pass_reservation_form(
        _config(),
        _request(trains=(_first_train(), _second_train())),
    )
    assert set(form) == set(DECLARED_RESERVE_FIELDS)


def test_two_train_reserve_form_values() -> None:
    form = build_commuter_pass_reservation_form(
        _config(),
        _request(trains=(_first_train(), _second_train())),
    )
    assert form["hidCmtrKndCd"] == "1"
    assert form["hidCmtrUtlTrmCd"] == "1"
    assert form["hidCmtrUtlTrmNm"] == "1개월"
    assert form["hidCmtrUtlAgeCd"] == "1"
    assert form["hidUseOpenDt"] == "20990101"
    # Origin is leg 1's departure; destination is the LAST leg's arrival, since
    # the app overwrites it on every iteration
    # (CommutationInquiryActivity.java:217-218).
    assert form["hidAppDptStnCd"] == "0001"
    assert form["hidAppDptStnNm"] == "서울"
    assert form["hidAppArvStnCd"] == "0723"
    assert form["hidAppArvStnNm"] == "익산"
    # The 환승역 is the second leg's DEPARTURE (:212-216).
    assert form["hidChtrnStnCd"] == "0501"
    assert form["hidChtrnStnNm"] == "대전"
    assert form["hidTrnNo1"] == "1001"
    assert form["hidTrnNo2"] == "1502"
    assert form["hidTrnGpCd1"] == "109"
    assert form["hidTrnGpCd2"] == "109"
    assert form["hidDtour1"] == "0"
    assert form["hidDtour2"] == "1"


def test_one_train_reserve_form_omits_the_second_train_and_empties_the_transfer(
) -> None:
    form = build_commuter_pass_reservation_form(_config(), _request())
    # Never assigned by the loop, so Retrofit drops the @Field entirely.
    assert "hidTrnNo2" not in form
    assert "hidTrnGpCd2" not in form
    assert "hidDtour2" not in form
    # Assigned on EVERY iteration, and the index-0 branch assigns "" -- so
    # these two are present and empty rather than absent.
    assert form["hidChtrnStnCd"] == ""
    assert form["hidChtrnStnNm"] == ""
    assert form["hidAppArvStnCd"] == "0501"


def test_reserve_form_key_order_follows_the_service_declaration() -> None:
    form = build_commuter_pass_reservation_form(
        _config(),
        _request(trains=(_first_train(), _second_train())),
    )
    # Same relative order as PassService.java:23-25 apart from the two train
    # blocks, which this builder emits per leg (No/GpCd/Dtour for leg 1, then
    # for leg 2) rather than field-by-field across legs. Retrofit's @Field order
    # is not something a form-encoded body's receiver can depend on, and the
    # per-leg grouping is what the app's own loop produces.
    assert list(form)[:14] == list(DECLARED_RESERVE_FIELDS[:14])
    assert list(form)[14:] == [
        "hidTrnNo1",
        "hidTrnGpCd1",
        "hidDtour1",
        "hidTrnNo2",
        "hidTrnGpCd2",
        "hidDtour2",
    ]


def test_reserve_form_refuses_more_than_two_trains() -> None:
    with pytest.raises(KorailProtocolError, match="1 or 2 trains"):
        build_commuter_pass_reservation_form(
            _config(),
            _request(
                trains=(_first_train(), _second_train(), _first_train()),
            ),
        )
    with pytest.raises(KorailProtocolError, match="1 or 2 trains"):
        build_commuter_pass_reservation_form(_config(), _request(trains=()))


def test_reserve_form_refuses_a_missing_period_name() -> None:
    with pytest.raises(KorailProtocolError, match="pass_period_name"):
        build_commuter_pass_reservation_form(
            _config(),
            _request(pass_period_name=""),
        )


def test_reserve_form_refuses_a_malformed_open_date() -> None:
    with pytest.raises(KorailProtocolError, match="use_open_date"):
        build_commuter_pass_reservation_form(
            _config(),
            _request(use_open_date="2099-01-01"),
        )


def test_reserve_form_refuses_foreign_train_rows() -> None:
    with pytest.raises(KorailProtocolError, match="PassScheduleTrain"):
        build_commuter_pass_reservation_form(
            _config(),
            _request(trains=({"train_no": "1001"},)),
        )


def test_a_train_without_a_detour_code_sends_an_empty_string() -> None:
    form = build_commuter_pass_reservation_form(
        _config(),
        _request(trains=(replace(_first_train(), detour_code=None),)),
    )
    assert form["hidDtour1"] == ""


# ---------------------------------------------------------------------------
# The reserve response.


_MAIN_INFO = {
    "h_rcvd_amt": "184000",
    "h_rcvd_prc": "167300",
    "h_rcvd_fare": "16700",
    "h_otm_rcvd_amt": "23700",
    "h_chg_mg_no": "0000123456",
    "h_chg_mg_dv_cd": "1",
    "h_cust_nm": "홍길동",
    "h_cust_no": "0009876543",
    "h_cmtr_knd_cd": "1",
    "h_cmtr_utl_trm_cd": "1",
    "h_cmtr_utl_trm_nm": "1개월",
    "h_cmtr_utl_age_cd": "1",
    "h_use_open_dt": "20990101",
    "h_use_cls_dt": "20990131",
    "h_use_psb_dno": "31",
    "h_use_psb_tno": "62",
    "h_app_dpt_rs_stn_cd": "0001",
    "h_app_dpt_rs_stn_nm": "서울",
    "h_app_arv_rs_stn_cd": "0501",
    "h_app_arv_rs_stn_nm": "대전",
    "h_chtrn_rs_stn_cd": "",
    "h_chtrn_rs_stn_nm": "",
    "h_trn_gp_cd": "109",
    "h_trn_no_1": "1001",
    "h_holiday_flg": "N",
}


def _reserve_response() -> CommuterPassReservationResponse:
    return parse_commuter_pass_reservation_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRG000000",
            "h_msg_txt": "",
            "h_guide": "정기승차권은 지정한 열차만 이용하실 수 있습니다.",
            "main_info": dict(_MAIN_INFO),
        }
    )


def test_reserve_response_parses_the_typed_slice_and_keeps_the_whole_object(
) -> None:
    response = _reserve_response()
    assert type(response) is CommuterPassReservationResponse
    assert response.guide.startswith("정기승차권")
    reservation = response.reservation
    assert type(reservation) is CommuterPassReservation
    assert reservation.received_amount == "184000"
    assert reservation.customer_name == "홍길동"
    assert reservation.use_close_date == "20990131"
    assert reservation.transfer_station_code == ""
    # The whole main_info survives, because the payment sends all of it.
    assert reservation.raw == _MAIN_INFO


def test_reserve_response_without_main_info_parses_to_none() -> None:
    response = parse_commuter_pass_reservation_response(
        {"strResult": "SUCC", "h_msg_cd": "IRG000000", "h_msg_txt": ""}
    )
    assert response.reservation is None


def test_reserve_response_refuses_a_non_object_main_info() -> None:
    with pytest.raises(KorailProtocolError, match="main_info"):
        parse_commuter_pass_reservation_response(
            {
                "strResult": "SUCC",
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "",
                "main_info": ["nope"],
            }
        )


# ---------------------------------------------------------------------------
# The payment form.


def _card() -> CardPayment:
    return CardPayment(
        card_number="4000000000000000",
        card_password="00",
        card_expire="3012",
        birthday="900101",
        card_type="J",
        installment="00",
    )


def _payment_form(**kwargs) -> dict[str, str]:
    reservation = kwargs.pop("reservation", None) or (
        _reserve_response().reservation
    )
    return build_commuter_pass_payment_form(
        _config(),
        reservation,
        _card(),
        station_info=kwargs.pop("station_info", "서울 → 대전"),
        user_names=kwargs.pop("user_names", "홍길동 님"),
    )


def test_payment_map_key_list_is_the_reflected_getter_set() -> None:
    # 54 h_* server fields; stationinfo and usernames are added by the builder
    # because the app writes them into the object before reflecting it
    # (CommutationInquiryActivity.java:238-240).
    assert len(KORAIL_COMMUTER_PASS_PAYMENT_FIELDS) == 54
    assert len(set(KORAIL_COMMUTER_PASS_PAYMENT_FIELDS)) == 54
    assert all(
        key.startswith("h_") for key in KORAIL_COMMUTER_PASS_PAYMENT_FIELDS
    )
    # isIncludeHoliday's getter is named "is...", so convertObjectToMap skips
    # it (S4/A.java:22 tests startsWith("get")).
    assert "isincludeholiday" not in KORAIL_COMMUTER_PASS_PAYMENT_FIELDS
    assert "includeholiday" not in KORAIL_COMMUTER_PASS_PAYMENT_FIELDS


def test_payment_form_carries_the_reservation_the_amount_and_the_card() -> None:
    form = _payment_form()
    assert form["hidPayAmount"] == "184000"
    # hidMnsStlAmt1 is the same number for the same reason, absent points.
    assert form["hidMnsStlAmt1"] == "184000"
    # Every main_info field present in the response is forwarded verbatim.
    for key, value in _MAIN_INFO.items():
        assert form[key] == value
    # ...and the two client-side strings the reflection sweeps in.
    assert form["stationinfo"] == "서울 → 대전"
    assert form["usernames"] == "홍길동 님"
    # The PaymentMethod half, identical in shape to a train payment's.
    assert form["hidInrecmnsGridcnt"] == "1"
    assert form["hidStlMnsSqno1"] == "1"
    assert form["hidStlMnsCd1"] == "02"
    assert form["hidCrdInpWayCd1"] == "@"
    assert form["hidStlCrCrdNo1"] == "4000000000000000"
    assert form["hiduserYn"] == "Y"


def test_payment_form_card_half_matches_the_train_payment_card_half() -> None:
    # Both come from V4/a.getCardRequest, so they must not drift apart.
    from korail_mobile_api.mutation_payloads import build_card_payment_form
    from korail_mobile_api import ReservationHoldResponse

    hold = ReservationHoldResponse(
        str_result="SUCC",
        h_msg_cd="IRR000000",
        h_msg_txt="",
        pnr_no="123456789",
        window_no="0001",
        received_amount="184000",
        journey_count="1",
        temporary_job_sequence_1="1",
        temporary_job_sequence_2="2",
        journeys=(),
    )
    train_form = build_card_payment_form(_config(), hold, _card())
    pass_form = _payment_form()
    card_keys = (
        "hidInrecmnsGridcnt",
        "hidStlMnsSqno1",
        "hidStlMnsCd1",
        "hidMnsStlAmt1",
        "hidCrdInpWayCd1",
        "hidStlCrCrdNo1",
        "hidVanPwd1",
        "hidCrdVlidTrm1",
        "hidIsmtMnthNum1",
        "hidAthnDvCd1",
        "hidAthnVal1",
        "hiduserYn",
    )
    assert {key: pass_form[key] for key in card_keys} == {
        key: train_form[key] for key in card_keys
    }


def test_payment_form_omits_a_field_the_server_did_not_send() -> None:
    form = _payment_form()
    # h_age is declared but absent from this fixture, so it is absent from the
    # form: the app would put a null in the map and Retrofit would drop it.
    assert "h_age" not in form
    assert "h_trn_no_2" not in form


def test_payment_form_refuses_a_reservation_without_a_numeric_amount() -> None:
    reservation = replace(
        _reserve_response().reservation,
        received_amount=None,
    )
    with pytest.raises(KorailProtocolError, match="h_rcvd_amt"):
        _payment_form(reservation=reservation)
    reservation = replace(
        _reserve_response().reservation,
        received_amount="184,000",
    )
    with pytest.raises(KorailProtocolError, match="h_rcvd_amt"):
        _payment_form(reservation=reservation)


def test_payment_form_refuses_a_non_digit_card_number() -> None:
    reservation = _reserve_response().reservation
    with pytest.raises(KorailProtocolError, match="digits"):
        build_commuter_pass_payment_form(
            _config(),
            reservation,
            replace(_card(), card_number="4000-0000-0000-0000"),
            station_info="",
            user_names="",
        )


# ---------------------------------------------------------------------------
# Safety: the category, the routes, the card gate, the redaction.


def test_commuter_pass_is_its_own_consent_category() -> None:
    assert "commuter_pass" in MUTATION_CATEGORIES
    assert len(MUTATION_CATEGORIES) == 6
    # Not reachable through any consent that existed before it.
    consent = MutationConsent(
        allow_reserve=True,
        allow_payment=True,
        allow_cancel=True,
        allow_refund=True,
        allow_discount_card=True,
    )
    assert consent.allow_commuter_pass is False
    from korail_mobile_api import require_mutation_consent

    with pytest.raises(MutationNotAllowedError):
        require_mutation_consent(consent, "commuter_pass")
    require_mutation_consent(
        MutationConsent(allow_commuter_pass=True),
        "commuter_pass",
    )


def test_both_routes_are_registered_and_owned_by_that_category() -> None:
    assert ("POST", RESERVE_ROUTE) in KORAIL_MUTATION_ROUTES
    assert ("POST", PAY_ROUTE) in KORAIL_MUTATION_ROUTES
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[RESERVE_ROUTE] == "commuter_pass"
    assert KORAIL_MUTATION_ROUTE_CATEGORIES[PAY_ROUTE] == "commuter_pass"
    # The 자유이용권 siblings are deliberately NOT registered.
    for path in (
        "/classes/com.korail.mobile.pass.passOtrReserve",
        "/classes/com.korail.mobile.pass.passOtrPayIssue",
    ):
        assert ("POST", path) not in KORAIL_MUTATION_ROUTES
        assert path not in KORAIL_MUTATION_ROUTE_CATEGORIES


def test_neither_route_is_reachable_from_the_read_path() -> None:
    from korail_mobile_api.safety import assert_read_only_route

    for path in (RESERVE_ROUTE, PAY_ROUTE):
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("POST", path)


def test_the_settlement_is_card_gated_like_a_train_payment() -> None:
    assert "commuter_pass" in KORAIL_CARD_BEARING_MUTATION_CATEGORIES
    client = _client()
    try:
        for consent in (
            MutationConsent(
                allow_commuter_pass=True,
                dry_run=False,
                fake_card_only=False,
                real_card_acknowledged=False,
            ),
            MutationConsent(
                allow_commuter_pass=True,
                dry_run=False,
                fake_card_only=True,
                real_card_acknowledged=True,
            ),
        ):
            with pytest.raises(MutationNotAllowedError):
                client.http.post_mutation_form(
                    PAY_ROUTE,
                    _payment_form(),
                    consent=consent,
                    category="commuter_pass",
                )
    finally:
        client.close()


def test_the_holder_identity_is_redacted_in_a_preview() -> None:
    for key in ("h_cust_nm", "usernames", "h_cust_no", "h_chg_mg_no"):
        assert key.casefold() in SENSITIVE_KEYS
    preview = MutationPreview(
        category="commuter_pass",
        method="POST",
        route=PAY_ROUTE,
        payload=_payment_form(),
    )
    assert preview.payload["h_cust_nm"] == "[REDACTED]"
    assert preview.payload["usernames"] == "[REDACTED]"
    assert preview.payload["h_cust_no"] == "[REDACTED]"
    assert preview.payload["h_chg_mg_no"] == "[REDACTED]"
    assert preview.payload["hidStlCrCrdNo1"] == "[REDACTED]"
    assert preview.payload["hidVanPwd1"] == "[REDACTED]"
    # Deliberately visible: the amount. A dry-run preview of a purchase whose
    # whole risk is the price must show the price.
    assert preview.payload["hidPayAmount"] == "184000"


# ---------------------------------------------------------------------------
# The client methods.


def _client() -> KorailClient:
    client = KorailClient(_config())
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    return client


def test_both_methods_deny_by_default() -> None:
    client = _client()
    try:
        with pytest.raises(MutationNotAllowedError):
            client.reserve_commuter_pass(
                _request(),
                consent=MutationConsent(),
            )
        with pytest.raises(MutationNotAllowedError):
            client.reserve_commuter_pass(
                _request(),
                consent=MutationConsent(allow_payment=True),
            )
        with pytest.raises(MutationNotAllowedError):
            client.pay_for_commuter_pass(
                _reserve_response().reservation,
                _card(),
                consent=MutationConsent(allow_payment=True),
                station_info="",
                user_names="",
            )
    finally:
        client.close()


def test_dry_run_previews_carry_the_category_and_the_route() -> None:
    client = _client()
    consent = MutationConsent(allow_commuter_pass=True)
    try:
        reserve_preview = client.reserve_commuter_pass(
            _request(),
            consent=consent,
        )
        pay_preview = client.pay_for_commuter_pass(
            _reserve_response().reservation,
            _card(),
            consent=consent,
            station_info="서울 → 대전",
            user_names="홍길동 님",
        )
    finally:
        client.close()
    for preview, route in (
        (reserve_preview, RESERVE_ROUTE),
        (pay_preview, PAY_ROUTE),
    ):
        assert type(preview) is MutationPreview
        assert preview.category == "commuter_pass"
        assert preview.method == "POST"
        assert preview.route == route
        assert preview.note == "dry-run: not sent"


def test_neither_method_is_reachable_without_a_session() -> None:
    from korail_mobile_api import KorailAuthError

    client = KorailClient(_config())
    try:
        with pytest.raises(KorailAuthError):
            client.reserve_commuter_pass(
                _request(),
                consent=MutationConsent(allow_commuter_pass=True),
            )
        with pytest.raises(KorailAuthError):
            client.pay_for_commuter_pass(
                _reserve_response().reservation,
                _card(),
                consent=MutationConsent(allow_commuter_pass=True),
                station_info="",
                user_names="",
            )
    finally:
        client.close()
