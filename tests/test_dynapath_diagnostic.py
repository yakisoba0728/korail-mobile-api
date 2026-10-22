"""SDK 2.0.1 diagnostic header contracts; synthetic transport only."""

import pickle

import httpx

from korail_mobile_api import (
    DynapathConfig,
    DynapathRequestContext,
    KorailConfig,
    KorailDeviceProfile,
    build_config_from_profile,
)
from korail_mobile_api.dynapath import build_default_token_settings


def test_default_client_uses_diagnostic_header_without_extra_requests(f8_client_factory):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"strResult": "SUCC", "h_msg_cd": "SYNTHETIC"})

    client = f8_client_factory(handler, logged_in=False)
    login = "/classes/com.korail.mobile.login.Login"
    for path, include in [(login, True), (login, True), ("/synthetic-unprotected", True), (login, False)]:
        client.http.post_form(path, include_dynapath=include)
    expected = "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
    assert [request.headers.get("x-dynapath-m-token") for request in requests] == [
        expected,
        expected,
        None,
        None,
    ]
    assert [request.url.path for request in requests] == [login, login, "/synthetic-unprotected", login]
    assert client.config.dynapath.token_settings is None
    restored = pickle.loads(pickle.dumps(client.config))
    assert restored == client.config
    assert restored.dynapath.token_provider(DynapathRequestContext(*("synthetic",) * 9)) == expected


def test_explicit_legacy_settings_still_select_v1(f8_client_factory):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"strResult": "SUCC"})

    settings = build_default_token_settings()
    config = KorailConfig(
        base_url="https://api.example.invalid",
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_settings=settings),
    )
    config = build_config_from_profile(
        KorailDeviceProfile("synthetic-install", "synthetic-model", "16", "synthetic-build"), base=config
    )
    assert config.dynapath.token_settings.device_id == "synthetic-install"
    client = f8_client_factory(handler, config=config)
    client.http.post_form("/classes/com.korail.mobile.login.Login")
    assert client.config.dynapath.token_provider is None and settings.sdk_version == "v1.0.3"
    assert requests[0].headers["x-dynapath-m-token"].startswith("bEeEP")
