from __future__ import annotations

import math
import re
from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import (
    AppDataResponse,
    AppVersionInfo,
    BaseKorailResponse,
    KorailStation,
    MaasMenuItem,
    MaasMenuListResponse,
    NoticeResponse,
    PhysicalSeat,
    SeatAttribute,
    SeatCar,
    SeatCarListResponse,
    SeatInventoryResponse,
    SeatWindow,
    StationDataResponse,
    StationInfoResponse,
    TrainCalendarDay,
    TrainCalendarResponse,
    TrainScheduleResponse,
    TrainScheduleStop,
    TrainSearchMetadata,
    TrainSummary,
    TransferStation,
    TransferStationListResponse,
    UuidResponse,
)


def _optional_string(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL cache field {key} must be a string or null"
        )
    return value


def _typed_optional_string(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or null"
        )
    return value


def _typed_required_string(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
    non_empty: bool = False,
) -> str:
    if key not in data or not isinstance(data[key], str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string"
        )
    value = data[key]
    if non_empty and not value.strip():
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a non-empty string"
        )
    return value


def _typed_required_list(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a list"
        )
    return value


def _typed_optional_int(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    return _typed_non_negative_integer_value(
        value,
        key,
        context=context,
    )


def _typed_non_negative_integer_value(
    value: object,
    key: str,
    *,
    context: str,
) -> int:
    if type(value) is int:
        parsed = value
    elif (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        try:
            parsed = int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL {context} field {key} has an unsupported "
                "ASCII-decimal length"
            ) from exc
    else:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a non-negative integer "
            "or ASCII-decimal string"
        )
    if parsed < 0:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must not be negative"
        )
    return parsed


def parse_app_data_response(response: BaseKorailResponse) -> AppDataResponse:
    raw = response.raw
    version_raw = raw.get("version")
    if version_raw is not None and not isinstance(version_raw, Mapping):
        raise KorailProtocolError(
            "KORAIL cache field version must be an object or null"
        )
    version = None
    if isinstance(version_raw, Mapping):
        version = AppVersionInfo(
            message=_optional_string(version_raw, "AMESSAGE"),
            new_version=_optional_string(version_raw, "NEWDVERSION"),
        )
    return AppDataResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        disability_certification_msg=_optional_string(
            raw,
            "disability_certification_msg",
        ),
        for_seat_intg=_optional_string(raw, "forSeatIntg"),
        airport_bus_msg=_optional_string(raw, "airportBusMsg"),
        railplus_cardinfo=_optional_string(raw, "railplus_cardinfo"),
        version=version,
    )


def parse_notice_response(response: BaseKorailResponse) -> NoticeResponse:
    raw = response.raw
    return NoticeResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        board_id=_optional_string(raw, "bbrdId"),
        post_sequence=_optional_string(raw, "ptwtSqno"),
        post_title=_optional_string(raw, "ptwtTtl"),
    )


def parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]:
    container = raw.get("stns")
    rows = container.get("stn") if isinstance(container, Mapping) else None
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    names = {
        str(row.get("stn_cd")): str(row.get("stn_nm"))
        for row in rows
        if isinstance(row, Mapping) and row.get("stn_cd") and row.get("stn_nm")
    }
    if not names:
        raise KorailProtocolError(
            "KORAIL station data did not contain usable stations"
        )
    return names


def resolve_station_name(reference: str, names: Mapping[str, str]) -> str:
    value = reference.strip()
    if not value:
        raise KorailProtocolError("KORAIL station reference must not be empty")
    if not value.isdigit():
        return value
    try:
        return names[value]
    except KeyError as exc:
        raise KorailProtocolError(
            f"KORAIL station code is unknown: {value}"
        ) from exc


def parse_train_rows(raw: Mapping[str, Any]) -> list[TrainSummary]:
    container = raw.get("trn_infos")
    if isinstance(container, Mapping):
        rows = container.get("trn_info", [])
    elif isinstance(container, list):
        rows = container
    elif container is None:
        rows = []
    else:
        raise KorailProtocolError(
            "KORAIL train response had invalid trn_infos"
        )
    if not isinstance(rows, list):
        raise KorailProtocolError(
            "KORAIL train response missing trn_infos.trn_info list"
        )
    if any(not isinstance(row, Mapping) for row in rows):
        raise KorailProtocolError(
            "KORAIL train response contained a non-object row"
        )
    return [
        TrainSummary.from_raw(dict(row))
        for row in rows
    ]


def parse_train_search_metadata(
    raw: Mapping[str, Any],
) -> TrainSearchMetadata:
    optional = lambda key: _typed_optional_string(
        raw,
        key,
        context="train search metadata",
    )
    train_container = raw.get("trn_infos")
    if isinstance(train_container, Mapping):
        merge_reservation_available_flag = _typed_optional_string(
            train_container,
            "h_merge_rsv_psb_flg",
            context="train search metadata",
        )
    else:
        merge_reservation_available_flag = None
    return TrainSearchMetadata(
        # No h_menu_id: see TrainSearchMetadata. txtMenuId is a client constant.
        job_id=optional("strJobId"),
        product_no=optional("h_gd_no"),
        next_page_flag=optional("h_next_pg_flg"),
        next_query_station_no=optional("h_qry_st_no_next"),
        next_train_no=optional("h_trn_no_next"),
        result_count=optional("h_rslt_cnt"),
        first_seat_count=optional("h_seat_cnt_first"),
        second_seat_count=optional("h_seat_cnt_second"),
        first_departure_time=optional("txtGoHour_first"),
        merge_reservation_available_flag=merge_reservation_available_flag,
        raw=dict(raw),
    )


def _station_optional_string(row: Mapping[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL station field {key} must be a string or null"
        )
    return value


def _station_required_string(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            f"KORAIL station field {key} must be a non-empty string"
        )
    return value


def parse_uuid_response(response: BaseKorailResponse) -> UuidResponse:
    value = response.raw.get("mutMrkVrfCd")
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            "KORAIL UUID response mutMrkVrfCd must be a non-empty string"
        )
    return UuidResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=response.raw,
        verification_code=value,
    )


def _maas_optional_string(
    data: Mapping[str, Any],
    key: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL MAAS menu field {key} must be a string or null"
        )
    return value


def parse_maas_menu_list_response(
    response: BaseKorailResponse,
) -> MaasMenuListResponse:
    rows = response.raw.get("menuList")
    if rows is None:
        rows = []
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL MAAS menuList must be a list or null")
    items: list[MaasMenuItem] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL MAAS menuList contained a non-object row"
            )
        raw = dict(row)
        items.append(
            MaasMenuItem(
                active=_maas_optional_string(row, "active"),
                additional_service_code=_maas_optional_string(
                    row,
                    "addSrvDvCd",
                ),
                app_data=_maas_optional_string(row, "appData"),
                icon_off=_maas_optional_string(row, "iconOff"),
                icon_on=_maas_optional_string(row, "iconOn"),
                info=_maas_optional_string(row, "info"),
                login_required=_maas_optional_string(row, "login"),
                name=_maas_optional_string(row, "name"),
                popup_image=_maas_optional_string(row, "poppImg"),
                menu_type=_maas_optional_string(row, "type"),
                url=_maas_optional_string(row, "url"),
                raw=raw,
            )
        )
    raw = response.raw
    return MaasMenuListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        items=tuple(items),
        departure_elevator_url=_maas_optional_string(raw, "dElevatorUrl"),
        departure_navigation_url=_maas_optional_string(raw, "dLeadNaviUrl"),
        departure_parking_url=_maas_optional_string(raw, "dParkingLotUrl"),
        arrival_elevator_url=_maas_optional_string(raw, "aElevatorUrl"),
        arrival_bus_info_url=_maas_optional_string(raw, "aBisInfoUrl"),
        arrival_parking_url=_maas_optional_string(raw, "aParkingLotUrl"),
        arrival_baggage_transfer_robot_url=_maas_optional_string(
            raw,
            "aBggTrsfRbtUrl",
        ),
    )


def parse_station_data_response(
    response: BaseKorailResponse,
) -> StationDataResponse:
    container = response.raw.get("stns")
    if not isinstance(container, Mapping):
        raise KorailProtocolError("KORAIL station data missing stns object")
    rows = container.get("stn")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    stations: list[KorailStation] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL station data contained a non-object row"
            )
        raw = dict(row)
        stations.append(
            KorailStation(
                code=_station_required_string(row, "stn_cd"),
                name=_station_required_string(row, "stn_nm"),
                longitude=_station_optional_string(row, "longitude"),
                latitude=_station_optional_string(row, "latitude"),
                raw=raw,
                group=_station_optional_string(row, "group"),
                major=_station_optional_string(row, "major"),
                popup_type=_typed_optional_int(
                    row,
                    "popupType",
                    context="station",
                ),
                popup_message=_station_optional_string(
                    row,
                    "popupMessage",
                ),
                popup_link_title=_station_optional_string(
                    row,
                    "popupLinkTitle",
                ),
                popup_link_url=_station_optional_string(
                    row,
                    "popupLinkUrl",
                ),
            )
        )
    return StationDataResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=response.raw,
        stations=tuple(stations),
    )


def parse_station_info_response(
    response: BaseKorailResponse,
) -> StationInfoResponse:
    raw = response.raw
    return StationInfoResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        count=_typed_non_negative_integer_value(
            raw.get("count"),
            "count",
            context="station info",
        ),
        map_version=_typed_required_string(
            raw,
            "map_version",
            context="station info",
            non_empty=True,
        ),
    )


def parse_train_calendar_response(
    response: BaseKorailResponse,
) -> TrainCalendarResponse:
    raw = response.raw
    # makeAvailableDatesFactory null-guards the list on SUCC responses
    # (C0805e.java:124: `if (isNull(list) || list.size() <= 0) { ...return; }`)
    # and getRunningCalendarList (TrainCalendarDao:101-103) is a nullable List,
    # so a missing/null runningCalendar yields an empty calendar in the app.
    # Accept absent/null as an empty day tuple; only a present non-list is a
    # genuine shape violation.
    raw_rows = raw.get("runningCalendar")
    if raw_rows is None:
        rows: list[Any] = []
    elif isinstance(raw_rows, list):
        rows = raw_rows
    else:
        raise KorailProtocolError(
            "KORAIL train calendar field runningCalendar must be a list"
        )
    days: list[TrainCalendarDay] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL train calendar contained a non-object row"
            )
        days.append(
            TrainCalendarDay(
                # runDt is nullable: getDateStr() (TrainCalendarDao:40-41)
                # returns the raw field, compareTo null-guards it (:89-94), and
                # makeAvailableDatesFactory gates use behind
                # !TextUtils.isEmpty(dateStr) (C0805e.java:140,147) — a null-date
                # row is silently skipped, never NPEing. So treat it as optional
                # rather than aborting the whole calendar parse.
                run_date=_typed_optional_string(
                    row,
                    "runDt",
                    context="train calendar",
                ),
                # bizDdStgCd is null-guarded by isPeakSeason()
                # (N.notNullEqual(this.bizDdStgCd,"5"), TrainCalendarDao:68-70),
                # so the app tolerates a null/absent value here.
                business_day_stage_code=_typed_optional_string(
                    row,
                    "bizDdStgCd",
                    context="train calendar",
                ),
                # dayDvCd has no accessor in TrainCalendarDao, so a
                # null/absent value never reaches app code.
                day_division_code=_typed_optional_string(
                    row,
                    "dayDvCd",
                    context="train calendar",
                ),
                # hldyDvCd stays required: isHoliday() calls
                # this.hldyDvCd.isEmpty() (TrainCalendarDao:60-62) with no
                # null-guard, so the app itself NPEs on a null value.
                holiday_division_code=_typed_required_string(
                    row,
                    "hldyDvCd",
                    context="train calendar",
                ),
                # saleDdDvCd is only read via constant.equals(this.saleDdDvCd)
                # in isForSaleDate() (TrainCalendarDao:52-54), which is
                # null-safe, so a null/absent value is tolerated.
                sale_day_division_code=_typed_optional_string(
                    row,
                    "saleDdDvCd",
                    context="train calendar",
                ),
                # Every *TrnOpFlg accessor is BOOL_YES.equals(this.xTrnOpFlg)
                # (TrainCalendarDao:44-82), null-safe and returning false, so
                # the app tolerates null/absent flags our parser must not reject.
                a_train_operation_flag=_typed_optional_string(
                    row,
                    "aTrnOpFlg",
                    context="train calendar",
                ),
                d_train_operation_flag=_typed_optional_string(
                    row,
                    "dTrnOpFlg",
                    context="train calendar",
                ),
                g_train_operation_flag=_typed_optional_string(
                    row,
                    "gTrnOpFlg",
                    context="train calendar",
                ),
                o_train_operation_flag=_typed_optional_string(
                    row,
                    "oTrnOpFlg",
                    context="train calendar",
                ),
                s_train_operation_flag=_typed_optional_string(
                    row,
                    "sTrnOpFlg",
                    context="train calendar",
                ),
                v_train_operation_flag=_typed_optional_string(
                    row,
                    "vTrnOpFlg",
                    context="train calendar",
                ),
                x_train_operation_flag=_typed_optional_string(
                    row,
                    "xTrnOpFlg",
                    context="train calendar",
                ),
                raw=dict(row),
            )
        )
    return TrainCalendarResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        days=tuple(days),
    )


def parse_train_schedule_response(
    response: BaseKorailResponse,
) -> TrainScheduleResponse:
    raw = response.raw
    rows = _typed_required_list(
        raw,
        "dlayList",
        context="train schedule",
    )
    stops: list[TrainScheduleStop] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL train schedule contained a non-object stop"
            )
        stops.append(
            TrainScheduleStop(
                station_code=_typed_optional_string(
                    row,
                    "stopRsStnCd",
                    context="train schedule stop",
                ),
                station_name=_typed_required_string(
                    row,
                    "stopStnNm",
                    context="train schedule stop",
                    non_empty=True,
                ),
                station_construction_order=_typed_optional_string(
                    row,
                    "stnConsOrdr",
                    context="train schedule stop",
                ),
                run_order=_typed_optional_string(
                    row,
                    "runOrdr",
                    context="train schedule stop",
                ),
                actual_arrival_delay_count=_typed_optional_int(
                    row,
                    "actArvDlayTnum",
                    context="train schedule stop",
                ),
                actual_arrival_date=_typed_optional_string(
                    row,
                    "actArvDt",
                    context="train schedule stop",
                ),
                actual_arrival_time=_typed_optional_string(
                    row,
                    "actArvTm",
                    context="train schedule stop",
                ),
                actual_departure_date=_typed_optional_string(
                    row,
                    "actDptDt",
                    context="train schedule stop",
                ),
                actual_departure_time=_typed_optional_string(
                    row,
                    "actDptTm",
                    context="train schedule stop",
                ),
                planned_arrival_date=_typed_optional_string(
                    row,
                    "arvDt",
                    context="train schedule stop",
                ),
                planned_arrival_time=_typed_optional_string(
                    row,
                    "arvTm",
                    context="train schedule stop",
                ),
                planned_departure_date=_typed_optional_string(
                    row,
                    "dptDt",
                    context="train schedule stop",
                ),
                planned_departure_time=_typed_optional_string(
                    row,
                    "dptTm",
                    context="train schedule stop",
                ),
                delay_fare_return_division_code=_typed_optional_string(
                    row,
                    "dlayFareRetDvCd",
                    context="train schedule stop",
                ),
                delay_fare_return_division_name=_typed_optional_string(
                    row,
                    "dlayFareRetDvCdNm",
                    context="train schedule stop",
                ),
                solo_operation_delay_flag=_typed_optional_string(
                    row,
                    "dlaySoloOprFlg",
                    context="train schedule stop",
                ),
                detour_driver_delay_count=_typed_optional_string(
                    row,
                    "dturDrvDlayTnum",
                    context="train schedule stop",
                ),
                expected_arrival_delay_count=_typed_optional_string(
                    row,
                    "expnArvDlayTnum",
                    context="train schedule stop",
                ),
                expected_departure_delay_count=_typed_optional_string(
                    row,
                    "expnDptDlayTnum",
                    context="train schedule stop",
                ),
                regular_flag=_typed_optional_string(
                    row,
                    "rgulFlg",
                    context="train schedule stop",
                ),
                service_flag=_typed_optional_string(
                    row,
                    "saodFlg",
                    context="train schedule stop",
                ),
                raw=dict(row),
            )
        )
    optional = lambda key: _typed_optional_string(
        raw,
        key,
        context="train schedule",
    )
    return TrainScheduleResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
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
        run_date=_typed_required_string(
            raw,
            "runDt1",
            context="train schedule",
            non_empty=True,
        ),
        run_segment_order=optional("runSegOrdr"),
        regular_sale_flag=optional("saleRgulFlg"),
        standard_train_class_code=optional("stlbTrnClsfCd"),
        terminal_station_code=optional("tmnRsStnCd"),
        terminal_station_name=optional("tmnRsStnNm"),
        train_attribute_code=optional("trnAttCd"),
        train_departure_flag=optional("trnDptFlg"),
        # trnNo1 is a nullable Gson String (TrainScheduleDao.java:123) and the
        # web-view consumer null-guards it (TrainServiceInfoWebViewActivity.java
        # :200 -> if (!N.isNull(tranNo1))), so a null train number is tolerated
        # by the app. runDt1/msgCont stay required because their consumers use
        # them unguarded (convertFormat(runDt1)/msgCont.replaceAll).
        train_no=optional("trnNo1"),
        special_train_flag=optional("trnSpsFlg"),
        up_down_division_code=optional("upDnDvCd"),
    )


def parse_transfer_station_list_response(
    response: BaseKorailResponse,
) -> TransferStationListResponse:
    raw = response.raw
    rows = raw.get("chtnList")
    if not isinstance(rows, list):
        raise KorailProtocolError(
            "KORAIL transfer station field chtnList must be a list"
        )
    stations: list[TransferStation] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL transfer station list contained a non-object row"
            )
        stations.append(
            TransferStation(
                station_code=_typed_required_string(
                    row,
                    "chtnRsStnCd",
                    context="transfer station",
                    non_empty=True,
                ),
                station_name=_typed_required_string(
                    row,
                    "chtnRsStnNm",
                    context="transfer station",
                    non_empty=True,
                ),
                raw=dict(row),
            )
        )
    return TransferStationListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        stations=tuple(stations),
    )


def _inventory_required_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a list"
        )
    return value


def _inventory_optional_list(
    data: Mapping[str, Any],
    key: str,
) -> list[Any]:
    # SearchCarListDao.CarInfo.seatAttInfos is a nullable Gson List
    # (SearchCarListDao.java:19) and the app null-guards it before use
    # (SeatSearchActivity.java:254 -> C0804d.isNull(list) || size()==0), so a
    # null/absent list is a valid "no special-seat attributes" car. Treat it as
    # empty; only a present-but-non-list value is malformed.
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a list or null"
        )
    return value


def _inventory_required_string(
    data: Mapping[str, Any],
    key: str,
) -> str:
    if key not in data or not isinstance(data[key], str):
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a string"
        )
    return data[key]


def _inventory_optional_string(
    data: Mapping[str, Any],
    key: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a string or null"
        )
    return value


def _inventory_integer_value(value: object, key: str) -> int:
    if type(value) is int:
        parsed = value
    elif (
        isinstance(value, str)
        and value
        and all("0" <= char <= "9" for char in value)
    ):
        try:
            parsed = int(value)
        except ValueError as exc:
            raise KorailProtocolError(
                f"KORAIL seat inventory field {key} has an unsupported "
                "ASCII-decimal length"
            ) from exc
    else:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be a non-negative "
            "integer or ASCII-decimal string"
        )
    if parsed < 0:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must not be negative"
        )
    return parsed


def _inventory_required_int(
    data: Mapping[str, Any],
    key: str,
) -> int:
    return _inventory_integer_value(data.get(key), key)


def _inventory_optional_int(
    data: Mapping[str, Any],
    key: str,
) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    return _inventory_integer_value(value, key)


def parse_seat_car_list_response(
    response: BaseKorailResponse,
) -> SeatCarListResponse:
    raw = response.raw
    container = raw.get("srcar_infos")
    if container is None:
        rows = []
    elif isinstance(container, Mapping):
        rows_value = container.get("srcar_info")
        if rows_value is None:
            rows = []
        elif isinstance(rows_value, list):
            rows = rows_value
        else:
            raise KorailProtocolError(
                "KORAIL seat inventory field srcar_info must be a list or "
                "null"
            )
    else:
        raise KorailProtocolError(
            "KORAIL seat inventory field srcar_infos must be an object or "
            "null"
        )
    cars: list[SeatCar] = []
    car_numbers: set[int] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL seat car list contained a non-object row"
            )
        car_no = _inventory_required_int(row, "h_srcar_no")
        if car_no in car_numbers:
            raise KorailProtocolError(
                "KORAIL seat car list contained a duplicate car number"
            )
        car_numbers.add(car_no)
        attributes_raw = _inventory_optional_list(row, "seatAttInfos")
        attributes: list[SeatAttribute] = []
        for attribute_raw in attributes_raw:
            if not isinstance(attribute_raw, Mapping):
                raise KorailProtocolError(
                    "KORAIL seat attribute list contained a non-object row"
                )
            attributes.append(
                SeatAttribute(
                    name=_inventory_required_string(
                        attribute_raw,
                        "seatAttNm",
                    ),
                    code=_inventory_optional_string(
                        attribute_raw,
                        "seatAttCd",
                    ),
                )
            )
        total_seat_count = _inventory_optional_int(row, "h_seat_cnt")
        remaining_seat_count = _inventory_required_int(
            row,
            "h_rest_seat_cnt",
        )
        if (
            total_seat_count is not None
            and remaining_seat_count > total_seat_count
        ):
            raise KorailProtocolError(
                "KORAIL seat car remaining count exceeds total count"
            )
        cars.append(
            SeatCar(
                car_no=car_no,
                room_class_name=_inventory_required_string(
                    row,
                    "h_psrm_cl_nm",
                ),
                remaining_seat_count=remaining_seat_count,
                attributes=tuple(attributes),
                room_class_code=_inventory_optional_string(
                    row,
                    "h_psrm_cl_cd",
                ),
                total_seat_count=total_seat_count,
            )
        )
    return SeatCarListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        recommended_car_no=_inventory_optional_int(
            raw,
            "h_rcmd_srcar_no",
        ),
        train_no=_inventory_optional_string(raw, "h_trn_no"),
        cars=tuple(cars),
        train_class_code=_inventory_optional_string(raw, "h_trn_clsf_cd"),
        train_group_code=_inventory_optional_string(raw, "h_trn_gp_cd"),
    )


def _inventory_ratio(data: Mapping[str, Any], key: str) -> float:
    value = data.get(key)
    is_number = type(value) in {int, float}
    is_ascii_decimal = (
        isinstance(value, str)
        and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) is not None
    )
    if not is_number and not is_ascii_decimal:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be numeric or an "
            "ASCII decimal string"
        )
    try:
        ratio = float(value)
    except (OverflowError, ValueError) as exc:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be finite"
        ) from exc
    if not math.isfinite(ratio):
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be finite"
        )
    return ratio


def parse_seat_inventory_response(
    response: BaseKorailResponse,
) -> SeatInventoryResponse:
    raw = response.raw
    layout_type = _inventory_required_int(raw, "layout_type")
    arrangement_code = _inventory_required_string(raw, "seat_ary_cd")
    remaining_count = _inventory_required_int(
        raw,
        "seat_remain_count",
    )
    total_count = _inventory_required_int(
        raw,
        "seat_total_count",
    )
    if remaining_count > total_count:
        raise KorailProtocolError(
            "KORAIL seat inventory remaining count exceeds total count"
        )

    seat_rows = _inventory_required_list(raw, "seatList")
    seats: list[PhysicalSeat] = []
    for row in seat_rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL seat inventory contained a non-object seat row"
            )
        seat_no = _inventory_required_string(row, "seat_no")
        seats.append(
            PhysicalSeat(
                seat_no=seat_no,
                sale_possible=_inventory_required_string(
                    row,
                    "sale_psb_flg",
                ),
                direction_code=_inventory_required_string(
                    row,
                    "dir_seat_att_cd",
                ),
                other_attribute_code=_inventory_required_string(
                    row,
                    "etc_seat_att_cd",
                ),
                requested_attribute_code=_inventory_required_string(
                    row,
                    "rq_seat_att_cd",
                ),
                floor=_inventory_optional_string(row, "floor"),
                specification=_inventory_required_string(
                    row,
                    "seat_spec",
                ),
                sequence_no=_inventory_required_string(row, "sqr_no"),
                message_code=_inventory_required_string(
                    row,
                    "intg_msg_cd",
                ),
                message=_inventory_required_string(row, "intg_msg"),
                visual_message_division_code=_inventory_required_string(
                    row,
                    "vz_msg_dv_cd",
                ),
            )
        )

    window_rows = _inventory_required_list(raw, "windowList")
    windows: list[SeatWindow] = []
    for row in window_rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL seat inventory contained a non-object window row"
            )
        windows.append(
            SeatWindow(
                start_location_ratio=_inventory_ratio(row, "st_loc_rt"),
                close_location_ratio=_inventory_ratio(row, "cls_loc_rt"),
            )
        )

    return SeatInventoryResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        layout_type=layout_type,
        arrangement_code=arrangement_code,
        remaining_count=remaining_count,
        total_count=total_count,
        seats=tuple(seats),
        windows=tuple(windows),
        vr_banner_url=_inventory_optional_string(raw, "vrBnrUrl"),
        car_type_code=_inventory_optional_string(raw, "car_tp_cd"),
        car_no=_inventory_optional_int(raw, "scar_no"),
        up_down_division_code=_inventory_optional_string(
            raw,
            "up_dn_dv_cd",
        ),
    )
