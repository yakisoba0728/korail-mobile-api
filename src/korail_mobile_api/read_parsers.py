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
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    PassAvailabilityResponse,
    PassOffice,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ReceiptPayment,
    ReservationHistoryResponse,
    ReservationHistoryTrain,
    ServiceStatusResponse,
    TicketReceipt,
    TicketReceiptResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)


def _validate_envelope(
    raw: Mapping[str, Any],
    *,
    accepted_empty_codes: frozenset[str] = frozenset(),
) -> bool:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    required = ("h_msg_cd", "h_msg_txt", "strResult")
    missing = [name for name in required if name not in raw]
    if missing:
        raise KorailProtocolError(
            "KORAIL response missing required envelope fields: "
            + ", ".join(missing)
        )
    invalid = [
        name
        for name in required
        if raw[name] is not None and not isinstance(raw[name], str)
    ]
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


def parse_service_status_response(
    raw: Mapping[str, Any],
) -> ServiceStatusResponse:
    _validate_envelope(raw)
    return ServiceStatusResponse(**_response_fields(raw))


def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw)
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
    _validate_envelope(raw)
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
    _validate_envelope(raw)
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
