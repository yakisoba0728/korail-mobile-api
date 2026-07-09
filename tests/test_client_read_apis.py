import httpx

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.models import TrainSearchQuery


def make_client(load_json_fixture, paths):
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(
            {
                "method": request.method,
                "path": request.url.path,
                "query": request.url.query.decode(),
                "body": request.content.decode(),
            }
        )
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
    station_data_request = captured[0]
    station_info_request = captured[1]
    train_calendar_request = captured[2]
    common_code_request = captured[3]
    assert "Device=AD" in station_data_request["query"]
    assert "Version=250601003" in station_data_request["query"]
    assert "Key=korail1234567890" in station_data_request["query"]
    assert "Device=AD" in station_info_request["query"]
    assert "Version=250601003" in station_info_request["query"]
    assert "Key=korail1234567890" in station_info_request["query"]
    assert "Device=AD" in train_calendar_request["query"]
    assert "Version=250601003" in train_calendar_request["query"]
    assert "Key=korail1234567890" in train_calendar_request["query"]
    assert common_code_request["path"] == "/classes/com.korail.mobile.common.code.do"


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
    posted_body = captured[0]["body"]
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


def test_train_schedule_request_shape(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.research.actualTrainSchedule.do": "train_schedule_success.json"},
    )

    response = client.get_train_schedule("20260710", "00123")

    assert response.raw["stops"][0]["trnNo"] == "00123"
    request = captured[0]
    assert request["query"] == ""
    assert "runDt=20260710" in request["body"]
    assert "trnNo=00123" in request["body"]
    assert "Device=" not in request["body"]
    assert "Version=" not in request["body"]
    assert "Key=" not in request["body"]


def test_transfer_stations_request_shape(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {"/classes/com.korail.mobile.qry.chtnStn.do": "transfer_stations_success.json"},
    )

    response = client.get_transfer_stations("0001", "0020")

    assert response.raw["stations"][0]["dptRsStnCd"] == "0001"
    request = captured[0]
    assert "dptRsStnCd=0001" in request["body"]
    assert "arvRsStnCd=0020" in request["body"]
