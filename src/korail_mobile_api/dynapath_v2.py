# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""DynaPath SDK 2.0.1이 native 라이브러리를 쓰지 못할 때 보내는 평문 진단 헤더를 만듭니다.

등록한 기기 키로 서명한 요청 토큰이 아니며 기기 등록·무결성·attestation이나 서버 수용을 뜻하지 않습니다.
기본 설정은 계속 기존 v1.0.3 생성기를 쓰고, 이 헤더는 ``DynapathConfig(token_provider=...)``로 고를 때만 보냅니다."""

# 상태값·필드 순서는 앱과 따로 대조하지 않았고, 이 헤더의 실서버 수용도 확인하지 않았습니다.

from __future__ import annotations

import base64
import re

from .dynapath import DynapathRequestContext

DYNAPATH_V2_SDK_VERSION = "2.0.1"
DYNAPATH_V2_APP_ID = "korailplus"
#: native 라이브러리를 쓸 수 없을 때 SDK가 보고하는 상태값입니다.
DYNAPATH_V2_NATIVE_UNAVAILABLE_STATE = 165489088780120535

# SDK 는 앱 ID 를 이스케이프하지 않고 그대로 넣으므로 구분자(&, =)·제어 문자가 없는 ASCII 식별자만 받습니다.
_APP_ID = re.compile(r"[A-Za-z0-9._-]+", re.ASCII)
_JAVA_LONG = (-(1 << 63), (1 << 63) - 1)
_JAVA_NONNEGATIVE_INT = (0, (1 << 31) - 1)


def _require_int(value: object, name: str, bounds: tuple[int, int]) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an int")
    low, high = bounds
    if not low <= value <= high:
        raise ValueError(f"{name} is outside the SDK integer range")
    return value


def _urlsafe_b64(value: object, name: str) -> str:
    """SDK 처럼 URL-safe 알파벳으로 인코딩하고 패딩(``=``)을 뗍니다."""
    if not isinstance(value, bytes):
        raise TypeError(f"{name} must be bytes")
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_dynapath_v2_diagnostic_header(
    *,
    state: int = DYNAPATH_V2_NATIVE_UNAVAILABLE_STATE,
    app_id: str = DYNAPATH_V2_APP_ID,
    os_version: bytes | None = None,
    device_model: bytes | None = None,
    install_id: bytes | None = None,
    manufacturer: bytes | None = None,
    board: bytes | None = None,
    sdk_int: int | None = None,
) -> str:
    """SDK 2.0.1의 평문 진단 헤더(``2!v=2&es=...``)를 만듭니다.

    기본값은 native를 쓸 수 없다는 상태와 앱 ID만 담고 기기 정보는 싣지 않습니다. 기기 정보는 관측한 값을 바이트로
    넘길 때만 URL-safe Base64로 넣으며, ``None``은 필드를 빼고 빈 바이트는 빈 값을 보냅니다. ``sdk_int``는 안드로이드
    SDK 정수입니다. 라이브러리는 기기 정보를 추측하지 않습니다. 기본 상태가 아닌 ``state``의 의미는 확인하지 않았습니다.

    ``state``는 Java ``long``, ``sdk_int``는 0 이상의 Java ``int`` 범위여야 하며 ``bool``은 받지 않습니다. 잘못된 타입은
    ``TypeError``, 범위 밖의 값이나 구분자가 들어간 ``app_id``는 ``ValueError``입니다."""
    _require_int(state, "state", _JAVA_LONG)
    if not isinstance(app_id, str):
        raise TypeError("app_id must be a str")
    if _APP_ID.fullmatch(app_id) is None:
        raise ValueError("app_id must be a nonempty ASCII identifier")
    if sdk_int is not None:
        _require_int(sdk_int, "sdk_int", _JAVA_NONNEGATIVE_INT)

    fields = [
        ("v", "2"),
        ("es", str(state)),
        ("st", "Android"),
        ("sv", DYNAPATH_V2_SDK_VERSION),
        ("ai", app_id),
    ]
    for name, value in (
        ("os", os_version),
        ("dm", device_model),
        ("iid", install_id),
        ("mf", manufacturer),
        ("bd", board),
    ):
        if value is not None:
            fields.append((name, _urlsafe_b64(value, name)))
    if sdk_int is not None:
        fields.append(("sl", str(sdk_int)))
    return "2!" + "&".join(f"{name}={value}" for name, value in fields)


def dynapath_v2_diagnostic_token(context: DynapathRequestContext) -> str:
    """``DynapathConfig.token_provider``로 쓰는 공급자입니다. 요청과 무관하게 기본 진단 헤더를 돌려줍니다.

    요청 문맥(경로·본문)으로 서명하지 않으며, 헤더를 붙일 경로는 ``DynapathConfig.allowlist_paths``가 정합니다."""
    return build_dynapath_v2_diagnostic_header()
