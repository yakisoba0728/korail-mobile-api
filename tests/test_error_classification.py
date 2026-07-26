"""The ``h_msg_cd`` taxonomy: what each server code means, and what it may not do.

The load-bearing property here is NEGATIVE. Classification chooses which
:class:`KorailAppError` subclass describes a failure; it must never decide that
there IS one. The app works the same way — its dispatcher recognises a handful
of codes and then drops every other code on a non-``FAIL`` response straight
through to ``onReceive()`` as a success
(``analysis/jadx/sources/com/korail/talk/view/base/BaseActivity.java:629``) —
and this repository has live proof it matters: ``WRR664296`` arrived alongside a
real, cancelable PNR.
"""

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailConfig
from korail_mobile_api.errors import (
    APP_UPDATE_REQUIRED_CODE,
    INVALID_REQUEST_CODES,
    NO_DIRECT_TRAIN_CODE,
    NO_RESULT_CODES,
    NOT_ENTITLED_CODES,
    RESERVATION_REFUSED_CODES,
    SEAT_UNAVAILABLE_CODES,
    SERVICE_UNAVAILABLE_CODE,
    SOLD_OUT_CODES,
    KorailApiError,
    KorailAppError,
    KorailAppUpdateRequiredError,
    KorailAuthError,
    KorailDynaPathError,
    KorailInvalidRequestError,
    KorailNoDirectTrainError,
    KorailNoResultsError,
    KorailNotEntitledError,
    KorailReservationRefusedError,
    KorailSeatUnavailableError,
    KorailServiceUnavailableError,
    KorailSessionExpiredError,
    KorailSoldOutError,
    classify_app_error,
)
from korail_mobile_api.http import KorailHttpClient, parse_base_response
from korail_mobile_api.read_parsers import parse_reservation_history_response


STATION_PATH = "/classes/com.korail.mobile.common.stationinfo"


def _envelope(code, message="", result="SUCC", **extra):
    return {
        "h_msg_cd": code,
        "h_msg_txt": message,
        "strResult": result,
        **extra,
    }


# ---------------------------------------------------------------------------
# Compatibility: every new type refines the one it replaces.
# ---------------------------------------------------------------------------

REFINEMENTS = (
    KorailNoResultsError,
    KorailNoDirectTrainError,
    KorailSoldOutError,
    KorailSeatUnavailableError,
    KorailReservationRefusedError,
    KorailInvalidRequestError,
    KorailNotEntitledError,
    KorailServiceUnavailableError,
    KorailAppUpdateRequiredError,
)


@pytest.mark.parametrize("subclass", REFINEMENTS)
def test_every_new_app_error_subclasses_the_one_it_replaces(subclass):
    # An existing `except KorailAppError` must keep catching everything it
    # caught before this taxonomy existed, so no caller's error handling
    # silently changes meaning.
    assert issubclass(subclass, KorailAppError)
    assert issubclass(subclass, KorailApiError)


def test_no_direct_train_refines_no_results():
    # WRD000061 renders the empty train list behind its dialog
    # (DirectInquiryActivity.java:630), so "nothing matched" still describes it.
    assert issubclass(KorailNoDirectTrainError, KorailNoResultsError)


def test_session_expiry_stays_an_auth_error_outside_the_app_taxonomy():
    # P058 is answered before the code map is consulted and must not be dragged
    # into KorailAppError, which would change what `except KorailAuthError`
    # catches.
    assert issubclass(KorailSessionExpiredError, KorailAuthError)
    assert not issubclass(KorailSessionExpiredError, KorailAppError)


# ---------------------------------------------------------------------------
# The map itself.
# ---------------------------------------------------------------------------

MAPPED = [
    *((code, KorailNoResultsError) for code in sorted(NO_RESULT_CODES)),
    (NO_DIRECT_TRAIN_CODE, KorailNoDirectTrainError),
    *((code, KorailSoldOutError) for code in sorted(SOLD_OUT_CODES)),
    *(
        (code, KorailSeatUnavailableError)
        for code in sorted(SEAT_UNAVAILABLE_CODES)
    ),
    *(
        (code, KorailReservationRefusedError)
        for code in sorted(RESERVATION_REFUSED_CODES)
    ),
    *(
        (code, KorailInvalidRequestError)
        for code in sorted(INVALID_REQUEST_CODES)
    ),
    *((code, KorailNotEntitledError) for code in sorted(NOT_ENTITLED_CODES)),
    (SERVICE_UNAVAILABLE_CODE, KorailServiceUnavailableError),
    (APP_UPDATE_REQUIRED_CODE, KorailAppUpdateRequiredError),
]


@pytest.mark.parametrize("code, expected", MAPPED)
def test_classify_app_error_maps_each_documented_code(code, expected):
    error = classify_app_error(code, "메시지", raw={"h_msg_cd": code})
    assert type(error) is expected
    assert error.code == code
    assert error.raw == {"h_msg_cd": code}


def test_live_observed_codes_land_where_this_session_saw_them():
    # The codes this repository actually captured on the wire, spelled out
    # rather than derived from the frozensets, so a careless edit to a set is
    # caught here.
    assert type(classify_app_error("P100", "검색된 데이터가 없습니다.")) is (
        KorailNoResultsError
    )
    assert type(classify_app_error("WRT300005", "조회자료가 없습니다.")) is (
        KorailNoResultsError
    )
    assert type(classify_app_error("ERR299943", "예약할인이 지원되지 않습니다")) is (
        KorailNotEntitledError
    )
    assert type(classify_app_error("WRG200018", "입력값오류(PNR번호)")) is (
        KorailInvalidRequestError
    )
    assert type(classify_app_error("WRT100002", "창구번호미입력,미승인창구")) is (
        KorailInvalidRequestError
    )
    assert type(classify_app_error("WRT100124", "반환번호를 확인해주세요")) is (
        KorailInvalidRequestError
    )


def test_sold_out_is_the_code_the_apk_branches_on():
    # ERR211161 -> tss_dialog_no_left_seat at TCSOptionsActivity.java:551 and
    # SpecialRoomUpgradeActivity.java:314.
    assert type(classify_app_error("ERR211161", "")) is KorailSoldOutError


def test_srtgo_sold_out_claim_is_not_encoded():
    # srtgo claims sold-out is {IRT010110, ERR211161} (srtgo/srtgo/ktx.py:388).
    # IRT010110 is 0-hit across jadx, all three smali trees, analysis/raw and
    # analysis/splits, so it stays third-party-attested only and must NOT be
    # silently promoted into the map.
    assert "IRT010110" not in SOLD_OUT_CODES
    assert type(classify_app_error("IRT010110", "")) is KorailAppError


def test_seat_unavailable_is_distinct_from_sold_out():
    # The app offers "임의 좌석 배정" for WRI411345 (two-button dialog,
    # SpecialRoomUpgradeActivity.java:312-313) but a dead-end alert for
    # ERR211161 three lines later, so a caller must be able to tell them apart.
    assert not issubclass(KorailSeatUnavailableError, KorailSoldOutError)
    assert not issubclass(KorailSoldOutError, KorailSeatUnavailableError)
    assert SEAT_UNAVAILABLE_CODES.isdisjoint(SOLD_OUT_CODES)


def test_unknown_codes_keep_the_previous_plain_app_error():
    error = classify_app_error("ZZZ999999", "새로운 오류", raw={"a": 1})
    assert type(error) is KorailAppError
    assert error.code == "ZZZ999999"
    assert error.message == "새로운 오류"
    assert error.raw == {"a": 1}


def test_absent_code_keeps_the_previous_plain_app_error():
    error = classify_app_error(None, None)
    assert type(error) is KorailAppError
    assert error.code is None
    assert str(error) == "UNKNOWN:"


def test_every_mapped_code_is_unique_across_the_sets():
    groups = [
        NO_RESULT_CODES,
        {NO_DIRECT_TRAIN_CODE},
        SOLD_OUT_CODES,
        SEAT_UNAVAILABLE_CODES,
        RESERVATION_REFUSED_CODES,
        INVALID_REQUEST_CODES,
        NOT_ENTITLED_CODES,
        {SERVICE_UNAVAILABLE_CODE},
        {APP_UPDATE_REQUIRED_CODE},
    ]
    seen = [code for group in groups for code in group]
    assert len(seen) == len(set(seen))
    # P058 is deliberately absent: it never reaches the app-error map.
    assert "P058" not in seen


# ---------------------------------------------------------------------------
# The negative property: classification never invents a failure.
# ---------------------------------------------------------------------------

# Codes the APK itself carries on a SUCCESSFUL response, plus the ones this
# repository observed live on successful mutations. None may raise.
SUCCESS_SIDE_CODES = [
    # Live-observed by this repository, this session.
    ("WRR664296", "KTX/새마을호/ITX-청춘 열차의 경로 및 장애인(4-6급)할인은 "
                  "토/일/공휴일에는 적용되지 않습니다."),
    ("IRR000018", "결제하지 않으면 예약이 취소됩니다."),
    ("IRR000001", "예약가능합니다."),
    ("IRG000000", "정상처리되었습니다"),
    ("IRT000000", "정상발매처리,정상발권처리"),
    ("IRT200277", "반환이 정상 처리되었습니다"),
    # APK-attested success/advisory codes.
    ("IRR000014", ""),   # waitlist accepted -- ui/inquiry/rir/orr/a.java:223
    ("IRT800005", ""),   # reserved with a notice -- .../orr/a.java:142
    ("WRS800036", ""),   # per-leg advisory -- DReservationConfirmActivity.java:76
    ("IRZ000001", ""),   # login success -- S4/u.java:131
    ("S200", ""),        # login success -- S4/u.java:131
    ("MRT200105", ""),   # upgrade quote accepted -- SpecialRoomUpgradeActivity.java:55
]


@pytest.mark.parametrize("code, message", SUCCESS_SIDE_CODES)
def test_a_successful_response_never_raises_whatever_its_code(code, message):
    response = parse_base_response(_envelope(code, message, result="SUCC"))
    assert response.h_msg_cd == code
    assert response.str_result == "SUCC"


def test_warning_that_accompanies_a_successful_reservation_stays_a_success():
    # The live proof. WRR664296 came back with strResult=SUCC and a real,
    # cancelable PNR (docs/MUTATION_HANDOFF.md:181-184). It is NOT the reserve
    # success code IRR000018, and nothing in this package may treat a
    # non-IRR000018 code as a failure.
    raw = _envelope(
        "WRR664296",
        "KTX/새마을호/ITX-청춘 열차의 경로 및 장애인(4-6급)할인은 "
        "토/일/공휴일에는 적용되지 않습니다.",
        result="SUCC",
        h_pnr_no="123456789",
    )
    response = parse_base_response(raw)
    assert response.h_msg_cd == "WRR664296"
    assert response.h_msg_cd != "IRR000018"
    assert response.raw["h_pnr_no"] == "123456789"


def test_a_mapped_code_on_a_successful_response_still_does_not_raise():
    # The sharpest form of the rule: even a code the map knows how to classify
    # must not become an exception when the server did not declare a failure.
    for code in sorted(SOLD_OUT_CODES | NO_RESULT_CODES | SEAT_UNAVAILABLE_CODES):
        response = parse_base_response(_envelope(code, "", result="SUCC"))
        assert response.h_msg_cd == code


def test_classification_over_http_only_refines_an_existing_failure():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_envelope("ERR211161", "잔여석 부족", result="FAIL"),
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailSoldOutError) as excinfo:
        client.get_json(STATION_PATH)
    # Still a KorailAppError, so an existing handler is unaffected.
    assert isinstance(excinfo.value, KorailAppError)
    assert excinfo.value.code == "ERR211161"


def test_http_raise_on_fail_disabled_still_returns_a_mapped_code():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_envelope("P100", "없음", result="FAIL"))

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json(STATION_PATH, raise_on_fail=False)
    assert response.h_msg_cd == "P100"


def test_wrc000288_keeps_its_independent_failure_behaviour():
    # The app treats WRC000288 as a failure regardless of strResult
    # (BaseActivity.java:620); classification must not have loosened that.
    with pytest.raises(KorailAppError) as excinfo:
        parse_base_response(_envelope("WRC000288", "오류", result="SUCC"))
    assert type(excinfo.value) is KorailAppError


def test_session_expiry_still_wins_over_the_code_map():
    with pytest.raises(KorailSessionExpiredError) as excinfo:
        parse_base_response(_envelope("P058", "세션 만료", result="FAIL"))
    assert not isinstance(excinfo.value, KorailAppError)


# ---------------------------------------------------------------------------
# The read-parser path.
# ---------------------------------------------------------------------------

def test_accepted_empty_codes_still_return_a_result_rather_than_raising():
    # parse_reservation_history_response opts P100 in as a non-fatal empty
    # result. Classification must not reach it: an opted-in code returns an
    # empty response object, it does not raise KorailNoResultsError.
    result = parse_reservation_history_response(
        _envelope("P100", "검색된 데이터가 없습니다.", result="FAIL")
    )
    assert result.h_msg_cd == "P100"
    assert tuple(result.trains) == ()


def test_read_parser_failures_are_refined_too():
    with pytest.raises(KorailNoDirectTrainError) as excinfo:
        parse_reservation_history_response(
            _envelope("WRD000061", "직통열차가 없습니다.", result="FAIL")
        )
    assert isinstance(excinfo.value, KorailNoResultsError)
    assert isinstance(excinfo.value, KorailAppError)
    assert excinfo.value.code == "WRD000061"


# ---------------------------------------------------------------------------
# Anti-macro: a header decision, not a code.
# ---------------------------------------------------------------------------

def test_anti_macro_rejection_arrives_as_a_dynapath_error_not_an_app_error():
    # BaseDaoHelper.java:59-86 reads DynaPath-Result, pulls `message` from the
    # body and shows it INSTEAD of running the h_msg_cd ladder
    # (BaseActivity.java:632-634). There is no anti-macro message code, so
    # nothing in the taxonomy claims one.
    path = "/classes/com.korail.mobile.seatMovie.ScheduleView"
    assert path in korail_mobile_api.DYNAPATH_ALLOWLIST_PATHS

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            headers={"DynaPath-Result": "-1"},
            json={"message": "비정상적인 접속이 감지되었습니다."},
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailDynaPathError) as excinfo:
        client.post_form(path)
    assert not isinstance(excinfo.value, KorailAppError)
    assert "비정상적인 접속" in str(excinfo.value)


def test_no_code_is_classified_by_the_macro_substring():
    # srtgo_plus classifies on `"MACRO" in code or "MACRO" in msg`
    # (srtgo/srtgo.py:756). That substring is 0-hit in this app as a server
    # code or message, so we must not have copied the heuristic.
    assert type(classify_app_error("MACRO_BLOCK", "MACRO detected")) is (
        KorailAppError
    )


# ---------------------------------------------------------------------------
# Public surface.
# ---------------------------------------------------------------------------

def test_taxonomy_is_exported():
    exported = (
        "KorailAppUpdateRequiredError",
        "KorailInvalidRequestError",
        "KorailNoDirectTrainError",
        "KorailNoResultsError",
        "KorailNotEntitledError",
        "KorailReservationRefusedError",
        "KorailSeatUnavailableError",
        "KorailServiceUnavailableError",
        "KorailSoldOutError",
        "classify_app_error",
    )
    for name in exported:
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name)


def test_every_refinement_documents_itself():
    for subclass in REFINEMENTS:
        assert subclass.__doc__, f"{subclass.__name__} needs a docstring"


def test_messages_stay_redacted_through_classification():
    # KorailAppError redacts its rendered message; a subclass must not have lost
    # that, and a payment failure is exactly where a PAN could echo back.
    error = classify_app_error("ERR299943", "카드 4111111111111111 오류")
    assert "4111111111111111" not in str(error)
    assert "[REDACTED_CARD]" in str(error)
    # ``message`` stays verbatim so a caller can still match on the original.
    assert error.message == "카드 4111111111111111 오류"
