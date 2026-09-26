# 열차 조회·좌석

이 페이지의 메서드는 열차를 찾고, 열차 한 편의 정차역·호차·좌석·운임을 조회합니다.
모두 서버의 상태를 바꾸지 않는 조회 메서드이며, 호차 목록과 좌석 배치 조회만 로그인이 필요합니다.
처음부터 순서대로 따라 하려면 [열차 조회 가이드](../guide/trains.md)를 참고하세요.

흐름:

1. [`search_trains`](#search_trains)로 직통 열차를 찾습니다. 직통이 없으면 [`search_transfer_trains`](#search_transfer_trains)나 [`search_trains_with_transfer_fallback`](#search_trains_with_transfer_fallback)으로 환승 여정을 찾습니다.
2. 조회 결과의 [`TrainSummary`][korail_mobile_api.models.TrainSummary]로 [`get_seat_cars`](#get_seat_cars), [`get_seat_inventory`](#get_seat_inventory) 순서로 호차와 좌석을 봅니다.
3. [`get_price_fare_quote`](#get_price_fare_quote)로 예매 전 운임을 확인한 뒤 [예약](reservations.md)으로 넘어갑니다.

## `search_trains`

한 구간·한 날짜의 직통 열차를 한 페이지 조회합니다.

```python
KorailClient.search_trains(
    query: TrainSearchQuery,
    *,
    continuation: TrainSearchContinuation | None = None,
    use_special_schedule: bool = False,
    peak_season: bool = False,
) -> TrainSearchResult
```

조회 조건은 [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery]로 넘깁니다.
출발역·도착역이 숫자로만 된 역 코드이면 처음 한 번 역 목록([`get_station_data`](session.md#get_station_data))을 조회해 역 이름으로 바꿔 보내고, 코드와 이름의 대응표는 클라이언트에 보관합니다.
숫자가 아닌 값은 역 이름으로 보고 앞뒤 공백만 뺀 뒤 그대로 보냅니다.
로그인하지 않아도 조회할 수 있습니다. 로그인한 세션에 회원카드 번호(`member_card_no`)가 있으면 요청에 함께 싣습니다.

결과는 한 번에 한 페이지씩 옵니다. 다음 페이지가 있으면 결과의 `next_page()`가 [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation]을 돌려주고, 이 값을 `continuation`에 넣어 같은 `query`로 다시 호출합니다.
조건에 맞는 열차가 없을 때 예외 없이 `trains`가 빈 결과가 올 수 있으므로 목록이 비었는지 확인하세요.

요청 전에 대기열을 거칩니다. 관문은 기본이 `inquiry`이고, `peak_season=True`이면 `peak_season_inquiry`, `use_special_schedule=True`이면 `peak_season`과 관계없이 `product_inquiry`입니다.
`peak_season_inquiry`와 `product_inquiry` 관문은 실서버에서 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery] | 필수 | 조회 조건입니다. 필드별 설명은 [열차 조회 가이드](../guide/trains.md)에 있습니다. |
| `continuation` | [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation] \| `None` | `None` | 다음 페이지를 조회할 때 이전 결과의 `next_page()` 값을 넣습니다. `None`이면 첫 페이지를 조회합니다. |
| `use_special_schedule` | `bool` | `False` | `True`이면 특가 상품 조회 경로로 보내고 `product_inquiry` 관문을 거칩니다. |
| `peak_season` | `bool` | `False` | 출발일이 성수기이면 `True`로 합니다. 대기열 관문만 `peak_season_inquiry`로 바뀌고 요청 내용은 같습니다. 앱은 운행 달력으로 성수기를 판정하지만 그 기준값이 공개돼 있지 않아 호출자가 정합니다. |

**반환값**

[`TrainSearchResult`][korail_mobile_api.models.TrainSearchResult] — `trains`에 열차가 [`TrainSummary`][korail_mobile_api.models.TrainSummary] 목록으로, `metadata`에 페이지 정보와 검색 안내 문구(`notice_message`)가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError] | 직통 열차가 없을 때 (결과 코드 `WRD000061`) |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 출발역·도착역이 비었거나, 역 목록에 없는 역 코드일 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 승객 수 필드 가운데 정수가 아닌 값이 있을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `seat_attribute_code`나 `query_division_code`가 빈 문자열이거나, `connection_station_codes`·`connection_train_group_code`에 빈 값이 있을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `continuation`이 [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation]이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | `inquiry` | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import TrainSearchQuery

query = TrainSearchQuery("서울", "부산", "20261002", "090000", passengers=2)
result = client.search_trains(query)
for train in result.trains:
    print(train.train_no, train.departure_time, train.general_availability_name)

continuation = result.next_page()
if continuation is not None:
    more = client.search_trains(query, continuation=continuation)
```

## `search_transfer_trains`

같은 조회 조건으로 환승 여정을 한 페이지 조회합니다.

```python
KorailClient.search_transfer_trains(
    query: TrainSearchQuery,
    *,
    continuation: TrainSearchContinuation | None = None,
    use_special_schedule: bool = False,
    peak_season: bool = False,
) -> TransferSearchResult
```

요청은 [`search_trains`](#search_trains)와 같고, 여정 구분만 환승으로 바꿔 보냅니다. 역 이름·역 코드 처리와 대기열 관문도 같습니다.

응답의 열차 행은 `train_sequence`가 같은 것끼리 응답에 나온 순서대로 묶습니다.
두 행으로 된 묶음만 [`TransferItinerary`][korail_mobile_api.models.TransferItinerary]가 되어 `itineraries`에 들어가고, 그 밖의 행은 `trains`에만 남습니다.
여정의 `transfer_station_code`와 `transfer_station_name`은 첫 구간의 도착역과 둘째 구간의 출발역이 같을 때만 값이 있습니다. 다르면 `None`이므로 두 구간의 역을 직접 확인하세요.

`next_page()`는 응답에 환승용 다음 페이지 값이 둘 다 있으면 그것을, 하나라도 없으면 직통용 값을 씁니다.
여정의 `legs`는 [`reserve_transfer`](reservations.md#reserve_transfer)에 그대로 넘겨 한 PNR로 예약할 수 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery] | 필수 | 조회 조건입니다. 출발역과 최종 도착역을 넣습니다. |
| `continuation` | [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation] \| `None` | `None` | 다음 페이지를 조회할 때 이전 환승 결과의 `next_page()` 값을 넣습니다. |
| `use_special_schedule` | `bool` | `False` | `True`이면 특가 상품 조회 경로로 보내고 `product_inquiry` 관문을 거칩니다. |
| `peak_season` | `bool` | `False` | `True`이면 `peak_season_inquiry` 관문을 거칩니다. |

**반환값**

[`TransferSearchResult`][korail_mobile_api.models.TransferSearchResult] — `itineraries`에 두 구간으로 묶은 여정, `trains`에 응답의 모든 열차 행, `metadata`에 페이지 정보가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | [`search_trains`](#search_trains)와 같은 요청 전 입력 검사에 실패했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | `inquiry` | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import TrainSearchQuery

query = TrainSearchQuery("강릉", "목포", "20261002", "080000")
result = client.search_transfer_trains(query)
for itinerary in result.itineraries:
    first, second = itinerary.legs
    print(first.train_no, itinerary.transfer_station_name, second.train_no, second.arrival_time)
```

## `search_trains_with_transfer_fallback`

직통 열차가 없을 때만 같은 조건으로 환승 여정을 조회합니다.

```python
KorailClient.search_trains_with_transfer_fallback(
    query: TrainSearchQuery,
    *,
    continuation: TrainSearchContinuation | None = None,
    use_special_schedule: bool = False,
    peak_season: bool = False,
) -> TrainSearchResult | TransferSearchResult
```

먼저 [`search_trains`](#search_trains)를 호출합니다.
[`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError](결과 코드 `WRD000061`)가 발생했을 때만 같은 `query`, `use_special_schedule`, `peak_season`으로 [`search_transfer_trains`](#search_transfer_trains)를 한 번 호출해 첫 페이지를 반환합니다.
다른 오류는 그대로 발생하며, 예외 없이 빈 결과가 온 경우에도 환승 조회로 넘어가지 않습니다.
앱은 환승 조회 전에 확인 창을 띄우고 열차 종류 선택을 바꾸지만, 이 메서드는 그런 단계 없이 바로 조회합니다.

반환 타입이 둘 중 하나이므로 `isinstance`로 구분하세요.
환승 결과의 다음 페이지는 [`search_transfer_trains`](#search_transfer_trains)에 `continuation`을 넘겨 조회합니다. 이 메서드에 넘긴 `continuation`은 직통 조회에만 쓰입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery] | 필수 | 조회 조건입니다. 직통 조회와 환승 조회에 같은 값을 씁니다. |
| `continuation` | [`TrainSearchContinuation`][korail_mobile_api.models.TrainSearchContinuation] \| `None` | `None` | 직통 조회에만 넘깁니다. 환승 조회로 넘어가면 쓰지 않고 첫 페이지를 조회합니다. |
| `use_special_schedule` | `bool` | `False` | `True`이면 두 조회 모두 특가 상품 조회 경로로 보내고 `product_inquiry` 관문을 거칩니다. |
| `peak_season` | `bool` | `False` | `True`이면 두 조회 모두 `peak_season_inquiry` 관문을 거칩니다. |

**반환값**

[`TrainSearchResult`][korail_mobile_api.models.TrainSearchResult] \| [`TransferSearchResult`][korail_mobile_api.models.TransferSearchResult] — 직통 조회가 성공하면 `TrainSearchResult`, 환승 조회로 넘어갔으면 `TransferSearchResult`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | [`search_trains`](#search_trains)와 같은 요청 전 입력 검사에 실패했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | `inquiry` | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import TrainSearchQuery, TransferSearchResult

query = TrainSearchQuery("강릉", "목포", "20261002", "080000")
result = client.search_trains_with_transfer_fallback(query)
if isinstance(result, TransferSearchResult):
    print("환승 여정", len(result.itineraries), "개")
else:
    print("직통 열차", len(result.trains), "편")
```

## `get_transfer_stations`

한 구간에서 환승할 수 있는 역 목록을 조회합니다.

```python
KorailClient.get_transfer_stations(
    departure_station_code: str,
    arrival_station_code: str,
) -> TransferStationListResponse
```

출발역과 도착역을 역 코드로 넘깁니다. [`search_trains`](#search_trains)와 달리 역 이름을 코드로 바꾸지 않습니다.
역 코드는 [`get_station_data`](session.md#get_station_data) 결과의 `code`나 조회 결과 행의 `departure_station_code`, `arrival_station_code`에서 얻을 수 있습니다.
응답에 환승역 목록이 없으면 빈 `stations`를 반환합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `departure_station_code` | `str` | 필수 | 출발역 코드입니다. |
| `arrival_station_code` | `str` | 필수 | 도착역 코드입니다. |

**반환값**

[`TransferStationListResponse`][korail_mobile_api.models.TransferStationListResponse] — `stations`에 [`TransferStation`][korail_mobile_api.models.TransferStation] 목록(`station_code`, `station_name`)이 들어 있습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
codes = {station.name: station.code for station in client.get_station_data().stations}
response = client.get_transfer_stations(codes["강릉"], codes["목포"])
for station in response.stations:
    print(station.station_code, station.station_name)
```

## `get_train_schedule`

열차 한 편의 정차역과 도착·출발 시각, 지연 정보를 조회합니다.

```python
KorailClient.get_train_schedule(run_date: str, train_no: str) -> TrainScheduleResponse
```

운행일과 열차 번호로 조회합니다. 조회 결과 행의 `run_date`와 `train_no`를 그대로 넘기면 됩니다.
열차 번호는 다섯 자리가 되도록 앞에 0을 채워 보냅니다.
정차역마다 계획 시각(`planned_arrival_time`, `planned_departure_time`)과 실제 시각(`actual_arrival_time`, `actual_departure_time`)이 [`TrainScheduleStop`][korail_mobile_api.models.TrainScheduleStop]으로 들어 있습니다.
응답 필드는 모두 선택값이라 서버가 보내지 않으면 `None`입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `run_date` | `str` | 필수 | 운행일(`YYYYMMDD`)입니다. |
| `train_no` | `str` | 필수 | 열차 번호입니다. 다섯 자리보다 짧으면 앞에 0을 채웁니다. |

**반환값**

[`TrainScheduleResponse`][korail_mobile_api.models.TrainScheduleResponse] — `stops`에 정차역 목록이, 그 밖에 노선 이름(`route_name`), 시발역·종착역 이름(`origin_station_name`, `terminal_station_name`), 지연 사유(`delay_detail_reason_content`) 등이 들어 있습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
train = result.trains[0]  # search_trains 결과의 첫 열차
schedule = client.get_train_schedule(train.run_date, train.train_no)
for stop in schedule.stops:
    print(stop.station_name, stop.planned_departure_time, stop.actual_departure_time)
```

## `get_seat_cars`

열차 한 편의 호차 목록과 호차별 잔여석·좌석 속성을 조회합니다.

```python
KorailClient.get_seat_cars(
    train: TrainSummary,
    *,
    passenger_count: int = 1,
    room_class_code: KorailRoomClassCode = '1',
    seat_attribute_code: str | None = None,
) -> SeatCarListResponse
```

좌석 지정 예약에서 호차를 고를 때 씁니다. 로그인하지 않았으면 요청을 보내지 않고 예외를 발생시킵니다.
운행일, 열차 번호, 출발·도착역, 운행 순번, 상품 번호 같은 열차 식별값은 `train`에서 가져옵니다. 열차 번호는 다섯 자리가 되도록 앞에 0을 채웁니다.

좌석 속성 코드는 `seat_attribute_code`를 넣으면 그 값을, `None`이나 빈 문자열이면 `train.seat_attribute_code`를 쓰고, 둘 다 없으면 보내지 않습니다.
이어서 [`get_seat_inventory`](#get_seat_inventory)를 호출할 때는 같은 `room_class_code`와 `seat_attribute_code`를 넘기세요. 앱도 호차 목록과 좌석 배치도에 같은 좌석 속성을 씁니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `train` | [`TrainSummary`][korail_mobile_api.models.TrainSummary] | 필수 | 조회할 열차입니다. 열차 조회 결과의 행을 넘깁니다. |
| `passenger_count` | `int` | `1` | 총 승객 수입니다. 1~9의 정수여야 합니다. |
| `room_class_code` | [`KorailRoomClassCode`][korail_mobile_api.constants.KorailRoomClassCode] | `'1'` | 객실 등급입니다. `"1"`(일반실) 또는 `"2"`(특실)이며 [`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass] 값도 받습니다. |
| `seat_attribute_code` | `str` \| `None` | `None` | 숫자 세 자리의 좌석 속성 코드입니다. `None`이면 `train.seat_attribute_code`를 씁니다. |

**반환값**

[`SeatCarListResponse`][korail_mobile_api.models.SeatCarListResponse] — `cars`에 [`SeatCar`][korail_mobile_api.models.SeatCar] 목록(호차 번호 `car_no`, 객실 이름 `room_class_name`, 잔여석 `remaining_seat_count`, 좌석 속성 `attributes`)이, `recommended_car_no`에 추천 호차 번호가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `train`이 [`TrainSummary`][korail_mobile_api.models.TrainSummary]가 아니거나, `train.goods_no`에 출력 가능한 ASCII가 아닌 문자가 있을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `passenger_count`가 1~9의 정수가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `room_class_code`가 `"1"`이나 `"2"`가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 보낼 좌석 속성 코드(`seat_attribute_code` 또는 `train.seat_attribute_code`)가 숫자 세 자리가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
train = result.trains[0]  # search_trains 결과의 첫 열차
cars = client.get_seat_cars(train, passenger_count=2)
for car in cars.cars:
    codes = [attribute.code for attribute in car.attributes]
    print(car.car_no, car.room_class_name, car.remaining_seat_count, codes)
```

## `get_seat_inventory`

한 호차의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다.

```python
KorailClient.get_seat_inventory(
    train: TrainSummary,
    car_no: int,
    *,
    passenger_count: int = 1,
    room_class_code: KorailRoomClassCode = '1',
    seat_attribute_code: str | None = None,
) -> SeatInventoryResponse
```

같은 세션에서 [`get_seat_cars`](#get_seat_cars)를 먼저 호출한 뒤 사용하세요. 실서버에서는 호차 목록을 조회하지 않고 바로 호출하면 인증 정보 오류가 돌아올 수 있었습니다. 앱도 호차 목록, 좌석 배치도 순서로 조회합니다.
열차 식별값과 좌석 속성 코드를 정하는 규칙은 [`get_seat_cars`](#get_seat_cars)와 같습니다.

좌석마다 [`PhysicalSeat`][korail_mobile_api.models.PhysicalSeat]가 있습니다. 예약할 때는 표시용 `specification`이 아니라 식별자 `seat_no`를 씁니다.
`sale_possible`이 `"Y"`인 좌석은 [`KorailSeatAssignment`][korail_mobile_api.mutation_models.KorailSeatAssignment]의 `from_inventory()`로 좌석 지정 입력으로 바꿀 수 있습니다.
응답에 호차 번호(`car_no`)가 없으면 `from_inventory()`를 쓸 수 없으므로 `KorailSeatAssignment(car_no=..., seat_no=...)`로 직접 만듭니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `train` | [`TrainSummary`][korail_mobile_api.models.TrainSummary] | 필수 | 조회할 열차입니다. [`get_seat_cars`](#get_seat_cars)에 넘긴 것과 같은 행을 넘깁니다. |
| `car_no` | `int` | 필수 | 호차 번호입니다. [`get_seat_cars`](#get_seat_cars) 결과의 `car_no`를 넘깁니다. 1 이상의 정수여야 합니다. |
| `passenger_count` | `int` | `1` | 총 승객 수입니다. 1~9의 정수여야 합니다. |
| `room_class_code` | [`KorailRoomClassCode`][korail_mobile_api.constants.KorailRoomClassCode] | `'1'` | 객실 등급입니다. `"1"`(일반실) 또는 `"2"`(특실)입니다. |
| `seat_attribute_code` | `str` \| `None` | `None` | 숫자 세 자리의 좌석 속성 코드입니다. `None`이면 `train.seat_attribute_code`를 씁니다. |

**반환값**

[`SeatInventoryResponse`][korail_mobile_api.models.SeatInventoryResponse] — `seats`에 좌석 목록, `windows`에 창문 위치 비율([`SeatWindow`][korail_mobile_api.models.SeatWindow]), `car_no`에 서버가 돌려준 호차 번호가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `car_no`가 1 이상의 정수가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | [`get_seat_cars`](#get_seat_cars)와 같은 입력 검사(`train`, `passenger_count`, `room_class_code`, 좌석 속성 코드)에 실패했을 때 |
| [`KorailAppError`][korail_mobile_api.errors.KorailAppError] | 같은 세션에서 [`get_seat_cars`](#get_seat_cars)를 먼저 호출하지 않아 서버가 인증 정보 오류로 응답했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import KorailSeatAssignment

cars = client.get_seat_cars(train)
car = next(car for car in cars.cars if car.car_no is not None and car.remaining_seat_count)
inventory = client.get_seat_inventory(train, car.car_no)
sellable = [seat for seat in inventory.seats if seat.sale_possible == "Y"]
if sellable:
    assignment = KorailSeatAssignment.from_inventory(inventory, sellable[0])
```

## `get_free_seat_car_info`

열차 한 편의 자유석 호차 안내를 조회합니다.

```python
KorailClient.get_free_seat_car_info(request: FreeSeatCarRequest) -> FreeSeatCarResponse
```

[`FreeSeatCarRequest`][korail_mobile_api.read_payloads.FreeSeatCarRequest]에 조회 결과 행의 운행일, 열차 번호, 출발·도착역 구성 순번과 운행 순번을 옮겨 넣습니다. 열차 번호는 다섯 자리가 되도록 앞에 0을 채워 보냅니다.
자유석 호차는 숫자 목록이 아니라 `car_no`에 안내 문자열로 오며, 호차가 여러 개이면 한 문자열에 함께 들어 있습니다.
자유석 칸이 없는 열차는 예외 없이 `car_no`가 `None`인 응답이 옵니다(결과 코드 `IRZ000005`).
실서버에서는 조회 결과 행의 `free_car_count`가 `"000"`이 아닌 열차에만 자유석 호차가 있었습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`FreeSeatCarRequest`][korail_mobile_api.read_payloads.FreeSeatCarRequest] | 필수 | 조회할 열차의 운행일, 열차 번호, 구성 순번, 운행 순번입니다. |

**반환값**

[`FreeSeatCarResponse`][korail_mobile_api.read_models.FreeSeatCarResponse] — 안내 제목 `title`, 자유석 호차 문자열 `car_no`, 안내 내용 `content`가 들어 있습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import FreeSeatCarRequest

info = client.get_free_seat_car_info(
    FreeSeatCarRequest(
        run_date=train.run_date,
        train_no=train.train_no,
        departure_construction_order=train.departure_construction_order,
        arrival_construction_order=train.arrival_construction_order,
        departure_run_order=train.departure_run_order,
        arrival_run_order=train.arrival_run_order,
    )
)
print(info.car_no if info.car_no is not None else "자유석 없음")
```

## `get_seat_assignment_schedule`

좌석배정 예매 화면의 열차 목록을 조회합니다.

```python
KorailClient.get_seat_assignment_schedule(
    request: SeatAssignmentScheduleRequest,
    *,
    peak_season: bool = False,
) -> SeatAssignmentScheduleResponse
```

앱의 좌석배정 예매 화면이 쓰는 열차 조회입니다. [`search_trains`](#search_trains)와 달리 역을 이름으로만 받으며 코드를 이름으로 바꾸지 않습니다.
[`SeatAssignmentScheduleRequest`][korail_mobile_api.read_payloads.SeatAssignmentScheduleRequest]는 만들 때 `passenger_count`가 1~9의 정수인지 검사하고, 아니면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]를 발생시킵니다.
요청에는 승객 수만큼 번호를 붙여 좌석 속성 코드, 승객 표시, 구분 이름을 반복해 싣고, 빈 문자열인 필드는 보내지 않습니다.

메뉴 ID나 구분 코드처럼 앱이 채우는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
실서버에서는 `menu_id`가 `"A1"`, `"A2"`일 때 열차 목록이 돌아왔고, 날짜·구간에 따라 결과 코드 `WRD000057`로 거절되기도 했습니다.
요청 전에 `inquiry` 관문을 거치며, `peak_season=True`이면 `peak_season_inquiry` 관문을 거칩니다. `peak_season_inquiry` 관문은 실서버에서 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`SeatAssignmentScheduleRequest`][korail_mobile_api.read_payloads.SeatAssignmentScheduleRequest] | 필수 | 메뉴 ID, 출발일(`YYYYMMDD`)·출발 시각(`HHMMSS`), 출발·도착역 이름, 열차군·객실 등급·좌석 속성 코드, 승객 수 등 조회 조건입니다. |
| `peak_season` | `bool` | `False` | 출발일이 성수기이면 `True`로 합니다. 대기열 관문만 바뀝니다. |

**반환값**

[`SeatAssignmentScheduleResponse`][korail_mobile_api.read_models.SeatAssignmentScheduleResponse] — `trains`에 열차가 [`TrainScheduleItem`][korail_mobile_api.read_models.TrainScheduleItem] 목록으로 들어 있습니다. 다음 페이지 정보(`next_page_flag` 등)도 담지만 이 메서드에는 이어서 조회하는 매개변수가 없습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAppError`][korail_mobile_api.errors.KorailAppError] | 날짜·구간에 따라 서버가 결과 코드 `WRD000057`로 거절했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | `inquiry` | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import SeatAssignmentScheduleRequest

request = SeatAssignmentScheduleRequest(
    menu_id="A1",
    departure_date="20261002",
    departure_time="090000",
    departure_station_name="서울",
    arrival_station_name="부산",
    train_group_code="109",
    room_class_code="1",
    seat_attribute_code="015",
    passenger_count=1,
    standing_detour_division_name="N",
    transfer_type_code="1",
    connection_arrival_station_name="",
)
schedule = client.get_seat_assignment_schedule(request)
for item in schedule.trains:
    print(item.train_no, item.departure_time, item.general_reservation_name)
```

## `get_merge_seats_inquiry`

병합 예약으로 이어 붙일 수 있는 열차 구간과 좌석이 갈리는 중간역을 조회합니다.

```python
KorailClient.get_merge_seats_inquiry(
    request: MergeSeatsInquiryRequest,
) -> MergeSeatsInquiryResponse
```

[병합 예약](../concepts/glossary.md)에서 입석 구간의 첫 홀드를 만든 뒤, 이어 붙일 좌석 구간을 찾을 때 씁니다.
[`MergeSeatsInquiryRequest`][korail_mobile_api.read_payloads.MergeSeatsInquiryRequest]의 `boarding_datetime`과 `run_datetime`에는 출발일과 출발 시각을 이어 붙인 값(`YYYYMMDDHHMMSS`)을 넣고, 역은 이름으로 넘깁니다.
열차 번호는 다섯 자리가 되도록 앞에 0을 채워 보내고, `selected_station_name`이 `None`이면 보내지 않습니다.
요청 객체는 만들 때 `passenger_count`가 1~9의 정수인지 검사하고, 아니면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]를 발생시킵니다.

반환된 `trains`는 [`reserve_merge`](reservations.md#reserve_merge)의 `merge_rows`로 넘깁니다. 전체 순서는 [예약 가이드](../guide/reservations.md)를 참고하세요.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`MergeSeatsInquiryRequest`][korail_mobile_api.read_payloads.MergeSeatsInquiryRequest] | 필수 | 승차·운행 일시, 열차 번호, 출발·도착역 이름, 선택한 중간역 이름, 객실 등급·좌석 속성 코드, 승객 수입니다. |

**반환값**

[`MergeSeatsInquiryResponse`][korail_mobile_api.read_models.MergeSeatsInquiryResponse] — `intermediate_stations`에 중간역([`IntermediateStation`][korail_mobile_api.read_models.IntermediateStation]) 목록, `trains`에 병합 대상 구간([`TrainScheduleItem`][korail_mobile_api.read_models.TrainScheduleItem]) 목록, `merge_reservation_possible_flag`에 병합 예약 가능 표시가 들어 있습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import MergeSeatsInquiryRequest

departure = train.departure_date + train.departure_time  # 첫 홀드를 만든 열차
merge = client.get_merge_seats_inquiry(
    MergeSeatsInquiryRequest(
        boarding_datetime=departure,
        run_datetime=departure,
        train_no=train.train_no,
        departure_station_name=train.departure_station_name,
        arrival_station_name=train.arrival_station_name,
        selected_station_name=None,
        room_class_code="1",
        seat_attribute_code="015",
        passenger_count=1,
    )
)
print([station.name for station in merge.intermediate_stations])
```

## `get_guide_seat_condition`

도우미석 이용 안내를 조회합니다.

```python
KorailClient.get_guide_seat_condition(
    request: GuideSeatConditionRequest,
) -> GuideSeatConditionResponse
```

좌석 속성 코드 하나를 보내고 서버의 안내를 받습니다. 안내 문구는 응답의 `h_msg_txt`에 있습니다.
이 메서드는 서버가 `FAIL`로 응답해도 예외를 발생시키지 않고 `str_result`가 `"FAIL"`인 응답을 반환합니다. 결과 코드 `P058`만은 세션 만료로 보고 예외를 발생시킵니다. 실서버에서는 오류 응답까지만 확인했습니다.

앱이 도우미석에 쓰는 좌석 속성 코드는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
서버는 로그인하지 않은 요청을 결과 코드 `P058`(세션 만료)로 거절하므로 로그인한 뒤 호출하세요. 라이브러리는 로그인 여부를 요청 전에 검사하지 않습니다.
실서버에서는 보낸 코드와 관계없이 `FAIL`과 결과 코드 `MRR800011`이 돌아왔습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`GuideSeatConditionRequest`][korail_mobile_api.read_payloads.GuideSeatConditionRequest] | 필수 | 안내를 받을 좌석 속성 코드(`seat_attribute_code`)입니다. |

**반환값**

[`GuideSeatConditionResponse`][korail_mobile_api.read_models.GuideSeatConditionResponse] — 봉투 필드(`str_result`, `h_msg_cd`, `h_msg_txt`)와 서버 시각 `time_stamp`가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 응답에 `strResult`가 없거나 값이 `SUCC`·`FAIL`이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 응답만 확인 |

**예제**

```python
from korail_mobile_api import GuideSeatConditionRequest

code = input("좌석 속성 코드: ")
guide = client.get_guide_seat_condition(GuideSeatConditionRequest(seat_attribute_code=code))
if guide.str_result == "FAIL":
    print(guide.h_msg_cd, guide.h_msg_txt)
```

## `get_price_fare_quote`

열차 한두 편의 운임을 예매 전에 조회합니다.

```python
KorailClient.get_price_fare_quote(
    request: PriceFareQuoteRequest,
) -> PriceFareQuoteResponse
```

구간마다 [`PriceFareLeg`][korail_mobile_api.read_payloads.PriceFareLeg]를 만들어 [`PriceFareQuoteRequest`][korail_mobile_api.read_payloads.PriceFareQuoteRequest]로 묶습니다. 환승 여정은 두 구간을 탑승 순서대로 넣습니다.
각 구간에는 조회 결과 행의 역 코드, 운행일, 열차 번호, 좌석 속성 코드, 열차군 코드, 열차 종류 코드를 옮겨 넣습니다. 열차 번호는 0을 채우지 않고 넣은 그대로 보냅니다.
`goods_no`가 `None`이면 앱처럼 빈 상품 번호를 보냅니다. 상품 번호는 모든 구간에 넣거나 모든 구간에서 비워야 합니다.
`PriceFareLeg`는 만들 때 필수 필드가 비었거나 쉼표가 들어 있으면, `PriceFareQuoteRequest`는 구간이 1개나 2개가 아니면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]를 발생시킵니다.

받은 금액은 표시용 기준 운임입니다. 결제할 금액은 예약한 뒤 홀드의 `received_amount`를 쓰세요. 할인이 적용되면 결제 금액은 이 운임보다 낮을 수 있습니다.
금액 필드는 서버가 보낸 문자열 그대로이며(예: `"21,600원"`) 숫자로 바꾸지 않습니다. 앱 화면 기준으로 `received_price`는 운임, `received_fare`는 요금(특실 추가 요금 등), `total_amount`는 합계입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`PriceFareQuoteRequest`][korail_mobile_api.read_payloads.PriceFareQuoteRequest] | 필수 | 운임을 조회할 구간 1~2개와 메뉴 ID(기본값 `"11"`)입니다. |

**반환값**

[`PriceFareQuoteResponse`][korail_mobile_api.read_models.PriceFareQuoteResponse] — `fares`에 [`PriceFare`][korail_mobile_api.read_models.PriceFare] 목록이 들어 있습니다. 행마다 구간 순번 `journey_sequence`와 객실 이름 `room_class_name`이 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `request`가 [`PriceFareQuoteRequest`][korail_mobile_api.read_payloads.PriceFareQuoteRequest]가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 일부 구간에만 `goods_no`가 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import PriceFareLeg, PriceFareQuoteRequest

leg = PriceFareLeg(
    departure_station_code=train.departure_station_code,
    arrival_station_code=train.arrival_station_code,
    run_date=train.run_date,
    train_no=train.train_no,
    requested_seat_attribute_code=train.seat_attribute_code,
    train_group_code=train.train_group_code,
    train_class_code=train.train_class_code,
)
quote = client.get_price_fare_quote(PriceFareQuoteRequest(legs=(leg,)))
for fare in quote.fares:
    print(fare.room_class_name, fare.received_price, fare.total_amount)
```
