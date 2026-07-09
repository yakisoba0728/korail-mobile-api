from dataclasses import dataclass


@dataclass(frozen=True)
class KorailConfig:
    base_url: str = "https://smart.letskorail.com"
    device: str = "AD"
    version: str = "250601003"
    key: str = "korail1234567890"
    timeout: float = 60.0
    user_agent: str = "korail-mobile-api/0.1.0"
    live_env_var: str = "KORAIL_MOBILE_API_LIVE"
