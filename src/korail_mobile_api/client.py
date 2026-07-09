import httpx

from .config import KorailConfig
from .http import KorailHttpClient
from .models import KorailSession
from .session import KorailSessionClient


class KorailClient:
    def __init__(self, config: KorailConfig | None = None, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config or KorailConfig()
        self.http = KorailHttpClient(self.config, transport=transport)
        self.session = KorailSessionClient(self.http)

    def close(self) -> None:
        self.http.close()

    def login(self, member_no: str, password: str, *, input_flag: str = "2") -> KorailSession:
        return self.session.login(member_no, password, input_flag=input_flag)

    def clear_session(self) -> None:
        self.session.clear_session()

    def logout(self) -> None:
        self.clear_session()
