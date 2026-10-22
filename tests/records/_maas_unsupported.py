# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공개하지 않는 부가서비스 호출을 기록합니다. 배포 패키지에 들어가지 않는 테스트 기록이며 KorailClient에도 노출하지 않습니다.

확인된 앱 흐름은 중계 페이지(/ebizmaas/EbizMaasShopView.do)가 요청번호(EbizMaasAddSrvReqNo.do)를 발급하고, /js/maas/maas_shop.js가 암호화된
고객 정보를 제휴사에 넘겨 상품 선택 후 장바구니 행을 만드는 방식입니다. 이 라이브러리는 그 웹 흐름과 보호된 통합결제(pay.intgStl.do)·환불(addService.coptCnc.do)
상수를 재현하지 않습니다. 2026-09-24 기준 아래 세 호출은 실서버 검증 못 함이므로 지원하지 않습니다.

이 호출만 쓰는 빌더(build_maas_cancel_fee_form·build_maas_cart_status_form·build_maas_cancel_form)와
응답 모델·파서(parse_maas_cancel_fee_response·parse_maas_cancel_response)도 이 모듈에 둡니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from korail_mobile_api._core.parsing import (
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _response_mapping,
    _validate_envelope,
)
from korail_mobile_api._core.parsing import _response_fields as _base_fields
from korail_mobile_api._core.validation import _required_mutation_text, _required_text
from korail_mobile_api._core.wire import _device_version_key
from korail_mobile_api._domains.airport_bus.models import MaasServiceDetail
from korail_mobile_api._domains.common.models import BaseKorailResponse
from korail_mobile_api._domains.reservations.models import CartItem
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.errors import KorailProtocolError

if TYPE_CHECKING:
    from korail_mobile_api.client import KorailClient


@dataclass(frozen=True)
class MaasCancelFeeResponse(BaseKorailResponse):
    """부가서비스 환불 수수료 응답을 담습니다. 이 요청을 보내는 공개 메서드는 없습니다."""

    # 지원하지 않는 부가서비스 환불 수수료 응답 구조를 기록합니다(_maas_unsupported.get_maas_cancel_fee). 앱은 "환불수수료 N원"
    # 확인창에 보여 준 뒤 그 값으로 환불을 요청합니다(MyTicketDetailViewModel.java:840-860,1922).
    cancel_fee: str | None = None


@dataclass(frozen=True)
class MaasCancelResponse(BaseKorailResponse):
    """지원하지 않는 결제 전 부가서비스 해제 응답 구조를 기록합니다."""

    integrated_message_code: str | None = None


def build_maas_cancel_fee_form(item: MaasServiceDetail) -> dict[str, str]:
    """지원하지 않는 부가서비스 환불 수수료 조회 폼을 구성합니다. MaasCancelFeeIn.java 의 세 속성이며 값은 list_maas_services 행에서 옵니다
    (MyTicketDetailViewModel.java:840-860)."""
    if not isinstance(item, MaasServiceDetail):
        raise KorailProtocolError("item must be a MaasServiceDetail from list_maas_services")
    return {
        "addSrvReqNo": _required_text(item.additional_service_request_no, "additional_service_request_no"),
        "addSrvDvCd": _required_text(item.additional_service_code, "additional_service_code"),
        "coptEntRsvNo": _required_text(item.partner_reservation_no, "partner_reservation_no"),
    }


def _maas_cart_item(item: CartItem) -> CartItem:
    """앱은 h_pnr_no 가 빈 행을 부가서비스로 다루고(BasketTicketViewModel.java:3080-3160,3757-3780), 열차·공항버스 행은
    cancel_unpaid_hold 로 취소합니다."""
    if not isinstance(item, CartItem):
        raise KorailProtocolError("item must be a CartItem from list_cart_items")
    if item.pnr_no:
        raise KorailProtocolError(
            "KORAIL cart row with a PNR is a train or bus hold; use cancel_unpaid_hold for it"
        )
    return item


def build_maas_cart_status_form(item: CartItem) -> dict[str, str]:
    """지원하지 않는 부가서비스 장바구니 상태 조회 폼을 구성합니다. 앱은 선택한 행들의 값을 보호된 1글자 구분자로 잇는데
    (BasketTicketViewModel.java:1690-1750), 구분자를 모르므로 이 빌더는 한 행만 받습니다. seletedPos 는 전송되지 않습니다(:93)."""
    row = _maas_cart_item(item)
    return {
        "addSrvDvCd": _required_text(row.additional_service_code, "additional_service_code"),
        "addSrvReqNo": _required_text(row.virtual_reservation_no, "virtual_reservation_no"),
        "coptEntRsvNo": _required_text(row.partner_reservation_no, "partner_reservation_no"),
        "lumpStlTgtNo": _required_text(row.lump_sum_target_no, "lump_sum_target_no"),
    }


def build_maas_cancel_form(config: KorailConfig, item: CartItem, *, customer_no: str) -> dict[str, str]:
    """PNR이 빈 미결제 부가서비스 해제용이며 결제 후 환불과 다릅니다(BasketTicketViewModel.java:3080-3160,5692-5723)."""
    if not isinstance(item, CartItem):
        raise KorailProtocolError("item must be a CartItem from list_cart_items")
    if item.pnr_no:
        raise KorailProtocolError(
            "KORAIL cart row with a PNR is a train or bus hold; use cancel_unpaid_hold for it"
        )
    form = _device_version_key(config)
    form["custMgNo"] = _required_mutation_text(customer_no, field="customer_no", context="MaaS cancel")
    form["lumpStlTgtNo"] = _required_mutation_text(
        item.lump_sum_target_no, field="lump_sum_target_no", context="MaaS cancel"
    )
    return form


@_preserve_read_raw
def parse_maas_cancel_fee_response(raw: Mapping[str, Any]) -> MaasCancelFeeResponse:
    """지원하지 않는 부가서비스 환불 수수료 응답을 읽습니다. maas.cncFee.do 응답. cncRetFee 는 선택 스칼라로 읽습니다(MaasCancelFeeOut.java)."""
    _validate_envelope(raw)
    return MaasCancelFeeResponse(
        cancel_fee=_optional_scalar_string(raw, "cncRetFee"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_maas_cancel_response(raw: Mapping[str, Any]) -> MaasCancelResponse:
    """지원하지 않는 미결제 부가서비스 해제 응답을 읽습니다. addService.cancelPay.do 응답. intgMsgCd 는 선택 스칼라입니다(MaasCancelOut.java)."""
    data = _response_mapping(raw)
    return MaasCancelResponse(
        **_base_fields(data),
        integrated_message_code=_optional_scalar_string(data, "intgMsgCd"),
    )


def get_maas_cancel_fee(client: KorailClient, item: MaasServiceDetail) -> MaasCancelFeeResponse:
    """결제된 부가서비스의 환불 수수료를 조회하는 미지원 호출을 기록합니다. item은 list_maas_services의
    행입니다(MyTicketDetailViewModel.java:840-860)."""
    client._require_session()
    return client._post_read(
        "/classes/com.korail.mobile.maas.cncFee.do",
        build_maas_cancel_fee_form(item),
        parser=parse_maas_cancel_fee_response,
    )


def check_maas_cart_status(client: KorailClient, item: CartItem) -> BaseKorailResponse:
    """결제 직전 부가서비스 장바구니 상태를 확인하는 미지원 호출을 기록합니다. 앱은 실패 시 결제 화면으로 이동하지 않습니다(BasketTicketViewModel.java:1690-1800).
    응답은 공통 봉투뿐입니다."""
    client._require_session()
    return client._post_read(
        "/classes/com.korail.mobile.maas.rsvStt.do",
        build_maas_cart_status_form(item),
        parser=BaseKorailResponse.from_raw,
    )


def cancel_unpaid_maas_item(client: KorailClient, item: CartItem) -> MaasCancelResponse:
    """미결제 부가서비스를 해제하는 미지원 변경 호출을 기록합니다. pnr_no가 빈 장바구니 행만
    받습니다(BasketTicketViewModel.java:3080-3160,5692-5723)."""
    customer_no = client._require_customer_no("MaaS cancel")
    return client._mutation(
        "/classes/com.korail.mobile.addService.cancelPay.do",
        build_maas_cancel_form(client.config, item, customer_no=customer_no),
        parser=parse_maas_cancel_response,
    )
