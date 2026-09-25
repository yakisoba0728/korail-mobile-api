# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""환경변수에서 기기 설정을 읽습니다. DynapathConfig 를 직접 구성하는 방법도 있습니다."""

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
    """환경변수로 KorailConfig 를 만듭니다. 자격증명이나 상태는 저장하지 않습니다.

    필수: KORAIL_DYNAPATH_DEVICE_ID(android_id), KORAIL_DYNAPATH_OS_VERSION(Build.VERSION.RELEASE),
    KORAIL_DYNAPATH_DEVICE_MODEL(Build.MODEL), KORAIL_ANDROID_BUILD_ID(Build.ID). ID 근거: a/a.java:15,
    a/b.java:85. OS·모델은 토큰과 대기열 User-Agent 에 함께 쓰고 Build ID 는 대기열 User-Agent 에만 씁니다.
    KORAIL_NETFUNNEL_USER_AGENT 를 주면 Build ID 는 필요 없지만 토큰 기기값과 달라질 수 있습니다. API User-Agent 는 기기와
    무관한 앱 값이며 KORAIL_USER_AGENT 로 바꿀 수 있습니다.

    선택 변수와 기본값은 아래 구성 코드를 따릅니다. 화면 1440×3120·SDK 37 의 원 근거는
    analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:5,10 및 getprop.txt:1055 입니다. 이는 특정 실기기 표본이지
    모든 단말의 기본값은 아닙니다."""
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
