# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""정기권·N카드 조회 응답을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    _nullable_scalar_fields,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _preserve_read_raw,
    _response_fields,
    _rows,
)
from ._read_parser_common import _validate_envelope, _validate_strict_read_envelope
from .errors import KorailProtocolError
from .read_models import (
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CommuterPassengerOption,
    DiscountCardScheduleResponse,
    DiscountCardScheduleTrain,
    DiscountCardUsage,
    DiscountCardUsageListResponse,
    PassAgeOption,
    PassAvailabilityMainInfo,
    PassAvailabilityResponse,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassOpenDate,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PassScheduleInfo,
    PassScheduleMainInfo,
    PassScheduleResponse,
    PassScheduleTrain,
)

_PASS_MENU_ITEM_FIELDS: dict[str, str] = {
    # afterDay는 문자열입니다(PassMenuOutItem.java:28). 실서버 관측: menu_no=1의 25행·2의 10행 모두 문자열이었고, 같은 25행의
    # detailType·isExpand·saleMsg1-3에는 빈 문자열도 있었습니다.
    "after_day": "afterDay",
    "agreement": "agree",
    "detail_type": "detailType",
    "detail_description": "dtlDsc",
    "enabled": "enable",
    "item_id": "id",
    "information": "information",
    "expanded": "isExpand",
    "parent_id": "parentId",
    "representative_arrival": "repSegArv",
    "representative_departure": "repSegDpt",
    "title": "title",
    "train_group_code": "trnGpCd",
    "item_type": "type",
}

_PASS_MENU_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "sale_message_1": "saleMsg1",
    "sale_message_2": "saleMsg2",
    "sale_message_3": "saleMsg3",
}

_COMMUTER_KIND_MENU_FIELDS: dict[str, str] = {
    "after_day": "afterDay",
    "agreement": "agree",
    "information": "information",
    "title": "title",
}

_PASS_SCHEDULE_TRAIN_FIELDS: dict[str, str] = {
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "detour_code": "h_dtour",
    "schedule_price": "h_schd_prc",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    # TrainList.java:25-70 의 필드 중 h_run_dt 는 운행일입니다.
    "train_sequence": "h_trn_seq",
    "change_train_sequence": "h_chg_trn_seq",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "run_date": "h_run_dt",
    "price_class_code": "h_prc_cl_cd",
    "route_code": "h_rout_cd",
    "departure_construction_order": "h_dpt_stn_cons_ordr",
    "arrival_construction_order": "h_arv_stn_cons_ordr",
    "car_type_code": "h_car_tp_cd",
    "train_class_code": "h_trn_clsf_cd",
    "commuter_use_terminal_code": "h_cmtr_utl_trm_cd",
    "commuter_use_terminal_name": "h_cmtr_utl_trm_nm",
}

_PASS_SCHEDULE_MAIN_FIELDS: dict[str, str] = {
    "sale_window_no": "h_wct_no",
    "work_date": "h_work_dt",
    "work_time": "h_work_tm",
    "job_id": "h_job_id",
    "version_no": "h_ver_no",
    "message_code": "h_msg_cd",
    "selected_count": "h_sel_cnt",
    "total_selected_count": "h_tot_sel_cnt",
    "count_per_page": "h_cnt_per_page",
    "page_count": "h_page_cnt",
    "next_page_flag": "h_next_pg_flg",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "page_no": "h_page_no",
}

_PASS_AVAILABILITY_MAIN_FIELDS: dict[str, str] = {
    "message_code": "h_msg_cd",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "selected_page_no": "h_sel_pg_no",
}

_PASS_AGE_OPTION_FIELDS: dict[str, str] = {
    "commuter_age_code": "h_cmtr_utl_age_cd",
    "display_name": "h_comn_cd_nm",
    "minimum_age": "h_min_age",
    "maximum_age": "h_max_age",
}

_PASS_PERIOD_OPTION_FIELDS: dict[str, str] = {
    "commuter_period_code": "h_cmtr_utl_trm_cd",
    "display_name": "h_comn_cd_nm",
}


def _parse_pass_menu_data(
    data: Mapping[str, Any] | None,
    *,
    station_selection_key: str = "h_select_station",
) -> PassMenuData | None:
    if data is None:
        return None
    age_options = tuple(
        PassAgeOption(
            **_nullable_scalar_fields(row, _PASS_AGE_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(data, "pass_ageinfo")
    )
    period_options = tuple(
        PassPeriodOption(
            **_nullable_scalar_fields(row, _PASS_PERIOD_OPTION_FIELDS),
            raw=row,
        )
        for row in _rows(data, "pass_periodinfo")
    )
    return PassMenuData(
        commuter_kind_code=_optional_scalar_string(data, "h_cmtr_knd_cd"),
        station_selection=_optional_scalar_string(data, station_selection_key),
        age_options=age_options,
        period_options=period_options,
        raw=data,
    )


def _parse_pass_goods_info(
    data: Mapping[str, Any] | None,
) -> PassGoodsInfo | None:
    if data is None:
        return None
    passenger_infos_data = _optional_mapping(data, "psg_infos")
    passenger_infos = None
    if passenger_infos_data is not None:
        passengers = []
        for item in _rows(
            passenger_infos_data,
            "psg_info",
        ):
            passengers.append(
                PassPassengerInfo(
                    # 관측된 패스 인원은 000001 같은 패딩 문자열입니다.
                    h_cls_prnb=_optional_integer(
                        item,
                        "h_cls_prnb",
                        "pass passenger info",
                    ),
                    h_dcnt_knd_cd=_optional_scalar_string(
                        item,
                        "h_dcnt_knd_cd",
                    ),
                    h_st_prnb=_optional_integer(
                        item,
                        "h_st_prnb",
                        "pass passenger info",
                    ),
                    raw=item,
                )
            )
        passenger_infos = PassPassengerInfos(
            **_nullable_scalar_fields(
                passenger_infos_data,
                {
                    "h_chtn_allw_flg": "h_chtn_allw_flg",
                    "h_max_cnt": "h_max_cnt",
                    "h_min_cnt": "h_min_cnt",
                },
            ),
            psg_info=tuple(passengers),
            raw=passenger_infos_data,
        )
    return PassGoodsInfo(
        h_cnd_flg_disc_no=_optional_scalar_string(
            data,
            "h_cnd_flg_disc_no",
        ),
        psg_infos=passenger_infos,
        raw=data,
    )


@_preserve_read_raw
def parse_pass_menu_response(raw: Mapping[str, Any]) -> PassMenuResponse:
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _rows(raw, "list"):
        web_data = _optional_mapping(item, "webData")
        items.append(
            PassMenuItem(
                **_nullable_scalar_fields(item, _PASS_MENU_ITEM_FIELDS),
                **_nullable_scalar_fields(item, _PASS_MENU_ITEM_SCALAR_FIELDS, "pass menu item"),
                goods_data=_parse_pass_goods_info(
                    _optional_mapping(item, "goodsData"),
                ),
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(item, "passData"),
                ),
                url=(_optional_scalar_string(web_data, "url") if web_data is not None else None),
                raw=item,
            )
        )
    return PassMenuResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_commuter_kind_menu_response(
    raw: Mapping[str, Any],
) -> CommuterKindMenuResponse:
    _validate_strict_read_envelope(raw)
    return CommuterKindMenuResponse(
        **_nullable_scalar_fields(raw, _COMMUTER_KIND_MENU_FIELDS),
        pass_data=_parse_pass_menu_data(
            _optional_mapping(raw, "passData"),
        ),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pass_availability_response(
    raw: Mapping[str, Any],
) -> PassAvailabilityResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    # PassInfo.java:92,96,100의 세 값은 pass_info에, 사용 개시일만 모은 편의 목록은 open_dates에 둡니다.
    open_dates = []
    pass_rows = []
    for item in _rows(raw, "pass_info"):
        date = _optional_scalar_string(item, "h_use_open_dt")
        if date is not None:
            open_dates.append(date)
        pass_rows.append(
            PassOpenDate(
                open_date=date,
                item_sequence=_optional_scalar_string(item, "h_item_sqno", "pass date"),
                pnr_no=_optional_scalar_string(item, "h_pnr_no", "pass date"),
                raw=item,
            )
        )
    ticket_issue_dates = []
    for item in _rows(raw, "ticket_info"):
        date = _optional_scalar_string(item, "h_ise_dt2")
        if date is not None:
            ticket_issue_dates.append(date)
    offices = []
    for item in _rows(raw, "wct_info"):
        offices.append(
            PassOffice(
                code=_optional_scalar_string(item, "eng_cd_val"),
                display_name=_optional_scalar_string(item, "kor_cd_val"),
                raw=item,
            )
        )
    # 상태는 중첩 main_info에서 읽습니다(PassInfoListOut.java:115; MainInfo.java:103,107,111,115). 29종은 최상위 h_msg_cd 없이
    # SUCC와 중첩 IRZ000005 등을 반환했습니다.
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassAvailabilityMainInfo(
            **_nullable_scalar_fields(main_raw, _PASS_AVAILABILITY_MAIN_FIELDS, "pass availability main info"),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    return PassAvailabilityResponse(
        open_dates=tuple(open_dates),
        ticket_issue_dates=tuple(ticket_issue_dates),
        offices=tuple(offices),
        pass_info=tuple(pass_rows),
        main_info=main_info,
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_pass_schedule_response(
    raw: Mapping[str, Any],
) -> PassScheduleResponse:
    # WRG000000 안내문은 조회 결과 없음(assets/error_json.json:4173,14397). 비치명적 처리의 근거는 안내문·라이브 기록이며 앱 호출부의 평문 분기는 확인되지
    # 않았습니다.
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    main_raw = _optional_mapping(raw, "main_info")
    main_info = (
        PassScheduleMainInfo(
            **_nullable_scalar_fields(main_raw, _PASS_SCHEDULE_MAIN_FIELDS, "pass schedule main info"),
            raw=main_raw,
        )
        if main_raw is not None
        else None
    )
    schedules = []
    for schedule in _rows(raw, "schedule_info"):
        trains = tuple(
            PassScheduleTrain(
                **_nullable_scalar_fields(row, _PASS_SCHEDULE_TRAIN_FIELDS, "pass schedule train"),
                raw=row,
            )
            for row in _rows(
                schedule,
                "train_list",
            )
        )
        schedules.append(PassScheduleInfo(trains=trains, raw=schedule))
    return PassScheduleResponse(
        main_info=main_info,
        schedules=tuple(schedules),
        **_response_fields(raw),
    )


_DISCOUNT_CARD_USAGE_FIELDS = {
    "passenger_name": "custNm",
    "departure_station_name": "dptStnNm",
    "arrival_station_name": "arvStnNm",
    "run_date": "runDt1",
    "additional_user_flag": "apdUsrFlg",
    # NCardHistoryInfo.java:224 의 8속성 중 판매 식별자 3개도 보존합니다. 화면은 나머지 5개를
    # 소비합니다(NCardHistoryScreenKt.java:431,439,526,528,301).
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
}

_DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS = {
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "run_date": "runDt",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "departure_station_order": "dptStnConsOrdr",
    "arrival_station_order": "arvStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "arrival_run_order": "arvStnRunOrdr",
    "transfer_train_order_no": "chtnTrnOrdrNo",
    "price_class_code": "prcClCd",
    "settlement_car_type_code": "stlbCarTpCd",
    "settlement_train_class_code": "stlbTrnClsfCd",
    "commuter_price": "cmtrPrc",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "detour_code": "dturCd",
    "detour_name": "dturNm",
    "route_code": "routCd",
    # stationStringInfo 는 NCardScheduleItem.java:25-49 의 응답 필드가 아니므로 읽지 않습니다. 서버가 추가로 보낸 값은 raw 에 남으며 DTO 미선언만으로
    # 전송 부재를 보장하지 않습니다.
}


@_preserve_read_raw
def parse_discount_card_usage_response(
    raw: Mapping[str, Any],
) -> DiscountCardUsageListResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    items = []
    for item in _rows(raw, "tkUseList"):
        items.append(
            DiscountCardUsage(
                # 다른 조회의 숫자형 관측을 고려해 순번은 문자열·정수를 모두 허용합니다(이 경로는 미검증).
                **_nullable_scalar_fields(item, _DISCOUNT_CARD_USAGE_FIELDS, "discount card usage"),
                raw=item,
            )
        )
    return DiscountCardUsageListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_discount_card_schedule_response(
    raw: Mapping[str, Any],
) -> DiscountCardScheduleResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다."""
    _validate_strict_read_envelope(raw)
    trains = []
    for item in _rows(raw, "trnScdlList"):
        trains.append(
            DiscountCardScheduleTrain(
                # 이 라우트의 라이브 근거는 없으며 파서 정책입니다.
                **_nullable_scalar_fields(
                    item, _DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS, "discount card schedule train"
                ),
                raw=item,
            )
        )
    # fllwPgExt 는 ScdlQryOut 필드이며 NCardScheduleOut.java:27-28 은 trnScdlList 만 선언합니다. 이 라우트의 페이지 신호는 미확인이라
    # following_page_exists 는 채우지 않습니다.
    return DiscountCardScheduleResponse(
        trains=tuple(trains),
        **_response_fields(raw),
    )


def _primitive_json_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int | None:
    """Kotlin Int 값을 읽되 누락은 0, 잘못된 형식은 None으로 처리합니다."""
    if data.get(key) is None:
        return 0
    return _optional_integer(data, key, context)


@_preserve_read_raw
def parse_commuter_info_response(
    raw: Mapping[str, Any],
) -> CommuterInfoResponse:
    _validate_strict_read_envelope(raw)
    passenger_options = []
    for item in _rows(raw, "psgList"):
        passenger_options.append(
            CommuterPassengerOption(
                commuter_usage_age_code=_optional_scalar_string(
                    item,
                    "cmtrUtlAgeCd",
                ),
                common_code_name=_optional_scalar_string(
                    item,
                    "comnCdNm",
                ),
                # Psg.java:30-31 의 연령 범위는 int 입니다.
                customer_age_from=_primitive_json_integer(
                    item,
                    "custAgeFrom",
                    "commuter passenger option",
                ),
                customer_age_to=_primitive_json_integer(
                    item,
                    "custAgeTo",
                    "commuter passenger option",
                ),
                passenger_count_from=_primitive_json_integer(
                    item,
                    "psgPrnbFrom",
                    "commuter passenger option",
                ),
                passenger_count_to=_primitive_json_integer(
                    item,
                    "psgPrnbTo",
                    "commuter passenger option",
                ),
                raw=item,
            )
        )
    return CommuterInfoResponse(
        **_nullable_scalar_fields(
            raw,
            {
                "additional_service_goods_flag": "addSrvGdFlg",
                "companion_flag": "cmpaFlg",
                "commuter_kind_code": "cmtrKndCd",
                "commuter_usage_age_code": "cmtrUtlAgeCd",
                "menu_id": "menuId",
                "popup_message": "poppMsg",
                "promotion_message": "prmoMsg",
                "promotion_url": "prmoUrl",
                "seat_attribute_code": "seatAttCd1",
            },
        ),
        available_passenger_count_from=_primitive_json_integer(
            raw,
            "avlPrnbFrom",
            "commuter info",
        ),
        available_passenger_count_to=_primitive_json_integer(
            raw,
            "avlPrnbTo",
            "commuter info",
        ),
        passenger_options=tuple(passenger_options),
        **_response_fields(raw),
    )
