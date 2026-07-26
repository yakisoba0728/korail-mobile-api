from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, Mapping
from urllib.parse import urlencode

import httpx

from .config import KorailConfig
from .constants import DYNAPATH_ALLOWLIST_PATHS
from .dynapath import DynapathRequestContext, DynapathTokenGenerator
from .errors import (
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
    MutationNotAllowedError,
    classify_app_error,
)
from .consent import MutationConsent, require_mutation_consent
from .models import BaseKorailResponse
from .safety import (
    assert_korail_origin,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_request_fields,
    assert_read_only_route,
)


def parse_base_response(data: Any, *, raise_on_fail: bool = True) -> BaseKorailResponse:
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
    def __init__(self, config: KorailConfig, *, transport: httpx.BaseTransport | None = None) -> None:
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
        return self._client.cookies

    def close(self) -> None:
        self._client.close()

    def common_fields(self) -> dict[str, str]:
        return {"Device": self.config.device, "Version": self.config.version, "Key": self.config.key}

    def _absolute_url(self, path: str) -> str:
        return f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _dynapath_headers(self, method: str, path: str) -> dict[str, str]:
        dynapath = self.config.dynapath
        if not dynapath.enabled:
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
        assert_korail_origin(str(self._client.base_url))
        assert_read_only_route("POST", path)
        if data is not None and not isinstance(data, (Mapping, Sequence)):
            raise KorailProtocolError(
                "KORAIL form data must be a mapping or registered ordered sequence"
            )
        ordered = data is not None and not isinstance(data, Mapping)
        form: dict[str, Any] | list[tuple[str, Any]]
        form = [] if ordered else {}
        if not include_common and data is not None:
            assert_read_only_request_fields(path, data)
        if include_common:
            if ordered:
                form.extend(self.common_fields().items())
            else:
                form.update(self.common_fields())
        if data:
            if ordered:
                form.extend(data)
            else:
                form.update(data)
        assert_read_only_request_fields(path, form)
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
        if include_dynapath:
            headers.update(self._dynapath_headers("POST", path))
        try:
            if ordered:
                response = self._client.post(
                    path,
                    content=urlencode(form).encode("ascii"),
                    headers=headers,
                )
            else:
                response = self._client.post(path, data=form, headers=headers)
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
        category: str,
        raise_on_fail: bool = True,
    ) -> BaseKorailResponse:
        """Send a state-changing form to an evidenced mutation route.

        This is the ONLY method that transmits to a mutation route, and it is
        double-gated: ``require_mutation_consent`` must pass for ``category``,
        ``consent.dry_run`` must be ``False`` (a dry-run preview never reaches
        the network), and ``assert_mutation_route`` restricts the target to
        :data:`~korail_mobile_api.safety.KORAIL_MUTATION_ROUTES`. The
        read-only path (:meth:`post_form`) still refuses these routes, so a
        mutation can only leave the process through this gate. ``data`` is sent
        verbatim (the reservation/cancel builders already include the common
        Device/Version/Key fields); no read-only field allowlist applies.

        A ``category="payment"`` send carries the PAN in the clear and is gated
        once more: the consent must state exactly one of
        ``fake_card_only=True`` (a non-chargeable test card) or
        ``real_card_acknowledged=True`` (an acknowledged real charge). Neither
        and both are refused.
        """
        require_mutation_consent(consent, category)
        if consent.dry_run:
            raise MutationNotAllowedError(
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
        if category == "payment":
            if consent.fake_card_only and consent.real_card_acknowledged:
                raise MutationNotAllowedError(
                    "payment mutations refuse a contradictory consent: "
                    "fake_card_only=True claims a non-chargeable test card "
                    "while real_card_acknowledged=True acknowledges a real "
                    "charge; set exactly one"
                )
            if not consent.fake_card_only and not consent.real_card_acknowledged:
                raise MutationNotAllowedError(
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
