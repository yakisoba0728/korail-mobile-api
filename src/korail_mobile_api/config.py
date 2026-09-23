# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청마다 실리는 설정값 — :class:`KorailConfig`.

기본값은 앱 v6.5.0 이 보내는 값입니다. DynaPath 는 기본으로 꺼져 있고,
``enable_dynapath=True`` 로 켜면 :func:`enabled_dynapath_config` 가 설정 객체마다
기기 값을 새로 합성합니다. 실제 단말 값을 고정하려면
:func:`~korail_mobile_api.live.build_config_from_env` 를 씁니다.
"""

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
    """DynaPath 를 켜고 기기 값을 새로 합성합니다.

    호출마다 :func:`~korail_mobile_api.dynapath.build_default_token_settings`
    를 새로 부릅니다 — 설치별 식별자와 시작 시각이 들어 있어 공유하면 봇
    서명이 됩니다.
    """
    return DynapathConfig(
        enabled=True,
        token_settings=build_default_token_settings(),
    )


@dataclass(frozen=True)
class KorailConfig:
    """매 요청에 싣는 값들.

    ``KorailConfig()`` 인자 없이 만들면 앱 v6.5.0 의 기본값이 채워집니다.
    ``base_url`` = ``smart.letskorail.com``, ``netfunnel_url`` =
    ``nf.letskorail.com`` 으로 각각 오리진 검사됩니다.
    """

    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    user_agent: str = KORAIL_USER_AGENT
    #: DynaPath 구성. 기본은 **꺼짐**. ``enable_dynapath`` 로 켜거나
    #: 여기에 직접 넘기면 됩니다.
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: NetFunnel 가상 대기열. 기본 거짓 — 거짓인 동안
    #: :class:`~korail_mobile_api.netfunnel.KorailNetFunnelClient` 생성 자체가
    #: 거절됩니다. 대기열 토큰 없이도 모든 호출이 통과하는 상태라 끌 이유가
    #: 있어야만 켭니다.
    netfunnel_enabled: bool = False
    #: DynaPath 안티오토메이션을 켭니다. **기본은 거짓.**
    #: 켜지 않은 채
    #: :data:`~korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS` 를 부르면
    #: :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError` 로 막힘.
    #:
    #: ``dynapath`` 에 ``enabled=True`` 인 구성을 넘겼다면 이 플래그는 무시됩니다.
    #: 기본 ``DynapathConfig()`` 와 함께 켜면 :func:`enabled_dynapath_config` 가 기기
    #: 값을 합성해 채웁니다. 직접 만든 ``enabled=False`` 구성과 함께 켜면
    #: ``ValueError`` 입니다(넘긴 구성을 조용히 바꾸지 않습니다).
    #:
    #: 필드 목록 **맨 끝**. 중간에 끼우면 위치 인자의 뜻이 조용히 바뀝니다.
    enable_dynapath: bool = False
    #: 7.0.6 ``CommonIn`` 의 4번째 공통 필드(``@SerialName(Constants.LANG)``,
    #: ``com/kakao/sdk/common/Constants.java:27`` 의 평문 리터럴 ``"lang"``).
    #: 실제 앱이 보내는 값은 ``LanguageProvider.getSTLeec()`` 가 반환하는
    #: AppSuit 보호 값이라 여기서 추측해 채우지 않습니다. ``None`` 은 "``lang`` 을
    #: 아예 싣지 않는다" 는 뜻이고, 실제 값을 아는 호출자만 직접 넘깁니다.
    #:
    #: 이 필드도 **맨 끝**. ``enable_dynapath`` 와 같은 이유로, 위치 인자
    #: 안전성 때문에 새 필드는 항상 끝에 추가합니다.
    lang: str | None = None

    def __post_init__(self) -> None:
        if not self.enable_dynapath or self.dynapath.enabled:
            return
        # 편의 경로는 그대로 둡니다 -- 맨손 ``KorailConfig(enable_dynapath=True)`` 는
        # 기기 값을 합성해 채웁니다. 거절하는 것은 호출자가 **직접 만든** 구성을
        # 함께 넘긴 경우뿐입니다. 그 구성을 조용히 갈아치우면, 기기 신원을 스스로
        # 정했다고 믿는 호출자가 실제로는 합성 신원으로 요청을 보내게 됩니다 --
        # 하필 안티오토메이션 토큰이 주장하는 값입니다.
        # 같은 종류의 충돌에 :meth:`DynapathConfig.__post_init__` 은 이미
        # ``ValueError`` 를 냅니다.
        if self.dynapath != DynapathConfig():
            raise ValueError(
                "enable_dynapath=True would replace the DynapathConfig passed "
                "alongside it; pass DynapathConfig(enabled=True, ...) instead"
            )
        object.__setattr__(self, "dynapath", enabled_dynapath_config())
