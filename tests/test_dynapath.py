import httpx

from korail_mobile_api import KorailConfig
from korail_mobile_api.constants import DYNAPATH_HEADER_NAME
from korail_mobile_api.dynapath import (
    DynapathConfig,
    DynapathTokenSettings,
    build_dynapath_prefix,
    generate_dynapath_encoding_table,
    generate_dynapath_token,
)
from korail_mobile_api.http import KorailHttpClient


def make_settings() -> DynapathTokenSettings:
    return DynapathTokenSettings(
        app_id="com.korail.talk",
        device_id="DEVICE-1234",
        as_value="[38ff229cb34c7dda8e28220a2d750cce]",
        app_start_ts="1712345600000",
        os_version="13",
        device_model="SM-S928N",
        os_type="Android",
        sdk_version="v1.0.3",
    )


def test_encoding_table_is_generated_from_original_sdk_permutation():
    table = generate_dynapath_encoding_table(1)

    assert table == "3FE9jgRD4KdCyuawklqGJYmvfMn15P7US8XbxeLQtWT6OicBAopINs2Vh0HZrz"
    assert build_dynapath_prefix(table=table, table_index=1, i11=2, i12=30) == "bEeEP"


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
        make_settings(),
        timestamp_ms=1712345678901,
        random_text="A1B2",
    )
