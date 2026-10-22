# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차 조회·좌석 입력과 폼입니다. 폼은 DTO 선언 순서를 따르며 보호된 기본값은 추측하지 않고 서버 메타데이터나 명시값을 씁니다."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, fields

from ..._core.validation import _ascii_digits, _passenger_count, _required_text, _wire_component
from ..._core.wire import _device_version, _device_version_key
from ...config import KorailConfig
from ...constants import KORAIL_DIRECT_ITINERARY_CODE, KORAIL_TRANSFER_ITINERARY_CODE, KorailRoomClassCode
from ...errors import KorailInvalidInputError
from .models import TrainSearchContinuation, TrainSearchQuery, TrainSummary

# 좌석 조회가 행에서 꺼내 보내는 식별자입니다. 비었으면 서버가 아닌 요청 전에 거절합니다.
_SEAT_READ_IDENTIFIERS = (
    "train_no",
    "run_date",
    "departure_station_code",
    "arrival_station_code",
    "departure_run_order",
    "arrival_run_order",
)


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise KorailInvalidInputError(f"{name} must not be empty")
    return value


def validate_seat_inventory_inputs(
    train: TrainSummary,
    passenger_count: int,
    *,
    car_no: int | None = None,
) -> None:
    """식별자는 비었는지만 보며 형식은 서버가 판정합니다."""
    if not isinstance(train, TrainSummary):
        raise KorailInvalidInputError("train must be a TrainSummary")
    _passenger_count(passenger_count, "passenger_count")
    if car_no is not None and (type(car_no) is not int or car_no < 1):
        raise KorailInvalidInputError("car_no must be a positive integer")
    for name in _SEAT_READ_IDENTIFIERS:
        _identifier(getattr(train, name), name)
    if train.goods_no:
        _wire_goods_no(train.goods_no)


def _seat_attribute(train: TrainSummary, override: str | None) -> str:
    """명시값이 있으면 그것만, 없으면(None·"") 행 값을 3자리 숫자로 검사해 씁니다. 둘 다 없으면 빈 값이라 보내지 않습니다."""
    value = override or train.seat_attribute_code
    if value:
        _ascii_digits(value, "seat_attribute_code", lengths=frozenset({3}))
    return value or ""


def _wire_goods_no(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.isascii()
        or any(character <= " " or character == "\x7f" for character in value)
    ):
        raise KorailInvalidInputError("goods_no must be a printable ASCII value")
    return value


def _validated_room_class_code(value: str) -> str:
    if value not in {"1", "2"}:
        raise KorailInvalidInputError('room_class_code must be "1" (general) or "2" (first class)')
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
    """Sid·txtCustSrtCd 는 보내지 않고, 빈 좌석속성·상품번호는 전송 계층이 뺍니다."""
    validate_seat_inventory_inputs(train, passenger_count)
    return {
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
        "txtSeatAttCd": _seat_attribute(train, seat_attribute_code),
        "txtDptStnRunOrdr": train.departure_run_order or "",
        "txtArvStnRunOrdr": train.arrival_run_order or "",
        "txtTotPsgCnt": str(passenger_count),
        # 상품번호가 없으면 기본값을 만들지 않습니다.
        "txtGdNo": train.goods_no or "",
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
    """직전 호차 조회의 속성을 이어 씁니다. 빈 좌석속성·상품번호는 전송 계층이 뺍니다."""
    validate_seat_inventory_inputs(train, passenger_count, car_no=car_no)
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
        # 속성이 없으면 기본값 015 를 만들지 않습니다.
        "seatAttCd": _seat_attribute(train, seat_attribute_code),
        "dptStnRunOrdr": train.departure_run_order or "",
        "arvStnRunOrdr": train.arrival_run_order or "",
        "totPsgCnt": str(passenger_count),
        "gdNo": train.goods_no or "",
        # evidence: app TrainSeatMapViewModel.smali:4116,4232-4238 (기본값 false 를 유지합니다)
        "isArrow": "false",
    }


def validate_train_search_query(query: TrainSearchQuery) -> None:
    """역 이름 조회·대기열 같은 선행 요청 전에 부르는 검사입니다. 빈 날짜·시각·열차군은 기존처럼 생략 대상입니다."""
    for name in ("departure_date", "departure_time", "train_group_code"):
        if not isinstance(getattr(query, name), str):
            raise KorailInvalidInputError(f"{name} must be a string")
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
    # 범위·합계는 앱 DTO 가 검사하지 않아 서버에 맡깁니다.
    if any(type(count) is not int for count in counts):
        raise KorailInvalidInputError("passenger counts must be integers")
    if not isinstance(query.seat_attribute_code, str) or not query.seat_attribute_code:
        raise KorailInvalidInputError("seat_attribute_code must be a non-empty string")
    if not isinstance(query.query_division_code, str) or not query.query_division_code:
        raise KorailInvalidInputError("query_division_code must be a non-empty string")
    codes = query.connection_station_codes
    if isinstance(codes, (str, bytes)) or any(not isinstance(code, str) or not code for code in codes):
        raise KorailInvalidInputError("connection_station_codes must be a sequence of non-empty strings")
    group = query.connection_train_group_code
    if group is not None and (not isinstance(group, str) or not group):
        raise KorailInvalidInputError("connection_train_group_code must be a non-empty string or None")


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
    """일반·특수 조회가 같은 폼을 씁니다. 이 진입점은 승차권 변경용 tkPsrmClCd/tkRcvdAmt 를 채우지 않습니다."""
    if continuation is not None and not isinstance(continuation, TrainSearchContinuation):
        raise KorailInvalidInputError("KORAIL train search continuation must be a TrainSearchContinuation")
    validate_train_search_query(query)
    form = {
        **_device_version_key(config),
        "txtMenuId": menu_id,
        "radJobId": KORAIL_TRANSFER_ITINERARY_CODE if transfer else KORAIL_DIRECT_ITINERARY_CODE,
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
        # evidence: app TrainScheduleViewModel.java:3137,3147 (두 칸은 같은 조건이며 Y/N 평문은 보호돼 미확인)
        "ebizCrossCheck": "Y" if query.include_srt else "N",
        "srtCheckYn": "Y" if query.include_srt else "N",
        "rtYn": "N",
        "adjStnScdlOfrFlg": "Y" if query.include_nearby_stations else "N",
        "mbCrdNo": member_card_no or "",
        "qryDvCd": query.query_division_code,
    }
    # 다음 쪽은 커서 세 개만 복사하고 pgPrCnt 는 보내지 않습니다.
    if continuation is not None:
        form["qryStNo"] = continuation.query_station_no
        form["qryStTrnNo"] = continuation.query_train_no
        form["qryStTrnNo2"] = continuation.query_train_no2
    # 선택역·후보 목록은 호출자가 주며 보호된 선택값은 추정하지 않습니다.
    if query.connection_station_codes:
        form["chtnCnt"] = str(len(query.connection_station_codes))
        for index, code in enumerate(query.connection_station_codes, 1):
            form[f"chtnRsStnCd{index}"] = code
    if query.connection_train_group_code is not None:
        form["trnGpCnt"] = "1"
        form["trnGpCd1"] = query.connection_train_group_code
    return form


def build_train_schedule_form(
    config: KorailConfig,
    run_date: str,
    train_no: str,
) -> dict[str, str]:
    """열차번호는 5자리로 영 채움하고 Key 는 싣지 않습니다."""
    return {
        **_device_version(config),
        "runDt": _identifier(run_date, "run_date"),
        "trnNo": _identifier(train_no, "train_no").zfill(5),
    }


@dataclass(frozen=True)
class FreeSeatCarRequest:
    """열차 한 편의 자유석 호차 조회 조건을 구성합니다.

    여섯 값은 모두 비어 있지 않은 문자열이어야 하며, 아니면 생성할 때 ``KorailInvalidInputError``가 발생합니다."""

    run_date: str
    train_no: str
    departure_construction_order: str
    arrival_construction_order: str
    departure_run_order: str
    arrival_run_order: str

    def __post_init__(self) -> None:
        for item in fields(self):
            _identifier(getattr(self, item.name), item.name)


@dataclass(frozen=True)
class GuideSeatConditionRequest:
    """도우미석 이용 안내 조회 조건을 구성합니다.

    ``seat_attribute_code``에는 안내를 받을 좌석 속성 코드를 넣습니다. 앱이 도우미석에 쓰는 좌석 속성 코드는 앱 내부 값이
    공개돼 있지 않아 확인하지 못했습니다."""

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
    """병합 가능한 좌석과 중간역 조회 조건을 구성합니다.

    승차·운행 일시, 열차 번호, 출발·도착역 이름이 비어 있으면 생성할 때 ``KorailInvalidInputError``가 발생합니다."""

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
        for name in (
            "boarding_datetime",
            "run_datetime",
            "train_no",
            "departure_station_name",
            "arrival_station_name",
        ):
            _identifier(getattr(self, name), name)
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
    # 두 번째 그룹부터는 SDK 확장이며(checks/BEHAVIOR.md) 각 그룹의 psgNumN 은 "1" 입니다.
    for slot in range(1, request.passenger_count + 1):
        form[f"seatAttCd{slot}"] = request.seat_attribute_code
        form[f"psgNum{slot}"] = "1"
        form[f"stlbDturDvNm{slot}"] = request.standing_detour_division_name
    return form


def build_merge_seats_inquiry_form(
    request: MergeSeatsInquiryRequest,
) -> dict[str, str]:
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
            raise KorailInvalidInputError("train must be a TrainSummary")
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

    ``legs``는 ``PriceFareLeg`` 한 개 또는 두 개여야 하고, ``goods_no``는 모든 구간에 넣거나 모두 비워 둬야 하며, 아니면
    생성할 때 ``KorailProtocolError``가 발생합니다. 앱이 보내는 메뉴 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다."""

    legs: tuple[PriceFareLeg, ...]
    # evidence: app TrainOpInfoViewModel.java:794 (메뉴 평문은 보호돼 미확인)
    menu_id: str = "11"

    def __post_init__(self) -> None:
        _wire_component(self.menu_id, "menu_id")
        # 목록 타입은 가리지 않고 tuple 로 고정합니다.
        if isinstance(self.legs, (str, bytes)) or not isinstance(self.legs, Sequence):
            raise KorailInvalidInputError("legs must be a sequence of one or two legs")
        object.__setattr__(self, "legs", tuple(self.legs))
        if len(self.legs) not in {1, 2}:
            raise KorailInvalidInputError("legs must contain one or two legs")
        if any(not isinstance(leg, PriceFareLeg) for leg in self.legs):
            raise KorailInvalidInputError("legs must contain PriceFareLeg values")
        if len({leg.goods_no is None for leg in self.legs}) > 1:
            raise KorailInvalidInputError("goods_no must be set on every leg or on none of them")


def build_price_fare_quote_form(
    request: PriceFareQuoteRequest,
) -> tuple[tuple[str, str], ...]:
    if not isinstance(request, PriceFareQuoteRequest):
        raise KorailInvalidInputError("request must be a PriceFareQuoteRequest")
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
    # 여덟 칸은 빈 gdNo 까지 같은 구분자로 이어 보냅니다(클라이언트는 omit_empty_fields=False 로 보냅니다).
    return (
        ("txtMenuId", request.menu_id),
        ("chtnDvCd", str(len(request.legs))),
        ("trnCnt", str(len(request.legs))),
        *(
            (wire_name, ",".join(getattr(leg, attribute) or "" for leg in request.legs))
            for wire_name, attribute in columns
        ),
    )
