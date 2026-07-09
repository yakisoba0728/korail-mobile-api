class KorailApiError(Exception):
    """Base error for KORAIL client failures."""


class KorailTransportError(KorailApiError):
    """HTTP transport failed before an app-level response was parsed."""


class KorailProtocolError(KorailApiError):
    """The server response did not match the documented protocol."""


class KorailAuthError(KorailApiError):
    """Login or session authentication failed."""


class KorailAppError(KorailApiError):
    """The server returned an app-level failure response."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(f"{code or 'UNKNOWN'}: {message or ''}".strip())
