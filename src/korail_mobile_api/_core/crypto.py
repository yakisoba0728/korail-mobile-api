# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인 비밀번호 변환입니다. 안쪽은 줄바꿈 없는 표준 Base64, 바깥은 76자마다 줄을 바꾸는 URL-safe Base64입니다."""

from __future__ import annotations

import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .._domains.common.models import LoginCryptoInfo
from ..errors import KorailProtocolError


def _aes_cbc_pkcs7_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


_URL_SAFE = str.maketrans("+/", "-_")


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    try:
        key = info.key.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV") from exc
    if len(key) not in {16, 24, 32}:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    """평문 폴백 없이 관측된 CBC·이중 Base64를 유지하며 보호된 Cipher/IV는 미확인입니다."""
    # 입력 비밀번호의 UTF-8 오류를 서버 키/IV 오류로 잘못 감싸지 않도록 먼저 인코딩합니다.
    try:
        plain = password.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KorailProtocolError("KORAIL login password cannot be encoded as UTF-8") from exc
    if not info.key:
        raise KorailProtocolError(
            "KORAIL login crypto metadata missing an AES key; this library "
            "refuses to send the password in plain text"
        )
    key = _validate_login_crypto_key(info)
    iv = key[:16]
    try:
        cipher_bytes = _aes_cbc_pkcs7_encrypt(plain, key, iv)
    except ValueError as exc:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV") from exc
    inner = base64.b64encode(cipher_bytes)
    # 안드로이드 URL_SAFE 는 NO_WRAP 을 켜지 않으므로 76자마다 줄을 바꿉니다. 입력이 비지 않아 끝 줄바꿈도 붙습니다.
    return base64.encodebytes(inner).decode("ascii").translate(_URL_SAFE)
