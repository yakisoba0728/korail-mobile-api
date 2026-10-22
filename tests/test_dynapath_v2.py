"""DynaPath SDK 2.0.1 평문 진단 헤더의 직렬화와 선택형 공급자 연결을 오프라인으로 검사합니다.

기대 문자열은 코드에서 다시 만든 값이 아닌 고정값입니다. 실제 기기값·토큰은 담지 않으며,
이 헤더를 서버가 받아들인다는 근거로 쓰지 않습니다.
"""

from __future__ import annotations

import pickle

import pytest

from korail_mobile_api import (
    DynapathConfig,
    KorailConfig,
    KorailDeviceProfile,
    build_config_from_profile,
    build_dynapath_v2_diagnostic_header,
    dynapath_v2_diagnostic_token,
)
from korail_mobile_api.constants import DYNAPATH_ALLOWLIST_PATHS

NATIVE_UNAVAILABLE = "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
SERVICE = "/file/CACHE/MobileService.cache"


def envelope() -> dict[str, str]:
    return {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "synthetic message"}


def v2_config() -> KorailConfig:
    return KorailConfig(
        base_url="https://api.example.invalid",
        netfunnel_enabled=False,
        dynapath=DynapathConfig(enabled=True, token_provider=dynapath_v2_diagnostic_token),
    )


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({}, NATIVE_UNAVAILABLE),
        (
            {
                "app_id": "test.fixture",
                "os_version": b"test-os",
                "device_model": b"test-model",
                "install_id": b"\xfb\xff",
                "manufacturer": b"test vendor",
                "board": b"unit",
                "sdk_int": 34,
            },
            "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=test.fixture"
            "&os=dGVzdC1vcw&dm=dGVzdC1tb2RlbA&iid=-_8&mf=dGVzdCB2ZW5kb3I&bd=dW5pdA&sl=34",
        ),
        # None 은 필드를 빼고, 빈 바이트와 0 은 빈 값·0 으로 보냅니다.
        (
            {"state": 0, "app_id": "test", "os_version": b"", "board": b"", "sdk_int": 0},
            "2!v=2&es=0&st=Android&sv=2.0.1&ai=test&os=&bd=&sl=0",
        ),
        ({"state": -(1 << 63)}, "2!v=2&es=-9223372036854775808&st=Android&sv=2.0.1&ai=korailplus"),
        ({"state": (1 << 63) - 1}, "2!v=2&es=9223372036854775807&st=Android&sv=2.0.1&ai=korailplus"),
        ({"sdk_int": (1 << 31) - 1}, NATIVE_UNAVAILABLE + "&sl=2147483647"),
    ],
)
def test_header_matches_independent_fixtures(kwargs: dict[str, object], expected: str) -> None:
    assert build_dynapath_v2_diagnostic_header(**kwargs) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "raw, encoded",
    [(b"", ""), (b"f", "Zg"), (b"fo", "Zm8"), (b"foo", "Zm9v"), (b"\xfb\xff\xff", "-___")],
)
def test_metadata_uses_unpadded_urlsafe_base64(raw: bytes, encoded: str) -> None:
    assert build_dynapath_v2_diagnostic_header(device_model=raw) == f"{NATIVE_UNAVAILABLE}&dm={encoded}"


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"app_id": ""}, ValueError),
        ({"app_id": "x&es=1"}, ValueError),
        ({"app_id": "x=y"}, ValueError),
        ({"app_id": "x\r\nHost: example"}, ValueError),
        ({"app_id": "x y"}, ValueError),
        ({"app_id": "앱"}, ValueError),
        ({"app_id": None}, TypeError),
        ({"state": -(1 << 63) - 1}, ValueError),
        ({"state": 1 << 63}, ValueError),
        ({"state": True}, TypeError),
        ({"state": "0"}, TypeError),
        ({"state": 0.0}, TypeError),
        ({"sdk_int": -1}, ValueError),
        ({"sdk_int": 1 << 31}, ValueError),
        ({"sdk_int": True}, TypeError),
        ({"sdk_int": "34"}, TypeError),
        ({"os_version": "synthetic"}, TypeError),
        ({"device_model": "synthetic"}, TypeError),
        ({"install_id": bytearray(b"synthetic")}, TypeError),
        ({"manufacturer": 0}, TypeError),
        ({"board": "synthetic"}, TypeError),
    ],
)
def test_invalid_inputs_are_rejected_before_serialization(kwargs: dict[str, object], error: type) -> None:
    with pytest.raises(error):
        build_dynapath_v2_diagnostic_header(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("path", sorted(DYNAPATH_ALLOWLIST_PATHS))
def test_selected_provider_sends_the_same_header_on_protected_paths(scripted_client_factory, path):
    client, requests, _ = scripted_client_factory([envelope(), envelope(), envelope()], config=v2_config())
    client.http.post_form(path, {"synthetic": "first"})
    client.http.post_form(path, {"synthetic": "second"})
    client.http.post_form(SERVICE)
    # 요청 내용과 무관한 고정 진단값이며, 보호 경로가 아닌 요청에는 붙이지 않습니다.
    assert [request.headers.get("x-dynapath-m-token") for request in requests] == [
        NATIVE_UNAVAILABLE,
        NATIVE_UNAVAILABLE,
        None,
    ]


def test_default_config_keeps_the_legacy_generator_and_profiles_reject_the_provider() -> None:
    default = KorailConfig()
    assert default.dynapath.token_provider is None and default.dynapath.token_settings is not None
    assert pickle.loads(pickle.dumps(dynapath_v2_diagnostic_token)) is dynapath_v2_diagnostic_token
    profile = KorailDeviceProfile("SYNTHETIC-ID", "SYNTHETIC-MODEL", "16", "SYNTHETIC-BUILD")
    with pytest.raises(ValueError, match="configurable DynaPath"):
        build_config_from_profile(profile, base=v2_config())
