# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""한 기기의 DynaPath 값과 대기열 User-Agent를 함께 구성합니다."""

from dataclasses import dataclass, field, replace

from .config import KorailConfig
from .constants import (
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_HEIGHT,
    KORAIL_DEFAULT_DEVICE_WIDTH,
    build_dalvik_user_agent,
)


@dataclass(frozen=True)
class KorailDeviceProfile:
    """호출자가 보유한 기기값입니다. ``device_id``는 출력 표현에서 숨깁니다.

    같은 계정으로 반복 실행한다면 같은 프로파일을 보관해 사용하세요. 이 객체는
    자격 증명이나 세션을 담지 않으며, 실제 기기 여부를 검증하지 않습니다.
    """

    device_id: str = field(repr=False)
    model: str
    android_release: str
    build_id: str
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    height: int = KORAIL_DEFAULT_DEVICE_HEIGHT

    def __post_init__(self) -> None:
        for name in ("device_id", "model", "android_release", "build_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or "\r" in value or "\n" in value:
                raise ValueError(f"{name} must be a non-empty single-line string")
        for name in ("android_sdk_int", "width", "height"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")


def build_config_from_profile(
    profile: KorailDeviceProfile,
    *,
    base: KorailConfig | None = None,
) -> KorailConfig:
    """기기값을 DynaPath·대기열 UA·OS/화면 정보에 일관되게 적용합니다.

    API User-Agent는 앱 관측값인 ``korailtalk``를 유지합니다. 직접 지정한
    토큰 공급자나 DynaPath 비활성화 설정은 덮어쓰지 않습니다.
    """
    if not isinstance(profile, KorailDeviceProfile):
        raise TypeError("profile must be a KorailDeviceProfile")
    config = base if base is not None else KorailConfig()
    if config.disable_dynapath or config.dynapath.token_provider is not None:
        raise ValueError("a device profile requires configurable DynaPath token settings")
    settings = config.dynapath.token_settings
    if settings is None:
        raise ValueError("DynaPath token settings are missing")
    settings = replace(
        settings,
        device_id=profile.device_id,
        os_version=profile.android_release,
        device_model=profile.model,
    )
    return replace(
        config,
        dynapath=replace(
            config.dynapath,
            enabled=True,
            token_settings=settings,
            device_name=profile.model,
            os_version=profile.android_release,
        ),
        netfunnel_user_agent=build_dalvik_user_agent(
            os_release=profile.android_release,
            device_model=profile.model,
            build_id=profile.build_id,
        ),
        android_sdk_int=profile.android_sdk_int,
        device_width=profile.width,
        device_height=profile.height,
    )
