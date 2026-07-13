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
from korail_mobile_api.safety import EXCLUDED_API_DOMAINS


def test_redact_mapping_masks_sensitive_values():
    data = {
        "txtMemberNo": "1234567890",
        "txtPwd": "secret-password",
        "JSESSIONID": "abc",
        "pnrNo": "123456789012",
        "mutMrkVrfCd": "server-secret",
        "verification_code": "model-secret",
        "safe": "value",
    }
    redacted = redact_mapping(data)
    assert redacted["txtMemberNo"] == "[REDACTED]"
    assert redacted["txtPwd"] == "[REDACTED]"
    assert redacted["JSESSIONID"] == "[REDACTED]"
    assert redacted["pnrNo"] == "[REDACTED]"
    assert redacted["mutMrkVrfCd"] == "[REDACTED]"
    assert redacted["verification_code"] == "[REDACTED]"
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
    assert "abc" not in redacted["outer"][0]["url"]
    assert "safe=1" in redacted["outer"][0]["url"]
    assert "token-value" not in redact_url(
        "https://host/path?x-dynapath-m-token=token-value"
    )


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
        "pnrNo=pnr-secret"
    )
    errors = public_errors(message)
    for error in errors:
        formatted = f"{error!s} {error!r}"
        assert "password-secret" not in formatted
        assert "token-secret" not in formatted
        assert "pnr-secret" not in formatted


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
