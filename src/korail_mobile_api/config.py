# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""기본 DynaPath 진단 설정. base_url·netfunnel_url의 신뢰 여부는 호출자가 판단합니다.

한 기기의 DynaPath 값과 대기열 User-Agent를 함께 구성합니다.

환경변수는 설정에만 사용하며 계정·카드 자격증명을 읽거나 저장하지 않습니다."""

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from urllib.parse import urlsplit

from ._core.dynapath import DynapathConfig, _DiagnosticTokenProvider
from .constants import (
    KORAIL_API_USER_AGENT,
    KORAIL_API_VERSION,
    KORAIL_APP_KEY,
    KORAIL_APP_VERSION,
    KORAIL_BASE_URL,
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_HEIGHT,
    KORAIL_DEFAULT_DEVICE_WIDTH,
    KORAIL_DEVICE_ANDROID,
    KORAIL_NETFUNNEL_TIMEOUT_SECONDS,
    KORAIL_NETFUNNEL_URL,
    KORAIL_TIMEOUT_SECONDS,
    KORAIL_USER_AGENT,
    build_dalvik_user_agent,
)

_PROXY_SCHEMES = frozenset({"http", "https", "socks5", "socks5h"})


def _validate_seconds(name: str, value: object, *, allow_zero: bool) -> None:
    # nan 은 대기 한도 비교를 항상 거짓으로 만들고 0·음수 timeout 은 의미가 없습니다.
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value < 0
        or (value == 0 and not allow_zero)
    ):
        raise ValueError(f"{name} must be a finite number {'>= 0' if allow_zero else '> 0'}")


def _validate_proxy(proxy: object) -> None:
    """URL에 자격 증명이 들어 있을 수 있어 오류 메시지에 URL을 싣지 않습니다."""
    if proxy is None:
        return
    if not isinstance(proxy, str) or not proxy or any(char.isspace() for char in proxy):
        raise ValueError("proxy must be a nonempty URL string without whitespace, or None")
    try:
        parts = urlsplit(proxy)
        host, _ = parts.hostname, parts.port  # 잘못된 포트는 port에서 ValueError가 됩니다.
    except ValueError:
        raise ValueError("proxy URL is malformed") from None
    if parts.scheme not in _PROXY_SCHEMES:
        raise ValueError("proxy URL scheme must be http, https, socks5 or socks5h")
    if not host:
        raise ValueError("proxy URL must include a host")


def enabled_dynapath_config() -> DynapathConfig:
    """등록·키·합성 기기값 없이 SDK 2.0.1 native-unavailable 진단 경로를 켭니다."""
    return DynapathConfig(enabled=True, token_provider=_DiagnosticTokenProvider())


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
    #: API 요청의 ``User-Agent`` 헤더입니다.
    user_agent: str = KORAIL_API_USER_AGENT
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: 대기열 요청의 ``User-Agent`` 헤더입니다. 앱의 대기열 요청은 안드로이드 기본 ``User-Agent``(``Dalvik/2.1.0 (...)``)를
    #: 쓰므로 기본값도 이 형식입니다. DynaPath 기기값을 바꾸면 이 값의 안드로이드 버전·기기 모델도 같게 맞추세요.
    #: ``build_config_from_env()``로 만든 설정은 기본적으로 두 값에 같은 기기값을 씁니다.
    netfunnel_user_agent: str = KORAIL_USER_AGENT
    #: 대기열을 거칠지 정합니다. 기본값은 ``True``입니다. ``False``이면 대기열 없이 모든 요청을 바로 보내므로 앱과 다르게
    #: 동작합니다.
    netfunnel_enabled: bool = True
    #: 요청의 언어 필드(``lang``)입니다. ``None``이면 보내지 않습니다. 앱이 보내는 값은 앱 내부 값이 공개돼 있지 않아
    #: 확인하지 못했습니다.
    lang: str | None = None
    #: 대기열에서 기다릴 누적 시간의 상한(초)입니다. ``None``이면 제한하지 않습니다. 상한을 넘으면 API 요청을 보내지 않고
    #: ``KorailNetFunnelError``를 발생시킵니다.
    netfunnel_wait_limit: float | None = None
    #: 관문별 대기열 식별값을 바꿉니다. 관문 이름(``inquiry``, ``peak_season_inquiry``, ``product_inquiry``, ``reserve``,
    #: ``pay``, ``reservation_view``)을 키로, 보낼 식별값을 값으로 받습니다. 기본 식별값은 앱 내부 값이 공개돼 있지 않아
    #: 확인하지 못했으므로 정확한 값을 알 때만 바꾸세요. 목록에 없는 관문 이름과 빈 문자열 값은 무시합니다.
    netfunnel_actions: Mapping[str, str] | None = None

    #: ``True``이면 DynaPath 토큰을 붙이지 않습니다. 이때 로그인 요청은 보내기 전에 ``KorailDynaPathRequiredError``로
    #: 거절되므로 로그인이 필요한 메서드를 쓸 수 없습니다. 켜진 ``DynapathConfig``와 함께 넘기면 ``ValueError``가 발생합니다.
    disable_dynapath: bool = False
    #: 공통 요청의 ``AppVersion`` 값입니다. 기존 ``Version``과 별개이며, ``None``이면 이전 SDK처럼 생략합니다.
    app_version: str | None = KORAIL_APP_VERSION
    #: API 요청과 대기열 요청을 함께 보낼 프록시 URL입니다. ``http``, ``https``, ``socks5``, ``socks5h`` 주소를 받습니다.
    #: ``socks5``·``socks5h``는 ``korail-mobile-api[socks]`` 설치가, ``https``는 httpx 0.25.0 이상, ``socks5h``는 httpx
    #: 0.28.0 이상이 필요합니다. ``None``이면 지정하지 않으며, 이때는 httpx 기본 동작대로 ``HTTPS_PROXY`` 같은 환경변수를
    #: 따릅니다. URL의 자격 증명은 ``repr``에 나오지 않습니다. KORAIL은 프록시의 IP로 접속을 판단하므로 데이터센터·VPN
    #: 대역의 프록시는 차단될 수 있습니다. 직접 관리하는 신뢰할 수 있는 프록시만 쓰세요.
    proxy: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.app_version is not None and (
            not isinstance(self.app_version, str) or not self.app_version.strip()
        ):
            raise ValueError("app_version must be a nonempty string or None")
        if self.timeout is not None:
            _validate_seconds("timeout", self.timeout, allow_zero=False)
        _validate_seconds("netfunnel_timeout", self.netfunnel_timeout, allow_zero=False)
        if self.netfunnel_wait_limit is not None:
            _validate_seconds("netfunnel_wait_limit", self.netfunnel_wait_limit, allow_zero=True)
        _validate_proxy(self.proxy)
        default = DynapathConfig()
        if self.disable_dynapath:
            if self.dynapath.enabled:
                raise ValueError("disable_dynapath=True conflicts with an enabled DynapathConfig")
            return
        if self.dynapath.enabled:
            return
        # 비활성 사용자 구성을 덮지 않고 명시적 disable_dynapath 사용을 요구합니다.
        if self.dynapath != default:
            raise ValueError(
                "pass disable_dynapath=True to turn DynaPath off, or "
                "DynapathConfig(enabled=True, ...) to supply your own"
            )
        object.__setattr__(self, "dynapath", enabled_dynapath_config())


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
    provider = config.dynapath.token_provider
    if config.disable_dynapath or (provider is not None and not isinstance(provider, _DiagnosticTokenProvider)):
        raise ValueError("a device profile requires configurable DynaPath token settings")
    settings = config.dynapath.token_settings
    if isinstance(provider, _DiagnosticTokenProvider):
        provider = replace(
            provider,
            os_version=profile.android_release.encode("utf-8"),
            device_model=profile.model.encode("utf-8"),
            install_id=profile.device_id.encode("utf-8"),
        )
    elif settings is None:
        raise ValueError("DynaPath token settings are missing")
    if settings is not None:
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
            token_provider=provider,
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


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required for KORAIL live DynaPath")
    return value


def build_config_from_env() -> KorailConfig:
    """환경변수에서 실제 기기 값을 읽어 DynaPath를 켠 ``KorailConfig``를 만듭니다.

    ``KORAIL_DYNAPATH_DEVICE_ID``, ``KORAIL_DYNAPATH_OS_VERSION``, ``KORAIL_DYNAPATH_DEVICE_MODEL``은 반드시 있어야 하며,
    ``KORAIL_NETFUNNEL_USER_AGENT``를 지정하지 않으면 ``KORAIL_ANDROID_BUILD_ID``도 필요합니다. 기기 모델과 OS 버전은
    DynaPath 토큰과 대기열 ``User-Agent``에 함께 씁니다. 나머지 값은 ``KORAIL_BASE_URL``, ``KORAIL_USER_AGENT``,
    ``KORAIL_DEVICE_WIDTH``, ``KORAIL_DEVICE_HEIGHT``, ``KORAIL_ANDROID_SDK_INT``,
    ``KORAIL_ADVERTISING_ID``로 바꿀 수 있습니다. ``KORAIL_APP_VERSION``과 ``KORAIL_API_VERSION``은 요청의
    ``AppVersion``과 ``Version``이 되며 비어 있으면 기본값을 씁니다. ``KORAIL_PROXY``는 ``proxy``가 되며 비어 있으면 지정하지 않습니다.
    로그인 정보나 카드 정보는 환경변수에서 읽지 않습니다.

    필요한 환경변수가 없거나 빈 값이면 ``RuntimeError``가 발생합니다. ``KORAIL_DEVICE_WIDTH``, ``KORAIL_DEVICE_HEIGHT``,
    ``KORAIL_ANDROID_SDK_INT``가 정수가 아니거나 ``KORAIL_PROXY``가 올바른 프록시 URL이 아니면 ``ValueError``가 발생합니다."""
    device_id = _required_env("KORAIL_DYNAPATH_DEVICE_ID")
    os_version = _required_env("KORAIL_DYNAPATH_OS_VERSION")
    device_model = _required_env("KORAIL_DYNAPATH_DEVICE_MODEL")
    if any(not value.strip() for value in (device_id, os_version, device_model)):
        raise ValueError("DynaPath device values must not be whitespace")
    advertising_id = os.environ.get("KORAIL_ADVERTISING_ID", "")
    dynapath = DynapathConfig(
        enabled=True,
        token_provider=_DiagnosticTokenProvider(
            os_version=os_version.encode("utf-8"),
            device_model=device_model.encode("utf-8"),
            install_id=device_id.encode("utf-8"),
        ),
        device_name=device_model,
        os_version=os_version,
    )
    return KorailConfig(
        base_url=os.environ.get(
            "KORAIL_BASE_URL",
            "https://smart.letskorail.com:443",
        ),
        version=os.environ.get("KORAIL_API_VERSION") or KORAIL_API_VERSION,
        app_version=os.environ.get("KORAIL_APP_VERSION") or KORAIL_APP_VERSION,
        user_agent=os.environ.get("KORAIL_USER_AGENT", KORAIL_API_USER_AGENT),
        netfunnel_user_agent=os.environ.get("KORAIL_NETFUNNEL_USER_AGENT")
        or build_dalvik_user_agent(
            os_release=os_version,
            device_model=device_model,
            build_id=_required_env("KORAIL_ANDROID_BUILD_ID"),
        ),
        device_width=int(os.environ.get("KORAIL_DEVICE_WIDTH", KORAIL_DEFAULT_DEVICE_WIDTH)),
        device_height=int(os.environ.get("KORAIL_DEVICE_HEIGHT", KORAIL_DEFAULT_DEVICE_HEIGHT)),
        android_sdk_int=int(os.environ.get("KORAIL_ANDROID_SDK_INT", KORAIL_DEFAULT_ANDROID_SDK_INT)),
        dynapath=dynapath,
        advertising_id=advertising_id,
        proxy=os.environ.get("KORAIL_PROXY") or None,
    )
