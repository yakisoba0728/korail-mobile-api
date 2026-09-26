# 공항버스·부가서비스

이 페이지는 공항버스(리무진)와 부가서비스 메서드를 설명합니다.
공항버스 메서드는 운행 편과 좌석을 조회하고, 좌석을 잡아 결제 전 예약(홀드)을 만듭니다.
부가서비스 메서드는 코레일+ 앱의 부가서비스 메뉴, 서비스별 이용 역, 계정이 신청한 부가서비스 내역을 조회만 합니다.
부가서비스(렌터카, 짐 배송 등)를 신청하거나 구매·결제·취소하는 기능은 지원하지 않습니다.

공항버스 흐름:

1. [`get_limousine_schedules`](#get_limousine_schedules)로 운행 편을 조회합니다.
2. 고른 편으로 [`get_limousine_seat_inventory`](#get_limousine_seat_inventory)를 호출해 좌석을 조회합니다.
3. [`reserve_limousine`](#reserve_limousine)에 편과 좌석 번호를 넘겨 홀드를 만듭니다.
4. 홀드는 열차 홀드와 같이 [`pay_with_card`](payments.md#pay_with_card)로 결제하거나 [`cancel_unpaid_hold`](reservations.md#cancel_unpaid_hold)로 취소합니다.

공항버스 메서드는 대기열을 거치지 않습니다.

## `get_limousine_schedules`

공항버스 운행 편 한 페이지를 조회합니다.

```python
KorailClient.get_limousine_schedules(
    query: LimousineScheduleQuery,
) -> LimousineScheduleResponse
```

조회 조건은 [`LimousineScheduleQuery`][korail_mobile_api.limousine_models.LimousineScheduleQuery]로 만듭니다. 아홉 필드가 모두 필수이며, 라이브러리는 값을 검사하거나 기본값을 채우지 않고 그대로 보냅니다.
빈 문자열을 넣은 필드는 요청에서 빠집니다. 각 코드의 전체 목록은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.

| 필드 | 요청 키 | 설명 |
|---|---|---|
| `departure_date` | `dptDt` | 출발일(`YYYYMMDD`)입니다. |
| `departure_station_code`, `arrival_station_code` | `dptRsStnCd`, `arvRsStnCd` | 출발·도착 정류장 코드입니다. |
| `service_code` | `trnGpCd` | 운행 그룹 코드입니다. |
| `room_class_code` | `psrmClCd` | 객실 등급 코드입니다. [`reserve_limousine`](#reserve_limousine)은 `"1"`을 보냅니다. |
| `departure_time` | `dptTm` | 출발 시각(`HHMMSS`)입니다. |
| `train_no` | `trnNo` | 편 번호입니다. |
| `seat_attribute_code` | `seatAttCd` | 좌석 속성 코드입니다. [`reserve_limousine`](#reserve_limousine)은 `"015"`를 보냅니다. |
| `reservation_sale_division_code` | `rsvSaleDvCd` | 예약 판매 구분 코드입니다. |

이 메서드는 서버가 돌려준 한 페이지만 반환합니다. 다음 페이지를 이어서 조회하는 매개변수는 없습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`LimousineScheduleQuery`][korail_mobile_api.limousine_models.LimousineScheduleQuery] | 필수 | 조회 조건입니다. |

**반환값**

[`LimousineScheduleResponse`][korail_mobile_api.limousine_models.LimousineScheduleResponse] — `schedules`에 운행 편이 [`LimousineSchedule`][korail_mobile_api.limousine_models.LimousineSchedule] 목록으로 들어 있습니다.
편마다 운행일, 편 번호, 출발·도착 정류장 코드와 시각, 잔여석 수(`general_remaining_seat_count` 등), 운임 문자열(`received_price`)이 있습니다. 응답의 편 목록(`trainList`)이 없거나 `null`이면 빈 튜플입니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import LimousineScheduleQuery

query = LimousineScheduleQuery(
    departure_date="20261002",
    departure_station_code=input("출발 정류장 코드: "),
    arrival_station_code=input("도착 정류장 코드: "),
    service_code=input("운행 그룹 코드: "),
    room_class_code="1",
    departure_time="090000",
    train_no="",
    seat_attribute_code="015",
    reservation_sale_division_code="",
)
schedules = client.get_limousine_schedules(query)
for bus in schedules.schedules:
    print(bus.train_no, bus.departure_time, bus.general_remaining_seat_count, bus.received_price)
```

## `get_limousine_seat_inventory`

공항버스 한 편의 좌석 배치와 좌석별 판매 가능 여부를 조회합니다.

```python
KorailClient.get_limousine_seat_inventory(
    query: LimousineSeatInventoryQuery,
) -> LimousineSeatInventoryResponse
```

조회 조건은 [`LimousineSeatInventoryQuery`][korail_mobile_api.limousine_models.LimousineSeatInventoryQuery]로 만듭니다.
열차 종류·운행 그룹 코드, 운행일, 편 번호, 출발·도착 정류장 코드와 순서는 [`get_limousine_schedules`](#get_limousine_schedules)가 반환한 [`LimousineSchedule`][korail_mobile_api.limousine_models.LimousineSchedule]의 같은 이름 필드(`train_class_code`, `service_code`, `run_date`, `train_no`, `departure_station_code`, `arrival_station_code`, `departure_run_order`, `arrival_run_order`)에서 옮깁니다.
[`reserve_limousine`](#reserve_limousine)은 호차 번호를 항상 `"0001"`로 보내므로 좌석도 같은 호차(`car_no="0001"`)로 조회하세요.

`passenger_count`는 인원 수이며, 이 조회에서는 1~9 범위를 검사하지 않습니다. `product_no`가 `None`(기본값)이면 보내지 않고, `is_arrow`는 `"true"`나 `"false"`로 보냅니다(기본값 `False`).
[`LimousineSeatInventoryQuery`][korail_mobile_api.limousine_models.LimousineSeatInventoryQuery]를 만들 때 `passenger_count`가 `int`가 아니거나 `is_arrow`가 `bool`이 아니면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`LimousineSeatInventoryQuery`][korail_mobile_api.limousine_models.LimousineSeatInventoryQuery] | 필수 | 조회 조건입니다. |

**반환값**

[`LimousineSeatInventoryResponse`][korail_mobile_api.limousine_models.LimousineSeatInventoryResponse] — `seats`에 좌석이 [`LimousineSeat`][korail_mobile_api.limousine_models.LimousineSeat] 목록으로 들어 있습니다.
좌석마다 좌석 번호(`seat_no`)와 판매 가능 표시(`sale_possible_flag`)가 있습니다. 응답에는 이 밖에 호차 번호, 배치 형식(`layout_type`), 창문 위치(`windows`)가 있습니다. 좌석 목록(`seatList`)이 없거나 `null`이면 빈 튜플입니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import LimousineSeatInventoryQuery

bus = schedules.schedules[0]
seat_query = LimousineSeatInventoryQuery(
    train_class_code=bus.train_class_code,
    service_code=bus.service_code,
    run_date=bus.run_date,
    train_no=bus.train_no,
    car_no="0001",
    room_class_code="1",
    departure_station_code=bus.departure_station_code,
    arrival_station_code=bus.arrival_station_code,
    seat_attribute_code="015",
    departure_run_order=bus.departure_run_order,
    arrival_run_order=bus.arrival_run_order,
    passenger_count=2,
)
inventory = client.get_limousine_seat_inventory(seat_query)
free = [seat.seat_no for seat in inventory.seats if seat.sale_possible_flag == "Y"]
```

## `reserve_limousine`

공항버스 좌석을 잡아 결제 전 예약(홀드)을 만듭니다.

```python
KorailClient.reserve_limousine(
    schedule: LimousineSchedule,
    seat_nos: Sequence[str],
    *,
    passengers: KorailPassengerCounts | None = None,
) -> ReservationHoldResponse
```

열차 예약과 같은 예약 요청으로 보내며, 좌석은 모두 호차 `"0001"`에 객실 등급 `"1"`로 보냅니다. 열차 예약과 달리 대기열을 거치지 않습니다.
승객은 어른과 어린이만 넣을 수 있고, 좌석 번호는 전체 인원 수와 같은 개수로 서로 다르게 넣어야 합니다.
라이브러리는 좌석의 판매 가능 여부를 확인하지 않으므로 [`get_limousine_seat_inventory`](#get_limousine_seat_inventory) 결과에서 판매 가능한 좌석을 고르세요.

요청을 보내기 전에 다음을 검사합니다.

- `schedule`의 `train_no`, `train_class_code`, `service_code`가 비어 있지 않은지
- `run_date`, `departure_date`가 숫자 8자리이고 `departure_time`이 숫자 6자리인지
- 출발·도착 정류장 코드와 순서가 숫자인지
- `general_remaining_seat_count`가 숫자일 때 인원 수보다 적지 않은지

반환된 홀드는 [`pay_with_card`](payments.md#pay_with_card)로 결제하거나 [`cancel_unpaid_hold`](reservations.md#cancel_unpaid_hold)로 취소합니다. 실패해도 자동으로 다시 보내지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `schedule` | [`LimousineSchedule`][korail_mobile_api.limousine_models.LimousineSchedule] | 필수 | 예약할 편입니다. [`get_limousine_schedules`](#get_limousine_schedules) 결과의 `schedules` 원소를 넘깁니다. |
| `seat_nos` | `Sequence[str]` | 필수 | 예약할 좌석 번호입니다. 좌석 조회 결과의 `seat_no`를 인원 수만큼 넣습니다. |
| `passengers` | [`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts] \| `None` | `None` | 승객 구성입니다. `adult`와 `child`만 쓸 수 있습니다. `None`이면 어른 1명입니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] — 만들어진 홀드입니다. `pnr_no`, 결제할 금액(`received_amount`), 결제 기한(`payment_deadline_date`, `payment_deadline_time`)이 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `schedule`이 [`LimousineSchedule`][korail_mobile_api.limousine_models.LimousineSchedule]이 아니거나 위 검사를 통과하지 못했을 때, `passengers`가 [`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts]가 아니거나 어른·어린이 외의 승객이 있을 때, `seat_nos`가 시퀀스가 아니거나 문자열·바이트일 때, 문자열이 아니거나 빈 좌석 번호, 중복 좌석 번호가 있을 때, 좌석 수가 전체 인원 수와 다를 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 공항버스 좌석이 실제로 점유되고 결제 전 예약이 만들어집니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import KorailPassengerCounts

hold = client.reserve_limousine(
    bus,
    free[:2],
    passengers=KorailPassengerCounts(adult=1, child=1),
)
print(hold.pnr_no, hold.received_amount, hold.payment_deadline_date, hold.payment_deadline_time)
```

## `get_maas_menu_list`

부가서비스 메뉴를 조회합니다. 전체 메뉴나 승차권 한 건에 대한 메뉴를 받을 수 있습니다.

```python
KorailClient.get_maas_menu_list(
    *,
    pnr_no: str | None = None,
    ticket_return_numbers: Sequence[str] | None = None,
) -> MaasMenuListResponse
```

두 매개변수를 모두 생략하면 전체 메뉴를 조회합니다. 전체 메뉴 조회는 로그인 여부를 검사하지 않으며, 요청 시각(밀리초)을 함께 보냅니다.
`pnr_no`나 `ticket_return_numbers`를 넘기면 그 승차권의 메뉴를 조회합니다. 이때는 로그인이 필요하고 두 값을 모두 넣어야 합니다.
승차권 반환 번호는 넘긴 순서대로 같은 키(`tkRetNo`)로 반복해 보내며, 라이브러리는 형식을 검사하지 않습니다.

메뉴 항목의 `uses_station_selection`은 항목이 역 선택을 쓰는지 판정합니다. 참이면 `additional_service_code`로 [`get_maas_station_data`](#get_maas_station_data)를 호출할 수 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `pnr_no` | `str` \| `None` | `None` | 승차권별 메뉴를 조회할 PNR입니다. |
| `ticket_return_numbers` | `Sequence[str]` \| `None` | `None` | 승차권별 메뉴를 조회할 승차권 반환 번호입니다. 하나 이상 넣습니다. |

**반환값**

[`MaasMenuListResponse`][korail_mobile_api.models.MaasMenuListResponse] — `items`에 메뉴 항목이 [`MaasMenuItem`][korail_mobile_api.models.MaasMenuItem] 목록으로 들어 있습니다. 항목마다 이름, 부가서비스 코드(`additional_service_code`), 활성 여부(`active`), 링크 주소(`url`) 등이 있습니다.
응답에 있으면 출발역·도착역 안내 주소(엘리베이터, 주차장 등)도 함께 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | `pnr_no`나 `ticket_return_numbers`를 넘겼는데 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 승차권별 조회에서 `pnr_no`가 비었거나 없을 때, `ticket_return_numbers`가 없거나 비었을 때, 문자열·바이트일 때, 빈 값이나 문자열이 아닌 값이 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
menu = client.get_maas_menu_list()
for item in menu.items:
    print(item.name, item.additional_service_code, item.uses_station_selection)
```

## `get_maas_station_data`

부가서비스 하나를 이용할 수 있는 역 목록을 조회합니다.

```python
KorailClient.get_maas_station_data(additional_service_code: str) -> StationDataResponse
```

부가서비스 코드 하나만 보내며 공통 필드는 붙이지 않습니다. 응답에 `strResult`가 없어도 실패로 보지 않습니다.
반환 형식은 [`get_station_data`](session.md#get_station_data)와 같습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `additional_service_code` | `str` | 필수 | 부가서비스 코드입니다. [`get_maas_menu_list`](#get_maas_menu_list) 결과 항목의 `additional_service_code`를 넣습니다. |

**반환값**

[`StationDataResponse`][korail_mobile_api.models.StationDataResponse] — `stations`에 역이 [`KorailStation`][korail_mobile_api.models.KorailStation] 목록으로 들어 있습니다. 역마다 코드(`code`), 이름(`name`), 좌표 등이 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `additional_service_code`가 문자열이 아니거나 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
menu = client.get_maas_menu_list()
item = next(item for item in menu.items if item.uses_station_selection)
stations = client.get_maas_station_data(item.additional_service_code)
for station in stations.stations:
    print(station.code, station.name)
```

## `get_maas_service_details`

로그인한 계정이 신청한 부가서비스 내역을 조회합니다.

```python
KorailClient.get_maas_service_details(
    query: MaasServiceDetailQuery | None = None,
) -> MaasServiceDetailListResponse
```

`query`를 생략하면 `MaasServiceDetailQuery.current()`와 같이 조회 기간을 보내지 않습니다.
기간을 지정하려면 `MaasServiceDetailQuery.history(start_date, end_date)`로 시작일과 종료일(`YYYYMMDD`)을 넣습니다.
[`MaasServiceDetailQuery`][korail_mobile_api.read_payloads.MaasServiceDetailQuery]는 만들 때 날짜가 숫자 8자리인지만 검사하고, 아니면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다. 두 날짜의 순서는 검사하지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | [`MaasServiceDetailQuery`][korail_mobile_api.read_payloads.MaasServiceDetailQuery] \| `None` | `None` | 조회 기간입니다. `None`이면 기간을 보내지 않습니다. |

**반환값**

[`MaasServiceDetailListResponse`][korail_mobile_api.read_models.MaasServiceDetailListResponse] — `details`에 신청 내역이 [`MaasServiceDetail`][korail_mobile_api.read_models.MaasServiceDetail] 목록으로 들어 있습니다.
내역마다 부가서비스 이름, 진행 상태 코드, 요청 번호, 연결된 PNR, 이용 기간이 있고, `detail_info`에 상품·이용·결제 상세([`MaasServiceDetailInfo`][korail_mobile_api.read_models.MaasServiceDetailInfo])가 있습니다. 내역 목록(`addSrvList`)이 없으면 빈 튜플입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import MaasServiceDetailQuery

query = MaasServiceDetailQuery.history("20260101", "20260930")
result = client.get_maas_service_details(query)
for detail in result.details:
    print(detail.additional_service_name, detail.progress_status_code, detail.pnr_no)
```
