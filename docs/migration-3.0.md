# 3.0으로 옮기기

3.0은 2.x와 호환되지 않는 변경을 한 번에 모은 판입니다. 옛 이름의 별칭은 두지 않으므로 아래 표에 따라 코드를 고치세요.
이름과 인자만 바뀐 메서드는 같은 입력에서 2.6.1과 같은 요청(본문·헤더·순서·횟수)을 보냅니다. 이는 합성 응답으로 비교한 결과이며 실서버 확인이 아닙니다.
날짜가 붙은 검증 기록([실서버 확인 현황](status.md)의 날짜별 절, `verification-*` 문서)은 당시 이름을 그대로 둡니다. 그 기록의 옛 메서드 링크는 새 이름의 절로 이어집니다.

## 메서드 이름 {#methods}

`KorailClient` 메서드 38개의 이름을 바꿨습니다. 목록은 `list_`, 한 건은 `get_`, 읽기 전용 가능 여부 확인은 `check_`로 시작하고, 상태를 바꾸는 메서드는 하는 일을 이름으로 씁니다. 공개 메서드는 85개에서 83개가 됐습니다([제거한 API](#removed)).

| 2.x | 3.0 |
|---|---|
| `confirm_standby_hold` | [`set_standby_options`](api/reservations.md#set_standby_options) |
| `execute_station_ticket_refund` | [`refund_station_ticket`](api/payments.md#refund_station_ticket) |
| `get_cart_list` | [`list_cart_items`](api/reservations.md#list_cart_items) |
| `get_common_code` | [`get_common_codes`](api/session.md#get_common_codes) |
| `get_crew_request_list` | [`list_crew_request_reasons`](api/session.md#list_crew_request_reasons) |
| `get_customer_trip_info` | [`get_trip_preferences`](api/account.md#get_trip_preferences) |
| `get_delay_discount_tickets` | [`list_delay_discount_tickets`](api/account.md#list_delay_discount_tickets) |
| `get_deposit_banks` | [`list_deposit_banks`](api/account.md#list_deposit_banks) |
| `get_discount_card_usage_history` | [`list_discount_card_usages`](api/passes.md#list_discount_card_usages) |
| `get_discount_coupons` | [`list_discount_coupons`](api/account.md#list_discount_coupons) |
| `get_free_seat_car_info` | [`get_free_seat_cars`](api/trains.md#get_free_seat_cars) |
| `get_korail_point_summary` | [`get_point_summary`](api/account.md#get_point_summary) |
| `get_limousine_schedules` | [`list_airport_bus_schedules`](api/airport-bus.md#list_airport_bus_schedules) |
| `get_limousine_seat_inventory` | [`get_airport_bus_seat_inventory`](api/airport-bus.md#get_airport_bus_seat_inventory) |
| `get_maas_menu_list` | [`list_maas_menus`](api/airport-bus.md#list_maas_menus) |
| `get_maas_service_details` | [`list_maas_services`](api/airport-bus.md#list_maas_services) |
| `get_maas_station_data` | [`list_maas_stations`](api/airport-bus.md#list_maas_stations) |
| `get_merge_seats_inquiry` | [`get_merge_seat_options`](api/trains.md#get_merge_seat_options) |
| `get_multi_child_discount_targets` | [`list_multi_child_discount_targets`](api/account.md#list_multi_child_discount_targets) |
| `get_original_ticket_inquiry` | [`get_original_tickets`](api/account.md#get_original_tickets) |
| `get_pass_available_dates` | [`get_pass_availability`](api/passes.md#get_pass_availability) |
| `get_pbp_acceptance_specifications` | [`list_pbp_acceptances`](api/delivery-checkin.md#list_pbp_acceptances) |
| `get_price_fare_quote` | [`get_fare_quote`](api/trains.md#get_fare_quote) |
| `get_product_reservations` | [`list_product_reservations`](api/passes.md#list_product_reservations) |
| `get_recent_delivery_history` | [`list_recent_delivery_recipients`](api/delivery-checkin.md#list_recent_delivery_recipients) |
| `get_refund_commission` | [`get_refund_fee`](api/payments.md#get_refund_fee) |
| `get_reservation_history` | [`list_reservations`](api/reservations.md#list_reservations) |
| `get_seat_cars` | [`list_seat_cars`](api/trains.md#list_seat_cars) |
| `get_self_checkin_info` | [`get_self_checkin`](api/delivery-checkin.md#get_self_checkin) |
| `get_self_seat_change_info` | [`get_self_seat_change_options`](api/account.md#get_self_seat_change_options) |
| `get_station_data` | [`list_stations`](api/session.md#list_stations) |
| `get_station_info` | [`get_station_list_version`](api/session.md#get_station_list_version) |
| `get_ticket_list` | [`list_tickets`](api/account.md#list_tickets) |
| `get_transfer_stations` | [`list_transfer_stations`](api/trains.md#list_transfer_stations) |
| `get_trip_change_dates` | [`list_trip_change_dates`](api/account.md#list_trip_change_dates) |
| `reserve_limousine` | [`reserve_airport_bus`](api/airport-bus.md#reserve_airport_bus) |
| `retrieve_delivered_ticket` | [`recall_delivered_ticket`](api/delivery-checkin.md#recall_delivered_ticket) |
| `verify_station_ticket_refund` | [`check_station_ticket_refund`](api/payments.md#check_station_ticket_refund) |

```text
history = client.get_reservation_history()
tickets = client.get_ticket_list(mode="2", boarding_date_from=start, boarding_date_to=end)
fee = client.get_refund_commission(reference)
```

```python
history = client.list_reservations()
tickets = client.list_tickets(mode="2", boarding_date_from=start, boarding_date_to=end)
fee = client.get_refund_fee(reference)
```

## 간편 API {#facade}

| 2.x | 3.0 |
|---|---|
| `korail.reservations.find(pnr)` | `korail.reservations.get(pnr)` |
| `korail.tickets.refund_fee(ticket, *, companion=...)` | `korail.tickets.refund_quote(ticket, *, companion=...)` |
| `korail.tickets.all(*, page_no=1)` | `korail.tickets.all(page_no=1, *, mode="1", boarding_date_from="", boarding_date_to="")` |
| 없음 | `korail.tickets.detail(ticket, *, from_purchase_history=False)` — [`get_refund_ticket_detail`](api/payments.md#get_refund_ticket_detail)을 호출합니다. |
| `korail.login(member_no, password)` | `korail.login(member_no, password, *, input_flag=None, check_valid_pw="Y", cust_id="", etr_path="")` — [`KorailClient.login`](api/session.md#login)과 같은 옵션입니다. |

간편 API가 직접 거절하던 `ValueError`는 이제 `KorailInvalidInputError`입니다([예외](#errors)). 인자 타입이 틀리면 계속 `TypeError`입니다.

```text
hold = korail.reservations.find(pnr)
fee = korail.tickets.refund_fee(reference)
```

```python
hold = korail.reservations.get(pnr)
fee = korail.tickets.refund_quote(reference)
history = korail.tickets.all(mode="2", boarding_date_from=start, boarding_date_to=end)
```

## 제거한 API {#removed}

| 2.x | 3.0에서 쓸 것 |
|---|---|
| `get_notice(timestamp_ms)` | [`get_app_data(timestamp_ms).notice`](api/session.md#get_app_data). 공지가 없으면 `None`입니다(이전에는 필드가 모두 `None`인 응답). 요청은 같습니다. |
| `register_discount_card(request)`와 `DiscountCardPurchaseRequest`, `DiscountCardSectionRequest`, `DiscountCardAdditionalUser`, `DiscountCardPurchaseResponse` | 없습니다. 실서버에서 확인하지 못했고, 라이브러리로 결제·취소할 수 없는 구매만 만들었습니다. |
| `DiscountCardTicket` | [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference]. [`extend_discount_card`](api/passes.md#extend_discount_card)는 같은 네 값을 받고 같은 요청을 보냅니다. |
| `reserve_merge(..., job_type=...)` | 인자를 빼세요. 병합 후속 예약은 항상 `MERGE_STANDING`으로 보냅니다(2.6.2부터 다른 값은 거절했습니다). |
| `recalculate_price(..., add_to_cart=True)` | 재계산이 성공한 뒤 [`add_to_cart`](api/reservations.md#add_to_cart)를 직접 호출하세요. 2.6.2에서 추가한 `ReservationHoldResponse.cart_addition`과 `ReservationHoldResponse.cart_addition_error`도 제거했습니다. |
| `search_trains_with_transfer_fallback(..., continuation=...)` | 이 메서드는 첫 페이지만 조회합니다. 다음 페이지는 [`search_trains`](api/trains.md#search_trains)나 [`search_transfer_trains`](api/trains.md#search_transfer_trains)에 `continuation`을 넘기세요. |
| `DiscountCardScheduleResponse.following_page_exists` | 없습니다. 항상 `None`이었습니다. |

```text
recalculated = client.recalculate_price(request, add_to_cart=True)
cart = recalculated.cart_addition
notice = client.get_notice()
client.extend_discount_card(DiscountCardTicket(window, sale_date, sequence, password))
```

```python
from korail_mobile_api import CartAddRequest, OriginalTicketReference

recalculated = client.recalculate_price(request)
cart = client.add_to_cart(CartAddRequest(recalculated.pnr_no))
notice = client.get_app_data().notice
client.extend_discount_card(OriginalTicketReference(window, sale_date, sequence, password))
```

## 추가한 API {#added}

요청 바이트를 바꾸지 않는 연결 도구입니다.

- [`HoldReference`][korail_mobile_api.HoldReference]`(pnr_no, journey_count, journey_sequence=None, change_no=None)`: [`cancel_unpaid_hold`](api/reservations.md#cancel_unpaid_hold)가 홀드 대신 받습니다. `hold.reference`로 얻거나, 응답을 읽지 못한 예약의 원문에서 `HoldReference.from_raw(error.raw)`로 만듭니다. `from_raw`는 PNR(`h_pnr_no`)과 여정 수(`h_jrny_cnt`)만 요구합니다. 같은 값이면 홀드로 취소할 때와 같은 요청을 보냅니다.
- `OriginalTicketReference.from_ticket(ticket)`: 승차권 목록의 한 장에서 원표 반환일(`return_sale_date`, `MMDD`)을 판매일로 넣습니다. `YYYYMMDD`를 받는 두 메서드는 [승차권 식별자 이어 쓰기](api/account.md#ticket-identifiers)를 참고하세요.
- `FreeSeatCarRequest.from_train(train)`, `MergeSeatsInquiryRequest.from_train(train, *, selected_station_name=None, room_class_code="1", seat_attribute_code=None, passenger_count=1)`: 조회한 열차의 값을 복사하고 빠진 값은 거절합니다.
- `KorailClient`를 `with` 문으로 쓸 수 있습니다. 블록이 끝나면 `close`만 부르며 서버 로그아웃은 하지 않습니다.

```python
from korail_mobile_api import FreeSeatCarRequest, OriginalTicketReference

client.cancel_unpaid_hold(hold.reference)
info = client.get_free_seat_cars(FreeSeatCarRequest.from_train(train))
reference = OriginalTicketReference.from_ticket(client.list_tickets().reservations[0].tickets[0])
```

## import 경로와 pickle {#imports}

공개 이름은 모두 패키지 루트에서 가져옵니다.

```text
from korail_mobile_api.models import TrainSummary
from korail_mobile_api.read_payloads import MileageHistoryRequest
from korail_mobile_api.device import KorailDeviceProfile
```

```python
from korail_mobile_api import KorailDeviceProfile, MileageHistoryRequest, TrainSummary
```

- 2.x의 하위 모듈(`models`, `read_models`, `mutation_models`, `limousine_models`, `payloads`, `read_payloads`, `mutation_payloads`, `limousine_payloads`, `parsers`, `read_parsers`, `mutation_parsers`, `limousine_parsers`, `http`, `session`, `crypto`, `netfunnel`, `netfunnel_safety`, `dynapath`, `device`, `live`, `error_messages`)은 없어졌습니다. 구현은 내부 패키지로 옮겼으며 내부 경로는 공개 API가 아닙니다.
- 대기열 로거 이름 `korail_mobile_api.netfunnel`, `korail_mobile_api.netfunnel_safety`는 그대로입니다.
- 2.x에서 pickle한 응답 모델·입력 모델·`KorailConfig`(안의 `DynapathConfig` 포함)·`KorailDeviceProfile`은 3.0에서 읽을 수 없습니다. 3.0으로 다시 만드세요. 예외는 2.x가 만든 pickle도 읽습니다.

## 예외 {#errors}

- [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError]: 요청 전 입력 검사에서 거절하면 모두 이 예외입니다. `KorailProtocolError`이자 `ValueError`이므로 기존 `except KorailProtocolError`와 `except ValueError`도 잡습니다.
- `request_sent`: 모든 라이브러리 예외에 있습니다. 요청을 HTTP 전송 계층에 넘긴 뒤 전송이나 응답 해석에 실패했으면 `True`이고, 상태를 바꾸는 메서드에서는 서버가 처리했을 수 있다는 note가 붙습니다. 요청 전에 거절했으면 `None`입니다. `True`이면 다시 보내기 전에 상태를 확인하세요.
- [`KorailTransportError`][korail_mobile_api.KorailTransportError]`.status_code`: 2xx가 아닌 HTTP 응답의 상태 코드입니다. 네트워크 단계에서 실패했으면 `None`입니다.

```python
from korail_mobile_api import KorailApiError, KorailInvalidInputError, KorailTransportError

try:
    hold = client.reserve(train)
except KorailInvalidInputError:
    raise  # 요청을 보내지 않았습니다.
except KorailApiError as error:
    if isinstance(error, KorailTransportError):
        print("HTTP 상태", error.status_code)
    if error.request_sent:
        history = client.list_reservations()  # 홀드가 만들어졌는지 먼저 확인합니다.
    raise
```

## 모델과 속성 이름 {#models}

모델·속성 이름 변경(`Limousine*` → `AirportBus*` 등)은 이 절에 정리할 예정입니다. 아직 작성 중입니다.
