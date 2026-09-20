# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

import inspect
from collections.abc import Sequence
from typing import get_type_hints

import korail_mobile_api
import korail_mobile_api.models as models
from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.limousine_models import (
    LimousineScheduleQuery,
    LimousineScheduleResponse,
    LimousineSeatInventoryQuery,
    LimousineSeatInventoryResponse,
)
from korail_mobile_api.models import (
    KorailSession,
    KorailStation,
    StationDataResponse,
    TrainSummary,
    UuidResponse,
)
from korail_mobile_api.mutation_models import (
    StationRefundExecutionRequest,
    StationRefundExecutionResponse,
    StationRefundVerificationRequest,
    StationRefundVerificationResponse,
)


def _assert_exported(name: str, expected: object = None) -> None:
    """``name`` is in ``__all__`` and importable -- and is ``expected`` if given."""
    assert name in korail_mobile_api.__all__, name
    exported = getattr(korail_mobile_api, name)
    if expected is None:
        assert exported, name
    else:
        assert exported is expected, name


def test_limousine_signatures_types_and_exports_are_public():
    expected = {
        "get_limousine_schedules": (
            LimousineScheduleQuery,
            LimousineScheduleResponse,
        ),
        "get_limousine_seat_inventory": (
            LimousineSeatInventoryQuery,
            LimousineSeatInventoryResponse,
        ),
    }
    for method_name, (query_type, response_type) in expected.items():
        method = getattr(KorailClient, method_name)
        assert list(inspect.signature(method).parameters) == ["self", "query"]
        assert get_type_hints(method) == {
            "query": query_type,
            "return": response_type,
        }
    for name in (
        "LimousineScheduleQuery",
        "LimousineSeatInventoryQuery",
        "LimousineScheduleViewQuery",
        "LimousineSchedule",
        "LimousineScheduleResponse",
        "LimousineSeat",
        "LimousineSeatInventoryResponse",
        "LimousineRecommendedProduct",
        "LimousineScheduleViewTrain",
        "LimousineScheduleViewResponse",
    ):
        _assert_exported(name)


def test_seat_inventory_signatures_types_and_exports_are_public():
    cars_signature = inspect.signature(KorailClient.get_seat_cars)
    inventory_signature = inspect.signature(
        KorailClient.get_seat_inventory
    )
    assert list(cars_signature.parameters) == [
        "self",
        "train",
        "passenger_count",
        "room_class_code",
        "seat_attribute_code",
    ]
    assert list(inventory_signature.parameters) == [
        "self",
        "train",
        "car_no",
        "passenger_count",
        "room_class_code",
    ]
    assert cars_signature.parameters["passenger_count"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert inventory_signature.parameters["passenger_count"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert cars_signature.parameters["room_class_code"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    assert inventory_signature.parameters["room_class_code"].kind is (
        inspect.Parameter.KEYWORD_ONLY
    )
    cars_hints = get_type_hints(KorailClient.get_seat_cars)
    inventory_hints = get_type_hints(KorailClient.get_seat_inventory)
    assert cars_hints == {
        "train": TrainSummary,
        "passenger_count": int,
        "room_class_code": str,
        "seat_attribute_code": str | None,
        "return": models.SeatCarListResponse,
    }
    assert inventory_hints == {
        "train": TrainSummary,
        "car_no": int,
        "passenger_count": int,
        "room_class_code": str,
        "return": models.SeatInventoryResponse,
    }
    for name in (
        "SeatAttribute",
        "SeatCar",
        "SeatCarListResponse",
        "PhysicalSeat",
        "SeatWindow",
        "SeatInventoryResponse",
    ):
        _assert_exported(name, getattr(models, name))


def test_uuid_maas_signatures_types_and_exports_are_stable():
    uuid_signature = inspect.signature(KorailClient.get_uuid)
    menu_signature = inspect.signature(KorailClient.get_maas_menu_list)
    maas_signature = inspect.signature(KorailClient.get_maas_station_data)
    assert list(uuid_signature.parameters) == ["self"]
    assert list(menu_signature.parameters) == [
        "self", "pnr_no", "ticket_return_numbers"
    ]
    assert list(maas_signature.parameters) == [
        "self",
        "additional_service_code",
    ]
    uuid_hints = get_type_hints(KorailClient.get_uuid)
    menu_hints = get_type_hints(KorailClient.get_maas_menu_list)
    maas_hints = get_type_hints(KorailClient.get_maas_station_data)
    assert uuid_hints["return"] is UuidResponse
    assert menu_hints["return"] is models.MaasMenuListResponse
    assert menu_hints["pnr_no"] == str | None
    assert menu_hints["ticket_return_numbers"] == Sequence[str] | None
    for name in ("pnr_no", "ticket_return_numbers"):
        assert menu_signature.parameters[name].default is None
        assert menu_signature.parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
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
        _assert_exported(name, model)


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
        "mode",
        "boarding_date_from",
        "boarding_date_to",
    ]


def test_new_social_login_and_station_refund_methods_have_explicit_contracts():
    social = inspect.signature(KorailClient.login_social)
    assert list(social.parameters) == [
        "self", "cust_id", "input_flag", "check_valid_pw"
    ]
    assert social.parameters["input_flag"].kind is inspect.Parameter.KEYWORD_ONLY
    assert social.parameters["check_valid_pw"].kind is inspect.Parameter.KEYWORD_ONLY
    assert get_type_hints(KorailClient.login_social) == {
        "cust_id": str,
        "input_flag": str,
        "check_valid_pw": str,
        "return": KorailSession,
    }

    verify = inspect.signature(KorailClient.verify_station_ticket_refund)
    assert list(verify.parameters) == ["self", "request"]
    assert get_type_hints(KorailClient.verify_station_ticket_refund) == {
        "request": StationRefundVerificationRequest,
        "return": StationRefundVerificationResponse,
    }
    for name, model in (
        ("StationRefundVerificationRequest", StationRefundVerificationRequest),
        ("StationRefundVerificationResponse", StationRefundVerificationResponse),
        ("StationRefundExecutionRequest", StationRefundExecutionRequest),
        ("StationRefundExecutionResponse", StationRefundExecutionResponse),
    ):
        _assert_exported(name, model)


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
        _assert_exported(name)


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


def test_raw_typed_core_exports_and_return_hints_are_public():
    expected_models = {
        "StationInfoResponse": models.StationInfoResponse,
        "TrainCalendarDay": models.TrainCalendarDay,
        "TrainCalendarResponse": models.TrainCalendarResponse,
        "TrainScheduleStop": models.TrainScheduleStop,
        "TrainScheduleResponse": models.TrainScheduleResponse,
        "TransferStation": models.TransferStation,
        "TransferStationListResponse": models.TransferStationListResponse,
        "TrainSearchMetadata": models.TrainSearchMetadata,
    }
    for name, model in expected_models.items():
        _assert_exported(name, model)

    methods = {
        "get_station_info": (
            ["self", "device"],
            models.StationInfoResponse,
        ),
        "get_station_data": (["self"], models.StationDataResponse),
        "get_train_calendar": (["self"], models.TrainCalendarResponse),
        "get_train_schedule": (
            ["self", "run_date", "train_no"],
            models.TrainScheduleResponse,
        ),
        "get_transfer_stations": (
            ["self", "departure_station_code", "arrival_station_code"],
            models.TransferStationListResponse,
        ),
    }
    for name, (parameters, return_type) in methods.items():
        method = getattr(KorailClient, name)
        assert list(inspect.signature(method).parameters) == parameters
        assert get_type_hints(method)["return"] is return_type
    assert inspect.signature(KorailClient.get_station_info).parameters[
        "device"
    ].default == "AD"
