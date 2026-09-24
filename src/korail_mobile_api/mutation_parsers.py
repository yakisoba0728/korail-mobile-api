# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태 변경 응답을 모델로 변환하고 원문을 보존합니다. 성공 여부는 전송 계층에서 판정하며 필수 신원·금액은 엄격히, 선택값은 관대하게 읽습니다. 파싱 실패는 서버 처리 실패의 증거가 아닙니다.
자동 재전송하지 마십시오. 클라이언트의 예외 원문 보존 규칙은 KorailClient._mutation을 따릅니다."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from ._parsing import (
    RESERVATION_OUT_EXTRA_FIELDS,
    _nested_rows,
    _nullable_scalar_fields,
    _optional_scalar_string,
    _reservation_passengers,
    _rows,
    _strict_scalar_string,
)
from ._parsing import _response_fields as _base_fields
from .errors import KorailProtocolError
from .mutation_models import (
    CartAddResponse,
    CartDiscountAddition,
    DiscountCardPurchaseResponse,
    MaasCancelResponse,
    ProductCancelResponse,
    RefundTicketResponse,
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
    ReservationPaymentSettlement,
    ReservationPaymentTableSeat,
    ReservationPaymentTicket,
    StationRefundExecutionResponse,
    StationRefundOriginalTicket,
    StationRefundVerificationResponse,
)


def parse_refund_ticket_response(raw: Mapping[str, Any]) -> RefundTicketResponse:
    """필수·nullable stlList 와 각 행의 필수 stl_mns_cd 를 읽습니다.

    RefundTicketOut.java:48-53 의 마스크는 8, StlList.java:46-55 는 1입니다.
    누락·잘못된 정산 행을 빈 성공 결과로 바꾸지 않습니다.
    """
    copied = _response_mapping(raw)
    if "stlList" not in copied:
        raise KorailProtocolError("KORAIL refund stlList is required")
    rows = copied["stlList"]
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL refund stlList must be a list or null")
    codes: list[str] = []
    for value in rows or ():
        try:
            row = _row(value, "refund settlement")
            code = _strict_scalar_string(row, "stl_mns_cd", "refund settlement")
            if code is None:
                raise KorailProtocolError("KORAIL refund stl_mns_cd is required and non-null")
        except KorailProtocolError as error:
            error.raw = value
            raise
        codes.append(code)
    return RefundTicketResponse(
        **_base_fields(copied),
        settlement_method_codes=tuple(codes),
        settlement_list_is_null=rows is None,
    )


_STATION_REFUND_ORIGINAL_FIELDS = {
    "original_sale_date": "ogtk_sale_dt",
    "original_sale_window_no": "ogtk_sale_wct_no",
    "original_sale_sequence": "ogtk_sale_sqno",
    "original_return_password": "ogtk_ret_pwd",
    "ticket_kind_code": "tk_knd_cd",
    "refund_division_code": "ret_dv_cd",
    "refund_reason_code": "ret_rsn_cd",
}


def parse_station_refund_verification_response(
    raw: Mapping[str, Any],
) -> StationRefundVerificationResponse:
    """역발행 승차권 환불 확인 응답과 원승차권 목록을 읽습니다. 원표 목록·PNR·원표 식별자·세 금액은 실제 환불의 확인값이므로 엄격히 읽고 두 안내 문구만 관대하게 읽습니다."""
    copied = _response_mapping(raw)
    rows = copied.get("orgtkinfo_list", [])
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station refund orgtkinfo_list must be a list")
    original_tickets: list[StationRefundOriginalTicket] = []
    for row in rows or ():
        row = _row(row, "station refund Orgtkinfo")
        pnr_no = _strict_scalar_string(row, "pnr_no", "station refund Orgtkinfo")
        if not pnr_no:
            raise KorailProtocolError("KORAIL station refund Orgtkinfo.pnr_no is required")
        identity_fields = {
            attr: _strict_scalar_string(row, wire_key, "station refund Orgtkinfo")
            for attr, wire_key in _STATION_REFUND_ORIGINAL_FIELDS.items()
        }
        original_tickets.append(
            StationRefundOriginalTicket(
                pnr_no=pnr_no,
                **identity_fields,
                raw=dict(row),
            )
        )
    return StationRefundVerificationResponse(
        **_base_fields(copied),
        received_amount=_strict_scalar_string(copied, "rcvd_amt", "station refund verification"),
        refund_fee=_strict_scalar_string(copied, "ret_fee", "station refund verification"),
        refund_amount=_strict_scalar_string(copied, "ret_amt", "station refund verification"),
        popup_message=_optional_scalar_string(copied, "poppMsg", "station refund verification"),
        result_message=_optional_scalar_string(copied, "strMsg", "station refund verification"),
        original_tickets=tuple(original_tickets),
        original_ticket_list_is_null=rows is None,
    )


def parse_station_refund_execution_response(
    raw: Mapping[str, Any],
) -> StationRefundExecutionResponse:
    """역발행 환불 실행의 반환 구분을 보존합니다."""
    copied = _response_mapping(raw)
    return StationRefundExecutionResponse(
        **_base_fields(copied),
        refund_division_code=_optional_scalar_string(copied, "h_ret_dv_cd", "station refund execution"),
    )


_DIGITS_RE = re.compile(r"[0-9]+")


def _response_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    """직접 호출도 가능하므로 raw 가 매핑인지 확인하고 복사합니다. 봉투 3필드의 타입은 _parsing._envelope 가 검사하며 성공 여부는 이 모듈이
    검사하지 않습니다."""
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    return dict(raw)


def _row(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(f"KORAIL {context} must be an object")
    return value


def _received_amount(
    raw: Mapping[str, Any],
    journey_rows: list[Mapping[str, Any]],
) -> str | None:
    """좌석별 h_rcvd_amt 합과 선언 총액을 대조하는 라이브러리 정책입니다. 앱은 일반 결제에서 h_tot_rcvd_amt 를
    합산합니다(PayViewModel.java:11297-11307). 번호 붙은 결제 금액으로의 최종 연결은 보호된 Bundle 키 때문에 미확인입니다
    (PaymentMethodHelper.java:113,211).

    미배정 0원 행은 제외하고, 사용할 좌석 행이 없으면 선언 총액만 씁니다. 한 좌석 금액이 읽히지 않으면 부분 합을 반환하지 않습니다. 두 출처가 다르면 오류, 사용 가능한 출처가 없으면
    None 입니다."""
    declared = _strict_scalar_string(raw, "h_tot_rcvd_amt", "reservation")
    if declared is not None:
        declared = declared.strip()
        if not _DIGITS_RE.fullmatch(declared):
            declared = None
    declared_int: int | None
    if declared is None:
        declared_int = None
    else:
        try:
            declared_int = int(declared)
        except ValueError:
            declared_int = None

    summed = 0
    seats_seen = 0
    for journey in journey_rows:
        container = journey.get("seat_infos")
        if container is None:
            continue
        if not isinstance(container, Mapping):
            raise KorailProtocolError("KORAIL reservation seat_infos must be an object or null")
        seat_rows = container.get("seat_info")
        if seat_rows is None:
            continue
        if not isinstance(seat_rows, list):
            raise KorailProtocolError("KORAIL reservation seat_infos.seat_info must be a list or null")
        for seat in seat_rows:
            seat = _row(seat, "reservation seat_info row")
            amount = _strict_scalar_string(seat, "h_rcvd_amt", "reservation seat")
            if amount is None or not _DIGITS_RE.fullmatch(amount.strip()):
                return None
            try:
                value = int(amount)
            except ValueError:
                # 큰 정수의 문자열 변환 실패도 0원으로 취급하지 않습니다.
                return None
            seat_no = _optional_scalar_string(seat, "h_seat_no", "reservation seat") or ""
            if value == 0 and not seat_no.strip():
                # 2026-09-22 예약대기 관측: 좌석번호 없는 0원 행은 정산 좌석이 아니었습니다. 동일 예약을 get_ticket_reservation_detail 로 조회한 좌석
                # 합은 선언 총액과 일치했습니다. 이 빈 행을 합산하면 잘못된 총액 불일치를 만들므로 제외합니다.
                continue
            summed += value
            seats_seen += 1
    if seats_seen == 0:
        return None if declared_int is None else str(declared_int)
    seat_total = str(summed)
    # 2026-07-27 라이브: 좌석 금액과 총액의 영 채움 폭이 달랐습니다. 표기 문자열이 아니라 숫자로 비교해야 같은 금액을 모순으로 오인하지 않습니다.
    if declared_int is not None and declared_int != summed:
        raise KorailProtocolError(
            "KORAIL reservation settlement amount is ambiguous: the seat rows "
            f"sum to {summed} but h_tot_rcvd_amt says {declared_int}. This "
            "library treats the per-seat sum as its primary source -- that is "
            "this package's policy, not a rule the app enforces -- so it "
            "refuses here rather than guess which amount to charge."
        )
    # 0 채움 없는 정산액 반환은 앱 재현이 아닌 라이브러리 정책입니다. 7.0.6 에는 번호 붙은 hidMnsStlAmt1 이 평문 0건이고 번호 없는
    # hidMnsStlAmt(ReservationPaymentInStlInfo, PaymentMethod)만 있습니다. hidMnsStlAmt<N> 으로 가는 마지막 단계는 보호돼 있습니다.
    return seat_total


_RESERVATION_HOLD_REQUIRED_FIELDS = {
    "pnr_no": "h_pnr_no",
    "journey_count": "h_jrny_cnt",
    "window_no": "h_wct_no",
    "temporary_job_sequence_1": "h_tmp_job_sqno1",
    "temporary_job_sequence_2": "h_tmp_job_sqno2",
}

_RESERVATION_HOLD_FIELDS = {
    "payment_flag": "h_payment_flg",
    "payment_message": "h_payment_msg",
    "payment_deadline_message": "h_pay_limit_msg",
    "payment_deadline_notice": "h_ntisu_lmt",
    "payment_deadline_date": "h_ntisu_lmt_dt",
    "payment_deadline_time": "h_ntisu_lmt_tm",
    "total_fare": "h_tot_fare",
    "total_price": "h_tot_prc",
    "total_discount_amount": "h_tot_dcnt_amt",
}

_RESERVATION_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "train_no": "h_trn_no",
    "arrival_date": "h_arv_dt",
}

_PAYMENT_COUPON_FIELDS = {
    "certificate_password": "h_cert_pwd",
    "coupon_no": "h_coup_no",
    "management_close_date": "h_fdcert_mg_cls_dt",
    "management_start_date": "h_fdcert_mg_st_dt",
    "ticket_return_no": "h_tk_ret_no",
}

# 결제 응답 고유 스칼라(ReservationPaymentOut.java:90).
_RESERVATION_PAYMENT_FIELDS = {
    "reservation_no": "h_rsv_no",
    "settlement_approval_no": "h_stl_cd_apprv_no",
    "total_received_amount": "h_tot_rcvd_amt",
    "settlement_amount": "h_stl_amt",
    "total_settlement_amount": "h_tot_stl_amt",
    "customer_no": "h_cust_no",
    "member_card_no": "h_mb_crd_no",
    "buyer_name": "h_buy_name",
    "publication_start_no": "h_publ_start_no",
    "publication_end_no": "h_publ_end_no",
    "mixed_settlement_division": "h_mix_stl_dv",
    "cancellation_fee": "h_cnc_fee",
    "window_no": "h_wct_no",
    "settlement_count": "h_stl_cnt",
    "discount_card_count": "h_disc_card_cnt",
    "total_price": "h_tot_prc",
    "total_fare": "h_tot_fare",
    "total_discount_amount": "h_tot_disc_amt",
    "adult_count": "h_adult_cnt",
    "child_count": "h_child_cnt",
    "table_seat_count": "h_tbl_seat_cnt",
    "ticket_count": "h_tk_cnt",
    "settlement_type_code": "h_stl_tp_cd",
    "trade_division": "h_trade_gbn",
    "remark": "h_bigo",
    "survey_flag": "h_survey_flg",
    "survey_title": "h_survey_title",
    "survey_text": "h_survey_text",
    "survey_url": "h_survey_url",
}

_RESERVATION_PAYMENT_TICKET_FIELDS = {
    "ticket_sequence": "h_tk_sqno",
    "sale_date": "h_sale_dt",
    "sale_sequence": "h_sale_sqno",
    "return_password": "h_tk_ret_pwd",
    "return_no": "h_tk_ret_no",
    "recipient_name": "h_take_name",
    "discount_card_no": "h_disc_card_no",
    "ticket_price": "h_tk_prc",
    "ticket_fare": "h_tk_fare",
    "bz5_fare_discount_amount": "h_bz5_fare_disc_amt",
    "bz6_fare_discount_amount": "h_bz6_fare_disc_amt",
    "total_discount_amount": "h_tot_disc_amt",
    "total_received_amount": "h_tot_rcvd_amt",
    "standard_seat_price_fare": "h_std_seat_prc_fare",
}

_RESERVATION_PAYMENT_SETTLEMENT_FIELDS = {
    "settlement_sequence": "h_stl_sqno",
    "settlement_type_code": "h_stl_tp_cd",
    "settlement_result": "h_stl_rlt",
    "transaction_division": "h_tr_gubun",
    "card_installment_count": "h_crd_stl_cnt",
    "installment_months": "h_inst_month",
    "settlement_amount": "h_stl_amt",
    "settlement_card_no": "h_stl_crd_no",
    "card_company_code": "h_crd_corp_cd",
    "card_company_name": "h_crd_corp_nm",
    "approval_date": "h_apv_dt",
    "approval_time": "h_apv_tm",
    "approval_no": "h_apv_no",
    "point_division": "h_xpoint_dv",
    "point_no": "h_xpoint_no",
    "point_approval_no": "h_xpoint_apv_no",
    "remnant_amount": "h_remnant_amt",
    "remote_point": "h_rmt_point",
}

_RESERVATION_PAYMENT_TABLE_SEAT_FIELDS = {
    "room_class_name_1": "h_psrm_cl_cd_nm1",
    "car_no_1": "h_srcar_no1",
    "seat_no_start_1": "h_tbl_seat_no_sno_1",
    "seat_no_end_1": "h_tbl_seat_no_eno_1",
    "seat_count_1": "h_tbl_seat_cnt_1",
    "group_name_1": "h_sgr_nm_1",
    "room_class_name_2": "h_psrm_cl_cd_nm2",
    "car_no_2": "h_srcar_no2",
    "seat_no_start_2": "h_tbl_seat_no_sno_2",
    "seat_no_end_2": "h_tbl_seat_no_eno_2",
    "seat_count_2": "h_tbl_seat_cnt_2",
    "group_name_2": "h_sgr_nm_2",
}


def parse_reservation_hold_response(
    raw: Mapping[str, Any],
) -> ReservationHoldResponse:
    """홀드의 후속 결제·취소 값을 읽습니다. 여정·정산값은 엄격히 검사하되 성공 여부는 재검사하지 않습니다. 직접 호출자는 str_result·h_msg_cd 를
    확인하고, 파싱 실패만 보고 다시 요청하지 마십시오 — 예약이 이미 생성됐을 수 있습니다."""
    copied = _response_mapping(raw)
    journeys_container = copied.get("jrny_infos")
    if journeys_container is None:
        journey_rows: list[Any] = []
    elif isinstance(journeys_container, Mapping):
        value = journeys_container.get("jrny_info")
        if value is None:
            journey_rows = []
        elif isinstance(value, list):
            journey_rows = value
        else:
            raise KorailProtocolError("KORAIL reservation jrny_infos.jrny_info must be a list or null")
    else:
        raise KorailProtocolError("KORAIL reservation jrny_infos must be an object or null")

    journeys: list[ReservationJourney] = []
    for value in journey_rows:
        row = dict(_row(value, "reservation journey"))
        journeys.append(
            ReservationJourney(
                **_nullable_scalar_fields(row, _RESERVATION_JOURNEY_FIELDS, "reservation journey"),
                reservation_change_no=_strict_scalar_string(row, "h_rsv_chg_no", "reservation journey"),
                raw=row,
            )
        )

    required: dict[str, Any] = {
        attr: _strict_scalar_string(copied, wire_key, "reservation")
        for attr, wire_key in _RESERVATION_HOLD_REQUIRED_FIELDS.items()
    }
    return ReservationHoldResponse(
        **_base_fields(copied),
        **required,
        **_nullable_scalar_fields(copied, _RESERVATION_HOLD_FIELDS, "reservation"),
        received_amount=_received_amount(
            copied,
            [journey.raw for journey in journeys],
        ),
        journeys=tuple(journeys),
        **_nullable_scalar_fields(copied, RESERVATION_OUT_EXTRA_FIELDS, "reservation"),
        passengers=_reservation_passengers(copied),
    )


def parse_reservation_payment_response(
    raw: Mapping[str, Any],
) -> ReservationPaymentResponse:
    """결제 결과의 중첩 목록을 관대하게 읽으며 성공 여부는 판정하지 않습니다. 반환 비밀번호·수령인 등 민감값은 타입 필드와 raw 에 그대로 남습니다. 이미 승인됐을 수 있으므로 파싱 결과만
    보고 결제를 재전송하지 마십시오."""
    copied = _response_mapping(raw)
    coupons: list[ReservationPaymentCoupon] = []
    for value in _rows(copied, "tk_coupon_info"):
        row = dict(value)
        coupons.append(
            ReservationPaymentCoupon(
                **_nullable_scalar_fields(row, _PAYMENT_COUPON_FIELDS, "payment coupon"),
                raw=row,
            )
        )

    tickets: list[ReservationPaymentTicket] = []
    for value in _nested_rows(copied, "tk_infos", "tk_info"):
        row = dict(value)
        tickets.append(
            ReservationPaymentTicket(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_TICKET_FIELDS, "payment ticket"),
                raw=row,
            )
        )

    settlements: list[ReservationPaymentSettlement] = []
    for value in _nested_rows(copied, "stl_infos", "stl_info"):
        row = dict(value)
        settlements.append(
            ReservationPaymentSettlement(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_SETTLEMENT_FIELDS, "payment settlement"),
                raw=row,
            )
        )

    table_seats: list[ReservationPaymentTableSeat] = []
    for value in _nested_rows(copied, "tbl_seat_infos", "tbl_seat_info"):
        row = dict(value)
        table_seats.append(
            ReservationPaymentTableSeat(
                **_nullable_scalar_fields(row, _RESERVATION_PAYMENT_TABLE_SEAT_FIELDS, "payment table seat"),
                raw=row,
            )
        )

    return ReservationPaymentResponse(
        **_base_fields(copied),
        image_ticket_flag=_optional_scalar_string(copied, "h_im_flg", "payment"),
        **_nullable_scalar_fields(copied, _RESERVATION_PAYMENT_FIELDS, "payment"),
        coupons=tuple(coupons),
        tickets=tuple(tickets),
        settlements=tuple(settlements),
        table_seats=tuple(table_seats),
    )


_DISCOUNT_CARD_PURCHASE_FIELDS = {
    "lump_settlement_target_no": "lumpStlTgtNo",
    "received_amount": "rcvdAmt",
    "usable_trip_count": "usePsbTno",
    "validity_start_date": "vlidTrmStDt",
    "validity_end_date": "vlidTrmClsDt",
    "discount_card_settlement_target_no": "dcntCrdStlTgtNo",
    "stx_amount": "stxAmt",
    "taxt_supply_amount": "taxtSplAmt",
    # NCardInfoOut.java:30 의 속성은 dcntCrdStlTgtNo 와 별개입니다. 전송 키는 @SerialName 없는 속성명에서 추정했으며 보호된 descriptor 로 직접
    # 확인되지 않았습니다.
    "registered_card_kind_management_no": "dcntCrdKndMgNo",
}


def parse_discount_card_purchase_response(
    raw: Mapping[str, Any],
) -> DiscountCardPurchaseResponse:
    """검증 못 함: N카드가 없는 계정이라 실서버에서 확인하지 못했습니다. NCardInfoOut.java:30-38 의 자체 속성 9개를 읽습니다. serializer 이름이 보호돼
    Kotlin 속성명을 전송 키로 사용하는 부분은 추정이며 실서버 검증 못 함입니다."""
    data = _response_mapping(raw)
    return DiscountCardPurchaseResponse(
        **_base_fields(data),
        **_nullable_scalar_fields(data, _DISCOUNT_CARD_PURCHASE_FIELDS, "discount card purchase"),
    )


_CART_DISCOUNT_ADDITION_FIELDS = {
    "passenger_sequence_no": "h_psg_sqno",
    "duty_reference_recognition_division_code": "h_duty_ref_rcgn_ps_dv_cd",
}


def _cart_discount_additions(
    data: Mapping[str, Any],
) -> tuple[CartDiscountAddition, ...]:
    """``psgDiscAdd_infos`` 를 읽습니다. 모양이 어긋나면 빈 튜플, 객체가 아닌 행은 건너뜁니다."""
    return tuple(
        CartDiscountAddition(
            raw=item,
            **_nullable_scalar_fields(item, _CART_DISCOUNT_ADDITION_FIELDS, "cart add discount row"),
        )
        for item in _nested_rows(data, "psgDiscAdd_infos", "psgDiscAdd_info")
    )


def parse_product_cancel_response(raw: Mapping[str, Any]) -> ProductCancelResponse:
    """여행상품 예약 취소 응답을 읽습니다. intgMsgCd 는 선택 스칼라입니다(ProductCancelOut.java)."""
    data = _response_mapping(raw)
    return ProductCancelResponse(
        **_base_fields(data),
        integrated_message_code=_optional_scalar_string(data, "intgMsgCd", "product cancel"),
    )


def parse_maas_cancel_response(raw: Mapping[str, Any]) -> MaasCancelResponse:
    """지원하지 않는 미결제 부가서비스 해제 응답을 읽습니다. addService.cancelPay.do 응답. intgMsgCd 는 선택 스칼라입니다(MaasCancelOut.java)."""
    data = _response_mapping(raw)
    return MaasCancelResponse(
        **_base_fields(data),
        integrated_message_code=_optional_scalar_string(data, "intgMsgCd", "MaaS cancel"),
    )


def parse_cart_add_response(raw: Mapping[str, Any]) -> CartAddResponse:
    """장바구니 추가 결과와 할인 목록을 읽습니다. 키 근거: AddCartListOut.java:76, PsgDiscAddInfos.java:81,
    PsgDiscAddInfo.java:81,85. 누락·잘못된 선택 목록은 비웁니다."""
    data = _response_mapping(raw)
    return CartAddResponse(
        **_base_fields(data),
        discount_additions=_cart_discount_additions(data),
    )
