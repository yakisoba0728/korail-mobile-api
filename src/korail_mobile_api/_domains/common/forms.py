# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 폼입니다."""

from __future__ import annotations

import time
from collections.abc import Sequence

from ..._core.wire import _device_version_key
from ...config import KorailConfig
from ...errors import KorailInvalidInputError


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    """캐시·서비스 상태·승무원 호출 사유 요청의 timeStamp 입니다. 생략하면 현재 밀리초 epoch 이며, 제공한 값은 검증하지 않습니다."""
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_common_code_form(
    config: KorailConfig,
    code: str | Sequence[str],
) -> dict[str, str | int | list[str]]:
    """문자열 하나는 코드 하나이고, 빈 목록이면 ``code`` 필드를 싣지 않습니다. 기기 크기·SDK 정수는 설정을 사용합니다."""
    if isinstance(code, str):
        codes = [code]
    elif (
        isinstance(code, Sequence)
        and not isinstance(code, bytes | bytearray | memoryview)
        and all(isinstance(item, str) for item in code)
    ):
        codes = list(code)
    else:
        raise KorailInvalidInputError("code must be a string or a sequence of strings")
    return {
        **_device_version_key(config),
        "code": codes,
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
        "OSVersion": config.android_sdk_int,
    }
