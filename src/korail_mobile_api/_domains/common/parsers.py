# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""세션·공통 조회 응답을 읽습니다. 18개 좌석·역 필드만 앱 누락 기본값을 사용하며 다른 선택값은 None입니다(checks/BEHAVIOR.md)."""

from __future__ import annotations

from collections.abc import Mapping
from functools import partial
from typing import Any

from ..._core.parsing import (
    _model_response_fields,
    _nullable_scalar_fields,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _typed_defaulted_string,
    _typed_required_string,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from ...errors import KorailProtocolError
from .models import (
    AppDataResponse,
    AppVersionInfo,
    BaseKorailResponse,
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

_station_string = partial(_typed_defaulted_string, context="station")


@_preserve_read_raw
def parse_app_data_response(response: BaseKorailResponse) -> AppDataResponse:
    """봉투 없는 prdMobilePlusMain.cache 를 읽습니다. 선택 필드의 잘못된 타입은 비웁니다. version 은 MobilePlusMainVersion.java:52 의
    3개 키를 읽고 나머지는 raw 에 둡니다."""
    raw = response.raw
    version_raw = raw.get("version")
    version = None
    if isinstance(version_raw, Mapping):
        version = AppVersionInfo(
            message=_optional_scalar_string(version_raw, "AMESSAGE"),
            new_version=_optional_scalar_string(version_raw, "NEWDVERSION"),
            store_url=_optional_scalar_string(version_raw, "CNTAURL"),
        )
    return AppDataResponse(
        **_model_response_fields(response),
        disability_certification_msg=_optional_scalar_string(
            raw,
            "disability_certification_msg",
        ),
        railplus_cardinfo=_optional_scalar_string(raw, "railplus_cardinfo"),
        version=version,
        notice=(parse_notice_response(response) if isinstance(raw.get("notice"), Mapping) else None),
    )


@_preserve_read_raw
def parse_notice_response(response: BaseKorailResponse) -> NoticeResponse:
    """메인 캐시의 중첩 ``notice`` 를 파싱합니다(MobilePlusMainOut.java:57, MobilePlusMainNotice.java:52). 공지가 없는 상태도
    정상입니다."""
    nested = response.raw.get("notice")
    notice_raw = nested if isinstance(nested, Mapping) else {}
    return NoticeResponse(
        **_model_response_fields(response),
        board_id=_optional_scalar_string(notice_raw, "BbrdId"),
        post_sequence=_optional_scalar_string(notice_raw, "PtwtSqno"),
        post_title=_optional_scalar_string(notice_raw, "PtwtTtl"),
        post_content=_optional_scalar_string(notice_raw, "PtwtCont"),
    )


@_preserve_read_raw
def parse_station_name_map(raw: Mapping[str, Any]) -> dict[str, str]:
    """역 코드와 이름의 캐시 대응표를 구성합니다. stns.stn 목록이나 사용 가능한 코드·이름 쌍이 없으면 오류입니다. 앱은 같은 응답을 로컬 역 DB 에 넣고 거기서 이름을
    찾습니다(StationDataRepositoryImpl.java:282-283)."""
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
        raise KorailProtocolError("KORAIL station data did not contain usable stations")
    return names


def resolve_station_name(reference: str, names: Mapping[str, str]) -> str:
    """숫자가 아니면 이미 이름이라고 보고 그대로 돌려줍니다. 빈 참조와 표에 없는 코드는 ``errors.KorailProtocolError`` 입니다."""
    value = reference.strip()
    if not value:
        raise KorailProtocolError("KORAIL station reference must not be empty")
    if not value.isdigit():
        return value
    try:
        return names[value]
    except KeyError as exc:
        raise KorailProtocolError(f"KORAIL station code is unknown: {value}") from exc


@_preserve_read_raw
def parse_uuid_response(response: BaseKorailResponse) -> UuidResponse:
    """ebizcross/getUUID.do 의 mutMrkVrfCd 를 문자열로 정규화하며 없거나 비면 KorailProtocolError 입니다. 완전한 KORAIL 봉투는 요구하지
    않습니다. strResult 만 동반된 관측과 부분 봉투 보존은 http.KorailHttpClient._exchange 참고."""
    value = _typed_required_string(response.raw, "mutMrkVrfCd", context="UUID response", non_empty=True)
    return UuidResponse(
        **_model_response_fields(response),
        verification_code=value,
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
    """봉투가 없는 역 목록을 읽습니다. stns.stn 은 필수입니다. 역 코드·이름은 mask 상 선택이라 누락되면 앱 기본값 "" 입니다
    (StationDataOutStnItem.java:60-63)."""
    container = response.raw.get("stns")
    if not isinstance(container, Mapping):
        raise KorailProtocolError("KORAIL station data missing stns object")
    rows = container.get("stn")
    if not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station data missing stns.stn list")
    stations: list[KorailStation] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError("KORAIL station data contained a non-object row")
        stations.append(
            KorailStation(
                code=_station_string(row, "stn_cd"),
                name=_station_string(row, "stn_nm"),
                raw=dict(row),
                # popupType 은 정수로 바꾸지 않고 String 선언대로 읽습니다(StationDataOutStnItem.java:60).
                popup_type=_optional_scalar_string(
                    row,
                    "popupType",
                ),
                **_nullable_scalar_fields(
                    row,
                    _STATION_OPTIONAL_STRING_FIELDS,
                ),
            )
        )
    return StationDataResponse(
        **_model_response_fields(response),
        stations=tuple(stations),
    )


@_preserve_read_raw
def parse_station_info_response(
    response: BaseKorailResponse,
) -> StationInfoResponse:
    """역 목록의 버전 정보를 읽습니다. count 와 map_version 은 필수 문자열 필드입니다(StationInfoOut.java:47-49). 빈 값은 DTO 도 거절하지 않으므로
    그대로 받고, 공통 String/정수 호환 규칙에 따라 정수도 문자열로 읽습니다."""
    raw = response.raw
    return StationInfoResponse(
        **_model_response_fields(response),
        count=_typed_required_string(raw, "count", context="station info"),
        map_version=_typed_required_string(raw, "map_version", context="station info"),
    )


@_preserve_read_raw
def parse_train_calendar_response(
    response: BaseKorailResponse,
) -> TrainCalendarResponse:
    """앱 근거: NetworkApi.java:651-652. runningCalendar 는 누락·null·비목록이면 비우고 비객체 행은 건너뜁니다. 앱의 목록 누락 기본값은
    emptyList()(RunDateOut.java:57-58,71-73)이며 날짜 기본값·성수기 판정 리터럴은 보호돼
    있습니다(RunDateOutItem.java:37,104-105,516-524)."""
    raw = response.raw
    # 앱의 누락 기본값과 라이브러리의 비목록 허용은 별개입니다(RunDateOut.java:57-58,71-73).
    days: list[TrainCalendarDay] = [
        TrainCalendarDay(
            # 보호된 날짜 기본값을 재현하지 않아 누락은 None 입니다(RunDateOutItem.java:37,104-105).
            **_nullable_scalar_fields(
                row,
                {
                    "run_date": "runDt",
                    # bizDdStgCd 의 누락 기본값은 null(RunDateOutItem.java:111-115). 판정 헬퍼의 null 처리까지 확인된 것은
                    # 아닙니다(RunDateOutItem.java:516-524).
                    "business_day_stage_code": "bizDdStgCd",
                    # dayDvCd 누락 기본값은 null 입니다(RunDateOutItem.java:106-110). 직접 getter 참조의 부재만으로 반사 호출까지 없다고
                    # 단정하지 않고, 파서는 선택값으로 읽습니다.
                    "day_division_code": "dayDvCd",
                    # hldyDvCd 는 누락 시 보호 기본값을 사용하므로 필수 키가 아닙니다(RunDateOutItem.java:116-119). 보호 기본값의 평문을 빈 문자열로
                    # 확정하지 않습니다.
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
                },
            ),
            raw=dict(row),
        )
        for row in _rows(raw, "runningCalendar")
    ]
    return TrainCalendarResponse(
        **_model_response_fields(response),
        days=tuple(days),
    )


_CREW_REQUEST_OPTION_FIELDS: dict[str, str] = {
    "message_code": "intgMsgCd",
    "content": "prsCont",
}


@_preserve_read_raw
def parse_crew_request_list_response(
    raw: Mapping[str, Any],
) -> CrewRequestListResponse:
    _validate_strict_read_envelope(raw)
    items = tuple(
        CrewRequestOption(
            **_nullable_scalar_fields(row, _CREW_REQUEST_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(raw, "prsList")
    )
    return CrewRequestListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_service_status_response(
    raw: Mapping[str, Any],
) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))
