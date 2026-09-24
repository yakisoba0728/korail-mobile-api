# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""KORAIL API를 전송하고 공통 필드와 응답 봉투를 처리합니다. config.base_url은 검사하지 않으며 라우트는 호출부가 선택합니다. 공통 필드는 호출 옵션에 따라 주입하고, lang은
KorailConfig.lang이 설정된 경우에만 붙입니다. 대기열 전송은 netfunnel 모듈이 담당합니다."""

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
# StationInfoOut(stationinfo). 이 경로라도 존재하는 봉투 필드는 보존합니다.
_NON_COMMON_OUT_READ_PATHS = frozenset(
    {
        "/classes/com.korail.mobile.common.stationdata",
        "/classes/com.korail.mobile.common.stationinfo",
        "/ebizmaas/EbizMaasStationList.do",
        # VerifyOnlineRefundsOut.java:29 는 CommonOut 을 상속하지 않습니다. strResult 누락 기본값(:91-94)은 null 이 아니라
        # 보호 문자열입니다. 이 경로는 봉투 키 누락을 허용하되 존재하는 필드는 보존합니다.
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
    """봉투 타입 검사 후 FAIL/P058 을 세션 만료로 처리합니다.

    CommonOut 의 strResult 누락은 실패 기본값입니다(CommonOut.java:361,455-463). 앱의 CommonOut.checkRequiredLogin() 은
    commonFail()(strResult 실패)이 참일 때만 hMsgCd 를 보호된 4바이트 리터럴과 비교합니다(CommonOut.java:426-438). 그래서 성공 봉투에 붙은 P058 은
    만료가 아닙니다.

    raise_on_fail=True 면 FAIL 또는 require_result=True 일 때 strResult 키 누락을 거절합니다. SUCC 와의 동등 비교는 아니며
    null·빈 문자열·미지의 결과값은 이 단계에서 거절하지 않습니다. 앱은 CommonOut.java:361,455-463 에서 기본값과 실패 비교에 같은 보호 리터럴을 사용합니다.
    FAIL 평문은 관측값입니다. 문자열 필드의 JSON 정수는 2026-09-21 관측에 따라 문자열로 읽되 raw 는 바꾸지 않습니다.

    common_out(기본값은 require_result)이 참이면 strResult 누락도 P058 판정에서는 실패로 봅니다. 봉투가 선택인 CommonOut 읽기 경로용입니다: 앱은
    CommonOut 이면 checkRequiredLogin 을 부르지만(NetworkService.java:6916-6919) 그 밖의 코드는 화면마다 다르게 다루므로, 이 경우 다른 코드는
    거절하지 않습니다."""
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
    """최상위 JSON 값에서 차단 정수 코드를 찾습니다.

    앱 근거: DynaPathInterceptor.java:97-124. 앱의 검사 키는 보호돼 있어 이 구현은 모든 키를 봅니다. 따라서 다른 필드의 같은 값도 차단으로 오인할 수 있습니다. 앱
    optInt 의 모든 변환까지 동일하게 재현한다는 보장은 없습니다."""
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
    # 닫힌 httpx 클라이언트는 RuntimeError 를 내므로 KorailApiError 계층으로 바꿉니다. 이때 요청은 나가지 않았습니다.
    if client.is_closed:
        raise KorailProtocolError(f"KORAIL client is closed; {method} {path} was not sent")
    try:
        return send()
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        raise KorailTransportError(f"KORAIL transport failed for {method} {path}") from exc


def _decode_response(response: httpx.Response, *, path: str) -> Any:
    """본문을 한 번만 해석합니다. 판정 순서: DynaPath 차단(보호 경로, 상태 코드와 무관) → 2xx 가 아닌 상태 → JSON 오류."""
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
    """빈 문자열 필드만 생략합니다. None·다른 값은 바꾸지 않습니다.

    앱의 평탄화기 근거: NetworkService.java:15342. key= 로 보내는 것과 구분해야 합니다."""
    return {key: value for key, value in mapping.items() if not _is_empty_string(value)}


def _form_value(value: Any) -> str:
    """순서 있는 폼 값을 httpx 의 data= 인코딩과 같게 씁니다. None 은 빈 값, bool 은 true/false 입니다."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class KorailHttpClient:
    """설정된 API 서버에 요청을 보내고 응답 봉투를 판정합니다. ``base_url`` 은 검사하지 않습니다."""

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
        """세션 쿠키를 저장하는 쿠키 저장소를 반환합니다."""
        return self._client.cookies

    def close(self) -> None:
        """HTTP 연결을 닫습니다."""
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        """Device/Version/Key 와 설정된 lang 을 만듭니다.

        lang 선언: CommonIn.java:381. LanguageProvider 가 주는 실제 값은 보호돼 있어 config.lang=None 이면 추측하지 않고 생략합니다."""
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
        """읽기 응답을 처리합니다. require_envelope 및 경로별 봉투 생략 규칙에 따릅니다."""
        payload = _decode_response(_send(self._client, send, method=method, path=path), path=path)
        # 2026-09-22 관측: getUUID.do 는 mutMrkVrfCd 와 strResult 만 반환합니다. 봉투 누락 허용과 존재하는 FAIL/P058 판정은 별개이며 raw 는
        # 그대로 보존합니다.
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
        """읽기 라우트에 폼을 POST 합니다.

        ``data`` 는 매핑이거나 순서 있는 ``(이름, 값)`` 시퀀스. ``require_envelope=False`` 는 KORAIL 봉투 없는 응답용."""
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
        """지연할인권 조회 조건을 POST 요청의 URL 쿼리로 보냅니다. 폼 본문은 비어 있습니다. NetworkApi.java:352-353의 @FormUrlEncoded·@QueryMap
        조합이며, 2026-09-24에는 이 방식으로 할인권 0행 응답을 확인했습니다. 할인권이 있는 응답까지 검증된 것은 아닙니다."""
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
        """공통 필드까지 완성된 변경 폼을 전송합니다.

        strResult 를 요구하며 raise_on_fail=False 는 실패 판정만 완화합니다. 봉투 타입 검사와 P058 처리는 그대로입니다."""
        # 빈 문자열 생략 규칙과 근거는 _drop_empty 참고.
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
        """읽기 라우트에 GET 합니다.

        ``include_common`` 기본 ``False`` — GET 라우트 대부분이 공통 필드 불필요. ``require_envelope=False`` 는 봉투 없는 응답용."""
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
