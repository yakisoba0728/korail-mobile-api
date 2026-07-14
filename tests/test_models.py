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
