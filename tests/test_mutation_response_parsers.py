from __future__ import annotations

import pytest

from korail_mobile_api import (
    KorailProtocolError,
    ReservationHoldResponse,
    ReservationPaymentResponse,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
)
from korail_mobile_api.redaction import redact_mapping


def test_reservation_hold_parser_preserves_payment_handoff_without_repr_leaks():
    raw = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000000",
        "h_msg_txt": "success",
        "h_pnr_no": "SYNTHETIC_PNR_REFERENCE",
        "h_jrny_cnt": "1",
        "h_wct_no": "SYNTHETIC_WINDOW",
        "h_tmp_job_sqno1": "SYNTHETIC_JOB_1",
        "h_tmp_job_sqno2": "SYNTHETIC_JOB_2",
        "h_payment_flg": "Y",
        "h_tot_prc": "8400",
        "jrny_infos": {
            "jrny_info": [
                {
                    "h_jrny_sqno": "0001",
                    "h_rsv_chg_no": "000",
                    "h_dpt_dt": "20990101",
                    "h_dpt_tm": "100000",
                    "h_arv_tm": "101700",
                    "h_dpt_rs_stn_cd": "SYNTHETIC_DPT",
                    "h_arv_rs_stn_cd": "SYNTHETIC_ARV",
                    "h_trn_no": "SYNTHETIC_TRAIN",
                }
            ]
        },
    }

    response = parse_reservation_hold_response(raw)

    assert isinstance(response, ReservationHoldResponse)
    assert response.str_result == "SUCC"
    assert response.pnr_no == "SYNTHETIC_PNR_REFERENCE"
    assert response.total_price == "8400"
    assert response.journeys[0].reservation_change_no == "000"
    rendered = repr(response)
    assert "SYNTHETIC_PNR_REFERENCE" not in rendered
    assert "SYNTHETIC_WINDOW" not in rendered
    assert "SYNTHETIC_JOB_1" not in rendered


def test_reservation_hold_parser_prefers_the_responses_total_received_amount():
    # BasketTicketActivity.java:638 reads RECEIVED_AMOUNT straight off
    # reservationResponse.getH_tot_rcvd_amt() (ReservationResponse.java:33).
    response = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_tot_prc": "8400",
            "h_tot_rcvd_amt": "7560",
            "jrny_infos": {
                "jrny_info": [
                    {
                        "h_jrny_sqno": "0001",
                        "seat_infos": {
                            "seat_info": [
                                {
                                    "h_seat_prc": "8400",
                                    "h_seat_fare": "0",
                                    "h_rcvd_amt": "7560",
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )
    assert response.total_price == "8400"
    assert response.received_amount == "7560"


def test_reservation_hold_parser_sums_seat_amounts_when_the_total_is_absent():
    # PaymentActivity.G0() (:186-199) computes mReceivedAmount as
    # sum(h_seat_prc + h_seat_fare) - sum((h_seat_prc + h_seat_fare) -
    # h_rcvd_amt), which is the plain sum of the per-seat h_rcvd_amt.
    response = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_tot_prc": "16800",
            "jrny_infos": {
                "jrny_info": [
                    {
                        "h_jrny_sqno": "0001",
                        "seat_infos": {
                            "seat_info": [
                                {
                                    "h_seat_prc": "8400",
                                    "h_seat_fare": "0",
                                    "h_rcvd_amt": "8400",
                                },
                                {
                                    "h_seat_prc": "8400",
                                    "h_seat_fare": "0",
                                    "h_rcvd_amt": "4200",
                                },
                            ]
                        },
                    }
                ]
            },
        }
    )
    assert response.total_price == "16800"
    assert response.received_amount == "12600"


@pytest.mark.parametrize(
    "jrny_infos",
    [
        None,  # no journeys at all
        {"jrny_info": [{"h_jrny_sqno": "0001"}]},  # journey without seat rows
        {
            "jrny_info": [
                {
                    "h_jrny_sqno": "0001",
                    "seat_infos": {
                        "seat_info": [
                            {"h_seat_prc": "8400", "h_rcvd_amt": "8400"},
                            {"h_seat_prc": "8400"},  # one seat unreadable
                        ]
                    },
                }
            ]
        },
    ],
)
def test_reservation_hold_parser_reports_no_received_amount_when_unknowable(
    jrny_infos,
):
    # A partial sum would under-charge, so the parser reports nothing and the
    # payment builder refuses rather than falling back to the display total.
    response = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_tot_prc": "8400",
            "jrny_infos": jrny_infos,
        }
    )
    assert response.total_price == "8400"
    assert response.received_amount is None


def test_reservation_payment_parser_accepts_failure_envelope_without_card_data():
    raw = {
        "strResult": "FAIL",
        "h_msg_cd": "SYNTHETIC_PAYMENT_REJECTED",
        "h_msg_txt": "validation rejected",
        "h_im_flg": None,
        "tk_coupon_info": None,
    }

    response = parse_reservation_payment_response(raw)

    assert isinstance(response, ReservationPaymentResponse)
    assert response.str_result == "FAIL"
    assert response.h_msg_cd == "SYNTHETIC_PAYMENT_REJECTED"
    assert response.image_ticket_flag is None
    assert response.coupons == ()


def test_reservation_payment_parser_preserves_coupon_rows_without_repr_leaks():
    raw = {
        "strResult": "SUCC",
        "h_msg_cd": "SYNTHETIC_SUCCESS",
        "h_msg_txt": "success",
        "h_im_flg": "Y",
        "tk_coupon_info": [
            {
                "h_cert_pwd": "SYNTHETIC_SECRET",
                "h_coup_no": "SYNTHETIC_COUPON",
                "h_fdcert_mg_cls_dt": "20991231",
                "h_fdcert_mg_st_dt": "20990101",
                "h_tk_ret_no": "SYNTHETIC_TICKET_REFERENCE",
            }
        ],
    }

    response = parse_reservation_payment_response(raw)

    assert response.image_ticket_flag == "Y"
    assert response.coupons[0].coupon_no == "SYNTHETIC_COUPON"
    rendered = repr(response)
    assert "SYNTHETIC_SECRET" not in rendered
    assert "SYNTHETIC_TICKET_REFERENCE" not in rendered


@pytest.mark.parametrize(
    "parser,raw",
    [
        (
            parse_reservation_hold_response,
            {
                "strResult": "SUCC",
                "h_msg_cd": "SYNTHETIC_SUCCESS",
                "h_msg_txt": "success",
                "jrny_infos": {"jrny_info": {}},
            },
        ),
        (
            parse_reservation_payment_response,
            {
                "strResult": "SUCC",
                "h_msg_cd": "SYNTHETIC_SUCCESS",
                "h_msg_txt": "success",
                "tk_coupon_info": {},
            },
        ),
    ],
)
def test_mutation_response_parsers_reject_malformed_repeated_containers(parser, raw):
    with pytest.raises(KorailProtocolError):
        parser(raw)


def test_mutation_models_and_raw_handoff_fields_are_recursively_redacted():
    hold = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "SYNTHETIC_SUCCESS",
            "h_msg_txt": "success",
            "h_pnr_no": "SYNTHETIC_PNR",
            "h_jrny_cnt": "1",
            "h_wct_no": "SYNTHETIC_WINDOW",
            "h_tmp_job_sqno1": "SYNTHETIC_JOB_1",
            "h_tmp_job_sqno2": "SYNTHETIC_JOB_2",
            "jrny_infos": {
                "jrny_info": [
                    {
                        "h_rsv_chg_no": "SYNTHETIC_CHANGE",
                    }
                ]
            },
        }
    )
    payment = parse_reservation_payment_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "SYNTHETIC_SUCCESS",
            "h_msg_txt": "success",
            "h_im_flg": "Y",
            "tk_coupon_info": [
                {
                    "h_cert_pwd": "SYNTHETIC_CERTIFICATE_PASSWORD",
                    "h_coup_no": "SYNTHETIC_COUPON",
                    "h_tk_ret_no": "SYNTHETIC_TICKET_RETURN",
                }
            ],
        }
    )

    redacted = redact_mapping({"hold": hold, "payment": payment})

    assert redacted["hold"]["window_no"] == "[REDACTED]"
    assert redacted["hold"]["temporary_job_sequence_1"] == "[REDACTED]"
    assert redacted["hold"]["temporary_job_sequence_2"] == "[REDACTED]"
    assert (
        redacted["hold"]["journeys"][0]["reservation_change_no"]
        == "[REDACTED]"
    )
    assert redacted["hold"]["raw"]["h_wct_no"] == "[REDACTED]"
    assert redacted["hold"]["raw"]["h_tmp_job_sqno1"] == "[REDACTED]"
    assert redacted["hold"]["raw"]["h_tmp_job_sqno2"] == "[REDACTED]"
    assert (
        redacted["hold"]["raw"]["jrny_infos"]["jrny_info"][0][
            "h_rsv_chg_no"
        ]
        == "[REDACTED]"
    )
    assert (
        redacted["payment"]["coupons"][0]["certificate_password"]
        == "[REDACTED]"
    )
    assert (
        redacted["payment"]["raw"]["tk_coupon_info"][0]["h_cert_pwd"]
        == "[REDACTED]"
    )
    assert (
        redacted["payment"]["raw"]["tk_coupon_info"][0]["h_coup_no"]
        == "[REDACTED]"
    )
    assert (
        redacted["payment"]["raw"]["tk_coupon_info"][0]["h_tk_ret_no"]
        == "[REDACTED]"
    )
