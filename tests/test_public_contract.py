import inspect
from typing import get_type_hints

import korail_mobile_api
import korail_mobile_api.models as models
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.models import (
    KorailStation,
    KorailSession,
    StationDataResponse,
    TrainSummary,
    UuidResponse,
)


def test_client_public_method_set_is_stable():
    methods = {
        name
        for name, value in inspect.getmembers(
            KorailClient,
            predicate=inspect.isfunction,
        )
        if not name.startswith("_")
    }
    assert methods == {
        "clear_session",
        "close",
        "get_app_data",
        "get_common_code",
        "get_maas_menu_list",
        "get_maas_station_data",
        "get_notice",
        "get_station_data",
        "get_station_info",
        "get_ticket_list",
        "get_train_calendar",
        "get_train_schedule",
        "get_transfer_stations",
        "get_uuid",
        "login",
        "logout",
        "search_trains",
    }


def test_uuid_maas_signatures_types_and_exports_are_stable():
    uuid_signature = inspect.signature(KorailClient.get_uuid)
    menu_signature = inspect.signature(KorailClient.get_maas_menu_list)
    maas_signature = inspect.signature(KorailClient.get_maas_station_data)
    assert list(uuid_signature.parameters) == ["self"]
    assert list(menu_signature.parameters) == ["self"]
    assert list(maas_signature.parameters) == [
        "self",
        "additional_service_code",
    ]
    uuid_hints = get_type_hints(KorailClient.get_uuid)
    menu_hints = get_type_hints(KorailClient.get_maas_menu_list)
    maas_hints = get_type_hints(KorailClient.get_maas_station_data)
    assert uuid_hints["return"] is UuidResponse
    assert menu_hints["return"] is models.MaasMenuListResponse
    assert maas_hints["additional_service_code"] is str
    assert maas_hints["return"] is StationDataResponse
    assert (
        maas_signature.parameters["additional_service_code"].default
        is inspect.Parameter.empty
    )
    expected_models = {
        "UuidResponse": UuidResponse,
        "MaasMenuItem": models.MaasMenuItem,
        "MaasMenuListResponse": models.MaasMenuListResponse,
        "KorailStation": KorailStation,
        "StationDataResponse": StationDataResponse,
    }
    for name, model in expected_models.items():
        assert name in korail_mobile_api.__all__
        assert getattr(korail_mobile_api, name) is model


def test_completed_errors_are_exported():
    assert korail_mobile_api.KorailSessionExpiredError
    assert korail_mobile_api.KorailDynaPathError
    assert korail_mobile_api.KorailTransportError
    assert korail_mobile_api.KorailAppError


def test_login_and_ticket_signatures_remain_compatible():
    assert list(inspect.signature(KorailClient.login).parameters) == [
        "self",
        "member_no",
        "password",
        "input_flag",
        "check_valid_pw",
        "cust_id",
        "etr_path",
    ]
    assert list(inspect.signature(KorailClient.get_ticket_list).parameters) == [
        "self",
        "page_no",
    ]


def test_cache_method_signatures_and_types_are_public():
    from korail_mobile_api.models import AppDataResponse, NoticeResponse

    app_signature = inspect.signature(KorailClient.get_app_data)
    notice_signature = inspect.signature(KorailClient.get_notice)
    assert list(app_signature.parameters) == ["self", "timestamp_ms"]
    assert list(notice_signature.parameters) == ["self", "timestamp_ms"]
    assert app_signature.parameters["timestamp_ms"].default is None
    assert notice_signature.parameters["timestamp_ms"].default is None
    assert app_signature.return_annotation is AppDataResponse
    assert notice_signature.return_annotation is NoticeResponse
    for name in ("AppDataResponse", "AppVersionInfo", "NoticeResponse"):
        assert getattr(korail_mobile_api, name)


def test_config_preserves_baseline_positional_constructor_order():
    dynapath = DynapathConfig()
    config = KorailConfig(
        "https://smart.letskorail.com",
        "DEVICE",
        "VERSION",
        "KEY",
        12.5,
        "USER-AGENT",
        "LIVE_FLAG",
        dynapath,
    )
    assert list(inspect.signature(KorailConfig).parameters)[:8] == [
        "base_url",
        "device",
        "version",
        "key",
        "timeout",
        "user_agent",
        "live_env_var",
        "dynapath",
    ]
    assert config.dynapath is dynapath
    assert config.device_width == 1080


def test_config_defaults_advertising_id_to_empty_string():
    assert KorailConfig().advertising_id == ""


def test_session_preserves_baseline_raw_positional_argument():
    raw = {"legacy": "session"}
    session = KorailSession("cookie", "member", raw)
    assert list(inspect.signature(KorailSession).parameters)[:3] == [
        "jsessionid",
        "member_no",
        "raw",
    ]
    assert session.raw is raw
    assert session.member_card_no is None


def test_train_summary_preserves_baseline_positional_constructor_order():
    raw = {"legacy": "train"}
    train = TrainSummary(
        "00123",
        "100",
        "0001",
        "0020",
        "20260710",
        "060000",
        "083000",
        raw,
    )
    assert list(inspect.signature(TrainSummary).parameters)[:8] == [
        "train_no",
        "train_group_code",
        "departure_station_code",
        "arrival_station_code",
        "departure_date",
        "departure_time",
        "arrival_time",
        "raw",
    ]
    assert train.departure_date == "20260710"
    assert train.departure_time == "060000"
    assert train.arrival_time == "083000"
    assert train.raw is raw
    assert train.departure_station_name is None
    assert train.arrival_station_name is None
