import pytest

from korail_mobile_api.crypto import generate_sid, transform_login_password
from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.models import LoginCryptoInfo


def test_transform_login_password_base64_only():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="N")
    assert transform_login_password("pw123", info) == "cHcxMjM="


def test_transform_login_password_aes_is_deterministic_and_not_plaintext():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="Y")
    first = transform_login_password("pw123", info)
    second = transform_login_password("pw123", info)
    assert first == second
    assert first == "ZkpkU2JycXlJSzYyeGNxcSsxdUNmUT09Cg=="
    assert first != "pw123"
    assert first != "cHcxMjM="


def test_aes_login_transform_preserves_android_default_newline_before_outer_base64():
    info = LoginCryptoInfo(
        idx="IDX",
        key="1234567890abcdef",
        pwd_aes_cphd="Y",
    )
    assert (
        transform_login_password("pw123", info)
        == "ZkpkU2JycXlJSzYyeGNxcSsxdUNmUT09Cg=="
    )


def test_transform_login_password_aes_accepts_32_byte_live_key():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef1234567890abcdef", pwd_aes_cphd="Y")

    assert (
        transform_login_password("pw123", info)
        == "Nldzc1VlbW0yeVRISi82RG04UXFkQT09Cg=="
    )


def test_generate_sid_is_deterministic_with_epoch_ms():
    sid = generate_sid(epoch_ms=1710000000000)
    assert isinstance(sid, str)
    assert sid == generate_sid(epoch_ms=1710000000000)
    assert sid != generate_sid(epoch_ms=1710000000001)


def test_sid_uses_android_base64_default():
    assert generate_sid(epoch_ms=1712345678901) == "rIPj+3cmqQgizSSxkiLJuA==\n"


@pytest.mark.parametrize("key", ["", "short", "1234567890abcdefX"])
def test_transform_login_password_aes_invalid_key_raises_protocol_error(key: str):
    info = LoginCryptoInfo(idx="IDX", key=key, pwd_aes_cphd="Y")

    with pytest.raises(KorailProtocolError):
        transform_login_password("pw123", info)
