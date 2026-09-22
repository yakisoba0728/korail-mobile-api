# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""로그인 비밀번호 변환과 ``Sid`` 생성.

6.5.0 인용(``S4/C0812l.java`` 의 ``encryptAES`` + ``F4/a.java`` 의
``encryptBase64``)은 스테일하지만 실질은 7.0.6 에서 확인됐습니다:
``LoginRepositoryImpl.java:929-931,1245`` (로그인 비밀번호 이중 Base64,
``AppSuitLinker2.AAISCVWJBPDORLBWPVALUHGTIELXZNGS`` →
``android.util.Base64.encodeToString(byte[], int)``) 와
``AESCrypto.java:182`` (내부 AES 암호문 인코딩). 안쪽과 바깥쪽이 쓰는
안드로이드 ``Base64`` 모드는 서로 다릅니다 — 아래 각 헬퍼의 독스트링 참고.
``generate_sid`` 는 별개 경로이며 여전히 ``Base64`` 기본 모드(76자마다
줄바꿈)만 씁니다. **그 경로는 로그인 비밀번호 쪽과 달리 7.0.6 에서 다시
확인되지 않았습니다** — ``getSid`` 도, ``Sid`` 와이어 필드도, flag 0
Base64 호출부도 7.0.6 에 없습니다. 자세한 확인 범위와 결론(미출처)은
:func:`generate_sid` 와 :func:`_android_base64_default` 의 독스트링에
있습니다.
"""
from __future__ import annotations

import base64
import time

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

from .errors import KorailProtocolError
from .models import LoginCryptoInfo


#: ``getSid`` 의 고정 AES 키이자 IV. **미출처** — 6.5.0 기원이며 7.0.6
#: 디컴파일에 이 리터럴도, 이 값을 쓰는 코드도 없습니다. 왜 그렇게
#: 판정했는지는 :func:`generate_sid` 의 독스트링에 있습니다.
SID_KEY = b"2485dd54d9deaa36"


def _aes_cbc_pkcs7_encrypt(plaintext: bytes, key: bytes, iv: bytes) -> bytes:
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _base64_no_wrap(data: bytes) -> str:
    """``Base64.encodeToString(..., NO_WRAP)`` — flag 2, 표준 ``+/`` 알파벳,
    줄바꿈 없음. ``F4/a.java:47`` 은 6.5.0 시절 난독화 이름이고 그 경로는
    7.0.6 디컴파일에 없습니다 — ``F4`` 라는 최상위 패키지 자체가 jadx/smali
    어디에도 없으므로 철회된 인용입니다. 7.0.6 에서는
    ``AESCrypto.java:182`` 의 ``Base64.encodeToString(cipherBytes, 2)`` —
    AES 암호문 바이트를 직접 감싸는 **안쪽** 인코딩이다
    (:func:`transform_login_password` 참고)."""
    return base64.b64encode(data).decode("ascii")


def _android_base64_default(data: bytes) -> str:
    """``Base64.encode(..., DEFAULT)`` — flag 0, 76자마다 ``\\n``, 표준 알파벳.

    **7.0.6 에 대응 호출부가 없습니다 — 미출처.** 스테일 인용
    ``S4/C0812l.java:23`` 은 6.5.0 난독화 이름이고 그 경로가 7.0.6 디컴파일에
    없습니다. 그래서 7.0.6 에서 ``android.util.Base64.encodeToString(byte[],
    int)`` 로 해소되는 디스패처
    (``AppSuitLinker2.AAISCVWJBPDORLBWPVALUHGTIELXZNGS``)의 호출부를 전수로
    훑어 플래그를 읽었는데, **여덟 곳 전부 flag 2 아니면 flag 8 이고 flag 0
    은 하나도 없습니다**:

    * flag 2 (``NO_WRAP``) — ``AESCrypto.java:182``,
      ``DisabilityViewModel.java:314``, ``PayViewModel.java:11001``, 그리고
      ``PayViewModel.java:11022``(디스패처 id 를 ``:11018`` 에서 읽고 호출은
      ``:11022``. 여기만 플래그가 리터럴이 아니라 ``:11017`` 의
      ``parseInt(AlienGuard…) > 3 ? 3 : 2`` 로 들어오는데, 이 저장소가 확인한
      AppSuit 정수 관용구에서 그 보호 리터럴은 1 이므로 결과는 2).
    * flag 8 (``URL_SAFE``) — ``LoginRepositoryImpl.java:931``, ``:1245``,
      ``CryptoWithKeyStore.java:308``, ``:310``(디스패처 id 는 ``:307``).

    이 함수가 남아 있는 이유는 :func:`generate_sid` 하나뿐인데, 그
    :func:`generate_sid` 자체도 7.0.6 에 대응이 없습니다(아래 참고).
    로그인 비밀번호의 바깥쪽 인코딩은 이것이 아니라
    :func:`_android_base64_url_safe_wrapped` 다.
    """
    return base64.encodebytes(data).decode("ascii")


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
    ``CryptoWithKeyStore.java:308``, ``:310``)으로 갈린다. (이전 주석은
    "다른 세 호출부가 전부 플래그 2" 라고 적었는데, 호출부 수를 적게 셌고
    ``CryptoWithKeyStore`` 의 flag 8 두 곳을 빠뜨린 것이었다 — 다만 **로그인
    비밀번호 경로에서 안쪽이 2·바깥쪽이 8** 이라는 결론 자체는 그대로다.)
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

    이전 구현은 이 둘의 wrap/알파벳 배정이 정확히 반대였다(안쪽이 76자
    wrap+표준, 바깥쪽이 NO_WRAP+표준) — AES 암호문에 ``+``/``/`` 가 하나라도
    들어가면 최종 ``txtPwd`` 가 앱과 달라지는 결함이었다.

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


def generate_sid(*, epoch_ms: int | None = None) -> str:
    """6.5.0 ``getSid`` 재현 — **7.0.6 에 대응이 없습니다.**

    ``"AD" + millis`` 를 고정 키(:data:`SID_KEY`)로 AES-CBC 암호화한 뒤
    Base64 DEFAULT 로 감쌉니다. 키와 IV 가 같습니다.

    **인용 정리 (2026-09-22).** 옛 인용 ``S4/C0812l.getSid`` 와
    ``C0812l.java:45``("키와 IV 가 같다" 의 근거)는 6.5.0 난독화 이름이고 그
    경로가 7.0.6 디컴파일에 없습니다. 7.0.6 에서 대응을 찾으려고 세 방향으로
    훑었지만 전부 빈손이었습니다:

    * ``getSid``/``makeSid`` 라는 이름의 메서드가 ``com/korail/talk/`` 아래에
      없습니다.
    * ``Sid`` 를 와이어 키로 쓰는 DTO 가 없습니다 —
      ``com/korail/talk/network/model/`` 의 1181개 모델 어디에도 ``Sid``
      ``@SerialName`` 이나 ``sid`` 속성/게터가 없습니다.
    * 이 함수가 쓰는 flag 0 Base64 도 7.0.6 호출부가 없습니다
      (:func:`_android_base64_default` 의 전수 목록 참고).

    따라서 :data:`SID_KEY` 의 리터럴 ``2485dd54d9deaa36`` 과 ``"AD" + millis``
    라는 평문 조립, 키=IV 라는 성질은 셋 다 **미출처**입니다 — 6.5.0 기원이며
    구버전 APK 없이 확정 불가입니다. 값을 손대지 않은 것은 확인돼서가 아니라
    이번 정리가 주석·독스트링 한정이기 때문입니다.

    .. note::
       **이 함수의 결과는 현재 와이어에 실리지 않습니다.**
       :mod:`korail_mobile_api.client` 가 세 곳에서 ``sid=generate_sid()`` 로
       넘기지만, 받는 :mod:`korail_mobile_api.payloads` 의 빌더들이 ``sid``
       를 폼에 넣지 않습니다 — 해당 라우트의 7.0.6 ``@SerialName`` 목록에
       ``Sid`` 가 없기 때문입니다(그쪽 독스트링에 라우트별로 적혀 있습니다).
       즉 계산만 하고 버립니다. 지우는 것이 맞아 보이지만 공개면 변경이라
       여기서는 손대지 않았습니다.
    """
    timestamp = epoch_ms if epoch_ms is not None else int(time.time() * 1000)
    encrypted = _aes_cbc_pkcs7_encrypt(
        f"AD{timestamp}".encode(),
        SID_KEY,
        SID_KEY,
    )
    return _android_base64_default(encrypted)
