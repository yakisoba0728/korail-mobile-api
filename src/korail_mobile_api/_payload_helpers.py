# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""조회 요청 빌더가 공유하는 필드·문자열 처리를 제공합니다."""
from typing import TypeGuard

from .config import KorailConfig


def _device_version(config: KorailConfig) -> dict[str, str]:
    """Device·Version·선택 lang을 순서대로 담은 새 폼을 만듭니다."""
    fields = {"Device": config.device, "Version": config.version}
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _is_ascii_digits(value: object, lengths: frozenset[int]) -> TypeGuard[str]:
    """value가 허용된 길이의 ASCII 숫자 문자열인지 검사합니다. str.isdigit은 전각 숫자도 받으므로 사용하지 않으며, 거절 예외와 문구는 각 빌더가 정합니다."""
    return (
        isinstance(value, str)
        and len(value) in lengths
        and all("0" <= character <= "9" for character in value)
    )
