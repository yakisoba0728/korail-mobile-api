"""읽기 라우트 응답을 :mod:`korail_mobile_api.read_models` 타입으로 변환.

파서 하나가 라우트 하나를 맡습니다. 봉투 확인 후 DAO 필드만 추출하며,
원본 JSON 은 모델의 ``raw`` 에 보존됩니다.

KORAIL 은 ``String`` 선언 필드를 JSON 숫자로도 보내므로
:func:`_optional_scalar_string` 으로 양쪽을 수용합니다.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import (
    KorailProtocolError,
    KorailSessionExpiredError,
    classify_app_error,
)
from .read_models import (
    CartItem,
    CartListResponse,
    CommuterInfoResponse,
    CommuterKindMenuResponse,
    CommuterPassengerOption,
    CrewRequestListResponse,
    CrewRequestOption,
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DeliveryRecipientResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCardOnTicket,
    DiscountCardScheduleResponse,
    DiscountCardScheduleTrain,
    DiscountCardSection,
    DiscountCardUsage,
    DiscountCardUsageListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GiftTicket,
    GiftTicketListResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    KorailPointSummaryResponse,
    MaasServiceDetail,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    OriginalTicket,
    OriginalTicketInquiryResponse,
    OriginalTicketJourney,
    OriginalTicketSeat,
    PassAgeOption,
    PassAvailabilityResponse,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PassScheduleInfo,
    PassScheduleResponse,
    PassScheduleTrain,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    PlatformNumberJourney,
    PlatformNumberResponse,
    PlatformNumberTicket,
    PriceFare,
    PriceFareQuoteResponse,
    ProductDetailResponse,
    ProductRecommendation,
    ProductReservation,
    ProductReservationListResponse,
    ProductTrain,
    ProductTrainInquiryResponse,
    ReceiptCashPayment,
    ReceiptPayment,
    RecentDeliveryHistoryResponse,
    RecentDeliveryRecipient,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketSeat,
    ReservationDetailJourney,
    ReservationHistoryResponse,
    ReservationHistoryTrain,
    ReservationSeatDetail,
    SeatAssignmentScheduleResponse,
    SelfSeatChangeInfoResponse,
    SelfSeatChangeReason,
    SelfSeatChangeStation,
    ServiceStatusResponse,
    TicketDuplicationCheckResponse,
    TicketReceipt,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TourTrainInfoResponse,
    TourTrainSeatAdditionalInfo,
    TourTrainSeatInfo,
    TrainScheduleItem,
    TripChangeDateResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
    allow_result_only_success: bool = False,
) -> bool:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    required = ("h_msg_cd", "h_msg_txt", "strResult")
    missing = [name for name in required if name not in raw]
    invalid = [
        name
        for name in required
        if name in raw
        and raw[name] is not None
        and not isinstance(raw[name], str)
    ]
    if missing:
        if allow_result_only_success:
            if invalid:
                raise KorailProtocolError(
                    "KORAIL response envelope fields must be strings or "
                    "null: "
                    + ", ".join(invalid)
                )
            if set(missing) == {"h_msg_cd", "h_msg_txt"}:
                if raw.get("strResult") != "SUCC":
                    raise KorailProtocolError(
                        "KORAIL result-only envelope requires the exact "
                        "success result"
                    )
                return False
        raise KorailProtocolError(
            "KORAIL response missing required envelope fields: "
            + ", ".join(missing)
        )
    if invalid:
        raise KorailProtocolError(
            "KORAIL response envelope fields must be strings or null: "
            + ", ".join(invalid)
        )
    code = raw.get("h_msg_cd")
    message = raw.get("h_msg_txt")
    result = raw.get("strResult")
    if code == "P058":
        raise KorailSessionExpiredError(code, message, raw=raw)
    failed = result == "FAIL" or code == "WRC000288"
    if failed and code not in accepted_empty_codes:
        # ``accepted_empty_codes`` still wins: a per-endpoint opt-in returns an
        # empty result without raising anything, so classification never touches
        # it. Only a failure that was already going to be raised gets refined.
        raise classify_app_error(code, message, raw=raw)
    return failed


def _response_fields(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "h_msg_cd": raw.get("h_msg_cd"),
        "h_msg_txt": raw.get("h_msg_txt"),
        "str_result": raw.get("strResult"),
        "raw": raw,
    }


def _validate_strict_read_envelope(
    raw: Mapping[str, Any],
    *,
    allow_result_only_success: bool = False,
) -> None:
    _validate_envelope(
        raw,
        allow_result_only_success=allow_result_only_success,
    )
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError(
            "KORAIL strict read response strResult must be SUCC"
        )


def _optional_mapping(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> Mapping[str, Any] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be an object or null"
        )
    return value


def _optional_list(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> list[Any]:
    value = data.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a list or null"
        )
    return value


def _nested_rows(
    raw: Mapping[str, Any],
    outer_key: str,
    inner_key: str,
    context: str,
) -> list[Any]:
    outer = _optional_mapping(raw, outer_key, context)
    if outer is None:
        return []
    return _optional_list(outer, inner_key, context)


def _row(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(
            f"KORAIL {context} contained a non-object item"
        )
    return value


def _optional_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or null"
        )
    return value


def _present_strings(
    data: Mapping[str, Any],
    keys: tuple[str, ...],
    context: str,
) -> tuple[str, ...]:
    """선택 문자열 값이 실제로 온 키들을 순서대로 모읍니다."""
    values: list[str] = []
    for key in keys:
        value = _optional_string(data, key, context)
        if value is not None:
            values.append(value)
    return tuple(values)


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    """스칼라 필드 — JSON 문자열과 JSON 정수를 모두 수용.

    KORAIL 이 ``String`` 선언 필드를 숫자로도 보내는 사례: ``h_jrny_cnt``,
    ``h_st_prnb``/``h_cls_prnb``, ``h_srcar_no``. ``bool``/``float``/리스트/객체는
    프로토콜 오류.
    """
    value = data.get(key)
    if value is None or isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass and `True` is not
    # a number KORAIL ever sends for one of these fields.
    if type(value) is int:
        return str(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string, an integer, or null"
    )


def _optional_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        return int(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be an integer, "
        "an ASCII decimal string, or null"
    )


def _required_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    # These fields are declared Java `int` in the DAO, and Gson's
    # JsonReader.nextInt() coerces a quoted numeric string ("2") into the int,
    # so the app accepts both the number and the string form. Accept either
    # (int or ASCII-decimal string); keep rejecting null/bool/float/non-numeric.
    value = data.get(key)
    if type(value) is int:
        return value
    if (
        isinstance(value, str)
        and value
        and all("0" <= character <= "9" for character in value)
    ):
        return int(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be an integer or an "
        "ASCII decimal string"
    )


def _nullable_string_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str,
) -> dict[str, str | None]:
    return {
        attribute: _optional_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


def _nullable_scalar_fields(
    data: Mapping[str, Any],
    field_map: Mapping[str, str],
    context: str,
) -> dict[str, str | None]:
    """Like :func:`_nullable_string_fields` but accepts JSON numbers too.

    See :func:`_optional_scalar_string`.
    """
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
    }


# ─── Field maps for the first-half parsers ───────────────────────────────────

_CART_ITEM_FIELDS: dict[str, str] = {
    "service_code": "addSrvDvCd",
    "provider_name": "h_add_srv_mrk_ent_nm",
    "product_name": "h_gd_nm",
    "item_type": "h_item_dv_nm",
    "departure_date": "h_dpt_dt",
    "received_amount": "h_rcvd_amt",
    "reservation_received_date": "h_rsv_rcp_dt",
    "usage_start_date": "utlStDt",
    "usage_start_time": "utlStTm",
    "usage_close_time": "utlClsTm",
    "partner_reservation_no": "coptEntRsvNo",
    "pnr_no": "h_pnr_no",
    "lump_sum_target_no": "h_lump_stl_tgt_no",
    "customer_no": "h_cust_no",
    "virtual_reservation_no": "h_vr_rsv_no",
}

_DEPOSIT_BANK_FIELDS: dict[str, str] = {
    "code": "dptnBankCd",
    "display_name": "dptnBankNm",
}

_DELAY_DISCOUNT_TICKET_FIELDS: dict[str, str] = {
    "fare": "h_dlay_fare",
    "usable_until_date": "h_use_psb_dt",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "window_no": "h_orgtk_wct_no",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
}

_CREW_REQUEST_OPTION_FIELDS: dict[str, str] = {
    "message_code": "intgMsgCd",
    "content": "prsCont",
}

_PASS_MENU_ITEM_FIELDS: dict[str, str] = {
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

_COMMUTER_KIND_MENU_FIELDS: dict[str, str] = {
    "after_day": "afterDay",
    "agreement": "agree",
    "information": "information",
    "title": "title",
}

_TRIP_MENU_CONTENT_FIELDS: dict[str, str] = {
    "title": "contTitle",
    "detail": "contDetail",
    "content_type": "detailType",
    "active": "passActive",
    "agree": "passAgree",
    "info": "passInfo",
    "image": "contImage",
    "url": "contUrl",
}

_TRIP_MENU_ITEM_FIELDS: dict[str, str] = {
    "title": "menuTitle",
    "detail": "menuDetail",
    "menu_type": "menuType",
    "button": "menuBtn",
    "url": "menuUrl",
}

_PRODUCT_RESERVATION_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "payment_deadline": "strStlDlnDt",
    "payment_status": "strStlSttCd",
    "virtual_reservation_no": "strVrRsvNo",
}

_PRODUCT_DETAIL_FIELDS: dict[str, str] = {
    "product_name": "strGdNm",
    "reservation_status": "strRsvSttNm",
    "cancellation_deadline": "strCncDlnDt",
    "cancellation_amount": "strCncRetAmt",
    "cancellation_fee": "strCncRetFee",
    "received_amount": "strRcvdAmt",
    "total_amount": "strTotStlAmt",
    "usage_period": "strUtlTrmCont",
    "virtual_reservation_no": "strVrRsvNo",
}

_RECEIPT_PAYMENT_FIELDS: dict[str, str] = {
    "payment_method": "h_stl_way_nm",
    "approval_date": "h_apv_dt",
    "account_no": "h_acnt_no",
    "approval_no": "h_apv_no",
    "card_no": "h_stl_crd_no",
    "point_no": "h_xpot_no",
}

_RECEIPT_CASH_PAYMENT_FIELDS: dict[str, str] = {
    "approval_method_name": "h_apv_mtd_nm",
    "authentication_domain_recognition_no": "h_athn_dmn_rcgn_no",
    "cash_receipt_approval_no": "h_cash_rcet_apv_no",
    "cash_receipt_transaction_division_code": "h_cash_rcet_txn_dv_cd",
}

_TICKET_RECEIPT_FIELDS: dict[str, str] = {
    "travel_date": "h_abrd_dt",
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "commuter_kind_code": "h_cmtr_knd_cd",
    "journey_type_code": "h_jrny_tp_cd",
    "printed_discount_name": "h_prt_disc_knd_nm",
    "print_type": "h_prt_type",
    "seat_class_name": "h_psrm_cl_nm",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_status_code": "h_tk_stt_cd",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "train_no": "h_trn_no",
    "member_card_no": "h_stl_mb_crd_no",
}

_RESERVATION_HISTORY_TRAIN_FIELDS: dict[str, str] = {
    "departure_station": "h_dpt_rs_stn_nm",
    "departure_time": "h_dpt_tm",
    "arrival_station": "h_arv_rs_stn_nm",
    "arrival_time": "h_arv_tm",
    "run_date": "h_run_dt",
    "train_no": "h_trn_no",
    "train_class_code": "h_trn_clsf_cd",
    "train_class_name": "h_trn_clsf_nm",
    "reservation_type_code": "h_rsv_tp_cd",
    "acceptance_possible_flag": "h_acpt_ps_flg",
    "payment_flag": "h_payment_flg",
    "settlement_flag": "h_stl_flg",
    "pnr_no": "h_pnr_no",
}

_TRAIN_SCHEDULE_ITEM_FIELDS: dict[str, str] = {
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
    "seat_map_flag": "h_rd_seat_map_flg",
    "delay_sale_flag": "h_dlay_sale_flg",
    "wait_reservation_flag": "h_wait_rsv_flg",
    "reservation_possible_name": "h_rsv_psb_nm",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "info_text": "h_info_txt",
    "popup_message": "h_popup_msg",
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


# ─── Composite parse helpers ─────────────────────────────────────────────────

def _parse_pass_menu_data(
    data: Mapping[str, Any] | None,
    context: str,
) -> PassMenuData | None:
    if data is None:
        return None
    age_options = tuple(
        PassAgeOption(
            **_nullable_string_fields(
                _row(v, f"{context} pass_ageinfo"),
                _PASS_AGE_OPTION_FIELDS,
                "pass age option",
            ),
            raw=_row(v, f"{context} pass_ageinfo"),
        )
        for v in _optional_list(data, "pass_ageinfo", context)
    )
    period_options = tuple(
        PassPeriodOption(
            **_nullable_string_fields(
                _row(v, f"{context} pass_periodinfo"),
                _PASS_PERIOD_OPTION_FIELDS,
                "pass period option",
            ),
            raw=_row(v, f"{context} pass_periodinfo"),
        )
        for v in _optional_list(data, "pass_periodinfo", context)
    )
    return PassMenuData(
        commuter_kind_code=_optional_string(data, "h_cmtr_knd_cd", context),
        station_selection=_optional_string(data, "h_select_station", context),
        age_options=age_options,
        period_options=period_options,
        raw=data,
    )


def _parse_pass_goods_info(
    data: Mapping[str, Any] | None,
    context: str,
) -> PassGoodsInfo | None:
    if data is None:
        return None
    passenger_infos_data = _optional_mapping(data, "psg_infos", context)
    passenger_infos = None
    if passenger_infos_data is not None:
        passengers = []
        for value in _optional_list(
            passenger_infos_data,
            "psg_info",
            "pass passenger infos",
        ):
            item = _row(value, "pass passenger infos psg_info")
            passengers.append(
                PassPassengerInfo(
                    # The live pass menu sends these counts as ZERO-PADDED
                    # decimal strings ("h_st_prnb": "000001", "h_cls_prnb":
                    # "000009"), never as JSON integers, so demanding a JSON
                    # integer rejected every real goods row. _optional_integer
                    # accepts both and coerces the padded string to int, which
                    # is what the int|None model field already promises.
                    h_cls_prnb=_optional_integer(
                        item,
                        "h_cls_prnb",
                        "pass passenger info",
                    ),
                    h_dcnt_knd_cd=_optional_string(
                        item,
                        "h_dcnt_knd_cd",
                        "pass passenger info",
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
            h_chtn_allw_flg=_optional_string(
                passenger_infos_data,
                "h_chtn_allw_flg",
                "pass passenger infos",
            ),
            h_max_cnt=_optional_string(
                passenger_infos_data,
                "h_max_cnt",
                "pass passenger infos",
            ),
            h_min_cnt=_optional_string(
                passenger_infos_data,
                "h_min_cnt",
                "pass passenger infos",
            ),
            psg_info=tuple(passengers),
            raw=passenger_infos_data,
        )
    return PassGoodsInfo(
        h_cnd_flg_disc_no=_optional_string(
            data,
            "h_cnd_flg_disc_no",
            context,
        ),
        psg_infos=passenger_infos,
        raw=data,
    )


def parse_pass_menu_response(raw: Mapping[str, Any]) -> PassMenuResponse:
    # Live pass.passMenu.do success is result-only (no h_msg_cd/h_msg_txt).
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for value in _optional_list(raw, "list", "pass menu"):
        item = _row(value, "pass menu list")
        web_data = _optional_mapping(item, "webData", "pass menu item")
        items.append(
            PassMenuItem(
                after_day=_optional_integer(item, "afterDay", "pass menu item"),
                **_nullable_string_fields(item, _PASS_MENU_ITEM_FIELDS, "pass menu item"),
                goods_data=_parse_pass_goods_info(
                    _optional_mapping(item, "goodsData", "pass menu item"),
                    "pass goods info",
                ),
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(item, "passData", "pass menu item"),
                    "pass menu data",
                ),
                url=(
                    _optional_string(web_data, "url", "pass menu web data")
                    if web_data is not None
                    else None
                ),
                raw=item,
            )
        )
    return PassMenuResponse(items=tuple(items), **_response_fields(raw))


def parse_commuter_kind_menu_response(
    raw: Mapping[str, Any],
) -> CommuterKindMenuResponse:
    _validate_strict_read_envelope(raw)
    return CommuterKindMenuResponse(
        **_nullable_string_fields(raw, _COMMUTER_KIND_MENU_FIELDS, "commuter kind menu"),
        pass_data=_parse_pass_menu_data(
            _optional_mapping(raw, "passData", "commuter kind menu"),
            "commuter kind pass data",
        ),
        **_response_fields(raw),
    )


def parse_crew_request_list_response(
    raw: Mapping[str, Any],
) -> CrewRequestListResponse:
    _validate_strict_read_envelope(raw)
    items = tuple(
        CrewRequestOption(
            **_nullable_string_fields(
                _row(v, "crew request list prsList"),
                _CREW_REQUEST_OPTION_FIELDS,
                "crew request option",
            ),
            raw=_row(v, "crew request list prsList"),
        )
        for v in _optional_list(raw, "prsList", "crew request list")
    )
    return CrewRequestListResponse(items=items, **_response_fields(raw))


def parse_service_status_response(
    raw: Mapping[str, Any],
) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))


def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    for value in _nested_rows(raw, "cart_infos", "cart_info", "cart list"):
        item = _row(value, "cart list cart_info")
        items.append(
            CartItem(
                **_nullable_string_fields(item, _CART_ITEM_FIELDS, "cart item"),
                ticket_count=_optional_integer(item, "h_tk_cnt", "cart item"),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


def parse_deposit_bank_response(
    raw: Mapping[str, Any],
) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = tuple(
        DepositBank(
            **_nullable_string_fields(
                _row(v, "deposit bank list dptnBank"),
                _DEPOSIT_BANK_FIELDS,
                "deposit bank",
            ),
            raw=_row(v, "deposit bank list dptnBank"),
        )
        for v in _optional_list(raw, "dptnBank", "deposit bank list")
    )
    return DepositBankListResponse(items=items, **_response_fields(raw))


def parse_delay_discount_ticket_response(
    raw: Mapping[str, Any],
) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    rows = _nested_rows(raw, "disc_infos", "disc_info", "delay discount ticket list")
    items = tuple(
        DelayDiscountTicket(
            **_nullable_string_fields(
                _row(v, "delay discount ticket list disc_info"),
                _DELAY_DISCOUNT_TICKET_FIELDS,
                "delay discount ticket",
            ),
            raw=_row(v, "delay discount ticket list disc_info"),
        )
        for v in rows
    )
    return DelayDiscountTicketListResponse(items=items, **_response_fields(raw))


def parse_discount_coupon_response(
    raw: Mapping[str, Any],
) -> DiscountCouponListResponse:
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"WRG000000"}),
    )
    if empty:
        return DiscountCouponListResponse(**_response_fields(raw))
    items = []
    rows = _nested_rows(
        raw,
        "coupon_infos",
        "coupon_info",
        "discount coupon list",
    )
    for value in rows:
        item = _row(value, "discount coupon list coupon_info")
        discount_values = _present_strings(
            item,
            (
                "h_disc_rt_amt_dv_cd",
                "h_inwk_fare_disc_rt_amt",
                "h_inwk_prc_disc_rt_amt",
                "h_wknd_fare_disc_rt_amt",
                "h_wknd_prc_disc_rt_amt",
            ),
            "discount coupon",
        )
        remarks = _present_strings(
            item,
            ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont"),
            "discount coupon",
        )
        items.append(
            DiscountCoupon(
                guide=_optional_string(item, "guide", "discount coupon"),
                expiration_date=_optional_string(
                    item, "h_fdcert_mg_cls_dt", "discount coupon"
                ),
                discount_values=discount_values,
                remarks=remarks,
                coupon_no=_optional_string(
                    item, "h_cpn_no", "discount coupon"
                ),
                raw=item,
            )
        )
    return DiscountCouponListResponse(
        items=tuple(items),
        current_page=_optional_integer(raw, "h_page_no", "coupon response"),
        total_pages=_optional_integer(
            raw, "h_tot_page_cnt", "coupon response"
        ),
        **_response_fields(raw),
    )


def parse_pass_availability_response(
    raw: Mapping[str, Any],
) -> PassAvailabilityResponse:
    # A live pass.passInfoList success nests its code as main_info.h_msg_cd and
    # leaves the top level with strResult only, so the top-level envelope check
    # rejected every successful response. Same result-only accommodation as
    # parse_pass_menu_response.
    _validate_envelope(raw, allow_result_only_success=True)
    open_dates = []
    for value in _optional_list(raw, "pass_info", "pass availability"):
        item = _row(value, "pass availability pass_info")
        date = _optional_string(item, "h_use_open_dt", "pass date")
        if date is not None:
            open_dates.append(date)
    ticket_issue_dates = []
    for value in _optional_list(raw, "ticket_info", "pass availability"):
        item = _row(value, "pass availability ticket_info")
        date = _optional_string(item, "h_ise_dt2", "ticket issue date")
        if date is not None:
            ticket_issue_dates.append(date)
    offices = []
    for value in _optional_list(raw, "wct_info", "pass availability"):
        item = _row(value, "pass availability wct_info")
        offices.append(
            PassOffice(
                code=_optional_string(item, "eng_cd_val", "pass office"),
                display_name=_optional_string(
                    item, "kor_cd_val", "pass office"
                ),
                raw=item,
            )
        )
    return PassAvailabilityResponse(
        open_dates=tuple(open_dates),
        ticket_issue_dates=tuple(ticket_issue_dates),
        offices=tuple(offices),
        **_response_fields(raw),
    )


def parse_trip_menu_response(raw: Mapping[str, Any]) -> TripMenuResponse:
    _validate_envelope(raw)
    items = []
    for value in _optional_list(raw, "menuList", "trip menu"):
        item = _row(value, "trip menu menuList")
        contents = tuple(
            TripMenuContent(
                **_nullable_string_fields(
                    _row(cv, "trip menu contList"),
                    _TRIP_MENU_CONTENT_FIELDS,
                    "trip menu content",
                ),
                raw=_row(cv, "trip menu contList"),
            )
            for cv in _optional_list(item, "contList", "trip menu")
        )
        items.append(
            TripMenuItem(
                **_nullable_string_fields(item, _TRIP_MENU_ITEM_FIELDS, "trip menu item"),
                contents=contents,
                raw=item,
            )
        )
    return TripMenuResponse(
        items=tuple(items),
        popup_message=_optional_string(raw, "poppMsg", "trip menu response"),
        **_response_fields(raw),
    )


def parse_product_reservation_list_response(
    raw: Mapping[str, Any],
) -> ProductReservationListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    main = _optional_mapping(raw, "mainInfo", "product reservation list")
    if main is None:
        return ProductReservationListResponse(**_response_fields(raw))
    items = tuple(
        ProductReservation(
            **_nullable_string_fields(
                _row(v, "product reservation list entity"),
                _PRODUCT_RESERVATION_FIELDS,
                "product reservation",
            ),
            raw=_row(v, "product reservation list entity"),
        )
        for v in _optional_list(main, "entity", "product reservation list")
    )
    return ProductReservationListResponse(
        items=items,
        total_count=_optional_integer(main, "strTotCnt", "product reservation list"),
        **_response_fields(raw),
    )


def parse_product_detail_response(
    raw: Mapping[str, Any],
) -> ProductDetailResponse:
    _validate_envelope(raw)
    main = _optional_mapping(raw, "mainInfo", "product detail")
    if main is None:
        return ProductDetailResponse(**_response_fields(raw))
    included_items = []
    for value in _optional_list(main, "entityOne", "product detail"):
        item = _row(value, "product detail entityOne")
        name = _optional_string(item, "strGdConsItmNm", "included item")
        if name is not None:
            included_items.append(name)
    return ProductDetailResponse(
        **_nullable_string_fields(main, _PRODUCT_DETAIL_FIELDS, "product detail"),
        included_item_names=tuple(included_items),
        detail_raw=main,
        **_response_fields(raw),
    )


def parse_ticket_receipt_response(
    raw: Mapping[str, Any],
) -> TicketReceiptResponse:
    _validate_envelope(raw)
    items = []
    rows = _nested_rows(raw, "receipt_infos", "receipt_info", "ticket receipt")
    for value in rows:
        item = _row(value, "ticket receipt receipt_info")
        payments = []
        for pv in _optional_list(item, "stl_info", "ticket receipt"):
            payment = _row(pv, "ticket receipt stl_info")
            payments.append(
                ReceiptPayment(
                    **_nullable_string_fields(
                        payment, _RECEIPT_PAYMENT_FIELDS, "receipt payment"
                    ),
                    installment_months=_optional_integer(
                        payment, "h_ismt_mnth_num", "receipt payment"
                    ),
                    amount=_optional_integer(
                        payment, "h_stl_amt", "receipt payment"
                    ),
                    raw=payment,
                )
            )
        cash_receipts = []
        for cv in _optional_list(item, "cash_rcet_info", "ticket receipt"):
            cash = _row(cv, "ticket receipt cash_rcet_info")
            cash_receipts.append(
                ReceiptCashPayment(
                    **_nullable_string_fields(
                        cash, _RECEIPT_CASH_PAYMENT_FIELDS,
                        "receipt cash payment",
                    ),
                    total_approved_amount=_optional_integer(
                        cash, "h_tot_apv_amt", "receipt cash payment"
                    ),
                    raw=cash,
                )
            )
        items.append(
            TicketReceipt(
                **_nullable_string_fields(item, _TICKET_RECEIPT_FIELDS, "ticket receipt"),
                passenger_counts=(
                    _optional_integer(item, "h_psg_type1_cnt", "ticket receipt"),
                    _optional_integer(item, "h_psg_type2_cnt", "ticket receipt"),
                    _optional_integer(item, "h_psg_type3_cnt", "ticket receipt"),
                ),
                received_amount=_optional_integer(item, "h_rcvd_amt", "ticket receipt"),
                card_refund_amount=_optional_integer(item, "h_crd_ret_amt", "ticket receipt"),
                refund_fee=_optional_integer(item, "h_ret_fee", "ticket receipt"),
                refund_received_amount=_optional_integer(item, "h_ret_rcvd_amt", "ticket receipt"),
                point_refund_amount=_optional_integer(item, "h_xpoint_ret_amt", "ticket receipt"),
                payments=tuple(payments),
                cash_receipts=tuple(cash_receipts),
                raw=item,
            )
        )
    return TicketReceiptResponse(items=tuple(items), **_response_fields(raw))


def parse_reservation_history_response(
    raw: Mapping[str, Any],
) -> ReservationHistoryResponse:
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"P100"}),
    )
    if empty:
        return ReservationHistoryResponse(**_response_fields(raw))
    trains = []
    journeys = _nested_rows(raw, "jrny_infos", "jrny_info", "reservation history")
    for journey_value in journeys:
        journey = _row(journey_value, "reservation history jrny_info")
        train_wrapper = _optional_mapping(
            journey, "train_infos", "reservation history"
        )
        if train_wrapper is None:
            continue
        for train_value in _optional_list(
            train_wrapper, "train_info", "reservation history"
        ):
            train = _row(train_value, "reservation history train_info")
            trains.append(
                ReservationHistoryTrain(
                    **_nullable_string_fields(
                        train, _RESERVATION_HISTORY_TRAIN_FIELDS,
                        "reservation history train",
                    ),
                    seat_count=_optional_integer(
                        train, "h_tot_seat_cnt",
                        "reservation history train",
                    ),
                    standing_count=_optional_integer(
                        train, "h_tot_stnd_cnt",
                        "reservation history train",
                    ),
                    raw=train,
                )
            )
    return ReservationHistoryResponse(items=tuple(trains), **_response_fields(raw))


def parse_free_seat_car_response(
    raw: Mapping[str, Any],
) -> FreeSeatCarResponse:
    _validate_strict_read_envelope(raw)
    return FreeSeatCarResponse(
        title=_optional_string(raw, "fresTtl", "free seat car response"),
        car_no=_optional_string(
            raw,
            "fresScarNo",
            "free seat car response",
        ),
        content=_optional_string(
            raw,
            "fresCont",
            "free seat car response",
        ),
        **_response_fields(raw),
    )


def parse_guide_seat_condition_response(
    raw: Mapping[str, Any],
) -> GuideSeatConditionResponse:
    _validate_strict_read_envelope(raw)
    return GuideSeatConditionResponse(**_response_fields(raw))


def _parse_train_schedule_item(
    raw: Mapping[str, Any],
) -> TrainScheduleItem:
    return TrainScheduleItem(
        **_nullable_string_fields(raw, _TRAIN_SCHEDULE_ITEM_FIELDS, "train schedule item"),
        raw=raw,
    )


def _parse_train_schedule_container(
    raw: Mapping[str, Any],
    context: str,
) -> tuple[str | None, tuple[TrainScheduleItem, ...]]:
    container = _optional_mapping(raw, "trn_infos", context)
    if container is None:
        return None, ()
    merge_flag = _optional_string(
        container,
        "h_merge_rsv_psb_flg",
        context,
    )
    trains = tuple(
        _parse_train_schedule_item(_row(value, f"{context} trn_info"))
        for value in _optional_list(container, "trn_info", context)
    )
    return merge_flag, trains


def parse_seat_assignment_schedule_response(
    raw: Mapping[str, Any],
) -> SeatAssignmentScheduleResponse:
    _validate_strict_read_envelope(raw)
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        "seat assignment schedule",
    )
    return SeatAssignmentScheduleResponse(
        next_page_flag=_optional_string(
            raw,
            "h_next_pg_flg",
            "seat assignment schedule",
        ),
        merge_reservation_possible_flag=merge_flag,
        trains=trains,
        **_response_fields(raw),
    )


def parse_merge_seats_inquiry_response(
    raw: Mapping[str, Any],
) -> MergeSeatsInquiryResponse:
    _validate_strict_read_envelope(raw)
    stations = []
    for value in _optional_list(raw, "midStnList", "merge seats inquiry"):
        station = _row(value, "merge seats inquiry midStnList")
        stations.append(
            IntermediateStation(
                code=_optional_string(
                    station,
                    "rsStnCd",
                    "merge seats intermediate station",
                ),
                name=_optional_string(
                    station,
                    "rsStnNm",
                    "merge seats intermediate station",
                ),
                run_order=_optional_string(
                    station,
                    "runOrdr",
                    "merge seats intermediate station",
                ),
                raw=station,
            )
        )
    merge_flag, trains = _parse_train_schedule_container(
        raw,
        "merge seats inquiry",
    )
    return MergeSeatsInquiryResponse(
        merge_reservation_possible_flag=merge_flag,
        intermediate_stations=tuple(stations),
        trains=trains,
        **_response_fields(raw),
    )


def parse_pass_schedule_response(
    raw: Mapping[str, Any],
) -> PassScheduleResponse:
    # WRG000000 is a non-fatal empty result (CommutationInquiryActivity.java:182).
    empty = _validate_envelope(raw, accepted_empty_codes=frozenset({"WRG000000"}))
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError("KORAIL pass schedule strResult must be exact SUCC")
    schedules = []
    for schedule_value in _optional_list(raw, "schedule_info", "pass schedule"):
        schedule = _row(schedule_value, "pass schedule schedule_info")
        trains = tuple(
            PassScheduleTrain(
                **_nullable_string_fields(
                    _row(tv, "pass schedule train_list"),
                    _PASS_SCHEDULE_TRAIN_FIELDS,
                    "pass schedule train",
                ),
                raw=_row(tv, "pass schedule train_list"),
            )
            for tv in _optional_list(schedule, "train_list", "pass schedule schedule_info")
        )
        schedules.append(PassScheduleInfo(trains=trains, raw=schedule))
    return PassScheduleResponse(
        schedules=tuple(schedules),
        **_response_fields(raw),
    )


_KORAIL_POINT_SUMMARY_FIELDS = {
    "korail_point": "h_korail_point",
    "discount_coupon_count": "h_disc_coup_cnt",
    "delay_discount_count": "h_delay_cnt",
    "disability_flag": "h_hdcp_flg",
    "welfare_discount_class_name": "h_subt_dcs_cl_nm",
    "welfare_discount_class_code": "h_subt_dcs_cl_cd",
    "customer_lead_flag_name": "h_cust_lead_flg_nm",
    "phone_verified_flag": "h_cp_athn_flg",
    "email_verified_flag": "h_emil_athn_flg",
    "contact_channel_content": "h_cntc_chn_cont1",
    "naver_linked_flag": "h_logn_tp_cd1",
    "kakao_linked_flag": "h_logn_tp_cd2",
    "google_linked_flag": "h_logn_tp_cd4",
    "apple_linked_flag": "h_logn_tp_cd5",
}

_MILEAGE_HISTORY_FIELDS = {
    "page_count": "pgCnt",
    "total_available_rail_point": "totAvlRailPontValNum",
    "total_available_rail_point_1": "totAvlRailPontValNum1",
    "total_available_affiliate_point": "totAvlAfltPontValNum",
    "total_accumulated_rail_point_1": "totAcmRailPontValNum1",
    "total_used_rail_point_1": "totUseRailPontValNum1",
    "rail_now_saved_point_1": "railNowSavePontValNum1",
    "expiring_point_value": "delPontValNum",
    "ktx_mileage_info": "ktxMlgInfo",
}

_MILEAGE_HISTORY_ENTRY_FIELDS = {
    "departure_date": "dptDt",
    "point_division_name": "pontDvNm",
    "accrual_division_name": "mlgAcmDvCdNm",
    "receipt_division_name": "rcpDvNm",
    "point_amount": "pontAmt",
    "saved_point_value": "savePontValNum",
    "settlement_amount": "stlAmt",
}


def parse_korail_point_summary_response(
    raw: Mapping[str, Any],
) -> KorailPointSummaryResponse:
    _validate_strict_read_envelope(raw)
    return KorailPointSummaryResponse(
        # Scalar rather than string: every point total here is a Java String in
        # the DAO but a number in spirit, and the app reads them back through
        # N.getInteger / N.getDecimalFormatString
        # (MileageHistoryActivity.java:574-580), which would not care either
        # way. Neither shape has been observed live.
        **_nullable_scalar_fields(
            raw,
            _KORAIL_POINT_SUMMARY_FIELDS,
            "korail point summary",
        ),
        **_response_fields(raw),
    )


def parse_mileage_history_response(
    raw: Mapping[str, Any],
) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = []
    for value in _optional_list(raw, "specList", "mileage history"):
        item = _row(value, "mileage history specList")
        entries.append(
            MileageHistoryEntry(
                **_nullable_scalar_fields(
                    item,
                    _MILEAGE_HISTORY_ENTRY_FIELDS,
                    "mileage history entry",
                ),
                raw=item,
            )
        )
    return MileageHistoryResponse(
        **_nullable_scalar_fields(
            raw,
            _MILEAGE_HISTORY_FIELDS,
            "mileage history",
        ),
        entries=tuple(entries),
        **_response_fields(raw),
    )


_DISCOUNT_CARD_USAGE_FIELDS = {
    "passenger_name": "custNm",
    "departure_station_name": "dptStnNm",
    "arrival_station_name": "arvStnNm",
    "run_date": "runDt1",
    "additional_user_flag": "apdUsrFlg",
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
    "commuter_price": "cmtrPrc",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "detour_code": "dturCd",
    "detour_name": "dturNm",
    "route_code": "routCd",
    "station_string_info": "stationStringInfo",
}


def parse_discount_card_usage_response(
    raw: Mapping[str, Any],
) -> DiscountCardUsageListResponse:
    _validate_strict_read_envelope(raw)
    items = []
    for value in _optional_list(raw, "tkUseList", "discount card usage"):
        item = _row(value, "discount card usage tkUseList")
        items.append(
            DiscountCardUsage(
                **_nullable_string_fields(
                    item,
                    _DISCOUNT_CARD_USAGE_FIELDS,
                    "discount card usage",
                ),
                raw=item,
            )
        )
    return DiscountCardUsageListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


def parse_discount_card_schedule_response(
    raw: Mapping[str, Any],
) -> DiscountCardScheduleResponse:
    _validate_strict_read_envelope(raw)
    trains = []
    for value in _optional_list(raw, "trnScdlList", "discount card schedule"):
        item = _row(value, "discount card schedule trnScdlList")
        trains.append(
            DiscountCardScheduleTrain(
                # Scalar rather than string: cmtrPrc is a fare and the
                # station-order fields are ordinals, and KORAIL has already
                # been caught sending a declared-String number on three
                # separate reads (see _optional_scalar_string). This route has
                # never been seen live, so the tolerant reader is the correct
                # default rather than a concession.
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_SCHEDULE_TRAIN_FIELDS,
                    "discount card schedule train",
                ),
                raw=item,
            )
        )
    return DiscountCardScheduleResponse(
        following_page_exists=_optional_string(
            raw,
            "fllwPgExt",
            "discount card schedule",
        ),
        trains=tuple(trains),
        **_response_fields(raw),
    )


_MULTI_CHILD_FIELDS = {
    "birth_date": "btdt",
    "customer_family_name": "custFmlyNm",
    "discount_kind_code": "dcntKndCd",
    "family_sequence": "fmlySqno",
    "passenger_type_code": "psgTpCd",
    "passenger_type_name": "psgTpNm",
    "room_class_code": "psrmClCd",
    "requested_discount_kind_code": "rqDcntKndCd",
}

_CUSTOMER_TRIP_FIELDS = {
    "additional_seat_attribute_code": "addSeatAttCd",
    "adult_disabled_person_count": "adltHdcpPrnb",
    "adult_count": "adulCnt",
    "arrival_station_code": "arvStnCd",
    "arrival_station_name": "arvStnNm",
    "baby_accompanying_person_count": "babyAcpnPrnb",
    "changed_at": "chgDttm",
    "changed_by": "chgUsrId",
    "child_count": "chilCnt",
    "child_disabled_person_count": "chldHdcpPrnb",
    "customer_management_no": "custMgNo",
    "day_code": "dayCd",
    "direction_seat_attribute_group_code": "dirSeatAttGpCd",
    "direct_transfer_division_code": "dirtChtnDvCd",
    "departure_station_code": "dptStnCd",
    "departure_station_name": "dptStnNm",
    "early_train_departure_time": "ectbTrnDptTm",
    "elderly_person_count": "edrPrnb",
    "included_flag": "inclFlg",
    "job_start_hour": "jobStHr",
    "location_seat_attribute_group_code": "locSeatAttGpCd",
    "media_division_code": "medDvCd",
    "room_class_code": "psrmClCd",
    "passenger_total": "ptwtTtl",
    "registered_at": "regDttm",
    "registration_sequence": "regSqno",
    "registered_by": "regUsrId",
    "trip_day_no": "tripDno",
    "train_classification_code": "trnClsfCd",
    "train_connection_flag": "trnCnecFlg",
    "train_group_code": "trnGpCd",
    "usage_day_no": "utlDno",
}

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
    "reservation_specification_url": "rsvSpecUrl",
    "usage_close_date": "utlClsDt",
    "usage_start_date": "utlStDt",
}


def parse_multi_child_discount_target_response(
    raw: Mapping[str, Any],
) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = []
    for value in _optional_list(raw, "fmlyList", "multi-child targets"):
        item = _row(value, "multi-child targets fmlyList")
        targets.append(
            MultiChildDiscountTarget(
                **_nullable_string_fields(
                    item,
                    _MULTI_CHILD_FIELDS,
                    "multi-child target",
                ),
                raw=item,
            )
        )
    return MultiChildDiscountTargetResponse(
        targets=tuple(targets),
        **_response_fields(raw),
    )


def parse_customer_trip_info_response(
    raw: Mapping[str, Any],
) -> CustomerTripInfoResponse:
    _validate_strict_read_envelope(raw)
    trips = []
    for value in _optional_list(raw, "mainList", "customer trip info"):
        item = _row(value, "customer trip info mainList")
        trips.append(
            CustomerTripInfo(
                **_nullable_string_fields(
                    item,
                    _CUSTOMER_TRIP_FIELDS,
                    "customer trip info",
                ),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
        **_response_fields(raw),
    )


def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for value in _optional_list(raw, "addSrvList", "MaaS service details"):
        item = _row(value, "MaaS service details addSrvList")
        details.append(
            MaasServiceDetail(
                **_nullable_string_fields(
                    item,
                    _MAAS_DETAIL_FIELDS,
                    "MaaS service detail",
                ),
                raw=item,
            )
        )
    return MaasServiceDetailListResponse(
        details=tuple(details),
        **_response_fields(raw),
    )


def parse_trip_change_date_response(
    raw: Mapping[str, Any],
) -> TripChangeDateResponse:
    _validate_strict_read_envelope(raw)
    dates = []
    for value in _optional_list(raw, "tripChgDates", "trip change dates"):
        if not isinstance(value, str):
            raise KorailProtocolError(
                "KORAIL trip change dates field tripChgDates must contain only strings"
            )
        dates.append(value)
    return TripChangeDateResponse(
        last_run_date=_optional_string(raw, "lastRunDt", "trip change dates"),
        trip_change_date=_optional_string(
            raw,
            "tripChgDate",
            "trip change dates",
        ),
        trip_change_dates=tuple(dates),
        **_response_fields(raw),
    )


def parse_tour_train_info_response(
    raw: Mapping[str, Any],
) -> TourTrainInfoResponse:
    _validate_strict_read_envelope(raw)
    seat_infos = _optional_mapping(raw, "seat_infos", "tour train info")
    seats = []
    if seat_infos is not None:
        for value in _optional_list(
            seat_infos,
            "seat_info",
            "tour train seat infos",
        ):
            seat = _row(value, "tour train seat_info")
            additional_wrapper = _optional_mapping(
                seat,
                "seat_add_infos",
                "tour train seat info",
            )
            additional_infos = []
            if additional_wrapper is not None:
                for additional_value in _optional_list(
                    additional_wrapper,
                    "seat_add_info",
                    "tour train additional seat infos",
                ):
                    additional = _row(
                        additional_value,
                        "tour train seat_add_info",
                    )
                    # TourTrainInfoDao.SeatAddInfo.h_psg_num is Java `int`
                    # (TourTrainInfoDao.java:14); the h_-prefixed backend
                    # serializes such ints as quoted strings on the wire (proven
                    # for sibling h_srcar_no/h_rest_seat_cnt), and Gson coerces
                    # them, so accept the string form too.
                    passenger_count = _required_integer(
                        additional,
                        "h_psg_num",
                        "tour train seat",
                    )
                    additional_infos.append(
                        TourTrainSeatAdditionalInfo(
                            passenger_count=passenger_count,
                            raw=additional,
                        )
                    )
            seats.append(
                TourTrainSeatInfo(
                    seat_attribute_code=_optional_string(
                        seat,
                        "h_seat_att_cd",
                        "tour train seat info",
                    ),
                    additional_infos=tuple(additional_infos),
                    raw=seat,
                )
            )
    return TourTrainInfoResponse(
        seat_infos=tuple(seats),
        **_response_fields(raw),
    )


_GIFT_TICKET_FIELDS = {
    "integrated_customer_name_1": "intgCustNm1",
    "integrated_customer_name_2": "intgCustNm2",
    "current_point_value": "nowPontValNum",
    "received_date": "rcvDt",
    "return_amount": "retAmt",
    "return_date": "retDt",
    "return_time": "retTm",
    "ticket_id": "tkId",
    "transaction_amount": "txnAmt",
    "usage_close_date": "useClsDt",
    "used_point_value": "usePontValNum",
    "usable_flag": "usePsbFlg",
}


def parse_gift_ticket_list_response(
    raw: Mapping[str, Any],
) -> GiftTicketListResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for value in _optional_list(raw, "gdList", "gift-ticket list"):
        item = _row(value, "gift-ticket gdList")
        tickets.append(
            GiftTicket(
                **_nullable_string_fields(
                    item,
                    _GIFT_TICKET_FIELDS,
                    "gift-ticket",
                ),
                raw=item,
            )
        )
    return GiftTicketListResponse(
        tickets=tuple(tickets),
        query_count=_optional_string(raw, "qryCnt", "gift-ticket list"),
        next_query_no=_optional_string(
            raw,
            "qryNumNext",
            "gift-ticket list",
        ),
        **_response_fields(raw),
    )


def _primitive_json_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    value = data.get(key)
    if value is None:
        return 0
    if type(value) is not int:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a JSON integer or null"
        )
    return value


def parse_commuter_info_response(
    raw: Mapping[str, Any],
) -> CommuterInfoResponse:
    _validate_strict_read_envelope(raw)
    passenger_options = []
    for value in _optional_list(raw, "psgList", "commuter info"):
        item = _row(value, "commuter info psgList")
        passenger_options.append(
            CommuterPassengerOption(
                commuter_usage_age_code=_optional_string(
                    item,
                    "cmtrUtlAgeCd",
                    "commuter passenger option",
                ),
                common_code_name=_optional_string(
                    item,
                    "comnCdNm",
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
        additional_service_goods_flag=_optional_string(
            raw,
            "addSrvGdFlg",
            "commuter info",
        ),
        companion_flag=_optional_string(raw, "cmpaFlg", "commuter info"),
        commuter_kind_code=_optional_string(
            raw,
            "cmtrKndCd",
            "commuter info",
        ),
        commuter_usage_age_code=_optional_string(
            raw,
            "cmtrUtlAgeCd",
            "commuter info",
        ),
        menu_id=_optional_string(raw, "menuId", "commuter info"),
        popup_message=_optional_string(raw, "poppMsg", "commuter info"),
        promotion_message=_optional_string(
            raw,
            "prmoMsg",
            "commuter info",
        ),
        promotion_url=_optional_string(raw, "prmoUrl", "commuter info"),
        seat_attribute_code=_optional_string(
            raw,
            "seatAttCd1",
            "commuter info",
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


_PRICE_FARE_FIELDS = {
    "journey_sequence": "jrnySqno",
    "room_class_name": "psrmClNm",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "total_amount": "sumAmt",
    "train_no": "trnNo",
}


def parse_price_fare_quote_response(
    raw: Mapping[str, Any],
) -> PriceFareQuoteResponse:
    _validate_strict_read_envelope(raw)
    fares = []
    for value in _optional_list(raw, "prcList", "price fare quote"):
        item = _row(value, "price fare quote prcList")
        fares.append(
            PriceFare(
                **_nullable_string_fields(
                    item,
                    _PRICE_FARE_FIELDS,
                    "price fare",
                ),
                raw=item,
            )
        )
    return PriceFareQuoteResponse(
        fares=tuple(fares),
        **_response_fields(raw),
    )


_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "member_card_no": "mbCrdNo",
}

_PBP_ACCEPTANCE_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
    "return_password": "tkRetPwd",
}

_PBP_ACCEPTANCE_JOURNEY_FIELDS = {
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "journey_type_code": "jrnyTpCd",
    "member_division_name": "mbDvNm",
    "acceptance_kind_name": "pbpAcepKndNm",
    "pbp_reservation_no": "pbpRsvNo",
    "registered_date": "regDt",
    "withdrawal_possible_flag": "wdrwPsbFlg",
}

_PBP_ACCEPTANCE_SEAT_FIELDS = {
    "passenger_type_division_name": "psgTpDvNm",
    "room_class_code": "psrmClCd",
    "room_class_name": "psrmClNm",
    "seat_no": "seatNo",
}

_PLATFORM_NUMBER_TICKET_FIELDS = {
    "sale_date": "saleDt",
    "sale_sequence": "saleSqno",
    "sale_window_no": "saleWctNo",
    "ticket_return_no": "tkRetNo",
    "return_password": "tkRetPwd",
}

_RECENT_DELIVERY_RECIPIENT_FIELDS = {
    "acceptance_customer_management_flag": "acepCustMgFlg",
    "acceptance_customer_management_no": "acepCustMgNo",
    "acceptance_customer_name": "acepCustNm",
    "acceptance_customer_phone": "acepCustTeln",
    "acceptance_customer_phone_2": "acepCustTeln2",
    "member_card_no": "mbCrdNo",
}


def parse_delivery_recipient_response(
    raw: Mapping[str, Any],
) -> DeliveryRecipientResponse:
    _validate_strict_read_envelope(raw)
    return DeliveryRecipientResponse(
        **_nullable_string_fields(
            raw,
            _DELIVERY_RECIPIENT_FIELDS,
            "delivery recipient",
        ),
        **_response_fields(raw),
    )


def parse_ticket_duplication_check_response(
    raw: Mapping[str, Any],
) -> TicketDuplicationCheckResponse:
    _validate_strict_read_envelope(raw)
    return TicketDuplicationCheckResponse(
        # DuplicationCheckResponse.rsvCnt is Java `int`
        # (TicketDuplicationCheckDao.java:27); Gson coerces a quoted numeric
        # string, so accept both "0" and 0 like the app.
        reservation_count=_required_integer(
            raw,
            "rsvCnt",
            "ticket duplication check",
        ),
        **_response_fields(raw),
    )


def parse_pbp_acceptance_specification_response(
    raw: Mapping[str, Any],
) -> PbpAcceptanceSpecificationResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket_value in _optional_list(
        raw,
        "tkList",
        "PBP acceptance specification",
    ):
        ticket = _row(ticket_value, "PBP acceptance specification tkList")
        journeys = []
        for journey_value in _optional_list(
            ticket,
            "jrnyList",
            "PBP acceptance ticket",
        ):
            journey = _row(journey_value, "PBP acceptance ticket jrnyList")
            seats = []
            for seat_value in _optional_list(
                journey,
                "seatList",
                "PBP acceptance journey",
            ):
                seat = _row(seat_value, "PBP acceptance journey seatList")
                seats.append(
                    PbpAcceptanceSeat(
                        **_nullable_string_fields(
                            seat,
                            _PBP_ACCEPTANCE_SEAT_FIELDS,
                            "PBP acceptance seat",
                        ),
                        # PbpAcepSpecDao.Seat.scarNo is Java `int`
                        # (PbpAcepSpecDao.java:102); Gson coerces a quoted
                        # numeric string, so accept both "3" and 3.
                        car_no=_required_integer(
                            seat,
                            "scarNo",
                            "PBP acceptance seat",
                        ),
                        raw=seat,
                    )
                )
            journeys.append(
                PbpAcceptanceJourney(
                    **_nullable_string_fields(
                        journey,
                        _PBP_ACCEPTANCE_JOURNEY_FIELDS,
                        "PBP acceptance journey",
                    ),
                    seats=tuple(seats),
                    raw=journey,
                )
            )
        tickets.append(
            PbpAcceptanceTicket(
                **_nullable_string_fields(
                    ticket,
                    _PBP_ACCEPTANCE_TICKET_FIELDS,
                    "PBP acceptance ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return PbpAcceptanceSpecificationResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


def parse_platform_number_response(
    raw: Mapping[str, Any],
) -> PlatformNumberResponse:
    _validate_strict_read_envelope(raw)
    tickets = []
    for ticket_value in _optional_list(raw, "tkList", "platform number"):
        ticket = _row(ticket_value, "platform number tkList")
        journeys = []
        for journey_value in _optional_list(
            ticket,
            "jrnyList",
            "platform number ticket",
        ):
            journey = _row(journey_value, "platform number ticket jrnyList")
            journeys.append(
                PlatformNumberJourney(
                    platform_no=_optional_string(
                        journey,
                        "plfNo",
                        "platform number journey",
                    ),
                    raw=journey,
                )
            )
        tickets.append(
            PlatformNumberTicket(
                **_nullable_string_fields(
                    ticket,
                    _PLATFORM_NUMBER_TICKET_FIELDS,
                    "platform number ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return PlatformNumberResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )


def parse_recent_delivery_history_response(
    raw: Mapping[str, Any],
) -> RecentDeliveryHistoryResponse:
    _validate_strict_read_envelope(raw)
    recipients = []
    for value in _optional_list(raw, "acepList", "recent delivery history"):
        recipient = _row(value, "recent delivery history acepList")
        recipients.append(
            RecentDeliveryRecipient(
                **_nullable_string_fields(
                    recipient,
                    _RECENT_DELIVERY_RECIPIENT_FIELDS,
                    "recent delivery recipient",
                ),
                raw=recipient,
            )
        )
    return RecentDeliveryHistoryResponse(
        recipients=tuple(recipients),
        **_response_fields(raw),
    )


_PRODUCT_RECOMMENDATION_FIELDS = {
    "discount_amount": "dcntAmt",
    "discount_surcharge_rate": "dcntSurRt",
    "fare_amount_percent_division_code": "famtPctDvCd",
    "goods_name": "gdNm",
    "goods_no": "gdNo",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "received_price_2": "rcvdPrc2",
}

_PRODUCT_TRAIN_FIELDS = {
    "detour_via_popup": "dturViaPopp",
    "elevator_damage_control": "elevDmgCtrl",
    "arrival_date": "h_arv_dt",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "arrival_station_construction_order": "h_arv_stn_cons_ordr",
    "arrival_station_run_order": "h_arv_stn_run_ordr",
    "arrival_time": "h_arv_tm",
    "car_type_name": "h_car_tp_nm",
    "change_train_division_code": "h_chg_trn_dv_cd",
    "change_train_sequence": "h_chg_trn_seq",
    "connection_traffic_need_time": "h_cnec_trfc_nd_hm",
    "connection_traffic_possible_flag": "h_cnec_trfc_psb_flg",
    "connection_traffic_received_price": "h_cnec_trfc_rcvd_prc",
    "delayed_sale_flag": "h_dlay_sale_flg",
    "departure_date": "h_dpt_dt",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "departure_station_construction_order": "h_dpt_stn_cons_ordr",
    "departure_station_run_order": "h_dpt_stn_run_ordr",
    "departure_time": "h_dpt_tm",
    "detour_flag": "h_dtour_flg",
    "detour_text": "h_dtour_txt",
    "expected_delay_hour": "h_expct_dlay_hr",
    "expected_departure_delay_count": "h_expn_dpt_dlay_tnum",
    "free_reservation_code": "h_free_rsv_cd",
    "free_seat_car_count": "h_free_sracar_cnt",
    "general_room_class_name": "h_gen_psrm_cl_nm",
    "general_reservation_code": "h_gen_rsv_cd",
    "general_reservation_code_2": "h_gen_rsv_cd2",
    "information_text": "h_info_txt",
    "journey_reservation_code": "h_jrny_rsv_cd",
    "journey_reservation_name": "h_jrny_rsv_nm",
    "nonstop_message": "h_nonstop_msg",
    "nonstop_message_text": "h_nonstop_msg_txt",
    "popup_message": "h_popup_msg",
    "received_amount": "h_rcvd_amt",
    "received_fare": "h_rcvd_fare",
    "received_price_2": "h_rcvd_prc2",
    "road_seat_map_flag": "h_rd_seat_map_flg",
    "reservation_possible_name": "h_rsv_psb_nm",
    "run_date": "h_run_dt",
    "run_time": "h_run_tm",
    "seat_attribute_code": "h_seat_att_cd",
    "simultaneous_train_flag": "h_smns_trn_flg",
    "special_discount_rate": "h_spe_disc_rt",
    "special_room_class_name": "h_spe_psrm_cl_nm",
    "special_reservation_code": "h_spe_rsv_cd",
    "special_reservation_code_2": "h_spe_rsv_cd2",
    "special_reservation_possible_name": "h_spe_rsv_psb_nm",
    "station_popup_message": "h_station_popup_msg",
    "standing_reservation_code": "h_stnd_rsv_cd",
    "train_discount_general_rate": "h_train_disc_gen_rt",
    "train_discount_origin_rate": "h_train_disc_origin_rt",
    "train_classification_code": "h_trn_clsf_cd",
    "train_classification_name": "h_trn_clsf_nm",
    "train_group_code": "h_trn_gp_cd",
    "train_no": "h_trn_no",
    "use_time_care_article_content": "h_use_tim_care_atcl_cont",
    "waiting_reservation_flag": "h_wait_rsv_flg",
    "youth_mileage_application_flag": "h_yms_apl_flg",
    "goods_no": "txtGdNo",
}


def parse_product_train_inquiry_response(
    raw: Mapping[str, Any],
) -> ProductTrainInquiryResponse:
    _validate_strict_read_envelope(raw)
    wrapper = _optional_mapping(raw, "trn_infos", "product train inquiry")
    merge_flag = None
    trains = []
    if wrapper is not None:
        merge_flag = _optional_string(
            wrapper,
            "h_merge_rsv_psb_flg",
            "product train inquiry trn_infos",
        )
        for value in _optional_list(
            wrapper,
            "trn_info",
            "product train inquiry trn_infos",
        ):
            item = _row(value, "product train inquiry trn_info")
            recommendations = []
            for recommendation_value in _optional_list(
                item,
                "rcmdGdList",
                "product train inquiry train",
            ):
                recommendation = _row(
                    recommendation_value,
                    "product train inquiry rcmdGdList",
                )
                recommendations.append(
                    ProductRecommendation(
                        **_nullable_string_fields(
                            recommendation,
                            _PRODUCT_RECOMMENDATION_FIELDS,
                            "product recommendation",
                        ),
                        raw=recommendation,
                    )
                )
            trains.append(
                ProductTrain(
                    **_nullable_string_fields(
                        item,
                        _PRODUCT_TRAIN_FIELDS,
                        "product train",
                    ),
                    total_passenger_count=_primitive_json_integer(
                        item,
                        "totPsgCnt",
                        "product train",
                    ),
                    recommendations=tuple(recommendations),
                    raw=item,
                )
            )
    return ProductTrainInquiryResponse(
        early_train_no_next=_optional_string(
            raw,
            "h_ectb_trn_no_next",
            "product train inquiry",
        ),
        goods_no=_optional_string(raw, "h_gd_no", "product train inquiry"),
        next_page_flag=_optional_string(
            raw,
            "h_next_pg_flg",
            "product train inquiry",
        ),
        notice_message=_optional_string(
            raw,
            "h_notice_msg",
            "product train inquiry",
        ),
        preceding_train_no_next=_optional_string(
            raw,
            "h_prcd_trn_no_next",
            "product train inquiry",
        ),
        next_query_station_no=_optional_string(
            raw,
            "h_qry_st_no_next",
            "product train inquiry",
        ),
        result_count=_optional_string(
            raw,
            "h_rslt_cnt",
            "product train inquiry",
        ),
        next_train_no=_optional_string(
            raw,
            "h_trn_no_next",
            "product train inquiry",
        ),
        merge_reservation_possible_flag=merge_flag,
        trains=tuple(trains),
        **_response_fields(raw),
    )


_RESERVATION_SEAT_DETAIL_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "room_class_code": "h_psrm_cl_cd",
    "room_class_name": "h_psrm_cl_nm",
    # ReservationResponse.SeatInfo declares the passenger type as a CODE
    # (:304). No h_psg_tp_dv_nm exists anywhere in the decompiled app, so the
    # display-name variant is deliberately NOT mapped; an unmapped key stays
    # reachable through `raw`.
    "passenger_type_code": "h_psg_tp_cd",
    "received_amount": "h_rcvd_amt",
    "seat_price": "h_seat_prc",
    "seat_fare": "h_seat_fare",
    "seat_group_name": "h_sgr_nm",
}

_RESERVATION_DETAIL_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "reservation_change_no": "h_rsv_chg_no",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_time": "h_arv_tm",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
}

_TICKET_RESERVATION_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "window_no": "h_wct_no",
    "journey_count": "h_jrny_cnt",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "payment_flag": "h_payment_flg",
}


def parse_ticket_reservation_detail_response(
    raw: Mapping[str, Any],
) -> TicketReservationDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for value in _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
        "ticket reservation detail",
    ):
        journey = _row(value, "ticket reservation detail jrny_info")
        seats = []
        for seat_value in _nested_rows(
            journey,
            "seat_infos",
            "seat_info",
            "ticket reservation detail journey",
        ):
            seat = _row(seat_value, "ticket reservation detail seat_info")
            seats.append(
                ReservationSeatDetail(
                    **_nullable_scalar_fields(
                        seat,
                        _RESERVATION_SEAT_DETAIL_FIELDS,
                        "reservation seat detail",
                    ),
                    raw=seat,
                )
            )
        journeys.append(
            ReservationDetailJourney(
                **_nullable_scalar_fields(
                    journey,
                    _RESERVATION_DETAIL_JOURNEY_FIELDS,
                    "reservation detail journey",
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    return TicketReservationDetailResponse(
        **_nullable_scalar_fields(
            raw,
            _TICKET_RESERVATION_DETAIL_FIELDS,
            "ticket reservation detail",
        ),
        journeys=tuple(journeys),
        **_response_fields(raw),
    )


_REFUND_COMMISSION_FIELDS = {
    "refund_amount": "ret_amt",
    "refund_fee": "ret_fee",
    "proceed_possible_flag": "prg_psb_flg",
    "ticket_return_times_division_code": "tk_ret_tms_dv_cd",
    "usable_mileage": "use_psb_mlg_num",
    "secondary_message_code": "h_msg_cd2",
    "secondary_message_text": "h_msg_txt2",
}


def parse_refund_commission_response(
    raw: Mapping[str, Any],
) -> RefundCommissionResponse:
    _validate_strict_read_envelope(raw)
    return RefundCommissionResponse(
        **_nullable_scalar_fields(
            raw,
            _REFUND_COMMISSION_FIELDS,
            "refund commission",
        ),
        **_response_fields(raw),
    )


_REFUND_TICKET_SEAT_FIELDS = {
    "car_no": "h_srcar_no",
    "seat_no": "h_seat_no",
    "buyer_name": "h_buy_ps_nm",
    "checkin_status_code": "h_chckn_stt_cd",
    "discount_kind_code": "h_dcnt_knd_cd",
    "discount_kind_name": "h_dcnt_knd_nm",
    "passenger_type_code": "h_psg_tp_cd",
    "passenger_type_name": "h_psg_tp_nm",
    "seat_group_name": "h_sgr_nm",
}

_REFUND_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "departure_station_name": "h_dpt_rs_stn_nm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "arrival_station_name": "h_arv_rs_stn_nm",
    "train_no": "h_trn_no",
    "train_class_name": "h_trn_clsf_nm",
    "room_class_name": "h_psrm_cl_nm",
    "platform_no": "h_plf_no",
}

_REFUND_TICKET_DETAIL_FIELDS = {
    "pnr_no": "h_pnr_no",
    "sale_date": "h_sale_dt",
    "sale_time": "h_sale_tm",
    "window_name": "h_wct_nm",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "original_window_no": "h_orgtk_wct_no",
    "original_sale_sequence": "h_orgtk_sale_sqno",
    "original_return_password": "h_orgtk_ret_pwd",
    "ticket_kind_code": "h_tk_knd_cd",
    "ticket_kind_name": "h_tk_knd_nm",
    "refund_possible_flag": "retPsbFlg",
    "return_flag": "h_ret_flg",
    "total_fare_amount": "h_tot_fare_amt",
    "total_discount_amount": "h_tot_disc_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "train_running_flag": "h_trn_running_flg",
    "companion_name": "h_compa_nm",
    "companion_birth_date": "h_compa_brth",
    # Flags the app echoes straight back into the refund it then sends
    # (TicketDetailDao.java:227-281). h_pbp_acep_tgt_flg is the one
    # build_refund_form needs: ticketReturn/a.java:430-431 puts this exact value
    # in pbpAcepTgtFlg, so without parsing it there is no way for a caller to
    # send anything but a guess.
    "pbp_acceptance_target_flag": "h_pbp_acep_tgt_flg",
    "delay_flag": "h_dlay_flg",
    "delay_ticket_flag": "h_dlay_tk_flg",
    "mileage_save_flag": "mlgSaveFlg",
    "additional_service_flag": "addSrvFlg",
    "additional_service_cancel": "addSrvCancel",
}


_DISCOUNT_CARD_SECTION_FIELDS = {
    "section_sequence": "dcntCrdAplSegSqno",
    "departure_station_name": "dptRsStnNm",
    "arrival_station_name": "arvRsStnNm",
    "journey_sequence": "jrnySqno",
    "journey_type_code": "jrnyTpCd",
    "train_group_code": "trnGpCd",
    "detour_division_name": "stlbDturDvNm",
}


def _discount_card_on_ticket(
    raw: Mapping[str, Any],
) -> DiscountCardOnTicket | None:
    """승차권 상세에서 ``dcnt_crd_info`` 를 읽습니다. 없으면 ``None``.

    평범한 승차권에는 없으므로 부재가 오류가 아닙니다. 구간 목록의 전선 키는
    ``appSegList`` — Gson 이 직렬화하는 자바 **필드** 이름입니다
    (``TicketDetailDao.java:124``). 게터는 ``getAppSeg_info()`` 로 철자가 다르며
    그것은 전선 이름이 아닙니다.
    """
    info = _optional_mapping(raw, "dcnt_crd_info", "refund ticket detail")
    if info is None:
        return None
    sections = []
    for value in _optional_list(
        info,
        "appSegList",
        "refund ticket detail dcnt_crd_info",
    ):
        item = _row(value, "refund ticket detail appSegList")
        sections.append(
            DiscountCardSection(
                **_nullable_scalar_fields(
                    item,
                    _DISCOUNT_CARD_SECTION_FIELDS,
                    "discount card section",
                ),
                raw=item,
            )
        )
    return DiscountCardOnTicket(
        card_no=_optional_scalar_string(
            info,
            "h_dcnt_crd_no",
            "discount card info",
        ),
        term_extension_possible_flag=_optional_string(
            info,
            "h_dcnt_crd_trm_extn_psb_flg",
            "discount card info",
        ),
        sections=tuple(sections),
        raw=info,
    )


def parse_refund_ticket_detail_response(
    raw: Mapping[str, Any],
) -> RefundTicketDetailResponse:
    _validate_strict_read_envelope(raw)
    journeys = []
    for value in _nested_rows(
        raw,
        "ticket_infos",
        "ticket_info",
        "refund ticket detail",
    ):
        journey = _row(value, "refund ticket detail ticket_info")
        seats = []
        for seat_value in _optional_list(
            journey,
            "tk_seat_info",
            "refund ticket detail ticket_info",
        ):
            seat = _row(seat_value, "refund ticket detail tk_seat_info")
            seats.append(
                RefundTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _REFUND_TICKET_SEAT_FIELDS,
                        "refund ticket seat",
                    ),
                    raw=seat,
                )
            )
        journeys.append(
            RefundTicketJourney(
                **_nullable_scalar_fields(
                    journey,
                    _REFUND_TICKET_JOURNEY_FIELDS,
                    "refund ticket journey",
                ),
                seats=tuple(seats),
                raw=journey,
            )
        )
    return RefundTicketDetailResponse(
        **_nullable_scalar_fields(
            raw,
            _REFUND_TICKET_DETAIL_FIELDS,
            "refund ticket detail",
        ),
        journeys=tuple(journeys),
        discount_card=_discount_card_on_ticket(raw),
        **_response_fields(raw),
    )


_SELF_SEAT_CHANGE_STATION_FIELDS = {
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "departure_construction_order": "dptStnConsOrdr",
    "departure_run_order": "dptStnRunOrdr",
    "general_remaining_seats": "gnrmRestSeatNum",
    "special_remaining_seats": "sprmRestSeatNum",
}
_SELF_SEAT_CHANGE_REASON_FIELDS = {
    "query_code": "qryCode",
    "query_order": "qryOrdr",
    "reason_text": "frcSaleRsnCont",
}
_SELF_SEAT_CHANGE_INFO_FIELDS = {
    "train_no": "trnNo",
    "train_class_code": "trnClsfCd",
    "train_class_name": "trnClsfNm",
    "train_group_code": "trnGpCd",
    "train_group_name": "trnGpNm",
    "run_date": "runDt",
    "general_reservation_possible_code": "gnrmRsvPsbCd",
    "special_reservation_possible_code": "sprmRsvPsbCd",
    "change_before_departure_construction_order": "chgBfDptStnConsOrdr",
    "change_before_arrival_construction_order": "chgBfArvStnConsOrdr",
    "existing_departure_run_order": "exsDptStnRunOrdr",
    "existing_arrival_run_order": "exsArvStnRunOrdr",
}


def parse_self_seat_change_info_response(
    raw: Mapping[str, Any],
) -> SelfSeatChangeInfoResponse:
    """``self.seatChgInfo.do`` 를 파싱합니다.

    ``CallSelfSeatChgInfoDao.CallSelfSeatChgInfoResponse`` 와 그 안의 두 행 타입
    (``dao/ticket/change/CallSelfSeatChgInfoDao.java:64-204``). DAO 가 선언한
    필드가 전부 자바 ``String`` 이라 모두 :func:`_optional_scalar_string` 으로
    읽습니다 — 잔여좌석 수와 편성/운행 순서가 맨 JSON 숫자로 오는 것이 관측된
    바로 그런 필드입니다.
    """
    if not isinstance(raw, Mapping):
        raise KorailProtocolError(
            "KORAIL self seat change info response must be a mapping"
        )
    _validate_strict_read_envelope(raw)
    stations = tuple(
        SelfSeatChangeStation(
            **_nullable_scalar_fields(
                station,
                _SELF_SEAT_CHANGE_STATION_FIELDS,
                "self seat change station",
            ),
            raw=station,
        )
        for station in (
            _row(value, "self seat change chgStnList")
            for value in _optional_list(
                raw,
                "chgStnList",
                "self seat change info",
            )
        )
    )
    reasons = tuple(
        SelfSeatChangeReason(
            **_nullable_scalar_fields(
                reason,
                _SELF_SEAT_CHANGE_REASON_FIELDS,
                "self seat change reason",
            ),
            raw=reason,
        )
        for reason in (
            _row(value, "self seat change chgRsnList")
            for value in _optional_list(
                raw,
                "chgRsnList",
                "self seat change info",
            )
        )
    )
    return SelfSeatChangeInfoResponse(
        **_nullable_scalar_fields(
            raw,
            _SELF_SEAT_CHANGE_INFO_FIELDS,
            "self seat change info",
        ),
        stations=stations,
        reasons=reasons,
        **_response_fields(raw),
    )


_ORIGINAL_TICKET_SEAT_FIELDS = {
    "passenger_sequence": "psgSqno",
    "assign_sequence": "asgnSqno",
    "passenger_type_code": "psgTpDvCd",
    "room_class_code": "psrmClCd",
    "car_no": "scarNo",
    "seat_no": "seatNo",
    "seat_count": "seatNum",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "requested_seat_attribute_code": "rqSeatAttCd",
    "direction_seat_attribute_code": "dirSeatAttCd",
    "location_seat_attribute_code": "locSeatAttCd",
    "smoking_seat_attribute_code": "smkSeatAttCd",
    "additional_seat_attribute_code": "addSeatAttCd",
    "etc_seat_attribute_code": "etcSeatAttCd",
}
_ORIGINAL_TICKET_JOURNEY_FIELDS = {
    "journey_sequence": "jrnySqno",
    "journey_order": "jrnyOrdr",
    "journey_type_code": "jrnyTpCd",
    "train_no": "trnNo",
    "train_group_code": "trnGpCd",
    "departure_date": "dptDt",
    "departure_time": "dptTm",
    "departure_station_code": "dptRsStnCd",
    "departure_station_name": "dptRsStnNm",
    "departure_construction_order": "dptStnConsOrdr",
    "arrival_date": "arvDt",
    "arrival_time": "arvTm",
    "arrival_station_code": "arvRsStnCd",
    "arrival_station_name": "arvRsStnNm",
    "arrival_construction_order": "arvStnConsOrdr",
    "goods_no": "gdNo",
    "total_seat_count": "totSeatNum",
    "total_standing_count": "totStndNum",
    "general_change_allowed_flag": "genChgAllwFlg",
    "single_ticket_flag": "snglTkFlg",
}
_ORIGINAL_TICKET_FIELDS = {
    "pnr_no": "pnrNo",
    "ticket_kind_code": "tkKndCd",
    "original_sale_datetime": "ogtkSaleDt",
    "original_window_no": "ogtkSaleWctNo",
    "original_sale_sequence": "ogtkSaleSqno",
    "original_return_password": "ogtkRetPwd",
    "member_card_no": "mbCrdNo",
    "adult_count": "adulCnt",
    "child_count": "chilCnt",
    "group_discount_count": "grpDcntCnt",
    "passenger_type_division_code": "psgTpDvCd",
    "received_amount": "rcvdAmt",
    "received_fare": "rcvdFare",
    "received_price": "rcvdPrc",
    "change_sale_transaction_no": "chgSaleTno",
    "sms_send_flag": "smsSndFlg",
    "forced_sale_reason_text": "frcSaleRsnCont",
}


def parse_original_ticket_inquiry_response(
    raw: Mapping[str, Any],
) -> OriginalTicketInquiryResponse:
    """``research.tripChgOgtk.do`` 를 파싱합니다.

    ``OgTkInquiryDao.OgTkInquiryResponse`` → ``response/research/OrgTk.java`` 의
    ``orgTkList``. 각 원표는 ``Jrny.java`` 의 ``jrnyList`` 를, 각 여정은
    ``Seat.java`` 의 ``seatList`` 를 가집니다.

    ``cmpnList`` 와 ``stlList`` 는 일부러 파싱하지 않습니다. 지연증명 반환번호
    (``Cmpn.java:11-14``)와 카드/승인번호(``Stl.java:5-16``) 같은 소지 자격증명을
    더 싣는데 변경 과정의 어느 단계도 그것을 필요로 하지 않습니다. 두 목록의 전선
    키는 :mod:`~korail_mobile_api.redaction` 에 등록돼 있어
    :attr:`~korail_mobile_api.read_models.OriginalTicket.raw` 안에서도 가려진
    채로 남습니다.
    """
    if not isinstance(raw, Mapping):
        raise KorailProtocolError(
            "KORAIL original ticket inquiry response must be a mapping"
        )
    _validate_strict_read_envelope(raw)
    tickets = []
    for value in _optional_list(raw, "orgTkList", "original ticket inquiry"):
        ticket = _row(value, "original ticket inquiry orgTkList")
        journeys = []
        for journey_value in _optional_list(
            ticket,
            "jrnyList",
            "original ticket",
        ):
            journey = _row(journey_value, "original ticket jrnyList")
            seats = tuple(
                OriginalTicketSeat(
                    **_nullable_scalar_fields(
                        seat,
                        _ORIGINAL_TICKET_SEAT_FIELDS,
                        "original ticket seat",
                    ),
                    raw=seat,
                )
                for seat in (
                    _row(seat_value, "original ticket seatList")
                    for seat_value in _optional_list(
                        journey,
                        "seatList",
                        "original ticket journey",
                    )
                )
            )
            journeys.append(
                OriginalTicketJourney(
                    **_nullable_scalar_fields(
                        journey,
                        _ORIGINAL_TICKET_JOURNEY_FIELDS,
                        "original ticket journey",
                    ),
                    seats=seats,
                    raw=journey,
                )
            )
        tickets.append(
            OriginalTicket(
                **_nullable_scalar_fields(
                    ticket,
                    _ORIGINAL_TICKET_FIELDS,
                    "original ticket",
                ),
                journeys=tuple(journeys),
                raw=ticket,
            )
        )
    return OriginalTicketInquiryResponse(
        tickets=tuple(tickets),
        **_response_fields(raw),
    )
