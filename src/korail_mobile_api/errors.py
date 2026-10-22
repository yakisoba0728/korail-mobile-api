# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""예외 분류는 라이브러리 정책이며 알려지지 않은 서버 코드는 KorailAppError로 보존합니다.

앱의 일반 결과 메시지 사전입니다. 사전에 있다는 이유만으로 실패나 재시도를 판정하지 않습니다."""

import copyreg
from functools import cache
from html.parser import HTMLParser
from importlib.resources import files
from json import loads
from typing import TypeGuard, cast

_LANGUAGES = {"ko": "ko", "en": "en", "ja": "ja", "jp": "ja", "zh": "zh", "cn": "zh"}
# P058's asset value is a browser redirect script, not a readable session-expiry explanation.
# These descriptions are SDK text; they are not reconstructed app literals.
_SESSION_MESSAGES = {
    "ko": "로그인이 만료되었습니다. 다시 로그인해 주세요.",
    "en": "Your session has expired. Please log in again.",
    "ja": "ログインの有効期限が切れました。再度ログインしてください。",
    "zh": "登录已过期，请重新登录。",  # noqa: RUF001
}


def _language(language: str) -> str:
    base = language.lower().replace("_", "-").split("-", 1)[0]
    try:
        return _LANGUAGES[base]
    except KeyError:
        raise ValueError("language must be ko, en, ja/jp or zh/cn (regional variants are accepted)") from None


@cache
def _messages() -> dict[str, dict[str, str]]:
    # Load on the first lookup, not during package import or version resolution.
    catalog = loads(files("korail_mobile_api").joinpath("error_messages.json").read_text(encoding="utf-8"))
    return cast(dict[str, dict[str, str]], catalog["messages"])


def get_error_message(code: str | None, *, language: str = "ko") -> str | None:
    """앱 7.0.10의 결과 메시지를 조회합니다. 알 수 없는 코드이면 ``None``입니다.

    한국어·영어·일본어(ja/jp)·중국어(zh/cn)를 지원하며 번역이 없으면 한국어를 반환합니다. 지역 언어값도 받습니다.
    지원하지 않는 언어는 ``ValueError``입니다. 메시지의 HTML과 치환 표시는 원문 그대로이며 실행하거나 치환하지 않습니다.
    성공·안내·과거 코드도 포함되어 있으므로 반환값으로 성공·실패나 계정 상태를 판정하지 마세요."""
    locale = _language(language)
    if not code:
        return None
    translations = _messages().get(code)
    if translations is None:
        return None
    return translations.get(locale) or translations.get("ko") or None


class _PlainMessage(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_tag: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.ignored_tag is not None:
            return
        if tag in {"script", "style"}:
            self.ignored_tag = tag
        elif tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.ignored_tag is not None:
            if tag == self.ignored_tag:
                self.ignored_tag = None
        elif tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.ignored_tag is None:
            self.parts.append(data)


def _plain_text(message: str | None) -> str | None:
    if not message:
        return None
    parser = _PlainMessage()
    parser.feed(message)
    parser.close()
    return "".join(parser.parts).strip() or None


def resolve_error_message(
    code: str | None,
    message: str | None = None,
    *,
    language: str = "ko",
) -> str | None:
    """표시할 메시지를 서버 원문 → 앱 사전 순으로 선택해 일반 텍스트로 반환합니다.

    줄바꿈 태그를 개행으로 바꾸고 태그·스크립트·스타일을 표시에서 제외합니다. 원본 객체는 바꾸지 않습니다.
    ``P058``에 읽을 메시지가 없으면 SDK의 세션 만료 안내를 반환합니다. 이것만으로 세션을 지우지는 않습니다.
    알 수 없는 코드에 읽을 서버 메시지도 없으면 ``None``입니다. 언어 규칙은 ``get_error_message``와 같습니다."""
    locale = _language(language)
    server_text = _plain_text(message)
    if server_text is not None:
        return server_text
    catalog_text = _plain_text(get_error_message(code, language=locale))
    if catalog_text is not None:
        return catalog_text
    if code == "P058":
        return _SESSION_MESSAGES[locale]
    return None


def _is_json_object(value: object) -> TypeGuard[dict[str, object]]:
    """JSON 객체(dict)인지 봅니다. 타입 검사기가 ``isinstance`` 만으로는 키·값 타입을 모르므로 둡니다."""
    return isinstance(value, dict)


# 타입 스텁에 없는 이름입니다. pickle 은 이 함수를 NEWOBJ 로 기록해 __init__ 없이 복원합니다.
_NEWOBJ: object = getattr(copyreg, "__newobj__")  # noqa: B009


class KorailApiError(Exception):
    """라이브러리가 발생시키는 모든 예외의 기반 클래스입니다.

    ``except KorailApiError``로 라이브러리 예외를 한꺼번에 처리할 수 있습니다. 라이브러리가 이 클래스 자체를 발생시키지는
    않습니다. 아래 속성은 값이 없으면 ``None``입니다."""

    #: 서버 결과 코드(``h_msg_cd``)입니다. 대기열 예외에서는 대기열 응답 코드입니다. 서버나 대기열의 응답 없이 발생한
    #: 예외에서는 ``None``입니다.
    code: str | None = None
    #: 서버 결과 메시지(``h_msg_txt``)입니다. 대기열 예외에서는 라이브러리가 쓴 설명입니다. 없으면 ``None``입니다.
    message: str | None = None
    #: 서버가 보낸 응답 원본입니다. 없으면 ``None``입니다.
    raw: object | None = None
    #: 응답 모델을 읽다가 실패했을 때 파서가 읽던 부분 원본입니다. 이때 ``raw``에는 받은 응답 전체가 들어 있습니다.
    #: 없으면 ``None``입니다.
    parser_raw: object | None = None
    #: 요청을 HTTP 전송 계층에 넘긴 뒤 전송이나 응답 해석에 실패했으면 ``True``입니다. 서버가 요청을 처리했을 수 있으므로
    #: 상태 변경 메서드라면 다시 보내기 전에 결과를 확인하세요. 요청 전에 거절한 예외는 ``None``입니다.
    request_sent: bool | None = None

    def __init__(
        self,
        *args: object,
        code: str | None = None,
        message: str | None = None,
        raw: object | None = None,
    ) -> None:
        super().__init__(*args)
        self.code = code
        self.message = message
        self.raw = raw

    def __reduce__(self) -> tuple[object, ...]:
        # __init__ 을 거치지 않고 args 와 속성만 복원하므로 하위 클래스의 생성자 모양과 무관합니다.
        return (_NEWOBJ, (type(self), *self.args), self.__dict__)

    @property
    def display_message(self) -> str | None:
        """읽을 서버 메시지 또는 앱 사전의 한국어 안내입니다. ``message``·``raw``와 예외 문자열은 보존합니다.

        다른 언어로 표시하려면 ``resolve_error_message(self.code, self.message, language=...)``를 사용하세요."""
        return resolve_error_message(self.code, self.message)


def _code_message(code: str | None, message: str | None) -> str:
    return f"{code or 'UNKNOWN'}: {message or ''}".strip()


class KorailTransportError(KorailApiError):
    """네트워크 오류로 응답을 받지 못했거나, 서버가 2xx가 아닌 HTTP 상태로 응답했음을 나타냅니다.

    리다이렉트는 따라가지 않으므로 3xx 응답도 이 예외가 됩니다. HTTP 상태 오류이면 ``status_code``에 상태 코드가, ``raw``에
    응답 본문이 들어 있고, 네트워크 오류이면 원래의 ``httpx`` 예외가 ``__cause__``에 들어 있습니다. 상태 변경 메서드에서
    발생했다면 요청이 서버에 닿았는지 알 수 없으므로, 다시 호출하기 전에 예약 목록이나 승차권 목록으로 결과를 확인하세요."""

    #: 2xx가 아닌 HTTP 상태로 응답했을 때의 상태 코드입니다. 네트워크 오류이면 ``None``입니다.
    status_code: int | None = None

    def __init__(self, *args: object, status_code: int | None = None, raw: object | None = None) -> None:
        super().__init__(*args, raw=raw)
        self.status_code = status_code


class KorailProtocolError(KorailApiError):
    """응답을 읽을 수 없거나 요청 전 입력 검사에 실패했음을 나타냅니다.

    응답이 JSON 객체가 아니거나 필수 값이 없을 때, 닫힌 클라이언트로 요청하려 할 때도 발생합니다. 요청 전 입력 검사에서
    발생했다면 요청은 보내지 않은 것입니다. 상태 변경 메서드가 응답을 읽지 못해 발생했다면 서버에서는 처리됐을 수
    있으므로, 다시 호출하기 전에 결과를 확인하세요."""


class KorailInvalidInputError(KorailProtocolError, ValueError):
    """요청 전 입력 검사에서 값이 잘못돼 요청을 보내지 않았음을 나타냅니다.

    ``KorailProtocolError``와 ``ValueError`` 어느 쪽으로도 잡을 수 있습니다."""


class KorailAuthError(KorailApiError):
    """로그인에 실패했거나, 로그인이 필요한 메서드를 로그인하지 않고 호출했음을 나타냅니다.

    로그인에 실패하면 ``code``에 로그인 응답의 결과 코드가, ``raw``에 로그인 응답 원본이 들어 있습니다. 로그인하지 않았거나
    세션에 고객번호가 없어 요청 전에 발생한 경우에는 ``code``와 ``raw``가 ``None``이며, 요청은 보내지 않은 것입니다."""


class KorailSessionExpiredError(KorailAuthError):
    """서버 세션이 만료됐음을 나타냅니다.

    실패 응답의 결과 코드가 ``P058``일 때 발생합니다. 클라이언트는 이 예외를 발생시키기 전에 로컬 세션을 비웁니다.
    계속하려면 ``login``을 다시 호출해 로그인하세요."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        super().__init__(
            f"{code or 'P058'}: {message or 'KORAIL session expired'}", code=code, message=message, raw=raw
        )


class KorailAccountLockedError(KorailAuthError):
    """로그인 응답이 비밀번호 오류 허용 횟수 초과를 알렸음을 나타냅니다(``WRC000390``).

    메시지 사전에 근거한 라이브러리 분류입니다. 로그인을 반복하지 말고 계정 상태를 확인하세요.
    로그인 이외의 응답에는 이 분류를 적용하지 않습니다."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        super().__init__(_code_message(code, message), code=code, message=message, raw=raw)


class KorailDynaPathError(KorailApiError):
    """DynaPath 토큰을 붙이는 경로의 응답에서 차단 코드를 감지했음을 나타냅니다.

    HTTP 상태와 봉투보다 먼저 판정하며, ``raw``에 차단 코드가 든 응답이 들어 있습니다. 차단 코드가 들어 있는 응답 필드는
    앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 그래서 응답 최상위의 정수 값을 모두 검사하므로, 다른 필드의 같은
    값도 차단으로 판정할 수 있습니다."""

    def __init__(self, message: str | None = None, *, raw: object | None = None) -> None:
        super().__init__(message or "KORAIL DynaPath request rejected", raw=raw)


class KorailAuthContinuationRequired(KorailAuthError):
    """로그인을 마치려면 휴면 계정 해제나 비밀번호 변경 같은 웹 단계가 필요함을 나타냅니다.

    로그인 응답의 결과 코드가 ``WRC000116`` 또는 ``WRC000420``일 때 발생합니다. ``redirect_url``에 서버가 준 웹 주소(없으면
    ``""``)가, ``code``와 ``raw``에 결과 코드와 로그인 응답 원본이 들어 있습니다. 라이브러리는 웹 단계를 대신 진행하지
    않습니다."""

    def __init__(self, redirect_url: str, *, raw: object | None = None) -> None:
        self.redirect_url = redirect_url
        code = raw.get("h_msg_cd") if _is_json_object(raw) else None
        message = raw.get("h_msg_txt") if _is_json_object(raw) else None
        super().__init__(
            "KORAIL login requires a web step (dormant account or password change)",
            code=code if isinstance(code, str) else None,
            message=message if isinstance(message, str) else None,
            raw=raw,
        )


class KorailAppError(KorailApiError):
    """서버가 실패로 응답했음을 나타냅니다.

    결과 코드에 따라 하위 예외로 나뉘며, 어느 하위 예외에도 해당하지 않는 결과 코드는 이 클래스 그대로 발생합니다.
    ``code``와 ``message``에 결과 코드와 결과 메시지가, ``raw``에 응답 원본이 들어 있습니다."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        super().__init__(_code_message(code, message), code=code, message=message, raw=raw)


class KorailNoResultsError(KorailAppError):
    """조회 조건에 맞는 결과가 없음을 나타냅니다. 결과 코드 ``WRG000000``, ``P100``, ``P114`` 등에서 발생합니다."""


class KorailNoDirectTrainError(KorailNoResultsError):
    """직통 열차가 없음을 나타냅니다(결과 코드 ``WRD000061``).

    환승 여정은 ``search_transfer_trains``로 조회하세요. ``search_trains_with_transfer_fallback``은 이 예외가 발생했을
    때만 환승 여정을 조회합니다."""


class KorailSoldOutError(KorailAppError):
    """매진됐거나 남은 좌석이 없음을 나타냅니다. 결과 코드 ``ERR211161``, ``WRT300001`` 등에서 발생합니다."""


class KorailSeatUnavailableError(KorailAppError):
    """지정한 좌석을 이용할 수 없음을 나타냅니다. 결과 코드 ``WRI411345`` 등에서 발생합니다."""


class KorailReservationRefusedError(KorailAppError):
    """중복 예약, 구매 한도, 예약 가능 시간, 지원하지 않는 할인 등의 이유로 예약이 거절됐음을 나타냅니다.

    결과 코드 ``WRR800029``, ``ERR911531``, ``ERR299943`` 등에서 발생합니다."""


class KorailInvalidRequestError(KorailAppError):
    """서버가 입력값을 거절했음을 나타냅니다. 결과 코드 ``WRG200018``, ``WRT100002`` 등에서 발생합니다."""


class KorailNotEntitledError(KorailAppError):
    """할인이나 상품을 이용할 자격이 없음을 나타냅니다. 결과 코드 ``WRC000419``, ``WRC800030`` 등에서 발생합니다."""


class KorailServiceUnavailableError(KorailAppError):
    """서비스 일시중지·혼잡·연결 문제 안내 응답을 나타냅니다(``S000``~``S003``, ``SEMGTK``).

    서버 장애만을 뜻하지는 않습니다. 로그인 응답이 이 결과 코드이면 ``KorailAuthError`` 대신 이 예외가 발생합니다."""


class KorailRateLimitError(KorailAppError):
    """요청 횟수 초과나 반복 호출 차단 안내입니다(``BT019``, ``BT023``).

    메시지 사전에 근거한 라이브러리 분류입니다. 해제 시각·재시도 간격은 알 수 없으며 자동 재시도하지 않습니다."""


class KorailProcessingError(KorailAppError):
    """요청이 처리 중이거나 이미 완료됐을 수 있어 결과 확인이 필요합니다(``WRT900900``).

    성공·실패를 이 코드만으로 확정할 수 없습니다. 예약·승차권 목록을 확인한 뒤 다음 작업을 결정하세요.
    메시지 사전에 근거한 라이브러리 분류이며 상태 변경 요청을 자동으로 다시 보내지 않습니다."""


class KorailAlreadyProcessedError(KorailAppError):
    """이미 반환된 승차권(``EZZ000014``) 또는 취소된 예약(``EVZ000102``) 안내입니다.

    메시지 사전에 근거한 라이브러리 분류입니다. 현재 작업을 성공으로 바꾸거나 재전송하지 않습니다."""


class KorailAppUpdateRequiredError(KorailAppError):
    """앱 업데이트를 요구하는 응답을 나타냅니다(결과 코드 ``SUPDATE``, 실서버 관측 ``-8204``).

    로그인 응답이 이 결과 코드이면 ``KorailAuthError`` 대신 이 예외가 발생합니다."""


class KorailNetFunnelError(KorailApiError):
    """대기열을 통과하지 못해 API 요청을 보내지 않았음을 나타냅니다.

    대기열 서버가 입장 키 없이 기다리라고 답했을 때, ``reserve``·``pay``·``reservation_view`` 관문에서 대기열 서버가
    통과(``200``)로 답하지 않거나 대기열 서버 오류가 났을 때, 누적 대기 시간이 ``netfunnel_wait_limit``를 넘었을 때
    발생합니다. 대기열 응답으로 판정한 경우에는 ``code``에 대기열 응답 코드가, ``raw``에 대기열 응답이 들어 있습니다.
    대기열 서버 오류로 요청을 보내지 않은 경우에는 ``code``와 ``raw``가 ``None``이고 원래 예외가 ``__cause__``에 들어
    있습니다."""

    def __init__(self, code: str | None, message: str | None, *, raw: object | None = None) -> None:
        super().__init__(_code_message(code, message), code=code, message=message, raw=raw)


class KorailQueueRejectedError(KorailNetFunnelError):
    """대기열 서버가 요청을 차단했음을 나타냅니다(대기열 응답 코드 ``301``, ``302``).

    모든 관문에서 발생하며, API 요청은 보내지 않은 것입니다. ``code``에 대기열 응답 코드가, ``raw``에 대기열 응답이 들어
    있습니다."""


class KorailDynaPathRequiredError(KorailApiError):
    """DynaPath를 끈 설정으로 토큰이 필요한 요청(로그인)을 보내려 했음을 나타냅니다.

    요청은 보내지 않습니다. 서버 응답의 차단 신호를 나타내는 ``KorailDynaPathError``와 달리, 이 예외는 서버 응답을 받았다는
    뜻이 아닙니다. 로그인하려면 DynaPath를 켠 설정(기본값)을 쓰세요."""


# 실패 응답에만 적용하는 라이브러리 분류입니다. 코드별 근거는 tests/test_auth_transport.py 의 오류 표 테스트에 있습니다.
NO_RESULT_CODES = frozenset(
    "WRG000000 P114 P100 WRT300005 ERR000100 WRT800083 WRG500116 IRR800002 IRT200279 IRZ000005 MRT200648 "
    "WRC000008 WRC000256 WRD000016 WRS600208 WRS600209 WRS600210 WRT100192 WRT200125 WRT300003 WRT800091".split()
)
NO_DIRECT_TRAIN_CODE = "WRD000061"
SOLD_OUT_CODES = frozenset(
    "ERR211161 IRT010110 WRT300001 ERR800048 IRT010510 IRT011010 IRT011210 IRT011310 WRG500113 WRG500114 "
    "ERI411321 EAZ000038".split()
)
SEAT_UNAVAILABLE_CODES = frozenset(
    "WRI411345 WRT800176 ERR521128 WRS200019 WRS600242 WRS800009 WRS900309".split()
)
RESERVATION_REFUSED_CODES = frozenset(
    "WRR800029 ERR911531 ERR911051 ERR911501 ERR299920 ERR299922 ERR299932 ERR299933 ERR299934 ERR299935 "
    "ERR299936 ERR299937 ERR299939 ERR299941 ERR299943 ERR299992 ERR299993 ERR521143 ERR521158 ERR521185 "
    "ERR800052 ERR911421 ERR911528 WRR664254 WRR800045 ERR911081 ERR800056 S-ERR911411 S021 WRR664325 "
    "WRR700001 WRX000007".split()
)
INVALID_REQUEST_CODES = frozenset(
    "ERB000001 WRG200018 WRT100002 WRT100124 WRG200001 WRG200002 WRG200003 WRG200004 WRG200005 WRG200006 "
    "WRG200007 WRG200008 WRG200009 WRG200010 WRG200011 WRG200012 WRG200013 WRG200014 WRG200015 WRG200016 "
    "WRG200017 WRG200019 WRG200020 ERR800001 ERR800002 ERR800003 ERR800004 ERR800005 ERR800006 ERR800008 "
    "ERR800009 ERR800010 ERR800011 ERR800012 ERR800014 ERR800015 ERR800016 ERR800017 ERR800018 ERR800019 "
    "ERR800020 ERR800021 ERR800022 ERR800023 ERR800024 ERR800025 ERR800026 ERR800029 ERR800030 ERR800031 "
    "ERR800033 ERR800034 ERR800035 ERR800036 ERR800037 ERR800038 ERR930224 ERR930226 ERR930227 ERR930228 "
    "ERR930250 ERR930260 ERR930261 ERR930267 ERR930268 ERR930278 ERR930279 ERR930280 ERR930292 ERR930293 "
    "ERR930310 ERR930312 ERR930328 ERR930329 WRC000063 WRC000210 WRC000260 WRC000370 WRC000392 WRC000436 "
    "WRR664227 WRT400191 WRT400235 WRT400356 WRT800053 WRT800074 WRT800075".split()
)
NOT_ENTITLED_CODES = frozenset(
    "ERR800049 WRC000419 WRC800030 WRR800058 MRR000008 MRT200005 WRC000107 WRC000302 WRC000373 WRC000412 "
    "WRC000446 WRR664211".split()
)
SERVICE_UNAVAILABLE_CODE = "SEMGTK"
SERVICE_UNAVAILABLE_CODES = frozenset({SERVICE_UNAVAILABLE_CODE, "S000", "S001", "S002", "S003"})
RATE_LIMIT_CODES = frozenset({"BT019", "BT023"})
PROCESSING_CODES = frozenset({"WRT900900"})
ALREADY_PROCESSED_CODES = frozenset({"EZZ000014", "EVZ000102"})
# 로그인 응답에만 적용합니다(session._finish_login).
ACCOUNT_LOCKED_CODES = frozenset({"WRC000390"})
APP_UPDATE_REQUIRED_CODE = "SUPDATE"
# 앱 리터럴이 아니라 2026-10-21 부터 실서버가 보낸 관측 코드입니다(GitHub #32).
OBSERVED_APP_UPDATE_REQUIRED_CODES = frozenset({"-8204"})
SESSION_EXPIRED_CODE = "P058"

_APP_ERROR_BY_CODE: dict[str, type[KorailAppError]] = {
    **dict.fromkeys(NO_RESULT_CODES, KorailNoResultsError),
    NO_DIRECT_TRAIN_CODE: KorailNoDirectTrainError,
    **dict.fromkeys(SOLD_OUT_CODES, KorailSoldOutError),
    **dict.fromkeys(SEAT_UNAVAILABLE_CODES, KorailSeatUnavailableError),
    **dict.fromkeys(RESERVATION_REFUSED_CODES, KorailReservationRefusedError),
    **dict.fromkeys(INVALID_REQUEST_CODES, KorailInvalidRequestError),
    **dict.fromkeys(NOT_ENTITLED_CODES, KorailNotEntitledError),
    **dict.fromkeys(SERVICE_UNAVAILABLE_CODES, KorailServiceUnavailableError),
    **dict.fromkeys(RATE_LIMIT_CODES, KorailRateLimitError),
    **dict.fromkeys(PROCESSING_CODES, KorailProcessingError),
    **dict.fromkeys(ALREADY_PROCESSED_CODES, KorailAlreadyProcessedError),
    APP_UPDATE_REQUIRED_CODE: KorailAppUpdateRequiredError,
    **dict.fromkeys(OBSERVED_APP_UPDATE_REQUIRED_CODES, KorailAppUpdateRequiredError),
}


def classify_app_error(code: str | None, message: str | None, *, raw: object | None = None) -> KorailAppError:
    """실패 응답의 결과 코드에 맞는 ``KorailAppError`` 또는 그 하위 예외 객체를 만들어 반환합니다. 예외를 발생시키지는 않습니다."""
    return _APP_ERROR_BY_CODE.get(code or "", KorailAppError)(code, message, raw=raw)
