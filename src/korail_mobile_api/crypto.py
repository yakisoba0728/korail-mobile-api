from __future__ import annotations

import base64
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .errors import KorailProtocolError
from .models import LoginCryptoInfo

SID_KEY = b"2485dd54d9deaa36"


def _aes_cbc_pkcs7_encrypt_to_base64(plaintext: bytes, key: bytes, iv: bytes) -> str:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    key = info.key.encode("utf-8")
    if len(key) != 16:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    if info.pwd_aes_cphd == "Y":
        key = _validate_login_crypto_key(info)
        try:
            encrypted = _aes_cbc_pkcs7_encrypt_to_base64(password.encode("utf-8"), key, key)
        except ValueError as exc:
            raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV") from exc
        return base64.b64encode(encrypted.encode("utf-8")).decode("ascii")
    return base64.b64encode(password.encode("utf-8")).decode("ascii")


def generate_sid(*, epoch_ms: int | None = None) -> str:
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    return _aes_cbc_pkcs7_encrypt_to_base64(f"AD{timestamp}".encode("utf-8"), SID_KEY, SID_KEY)
