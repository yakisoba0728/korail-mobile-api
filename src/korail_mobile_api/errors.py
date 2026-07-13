from .redaction import redact_text


class KorailApiError(Exception):
    """Base error for KORAIL client failures."""

    def __init__(self, *args: object) -> None:
        super().__init__(
            *(
                redact_text(arg) if isinstance(arg, str) else arg
                for arg in args
            )
        )


class KorailTransportError(KorailApiError):
    """HTTP transport failed before an app-level response was parsed."""


class KorailProtocolError(KorailApiError):
    """The server response did not match the documented protocol."""


class KorailAuthError(KorailApiError):
    """Login or session authentication failed."""


class KorailSessionExpiredError(KorailAuthError):
    """The authenticated KORAIL session is no longer valid."""

    def __init__(
        self,
        code: str | None,
        message: str | None,
        *,
        raw: object | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'P058'}: "
            f"{redact_text(message or 'KORAIL session expired')}"
        )


class KorailDynaPathError(KorailApiError):
    """The KORAIL DynaPath layer rejected a request."""

    def __init__(
        self,
        message: str | None = None,
        *,
        raw: object | None = None,
    ) -> None:
        self.raw = raw
        super().__init__(
            redact_text(message or "KORAIL DynaPath request rejected")
        )


class KorailAuthContinuationRequired(KorailAuthError):
    """Login requires the app's WebView authentication continuation."""

    def __init__(self, redirect_url: str, post_data: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        self.post_data = post_data
        self.raw = raw
        super().__init__("KORAIL login requires WebView continuation")


class KorailAppError(KorailApiError):
    """The server returned an app-level failure response."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        self.code = code
        self.message = message
        self.raw = raw
        super().__init__(
            f"{code or 'UNKNOWN'}: {redact_text(message or '')}".strip()
        )
