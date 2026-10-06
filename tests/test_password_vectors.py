"""Supplement the existing OpenSSL vectors with nine Android reference outputs.

These mechanical vectors were generated with Java AES and AOSP Android 14 Base64.
Reference generator and outputs: devgyurak/pykorail, commit dede6551e4d78e27bea6ff66c20d2c684d0fd7b2,
tests/reference/PasswordVectors.java and tests/password_vectors.json.
All inputs are synthetic; expected outputs are fixed independently of our implementation.
"""

from __future__ import annotations

import pytest

from korail_mobile_api.crypto import transform_login_password
from korail_mobile_api.models import LoginCryptoInfo


@pytest.mark.parametrize(
    "password, expected",
    [
        ("", "T0s2RG8rM1NLbkhzOHBaVG5kOXpJQT09\n"),
        ("a", "eDlNejMweEQvamh6eVc4dDVtdVpuUT09\n"),
        ("a" * 15, "QzZpeW1uLzRIZThoM0pLeHJhUjFUQT09\n"),
        ("a" * 16, "eDZ2eWZyZlh0RmY4ZGV3VFNQa1RVVEI2NmhrR2tOMml6aWZNQm45ejBEQT0=\n"),
        ("a" * 31, "eDZ2eWZyZlh0RmY4ZGV3VFNQa1RVWXBUTTR4MzZlZW9HYThYQkdwNElWUT0=\n"),
        (
            "a" * 32,
            "eDZ2eWZyZlh0RmY4ZGV3VFNQa1RVWmFqam1DRFVKdlJoN2Q1d2xjdGxzWnVYcmlvS3hYM0lMVFd6\nUXJ3QWtENA==\n",
        ),
        (
            "a" * 64,
            "eDZ2eWZyZlh0RmY4ZGV3VFNQa1RVWmFqam1DRFVKdlJoN2Q1d2xjdGxzYmxEQWs0ZGhtNWowMmVy\ndzhGQjVsNHRDTmN4RThMSFJVUU1MdXlsN0hUSjU1ZlNiK20xNGswdEt6Mi9DNVFzK1E9\n",
        ),
        ("한글🙂" * 3, "SUNkd1hxSEk4T3V3aHpsRkNoRkk5S3FrUmR5TCt4d2VRODRINThEMUpvUT0=\n"),
        (
            "한글🙂" * 4,
            "SUNkd1hxSEk4T3V3aHpsRkNoRkk5SnZMYk5xUlFKUlN3ZjViWFlCUnladGhjN2lNZnFvU08rM1g5\nOHc3U2FOZQ==\n",
        ),
    ],
    ids=[
        "empty",
        "one-byte",
        "15-bytes",
        "16-bytes",
        "31-bytes",
        "32-bytes",
        "64-bytes",
        "unicode-30-bytes",
        "unicode-40-bytes",
    ],
)
def test_password_matches_android_reference(password: str, expected: str) -> None:
    info = LoginCryptoInfo(key="0123456789abcdef0123456789abcdef")
    assert transform_login_password(password, info) == expected
