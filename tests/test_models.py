# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

from dataclasses import FrozenInstanceError, is_dataclass

import pytest

import korail_mobile_api
import korail_mobile_api.models as models
from korail_mobile_api import KorailConfig
from korail_mobile_api.errors import (
    KorailApiError,
    KorailAuthError,
    KorailDynaPathError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import (
    AppDataResponse,
    AppVersionInfo,
    BaseKorailResponse,
    KorailSession,
    KorailStation,
    NoticeResponse,
    StationDataResponse,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
    UuidResponse,
)


def test_public_exports_are_available():
    assert korail_mobile_api.KorailConfig is KorailConfig
    assert issubclass(KorailAuthError, KorailApiError)
    assert issubclass(KorailProtocolError, KorailApiError)


def test_core_models_are_dataclasses():
    assert is_dataclass(KorailConfig)
    assert is_dataclass(KorailSession)
    assert is_dataclass(TrainSearchQuery)
    assert is_dataclass(TrainSummary)
    assert is_dataclass(TrainSearchResult)


def test_train_summary_exposes_seat_map_flag_and_general_reservation_code():
    train = TrainSummary.from_raw(
        {
            "h_trn_no": "00001",
            "h_rd_seat_map_flg": "Y",
            "h_gen_rsv_cd": "11",
        }
    )

    assert train.seat_map_flag == "Y"
    assert train.general_reservation_code == "11"


def test_train_summary_retains_apk_suspension_flag():
    train = TrainSummary.from_raw(
        {"h_trn_no": "00001", "h_trn_sps_flg": "SYNTHETIC-SUSPENDED"}
    )
    assert train.train_suspension_flag == "SYNTHETIC-SUSPENDED"


def test_config_defaults_match_design():
    config = KorailConfig()
    assert config.base_url == "https://smart.letskorail.com"
    assert config.device == "AD"
    assert config.version == "250601003"
    assert config.key == "korail1234567890"
    assert config.timeout == 60.0
    assert config.live_env_var == "KORAIL_MOBILE_API_LIVE"


def test_completed_error_hierarchy_is_public():
    assert issubclass(KorailSessionExpiredError, KorailAuthError)
    assert issubclass(KorailDynaPathError, KorailApiError)


def test_sensitive_model_fields_do_not_appear_in_repr():
    session = KorailSession(
        jsessionid="cookie-secret",
        member_no="member-secret",
        raw={"txtPwd": "pw"},
    )
    response = BaseKorailResponse(raw={"JSESSIONID": "cookie-secret"})
    assert "cookie-secret" not in repr(session)
    assert "member-secret" not in repr(session)
    assert "cookie-secret" not in repr(response)


def test_cache_response_models_are_frozen_dataclasses():
    assert is_dataclass(AppVersionInfo)
    assert is_dataclass(AppDataResponse)
    assert is_dataclass(NoticeResponse)

    response = AppDataResponse(for_seat_intg="Y")
    with pytest.raises(FrozenInstanceError):
        response.for_seat_intg = "N"


def test_uuid_and_station_models_are_frozen_and_repr_safe():
    station = KorailStation(
        code="0001",
        name="서울",
        raw={"secret": "station-raw-secret"},
    )
    uuid = UuidResponse(
        verification_code="uuid-secret",
        raw={"mutMrkVrfCd": "uuid-secret"},
    )
    response = StationDataResponse(stations=(station,))
    assert is_dataclass(UuidResponse)
    assert is_dataclass(KorailStation)
    assert is_dataclass(StationDataResponse)
    assert "uuid-secret" not in repr(uuid)
    assert "station-raw-secret" not in repr(station)
    with pytest.raises(FrozenInstanceError):
        response.stations = ()


def test_maas_menu_models_are_frozen_and_hide_service_code_and_raw():
    menu = models.MaasMenuItem(
        active="Y",
        additional_service_code="maas-service-secret",
        app_data="Y",
        raw={"marker": "maas-raw-secret"},
    )
    response = models.MaasMenuListResponse(items=(menu,))

    assert is_dataclass(models.MaasMenuItem)
    assert is_dataclass(models.MaasMenuListResponse)
    assert menu.uses_station_selection is True
    assert "maas-service-secret" not in repr(menu)
    assert "maas-raw-secret" not in repr(menu)
    with pytest.raises(FrozenInstanceError):
        response.items = ()


def test_maas_menu_models_hide_urls_with_sensitive_query_values():
    marker = "sensitive-reservation-marker"
    menu = models.MaasMenuItem(
        icon_off=f"https://example.invalid/off?pnrNo={marker}",
        icon_on=f"https://example.invalid/on?tkRetNo={marker}",
        popup_image=f"https://example.invalid/popup?addSrvReqNo={marker}",
        url=f"https://example.invalid/menu?pnrNo={marker}",
    )
    response = models.MaasMenuListResponse(
        items=(menu,),
        departure_elevator_url=(
            f"https://example.invalid/departure?pnrNo={marker}"
        ),
        arrival_bus_info_url=(
            f"https://example.invalid/arrival?tkRetNo={marker}"
        ),
    )

    assert marker not in repr(menu)
    assert marker not in repr(response)


def test_maas_limo_menu_is_not_selected_for_station_lookup():
    menu = models.MaasMenuItem(
        active="Y",
        additional_service_code="server-code",
        app_data="Y",
        menu_type="N",
    )

    assert menu.uses_station_selection is False


@pytest.mark.parametrize("app_data", ["Y", "M10", "M30"])
def test_maas_station_app_routing_markers_are_eligible(app_data):
    menu = models.MaasMenuItem(
        active="Y",
        additional_service_code="server-code",
        app_data=app_data,
        menu_type="Y",
    )

    assert menu.uses_station_selection is True


def _raw_fields():
    import dataclasses
    import importlib

    for module_name in ("models", "read_models", "limousine_models", "mutation_models"):
        module = importlib.import_module(f"korail_mobile_api.{module_name}")
        for name, obj in vars(module).items():
            if (
                dataclasses.is_dataclass(obj)
                and isinstance(obj, type)
                and obj.__module__ == module.__name__
            ):
                for field_ in dataclasses.fields(obj):
                    if field_.name in {"raw", "detail_raw"}:
                        yield f"{module_name}.{name}.{field_.name}", field_


def test_no_model_compares_or_hashes_its_raw_payload():
    # raw is the server's JSON kept as evidence, not part of what a parsed
    # value is. Compared, it made two responses with the same parsed fields
    # unequal over a key nobody reads, and made every frozen model unhashable.
    fields = dict(_raw_fields())
    assert len(fields) >= 78
    compared = sorted(name for name, field_ in fields.items() if field_.compare)
    assert compared == []


def test_two_responses_that_differ_only_in_raw_are_equal_and_hashable():
    first = BaseKorailResponse("S000", "ok", "SUCC", raw={"h_msg_cd": "S000"})
    second = BaseKorailResponse("S000", "ok", "SUCC", raw={"extra": 1})
    assert first == second
    assert hash(first) == hash(second)
    assert first != BaseKorailResponse("S001", "ok", "SUCC", raw={"h_msg_cd": "S000"})
