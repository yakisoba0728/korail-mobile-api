"""상태 변경 응답을 :mod:`korail_mobile_api.mutation_models` 의 타입으로 옮긴다.

예약 홀드, 결제, 할인카드 구매의 응답 셋을 파싱한다. 취소·환불·장바구니
추가처럼 DAO 의 응답 타입이 맨 ``BaseResponse`` 인 라우트는 전용 모델이
없어 여기 파서도 없다.

읽기 파서와 다른 점이 하나 있다. 여기서 나오는 값은 서버에 **이미 존재할 수
있는** 예약을 가리킨다 — PNR, 발권창구번호, 결제 폼이 되울릴 job 일련번호,
정산 금액. 그래서 값의 표현 형태가 예상과 달라도 최대한 받아들인다
(:func:`_optional_string`). 파싱 실패로 실제 예약을 놓치는 것이 이 패키지가
낼 수 있는 최악의 결과다.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse
from .mutation_models import (
    DiscountCardPurchaseResponse,
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
)


_DIGITS_RE = re.compile(r"[0-9]+")


def _response_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise KorailProtocolError("KORAIL response must be a JSON object")
    copied = dict(raw)
    BaseKorailResponse.from_raw(copied)
    return copied


def _optional_string(
    row: Mapping[str, Any],
    key: str,
    *,
    context: str,
) -> str | None:
    """스칼라 필드 하나. JSON 문자열로 와도 JSON 숫자로 와도 받는다.

    KORAIL 은 APK 가 자바 ``String`` 으로 선언한 필드를 마음대로 둘 중 하나로
    보내고, Gson 의 ``JsonReader.nextString()`` 이 숫자를 문자열로 강제 변환하기
    때문에 앱은 개의치 않는다. 예약 응답은 여정 수를 따옴표로 감싸고 0 까지
    채워 보내는데(``h_jrny_cnt="0001"``) 예약 이력은 같은 필드를 JSON 정수
    ``1`` 로 보낸다. 홀드를 이력에서 다시 읽는 것이 PNR 을 잃었을 때의 복구
    경로이므로 둘 다 파싱돼야 한다.

    이것이 읽기 파서에서보다 여기서 더 중요하다. 아래의 모든 값이 서버에 이미
    존재할 수 있는 홀드를 가리킨다. 따옴표가 없다고 거부하면 실제 예약이
    고아가 된다. 그래서 폼 빌더가 기대하는 문자열로 정규화하고, 정말로 다른
    모양인 것 — ``bool``, ``float``, 리스트, 객체 — 만 계속 거부한다.
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
    """앱이 정산할 금액을 앱이 계산하는 방식대로 복원한다.

    ``PaymentActivity.G0()``(``:186-199``)은 좌석마다
    ``h_seat_prc + h_seat_fare`` 를 ``totalAmount`` 에,
    ``(h_seat_prc + h_seat_fare) - h_rcvd_amt`` 를 ``discountAmount`` 에 더한 뒤
    ``mReceivedAmount = totalAmount - discountAmount`` 로 둔다. 대수적으로 좌석별
    ``h_rcvd_amt`` 의 단순 합이다.

    여기서도 좌석 합이 **1차 출처**이며 앱과 같다. ``h_tot_rcvd_amt`` 키가
    지름길처럼 보이고 ``BasketTicketActivity.java:637-641`` 이 그 값을 결제
    번들에 넣기는 하지만, 같은 번들에 예약 응답도 넣기 때문에
    ``PaymentActivity.java:169`` 가 다시 계산하는 가지를 타고 그 엑스트라는 읽히지
    않는다. APK 안에 ``h_tot_rcvd_amt`` 가 ``hidMnsStlAmt1`` 에 닿는 살아 있는
    경로가 없다. 두 값은 부가상품·수수료·마일리지가 좌석 행과 다른 시점에
    반영되는 순간 갈라진다.

    두 출처를 모두 읽을 수 있는데 값이 다르면 하나를 고르지 않고 거부한다.
    금액이 모호한 정산이야말로 전선에 올라서는 안 되는 것이다. 좌석 행이 아예
    없는 응답에서는 ``h_tot_rcvd_amt`` 가 대체 출처로 남는다.

    둘 다 쓸 수 없으면 부분적인 숫자 대신 ``None`` 을 돌려준다.
    """
    declared = _optional_string(raw, "h_tot_rcvd_amt", context="reservation")
    if declared is not None:
        declared = declared.strip()
        if not _DIGITS_RE.fullmatch(declared):
            declared = None

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
            if not isinstance(seat, Mapping):
                raise KorailProtocolError(
                    "KORAIL reservation seat_info row must be an object"
                )
            amount = _optional_string(
                seat,
                "h_rcvd_amt",
                context="reservation seat",
            )
            if amount is None or not _DIGITS_RE.fullmatch(amount.strip()):
                # One unreadable seat makes the whole sum wrong, so refuse the
                # whole sum rather than under-charge the settlement.
                return None
            summed += int(amount)
            seats_seen += 1
    if seats_seen == 0:
        # No seat rows to recompute from; the declared total is all there is.
        # Normalised the same way as the sum, for the same reason as below.
        return None if declared is None else str(int(declared))
    seat_total = str(summed)
    # Compare NUMERICALLY. Both of these arrive zero-padded, to different
    # widths, and the padding is not part of the number: a live 2026-07-27 hold
    # answered h_tot_rcvd_amt="0000000000042600" beside h_rcvd_amt="00000042600"
    # for one seat. Comparing the strings made 42,600 disagree with 42,600, and
    # every ordinary hold then failed to produce an amount at all -- which the
    # payment builder turns into a refusal to build the form. The synthetic
    # fixtures behind the offline tests were unpadded, so only a real response
    # could show this.
    if declared is not None and int(declared) != summed:
        raise KorailProtocolError(
            "KORAIL reservation settlement amount is ambiguous: the seat rows "
            f"sum to {summed} but h_tot_rcvd_amt says {int(declared)}. The app "
            "settles the seat sum; refusing rather than guessing which one to "
            "charge."
        )
    # Unpadded, because that is what the app settles: PaymentActivity computes
    # mReceivedAmount as an int and hands the decimal form to hidMnsStlAmt1.
    return seat_total


def _base_fields(raw: dict[str, Any]) -> dict[str, Any]:
    base = BaseKorailResponse.from_raw(raw)
    return {
        "h_msg_cd": base.h_msg_cd,
        "h_msg_txt": base.h_msg_txt,
        "str_result": base.str_result,
        "raw": raw,
    }


def parse_reservation_hold_response(
    raw: Mapping[str, Any],
) -> ReservationHoldResponse:
    """``certification.TicketReservation`` 의 응답을 파싱한다.

    성공한 홀드의 PNR·발권창구번호·여정 목록·정산 금액을 꺼내
    :class:`~korail_mobile_api.mutation_models.ReservationHoldResponse` 로 만든다.
    결제(:func:`~korail_mobile_api.mutation_payloads.build_card_payment_form`)와
    취소(:func:`~korail_mobile_api.mutation_payloads.build_unpaid_reservation_cancel_form`)
    가 되울릴 값이 전부 여기서 나온다.

    ``jrny_infos`` 는 없거나 ``null`` 이어도 되고 그때는 여정이 빈 튜플이다.
    객체가 아니거나 ``jrny_info`` 가 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 다.

    **성공 여부는 판정하지 않는다.** 봉투는 세 필드가 있고 문자열이거나
    ``null`` 인지만 확인하므로, 실패한 홀드 응답도 그대로 돌아온다. 호출자가
    ``str_result``·``h_msg_cd`` 를 직접 봐야 한다. 홀드가 실제로 걸렸는데
    파싱이 거부하면 놓을 수 없는 예약이 남기 때문이다.
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
        if not isinstance(value, Mapping):
            raise KorailProtocolError(
                "KORAIL reservation journey must be an object"
            )
        row = dict(value)
        journeys.append(
            ReservationJourney(
                journey_sequence=_optional_string(
                    row,
                    "h_jrny_sqno",
                    context="reservation journey",
                ),
                reservation_change_no=_optional_string(
                    row,
                    "h_rsv_chg_no",
                    context="reservation journey",
                ),
                departure_date=_optional_string(
                    row,
                    "h_dpt_dt",
                    context="reservation journey",
                ),
                departure_time=_optional_string(
                    row,
                    "h_dpt_tm",
                    context="reservation journey",
                ),
                arrival_time=_optional_string(
                    row,
                    "h_arv_tm",
                    context="reservation journey",
                ),
                departure_station_code=_optional_string(
                    row,
                    "h_dpt_rs_stn_cd",
                    context="reservation journey",
                ),
                arrival_station_code=_optional_string(
                    row,
                    "h_arv_rs_stn_cd",
                    context="reservation journey",
                ),
                train_no=_optional_string(
                    row,
                    "h_trn_no",
                    context="reservation journey",
                ),
                raw=row,
            )
        )

    return ReservationHoldResponse(
        **_base_fields(copied),
        pnr_no=_optional_string(copied, "h_pnr_no", context="reservation"),
        journey_count=_optional_string(
            copied,
            "h_jrny_cnt",
            context="reservation",
        ),
        window_no=_optional_string(copied, "h_wct_no", context="reservation"),
        temporary_job_sequence_1=_optional_string(
            copied,
            "h_tmp_job_sqno1",
            context="reservation",
        ),
        temporary_job_sequence_2=_optional_string(
            copied,
            "h_tmp_job_sqno2",
            context="reservation",
        ),
        payment_flag=_optional_string(
            copied,
            "h_payment_flg",
            context="reservation",
        ),
        payment_message=_optional_string(
            copied,
            "h_payment_msg",
            context="reservation",
        ),
        payment_deadline_message=_optional_string(
            copied,
            "h_pay_limit_msg",
            context="reservation",
        ),
        payment_deadline_notice=_optional_string(
            copied,
            "h_ntisu_lmt",
            context="reservation",
        ),
        payment_deadline_date=_optional_string(
            copied,
            "h_ntisu_lmt_dt",
            context="reservation",
        ),
        payment_deadline_time=_optional_string(
            copied,
            "h_ntisu_lmt_tm",
            context="reservation",
        ),
        total_fare=_optional_string(
            copied,
            "h_tot_fare",
            context="reservation",
        ),
        total_price=_optional_string(
            copied,
            "h_tot_prc",
            context="reservation",
        ),
        received_amount=_received_amount(
            copied,
            [journey.raw for journey in journeys],
        ),
        journeys=tuple(journeys),
    )


def parse_reservation_payment_response(
    raw: Mapping[str, Any],
) -> ReservationPaymentResponse:
    """``payment.ReservationPayment`` 의 응답을 파싱한다.

    :class:`~korail_mobile_api.mutation_models.ReservationPaymentResponse` 를
    만든다. ``tk_coupon_info`` 는 없거나 ``null`` 이어도 되고 그때는 쿠폰이 빈
    튜플이다. 리스트가 아니면
    :class:`~korail_mobile_api.errors.KorailProtocolError` 다.

    홀드 파서와 마찬가지로 성공 여부는 판정하지 않는다. 결제가 서버에서 이미
    이뤄졌을 수 있으므로 응답을 버리지 않는다.
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
        if not isinstance(value, Mapping):
            raise KorailProtocolError(
                "KORAIL payment coupon must be an object"
            )
        row = dict(value)
        coupons.append(
            ReservationPaymentCoupon(
                certificate_password=_optional_string(
                    row,
                    "h_cert_pwd",
                    context="payment coupon",
                ),
                coupon_no=_optional_string(
                    row,
                    "h_coup_no",
                    context="payment coupon",
                ),
                management_close_date=_optional_string(
                    row,
                    "h_fdcert_mg_cls_dt",
                    context="payment coupon",
                ),
                management_start_date=_optional_string(
                    row,
                    "h_fdcert_mg_st_dt",
                    context="payment coupon",
                ),
                ticket_return_no=_optional_string(
                    row,
                    "h_tk_ret_no",
                    context="payment coupon",
                ),
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
        coupons=tuple(coupons),
    )


_DISCOUNT_CARD_PURCHASE_FIELDS = {
    "lump_settlement_target_no": "lumpStlTgtNo",
    "received_amount": "rcvdAmt",
    "usable_trip_count": "usePsbTno",
    "validity_start_date": "vlidTrmStDt",
    "validity_end_date": "vlidTrmClsDt",
}


def parse_discount_card_purchase_response(
    raw: Mapping[str, Any],
) -> DiscountCardPurchaseResponse:
    """``research.dcntCrdInfo.do`` 의 응답을 파싱한다.

    ``NCardReservationDao.NCardReservationResponse``
    (``dao/research/NCardReservationDao.java:127-174``). ``mStationInfo`` 와
    ``mUserNames`` 는 모델에 없다. 앱이 호출 뒤 지역적으로 채우는 값이고
    (``:167-173``) 서버는 보내지 않는다.

    **라이브 미검증.** 전송된 적이 없으므로 관측된 적도 없다.
    """
    data = _response_mapping(raw)
    base = BaseKorailResponse.from_raw(data)
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


