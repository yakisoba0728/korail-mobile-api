# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""API·대기열·기기 설정을 제공합니다. 기본값은 constants를 따르며 앱의 실기기 값과 같다는 보장은 없습니다. DynaPath는 설정마다 합성 기기값으로 켜집니다. 환경변수 구성은
live.build_config_from_env, 명시적 비활성화는 disable_dynapath를 사용합니다."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from .constants import (
    KORAIL_API_VERSION,
    KORAIL_APP_KEY,
    KORAIL_BASE_URL,
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_HEIGHT,
    KORAIL_DEFAULT_DEVICE_WIDTH,
    KORAIL_DEVICE_ANDROID,
    KORAIL_NETFUNNEL_TIMEOUT_SECONDS,
    KORAIL_NETFUNNEL_URL,
    KORAIL_TIMEOUT_SECONDS,
    KORAIL_USER_AGENT,
)
from .dynapath import DynapathConfig, build_default_token_settings


def enabled_dynapath_config() -> DynapathConfig:
    """설정 간 식별자·시작 시각을 공유하지 않도록 DynaPath 기기 값을 새로 합성합니다."""
    return DynapathConfig(
        enabled=True,
        token_settings=build_default_token_settings(),
    )


@dataclass(frozen=True)
class KorailConfig:
    """API·대기열·기기·인증 토큰의 요청 설정을 구성합니다. base_url·netfunnel_url 은 검사하지 않고 그대로 씁니다 — 다른 곳을 가리키면 로그인 자격증명도 그리로
    갑니다."""

    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    user_agent: str = KORAIL_USER_AGENT
    #: 기본 구성은 합성값으로 활성화됩니다. 직접 넘긴 enabled=True 구성은 유지합니다.
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: 기본 활성화. 관문 목록은 아래 netfunnel_actions 참고. 7.0.6 SDK 기본 bypass 는
    #: 거짓(com/netfunnel/api/Property.java:8), 앱 설정은 KorailTalkApplication.java:361-389. 실제 호출 여부는 각 클라이언트 메서드와 앱
    #: 호출부에 따릅니다.
    netfunnel_enabled: bool = True
    #: lang은 CommonIn.java:381의 필드이며 평문은 보호돼 None이면 생략합니다. 필드명 상수는 com/kakao/sdk/common/Constants.java:27을 따릅니다.
    lang: str | None = None
    #: 누적 대기 상한(초)이며 None이면 제한하지 않습니다. 초과 시 API를 보내지 않습니다. SDK 루프에는 상한이 없으며(Netfunnel.java:622-664), 앱 콜백 감시의
    #: 단위·차이는 netfunnel 모듈을 따릅니다.
    netfunnel_wait_limit: float | None = None
    #: 관문 이름 → ``aid`` 덮어쓰기. 이름은 inquiry·peak_season_inquiry·product_inquiry·reserve·pay·reservation_view
    #: 입니다. ``aid`` 리터럴은 7.0.6 에서 보호돼 있어 기본값은 길이·호출부 이름으로 고른 **미검증** 값입니다
    #: (netfunnel.KORAIL_NETFUNNEL_GATES).
    netfunnel_actions: Mapping[str, str] | None = None

    #: disable_dynapath는 명시적으로 토큰을 끕니다. 필수 경로는 전송 전에 거절됩니다. 2026-09-24 토큰 없는 조회의 차단 관측은
    #: constants.DYNAPATH_REQUIRED_PATHS를 따릅니다.
    disable_dynapath: bool = False

    def __post_init__(self) -> None:
        default = DynapathConfig()
        if self.disable_dynapath:
            if self.dynapath.enabled:
                raise ValueError("disable_dynapath=True conflicts with an enabled DynapathConfig")
            return
        if self.dynapath.enabled:
            return
        # 비활성 구성을 합성값으로 덮지 않고 명시적 disable_dynapath 사용을 요구합니다.
        if self.dynapath != default:
            raise ValueError(
                "pass disable_dynapath=True to turn DynaPath off, or "
                "DynapathConfig(enabled=True, ...) to supply your own"
            )
        object.__setattr__(self, "dynapath", enabled_dynapath_config())
