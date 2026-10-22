# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 응답을 읽습니다. 공항버스는 정확한 SUCC를 요구하며 null 목록의 허용은 라이브러리 정책입니다(TResidualSeatsResearchOut.java:79)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..._core.parsing import (
    _inventory_ratio,
    _model_response_fields,
    _nullable_scalar_fields,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _row,
    _rows,
    _strict_scalar_string,
    _validate_strict_read_envelope,
)
from ...errors import KorailProtocolError
from ..common.models import BaseKorailResponse
from ..trains.models import SeatWindow
from .models import (
    LimousineSchedule,
    LimousineScheduleResponse,
    LimousineSeat,
    LimousineSeatInventoryResponse,
    LimousineStop,
    MaasMenuItem,
    MaasMenuListResponse,
    MaasServiceDetail,
    MaasServiceDetailInfo,
    MaasServiceDetailListResponse,
)


def _required_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(f"KORAIL {context} field {key} must be a list")
    return value


def _require_exact_success(response: BaseKorailResponse) -> None:
    if response.str_result != "SUCC":
        raise KorailProtocolError("KORAIL limousine read strResult must be exact SUCC")


@_preserve_read_raw
def parse_limousine_stops(response: BaseKorailResponse) -> tuple[LimousineStop, ...]:
    """이름·코드 목록의 순서를 유지합니다. 잘못된 짝을 만들거나 일부 행을 버리지 않습니다."""
    _require_exact_success(response)
    names = _required_list(response.raw, "app.limousine.stationNm", "limousine stops")
    codes = _required_list(response.raw, "app.limousine.stationCd", "limousine stops")
    if len(names) != len(codes):
        raise KorailProtocolError("KORAIL limousine stop names and codes must have the same length")
    stops = []
    for name, code in zip(names, codes, strict=True):
        row = {"name": name, "code": code}
        name = _strict_scalar_string(row, "name", "limousine stop")
        code = _strict_scalar_string(row, "code", "limousine stop")
        if not name or not name.strip() or not code or not code.strip():
            raise KorailProtocolError("KORAIL limousine stop name and code must not be empty")
        stops.append(LimousineStop(code=code, name=name))
    if len({stop.code for stop in stops}) != len(stops) or len({stop.name for stop in stops}) != len(stops):
        raise KorailProtocolError("KORAIL limousine stop names and codes must be unambiguous")
    return tuple(stops)


_SCHEDULE_FIELDS = {
    "arrival_date": "arvDt",
    "arrival_station_code": "arvRsStnCd",
    "arrival_run_order": "arvStnRunOrdr",
    "arrival_time": "arvTm",
    "transfer_division_code": "chtnDvCd",
    "departure_date": "dptDt",
    "departure_station_code": "dptRsStnCd",
    "departure_run_order": "dptStnRunOrdr",
    "departure_time": "dptTm",
    "general_remaining_seat_count": "gnrmRestSeatNum",
    "delay_minutes": "ocurDlayTnum",
    "free_remaining_seat_count": "restFresNum",
    "standing_remaining_seat_count": "restStndNum",
    "run_date": "runDt",
    "special_remaining_seat_count": "sprmRestSeatNum",
    "train_class_code": "stlbTrnClsfCd",
    "service_code": "trnGpCd",
    "train_no": "trnNo",
    # 속성 ymsAplFlgYMS(ScdlQryOutTrain.java:48-49)와 전송 키를 구분합니다. serializer 이름은
    # 보호됨(ScdlQryOutTrain$$serializer.java:35-55). ymsAplFlg 전송 키는 라이브 관측에 근거합니다.
    "yms_application_flag": "ymsAplFlg",
}
#: 선택 스칼라. trnOrdrNo 는 속성 선언만 확인돼 실서버 검증 못 함입니다(ScdlQryOutTrain.java:48). rcvdPrc 의 선언(ScdlQryOutTrain.java:40)과
#: 날짜 있는 359행 관측은 LimousineSchedule.received_price 설명 참고.
_SCHEDULE_ADDED_FIELDS = {
    "train_order_no": "trnOrdrNo",
    "received_price": "rcvdPrc",
}


@_preserve_read_raw
def parse_limousine_schedule_response(
    response: BaseKorailResponse,
) -> LimousineScheduleResponse:
    _require_exact_success(response)
    raw = response.raw
    schedules = []
    rows = [] if raw.get("trainList") is None else _required_list(raw, "trainList", "limousine schedule")
    for value in rows:
        row = _row(value, "limousine schedule trainList")
        schedules.append(
            LimousineSchedule(
                **_nullable_scalar_fields(row, _SCHEDULE_FIELDS, "limousine schedule"),
                **{
                    name: _optional_scalar_string(row, wire, "limousine schedule")
                    for name, wire in _SCHEDULE_ADDED_FIELDS.items()
                },
                raw=row,
            )
        )
    return LimousineScheduleResponse(
        following_page_extension=_optional_scalar_string(
            raw,
            "fllwPgExt",
            "limousine schedule",
        ),
        long_short_division_code=_optional_scalar_string(
            raw,
            "lgtmShtmDvCd",
            "limousine schedule",
        ),
        schedules=tuple(schedules),
        **_model_response_fields(response),
    )


_SEAT_FIELDS = {
    "direction_attribute_code": "dir_seat_att_cd",
    "other_attribute_code": "etc_seat_att_cd",
    "integrated_message": "intg_msg",
    "integrated_message_code": "intg_msg_cd",
    "requested_attribute_code": "rq_seat_att_cd",
    "sale_possible_flag": "sale_psb_flg",
    "seat_no": "seat_no",
    "specification": "seat_spec",
    "sequence_no": "sqr_no",
    "visual_message_division_code": "vz_msg_dv_cd",
}


@_preserve_read_raw
def parse_limousine_seat_inventory_response(
    response: BaseKorailResponse,
) -> LimousineSeatInventoryResponse:
    """공항버스 좌석 재고를 읽습니다. seatList 생략·null 은 빈 목록, 비목록·비객체 행은 오류입니다. 일반 좌석 재고와 DTO 를
    공유합니다(NetworkApi.java:271,741). layout_type 은 문자열·정수를 허용합니다."""
    _require_exact_success(response)
    raw = response.raw
    seats = []
    # seatList 누락 기본값은 emptyList()(TResidualSeatsResearchOut.java:79). null 허용 근거는 아닙니다.
    for value in (
        _required_list(raw, "seatList", "limousine seat inventory") if raw.get("seatList") is not None else []
    ):
        row = _row(value, "limousine seat inventory seatList")
        seats.append(
            LimousineSeat(
                **_nullable_scalar_fields(row, _SEAT_FIELDS, "limousine seat inventory"),
                raw=row,
            )
        )
    window_value = raw.get("windowList")
    windows = []
    for value in window_value if isinstance(window_value, list) else ():
        if not isinstance(value, Mapping):
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
    return LimousineSeatInventoryResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "car_type_code": "car_tp_cd",
                "car_no": "scar_no",
                "seat_arrangement_code": "seat_ary_cd",
            },
            "limousine seat inventory",
        ),
        layout_type=_optional_scalar_string(raw, "layout_type", "limousine seat inventory"),
        vr_banner_url=_optional_scalar_string(raw, "vrBnrUrl", "limousine seat inventory"),
        windows=tuple(windows),
        up_down_division_code=_optional_scalar_string(
            raw,
            "up_dn_dv_cd",
            "limousine seat inventory",
        ),
        seats=tuple(seats),
        **_model_response_fields(response),
    )


_MAAS_ITEM_FIELDS: dict[str, str] = {
    "active": "active",
    "additional_service_code": "addSrvDvCd",
    "app_data": "appData",
    "icon_off": "iconOff",
    "icon_on": "iconOn",
    "info": "info",
    "login_required": "login",
    "name": "name",
    "popup_image": "poppImg",
    "menu_type": "type",
    "url": "url",
}

_MAAS_RESPONSE_FIELDS: dict[str, str] = {
    "departure_elevator_url": "dElevatorUrl",
    "departure_navigation_url": "dLeadNaviUrl",
    "departure_parking_url": "dParkingLotUrl",
    "arrival_elevator_url": "aElevatorUrl",
    "arrival_bus_info_url": "aBisInfoUrl",
    "arrival_parking_url": "aParkingLotUrl",
    "arrival_baggage_transfer_robot_url": "aBggTrsfRbtUrl",
}


@_preserve_read_raw
def parse_maas_menu_list_response(
    response: BaseKorailResponse,
) -> MaasMenuListResponse:
    items: list[MaasMenuItem] = [
        MaasMenuItem(
            **_nullable_scalar_fields(row, _MAAS_ITEM_FIELDS, context="train read"),
            raw=dict(row),
        )
        for row in _rows(response.raw, "menuList")
    ]
    raw = response.raw
    return MaasMenuListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        items=tuple(items),
        **_nullable_scalar_fields(raw, _MAAS_RESPONSE_FIELDS, context="train read"),
    )


_MAAS_DETAIL_FIELDS = {
    "additional_service_division_code": "addSrvDvCd",
    "additional_service_goods_code": "addSrvGdCd",
    "additional_service_id": "addSrvId",
    "marketing_entity_id": "addSrvMrkEntId",
    "marketing_entity_name": "addSrvMrkEntNm",
    "additional_service_name": "addSrvNm",
    "progress_status_code": "addSrvPrgSttCd",
    "request_no": "addSrvReqNo",
    "passenger_reference_content": "cgPsRefAtclCont",
    "partner_reservation_no": "coptEntRsvNo",
    "delivery_close_time": "dlivPsbClsTm",
    "delivery_start_time": "dlivPsbStTm",
    "lead_message_1": "leadMsgCont1",
    "lead_message_2": "leadMsgCont2",
    "pnr_no": "pnrNo",
    "request_date": "reqDt",
    "request_quantity": "reqQnty",
    "reservation_station_code_name": "rsStnCdNm",
    "reservation_specification_url": "rsvSpecUrl",
    "usage_close_date": "utlClsDt",
    "usage_start_date": "utlStDt",
}

_MAAS_DETAIL_INFO_FIELDS = {
    "additional_service_request_no": "addSrvReqNo",
    "booking_time": "bookTime",
    "branch_name": "branchName",
    "partner_name": "coptEntName",
    "delivery_datetime": "deliveryDtm",
    "drop_times": "dropTimes",
    "dropoff_name": "dropoffName",
    "image": "image",
    "name": "name",
    "option_name": "optionName",
    "pickup_name": "pickupName",
    "pickup_place": "pickupPlace",
    "pickup_times": "pickupTimes",
    "reservation_date": "reserveDt",
    "return_datetime": "returnDttm",
    "start_datetime": "startDttm",
    "cancel_deadline_date": "strCncDlnDt",
    "cancel_return_amount": "strCncRetAmt",
    "cancel_return_fee": "strCncRetFee",
    "goods_sequence": "strGdSqno",
    "intermediate_value": "strInt11",
    "received_amount": "strRcvdAmt",
    "reservation_status_name": "strRsvSttNm",
    "reservation_passenger_name": "strRsvpsnm",
    "settlement_deadline_date": "strStlDlnDt",
    "settlement_deadline_datetime": "strStlDlnDttm",
    "settlement_status_code": "strStlSttCd",
    "settlement_status_name": "strStlSttNm",
    "total_settlement_amount": "strTotStlAmt",
    "usage_period_content": "strUtlTrmCont",
}


def _parse_add_srv_item(
    item: Mapping[str, Any],
    context: str,
    info_context: str,
) -> MaasServiceDetail:
    """MaaS 상세와 승차권의 부가서비스를 같은 모델로 읽습니다 (AddSrvItem.java:28-49, MaasDetailOut.java:27,
    MyTicketListOutReservation.java:39). @SerialName 이 없고 serializer 이름이 보호돼 있어 전송 키는 속성명에 따른 추정입니다."""
    info_raw = _optional_mapping(item, "detailInfo")
    detail_info = None
    if info_raw is not None:
        detail_info = MaasServiceDetailInfo(
            **_nullable_scalar_fields(info_raw, _MAAS_DETAIL_INFO_FIELDS, info_context),
            entity_one=tuple(_rows(info_raw, "entityOne")),
            raw=info_raw,
        )
    return MaasServiceDetail(
        **_nullable_scalar_fields(item, _MAAS_DETAIL_FIELDS, context),
        detail_info=detail_info,
        raw=item,
    )


def _optional_add_srv_item(
    data: Mapping[str, Any],
    key: str,
    item_context: str,
    info_context: str,
) -> MaasServiceDetail | None:
    """객체가 아니면 ``None``."""
    item = _optional_mapping(data, key)
    if item is None:
        return None
    return _parse_add_srv_item(item, item_context, info_context)


@_preserve_read_raw
def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for item in _rows(raw, "addSrvList"):
        details.append(_parse_add_srv_item(item, "MaaS service detail", "MaaS detail info"))
    return MaasServiceDetailListResponse(
        details=tuple(details),
        **_response_fields(raw),
    )
