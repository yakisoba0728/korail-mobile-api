# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 입력과 폼입니다. 열차와 다른 공항버스 필드명은 DTO에 맞춰 별도로 구성합니다."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

from ..._core.validation import _ascii_digits, _required_mutation_text
from ..._core.wire import _device_version, _device_version_key
from ...config import KorailConfig
from ...constants import (
    KORAIL_DIRECT_ITINERARY_CODE,
    KORAIL_DIRECT_JOURNEY_TYPE_CODE,
    KorailReservationJobType,
    KorailSeatClass,
)
from ...errors import KorailProtocolError
from ..reservations.forms import (
    _DATE_RE,
    _TIME_RE,
    KorailPassengerCounts,
    _add_passenger_rows,
    _in_reservation_order,
    _required_digits,
    _required_pattern,
    _seat_no_key,
    _sequence_no,
    _srcar_no_key,
)
from .models import LimousineSchedule


@dataclass(frozen=True)
class LimousineScheduleQuery:
    """공항버스 운행 스케줄 조회 조건을 구성합니다."""

    departure_date: str
    departure_station_code: str
    arrival_station_code: str
    service_code: str
    room_class_code: str
    departure_time: str
    train_no: str
    seat_attribute_code: str
    reservation_sale_division_code: str


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    """공항버스 한 호차의 좌석 조회 조건을 구성합니다."""

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
    # 7.0.6 공항버스 화면은 null 을 넘깁니다(AirportBusSeatMapViewModel.java:865).
    #: 상품 번호(``gdNo``)입니다. 앱의 공항버스 좌석 조회는 이 값을 넘기지 않습니다. ``None``(기본값)이면 요청에서 뺍니다.
    product_no: str | None = None
    # 기본값 근거: TResidualSeatsResearchIn.java:132; AirportBusSeatMapViewModel.java:865 의 기본값 마스크.
    #: 요청의 ``isArrow`` 값입니다. ``"true"`` 또는 ``"false"``로 보내며, 기본값 ``False``는 앱의 공항버스 좌석 조회와
    #: 같습니다.
    is_arrow: bool = False

    def __post_init__(self) -> None:
        if type(self.passenger_count) is not int:
            raise KorailProtocolError("passenger_count must be an integer")
        if type(self.is_arrow) is not bool:
            raise KorailProtocolError("is_arrow must be a boolean")


def build_limousine_schedule_form(
    config: KorailConfig,
    query: LimousineScheduleQuery,
) -> dict[str, str]:
    """앱 근거: NetworkApi.java:654-656."""
    return {
        **_device_version_key(config),
        "dptDt": query.departure_date,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        # 속성명은 trnGpCd(ScdlQryIn.java:38,60). 보호된 serializer 이름의 길이만으로 전송 키의 평문을 확정할 수는
        # 없습니다(ScdlQryIn$$serializer.java:32-44).
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
    """앱 근거: NetworkApi.java:269-271. isArrow 는 true/false 문자열입니다. ctlDvCd 는 공유 DTO 의 필드이나 공항버스 생성자는 기본값 슬롯을
    사용합니다 (AirportBusSeatMapViewModel.java:717,865). 열차 좌석변경 생성자 (TrainSeatMapViewModel.java:1976)와 달리 이
    폼에서는 생략합니다."""
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


#: 앱 상수 DEFINE_SRCARNO(AirportBusSeatMapViewModel.java:101)는 보호된 4바이트이며 좌석 조회와 예약에 같은 값을 씁니다(:766-783,853,865).
LIMOUSINE_CAR_NO = "0001"


def build_limousine_reservation_form(
    config: KorailConfig,
    schedule: LimousineSchedule,
    seat_nos: Sequence[str],
    *,
    passengers: KorailPassengerCounts | None = None,
    car_no: str = LIMOUSINE_CAR_NO,
) -> dict[str, str]:
    """같은 예약 DTO를 쓰되 구성순서는 보내지 않으며 보호된 기본값은 관측값입니다(AirportBusSeatMapViewModel.java:752-788)."""
    if not isinstance(schedule, LimousineSchedule):
        raise KorailProtocolError("KORAIL airport bus reservation requires a LimousineSchedule")
    if passengers is None:
        passengers = KorailPassengerCounts()
    elif not isinstance(passengers, KorailPassengerCounts):
        raise KorailProtocolError("KORAIL reservation requires an exact KorailPassengerCounts")
    if passengers.total - passengers.adult - passengers.child:
        raise KorailProtocolError("KORAIL airport bus passengers can only be adults and children")
    if isinstance(seat_nos, (str, bytes)) or not isinstance(seat_nos, Sequence):
        raise KorailProtocolError("seat_nos must be a sequence of seat numbers")
    seats = tuple(
        _required_mutation_text(seat, field="seat_no", context="airport bus reservation") for seat in seat_nos
    )
    if len(seats) != passengers.total:
        raise KorailProtocolError("KORAIL airport bus reservation needs exactly one seat per passenger")
    # 앱은 seat_no 를 토글하므로 같은 좌석을 두 번 선택할 수 없습니다(AirportBusSeatMapViewModel.java:1996-2038).
    if len(set(seats)) != len(seats):
        raise KorailProtocolError("KORAIL airport bus reservation requires distinct seat numbers")
    remaining = schedule.general_remaining_seat_count
    # 앱은 잔여석이 인원보다 적은 행을 고를 수 없게 합니다(AirportBusScheduleViewModel.java:407-426).
    if (
        isinstance(remaining, str)
        and remaining.isascii()
        and remaining.isdigit()
        and int(remaining) < passengers.total
    ):
        raise KorailProtocolError("KORAIL airport bus schedule has fewer remaining seats than passengers")
    context = "airport bus reservation"
    journey = {
        "txtTrnNo1": _required_mutation_text(schedule.train_no, field="train_no", context=context),
        "txtTrnClsfCd1": _required_mutation_text(
            schedule.train_class_code, field="train_class_code", context=context
        ),
        "txtTrnGpCd1": _required_mutation_text(schedule.service_code, field="service_code", context=context),
        "txtRunDt1": _required_pattern(schedule.run_date, field="run_date", pattern=_DATE_RE),
        "txtDptDt1": _required_pattern(schedule.departure_date, field="departure_date", pattern=_DATE_RE),
        "txtDptTm1": _required_pattern(schedule.departure_time, field="departure_time", pattern=_TIME_RE),
        "txtDptRsStnCd1": _required_digits(schedule.departure_station_code, field="departure_station_code"),
        "txtDptStnRunOrdr1": _required_digits(schedule.departure_run_order, field="departure_run_order"),
        "txtArvRsStnCd1": _required_digits(schedule.arrival_station_code, field="arrival_station_code"),
        "txtArvStnRunOrdr1": _required_digits(schedule.arrival_run_order, field="arrival_run_order"),
    }
    car = _required_mutation_text(car_no, field="car_no", context=context)
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
            "txtSeatAttCd4": "015",
            "txtSeatAttCd5": "000",
            "txtPsrmClCd1": KorailSeatClass.GENERAL.value,
            "txtJrnyCnt": KORAIL_DIRECT_ITINERARY_CODE,
            "txtJrnyTpCd1": KORAIL_DIRECT_JOURNEY_TYPE_CODE,
            "txtJrnySqno1": _sequence_no(KORAIL_DIRECT_ITINERARY_CODE),
            **journey,
            "txtSrcarCnt": str(len(seats)),
        }
    )
    for index, seat in enumerate(seats, start=1):
        form[_srcar_no_key(1, index)] = car
        form[_seat_no_key(1, index)] = seat
    return _in_reservation_order(form)


def build_maas_menu_form(config: KorailConfig) -> dict[str, str]:
    """앱 DTO 는 CommonIn 기본 생성자를 사용합니다(GdMenuLtIn.java:59-61). 공통 필드 인코딩: CommonIn.java:448-465."""
    return {
        **_device_version_key(config),
        "timeStamp": str(int(time.time() * 1000)),
    }


def _build_ticket_maas_menu_form(
    pnr_no: str | None,
    ticket_return_numbers: Sequence[str] | None,
) -> list[tuple[str, str]]:
    if not isinstance(pnr_no, str) or not pnr_no.strip():
        raise KorailProtocolError("KORAIL ticket MaaS menu requires a PNR")
    if (
        ticket_return_numbers is None
        or isinstance(ticket_return_numbers, (str, bytes))
        or not ticket_return_numbers
        or any(not isinstance(number, str) or not number.strip() for number in ticket_return_numbers)
    ):
        raise KorailProtocolError("KORAIL ticket MaaS menu requires at least one return number")
    return [
        ("pnrNo", pnr_no),
        *(("tkRetNo", number) for number in ticket_return_numbers),
    ]


def build_maas_station_form(additional_service_code: str) -> dict[str, str]:
    """부가서비스 코드(``addSrvDvCd``) 하나뿐이고 공통 필드도 붙지 않습니다."""
    if not isinstance(additional_service_code, str) or not additional_service_code.strip():
        raise KorailProtocolError("additional_service_code must be a non-empty string")
    return {"addSrvDvCd": additional_service_code}


@dataclass(frozen=True)
class MaasServiceDetailQuery:
    """부가서비스 이용 내역의 조회 기간을 구성합니다."""

    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self) -> None:
        _validate_maas_service_detail_query_values(
            self.start_date,
            self.end_date,
        )

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


def _validate_maas_service_detail_query_values(
    start_date: str | None,
    end_date: str | None,
) -> None:
    # 앱은 두 날짜를 따로 nullable 로 넘깁니다(MaasDetailIn.java:65-68, MyTicketBaseViewModel$executeMaasList$1.java:117).
    # 짝·순서는 검사하지 않고, 주어진 값의 YYYYMMDD 형식만 봅니다.
    for value, name in ((start_date, "start_date"), (end_date, "end_date")):
        if value is not None:
            _ascii_digits(value, name, lengths=frozenset({8}))
