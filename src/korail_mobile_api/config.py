# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""설정마다 합성 기기값을 만들며 base_url·netfunnel_url의 신뢰 여부는 호출자가 판단합니다."""

from collections.abc import Mapping
from dataclasses import dataclass, field

from .constants import (
    KORAIL_API_USER_AGENT,
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
    """API·대기열·기기·인증 토큰의 요청 설정을 구성합니다.

    ``base_url``과 ``netfunnel_url``은 검사하지 않고 그대로 씁니다. ``base_url``이 다른 서버를 가리키면 로그인 자격 증명도
    그 서버로 갑니다. 대기열 요청에는 자격 증명을 싣지 않지만, ``netfunnel_url``이 다른 서버를 가리키면 API 요청을 보낼지와
    언제 보낼지를 그 서버가 정합니다. 신뢰할 수 있는 주소가 아니면 바꾸지 마세요."""

    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    # 운영 관측값이며 앱의 헤더 문자열은 보호돼 있어 해독하지 않습니다(NetworkModule.java:405-423).
    #: API 요청의 ``User-Agent`` 헤더입니다.
    user_agent: str = KORAIL_API_USER_AGENT
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    # 대기열 SDK 는 값을 넣지 않아 안드로이드 기본값(http.agent)이 나갑니다. 기본값은 표본 기기의 값입니다
    # (constants.KORAIL_USER_AGENT); 기기를 바꾸면 constants.build_dalvik_user_agent 로 dynapath 기기값과 맞춥니다.
    #: 대기열 요청의 ``User-Agent`` 헤더입니다. 앱의 대기열 요청은 안드로이드 기본 ``User-Agent``(``Dalvik/2.1.0 (...)``)를
    #: 쓰므로 기본값도 이 형식입니다. DynaPath 기기값을 바꾸면 이 값의 안드로이드 버전·기기 모델도 같게 맞추세요.
    #: ``build_config_from_env()``로 만든 설정은 기본적으로 두 값에 같은 기기값을 씁니다.
    netfunnel_user_agent: str = KORAIL_USER_AGENT
    # 7.0.6 SDK 기본 bypass 는 거짓(com/netfunnel/api/Property.java:8), 앱 설정은 KorailTalkApplication.java:361-389.
    #: 대기열을 거칠지 정합니다. 기본값은 ``True``입니다. ``False``이면 대기열 없이 모든 요청을 바로 보내므로 앱과 다르게
    #: 동작합니다.
    netfunnel_enabled: bool = True
    # lang은 CommonIn.java:381의 필드이며 평문은 보호돼 None이면 생략합니다. 필드명 상수는
    # com/kakao/sdk/common/Constants.java:27을 따릅니다.
    #: 요청의 언어 필드(``lang``)입니다. ``None``이면 보내지 않습니다. 앱이 보내는 값은 앱 내부 값이 공개돼 있지 않아
    #: 확인하지 못했습니다.
    lang: str | None = None
    #: 대기열에서 기다릴 누적 시간의 상한(초)입니다. ``None``이면 제한하지 않습니다. 상한을 넘으면 API 요청을 보내지 않고
    #: ``KorailNetFunnelError``를 발생시킵니다.
    netfunnel_wait_limit: float | None = None
    # ``aid`` 리터럴은 7.0.6 에서 보호돼 있어 기본값은 길이·호출부 이름으로 고른 미검증 값입니다
    # (netfunnel.KORAIL_NETFUNNEL_GATES).
    #: 관문별 대기열 식별값을 바꿉니다. 관문 이름(``inquiry``, ``peak_season_inquiry``, ``product_inquiry``, ``reserve``,
    #: ``pay``, ``reservation_view``)을 키로, 보낼 식별값을 값으로 받습니다. 기본 식별값은 앱 내부 값이 공개돼 있지 않아
    #: 확인하지 못했으므로 정확한 값을 알 때만 바꾸세요. 목록에 없는 관문 이름과 빈 문자열 값은 무시합니다.
    netfunnel_actions: Mapping[str, str] | None = None

    # 필수 경로는 전송 전에 거절됩니다. 토큰 없는 조회의 차단 관측은 constants.DYNAPATH_REQUIRED_PATHS를 따릅니다.
    #: ``True``이면 DynaPath 토큰을 붙이지 않습니다. 이때 로그인 요청은 보내기 전에 ``KorailDynaPathRequiredError``로
    #: 거절되므로 로그인이 필요한 메서드를 쓸 수 없습니다. 켜진 ``DynapathConfig``와 함께 넘기면 ``ValueError``가 발생합니다.
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
