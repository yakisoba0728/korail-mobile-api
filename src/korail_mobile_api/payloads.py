import time

from .config import KorailConfig
from .errors import KorailProtocolError
from .models import TrainSearchQuery, TrainSummary


def _required_ascii_digits(
    value: object,
    name: str,
    *,
    lengths: frozenset[int],
) -> str:
    if (
        not isinstance(value, str)
        or len(value) not in lengths
        or any(character < "0" or character > "9" for character in value)
    ):
        expected = ", ".join(str(length) for length in sorted(lengths))
        raise KorailProtocolError(
            f"{name} must contain {expected} ASCII digit(s)"
        )
    return value


def validate_seat_inventory_inputs(
    train: TrainSummary,
    passenger_count: int,
    *,
    car_no: int | None = None,
) -> None:
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("train must be a TrainSummary")
    if type(passenger_count) is not int or not 1 <= passenger_count <= 9:
        raise ValueError("passenger_count must be an integer from 1 through 9")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise ValueError("car_no must be a positive integer")
    _required_ascii_digits(
        train.train_no,
        "train_no",
        lengths=frozenset(range(1, 6)),
    )
    _required_ascii_digits(
        train.train_group_code,
        "train_group_code",
        lengths=frozenset({3}),
    )
    _required_ascii_digits(
        train.departure_station_code,
        "departure_station_code",
        lengths=frozenset({4}),
    )
    _required_ascii_digits(
        train.arrival_station_code,
        "arrival_station_code",
        lengths=frozenset({4}),
    )
    _required_ascii_digits(
        train.departure_date,
        "departure_date",
        lengths=frozenset({8}),
    )
    _required_ascii_digits(
        train.run_date,
        "run_date",
        lengths=frozenset({8}),
    )
    _required_ascii_digits(
        train.train_class_code,
        "train_class_code",
        lengths=frozenset({2}),
    )
    _required_ascii_digits(
        train.departure_run_order,
        "departure_run_order",
        lengths=frozenset({6}),
    )
    _required_ascii_digits(
        train.arrival_run_order,
        "arrival_run_order",
        lengths=frozenset({6}),
    )


def _inventory_sid(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("sid must be a non-empty string")
    return value


def build_seat_car_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passenger_count: int,
    sid: str,
) -> dict[str, str]:
    validate_seat_inventory_inputs(train, passenger_count)
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "Sid": _inventory_sid(sid),
        "txtMenuId": "11",
        "txtPsrmClCd": "1",
        "txtRunDt": train.run_date or "",
        "txtDptDt": train.departure_date or "",
        "txtTrnClsfCd": train.train_class_code or "",
        "txtTrnNo": train.train_no.zfill(5),
        "txtDptRsStnCd": train.departure_station_code or "",
        "txtArvRsStnCd": train.arrival_station_code or "",
        "txtDptStnRunOrdr": train.departure_run_order or "",
        "txtArvStnRunOrdr": train.arrival_run_order or "",
        "txtTrnGpCd": train.train_group_code or "",
        "txtTotPsgCnt": str(passenger_count),
        "txtSeatAttCd": "015",
        "txtGdNo": "",
    }


def build_seat_inventory_form(
    config: KorailConfig,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int,
    sid: str,
) -> dict[str, str]:
    validate_seat_inventory_inputs(
        train,
        passenger_count,
        car_no=car_no,
    )
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "trnClsfCd": train.train_class_code or "",
        "trnGpCd": train.train_group_code or "",
        "runDt": train.run_date or "",
        "trnNo": train.train_no.zfill(5),
        "srcarNo": str(car_no),
        "psrmClCd": "1",
        "dptRsStnCd": train.departure_station_code or "",
        "arvRsStnCd": train.arrival_station_code or "",
        "seatAttCd": "015",
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        "gdNo": "",
        "isArrow": "true",
        "Sid": _inventory_sid(sid),
        "ctlDvCd": "",
    }


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    if timestamp_ms is not None and (
        type(timestamp_ms) is not int or timestamp_ms < 0
    ):
        raise ValueError("timestamp_ms must be a non-negative integer or None")
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_train_search_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    sid: str,
    member_card_no: str | None = None,
) -> dict[str, str]:
    form = {
        "Device": config.device,
        "Version": config.version,
        "Sid": sid,
        "txtMenuId": "11",
        "radJobId": "1",
        "selGoTrain": query.train_group_code,
        "txtTrnGpCd": query.train_group_code,
        "txtGoStart": departure_name,
        "txtGoEnd": arrival_name,
        "txtGoAbrdDt": query.departure_date,
        "txtGoHour": query.departure_time,
        "txtPsgFlg_1": str(query.passengers),
        "txtPsgFlg_2": "0",
        "txtPsgFlg_3": "0",
        "txtPsgFlg_4": "0",
        "txtPsgFlg_5": "0",
        "txtSeatAttCd_2": "000",
        "txtSeatAttCd_3": "000",
        "txtSeatAttCd_4": "015",
        "ebizCrossCheck": "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    return form


def build_train_schedule_form(
    config: KorailConfig,
    run_date: str,
    train_no: str,
) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(
    config: KorailConfig,
    code: str | list[str],
    *,
    depart_date: str = "",
    arrival_date: str = "",
    holiday_yn: str = "",
) -> dict[str, object]:
    form: dict[str, object] = {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "code": [code] if isinstance(code, str) else code,
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
    }
    if depart_date:
        form["departDate"] = depart_date
    if arrival_date:
        form["arrivalDate"] = arrival_date
    if holiday_yn:
        form["holidayYn"] = holiday_yn
    form["OSVersion"] = config.android_sdk_int
    return form


def build_ticket_list_form(
    config: KorailConfig,
    page_no: int,
) -> dict[str, str]:
    page = max(1, page_no)
    return {
        "txtDeviceId": config.advertising_id,
        "txtIndex": str(page),
        "h_page_no": str(page),
        "h_abrd_dt_from": "",
        "h_abrd_dt_to": "",
        "hiduserYn": "Y",
    }


def build_maas_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        "Device": config.device,
        "Version": config.version,
    }


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise ValueError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
