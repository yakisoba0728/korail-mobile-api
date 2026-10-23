# 정기권·패스·N카드·여행상품

이 페이지의 메서드는 정기권·패스, N카드, 여행상품의 세 묶음으로 나뉩니다.
묶음마다 앞 메서드가 돌려준 값을 다음 메서드의 입력으로 씁니다.

**정기권·패스**는 조회만 합니다. [`get_pass_menu`](#get_pass_menu)로 메뉴 항목을 읽고, 항목의 `pass_data`([`PassMenuData`][korail_mobile_api.PassMenuData])에 든 종류·기간·연령 코드로 사용 가능일([`get_pass_availability`](#get_pass_availability)), 탈 수 있는 열차([`get_pass_schedule`](#get_pass_schedule)), 예매 조건([`get_commuter_info`](#get_commuter_info))을 조회합니다. 정기권·패스를 구매하는 메서드는 없습니다.

**N카드**는 사용 내역과 이용 가능 열차 조회, 기간 연장, N카드 예약을 제공합니다. N카드 구매·결제는 지원하지 않습니다(결제 전 구매를 만들던 `register_discount_card`는 3.0에서 제거했습니다). 7.0.8에서 스케줄 조회는 서버 오류 `EAZ000028`까지 확인했고, 보유 N카드가 없어 정상 조회와 다른 N카드 메서드는 확인하지 못했습니다.

**여행상품**은 검색·예약·결제를 지원하지 않습니다. 다른 경로로 만든 여행상품 예약을 목록([`list_product_reservations`](#list_product_reservations))과 상세([`get_product_detail`](#get_product_detail))로 조회하고, [`cancel_product_reservation`](#cancel_product_reservation)으로 취소합니다. [`get_trip_menu`](#get_trip_menu)는 여행상품 메뉴 화면의 항목을 읽습니다.

## `get_pass_menu`

정기권·패스 메뉴 한 갈래의 화면 구성 항목을 조회합니다.

```python
KorailClient.get_pass_menu(menu_no: str) -> PassMenuResponse
```

`menu_no`로 메뉴 갈래를 고르면 그 갈래에 속한 항목 목록이 옵니다.
각 항목([`PassMenuItem`][korail_mobile_api.PassMenuItem])에는 제목·안내 문구와 함께, 정기권 조회에 쓰는 `pass_data`([`PassMenuData`][korail_mobile_api.PassMenuData])가 들어 있을 수 있습니다.
`pass_data`는 정기권 종류 코드(`commuter_kind_code`), 연령 선택지(`age_options`), 기간 선택지(`period_options`)를 담으며, 이 페이지의 다른 정기권 메서드가 이 값을 입력으로 씁니다.
항목에 따라 `pass_data`가 없을 수 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `menu_no` | `str` | 필수 | 조회할 메뉴 갈래 번호입니다. 예: `"1"`, `"2"`. 그 밖의 번호는 확인하지 못했습니다. |

**반환값**

[`PassMenuResponse`][korail_mobile_api.PassMenuResponse] — `items`에 메뉴 항목이 [`PassMenuItem`][korail_mobile_api.PassMenuItem] 목록으로 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `menu_no`가 비어 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 응답 파싱 |

**예제**

```python
menu = client.get_pass_menu("1")
for item in menu.items:
    print(item.title, item.item_type)

pass_data = next(item.pass_data for item in menu.items if item.pass_data is not None)
```

<a id="get_pass_available_dates"></a>

## `get_pass_availability`

정기권 상품 하나의 사용 개시 가능일과 발권 가능일을 조회합니다.

```python
KorailClient.get_pass_availability(
    kind_code: str,
    period_code: str,
    age_code: str,
) -> PassAvailabilityResponse
```

세 코드는 [`get_pass_menu`](#get_pass_menu)가 돌려준 `pass_data`에서 가져옵니다.
종류는 `pass_data.commuter_kind_code`, 기간은 `period_options`의 `commuter_period_code`, 연령은 `age_options`의 `commuter_age_code`입니다.

서버는 결과 코드를 최상위 봉투 대신 `main_info.message_code`에 담아 보내기도 합니다.
이 경우 조회 결과가 없어도 예외가 발생하지 않으므로 `open_dates`가 비었는지 확인하세요.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `kind_code` | `str` | 필수 | 정기권 종류 코드입니다. |
| `period_code` | `str` | 필수 | 이용 기간 코드입니다. |
| `age_code` | `str` | 필수 | 이용 연령 코드입니다. |

**반환값**

[`PassAvailabilityResponse`][korail_mobile_api.PassAvailabilityResponse] — 사용 개시 가능일(`open_dates`), 발권 가능일(`ticket_issue_dates`), 발권처 목록(`offices`), 사용 개시일 행(`pass_info`), 중첩 상태 블록(`main_info`)을 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `kind_code`, `period_code`, `age_code` 중 하나가 비어 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 응답 파싱 |

**예제**

```python
dates = client.get_pass_availability(
    pass_data.commuter_kind_code,
    pass_data.period_options[0].commuter_period_code,
    pass_data.age_options[0].commuter_age_code,
)
print(dates.open_dates)
print(dates.ticket_issue_dates)
```

## `get_pass_schedule`

정기권으로 탈 수 있는 열차 스케줄 한 페이지를 조회합니다.

```python
KorailClient.get_pass_schedule(request: PassScheduleRequest) -> PassScheduleResponse
```

구매나 예약은 하지 않습니다.
조회 조건은 [`PassScheduleRequest`][korail_mobile_api.PassScheduleRequest]로 만듭니다. 열두 필드가 모두 필수이며 문자열입니다.
정기권 코드 세 개(`pass_kind_code`, `pass_period_code`, `pass_age_code`)는 [`get_pass_availability`](#get_pass_availability)와 같이 `pass_data`에서 가져옵니다.
`selected_train_code`에는 열차 그룹 코드를 넣습니다. [`search_trains`](trains.md#search_trains)가 [`TrainSearchQuery`][korail_mobile_api.TrainSearchQuery]의 `train_group_code`(기본값 `"109"`)를 싣는 요청 필드와 같은 필드입니다.
`departure_station_name`과 `arrival_station_name`에는 역 코드가 아니라 역 이름을 넣습니다.
`transfer_type_code`와 `weekend_use_flag`의 뜻과 허용 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
날짜는 `YYYYMMDD`, 시각은 `HHMMSS` 형식으로 넣습니다. 라이브러리는 이 요청 값의 형식을 검사하지 않습니다. 빈 문자열인 필드는 요청에서 빠집니다.
`None`이나 문자열이 아닌 필드는 `PassScheduleRequest`를 만들 때 [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError]로 거절합니다.

서버가 결과 코드 `WRG000000`(조회 결과 없음)으로 실패를 알리면 예외를 발생시키지 않고, 열차가 없는 응답(`str_result`는 `"FAIL"`)을 반환합니다. 이 응답이 정기권 보유 여부를 뜻하는 것은 아닙니다.

한 번에 받을 건수는 `page_size`로 정합니다. `page_no`를 바꿔도 첫 페이지가 올 수 있고, 결과가 페이지 크기보다 많아도 `main_info.next_page_flag`가 `"N"`일 수 있으므로 이 값만으로 다음 페이지 여부를 판단하지 마세요.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`PassScheduleRequest`][korail_mobile_api.PassScheduleRequest] | 필수 | 조회 조건입니다. |

**반환값**

[`PassScheduleResponse`][korail_mobile_api.PassScheduleResponse] — `schedules`의 각 항목([`PassScheduleInfo`][korail_mobile_api.PassScheduleInfo])에 열차가 [`PassScheduleTrain`][korail_mobile_api.PassScheduleTrain] 목록으로 들어 있고, `main_info`에 페이지 정보가 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError] | `PassScheduleRequest`의 필드가 `None`이거나 문자열이 아닐 때(요청을 만들 때 발생) |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 응답 파싱 |

**예제**

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import PassScheduleRequest

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

request = PassScheduleRequest(
    selected_train_code="109",
    departure_date=departure_date,
    departure_time="090000",
    transfer_type_code="1",
    pass_kind_code=pass_data.commuter_kind_code,
    pass_period_code=pass_data.period_options[0].commuter_period_code,
    pass_age_code=pass_data.age_options[0].commuter_age_code,
    page_no="1",
    page_size="10",
    departure_station_name="서울",
    arrival_station_name="부산",
    weekend_use_flag="N",
)
result = client.get_pass_schedule(request)
for schedule in result.schedules:
    for train in schedule.trains:
        print(train.train_no, train.departure_station_name, train.arrival_station_name)
```

## `get_commuter_kind_menu`

정기권 종류 하나의 안내 문구와 조회 파라미터를 받아 옵니다.

```python
KorailClient.get_commuter_kind_menu(commuter_kind_code: str) -> CommuterKindMenuResponse
```

정기권 종류 코드를 넘기면 그 종류의 제목(`title`), 안내(`information`), 동의 안내(`agreement`)와 연령·기간 선택지를 담은 `pass_data`를 돌려줍니다.
종류 코드는 [`get_pass_menu`](#get_pass_menu)의 `pass_data.commuter_kind_code`나 [`get_trip_menu`](#get_trip_menu) 항목의 `commuter_kind_code`에서 가져옵니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `commuter_kind_code` | `str` | 필수 | 정기권 종류 코드입니다. |

**반환값**

[`CommuterKindMenuResponse`][korail_mobile_api.CommuterKindMenuResponse] — 안내 문구와 `pass_data`([`PassMenuData`][korail_mobile_api.PassMenuData])를 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `commuter_kind_code`가 비어 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 응답 파싱 |

**예제**

```python
kind = client.get_commuter_kind_menu(pass_data.commuter_kind_code)
print(kind.title)
print(kind.information)
```

## `get_commuter_info`

정기권 예매에 필요한 조건을 세 단계 중 하나로 조회합니다.

```python
KorailClient.get_commuter_info(request: CommuterInfoRequest) -> CommuterInfoResponse
```

앱의 정기권 예매 화면이 단계별로 보내는 조회입니다. 넘기는 입력 타입에 따라 단계가 정해집니다.
7.0.8에서는 현재 계정의 조회가 `ERR000100`으로 거절됐습니다. 아래 단계별 정상 응답 설명은 성공 시의 모델 계약이며, 이번 계정에서 다시 확인한 결과는 아닙니다.

- **초기 단계**: [`CommuterInitialRequest`][korail_mobile_api.CommuterInitialRequest]에 `pass_data`를 넣습니다. 응답의 `passenger_options`에 승객 종류별 연령 코드와 연령·인원 범위가 옵니다.
- **인원 단계**: [`CommuterPassengerRequest`][korail_mobile_api.CommuterPassengerRequest]는 생성자 대신 `from_response(pass_data, source, passenger_counts)`로 만듭니다. `source`는 초기 단계의 응답이고, `passenger_counts`는 `source.passenger_options`의 행마다 인원을 하나씩 적은 `Sequence[int]`(목록·튜플 등)입니다. 실제 `int`인 비음수만 받으며 입력을 튜플로 복사해 보관합니다. 요청에는 승객 한 명마다 그 행의 연령 코드를 한 번씩 넣습니다.
- **원표 단계**: [`CommuterTicketInquiryRequest`][korail_mobile_api.CommuterTicketInquiryRequest]에 원표의 반환 식별자([`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference])를 넣습니다. 판매일에 `sale_date`(`YYYYMMDD`)와 `return_sale_date`(`MMDD`) 중 어느 값을 넣어야 하는지는 확인하지 못했습니다([승차권 식별자 이어 쓰기](account.md#ticket-identifiers) 참고). `inquiry_type`은 `"0"`(기본값) 또는 `"1"`이며, 두 값의 뜻은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`CommuterInfoRequest`][korail_mobile_api.CommuterInfoRequest] | 필수 | 세 입력 타입 중 하나입니다. |

**반환값**

[`CommuterInfoResponse`][korail_mobile_api.CommuterInfoResponse] — 승객 종류별 선택지(`passenger_options`, [`CommuterPassengerOption`][korail_mobile_api.CommuterPassengerOption] 목록), 예매 가능 인원 범위(`available_passenger_count_from`, `available_passenger_count_to`), 안내·프로모션 문구 등을 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 입력 객체를 만들 때나 요청을 보내기 전에 검사합니다. `pass_data.commuter_kind_code`가 비어 있을 때, `passenger_counts`의 개수가 `source.passenger_options`의 행 수와 다르거나 음수·정수가 아닌 값이 있을 때, 연령 코드가 빈 행이 있을 때, 인원 합계가 0일 때, `inquiry_type`이 `"0"`·`"1"`이 아니거나 `original_ticket`이 `OriginalTicketReference`가 아닐 때, 세 입력 타입이 아닌 값을 넘겼을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 거절 |

**예제**

```python
from korail_mobile_api import CommuterInitialRequest, CommuterPassengerRequest

initial = client.get_commuter_info(CommuterInitialRequest(pass_data=pass_data))
counts = (1,) + (0,) * (len(initial.passenger_options) - 1)
request = CommuterPassengerRequest.from_response(pass_data, initial, counts)
passengers = client.get_commuter_info(request)
print(passengers.available_passenger_count_from, passengers.available_passenger_count_to)
```

## `get_trip_menu`

여행상품 메뉴 화면에 그릴 항목과 그 안의 문구 묶음을 조회합니다.

```python
KorailClient.get_trip_menu() -> TripMenuResponse
```

메뉴 항목마다 제목, 설명, 메뉴 종류(`menu_type`), 링크, 안내 목록(`contents`)이 옵니다.
안내 목록의 일부 행([`TripMenuContent`][korail_mobile_api.TripMenuContent])에는 정기권 종류 코드(`commuter_kind_code`)와 `pass_data`가 들어 있습니다. 이 코드는 [`get_commuter_kind_menu`](#get_commuter_kind_menu)의 입력으로 씁니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`TripMenuResponse`][korail_mobile_api.TripMenuResponse] — `items`에 메뉴 항목이 [`TripMenuItem`][korail_mobile_api.TripMenuItem] 목록으로, `popup_message`에 팝업 문구가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 응답 파싱 |

**예제**

```python
trip_menu = client.get_trip_menu()
for item in trip_menu.items:
    print(item.title, len(item.contents))
    for content in item.contents:
        if content.commuter_kind_code:
            print("  ", content.title, content.commuter_kind_code)
```

<a id="get_discount_card_usage_history"></a>

## `list_discount_card_usages`

N카드 한 장을 이미 사용한 여행 내역을 조회합니다.

```python
KorailClient.list_discount_card_usages(
    card_no: str,
) -> DiscountCardUsageListResponse
```

N카드 번호 하나를 넘기면 그 카드로 이용한 여행이 한 행씩 옵니다. 실서버에서 확인하지 못한 메서드입니다.

각 행에는 승객 이름, 출발·도착역 이름, 운행일과 판매일·일련번호·판매 창구번호(`sale_date`, `sale_sequence`, `sale_window_no`)가 들어 있습니다. 반환 비밀번호가 없으므로 이 값만으로는 반환 식별자로 쓸 수 없습니다.

서버가 `strResult`를 `FAIL`로 보내면 빈 `items`를 반환하지 않고 [공통 예외](index.md#공통-예외)가 발생합니다. 예를 들어 결과 코드 `ERR000100`(조회 자료 없음)이면 [`KorailNoResultsError`][korail_mobile_api.KorailNoResultsError]가 발생합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `card_no` | `str` | 필수 | N카드 번호입니다. |

**반환값**

[`DiscountCardUsageListResponse`][korail_mobile_api.DiscountCardUsageListResponse] — `items`에 사용 내역이 [`DiscountCardUsage`][korail_mobile_api.DiscountCardUsage] 목록으로 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `card_no`가 비어 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 미실행 |

**예제**

```python
card_no = input("N카드 번호: ")
history = client.list_discount_card_usages(card_no)
for usage in history.items:
    print(usage.run_date, usage.departure_station_name, usage.arrival_station_name)
```

## `get_discount_card_schedule`

N카드로 아직 탈 수 있는 열차를 한 구간에 대해 조회합니다.

```python
KorailClient.get_discount_card_schedule(
    request: DiscountCardScheduleRequest,
) -> DiscountCardScheduleResponse
```

조회 조건은 [`DiscountCardScheduleRequest`][korail_mobile_api.DiscountCardScheduleRequest]로 만듭니다. 7.0.8에서 알려진 상품 코드로 요청하자 서버가 `EAZ000028`을 반환했습니다. 보유 N카드가 없어 정상 열차 목록은 확인하지 못했습니다.

필수 필드는 N카드 상품 관리번호(`card_kind_management_no`), 출발·도착역 이름, 출발일(`YYYYMMDD`)입니다.
`for_card()`로 만들면 상품 관리번호에서 카드 종류 코드(`card_kind_code`)를 정합니다. `B2N18120402`·`B2N18120403`만 `"B2N"`, 나머지는 `"MMM"`입니다.
이 구분은 저장소의 이전 정적 근거와 맞지 않습니다. 7.0.6 분석에서 앱의 분기는 `B2N19060502`·`B2N19060503`·`B2N19061002`·`B2N19061003` 네 상품을 따로 다뤘고, 위 두 상품은 그 분기에 없었습니다.
앱의 두 반환값은 보호돼 있어 `"B2N"`·`"MMM"` 자체도 이전 앱 버전의 값입니다. 실서버에서 어느 쪽이 맞는지는 확인하지 못했으므로, 카드 종류 코드를 알면 `card_kind_code`로 직접 넘기세요.
출발 시각(`departure_time`, 기본값 `"000000"`), 열차 그룹 코드(`train_group_code`, 기본값 `"109"`), 직통·환승 구분(`direct_transfer_division_code`, 기본값 `"1"`)은 `for_card()`가 받지 않습니다.
바꾸려면 `dataclasses.replace(request, departure_time="090000")`처럼 만들어진 요청을 복사하세요.
생성자를 직접 쓰면 `card_kind_code`가 상품 관리번호와 관계없이 기본값 `"MMM"`이 되므로, 필요하면 직접 넣으세요.

`usable_trip_count`에는 카드에 남은 사용 가능 횟수를 넣으세요. 빈 문자열(기본값)이면 이 필드를 보내지 않습니다.
7.0.6 시기(2026-09-21) 실서버는 이 필드를 생략한 요청을 `WRR000100`(`usePsbTno` 입력값 오류)으로 거절했으므로 사실상 필요한 값입니다. 라이브러리에는 남은 횟수를 조회하는 메서드가 없습니다.
`usage_period_days`와 `page_no`는 `None`(기본값)이면 보내지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`DiscountCardScheduleRequest`][korail_mobile_api.DiscountCardScheduleRequest] | 필수 | 조회 조건입니다. |

**반환값**

[`DiscountCardScheduleResponse`][korail_mobile_api.DiscountCardScheduleResponse] — `trains`에 열차가 [`DiscountCardScheduleTrain`][korail_mobile_api.DiscountCardScheduleTrain] 목록으로 들어 있습니다. 이 응답에는 다음 페이지 신호가 없습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `departure_date`가 숫자 8자리가 아니거나 `departure_time`이 숫자 6자리가 아닐 때, 역 이름·`card_kind_management_no`·`card_kind_code`·`train_group_code`·`direct_transfer_division_code` 중 하나가 비어 있을 때, `usable_trip_count`가 문자열이 아닐 때, `usage_period_days`나 `page_no`를 빈 문자열로 넣었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 거절 |

**예제**

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import DiscountCardScheduleRequest

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

request = DiscountCardScheduleRequest.for_card(
    input("N카드 상품 관리번호: "),
    departure_station_name="서울",
    arrival_station_name="부산",
    departure_date=departure_date,
    usable_trip_count=input("남은 사용 횟수: "),
)
result = client.get_discount_card_schedule(request)
for train in result.trains:
    print(train.train_no, train.run_date, train.departure_station_name, train.arrival_station_name)
```

## `register_discount_card`

3.0에서 제거했습니다. 실서버에서 확인하지 못했고 라이브러리로 결제·취소할 수 없는 구매만 만들었기 때문입니다. `DiscountCardPurchaseRequest`, `DiscountCardSectionRequest`, `DiscountCardAdditionalUser`, `DiscountCardPurchaseResponse`도 함께 제거했습니다. 대신 쓸 메서드는 없으며 [3.0으로 옮기기](../migration-3.0.md#removed)를 참고하세요.

## `extend_discount_card`

N카드의 유효기간을 실제로 연장합니다.

```python
KorailClient.extend_discount_card(ticket: OriginalTicketReference) -> BaseKorailResponse
```

연장할 N카드 승차권(원표)의 반환 식별자 네 값(판매 창구번호, 판매일, 일련번호, 반환 비밀번호)을 [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference]에 넣어 보냅니다. 3.0 전에는 같은 네 값을 `DiscountCardTicket`에 넣었고 요청 바이트는 같습니다. 판매일에 `YYYYMMDD`와 `MMDD` 중 어느 형식을 넣어야 하는지는 확인하지 못했습니다. 두 판매일 필드의 차이는 [승차권 식별자 이어 쓰기](account.md#ticket-identifiers)를 참고하세요. 실서버에서 확인하지 못한 메서드입니다.

승차권 상세([`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail))의 `discount_card`([`DiscountCardOnTicket`][korail_mobile_api.DiscountCardOnTicket])에는 기간 연장 가능 여부 플래그(`term_extension_possible_flag`)가 있습니다. 어떤 값이 연장 가능을 뜻하는지는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference] | 필수 | 연장할 N카드 승차권의 반환 식별자입니다. |

**반환값**

[`BaseKorailResponse`][korail_mobile_api.BaseKorailResponse] — 결과 봉투(`str_result`, `h_msg_cd`, `h_msg_txt`)와 원문만 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `ticket`이 `OriginalTicketReference`가 아닐 때. 네 값 중 하나가 비어 있으면 `OriginalTicketReference`를 만들 때 거절합니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 N카드의 유효기간이 실제로 연장됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import OriginalTicketReference

tickets = client.list_tickets()
card_ticket = tickets.reservations[0].tickets[0]  # 기간을 연장할 N카드 승차권
result = client.extend_discount_card(
    OriginalTicketReference(
        sale_window_no=card_ticket.sale_window_no,
        sale_date=card_ticket.sale_date,  # YYYYMMDD. MMDD(return_sale_date)가 맞는지는 확인하지 못했습니다
        sale_sequence=card_ticket.sale_sequence,
        return_password=card_ticket.return_password,
    )
)
print(result.str_result, result.h_msg_cd)
```

## `reserve_with_discount_card`

N카드로 좌석을 홀드합니다.

```python
KorailClient.reserve_with_discount_card(
    train: TrainSummary,
    *,
    card_no: str,
) -> ReservationHoldResponse
```

[`reserve`](reservations.md#reserve)와 같은 예약 경로에 N카드 번호를 붙여 보냅니다. 승객 한 명, 일반실로 홀드합니다. 실서버에서 확인하지 못한 메서드입니다.

`train`은 열차 조회 결과의 [`TrainSummary`][korail_mobile_api.TrainSummary]를 그대로 넘깁니다. 라이브러리는 일반실 예약 코드(`general_reservation_code`)가 `"11"`인 열차만 받습니다.
요청에는 N카드 할인 코드로 `"153"`, 메뉴 ID로 `"A2"`를 넣습니다.
할인 코드 `"153"`은 7.0.8의 `ReqDiscount.N_CARD` 복호화로 확인한 값이며,
발권 응답의 `ResDiscount.N_CARD` 값 `"443"`과 구분합니다.
메뉴 ID `"A2"`는 확인한 값이 아닙니다. 좌석배정 메뉴의 값을 재사용한 것이며, 앱은 좌석배정(`SEAT_ASSIGN`)과 N카드(`N_CARD`) 메뉴 ID를 따로 선언하고 두 값은 보호돼 있습니다.
이 예약 흐름의 실서버 성공은 미확인입니다.
반환값은 [`reserve`](reservations.md#reserve)와 같은 홀드 모델입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `train` | [`TrainSummary`][korail_mobile_api.TrainSummary] | 필수 | 예약할 열차입니다. |
| `card_no` | `str` | 필수 | 사용할 N카드 번호입니다. 키워드 인자로만 넘깁니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.ReservationHoldResponse] — 홀드의 PNR(`pnr_no`), 결제 기한, 금액 등을 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `train`이 `TrainSummary`가 아닐 때, `general_reservation_code`가 `"11"`이 아닐 때, `card_no`가 비어 있을 때, 열차 번호·운행일·역 코드 같은 필수 값이 없거나 형식이 맞지 않을 때. 응답을 읽지 못했을 때도 발생하며, 이때 홀드는 이미 만들어졌을 수 있습니다. |
| [`KorailSoldOutError`][korail_mobile_api.KorailSoldOutError] | 서버가 매진으로 응답했을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.KorailSeatUnavailableError] | 서버가 좌석을 이용할 수 없다고 응답했을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.KorailReservationRefusedError] | 서버가 중복 예약, 구매 한도, 예약 가능 시간, 지원하지 않는 할인(`ERR299943`) 등의 이유로 예약을 거절했을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | `reserve` | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 N카드로 좌석이 실제로 홀드됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

query = TrainSearchQuery(
    departure_station="서울",
    arrival_station="부산",
    departure_date=departure_date,
    departure_time="090000",
)
result = client.search_trains(query)
train = next(t for t in result.trains if t.general_reservation_code == "11")
hold = client.reserve_with_discount_card(train, card_no=input("N카드 번호: "))
print(hold.pnr_no, hold.payment_deadline_date, hold.payment_deadline_time)
```

<a id="get_product_reservations"></a>

## `list_product_reservations`

로그인 계정이 예약한 여행상품 목록 한 페이지를 조회합니다.

```python
KorailClient.list_product_reservations(
    page_no: int = 1,
    page_size: int = 20,
    *,
    reservation_status_code: str | None = None,
    payment_status_code: str | None = None,
) -> ProductReservationListResponse
```

각 행([`ProductReservation`][korail_mobile_api.ProductReservation])의 예약번호(`virtual_reservation_no`)와 예약 순번(`reservation_sequence`)은 [`get_product_detail`](#get_product_detail)의 입력입니다.

`reservation_status_code`와 `payment_status_code`는 조회 조건으로 함께 보냅니다. `None`(기본값)이면 보내지 않습니다. 앱이 이 두 필드에 보내는 기본값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.
서버 응답에 목록 블록이 없으면 빈 `items`를 반환합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page_no` | `int` | `1` | 조회할 페이지 번호입니다. |
| `page_size` | `int` | `20` | 한 페이지의 건수입니다. |
| `reservation_status_code` | `str` \| `None` | `None` | 요청에 함께 보낼 예약 상태 코드입니다. |
| `payment_status_code` | `str` \| `None` | `None` | 요청에 함께 보낼 결제 상태 코드입니다. |

**반환값**

[`ProductReservationListResponse`][korail_mobile_api.ProductReservationListResponse] — `items`에 예약이 [`ProductReservation`][korail_mobile_api.ProductReservation] 목록으로, `total_count`에 전체 건수가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `page_no`나 `page_size`가 정수가 아닐 때, 상태 코드를 빈 문자열로 넣었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 응답 파싱 |

**예제**

```python
page = client.list_product_reservations()
print(page.total_count, "건")
for reservation in page.items:
    print(
        reservation.product_name, reservation.reservation_status_name, reservation.settlement_deadline
    )
```

## `get_product_detail`

여행상품 예약 한 건의 상세와 취소 조건을 조회합니다.

```python
KorailClient.get_product_detail(
    reservation_no: str,
    reservation_sequence: str | None = None,
) -> ProductDetailResponse
```

[`list_product_reservations`](#list_product_reservations)가 돌려준 행의 `virtual_reservation_no`와 `reservation_sequence`를 넘깁니다. `reservation_sequence`가 `None`이면 보내지 않습니다.

응답에는 금액과 취소 조건(취소 기한, 취소 시 돌려받는 금액, 취소 수수료), 포함된 구성 항목 이름이 들어 있습니다.
이 응답을 그대로 [`cancel_product_reservation`](#cancel_product_reservation)에 넘겨 취소합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `reservation_no` | `str` | 필수 | 여행상품 예약번호입니다. |
| `reservation_sequence` | `str` \| `None` | `None` | 예약 순번입니다. |

**반환값**

[`ProductDetailResponse`][korail_mobile_api.ProductDetailResponse] — 상품 이름, 예약 상태, 취소 기한(`cancellation_deadline`), 취소 반환 금액(`cancellation_return_amount`), 취소 수수료(`cancellation_fee`), 받은 금액(`received_amount`), 총 결제 금액(`total_settlement_amount`), 구성 항목 이름(`included_item_names`), 취소에 쓰는 `virtual_reservation_no`와 `goods_sequence`를 담습니다. 서버 응답에 상세 블록이 없으면 이 필드들은 `None`이거나 비어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `reservation_no`가 비어 있을 때, `reservation_sequence`를 빈 문자열로 넣었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 응답 파싱 |

**예제**

```python
reservation = client.list_product_reservations().items[0]
detail = client.get_product_detail(
    reservation.virtual_reservation_no,
    reservation.reservation_sequence,
)
print(detail.product_name, detail.included_item_names)
print("취소 수수료:", detail.cancellation_fee, "반환 금액:", detail.cancellation_return_amount)
```

## `cancel_product_reservation`

여행상품 예약을 취소합니다.

```python
KorailClient.cancel_product_reservation(
    detail: ProductDetailResponse,
) -> ProductCancelResponse
```

[`get_product_detail`](#get_product_detail)이 돌려준 응답을 넘기면, 그 안의 `virtual_reservation_no`와 `goods_sequence`로 취소를 요청합니다.

같은 요청이 결제 전 예약의 취소와 결제한 예약의 환불에 모두 쓰입니다. 결제한 예약은 수수료가 붙을 수 있으므로 호출하기 전에 상세의 `cancellation_fee`와 `cancellation_return_amount`를 확인하세요.
7.0.8에서는 조회 가능한 여행상품 1건이 이미 고객 취소 상태라 취소 요청을 실행하지 않았습니다. 7.0.6 시기에는 결제 전 예약 취소를 확인했으며, 결제한 예약의 환불은 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail` | [`ProductDetailResponse`][korail_mobile_api.ProductDetailResponse] | 필수 | 취소할 예약의 상세 응답입니다. |

**반환값**

[`ProductCancelResponse`][korail_mobile_api.ProductCancelResponse] — 결과 봉투와 `integrated_message_code`를 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `detail`이 `ProductDetailResponse`가 아니거나 `virtual_reservation_no`·`goods_sequence`가 비어 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 여행상품 예약이 실제로 취소되고, 결제한 예약이면 환불로 처리됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
detail = client.get_product_detail(
    reservation.virtual_reservation_no,
    reservation.reservation_sequence,
)
print("취소 수수료:", detail.cancellation_fee, "반환 금액:", detail.cancellation_return_amount)
result = client.cancel_product_reservation(detail)
print(result.str_result, result.h_msg_cd)
```
