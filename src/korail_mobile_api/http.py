# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""HTTP 전송 계층 — 폼·쿼리를 실제로 보내는 유일한 곳.

읽기(:meth:`~KorailHttpClient.post_form`, :meth:`~KorailHttpClient.get_json`)와
변경(:meth:`~KorailHttpClient.post_mutation_form`)이 완전히 갈리며 서로의 라우트에 닿을 수
없습니다. 공통 필드(``Device``/``Version``/``Key``, 그리고 호출자가
``KorailConfig.lang`` 을 채웠을 때만 ``lang``), DynaPath 헤더,
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
    # VerifyOnlineRefundsOut 도 CommonOut 을 상속하지 않고 strResult 기본값이
    # null 입니다(VerifyOnlineRefundsOut.java:97). 없는 strResult 를 실패로 읽으면
    # 성공한 검증이 실패로 분류됩니다. 삭제된 V7Gateway 가 같은 판정을
    # _NON_COMMON_OUT_RESPONSE_MODELS 로 따로 들고 있던 것을 여기로 옮겼습니다.
    "/classes/com.korail.mobile.refunds.verifyOnlineRefunds",
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


#: 7.0.6 ``DynaPathInterceptor`` 의 고정 리터럴 차단 코드 집합
#: (``DynaPathInterceptor.java:41`` ``STLhns``). 보호 경로 응답 본문의
#: 정수 필드가 이 중 하나면 차단입니다.
_DYNAPATH_BLOCK_CODES = frozenset({-1203, -1406, -2000, -8005, -8201, -8202, -8203})


def _dynapath_block_payload(payload: Any) -> dict[str, Any] | None:
    """``payload`` 에 DynaPath 차단 신호가 있으면 그 dict 를, 없으면 ``None``.

    7.0.6 ``DynaPathInterceptor.intercept()``
    (analysis/jadx/sources/com/korail/talk/network/interceptor/DynaPathInterceptor.java:97-124)
    는 HTTP 상태와 무관하게 응답 본문을 ``JSONObject`` 로 파싱하고, 정수
    필드 하나를 ``optInt(<field>, 0)`` 으로 꺼내 :data:`_DYNAPATH_BLOCK_CODES`
    에 속하면 응답을 닫고 ``DynaPathBlockedException`` 을 던집니다
    (``:113,122-124``).

    그 ``<field>`` 이름 자체는 같은 파일의 다른 상수들과 똑같이 AlienGuard
    로 난독화된 바이트 배열 리터럴로 만들어지며(``optInt`` 호출의 키 인자가
    ``listOf(TuplesKt.to(<난독 문자열A>, <난독 문자열B>)).iterator()`` 에서
    나온 ``Pair`` 의 ``first`` 입니다), 정적 분석으로 평문을 복원할 수
    없습니다. 이미 ``analysis/reports/7.0.6-compare/auth-security.md:10`` 가
    "정확한 JSON 필드명은 불명이다" 로 기록해 두었습니다 — PROTECTED.

    필드 이름을 추측해 박아 넣는 대신(그 자체로 새 UNSUPPORTED 값이 됩니다),
    최상위 키 전부를 훑어 그 정수 중 하나를 가진 키가 있는지 봅니다. 실제
    인터셉터보다 넓게 봅니다(키 하나만 읽는 대신 전부 읽음)만, 좁게 보는
    일은 없으므로 틀린 필드 이름을 골라 실제 차단을 놓치는 경우는 없습니다.
    정상 응답이 이 특정 음수 센티넬 값을 무관한 용도의 필드로 우연히 가질
    가능성은 낮다고 보고 받아들입니다.
    """
    if not isinstance(payload, dict):
        return None
    for value in payload.values():
        if isinstance(value, bool):
            continue
        if isinstance(value, int) and value in _DYNAPATH_BLOCK_CODES:
            return payload
    return None


def _raise_for_status(response: httpx.Response, *, path: str) -> None:
    if path in DYNAPATH_ALLOWLIST_PATHS:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        blocked_payload = _dynapath_block_payload(payload)
        if blocked_payload is not None:
            message = blocked_payload.get("message")
            raise KorailDynaPathError(
                str(message or "KORAIL DynaPath request rejected"),
                raw=blocked_payload,
            )
    if response.is_error:
        raise KorailTransportError(
            f"KORAIL HTTP {response.status_code} for "
            f"{response.request.method} {response.request.url.path}"
        )


def _is_empty_string(value: Any) -> bool:
    return isinstance(value, str) and value == ""


def _drop_empty(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """빈 문자열(``""``) 값을 가진 항목을 제거한 새 dict 를 돌려줍니다.

    7.0.6 ``NetworkService.java:15342`` 의 평탄화기는 ``JsonPrimitive`` 를
    문자열 길이가 0보다 클 때만 폼 맵에 담습니다 — 빈 문자열 필드는 ``key=``
    로 나가지 않고 키 자체가 사라집니다. httpx 는 그런 필터링을 하지 않으므로
    여기서 앱과 같은 모양으로 맞춥니다. ``None``, 리스트/튜플, 그 밖의 비어
    있지 않은 값은 건드리지 않습니다 — 문자열의 빈 값만입니다.
    """
    return {key: value for key, value in mapping.items() if not _is_empty_string(value)}


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
        """공통 필드 ``Device``/``Version``/``Key`` (+ 선택적 ``lang``).

        7.0.6 ``CommonIn`` 은 실제로 4번째 필드 ``lang``
        (``@SerialName(Constants.LANG)``, ``CommonIn.java:381``) 도 선언합니다.
        그 실제 값은 AppSuit 보호(``LanguageProvider.getSTLeec()``)라 추측해
        채우지 않습니다 — ``self.config.lang`` 이 ``None`` 이면(기본값)
        이 패키지의 예전 동작대로 ``lang`` 을 아예 보내지 않고, 호출자가
        실제 값을 :class:`~korail_mobile_api.config.KorailConfig` 에 넘기면
        그 값을 싣습니다.
        """
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
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
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
                # ``from_raw``, not ``BaseKorailResponse(raw=...)``: 봉투가
                # **부분적으로** 있는 응답이 있습니다. ``/ebizcross/getUUID.do``
                # 는 ``{"mutMrkVrfCd": ..., "strResult": "SUCC"}`` 를 주는데,
                # 세 키가 다 있어야 통과하는 위 조건에 걸려 예전에는 ``raw`` 만
                # 채운 객체가 나갔습니다 — 서버가 ``SUCC`` 라고 말했는데
                # ``str_result`` 는 ``None`` 이었습니다(2026-09-22 확인).
                # ``from_raw`` 는 있는 것만 그대로 옮기므로 완전한 봉투에서는
                # 동작이 같고, 없는 키에 대해 새로 예외를 내지도 않습니다.
                return BaseKorailResponse.from_raw(payload)
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
        path = assert_read_only_route("POST", path)
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
            ordered_form = [
                item for item in ordered_form if not _is_empty_string(item[1])
            ]
        else:
            mapping_form = {}
            if include_common:
                mapping_form.update(self.common_fields())
            if data:
                mapping_form.update(data)
            mapping_form = _drop_empty(mapping_form)
        if path == _RESERVATION_LIST_PATH:
            field_names = (
                {name for name, _value in ordered_form}
                if ordered_form is not None
                else set(mapping_form or {})
            )
            # ``lang`` 은 공통 필드라 빼고 비교합니다. 이 검사가 막으려는 것은
            # 같은 경로를 쓰는 **쓰기** 오버로드(applyDisabilityCertification)의
            # 필드이지, ``CommonIn`` 의 4번째 공통 필드가 아닙니다. 예전에는
            # 정확히 같은지만 봐서, ``KorailConfig(lang=...)`` 를 설정한 호출자는
            # :meth:`~korail_mobile_api.client.KorailClient.get_ticket_reservation_detail`
            # 이 서버에 닿기도 전에 ``KorailProtocolError`` 로 막혔습니다 --
            # ``lang`` 이 ``None``/``""`` 일 때만 통과했으니, 기본값을 쓰는 동안은
            # 아무도 못 보던 버그입니다(2026-09-22 재현). ``lang`` **하나만**
            # 예외이고 나머지 여분 필드는 여전히 거절합니다.
            if field_names - {"lang"} != _RESERVATION_LIST_READ_FIELDS:
                raise KorailProtocolError(
                    "KORAIL certification.ReservationList shares its path "
                    "with a write overload (applyDisabilityCertification); "
                    "the read send path only accepts the read overload's "
                    "exact fields (plus the optional common lang): "
                    + ", ".join(sorted(_RESERVATION_LIST_READ_FIELDS))
                )
        headers = (
            {"Content-Type": "application/x-www-form-urlencoded"}
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
        path = assert_read_only_route("POST", path)
        if not isinstance(params, Mapping):
            raise KorailProtocolError("KORAIL POST query params must be a mapping")
        query: dict[str, Any] = {}
        if include_common:
            query.update(self.common_fields())
        query.update(params)
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
        category: MutationCategory,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """변경 라우트로 폼을 보냅니다.

        ``assert_mutation_route`` + ``assert_mutation_route_category`` 를 모두
        통과해야 합니다.
        """
        assert_korail_origin(str(self._client.base_url))
        path = assert_mutation_route("POST", path)
        assert_mutation_route_category(path, category)
        if not isinstance(data, Mapping):
            raise KorailProtocolError(
                "KORAIL mutation form data must be a mapping"
            )
        # 7.0.6's flattener (NetworkService.java:15342) drops empty-string
        # fields rather than sending `key=`; filter before the shape guard
        # below runs so that guard sees the form the wire will actually
        # carry (and can treat any empty string that still reaches it as a
        # sign something slipped past this filter).
        data = _drop_empty(data)
        assert_mutation_form_shape(path, data)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        headers.update(self._dynapath_headers("POST", path))
        try:
            response = self._client.post(path, data=dict(data), headers=headers)
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
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
        path = assert_read_only_route("GET", path)
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
