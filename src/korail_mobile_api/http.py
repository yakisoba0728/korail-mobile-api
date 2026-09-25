# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공통 필드·헤더·실패 봉투 정책을 공유하며 대기열 전송은 netfunnel에서 분리합니다."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any
from urllib.parse import urlencode

import httpx

from ._parsing import _envelope
from .config import KorailConfig
from .constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_REQUIRED_PATHS,
)
from .dynapath import DynapathRequestContext, DynapathTokenGenerator
from .errors import (
    SESSION_EXPIRED_CODE,
    KorailDynaPathError,
    KorailDynaPathRequiredError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
    classify_app_error,
)
from .models import BaseKorailResponse

# 응답 모델이 CommonOut 을 상속하지 않아 strResult 누락이 실패가 아닌 읽기 경로: StationDataOut(stationdata, EbizMaasStationList),
# StationInfoOut(stationinfo).
_NON_COMMON_OUT_READ_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.common.stationdata",
        "/classes/com.korail.mobile.common.stationinfo",
        "/ebizmaas/EbizMaasStationList.do",
        # VerifyOnlineRefundsOut.java:29 는 CommonOut 을 상속하지 않습니다. strResult 누락 기본값(:91-94)은 null 이 아니라 보호
        # 문자열입니다.
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
    """FAIL 또는 CommonOut 기본 실패만 P058 만료로 판정합니다(CommonOut.java:361,426-438); 옵션별 계약은 checks/BEHAVIOR.md 참고."""
    if not isinstance(data, dict):
        error = KorailProtocolError("KORAIL response must be a JSON object")
        error.raw = data
        raise error
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
        raise KorailSessionExpiredError(
            response.h_msg_cd,
            response.h_msg_txt,
            raw=data,
        )
    if raise_on_fail and failed:
        raise classify_app_error(
            response.h_msg_cd,
            response.h_msg_txt,
            raw=data,
        )
    return response


#: 7.0.6 ``DynaPathInterceptor`` 의 고정 리터럴 차단 코드 집합 (``DynaPathInterceptor.java:41`` ``STLhns``). 보호 경로 응답 본문의 정수
#: 필드가 이 중 하나면 차단입니다.
_DYNAPATH_BLOCK_CODES = frozenset({-1203, -1406, -2000, -8005, -8201, -8202, -8203})


def _dynapath_block_payload(payload: object) -> dict[str, Any] | None:
    """앱의 키가 보호돼 최상위 정수를 모두 검사하므로 다른 필드의 같은 값도 오인할 수 있습니다(DynaPathInterceptor.java:97-124)."""
    if not isinstance(payload, dict):
        return None
    for value in payload.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, int) and value in _DYNAPATH_BLOCK_CODES:
            return payload
    return None


def _send(
    client: httpx.Client, send: Callable[[], httpx.Response], *, method: str, path: str
) -> httpx.Response:
    # 이때 요청은 나가지 않았습니다.
    if client.is_closed:
        raise KorailProtocolError(f"KORAIL client is closed; {method} {path} was not sent")
    try:
        return send()
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        raise KorailTransportError(f"KORAIL transport failed for {method} {path}") from exc


def _decode_response(response: httpx.Response, *, path: str) -> Any:
    """판정 순서: DynaPath 차단(보호 경로, 상태 코드와 무관) → 2xx 가 아닌 상태 → JSON 오류."""
    try:
        payload, decoded = response.json(), True
    except ValueError:
        payload, decoded = None, False
    if path in DYNAPATH_ALLOWLIST_PATHS:
        blocked_payload = _dynapath_block_payload(payload)
        if blocked_payload is not None:
            message = blocked_payload.get("message")
            raise KorailDynaPathError(
                str(message or "KORAIL DynaPath request rejected"),
                raw=blocked_payload,
            )
    # 3xx 도 실패입니다 — Retrofit 은 2xx 가 아닌 응답을 성공 본문으로 넘기지 않습니다
    # (analysis/jadx/sources/retrofit2/OkHttpCall.java:184-201). 리다이렉트는 따라가지 않습니다.
    if not 200 <= response.status_code < 300:
        transport_error = KorailTransportError(
            f"KORAIL HTTP {response.status_code} for {response.request.method} {response.request.url.path}"
        )
        transport_error.raw = payload if decoded else response.content
        raise transport_error
    if not decoded:
        protocol_error = KorailProtocolError("KORAIL response body was not valid JSON")
        protocol_error.raw = response.content
        raise protocol_error
    return payload


def _is_empty_string(value: object) -> bool:
    return isinstance(value, str) and value == ""


def _drop_empty(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """빈 문자열만 생략하며 None은 바꾸지 않습니다(NetworkService.java:15342)."""
    return {key: value for key, value in mapping.items() if not _is_empty_string(value)}


def _form_value(value: Any) -> str:
    """None 은 빈 값, bool 은 true/false 입니다."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


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
        # 앱의 OkHttp 가 API 요청에 붙이는 기본 헤더와 맞춥니다(okhttp3/internal/http/BridgeInterceptor.java:56-68). OkHttp 는
        # Accept 를 붙이지 않으므로 httpx 기본값을 지웁니다.
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"User-Agent": config.user_agent, "Connection": "Keep-Alive", "Accept-Encoding": "gzip"},
            transport=transport,
        )
        del self._client.headers["Accept"]

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    def close(self) -> None:
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        """lang은 보호된 기본값을 추측하지 않고 설정된 경우만 싣습니다(CommonIn.java:381,467-474)."""
        fields: dict[str, str] = {
            "Device": self.config.device,
            "Version": self.config.version,
            "Key": self.config.key,
        }
        if self.config.lang is not None:
            fields["lang"] = self.config.lang
        return fields

    def _absolute_url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _refuse_missing_dynapath(self, path: str) -> None:
        if not self.config.dynapath.enabled and path in DYNAPATH_REQUIRED_PATHS:
            raise KorailDynaPathRequiredError(
                f"KORAIL {path} 는 DynaPath 토큰을 요구합니다. "
                "KorailConfig(disable_dynapath=True) 를 빼거나, 실제 단말 "
                "값을 쓰려면 build_config_from_env() 를 넘겨야 합니다."
            )

    def _dynapath_headers(self, method: str, path: str) -> dict[str, str]:
        dynapath = self.config.dynapath
        if not dynapath.enabled:
            self._refuse_missing_dynapath(path)
            return {}
        if path not in dynapath.allowlist_paths:
            return {}
        context = DynapathRequestContext(
            method=method,
            path=path,
            url=self._absolute_url(path),
            device=self.config.device,
            version=self.config.version,
            key=self.config.key,
            user_agent=self.config.user_agent,
            device_name=dynapath.device_name,
            os_version=dynapath.os_version,
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
        return {dynapath.header_name: token}

    def _finish_read(
        self,
        send: Callable[[], httpx.Response],
        *,
        method: str,
        path: str,
        raise_on_fail: bool,
        require_envelope: bool,
    ) -> BaseKorailResponse:
        payload = _decode_response(_send(self._client, send, method=method, path=path), path=path)
        # 관측: getUUID.do 는 mutMrkVrfCd 와 strResult 만 반환합니다.
        common_out = path not in _NON_COMMON_OUT_READ_PATHS
        return parse_base_response(
            payload,
            raise_on_fail=raise_on_fail,
            require_result=require_envelope and common_out,
            common_out=common_out,
        )

    def post_form(
        self,
        path: str,
        data: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        *,
        include_common: bool = True,
        include_dynapath: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        form_encoded: bool = True,
        omit_empty_fields: bool = True,
    ) -> BaseKorailResponse:
        """``require_envelope=False`` 는 KORAIL 봉투 없는 응답용."""
        ordered_form: list[tuple[str, Any]] | None = None
        mapping_form: dict[str, Any] | None = None
        if data is not None and not isinstance(data, Mapping):
            ordered_form = []
            if include_common:
                ordered_form.extend(self.common_fields().items())
            if data:
                ordered_form.extend(data)
            if omit_empty_fields:
                ordered_form = [item for item in ordered_form if not _is_empty_string(item[1])]
        else:
            mapping_form = {}
            if include_common:
                mapping_form.update(self.common_fields())
            if data:
                mapping_form.update(data)
            if omit_empty_fields:
                mapping_form = _drop_empty(mapping_form)
        headers = {"Content-Type": "application/x-www-form-urlencoded"} if form_encoded else {}
        if include_dynapath:
            headers.update(self._dynapath_headers("POST", path))

        def send() -> httpx.Response:
            if not form_encoded:
                return self._client.post(path, headers=headers)
            if ordered_form is not None:
                return self._client.post(
                    path,
                    content=urlencode([(name, _form_value(value)) for name, value in ordered_form]).encode(
                        "ascii"
                    ),
                    headers=headers,
                )
            return self._client.post(path, data=mapping_form, headers=headers)

        return self._finish_read(
            send,
            method="POST",
            path=path,
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )

    def post_query(
        self,
        path: str,
        params: Mapping[str, Any],
        *,
        include_common: bool = True,
        include_dynapath: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        omit_empty_fields: bool = False,
    ) -> BaseKorailResponse:
        """DTO가 @QueryMap이므로 POST 본문은 비우고 URL에 실어 보냅니다(NetworkApi.java:352-353)."""
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        query.update(params)
        if omit_empty_fields:
            query = _drop_empty(query)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if include_dynapath:
            headers.update(self._dynapath_headers("POST", path))
        return self._finish_read(
            lambda: self._client.post(path, params=query, content=b"", headers=headers),
            method="POST",
            path=path,
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )

    def post_mutation_form(
        self,
        path: str,
        data: Mapping[str, Any],
        *,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """실패 판정을 꺼도 봉투 타입 검사와 P058 만료 판정은 유지합니다."""
        data = _drop_empty(data)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        headers.update(self._dynapath_headers("POST", path))
        response = _send(
            self._client,
            lambda: self._client.post(path, data=dict(data), headers=headers),
            method="POST",
            path=path,
        )
        payload = _decode_response(response, path=path)
        return parse_base_response(payload, raise_on_fail=raise_on_fail, require_result=True)

    def get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        include_common: bool = False,
        include_dynapath: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
        omit_empty_fields: bool = False,
    ) -> BaseKorailResponse:
        """``require_envelope=False`` 는 봉투 없는 응답용."""
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        if params:
            query.update(params)
        if omit_empty_fields:
            query = _drop_empty(query)
        headers = self._dynapath_headers("GET", path) if include_dynapath else {}
        return self._finish_read(
            lambda: self._client.get(path, params=query, headers=headers),
            method="GET",
            path=path,
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )
