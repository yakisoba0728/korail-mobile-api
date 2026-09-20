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

수리는 **두 번에 걸쳐** 이루어졌고, 첫 번째는 끝나지 않았습니다. 오염을 키 이름의
끝자리로 찾았기 때문입니다 — ``h_dpt_tm`` 은 고쳤는데 바로 옆 ``h_dpt_tm_qb`` 의
``94:45`` 는 남았고, ``runDt1`` 도 ``boarding_date_start`` 도 그랬습니다. 개수와
순번은 아예 한 종류로 세지도 않아서 잔여석 305,082 석과 6억 건짜리 조회가 남아
있었습니다. 두 번째에는 추측을 그만두고 픽스처의 **키 326개를 전수로 뽑아**
하나씩 읽었습니다. 망가진 패스 직후의 상태와 견주면 값 2,018개가 바뀌었습니다.

고친 뒤 **파서 출력의 구조 서명이 수리 전과 한 글자도 다르지 않음**을 확인했습니다
(모델 타입, 어떤 필드가 ``None`` 이 아닌지, 모든 컬렉션 길이). 다만 이 확인은
망가진 입력 위에서 뜬 기준선과의 비교이므로, **값 오염은 원리상 여기에 걸리지
않습니다** — 고친 값이 전부 모델로 그대로 흘러가는 것이라 구조가 움직이지 않기
때문입니다. 값 쪽을 보는 것은 ``tests/test_parser_contracts.py`` 의 가드 여섯입니다.

두 번째 수리는 값 하나씩이 아니라 **행 단위**로 했습니다. 그렇게 하지 않으면
잔여석 372 석이 전체 353 석짜리 열차에 들어갑니다. 지금은 출발 순번 < 도착 순번,
잔여석 <= 전체 좌석, 시작 위치 비율 < 끝 위치 비율, 쪽수 <= 건수가 성립합니다.
``h_dpt_tm_qb`` 는 ``h_dpt_tm`` 에서 끌어냈습니다 — ``h_trn_no_qb == h_trn_no`` 가
모든 행에서 성립하는 것을 먼저 확인했으므로, 이것은 지어낸 것이 아니라 데이터를
읽은 것입니다.

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

코드·플래그가 정말 원문인지는 따로 확인했습니다: ``strResult`` 는 ``SUCC``/``FAIL``
뿐이고, ``h_msg_cd`` 13종은 모두 서버 코드 형식입니다. ``*Cd`` 쪽 확인은 **한글이
뭉개졌는지만** 보았고, 그래서 자릿수가 섞인 코드 하나를 놓쳤습니다(아래).

**지어내지 않기로 한 자리가 넷 있습니다.** 날짜를 합성하는 것은 API 에 대해
아무것도 주장하지 않지만, 코드 칸에 값을 넣는 것은 API 의 어휘를 지어내는
것입니다. 넷 다 분기를 몰지 않고 파서가 그대로 옮겨 담기만 합니다.

* ``recent_delivery_history`` 의 ``acepCustMgFlg`` 가 ``j`` 입니다. 다른 플래그가
  전부 ``Y``/``N`` 인 것을 보면 글자 하나가 바뀐 것이지만, 둘 중 무엇이었는지는
  알 길이 없습니다.
* ``seat_inventory`` 의 ``car_tp_cd`` 가 ``50564108`` 입니다. 차량 종류 코드가
  여덟 자리일 리 없지만, 원래 무엇이었는지 알 수 없고 이 저장소 어디에도
  차량 종류 코드 목록이 없습니다.
* ``search_trains`` 의 ``h_train_disc_origin_rt`` 가 ``Y``/``N`` 입니다. 짝이 되는
  ``h_train_disc_gen_rt`` 는 숫자인데 이쪽만 플래그 모양이라, 둘이 뒤바뀐 것인지
  원래 그런 것인지 판단할 근거가 없습니다.
* ``pass_available_dates`` 의 ``eng_cd_val`` 이 다섯 자리 숫자입니다. 짝인
  ``kor_cd_val`` 이 역명(``서울``, ``대전``)이라 영문명이 와야 할 것 같지만,
  로마자 표기를 적으면 "이 API 가 그렇게 돌려준다"고 주장하게 됩니다.

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
