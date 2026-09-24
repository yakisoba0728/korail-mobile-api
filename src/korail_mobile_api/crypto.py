# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인 비밀번호 변환. 안쪽·바깥쪽 Base64 의 모드가 다릅니다; 각 헬퍼의 근거를 참고하십시오."""
from __future__ import annotations

import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .errors import KorailProtocolError
from .models import LoginCryptoInfo


def _aes_cbc_pkcs7_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _base64_no_wrap(data: bytes) -> str:
    """안쪽 Base64: 표준 알파벳·줄바꿈 없음. 7.0.6 근거: AESCrypto.java:182 의 flag 2."""
    return base64.b64encode(data).decode("ascii")


def _android_base64_url_safe_wrapped(data: bytes) -> str:
    """바깥쪽 Base64: URL_SAFE(flag 8), 패딩 유지, 76자마다 및 끝에 줄바꿈.

    URL_SAFE 만으로 NO_WRAP 이 켜지지 않습니다. 로그인 호출: LoginRepositoryImpl.java:929-931,1245. 안쪽 flag 2 와 혼동하지 마십시오."""
    b64 = base64.urlsafe_b64encode(data).decode("ascii")
    lines = [b64[i : i + 76] for i in range(0, len(b64), 76)]
    return "\n".join(lines) + "\n"


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    try:
        key = info.key.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KorailProtocolError(
            "KORAIL login crypto metadata contained an invalid AES key/IV"
        ) from exc
    if len(key) not in {16, 24, 32}:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    """AES-CBC/PKCS7 암호문에 안쪽·바깥쪽 Base64 를 적용합니다.

    두 Base64 단계: LoginRepositoryImpl.java:929-931,1245, AESCrypto.java:182. Cipher transformation 과 IV 가공은
    보호돼 있어(AESCrypto.java:31,60-83) CBC/PKCS7·key[:16] 은 디컴파일로 확정하지 못했지만, 실서버 로그인은 이 방식으로
    성공합니다. 앱은 빈 키를 재조회합니다(LoginRepositoryImpl.java:1230-1234). 이 함수는 재조회하지 않고 빈 키·지원하지 않는
    길이를 KorailProtocolError 로 거절하여 평문 폴백을 막습니다. 키 구성 근거: AESCrypto.java:45-57."""
    # 입력 비밀번호의 UTF-8 오류를 서버 키/IV 오류로 잘못 감싸지 않도록 먼저 인코딩합니다.
    try:
        plain = password.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KorailProtocolError(
            "KORAIL login password cannot be encoded as UTF-8"
        ) from exc
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
        raise KorailProtocolError(
            "KORAIL login crypto metadata contained an invalid AES key/IV"
        ) from exc
    inner = _base64_no_wrap(cipher_bytes)
    return _android_base64_url_safe_wrapped(inner.encode("utf-8"))

