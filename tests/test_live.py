import pytest

from korail_mobile_api import KorailConfig
from korail_mobile_api.live import live_enabled, read_credentials_from_env
from korail_mobile_api.models import (
    AppDataResponse,
    BaseKorailResponse,
    KorailSession,
    NoticeResponse,
    TrainSearchQuery,
    TrainSearchResult,
    TrainSummary,
)


def test_live_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KORAIL_MOBILE_API_LIVE", raising=False)
    assert live_enabled() is False


def test_live_enabled_only_with_explicit_flag(monkeypatch):
    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    assert live_enabled() is True


def test_credentials_are_read_from_environment(monkeypatch):
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "pw")
    assert read_credentials_from_env() == ("member", "pw")


def test_build_config_from_env_requires_device_identity(monkeypatch):
    import korail_mobile_api.live as live

    for name in (
        "KORAIL_DYNAPATH_DEVICE_ID",
        "KORAIL_DYNAPATH_OS_VERSION",
        "KORAIL_DYNAPATH_DEVICE_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="KORAIL_DYNAPATH_DEVICE_ID"):
        live.build_config_from_env()


def test_build_config_from_env_builds_sdk_settings(monkeypatch):
    import korail_mobile_api.live as live

    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.setenv("KORAIL_ADVERTISING_ID", "ad-id")
    monkeypatch.setattr(live.time, "time", lambda: 1712345600.0)
    config = live.build_config_from_env()
    assert config.dynapath.token_provider is None
    assert config.dynapath.token_settings.device_id == "device-1"
    assert config.dynapath.token_settings.app_start_ts == "1712345600000"
    assert config.dynapath.token_settings.sdk_version == "v1"
    assert config.dynapath.token_settings.as_value == (
        "[38ff229cb34c7dda8e28220a2d750cce]"
    )
    assert config.advertising_id == "ad-id"


def test_build_config_from_env_defaults_advertising_id_to_empty(monkeypatch):
    import korail_mobile_api.live as live

    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_ID", "device-1")
    monkeypatch.setenv("KORAIL_DYNAPATH_OS_VERSION", "14")
    monkeypatch.setenv("KORAIL_DYNAPATH_DEVICE_MODEL", "SM-S911N")
    monkeypatch.delenv("KORAIL_ADVERTISING_ID", raising=False)

    config = live.build_config_from_env()

    assert config.advertising_id == ""


def test_run_live_smoke_calls_every_current_read_without_raw_output(monkeypatch):
    import korail_mobile_api.live as live

    calls: list[tuple[object, ...]] = []
    ok = BaseKorailResponse(
        h_msg_cd="IRG000000",
        h_msg_txt="OK",
        str_result="SUCC",
        raw={},
    )
    train = TrainSummary(
        train_no="00123",
        departure_date="20260710",
        departure_station_code="0001",
        arrival_station_code="0020",
    )

    class FakeClient:
        def __init__(self, _config):
            calls.append(("init",))

        def get_app_data(self) -> AppDataResponse:
            calls.append(("get_app_data",))
            return AppDataResponse(
                h_msg_cd="S000",
                str_result="SUCC",
                raw={"version": {"AMESSAGE": "must not leak"}},
            )

        def get_notice(self) -> NoticeResponse:
            calls.append(("get_notice",))
            return NoticeResponse(
                h_msg_cd="S000",
                str_result="SUCC",
                raw={"ptwtTtl": "must not leak"},
            )

        def login(self, member_no: str, password: str) -> KorailSession:
            calls.append(("login", member_no, password))
            return KorailSession(jsessionid="session", member_no=member_no)

        def get_common_code(self, code: str = "") -> BaseKorailResponse:
            calls.append(("get_common_code", code))
            return BaseKorailResponse(
                h_msg_cd="API.I00000",
                str_result="SUCC",
                raw={},
            )

        def get_station_info(self, device: str = "AD") -> BaseKorailResponse:
            calls.append(("get_station_info", device))
            return BaseKorailResponse(raw={"map_version": "1"})

        def get_station_data(self) -> BaseKorailResponse:
            calls.append(("get_station_data",))
            return BaseKorailResponse(
                raw={
                    "stns": {
                        "stn": [
                            {"stn_cd": "0001"},
                            {"stn_cd": "0020"},
                        ]
                    }
                }
            )

        def get_train_calendar(self) -> BaseKorailResponse:
            calls.append(("get_train_calendar",))
            return BaseKorailResponse(
                h_msg_cd="IRG000000",
                str_result="SUCC",
                raw={"days": [{"runDt": "20260710"}]},
            )

        def search_trains(self, query: TrainSearchQuery) -> TrainSearchResult:
            calls.append(
                (
                    "search_trains",
                    query.departure_station_code,
                    query.arrival_station_code,
                )
            )
            return TrainSearchResult(trains=[train], response=ok, raw={})

        def get_train_schedule(
            self,
            run_date: str,
            train_no: str,
        ) -> BaseKorailResponse:
            calls.append(("get_train_schedule", run_date, train_no))
            return BaseKorailResponse(
                h_msg_cd="API.I00000",
                str_result="SUCC",
                raw={},
            )

        def get_transfer_stations(
            self,
            departure: str,
            arrival: str,
        ) -> BaseKorailResponse:
            calls.append(("get_transfer_stations", departure, arrival))
            return ok

        def get_ticket_list(self, page_no: int = 0) -> BaseKorailResponse:
            calls.append(("get_ticket_list", page_no))
            return BaseKorailResponse(
                h_msg_cd="WRT300005",
                str_result="SUCC",
                raw={},
            )

        def close(self) -> None:
            calls.append(("close",))

    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "password")
    monkeypatch.setattr(live, "KorailClient", FakeClient)
    monkeypatch.setattr(live, "build_config_from_env", KorailConfig)
    result = live.run_live_smoke_from_env()

    assert result == {
        "appDataLoaded": True,
        "noticeLoaded": True,
        "loggedIn": True,
        "commonCode": "API.I00000",
        "stationInfoLoaded": True,
        "stationDataCount": 2,
        "calendarCode": "IRG000000",
        "trainCount": 1,
        "scheduleCode": "API.I00000",
        "transferCode": "IRG000000",
        "ticketCode": "WRT300005",
    }
    assert "password" not in repr(result).lower()
    assert "must not leak" not in repr(result)
    assert "raw" not in result
    assert [call[0] for call in calls] == [
        "init",
        "get_app_data",
        "get_notice",
        "login",
        "get_common_code",
        "get_station_info",
        "get_station_data",
        "get_train_calendar",
        "search_trains",
        "get_train_schedule",
        "get_transfer_stations",
        "get_ticket_list",
        "close",
    ]
