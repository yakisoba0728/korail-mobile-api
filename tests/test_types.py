"""Public type boundaries must not constrain future server codes or copy raw data."""

from __future__ import annotations

import inspect
import pickle
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import get_type_hints

import pytest

import korail_mobile_api as api
from korail_mobile_api import read_parsers, read_payloads
from korail_mobile_api.models import TrainSummary
from korail_mobile_api.read_payloads import build_self_seat_change_info_form
from korail_mobile_api.session import infer_login_input_flag


@pytest.mark.parametrize("module", [read_parsers, read_payloads])
def test_split_parser_and_builder_import_contracts(module: ModuleType) -> None:
    for name, function in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith(("parse_", "build_")) and name != "self_checkin_ticket_fields":
            continue
        # This pre-existing alias intentionally points to the general payload module.
        if name == "build_cache_query":
            continue
        assert function.__module__ == module.__name__, name
        assert pickle.loads(pickle.dumps(function)) is function, name
        assert "return" in get_type_hints(function), name


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


def test_unknown_response_codes_remain_strings() -> None:
    raw = {"h_trn_no": "00001", "h_trn_gp_cd": "FUTURE-GROUP", "h_gen_rsv_cd": "FUTURE-STATE"}
    train = TrainSummary.from_raw(raw)
    assert train.train_group_code == "FUTURE-GROUP"
    assert train.general_reservation_code == "FUTURE-STATE"
    hints = get_type_hints(TrainSummary)
    assert hints["train_group_code"] == str | None
    assert hints["general_reservation_code"] == str | None


@pytest.mark.parametrize("room_class_code", ["1", "2", "FUTURE", None])
def test_self_seat_change_preserves_room_codes(room_class_code: str | None) -> None:
    request = api.SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", room_class_code)
    form = build_self_seat_change_info_form(request)
    if room_class_code is None:
        assert "psrmClCd" not in form
    else:
        assert form["psrmClCd"] == room_class_code


@pytest.mark.parametrize("room_class_code", [1, True, object(), "", " "])
def test_self_seat_change_rejects_invalid_room_codes(room_class_code: object) -> None:
    with pytest.raises(api.KorailProtocolError, match="room_class_code must not be empty"):
        api.SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", room_class_code)  # type: ignore[arg-type]


def test_commuter_passenger_request_requires_factory() -> None:
    with pytest.raises(TypeError, match=r"CommuterPassengerRequest must be created with from_response\(\)"):
        api.CommuterPassengerRequest()


def test_self_seat_change_consumer_type_contract(tmp_path: Path) -> None:
    mypy = pytest.importorskip("mypy.api")
    config = tmp_path / "mypy.ini"
    config.write_text(
        "[mypy]\nstrict = True\npython_version = 3.11\n"
        f"mypy_path = {Path(__file__).resolve().parents[1] / 'src'}\n",
        encoding="utf-8",
    )
    consumer = tmp_path / "consumer.py"
    consumer.write_text(
        """from typing import assert_type

from korail_mobile_api import KorailSelfSeatChangeRoomClassCode, SelfSeatChangeInfoRequest

server_code: KorailSelfSeatChangeRoomClassCode = "FUTURE"
for room_code in ("1", "2", server_code, None):
    request = SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", room_code)
    assert_type(request.room_class_code, str | None)

# Strict mypy checks that these ignores are necessary, proving each argument is rejected.
SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", 1)  # type: ignore[arg-type]
SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", True)  # type: ignore[arg-type]
SelfSeatChangeInfoRequest("20261007", "00001", "TEST-A", "TEST-B", object())  # type: ignore[arg-type]
""",
        encoding="utf-8",
    )
    stdout, stderr, status = mypy.run(
        ["--config-file", str(config), "--cache-dir", str(tmp_path / "mypy-cache"), str(consumer)]
    )
    assert status == 0, stdout + stderr
