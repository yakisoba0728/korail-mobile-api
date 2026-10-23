"""Public types preserve future server codes, import paths and documented raw sharing."""

from __future__ import annotations

import importlib
import inspect
import json
import pickle
import pkgutil
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import get_args, get_type_hints

import pytest
from conftest import wire_form

import korail_mobile_api as api
from korail_mobile_api import TrainSummary, _domains
from korail_mobile_api._core.session import infer_login_input_flag
from korail_mobile_api._domains.payments.parsers import (
    parse_refund_ticket_response,
    parse_reservation_payment_response,
)
from korail_mobile_api._domains.reservations.parsers import parse_reservation_hold_response

DOMAIN_MODULES = [
    importlib.import_module(info.name)
    for info in pkgutil.walk_packages(_domains.__path__, prefix=_domains.__name__ + ".")
    if not info.ispkg
]

REQUIRED_WIRE_MODELS = {
    name: model
    for name in api.__all__
    if inspect.isclass(model := getattr(api, name))
    and is_dataclass(model)
    and any("wire" in item.metadata and item.default is MISSING for item in fields(model))
}


def _constructor_values(model: type) -> dict[str, object]:
    literals = {str: "SYNTHETIC", int: 1, str | None: None, tuple[int, int, int]: (1, 0, 0)}
    hints = get_type_hints(model)
    return {
        item.name: literals[hints[item.name]]
        for item in fields(model)
        if item.init and item.default is MISSING and item.default_factory is MISSING
    }


def test_required_wire_constructor_and_reader_contracts() -> None:
    total = 0
    for name, model in REQUIRED_WIRE_MODELS.items():
        assert getattr(importlib.import_module(model.__module__), name) is model
        values = _constructor_values(model)
        instance = model(**values)
        assert pickle.loads(pickle.dumps(instance)) == instance
        assert model.__dataclass_params__.frozen
        for item in fields(model):
            if "wire" not in item.metadata or item.default is not MISSING:
                continue
            total += 1
            parameter = inspect.signature(model).parameters[item.name]
            assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
            assert parameter.default is inspect.Parameter.empty
            with pytest.raises(TypeError, match=item.name):
                model(**{key: value for key, value in values.items() if key != item.name})
    assert total == 104

    for module in DOMAIN_MODULES:
        for model in vars(module).values():
            if not inspect.isclass(model) or not is_dataclass(model):
                continue
            hints = get_type_hints(model)
            for item in fields(model):
                if "read" not in item.metadata:
                    continue
                returned = get_type_hints(item.metadata["read"])["return"]
                assert set(get_args(returned) or (returned,)) <= set(
                    get_args(hints[item.name]) or (hints[item.name],)
                ), (model.__name__, item.name)


@pytest.mark.parametrize("module", DOMAIN_MODULES, ids=lambda module: module.__name__.split("_domains.")[1])
def test_domain_parser_and_builder_import_contracts(module: ModuleType) -> None:
    """Functions keep the module they are defined in, so pickling by reference finds them again."""
    own = 0
    for name, function in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith(("parse_", "build_")) and name != "self_checkin_ticket_fields":
            continue
        assert function.__module__.startswith(_domains.__name__ + "."), name
        assert pickle.loads(pickle.dumps(function)) is function, name
        assert "return" in get_type_hints(function), name
        own += function.__module__ == module.__name__
    if module.__name__.endswith((".forms", ".parsers")):
        assert own, module.__name__


def test_public_callable_signatures_are_concrete() -> None:
    for name in api.__all__:
        value = getattr(api, name)
        if inspect.isclass(value):
            methods = inspect.getmembers(
                value, lambda member: inspect.isfunction(member) or inspect.ismethod(member)
            )
        elif inspect.isfunction(value):
            methods = [(name, value)]
        else:
            continue
        for method_name, method in methods:
            if method_name.startswith("_"):
                continue
            hints = get_type_hints(method)
            assert "return" in hints, (name, method_name)
            assert "Any" not in str(hints), (name, method_name)
    hints = get_type_hints(api.KorailClient.login)
    assert hints["input_flag"] == api.KorailLoginInputFlag | None
    assert get_type_hints(infer_login_input_flag)["return"] == api.KorailLoginInputFlag
    hints = get_type_hints(api.KorailClient.get_seat_inventory)
    assert hints["room_class_code"] == api.KorailRoomClassCode
    assert get_type_hints(api.PaidTicket.from_refund_detail)["detail"] is api.RefundTicketDetailResponse


def test_public_raw_fields_expose_objects_not_any() -> None:
    for name in api.__all__:
        model = getattr(api, name)
        if inspect.isclass(model) and is_dataclass(model):
            hints = get_type_hints(model)
            for attribute in fields(model):
                assert "Any" not in str(hints[attribute.name]), (name, attribute.name)
            if "raw" in hints:
                assert hints["raw"] == Mapping[str, object], name
    raw = {"strResult": "SUCC", "extra": {"nested": [1, "synthetic"]}}
    parsed = api.BaseKorailResponse.from_raw(raw)
    assert parsed.raw is raw
    assert api.BaseKorailResponse().raw is not api.BaseKorailResponse().raw


@pytest.mark.parametrize("key", [1, None, ("synthetic",)])
def test_from_raw_rejects_non_string_keys_without_losing_raw(key: object) -> None:
    raw = {key: "synthetic", "strResult": "SUCC"}
    with pytest.raises(api.KorailProtocolError) as caught:
        api.BaseKorailResponse.from_raw(raw)
    assert caught.value.raw is raw
    assert caught.value.request_sent is None


def test_inherited_from_raw_is_envelope_only_and_wraps_constructor_failure() -> None:
    raw = {"strResult": "FAIL", "count": "2", "map_version": "synthetic", "nested": {1: ["untouched"]}}
    response = api.StationInfoResponse.from_raw(raw)
    assert response.raw is raw and response.str_result == "FAIL"
    assert response.count == "" and response.map_version is None
    assert api.RefundCommissionResponse.from_raw(raw)._request_context is None
    complete = {
        "strResult": "SUCC",
        "acepCustMgNo": "TEST-ID",
        "acepCustNm": "TEST-NAME",
        "acepCustTeln": "TEST-PHONE",
        "mbCrdNo": "TEST-CARD",
    }
    with pytest.raises(api.KorailProtocolError) as caught:
        api.DeliveryRecipientResponse.from_raw(complete)
    assert caught.value.raw is complete
    assert isinstance(caught.value.__cause__, TypeError)
    assert caught.value.request_sent is None


def test_inherited_from_raw_keeps_envelope_extraction_outside_constructor_catch() -> None:
    original = TypeError("synthetic envelope extraction")
    calls = []

    class BrokenEnvelope(dict):
        def get(self, key, default=None):
            calls.append(key)
            raise original

    raw = BrokenEnvelope(strResult="SUCC")
    with pytest.raises(TypeError) as caught:
        api.DeliveryRecipientResponse.from_raw(raw)
    assert caught.value is original and caught.value.__cause__ is None
    assert calls == ["h_msg_cd"] and raw == {"strResult": "SUCC"}


def test_commuter_factory_copies_read_only_sequence_input() -> None:
    pass_data = api.PassMenuData(commuter_kind_code="TEST-KIND")
    source = api.CommuterInfoResponse(
        passenger_options=(api.CommuterPassengerOption(commuter_usage_age_code="TEST-AGE"),)
    )
    counts = [1]
    request = api.CommuterPassengerRequest.from_response(pass_data, source, counts)
    counts[0] = 2
    assert request.passenger_counts == (1,)
    assert request.source is source and request.pass_data is pass_data
    for invalid in ([True], [-1], ["1"], "1", b"1"):
        with pytest.raises(api.KorailProtocolError):
            api.CommuterPassengerRequest.from_response(pass_data, source, invalid)


@pytest.mark.parametrize(
    "parser",
    [
        parse_reservation_hold_response,
        parse_reservation_payment_response,
        parse_refund_ticket_response,
    ],
)
def test_mutation_responses_keep_shallow_raw_copies(parser) -> None:
    nested = {"keep": [1, "synthetic"]}
    raw = {"strResult": "SUCC", "stlList": [], "extra": nested}
    response = parser(raw)
    assert response.raw == raw and response.raw is not raw
    assert response.raw["extra"] is nested
    raw["later"] = "not in the shallow copy"
    assert "later" not in response.raw


# 3.0: every model field that reads one of these wire keys carries the same attribute name.
CANONICAL_WIRE_NAMES = {
    "addSrvDvCd": "additional_service_code",
    "addSrvReqNo": "additional_service_request_no",
    "arvDt": "arrival_date",
    "dptDt": "departure_date",
    "arvTm": "arrival_time",
    "dptTm": "departure_time",
    "arvStnConsOrdr": "arrival_construction_order",
    "dptStnConsOrdr": "departure_construction_order",
    "asgnSqno": "assignment_sequence",
    "frcSaleRsnCont": "forced_sale_reason_text",
    "gdTripArNm": "area_name",
    "gnrmRestSeatNum": "general_remaining_seat_count",
    "sprmRestSeatNum": "special_remaining_seat_count",
    "restStndNum": "standing_remaining_seat_count",
    "h_arv_rs_stn_nm": "arrival_station_name",
    "h_dpt_rs_stn_nm": "departure_station_name",
    "h_cmtr_utl_trm_cd": "commuter_period_code",
    "h_dcsp_no": "discount_proof_no",
    "h_dcsp_no2": "discount_proof_no_2",
    "h_fdcert_mg_st_dt": "management_start_date",
    "h_fdcert_mg_cls_dt": "management_close_date",
    "h_page_no": "page_no",
    "h_pre_stl_tgt_flg": "pre_settlement_target_flag",
    "h_psg_info_per_prnb": "passenger_count",
    "h_psrm_cl_nm": "room_class_name",
    "psgTpDvCd": "passenger_type_code",
    "stlbTrnClsfCd": "settlement_train_class_code",
    "strCncDlnDt": "cancellation_deadline",
    "strCncRetAmt": "cancellation_return_amount",
    "strCncRetFee": "cancellation_fee",
    "strRsvSttNm": "reservation_status_name",
    "strStlDlnDt": "settlement_deadline",
    "strStlSttCd": "settlement_status_code",
    "strTotStlAmt": "total_settlement_amount",
    "strUtlTrmCont": "usage_period",
    "trnClsfCd": "train_class_code",
    "trnGpCd": "train_group_code",
    "h_tk_ret_no": "ticket_return_no",
    "h_stl_crd_no": "settlement_card_no",
}


def test_same_wire_key_reads_into_one_attribute_name() -> None:
    models = {
        model
        for module in DOMAIN_MODULES
        for model in vars(module).values()
        if inspect.isclass(model) and is_dataclass(model)
    }
    names = {
        (model.__name__, item.name, CANONICAL_WIRE_NAMES[item.metadata["wire"]])
        for model in models
        for item in fields(model)
        if item.metadata.get("wire") in CANONICAL_WIRE_NAMES
    }
    assert len(names) > 80
    assert {(model, name) for model, name, canonical in names if name != canonical} == set()


def test_unknown_response_codes_remain_strings() -> None:
    raw = {"h_trn_no": "00001", "h_trn_gp_cd": "FUTURE-GROUP", "h_gen_rsv_cd": "FUTURE-STATE"}
    train = TrainSummary.from_raw(raw)
    assert train.train_group_code == "FUTURE-GROUP"
    assert train.general_reservation_code == "FUTURE-STATE"
    hints = get_type_hints(TrainSummary)
    assert hints["train_group_code"] == str | None
    assert hints["general_reservation_code"] == str | None


@pytest.mark.parametrize("room_class_code", ["1", "2", "FUTURE", None])
def test_self_seat_change_preserves_room_codes(
    room_class_code: str | None, scripted_client_factory, f8_logged_in_session
) -> None:
    """SeatAvailabilityIn.java:26-30,55: String, no allowlist (PsrmType.java:19-29 literals are protected);
    SelfSeatChangeOptionViewModel.java:342-344: psrmClCd only when the room value is not null."""
    request = api.SelfSeatChangeInfoRequest(
        run_date="20261007",
        train_no="00001",
        departure_station_code="TEST-A",
        arrival_station_code="TEST-B",
        room_class_code=room_class_code,
    )
    client, requests, _ = scripted_client_factory([{"strResult": "SUCC"}], session=f8_logged_in_session)
    client.get_self_seat_change_options(request)
    form = wire_form(requests[0])
    if room_class_code is None:
        assert "psrmClCd" not in form
    else:
        assert form["psrmClCd"] == [room_class_code]


@pytest.mark.parametrize("room_class_code", [1, True, object(), "", " "])
def test_self_seat_change_rejects_invalid_room_codes(room_class_code: object) -> None:
    with pytest.raises(api.KorailProtocolError, match="room_class_code must not be empty"):
        api.SelfSeatChangeInfoRequest(
            run_date="20261007",
            train_no="00001",
            departure_station_code="TEST-A",
            arrival_station_code="TEST-B",
            room_class_code=room_class_code,
        )  # type: ignore[arg-type]


def test_commuter_passenger_request_requires_factory() -> None:
    with pytest.raises(TypeError, match=r"CommuterPassengerRequest must be created with from_response\(\)"):
        api.CommuterPassengerRequest()


@pytest.mark.parametrize("checker", ["mypy", "pyright"])
def test_public_consumer_type_contract(tmp_path: Path, checker: str) -> None:
    pytest.importorskip(checker)
    source = Path(__file__).resolve().parents[1] / "src"
    config = tmp_path / "mypy.ini"
    config.write_text(
        f"[mypy]\nstrict = True\npython_version = 3.11\nmypy_path = {source}\n",
        encoding="utf-8",
    )
    consumer = tmp_path / "consumer.py"
    positive = """from typing import assert_type

import korail_mobile_api as api
from korail_mobile_api import KorailSelfSeatChangeRoomClassCode, SelfSeatChangeInfoRequest

server_code: KorailSelfSeatChangeRoomClassCode = "FUTURE"
for room_code in ("1", "2", server_code, None):
    request = SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code=room_code)
    assert_type(request.room_class_code, str | None)

first = api.TrainSummary(train_no="1")
second = api.TrainSummary(train_no="2")
assert_type(api.TransferItinerary(first=first, second=second).legs, tuple[api.TrainSummary, api.TrainSummary])
pass_data = api.PassMenuData(commuter_kind_code="TEST-KIND")
source = api.CommuterInfoResponse(passenger_options=(api.CommuterPassengerOption(commuter_usage_age_code="TEST-AGE"),))
for counts in ([1], (1,)):
    commuter = api.CommuterPassengerRequest.from_response(pass_data, source, counts)
    assert_type(commuter.passenger_counts, tuple[int, ...])
api.StationInfoResponse()
api.SelfCheckInInfoResponse()
api.SeatInventoryResponse()
config = api.KorailConfig(timeout=None)
assert_type(config.timeout, float | None)
ticket = api.TicketListTicket(sale_window_no="TEST-WINDOW", sale_date="20990102", return_sale_date="0102", sale_sequence="1", return_password="TEST-PASSWORD")
assert_type(api.OriginalTicketReference.from_ticket(ticket), api.OriginalTicketReference)
assert_type(api.OriginalTicketReference.from_sale_ticket(ticket), api.OriginalTicketReference)
hold = api.ReservationHoldResponse()
reference = api.HoldReference(pnr_no="TEST-PNR", journey_count="1")
assert_type(hold.reference, api.HoldReference)
assert_type(api.HoldReference.from_raw({"h_pnr_no": "TEST-PNR", "h_jrny_cnt": "1"}), api.HoldReference)
korail = api.Korail()
assert_type(api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD", input_flag="4", check_valid_pw="N", cust_id=None, etr_path=None), api.Korail)
assert_type(api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD"), api.Korail)
assert_type(korail.reservations.cancel(hold), api.BaseKorailResponse)
assert_type(korail.reservations.cancel(reference, check_first=False), api.BaseKorailResponse)
for assignments in ([api.KorailSeatAssignment(car_no=1, seat_no="01A")], (api.KorailSeatAssignment(car_no=1, seat_no="01A"),)):
    assert_type(korail.reservations.create(first, job_type=api.KorailReservationJobType.SEAT_DESIGNATED, seats=assignments, seat_attribute_code="015"), api.ReservationHoldResponse)
assert_type(korail.reservations.create(first, seats=None, seat_attribute_code=None), api.ReservationHoldResponse)
"""
    negative: list[str] = []
    for name, model in REQUIRED_WIRE_MODELS.items():
        values = _constructor_values(model)
        arguments = ", ".join(f"{key}={value!r}" for key, value in values.items())
        positive += f"api.{name}({arguments})\n"
        for item in fields(model):
            if "wire" in item.metadata and item.default is MISSING:
                arguments = ", ".join(f"{key}={value!r}" for key, value in values.items() if key != item.name)
                negative.append(f"api.{name}({arguments})")
    assert len(negative) == 104
    negative.extend(
        f'SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code={value})'
        for value in ("1", "True", "object()")
    )
    negative.append('api.CommuterPassengerRequest.from_response(pass_data, source, ["1"])')
    negative.extend(
        [
            "api.OriginalTicketReference.from_sale_ticket(object())",
            'api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD", input_flag=1)',
            'api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD", check_valid_pw="invalid")',
            'api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD", cust_id=1)',
            'api.Korail.logged_in("TEST-MEMBER", "TEST-PASSWORD", etr_path=1)',
            'korail.reservations.cancel(reference, check_first="False")',
            "korail.reservations.cancel(object())",
            'korail.reservations.create(first, seats=["01A"])',
            "korail.reservations.create(first, seat_attribute_code=1)",
        ]
    )
    positive_lines = len(positive.splitlines())
    consumer.write_text(positive + "\n".join(negative) + "\n", encoding="utf-8")
    expected = {(consumer.name, line) for line in range(positive_lines + 1, positive_lines + 1 + len(negative))}
    readers = tmp_path / "readers.py"
    reader_lines = [
        "from collections.abc import Callable, Mapping",
        "from korail_mobile_api._core import parsing",
    ]
    for model in REQUIRED_WIRE_MODELS.values():
        hints = get_type_hints(model)
        for item in fields(model):
            if "wire" not in item.metadata or item.default is not MISSING:
                continue
            read = item.metadata["read"]
            alias = f"readers_{len(reader_lines)}"
            reader_lines.append(f"import {read.__module__} as {alias}")
            reader_lines.append(
                f"check_{len(reader_lines)}: Callable[[Mapping[str, object], str, str], "
                f"{inspect.formatannotation(hints[item.name])}] = {alias}.{read.__name__}"
            )
    reader_lines.append('wrong: int = parsing.wire("wrong", parsing.required_str, default="")')
    expected.add((readers.name, len(reader_lines)))
    reader_lines.append('required: str = parsing.wire("required", parsing.required_str)')
    expected.add((readers.name, len(reader_lines)))
    readers.write_text("\n".join(reader_lines) + "\n", encoding="utf-8")
    if checker == "mypy":
        from mypy import api as mypy

        stdout, stderr, status = mypy.run(
            [
                "--config-file",
                str(config),
                "--cache-dir",
                str(tmp_path / "mypy-cache"),
                "--no-pretty",
                "--no-error-summary",
                str(consumer),
                str(readers),
            ]
        )
        actual = {(name, int(line)) for name, line in re.findall(r"([^/\n]+\.py):(\d+): error:", stdout)}
        assert status == 1 and not stderr, stdout + stderr
        assert actual == expected, stdout
    else:
        config = tmp_path / "pyrightconfig.json"
        config.write_text(
            json.dumps(
                {
                    "include": [str(consumer), str(readers)],
                    "extraPaths": [str(source)],
                    "pythonVersion": "3.11",
                    "typeCheckingMode": "strict",
                    "reportPrivateUsage": False,
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyright",
                "--project",
                str(config),
                "--outputjson",
                "--pythonpath",
                sys.executable,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        diagnostics = json.loads(result.stdout)["generalDiagnostics"]
        actual = {(Path(item["file"]).name, item["range"]["start"]["line"] + 1) for item in diagnostics}
        assert result.returncode == 1, result.stdout + result.stderr
        assert actual == expected, result.stdout
