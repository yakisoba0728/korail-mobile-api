# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""API·대기열 클라이언트가 같은 규칙으로 전송 계층을 고르며 프록시 URL은 오류 메시지에 싣지 않습니다."""

from __future__ import annotations

import httpx

from .config import KorailConfig


def build_transport(config: KorailConfig, transport: httpx.BaseTransport | None) -> httpx.BaseTransport | None:
    """``proxy``가 없으면 ``transport``를 그대로 돌려줘 httpx 기본 동작(환경변수 프록시 포함)을 유지합니다."""
    if config.proxy is None:
        return transport
    # 함께 주면 httpx 는 프록시 mount 로 모든 요청을 보내 transport 를 조용히 무시합니다.
    if transport is not None:
        raise ValueError("KorailConfig.proxy cannot be combined with a custom transport")
    try:
        proxy = httpx.Proxy(config.proxy)
    except (ValueError, httpx.InvalidURL):
        # httpx 0.28 미만은 socks5h 를 받지 않습니다. httpx 의 메시지에는 사용자 이름이 남아 원인을 잇지 않습니다.
        raise ValueError("httpx rejected the proxy URL; socks5h needs httpx 0.28 or later") from None
    try:
        # Client 의 proxies/proxy 인자는 httpx 0.24 와 0.28 에서 달라 두 버전에 공통인 HTTPTransport(proxy=Proxy) 를 씁니다.
        return httpx.HTTPTransport(proxy=proxy)
    except ImportError as exc:
        raise ImportError("SOCKS proxies need the socks extra: pip install 'korail-mobile-api[socks]'") from exc
