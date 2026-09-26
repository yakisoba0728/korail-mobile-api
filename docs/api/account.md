# 승차권·계정

이 페이지의 메서드는 로그인한 계정의 승차권 목록과 영수증, 포인트·마일리지·쿠폰, 여정 변경에 필요한 정보, 지연확인증을 조회합니다.
모두 서버 상태를 바꾸지 않는 조회 메서드이며, 호출하기 전에 [`login`](session.md#login)이 필요합니다.
승차권 한 장을 대상으로 하는 메서드는 [`get_ticket_list`](#get_ticket_list)가 돌려준 반환 식별자를 이어 받습니다.
여정 변경과 자율 좌석 변경은 필요한 정보를 조회하는 메서드만 있고, 변경 요청을 보내는 메서드는 없습니다.

**승차권 식별자 이어 쓰기**{#ticket-identifiers}

[`get_ticket_list`](#get_ticket_list)가 돌려주는 승차권([`TicketListTicket`][korail_mobile_api.read_models.TicketListTicket])에는 반환 식별자가 들어 있습니다.
판매 창구번호(`sale_window_no`), 일련번호(`sale_sequence`), 반환 비밀번호(`return_password`)는 그대로 옮깁니다.
판매일은 두 필드가 있고, 메서드마다 받는 형식이 다릅니다.

| `TicketListTicket` 필드 | 형식 | 이 값을 판매일로 받는 메서드 |
|---|---|---|
| `return_sale_date` | `MMDD` (4자리) | [`get_ticket_receipt`](#get_ticket_receipt), [`get_original_ticket_inquiry`](#get_original_ticket_inquiry), [`get_delay_certificate`](#get_delay_certificate), [`get_delay_return_receipt`](#get_delay_return_receipt), [`get_refund_commission`](payments.md#get_refund_commission), [`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail) |
| `sale_date` | `YYYYMMDD` (8자리) | [`get_delivery_recipient`](delivery-checkin.md#get_delivery_recipient), [`get_pbp_acceptance_specifications`](delivery-checkin.md#get_pbp_acceptance_specifications) |

[`get_ticket_receipt`](#get_ticket_receipt)는 네 값을 키워드 인자로 따로 받고, 나머지 메서드는 [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]에 담아 받습니다.
[`get_commuter_info`](passes.md#get_commuter_info)는 [`CommuterTicketInquiryRequest`][korail_mobile_api.read_payloads.CommuterTicketInquiryRequest]의 `original_ticket`에 담아 받습니다. 이 단계에 `sale_date`와 `return_sale_date` 중 어느 값을 넣어야 하는지는 확인하지 못했습니다. 라이브러리는 넣은 값을 그대로 보냅니다.
`OriginalTicketReference`는 네 값이 비어 있지 않은지만 검사하고 판매일의 자릿수는 검사하지 않습니다.
[`get_ticket_receipt`](#get_ticket_receipt)를 뺀 메서드는 판매일 필드를 잘못 골라도 요청 전에 거절하지 않고 그대로 보내므로, 위 표에 맞는 필드를 넣으세요.
`TicketListTicket`의 필드는 응답에 없으면 `None`이며, `None`이나 빈 문자열을 넣으면 `OriginalTicketReference`를 만들 때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

```python
from korail_mobile_api import OriginalTicketReference

tickets = client.get_ticket_list()
ticket = tickets.reservations[0].tickets[0]
reference = OriginalTicketReference(
    sale_window_no=ticket.sale_window_no,
    sale_date=ticket.return_sale_date,  # MMDD를 받는 메서드용
    sale_sequence=ticket.sale_sequence,
    return_password=ticket.return_password,
)
```

## `get_ticket_list`

로그인 계정의 승차권 목록 한 페이지를 예약별로 묶어 조회합니다.

```python
KorailClient.get_ticket_list(
    page_no: int = 1,
    *,
    mode: Literal['1', '2'] = '1',
    boarding_date_from: str = '',
    boarding_date_to: str = '',
) -> TicketListResponse
```

결과는 예약([`TicketListReservation`][korail_mobile_api.read_models.TicketListReservation]) 목록입니다.
예약마다 승차권([`TicketListTicket`][korail_mobile_api.read_models.TicketListTicket]) 목록이, 승차권마다 열차 구간([`TicketListTrain`][korail_mobile_api.read_models.TicketListTrain]) 목록이 들어 있습니다.
승차권에는 영수증·원표·지연확인증 조회에 쓰는 반환 식별자가 함께 들어 있습니다. 넘기는 방법은 [승차권 식별자 이어 쓰기](#ticket-identifiers)를 참고하세요.

`mode`가 `"1"`이면 현재 승차권을, `"2"`이면 구매 이력을 돌려줍니다. 앱 내부 값이 공개돼 있지 않아 이 대응은 실서버 응답을 보고 정했습니다.
라이브러리는 `mode`, 날짜, 페이지 번호를 고치지 않고 그대로 보내며, 빈 문자열인 날짜는 보내지 않습니다.
[`KorailConfig`][korail_mobile_api.config.KorailConfig]의 `advertising_id`를 설정했으면 그 값도 함께 보냅니다.

예약 행에서 `tickets`를 뺀 나머지 필드는 응답에 없을 수 있으며, 없으면 `None`입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page_no` | `int` | `1` | 페이지 번호입니다. |
| `mode` | `Literal['1', '2']` | `'1'` | 목록 종류입니다. `"1"`은 현재 승차권, `"2"`는 구매 이력입니다. 라이브러리는 다른 값도 막지 않고 그대로 보냅니다. |
| `boarding_date_from` | `str` | `''` | 조회할 승차일 범위의 시작일(`YYYYMMDD`)입니다. 빈 문자열이면 보내지 않습니다. |
| `boarding_date_to` | `str` | `''` | 조회할 승차일 범위의 종료일(`YYYYMMDD`)입니다. 빈 문자열이면 보내지 않습니다. |

**반환값**

[`TicketListResponse`][korail_mobile_api.read_models.TicketListResponse] — `reservations`에 예약 목록이, `total_count`에 서버가 알려 준 전체 건수가 들어 있습니다. 승차권이 없으면 `reservations`는 빈 튜플입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `page_no`가 `int`가 아닐 때(`bool` 포함), `mode`가 문자열이 아니거나 빈 문자열일 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
tickets = client.get_ticket_list()
for reservation in tickets.reservations:
    for ticket in reservation.tickets:
        for train in ticket.trains:
            print(ticket.pnr_no, train.train_no, train.departure_date, train.departure_time)

history = client.get_ticket_list(2, mode="2")
print(history.total_count)
```

## `get_ticket_receipt`

승차권 한 장의 영수증과 결제수단을 조회합니다.

```python
KorailClient.get_ticket_receipt(
    *,
    sale_date: str,
    window_no: str,
    sale_sequence: str,
    return_password: str,
    txt_index: str | None = None,
) -> TicketReceiptResponse
```

네 식별값은 [`get_ticket_list`](#get_ticket_list)가 돌려준 승차권에서 가져옵니다.
`sale_date`에는 4자리 `return_sale_date`(`MMDD`)를 넣습니다. 8자리인 `sale_date`(`YYYYMMDD`)를 넣으면 요청을 보내기 전에 거절합니다.

식별값은 키워드 인자로만 받습니다. [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]와 인자 순서가 달라, 위치 인자로 넘기면 창구번호와 판매일이 뒤바뀔 수 있기 때문입니다.

금액과 인원 수는 정수(`int`)로 담습니다. 응답 모델은 카드번호·승인번호 같은 값을 가리지 않고 서버가 보낸 그대로 담으므로 로그에 남기지 마세요.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `sale_date` | `str` | 필수 | 판매일(`MMDD`, ASCII 숫자 4자리)입니다. 승차권의 `return_sale_date`를 넣습니다. |
| `window_no` | `str` | 필수 | 판매 창구번호입니다. 승차권의 `sale_window_no`를 넣습니다. |
| `sale_sequence` | `str` | 필수 | 일련번호입니다. 승차권의 `sale_sequence`를 넣습니다. |
| `return_password` | `str` | 필수 | 반환 비밀번호입니다. 승차권의 `return_password`를 넣습니다. |
| `txt_index` | `str \| None` | `None` | 요청의 `txtIndex`로 보내는 값입니다. `None`이거나 공백뿐인 문자열이면 보내지 않습니다. |

**반환값**

[`TicketReceiptResponse`][korail_mobile_api.read_models.TicketReceiptResponse] — `items`에 영수증([`TicketReceipt`][korail_mobile_api.read_models.TicketReceipt]) 목록이 들어 있습니다. 영수증마다 결제수단([`ReceiptPayment`][korail_mobile_api.read_models.ReceiptPayment])과 현금영수증([`ReceiptCashPayment`][korail_mobile_api.read_models.ReceiptCashPayment]) 목록이 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `sale_date`가 ASCII 숫자 4자리가 아닐 때, `window_no`·`sale_sequence`·`return_password`가 비었을 때, `txt_index`가 문자열도 `None`도 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
ticket = client.get_ticket_list(mode="2").reservations[0].tickets[0]
receipt = client.get_ticket_receipt(
    sale_date=ticket.return_sale_date,
    window_no=ticket.sale_window_no,
    sale_sequence=ticket.sale_sequence,
    return_password=ticket.return_password,
)
for item in receipt.items:
    print(item.train_no, item.travel_date, item.received_amount)
    for payment in item.payments:
        print(payment.payment_method, payment.amount)
```

## `get_korail_point_summary`

계정의 포인트, 쿠폰·지연할인권 개수, 복지 할인 자격 같은 요약 정보를 조회합니다.

```python
KorailClient.get_korail_point_summary() -> KorailPointSummaryResponse
```

응답의 모든 필드는 문자열이며, 응답에 없으면 `None`입니다.
`discount_coupon_count`는 서버가 알려 준 개수이며 [`get_discount_coupons`](#get_discount_coupons) 결과의 개수와 항상 같다고 보장하지 않습니다.
소셜 로그인 연동 플래그 네 개(`naver_linked_flag`, `kakao_linked_flag`, `google_linked_flag`, `apple_linked_flag`)는 필드와 서비스의 대응을 확인하지 못했습니다. 필드 이름을 확정된 대응으로 믿지 마세요.

**매개변수**

매개변수가 없습니다.

**반환값**

[`KorailPointSummaryResponse`][korail_mobile_api.read_models.KorailPointSummaryResponse] — 포인트(`korail_point`), 할인쿠폰 개수(`discount_coupon_count`), 지연할인권 개수(`delay_discount_count`), 복지 할인 등급, 장애 여부와 유형, 휴대전화·이메일 인증 여부 등이 들어 있습니다.

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
summary = client.get_korail_point_summary()
print(summary.korail_point, summary.discount_coupon_count, summary.delay_discount_count)
```

## `get_mileage_history`

기간 안의 마일리지 적립·사용 내역 한 페이지를 조회합니다.

```python
KorailClient.get_mileage_history(
    request: MileageHistoryRequest,
) -> MileageHistoryResponse
```

조회 조건은 [`MileageHistoryRequest`][korail_mobile_api.read_payloads.MileageHistoryRequest]로 만듭니다.
조건 값은 이 메서드를 호출할 때 검사하며, 검사에 실패하면 요청을 보내지 않습니다.
한 페이지는 20행으로 요청합니다. 앱이 쓰는 페이지 크기는 공개돼 있지 않아 확인하지 못했습니다.

| 필드 | 기본값 | 설명 |
|---|---|---|
| `start_date`, `end_date` | 필수 | 조회 기간의 시작일과 종료일(`YYYYMMDD`)입니다. ASCII 숫자 8자리여야 하고, 시작일이 종료일보다 늦으면 안 됩니다. |
| `ledger` | `"1"` | 조회할 원장입니다. `"1"`은 KTX 마일리지, `"2"`는 레일포인트입니다. 두 값은 실서버에서 동작을 확인했으며, 앱이 쓰는 값은 공개돼 있지 않아 확인하지 못했습니다. |
| `movement` | `"0"` | 증감 구분입니다. `"0"`은 전체, `"1"`은 적립, `"2"`는 사용입니다. |
| `page_no` | `1` | 페이지 번호(`int`)입니다. |

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`MileageHistoryRequest`][korail_mobile_api.read_payloads.MileageHistoryRequest] | 필수 | 조회 기간, 원장, 증감 구분, 페이지 번호입니다. |

**반환값**

[`MileageHistoryResponse`][korail_mobile_api.read_models.MileageHistoryResponse] — `entries`에 내역([`MileageHistoryEntry`][korail_mobile_api.read_models.MileageHistoryEntry]) 목록이, `page_count`에 전체 페이지 수가 들어 있습니다. 사용 가능 포인트, 누적 적립·사용 포인트 같은 합계는 응답의 필드를 합치지 않고 각각 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `ledger`나 `movement`가 허용된 값이 아닐 때, `start_date`·`end_date`가 ASCII 숫자 8자리가 아닐 때, `start_date`가 `end_date`보다 늦을 때, `page_no`가 `int`가 아닐 때(`bool` 포함) |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import MileageHistoryRequest

history = client.get_mileage_history(
    MileageHistoryRequest(start_date="20260101", end_date="20260930")
)
for entry in history.entries:
    print(entry.departure_date, entry.accrual_division_name, entry.point_amount)

earned = client.get_mileage_history(
    MileageHistoryRequest(start_date="20260101", end_date="20260930", movement="1", page_no=2)
)
```

## `get_discount_coupons`

계정이 가진 할인쿠폰 목록 한 페이지를 조회합니다.

```python
KorailClient.get_discount_coupons(
    page_no: int = 1,
    pnr_no: str = '',
) -> DiscountCouponListResponse
```

보유한 쿠폰이 없으면 서버는 결과 코드 `WRG000000`의 실패로 응답합니다.
이때는 예외를 발생시키지 않고, `str_result`가 `"FAIL"`이고 `items`가 빈 응답을 반환합니다. 다른 실패 코드는 다른 메서드처럼 예외로 처리합니다.

할인값은 평일·주말과 운임·요금에 따라 네 필드(`weekday_fare_discount`, `weekday_price_discount`, `weekend_fare_discount`, `weekend_price_discount`)에 나눠 담습니다.
`discount_rate_amount_division_code`는 코드 값의 뜻을 확인하지 못했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page_no` | `int` | `1` | 페이지 번호입니다. |
| `pnr_no` | `str` | `''` | 요청의 `pnrNo`로 보내는 PNR입니다. 빈 문자열이면 보내지 않습니다. |

**반환값**

[`DiscountCouponListResponse`][korail_mobile_api.read_models.DiscountCouponListResponse] — `items`에 쿠폰([`DiscountCoupon`][korail_mobile_api.read_models.DiscountCoupon]) 목록이 들어 있습니다. `current_page`와 `total_pages`는 정수, `total_count`와 `row_count`는 문자열이며 응답에 없으면 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `page_no`가 `int`가 아니거나(`bool` 포함) `pnr_no`가 문자열이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
coupons = client.get_discount_coupons()
if not coupons.items:
    print(coupons.h_msg_cd, coupons.h_msg_txt)
for coupon in coupons.items:
    print(coupon.coupon_no, coupon.start_date, coupon.expiration_date)
```

## `get_delay_discount_tickets`

계정이 가진 지연할인권 목록을 조회합니다.

```python
KorailClient.get_delay_discount_tickets(
    departure_date_to: str,
) -> DelayDiscountTicketListResponse
```

`departure_date_to`는 앱과 같은 방식으로 `h_page_no`라는 이름으로 보내며, POST 본문이 아니라 URL 쿼리에 싣습니다.
라이브러리는 ASCII 숫자 8자리인지만 검사하고, 달력에 있는 날짜인지는 검사하지 않습니다.

페이지 정보(`current_page`, `total_pages`, `total_count`, `row_count`, `last_page_flag`)는 응답의 `main_info` 블록에서 읽으며, 블록이 없으면 모두 `None`입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `departure_date_to` | `str` | 필수 | 기준 출발일(`YYYYMMDD`)입니다. |

**반환값**

[`DelayDiscountTicketListResponse`][korail_mobile_api.read_models.DelayDiscountTicketListResponse] — `items`에 지연할인권([`DelayDiscountTicket`][korail_mobile_api.read_models.DelayDiscountTicket]) 목록과 페이지 정보가 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `departure_date_to`가 ASCII 숫자 8자리가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
tickets = client.get_delay_discount_tickets("20261231")
for item in tickets.items:
    print(item.train_no, item.departure_date, item.ticket_status_name)
```

## `get_deposit_banks`

입금 가능한 은행의 코드와 이름 목록을 조회합니다.

```python
KorailClient.get_deposit_banks() -> DepositBankListResponse
```

요청에는 앱과 같이 `Device`, `Version`, `Key` 세 필드만 싣습니다.
[`KorailConfig`][korail_mobile_api.config.KorailConfig]의 `lang`을 설정해도 `lang`은 보내지 않으며, 세 필드는 값이 빈 문자열이어도 빼지 않고 보냅니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`DepositBankListResponse`][korail_mobile_api.read_models.DepositBankListResponse] — `items`에 은행([`DepositBank`][korail_mobile_api.read_models.DepositBank]) 목록이 들어 있습니다. 은행마다 코드(`code`)와 이름(`display_name`)이 있습니다.

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
banks = client.get_deposit_banks()
for bank in banks.items:
    print(bank.code, bank.display_name)
```

## `get_customer_trip_info`

로그인 계정에 저장된 여행 편의설정을 조회합니다.

```python
KorailClient.get_customer_trip_info() -> CustomerTripInfoResponse
```

편의설정에는 출발역·도착역, 승객 종류별 인원, 열차 종류, 객실 등급, 좌석 속성 같은 값이 들어 있습니다.
요청에는 로그인 세션([`KorailSession`][korail_mobile_api.models.KorailSession])의 고객번호(`customer_no`)를 싣습니다.
매체 구분과 등록 순번은 라이브러리가 고정값을 보냅니다. 앱이 쓰는 값은 공개돼 있지 않아 확인하지 못했습니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`CustomerTripInfoResponse`][korail_mobile_api.read_models.CustomerTripInfoResponse] — `trips`에 편의설정([`CustomerTripInfo`][korail_mobile_api.read_models.CustomerTripInfo]) 목록이 들어 있습니다. 각 필드는 문자열이며 응답에 없으면 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았거나 세션에 고객번호(`customer_no`)가 없을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
info = client.get_customer_trip_info()
for trip in info.trips:
    print(trip.departure_station_name, trip.arrival_station_name, trip.adult_count)
```

## `get_multi_child_discount_targets`

다자녀 할인 대상으로 등록된 가족 구성원을 조회합니다.

```python
KorailClient.get_multi_child_discount_targets(
    departure_date: str,
) -> MultiChildDiscountTargetResponse
```

`departure_date`는 달력에 있는 날짜여야 하며, 요청을 보내기 전에 검사합니다. 실서버에서는 오류 응답까지만 확인했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `departure_date` | `str` | 필수 | 출발일(`YYYYMMDD`)입니다. |

**반환값**

[`MultiChildDiscountTargetResponse`][korail_mobile_api.read_models.MultiChildDiscountTargetResponse] — `targets`에 가족 구성원([`MultiChildDiscountTarget`][korail_mobile_api.read_models.MultiChildDiscountTarget]) 목록이 들어 있습니다. 구성원마다 이름, 생년월일, 승객 유형, 할인 종류 코드 등이 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `departure_date`가 ASCII 숫자 8자리가 아니거나 달력에 없는 날짜일 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 응답만 확인 |

**예제**

```python
result = client.get_multi_child_discount_targets("20261002")
for target in result.targets:
    print(target.customer_family_name, target.passenger_type_name)
```

## `get_trip_change_dates`

여정 변경으로 옮겨 갈 수 있는 날짜 목록을 조회합니다.

```python
KorailClient.get_trip_change_dates(departure_date: str) -> TripChangeDateResponse
```

`departure_date`는 달력에 있는 날짜여야 하며, 요청을 보내기 전에 검사합니다.
달력에 없는 날짜를 보내면 서버가 날짜 목록 없이 성공으로 응답하기 때문에, 라이브러리가 먼저 거절합니다.
변경할 수 있는 날짜가 없으면 `trip_change_dates`는 빈 튜플입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `departure_date` | `str` | 필수 | 출발일(`YYYYMMDD`)입니다. |

**반환값**

[`TripChangeDateResponse`][korail_mobile_api.read_models.TripChangeDateResponse] — `trip_change_dates`에 변경 가능한 날짜 문자열이, `last_run_date`에 서버가 알려 준 마지막 운행일이 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `departure_date`가 ASCII 숫자 8자리가 아니거나 달력에 없는 날짜일 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
dates = client.get_trip_change_dates("20261002")
for date in dates.trip_change_dates:
    print(date)
print(dates.last_run_date)
```

## `get_original_ticket_inquiry`

여정 변경의 기준이 되는 원표를 조회합니다.

```python
KorailClient.get_original_ticket_inquiry(
    tickets: Sequence[OriginalTicketReference],
    *,
    ticket_count: int | None = None,
) -> OriginalTicketInquiryResponse
```

여러 장을 한 번에 조회할 수 있으며, 승차권마다 반환 식별자 네 값에 1부터 번호를 붙여 보냅니다.
각 [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]의 `sale_date`에는 승차권의 `return_sale_date`(`MMDD`)를 넣습니다. 자세한 내용은 [승차권 식별자 이어 쓰기](#ticket-identifiers)를 참고하세요.

`ticket_count`를 생략하면 `tickets`의 길이를 승차권 수로 보냅니다.
앱은 호출하는 곳에 따라 이 값을 다르게 보내므로, 라이브러리는 `ticket_count`가 `tickets`의 길이와 같은지 검사하지 않습니다.

응답의 [`OriginalTicket`][korail_mobile_api.read_models.OriginalTicket]에서 `original_`로 시작하는 필드는 요청한 승차권의 반환 식별자가 되돌아온 값입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `tickets` | `Sequence[`[`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]`]` | 필수 | 조회할 승차권의 반환 식별자 목록입니다. 한 장 이상이어야 합니다. |
| `ticket_count` | `int \| None` | `None` | 요청에 싣는 승차권 수입니다. `None`이면 `tickets`의 길이를 씁니다. |

**반환값**

[`OriginalTicketInquiryResponse`][korail_mobile_api.read_models.OriginalTicketInquiryResponse] — `tickets`에 원표([`OriginalTicket`][korail_mobile_api.read_models.OriginalTicket]) 목록이 들어 있습니다. 원표마다 여정([`OriginalTicketJourney`][korail_mobile_api.read_models.OriginalTicketJourney])이, 여정마다 좌석([`OriginalTicketSeat`][korail_mobile_api.read_models.OriginalTicketSeat])이 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `tickets`가 시퀀스가 아니거나(문자열 포함) 비었을 때, 항목이 `OriginalTicketReference`가 아닐 때, `ticket_count`가 `int`가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import OriginalTicketReference

reservation = client.get_ticket_list().reservations[0]
references = [  # 판매일은 return_sale_date(MMDD)
    OriginalTicketReference(t.sale_window_no, t.return_sale_date, t.sale_sequence, t.return_password)
    for t in reservation.tickets
]
result = client.get_original_ticket_inquiry(references)
for original in result.tickets:
    print(original.pnr_no, [journey.train_no for journey in original.journeys])
```

## `get_self_seat_change_info`

자율 좌석·열차 변경으로 옮겨 갈 수 있는 승차역과 변경 사유를 조회합니다.

```python
KorailClient.get_self_seat_change_info(
    request: SelfSeatChangeInfoRequest,
) -> SelfSeatChangeInfoResponse
```

요청에는 승차권 식별자가 들어가지 않고 열차 정보만 들어갑니다. 값은 [`get_ticket_list`](#get_ticket_list)의 열차 구간([`TicketListTrain`][korail_mobile_api.read_models.TicketListTrain])에서 가져올 수 있습니다.
조회 조건은 [`SelfSeatChangeInfoRequest`][korail_mobile_api.read_payloads.SelfSeatChangeInfoRequest]로 만들며, 값은 객체를 만들 때 검사해 잘못되면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

| 필드 | 기본값 | 설명 |
|---|---|---|
| `run_date` | 필수 | 운행일(`YYYYMMDD`, ASCII 숫자 8자리)입니다. |
| `train_no` | 필수 | 열차 번호(ASCII 숫자 5자리 이하)입니다. |
| `departure_station_code`, `arrival_station_code` | 필수 | 출발역과 도착역 코드입니다. 비어 있으면 안 됩니다. |
| `room_class_code` | `None` | 객실 등급입니다. `"1"`은 일반실, `"2"`는 특실이며 `None`이면 보내지 않습니다. 이 대응은 실서버 응답을 보고 정했습니다. |

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`SelfSeatChangeInfoRequest`][korail_mobile_api.read_payloads.SelfSeatChangeInfoRequest] | 필수 | 조회할 열차의 운행일, 열차 번호, 구간, 객실 등급입니다. |

**반환값**

[`SelfSeatChangeInfoResponse`][korail_mobile_api.read_models.SelfSeatChangeInfoResponse] — 열차 정보와 함께 `stations`에 변경할 수 있는 승차역([`SelfSeatChangeStation`][korail_mobile_api.read_models.SelfSeatChangeStation])이, `reasons`에 변경 사유([`SelfSeatChangeReason`][korail_mobile_api.read_models.SelfSeatChangeReason])가 들어 있습니다. 승차역마다 일반실·특실 잔여석 수가 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.errors.KorailSeatUnavailableError] | 좌석을 변경할 수 있는 시간이 아닐 때 (결과 코드 `WRT800176`). 운행 시간 밖의 열차가 여기에 해당합니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import SelfSeatChangeInfoRequest

train = client.get_ticket_list().reservations[0].tickets[0].trains[0]
request = SelfSeatChangeInfoRequest(
    run_date=train.run_date,
    train_no=train.train_no,
    departure_station_code=train.departure_station_code,
    arrival_station_code=train.arrival_station_code,
)
info = client.get_self_seat_change_info(request)
for station in info.stations:
    print(station.departure_station_name, station.general_remaining_seats)
```

## `get_delay_certificate`

지난 승차권의 지연확인증(열차가 몇 분 늦게 도착했는지)을 조회합니다.

```python
KorailClient.get_delay_certificate(
    ticket: OriginalTicketReference,
) -> DelayCertificateResponse
```

지연된 승차권만 대상입니다. 지연되지 않은 승차권은 서버가 실패(결과 코드 `WRT400456`)로 응답하므로 [`KorailAppError`][korail_mobile_api.errors.KorailAppError]가 발생합니다. `ticket`의 `sale_date`에는 승차권의 `return_sale_date`(`MMDD`)를 넣습니다.
지난 승차권은 [`get_ticket_list`](#get_ticket_list)를 `mode="2"`로 호출해 찾습니다.

앱은 `delay_arrival_flag`가 특정 값인 행만 화면에 보여 줍니다. 그 값은 공개돼 있지 않아 확인하지 못했으므로, 라이브러리는 행을 거르지 않고 모두 돌려줍니다.
`run_date`는 응답에 없을 수 있으며 없으면 `None`입니다. 운행일은 `run_day`에도 들어 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference] | 필수 | 조회할 승차권의 반환 식별자입니다. |

**반환값**

[`DelayCertificateResponse`][korail_mobile_api.read_models.DelayCertificateResponse] — `delays`에 지연 행([`DelayCertificateRow`][korail_mobile_api.read_models.DelayCertificateRow]) 목록이 들어 있습니다. 행마다 운행일, 열차 번호, 출발역·도착역, 지연 도착 여부, 지연 시간(분)이 있습니다. 응답에 행 목록이 없으면 빈 튜플입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `ticket`이 `OriginalTicketReference`가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import OriginalTicketReference

ticket = client.get_ticket_list(mode="2").reservations[0].tickets[0]
reference = OriginalTicketReference(
    sale_window_no=ticket.sale_window_no,
    sale_date=ticket.return_sale_date,
    sale_sequence=ticket.sale_sequence,
    return_password=ticket.return_password,
)
certificate = client.get_delay_certificate(reference)
for row in certificate.delays:
    print(row.run_day, row.train_no, row.arrival_station_name, row.delay_minutes)
```

## `get_delay_return_receipt`

열차 지연으로 돌려받은 지연료의 반환 영수증을 조회합니다.

```python
KorailClient.get_delay_return_receipt(
    ticket: OriginalTicketReference,
) -> DelayReturnReceiptResponse
```

[`get_delay_certificate`](#get_delay_certificate)와 같은 반환 식별자를 쓰며, `ticket`의 `sale_date`에는 승차권의 `return_sale_date`(`MMDD`)를 넣습니다. 실서버에서는 오류 응답까지만 확인했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference] | 필수 | 조회할 승차권의 반환 식별자입니다. |

**반환값**

[`DelayReturnReceiptResponse`][korail_mobile_api.read_models.DelayReturnReceiptResponse] — 반환일(`return_date`), 지급 방법(`payment_method_name`), 반환 금액(`return_amount`)이 들어 있습니다. 세 필드는 모두 문자열이며 응답에 없으면 `None`입니다. 반환 내역이 없으면 `None` 필드를 담은 응답 대신 [`KorailNoResultsError`][korail_mobile_api.errors.KorailNoResultsError]가 발생합니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `ticket`이 `OriginalTicketReference`가 아닐 때 |
| [`KorailNoResultsError`][korail_mobile_api.errors.KorailNoResultsError] | 조회할 지연료 반환 내역이 없을 때 (결과 코드 `IRZ000005`) |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 응답만 확인 |

**예제**

```python
from korail_mobile_api import KorailNoResultsError

# reference는 get_delay_certificate 예제와 같은 방법으로 만든 값입니다.
try:
    receipt = client.get_delay_return_receipt(reference)
except KorailNoResultsError:
    print("지연료 반환 내역이 없습니다.")
else:
    print(receipt.return_date, receipt.payment_method_name, receipt.return_amount)
```
