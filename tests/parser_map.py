# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0

"""픽스처 이름 → 그것을 읽는 파서.

``tests/fixtures/responses/`` 의 파일은 2026-09-21 실서버 응답을 **비식별화**한
것입니다. 구조(키·중첩·``null`` 과 키 없음의 구분·목록 길이)는 원본 그대로이고,
값만 합성값입니다. 분기를 모는 것(``strResult``, ``h_msg_cd``, ``*Cd``/``*Flg``
로 끝나는 코드·플래그)은 원문입니다 — 그것이 바뀌면 파서가 다른 길로 가서
픽스처가 원본을 대표하지 못합니다.

**1차 비식별화는 망가진 채로 커밋되기 직전이었습니다.** 값을 같은 모양의
합성값으로 바꾸는 대신 자릿수와 음절을 뒤섞어, 열네 음절(``가나다라마바사아자차카타파하``)
로만 이루어진 한글 뭉치, 한국 밖의 좌표(경도 ``843.94``), 있을 수 없는 날짜
(``42622082``), 태그 이름까지 깨진 HTML, 스킴이 ``aakff://`` 인 URL 을 남겼습니다.
값 1,696개를 고쳤고, 고친 뒤 **파서 출력의 구조 서명 7,577개 노드가 수리 전과
한 글자도 다르지 않음**을 확인했습니다(모델 타입, 어떤 필드가 ``None`` 이 아닌지,
모든 컬렉션 길이).

고칠 때 **없는 사실을 지어내지 않았습니다.** 역 코드에 실제 역명을 붙이려면
코드→역명 대응표가 있어야 하는데 저장소에도 APK 리소스에도 없습니다. 추측으로
채우면 이 저장소가 "0531 번 역은 무엇이다"라고 거짓을 주장하게 되므로, 근거가
없는 값은 합성임이 드러나는 플레이스홀더(``합성역0531``, ``합성 popupMessage 문구 620``,
``https://example.invalid/synthetic/31005``)로 두었습니다. 그래서 역 목록은
**섞여 있습니다** — 1차 비식별화가 건드리지 않고 지나간 실제 역명(``가남``,
``가평``, ``강경``)은 그대로고, 뭉개진 것만 플레이스홀더입니다.

날짜·시각은 원본이 우연히 남긴 관계를 지켜서 고쳤습니다. 같은 원본값은 같은
값으로 바뀌므로 한 행의 ``h_run_dt`` 와 ``h_dpt_dt`` 는 여전히 같고, 한 행 안에서
출발이 도착보다 앞서며, ``runningCalendar`` 의 ``runDt`` 는 연속된 날짜이자
같은 행의 ``dayDvCd`` 요일과 맞습니다.

코드·플래그가 정말 원문인지는 따로 확인했습니다: ``*Cd`` 값에 뭉개진 것이 하나도
없고, ``strResult`` 는 ``SUCC``/``FAIL`` 뿐이며, ``h_msg_cd`` 13종은 모두 서버
코드 형식입니다.

한 곳은 예외입니다 — ``recent_delivery_history`` 의 ``acepCustMgFlg`` 가 ``j`` 입니다.
다른 플래그가 전부 ``Y``/``N`` 인 것을 보면 1차 비식별화가 글자 하나를 바꿔 놓은
것으로 보이지만, ``Y`` 와 ``N`` 중 무엇이었는지는 알 길이 없습니다. 고르면 그것도
지어내는 것이라 그대로 두었습니다. 이 필드는 분기를 몰지 않고 파서가 그대로
옮겨 담기만 합니다.

로그인 응답은 픽스처로 만들지 않았습니다 — 이 캡처에서 가장 개인적인 본문이고,
세션 조립은 :mod:`korail_mobile_api.session` 이 따로 합니다.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from korail_mobile_api import limousine_parsers, parsers, read_parsers
from korail_mobile_api.models import BaseKorailResponse


#: 원본 ``dict`` 대신 :class:`BaseKorailResponse` 를 받는 파서들.
WRAPPED = {
    "app_data",
    "limousine_schedules",
    "maas_menu_list",
    "maas_station_data",
    "notice",
    "seat_cars",
    "seat_inventory",
    "station_data",
    "station_info",
    "ticket_list",
    "train_calendar",
    "train_schedule",
    "transfer_stations",
    "uuid",
}


def parse_train_search(raw: Any) -> tuple[Any, Any]:
    """열차 조회 응답에는 파서가 둘 붙습니다.

    :meth:`~korail_mobile_api.client.KorailClient._search_trains` 가 하는 것과
    같은 조립입니다 — 행 목록과 메타데이터를 같은 ``raw`` 에서 따로 꺼내
    ``TrainSearchResult`` 에 담습니다. 골든이 둘 다 덮도록 여기서도 둘 다 부릅니다.
    """
    return parsers.parse_train_rows(raw), parsers.parse_train_search_metadata(raw)


PARSERS: dict[str, Callable[[Any], Any]] = {
    "app_data": parsers.parse_app_data_response,
    "cart_list": read_parsers.parse_cart_list_response,
    # 공통코드 조회는 봉투 그대로 돌려줍니다 — `KorailClient.get_common_code` 의
    # 반환 타입이 `BaseKorailResponse` 이고 전용 파서가 없습니다.
    "common_code": BaseKorailResponse.from_raw,
    "commuter_info": read_parsers.parse_commuter_info_response,
    "commuter_kind_menu": read_parsers.parse_commuter_kind_menu_response,
    "crew_request_list": read_parsers.parse_crew_request_list_response,
    "customer_trip_info": read_parsers.parse_customer_trip_info_response,
    "delay_discount_tickets": read_parsers.parse_delay_discount_ticket_response,
    "deposit_banks": read_parsers.parse_deposit_bank_response,
    "discount_coupons": read_parsers.parse_discount_coupon_response,
    "free_seat_car_info": read_parsers.parse_free_seat_car_response,
    "guide_seat_condition": read_parsers.parse_guide_seat_condition_response,
    "limousine_schedules": limousine_parsers.parse_limousine_schedule_response,
    "maas_menu_list": parsers.parse_maas_menu_list_response,
    "maas_service_details": read_parsers.parse_maas_service_detail_list_response,
    "maas_station_data": parsers.parse_station_data_response,
    "merge_seats_inquiry": read_parsers.parse_merge_seats_inquiry_response,
    "multi_child_discount_targets": (read_parsers.parse_multi_child_discount_target_response),
    "notice": parsers.parse_notice_response,
    "pass_available_dates": read_parsers.parse_pass_availability_response,
    "pass_menu": read_parsers.parse_pass_menu_response,
    "product_reservations": read_parsers.parse_product_reservation_list_response,
    "recent_delivery_history": read_parsers.parse_recent_delivery_history_response,
    "reservation_history": read_parsers.parse_reservation_history_response,
    "search_trains": parse_train_search,
    "seat_assignment_schedule": read_parsers.parse_seat_assignment_schedule_response,
    "seat_cars": parsers.parse_seat_car_list_response,
    "seat_inventory": parsers.parse_seat_inventory_response,
    "service_status": read_parsers.parse_service_status_response,
    "station_data": parsers.parse_station_data_response,
    "station_info": parsers.parse_station_info_response,
    "ticket_list": read_parsers.parse_ticket_list_response,
    "train_calendar": parsers.parse_train_calendar_response,
    "train_schedule": parsers.parse_train_schedule_response,
    "transfer_stations": parsers.parse_transfer_station_list_response,
    "trip_change_dates": read_parsers.parse_trip_change_date_response,
    "trip_menu": read_parsers.parse_trip_menu_response,
    "uuid": parsers.parse_uuid_response,
}

__all__ = ["PARSERS", "WRAPPED", "parse_train_search"]
