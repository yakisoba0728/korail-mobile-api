# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 응답을 읽습니다. 18개 좌석·역 필드만 앱 누락 기본값을 사용하며 다른 선택값은 None입니다(checks/BEHAVIOR.md)."""

from __future__ import annotations

from collections.abc import Mapping

from ..._core.parsing import (
    _optional_mapping,
    _preserve_read_raw,
    _response_fields,
    _row,
    _rows,
    _typed_required_string,
    _validate_envelope,
    _validate_strict_read_envelope,
    wire_model,
    wire_models,
)
from ...errors import KorailInvalidInputError, KorailProtocolError
from .models import (
    AppDataResponse,
    AppVersionInfo,
    CrewRequestListResponse,
    CrewRequestOption,
    KorailStation,
    NoticeResponse,
    ServiceStatusResponse,
    StationDataResponse,
    StationInfoResponse,
    TrainCalendarDay,
    TrainCalendarResponse,
    UuidResponse,
)


@_preserve_read_raw
def parse_app_data_response(raw: Mapping[str, object]) -> AppDataResponse:
    """봉투 없는 앱 메인 캐시를 읽습니다. version·notice 가 객체가 아니면 None 이고 나머지 키는 raw 에 둡니다."""
    response = _response_fields(raw)
    version = _optional_mapping(raw, "version")
    notice = _optional_mapping(raw, "notice")
    return wire_model(
        AppDataResponse,
        raw,
        "app data",
        version=None if version is None else wire_model(AppVersionInfo, version, "app data"),
        notice=None if notice is None else wire_model(NoticeResponse, notice, "app data", **response),
        **response,
    )


def resolve_station_name(reference: str, names: Mapping[str, str]) -> str:
    """숫자가 아니면 이미 이름이라고 보고 그대로 돌려줍니다. 빈 참조와 표에 없는 코드는 ``errors.KorailProtocolError`` 입니다."""
    value = reference.strip()
    if not value:
        raise KorailInvalidInputError("KORAIL station reference must not be empty")
    if not value.isdigit():
        return value
    try:
        return names[value]
    except KeyError as exc:
        raise KorailProtocolError(f"KORAIL station code is unknown: {value}") from exc


@_preserve_read_raw
def parse_uuid_response(raw: Mapping[str, object]) -> UuidResponse:
    """mutMrkVrfCd 를 문자열로 읽으며 없거나 비면 KorailProtocolError 입니다. 완전한 KORAIL 봉투는 요구하지 않습니다."""
    return UuidResponse(
        verification_code=_typed_required_string(raw, "mutMrkVrfCd", context="UUID response", non_empty=True),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_station_data_response(raw: Mapping[str, object]) -> StationDataResponse:
    """봉투가 없는 역 목록을 읽습니다. stns.stn 객체 목록은 필수입니다."""
    container = raw.get("stns")
    if not isinstance(container, Mapping):
        raise KorailProtocolError("KORAIL station data missing stns object")
    rows = container.get("stn")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    stations = (_row(row, "station data stns.stn item") for row in rows)
    return StationDataResponse(
        stations=wire_models(KorailStation, stations, "station", copy_raw=True),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_station_info_response(raw: Mapping[str, object]) -> StationInfoResponse:
    """역 목록의 판본을 읽습니다. count·map_version 은 키가 필수이고 빈 값과 정수도 문자열로 받습니다."""
    return wire_model(StationInfoResponse, raw, "station info", **_response_fields(raw))


@_preserve_read_raw
def parse_train_calendar_response(raw: Mapping[str, object]) -> TrainCalendarResponse:
    """runningCalendar 는 누락·null·비목록이면 비우고 객체가 아닌 행은 건너뜁니다."""
    return TrainCalendarResponse(
        days=wire_models(TrainCalendarDay, _rows(raw, "runningCalendar"), "train calendar", copy_raw=True),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_crew_request_list_response(raw: Mapping[str, object]) -> CrewRequestListResponse:
    _validate_strict_read_envelope(raw)
    items = wire_models(CrewRequestOption, _rows(raw, "prsList"), "crew request")
    return CrewRequestListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_service_status_response(raw: Mapping[str, object]) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))
