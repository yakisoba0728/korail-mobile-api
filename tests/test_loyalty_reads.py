# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

from __future__ import annotations

from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
from _helpers import korail_ok_envelope as _envelope
from _helpers import make_authenticated_client as _client
from _helpers import no_network_client
from _read_field_contracts import (
    KORAIL_EXACT_REQUEST_FIELDS,
    assert_read_only_request_fields,
)
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import KorailAuthError, KorailProtocolError
from korail_mobile_api.models import KorailSession
from korail_mobile_api.read_models import (
    KorailPointSummaryResponse,
    MileageHistoryResponse,
)
from korail_mobile_api.read_parsers import (
    parse_korail_point_summary_response,
    parse_mileage_history_response,
)
from korail_mobile_api.read_payloads import (
    KORAIL_MILEAGE_LEDGER_KTX,
    KORAIL_MILEAGE_LEDGER_RAIL_POINT,
    KORAIL_MILEAGE_MOVEMENT_ALL,
    KORAIL_MILEAGE_MOVEMENT_SPENT,
    MileageHistoryRequest,
    build_korail_point_summary_form,
    build_mileage_history_form,
)
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_route,
)


SUMMARY_PATH = "/classes/com.korail.mobile.xPoint.MyXPointView"
MILEAGE_PATH = "/classes/com.korail.mobile.mlg.amtSpec.do"

# The loyalty routes that stay out, each because it changes state rather than
# because of its category. See the EXCLUDED_API_DOMAINS comment in safety.py.
WITHHELD_PATHS = (
    "/classes/com.korail.mobile.mlg.lpotAthn.do",
    "/classes/com.korail.mobile.xPoint.XPointView",
    "/classes/com.korail.mobile.xPoint.OkCashbagCertView",
    "/classes/com.korail.mobile.mileage.acpnMlgSave.do",
    "/classes/com.korail.mobile.mileage.acpnMlgNoti.do",
)





def test_only_the_two_password_free_loyalty_reads_are_reachable():
    assert ("POST", SUMMARY_PATH) in KORAIL_READ_ONLY_ROUTES
    assert ("POST", MILEAGE_PATH) in KORAIL_READ_ONLY_ROUTES
    for path in WITHHELD_PATHS:
        for method in ("GET", "POST"):
            assert (method, path) not in KORAIL_READ_ONLY_ROUTES
            assert (method, path) not in KORAIL_MUTATION_ROUTES
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("POST", path)


def test_point_summary_form_is_the_daos_own_constant():
    assert build_korail_point_summary_form() == {"point_dv_cd": "0"}
    assert KORAIL_EXACT_REQUEST_FIELDS[SUMMARY_PATH] == frozenset(
        {"Device", "Version", "Key", "point_dv_cd"}
    )


def test_mileage_form_defaults_to_the_screens_own_choices():
    form = build_mileage_history_form(
        MileageHistoryRequest(start_date="20990101", end_date="20990331")
    )
    assert form == {
        "pontTpVal": KORAIL_MILEAGE_LEDGER_KTX,
        "qryDvVal": KORAIL_MILEAGE_MOVEMENT_ALL,
        "qryStDt": "20990101",
        "qryClsDt": "20990331",
        "pgPrCnt": "20",
        "nowPgNo": "1",
    }
    assert_read_only_request_fields(
        MILEAGE_PATH,
        {"Device": "AD", "Version": "v", "Key": "k", **form},
    )
    other = build_mileage_history_form(
        MileageHistoryRequest(
            start_date="20990101",
            end_date="20990331",
            ledger=KORAIL_MILEAGE_LEDGER_RAIL_POINT,
            movement=KORAIL_MILEAGE_MOVEMENT_SPENT,
            page_no=3,
        )
    )
    assert other["pontTpVal"] == "2"
    assert other["qryDvVal"] == "2"
    assert other["nowPgNo"] == "3"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"ledger": "3"},
        {"movement": "9"},
        {"page_no": 0},
        {"start_date": "2099-01-01"},
        {"end_date": ""},
        # A reversed window would silently return nothing rather than fail.
        {"start_date": "20990401", "end_date": "20990331"},
    ],
)
def test_mileage_form_refuses_out_of_contract_inputs(kwargs):
    fields = {"start_date": "20990101", "end_date": "20990331", **kwargs}
    with pytest.raises(ValueError):
        build_mileage_history_form(MileageHistoryRequest(**fields))


def test_mileage_form_refuses_a_non_request_value():
    with pytest.raises(TypeError):
        build_mileage_history_form(object())


def test_point_summary_parser_exposes_the_welfare_registration():
    parsed = parse_korail_point_summary_response(
        _envelope(
            h_korail_point="1234",
            h_disc_coup_cnt="2",
            h_delay_cnt="1",
            h_hdcp_flg="Y",
            h_subt_dcs_cl_cd="01",
            h_subt_dcs_cl_nm="중증",
            h_cust_lead_flg_nm="보조견 동반",
            h_cp_athn_flg="Y",
            h_emil_athn_flg="N",
            h_cntc_chn_cont1="",
            h_logn_tp_cd1="N",
            h_logn_tp_cd2="Y",
            h_logn_tp_cd4="N",
            h_logn_tp_cd5="N",
        )
    )
    assert type(parsed) is KorailPointSummaryResponse
    # MyPageActivity.java:206-212: this flag alone reveals the 장애인 section,
    # and the two names below are what it renders under 장애인증 / 보조견.
    assert parsed.disability_flag == "Y"
    assert parsed.welfare_discount_class_name == "중증"
    assert parsed.customer_lead_flag_name == "보조견 동반"
    assert parsed.korail_point == "1234"
    assert parsed.discount_coupon_count == "2"
    assert parsed.delay_discount_count == "1"
    assert parsed.kakao_linked_flag == "Y"
    # A numeric balance is accepted too; nothing here has been seen live.
    assert (
        parse_korail_point_summary_response(
            _envelope(h_korail_point=1234)
        ).korail_point
        == "1234"
    )


def test_mileage_parser_reads_totals_and_rows():
    parsed = parse_mileage_history_response(
        _envelope(
            pgCnt="3",
            qryCnt="18",
            totAvlRailPontValNum="1000",
            totAvlRailPontValNum1="500",
            totAvlAfltPontValNum="20",
            totAcmRailPontValNum1="9000",
            totUseRailPontValNum1="8500",
            railNowSavePontValNum1="100",
            delPontValNum="30",
            ktxMlgInfo="안내",
            specList=[
                {
                    "dptDt": "20990101",
                    "pontDvNm": "적립",
                    "mlgAcmDvCdNm": "승차권",
                    "rcpDvNm": "카드",
                    "pontAmt": 250,
                    "savePontValNum": "1000",
                    "stlAmt": "50000",
                }
            ],
        )
    )
    assert type(parsed) is MileageHistoryResponse
    assert parsed.page_count == "3"
    assert parsed.query_count == "18"
    assert parsed.total_available_rail_point == "1000"
    assert parsed.total_available_rail_point_1 == "500"
    assert parsed.expiring_point_value == "30"
    assert len(parsed.entries) == 1
    assert parsed.entries[0].point_amount == "250"
    assert parsed.entries[0].point_division_name == "적립"
    assert parse_mileage_history_response(_envelope()).entries == ()


def test_parsers_refuse_malformed_bodies():
    with pytest.raises(KorailProtocolError):
        parse_mileage_history_response(_envelope(specList={"nope": 1}))
    with pytest.raises(KorailProtocolError):
        parse_korail_point_summary_response(_envelope(h_hdcp_flg=["Y"]))


def test_client_reads_send_exactly_the_registered_forms():
    seen: list[tuple[str, str, dict[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.method,
                request.url.path,
                dict(parse_qsl(request.content.decode())),
            )
        )
        return httpx.Response(200, json=_envelope())

    client = _client(handler)
    try:
        client.get_korail_point_summary()
        client.get_mileage_history(
            MileageHistoryRequest(start_date="20990101", end_date="20990331")
        )
    finally:
        client.close()

    assert seen[0][:2] == ("POST", SUMMARY_PATH)
    assert seen[0][2] == {
        "Device": "AD",
        "Version": client.config.version,
        "Key": client.config.key,
        "point_dv_cd": "0",
    }
    assert seen[1][:2] == ("POST", MILEAGE_PATH)
    assert set(seen[1][2]) == {
        "Device",
        "Version",
        "Key",
        "pontTpVal",
        "qryDvVal",
        "qryStDt",
        "qryClsDt",
        "pgPrCnt",
        "nowPgNo",
    }


def test_loyalty_reads_require_a_session():
    client = no_network_client()
    try:
        with pytest.raises(KorailAuthError):
            client.get_korail_point_summary()
        with pytest.raises(KorailAuthError):
            client.get_mileage_history(
                MileageHistoryRequest(
                    start_date="20990101",
                    end_date="20990331",
                )
            )
    finally:
        client.close()


def test_public_surface_exports_the_loyalty_names():
    for name in (
        "KorailPointSummaryResponse",
        "MileageHistoryEntry",
        "MileageHistoryRequest",
        "MileageHistoryResponse",
        "KORAIL_MILEAGE_LEDGER_KTX",
        "KORAIL_MILEAGE_LEDGER_RAIL_POINT",
        "KORAIL_MILEAGE_MOVEMENT_ALL",
        "KORAIL_MILEAGE_MOVEMENT_EARNED",
        "KORAIL_MILEAGE_MOVEMENT_SPENT",
    ):
        assert name in korail_mobile_api.__all__
        assert hasattr(korail_mobile_api, name)
    # No spending path was added along with the reads.
    assert not hasattr(KorailClient, "spend_mileage")
    assert not hasattr(KorailClient, "get_lpoint")


def test_neither_loyalty_read_is_signed_with_dynapath():
    # The same check test_uuid_maas_read_apis.py makes: DynaPath on and both
    # routes allowlisted, so a read that asked for a token would reach the
    # provider. With DynaPath off, "no token header" would hold whatever the
    # client did.
    from korail_mobile_api.constants import DYNAPATH_HEADER_NAME
    from korail_mobile_api.dynapath import DynapathConfig

    provider_calls: list[object] = []
    seen: list[httpx.Request] = []

    def token_provider(context: object) -> str:
        provider_calls.append(context)
        return "SYNTHETIC-TOKEN"

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=_envelope())

    client = KorailClient(
        KorailConfig(
            dynapath=DynapathConfig(
                enabled=True,
                token_provider=token_provider,
                allowlist_paths=frozenset({SUMMARY_PATH, MILEAGE_PATH}),
            )
        ),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(jsessionid="SYNTHETIC_SESSION")
    try:
        client.get_korail_point_summary()
        client.get_mileage_history(
            MileageHistoryRequest(start_date="20990101", end_date="20990331")
        )
    finally:
        client.close()

    assert provider_calls == []
    assert [request.url.path for request in seen] == [SUMMARY_PATH, MILEAGE_PATH]
    assert all(DYNAPATH_HEADER_NAME not in request.headers for request in seen)
