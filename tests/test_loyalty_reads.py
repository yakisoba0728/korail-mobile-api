from __future__ import annotations

from urllib.parse import parse_qsl

import httpx
import pytest

import korail_mobile_api
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
    EXCLUDED_API_DOMAINS,
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_MUTATION_ROUTES,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
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


def _envelope(**extra: object) -> dict[str, object]:
    return {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "정상처리되었습니다",
        "strResult": "SUCC",
        **extra,
    }


def _client(handler) -> KorailClient:
    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="SYNTHETIC_SESSION",
        member_no="SYNTHETIC_MEMBER_NO",
        customer_no="SYNTHETIC_CUSTOMER_NO",
        raw={},
    )
    return client


def test_only_the_two_password_free_loyalty_reads_are_reachable():
    assert len(KORAIL_READ_ONLY_ROUTES) == 60
    assert ("POST", SUMMARY_PATH) in KORAIL_READ_ONLY_ROUTES
    assert ("POST", MILEAGE_PATH) in KORAIL_READ_ONLY_ROUTES
    for path in WITHHELD_PATHS:
        for method in ("GET", "POST"):
            assert (method, path) not in KORAIL_READ_ONLY_ROUTES
            assert (method, path) not in KORAIL_MUTATION_ROUTES
        with pytest.raises(KorailProtocolError):
            assert_read_only_route("POST", path)


def test_the_excluded_domain_label_narrowed_to_writes_only():
    # The label was "points-mileage", which also excluded balance reads. The
    # new label names what is still refused and nothing more.
    assert "points-mileage" not in EXCLUDED_API_DOMAINS
    assert "points-mileage-write" in EXCLUDED_API_DOMAINS
    # Narrowing this one label must not have relaxed any other domain.
    assert {
        "reservation",
        "payment",
        "refund",
        "check-in",
        "member-drop",
        "push-sms",
        "dynapath-token-generation",
    } <= EXCLUDED_API_DOMAINS
    assert len(EXCLUDED_API_DOMAINS) == 8


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


def test_mileage_form_refuses_a_lookalike_request():
    class Lookalike(MileageHistoryRequest):
        pass

    with pytest.raises(TypeError):
        build_mileage_history_form(
            Lookalike(start_date="20990101", end_date="20990331")
        )


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
    def handler(_: httpx.Request) -> httpx.Response:
        raise AssertionError("no request may be sent without a session")

    client = KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
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
