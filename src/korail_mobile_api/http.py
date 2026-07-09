from __future__ import annotations

import json
from typing import Any, Mapping

import httpx

from .config import KorailConfig
from .dynapath import DynapathRequestContext
from .errors import KorailAppError, KorailProtocolError, KorailTransportError
from .models import BaseKorailResponse
from .safety import EXCLUDED_API_DOMAINS


def parse_base_response(data: Any, *, raise_on_fail: bool = True) -> BaseKorailResponse:
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    response = BaseKorailResponse.from_raw(data)
    if raise_on_fail and response.str_result == "FAIL":
        raise KorailAppError(response.h_msg_cd, response.h_msg_txt, raw=data)
    return response


class KorailHttpClient:
    def __init__(self, config: KorailConfig, *, transport: httpx.BaseTransport | None = None) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"User-Agent": config.user_agent},
            transport=transport,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        return self._client.cookies

    def close(self) -> None:
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        return {"Device": self.config.device, "Version": self.config.version, "Key": self.config.key}

    def _absolute_url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _dynapath_headers(self, method: str, path: str) -> dict[str, str]:
        dynapath = self.config.dynapath
        if not dynapath.enabled or dynapath.token_provider is None:
            return {}
        if not any(allowlisted in path for allowlisted in dynapath.allowlist_paths):
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
            token = dynapath.token_provider(context)
        except Exception as exc:
            raise KorailProtocolError("KORAIL DynaPath token provider failed") from exc
        if not token:
            return {}
        return {dynapath.header_name: token}

    def _assert_safe_path(self, path: str) -> None:
        lowered_path = path.lower()
        for domain in EXCLUDED_API_DOMAINS:
            if domain in lowered_path:
                raise KorailProtocolError(f"KORAIL path is excluded by MVP safety policy: {path}")

    def post_form(
        self,
        path: str,
        data: Mapping[str, Any] | None = None,
        *,
        include_common: bool = True,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        self._assert_safe_path(path)
        form: dict[str, Any] = {}
        if include_common:
            form.update(self.common_fields())
        if data:
            form.update(data)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        headers.update(self._dynapath_headers("POST", path))
        try:
            response = self._client.post(path, data=form, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KorailTransportError(str(exc)) from exc
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        return parse_base_response(payload, raise_on_fail=raise_on_fail)

    def get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        include_common: bool = False,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
    ) -> BaseKorailResponse:
        self._assert_safe_path(path)
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        if params:
            query.update(params)
        headers = self._dynapath_headers("GET", path)
        try:
            response = self._client.get(path, params=query, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KorailTransportError(str(exc)) from exc
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        if not require_envelope:
            if not isinstance(payload, dict):
                raise KorailProtocolError("KORAIL response must be a JSON object")
            return BaseKorailResponse(raw=payload)
        return parse_base_response(payload, raise_on_fail=raise_on_fail)
