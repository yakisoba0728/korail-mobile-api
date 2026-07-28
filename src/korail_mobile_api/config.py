"""요청마다 실리는 설정값 — :class:`KorailConfig` 하나와 그 기본 구성.

기본값은 앱 v6.5.0 이 보내는 값이고, 그중 DynaPath 기기 값만은 설정 객체마다
새로 만들어진다. 모든 설치본이 같은 식별자를 보내는 것이 안티매크로 검사가
찾는 신호이기 때문이다(:func:`_default_dynapath_config`).

실제 단말 값을 프로세스 사이에서 유지하려면 이 클래스를 직접 채우지 말고
:func:`~korail_mobile_api.live.build_config_from_env` 를 쓴다. User-Agent 와
DynaPath 토큰이 같은 단말을 주장하게 맞춰 주는 것은 그쪽뿐이다.
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
    """DynaPath 를 켜고 기기 값을 이 구성만을 위해 새로 만든다.

    ``KorailConfig(enable_dynapath=True)`` 가 부르는 것이 이 함수다. 직접
    불러 :class:`KorailConfig` 의 ``dynapath`` 에 넣어도 결과는 같다.

    :func:`~korail_mobile_api.dynapath.build_default_token_settings` 를
    모듈 수준 싱글턴이 아니라 호출마다 새로 부르는 것은 의도다. 이 설정에는
    설치별 기기 식별자와 앱 시작 시각이 들어 있어서, 하나를 공유하면 한
    프로세스 안의 모든 클라이언트가 같은 기기·같은 시작 시각을 주장하게
    된다.
    """
    return DynapathConfig(
        enabled=True,
        token_settings=build_default_token_settings(),
    )


@dataclass(frozen=True)
class KorailConfig:
    """:class:`~korail_mobile_api.client.KorailClient` 가 매 요청에 싣는 값들.

    ``KorailConfig()`` 를 인자 없이 만들면 앱 v6.5.0 의
    ``Device``/``Version``/``Key`` 와 켜진 DynaPath 가 채워진다. 필드를
    직접 바꾸기보다
    :func:`~korail_mobile_api.live.build_config_from_env` 로 실제 기기 값을
    주입하는 쪽이 낫다 — 기기 이름·화면 크기·SDK 레벨이 서로 맞아야
    의미가 있기 때문이다.

    ``base_url`` 과 ``netfunnel_url`` 은 서로 다른 호스트이고 서로를 부를 수
    없다. API 는 ``smart.letskorail.com``, 대기열은 ``nf.letskorail.com``
    으로 각각 고정 검사된다.

    ``live_env_var`` 는 라이브 테스트를 여는 환경변수 이름이며 요청에
    실리지 않는다.
    """

    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    user_agent: str = KORAIL_USER_AGENT
    live_env_var: str = "KORAIL_MOBILE_API_LIVE"
    #: DynaPath 구성 전체. 기본은 **꺼짐** 이다. 보통은 아래
    #: ``enable_dynapath`` 로 켜고, 토큰 제공자를 갈아끼우거나 허용목록을
    #: 바꿔야 할 때만 이쪽을 직접 넘긴다.
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: NetFunnel 가상 대기열을 쓸지 여부. 기본은 거짓이다.
    #:
    #: 거짓인 동안
    #: :class:`~korail_mobile_api.netfunnel.KorailNetFunnelClient` 생성 자체가
    #: 거절되므로, 명시적으로 켜기 전에는 이 패키지가 ``nf.letskorail.com``
    #: 에 닿을 수 없다.
    #:
    #: 지금까지 예약·취소·결제·환불과 읽기 전부가 대기열 토큰 없이 통과했다 —
    #: 서버가 우리를 계량하고 있지 않다는 뜻이다. 그 상태에서 대기열을 켜면
    #: 게이트가 걸린 모든 호출에 왕복 한 번과 3초 타임아웃과 실패 모드가
    #: 얹힐 뿐이다. 그래서 폴링 경로는 실제 서버에 대고 돌아간 적이 없고
    #: 오프라인 테스트만 있다.
    #:
    #: 대기열은 서버 정책이고 앱은 그 클라이언트를 싣고 다닌다 — 성수기
    #: 전용 조회 액션(``act_8_2``)이 따로 있는 것이 그 증거다. 대기열 모양의
    #: 실패가 보이면 그때 ``True`` 로 켜라.
    netfunnel_enabled: bool = False
    #: DynaPath 안티오토메이션을 켠다. **기본은 거짓이다.**
    #:
    #: 이 토큰은 자동화 탐지를 통과하기 위한 값이라 보낼지 말지를 이 패키지가
    #: 대신 정하지 않는다. 켜지 않은 채
    #: :data:`~korail_mobile_api.constants.DYNAPATH_REQUIRED_PATHS` 의 경로를
    #: 부르면 전송 전에
    #: :class:`~korail_mobile_api.errors.KorailDynaPathRequiredError` 로
    #: 막힌다. 다른 경로는 켜든 끄든 그대로 나간다.
    #:
    #: ``dynapath`` 를 직접 켜서 넘겼다면 이 플래그는 아무것도 하지 않는다.
    #:
    #: **필드 목록 맨 끝에 붙였다.** 이 앞의 순서는
    #: ``tests/test_public_contract.py`` 가 고정하고 있고, 중간에 끼우면 이미
    #: 위치 인자로 쓰던 호출의 뜻이 조용히 바뀐다.
    enable_dynapath: bool = False

    def __post_init__(self) -> None:
        # ``enable_dynapath`` 는 편의 플래그이고 ``dynapath`` 가 실체다. 직접
        # 넘긴 구성이 있으면 그것을 이긴다 — 토큰 제공자를 갈아끼운 호출자가
        # 플래그 하나로 그것을 덮어쓰게 되면 안 된다.
        if self.enable_dynapath and not self.dynapath.enabled:
            object.__setattr__(self, "dynapath", enabled_dynapath_config())
