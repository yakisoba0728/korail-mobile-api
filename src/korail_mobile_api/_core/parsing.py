# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""선택값은 관대하게, 후속 요청에 필요한 값은 엄격하게 읽습니다; 공통 규칙은 checks/BEHAVIOR.md 참고.

조회 봉투와 필수 행 규칙, 타입이 정해진 스칼라 읽기를 함께 둡니다.

필드 메타데이터 패턴(``_domains/checkin`` 이 기준 예시): 모델 필드가 전송 키와 읽기 규칙을 들고, 파서는 ``wire_model``
하나로 읽습니다. ``wire(key)`` 는 관대한 nullable 문자열·기본값 ``None``, ``wire(key, read, default=...)`` 는
명시한 기본값을 씁니다. 생성자 필수 필드는 표준 ``field(metadata=...)`` 로 선언합니다::

    @dataclass(frozen=True, kw_only=True)
    class Seat:
        seat_no: str = field(metadata={"wire": "seatNo", "read": required_str})
        car_no: int = field(metadata={"wire": "scarNo", "read": required_int})
        note: str | None = wire("rmkCont")
        rows: tuple[Row, ...] = ()  # 중첩 목록·교차 검사·특수 규칙은 메타데이터 없이 명시 코드로 넘깁니다
        raw: Mapping[str, object] = field(default_factory=dict[str, object], repr=False, compare=False)

    seat = wire_model(Seat, row, "seat", rows=tuple(rows), raw=row)
    seats = wire_models(Seat, _required_read_rows(raw, "seatList", "seat list"), "seat")
    response = wire_model(SeatResponse, raw, "seat list", seats=seats, **_response_fields(raw))

``wire_model(cls, data, context, /, **extra)`` 는 ``dataclasses.fields(cls)`` 순서로 ``read(data, key, context)`` 를
부르고 ``extra`` 와 합쳐 생성합니다. ``raw`` 는 호출부가 지금 규칙대로 넘깁니다: 행 동일성 ``raw=row``, 얕은 복사
``raw=dict(row)``, 응답은 ``**_response_fields(raw)``. ``wire_models`` 는 ``raw=row``, ``copy_raw=True`` 면
``dict(row)`` 입니다. 읽기 규칙(누락 / null / 잘못된 타입; ``context`` 는 엄격 규칙의 오류 문구에만 쓰입니다):

- ``nullable_str`` (기본): None / None / None. 문자열 규칙은 모두 JSON 정수를 문자열로 읽습니다.
- ``strict_str``: None / None / 오류.
- ``present_str``: 오류 / None / 오류. 키는 필수, 값은 nullable 입니다.
- ``required_str``: 오류 / 오류 / 오류.
- ``defaulted_str``: "" / 오류 / 오류. 앱 기본값을 쓰는 18개 필드 전용입니다(checks/BEHAVIOR.md).
- ``optional_int``: None / None / None. JSON int 와 ASCII 십진 문자열을 받습니다.
- ``required_int``: 오류 / 오류 / 오류. JSON int 와 ASCII 십진 문자열(앞의 ``-`` 하나)을 받습니다.
- ``optional_bool``: None / None / None.

``wire()`` 의 반환 타입과 필수 생성자 인자는 mypy·Pyright 가 검사합니다. 표준 필드 메타데이터의 reader 반환형은
``tests/test_types.py`` 가 선언과 대조합니다. ``wire_model`` 의 동적 키·추가 중첩값은 정적으로 연결되지 않으므로
각 도메인 파서 계약 테스트에서 검증합니다.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import MISSING, field, fields
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeAlias, TypedDict, TypeGuard, TypeVar, cast, overload

from ..errors import (
    SESSION_EXPIRED_CODE,
    KorailApiError,
    KorailProtocolError,
    KorailSessionExpiredError,
    classify_app_error,
)
from .wire import _is_ascii_digits

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

_P = ParamSpec("_P")
_R = TypeVar("_R")
_T = TypeVar("_T")
_D = TypeVar("_D", bound="DataclassInstance")
_Reader: TypeAlias = Callable[[Mapping[str, object], str, str], _T]


def _is_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    if not isinstance(value, Mapping):
        return False
    return all(isinstance(key, str) for key in cast(Mapping[object, object], value))


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _all_mappings(rows: list[object]) -> TypeGuard[list[Mapping[str, object]]]:
    return all(_is_mapping(row) for row in rows)


def _preserve_read_raw(parser: Callable[_P, _R]) -> Callable[_P, _R]:
    """파서가 거절한 응답 전체를 기존 예외의 raw 에, 기존 부분 원문을 parser_raw 에 남깁니다. 검사·재전송은 하지 않습니다."""

    @wraps(parser)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return parser(*args, **kwargs)
        except KorailApiError as error:
            response = args[0] if args else kwargs.get("raw", kwargs.get("response"))
            raw = getattr(response, "raw", response) if not _is_mapping(response) else response
            if error.raw is not raw:
                error.parser_raw = error.raw
                error.raw = raw
            raise

    return wrapped


def _envelope(data: Mapping[str, object]) -> dict[str, str | None]:
    """JSON 정수는 관측에 따라 문자열로 읽고, 다른 비문자열 값은 거절합니다."""
    envelope: dict[str, str | None] = {}
    invalid: list[str] = []
    for name in ("h_msg_cd", "h_msg_txt", "strResult"):
        value = data.get(name)
        if isinstance(value, int) and not isinstance(value, bool):
            try:
                envelope[name] = str(value)
            except ValueError as exc:
                error = KorailProtocolError(
                    f"KORAIL response envelope field {name} is an integer too long to use"
                )
                error.raw = data
                raise error from exc
        elif value is None or isinstance(value, str):
            envelope[name] = value
        else:
            invalid.append(name)
    if invalid:
        error = KorailProtocolError(
            f"KORAIL response envelope fields must be strings or null: {', '.join(invalid)}"
        )
        error.raw = data
        raise error
    return envelope


class _ResponseFields(TypedDict):
    h_msg_cd: str | None
    h_msg_txt: str | None
    str_result: str | None
    raw: Mapping[str, object]


def _response_fields(raw: Mapping[str, object]) -> _ResponseFields:
    envelope = _envelope(raw)
    return {
        "h_msg_cd": envelope["h_msg_cd"],
        "h_msg_txt": envelope["h_msg_txt"],
        "str_result": envelope["strResult"],
        "raw": raw,
    }


def _optional_mapping(data: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    value = data.get(key)
    return value if _is_mapping(value) else None


def _optional_list(data: Mapping[str, object], key: str) -> list[object]:
    value = data.get(key)
    return value if _is_list(value) else []


def _nested_rows(raw: Mapping[str, object], outer_key: str, inner_key: str) -> list[Mapping[str, object]]:
    return _rows(_optional_mapping(raw, outer_key), inner_key)


def _row(value: object, context: str) -> Mapping[str, object]:
    if _is_mapping(value):
        return value
    raise KorailProtocolError(f"KORAIL {context} must be an object")


def _response_mapping(raw: Mapping[str, object]) -> dict[str, object]:
    """얕은 복사본을 돌려줍니다. 봉투 필드 타입은 ``_envelope`` 가 검사하며 성공 여부는 보지 않습니다."""
    if not _is_mapping(raw):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    return dict(raw)


def _rows(data: Mapping[str, object] | None, key: str) -> list[Mapping[str, object]]:
    if not _is_mapping(data):
        return []
    return [item for item in _optional_list(data, key) if _is_mapping(item)]


def _present_strings(data: Mapping[str, object], keys: tuple[str, ...]) -> tuple[str, ...]:
    values: list[str] = []
    for key in keys:
        value = _optional_scalar_string(data, key)
        if value is not None:
            values.append(value)
    return tuple(values)


def _strict_scalar_string(
    data: Mapping[str, object],
    key: str,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(f"KORAIL {context} field {key} is an integer too long to use") from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be a string, an integer, or null")


def required_str(data: Mapping[str, object], key: str, context: str) -> str:
    """누락·null 은 거절하고, JSON 정수는 문자열로 받습니다(String 선언 필드가 정수로 온 관측)."""
    value = _strict_scalar_string(data, key, context)
    if value is None:
        raise KorailProtocolError(f"KORAIL {context} field {key} is required")
    return value


def present_str(data: Mapping[str, object], key: str, context: str) -> str | None:
    """키는 필수이고 값은 nullable 입니다."""
    if key not in data:
        raise KorailProtocolError(f"KORAIL {context} field {key} is required")
    return _strict_scalar_string(data, key, context)


def _optional_scalar_string(data: Mapping[str, object], key: str) -> str | None:
    """선택 스칼라를 문자열로 읽고 잘못된 값은 None으로 처리합니다."""
    try:
        return _strict_scalar_string(data, key, "")
    except KorailProtocolError:
        return None


def _optional_integer(data: Mapping[str, object], key: str) -> int | None:
    """JSON 정수나 ASCII 숫자 문자열을 정수로 읽고 그 밖의 값은 None으로 처리합니다."""
    if data.get(key) is None:
        return None
    try:
        return _required_integer(data, key, "")
    except KorailProtocolError:
        return None


# evidence: app 7.0.6 StreamingJsonDecoder.java:395-403, kotlinx/serialization/json/internal/JsonReader.java:575-640
def _required_integer(
    data: Mapping[str, object],
    key: str,
    context: str,
) -> int:
    """필수 정수: JSON int 또는 ASCII 숫자 문자열(앞의 ``-`` 하나 허용)을 받습니다. null/bool/float·지수 표기는 거절합니다.
    앱도 따옴표 숫자는 첫 글자의 ``-`` 만 부호로 받습니다."""
    value = data.get(key)
    if type(value) is int:
        return value
    if isinstance(value, str) and _is_ascii_digits(value.removeprefix("-")):
        try:
            return int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported ASCII-decimal length"
            ) from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be an integer or an ASCII decimal string")


def _inventory_ratio(data: Mapping[str, object], key: str) -> float | None:
    """창측 비율(앱 String 필드)을 읽습니다. 누락과 앱 기본값 "" 은 None 입니다."""
    value = data.get(key, "")
    if value == "":
        return None
    number: int | float | str
    # bool 을 숫자로 받지 않도록 정확한 int·float 타입만 허용합니다.
    if (
        type(value) is int
        or type(value) is float
        or (isinstance(value, str) and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) is not None)
    ):
        number = value
    else:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be numeric or an ASCII decimal string"
        )
    try:
        ratio = float(number)
    except (OverflowError, ValueError) as exc:
        raise KorailProtocolError(f"KORAIL seat inventory field {key} must be finite") from exc
    if not math.isfinite(ratio):
        raise KorailProtocolError(f"KORAIL seat inventory field {key} must be finite")
    return ratio


def _validate_envelope(
    raw: Mapping[str, object],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    returned_failure_codes: frozenset[str] = frozenset(),
    return_all_failures: bool = False,
    allow_result_only_success: bool = False,
) -> bool:
    if not _is_mapping(raw):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    # raw 를 직접 받는 호출자는 http.parse_base_response 를 거치지 않으므로 봉투 필드 타입을 여기서도 확인합니다.
    envelope = _envelope(raw)
    if "strResult" not in raw:
        raise KorailProtocolError(
            "KORAIL response omitted strResult; the protected APK default "
            "cannot be inferred for this typed read"
        )
    if allow_result_only_success and ("h_msg_cd" not in raw and "h_msg_txt" not in raw):
        if raw["strResult"] != "SUCC":
            raise KorailProtocolError("KORAIL result-only envelope requires the exact success result")
        return False
    code = envelope["h_msg_cd"]
    message = envelope["h_msg_txt"]
    result = envelope["strResult"]
    # 앱은 strResult 실패일 때만 로그인 필요로 봅니다.
    if result == "FAIL" and code == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(code, message, raw=raw)
    failed = result == "FAIL"
    if (
        failed
        and not return_all_failures
        and code not in accepted_empty_codes
        and code not in returned_failure_codes
    ):
        raise classify_app_error(code, message, raw=raw)
    return failed


def _validate_strict_read_envelope(
    raw: Mapping[str, object],
    *,
    allow_result_only_success: bool = False,
) -> None:
    _validate_envelope(
        raw,
        allow_result_only_success=allow_result_only_success,
    )
    if raw.get("strResult") != "SUCC":
        raise KorailProtocolError("KORAIL strict read response strResult must be SUCC")


def _required_read_rows(data: Mapping[str, object], key: str, context: str) -> list[Mapping[str, object]]:
    """누락·null·비객체 행은 거절합니다. 앱이 필수로 표시한 목록에 씁니다."""
    value = data.get(key)
    if _is_list(value) and _all_mappings(value):
        return value
    raise KorailProtocolError(f"KORAIL {context} field {key} must be an object list")


def _optional_read_rows(data: Mapping[str, object], key: str, context: str) -> list[Mapping[str, object]]:
    """선택·nullable 객체 목록을 읽습니다. 누락·null 은 빈 목록이고, 목록이 아니거나 객체가 아닌 행은 거절합니다."""
    if data.get(key) is None:
        return []
    return _required_read_rows(data, key, context)


def _typed_required_string(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
    non_empty: bool = False,
) -> str:
    value = required_str(data, key, context)
    if non_empty and not value.strip():
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a non-empty string")
    return value


def _typed_optional_int(data: Mapping[str, object], key: str) -> int | None:
    """선택값을 음이 아닌 정수로 읽고 다른 값은 None으로 처리합니다."""
    value = _optional_integer(data, key)
    return value if value is not None and value >= 0 else None


def _typed_non_negative_integer_value(
    value: object,
    key: str,
    *,
    context: str,
) -> int:
    if type(value) is int:
        parsed = value
    elif _is_ascii_digits(value):
        try:
            parsed = int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported ASCII-decimal length"
            ) from exc
    else:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a non-negative integer or ASCII-decimal string"
        )
    if parsed < 0:
        raise KorailProtocolError(f"KORAIL {context} field {key} must not be negative")
    return parsed


def defaulted_str(data: Mapping[str, object], key: str, context: str) -> str:
    """누락은 앱 합성 생성자의 기본값 "" 이고, 값이 있으면 문자열·JSON 정수만 받습니다(일반 좌석 재고의 layout_type 정수 관측). null 과 다른
    타입은 앱의 Json 설정이 보호돼 있어 받아도 되는지 확인할 수 없으므로 거절합니다."""
    return required_str(data, key, context) if key in data else ""


def nullable_str(data: Mapping[str, object], key: str, context: str) -> str | None:
    return _optional_scalar_string(data, key)


def optional_int(data: Mapping[str, object], key: str, context: str) -> int | None:
    return _optional_integer(data, key)


def optional_bool(data: Mapping[str, object], key: str, context: str) -> bool | None:
    value = data.get(key)
    return value if isinstance(value, bool) else None


strict_str = _strict_scalar_string
required_int = _required_integer


@overload
def wire(key: str) -> str | None: ...
@overload
def wire(key: str, read: _Reader[_T], *, default: _T) -> _T: ...
def wire(key: str, read: _Reader[object] | None = None, *, default: object = MISSING) -> object:
    """모델 필드에 전송 키와 읽기 규칙을 붙입니다. ``read`` 를 빼면 nullable_str·기본값 None 입니다."""
    if read is None:
        read, default = nullable_str, None
    return field(default=default, metadata={"wire": key, "read": read})


def wire_model(cls: type[_D], data: Mapping[str, object], context: str, /, **extra: object) -> _D:
    """전송 메타데이터 필드를 선언 순서로 읽어 ``extra`` 와 함께 생성합니다."""
    values: dict[str, object] = {
        item.name: item.metadata["read"](data, item.metadata["wire"], context)
        for item in fields(cls)
        if "wire" in item.metadata
    }
    return cls(**values, **extra)


def wire_models(
    cls: type[_D],
    rows: Iterable[Mapping[str, object]],
    context: str,
    *,
    copy_raw: bool = False,
) -> tuple[_D, ...]:
    """행마다 ``wire_model`` 을 부르고 ``raw`` 에 행 자체(또는 ``copy_raw`` 면 얕은 복사)를 넘깁니다."""
    return tuple(wire_model(cls, row, context, raw=dict(row) if copy_raw else row) for row in rows)
