# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스 운행·좌석 조회 모델을 제공합니다. 문자열 형식과 인원 범위는 서버에 맡기며 좌석 조회 입력의 passenger_count는 int, is_arrow는 bool인지 확인합니다.
2026-09-16: 광명→인천공항T1 스케줄 42편을 확인했습니다. 2026-09-22 동일 조건 3쌍은 isArrow=true에서 S003, false에서 성공 봉투를 반환했습니다. 모든
조건의 성공·좌석 필드 의미·보호된 값의 평문을 보장하지 않습니다. layout_type 정수 허용은 같은 DTO를 쓰는 일반 좌석 재고의 2026-09-21 관측에 근거합니다."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse, SeatWindow


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
    #: gdNo. 7.0.6 공항버스 화면은 null 을 넘깁니다(AirportBusSeatMapViewModel.java:865). None 이면 폼에서 뺍니다.
    product_no: str | None = None
    #: isArrow 기본값은 거짓입니다(TResidualSeatsResearchIn.java:132; AirportBusSeatMapViewModel.java:865 의 기본값 마스크).
    is_arrow: bool = False

    def __post_init__(self) -> None:
        if type(self.passenger_count) is not int:
            raise KorailProtocolError("passenger_count must be an integer")
        if type(self.is_arrow) is not bool:
            raise KorailProtocolError("is_arrow must be a boolean")


@dataclass(frozen=True)
class LimousineSchedule:
    """조회된 공항버스 한 편의 구간·운행·운임 정보를 담습니다."""
    arrival_date: str | None = None
    arrival_station_code: str | None = None
    arrival_run_order: str | None = None
    arrival_time: str | None = None
    transfer_division_code: str | None = None
    departure_date: str | None = None
    departure_station_code: str | None = None
    departure_run_order: str | None = None
    departure_time: str | None = None
    general_remaining_seat_count: str | None = None
    delay_minutes: str | None = None
    free_remaining_seat_count: str | None = None
    standing_remaining_seat_count: str | None = None
    run_date: str | None = None
    special_remaining_seat_count: str | None = None
    train_class_code: str | None = None
    service_code: str | None = None
    train_no: str | None = None
    train_order_no: str | None = None
    yms_application_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)
    #: rcvdPrc 운임 문자열(ScdlQryOutTrain.java:40,389). 2026-09-22 라이브 359행 모두 14자리 영 채움 문자열이었고 광명→인천공항T1 20260925 의
    #: 42행은 16,000원을 표시했습니다. 영 채움을 보존합니다.
    received_price: str | None = None


@dataclass(frozen=True)
class LimousineScheduleResponse(BaseKorailResponse):
    """공항버스 운행 스케줄 한 페이지를 담습니다."""
    following_page_extension: str | None = None
    long_short_division_code: str | None = None
    schedules: tuple[LimousineSchedule, ...] = ()


@dataclass(frozen=True)
class LimousineSeat:
    """공항버스 좌석표 한 자리의 식별자와 점유 상태를 담습니다."""
    direction_attribute_code: str | None = None
    other_attribute_code: str | None = None
    integrated_message: str | None = None
    integrated_message_code: str | None = None
    requested_attribute_code: str | None = None
    sale_possible_flag: str | None = None
    seat_no: str | None = None
    specification: str | None = None
    sequence_no: str | None = None
    visual_message_division_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], compare=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    """공항버스 한 호차의 좌석표와 배치 정보를 담습니다. 일반 좌석 재고와 TResidualSeatsResearchOut 을 공유합니다 (NetworkApi.java:271,741).
    배치·배너·창측 위치의 선언은 TResidualSeatsResearchOut.java:29,34-35,114,134,138 참고."""
    car_type_code: str | None = None
    car_no: str | None = None
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    layout_type: str | None = None
    vr_banner_url: str | None = None
    windows: tuple[SeatWindow, ...] = ()
    seats: tuple[LimousineSeat, ...] = ()
