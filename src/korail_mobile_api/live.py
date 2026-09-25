# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""환경변수는 설정에만 사용하며 계정·카드 자격증명을 읽거나 저장하지 않습니다."""

from __future__ import annotations

import os
import time

from .config import KorailConfig
from .constants import KORAIL_API_USER_AGENT, build_dalvik_user_agent
from .dynapath import (
    KORAIL_DYNAPATH_AS_VALUE,
    DynapathConfig,
    DynapathTokenSettings,
)


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    """기기값은 토큰·대기열 UA에 공유하고 자격증명은 읽거나 저장하지 않습니다(a/a.java:15; a/b.java:85)."""
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    advertising_id = os.environ.get("KORAIL_ADVERTISING_ID", "")
    settings = DynapathTokenSettings(
        device_id=device_id,
        as_value=os.environ.get(
            "KORAIL_DYNAPATH_AS_VALUE",
            KORAIL_DYNAPATH_AS_VALUE,
        ),
        app_start_ts=str(int(time.time() * 1000)),
        os_version=os_version,
        device_model=device_model,
    )
    dynapath = DynapathConfig(
        enabled=True,
        token_settings=settings,
        device_name=device_model,
        os_version=os_version,
    )
    return KorailConfig(
        base_url=os.environ.get(
            "KORAIL_BASE_URL",
            "https://smart.letskorail.com:443",
        ),
        user_agent=os.environ.get("KORAIL_USER_AGENT", KORAIL_API_USER_AGENT),
        netfunnel_user_agent=os.environ.get("KORAIL_NETFUNNEL_USER_AGENT")
        or build_dalvik_user_agent(
            os_release=os_version,
            device_model=device_model,
            build_id=_required_env("KORAIL_ANDROID_BUILD_ID"),
        ),
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", "1440")),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", "3120")),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", "37")),
        dynapath=dynapath,
        advertising_id=advertising_id,
    )
