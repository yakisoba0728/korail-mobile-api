from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse
from .mutation_models import (
    DiscountCardPurchaseResponse,
    OfflineRefundExecuteResponse,
    OfflineRefundJourney,
    OfflineRefundSeat,
    OfflineRefundTicket,
    OfflineRefundVerifyResponse,
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPassengerChangeResponse,
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
    ``h_rcvd_amt``.

    The seat sum is the PRIMARY source here, matching the app. The
    ``h_tot_rcvd_amt`` key looks like the obvious shortcut, and
    ``BasketTicketActivity.java:637-641`` does put that figure in the payment
    bundle — but it puts the reservation response in the same bundle, so
    ``PaymentActivity.java:169`` takes the recalculating branch and the
    extra is never read. There is no live path in the APK by which
    ``h_tot_rcvd_amt`` reaches ``hidMnsStlAmt1``. Preferring it was therefore
    preferring a number the app deliberately ignores, and the two can only
    agree by luck once add-on products, fees or mileage land at a different
    moment than the seat rows.

    When both sources are readable and disagree, this refuses outright rather
    than picking one: a settlement whose amount is ambiguous is exactly the
    thing that must not reach the wire. ``h_tot_rcvd_amt`` remains the fallback
    for a response that carries no seat rows at all.

    Returns ``None`` rather than a partial figure when neither source is usable.
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


# --- 비회원 오프라인 반환 ------------------------------------------------

#: ``RefundVerifyTicketDao.RefundVerifyTicketResponse.SeatInfo:169-171``.
_OFFLINE_REFUND_SEAT_FIELDS = {
    "room_class_name": "psrm_cl_nm",
    "car_no": "scar_no",
    "seat_no": "seat_no",
}

#: ``RefundVerifyTicketDao.RefundVerifyTicketResponse.JrnyInfo:72-79``.
_OFFLINE_REFUND_JOURNEY_FIELDS = {
    "departure_date": "dpt_dt",
    "departure_time": "dpt_tm",
    "arrival_time": "arv_tm",
    "departure_station_code": "dpt_rs_stn_cd",
    "arrival_station_code": "arv_rs_stn_cd",
    "train_group_code": "trn_gp_cd",
    "train_no": "trn_no",
}

#: ``RefundVerifyTicketDao.RefundVerifyTicketResponse.Orgtkinfo:118-126``.
#: ``prnNo`` is P-r-n here and becomes the execute form's P-n-r ``pnrNo``;
#: see :class:`~korail_mobile_api.mutation_models.OfflineRefundTicket`.
_OFFLINE_REFUND_TICKET_FIELDS = {
    "pnr_no": "prnNo",
    "original_sale_date": "ogtk_sale_dt",
    "original_window_no": "ogtk_sale_wct_no",
    "original_sale_sequence": "ogtk_sale_sqno",
    "original_return_password": "ogtk_ret_pwd",
    "ticket_kind_code": "tk_knd_cd",
    "return_division_code": "ret_dv_cd",
    "return_reason_code": "ret_rsn_cd",
}

#: ``RefundVerifyTicketDao.RefundVerifyTicketResponse:66-69``.
_OFFLINE_REFUND_VERIFY_FIELDS = {
    "received_amount": "rcvd_amt",
    "refund_amount": "ret_amt",
    "refund_fee": "ret_fee",
    "popup_message": "poppMsg",
}


def _offline_refund_rows(
    container: Any,
    *,
    key: str,
    context: str,
) -> list[Mapping[str, Any]]:
    """Read one of the response's ``ArrayList`` members.

    Gson gives the app a plain JSON array for each of ``orgtkinfo_list`` /
    ``jrnyinfo_list`` / ``seatinfo_list``
    (``RefundVerifyTicketDao.java:65,77,118``). Absent and null both mean "no
    rows" rather than an error, because the app dereferences them only when it
    has already decided the verification succeeded (``s5/h.java:61-85``).
    """
    if container is None:
        return []
    if isinstance(container, list):
        rows = container
    else:
        raise KorailProtocolError(
            f"KORAIL offline refund {key} must be a list or null"
        )
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                f"KORAIL offline refund {context} must be an object"
            )
    return list(rows)


def parse_offline_refund_verify_response(
    raw: Mapping[str, Any],
) -> OfflineRefundVerifyResponse:
    """Parse ``refunds.verifyOnlineRefunds``'s reply.

    ``RefundVerifyTicketDao.RefundVerifyTicketResponse``
    (``RefundVerifyTicketDao.java:64-209``), including the three nested lists
    the confirmation screen renders (``s5/h.java:61-90``).

    **NOT LIVE-VERIFIED.** The shape comes from the DAO alone; no capture of a
    real 비회원 반환 조회 exists in this repository.

    The parsed object carries the ticket's four-part sale identity and its
    return password in the clear — that is what the call is FOR — so treat it
    as a credential. Its attribute names are registered in
    :data:`~korail_mobile_api.redaction.SENSITIVE_KEYS`.
    """
    data = _response_mapping(raw)
    base = BaseKorailResponse.from_raw(data)
    tickets: list[OfflineRefundTicket] = []
    for ticket_row in _offline_refund_rows(
        data.get("orgtkinfo_list"),
        key="orgtkinfo_list",
        context="ticket",
    ):
        ticket_data = dict(ticket_row)
        journeys: list[OfflineRefundJourney] = []
        for journey_row in _offline_refund_rows(
            ticket_data.get("jrnyinfo_list"),
            key="jrnyinfo_list",
            context="journey",
        ):
            journey_data = dict(journey_row)
            seats = tuple(
                OfflineRefundSeat(
                    raw=dict(seat_row),
                    **{
                        attribute: _optional_string(
                            seat_row,
                            wire_name,
                            context="offline refund seat",
                        )
                        for attribute, wire_name in (
                            _OFFLINE_REFUND_SEAT_FIELDS.items()
                        )
                    },
                )
                for seat_row in _offline_refund_rows(
                    journey_data.get("seatinfo_list"),
                    key="seatinfo_list",
                    context="seat",
                )
            )
            journeys.append(
                OfflineRefundJourney(
                    seats=seats,
                    raw=journey_data,
                    **{
                        attribute: _optional_string(
                            journey_data,
                            wire_name,
                            context="offline refund journey",
                        )
                        for attribute, wire_name in (
                            _OFFLINE_REFUND_JOURNEY_FIELDS.items()
                        )
                    },
                )
            )
        tickets.append(
            OfflineRefundTicket(
                journeys=tuple(journeys),
                raw=ticket_data,
                **{
                    attribute: _optional_string(
                        ticket_data,
                        wire_name,
                        context="offline refund ticket",
                    )
                    for attribute, wire_name in (
                        _OFFLINE_REFUND_TICKET_FIELDS.items()
                    )
                },
            )
        )
    return OfflineRefundVerifyResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=data,
        tickets=tuple(tickets),
        **{
            attribute: _optional_string(
                data,
                wire_name,
                context="offline refund verification",
            )
            for attribute, wire_name in _OFFLINE_REFUND_VERIFY_FIELDS.items()
        },
    )


def parse_offline_refund_execute_response(
    raw: Mapping[str, Any],
) -> OfflineRefundExecuteResponse:
    """Parse ``refunds.executeOnlineRefunds``'s reply.

    ``RefundExecuteTicketRefundDao.RefundExecuteTicketRefundResponse``
    (``RefundExecuteTicketRefundDao.java:125-133``): the envelope plus
    ``h_ret_dv_cd``, which says whether the money came back now or the paper
    ticket still has to be handed in (``s5/h.java:187``).

    **NOT LIVE-VERIFIED.**
    """
    data = _response_mapping(raw)
    base = BaseKorailResponse.from_raw(data)
    return OfflineRefundExecuteResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=data,
        return_division_code=_optional_string(
            data,
            "h_ret_dv_cd",
            context="offline refund execution",
        ),
    )


def parse_reservation_passenger_change_response(
    raw: Mapping[str, Any],
) -> ReservationPassengerChangeResponse:
    """Parse ``reservation.reservationChange.do``'s reply.

    ``ReservationChangeDao.ReservationChangeResponse`` (``:151-160``) declares
    exactly one field beyond the common three: ``jrnyList``, a list of
    ``JrnyInfo`` objects whose only member is ``lumpStlTgtNo`` (``:17-26``).

    ``jrnyList`` is REQUIRED, not optional. The app dereferences
    ``getJrnyList().get(0).getLumpStlTgtNo()`` with no null check the moment
    the DAO returns (``ReservedTicketChangeActivity.java:179``), so a reply
    without it is one the app itself could not use — and this call has already
    changed the PNR by the time it answers, which is why an unusable reply is
    raised rather than swallowed into an empty tuple that would read as
    "nothing to settle".

    **NOT LIVE-VERIFIED.** Never sent, so never observed.
    """
    data = _response_mapping(raw)
    base = BaseKorailResponse.from_raw(data)
    rows = data.get("jrnyList")
    if not isinstance(rows, list) or not rows:
        raise KorailProtocolError(
            "KORAIL reservation passenger change response must carry a "
            "non-empty jrnyList"
        )
    targets: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise KorailProtocolError(
                "KORAIL reservation passenger change jrnyList must contain "
                "objects"
            )
        target = _optional_string(
            row,
            "lumpStlTgtNo",
            context="reservation passenger change",
        )
        if target is None:
            raise KorailProtocolError(
                "KORAIL reservation passenger change jrnyList row is missing "
                "lumpStlTgtNo"
            )
        targets.append(target)
    return ReservationPassengerChangeResponse(
        h_msg_cd=base.h_msg_cd,
        h_msg_txt=base.h_msg_txt,
        str_result=base.str_result,
        raw=data,
        lump_settlement_target_nos=tuple(targets),
    )
