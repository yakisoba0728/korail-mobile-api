# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""리무진 연계 조회의 요청 폼 빌더.

:mod:`korail_mobile_api.limousine_models` 의 질의를 전선 키로 옮깁니다.
``validate_*`` 함수는 질의가 **정확히** 그 타입인지 확인한 뒤
``__post_init__`` 의 검사를 다시 돌립니다.

세 폼 모두 공통 ``Device``/``Version`` 을 싣습니다.
``seatMovie.LimousineScheduleView`` 는 7.0.6 앱에서 사라졌고, 그 요청을 만들던
빌더와 질의 타입도 함께 없어졌습니다 — 보낼 수 없는 라우트의 폼을 짓는 함수였기
때문입니다. 저장해 둔 6.5.0 응답을 해석하는 쪽은 남아 있습니다
(:func:`~korail_mobile_api.limousine_parsers.parse_limousine_schedule_view_response`).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from .config import KorailConfig
from .limousine_models import (
    LimousineScheduleQuery,
    LimousineSeatInventoryQuery,
)


QueryT = TypeVar("QueryT")


def _validated_query(
    query: object,
    expected: type[QueryT],
    validator: Callable[[QueryT], None],
    name: str,
) -> QueryT:
    if type(query) is not expected:
        raise TypeError(
            f"{name} query must be exactly {expected.__name__}"
        )
    validated = cast(QueryT, query)
    validator(validated)
    return validated


# payloads.py 에 같은 함수가 있지만 import 하지 않습니다. 이 모듈은 pyright strict
# 목록에 있고 strict 는 사적 이름의 모듈 간 사용을 거부합니다(reportPrivateUsage).
# 제대로 된 답은 형제 모듈들이 함께 쓰는 내부 유틸 모듈이고, 그것은 모듈 분할을
# 다시 자를 때 할 일입니다.
def _device_version(config: KorailConfig) -> dict[str, str]:
    """The ``Device`` and ``Version`` pair every read form here starts with."""
    return {"Device": config.device, "Version": config.version}


def validate_limousine_schedule_query(
    query: object,
) -> LimousineScheduleQuery:
    """``query`` 가 정확히 :class:`LimousineScheduleQuery` 인지 확인하고 돌려줍니다."""
    return _validated_query(
        query,
        LimousineScheduleQuery,
        LimousineScheduleQuery.__post_init__,
        "schedule",
    )


def validate_limousine_seat_inventory_query(
    query: object,
) -> LimousineSeatInventoryQuery:
    """``query`` 가 정확히 :class:`LimousineSeatInventoryQuery` 인지 확인하고
    돌려줍니다.

    :func:`validate_limousine_schedule_query` 와 같은 규칙입니다.
    """
    return _validated_query(
        query,
        LimousineSeatInventoryQuery,
        LimousineSeatInventoryQuery.__post_init__,
        "seat inventory",
    )


def build_limousine_schedule_form(
    config: KorailConfig,
    query: LimousineScheduleQuery,
) -> dict[str, str]:
    """``lmu.scdlQry.do`` 의 운행 스케줄 조회 폼을 만듭니다.

    ``BusReservationService.java:27`` 을 인용하던 자리입니다. 7.0.6 에 그
    클래스는 없고, 같은 라우트 선언은
    ``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:654-656``
    의 ``postScdlQry()`` 입니다 — ``@FormUrlEncoded`` + ``@POST`` 에
    ``@FieldMap Map<String, String>`` 이라, 이 빌더가 폼을 만드는 것 자체는
    거기서 확인됩니다. 필드 이름·분기가 옛 클래스와 같다는 뜻은 아닙니다.
    역은 역이름이 아니라 4자리 역코드
    (``dptRsStnCd``/``arvRsStnCd``)이고, 날짜는 ``YYYYMMDD``, 시각은
    ``HHMMSS`` 입니다.
    """
    query = validate_limousine_schedule_query(query)
    return {
        **_device_version(config),
        "Key": config.key,
        "dptDt": query.departure_date,
        "dptRsStnCd": query.departure_station_code,
        "arvRsStnCd": query.arrival_station_code,
        # 6.5.0 의 @Field("tmGpCd") 가 아니라 7.0.6 ScdlQryIn 의 trnGpCd 다. 이 속성엔
        # @SerialName 이 없고(개명은 Device/Version/Key/lang 뿐), serializer 13개 이름의
        # AlienGuard 암호문 길이(= 평문 길이) [6,7,3,4,5,10,10,7,8,5,5,9,11] 이 공통 4개와
        # 속성 9개 이름 길이에 순서대로 맞는다. 속성 9칸 중 7자는 trnGpCd 자리 하나뿐이고
        # 6자 칸은 없다.
        # analysis/jadx/sources/com/korail/talk/network/model/ScdlQryIn.java:38,60
        # analysis/jadx/sources/com/korail/talk/network/model/ScdlQryIn$$serializer.java:32-44
        # 2026-09-16 실서버: 서버는 이 값으로 거르지 않는다(키 없음·trnGpCd=999·
        # tmGpCd=999 가 같은 42편). 응답 행은 trnGpCd="980" 을 싣는다.
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
    """``lms.TResidualSeatsResearch.do`` 의 좌석 재고 조회 폼을 만듭니다.

    ``BusReservationService.java:31`` 을 인용하던 자리입니다. 7.0.6 에 그
    클래스는 없고, 같은 라우트 선언은
    ``analysis/jadx/sources/com/korail/talk/network/NetworkApi.java:269-271``
    의 ``postAirportBusTResidualSeatsResearch()`` 입니다(``@FormUrlEncoded``
    + ``@POST`` + ``@FieldMap Map<String, String>``, 응답 DTO 는
    ``TResidualSeatsResearchOut``). 필드 이름·분기가 옛 클래스와 같다는 뜻은
    아닙니다. 두 값만 문자열이 아닌 파이썬 값에서
    옵니다 — ``totPsgCnt`` 는 ``str(int)``, ``isArrow`` 는 ``"Y"``/``"N"`` 이
    아니라 ``"true"``/``"false"`` 입니다.

    ``TResidualSeatsResearchIn`` 은 ``ctlDvCd`` 필드도 선언하지만(``@SerialName``
    붙은 15번째 필드, 전부 널 허용) 이 폼은 일부러 보내지 않습니다. 이 DTO 는
    열차 좌석 재고(``research.TResidualSeatsResearch.do``)와 공유되는데
    (``analysis/reports/src-verification/route-map.tsv:24-25``,
    ``NetworkApi.java:271,741``), 두 화면의 실제 생성 지점을 비교하면 값이 갈린다:
    열차 쪽 ``TrainSeatMapViewModel.java:1976`` 는 좌석변경 모드에 따라 실제
    ``ctlDvCd`` 문자열을 채우지만, 리무진(공항버스) 쪽
    ``AirportBusSeatMapViewModel.java:865``(그리고 초기화 시점의 :717)는 항상
    ``null`` 을 넘긴다 — 뒤에 붙는 정수 마스크(``28672``/``32767``)가 ``ctlDvCd``
    슬롯(비트 ``16384``)을 매번 "기본값 사용"으로 표시하기 때문이다. 서버로 가는
    ``JsonObject`` 에서 ``null`` 필드는 폼 플래트닝 규칙상 실리지 않으므로(§2),
    이 폼에 ``ctlDvCd`` 를 넣지 않는 쪽이 7.0.6 리무진 화면이 실제로 보내는 폼과
    일치한다. (이전 W4 패스가 "도달 불가"로 보류했던 항목을 이번에 위 호출부
    비교로 확정했다.)
    """
    query = validate_limousine_seat_inventory_query(query)
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
        "gdNo": query.product_no,
        "isArrow": "true" if query.is_arrow else "false",
    }


