# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""7.0.6 APK에서 추가된 Retrofit 계약의 메서드별 전송 경계.

각 이름은 ``v7_contract_data.py`` 에 고정된 단일 인터페이스/메서드를 가리킨다.
호출자는 APK 모델의 *wire key*를 전달한다. 보호된 기본값과 제휴 호스트는
정적 디컴파일에서 확인할 수 없어 여기서 합성하지 않는다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict, cast
from urllib.parse import urlencode, urlsplit

import httpx

from .errors import KorailMutationNotAllowedError, KorailProtocolError, KorailTransportError
from .http import KorailHttpClient, _raise_for_status, parse_base_response
from .safety import (
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    assert_korail_origin,
    assert_mutation_route,
    assert_mutation_route_category,
    assert_read_only_route,
)
from .v7_contract_data import CONTRACT_ROWS


_ANNOTATION = re.compile(r"(Field|Query)\(([^)]+)\)")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
# 정기권/패스 purchase and issue. The APK declares these contracts, so the
# registry lists them, but this package never sends one: a settlement is
# ₩150,000-₩250,000 with no refund or cancel route here, and the shipped app
# never reaches passPayIssue itself (PaymentActivity.isCommPaymentRequest()
# tests a Response type where a Request is required). A purchase pair was
# implemented on 2026-07-26 and removed the same day; MUTATION_HANDOFF records
# why. call() refuses them first, unconditionally, regardless of what the
# caller sends.
_NEVER_SENT = frozenset({
    "NetworkApi.postPassReserve",
    "NetworkApi.postPassPayIssue",
    "NetworkApi.passOtrReserve",
    "NetworkApi.postPassOtrPayIssue",
})
# NetworkApi response models that do not extend CommonOut. VerifyOnlineRefundsOut
# declares its own strResult defaulting to null rather than CommonOut's FAIL
# constant (VerifyOnlineRefundsOut.java:97), so a missing strResult is not a
# failure for it (주의할 점: dropping this exemption misclassifies a real
# successful verifyOnlineRefunds response as a failure).
_NON_COMMON_OUT_RESPONSE_MODELS = frozenset({
    "com.korail.talk.network.model.VerifyOnlineRefundsOut",
})


V7Effect = Literal["read", "mutation"]


class _ContractRow(TypedDict):
    """One row of ``v7_contract_data.CONTRACT_ROWS``."""

    interface: str
    method: str
    http: str
    route: str
    params: str
    form: bool
    request_model: str | None
    response_model: str
    effect: V7Effect


@dataclass(frozen=True)
class V7Contract:
    interface: str
    method: str
    http: str
    route: str
    params: str
    form: bool
    request_model: str | None
    response_model: str
    effect: V7Effect

    @property
    def name(self) -> str:
        return f"{self.interface}.{self.method}"

    def _names(self, kind: str) -> frozenset[str]:
        return frozenset(
            name for found, name in _ANNOTATION.findall(self.params) if found == kind
        )

    @property
    def fields(self) -> frozenset[str]:
        return self._names("Field")

    @property
    def queries(self) -> frozenset[str]:
        return self._names("Query")


def _load_registry() -> dict[str, V7Contract]:
    rows = cast(tuple[_ContractRow, ...], CONTRACT_ROWS)
    # What the cast promises, checked: rows carry "read" or "mutation" as
    # documentation of intent, so a misspelled effect would go unnoticed by
    # call() itself. Checked on the rows, before an override could paper over one.
    if any(row["effect"] not in ("read", "mutation") for row in rows):
        raise KorailProtocolError(
            "7.0.6 contract registry has an effect other than read or mutation"
        )
    contracts = [V7Contract(**row) for row in rows]
    registry = {contract.name: contract for contract in contracts}
    if len(registry) != len(contracts):
        raise KorailProtocolError("7.0.6 contract registry is incomplete")
    if any(
        (parts := urlsplit(contract.route)).scheme
        or parts.netloc
        or parts.query
        or parts.fragment
        or ".." in contract.route.split("/")
        or not contract.route
        for contract in contracts
    ):
        raise KorailProtocolError("7.0.6 contract registry has an unsafe route")
    return registry


V7_CONTRACTS = _load_registry()


@dataclass(frozen=True)
class V7Response:
    name: str
    response_model: str
    raw: Any = field(repr=False)


def _assert_wire_value(value: Any) -> None:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        return
    raise KorailProtocolError("form/query wire values must be strings, integers or string lists")


class V7Gateway:
    """유일하게 살아남은 Retrofit 메서드 2개의 폼 요청을 전송한다.

    메인 API는 ``KorailClient``의 기존 세션과 DynaPath 설정을 공유한다.
    """

    def __init__(self, http: KorailHttpClient) -> None:
        self.http = http

    def close(self) -> None:
        """더 이상 닫을 별도 클라이언트가 없다."""

    def _client(self) -> httpx.Client:
        assert_korail_origin(str(self.http._client.base_url))
        return self.http._client

    def call(
        self,
        name: str,
        values: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        include_common: bool = False,
        raise_on_fail: bool = True,
    ) -> V7Response:
        """APK의 메서드 이름을 고르고 원래 어노테이션 형태로 요청한다.

        ``values`` 는 DTO의 Python 속성명이 아닌 wire key다. 메서드에
        ``@FieldMap``/``@QueryMap``이 있으면 가변 키가 허용되고, 다른 경우
        어노테이션에 선언된 키만 허용된다. nullable 인자 생략은 키 생략으로
        표현한다. 상태 변경(mutation)은 즉시 전송된다. 단, _NEVER_SENT 에 오른
        정기권/패스 구매 계약은 이름으로 거절된다. 그 밖의 모든 계약은 상위 API와 같은
        ``safety`` 라우트 표를 거친다 — ``effect == "read"`` 면
        :data:`~korail_mobile_api.safety.KORAIL_READ_ONLY_ROUTES` 의 원소여야 하고,
        ``effect == "mutation"`` 이면
        :data:`~korail_mobile_api.safety.KORAIL_MUTATION_ROUTES` 의 원소이면서
        :data:`~korail_mobile_api.safety.KORAIL_MUTATION_ROUTE_CATEGORIES` 에 등록된
        범주와 일치해야 한다. 근거 없는 라우트는 여기서도 나갈 수 없다.
        """
        if name in _NEVER_SENT:
            raise KorailMutationNotAllowedError(
                f"{name} is a 정기권/패스 purchase, which this package never sends: "
                "it has no refund or cancel route here"
            )
        contract = V7_CONTRACTS.get(name)
        if contract is None:
            raise KorailProtocolError(f"unknown 7.0.6 method: {name}")
        data = dict(values or {})
        header_map = dict(headers or {})
        is_body = "Body" in contract.params
        if include_common:
            if contract.interface != "NetworkApi" or is_body:
                raise KorailProtocolError("common fields only apply to main form/query contracts")
            # Every CommonIn subclass serializes CommonIn first
            # (VerifyOnlineRefundsIn.java:123-124; PushUpdateIn.java's
            # write$Self calls CommonIn.write$Self first), so Device/Version/
            # Key must lead the wire form, not trail the caller's fields.
            common = {k: v for k, v in self.http.common_fields().items() if k not in data}
            data = {**common, **data}
        if any(not isinstance(key, str) or not _NAME.fullmatch(key) for key in data):
            raise KorailProtocolError("invalid wire field name")
        if any(not isinstance(value, str) or "\r" in value or "\n" in value
               for value in header_map.values()):
            raise KorailProtocolError("invalid header value")
        map_kind = "FieldMap" if contract.form else "QueryMap"
        has_map = map_kind in contract.params
        declared = contract.fields if contract.form else contract.queries
        if not is_body:
            if not has_map and not set(data) <= declared:
                raise KorailProtocolError("wire fields do not match Retrofit annotations")
            for value in data.values():
                _assert_wire_value(value)
        elif not isinstance(values, Mapping):
            raise KorailProtocolError("@Body requires a JSON object")
        # The same route table the high-level senders check, not a separate
        # v7-only allowlist: a read contract must be a registered read route,
        # a mutation contract a registered mutation route whose category
        # matches what safety.py has on file for it. Before this, a 7.0.6
        # contract with no counterpart in either table -- like the refund
        # execute/verify pair once was -- reached the wire with no route
        # check at all.
        if contract.effect == "read":
            assert_read_only_route(contract.http, contract.route)
        else:
            assert_mutation_route(contract.http, contract.route)
            assert_mutation_route_category(
                contract.route,
                KORAIL_MUTATION_ROUTE_CATEGORIES.get(contract.route, ""),
            )
        client = self._client()
        target = contract.route
        request_headers = dict(header_map)
        request_headers.update(self.http._dynapath_headers(contract.http, contract.route))
        try:
            if is_body:
                response = client.request(
                    contract.http, target, json=data, headers=request_headers
                )
            elif contract.form:
                pairs: list[tuple[str, Any]] = []
                for key, value in data.items():
                    if isinstance(value, list):
                        pairs.extend((key, item) for item in value)
                    else:
                        pairs.append((key, value))
                request_headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                response = client.request(
                    contract.http, target,
                    content=urlencode(pairs).encode("ascii"), headers=request_headers,
                )
            elif contract.http == "GET":
                response = client.get(target, params=data, headers=request_headers)
            else:
                response = client.post(target, headers=request_headers)
        except httpx.HTTPError as exc:
            raise KorailTransportError(f"7.0.6 transport failed for {name}") from exc
        _raise_for_status(response, path=contract.route)
        try:
            raw = response.json()
        except ValueError as exc:
            raise KorailProtocolError("7.0.6 response is not valid JSON") from exc
        if contract.interface == "NetworkApi" and isinstance(raw, dict) and any(
            key in raw for key in ("strResult", "h_msg_cd")
        ):
            parse_base_response(
                raw,
                raise_on_fail=raise_on_fail,
                require_result=(
                    contract.response_model not in _NON_COMMON_OUT_RESPONSE_MODELS
                ),
            )
        return V7Response(name=name, response_model=contract.response_model, raw=raw)
