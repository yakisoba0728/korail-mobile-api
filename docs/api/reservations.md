# 예약

결제 전 예약(홀드)을 만들고, 확인하고, 취소하는 메서드입니다.
예약 메서드는 서버에 실제 홀드를 만들고 [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse]를 반환합니다.
라이브러리는 홀드를 자동으로 결제하거나 취소하지 않으므로, 결제 기한 안에 [`pay_with_card`](payments.md#pay_with_card)로 결제하거나 [`cancel_unpaid_hold`](#cancel_unpaid_hold)로 취소해야 합니다.

흐름:

1. 열차를 조회합니다([`search_trains`](trains.md#search_trains), [`search_transfer_trains`](trains.md#search_transfer_trains)).
2. [`reserve`](#reserve), [`reserve_transfer`](#reserve_transfer), [`reserve_merge`](#reserve_merge) 중 하나로 홀드를 만듭니다.
3. [`get_reservation_history`](#get_reservation_history)나 [`get_ticket_reservation_detail`](#get_ticket_reservation_detail)로 홀드를 확인합니다.
4. 결제하거나 [`cancel_unpaid_hold`](#cancel_unpaid_hold)로 취소합니다.

처음부터 따라 하려면 [예약 가이드](../guide/reservations.md)를 참고하세요.

## `reserve`

열차 한 편에 결제 전 예약(홀드)을 만듭니다.

```python
KorailClient.reserve(
    train: TrainSummary,
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[KorailSeatAssignment] | None = None,
    seat_attribute_code: str | None = None,
) -> ReservationHoldResponse
```

[`search_trains`](trains.md#search_trains)가 반환한 열차 행을 그대로 넘깁니다.
요청 전에 열차의 식별 값(열차 번호, 운행일, 출발 일시, 역 코드와 역 순서 등)이 있는지와 형식이 맞는지 검사하고, `job_type`에 따라 아래 조건을 검사합니다.
검사를 통과하지 못하면 요청을 보내지 않습니다.

| `job_type` | 요청 전 검사 |
|---|---|
| `IMMEDIATE` (일반 예약) | 선택한 객실의 예약 코드가 `"11"`이어야 합니다. 일반실은 `general_reservation_code`, 특실은 `special_reservation_code`를 봅니다. 입석만 남은 열차는 거절합니다. |
| `SEAT_DESIGNATED` (좌석 지정 예약) | `IMMEDIATE`와 같은 검사에 더해, `seats`에 `passengers.total`과 같은 개수의 서로 다른 좌석이 있어야 합니다. |
| `STANDBY` (예약대기) | 일반실만 가능하며 열차의 `wait_reservation_flag`가 `" 9"`여야 합니다. |
| `MERGE_STANDING` (병합 예약의 첫 홀드) | 열차의 `merge_seat_application_flag`가 일반실은 `"A"`·`"G"`, 특실은 `"A"`·`"S"` 중 하나여야 합니다. |

`strResult`가 `FAIL`인 응답은 예외로 바뀝니다. 그 밖의 응답은 그대로 반환하므로 `str_result`가 `SUCC`인지 확인하세요.
`STANDBY`로 만든 홀드는 `payable`이 `False`이며 결제할 수 없습니다. 예약대기 옵션은 [`confirm_standby_hold`](#confirm_standby_hold)로 저장합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `train` | [`TrainSummary`][korail_mobile_api.models.TrainSummary] | 필수 | 예약할 열차입니다. 조회 결과의 행을 그대로 넘깁니다. |
| `passengers` | [`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts] \| `None` | `None` | 승객 구성입니다. `None`이면 어른 1명입니다. 유아가 있는데 어린이·유아 외의 승객이 없거나, 안내견이 장애 승객 수보다 많으면 거절합니다. |
| `seat_class` | [`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass] | `KorailSeatClass.GENERAL` | 객실 등급입니다. `GENERAL`(일반실) 또는 `SPECIAL`(특실)입니다. |
| `job_type` | [`KorailReservationJobType`][korail_mobile_api.constants.KorailReservationJobType] | `KorailReservationJobType.IMMEDIATE` | 예약 종류입니다. 위 표를 참고하세요. |
| `seats` | `Sequence[`[`KorailSeatAssignment`][korail_mobile_api.mutation_models.KorailSeatAssignment]`]` \| `None` | `None` | 지정할 좌석입니다. `job_type`이 `SEAT_DESIGNATED`일 때만 넣고, 승객 한 명에 한 좌석씩 넣습니다. |
| `seat_attribute_code` | `str` \| `None` | `None` | 숫자 3자리 좌석 속성 코드입니다. `None`이면 열차의 `seat_attribute_code`를, 그것도 없으면 `"015"`를 보냅니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] — 만들어진 홀드입니다. 예약 번호 `pnr_no`, 결제할 금액 `received_amount`, 결제 기한 `payment_deadline_date`·`payment_deadline_time`, 여정 목록 `journeys`가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 요청 전 검사에 실패했을 때(위 표의 조건, 승객 조합, 열차 식별 값, 좌석 수·중복, `seat_attribute_code` 형식, `seat_class`·`job_type` 값). 응답의 좌석별 정산액 합계와 총 정산액이 다를 때처럼 응답을 읽지 못했을 때도 발생하며, 이때 홀드는 이미 만들어졌을 수 있습니다. |
| [`KorailSoldOutError`][korail_mobile_api.errors.KorailSoldOutError] | 서버가 매진으로 응답했을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.errors.KorailSeatUnavailableError] | 서버가 지정 좌석을 이용할 수 없다고 응답했을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.errors.KorailReservationRefusedError] | 서버가 중복 예약, 구매 한도, 예약 가능 시간 등의 이유로 예약을 거절했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | `reserve` | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 좌석을 점유하는 홀드가 실제로 만들어집니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import KorailPassengerCounts, TrainSearchQuery

query = TrainSearchQuery(
    departure_station_code="서울",
    arrival_station_code="부산",
    departure_date="20261002",
    departure_time="090000",
    passengers=2,
)
result = client.search_trains(query)
train = next(t for t in result.trains if t.general_reservation_code == "11")
hold = client.reserve(train, passengers=KorailPassengerCounts(adult=2))
print(hold.pnr_no, hold.received_amount, hold.payment_deadline_date, hold.payment_deadline_time)
```

## `reserve_transfer`

환승 여정의 두 열차를 한 PNR로 홀드합니다.

```python
KorailClient.reserve_transfer(
    legs: Sequence[TrainSummary],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_classes: Sequence[KorailSeatClass] | KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.IMMEDIATE,
    seats: Sequence[Sequence[KorailSeatAssignment]] | None = None,
    seat_attribute_codes: Sequence[str | None] | None = None,
) -> ReservationHoldResponse
```

두 구간을 탑승 순서대로 넘깁니다. [`search_transfer_trains`](trains.md#search_transfer_trains) 결과의 [`TransferItinerary`][korail_mobile_api.models.TransferItinerary]에서 `legs`를 그대로 넘길 수 있습니다.
두 구간은 서로 다른 열차여야 합니다(열차 번호와 운행일이 모두 같으면 거절합니다). 두 번째 구간은 첫 구간보다 늦게 출발해야 하고, 첫 구간의 도착 일시(`arrival_date`, `arrival_time`)가 있으면 그 이후에 출발해야 합니다.

`passengers`와 `job_type`은 두 구간에 함께 적용됩니다. 구간마다 [`reserve`](#reserve)와 같은 예약 가능 여부를 검사합니다.
`STANDBY`로 만든 홀드는 `payable`이 `False`입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `legs` | `Sequence[`[`TrainSummary`][korail_mobile_api.models.TrainSummary]`]` | 필수 | 탑승 순서대로 놓은 두 구간입니다. 정확히 두 개여야 합니다. |
| `passengers` | [`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts] \| `None` | `None` | 두 구간에 같이 쓰는 승객 구성입니다. `None`이면 어른 1명입니다. |
| `seat_classes` | `Sequence[`[`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass]`]` \| [`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass] | `KorailSeatClass.GENERAL` | 객실 등급입니다. 값 하나나 원소가 하나인 목록은 두 구간에 같이 쓰고, 두 개짜리 목록은 구간 순서대로 씁니다. |
| `job_type` | [`KorailReservationJobType`][korail_mobile_api.constants.KorailReservationJobType] | `KorailReservationJobType.IMMEDIATE` | 두 구간에 같이 쓰는 예약 종류입니다. |
| `seats` | `Sequence[Sequence[`[`KorailSeatAssignment`][korail_mobile_api.mutation_models.KorailSeatAssignment]`]]` \| `None` | `None` | `job_type`이 `SEAT_DESIGNATED`일 때 구간마다 좌석 목록을 하나씩 넣습니다. 각 목록에는 승객 한 명에 한 좌석씩 넣습니다. |
| `seat_attribute_codes` | `Sequence[str | None]` \| `None` | `None` | 구간마다 하나씩 넣는 좌석 속성 코드입니다. `None`인 자리는 [`reserve`](#reserve)의 `seat_attribute_code`와 같은 규칙으로 정합니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] — 두 구간을 한 PNR로 묶은 홀드입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `legs`가 [`TrainSummary`][korail_mobile_api.models.TrainSummary] 두 개가 아니거나, 같은 열차이거나, 탑승 순서가 아닐 때. `seat_classes`·`seats`·`seat_attribute_codes`의 개수가 구간 수와 맞지 않을 때. 구간마다 [`reserve`](#reserve)와 같은 요청 전 검사에 실패했을 때 |
| [`KorailSoldOutError`][korail_mobile_api.errors.KorailSoldOutError] | 서버가 매진으로 응답했을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.errors.KorailSeatUnavailableError] | 서버가 지정 좌석을 이용할 수 없다고 응답했을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.errors.KorailReservationRefusedError] | 서버가 중복 예약, 구매 한도, 예약 가능 시간 등의 이유로 예약을 거절했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | `reserve` | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 두 구간의 좌석을 점유하는 홀드가 실제로 만들어집니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import KorailPassengerCounts, TrainSearchQuery

query = TrainSearchQuery("강릉", "목포", "20261002", "080000", passengers=2)
transfer = client.search_transfer_trains(query)
itinerary = transfer.itineraries[0]
hold = client.reserve_transfer(itinerary.legs, passengers=KorailPassengerCounts(adult=2))
print(hold.pnr_no, hold.received_amount)
```

## `reserve_merge`

병합 예약의 후속 홀드를 만듭니다.

```python
KorailClient.reserve_merge(
    standing_hold_train: TrainSummary,
    merge_rows: Sequence[TrainScheduleItem],
    *,
    passengers: KorailPassengerCounts | None = None,
    seat_class: KorailSeatClass = KorailSeatClass.GENERAL,
    job_type: KorailReservationJobType = KorailReservationJobType.MERGE_STANDING,
    seat_attribute_code: str | None = None,
) -> ReservationHoldResponse
```

병합 예약은 앱과 같은 순서로 네 단계를 거칩니다. 이 메서드는 마지막 단계의 요청 하나만 보냅니다.

1. [`reserve`](#reserve)에 `job_type=KorailReservationJobType.MERGE_STANDING`을 넣어 첫 홀드를 만듭니다.
2. [`get_merge_seats_inquiry`](trains.md#get_merge_seats_inquiry)로 병합할 열차 행을 조회합니다.
3. [`cancel_unpaid_hold`](#cancel_unpaid_hold)로 첫 홀드를 취소합니다.
4. 이 메서드로 후속 홀드를 만듭니다.

첫 홀드, 병합 조회, 첫 홀드 취소는 이 메서드가 대신 보내지 않습니다. 첫 홀드는 호출자가 취소해야 하며, 후속 홀드는 첫 홀드와 다른 PNR일 수 있습니다.

라이브러리는 첫 홀드 요청을 보관하지 않습니다. `standing_hold_train`, `passengers`, `seat_class`, `job_type`, `seat_attribute_code`로 첫 홀드와 같은 요청을 다시 만든 뒤 입석 여부와 중간역 값만 바꿔 보냅니다.
따라서 첫 홀드를 만들 때와 같은 값을 넘기세요. 중간역은 `merge_rows` 첫 행의 도착역이고, 입석 여부는 병합 행의 예약 코드로 정합니다.
이 메서드는 대기열을 거치지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `standing_hold_train` | [`TrainSummary`][korail_mobile_api.models.TrainSummary] | 필수 | 첫 홀드를 만들 때 넘긴 열차입니다. |
| `merge_rows` | `Sequence[`[`TrainScheduleItem`][korail_mobile_api.read_models.TrainScheduleItem]`]` | 필수 | [`get_merge_seats_inquiry`](trains.md#get_merge_seats_inquiry)가 반환한 `trains`입니다. 모든 행의 열차 번호가 `standing_hold_train`과 같아야 하고, 행에 운행일이 있으면 운행일도 같아야 합니다. 첫 행에는 도착역 코드와 도착역 순서 값이 있어야 합니다. |
| `passengers` | [`KorailPassengerCounts`][korail_mobile_api.mutation_models.KorailPassengerCounts] \| `None` | `None` | 첫 홀드와 같은 승객 구성입니다. `None`이면 어른 1명입니다. |
| `seat_class` | [`KorailSeatClass`][korail_mobile_api.constants.KorailSeatClass] | `KorailSeatClass.GENERAL` | 첫 홀드와 같은 객실 등급입니다. |
| `job_type` | [`KorailReservationJobType`][korail_mobile_api.constants.KorailReservationJobType] | `KorailReservationJobType.MERGE_STANDING` | 첫 홀드와 같은 예약 종류입니다. |
| `seat_attribute_code` | `str` \| `None` | `None` | 첫 홀드와 같은 좌석 속성 코드입니다. `None`이면 [`reserve`](#reserve)와 같은 규칙으로 정합니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] — 후속 홀드입니다. 첫 홀드와 다른 PNR일 수 있으므로 이후 결제와 취소에는 이 값을 씁니다. 병합 홀드의 `payable`은 `True`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `merge_rows`가 비었거나 [`TrainScheduleItem`][korail_mobile_api.read_models.TrainScheduleItem]이 아닌 값이 있을 때. 행의 열차 번호나 운행일이 `standing_hold_train`과 다를 때. 첫 행에 중간역 값이 없을 때. `job_type`이 `MERGE_STANDING`인데 열차가 병합 대상이 아닐 때. 그 밖의 [`reserve`](#reserve)와 같은 요청 전 검사에 실패했을 때 |
| [`KorailSoldOutError`][korail_mobile_api.errors.KorailSoldOutError] | 서버가 매진으로 응답했을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.errors.KorailReservationRefusedError] | 서버가 중복 예약, 구매 한도, 예약 가능 시간 등의 이유로 예약을 거절했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 좌석을 점유하는 후속 홀드가 실제로 만들어집니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

병합 조회 요청을 만드는 방법은 [예약 가이드의 병합 예약](../guide/reservations.md#merge)을 참고하세요.

```python
from korail_mobile_api import KorailReservationJobType

# train: 병합 대상 열차, merge_request: 이 열차의 MergeSeatsInquiryRequest
first = client.reserve(train, job_type=KorailReservationJobType.MERGE_STANDING)
merge = client.get_merge_seats_inquiry(merge_request)
client.cancel_unpaid_hold(first)
hold = client.reserve_merge(train, merge.trains)
print(hold.pnr_no, hold.received_amount)
```

## `confirm_standby_hold`

예약대기 홀드에 문자 알림과 객실 등급 변경 옵션을 저장합니다.

```python
KorailClient.confirm_standby_hold(
    hold: ReservationHoldResponse,
    *,
    allow_seat_class_change: bool = False,
    sms_notify: bool = False,
    phone_no: str | None = None,
) -> BaseKorailResponse
```

[`reserve`](#reserve)나 [`reserve_transfer`](#reserve_transfer)에 `job_type=KorailReservationJobType.STANDBY`를 넣어 만든 홀드에 씁니다.
기존 홀드의 옵션만 저장하며 새 예약이나 결제를 만들지 않습니다.
`hold`의 `str_result`가 `SUCC`이고 `pnr_no`가 있어야 합니다. 홀드가 예약대기인지는 검사하지 않으므로 예약대기 홀드만 넘기세요.

`phone_no`는 `sms_notify`가 `True`일 때만 보냅니다. `sms_notify`가 `False`이면 `phone_no`는 검사하지도 보내지도 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `hold` | [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] | 필수 | 예약대기로 만든 홀드입니다. |
| `allow_seat_class_change` | `bool` | `False` | 객실 등급 변경을 허용할지 여부입니다. |
| `sms_notify` | `bool` | `False` | 문자 알림을 받을지 여부입니다. |
| `phone_no` | `str` \| `None` | `None` | 알림을 받을 휴대전화 번호입니다. 하이픈 없는 숫자 11자리여야 합니다. |

**반환값**

[`BaseKorailResponse`][korail_mobile_api.models.BaseKorailResponse] — 봉투(`str_result`, `h_msg_cd`, `h_msg_txt`)만 담은 응답입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `hold`의 `str_result`가 `SUCC`가 아니거나 `pnr_no`가 없을 때. `allow_seat_class_change`나 `sms_notify`가 `bool`이 아닐 때. `sms_notify`가 `True`인데 `phone_no`가 숫자 11자리가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 예약대기 홀드에 알림·객실 등급 변경 옵션이 실제로 저장됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import KorailReservationJobType

# result: search_trains 결과
train = next(t for t in result.trains if t.wait_reservation_flag == " 9")
standby = client.reserve(train, job_type=KorailReservationJobType.STANDBY)
response = client.confirm_standby_hold(
    standby,
    sms_notify=True,
    phone_no=input("휴대전화 번호(숫자 11자리): "),
)
print(response.h_msg_cd)
```

## `cancel_unpaid_hold`

결제하지 않은 홀드를 취소합니다.

```python
KorailClient.cancel_unpaid_hold(
    hold: ReservationHoldResponse,
    *,
    check_first: bool = True,
) -> BaseKorailResponse
```

예약 메서드가 반환한 홀드를 그대로 넘깁니다.
`hold`의 `str_result`가 `SUCC`이고, `pnr_no`와 `journey_count`(1 이상의 숫자 문자열)가 있어야 합니다.
요청에는 이 값과 첫 여정의 순번·변경 번호를 싣습니다. 첫 여정에 값이 없으면 각각 `"0001"`과 `"000"`을 보냅니다.

`check_first`가 `True`(기본값)이면 앱과 같이 취소 가능 여부를 먼저 확인한 뒤 취소 요청을 보냅니다. 확인 요청이 실패하면 예외가 발생하고 취소 요청은 보내지 않습니다.
`check_first`가 `False`이면 확인 없이 취소 요청만 보냅니다. 어느 요청도 자동으로 다시 보내지 않습니다.

발권된 승차권에는 쓰지 않습니다. 발권된 승차권은 [`refund`](payments.md#refund)로 환불합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `hold` | [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse] | 필수 | 취소할 홀드입니다. |
| `check_first` | `bool` | `True` | 취소 가능 여부를 먼저 확인할지 여부입니다. |

**반환값**

[`BaseKorailResponse`][korail_mobile_api.models.BaseKorailResponse] — 취소 요청의 응답입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `hold`가 [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse]가 아니거나, `str_result`가 `SUCC`가 아니거나, `pnr_no`가 비었거나, `journey_count`가 1 이상의 숫자 문자열이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 홀드가 실제로 취소됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
# train: search_trains로 찾은 열차
hold = client.reserve(train)
response = client.cancel_unpaid_hold(hold)
print(response.str_result, response.h_msg_cd)
```

## `get_reservation_history`

로그인 계정에 남아 있는 예약(결제 전 홀드 포함)을 조회합니다.

```python
KorailClient.get_reservation_history() -> ReservationHistoryResponse
```

예약 메서드가 예외로 끝났을 때 홀드가 실제로 만들어졌는지 확인하는 데 씁니다.

남아 있는 예약이 없으면 서버는 결과 코드 `P100`의 실패 응답을 보냅니다. 이 메서드는 이때 예외를 발생시키지 않고, `str_result`가 `FAIL`이고 `h_msg_cd`가 `P100`이며 목록이 빈 응답을 반환합니다. 다른 실패 코드는 예외로 바뀝니다.

응답은 두 가지 모양으로 읽을 수 있습니다.
`journeys`는 여정([`ReservationHistoryJourney`][korail_mobile_api.read_models.ReservationHistoryJourney])마다 열차 목록과 예약·운임 정보(`reservation`)를 담습니다.
`trains`(`items`와 같습니다)는 모든 여정의 열차 행([`ReservationHistoryTrain`][korail_mobile_api.read_models.ReservationHistoryTrain])을 한 목록으로 담습니다.
열차 행에는 `pnr_no`와 결제 기한 필드(`payment_deadline_date`, `payment_deadline_time`)가 있지만, 기한 값이 채워져 오는지는 확인하지 못했습니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`ReservationHistoryResponse`][korail_mobile_api.read_models.ReservationHistoryResponse] — 남아 있는 예약의 여정·열차 목록입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | `reservation_view` | 아니요 | 확인됨 |

**예제**

```python
history = client.get_reservation_history()
if history.h_msg_cd == "P100":
    print("남아 있는 예약이 없습니다.")
for row in history.trains:
    print(row.pnr_no, row.train_no, row.run_date, row.departure_time, row.reserved_amount)
```

## `get_ticket_reservation_detail`

PNR로 예약 하나의 여정과 좌석 상세를 다시 읽습니다.

```python
KorailClient.get_ticket_reservation_detail(
    request: TicketReservationDetailRequest,
) -> TicketReservationDetailResponse
```

[`TicketReservationDetailRequest`][korail_mobile_api.read_payloads.TicketReservationDetailRequest]에 홀드의 `pnr_no`를 넣어 넘깁니다. `pnr_no`가 비어 있으면 요청 객체를 만들 때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
응답의 `journeys`에는 여정([`ReservationDetailJourney`][korail_mobile_api.read_models.ReservationDetailJourney])마다 좌석([`ReservationSeatDetail`][korail_mobile_api.read_models.ReservationSeatDetail]) 목록이 있습니다. 좌석마다 호차 번호, 좌석 번호, 객실 등급, 정산액이 들어 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`TicketReservationDetailRequest`][korail_mobile_api.read_payloads.TicketReservationDetailRequest] | 필수 | 조회할 예약의 PNR입니다. |

**반환값**

[`TicketReservationDetailResponse`][korail_mobile_api.read_models.TicketReservationDetailResponse] — PNR, 총 정산액 `total_received_amount`, 여정·좌석 목록입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `request`가 [`TicketReservationDetailRequest`][korail_mobile_api.read_payloads.TicketReservationDetailRequest]가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import TicketReservationDetailRequest

# hold: reserve가 반환한 홀드
detail = client.get_ticket_reservation_detail(TicketReservationDetailRequest(pnr_no=hold.pnr_no))
for journey in detail.journeys:
    for seat in journey.seats:
        print(journey.train_no, seat.car_no, seat.seat_no, seat.received_amount)
```

## `check_ticket_duplication`

같은 PNR로 잡혀 있는 예약 건수를 조회합니다.

```python
KorailClient.check_ticket_duplication(
    request: TicketDuplicationCheckRequest,
) -> TicketDuplicationCheckResponse
```

[`TicketDuplicationCheckRequest`][korail_mobile_api.read_payloads.TicketDuplicationCheckRequest]에 PNR을 넣어 넘깁니다. `pnr_no`가 비어 있으면 요청 객체를 만들 때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
결과의 `reservation_count`는 숫자로 바꾸지 않고 서버가 보낸 문자열 그대로 담습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`TicketDuplicationCheckRequest`][korail_mobile_api.read_payloads.TicketDuplicationCheckRequest] | 필수 | 확인할 예약의 PNR입니다. |

**반환값**

[`TicketDuplicationCheckResponse`][korail_mobile_api.read_models.TicketDuplicationCheckResponse] — 예약 건수 `reservation_count`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `request`가 [`TicketDuplicationCheckRequest`][korail_mobile_api.read_payloads.TicketDuplicationCheckRequest]가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import TicketDuplicationCheckRequest

# hold: reserve가 반환한 홀드
result = client.check_ticket_duplication(TicketDuplicationCheckRequest(pnr_no=hold.pnr_no))
print(result.reservation_count)
```

## `get_cart_list`

로그인 계정의 장바구니를 조회합니다.

```python
KorailClient.get_cart_list(
    pnr_no: str = '',
    additional_service_request_no: str = '',
) -> CartListResponse
```

장바구니의 행([`CartItem`][korail_mobile_api.read_models.CartItem])은 열차·공항버스 예약이나 부가서비스 한 건입니다.
행마다 `pnr_no`, 상품 이름 `product_name`, 정산액 `received_amount`, 출발일 `departure_date` 등이 들어 있습니다. 부가서비스의 중첩 결제 상세는 모델 필드로 옮기지 않고 행의 `raw`에만 남깁니다.

두 매개변수는 앱과 같은 요청 필드로 보내며, 빈 문자열(기본값)이면 보내지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `pnr_no` | `str` | `''` | 요청에 함께 보낼 예약 번호입니다. |
| `additional_service_request_no` | `str` | `''` | 요청에 함께 보낼 부가서비스 신청 번호입니다. |

**반환값**

[`CartListResponse`][korail_mobile_api.read_models.CartListResponse] — `items`에 장바구니 행 목록이 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `pnr_no`나 `additional_service_request_no`가 문자열이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
cart = client.get_cart_list()
for item in cart.items:
    print(item.pnr_no, item.product_name, item.received_amount)
```

## `add_to_cart`

결제 전 홀드를 장바구니에 담습니다.

```python
KorailClient.add_to_cart(request: CartAddRequest) -> CartAddResponse
```

[`CartAddRequest`][korail_mobile_api.mutation_models.CartAddRequest]에 홀드의 `pnr_no`를 넣어 넘깁니다. 요청에는 공통 필드와 PNR만 싣습니다.
응답의 `discount_additions`에는 서버가 돌려준 승객별 할인 행([`CartDiscountAddition`][korail_mobile_api.mutation_models.CartDiscountAddition])이 들어 있으며, 행이 없으면 빈 튜플입니다.
할인을 재계산한 홀드는 [`recalculate_price`](payments.md#recalculate_price)에 `add_to_cart=True`를 넘겨 재계산 뒤에 바로 담을 수도 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`CartAddRequest`][korail_mobile_api.mutation_models.CartAddRequest] | 필수 | 장바구니에 담을 홀드의 PNR입니다. |

**반환값**

[`CartAddResponse`][korail_mobile_api.mutation_models.CartAddResponse] — 추가 결과와 승객별 할인 행 `discount_additions`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `request`가 [`CartAddRequest`][korail_mobile_api.mutation_models.CartAddRequest]가 아니거나 `pnr_no`가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 확인됨 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 홀드가 계정의 장바구니에 실제로 추가됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import CartAddRequest

# hold: reserve가 반환한 홀드
added = client.add_to_cart(CartAddRequest(pnr_no=hold.pnr_no))
print(added.h_msg_cd, len(added.discount_additions))
cart = client.get_cart_list()
```
