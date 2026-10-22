# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 응답을 읽습니다. 공항버스는 정확한 SUCC를 요구하며 null 목록의 허용은 라이브러리 정책입니다."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _inventory_ratio,
    _is_list,
    _is_mapping,
    _optional_list,
    _optional_mapping,
    _optional_read_rows,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _strict_scalar_string,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from ..trains.models import SeatWindow
from .models import (
    AirportBusSchedule,
    AirportBusScheduleResponse,
    AirportBusSeat,
    AirportBusSeatInventoryResponse,
    AirportBusStop,
    MaasMenuItem,
    MaasMenuListResponse,
    MaasServiceDetail,
    MaasServiceDetailInfo,
    MaasServiceDetailListResponse,
)


def _require_exact_success(raw: Mapping[str, object]) -> None:
    if raw.get("strResult") != "SUCC":
        raise KorailProtocolError("KORAIL limousine read strResult must be exact SUCC")


@_preserve_read_raw
def parse_limousine_stops(raw: Mapping[str, object]) -> tuple[AirportBusStop, ...]:
    """이름·코드 목록의 순서를 유지합니다. 잘못된 짝을 만들거나 일부 행을 버리지 않습니다."""
    _require_exact_success(raw)
    names = raw.get("app.limousine.stationNm")
    codes = raw.get("app.limousine.stationCd")
    if not _is_list(names) or not _is_list(codes) or len(names) != len(codes):
        raise KorailProtocolError("KORAIL limousine stop names and codes must be lists of the same length")
    stops: list[AirportBusStop] = []
    for pair in ({"name": name, "code": code} for name, code in zip(names, codes, strict=True)):
        name = _strict_scalar_string(pair, "name", "limousine stop")
        code = _strict_scalar_string(pair, "code", "limousine stop")
        if not name or not name.strip() or not code or not code.strip():
            raise KorailProtocolError("KORAIL limousine stop name and code must not be empty")
        stops.append(AirportBusStop(code=code, name=name))
    if len({stop.code for stop in stops}) != len(stops) or len({stop.name for stop in stops}) != len(stops):
        raise KorailProtocolError("KORAIL limousine stop names and codes must be unambiguous")
    return tuple(stops)


@_preserve_read_raw
def parse_limousine_schedule_response(raw: Mapping[str, object]) -> AirportBusScheduleResponse:
    _require_exact_success(raw)
    schedules = wire_models(
        AirportBusSchedule, _optional_read_rows(raw, "trainList", "limousine schedule"), "limousine schedule"
    )
    return wire_model(
        AirportBusScheduleResponse, raw, "limousine schedule", schedules=schedules, **_response_fields(raw)
    )


@_preserve_read_raw
def parse_limousine_seat_inventory_response(raw: Mapping[str, object]) -> AirportBusSeatInventoryResponse:
    """seatList 생략·null 은 빈 목록, 비목록·비객체 행은 오류이고 잘못된 창문 행은 건너뜁니다."""
    _require_exact_success(raw)
    seats = wire_models(
        AirportBusSeat,
        _optional_read_rows(raw, "seatList", "limousine seat inventory"),
        "limousine seat inventory",
    )
    windows: list[SeatWindow] = []
    for value in _optional_list(raw, "windowList"):
        if not _is_mapping(value):
            continue
        try:
            windows.append(
                SeatWindow(
                    start_location_ratio=_inventory_ratio(value, "st_loc_rt"),
                    close_location_ratio=_inventory_ratio(value, "cls_loc_rt"),
                )
            )
        except (KorailProtocolError, ValueError, OverflowError):
            continue
    return wire_model(
        AirportBusSeatInventoryResponse,
        raw,
        "limousine seat inventory",
        windows=tuple(windows),
        seats=seats,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_maas_menu_list_response(raw: Mapping[str, object]) -> MaasMenuListResponse:
    items = wire_models(MaasMenuItem, _rows(raw, "menuList"), "MaaS menu", copy_raw=True)
    return wire_model(MaasMenuListResponse, raw, "MaaS menu", items=items, **_response_fields(raw))


def parse_maas_service_detail(item: Mapping[str, object]) -> MaasServiceDetail:
    """MaaS 상세와 승차권의 부가서비스를 같은 모델로 읽습니다. 앱이 전송 키를 감춰 키는 속성명에 따른 추정입니다."""
    info_raw = _optional_mapping(item, "detailInfo")
    detail_info = None
    if info_raw is not None:
        detail_info = wire_model(
            MaasServiceDetailInfo,
            info_raw,
            "MaaS detail info",
            entity_one=tuple(_rows(info_raw, "entityOne")),
            raw=info_raw,
        )
    return wire_model(MaasServiceDetail, item, "MaaS service detail", detail_info=detail_info, raw=item)


@_preserve_read_raw
def parse_maas_service_detail_list_response(raw: Mapping[str, object]) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = tuple(parse_maas_service_detail(item) for item in _rows(raw, "addSrvList"))
    return MaasServiceDetailListResponse(details=details, **_response_fields(raw))
