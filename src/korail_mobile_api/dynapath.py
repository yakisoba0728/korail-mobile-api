# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""토큰 공식은 SDK 평문 흐름을 유지하며 기본 기기 식별자는 합성값입니다(DynaPathMobileSDK.java:29-72)."""

from __future__ import annotations

import random
import string
import threading
import time
import uuid
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import quote_plus

from .constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    KORAIL_DEFAULT_DEVICE_NAME,
)

DYNAPATH_BASE_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DYNAPATH_TABLE_INDEX = 1
# 논스 알파벳과 4회 추출: a/b.java:138-149. SDK 의 평문 리터럴입니다.
DYNAPATH_RANDOM_ALPHABET = string.ascii_lowercase + string.ascii_uppercase + string.digits
DYNAPATH_DEFAULT_I8 = 161
DYNAPATH_DEFAULT_I9 = 30
DYNAPATH_DEFAULT_I10 = 2
KORAIL_DYNAPATH_APP_ID = "com.korail.talk"
KORAIL_DYNAPATH_OS_TYPE = "Android"
KORAIL_DYNAPATH_SDK_VERSION = "v1.0.3"
KORAIL_DYNAPATH_SIGNING_CERT_SHA256 = "38ff229cb34c7dda8e28220a2d750cceec28db661a36d95ad92d82f6d3c618f9"
# b/e.java:55-71 은 서명 해시를 소문자 hex 32자로 절단합니다(b/d.java:20). SHA-256 상수: com/kakao/sdk/auth/Constants.java:28.
KORAIL_DYNAPATH_APP_SIGNATURE_HASH = KORAIL_DYNAPATH_SIGNING_CERT_SHA256[:32]
KORAIL_DYNAPATH_AS_VALUE = f"[{KORAIL_DYNAPATH_APP_SIGNATURE_HASH}]"


def _prime_table(count: int = 100) -> list[int]:
    primes: list[int] = []
    candidate = 2
    while len(primes) < count + 1:
        is_prime = True
        for prime in primes:
            if prime * prime > candidate:
                break
            if candidate % prime == 0:
                is_prime = False
                break
        if is_prime:
            primes.append(candidate)
        candidate += 1
    return primes[1:]


DYNAPATH_PRIMES = tuple(_prime_table())


def _sdk_permute_alphabet(value: str, multiplier: int, step: int) -> str:
    length = len(value)
    block_size = 1
    for prime in DYNAPATH_PRIMES:
        if prime <= length:
            block_size = prime
        else:
            break

    counts = [0] * block_size
    chars = [""] * block_size
    factor = 1
    for idx in range(block_size):
        target = ((factor % block_size) * step) % block_size
        counts[target] += 1
        if counts[target] == 1:
            chars[idx] = value[target]
        factor *= multiplier

    encoded: list[str] = []
    missing: list[str] = []
    for idx, char in enumerate(chars):
        if char:
            encoded.append(char)
            continue
        for missing_idx in range(block_size):
            if counts[missing_idx] == 0:
                replacement = value[missing_idx]
                chars[idx] = replacement
                missing.append(replacement)
                counts[missing_idx] = 1
                break

    while block_size < length:
        missing.append(value[block_size])
        block_size += 1

    missing_text = "".join(missing)
    if len(missing_text) < DYNAPATH_PRIMES[0]:
        return "".join(encoded) + missing_text
    return "".join(encoded) + _sdk_permute_alphabet(missing_text, multiplier, step)


def generate_dynapath_encoding_table(index: int = DYNAPATH_TABLE_INDEX) -> str:
    multiplier = DYNAPATH_PRIMES[index % 29]
    step = DYNAPATH_PRIMES[(index // 29) % 29]
    return _sdk_permute_alphabet(DYNAPATH_BASE_ALPHABET, multiplier, step)


DYNAPATH_ENCODING_TABLE = generate_dynapath_encoding_table(DYNAPATH_TABLE_INDEX)


def build_dynapath_prefix(
    *,
    table: str,
    table_index: int = DYNAPATH_TABLE_INDEX,
    i11: int = 2,
    i12: int = 30,
) -> str:
    return f"{chr(table_index + 97)}{table[2]}{table[37]}{table[i11]}{table[i12 - 1]}"


@dataclass(frozen=True)
class DynapathRequestContext:
    """DynaPath 토큰 공급자에게 전달할 요청 메타데이터를 담습니다."""

    method: str
    path: str
    url: str
    device: str
    version: str
    key: str
    user_agent: str
    device_name: str
    os_version: str


#: 요청 정보(``DynapathRequestContext``)를 받아 DynaPath 토큰 문자열을 돌려주는 함수의 타입입니다. ``None``을 돌려주면
#: 헤더를 붙이지 않고, 함수가 예외를 발생시키면 요청을 보내지 않고 ``KorailProtocolError``를 발생시킵니다.
DynapathTokenProvider = Callable[[DynapathRequestContext], str | None]
TimestampMsProvider = Callable[[], int]
RandomTextProvider = Callable[[], str]


@dataclass(frozen=True)
class DynapathTokenSettings:
    """DynaPath 토큰 생성에 사용할 기기값과 시각 공급자를 구성합니다."""

    device_id: str
    as_value: str
    app_start_ts: str
    os_version: str
    device_model: str
    app_id: str = KORAIL_DYNAPATH_APP_ID
    os_type: str = KORAIL_DYNAPATH_OS_TYPE
    sdk_version: str = KORAIL_DYNAPATH_SDK_VERSION
    table_index: int = DYNAPATH_TABLE_INDEX
    table: str = DYNAPATH_ENCODING_TABLE
    i8: int = DYNAPATH_DEFAULT_I8
    i9: int = DYNAPATH_DEFAULT_I9
    i10: int = DYNAPATH_DEFAULT_I10
    secure_user: bool = False
    debug: bool = False
    emulator: bool = False
    hooked: bool = False

    def __post_init__(self) -> None:
        for name in (
            "device_id",
            "as_value",
            "app_start_ts",
            "os_version",
            "device_model",
        ):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"DynaPath {name} must be provided")
        int(self.app_start_ts)


def generate_dynapath_device_id() -> str:
    """앱은 실제 android_id 를 읽습니다(a/a.java:15-20); 토큰 필드는 a/b.java:85 의 di 입니다."""
    return uuid.uuid4().hex[:16]


def build_default_token_settings() -> DynapathTokenSettings:
    """앱의 it 는 초기화 시각(a/a.java:13-20, a/b.java:95, DynaPathMobileSDK.java:64), ts 는 토큰 생성
    시각(DynaPathMobileSDK.java:43, a/b.java:98)으로 서로 다릅니다."""
    return DynapathTokenSettings(
        device_id=generate_dynapath_device_id(),
        as_value=KORAIL_DYNAPATH_AS_VALUE,
        app_start_ts=str(_timestamp_ms()),
        os_version=KORAIL_DEFAULT_ANDROID_OS_RELEASE,
        device_model=KORAIL_DEFAULT_DEVICE_NAME,
    )


@dataclass(frozen=True)
class DynapathConfig:
    """DynaPath 활성화 여부와 토큰 공급 방식을 구성합니다."""

    enabled: bool = False
    token_provider: DynapathTokenProvider | None = None
    token_settings: DynapathTokenSettings | None = None
    timestamp_ms_provider: TimestampMsProvider | None = None
    random_text_provider: RandomTextProvider | None = None
    header_name: str = DYNAPATH_HEADER_NAME
    allowlist_paths: frozenset[str] = DYNAPATH_ALLOWLIST_PATHS
    device_name: str = KORAIL_DEFAULT_DEVICE_NAME
    os_version: str = KORAIL_DEFAULT_ANDROID_OS_RELEASE

    def __post_init__(self) -> None:
        if self.enabled and ((self.token_provider is None) == (self.token_settings is None)):
            raise ValueError("enabled DynaPath requires exactly one token provider or token settings")


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
    return "".join(random.choices(DYNAPATH_RANDOM_ALPHABET, k=4))


def java_urlencode(value: str) -> str:
    return quote_plus(value, safe="*-._").replace("~", "%7E")


def _java_form_encode(fields: list[tuple[str, str]]) -> str:
    return "&".join(f"{java_urlencode(key)}={java_urlencode(value)}" for key, value in fields)


def generate_dynapath_token(
    settings: DynapathTokenSettings,
    *,
    timestamp_ms: int | None = None,
    random_text: str | None = None,
    recent_intervals: Sequence[int] = (),
) -> str:
    """토큰 하나를 만듭니다. recent_intervals 는 rt 값이며 비어 있으면 SDK 처럼 키를 뺍니다(a/b.java:100-108). SDK 의 generate() 는 만들기
    직전에 이력을 추가하므로 앱 토큰에는 rt 가 늘 있습니다."""
    ts = _timestamp_ms() if timestamp_ms is None else timestamp_ms
    rand = _random_text() if random_text is None else random_text
    fields = [
        ("ai", settings.app_id),
        ("di", settings.device_id),
        ("as", settings.as_value),
        ("su", str(settings.secure_user).lower()),
        ("dbg", str(settings.debug).lower()),
        ("emu", str(settings.emulator).lower()),
        ("hk", str(settings.hooked).lower()),
        ("it", settings.app_start_ts),
        ("ts", str(ts)),
        *(("rt", str(interval)) for interval in recent_intervals),
        ("os", settings.os_version),
        ("dm", settings.device_model),
        ("st", settings.os_type),
        ("sv", settings.sdk_version),
    ]
    payload = _java_form_encode(fields)
    dyn_key = f"{settings.sdk_version}+{rand}+{ts}"
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
    prefix = build_dynapath_prefix(
        table=settings.table,
        table_index=settings.table_index,
        i11=settings.i10,
        i12=settings.i9,
    )
    return f"{prefix}{settings.table[len(encoded_key)]}{encoded_key}{encoded_body}"


class DynapathTokenGenerator:
    """앱의 DynaPath SDK처럼 토큰마다 직전 토큰(첫 토큰은 앱 시작 시각)과의 시간 차이를 최근 5개까지 기록해 ``rt``로 보냅니다.

    SDK와 같이 빈 이력으로 시작합니다."""

    # 근거: DynaPathMobileSDK.java:43-44, a/b.java:58-68. SDK 도 초기화 때 빈 이력으로 시작합니다(a/a.java:17).

    def __init__(
        self,
        settings: DynapathTokenSettings,
        *,
        timestamp_ms_provider: TimestampMsProvider | None = None,
        random_text_provider: RandomTextProvider | None = None,
    ) -> None:
        self.settings = settings
        self._timestamp_ms_provider = timestamp_ms_provider or _timestamp_ms
        self._random_text_provider = random_text_provider or _random_text
        self._lock = threading.Lock()
        self._last_ts = int(settings.app_start_ts)
        self._intervals: deque[int] = deque(maxlen=5)

    def __call__(self, _context: DynapathRequestContext | None = None) -> str:
        with self._lock:
            ts = self._timestamp_ms_provider()
            self._intervals.append(ts - self._last_ts)
            self._last_ts = ts
            intervals = tuple(self._intervals)
        return generate_dynapath_token(
            self.settings,
            timestamp_ms=ts,
            random_text=self._random_text_provider(),
            recent_intervals=intervals,
        )
