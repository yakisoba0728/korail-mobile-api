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
    CommuterKindMenuResponse,
    CustomerTripInfo,
    CustomerTripInfoResponse,
    CommuterInfoResponse,
    CommuterPassengerOption,
    CrewRequestListResponse,
    CrewRequestOption,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DeliveryRecipientResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GiftTicket,
    GiftTicketListResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    MaasServiceDetail,
    MaasServiceDetailListResponse,
    MergeSeatsInquiryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    PassScheduleInfo,
    PassScheduleResponse,
    PassScheduleTrain,
    PassAvailabilityResponse,
    PassAgeOption,
    PassGoodsInfo,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassPassengerInfo,
    PassPassengerInfos,
    PassPeriodOption,
    PbpAcceptanceJourney,
    PbpAcceptanceSeat,
    PbpAcceptanceSpecificationResponse,
    PbpAcceptanceTicket,
    PlatformNumberJourney,
    PlatformNumberResponse,
    PlatformNumberTicket,
    ProductDetailResponse,
    ProductRecommendation,
    ProductReservation,
    ProductReservationListResponse,
    ProductTrain,
    ProductTrainInquiryResponse,
    PriceFare,
    PriceFareQuoteResponse,
    RecentDeliveryHistoryResponse,
    RecentDeliveryRecipient,
    ReceiptPayment,
    RefundCommissionResponse,
    RefundTicketDetailResponse,
    RefundTicketJourney,
    RefundTicketSeat,
    ReservationDetailJourney,
    ReservationHistoryResponse,
    ReservationHistoryTrain,
    ReservationSeatDetail,
    SeatAssignmentScheduleResponse,
    ServiceStatusResponse,
    TicketReceipt,
    TicketReceiptResponse,
    TicketReservationDetailResponse,
    TicketDuplicationCheckResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
    TourTrainInfoResponse,
    TourTrainSeatAdditionalInfo,
    TourTrainSeatInfo,
    TrainScheduleItem,
    TripChangeDateResponse,
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


def _optional_scalar_string(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> str | None:
    """A scalar field, accepted as a JSON string OR a JSON number.

    KORAIL is not consistent about which of the two it sends for a field the
    APK declares as a Java ``String``, and the app never notices: every one of
    these DAOs is deserialized by Gson, whose ``JsonReader.nextString()``
    coerces a JSON number into its string form. Three separate live findings
    have now landed on the same seam -- ``h_jrny_cnt`` arrived zero-padded as
    ``"0001"``, ``h_st_prnb``/``h_cls_prnb`` arrived as zero-padded strings
    where an ``int`` was demanded, and ``h_srcar_no`` arrived as a JSON number
    where a string was demanded, which is what killed a live reserve on
    2026-07-25 -- so this is treated as the systemic issue it is rather than as
    three one-offs.

    Accepting both is not the same as accepting anything. A ``bool``, a
    ``float``, a list or an object where a scalar belongs is still a protocol
    error: those are not shapes Gson would have taken for a String either, and
    silently stringifying one would hide a genuinely different response.
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


def _required_json_integer(
    data: Mapping[str, Any],
    key: str,
    context: str,
) -> int:
    value = data.get(key)
    if type(value) is not int:
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a JSON integer"
        )
    return value


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


def _parse_pass_menu_data(
    data: Mapping[str, Any] | None,
    context: str,
) -> PassMenuData | None:
    if data is None:
        return None
    age_options = []
    for value in _optional_list(data, "pass_ageinfo", context):
        item = _row(value, f"{context} pass_ageinfo")
        age_options.append(
            PassAgeOption(
                commuter_age_code=_optional_string(
                    item,
                    "h_cmtr_utl_age_cd",
                    "pass age option",
                ),
                display_name=_optional_string(
                    item,
                    "h_comn_cd_nm",
                    "pass age option",
                ),
                minimum_age=_optional_string(
                    item,
                    "h_min_age",
                    "pass age option",
                ),
                maximum_age=_optional_string(
                    item,
                    "h_max_age",
                    "pass age option",
                ),
                raw=item,
            )
        )
    period_options = []
    for value in _optional_list(data, "pass_periodinfo", context):
        item = _row(value, f"{context} pass_periodinfo")
        period_options.append(
            PassPeriodOption(
                commuter_period_code=_optional_string(
                    item,
                    "h_cmtr_utl_trm_cd",
                    "pass period option",
                ),
                display_name=_optional_string(
                    item,
                    "h_comn_cd_nm",
                    "pass period option",
                ),
                raw=item,
            )
        )
    return PassMenuData(
        commuter_kind_code=_optional_string(
            data,
            "h_cmtr_knd_cd",
            context,
        ),
        station_selection=_optional_string(
            data,
            "h_select_station",
            context,
        ),
        age_options=tuple(age_options),
        period_options=tuple(period_options),
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
    # A live pass.passMenu.do success is result-only: the body is
    # {"list": [...], "strResult": "SUCC"} with no h_msg_cd/h_msg_txt at all.
    # Only the failure body carries the full envelope (P058 when unauthenticated),
    # so requiring h_msg_cd made every SUCCESS unparseable while every FAILURE
    # parsed. Accept the result-only shape the way the cart/delay-discount reads
    # already do.
    _validate_strict_read_envelope(raw, allow_result_only_success=True)
    items = []
    for value in _optional_list(raw, "list", "pass menu"):
        item = _row(value, "pass menu list")
        web_data = _optional_mapping(item, "webData", "pass menu item")
        items.append(
            PassMenuItem(
                after_day=_optional_integer(
                    item,
                    "afterDay",
                    "pass menu item",
                ),
                agreement=_optional_string(
                    item,
                    "agree",
                    "pass menu item",
                ),
                detail_type=_optional_string(
                    item,
                    "detailType",
                    "pass menu item",
                ),
                detail_description=_optional_string(
                    item,
                    "dtlDsc",
                    "pass menu item",
                ),
                enabled=_optional_string(
                    item,
                    "enable",
                    "pass menu item",
                ),
                item_id=_optional_string(
                    item,
                    "id",
                    "pass menu item",
                ),
                information=_optional_string(
                    item,
                    "information",
                    "pass menu item",
                ),
                expanded=_optional_string(
                    item,
                    "isExpand",
                    "pass menu item",
                ),
                parent_id=_optional_string(
                    item,
                    "parentId",
                    "pass menu item",
                ),
                representative_arrival=_optional_string(
                    item,
                    "repSegArv",
                    "pass menu item",
                ),
                representative_departure=_optional_string(
                    item,
                    "repSegDpt",
                    "pass menu item",
                ),
                title=_optional_string(
                    item,
                    "title",
                    "pass menu item",
                ),
                train_group_code=_optional_string(
                    item,
                    "trnGpCd",
                    "pass menu item",
                ),
                item_type=_optional_string(
                    item,
                    "type",
                    "pass menu item",
                ),
                goods_data=_parse_pass_goods_info(
                    _optional_mapping(
                        item,
                        "goodsData",
                        "pass menu item",
                    ),
                    "pass goods info",
                ),
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(
                        item,
                        "passData",
                        "pass menu item",
                    ),
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
        after_day=_optional_string(raw, "afterDay", "commuter kind menu"),
        agreement=_optional_string(raw, "agree", "commuter kind menu"),
        information=_optional_string(
            raw,
            "information",
            "commuter kind menu",
        ),
        title=_optional_string(raw, "title", "commuter kind menu"),
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
    items = []
    for value in _optional_list(raw, "prsList", "crew request list"):
        item = _row(value, "crew request list prsList")
        items.append(
            CrewRequestOption(
                message_code=_optional_string(
                    item,
                    "intgMsgCd",
                    "crew request option",
                ),
                content=_optional_string(
                    item,
                    "prsCont",
                    "crew request option",
                ),
                raw=item,
            )
        )
    return CrewRequestListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


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
                service_code=_optional_string(
                    item, "addSrvDvCd", "cart item"
                ),
                provider_name=_optional_string(
                    item, "h_add_srv_mrk_ent_nm", "cart item"
                ),
                product_name=_optional_string(item, "h_gd_nm", "cart item"),
                item_type=_optional_string(
                    item, "h_item_dv_nm", "cart item"
                ),
                departure_date=_optional_string(
                    item, "h_dpt_dt", "cart item"
                ),
                received_amount=_optional_string(
                    item, "h_rcvd_amt", "cart item"
                ),
                reservation_received_date=_optional_string(
                    item, "h_rsv_rcp_dt", "cart item"
                ),
                ticket_count=_optional_integer(
                    item, "h_tk_cnt", "cart item"
                ),
                usage_start_date=_optional_string(
                    item, "utlStDt", "cart item"
                ),
                usage_start_time=_optional_string(
                    item, "utlStTm", "cart item"
                ),
                usage_close_time=_optional_string(
                    item, "utlClsTm", "cart item"
                ),
                partner_reservation_no=_optional_string(
                    item, "coptEntRsvNo", "cart item"
                ),
                pnr_no=_optional_string(item, "h_pnr_no", "cart item"),
                lump_sum_target_no=_optional_string(
                    item, "h_lump_stl_tgt_no", "cart item"
                ),
                customer_no=_optional_string(
                    item, "h_cust_no", "cart item"
                ),
                virtual_reservation_no=_optional_string(
                    item, "h_vr_rsv_no", "cart item"
                ),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


def parse_deposit_bank_response(
    raw: Mapping[str, Any],
) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = []
    for value in _optional_list(raw, "dptnBank", "deposit bank list"):
        item = _row(value, "deposit bank list dptnBank")
        items.append(
            DepositBank(
                code=_optional_string(item, "dptnBankCd", "deposit bank"),
                display_name=_optional_string(
                    item, "dptnBankNm", "deposit bank"
                ),
                raw=item,
            )
        )
    return DepositBankListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


def parse_delay_discount_ticket_response(
    raw: Mapping[str, Any],
) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    rows = _nested_rows(
        raw,
        "disc_infos",
        "disc_info",
        "delay discount ticket list",
    )
    for value in rows:
        item = _row(value, "delay discount ticket list disc_info")
        items.append(
            DelayDiscountTicket(
                fare=_optional_string(
                    item, "h_dlay_fare", "delay discount ticket"
                ),
                usable_until_date=_optional_string(
                    item, "h_use_psb_dt", "delay discount ticket"
                ),
                original_sale_date=_optional_string(
                    item, "h_orgtk_ret_sale_dt", "delay discount ticket"
                ),
                window_no=_optional_string(
                    item, "h_orgtk_wct_no", "delay discount ticket"
                ),
                sale_sequence=_optional_string(
                    item, "h_orgtk_sale_sqno", "delay discount ticket"
                ),
                return_password=_optional_string(
                    item, "h_orgtk_ret_pwd", "delay discount ticket"
                ),
                raw=item,
            )
        )
    return DelayDiscountTicketListResponse(
        items=tuple(items),
        **_response_fields(raw),
    )


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
        discount_values = tuple(
            result
            for key in (
                "h_disc_rt_amt_dv_cd",
                "h_inwk_fare_disc_rt_amt",
                "h_inwk_prc_disc_rt_amt",
                "h_wknd_fare_disc_rt_amt",
                "h_wknd_prc_disc_rt_amt",
            )
            if (result := _optional_string(item, key, "discount coupon"))
            is not None
        )
        remarks = tuple(
            result
            for key in ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont")
            if (result := _optional_string(item, key, "discount coupon"))
            is not None
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
        contents = []
        for content_value in _optional_list(item, "contList", "trip menu"):
            content = _row(content_value, "trip menu contList")
            contents.append(
                TripMenuContent(
                    title=_optional_string(
                        content, "contTitle", "trip menu content"
                    ),
                    detail=_optional_string(
                        content, "contDetail", "trip menu content"
                    ),
                    content_type=_optional_string(
                        content, "detailType", "trip menu content"
                    ),
                    active=_optional_string(
                        content, "passActive", "trip menu content"
                    ),
                    agree=_optional_string(
                        content, "passAgree", "trip menu content"
                    ),
                    info=_optional_string(
                        content, "passInfo", "trip menu content"
                    ),
                    image=_optional_string(
                        content, "contImage", "trip menu content"
                    ),
                    url=_optional_string(
                        content, "contUrl", "trip menu content"
                    ),
                    raw=content,
                )
            )
        items.append(
            TripMenuItem(
                title=_optional_string(item, "menuTitle", "trip menu item"),
                detail=_optional_string(
                    item, "menuDetail", "trip menu item"
                ),
                menu_type=_optional_string(
                    item, "menuType", "trip menu item"
                ),
                button=_optional_string(item, "menuBtn", "trip menu item"),
                contents=tuple(contents),
                url=_optional_string(item, "menuUrl", "trip menu item"),
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
    items = []
    for value in _optional_list(main, "entity", "product reservation list"):
        item = _row(value, "product reservation list entity")
        items.append(
            ProductReservation(
                product_name=_optional_string(
                    item, "strGdNm", "product reservation"
                ),
                reservation_status=_optional_string(
                    item, "strRsvSttNm", "product reservation"
                ),
                payment_deadline=_optional_string(
                    item, "strStlDlnDt", "product reservation"
                ),
                payment_status=_optional_string(
                    item, "strStlSttCd", "product reservation"
                ),
                virtual_reservation_no=_optional_string(
                    item, "strVrRsvNo", "product reservation"
                ),
                raw=item,
            )
        )
    return ProductReservationListResponse(
        items=tuple(items),
        total_count=_optional_integer(
            main,
            "strTotCnt",
            "product reservation list",
        ),
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
        product_name=_optional_string(main, "strGdNm", "product detail"),
        reservation_status=_optional_string(
            main, "strRsvSttNm", "product detail"
        ),
        cancellation_deadline=_optional_string(
            main, "strCncDlnDt", "product detail"
        ),
        cancellation_amount=_optional_string(
            main, "strCncRetAmt", "product detail"
        ),
        cancellation_fee=_optional_string(
            main, "strCncRetFee", "product detail"
        ),
        received_amount=_optional_string(
            main, "strRcvdAmt", "product detail"
        ),
        total_amount=_optional_string(
            main, "strTotStlAmt", "product detail"
        ),
        usage_period=_optional_string(
            main, "strUtlTrmCont", "product detail"
        ),
        included_item_names=tuple(included_items),
        virtual_reservation_no=_optional_string(
            main, "strVrRsvNo", "product detail"
        ),
        detail_raw=main,
        **_response_fields(raw),
    )


def parse_ticket_receipt_response(
    raw: Mapping[str, Any],
) -> TicketReceiptResponse:
    _validate_envelope(raw)
    items = []
    rows = _nested_rows(
        raw,
        "receipt_infos",
        "receipt_info",
        "ticket receipt",
    )
    for value in rows:
        item = _row(value, "ticket receipt receipt_info")
        payments = []
        for payment_value in _optional_list(
            item, "stl_info", "ticket receipt"
        ):
            payment = _row(payment_value, "ticket receipt stl_info")
            payments.append(
                ReceiptPayment(
                    payment_method=_optional_string(
                        payment, "h_stl_way_nm", "receipt payment"
                    ),
                    approval_date=_optional_string(
                        payment, "h_apv_dt", "receipt payment"
                    ),
                    installment_months=_optional_integer(
                        payment, "h_ismt_mnth_num", "receipt payment"
                    ),
                    amount=_optional_integer(
                        payment, "h_stl_amt", "receipt payment"
                    ),
                    account_no=_optional_string(
                        payment, "h_acnt_no", "receipt payment"
                    ),
                    approval_no=_optional_string(
                        payment, "h_apv_no", "receipt payment"
                    ),
                    card_no=_optional_string(
                        payment, "h_stl_crd_no", "receipt payment"
                    ),
                    point_no=_optional_string(
                        payment, "h_xpot_no", "receipt payment"
                    ),
                    raw=payment,
                )
            )
        items.append(
            TicketReceipt(
                travel_date=_optional_string(
                    item, "h_abrd_dt", "ticket receipt"
                ),
                departure_station=_optional_string(
                    item, "h_dpt_rs_stn_nm", "ticket receipt"
                ),
                departure_time=_optional_string(
                    item, "h_dpt_tm", "ticket receipt"
                ),
                arrival_station=_optional_string(
                    item, "h_arv_rs_stn_nm", "ticket receipt"
                ),
                arrival_time=_optional_string(
                    item, "h_arv_tm", "ticket receipt"
                ),
                commuter_kind_code=_optional_string(
                    item, "h_cmtr_knd_cd", "ticket receipt"
                ),
                journey_type_code=_optional_string(
                    item, "h_jrny_tp_cd", "ticket receipt"
                ),
                printed_discount_name=_optional_string(
                    item, "h_prt_disc_knd_nm", "ticket receipt"
                ),
                print_type=_optional_string(
                    item, "h_prt_type", "ticket receipt"
                ),
                seat_class_name=_optional_string(
                    item, "h_psrm_cl_nm", "ticket receipt"
                ),
                ticket_kind_code=_optional_string(
                    item, "h_tk_knd_cd", "ticket receipt"
                ),
                ticket_status_code=_optional_string(
                    item, "h_tk_stt_cd", "ticket receipt"
                ),
                train_class_code=_optional_string(
                    item, "h_trn_clsf_cd", "ticket receipt"
                ),
                train_class_name=_optional_string(
                    item, "h_trn_clsf_nm", "ticket receipt"
                ),
                train_no=_optional_string(
                    item, "h_trn_no", "ticket receipt"
                ),
                passenger_counts=(
                    _optional_integer(
                        item, "h_psg_type1_cnt", "ticket receipt"
                    ),
                    _optional_integer(
                        item, "h_psg_type2_cnt", "ticket receipt"
                    ),
                    _optional_integer(
                        item, "h_psg_type3_cnt", "ticket receipt"
                    ),
                ),
                received_amount=_optional_integer(
                    item, "h_rcvd_amt", "ticket receipt"
                ),
                card_refund_amount=_optional_integer(
                    item, "h_crd_ret_amt", "ticket receipt"
                ),
                refund_fee=_optional_integer(
                    item, "h_ret_fee", "ticket receipt"
                ),
                refund_received_amount=_optional_integer(
                    item, "h_ret_rcvd_amt", "ticket receipt"
                ),
                point_refund_amount=_optional_integer(
                    item, "h_xpoint_ret_amt", "ticket receipt"
                ),
                payments=tuple(payments),
                member_card_no=_optional_string(
                    item, "h_stl_mb_crd_no", "ticket receipt"
                ),
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
    journeys = _nested_rows(
        raw,
        "jrny_infos",
        "jrny_info",
        "reservation history",
    )
    for journey_value in journeys:
        journey = _row(journey_value, "reservation history jrny_info")
        train_wrapper = _optional_mapping(
            journey,
            "train_infos",
            "reservation history",
        )
        if train_wrapper is None:
            continue
        for train_value in _optional_list(
            train_wrapper,
            "train_info",
            "reservation history",
        ):
            train = _row(train_value, "reservation history train_info")
            trains.append(
                ReservationHistoryTrain(
                    departure_station=_optional_string(
                        train, "h_dpt_rs_stn_nm", "reservation history train"
                    ),
                    departure_time=_optional_string(
                        train, "h_dpt_tm", "reservation history train"
                    ),
                    arrival_station=_optional_string(
                        train, "h_arv_rs_stn_nm", "reservation history train"
                    ),
                    arrival_time=_optional_string(
                        train, "h_arv_tm", "reservation history train"
                    ),
                    run_date=_optional_string(
                        train, "h_run_dt", "reservation history train"
                    ),
                    train_no=_optional_string(
                        train, "h_trn_no", "reservation history train"
                    ),
                    train_class_code=_optional_string(
                        train, "h_trn_clsf_cd", "reservation history train"
                    ),
                    train_class_name=_optional_string(
                        train, "h_trn_clsf_nm", "reservation history train"
                    ),
                    reservation_type_code=_optional_string(
                        train, "h_rsv_tp_cd", "reservation history train"
                    ),
                    acceptance_possible_flag=_optional_string(
                        train, "h_acpt_ps_flg", "reservation history train"
                    ),
                    payment_flag=_optional_string(
                        train, "h_payment_flg", "reservation history train"
                    ),
                    settlement_flag=_optional_string(
                        train, "h_stl_flg", "reservation history train"
                    ),
                    seat_count=_optional_integer(
                        train, "h_tot_seat_cnt", "reservation history train"
                    ),
                    standing_count=_optional_integer(
                        train, "h_tot_stnd_cnt", "reservation history train"
                    ),
                    pnr_no=_optional_string(
                        train, "h_pnr_no", "reservation history train"
                    ),
                    raw=train,
                )
            )
    return ReservationHistoryResponse(
        items=tuple(trains),
        **_response_fields(raw),
    )


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
    context = "train schedule item"
    return TrainScheduleItem(
        train_no=_optional_string(raw, "h_trn_no", context),
        train_group_code=_optional_string(raw, "h_trn_gp_cd", context),
        train_class_code=_optional_string(
            raw,
            "h_trn_clsf_cd",
            context,
        ),
        train_class_name=_optional_string(
            raw,
            "h_trn_clsf_nm",
            context,
        ),
        run_date=_optional_string(raw, "h_run_dt", context),
        departure_date=_optional_string(raw, "h_dpt_dt", context),
        departure_time=_optional_string(raw, "h_dpt_tm", context),
        arrival_date=_optional_string(raw, "h_arv_dt", context),
        arrival_time=_optional_string(raw, "h_arv_tm", context),
        departure_station_code=_optional_string(
            raw,
            "h_dpt_rs_stn_cd",
            context,
        ),
        departure_station_name=_optional_string(
            raw,
            "h_dpt_rs_stn_nm",
            context,
        ),
        arrival_station_code=_optional_string(
            raw,
            "h_arv_rs_stn_cd",
            context,
        ),
        arrival_station_name=_optional_string(
            raw,
            "h_arv_rs_stn_nm",
            context,
        ),
        departure_construction_order=_optional_string(
            raw,
            "h_dpt_stn_cons_ordr",
            context,
        ),
        arrival_construction_order=_optional_string(
            raw,
            "h_arv_stn_cons_ordr",
            context,
        ),
        departure_run_order=_optional_string(
            raw,
            "h_dpt_stn_run_ordr",
            context,
        ),
        arrival_run_order=_optional_string(
            raw,
            "h_arv_stn_run_ordr",
            context,
        ),
        car_type_name=_optional_string(raw, "h_car_tp_nm", context),
        general_room_name=_optional_string(
            raw,
            "h_gen_psrm_cl_nm",
            context,
        ),
        special_room_name=_optional_string(
            raw,
            "h_spe_psrm_cl_nm",
            context,
        ),
        general_reservation_code=_optional_string(
            raw,
            "h_gen_rsv_cd",
            context,
        ),
        special_reservation_code=_optional_string(
            raw,
            "h_spe_rsv_cd",
            context,
        ),
        free_seat_reservation_code=_optional_string(
            raw,
            "h_free_rsv_cd",
            context,
        ),
        standing_reservation_code=_optional_string(
            raw,
            "h_stnd_rsv_cd",
            context,
        ),
        seat_map_flag=_optional_string(
            raw,
            "h_rd_seat_map_flg",
            context,
        ),
        delay_sale_flag=_optional_string(
            raw,
            "h_dlay_sale_flg",
            context,
        ),
        wait_reservation_flag=_optional_string(
            raw,
            "h_wait_rsv_flg",
            context,
        ),
        reservation_possible_name=_optional_string(
            raw,
            "h_rsv_psb_nm",
            context,
        ),
        special_reservation_possible_name=_optional_string(
            raw,
            "h_spe_rsv_psb_nm",
            context,
        ),
        info_text=_optional_string(raw, "h_info_txt", context),
        popup_message=_optional_string(raw, "h_popup_msg", context),
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
    # CommutationInquiryActivity.java:182 registers WRG000000 as a non-fatal
    # empty result for the pass-schedule DAO (CommRsvInquiryDao) via
    # setErrorMsgCdNotShowDialog, so an empty query returns strResult=FAIL +
    # h_msg_cd=WRG000000 and the app renders "no schedules" rather than an
    # error. Mirror parse_discount_coupon_response and treat it as empty.
    empty = _validate_envelope(
        raw,
        accepted_empty_codes=frozenset({"WRG000000"}),
    )
    if empty:
        return PassScheduleResponse(**_response_fields(raw))
    if raw["strResult"] != "SUCC":
        raise KorailProtocolError(
            "KORAIL pass schedule strResult must be exact SUCC"
        )

    schedules = []
    for schedule_value in _optional_list(
        raw,
        "schedule_info",
        "pass schedule",
    ):
        schedule = _row(schedule_value, "pass schedule schedule_info")
        trains = []
        for train_value in _optional_list(
            schedule,
            "train_list",
            "pass schedule schedule_info",
        ):
            train = _row(train_value, "pass schedule train_list")
            trains.append(
                PassScheduleTrain(
                    arrival_station_code=_optional_string(
                        train,
                        "h_arv_rs_stn_cd",
                        "pass schedule train",
                    ),
                    arrival_station_name=_optional_string(
                        train,
                        "h_arv_rs_stn_nm",
                        "pass schedule train",
                    ),
                    departure_station_code=_optional_string(
                        train,
                        "h_dpt_rs_stn_cd",
                        "pass schedule train",
                    ),
                    departure_station_name=_optional_string(
                        train,
                        "h_dpt_rs_stn_nm",
                        "pass schedule train",
                    ),
                    detour_code=_optional_string(
                        train,
                        "h_dtour",
                        "pass schedule train",
                    ),
                    schedule_price=_optional_string(
                        train,
                        "h_schd_prc",
                        "pass schedule train",
                    ),
                    train_group_code=_optional_string(
                        train,
                        "h_trn_gp_cd",
                        "pass schedule train",
                    ),
                    train_no=_optional_string(
                        train,
                        "h_trn_no",
                        "pass schedule train",
                    ),
                    raw=train,
                )
            )
        schedules.append(
            PassScheduleInfo(
                trains=tuple(trains),
                raw=schedule,
            )
        )
    return PassScheduleResponse(
        schedules=tuple(schedules),
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
    """:func:`_nullable_string_fields`, but string-or-number per field.

    Used by the reservation-detail and refund-ticket-detail parsers, whose
    success shapes were built from the APK's DAO declarations and never seen
    live until 2026-07-25. See :func:`_optional_scalar_string`.
    """
    return {
        attribute: _optional_scalar_string(data, wire_name, context)
        for attribute, wire_name in field_map.items()
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
}


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
        **_response_fields(raw),
    )
