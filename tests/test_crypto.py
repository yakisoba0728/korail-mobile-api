from korail_mobile_api.crypto import generate_sid, transform_login_password
from korail_mobile_api.models import LoginCryptoInfo


def test_transform_login_password_base64_only():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="N")
    assert transform_login_password("pw123", info) == "cHcxMjM="


def test_transform_login_password_aes_is_deterministic_and_not_plaintext():
    info = LoginCryptoInfo(idx="IDX", key="1234567890abcdef", pwd_aes_cphd="Y")
    first = transform_login_password("pw123", info)
    second = transform_login_password("pw123", info)
    assert first == second
    assert first != "pw123"
    assert first != "cHcxMjM="


def test_generate_sid_is_deterministic_with_epoch_ms():
    sid = generate_sid(epoch_ms=1710000000000)
    assert isinstance(sid, str)
    assert sid == generate_sid(epoch_ms=1710000000000)
    assert sid != generate_sid(epoch_ms=1710000000001)
