# 결제와 환불

이 가이드는 예약으로 만든 홀드를 카드로 결제하고, 필요하면 결제 전에 할인을 다시 계산하고, 발권된 승차권을 환불하는 과정을 순서대로 따라 합니다.
역에서 발권한 승차권의 환불도 다룹니다.
결제·재계산·환불 단계는 모두 호출하는 즉시 실제로 처리되므로 금액과 대상을 확인한 뒤 실행하세요.

## 준비 {#setup}

결제·환불 메서드는 모두 로그인이 필요하며, 결제에는 홀드도 필요합니다.
아래 예제는 열차를 조회해 첫 열차에 어른 1명으로 홀드를 만듭니다. 홀드를 만드는 다른 방법은 [예약](reservations.md) 가이드를 참고하세요.
이후 예제는 이 블록의 `client`와 `hold`를 이어서 씁니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))

query = TrainSearchQuery(
    departure_station_code="서울",
    arrival_station_code="부산",
    departure_date="20261002",
    departure_time="090000",
)
train = client.search_trains(query).trains[0]
hold = client.reserve(train)
print(hold.pnr_no, hold.received_amount, hold.payment_deadline_date, hold.payment_deadline_time)
```

결제 기한은 홀드의 `payment_deadline_date`와 `payment_deadline_time`에 들어 있습니다.
결제하지 않을 홀드는 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소하세요.

!!! warning "실제로 처리됩니다"
    [`reserve`](../api/reservations.md#reserve)를 호출하면 좌석이 실제로 잡힙니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 [`get_reservation_history`](../api/reservations.md#get_reservation_history)로 결과를 확인하세요.

## 카드로 결제하기 {#card-payment}

카드 정보는 [`CardPayment`][korail_mobile_api.mutation_models.CardPayment]로 만들어 [`pay_with_card`](../api/payments.md#pay_with_card)에 넘깁니다.

| 필드 | 기본값 | 형식 |
|---|---|---|
| `card_number` | 필수 | 카드 번호입니다. 하이픈 없이 숫자 13~16자리입니다. |
| `card_password` | 필수 | 카드 비밀번호 앞 2자리 숫자입니다. |
| `card_expire` | 필수 | 유효기간 `YYMM` 숫자 4자리입니다. 월은 `01`~`12`입니다. |
| `birthday` | 필수 | `card_type`이 `"J"`이면 생년월일 숫자 6자리, `"S"`이면 숫자 10자리입니다. |
| `installment` | `"0"` | 할부 개월 수입니다. 숫자 1~2자리이며 `"0"`은 일시불입니다. |
| `card_type` | `"J"` | `"J"`(개인) 또는 `"S"`(법인)입니다. |

`card_type`은 `CardPayment`를 만들 때 검사하고, 나머지 필드는 `pay_with_card`가 요청을 보내기 전에 검사합니다.
어느 쪽이든 형식이 틀리면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생하고 요청은 나가지 않습니다.
유효기간이 한국 시간 기준 이번 달이면 허용하고, 그보다 이전이면 만료로 보고 거절합니다.
검사는 형식과 유효기간만 확인하며, 카드를 실제로 쓸 수 있는지는 확인하지 않습니다.

청구 금액은 홀드의 `received_amount`입니다. `total_price`는 앱이 화면에 표시하는 합계이며 결제에 쓰지 않습니다.
라이브러리는 홀드 응답에 좌석별 금액이 있으면 그 합을 `received_amount`로 쓰고, 그 합이 응답의 총액과 다르면 홀드를 읽는 단계에서 `KorailProtocolError`를 발생시킵니다.

```python
from getpass import getpass

from korail_mobile_api import CardPayment

card = CardPayment(
    card_number=getpass("카드 번호(숫자만): "),
    card_password=getpass("카드 비밀번호 앞 2자리: "),
    card_expire=input("유효기간(YYMM): "),
    birthday=getpass("생년월일 6자리: "),
)
print("청구 금액:", hold.received_amount)
payment = client.pay_with_card(hold, card)
if payment.str_result == "SUCC":
    print("결제 완료:", len(payment.tickets), "장 발권")
else:
    print("결제 실패:", payment.h_msg_cd, payment.h_msg_txt)
```

### 카드 거절 확인 {#card-decline}

카드 거절은 예외가 아닙니다. `pay_with_card`는 `str_result`가 `"FAIL"`인 [`ReservationPaymentResponse`][korail_mobile_api.mutation_models.ReservationPaymentResponse]를 반환하며, 사유는 `h_msg_cd`와 `h_msg_txt`에 들어 있습니다.
반환값을 받았다는 것만으로 결제가 끝났다고 판단하지 말고 `str_result`를 확인하세요. 세션 만료(`P058`)는 예외로 발생합니다.
결제 응답에는 PNR이 없으므로 이후 단계에서는 `hold.pnr_no`를 씁니다.

### 결제할 수 없는 홀드 {#unpayable-holds}

다음 홀드는 요청을 보내기 전에 `KorailProtocolError`로 거절합니다.

- **예약대기 홀드**: `payable`이 `False`입니다. 예약대기는 좌석을 확보한 것이 아니므로 결제하지 않고, 대기 옵션만 [`confirm_standby_hold`](../api/reservations.md#confirm_standby_hold)로 저장합니다.
- **0원 홀드**: `received_amount`가 0인 홀드입니다. 앱은 이런 홀드를 카드 없이 발권하며, 라이브러리는 그 경로를 구현하지 않습니다.
- **실패했거나 식별자가 빠진 홀드**: `str_result`가 `"SUCC"`가 아니거나, `pnr_no`·`window_no`가 비었거나, `received_amount`가 숫자가 아닌 홀드입니다.

!!! warning "실제로 처리됩니다"
    `pay_with_card`를 호출하면 카드로 실제 금액이 청구됩니다. 응답을 읽지 못해 예외가 나도 결제는 처리됐을 수 있으므로 다시 결제하기 전에 [`get_reservation_history`](../api/reservations.md#get_reservation_history)나 [`get_ticket_list`](../api/account.md#get_ticket_list)로 결과를 확인하세요.

## 결제 전에 할인 다시 계산하기 {#recalculation}

홀드의 할인 조합을 바꾸려면 결제 전에 [`recalculate_price`](../api/payments.md#recalculate_price)를 호출합니다.
요청은 [`PriceRecalculationRequest`][korail_mobile_api.mutation_models.PriceRecalculationRequest]의 `for_hold()`로 만듭니다.

- `for_hold(hold, requested_discount_codes)`는 성공한 홀드의 첫 여정 좌석마다 한 행을 만들고, 좌석의 승객 유형·객실·현재 할인 코드·증빙 번호를 복사합니다.
- `requested_discount_codes`는 좌석마다 새로 요청할 할인 코드를 좌석 순서대로 담은 목록입니다. 빈 문자열도 그 좌석의 자리를 지키도록 그대로 보냅니다.
- 코드 개수가 첫 여정 좌석 수와 다르면 `KorailProtocolError`가 발생하며, 메시지에 좌석 수가 들어 있습니다.

재계산 결과는 새 [`ReservationHoldResponse`][korail_mobile_api.mutation_models.ReservationHoldResponse]입니다. 결제는 원래 홀드가 아니라 이 반환값으로 합니다.

`add_to_cart=True`를 넘기면 재계산이 성공한 뒤 같은 PNR을 장바구니에 추가합니다.
장바구니 추가가 실패 응답이어도 예외는 나지 않고 결과가 반환값의 `cart_addition`에 남습니다.
재계산 자체가 실패하면 예외가 발생하고 장바구니 요청은 보내지 않습니다.

```python
from korail_mobile_api import PriceRecalculationRequest

request = PriceRecalculationRequest.for_hold(hold, [input("요청할 할인 코드: ")])
recalculated = client.recalculate_price(request, add_to_cart=True)
print(hold.received_amount, "->", recalculated.received_amount)
cart = recalculated.cart_addition
if cart is not None and cart.str_result != "SUCC":
    print("장바구니 추가 실패:", cart.h_msg_cd, cart.h_msg_txt)

hold = recalculated  # 결제는 재계산된 홀드로 합니다
```

!!! warning "실제로 처리됩니다"
    `recalculate_price`를 호출하면 서버에 있는 홀드의 할인과 결제 금액이 바뀌고, `add_to_cart=True`이면 장바구니에도 추가됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 환불할 승차권 찾기 {#find-ticket}

환불은 발권된 승차권 한 장 단위로 합니다.
먼저 [`get_ticket_list`](../api/account.md#get_ticket_list)에서 환불할 승차권을 찾고, 그 반환 식별자로 [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]를 만듭니다.
`sale_date`에는 승차권의 `sale_date`가 아니라 `return_sale_date`를 넣습니다.
넘긴 값이 `None`이거나 비어 있으면 `OriginalTicketReference`를 만들 때 `KorailProtocolError`가 발생합니다.

```python
from korail_mobile_api import OriginalTicketReference

tickets = client.get_ticket_list()
ticket = next(
    t for reservation in tickets.reservations for t in reservation.tickets if t.pnr_no == hold.pnr_no
)
reference = OriginalTicketReference(
    sale_window_no=ticket.sale_window_no,
    sale_date=ticket.return_sale_date,
    sale_sequence=ticket.sale_sequence,
    return_password=ticket.return_password,
)
```

## 상세와 수수료 확인하기 {#commission}

환불 요청에는 두 조회 결과가 필요합니다.

1. [`get_refund_ticket_detail`](../api/payments.md#get_refund_ticket_detail)로 승차권 상세를 조회하고, `PaidTicket.from_refund_detail()`로 환불 입력을 만듭니다.
   상세에 PNR, 판매일, 원표 창구번호·일련번호·반환 비밀번호 중 빠진 값이 있으면 `KorailProtocolError`가 발생합니다.
2. [`get_refund_commission`](../api/payments.md#get_refund_commission)으로 예상 환불액과 수수료를 조회합니다. 이 응답은 환불 요청에 그대로 넘깁니다.

두 단계는 판매일을 다르게 씁니다. 상세 조회와 수수료 조회는 `reference`의 원표 반환일을 쓰고, 환불 요청은 상세 응답의 판매일을 씁니다.
`from_refund_detail()`이 이 차이를 처리하므로 [`PaidTicket`][korail_mobile_api.mutation_models.PaidTicket]을 직접 만들기보다 이 메서드를 쓰세요.

```python
from korail_mobile_api import PaidTicket

detail = client.get_refund_ticket_detail(reference)
paid = PaidTicket.from_refund_detail(detail)

commission = client.get_refund_commission(reference)
print("환불액", commission.refund_amount, "수수료", commission.refund_fee)
print("사용 가능 마일리지", commission.usable_mileage)
```

상세의 `refund_possible_flag`는 환불 성공을 보장하지 않습니다.
이미 환불한 승차권이나 승차일이 지난 승차권은 수수료 조회에서 [`KorailAppError`][korail_mobile_api.errors.KorailAppError]가 발생합니다.

## 환불하기 {#refund}

[`refund`](../api/payments.md#refund)에 `PaidTicket`과 수수료 조회 응답을 넘깁니다. 수수료 조회 응답은 `commission=` 키워드 인자로 넘깁니다.
`commission`은 필수이며, 성공 응답(`str_result`가 `"SUCC"`)이 아니면 요청 전에 거절합니다.
라이브러리는 수수료를 대신 조회하지 않고, 환불 요청을 다시 보내지도 않습니다.

수수료를 마일리지로 정산하려면 `settle_mileage=True`를 넘깁니다.
사용 가능 마일리지(`commission.usable_mileage`)가 수수료(`commission.refund_fee`) 이상일 때만 허용하며, 부족하면 요청 전에 `KorailProtocolError`가 발생합니다.
두 값이 없거나 정수로 읽을 수 없으면 0으로 봅니다.

```python
answer = input(f"수수료 {commission.refund_fee}원을 빼고 환불하려면 y를 입력하세요: ")
if answer == "y":
    result = client.refund(paid, commission=commission)
    print(result.h_msg_cd, result.h_msg_txt)
```

서버가 실패로 응답하면 예외가 발생합니다. 한 PNR에 승차권이 여러 장이면 상세 조회부터 환불까지를 장마다 반복합니다.

!!! warning "실제로 처리됩니다"
    `refund`를 호출하면 승차권 한 장이 실제로 환불되며 수수료가 빠질 수 있습니다. 응답을 읽지 못해 예외가 나도 환불은 처리됐을 수 있으므로 다시 호출하기 전에 [`get_ticket_list`](../api/account.md#get_ticket_list)로 승차권 상태를 확인하세요.

## 역에서 발권한 승차권 환불 {#station-refund}

역에서 발권한 승차권은 확인과 실행 두 단계로 환불합니다. 두 메서드 모두 실서버에서 확인하지 못했습니다.

1. [`verify_station_ticket_refund`](../api/payments.md#verify_station_ticket_refund)에 이름과 반환번호 네 칸을 넘겨 환불 가능 여부와 금액을 확인합니다. 이 단계에서는 환불하지 않습니다.
2. `StationRefundExecutionRequest.from_verification()`으로 확인 결과의 첫 원표와 금액을 옮겨 담고 연락처와 이름을 더해 실행 입력을 만듭니다.
   확인 응답의 `str_result`가 `"SUCC"`가 아니거나 원표가 없으면 `KorailProtocolError`가 발생합니다.
3. [`execute_station_ticket_refund`](../api/payments.md#execute_station_ticket_refund)로 환불을 요청하고, 반환값의 결과와 `refund_division_code`를 확인합니다.

```python
from korail_mobile_api import StationRefundExecutionRequest, StationRefundVerificationRequest

name = input("이름: ")
verification = client.verify_station_ticket_refund(
    StationRefundVerificationRequest(
        customer_name=name,
        return_no_1=input("반환번호 1: "),
        return_no_2=input("반환번호 2: "),
        return_no_3=input("반환번호 3: "),
        return_no_4=input("반환번호 4: "),
    )
)
print("환불액", verification.refund_amount, "수수료", verification.refund_fee)

request = StationRefundExecutionRequest.from_verification(
    verification,
    customer_phone=input("연락처: "),
    customer_name=name,
)
if input("환불하려면 y를 입력하세요: ") == "y":
    result = client.execute_station_ticket_refund(request)
    print(result.str_result, result.refund_division_code)
```

!!! warning "실제로 처리됩니다"
    `execute_station_ticket_refund`를 호출하면 역에서 발권한 승차권의 환불이 실제로 요청됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

## 정리 {#cleanup}

다 쓰고 나면 로그아웃하고 연결을 닫습니다. 자세한 차이는 [시작하기](../getting-started.md)를 참고하세요.

```python
client.logout()
client.close()
```
