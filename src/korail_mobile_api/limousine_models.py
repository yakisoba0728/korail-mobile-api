# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 연계 조회의 요청 질의와 응답 타입.

``lmu.scdlQry.do``(운행 스케줄)와 ``lms.TResidualSeatsResearch.do``(좌석 재고)가
씁니다. 6.5.0 의 ``seatMovie.LimousineScheduleView``(좌석이동 화면의 열차 목록)는
7.0.6 앱에서 사라져 요청·응답 타입 모두 지웠습니다.

``*Query`` 두 클래스는 얼어붙은 데이터클래스이고 ``__post_init__`` 에서 형식을
검사합니다. 둘 다 역**코드**(4자리)로 역을 받습니다.
``LimousineScheduleQuery``·``LimousineSeatInventoryQuery`` 는 운행/열차 식별자를
그대로 보여 주고 ``room_class_code``(좌석 재고는 ``car_no`` 도)만 가립니다.

운행 스케줄은 2026-09-16 실서버에서 확인했습니다 — 광명역→인천공항T1 42편을
파싱했습니다.

좌석 재고(``lms.TResidualSeatsResearch.do``)는 **요청 한 가지만** 라이브로
확인했습니다: 2026-09-22 나머지 조건이 같은 질의 3건을 ``isArrow`` 참/거짓으로
보내 참은 3건 모두 ``S003`` 거절, 거짓은 3건 모두 성공 봉투였습니다
(:attr:`LimousineSeatInventoryQuery.is_arrow`). 그 밖의 요청 필드와 **응답 모양**
(:class:`LimousineSeatInventoryResponse` 의 필드별 해석)은 라이브로 확인하지
않았고 APK 선언에서 나왔습니다 — ``layout_type`` 이 정수로도 온다는 사실은 같은
DTO 를 쓰는 일반 좌석재고 라우트의 2026-09-21 관측에서 빌려 온 것입니다.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .errors import KorailProtocolError
from .models import BaseKorailResponse, SeatWindow


def _non_empty_ascii(value: object, name: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
    if allow_empty and value == "":
        return
    if not value or not value.isascii():
        raise KorailProtocolError(f"{name} must be a non-empty ASCII string")


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
    if not value.strip():
        raise KorailProtocolError(f"{name} must not be empty")


def _optional_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise KorailProtocolError(f"{name} must be a string")
    if value and not value.strip():
        raise KorailProtocolError(f"{name} must be empty or contain non-whitespace text")


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
    room_class_code: str = field(repr=False)
    departure_time: str
    train_no: str
    seat_attribute_code: str
    reservation_sale_division_code: str

    def __post_init__(self) -> None:
        # The exact digit-length each field must have on the wire is the
        # server's format check to make, not this client's -- lmu.scdlQry.do
        # forwards every one of these straight into the form
        # (build_limousine_schedule_form) with nothing here branching on a
        # specific length. Only "is this a real ASCII string" stays.
        text_fields: tuple[tuple[str, str, bool], ...] = (
            (self.departure_date, "departure_date", False),
            (self.departure_station_code, "departure_station_code", False),
            (self.arrival_station_code, "arrival_station_code", False),
            (self.service_code, "service_code", False),
            (self.room_class_code, "room_class_code", False),
            (self.departure_time, "departure_time", False),
            (self.train_no, "train_no", True),
            (self.seat_attribute_code, "seat_attribute_code", True),
        )
        for value, name, allow_empty in text_fields:
            _non_empty_ascii(value, name, allow_empty=allow_empty)
        _required_text(
            self.reservation_sale_division_code,
            "reservation_sale_division_code",
        )


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    """``lms.TResidualSeatsResearch.do`` 좌석 재고 조회의 입력."""
    train_class_code: str
    service_code: str
    run_date: str
    train_no: str
    car_no: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_station_code: str
    arrival_station_code: str
    seat_attribute_code: str
    departure_run_order: str
    arrival_run_order: str
    passenger_count: int
    product_no: str
    #: ``isArrow`` — 앱이 보내는 값은 거짓입니다. 참으로 보내면
    #: ``lms.TResidualSeatsResearch.do`` 가 ``S003`` 로 거절합니다
    #: (2026-09-22 라이브: 나머지 조건이 같은 질의 3건이 참에서 전부 실패,
    #: 거짓에서 전부 성공). 호출자가 반드시 골라야 하는 값이 아니라 기본값이
    #: 있는 값이라 기본을 거짓으로 둡니다.
    is_arrow: bool = False

    def __post_init__(self) -> None:
        # Same reasoning as LimousineScheduleQuery.__post_init__: exact wire
        # length is lms.TResidualSeatsResearch.do's format check to make, not
        # this client's -- build_limousine_seat_inventory_form never branches
        # on a specific length either.
        text_fields: tuple[tuple[str, str, bool], ...] = (
            (self.train_class_code, "train_class_code", False),
            (self.service_code, "service_code", False),
            (self.run_date, "run_date", False),
            (self.train_no, "train_no", False),
            (self.car_no, "car_no", False),
            (self.room_class_code, "room_class_code", False),
            (self.departure_station_code, "departure_station_code", False),
            (self.arrival_station_code, "arrival_station_code", False),
            (self.seat_attribute_code, "seat_attribute_code", True),
            (self.departure_run_order, "departure_run_order", False),
            (self.arrival_run_order, "arrival_run_order", False),
        )
        for value, name, allow_empty in text_fields:
            _non_empty_ascii(value, name, allow_empty=allow_empty)
        _passenger_count(
            self.passenger_count,
            "passenger_count",
            allow_zero=False,
        )
        _optional_text(self.product_no, "product_no")
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
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)
    #: ``rcvdPrc`` — 이 편의 운임. 행에 있는 **유일한** 금액 필드인데 한동안
    #: 이름이 붙어 있지 않아 ``raw`` 로만 닿았습니다. 7.0.6 DTO 는 21개 String
    #: 필드를 선언하고(``ScdlQryOutTrain.java:29-49``) 그중 ``rcvdPrc`` 는
    #: ``:40`` 에 있습니다 — 게터 ``getRcvdPrc()`` 가 ``:389``, ``copy()`` 의
    #: 21번째 인자가 ``:428`` 입니다. 실서버도 빠뜨리지 않습니다:
    #: 2026-09-22 라이브 9개 변형 359행 전부에 있었습니다.
    #:
    #: 값은 0으로 앞을 채운 14자리 원 단위 숫자 문자열입니다 — 2026-09-22
    #: 광명→인천공항T1 20260925 의 42행이 모두 ``'00000000016000'``(16,000원)
    #: 이었습니다. 형제 필드들과 마찬가지로 손대지 않은 문자열로 둡니다:
    #: ``int`` 로 바꾸면 자릿수 채움이 사라지고, 같은 맵의 나머지 20개도 전부
    #: 널 가능 문자열입니다.
    #:
    #: ``raw`` **뒤**에 있는 것은 의도입니다. 앞에 끼워 넣으면 ``raw`` 의
    #: 위치 인자 자리가 한 칸 밀립니다.
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
    seat_no: str | None = field(default=None, repr=False)
    specification: str | None = None
    sequence_no: str | None = None
    visual_message_division_code: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict[str, Any], repr=False, compare=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    """``lms.TResidualSeatsResearch.do`` 의 응답 — 한 호차의 좌석표.

    이 라우트와 ``research.TResidualSeatsResearch.do``(열차 좌석표)는 같은
    DTO(``TResidualSeatsResearchOut.java``)를 돌려받습니다
    (``NetworkApi.java:271,741``). 형제 파서
    :func:`~korail_mobile_api.parsers.parse_seat_inventory_response` 가 이미
    읽는 ``layout_type``·``vrBnrUrl``·``windowList`` 세 필드를 이 응답도
    같은 DTO 에서 받지만, 좌석표를 그릴 목적이 아니라면 놓쳐도 눈에 띄지
    않아 리무진 쪽 파서는 오랫동안 세 필드를 읽지 않았습니다
    (``TResidualSeatsResearchOut.java:29,34-35,114,134,138``).
    """
    car_type_code: str | None = None
    car_no: str | None = field(default=None, repr=False)
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    #: ``layoutType`` — 좌석 배치 형식. 형제 응답
    #: :attr:`~korail_mobile_api.models.SeatInventoryResponse.layout_type`
    #: 과 같은 DTO 필드이며, DAO 선언은 String 이지만 실서버는 JSON 정수로도
    #: 보냅니다(2026-09-21 확인) — 파서가 둘 다 받아 문자열로 정규화합니다.
    layout_type: str | None = None
    #: ``vrBnrUrl`` — VR 배너 URL. 민감하지 않아 ``repr=False`` 없음(형제
    #: ``SeatInventoryResponse.vr_banner_url`` 과 동일한 판단).
    vr_banner_url: str | None = None
    #: ``windowList`` — 창측/통로측 위치 비율 목록.
    #: :class:`~korail_mobile_api.models.SeatWindow` 를 그대로 재사용합니다 —
    #: ``{st_loc_rt, cls_loc_rt}`` 구조가 형제 응답과 동일합니다.
    windows: tuple[SeatWindow, ...] = ()
    seats: tuple[LimousineSeat, ...] = ()
