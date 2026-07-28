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


def _default_dynapath_config() -> DynapathConfig:
    """DynaPath 를 켜고 기기 값을 이 설정만을 위해 새로 만든 구성.

    ``KorailClient()`` 를 인자 없이 만들어도 로그인이 되는 이유가 이것이다.
    DynaPath 를 끈 설정으로 ``login.Login`` 을 부르면 서버가 거절하는데, 그
    거절이 사용자 문구로는 "앱을 업데이트하라"로 위장돼 온다. 계정과 무관한
    읽기는 같은 설정에서 계속 동작하므로 로그인만 골라 실패하는 것처럼
    보인다.

    :func:`~korail_mobile_api.dynapath.build_default_token_settings` 를
    모듈 수준 싱글턴이 아니라 설정마다 새로 부르는 것은 의도다. 이 설정에는
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
    #: DynaPath 안티오토메이션. 기본이 켜짐이며 이유는
    #: :func:`_default_dynapath_config` 에 있다. 끄려면 ``DynapathConfig()`` 를
    #: 넘긴다. 켜든 끄든 허용목록 여섯 경로 밖에는 아무 영향이 없다.
    dynapath: DynapathConfig = field(default_factory=_default_dynapath_config)
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
