import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.models import TrainSearchQuery


def make_client(load_json_fixture, paths):
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append((request.method, request.url.path, request.content.decode()))
        fixture = paths.get(request.url.path)
        if fixture is None:
            raise AssertionError(f"unexpected path {request.url.path}")
        return httpx.Response(200, json=load_json_fixture(fixture))

    return KorailClient(KorailConfig(), transport=httpx.MockTransport(handler)), captured


def test_station_and_calendar_read_methods(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.common.stationinfo": "station_info.json",
            "/classes/com.korail.mobile.schedule.runDt": "train_calendar.json",
            "/classes/com.korail.mobile.common.code.do": "common_code_login_crypto_n.json",
        },
    )

    assert client.get_station_data().raw["stations"][0]["stnNm"] == "서울"
    assert client.get_station_info().raw["stationInfo"][0]["stnCd"] == "0001"
    assert client.get_train_calendar().raw["days"][0]["runDt"] == "20260710"
    assert client.get_common_code("login").raw["idx"] == "IDX-N"
    assert any(path == "/classes/com.korail.mobile.common.code.do" for _, path, _ in captured)


def test_search_trains_maps_rows(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.seatMovie.ScheduleView": "schedule_view_success.json"},
    )

    result = client.search_trains(
        TrainSearchQuery(
            departure_station_code="0001",
            arrival_station_code="0020",
            departure_date="20260710",
            departure_time="060000",
        )
    )

    assert result.response.h_msg_cd == "IRG000000"
    assert result.trains[0].train_no == "00123"
    posted_body = captured[0][2]
    assert "Sid=" in posted_body
    assert "txtGoStart=0001" in posted_body
    assert "txtGoEnd=0020" in posted_body


def test_history_and_ticket_list_are_read_only(load_json_fixture):
    client, _ = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.reservation.ReservationView": "reservation_history_empty.json",
            "/classes/com.korail.mobile.myTicket.MyTicketList": "ticket_list_empty.json",
        },
    )

    assert client.get_reservation_history().raw["reservations"] == []
    assert client.get_ticket_list().raw["tickets"] == []
