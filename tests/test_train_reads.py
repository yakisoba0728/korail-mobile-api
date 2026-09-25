"""F2 / 291e01c: offline train-read contracts; no credentials or captured payloads.

The literal forms below are independent of production builders. They freeze this
library's wire policy, NOT the plaintext of encrypted Android literals. See
REPORT.md for protected values and retained extra validation. Socket attempts fail.
Run: PYTHONPATH=src python -m pytest -q tests/test_train_reads.py
"""

from __future__ import annotations

import ast
import socket
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from urllib.parse import parse_qsl

import httpx
import pytest

from korail_mobile_api.client import KorailClient
from korail_mobile_api.config import KorailConfig
from korail_mobile_api.dynapath import DynapathConfig
from korail_mobile_api.errors import (
    KorailApiError,
    KorailAuthError,
    KorailProtocolError,
    KorailSessionExpiredError,
)
from korail_mobile_api.models import (
    KorailSession,
    TrainSearchContinuation,
    TrainSearchQuery,
    TrainSummary,
    TransferSearchResult,
)
from korail_mobile_api.read_payloads import (
    FreeSeatCarRequest,
    GuideSeatConditionRequest,
    MaasServiceDetailQuery,
    MergeSeatsInquiryRequest,
    PriceFareLeg,
    PriceFareQuoteRequest,
    TravelProductSearchQuery,
)

P = "/classes/com.korail.mobile."
DATE = "20300102"
COMMON = {"Device": "SYNTH-DEVICE", "Version": "SYNTH-VERSION", "lang": "SYNTH-LANG", "Key": "SYNTH-KEY"}
DEVICE = {k: v for k, v in COMMON.items() if k != "Key"}
ENVELOPE = {"strResult": "SUCC", "h_msg_cd": "API.I00000", "h_msg_txt": "synthetic"}
ROW = {
    "h_trn_no": "7",
    "h_trn_gp_cd": "101",
    "h_trn_clsf_cd": "00",
    "h_dpt_rs_stn_cd": "0001",
    "h_arv_rs_stn_cd": "0099",
    "h_dpt_rs_stn_nm": "SYNTH_DEP",
    "h_arv_rs_stn_nm": "SYNTH_ARR",
    "h_dpt_dt": DATE,
    "h_dpt_tm": "090000",
    "h_arv_tm": "110000",
    "h_run_dt": DATE,
    "h_dpt_stn_run_ordr": "1",
    "h_arv_stn_run_ordr": "3",
    "h_dpt_stn_cons_ordr": "1",
    "h_arv_stn_cons_ordr": "3",
    "h_seat_att_cd": "015",
    "h_gd_no": "SYNTH-G",
    "h_trn_seq": "A",
}
TRAIN = TrainSummary.from_raw(ROW)
QUERY = TrainSearchQuery("SYNTH_DEP", "SYNTH_ARR", DATE, "090000")
SEARCH_FORM = {
    **COMMON,
    "txtMenuId": "11",
    "radJobId": "1",
    "selGoTrain": "109",
    "txtTrnGpCd": "109",
    "txtGoStart": "SYNTH_DEP",
    "txtGoEnd": "SYNTH_ARR",
    "txtGoAbrdDt": DATE,
    "txtGoHour": "090000",
    "txtPsgFlg_1": "1",
    "txtPsgFlg_2": "0",
    "txtPsgFlg_3": "0",
    "txtPsgFlg_4": "0",
    "txtPsgFlg_5": "0",
    "txtSeatAttCd_2": "000",
    "txtSeatAttCd_3": "000",
    "txtSeatAttCd_4": "015",
    "ebizCrossCheck": "N",
    "srtCheckYn": "N",
    "rtYn": "N",
    "adjStnScdlOfrFlg": "N",
    "qryDvCd": "1",
}
CAR_FORM = {
    **COMMON,
    "txtMenuId": "11",
    "txtPsrmClCd": "1",
    "txtRunDt": DATE,
    "txtDptDt": DATE,
    "txtDptTm": "090000",
    "txtTrnClsfCd": "00",
    "txtTrnNo": "00007",
    "txtDptRsStnCd": "0001",
    "txtArvRsStnCd": "0099",
    "txtDptStnRunOrdr": "1",
    "txtArvStnRunOrdr": "3",
    "txtTrnGpCd": "101",
    "txtTotPsgCnt": "2",
    "txtSeatAttCd": "015",
    "txtGdNo": "SYNTH-G",
}
INVENTORY_FORM = {
    **COMMON,
    "trnClsfCd": "00",
    "trnGpCd": "101",
    "runDt": DATE,
    "trnNo": "00007",
    "srcarNo": "2",
    "psrmClCd": "1",
    "dptRsStnCd": "0001",
    "arvRsStnCd": "0099",
    "seatAttCd": "015",
    "dptStnRunOrdr": "1",
    "arvStnRunOrdr": "3",
    "totPsgCnt": "2",
    "gdNo": "SYNTH-G",
    "isArrow": "false",
}
SEAT = {
    "seat_no": "1A",
    "sale_psb_flg": "Y",
    "dir_seat_att_cd": "001",
    "rq_seat_att_cd": "015",
    "seat_spec": "SYNTH",
    "sqr_no": "1",
    "intg_msg_cd": "",
    "intg_msg": "",
    "etc_seat_att_cd": "000",
    "vz_msg_dv_cd": "V",
    "floor": "1",
}
INVENTORY = {
    **ENVELOPE,
    "layout_type": 1,
    "seat_ary_cd": "A",
    "scar_no": "2",
    "seatList": [SEAT],
    "windowList": [{"st_loc_rt": "0.25", "cls_loc_rt": "0.75"}],
    "seat_total_count": "1",
}
CARS = {
    **ENVELOPE,
    "h_trn_no": "00007",
    "h_scar_num": "1",
    "h_rcmd_srcar_no": "2",
    "srcar_infos": {
        "srcar_info": [
            {
                "h_srcar_no": "2",
                "h_rest_seat_cnt": "4",
                "h_seat_cnt": "10",
                "h_psrm_cl_nm": "SYNTH_ROOM",
                "seatAttInfos": [{"seatAttNm": "SYNTH", "seatAttCd": "015"}],
            }
        ]
    },
}
STATIONS = {
    "stns": {"stn": [{"stn_cd": "0001", "stn_nm": "SYNTH_DEP", "latitude": "37.1", "longitude": "128.1"}]}
}
SEARCH = {
    **ENVELOPE,
    "trn_infos": {"trn_info": [ROW]},
    "h_next_pg_flg": "Y",
    "h_qry_st_no_next": "9",
    "h_trn_no_next": "00008",
}
TRANSFER = {
    **SEARCH,
    "trn_infos": {"trn_info": [ROW, {**ROW, "h_trn_no": "8"}]},
    "h_prcd_trn_no_next": "00009",
    "h_ectb_trn_no_next": "00010",
}
APP = {
    "version": {"AMESSAGE": "SYNTH", "NEWDVERSION": "9", "CNTAURL": "https://example.invalid/store"},
    "notice": {"BbrdId": "1", "PtwtSqno": "2", "PtwtTtl": "SYNTH_TITLE", "PtwtCont": "SYNTH_BODY"},
    "railplus_cardinfo": "SYNTH_CARDINFO",
    "unknown": {"retained": True},
}
FREE_REQUEST = FreeSeatCarRequest(DATE, "7", "1", "3", "1", "3")
MERGE_REQUEST = MergeSeatsInquiryRequest(
    DATE + "090000", DATE + "090000", "7", "SYNTH_DEP", "SYNTH_ARR", "SYNTH_MID", "1", "015", 2
)
FARE_LEG = PriceFareLeg("0001", "0099", DATE, "00007", "015", "101", "00")
FARE_REQUEST = PriceFareQuoteRequest((FARE_LEG,))
FARE_FORM = {
    **COMMON,
    "txtMenuId": "11",
    "chtnDvCd": "1",
    "trnCnt": "1",
    "dptRsStnCd": "0001",
    "arvRsStnCd": "0099",
    "runDt": DATE,
    "trnNo": "00007",
    # PrcFareInItem.java:109 default (zero-length) sent because the joined columns bypass the empty filter
    # (NetworkService.java:9895-9902).
    "gdNo": "",
    "rqSeatAttCd": "015",
    "trnGpCd": "101",
    "stlbTrnClsfCd": "00",
}

# (public method, positional args, keyword args, route, exact form, response, parsed fields, local auth)
CASES = [
    (
        "search_trains",
        (QUERY,),
        {},
        P + "seatMovie.ScheduleView",
        SEARCH_FORM,
        SEARCH,
        {"trains.0.train_no": "7", "metadata.next_train_no": "00008"},
        False,
    ),
    (
        "search_transfer_trains",
        (QUERY,),
        {},
        P + "seatMovie.ScheduleView",
        {**SEARCH_FORM, "radJobId": "2"},
        TRANSFER,
        {"itineraries.0.first.train_no": "7", "itineraries.0.second.train_no": "8"},
        False,
    ),
    (
        "search_trains_with_transfer_fallback",
        (QUERY,),
        {},
        P + "seatMovie.ScheduleView",
        SEARCH_FORM,
        SEARCH,
        {"trains.0.train_no": "7"},
        False,
    ),
    (
        "get_train_schedule",
        (DATE, "7"),
        {},
        P + "research.actualTrainSchedule.do",
        {**DEVICE, "runDt": DATE, "trnNo": "00007"},
        {
            **ENVELOPE,
            "trnNo1": "00007",
            "runDt1": DATE,
            "dlayList": [
                {"stopRsStnCd": "0001", "stopStnNm": "SYNTH_DEP", "actArvDlayTnum": 2, "actDptTm": "090000"}
            ],
        },
        {"train_no": "00007", "stops.0.station_name": "SYNTH_DEP", "stops.0.actual_arrival_delay_count": "2"},
        False,
    ),
    (
        "get_transfer_stations",
        ("0001", "0099"),
        {},
        P + "qry.chtnStn.do",
        {**COMMON, "dptRsStnCd": "0001", "arvRsStnCd": "0099"},
        {**ENVELOPE, "chtnList": [{"chtnRsStnCd": "0050", "chtnRsStnNm": "SYNTH_MID"}]},
        {"stations.0.station_code": "0050"},
        False,
    ),
    (
        "get_train_calendar",
        (),
        {},
        P + "schedule.runDt",
        {**COMMON, "timeStamp": "1700000000000"},
        {**ENVELOPE, "runningCalendar": [{"runDt": DATE, "hldyDvCd": "N", "aTrnOpFlg": "Y"}]},
        {"days.0.run_date": DATE, "days.0.a_train_operation_flag": "Y"},
        False,
    ),
    (
        "get_seat_cars",
        (TRAIN,),
        {"passenger_count": 2},
        P + "research.TrainResearch",
        CAR_FORM,
        CARS,
        {"cars.0.car_no": 2, "cars.0.remaining_seat_count": 4, "cars.0.attributes.0.code": "015"},
        True,
    ),
    (
        "get_seat_inventory",
        (TRAIN, 2),
        {"passenger_count": 2},
        P + "research.TResidualSeatsResearch.do",
        INVENTORY_FORM,
        INVENTORY,
        {"layout_type": "1", "seats.0.seat_no": "1A", "windows.0.start_location_ratio": 0.25},
        True,
    ),
    (
        "get_free_seat_car_info",
        (FREE_REQUEST,),
        {},
        P + "trn.fresScar.do",
        {
            **COMMON,
            "runDt": DATE,
            "trnNo": "00007",
            "dptStnConsOrdr": "1",
            "arvStnConsOrdr": "3",
            "dptStnRunOrdr": "1",
            "arvStnRunOrdr": "3",
        },
        {**ENVELOPE, "fresTtl": "SYNTH", "fresScarNo": "2", "fresCont": "SYNTH_BODY"},
        {"car_no": "2", "title": "SYNTH"},
        False,
    ),
    (
        "get_guide_seat_condition",
        (GuideSeatConditionRequest("015"),),
        {},
        P + "reservation.guideSeatCnd.do",
        {**COMMON, "rqSeatAttCd": "015"},
        {"strResult": "FAIL", "h_msg_cd": "MRR800011", "h_msg_txt": "SYNTH_GUIDE", "timeStamp": 7},
        {"h_msg_cd": "MRR800011", "time_stamp": 7},
        False,
    ),
    (
        "get_merge_seats_inquiry",
        (MERGE_REQUEST,),
        {},
        P + "research.mergeSeatsC.do",
        {
            **COMMON,
            "abrdDt": DATE + "090000",
            "runDt": DATE + "090000",
            "trnNo": "00007",
            "dptRsStnNm": "SYNTH_DEP",
            "arvRsStnNm": "SYNTH_ARR",
            "psrmClCd": "1",
            "seatAttCd": "015",
            "totPsgNum": "2",
            "selRsStnNm": "SYNTH_MID",
        },
        {
            **ENVELOPE,
            "runDt": DATE,
            "midStnList": [{"rsStnCd": "0050", "rsStnNm": "SYNTH_MID", "runOrdr": "2"}],
            "trn_infos": {"h_merge_rsv_psb_flg": "Y", "trn_info": [ROW]},
        },
        {
            "intermediate_stations.0.code": "0050",
            "merge_reservation_possible_flag": "Y",
            "trains.0.train_no": "7",
        },
        False,
    ),
    (
        "get_price_fare_quote",
        (FARE_REQUEST,),
        {},
        P + "trn.prcFare.do",
        FARE_FORM,
        {
            **ENVELOPE,
            "prcList": [
                {
                    "jrnySqno": "1",
                    "psrmClNm": "SYNTH_ROOM",
                    "rcvdFare": "1000",
                    "rcvdPrc": "200",
                    "sumAmt": "1200",
                    "trnNo": "00007",
                }
            ],
        },
        {"fares.0.total_amount": "1200", "fares.0.train_no": "00007"},
        False,
    ),
    (
        "get_station_info",
        (),
        {},
        P + "common.stationinfo",
        {},
        {"count": "1", "map_version": "v1"},
        {"count": "1", "map_version": "v1"},
        False,
    ),
    (
        "get_station_data",
        (),
        {},
        P + "common.stationdata",
        {},
        STATIONS,
        {"stations.0.code": "0001", "stations.0.name": "SYNTH_DEP", "stations.0.latitude": "37.1"},
        False,
    ),
    (
        "get_common_code",
        (["SYNTH_A", "SYNTH_B"],),
        {},
        P + "common.code.do",
        {
            **COMMON,
            "code": ["SYNTH_A", "SYNTH_B"],
            "deviceWidth": "101",
            "deviceHeight": "202",
            "OSVersion": "33",
        },
        {**ENVELOPE, "SYNTH_A": {"value": 1}, "SYNTH_B": []},
        {"raw.SYNTH_A.value": 1},
        False,
    ),
    (
        "get_app_data",
        (),
        {},
        "/file/CACHE/prdMobilePlusMain.cache",
        {"timeStamp": "1700000000000"},
        APP,
        {"version.new_version": "9", "notice.post_title": "SYNTH_TITLE"},
        False,
    ),
    (
        "get_notice",
        (),
        {},
        "/file/CACHE/prdMobilePlusMain.cache",
        {"timeStamp": "1700000000000"},
        APP,
        {"board_id": "1", "post_content": "SYNTH_BODY"},
        False,
    ),
    (
        "get_uuid",
        (),
        {},
        "/ebizcross/getUUID.do",
        {},
        {"mutMrkVrfCd": "SYNTH-VERIFICATION"},
        {"verification_code": "SYNTH-VERIFICATION"},
        False,
    ),
    (
        "get_service_status",
        (),
        {},
        "/file/CACHE/MobileService.cache",
        {"timeStamp": "1700000000000"},
        {**ENVELOPE, "timeStamp": 7},
        {"h_msg_cd": "API.I00000", "raw.timeStamp": 7},
        False,
    ),
    (
        "get_maas_menu_list",
        (),
        {},
        P + "copt.gdMenuLt.do",
        {**COMMON, "timeStamp": "1700000000000"},
        {
            **ENVELOPE,
            "menuList": [
                {
                    "active": "Y",
                    "addSrvDvCd": "SYNTH_SERVICE",
                    "appData": "Y",
                    "type": "M",
                    "name": "SYNTH_MENU",
                }
            ],
            "dElevatorUrl": "https://example.invalid/elevator",
        },
        {"items.0.name": "SYNTH_MENU", "departure_elevator_url": "https://example.invalid/elevator"},
        False,
    ),
    (
        "get_maas_station_data",
        ("SYNTH_SERVICE",),
        {},
        "/ebizmaas/EbizMaasStationList.do",
        {"addSrvDvCd": "SYNTH_SERVICE"},
        STATIONS,
        {"stations.0.code": "0001"},
        False,
    ),
    (
        "get_maas_service_details",
        (),
        {},
        P + "copt.gdReqQry.do",
        DEVICE,
        {
            **ENVELOPE,
            "addSrvList": [
                {
                    "addSrvId": "SYNTH_SERVICE",
                    "reqQnty": "1",
                    "detailInfo": {"name": "SYNTH_DETAIL", "entityOne": [{"synthetic": 1}]},
                }
            ],
        },
        {"details.0.additional_service_id": "SYNTH_SERVICE", "details.0.detail_info.name": "SYNTH_DETAIL"},
        True,
    ),
]
BY_NAME = {case[0]: case for case in CASES}


def lookup(obj, path):
    for key in path.split("."):
        obj = obj[int(key)] if key.isdecimal() else obj[key] if isinstance(obj, dict) else getattr(obj, key)
    return obj


def put(obj, path, value):
    keys = path.split(".")
    for key in keys[:-1]:
        obj = obj[int(key)] if key.isdecimal() else obj[key]
    if value is ABSENT:
        del obj[keys[-1]]
    else:
        obj[keys[-1]] = value


ABSENT = object()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network sockets are forbidden in F2")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr("korail_mobile_api.payloads.time.time", lambda: 1700000000.0)


@pytest.fixture
def rig():
    clients = []

    def make(responses, *, auth=False):
        pending = list(deepcopy(responses))
        calls = []

        def handler(request):
            calls.append(request)
            assert request.url.host == "example.invalid"
            assert pending, "unexpected additional HTTP request"
            payload = pending.pop(0)
            return httpx.Response(200, json=payload)

        config = KorailConfig(
            base_url="https://example.invalid",
            device=COMMON["Device"],
            version=COMMON["Version"],
            key=COMMON["Key"],
            lang=COMMON["lang"],
            device_width=101,
            device_height=202,
            android_sdk_int=33,
            netfunnel_enabled=False,
            dynapath=DynapathConfig(enabled=True, token_provider=lambda *args: "SYNTH-TOKEN"),
        )
        client = KorailClient(config, transport=httpx.MockTransport(handler))
        if auth:
            client.session.current = KorailSession(jsessionid="SYNTH-SESSION")
        clients.append(client)
        return client, calls, pending

    yield make
    for client in clients:
        client.close()


def exact_request(request, route, form, *, dynapath=False):
    dynapath = dynapath or route in {P + "seatMovie.ScheduleView", P + "seatMovie.ScheduleViewSpecial"}
    assert request.method == "POST"
    assert request.url.path == route
    assert not request.url.query
    expected = [(k, str(vv)) for k, v in form.items() for vv in (v if isinstance(v, list) else [v])]
    assert Counter(parse_qsl(request.content.decode(), keep_blank_values=True)) == Counter(expected)
    assert (request.headers.get("x-dynapath-m-token") == "SYNTH-TOKEN") is dynapath
    assert "Sid" not in dict(parse_qsl(request.content.decode()))
    if not form and route in {P + "common.stationinfo", P + "common.stationdata", "/ebizcross/getUUID.do"}:
        assert request.content == b""
        assert "content-type" not in request.headers
    else:
        assert request.headers["content-type"] == "application/x-www-form-urlencoded"


@pytest.mark.parametrize("case", CASES, ids=[x[0] for x in CASES])
def test_public_method_form_and_representative_parse(case, rig):
    """NetworkApi.java:214-773; each DTO/mask/callsite is indexed in REPORT §4.

    Synthetic nonempty MaaS data freezes inferred keys, not a verified live schema.
    """
    name, args, kwargs, route, form, raw, fields, auth = case
    client, calls, pending = rig([raw], auth=auth)
    result = getattr(client, name)(*args, **kwargs)
    assert len(calls) == 1 and not pending
    exact_request(calls[0], route, form, dynapath=name == "get_price_fare_quote")
    for path, value in fields.items():
        assert lookup(result, path) == value
    assert result.raw == raw


OPTIONAL = [
    ("search_trains", "trn_infos.trn_info.0.h_arv_tm", "trains.0.arrival_time"),
    ("search_transfer_trains", "trn_infos.trn_info.0.h_arv_tm", "trains.0.arrival_time"),
    ("search_trains_with_transfer_fallback", "trn_infos.trn_info.0.h_arv_tm", "trains.0.arrival_time"),
    ("get_train_schedule", "dlayList.0.stopStnNm", "stops.0.station_name"),
    ("get_transfer_stations", "chtnList.0.chtnRsStnCd", "stations.0.station_code"),
    ("get_train_calendar", "runningCalendar.0.runDt", "days.0.run_date"),
    ("get_seat_cars", "srcar_infos.srcar_info.0.seatAttInfos.0.seatAttCd", "cars.0.attributes.0.code"),
    ("get_seat_inventory", "seatList.0.etc_seat_att_cd", "seats.0.other_attribute_code"),
    ("get_free_seat_car_info", "fresScarNo", "car_no"),
    ("get_merge_seats_inquiry", "midStnList.0.runOrdr", "intermediate_stations.0.run_order"),
    ("get_price_fare_quote", "prcList.0.sumAmt", "fares.0.total_amount"),
    ("get_station_data", "stns.stn.0.latitude", "stations.0.latitude"),
    ("get_maas_station_data", "stns.stn.0.longitude", "stations.0.longitude"),
    ("get_app_data", "version.NEWDVERSION", "version.new_version"),
    ("get_notice", "notice.PtwtTtl", "post_title"),
    ("get_maas_menu_list", "menuList.0.addSrvDvCd", "items.0.additional_service_code"),
    ("get_maas_service_details", "addSrvList.0.reqQnty", "details.0.request_quantity"),
]


@pytest.mark.parametrize("name,wire,model", OPTIONAL)
@pytest.mark.parametrize(
    "value",
    [ABSENT, None, True, False, [], {}, 1.5],
    ids=["missing", "null", "true", "false", "list", "object", "float"],
)
def test_optional_strings_are_lenient(name, wire, model, value, rig):
    """Optional constructors: TrainScheduleOutTrainInfo.java:172-563; seat:62-105;
    RunDateOutItem.java:104-161; remaining DTOs/masks are in REPORT §5.
    """
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    put(raw, wire, value)
    client, calls, _ = rig([raw], auth=case[7])
    result = getattr(client, name)(*case[1], **case[2])
    assert lookup(result, model) is None
    assert result.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize("name,wire,model", OPTIONAL)
@pytest.mark.parametrize("value", [0, 12])
def test_optional_integer_string_compatibility(name, wire, model, value, rig):
    """SESSION_CONTEXT §3.6 integer/String compatibility; optional DTO masks in REPORT.
    This is the supplied interoperability policy, not Android's exact JSON decoder.
    """
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    put(raw, wire, value)
    client, _, _ = rig([raw], auth=case[7])
    result = getattr(client, name)(*case[1], **case[2])
    assert lookup(result, model) == str(value)
    assert result.raw == raw


@pytest.mark.parametrize("key", ["count", "map_version"])
@pytest.mark.parametrize("value", [ABSENT, None, True, [], {}, 1.5])
def test_station_info_serializer_required_mask(key, value, rig):
    """StationInfoOut.java:47-53 requires mask 0b11; null/malformed remain rejected."""
    raw = {"count": "1", "map_version": "1"}
    put(raw, key, value)
    client, calls, _ = rig([raw])
    with pytest.raises(KorailProtocolError) as error:
        client.get_station_info()
    assert error.value.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize("raw", [{"count": 0, "map_version": 12}, {"count": "", "map_version": ""}])
def test_station_info_required_string_accepts_integers_and_empty(raw, rig):
    """StationInfoOut.java:47-53 required presence; SESSION_CONTEXT §3.6 allows integers."""
    client, _, _ = rig([raw])
    result = client.get_station_info()
    assert result.count == str(raw["count"])
    assert result.map_version == str(raw["map_version"])
    assert result.raw == raw


@pytest.mark.parametrize("name", ["get_station_data", "get_maas_station_data"])
@pytest.mark.parametrize(
    "raw", [{}, {"stns": None}, {"stns": {}}, {"stns": {"stn": None}}, {"stns": {"stn": {}}}]
)
def test_station_container_required_masks(name, raw, rig):
    """StationDataOut.java:44-49 and StationDataOutStn.java:48-53 both require bit 1."""
    case = BY_NAME[name]
    client, _, _ = rig([raw])
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, name)(*case[1])
    assert error.value.raw == raw


@pytest.mark.parametrize(
    "name,wire,model",
    [
        ("get_seat_inventory", "seatList.0.sqr_no", "seats.0.sequence_no"),
        ("get_seat_inventory", "seat_ary_cd", "arrangement_code"),
        ("get_seat_cars", "srcar_infos.srcar_info.0.h_psrm_cl_nm", "cars.0.room_class_name"),
        ("get_station_data", "stns.stn.0.stn_cd", "stations.0.code"),
        ("get_uuid", "mutMrkVrfCd", "verification_code"),
    ],
)
def test_string_fields_allow_integer_strings(name, wire, model, rig):
    """String declarations read a JSON integer as its string (2026-09-21 observation)."""
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    put(raw, wire, 0)
    client, _, _ = rig([raw], auth=case[7])
    result = getattr(client, name)(*case[1], **case[2])
    assert lookup(result, model) == "0"
    assert result.raw == raw


@pytest.mark.parametrize(
    "name,wire,model,default",
    [
        ("get_seat_inventory", "layout_type", "layout_type", ""),
        ("get_seat_inventory", "seat_ary_cd", "arrangement_code", ""),
        ("get_seat_inventory", "seatList.0.seat_no", "seats.0.seat_no", ""),
        ("get_seat_inventory", "seatList.0.sale_psb_flg", "seats.0.sale_possible", ""),
        ("get_seat_inventory", "seatList.0.dir_seat_att_cd", "seats.0.direction_code", ""),
        ("get_seat_inventory", "seatList.0.rq_seat_att_cd", "seats.0.requested_attribute_code", ""),
        ("get_seat_inventory", "seatList.0.seat_spec", "seats.0.specification", ""),
        ("get_seat_inventory", "seatList.0.sqr_no", "seats.0.sequence_no", ""),
        ("get_seat_inventory", "seatList.0.intg_msg_cd", "seats.0.message_code", ""),
        ("get_seat_inventory", "seatList.0.intg_msg", "seats.0.message", ""),
        ("get_seat_inventory", "windowList.0.st_loc_rt", "windows.0.start_location_ratio", None),
        ("get_seat_inventory", "windowList.0.cls_loc_rt", "windows.0.close_location_ratio", None),
        ("get_seat_cars", "srcar_infos.srcar_info.0.h_srcar_no", "cars.0.car_no", None),
        ("get_seat_cars", "srcar_infos.srcar_info.0.h_rest_seat_cnt", "cars.0.remaining_seat_count", None),
        ("get_seat_cars", "srcar_infos.srcar_info.0.h_psrm_cl_nm", "cars.0.room_class_name", ""),
        ("get_seat_cars", "srcar_infos.srcar_info.0.seatAttInfos.0.seatAttNm", "cars.0.attributes.0.name", ""),
        ("get_station_data", "stns.stn.0.stn_cd", "stations.0.code", ""),
        ("get_station_data", "stns.stn.0.stn_nm", "stations.0.name", ""),
    ],
)
def test_optional_mask_fields_take_the_app_default(name, wire, model, default, rig):
    """TResidualSeatsResearchOut.java:61-82; TResidualSeatsResearchOutSeat.java:62-104;
    TResidualSeatsResearchOutWindow.java:51-56; TrainResearchOutCarInfo.java:59-85;
    TrainResearchOutSeatInfo.java:51-56; StationDataOutStnItem.java:60-63: an absent optional String
    is the app's "" default; the library's numeric fields read it as None."""
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    put(raw, wire, ABSENT)
    client, calls, _ = rig([raw], auth=case[7])
    result = getattr(client, name)(*case[1], **case[2])
    assert lookup(result, model) == default
    assert result.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize(
    "name,wire",
    [
        ("get_seat_inventory", "seatList.0.seat_no"),
        ("get_seat_cars", "srcar_infos.srcar_info.0.h_srcar_no"),
        ("get_seat_inventory", "windowList.0.st_loc_rt"),
        ("get_station_data", "stns.stn.0.stn_cd"),
    ],
)
@pytest.mark.parametrize("bad", [None, True, [], {}])
def test_optional_mask_fields_still_reject_null_and_wrong_types(name, wire, bad, rig):
    """The app's Json leniency flags are protected (NetworkServiceKt.java:25-29), so only absence is
    read as the default."""
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    put(raw, wire, bad)
    client, _, _ = rig([raw], auth=case[7])
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, name)(*case[1], **case[2])
    assert error.value.raw == raw


def test_uuid_verification_code_guard_is_retained(rig):
    """EBizCrossUUIDOut.java:51-58 marks mutMrkVrfCd optional; the library keeps requiring the code it
    must send next."""
    case = BY_NAME["get_uuid"]
    raw = deepcopy(case[5])
    put(raw, "mutMrkVrfCd", ABSENT)
    client, calls, _ = rig([raw], auth=case[7])
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, "get_uuid")(*case[1], **case[2])
    assert error.value.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize(
    "key,alias,model",
    [
        ("h_trn_no", "trnNo", "train_no"),
        ("h_trn_gp_cd", "trnGpCd", "train_group_code"),
        ("h_dpt_stn_run_ordr", "dptStnRunOrdr", "departure_run_order"),
        ("h_gd_no", "txtGdNo", "goods_no"),
    ],
)
def test_zero_canonical_train_scalar_does_not_select_alias(key, alias, model):
    """TrainScheduleOutTrainInfo.java:172-563; integer 0 must survive library alias logic."""
    raw = {key: 0, alias: "99"}
    train = TrainSummary.from_raw(raw)
    assert getattr(train, model) == "0"
    assert train.raw == raw


@pytest.mark.parametrize("name", ["search_trains", "search_transfer_trains"])
@pytest.mark.parametrize("empty", [True, False])
def test_next_page_empty_page_and_cursor_choice(name, empty, rig):
    """TrainScheduleViewModel.smali:36786-36851: empty list stops; cursor tuple branches.
    Library chooses transfer by cursor presence, not protected strJobId (REPORT F2-05).
    """
    raw = deepcopy(TRANSFER if name == "search_transfer_trains" else SEARCH)
    if empty:
        raw["trn_infos"]["trn_info"] = []
    client, _, _ = rig([raw])
    result = getattr(client, name)(QUERY)
    cursor = result.next_page()
    if empty:
        assert cursor is None
    elif name == "search_trains":
        assert cursor == TrainSearchContinuation("9", "00008", "")
    else:
        assert cursor == TrainSearchContinuation("9", "00009", "00010")


@pytest.mark.parametrize("name", ["search_trains", "search_transfer_trains"])
@pytest.mark.parametrize("key", ["h_next_pg_flg", "h_qry_st_no_next"])
@pytest.mark.parametrize("value", [ABSENT, None, "", "N", []])
def test_invalid_cursor_or_flag_never_creates_empty_request(name, key, value, rig):
    """Library continuation guards; app's emptiness check: TrainScheduleViewModel.smali:36786."""
    raw = deepcopy(TRANSFER if name == "search_transfer_trains" else SEARCH)
    put(raw, key, value)
    client, _, _ = rig([raw])
    result = getattr(client, name)(QUERY)
    if key == "h_qry_st_no_next" and value == "N":
        assert result.next_page().query_station_no == "N"  # opaque nonempty cursor
    else:
        assert result.next_page() is None


def test_numeric_zero_cursor_survives_parsing(rig):
    """TrainScheduleOut.java:67-109 declares cursor Strings; supplied integer policy."""
    raw = {**SEARCH, "h_qry_st_no_next": 0, "h_trn_no_next": 0}
    client, _, _ = rig([raw])
    cursor = client.search_trains(QUERY).next_page()
    assert cursor == TrainSearchContinuation("0", "0", "")


def test_transfer_incomplete_cursor_policy_is_not_app_proof(rig):
    """TrainScheduleViewModel.smali:36806-36851 does NOT test both cursors for presence."""
    raw = {**TRANSFER, "h_ectb_trn_no_next": None}
    client, _, _ = rig([raw])
    cursor = client.search_transfer_trains(QUERY).next_page()
    assert cursor == TrainSearchContinuation("9", "00008", "")  # retained library-only rule


def test_interleaved_transfer_grouping_uses_h_trn_seq_not_change_seq(rig):
    """TrainScheduleViewModel.smali:36958-37084: LinkedHashMap groupBy(h_trn_seq)."""
    rows = [
        {**ROW, "h_trn_no": str(i), "h_trn_seq": seq, "h_chg_trn_seq": "SAME"}
        for i, seq in [(1, "A"), (2, "B"), (3, "A"), (4, "B"), (5, "C")]
    ]
    client, _, _ = rig([{**ENVELOPE, "trn_infos": {"trn_info": rows}}])
    result = client.search_transfer_trains(QUERY)
    assert [(i.first.train_no, i.second.train_no) for i in result.itineraries] == [("1", "3"), ("2", "4")]
    assert len(result.trains) == 5  # single-member group retained raw, not in two-leg API


@pytest.mark.parametrize("size", [1, 2, 3])
def test_missing_sequence_groups_and_non_two_leg_groups_remain_raw(size, rig):
    """TrainScheduleViewModel.smali:36958-37084; two-leg filtering is a library limitation."""
    rows = [{"h_trn_no": str(i)} for i in range(size)]
    client, _, _ = rig([{**ENVELOPE, "trn_infos": {"trn_info": rows}}])
    result = client.search_transfer_trains(QUERY)
    assert len(result.itineraries) == (1 if size == 2 else 0)
    assert len(result.trains) == size and result.raw["trn_infos"]["trn_info"] == rows


def test_search_groups_teenager_infant_and_guide_dog_like_the_app(rig):
    """TrainScheduleViewModel.java:280-306,3050-3075: TEENAGER/GUIDE_DOG join ADULT (_1), BABY joins CHILD
    (_2)."""
    query = replace(
        QUERY,
        passengers=1,
        teenager_passengers=2,
        guide_dog_passengers=1,
        child_passengers=1,
        infant_passengers=1,
        senior_passengers=1,
    )
    client, calls, _ = rig([SEARCH])
    client.search_trains(query)
    sent = dict(parse_qsl(calls[0].content.decode()))
    assert [sent[f"txtPsgFlg_{index}"] for index in range(1, 6)] == ["4", "2", "1", "0", "0"]
    with pytest.raises(KorailProtocolError):
        client.search_trains(replace(QUERY, infant_passengers="1"))


@pytest.mark.parametrize("special", [False, True])
def test_exact_form_options_and_three_continuation_fields(special, rig):
    """TrainScheduleIn.java:95-285; TrainScheduleViewModel.java:7340 copies exactly three cursor fields."""
    query = replace(
        QUERY,
        passengers=2,
        child_passengers=1,
        senior_passengers=1,
        high_disability_passengers=1,
        low_disability_passengers=1,
        include_srt=True,
        seat_attribute_code="031",
        query_division_code="SYNTH_SORT",
        connection_station_codes=("0050", "0060"),
        connection_train_group_code="SYNTH_GROUP",
    )
    client, calls, _ = rig([SEARCH], auth=True)
    client.session.current = KorailSession(jsessionid="SYNTH-SESSION", member_card_no="SYNTH-MEMBER")
    client.search_trains(
        query, continuation=TrainSearchContinuation("S", "A", "B"), use_special_schedule=special
    )
    form = {
        **SEARCH_FORM,
        "txtPsgFlg_1": "2",
        "txtPsgFlg_2": "1",
        "txtPsgFlg_3": "1",
        "txtPsgFlg_4": "1",
        "txtPsgFlg_5": "1",
        "ebizCrossCheck": "Y",
        "srtCheckYn": "Y",
        "txtSeatAttCd_4": "031",
        "qryDvCd": "SYNTH_SORT",
        "qryStNo": "S",
        "qryStTrnNo": "A",
        "qryStTrnNo2": "B",
        "chtnCnt": "2",
        "chtnRsStnCd1": "0050",
        "chtnRsStnCd2": "0060",
        "trnGpCnt": "1",
        "trnGpCd1": "SYNTH_GROUP",
        "mbCrdNo": "SYNTH-MEMBER",
    }
    exact_request(calls[0], P + "seatMovie.ScheduleView" + ("Special" if special else ""), form)


def test_numeric_station_codes_are_resolved_once_then_cached(rig):
    """StationDataOut.java:44-49, TrainScheduleIn.java:95-285 expects departure/arrival names."""
    raw = {
        "stns": {"stn": [{"stn_cd": "0001", "stn_nm": "SYNTH_DEP"}, {"stn_cd": "0099", "stn_nm": "SYNTH_ARR"}]}
    }
    client, calls, _ = rig([raw, SEARCH, SEARCH])
    query = replace(QUERY, departure_station_code="0001", arrival_station_code="0099")
    client.search_trains(query)
    client.search_trains(query)
    exact_request(calls[0], P + "common.stationdata", {})
    for request in calls[1:]:
        exact_request(request, P + "seatMovie.ScheduleView", SEARCH_FORM)


def test_direct_no_results_falls_back_once_and_resets_continuation(rig):
    """TrainScheduleViewModel.smali:35513-35566 confirms dialog, not plaintext WRD000061 (protected).
    Library WRD000061 policy is fixed; user confirmation/filter reset are not emulated.
    """
    failure = {"strResult": "FAIL", "h_msg_cd": "WRD000061", "h_msg_txt": "SYNTH_NO_DIRECT"}
    client, calls, _ = rig([failure, TRANSFER])
    result = client.search_trains_with_transfer_fallback(
        QUERY, continuation=TrainSearchContinuation("S", "T", "U")
    )
    assert isinstance(result, TransferSearchResult)
    exact_request(
        calls[0],
        P + "seatMovie.ScheduleView",
        {**SEARCH_FORM, "qryStNo": "S", "qryStTrnNo": "T", "qryStTrnNo2": "U"},
    )
    exact_request(calls[1], P + "seatMovie.ScheduleView", {**SEARCH_FORM, "radJobId": "2"})


@pytest.mark.parametrize(
    "raw,raises",
    [
        ({"strResult": "SUCC", "h_msg_cd": "WRG000000"}, False),
        ({"strResult": "FAIL", "h_msg_cd": "SYNTH_OTHER"}, True),
    ],
)
def test_fallback_not_triggered_by_empty_success_or_unrelated_error(raw, raises, rig):
    """Supplied 2026-09-22 observation: SUCC/WRG000000 empty is not WRD000061."""
    client, calls, _ = rig([raw])
    if raises:
        with pytest.raises(KorailApiError):
            client.search_trains_with_transfer_fallback(QUERY)
    else:
        assert client.search_trains_with_transfer_fallback(QUERY).trains == []
    assert len(calls) == 1


@pytest.mark.parametrize("case", CASES, ids=[x[0] for x in CASES])
def test_failure_no_automatic_read_retry_and_raw_preserved(case, rig):
    """NetworkApi.java:214-773 read routes; envelope handling is the library HTTP contract."""
    raw = {"strResult": "FAIL", "h_msg_cd": "SYNTH_FAILURE", "h_msg_txt": "SYNTH", "extra": {"raw": True}}
    client, calls, _ = rig([raw], auth=case[7])
    if case[0] == "get_guide_seat_condition":
        assert getattr(client, case[0])(*case[1], **case[2]).raw == raw
    else:
        with pytest.raises(KorailApiError) as error:
            getattr(client, case[0])(*case[1], **case[2])
        assert error.value.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize(
    "name", ["search_trains", "get_guide_seat_condition", "get_seat_inventory", "get_maas_service_details"]
)
def test_p058_clears_session_even_on_guidance_path(name, rig):
    """CommonOut.java:426-438 has protected code; P058 mapping is supplied library policy."""
    case = BY_NAME[name]
    raw = {"strResult": "FAIL", "h_msg_cd": "P058", "h_msg_txt": "SYNTH_EXPIRED"}
    client, calls, _ = rig([raw], auth=True)
    client.http._client.cookies.set("JSESSIONID", "SYNTH-SESSION")
    with pytest.raises(KorailSessionExpiredError) as error:
        getattr(client, name)(*case[1], **case[2])
    assert error.value.raw == raw
    assert client.session.current is None and not client.http._client.cookies
    assert len(calls) == 1


@pytest.mark.parametrize("name", ["get_seat_cars", "get_seat_inventory", "get_maas_service_details"])
def test_local_auth_guard_is_retained_not_app_equivalence(name, rig):
    """Retained library-only check; app DTOs do not imply this preflight restriction."""
    case = BY_NAME[name]
    client, calls, _ = rig([])
    with pytest.raises(KorailAuthError):
        getattr(client, name)(*case[1], **case[2])
    assert calls == []


def test_ticket_maas_repeated_return_numbers_and_history_dates(rig):
    """NetworkApi.java:403-404 @Field(tkRetNo) List; MaasDetailIn.java:51-63 dates."""
    client, calls, _ = rig([ENVELOPE, ENVELOPE], auth=True)
    client.get_maas_menu_list(pnr_no="SYNTH-PNR", ticket_return_numbers=["SYNTH-RETURN-A", "SYNTH-RETURN-B"])
    exact_request(
        calls[0],
        P + "copt.gdMenuLt.do",
        {**COMMON, "pnrNo": "SYNTH-PNR", "tkRetNo": ["SYNTH-RETURN-A", "SYNTH-RETURN-B"]},
    )
    client.get_maas_service_details(MaasServiceDetailQuery.history("20290101", "20291231"))
    exact_request(calls[1], P + "copt.gdReqQry.do", {**DEVICE, "qryDtFrom": "20290101", "qryDtTo": "20291231"})


def test_two_leg_fare_and_goods_column_order(rig):
    """NetworkService.java:9839-9905 joins eight columns; separator/map names protected.
    The comma literals here deliberately freeze library policy, not decryption claims.
    """
    first = replace(FARE_LEG, goods_no="SYNTH-G1")
    second = PriceFareLeg("0099", "0100", DATE, "00008", "031", "102", "01", "SYNTH-G2")
    client, calls, _ = rig([ENVELOPE])
    client.get_price_fare_quote(PriceFareQuoteRequest((first, second)))
    form = {
        **COMMON,
        "txtMenuId": "11",
        "chtnDvCd": "2",
        "trnCnt": "2",
        "dptRsStnCd": "0001,0099",
        "arvRsStnCd": "0099,0100",
        "runDt": DATE + "," + DATE,
        "trnNo": "00007,00008",
        "gdNo": "SYNTH-G1,SYNTH-G2",
        "rqSeatAttCd": "015,031",
        "trnGpCd": "101,102",
        "stlbTrnClsfCd": "00,01",
    }
    exact_request(calls[0], P + "trn.prcFare.do", form, dynapath=True)
    keys = [k for k, _ in parse_qsl(calls[0].content.decode())]
    assert keys.index("trnNo") < keys.index("gdNo") < keys.index("rqSeatAttCd")


def test_price_fare_quote_sends_empty_goods_numbers_like_the_app(rig):
    """TrainOpInfoViewModel.java:794 passes null gdNo, so both legs carry the empty default and the joined
    column is just the separator."""
    second = PriceFareLeg("0099", "0100", DATE, "00008", "031", "102", "01")
    client, calls, _ = rig([ENVELOPE, ENVELOPE])
    client.get_price_fare_quote(PriceFareQuoteRequest((FARE_LEG,)))
    client.get_price_fare_quote(PriceFareQuoteRequest((FARE_LEG, second)))
    sent = [dict(parse_qsl(call.content.decode(), keep_blank_values=True)) for call in calls]
    assert sent[0]["gdNo"] == "" and sent[1]["gdNo"] == ","


@pytest.mark.parametrize("method", ["get_seat_cars", "get_seat_inventory"])
def test_optional_goods_and_seat_attribute_are_not_invented(method, rig):
    """TrainResearchIn.java:68-110; TResidualSeatsResearchIn.java:107-110,127-130.
    Empty primitives omitted by NetworkService.java:15335-15343; null encoding protected.
    """
    train = replace(TRAIN, goods_no=None, seat_attribute_code=None)
    response = CARS if method == "get_seat_cars" else INVENTORY
    client, calls, _ = rig([response], auth=True)
    args = (train,) if method == "get_seat_cars" else (train, 2)
    getattr(client, method)(*args, passenger_count=2)
    expected = dict(CAR_FORM if method == "get_seat_cars" else INVENTORY_FORM)
    for key in ("txtGdNo", "txtSeatAttCd", "gdNo", "seatAttCd"):
        expected.pop(key, None)
    exact_request(calls[0], BY_NAME[method][3], expected)


@pytest.mark.parametrize("method", ["get_seat_cars", "get_seat_inventory"])
def test_seat_attribute_override_follows_one_rule_for_both_seat_reads(method, rig):
    """An explicit value replaces the row value (even an unusable one); "" and None both fall back to the
    row."""
    response = CARS if method == "get_seat_cars" else INVENTORY
    key = "txtSeatAttCd" if method == "get_seat_cars" else "seatAttCd"
    args = (1,) if method == "get_seat_inventory" else ()
    client, calls, _ = rig([response, response], auth=True)
    getattr(client, method)(
        replace(TRAIN, seat_attribute_code="15"), *args, passenger_count=2, seat_attribute_code="021"
    )
    getattr(client, method)(
        replace(TRAIN, seat_attribute_code="031"), *args, passenger_count=2, seat_attribute_code=""
    )
    sent = [dict(parse_qsl(call.content.decode()))[key] for call in calls]
    assert sent == ["021", "031"]
    with pytest.raises(KorailProtocolError):
        getattr(client, method)(TRAIN, *args, passenger_count=2, seat_attribute_code="abc")
    assert len(calls) == 2


def test_notice_missing_and_optional_lists_empty(rig):
    """MobilePlusMainOut.java:57-77; RunDateOut.java:55-62; optional list defaults."""
    client, _, _ = rig([{}, ENVELOPE, ENVELOPE, ENVELOPE])
    notice = client.get_notice()
    assert notice.post_title is None and notice.raw == {}
    assert client.get_train_calendar().days == ()
    assert client.get_train_schedule(DATE, "7").stops == ()
    assert client.get_price_fare_quote(FARE_REQUEST).fares == ()


@pytest.mark.parametrize("value", [ABSENT, None, True, [], {}, 1.5])
def test_optional_long_on_guidance_is_lenient(value, rig):
    """GuideSeatCndOut.java:50-57 optional Long timeStamp; descriptor plaintext protected."""
    raw = {**ENVELOPE, "timeStamp": 1}
    put(raw, "timeStamp", value)
    client, _, _ = rig([raw])
    result = client.get_guide_seat_condition(GuideSeatConditionRequest("015"))
    assert result.time_stamp is None and result.raw == raw


def test_travel_search_is_record_only_and_keeps_the_dto_order(rig):
    """TravelSearchProductIn.java:60-81: funcDvCd, keyword field, bltnLstOrdr, nowPgNo, pgPrCnt. The app's codes
    are protected and the 2026-09-25 server refused a search without funcDvCd (WRR000100), so the call is
    record-only."""
    from korail_mobile_api import _travel_search_unsupported as record

    assert not hasattr(KorailClient, "search_travel_products")
    importers = []
    for path in Path(record.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [getattr(node, "module", None) or "", *(alias.name for alias in node.names)]
                if any("_travel_search_unsupported" in name for name in names):
                    importers.append(path.name)
    assert importers == []
    query = TravelProductSearchQuery(
        "SYNTH", "theme", page_no=2, function_code="SYNTH-F", order_code="SYNTH-O", page_size="SYNTH-P"
    )
    listing = {"gdList": [{"gdNo": "SYNTH_GOODS", "gdRepFare": "1000"}], "qryCnt": "1", "pgCnt": "1"}
    client, calls, _ = rig(
        [{**ENVELOPE, "lst": listing}, {**ENVELOPE, "lst": None}, {**ENVELOPE, "lst": {"gdList": {}}}]
    )
    result = record.search_travel_products(client, query)
    assert (result.products[0].goods_no, result.page_count) == ("SYNTH_GOODS", "1")
    assert calls[0].url.path == "/ebizcom/gdLstDtl.do"
    assert [key for key, _ in parse_qsl(calls[0].content.decode())][4:] == [
        "funcDvCd",
        "gdThmNm",
        "bltnLstOrdr",
        "nowPgNo",
        "pgPrCnt",
    ]
    assert record.search_travel_products(client, query).products == ()
    with pytest.raises(KorailProtocolError):
        record.search_travel_products(client, query)
    for bad in ({"keyword": " "}, {"keyword": "x", "keyword_field": "date"}, {"keyword": "x", "page_no": "1"}):
        with pytest.raises(KorailProtocolError):
            TravelProductSearchQuery(**bad)


def test_all_public_methods_have_contract_cases():
    assert len(CASES) == len(BY_NAME) == 22


@pytest.mark.parametrize("case", CASES, ids=[x[0] for x in CASES])
@pytest.mark.parametrize("raw", [{"strResult": True, "trace": {"synthetic": 1}}, ["synthetic-not-an-object"]])
def test_transport_parse_failure_keeps_full_json(case, raw, rig):
    """SESSION_CONTEXT §3.6 raw preservation; no Android/protected-field claim."""
    client, calls, _ = rig([raw], auth=case[7])
    with pytest.raises(KorailProtocolError) as error:
        getattr(client, case[0])(*case[1], **case[2])
    assert error.value.raw == raw
    assert len(calls) == 1


@pytest.mark.parametrize(
    "name,expected",
    [
        (
            "get_seat_cars",
            "Device Version Key lang txtMenuId txtRunDt txtDptDt txtTrnNo txtDptTm txtTrnClsfCd txtTrnGpCd "
            "txtDptRsStnCd txtArvRsStnCd txtPsrmClCd txtSeatAttCd txtDptStnRunOrdr txtArvStnRunOrdr "
            "txtTotPsgCnt txtGdNo",
        ),
        (
            "get_seat_inventory",
            "Device Version Key lang trnClsfCd trnGpCd runDt trnNo srcarNo psrmClCd dptRsStnCd arvRsStnCd "
            "seatAttCd "
            "dptStnRunOrdr arvStnRunOrdr totPsgCnt gdNo isArrow",
        ),
        (
            "get_merge_seats_inquiry",
            "Device Version Key lang abrdDt runDt trnNo dptRsStnNm arvRsStnNm selRsStnNm psrmClCd seatAttCd "
            "totPsgNum",
        ),
        ("get_common_code", "Device Version Key lang code code deviceWidth deviceHeight OSVersion"),
        ("get_maas_menu_list", "Device Version Key lang timeStamp"),
    ],
)
def test_read_forms_follow_the_app_dto_order(name, expected, rig):
    """TrainResearchIn.java:68; TResidualSeatsResearchIn.java:65; MergeSeatsCIn.java:63; CommonCodeIn.java:55;
    MaasMenuLtIn.java:58: the app flattens each DTO in declaration order (NetworkService.java:15335-15392),
    Key before lang."""
    case = BY_NAME[name]
    client, calls, _ = rig([case[5]], auth=case[7])
    getattr(client, name)(*case[1], **case[2])
    assert [key for key, _ in parse_qsl(calls[0].content.decode(), keep_blank_values=True)] == expected.split()


def test_nested_parser_raw_promotes_partial_context(rig, monkeypatch):
    """_preserve_read_raw contract: preserve full response AND existing partial evidence."""
    from korail_mobile_api import parsers

    partial = {"synthetic": "partial"}

    def fail(*args, **kwargs):
        error = KorailProtocolError("synthetic parse failure")
        error.raw = partial
        raise error

    monkeypatch.setattr(parsers, "_inventory_string", fail)
    client, _, _ = rig([INVENTORY], auth=True)
    with pytest.raises(KorailProtocolError) as error:
        client.get_seat_inventory(TRAIN, 2, passenger_count=2)
    assert error.value.raw == INVENTORY
    assert error.value.parser_raw is partial


@pytest.mark.parametrize("bad", [True, [], {}, 1.5])
def test_optional_merge_flag_is_lenient_and_raw_survives(bad, rig):
    """MergeSeatsCOutTrnInfos.java:54-61 optional merge flag."""
    raw = {**ENVELOPE, "trn_infos": {"h_merge_rsv_psb_flg": bad, "trn_info": []}}
    client, _, _ = rig([raw])
    result = client.get_merge_seats_inquiry(MERGE_REQUEST)
    assert result.merge_reservation_possible_flag is None and result.raw == raw


def test_zero_merge_flag_and_numeric_metadata(rig):
    """MergeSeatsCOutTrnInfos.java:54-61; TrainScheduleOut.java:67-109 optional Strings."""
    raw = {**ENVELOPE, "trn_infos": {"h_merge_rsv_psb_flg": 0, "trn_info": []}}
    client, _, _ = rig([raw, {**SEARCH, "h_rslt_cnt": 0, "h_rest_seat_cnt": 0}])
    assert client.get_merge_seats_inquiry(MERGE_REQUEST).merge_reservation_possible_flag == "0"
    result = client.search_trains(QUERY)
    assert result.metadata.result_count == "0" and result.metadata.remaining_seat_count == "0"


@pytest.mark.parametrize(
    "name,container",
    [
        ("get_train_schedule", "dlayList"),
        ("get_train_calendar", "runningCalendar"),
        ("get_maas_menu_list", "menuList"),
        ("get_maas_service_details", "addSrvList"),
        ("get_price_fare_quote", "prcList"),
        ("get_merge_seats_inquiry", "midStnList"),
    ],
)
@pytest.mark.parametrize("bad", [None, "not-a-list", 3, {}, ["bad-row", None, 5]])
def test_optional_containers_tolerate_bad_shapes(name, container, bad, rig):
    """Optional DTO lists; malformed-shape tolerance is library policy, not app decoder equivalence."""
    case = BY_NAME[name]
    raw = deepcopy(case[5])
    raw[container] = bad
    client, _, _ = rig([raw], auth=case[7])
    result = getattr(client, name)(*case[1], **case[2])
    attribute = {
        "dlayList": "stops",
        "runningCalendar": "days",
        "menuList": "items",
        "addSrvList": "details",
        "prcList": "fares",
        "midStnList": "intermediate_stations",
    }[container]
    assert getattr(result, attribute) == () and result.raw == raw


@pytest.mark.parametrize("bad", [True, False, [], {}, 1.5])
def test_train_no_retained_truthiness_dependent_type_guard(bad, rig):
    """TrainScheduleOutTrainInfo.java:172-563 marks even h_trn_no optional; retained guard."""
    raw = {**ENVELOPE, "trn_infos": {"trn_info": [{"h_trn_no": bad}]}}
    client, _, _ = rig([raw])
    if bad:
        with pytest.raises(KorailProtocolError) as error:
            client.search_trains(QUERY)
        assert error.value.raw == raw
    else:
        result = client.search_trains(QUERY)
        assert result.trains[0].train_no == "" and result.raw == raw


def test_common_code_and_status_unmodeled_values_remain_raw(rig):
    """CommonCodeOut.java:88-164; MobileServiceOut.java:49-56: raw-only data stays available."""
    raw = {**ENVELOPE, "timeStamp": {"malformed": True}, "SYNTH_CODE": [None, {"x": 1}]}
    client, calls, _ = rig([raw, raw])
    assert client.get_common_code("SYNTH_CODE").raw == raw
    assert client.get_service_status().raw == raw
    exact_request(
        calls[0],
        P + "common.code.do",
        {**COMMON, "code": "SYNTH_CODE", "deviceWidth": "101", "deviceHeight": "202", "OSVersion": "33"},
    )


@pytest.mark.parametrize(
    "peak,special,expected",
    [
        (False, False, "inquiry"),
        (True, False, "peak_season_inquiry"),
        (False, True, "product_inquiry"),
        (True, True, "product_inquiry"),
    ],
)
def test_search_queue_gate_wraps_request_without_extra_posts(peak, special, expected, rig):
    """TrainScheduleViewModel.java:5213-5235; aid plaintext protected, names are library settings."""
    client, calls, _ = rig([SEARCH])
    events = []

    class LocalQueue:
        def run(self, gate, send):
            events.append((gate, "enter", len(calls)))
            try:
                return send()
            finally:
                events.append((gate, "exit", len(calls)))

        def close(self):
            pass

    client.netfunnel = LocalQueue()
    client.search_trains(QUERY, peak_season=peak, use_special_schedule=special)
    assert events == [(expected, "enter", 0), (expected, "exit", 1)]


def test_cars_then_inventory_stays_two_read_posts(rig):
    """TrainSeatMapViewModel.java:1974-1976,2527-2577; no implicit reservation/payment."""
    client, calls, _ = rig([CARS, INVENTORY], auth=True)
    cars = client.get_seat_cars(TRAIN, passenger_count=2)
    client.get_seat_inventory(TRAIN, cars.cars[0].car_no, passenger_count=2)
    assert [r.url.path for r in calls] == [
        P + "research.TrainResearch",
        P + "research.TResidualSeatsResearch.do",
    ]
