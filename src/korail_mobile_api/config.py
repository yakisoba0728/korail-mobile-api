"""요청마다 실리는 설정값 — :class:`KorailConfig`.

기본값은 앱 v6.5.0 이 보내는 값이며, DynaPath 기기 값만 설정 객체마다 새로
만듭니다(:func:`_default_dynapath_config`). 실제 단말 값을 고정하려면
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
    live_env_var: str = "KORAIL_MOBILE_API_LIVE"
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
    #: ``dynapath`` 를 직접 넘겼다면 이 플래그는 무시됩니다.
    #:
    #: 필드 목록 **맨 끝**. 중간에 끼우면 위치 인자의 뜻이 조용히 바뀝니다.
    enable_dynapath: bool = False

    def __post_init__(self) -> None:
        if self.enable_dynapath and not self.dynapath.enabled:
            object.__setattr__(self, "dynapath", enabled_dynapath_config())
