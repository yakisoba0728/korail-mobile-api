# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""폼 빌더가 내보내는 **이름과 순서**를 얼립니다.

``ebc4d5f`` 가 지운 것 중 저자가 "the loss worth naming" 이라 적은 것이
``tests/_read_field_contracts.py`` 910줄이고, 그것이 라우트마다 어떤 필드를 어떤
**순서**로 보내는지의 유일한 기록이었습니다. 1.2.0 이 그 계약을 전송 경로 밖으로
옮긴 뒤로 남은 것은 각 빌더의 코드뿐입니다.

여기서 고정하는 것은 값이 아니라 **키의 나열**입니다. Retrofit ``@Field`` 이름은
정확히 일치해야 하고(``txtPnrNo`` 를 ``txtPrnNo`` 로 쓰면 PNR 없는 환불이 나갑니다),
앱이 만든 순서는 장식이 아니라 ``URLEncodedUtils.format`` 이 리스트를 그대로 뱉은
결과입니다. botocore 의 ``Stubber.expected_params`` 는 딕셔너리 비교라 순서를 보지
않으므로, 표준 도구로 대체되지 않습니다.

골든을 다시 뜨려면 ``KORAIL_GOLDEN_UPDATE=1 pytest`` — 그리고 **diff 를 읽으십시오.**
전선 계약이 바뀐 것인지 빌더가 깨진 것인지는 사람만 압니다.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import canonical as c
from korail_mobile_api import mutation_payloads as mutation
from korail_mobile_api import payloads as basic
from korail_mobile_api.safety import (
    KORAIL_MUTATION_ROUTE_CATEGORIES,
    assert_mutation_form_shape,
)


GOLDEN = Path(__file__).resolve().parent / "golden" / "form_field_order.json"

#: 빌더 이름 → 정해진 입력으로 부르는 방법. 상태변경 빌더에는 그 폼이 나가는
#: 라우트를 함께 적습니다 -- 전송 경계가 그 폼을 받아 주는지도 같이 보기 위해서입니다.
_MUTATION: dict[str, tuple[Callable[[], Any], str]] = {
    "build_reservation_form": (
        lambda: mutation.build_reservation_form(c.CONFIG, c.TRAIN),
        "/classes/com.korail.mobile.certification.TicketReservation",
    ),
    "build_transfer_reservation_form": (
        lambda: mutation.build_transfer_reservation_form(c.CONFIG, [c.TRAIN, c.SECOND_TRAIN]),
        "/classes/com.korail.mobile.certification.TicketReservation",
    ),
    "build_merge_reservation_form": (
        lambda: mutation.build_merge_reservation_form(c.CONFIG, c.TRAIN, [c.LEG, c.SECOND_LEG]),
        "/classes/com.korail.mobile.certification.TicketReservation",
    ),
    "build_single_adult_reservation_form": (
        lambda: mutation.build_single_adult_reservation_form(c.CONFIG, c.TRAIN),
        "/classes/com.korail.mobile.certification.TicketReservation",
    ),
    "build_discount_card_reservation_form": (
        lambda: mutation.build_discount_card_reservation_form(
            c.CONFIG, c.TRAIN, card_no="0000000000000000"
        ),
        "/classes/com.korail.mobile.certification.TicketReservation",
    ),
    "build_standby_wait_form": (
        lambda: mutation.build_standby_wait_form(c.CONFIG, c.HOLD),
        "/classes/com.korail.mobile.reservationWait.ReservationWait",
    ),
    "build_unpaid_reservation_cancel_form": (
        lambda: mutation.build_unpaid_reservation_cancel_form(c.CONFIG, c.HOLD),
        "/classes/com.korail.mobile.reservationCancel.ReservationCancelChk",
    ),
    "build_card_payment_form": (
        lambda: mutation.build_card_payment_form(c.CONFIG, c.HOLD, c.CARD),
        "/classes/com.korail.mobile.payment.ReservationPayment",
    ),
    "build_refund_form": (
        lambda: mutation.build_refund_form(c.CONFIG, c.PAID_TICKET),
        "/classes/com.korail.mobile.refunds.RefundsRequest",
    ),
    "build_station_refund_execution_form": (
        lambda: mutation.build_station_refund_execution_form(c.CONFIG, c.STATION_REFUND),
        "/classes/com.korail.mobile.refunds.executeOnlineRefunds",
    ),
    "build_discount_card_purchase_form": (
        lambda: mutation.build_discount_card_purchase_form(c.CONFIG, c.DISCOUNT_CARD_PURCHASE),
        "/classes/com.korail.mobile.research.dcntCrdInfo.do",
    ),
    "build_discount_card_extension_query": (
        lambda: mutation.build_discount_card_extension_query(c.CONFIG, c.DISCOUNT_CARD_TICKET),
        "/classes/com.korail.mobile.reservation.dcntCrdExtn.do",
    ),
    "build_price_recalculation_form": (
        lambda: mutation.build_price_recalculation_form(c.CONFIG, c.PRICE_RECALCULATION),
        "/classes/com.korail.mobile.certification.PriceReCalculation",
    ),
    "build_cart_add_form": (
        lambda: mutation.build_cart_add_form(c.CONFIG, c.CART),
        "/classes/com.korail.mobile.cart.addCartList",
    ),
}

_READ: dict[str, Callable[[], Any]] = {
    "build_cache_query": lambda: basic.build_cache_query(timestamp_ms=1758412800000),
    "build_common_code_form": lambda: basic.build_common_code_form(c.CONFIG, "app.login.cphd"),
    "build_maas_menu_form": lambda: basic.build_maas_menu_form(c.CONFIG),
    "build_maas_station_form": lambda: basic.build_maas_station_form("001"),
    "build_seat_car_form": lambda: basic.build_seat_car_form(
        c.CONFIG, c.TRAIN, passenger_count=1, sid="SID"
    ),
    "build_seat_inventory_form": lambda: basic.build_seat_inventory_form(
        c.CONFIG, c.TRAIN, 1, passenger_count=1, sid="SID"
    ),
    "build_ticket_list_form": lambda: basic.build_ticket_list_form(c.CONFIG, 1),
    "build_train_schedule_form": lambda: basic.build_train_schedule_form(
        c.CONFIG, "20260921", "0001"
    ),
    "build_train_schedule_special_form": lambda: basic.build_train_schedule_special_form(
        c.CONFIG, c.SEARCH_QUERY, departure_name="서울", arrival_name="부산"
    ),
    "build_train_search_form": lambda: basic.build_train_search_form(
        c.CONFIG, c.SEARCH_QUERY, departure_name="서울", arrival_name="부산", sid="SID"
    ),
}

_ALL: dict[str, Callable[[], Any]] = {
    **{name: call for name, (call, _route) in _MUTATION.items()},
    **_READ,
}


def _field_order(form: Any) -> list[str]:
    if isinstance(form, dict):
        return list(form)
    return [name for name, _value in form]


def _recorded() -> dict[str, list[str]]:
    if not GOLDEN.exists():
        return {}
    return json.loads(GOLDEN.read_text())


if os.environ.get("KORAIL_GOLDEN_UPDATE") == "1":  # pragma: no cover - 사람이 부른다
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(
        json.dumps(
            {name: _field_order(call()) for name, call in sorted(_ALL.items())},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


@pytest.mark.parametrize("name", sorted(_ALL))
def test_field_names_and_order_are_unchanged(name: str) -> None:
    recorded = _recorded()
    assert name in recorded, (
        f"{name} 의 골든이 없습니다. 새 빌더라면 "
        "KORAIL_GOLDEN_UPDATE=1 pytest 로 뜨고 diff 를 읽으십시오."
    )
    assert _field_order(_ALL[name]()) == recorded[name]


def test_the_golden_has_no_entry_for_a_builder_that_is_gone() -> None:
    assert set(_recorded()) <= set(_ALL)


@pytest.mark.parametrize("name", sorted(_MUTATION))
def test_every_mutation_form_passes_the_send_boundary(name: str) -> None:
    """빌더가 만든 폼은 ``post_mutation_form`` 의 모양 단언을 통과해야 합니다.

    ``build_station_refund_execution_form`` 은 실제로는 ``V7Gateway.call`` 로 나가서
    이 단언을 거치지 않습니다(그 비대칭 자체가 기록해 둘 만한 것입니다). 여기서는
    **통과할 수 있어야 한다**는 계약만 확인합니다.
    """
    call, route = _MUTATION[name]
    assert_mutation_form_shape(route, call())


@pytest.mark.parametrize("name", sorted(_MUTATION))
def test_every_mutation_route_is_a_registered_one(name: str) -> None:
    _call, route = _MUTATION[name]
    assert route in KORAIL_MUTATION_ROUTE_CATEGORIES
