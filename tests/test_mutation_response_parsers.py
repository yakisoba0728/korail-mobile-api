from __future__ import annotations

import pytest

from korail_mobile_api import (
    KorailConfig,
    KorailProtocolError,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from korail_mobile_api.mutation_parsers import (
    parse_reservation_hold_response,
    parse_reservation_payment_response,
)
from korail_mobile_api.mutation_payloads import (
    build_unpaid_reservation_cancel_form,
)
from korail_mobile_api.read_parsers import parse_reservation_history_response
from korail_mobile_api.redaction import redact_mapping


#: 15 decimal digits, the real PNR shape. Synthetic value.
SYNTHETIC_LIVE_PNR = "399999999999999"


def _reservation_history_body() -> dict[str, object]:
    """The reservation-history shape a live account with one hold returns.

    Structure and types from the 2026-07-25 live run, identities replaced with
    synthetic values. The two things that matter here are that ``h_jrny_cnt``
    is the JSON integer ``1`` -- where the reserve response sends the string
    ``"0001"`` -- and that the PNR lives on the ``train_info`` row. The DAO
    (``TicketRsvHistoryDao``) declares no ``h_jrny_cnt`` at all; the server
    sends it anyway, and Gson simply ignores what it does not declare.
    """
    return {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "synthetic history",
        "strResult": "SUCC",
        "h_jrny_cnt": 1,
        "jrny_infos": {
            "jrny_info": [
                {
                    "train_infos": {
                        "train_info": [
                            {
                                "h_pnr_no": SYNTHETIC_LIVE_PNR,
                                "h_trn_no": "00101",
                                "h_run_dt": "20990101",
                                "h_dpt_rs_stn_nm": "SYNTHETIC_DEPARTURE",
                                "h_arv_rs_stn_nm": "SYNTHETIC_ARRIVAL",
                                "h_dpt_tm": "060000",
                                "h_arv_tm": "083000",
                                "h_payment_flg": "N",
                                "h_stl_flg": "N",
                                "h_tot_seat_cnt": 1,
                                "h_tot_stnd_cnt": 0,
                            }
                        ]
                    }
                }
            ]
        },
    }


def test_a_hold_can_be_read_back_out_of_the_reservation_history():
    """The documented recovery path, end to end, on the real history shape.

    When the PNR is lost, the reservation history is where it is found again.
    On 2026-07-25 that path did not work: handing the history response to
    ``parse_reservation_hold_response`` raised "KORAIL reservation field
    h_jrny_cnt must be a string or null", because the history sends the JSON
    integer ``1`` while a reserve response sends ``"0001"``. The operator had to
    hand-build a hold to cancel a real reservation.
    """
    history_raw = _reservation_history_body()

    # 1. The history itself parses and names the outstanding PNR.
    history = parse_reservation_history_response(history_raw)
    assert [item.pnr_no for item in history.items] == [SYNTHETIC_LIVE_PNR]

    # 2. The SAME body goes through the hold parser without raising, and the
    #    integer journey count normalises to the string the builders expect.
    hold = parse_reservation_hold_response(history_raw)
    assert hold.journey_count == "1"

    # 3. And a hold carrying the recovered PNR builds a real cancel form. The
    #    builder compares journey counts numerically, so all three live spellings
    #    have to reach it intact.
    for journey_count in (1, "1", "0001"):
        recovered = parse_reservation_hold_response(
            {**history_raw, "h_pnr_no": SYNTHETIC_LIVE_PNR, "h_jrny_cnt": journey_count}
        )
        assert recovered.pnr_no == SYNTHETIC_LIVE_PNR
        form = build_unpaid_reservation_cancel_form(KorailConfig(), recovered)
        assert form["txtPnrNo"] == SYNTHETIC_LIVE_PNR
        assert form["txtJrnyCnt"] == "1"
        assert form["txtJrnySqno"] == "0001"


def test_hold_parser_normalises_a_numeric_pnr_and_identity_rather_than_refusing():
    """A hold that EXISTS must never be lost to an unquoted identity field.

    A PNR is 15 digits and the settlement amount is a number; either could
    arrive unquoted, and refusing one strands a real reservation on the server.
    """
    hold = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000018",
            "h_msg_txt": "success",
            "h_pnr_no": int(SYNTHETIC_LIVE_PNR),
            "h_jrny_cnt": 1,
            "h_wct_no": 1234,
            "h_tot_rcvd_amt": 59800,
            "jrny_infos": {"jrny_info": [{"h_jrny_sqno": 1, "h_trn_no": 101}]},
        }
    )
    assert hold.pnr_no == SYNTHETIC_LIVE_PNR
    assert hold.journey_count == "1"
    assert hold.window_no == "1234"
    assert hold.received_amount == "59800"
    assert hold.journeys[0].journey_sequence == "1"
    assert hold.journeys[0].train_no == "101"


@pytest.mark.parametrize("value", [True, 1.5, ["1"], {"count": 1}])
def test_hold_parser_still_refuses_a_genuinely_wrong_scalar_type(value):
    # Tolerating a number is not tolerating anything: these are not shapes Gson
    # would have read as a String either.
    with pytest.raises(KorailProtocolError):
        parse_reservation_hold_response(
            {
                "strResult": "SUCC",
                "h_msg_cd": "IRR000018",
                "h_msg_txt": "success",
                "h_pnr_no": "SYNTHETIC_PNR",
                "h_jrny_cnt": value,
            }
        )


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


def test_reservation_hold_parser_exposes_the_live_payment_deadline():
    # Shape taken from a real hold captured by
    # scripts/capture_live_read_surface.py, with identity fields replaced by
    # synthetic values. The live server leaves h_pay_limit_msg EMPTY and puts
    # the deadline in h_ntisu_lmt / h_ntisu_lmt_dt / h_ntisu_lmt_tm, which is
    # what the app concatenates and parses as yyyyMMddHHmmss
    # (S4/C0816p.java:64-70, ReservedTicketActivity.java:356,365).
    # h_pay_limit_msg is declared on ReservationResponse (:22, getter :529) but
    # read by no app screen, so a caller reading only payment_deadline_message
    # never learns when the unpaid hold self-cancels.
    raw = {
        "strResult": "SUCC",
        "h_msg_cd": "IRR000018",
        "h_msg_txt": "synthetic hold notice",
        "h_pnr_no": "SYNTHETIC_PNR",
        "h_jrny_cnt": "0001",
        "h_payment_flg": "Y",
        "h_payment_msg": "",
        "h_pay_limit_msg": "",
        "h_ntisu_lmt": "synthetic deadline notice",
        "h_ntisu_lmt_dt": "20990101",
        "h_ntisu_lmt_tm": "025852",
        "h_tot_prc": "00000059800",
        "jrny_infos": {"jrny_info": [{"h_jrny_sqno": "0001"}]},
    }

    response = parse_reservation_hold_response(raw)

    assert response.payment_deadline_message == ""
    assert response.payment_deadline_notice == "synthetic deadline notice"
    assert response.payment_deadline_date == "20990101"
    assert response.payment_deadline_time == "025852"
    assert (
        response.payment_deadline_date + response.payment_deadline_time
        == "20990101025852"
    )


def test_reservation_hold_payment_deadline_is_absent_not_invented():
    response = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_pnr_no": "SYNTHETIC_PNR",
            "h_jrny_cnt": "1",
            "jrny_infos": {"jrny_info": [{"h_jrny_sqno": "0001"}]},
        }
    )

    assert response.payment_deadline_notice is None
    assert response.payment_deadline_date is None
    assert response.payment_deadline_time is None
