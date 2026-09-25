# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공개하지 않는 여행상품 검색 호출을 기록합니다. 패키지 내부에서 가져오지 않으며 KorailClient에도 노출하지 않습니다.

앱은 /ebizcom/gdLstDtl.do 에 검색 종류(funcDvCd)·정렬(bltnLstOrdr)·쪽당 건수(pgPrCnt)를 늘 싣는데 세 값 모두 보호돼
있습니다(SearchFunctionType.java:18; SearchOrderType.java:21-23; TravelSearchProductIn.java:78). 2026-09-25 실서버는 funcDvCd 없이 보낸
검색을 WRR000100(입력값 오류(funcDvCd))으로 거절했습니다. 보호값을 추측하지 않으므로 지원하지 않습니다.

요청 빌더는 read_payloads.build_travel_product_search_form(TravelProductSearchQuery), 응답은
read_parsers.parse_travel_product_search_response(TravelProductSearchResponse)에서 처리합니다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .read_models import TravelProductSearchResponse
from .read_parsers import parse_travel_product_search_response
from .read_payloads import TravelProductSearchQuery, build_travel_product_search_form

if TYPE_CHECKING:
    from .client import KorailClient


def search_travel_products(
    client: KorailClient, query: TravelProductSearchQuery
) -> TravelProductSearchResponse:
    """여행상품을 검색하는 미지원 호출을 기록합니다(NetworkApi.java:666-668). 앱은 로그인 없이도 부르며 대기열·DynaPath 가
    없습니다(TravelSearchViewModel.java:877-904; TravelSearchRepositoryImpl.java:609-633)."""
    return client._post_read(
        "/ebizcom/gdLstDtl.do",
        build_travel_product_search_form(query),
        parser=parse_travel_product_search_response,
    )
