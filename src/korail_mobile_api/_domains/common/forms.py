# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 폼입니다. 보호된 기본값은 추측하지 않으며 순서·빈 값 처리의 근거는 각 빌더에 남깁니다."""

from __future__ import annotations

import time
from collections.abc import Sequence

from ..._core.wire import _device_version_key
from ...config import KorailConfig


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    """캐시 요청에 현재 시각의 쿼리를 구성합니다. timestamp_ms 를 생략하면 현재 밀리초 epoch 이며, 제공한 값은 검증하지 않습니다."""
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_common_code_form(
    config: KorailConfig,
    code: str | Sequence[str],
) -> dict[str, object]:
    """라우트 선언: NetworkApi.java:317,321. 기기 크기·SDK 정수는 설정을 사용합니다 (CommonCodeIn.java:31-34,55)."""
    form: dict[str, object] = {
        **_device_version_key(config),
        "code": [code] if isinstance(code, str) else list(code),
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
    }
    form["OSVersion"] = config.android_sdk_int
    return form


def build_service_status_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    return build_cache_query(timestamp_ms)


def build_crew_request_list_query(
    timestamp_ms: int | None = None,
) -> dict[str, str]:
    """sealed CommonIn이 실제 CrewCallCommonIn 직렬화기로 넘기므로 timeStamp를 싣습니다(NetworkService.java:3952-3955;
    CommonIn.java:350)."""
    return build_cache_query(timestamp_ms)
