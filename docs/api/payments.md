# 결제·환불

홀드를 카드로 결제하고, 결제 전에 할인 조합을 다시 계산하고, 발권된 승차권을 환불하는 메서드입니다.
환불은 승차권 한 장씩 처리하며, 상세 조회와 수수료 조회를 거친 뒤에 요청합니다.
역에서 발권한 승차권은 확인과 실행으로 나뉜 별도 메서드로 환불합니다.
작업 순서 전체는 [결제와 환불](../guide/payments.md) 가이드를 참고하세요.

흐름:

- 결제: 예약 메서드로 홀드 만들기 → (필요하면) [`recalculate_price`](#recalculate_price) → [`pay_with_card`](#pay_with_card)
- 기존 예약 결제: [`get_reservation_hold`](reservations.md#get_reservation_hold)로 홀드 가져오기 → 금액 확인 → [`pay_with_card`](#pay_with_card)
- 환불: [`list_tickets`](account.md#list_tickets) → [`get_refund_ticket_detail`](#get_refund_ticket_detail) → `PaidTicket.from_refund_detail()` → [`get_refund_fee`](#get_refund_fee) → [`refund`](#refund)
- 역에서 발권한 승차권 환불: [`check_station_ticket_refund`](#check_station_ticket_refund) → `StationRefundExecutionRequest.from_verification()` → [`refund_station_ticket`](#refund_station_ticket)

## `pay_with_card`

홀드를 카드로 결제합니다.

```python
KorailClient.pay_with_card(
    hold: ReservationHoldResponse,
    card: CardPayment,
) -> ReservationPaymentResponse
```

홀드 응답에 담긴 PNR, 창구번호, 임시 작업번호, 첫 여정의 예약 변경번호를 그대로 되돌려 보내고, `hold.received_amount`를 청구합니다.
`total_price`는 앱이 화면에 표시하는 합계이며 결제 금액으로 쓰지 않습니다.
`hold`에는 예약 메서드, [`get_reservation_hold`](reservations.md#get_reservation_hold),
[`recalculate_price`](#recalculate_price)가 반환한 객체를 그대로 넘깁니다.
기존 예약번호로 가져오는 방법은 [기존 예약 결제 가이드](../guide/payments.md#existing-reservation)를 참고하세요.

`pay_with_card`는 세션 만료(`P058`)를 뺀 모든 실패 응답을 예외로 바꾸지 않고 반환하며, 카드 거절도 그중 하나입니다.
실패 응답은 `strResult`가 `"FAIL"`이거나 없는 응답이며, `strResult`가 없으면 `str_result`는 `None`입니다. 반환값의 `str_result`가 `"SUCC"`인지 반드시 확인하세요.
최상위 결과와 정산수단별 `settlement_result`는 따로 읽으며, 라이브러리는 `settlement_result`의 값을 해석하지 않습니다.

요청 전에 홀드와 카드 입력을 검사하며, 검사는 대기열에 들어가기 전에 끝납니다.
예약대기 홀드와 결제 금액이 0원인 홀드는 거절합니다. 앱은 0원 홀드를 카드 없이 발권하는데, 라이브러리는 그 경로를 구현하지 않습니다.
카드 입력 규칙은 [가이드의 카드 정보 표](../guide/payments.md#card-payment)에 정리돼 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `hold` | [`ReservationHoldResponse`][korail_mobile_api.ReservationHoldResponse] | 필수 | 결제할 홀드입니다. 성공한 홀드여야 하며 `pnr_no`, `window_no`, 숫자로 된 `received_amount`가 있어야 합니다. |
| `card` | [`CardPayment`][korail_mobile_api.CardPayment] | 필수 | 결제할 카드 정보입니다. |

**반환값**

[`ReservationPaymentResponse`][korail_mobile_api.ReservationPaymentResponse] — 결제 결과입니다.
발권된 승차권은 `tickets`([`ReservationPaymentTicket`][korail_mobile_api.ReservationPaymentTicket]), 정산 내역은 `settlements`([`ReservationPaymentSettlement`][korail_mobile_api.ReservationPaymentSettlement])에 들어 있습니다.
결제 응답에는 PNR이 없으므로 PNR은 `hold.pnr_no`를 씁니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `card`가 [`CardPayment`][korail_mobile_api.CardPayment]가 아니거나 `hold`가 [`ReservationHoldResponse`][korail_mobile_api.ReservationHoldResponse]가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 예약대기 홀드(`hold.payable`이 `False`)일 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 홀드의 `str_result`가 `"SUCC"`가 아니거나, `pnr_no`·`window_no`가 비었거나, `received_amount`가 숫자가 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `received_amount`가 0일 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 유효기간이 이미 지났을 때. 카드 번호·할부 개월 수·유효기간·비밀번호·`birthday`의 형식 오류는 [`CardPayment`][korail_mobile_api.CardPayment]를 만들 때 발생합니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | `pay` | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 카드로 `hold.received_amount`만큼 실제로 청구됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from getpass import getpass

from korail_mobile_api import CardPayment

hold = client.reserve(train)  # train은 search_trains 결과의 열차입니다
card = CardPayment(
    card_number=getpass("카드 번호: "),
    card_password=getpass("카드 비밀번호 앞 2자리: "),
    card_expire=input("유효기간(YYMM): "),
    birthday=getpass("생년월일 6자리: "),
)
payment = client.pay_with_card(hold, card)
if payment.str_result != "SUCC":
    print("결제 실패:", payment.h_msg_cd, payment.h_msg_txt)
```

## `recalculate_price`

홀드의 할인 조합을 바꿔 결제 금액을 다시 계산합니다.

```python
KorailClient.recalculate_price(
    request: PriceRecalculationRequest,
) -> ReservationHoldResponse
```

PNR과 승객별 할인 행을 보내고, 서버가 다시 계산한 홀드를 반환합니다. 결제는 이 반환값으로 합니다.
요청은 보통 [`PriceRecalculationRequest`][korail_mobile_api.PriceRecalculationRequest]의 `for_hold()`로 만듭니다.
`for_hold()`는 홀드의 첫 여정 좌석마다 한 행을 만들고, 좌석의 승객 유형·객실·현재 할인 코드·증빙 번호를 복사합니다.
요청할 할인 코드는 좌석 수와 같은 개수로 넘겨야 합니다. `for_hold()`는 `payable=False`인 예약대기 홀드를 요청 전에 [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError]로 거절합니다.
7.0.8에서는 실제 홀드로 요청했지만 할인 코드 `000`은 `WZZ000001`, 변경 없는 요청은 `ERR930202`로 거절됐습니다. 이 버전의 정상 재계산은 아직 확인하지 못했습니다.

요청은 하나만 보냅니다. 앱처럼 재계산 뒤 같은 PNR을 장바구니에 담으려면 재계산이 성공한 뒤 [`add_to_cart`](reservations.md#add_to_cart)를 따로 호출하세요.
3.0에서 `add_to_cart=` 인자와 그 결과를 담던 `cart_addition`·`cart_addition_error`(2.6.2에서 추가)를 제거했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`PriceRecalculationRequest`][korail_mobile_api.PriceRecalculationRequest] | 필수 | 재계산할 PNR과 승객별 할인 행([`PriceRecalculationRow`][korail_mobile_api.PriceRecalculationRow])입니다. 행은 1~9개입니다. |

**반환값**

[`ReservationHoldResponse`][korail_mobile_api.ReservationHoldResponse] — 재계산된 홀드입니다. 바뀐 결제 금액은 `received_amount`에 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `request`가 [`PriceRecalculationRequest`][korail_mobile_api.PriceRecalculationRequest]가 아니거나, `pnr_no`가 비었거나, 행이 없거나 9개를 넘을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 행이 [`PriceRecalculationRow`][korail_mobile_api.PriceRecalculationRow]가 아니거나, 행의 필드가 문자열이 아니거나, `passenger_type_code`·`room_class_code`·`discount_kind_code`가 비었을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `non_member_no`, `cabin_class_code`, `seat_attribute_code_2`, `seat_attribute_code_4`, `seat_attribute_code_5`가 `None`이 아니면서 비어 있거나 문자열이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 서버 거절 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 서버에 있는 홀드의 할인과 결제 금액이 바뀝니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import PriceRecalculationRequest

hold = client.reserve(train)  # 어른 1명이므로 첫 여정 좌석은 하나입니다
request = PriceRecalculationRequest.for_hold(hold, [input("요청할 할인 코드: ")])
recalculated = client.recalculate_price(request)
print(hold.received_amount, "->", recalculated.received_amount)
payment = client.pay_with_card(recalculated, card)
```

## `get_refund_ticket_detail`

환불할 승차권의 여정·좌석·운임 상세를 조회합니다.

```python
KorailClient.get_refund_ticket_detail(
    ticket: OriginalTicketReference,
    *,
    from_purchase_history: bool = False,
    txt_index: str | None = None,
) -> RefundTicketDetailResponse
```

환불하기 전에 승차권 내용을 확인하고, 환불 입력인 [`PaidTicket`][korail_mobile_api.PaidTicket]을 만드는 데 씁니다.
반환값을 `PaidTicket.from_refund_detail()`에 넘기면 [`refund`](#refund)에 필요한 식별자를 앱과 같은 방식으로 채웁니다.

`ticket`은 [`list_tickets`](account.md#list_tickets)의 승차권에서 만듭니다. `sale_date`에는 승차권의 `return_sale_date`를 넣습니다.
응답의 `refund_possible_flag`는 환불 성공을 보장하지 않습니다. 이 값이 `"Y"`여도 [`get_refund_fee`](#get_refund_fee)이 실패할 수 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference] | 필수 | 승차권의 반환 식별자입니다. 네 필드 모두 비어 있지 않아야 합니다. |
| `from_purchase_history` | `bool` | `False` | 구매 이력에서 조회하는 승차권이면 `True`입니다. `True`이면 `"Y"`, `False`이면 `"N"`을 보냅니다. 앱이 이 필드에 쓰는 값은 공개돼 있지 않아 확인하지 못했습니다. |
| `txt_index` | `str \| None` | `None` | `txtIndex` 필드로 보낼 값입니다. `None`이면 보내지 않습니다. |

**반환값**

[`RefundTicketDetailResponse`][korail_mobile_api.RefundTicketDetailResponse] — 승차권 상세입니다.
`pnr_no`, 현재 `sale_date`, `original_window_no`, `original_sale_date`, `original_sale_sequence`, `original_return_password`가 환불 입력·조회 대상 연결에 쓰입니다.
`PaidTicket.from_refund_detail()`은 `original_sale_date`를 `return_sale_date`에, 동반자 이름·생년월일을
`companion_name`·`companion_certificate_no`에 복사하고 현재 `sale_date`는 별도로 유지합니다.
여정은 `journeys`([`RefundTicketJourney`][korail_mobile_api.RefundTicketJourney]), 좌석은 각 여정의 `seats`([`RefundTicketSeat`][korail_mobile_api.RefundTicketSeat])에 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError] | `ticket`이 [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference]가 아니거나, `from_purchase_history`가 `bool`이 아니거나, `txt_index`가 문자열도 `None`도 아니거나 빈 문자열·공백뿐인 문자열일 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 응답 파싱 |

**예제**

```python
from korail_mobile_api import OriginalTicketReference

ticket = client.list_tickets().reservations[0].tickets[0]
reference = OriginalTicketReference(
    sale_window_no=ticket.sale_window_no,
    sale_date=ticket.return_sale_date,
    sale_sequence=ticket.sale_sequence,
    return_password=ticket.return_password,
)
detail = client.get_refund_ticket_detail(reference)
for journey in detail.journeys:
    print(journey.train_no, journey.departure_station_name, journey.arrival_station_name)
```

<a id="get_refund_commission"></a>

## `get_refund_fee`

승차권 한 장의 예상 환불액과 수수료를 조회합니다.

```python
KorailClient.get_refund_fee(
    ticket: OriginalTicketReference,
    companion: RefundCompanion = RefundCompanion(),
) -> RefundCommissionResponse
```

실제로 환불하지는 않습니다. [`refund`](#refund)는 이 메서드의 성공 응답을 `commission`으로 받아야 하므로 환불 전에 반드시 호출합니다.
`ticket`에는 [`get_refund_ticket_detail`](#get_refund_ticket_detail)에 넘긴 값과 같은 반환 식별자를 씁니다.
이 식별자의 `sale_date`(원표 반환일)는 환불 요청에 쓰는 `PaidTicket.sale_date`와 다른 값이므로 섞어 쓰지 않습니다.
동반자가 있다면 상세에서 복사한 이름·증빙번호와 같은 `RefundCompanion`을 넘기세요.
기존 시그니처는 유지하며 조회 시그니처에 별도 필수 인자는 추가하지 않습니다.

응답의 `proceed_possible_flag`는 라이브러리가 검사하지 않습니다. 앱이 비교하는 값이 공개돼 있지 않아 확인하지 못했습니다.
이미 환불한 승차권(결과 코드 `WRT200399`)이나 승차일이 지난 승차권(`WRT200022`)은 서버가 실패로 응답하므로 [`KorailAppError`][korail_mobile_api.KorailAppError]가 발생합니다.
7.0.8에서는 과거 승차권의 `WRT200022`까지만 확인했습니다. 실제 환불액·수수료의 정상 응답은 7.0.6 시기 기록입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference] | 필수 | 수수료를 조회할 승차권의 반환 식별자입니다. |
| `companion` | [`RefundCompanion`][korail_mobile_api.RefundCompanion] | `RefundCompanion()` | 동반자 이름(`name`)과 생년월일(`certificate_no`)입니다. 기본값은 두 값이 모두 빈 문자열이며, 빈 값은 요청에 싣지 않습니다. |

**반환값**

[`RefundCommissionResponse`][korail_mobile_api.RefundCommissionResponse] — 예상 환불액(`refund_amount`), 수수료(`refund_fee`), 사용 가능 마일리지(`usable_mileage`)를 담습니다.
`ticket_return_times_division_code`는 [`refund`](#refund)가 요청에 되돌려 싣는 값입니다.
반환 시 원표 창구번호·반환일·일련번호·비밀번호·동반자 이름·증빙번호를 비공개 조회 문맥으로 연결합니다.
이 문맥은 `repr`에서 숨기며 파일에 저장하지 않습니다. 직접 생성·직접 파싱한 응답에는 이 연결이 없으므로
환불에 사용할 수 없습니다. 이는 대상 혼용 방지이지 금액의 유효기간·서버 승인 보장이 아닙니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `ticket`이 [`OriginalTicketReference`][korail_mobile_api.OriginalTicketReference]가 아니거나 `companion`이 [`RefundCompanion`][korail_mobile_api.RefundCompanion]이 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 거절 |

**예제**

```python
from korail_mobile_api import PaidTicket, RefundCompanion

paid = PaidTicket.from_refund_detail(client.get_refund_ticket_detail(reference))
companion = RefundCompanion(name=paid.companion_name, certificate_no=paid.companion_certificate_no)
commission = client.get_refund_fee(reference, companion)
print("환불액", commission.refund_amount, "수수료", commission.refund_fee)
print("사용 가능 마일리지", commission.usable_mileage)
```

## `refund`

발권된 승차권 한 장을 환불합니다.

```python
KorailClient.refund(
    ticket: PaidTicket,
    *,
    settle_mileage: bool = False,
    pbp_acceptance_target_flag: str | None = None,
    commission: RefundCommissionResponse,
    latitude: str | None = None,
    longitude: str | None = None,
) -> RefundTicketResponse
```

PNR 전체가 아니라 `ticket`이 가리키는 승차권 한 장만 환불하며, 수수료가 빠질 수 있습니다.
한 PNR에 승차권이 여러 장이면 장마다 상세 조회, 수수료 조회, 환불을 따로 합니다.
`commission`은 필수 키워드 인자이며 [`get_refund_fee`](#get_refund_fee)의 성공 응답이어야 합니다. `None`을 포함해 [`RefundCommissionResponse`][korail_mobile_api.RefundCommissionResponse]가 아닌 값이나 실패 응답을 넘기면 요청 전에 거절합니다.
환불은 **fail-closed**입니다. 실제 조회 반환값의 비공개 문맥과 원표 창구번호·반환일·일련번호·비밀번호·동반자 이름·증빙번호가 모두 일치해야 합니다.
직접 생성·직접 파싱한 수수료 응답, 다른 표의 응답, 원표 반환일이 없는 입력은 요청 전에 거절합니다.
라이브러리는 수수료를 대신 조회하지 않고, 요청을 다시 보내지도 않습니다.

`ticket`은 `PaidTicket.from_refund_detail()`로 만듭니다. 이 메서드는 상세 응답의 판매일(`sale_date`)과 원표 식별자를 옮겨 담고, 열차 번호를 따로 주지 않으면 첫 여정의 열차 번호를 씁니다.
원표 반환일은 상세의 `original_sale_date`에서 `return_sale_date`로 따로 옮깁니다. 수동 생성할 때도
키워드 전용 `return_sale_date`를 명시해야 하며 현재 `sale_date`로 대체하지 않습니다.
동반자 필드와 조회 문맥의 `repr` 숨김은 속성·`raw`·직렬화 전체의 마스킹이 아닙니다.
대상 연결은 수수료 금액의 유효기간이나 서버 승인을 보장하지 않습니다.
`ticket.train_no`가 있으면 열차 번호를, `commission.ticket_return_times_division_code`가 있으면 그 값을 요청에 함께 싣습니다.

`settle_mileage=True`는 `commission.usable_mileage`가 `commission.refund_fee` 이상일 때만 허용합니다.
두 값은 정수로 읽으며, 없거나 정수로 읽을 수 없으면 0으로 봅니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`PaidTicket`][korail_mobile_api.PaidTicket] | 필수 | 환불할 승차권 한 장입니다. `pnr_no`, 현재 `sale_date`, `sale_window_no`, 원표 `return_sale_date`, `sale_sequence`, `return_password`가 비어 있지 않아야 하며 동반자 정보도 수수료 조회와 같아야 합니다. |
| `settle_mileage` | `bool` | `False` | 수수료를 마일리지로 정산할지 여부입니다. |
| `pbp_acceptance_target_flag` | `str \| None` | `None` | 대리수령 대상 플래그입니다. `None`이면 `ticket.pbp_acceptance_target_flag`를 씁니다. 승차권 상세 응답에는 이 값이 보통 없으므로 `from_refund_detail()`로 만든 `ticket`에서는 `None`일 수 있으며, 그러면 이 필드를 보내지 않습니다. 앱처럼 보내려면 [`list_tickets`](account.md#list_tickets) 승차권의 `pbp_acceptance_target_flag`를 넘기세요. |
| `commission` | [`RefundCommissionResponse`][korail_mobile_api.RefundCommissionResponse] | 필수 | 같은 원표·동반자로 실제 [`get_refund_fee`](#get_refund_fee)이 반환한 성공 응답입니다. |
| `latitude` | `str \| None` | `None` | 위도입니다. `None`이면 보내지 않습니다. |
| `longitude` | `str \| None` | `None` | 경도입니다. `None`이면 보내지 않습니다. |

**반환값**

[`RefundTicketResponse`][korail_mobile_api.RefundTicketResponse] — 환불 결과입니다.
`settlement_method_codes`에 정산수단 코드가, `settlement_list_is_null`에 서버가 정산 목록을 `null`로 보냈는지가 들어 있습니다.
서버가 실패로 응답하면 반환하지 않고 예외가 발생합니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `commission`이 [`RefundCommissionResponse`][korail_mobile_api.RefundCommissionResponse]가 아닐 때. `None`도 거절합니다. |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `ticket`이 [`PaidTicket`][korail_mobile_api.PaidTicket]이 아닐 때. `pnr_no`, `sale_date`, `sale_window_no`, `sale_sequence`, `return_password` 중 비었거나 문자열이 아닌 값은 `PaidTicket`을 만들 때 거절합니다. |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `settle_mileage`가 `bool`이 아니거나, 대리수령 대상 플래그가 문자열도 `None`도 아닐 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `commission.str_result`가 `"SUCC"`가 아닐 때. 예외의 `raw`에 `commission.raw`가 들어 있습니다. |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | 수수료 응답의 비공개 조회 문맥이 없거나 원표·동반자 정보가 다르거나 `ticket.return_sale_date`가 없을 때. 직접 생성·직접 파싱한 수수료 응답도 거절합니다. |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `settle_mileage=True`인데 사용 가능 마일리지가 수수료보다 적을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 승차권 한 장이 실제로 환불되며 수수료가 빠질 수 있습니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import PaidTicket, RefundCompanion

detail = client.get_refund_ticket_detail(reference)
paid = PaidTicket.from_refund_detail(detail)
companion = RefundCompanion(name=paid.companion_name, certificate_no=paid.companion_certificate_no)
commission = client.get_refund_fee(reference, companion)
result = client.refund(
    paid,
    commission=commission,
    pbp_acceptance_target_flag=ticket.pbp_acceptance_target_flag,  # list_tickets의 승차권
)
print(result.h_msg_cd, result.h_msg_txt)
```

<a id="verify_station_ticket_refund"></a>

## `check_station_ticket_refund`

역에서 발권한 승차권을 온라인으로 환불할 수 있는지와 금액을 확인합니다.

```python
KorailClient.check_station_ticket_refund(
    request: StationRefundVerificationRequest,
) -> StationRefundVerificationResponse
```

실제 환불은 하지 않습니다. 확인 결과로 [`refund_station_ticket`](#refund_station_ticket)의 입력을 만듭니다. 실서버에서 확인하지 못한 메서드입니다.

이 응답은 다른 응답과 달리 `strResult`가 없어도 실패로 보지 않으며, 이때 `str_result`는 `None`입니다. `strResult`가 `"FAIL"`이면 다른 메서드처럼 예외가 발생합니다.
다만 `StationRefundExecutionRequest.from_verification()`은 `str_result`가 `"SUCC"`인 응답만 받습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`StationRefundVerificationRequest`][korail_mobile_api.StationRefundVerificationRequest] | 필수 | 고객 이름(`customer_name`)과 반환번호 네 칸(`return_no_1`~`return_no_4`)입니다. 모든 필드는 만들 때 비어 있지 않은지 검사합니다. |

**반환값**

[`StationRefundVerificationResponse`][korail_mobile_api.StationRefundVerificationResponse] — 받은 금액(`received_amount`), 수수료(`refund_fee`), 환불액(`refund_amount`), 안내 문구(`popup_message`, `result_message`)를 담습니다.
원표 목록은 `original_tickets`([`StationRefundOriginalTicket`][korail_mobile_api.StationRefundOriginalTicket])에 있고, 서버가 목록을 `null`로 보냈으면 `original_ticket_list_is_null`이 `True`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `request`가 [`StationRefundVerificationRequest`][korail_mobile_api.StationRefundVerificationRequest]가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 미실행 |

**예제**

```python
from korail_mobile_api import StationRefundVerificationRequest

name = input("이름: ")
verification = client.check_station_ticket_refund(
    StationRefundVerificationRequest(
        customer_name=name,
        return_no_1=input("반환번호 1: "),
        return_no_2=input("반환번호 2: "),
        return_no_3=input("반환번호 3: "),
        return_no_4=input("반환번호 4: "),
    )
)
print(verification.refund_amount, verification.refund_fee, verification.result_message)
```

<a id="execute_station_ticket_refund"></a>

## `refund_station_ticket`

역에서 발권해 확인을 마친 승차권의 환불을 요청합니다.

```python
KorailClient.refund_station_ticket(
    request: StationRefundExecutionRequest,
) -> StationRefundExecutionResponse
```

`request`는 `StationRefundExecutionRequest.from_verification()`으로 만듭니다. 실서버에서 확인하지 못한 메서드입니다.

`from_verification()`은 확인 응답의 첫 원표와 확인된 환불액·수수료를 옮겨 담고, 연락처와 이름을 추가로 받습니다.
확인 응답이 성공이 아니거나 원표가 없을 때, 옮겨 담을 값이나 연락처·이름 중 빈 값이 있을 때 [`KorailProtocolError`][korail_mobile_api.KorailProtocolError]를 발생시킵니다.

환불과 접수 상태가 실제로 바뀔 수 있으므로 반환값의 결과와 반환 구분 코드를 확인하세요. 서버가 실패로 응답하면 예외가 발생합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `request` | [`StationRefundExecutionRequest`][korail_mobile_api.StationRefundExecutionRequest] | 필수 | 환불 실행 입력입니다. 12개 필드 모두 만들 때 비어 있지 않은지 검사합니다. |

**반환값**

[`StationRefundExecutionResponse`][korail_mobile_api.StationRefundExecutionResponse] — 환불 요청 결과입니다. 반환 구분 코드는 `refund_division_code`에 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `request`가 [`StationRefundExecutionRequest`][korail_mobile_api.StationRefundExecutionRequest]가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 7.0.8 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미실행 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 역에서 발권한 승차권의 환불이 실제로 요청됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
from korail_mobile_api import StationRefundExecutionRequest

request = StationRefundExecutionRequest.from_verification(
    verification,
    customer_phone=input("연락처: "),
    customer_name=name,
)
result = client.refund_station_ticket(request)
print(result.str_result, result.refund_division_code)
```
