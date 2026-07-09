from .config import KorailConfig


class KorailClient:
    def __init__(self, config: KorailConfig | None = None) -> None:
        self.config = config or KorailConfig()
