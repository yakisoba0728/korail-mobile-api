import httpx
import pytest
from urllib.parse import parse_qs

from korail_mobile_api import KorailClient, KorailConfig
from korail_mobile_api.errors import KorailAppError, KorailSessionExpiredError
from korail_mobile_api.models import KorailSession, TrainSearchQuery


def make_client(
    load_json_fixture,
    paths,
    *,
    config: KorailConfig | None = None,
):
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

    return (
        KorailClient(
            config or KorailConfig(),
            transport=httpx.MockTransport(handler),
        ),
        captured,
    )


def client_returning_failure_for(path: str, *, code: str = "ERR") -> KorailClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path != path:
            raise AssertionError(f"unexpected path {request.url.path}")
        return httpx.Response(
            200,
            json={
                "h_msg_cd": code,
                "h_msg_txt": "request failed",
                "strResult": "FAIL",
            },
        )

    return KorailClient(
        KorailConfig(),
        transport=httpx.MockTransport(handler),
    )


def test_common_station_and_calendar_use_exact_endpoint_fields(
    load_json_fixture,
):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.code.do": "common_code_login_crypto_n.json",
            "/classes/com.korail.mobile.common.stationinfo": "station_info.json",
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.schedule.runDt": (
                "raw_typed_train_calendar.json"
            ),
        },
    )
    client.get_common_code("login")
    client.get_station_info()
    client.get_station_data()
    client.get_train_calendar()
    common_body = parse_qs(captured[0]["body"])
    assert common_body["Device"] == ["AD"]
    assert common_body["Version"] == ["250601003"]
    assert common_body["Key"] == ["korail1234567890"]
    assert common_body["deviceWidth"] == ["1080"]
    assert common_body["deviceHeight"] == ["2400"]
    assert common_body["OSVersion"] == ["35"]
    assert captured[1]["query"] == "Device=AD"
    assert captured[2]["query"] == ""
    assert captured[3]["query"] == ""


def test_search_resolves_codes_to_names_and_parses_nested_rows(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.common.stationdata": "station_data.json",
            "/classes/com.korail.mobile.seatMovie.ScheduleView": (
                "schedule_view_success.json"
            ),
        },
    )
    result = client.search_trains(
        TrainSearchQuery("0001", "0020", "20260710", departure_time="060000")
    )
    search_request = captured[1]
    assert "txtGoStart=%EC%84%9C%EC%9A%B8" in search_request["body"]
    assert "txtGoEnd=%EB%B6%80%EC%82%B0" in search_request["body"]
    assert "Device=AD" in search_request["body"]
    assert "Version=250601003" in search_request["body"]
    assert "Key=" not in search_request["body"]
    assert result.trains[0].train_no == "00123"
    assert result.trains[0].departure_station_name == "서울"


def test_search_accepts_names_without_station_catalog_request(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.seatMovie.ScheduleView": (
                "schedule_view_success.json"
            )
        },
    )
    client.search_trains(TrainSearchQuery("서울", "부산", "20260710"))
    assert [request["path"] for request in captured] == [
        "/classes/com.korail.mobile.seatMovie.ScheduleView"
    ]


def test_ticket_list_sends_complete_member_form(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.myTicket.MyTicketList": "ticket_list_empty.json",
        },
        config=KorailConfig(advertising_id="ad-id"),
    )
    client.session.current = KorailSession(
        jsessionid="session",
        member_no="member",
    )
    client.get_ticket_list()
    body = captured[0]["body"]
    for expected in (
        "txtDeviceId=ad-id",
        "txtIndex=1",
        "h_page_no=1",
        "h_abrd_dt_from=",
        "h_abrd_dt_to=",
        "hiduserYn=Y",
    ):
        assert expected in body
    for nonmember_only in ("hidName", "hidTeleNo", "hidPwd", "tsRsStnCd"):
        assert nonmember_only not in body


def test_ticket_list_defaults_to_empty_device_id(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.myTicket.MyTicketList": (
                "ticket_list_empty.json"
            ),
        },
    )
    client.session.current = KorailSession(
        jsessionid="session",
        member_no="member",
    )

    client.get_ticket_list()

    assert "txtDeviceId=" in captured[0]["body"]


def _ticket_client(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.myTicket.MyTicketList": (
                "ticket_list_empty.json"
            ),
        },
        config=KorailConfig(advertising_id="ad-id"),
    )
    client.session.current = KorailSession(
        jsessionid="session",
        member_no="member",
    )
    return client, captured


def test_ticket_list_txtindex_is_active_mode_and_page_rides_h_page_no(
    load_json_fixture,
):
    # RV3-03: txtIndex is the active/history mode selector (TicketListActivity
    # sends "1"), NOT a page cursor; the page rides h_page_no.
    client, captured = _ticket_client(load_json_fixture)
    client.get_ticket_list(3)
    body = parse_qs(captured[0]["body"], keep_blank_values=True)
    assert body["txtIndex"] == ["1"]
    assert body["h_page_no"] == ["3"]
    assert body["h_abrd_dt_from"] == [""]
    assert body["h_abrd_dt_to"] == [""]


def test_ticket_list_history_mode_sends_txtindex_two_with_date_bounds(
    load_json_fixture,
):
    # RV3-03: purchase-history mode is txtIndex="2" plus the boarding-date
    # bounds (TicketPurchaseHistoryActivity.java:276-278).
    client, captured = _ticket_client(load_json_fixture)
    client.get_ticket_list(
        mode="2",
        boarding_date_from="20260101",
        boarding_date_to="20260131",
    )
    body = parse_qs(captured[0]["body"], keep_blank_values=True)
    assert body["txtIndex"] == ["2"]
    assert body["h_page_no"] == ["1"]
    assert body["h_abrd_dt_from"] == ["20260101"]
    assert body["h_abrd_dt_to"] == ["20260131"]


def test_ticket_list_rejects_unknown_mode(load_json_fixture):
    from korail_mobile_api.errors import KorailProtocolError

    client, _ = _ticket_client(load_json_fixture)
    with pytest.raises(KorailProtocolError, match="mode"):
        client.get_ticket_list(mode="3")


def test_train_search_couples_ebiz_cross_check_to_include_srt():
    # RV3-01: MainBookingActivity.java:775-776 sets ebizCrossCheck and
    # srtCheckYn from the single "include SRT" checkbox, so they are always
    # equal; the phantom N/Y pair the app never produces must not appear.
    from korail_mobile_api.payloads import build_train_search_form

    config = KorailConfig()
    off = build_train_search_form(
        config,
        TrainSearchQuery("서울", "부산", "20260710"),
        departure_name="서울",
        arrival_name="부산",
        sid="sid",
    )
    on = build_train_search_form(
        config,
        TrainSearchQuery("서울", "부산", "20260710", include_srt=True),
        departure_name="서울",
        arrival_name="부산",
        sid="sid",
    )
    assert off["ebizCrossCheck"] == off["srtCheckYn"] == "N"
    assert on["ebizCrossCheck"] == on["srtCheckYn"] == "Y"


def test_train_search_always_sends_the_apps_paging_block():
    # b5/c.java:145-147 calls setQryDvCd("1"),
    # setSelectTransferPage("0", "10") and setSelectTransferPages("00000", "")
    # unconditionally on every search; RsvInquiryRequest.java:207-215 maps them
    # onto qryStNo/pgPrCnt and qryStTrnNo/qryStTrnNo2, and all five are declared
    # on SeatMovieService.java:14. They are not transfer-only extras.
    from korail_mobile_api.payloads import build_train_search_form

    form = build_train_search_form(
        KorailConfig(),
        TrainSearchQuery("서울", "부산", "20260710"),
        departure_name="서울",
        arrival_name="부산",
        sid="sid",
        member_card_no="SYNTHETIC-CARD",
    )
    assert form["qryDvCd"] == "1"
    assert form["qryStNo"] == "0"
    assert form["qryStTrnNo"] == "00000"
    assert form["qryStTrnNo2"] == ""
    assert form["pgPrCnt"] == "10"
    # SeatMovieService.java:14 declares ... adjStnScdlOfrFlg, mbCrdNo, ...,
    # qryDvCd, qryStNo, qryStTrnNo, qryStTrnNo2, pgPrCnt.
    names = list(form)
    assert names[names.index("adjStnScdlOfrFlg") :] == [
        "adjStnScdlOfrFlg",
        "mbCrdNo",
        "qryDvCd",
        "qryStNo",
        "qryStTrnNo",
        "qryStTrnNo2",
        "pgPrCnt",
    ]


def test_train_search_continuation_replays_the_previous_pages_cursor():
    from korail_mobile_api import TrainSearchContinuation
    from korail_mobile_api.payloads import build_train_search_form

    form = build_train_search_form(
        KorailConfig(),
        TrainSearchQuery("서울", "부산", "20260710"),
        departure_name="서울",
        arrival_name="부산",
        sid="sid",
        continuation=TrainSearchContinuation(
            query_station_no="SYNTHETIC-QRY-ST-NO",
            query_train_no="SYNTHETIC-TRN-NO",
            page_count="SYNTHETIC-RSLT-CNT",
        ),
    )
    # setNextTimeTC(h_qry_st_no_next, h_trn_no_next) then
    # setSelectTransferPage(h_qry_st_no_next, h_rslt_cnt) -- b5/c.java:184-191.
    assert form["qryDvCd"] == "1"
    assert form["qryStNo"] == "SYNTHETIC-QRY-ST-NO"
    assert form["qryStTrnNo"] == "SYNTHETIC-TRN-NO"
    assert form["pgPrCnt"] == "SYNTHETIC-RSLT-CNT"
    # setSelectTransferPages needs BOTH transfer cursors non-empty
    # (b5/c.java:192), which a direct search never has.
    assert form["qryStTrnNo2"] == ""


def test_train_search_continuation_must_be_the_exact_type():
    from korail_mobile_api.errors import KorailProtocolError
    from korail_mobile_api.payloads import build_train_search_form

    with pytest.raises(KorailProtocolError):
        build_train_search_form(
            KorailConfig(),
            TrainSearchQuery("서울", "부산", "20260710"),
            departure_name="서울",
            arrival_name="부산",
            sid="sid",
            continuation={"query_station_no": "1"},
        )


def test_train_search_result_yields_a_cursor_only_when_the_app_would_page():
    from korail_mobile_api import (
        BaseKorailResponse,
        TrainSearchContinuation,
        TrainSearchMetadata,
        TrainSearchResult,
    )

    def result(**metadata) -> TrainSearchResult:
        return TrainSearchResult(
            trains=[],
            response=BaseKorailResponse(),
            metadata=TrainSearchMetadata(**metadata),
        )

    complete = result(
        next_page_flag="Y",
        next_query_station_no="SYNTHETIC-QRY-ST-NO",
        next_train_no="SYNTHETIC-TRN-NO",
        result_count="SYNTHETIC-RSLT-CNT",
    )
    assert complete.next_page() == TrainSearchContinuation(
        query_station_no="SYNTHETIC-QRY-ST-NO",
        query_train_no="SYNTHETIC-TRN-NO",
        page_count="SYNTHETIC-RSLT-CNT",
    )
    # b5/c.java:381-387 stops paging as soon as h_next_pg_flg is not "Y".
    assert (
        result(
            next_page_flag="N",
            next_query_station_no="SYNTHETIC-QRY-ST-NO",
            next_train_no="SYNTHETIC-TRN-NO",
        ).next_page()
        is None
    )
    assert result().next_page() is None
    # A half-filled cursor would silently re-request page one.
    assert (
        result(
            next_page_flag="Y",
            next_query_station_no="SYNTHETIC-QRY-ST-NO",
        ).next_page()
        is None
    )


def test_search_trains_next_page_posts_the_cursor(load_json_fixture):
    from korail_mobile_api import TrainSearchContinuation

    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.seatMovie.ScheduleView": (
                "schedule_view_success.json"
            )
        },
    )
    first = client.search_trains(TrainSearchQuery("서울", "부산", "20260710"))
    assert "qryStNo=0" in captured[0]["body"]
    # This fixture carries no h_next_pg_flg, so the app would stop here.
    assert first.next_page() is None

    client.search_trains(
        TrainSearchQuery("서울", "부산", "20260710"),
        continuation=TrainSearchContinuation(
            query_station_no="12",
            query_train_no="00777",
            page_count="10",
        ),
    )
    body = parse_qs(captured[1]["body"])
    assert body["qryDvCd"] == ["1"]
    assert body["qryStNo"] == ["12"]
    assert body["qryStTrnNo"] == ["00777"]
    assert body["pgPrCnt"] == ["10"]


def test_train_schedule_sends_device_and_version_without_key(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.research.actualTrainSchedule.do": (
                "raw_typed_train_schedule.json"
            )
        },
    )

    client.get_train_schedule("20260710", "123")
    body = captured[0]["body"]
    assert "Device=AD" in body
    assert "Version=250601003" in body
    assert "Key=" not in body
    assert "trnNo=00123" in body


def test_transfer_stations_request_shape(load_json_fixture):
    client, captured = make_client(
        load_json_fixture,
        {
            "/classes/com.korail.mobile.qry.chtnStn.do": (
                "raw_typed_transfer_stations.json"
            )
        },
    )

    response = client.get_transfer_stations("0001", "0020")

    assert (
        response.stations[0].station_code
        == "SYNTHETIC-TRANSFER-STATION-CODE"
    )
    request = captured[0]
    assert "dptRsStnCd=0001" in request["body"]
    assert "arvRsStnCd=0020" in request["body"]


def test_public_read_method_raises_application_failure():
    client = client_returning_failure_for(
        "/classes/com.korail.mobile.schedule.runDt"
    )
    with pytest.raises(KorailAppError):
        client.get_train_calendar()


def test_session_expiry_clears_client_state_before_raising():
    client = client_returning_failure_for(
        "/classes/com.korail.mobile.schedule.runDt",
        code="P058",
    )
    client.session.current = KorailSession(
        jsessionid="stale",
        member_no="member",
    )
    client.http.cookies.set("JSESSIONID", "stale")
    with pytest.raises(KorailSessionExpiredError):
        client.get_train_calendar()
    assert client.session.current is None
    assert "JSESSIONID" not in client.http.cookies
