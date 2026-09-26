"""Offline regressions for cleanup; application references use the supplied 7.0.6 sources."""

from __future__ import annotations

from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig


@pytest.mark.parametrize("lang", [None, "synthetic-language"])
@pytest.mark.parametrize("optional", [False, True])
def test_login_form_matches_dto_declaration_order(lang: str | None, optional: bool) -> None:
    """LoginIn.java:57-80,141-164; CommonIn.java:467-474; NetworkService.java:15335-15392."""
    seen: list[httpx.Request] = []
    replies = iter(
        [
            {"strResult": "SUCC"},
            {
                "strResult": "SUCC",
                "app.login.cphd": {"idx": "synthetic-index", "key": "0123456789abcdef"},
            },
            {"strResult": "SUCC", "h_msg_cd": "IRZ000001"},
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json=next(replies),
            headers={"Set-Cookie": "JSESSIONID=synthetic-session; Path=/"},
        )

    config = KorailConfig(
        base_url="https://api.example.invalid",
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_provider=lambda context: "synthetic-token"),
        lang=lang,
    )
    client = KorailClient(config, transport=httpx.MockTransport(handler))
    try:
        client.login(
            "0000000000",
            "synthetic-password",
            cust_id="synthetic-customer" if optional else None,
            etr_path="synthetic-entry" if optional else None,
        )
    finally:
        client.close()
    assert [request.url.path for request in seen] == [
        "/file/CACHE/MobileService.cache",
        "/classes/com.korail.mobile.common.code.do",
        "/classes/com.korail.mobile.login.Login",
    ]
    pairs = parse_qsl(seen[-1].content.decode("ascii"), keep_blank_values=True)
    expected = ["Device", "Version", "Key"]
    if lang is not None:
        expected.append("lang")
    expected.extend(["txtInputFlg", "txtMemberNo", "txtPwd"])
    if optional:
        expected.append("custId")
    expected.append("checkValidPw")
    if optional:
        expected.append("etrPath")
    expected.append("idx")
    assert [name for name, _ in pairs] == expected
    values = dict(pairs)
    assert values["txtInputFlg"] == "2"
    assert values["txtMemberNo"] == "0000000000"
    assert values["checkValidPw"] == "Y"
    assert values["idx"] == "synthetic-index"
    assert seen[-1].headers["User-Agent"] == "korailtalk"


@pytest.mark.parametrize("key", ["h_msg_cd", "h_msg_txt", "strResult"])
@pytest.mark.parametrize("entrypoint", ["http", "parser", "model"])
def test_oversized_envelope_integer_is_protocol_error_with_raw(key: str, entrypoint: str) -> None:
    """checks/BEHAVIOR.md (스칼라·봉투): numeric strings normalize; rejected responses retain the entire raw object."""
    import sys

    from korail_mobile_api import BaseKorailResponse, KorailProtocolError
    from korail_mobile_api.http import parse_base_response
    from korail_mobile_api.read_parsers import parse_delay_return_receipt_response

    parsers = {
        "http": parse_base_response,
        "parser": parse_delay_return_receipt_response,
        "model": BaseKorailResponse.from_raw,
    }
    raw = {"strResult": "SUCC", key: 10**700, "extra": {"synthetic": True}}
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        with pytest.raises(KorailProtocolError) as error:
            parsers[entrypoint](raw)
        assert error.value.raw is raw
    finally:
        sys.set_int_max_str_digits(previous)


def test_base_response_from_raw_normalizes_envelope_without_classifying_status() -> None:
    from korail_mobile_api import BaseKorailResponse

    raw = {"h_msg_cd": 12, "h_msg_txt": 34, "strResult": 56}
    result = BaseKorailResponse.from_raw(raw)
    assert (result.h_msg_cd, result.h_msg_txt, result.str_result) == ("12", "34", "56")
    assert result.raw is raw
    assert BaseKorailResponse.from_raw({"strResult": "FAIL", "h_msg_cd": "P058"}).h_msg_cd == "P058"
    assert BaseKorailResponse.from_raw({}).str_result is None


@pytest.mark.parametrize("value", [True, 1.5, [], {}])
def test_base_response_from_raw_rejects_invalid_envelope_values(value: object) -> None:
    from korail_mobile_api import BaseKorailResponse, KorailProtocolError

    raw = {"strResult": "SUCC", "h_msg_txt": value, "extra": "synthetic"}
    with pytest.raises(KorailProtocolError) as error:
        BaseKorailResponse.from_raw(raw)
    assert error.value.raw is raw


def test_base_response_from_raw_retains_non_object_on_rejection() -> None:
    from korail_mobile_api import BaseKorailResponse, KorailProtocolError

    raw = ["synthetic"]
    with pytest.raises(KorailProtocolError) as error:
        BaseKorailResponse.from_raw(raw)
    assert error.value.raw is raw


@pytest.mark.parametrize("value", [True, 1.5, [], {}, "20300102", 20300102, None])
def test_optional_delay_run_date_uses_optional_scalar_policy(value: object) -> None:
    """DelayCertificate.java:57-60 differs from the observed optional runDt; checks/BEHAVIOR.md governs it."""
    from korail_mobile_api.read_parsers import parse_delay_certificate_response

    row = {
        "runDay": "synthetic-day",
        "trnNo": "00001",
        "dptRsStnCd": "0001",
        "arvRsStnCd": "0002",
        "arvRsStnNm": "synthetic-station",
        "dlayArvFlg": "Y",
        "trnDlayTm": "20",
        "runDt": value,
    }
    raw = {"strResult": "SUCC", "dlayList": [row]}
    parsed = parse_delay_certificate_response(raw)
    expected = str(value) if type(value) in (int, str) else None
    assert parsed.delays[0].run_date == expected
    assert parsed.delays[0].raw is row
    assert parsed.raw is raw


@pytest.mark.parametrize("key", ["h_psg_tp_cd", "h_psrm_cl_cd", "h_dcnt_knd_cd1", "dcnt_reld_no"])
def test_recalculation_from_hold_keeps_raw_on_oversized_integer(key: str) -> None:
    """ReservationOutSeatInfo.java:80–109 declares strings; conversion errors must preserve the hold."""
    import sys

    from korail_mobile_api import KorailProtocolError, PriceRecalculationRequest, ReservationHoldResponse
    from korail_mobile_api.mutation_models import ReservationJourney

    seat = {key: 10**700}
    journey_raw = {"seat_infos": {"seat_info": [seat]}}
    raw = {"strResult": "SUCC", "synthetic_journey": journey_raw}
    hold = ReservationHoldResponse(
        str_result="SUCC",
        pnr_no="SYNTHETIC-PNR",
        journeys=(ReservationJourney(raw=journey_raw),),
        raw=raw,
    )
    previous = sys.get_int_max_str_digits()
    try:
        sys.set_int_max_str_digits(640)
        with pytest.raises(KorailProtocolError) as error:
            PriceRecalculationRequest.for_hold(hold, ["SYNTHETIC-DISCOUNT"])
        assert error.value.raw is raw
        assert error.value.parser_raw is seat
        assert isinstance(error.value.__cause__, ValueError)
    finally:
        sys.set_int_max_str_digits(previous)
