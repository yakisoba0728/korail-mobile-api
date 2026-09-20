# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

from __future__ import annotations

import pytest

from korail_mobile_api import (
    KorailConfig,
    KorailProtocolError,
    PaidTicket,
    ReservationHoldResponse,
    ReservationPaymentResponse,
)
from korail_mobile_api.mutation_models import (
    StationRefundExecutionRequest,
    StationRefundVerificationRequest,
)
from korail_mobile_api.mutation_parsers import (
    parse_cash_receipt_issue_response,
    parse_discount_card_purchase_response,
    parse_refund_ticket_response,
    parse_reservation_hold_response,
    parse_reservation_payment_response,
    parse_station_refund_execution_response,
    parse_station_refund_verification_response,
)
from korail_mobile_api.mutation_payloads import (
    build_unpaid_reservation_cancel_form,
)
from korail_mobile_api.read_parsers import (
    parse_refund_ticket_detail_response,
    parse_reservation_history_response,
)
from korail_mobile_api.redaction import redact_mapping


#: 15 decimal digits, the real PNR shape. Synthetic value.
SYNTHETIC_LIVE_PNR = "399999999999999"


def test_refund_result_accepts_nullable_or_absent_settlement_list():
    # RefundTicketOut.java:48-53 declares stlList nullable. A response that
    # omits the key outright is treated the same as an explicit null, like
    # every other optional field this package parses.
    null_result = parse_refund_ticket_response(
        {"strResult": "SUCC", "stlList": None}
    )
    empty_result = parse_refund_ticket_response(
        {"strResult": "SUCC", "stlList": []}
    )
    missing_result = parse_refund_ticket_response({"strResult": "SUCC"})
    assert null_result.settlement_method_codes == ()
    assert null_result.settlement_list_is_null is True
    assert empty_result.settlement_method_codes == ()
    assert empty_result.settlement_list_is_null is False
    assert missing_result.settlement_method_codes == ()
    assert missing_result.settlement_list_is_null is True


def test_ncard_purchase_preserves_settlement_and_tax_fields():
    result = parse_discount_card_purchase_response(
        {
            "strResult": "SUCC",
            "lumpStlTgtNo": "SYNTHETIC_LUMP_TARGET",
            "dcntCrdStlTgtNo": "SYNTHETIC_NCARD_TARGET",
            "rcvdAmt": 60000,
            "stxAmt": 3000,
            "taxtSplAmt": "57000",
        }
    )
    assert result.lump_settlement_target_no == "SYNTHETIC_LUMP_TARGET"
    assert result.discount_card_settlement_target_no == "SYNTHETIC_NCARD_TARGET"
    assert result.received_amount == "60000"
    assert result.stx_amount == "3000"
    assert result.taxt_supply_amount == "57000"
    assert "SYNTHETIC_NCARD_TARGET" not in repr(result)


def test_ncard_purchase_tax_fields_allow_null_or_absence():
    absent = parse_discount_card_purchase_response({"strResult": "SUCC"})
    present_null = parse_discount_card_purchase_response(
        {
            "strResult": "SUCC",
            "dcntCrdStlTgtNo": None,
            "stxAmt": None,
            "taxtSplAmt": None,
        }
    )
    for result in (absent, present_null):
        assert result.discount_card_settlement_target_no is None
        assert result.stx_amount is None
        assert result.taxt_supply_amount is None
    with pytest.raises(KorailProtocolError):
        parse_discount_card_purchase_response(
            {"strResult": "SUCC", "stxAmt": [3000]}
        )


def test_paid_ticket_carries_the_refund_details_pbp_flag():
    detail = parse_refund_ticket_detail_response(
        {
            "strResult": "SUCC",
            "h_pnr_no": SYNTHETIC_LIVE_PNR,
            "h_sale_dt": "20990101",
            "h_orgtk_wct_no": "SYNTHETIC_WINDOW",
            "h_orgtk_sale_sqno": "SYNTHETIC_SEQUENCE",
            "h_orgtk_ret_pwd": "SYNTHETIC_RETURN_PASSWORD",
            "h_pbp_acep_tgt_flg": "Y",
        }
    )
    ticket = PaidTicket.from_refund_detail(detail)
    assert ticket.pbp_acceptance_target_flag == "Y"
    assert "SYNTHETIC_RETURN_PASSWORD" not in repr(ticket)


def test_cash_receipt_issue_parses_approval_list_and_hides_identifiers():
    result = parse_cash_receipt_issue_response(
        {
            "strResult": "SUCC",
            "cashRcetTxnDvCd": "SYNTHETIC_TXN",
            "athnDmnRcgnNo": "SYNTHETIC_AUTH_NO",
            "totApvAmt": "8400",
            "apvList": [
                {
                    "jobDvCd": "SYNTHETIC_JOB",
                    "rcptNo": "SYNTHETIC_RECEIPT_NO",
                    "cashRcetApvNo": "SYNTHETIC_APPROVAL_NO",
                    "totApvAmt": "8400",
                }
            ],
        }
    )
    assert result.total_approved_amount == "8400"
    assert result.approvals[0].approved_amount == "8400"
    assert result.approvals[0].cash_receipt_approval_no == "SYNTHETIC_APPROVAL_NO"
    assert "SYNTHETIC_AUTH_NO" not in repr(result)
    assert "SYNTHETIC_APPROVAL_NO" not in repr(result.approvals[0])
    assert parse_cash_receipt_issue_response(
        {"strResult": "FAIL"}
    ).approvals == ()
    assert parse_cash_receipt_issue_response(
        {"strResult": "SUCC", "apvList": None}
    ).approval_list_is_null is True
    with pytest.raises(KorailProtocolError, match="apvList must be a list"):
        parse_cash_receipt_issue_response({"strResult": "SUCC", "apvList": "bad"})


def test_station_refund_execution_uses_verified_original_ticket_and_amounts():
    verification = parse_station_refund_verification_response(
        {
            "strResult": "SUCC",
            "rcvd_amt": "8400",
            "ret_amt": "8400",
            "ret_fee": "0",
            "orgtkinfo_list": [
                {
                    "pnr_no": SYNTHETIC_LIVE_PNR,
                    "ogtk_sale_dt": "20990101",
                    "ogtk_sale_wct_no": "SYNTHETIC_WINDOW",
                    "ogtk_sale_sqno": "SYNTHETIC_SEQUENCE",
                    "ogtk_ret_pwd": "SYNTHETIC_RETURN_PASSWORD",
                    "ret_dv_cd": "SYNTHETIC_DIVISION",
                    "ret_rsn_cd": "SYNTHETIC_REASON",
                    "tk_knd_cd": "SYNTHETIC_KIND",
                }
            ],
        }
    )
    request = StationRefundExecutionRequest.from_verification(
        verification,
        customer_phone="SYNTHETIC_PHONE",
        customer_name="SYNTHETIC_NAME",
    )
    assert request.pnr_no == SYNTHETIC_LIVE_PNR
    assert request.refund_amount == "8400"
    assert request.refund_fee == "0"
    assert request.refund_division_code == "SYNTHETIC_DIVISION"
    assert "SYNTHETIC_RETURN_PASSWORD" not in repr(request)
    assert "SYNTHETIC_PHONE" not in repr(request)
    assert parse_station_refund_execution_response(
        {"strResult": "SUCC", "h_ret_dv_cd": "SYNTHETIC_DIVISION"}
    ).refund_division_code == "SYNTHETIC_DIVISION"


def test_station_refund_verification_request_keeps_return_parts_separate():
    request = StationRefundVerificationRequest(
        customer_name="SYNTHETIC_NAME",
        return_no_1="111",
        return_no_2="222",
        return_no_3="333",
        return_no_4="444",
    )
    assert (request.return_no_1, request.return_no_4) == ("111", "444")
    assert "SYNTHETIC_NAME" not in repr(request)
    with pytest.raises(ValueError, match="verification requires return_no_4"):
        StationRefundVerificationRequest(
            customer_name="SYNTHETIC_NAME",
            return_no_1="111",
            return_no_2="222",
            return_no_3="333",
            return_no_4="",
        )


_VERIFIED_TICKET = {
    "pnr_no": SYNTHETIC_LIVE_PNR,
    "ogtk_sale_dt": "20990101",
    "ogtk_sale_wct_no": "SYNTHETIC_WINDOW",
    "ogtk_sale_sqno": "SYNTHETIC_SEQUENCE",
    "ogtk_ret_pwd": "SYNTHETIC_RETURN_PASSWORD",
    "ret_dv_cd": "SYNTHETIC_DIVISION",
    "ret_rsn_cd": "SYNTHETIC_REASON",
    "tk_knd_cd": "SYNTHETIC_KIND",
}


def _verification(ticket=_VERIFIED_TICKET, **amounts):
    return parse_station_refund_verification_response(
        {
            "strResult": "SUCC",
            "ret_amt": "8400",
            "ret_fee": "0",
            "orgtkinfo_list": [ticket],
            **amounts,
        }
    )


def test_station_refund_execution_refuses_unverified_or_missing_echo_values():
    for raw in (
        {"strResult": "FAIL", "orgtkinfo_list": []},
        {"strResult": "SUCC", "orgtkinfo_list": None},
    ):
        verification = parse_station_refund_verification_response(raw)
        with pytest.raises(KorailProtocolError, match="successful verification"):
            StationRefundExecutionRequest.from_verification(
                verification,
                customer_phone="SYNTHETIC_PHONE",
                customer_name="SYNTHETIC_NAME",
            )
    # What the verification should have echoed and did not is the server's
    # answer falling short, so it is a protocol error that names every
    # missing value -- blank ones included -- not the first one the
    # constructor trips on.
    for verification, missing in (
        (
            _verification({"pnr_no": SYNTHETIC_LIVE_PNR}),
            "original_return_password, original_sale_date, original_sale_sequence, "
            "original_sale_window_no, refund_division_code, refund_reason_code, "
            "ticket_kind_code",
        ),
        (_verification({**_VERIFIED_TICKET, "tk_knd_cd": "  "}), "ticket_kind_code"),
        (_verification(ret_fee=None), "refund_fee"),
    ):
        with pytest.raises(KorailProtocolError, match=f"is missing {missing}$"):
            StationRefundExecutionRequest.from_verification(
                verification,
                customer_phone="SYNTHETIC_PHONE",
                customer_name="SYNTHETIC_NAME",
            )


@pytest.mark.parametrize("blank", ["customer_phone", "customer_name"])
def test_station_refund_execution_checks_the_callers_own_values_as_input(blank):
    # The phone and name come from the caller, not the server, so the
    # constructor refuses them as input (ValueError), as it would any directly
    # built request; the verification's own gaps stay KorailProtocolError.
    values = {"customer_phone": "SYNTHETIC_PHONE", "customer_name": "SYNTHETIC_NAME"}
    values[blank] = " "
    with pytest.raises(ValueError, match=f"execution requires {blank}"):
        StationRefundExecutionRequest.from_verification(_verification(), **values)


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
        assert form["txtJrnyCnt"] == str(journey_count)
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


def test_reservation_hold_parser_reports_no_received_amount_when_oversized():
    # A digit string past Python's int-string conversion limit (4300 digits,
    # sys.int_info.default_max_str_digits) used to leak a bare ValueError out
    # of int(). Both the total and a per-seat amount are unreadable, so the
    # parser reports no received amount, the same as any other unreadable one.
    huge = "9" * 5000
    no_seats = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_tot_prc": "8400",
            "h_tot_rcvd_amt": huge,
            "jrny_infos": None,
        }
    )
    assert no_seats.received_amount is None

    one_seat = parse_reservation_hold_response(
        {
            "strResult": "SUCC",
            "h_msg_cd": "IRR000000",
            "h_msg_txt": "success",
            "h_tot_prc": "8400",
            "jrny_infos": {
                "jrny_info": [
                    {
                        "h_jrny_sqno": "0001",
                        "seat_infos": {
                            "seat_info": [
                                {
                                    "h_seat_prc": "8400",
                                    "h_seat_fare": "0",
                                    "h_rcvd_amt": huge,
                                }
                            ]
                        },
                    }
                ]
            },
        }
    )
    assert one_seat.received_amount is None


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


def _mutation_parser(name):
    from korail_mobile_api import mutation_parsers

    return getattr(mutation_parsers, name)


@pytest.mark.parametrize(
    ("parser", "body", "message"),
    [
        ("parse_refund_ticket_response", {"stlList": ["x"]}, "refund settlement"),
        ("parse_cash_receipt_issue_response", {"apvList": ["x"]}, "cash receipt ApvItem"),
        (
            "parse_station_refund_verification_response",
            {"orgtkinfo_list": ["x"]},
            "station refund Orgtkinfo",
        ),
        (
            "parse_reservation_hold_response",
            {"jrny_infos": {"jrny_info": ["x"]}},
            "reservation journey",
        ),
        (
            "parse_reservation_hold_response",
            {"jrny_infos": {"jrny_info": [{"seat_infos": {"seat_info": ["x"]}}]}},
            "reservation seat_info row",
        ),
        ("parse_reservation_payment_response", {"tk_coupon_info": ["x"]}, "payment coupon"),
    ],
)
def test_a_mutation_parser_names_a_row_that_is_not_an_object(parser, body, message):
    with pytest.raises(KorailProtocolError, match=rf"^KORAIL {message} must be an object$"):
        _mutation_parser(parser)({"strResult": "SUCC", **body})


# Every scalar field of the hold, its journeys and the payment coupons, and the
# wire key it is read from -- written out here, not imported, so a rewrite of
# the parsers into field maps is checked against this list and not itself.
_HOLD_KEYS = (
    ("pnr_no", "h_pnr_no"),
    ("journey_count", "h_jrny_cnt"),
    ("window_no", "h_wct_no"),
    ("temporary_job_sequence_1", "h_tmp_job_sqno1"),
    ("temporary_job_sequence_2", "h_tmp_job_sqno2"),
    ("payment_flag", "h_payment_flg"),
    ("payment_message", "h_payment_msg"),
    ("payment_deadline_message", "h_pay_limit_msg"),
    ("payment_deadline_notice", "h_ntisu_lmt"),
    ("payment_deadline_date", "h_ntisu_lmt_dt"),
    ("payment_deadline_time", "h_ntisu_lmt_tm"),
    ("total_fare", "h_tot_fare"),
    ("total_price", "h_tot_prc"),
)
_JOURNEY_KEYS = (
    ("journey_sequence", "h_jrny_sqno"),
    ("reservation_change_no", "h_rsv_chg_no"),
    ("departure_date", "h_dpt_dt"),
    ("departure_time", "h_dpt_tm"),
    ("arrival_time", "h_arv_tm"),
    ("departure_station_code", "h_dpt_rs_stn_cd"),
    ("arrival_station_code", "h_arv_rs_stn_cd"),
    ("train_no", "h_trn_no"),
)
_COUPON_KEYS = (
    ("certificate_password", "h_cert_pwd"),
    ("coupon_no", "h_coup_no"),
    ("management_close_date", "h_fdcert_mg_cls_dt"),
    ("management_start_date", "h_fdcert_mg_st_dt"),
    ("ticket_return_no", "h_tk_ret_no"),
)


def test_the_hold_key_tables_cover_every_scalar_field():
    from dataclasses import fields

    from korail_mobile_api.mutation_models import (
        ReservationHoldResponse,
        ReservationJourney,
        ReservationPaymentCoupon,
    )

    envelope = {"h_msg_cd", "h_msg_txt", "str_result", "raw"}
    assert {f.name for f in fields(ReservationHoldResponse)} == (
        {attr for attr, _ in _HOLD_KEYS} | envelope | {"received_amount", "journeys"}
    )
    assert {f.name for f in fields(ReservationJourney)} == (
        {attr for attr, _ in _JOURNEY_KEYS} | {"raw"}
    )
    assert {f.name for f in fields(ReservationPaymentCoupon)} == (
        {attr for attr, _ in _COUPON_KEYS} | {"raw"}
    )


def _hold_field(attr, key, value):
    return getattr(parse_reservation_hold_response({"strResult": "SUCC", key: value}), attr)


def _journey_field(attr, key, value):
    hold = parse_reservation_hold_response(
        {"strResult": "SUCC", "jrny_infos": {"jrny_info": [{key: value}]}}
    )
    return getattr(hold.journeys[0], attr)


def _coupon_field(attr, key, value):
    payment = parse_reservation_payment_response(
        {"strResult": "SUCC", "tk_coupon_info": [{key: value}]}
    )
    return getattr(payment.coupons[0], attr)


@pytest.mark.parametrize(
    ("read", "attr", "key", "context"),
    [(_hold_field, a, k, "reservation") for a, k in _HOLD_KEYS]
    + [(_journey_field, a, k, "reservation journey") for a, k in _JOURNEY_KEYS]
    + [(_coupon_field, a, k, "payment coupon") for a, k in _COUPON_KEYS],
    ids=[f"hold-{a}" for a, _ in _HOLD_KEYS]
    + [f"journey-{a}" for a, _ in _JOURNEY_KEYS]
    + [f"coupon-{a}" for a, _ in _COUPON_KEYS],
)
def test_each_hold_payment_field_reads_its_own_key(read, attr, key, context):
    assert read(attr, key, "SYNTHETIC-VALUE") == "SYNTHETIC-VALUE"
    assert read(attr, key, 7) == "7"
    assert read(attr, key, None) is None
    with pytest.raises(
        KorailProtocolError,
        match=rf"^KORAIL {context} field {key} must be a string, an integer, or null$",
    ):
        read(attr, key, [7])
