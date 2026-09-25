# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 폼의 삽입 순서를 한곳에서 유지합니다."""

from typing import TypeGuard

from .config import KorailConfig


def _device_version(config: KorailConfig) -> dict[str, str]:
    """Key 를 싣지 않는 요청용입니다."""
    fields = {"Device": config.device, "Version": config.version}
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _device_version_key(config: KorailConfig) -> dict[str, str]:
    """공통 DTO의 Device·Version·Key·선택 lang 순서입니다(CommonIn.java:467–474)."""
    fields = {"Device": config.device, "Version": config.version, "Key": config.key}
    if config.lang is not None:
        fields["lang"] = config.lang
    return fields


def _is_ascii_digits(value: object, lengths: frozenset[int]) -> TypeGuard[str]:
    """value가 허용된 길이의 ASCII 숫자 문자열인지 검사합니다. str.isdigit은 전각 숫자도 받으므로 사용하지 않으며, 거절 예외와 문구는 각 빌더가 정합니다."""
    return (
        isinstance(value, str) and len(value) in lengths and all("0" <= character <= "9" for character in value)
    )
