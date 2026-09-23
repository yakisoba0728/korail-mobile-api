# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""요청마다 실리는 설정값 — :class:`KorailConfig`.

기본값은 앱 v6.5.0 이 보내는 값입니다. DynaPath 는 **기본으로 켜져** 있고,
:func:`enabled_dynapath_config` 가 설정 객체마다 기기 값을 새로 합성합니다. 끄려면
``disable_dynapath=True``. 실제 단말 값을 고정하려면
:func:`~korail_mobile_api.live.build_config_from_env` 를 씁니다.
"""

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
    ``base_url``·``netfunnel_url`` 은 검사하지 않고 그대로 씁니다 — 다른 곳을
    가리키면 로그인 자격증명도 그리로 갑니다.
    """

    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    user_agent: str = KORAIL_USER_AGENT
    #: DynaPath 구성. 넘기지 않으면 :func:`enabled_dynapath_config` 의 합성값으로
    #: **켜집니다**. 직접 만든 구성(``enabled=True``)을 넘기면 그대로 씁니다.
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: NetFunnel 가상 대기열. **기본 참** — 7.0.6 앱은 열차조회·예약·결제·예약내역
    #: 앞에서 언제나 대기열을 거칩니다(끄는 설정이 없고 SDK 의 ``bypass_`` 도 기본
    #: 거짓 그대로입니다 — ``com/netfunnel/api/Property.java:8``,
    #: ``KorailTalkApplication.java:361-389``). 대기열이 한가하면 5101 이 곧바로
    #: 200 이라 작업마다 대기열 요청 두 번(5101·5004)이 더해질 뿐입니다. 거짓이면
    #: 대기열을 부르지 않습니다. 관문 목록은
    #: :data:`~korail_mobile_api.netfunnel.KORAIL_NETFUNNEL_GATES`.
    netfunnel_enabled: bool = True
    #: 7.0.6 ``CommonIn`` 의 4번째 공통 필드(``@SerialName(Constants.LANG)``,
    #: ``com/kakao/sdk/common/Constants.java:27`` 의 평문 리터럴 ``"lang"``).
    #: 실제 앱이 보내는 값은 ``LanguageProvider.getSTLeec()`` 가 반환하는
    #: AppSuit 보호 값이라 여기서 추측해 채우지 않습니다. ``None`` 은 "``lang`` 을
    #: 아예 싣지 않는다" 는 뜻이고, 실제 값을 아는 호출자만 직접 넘깁니다.
    #:
    #: 위치 인자 안전성 때문에 새 필드는 항상 끝에 추가합니다.
    lang: str | None = None
    #: 대기열 대기의 누적 상한(초). ``None``(기본)은 앱처럼 상한 없이 기다립니다 —
    #: 7.0.6 의 대기 루프는 사용자가 화면을 닫을 때만 멈춥니다
    #: (``com/netfunnel/api/Netfunnel.java:622-664``). 넘으면 요청을 보내지 않고
    #: :class:`~korail_mobile_api.errors.KorailNetFunnelError` 입니다.
    netfunnel_wait_limit: float | None = None
    #: 관문 이름 → ``aid`` 덮어쓰기. ``aid`` 리터럴은 7.0.6 에서 보호돼 있어 기본값은
    #: 길이·호출부 이름으로 고른 **미검증** 값입니다
    #: (:data:`~korail_mobile_api.netfunnel.KORAIL_NETFUNNEL_GATES`).
    netfunnel_actions: Mapping[str, str] | None = None

    #: DynaPath 를 끕니다. **기본 거짓(켜짐).** 앱은 DynaPath 를 언제나 싣고, 서버는
    #: 토큰 없는 열차조회를 ``MACRO ERROR`` 로 거절합니다(2026-09-24 라이브 확인).
    #: 끈 채 :data:`~korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS` 를 부르면
    #: :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError` 로 막힙니다.
    #:
    #: 필드 목록 **맨 끝**. 중간에 끼우면 위치 인자의 뜻이 조용히 바뀝니다.
    disable_dynapath: bool = False

    def __post_init__(self) -> None:
        default = DynapathConfig()
        if self.disable_dynapath:
            # 켜진 구성을 함께 넘기면 어느 쪽이 뜻인지 알 수 없습니다.
            if self.dynapath.enabled:
                raise ValueError(
                    "disable_dynapath=True conflicts with an enabled DynapathConfig"
                )
            return
        if self.dynapath.enabled:
            return
        # 끈 구성을 직접 넘긴 경우는 끄려는 뜻이 분명하지 않습니다 — 조용히 합성값으로
        # 갈아치우지 않고, 끄는 방법을 알려 줍니다.
        if self.dynapath != default:
            raise ValueError(
                "pass disable_dynapath=True to turn DynaPath off, or "
                "DynapathConfig(enabled=True, ...) to supply your own"
            )
        object.__setattr__(self, "dynapath", enabled_dynapath_config())
