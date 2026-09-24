# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청 설정. 기본값은 constants 의 라이브러리 기본값이며 앱의 실기기 값과 같다는 보장은 없습니다.

DynaPath 는 기본으로 켜지고 기기 값은 설정마다 합성됩니다. 실기기 환경변수는 live.build_config_from_env, 명시적 비활성화는 disable_dynapath 를
사용합니다."""

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
    """요청·기기 설정. base_url·netfunnel_url 은 검사하지 않고 그대로 씁니다 — 다른 곳을 가리키면 로그인 자격증명도 그리로 갑니다."""

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
    #: 기본 활성화. 관문 목록은 netfunnel.KORAIL_NETFUNNEL_GATES 참고. 7.0.6 SDK 기본 bypass 는
    #: 거짓(com/netfunnel/api/Property.java:8), 앱 설정은 KorailTalkApplication.java:361-389. 실제 호출 여부는 각 클라이언트 메서드와 앱
    #: 호출부에 따릅니다.
    netfunnel_enabled: bool = True
    #: CommonIn.java:381 의 lang. 평문 값은 보호돼 있으므로 None 이면 생략합니다. 필드명 상수: com/kakao/sdk/common/Constants.java:27.
    #: 위치 인자 호환성을 위해 순서를 유지합니다.
    lang: str | None = None
    #: 누적 대기 상한(초). None 은 상한 없음. 대기열을 빠져나온 시점(통과든 mode=1 의 ErrorBypass 든)에 넘겼으면 요청 없이 KorailNetFunnelError. SDK
    #: 루프에는 상한이 없고(Netfunnel.java:622-664), 앱의 15초 콜백 감시는 netfunnel 모듈 설명 참고.
    netfunnel_wait_limit: float | None = None
    #: 관문 이름 → ``aid`` 덮어쓰기. ``aid`` 리터럴은 7.0.6 에서 보호돼 있어 기본값은 길이·호출부 이름으로 고른 **미검증** 값입니다
    #: (:data:`~korail_mobile_api.netfunnel.KORAIL_NETFUNNEL_GATES`).
    netfunnel_actions: Mapping[str, str] | None = None

    #: 명시적 DynaPath 비활성화(기본 켜짐). 끈 채 DYNAPATH_REQUIRED_PATHS 를 부르면 전송 전에 거절됩니다. 토큰 없는 조회의 2026-09-24 라이브 결론은
    #: constants.DYNAPATH_REQUIRED_PATHS 참고. 위치 인자 호환을 위해 마지막 필드입니다.
    disable_dynapath: bool = False

    def __post_init__(self) -> None:
        default = DynapathConfig()
        if self.disable_dynapath:
            if self.dynapath.enabled:
                raise ValueError(
                    "disable_dynapath=True conflicts with an enabled DynapathConfig"
                )
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
