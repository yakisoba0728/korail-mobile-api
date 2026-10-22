# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""선택값은 관대하게, 후속 요청에 필요한 값은 엄격하게 읽습니다; 공통 규칙은 checks/BEHAVIOR.md 참고.

조회 봉투와 필수 행 규칙, 타입이 정해진 스칼라 읽기를 함께 둡니다."""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, ParamSpec, TypedDict, TypeVar

from .._domains.common.models import BaseKorailResponse
from ..errors import (
    SESSION_EXPIRED_CODE,
    KorailApiError,
    KorailProtocolError,
    KorailSessionExpiredError,
    classify_app_error,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _preserve_read_raw(parser: Callable[_P, _R]) -> Callable[_P, _R]:
    """파서가 거절한 응답 전체를 기존 예외의 raw 에, 기존 부분 원문을 parser_raw 에 남깁니다. 검사·재전송은 하지 않습니다."""

    @wraps(parser)
    def wrapped(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return parser(*args, **kwargs)
        except KorailApiError as error:
            response = args[0] if args else kwargs.get("raw", kwargs.get("response"))
            raw = response if isinstance(response, Mapping) else getattr(response, "raw", response)
            if error.raw is not raw:
                error.parser_raw = error.raw
                error.raw = raw
            raise

    return wrapped


def _envelope(data: Mapping[str, Any]) -> dict[str, str | None]:
    """JSON 정수는 관측에 따라 문자열로 읽고, 다른 비문자열 값은 거절합니다."""
    envelope: dict[str, str | None] = {}
    invalid = []
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


def _model_response_fields(response: BaseKorailResponse) -> _ResponseFields:
    return {
        "h_msg_cd": response.h_msg_cd,
        "h_msg_txt": response.h_msg_txt,
        "str_result": response.str_result,
        "raw": response.raw,
    }


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any] | None:
    value = data.get(key)
    return value if isinstance(value, Mapping) else None


def _optional_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = data.get(key)
    return value if isinstance(value, list) else []


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
) -> list[Mapping[str, Any]]:
    return _rows(_optional_mapping(raw, outer_key), inner_key)


def _row(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(f"KORAIL {context} contained a non-object item")
    return value


def _rows(
    data: Mapping[str, Any] | None,
    key: str,
) -> list[Mapping[str, Any]]:
    if not isinstance(data, Mapping):
        return []
    return [item for item in _optional_list(data, key) if isinstance(item, Mapping)]


def _present_strings(
    data: Mapping[str, Any],
    keys: tuple[str, ...],
) -> tuple[str, ...]:
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


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> str | None:
    """선택 스칼라를 문자열로 읽고 잘못된 값은 None으로 처리합니다."""
    try:
        return _strict_scalar_string(data, key, context)
    except KorailProtocolError:
        return None


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> int | None:
    """JSON 정수나 ASCII 숫자 문자열을 정수로 읽고 그 밖의 값은 None으로 처리합니다."""
    if data.get(key) is None:
        return None
    try:
        return _required_integer(data, key, context)
    except KorailProtocolError:
        return None


def _required_integer(
    data: Mapping[str, object],
    key: str,
    context: str,
) -> int:
    """필수 정수: JSON int 또는 ASCII 숫자 문자열(앞의 ``-`` 하나 허용)을 받습니다. null/bool/float·지수 표기는 거절합니다. 앱의 따옴표 숫자 처리는
    StreamingJsonDecoder.java:395-403 → kotlinx/serialization/json/internal/JsonReader.java:575-640 에 있고,
    첫 글자의 ``-`` 만 부호로 받습니다."""
    value = data.get(key)
    if type(value) is int:
        return value
    if isinstance(value, str):
        digits = value[1:] if value.startswith("-") else value
        if digits and all("0" <= character <= "9" for character in digits):
            try:
                return int(value)
            except ValueError as exc:
                raise KorailProtocolError(
                    f"KORAIL {context} field {key} has an unsupported ASCII-decimal length"
                ) from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be an integer or an ASCII decimal string")


def _optional_bool(
    data: Mapping[str, object],
    key: str,
) -> bool | None:
    """불리언을 그대로 반환하고 누락·다른 타입은 None으로 처리합니다."""
    value = data.get(key)
    return value if isinstance(value, bool) else None


def _inventory_ratio(data: Mapping[str, Any], key: str) -> float | None:
    """창측 비율(String 선언, TResidualSeatsResearchOutWindow.java:51-56)을 읽습니다. 누락과 앱 기본값 "" 은 None 입니다."""
    value = data.get(key, "")
    if value == "":
        return None
    number: int | float | str
    # bool 을 숫자로 받지 않도록 정확한 int·float 타입만 허용합니다.
    if type(value) in (int, float):
        number = value
    elif isinstance(value, str) and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) is not None:
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


def _nullable_scalar_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str = "",
) -> dict[str, Any]:
    """String 선택값을 같은 규칙으로 읽으며 모델 생성자 **kwargs 호환을 위해 값 타입은 Any입니다."""
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    returned_failure_codes: frozenset[str] = frozenset(),
    return_all_failures: bool = False,
    allow_result_only_success: bool = False,
) -> bool:
    if not isinstance(raw, Mapping):
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
    # 앱은 strResult 실패일 때만 로그인 필요로 봅니다(CommonOut.java:426-438).
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
    raw: Mapping[str, Any],
    *,
    allow_result_only_success: bool = False,
) -> None:
    _validate_envelope(
        raw,
        allow_result_only_success=allow_result_only_success,
    )
    if raw.get("strResult") != "SUCC":
        raise KorailProtocolError("KORAIL strict read response strResult must be SUCC")


def _required_read_rows(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Mapping[str, Any]]:
    """누락·null·비객체 행은 거절합니다(ReceiptInfos.java:49, DeliveredTicketOut.java:50 의 필수 마스크)."""
    value = data.get(key)
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be an object list")
    return value


def _required_read_strings(
    data: Mapping[str, Any],
    fields: Mapping[str, str],
    context: str,
) -> dict[str, Any]:
    """누락·null 은 거절하고, JSON 정수는 문자열로 받습니다(String 선언 필드가 정수로 온 관측, :func:`_strict_scalar_string`)."""
    values = {}
    for attr, key in fields.items():
        value = _strict_scalar_string(data, key, context)
        if value is None:
            raise KorailProtocolError(f"KORAIL {context} field {key} is required")
        values[attr] = value
    return values


def _optional_read_rows(data: Mapping[str, Any], key: str, context: str) -> list[Mapping[str, Any]]:
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
    value = _typed_required_scalar_string(data, key, context=context)
    if non_empty and not value.strip():
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a non-empty string")
    return value


def _typed_required_scalar_string(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
) -> str:
    """일반 좌석 재고에서 layout_type 정수가 관측되어 String 선언과 달리 허용합니다."""
    if key not in data:
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a string or an integer")
    value = data[key]
    if isinstance(value, str):
        return value
    # bool 을 정수 스칼라로 받지 않습니다.
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(f"KORAIL {context} field {key} is an integer too long to use") from exc
    raise KorailProtocolError(f"KORAIL {context} field {key} must be a string or an integer")


def _typed_optional_int(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> int | None:
    """선택값을 음이 아닌 정수로 읽고 다른 값은 None으로 처리합니다."""
    value = _optional_integer(data, key, context)
    return value if value is not None and value >= 0 else None


def _typed_non_negative_integer_value(
    value: object,
    key: str,
    *,
    context: str,
) -> int:
    if type(value) is int:
        parsed = value
    elif isinstance(value, str) and value and all("0" <= character <= "9" for character in value):
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


def _typed_defaulted_string(
    data: Mapping[str, object],
    key: str,
    *,
    context: str,
) -> str:
    """누락은 앱 합성 생성자의 기본값 "" 이고, 값이 있으면 문자열·JSON 정수만 받습니다. null 과 다른 타입은 앱의 Json 설정이 보호돼 있어 받아도 되는지 확인할 수 없으므로
    거절합니다."""
    return _typed_required_scalar_string(data, key, context=context) if key in data else ""
