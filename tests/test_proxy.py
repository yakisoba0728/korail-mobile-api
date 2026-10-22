"""Proxy settings are checked offline: transports are replaced or only constructed, never connected."""

from __future__ import annotations

import dataclasses
import os
import sys

import httpx
import pytest

from korail_mobile_api import (
    DynapathRequestContext,
    Korail,
    KorailClient,
    KorailConfig,
    KorailDeviceProfile,
    build_config_from_env,
    build_config_from_profile,
)
from korail_mobile_api import _transport as transport_module
from korail_mobile_api._transport import build_transport

USER = "synthetic-proxy-user"
SECRET = "synthetic-proxy-secret"
PROXY = f"http://{USER}:{SECRET}@127.0.0.1:8080"
HTTPX_VERSION = tuple(int(part) for part in httpx.__version__.split(".")[:2])
HTTPX_HAS_HTTPS_PROXY = HTTPX_VERSION >= (0, 25)
HTTPX_HAS_SOCKS5H = HTTPX_VERSION >= (0, 28)


def _assert_no_credentials(text: str) -> None:
    assert USER not in text and SECRET not in text


@pytest.fixture
def recorded(monkeypatch: pytest.MonkeyPatch) -> tuple[list[httpx.MockTransport], list[httpx.Request]]:
    """Stand in for httpx.HTTPTransport so proxied requests reach a scripted reply instead of a socket."""
    created: list[httpx.MockTransport] = []
    requests: list[httpx.Request] = []

    class RecordingProxyTransport(httpx.MockTransport):
        def __init__(self, *, proxy: httpx.Proxy) -> None:
            super().__init__(self._reply)
            self.proxy = proxy
            created.append(self)

        def _reply(self, request: httpx.Request) -> httpx.Response:
            requests.append(request)
            return httpx.Response(200, json={"strResult": "SUCC", "h_msg_cd": "S100", "h_msg_txt": "synthetic"})

    monkeypatch.setattr(httpx, "HTTPTransport", RecordingProxyTransport)
    return created, requests


@pytest.mark.parametrize(
    "proxy",
    [
        "http://127.0.0.1:8080",
        "https://proxy.example.invalid",
        PROXY,
        "socks5://127.0.0.1:1080",
        "socks5h://[::1]:1080",
        "SOCKS5://proxy.example.invalid:1080",
    ],
)
def test_proxy_accepts_supported_urls(proxy: str) -> None:
    assert KorailConfig(proxy=proxy).proxy == proxy


@pytest.mark.parametrize(
    "proxy",
    [
        "",
        " ",
        f"{PROXY}\n",
        f"http://{USER}:{SECRET} @127.0.0.1:8080",
        f"ftp://{USER}:{SECRET}@127.0.0.1:21",
        f"socks4://{USER}:{SECRET}@127.0.0.1:1080",
        f"{USER}:{SECRET}@127.0.0.1:8080",
        f"http://{USER}:{SECRET}@:8080",
        f"http://{USER}:{SECRET}@127.0.0.1:99999",
        f"http://{USER}:{SECRET}@127.0.0.1:port",
        f"http://{USER}:{SECRET}@[::1:8080",
        8080,
        PROXY.encode(),
    ],
)
def test_proxy_rejects_invalid_values_without_echoing_them(proxy: object) -> None:
    with pytest.raises(ValueError) as excinfo:
        KorailConfig(proxy=proxy)  # type: ignore[arg-type]
    _assert_no_credentials(str(excinfo.value))
    assert excinfo.value.__cause__ is None


def test_proxy_credentials_stay_out_of_repr() -> None:
    config = KorailConfig(proxy=PROXY)
    assert "proxy" not in repr(config)
    _assert_no_credentials(repr(config))


def test_without_proxy_the_transport_argument_is_unchanged() -> None:
    mock = httpx.MockTransport(lambda request: httpx.Response(200))
    assert build_transport(KorailConfig(), mock) is mock
    assert build_transport(KorailConfig(), None) is None


def test_api_and_queue_share_the_configured_proxy(recorded) -> None:
    created, requests = recorded
    client = KorailClient(KorailConfig(proxy=PROXY))
    try:
        assert len(created) == 2
        api, queue = created
        for transport in created:
            assert transport.proxy.url == httpx.URL("http://127.0.0.1:8080")
            assert transport.proxy.auth == (USER, SECRET)
        assert client.http._client._transport is api
        assert client.netfunnel is not None and client.netfunnel._client._transport is queue
        client.get_service_status()
        assert [request.url.host for request in requests] == ["smart.letskorail.com"]
    finally:
        client.close()


def test_queue_disabled_builds_only_the_api_transport(recorded) -> None:
    created, _ = recorded
    client = KorailClient(KorailConfig(proxy=PROXY, netfunnel_enabled=False))
    try:
        assert len(created) == 1 and client.netfunnel is None
    finally:
        client.close()


def test_proxy_and_custom_transport_cannot_be_combined() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request is sent")

    config = KorailConfig(proxy=PROXY)
    for make in (KorailClient, Korail):
        with pytest.raises(ValueError, match="custom transport") as excinfo:
            make(config, transport=httpx.MockTransport(handler))
        _assert_no_credentials(str(excinfo.value))
    with pytest.raises(ValueError, match="custom transport"):
        Korail.logged_in(
            "0000000000", "synthetic-password", config=config, transport=httpx.MockTransport(handler)
        )


@pytest.mark.parametrize("proxy", ["http://127.0.0.1:8080", "socks5://127.0.0.1:1080"])
def test_real_proxy_transport_is_built_without_connecting(proxy: str) -> None:
    transport = build_transport(KorailConfig(proxy=proxy), None)
    assert isinstance(transport, httpx.HTTPTransport)
    transport.close()


@pytest.mark.parametrize(
    "proxy, supported, message",
    [
        (f"https://{USER}:{SECRET}@127.0.0.1:8443", HTTPX_HAS_HTTPS_PROXY, "httpx 0.25"),
        (f"socks5h://{USER}:{SECRET}@127.0.0.1:1080", HTTPX_HAS_SOCKS5H, "httpx 0.28"),
    ],
)
def test_version_dependent_schemes_follow_the_installed_httpx(
    proxy: str, supported: bool, message: str
) -> None:
    config = KorailConfig(proxy=proxy)
    if supported:
        transport = build_transport(config, None)
        assert isinstance(transport, httpx.HTTPTransport)
        transport.close()
    else:
        with pytest.raises(ValueError, match=message) as excinfo:
            build_transport(config, None)
        _assert_no_credentials(str(excinfo.value))


def test_https_proxy_is_rejected_before_httpx_025(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(transport_module, "_HTTPX_VERSION", (0, 24))
    with pytest.raises(ValueError, match="httpx 0.25") as excinfo:
        build_transport(KorailConfig(proxy=f"https://{USER}:{SECRET}@127.0.0.1:8443"), None)
    _assert_no_credentials(str(excinfo.value))
    monkeypatch.setattr(transport_module, "_HTTPX_VERSION", (0, 25))
    transport = build_transport(KorailConfig(proxy="http://127.0.0.1:8080"), None)
    assert isinstance(transport, httpx.HTTPTransport)
    transport.close()


@pytest.mark.parametrize("error", [ValueError, httpx.InvalidURL])
def test_httpx_rejection_is_reraised_without_the_url(
    monkeypatch: pytest.MonkeyPatch, error: type[Exception]
) -> None:
    def reject(url: object) -> httpx.Proxy:
        raise error(f"Unknown scheme for proxy URL {url!r}")

    monkeypatch.setattr(httpx, "Proxy", reject)
    with pytest.raises(ValueError, match="httpx rejected the proxy URL") as excinfo:
        build_transport(KorailConfig(proxy=PROXY), None)
    _assert_no_credentials(str(excinfo.value))
    assert excinfo.value.__cause__ is None and excinfo.value.__suppress_context__


def test_missing_socksio_points_to_the_socks_extra(monkeypatch: pytest.MonkeyPatch) -> None:
    # httpcore installs a permanent SOCKS fallback if first imported while socksio is blocked.
    import httpcore  # noqa: F401

    monkeypatch.setitem(sys.modules, "socksio", None)
    config = KorailConfig(proxy=f"socks5://{USER}:{SECRET}@127.0.0.1:1080")
    with pytest.raises(ImportError, match=r"korail-mobile-api\[socks\]") as excinfo:
        KorailClient(config)
    _assert_no_credentials(str(excinfo.value))


def test_replace_and_device_profile_keep_the_proxy() -> None:
    config = KorailConfig(proxy=PROXY)
    assert dataclasses.replace(config, timeout=5.0).proxy == PROXY
    profile = KorailDeviceProfile(
        device_id="0123456789abcdef",
        model="SM-S948N",
        android_release="17",
        build_id="CP2A.260605.016",
    )
    assert build_config_from_profile(profile, base=config).proxy == PROXY


@pytest.fixture
def device_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for name in tuple(os.environ):
        if name.startswith("KORAIL_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "0123456789abcdef")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "17")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S948N")
    monkeypatch.setenv("KORAIL_ANDROID_BUILD_ID", "CP2A.260605.016")
    return monkeypatch


def test_build_config_from_env_reads_request_versions(device_env: pytest.MonkeyPatch) -> None:
    default = build_config_from_env()
    assert (default.app_version, default.version) == (KorailConfig().app_version, KorailConfig().version)
    device_env.setenv("KORAIL_APP_VERSION", "")
    device_env.setenv("KORAIL_API_VERSION", "")
    assert build_config_from_env().version == KorailConfig().version
    device_env.setenv("KORAIL_APP_VERSION", "9.9.9")
    device_env.setenv("KORAIL_API_VERSION", "999999999")
    config = build_config_from_env()
    assert (config.app_version, config.version) == ("9.9.9", "999999999")


def test_build_config_from_env_reads_korail_proxy(device_env: pytest.MonkeyPatch) -> None:
    assert build_config_from_env().proxy is None
    device_env.setenv("KORAIL_PROXY", "")
    assert build_config_from_env().proxy is None
    device_env.setenv("KORAIL_PROXY", PROXY)
    assert build_config_from_env().proxy == PROXY
    device_env.setenv("KORAIL_PROXY", f"ftp://{USER}:{SECRET}@127.0.0.1:21")
    with pytest.raises(ValueError) as excinfo:
        build_config_from_env()
    _assert_no_credentials(str(excinfo.value))


def test_environment_uses_diagnostic_device_facts(device_env: pytest.MonkeyPatch) -> None:
    device_env.setenv("KORAIL_DYNAPATH_DEVICE_ID", "synthetic-install")
    device_env.setenv("KORAIL_DYNAPATH_OS_VERSION", "16")
    device_env.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "synthetic-model")
    config = build_config_from_env()
    assert config.dynapath.token_settings is None
    assert config.dynapath.token_provider is not None
    assert config.dynapath.token_provider(DynapathRequestContext(*("synthetic",) * 9)) == (
        "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
        "&os=MTY&dm=c3ludGhldGljLW1vZGVs&iid=c3ludGhldGljLWluc3RhbGw"
    )


@pytest.mark.parametrize("name", ["DEVICE_ID", "OS_VERSION", "DEVICE_MODEL"])
def test_environment_still_rejects_blank_device_values(device_env: pytest.MonkeyPatch, name: str) -> None:
    device_env.setenv("KORAIL_DYNAPATH_" + name, "\u3000")
    with pytest.raises(ValueError):
        build_config_from_env()


@pytest.mark.parametrize(
    "name,attribute,default,override,expected",
    [
        ("KORAIL_DEVICE_WIDTH", "device_width", 1440, " 801 ", 801),
        ("KORAIL_DEVICE_HEIGHT", "device_height", 3120, "1602", 1602),
        ("KORAIL_ANDROID_SDK_INT", "android_sdk_int", 37, "34", 34),
    ],
)
def test_environment_device_dimensions_keep_defaults_and_integer_policy(
    device_env: pytest.MonkeyPatch, name: str, attribute: str, default: int, override: str, expected: int
) -> None:
    config = build_config_from_env()
    assert config.base_url == "https://smart.letskorail.com:443"
    assert getattr(config, attribute) == default
    device_env.setenv(name, override)
    assert getattr(build_config_from_env(), attribute) == expected
    device_env.setenv(name, "synthetic-invalid-integer")
    with pytest.raises(ValueError, match="invalid literal"):
        build_config_from_env()


@pytest.mark.parametrize(
    "field, value",
    [
        ("timeout", 0),
        ("timeout", -1.0),
        ("timeout", float("nan")),
        ("timeout", float("inf")),
        ("timeout", True),
        ("netfunnel_timeout", 0),
        ("netfunnel_timeout", None),
        ("netfunnel_timeout", float("nan")),
        ("netfunnel_wait_limit", -1),
        ("netfunnel_wait_limit", float("nan")),
    ],
)
def test_config_rejects_unusable_durations(field: str, value: object) -> None:
    """2.6.2: nan disabled the wait limit silently and None failed only when the queue did."""
    with pytest.raises(ValueError, match=field):
        KorailConfig(**{field: value})


def test_config_keeps_documented_duration_escapes() -> None:
    assert KorailConfig(timeout=None).timeout is None  # type: ignore[arg-type]
    assert KorailConfig(netfunnel_wait_limit=0).netfunnel_wait_limit == 0
    assert KorailConfig(netfunnel_wait_limit=None).netfunnel_wait_limit is None
