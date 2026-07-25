from __future__ import annotations

import inspect
from copy import deepcopy
from dataclasses import FrozenInstanceError, is_dataclass
from typing import Any, get_type_hints
from urllib.parse import parse_qs

import httpx
import pytest

import korail_mobile_api.models as models
import korail_mobile_api.parsers as parsers
from korail_mobile_api import KorailClient
from korail_mobile_api.errors import KorailProtocolError
from korail_mobile_api.models import BaseKorailResponse


def _partial_response(raw: dict[str, Any]) -> BaseKorailResponse:
    return BaseKorailResponse(raw=raw)


def _enveloped_response(raw: dict[str, Any]) -> BaseKorailResponse:
    return BaseKorailResponse.from_raw(raw)


def test_station_info_parser_and_normal_station_data_are_typed_and_repr_safe(
    load_json_fixture,
):
    info_raw = load_json_fixture("raw_typed_station_info.json")
    station_raw = load_json_fixture("raw_typed_station_data.json")

    info = parsers.parse_station_info_response(_partial_response(info_raw))
    response = parsers.parse_station_data_response(
        _partial_response(station_raw)
    )
    station = response.stations[0]

    assert isinstance(info, models.StationInfoResponse)
    assert info.count == 42
    assert info.map_version == "SYNTHETIC-MAP-VERSION"
    assert info.raw is info_raw
    assert isinstance(response, models.StationDataResponse)
    assert station.code == "SYNTHETIC-STATION-CODE"
    assert station.group == "SYNTHETIC-STATION-GROUP"
    assert station.major == "SYNTHETIC-MAJOR-FLAG"
    assert station.popup_type == 7
    assert station.popup_message == "synthetic-station-popup-message-secret"
    assert station.popup_link_title == "synthetic-station-popup-title-secret"
    assert station.popup_link_url.endswith("synthetic-station-url-secret")
    assert list(inspect.signature(models.KorailStation).parameters)[:5] == [
        "code",
        "name",
        "longitude",
        "latitude",
        "raw",
    ]
    rendered = f"{info!r} {response!r} {station!r}"
    for secret in (
        "synthetic-station-info-raw-secret",
        "synthetic-station-row-raw-secret",
        "synthetic-station-data-raw-secret",
        "synthetic-station-popup-message-secret",
        "synthetic-station-popup-title-secret",
        "synthetic-station-url-secret",
    ):
        assert secret not in rendered


def test_live_evidenced_ascii_decimal_station_and_delay_fields_are_normalized(
    load_json_fixture,
):
    station_raw = load_json_fixture("raw_typed_station_data.json")
    station_raw["stns"]["stn"][0]["popupType"] = "7"
    station = parsers.parse_station_data_response(
        _partial_response(station_raw)
    ).stations[0]

    schedule_raw = load_json_fixture("raw_typed_train_schedule.json")
    schedule_raw["dlayList"][0]["actArvDlayTnum"] = "3"
    stop = parsers.parse_train_schedule_response(
        _enveloped_response(schedule_raw)
    ).stops[0]

    assert station.popup_type == 7
    assert stop.actual_arrival_delay_count == 3


@pytest.mark.parametrize("value", ["", "-1", "１", True, 1.5])
def test_live_evidenced_optional_integer_fields_still_reject_invalid_values(
    load_json_fixture,
    value,
):
    station_raw = load_json_fixture("raw_typed_station_data.json")
    station_raw["stns"]["stn"][0]["popupType"] = value
    with pytest.raises(KorailProtocolError):
        parsers.parse_station_data_response(_partial_response(station_raw))

    schedule_raw = load_json_fixture("raw_typed_train_schedule.json")
    schedule_raw["dlayList"][0]["actArvDlayTnum"] = value
    with pytest.raises(KorailProtocolError):
        parsers.parse_train_schedule_response(
            _enveloped_response(schedule_raw)
        )


@pytest.mark.parametrize("count", [None, True, -1, "-1", " 42", 4.2])
def test_station_info_parser_rejects_invalid_count(
    load_json_fixture,
    count,
):
    raw = load_json_fixture("raw_typed_station_info.json")
    raw["count"] = count

    with pytest.raises(KorailProtocolError):
        parsers.parse_station_info_response(_partial_response(raw))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("group", 1),
        ("major", False),
        ("popupType", "not-an-integer"),
        ("popupMessage", []),
        ("popupLinkTitle", {}),
        ("popupLinkUrl", 1),
    ],
)
def test_station_parser_rejects_wrong_optional_field_types(
    load_json_fixture,
    key,
    value,
):
    raw = load_json_fixture("raw_typed_station_data.json")
    raw["stns"]["stn"][0][key] = value

    with pytest.raises(KorailProtocolError):
        parsers.parse_station_data_response(_partial_response(raw))


def test_train_calendar_parser_maps_evidenced_day_shape(load_json_fixture):
    raw = load_json_fixture("raw_typed_train_calendar.json")

    response = parsers.parse_train_calendar_response(
        _enveloped_response(raw)
    )
    day = response.days[0]

    assert isinstance(response, models.TrainCalendarResponse)
    assert isinstance(day, models.TrainCalendarDay)
    assert response.raw is raw
    assert day.run_date == "SYNTHETIC-RUN-DATE"
    assert day.business_day_stage_code == "SYNTHETIC-BUSINESS-DAY-STAGE"
    assert day.sale_day_division_code == "SYNTHETIC-SALE-DAY-DIVISION"
    assert (
        day.a_train_operation_flag,
        day.d_train_operation_flag,
        day.g_train_operation_flag,
        day.o_train_operation_flag,
        day.s_train_operation_flag,
        day.v_train_operation_flag,
        day.x_train_operation_flag,
    ) == (
        "SYNTHETIC-A-TRAIN-FLAG",
        "SYNTHETIC-D-TRAIN-FLAG",
        "SYNTHETIC-G-TRAIN-FLAG",
        "SYNTHETIC-O-TRAIN-FLAG",
        "SYNTHETIC-S-TRAIN-FLAG",
        "SYNTHETIC-V-TRAIN-FLAG",
        "SYNTHETIC-X-TRAIN-FLAG",
    )
    assert "synthetic-calendar-row-raw-secret" not in repr(day)
    assert "synthetic-calendar-raw-secret" not in repr(response)


@pytest.mark.parametrize(
    "mutation",
    [
        # A present-but-non-list runningCalendar is a genuine shape violation
        # (Gson cannot deserialize an object into List<RunningCalendar>).
        lambda raw: raw.__setitem__("runningCalendar", {}),
        lambda raw: raw["runningCalendar"].__setitem__(0, []),
        # hldyDvCd stays required: isHoliday() calls hldyDvCd.isEmpty()
        # unguarded (TrainCalendarDao:60-62), so the app NPEs on null.
        lambda raw: raw["runningCalendar"][0].__setitem__("hldyDvCd", None),
        lambda raw: raw["runningCalendar"][0].pop("hldyDvCd"),
        lambda raw: raw["runningCalendar"][0].__setitem__("xTrnOpFlg", 1),
    ],
)
def test_train_calendar_parser_rejects_malformed_shape(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("raw_typed_train_calendar.json")
    mutation(raw)

    with pytest.raises(KorailProtocolError):
        parsers.parse_train_calendar_response(_enveloped_response(raw))


@pytest.mark.parametrize("absent_shape", ["null", "missing"])
def test_train_calendar_parser_accepts_absent_running_calendar(
    load_json_fixture,
    absent_shape,
):
    # makeAvailableDatesFactory null-guards the list on SUCC responses
    # (C0805e.java:124: isNull(list) || size<=0 -> log + return), and
    # getRunningCalendarList is a nullable List (TrainCalendarDao:101-103), so a
    # missing/null runningCalendar yields an empty calendar rather than raising.
    raw = load_json_fixture("raw_typed_train_calendar.json")
    if absent_shape == "null":
        raw["runningCalendar"] = None
    else:
        raw.pop("runningCalendar")

    response = parsers.parse_train_calendar_response(
        _enveloped_response(raw)
    )

    assert response.days == ()


@pytest.mark.parametrize("absent_shape", ["null", "missing"])
def test_train_calendar_parser_skips_but_keeps_null_run_date_rows(
    load_json_fixture,
    absent_shape,
):
    # runDt is nullable per row: getDateStr() returns the raw field, compareTo
    # null-guards it, and makeAvailableDatesFactory gates use behind
    # !TextUtils.isEmpty(dateStr) (C0805e.java:140,147), silently skipping
    # null-date rows. So a null/absent runDt must not abort the whole parse.
    raw = load_json_fixture("raw_typed_train_calendar.json")
    row = raw["runningCalendar"][0]
    if absent_shape == "null":
        row["runDt"] = None
    else:
        row.pop("runDt")

    response = parsers.parse_train_calendar_response(
        _enveloped_response(raw)
    )

    assert response.days[0].run_date is None
    # The rest of the row is still parsed (hldyDvCd stays required).
    assert response.days[0].holiday_division_code == "SYNTHETIC-HOLIDAY-DIVISION"


def test_train_calendar_parser_accepts_empty_running_calendar(
    load_json_fixture,
):
    # TrainCalendarDao.getRunningCalendarList (:101-103) tolerates an empty
    # calendar (a window with no bookable dates), so a SUCC response with an
    # empty runningCalendar must parse rather than raise.
    raw = load_json_fixture("raw_typed_train_calendar.json")
    raw["runningCalendar"] = []

    response = parsers.parse_train_calendar_response(
        _enveloped_response(raw)
    )

    assert response.days == ()


@pytest.mark.parametrize(
    "optional_key",
    [
        "bizDdStgCd",
        "dayDvCd",
        "saleDdDvCd",
        "aTrnOpFlg",
        "dTrnOpFlg",
        "gTrnOpFlg",
        "oTrnOpFlg",
        "sTrnOpFlg",
        "vTrnOpFlg",
        "xTrnOpFlg",
    ],
)
@pytest.mark.parametrize("absent_shape", ["null", "missing"])
def test_train_calendar_parser_tolerates_app_nullable_fields(
    load_json_fixture,
    optional_key,
    absent_shape,
):
    # The DAO treats these fields as nullable (isPeakSeason null-guards
    # bizDdStgCd; dayDvCd has no accessor; the *TrnOpFlg accessors and
    # isForSaleDate are null-safe — TrainCalendarDao:44-82), so an
    # app-conformant SUCC response that omits or nulls them must still parse.
    raw = load_json_fixture("raw_typed_train_calendar.json")
    row = raw["runningCalendar"][0]
    if absent_shape == "null":
        row[optional_key] = None
    else:
        row.pop(optional_key)

    response = parsers.parse_train_calendar_response(
        _enveloped_response(raw)
    )
    day = response.days[0]

    field_name = {
        "bizDdStgCd": "business_day_stage_code",
        "dayDvCd": "day_division_code",
        "saleDdDvCd": "sale_day_division_code",
        "aTrnOpFlg": "a_train_operation_flag",
        "dTrnOpFlg": "d_train_operation_flag",
        "gTrnOpFlg": "g_train_operation_flag",
        "oTrnOpFlg": "o_train_operation_flag",
        "sTrnOpFlg": "s_train_operation_flag",
        "vTrnOpFlg": "v_train_operation_flag",
        "xTrnOpFlg": "x_train_operation_flag",
    }[optional_key]
    assert getattr(day, field_name) is None
    # hldyDvCd stays required; runDt is optional but present here.
    assert day.run_date == "SYNTHETIC-RUN-DATE"
    assert day.holiday_division_code == "SYNTHETIC-HOLIDAY-DIVISION"


def test_train_schedule_parser_maps_header_and_stop_repr_safely(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_train_schedule.json")

    response = parsers.parse_train_schedule_response(
        _enveloped_response(raw)
    )
    stop = response.stops[0]

    assert isinstance(response, models.TrainScheduleResponse)
    assert isinstance(stop, models.TrainScheduleStop)
    assert response.run_date == "SYNTHETIC-SCHEDULE-RUN-DATE"
    assert response.run_segment_order == "SYNTHETIC-RUN-SEGMENT-ORDER"
    assert response.delay_station_construction_order == (
        "SYNTHETIC-DELAY-STATION-CONSTRUCTION-ORDER"
    )
    assert response.integrated_message_code == (
        "SYNTHETIC-INTEGRATED-MESSAGE-CODE"
    )
    assert response.message_code == "SYNTHETIC-SCHEDULE-MESSAGE-CODE"
    assert response.origin_station_code == "SYNTHETIC-ORIGIN-STATION-CODE"
    assert response.origin_station_name == "Synthetic Origin Station Name"
    assert response.route_code == "SYNTHETIC-ROUTE-CODE"
    assert response.route_name == "Synthetic Route Name"
    assert response.regular_sale_flag == "SYNTHETIC-REGULAR-SALE-FLAG"
    assert response.standard_train_class_code == (
        "SYNTHETIC-STANDARD-TRAIN-CLASS-CODE"
    )
    assert response.terminal_station_code == (
        "SYNTHETIC-TERMINAL-STATION-CODE"
    )
    assert response.terminal_station_name == "Synthetic Terminal Station Name"
    assert response.train_attribute_code == (
        "SYNTHETIC-TRAIN-ATTRIBUTE-CODE"
    )
    assert response.train_departure_flag == "SYNTHETIC-TRAIN-DEPARTURE-FLAG"
    assert response.train_no == "SYNTHETIC-SCHEDULE-TRAIN-NO"
    assert response.special_train_flag == "SYNTHETIC-SPECIAL-TRAIN-FLAG"
    assert response.up_down_division_code == (
        "SYNTHETIC-UP-DOWN-DIVISION-CODE"
    )
    assert stop.station_code == "SYNTHETIC-STOP-STATION-CODE"
    assert stop.station_construction_order == (
        "SYNTHETIC-STATION-CONSTRUCTION-ORDER"
    )
    assert stop.run_order == "SYNTHETIC-STOP-RUN-ORDER"
    assert stop.actual_arrival_delay_count == 3
    assert stop.delay_fare_return_division_code == (
        "SYNTHETIC-DELAY-FARE-RETURN-CODE"
    )
    assert stop.delay_fare_return_division_name == (
        "synthetic-delay-fare-return-name-secret"
    )
    assert stop.solo_operation_delay_flag == (
        "SYNTHETIC-SOLO-OPERATION-FLAG"
    )
    assert stop.detour_driver_delay_count == (
        "SYNTHETIC-DETOUR-DRIVER-DELAY-COUNT"
    )
    assert stop.regular_flag == "SYNTHETIC-REGULAR-FLAG"
    assert stop.service_flag == "SYNTHETIC-SERVICE-FLAG"
    assert response.raw is raw
    rendered = f"{response!r} {stop!r}"
    for secret in (
        "synthetic-schedule-envelope-message-secret",
        "synthetic-delay-detail-secret",
        "synthetic-schedule-message-secret",
        "synthetic-schedule-message-text-secret",
        "synthetic-delay-fare-return-name-secret",
        "SYNTHETIC-SCHEDULE-RUN-DATE",
        "SYNTHETIC-SCHEDULE-TRAIN-NO",
        "SYNTHETIC-STOP-STATION-CODE",
        "Synthetic Stop Station Name",
        "synthetic-schedule-stop-raw-secret",
        "synthetic-schedule-raw-secret",
    ):
        assert secret not in rendered


def test_train_schedule_parser_accepts_app_model_conformant_response(
    load_json_fixture,
):
    # The app's TrainScheduleDao.TimeInfo model declares only stopStnNm among
    # the station fields (no stopRsStnCd/stnConsOrdr/runOrdr), so an
    # app-conformant SUCC response omits those three keys entirely.
    raw = load_json_fixture("raw_typed_train_schedule_app_model.json")

    response = parsers.parse_train_schedule_response(_enveloped_response(raw))
    stop = response.stops[0]

    assert isinstance(response, models.TrainScheduleResponse)
    assert isinstance(stop, models.TrainScheduleStop)
    assert response.run_date == "APP-MODEL-SCHEDULE-RUN-DATE"
    assert response.train_no == "APP-MODEL-SCHEDULE-TRAIN-NO"
    assert stop.station_name == "App Model Stop Station Name"
    # Downgraded to optional -> omitted keys parse to None instead of raising.
    assert stop.station_code is None
    assert stop.station_construction_order is None
    assert stop.run_order is None
    assert stop.actual_arrival_delay_count == 0
    assert stop.regular_flag == "APP-MODEL-REGULAR-FLAG"
    assert stop.service_flag == "APP-MODEL-SERVICE-FLAG"

    # An empty delay list (empty schedule) is valid and must not raise.
    raw["dlayList"] = []
    empty = parsers.parse_train_schedule_response(_enveloped_response(raw))
    assert empty.stops == ()
    assert empty.run_date == "APP-MODEL-SCHEDULE-RUN-DATE"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("dlayList"),
        lambda raw: raw.__setitem__("dlayList", {}),
        lambda raw: raw["dlayList"].__setitem__(0, []),
        lambda raw: raw["dlayList"][0].pop("stopStnNm"),
        lambda raw: raw["dlayList"][0].__setitem__(
            "actArvDlayTnum", True
        ),
        lambda raw: raw.pop("runDt1"),
        lambda raw: raw.__setitem__("msgCont", []),
    ],
)
def test_train_schedule_parser_rejects_malformed_shape(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("raw_typed_train_schedule.json")
    mutation(raw)

    with pytest.raises(KorailProtocolError):
        parsers.parse_train_schedule_response(_enveloped_response(raw))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("trnNo1"),
        lambda raw: raw.__setitem__("trnNo1", None),
    ],
)
def test_train_schedule_parser_tolerates_null_train_no(
    load_json_fixture,
    mutation,
):
    # RV4-04: trnNo1 is a nullable Gson String and the web-view consumer
    # null-guards it (TrainServiceInfoWebViewActivity.java:200), so a null train
    # number parses (train_no is None) instead of failing the whole response.
    raw = load_json_fixture("raw_typed_train_schedule.json")
    mutation(raw)
    parsed = parsers.parse_train_schedule_response(_enveloped_response(raw))
    assert parsed.train_no is None


def test_transfer_station_parser_maps_evidenced_rows_repr_safely(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_transfer_stations.json")

    response = parsers.parse_transfer_station_list_response(
        _enveloped_response(raw)
    )
    station = response.stations[0]

    assert isinstance(response, models.TransferStationListResponse)
    assert isinstance(station, models.TransferStation)
    assert station.station_code == "SYNTHETIC-TRANSFER-STATION-CODE"
    assert station.station_name == "Synthetic Transfer Station Name"
    assert response.raw is raw
    rendered = f"{response!r} {station!r}"
    for secret in (
        "SYNTHETIC-TRANSFER-STATION-CODE",
        "synthetic-transfer-row-raw-secret",
        "synthetic-transfer-raw-secret",
    ):
        assert secret not in rendered


def test_transfer_station_parser_accepts_present_empty_list(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_transfer_stations.json")
    raw["chtnList"] = []

    response = parsers.parse_transfer_station_list_response(
        _enveloped_response(raw)
    )

    assert response.stations == ()
    assert response.raw is raw


@pytest.mark.parametrize(
    "mutation",
    [
        lambda raw: raw.pop("chtnList"),
        lambda raw: raw.__setitem__("chtnList", {}),
        lambda raw: raw["chtnList"].__setitem__(0, []),
        lambda raw: raw["chtnList"][0].pop("chtnRsStnCd"),
        lambda raw: raw["chtnList"][0].__setitem__("chtnRsStnNm", 1),
    ],
)
def test_transfer_station_parser_rejects_malformed_shape(
    load_json_fixture,
    mutation,
):
    raw = load_json_fixture("raw_typed_transfer_stations.json")
    mutation(raw)

    with pytest.raises(KorailProtocolError):
        parsers.parse_transfer_station_list_response(
            _enveloped_response(raw)
        )


def test_existing_reference_methods_return_typed_models_without_request_changes(
    load_json_fixture,
):
    fixtures = {
        "/classes/com.korail.mobile.common.stationinfo": (
            "raw_typed_station_info.json"
        ),
        "/classes/com.korail.mobile.common.stationdata": (
            "raw_typed_station_data.json"
        ),
        "/classes/com.korail.mobile.schedule.runDt": (
            "raw_typed_train_calendar.json"
        ),
        "/classes/com.korail.mobile.research.actualTrainSchedule.do": (
            "raw_typed_train_schedule.json"
        ),
        "/classes/com.korail.mobile.qry.chtnStn.do": (
            "raw_typed_transfer_stations.json"
        ),
    }
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json=load_json_fixture(fixtures[request.url.path]),
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        results = (
            client.get_station_info(),
            client.get_station_data(),
            client.get_train_calendar(),
            client.get_train_schedule("SYNTHETIC-DATE", "123"),
            client.get_transfer_stations(
                "SYNTHETIC-DEPARTURE-CODE",
                "SYNTHETIC-ARRIVAL-CODE",
            ),
        )
    finally:
        client.close()

    assert tuple(type(result) for result in results) == (
        models.StationInfoResponse,
        models.StationDataResponse,
        models.TrainCalendarResponse,
        models.TrainScheduleResponse,
        models.TransferStationListResponse,
    )
    assert [request.method for request in captured] == [
        "GET",
        "GET",
        "GET",
        "POST",
        "POST",
    ]
    assert captured[0].url.query.decode() == "Device=AD"
    assert captured[1].url.query == b""
    assert captured[2].url.query == b""
    assert parse_qs(captured[3].content.decode()) == {
        "Device": ["AD"],
        "Version": ["250601003"],
        "runDt": ["SYNTHETIC-DATE"],
        "trnNo": ["00123"],
    }
    assert parse_qs(captured[4].content.decode()) == {
        "Device": ["AD"],
        "Version": ["250601003"],
        "Key": ["korail1234567890"],
        "dptRsStnCd": ["SYNTHETIC-DEPARTURE-CODE"],
        "arvRsStnCd": ["SYNTHETIC-ARRIVAL-CODE"],
    }


def test_typed_reference_models_are_frozen_dataclasses():
    instances = (
        models.StationInfoResponse(),
        models.TrainCalendarDay(),
        models.TrainCalendarResponse(),
        models.TrainScheduleStop(),
        models.TrainScheduleResponse(),
        models.TransferStation(),
        models.TransferStationListResponse(),
    )
    for instance in instances:
        assert is_dataclass(instance)
        with pytest.raises(FrozenInstanceError):
            instance.raw = {}


def test_train_rows_reject_mixed_object_and_non_object_rows(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_train_search.json")
    raw["trn_infos"]["trn_info"].append("SYNTHETIC-NON-OBJECT-ROW")

    with pytest.raises(KorailProtocolError, match="non-object row"):
        parsers.parse_train_rows(raw)


def test_train_search_metadata_preserves_named_server_strings_repr_safely(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_train_search.json")

    metadata = parsers.parse_train_search_metadata(raw)

    assert isinstance(metadata, models.TrainSearchMetadata)
    # No menu_id: h_menu_id is not a wire key (zero hits in the app);
    # txtMenuId is the client constant "11" (a5/k.java:92-94).
    assert not hasattr(metadata, "menu_id")
    assert metadata.job_id == "SYNTHETIC-JOB-ID"
    assert metadata.product_no == "SYNTHETIC-PRODUCT-NO"
    assert metadata.next_page_flag == "SYNTHETIC-NEXT-PAGE-FLAG"
    assert metadata.next_query_station_no == (
        "SYNTHETIC-NEXT-QUERY-STATION-NO"
    )
    assert metadata.next_train_no == "SYNTHETIC-NEXT-TRAIN-NO"
    assert metadata.result_count == "SYNTHETIC-RESULT-COUNT"
    assert metadata.first_seat_count == "SYNTHETIC-FIRST-SEAT-COUNT"
    assert metadata.second_seat_count == "SYNTHETIC-SECOND-SEAT-COUNT"
    assert metadata.first_departure_time == (
        "SYNTHETIC-FIRST-DEPARTURE-TIME"
    )
    assert metadata.merge_reservation_available_flag == (
        "SYNTHETIC-MERGE-AVAILABILITY-FLAG"
    )
    rendered = repr(metadata)
    for secret in (
        "SYNTHETIC-MENU-ID",
        "SYNTHETIC-JOB-ID",
        "SYNTHETIC-PRODUCT-NO",
        "SYNTHETIC-NEXT-QUERY-STATION-NO",
        "SYNTHETIC-NEXT-TRAIN-NO",
        "SYNTHETIC-FIRST-DEPARTURE-TIME",
        "synthetic-train-search-raw-secret",
    ):
        assert secret not in rendered


def test_train_summary_promotes_safe_follow_on_fields_losslessly(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_train_search.json")
    row = raw["trn_infos"]["trn_info"][0]

    train = models.TrainSummary.from_raw(row)

    assert train.departure_construction_order == (
        "SYNTHETIC-DEPARTURE-CONSTRUCTION-ORDER"
    )
    assert train.arrival_construction_order == (
        "SYNTHETIC-ARRIVAL-CONSTRUCTION-ORDER"
    )
    assert train.seat_attribute_code == "SYNTHETIC-SEAT-ATTRIBUTE-CODE"
    assert train.car_type_code == "SYNTHETIC-CAR-TYPE-CODE"
    assert train.car_type_name == "Synthetic Car Type Name"
    assert train.train_class_name == "Synthetic Train Class Name"
    assert train.train_group_name == "Synthetic Train Group Name"
    assert train.general_room_class_name == "Synthetic General Room Name"
    assert train.special_room_class_name == "Synthetic Special Room Name"
    assert train.secondary_general_reservation_code == (
        "SYNTHETIC-SECONDARY-GENERAL-RESERVATION-CODE"
    )
    assert train.special_reservation_code is None
    assert train.secondary_special_reservation_code == (
        "SYNTHETIC-SECONDARY-SPECIAL-RESERVATION-CODE"
    )
    assert train.free_reservation_code == "SYNTHETIC-FREE-RESERVATION-CODE"
    assert train.standing_reservation_code == (
        "SYNTHETIC-STANDING-RESERVATION-CODE"
    )
    assert train.general_availability_name == (
        "synthetic-general-availability-name-secret"
    )
    assert train.special_availability_name == (
        "synthetic-special-availability-name-secret"
    )
    assert train.wait_reservation_flag == (
        "SYNTHETIC-WAIT-RESERVATION-FLAG"
    )
    assert train.standard_remaining_seat_count == (
        "SYNTHETIC-STANDARD-REMAINING-SEAT-COUNT"
    )
    assert train.first_class_remaining_seat_count == (
        "SYNTHETIC-FIRST-CLASS-REMAINING-SEAT-COUNT"
    )
    assert train.free_car_count == "SYNTHETIC-FREE-CAR-COUNT"
    assert train.reservation_wait_passenger_count == (
        "SYNTHETIC-RESERVATION-WAIT-PASSENGER-COUNT"
    )
    assert train.total_passenger_count == 4
    assert train.raw is row
    rendered = repr(train)
    for secret in (
        "SYNTHETIC-DEPARTURE-CONSTRUCTION-ORDER",
        "SYNTHETIC-SEAT-ATTRIBUTE-CODE",
        "SYNTHETIC-CAR-TYPE-CODE",
        "synthetic-general-availability-name-secret",
        "SYNTHETIC-STANDARD-REMAINING-SEAT-COUNT",
        "synthetic-train-row-raw-secret",
    ):
        assert secret not in rendered


def test_train_search_extensions_preserve_legacy_constructor_positions():
    assert list(inspect.signature(models.TrainSummary).parameters)[:8] == [
        "train_no",
        "train_group_code",
        "departure_station_code",
        "arrival_station_code",
        "departure_date",
        "departure_time",
        "arrival_time",
        "raw",
    ]
    assert list(inspect.signature(models.TrainSearchResult).parameters)[:3] == [
        "trains",
        "response",
        "raw",
    ]
    assert list(inspect.signature(models.TrainSearchResult).parameters)[-1] == (
        "metadata"
    )


@pytest.mark.parametrize(
    "key",
    [
        "h_std_rest_seat_cnt",
        "h_fst_rest_seat_cnt",
        "h_free_sracar_cnt",
        "h_rsv_wait_ps_cnt",
        "h_spe_rsv_cd",
    ],
)
def test_train_summary_rejects_non_string_server_fields(
    load_json_fixture,
    key,
):
    raw = load_json_fixture("raw_typed_train_search.json")
    row = raw["trn_infos"]["trn_info"][0]
    row[key] = 1

    with pytest.raises(KorailProtocolError):
        models.TrainSummary.from_raw(row)


@pytest.mark.parametrize(
    "key",
    [
        "strJobId",
        "h_gd_no",
        "h_next_pg_flg",
        "h_qry_st_no_next",
        "h_trn_no_next",
        "h_rslt_cnt",
        "h_seat_cnt_first",
        "h_seat_cnt_second",
        "txtGoHour_first",
    ],
)
def test_train_search_metadata_rejects_non_string_fields(
    load_json_fixture,
    key,
):
    raw = load_json_fixture("raw_typed_train_search.json")
    raw[key] = False

    with pytest.raises(KorailProtocolError):
        parsers.parse_train_search_metadata(raw)


def test_train_search_metadata_rejects_non_string_merge_flag(
    load_json_fixture,
):
    raw = load_json_fixture("raw_typed_train_search.json")
    raw["trn_infos"]["h_merge_rsv_psb_flg"] = 1

    with pytest.raises(KorailProtocolError):
        parsers.parse_train_search_metadata(raw)


def test_search_trains_populates_metadata_without_changing_request(
    load_json_fixture,
):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            200,
            json=load_json_fixture("raw_typed_train_search.json"),
        )

    client = KorailClient(transport=httpx.MockTransport(handler))
    try:
        result = client.search_trains(
            models.TrainSearchQuery(
                "Synthetic Departure Name",
                "Synthetic Arrival Name",
                "SYNTHETIC-DATE",
            )
        )
    finally:
        client.close()

    assert isinstance(result.metadata, models.TrainSearchMetadata)
    assert not hasattr(result.metadata, "menu_id")
    assert result.trains[0].seat_attribute_code == (
        "SYNTHETIC-SEAT-ATTRIBUTE-CODE"
    )
    assert result.raw is result.response.raw
    assert len(captured) == 1
    assert captured[0].method == "POST"
    assert captured[0].url.path == (
        "/classes/com.korail.mobile.seatMovie.ScheduleView"
    )
    form = parse_qs(captured[0].content.decode())
    assert form["txtGoStart"] == ["Synthetic Departure Name"]
    assert form["txtGoEnd"] == ["Synthetic Arrival Name"]
    assert "Key" not in form
