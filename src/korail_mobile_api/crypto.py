"""로그인 비밀번호 변환과 ``Sid`` 생성.

``S4/C0812l.java`` 의 ``encryptAES`` + ``F4/a.java`` 의 ``encryptBase64`` 를
재현합니다. 안드로이드 ``Base64`` 기본 모드(76자마다 줄바꿈)를 씁니다.
"""
from __future__ import annotations

import base64
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .errors import KorailProtocolError
from .models import LoginCryptoInfo


SID_KEY = b"2485dd54d9deaa36"


def _aes_cbc_pkcs7_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _base64_no_wrap(data: bytes) -> str:
    """``Base64.encodeToString(..., NO_WRAP)`` — ``F4/a.java:47``."""
    return base64.b64encode(data).decode("ascii")


def _android_base64_default(data: bytes) -> str:
    """``Base64.encode(..., DEFAULT)`` — 76자마다 ``\\n``. ``S4/C0812l.java:23``."""
    return base64.encodebytes(data).decode("ascii")


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    key = info.key.encode("utf-8")
    if len(key) not in {16, 24, 32}:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    """``S4/C0812l.getAmountEncrypt`` 재현.

    ``"Y"``: AES-CBC(PKCS7), IV = key[:16] → Base64 DEFAULT → Base64 NO_WRAP.
    ``"N"``: Base64 NO_WRAP 만.
    키 길이 ∉ {16,24,32} 이면 :class:`~korail_mobile_api.errors.KorailProtocolError`.
    """
    if info.pwd_aes_cphd == "Y":
        key = _validate_login_crypto_key(info)
        iv = key[:16]
        try:
            encrypted = _android_base64_default(
                _aes_cbc_pkcs7_encrypt(password.encode("utf-8"), key, iv)
            )
        except ValueError as exc:
            raise KorailProtocolError(
                "KORAIL login crypto metadata contained an invalid AES key/IV"
            ) from exc
        return _base64_no_wrap(encrypted.encode("utf-8"))
    return _base64_no_wrap(password.encode("utf-8"))


def generate_sid(*, epoch_ms: int | None = None) -> str:
    """``S4/C0812l.getSid`` 재현.

    ``"AD" + millis`` 를 고정 키(:data:`SID_KEY`)로 AES-CBC 암호화 후
    Base64 DEFAULT. 키와 IV 가 같습니다(``C0812l.java:45``).
    """
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    encrypted = _aes_cbc_pkcs7_encrypt(
        f"AD{timestamp}".encode(),
        SID_KEY,
        SID_KEY,
    )
    return _android_base64_default(encrypted)
