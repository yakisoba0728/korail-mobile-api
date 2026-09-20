# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""기본 조회 응답을 :mod:`korail_mobile_api.models` 의 타입으로 옮깁니다.

앱 기동 데이터, 공지, 역 목록·상세, 열차 조회 행, 운행달력, 정차역, 호차 목록,
좌석 재고를 파싱합니다. 나머지 읽기 라우트는
:mod:`korail_mobile_api.read_parsers` 에 있습니다.

각 파서는 봉투를 먼저 확인하고 그 라우트의 DAO 선언이 말하는 필드만 꺼냅니다.
원본 JSON 은 모델의 ``raw`` 에 남습니다. 역이름과 역코드의 대응은
:func:`parse_station_name_map` 과 :func:`resolve_station_name` 이 맡으며,
:class:`~korail_mobile_api.client.KorailClient` 가 그 표를 캐시합니다.
"""
from __future__ import annotations

import math
import re
from collections.abc import Mapping
from functools import partial
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
from .read_parsers import _nested_rows, _nullable_string_fields, _optional_list
from .read_parsers import _optional_string as _typed_optional_string


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


# Each response family's names for the typed helpers -- _typed_optional_string
# from read_parsers, the rest defined above -- with the context each family's
# messages say. Seat inventory accepts a blank required string and stations do
# not -- a station row without a code or a name is not a station.
_optional_string = partial(_typed_optional_string, context="cache")
_station_required_string = partial(
    _typed_required_string, context="station", non_empty=True
)
_inventory_optional_string = partial(_typed_optional_string, context="seat inventory")
_inventory_required_string = partial(_typed_required_string, context="seat inventory")
_inventory_integer_value = partial(
    _typed_non_negative_integer_value, context="seat inventory"
)
_inventory_optional_int = partial(_typed_optional_int, context="seat inventory")


def _response_fields(response: BaseKorailResponse) -> dict[str, Any]:
    return {
        "h_msg_cd": response.h_msg_cd,
        "h_msg_txt": response.h_msg_txt,
        "str_result": response.str_result,
        "raw": response.raw,
    }


def parse_app_data_response(response: BaseKorailResponse) -> AppDataResponse:
    """``prdMobilePlusMain.cache`` 를 파싱합니다.

    캐시 파일이라 KORAIL 봉투가 없습니다. 모든 필드가 선택값이므로 서버가 빼면
    ``None`` 입니다. ``version`` 이 객체로 오면 앱 업데이트 안내
    (:class:`~korail_mobile_api.models.AppVersionInfo`)이고, 객체도 ``null`` 도
    아니면 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
    """
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
        **_response_fields(response),
        disability_certification_msg=_optional_string(
            raw,
            "disability_certification_msg",
        ),
        for_seat_intg=_optional_string(raw, "forSeatIntg"),
        airport_bus_msg=_optional_string(raw, "airportBusMsg"),
        railplus_cardinfo=_optional_string(raw, "railplus_cardinfo"),
        version=version,
        notice=(
            parse_notice_response(response)
            if raw.get("notice") is not None
            else None
        ),
    )


def parse_notice_response(response: BaseKorailResponse) -> NoticeResponse:
    """공지 응답을 파싱합니다.

    게시판 아이디·게시물 일련번호·제목 셋만 꺼내며 모두 선택값입니다. 공지가
    없는 상태도 정상이라 빈 값이 오류가 아닙니다.
    """
    raw = response.raw
    nested = raw.get("notice")
    if nested is not None and not isinstance(nested, Mapping):
        raise KorailProtocolError("KORAIL cache field notice must be an object or null")
    notice_raw = nested if isinstance(nested, Mapping) else raw
    nested_notice = isinstance(nested, Mapping)
    return NoticeResponse(
        **_response_fields(response),
        board_id=_optional_string(notice_raw, "BbrdId" if nested_notice else "bbrdId"),
        post_sequence=_optional_string(
            notice_raw, "PtwtSqno" if nested_notice else "ptwtSqno"
        ),
        post_title=_optional_string(notice_raw, "PtwtTtl" if nested_notice else "ptwtTtl"),
        post_content=(
            _optional_string(notice_raw, "PtwtCont") if nested_notice else None
        ),
    )


def parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]:
    """역 목록 응답에서 역코드 → 역이름 대응표를 만듭니다.

    ``stns.stn`` 리스트가 없으면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 코드와 이름이
    둘 다 있는 행만 담으며, 쓸 만한 역이 하나도 없으면 빈 dict 가 아니라 역시
    예외입니다. :meth:`~korail_mobile_api.client.KorailClient.search_trains` 가
    역코드를 이름으로 바꾸려고 이 표를 만들어 캐시합니다.
    """
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
    """역 참조를 조회 폼에 실을 역이름으로 바꿉니다.

    숫자가 아니면 이미 이름이라고 보고 그대로 돌려줍니다. 숫자면 역코드로 보고
    ``names``(:func:`parse_station_name_map` 의 결과)에서 찾습니다. 빈 참조와
    표에 없는 코드는 :class:`~korail_mobile_api.errors.KorailProtocolError`
    입니다.
    """
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
    """조회 응답의 열차 행들을 :class:`~korail_mobile_api.models.TrainSummary` 로
    만듭니다.

    ``trn_infos`` 는 세 모양을 모두 받습니다 — ``trn_info`` 를 담은 객체, 리스트
    그 자체, ``null``(결과 없음). 그 밖의 값이거나 행이 객체가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    빈 목록 자체는 오류가 아닙니다. 직통 열차가 없다는 판정은 호출자가
    :class:`~korail_mobile_api.errors.KorailNoDirectTrainError` 로 내립니다.
    """
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
    """조회 응답에서 열차 행이 아닌 값들 — 페이지 커서와 조회 조건 — 을 꺼냅니다.

    다음 페이지 요청에 되실을 커서(``h_next_pg_flg``, ``strJobId``, ``h_gd_no``
    등)가 여기 담깁니다. 병합예약 가능 플래그(``h_merge_rsv_psb_flg``)는 최상위가
    아니라 ``trn_infos`` 안에 있어 거기서 읽습니다.

    7.0.6 ``TrainScheduleOut`` 의 ``h_menu_id`` 도 보존합니다.
    """
    def optional(key: str) -> str | None:
        return _typed_optional_string(raw, key, context="train search metadata")

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
        job_id=optional("strJobId"),
        menu_id=optional("h_menu_id"),
        product_no=optional("h_gd_no"),
        next_page_flag=optional("h_next_pg_flg"),
        next_query_station_no=optional("h_qry_st_no_next"),
        next_train_no=optional("h_trn_no_next"),
        # The 환승 cursor pair (b5/c.java:370-371). Read on every response
        # because the app reads them on every response; they simply come back
        # empty for a direct search, and TransferSearchResult.next_page applies
        # the app's both-non-empty rule.
        next_preceding_train_no=optional("h_prcd_trn_no_next"),
        next_connecting_train_no=optional("h_ectb_trn_no_next"),
        result_count=optional("h_rslt_cnt"),
        notice_message=optional("h_notice_msg"),
        first_seat_count=optional("h_seat_cnt_first"),
        second_seat_count=optional("h_seat_cnt_second"),
        first_departure_time=optional("txtGoHour_first"),
        merge_reservation_available_flag=merge_reservation_available_flag,
        raw=dict(raw),
    )


def parse_uuid_response(response: BaseKorailResponse) -> UuidResponse:
    """``ebizcross/getUUID.do`` 를 파싱합니다.

    ``mutMrkVrfCd`` 가 비어 있지 않은 문자열이어야 하고 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 이 라우트는
    KORAIL 봉투를 싣지 않습니다.
    """
    value = response.raw.get("mutMrkVrfCd")
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            "KORAIL UUID response mutMrkVrfCd must be a non-empty string"
        )
    return UuidResponse(
        **_response_fields(response),
        verification_code=value,
    )


# Field maps (attribute -> wire key) for the MAAS menu parser, in the field
# order parse_maas_menu_list_response has always used.
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


def parse_maas_menu_list_response(
    response: BaseKorailResponse,
) -> MaasMenuListResponse:
    """``copt.gdMenuLt.do`` 의 MaaS 메뉴 목록을 파싱합니다.

    ``menuList`` 는 없거나 ``null`` 이어도 되고 그때는 빈 목록입니다. 리스트가
    아니거나 행이 객체가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    각 항목은 부가서비스 코드를 가지며, 역 선택을 쓰는 항목의 그 코드가
    :meth:`~korail_mobile_api.client.KorailClient.get_maas_station_data` 의
    입력입니다.
    """
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
        items.append(
            MaasMenuItem(
                **_nullable_string_fields(row, _MAAS_ITEM_FIELDS, "MAAS menu"),
                raw=dict(row),
            )
        )
    raw = response.raw
    return MaasMenuListResponse(
        h_msg_cd=response.h_msg_cd,
        h_msg_txt=response.h_msg_txt,
        str_result=response.str_result,
        raw=raw,
        items=tuple(items),
        **_nullable_string_fields(raw, _MAAS_RESPONSE_FIELDS, "MAAS menu"),
    )


# Field map (attribute -> wire key) for the station data parser's optional
# strings, in the field order parse_station_data_response has always used.
_STATION_OPTIONAL_STRING_FIELDS: dict[str, str] = {
    "longitude": "longitude",
    "latitude": "latitude",
    "group": "group",
    "major": "major",
    "popup_message": "popupMessage",
    "popup_link_title": "popupLinkTitle",
    "popup_link_url": "popupLinkUrl",
}


def parse_station_data_response(
    response: BaseKorailResponse,
) -> StationDataResponse:
    """역 목록 응답을 파싱합니다.

    ``common.stationdata`` 와 ``EbizMaasStationList.do`` 가 같은 모양을 씁니다.
    두 라우트 모두 KORAIL 봉투를 싣지 않지만 ``stns.stn`` 리스트는 필수라서
    없으면 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    역마다 코드(``stn_cd``)와 이름(``stn_nm``)은 필수, 위경도·그룹·팝업 문구는
    선택값입니다.
    """
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
        stations.append(
            KorailStation(
                code=_station_required_string(row, "stn_cd"),
                name=_station_required_string(row, "stn_nm"),
                raw=dict(row),
                popup_type=_typed_optional_int(
                    row,
                    "popupType",
                    context="station",
                ),
                **_nullable_string_fields(
                    row,
                    _STATION_OPTIONAL_STRING_FIELDS,
                    "station",
                ),
            )
        )
    return StationDataResponse(
        **_response_fields(response),
        stations=tuple(stations),
    )


def parse_station_info_response(
    response: BaseKorailResponse,
) -> StationInfoResponse:
    """``common.stationinfo`` 를 파싱합니다.

    역 목록이 아니라 그 목록의 버전 정보입니다. ``count``(0 이상의 정수)와
    ``map_version``(비어 있지 않은 문자열) 둘 다 필수이며, 하나라도 어긋나면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 앱은 이 값으로
    캐시한 역 목록을 다시 받을지 판단합니다.
    """
    raw = response.raw
    return StationInfoResponse(
        **_response_fields(response),
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
    """``schedule.runDt`` 열차운행달력을 파싱합니다.

    ``runningCalendar`` 가 없거나 ``null`` 이면 빈 날짜 튜플입니다. 앱도 그렇게
    다룹니다 — ``makeAvailableDatesFactory`` 가 SUCC 응답에서 리스트를 null 검사
    하고(``C0805e.java:124``) ``getRunningCalendarList``
    (``TrainCalendarDao:101-103``)가 nullable ``List`` 입니다. 값이 있는데
    리스트가 아닐 때만 :class:`~korail_mobile_api.errors.KorailProtocolError`
    입니다.

    행의 날짜(``runDt``)도 선택값이라 ``None`` 인 행이 섞일 수 있습니다. 성수기
    여부는 이 응답에서 오며
    :func:`~korail_mobile_api.netfunnel.inquiry_action` 이 그것을 봅니다.
    """
    raw = response.raw
    # makeAvailableDatesFactory null-guards the list on SUCC responses
    # (C0805e.java:124: `if (isNull(list) || list.size() <= 0) { ...return; }`)
    # and getRunningCalendarList (TrainCalendarDao:101-103) is a nullable List,
    # so a missing/null runningCalendar yields an empty calendar in the app.
    # Accept absent/null as an empty day tuple; only a present non-list is a
    # genuine shape violation.
    rows = _optional_list(raw, "runningCalendar", "train calendar")
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
        **_response_fields(response),
        days=tuple(days),
    )


def parse_train_schedule_response(
    response: BaseKorailResponse,
) -> TrainScheduleResponse:
    """``research.actualTrainSchedule.do`` 의 정차역·지연 정보를 파싱합니다.

    7.0.6 DTO에서는 ``dlayList`` 가 생략되면 빈 목록입니다. 행 하나가
    정차역 하나이며 도착·출발 시각과 지연 시간이 담깁니다. 개별 필드는
    선택값이라 서버가 빼면 ``None`` 입니다.
    """
    raw = response.raw
    rows = raw.get("dlayList", [])
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL train schedule field dlayList must be a list")
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
    def optional(key: str) -> str | None:
        return _typed_optional_string(raw, key, context="train schedule")

    return TrainScheduleResponse(
        **_response_fields(response),
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
        # by the app. runDt1 stays required because its consumer uses it
        # unguarded (convertFormat(runDt1)); msgCont is read as optional above,
        # and a response without it parses to None.
        train_no=optional("trnNo1"),
        special_train_flag=optional("trnSpsFlg"),
        up_down_division_code=optional("upDnDvCd"),
    )


def parse_transfer_station_list_response(
    response: BaseKorailResponse,
) -> TransferStationListResponse:
    """``qry.chtnStn.do`` 의 환승역 목록을 파싱합니다.

    ``chtnList`` 는 필수 리스트이고 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 역마다 코드와
    이름이 필수입니다. 빈 리스트는 그 구간에 환승역이 없다는 뜻이며 오류가
    아닙니다.
    """
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
        **_response_fields(response),
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


def _inventory_required_int(
    data: Mapping[str, Any],
    key: str,
) -> int:
    return _inventory_integer_value(data.get(key), key)


def parse_seat_car_list_response(
    response: BaseKorailResponse,
) -> SeatCarListResponse:
    """``research.TrainResearch`` 의 호차 목록을 파싱합니다.

    ``srcar_infos`` 는 없거나 ``null`` 이어도 되고 그때는 빈 목록입니다. 객체면
    ``srcar_info`` 를 읽으며, 그 값이 리스트도 ``null`` 도 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    호차마다 좌석 속성(유아동반·휠체어 등) 목록이 함께 오고, 그 호차번호가
    :meth:`~korail_mobile_api.client.KorailClient.get_seat_inventory` 의
    입력입니다.
    """
    raw = response.raw
    rows = _nested_rows(raw, "srcar_infos", "srcar_info", "seat inventory")
    cars: list[SeatCar] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL seat car list contained a non-object row"
            )
        car_no = _inventory_required_int(row, "h_srcar_no")
        # SearchCarListDao.CarInfo.seatAttInfos is a nullable Gson List
        # (SearchCarListDao.java:19) and the app null-guards it before use
        # (SeatSearchActivity.java:254 -> C0804d.isNull(list) || size()==0), so a
        # null/absent list is a valid "no special-seat attributes" car. Treat it as
        # empty; only a present-but-non-list value is malformed.
        attributes_raw = _optional_list(row, "seatAttInfos", "seat inventory")
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
        **_response_fields(response),
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
    number: int | float | str
    # ``type(value) in {int, float}`` deliberately rejects bool and any other
    # int subclass; the isinstance call is redundant at runtime and is here
    # only so the type checker can narrow ``value`` for ``float()``.
    if type(value) in {int, float} and isinstance(value, (int, float)):
        number = value
    elif (
        isinstance(value, str)
        and re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", value) is not None
    ):
        number = value
    else:
        raise KorailProtocolError(
            f"KORAIL seat inventory field {key} must be numeric or an "
            "ASCII decimal string"
        )
    try:
        ratio = float(number)
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
    """``research.TResidualSeatsResearch.do`` 의 좌석 배치와 점유 상태를 파싱합니다.

    7.0.6 DTO는 ``seatList``·``windowList`` 생략 시 빈 목록이며 잔여·전체
    좌석 수 키는 선언하지 않습니다. 있으면 그대로 담고, 없으면 ``None`` 으로
    둡니다. 두 건수가 서로 모순이어도 서버가 보낸 그대로 돌려줍니다 — 읽기
    전용 재고 데이터라 서버 자신의 계수기끼리의 불일치는 호출자가 볼 서버
    이상 현상이지, 이 클라이언트가 응답을 거부할 사유가 아닙니다.

    좌석 행은 :class:`~korail_mobile_api.models.PhysicalSeat` 가 됩니다. 창문
    위치 비율은 좌석이 아니라 좌석표를 그리기 위한 값이라
    :class:`~korail_mobile_api.models.SeatWindow` 로 따로 담깁니다.
    """
    raw = response.raw
    layout_type = _inventory_required_int(raw, "layout_type")
    arrangement_code = _inventory_required_string(raw, "seat_ary_cd")
    remaining_count = _inventory_optional_int(
        raw,
        "seat_remain_count",
    )
    total_count = _inventory_optional_int(
        raw,
        "seat_total_count",
    )

    seat_rows = (
        _inventory_required_list(raw, "seatList") if "seatList" in raw else []
    )
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

    window_rows = (
        _inventory_required_list(raw, "windowList") if "windowList" in raw else []
    )
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
        **_response_fields(response),
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
