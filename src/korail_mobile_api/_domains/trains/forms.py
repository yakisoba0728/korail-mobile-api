# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차 조회·좌석 입력과 폼입니다. 보호된 기본값은 추측하지 않으며 순서·빈 값 처리의 근거는 각 빌더에 남깁니다.

조회 폼도 DTO 선언 순서를 따르며 보호된 입력 코드는 서버 메타데이터 또는 명시값을 사용합니다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..._core.validation import _passenger_count, _required_text, _wire_component
from ..._core.wire import _device_version, _device_version_key, _is_ascii_digits
from ...config import KorailConfig
from ...constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_MAX_PASSENGERS_PER_RESERVATION,
    KORAIL_TRANSFER_ITINERARY_CODE,
    KorailRoomClassCode,
)
from ...errors import KorailProtocolError
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
    if type(passenger_count) is not int or not 1 <= passenger_count <= KORAIL_MAX_PASSENGERS_PER_RESERVATION:
        raise KorailProtocolError(
            f"passenger_count must be an integer from 1 through {KORAIL_MAX_PASSENGERS_PER_RESERVATION}"
        )
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


def validate_train_search_query(query: TrainSearchQuery) -> None:
    """역 이름 조회·대기열 같은 선행 요청 전에 부르는 검사입니다. 빈 문자열은 기존처럼 생략 대상입니다."""
    for name in ("departure_date", "departure_time", "train_group_code"):
        if not isinstance(getattr(query, name), str):
            raise KorailProtocolError(f"{name} must be a string")
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
    validate_train_search_query(query)
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
        "adjStnScdlOfrFlg": "Y" if query.include_nearby_stations else "N",
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
    app_version = form.pop("AppVersion", None)
    form.pop("Key", None)
    # 앱 평탄화기처럼 빈 primitive 를 생략합니다(NetworkService.java:15335-15343).
    form = {key: value for key, value in form.items() if value}
    return {
        "Device": device,
        "Version": version,
        **({"AppVersion": app_version} if app_version is not None else {}),
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


@dataclass(frozen=True)
class FreeSeatCarRequest:
    """열차 한 편의 자유석 호차 조회 조건을 구성합니다."""

    run_date: str
    train_no: str
    departure_construction_order: str
    arrival_construction_order: str
    departure_run_order: str
    arrival_run_order: str


@dataclass(frozen=True)
class GuideSeatConditionRequest:
    """도우미석 이용 안내 조회 조건을 구성합니다.

    ``seat_attribute_code``에는 안내를 받을 좌석 속성 코드를 넣습니다. 앱이 도우미석에 쓰는 좌석 속성 코드는 앱 내부 값이
    공개돼 있지 않아 확인하지 못했습니다."""

    # 앱은 SeatType.HELPER 코드를 사용합니다(TrainOptionViewModel.java:270). 이 표본만으로 모든 입력·시점의 응답이 같다고
    # 보장하지 않습니다.

    seat_attribute_code: str


@dataclass(frozen=True)
class SeatAssignmentScheduleRequest:
    """좌석배정 화면의 열차 조회 조건을 구성합니다."""

    menu_id: str
    departure_date: str
    departure_time: str
    departure_station_name: str
    arrival_station_name: str
    train_group_code: str
    room_class_code: str
    seat_attribute_code: str
    passenger_count: int
    standing_detour_division_name: str
    transfer_type_code: str
    connection_arrival_station_name: str

    def __post_init__(self) -> None:
        _passenger_count(self.passenger_count, "passenger_count")


@dataclass(frozen=True)
class MergeSeatsInquiryRequest:
    """병합 가능한 좌석과 중간역 조회 조건을 구성합니다."""

    boarding_datetime: str
    run_datetime: str
    train_no: str
    departure_station_name: str
    arrival_station_name: str
    selected_station_name: str | None
    room_class_code: str
    seat_attribute_code: str
    passenger_count: int

    def __post_init__(self) -> None:
        _passenger_count(self.passenger_count, "passenger_count")


def build_free_seat_car_form(
    request: FreeSeatCarRequest,
) -> dict[str, str]:
    return {
        "runDt": request.run_date,
        "trnNo": request.train_no.zfill(5),
        "dptStnConsOrdr": request.departure_construction_order,
        "arvStnConsOrdr": request.arrival_construction_order,
        "dptStnRunOrdr": request.departure_run_order,
        "arvStnRunOrdr": request.arrival_run_order,
    }


def build_guide_seat_condition_form(
    request: GuideSeatConditionRequest,
) -> dict[str, str]:
    return {"rqSeatAttCd": request.seat_attribute_code}


def build_seat_assignment_schedule_form(
    request: SeatAssignmentScheduleRequest,
) -> dict[str, str]:
    form = {
        "menuId": request.menu_id,
        "dptDt": request.departure_date,
        "dptTm": request.departure_time,
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
        "trnGpCd": request.train_group_code,
        "psrmClCd": request.room_class_code,
        "dirtChtnDvCd": request.transfer_type_code,
        "chtnArvRsStnNm": request.connection_arrival_station_name,
    }
    # 7.0.10 앱 DTO에서 확인한 번호 그룹은 한 묶음입니다. *2 이상은 기존 SDK 확장으로 유지하며,
    # 앱 DTO와 동등하다고 보지 않습니다. SDK는 각 그룹의 psgNumN을 "1"로 보냅니다.
    for slot in range(1, request.passenger_count + 1):
        form[f"seatAttCd{slot}"] = request.seat_attribute_code
        form[f"psgNum{slot}"] = "1"
        form[f"stlbDturDvNm{slot}"] = request.standing_detour_division_name
    return form


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
    # 키 순서는 MergeSeatsCIn 합성 생성자(MergeSeatsCIn.java:63)의 선언 순서입니다.
    form = {
        "abrdDt": request.boarding_datetime,
        "runDt": request.run_datetime,
        "trnNo": request.train_no.zfill(5),
        "dptRsStnNm": request.departure_station_name,
        "arvRsStnNm": request.arrival_station_name,
    }
    if request.selected_station_name is not None:
        form["selRsStnNm"] = request.selected_station_name
    form["psrmClCd"] = request.room_class_code
    form["seatAttCd"] = request.seat_attribute_code
    form["totPsgNum"] = str(request.passenger_count)
    return form


@dataclass(frozen=True)
class PriceFareLeg:
    """예매 전 운임을 조회할 열차 한 구간을 구성합니다.

    ``goods_no``가 ``None``이면 앱처럼 상품 번호(``gdNo``) 칸을 빈 문자열로 보냅니다. ``None``이 아닌 값은 모두 비어 있지
    않은 문자열이어야 하고 쉼표를 포함할 수 없으며, 아니면 ``KorailProtocolError``가 발생합니다."""

    # 앱의 일반 열차 생성자는 기본값 마스크 64 로 gdNo 기본값을 쓰며(TrainOpInfoViewModel.java:794) 그 값은 길이 0 암호문,
    # 곧 빈 문자열입니다(PrcFareInItem.java:109).

    departure_station_code: str
    arrival_station_code: str
    run_date: str
    train_no: str
    requested_seat_attribute_code: str
    train_group_code: str
    train_class_code: str
    goods_no: str | None = None

    def __post_init__(self) -> None:
        for value, name in (
            (self.departure_station_code, "departure_station_code"),
            (self.arrival_station_code, "arrival_station_code"),
            (self.run_date, "run_date"),
            (self.train_no, "train_no"),
            (self.requested_seat_attribute_code, "requested_seat_attribute_code"),
            (self.train_group_code, "train_group_code"),
            (self.train_class_code, "train_class_code"),
        ):
            _wire_component(value, name)
        if self.goods_no is not None:
            _wire_component(self.goods_no, "goods_no")

    @classmethod
    def from_train(cls, train: TrainSummary) -> PriceFareLeg:
        """조회한 열차의 운행일·역·좌석 속성을 복사합니다. 누락값은 추측하지 않고 거절합니다."""
        if not isinstance(train, TrainSummary):
            raise KorailProtocolError("train must be a TrainSummary")
        return cls(
            departure_station_code=_required_text(train.departure_station_code, "departure_station_code"),
            arrival_station_code=_required_text(train.arrival_station_code, "arrival_station_code"),
            run_date=_required_text(train.run_date, "run_date"),
            train_no=train.train_no,
            requested_seat_attribute_code=_required_text(train.seat_attribute_code, "seat_attribute_code"),
            train_group_code=_required_text(train.train_group_code, "train_group_code"),
            train_class_code=_required_text(train.train_class_code, "train_class_code"),
            goods_no=None if train.goods_no == "" else train.goods_no,
        )


@dataclass(frozen=True)
class PriceFareQuoteRequest:
    """한두 구간의 운임 조회 조건과 메뉴를 구성합니다.

    ``legs``는 ``PriceFareLeg`` 한 개 또는 두 개여야 하며, 아니면 ``KorailProtocolError``가 발생합니다. ``goods_no``는 모든
    구간에 넣거나 모두 비워 두세요. 앱이 보내는 메뉴 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    # DTO: PrcFareIn.java:28-31,197. 생성자 TrainOpInfoViewModel.java:794 의 메뉴 리터럴은 보호됨.

    legs: tuple[PriceFareLeg, ...]
    menu_id: str = "11"

    def __post_init__(self) -> None:
        _wire_component(self.menu_id, "menu_id")
        # 목록 타입은 가리지 않고 tuple 로 고정합니다.
        if isinstance(self.legs, (str, bytes)) or not isinstance(self.legs, Sequence):
            raise KorailProtocolError("legs must be a sequence of one or two legs")
        object.__setattr__(self, "legs", tuple(self.legs))
        if len(self.legs) not in {1, 2}:
            raise KorailProtocolError("legs must contain one or two legs")
        for leg in self.legs:
            if not isinstance(leg, PriceFareLeg):
                raise KorailProtocolError("legs must contain PriceFareLeg values")


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(request, PriceFareQuoteRequest):
        raise KorailProtocolError("request must be a PriceFareQuoteRequest")
    columns = [
        ("dptRsStnCd", "departure_station_code"),
        ("arvRsStnCd", "arrival_station_code"),
        ("runDt", "run_date"),
        ("trnNo", "train_no"),
        ("gdNo", "goods_no"),
        ("rqSeatAttCd", "requested_seat_attribute_code"),
        ("trnGpCd", "train_group_code"),
        ("stlbTrnClsfCd", "train_class_code"),
    ]
    # 앱은 여덟 칸을 모두 같은 구분자로 이어 보내며 gdNo 도 빠지지 않습니다(NetworkService.java:9838-9905). 앱의 일반 열차 입력은 gdNo 가 null
    # 이라(TrainOpInfoViewModel.java:794) 기본값인 빈 문자열(PrcFareInItem.java:109, 길이 0 암호문)이 들어갑니다.
    supplied = [leg.goods_no is not None for leg in request.legs]
    if any(supplied) and not all(supplied):
        raise KorailProtocolError("goods_no must be set on every leg or on none of them")
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        ("trnCnt", str(len(request.legs))),
        *(
            (
                wire_name,
                ",".join(getattr(leg, attribute) or "" for leg in request.legs),
            )
            for wire_name, attribute in columns
        ),
    )
