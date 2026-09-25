"""Response.java:147–154 uses Integer.parseInt for TTL and wait counts."""

from __future__ import annotations

import sys

import pytest

from korail_mobile_api.netfunnel import parse_netfunnel_body


@pytest.mark.parametrize(
    "ttl,nwait,expected_ttl,expected_count",
    [
        ("+7", "+12", 7, 12),
        ("７", "１２", 7, 12),
        ("٧", "١٢", 7, 12),
        ("-7", "-12", 1, -12),
        ("0" * 700 + "7", "0" * 700 + "12", 7, 12),
        ("7", "12", 7, 12),
        ("not-numeric", "not-numeric", 1, 0),
        ("2147483648", "2147483648", 1, 0),
    ],
    ids=["plus", "fullwidth", "arabic", "negative", "leading-zeros", "ascii", "invalid", "overflow"],
)
def test_queue_number_properties_use_java_int32(
    ttl: str, nwait: str, expected_ttl: int, expected_count: int
) -> None:
    """Valid SDK numbers normalize; invalid values retain the library's zero fallback."""
    raw = f"201:key=SYNTHETIC-KEY&ttl={ttl}&nwait={nwait}"
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        token = parse_netfunnel_body(raw)
        assert token.wait_seconds == expected_ttl
        assert token.wait_count == expected_count
        assert token.raw == raw
        assert token.params["ttl"] == ttl and token.params["nwait"] == nwait
    finally:
        sys.set_int_max_str_digits(previous)
