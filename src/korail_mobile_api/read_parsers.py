from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import (
    KorailAppError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from .read_models import (
    CartItem,
    CartListResponse,
    CommuterKindMenuResponse,
    CrewRequestListResponse,
    CrewRequestOption,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    FreeSeatCarResponse,
    GuideSeatConditionResponse,
    IntermediateStation,
    MergeSeatsInquiryResponse,
    PassAvailabilityResponse,
    PassAgeOption,
    PassMenuData,
    PassMenuItem,
    PassMenuResponse,
    PassOffice,
    PassPeriodOption,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ReceiptPayment,
    ReservationHistoryResponse,
    ReservationHistoryTrain,
    SeatAssignmentScheduleResponse,
    ServiceStatusResponse,
    TicketReceipt,
    TicketReceiptResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
    TrainScheduleItem,
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
        raise KorailAppError(code, message, raw=raw)
    return failed


def _response_fields(raw: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "h_msg_cd": raw.get("h_msg_cd"),
        "h_msg_txt": raw.get("h_msg_txt"),
        "str_result": raw.get("strResult"),
        "raw": raw,
    }


def _validate_strict_read_envelope(raw: Mapping[str, Any]) -> None:
    _validate_envelope(raw)
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


def parse_pass_menu_response(raw: Mapping[str, Any]) -> PassMenuResponse:
    _validate_envelope(raw)
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
    _validate_envelope(raw)
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
    _validate_envelope(raw)
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
    _validate_envelope(raw)
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
