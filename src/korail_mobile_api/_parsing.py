# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""도메인 모델에 의존하지 않는 내부 JSON 필드 읽기 도구.

선택 필드의 관대한 변환과 필수 필드의 오류 문구는 구분해서 유지합니다.
응답 봉투의 성공·실패 정책과 raw 복사 여부는 각 호출자가 결정합니다.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from .errors import KorailApiError, KorailProtocolError


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _preserve_read_raw(parser: Callable[_P, _R]) -> Callable[_P, _R]:
    """조회 파서가 거절한 응답 전체를 기존 예외에 남깁니다. 검사·재전송은 하지 않습니다."""
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


def _reject_non_string_envelope_fields(data: Mapping[str, Any]) -> None:
    """봉투의 세 필드는 문자열 또는 null이어야 합니다. 성공 판정은 호출자가 맡습니다."""
    invalid = [
        name
        for name in ("h_msg_cd", "h_msg_txt", "strResult")
        if name in data and data[name] is not None and not isinstance(data[name], str)
    ]
    if invalid:
        raise KorailProtocolError(
            "KORAIL response envelope fields must be strings or null: "
            f"{', '.join(invalid)}"
        )


def _response_fields(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "h_msg_cd": raw.get("h_msg_cd"),
        "h_msg_txt": raw.get("h_msg_txt"),
        "str_result": raw.get("strResult"),
        "raw": raw,
    }


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any] | None:
    """객체면 그대로, 아니면(없음·리스트·스칼라) ``None``."""
    value = data.get(key)
    return value if isinstance(value, Mapping) else None


def _optional_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    """리스트면 그대로(원소 검사 없음), 아니면 빈 리스트."""
    value = data.get(key)
    return value if isinstance(value, list) else []


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
) -> list[Mapping[str, Any]]:
    """``{outer: {inner: [...]}}`` 의 객체 원소들. 모양이 어긋나면 빈 리스트."""
    return _rows(_optional_mapping(raw, outer_key), inner_key)


def _row(value: Any, context: str) -> Mapping[str, Any]:
    """필수 객체 — 객체가 아니면 거부합니다."""
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} contained a non-object item"
        )
    return value


def _rows(
    data: Mapping[str, Any] | None,
    key: str,
) -> list[Mapping[str, Any]]:
    """``key`` 리스트의 객체 원소들. 리스트가 아니면 빈 리스트, 객체가 아닌 원소는 건너뜀."""
    if not isinstance(data, Mapping):
        return []
    return [item for item in _optional_list(data, key) if isinstance(item, Mapping)]


def _optional_string(
    data: Mapping[str, Any],
    key: str,
) -> str | None:
    """문자열이면 그대로, 아니면 ``None``."""
    value = data.get(key)
    return value if isinstance(value, str) else None


def _required_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str:
    """필수 문자열. 키가 없거나 문자열이 아니면 거부합니다.

    ``Seat`` 의 합성 생성자(``Seat.java:53-59``)는 다섯 필드 중 하나라도 없으면
    ``throwMissingFieldException`` 을 던집니다 — 7.0.6 도 처리하지 않는 응답
    모양이므로 선택으로 읽지 않습니다.
    """
    value = data.get(key)
    if not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string"
        )
    return value


def _present_strings(
    data: Mapping[str, Any],
    keys: tuple[str, ...],
) -> tuple[str, ...]:
    """선택 문자열 값이 실제로 온 키들을 순서대로 모읍니다."""
    values: list[str] = []
    for key in keys:
        value = _optional_string(data, key)
        if value is not None:
            values.append(value)
    return tuple(values)


def _strict_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    """JSON 문자열·정수·``null`` 을 받고 그 밖의 모양은 **거부**합니다.

    KORAIL 은 APK 가 자바 ``String`` 으로 선언한 필드를 숫자로도 보냅니다(예약
    응답의 ``h_jrny_cnt="0001"`` 과 예약 이력의 ``1``). 정수는 문자열로
    정규화합니다. 폼에 되울리는 값처럼 정확해야 하는 필드에만 씁니다 —
    선택 필드는 :func:`_optional_scalar_string` 입니다.
    """
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass.
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(
                f"KORAIL {context} field {key} is an integer too long to use"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string, an integer, or null"
    )


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> str | None:
    """선택 스칼라 — 문자열은 그대로, JSON 정수는 문자열로, 그 밖은 ``None``."""
    try:
        return _strict_scalar_string(data, key, context)
    except KorailProtocolError:
        return None


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str = "",
) -> int | None:
    """선택 정수 — 정수나 ASCII 10진 문자열이면 ``int``, 그 밖은 ``None``."""
    if data.get(key) is None:
        return None
    try:
        return _required_integer(data, key, context)
    except KorailProtocolError:
        return None


def _required_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    """필수 정수. JSON 정수와 따옴표 친 ASCII 10진 문자열을 받습니다.

    앱의 kotlinx 디코더(``StreamingJsonDecoder.decodeInt()`` →
    ``JsonReader.consumeNumericLiteral()``)도 따옴표 친 숫자를 받습니다.
    null/bool/float/비숫자는 거부합니다.
    """
    value = data.get(key)
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        try:
            return int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported "
                "ASCII-decimal length"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be an integer or an "
        "ASCII decimal string"
    )


def _optional_bool(
    data: Mapping[str, Any],
    key: str,
) -> bool | None:
    """``bool`` 이면 그대로, 아니면(없음 포함) ``None`` — "없음" 과 "거짓" 을 구분합니다."""
    value = data.get(key)
    return value if isinstance(value, bool) else None


def _nullable_string_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
) -> dict[str, str | None]:
    return {
        attribute: _optional_string(data, wire_name)
        for attribute, wire_name in field_map.items()
    }


def _nullable_scalar_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str,
) -> dict[str, str | None]:
    """:func:`_nullable_string_fields` 와 같되 JSON 정수도 문자열로 받습니다."""
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }
