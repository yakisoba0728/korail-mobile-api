import httpx
import korail_mobile_api as api
import pytest

from korail_mobile_api import (
    DYNAPATH_ALLOWLIST_PATHS,
    DYNAPATH_HEADER_NAME,
    DynapathTokenGenerator,
    KORAIL_API_VERSION,
    KORAIL_APP_KEY,
    KORAIL_COMMON_CODE_BOOTSTRAP_CODES,
    KORAIL_DEFAULT_ANDROID_SDK_INT,
    KORAIL_DEFAULT_DEVICE_NAME,
    KORAIL_DEVICE_ANDROID,
    KORAIL_DYNAPATH_AS_VALUE,
    KORAIL_DYNAPATH_SDK_VERSION,
    KorailConfig,
)
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.http import KorailHttpClient, parse_base_response
from korail_mobile_api.safety import (
    EXCLUDED_API_DOMAINS,
    KORAIL_EXACT_FORM_FIELDS,
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_korail_origin,
    assert_read_only_route,
)
from conftest import load_json_fixture


def test_post_form_adds_common_fields_and_form_encoding():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers["content-type"]
        captured["connection"] = request.headers["connection"]
        captured["body"] = request.content.decode()
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.post_form(
        "/classes/com.korail.mobile.common.code.do",
        {"custom": "value"},
    )

    assert captured["url"] == (
        "https://smart.letskorail.com/classes/com.korail.mobile.common.code.do"
    )
    assert captured["content_type"] == "application/x-www-form-urlencoded; charset=UTF-8"
    assert captured["connection"] == "close"
    assert "Device=AD" in captured["body"]
    assert "Version=250601003" in captured["body"]
    assert "Key=korail1234567890" in captured["body"]
    assert "custom=value" in captured["body"]
    assert response.h_msg_cd == "IRG000000"


def test_korail_runtime_constants_are_importable():
    assert KORAIL_DEVICE_ANDROID == "AD"
    assert KORAIL_API_VERSION == "250601003"
    assert KORAIL_APP_KEY == "korail1234567890"
    assert KORAIL_DEFAULT_ANDROID_SDK_INT == 35
    assert "app.login.cphd" in KORAIL_COMMON_CODE_BOOTSTRAP_CODES
    assert KORAIL_DYNAPATH_AS_VALUE == "[38ff229cb34c7dda8e28220a2d750cce]"
    assert KORAIL_DYNAPATH_SDK_VERSION == "v1"
    assert KORAIL_DEFAULT_DEVICE_NAME
    assert DYNAPATH_HEADER_NAME == "x-dynapath-m-token"
    assert DynapathTokenGenerator
    assert not hasattr(api, "KorailProbeDynapathTokenProvider")
    assert not hasattr(api, "generate_korail_probe_dynapath_token")
    assert "/classes/com.korail.mobile.login.Login" in DYNAPATH_ALLOWLIST_PATHS


def test_post_form_adds_dynapath_header_for_allowlisted_path():
    captured = {}
    contexts = []

    def token_provider(context):
        contexts.append(context)
        return "dynapath-token"

    def handler(request: httpx.Request) -> httpx.Response:
        captured["token"] = request.headers.get(DYNAPATH_HEADER_NAME)
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    response = client.post_form("/classes/com.korail.mobile.login.Login")

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
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    config = KorailConfig(dynapath=DynapathConfig(enabled=True, token_provider=token_provider))
    client = KorailHttpClient(config, transport=httpx.MockTransport(handler))
    client.post_form("/classes/com.korail.mobile.common.code.do")

    assert called is False


def test_get_json_adds_dynapath_header_for_allowlisted_path_by_default():
    captured = {}
    contexts = []
    path = "/classes/com.korail.mobile.common.stationinfo"

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

    response = client.get_json(path)

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
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json(
        "/classes/com.korail.mobile.common.stationinfo",
        {"custom": "value"},
    )

    assert captured["url"] == (
        "https://smart.letskorail.com/classes/com.korail.mobile.common.stationinfo"
        "?custom=value"
    )
    assert captured["query"] == "custom=value"
    assert response.str_result == "SUCC"


def test_get_json_can_return_raw_object_without_korail_envelope():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"count": "281", "map_version": "260608002"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))
    response = client.get_json(
        "/classes/com.korail.mobile.common.stationinfo",
        require_envelope=False,
    )

    assert response.h_msg_cd is None
    assert response.raw["map_version"] == "260608002"


def test_parse_base_response_raises_app_error_for_fail():
    try:
        parse_base_response({"h_msg_cd": "WRG000000", "h_msg_txt": "조회 결과 없음", "strResult": "FAIL"})
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


def test_parse_base_response_requires_korail_envelope_fields():
    try:
        parse_base_response(load_json_fixture("dynapath_403.json"))
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("h_msg_cd", {"unexpected": "object"}),
        ("h_msg_txt", ["unexpected", "list"]),
        ("strResult", ["unexpected", "list"]),
    ],
)
def test_parse_base_response_rejects_non_string_envelope_values(field, value):
    payload = {
        "h_msg_cd": "IRG000000",
        "h_msg_txt": "OK",
        "strResult": "SUCC",
    }
    payload[field] = value
    with pytest.raises(KorailProtocolError, match=field):
        parse_base_response(payload)


def test_post_form_raises_protocol_error_for_non_json_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html>not json</html>")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    try:
        client.post_form("/classes/com.korail.mobile.common.code.do")
    except KorailProtocolError:
        pass
    else:
        raise AssertionError("KorailProtocolError was not raised")


def test_get_json_raises_protocol_error_for_non_json_response():
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain text")

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    try:
        client.get_json("/classes/com.korail.mobile.common.stationinfo")
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
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

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
        return httpx.Response(200, json={"h_msg_cd": "IRG000000", "h_msg_txt": "OK", "strResult": "SUCC"})

    client = KorailHttpClient(KorailConfig(), transport=httpx.MockTransport(handler))

    with pytest.raises(KorailProtocolError):
        client.get_json(f"/classes/com.korail.mobile.{blocked_domain}.Example")

    assert called is False


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/file/CACHE/MobileService.cache"),
        ("GET", "/file/CACHE/prdMobilePlusMain.cache"),
        ("GET", "/file/CACHE/prdMobilePlusNotice.cache"),
        ("POST", "/classes/com.korail.mobile.common.code.do"),
        ("POST", "/classes/com.korail.mobile.login.Login"),
        ("GET", "/classes/com.korail.mobile.common.stationinfo"),
        ("GET", "/classes/com.korail.mobile.common.stationdata"),
        ("GET", "/classes/com.korail.mobile.schedule.runDt"),
        ("POST", "/classes/com.korail.mobile.seatMovie.ScheduleView"),
        (
            "POST",
            "/classes/com.korail.mobile.research.actualTrainSchedule.do",
        ),
        ("POST", "/classes/com.korail.mobile.qry.chtnStn.do"),
        ("POST", "/classes/com.korail.mobile.myTicket.MyTicketList"),
        ("GET", "/ebizcross/getUUID.do"),
        ("POST", "/classes/com.korail.mobile.copt.gdMenuLt.do"),
        ("POST", "/ebizmaas/EbizMaasStationList.do"),
    ],
)
def test_read_only_route_registry_accepts_current_public_requests(method, path):
    assert_read_only_route(method, path)


def test_read_only_route_registry_has_exact_expanded_count():
    assert len(KORAIL_READ_ONLY_ROUTES) == 38


def test_exact_form_field_mapping_remains_a_compatibility_alias():
    assert KORAIL_EXACT_FORM_FIELDS is KORAIL_EXACT_REQUEST_FIELDS


@pytest.mark.parametrize(
    "data",
    [
        {"pnrNo": ""},
        {"pnrNo": "", "addSrvReqNo": "", "unexpected": "blocked"},
        {"pnrNo": "", "addSrvReqNo": ["blocked"]},
        {"pnrNo": "", "addSrvReqNo": True},
    ],
)
def test_exact_post_request_fields_and_scalar_values_fail_before_io(data):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailProtocolError, match="request (fields|values)"):
        client.post_form(
            "/classes/com.korail.mobile.cart.showCartList",
            data,
        )
    assert called is False


@pytest.mark.parametrize(
    "params",
    [
        {"txtSelPage": "1"},
        {
            "txtSelPage": "1",
            "txtCntPerPage": "20",
            "unexpected": "blocked",
        },
        {"txtSelPage": "1", "txtCntPerPage": ["20"]},
        {"txtSelPage": "1", "txtCntPerPage": False},
    ],
)
def test_exact_get_request_fields_and_scalar_values_fail_before_io(params):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailProtocolError, match="request (fields|values)"):
        client.get_json(
            "/classes/com.korail.mobile.product.ReservationList",
            params,
            include_common=True,
        )
    assert called is False


@pytest.mark.parametrize(
    "extra_field",
    ["Key", "pnrNo", "tkRetNo", "addSrvReqNo", "unexpected"],
)
def test_maas_menu_route_rejects_non_generic_form_fields_before_io(
    extra_field,
):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailProtocolError, match="request fields"):
        client.post_form(
            "/classes/com.korail.mobile.copt.gdMenuLt.do",
            {
                "Device": "AD",
                "Version": "250601003",
                extra_field: "blocked-value",
            },
            include_common=False,
        )

    assert called is False


@pytest.mark.parametrize(
    "form",
    [{}, {"Device": "AD"}, {"Version": "250601003"}],
)
def test_maas_menu_route_requires_exact_generic_form_fields(form):
    called = False

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200, json={})

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailProtocolError, match="request fields"):
        client.post_form(
            "/classes/com.korail.mobile.copt.gdMenuLt.do",
            form,
            include_common=False,
        )

    assert called is False


def test_post_form_can_accept_one_envelope_free_object_without_weakening_default():
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
    with pytest.raises(KorailProtocolError, match="envelope"):
        client.post_form(
            "/ebizmaas/EbizMaasStationList.do",
            {"addSrvDvCd": "M10"},
            include_common=False,
        )


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
        ("POST", "/ebizcross/getUUID.do"),
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
    if method == "GET":
        client.get_json(path)
    else:
        client.post_form(path, {"addSrvDvCd": "M10"}, include_common=False)
    assert provider_called is False


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/file/CACHE/prdMobilePlusMain.cache"),
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


@pytest.mark.parametrize(
    "path",
    [
        "/file/CACHE/prdMobilePlusMain.cache",
        "/file/CACHE/prdMobilePlusNotice.cache",
    ],
)
def test_cache_routes_never_generate_a_dynapath_token(path):
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
    client.get_json(path, {"timeStamp": "1"})
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

    client = KorailHttpClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(KorailDynaPathError, match="macro protection"):
        client.post_form("/classes/com.korail.mobile.login.Login")


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
        "/classes/com.korail.mobile.common.code.do"
    )
    assert response.str_result == "SUCC"
