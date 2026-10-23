"""SDK 2.0.1 diagnostic header contracts; synthetic transport only."""

import pickle
from dataclasses import asdict, replace

import pytest
from conftest import synthetic_config
from test_auth_transport import ID, PASSWORD, bootstrap, login_response

from korail_mobile_api import (
    DynapathConfig,
    DynapathRequestContext,
    DynapathTokenSettings,
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


@pytest.mark.parametrize(
    "name",
    [
        "",
        "nonascii-한글",
        "has space",
        "has:colon",
        "has/separator",
        "tab\t",
        "cr\r",
        "lf\n",
        "nul\0",
        "del\x7f",
        None,
        123,
    ],
)
def test_dynapath_rejects_invalid_header_names_at_configuration(name):
    with pytest.raises(ValueError, match="header_name"):
        DynapathConfig(enabled=True, token_provider=lambda context: "synthetic-token", header_name=name)


@pytest.mark.parametrize("name", ["X-Synthetic-Token", "!#$%&'*+-.^_`|~0123456789ABCxyz"])
def test_dynapath_preserves_valid_custom_header_names(scripted_client_factory, name):
    config = synthetic_config(
        dynapath=DynapathConfig(
            enabled=True, token_provider=lambda context: "synthetic-token", header_name=name
        )
    )
    client, requests, _ = scripted_client_factory([{"strResult": "SUCC"}], config=config)
    client.http.post_form("/classes/com.korail.mobile.login.Login")
    assert requests[0].headers[name] == "synthetic-token"


@pytest.mark.parametrize("name", ["device_id", "as_value", "app_start_ts", "os_version", "device_model"])
@pytest.mark.parametrize("value", [None, 123, True, b"synthetic", "", " \t "])
def test_required_legacy_token_facts_are_actual_nonblank_strings(name, value):
    settings = DynapathTokenSettings(
        device_id="synthetic-install",
        as_value="synthetic-signature",
        app_start_ts="1",
        os_version="16",
        device_model="모델",
    )
    with pytest.raises(ValueError, match=name):
        replace(settings, **{name: value})


def test_login_context_body_is_available_but_hidden_from_repr(scripted_client_factory):
    contexts = []

    def provider(context):
        contexts.append(context)
        return "synthetic-token"

    client, requests, _ = scripted_client_factory(
        [*bootstrap(), login_response()],
        config=synthetic_config(dynapath=DynapathConfig(enabled=True, token_provider=provider)),
    )
    client.login(ID, PASSWORD)
    (context,) = contexts
    assert context.body == requests[-1].content
    assert b"txtMemberNo" in context.body and b"txtPwd" in context.body
    for output in (repr(context), str(context), str(contexts)):
        assert "txtMemberNo" not in output and "txtPwd" not in output
    assert asdict(context)["body"] == context.body
    assert pickle.loads(pickle.dumps(context)) == context
