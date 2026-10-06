# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""계정·마일리지·장바구니·상품 조회 응답을 읽습니다."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._parsing import (
    _nested_rows,
    _nullable_scalar_fields,
    _optional_integer,
    _optional_mapping,
    _optional_scalar_string,
    _present_strings,
    _preserve_read_raw,
    _response_fields,
    _rows,
    _strict_scalar_string,
)
from ._read_parser_common import (
    _optional_read_rows,
    _parse_add_srv_item,
    _required_read_rows,
    _required_read_strings,
    _validate_envelope,
    _validate_strict_read_envelope,
)
from ._read_pass_parsers import _parse_pass_menu_data
from .errors import KorailProtocolError
from .read_models import (
    CartItem,
    CartListResponse,
    CrewRequestListResponse,
    CrewRequestOption,
    CustomerTripInfo,
    CustomerTripInfoResponse,
    DelayDiscountTicket,
    DelayDiscountTicketListResponse,
    DepositBank,
    DepositBankListResponse,
    DiscountCoupon,
    DiscountCouponListResponse,
    KorailPointSummaryResponse,
    MaasCancelFeeResponse,
    MaasServiceDetailListResponse,
    MileageHistoryEntry,
    MileageHistoryResponse,
    MultiChildDiscountTarget,
    MultiChildDiscountTargetResponse,
    ProductDetailResponse,
    ProductReservation,
    ProductReservationListResponse,
    ServiceStatusResponse,
    TravelProduct,
    TravelProductSearchResponse,
    TripChangeDateResponse,
    TripMenuContent,
    TripMenuItem,
    TripMenuResponse,
)

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

# CartInfo.java:28-61,281-392의 문자열 28개를 읽습니다. 숫자형 전송 가능성을 고려해 JSON 정수도 허용하지만 각 장바구니 필드의 실제 숫자 형식은 미확인입니다.
_CART_ITEM_SCALAR_FIELDS: dict[str, str] = {
    "item_type_code": "h_item_dv_cd",
    "provider_id": "h_add_srv_mrk_ent_id",
    "item_sequence": "h_item_sqno",
    "journey_sequence": "h_jrny_sqno",
    "journey_type_code": "h_jrny_tp_cd",
    "usage_close_date": "utlClsDt",
    "settlement_limit_time": "h_stl_lmt_tm",
    "settlement_extension_transaction_no": "h_stl_extns_tno",
    "settlement_means_allow_value": "h_stl_mns_allw_val",
    "field_settlement_division": "h_fld_stl_dv",
    "supervising_station_code": "h_spvs_rs_stn_cd",
    "filler": "h_filler",
}

_DEPOSIT_BANK_FIELDS: dict[str, str] = {
    "code": "dptnBankCd",
    "display_name": "dptnBankNm",
}

_DELAY_DISCOUNT_TICKET_FIELDS: dict[str, str] = {
    "fare": "h_dlay_fare",
    "original_sale_date": "h_orgtk_ret_sale_dt",
    "window_no": "h_orgtk_wct_no",
    "sale_sequence": "h_orgtk_sale_sqno",
    "return_password": "h_orgtk_ret_pwd",
}

_DELAY_DISCOUNT_TICKET_SCALAR_FIELDS: dict[str, str] = {
    "ticket_sequence": "h_tk_sqno",
    "ticket_kind_code": "h_tk_knd_cd",
    "original_ticket_sale_date": "h_orgtk_sale_dt",
    "received_amount": "h_rcvd_amt",
    "train_class_code": "h_trn_clsf_cd",
    "room_class_code": "h_psrm_cl_cd",
    "train_no": "h_trn_no",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "ticket_status_code": "h_tk_stt_cd",
    "ticket_status_name": "h_tk_stt_nm",
    "buyer_name": "h_buy_ps_nm",
    "passenger_name": "h_abrd_ps_nm",
    "page_no": "h_page_no",
}

_DELAY_DISCOUNT_MAIN_INFO_FIELDS: dict[str, str] = {
    "current_page": "h_page_no",
    "total_pages": "h_tot_page_cnt",
    "total_count": "h_tot_cnt",
    "row_count": "h_row_cnt",
    "last_page_flag": "h_last_page_yn",
}

_CREW_REQUEST_OPTION_FIELDS: dict[str, str] = {
    "message_code": "intgMsgCd",
    "content": "prsCont",
}

_TRIP_MENU_CONTENT_FIELDS: dict[str, str] = {
    "title": "contTitle",
    "detail": "contDetail",
    # detailType은 항목 종류로 해석하지 않습니다(TrGdMenuLtOutCont.java:42).
    "detail_type": "detailType",
    "active": "passActive",
    "agree": "passAgree",
    "info": "passInfo",
    "image": "contImage",
    "url": "contUrl",
    # 앱은 cmtrKndCd로 항목을 찾아 passData가 없으면 화면을 되돌립니다(PassConditionViewModel.java:1241,1244,1247-1248).
    # 실서버 관측: menuType='P'인 6/60행에서 확인했습니다.
    "commuter_kind_code": "cmtrKndCd",
    "pass_type": "passType",
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
    "reservation_sequence": "strVrRsvSqno",
    "reservation_status_code": "strRsvSttCd",
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
    "goods_sequence": "strGdSqno",
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


@_preserve_read_raw
def parse_cart_list_response(raw: Mapping[str, Any]) -> CartListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    items = []
    for item in _nested_rows(raw, "cart_infos", "cart_info"):
        items.append(
            CartItem(
                **_nullable_scalar_fields(item, _CART_ITEM_FIELDS),
                **_nullable_scalar_fields(item, _CART_ITEM_SCALAR_FIELDS, "cart item"),
                # h_tk_cnt 는 String 선언입니다(CartInfo.java:51).
                ticket_count=_optional_scalar_string(item, "h_tk_cnt"),
                raw=item,
            )
        )
    return CartListResponse(items=tuple(items), **_response_fields(raw))


@_preserve_read_raw
def parse_deposit_bank_response(
    raw: Mapping[str, Any],
) -> DepositBankListResponse:
    _validate_envelope(raw)
    items = tuple(
        DepositBank(
            **_required_read_strings(row, _DEPOSIT_BANK_FIELDS, "deposit bank"),
            raw=row,
        )
        for row in _rows(raw, "dptnBank")
    )
    return DepositBankListResponse(items=items, **_response_fields(raw))


@_preserve_read_raw
def parse_delay_discount_ticket_response(
    raw: Mapping[str, Any],
) -> DelayDiscountTicketListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    rows = _nested_rows(raw, "disc_infos", "disc_info")
    items = tuple(
        DelayDiscountTicket(
            **_nullable_scalar_fields(row, _DELAY_DISCOUNT_TICKET_FIELDS),
            **_nullable_scalar_fields(row, _DELAY_DISCOUNT_TICKET_SCALAR_FIELDS, "delay discount ticket"),
            raw=row,
        )
        for row in rows
    )
    # main_info 는 DTO 밖 서버 추가 블록(DelayDiscountViewOut.java:24,51). 관측은 할인권 없는 계정의 0 값뿐입니다.
    main_info = _optional_mapping(raw, "main_info")
    pagination: dict[str, Any] = {}
    if main_info is not None:
        pagination = _nullable_scalar_fields(
            main_info,
            _DELAY_DISCOUNT_MAIN_INFO_FIELDS,
            "delay discount ticket list main_info",
        )
    return DelayDiscountTicketListResponse(
        items=items,
        **pagination,
        **_response_fields(raw),
    )


# CouponOutInfo.java:63 의 13필드는 모두 선택입니다.
_DISCOUNT_COUPON_FIELDS = {
    "guide": "guide",
    "start_date": "h_fdcert_mg_st_dt",
    "expiration_date": "h_fdcert_mg_cls_dt",
    "discount_kind_code": "h_dscp_knd_cd",
    "discount_rate_amount_division_code": "h_disc_rt_amt_dv_cd",
    "weekday_fare_discount": "h_inwk_fare_disc_rt_amt",
    "weekday_price_discount": "h_inwk_prc_disc_rt_amt",
    "weekend_fare_discount": "h_wknd_fare_disc_rt_amt",
    "weekend_price_discount": "h_wknd_prc_disc_rt_amt",
    "coupon_no": "h_cpn_no",
}


@_preserve_read_raw
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
    )
    for item in rows:
        items.append(
            DiscountCoupon(
                **_nullable_scalar_fields(item, _DISCOUNT_COUPON_FIELDS, "discount coupon"),
                remarks=_present_strings(item, ("h_rmk_1_cont", "h_rmk_2_cont", "h_rmk_3_cont")),
                raw=item,
            )
        )
    return DiscountCouponListResponse(
        items=tuple(items),
        current_page=_optional_integer(raw, "h_page_no", "coupon response"),
        total_pages=_optional_integer(raw, "h_tot_page_cnt", "coupon response"),
        total_count=_optional_scalar_string(raw, "h_tot_cnt", "coupon response"),
        row_count=_optional_scalar_string(raw, "h_row_cnt", "coupon response"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_trip_menu_response(raw: Mapping[str, Any]) -> TripMenuResponse:
    _validate_envelope(raw)
    items = []
    for item in _rows(raw, "menuList"):
        contents = tuple(
            TripMenuContent(
                **_nullable_scalar_fields(row, _TRIP_MENU_CONTENT_FIELDS, "trip menu content"),
                # TrGdMenuLtOutCont.java:45 passData → TrGdMenuLtOutPass.java:29-35.
                pass_data=_parse_pass_menu_data(
                    _optional_mapping(row, "passData"),
                    # TrGdMenuLtOutPass.java:152 — 여행 메뉴의 키 철자는 별도입니다.
                    station_selection_key="h_seiect_station",
                ),
                raw=row,
            )
            for row in _rows(item, "contList")
        )
        items.append(
            TripMenuItem(
                **_nullable_scalar_fields(item, _TRIP_MENU_ITEM_FIELDS),
                content_count=_optional_integer(item, "contCount", "trip menu item"),
                contents=contents,
                raw=item,
            )
        )
    return TripMenuResponse(
        items=tuple(items),
        popup_message=_optional_scalar_string(raw, "poppMsg"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_product_reservation_list_response(
    raw: Mapping[str, Any],
) -> ProductReservationListResponse:
    _validate_envelope(raw, allow_result_only_success=True)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductReservationListResponse(**_response_fields(raw))
    items = tuple(
        ProductReservation(
            **_nullable_scalar_fields(row, _PRODUCT_RESERVATION_FIELDS),
            raw=row,
        )
        for row in _rows(main, "entity")
    )
    return ProductReservationListResponse(
        items=items,
        total_count=_optional_integer(main, "strTotCnt", "product reservation list"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_product_detail_response(
    raw: Mapping[str, Any],
) -> ProductDetailResponse:
    _validate_envelope(raw)
    main = _optional_mapping(raw, "mainInfo")
    if main is None:
        return ProductDetailResponse(**_response_fields(raw))
    included_items = []
    for item in _rows(main, "entityOne"):
        name = _optional_scalar_string(item, "strGdConsItmNm")
        if name is not None:
            included_items.append(name)
    return ProductDetailResponse(
        **_nullable_scalar_fields(main, _PRODUCT_DETAIL_FIELDS),
        included_item_names=tuple(included_items),
        detail_raw=main,
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
    # MyXPointViewOut.java:43,53,54 — customer_lead_flag_name 의 플래그 짝과 disability_flag 의 유형 코드·이름입니다.
    "customer_lead_flag": "h_cust_lead_flg",
    "disability_type_code": "h_hdcp_tp_cd",
    "disability_type_name": "h_hdcp_tp_cd_nm",
    # 아래 넷의 네이버/카카오/구글/애플 **순서는 7.0.6 에서 미확인** 입니다 (read_models.KorailPointSummaryResponse 의 해당 주석 참고).
    "naver_linked_flag": "h_logn_tp_cd1",
    "kakao_linked_flag": "h_logn_tp_cd2",
    "google_linked_flag": "h_logn_tp_cd4",
    "apple_linked_flag": "h_logn_tp_cd5",
}

_MILEAGE_HISTORY_FIELDS = {
    "page_count": "pgCnt",
    "query_count": "qryCnt",
    "total_available_rail_point": "totAvlRailPontValNum",
    "total_available_rail_point_1": "totAvlRailPontValNum1",
    "total_available_affiliate_point": "totAvlAfltPontValNum",
    "total_accumulated_rail_point_1": "totAcmRailPontValNum1",
    "total_used_rail_point_1": "totUseRailPontValNum1",
    # railNowSavePontValNum1 은 DTO 미선언(AmtSpecOut.java:29-39, AmtSpecOutSpecInfo.java:29-35). 관측: KTX/RAIL_POINT
    # 의 모든 확인 페이지에 9자리 문자열로 있었으며 해당 계정에서는 totAcmRailPontValNum1 과 같았습니다.
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


@_preserve_read_raw
def parse_korail_point_summary_response(
    raw: Mapping[str, Any],
) -> KorailPointSummaryResponse:
    _validate_strict_read_envelope(raw)
    return KorailPointSummaryResponse(
        # MyXPointViewOut.java:27-74 는 String 이고 표본도 48키 모두 문자열이었습니다.
        **_nullable_scalar_fields(raw, _KORAIL_POINT_SUMMARY_FIELDS, "korail point summary"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_mileage_history_response(
    raw: Mapping[str, Any],
) -> MileageHistoryResponse:
    _validate_strict_read_envelope(raw)
    entries = []
    for item in _rows(raw, "specList"):
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
        **_nullable_scalar_fields(raw, _MILEAGE_HISTORY_FIELDS, "mileage history"),
        entries=tuple(entries),
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
    # CustTripInfo.java:48 의 별칭 없는 속성명에서 키를 추정합니다. 보호 descriptor 는 미확인입니다.
    "goods_no": "gdNo",
}


@_preserve_read_raw
def parse_multi_child_discount_target_response(
    raw: Mapping[str, Any],
) -> MultiChildDiscountTargetResponse:
    _validate_strict_read_envelope(raw)
    targets = []
    for item in _rows(raw, "fmlyList"):
        targets.append(
            MultiChildDiscountTarget(
                **_nullable_scalar_fields(
                    item,
                    _MULTI_CHILD_FIELDS,
                ),
                raw=item,
            )
        )
    return MultiChildDiscountTargetResponse(
        targets=tuple(targets),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_customer_trip_info_response(
    raw: Mapping[str, Any],
) -> CustomerTripInfoResponse:
    _validate_strict_read_envelope(raw)
    trips = []
    for item in _required_read_rows(raw, "mainList", "customer trip info"):
        trips.append(
            CustomerTripInfo(
                **_nullable_scalar_fields(item, _CUSTOMER_TRIP_FIELDS, "customer trip info"),
                raw=item,
            )
        )
    return CustomerTripInfoResponse(
        trips=tuple(trips),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_maas_cancel_fee_response(raw: Mapping[str, Any]) -> MaasCancelFeeResponse:
    """지원하지 않는 부가서비스 환불 수수료 응답을 읽습니다. maas.cncFee.do 응답. cncRetFee 는 선택 스칼라로 읽습니다(MaasCancelFeeOut.java)."""
    _validate_envelope(raw)
    return MaasCancelFeeResponse(
        cancel_fee=_optional_scalar_string(raw, "cncRetFee", "MaaS cancel fee"),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_maas_service_detail_list_response(
    raw: Mapping[str, Any],
) -> MaasServiceDetailListResponse:
    _validate_strict_read_envelope(raw)
    details = []
    for item in _rows(raw, "addSrvList"):
        details.append(_parse_add_srv_item(item, "MaaS service detail", "MaaS detail info"))
    return MaasServiceDetailListResponse(
        details=tuple(details),
        **_response_fields(raw),
    )


@_preserve_read_raw
def parse_trip_change_date_response(
    raw: Mapping[str, Any],
) -> TripChangeDateResponse:
    _validate_strict_read_envelope(raw)
    dates = raw.get("tripChgDates")
    if not isinstance(dates, list):
        raise KorailProtocolError("KORAIL tripChgDates must be a string list")
    normalized_dates = []
    for value in dates:
        date = _strict_scalar_string({"tripChgDates": value}, "tripChgDates", "trip change dates")
        if date is None:
            raise KorailProtocolError("KORAIL tripChgDates must not contain null")
        normalized_dates.append(date)
    # 응답은 복수형 tripChgDates 입니다(TipChgDateInquiryOut.java:28-30). 단수형 tripChgDate 는 요청
    # 필드(TipChgDateInquiryIn.java:29)이므로 응답 별칭으로 쓰지 않습니다.
    return TripChangeDateResponse(
        last_run_date=_optional_scalar_string(raw, "lastRunDt"),
        trip_change_dates=tuple(normalized_dates),
        **_response_fields(raw),
    )


_TRAVEL_PRODUCT_FIELDS = {
    "goods_no": "gdNo",
    "name": "gdNm",
    "area_code": "gdTripArCd",
    "area_name": "gdTripArNm",
    "event_start_date": "evtStDt",
    "event_end_date": "evtClsDt",
    "company_name": "entNm",
    "info_url": "gdInfoUrlAdr",
    "representative_fare": "gdRepFare",
    "description": "ln1DscCont",
    "standard_clause_1": "gdStdrClauValCont1",
    "standard_clause_2": "gdStdrClauValCont2",
}


@_preserve_read_raw
def parse_travel_product_search_response(raw: Mapping[str, Any]) -> TravelProductSearchResponse:
    _validate_strict_read_envelope(raw)
    listing = raw.get("lst")
    if listing is None:
        return TravelProductSearchResponse(**_response_fields(raw))
    if not isinstance(listing, Mapping):
        raise KorailProtocolError("KORAIL travel product search field lst must be an object or null")
    products = tuple(
        TravelProduct(**_nullable_scalar_fields(row, _TRAVEL_PRODUCT_FIELDS, "travel product"), raw=row)
        for row in _optional_read_rows(listing, "gdList", "travel product search")
    )
    return TravelProductSearchResponse(
        products=products,
        query_count=_optional_scalar_string(listing, "qryCnt", "travel product search"),
        page_count=_optional_scalar_string(listing, "pgCnt", "travel product search"),
        **_response_fields(raw),
    )
