# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 Query 를 요청 폼으로 옮깁니다. 좌석 재고 Query 만 인원·is_arrow 의 타입을 검사하고 문자열 형식은 서버가 판정합니다."""
from __future__ import annotations

from ._payload_helpers import _device_version
from .config import KorailConfig
from .limousine_models import (
    LimousineScheduleQuery,
    LimousineSeatInventoryQuery,
)


def build_limousine_schedule_form(
    config: KorailConfig,
    query: LimousineScheduleQuery,
) -> dict[str, str]:
    """리무진 운행 스케줄 폼(NetworkApi.java:654-656, postScdlQry). 역은 역코드, 날짜·시각은 YYYYMMDD·HHMMSS 입니다. 형식 자릿수는 서버에서 검사합니다."""
    return {
        **_device_version(config),
        "Key": config.key,
        "dptDt": query.departure_date,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        # 속성명은 trnGpCd(ScdlQryIn.java:38,60). 보호된 serializer 이름의 길이만으로 전송 키의 평문을 확정할 수는
        # 없습니다(ScdlQryIn$$serializer.java:32-44). 2026-09-16 관측: 키 생략·trnGpCd=999·tmGpCd=999 모두 같은 42편; 응답은
        # trnGpCd="980". 따라서 이 표본은 요청 필터가 적용된다는 증거가 아닙니다.
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
    """리무진 좌석 재고 폼(NetworkApi.java:269-271). isArrow 는 true/false 문자열입니다.

    ctlDvCd 는 공유 DTO 의 필드이나 공항버스 생성자는 기본값 슬롯을 사용합니다 (AirportBusSeatMapViewModel.java:717,865). 열차 좌석변경 생성자
    (TrainSeatMapViewModel.java:1976)와 달리 이 폼에서는 생략합니다. 보호된 Json 설정만으로 앱의 모든 null 직렬화 동작을 단정하지 않습니다."""
    return {
        **_device_version(config),
        "Key": config.key,
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
