"""Public type boundaries must not constrain future server codes or copy raw data."""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import get_type_hints

import korail_mobile_api as api
from korail_mobile_api.models import TrainSummary
from korail_mobile_api.session import infer_login_input_flag


def test_public_client_signatures_are_concrete() -> None:
    for name, method in inspect.getmembers(api.KorailClient, inspect.isfunction):
        if not name.startswith("_"):
            hints = get_type_hints(method)
            assert "return" in hints, name
            assert "Any" not in str(hints), name
    hints = get_type_hints(api.KorailClient.login)
    assert hints["input_flag"] == api.KorailLoginInputFlag | None
    assert get_type_hints(infer_login_input_flag)["return"] == api.KorailLoginInputFlag
    hints = get_type_hints(api.KorailClient.get_seat_inventory)
    assert hints["room_class_code"] == api.KorailRoomClassCode


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
