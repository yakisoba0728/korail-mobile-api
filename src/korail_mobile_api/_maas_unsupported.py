# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""사용하지 않는 부가서비스(MaaS) 호출 — 기록용입니다. 패키지 어디에서도 import 하지 않고 KorailClient 에도 없습니다.

직접 지원하지 않는 이유: 부가서비스 장바구니 행은 KORAIL API 로 만들 수 없습니다. 메뉴의 중계 페이지(/ebizmaas/EbizMaasShopView.do)가
요청번호를 발급하고(EbizMaasAddSrvReqNo.do) 암호화된 본인 정보를 제휴사 사이트(야놀자, 짐캐리, 로이쿠, SK·롯데 렌터카, 그린카, KN파킹 —
/js/maas/maas_shop.js)로 넘긴 뒤, 제휴사에서 상품을 고를 때만 행이 생깁니다. 결제는 통합결제(pay.intgStl.do), 환불은 addService.coptCnc.do
인데 두 폼의 상수는 앱에서 보호돼 있습니다. 그래서 아래 세 호출은 앱 코드와 같게 만들었지만 실서버에서 한 번도 확인하지 못했고, 공개 API 에서
뺐습니다(2026-09-24).

폼·파서는 read_payloads.build_maas_cancel_fee_form / build_maas_cart_status_form,
mutation_payloads.build_maas_cancel_form, read_parsers.parse_maas_cancel_fee_response,
mutation_parsers.parse_maas_cancel_response 에 있습니다."""
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
    """결제된 부가서비스의 환불 수수료(maas.cncFee.do). item 은 get_maas_service_details 의
    행입니다(MyTicketDetailViewModel.java:840-860)."""
    client._require_session()
    return client._post_read(
        "/classes/com.korail.mobile.maas.cncFee.do",
        build_maas_cancel_fee_form(item),
        parser=parse_maas_cancel_fee_response,
    )


def check_maas_cart_status(client: KorailClient, item: CartItem) -> BaseKorailResponse:
    """결제 직전 부가서비스 장바구니 행 하나의 상태 확인(maas.rsvStt.do). 앱은 실패면 결제 화면으로 가지 않습니다
    (BasketTicketViewModel.java:1690-1800). 응답은 봉투뿐입니다."""
    client._require_session()
    return client._post_read(
        "/classes/com.korail.mobile.maas.rsvStt.do",
        build_maas_cart_status_form(item),
        parser=BaseKorailResponse.from_raw,
    )


def cancel_unpaid_maas_item(client: KorailClient, item: CartItem) -> MaasCancelResponse:
    """장바구니의 결제 전 부가서비스 해제(addService.cancelPay.do). pnr_no 가 빈 부가서비스 행만 받습니다(BasketTicketViewModel.java:
    3080-3160,5692-5723)."""
    customer_no = client._require_customer_no("MaaS cancel")
    return client._mutation(
        "/classes/com.korail.mobile.addService.cancelPay.do",
        build_maas_cancel_form(client.config, item, customer_no=customer_no),
        parser=parse_maas_cancel_response,
    )
