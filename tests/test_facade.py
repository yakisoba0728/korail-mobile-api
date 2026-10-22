"""간편 API는 기존 전송 계약을 쓰며 조회 외의 상태 변경을 숨기지 않습니다."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import parse_qs

import httpx
import pytest

from korail_mobile_api import (
    DynapathConfig,
    DynapathRequestContext,
    Korail,
    KorailConfig,
    KorailDeviceProfile,
    KorailPassengerCounts,
    ReservationHoldResponse,
    TrainSearchContinuation,
    TrainSummary,
    build_config_from_profile,
)


def _config() -> KorailConfig:
    return KorailConfig(
        base_url="https://api.example.invalid",
        netfunnel_enabled=False,
        key="SYNTHETIC-KEY",
        dynapath=DynapathConfig(enabled=True, token_provider=lambda *args: "SYNTHETIC-TOKEN"),
    )


def test_search_uses_kst_station_cache_and_nearby_flag() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("common.stationdata"):
            return httpx.Response(
                200,
                json={
                    "stns": {
                        "stn": [
                            {"stn_cd": "0001", "stn_nm": "서울"},
                            {"stn_cd": "0020", "stn_nm": "부산"},
                        ]
                    }
                },
            )
        assert request.url.path.endswith("seatMovie.ScheduleView")
        return httpx.Response(
            200,
            json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "trn_infos": {"trn_info": []}},
        )

    with Korail(_config(), transport=httpx.MockTransport(handler)) as korail:
        moment = datetime(2099, 1, 2, 0, 30, tzinfo=timezone.utc)
        counts = KorailPassengerCounts(adult=2, child=1)
        result = korail.trains.search(
            "서울", "부산", depart_after=moment, passengers=counts, include_nearby_stations=True
        )
        assert result.trains == []
        korail.trains.search("서울", "부산", depart_after=moment)
        station = korail.stations.find("0001")
        assert station is not None and station.name == "서울"
        names = korail.stations.names()
        assert names == {"서울", "부산"}
        names.clear()
        assert korail.stations.names() == {"서울", "부산"}

    assert sum(request.url.path.endswith("common.stationdata") for request in calls) == 1
    first_search = parse_qs(calls[1].content.decode())
    assert first_search["txtGoAbrdDt"] == ["20990102"]
    assert first_search["txtGoHour"] == ["093000"]
    assert first_search["txtPsgFlg_1"] == ["2"]
    assert first_search["txtPsgFlg_2"] == ["1"]
    assert first_search["adjStnScdlOfrFlg"] == ["Y"]
    second_search = parse_qs(calls[2].content.decode())
    assert second_search["adjStnScdlOfrFlg"] == ["N"]
    assert korail.client.http._client.is_closed


def test_past_date_and_unknown_station_do_not_send_search() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.path.endswith("common.stationdata")
        return httpx.Response(200, json={"stns": {"stn": [{"stn_cd": "0001", "stn_nm": "서울"}]}})

    with Korail(_config(), transport=httpx.MockTransport(handler)) as korail:
        with pytest.raises(ValueError, match="지난 출발"):
            korail.trains.search("서울", "부산", depart_after=datetime(2000, 1, 1))
        with pytest.raises(ValueError, match="역을 찾을 수 없습니다"):
            korail.trains.search("서울", "부산", depart_after=datetime(2099, 1, 1))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        pytest.param(
            {"passengers": KorailPassengerCounts(adult=0, teenager=1)},
            {"txtPsgFlg_1": ["1"]},
            id="teenager-counted-as-adult",
        ),
        pytest.param(
            {"continuation": TrainSearchContinuation("0001", "0123")},
            {"qryStNo": ["0001"], "qryStTrnNo": ["0123"]},
            id="continuation-without-station-lookup",
        ),
    ],
)
def test_search_without_station_validation_keeps_request_options(
    kwargs: dict[str, object], expected: dict[str, list[str]]
) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200, json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "trn_infos": {"trn_info": []}}
        )

    with Korail(_config(), transport=httpx.MockTransport(handler), validate_stations=False) as korail:
        korail.trains.search(
            "서울",
            "부산",
            depart_after=datetime(2099, 1, 1),
            **kwargs,
        )
    assert len(calls) == 1
    form = parse_qs(calls[0].content.decode())
    for key, value in expected.items():
        assert form[key] == value
    assert "P11" not in calls[0].content.decode()


def test_reservation_detail_is_an_explicit_follow_up(monkeypatch: pytest.MonkeyPatch) -> None:
    hold = ReservationHoldResponse(str_result="SUCC", pnr_no="SYNTHETIC-PNR")
    with Korail(_config()) as korail:
        calls: list[str] = []

        def reserve(*args: object, **kwargs: object) -> ReservationHoldResponse:
            calls.append("reserve")
            return hold

        def detail(*args: object, **kwargs: object) -> None:
            calls.append("detail")
            raise RuntimeError("synthetic detail failure")

        monkeypatch.setattr(korail.client, "reserve", reserve)
        monkeypatch.setattr(korail.client, "get_ticket_reservation_detail", detail)
        assert korail.reservations.create(TrainSummary(train_no="1")) is hold
        assert calls == ["reserve"]
        with pytest.raises(RuntimeError, match="synthetic detail failure"):
            korail.reservations.detail(hold)
        assert calls == ["reserve", "detail"]


def test_profile_keeps_token_queue_and_device_fields_consistent() -> None:
    profile = KorailDeviceProfile(
        device_id="SYNTHETIC-DEVICE-ID",
        model="SYNTHETIC-MODEL",
        android_release="16",
        build_id="SYNTHETIC-BUILD",
        android_sdk_int=36,
        width=1080,
        height=2400,
    )
    config = build_config_from_profile(profile)
    assert config.dynapath.token_settings is None
    assert config.dynapath.token_provider is not None
    context = DynapathRequestContext(*("synthetic",) * 9)
    token = config.dynapath.token_provider(context)
    assert token == (
        "2!v=2&es=165489088780120535&st=Android&sv=2.0.1&ai=korailplus"
        "&os=MTY&dm=U1lOVEhFVElDLU1PREVM&iid=U1lOVEhFVElDLURFVklDRS1JRA"
    )
    assert "Android 16; SYNTHETIC-MODEL Build/SYNTHETIC-BUILD" in config.netfunnel_user_agent
    assert (config.android_sdk_int, config.device_width, config.device_height) == (36, 1080, 2400)
    assert config.user_agent == "korailtalk"
    assert "SYNTHETIC-DEVICE-ID" not in repr(profile)


def test_profile_rejects_conflicting_token_provider() -> None:
    profile = KorailDeviceProfile("SYNTHETIC-ID", "MODEL", "16", "BUILD")
    with pytest.raises(ValueError, match="configurable DynaPath"):
        build_config_from_profile(profile, base=_config())
    with pytest.raises(ValueError, match="single-line"):
        KorailDeviceProfile("ID\nWRONG", "MODEL", "16", "BUILD")


def _station_and_search_handler(calls: list[httpx.Request]):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("common.stationdata"):
            return httpx.Response(
                200,
                json={
                    "stns": {
                        "stn": [{"stn_cd": "0001", "stn_nm": "서울"}, {"stn_cd": "0020", "stn_nm": "부산"}]
                    }
                },
            )
        return httpx.Response(
            200, json={"strResult": "SUCC", "h_msg_cd": "IRZ000001", "trn_infos": {"trn_info": []}}
        )

    return handler


def test_numeric_codes_fetch_the_station_list_once() -> None:
    """2.6.2: the facade check and the client's code lookup each fetched the list."""
    calls: list[httpx.Request] = []
    with Korail(_config(), transport=httpx.MockTransport(_station_and_search_handler(calls))) as korail:
        korail.trains.search("0001", "0020", depart_after=datetime(2099, 1, 2, tzinfo=timezone.utc))
        korail.stations.all(refresh=True)
    paths = [request.url.path.rsplit(".", 1)[-1] for request in calls]
    assert paths == ["stationdata", "ScheduleView", "stationdata"]
    assert parse_qs(calls[1].content.decode())["txtGoStart"] == ["서울"]


def test_bad_passengers_are_refused_before_the_station_list() -> None:
    calls: list[httpx.Request] = []
    with Korail(_config(), transport=httpx.MockTransport(_station_and_search_handler(calls))) as korail:
        with pytest.raises(TypeError, match="KorailPassengerCounts"):
            korail.trains.search("서울", "부산", passengers=2)  # type: ignore[arg-type]
    assert calls == []


def test_continuation_keeps_the_first_page_moment() -> None:
    """2.6.2: the next page re-read the clock and refused a first-page time over a minute old."""
    calls: list[httpx.Request] = []
    cursor = TrainSearchContinuation("0001", "0123")
    with Korail(_config(), transport=httpx.MockTransport(_station_and_search_handler(calls))) as korail:
        with pytest.raises(ValueError, match="depart_after"):
            korail.trains.search("서울", "부산", continuation=cursor)
        first_page_moment = datetime(2000, 1, 2, 9, 0, tzinfo=timezone.utc)
        korail.trains.search("서울", "부산", depart_after=first_page_moment, continuation=cursor)
    sent = parse_qs(calls[-1].content.decode())
    assert sent["txtGoAbrdDt"] == ["20000102"] and sent["txtGoHour"] == ["180000"]
    assert sent["qryStTrnNo"] == ["0123"]
