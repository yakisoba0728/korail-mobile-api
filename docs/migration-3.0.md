# 3.0으로 옮기기

3.0은 2.x와 호환되지 않는 변경을 한 번에 모은 판입니다. 옛 이름의 별칭은 두지 않으므로 아래 표에 따라 코드를 고치세요.
이름과 인자만 바뀐 메서드는 같은 입력에서 2.6.1 캡처의 정규화된 URL·본문 필드·헤더·순서·횟수와 비교했습니다. 합성 응답으로 검사한 범위이며 모든 인코딩 변형의 바이트 동일성이나 실서버 수용의 증거는 아닙니다.
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
| `Korail.logged_in(member_no, password, ...)` | 기존 설정·transport 옵션에 `input_flag=None`, `check_valid_pw="Y"`, `cust_id=""`, `etr_path=""` 전달을 추가합니다. |
| `korail.reservations.cancel(hold)` | `HoldReference`도 받으며 `check_first=True`가 기본입니다. `False`이면 확인만 생략하고 실제 취소를 한 번 보냅니다. |
| `korail.reservations.create(train, ...)` | `seats=None`, `seat_attribute_code=None`을 기존 `reserve` 규칙대로 전달합니다. 지정 좌석은 `SEAT_DESIGNATED`를 명시해야 합니다. |

간편 API가 직접 거절하던 `ValueError`는 이제 `KorailInvalidInputError`입니다([예외](#errors)). 잘못된 역 값도 조회 전 이 예외로 거절하며, 없는 키워드 등 Python 호출 시그니처 위반은 계속 `TypeError`입니다. 추가 요청·자동 재로그인·좌석 조회·재시도는 하지 않습니다([편의 흐름](guide/convenience.md)).

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
| `CartItem.usage_window` | 없습니다. 쓰이지 않던 필드입니다. |

```text
recalculated = client.recalculate_price(request, add_to_cart=True)
cart = recalculated.cart_addition
notice = client.get_notice()
client.extend_discount_card(DiscountCardTicket(window, sale_date, sequence, password))
```

```python
from korail_mobile_api import CartAddRequest, OriginalTicketReference

recalculated = client.recalculate_price(request)
cart = client.add_to_cart(CartAddRequest(pnr_no=recalculated.pnr_no))
notice = client.get_app_data().notice
client.extend_discount_card(
    OriginalTicketReference(
        sale_window_no=window, sale_date=sale_date, sale_sequence=sequence, return_password=password
    )
)
```

## 추가한 API {#added}

요청 바이트를 바꾸지 않는 연결 도구입니다.

- [`HoldReference`][korail_mobile_api.HoldReference]`(*, pnr_no, journey_count, journey_sequence=None, change_no=None)`: [`cancel_unpaid_hold`](api/reservations.md#cancel_unpaid_hold)가 홀드 대신 받습니다. `hold.reference`로 얻거나, 응답을 읽지 못한 예약의 원문에서 `HoldReference.from_raw(error.raw)`로 만듭니다. `from_raw`는 PNR(`h_pnr_no`)과 여정 수(`h_jrny_cnt`)만 요구합니다. 같은 값이면 홀드로 취소할 때와 같은 요청을 보냅니다.
- `OriginalTicketReference.from_ticket(ticket)`: 승차권 목록의 한 장에서 원표 반환일(`return_sale_date`, `MMDD`)을 판매일로 넣습니다. `YYYYMMDD`를 받는 두 메서드는 [승차권 식별자 이어 쓰기](api/account.md#ticket-identifiers)를 참고하세요.
- `OriginalTicketReference.from_sale_ticket(ticket)`: `TicketListTicket.sale_date`를 ASCII 숫자 8자리 그대로 복사해 `YYYYMMDD`를 받는 수령자·PBP 조회에 씁니다. 기존 `from_ticket`의 MMDD 의미는 유지하며 날짜 변환·미확인 경로 선택은 하지 않습니다.
- `AirportBusSeatInventoryQuery.from_schedule(schedule, *, passenger_count=1)`: 조회한 운행 편의 식별값을 좌석 조회 입력으로 옮깁니다([아래 예](#response-attributes)).
- `DynapathRequestContext`에 보낼 본문 바이트 `body`와 `app_version`이 들어갑니다. 직접 만든 `token_provider`가 읽을 수 있습니다.
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
- `BaseKorailResponse.from_raw`와 상속 factory는 문자열 키 `dict`의 봉투만 구성합니다. 도메인 필드를 파싱하지 않으며 필수 도메인 인자가 더 필요한 하위 클래스는 원래 `TypeError`를 cause로 가진 `KorailProtocolError`입니다. 직접 생성자나 typed client 조회의 계약과 구별하세요.
- 일부 여정만 정산 좌석을 제공하거나 선언 여정 수와 행 수가 모순되면 새 홀드의 `received_amount=None`입니다. 원문·취소 참조는 보존하고 부분합을 청구하지 않습니다. 총액만 있는 응답 등의 fallback은 [결제 금액 규칙](guide/payments.md#card-payment)을 따릅니다.

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

이름만 바뀌었습니다. 읽는 전송 키, 값, 누락·`null` 규칙과 요청 바이트는 같습니다.

### 클래스 {#model-classes}

| 2.x | 3.0 |
|---|---|
| `LimousineStop` | [`AirportBusStop`][korail_mobile_api.AirportBusStop] |
| `LimousineSchedule` | [`AirportBusSchedule`][korail_mobile_api.AirportBusSchedule] |
| `LimousineScheduleQuery` | [`AirportBusScheduleQuery`][korail_mobile_api.AirportBusScheduleQuery] |
| `LimousineScheduleResponse` | [`AirportBusScheduleResponse`][korail_mobile_api.AirportBusScheduleResponse] |
| `LimousineSeat` | [`AirportBusSeat`][korail_mobile_api.AirportBusSeat] |
| `LimousineSeatInventoryQuery` | [`AirportBusSeatInventoryQuery`][korail_mobile_api.AirportBusSeatInventoryQuery] |
| `LimousineSeatInventoryResponse` | [`AirportBusSeatInventoryResponse`][korail_mobile_api.AirportBusSeatInventoryResponse] |

2.x `limousine_models` 모듈의 `LIMOUSINE_CAR_NO`, `LIMOUSINE_ROOM_CLASS_CODE`, `LIMOUSINE_SEAT_ATTRIBUTE_CODE`는 내부 상수 `AIRPORT_BUS_*`가 됐으며 공개 API가 아닙니다. 값은 같습니다.

### 입력 모델 필드 {#request-fields}

| 2.x | 3.0 |
|---|---|
| `TrainSearchQuery.departure_station_code` | `TrainSearchQuery.departure_station` |
| `TrainSearchQuery.arrival_station_code` | `TrainSearchQuery.arrival_station` |

역 이름이나 숫자로만 된 역 코드를 받는 동작은 같습니다. 문자열이 아닌 값을 거절하는 오류 문구도 새 이름을 씁니다(예: `arrival_station must be a string`).

### 응답 모델 속성 {#response-attributes}

같은 전송 키를 읽는 필드는 모든 모델에서 한 이름을 씁니다. 아래 47개 필드의 이름이 바뀌었습니다.

| 모델 | 2.x | 3.0 | 전송 키 |
|---|---|---|---|
| `AirportBusSchedule` | `service_code` | `train_group_code` | `trnGpCd` |
| `AirportBusSchedule` | `train_class_code` | `settlement_train_class_code` | `stlbTrnClsfCd` |
| `CartItem` | `service_code` | `additional_service_code` | `addSrvDvCd` |
| `CustomerTripInfo` | `train_classification_code` | `train_class_code` | `trnClsfCd` |
| `DelayDiscountTicketListResponse` | `current_page` | `page_no` | `h_page_no` |
| `DiscountCardScheduleTrain` | `arrival_station_order` | `arrival_construction_order` | `arvStnConsOrdr` |
| `DiscountCardScheduleTrain` | `departure_station_order` | `departure_construction_order` | `dptStnConsOrdr` |
| `DiscountCoupon` | `expiration_date` | `management_close_date` | `h_fdcert_mg_cls_dt` |
| `DiscountCoupon` | `start_date` | `management_start_date` | `h_fdcert_mg_st_dt` |
| `DiscountCouponListResponse` | `current_page` | `page_no` | `h_page_no` |
| `MaasServiceDetail` | `additional_service_division_code` | `additional_service_code` | `addSrvDvCd` |
| `MaasServiceDetail` | `request_no` | `additional_service_request_no` | `addSrvReqNo` |
| `MaasServiceDetailInfo` | `cancel_deadline_date` | `cancellation_deadline` | `strCncDlnDt` |
| `MaasServiceDetailInfo` | `cancel_return_amount` | `cancellation_return_amount` | `strCncRetAmt` |
| `MaasServiceDetailInfo` | `cancel_return_fee` | `cancellation_fee` | `strCncRetFee` |
| `MaasServiceDetailInfo` | `settlement_deadline_date` | `settlement_deadline` | `strStlDlnDt` |
| `MaasServiceDetailInfo` | `usage_period_content` | `usage_period` | `strUtlTrmCont` |
| `OriginalTicket` | `passenger_type_division_code` | `passenger_type_code` | `psgTpDvCd` |
| `OriginalTicketSeat` | `assign_sequence` | `assignment_sequence` | `asgnSqno` |
| `PassScheduleTrain` | `commuter_use_terminal_code` | `commuter_period_code` | `h_cmtr_utl_trm_cd` |
| `ProductDetailResponse` | `cancellation_amount` | `cancellation_return_amount` | `strCncRetAmt` |
| `ProductDetailResponse` | `reservation_status` | `reservation_status_name` | `strRsvSttNm` |
| `ProductDetailResponse` | `total_amount` | `total_settlement_amount` | `strTotStlAmt` |
| `ProductReservation` | `payment_deadline` | `settlement_deadline` | `strStlDlnDt` |
| `ProductReservation` | `payment_status` | `settlement_status_code` | `strStlSttCd` |
| `ProductReservation` | `reservation_status` | `reservation_status_name` | `strRsvSttNm` |
| `ReceiptPayment` | `card_no` | `settlement_card_no` | `h_stl_crd_no` |
| `ReservationHistoryPassenger` | `discount_no` | `discount_proof_no` | `h_dcsp_no` |
| `ReservationHistoryPassenger` | `discount_no_2` | `discount_proof_no_2` | `h_dcsp_no2` |
| `ReservationHistoryPassenger` | `passenger_count_per_info` | `passenger_count` | `h_psg_info_per_prnb` |
| `ReservationHistoryTrain` | `arrival_station` | `arrival_station_name` | `h_arv_rs_stn_nm` |
| `ReservationHistoryTrain` | `departure_station` | `departure_station_name` | `h_dpt_rs_stn_nm` |
| `ReservationHistoryTrain` | `prepayment_target_flag` | `pre_settlement_target_flag` | `h_pre_stl_tgt_flg` |
| `ReservationPaymentTicket` | `return_no` | `ticket_return_no` | `h_tk_ret_no` |
| `SelfSeatChangeReason` | `reason_text` | `forced_sale_reason_text` | `frcSaleRsnCont` |
| `SelfSeatChangeStation` | `general_remaining_seats` | `general_remaining_seat_count` | `gnrmRestSeatNum` |
| `SelfSeatChangeStation` | `special_remaining_seats` | `special_remaining_seat_count` | `sprmRestSeatNum` |
| `TicketReceipt` | `arrival_station` | `arrival_station_name` | `h_arv_rs_stn_nm` |
| `TicketReceipt` | `departure_station` | `departure_station_name` | `h_dpt_rs_stn_nm` |
| `TicketReceipt` | `seat_class_name` | `room_class_name` | `h_psrm_cl_nm` |
| `TrainScheduleItem` | `remaining_standing_count` | `standing_remaining_seat_count` | `restStndNum` |
| `TrainScheduleResponse` | `standard_train_class_code` | `settlement_train_class_code` | `stlbTrnClsfCd` |
| `TrainScheduleStop` | `planned_arrival_date` | `arrival_date` | `arvDt` |
| `TrainScheduleStop` | `planned_arrival_time` | `arrival_time` | `arvTm` |
| `TrainScheduleStop` | `planned_departure_date` | `departure_date` | `dptDt` |
| `TrainScheduleStop` | `planned_departure_time` | `departure_time` | `dptTm` |
| `TrainSearchMetadata` | `product_no` | `goods_no` | `h_gd_no` |

입력 모델은 보내는 필드의 이름을 그대로 둡니다. 예를 들어 [`AirportBusSeatInventoryQuery`][korail_mobile_api.AirportBusSeatInventoryQuery]의 `train_class_code`, `service_code`는 그대로이며, `from_schedule()`은 운행 편의 `settlement_train_class_code`, `train_group_code`를 옮겨 담습니다.

```text
print(stop.planned_departure_time, reservation.payment_deadline)
seat_query = LimousineSeatInventoryQuery(train_class_code=bus.train_class_code, service_code=bus.service_code, ...)
```

```python
from korail_mobile_api import AirportBusSeatInventoryQuery

print(stop.departure_time, reservation.settlement_deadline)
seat_query = AirportBusSeatInventoryQuery.from_schedule(bus)
```

### 키워드 생성과 `repr` {#dataclasses}

- 모든 입력·응답 모델과 설정 dataclass(`KorailConfig`, `KorailDeviceProfile`, `DynapathConfig`, `DynapathTokenSettings`, `DynapathRequestContext`)는 `frozen=True, kw_only=True`입니다. 위치 인자로 만들면 `TypeError`입니다. 키워드 생성과 `dataclasses.replace()`는 그대로 씁니다.
- 단, 팩토리 전용 `CommuterPassengerRequest`는 직접 생성하거나 `dataclasses.replace()`로 바꿀 수 없습니다. 변경하려면 `from_response(pass_data, source, counts)`를 다시 호출하세요.
- 기존 필수 생성자 인자 누락은 mypy·Pyright도 거절합니다. 실행 시 시그니처·기본값·필드 순서·nullable 읽기 규칙은 바꾸지 않았습니다. `TransferItinerary.legs`는 정확한 두 원소 튜플이며, commuter factory의 `counts`는 `Sequence[int]`(목록·튜플 등)를 받아 튜플로 보관합니다.
- `raw`는 그 필드를 선언한 모델에서 마지막 필드가 됐고 `repr()`에 나오지 않습니다. 비교(`==`)에서 빠지는 것은 같습니다. 응답 모델의 `raw`는 `BaseKorailResponse`에 선언돼 있어 `dataclasses.fields()` 순서에서 봉투 필드 바로 뒤에 그대로 있습니다.
- 호출자가 넣는 비밀값도 `repr()`에서 숨깁니다: `KorailSession.jsessionid`, `OriginalTicketReference.return_password`, `PaidTicket.return_password`, `StationRefundExecutionRequest`의 `original_return_password`·`customer_phone`·`customer_name`, `StationRefundVerificationRequest.customer_name`, `RefundCompanion`의 `name`·`certificate_no`, `PriceRecalculationRequest.non_member_no`, `DynapathTokenSettings.device_id`, `KorailConfig.advertising_id`. 이미 숨기던 `CardPayment`의 모든 필드, `PaidTicket`의 원표 반환일·동반자 필드, `KorailDeviceProfile.device_id`, `KorailConfig.proxy`도 그대로 숨깁니다.
- 숨기는 것은 `repr()`·`str()` 출력뿐입니다. 속성 값, `raw` 내용, `dataclasses.asdict()`, pickle은 가리지 않으므로 로그에 남기지 마세요.
- `ProductDetailResponse.detail_raw`와 `DynapathRequestContext.body`도 `repr`에서 숨기며 실제 원문·본문과 직렬화 결과는 유지합니다.

```text
query = TrainSearchQuery("서울", "부산", departure_date, "090000")
reference = OriginalTicketReference(window, sale_date, sequence, password)
```

```python
from korail_mobile_api import OriginalTicketReference, TrainSearchQuery

query = TrainSearchQuery(
    departure_station="서울", arrival_station="부산", departure_date=departure_date, departure_time="090000"
)
reference = OriginalTicketReference(
    sale_window_no=window, sale_date=sale_date, sale_sequence=sequence, return_password=password
)
```
