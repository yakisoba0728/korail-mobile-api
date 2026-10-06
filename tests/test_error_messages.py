"""Message lookups and error policy stay offline and never change raw responses or retry decisions."""

import hashlib
import json
import pickle
import runpy
import subprocess
import sys
from contextlib import closing
from importlib.resources import files
from pathlib import Path

import httpx
import pytest

import korail_mobile_api as api
from korail_mobile_api import errors as E
from korail_mobile_api.http import parse_base_response

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_provenance_and_shape():
    catalog = json.loads(files("korail_mobile_api").joinpath("error_messages.json").read_text(encoding="utf-8"))
    assert catalog["schema_version"] == 1 and catalog["app_version"] == "7.0.8"
    assert catalog["source"] == "assets/error_json.json"
    assert catalog["source_sha256"] == "e5fc297b09f25efae609c42e2c341cb131ca257be9a991a2add9898ddda50038"
    messages = catalog["messages"]
    assert len(messages) == 10305
    assert sum(len(translations) for translations in messages.values()) == 17256
    builder = runpy.run_path(str(ROOT / "checks/build_error_catalog.py"))
    for code, translations in messages.items():
        assert builder["RESULT_CODE"].fullmatch(code)
        assert "ko" in translations
        assert translations.keys() <= {"ko", "en", "ja", "zh"}
        assert all(isinstance(text, str) for text in translations.values())


def test_catalog_builder_keeps_only_result_messages_and_translations():
    builder = runpy.run_path(str(ROOT / "checks/build_error_catalog.py"))["build_catalog"]
    source = json.dumps(
        {
            "S003": "합성 서비스 오류",
            "S003EN": "synthetic service error",
            "S003JP": "合成エラー",
            "S003CN": "合成错误",
            "S-ERR911411": "합성 출발 후 예약 거절",
            "API.E00000": "synthetic protocol message",
            "ServiceContraint": "synthetic setting",
            "secret001": "synthetic unrelated resource",
            "WRT123456EN": "synthetic orphan translation",
        }
    ).encode()
    catalog = builder(source, app_version="synthetic")
    assert catalog["source_sha256"] == hashlib.sha256(source).hexdigest()
    assert catalog["messages"] == {
        "API.E00000": {"ko": "synthetic protocol message"},
        "S-ERR911411": {"ko": "합성 출발 후 예약 거절"},
        "S003": {
            "ko": "합성 서비스 오류",
            "en": "synthetic service error",
            "ja": "合成エラー",
            "zh": "合成错误",
        },
    }
    for invalid in ([], {"S003": 123}, {"S003": None}):
        with pytest.raises(ValueError):
            builder(json.dumps(invalid).encode(), app_version="synthetic")


@pytest.mark.parametrize("language", ["en", "en-US", "EN_us"])
def test_catalog_english_locale(language):
    assert api.get_error_message("S003", language=language) == "API Error"


@pytest.mark.parametrize("language", ["ja", "jp", "ja-JP", "zh", "cn", "zh-CN"])
def test_catalog_translation_aliases(language):
    canonical = "ja" if language.split("-")[0] in {"ja", "jp"} else "zh"
    message = api.get_error_message("WRT900900", language=language)
    assert message == api.get_error_message("WRT900900", language=canonical)
    assert message and message != api.get_error_message("WRT900900")


def test_catalog_korean_fallback_unknown_and_exceptional_code():
    assert api.get_error_message("BT019", language="en") == "요청횟수(6회)를 초과하였습니다."
    assert "출발시각 이후" in api.get_error_message("S-ERR911411")
    for code in (None, "", "SYNTHETIC-UNKNOWN", "ServiceContraint", "secret001"):
        assert api.get_error_message(code) is None


@pytest.mark.parametrize("function", [api.get_error_message, api.resolve_error_message])
def test_message_locale_validation(function):
    with pytest.raises(ValueError, match="language"):
        function("S003", language="unsupported")


def test_server_message_priority_plain_text_and_raw_preservation():
    raw = {"strResult": "FAIL", "h_msg_cd": "S003", "h_msg_txt": "<b>서버 안내</b><br/>A &amp; B"}
    with pytest.raises(api.KorailServiceUnavailableError) as caught:
        parse_base_response(raw)
    error = caught.value
    assert error.display_message == "서버 안내\nA & B"
    assert error.message == raw["h_msg_txt"] and error.raw is raw
    assert str(error) == "S003: <b>서버 안내</b><br/>A &amp; B"
    assert api.resolve_error_message("S003", "서버 원문", language="en") == "서버 원문"


@pytest.mark.parametrize("message", [None, "", "  \n ", "<script>synthetic()</script><style>body{}</style>"])
def test_missing_or_unreadable_server_message_uses_catalog(message):
    error = E.classify_app_error("BT019", message)
    assert error.display_message == "요청횟수(6회)를 초과하였습니다."
    assert error.message is message
    assert api.resolve_error_message("S003", message, language="en") == "API Error"
    assert api.resolve_error_message("SYNTHETIC-UNKNOWN", message) is None


def test_session_script_is_data_and_display_does_not_decide_session_state():
    assert "location.replace" in api.get_error_message("P058")
    assert api.resolve_error_message("P058") == "로그인이 만료되었습니다. 다시 로그인해 주세요."
    assert api.resolve_error_message("P058", language="en") == "Your session has expired. Please log in again."
    raw = {"strResult": "SUCC", "h_msg_cd": "P058"}
    response = parse_base_response(raw)
    assert response.str_result == "SUCC" and response.raw is raw
    assert response.display_message == api.resolve_error_message("P058")
    assert type(E.classify_app_error("P058", None)) is api.KorailAppError


@pytest.mark.parametrize("code", ["ERR800007", "S035", "P092", "WRC000390"])
def test_catalog_membership_does_not_add_an_error_class_or_session_transition(code):
    raw = {"strResult": "FAIL", "h_msg_cd": code, "h_msg_txt": ""}
    with pytest.raises(api.KorailAppError) as caught:
        parse_base_response(raw)
    assert type(caught.value) is api.KorailAppError
    assert caught.value.message == "" and caught.value.raw is raw
    assert caught.value.display_message == api.resolve_error_message(code)
    assert caught.value.display_message


NEW_FAILURES = [
    ("S000", api.KorailServiceUnavailableError),
    ("S001", api.KorailServiceUnavailableError),
    ("S002", api.KorailServiceUnavailableError),
    ("S003", api.KorailServiceUnavailableError),
    ("BT019", api.KorailRateLimitError),
    ("BT023", api.KorailRateLimitError),
    ("WRT900900", api.KorailProcessingError),
    ("EZZ000014", api.KorailAlreadyProcessedError),
    ("EVZ000102", api.KorailAlreadyProcessedError),
]


@pytest.mark.parametrize("code,exception", NEW_FAILURES)
def test_new_failure_response_is_sent_once_and_can_be_returned_as_a_model(code, exception):
    requests = []
    raw = {"strResult": "FAIL", "h_msg_cd": code, "h_msg_txt": "", "synthetic": {"keep": True}}

    def reply(request):
        requests.append(request)
        return httpx.Response(200, json=raw)

    with closing(
        api.KorailClient(
            api.KorailConfig(base_url="https://offline.invalid", disable_dynapath=True),
            transport=httpx.MockTransport(reply),
        )
    ) as client:
        with pytest.raises(exception) as caught:
            client.http.post_form("/synthetic", {})
        assert len(requests) == 1
        assert caught.value.raw == raw and caught.value.message == ""
        assert caught.value.display_message
        response = client.http.post_form("/synthetic", {}, raise_on_fail=False)
        assert len(requests) == 2
        assert response.str_result == "FAIL" and response.h_msg_txt == "" and response.raw == raw
        assert response.display_message == caught.value.display_message
    success_raw = {**raw, "strResult": "SUCC"}
    assert parse_base_response(success_raw).str_result == "SUCC"


@pytest.mark.parametrize(
    "code,exception",
    NEW_FAILURES + [("WRC000390", api.KorailAccountLockedError), ("P058", api.KorailSessionExpiredError)],
)
def test_new_errors_survive_pickle_without_losing_original_fields(code, exception):
    error = exception(code, None, raw={"synthetic": ["keep"]})
    error.parser_raw = {"partial": True}
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is exception
    assert restored.code == code and restored.message is None
    assert restored.raw == error.raw and restored.parser_raw == error.parser_raw
    assert restored.args == error.args and restored.display_message == error.display_message


def test_catalog_is_loaded_lazily(f8_subprocess_env):
    code = (
        "from korail_mobile_api.error_messages import _messages; "
        "from korail_mobile_api import get_error_message; "
        "assert _messages.cache_info().currsize == 0; "
        "assert get_error_message('S003') is not None; "
        "assert _messages.cache_info().currsize == 1"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], env=f8_subprocess_env, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
