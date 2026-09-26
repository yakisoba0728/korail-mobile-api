# 예약

이 가이드는 조회한 열차에 결제 전 예약(홀드)을 만들고, 확인하고, 취소하는 과정을 따라 합니다.
일반 예약, 좌석 지정 예약, 예약대기, 환승 예약, 병합 예약을 차례로 다루고, 예약 확인·장바구니·취소를 설명합니다.
예약 메서드는 호출하는 즉시 실제로 처리되므로, 연습할 때도 만든 홀드는 반드시 결제하거나 취소하세요.

메서드별 매개변수와 예외는 [예약 API](../api/reservations.md)에 있습니다.

## 홀드와 결제 기한 {#hold}

예약 메서드([`reserve`](../api/reservations.md#reserve), [`reserve_transfer`](../api/reservations.md#reserve_transfer), [`reserve_merge`](../api/reservations.md#reserve_merge))는 결제 전 예약인 홀드를 만들고 [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse]를 반환합니다.
홀드는 좌석을 점유하며, 결제 기한까지 결제하거나 취소해야 합니다. 라이브러리는 홀드를 자동으로 결제하거나 취소하지 않습니다.

| 필드 | 뜻 |
|---|---|
| `pnr_no` | 예약 번호(PNR)입니다. 예약 상세 조회와 장바구니에 씁니다. |
| `received_amount` | 결제할 금액입니다. 카드 결제는 이 금액으로 합니다. |
| `payment_deadline_date`, `payment_deadline_time` | 결제 기한의 날짜와 시각입니다. 앱은 두 값을 이어 붙여 표시합니다. |
| `payable` | 결제할 수 있는 홀드인지 여부입니다. 예약대기 홀드는 `False`입니다. |
| `journeys` | 예약된 여정 목록([`ReservationJourney`][korail_mobile_api.mutation_models.ReservationJourney])입니다. |

`payment_deadline_message`는 이름과 달리 결제 기한 값이 아닙니다. `total_price`는 표시용 합계이므로 결제 금액으로 쓰지 마세요.

## 승객 구성 {#passengers}

[`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts]로 승객 종류별 인원을 정합니다. 예약 메서드에 넘기지 않으면 어른 1명입니다.

| 필드 | 승객 종류 | 기본값 |
|---|---|---|
| `adult` | 어른 | `1` |
| `teenager` | 청소년 | `0` |
| `child` | 어린이 | `0` |
| `infant` | 동반유아 | `0` |
| `senior` | 경로 | `0` |
| `severe_disability` | 1~3급 장애 | `0` |
| `mild_disability` | 4~6급 장애 | `0` |
| `guide_dog` | 안내견 | `0` |

- 각 값은 0 이상의 `int`여야 하며 `True`·`False`는 받지 않습니다.
- 전체 인원(`total`)은 유아와 안내견을 포함해 1명 이상 9명 이하입니다. 어기면 객체를 만들 때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
- 예약 요청 전에 두 조합을 더 검사합니다. 유아가 있으면 어린이·유아 외의 승객이 있어야 하고, 안내견은 장애 승객(`severe_disability`와 `mild_disability`의 합)보다 많을 수 없습니다.
- 조회할 때와 같은 승객 구성으로 예약하세요.

```python
from korail_mobile_api import KorailPassengerCounts

passengers = KorailPassengerCounts(adult=2, child=1)
print(passengers.total)  # 3
```

## 일반 예약 {#immediate}

일반 예약(`KorailReservationJobType.IMMEDIATE`)은 서버가 좌석을 배정합니다. `job_type`의 기본값이므로 따로 넣지 않아도 됩니다.
선택한 객실의 예약 코드가 `"11"`인 열차만 예약할 수 있습니다(일반실은 `general_reservation_code`, 특실은 `special_reservation_code`). 입석만 남은 열차는 요청 전에 거절합니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient, KorailPassengerCounts, TrainSearchQuery

client = KorailClient()
try:
    client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    query = TrainSearchQuery(
        departure_station_code="서울",
        arrival_station_code="부산",
        departure_date="20261002",
        departure_time="090000",
        passengers=2,
    )
    result = client.search_trains(query)
    train = next((t for t in result.trains if t.general_reservation_code == "11"), None)
    if train is None:
        raise SystemExit("예약할 수 있는 열차가 없습니다.")
    hold = client.reserve(train, passengers=KorailPassengerCounts(adult=2))
    print(hold.pnr_no, hold.received_amount)
    print("결제 기한:", hold.payment_deadline_date, hold.payment_deadline_time)
finally:
    try:
        client.logout()
    finally:
        client.close()
```

아래 예제는 이 블록의 `try` 안에서 `client`, `query`, `result`, `train`, `hold`를 이어 쓴다고 가정합니다.
좌석 지정·예약대기·환승·병합 예제는 각자 만든 홀드를 마지막에 취소하고, 예약 확인·장바구니·취소 예제는 일반 예약의 `hold`를 씁니다.
`hold`는 마지막 [취소](#cancel) 단계에서 취소합니다. 이 블록만 실행할 때는 마지막 `print` 다음 줄에 `client.cancel_unpaid_hold(hold)`를 넣으세요.

!!! warning "실제로 처리됩니다"
    `reserve`를 호출하면 좌석을 점유하는 홀드가 실제로 만들어집니다.
    응답을 읽지 못해 예외가 나도 홀드는 만들어졌을 수 있으므로, 다시 호출하지 말고 예외의 `raw`나 [예약 확인](#history)으로 먼저 결과를 확인하세요.

## 좌석 지정 예약 {#seat-designated}

좌석 지정 예약(`KorailReservationJobType.SEAT_DESIGNATED`)은 호차와 좌석을 직접 골라 잡습니다.
앱과 같은 순서로 [`get_seat_cars`](../api/trains.md#get_seat_cars)로 호차 목록을 먼저 읽고 [`get_seat_inventory`](../api/trains.md#get_seat_inventory)로 좌석 배치를 읽습니다. 호차 목록을 읽지 않고 좌석 배치를 바로 조회하면 서버가 오류로 응답할 수 있습니다.

좌석 배치에서 판매 가능한 좌석(`sale_possible`이 `"Y"`)을 골라 [`KorailSeatAssignment`][korail_mobile_api.mutation_models.KorailSeatAssignment]의 `from_inventory`로 좌석 입력을 만듭니다.
좌석은 전체 인원(`passengers.total`)만큼, 서로 다르게 넣어야 합니다.
아래 예제는 일반 예약의 `hold`가 잡은 `train`과 다른 열차를 고르고, 만든 홀드를 마지막에 취소합니다.

```python
from korail_mobile_api import KorailPassengerCounts, KorailReservationJobType, KorailSeatAssignment

passengers = KorailPassengerCounts(adult=2)
seat_train = next(t for t in result.trains if t is not train and t.general_reservation_code == "11")
cars = client.get_seat_cars(seat_train, passenger_count=passengers.total)
car = next(c for c in cars.cars if c.car_no is not None and (c.remaining_seat_count or 0) >= passengers.total)
inventory = client.get_seat_inventory(seat_train, car.car_no, passenger_count=passengers.total)
sellable = [seat for seat in inventory.seats if seat.sale_possible == "Y"]
seats = [KorailSeatAssignment.from_inventory(inventory, seat) for seat in sellable[: passengers.total]]
seat_hold = client.reserve(
    seat_train,
    passengers=passengers,
    job_type=KorailReservationJobType.SEAT_DESIGNATED,
    seats=seats,
)
print(seat_hold.pnr_no, seat_hold.received_amount)
client.cancel_unpaid_hold(seat_hold)
```

`from_inventory`는 좌석 배치 응답에 호차 번호(`car_no`)가 없으면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]를 발생시킵니다. 이때는 `KorailSeatAssignment(car_no=car.car_no, seat_no=seat.seat_no)`처럼 직접 만듭니다.

!!! warning "실제로 처리됩니다"
    `reserve`는 고른 좌석을 점유하는 홀드를 실제로 만들고, `cancel_unpaid_hold`는 그 홀드를 실제로 취소합니다.
    응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 예약대기 {#standby}

매진된 열차는 예약대기(`KorailReservationJobType.STANDBY`)로 신청할 수 있습니다. 일반실만 가능하며 열차의 `wait_reservation_flag`가 `" 9"`여야 합니다.
예약대기 홀드는 좌석을 확보한 것이 아니므로 `payable`이 `False`이고, [`pay_with_card`](../api/payments.md#pay_with_card)는 이 홀드를 요청 전에 거절합니다.

신청한 뒤에는 [`confirm_standby_hold`](../api/reservations.md#confirm_standby_hold)로 문자 알림과 객실 등급 변경 옵션을 저장합니다. 이 메서드는 기존 홀드의 옵션만 저장하며 새 예약이나 결제를 만들지 않습니다.

예약대기 홀드도 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소합니다. 아래 예제는 옵션을 저장한 뒤 홀드를 취소합니다.

```python
from korail_mobile_api import KorailPassengerCounts, KorailReservationJobType

standby_train = next(t for t in result.trains if t.wait_reservation_flag == " 9")
standby = client.reserve(
    standby_train,
    passengers=KorailPassengerCounts(adult=2),
    job_type=KorailReservationJobType.STANDBY,
)
print(standby.pnr_no, standby.payable)  # payable은 False
client.confirm_standby_hold(
    standby,
    sms_notify=True,
    phone_no=input("휴대전화 번호(숫자 11자리): "),
)
client.cancel_unpaid_hold(standby)
```

!!! warning "실제로 처리됩니다"
    `reserve`는 예약대기를 실제로 신청하고, `confirm_standby_hold`는 그 홀드에 옵션을 실제로 저장하며, `cancel_unpaid_hold`는 그 홀드를 실제로 취소합니다.
    응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 환승 예약 {#transfer}

[`search_transfer_trains`](../api/trains.md#search_transfer_trains)로 찾은 환승 여정은 [`reserve_transfer`](../api/reservations.md#reserve_transfer)로 한 PNR에 홀드합니다.
[`TransferItinerary`][korail_mobile_api.models.TransferItinerary]의 `legs`가 탑승 순서대로 놓인 두 구간이므로 그대로 넘깁니다.
두 구간은 서로 다른 열차여야 하고 두 번째 구간은 첫 구간 이후에 출발해야 합니다. 구간마다 일반 예약과 같은 예약 가능 여부를 검사합니다.
객실 등급은 `seat_classes`에 값 하나(두 구간 공통)나 구간별 목록으로 넣습니다.
아래 예제는 만든 환승 홀드를 마지막에 취소합니다.

```python
from korail_mobile_api import KorailPassengerCounts, TrainSearchQuery

transfer_query = TrainSearchQuery("강릉", "목포", "20261002", "080000", passengers=2)
transfer = client.search_transfer_trains(transfer_query)
itinerary = transfer.itineraries[0]
transfer_hold = client.reserve_transfer(itinerary.legs, passengers=KorailPassengerCounts(adult=2))
print(transfer_hold.pnr_no, transfer_hold.received_amount)
client.cancel_unpaid_hold(transfer_hold)
```

!!! warning "실제로 처리됩니다"
    `reserve_transfer`는 두 구간의 좌석을 점유하는 홀드를 실제로 만들고, `cancel_unpaid_hold`는 그 홀드를 실제로 취소합니다.
    응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 병합 예약 {#merge}

병합 예약은 입석으로 잡은 구간과 좌석이 있는 구간을 이어 붙여 예약합니다. 앱과 같은 순서로 네 단계를 거치며, 라이브러리는 이 단계를 자동으로 이어서 보내지 않습니다.

1. `KorailReservationJobType.MERGE_STANDING`으로 첫 홀드를 만듭니다.
2. [`get_merge_seats_inquiry`](../api/trains.md#get_merge_seats_inquiry)로 병합할 열차 행을 조회합니다.
3. 첫 홀드를 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소합니다.
4. [`reserve_merge`](../api/reservations.md#reserve_merge)로 후속 홀드를 만듭니다.

병합 예약을 할 수 있는 열차는 `merge_seat_application_flag`가 일반실은 `"A"`·`"G"`, 특실은 `"A"`·`"S"` 중 하나인 열차입니다. 이 조건은 요청 전에 검사합니다.
아래 예제는 일반 예약의 `hold`가 잡은 `train`과 다른 열차를 고르고, 4단계에서 만든 후속 홀드를 마지막에 취소합니다.

### 1. 첫 홀드 {#merge-first-hold}

```python
from korail_mobile_api import KorailPassengerCounts, KorailReservationJobType

passengers = KorailPassengerCounts(adult=2)
merge_train = next(t for t in result.trains if t is not train and t.merge_seat_application_flag in {"A", "G"})
first = client.reserve(merge_train, passengers=passengers, job_type=KorailReservationJobType.MERGE_STANDING)
```

!!! warning "실제로 처리됩니다"
    첫 홀드도 좌석을 점유하는 실제 홀드입니다. 3단계에서 취소하기 전까지 남아 있습니다.

### 2. 병합 조회 {#merge-inquiry}

[`MergeSeatsInquiryRequest`][korail_mobile_api.read_payloads.MergeSeatsInquiryRequest]에 첫 홀드의 열차 정보를 넣습니다. 이 조회는 서버 상태를 바꾸지 않습니다.

```python
from korail_mobile_api import MergeSeatsInquiryRequest

when = merge_train.departure_date + merge_train.departure_time
merge = client.get_merge_seats_inquiry(
    MergeSeatsInquiryRequest(
        boarding_datetime=when,
        run_datetime=when,
        train_no=merge_train.train_no,
        departure_station_name=merge_train.departure_station_name,
        arrival_station_name=merge_train.arrival_station_name,
        selected_station_name=None,
        room_class_code="1",
        seat_attribute_code=merge_train.seat_attribute_code or "015",
        passenger_count=passengers.total,
    )
)
print([station.name for station in merge.intermediate_stations])
```

응답의 `trains`([`TrainScheduleItem`][korail_mobile_api.read_models.TrainScheduleItem] 목록)를 4단계에 그대로 넘깁니다. 첫 행의 도착역이 좌석이 갈리는 중간역이 됩니다.
`trains`가 비어 있으면 `reserve_merge`가 요청 전에 거절하므로, 첫 홀드를 취소하고 멈춥니다.

### 3. 첫 홀드 취소 {#merge-cancel}

```python
client.cancel_unpaid_hold(first)
```

!!! warning "실제로 처리됩니다"
    `cancel_unpaid_hold`를 호출하면 첫 홀드가 실제로 취소됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

### 4. 후속 홀드 {#merge-follow-up}

`reserve_merge`는 첫 홀드 요청을 보관하지 않고 인자로 다시 만듭니다. 첫 홀드와 같은 열차, 승객 구성, 객실 등급, 좌석 속성을 넘기세요.
후속 홀드는 첫 홀드와 다른 PNR일 수 있으므로 이후의 결제와 취소에는 반환된 홀드를 씁니다.

```python
merge_hold = client.reserve_merge(merge_train, merge.trains, passengers=passengers)
print(merge_hold.pnr_no, merge_hold.received_amount)
client.cancel_unpaid_hold(merge_hold)
```

!!! warning "실제로 처리됩니다"
    `reserve_merge`는 좌석을 점유하는 후속 홀드를 실제로 만들고, `cancel_unpaid_hold`는 그 홀드를 실제로 취소합니다.
    응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 예약 확인 {#history}

[`get_reservation_history`](../api/reservations.md#get_reservation_history)는 계정에 남아 있는 예약을 조회합니다. 예약 메서드가 예외로 끝났을 때 홀드가 만들어졌는지 확인하는 데 씁니다.
남은 예약이 없으면 예외 없이 결과 코드(`h_msg_cd`) `P100`과 빈 목록을 담은 응답을 반환합니다.

```python
history = client.get_reservation_history()
if history.h_msg_cd == "P100":
    print("남아 있는 예약이 없습니다.")
for row in history.trains:
    print(row.pnr_no, row.train_no, row.run_date, row.departure_time, row.reserved_amount)
```

PNR을 알고 있으면 [`get_ticket_reservation_detail`](../api/reservations.md#get_ticket_reservation_detail)로 그 예약의 여정과 좌석을 다시 읽을 수 있습니다.

```python
from korail_mobile_api import TicketReservationDetailRequest

detail = client.get_ticket_reservation_detail(TicketReservationDetailRequest(pnr_no=hold.pnr_no))
for journey in detail.journeys:
    for seat in journey.seats:
        print(journey.train_no, seat.car_no, seat.seat_no, seat.received_amount)
```

## 장바구니 {#cart}

[`add_to_cart`](../api/reservations.md#add_to_cart)는 홀드를 계정의 장바구니에 담고, [`get_cart_list`](../api/reservations.md#get_cart_list)는 장바구니를 조회합니다.
장바구니 행([`CartItem`][korail_mobile_api.read_models.CartItem])은 열차·공항버스 예약이나 부가서비스 한 건입니다.
라이브러리에는 장바구니에서 행을 빼는 메서드가 없습니다.

```python
from korail_mobile_api import CartAddRequest

client.add_to_cart(CartAddRequest(pnr_no=hold.pnr_no))
cart = client.get_cart_list()
for item in cart.items:
    print(item.pnr_no, item.product_name, item.received_amount)
```

!!! warning "실제로 처리됩니다"
    `add_to_cart`를 호출하면 홀드가 장바구니에 실제로 추가됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 `get_cart_list`로 결과를 확인하세요.

## 취소 {#cancel}

결제하지 않은 홀드는 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소합니다. 예약 메서드가 반환한 홀드를 그대로 넘깁니다.
아래 예제는 일반 예약에서 만들어 예약 확인과 장바구니에 쓴 `hold`를 취소합니다.
기본값으로는 취소 가능 여부를 먼저 확인하고, 확인에 실패하면 취소 요청을 보내지 않습니다.
발권된 승차권은 취소가 아니라 환불로 처리합니다.

```python
response = client.cancel_unpaid_hold(hold)
print(response.str_result, response.h_msg_cd)
```

!!! warning "실제로 처리됩니다"
    `cancel_unpaid_hold`를 호출하면 홀드가 실제로 취소됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 [예약 확인](#history)으로 결과를 확인하세요.

## 다음 단계 {#next}

만든 홀드는 결제 기한 안에 결제합니다. 카드 결제, 할인 재계산, 환불은 [결제와 환불](payments.md)을 참고하세요.
