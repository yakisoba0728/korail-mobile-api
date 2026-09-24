# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 요청 빌더가 공유하는 내부 필드·문자열 도구."""
from typing import TypeGuard

from .config import KorailConfig


def _device_version(config: KorailConfig) -> dict[str, str]:
    """Device·Version·선택 lang을 순서대로 담은 새 폼을 만듭니다."""
    fields = {"Device": config.device, "Version": config.version}
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _is_ascii_digits(value: object, lengths: frozenset[int]) -> TypeGuard[str]:
    """``value`` 가 ``lengths`` 중 한 길이의 ASCII 숫자 문자열인지.

    ``str.isdigit`` 은 전각 숫자도 받으므로 쓰지 않습니다. read_payloads 도 이것을 씁니다; 거절할 때의 예외와 문구는 각 모듈이 정합니다."""
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all("0" <= character <= "9" for character in value)
    )
