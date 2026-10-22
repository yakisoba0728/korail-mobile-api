# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""공항버스·부가서비스 모델입니다. 공항버스 응답의 서버 코드는 알려지지 않은 값도 보존하기 위해 str로 둡니다."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..common.models import BaseKorailResponse
from ..trains.models import SeatWindow


@dataclass(frozen=True)
class LimousineStop:
    """공통 코드 조회에서 짝지은 공항버스 정류장 코드와 이름입니다."""

    code: str
    name: str


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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)
    # rcvdPrc 선언: ScdlQryOutTrain.java:40,389.
    #: 표시용 운임 문자열(``rcvdPrc``)입니다.
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
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class LimousineSeatInventoryResponse(BaseKorailResponse):
    """공항버스 한 호차의 좌석표와 배치 정보를 담습니다.

    응답 형식은 열차 좌석 재고와 같으며, 창문 위치는 같은 ``SeatWindow``로 담습니다. 좌석 목록이 없거나 ``null``이면
    ``seats``는 빈 튜플입니다."""

    # 일반 좌석 재고와 TResidualSeatsResearchOut 을 공유합니다(NetworkApi.java:271,741). 배치·배너·창측 위치의 선언은
    # TResidualSeatsResearchOut.java:29,34-35,114,134,138 참고.

    car_type_code: str | None = None
    car_no: str | None = None
    seat_arrangement_code: str | None = None
    up_down_division_code: str | None = None
    layout_type: str | None = None
    vr_banner_url: str | None = None
    windows: tuple[SeatWindow, ...] = ()
    seats: tuple[LimousineSeat, ...] = ()


@dataclass(frozen=True)
class MaasMenuItem:
    """부가서비스 메뉴 한 항목과 역 선택 조건을 담습니다."""

    active: str | None = None
    additional_service_code: str | None = None
    app_data: str | None = None
    icon_off: str | None = None
    icon_on: str | None = None
    info: str | None = None
    login_required: str | None = None
    name: str | None = None
    popup_image: str | None = None
    menu_type: str | None = None
    url: str | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)

    @property
    def uses_station_selection(self) -> bool:
        """메뉴가 역 선택을 사용하는지 판정합니다.

        ``active``가 ``"Y"``이고, ``menu_type``이 ``"N"``이 아니고, ``app_data``가 비어 있지 않으면서 ``"N"``도 아니고,
        ``additional_service_code``가 있을 때 ``True``입니다."""
        return (
            self.active == "Y"
            and self.menu_type != "N"
            # appData='N'만 역 선택에서 제외합니다. 실서버 관측: 'C'(604)는 역 15개, 'N'(001)은 0개, 'Y'·'M30'은 25~111개였으므로 Y·M10·M30만 허용하는
            # 방식으로 제한하지 않습니다.
            and self.app_data not in (None, "", "N")
            and isinstance(self.additional_service_code, str)
            and bool(self.additional_service_code.strip())
        )


@dataclass(frozen=True)
class MaasMenuListResponse(BaseKorailResponse):
    """부가서비스 메뉴 목록을 담습니다."""

    items: tuple[MaasMenuItem, ...] = ()
    departure_elevator_url: str | None = None
    departure_navigation_url: str | None = None
    departure_parking_url: str | None = None
    arrival_elevator_url: str | None = None
    arrival_bus_info_url: str | None = None
    arrival_parking_url: str | None = None
    arrival_baggage_transfer_robot_url: str | None = None


@dataclass(frozen=True)
class MaasServiceDetailInfo:
    """부가서비스의 상품·이용·결제 상세를 담습니다."""

    additional_service_request_no: str | None = None
    booking_time: str | None = None
    branch_name: str | None = None
    partner_name: str | None = None
    delivery_datetime: str | None = None
    drop_times: str | None = None
    dropoff_name: str | None = None
    image: str | None = None
    name: str | None = None
    option_name: str | None = None
    pickup_name: str | None = None
    pickup_place: str | None = None
    pickup_times: str | None = None
    reservation_date: str | None = None
    return_datetime: str | None = None
    start_datetime: str | None = None
    cancel_deadline_date: str | None = None
    cancel_return_amount: str | None = None
    cancel_return_fee: str | None = None
    goods_sequence: str | None = None
    intermediate_value: str | None = None
    received_amount: str | None = None
    reservation_status_name: str | None = None
    reservation_passenger_name: str | None = None
    settlement_deadline_date: str | None = None
    settlement_deadline_datetime: str | None = None
    settlement_status_code: str | None = None
    settlement_status_name: str | None = None
    total_settlement_amount: str | None = None
    usage_period_content: str | None = None
    entity_one: tuple[Mapping[str, object], ...] = field(default=(), compare=False)
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MaasServiceDetail:
    """신청한 부가서비스 한 건과 그 상세를 담습니다."""

    additional_service_division_code: str | None = None
    additional_service_goods_code: str | None = None
    additional_service_id: str | None = None
    marketing_entity_id: str | None = None
    marketing_entity_name: str | None = None
    additional_service_name: str | None = None
    progress_status_code: str | None = None
    request_no: str | None = None
    passenger_reference_content: str | None = None
    partner_reservation_no: str | None = None
    delivery_close_time: str | None = None
    delivery_start_time: str | None = None
    lead_message_1: str | None = None
    lead_message_2: str | None = None
    pnr_no: str | None = None
    request_date: str | None = None
    request_quantity: str | None = None
    reservation_station_code_name: str | None = None
    reservation_specification_url: str | None = None
    usage_close_date: str | None = None
    usage_start_date: str | None = None
    detail_info: MaasServiceDetailInfo | None = None
    raw: Mapping[str, object] = field(default_factory=dict[str, object], compare=False)


@dataclass(frozen=True)
class MaasServiceDetailListResponse(BaseKorailResponse):
    """신청한 부가서비스 목록을 담습니다."""

    details: tuple[MaasServiceDetail, ...] = ()
