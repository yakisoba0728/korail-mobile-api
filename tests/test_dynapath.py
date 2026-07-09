import httpx

from korail_mobile_api import KorailConfig
from korail_mobile_api.constants import DYNAPATH_HEADER_NAME
from korail_mobile_api.dynapath import DynapathConfig, DynapathTokenSettings, generate_dynapath_token
from korail_mobile_api.http import KorailHttpClient


def make_settings() -> DynapathTokenSettings:
    return DynapathTokenSettings(
        app_id="com.korail.talk",
        device_id="DEVICE-1234",
        as_value="%5B38ff229cb34c7dda8e28220a2d750cce%5D",
        app_start_ts="1712345600000",
        os_version="13",
        device_model="SM-S928N",
        os_type="Android",
        sdk_version="v1",
    )


def test_generate_dynapath_token_uses_user_supplied_runtime_constants():
    token = generate_dynapath_token(
        make_settings(),
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )

    assert token == (
        "bEeEPSYj1Dm54Mg4Pv4ff4fGKguKkDK1FdDwFGkG9fwdEuJYJ3EuakG9EfldmgE34vnYDmC1qqa3u1jFY5lR"
        "wjRJJkG1JKDRCER4kDJPRwwJRvkkER1fRKakunJ5nRwvRwwYdmRjdRFKYdnkPdvdJ1vvdy9fwgkG4ddCvnYkEffwg"
        "kG4ddCvnREDFfwgkG4ddCvn1EvYDJEE33D5RDnfJuwRFPRwjRJmRy1YEvYEvvnPdEvYPPYPER43RCqRnjJqaYPq"
        "dadJKuvnEdEvYPdvnYEkwGKwYlYJqkJ5lvngdPkfMaDwGEuvknKdy5fjRjE"
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
        make_settings(),
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )
