# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""환경변수는 설정에만 사용하며 계정·카드 자격증명을 읽거나 저장하지 않습니다."""

from __future__ import annotations

import os

from .config import KorailConfig
from .constants import (
    KORAIL_API_USER_AGENT,
    KORAIL_API_VERSION,
    KORAIL_APP_VERSION,
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_HEIGHT,
    KORAIL_DEFAULT_DEVICE_WIDTH,
    build_dalvik_user_agent,
)
from .dynapath import DynapathConfig, _DiagnosticTokenProvider


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    """환경변수에서 실제 기기 값을 읽어 DynaPath를 켠 ``KorailConfig``를 만듭니다.

    ``KORAIL_DYNAPATH_DEVICE_ID``, ``KORAIL_DYNAPATH_OS_VERSION``, ``KORAIL_DYNAPATH_DEVICE_MODEL``은 반드시 있어야 하며,
    ``KORAIL_NETFUNNEL_USER_AGENT``를 지정하지 않으면 ``KORAIL_ANDROID_BUILD_ID``도 필요합니다. 기기 모델과 OS 버전은
    DynaPath 토큰과 대기열 ``User-Agent``에 함께 씁니다. 나머지 값은 ``KORAIL_BASE_URL``, ``KORAIL_USER_AGENT``,
    ``KORAIL_DEVICE_WIDTH``, ``KORAIL_DEVICE_HEIGHT``, ``KORAIL_ANDROID_SDK_INT``,
    ``KORAIL_ADVERTISING_ID``로 바꿀 수 있습니다. ``KORAIL_APP_VERSION``과 ``KORAIL_API_VERSION``은 요청의
    ``AppVersion``과 ``Version``이 되며 비어 있으면 기본값을 씁니다. ``KORAIL_PROXY``는 ``proxy``가 되며 비어 있으면 지정하지 않습니다.
    로그인 정보나 카드 정보는 환경변수에서 읽지 않습니다.

    필요한 환경변수가 없거나 빈 값이면 ``RuntimeError``가 발생합니다. ``KORAIL_DEVICE_WIDTH``, ``KORAIL_DEVICE_HEIGHT``,
    ``KORAIL_ANDROID_SDK_INT``가 정수가 아니거나 ``KORAIL_PROXY``가 올바른 프록시 URL이 아니면 ``ValueError``가 발생합니다."""
    # 기기값은 토큰·대기열 UA에 공유하고 자격증명은 읽거나 저장하지 않습니다(a/a.java:15; a/b.java:85).
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    if any(not value.strip() for value in (device_id, os_version, device_model)):
        raise ValueError("DynaPath device values must not be whitespace")
    advertising_id = os.environ.get("KORAIL_ADVERTISING_ID", "")
    dynapath = DynapathConfig(
        enabled=True,
        token_provider=_DiagnosticTokenProvider(
            os_version=os_version.encode("utf-8"),
            device_model=device_model.encode("utf-8"),
            install_id=device_id.encode("utf-8"),
        ),
        device_name=device_model,
        os_version=os_version,
    )
    return KorailConfig(
        base_url=os.environ.get(
            "KORAIL_BASE_URL",
            "https://smart.letskorail.com:443",
        ),
        version=os.environ.get("KORAIL_API_VERSION") or KORAIL_API_VERSION,
        app_version=os.environ.get("KORAIL_APP_VERSION") or KORAIL_APP_VERSION,
        user_agent=os.environ.get("KORAIL_USER_AGENT", KORAIL_API_USER_AGENT),
        netfunnel_user_agent=os.environ.get("KORAIL_NETFUNNEL_USER_AGENT")
        or build_dalvik_user_agent(
            os_release=os_version,
            device_model=device_model,
            build_id=_required_env("KORAIL_ANDROID_BUILD_ID"),
        ),
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", KORAIL_DEFAULT_DEVICE_WIDTH)),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", KORAIL_DEFAULT_DEVICE_HEIGHT)),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", KORAIL_DEFAULT_ANDROID_SDK_INT)),
        dynapath=dynapath,
        advertising_id=advertising_id,
        proxy=os.environ.get("KORAIL_PROXY") or None,
    )
