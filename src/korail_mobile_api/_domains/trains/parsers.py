# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차 조회·좌석 응답을 읽습니다. 18개 좌석·역 필드만 앱 누락 기본값을 사용하며 다른 선택값은 None입니다(checks/BEHAVIOR.md)."""

from __future__ import annotations

from collections.abc import Iterator, Mapping

from ..._core.parsing import (
    _all_mappings,
    _inventory_ratio,
    _is_list,
    _is_mapping,
    _nested_rows,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _row,
    _rows,
    _typed_non_negative_integer_value,
    _typed_optional_int,
    _validate_envelope,
    _validate_strict_read_envelope,
    defaulted_str,
    wire_model,
    wire_models,
)
from ...errors import KorailProtocolError
from .models import (
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    MergeSeatsInquiryResponse,
    PhysicalSeat,
    PriceFare,
    PriceFareQuoteResponse,
    SeatAssignmentScheduleResponse,
    SeatAttribute,
    SeatCar,
    SeatCarListResponse,
    SeatInventoryResponse,
    SeatWindow,
    TrainScheduleItem,
    TrainScheduleResponse,
    TrainScheduleStop,
    TrainSearchMetadata,
    TrainSummary,
    TransferStation,
    TransferStationListResponse,
)

_SEAT = "seat inventory"
# 좌석배정·병합 행은 같은 키를 쓰지만 선언 집합이 달라, 상대 DTO 에만 선언된 키는 읽지 않고 None 으로 둡니다.
_MERGE_ONLY_KEYS = frozenset(
    {
        "h_trn_no_qb",
        "h_trn_seq",
        "shtmStndOpFlg",
        "h_dpt_tm_qb",
        "h_arv_tm_qb",
        "restStndNum",
        "h_jrny_rsv_cd",
        "h_jrny_rsv_nm",
    }
)
_SCHEDULE_ONLY_KEYS = frozenset(
    {
        "h_car_tp_nm",
        "h_gen_psrm_cl_nm",
        "h_spe_psrm_cl_nm",
        "h_spe_rsv_cd",
        "h_free_rsv_cd",
        "h_spe_rsv_nm",
        "h_free_rsv_nm",
        "h_rd_seat_map_flg",
        "h_dlay_sale_flg",
        "h_wait_rsv_flg",
        "h_rsv_psb_nm",
        "h_spe_rsv_psb_nm",
        "h_info_txt",
        "h_popup_msg",
        "h_fst_rest_seat_cnt",
        "h_yms_apl_flg",
        "h_trn_sps_flg",
    }
)


@_preserve_read_raw
def parse_train_rows(raw: Mapping[str, object]) -> list[TrainSummary]:
    """그 밖의 컨테이너·비객체 행은 오류입니다. 빈 목록만으로 직통 없음 예외를 만들지는 않습니다."""
    container = raw.get("trn_infos")
    if _is_mapping(container):
        rows = container.get("trn_info", [])
    elif _is_list(container):
        rows = container
    elif container is None:
        rows = []
    else:
        raise KorailProtocolError("KORAIL train response had invalid trn_infos")
    if not _is_list(rows):
        raise KorailProtocolError("KORAIL train response missing trn_infos.trn_info list")
    if not _all_mappings(rows):
        raise KorailProtocolError("KORAIL train response contained a non-object row")
    return [TrainSummary.from_raw(dict(row)) for row in rows]


@_preserve_read_raw
def parse_train_search_metadata(raw: Mapping[str, object]) -> TrainSearchMetadata:
    """페이지 커서와 조회 조건을 읽습니다. h_merge_rsv_psb_flg 는 병합 조회 DTO 의 필드라 읽지 않습니다."""
    return wire_model(TrainSearchMetadata, raw, "train search", raw=dict(raw))


@_preserve_read_raw
def parse_train_schedule_response(raw: Mapping[str, object]) -> TrainScheduleResponse:
    """개별 필드는 선택값이라 서버가 빼면 ``None`` 입니다."""
    stops = wire_models(TrainScheduleStop, _rows(raw, "dlayList"), "train schedule", copy_raw=True)
    return wire_model(TrainScheduleResponse, raw, "train schedule", stops=stops, **_response_fields(raw))


def _present_rows(data: Mapping[str, object], key: str, context: str) -> Iterator[Mapping[str, object]]:
    """누락은 빈 목록이고, 명시적 null·목록이 아닌 값·객체가 아닌 행은 거절합니다."""
    rows = data.get(key, [])
    if not _is_list(rows):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a list")
    return (_row(row, f"{context} field {key} item") for row in rows)


@_preserve_read_raw
def parse_transfer_station_list_response(raw: Mapping[str, object]) -> TransferStationListResponse:
    """환승역 목록을 읽습니다. 역 코드·이름은 앱이 누락 기본값을 쓰는 선택값이며 빈 목록 자체는 오류가 아닙니다."""
    context = "transfer station"
    stations = wire_models(TransferStation, _present_rows(raw, "chtnList", context), context, copy_raw=True)
    return TransferStationListResponse(stations=stations, **_response_fields(raw))


def _inventory_count(data: Mapping[str, object], key: str) -> int | None:
    """누락과 앱 기본값 "" 은 None 이고, 그 밖의 잘못된 값은 거절합니다."""
    value = data.get(key, "")
    if value == "":
        return None
    return _typed_non_negative_integer_value(value, key, context=_SEAT)


@_preserve_read_raw
def parse_seat_car_list_response(raw: Mapping[str, object]) -> SeatCarListResponse:
    """호차 네 예외 필드는 누락 시 앱 기본값을 쓰며 나머지 선택값은 None입니다(checks/BEHAVIOR.md)."""
    cars: list[SeatCar] = []
    for row in _nested_rows(raw, "srcar_infos", "srcar_info"):
        car_no = _inventory_count(row, "h_srcar_no")
        # seatAttInfos 누락은 앱 기본값 빈 목록이고, 명시적 null 도 빈 목록으로 읽는 것은 라이브러리 정책입니다.
        attributes = tuple(wire_model(SeatAttribute, item, _SEAT) for item in _rows(row, "seatAttInfos"))
        cars.append(
            SeatCar(
                car_no=car_no,
                remaining_seat_count=_inventory_count(row, "h_rest_seat_cnt"),
                room_class_name=defaulted_str(row, "h_psrm_cl_nm", _SEAT),
                attributes=attributes,
                room_class_code=_optional_scalar_string(row, "h_psrm_cl_cd"),
                total_seat_count=_typed_optional_int(row, "h_seat_cnt"),
            )
        )
    return wire_model(SeatCarListResponse, raw, "seat car list", cars=tuple(cars), **_response_fields(raw))


@_preserve_read_raw
def parse_seat_inventory_response(raw: Mapping[str, object]) -> SeatInventoryResponse:
    """18개 좌석·역 예외만 앱 누락 기본값을 쓰며 명시 null·오타입은 거절합니다(checks/BEHAVIOR.md)."""
    seats = tuple(wire_model(PhysicalSeat, row, _SEAT) for row in _present_rows(raw, "seatList", _SEAT))
    windows = tuple(
        SeatWindow(
            start_location_ratio=_inventory_ratio(row, "st_loc_rt"),
            close_location_ratio=_inventory_ratio(row, "cls_loc_rt"),
        )
        for row in _present_rows(raw, "windowList", _SEAT)
    )
    return wire_model(SeatInventoryResponse, raw, _SEAT, seats=seats, windows=windows, **_response_fields(raw))


@_preserve_read_raw
def parse_free_seat_car_response(raw: Mapping[str, object]) -> FreeSeatCarResponse:
    _validate_strict_read_envelope(raw)
    return wire_model(FreeSeatCarResponse, raw, "free seat car", **_response_fields(raw))


@_preserve_read_raw
def parse_guide_seat_condition_response(raw: Mapping[str, object]) -> GuideSeatConditionResponse:
    # 앱은 실패 응답의 h_msg_txt 를 안내하므로 FAIL 도 돌려줍니다.
    _validate_envelope(raw, return_all_failures=True)
    if raw.get("strResult") not in {"SUCC", "FAIL"}:
        raise KorailProtocolError("KORAIL seat guidance result must be SUCC or FAIL")
    return wire_model(GuideSeatConditionResponse, raw, "seat guidance", **_response_fields(raw))


def _schedule_items(raw: Mapping[str, object], skip: frozenset[str]) -> tuple[TrainScheduleItem, ...]:
    return tuple(
        wire_model(
            TrainScheduleItem, {k: v for k, v in row.items() if k not in skip}, "train schedule", raw=row
        )
        for row in _nested_rows(raw, "trn_infos", "trn_info")
    )


@_preserve_read_raw
def parse_seat_assignment_schedule_response(raw: Mapping[str, object]) -> SeatAssignmentScheduleResponse:
    """좌석배정 행과 열차 조회와 같은 커서·조건을 읽습니다."""
    _validate_strict_read_envelope(raw)
    return wire_model(
        SeatAssignmentScheduleResponse,
        raw,
        "seat assignment schedule",
        trains=_schedule_items(raw, _MERGE_ONLY_KEYS),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_merge_seats_inquiry_response(raw: Mapping[str, object]) -> MergeSeatsInquiryResponse:
    _validate_strict_read_envelope(raw)
    container = _optional_mapping(raw, "trn_infos") or {}
    return wire_model(
        MergeSeatsInquiryResponse,
        raw,
        "merge seats",
        merge_reservation_possible_flag=_optional_scalar_string(container, "h_merge_rsv_psb_flg"),
        intermediate_stations=wire_models(IntermediateStation, _rows(raw, "midStnList"), "merge seats"),
        trains=_schedule_items(raw, _SCHEDULE_ONLY_KEYS),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_price_fare_quote_response(raw: Mapping[str, object]) -> PriceFareQuoteResponse:
    _validate_strict_read_envelope(raw)
    fares = wire_models(PriceFare, _rows(raw, "prcList"), "price fare")
    return PriceFareQuoteResponse(fares=fares, **_response_fields(raw))
