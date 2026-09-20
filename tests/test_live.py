# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

import pytest

from korail_mobile_api.live import live_enabled, read_credentials_from_env


def test_live_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KORAIL_MOBILE_API_LIVE", raising=False)
    assert live_enabled() is False


def test_live_enabled_only_with_explicit_flag(monkeypatch):
    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    assert live_enabled() is True


def test_credentials_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "pw")
    assert read_credentials_from_env() == ("member", "pw")


def test_build_config_from_env_requires_device_identity(monkeypatch):
    import korail_mobile_api.live as live

    for name in (
        "KORAIL_DYNAPATH_DEVICE_ID",
        "KORAIL_DYNAPATH_OS_VERSION",
        "KORAIL_DYNAPATH_DEVICE_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="KORAIL_DYNAPATH_DEVICE_ID"):
        live.build_config_from_env()


def test_build_config_from_env_builds_sdk_settings(monkeypatch):
    import korail_mobile_api.live as live

    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.setenv("KORAIL_ADVERTISING_ID", "ad-id")
    monkeypatch.setattr(live.time, "time", lambda: 1712345600.0)
    config = live.build_config_from_env()
    assert config.dynapath.token_provider is None
    assert config.dynapath.token_settings.device_id == "device-1"
    assert config.dynapath.token_settings.app_start_ts == "1712345600000"
    assert config.dynapath.token_settings.sdk_version == "v1.0.3"
    assert config.dynapath.token_settings.as_value == (
        "[38ff229cb34c7dda8e28220a2d750cce]"
    )
    assert config.advertising_id == "ad-id"


def test_build_config_from_env_defaults_advertising_id_to_empty(monkeypatch):
    import korail_mobile_api.live as live

    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.delenv("KORAIL_ADVERTISING_ID", raising=False)

    config = live.build_config_from_env()

    assert config.advertising_id == ""
