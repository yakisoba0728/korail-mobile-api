"""Small invariant tests for common forms and lenient row/scalar helpers."""

from __future__ import annotations

from collections import UserDict

import httpx
import pytest

from korail_mobile_api import KorailConfig
from korail_mobile_api._parsing import _nullable_scalar_fields, _reservation_passengers
from korail_mobile_api._payload_helpers import _device_version_key
from korail_mobile_api.http import KorailHttpClient


@pytest.mark.parametrize("lang", [None, "", "synthetic-language"])
def test_common_form_keeps_order_and_returns_fresh_mapping(lang: str | None) -> None:
    config = KorailConfig(
        device="SYNTHETIC-DEVICE",
        version="SYNTHETIC-VERSION",
        key="SYNTHETIC-APP-KEY",
        lang=lang,
        disable_dynapath=True,
    )
    expected = [
        ("Device", config.device),
        ("Version", config.version),
        ("Key", config.key),
    ]
    if lang is not None:
        expected.append(("lang", lang))
    client = KorailHttpClient(config, transport=httpx.MockTransport(lambda request: httpx.Response(200)))
    try:
        first = client.common_fields()
        assert list(first.items()) == expected
        assert list(_device_version_key(config).items()) == expected
        first["Device"] = "changed"
        assert list(client.common_fields().items()) == expected
    finally:
        client.close()


@pytest.mark.parametrize(
    "value,expected",
    [(None, None), ("", ""), ("Y", "Y"), (12, "12"), (-1, "-1"), (False, None), (1.5, None), ([], None), ({}, None)],
)
def test_nullable_field_map_preserves_optional_policy(value: object, expected: str | None) -> None:
    raw = {"wire": value}
    fields = {"present": "wire", "missing": "absent"}
    assert _nullable_scalar_fields(raw, fields) == {"present": expected, "missing": None}
    assert _nullable_scalar_fields(raw, fields, "synthetic context") == {"present": expected, "missing": None}


@pytest.mark.parametrize("container", [None, [], "invalid", {}, {"psg_info": None}, {"psg_info": {}}])
def test_passenger_rows_keep_lenient_container_policy(container: object) -> None:
    assert _reservation_passengers({"psg_infos": container}) == ()


def test_passenger_rows_filter_only_non_mappings_and_copy_row_raw() -> None:
    row = UserDict({"h_psg_tp_cd": 1, "h_psg_info_per_prnb": "2", "h_dcnt_knd_cd": False})
    result = _reservation_passengers({"psg_infos": {"psg_info": [None, "invalid", row, {}]}})
    assert len(result) == 2
    assert result[0].passenger_type_code == "1" and result[0].passenger_count == "2"
    assert result[0].discount_kind_code is None
    assert result[0].raw == row and result[0].raw is not row
    assert result[1].passenger_type_code is None
