# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공개하지 않는 부가서비스 호출을 기록합니다. 패키지 내부에서 가져오지 않으며 KorailClient에도 노출하지 않습니다.

확인된 앱 흐름은 중계 페이지(/ebizmaas/EbizMaasShopView.do)가 요청번호(EbizMaasAddSrvReqNo.do)를 발급하고, /js/maas/maas_shop.js가 암호화된
고객 정보를 제휴사에 넘겨 상품 선택 후 장바구니 행을 만드는 방식입니다. 이 라이브러리는 그 웹 흐름과 보호된 통합결제(pay.intgStl.do)·환불(addService.coptCnc.do)
상수를 재현하지 않습니다. 2026-09-24 기준 아래 세 호출은 실서버 검증 못 함이므로 지원하지 않습니다.

관련 빌더는 read_payloads.build_maas_cancel_fee_form·build_maas_cart_status_form과
mutation_payloads.build_maas_cancel_form이며, 응답은 read_parsers·mutation_parsers에서 처리합니다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import BaseKorailResponse
from .mutation_models import MaasCancelResponse
from .mutation_parsers import parse_maas_cancel_response
from .mutation_payloads import build_maas_cancel_form
from .read_models import CartItem, MaasCancelFeeResponse, MaasServiceDetail
from .read_parsers import parse_maas_cancel_fee_response
from .read_payloads import build_maas_cancel_fee_form, build_maas_cart_status_form

if TYPE_CHECKING:
    from .client import KorailClient


def get_maas_cancel_fee(client: KorailClient, item: MaasServiceDetail) -> MaasCancelFeeResponse:
    """결제된 부가서비스의 환불 수수료를 조회하는 미지원 호출을 기록합니다. item은 get_maas_service_details의
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
