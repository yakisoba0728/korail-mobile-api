# 오류 처리

이 가이드는 라이브러리가 발생시키는 예외의 계층과 예외에 담긴 정보, 결과 코드와 예외의 대응을 설명합니다.
이어서 세션 만료, 상태 변경 요청의 실패, 카드 결제 거절, 웹 단계가 필요한 로그인을 처리하는 방법을 예제로 보여 줍니다.
라이브러리는 KORAIL API 요청을 자동으로 다시 보내지 않으며, 자동으로 다시 로그인하지도 않습니다.

## 예외 계층

요청을 처리하면서 라이브러리가 발생시키는 예외는 모두 [`KorailApiError`][korail_mobile_api.errors.KorailApiError]를 상속합니다. 모든 예외는 패키지 루트에서 가져올 수 있습니다.

```text
Exception
└── KorailApiError
    ├── KorailTransportError
    ├── KorailProtocolError
    ├── KorailAuthError
    │   ├── KorailSessionExpiredError
    │   └── KorailAuthContinuationRequired
    ├── KorailDynaPathError
    ├── KorailDynaPathRequiredError
    ├── KorailAppError
    │   ├── KorailNoResultsError
    │   │   └── KorailNoDirectTrainError
    │   ├── KorailSoldOutError
    │   ├── KorailSeatUnavailableError
    │   ├── KorailReservationRefusedError
    │   ├── KorailInvalidRequestError
    │   ├── KorailNotEntitledError
    │   ├── KorailServiceUnavailableError
    │   └── KorailAppUpdateRequiredError
    └── KorailNetFunnelError
        └── KorailQueueRejectedError
```

| 예외 | 부모 | 발생 조건 |
|---|---|---|
| [`KorailApiError`][korail_mobile_api.errors.KorailApiError] | `Exception` | 모든 라이브러리 예외의 기반 클래스입니다. 이 클래스 자체를 발생시키지는 않습니다. |
| [`KorailTransportError`][korail_mobile_api.errors.KorailTransportError] | `KorailApiError` | 연결 실패나 시간 초과 같은 네트워크 오류가 났을 때, 서버가 2xx가 아닌 HTTP 상태로 응답했을 때(3xx 포함, 리다이렉트는 따라가지 않음) |
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `KorailApiError` | 요청 전 입력 검사에 실패했을 때, 응답이 JSON 객체가 아니거나 봉투 필드의 타입이 틀렸을 때, 필수 값이 없어 응답을 읽을 수 없을 때, 닫힌 클라이언트로 요청하려 할 때, DynaPath 토큰 함수가 예외를 발생시켰을 때 |
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | `KorailApiError` | 로그인에 실패했을 때, 로그인이 필요한 메서드를 로그인하지 않고 호출했을 때(요청을 보내지 않음), 고객번호가 필요한 메서드인데 세션에 고객번호가 없을 때 |
| [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError] | `KorailAuthError` | 서버가 결과 코드 `P058`로 세션 만료를 알려 왔을 때. 로컬 세션을 비웁니다. |
| [`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired] | `KorailAuthError` | 로그인 응답이 휴면 계정 해제나 비밀번호 변경 같은 웹 단계를 요구할 때(`WRC000116`, `WRC000420`) |
| [`KorailDynaPathError`][korail_mobile_api.errors.KorailDynaPathError] | `KorailApiError` | DynaPath 토큰을 붙이는 경로의 응답에서 차단 코드를 감지했을 때. HTTP 상태와 봉투보다 먼저 판정합니다. |
| [`KorailDynaPathRequiredError`][korail_mobile_api.errors.KorailDynaPathRequiredError] | `KorailApiError` | DynaPath를 끈 설정으로 로그인 요청을 보내려 할 때(요청을 보내지 않음) |
| [`KorailAppError`][korail_mobile_api.errors.KorailAppError] | `KorailApiError` | 서버가 실패로 응답했을 때. 결과 코드가 [결과 코드와 예외](#result-codes)의 표에 없으면 이 클래스 그대로 발생합니다. |
| [`KorailNoResultsError`][korail_mobile_api.errors.KorailNoResultsError] | `KorailAppError` | 조회 조건에 맞는 결과가 없을 때 |
| [`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError] | `KorailNoResultsError` | 직통 열차가 없을 때 |
| [`KorailSoldOutError`][korail_mobile_api.errors.KorailSoldOutError] | `KorailAppError` | 매진됐거나 남은 좌석이 없을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.errors.KorailSeatUnavailableError] | `KorailAppError` | 지정한 좌석을 이용할 수 없을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.errors.KorailReservationRefusedError] | `KorailAppError` | 중복 예약, 구매 한도, 예약 가능 시간 등의 이유로 예약을 거절했을 때 |
| [`KorailInvalidRequestError`][korail_mobile_api.errors.KorailInvalidRequestError] | `KorailAppError` | 서버가 입력값 검증에서 거절했을 때 |
| [`KorailNotEntitledError`][korail_mobile_api.errors.KorailNotEntitledError] | `KorailAppError` | 할인이나 상품을 이용할 자격이 없을 때 |
| [`KorailServiceUnavailableError`][korail_mobile_api.errors.KorailServiceUnavailableError] | `KorailAppError` | 서비스나 연결을 이용할 수 없다는 안내로 응답했을 때. 서버 장애만을 뜻하지는 않습니다. |
| [`KorailAppUpdateRequiredError`][korail_mobile_api.errors.KorailAppUpdateRequiredError] | `KorailAppError` | 앱 업데이트를 요구하는 응답일 때 |
| [`KorailNetFunnelError`][korail_mobile_api.errors.KorailNetFunnelError] | `KorailApiError` | 대기열을 통과하지 못했을 때. 이 예외가 나면 API 요청은 보내지 않은 것입니다. |
| [`KorailQueueRejectedError`][korail_mobile_api.errors.KorailQueueRejectedError] | `KorailNetFunnelError` | 대기열 서버가 요청을 차단했을 때(`301`, `302`) |

- 대기열 서버와의 네트워크 오류는 `KorailTransportError`로 나오지 않습니다. 관문에 따라 경고 로그를 남기고 건너뛰거나 `KorailNetFunnelError`로 바뀝니다. 자세한 규칙은 [설정](configuration.md#netfunnel)을 참고하세요.
- `KorailDynaPathError`는 차단 코드가 들어 있는 응답 필드를 확인하지 못해 응답 최상위의 정수 값을 모두 검사합니다. 따라서 다른 필드의 같은 값을 차단으로 판정할 수 있습니다.
- 설정 객체를 만들 때의 오류는 라이브러리 예외가 아닙니다. `KorailConfig`, `DynapathConfig`, `DynapathTokenSettings`는 `ValueError`를, `build_config_from_env`는 필수 환경변수가 없으면 `RuntimeError`를 발생시킵니다.

## 예외에 담긴 정보

모든 라이브러리 예외에는 아래 속성이 있습니다. 값이 없으면 `None`입니다.

| 속성 | 타입 | 뜻 |
|---|---|---|
| `code` | `str` \| `None` | 서버 결과 코드(`h_msg_cd`)입니다. 대기열 예외에서는 대기열 응답 코드(예: `"301"`)입니다. 서버 응답 없이 난 오류는 `None`입니다. |
| `message` | `str` \| `None` | 서버 결과 메시지(`h_msg_txt`)입니다. 대기열 예외에서는 라이브러리가 쓴 설명입니다. |
| `raw` | `object` \| `None` | 서버가 보낸 응답 원본입니다. JSON이면 읽은 값(보통 `dict`), JSON이 아니면 `bytes`, 대기열 응답이면 `str`입니다. |
| `parser_raw` | `object` \| `None` | 응답을 읽다가 멈췄을 때 파서가 보던 부분 원본입니다. 이때 `raw`에는 받은 응답 전체가 들어 있습니다. |

예외마다 채워지는 속성은 다음과 같습니다.

| 예외 | 채워지는 값 |
|---|---|
| `KorailAppError`와 하위 예외, `KorailSessionExpiredError` | `code`, `message`, `raw` |
| `KorailAuthError`(로그인 실패) | `code`, `raw`. 메시지는 `str(error)`에 있습니다. 로그인하지 않고 호출해 난 경우에는 모두 `None`입니다. |
| `KorailAuthContinuationRequired` | `code`, `raw`, `redirect_url`(서버가 준 웹 주소, 없으면 `""`) |
| `KorailTransportError` | HTTP 상태 오류이면 `raw`에 응답 본문. 네트워크 오류이면 원래의 `httpx` 예외가 `__cause__`에 들어 있습니다. |
| `KorailProtocolError` | 응답을 읽지 못했으면 `raw`. 파서가 읽다가 멈춘 부분이 있으면 `parser_raw`도 채웁니다. 요청 전 입력 검사에서 났으면 비어 있습니다. |
| `KorailDynaPathError` | `raw`(차단 코드가 든 응답) |
| `KorailNetFunnelError`, `KorailQueueRejectedError` | `message`는 항상 채웁니다. 대기열 응답으로 판정한 경우(차단, 입장 키 없음, 통과가 아닌 응답)에는 `code`(대기열 응답 코드)와 `raw`도 채웁니다. 대기열 서버 오류 때문에 요청을 보내지 않은 경우에는 `code`와 `raw`가 `None`이고 원래 예외가 `__cause__`에 들어 있습니다. 대기 시간 제한을 넘은 경우에는 마지막으로 읽은 대기열 응답의 값이 들어가며, 읽은 응답이 없으면 `None`입니다. |

```python
from korail_mobile_api import KorailApiError, KorailClient

client = KorailClient()
try:
    calendar = client.get_train_calendar()
except KorailApiError as error:
    print(type(error).__name__, error.code, error.message)
finally:
    client.close()
```

## 결과 코드와 예외 {#result-codes}

서버 응답의 `strResult`가 `FAIL`이면 실패로 판정합니다. 봉투가 반드시 있어야 하는 응답에서 `strResult`가 빠져도 실패로 봅니다.
실패 응답의 결과 코드가 `P058`이면 [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError]를 발생시키고, 그 밖에는 결과 코드로 [`KorailAppError`][korail_mobile_api.errors.KorailAppError]의 하위 예외를 고릅니다.

- 표의 결과 코드가 와도 `strResult`가 `SUCC`이면 예외가 아닙니다.
- 실패를 응답 모델로 돌려주는 메서드(예: [`pay_with_card`](../api/payments.md#pay_with_card))는 이 분류를 거치지 않습니다. 각 메서드 설명에 표시했습니다.
- 이 분류는 라이브러리가 정한 것입니다. 앱이 같은 코드에서 같은 화면을 보여 준다는 뜻은 아닙니다.

| 예외 | 결과 코드 |
|---|---|
| `KorailNoResultsError` | 21개 (예: `WRG000000`, `P100`, `P114`) |
| `KorailNoDirectTrainError` | `WRD000061` |
| `KorailSoldOutError` | 12개 (예: `ERR211161`, `WRT300001`) |
| `KorailSeatUnavailableError` | 7개 (예: `WRI411345`) |
| `KorailReservationRefusedError` | 31개 (예: `WRR800029`, `ERR911531`) |
| `KorailInvalidRequestError` | 87개 (예: `ERB000001`, `WRG200018`) |
| `KorailNotEntitledError` | 13개 (예: `ERR299943`, `WRC000419`) |
| `KorailServiceUnavailableError` | `SEMGTK` |
| `KorailAppUpdateRequiredError` | `SUPDATE` |
| `KorailAppError` | 위에 없는 모든 결과 코드 |

??? note "결과 코드 전체 목록"

    | 예외 | 결과 코드 |
    |---|---|
    | `KorailNoResultsError` | `ERR000100`, `IRR800002`, `IRT200279`, `IRZ000005`, `MRT200648`, `P100`, `P114`, `WRC000008`, `WRC000256`, `WRD000016`, `WRG000000`, `WRG500116`, `WRS600208`, `WRS600209`, `WRS600210`, `WRT100192`, `WRT200125`, `WRT300003`, `WRT300005`, `WRT800083`, `WRT800091` |
    | `KorailNoDirectTrainError` | `WRD000061` |
    | `KorailSoldOutError` | `EAZ000038`, `ERI411321`, `ERR211161`, `ERR800048`, `IRT010110`, `IRT010510`, `IRT011010`, `IRT011210`, `IRT011310`, `WRG500113`, `WRG500114`, `WRT300001` |
    | `KorailSeatUnavailableError` | `ERR521128`, `WRI411345`, `WRS200019`, `WRS600242`, `WRS800009`, `WRS900309`, `WRT800176` |
    | `KorailReservationRefusedError` | `ERR299920`, `ERR299922`, `ERR299932`, `ERR299933`, `ERR299934`, `ERR299935`, `ERR299936`, `ERR299937`, `ERR299939`, `ERR299941`, `ERR299992`, `ERR299993`, `ERR521143`, `ERR521158`, `ERR521185`, `ERR800052`, `ERR800056`, `ERR911051`, `ERR911081`, `ERR911421`, `ERR911501`, `ERR911528`, `ERR911531`, `S-ERR911411`, `S021`, `WRR664254`, `WRR664325`, `WRR700001`, `WRR800029`, `WRR800045`, `WRX000007` |
    | `KorailInvalidRequestError` | `ERB000001`, `ERR800001`, `ERR800002`, `ERR800003`, `ERR800004`, `ERR800005`, `ERR800006`, `ERR800008`, `ERR800009`, `ERR800010`, `ERR800011`, `ERR800012`, `ERR800014`, `ERR800015`, `ERR800016`, `ERR800017`, `ERR800018`, `ERR800019`, `ERR800020`, `ERR800021`, `ERR800022`, `ERR800023`, `ERR800024`, `ERR800025`, `ERR800026`, `ERR800029`, `ERR800030`, `ERR800031`, `ERR800033`, `ERR800034`, `ERR800035`, `ERR800036`, `ERR800037`, `ERR800038`, `ERR930224`, `ERR930226`, `ERR930227`, `ERR930228`, `ERR930250`, `ERR930260`, `ERR930261`, `ERR930267`, `ERR930268`, `ERR930278`, `ERR930279`, `ERR930280`, `ERR930292`, `ERR930293`, `ERR930310`, `ERR930312`, `ERR930328`, `ERR930329`, `WRC000063`, `WRC000210`, `WRC000260`, `WRC000370`, `WRC000392`, `WRC000436`, `WRG200001`, `WRG200002`, `WRG200003`, `WRG200004`, `WRG200005`, `WRG200006`, `WRG200007`, `WRG200008`, `WRG200009`, `WRG200010`, `WRG200011`, `WRG200012`, `WRG200013`, `WRG200014`, `WRG200015`, `WRG200016`, `WRG200017`, `WRG200018`, `WRG200019`, `WRG200020`, `WRR664227`, `WRT100002`, `WRT100124`, `WRT400191`, `WRT400235`, `WRT400356`, `WRT800053`, `WRT800074`, `WRT800075` |
    | `KorailNotEntitledError` | `ERR299943`, `ERR800049`, `MRR000008`, `MRT200005`, `WRC000107`, `WRC000302`, `WRC000373`, `WRC000412`, `WRC000419`, `WRC000446`, `WRC800030`, `WRR664211`, `WRR800058` |
    | `KorailServiceUnavailableError` | `SEMGTK` |
    | `KorailAppUpdateRequiredError` | `SUPDATE` |

하위 예외를 먼저 잡고 상위 예외를 나중에 잡습니다. `KorailNoDirectTrainError`는 `KorailNoResultsError`의 하위 예외이므로 먼저 잡아야 합니다.
직통 열차가 없을 때 환승 조회로 넘어가는 동작은 [`search_trains_with_transfer_fallback`](../api/trains.md#search_trains_with_transfer_fallback)이 대신 해 줍니다.

```python
from korail_mobile_api import (
    KorailAppError,
    KorailClient,
    KorailNoDirectTrainError,
    KorailNoResultsError,
    TrainSearchQuery,
)

client = KorailClient()
query = TrainSearchQuery(
    departure_station_code="서울",
    arrival_station_code="부산",
    departure_date="20261002",
    departure_time="090000",
    passengers=1,
)
try:
    result = client.search_trains(query)
except KorailNoDirectTrainError:
    transfers = client.search_transfer_trains(query)
except KorailNoResultsError:
    print("조건에 맞는 열차가 없습니다.")
except KorailAppError as error:
    print("조회 실패:", error.code, error.message)
finally:
    client.close()
```

## 세션이 만료됐을 때 {#session-expired}

로그인 후 서버 세션이 끝나면 다음 요청에서 [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError]가 발생합니다.
이때 라이브러리는 로컬 세션과 쿠키를 비우지만, 다시 로그인하거나 요청을 다시 보내지는 않습니다.

- `KorailSessionExpiredError`는 `KorailAuthError`의 하위 예외입니다. 둘을 따로 처리하려면 `KorailSessionExpiredError`를 먼저 잡으세요.
- 조회 메서드는 다시 로그인한 뒤 다시 호출하면 됩니다.
- 상태 변경 메서드는 다시 호출하기 전에 [결과를 확인](#mutations)하세요.
- 다시 로그인이 `KorailAuthError`로 실패하면 반복해서 재시도하지 마세요. 비밀번호 오류가 누적되면 계정이 잠길 수 있습니다(예: 결과 코드 `WRC000390`).

아래 예제는 로그인한 클라이언트와 조회 조건을 만들고, 조회 메서드에만 쓰는 다시 로그인 함수를 정의합니다. 이 가이드의 나머지 예제는 여기서 만든 `client`, `query`를 이어 씁니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient, KorailSessionExpiredError, TrainSearchQuery

member_no = input("회원번호·전화번호·이메일: ")
password = getpass("비밀번호: ")

client = KorailClient()
client.login(member_no, password)
query = TrainSearchQuery(
    departure_station_code="서울",
    arrival_station_code="부산",
    departure_date="20261002",
    departure_time="090000",
    passengers=1,
)


def read_with_relogin(read):
    """조회 메서드에만 씁니다. 세션이 만료됐으면 한 번 다시 로그인하고 다시 조회합니다."""
    try:
        return read()
    except KorailSessionExpiredError:
        client.login(member_no, password)
        return read()


tickets = read_with_relogin(client.get_ticket_list)
```

다 쓴 클라이언트는 `client.logout()`과 `client.close()`로 정리합니다.

## 상태 변경 요청이 실패했을 때 {#mutations}

예약, 결제, 환불처럼 서버의 상태를 바꾸는 메서드는 API 레퍼런스의 정보 표에 "상태 변경: 예"로 표시돼 있습니다.
라이브러리는 이런 요청을 자동으로 다시 보내지 않습니다. 응답을 읽지 못했어도 서버에서는 이미 처리됐을 수 있기 때문입니다.
예외 종류에 따라 요청이 서버에 닿았는지가 다릅니다.

| 예외 | 요청 | 할 일 |
|---|---|---|
| `KorailNetFunnelError`, `KorailQueueRejectedError` | 보내지 않았습니다. | 대기열 상황을 보고 다시 호출할지 정합니다. |
| `KorailProtocolError`(요청 전 입력 검사) | 보내지 않았습니다. | 입력을 고친 뒤 호출합니다. |
| `KorailAuthError`(로그인하지 않음) | 보내지 않았습니다. | 로그인한 뒤 호출합니다. |
| `KorailProtocolError`(응답을 읽지 못함) | 보냈고 응답을 받았습니다. | 서버에서 처리됐을 수 있습니다. `raw`와 예약 내역으로 결과를 확인합니다. |
| `KorailDynaPathError` | 보냈고 차단 코드가 든 응답을 받았습니다. | 서버에서 처리됐는지 알 수 없으므로 예약 내역으로 결과를 확인합니다. |
| `KorailTransportError` | 서버에 닿았는지 알 수 없습니다. | 예약 내역이나 승차권 목록으로 결과를 확인합니다. |
| `KorailAppError`와 하위 예외 | 보냈고 서버가 실패로 응답했습니다. | `code`와 `message`로 사유를 확인합니다. |
| `KorailSessionExpiredError` | 보냈고 서버가 세션 만료로 응답했습니다. | 다시 로그인한 뒤 결과를 확인하고 다시 호출할지 정합니다. |

결과는 결제 전 홀드라면 [`get_reservation_history`](../api/reservations.md#get_reservation_history), 발권된 승차권이라면 [`get_ticket_list`](../api/account.md#get_ticket_list)로 확인합니다.
아래 예제는 예약 전에 살아 있는 홀드의 PNR을 기록해 두고, 예약이 불확실하게 끝나면 새 PNR이 생겼는지 비교합니다. 요청 전 입력 검사에서 난 `KorailProtocolError`는 `raw`가 `None`이므로 구분할 수 있습니다.

!!! warning "실제로 처리됩니다"
    이 예제의 `reserve()`는 실제로 좌석을 점유하는 홀드를 만듭니다. 결제하지 않을 홀드는 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소하세요. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

```python
from korail_mobile_api import KorailProtocolError, KorailTransportError


def held_pnrs():
    history = client.get_reservation_history()
    return {row.pnr_no for row in history.trains if row.pnr_no}


train = next(t for t in client.search_trains(query).trains if t.general_reservation_code == "11")
before = held_pnrs()
try:
    hold = client.reserve(train)
except (KorailTransportError, KorailProtocolError) as error:
    if isinstance(error, KorailProtocolError) and error.raw is None:
        raise  # 요청 전 입력 검사에서 거절돼 요청을 보내지 않았습니다.
    created = held_pnrs() - before
    if created:
        print("홀드가 만들어졌습니다. 다시 예약하지 마세요:", sorted(created))
    else:
        print("새 홀드가 보이지 않습니다. 확인한 뒤 다시 예약할지 정하세요.")
    raise
```

## 카드 결제가 거절됐을 때 {#card-decline}

[`pay_with_card`](../api/payments.md#pay_with_card)는 카드 거절 같은 실패 응답에서 예외를 발생시키지 않고 [`ReservationPaymentResponse`][korail_mobile_api.mutation_models.ReservationPaymentResponse]를 반환합니다.
거절이면 `str_result`가 `"FAIL"`이고, 응답에 `strResult`가 없으면 `None`입니다. 사유는 `h_msg_cd`와 `h_msg_txt`에 있습니다.
`str_result`가 `"SUCC"`일 때만 결제 완료로 처리하세요.

다음 경우에는 여전히 예외가 발생합니다.

- 요청 전 검사: 예약대기 홀드, 결제 금액이 0원인 홀드, 형식이 맞지 않는 카드 입력은 요청을 보내기 전에 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]로 거절합니다.
- 대기열: `pay` 관문을 통과하지 못하면 `KorailNetFunnelError`가 발생하고 결제 요청은 보내지 않습니다.
- 세션 만료(`P058`), 네트워크 오류, 읽을 수 없는 응답은 다른 메서드와 같이 예외가 발생합니다. 이때는 다시 결제하기 전에 [결과를 확인](#mutations)하세요.

!!! warning "실제로 처리됩니다"
    이 예제는 실제로 카드 결제를 요청합니다. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

```python
from getpass import getpass

from korail_mobile_api import CardPayment

card = CardPayment(
    card_number=getpass("카드 번호(숫자만): "),
    card_password=getpass("카드 비밀번호 앞 두 자리: "),
    card_expire=input("유효기간(YYMM): "),
    birthday=getpass("생년월일 6자리: "),
)
payment = client.pay_with_card(hold, card)
if payment.str_result != "SUCC":
    print("결제가 완료되지 않았습니다:", payment.str_result, payment.h_msg_cd, payment.h_msg_txt)
```

## 웹 단계가 필요한 로그인 {#auth-continuation}

휴면 계정 해제나 비밀번호 변경처럼 웹 화면에서 처리해야 하면 [`login`](../api/session.md#login)이 [`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired]를 발생시킵니다.
`redirect_url`에 서버가 알려 준 주소가, `code`에 결과 코드가 들어 있습니다. 라이브러리는 이 단계를 진행하지 않으며 로그인된 상태로 만들지도 않습니다.
앱이나 웹에서 조치를 마친 뒤 다시 로그인하세요.

```python
from getpass import getpass

from korail_mobile_api import KorailAuthContinuationRequired, KorailClient

client = KorailClient()
try:
    client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
except KorailAuthContinuationRequired as error:
    print("웹에서 먼저 처리해야 합니다:", error.code, error.redirect_url)
finally:
    client.close()
```

## 개인정보 주의 {#personal-data}

!!! danger "원본과 모델은 마스킹하지 않습니다"
    응답 모델과 예외의 `raw`에는 서버가 보낸 응답이 가공 없이 들어 있습니다. 이름, 전화번호, 고객번호, 예약 번호, 결제 정보 같은 개인정보가 포함될 수 있습니다.
    응답 모델을 `print`하거나 로그에 남기면 `raw`를 포함한 모든 필드가 그대로 출력됩니다. [`KorailSession`][korail_mobile_api.models.KorailSession]에는 세션 쿠키 값과 로그인 ID도 들어 있습니다.
    모델이 바꿀 수 없는(frozen) dataclass여도 `raw` 안의 사전과 목록은 복사하거나 고정하지 않습니다.
    오류를 기록할 때는 예외의 클래스 이름과 `code`처럼 필요한 값만 남기고, `raw`와 모델 전체를 로그나 오류 보고에 넣지 마세요.
