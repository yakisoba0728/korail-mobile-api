# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인 비밀번호 변환.

7.0.6 근거: ``LoginRepositoryImpl.java:929-931,1245`` (로그인 비밀번호 이중 Base64,
``AppSuitLinker2.AAISCVWJBPDORLBWPVALUHGTIELXZNGS`` →
``android.util.Base64.encodeToString(byte[], int)``) 와
``AESCrypto.java:182`` (내부 AES 암호문 인코딩). 안쪽과 바깥쪽이 쓰는
안드로이드 ``Base64`` 모드는 서로 다릅니다 — 아래 각 헬퍼의 독스트링 참고.
"""
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
    """``Base64.encodeToString(..., NO_WRAP)`` — flag 2, 표준 ``+/`` 알파벳,
    줄바꿈 없음. 7.0.6 에서는
    ``AESCrypto.java:182`` 의 ``Base64.encodeToString(cipherBytes, 2)`` —
    AES 암호문 바이트를 직접 감싸는 **안쪽** 인코딩이다
    (:func:`transform_login_password` 참고)."""
    return base64.b64encode(data).decode("ascii")


def _android_base64_url_safe_wrapped(data: bytes) -> str:
    """``Base64.encodeToString(data, Base64.URL_SAFE)`` — flag 8.

    ``URL_SAFE`` 는 알파벳의 ``+``/``/`` 를 ``-``/``_`` 로 바꿀 뿐, 그 자체로는
    ``NO_WRAP`` 을 켜지 않는다 — 안드로이드 ``Base64.DEFAULT`` 와 같은
    76자마다 줄바꿈(각 줄 뒤 ``\\n``, 끝에도 ``\\n``)이 그대로 적용된다.
    패딩도 ``NO_PADDING`` 을 별도로 켜지 않는 한 표준과 동일하게 ``=`` 를
    쓴다(flag 8 은 ``NO_PADDING`` 비트를 포함하지 않는다).

    7.0.6 ``LoginRepositoryImpl`` 이 안쪽 Base64 문자열의 UTF-8 바이트에
    적용하는 **바깥쪽** 인코딩이다 — ``LoginRepositoryImpl.java:929-931``
    (재조회 분기의 미러는 ``:1245``): ``bArr = 안쪽문자열.getBytes(UTF_8)``
    다음 ``AppSuitLinker2.AAISCVWJBPDORLBWPVALUHGTIELXZNGS(bArr, 8)`` 가
    ``android.util.Base64.encodeToString(byte[], int)`` 로 해소되며 플래그가
    8 이다. 같은 디스패처의 호출부는 7.0.6 전체에서 여덟 곳이고 flag 2 네 곳
    (``AESCrypto.java:182``, ``DisabilityViewModel.java:314``,
    ``PayViewModel.java:11001``, ``:11022``)과 flag 8 네 곳
    (``LoginRepositoryImpl.java:931``, ``:1245``,
    ``CryptoWithKeyStore.java:308``, ``:310``)으로 갈린다. **로그인
    비밀번호 경로에서는 안쪽이 2·바깥쪽이 8** 이다.
    """
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
    """``LoginRepositoryImpl.login`` 의 비밀번호 변환 재현.

    **AES 분기 (``key`` 가 있을 때)** — 이중 Base64 의 wrap/알파벳 배정이
    확인됐다(``LoginRepositoryImpl.java:929-931,1245``, ``AESCrypto.java:182``):

    - 안쪽: AES-CBC/PKCS7 암호문 바이트에 그대로
      :func:`_base64_no_wrap` — NO_WRAP + 표준 ``+/`` 알파벳.
    - 바깥쪽: 안쪽 결과 문자열의 UTF-8 바이트에
      :func:`_android_base64_url_safe_wrapped` — URL_SAFE 알파벳
      (``-``/``_``) 이면서 76자마다 줄바꿈(DEFAULT 와 같은 wrap).

    **``key`` 가 빈 경우** — 7.0.6 에는 암호화를 건너뛰고 평문을 보내는
    분기가 없다. ``LoginRepositoryImpl`` 은 ``key.length()==0`` 이면
    ``commonCode`` 를 한 번 더 호출해 새 키를 받아오고
    (``LoginRepositoryImpl.java:1230-1234``), 그래도 비어 있으면
    ``AESCrypto`` 가 ``SecretKeySpec(new byte[0], "AES")`` 에서 크래시한다
    (``AESCrypto.java:45-57``). 이 라이브러리에는 그 재조회 루프가 없으므로,
    평문을 내보내는 대신 :class:`~korail_mobile_api.errors.KorailProtocolError`
    를 던진다 — 자격증명이 걸린 값이라 조용한 평문 폴백보다 실패가 낫다.

    키 길이 ∉ {16,24,32} 이면 마찬가지로
    :class:`~korail_mobile_api.errors.KorailProtocolError`.
    """
    # Encoded before either branch: a password that cannot be UTF-8 (a lone
    # surrogate) is the caller's input, and UnicodeEncodeError is a
    # ValueError that the key/IV handler would otherwise report as bad
    # server metadata.
    try:
        plain = password.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise KorailProtocolError(
            "KORAIL login password cannot be encoded as UTF-8"
        ) from exc
    if not info.key:
        raise KorailProtocolError(
            "KORAIL login crypto metadata missing an AES key; the 7.0.6 app "
            "never sends a plaintext password (it retries commonCode once, "
            "then AESCrypto crashes on an empty key) so this library refuses "
            "instead of leaking the password"
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

