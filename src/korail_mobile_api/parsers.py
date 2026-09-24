# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""기본 조회 응답을 models 로 변환합니다. 나머지 조회는 read_parsers 에 있습니다.

일반 봉투 판정은 HTTP 계층에서 수행하며, 개별 파서는 전달된 응답을 읽습니다. 선택 필드는 관대하게 읽지만 역 코드·이름, 열차 행, 좌석 재고의 필수 값은 형식 오류 시
KorailProtocolError 입니다. 모든 모델이 raw 를 갖는 것은 아닙니다."""
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
from ._parsing import (
    _nested_rows,
    _nullable_string_fields,
    _optional_integer,
    _optional_scalar_string,
    _preserve_read_raw,
    _rows,
)
from ._parsing import _optional_string as _typed_optional_string


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
    """문자열·JSON 정수를 받는 필수 스칼라. bool 은 제외합니다. 2026-09-21 일반 좌석 재고에서 layout_type 정수가 관측되어 String 선언과 달리 허용합니다."""
    if key not in data:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or an integer"
        )
    value = data[key]
    if isinstance(value, str):
        return value
    # bool 을 정수 스칼라로 받지 않습니다.
    if type(value) is int:
        try:
            return str(value)
        except ValueError as exc:  # 파이썬의 정수→문자열 자릿수 한도
            raise KorailProtocolError(
                f"KORAIL {context} field {key} is an integer too long to use"
            ) from exc
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string or an integer"
    )


def _typed_optional_int(
    data: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> int | None:
    """선택 정수 — 음이 아닌 정수나 ASCII 10진 문자열이 아니면 ``None``."""
    value = _optional_integer(data, key, context)
    return value if value is not None and value >= 0 else None


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


# 좌석 재고의 필수 문자열은 빈 값도 허용하지만 역 코드·역명은 빈 값을 허용하지 않습니다.
_optional_string = _typed_optional_string
_station_required_string = partial(
    _typed_required_string, context="station", non_empty=True
)
_inventory_optional_string = _typed_optional_string
_inventory_required_string = partial(_typed_required_string, context="seat inventory")
_inventory_required_scalar_string = partial(
    _typed_required_scalar_string, context="seat inventory"
)
_inventory_optional_int = partial(_typed_optional_int, context="seat inventory")


def _response_fields(response: BaseKorailResponse) -> dict[str, Any]:
    return {
        "h_msg_cd": response.h_msg_cd,
        "h_msg_txt": response.h_msg_txt,
        "str_result": response.str_result,
        "raw": response.raw,
    }


@_preserve_read_raw
def parse_app_data_response(response: BaseKorailResponse) -> AppDataResponse:
    """봉투 없는 prdMobilePlusMain.cache 를 읽습니다. 선택 필드의 잘못된 타입은 비웁니다. version 은 MobilePlusMainVersion.java:52 의 3개
    키를 읽고 나머지는 raw 에 둡니다. 2026-09-22 라이브에는 19개 키가 있었습니다. CNTAURL 은 업데이트 버튼 URL 입니다 (AppKt.java:1240,1635)."""
    raw = response.raw
    version_raw = raw.get("version")
    version = None
    if isinstance(version_raw, Mapping):
        version = AppVersionInfo(
            message=_optional_string(version_raw, "AMESSAGE"),
            new_version=_optional_string(version_raw, "NEWDVERSION"),
            store_url=_optional_scalar_string(version_raw, "CNTAURL", "app data version"),
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
            if isinstance(raw.get("notice"), Mapping)
            else None
        ),
    )


@_preserve_read_raw
def parse_notice_response(response: BaseKorailResponse) -> NoticeResponse:
    """메인 캐시의 중첩 ``notice`` 를 파싱합니다(MobilePlusMainOut.java:57, MobilePlusMainNotice.java:52).

    게시판 아이디·게시물 일련번호·제목·본문은 모두 선택값입니다. 공지가 없는 상태도 정상입니다."""
    nested = response.raw.get("notice")
    notice_raw = nested if isinstance(nested, Mapping) else {}
    return NoticeResponse(
        **_response_fields(response),
        board_id=_optional_string(notice_raw, "BbrdId"),
        post_sequence=_optional_string(notice_raw, "PtwtSqno"),
        post_title=_optional_string(notice_raw, "PtwtTtl"),
        post_content=_optional_string(notice_raw, "PtwtCont"),
    )


@_preserve_read_raw
def parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]:
    """역코드→이름 캐시용 표. stns.stn 목록이나 사용 가능한 코드·이름 쌍이 없으면 오류입니다."""
    container = raw.get("stns")
    rows = container.get("stn") if isinstance(container, Mapping) else None
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    names: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        code = _optional_scalar_string(row, "stn_cd")
        name = _optional_scalar_string(row, "stn_nm")
        if code and name:
            names[code] = name
    if not names:
        raise KorailProtocolError(
            "KORAIL station data did not contain usable stations"
        )
    return names


def resolve_station_name(reference: str, names: Mapping[str, str]) -> str:
    """역 참조를 조회 폼에 실을 역이름으로 바꿉니다.

    숫자가 아니면 이미 이름이라고 보고 그대로 돌려줍니다. 숫자면 역코드로 보고 ``names``(:func:`parse_station_name_map` 의 결과)에서 찾습니다. 빈 참조와 표에
    없는 코드는 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다."""
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


@_preserve_read_raw
def parse_train_rows(raw: Mapping[str, Any]) -> list[TrainSummary]:
    """trn_infos 는 객체 안의 trn_info 목록, 직접 목록, null 을 허용합니다. 그 밖의 컨테이너·비객체 행은 오류입니다. 빈 목록만으로 직통 없음 예외를 만들지는
    않습니다."""
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


@_preserve_read_raw
def parse_train_search_metadata(
    raw: Mapping[str, Any],
) -> TrainSearchMetadata:
    """페이지 커서와 조회 조건을 읽습니다. h_merge_rsv_psb_flg 는 다른 DTO 의 필드입니다 (TrainScheduleOutTrainInfos.java:25-26,
    MergeSeatsCOutTrnInfos.java:25-26,85)."""
    def optional(key: str) -> str | None:
        return _typed_optional_string(raw, key)

    return TrainSearchMetadata(
        job_id=optional("strJobId"),
        menu_id=_optional_scalar_string(raw, "h_menu_id", "train search metadata"),
        product_no=optional("h_gd_no"),
        next_page_flag=optional("h_next_pg_flg"),
        next_query_station_no=optional("h_qry_st_no_next"),
        next_train_no=optional("h_trn_no_next"),
        # 환승 커서 선언: TrainScheduleOut.java:28,33,67. 소비 메서드는 jadx 복원 실패로 앱의 선택 조건을 여기서 확정하지 않습니다.
        # TransferSearchResult.next_page 의 두 필드 비어 있지 않음 조건은 라이브러리 정책입니다.
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
def parse_uuid_response(response: BaseKorailResponse) -> UuidResponse:
    """ebizcross/getUUID.do 의 비어 있지 않은 문자열 mutMrkVrfCd 를 읽고 없으면 KorailProtocolError 입니다. 완전한 KORAIL 봉투는 요구하지
    않습니다. strResult 만 동반된 2026-09-22 관측과 부분 봉투 보존은 http.KorailHttpClient._finish_read 참고."""
    value = response.raw.get("mutMrkVrfCd")
    if not isinstance(value, str) or not value.strip():
        raise KorailProtocolError(
            "KORAIL UUID response mutMrkVrfCd must be a non-empty string"
        )
    return UuidResponse(
        **_response_fields(response),
        verification_code=value,
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
    """MaaS 메뉴. menuList 의 비목록·비객체 행은 비웁니다. 부가서비스 코드는 역 선택 조회에 사용합니다."""
    items: list[MaasMenuItem] = []
    for row in _rows(response.raw, "menuList"):
        items.append(
            MaasMenuItem(
                **_nullable_string_fields(row, _MAAS_ITEM_FIELDS),
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
        **_nullable_string_fields(raw, _MAAS_RESPONSE_FIELDS),
    )


_STATION_OPTIONAL_STRING_FIELDS: dict[str, str] = {
    "longitude": "longitude",
    "latitude": "latitude",
    "group": "group",
    "major": "major",
    "popup_message": "popupMessage",
    "popup_link_title": "popupLinkTitle",
    "popup_link_url": "popupLinkUrl",
    "area": "area",
    "stop": "stop",
}


@_preserve_read_raw
def parse_station_data_response(
    response: BaseKorailResponse,
) -> StationDataResponse:
    """봉투 없는 역 목록. stns.stn 과 각 역의 비어 있지 않은 코드·이름은 필수입니다."""
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
                # popupType 은 정수로 바꾸지 않고 String 선언대로 읽습니다(StationDataOutStnItem.java:60).
                popup_type=_typed_optional_string(
                    row,
                    "popupType",
                ),
                **_nullable_string_fields(
                    row,
                    _STATION_OPTIONAL_STRING_FIELDS,
                ),
            )
        )
    return StationDataResponse(
        **_response_fields(response),
        stations=tuple(stations),
    )


@_preserve_read_raw
def parse_station_info_response(
    response: BaseKorailResponse,
) -> StationInfoResponse:
    """역 목록의 버전 정보. count 와 map_version 은 비어 있지 않은 문자열입니다. String 선언을 따라 count 도 정수로 바꾸지
    않습니다(StationInfoOut.java:47)."""
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


@_preserve_read_raw
def parse_train_calendar_response(
    response: BaseKorailResponse,
) -> TrainCalendarResponse:
    """운행 달력(NetworkApi.java:651-652). runningCalendar 는 누락·null·비목록이면 비우고 비객체 행은 건너뜁니다. 날짜·플래그의 선택 처리는 라이브러리
    정책입니다. 앱의 목록 누락 기본값은 emptyList()(RunDateOut.java:57-58,71-73)이며 날짜 기본값·성수기 판정 리터럴은 보호돼
    있습니다(RunDateOutItem.java:37,104-105,516-524). 조회 관문은 호출자가 peak_season 으로 선택합니다."""
    raw = response.raw
    # 앱의 누락 기본값과 라이브러리의 비목록 허용은 별개입니다(RunDateOut.java:57-58,71-73).
    days: list[TrainCalendarDay] = []
    for row in _rows(raw, "runningCalendar"):
        days.append(
            TrainCalendarDay(
                # 보호된 날짜 기본값을 재현하지 않아 누락은 None 입니다(RunDateOutItem.java:37,104-105).
                **_nullable_string_fields(row, {
                    "run_date": "runDt",
                    # bizDdStgCd 의 누락 기본값은 null(RunDateOutItem.java:111-115). 판정 헬퍼의 null 처리까지 확인된 것은
                    # 아닙니다(RunDateOutItem.java:516-524).
                    "business_day_stage_code": "bizDdStgCd",
                    # dayDvCd 누락 기본값은 null 입니다(RunDateOutItem.java:106-110). 직접 getter 참조의 부재만으로 반사 호출까지
                    # 없다고 단정하지 않고, 파서는 선택값으로 읽습니다.
                    "day_division_code": "dayDvCd",
                    # hldyDvCd 는 누락 시 보호 기본값을 사용하므로 필수 키가 아닙니다(RunDateOutItem.java:116-119). 보호 기본값의 평문을 빈
                    # 문자열로 확정하지 않습니다.
                    "holiday_division_code": "hldyDvCd",
                    # saleDdDvCd 누락 기본값은 null 이므로 선택값으로 읽습니다(RunDateOutItem.java:121-125).
                    "sale_day_division_code": "saleDdDvCd",
                    # 운행 플래그의 누락 기본값은 null(RunDateOutItem.java:126-160). isRunDate 비교 리터럴·null 처리 결과는 보호돼
                    # 있습니다(RunDateOutItem.java:526-590).
                    "a_train_operation_flag": "aTrnOpFlg",
                    "d_train_operation_flag": "dTrnOpFlg",
                    "g_train_operation_flag": "gTrnOpFlg",
                    "o_train_operation_flag": "oTrnOpFlg",
                    "s_train_operation_flag": "sTrnOpFlg",
                    "v_train_operation_flag": "vTrnOpFlg",
                    "x_train_operation_flag": "xTrnOpFlg",
                }),
                raw=dict(row),
            )
        )
    return TrainCalendarResponse(
        **_response_fields(response),
        days=tuple(days),
    )


@_preserve_read_raw
def parse_train_schedule_response(
    response: BaseKorailResponse,
) -> TrainScheduleResponse:
    """``research.actualTrainSchedule.do`` 의 정차역·지연 정보를 파싱합니다.

    7.0.6 DTO에서는 ``dlayList`` 가 생략되면 빈 목록입니다. 행 하나가 정차역 하나이며 도착·출발 시각과 지연 시간이 담깁니다. 개별 필드는 선택값이라 서버가 빼면 ``None``
    입니다."""
    raw = response.raw
    stops: list[TrainScheduleStop] = []
    for row in _rows(raw, "dlayList"):
        stops.append(
            TrainScheduleStop(
                **_nullable_string_fields(row, {
                    "station_code": "stopRsStnCd",
                    # stopStnNm 은 누락 시 기본값을 사용하는 필드입니다(ActualTrainScheduleOutDlay.java:71-76).
                    "station_name": "stopStnNm",
                    "station_construction_order": "stnConsOrdr",
                    "run_order": "runOrdr",
                }),
                # ActualTrainScheduleOutDlay.java:30 — 앱 DTO 는 String("001" 등)입니다.
                actual_arrival_delay_count=_optional_scalar_string(row, "actArvDlayTnum"),
                **_nullable_string_fields(row, {
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
                }),
                raw=dict(row),
            )
        )
    def optional(key: str) -> str | None:
        return _typed_optional_string(raw, key)

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
        # runDt1 은 누락 시 기본값을 사용하는 필드입니다(ActualTrainScheduleOut.java:75-80).
        run_date=_typed_optional_string(
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
        # 입니다. 소비: MyTicketDetailViewModel.java:2173-2175.
        train_no=optional("trnNo1"),
        special_train_flag=optional("trnSpsFlg"),
        up_down_division_code=optional("upDnDvCd"),
    )


@_preserve_read_raw
def parse_transfer_station_list_response(
    response: BaseKorailResponse,
) -> TransferStationListResponse:
    """qry.chtnStn.do 의 환승역 목록. chtnList 생략은 빈 목록(ChtnStnOut.java:54-60), 명시적 null·비목록은 KorailProtocolError 입니다.
    역 코드·이름은 선택값이며 빈 목록 자체는 오류가 아닙니다."""
    raw = response.raw
    rows = raw.get("chtnList", [])
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
                # 환승역 코드·역명은 누락 시 기본값을 사용하므로 선택값으로 읽습니다(ChtnStnOutItem.java:51-61).
                station_code=_typed_optional_string(
                    row,
                    "chtnRsStnCd",
                ),
                station_name=_typed_optional_string(
                    row,
                    "chtnRsStnNm",
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
    return _typed_non_negative_integer_value(
        data.get(key), key, context="seat inventory"
    )


@_preserve_read_raw
def parse_seat_car_list_response(
    response: BaseKorailResponse,
) -> SeatCarListResponse:
    """호차와 좌석 속성 목록. 호차번호를 다음 좌석 재고 조회에 사용합니다. 컨테이너는 선택 목록 헬퍼의 정책을 따릅니다."""
    raw = response.raw
    cars: list[SeatCar] = []
    for row in _nested_rows(raw, "srcar_infos", "srcar_info"):
        # 앱은 호차번호를 String 으로 선언합니다(TrainResearchOutCarInfo.java:32). 이 모델은 int 이므로 원래 영 채움은 잃습니다. 재전송 형식은 요청
        # 빌더에서 결정합니다.
        car_no = _inventory_required_int(row, "h_srcar_no")
        # seatAttInfos 생략 시 빈 목록은 TrainResearchOutCarInfo.java:33,81-84 의 기본값입니다. 명시적 null 도 빈 목록으로 읽는 것은 라이브러리
        # 정책이며 특정 객실 종류를 증명하지 않습니다.
        attributes: list[SeatAttribute] = []
        for attribute_raw in _rows(row, "seatAttInfos"):
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
        # TrainResearchOut.java:27,105 의 고유 필드.
        car_count=_optional_scalar_string(raw, "h_scar_num", "seat car list"),
    )


def _inventory_ratio(data: Mapping[str, Any], key: str) -> float:
    value = data.get(key)
    number: int | float | str
    # bool·사용자 정의 숫자 하위형을 제외합니다. isinstance 는 타입 검사기의 float 변환 추론용입니다.
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


@_preserve_read_raw
def parse_seat_inventory_response(
    response: BaseKorailResponse,
) -> SeatInventoryResponse:
    """일반 좌석 재고. seatList·windowList 는 누락만 빈 목록이며 키가 있으면 목록을 요구합니다. 좌석 필수 문자열·창측 비율의 오류는 응답 전체를 거절합니다. 선택 건수의 상호
    모순은 검증하지 않습니다. layout_type 은 String 선언(TResidualSeatsResearchOut.java:29)과 달리 정수도 허용합니다. 2026-09-21 라이브
    15대에서 JSON 정수를 관측했습니다."""
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
                # etc_seat_att_cd·vz_msg_dv_cd 는 생략·null 을
                # 허용합니다(TResidualSeatsResearchOutSeat.java:79-82,94-97).
                other_attribute_code=_inventory_optional_string(row, "etc_seat_att_cd"),
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
                visual_message_division_code=_inventory_optional_string(row, "vz_msg_dv_cd"),
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
