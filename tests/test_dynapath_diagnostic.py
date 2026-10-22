"""SDK 2.0.1 diagnostic header contracts; synthetic transport only."""

import pickle

from conftest import synthetic_config

from korail_mobile_api import (
    DynapathConfig,
    DynapathRequestContext,
    KorailDeviceProfile,
    build_config_from_profile,
)
from korail_mobile_api._core.dynapath import build_default_token_settings


def test_default_client_uses_diagnostic_header_without_extra_requests(scripted_client_factory):
    client, requests, _ = scripted_client_factory([{"strResult": "SUCC", "h_msg_cd": "SYNTHETIC"}], repeat=True)
    login = "/classes/com.korail.mobile.login.Login"
    for path in (login, login, "/synthetic-unprotected"):
        client.http.post_form(path)
    expected = "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
    assert [request.headers.get("x-dynapath-m-token") for request in requests] == [expected, expected, None]
    assert [request.url.path for request in requests] == [login, login, "/synthetic-unprotected"]
    assert client.config.dynapath.token_settings is None
    restored = pickle.loads(pickle.dumps(client.config))
    assert restored == client.config
    names = "method path url device version key user_agent device_name os_version".split()
    assert (
        restored.dynapath.token_provider(DynapathRequestContext(**dict.fromkeys(names, "synthetic")))
        == expected
    )


def test_explicit_legacy_settings_still_select_v1(scripted_client_factory):
    settings = build_default_token_settings()
    config = synthetic_config(
        netfunnel_enabled=False, dynapath=DynapathConfig(enabled=True, token_settings=settings)
    )
    config = build_config_from_profile(
        KorailDeviceProfile(
            device_id="synthetic-install",
            model="synthetic-model",
            android_release="16",
            build_id="synthetic-build",
        ),
        base=config,
    )
    assert config.dynapath.token_settings.device_id == "synthetic-install"
    client, requests, _ = scripted_client_factory([{"strResult": "SUCC"}], config=config)
    client.http.post_form("/classes/com.korail.mobile.login.Login")
    assert client.config.dynapath.token_provider is None and settings.sdk_version == "v1.0.3"
    assert requests[0].headers["x-dynapath-m-token"].startswith("bEeEP")
