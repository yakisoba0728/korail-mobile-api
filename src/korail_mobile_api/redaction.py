from collections.abc import Mapping
import re
from typing import Any


SENSITIVE_KEYS = {
    "txtMemberNo",
    "txtPwd",
    "password",
    "JSESSIONID",
    "Cookie",
    "Set-Cookie",
    "pnrNo",
    "hidPnrNo",
    "tkRetPwd",
}

CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def redact_text(value: str) -> str:
    return CARD_RE.sub("[REDACTED_CARD]", value)


def redact_mapping(data: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in data.items():
        if key in SENSITIVE_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        else:
            redacted[key] = value
    return redacted
