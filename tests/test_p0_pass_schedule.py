from __future__ import annotations

import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass
from pathlib import Path
from typing import Any, get_type_hints
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api import read_models, read_parsers, read_payloads
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailAppError,
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import KorailSession
from korail_mobile_api.safety import (
    KORAIL_EXACT_REQUEST_FIELDS,
    KORAIL_READ_ONLY_ROUTES,
    assert_read_only_request_fields,
)


PASS_SCHEDULE_PATH = (
    "/classes/com.korail.mobile.pass.passScheduleInfoList"
)
PASS_SCHEDULE_FIELDS = {
    "Device",
    "Version",
    "Key",
    "selGoTrain",
    "selGoAbrdDt",
    "txtGoHour",
    "radChgTrnDvCd",
    "txtCmtrKndCd",
    "txtCmtrUtlTrmCd",
    "txtCmtrUtlAgeCd",
    "txtSelPage",
    "txtCntPerPage",
    "txtGoStart",
    "txtGoEnd",
    "txtWkndUseFlg",
}
CALLER_FIELDS = {
    "selGoTrain": "SYNTHETIC-TRAIN-SELECTION",
    "selGoAbrdDt": "20990102",
    "txtGoHour": "010203",
    "radChgTrnDvCd": "SYNTHETIC-TRANSFER-TYPE",
    "txtCmtrKndCd": "SYNTHETIC-PASS-KIND",
    "txtCmtrUtlTrmCd": "SYNTHETIC-PASS-PERIOD",
    "txtCmtrUtlAgeCd": "SYNTHETIC-PASS-AGE",
    "txtSelPage": "7",
    "txtCntPerPage": "",
    "txtGoStart": "synthetic-request-departure-secret",
    "txtGoEnd": "synthetic-request-arrival-secret",
    "txtWkndUseFlg": "N",
}


def _require(module: Any, name: str) -> Any:
    value = getattr(module, name, None)
    assert value is not None, f"missing R20 pass schedule symbol: {name}"
    return value


def _request(**overrides: Any) -> Any:
    values = {
        "selected_train_code": CALLER_FIELDS["selGoTrain"],
        "departure_date": CALLER_FIELDS["selGoAbrdDt"],
        "departure_time": CALLER_FIELDS["txtGoHour"],
        "transfer_type_code": CALLER_FIELDS["radChgTrnDvCd"],
        "pass_kind_code": CALLER_FIELDS["txtCmtrKndCd"],
        "pass_period_code": CALLER_FIELDS["txtCmtrUtlTrmCd"],
        "pass_age_code": CALLER_FIELDS["txtCmtrUtlAgeCd"],
        "page_no": CALLER_FIELDS["txtSelPage"],
        "page_size": CALLER_FIELDS["txtCntPerPage"],
        "departure_station_name": CALLER_FIELDS["txtGoStart"],
        "arrival_station_name": CALLER_FIELDS["txtGoEnd"],
        "weekend_use_flag": CALLER_FIELDS["txtWkndUseFlg"],
    }
    values.update(overrides)
    return _require(read_payloads, "PassScheduleRequest")(**values)


def _parser():
    return _require(read_parsers, "parse_pass_schedule_response")


def test_public_request_models_and_method_signature_are_exact():
    request_type = _require(read_payloads, "PassScheduleRequest")
    model_names = (
        "PassScheduleTrain",
        "PassScheduleInfo",
        "PassScheduleResponse",
    )
    for name in ("PassScheduleRequest", *model_names):
        assert name in korail_mobile_api.__all__
        source = read_payloads if name == "PassScheduleRequest" else read_models
        assert getattr(korail_mobile_api, name) is _require(source, name)

    method = _require(KorailClient, "get_pass_schedule")
    signature = inspect.signature(method)
    assert list(signature.parameters) == ["self", "request"]
    assert signature.parameters["request"].default is inspect.Parameter.empty
    assert get_type_hints(method) == {
        "request": request_type,
        "return": _require(read_models, "PassScheduleResponse"),
    }

    for java_or_mutation_name in (
        "getCommRsvInquiry",
        "commReservation",
        "commPayment",
        "get_pass_reservation",
        "get_pass_payment",
    ):
        assert not hasattr(KorailClient, java_or_mutation_name)


def test_request_is_closed_frozen_required_and_repr_safe():
    request_type = _require(read_payloads, "PassScheduleRequest")
    request = _request()
    assert is_dataclass(request)
    assert request.__dataclass_params__.frozen is True
    assert all(
        parameter.default is inspect.Parameter.empty
        for parameter in inspect.signature(request_type).parameters.values()
    )
    assert not hasattr(request, "extra_fields")
    with pytest.raises(FrozenInstanceError):
        request.page_no = "8"
    with pytest.raises(TypeError):
        _request(extra_fields={"must": "not pass"})

    rendered = repr(request)
    for secret in CALLER_FIELDS.values():
        if secret:
            assert secret not in rendered


def test_closed_builder_emits_only_the_exact_apk_caller_fields():
    builder = _require(read_payloads, "build_pass_schedule_form")
    form = builder(_request())
    assert form == CALLER_FIELDS
    assert set(form) == PASS_SCHEDULE_FIELDS - {"Device", "Version", "Key"}
    assert all(type(value) is str for value in form.values())
    with pytest.raises(TypeError, match="PassScheduleRequest"):
        builder(object())


def test_builder_rejects_subclasses_and_revalidates_without_virtual_dispatch():
    request_type = _require(read_payloads, "PassScheduleRequest")
    builder = _require(read_payloads, "build_pass_schedule_form")

    class ForgedPassScheduleRequest(request_type):
        def _validate(self) -> None:
            return None

    forged = ForgedPassScheduleRequest(
        **{
            item.name: getattr(_request(), item.name)
            for item in fields(request_type)
        }
    )
    with pytest.raises(TypeError, match="PassScheduleRequest"):
        builder(forged)

    mutated = _request()
    object.__setattr__(mutated, "page_no", "0")
    with pytest.raises(ValueError, match="page_no"):
        builder(mutated)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("selected_train_code", ""),
        ("departure_date", "２０９９０１０２"),
        ("departure_date", "2099-01-02"),
        ("departure_time", "0102A3"),
        ("transfer_type_code", ""),
        ("pass_kind_code", ""),
        ("pass_period_code", None),
        ("pass_age_code", " "),
        ("page_no", "0"),
        ("page_no", True),
        ("page_size", "0"),
        ("page_size", "１２"),
        ("page_size", None),
        ("departure_station_name", ""),
        ("arrival_station_name", " "),
        ("weekend_use_flag", "X"),
    ),
)
def test_request_rejects_malformed_or_ambiguous_values(
    field_name,
    bad_value,
):
    with pytest.raises(ValueError, match=field_name):
        _request(**{field_name: bad_value})


def test_safety_registers_one_exact_read_only_contract():
    assert ("POST", PASS_SCHEDULE_PATH) in KORAIL_READ_ONLY_ROUTES
    assert len(KORAIL_READ_ONLY_ROUTES) == 42
    assert KORAIL_EXACT_REQUEST_FIELDS[PASS_SCHEDULE_PATH] == (
        PASS_SCHEDULE_FIELDS
    )
    assert_read_only_request_fields(
        PASS_SCHEDULE_PATH,
        {name: "" for name in PASS_SCHEDULE_FIELDS},
    )

    missing = {name: "" for name in PASS_SCHEDULE_FIELDS - {"txtSelPage"}}
    extra = {name: "" for name in PASS_SCHEDULE_FIELDS}
    extra["hidPayAmount"] = "blocked"
    for values in (missing, extra):
        with pytest.raises(KorailProtocolError, match="exactly"):
            assert_read_only_request_fields(PASS_SCHEDULE_PATH, values)


def test_client_requires_session_before_validation_or_io():
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    client = KorailClient(transport=httpx.MockTransport(handler))
    with pytest.raises(KorailAuthError, match="authenticated session"):
        _require(client, "get_pass_schedule")(_request())
    assert calls == 0


def test_client_issues_one_exact_post_without_dynapath(
    load_json_fixture,
):
    requests: list[httpx.Request] = []
    token_calls = 0

    def token_provider(_):
        nonlocal token_calls
        token_calls += 1
        return "must-not-be-requested"

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=load_json_fixture("pass_schedule_success.json"),
        )

    config = KorailConfig(
        dynapath=DynapathConfig(
            enabled=True,
            token_provider=token_provider,
            allowlist_paths=frozenset({PASS_SCHEDULE_PATH}),
        )
    )
    client = KorailClient(
        config,
        transport=httpx.MockTransport(handler),
    )
    client.session.current = KorailSession(
        jsessionid="synthetic-cookie-secret",
        member_no="synthetic-member-secret",
    )

    response = client.get_pass_schedule(_request())

    assert type(response) is _require(read_models, "PassScheduleResponse")
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert request.url.path == PASS_SCHEDULE_PATH
    assert parse_qs(
        request.content.decode(),
        keep_blank_values=True,
    ) == {
        **{name: [value] for name, value in client.http.common_fields().items()},
        **{name: [value] for name, value in CALLER_FIELDS.items()},
    }
    assert token_calls == 0
    assert "x-dynapath-m-token" not in request.headers


def test_parser_maps_only_the_eight_static_train_dto_fields(
    load_json_fixture,
):
    raw = load_json_fixture("pass_schedule_success.json")
    response = _parser()(raw)
    response_type = _require(read_models, "PassScheduleResponse")
    info_type = _require(read_models, "PassScheduleInfo")
    train_type = _require(read_models, "PassScheduleTrain")

    assert type(response) is response_type
    assert response.raw is raw
    assert isinstance(response.schedules, tuple)
    assert len(response.schedules) == 1
    schedule = response.schedules[0]
    assert type(schedule) is info_type
    assert schedule.raw is raw["schedule_info"][0]
    assert isinstance(schedule.trains, tuple)
    train = schedule.trains[0]
    assert type(train) is train_type
    assert [item.name for item in fields(train_type)] == [
        "arrival_station_code",
        "arrival_station_name",
        "departure_station_code",
        "departure_station_name",
        "detour_code",
        "schedule_price",
        "train_group_code",
        "train_no",
        "raw",
    ]
    assert train.arrival_station_code == "SYNTHETIC-ARRIVAL-CODE"
    assert train.arrival_station_name == "synthetic-arrival-name-secret"
    assert train.departure_station_code == "SYNTHETIC-DEPARTURE-CODE"
    assert train.departure_station_name == (
        "synthetic-departure-name-secret"
    )
    assert train.detour_code == "SYNTHETIC-DETOUR-CODE"
    assert train.schedule_price == "SYNTHETIC-SCHEDULE-PRICE"
    assert train.train_group_code == "SYNTHETIC-TRAIN-GROUP-CODE"
    assert train.train_no == "SYNTHETIC-TRAIN-NO"
    assert train.raw is raw["schedule_info"][0]["train_list"][0]

    with pytest.raises(FrozenInstanceError):
        train.train_no = "changed"
    rendered = repr(response)
    for secret in (
        raw["h_msg_txt"],
        "SYNTHETIC-ARRIVAL-CODE",
        "synthetic-arrival-name-secret",
        "SYNTHETIC-SCHEDULE-PRICE",
        "SYNTHETIC-TRAIN-NO",
    ):
        assert secret not in rendered


@pytest.mark.parametrize(
    ("mutation", "match"),
    (
        (lambda raw: raw.pop("h_msg_cd"), "envelope"),
        (lambda raw: raw.__setitem__("strResult", None), "SUCC"),
        (lambda raw: raw.__setitem__("strResult", "SUCCESS"), "SUCC"),
        (lambda raw: raw.__setitem__("schedule_info", {}), "schedule_info"),
        (
            lambda raw: raw["schedule_info"][0].__setitem__(
                "train_list", {}
            ),
            "train_list",
        ),
        (
            lambda raw: raw["schedule_info"][0]["train_list"][0].__setitem__(
                "h_schd_prc", 1
            ),
            "h_schd_prc",
        ),
    ),
)
def test_parser_rejects_non_succ_and_malformed_shapes(
    load_json_fixture,
    mutation,
    match,
):
    raw = load_json_fixture("pass_schedule_success.json")
    mutation(raw)
    with pytest.raises(KorailProtocolError, match=match):
        _parser()(raw)


def test_parser_preserves_typed_failure_and_session_expiry_errors(
    load_json_fixture,
):
    raw = load_json_fixture("pass_schedule_success.json")
    raw.update(
        h_msg_cd="SYNTHETIC.FAIL",
        h_msg_txt="synthetic-failure-message-secret",
        strResult="FAIL",
    )
    with pytest.raises(KorailAppError) as app_error:
        _parser()(raw)
    assert app_error.value.raw is raw

    raw.update(h_msg_cd="P058")
    with pytest.raises(KorailSessionExpiredError) as expired:
        _parser()(raw)
    assert expired.value.raw is raw


def test_client_clears_session_on_p058(load_json_fixture):
    def handler(_: httpx.Request) -> httpx.Response:
        raw = load_json_fixture("pass_schedule_success.json")
        raw.update(h_msg_cd="P058", strResult="FAIL")
        return httpx.Response(200, json=raw)

    client = KorailClient(transport=httpx.MockTransport(handler))
    client.session.current = KorailSession(jsessionid="synthetic-secret")
    with pytest.raises(KorailSessionExpiredError):
        client.get_pass_schedule(_request())
    assert client.session.current is None


def test_documentation_keeps_unverified_session_and_mutation_boundary():
    root = Path(__file__).resolve().parents[1]
    document = (root / "docs/pass-schedule-read.md").read_text()
    assert PASS_SCHEDULE_PATH in document
    normalized = " ".join(document.casefold().split())
    assert "server session requirement is unverified" in normalized
    assert "client-side safety gate" in normalized
    assert "validate live only after login" in normalized
    assert "account-neutral" in normalized
    assert "not account-neutral" in normalized
    assert "reservation" in normalized
    assert "payment" in normalized
    assert "caller-supplied" in normalized
    assert "no runtime pass or menu code is hardcoded" in normalized
