# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""보호된 기본값은 추측하지 않으며 순서·빈 값 처리의 근거는 각 빌더에 남깁니다."""

import time
from collections.abc import Sequence

from ._payload_helpers import _device_version, _device_version_key, _is_ascii_digits
from .config import KorailConfig
from .constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KorailRoomClassCode,
)
from .errors import KorailProtocolError
from .models import TrainSearchContinuation, TrainSearchQuery, TrainSummary


def _required_ascii_digits(
    value: object,
    name: str,
    *,
    lengths: frozenset[int],
) -> str:
    if not _is_ascii_digits(value, lengths):
        expected = ", ".join(str(length) for length in sorted(lengths))
        raise KorailProtocolError(f"{name} must contain {expected} ASCII digit(s)")
    return value


def validate_seat_inventory_inputs(
    train: TrainSummary,
    passenger_count: int,
    *,
    car_no: int | None = None,
) -> None:
    """행의 열차·역·날짜 식별자는 재검사하지 않으므로 임의 생성한 행의 유효성은 보장하지 않습니다."""
    if not isinstance(train, TrainSummary):
        raise KorailProtocolError("train must be a TrainSummary")
    if type(passenger_count) is not int or not 1 <= passenger_count <= 9:
        raise KorailProtocolError("passenger_count must be an integer from 1 through 9")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise KorailProtocolError("car_no must be a positive integer")
    if train.goods_no:
        _wire_goods_no(train.goods_no)


def _seat_attribute(train: TrainSummary, override: str | None) -> str:
    """좌석 속성은 선택된 예약 구간에서 옵니다(TrainSeatMapViewModel.java:2527,2546,2573-2577; TrainResearchIn.java:39,43,68).
    두 좌석 조회 모두 명시값이 있으면 그것만, 없으면(None·"") 행 값을 3자리 숫자로 검사해 씁니다."""
    value = override or train.seat_attribute_code
    if value:
        _required_ascii_digits(value, "seat_attribute_code", lengths=frozenset({3}))
    return value or ""


def _wire_goods_no(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or any(character <= " " or character == "\x7f" for character in value)
    ):
        raise KorailProtocolError("goods_no must be a printable ASCII value")
    return value


def _validated_room_class_code(value: str) -> str:
    # 객실은 사용자 선택값(TrainScheduleListContentRowItemPriceKt.java:600,621)이며 좌석 조회도 구간에서
    # 복사합니다(TrainSeatMapViewModel.java:2542,2546). PsrmType.java:19-22 의 GENERAL/SPECIAL 값은 보호됨.
    if value not in {"1", "2"}:
        raise KorailProtocolError('room_class_code must be "1" (general) or "2" (first class)')
    return value


def build_seat_car_form(
    config: KorailConfig,
    train: TrainSummary,
    *,
    passenger_count: int,
    room_class_code: KorailRoomClassCode = "1",
    seat_attribute_code: str | None = None,
    menu_id: str = "11",
) -> dict[str, str]:
    """호차 조회 DTO에는 Sid가 없으며 빈 좌석속성·상품번호는 생략합니다(TrainResearchIn.java:68; NetworkService.java:15342)."""
    validate_seat_inventory_inputs(train, passenger_count)
    seat_attribute = _seat_attribute(train, seat_attribute_code)
    return {
        # 키 순서는 TrainResearchIn 합성 생성자(TrainResearchIn.java:68)의 선언 순서입니다. txtCustSrtCd 는 보내지 않습니다.
        **_device_version_key(config),
        "txtMenuId": menu_id,
        "txtRunDt": train.run_date or "",
        "txtDptDt": train.departure_date or "",
        "txtTrnNo": train.train_no.zfill(5),
        "txtDptTm": train.departure_time or "",
        "txtTrnClsfCd": train.train_class_code or "",
        "txtTrnGpCd": train.train_group_code or "",
        "txtDptRsStnCd": train.departure_station_code or "",
        "txtArvRsStnCd": train.arrival_station_code or "",
        "txtPsrmClCd": _validated_room_class_code(room_class_code),
        # 상품이 아닌 좌석속성은 열차별 값입니다(TrainResearchIn.java:43; TrainSeatMapViewModel.java:2546,2577). 앱 평탄화기는 빈
        # primitive 를 생략합니다 (NetworkService.java:15335-15343).
        **({"txtSeatAttCd": seat_attribute} if seat_attribute else {}),
        "txtDptStnRunOrdr": train.departure_run_order or "",
        "txtArvStnRunOrdr": train.arrival_run_order or "",
        "txtTotPsgCnt": str(passenger_count),
        # 상품번호는 예약 입력에서 옵니다(TrainResearchIn.java:39; TrainSeatMapViewModel.java:2527). 값이 없으면 임의 기본값을 넣지 않습니다.
        **({"txtGdNo": train.goods_no} if train.goods_no else {}),
    }


def build_seat_inventory_form(
    config: KorailConfig,
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int,
    room_class_code: KorailRoomClassCode = "1",
    seat_attribute_code: str | None = None,
) -> dict[str, str]:
    """직전 호차 조회의 속성을 이어 쓰며 기본 isArrow=false를 유지합니다(TrainSeatMapViewModel.smali:4116,4232-4238)."""
    validate_seat_inventory_inputs(
        train,
        passenger_count,
        car_no=car_no,
    )
    seat_attribute = _seat_attribute(train, seat_attribute_code)
    return {
        **_device_version_key(config),
        "trnClsfCd": train.train_class_code or "",
        "trnGpCd": train.train_group_code or "",
        "runDt": train.run_date or "",
        "trnNo": train.train_no.zfill(5),
        "srcarNo": str(car_no),
        "psrmClCd": _validated_room_class_code(room_class_code),
        "dptRsStnCd": train.departure_station_code or "",
        "arvRsStnCd": train.arrival_station_code or "",
        # 속성이 없으면 기본값 015 를 만들지 않습니다. FieldMap 경로(NetworkApi.java:739-741)는 DTO 를 빈 primitive 제외 후
        # 평탄화합니다(TResidualSeatsResearchIn.java:39; NetworkService.java:14800-14803,15335-15343).
        **({"seatAttCd": seat_attribute} if seat_attribute else {}),
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        # 상품번호가 없으면 라이브러리는 해당 필드를 생략합니다.
        **({"gdNo": train.goods_no} if train.goods_no else {}),
        "isArrow": "false",
        "ctlDvCd": "",
    }


def build_cache_query(timestamp_ms: int | None = None) -> dict[str, str]:
    """캐시 요청에 현재 시각의 쿼리를 구성합니다. timestamp_ms 를 생략하면 현재 밀리초 epoch 이며, 제공한 값은 검증하지 않습니다."""
    resolved = int(time.time() * 1000) if timestamp_ms is None else timestamp_ms
    return {"timeStamp": str(resolved)}


def build_train_search_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    member_card_no: str | None = None,
    continuation: TrainSearchContinuation | None = None,
    transfer: bool = False,
    menu_id: str = "11",
) -> dict[str, str]:
    """다음 쪽 커서는 세 필드만 보내며 pgPrCnt는 보내지 않습니다(TrainScheduleIn.java:641-650; TrainScheduleViewModel.java:7340)."""
    if continuation is not None and not isinstance(continuation, TrainSearchContinuation):
        raise KorailProtocolError("KORAIL train search continuation must be a TrainSearchContinuation")
    counts = (
        query.passengers,
        query.child_passengers,
        query.senior_passengers,
        query.high_disability_passengers,
        query.low_disability_passengers,
        query.teenager_passengers,
        query.infant_passengers,
        query.guide_dog_passengers,
    )
    # 범위·합계는 앱 DTO 가 검사하지 않아 서버에 맡깁니다(TrainScheduleIn.java:95).
    if any(type(count) is not int for count in counts):
        raise KorailProtocolError("passenger counts must be integers")
    if not isinstance(query.seat_attribute_code, str) or not query.seat_attribute_code:
        raise KorailProtocolError("seat_attribute_code must be a non-empty string")
    form = {
        **_device_version_key(config),
        "txtMenuId": menu_id,
        "radJobId": (KORAIL_TRANSFER_ITINERARY_CODE if transfer else KORAIL_DIRECT_ITINERARY_CODE),
        "selGoTrain": query.train_group_code,
        "txtTrnGpCd": query.train_group_code,
        "txtGoStart": departure_name,
        "txtGoEnd": arrival_name,
        "txtGoAbrdDt": query.departure_date,
        "txtGoHour": query.departure_time,
        "txtPsgFlg_1": str(query.passengers + query.teenager_passengers + query.guide_dog_passengers),
        "txtPsgFlg_2": str(query.child_passengers + query.infant_passengers),
        "txtPsgFlg_3": str(query.senior_passengers),
        "txtPsgFlg_4": str(query.high_disability_passengers),
        "txtPsgFlg_5": str(query.low_disability_passengers),
        "txtSeatAttCd_2": "000",
        "txtSeatAttCd_3": "000",
        "txtSeatAttCd_4": query.seat_attribute_code,
        # 앱 두 선택 조건은 isSrt() || isSuseoTogether() 로 같습니다 (TrainScheduleViewModel.java:3137,3147;
        # TrainScheduleIn.java:33). 이 사실만으로 두 보호 리터럴이 Y/N 이거나 SRT 체크박스만의 조건이라고 할 수는 없습니다.
        "ebizCrossCheck": "Y" if query.include_srt else "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "N",
    }
    if member_card_no:
        form["mbCrdNo"] = member_card_no
    # 페이징 필드 위치는 DTO 선언 순서에 따릅니다(TrainScheduleIn.java:27,33). 이 진입점은 승차권 변경용 tkPsrmClCd/tkRcvdAmt 를 채우지 않습니다.
    if not isinstance(query.query_division_code, str) or not query.query_division_code:
        raise KorailProtocolError("query_division_code must be a non-empty string")
    connection_station_codes = query.connection_station_codes
    if isinstance(connection_station_codes, (str, bytes)) or any(
        not isinstance(code, str) or not code for code in connection_station_codes
    ):
        raise KorailProtocolError("connection_station_codes must be a sequence of non-empty strings")
    if query.connection_train_group_code is not None and (
        not isinstance(query.connection_train_group_code, str) or not query.connection_train_group_code
    ):
        raise KorailProtocolError("connection_train_group_code must be a non-empty string or None")
    form["qryDvCd"] = query.query_division_code
    # 신규 빌드의 커서 4개는 null(TrainScheduleViewModel.java:3212). 다음 페이지의 3튜플만 복사하며 pgPrCnt 는 추가하지
    # 않습니다(TrainScheduleViewModel.java:7340).
    if continuation is not None:
        form["qryStNo"] = continuation.query_station_no
        form["qryStTrnNo"] = continuation.query_train_no
        # continuation 의 결과를 재판정하지 않고 전달합니다. 일반 결과는 세 번째 커서가 빈 값, 환승 결과는 h_ectb_trn_no_next 를 사용할 수
        # 있습니다(TrainScheduleOut.java:67). 보호 리터럴은 미확인입니다.
        form["qryStTrnNo2"] = continuation.query_train_no2
    # 선택역·후보 목록은 호출자가 주며 보호된 선택값은 추정하지 않습니다.
    if connection_station_codes:
        form["chtnCnt"] = str(len(connection_station_codes))
        for index, code in enumerate(connection_station_codes, 1):
            form[f"chtnRsStnCd{index}"] = code
    if query.connection_train_group_code is not None:
        form["trnGpCnt"] = "1"
        form["trnGpCd1"] = query.connection_train_group_code
    return form


def build_train_schedule_special_form(
    config: KorailConfig,
    query: TrainSearchQuery,
    *,
    departure_name: str,
    arrival_name: str,
    member_card_no: str | None = None,
    continuation: TrainSearchContinuation | None = None,
    transfer: bool = False,
) -> dict[str, str]:
    """보호된 qryDvCd 값은 재구성하지 않고 query 에서 받습니다."""
    form = build_train_search_form(
        config,
        query,
        departure_name=departure_name,
        arrival_name=arrival_name,
        member_card_no=member_card_no,
        continuation=continuation,
        transfer=transfer,
    )
    device = form.pop("Device")
    version = form.pop("Version")
    # 앱 평탄화기처럼 빈 primitive 를 생략합니다(NetworkService.java:15335-15343).
    form = {key: value for key, value in form.items() if value}
    return {
        "Device": device,
        "Version": version,
        "Key": config.key,
        **form,
    }


def build_train_schedule_form(
    config: KorailConfig,
    run_date: str,
    train_no: str,
) -> dict[str, str]:
    """열차번호는 5자리 영 채움, Key 는 싣지 않습니다. 설정된 lang 은 공통 필드에 포함합니다(ActualTrainScheduleIn.java:53,
    CommonIn.java:40,432,467-474)."""
    return {
        **_device_version(config),
        "runDt": run_date,
        "trnNo": train_no.zfill(5),
    }


def build_common_code_form(
    config: KorailConfig,
    code: str | Sequence[str],
) -> dict[str, object]:
    """라우트 선언: NetworkApi.java:317,321. 기기 크기·SDK 정수는 설정을 사용합니다 (CommonCodeIn.java:31-34,55)."""
    form: dict[str, object] = {
        **_device_version_key(config),
        "code": [code] if isinstance(code, str) else list(code),
        "deviceWidth": config.device_width,
        "deviceHeight": config.device_height,
    }
    form["OSVersion"] = config.android_sdk_int
    return form


TICKET_LIST_MODE_ACTIVE = "1"


def build_ticket_list_form(
    config: KorailConfig,
    page_no: int,
    *,
    mode: str = TICKET_LIST_MODE_ACTIVE,
    boarding_date_from: str = "",
    boarding_date_to: str = "",
) -> dict[str, str]:
    """목록 종류·날짜·쪽번호를 보정하지 않으며 mode 의미는 관측값입니다(MyTicketListIn.java:62; 호출 리터럴 보호됨)."""
    if not isinstance(mode, str) or not mode:
        raise KorailProtocolError("ticket list mode must be a non-empty string")
    if type(page_no) is not int:
        raise KorailProtocolError("page_no must be an integer")
    # 키 순서는 MyTicketListIn 합성 생성자(MyTicketListIn.java:62)의 선언 순서입니다.
    return {
        "txtIndex": mode,
        "h_abrd_dt_from": boarding_date_from,
        "h_abrd_dt_to": boarding_date_to,
        "txtDeviceId": config.advertising_id,
        "hiduserYn": "Y",
        "h_page_no": str(page_no),
    }


def build_maas_menu_form(config: KorailConfig) -> dict[str, str]:
    """앱 DTO 는 CommonIn 기본 생성자를 사용합니다(GdMenuLtIn.java:59-61). 공통 필드 인코딩: CommonIn.java:448-465."""
    return {
        **_device_version_key(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    """부가서비스 코드(``addSrvDvCd``) 하나뿐이고 공통 필드도 붙지 않습니다."""
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise KorailProtocolError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}
