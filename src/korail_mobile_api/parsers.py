from __future__ import annotations

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
    StationDataResponse,
    TrainSummary,
    UuidResponse,
)


def _optional_string(data: Mapping[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL cache field {key} must be a string or null"
        )
    return value


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
    return [
        TrainSummary.from_raw(dict(row))
        for row in rows
        if isinstance(row, Mapping)
    ]


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
            )
        )
    return StationDataResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=response.raw,
        stations=tuple(stations),
    )
