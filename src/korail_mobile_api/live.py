# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""환경변수로 실기기 값을 고정하는 보조 모듈.

:func:`build_config_from_env` 는 DynaPath 의 기기 식별자·OS·모델을 환경변수에서 읽어
:class:`~korail_mobile_api.config.KorailConfig` 를 만듭니다 — 프로세스를 넘어
안정적인 기기 식별자를 얻는 유일한 방법입니다.

라이브 호출은 ``KORAIL_MOBILE_API_LIVE=1`` 이 없으면 시작하지 않습니다
(:func:`live_enabled`).
"""
from __future__ import annotations

import os
import time

from .config import KorailConfig
from .constants import build_dalvik_user_agent
from .dynapath import (
    KORAIL_DYNAPATH_AS_VALUE,
    DynapathConfig,
    DynapathTokenSettings,
)


def live_enabled() -> bool:
    """``KORAIL_MOBILE_API_LIVE=1`` 인지. 라이브 호출의 유일한 스위치입니다."""
    return os.environ.get("KORAIL_MOBILE_API_LIVE") == "1"


def read_credentials_from_env() -> tuple[str, str]:
    """``KORAIL_MEMBER_NO``·``KORAIL_PASSWORD`` 를 읽어 짝으로 돌려줍니다.

    둘 중 하나라도 비어 있으면 ``RuntimeError`` 입니다. 이 패키지는 자격증명을 파일에서
    읽지 않습니다.
    """
    member_no = os.environ.get("KORAIL_MEMBER_NO")
    password = os.environ.get("KORAIL_PASSWORD")
    if not member_no or not password:
        raise RuntimeError("KORAIL_MEMBER_NO and KORAIL_PASSWORD are required for live smoke")
    return member_no, password


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    """기기 신원을 환경변수에서 가져온 :class:`KorailConfig`.

    맨손 ``KorailConfig()`` 는 DynaPath 가 꺼져 있어 로그인하지 못합니다.
    ``KorailConfig(enable_dynapath=True)`` 는 인스턴스마다 합성된 기기 값을 씁니다.
    이 함수는 **실제 값**을 고정하는 방법이고, 프로세스를 넘어 안정적인 기기 식별자를
    얻는 유일한 길입니다 — 이 패키지는 아무 상태도 저장하지 않으므로 합성 값은 그럴 수
    없습니다.

    세 변수는 필수이며 기본값이 없습니다. 여기서는 틀린 값이 없는 값보다 나쁩니다.

    ``KORAIL_DYNAPATH_DEVICE_ID``
        DynaPath 의 ``di``. 기기의 ``Settings.Secure.ANDROID_ID``
        (``AbstractC1228a.java:16``), 소문자 hex 16자.
    ``KORAIL_DYNAPATH_OS_VERSION``
        ``Build.VERSION.RELEASE``. 예: ``"15"``. SDK 정수가 아닙니다.
    ``KORAIL_DYNAPATH_DEVICE_MODEL``
        ``Build.MODEL``. 예: ``"SM-S928N"``.

    뒤의 둘은 일부러 두 번 쓰입니다. 토큰의 ``os``·``dm`` 으로 들어가고,
    :func:`~korail_mobile_api.constants.build_dalvik_user_agent` 를 통해
    ``User-Agent`` 로도 들어갑니다. 그래서 ``KORAIL_USER_AGENT`` 만 따로 덮어쓰면 토큰이
    뒷받침하지 않는 기기를 헤더에서 주장하게 됩니다.

    나머지는 환경변수로 덮어쓸 수 있고, 없으면 이렇게 떨어집니다. 광고 식별자
    (``KORAIL_ADVERTISING_ID``)와 ``KORAIL_DYNAPATH_AS_VALUE`` 는 패키지 기본값입니다.
    base URL(``KORAIL_BASE_URL``)은 ``https://smart.letskorail.com:443`` 이고, 화면
    크기(``KORAIL_DEVICE_WIDTH``/``KORAIL_DEVICE_HEIGHT``)와 SDK 정수
    (``KORAIL_ANDROID_SDK_INT``)는 패키지 기본값이 아니라 이 함수의 리터럴
    1440×3120, 37 입니다 — 이제는 근거가 있는 값입니다, 추측이 아닙니다:
    ``analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:5,10``
    (``sdk 37``, ``wm_size Physical size: 1440x3120``). SDK 37 은
    ``getprop.txt:1055`` 의 ``[ro.build.version.sdk]: [37]`` 로도 교차
    확인됩니다. 이 저장소에 있는 유일한 7.0.6 실기기 샘플입니다.
    """
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
        user_agent=os.environ.get(
            "KORAIL_USER_AGENT",
            build_dalvik_user_agent(
                os_release=os_version,
                device_model=device_model,
            ),
        ),
        # Fallbacks 1440x3120 / SDK 37 are grounded evidence, not a guess:
        # analysis/device-pull/2026-09-14_korail-7.0.6/device/summary.tsv:5
        # (`sdk 37`, cross-confirmed by getprop.txt:1055
        # `[ro.build.version.sdk]: [37]`) and summary.tsv:10 (`wm_size
        # Physical size: 1440x3120`) -- the only 7.0.6 device sample in this
        # repo. Width (1440) already matched the prior literal; height and
        # SDK did not (3088, 33) and are corrected here.
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", "1440")),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", "3120")),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", "37")),
        dynapath=dynapath,
        advertising_id=advertising_id,
    )
