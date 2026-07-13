from __future__ import annotations

import random
import string
import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from urllib.parse import quote_plus

from .constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEFAULT_OS_VERSION,
)

DYNAPATH_BASE_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
DYNAPATH_TABLE_INDEX = 1
DYNAPATH_RANDOM_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
DYNAPATH_DEFAULT_I8 = 161
DYNAPATH_DEFAULT_I9 = 30
DYNAPATH_DEFAULT_I10 = 2
KORAIL_DYNAPATH_APP_ID = "com.korail.talk"
KORAIL_DYNAPATH_OS_TYPE = "Android"
KORAIL_DYNAPATH_SDK_VERSION = "v1.0.3"
KORAIL_DYNAPATH_SIGNING_CERT_SHA256 = "38ff229cb34c7dda8e28220a2d750cceec28db661a36d95ad92d82f6d3c618f9"
KORAIL_DYNAPATH_APP_SIGNATURE_HASH = "38ff229cb34c7dda8e28220a2d750cce"
KORAIL_DYNAPATH_AS_VALUE = f"[{KORAIL_DYNAPATH_APP_SIGNATURE_HASH}]"
KORAIL_PROBE_DYNAPATH_DEVICE_ID = "7f000001-android-probe"
KORAIL_PROBE_DYNAPATH_AS_VALUE = f"%5B{KORAIL_DYNAPATH_APP_SIGNATURE_HASH}%5D"
KORAIL_PROBE_DYNAPATH_DEVICE_MODEL = "SM-S928N"
KORAIL_PROBE_DYNAPATH_OS_VERSION = "13"
KORAIL_PROBE_DYNAPATH_SDK_VERSION = "v1"
KORAIL_PROBE_DYNAPATH_RANDOM_ALPHABET = string.ascii_uppercase + string.digits


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


def build_dynapath_prefix(*, table: str, table_index: int = DYNAPATH_TABLE_INDEX, i11: int = 2, i12: int = 30) -> str:
    return f"{chr(table_index + 97)}{table[2]}{table[37]}{table[i11]}{table[i12 - 1]}"


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
    device_id: str
    as_value: str
    app_start_ts: str
    os_version: str
    device_model: str
    app_id: str = KORAIL_DYNAPATH_APP_ID
    os_type: str = KORAIL_DYNAPATH_OS_TYPE
    sdk_version: str = KORAIL_DYNAPATH_SDK_VERSION
    table_index: int = DYNAPATH_TABLE_INDEX
    table: str = field(default_factory=lambda: generate_dynapath_encoding_table(DYNAPATH_TABLE_INDEX))
    i8: int = DYNAPATH_DEFAULT_I8
    i9: int = DYNAPATH_DEFAULT_I9
    i10: int = DYNAPATH_DEFAULT_I10
    secure_user: bool = False
    debug: bool = False
    emulator: bool = False
    hooked: bool = False
    recent_request_deltas: tuple[int, ...] = (0,)

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

    def __post_init__(self) -> None:
        if self.enabled and (
            (self.token_provider is None) == (self.token_settings is None)
        ):
            raise ValueError(
                "enabled DynaPath requires exactly one token provider or token settings"
            )


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
) -> str:
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
    ]
    fields.extend(("rt", str(delta)) for delta in settings.recent_request_deltas)
    fields.extend(
        [
            ("os", settings.os_version),
            ("dm", settings.device_model),
            ("st", settings.os_type),
            ("sv", settings.sdk_version),
        ]
    )
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


def _probe_random_text() -> str:
    return "".join(random.choices(KORAIL_PROBE_DYNAPATH_RANDOM_ALPHABET, k=4))


def generate_korail_probe_dynapath_token(
    *,
    device_id: str = KORAIL_PROBE_DYNAPATH_DEVICE_ID,
    timestamp_ms: int | None = None,
    random_text: str | None = None,
    app_start_ts: int | str | None = None,
    as_value: str = KORAIL_PROBE_DYNAPATH_AS_VALUE,
    os_version: str = KORAIL_PROBE_DYNAPATH_OS_VERSION,
    device_model: str = KORAIL_PROBE_DYNAPATH_DEVICE_MODEL,
    sdk_version: str = KORAIL_PROBE_DYNAPATH_SDK_VERSION,
    table: str = DYNAPATH_ENCODING_TABLE,
) -> str:
    ts = _timestamp_ms() if timestamp_ms is None else timestamp_ms
    rand = _probe_random_text() if random_text is None else random_text
    start_ts = str(_timestamp_ms() if app_start_ts is None else app_start_ts)
    payload = (
        f"ai={KORAIL_DYNAPATH_APP_ID}"
        f"&di={device_id}"
        f"&as={as_value}"
        f"&su=false"
        f"&dbg=false"
        f"&emu=false"
        f"&hk=false"
        f"&it={start_ts}"
        f"&ts={ts}"
        f"&rt=0"
        f"&os={os_version}"
        f"&dm={device_model}"
        f"&st={KORAIL_DYNAPATH_OS_TYPE}"
        f"&sv={sdk_version}"
    )
    dyn_key = f"{sdk_version}+{rand}+{ts}"
    encoded_key = encode_normal_be(
        dyn_key,
        table,
        i8=DYNAPATH_DEFAULT_I8,
        i9=DYNAPATH_DEFAULT_I9,
        i10=DYNAPATH_DEFAULT_I10,
    )
    custom_table = make_encode_table(make_dynapath_key(dyn_key), DYNAPATH_DEFAULT_I9, table)
    encoded_body = encode_normal_be(
        payload,
        custom_table,
        i8=DYNAPATH_DEFAULT_I8,
        i9=DYNAPATH_DEFAULT_I9,
        i10=DYNAPATH_DEFAULT_I10,
    )
    prefix = build_dynapath_prefix(
        table=table,
        table_index=DYNAPATH_TABLE_INDEX,
        i11=DYNAPATH_DEFAULT_I10,
        i12=DYNAPATH_DEFAULT_I9,
    )
    return f"{prefix}{table[len(encoded_key)]}{encoded_key}{encoded_body}"


class KorailProbeDynapathTokenProvider:
    def __init__(
        self,
        *,
        device_id: str = KORAIL_PROBE_DYNAPATH_DEVICE_ID,
        as_value: str = KORAIL_PROBE_DYNAPATH_AS_VALUE,
        os_version: str = KORAIL_PROBE_DYNAPATH_OS_VERSION,
        device_model: str = KORAIL_PROBE_DYNAPATH_DEVICE_MODEL,
        sdk_version: str = KORAIL_PROBE_DYNAPATH_SDK_VERSION,
        timestamp_ms_provider: TimestampMsProvider | None = None,
        random_text_provider: RandomTextProvider | None = None,
        app_start_ts_provider: TimestampMsProvider | None = None,
    ) -> None:
        self.device_id = device_id
        self.as_value = as_value
        self.os_version = os_version
        self.device_model = device_model
        self.sdk_version = sdk_version
        self._timestamp_ms_provider = timestamp_ms_provider or _timestamp_ms
        self._random_text_provider = random_text_provider or _probe_random_text
        self._app_start_ts_provider = app_start_ts_provider or _timestamp_ms

    def __call__(self, context: DynapathRequestContext | None = None) -> str | None:
        if context is not None and not any(path in context.url for path in DYNAPATH_ALLOWLIST_PATHS):
            return None
        return generate_korail_probe_dynapath_token(
            device_id=self.device_id,
            timestamp_ms=self._timestamp_ms_provider(),
            random_text=self._random_text_provider(),
            app_start_ts=self._app_start_ts_provider(),
            as_value=self.as_value,
            os_version=self.os_version,
            device_model=self.device_model,
            sdk_version=self.sdk_version,
        )


class DynapathTokenGenerator:
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
        self._last_timestamp_ms: int | None = None
        self._recent_request_deltas: list[int] = []

    @property
    def recent_request_deltas(self) -> tuple[int, ...]:
        return tuple(self._recent_request_deltas)

    def __call__(self, _context: DynapathRequestContext | None = None) -> str:
        timestamp_ms = self._timestamp_ms_provider()
        previous = self._last_timestamp_ms
        if previous is None:
            try:
                previous = int(self.settings.app_start_ts)
            except ValueError:
                previous = timestamp_ms
        delta = timestamp_ms - previous
        self._last_timestamp_ms = timestamp_ms
        if len(self._recent_request_deltas) >= 5:
            self._recent_request_deltas.pop(0)
        self._recent_request_deltas.append(delta)
        return generate_dynapath_token(
            replace(self.settings, recent_request_deltas=self.recent_request_deltas),
            timestamp_ms=timestamp_ms,
            random_text=self._random_text_provider(),
        )
