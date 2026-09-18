# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""Offline checks for the confirmed KORAIL Talk 7.0.6 contract changes."""

import httpx
import pytest

from korail_mobile_api import BaseKorailResponse, KorailConfig, TrainSearchQuery
from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.http import KorailHttpClient
from korail_mobile_api.mutation_parsers import parse_refund_ticket_response
from korail_mobile_api.netfunnel import parse_queue_response
from korail_mobile_api.payloads import build_train_search_form
from korail_mobile_api.read_parsers import (
    parse_refund_ticket_detail_response,
    parse_ticket_list_response,
)


def test_v7_ticket_list_uses_the_nested_snake_case_wire_keys():
    raw = {
        "strResult": "SUCC",
        "pnr_list": [
            {
                "h_pnr_no": "SYNTHETIC_PNR",
                "ticket_list": [
                    {
                        "h_pnr_no": "SYNTHETIC_PNR",
                        "h_orgtk_wct_no": "SYNTHETIC_WINDOW",
                        "h_orgtk_ret_sale_dt": "20990101",
                        "h_orgtk_sale_sqno": "0001",
                        "h_orgtk_ret_pwd": "SYNTHETIC_PASSWORD",
                        "jrn_info": [{"h_trn_no": "00101"}],
                    }
                ],
            }
        ],
    }
    result = parse_ticket_list_response(BaseKorailResponse.from_raw(raw))
    ticket = result.reservations[0].tickets[0]
    assert ticket.return_sale_date == "20990101"
    assert ticket.train_info[0]["h_trn_no"] == "00101"
    assert "SYNTHETIC_PASSWORD" not in repr(ticket)
    for bad in ({"pnr_list": {}}, {"pnr_list": [{"ticket_list": {}}]}):
        with pytest.raises(KorailProtocolError):
            parse_ticket_list_response(
                BaseKorailResponse.from_raw({"strResult": "SUCC", **bad})
            )


def test_v7_no_argument_post_has_no_common_form_or_content_type():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    for path in (
        "/classes/com.korail.mobile.common.stationinfo",
        "/classes/com.korail.mobile.common.stationdata",
        "/ebizcross/getUUID.do",
    ):
        client.post_form(path, include_common=False, form_encoded=False)
    assert [request.method for request in seen] == ["POST"] * 3
    assert all(request.content == b"" and request.url.query == b"" for request in seen)
    assert all("content-type" not in request.headers for request in seen)


def test_v7_search_passenger_types_and_seat_attribute_reach_the_form():
    positional_query = TrainSearchQuery(
        "0001", "0002", "20990101", "000000", 1, "101"
    )
    assert positional_query.train_group_code == "101"
    form = build_train_search_form(
        KorailConfig(),
        TrainSearchQuery(
            "0001",
            "0002",
            "20990101",
            passengers=1,
            child_passengers=2,
            senior_passengers=1,
            high_disability_passengers=1,
            low_disability_passengers=1,
            seat_attribute_code="009",
        ),
        departure_name="SYNTHETIC_START",
        arrival_name="SYNTHETIC_END",
        sid="SYNTHETIC_SID",
    )
    assert [form[f"txtPsgFlg_{index}"] for index in range(1, 6)] == [
        "1", "2", "1", "1", "1"
    ]
    assert form["txtSeatAttCd_4"] == "009"


def test_v7_refund_settlement_and_netfunnel_303_are_parsed():
    result = parse_refund_ticket_response(
        {"strResult": "SUCC", "stlList": [{"stl_mns_cd": "SYNTHETIC_METHOD"}]}
    )
    assert result.settlement_method_codes == ("SYNTHETIC_METHOD",)
    for incomplete in (
        {"strResult": "SUCC"},
        {"strResult": "SUCC", "stlList": [{}]},
    ):
        with pytest.raises(KorailProtocolError):
            parse_refund_ticket_response(incomplete)
    assert parse_queue_response(
        "303:key=ABC123&nwait=0&ttl=0", action="act_8"
    ).code == "303"


def test_refund_detail_reads_both_known_and_inferred_pbp_names():
    envelope = {"h_msg_cd": "IRG000000", "h_msg_txt": "", "strResult": "SUCC"}
    assert parse_refund_ticket_detail_response(
        {**envelope, "pbpAcepTgtFlg": "Y"}
    ).pbp_acceptance_target_flag == "Y"
    assert parse_refund_ticket_detail_response(
        {**envelope, "h_pbp_acep_tgt_flg": "N"}
    ).pbp_acceptance_target_flag == "N"
