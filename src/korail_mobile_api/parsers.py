# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

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


def _typed_required_scalar_string(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> str:
    """Like :func:`_typed_required_string` but also accepts a JSON integer.

    Live-confirmed against production (2026-09-21, seat inventory for train
    141/KTX-산천): the server sends ``layout_type`` as a bare JSON integer
    (``2``), not the ``@SerialName("layout_type") String`` the DAO declares —
    every call fails otherwise, even though the surrounding seat rows parse
    fine. Same class of Java-``String``-sent-as-a-JSON-number inconsistency
    :func:`~korail_mobile_api.read_parsers._optional_scalar_string` already
    handles for other routes; this is the required-field counterpart.
    """
    if key not in data:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or an integer"
        )
    value = data[key]
    if isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass.
    if type(value) is int:
        return str(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string or an integer"
    )


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
_inventory_required_scalar_string = partial(
    _typed_required_scalar_string, context="seat inventory"
)
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

    ``version`` 에서 읽는 세 키가 7.0.6 ``MobilePlusMainVersion`` 이 선언하는
    필드 전부입니다 — ``MobilePlusMainVersion.java:52`` 의 역직렬화 생성자에
    ``NEWDVERSION``/``CNTAURL``/``AMESSAGE`` 세 ``@SerialName`` 만 있습니다.
    ``CNTAURL`` 은 한동안 빠져 있었는데, 앱이 업데이트 팝업의 스토어 버튼
    링크로 쓰는 값이라(``AppKt.java:1240`` → ``AppKt.java:1635`` 의
    ``StoreConfirmDialog``) 그것만 없으면 "새 버전이 있다"까지만 알고 어디로
    보낼지는 모르는 상태가 됩니다. 실서버는 같은 객체에 19개 키를 실어
    보내지만(2026-09-22 확인) 나머지 16개(``NEWAVERSION``/``NEWIVERSION``/
    ``CNT{D,I,S}URL``/``{D,I,S}MESSAGE``/``OLD*VERSION``/``AADD*MSG``)는 DTO 에
    없는 키라 일부러 읽지 않습니다 — 필요하면 ``AppDataResponse.raw`` 에
    그대로 남아 있습니다.
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
            store_url=_optional_string(version_raw, "CNTAURL"),
        )
    return AppDataResponse(
        **_response_fields(response),
        disability_certification_msg=_optional_string(
            raw,
            "disability_certification_msg",
        ),
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
    등)가 여기 담깁니다.

    7.0.6 ``TrainScheduleOut`` 의 ``h_menu_id`` 도 보존합니다.

    ``h_merge_rsv_psb_flg`` 는 더 이상 여기서 읽지 않습니다: 7.0.6
    ``TrainScheduleOutTrainInfos`` (``trn_infos`` 의 실제 DTO)는 이 키를
    선언하지 않습니다 — ``trn_info`` 하나만 멤버입니다. 이 이름의 필드는
    다른 DTO(``MergeSeatsCOutTrnInfos``)에 속하며, 여기서 읽어도 항상
    ``None`` 이 되는 죽은 읽기였습니다.
    """
    def optional(key: str) -> str | None:
        return _typed_optional_string(raw, key, context="train search metadata")

    return TrainSearchMetadata(
        job_id=optional("strJobId"),
        menu_id=optional("h_menu_id"),
        product_no=optional("h_gd_no"),
        next_page_flag=optional("h_next_pg_flg"),
        next_query_station_no=optional("h_qry_st_no_next"),
        next_train_no=optional("h_trn_no_next"),
        # The 환승 cursor pair. Both keys are declared on the 7.0.6 response
        # DTO (TrainScheduleOut.java:28,33; @SerialName list at :67), so they
        # are read on every response; they simply come back empty for a direct
        # search. The old citation b5/c.java:370-371 is a 6.5.0 leftover with
        # no 7.0.6 counterpart. Where 7.0.6 consumes them is only readable in
        # smali (jadx failed on responseTrainSchedule):
        # smali_classes5/.../TrainScheduleViewModel.smali:36806-36845 builds
        # Triple(hQryStNoNext, hPrcdTrnNoNext, hEctbTrnNoNext) for the transfer
        # form. Note the app picks that form off the echoed strJobId
        # (:35651-35698), NOT off "both halves non-empty" -- the both-non-empty
        # rule that TransferSearchResult.next_page applies is this package's
        # own, live-verified choice, documented there.
        next_preceding_train_no=optional("h_prcd_trn_no_next"),
        next_connecting_train_no=optional("h_ectb_trn_no_next"),
        result_count=optional("h_rslt_cnt"),
        notice_message=optional("h_notice_msg"),
        first_seat_count=optional("h_seat_cnt_first"),
        second_seat_count=optional("h_seat_cnt_second"),
        first_departure_time=optional("txtGoHour_first"),
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
                # StationDataOutStnItem.java:60 declares popupType as a
                # String (@SerialName("popupType") String), not an int --
                # read it as an optional string instead of coercing.
                popup_type=_typed_optional_string(
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

    역 목록이 아니라 그 목록의 버전 정보입니다. ``count``와 ``map_version``
    둘 다 비어 있지 않은 문자열이어야 하며, 하나라도 어긋나면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다. 앱은 이 값으로
    캐시한 역 목록을 다시 받을지 판단합니다.

    ``StationInfoOut.java:47`` 은 ``count`` 를 ``@SerialName("count") String``
    으로 선언합니다(``mapVersion`` 과 동일한 non-null String) — int 로
    강제 변환하지 않고 그대로 문자열로 둡니다.
    """
    raw = response.raw
    return StationInfoResponse(
        **_response_fields(response),
        count=_typed_required_string(
            raw,
            "count",
            context="station info",
            non_empty=True,
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

    라우트 선언은 ``NetworkApi.java:651-652``(``postRunDate(@FieldMap)``)입니다.

    ``runningCalendar`` 가 없거나 ``null`` 이면 빈 날짜 튜플입니다. 7.0.6 도 없는
    경우를 빈 목록으로 다룹니다 — ``RunDateOut.java:28`` 의
    ``List<RunDateOutItem> runningCalendar`` 는 키가 빠지면
    ``CollectionsKt.emptyList()`` 로 채워지고(``:57-58``, ``:71-73``) 소비 쪽은
    그래도 null 을 한 번 더 막습니다(``CacheHelper.java:82`` 의
    ``runDateOut != null && (runningCalendar = ...) != null``;
    ``NetworkRepositoryImpl.java:12413`` 은 보호된 헬퍼로 비어 있는지 검사).
    **다만 7.0.6 의 선언은 nullable 이 아니라 기본값 있는 non-null 입니다** —
    "nullable ``List``" 라던 옛 서술과 그 근거 ``C0805e.java:124`` /
    ``TrainCalendarDao:101-103`` 은 7.0.6 에 없는 6.5.0 잔재입니다. 값이 있는데
    리스트가 아닐 때만 :class:`~korail_mobile_api.errors.KorailProtocolError`
    입니다.

    행의 날짜(``runDt``)를 여기서 선택값으로 두는 것은 이 패키지의 판단입니다 —
    7.0.6 은 ``RunDateOutItem.java:37,104-105`` 에서 ``runDt`` 를 non-null
    ``String`` 으로 선언하고 키가 빠지면 AlienGuard 로 보호된 리터럴을 넣습니다
    (그 평문은 읽히지 않습니다). 생 JSON 을 파싱하는 쪽에서는 서버가 키를 빼는
    경우를 그래도 견뎌야 하므로 ``None`` 인 행이 섞일 수 있습니다. 성수기
    여부는 이 응답에서 오며
    :func:`~korail_mobile_api.netfunnel.inquiry_action` 이 그것을 봅니다.
    """
    raw = response.raw
    # A missing runningCalendar yields an empty calendar in 7.0.6 too, but by
    # a default rather than by nullability: RunDateOut.java:57-58,71-73 fill
    # the field with CollectionsKt.emptyList() when the key is absent, and
    # consumers still null-guard it (CacheHelper.java:82,
    # NetworkRepositoryImpl.java:12413). The old citations C0805e.java:124 and
    # TrainCalendarDao:101-103 are 6.5.0 leftovers absent from 7.0.6.
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
                # runDt is treated as optional here by this package's own
                # choice, not on the app's authority. 7.0.6 declares it
                # non-null with an AlienGuard-protected missing-value default
                # (RunDateOutItem.java:37,104-105) and its reader compares it
                # through a protected helper (TrainOptionViewModel.java
                # :1066-1069), so there is no 7.0.6 null-date skip to cite --
                # the old TrainCalendarDao:40-41,:89-94 / C0805e.java:140,147
                # chain is a 6.5.0 leftover with no counterpart here. Parsing
                # raw JSON still has to survive a server that omits the key,
                # so treat it as optional rather than aborting the whole
                # calendar parse.
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
                # W4 finding: the 6.5.0 rationale above (TrainCalendarDao, not
                # on disk for 7.0.6) doesn't hold for 7.0.6's RunDateOutItem --
                # its synthetic constructor supplies a compiled default ("")
                # for hldyDvCd when the key's mask bit is unset, with no
                # throwMissingFieldException for it (RunDateOutItem.java:116-
                # 119). 7.0.6 itself deserializes an absent key fine, so
                # requiring it here rejects a response shape the real app
                # accepts.
                holiday_division_code=_typed_optional_string(
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
                # W4 finding: ActualTrainScheduleOutDlay.java's synthetic
                # constructor gives stopStnNm a compiled default (bit 2 of
                # its mask) like every sibling field on this row -- 7.0.6
                # never throws for an absent value, so requiring it here
                # rejects a response 7.0.6 itself accepts.
                station_name=_typed_optional_string(
                    row,
                    "stopStnNm",
                    context="train schedule stop",
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
        # W4 finding: ActualTrainScheduleOut.java's synthetic constructor
        # gives runDt1 a compiled default (bit 4 of its mask) with no
        # throwMissingFieldException for it -- 7.0.6 deserializes an absent
        # key fine, so requiring it here rejects a response shape the real
        # app accepts.
        run_date=_typed_optional_string(
            raw,
            "runDt1",
            context="train schedule",
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
                # W4 finding: ChtnStnOutItem.java's synthetic constructor
                # gives both chtnRsStnCd (bit 8) and chtnRsStnNm (bit 16)
                # compiled defaults, same as the third field on this row
                # (chtnRsStnEngNm) which was already read as optional -- no
                # throwMissingFieldException for either, so requiring them
                # here rejects a response shape 7.0.6 itself accepts.
                station_code=_typed_optional_string(
                    row,
                    "chtnRsStnCd",
                    context="transfer station",
                ),
                station_name=_typed_optional_string(
                    row,
                    "chtnRsStnNm",
                    context="transfer station",
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
        # TrainResearchOutCarInfo.java:32 declares hSrcarNo as a String
        # (public final String hSrcarNo;), not an int. Coercing it to int
        # here loses leading zeros (e.g. "01" -> 1) -- a lossy round-trip.
        # SeatCar.car_no is kept as int anyway for ergonomics (client.py's
        # get_seat_inventory(train, car_no: int, ...) and friends depend on
        # it), but any re-send of this value elsewhere in the codebase
        # (payloads.py) MUST zero-pad it back to the original wire width or
        # it will reach the server under a different spelling than the one
        # the server assigned.
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
        # TrainResearchOut.java:27,105 -- one of the DTO's own 6 fields,
        # previously unread.
        car_count=_inventory_optional_string(raw, "h_scar_num"),
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

    ``TResidualSeatsResearchOut.java:29`` 는 ``layout_type`` 을
    ``@SerialName("layout_type") String`` 으로 선언하지만, 2026-09-21 실서버
    확인(열차 141/KTX-산천 등 15대) 결과 실제로는 JSON 정수(예: ``2``)로
    옵니다 — 문자열만 받으면 좌석 데이터가 멀쩡한데도 이 필드 하나 때문에
    모든 호출이 깨집니다. 그래서 문자열·정수 둘 다 받아 문자열로 정규화합니다
    (:func:`_typed_required_scalar_string`).
    """
    raw = response.raw
    layout_type = _inventory_required_scalar_string(raw, "layout_type")
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
