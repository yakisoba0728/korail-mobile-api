# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 운행 스케줄·좌석 재고의 요청과 응답 모델.

Query 는 문자열 형식을 검사하지 않고 서버에 맡깁니다(좌석 재고 Query 는 인원 1~9 와 is_arrow 불리언만 검사). 2026-09-16 라이브 관측: 광명→인천공항T1 스케줄 42편.
2026-09-22 관측: 동일 조건 3쌍에서 isArrow=true 는 S003, false 는 성공 봉투였습니다. 좌석 응답의 필드별 해석은 이 실험으로 검증하지 않았습니다.
layout_type 정수 허용은 같은 DTO 를 쓰는 일반 좌석 재고의 2026-09-21 관측에 근거합니다.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse, SeatWindow


def _passenger_count(value: object, name: str, *, allow_zero: bool) -> None:
    minimum = 0 if allow_zero else 1
    if type(value) is not int:
        raise KorailProtocolError(f"{name} must be an integer")
    if not minimum <= value <= 9:
        qualifier = "0 through 9" if allow_zero else "1 through 9"
        raise KorailProtocolError(f"{name} must be an integer from {qualifier}")


def _boolean(value: object, name: str) -> None:
    if type(value) is not bool:
        raise KorailProtocolError(f"{name} must be a boolean")


@dataclass(frozen=True)
class LimousineScheduleQuery:
    """``lmu.scdlQry.do`` 운행 스케줄 조회의 입력."""
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
    """``lms.TResidualSeatsResearch.do`` 좌석 재고 조회의 입력."""
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
    #: isArrow 기본값은 거짓. 2026-09-22 동일 조건 3쌍에서 참은 S003, 거짓은 성공. 이 표본만으로 모든 조건의 성공 여부나 보호된 앱 리터럴의 평문은
    #: 확정하지 않습니다.
    is_arrow: bool = False

    def __post_init__(self) -> None:
        _passenger_count(
            self.passenger_count,
            "passenger_count",
            allow_zero=False,
        )
        _boolean(self.is_arrow, "is_arrow")


@dataclass(frozen=True)
class LimousineSchedule:
    """운행 스케줄 조회 결과의 한 편."""
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
    #: rcvdPrc 운임 문자열(ScdlQryOutTrain.java:40,389). 2026-09-22 라이브 359행에 존재; 광명→인천공항T1 20260925 의 42행은
    #: 14자리 영 채움으로 16,000원을 표시했습니다. 영 채움을 보존하며, raw 의 위치 인자 호환성을 위해 raw 뒤에 둡니다.
    received_price: str | None = None


@dataclass(frozen=True)
class LimousineScheduleResponse(BaseKorailResponse):
    """``lmu.scdlQry.do`` 의 응답."""
    following_page_extension: str | None = None
    long_short_division_code: str | None = None
    schedules: tuple[LimousineSchedule, ...] = ()


@dataclass(frozen=True)
class LimousineSeat:
    """좌석표의 좌석 한 자리."""
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
    """한 호차 좌석표. 일반 좌석 재고와 TResidualSeatsResearchOut 을 공유합니다 (NetworkApi.java:271,741). 배치·배너·창측 위치의 선언은
    TResidualSeatsResearchOut.java:29,34-35,114,134,138 참고.
    """
    car_type_code: str | None = None
    car_no: str | None = None
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    #: layout_type: 선언은 String 이나 일반 좌석 재고에서 JSON 정수도 관측(2026-09-21). 리무진 파서도 문자열·정수를 받아 문자열로 정규화합니다.
    layout_type: str | None = None
    #: VR 배너 URL. repr 에 표시됩니다.
    vr_banner_url: str | None = None
    #: 일반 좌석 재고와 같은 {st_loc_rt, cls_loc_rt} 구조이므로 SeatWindow 를 재사용합니다.
    windows: tuple[SeatWindow, ...] = ()
    seats: tuple[LimousineSeat, ...] = ()
