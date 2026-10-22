# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 필드·헤더·실패 봉투 정책을 공유하며 대기열 전송은 netfunnel에서 분리합니다.

API·대기열 클라이언트가 같은 규칙으로 전송 계층을 고르며 프록시 URL은 오류 메시지에 싣지 않습니다."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from collections.abc import Set as AbstractSet
from typing import TypeAlias
from urllib.parse import urlencode

import httpx

from .._domains.common.models import BaseKorailResponse
from ..config import KorailConfig
from ..errors import (
    SESSION_EXPIRED_CODE,
    KorailDynaPathError,
    KorailDynaPathRequiredError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
    classify_app_error,
)
from .dynapath import DYNAPATH_REQUIRED_PATHS, DynapathRequestContext, DynapathTokenGenerator
from .parsing import _envelope
from .wire import _device_version_key

#: 폼·쿼리 값입니다. 목록은 같은 키를 반복해 보냅니다.
FormValue: TypeAlias = str | int | bool | None | Sequence[str]
Form: TypeAlias = Mapping[str, FormValue] | Sequence[tuple[str, FormValue]]

_FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}

# 응답 DTO 가 CommonOut 을 상속하지 않아 strResult 누락이 실패가 아닌 경로입니다.
# evidence: app 7.0.6 StationDataOut.java:44-49, StationInfoOut.java:47-53, VerifyOnlineRefundsOut.java:29
_NON_COMMON_OUT_READ_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.common.stationdata",
        "/classes/com.korail.mobile.common.stationinfo",
        "/ebizmaas/EbizMaasStationList.do",
        "/classes/com.korail.mobile.refunds.verifyOnlineRefunds",
    }
)


def parse_base_response(
    data: object,
    *,
    raise_on_fail: bool = True,
    require_result: bool = True,
    common_out: bool | None = None,
) -> BaseKorailResponse:
    """FAIL 또는 CommonOut 기본 실패만 P058 만료로 판정합니다. 옵션별 계약은 checks/BEHAVIOR.md 참고."""
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object", raw=data)
    envelope = _envelope(data)
    response = BaseKorailResponse(
        h_msg_cd=envelope["h_msg_cd"],
        h_msg_txt=envelope["h_msg_txt"],
        str_result=envelope["strResult"],
        raw=data,
    )
    missing_result = "strResult" not in data
    failed = response.str_result == "FAIL" or (require_result and missing_result)
    if common_out is None:
        common_out = require_result
    if (failed or (common_out and missing_result)) and response.h_msg_cd == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(response.h_msg_cd, response.h_msg_txt, raw=data)
    if raise_on_fail and failed:
        raise classify_app_error(response.h_msg_cd, response.h_msg_txt, raw=data)
    return response


# evidence: app 7.0.6 DynaPathInterceptor.java:41
_DYNAPATH_BLOCK_CODES = frozenset({-1203, -1406, -2000, -8005, -8201, -8202, -8203})


def _dynapath_block_payload(payload: object) -> dict[str, object] | None:
    """앱의 키가 보호돼 최상위 정수를 모두 검사하므로 다른 필드의 같은 값도 오인할 수 있습니다."""
    if not isinstance(payload, dict):
        return None
    # 문자열은 봉투 없는 명시적 이용제한 코드만 봅니다. 다른 문자열 필드까지 보면 정상 데이터를 오인합니다.
    if "strResult" not in payload and payload.get("code") == "-2000":
        return payload
    for value in payload.values():
        if isinstance(value, int) and not isinstance(value, bool) and value in _DYNAPATH_BLOCK_CODES:
            return payload
    return None


def _decode_response(response: httpx.Response, *, path: str, block_paths: AbstractSet[str]) -> object:
    """판정 순서: DynaPath 차단(보호 경로, 상태 코드와 무관) → 2xx 가 아닌 상태 → JSON 오류."""
    try:
        payload, decoded = response.json(), True
    except ValueError:
        payload, decoded = None, False
    if path in block_paths:
        blocked_payload = _dynapath_block_payload(payload)
        if blocked_payload is not None:
            message = blocked_payload.get("message")
            raise KorailDynaPathError(str(message or "KORAIL DynaPath request rejected"), raw=blocked_payload)
    # 3xx 도 실패입니다. Retrofit 은 2xx 가 아닌 응답을 성공 본문으로 넘기지 않으며 리다이렉트는 따라가지 않습니다.
    if not 200 <= response.status_code < 300:
        raise KorailTransportError(
            f"KORAIL HTTP {response.status_code} for {response.request.method} {response.request.url.path}",
            status_code=response.status_code,
            raw=payload if decoded else response.content,
        )
    if not decoded:
        raise KorailProtocolError("KORAIL response body was not valid JSON", raw=response.content)
    return payload


def _without_empty(fields: Iterable[tuple[str, FormValue]]) -> list[tuple[str, FormValue]]:
    """빈 문자열만 생략하며 None은 바꾸지 않습니다."""
    return [(name, value) for name, value in fields if not (isinstance(value, str) and value == "")]


def _reject_none(fields: Iterable[tuple[str, FormValue]], path: str) -> None:
    # httpx 는 None 을 빈 값(key=)으로 보내지만 빌더의 생략 규칙은 빈 문자열이나 키 제외입니다.
    for name, value in fields:
        if value is None:
            raise KorailProtocolError(f"KORAIL request field {name} is None; nothing was sent to {path}")


def _form_value(value: object) -> str:
    """httpx 의 폼 값 변환과 같습니다. bool 은 true/false 입니다."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return "" if value is None else str(value)


def _encode_form(fields: Iterable[tuple[str, FormValue]]) -> bytes:
    """httpx ``data=`` 와 같은 바이트를 만들며 목록 값은 같은 키를 반복합니다."""
    pairs: list[tuple[str, str]] = []
    for name, value in fields:
        items = value if isinstance(value, list | tuple) else (value,)
        pairs.extend((name, _form_value(item)) for item in items)
    return urlencode(pairs).encode("ascii")


class KorailHttpClient:
    """``base_url`` 은 검사하지 않습니다."""

    def __init__(
        self,
        config: KorailConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.config = config
        self._dynapath_generator = (
            DynapathTokenGenerator(
                config.dynapath.token_settings,
                timestamp_ms_provider=config.dynapath.timestamp_ms_provider,
                random_text_provider=config.dynapath.random_text_provider,
            )
            if config.dynapath.token_settings is not None
            else None
        )
        # 앱의 OkHttp 가 API 요청에 붙이는 기본 헤더와 맞춥니다. OkHttp 는 Accept 를 붙이지 않으므로 httpx 기본값을 지웁니다.
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"User-Agent": config.user_agent, "Connection": "Keep-Alive", "Accept-Encoding": "gzip"},
            transport=build_transport(config, transport),
        )
        del self._client.headers["Accept"]

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    def close(self) -> None:
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        """설정된 AppVersion과 lang을 싣습니다. 보호된 언어 기본값은 추측하지 않습니다."""
        return _device_version_key(self.config)

    def _fields(
        self, data: Form | None, *, include_common: bool, omit_empty_fields: bool, path: str
    ) -> list[tuple[str, FormValue]]:
        """매핑은 공통 필드와 키를 합치고(뒤 값이 이김), 순서 목록은 그대로 이어 붙입니다."""
        common = self.common_fields() if include_common else {}
        if data is None or isinstance(data, Mapping):
            fields: list[tuple[str, FormValue]] = list({**common, **(data or {})}.items())
        else:
            fields = [*common.items(), *data]
        if omit_empty_fields:
            fields = _without_empty(fields)
        _reject_none(fields, path)
        return fields

    def _dynapath_headers(self, method: str, path: str, body: bytes) -> dict[str, str]:
        dynapath = self.config.dynapath
        if not dynapath.enabled:
            if path in DYNAPATH_REQUIRED_PATHS:
                raise KorailDynaPathRequiredError(
                    f"KORAIL {path} 는 DynaPath 토큰을 요구합니다. "
                    "KorailConfig(disable_dynapath=True) 를 빼거나, 실제 단말 "
                    "값을 쓰려면 build_config_from_env() 를 넘겨야 합니다."
                )
            return {}
        if path not in dynapath.allowlist_paths:
            return {}
        context = DynapathRequestContext(
            method=method,
            path=path,
            url=f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}",
            device=self.config.device,
            version=self.config.version,
            key=self.config.key,
            user_agent=self.config.user_agent,
            device_name=dynapath.device_name,
            os_version=dynapath.os_version,
            body=body,
            app_version=self.config.app_version,
        )
        try:
            if dynapath.token_provider is not None:
                token = dynapath.token_provider(context)
            elif self._dynapath_generator is not None:
                token = self._dynapath_generator(context)
            else:
                token = None
        except Exception as exc:
            raise KorailProtocolError("KORAIL DynaPath token provider failed") from exc
        if token is None:
            return {}
        # 헤더에 실을 수 없는 값은 httpx 의 날 예외 대신 요청 전에 거절합니다.
        if not isinstance(token, str) or not token.isascii():
            raise KorailProtocolError("KORAIL DynaPath token provider must return an ASCII str or None")
        return {dynapath.header_name: token}

    def _exchange(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        content: bytes | None = None,
        params: Mapping[str, FormValue] | None = None,
        raise_on_fail: bool,
        require_envelope: bool,
    ) -> BaseKorailResponse:
        """유일한 전송 경로입니다. 본문을 먼저 만든 뒤 그 바이트로 DynaPath 헤더를 정하고 한 번만 보냅니다."""
        headers.update(self._dynapath_headers(method, path, content or b""))
        if self._client.is_closed:
            raise KorailProtocolError(f"KORAIL client is closed; {method} {path} was not sent")
        try:
            try:
                response = self._client.send(
                    self._client.build_request(method, path, params=params, content=content, headers=headers)
                )
            except (httpx.HTTPError, httpx.InvalidURL) as exc:
                redact_failed_request(exc)
                raise KorailTransportError(f"KORAIL transport failed for {method} {path}") from exc
            payload = _decode_response(response, path=path, block_paths=self.config.dynapath.allowlist_paths)
            # 관측: getUUID.do 는 mutMrkVrfCd 와 strResult 만 반환합니다.
            common_out = path not in _NON_COMMON_OUT_READ_PATHS
            return parse_base_response(
                payload,
                raise_on_fail=raise_on_fail,
                require_result=require_envelope and common_out,
                common_out=common_out,
            )
        except (KorailTransportError, KorailProtocolError) as error:
            error.request_sent = True
            raise

    def post_form(
        self,
        path: str,
        data: Form | None = None,
        *,
        include_common: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        form_encoded: bool = True,
        omit_empty_fields: bool = True,
    ) -> BaseKorailResponse:
        """``require_envelope=False`` 는 KORAIL 봉투 없는 응답용. ``form_encoded=False`` 는 빈 본문 POST 입니다."""
        fields = self._fields(
            data, include_common=include_common, omit_empty_fields=omit_empty_fields, path=path
        )
        return self._exchange(
            "POST",
            path,
            headers=dict(_FORM_HEADERS) if form_encoded else {},
            content=_encode_form(fields) if form_encoded else None,
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )

    def post_query(
        self,
        path: str,
        params: Mapping[str, FormValue],
        *,
        include_common: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        omit_empty_fields: bool = False,
    ) -> BaseKorailResponse:
        """DTO가 @QueryMap이므로 POST 본문은 비우고 URL에 실어 보냅니다."""
        fields = self._fields(
            params, include_common=include_common, omit_empty_fields=omit_empty_fields, path=path
        )
        return self._exchange(
            "POST",
            path,
            headers=dict(_FORM_HEADERS),
            content=b"",
            params=dict(fields),
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )

    def get_json(
        self,
        path: str,
        params: Mapping[str, FormValue] | None = None,
        *,
        include_common: bool = False,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        omit_empty_fields: bool = False,
    ) -> BaseKorailResponse:
        """``require_envelope=False`` 는 봉투 없는 응답용."""
        fields = self._fields(
            params, include_common=include_common, omit_empty_fields=omit_empty_fields, path=path
        )
        return self._exchange(
            "GET",
            path,
            headers={},
            params=dict(fields),
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )


# 프록시까지의 TLS(https 프록시)는 httpx 0.25.0·httpcore 0.18.0부터 지원합니다.
_HTTPX_VERSION = tuple(int(part) for part in re.findall(r"\d+", httpx.__version__)[:2])


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
    # 낮은 httpx 에서 프록시까지 TLS 없이 연결되거나 실패하는 대신 요청 전에 거절합니다.
    if proxy.url.scheme == "https" and _HTTPX_VERSION < (0, 25):
        raise ValueError("https proxies need httpx 0.25 or later")
    try:
        # Client 의 proxies/proxy 인자는 httpx 0.24 와 0.28 에서 달라 두 버전에 공통인 HTTPTransport(proxy=Proxy) 를 씁니다.
        return httpx.HTTPTransport(proxy=proxy)
    except ImportError as exc:
        raise ImportError("SOCKS proxies need the socks extra: pip install 'korail-mobile-api[socks]'") from exc


def redact_failed_request(exc: Exception) -> None:
    """전송 실패 예외에 붙은 요청을 메서드와 쿼리 없는 URL만 남긴 사본으로 바꿉니다. 예외 객체와 타입은 그대로입니다."""
    # 원래 요청에는 로그인 아이디·변환된 비밀번호·카드 필드(본문), 세션 쿠키·DynaPath 토큰(헤더), 식별자(쿼리)가 있습니다.
    if not isinstance(exc, httpx.HTTPError):
        return
    try:
        request = exc.request
    except RuntimeError:
        return
    exc.request = httpx.Request(request.method, request.url.copy_with(query=None))
