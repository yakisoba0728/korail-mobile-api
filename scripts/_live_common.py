# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""Shared pacing and device-identity helpers for the live operator scripts.

Every live script paces its outbound requests the same way and aborts the
same way when the device identity cannot be built from the environment. This
module holds both, so each script no longer carries its own copy.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from korail_mobile_api import KorailClient
    from korail_mobile_api.config import KorailConfig


class Pacer:
    """Enforce a minimum spacing between outbound requests."""

    def __init__(self, min_interval_s: float) -> None:
        self.min_interval_s = min_interval_s
        self._last: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self._last is not None:
            remaining = self.min_interval_s - (now - self._last)
            if remaining > 0:
                time.sleep(remaining)
        self._last = time.monotonic()


def install_pacing(client: KorailClient, pacer: Pacer) -> None:
    inner = client.http._client
    hooks = dict(inner.event_hooks)
    hooks["request"] = [
        *hooks.get("request", []),
        lambda request: pacer.wait(),
    ]
    inner.event_hooks = hooks


def device_identity_or_abort(
    build_config_from_env: Callable[[], KorailConfig],
) -> KorailConfig | None:
    try:
        return build_config_from_env()
    except RuntimeError as exc:
        print(f"ABORTED: {exc}")
        return None
