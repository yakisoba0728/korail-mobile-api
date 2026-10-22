# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 입력과 폼입니다. 열차와 다른 공항버스 필드명은 DTO에 맞춰 별도로 구성합니다."""

from __future__ import annotations

import re
import time
from collections.abc import Sequence
from dataclasses import dataclass, fields

from ..._core.validation import _DATE_RE, _DIGITS_RE, _TIME_RE, _ascii_digits
from ..._core.wire import _device_version, _device_version_key, _in_reservation_order, _is_ascii_digits
from ...config import KorailConfig
from ...constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KorailReservationJobType,
)
from ...errors import KorailInvalidInputError
from ..reservations.forms import KorailPassengerCounts, _add_passenger_rows, _passenger_counts
from .models import (
    LIMOUSINE_CAR_NO,
    LIMOUSINE_ROOM_CLASS_CODE,
    LIMOUSINE_SEAT_ATTRIBUTE_CODE,
    LimousineSchedule,
)

# 좌석 조회가 운행 편에서 그대로 옮기는 식별값입니다.
_SCHEDULE_IDENTIFIERS = (
    "train_class_code",
    "service_code",
    "run_date",
    "train_no",
    "departure_station_code",
    "arrival_station_code",
    "departure_run_order",
    "arrival_run_order",
)


_OPTIONAL_SCHEDULE_FILTERS = ("train_no", "reservation_sale_division_code")


def _text(value: object, name: str, *, allow_blank: bool = False) -> str:
    """빈 값은 서버에서 키가 빠진 요청이 되므로 보내기 전에 거절합니다."""
    if not isinstance(value, str) or not (allow_blank or value.strip()):
        raise KorailInvalidInputError(f"{name} must be a {'' if allow_blank else 'non-empty '}string")
    return value


@dataclass(frozen=True)
class LimousineScheduleQuery:
    """공항버스 운행 스케줄 조회 조건을 구성합니다.

    ``train_no``와 ``reservation_sale_division_code``만 빈 문자열로 둘 수 있고(요청에서 빠짐), 나머지가 비었거나 문자열이
    아니면 ``KorailInvalidInputError``가 발생합니다."""

    departure_date: str
    departure_station_code: str
    arrival_station_code: str
    service_code: str
    room_class_code: str
    departure_time: str
    train_no: str
    seat_attribute_code: str
    reservation_sale_division_code: str

    def __post_init__(self) -> None:
        for item in fields(self):
            _text(getattr(self, item.name), item.name, allow_blank=item.name in _OPTIONAL_SCHEDULE_FILTERS)


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    """공항버스 한 호차의 좌석 조회 조건을 구성합니다.

    필수 문자열 필드가 비었거나 문자열이 아니면 ``KorailInvalidInputError``가 발생합니다."""

    train_class_code: str
    service_code: str
    run_date: str
    train_no: str
    car_no: str
    room_class_code: str
    departure_station_code: str
    arrival_station_code: str
    seat_attribute_code: str
    departure_run_order: str
    arrival_run_order: str
    passenger_count: int
    #: 상품 번호(``gdNo``)입니다. 앱의 공항버스 좌석 조회는 이 값을 넘기지 않습니다. ``None``(기본값)이면 요청에서 뺍니다.
    product_no: str | None = None
    #: 요청의 ``isArrow`` 값입니다. ``"true"`` 또는 ``"false"``로 보내며, 기본값 ``False``는 앱의 공항버스 좌석 조회와
    #: 같습니다.
    is_arrow: bool = False

    def __post_init__(self) -> None:
        if type(self.passenger_count) is not int:
            raise KorailInvalidInputError("passenger_count must be an integer")
        if type(self.is_arrow) is not bool:
            raise KorailInvalidInputError("is_arrow must be a boolean")
        for item in fields(self):
            if item.name not in ("passenger_count", "product_no", "is_arrow"):
                _text(getattr(self, item.name), item.name)

    @classmethod
    def from_schedule(
        cls, schedule: LimousineSchedule, *, passenger_count: int = 1
    ) -> LimousineSeatInventoryQuery:
        """조회한 편의 식별값과 공항버스 호차·객실 등급·좌석 속성으로 좌석 조회 조건을 만듭니다."""
        if not isinstance(schedule, LimousineSchedule):
            raise KorailInvalidInputError("schedule must be a LimousineSchedule")
        return cls(
            **{name: getattr(schedule, name) for name in _SCHEDULE_IDENTIFIERS},
            car_no=LIMOUSINE_CAR_NO,
            room_class_code=LIMOUSINE_ROOM_CLASS_CODE,
            seat_attribute_code=LIMOUSINE_SEAT_ATTRIBUTE_CODE,
            passenger_count=passenger_count,
        )


def build_limousine_schedule_form(
    config: KorailConfig,
    query: LimousineScheduleQuery,
) -> dict[str, str]:
    return {
        **_device_version_key(config),
        "dptDt": query.departure_date,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        "trnGpCd": query.service_code,
        "psrmClCd": query.room_class_code,
        "dptTm": query.departure_time,
        "trnNo": query.train_no,
        "seatAttCd": query.seat_attribute_code,
        "rsvSaleDvCd": query.reservation_sale_division_code,
    }


def build_limousine_seat_inventory_form(
    config: KorailConfig,
    query: LimousineSeatInventoryQuery,
) -> dict[str, str]:
    # 앱 공항버스 화면은 공유 DTO 의 ctlDvCd 를 기본값으로 두므로 열차 좌석변경과 달리 보내지 않습니다.
    return {
        **_device_version_key(config),
        "trnClsfCd": query.train_class_code,
        "trnGpCd": query.service_code,
        "runDt": query.run_date,
        "trnNo": query.train_no,
        "srcarNo": query.car_no,
        "psrmClCd": query.room_class_code,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        "seatAttCd": query.seat_attribute_code,
        "dptStnRunOrdr": query.departure_run_order,
        "arvStnRunOrdr": query.arrival_run_order,
        "totPsgCnt": str(query.passenger_count),
        **({"gdNo": query.product_no} if query.product_no is not None else {}),
        "isArrow": "true" if query.is_arrow else "false",
    }


# (전송 키, LimousineSchedule 필드, 형식) — 예약 여정 키의 순서입니다.
_RESERVATION_JOURNEY: tuple[tuple[str, str, re.Pattern[str] | None], ...] = (
    ("txtTrnNo1", "train_no", None),
    ("txtTrnClsfCd1", "train_class_code", None),
    ("txtTrnGpCd1", "service_code", None),
    ("txtRunDt1", "run_date", _DATE_RE),
    ("txtDptDt1", "departure_date", _DATE_RE),
    ("txtDptTm1", "departure_time", _TIME_RE),
    ("txtDptRsStnCd1", "departure_station_code", _DIGITS_RE),
    ("txtDptStnRunOrdr1", "departure_run_order", _DIGITS_RE),
    ("txtArvRsStnCd1", "arrival_station_code", _DIGITS_RE),
    ("txtArvStnRunOrdr1", "arrival_run_order", _DIGITS_RE),
)


def build_limousine_reservation_form(
    config: KorailConfig,
    schedule: LimousineSchedule,
    seat_nos: Sequence[str],
    *,
    passengers: KorailPassengerCounts | None = None,
) -> dict[str, str]:
    """열차 예약 DTO 를 쓰되 구성순서·변경 플래그는 보내지 않습니다. 보호된 기본값은 실서버에서 받아들여진 값입니다."""
    if not isinstance(schedule, LimousineSchedule):
        raise KorailInvalidInputError("KORAIL airport bus reservation requires a LimousineSchedule")
    passengers = _passenger_counts(passengers)
    if passengers.total - passengers.adult - passengers.child:
        raise KorailInvalidInputError("KORAIL airport bus passengers can only be adults and children")
    if isinstance(seat_nos, str | bytes) or not isinstance(seat_nos, Sequence):
        raise KorailInvalidInputError("seat_nos must be a sequence of seat numbers")
    seats = tuple(_text(seat, "seat_no") for seat in seat_nos)
    if len(seats) != passengers.total:
        raise KorailInvalidInputError("KORAIL airport bus reservation needs exactly one seat per passenger")
    # 앱은 좌석을 토글하므로 같은 좌석을 두 번 고를 수 없습니다.
    if len(set(seats)) != len(seats):
        raise KorailInvalidInputError("KORAIL airport bus reservation requires distinct seat numbers")
    # 앱은 잔여석이 인원보다 적은 편을 고르지 못하게 합니다. 숫자가 아닌 잔여석은 알 수 없는 값으로 보고 넘어갑니다.
    remaining = schedule.general_remaining_seat_count
    if _is_ascii_digits(remaining) and int(remaining) < passengers.total:
        raise KorailInvalidInputError("KORAIL airport bus schedule has fewer remaining seats than passengers")
    journey: dict[str, str] = {}
    for key, name, pattern in _RESERVATION_JOURNEY:
        value = _text(getattr(schedule, name), name)
        if pattern is not None and pattern.fullmatch(value) is None:
            raise KorailInvalidInputError(f"KORAIL airport bus schedule field {name} has an invalid shape")
        journey[key] = value
    form = _device_version_key(config)
    form.update(
        {
            "txtMenuId": "11",
            "txtJobId": KorailReservationJobType.IMMEDIATE.value,
            "hidFreeFlg": "N",
            "txtStndFlg": "N",
            "txtTotPsgCnt": str(passengers.total),
        }
    )
    _add_passenger_rows(form, passengers)
    form.update(
        {
            "txtSeatAttCd1": "000",
            "txtSeatAttCd2": "000",
            "txtSeatAttCd3": "000",
            "txtSeatAttCd4": LIMOUSINE_SEAT_ATTRIBUTE_CODE,
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": LIMOUSINE_ROOM_CLASS_CODE,
            "txtJrnyCnt": KORAIL_DIRECT_ITINERARY_CODE,
            "txtJrnyTpCd1": KORAIL_DIRECT_JOURNEY_TYPE_CODE,
            # 열차 예약과 같은 관측값 001 입니다. 앱은 전달받은 값을 그대로 씁니다.
            "txtJrnySqno1": "001",
            **journey,
            "txtSrcarCnt": str(len(seats)),
        }
    )
    for index, seat in enumerate(seats, start=1):
        form[f"txtSrcarNo{index}"] = LIMOUSINE_CAR_NO
        form[f"txtSeatNo{index}"] = seat
    return _in_reservation_order(form)


def build_maas_menu_form(config: KorailConfig) -> dict[str, str]:
    return {
        **_device_version_key(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


def _build_ticket_maas_menu_form(
    pnr_no: str | None,
    ticket_return_numbers: Sequence[str] | None,
) -> list[tuple[str, str]]:
    if not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailInvalidInputError("KORAIL ticket MaaS menu requires a PNR")
    if (
        ticket_return_numbers is None
        or isinstance(ticket_return_numbers, str | bytes)
        or not ticket_return_numbers
        or any(not isinstance(number, str) or not number.strip() for number in ticket_return_numbers)
    ):
        raise KorailInvalidInputError("KORAIL ticket MaaS menu requires at least one return number")
    return [
        ("pnrNo", pnr_no),
        *(("tkRetNo", number) for number in ticket_return_numbers),
    ]


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    """부가서비스 코드(``addSrvDvCd``) 하나뿐이고 공통 필드도 붙지 않습니다."""
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise KorailInvalidInputError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}


@dataclass(frozen=True)
class MaasServiceDetailQuery:
    """부가서비스 이용 내역의 조회 기간을 구성합니다."""

    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        # 앱은 두 날짜를 따로 nullable 로 넘기므로 짝·순서는 보지 않고 주어진 값의 YYYYMMDD 형식만 봅니다.
        for value, name in ((self.start_date, "start_date"), (self.end_date, "end_date")):
            if value is not None:
                _ascii_digits(value, name, lengths=frozenset({8}))

    @classmethod
    def current(cls) -> MaasServiceDetailQuery:
        """기간을 보내지 않는 조회 조건을 만듭니다."""
        return cls()

    @classmethod
    def history(
        cls,
        start_date: str,
        end_date: str,
    ) -> MaasServiceDetailQuery:
        """시작일~종료일 기간을 보내는 조회 조건을 만듭니다."""
        return cls(start_date=start_date, end_date=end_date)


def build_maas_service_detail_form(
    config: KorailConfig,
    query: MaasServiceDetailQuery,
) -> dict[str, str]:
    form = _device_version(config)
    if query.start_date is not None:
        form["qryDtFrom"] = query.start_date
    if query.end_date is not None:
        form["qryDtTo"] = query.end_date
    return form
