# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""상태 변경 응답을 :mod:`korail_mobile_api.mutation_models` 의 타입으로 옮깁니다.

예약 홀드, 결제, 할인카드 구매, 장바구니 추가와 7.0.6 환불 결과의 응답을
파싱합니다. 장바구니 추가는 예전에 봉투만 돌려준다고 적혀 있었으나, 응답
DTO 는 ``AddCartListOut.java:24-25`` 이고 그 자체 속성의 전선 키는
``:76-77`` 의 ``@SerialName("psgDiscAdd_infos")`` 입니다 — 지금은
:func:`parse_cart_add_response` 가 이것을 파싱합니다. 취소처럼 DAO 의 응답
타입이 맨 ``BaseResponse`` 인 라우트에는 여전히 전용 파서가 없습니다.

읽기 파서와 다른 점이 하나 있습니다. 여기서 나오는 값은 서버에 **이미 존재할 수
있는** 예약을 가리킵니다 — PNR, 발권창구번호, 결제 폼이 되울릴 job 일련번호,
정산 금액. 그래서 값의 표현 형태가 예상과 달라도 최대한 받아들입니다
(:func:`_optional_string`). 파싱 실패로 실제 예약을 놓치는 것이 이 패키지가 낼
수 있는 최악의 결과이기 때문입니다.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .mutation_models import (
    CartAddResponse,
    CartDiscountAddition,
    DiscountCardPurchaseResponse,
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
from .read_parsers import _additive_scalar_string, _nested_rows
from .read_parsers import _optional_scalar_string as _optional_string


def parse_refund_ticket_response(raw: Mapping[str, Any]) -> RefundTicketResponse:
    """``stlList``의 nullable 값과 정산 수단 코드를 보존합니다."""
    copied = _response_mapping(raw)
    rows = copied.get("stlList")
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL refund stlList must be a list")
    codes: list[str] = []
    for row in rows or ():
        row = _row(row, "refund settlement")
        code = row.get("stl_mns_cd")
        if not isinstance(code, str):
            raise KorailProtocolError("KORAIL refund stl_mns_cd is required")
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
    """Parse ``VerifyOnlineRefundsOut`` and the original ticket it validates."""
    copied = _response_mapping(raw)
    rows = copied.get("orgtkinfo_list", [])
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL station refund orgtkinfo_list must be a list")
    original_tickets: list[StationRefundOriginalTicket] = []
    for row in rows or ():
        row = _row(row, "station refund Orgtkinfo")
        pnr_no = _optional_string(row, "pnr_no", context="station refund Orgtkinfo")
        if not pnr_no:
            raise KorailProtocolError("KORAIL station refund Orgtkinfo.pnr_no is required")
        identity_fields = {
            attr: _optional_string(row, wire_key, context="station refund Orgtkinfo")
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
        received_amount=_optional_string(
            copied, "rcvd_amt", context="station refund verification"
        ),
        refund_fee=_optional_string(
            copied, "ret_fee", context="station refund verification"
        ),
        refund_amount=_optional_string(
            copied, "ret_amt", context="station refund verification"
        ),
        popup_message=_optional_string(
            copied, "poppMsg", context="station refund verification"
        ),
        result_message=_optional_string(
            copied, "strMsg", context="station refund verification"
        ),
        original_tickets=tuple(original_tickets),
        original_ticket_list_is_null=rows is None,
    )


def parse_station_refund_execution_response(
    raw: Mapping[str, Any],
) -> StationRefundExecutionResponse:
    """Parse ``ExecuteOnlineRefundsOut`` without dropping its refund type."""
    copied = _response_mapping(raw)
    return StationRefundExecutionResponse(
        **_base_fields(copied),
        refund_division_code=_optional_string(
            copied, "h_ret_dv_cd", context="station refund execution"
        ),
    )


_DIGITS_RE = re.compile(r"[0-9]+")


def _response_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    """A copy of the answer, checked once before any row.

    Whether ``raw`` is a JSON object is still worth checking here -- callers
    do reach these parsers directly, not only through the http layer -- but
    that is now the only envelope check this module makes. It used to also
    rebuild and re-check a :class:`~korail_mobile_api.models.BaseKorailResponse`
    from the same mapping just to read three fields off it; the fields are
    read straight off ``raw`` instead, the way ``read_parsers.py`` does.
    """
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
    """결제에 쓸 금액을 정합니다 — **앱 재현이 아니라 이 패키지의 선택입니다.**

    7.0.6 ``PayViewModel.initAmountData()``(``:11303-11307``)는 일반 분기에서
    ``h_tot_rcvd_amt`` 를 그대로 합산하고 좌석별로 재계산하지 않습니다. 좌석
    합을 1차 출처로 두는 것은 좌석 단위로 검산하려는 이 패키지의 판단이며,
    아래 정정 뒤에도 유지합니다 — 다만 "앱이 계산하는 방식대로" 라고 말하던
    예전 첫 문장은 사실이 아니었습니다.

    이 함수가 하는 일은 좌석별 ``h_rcvd_amt`` 를 더하고, 응답이 선언한
    ``h_tot_rcvd_amt`` 와 맞춰 보는 것입니다. 좌석 합을 **1차 출처**로 두는
    선택은 이 패키지의 것이며, 아래 근거 정정 뒤에도 그대로입니다.

    **인용 정정(2026-09-22).** 종전 독스트링은 ``PaymentActivity.G0()``
    (``:186-199``)의 좌석별 ``h_seat_prc + h_seat_fare`` 재계산을 근거로
    들고, ``h_tot_rcvd_amt`` 는 ``hidMnsStlAmt1`` 에 닿는 살아 있는 경로가
    없다고(``PaymentActivity.java:169``) 단언했습니다. ``PaymentActivity`` 는
    6.5.0 클래스이고 7.0.6 디컴파일에 없습니다. 7.0.6 에서 실제로 확인되는
    것은 반대에 가깝습니다:

    * ``analysis/jadx/sources/com/korail/talk/ui/screen/pay/PayViewModel.java:11303-11307``
      (``initAmountData()``, ``:11222``)이 ``ReservationOut.getHTotRcvdAmt()``
      를 예약 목록에 걸쳐 **그냥 더합니다**(여정변경 분기는 ``:11297-11301``
      에서 ``scnIndcAmt``). 즉 ``h_tot_rcvd_amt`` 는 7.0.6 에서 죽은 필드가
      아닙니다.
    * 좌석별 ``h_seat_prc``/``h_seat_fare`` 를 다시 더하는 코드는 7.0.6 에
      없습니다 — ``getHSeatPrc()``/``getHSeatFare()`` 호출자가 0건입니다.
    * 그 합계가 ``hidMnsStlAmt<N>`` 로 들어가는 마지막 한 걸음은
      ``analysis/jadx/sources/com/korail/talk/common/helper/PaymentMethodHelper.java:113``
      (``getCardRequest``, ``:89``)와 ``:211``(``getEasyRequest``, ``:147``)이
      **AlienGuard 로 보호된 키**로 ``Bundle`` 에서 값을 꺼내는 자리라
      정적으로 이어 붙을 수 없습니다 — 미출처입니다.

    그러므로 "좌석 합이 1차"라는 규칙은 앱 동작의 재현이 아니라 이 패키지의
    보수적 선택으로 읽어야 합니다. 좌석 행이 아예 없는 응답에서만
    ``h_tot_rcvd_amt`` 를 단독 출처로 씁니다.

    두 출처를 모두 읽을 수 있는데 값이 다르면 하나를 고르지 않고 거부합니다.
    둘 다 쓸 수 없으면 부분적인 숫자 대신 ``None`` 을 돌려줍니다.
    """
    declared = _optional_string(raw, "h_tot_rcvd_amt", context="reservation")
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
            raise KorailProtocolError(
                "KORAIL reservation seat_infos must be an object or null"
            )
        seat_rows = container.get("seat_info")
        if seat_rows is None:
            continue
        if not isinstance(seat_rows, list):
            raise KorailProtocolError(
                "KORAIL reservation seat_infos.seat_info must be a list or null"
            )
        for seat in seat_rows:
            seat = _row(seat, "reservation seat_info row")
            amount = _optional_string(
                seat,
                "h_rcvd_amt",
                context="reservation seat",
            )
            if amount is None or not _DIGITS_RE.fullmatch(amount.strip()):
                # One unreadable seat makes the whole sum wrong, so refuse the
                # whole sum rather than under-charge the settlement.
                return None
            try:
                value = int(amount)
            except ValueError:
                # Same refusal as an unreadable seat: a digit string past
                # Python's int-string conversion limit is unusable, not zero.
                return None
            seat_no = (
                _optional_string(seat, "h_seat_no", context="reservation seat")
                or ""
            )
            if value == 0 and not seat_no.strip():
                # 예약대기(``job_type=STANDBY``, ``h_msg_cd`` ``IRR000014``)는
                # 좌석이 아직 배정되지 않은 행을 하나 보냅니다 -- ``h_seat_no``
                # ``""``, ``h_srcar_no`` ``"0000"``, ``h_rcvd_amt`` 전부 0.
                # 그것은 정산 금액이 아니므로 합에 넣지 않습니다. 넣으면 합이
                # 0이 되어 ``h_tot_rcvd_amt`` 와 "모순" 으로 보이고, 아래
                # 예외가 올라가 :meth:`KorailClient.reserve` 의 폴백이 PNR 만
                # 남긴 홀드를 돌려줍니다 -- 전선에 값이 있는 12개 필드와
                # 여정 목록이 통째로 사라지고, 결제 폼이 그 홀드를 거부해
                # **확정된 예약대기를 결제할 수 없었습니다**(2026-09-22 재현:
                # ``h_wct_no='82002'``·``h_tot_rcvd_amt=42600`` 이 살아 있는데
                # ``window_no``/``received_amount`` 가 ``None``).
                #
                # 모순이 아니라는 근거: 같은 PNR 을 독립 경로
                # ``certification.ReservationList``
                # (:meth:`KorailClient.get_ticket_reservation_detail`)로 다시
                # 읽으면 좌석별 ``h_rcvd_amt`` 가 채워져 있고 그 합이
                # ``h_tot_rcvd_amt`` 와 같습니다. 즉 이 응답의 좌석 행만
                # 비어 있는 것이고 선언된 총액이 맞는 값입니다.
                continue
            summed += value
            seats_seen += 1
    if seats_seen == 0:
        # No seat rows to recompute from; the declared total is all there is.
        # Normalised the same way as the sum, for the same reason as below.
        return None if declared_int is None else str(declared_int)
    seat_total = str(summed)
    # Compare NUMERICALLY. Both of these arrive zero-padded, to different
    # widths, and the padding is not part of the number: a live 2026-07-27 hold
    # answered h_tot_rcvd_amt="0000000000042600" beside h_rcvd_amt="00000042600"
    # for one seat. Comparing the strings made 42,600 disagree with 42,600, and
    # every ordinary hold then failed to produce an amount at all -- which the
    # payment builder turns into a refusal to build the form. The synthetic
    # fixtures behind the offline tests were unpadded, so only a real response
    # could show this.
    if declared_int is not None and declared_int != summed:
        raise KorailProtocolError(
            "KORAIL reservation settlement amount is ambiguous: the seat rows "
            f"sum to {summed} but h_tot_rcvd_amt says {declared_int}. This "
            "library treats the per-seat sum as its primary source -- that is "
            "this package's policy, not a rule the app enforces -- so it "
            "refuses here rather than guess which amount to charge."
        )
    # 자리수 0 채움 없이 그대로 돌려줍니다. 예전에는 그 근거로
    # ``PaymentActivity`` 가 ``mReceivedAmount`` 를 int 로 계산한다고 적었지만,
    # 셋 다 7.0.6 에 없습니다 — ``PaymentActivity`` 도(6.5.0 클래스),
    # ``mReceivedAmount`` 도, 번호 붙은 ``hidMnsStlAmt1`` 도 평문 검색 0건이고
    # 존재하는 것은 번호 없는 ``hidMnsStlAmt``(``ReservationPaymentInStlInfo``,
    # ``PaymentMethod``) 뿐입니다(2026-09-23 확인). 이 파일 위쪽의 근거 정리와
    # 정면으로 어긋나 있었습니다: 거기서 이미 ``hidMnsStlAmt<N>`` 로 들어가는
    # 마지막 한 걸음이 AlienGuard 로 보호되어 **미출처**라고 적고 있습니다.
    # 따라서 자리수를 채우지 않는 것도 앱 동작의 재현이 아니라 이 패키지의
    # 선택으로 읽어야 합니다.
    return seat_total


def _base_fields(copied: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "h_msg_cd": copied.get("h_msg_cd"),
        "h_msg_txt": copied.get("h_msg_txt"),
        "str_result": copied.get("strResult"),
        "raw": copied,
    }


# The hold's scalar fields and their wire keys. received_amount and journeys
# are computed and stay out of it.
_RESERVATION_HOLD_FIELDS = {
    "pnr_no": "h_pnr_no",
    "journey_count": "h_jrny_cnt",
    "window_no": "h_wct_no",
    "temporary_job_sequence_1": "h_tmp_job_sqno1",
    "temporary_job_sequence_2": "h_tmp_job_sqno2",
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

# A reserved journey's fields, one jrny_info row each.
_RESERVATION_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "reservation_change_no": "h_rsv_chg_no",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
    "arrival_date": "h_arv_dt",
    "arrival_time": "h_arv_tm",
    "departure_station_code": "h_dpt_rs_stn_cd",
    "arrival_station_code": "h_arv_rs_stn_cd",
    "train_no": "h_trn_no",
}

# A paid ticket's coupon fields, one tk_coupon_info row each.
_PAYMENT_COUPON_FIELDS = {
    "certificate_password": "h_cert_pwd",
    "coupon_no": "h_coup_no",
    "management_close_date": "h_fdcert_mg_cls_dt",
    "management_start_date": "h_fdcert_mg_st_dt",
    "ticket_return_no": "h_tk_ret_no",
}

# ReservationPaymentOut's own scalar fields (ReservationPaymentOut.java:90).
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
}

# tk_infos.tk_info row fields (ReservationPaymentOutTkInfo.java).
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

# stl_infos.stl_info row fields (ReservationPaymentOutStlInfo.java). acnt_info
# (ReservationPaymentOutActInfo -- gateway transaction/error metadata, not
# bank-account data) is left in raw; it is not modeled here.
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

# tbl_seat_infos.tbl_seat_info row fields (ReservationPaymentOutTblSeatInfo.java).
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
    """``certification.TicketReservation`` 의 응답을 파싱합니다.

    성공한 홀드의 PNR·발권창구번호·여정 목록·정산 금액을 꺼냅니다.
    결제(:func:`~korail_mobile_api.mutation_payloads.build_card_payment_form`)와
    취소(:func:`~korail_mobile_api.mutation_payloads.build_unpaid_reservation_cancel_form`)
    가 되울릴 값이 전부 여기서 나옵니다.

    ``jrny_infos`` 는 없거나 ``null`` 이어도 되고 그때는 여정이 빈 튜플입니다.
    객체가 아니거나 ``jrny_info`` 가 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.

    **성공 여부는 판정하지 않습니다.** 봉투의 세 필드는 있으면 문자열이거나
    ``null`` 인지만 확인하고, 없어도 받으므로 실패한 홀드 응답도 그대로 돌아옵니다. 호출자가
    ``str_result``·``h_msg_cd`` 를 직접 봐야 합니다. 홀드가 실제로 걸렸는데
    파싱이 거부하면 놓을 수 없는 예약이 남기 때문입니다.
    """
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
            raise KorailProtocolError(
                "KORAIL reservation jrny_infos.jrny_info must be a list or null"
            )
    else:
        raise KorailProtocolError(
            "KORAIL reservation jrny_infos must be an object or null"
        )

    journeys: list[ReservationJourney] = []
    for value in journey_rows:
        row = dict(_row(value, "reservation journey"))
        journeys.append(
            ReservationJourney(
                **{
                    attr: _optional_string(row, wire_key, context="reservation journey")
                    for attr, wire_key in _RESERVATION_JOURNEY_FIELDS.items()
                },
                raw=row,
            )
        )

    return ReservationHoldResponse(
        # Spelled out rather than **_base_fields(copied): with the field map
        # also unpacked, the type checker cannot tell which one fills raw.
        h_msg_cd=copied.get("h_msg_cd"),
        h_msg_txt=copied.get("h_msg_txt"),
        str_result=copied.get("strResult"),
        raw=copied,
        **{
            attr: _optional_string(copied, wire_key, context="reservation")
            for attr, wire_key in _RESERVATION_HOLD_FIELDS.items()
        },
        received_amount=_received_amount(
            copied,
            [journey.raw for journey in journeys],
        ),
        journeys=tuple(journeys),
    )


def parse_reservation_payment_response(
    raw: Mapping[str, Any],
) -> ReservationPaymentResponse:
    """``payment.ReservationPayment`` 의 응답을 파싱합니다.

    ``tk_coupon_info`` 는 없거나 ``null`` 이어도 되고 그때는 쿠폰이 빈 튜플입니다.
    리스트가 아니면 :class:`~korail_mobile_api.errors.KorailProtocolError` 입니다.
    ``tk_infos``/``stl_infos``/``tbl_seat_infos`` 는 ``{"tk_info": [...]}`` 처럼
    바깥 객체 하나가 안쪽 리스트 하나를 감싼 모양이고 (:func:`_nested_rows`),
    셋 다 없거나 ``null`` 이면 빈 튜플입니다.

    이 세 목록을 타입 필드로 파싱하는 것은 기능 문제(결제 승인번호·예약번호·
    금액이 ``.raw`` 에만 있던 문제)와 보안 문제(``h_tk_ret_pwd``·
    ``h_take_name``·``h_disc_card_no``·``h_xpoint_apv_no`` 같은 민감 필드가
    ``.raw`` 를 통해 redaction 을 우회하던 문제)를 동시에 닫습니다 — 두 문제
    모두 같은 파서가 이 세 목록을 건너뛰던 것이 원인이었습니다.

    홀드 파서와 마찬가지로 성공 여부는 판정하지 않습니다. 결제가 서버에서 이미
    이뤄졌을 수 있으므로 응답을 버리지 않습니다.
    """
    copied = _response_mapping(raw)
    value = copied.get("tk_coupon_info")
    if value is None:
        rows: list[Any] = []
    elif isinstance(value, list):
        rows = value
    else:
        raise KorailProtocolError(
            "KORAIL payment tk_coupon_info must be a list or null"
        )

    coupons: list[ReservationPaymentCoupon] = []
    for value in rows:
        row = dict(_row(value, "payment coupon"))
        coupons.append(
            ReservationPaymentCoupon(
                **{
                    attr: _optional_string(row, wire_key, context="payment coupon")
                    for attr, wire_key in _PAYMENT_COUPON_FIELDS.items()
                },
                raw=row,
            )
        )

    tickets: list[ReservationPaymentTicket] = []
    for value in _nested_rows(copied, "tk_infos", "tk_info", "payment ticket"):
        row = dict(_row(value, "payment ticket"))
        tickets.append(
            ReservationPaymentTicket(
                **{
                    attr: _optional_string(row, wire_key, context="payment ticket")
                    for attr, wire_key in _RESERVATION_PAYMENT_TICKET_FIELDS.items()
                },
                raw=row,
            )
        )

    settlements: list[ReservationPaymentSettlement] = []
    for value in _nested_rows(copied, "stl_infos", "stl_info", "payment settlement"):
        row = dict(_row(value, "payment settlement"))
        settlements.append(
            ReservationPaymentSettlement(
                **{
                    attr: _optional_string(row, wire_key, context="payment settlement")
                    for attr, wire_key in _RESERVATION_PAYMENT_SETTLEMENT_FIELDS.items()
                },
                raw=row,
            )
        )

    table_seats: list[ReservationPaymentTableSeat] = []
    for value in _nested_rows(
        copied, "tbl_seat_infos", "tbl_seat_info", "payment table seat"
    ):
        row = dict(_row(value, "payment table seat"))
        table_seats.append(
            ReservationPaymentTableSeat(
                **{
                    attr: _optional_string(row, wire_key, context="payment table seat")
                    for attr, wire_key in _RESERVATION_PAYMENT_TABLE_SEAT_FIELDS.items()
                },
                raw=row,
            )
        )

    return ReservationPaymentResponse(
        **_base_fields(copied),
        image_ticket_flag=_optional_string(
            copied,
            "h_im_flg",
            context="payment",
        ),
        **{
            attr: _optional_string(copied, wire_key, context="payment")
            for attr, wire_key in _RESERVATION_PAYMENT_FIELDS.items()
        },
        coupons=tuple(coupons),
        tickets=tuple(tickets),
        settlements=tuple(settlements),
        table_seats=tuple(table_seats),
    )


_DISCOUNT_CARD_PURCHASE_FIELDS = {
    "lump_settlement_target_no": "lumpStlTgtNo",
    "discount_card_settlement_target_no": "dcntCrdStlTgtNo",
    "received_amount": "rcvdAmt",
    "stx_amount": "stxAmt",
    "taxt_supply_amount": "taxtSplAmt",
    "usable_trip_count": "usePsbTno",
    "validity_start_date": "vlidTrmStDt",
    "validity_end_date": "vlidTrmClsDt",
    # NCardInfoOut.java:30 -- distinct from dcntCrdStlTgtNo. No @SerialName
    # is declared, same as its siblings above, so the bare Kotlin property
    # name is the wire key (established pattern, not a new guess).
    "registered_card_kind_management_no": "dcntCrdKndMgNo",
}


def parse_discount_card_purchase_response(
    raw: Mapping[str, Any],
) -> DiscountCardPurchaseResponse:
    """``research.dcntCrdInfo.do`` 의 응답을 파싱합니다.

    7.0.6 ``NCardInfoOut.java:30-38`` 이 선언하는 자체 속성은 아홉입니다 --
    ``dcntCrdKndMgNo``/``dcntCrdStlTgtNo``/``lumpStlTgtNo``/``rcvdAmt``/
    ``stxAmt``/``taxtSplAmt``/``usePsbTno``/``vlidTrmClsDt``/``vlidTrmStDt``
    (``strResult``/``hMsgCd``/``_hMsgTxt`` 는 상위 ``CommonOut`` 것입니다).
    serializer descriptor 문자열이 보호돼 있어 파서는 Kotlin 속성명을 전선
    키로 씁니다.

    **인용 정정(2026-09-23).** 종전 독스트링은 범위를 ``:30-36`` 으로 적고
    속성이 일곱이라고 했습니다. 그 범위가 ``vlidTrmClsDt``(``:37``) 와
    ``vlidTrmStDt``(``:38``) 를 잘라내는 바람에 둘이 목록에서 빠진 것이고,
    실제 선언은 ``:30-38`` 의 아홉 줄입니다. **모델링 누락이 아닙니다** --
    위 :data:`_DISCOUNT_CARD_PURCHASE_FIELDS` 가 두 날짜를 각각
    ``validity_end_date``/``validity_start_date`` 로 이미 파싱하고,
    :class:`~korail_mobile_api.mutation_models.DiscountCardPurchaseResponse`
    에도 같은 이름의 필드가 있습니다. 틀렸던 것은 산문의 숫자와 줄 범위뿐이며,
    이 문단은 뒤에 읽는 사람이 이것을 커버리지 구멍으로 오해하지 않도록
    남겨 둡니다.

    예전에 여기 적혀 있던 ``mStationInfo``/``mUserNames`` 는 **이 DTO 와 아무
    관계가 없습니다.** 그 둘은 7.0.6 의 ``NCardInfoOut`` 어디에도 없고, 근거로
    달려 있던 ``:167-173`` 은 금액·사용횟수 속성의 직렬화 구간입니다. 잘못된
    설명이라 지웁니다.

    **라이브 미검증.** 전송된 적이 없으므로 관측된 적도 없습니다.
    """
    data = _response_mapping(raw)
    return DiscountCardPurchaseResponse(
        h_msg_cd=data.get("h_msg_cd"),
        h_msg_txt=data.get("h_msg_txt"),
        str_result=data.get("strResult"),
        raw=data,
        **{
            attribute: _optional_string(
                data,
                wire_name,
                context="discount card purchase",
            )
            for attribute, wire_name in _DISCOUNT_CARD_PURCHASE_FIELDS.items()
        },
    )


_CART_DISCOUNT_ADDITION_FIELDS = {
    "passenger_sequence_no": "h_psg_sqno",
    "duty_reference_recognition_division_code": "h_duty_ref_rcgn_ps_dv_cd",
}


def _cart_discount_additions(
    data: Mapping[str, Any],
) -> tuple[CartDiscountAddition, ...]:
    """``psgDiscAdd_infos`` 를 **관대하게** 읽습니다.

    이 블록은 통째로 나중에 덧붙였습니다 — 예전 버전은 이 키를 아예 들여다보지
    않고 봉투만 돌려줬으므로, 키가 어떤 모양으로 오든 파싱은 **성공** 했습니다.
    라이브 캡처도 없어 서버가 실제로 무엇을 보내는지 모릅니다. 그러니 모양이
    어긋난다고 응답 전체를 버리면, 필드를 덧붙인 일이 라이브러리가 받아들이는
    응답의 폭을 좁히는 변경이 됩니다(read_parsers 의
    ``_additive_scalar_string`` 과 같은 이유).

    그래서: 바깥 객체나 리스트의 모양이 다르면 빈 튜플, 객체가 아닌 행은 건너
    뛰고, 행 안의 두 필드는 문자열·정수가 아니면 ``None`` 입니다. 무엇이 왔든
    :attr:`CartAddResponse.raw` 에 원본이 남습니다.
    """
    try:
        rows = _nested_rows(data, "psgDiscAdd_infos", "psgDiscAdd_info", "cart add")
    except KorailProtocolError:
        return ()
    additions = []
    for item in rows:
        if not isinstance(item, Mapping):
            continue
        additions.append(
            CartDiscountAddition(
                raw=item,
                **{
                    attribute: _additive_scalar_string(
                        item, wire_name, "cart add discount row"
                    )
                    for attribute, wire_name in _CART_DISCOUNT_ADDITION_FIELDS.items()
                },
            )
        )
    return tuple(additions)


def parse_cart_add_response(raw: Mapping[str, Any]) -> CartAddResponse:
    """``cart.addCartList`` 의 응답을 파싱합니다.

    봉투 밖의 자체 속성은 ``psgDiscAdd_infos`` 하나이고
    (``AddCartListOut.java:76`` 의 ``@SerialName``), 그 안에
    ``psgDiscAdd_info`` 리스트가 있습니다(``PsgDiscAddInfos.java:81``).
    행의 두 필드는 ``PsgDiscAddInfo.java:85``(``h_psg_sqno``)와
    ``:81``(``h_duty_ref_rcgn_ps_dv_cd``)입니다.

    예전에는 이 라우트가 봉투만 돌려준다고 보고
    :class:`~korail_mobile_api.models.BaseKorailResponse` 를 그대로
    넘겼습니다. 위 세 DTO 가 그렇지 않다고 말합니다.

    **라이브 미검증** — 실제 응답을 받아 본 적이 없습니다. 행이 없거나
    바깥 객체가 통째로 없으면 빈 튜플이고, 모양이 어긋나도 봉투는 그대로
    돌려줍니다(:func:`_cart_discount_additions`).
    """
    data = _response_mapping(raw)
    return CartAddResponse(
        h_msg_cd=data.get("h_msg_cd"),
        h_msg_txt=data.get("h_msg_txt"),
        str_result=data.get("strResult"),
        raw=data,
        discount_additions=_cart_discount_additions(data),
    )


