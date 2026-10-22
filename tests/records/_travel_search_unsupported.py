# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공개하지 않는 여행상품 검색 호출을 기록합니다. 배포 패키지에 들어가지 않는 테스트 기록이며 KorailClient에도 노출하지 않습니다.

앱은 /ebizcom/gdLstDtl.do 에 검색 종류(funcDvCd)·정렬(bltnLstOrdr)·쪽당 건수(pgPrCnt)를 늘 싣는데 세 값 모두 보호돼
있습니다(SearchFunctionType.java:18; SearchOrderType.java:21-23; TravelSearchProductIn.java:78). 2026-09-25 실서버는 funcDvCd 없이 보낸
검색을 WRR000100(입력값 오류(funcDvCd))으로 거절했습니다. 보호값을 추측하지 않으므로 지원하지 않습니다.

요청 빌더 build_travel_product_search_form(TravelProductSearchQuery)와 응답 파서
parse_travel_product_search_response(TravelProductSearchResponse)도 이 모듈에 둡니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from korail_mobile_api._core.parsing import (
    _nullable_scalar_fields,
    _optional_read_rows,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _validate_strict_read_envelope,
)
from korail_mobile_api._core.validation import _int_text, _required_text
from korail_mobile_api._domains.common.models import BaseKorailResponse
from korail_mobile_api.errors import KorailProtocolError

if TYPE_CHECKING:
    from korail_mobile_api.client import KorailClient


@dataclass(frozen=True)
class TravelProduct:
    """여행상품 검색 결과의 상품 한 개를 담습니다.

    열두 필드 모두 응답에 없으면 ``None``입니다. ``goods_no``는 ``get_product_detail``의 예약 번호가 아닙니다."""

    # 열두 필드 모두 선택입니다(TravelProductItem.java:61-105). 앱은 goods_no·name·info_url·representative_fare 만
    # 씁니다(TravelSearchViewModel.java:1070-1074).
    goods_no: str | None = None
    name: str | None = None
    area_code: str | None = None
    area_name: str | None = None
    event_start_date: str | None = None
    event_end_date: str | None = None
    company_name: str | None = None
    info_url: str | None = None
    representative_fare: str | None = None
    description: str | None = None
    standard_clause_1: str | None = None
    standard_clause_2: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class TravelProductSearchResponse(BaseKorailResponse):
    """여행상품 검색 결과를 담습니다.

    응답의 목록 객체(``lst``)가 없거나 ``null``이면 빈 결과입니다. 이 요청을 보내는 공개 메서드는 없습니다."""

    # 여행상품 검색(/ebizcom/gdLstDtl.do, _travel_search_unsupported). lst 객체는 선택·nullable 이고
    # (TravelSearchProductOut.java:48-55) 그 안의 gdList·qryCnt·pgCnt 도 모두 선택입니다(TravelProductList.java:56-68). 앱은 현재 쪽
    # 번호가 page_count 이상이면 더 부르지 않습니다.
    products: tuple[TravelProduct, ...] = ()
    query_count: str | None = None
    page_count: str | None = None


# 앱은 검색어를 한 칸에만 넣습니다(TravelSearchViewModel.java:877-904).
_TRAVEL_KEYWORD_KEYS = {"name": "gdNm", "area": "gdTripArNm", "theme": "gdThmNm", "category": "gdCateCdNm"}


@dataclass(frozen=True)
class TravelProductSearchQuery:
    """필수 값(``funcDvCd``)을 확인하지 못해 공개 클라이언트에서는 쓰지 않는 기록용 입력입니다."""

    # 필수 funcDvCd 가 보호돼 있습니다(TravelSearchProductIn.java:78; 서버 거절 관측).

    keyword: str
    keyword_field: Literal["name", "area", "theme", "category"] = "name"
    page_no: int = 1
    function_code: str | None = None
    order_code: str | None = None
    page_size: str | None = None

    def __post_init__(self) -> None:
        _required_text(self.keyword, "keyword")
        if self.keyword_field not in _TRAVEL_KEYWORD_KEYS:
            raise KorailProtocolError("keyword_field must be one of name, area, theme, category")
        _int_text(self.page_no, "page_no")
        for name in ("function_code", "order_code", "page_size"):
            value = getattr(self, name)
            if value is not None:
                _required_text(value, name)


def build_travel_product_search_form(query: TravelProductSearchQuery) -> dict[str, str]:
    """키 순서는 TravelSearchProductIn 합성 생성자(TravelSearchProductIn.java:60-81)의 순서이며 앱이 채우지 않는
    gdNo·qryCnt·mrkWctNo 는 빈 값이라 평탄화에서 빠집니다."""
    if not isinstance(query, TravelProductSearchQuery):
        raise KorailProtocolError("query must be a TravelProductSearchQuery")
    form: dict[str, str] = {}
    if query.function_code is not None:
        form["funcDvCd"] = query.function_code
    form[_TRAVEL_KEYWORD_KEYS[query.keyword_field]] = query.keyword.strip()
    if query.order_code is not None:
        form["bltnLstOrdr"] = query.order_code
    form["nowPgNo"] = _int_text(query.page_no, "page_no")
    if query.page_size is not None:
        form["pgPrCnt"] = query.page_size
    return form


_TRAVEL_PRODUCT_FIELDS = {
    "goods_no": "gdNo",
    "name": "gdNm",
    "area_code": "gdTripArCd",
    "area_name": "gdTripArNm",
    "event_start_date": "evtStDt",
    "event_end_date": "evtClsDt",
    "company_name": "entNm",
    "info_url": "gdInfoUrlAdr",
    "representative_fare": "gdRepFare",
    "description": "ln1DscCont",
    "standard_clause_1": "gdStdrClauValCont1",
    "standard_clause_2": "gdStdrClauValCont2",
}


@_preserve_read_raw
def parse_travel_product_search_response(raw: Mapping[str, Any]) -> TravelProductSearchResponse:
    _validate_strict_read_envelope(raw)
    listing = raw.get("lst")
    if listing is None:
        return TravelProductSearchResponse(**_response_fields(raw))
    if not isinstance(listing, Mapping):
        raise KorailProtocolError("KORAIL travel product search field lst must be an object or null")
    products = tuple(
        TravelProduct(**_nullable_scalar_fields(row, _TRAVEL_PRODUCT_FIELDS, "travel product"), raw=row)
        for row in _optional_read_rows(listing, "gdList", "travel product search")
    )
    return TravelProductSearchResponse(
        products=products,
        query_count=_optional_scalar_string(listing, "qryCnt", "travel product search"),
        page_count=_optional_scalar_string(listing, "pgCnt", "travel product search"),
        **_response_fields(raw),
    )


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
