import os

from korail_mobile_api.models import BaseKorailResponse, KorailSession
from korail_mobile_api.live import live_enabled, read_credentials_from_env


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


def test_run_live_smoke_calls_only_login_station_data_and_calendar(monkeypatch):
    import korail_mobile_api.live as live

    calls = []

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def login(self, member_no: str, password: str) -> KorailSession:
            calls.append(("login", member_no, password))
            return KorailSession(jsessionid="session-123", member_no=member_no)

        def get_station_data(self) -> BaseKorailResponse:
            calls.append(("get_station_data",))
            return BaseKorailResponse(
                h_msg_cd="IRG000000",
                h_msg_txt="OK",
                str_result="SUCC",
                raw={},
            )

        def get_train_calendar(self) -> BaseKorailResponse:
            calls.append(("get_train_calendar",))
            return BaseKorailResponse(
                h_msg_cd="IRG000000",
                h_msg_txt="OK",
                str_result="SUCC",
                raw={},
            )

        def close(self) -> None:
            calls.append(("close",))

    monkeypatch.setenv("KORAIL_MOBILE_API_LIVE", "1")
    monkeypatch.setenv("KORAIL_MEMBER_NO", "member")
    monkeypatch.setenv("KORAIL_PASSWORD", "pw")
    monkeypatch.setattr(live, "KorailClient", FakeClient)

    result = live.run_live_smoke_from_env()

    assert result == {
        "loggedIn": True,
        "stationDataCode": "IRG000000",
        "calendarCode": "IRG000000",
    }
    assert calls == [
        ("login", "member", "pw"),
        ("get_station_data",),
        ("get_train_calendar",),
        ("close",),
    ]
