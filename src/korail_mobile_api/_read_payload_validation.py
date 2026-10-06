# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 요청의 문자열·숫자·날짜 검증입니다. 요청별 범위와 선택값 정책은 호출부가 정합니다."""

from __future__ import annotations

from datetime import date

from ._payload_helpers import _is_ascii_digits
from .constants import KORAIL_MAX_PASSENGERS_PER_RESERVATION
from .errors import KorailProtocolError


def _int_text(value: int, name: str) -> str:
    """앱 DTO 는 String 이고 범위 검사가 없어 값의 판정은 서버에 맡깁니다 (CouponIn.java:29-30, ProductListIn.java:30-35,
    AmtSpecIn.java:30-36)."""
    if type(value) is not int:
        raise KorailProtocolError(f"{name} must be an integer")
    return str(value)


def _required_text(value: str | None, name: str) -> str:
    """``value`` 를 그대로 돌려주되 없거나 빈 문자열이면 거부합니다. 호출자 대부분이 서버 응답에서 파싱한 선택 필드를 그대로 넘기므로, ``None`` 도 인자로 받아
    ``errors.KorailProtocolError`` 로 거절합니다."""
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(f"{name} must not be empty")
    return value


def _optional_text(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
    return value


def _ascii_digits(
    value: str,
    name: str,
    *,
    lengths: frozenset[int] | None = None,
    maximum_length: int | None = None,
    allow_empty: bool = False,
) -> str:
    """ASCII 숫자 형식을 검사하고 요청별 오류를 발생시킵니다. lengths 는 허용 길이 집합, maximum_length 는 상한입니다. 둘 다 없으면 길이를 제한하지 않고
    allow_empty=True 이면 빈 문자열도 허용합니다."""
    if allow_empty and value == "":
        return value
    if lengths is not None:
        if not _is_ascii_digits(value, lengths):
            if len(lengths) == 1:
                (length,) = lengths
                raise KorailProtocolError(f"{name} must contain exactly {length} ASCII digits")
            expected = ", ".join(str(length) for length in sorted(lengths))
            raise KorailProtocolError(f"{name} must contain {expected} ASCII digit(s)")
        return value
    if (
        not isinstance(value, str)
        or not value
        or any(character < "0" or character > "9" for character in value)
        or (maximum_length is not None and len(value) > maximum_length)
    ):
        suffix = f" with at most {maximum_length} digits" if maximum_length is not None else ""
        raise KorailProtocolError(f"{name} must be an ASCII decimal string{suffix}")
    return value


def _passenger_count(value: int, name: str) -> int:
    if type(value) is not int or not 1 <= value <= KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            f"{name} must be an integer from 1 through {KORAIL_MAX_PASSENGERS_PER_RESERVATION}"
        )
    return value


def _calendar_date(value: str, name: str) -> date:
    _ascii_digits(value, name, lengths=frozenset({8}))
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError as exc:
        raise KorailProtocolError(f"{name} must be a valid calendar date") from exc


def _wire_component(value: str, name: str) -> str:
    resolved = _required_text(value, name)
    if "," in resolved:
        raise KorailProtocolError(f"{name} must not contain a comma")
    return resolved
