from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse
from .mutation_models import (
    CommuterPassReservation,
    CommuterPassReservationResponse,
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
    """A scalar field, accepted as a JSON string OR a JSON number.

    KORAIL sends whichever it likes for a field the APK declares as a Java
    ``String``, and the app is indifferent because Gson's
    ``JsonReader.nextString()`` coerces a number into its string form. The
    reserve response quotes the journey count and zero-pads it
    (``h_jrny_cnt="0001"``); the reservation history sends the same field as the
    JSON integer ``1``. Both must parse, because reading a hold back out of the
    history is the recovery path when a PNR has been lost.

    This matters more here than on a read parser. Every value below identifies a
    hold that may already EXIST on the server -- the PNR, the window number, the
    job sequences the payment form echoes, the amount it settles. Refusing one
    because it arrived unquoted strands a real reservation, which is the single
    worst outcome this package can produce. So normalise to the string the form
    builders expect, and keep rejecting only what is genuinely a different
    shape: a bool, a float, a list or an object.
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
    """Recover the amount the app would settle, the way the app computes it.

    ``PaymentActivity.G0()`` (``:186-199``) sums ``h_seat_prc + h_seat_fare``
    per seat into ``totalAmount`` and ``(h_seat_prc + h_seat_fare) - h_rcvd_amt``
    into ``discountAmount``, then sets ``mReceivedAmount = totalAmount -
    discountAmount`` — algebraically the plain sum of the per-seat
    ``h_rcvd_amt``. ``BasketTicketActivity.java:638`` takes the identical figure
    straight off the response's ``h_tot_rcvd_amt``
    (``ReservationResponse.java:33``), so prefer that key when it is present and
    fall back to the seat rows when it is not.

    Returns ``None`` rather than a partial figure when neither source is usable:
    a wrong settlement amount must never reach the wire.
    """
    total = _optional_string(raw, "h_tot_rcvd_amt", context="reservation")
    if total is not None and _DIGITS_RE.fullmatch(total.strip()):
        return total.strip()

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
        return None
    return str(summed)


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
    """Parse ``research.dcntCrdInfo.do``'s reply.

    ``NCardReservationDao.NCardReservationResponse``
    (``dao/research/NCardReservationDao.java:127-174``). ``mStationInfo`` and
    ``mUserNames`` are absent from the model because the app writes them
    locally after the call (``:167-173``) and the server never sends them.

    **NOT LIVE-VERIFIED.** Never sent, so never observed.
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


# The typed slice of ``main_info`` this package names. Every key the app's
# reflection sweeps into the payment map is still available through
# ``CommuterPassReservation.raw``; these are the ones a caller acts on.
_COMMUTER_PASS_RESERVATION_FIELDS = {
    "received_amount": "h_rcvd_amt",
    "received_price": "h_rcvd_prc",
    "received_fare": "h_rcvd_fare",
    "one_time_received_amount": "h_otm_rcvd_amt",
    "change_management_no": "h_chg_mg_no",
    "change_management_division_code": "h_chg_mg_dv_cd",
    "customer_name": "h_cust_nm",
    "customer_no": "h_cust_no",
    "pass_kind_code": "h_cmtr_knd_cd",
    "pass_period_code": "h_cmtr_utl_trm_cd",
    "pass_period_name": "h_cmtr_utl_trm_nm",
    "pass_age_code": "h_cmtr_utl_age_cd",
    "use_open_date": "h_use_open_dt",
    "use_close_date": "h_use_cls_dt",
    "usable_day_count": "h_use_psb_dno",
    "usable_trip_count": "h_use_psb_tno",
    "departure_station_code": "h_app_dpt_rs_stn_cd",
    "departure_station_name": "h_app_dpt_rs_stn_nm",
    "arrival_station_code": "h_app_arv_rs_stn_cd",
    "arrival_station_name": "h_app_arv_rs_stn_nm",
    "transfer_station_code": "h_chtrn_rs_stn_cd",
    "transfer_station_name": "h_chtrn_rs_stn_nm",
    "train_group_code": "h_trn_gp_cd",
    "train_no_1": "h_trn_no_1",
    "train_no_2": "h_trn_no_2",
    "holiday_flag": "h_holiday_flg",
}


def parse_commuter_pass_reservation_response(
    raw: Mapping[str, Any],
) -> CommuterPassReservationResponse:
    """Parse ``pass.passReserve``'s reply.

    ``CommReservationDao.CommReservationResponse``: a free-text ``h_guide``
    beside a ``main_info`` object. ``h_guide`` is advisory -- the app shows it
    in a confirm dialog and proceeds either way
    (``CommutationInquiryActivity.java:155-166``).

    ``main_info`` is kept whole in
    :attr:`CommuterPassReservation.raw
    <korail_mobile_api.CommuterPassReservation.raw>` and not merely sampled,
    because the payment that follows transmits every field of it -- see
    :func:`~korail_mobile_api.mutation_payloads.build_commuter_pass_payment_form`.

    **NOT LIVE-VERIFIED.** Never sent, so never observed.
    """
    data = _response_mapping(raw)
    base = BaseKorailResponse.from_raw(data)
    main_info = data.get("main_info")
    reservation: CommuterPassReservation | None = None
    if main_info is not None:
        if not isinstance(main_info, Mapping):
            raise KorailProtocolError(
                "KORAIL commuter pass reservation main_info must be an object"
            )
        row = dict(main_info)
        reservation = CommuterPassReservation(
            raw=row,
            **{
                attribute: _optional_string(
                    row,
                    wire_name,
                    context="commuter pass reservation",
                )
                for attribute, wire_name in (
                    _COMMUTER_PASS_RESERVATION_FIELDS.items()
                )
            },
        )
    return CommuterPassReservationResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=data,
        guide=_optional_string(
            data,
            "h_guide",
            context="commuter pass reservation",
        ),
        reservation=reservation,
    )
