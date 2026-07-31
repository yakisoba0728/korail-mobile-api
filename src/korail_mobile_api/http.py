"""HTTP 전송 계층 — 폼·쿼리를 실제로 보내는 유일한 곳.

읽기(:meth:`~KorailHttpClient.post_form`, :meth:`~KorailHttpClient.get_json`)와
변경(:meth:`~KorailHttpClient.post_mutation_form`,
:meth:`~KorailHttpClient.get_mutation_query`)이 완전히 갈리며 서로의 라우트에 닿을 수
없습니다. 공통 세 필드(``Device``/``Version``/``Key``), DynaPath 헤더,
``h_msg_cd`` 판정이 여기서 붙습니다.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import KorailConfig
from .consent import (
    MutationCategory,
    MutationConsent,
    require_mutation_consent,
)
from .constants import DYNAPATH_ALLOWLIST_PATHS, DYNAPATH_REQUIRED_PATHS
from .dynapath import DynapathRequestContext, DynapathTokenGenerator
from .errors import (
    KorailDynaPathError,
    KorailDynaPathRequiredError,
    KorailMutationNotAllowedError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
    classify_app_error,
)
from .models import BaseKorailResponse
from .safety import (
    KORAIL_CARD_BEARING_MUTATION_CATEGORIES,
    assert_korail_origin,
    assert_mutation_form_shape,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_request_fields,
    assert_read_only_route,
)


def parse_base_response(data: Any, *, raise_on_fail: bool = True) -> BaseKorailResponse:
    """응답 봉투를 검사합니다.

    ``P058`` → :class:`~korail_mobile_api.errors.KorailSessionExpiredError`.
    실패 판정은 앱과 같음(``BaseActivity.java:620``): ``strResult == "FAIL"`` 또는
    ``h_msg_cd == "WRC000288"`` 일 때만 실패.
    """
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    response = BaseKorailResponse.from_raw(data)
    if response.h_msg_cd == "P058":
        raise KorailSessionExpiredError(
            response.h_msg_cd,
            response.h_msg_txt,
            raw=data,
        )
    if raise_on_fail and (
        response.str_result == "FAIL"
        or response.h_msg_cd == "WRC000288"
    ):
        raise classify_app_error(
            response.h_msg_cd,
            response.h_msg_txt,
            raw=data,
        )
    return response


def _raise_for_status(response: httpx.Response, *, path: str) -> None:
    dynapath_result = response.headers.get("DynaPath-Result")
    try:
        dynapath_rejected = (
            dynapath_result is not None and int(dynapath_result) < 0
        )
    except ValueError:
        dynapath_rejected = False
    if (
        response.status_code == 403
        and path in DYNAPATH_ALLOWLIST_PATHS
        and dynapath_rejected
    ):
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        message = payload.get("message") if isinstance(payload, dict) else None
        raise KorailDynaPathError(
            str(message or "KORAIL DynaPath request rejected"),
            raw=payload,
        )
    if response.is_error:
        raise KorailTransportError(
            f"KORAIL HTTP {response.status_code} for "
            f"{response.request.method} {response.request.url.path}"
        )


class KorailHttpClient:
    """KORAIL API 호스트에 고정된 HTTP 클라이언트.

    ``assert_korail_origin`` 이 ``config.base_url`` 을
    ``https://smart.letskorail.com`` 으로 못 박습니다.
    """

    def __init__(
        self,
        config: KorailConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        assert_korail_origin(config.base_url)
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
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={"User-Agent": config.user_agent, "Connection": "close"},
            transport=transport,
        )

    @property
    def cookies(self) -> httpx.Cookies:
        """``JSESSIONID`` 가 담기는 쿠키 저장소."""
        return self._client.cookies

    def close(self) -> None:
        """HTTP 연결을 닫습니다."""
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        """공통 세 필드 ``Device``/``Version``/``Key``."""
        return {
            "Device": self.config.device,
            "Version": self.config.version,
            "Key": self.config.key,
        }

    def _absolute_url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _dynapath_headers(self, method: str, path: str) -> dict[str, str]:
        dynapath = self.config.dynapath
        if not dynapath.enabled:
            if path in DYNAPATH_REQUIRED_PATHS:
                raise KorailDynaPathRequiredError(
                    f"KORAIL {path} 는 DynaPath 토큰을 요구합니다. "
                    "KorailConfig(enable_dynapath=True) 로 켜거나, 실제 단말 "
                    "값을 쓰려면 build_config_from_env() 를 넘겨야 합니다."
                )
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
        if not token:
            return {}
        return {dynapath.header_name: token}

    def post_form(
        self,
        path: str,
        data: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        *,
        include_common: bool = True,
        include_dynapath: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
    ) -> BaseKorailResponse:
        """읽기 라우트에 폼을 POST 합니다.

        ``data`` 는 매핑이거나 순서 있는 ``(이름, 값)`` 시퀀스.
        ``require_envelope=False`` 는 KORAIL 봉투 없는 응답용.
        """
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("POST", path)
        if data is not None and not isinstance(data, (Mapping, Sequence)):
            raise KorailProtocolError(
                "KORAIL form data must be a mapping or registered ordered sequence"
            )
        if not include_common and data is not None:
            assert_read_only_request_fields(path, data)
        ordered_form: list[tuple[str, Any]] | None = None
        mapping_form: dict[str, Any] | None = None
        if data is not None and not isinstance(data, Mapping):
            ordered_form = []
            if include_common:
                ordered_form.extend(self.common_fields().items())
            if data:
                ordered_form.extend(data)
            assert_read_only_request_fields(path, ordered_form)
        else:
            mapping_form = {}
            if include_common:
                mapping_form.update(self.common_fields())
            if data:
                mapping_form.update(data)
            assert_read_only_request_fields(path, mapping_form)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        if include_dynapath:
            headers.update(self._dynapath_headers("POST", path))
        try:
            if ordered_form is not None:
                response = self._client.post(
                    path,
                    content=urlencode(ordered_form).encode("ascii"),
                    headers=headers,
                )
            else:
                response = self._client.post(
                    path, data=mapping_form, headers=headers
                )
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL transport failed for POST {path}"
            ) from exc
        _raise_for_status(response, path=path)
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        if not require_envelope:
            if not isinstance(payload, dict):
                raise KorailProtocolError(
                    "KORAIL response must be a JSON object"
                )
            if all(
                name in payload
                for name in ("h_msg_cd", "h_msg_txt", "strResult")
            ):
                return parse_base_response(
                    payload,
                    raise_on_fail=raise_on_fail,
                )
            return BaseKorailResponse(raw=payload)
        return parse_base_response(payload, raise_on_fail=raise_on_fail)

    def post_mutation_form(
        self,
        path: str,
        data: Mapping[str, Any],
        *,
        consent: MutationConsent,
        category: MutationCategory,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """변경 라우트로 폼을 보냅니다.

        ``require_mutation_consent`` + ``consent.dry_run=False`` +
        ``assert_mutation_route`` + ``assert_mutation_route_category`` 를 모두
        통과해야 합니다. 카드 보유 범주는 추가로
        ``fake_card_only``/``real_card_acknowledged`` 중 정확히 하나를 요구합니다.
        """
        require_mutation_consent(consent, category)
        if consent.dry_run:
            raise KorailMutationNotAllowedError(
                "post_mutation_form requires consent.dry_run=False; a dry-run "
                "preview must never be transmitted"
            )
        if category in KORAIL_CARD_BEARING_MUTATION_CATEGORIES:
            if consent.fake_card_only and consent.real_card_acknowledged:
                raise KorailMutationNotAllowedError(
                    "payment mutations refuse a contradictory consent: "
                    "fake_card_only=True claims a non-chargeable test card "
                    "while real_card_acknowledged=True acknowledges a real "
                    "charge; set exactly one"
                )
            if not consent.fake_card_only and not consent.real_card_acknowledged:
                raise KorailMutationNotAllowedError(
                    "payment mutations require consent.fake_card_only=True (a "
                    "non-chargeable test card) or "
                    "consent.real_card_acknowledged=True (an acknowledged real "
                    "charge); the PAN is transmitted in the clear, so an "
                    "unstated card kind is never sent"
                )
        assert_korail_origin(str(self._client.base_url))
        assert_mutation_route("POST", path)
        assert_mutation_route_category(path, category)
        if not isinstance(data, Mapping):
            raise KorailProtocolError(
                "KORAIL mutation form data must be a mapping"
            )
        assert_mutation_form_shape(path, data)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        headers.update(self._dynapath_headers("POST", path))
        try:
            response = self._client.post(path, data=dict(data), headers=headers)
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL transport failed for POST {path}"
            ) from exc
        _raise_for_status(response, path=path)
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise KorailProtocolError(
                "KORAIL response body was not valid JSON"
            ) from exc
        return parse_base_response(payload, raise_on_fail=raise_on_fail)

    def get_mutation_query(
        self,
        path: str,
        params: Mapping[str, Any],
        *,
        consent: MutationConsent,
        category: MutationCategory,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """:meth:`post_mutation_form` 의 GET 판(``reservation.dcntCrdExtn.do``).

        동일한 게이트 적용. 카드 분기 없음.
        """
        require_mutation_consent(consent, category)
        if consent.dry_run:
            raise KorailMutationNotAllowedError(
                "get_mutation_query requires consent.dry_run=False; a dry-run "
                "preview must never be transmitted"
            )
        assert_korail_origin(str(self._client.base_url))
        assert_mutation_route("GET", path)
        assert_mutation_route_category(path, category)
        if not isinstance(params, Mapping):
            raise KorailProtocolError(
                "KORAIL mutation query params must be a mapping"
            )
        assert_mutation_form_shape(path, params)
        headers = self._dynapath_headers("GET", path)
        try:
            response = self._client.get(
                path,
                params=dict(params),
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL transport failed for GET {path}"
            ) from exc
        _raise_for_status(response, path=path)
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise KorailProtocolError(
                "KORAIL response body was not valid JSON"
            ) from exc
        return parse_base_response(payload, raise_on_fail=raise_on_fail)

    def get_json(
        self,
        path: str,
        params: Mapping[str, Any] | None = None,
        *,
        include_common: bool = False,
        include_dynapath: bool = True,
        raise_on_fail: bool = True,
        require_envelope: bool = True,
    ) -> BaseKorailResponse:
        """읽기 라우트에 GET 합니다.

        ``include_common`` 기본 ``False`` — GET 라우트 대부분이 공통 필드 불필요.
        ``require_envelope=False`` 는 봉투 없는 응답용.
        """
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("GET", path)
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        if params:
            query.update(params)
        assert_read_only_request_fields(path, query)
        headers = (
            self._dynapath_headers("GET", path)
            if include_dynapath
            else {}
        )
        try:
            response = self._client.get(path, params=query, headers=headers)
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL transport failed for GET {path}"
            ) from exc
        _raise_for_status(response, path=path)
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        if not require_envelope:
            if not isinstance(payload, dict):
                raise KorailProtocolError("KORAIL response must be a JSON object")
            if all(
                key in payload
                for key in ("h_msg_cd", "h_msg_txt", "strResult")
            ):
                return parse_base_response(
                    payload,
                    raise_on_fail=raise_on_fail,
                )
            return BaseKorailResponse(raw=payload)
        return parse_base_response(payload, raise_on_fail=raise_on_fail)
