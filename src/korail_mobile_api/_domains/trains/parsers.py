# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차 조회·좌석 응답을 읽습니다. 18개 좌석·역 필드만 앱 누락 기본값을 사용하며 다른 선택값은 None입니다(checks/BEHAVIOR.md)."""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import Any

from ..._core.parsing import (
    _inventory_ratio,
    _model_response_fields,
    _nested_rows,
    _nullable_scalar_fields,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _typed_defaulted_string,
    _typed_non_negative_integer_value,
    _typed_optional_int,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from ...errors import KorailProtocolError
from ..common.models import BaseKorailResponse
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

_inventory_string = partial(_typed_defaulted_string, context="seat inventory")
_inventory_optional_int = _typed_optional_int


@_preserve_read_raw
def parse_train_rows(raw: Mapping[str, Any]) -> list[TrainSummary]:
    """그 밖의 컨테이너·비객체 행은 오류입니다. 빈 목록만으로 직통 없음 예외를 만들지는 않습니다."""
    container = raw.get("trn_infos")
    if isinstance(container, Mapping):
        rows = container.get("trn_info", [])
    elif isinstance(container, list):
        rows = container
    elif container is None:
        rows = []
    else:
        raise KorailProtocolError("KORAIL train response had invalid trn_infos")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL train response missing trn_infos.trn_info list")
    if any(not isinstance(row, Mapping) for row in rows):
        raise KorailProtocolError("KORAIL train response contained a non-object row")
    return [TrainSummary.from_raw(dict(row)) for row in rows]


@_preserve_read_raw
def parse_train_search_metadata(
    raw: Mapping[str, Any],
) -> TrainSearchMetadata:
    """페이지 커서와 조회 조건을 읽습니다. h_merge_rsv_psb_flg 는 다른 DTO 의 필드입니다 (TrainScheduleOutTrainInfos.java:25-26,
    MergeSeatsCOutTrnInfos.java:25-26,85)."""

    def optional(key: str) -> str | None:
        return _optional_scalar_string(raw, key)

    return TrainSearchMetadata(
        job_id=optional("strJobId"),
        menu_id=_optional_scalar_string(raw, "h_menu_id"),
        product_no=optional("h_gd_no"),
        next_page_flag=optional("h_next_pg_flg"),
        next_query_station_no=optional("h_qry_st_no_next"),
        next_train_no=optional("h_trn_no_next"),
        # 환승 커서 선언: TrainScheduleOut.java:28,33,67. 소비 메서드는 jadx 복원 실패로 앱의 선택 조건을 여기서 확정하지 않습니다.
        next_preceding_train_no=optional("h_prcd_trn_no_next"),
        next_connecting_train_no=optional("h_ectb_trn_no_next"),
        result_count=optional("h_rslt_cnt"),
        notice_message=optional("h_notice_msg"),
        first_seat_count=optional("h_seat_cnt_first"),
        second_seat_count=optional("h_seat_cnt_second"),
        first_departure_time=optional("txtGoHour_first"),
        agreement_text=optional("h_agree_txt"),
        remaining_seat_count=optional("h_rest_seat_cnt"),
        raw=dict(raw),
    )


@_preserve_read_raw
def parse_train_schedule_response(
    response: BaseKorailResponse,
) -> TrainScheduleResponse:
    """개별 필드는 선택값이라 서버가 빼면 ``None`` 입니다."""
    raw = response.raw
    stops: list[TrainScheduleStop] = [
        TrainScheduleStop(
            **_nullable_scalar_fields(
                row,
                {
                    "station_code": "stopRsStnCd",
                    # stopStnNm 은 누락 시 기본값을 사용하는 필드입니다(ActualTrainScheduleOutDlay.java:71-76).
                    "station_name": "stopStnNm",
                    "station_construction_order": "stnConsOrdr",
                    "run_order": "runOrdr",
                },
            ),
            # ActualTrainScheduleOutDlay.java:30 — 앱 DTO 는 String("001" 등)입니다.
            actual_arrival_delay_count=_optional_scalar_string(row, "actArvDlayTnum"),
            **_nullable_scalar_fields(
                row,
                {
                    "actual_arrival_date": "actArvDt",
                    "actual_arrival_time": "actArvTm",
                    "actual_departure_date": "actDptDt",
                    "actual_departure_time": "actDptTm",
                    "planned_arrival_date": "arvDt",
                    "planned_arrival_time": "arvTm",
                    "planned_departure_date": "dptDt",
                    "planned_departure_time": "dptTm",
                    "delay_fare_return_division_code": "dlayFareRetDvCd",
                    "delay_fare_return_division_name": "dlayFareRetDvCdNm",
                    "solo_operation_delay_flag": "dlaySoloOprFlg",
                    "detour_driver_delay_count": "dturDrvDlayTnum",
                    "expected_arrival_delay_count": "expnArvDlayTnum",
                    "expected_departure_delay_count": "expnDptDlayTnum",
                    "regular_flag": "rgulFlg",
                    "service_flag": "saodFlg",
                },
            ),
            raw=dict(row),
        )
        for row in _rows(raw, "dlayList")
    ]

    def optional(key: str) -> str | None:
        return _optional_scalar_string(raw, key)

    return TrainScheduleResponse(
        **_model_response_fields(response),
        delay_detail_reason_content=optional("dlayDtlRsnCont"),
        stops=tuple(stops),
        delay_station_construction_order=optional("dlayStnConsOrdr"),
        integrated_message_code=optional("intgMsgCd"),
        message_code=optional("msgCd"),
        message_content=optional("msgCont"),
        message_text=optional("msgTxt"),
        origin_station_code=optional("orgRsStnCd"),
        origin_station_name=optional("orgRsStnNm"),
        route_code=optional("routCd"),
        route_name=optional("routNm"),
        # runDt1 은 누락 시 기본값을 사용하는 필드입니다(ActualTrainScheduleOut.java:75-80).
        run_date=_optional_scalar_string(
            raw,
            "runDt1",
        ),
        run_segment_order=optional("runSegOrdr"),
        regular_sale_flag=optional("saleRgulFlg"),
        standard_train_class_code=optional("stlbTrnClsfCd"),
        terminal_station_code=optional("tmnRsStnCd"),
        terminal_station_name=optional("tmnRsStnNm"),
        train_attribute_code=optional("trnAttCd"),
        train_departure_flag=optional("trnDptFlg"),
        # 앱의 trnNo1/runDt1 은 보호된 기본값을 갖습니다(ActualTrainScheduleOut.java:38,47,78-85). 그 기본값을 재현하지 않으므로 누락은 None
        # 입니다.
        train_no=optional("trnNo1"),
        special_train_flag=optional("trnSpsFlg"),
        up_down_division_code=optional("upDnDvCd"),
    )


@_preserve_read_raw
def parse_transfer_station_list_response(
    response: BaseKorailResponse,
) -> TransferStationListResponse:
    """환승역 목록을 읽습니다. chtnList 생략은 빈 목록(ChtnStnOut.java:54-60), 명시적 null·비목록은 KorailProtocolError 입니다. 역
    코드·이름은 선택값이며 빈 목록 자체는 오류가 아닙니다."""
    raw = response.raw
    rows = raw.get("chtnList", [])
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL transfer station field chtnList must be a list")
    stations: list[TransferStation] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError("KORAIL transfer station list contained a non-object row")
        stations.append(
            TransferStation(
                # 환승역 코드·역명은 누락 시 기본값을 사용하므로 선택값으로 읽습니다(ChtnStnOutItem.java:51-61).
                station_code=_optional_scalar_string(
                    row,
                    "chtnRsStnCd",
                ),
                station_name=_optional_scalar_string(
                    row,
                    "chtnRsStnNm",
                ),
                raw=dict(row),
            )
        )
    return TransferStationListResponse(
        **_model_response_fields(response),
        stations=tuple(stations),
    )


def _inventory_required_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(f"KORAIL seat inventory field {key} must be a list")
    return value


def _inventory_count(
    data: Mapping[str, Any],
    key: str,
) -> int | None:
    """누락과 앱 기본값 "" 은 None 이고, 그 밖의 잘못된 값은 거절합니다."""
    value = data.get(key, "")
    if value == "":
        return None
    return _typed_non_negative_integer_value(value, key, context="seat inventory")


@_preserve_read_raw
def parse_seat_car_list_response(
    response: BaseKorailResponse,
) -> SeatCarListResponse:
    """호차 네 예외 필드는 누락 시 앱 기본값을 쓰며 나머지 선택값은 None입니다(TrainResearchOutCarInfo.java:59-85; checks/BEHAVIOR.md)."""
    raw = response.raw
    cars: list[SeatCar] = []
    for row in _nested_rows(raw, "srcar_infos", "srcar_info"):
        # 앱은 호차번호를 String 으로 선언합니다(TrainResearchOutCarInfo.java:32).
        car_no = _inventory_count(row, "h_srcar_no")
        # seatAttInfos 생략 시 빈 목록은 TrainResearchOutCarInfo.java:33,81-84 의 기본값입니다. 명시적 null 도 빈 목록으로 읽는 것은 라이브러리
        # 정책이며 특정 객실 종류를 증명하지 않습니다.
        attributes: list[SeatAttribute] = []
        for attribute_raw in _rows(row, "seatAttInfos"):
            attributes.append(
                SeatAttribute(
                    name=_inventory_string(attribute_raw, "seatAttNm"),
                    code=_optional_scalar_string(
                        attribute_raw,
                        "seatAttCd",
                    ),
                )
            )
        total_seat_count = _inventory_optional_int(row, "h_seat_cnt")
        remaining_seat_count = _inventory_count(row, "h_rest_seat_cnt")
        cars.append(
            SeatCar(
                car_no=car_no,
                room_class_name=_inventory_string(row, "h_psrm_cl_nm"),
                remaining_seat_count=remaining_seat_count,
                attributes=tuple(attributes),
                room_class_code=_optional_scalar_string(
                    row,
                    "h_psrm_cl_cd",
                ),
                total_seat_count=total_seat_count,
            )
        )
    return SeatCarListResponse(
        **_model_response_fields(response),
        recommended_car_no=_inventory_optional_int(
            raw,
            "h_rcmd_srcar_no",
        ),
        train_no=_optional_scalar_string(raw, "h_trn_no"),
        cars=tuple(cars),
        train_class_code=_optional_scalar_string(raw, "h_trn_clsf_cd"),
        train_group_code=_optional_scalar_string(raw, "h_trn_gp_cd"),
        # TrainResearchOut.java:27,105 의 고유 필드.
        car_count=_optional_scalar_string(raw, "h_scar_num"),
    )


@_preserve_read_raw
def parse_seat_inventory_response(
    response: BaseKorailResponse,
) -> SeatInventoryResponse:
    """18개 좌석·역 예외만 앱 누락 기본값을 쓰며 명시 null·오타입은 거절합니다(TResidualSeatsResearchOutSeat.java:62-104;
    checks/BEHAVIOR.md)."""
    raw = response.raw
    layout_type = _inventory_string(raw, "layout_type")
    arrangement_code = _inventory_string(raw, "seat_ary_cd")
    remaining_count = _inventory_optional_int(
        raw,
        "seat_remain_count",
    )
    total_count = _inventory_optional_int(
        raw,
        "seat_total_count",
    )

    seat_rows = _inventory_required_list(raw, "seatList") if "seatList" in raw else []
    seats: list[PhysicalSeat] = []
    for row in seat_rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError("KORAIL seat inventory contained a non-object seat row")
        seat_no = _inventory_string(row, "seat_no")
        seats.append(
            PhysicalSeat(
                seat_no=seat_no,
                sale_possible=_inventory_string(row, "sale_psb_flg"),
                direction_code=_inventory_string(row, "dir_seat_att_cd"),
                # etc_seat_att_cd·vz_msg_dv_cd 는 생략·null 을
                # 허용합니다(TResidualSeatsResearchOutSeat.java:79-82,94-97).
                other_attribute_code=_optional_scalar_string(row, "etc_seat_att_cd"),
                requested_attribute_code=_inventory_string(row, "rq_seat_att_cd"),
                floor=_optional_scalar_string(row, "floor"),
                specification=_inventory_string(row, "seat_spec"),
                sequence_no=_inventory_string(row, "sqr_no"),
                message_code=_inventory_string(row, "intg_msg_cd"),
                message=_inventory_string(row, "intg_msg"),
                visual_message_division_code=_optional_scalar_string(row, "vz_msg_dv_cd"),
            )
        )

    window_rows = _inventory_required_list(raw, "windowList") if "windowList" in raw else []
    windows: list[SeatWindow] = []
    for row in window_rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError("KORAIL seat inventory contained a non-object window row")
        windows.append(
            SeatWindow(
                start_location_ratio=_inventory_ratio(row, "st_loc_rt"),
                close_location_ratio=_inventory_ratio(row, "cls_loc_rt"),
            )
        )

    return SeatInventoryResponse(
        **_model_response_fields(response),
        layout_type=layout_type,
        arrangement_code=arrangement_code,
        remaining_count=remaining_count,
        total_count=total_count,
        seats=tuple(seats),
        windows=tuple(windows),
        vr_banner_url=_optional_scalar_string(raw, "vrBnrUrl"),
        car_type_code=_optional_scalar_string(raw, "car_tp_cd"),
        car_no=_inventory_optional_int(raw, "scar_no"),
        up_down_division_code=_optional_scalar_string(
            raw,
            "up_dn_dv_cd",
        ),
    )


_MERGE_SEATS_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_no_qb": "h_trn_no_qb",
    "train_sequence": "h_trn_seq",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "shuttle_standing_open_flag": "shtmStndOpFlg",
    "run_date": "h_run_dt",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_date": "h_dpt_dt",
    "arrival_date": "h_arv_dt",
    "departure_time": "h_dpt_tm",
    "departure_time_qb": "h_dpt_tm_qb",
    "arrival_time": "h_arv_tm",
    "arrival_time_qb": "h_arv_tm_qb",
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "general_reservation_code": "h_gen_rsv_cd",
    "general_reservation_name": "h_gen_rsv_nm",
    "remaining_standing_count": "restStndNum",
    "standing_reservation_code": "h_stnd_rsv_cd",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "journey_reservation_code": "h_jrny_rsv_cd",
    "journey_reservation_name": "h_jrny_rsv_nm",
}

_TRAIN_SCHEDULE_OUT_TRAIN_FIELDS: dict[str, str] = {
    "train_no": "h_trn_no",
    "train_group_code": "h_trn_gp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "run_date": "h_run_dt",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "departure_run_order": "h_dpt_stn_run_ordr",
    "arrival_run_order": "h_arv_stn_run_ordr",
    "car_type_name": "h_car_tp_nm",
    "general_room_name": "h_gen_psrm_cl_nm",
    "special_room_name": "h_spe_psrm_cl_nm",
    "general_reservation_code": "h_gen_rsv_cd",
    "special_reservation_code": "h_spe_rsv_cd",
    "free_seat_reservation_code": "h_free_rsv_cd",
    "standing_reservation_code": "h_stnd_rsv_cd",
    # 네 개의 *_rsv_nm — TrainScheduleOutTrainInfo.java:1228/1380/1344/1196 이 코드 짝과 나란히 선언하며, 전송에 '예약하기'/'역발매중' 같은
    # 값으로 옵니다(: menu_id='A1','A2' 각 10행).
    "general_reservation_name": "h_gen_rsv_nm",
    "standing_reservation_name": "h_stnd_rsv_nm",
    "special_reservation_name": "h_spe_rsv_nm",
    "free_seat_reservation_name": "h_free_rsv_nm",
    "seat_map_flag": "h_rd_seat_map_flg",
    "delay_sale_flag": "h_dlay_sale_flg",
    "wait_reservation_flag": "h_wait_rsv_flg",
    "reservation_possible_name": "h_rsv_psb_nm",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "info_text": "h_info_txt",
    "popup_message": "h_popup_msg",
    # TrainScheduleOutTrainInfo.java:1204,1364,1468,1480.
    "standard_remaining_seat_count": "h_std_rest_seat_cnt",
    "first_remaining_seat_count": "h_fst_rest_seat_cnt",
    "merge_target_flag": "h_yms_apl_flg",
    "train_suspended_flag": "h_trn_sps_flg",
}


@_preserve_read_raw
def parse_free_seat_car_response(
    raw: Mapping[str, Any],
) -> FreeSeatCarResponse:
    _validate_strict_read_envelope(raw)
    return FreeSeatCarResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "title": "fresTtl",
                "car_no": "fresScarNo",
                "content": "fresCont",
            },
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_guide_seat_condition_response(
    raw: Mapping[str, Any],
) -> GuideSeatConditionResponse:
    # 앱은 실패 응답의 h_msg_txt를 안내합니다(TrainOptionViewModel.java:290-300).
    _validate_envelope(raw, return_all_failures=True)
    if raw.get("strResult") not in {"SUCC", "FAIL"}:
        raise KorailProtocolError("KORAIL seat guidance result must be SUCC or FAIL")
    # 실서버 검증 못 함. timeStamp 는 속성명(GuideSeatCndOut.java:29). 보호된 descriptor 의 9자 길이는 평문을 증명하지
    # 않습니다(GuideSeatCndOut$$serializer.java:39).
    return GuideSeatConditionResponse(
        time_stamp=_optional_integer(raw, "timeStamp"),
        **_response_fields(raw),
    )


def _parse_train_schedule_item(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
) -> TrainScheduleItem:
    return TrainScheduleItem(
        **_nullable_scalar_fields(raw, field_map),
        raw=raw,
    )


def _parse_train_schedule_container(
    raw: Mapping[str, Any],
    field_map: Mapping[str, str],
    *,
    read_merge_flag: bool,
) -> tuple[str | None, tuple[TrainScheduleItem, ...]]:
    """병합 플래그는 MergeSeatsCOutTrnInfos.java:25-26,85 에만 선언되며, TrainScheduleOutTrainInfos.java:25-26,78 은
    trn_info 만 선언합니다."""
    container = _optional_mapping(raw, "trn_infos")
    if container is None:
        return None, ()
    merge_flag = _optional_scalar_string(container, "h_merge_rsv_psb_flg") if read_merge_flag else None
    trains = tuple(_parse_train_schedule_item(value, field_map) for value in _rows(container, "trn_info"))
    return merge_flag, trains


@_preserve_read_raw
def parse_seat_assignment_schedule_response(
    raw: Mapping[str, Any],
) -> SeatAssignmentScheduleResponse:
    """TrainScheduleOut.java:67 의 커서·조건을 함께 읽습니다. h_merge_rsv_psb_flg 는 다른 응답
    컨테이너(MergeSeatsCOutTrnInfos.java:85)의 필드라 읽지 않습니다."""
    _validate_strict_read_envelope(raw)
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        _TRAIN_SCHEDULE_OUT_TRAIN_FIELDS,
        read_merge_flag=False,
    )
    return SeatAssignmentScheduleResponse(
        next_page_flag=_optional_scalar_string(
            raw,
            "h_next_pg_flg",
        ),
        merge_reservation_possible_flag=merge_flag,
        **_nullable_scalar_fields(
            raw,
            {
                "job_id": "strJobId",
                "menu_id": "h_menu_id",
                "goods_no": "h_gd_no",
                "notice_message": "h_notice_msg",
                "first_seat_count": "h_seat_cnt_first",
                "second_seat_count": "h_seat_cnt_second",
                "agreement_text": "h_agree_txt",
                "first_departure_time": "txtGoHour_first",
                "result_count": "h_rslt_cnt",
                "next_query_station_no": "h_qry_st_no_next",
                "next_train_no": "h_trn_no_next",
                "next_preceding_train_no": "h_prcd_trn_no_next",
                "next_connecting_train_no": "h_ectb_trn_no_next",
                "remaining_seat_count": "h_rest_seat_cnt",
            },
        ),
        trains=trains,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_merge_seats_inquiry_response(
    raw: Mapping[str, Any],
) -> MergeSeatsInquiryResponse:
    _validate_strict_read_envelope(raw)
    stations = []
    for station in _rows(raw, "midStnList"):
        stations.append(
            IntermediateStation(
                **_nullable_scalar_fields(
                    station,
                    {
                        "code": "rsStnCd",
                        "name": "rsStnNm",
                        "run_order": "runOrdr",
                    },
                ),
                raw=station,
            )
        )
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        _MERGE_SEATS_TRAIN_FIELDS,
        read_merge_flag=True,
    )
    return MergeSeatsInquiryResponse(
        merge_reservation_possible_flag=merge_flag,
        # runDt 는 최상위 선언(MergeSeatsCOut.java:29,112)이지만 관측 20여 회에는 없었고 행별 h_run_dt 만 있었습니다. 다른 조건에서도 없다고 일반화하지
        # 않습니다.
        run_date=_optional_scalar_string(raw, "runDt"),
        intermediate_stations=tuple(stations),
        trains=trains,
        **_response_fields(raw),
    )


_PRICE_FARE_FIELDS = {
    "journey_sequence": "jrnySqno",
    "room_class_name": "psrmClNm",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "total_amount": "sumAmt",
    "train_no": "trnNo",
}


@_preserve_read_raw
def parse_price_fare_quote_response(
    raw: Mapping[str, Any],
) -> PriceFareQuoteResponse:
    _validate_strict_read_envelope(raw)
    fares = []
    for item in _rows(raw, "prcList"):
        fares.append(
            PriceFare(
                **_nullable_scalar_fields(
                    item,
                    _PRICE_FARE_FIELDS,
                ),
                raw=item,
            )
        )
    return PriceFareQuoteResponse(
        fares=tuple(fares),
        **_response_fields(raw),
    )
