import time

from .config import KorailConfig
from .models import TrainSearchQuery


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
) -> dict[str, object]:
    return {
        "Device": config.device,
        "Version": config.version,
        "Key": config.key,
        "code": [code] if isinstance(code, str) else code,
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
        "departDate": "",
        "arrivalDate": "",
        "holidayYn": "",
        "OSVersion": config.android_sdk_int,
    }


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


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise ValueError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
