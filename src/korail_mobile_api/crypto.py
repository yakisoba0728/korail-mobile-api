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
    return base64.b64encode(data).decode("ascii")


def _android_base64_default(data: bytes) -> str:
    return base64.encodebytes(data).decode("ascii")


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    key = info.key.encode("utf-8")
    if len(key) not in {16, 24, 32}:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    if info.pwd_aes_cphd == "Y":
        key = _validate_login_crypto_key(info)
        iv = key[:16]
        try:
            encrypted = _android_base64_default(
                _aes_cbc_pkcs7_encrypt(password.encode("utf-8"), key, iv)
            )
        except ValueError as exc:
            raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV") from exc
        return _base64_no_wrap(encrypted.encode("utf-8"))
    return _base64_no_wrap(password.encode("utf-8"))


def generate_sid(*, epoch_ms: int | None = None) -> str:
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    encrypted = _aes_cbc_pkcs7_encrypt(
        f"AD{timestamp}".encode("utf-8"),
        SID_KEY,
        SID_KEY,
    )
    return _android_base64_default(encrypted)
