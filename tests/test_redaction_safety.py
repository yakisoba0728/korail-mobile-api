from korail_mobile_api.redaction import redact_mapping, redact_text
from korail_mobile_api.safety import EXCLUDED_API_DOMAINS


def test_redact_mapping_masks_sensitive_values():
    data = {
        "txtMemberNo": "1234567890",
        "txtPwd": "secret-password",
        "JSESSIONID": "abc",
        "pnrNo": "123456789012",
        "safe": "value",
    }
    redacted = redact_mapping(data)
    assert redacted["txtMemberNo"] == "[REDACTED]"
    assert redacted["txtPwd"] == "[REDACTED]"
    assert redacted["JSESSIONID"] == "[REDACTED]"
    assert redacted["pnrNo"] == "[REDACTED]"
    assert redacted["safe"] == "value"


def test_redact_text_masks_card_like_values():
    assert "411111" not in redact_text("card 4111-1111-1111-1111")


def test_safety_excludes_dangerous_domains_without_stub_apis():
    assert "reservation" in EXCLUDED_API_DOMAINS
    assert "payment" in EXCLUDED_API_DOMAINS
    assert "refund" in EXCLUDED_API_DOMAINS
    assert "check-in" in EXCLUDED_API_DOMAINS
