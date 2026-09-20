# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""7.0.6 APK에서 추가된 Retrofit 계약의 메서드별 전송 경계.

각 이름은 ``v7_contract_data.py`` 에 고정된 단일 인터페이스/메서드를 가리킨다.
호출자는 APK 모델의 *wire key*를 전달한다. 보호된 기본값과 제휴 호스트는
정적 디컴파일에서 확인할 수 없어 여기서 합성하지 않는다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Literal, TypedDict, cast
from urllib.parse import urlencode, urlsplit

import httpx

from .errors import KorailMutationNotAllowedError, KorailProtocolError, KorailTransportError
from .http import KorailHttpClient, _raise_for_status, parse_base_response
from .safety import (
    KORAIL_MUTATION_ROUTES,
    assert_korail_origin,
)
from .v7_contract_data import CONTRACT_ROWS


_ANNOTATION = re.compile(r"(Field|Query|Header)\(([^)]+)\)")
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
# Generated Retrofit rows preserve signatures and DTO names. Effect is a local
# safety decision: password checks can increment failure counters, while the
# check-in, QR and payment-status routes have unverified operational side effects.
_MUTATION_OVERRIDES = frozenset({
    "NetworkApi.postDiscountCheck",
    "NetworkApi.postInquiryIsMember",
    "NetworkApi.postLPotAthn",
    "NetworkApi.postXPointView",
    "NetworkApi.postOkCashbagCertView",
    "NetworkApi.postSelfCheckInInfo",
    "NetworkApi.postSelfCheckInPossible",
    "NetworkApi.postLocalRailwayTravelQrAuth",
    "NetworkApi.postMemberVerify",
    "NetworkApi.paymentMassStatusIn",
    # 비회원 예약 생성. NonMemTicketIn is the non-member TicketReservationIn
    # (txtJobId, jrnyList, passengerInfoList, txtCustPw, ...) and returns the
    # same ReservationOut as certification.TicketReservation: it creates a hold.
    # The generator (analysis/generated/build_v7_contract.py READ_METHODS) lists
    # it as read; this override is the deciding classification.
    # postNonMemTicketList stays a read (lookup).
    "NetworkApi.postNonMemTicket",
})
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
# Interfaces sent on the shared KORAIL HTTP client; a partner origin serves the rest.
_MAIN_HTTP_INTERFACES = frozenset({"NetworkApi", "PushService"})
# NetworkApi response models that do not extend CommonOut. Three declare their
# own strResult defaulting to null or "" rather than CommonOut's FAIL constant
# (CacheCheckResponse.java:62, AcpnMlgSaveResponse.java:101,
# VerifyOnlineRefundsOut.java:97); the other four have no envelope field at all.
# A missing strResult is therefore not a failure for these.
_NON_COMMON_OUT_RESPONSE_MODELS = frozenset({
    "com.korail.talk.data.CacheCheckResponse",
    "com.korail.talk.data.CacheReadResponse",
    "com.korail.talk.network.model.AcpnMlgSaveResponse",
    "com.korail.talk.network.model.LostCenterResponse",
    "com.korail.talk.network.model.SearchMetaOut",
    "com.korail.talk.network.model.SpecificDateDataOut",
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

    @property
    def headers(self) -> frozenset[str]:
        return self._names("Header")


def _load_registry() -> dict[str, V7Contract]:
    rows = cast(tuple[_ContractRow, ...], CONTRACT_ROWS)
    # What the cast promises, checked: rows carry "read" or "mutation" as
    # documentation of intent, so a misspelled effect would go unnoticed by
    # call() itself. Checked on the rows, before an override could paper over one.
    if any(row["effect"] not in ("read", "mutation") for row in rows):
        raise KorailProtocolError(
            "7.0.6 contract registry has an effect other than read or mutation"
        )
    contracts = [
        replace(contract, effect="mutation")
        if contract.name in _MUTATION_OVERRIDES else contract
        for contract in (V7Contract(**row) for row in rows)
    ]
    registry = {contract.name: contract for contract in contracts}
    if len(contracts) != 117 or len(registry) != len(contracts):
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


def _assert_partner_origin(origin: str) -> None:
    parsed = urlsplit(origin)
    try:
        port = parsed.port
    except ValueError as exc:
        raise KorailProtocolError("invalid partner origin") from exc
    if (
        parsed.scheme.lower() != "https"
        or not parsed.hostname
        or port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise KorailProtocolError("partner origin must be an HTTPS origin")


def _assert_wire_value(value: Any) -> None:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return
    if isinstance(value, list) and value and all(isinstance(item, str) for item in value):
        return
    raise KorailProtocolError("form/query wire values must be strings, integers or string lists")


def _assert_body_shape(contract: V7Contract, data: Mapping[str, Any]) -> None:
    """보호된 wire 이름을 추측하지 않고 확인된 DTO 필드의 형을 검사한다."""
    if contract.request_model == "com.korail.talk.network.model.GreenCarDetailRequest":
        if len(data) != 2 or any(not isinstance(value, str) for value in data.values()):
            raise KorailProtocolError("GreenCar detail body requires two strings")
    elif contract.request_model == "com.korail.talk.data.CacheCheckRequest":
        if len(data) != 1:
            raise KorailProtocolError("cache-check body requires a versions map")
        versions = next(iter(data.values()))
        if not isinstance(versions, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in versions.items()
        ):
            raise KorailProtocolError("cache-check versions must map strings to strings")


def _assert_known_map_shape(contract: V7Contract, data: Mapping[str, Any]) -> None:
    """Limit a known DTO even though Retrofit accepts a generic QueryMap."""
    if contract.name != "NetworkApi.productCancel":
        return
    allowed = {"Device", "Version", "Key", "lang", "txtVrRsNo", "txtGdSqno"}
    if not set(data) <= allowed:
        raise KorailProtocolError("product cancellation has unknown DTO fields")
    if any(
        not isinstance(data.get(key), str) or not data[key].strip()
        for key in ("txtVrRsNo", "txtGdSqno")
    ):
        raise KorailProtocolError("product cancellation requires reservation and product IDs")


class V7Gateway:
    """고유 Retrofit 메서드 117개의 폼/쿼리/JSON 요청을 전송한다.

    메인 API는 ``KorailClient``의 기존 세션과 DynaPath 설정을 공유한다.
    제휴 API는 caller가 지정한 HTTPS origin에 독립 클라이언트를 만들되
    APK의 공유 CookieManager처럼 메인 API와 도메인 범위의 쿠키 저장소를 공유한다.
    PushService는 주입된 webHost origin에 메인 HTTP 클라이언트로 요청한다.
    """

    def __init__(
        self,
        http: KorailHttpClient,
        *,
        partner_origins: Mapping[str, str] | None = None,
        partner_transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.http = http
        self.partner_origins = MappingProxyType(dict(partner_origins or {}))
        known_interfaces = {contract.interface for contract in V7_CONTRACTS.values()}
        korail_host = urlsplit(self.http.config.base_url).hostname
        for interface, origin in self.partner_origins.items():
            if interface == "NetworkApi" or interface not in known_interfaces:
                raise KorailProtocolError("unknown partner interface")
            _assert_partner_origin(origin)
            if (interface != "PushService" and
                urlsplit(origin).hostname == korail_host):
                raise KorailProtocolError("partner origin must be separate from KORAIL")
        self.partner_transport = partner_transport
        self._partners: dict[str, httpx.Client] = {}

    def close(self) -> None:
        for client in self._partners.values():
            client.close()
        self._partners.clear()

    def _client_for(self, contract: V7Contract) -> httpx.Client:
        if contract.interface in _MAIN_HTTP_INTERFACES:
            assert_korail_origin(str(self.http._client.base_url))
            return self.http._client
        origin = self.partner_origins.get(contract.interface)
        if origin is None:
            raise KorailProtocolError(f"origin required for {contract.interface}")
        client = self._partners.get(contract.interface)
        if client is None:
            client = httpx.Client(
                base_url=origin,
                timeout=self.http.config.timeout,
                transport=self.partner_transport,
                cookies=self.http.cookies.jar,
            )
            self._partners[contract.interface] = client
        return client

    def _target_for(self, contract: V7Contract) -> str:
        if contract.interface == "PushService":
            origin = self.partner_origins.get("PushService")
            if origin is None:
                raise KorailProtocolError("web origin required for PushService")
            return origin.rstrip("/") + contract.route
        return contract.route

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
        정기권/패스 구매 계약은 이름으로 거절된다. 상위 API의 읽기 라우트와
        겹치는 계약은 같은 ``safety`` 필드 검증을 거치고, 변경 라우트와 겹치는
        계약은 거부된다.
        """
        contract = V7_CONTRACTS.get(name)
        if contract is None:
            raise KorailProtocolError(f"unknown 7.0.6 method: {name}")
        if name in _NEVER_SENT:
            raise KorailMutationNotAllowedError(
                f"{name} is a 정기권/패스 purchase, which this package never sends: "
                "it has no refund or cancel route here"
            )
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
        if not set(header_map) <= contract.headers:
            raise KorailProtocolError("headers must match Retrofit @Header declarations")
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
            _assert_known_map_shape(contract, data)
        elif not isinstance(values, Mapping):
            raise KorailProtocolError("@Body requires a JSON object")
        else:
            _assert_body_shape(contract, data)
        route = (contract.http, contract.route)
        if route in KORAIL_MUTATION_ROUTES:
            # The high-level mutation transport owns the route/category check.
            raise KorailProtocolError(
                f"{name} targets KORAIL mutation route {contract.route}; use the "
                "high-level KorailClient method for it"
            )
        client = self._client_for(contract)
        target = self._target_for(contract)
        request_headers = dict(header_map)
        if contract.interface in _MAIN_HTTP_INTERFACES:
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
