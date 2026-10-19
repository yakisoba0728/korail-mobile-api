"""Existing PNRs are read once and validated before a caller can explicitly pay."""

from __future__ import annotations

import sys
from collections.abc import Callable
from copy import deepcopy
from typing import Any
from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import (
    CardPayment,
    KorailAppError,
    KorailAuthError,
    KorailClient,
    KorailConfig,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
    ReservationHoldResponse,
)

PNR = "SYNTHETIC-EXISTING-PNR"
DETAIL_PATH = "/classes/com.korail.mobile.certification.ReservationList"
PAYMENT_PATH = "/classes/com.korail.mobile.payment.ReservationPayment"
ABSENT = object()


@pytest.fixture
def detail_raw() -> dict[str, Any]:
    return {
        "strResult": "SUCC",
        "h_msg_cd": "IRZ000001",
        "h_pnr_no": PNR,
        "h_wct_no": "SYNTHETIC-ACTUAL-WINDOW",
        "h_payment_flg": "Y",
        "h_jrny_cnt": "0001",
        "h_tot_prc": "99999",
        "h_tot_rcvd_amt": "53900",
        "h_tmp_job_sqno1": "001234",
        "h_tmp_job_sqno2": "005678",
        "h_ntisu_lmt_dt": "20990102",
        "h_ntisu_lmt_tm": "090000",
        "jrny_infos": {
            "jrny_info": [
                {
                    "h_jrny_sqno": "0001",
                    "h_rsv_chg_no": "009",
                    "h_trn_no": "90001",
                    "seat_infos": {
                        "seat_info": [
                            {"h_seat_no": "1A", "h_rcvd_amt": "30000", "h_dcnt_knd_cd1": "153"},
                            {"h_seat_no": "1B", "h_rcvd_amt": "23900"},
                        ]
                    },
                }
            ]
        },
        "psg_infos": {"psg_info": [{"h_psg_tp_cd": "1", "h_psg_info_per_prnb": "2"}]},
        "unmodeled": {"preserved": True},
    }


@pytest.fixture
def existing_client(detail_raw, scripted_client_factory, f8_logged_in_session):
    client, requests, _ = scripted_client_factory(
        [detail_raw],
        config=KorailConfig(
            base_url="https://api.example.invalid",
            netfunnel_url="https://queue.example.invalid",
            key="SYNTHETIC-APP-KEY",
        ),
        session=f8_logged_in_session,
        repeat=True,
    )
    client.http.cookies.set("JSESSIONID", f8_logged_in_session.jsessionid)
    return client, requests


@pytest.mark.parametrize("payment_flag_present", [True, False])
@pytest.mark.parametrize("sequences_present,payment_result", [(True, "FAIL"), (False, "SUCC")])
def test_read_existing_reservation_then_explicitly_pay(
    payment_flag_present: bool,
    sequences_present: bool,
    payment_result: str,
    detail_raw: dict[str, Any],
    f8_client_factory: Callable[..., KorailClient],
) -> None:
    if not payment_flag_present:
        detail_raw.pop("h_payment_flg")
    if not sequences_present:
        detail_raw.pop("h_tmp_job_sqno1")
        detail_raw.pop("h_tmp_job_sqno2")
        detail_raw["jrny_infos"]["jrny_info"][0].pop("h_rsv_chg_no")
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == DETAIL_PATH:
            assert request.method == "POST"
            assert not request.url.query
            assert parse_qs(request.content.decode()) == {
                "Device": ["AD"],
                "Version": ["250601003"],
                "AppVersion": ["7.0.8"],
                "Key": ["SYNTHETIC-APP-KEY"],
                "hidPnrNo": [PNR],
            }
            return httpx.Response(200, json=detail_raw)
        if request.url.path == "/ts.wseq":
            return httpx.Response(200, text="200:key=SYNTHETIC-QUEUE")
        assert request.url.path == PAYMENT_PATH
        form = parse_qs(request.content.decode())
        assert form["hidPnrNo"] == [PNR]
        assert form["hidWctNo"] == ["SYNTHETIC-ACTUAL-WINDOW"]
        assert form["hidMnsStlAmt1"] == ["53900"]
        assert form["hidTmpJobSqno1"] == ["001234" if sequences_present else "000000"]
        assert form["hidTmpJobSqno2"] == ["005678" if sequences_present else "000000"]
        assert form["hidRsvChgNo"] == ["009" if sequences_present else "000"]
        # Server declines still return a FAIL model; the payment must not be retried.
        return httpx.Response(200, json={"strResult": payment_result, "h_msg_cd": "SYNTHETIC-DECLINED"})

    client = f8_client_factory(handler)
    hold = client.get_reservation_hold(PNR)
    assert type(hold) is ReservationHoldResponse
    assert hold.raw == detail_raw
    assert hold.received_amount == "53900" and hold.total_price == "99999"
    assert hold.journey_count == "0001" and hold.payable
    assert hold.payment_flag == ("Y" if payment_flag_present else None)
    assert hold.payment_deadline_date == "20990102" and hold.payment_deadline_time == "090000"
    assert hold.passengers[0].passenger_count == "2"
    assert hold.journeys[0].raw == detail_raw["jrny_infos"]["jrny_info"][0]
    assert hold.temporary_job_sequence_1 == ("001234" if sequences_present else None)
    assert hold.temporary_job_sequence_2 == ("005678" if sequences_present else None)
    assert hold.journeys[0].reservation_change_no == ("009" if sequences_present else None)
    assert len(calls) == 1  # Reading never reserves, queues, or charges.
    result = client.pay_with_card(hold, CardPayment("0" * 16, "00", "9912", "000101"))
    assert result.str_result == payment_result
    assert [request.url.params.get("opcode", request.url.path) for request in calls] == [
        DETAIL_PATH,
        "5101",
        PAYMENT_PATH,
        "5004",
    ]


@pytest.mark.parametrize("declared", [ABSENT, "55200", "00055200", 55200])
def test_transfer_uses_all_journeys_and_actual_change_number(
    existing_client, declared: object, detail_raw: dict[str, Any]
) -> None:
    detail_raw["h_jrny_cnt"] = 2
    second = deepcopy(detail_raw["jrny_infos"]["jrny_info"][0])
    second.update(h_jrny_sqno="0002", h_trn_no="90002")
    second["seat_infos"]["seat_info"] = [{"h_seat_no": "2A", "h_rcvd_amt": 1300}]
    detail_raw["jrny_infos"]["jrny_info"].append(second)
    if declared is ABSENT:
        detail_raw.pop("h_tot_rcvd_amt")
    else:
        detail_raw["h_tot_rcvd_amt"] = declared
    client, requests = existing_client
    hold = client.get_reservation_hold(PNR)
    assert hold.received_amount == "55200" and len(hold.journeys) == 2
    assert hold.journeys[0].reservation_change_no == "009"
    assert [request.url.path for request in requests] == [DETAIL_PATH]


@pytest.mark.parametrize(
    "field,value",
    [
        ("h_pnr_no", "ANOTHER-PNR"),
        ("h_pnr_no", ABSENT),
        ("h_wct_no", ABSENT),
        ("h_wct_no", None),
        ("h_wct_no", " "),
        ("h_wct_no", False),
        *[("h_payment_flg", value) for value in (None, "", "N", "UNKNOWN", True)],
        *[("h_jrny_cnt", value) for value in (ABSENT, None, 0, 2, True, "-1", "1.0")],
        *[("h_tot_rcvd_amt", value) for value in (None, "", "53,900", "-53900", True, 53900.0, "53000")],
        ("jrny_infos", ABSENT),
        ("jrny_infos", None),
        ("jrny_infos", {"jrny_info": []}),
        ("jrny_infos", {"jrny_info": [None]}),
        ("jrny_infos", {"jrny_info": {}}),
        ("strResult", None),
        ("strResult", "UNKNOWN"),
    ],
)
def test_unusable_details_preserve_raw_and_do_not_pay(
    existing_client, field: str, value: object, detail_raw: dict[str, Any]
) -> None:
    if value is ABSENT:
        detail_raw.pop(field)
    else:
        detail_raw[field] = value
    client, requests = existing_client
    with pytest.raises(KorailProtocolError) as caught:
        client.get_reservation_hold(PNR)
    assert caught.value.raw == detail_raw
    assert [request.url.path for request in requests] == [DETAIL_PATH]


@pytest.mark.parametrize(
    "seat_infos",
    [
        None,
        {},
        {"seat_info": None},
        {"seat_info": []},
        {"seat_info": [None]},
        {"seat_info": [{}]},
        *[
            {"seat_info": [{"h_seat_no": "1A", "h_rcvd_amt": amount}]}
            for amount in ("53,900", "-53900", "+53900", "５３９００", True, None, "", 53900.0)
        ],
        # No assigned seat and zero price is an observed standby shape, even if a flag says Y.
        {"seat_info": [{"h_seat_no": "", "h_rcvd_amt": "0"}]},
    ],
)
def test_missing_or_invalid_seat_amounts_are_not_replaced_with_a_total(
    existing_client, seat_infos: object, detail_raw: dict[str, Any]
) -> None:
    detail_raw["jrny_infos"]["jrny_info"][0]["seat_infos"] = seat_infos
    client, requests = existing_client
    with pytest.raises(KorailProtocolError) as caught:
        client.get_reservation_hold(PNR)
    assert caught.value.raw == detail_raw
    assert [request.url.path for request in requests] == [DETAIL_PATH]


@pytest.mark.parametrize("payment_flag_present", [True, False])
def test_zero_amount_and_incomplete_transfer_are_rejected(
    existing_client, payment_flag_present: bool, detail_raw: dict[str, Any]
) -> None:
    if not payment_flag_present:
        detail_raw.pop("h_payment_flg")
    detail_raw["h_tot_rcvd_amt"] = "0"
    detail_raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"] = [
        {"h_seat_no": "1A", "h_rcvd_amt": "0"}
    ]
    client, requests = existing_client
    with pytest.raises(KorailProtocolError, match="positive"):
        client.get_reservation_hold(PNR)
    detail_raw["h_jrny_cnt"] = "2"
    detail_raw["jrny_infos"]["jrny_info"].append({"h_jrny_sqno": "0002"})
    with pytest.raises(KorailProtocolError, match="seat_infos"):
        client.get_reservation_hold(PNR)
    assert [request.url.path for request in requests] == [DETAIL_PATH, DETAIL_PATH]


@pytest.mark.skipif(sys.get_int_max_str_digits() == 0, reason="runtime has no integer string limit")
def test_oversized_seat_sum_preserves_raw(existing_client, detail_raw: dict[str, Any]) -> None:
    detail_raw.pop("h_tot_rcvd_amt")
    for seat in detail_raw["jrny_infos"]["jrny_info"][0]["seat_infos"]["seat_info"]:
        seat["h_rcvd_amt"] = "9" * sys.get_int_max_str_digits()
    client, requests = existing_client
    with pytest.raises(KorailProtocolError, match="unsupported numeric") as caught:
        client.get_reservation_hold(PNR)
    assert caught.value.raw == detail_raw
    assert [request.url.path for request in requests] == [DETAIL_PATH]


@pytest.mark.parametrize("pnr_no", [None, "", " ", 123, False])
def test_invalid_pnr_never_sends(pnr_no: Any, f8_client_factory: Callable[..., KorailClient]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("invalid input must not send a request")

    with pytest.raises(KorailProtocolError):
        f8_client_factory(handler).get_reservation_hold(pnr_no)


def test_login_required(f8_client_factory: Callable[..., KorailClient]) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("unauthenticated reads must not send a request")

    with pytest.raises(KorailAuthError):
        f8_client_factory(handler, logged_in=False).get_reservation_hold(PNR)


@pytest.mark.parametrize("code", ["P058", "SYNTHETIC-MISSING-RESERVATION"])
def test_server_refusal_keeps_error_and_clears_expired_session(
    existing_client, detail_raw: dict[str, Any], code: str
) -> None:
    raw = {"strResult": "FAIL", "h_msg_cd": code}
    detail_raw.clear()
    detail_raw.update(raw)
    client, requests = existing_client
    with pytest.raises(KorailSessionExpiredError if code == "P058" else KorailAppError) as caught:
        client.get_reservation_hold(PNR)
    assert caught.value.raw == raw and len(requests) == 1
    if code == "P058":
        assert client.session.current is None and not client.http.cookies


def test_transport_failure_is_not_retried(scripted_client_factory, f8_logged_in_session) -> None:
    client, requests, _ = scripted_client_factory(
        [httpx.ReadTimeout("synthetic")],
        config=KorailConfig(base_url="https://api.example.invalid"),
        session=f8_logged_in_session,
    )
    with pytest.raises(KorailTransportError):
        client.get_reservation_hold(PNR)
    assert len(requests) == 1
