# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""폼 빌더에 넣는 **정해진 입력**.

값은 전부 지어낸 것이고 아무것도 가리키지 않습니다 — 골든이 고정하는 것은 값이
아니라 **어떤 이름이 어떤 순서로 나가는가** 이기 때문입니다. 실제 계정·실제 카드·
실제 PNR 은 여기 있어서는 안 됩니다.

``ebc4d5f`` 가 지운 ``tests/_read_field_contracts.py`` 910줄이 하던 일의 자리입니다.
그쪽은 라우트마다 필드 이름과 **순서**를 표로 들고 있었고, 그 계약이 1.2.0 에서
전송 경로 밖으로 나간 뒤로는 그 표가 유일한 기록이었습니다. botocore 의
``Stubber.expected_params`` 는 딕셔너리 비교라 순서를 보지 않으므로, 표준 도구로는
대체되지 않는 것이었습니다.
"""

from __future__ import annotations

from korail_mobile_api import (
    CardPayment,
    CartAddRequest,
    DiscountCardPurchaseRequest,
    DiscountCardSectionRequest,
    DiscountCardTicket,
    KorailConfig,
    KorailPassengerCounts,
    KorailSeatAssignment,
    PaidTicket,
    PriceRecalculationRequest,
    PriceRecalculationRow,
    ReservationHoldResponse,
    StationRefundExecutionRequest,
    TrainScheduleItem,
    TrainSearchQuery,
    TrainSummary,
)


CONFIG = KorailConfig()

def _train(
    train_no: str, departure: str, arrival: str, depart_at: str, arrive_at: str
) -> TrainSummary:
    return TrainSummary(
        train_no=train_no,
        train_group_code="100",
        departure_station_code=departure,
        arrival_station_code=arrival,
        departure_date="20260921",
        departure_time=depart_at,
        arrival_time=arrive_at,
        run_date="20260921",
        train_class_code="00",
        departure_run_order="000001",
        arrival_run_order="000015",
        departure_construction_order="000001",
        arrival_construction_order="000015",
        general_reservation_code="11",
        special_reservation_code="11",
        standing_reservation_code="00",
        merge_seat_application_flag="A",
    )


TRAIN = _train("0001", "0001", "0015", "080000", "100000")
SECOND_TRAIN = _train("0002", "0015", "0030", "110000", "130000")


def _leg(departure: str, arrival: str, depart_at: str, arrive_at: str) -> TrainScheduleItem:
    return TrainScheduleItem(
        train_no="0001",
        train_group_code="100",
        train_class_code="00",
        run_date="20260921",
        departure_date="20260921",
        departure_time=depart_at,
        arrival_date="20260921",
        arrival_time=arrive_at,
        departure_station_code=departure,
        arrival_station_code=arrival,
        departure_construction_order="000001",
        arrival_construction_order="000015",
        departure_run_order="000001",
        arrival_run_order="000015",
        general_reservation_code="11",
        special_reservation_code="11",
        standing_reservation_code="00",
    )


LEG = _leg("0001", "0015", "080000", "090000")
SECOND_LEG = _leg("0015", "0030", "090000", "100000")

PASSENGERS = KorailPassengerCounts(adult=1)

SEAT = KorailSeatAssignment(car_no=1, seat_no="1A")

HOLD = ReservationHoldResponse(
    str_result="SUCC",
    pnr_no="0000000001",
    window_no="0001",
    received_amount="8400",
    journey_count="1",
    temporary_job_sequence_1="1",
)

PAID_TICKET = PaidTicket(
    pnr_no="0000000001",
    sale_date="20260921",
    sale_window_no="0001",
    sale_sequence="0001",
    return_password="0000",
    train_no="0001",
)

#: PG 가 거절할 모양의 지어낸 번호. 실제 카드가 아닙니다.
CARD = CardPayment(
    card_number="0000000000000000",
    card_password="00",
    card_expire="3012",
    birthday="000101",
    card_type="J",
)

CART = CartAddRequest(pnr_no="0000000001")

DISCOUNT_CARD_TICKET = DiscountCardTicket(
    sale_window_no="0001",
    sale_date="20260921",
    sale_sequence="0001",
    return_password="0000",
)

DISCOUNT_CARD_PURCHASE = DiscountCardPurchaseRequest(
    card_kind_management_no="0001",
    customer_no="0000000000",
    validity_start_date="20260921",
    usable_trip_count="2",
    sections=(
        DiscountCardSectionRequest(
            run_date="20260921",
            train_no="0001",
            departure_station_code="0001",
            arrival_station_code="0015",
        ),
    ),
)

PRICE_RECALCULATION = PriceRecalculationRequest(
    pnr_no="0000000001",
    rows=(
        PriceRecalculationRow(
            passenger_type_code="1",
            room_class_code="1",
            discount_kind_code="000",
        ),
    ),
)

STATION_REFUND = StationRefundExecutionRequest(
    pnr_no="0000000001",
    original_sale_date="20260921",
    original_sale_window_no="0001",
    original_sale_sequence="0001",
    original_return_password="0000",
    refund_division_code="1",
    refund_reason_code="1",
    ticket_kind_code="1",
    customer_phone="01000000000",
    refund_amount="8400",
    refund_fee="400",
    customer_name="홍길동",
)

SEARCH_QUERY = TrainSearchQuery(
    departure_station_code="0001",
    arrival_station_code="0015",
    departure_date="20260921",
)
