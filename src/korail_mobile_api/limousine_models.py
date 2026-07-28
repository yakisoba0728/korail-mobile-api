"""리무진 연계 조회의 요청 질의와 응답 타입.

``lmu.scdlQry.do``(운행 스케줄), ``lms.TResidualSeatsResearch.do``(좌석
재고), ``seatMovie.LimousineScheduleView``(좌석이동 화면의 열차 목록) 세
라우트가 쓴다.

``*Query`` 세 클래스는 얼어붙은 데이터클래스이고 ``__post_init__`` 에서
자릿수·형식을 검사한다. 역은 라우트마다 다르게 준다 — 스케줄과 좌석 재고는
역**코드**(4자리), 좌석이동 목록은 역**이름**이다. 모든 필드가
``repr=False`` 라서 질의 객체를 로그에 찍어도 승객 구성이 새지 않는다.

라이브 미검증 — 요청과 응답 모양은 모두 APK 선언에서 나왔다.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .models import BaseKorailResponse


def _ascii_digits(
    value: object,
    name: str,
    *,
    lengths: frozenset[int],
    allow_empty: bool = False,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if allow_empty and value == "":
        return
    if (
        len(value) not in lengths
        or any(character < "0" or character > "9" for character in value)
    ):
        expected = ", ".join(str(length) for length in sorted(lengths))
        raise ValueError(f"{name} must contain {expected} ASCII digit(s)")


def _required_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _optional_text(value: object, name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value and not value.strip():
        raise ValueError(f"{name} must be empty or contain non-whitespace text")


def _passenger_count(value: object, name: str, *, allow_zero: bool) -> None:
    minimum = 0 if allow_zero else 1
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer")
    if not minimum <= value <= 9:
        qualifier = "0 through 9" if allow_zero else "1 through 9"
        raise ValueError(f"{name} must be an integer from {qualifier}")


def _boolean(value: object, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"{name} must be a boolean")


@dataclass(frozen=True)
class LimousineScheduleQuery:
    """``lmu.scdlQry.do`` 운행 스케줄 조회의 입력.

    역은 이름이 아니라 **4자리 역코드**다. ``departure_date`` 는 ``YYYYMMDD``,
    ``departure_time`` 은 ``HHMMSS``. ``train_no`` 와 ``seat_attribute_code`` 는
    빈 문자열을 허용한다 — 편이나 좌석 속성을 좁히지 않는다는 뜻이다.

    ``service_code``(``tmGpCd``)와 ``room_class_code``(``psrmClCd``)는 자릿수만
    검사한다. 어떤 코드가 유효한지는 서버가 정한다.
    """
    departure_date: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    service_code: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_time: str = field(repr=False)
    train_no: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    reservation_sale_division_code: str = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.departure_date,
            "departure_date",
            lengths=frozenset({8}),
        )
        _ascii_digits(
            self.departure_station_code,
            "departure_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.arrival_station_code,
            "arrival_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.room_class_code,
            "room_class_code",
            lengths=frozenset({1, 2}),
        )
        _ascii_digits(
            self.departure_time,
            "departure_time",
            lengths=frozenset({6}),
        )
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
            allow_empty=True,
        )
        _ascii_digits(
            self.seat_attribute_code,
            "seat_attribute_code",
            lengths=frozenset({3}),
            allow_empty=True,
        )
        _required_text(
            self.reservation_sale_division_code,
            "reservation_sale_division_code",
        )


@dataclass(frozen=True)
class LimousineSeatInventoryQuery:
    """``lms.TResidualSeatsResearch.do`` 좌석 재고 조회의 입력.

    편과 호차를 지목하는 값들에 구간과 인원이 붙는다. 역은 4자리 역코드이고,
    ``departure_run_order``/``arrival_run_order`` 는 그 편에서 두 역이 몇 번째
    정차인지다 — 같은 열차가 한 역을 두 번 지날 수 있어 역코드만으로는 구간이
    정해지지 않는다.

    ``passenger_count`` 는 0 을 허용하지 않는 정수, ``is_arrow`` 는 불리언이다.
    둘만 문자열이 아니며 폼 빌더가 각각 ``str(int)`` 과 ``"true"``/``"false"``
    로 바꾼다. ``product_no``(``gdNo``)는 선택값이라 빈 문자열이 될 수 있다.
    """
    train_class_code: str = field(repr=False)
    service_code: str = field(repr=False)
    run_date: str = field(repr=False)
    train_no: str = field(repr=False)
    car_no: str = field(repr=False)
    room_class_code: str = field(repr=False)
    departure_station_code: str = field(repr=False)
    arrival_station_code: str = field(repr=False)
    seat_attribute_code: str = field(repr=False)
    departure_run_order: str = field(repr=False)
    arrival_run_order: str = field(repr=False)
    passenger_count: int = field(repr=False)
    product_no: str = field(repr=False)
    is_arrow: bool = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.train_class_code,
            "train_class_code",
            lengths=frozenset({2}),
        )
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(self.run_date, "run_date", lengths=frozenset({8}))
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
        )
        _ascii_digits(
            self.car_no,
            "car_no",
            lengths=frozenset({1, 2, 3, 4}),
        )
        _ascii_digits(
            self.room_class_code,
            "room_class_code",
            lengths=frozenset({1, 2}),
        )
        _ascii_digits(
            self.departure_station_code,
            "departure_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.arrival_station_code,
            "arrival_station_code",
            lengths=frozenset({4}),
        )
        _ascii_digits(
            self.seat_attribute_code,
            "seat_attribute_code",
            lengths=frozenset({3}),
            allow_empty=True,
        )
        _ascii_digits(
            self.departure_run_order,
            "departure_run_order",
            lengths=frozenset({6}),
        )
        _ascii_digits(
            self.arrival_run_order,
            "arrival_run_order",
            lengths=frozenset({6}),
        )
        _passenger_count(
            self.passenger_count,
            "passenger_count",
            allow_zero=False,
        )
        _optional_text(self.product_no, "product_no")
        _boolean(self.is_arrow, "is_arrow")


@dataclass(frozen=True)
class LimousineScheduleViewQuery:
    """``seatMovie.LimousineScheduleView`` 열차 목록 조회의 입력.

    앞의 두 질의와 달리 역을 **역이름**으로 준다
    (``departure_station_name``/``arrival_station_name``).

    인원은 하나의 총원이 아니라 다섯 칸으로 나뉘고 각각 ``txtPsgFlg_1``~
    ``txtPsgFlg_5`` 가 된다 — 승객 그룹 둘, 경로우대, 중증장애, 경증장애.

    좌석 속성 셋은 방향(``direction_seat_attribute_code``), 위치
    (``location_seat_attribute_code``), 객실(``room_seat_attribute_code``)이며
    각각 ``txtSeatAttCd_2``/``_3``/``_4`` 로 나간다.

    ``ebiz_cross_check``·``srt_check``·``round_trip`` 은 불리언이고 전선에서는
    ``"Y"``/``"N"`` 이 된다.
    """
    menu_id: str = field(repr=False)
    job_id: str = field(repr=False)
    job_division: str = field(repr=False)
    service_code: str = field(repr=False)
    train_no: str = field(repr=False)
    departure_station_name: str = field(repr=False)
    arrival_station_name: str = field(repr=False)
    departure_date: str = field(repr=False)
    departure_time: str = field(repr=False)
    passenger_group_1_count: int = field(repr=False)
    passenger_group_2_count: int = field(repr=False)
    senior_count: int = field(repr=False)
    severe_disability_count: int = field(repr=False)
    mild_disability_count: int = field(repr=False)
    direction_seat_attribute_code: str = field(repr=False)
    location_seat_attribute_code: str = field(repr=False)
    room_seat_attribute_code: str = field(repr=False)
    ebiz_cross_check: bool = field(repr=False)
    srt_check: bool = field(repr=False)
    round_trip: bool = field(repr=False)

    def __post_init__(self) -> None:
        _ascii_digits(
            self.menu_id,
            "menu_id",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.job_id,
            "job_id",
            lengths=frozenset({1, 2, 3}),
        )
        _optional_text(self.job_division, "job_division")
        _ascii_digits(
            self.service_code,
            "service_code",
            lengths=frozenset({1, 2, 3}),
        )
        _ascii_digits(
            self.train_no,
            "train_no",
            lengths=frozenset({1, 2, 3, 4, 5}),
            allow_empty=True,
        )
        _required_text(self.departure_station_name, "departure_station_name")
        _required_text(self.arrival_station_name, "arrival_station_name")
        _ascii_digits(
            self.departure_date,
            "departure_date",
            lengths=frozenset({8}),
        )
        _ascii_digits(
            self.departure_time,
            "departure_time",
            lengths=frozenset({6}),
        )
        passenger_fields = (
            ("passenger_group_1_count", self.passenger_group_1_count),
            ("passenger_group_2_count", self.passenger_group_2_count),
            ("senior_count", self.senior_count),
            ("severe_disability_count", self.severe_disability_count),
            ("mild_disability_count", self.mild_disability_count),
        )
        for name, value in passenger_fields:
            _passenger_count(value, name, allow_zero=True)
        total = sum(value for _, value in passenger_fields)
        if not 1 <= total <= 9:
            raise ValueError(
                "passenger counts must total an integer from 1 through 9"
            )
        for name, value in (
            (
                "direction_seat_attribute_code",
                self.direction_seat_attribute_code,
            ),
            (
                "location_seat_attribute_code",
                self.location_seat_attribute_code,
            ),
            ("room_seat_attribute_code", self.room_seat_attribute_code),
        ):
            _ascii_digits(value, name, lengths=frozenset({3}))
        _boolean(self.ebiz_cross_check, "ebiz_cross_check")
        _boolean(self.srt_check, "srt_check")
        _boolean(self.round_trip, "round_trip")


@dataclass(frozen=True)
class LimousineSchedule:
    """운행 스케줄 조회 결과의 한 편.

    잔여 좌석이 등급별로 따로 온다 — 일반
    (``general_remaining_seat_count``), 자유석(``free_remaining_seat_count``),
    입석(``standing_remaining_seat_count``), 특실
    (``special_remaining_seat_count``).

    ``departure_run_order``/``arrival_run_order`` 는
    :class:`LimousineSeatInventoryQuery` 가 요구하는 정차 순서와 같은 값이라
    좌석 재고 조회로 그대로 넘기면 된다. 모든 필드가 선택 문자열이고 서버가
    빼면 ``None`` 이다. 원본 행은 ``raw`` 에 남는다.
    """
    arrival_date: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_run_order: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    transfer_division_code: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_run_order: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    general_remaining_seat_count: str | None = None
    delay_minutes: str | None = None
    free_remaining_seat_count: str | None = None
    standing_remaining_seat_count: str | None = None
    run_date: str | None = field(default=None, repr=False)
    special_remaining_seat_count: str | None = None
    train_class_code: str | None = field(default=None, repr=False)
    service_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    train_order_no: str | None = field(default=None, repr=False)
    yms_application_flag: str | None = None
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleResponse(BaseKorailResponse):
    """``lmu.scdlQry.do`` 의 응답.

    ``schedules`` 가 편 목록이고, 조건에 맞는 편이 없으면 빈 튜플이다.
    ``following_page_extension`` 이 다음 페이지가 있는지를 말하며,
    ``long_short_division_code`` 는 장·단거리 구분이다.
    """
    h_msg_txt: str | None = field(default=None, repr=False)
    following_page_extension: str | None = field(default=None, repr=False)
    long_short_division_code: str | None = None
    schedules: tuple[LimousineSchedule, ...] = ()


@dataclass(frozen=True)
class LimousineSeat:
    """좌석표의 좌석 한 자리.

    ``seat_no`` 가 전선 식별자이고 ``specification`` 이 사람이 읽는 표시다.
    ``sale_possible_flag`` 가 ``"Y"`` 인 좌석만 고를 수 있다.

    속성 코드가 셋이다 — 방향(``direction_attribute_code``), 그 밖
    (``other_attribute_code``), 요청한 속성(``requested_attribute_code``).
    마지막 것은 질의가 요구한 속성을 서버가 되울린 값이다.
    """
    direction_attribute_code: str | None = field(default=None, repr=False)
    other_attribute_code: str | None = field(default=None, repr=False)
    integrated_message: str | None = field(default=None, repr=False)
    integrated_message_code: str | None = field(default=None, repr=False)
    requested_attribute_code: str | None = field(default=None, repr=False)
    sale_possible_flag: str | None = None
    seat_no: str | None = field(default=None, repr=False)
    specification: str | None = field(default=None, repr=False)
    sequence_no: str | None = field(default=None, repr=False)
    visual_message_division_code: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    """``lms.TResidualSeatsResearch.do`` 의 응답 — 한 호차의 좌석표.

    ``seats`` 가 좌석 하나하나다. 빈 튜플은 좌석 정보가 없다는 뜻이며 정상이다.
    ``car_no`` 는 서버가 되돌려 준 호차 번호이고,
    ``seat_arrangement_code`` 와 ``car_type_code`` 는 좌석표를 그릴 때 쓴다.
    """
    h_msg_txt: str | None = field(default=None, repr=False)
    car_type_code: str | None = None
    car_no: str | None = field(default=None, repr=False)
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    seats: tuple[LimousineSeat, ...] = ()


@dataclass(frozen=True)
class LimousineRecommendedProduct:
    """열차 행에 딸려 오는 추천 상품 한 건.

    ``goods_no``(``goodsNo``)가 상품 식별자, ``goods_name``(``goodsNm``)이 표시
    이름이다. 금액이 여럿으로 온다 — 할인액·할인율, 운임(``rcvdFare``), 요금
    (``rcvdPrc``)과 그 둘째 자리(``rcvdPrc2``), 그리고 구분 코드
    (``famtPctDvCd``). 전부 선택 문자열이라 서버가 빼면 ``None`` 이다.
    """
    discount_amount: str | None = field(default=None, repr=False)
    discount_rate: str | None = field(default=None, repr=False)
    fare_amount_division_code: str | None = field(default=None, repr=False)
    goods_name: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price: str | None = field(default=None, repr=False)
    received_price_secondary: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleViewTrain:
    """좌석이동 화면이 쓰는 열차 목록의 한 행.

    앞의 :class:`LimousineSchedule` 보다 훨씬 넓다. 같은 편에 대해 화면이
    그리는 모든 것 — 등급별 예약 코드와 이름, 우회·지연 안내, 환승 연결
    가능 여부와 소요 시간, 팝업 문구, 추천 상품 목록 — 이 한 행에 실린다.

    등급 관련 값은 일반(``general_*``)과 특실(``special_*``)로 짝을 이룬다.
    ``*_secondary`` 로 끝나는 필드는 전선 키가 ``2`` 로 끝나는 짝이다 —
    ``h_gen_rsv_cd`` 옆의 ``h_gen_rsv_cd2`` 같은 것이다.

    ``recommended_products`` 는 :class:`LimousineRecommendedProduct` 의 튜플이며
    비어 있을 수 있다. 나머지는 전부 선택 문자열이라 서버가 빼면 ``None``
    이고, 원본 행은 ``raw`` 에 남는다.
    """
    detour_via_popup: str | None = field(default=None, repr=False)
    elevator_damage_control: str | None = field(default=None, repr=False)
    arrival_date: str | None = field(default=None, repr=False)
    arrival_station_code: str | None = field(default=None, repr=False)
    arrival_station_name: str | None = field(default=None, repr=False)
    arrival_consist_order: str | None = field(default=None, repr=False)
    arrival_run_order: str | None = field(default=None, repr=False)
    arrival_time: str | None = field(default=None, repr=False)
    car_type_name: str | None = field(default=None, repr=False)
    change_train_division_code: str | None = field(default=None, repr=False)
    change_train_sequence: str | None = field(default=None, repr=False)
    connection_required_time: str | None = field(default=None, repr=False)
    connection_possible_flag: str | None = field(default=None, repr=False)
    connection_received_price: str | None = field(default=None, repr=False)
    delay_sale_flag: str | None = field(default=None, repr=False)
    departure_date: str | None = field(default=None, repr=False)
    departure_station_code: str | None = field(default=None, repr=False)
    departure_station_name: str | None = field(default=None, repr=False)
    departure_consist_order: str | None = field(default=None, repr=False)
    departure_run_order: str | None = field(default=None, repr=False)
    departure_time: str | None = field(default=None, repr=False)
    detour_flag: str | None = field(default=None, repr=False)
    detour_text: str | None = field(default=None, repr=False)
    expected_delay_hours: str | None = field(default=None, repr=False)
    expected_departure_delay_count: str | None = field(
        default=None,
        repr=False,
    )
    free_reservation_code: str | None = field(default=None, repr=False)
    free_car_count: str | None = field(default=None, repr=False)
    general_room_class_name: str | None = field(default=None, repr=False)
    general_reservation_code: str | None = field(default=None, repr=False)
    general_reservation_code_secondary: str | None = field(
        default=None,
        repr=False,
    )
    information_text: str | None = field(default=None, repr=False)
    journey_reservation_code: str | None = field(default=None, repr=False)
    journey_reservation_name: str | None = field(default=None, repr=False)
    nonstop_message: str | None = field(default=None, repr=False)
    nonstop_message_text: str | None = field(default=None, repr=False)
    popup_message: str | None = field(default=None, repr=False)
    received_amount: str | None = field(default=None, repr=False)
    received_fare: str | None = field(default=None, repr=False)
    received_price_secondary: str | None = field(default=None, repr=False)
    seat_map_flag: str | None = field(default=None, repr=False)
    reservation_possible_name: str | None = field(default=None, repr=False)
    run_date: str | None = field(default=None, repr=False)
    run_time: str | None = field(default=None, repr=False)
    seat_attribute_code: str | None = field(default=None, repr=False)
    smns_train_flag: str | None = field(default=None, repr=False)
    special_discount_rate: str | None = field(default=None, repr=False)
    special_room_class_name: str | None = field(default=None, repr=False)
    special_reservation_code: str | None = field(default=None, repr=False)
    special_reservation_code_secondary: str | None = field(
        default=None,
        repr=False,
    )
    special_reservation_possible_name: str | None = field(
        default=None,
        repr=False,
    )
    station_popup_message: str | None = field(default=None, repr=False)
    standing_reservation_code: str | None = field(default=None, repr=False)
    general_train_discount_rate: str | None = field(default=None, repr=False)
    origin_train_discount_rate: str | None = field(default=None, repr=False)
    train_class_code: str | None = field(default=None, repr=False)
    train_class_name: str | None = field(default=None, repr=False)
    service_code: str | None = field(default=None, repr=False)
    train_no: str | None = field(default=None, repr=False)
    use_time_care_content: str | None = field(default=None, repr=False)
    wait_reservation_flag: str | None = field(default=None, repr=False)
    yms_application_flag: str | None = field(default=None, repr=False)
    recommended_products: tuple[LimousineRecommendedProduct, ...] = ()
    total_passenger_count: int = 0
    goods_no: str | None = field(default=None, repr=False)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class LimousineScheduleViewResponse(BaseKorailResponse):
    """``seatMovie.LimousineScheduleView`` 의 응답.

    ``schedules`` 가 열차 행 목록이고 ``trn_infos`` 가 ``null`` 이면 빈 튜플이다.

    페이지 커서가 여럿이다 — ``next_page_flag`` 가 다음 페이지 유무,
    ``next_train_no``·``next_preceding_train_no``·``next_ectb_train_no``·
    ``next_query_station_no`` 가 다음 요청에 되실을 값이다. ``result_count`` 는
    전체 건수, ``merge_reservation_possible_flag`` 는 병합예약 가능 여부다.
    """
    h_msg_txt: str | None = field(default=None, repr=False)
    next_ectb_train_no: str | None = field(default=None, repr=False)
    goods_no: str | None = field(default=None, repr=False)
    next_page_flag: str | None = None
    notice_message: str | None = field(default=None, repr=False)
    next_preceding_train_no: str | None = field(default=None, repr=False)
    next_query_station_no: str | None = field(default=None, repr=False)
    result_count: str | None = None
    next_train_no: str | None = field(default=None, repr=False)
    merge_reservation_possible_flag: str | None = None
    schedules: tuple[LimousineScheduleViewTrain, ...] = ()
