"""Public types preserve future server codes, import paths and documented raw sharing."""

from __future__ import annotations

import importlib
import inspect
import pickle
import pkgutil
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import get_type_hints

import pytest

import korail_mobile_api as api
from korail_mobile_api import TrainSummary, _domains
from korail_mobile_api._core.session import infer_login_input_flag
from korail_mobile_api._domains.payments.parsers import (
    parse_refund_ticket_response,
    parse_reservation_payment_response,
)
from korail_mobile_api._domains.reservations.parsers import parse_reservation_hold_response
from korail_mobile_api._domains.tickets.forms import build_self_seat_change_info_form

DOMAIN_MODULES = [
    importlib.import_module(info.name)
    for info in pkgutil.walk_packages(_domains.__path__, prefix=_domains.__name__ + ".")
    if not info.ispkg
]


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
def test_self_seat_change_preserves_room_codes(room_class_code: str | None) -> None:
    """SeatAvailabilityIn.java:26-30,55: String, no allowlist (PsrmType.java:19-29 literals are protected);
    SelfSeatChangeOptionViewModel.java:342-344: psrmClCd only when the room value is not null."""
    request = api.SelfSeatChangeInfoRequest(
        run_date="20261007",
        train_no="00001",
        departure_station_code="TEST-A",
        arrival_station_code="TEST-B",
        room_class_code=room_class_code,
    )
    form = build_self_seat_change_info_form(request)
    if room_class_code is None:
        assert "psrmClCd" not in form
    else:
        assert form["psrmClCd"] == room_class_code


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
    request = SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code=room_code)
    assert_type(request.room_class_code, str | None)

# Strict mypy checks that these ignores are necessary, proving each argument is rejected.
SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code=1)  # type: ignore[arg-type]
SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code=True)  # type: ignore[arg-type]
SelfSeatChangeInfoRequest(run_date="20261007", train_no="00001", departure_station_code="TEST-A", arrival_station_code="TEST-B", room_class_code=object())  # type: ignore[arg-type]
""",
        encoding="utf-8",
    )
    stdout, stderr, status = mypy.run(
        ["--config-file", str(config), "--cache-dir", str(tmp_path / "mypy-cache"), str(consumer)]
    )
    assert status == 0, stdout + stderr
