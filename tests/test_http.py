# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

import inspect
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api as api
from korail_mobile_api import KorailConfig
from korail_mobile_api.constants import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    KORAIL_API_VERSION,
    KORAIL_APP_KEY,
    KORAIL_COMMON_CODE_BOOTSTRAP_CODES,
    KORAIL_DEFAULT_ANDROID_OS_RELEASE,
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEVICE_ANDROID,
)
from korail_mobile_api.dynapath import (
    KORAIL_DYNAPATH_AS_VALUE,
    KORAIL_DYNAPATH_SDK_VERSION,
    DynapathConfig,
    DynapathTokenGenerator,
    DynapathTokenSettings,
)
from korail_mobile_api.errors import (
    KorailApiError,
    KorailAppError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)
from korail_mobile_api.http import KorailHttpClient, parse_base_response
from korail_mobile_api.safety import (
    EXCLUDED_API_DOMAINS,
    KORAIL_EXACT_FORM_FIELDS,
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_korail_origin,
    assert_read_only_request_fields,
    assert_read_only_route,
)


# Complete request bodies for the two read routes the transport tests below
# use as vehicles, minus the common three that post_form adds itself. The tests
# are about headers, encoding, origins and error classification, not about
# these routes, but both have a field contract, so a bare post_form(route) is
# refused before it is sent. Literal values, not the session builders: this
# file tests the HTTP layer on its own.
LOGIN_FORM = {
    "txtMemberNo": "SYNTHETIC_MEMBER",
    "txtPwd": "SYNTHETIC_PASSWORD",
    "txtInputFlg": "2",
    "checkValidPw": "Y",
}
# The plain success answer most transport tests reply with.
_IRG_OK = {"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"}
COMMON_CODE_FORM = {
    "code": ["app.login.cphd"],
    "deviceWidth": 1080,
    "deviceHeight": 2400,
    "OSVersion": 35,
}


def test_delay_discount_post_query_map_places_fields_in_url_and_empty_form_body():
    captured = {}
    path = "/classes/com.korail.mobile.passCard.DelayDiscountView"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200, json={"h_msg_cd": "S000", "h_msg_txt": "OK", "strResult": "SUCC"}
        )

    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True), transport=httpx.MockTransport(handler)
    )
    client.post_query(path, {"h_page_no": "20991231"})
    request = captured["request"]
    assert request.method == "POST"
    assert request.url.path == path
    assert parse_qs(request.url.query.decode())["h_page_no"] == ["20991231"]
    assert set(parse_qs(request.url.query.decode())) == {
        "Device", "Version", "Key", "h_page_no"
    }
    assert request.content == b""
    assert request.headers["content-type"].startswith("application/x-www-form-urlencoded")


def test_post_query_rejects_unregistered_path_before_io():
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        raise AssertionError("no request expected")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    with pytest.raises(KorailProtocolError, match="only for DelayDiscountView"):
        client.post_query("/classes/com.korail.mobile.login.Login", {"custId": "x"})
    assert called is False


def test_delay_discount_post_query_can_return_envelope_free_object():
    path = "/classes/com.korail.mobile.passCard.DelayDiscountView"
    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, json={"discountTickets": []})
        ),
    )
    response = client.post_query(
        path, {"h_page_no": "20991231"}, require_envelope=False
    )
    assert response.raw == {"discountTickets": []}


def test_post_form_adds_common_fields_and_form_encoding():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers["content-type"]
        captured["connection"] = request.headers["connection"]
        captured["body"] = request.content.decode()
        return httpx.Response(
            200, json=_IRG_OK
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.post_form(
        "/classes/com.korail.mobile.common.code.do",
        COMMON_CODE_FORM,
    )

    assert captured["url"] == (
        "https://smart.letskorail.com/classes/com.korail.mobile.common.code.do"
    )
    assert captured["content_type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    assert captured["connection"] == "close"
    assert "Device=AD" in captured["body"]
    assert "Version=250601003" in captured["body"]
    assert "Key=korail1234567890" in captured["body"]
    assert "code=app.login.cphd" in captured["body"]
    assert "OSVersion=35" in captured["body"]
    assert response.h_msg_cd == "IRG000000"


def test_korail_runtime_constants_are_importable():
    assert KORAIL_DEVICE_ANDROID == "AD"
    assert KORAIL_API_VERSION == "250601003"
    assert KORAIL_APP_KEY == "korail1234567890"
    assert KORAIL_DEFAULT_ANDROID_SDK_INT == 35
    assert "app.login.cphd" in KORAIL_COMMON_CODE_BOOTSTRAP_CODES
    assert KORAIL_DEFAULT_ANDROID_OS_RELEASE == "15"
    assert KORAIL_DYNAPATH_AS_VALUE == "[38ff229cb34c7dda8e28220a2d750cce]"
    assert KORAIL_DYNAPATH_SDK_VERSION == "v1.0.3"
    assert KORAIL_DEFAULT_DEVICE_NAME
    assert DYNAPATH_HEADER_NAME == "x-dynapath-m-token"
    assert DynapathTokenGenerator
    assert not hasattr(api, "KorailProbeDynapathTokenProvider")
    assert not hasattr(api, "generate_korail_probe_dynapath_token")
    assert "/classes/com.korail.mobile.login.Login" in DYNAPATH_ALLOWLIST_PATHS


def test_os_release_and_sdk_int_are_distinct_app_values():
    # The DynaPath "os" field is Build.VERSION.RELEASE (b/C1229b.java:128-131),
    # i.e. "15" for Android 15. Build.VERSION.SDK_INT (35) is a different value
    # the app only sends as the integer OSVersion field on common.code.do
    # (CommonService.java:32). The two constants used to hold the same number
    # with different meanings, which is how "35" ended up as the release string.
    assert KORAIL_DEFAULT_ANDROID_OS_RELEASE != str(
        KORAIL_DEFAULT_ANDROID_SDK_INT
    )
    assert isinstance(KORAIL_DEFAULT_ANDROID_OS_RELEASE, str)
    assert isinstance(KORAIL_DEFAULT_ANDROID_SDK_INT, int)
    # The default reaches the wire only through a custom token_provider: it is
    # surfaced on DynapathRequestContext, while the built-in generator reads
    # DynapathTokenSettings.os_version, which has no default at all.
    assert (
        DynapathConfig().os_version == KORAIL_DEFAULT_ANDROID_OS_RELEASE
    )
    assert "os_version" not in {
        name
        for name, parameter in inspect.signature(
            DynapathTokenSettings
        ).parameters.items()
        if parameter.default is not inspect.Parameter.empty
    }


def test_post_form_adds_dynapath_header_for_allowlisted_path():
    captured = {}
    contexts = []

    def token_provider(context):
        contexts.append(context)
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        return httpx.Response(
            200, json=_IRG_OK
        )

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    response = client.post_form("/classes/com.korail.mobile.login.Login", LOGIN_FORM)

    assert response.str_result == "SUCC"
    assert captured["token"] == "dynapath-token"
    assert len(contexts) == 1
    assert contexts[0].method == "POST"
    assert contexts[0].path == "/classes/com.korail.mobile.login.Login"
    assert contexts[0].device == KORAIL_DEVICE_ANDROID
    assert contexts[0].device_name == KORAIL_DEFAULT_DEVICE_NAME


def test_dynapath_provider_is_not_called_for_non_allowlisted_path():
    called = False

    def token_provider(_context):
        nonlocal called
        called = True
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get(DYNAPATH_HEADER_NAME) is None
        return httpx.Response(
            200, json=_IRG_OK
        )

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form("/classes/com.korail.mobile.common.code.do", COMMON_CODE_FORM)

    assert called is False


def test_get_json_adds_dynapath_header_for_allowlisted_path_by_default():
    captured = {}
    contexts = []
    path = "/classes/com.korail.mobile.product.ReservationList"

    def token_provider(context):
        contexts.append(context)
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "OK",
                "strResult": "SUCC",
            },
        )

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({path}),
        )
    )
    client = KorailHttpClient(
        config,
        transport=httpx.MockTransport(handler),
    )

    response = client.get_json(
        path, {"txtSelPage": "1", "txtCntPerPage": "20"}, include_common=True
    )

    assert response.str_result == "SUCC"
    assert captured["token"] == "dynapath-token"
    assert len(contexts) == 1
    assert contexts[0].method == "GET"
    assert contexts[0].path == path


def test_get_json_returns_parsed_response():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["query"] = request.url.query.decode()
        return httpx.Response(
            200, json=_IRG_OK
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json(
        "/classes/com.korail.mobile.product.ReservationList",
        {"txtSelPage": "1", "txtCntPerPage": "20"},
        include_common=True,
    )

    assert captured["url"].startswith(
        "https://smart.letskorail.com/classes/com.korail.mobile.product.ReservationList?"
    )
    assert parse_qs(captured["query"]) == {
        "Device": [client.config.device],
        "Version": [client.config.version],
        "Key": [client.config.key],
        "txtSelPage": ["1"],
        "txtCntPerPage": ["20"],
    }
    assert response.str_result == "SUCC"


def test_get_json_can_return_raw_object_without_korail_envelope():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": "281", "map_version": "260608002"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json(
        "/classes/com.korail.mobile.product.ReservationList",
        {"txtSelPage": "1", "txtCntPerPage": "20"},
        include_common=True,
        require_envelope=False,
    )

    assert response.h_msg_cd is None
    assert response.raw["map_version"] == "260608002"


def test_parse_base_response_raises_app_error_for_fail():
    try:
        parse_base_response(
            {"h_msg_cd": "WRG000000", "h_msg_txt": "조회 결과 없음", "strResult": "FAIL"}
        )
    except KorailAppError as exc:
        assert exc.code == "WRG000000"
        assert "조회 결과 없음" in str(exc)
    else:
        raise AssertionError("KorailAppError was not raised")


def test_wrc000288_is_application_failure_even_when_str_result_is_succ():
    with pytest.raises(KorailAppError) as exc_info:
        parse_base_response(
            {
                "h_msg_cd": "WRC000288",
                "h_msg_txt": "request rejected",
                "strResult": "SUCC",
            }
        )
    assert exc_info.value.code == "WRC000288"


def test_parse_base_response_requires_dict():
    try:
        parse_base_response(["not", "a", "dict"])
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


def test_parse_base_response_allows_omitted_common_out_fields():
    response = parse_base_response({"strResult": "SUCC"})
    assert response.h_msg_cd is None
    assert response.h_msg_txt is None


def test_post_form_raises_protocol_error_for_non_json_response():
    # The request must actually go out, or this passes on whatever else raises
    # KorailProtocolError first -- a field contract, an origin check -- and the
    # non-JSON branch could be deleted without a failure here.
    answered = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal answered
        answered = True
        return httpx.Response(200, text="<html>not json</html>")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError, match="valid JSON"):
        client.post_form("/classes/com.korail.mobile.common.code.do", COMMON_CODE_FORM)
    assert answered


def test_get_json_raises_protocol_error_for_non_json_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    try:
        client.get_json(
            "/classes/com.korail.mobile.product.ReservationList",
            {"txtSelPage": "1", "txtCntPerPage": "20"},
            include_common=True,
        )
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


@pytest.mark.parametrize("blocked_domain", sorted(EXCLUDED_API_DOMAINS))
def test_http_client_blocks_excluded_domains_before_post(blocked_domain: str):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(
            200, json=_IRG_OK
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.post_form(f"/classes/com.korail.mobile.{blocked_domain}.Example")

    assert called is False


@pytest.mark.parametrize("blocked_domain", sorted(EXCLUDED_API_DOMAINS))
def test_http_client_blocks_excluded_domains_before_get(blocked_domain: str):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(
            200, json=_IRG_OK
        )

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.get_json(f"/classes/com.korail.mobile.{blocked_domain}.Example")

    assert called is False


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/file/CACHE/MobileService.cache"),
        ("POST", "/file/CACHE/prdMobilePlusMain.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("POST", "/classes/com.korail.mobile.login.Logout"),
        ("POST", "/classes/com.korail.mobile.common.stationinfo"),
        ("POST", "/classes/com.korail.mobile.common.stationdata"),
        ("POST", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial"),
        (
            "POST",
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
        ),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketNewList.do"),
        ("POST", "/ebizcross/getUUID.do"),
        ("POST", "/classes/com.korail.mobile.copt.gdMenuLt.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do"),
    ],
)
def test_read_only_route_registry_accepts_current_public_requests(method, path):
    assert_read_only_route(method, path)


def test_logout_route_is_post_only_and_carries_timestamp_form():
    logout_path = "/classes/com.korail.mobile.login.Logout"
    assert ("POST", logout_path) in KORAIL_READ_ONLY_ROUTES
    assert ("GET", logout_path) not in KORAIL_READ_ONLY_ROUTES
    assert KORAIL_EXACT_REQUEST_FIELDS[logout_path] == frozenset(
        {"Device", "Version", "Key", "timeStamp"}
    )
    assert_read_only_route("POST", logout_path)
    assert_read_only_request_fields(
        logout_path, {"Device": "AD", "Version": "v", "Key": "k", "timeStamp": 1}
    )
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("GET", logout_path)
    with pytest.raises(KorailProtocolError, match="request fields"):
        assert_read_only_request_fields(logout_path, {"Device": "AD"})


# --- the six read routes that had no field contract ----------------------------
# login.Login, common.code.do, seatMovie.ScheduleView, qry.chtnStn.do,
# research.actualTrainSchedule.do and EbizMaasStationList.do went out with
# whatever fields a caller put in. Each now has the exact set its builder
# produces; these pin both the shapes that pass and the ones that must not.

LOGIN = "/classes/com.korail.mobile.login.Login"
COMMON3 = {"Device": "AD", "Version": "250601003", "Key": "korail1234567890"}
CREDENTIAL_LOGIN = {**COMMON3, **LOGIN_FORM}
SOCIAL_LOGIN = {**COMMON3, "txtInputFlg": "8", "custId": "SYNTHETIC", "checkValidPw": "Y"}


@pytest.mark.parametrize(
    "form",
    [
        CREDENTIAL_LOGIN,
        {**CREDENTIAL_LOGIN, "custId": "C", "etrPath": "E", "idx": "1"},
        SOCIAL_LOGIN,
    ],
    ids=["credential", "credential-with-optionals", "social"],
)
def test_login_accepts_exactly_the_two_shapes_the_session_builds(form):
    assert_read_only_request_fields(LOGIN, form)


@pytest.mark.parametrize(
    "form",
    [
        {**COMMON3, "txtInputFlg": "2", "checkValidPw": "Y"},
        {**COMMON3, "txtMemberNo": "M", "txtInputFlg": "2", "checkValidPw": "Y"},
        {**CREDENTIAL_LOGIN, "txtUnknown": "x"},
        {**SOCIAL_LOGIN, "txtPwd": "P"},
    ],
    ids=["no-credential-or-custId", "member-without-password", "unknown-name", "mixed-shapes"],
)
def test_login_refuses_anything_outside_those_shapes(form):
    # Each carries every name the two shapes share, so only the shape rule can
    # refuse it. A loose contract -- the shared names required, the rest
    # optional -- would pass all but the unknown name.
    with pytest.raises(KorailProtocolError, match="read-only contract"):
        assert_read_only_request_fields(LOGIN, form)


COMMON_CODE = "/classes/com.korail.mobile.common.code.do"


def test_common_code_accepts_its_builder_form_with_a_code_list():
    from korail_mobile_api.payloads import build_common_code_form

    assert_read_only_request_fields(
        COMMON_CODE,
        build_common_code_form(KorailConfig(), ["app.login.cphd", "app.menu.biz"]),
    )
    assert_read_only_request_fields(
        COMMON_CODE,
        build_common_code_form(
            KorailConfig(), "x", depart_date="20990101", arrival_date="20990102",
            holiday_yn="Y",
        ),
    )


@pytest.mark.parametrize(
    ("route", "form"),
    [
        (COMMON_CODE, {**COMMON3, **COMMON_CODE_FORM, "deviceWidth": ["1080"]}),
        (COMMON_CODE, {**COMMON3, **COMMON_CODE_FORM, "code": []}),
        (COMMON_CODE, {**COMMON3, **COMMON_CODE_FORM, "code": ["a", 1]}),
        (
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {**COMMON3, "dptRsStnCd": ["0001"], "arvRsStnCd": "0020"},
        ),
    ],
    ids=["list-in-another-field", "empty-code-list", "non-string-code", "list-on-another-route"],
)
def test_the_code_list_exception_is_that_field_on_that_route_only(route, form):
    with pytest.raises(KorailProtocolError):
        assert_read_only_request_fields(route, form)


@pytest.mark.parametrize(
    ("route", "form"),
    [
        (COMMON_CODE, {**COMMON3, "code": ["x"], "deviceWidth": 1, "deviceHeight": 2}),
        (COMMON_CODE, {**COMMON3, **COMMON_CODE_FORM, "extra": "x"}),
        (
            "/classes/com.korail.mobile.qry.chtnStn.do",
            {**COMMON3, "dptRsStnCd": "0001", "arvRsStnCd": "0020", "extra": "x"},
        ),
        (
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
            {
                "Device": "AD", "Version": "250601003", "runDt": "20990101",
                "trnNo": "00101", "Key": "k",
            },
        ),
        ("/ebizmaas/EbizMaasStationList.do", {"addSrvDvCd": "M10", "Device": "AD"}),
    ],
    ids=["common-code-missing-OSVersion", "common-code-extra", "chtnStn-extra",
         "schedule-with-Key", "maas-station-with-common"],
)
def test_the_newly_contracted_routes_refuse_extra_or_missing_fields(route, form):
    with pytest.raises(KorailProtocolError, match="read-only contract"):
        assert_read_only_request_fields(route, form)


SCHEDULE_VIEW = "/classes/com.korail.mobile.seatMovie.ScheduleView"


def _schedule_view_form(**query_kwargs):
    from korail_mobile_api import TrainSearchQuery
    from korail_mobile_api.payloads import build_train_search_form

    transfer = bool(query_kwargs)
    return build_train_search_form(
        KorailConfig(),
        TrainSearchQuery("서울", "부산", "20990101", **query_kwargs),
        departure_name="서울",
        arrival_name="부산",
        sid="SYNTHETIC_SID",
        member_card_no="SYNTHETIC_CARD",
        transfer=transfer,
    )


def test_schedule_view_accepts_its_builder_forms_direct_and_filtered():
    assert_read_only_request_fields(SCHEDULE_VIEW, _schedule_view_form())
    assert_read_only_request_fields(
        SCHEDULE_VIEW,
        _schedule_view_form(
            connection_station_codes=("0010", "0015"),
            connection_train_group_code="100",
        ),
    )


def test_schedule_view_refuses_a_key_and_misnumbered_connections():
    form = _schedule_view_form()
    with pytest.raises(KorailProtocolError, match="read-only contract"):
        assert_read_only_request_fields(SCHEDULE_VIEW, {**form, "Key": "k"})
    filtered = _schedule_view_form(connection_station_codes=("0010", "0015"))
    with pytest.raises(KorailProtocolError, match="numbered"):
        assert_read_only_request_fields(SCHEDULE_VIEW, {**filtered, "chtnCnt": "3"})


# --- ordered pairs --------------------------------------------------------------
# Pinned before this check was shared with assert_netfunnel_request. The read
# side checks the NAME here and leaves the value to the scalar check after the
# contract, which allows an int -- the NetFunnel side does not.

DELIVERY_HISTORY = "/classes/com.korail.mobile.tk.rcntDlvHst.do"
DELIVERY_HISTORY_HEAD = (("Device", "AD"), ("Version", "250601003"), ("Key", "k"))


@pytest.mark.parametrize(
    "last_pair",
    [
        ["custMgNo", "C"],
        ("custMgNo",),
        ("custMgNo", "C", "x"),
        (1, "C"),
    ],
    ids=["list", "one-item", "three-items", "int-name"],
)
def test_ordered_request_fields_must_be_name_value_tuples(last_pair):
    with pytest.raises(KorailProtocolError, match="must be scalar name/value pairs"):
        assert_read_only_request_fields(
            DELIVERY_HISTORY, (*DELIVERY_HISTORY_HEAD, last_pair)
        )


def test_an_ordered_pair_may_carry_an_int_value():
    assert_read_only_request_fields(
        DELIVERY_HISTORY, (*DELIVERY_HISTORY_HEAD, ("custMgNo", 1))
    )
    with pytest.raises(KorailProtocolError, match="scalar strings or integers"):
        assert_read_only_request_fields(
            DELIVERY_HISTORY, (*DELIVERY_HISTORY_HEAD, ("custMgNo", 1.5))
        )


# --- the read tail, pinned for all three senders --------------------------------
# post_form, post_query and get_json each finish the same way: transport
# failure, HTTP status, JSON decode, then the envelope. Pinned before that tail
# was shared, messages included.

_READ_SENDERS = {
    "post_form": (
        "POST",
        "/classes/com.korail.mobile.common.code.do",
        lambda client, path, **kw: client.post_form(path, COMMON_CODE_FORM, **kw),
    ),
    "post_query": (
        "POST",
        "/classes/com.korail.mobile.passCard.DelayDiscountView",
        lambda client, path, **kw: client.post_query(
            path, {"h_page_no": "20991231"}, **kw
        ),
    ),
    "get_json": (
        "GET",
        "/classes/com.korail.mobile.push.cmtrKnd.do",
        lambda client, path, **kw: client.get_json(
            path, {"cmtrKndCd": "1"}, include_common=True, **kw
        ),
    ),
}


def _read_through(sender, answer, **kw):
    method, path, call = _READ_SENDERS[sender]
    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True), transport=httpx.MockTransport(answer)
    )
    return method, path, lambda: call(client, path, **kw)


@pytest.mark.parametrize("sender", sorted(_READ_SENDERS))
def test_a_read_that_cannot_be_sent_names_its_method_and_path(sender):
    def answer(request):
        raise httpx.ConnectError("synthetic", request=request)

    method, path, send = _read_through(sender, answer)
    with pytest.raises(KorailTransportError) as raised:
        send()
    assert str(raised.value) == f"KORAIL transport failed for {method} {path}"


@pytest.mark.parametrize("sender", sorted(_READ_SENDERS))
@pytest.mark.parametrize("require_envelope", [True, False])
def test_a_read_answered_with_something_other_than_json_is_refused(
    sender, require_envelope
):
    _, _, send = _read_through(
        sender,
        lambda _: httpx.Response(200, text="<html>"),
        require_envelope=require_envelope,
    )
    with pytest.raises(KorailProtocolError, match=r"^KORAIL response body was not valid JSON$"):
        send()


@pytest.mark.parametrize("sender", sorted(_READ_SENDERS))
def test_a_relaxed_read_takes_any_object_and_parses_a_full_envelope(sender):
    def run(body, **kw):
        _, _, send = _read_through(
            sender, lambda _: httpx.Response(200, json=body), require_envelope=False, **kw
        )
        return send()

    # Not an object: refused even when the envelope is optional.
    with pytest.raises(KorailProtocolError, match=r"^KORAIL response must be a JSON object$"):
        run([{"h_msg_cd": "S000"}])
    # Some envelope keys but not all three: kept as it came, not judged.
    partial = {"strResult": "FAIL", "h_msg_cd": "ERR"}
    kept = run(partial)
    assert (kept.raw, kept.str_result, kept.h_msg_cd) == (partial, None, None)
    # All three: judged like any enveloped answer.
    full = {"h_msg_cd": "ERR", "h_msg_txt": "no", "strResult": "FAIL"}
    with pytest.raises(KorailAppError):
        run(full)
    assert run(full, raise_on_fail=False).str_result == "FAIL"


@pytest.mark.parametrize("sender", sorted(_READ_SENDERS))
def test_an_enveloped_read_without_its_result_is_a_failure(sender):
    # 7.0.6 CommonOut fills a missing strResult with its FAIL constant.
    _, _, send = _read_through(
        sender, lambda _: httpx.Response(200, json={"h_msg_cd": "S000", "h_msg_txt": "ok"})
    )
    with pytest.raises(KorailAppError, match="S000"):
        send()


@pytest.mark.parametrize(
    ("include_common", "data"), [(True, None), (False, {"x": "1"})]
)
def test_an_empty_post_with_fields_is_refused_before_sending(include_common, data):
    # Which refusal names it first (the empty-POST rule or the field contract)
    # is not the point; that nothing goes out is.
    sent = []
    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(lambda request: sent.append(request)),
    )
    with pytest.raises(KorailProtocolError):
        client.post_form(
            "/classes/com.korail.mobile.common.stationinfo",
            data,
            include_common=include_common,
            form_encoded=False,
        )
    assert sent == []


# --- read form key order ---------------------------------------------------------
# The form tests elsewhere compare dicts, which are equal in any order, so none
# of them sees a field that moved. These pin each read builder's order as the
# app's @Field declaration order sends it.

def _order_train(**extra):
    from korail_mobile_api.models import TrainSummary

    return TrainSummary(
        train_no="123", train_group_code="100", departure_station_code="0001",
        arrival_station_code="0020", departure_date="20260714",
        departure_time="060000", run_date="20260714", train_class_code="00",
        departure_run_order="000001", arrival_run_order="000010", **extra,
    )


_SEAT_CAR_ORDER = [
    "Device", "Version", "Key", "Sid", "txtMenuId", "txtPsrmClCd", "txtRunDt",
    "txtDptDt", "txtDptTm", "txtTrnClsfCd", "txtTrnNo", "txtDptRsStnCd",
    "txtArvRsStnCd", "txtDptStnRunOrdr", "txtArvStnRunOrdr", "txtTrnGpCd",
    "txtTotPsgCnt",
]
_SEAT_INVENTORY_ORDER = [
    "Device", "Version", "Key", "trnClsfCd", "trnGpCd", "runDt", "trnNo",
    "srcarNo", "psrmClCd", "dptRsStnCd", "arvRsStnCd", "seatAttCd",
    "dptStnRunOrdr", "arvStnRunOrdr", "totPsgCnt", "gdNo", "isArrow", "Sid",
    "ctlDvCd",
]
_SEARCH_ORDER = [
    "Device", "Version", "Sid", "txtMenuId", "radJobId", "selGoTrain",
    "txtTrnGpCd", "txtGoStart", "txtGoEnd", "txtGoAbrdDt", "txtGoHour",
    "txtPsgFlg_1", "txtPsgFlg_2", "txtPsgFlg_3", "txtPsgFlg_4", "txtPsgFlg_5",
    "txtSeatAttCd_2", "txtSeatAttCd_3", "txtSeatAttCd_4", "ebizCrossCheck",
    "srtCheckYn", "rtYn", "adjStnScdlOfrFlg", "mbCrdNo", "qryDvCd", "qryStNo",
    "qryStTrnNo", "qryStTrnNo2", "pgPrCnt",
]


def test_read_forms_keep_their_key_order():
    from korail_mobile_api import TrainSearchQuery
    from korail_mobile_api import payloads as P
    from korail_mobile_api import read_payloads as R

    config = KorailConfig()
    seat_train = _order_train(seat_attribute_code="015", goods_no="G1")
    cases = {
        "seat car": (
            P.build_seat_car_form(config, seat_train, passenger_count=1, sid="S"),
            [*_SEAT_CAR_ORDER, "txtSeatAttCd", "txtGdNo"],
        ),
        "seat car, no attribute or goods": (
            P.build_seat_car_form(config, _order_train(), passenger_count=1, sid="S"),
            _SEAT_CAR_ORDER,
        ),
        "seat inventory": (
            P.build_seat_inventory_form(config, seat_train, 3, passenger_count=1, sid="S"),
            _SEAT_INVENTORY_ORDER,
        ),
        "seat inventory, no attribute or goods": (
            P.build_seat_inventory_form(config, _order_train(), 3, passenger_count=1, sid="S"),
            [key for key in _SEAT_INVENTORY_ORDER if key not in {"seatAttCd", "gdNo"}],
        ),
        "search": (
            P.build_train_search_form(
                config, TrainSearchQuery("0001", "0020", "20990101"),
                departure_name="a", arrival_name="b", sid="S", member_card_no="M",
            ),
            _SEARCH_ORDER,
        ),
        "search, filtered transfer": (
            P.build_train_search_form(
                config,
                TrainSearchQuery(
                    "0001", "0020", "20990101",
                    connection_station_codes=("0010",),
                    connection_train_group_code="100",
                ),
                departure_name="a", arrival_name="b", sid="S", transfer=True,
            ),
            [key for key in _SEARCH_ORDER if key != "mbCrdNo"]
            + ["chtnCnt", "chtnRsStnCd1", "trnGpCnt", "trnGpCd1"],
        ),
        "train schedule": (
            P.build_train_schedule_form(config, "20990101", "101"),
            ["Device", "Version", "runDt", "trnNo"],
        ),
        "common code": (
            P.build_common_code_form(
                config, "x", depart_date="1", arrival_date="2", holiday_yn="Y"
            ),
            ["Device", "Version", "Key", "code", "deviceWidth", "deviceHeight",
             "departDate", "arrivalDate", "holidayYn", "OSVersion"],
        ),
        "maas menu": (P.build_maas_menu_form(config), ["Device", "Version", "timeStamp"]),
        "trip menu": (R.build_trip_menu_form(config), ["Device", "Version", "timeStamp"]),
        "maas service detail": (
            R.build_maas_service_detail_form(
                config, R.MaasServiceDetailQuery("20990101", "20990102")
            ),
            ["Device", "Version", "qryDtFrom", "qryDtTo"],
        ),
    }
    for name, (form, expected) in cases.items():
        assert list(form) == expected, name


# --- the mutation tail, pinned for both senders -----------------------------------
# post_mutation_form and get_mutation_query end the same way after sending:
# status, JSON, and an envelope that is never relaxed. Pinned before that tail
# was shared. Nothing here leaves the mock transport. No mutation route is a
# GET in 7.0.6, so the GET sender gets one for the test's duration, as
# test_safety does.

_CART = "/classes/com.korail.mobile.cart.addCartList"
_EXTENSION = "/classes/com.korail.mobile.reservation.dcntCrdExtn.do"


def _mutate_through(sender, answer, monkeypatch, **kw):
    from korail_mobile_api import safety
    from korail_mobile_api.consent import MutationConsent

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(answer))
    if sender == "post_mutation_form":
        return "POST", _CART, lambda: client.post_mutation_form(
            _CART,
            {**client.common_fields(), "hidPnrNo": "SYNTHETIC_PNR"},
            consent=MutationConsent(allow_cart=True, dry_run=False),
            category="cart",
            **kw,
        )
    monkeypatch.setattr(
        safety,
        "KORAIL_MUTATION_ROUTES",
        safety.KORAIL_MUTATION_ROUTES | {("GET", _EXTENSION)},
    )
    return "GET", _EXTENSION, lambda: client.get_mutation_query(
        _EXTENSION,
        {**client.common_fields(), "txtCrdNo": "SYNTHETIC_CARD"},
        consent=MutationConsent(allow_discount_card=True, dry_run=False),
        category="discount_card",
        **kw,
    )


_MUTATION_SENDERS = ["get_mutation_query", "post_mutation_form"]


@pytest.mark.parametrize("sender", _MUTATION_SENDERS)
def test_a_mutation_that_cannot_be_sent_names_its_method_and_path(sender, monkeypatch):
    def answer(request):
        raise httpx.ConnectError("synthetic", request=request)

    method, path, send = _mutate_through(sender, answer, monkeypatch)
    with pytest.raises(KorailTransportError) as raised:
        send()
    assert str(raised.value) == f"KORAIL transport failed for {method} {path}"


@pytest.mark.parametrize("sender", _MUTATION_SENDERS)
def test_a_mutation_answer_is_checked_like_an_enveloped_read(sender, monkeypatch):
    def run(response, **kw):
        _, _, send = _mutate_through(sender, lambda _: response, monkeypatch, **kw)
        return send()

    with pytest.raises(KorailApiError, match="HTTP 500"):
        run(httpx.Response(500, text="down"))
    with pytest.raises(KorailProtocolError, match=r"^KORAIL response body was not valid JSON$"):
        run(httpx.Response(200, text="<html>"))
    with pytest.raises(KorailProtocolError, match=r"^KORAIL response must be a JSON object$"):
        run(httpx.Response(200, json=[{"strResult": "SUCC"}]))
    # Never relaxed: a missing strResult is a failure, as it is for CommonOut.
    with pytest.raises(KorailAppError, match="S000"):
        run(httpx.Response(200, json={"h_msg_cd": "S000", "h_msg_txt": "ok"}))
    fail = {"h_msg_cd": "ERR", "h_msg_txt": "no", "strResult": "FAIL"}
    with pytest.raises(KorailAppError, match="ERR"):
        run(httpx.Response(200, json=fail))
    assert run(httpx.Response(200, json=fail), raise_on_fail=False).str_result == "FAIL"
    with pytest.raises(KorailSessionExpiredError):
        run(
            httpx.Response(200, json={"h_msg_cd": "P058", "h_msg_txt": "x", "strResult": "FAIL"}),
            raise_on_fail=False,
        )
    ok = run(httpx.Response(200, json={"h_msg_cd": "S000", "h_msg_txt": "ok", "strResult": "SUCC"}))
    assert ok.str_result == "SUCC"


def test_exact_form_field_mapping_remains_a_compatibility_alias():
    assert KORAIL_EXACT_FORM_FIELDS is KORAIL_EXACT_REQUEST_FIELDS


def test_exact_unordered_cart_contract_keeps_mapping_transport_compatible():
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "SYNTHETIC.OK",
                "h_msg_txt": "synthetic",
                "strResult": "SUCC",
            },
        )

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    client.post_form(
        "/classes/com.korail.mobile.cart.showCartList",
        {"pnrNo": "", "addSrvReqNo": ""},
    )
    assert called is True


def test_registered_variant_routes_allow_only_their_ordered_sequences():
    registered = {
        "/classes/com.korail.mobile.research.cmtrInfo.do": (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("jobDvCd", "b"),
            ("cmtrKndCd", "C"),
            ("psgCnt", "1"),
            ("cmtrUtlAgeCd", "A"),
        ),
        "/classes/com.korail.mobile.trn.prcFare.do": (
            ("Device", "AD"),
            ("Version", "1"),
            ("Key", "K"),
            ("txtMenuId", "11"),
            ("chtnDvCd", "1"),
            ("trnCnt", "1"),
            ("dptRsStnCd", "D"),
            ("arvRsStnCd", "A"),
            ("runDt", "20990101"),
            ("trnNo", "00001"),
            ("gdNo", "G"),
            ("rqSeatAttCd", "S"),
            ("trnGpCd", "T"),
            ("stlbTrnClsfCd", "C"),
        ),
    }
    for path, fields in registered.items():
        assert_read_only_request_fields(path, fields)


def test_maas_ticket_menu_accepts_pnr_and_repeated_ticket_return_numbers():
    captured = {}
    path = "/classes/com.korail.mobile.copt.gdMenuLt.do"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["request"] = request
        return httpx.Response(
            200, json={"h_msg_cd": "S000", "h_msg_txt": "OK", "strResult": "SUCC"}
        )

    client = KorailHttpClient(
        KorailConfig(), transport=httpx.MockTransport(handler)
    )
    client.post_form(
        path,
        (
            ("Device", "AD"),
            ("Version", "250601003"),
            ("Key", "synthetic-key"),
            ("pnrNo", "synthetic-pnr"),
            ("tkRetNo", "synthetic-one"),
            ("tkRetNo", "synthetic-two"),
            ("addSrvReqNo", "synthetic-request"),
        ),
        include_common=False,
    )
    fields = parse_qs(captured["request"].content.decode())
    assert fields["pnrNo"] == ["synthetic-pnr"]
    assert fields["tkRetNo"] == ["synthetic-one", "synthetic-two"]


def test_maas_ticket_menu_rejects_pnr_without_ticket_return_number():
    path = "/classes/com.korail.mobile.copt.gdMenuLt.do"
    with pytest.raises(KorailProtocolError, match="request fields"):
        assert_read_only_request_fields(
            path,
            (
                ("Device", "AD"),
                ("Version", "1"),
                ("Key", "k"),
                ("pnrNo", "p"),
            ),
        )


def test_post_form_accepts_a_common_out_object_with_omitted_envelope_fields():
    calls = 0
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        captured.append(request)
        if calls == 1:
            return httpx.Response(200, json={"stns": {"stn": []}})
        return httpx.Response(200, json={"stns": {"stn": []}})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    relaxed = client.post_form(
        "/ebizmaas/EbizMaasStationList.do",
        {"addSrvDvCd": "M10"},
        include_common=False,
        require_envelope=False,
    )
    assert relaxed.raw == {"stns": {"stn": []}}
    assert captured[0].content == b"addSrvDvCd=M10"
    default = client.post_form(
        "/ebizmaas/EbizMaasStationList.do",
        {"addSrvDvCd": "M10"},
        include_common=False,
    )
    assert default.raw == relaxed.raw


def test_relaxed_post_still_raises_for_a_session_expiry_envelope():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "P058",
                "h_msg_txt": "logged out",
                "strResult": "FAIL",
            },
        )

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailSessionExpiredError):
        client.post_form(
            "/ebizmaas/EbizMaasStationList.do",
            {"addSrvDvCd": "M10"},
            include_common=False,
            require_envelope=False,
        )


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/ebizcross/getUUID.do"),
        ("GET", "/ebizmaas/EbizMaasStationList.do"),
        ("GET", "/ebizcross/%67etUUID.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do/extra"),
    ],
)
def test_uuid_maas_route_bypasses_are_rejected(method, path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route(method, path)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/ebizcross/getUUID.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do"),
    ],
)
def test_uuid_maas_routes_never_generate_dynapath(method, path):
    provider_called = False

    def provider(_context):
        nonlocal provider_called
        provider_called = True
        return "must-not-be-used"

    def handler(request: httpx.Request) -> httpx.Response:
        assert DYNAPATH_HEADER_NAME not in request.headers
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "API.I00000",
                "h_msg_txt": "Success",
                "strResult": "SUCC",
                "mutMrkVrfCd": "fixture-code",
            },
        )

    client = KorailHttpClient(
        KorailConfig(
            dynapath=DynapathConfig(enabled=True, token_provider=provider)
        ),
        transport=httpx.MockTransport(handler),
    )
    if path == "/ebizcross/getUUID.do":
        client.post_form(path, include_common=False, form_encoded=False)
    else:
        client.post_form(path, {"addSrvDvCd": "M10"}, include_common=False)
    assert provider_called is False


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/file/CACHE/prdMobilePlusMain.cache"),
        ("POST", "/file/CACHE/prdMobilePlusNotice.cache"),
        ("GET", "https://evil.example/file/CACHE/prdMobilePlusMain.cache"),
        ("GET", "/file/CACHE/%70rdMobilePlusMain.cache"),
        ("GET", "/file/CACHE/unknown.cache"),
        ("GET", "/file/CACHE/prdMobilePlusMain.cache.bak"),
        ("GET", "/file/CACHE/prdMobilePlusNotice.cache/extra"),
    ],
)
def test_cache_route_bypasses_are_rejected_before_transport(method, path):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "S000",
                "h_msg_txt": "",
                "strResult": "SUCC",
            },
        )

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailProtocolError):
        if method == "POST":
            client.post_form(path)
        else:
            client.get_json(path)
    assert called is False


def test_cache_routes_never_generate_a_dynapath_token():
    path = "/file/CACHE/prdMobilePlusMain.cache"
    provider_called = False

    def token_provider(_context):
        nonlocal provider_called
        provider_called = True
        return "token"

    def handler(request: httpx.Request) -> httpx.Response:
        assert DYNAPATH_HEADER_NAME not in request.headers
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "S000",
                "h_msg_txt": "",
                "strResult": "SUCC",
            },
        )

    client = KorailHttpClient(
        KorailConfig(
            dynapath=DynapathConfig(
                enabled=True,
                token_provider=token_provider,
            )
        ),
        transport=httpx.MockTransport(handler),
    )
    client.post_form(path, {"timeStamp": "1"}, include_common=False)
    assert provider_called is False
    assert path not in DYNAPATH_ALLOWLIST_PATHS


@pytest.mark.parametrize(
    "path",
    [
        "/classes/com.korail.mobile.login.mbSced.do",
        "/classes/com.korail.mobile.certification.TicketReservation",
        "https://evil.example/classes/com.korail.mobile.common.code.do",
    ],
)
def test_route_registry_rejects_mutation_and_absolute_paths_before_io(path):
    with pytest.raises(KorailProtocolError):
        assert_read_only_route("POST", path)


def test_p058_is_always_session_expired_even_when_failure_opt_out_is_requested():
    with pytest.raises(KorailSessionExpiredError):
        parse_base_response(
            {
                "h_msg_cd": "P058",
                "h_msg_txt": "logged out",
                "strResult": "FAIL",
            },
            raise_on_fail=False,
        )


def test_allowlisted_403_is_classified_as_dynapath_error(load_json_fixture):
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json=load_json_fixture("dynapath_403.json"),
            headers={"DynaPath-Result": "-1"},
        )

    # 서버가 보낸 403 을 분류하는 테스트이므로 요청이 실제로 나가야 한다.
    # 끈 설정이면 전송 전에 KorailDynaPathRequiredError 로 막혀 서버 응답을
    # 볼 기회 자체가 없다.
    client = KorailHttpClient(
        KorailConfig(enable_dynapath=True),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailDynaPathError, match="macro protection"):
        client.post_form("/classes/com.korail.mobile.login.Login", LOGIN_FORM)


@pytest.mark.parametrize(
    "base_url",
    [
        "https://evil.example",
        "https://smart.letskorail.com.evil.example",
        "http://smart.letskorail.com",
        "https://smart.letskorail.com:0",
        "https://smart.letskorail.com:444",
        "https://user@smart.letskorail.com",
        "https://smart.letskorail.com/api",
    ],
)
def test_untrusted_origin_is_rejected_before_dynapath_or_io(base_url):
    token_called = False
    handler_called = False

    def token_provider(_context):
        nonlocal token_called
        token_called = True
        return "token"

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal handler_called
        handler_called = True
        return httpx.Response(
            200,
            json={
                "h_msg_cd": "IRG000000",
                "h_msg_txt": "OK",
                "strResult": "SUCC",
            },
        )

    config = KorailConfig(
        base_url=base_url,
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
        ),
    )
    with pytest.raises(KorailProtocolError, match="origin"):
        client = KorailHttpClient(
            config,
            transport=httpx.MockTransport(handler),
        )
        client.post_form("/classes/com.korail.mobile.login.Login")
    assert token_called is False
    assert handler_called is False


def test_origin_helper_rejects_explicit_port_zero():
    with pytest.raises(KorailProtocolError, match="origin"):
        assert_korail_origin("https://smart.letskorail.com:0")


@pytest.mark.parametrize(
    "base_url",
    [
        "https://smart.letskorail.com",
        "https://smart.letskorail.com:443",
        "https://smart.letskorail.com/",
    ],
)
def test_exact_https_korail_origin_is_accepted(base_url):
    client = KorailHttpClient(
        KorailConfig(base_url=base_url),
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200,
                json={
                    "h_msg_cd": "IRG000000",
                    "h_msg_txt": "OK",
                    "strResult": "SUCC",
                },
            )
        ),
    )
    response = client.post_form(
        "/classes/com.korail.mobile.common.code.do", COMMON_CODE_FORM
    )
    assert response.str_result == "SUCC"
