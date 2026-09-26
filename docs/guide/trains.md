# 열차 조회

이 가이드는 조회 조건을 만들어 직통·환승 열차를 찾고, 고른 열차의 호차·좌석과 운임을 확인하는 데까지 따라 합니다.
모든 단계는 조회만 하며 서버의 상태를 바꾸지 않습니다. 호차와 좌석을 볼 때만 로그인이 필요합니다.
각 메서드의 세부 사항은 [열차 조회·좌석 API](../api/trains.md)에 있습니다.

## 조회 조건 {#query}

조회 조건은 [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery]로 만들어 [`search_trains`](../api/trains.md#search_trains)에 넘깁니다.
필수 필드는 출발역, 도착역, 출발일 세 개이고 나머지는 기본값이 있습니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    query = TrainSearchQuery(
        departure_station_code="서울",
        arrival_station_code="부산",
        departure_date="20261002",
        departure_time="090000",
        passengers=2,
        child_passengers=1,
        infant_passengers=1,
        senior_passengers=1,
    )
    result = client.search_trains(query)
    for train in result.trains:
        print(train.train_class_name, train.train_no, train.departure_time, train.arrival_time)
finally:
    client.close()
```

### 승객 {#passengers}

인원은 승객 유형별 필드로 넣습니다. 요청에는 앱과 같은 방식으로 다섯 칸으로 합쳐 보냅니다.

| 요청의 인원 칸 | 더하는 필드 |
|---|---|
| 어른 | `passengers`(기본값 `1`) + `teenager_passengers`(청소년) + `guide_dog_passengers`(안내견) |
| 어린이 | `child_passengers` + `infant_passengers`(유아) |
| 경로 | `senior_passengers` |
| 중증 장애인 | `high_disability_passengers` |
| 경증 장애인 | `low_disability_passengers` |

인원 필드는 모두 정수여야 하며, 아니면 요청을 보내기 전에 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
인원의 범위와 합계는 라이브러리가 검사하지 않고 서버에 맡깁니다.

### 역 이름과 역 코드 {#stations}

`departure_station_code`와 `arrival_station_code`에는 역 이름(`"서울"`)이나 숫자로만 된 역 코드를 넣습니다.
역 코드를 넣으면 처음 한 번 [`get_station_data`](../api/session.md#get_station_data)로 역 목록을 받아 이름으로 바꿔 보내고, 대응표는 클라이언트에 보관합니다. 목록에 없는 코드는 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]입니다.
역 이름은 앞뒤 공백만 뺀 뒤 그대로 보냅니다. 비어 있으면 요청 전에 거절합니다.

다른 메서드는 역을 받는 방식이 다릅니다.

| 메서드 | 역을 넘기는 방식 |
|---|---|
| [`search_trains`](../api/trains.md#search_trains), [`search_transfer_trains`](../api/trains.md#search_transfer_trains), [`search_trains_with_transfer_fallback`](../api/trains.md#search_trains_with_transfer_fallback) | 역 이름 또는 역 코드 |
| [`get_transfer_stations`](../api/trains.md#get_transfer_stations), [`get_price_fare_quote`](../api/trains.md#get_price_fare_quote) | 역 코드 |
| [`get_seat_assignment_schedule`](../api/trains.md#get_seat_assignment_schedule), [`get_merge_seats_inquiry`](../api/trains.md#get_merge_seats_inquiry) | 역 이름 |

### 날짜와 시각 {#date-time}

`departure_date`는 `YYYYMMDD`, `departure_time`은 `HHMMSS`(기본값 `"000000"`)이며, 이 시각 이후에 출발하는 열차를 조회합니다.
라이브러리는 형식을 검사하지 않고 그대로 보냅니다. 예매할 수 있는 운행일은 [`get_train_calendar`](../api/session.md#get_train_calendar)로 확인할 수 있습니다.

### 그 밖의 필드 {#other-fields}

| 필드 | 기본값 | 설명 |
|---|---|---|
| `train_group_code` | `"109"` | 열차군 코드입니다. 기본값은 관측한 값이며, 앱이 열차 종류별로 쓰는 다른 코드는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. |
| `seat_attribute_code` | `"015"` | 좌석 속성 코드입니다. 빈 문자열이면 요청 전에 거절합니다. |
| `query_division_code` | `"1"` | 조회 구분 코드입니다. 앱이 정렬 방식마다 쓰는 값은 공개돼 있지 않습니다. 빈 문자열이면 거절합니다. |
| `include_srt` | `False` | `True`이면 요청의 SRT 함께 조회 표시 두 필드(`ebizCrossCheck`, `srtCheckYn`)를 `"Y"`로 보냅니다. 앱이 이 필드에 넣는 값과 서버에서의 효과는 확인하지 못했습니다. |
| `connection_station_codes` | `()` | 환승역 코드 목록입니다. 비어 있지 않으면 개수와 함께 요청에 싣습니다. |
| `connection_train_group_code` | `None` | 환승 열차군 코드입니다. `None`이 아니면 요청에 싣습니다. |

`connection_station_codes`와 `connection_train_group_code`는 값을 넣었을 때만 보내며, 서버가 이 값을 어떻게 쓰는지는 확인하지 못했습니다.

## 조회 결과 {#results}

[`TrainSearchResult`][korail_mobile_api.models.TrainSearchResult]의 `trains`에 열차가 [`TrainSummary`][korail_mobile_api.models.TrainSummary] 목록으로 들어 있습니다. 자주 쓰는 필드는 다음과 같습니다.

| 필드 | 뜻 |
|---|---|
| `train_class_name`, `train_no` | 열차 종류 이름, 열차 번호 |
| `departure_date`, `departure_time`, `arrival_time` | 출발일, 출발 시각, 도착 시각 |
| `general_availability_name`, `special_availability_name` | 일반실·특실 예약 상태 문구 |
| `free_car_count` | 자유석 칸 수 |

조건에 맞는 열차가 없으면 예외 없이 `trains`가 비어 있을 수 있습니다. 직통 열차가 없다는 결과 코드(`WRD000061`)에는 [`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError]가 발생합니다.
`result.metadata.notice_message`에 검색 안내 문구가 올 수 있습니다. 앱은 이 값이 있으면 안내 창을 띄웁니다.

## 다음 페이지 조회 {#next-page}

결과는 한 페이지씩 옵니다. `next_page()`가 [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation]을 돌려주면 같은 `query`와 함께 `continuation`으로 넘깁니다.
`next_page()`는 목록이 비었거나, 다음 페이지 표시가 없거나, 필요한 값이 빠졌으면 `None`입니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    query = TrainSearchQuery("서울", "부산", "20261002", "060000")
    result = client.search_trains(query)
    trains = list(result.trains)
    for _ in range(4):  # 최대 네 페이지 더
        continuation = result.next_page()
        if continuation is None:
            break
        result = client.search_trains(query, continuation=continuation)
        trains.extend(result.trains)
    print(len(trains), "편")
finally:
    client.close()
```

실서버의 직통 조회에서는 다음 페이지 표시(`result.metadata.next_page_flag`가 `"Y"`)가 있어도 필요한 값이 오지 않아 `next_page()`가 `None`인 경우가 있었습니다.
이때는 `result.next_query_from_last_departure(query)`로 마지막 열차의 출발일·출발 시각에서 시작하는 새 조건을 만들어 다시 조회할 수 있습니다. 이 메서드는 요청을 보내지 않고 조건만 만듭니다.
열차가 없거나 마지막 열차의 출발일·출발 시각이 없으면 `None`을 반환합니다.
마지막 열차가 다시 포함될 수 있으므로 열차 번호로 중복을 거르세요.
마지막 열차의 출발일·출발 시각이 조건의 값과 같으면 새 조건이 이전 조건과 같아집니다. 새 조건이 이전 조건과 같거나 새 열차가 없으면 조회를 멈추세요.

## 환승 여정 조회 {#transfer}

직통 열차가 없는 구간은 [`search_transfer_trains`](../api/trains.md#search_transfer_trains)로 환승 여정을 찾습니다.
결과의 `itineraries`에 두 구간을 묶은 [`TransferItinerary`][korail_mobile_api.models.TransferItinerary]가 들어 있습니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    query = TrainSearchQuery("강릉", "목포", "20261002", "080000")
    result = client.search_transfer_trains(query)
    for itinerary in result.itineraries:
        first, second = itinerary.legs
        print(
            first.train_no, first.departure_time,
            itinerary.transfer_station_name,
            second.train_no, second.arrival_time,
        )
finally:
    client.close()
```

- `first`와 `second`는 응답에 나온 순서의 두 구간입니다. `legs`는 두 구간을 튜플로 돌려줍니다.
- `transfer_station_code`와 `transfer_station_name`은 첫 구간의 도착역과 둘째 구간의 출발역이 같을 때만 값이 있습니다. 다르면 `None`입니다.
- 여정은 `train_sequence`가 같은 행이 두 개일 때 그 두 행을 묶은 것입니다. 두 구간으로 묶이지 않은 열차 행은 `itineraries`에 없고 `trains`에만 남습니다.
- `train_sequence`가 없는(`None`) 행끼리도 한 묶음으로 보므로, 서로 관계없는 두 행이 여정으로 묶일 수 있습니다. 예약에 넘기기 전에 두 구간의 `train_sequence`와 역을 확인하세요.
- 환승할 수 있는 역 목록은 [`get_transfer_stations`](../api/trains.md#get_transfer_stations)에 역 코드를 넘겨 따로 조회할 수 있습니다.

여정의 `legs`는 [`reserve_transfer`](../api/reservations.md#reserve_transfer)에 넘겨 한 PNR로 예약합니다.

## 직통이 없을 때 환승 조회 {#transfer-fallback}

[`search_trains_with_transfer_fallback`](../api/trains.md#search_trains_with_transfer_fallback)은 직통 조회가 [`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError]로 끝났을 때만 같은 조건으로 환승 첫 페이지를 조회합니다.
직통 결과가 빈 목록이거나 다른 오류가 난 경우에는 환승 조회로 넘어가지 않습니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery, TransferSearchResult

client = KorailClient()
try:
    query = TrainSearchQuery("강릉", "목포", "20261002", "080000")
    result = client.search_trains_with_transfer_fallback(query)
    if isinstance(result, TransferSearchResult):
        print("직통 없음, 환승 여정", len(result.itineraries), "개")
        continuation = result.next_page()
        if continuation is not None:
            more = client.search_transfer_trains(query, continuation=continuation)
    else:
        print("직통 열차", len(result.trains), "편")
finally:
    client.close()
```

환승 결과의 다음 페이지는 이 메서드가 아니라 [`search_transfer_trains`](../api/trains.md#search_transfer_trains)로 조회합니다. 이 메서드에 넘긴 `continuation`은 직통 조회에만 쓰입니다.

## 성수기와 특가 상품 조회 {#peak-season}

열차 조회는 요청 전에 대기열을 거칩니다. 두 인자에 따라 관문과 요청 경로가 바뀝니다.

| 인자 | 관문 | 요청 |
|---|---|---|
| 기본값 | `inquiry` | 일반 열차 조회 |
| `peak_season=True` | `peak_season_inquiry` | 일반 열차 조회(내용 같음) |
| `use_special_schedule=True` | `product_inquiry` | 특가 상품 조회 경로 |

- `peak_season`은 관문만 바꿉니다. 앱은 운행 달력으로 성수기를 판정하지만 그 기준값이 공개돼 있지 않아 라이브러리는 판정하지 않습니다. 출발일이 성수기인지는 호출자가 정합니다.
- `use_special_schedule=True`이면 `peak_season`과 관계없이 `product_inquiry` 관문을 씁니다.
- `peak_season_inquiry`와 `product_inquiry` 관문은 실서버에서 확인하지 못했습니다.
- [`get_seat_assignment_schedule`](../api/trains.md#get_seat_assignment_schedule)도 `peak_season`으로 `inquiry`와 `peak_season_inquiry` 가운데 하나를 고릅니다.

조회 관문은 대기열 서버에 오류가 나면 대기열을 건너뛰고 요청을 보냅니다. 자세한 동작은 [요청 흐름](../concepts/how-it-works.md)을, 대기열을 끄거나 조정하는 방법은 [설정](configuration.md)을 참고하세요.

## 호차와 좌석 조회 {#seats}

호차와 좌석 조회는 로그인이 필요합니다. [`get_seat_cars`](../api/trains.md#get_seat_cars)로 호차 목록을 먼저 받고, 같은 세션에서 [`get_seat_inventory`](../api/trains.md#get_seat_inventory)로 호차 하나의 좌석을 봅니다.
실서버에서는 호차 목록 없이 좌석 배치를 바로 조회하면 인증 정보 오류가 돌아올 수 있었습니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient, KorailSeatAssignment, KorailSeatClass, TrainSearchQuery

client = KorailClient()
try:
    client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    train = client.search_trains(TrainSearchQuery("서울", "부산", "20261002", "090000")).trains[0]

    cars = client.get_seat_cars(train, room_class_code=KorailSeatClass.GENERAL)
    for car in cars.cars:
        names = [attribute.name for attribute in car.attributes]
        print(car.car_no, car.room_class_name, car.remaining_seat_count, names)

    car = next(car for car in cars.cars if car.car_no is not None and car.remaining_seat_count)
    inventory = client.get_seat_inventory(train, car.car_no, room_class_code=KorailSeatClass.GENERAL)
    sellable = [seat for seat in inventory.seats if seat.sale_possible == "Y"]
    for seat in sellable[:5]:
        print(seat.seat_no, seat.specification, seat.direction_code)
    if sellable:
        assignment = KorailSeatAssignment.from_inventory(inventory, sellable[0])
finally:
    try:
        client.logout()
    finally:
        client.close()
```

### 좌석 속성 {#seat-attributes}

호차의 `attributes`는 그 호차에서 고를 수 있는 좌석 속성([`SeatAttribute`][korail_mobile_api.models.SeatAttribute])의 이름 `name`과 코드 `code`입니다.
두 메서드의 `seat_attribute_code`에 코드를 넣으면 그 값을, 넣지 않으면 조회 결과 행의 `train.seat_attribute_code`를 보냅니다. 코드는 숫자 세 자리여야 하며, 아니면 요청 전에 거절합니다.
앱처럼 호차 목록과 좌석 배치에는 같은 `room_class_code`와 `seat_attribute_code`를 넘기세요.

좌석 배치의 좌석마다 [`PhysicalSeat`][korail_mobile_api.models.PhysicalSeat]가 있습니다.

| 필드 | 뜻 |
|---|---|
| `seat_no` | 좌석 식별자입니다. 좌석 지정 예약에는 이 값을 씁니다. |
| `specification` | 화면에 보이는 좌석 표시입니다. 예약에는 쓰지 않습니다. |
| `sale_possible` | `"Y"`이면 판매할 수 있는 좌석입니다. |
| `direction_code`, `requested_attribute_code`, `other_attribute_code` | 좌석 방향 속성, 요청 좌석 속성, 기타 속성 코드입니다. |
| `message` | 좌석에 붙은 안내 문구입니다. |

`KorailSeatAssignment.from_inventory()`는 판매할 수 있는 좌석만 받아 좌석 지정 입력([`KorailSeatAssignment`][korail_mobile_api.mutation_models.KorailSeatAssignment])으로 바꿉니다.
이 값은 좌석 지정 예약(`job_type=KorailReservationJobType.SEAT_DESIGNATED`)으로 [`reserve`](../api/reservations.md#reserve)를 호출할 때 `seats`에 승객 수만큼 넘깁니다.
자유석 호차는 [`get_free_seat_car_info`](../api/trains.md#get_free_seat_car_info)로 따로 조회합니다. 호차가 숫자가 아니라 안내 문자열로 옵니다.

## 예매 전 운임 조회 {#fare}

[`get_price_fare_quote`](../api/trains.md#get_price_fare_quote)는 열차 한 편이나 환승 두 구간의 운임을 예매 전에 조회합니다.
조회 결과 행의 값을 [`PriceFareLeg`][korail_mobile_api.read_payloads.PriceFareLeg]로 옮기는 함수를 두면 직통과 환승에 같이 쓸 수 있습니다.

```python
from korail_mobile_api import KorailClient, PriceFareLeg, PriceFareQuoteRequest, TrainSearchQuery


def fare_leg(train):
    return PriceFareLeg(
        departure_station_code=train.departure_station_code,
        arrival_station_code=train.arrival_station_code,
        run_date=train.run_date,
        train_no=train.train_no,
        requested_seat_attribute_code=train.seat_attribute_code,
        train_group_code=train.train_group_code,
        train_class_code=train.train_class_code,
    )


client = KorailClient()
try:
    query = TrainSearchQuery("강릉", "목포", "20261002", "080000")
    itinerary = client.search_transfer_trains(query).itineraries[0]
    request = PriceFareQuoteRequest(legs=tuple(fare_leg(train) for train in itinerary.legs))
    for fare in client.get_price_fare_quote(request).fares:
        print(fare.journey_sequence, fare.room_class_name, fare.received_price, fare.total_amount)
finally:
    client.close()
```

- 조회 결과 행에 필요한 값이 없으면(`None`) `PriceFareLeg`를 만들 때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
- 금액은 서버가 보낸 표시용 문자열이며 기준 운임입니다. 결제할 금액은 예약한 뒤 홀드의 `received_amount`를 쓰세요. 할인이 적용되면 결제 금액은 이 운임보다 낮을 수 있습니다.

## 다음 단계 {#next}

- [예약](reservations.md): 조회한 열차로 홀드를 만들고, 확인하고, 취소하기
- [오류 처리](errors.md): 조회에서 나는 예외와 응답 원본 확인
