# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·패스·N카드·여행상품 응답을 읽습니다. 변경 응답 파싱 실패 시 전체 raw와 부분 parser_raw를 보존하며 재전송하지 않습니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _validate_envelope,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from ..reservations.parsers import _response_mapping
from .models import (
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CommuterPassengerOption,
    DiscountCardPurchaseResponse,
    DiscountCardScheduleResponse,
    DiscountCardScheduleTrain,
    DiscountCardUsage,
    DiscountCardUsageListResponse,
    PassAgeOption,
    PassAvailabilityMainInfo,
    PassAvailabilityResponse,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassOpenDate,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PassScheduleInfo,
    PassScheduleMainInfo,
    PassScheduleResponse,
    PassScheduleTrain,
    ProductCancelResponse,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)


def _parse_pass_menu_data(
    data: Mapping[str, object] | None,
    *,
    station_selection_key: str = "h_select_station",
) -> PassMenuData | None:
    if data is None:
        return None
    return wire_model(
        PassMenuData,
        data,
        "pass menu data",
        station_selection=_optional_scalar_string(data, station_selection_key),
        age_options=wire_models(PassAgeOption, _rows(data, "pass_ageinfo"), "pass age option"),
        period_options=wire_models(PassPeriodOption, _rows(data, "pass_periodinfo"), "pass period option"),
        raw=data,
    )


def _parse_pass_goods_info(data: Mapping[str, object] | None) -> PassGoodsInfo | None:
    if data is None:
        return None
    infos = _optional_mapping(data, "psg_infos")
    passenger_infos = (
        None
        if infos is None
        else wire_model(
            PassPassengerInfos,
            infos,
            "pass passenger infos",
            psg_info=wire_models(PassPassengerInfo, _rows(infos, "psg_info"), "pass passenger info"),
            raw=infos,
        )
    )
    return wire_model(PassGoodsInfo, data, "pass goods info", psg_infos=passenger_infos, raw=data)


@_preserve_read_raw
def parse_pass_menu_response(raw: Mapping[str, object]) -> PassMenuResponse:
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _rows(raw, "list"):
        web_data = _optional_mapping(item, "webData")
        items.append(
            wire_model(
                PassMenuItem,
                item,
                "pass menu item",
                goods_data=_parse_pass_goods_info(_optional_mapping(item, "goodsData")),
                pass_data=_parse_pass_menu_data(_optional_mapping(item, "passData")),
                url=_optional_scalar_string(web_data, "url") if web_data is not None else None,
                raw=item,
            )
        )
    return PassMenuResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_commuter_kind_menu_response(raw: Mapping[str, object]) -> CommuterKindMenuResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(
        CommuterKindMenuResponse,
        raw,
        "commuter kind menu",
        pass_data=_parse_pass_menu_data(_optional_mapping(raw, "passData")),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pass_availability_response(raw: Mapping[str, object]) -> PassAvailabilityResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    pass_info = wire_models(PassOpenDate, _rows(raw, "pass_info"), "pass open date")
    issue_dates = (_optional_scalar_string(item, "h_ise_dt2") for item in _rows(raw, "ticket_info"))
    # 결과 코드는 최상위 h_msg_cd 없이 중첩 main_info 에만 올 수 있습니다.
    main_raw = _optional_mapping(raw, "main_info")
    return PassAvailabilityResponse(
        open_dates=tuple(row.open_date for row in pass_info if row.open_date is not None),
        ticket_issue_dates=tuple(date for date in issue_dates if date is not None),
        offices=wire_models(PassOffice, _rows(raw, "wct_info"), "pass office"),
        pass_info=pass_info,
        main_info=(
            None
            if main_raw is None
            else wire_model(PassAvailabilityMainInfo, main_raw, "pass availability main info", raw=main_raw)
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pass_schedule_response(raw: Mapping[str, object]) -> PassScheduleResponse:
    # WRG000000 은 조회 결과 없음 안내입니다. 빈 결과로 두는 근거는 안내문·실서버 기록이며 앱의 분기는 확인하지 못했습니다.
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    main_raw = _optional_mapping(raw, "main_info")
    schedules = tuple(
        PassScheduleInfo(
            trains=wire_models(PassScheduleTrain, _rows(schedule, "train_list"), "pass schedule train"),
            raw=schedule,
        )
        for schedule in _rows(raw, "schedule_info")
    )
    return PassScheduleResponse(
        main_info=(
            None
            if main_raw is None
            else wire_model(PassScheduleMainInfo, main_raw, "pass schedule main info", raw=main_raw)
        ),
        schedules=schedules,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_card_usage_response(raw: Mapping[str, object]) -> DiscountCardUsageListResponse:
    _validate_strict_read_envelope(raw)
    return DiscountCardUsageListResponse(
        items=wire_models(DiscountCardUsage, _rows(raw, "tkUseList"), "discount card usage"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_card_schedule_response(raw: Mapping[str, object]) -> DiscountCardScheduleResponse:
    _validate_strict_read_envelope(raw)
    return DiscountCardScheduleResponse(
        trains=wire_models(
            DiscountCardScheduleTrain, _rows(raw, "trnScdlList"), "discount card schedule train"
        ),
        **_response_fields(raw),
    )


def _primitive_json_integer(data: Mapping[str, object], key: str) -> int | None:
    """Kotlin Int 값을 읽되 누락·null 은 0, 잘못된 형식은 None 입니다."""
    if data.get(key) is None:
        return 0
    return _optional_integer(data, key)


@_preserve_read_raw
def parse_commuter_info_response(raw: Mapping[str, object]) -> CommuterInfoResponse:
    _validate_strict_read_envelope(raw)
    passenger_options = tuple(
        wire_model(
            CommuterPassengerOption,
            item,
            "commuter passenger option",
            customer_age_from=_primitive_json_integer(item, "custAgeFrom"),
            customer_age_to=_primitive_json_integer(item, "custAgeTo"),
            passenger_count_from=_primitive_json_integer(item, "psgPrnbFrom"),
            passenger_count_to=_primitive_json_integer(item, "psgPrnbTo"),
            raw=item,
        )
        for item in _rows(raw, "psgList")
    )
    return wire_model(
        CommuterInfoResponse,
        raw,
        "commuter info",
        available_passenger_count_from=_primitive_json_integer(raw, "avlPrnbFrom"),
        available_passenger_count_to=_primitive_json_integer(raw, "avlPrnbTo"),
        passenger_options=passenger_options,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_trip_menu_response(raw: Mapping[str, object]) -> TripMenuResponse:
    _validate_envelope(raw)
    items = []
    for item in _rows(raw, "menuList"):
        contents = tuple(
            wire_model(
                TripMenuContent,
                row,
                "trip menu content",
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(row, "passData"), station_selection_key="h_seiect_station"
                ),
                raw=row,
            )
            for row in _rows(item, "contList")
        )
        items.append(wire_model(TripMenuItem, item, "trip menu item", contents=contents, raw=item))
    return wire_model(TripMenuResponse, raw, "trip menu", items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_product_reservation_list_response(raw: Mapping[str, object]) -> ProductReservationListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductReservationListResponse(**_response_fields(raw))
    return wire_model(
        ProductReservationListResponse,
        main,
        "product reservation list",
        items=wire_models(ProductReservation, _rows(main, "entity"), "product reservation"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_product_detail_response(raw: Mapping[str, object]) -> ProductDetailResponse:
    _validate_envelope(raw)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductDetailResponse(**_response_fields(raw))
    names = (_optional_scalar_string(item, "strGdConsItmNm") for item in _rows(main, "entityOne"))
    return wire_model(
        ProductDetailResponse,
        main,
        "product detail",
        included_item_names=tuple(name for name in names if name is not None),
        detail_raw=main,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_card_purchase_response(raw: Mapping[str, object]) -> DiscountCardPurchaseResponse:
    data = _response_mapping(raw)
    return wire_model(DiscountCardPurchaseResponse, data, "discount card purchase", **_response_fields(data))


@_preserve_read_raw
def parse_product_cancel_response(raw: Mapping[str, object]) -> ProductCancelResponse:
    data = _response_mapping(raw)
    return wire_model(ProductCancelResponse, data, "product cancel", **_response_fields(data))
