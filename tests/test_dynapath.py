import httpx
from dataclasses import replace
import pytest

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.constants import DYNAPATH_HEADER_NAME
from korail_mobile_api.dynapath import (
    DynapathConfig,
    DynapathTokenGenerator,
    DynapathTokenSettings,
    KorailProbeDynapathTokenProvider,
    KORAIL_DYNAPATH_APP_ID,
    KORAIL_DYNAPATH_OS_TYPE,
    KORAIL_DYNAPATH_SDK_VERSION,
    build_dynapath_prefix,
    generate_dynapath_encoding_table,
    generate_dynapath_token,
)
from korail_mobile_api.http import KorailHttpClient
from korail_mobile_api.errors import KorailProtocolError


def make_settings() -> DynapathTokenSettings:
    return DynapathTokenSettings(
        device_id="DEVICE-1234",
        as_value="[38ff229cb34c7dda8e28220a2d750cce]",
        app_start_ts="1712345600000",
        os_version="13",
        device_model="SM-S928N",
    )


def success_handler(_: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "h_msg_cd": "IRG000000",
            "h_msg_txt": "OK",
            "strResult": "SUCC",
        },
    )


def test_encoding_table_is_generated_from_original_sdk_permutation():
    table = generate_dynapath_encoding_table(1)

    assert table == "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"
    assert build_dynapath_prefix(table=table, table_index=1, i11=2, i12=30) == "bEeEP"


def test_token_settings_default_to_korail_source_hardcoded_values():
    settings = make_settings()

    assert settings.app_id == KORAIL_DYNAPATH_APP_ID == "com.korail.talk"
    assert settings.os_type == KORAIL_DYNAPATH_OS_TYPE == "Android"
    assert settings.sdk_version == KORAIL_DYNAPATH_SDK_VERSION == "v1.0.3"


def test_generate_dynapath_token_uses_user_supplied_runtime_constants():
    token = generate_dynapath_token(
        make_settings(),
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )

    assert token == (
        "bEeEPLYj144a44lDm54Mg4Pv4ff4fGKguKkDK1FdDwFGP4Gdlqujn5nfujYP4GudEqyRufK9v5Jy1aggYfjaDF"
        "53EmlDmnnP4ankJm1umKPJnCmllnm9PPumadmkYPjvn3vml9mll5qymDqmFk5qvPCq9qna99qwGdlRP4Kqq"
        "19v5PuddlRP4Kqq19vmuJFdlRP4Kqq19vau95JnuuffJ3mJvdnjlmFCmlDmnymwa5u95u99vCqu95CC5CumK"
        "fm1gmvDngY5CgqYqnkj9vuqu95Cq9v5uPl4kl5E5ngPn3E9vRqCPdMYJl4uj9Pvkqw3dDm5CY5uEDw"
    )


def test_http_client_generates_dynapath_header_from_token_settings():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_settings=make_settings(),
            timestamp_ms_provider=lambda: 1712345678901,
            random_text_provider=lambda: "A1B2",
        )
    )
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))

    client.post_form("/classes/com.korail.mobile.login.Login")

    assert captured["token"] == generate_dynapath_token(
        replace(make_settings(), recent_request_deltas=(78901,)),
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )


def test_stateful_dynapath_generator_tracks_request_deltas_like_sdk():
    timestamps = iter([1712345600100, 1712345600250])
    random_texts = iter(["A1B2", "C3D4"])
    base_settings = replace(make_settings(), app_start_ts="1712345600000")
    generator = DynapathTokenGenerator(
        base_settings,
        timestamp_ms_provider=lambda: next(timestamps),
        random_text_provider=lambda: next(random_texts),
    )

    first = generator()
    second = generator()

    assert first == generate_dynapath_token(
        replace(base_settings, recent_request_deltas=(100,)),
        timestamp_ms=1712345600100,
        random_text="A1B2",
    )
    assert second == generate_dynapath_token(
        replace(base_settings, recent_request_deltas=(100, 150)),
        timestamp_ms=1712345600250,
        random_text="C3D4",
    )


def test_stateful_dynapath_generator_keeps_latest_five_deltas():
    timestamps = iter([1010, 1020, 1030, 1040, 1050, 1060])
    settings = replace(make_settings(), app_start_ts="1000")
    generator = DynapathTokenGenerator(
        settings,
        timestamp_ms_provider=lambda: next(timestamps),
        random_text_provider=lambda: "A1B2",
    )

    for _ in range(6):
        generator()

    assert generator.recent_request_deltas == (10, 10, 10, 10, 10)


def test_probe_dynapath_provider_matches_successful_login_probe_token():
    provider = KorailProbeDynapathTokenProvider(
        device_id="7f000001-android-probe",
        app_start_ts_provider=lambda: 1712345600000,
        timestamp_ms_provider=lambda: 1712345678901,
        random_text_provider=lambda: "A1B2",
    )

    assert provider() == (
        "bEeEPSYj1Dm54Mg4Pv4ff4fGKguKkDK1FdDwFGkG9fwdEuJYJ3EuakG9EfldmgE34vnYDmCRKkYEv"
        "YEvYEqYlMEgddaaDFmY4qdaakERvn4dEvvdJfmnJ5KDR9RwqkPkR43kglDwwk13D5yJ9vYuKk1"
        "qkKaRCjkPDD5YRCyvngduKDJEE33D5RkuKDGPDJEE33D5RD4dduKDJEE33D5RDyyfwgkG4ddCvn3"
        "dPkYPPYPER43RCqYEvYEvYDFdFfJuwRFPRwjRJmRyEJ93YEqvnMdPkYDFEuCJuwRluDwRfwl3PMG"
        "nJRwv3uFdyjJuCEgddaaDFmvngy4Ryln"
    )


def test_enabled_dynapath_requires_exactly_one_token_source():
    with pytest.raises(ValueError, match="exactly one"):
        DynapathConfig(enabled=True)
    with pytest.raises(ValueError, match="exactly one"):
        DynapathConfig(
            enabled=True,
            token_provider=lambda _context: "token",
            token_settings=make_settings(),
        )


def test_http_reuses_one_stateful_generator_across_requests():
    timestamps = iter([1712345600100, 1712345600250])
    random_texts = iter(["A1B2", "C3D4"])
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request.headers[DYNAPATH_HEADER_NAME])
        return success_handler(request)

    settings = replace(make_settings(), app_start_ts="1712345600000")
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_settings=settings,
            timestamp_ms_provider=lambda: next(timestamps),
            random_text_provider=lambda: next(random_texts),
        )
    )
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form("/classes/com.korail.mobile.login.Login")
    client.post_form("/classes/com.korail.mobile.login.Login")
    assert captured == [
        generate_dynapath_token(
            replace(settings, recent_request_deltas=(100,)),
            timestamp_ms=1712345600100,
            random_text="A1B2",
        ),
        generate_dynapath_token(
            replace(settings, recent_request_deltas=(100, 150)),
            timestamp_ms=1712345600250,
            random_text="C3D4",
        ),
    ]


def test_dynapath_generator_is_per_client_and_survives_logout():
    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_settings=make_settings(),
        )
    )
    first = KorailClient(config, transport=httpx.MockTransport(success_handler))
    second = KorailClient(config, transport=httpx.MockTransport(success_handler))
    first_generator = first.http._dynapath_generator
    assert first_generator is not None
    assert first_generator is not second.http._dynapath_generator
    first.logout()
    assert first.http._dynapath_generator is first_generator


def test_dynapath_allowlist_uses_exact_path():
    called = False

    def provider(_context):
        nonlocal called
        called = True
        return "token"

    config = KorailConfig(
        dynapath=DynapathConfig(enabled=True, token_provider=provider)
    )
    client = KorailHttpClient(config, transport=httpx.MockTransport(success_handler))
    with pytest.raises(KorailProtocolError):
        client.post_form("/classes/com.korail.mobile.login.Login.suffix")
    assert called is False
