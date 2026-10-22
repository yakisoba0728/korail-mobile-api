"""Independent, bounded 7.0.10 app facts, not goldens captured from this SDK.

Artifact: com.korail.talk, versionCode 70001000; base APK SHA256
2847ceb54ba7f7e26edf3426ed606bb1f7e7dfabacf01011d6d164eb45dc993b.
Evidence: NetworkApi.smali postDptnBank parameter @Field annotations (2039-2059)
and write$Self's CommonIn-first call in RefundCommissionIn (140-168) and RefundTicketIn (184-226).
Source SHA256 (local disassembly; source files need not ship with the tests):
NetworkApi: 85532050c4637f8ce756720233862689795fd0208aa84c820ef066d40c975b5a
RefundCommissionIn: 092952e234450d1d116da271a1f8488f4df5d75834cc5e836dadda5b325538d7
RefundTicketIn: 7efb10e4b83108661cf0f36e23ca98187cf2b6c81803f84f31c4b607fcca619d

The refund tests assert only inherited-before-own order, not protected defaults,
the final protected map, server order sensitivity or runtime equivalence.
"""

from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api import (
    KorailConfig,
    OriginalTicketReference,
    PaidTicket,
    RefundCompanion,
)

APP_CONTRACT = {
    "bank": {
        "path": "/classes/com.korail.mobile.dlay.dptnBank.do",
        "fields": ("Device", "Version", "Key", "AppVersion"),
    },
    "fee": {
        "path": "/classes/com.korail.mobile.refunds.CommissionView",
        "identity": "h_orgtk_ret_sale_dt",
    },
    "refund": {
        "path": "/classes/com.korail.mobile.refunds.RefundsRequest",
        "identity": "txtPnrNo",
    },
}


@pytest.mark.parametrize("app_version", [None, "7.0.10"])
@pytest.mark.parametrize("lang", [None, "ko"])
def test_observed_app_contract_subset(f8_client_factory, app_version, lang):
    seen = []

    def handler(request):
        assert request.method == "POST"
        assert request.url.query == b""
        seen.append(request)
        return httpx.Response(200, json={"strResult": "SUCC", "dptnBank": [], "stlList": []})

    client = f8_client_factory(
        handler,
        logged_in=True,
        config=KorailConfig(
            base_url="https://api.example.invalid",
            netfunnel_enabled=False,
            disable_dynapath=True,
            key="",  # Explicit @Field preserves this; flattened forms omit it below.
            app_version=app_version,
            lang=lang,
        ),
    )
    client.list_deposit_banks()
    expected_bank = list(APP_CONTRACT["bank"]["fields"])
    if app_version is None:
        expected_bank.remove("AppVersion")
    bank = list(parse_qsl(seen[0].content.decode(), keep_blank_values=True))
    assert seen[0].url.path == APP_CONTRACT["bank"]["path"]
    assert [key for key, _ in bank] == expected_bank
    assert ("Key", "") in bank
    assert "lang" not in dict(bank)

    original = OriginalTicketReference(
        sale_window_no="SYNTH-WINDOW", sale_date="0102", sale_sequence="1", return_password="SYNTH-PASSWORD"
    )
    companion = RefundCompanion(name="SYNTH-NAME", certificate_no="20990101")
    commission = client.get_refund_fee(original, companion)
    ticket = PaidTicket(
        pnr_no="SYNTH-PNR",
        sale_date="20990103",  # Current sale date is deliberately not the original MMDD.
        sale_window_no=original.sale_window_no,
        sale_sequence=original.sale_sequence,
        return_password=original.return_password,
        return_sale_date=original.sale_date,
        companion_name=companion.name,
        companion_certificate_no=companion.certificate_no,
    )
    client.refund(ticket, commission=commission, latitude="0", longitude="0")
    expected_common = ["Device", "Version"]
    if app_version is not None:
        expected_common.append("AppVersion")
    if lang is not None:
        expected_common.append("lang")
    for name, request in zip(("fee", "refund"), seen[1:], strict=True):
        assert request.url.path == APP_CONTRACT[name]["path"]
        pairs = parse_qsl(request.content.decode(), keep_blank_values=True)
        keys = [key for key, _ in pairs]
        assert keys[: len(expected_common)] == expected_common
        assert keys[len(expected_common)] == APP_CONTRACT[name]["identity"]
        assert "Key" not in keys
        assert len(keys) == len(set(keys))
        assert dict(pairs).get("AppVersion") == app_version
    fee_form = dict(parse_qsl(seen[1].content.decode()))
    refund_form = dict(parse_qsl(seen[2].content.decode()))
    assert fee_form["h_orgtk_ret_sale_dt"] == "0102"
    assert fee_form["h_comp_nm"] == companion.name
    assert fee_form["h_comp_cert_no"] == companion.certificate_no
    assert refund_form["h_orgtk_sale_dt"] == "20990103"
    assert refund_form["latitude"] == refund_form["longitude"] == "0"
    assert len(seen) == 3
