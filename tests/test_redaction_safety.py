import pytest

from korail_mobile_api.errors import (
    KorailApiError,
    KorailAppError,
    KorailAuthContinuationRequired,
    KorailAuthError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)
from korail_mobile_api.redaction import redact_mapping, redact_text, redact_url
from korail_mobile_api.read_parsers import (
    parse_reservation_history_response,
    parse_trip_menu_response,
)
from korail_mobile_api.safety import EXCLUDED_API_DOMAINS


def test_redact_mapping_masks_sensitive_values():
    data = {
        "txtMemberNo": "1234567890",
        "txtPwd": "secret-password",
        "JSESSIONID": "abc",
        "pnrNo": "123456789012",
        "mutMrkVrfCd": "server-secret",
        "verification_code": "model-secret",
        "addSrvDvCd": "maas-wire-secret",
        "additional_service_code": "maas-model-secret",
        "safe": "value",
    }
    redacted = redact_mapping(data)
    assert redacted["txtMemberNo"] == "[REDACTED]"
    assert redacted["txtPwd"] == "[REDACTED]"
    assert redacted["JSESSIONID"] == "[REDACTED]"
    assert redacted["pnrNo"] == "[REDACTED]"
    assert redacted["mutMrkVrfCd"] == "[REDACTED]"
    assert redacted["verification_code"] == "[REDACTED]"
    assert redacted["addSrvDvCd"] == "[REDACTED]"
    assert redacted["additional_service_code"] == "[REDACTED]"
    assert redacted["safe"] == "value"


def test_redact_text_masks_card_like_values():
    assert "411111" not in redact_text("card 4111-1111-1111-1111")


def test_redaction_is_recursive_case_insensitive_and_url_safe():
    value = {
        "outer": [
            {
                "TXTPWD": "secret",
                "url": "https://host/path?JSESSIONID=abc&safe=1",
            }
        ],
    }
    redacted = redact_mapping(value)
    assert redacted["outer"][0]["TXTPWD"] == "[REDACTED]"
    assert redacted["outer"][0]["url"] == "[REDACTED]"
    assert "safe=1" in redact_url(
        "https://host/path?JSESSIONID=abc&safe=1"
    )
    assert "token-value" not in redact_url(
        "https://host/path?x-dynapath-m-token=token-value"
    )


def test_parsed_history_and_trip_models_redact_sensitive_fields_without_mutation(
    load_json_fixture,
):
    history = parse_reservation_history_response(
        load_json_fixture("reservation_history_success.json")
    )
    trip = parse_trip_menu_response(
        load_json_fixture("trip_menu_success.json")
    )
    train = history.trains[0]
    menu = trip.items[0]
    content = menu.contents[0]
    original_values = (
        train.pnr_no,
        menu.url,
        content.url,
        content.image,
    )

    redacted = redact_mapping({"history": history, "trip": trip})
    redacted_history = redacted["history"]
    redacted_trains = redacted_history.get(
        "items", redacted_history.get("trains")
    )
    assert redacted_trains[0]["pnr_no"] == "[REDACTED]"
    assert redacted["trip"]["items"][0]["url"] == "[REDACTED]"
    redacted_content = redacted["trip"]["items"][0]["contents"][0]
    assert redacted_content["url"] == "[REDACTED]"
    assert redacted_content["image"] == "[REDACTED]"

    assert train.pnr_no == original_values[0]
    assert menu.url == original_values[1]
    assert content.url == original_values[2]
    assert content.image == original_values[3]


def test_raw_trip_menu_wire_values_are_redacted_without_mutation(
    load_json_fixture,
):
    raw = load_json_fixture("trip_menu_success.json")
    menu = raw["menuList"][0]
    content = menu["contList"][0]
    original_values = (
        menu["menuUrl"],
        content["contUrl"],
        content["contImage"],
    )

    redacted = redact_mapping({"menu": menu})["menu"]
    assert redacted["menuUrl"] == "[REDACTED]"
    assert redacted["contList"][0]["contUrl"] == "[REDACTED]"
    assert redacted["contList"][0]["contImage"] == "[REDACTED]"

    assert menu["menuUrl"] == original_values[0]
    assert content["contUrl"] == original_values[1]
    assert content["contImage"] == original_values[2]


@pytest.mark.parametrize(
    "key",
    [
        "txtMemberNo",
        "txtPwd",
        "password",
        "JSESSIONID",
        "Cookie",
        "Set-Cookie",
        "pnrNo",
        "hidPnrNo",
        "tkRetPwd",
        "x-dynapath-m-token",
        "mutMrkVrfCd",
        "verification_code",
        "addSrvDvCd",
        "additional_service_code",
        "tkRetNo",
        "addSrvReqNo",
        "h_orgtk_tk_ret_pwd",
        "partner_reservation_no",
        "lump_sum_target_no",
        "customer_no",
        "virtual_reservation_no",
        "original_sale_date",
        "window_no",
        "sale_sequence",
        "return_password",
        "coupon_no",
        "member_card_no",
        "account_no",
        "approval_no",
        "card_no",
        "point_no",
        "h_stl_mb_crd_no",
        "h_acnt_no",
        "h_apv_no",
        "h_stl_crd_no",
        "h_xpot_no",
        "coptEntRsvNo",
        "h_pnr_no",
        "h_lump_stl_tgt_no",
        "h_cust_no",
        "h_vr_rsv_no",
        "h_orgtk_ret_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "h_orgtk_ret_pwd",
        "h_cpn_no",
        "strVrRsvNo",
        "txtVrRsNo",
        "txtVrRsvSqNo",
        "h_orgtk_sale_dt",
        "h_orgtk_wct_no",
        "h_orgtk_sale_sqno",
        "pnr_no",
        "url",
        "image",
        "menuUrl",
        "contUrl",
        "contImage",
    ],
)
def test_redact_text_masks_sensitive_key_value_pairs(key):
    redacted = redact_text(f"prefix {key}=secret-value suffix")
    assert "secret-value" not in redacted
    assert "[REDACTED]" in redacted


def test_uuid_verification_names_are_redacted_case_insensitively():
    value = {
        "mutMrkVrfCd": "server-secret",
        "VERIFICATION_CODE": "model-secret",
    }
    redacted = redact_mapping(value)
    assert redacted == {
        "mutMrkVrfCd": "[REDACTED]",
        "VERIFICATION_CODE": "[REDACTED]",
    }
    rendered = redact_text(
        'mutMrkVrfCd="server-secret" verification_code=model-secret'
    )
    assert "server-secret" not in rendered
    assert "model-secret" not in rendered


def public_errors(message):
    return [
        KorailApiError(message),
        KorailTransportError(message),
        KorailProtocolError(message),
        KorailAuthError(message),
        KorailSessionExpiredError("P058", message),
        KorailDynaPathError(message),
        KorailAuthContinuationRequired(
            "https://smart.letskorail.com/continue"
            "?x-dynapath-m-token=token-secret",
            message,
        ),
        KorailAppError("ERR", message),
    ]


def test_every_public_exception_formatter_redacts_free_text_secrets():
    message = (
        "txtPwd=password-secret "
        "x-dynapath-m-token=token-secret "
        "pnrNo=pnr-secret "
        "pnr_no=typed-reservation-secret"
    )
    errors = public_errors(message)
    for error in errors:
        formatted = f"{error!s} {error!r}"
        assert "password-secret" not in formatted
        assert "token-secret" not in formatted
        assert "pnr-secret" not in formatted
        assert "typed-reservation-secret" not in formatted


@pytest.mark.parametrize("quote", ['"', "'"])
def test_every_public_exception_redacts_quoted_json_like_keys(quote):
    message = (
        f"{{{quote}txtPwd{quote}: {quote}password-secret{quote}, "
        f"{quote}x-dynapath-m-token{quote}: {quote}token-secret{quote}, "
        f"{quote}pnrNo{quote}: {quote}pnr-secret{quote}, "
        f"{quote}safe{quote}: {quote}safe-value{quote}}}"
    )
    safe_field = f"{quote}safe{quote}: {quote}safe-value{quote}"
    redacted = redact_text(message)
    assert safe_field in redacted
    assert "password-secret" not in redacted
    assert "token-secret" not in redacted
    assert "pnr-secret" not in redacted

    for error in public_errors(message):
        formatted = f"{error!s} {error!r}"
        assert "password-secret" not in formatted
        assert "token-secret" not in formatted
        assert "pnr-secret" not in formatted


@pytest.mark.parametrize(
    ("message", "secrets", "safe_field"),
    [
        (
            r'{"txtPwd": "start-secret\"tail-secret", "safe": "safe-value"}',
            ("start-secret", "tail-secret"),
            '"safe": "safe-value"',
        ),
        (
            r"{'txtPwd': 'start-secret\'tail-secret', 'safe': 'safe-value'}",
            ("start-secret", "tail-secret"),
            "'safe': 'safe-value'",
        ),
        (
            r'{"txtPwd": "start-secret\\tail-secret", "safe": "safe-value"}',
            ("start-secret", "tail-secret"),
            '"safe": "safe-value"',
        ),
        (
            r"{'txtPwd': 'start-secret\\tail-secret', 'safe': 'safe-value'}",
            ("start-secret", "tail-secret"),
            "'safe': 'safe-value'",
        ),
        (
            r'''{"txtPwd": 'start-secret\'tail-secret', "safe": "safe-value"}''',
            ("start-secret", "tail-secret"),
            '"safe": "safe-value"',
        ),
        (
            r'''{'txtPwd': "start-secret\"tail-secret", 'safe': 'safe-value'}''',
            ("start-secret", "tail-secret"),
            "'safe': 'safe-value'",
        ),
        (
            r'{"txtPwd": "start-secret\\\"tail-secret", "safe": "safe-value"}',
            ("start-secret", "tail-secret"),
            '"safe": "safe-value"',
        ),
        (
            r"{'txtPwd': 'start-secret\\\'tail-secret', 'safe': 'safe-value'}",
            ("start-secret", "tail-secret"),
            "'safe': 'safe-value'",
        ),
        (
            r'{"txtPwd": "start-secret\"tail-secret and trailing-secret',
            ("start-secret", "tail-secret", "trailing-secret"),
            None,
        ),
        (
            r"{'txtPwd': 'start-secret\'tail-secret and trailing-secret",
            ("start-secret", "tail-secret", "trailing-secret"),
            None,
        ),
    ],
    ids=[
        "double-escaped-quote",
        "single-escaped-quote",
        "double-escaped-backslash",
        "single-escaped-backslash",
        "double-key-single-value",
        "single-key-double-value",
        "double-backslash-and-escaped-quote",
        "single-backslash-and-escaped-quote",
        "double-unclosed",
        "single-unclosed",
    ],
)
def test_escape_aware_quoted_values_never_leak(
    message,
    secrets,
    safe_field,
):
    redacted = redact_text(message)
    if safe_field is not None:
        assert safe_field in redacted
    for secret in secrets:
        assert secret not in redacted

    for error in public_errors(message):
        formatted = f"{error!s} {error!r}"
        for secret in secrets:
            assert secret not in formatted


def test_safety_excludes_dangerous_domains_without_stub_apis():
    assert "reservation" in EXCLUDED_API_DOMAINS
    assert "payment" in EXCLUDED_API_DOMAINS
    assert "refund" in EXCLUDED_API_DOMAINS
    assert "check-in" in EXCLUDED_API_DOMAINS


# --------------------------------------------------------------------------
# The read side, swept whole rather than per-route. The 2026-07-27 audit
# checked the three routes added that day; this checks all 47 field contracts
# and every model dataclass at once, which is what found that the policy was
# implemented in one spelling out of five.
# --------------------------------------------------------------------------


def test_every_special_category_label_spelling_is_masked():
    """One meaning, five wire spellings; masking one of them masks nothing.

    These carry a human-readable special-category value -- "장애 1~3급",
    "국가유공자", "만 65세이상". This module's documented policy is to mask
    what a human can read and to leave the CODES that stand for it, so all of
    them belong in SENSITIVE_KEYS. Only psgTpDvNm was there.
    """
    from korail_mobile_api.redaction import is_sensitive_key

    for spelling in (
        "psgTpDvNm",
        "psgTpNm",
        "h_psg_tp_nm",
        "h_dcnt_knd_nm",
        "h_subt_dcs_cl_nm",
    ):
        assert is_sensitive_key(spelling), spelling


def test_no_special_category_label_is_left_in_a_model_repr():
    """The other half: masked on the wire, hidden in repr().

    These were the wrong way round -- welfare_discount_class_CODE was
    repr=False while welfare_discount_class_NAME, the directly readable one,
    was printed. A repr lands in logs and tracebacks, which is the same
    exposure redact_payload exists to prevent.
    """
    import dataclasses

    from korail_mobile_api import read_models

    exposed = []
    for name, obj in vars(read_models).items():
        if not dataclasses.is_dataclass(obj):
            continue
        for field_ in dataclasses.fields(obj):
            if field_.name in {
                "disability_flag",
                "welfare_discount_class_name",
                "customer_lead_flag_name",
                "discount_kind_name",
                "passenger_type_name",
            } and field_.repr:
                exposed.append(f"{name}.{field_.name}")

    assert not exposed, f"special-category labels still in repr(): {exposed}"


def test_no_read_route_field_contract_carries_an_unmasked_identity_field():
    """All 47 contracts at once, so a new route cannot quietly add one.

    Station names (dptRsStnNm and friends) are the deliberate exception: they
    name a PLACE, are not tied to a person, and masking them would make every
    preview unreadable for no privacy gain.
    """
    import re

    from korail_mobile_api import safety
    from korail_mobile_api.redaction import is_sensitive_key

    identity_shaped = re.compile(
        r"cust|teln|phone|jumin|birth|regnum|pwd|passwd|email|addr", re.I
    )
    allowed = {"custMgNo"}  # a management number, masked by its indexed forms

    unmasked = {
        field_
        for fields in safety.KORAIL_EXACT_REQUEST_FIELDS.values()
        for field_ in fields
        if identity_shaped.search(field_)
        and not is_sensitive_key(field_)
        and field_ not in allowed
    }

    assert not unmasked, f"identity-shaped request fields not masked: {unmasked}"
