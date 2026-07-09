from __future__ import annotations

import random
import string
import time
from collections.abc import Callable
from dataclasses import dataclass

from .constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEFAULT_OS_VERSION,
)

DYNAPATH_ENCODING_TABLE = "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"


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
TimestampMsProvider = Callable[[], int]
RandomTextProvider = Callable[[], str]


@dataclass(frozen=True)
class DynapathTokenSettings:
    app_id: str
    device_id: str
    as_value: str
    app_start_ts: str
    os_version: str
    device_model: str
    os_type: str
    sdk_version: str
    table: str = DYNAPATH_ENCODING_TABLE
    i8: int = 161
    i9: int = 30
    i10: int = 2


@dataclass(frozen=True)
class DynapathConfig:
    enabled: bool = False
    token_provider: DynapathTokenProvider | None = None
    token_settings: DynapathTokenSettings | None = None
    timestamp_ms_provider: TimestampMsProvider | None = None
    random_text_provider: RandomTextProvider | None = None
    header_name: str = DYNAPATH_HEADER_NAME
    allowlist_paths: frozenset[str] = DYNAPATH_ALLOWLIST_PATHS
    device_name: str = KORAIL_DEFAULT_DEVICE_NAME
    os_version: str = KORAIL_DEFAULT_OS_VERSION


def string_to_xa1s(data: str) -> list[int]:
    result: list[int] = []
    for ch in data:
        cp = ord(ch)
        if cp < 128:
            result.append(cp)
        elif cp < 2048:
            result.append(128 | ((cp >> 7) & 15))
            result.append(cp & 127)
        elif cp >= 262144:
            result.append(160)
            result.append((cp >> 14) & 127)
            result.append((cp >> 7) & 127)
            result.append(cp & 127)
        elif (63488 & cp) != 55296:
            result.append(((cp >> 14) & 15) | 144)
            result.append((cp >> 7) & 127)
            result.append(cp & 127)
    return result


def make_dynapath_key(key: str) -> int:
    value = 0
    for ch in key:
        cp = ord(ch)
        bit = 32768
        for _ in range(16):
            if bit & cp:
                break
            bit >>= 1
        value = (value * (bit << 1)) + cp
    return value


def _pick_table_char(base_table: str, remainder: int, used: str) -> str:
    count = 0
    for ch in base_table:
        if ch not in used:
            if count == remainder:
                return ch
            count += 1
    return " "


def make_encode_table(num: int, encode_size: int, base_table: str) -> str:
    result = ""
    temp = num
    for i in range(encode_size):
        divisor = encode_size - i
        remainder = temp % divisor
        result += _pick_table_char(base_table, remainder, result)
        temp //= divisor
    return result


def encode_normal_be(data: str, table: str, *, i8: int = 161, i9: int = 30, i10: int = 2) -> str:
    bytes_like = string_to_xa1s(data)
    out: list[str] = []
    arr = [0] * (i10 + 1)

    idx = 0
    remain = len(bytes_like) % i10
    full_len = len(bytes_like) - remain

    while idx < full_len:
        val = 0
        for _ in range(i10):
            val = (val * i8) + bytes_like[idx]
            idx += 1
        for i in range(i10 + 1):
            arr[i] = val % i9
            val //= i9
        for i in range(i10, -1, -1):
            out.append(table[arr[i]])

    if remain > 0:
        val = 0
        for _ in range(remain):
            val = (val * i8) + bytes_like[idx]
            idx += 1
        for i in range(remain + 1):
            arr[i] = val % i9
            val //= i9
        while remain >= 0:
            out.append(table[arr[remain]])
            remain -= 1

    return "".join(out)


def _timestamp_ms() -> int:
    return int(time.time() * 1000)


def _random_text() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


def generate_dynapath_token(
    settings: DynapathTokenSettings,
    *,
    timestamp_ms: int | None = None,
    random_text: str | None = None,
) -> str:
    ts = _timestamp_ms() if timestamp_ms is None else timestamp_ms
    rand = _random_text() if random_text is None else random_text
    payload = (
        f"ai={settings.app_id}"
        f"&di={settings.device_id}"
        f"&as={settings.as_value}"
        f"&su=false"
        f"&dbg=false"
        f"&emu=false"
        f"&hk=false"
        f"&it={settings.app_start_ts}"
        f"&ts={ts}"
        f"&rt=0"
        f"&os={settings.os_version}"
        f"&dm={settings.device_model}"
        f"&st={settings.os_type}"
        f"&sv={settings.sdk_version}"
    )
    dyn_key = f"v1+{rand}+{ts}"
    encoded_key = encode_normal_be(
        dyn_key,
        settings.table,
        i8=settings.i8,
        i9=settings.i9,
        i10=settings.i10,
    )
    custom_table = make_encode_table(
        make_dynapath_key(dyn_key),
        settings.i9,
        settings.table,
    )
    encoded_body = encode_normal_be(
        payload,
        custom_table,
        i8=settings.i8,
        i9=settings.i9,
        i10=settings.i10,
    )
    return f"bEeEP{settings.table[len(encoded_key)]}{encoded_key}{encoded_body}"
