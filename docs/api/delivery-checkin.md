# 대리수령·셀프 체크인

이 페이지는 대리수령과 셀프 체크인 메서드를 설명합니다.
대리수령 메서드는 승차권을 전달했던 수령자와 전달한 승차권의 내역을 조회하고, 전달한 승차권을 회수합니다.
셀프 체크인 메서드는 자유석 승차권으로 앉은 좌석을 확인해 등록하고, 등록 정보를 조회하고, 등록을 취소합니다.
승차권을 다른 회원에게 전달하는 요청은 제공하지 않습니다.

대리수령 흐름:

1. [`get_recent_delivery_history`](#get_recent_delivery_history)로 최근에 승차권을 전달했던 수령자를 확인합니다.
2. [`get_pbp_acceptance_specifications`](#get_pbp_acceptance_specifications)로 전달한 승차권의 여정·좌석·수령자 내역을 조회합니다.
3. 회수하려면 2단계에서 받은 승차권 중 첫 여정의 대리수령 예약 번호(`pbp_reservation_no`)마다 한 장을 [`retrieve_delivered_ticket`](#retrieve_delivered_ticket)에 넘깁니다.

셀프 체크인 흐름:

1. [`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail)로 체크인할 승차권의 상세([`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse])를 받습니다. 이후 네 메서드는 모두 이 상세를 받습니다. `get_refund_ticket_detail`에 넘기는 반환 식별자의 판매일에는 승차권의 `return_sale_date`(`MMDD`)를 넣습니다([승차권 식별자 이어 쓰기](account.md#ticket-identifiers) 참고).
2. 자유석에 앉아 좌석에 붙은 QR 코드를 스캔한 문자열로 [`check_self_checkin_seat`](#check_self_checkin_seat)를 호출해 체크인할 수 있는 좌석을 확인합니다.
3. 확인한 좌석 한 행을 [`register_self_checkin`](#register_self_checkin)에 넘겨 등록합니다.
4. [`get_self_checkin_info`](#get_self_checkin_info)로 등록된 좌석 정보를 조회합니다.
5. 등록을 취소하려면 [`cancel_self_checkin`](#cancel_self_checkin)을 호출합니다.

네 메서드가 요청에 싣는 상세 필드는 다음과 같습니다. 판매일만 메서드에 따라 다른 필드를 씁니다.

| [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse] 필드 | 정보 조회·취소 | 좌석 확인·등록 |
|---|:-:|:-:|
| `original_window_no` | 사용 | 사용 |
| `sale_date` | 사용 | - |
| `original_sale_date` | - | 사용 |
| `original_sale_sequence` | 사용 | 사용 |
| `original_return_password` | 사용 | 사용 |
| `journeys[0].journey_sequence` | 값이 있으면 사용 | 값이 있으면 사용 |

`journeys`가 비었거나 첫 여정의 `journey_sequence`가 `None`이면 여정 순번은 보내지 않습니다.
나머지 필드 중 메서드가 쓰는 값이 `None`이거나 비어 있으면 요청을 보내기 전에 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
상세의 `qr_code`(승차권 자체의 QR 코드)는 셀프 체크인 요청에 쓰지 않습니다.

## `get_recent_delivery_history`

최근에 승차권을 전달했던 수령자 목록을 조회합니다.

```python
KorailClient.get_recent_delivery_history() -> RecentDeliveryHistoryResponse
```

요청에는 공통 필드와 함께 로그인 세션의 고객번호(`customer_no`)를 싣습니다.
응답의 수령자 목록(`acepList`)이 `null`이면 `recipients`는 빈 튜플입니다.
`changed_acceptance_reservation_no`는 응답에 해당 값(`chgePbpRsvNo`)이 없으면 `None`입니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`RecentDeliveryHistoryResponse`][korail_mobile_api.read_models.RecentDeliveryHistoryResponse] — `recipients`에 수령자가 [`RecentDeliveryRecipient`][korail_mobile_api.read_models.RecentDeliveryRecipient] 목록으로 들어 있습니다. 각 수령자에는 고객번호, 이름, 전화번호, 회원카드 번호 등이 있습니다.

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
history = client.get_recent_delivery_history()
for recipient in history.recipients:
    print(recipient.acceptance_customer_name, recipient.acceptance_customer_phone)
```

## `get_delivery_recipient`

N카드 2인 승차권을 전달하기 전에 수령자 후보를 조회합니다.

```python
KorailClient.get_delivery_recipient(
    ticket: OriginalTicketReference,
) -> DeliveryRecipientResponse
```

승차권 한 장의 반환 식별자(판매 창구번호, 판매일, 일련번호, 반환 비밀번호)를 보냅니다.
판매일(`sale_date`)은 `YYYYMMDD` 형식으로 넣습니다. [`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail)처럼 `MMDD` 형식을 쓰는 메서드의 값과 섞어 쓰지 마세요.
앱이 이 조회를 부르는 N카드 조건은 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다. 실서버에서 확인하지 못한 메서드입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference] | 필수 | 전달할 N카드 2인 승차권의 반환 식별자입니다. |

**반환값**

[`DeliveryRecipientResponse`][korail_mobile_api.read_models.DeliveryRecipientResponse] — 수령자 후보의 고객번호(`acceptance_customer_management_no`), 이름, 전화번호, 회원카드 번호(`member_card_no`)입니다. 네 값 중 하나라도 응답에 없으면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `ticket`이 [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 미확인 |

**예제**

```python
# reference: N카드 2인 승차권의 OriginalTicketReference (sale_date는 YYYYMMDD)
recipient = client.get_delivery_recipient(reference)
print(recipient.acceptance_customer_name, recipient.member_card_no)
```

## `get_pbp_acceptance_specifications`

전달한 승차권 여러 장의 대리수령 내역을 여정·좌석 단위로 조회합니다.

```python
KorailClient.get_pbp_acceptance_specifications(
    tickets: Sequence[OriginalTicketReference],
) -> PbpAcceptanceSpecificationResponse
```

넘긴 승차권마다 반환 식별자 네 값을 `-`로 이어 붙인 승차권 반환 번호(`tkRetNo`)를 만들고, 승차권 수(`tkCnt`)와 함께 한 번에 보냅니다.
판매일(`sale_date`)은 `YYYYMMDD` 형식으로 넣습니다. 튜플과 목록 모두 받습니다.
대리수령 대상이 아닌 승차권에 대해서는 행이 오지 않을 수 있으므로, 결과의 승차권 수가 넘긴 수보다 적을 수 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `tickets` | `Sequence[`[`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]`]` | 필수 | 조회할 승차권의 반환 식별자입니다. 한 장 이상 넣습니다. |

**반환값**

[`PbpAcceptanceSpecificationResponse`][korail_mobile_api.read_models.PbpAcceptanceSpecificationResponse] — `tickets`에 승차권별 내역이 [`PbpAcceptanceTicket`][korail_mobile_api.read_models.PbpAcceptanceTicket]으로 들어 있습니다.
승차권마다 PNR과 반환 식별자, 여정 목록([`PbpAcceptanceJourney`][korail_mobile_api.read_models.PbpAcceptanceJourney])이 있고, 여정마다 수령자 이름·전화번호, 대리수령 예약 번호(`pbp_reservation_no`), 회수 가능 표시(`withdrawal_possible_flag`), 좌석 목록([`PbpAcceptanceSeat`][korail_mobile_api.read_models.PbpAcceptanceSeat])이 있습니다.
좌석의 `car_no`는 정수입니다. 이 필드들은 모두 필수이므로 하나라도 없으면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `tickets`가 시퀀스가 아니거나 문자열·바이트일 때, 비어 있을 때, [`OriginalTicketReference`][korail_mobile_api.read_payloads.OriginalTicketReference]가 아닌 원소가 있을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 확인됨 |

**예제**

```python
# references: 전달한 승차권들의 OriginalTicketReference 목록 (sale_date는 YYYYMMDD)
spec = client.get_pbp_acceptance_specifications(references)
for ticket in spec.tickets:
    for journey in ticket.journeys:
        seats = [(seat.car_no, seat.seat_no) for seat in journey.seats]
        print(ticket.pnr_no, journey.acceptance_customer_name, seats)
```

## `retrieve_delivered_ticket`

다른 회원에게 전달한 승차권을 회수합니다.

```python
KorailClient.retrieve_delivered_ticket(
    ticket: PbpAcceptanceTicket,
) -> DeliveredTicketRetrievalResponse
```

[`get_pbp_acceptance_specifications`](#get_pbp_acceptance_specifications)가 반환한 승차권 한 장을 받아, 첫 여정의 대리수령 예약 번호(`pbp_reservation_no`)와 승차권의 PNR을 한 쌍으로 보냅니다.
여정이 여러 개여도 첫 여정의 값만 씁니다. 라이브러리는 여정의 `withdrawal_possible_flag`를 검사하지 않습니다.
실패해도 자동으로 다시 보내지 않습니다. 실서버에서 확인하지 못한 메서드입니다.

앱은 첫 여정의 `pbp_reservation_no`가 같은 승차권들을 한 묶음으로 보고, 묶음마다 그 번호와 묶음 첫 승차권의 PNR로 한 번만 요청합니다.
앱과 같게 보내려면 같은 `pbp_reservation_no`를 가진 승차권 중 [`get_pbp_acceptance_specifications`](#get_pbp_acceptance_specifications) 결과에서 처음 나온 한 장으로 한 번만 호출하세요.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `ticket` | [`PbpAcceptanceTicket`][korail_mobile_api.read_models.PbpAcceptanceTicket] | 필수 | 회수할 승차권입니다. [`get_pbp_acceptance_specifications`](#get_pbp_acceptance_specifications) 결과의 `tickets` 원소를 넘깁니다. |

**반환값**

[`DeliveredTicketRetrievalResponse`][korail_mobile_api.mutation_models.DeliveredTicketRetrievalResponse] — `process_flags`에 응답의 처리 결과 행(`prsList`)마다 처리 표시값(`prsFlg`)이 문자열로 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `ticket`이 [`PbpAcceptanceTicket`][korail_mobile_api.read_models.PbpAcceptanceTicket]이 아닐 때, `journeys`가 비었을 때, 첫 여정의 `pbp_reservation_no`나 승차권의 `pnr_no`가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미확인 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 다른 회원에게 전달한 승차권이 실제로 회수됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
spec = client.get_pbp_acceptance_specifications(references)
ticket = spec.tickets[0]
result = client.retrieve_delivered_ticket(ticket)
print(result.str_result, result.process_flags)
```

## `get_self_checkin_info`

셀프 체크인으로 등록한 자유석 좌석 정보를 조회합니다.

```python
KorailClient.get_self_checkin_info(
    detail: RefundTicketDetailResponse,
) -> SelfCheckInInfoResponse
```

`detail`은 [`get_refund_ticket_detail`](payments.md#get_refund_ticket_detail)의 결과입니다. 판매일로는 상세의 `sale_date`를 보냅니다. 보내는 필드는 이 페이지 개요의 표를 참고하세요.
실서버에서는 오류 응답까지만 확인했습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail` | [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse] | 필수 | 체크인한 승차권의 상세입니다. |

**반환값**

[`SelfCheckInInfoResponse`][korail_mobile_api.read_models.SelfCheckInInfoResponse] — PNR, 열차 번호·종류, 출발·도착역 이름과 시각, 호차·좌석 번호, 체크인 구분 코드(`checkin_division_code`)입니다.
응답에는 열 개의 키가 모두 있어야 하며, 키가 없으면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다. 값이 `null`인 필드는 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `detail`이 [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse]가 아닐 때, `original_window_no`·`sale_date`·`original_sale_sequence`·`original_return_password` 중 하나가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 서버 응답만 확인 |

**예제**

```python
# reference: 체크인한 승차권의 OriginalTicketReference (sale_date는 return_sale_date, MMDD)
detail = client.get_refund_ticket_detail(reference)
info = client.get_self_checkin_info(detail)
print(info.train_no, info.car_no, info.seat_no)
```

## `check_self_checkin_seat`

좌석의 QR 코드를 스캔한 문자열로 셀프 체크인할 수 있는 좌석을 확인합니다.

```python
KorailClient.check_self_checkin_seat(
    detail: RefundTicketDetailResponse,
    qr_code: str,
) -> SelfCheckInSeatCheckResponse
```

자유석에 앉은 뒤 좌석에 붙은 QR 코드를 스캔한 문자열을 `qr_code`로 넘깁니다. 승차권 상세의 `qr_code`(승차권 자체의 QR 코드)가 아닙니다.
판매일로는 상세의 `original_sale_date`를 보냅니다. 서버 상태를 바꾸지 않는 조회입니다. 실서버에서 확인하지 못한 메서드입니다.

결과의 `seats`가 비어 있으면 등록할 좌석이 없는 것입니다. 앱은 첫 행을 등록에 사용합니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail` | [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse] | 필수 | 체크인할 승차권의 상세입니다. |
| `qr_code` | `str` | 필수 | 좌석 QR 코드를 스캔한 문자열입니다. |

**반환값**

[`SelfCheckInSeatCheckResponse`][korail_mobile_api.read_models.SelfCheckInSeatCheckResponse] — `seats`에 체크인할 수 있는 좌석이 [`SelfCheckInSeat`][korail_mobile_api.read_models.SelfCheckInSeat] 목록으로 들어 있습니다.
각 행에는 PNR, 여정·배정 순번, 운행일, 열차 번호, 출발·도착역 코드와 순서, 호차·좌석 번호, `cps_no` 등 16개 값이 있으며 모두 필수입니다. 응답의 목록(`consList`)이 `null`이면 빈 튜플입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `qr_code`가 비었을 때, `detail`이 [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse]가 아닐 때, `original_window_no`·`original_sale_date`·`original_sale_sequence`·`original_return_password` 중 하나가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 아니요 | 미확인 |

**예제**

```python
detail = client.get_refund_ticket_detail(reference)
qr_code = input("좌석 QR 문자열: ")
check = client.check_self_checkin_seat(detail, qr_code)
for seat in check.seats:
    print(seat.car_no, seat.seat_no)
```

## `register_self_checkin`

[`check_self_checkin_seat`](#check_self_checkin_seat)로 확인한 좌석으로 셀프 체크인을 등록합니다.

```python
KorailClient.register_self_checkin(
    detail: RefundTicketDetailResponse,
    seat: SelfCheckInSeat,
) -> SelfCheckInRegisterResponse
```

좌석 행에서는 `cps_no`, `car_no`, `seat_no`를 보내고, 나머지는 좌석 확인과 같은 상세 필드를 보냅니다. 여정 순번도 좌석 행이 아니라 상세의 값을 씁니다.
좌석 확인에 쓴 것과 같은 `detail`을 넘기세요. 실패해도 자동으로 다시 보내지 않습니다. 실서버에서 확인하지 못한 메서드입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail` | [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse] | 필수 | 체크인할 승차권의 상세입니다. |
| `seat` | [`SelfCheckInSeat`][korail_mobile_api.read_models.SelfCheckInSeat] | 필수 | 등록할 좌석입니다. [`check_self_checkin_seat`](#check_self_checkin_seat) 결과의 `seats` 원소를 넘깁니다. |

**반환값**

[`SelfCheckInRegisterResponse`][korail_mobile_api.mutation_models.SelfCheckInRegisterResponse] — 봉투와 `message_id`(`msgId`)입니다. 응답에 `msgId` 키가 없으면 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생하고, 값이 `null`이면 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `seat`이 [`SelfCheckInSeat`][korail_mobile_api.read_models.SelfCheckInSeat]이 아니거나 `cps_no`·`car_no`·`seat_no` 중 하나가 비었을 때, `detail`이 [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse]가 아니거나 좌석 확인에 쓰는 상세 필드가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미확인 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 셀프 체크인이 실제로 등록됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
check = client.check_self_checkin_seat(detail, qr_code)
if check.seats:
    result = client.register_self_checkin(detail, check.seats[0])
    print(result.str_result, result.h_msg_txt)
```

## `cancel_self_checkin`

등록한 셀프 체크인을 취소합니다.

```python
KorailClient.cancel_self_checkin(
    detail: RefundTicketDetailResponse,
) -> SelfCheckInCancelResponse
```

[`get_self_checkin_info`](#get_self_checkin_info)와 같은 상세 필드를 보냅니다. 판매일로는 상세의 `sale_date`를 보냅니다.
실패해도 자동으로 다시 보내지 않습니다. 실서버에서 확인하지 못한 메서드입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `detail` | [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse] | 필수 | 체크인을 취소할 승차권의 상세입니다. |

**반환값**

[`SelfCheckInCancelResponse`][korail_mobile_api.mutation_models.SelfCheckInCancelResponse] — 봉투와 `message_id`(`msgId`)입니다. 응답에 `msgId`가 없으면 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인하지 않았을 때 |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `detail`이 [`RefundTicketDetailResponse`][korail_mobile_api.read_models.RefundTicketDetailResponse]가 아닐 때, `original_window_no`·`sale_date`·`original_sale_sequence`·`original_return_password` 중 하나가 비었을 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 | - | 예 | 미확인 |

!!! warning "실제로 처리됩니다"
    이 메서드를 호출하면 등록된 셀프 체크인이 실제로 취소됩니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

**예제**

```python
detail = client.get_refund_ticket_detail(reference)
result = client.cancel_self_checkin(detail)
print(result.str_result, result.h_msg_txt)
```
