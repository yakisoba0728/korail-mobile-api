from dataclasses import FrozenInstanceError, is_dataclass

import korail_mobile_api
import pytest
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
