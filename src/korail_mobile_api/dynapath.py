from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEFAULT_OS_VERSION,
)


@dataclass(frozen=True)
class DynapathRequestContext:
    method: str
    path: str
    url: str
    device: str
    version: str
    key: str
    user_agent: str
    device_name: str
    os_version: str


DynapathTokenProvider = Callable[[DynapathRequestContext], str | None]


@dataclass(frozen=True)
class DynapathConfig:
    enabled: bool = False
    token_provider: DynapathTokenProvider | None = None
    header_name: str = DYNAPATH_HEADER_NAME
    allowlist_paths: frozenset[str] = DYNAPATH_ALLOWLIST_PATHS
    device_name: str = KORAIL_DEFAULT_DEVICE_NAME
    os_version: str = KORAIL_DEFAULT_OS_VERSION
