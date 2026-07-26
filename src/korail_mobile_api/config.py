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
from .dynapath import DynapathConfig


@dataclass(frozen=True)
class KorailConfig:
    base_url: str = KORAIL_BASE_URL
    device: str = KORAIL_DEVICE_ANDROID
    version: str = KORAIL_API_VERSION
    key: str = KORAIL_APP_KEY
    timeout: float = KORAIL_TIMEOUT_SECONDS
    user_agent: str = KORAIL_USER_AGENT
    live_env_var: str = "KORAIL_MOBILE_API_LIVE"
    dynapath: DynapathConfig = field(default_factory=DynapathConfig)
    device_width: int = KORAIL_DEFAULT_DEVICE_WIDTH
    device_height: int = KORAIL_DEFAULT_DEVICE_HEIGHT
    android_sdk_int: int = KORAIL_DEFAULT_ANDROID_SDK_INT
    advertising_id: str = ""
    netfunnel_url: str = KORAIL_NETFUNNEL_URL
    netfunnel_timeout: float = KORAIL_NETFUNNEL_TIMEOUT_SECONDS
    #: Whether the NetFunnel virtual waiting room may be used at all.
    #:
    #: **FALSE, and that default is load-bearing.** Constructing a
    #: :class:`~korail_mobile_api.netfunnel.KorailNetFunnelClient` against a
    #: config with this unset is refused outright, so nothing in this package
    #: can reach ``nf.letskorail.com`` until a caller says so in writing.
    #:
    #: The reason is evidence, not caution. Every live call this repository has
    #: made to ``smart.letskorail.com`` — reserve, cancel, pay, refund and the
    #: whole read surface — succeeded WITHOUT a queue token, so the server does
    #: not currently meter us. Turning the queue on by default would therefore
    #: add a round trip (and a 3-second timeout, and a failure mode) to every
    #: gated operation in exchange for nothing, and could only regress a client
    #: that works today. The polling path has consequently never been exercised
    #: against the real server and is offline-tested only.
    #:
    #: What it is FOR is the load at which that stops being true. Enforcement is
    #: a server-side policy and the app ships the client for it — including a
    #: dedicated peak-season inquiry action (``act_8_2``) that exists precisely
    #: because peak season is when a waiting room gets switched on. Set this to
    #: ``True`` when a queue-shaped failure appears, which is the situation this
    #: subsystem was built for and the only one in which it earns its round trip.
    netfunnel_enabled: bool = False
