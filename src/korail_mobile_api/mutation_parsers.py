# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""상태 변경 응답을 :mod:`korail_mobile_api.mutation_models` 의 타입으로 옮깁니다.

예약 홀드, 결제, 할인카드 구매와 7.0.6 환불 결과의 응답을 파싱합니다.
취소·장바구니 추가처럼 DAO 의 응답 타입이 맨 ``BaseResponse`` 인 라우트에는
전용 파서가 없습니다.

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
from .models import BaseKorailResponse
from .mutation_models import (
    CashReceiptApprovalItem,
    CashReceiptIssueResponse,
    DiscountCardPurchaseResponse,
    RefundTicketResponse,
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
    StationRefundExecutionResponse,
    StationRefundOriginalTicket,
    StationRefundVerificationResponse,
)


def parse_refund_ticket_response(raw: Mapping[str, Any]) -> RefundTicketResponse:
    """필수 키 ``stlList``의 nullable 값과 정산 수단 코드를 보존합니다."""
    copied, base = _response_mapping(raw)
    if "stlList" not in copied:
        raise KorailProtocolError("KORAIL refund stlList is required")
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
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=copied,
        settlement_method_codes=tuple(codes),
        settlement_list_is_null=rows is None,
    )


_CASH_RECEIPT_APPROVAL_FIELDS = {
    "job_division_code": "jobDvCd",
    "receipt_no": "rcptNo",
    "approval_date": "apvDt",
    "cash_receipt_approval_no": "cashRcetApvNo",
    "approved_amount": "totApvAmt",
    "approval_processed_at": "apvPrsDttm",
    "normal_processing_flag": "nmlPrsFlg",
    "response_message_code": "rspMsgCd",
    "short_message_content": "shrtMsgCont",
    "sale_date": "saleDt",
    "sale_window_no": "saleWctNo",
    "sale_sequence": "saleSqno",
}


def parse_cash_receipt_issue_response(
    raw: Mapping[str, Any],
) -> CashReceiptIssueResponse:
    """Parse the unprotected ``CashReceiptIssueOut`` and ``ApvItem`` fields.

    The APK defaults an omitted ``apvList`` to an empty list, but the field is
    nullable. Present lists must contain objects; approval identifiers remain
    hidden from ``repr``.
    """
    copied, base = _response_mapping(raw)
    rows = copied.get("apvList", [])
    if rows is not None and not isinstance(rows, list):
        raise KorailProtocolError("KORAIL cash receipt apvList must be a list")
    approvals: list[CashReceiptApprovalItem] = []
    for row in rows or ():
        row = _row(row, "cash receipt ApvItem")
        approval_fields = {
            attr: _optional_string(row, wire_key, context="cash receipt ApvItem")
            for attr, wire_key in _CASH_RECEIPT_APPROVAL_FIELDS.items()
        }
        approvals.append(CashReceiptApprovalItem(**approval_fields, raw=dict(row)))
    return CashReceiptIssueResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=copied,
        transaction_division_code=_optional_string(
            copied, "cashRcetTxnDvCd", context="cash receipt issue"
        ),
        authentication_method_code=_optional_string(
            copied, "cashRcetAthnMtdCd", context="cash receipt issue"
        ),
        authentication_recognition_no=_optional_string(
            copied, "athnDmnRcgnNo", context="cash receipt issue"
        ),
        total_approved_amount=_optional_string(
            copied, "totApvAmt", context="cash receipt issue"
        ),
        approvals=tuple(approvals),
        approval_list_is_null=rows is None,
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
    copied, base = _response_mapping(raw)
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
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=copied,
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
    copied, base = _response_mapping(raw)
    return StationRefundExecutionResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=copied,
        refund_division_code=_optional_string(
            copied, "h_ret_dv_cd", context="station refund execution"
        ),
    )


_DIGITS_RE = re.compile(r"[0-9]+")


def _response_mapping(
    raw: Mapping[str, Any],
) -> tuple[dict[str, Any], BaseKorailResponse]:
    """A copy of the answer and its envelope, checked before anything else.

    Every parser here calls this first, so a bad envelope is reported before
    any row, and the envelope is not checked a second time.
    """
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    copied = dict(raw)
    return copied, BaseKorailResponse.from_raw(copied)


def _row(value: object, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise KorailProtocolError(f"KORAIL {context} must be an object")
    return value


def _optional_string(
    row: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> str | None:
    """스칼라 필드 하나. JSON 문자열로 와도 JSON 숫자로 와도 받습니다.

    KORAIL 은 APK 가 자바 ``String`` 으로 선언한 필드를 둘 중 아무 쪽으로나
    보냅니다. 예약 응답은 여정 수를 ``h_jrny_cnt="0001"`` 로 보내는데 예약 이력은
    같은 필드를 JSON 정수 ``1`` 로 보냅니다. 홀드를 이력에서 다시 읽는 것이 PNR 을
    잃었을 때의 복구 경로이므로 둘 다 파싱돼야 합니다.

    따옴표가 없다고 거부하면 실제 예약이 고아가 되므로, 폼 빌더가 기대하는
    문자열로 정규화하고 정말로 다른 모양인 것 — ``bool``, ``float``, 리스트,
    객체 — 만 계속 거부합니다.
    """
    value = row.get(key)
    if value is None or isinstance(value, str):
        return value
    # `type(...) is int` on purpose: bool is an int subclass, and True is not a
    # number KORAIL sends for any of these.
    if type(value) is int:
        return str(value)
    raise KorailProtocolError(
        f"KORAIL {context} field {key} must be a string, an integer, or null"
    )


def _received_amount(
    raw: Mapping[str, Any],
    journey_rows: list[Mapping[str, Any]],
) -> str | None:
    """앱이 정산할 금액을 앱이 계산하는 방식대로 복원합니다.

    ``PaymentActivity.G0()``(``:186-199``)은 좌석마다
    ``h_seat_prc + h_seat_fare`` 를 ``totalAmount`` 에,
    ``(h_seat_prc + h_seat_fare) - h_rcvd_amt`` 를 ``discountAmount`` 에 더한 뒤
    ``mReceivedAmount = totalAmount - discountAmount`` 로 둡니다. 대수적으로
    좌석별 ``h_rcvd_amt`` 의 단순 합입니다.

    그래서 여기서도 좌석 합이 **1차 출처**입니다. ``h_tot_rcvd_amt`` 는 지름길로
    보이지만 APK 안에 그 값이 ``hidMnsStlAmt1`` 에 닿는 살아 있는 경로가 없습니다
    (``PaymentActivity.java:169`` 가 다시 계산하는 가지를 탑니다). 좌석 행이 아예
    없는 응답에서만 대체 출처로 씁니다.

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
                summed += int(amount)
            except ValueError:
                # Same refusal as an unreadable seat: a digit string past
                # Python's int-string conversion limit is unusable, not zero.
                return None
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
            f"sum to {summed} but h_tot_rcvd_amt says {declared_int}. The app "
            "settles the seat sum; refusing rather than guessing which one to "
            "charge."
        )
    # Unpadded, because that is what the app settles: PaymentActivity computes
    # mReceivedAmount as an int and hands the decimal form to hidMnsStlAmt1.
    return seat_total


def _base_fields(base: BaseKorailResponse) -> dict[str, Any]:
    return {
        "h_msg_cd": base.h_msg_cd,
        "h_msg_txt": base.h_msg_txt,
        "str_result": base.str_result,
        "raw": base.raw,
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
}

# A reserved journey's fields, one jrny_info row each.
_RESERVATION_JOURNEY_FIELDS = {
    "journey_sequence": "h_jrny_sqno",
    "reservation_change_no": "h_rsv_chg_no",
    "departure_date": "h_dpt_dt",
    "departure_time": "h_dpt_tm",
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
    copied, base = _response_mapping(raw)
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
        # Spelled out rather than **_base_fields(base): with the field map
        # also unpacked, the type checker cannot tell which one fills raw.
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=base.raw,
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

    홀드 파서와 마찬가지로 성공 여부는 판정하지 않습니다. 결제가 서버에서 이미
    이뤄졌을 수 있으므로 응답을 버리지 않습니다.
    """
    copied, base = _response_mapping(raw)
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

    return ReservationPaymentResponse(
        **_base_fields(base),
        image_ticket_flag=_optional_string(
            copied,
            "h_im_flg",
            context="payment",
        ),
        coupons=tuple(coupons),
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
}


def parse_discount_card_purchase_response(
    raw: Mapping[str, Any],
) -> DiscountCardPurchaseResponse:
    """``research.dcntCrdInfo.do`` 의 응답을 파싱합니다.

    7.0.6 ``NCardInfoOut.java:31-39,59-89`` declares the settlement and tax
    fields. Its serializer descriptor strings are protected, so the parser
    uses the Kotlin property names, as it already does for ``rcvdAmt`` and
    ``lumpStlTgtNo``. ``mStationInfo`` 와
    ``mUserNames`` 는 모델에 없습니다. 앱이 호출 뒤 지역적으로 채우는 값이고
    (``:167-173``) 서버는 보내지 않습니다.

    **라이브 미검증.** 전송된 적이 없으므로 관측된 적도 없습니다.
    """
    data, base = _response_mapping(raw)
    return DiscountCardPurchaseResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
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


