from __future__ import annotations

import json
from typing import Any, Mapping

import httpx

from .config import KorailConfig
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
    ) -> BaseKorailResponse:
        self._assert_safe_path(path)
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        if params:
            query.update(params)
        try:
            response = self._client.get(path, params=query)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise KorailTransportError(str(exc)) from exc
        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        return parse_base_response(payload, raise_on_fail=raise_on_fail)
