from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse
from .mutation_models import (
    ReservationHoldResponse,
    ReservationJourney,
    ReservationPaymentCoupon,
    ReservationPaymentResponse,
)


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
    value = row.get(key)
    if value is not None and not isinstance(value, str):
        raise KorailProtocolError(
            f"KORAIL {context} field {key} must be a string or null"
        )
    return value


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
