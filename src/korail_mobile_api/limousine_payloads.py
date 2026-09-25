# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""열차와 다른 공항버스 필드명은 DTO에 맞춰 별도로 구성합니다."""

from __future__ import annotations

from ._payload_helpers import _device_version_key
from .config import KorailConfig
from .limousine_models import (
    LimousineScheduleQuery,
    LimousineSeatInventoryQuery,
)


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
