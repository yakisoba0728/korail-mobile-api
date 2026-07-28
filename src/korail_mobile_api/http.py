"""HTTP 전송 계층 — 폼·쿼리를 실제로 보내는 유일한 곳.

:class:`KorailHttpClient` 하나가 읽기와 변경을 서로 다른 메서드로 가릅니다.
:meth:`~KorailHttpClient.post_form` 과 :meth:`~KorailHttpClient.get_json` 은 읽기
라우트만, :meth:`~KorailHttpClient.post_mutation_form` 과
:meth:`~KorailHttpClient.get_mutation_query` 는 변경 라우트만 갈 수 있고, 어느 쪽도
상대의 라우트에 닿지 못합니다. 그 제한은 :mod:`korail_mobile_api.safety` 의 단언으로
걸립니다.

여기서 붙는 것은 공통 세 필드(``Device``/``Version``/``Key``), 필요한 경로의 DynaPath
헤더, 그리고 응답의 ``h_msg_cd`` 판정(:func:`parse_base_response` →
:func:`~korail_mobile_api.errors.classify_app_error`)입니다. 응답을 모델로 바꾸는 일은
하지 않습니다 — 그것은 파서의 몫입니다.
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
    """응답 봉투를 검사하고 실패면 알맞은 예외로 바꿉니다.

    ``h_msg_cd`` 가 ``P058`` 이면 세션 만료라
    :class:`~korail_mobile_api.errors.KorailSessionExpiredError` 입니다.

    실패 판정은 앱과 같습니다 — ``strResult == "FAIL"`` 또는 ``h_msg_cd == "WRC000288"``
    일 때만 실패이고(``BaseActivity.java:620``, ``:629`` 에서 그 밖의 코드는 성공으로
    떨어집니다), :func:`~korail_mobile_api.errors.classify_app_error` 는 그 실패가 어느
    :class:`~korail_mobile_api.errors.KorailAppError` 하위 클래스인지만 고릅니다. 그래서
    경고 코드를 실은 성공 응답은 그대로 돌아옵니다.

    ``raise_on_fail=False`` 면 실패도 예외로 만들지 않고 봉투를 돌려줍니다. 로그아웃처럼
    실패가 의미 없는 호출이 씁니다.
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
        # The FAIL/WRC000288 gate above is unchanged and remains the ONLY thing
        # that decides there is a failure at all -- exactly as the app decides it
        # (BaseActivity.java:620, with any unrecognised code on a non-FAIL
        # response falling through to success at :629). classify_app_error only
        # picks which KorailAppError subclass describes the failure, so a
        # success carrying a warning code (WRR664296) still returns normally.
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
    """KORAIL API 호스트 하나에 고정된 HTTP 클라이언트.

    생성 시점에 ``assert_korail_origin`` 이 ``config.base_url`` 을
    ``https://smart.letskorail.com`` 으로 못 박으므로, 다른 호스트를 가리키는 설정은 소켓이
    생기기 전에 거부됩니다. 대기열 호스트는 여기로 닿을 수 없고
    :class:`~korail_mobile_api.netfunnel.KorailNetFunnelClient` 를 씁니다.

    전송 메서드가 넷이고 읽기와 변경이 완전히 갈립니다 — :meth:`post_form` 과
    :meth:`get_json` 은 읽기 라우트만, :meth:`post_mutation_form` 과
    :meth:`get_mutation_query` 는 변경 라우트만 갑니다.

    DynaPath 토큰은 설정이 켜져 있고 경로가 allowlist 에 있을 때만 붙습니다. 토큰 생성이
    실패하면 헤더 없이 보내는 대신
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
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
        """밑에 깔린 httpx 클라이언트의 쿠키 저장소. ``JSESSIONID`` 가 여기 삽니다."""
        return self._client.cookies

    def close(self) -> None:
        """HTTP 연결을 닫습니다."""
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        """모든 요청에 실리는 공통 세 필드 ``Device``/``Version``/``Key``."""
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
                # 조용히 헤더를 빼면 서버가 대신 거절하는데, 그 거절이 사용자
                # 문구로는 "앱을 최신 버전으로 업데이트하라"로 위장돼 온다.
                # 설정 문제를 버전 문제로 오진하게 만드는 자리라, 보내기 전에
                # 무엇을 켜야 하는지 말하고 끝낸다.
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
        """읽기 라우트에 폼을 POST 하고 봉투를 돌려줍니다.

        라우트는 :data:`~korail_mobile_api.safety.KORAIL_READ_ONLY_ROUTES` 의 원소여야
        합니다. 변경 라우트는 여기서 거부되며 전용 문(:meth:`post_mutation_form`)으로만
        나갑니다.

        ``data`` 는 매핑이거나 순서 있는 ``(이름, 값)`` 시퀀스입니다. 순서 있는 형태는 같은
        키가 여러 번 나오는 폼(원표 조회 등)을 위한 것입니다.

        ``include_common=False`` 면 공통 세 필드를 붙이지 않습니다. 대신 그때는 ``data`` 가
        그 라우트의 정확한 필드 계약을 통과해야 합니다
        (:func:`~korail_mobile_api.safety.assert_read_only_request_fields`).

        ``require_envelope=False`` 는 KORAIL 봉투가 없는 캐시 파일용입니다. 봉투 세 필드가
        모두 있으면 평소대로 판정하고, 없으면 원본만 실은
        :class:`~korail_mobile_api.models.BaseKorailResponse` 를 돌려줍니다.
        """
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("POST", path)
        if data is not None and not isinstance(data, (Mapping, Sequence)):
            raise KorailProtocolError(
                "KORAIL form data must be a mapping or registered ordered sequence"
            )
        if not include_common and data is not None:
            assert_read_only_request_fields(path, data)
        # The ordered and mapping paths carry different form types, so each
        # branch builds its own concretely typed container.
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
        """상태를 바꾸는 폼을 근거가 확인된 변경 라우트로 보냅니다.

        변경 라우트로 전송하는 **유일한** 메서드이며 이중으로 잠겨 있습니다. ``category`` 에
        대한 ``require_mutation_consent`` 가 통과해야 하고, ``consent.dry_run`` 이 ``False``
        여야 하며(미리보기는 네트워크에 닿지 않습니다), ``assert_mutation_route`` 가 대상을
        :data:`~korail_mobile_api.safety.KORAIL_MUTATION_ROUTES` 로 제한합니다. 읽기
        경로(:meth:`post_form`)는 이 라우트들을 여전히 거부하므로 변경은 이 문으로만 프로세스를
        떠납니다. ``data`` 는 그대로 전송됩니다(예약·취소 빌더가 공통 Device/Version/Key
        필드를 이미 넣습니다). 읽기 쪽 필드 허용목록은 적용되지 않습니다.

        :data:`~korail_mobile_api.safety.KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 범주의
        전송은 카드번호를 평문으로 싣기 때문에 한 겹 더 잠깁니다 — consent 가
        ``fake_card_only=True``(청구되지 않는 테스트 카드)와
        ``real_card_acknowledged=True``(실제 청구 인지) 중 정확히 하나를 켜야 합니다.
        둘 다 꺼짐도, 둘 다 켜짐도 거부입니다.
        """
        require_mutation_consent(consent, category)
        if consent.dry_run:
            raise KorailMutationNotAllowedError(
                "post_mutation_form requires consent.dry_run=False; a dry-run "
                "preview must never be transmitted"
            )
        # Defense-in-depth at the transmit boundary: a payment carries the PAN
        # in the clear, so the send gate itself refuses to transmit one unless
        # the consent states, unambiguously, WHICH kind of card it is. Exactly
        # one of the two claims must hold:
        #
        #   fake_card_only=True        -> a non-chargeable test card (default)
        #   real_card_acknowledged=True -> a real card, money will move
        #
        # Neither set is the historical refusal, unchanged. BOTH set is a
        # contradiction -- the consent simultaneously claims a test card and
        # acknowledges a real charge -- and is refused rather than resolved,
        # because sending a payment on an ambiguous consent is precisely the
        # mistake this gate exists to prevent. This keeps the invariant at the
        # layer that actually sends, not only in the public payment methods.
        #
        # Keyed on MEMBERSHIP of the card-bearing set rather than on the single
        # literal "payment": which product a category owns and whether its forms
        # carry a PAN are different questions, and a second card-bearing
        # category must not slip past a gate that only knows the first one's
        # name.
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
        """:meth:`post_mutation_form` 의 GET 판. 앱이 GET 으로 수행하는 변경에 씁니다.

        그런 라우트는 현재 하나뿐입니다 — ``reservation.dcntCrdExtn.do``. ``@GET`` 에
        ``@Query`` 일곱 개로 선언돼 있고(``ResearchService.java:65-66``) 실제로 상태를
        바꿉니다. 할인카드의 유효기간을 연장합니다. POST 로 등록해
        :meth:`post_mutation_form` 에 태우면 허용목록이 앱과 다른 메서드를 기록하게 되므로
        그렇게 하지 않았습니다.

        :meth:`post_mutation_form` 의 모든 게이트가 그대로 적용됩니다 — ``category`` 에 대한
        ``require_mutation_consent``, ``dry_run=True`` 거부, 정확한 ``(method, path)`` 쌍에
        대한 :func:`~korail_mobile_api.safety.assert_mutation_route`, 범주 교차를 막는
        :func:`~korail_mobile_api.safety.assert_mutation_route_category`, 나가는 값에 대한
        :func:`~korail_mobile_api.safety.assert_mutation_form_shape`. 마지막 것까지 거는
        이유는 이 라우트의 쿼리도 ``_common_fields`` 에 네 필드를 더한 것이라 POST 본문과
        구조가 같기 때문입니다. 읽기 경로(:meth:`get_json`)는 이 라우트를 거부합니다.

        카드 분기는 없습니다.
        :data:`~korail_mobile_api.safety.KORAIL_CARD_BEARING_MUTATION_CATEGORIES` 중 GET
        라우트를 가진 범주가 없기 때문이며, 그 교집합이 비어 있다는 것은 테스트가 단언합니다.
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
        """읽기 라우트에 GET 하고 봉투를 돌려줍니다.

        :meth:`post_form` 의 GET 판이며 라우트·필드 가드가 같습니다. 다른 점은
        ``include_common`` 의 기본값이 ``False`` 라는 것입니다 — GET 라우트 대부분이 공통 세
        필드를 쿼리에 싣지 않습니다.

        ``params`` 는 공통 필드 위에 덮어써 최종 쿼리가 되고, 그 쿼리 전체가
        :func:`~korail_mobile_api.safety.assert_read_only_request_fields` 를 지납니다.
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
