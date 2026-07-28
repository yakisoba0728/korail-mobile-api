"""``KorailConfig()`` 가 인자 없이 무엇을 주는가, 그리고 무엇을 주지 않는가.

DynaPath 는 자동화 탐지를 통과하기 위한 토큰이다. 그것을 보낼지 말지를 이
패키지가 호출자 대신 정하지 않으므로 **기본은 꺼짐** 이고, 켜는 것은
``KorailConfig(enable_dynapath=True)`` 라고 명시적으로 말한 사람뿐이다.

끈 채로도 대부분은 그대로 나간다. 토큰 없이 성공하는 것이 관측된 읽기는 그대로
가고, 관측된 거절이 있는 ``login.Login`` 만 전송 전에
``KorailDynaPathRequiredError`` 로 막힌다. 그 자리에서 막는 이유는 서버의 거절이
사용자 문구로 "앱을 최신 버전으로 업데이트"로 위장돼 오기 때문이다 — 그대로 두면
설정 문제가 버전 문제로 오진된다.

여기의 어떤 테스트도 "로그인이 성공한다"를 주장하지 않는다. 오프라인에서 확인할
수 없는 것이고 어디에서도 주장하지 않는다.
"""

from __future__ import annotations

import inspect
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
    DYNAPATH_REQUIRED_PATHS,
    KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    KORAIL_DEFAULT_DEVICE_NAME,
)
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import KorailDynaPathRequiredError
from korail_mobile_api.http import KorailHttpClient


README = Path(__file__).parents[1] / "README.md"
CHANGELOG = Path(__file__).parents[1] / "CHANGELOG.md"
LOGIN_PATH = "/classes/com.korail.mobile.login.Login"
SEARCH_PATH = "/classes/com.korail.mobile.seatMovie.ScheduleView"
OK = {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"}


# ---------------------------------------------------------------------------
# 기본값은 꺼짐이다
# ---------------------------------------------------------------------------


def test_bare_config_leaves_dynapath_off():
    config = KorailConfig()

    assert config.dynapath.enabled is False
    assert config.dynapath.token_settings is None
    assert config.dynapath.token_provider is None


def test_a_bare_client_refuses_the_login_path_before_sending_anything():
    sent: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request.url.path)
        return httpx.Response(200, json=OK)

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(KorailDynaPathRequiredError) as raised:
        client.post_form(LOGIN_PATH)

    # 전송 전에 막는다는 것이 요지다. 한 건이라도 나갔다면 서버가 대신 거절할
    # 자리를 남긴 것이고, 그 거절은 버전 문제로 위장돼 돌아온다.
    assert sent == []
    # 무엇을 켜야 하는지 메시지가 직접 말해야 한다. 그러지 않으면 이 예외는
    # 자신이 대체한 위장된 거절보다 나을 것이 없다.
    assert "enable_dynapath=True" in str(raised.value)
    assert "build_config_from_env" in str(raised.value)


def test_only_the_paths_with_observed_refusals_are_required():
    # 허용목록과 요구목록은 다르다. 토큰 없이 성공한 것이 관측된 읽기까지 막으면
    # 이 패키지가 잘 되던 호출을 끊는 셈이다.
    assert DYNAPATH_REQUIRED_PATHS < DYNAPATH_ALLOWLIST_PATHS
    assert DYNAPATH_REQUIRED_PATHS == {LOGIN_PATH}


def test_an_allowlisted_but_not_required_path_still_goes_out_untokened():
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get(DYNAPATH_HEADER_NAME))
        return httpx.Response(200, json=OK)

    assert SEARCH_PATH in DYNAPATH_ALLOWLIST_PATHS
    assert SEARCH_PATH not in DYNAPATH_REQUIRED_PATHS

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.post_form(SEARCH_PATH)

    assert seen == [None]


# ---------------------------------------------------------------------------
# 켰을 때는 앱과 같은 모양이 나온다
# ---------------------------------------------------------------------------


def test_the_flag_builds_settings_rather_than_only_flipping_a_boolean():
    config = KorailConfig(enable_dynapath=True)

    assert config.dynapath.enabled is True
    # 제공자도 설정도 없이 켜진 상태는 DynapathConfig.__post_init__ 이 거부하고,
    # 닿지 않는 설정으로 켜진 상태는 조용히 실패하므로 그보다 나쁘다.
    assert config.dynapath.token_settings is not None
    assert config.dynapath.token_provider is None


def test_an_enabled_client_puts_the_token_on_the_login_request():
    captured: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        captured["user_agent"] = request.headers.get("user-agent")
        return httpx.Response(200, json=OK)

    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True),
        transport=httpx.MockTransport(handler),
    )
    client.post_form(LOGIN_PATH)

    # 사슬의 끝 — 플래그에서 생성기를 거쳐 실제 헤더까지. 위의 것들이 모양이라면
    # 이것은 도착한다는 진술이다.
    assert captured["token"]
    assert captured["user_agent"] == KorailConfig().user_agent


def test_the_token_stays_confined_to_the_allowlisted_paths():
    seen: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get(DYNAPATH_HEADER_NAME))
        return httpx.Response(200, json=OK)

    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True),
        transport=httpx.MockTransport(handler),
    )
    client.post_form("/classes/com.korail.mobile.common.code.do")

    # 켜는 것은 토큰을 **언제** 보내는지를 넓힐 뿐 **어디로** 보내는지를 넓히지
    # 않는다.
    assert seen == [None]
    assert LOGIN_PATH in DYNAPATH_ALLOWLIST_PATHS


def test_bare_config_user_agent_has_the_shape_the_platform_sends():
    # User-Agent 는 DynaPath 와 별개다. 토큰을 끄든 켜든 앱이 보내는 모양이어야
    # 하며, 파이썬 패키지 이름을 다는 것은 어떤 앱도 하지 않는 일이다.
    user_agent = KorailConfig().user_agent

    assert user_agent.startswith("Dalvik/2.1.0 (Linux; U; Android ")
    assert "korail-mobile-api" not in user_agent
    assert "python" not in user_agent.casefold()


def test_user_agent_claims_the_same_device_and_release_as_the_token():
    config = KorailConfig(enable_dynapath=True)
    settings = config.dynapath.token_settings
    assert settings is not None

    # 한 요청 안에서 User-Agent 가 주장하는 단말과 토큰이 주장하는 단말이 다르면
    # 무해한 불일치가 아니라 둘이 서로 다른 것에서 나왔다는 증거다.
    assert settings.os_version == KORAIL_DEFAULT_ANDROID_OS_RELEASE
    assert settings.device_model == KORAIL_DEFAULT_DEVICE_NAME
    assert (
        f"Android {settings.os_version}; {settings.device_model})"
        in config.user_agent
    )
    # 커스텀 token_provider 는 DynapathRequestContext 로만 이 쌍에 닿으므로
    # DynapathConfig 가 들고 있는 세 번째 사본도 일치해야 한다.
    assert config.dynapath.os_version == settings.os_version
    assert config.dynapath.device_name == settings.device_model


def test_device_id_is_per_instance_and_android_id_shaped():
    ids = {
        KorailConfig(enable_dynapath=True).dynapath.token_settings.device_id
        for _ in range(16)
    }

    # 패키지에 박힌 기기 식별자는 모든 설치본이 공유하는 고정값이 되고, 그것이
    # 바로 이 토큰이 피하려는 봇 신호다.
    assert len(ids) == 16
    for device_id in ids:
        # Settings.Secure.ANDROID_ID (AbstractC1228a.java:16) — 64비트를 소문자
        # hex 16자로. 32자 UUID 는 어떤 안드로이드 단말도 내놓지 않는 값이다.
        assert re.fullmatch(r"[0-9a-f]{16}", device_id), device_id


def test_device_id_is_stable_within_one_config():
    config = KorailConfig(enable_dynapath=True)
    settings = config.dynapath.token_settings

    # ANDROID_ID 는 설치별이지 요청별이 아니다. 호출마다 바뀌면 매 요청이 새
    # 단말로 읽힌다.
    assert settings.device_id == config.dynapath.token_settings.device_id


def test_app_start_ts_is_the_moment_the_config_was_built():
    before = int(time.time() * 1000)
    settings = KorailConfig(enable_dynapath=True).dynapath.token_settings
    after = int(time.time() * 1000)

    # ``it`` 은 엔진 생성 시각의 System.currentTimeMillis()
    # (AbstractC1228a.java:14). 설정을 만드는 순간이 이쪽의 대응 시점이다.
    app_start_ts = int(settings.app_start_ts)
    assert before <= app_start_ts <= after


# ---------------------------------------------------------------------------
# 구성 방법이 서로를 덮어쓰지 않는다
# ---------------------------------------------------------------------------


def test_an_explicit_dynapath_config_wins_over_the_flag():
    provider_config = DynapathConfig(enabled=True, token_provider=lambda _c: "t")
    config = KorailConfig(enable_dynapath=True, dynapath=provider_config)

    # 토큰 제공자를 갈아끼운 호출자가 편의 플래그 하나로 그것을 잃으면 안 된다.
    assert config.dynapath is provider_config
    assert config.dynapath.token_settings is None


def test_the_custom_token_provider_form_stays_constructible():
    # 기본 설정이 KorailConfig 쪽에 있고 DynapathConfig 에 없는 이유가 이것이다.
    # DynapathConfig.__post_init__ 은 제공자와 설정 중 정확히 하나를 요구하므로,
    # 기본 token_settings 가 있었다면 모든 커스텀 제공자가 모순이 됐을 것이다.
    config = KorailConfig(
        dynapath=DynapathConfig(enabled=True, token_provider=lambda _c: "t"),
    )
    assert config.dynapath.token_settings is None

    with pytest.raises(ValueError):
        DynapathConfig(enabled=True)


def test_enable_dynapath_was_appended_and_did_not_shift_anything():
    # 필드를 중간에 끼우면 이미 위치 인자로 쓰던 호출의 뜻이 조용히 바뀐다.
    parameters = list(inspect.signature(KorailConfig).parameters)
    assert parameters[-1] == "enable_dynapath"
    assert parameters.index("dynapath") == 7


def test_build_config_from_env_is_part_of_the_public_api():
    # 실제 단말 값을 고정하는 지원 경로. 프로세스 사이에서 유지되는 식별자를
    # 쓰려면 이쪽이다.
    assert "build_config_from_env" in korail_mobile_api.__all__
    assert callable(getattr(korail_mobile_api, "build_config_from_env", None))
    # 짝은 일부러 비공개로 둔다. 자격증명과 이 저장소 전용 스모크 발판은 이
    # 패키지의 API 가 아니다.
    for name in ("read_credentials_from_env", "run_live_smoke_from_env"):
        assert name not in korail_mobile_api.__all__


def test_the_error_and_the_flag_are_reachable_from_the_package_root():
    # 사용자가 잡아야 하는 예외와 켜야 하는 이름이 최상위에 없으면, 오류 메시지가
    # 가리키는 곳에 손이 닿지 않는다.
    assert "KorailDynaPathRequiredError" in korail_mobile_api.__all__
    assert "enable_dynapath" in inspect.signature(KorailConfig).parameters
    # 경로 집합은 최상위에 올리지 않는다 — 형제인 DYNAPATH_ALLOWLIST_PATHS 와
    # 마찬가지로 전송 계층 상수이고, 공개 표면 규칙이 그것을 서브모듈에 둔다.
    assert "DYNAPATH_REQUIRED_PATHS" not in korail_mobile_api.__all__
    assert "DYNAPATH_ALLOWLIST_PATHS" not in korail_mobile_api.__all__


# ---------------------------------------------------------------------------
# 문서
# ---------------------------------------------------------------------------


def test_the_documents_describe_the_opt_in_rather_than_a_default():
    readme = README.read_text(encoding="utf-8")
    unwrapped = re.sub(r"\s+", " ", readme)

    # 문장을 그대로 고정하지 않는다 — 문서는 다시 쓰이고, 줄바꿈 위치에 매달린
    # 단언은 내용이 옳은 채로도 깨진다. 사실만 본다: 켜는 법, 켜지 않았을 때 나는
    # 예외, 그리고 철회된 옛 주장이 돌아오지 않았다는 것.
    assert "enable_dynapath" in readme
    assert "KorailDynaPathRequiredError" in readme
    assert "Nothing above needs DynaPath" not in unwrapped
    assert "기본적으로 켜져 있다" not in unwrapped

    # 실제 단말을 고정하는 경로와 그 세 환경변수는 이름이 나와 있어야 한다.
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

    # 한국어 문구를 그대로 믿은 호출자는 낡은 KORAIL_API_VERSION 을 찾으러 간다.
    # 증상과, 진짜 SUPDATE 와 구별하는 단서가 둘 다 적혀 있어야 한다.
    for document in (readme, changelog):
        assert "MACRO ERROR" in document
        assert "앱을 최신 버전으로 업데이트" in document
    assert "SUPDATE" in readme
