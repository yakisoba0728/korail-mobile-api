"""What a caller gets from ``KorailConfig()`` with no arguments.

Until 1.0.0 the README's quickstart — ``KorailClient()`` then ``login(...)`` —
did not work. A bare config produced a User-Agent naming this Python package
and a DISABLED DynaPath, and ``login.Login`` came back ``**MACRO ERROR**``,
which the server dresses up as "앱을 최신 버전으로 업데이트" in the user-facing
text. Account-neutral reads kept succeeding under the same config, so the
library looked healthy and the failure looked like a version gate.

None of these tests claim a login succeeds. That cannot be asserted offline and
is not asserted anywhere. What they pin is the three things that were wrong and
are checkable without a network: DynaPath is on, the User-Agent has the app's
shape, and the device the User-Agent claims is the device the token claims.

Every name used here already existed before the change, deliberately: reverting
``src/`` has to make these FAIL, not fail to import.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailConfig
from korail_mobile_api.constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    KORAIL_DEFAULT_DEVICE_NAME,
)
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.http import KorailHttpClient


README = Path(__file__).parents[1] / "README.md"
CHANGELOG = Path(__file__).parents[1] / "CHANGELOG.md"
LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
OK = {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"}


def _ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=OK)


def test_bare_config_enables_dynapath_and_carries_its_own_token_settings():
    config = KorailConfig()

    assert config.dynapath.enabled is True
    # Enabled with neither provider nor settings would have been rejected by
    # DynapathConfig.__post_init__; enabled with settings that are never
    # reached would be worse, because it fails silently. Assert the settings
    # are actually there.
    assert config.dynapath.token_settings is not None
    assert config.dynapath.token_provider is None


def test_bare_config_user_agent_has_the_shape_the_platform_sends():
    user_agent = KorailConfig().user_agent

    assert user_agent.startswith("Dalvik/2.1.0 (Linux; U; Android ")
    # The specific thing that was wrong: a header naming a Python package is
    # not something any genuine app sends.
    assert "korail-mobile-api" not in user_agent
    assert "python" not in user_agent.casefold()


def test_user_agent_claims_the_same_device_and_release_as_the_token():
    config = KorailConfig()
    settings = config.dynapath.token_settings
    assert settings is not None

    # A User-Agent claiming one handset while the DynaPath token in the same
    # request claims another is not a harmless inconsistency: it is evidence
    # the two were produced by different things. Both must come from the same
    # two constants.
    assert settings.os_version == KORAIL_DEFAULT_ANDROID_OS_RELEASE
    assert settings.device_model == KORAIL_DEFAULT_DEVICE_NAME
    assert (
        f"Android {settings.os_version}; {settings.device_model})"
        in config.user_agent
    )
    # DynapathConfig carries the same pair for a custom token_provider's
    # benefit (it reaches one only through DynapathRequestContext), so that
    # third copy has to agree too.
    assert config.dynapath.os_version == settings.os_version
    assert config.dynapath.device_name == settings.device_model


def test_device_id_is_per_instance_and_android_id_shaped():
    ids = {
        KorailConfig().dynapath.token_settings.device_id
        for _ in range(16)
    }

    # A device id baked into the package would be a fixed identifier shared by
    # every installation — which is exactly the bot signature this is supposed
    # to avoid, so one distinct value per config is the assertion.
    assert len(ids) == 16
    for device_id in ids:
        # Settings.Secure.ANDROID_ID (AbstractC1228a.java:16): 64 bits as 16
        # lowercase hex characters. A 32-hex-digit UUID would be a value no
        # Android device can produce.
        assert re.fullmatch(r"[0-9a-f]{16}", device_id), device_id


def test_device_id_is_stable_within_one_config():
    config = KorailConfig()
    settings = config.dynapath.token_settings

    # ANDROID_ID is per-installation, not per-request: a value that changed
    # between calls would read as a new device on every request.
    assert settings.device_id == config.dynapath.token_settings.device_id


def test_app_start_ts_is_the_moment_the_config_was_built():
    before = int(time.time() * 1000)
    settings = KorailConfig().dynapath.token_settings
    after = int(time.time() * 1000)

    # `it` is System.currentTimeMillis() at engine construction
    # (AbstractC1228a.java:14). Building the config is our equivalent moment.
    app_start_ts = int(settings.app_start_ts)
    assert before <= app_start_ts <= after


def test_a_bare_client_actually_puts_a_token_on_the_login_request():
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        captured["user_agent"] = request.headers.get("user-agent")
        return httpx.Response(200, json=OK)

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.post_form(LOGIN_PATH)

    # The end of the chain: config default -> generator -> header on the wire.
    # Everything above is shape; this is the one that says it arrives.
    assert captured["token"]
    assert captured["user_agent"] == KorailConfig().user_agent


def test_the_token_is_still_confined_to_the_allowlisted_paths():
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get(DYNAPATH_HEADER_NAME))
        return httpx.Response(200, json=OK)

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.post_form("/classes/com.korail.mobile.common.code.do")

    # Turning DynaPath on by default widened WHEN a token is sent, not WHERE.
    assert seen == [None]
    assert LOGIN_PATH in DYNAPATH_ALLOWLIST_PATHS


def test_dynapath_can_still_be_switched_off_explicitly():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get(DYNAPATH_HEADER_NAME) is None
        return httpx.Response(200, json=OK)

    config = KorailConfig(dynapath=DynapathConfig())
    assert config.dynapath.enabled is False
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form(LOGIN_PATH)


def test_the_custom_token_provider_form_survives_the_default():
    # The default settings live on KorailConfig, not on DynapathConfig,
    # precisely so this stays constructible: DynapathConfig.__post_init__
    # requires EXACTLY ONE of provider/settings, so a defaulted token_settings
    # would have turned every custom provider into a contradiction.
    config = KorailConfig(
        dynapath=DynapathConfig(enabled=True, token_provider=lambda _c: "t"),
    )
    assert config.dynapath.token_settings is None

    with pytest.raises(ValueError):
        DynapathConfig(enabled=True)


def test_build_config_from_env_is_part_of_the_public_api():
    # The supported way to pin a REAL device identity. It was the only path
    # that logged in, and it was reachable only by importing a private module.
    # Asserted by name rather than imported, so that reverting src/ fails this
    # test instead of breaking collection.
    assert "build_config_from_env" in korail_mobile_api.__all__
    assert callable(getattr(korail_mobile_api, "build_config_from_env", None))
    # Its counterparts stay unexported on purpose: credentials and this
    # repository's smoke scaffolding are not this package's API.
    for name in ("read_credentials_from_env", "run_live_smoke_from_env"):
        assert name not in korail_mobile_api.__all__

    # The README names KORAIL_USER_AGENT as the thing a caller compares their
    # own override against, and every sibling KORAIL_DEFAULT_* is exported.
    # A README naming something unreachable is the defect this change fixes.
    assert "KORAIL_USER_AGENT" in korail_mobile_api.__all__
    assert korail_mobile_api.KORAIL_USER_AGENT == KorailConfig().user_agent


def test_the_readme_no_longer_says_dynapath_is_off_for_korail():
    # Prose wraps, so read it unwrapped: an assertion that a sentence is
    # present must not depend on where the line break landed.
    readme = README.read_text(encoding="utf-8")
    unwrapped = re.sub(r"\s+", " ", readme)

    # The sentence this replaces -- "Nothing above needs DynaPath. That
    # anti-automation header is off by default ... from settings you supply
    # explicitly" -- described a client that could not log in.
    assert "Nothing above needs DynaPath" not in unwrapped
    assert "anti-automation header is **on by default**" in unwrapped
    # NetFunnel is a different subsystem and IS off by default; that claim has
    # to survive, and test_netfunnel.py reads the README for it.
    assert "It is **off by default** because no live call" in unwrapped

    # The env path is the supported way to pin a real device, so the README
    # has to name it and its three required variables.
    assert "build_config_from_env" in readme
    for variable in (
        "KORAIL_DYNAPATH_DEVICE_ID",
        "KORAIL_DYNAPATH_OS_VERSION",
        "KORAIL_DYNAPATH_DEVICE_MODEL",
    ):
        assert variable in readme


def test_the_disguised_macro_rejection_is_documented_where_it_is_hit():
    readme = README.read_text(encoding="utf-8")
    changelog = CHANGELOG.read_text(encoding="utf-8")

    # A caller who reads the Korean text at face value goes looking for a
    # superseded KORAIL_API_VERSION. Both the symptom and the tell that
    # distinguishes it from a real SUPDATE have to be written down.
    for document in (readme, changelog):
        assert "MACRO ERROR" in document
        assert "앱을 최신 버전으로 업데이트" in document
    assert "SUPDATE" in readme
