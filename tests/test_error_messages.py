"""Message lookups and error policy stay offline and never change raw responses or retry decisions."""

import copy
import hashlib
import io
import json
import pickle
import runpy
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import pytest

import korail_mobile_api as api
from korail_mobile_api import errors as E
from korail_mobile_api._core.http import parse_base_response

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_provenance_and_shape():
    catalog = json.loads(files("korail_mobile_api").joinpath("error_messages.json").read_text(encoding="utf-8"))
    assert catalog["schema_version"] == 1 and catalog["app_version"] == "7.0.10"
    assert catalog["source"] == "assets/error_json.json"
    assert catalog["source_sha256"] == "7b7998f2582217aba20e58a722b3640a6ef3a2751d9816aaf2f78cfc97c74d00"
    messages = catalog["messages"]
    canonical = json.dumps(messages, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert (
        hashlib.sha256(canonical).hexdigest()
        == "7f6674b4fbf1ff60a4829ee8129bdfa0ee65c24a95a3e0fe6ddaa59e87df4885"
    )
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


@pytest.mark.parametrize(
    "source",
    [
        b'{"S003":"first","S003":"last"}',
        b'{"S003":"base","S003EN":"first","S003EN":"last"}',
        b'{"S003":123,"S003":"valid last"}',
        b'{"S003":"same","S003":"same"}',
    ],
)
def test_catalog_builder_rejects_duplicate_keys(source):
    builder = runpy.run_path(str(ROOT / "checks/build_error_catalog.py"))["build_catalog"]
    with pytest.raises(ValueError, match="duplicate.*S003"):
        builder(source, app_version="synthetic")


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


@pytest.mark.parametrize("language", ["ko", "ja", "jp", "zh", "cn"])
def test_7010_reservation_window_and_translation_fallback(language):
    expected = "예약은 열차출발 2개월 전 07시부터 열차출발 20분전까지 가능합니다."
    assert api.get_error_message("WRD000058", language=language) == expected
    assert api.resolve_error_message("WRD000058", language=language) == expected


def test_7010_reservation_window_preserves_english_asset_text():
    # The shipped English text still differs from Korean; do not silently translate or correct it.
    expected = "Reservation may be made from 30 minutes to 1 month prior to departure."
    assert api.get_error_message("WRD000058", language="en") == expected
    assert api.resolve_error_message("WRD000058", language="en") == expected


@pytest.mark.parametrize("message", [None, "", "<b>예약은 서버 안내를 따르세요.</b>"])
def test_7010_reservation_message_keeps_server_priority_and_raw(message):
    raw = {
        "strResult": "FAIL",
        "h_msg_cd": "WRD000058",
        "h_msg_txt": message,
        "synthetic": {"keep": [True]},
    }
    original = json.loads(json.dumps(raw))
    expected = (
        "예약은 서버 안내를 따르세요."
        if message
        else "예약은 열차출발 2개월 전 07시부터 열차출발 20분전까지 가능합니다."
    )
    with pytest.raises(api.KorailAppError) as caught:
        parse_base_response(raw)
    error = caught.value
    assert type(error) is api.KorailAppError
    assert error.display_message == expected
    assert error.message is message and error.raw is raw
    response = parse_base_response(raw, raise_on_fail=False)
    assert response.display_message == expected
    assert response.h_msg_txt is message and response.raw is raw
    assert raw == original
    if message:
        assert api.resolve_error_message("WRD000058", message, language="en") == expected


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


@pytest.mark.parametrize(
    "message,expected",
    [
        ("합성 범위 (0<SRCAR_NO<21)", "합성 범위 (0<SRCAR_NO<21)"),
        ("<b>합성 범위</b> (0<SRCAR_NO<21)", "합성 범위 (0<SRCAR_NO<21)"),
        ("A\nB (0<X<21)", "A\nB (0<X<21)"),
        ("1 <= n <= 20", "1 <= n <= 20"),
        ("<안내> %s, %ld, {{amount}}", "<안내> %s, %ld, {{amount}}"),
        ("A <b", "A <b"),
        ("A <b title='unfinished", "A <b title='unfinished"),
        ("A </b", "A </b"),
        ("A <", "A <"),
        ("A &amp", "A &"),
        ("A &#65", "A A"),
        ("A &#x41", "A A"),
        ("A &#x", "A &#x"),
        ("A &unknown", "A &unknown"),
        ("A &amp;lt;", "A &lt;"),
        ("&lt;script&gt;synthetic()&lt;/script&gt;", "<script>synthetic()</script>"),
        ("A<br>B<br/>C", "A\nB\nC"),
        ("A<b>B</b>C", "ABC"),
        ("A\n\n<div>B</div>", "A\n\nB"),
        ("<div>A\n\nB</div>", "A\n\nB"),
        ("A<script>synthetic()</script>B<style>body{}</style>C", "ABC"),
        ("A<script>synthetic(0<X<21)", "A"),
        ("A<style>body{color:red}&amp", "A"),
        ("A<script>synthetic()</scr", "A"),
        ("A<style>body{}</sty", "A"),
        ("A<script", "A"),
        ("A<STYLE type='unfinished", "A"),
        ("A<scripture", "A<scripture"),
        ("A<!--hidden-->B", "AB"),
        ("A<!--unfinished", "A"),
        ("A<!--unfinished<script>synthetic()</script>", "A"),
        ("A<!--unfinished--", "A"),
        ("A<!-", "A"),
        ("A<?unfinished", "A"),
        ("A<!DOCTYPE unfinished", "A"),
        ("A &amp<!--unfinished", "A &"),
        ("A\nB &amp", "A\nB &"),
    ],
)
def test_plain_display_preserves_text_and_original_response(message, expected):
    raw = {"strResult": "FAIL", "h_msg_cd": "SYNTHETIC-UNKNOWN", "h_msg_txt": message}
    original = copy.deepcopy(raw)
    with pytest.raises(api.KorailAppError) as caught:
        parse_base_response(raw)
    error = caught.value
    assert type(error) is api.KorailAppError
    assert error.display_message == expected
    assert error.message is message and error.raw is raw
    assert error.args == (f"SYNTHETIC-UNKNOWN: {message}",)
    assert str(error) == f"SYNTHETIC-UNKNOWN: {message}"
    response = parse_base_response(raw, raise_on_fail=False)
    assert response.display_message == expected
    assert response.h_msg_txt is message and response.raw is raw
    assert raw == original
    assert api.resolve_error_message(None, message) == expected


@pytest.mark.parametrize("tag", ["p", "div", "li", "tr"])
@pytest.mark.parametrize(
    "message,expected",
    [
        ("A<{tag}>B</{tag}>", "A\nB"),
        ("<{tag}>A</{tag}><{tag}>B</{tag}>", "A\nB"),
    ],
)
def test_plain_display_preserves_block_boundaries(tag, message, expected):
    message = message.format(tag=tag)
    raw = {"h_msg_cd": "SYNTHETIC-UNKNOWN", "h_msg_txt": message}
    assert api.resolve_error_message(None, message) == expected
    assert api.BaseKorailResponse.from_raw(raw).display_message == expected
    assert api.KorailAppError("SYNTHETIC-UNKNOWN", message, raw=raw).display_message == expected


@pytest.mark.parametrize(
    "code,language,expected",
    [
        ("WRS600022", "ko", "호차범위를 초과했습니다.(0<SRCAR_NO<21)"),
        ("WRS600022", "en", "Exceeds the maximum compartment number(0<SRCAR_NO<21)"),
        ("WRS600022", "ja", "号車範囲を超過しました。(0<SRCAR_NO<21)"),
        ("WRS600022", "zh", "超过号次范围(0<SRCAR_NO<21)"),
        (
            "WRS600162",
            "en",
            "The number of the tickets for cancellation exceeds the limit(0<the number of tickets for cancellation<11)",
        ),
        (
            "WRS600163",
            "en",
            "The number of the cancelled tickets exceeds the limit.(0<The number of the cancelled tickets<10)",
        ),
        (
            "WRS600164",
            "en",
            "Entered incorrect compartment number for cancellation(0<compartment for cancellation<21)",
        ),
        ("WRS600165", "en", "Entered incorrect seat number for cancellation(0<seat for cancellation<101)"),
    ],
)
def test_catalog_comparison_text_is_not_an_unfinished_html_tag(code, language, expected):
    assert api.get_error_message(code, language=language) == expected
    assert api.resolve_error_message(code, language=language) == expected


@pytest.mark.parametrize(
    "message",
    [
        None,
        "",
        "  \n ",
        "<script>synthetic()</script><style>body{}</style>",
        "<script>synthetic(0<X<21)",
        "<style>body{}",
        "<script",
        "<style type='unfinished",
        "<!--unfinished",
        "<?unfinished",
    ],
)
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
def test_new_failure_response_is_sent_once_and_can_be_returned_as_a_model(
    code, exception, scripted_client_factory
):
    raw = {"strResult": "FAIL", "h_msg_cd": code, "h_msg_txt": "", "synthetic": {"keep": True}}
    client, requests, _ = scripted_client_factory(
        [raw, raw],
        config=api.KorailConfig(
            base_url="https://offline.invalid", disable_dynapath=True, netfunnel_enabled=False
        ),
    )
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
        "import sys; sys.path.insert(0, sys.argv[1]); "
        "from korail_mobile_api.errors import _messages; "
        "from korail_mobile_api import get_error_message; "
        "assert _messages.cache_info().currsize == 0; "
        "assert get_error_message('S003') is not None; "
        "assert _messages.cache_info().currsize == 1"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(ROOT / "src")],
        env=f8_subprocess_env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def _v2_reduce(error: E.KorailApiError) -> tuple[object, ...]:
    """The __reduce__ shapes 2.6.2 wrote; unset attributes lived on the class, not in the state."""
    state = {name: value for name, value in error.__dict__.items() if value is not None}
    if isinstance(error, E.KorailAuthContinuationRequired):
        return (type(error), (error.redirect_url,), state)
    if isinstance(
        error,
        (E.KorailAppError, E.KorailNetFunnelError, E.KorailSessionExpiredError, E.KorailAccountLockedError),
    ):
        return (type(error), (error.code, error.message), state)
    return (type(error), error.args, state)


class _V2Pickler(pickle.Pickler):
    def reducer_override(self, obj: object) -> object:
        return _v2_reduce(obj) if isinstance(obj, E.KorailApiError) else NotImplemented


V2_ERRORS = [
    E.KorailTransportError("synthetic transport", raw=b"synthetic body"),
    E.KorailProtocolError("synthetic protocol", raw={"synthetic": True}),
    E.KorailAuthError("synthetic auth", code="SYNTH", message="synthetic", raw={"k": "v"}),
    E.KorailSessionExpiredError("P058", "synthetic", raw={"k": "v"}),
    E.KorailAccountLockedError("WRC000390", "synthetic", raw={"k": "v"}),
    E.KorailDynaPathError("synthetic block", raw={"code": -2000}),
    E.KorailAuthContinuationRequired("/synthetic", raw={"h_msg_cd": "WRC000116", "h_msg_txt": "synthetic"}),
    E.KorailSoldOutError("ERR211161", "synthetic", raw={"k": "v"}),
    E.KorailQueueRejectedError("301", "synthetic", raw="301:key=synthetic"),
    E.KorailDynaPathRequiredError("synthetic"),
]


@pytest.mark.parametrize("error", V2_ERRORS, ids=lambda error: type(error).__name__)
def test_errors_pickled_by_2x_still_load(error: E.KorailApiError) -> None:
    buffer = io.BytesIO()
    _V2Pickler(buffer, protocol=2).dump(error)
    # Bytes produced in this test from synthetic values, not untrusted input.
    restored = pickle.loads(buffer.getvalue())
    assert type(restored) is type(error) and restored.args == error.args and str(restored) == str(error)
    for name in ("code", "message", "raw", "redirect_url"):
        assert getattr(restored, name, None) == getattr(error, name, None)


@pytest.mark.parametrize("error", V2_ERRORS, ids=lambda error: type(error).__name__)
def test_errors_survive_pickle_and_copy_with_notes_and_3x_fields(error: E.KorailApiError) -> None:
    error = copy.copy(error)
    error.request_sent = True
    error.add_note("synthetic note")
    for restored in (pickle.loads(pickle.dumps(error)), copy.copy(error), copy.deepcopy(error)):
        assert type(restored) is type(error) and restored.args == error.args
        assert restored.__dict__ == error.__dict__
