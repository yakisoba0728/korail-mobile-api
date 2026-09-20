# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""HTTP 전송 계층 — 폼·쿼리를 실제로 보내는 유일한 곳.

읽기(:meth:`~KorailHttpClient.post_form`, :meth:`~KorailHttpClient.get_json`)와
변경(:meth:`~KorailHttpClient.post_mutation_form`)이 완전히 갈리며 서로의 라우트에 닿을 수
없습니다. 공통 세 필드(``Device``/``Version``/``Key``), DynaPath 헤더,
``h_msg_cd`` 판정이 여기서 붙습니다.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any
from urllib.parse import urlencode

import httpx

from .config import KorailConfig
from .constants import DYNAPATH_ALLOWLIST_PATHS, DYNAPATH_REQUIRED_PATHS
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
from .safety import (
    MutationCategory,
    assert_korail_origin,
    assert_mutation_form_shape,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)


# 7.0.6 응답 모델이 CommonOut 을 상속하지 않아 봉투 필드가 아예 없는 읽기 경로.
# StationDataOut(stationdata, EbizMaasStationList)과 StationInfoOut(stationinfo)
# 이라 strResult 가 빠져도 실패가 아닙니다.
_NON_COMMON_OUT_READ_PATHS = frozenset({
    "/classes/com.korail.mobile.common.stationdata",
    "/classes/com.korail.mobile.common.stationinfo",
    "/ebizmaas/EbizMaasStationList.do",
})

# certification.ReservationList is the one read-only path this package sends
# to that CertificationService.java also declares a WRITE Retrofit method on:
# inquiryTicketRsv (the read this package implements, exactly these four
# fields) and applyDisabilityCertification (:22, which adds txtPsgDisc0019Cnt
# and six @QueryMaps to attach a disability certificate to a held
# reservation). The general per-route field contract that used to keep the
# write shape off this send path moved into the test suite, which has since
# been deleted, so no other route is checked at all -- but for this one path
# a caller (or a future builder bug) that hands post_form the write overload's
# fields would otherwise reach the wire unexamined, since nothing else on the
# read send path is route-specific. This is the one targeted exception, not a
# reinstatement of the general contract.
_RESERVATION_LIST_PATH = "/classes/com.korail.mobile.certification.ReservationList"
_RESERVATION_LIST_READ_FIELDS = frozenset({"Device", "Version", "Key", "hidPnrNo"})

#: ``parse_base_response`` 가 값 판정 전에 타입을 확인하는 세 봉투 필드.
_ENVELOPE_STRING_FIELDS = ("h_msg_cd", "h_msg_txt", "strResult")


def _reject_non_string_envelope_fields(data: dict[str, Any]) -> None:
    """봉투 필드가 있으면 문자열이거나 ``null`` 이어야 합니다.

    ``errors.classify_app_error`` 는 ``h_msg_cd`` 로 dict 조회를 하고,
    ``read_parsers._validate_envelope`` 는 같은 값으로 frozenset 멤버십을
    검사합니다. 둘 다 리스트·객체가 오면 ``TypeError`` 로 죽습니다 — 이 패키지가
    올려야 할 :class:`~korail_mobile_api.errors.KorailProtocolError` 대신.
    ``BaseKorailResponse.from_raw`` 는 일부러 이 판정을 하지 않으므로(문서화된
    대로 호출자 몫), 값을 실제로 쓰는 이 함수가 판정보다 먼저 검사합니다.
    """
    invalid = [
        name
        for name in _ENVELOPE_STRING_FIELDS
        if name in data and data[name] is not None and not isinstance(data[name], str)
    ]
    if invalid:
        raise KorailProtocolError(
            "KORAIL response envelope fields must be strings or null: "
            f"{', '.join(invalid)}"
        )


def parse_base_response(
    data: Any,
    *,
    raise_on_fail: bool = True,
    require_result: bool = True,
) -> BaseKorailResponse:
    """응답 봉투를 검사합니다.

    ``P058`` → :class:`~korail_mobile_api.errors.KorailSessionExpiredError`.
    ``strResult == "FAIL"`` 또는 ``h_msg_cd == "WRC000288"`` 이면 실패입니다
    (``BaseActivity.java:620``). ``require_result`` 가 참(기본)이면 ``strResult``
    키가 아예 없는 응답도 실패입니다. 7.0.6 ``CommonOut`` 은 빠진 ``strResult`` 를
    ``commonFail()`` 이 비교하는 바로 그 보호 상수로 채웁니다
    (``analysis/jadx/sources/com/korail/talk/network/model/CommonOut.java:361,455-462``).
    ``CommonOut`` 을 상속하지 않는 응답을 받는 호출자만 ``False`` 를 넘깁니다.
    """
    if not isinstance(data, dict):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    _reject_non_string_envelope_fields(data)
    response = BaseKorailResponse.from_raw(data)
    if response.h_msg_cd == SESSION_EXPIRED_CODE:
        raise KorailSessionExpiredError(
            response.h_msg_cd,
            response.h_msg_txt,
            raw=data,
        )
    if raise_on_fail and (
        response.str_result == "FAIL"
        or response.h_msg_cd == "WRC000288"
        or (require_result and "strResult" not in data)
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


def _finish_mutation(
    response: httpx.Response,
    *,
    path: str,
    raise_on_fail: bool,
) -> BaseKorailResponse:
    """The end of post_mutation_form: status, JSON and the envelope.

    The mutation sender only, and separate from the read senders' tail on
    purpose. The envelope is never relaxed here: every mutation route answers
    with a CommonOut, so a missing strResult is a failure.
    """
    _raise_for_status(response, path=path)
    try:
        payload = response.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
    return parse_base_response(payload, raise_on_fail=raise_on_fail, require_result=True)


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

    def _refuse_missing_dynapath(self, path: str) -> None:
        if not self.config.dynapath.enabled and path in DYNAPATH_REQUIRED_PATHS:
            raise KorailDynaPathRequiredError(
                f"KORAIL {path} 는 DynaPath 토큰을 요구합니다. "
                "KorailConfig(enable_dynapath=True) 로 켜거나, 실제 단말 "
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
        if not token:
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
        """The end of every read: send, then status, JSON and the envelope.

        Read senders only. The mutation sender keeps its own tail, which
        never relaxes the envelope.
        """
        try:
            response = send()
        except httpx.HTTPError as exc:
            raise KorailTransportError(
                f"KORAIL transport failed for {method} {path}"
            ) from exc
        _raise_for_status(response, path=path)
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise KorailProtocolError("KORAIL response body was not valid JSON") from exc
        if not require_envelope:
            if not isinstance(payload, dict):
                raise KorailProtocolError("KORAIL response must be a JSON object")
            if not all(name in payload for name in ("h_msg_cd", "h_msg_txt", "strResult")):
                return BaseKorailResponse(raw=payload)
        return parse_base_response(
            payload,
            raise_on_fail=raise_on_fail,
            require_result=path not in _NON_COMMON_OUT_READ_PATHS,
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
    ) -> BaseKorailResponse:
        """읽기 라우트에 폼을 POST 합니다.

        ``data`` 는 매핑이거나 순서 있는 ``(이름, 값)`` 시퀀스.
        ``require_envelope=False`` 는 KORAIL 봉투 없는 응답용.
        """
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("POST", path)
        if include_dynapath:
            self._refuse_missing_dynapath(path)
        if data is not None and not isinstance(data, (Mapping, Sequence)):
            raise KorailProtocolError(
                "KORAIL form data must be a mapping or registered ordered sequence"
            )
        if not form_encoded and (include_common or data):
            raise KorailProtocolError(
                "KORAIL empty POST must not contain common or form fields"
            )
        ordered_form: list[tuple[str, Any]] | None = None
        mapping_form: dict[str, Any] | None = None
        if data is not None and not isinstance(data, Mapping):
            ordered_form = []
            if include_common:
                ordered_form.extend(self.common_fields().items())
            if data:
                ordered_form.extend(data)
        else:
            mapping_form = {}
            if include_common:
                mapping_form.update(self.common_fields())
            if data:
                mapping_form.update(data)
        if path == _RESERVATION_LIST_PATH:
            field_names = (
                {name for name, _value in ordered_form}
                if ordered_form is not None
                else set(mapping_form or {})
            )
            if field_names != _RESERVATION_LIST_READ_FIELDS:
                raise KorailProtocolError(
                    "KORAIL certification.ReservationList shares its path "
                    "with a write overload (applyDisabilityCertification); "
                    "the read send path only accepts the read overload's "
                    "exact fields: " + ", ".join(sorted(_RESERVATION_LIST_READ_FIELDS))
                )
        headers = (
            {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
            if form_encoded
            else {}
        )
        if include_dynapath:
            headers.update(self._dynapath_headers("POST", path))

        def send() -> httpx.Response:
            if not form_encoded:
                return self._client.post(path, headers=headers)
            if ordered_form is not None:
                return self._client.post(
                    path,
                    content=urlencode(ordered_form).encode("ascii"),
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
    ) -> BaseKorailResponse:
        """Send the 7.0.6 delay-discount POST ``@QueryMap`` request.

        APK ``NetworkApi.postDelayDiscountView`` combines
        ``@FormUrlEncoded`` and ``@QueryMap``. This reproduces the declared
        URL position with an empty form body. Its runtime acceptance cannot
        be inferred from the annotation alone.
        """
        if path != "/classes/com.korail.mobile.passCard.DelayDiscountView":
            raise KorailProtocolError(
                "KORAIL POST query maps are registered only for DelayDiscountView"
            )
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("POST", path)
        if not isinstance(params, Mapping):
            raise KorailProtocolError("KORAIL POST query params must be a mapping")
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        query.update(params)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
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
        category: MutationCategory,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """변경 라우트로 폼을 보냅니다.

        ``assert_mutation_route`` + ``assert_mutation_route_category`` 를 모두
        통과해야 합니다.
        """
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
        return _finish_mutation(response, path=path, raise_on_fail=raise_on_fail)

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
        headers = (
            self._dynapath_headers("GET", path)
            if include_dynapath
            else {}
        )
        return self._finish_read(
            lambda: self._client.get(path, params=query, headers=headers),
            method="GET",
            path=path,
            raise_on_fail=raise_on_fail,
            require_envelope=require_envelope,
        )
