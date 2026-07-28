"""로그인 비밀번호 변환과 ``Sid`` 생성.

로그인 폼에 실리는 비밀번호는 평문이 아니다. ``common.code.do`` 가 내려주는
암호화 파라미터(:class:`~korail_mobile_api.models.LoginCryptoInfo`)에 따라
:func:`transform_login_password` 가 변환한다.
:func:`generate_sid` 는 리무진 좌석이동 조회처럼 공통 ``Key`` 대신 요청마다
새 ``Sid`` 를 요구하는 폼에 쓴다.

두 함수 모두 안드로이드 ``Base64`` 의 기본 모드를 흉내 낸다. 그 모드는
76자마다 줄바꿈을 넣으므로, 결과 문자열에 개행이 들어가는 것이 정상이다.
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
    return base64.b64encode(data).decode("ascii")


def _android_base64_default(data: bytes) -> str:
    return base64.encodebytes(data).decode("ascii")


def _validate_login_crypto_key(info: LoginCryptoInfo) -> bytes:
    key = info.key.encode("utf-8")
    if len(key) not in {16, 24, 32}:
        raise KorailProtocolError("KORAIL login crypto metadata contained an invalid AES key/IV")
    return key


def transform_login_password(password: str, info: LoginCryptoInfo) -> str:
    """로그인 폼에 실을 비밀번호를 서버가 지정한 방식으로 변환한다.

    ``info.pwd_aes_cphd`` 가 ``"Y"`` 면 AES-128/192/256-CBC(PKCS7)로 암호화한다.
    키는 ``info.key`` 의 UTF-8 바이트이고 IV 는 그 앞 16바이트다. 결과를 안드로이드
    ``Base64`` 기본 모드로 한 번, 그 문자열을 줄바꿈 없는 Base64 로 다시 한 번
    감싼다. 두 번 감싸는 것이 앱의 동작이다.

    ``"N"`` 이면 암호화 없이 줄바꿈 없는 Base64 만 적용한다.

    키 길이가 16·24·32바이트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 다.
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
    """요청마다 새로 만드는 ``Sid`` 값.

    ``"AD"`` 에 밀리초 epoch 을 붙인 문자열을 고정 키
    (:data:`SID_KEY`, 키와 IV 가 같다)로 AES-CBC 암호화하고 안드로이드
    ``Base64`` 기본 모드로 인코딩한다. 그래서 값은 부를 때마다 다르고 76자마다
    개행이 들어간다.

    ``epoch_ms`` 는 시각을 고정하고 싶을 때만 준다. 주지 않으면 현재 시각이다.
    공통 ``Key`` 대신 이 값을 요구하는 폼은
    :func:`~korail_mobile_api.limousine_payloads.build_limousine_schedule_view_form`
    뿐이다.
    """
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    encrypted = _aes_cbc_pkcs7_encrypt(
        f"AD{timestamp}".encode(),
        SID_KEY,
        SID_KEY,
    )
    return _android_base64_default(encrypted)
