# 오류 처리

이 가이드는 라이브러리가 발생시키는 예외의 계층과 예외에 담긴 정보, 결과 코드와 예외의 대응을 설명합니다.
이어서 세션 만료, 상태 변경 요청의 실패, 카드 결제 거절, 웹 단계가 필요한 로그인을 처리하는 방법을 예제로 보여 줍니다.
라이브러리는 KORAIL API 요청을 자동으로 다시 보내지 않으며, 자동으로 다시 로그인하지도 않습니다.

## 예외 계층

요청을 처리하면서 라이브러리가 발생시키는 예외는 모두 [`KorailApiError`][korail_mobile_api.KorailApiError]를 상속합니다. 모든 예외는 패키지 루트에서 가져올 수 있습니다.

```text
Exception
└── KorailApiError
    ├── KorailTransportError
    ├── KorailProtocolError
    │   └── KorailInvalidInputError (ValueError 도 상속)
    ├── KorailAuthError
    │   ├── KorailSessionExpiredError
    │   ├── KorailAccountLockedError
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
    │   ├── KorailRateLimitError
    │   ├── KorailProcessingError
    │   ├── KorailAlreadyProcessedError
    │   └── KorailAppUpdateRequiredError
    └── KorailNetFunnelError
        └── KorailQueueRejectedError
```

| 예외 | 부모 | 발생 조건 |
|---|---|---|
| [`KorailApiError`][korail_mobile_api.KorailApiError] | `Exception` | 모든 라이브러리 예외의 기반 클래스입니다. 이 클래스 자체를 발생시키지는 않습니다. |
| [`KorailTransportError`][korail_mobile_api.KorailTransportError] | `KorailApiError` | 연결 실패나 시간 초과 같은 네트워크 오류가 났을 때, 서버가 2xx가 아닌 HTTP 상태로 응답했을 때(3xx 포함, 리다이렉트는 따라가지 않음) |
| [`KorailProtocolError`][korail_mobile_api.KorailProtocolError] | `KorailApiError` | 요청 전 입력 검사에 실패했을 때, 응답이 JSON 객체가 아니거나 봉투 필드의 타입이 틀렸을 때, 필수 값이 없어 응답을 읽을 수 없을 때, 닫힌 클라이언트로 요청하려 할 때, DynaPath 토큰 함수가 예외를 발생시키거나 문자열이 아니거나 ASCII가 아닌 값을 돌려줬을 때 |
| [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError] | `KorailProtocolError`, `ValueError` | 요청 전 입력 검사에 실패했을 때(입력 모델 생성, 폼 구성, 간편 API 인자). 요청을 보내지 않습니다. |
| [`KorailAuthError`][korail_mobile_api.KorailAuthError] | `KorailApiError` | 로그인에 실패했을 때, 로그인이 필요한 메서드를 로그인하지 않고 호출했을 때(요청을 보내지 않음), 고객번호가 필요한 메서드인데 세션에 고객번호가 없을 때 |
| [`KorailSessionExpiredError`][korail_mobile_api.KorailSessionExpiredError] | `KorailAuthError` | 서버가 결과 코드 `P058`로 세션 만료를 알려 왔을 때. 로컬 세션을 비웁니다. |
| [`KorailAccountLockedError`][korail_mobile_api.KorailAccountLockedError] | `KorailAuthError` | 로그인 응답이 비밀번호 오류 허용 횟수 초과(`WRC000390`)를 알렸을 때. 로그인을 반복하지 말고 계정 상태를 확인하세요. |
| [`KorailAuthContinuationRequired`][korail_mobile_api.KorailAuthContinuationRequired] | `KorailAuthError` | 로그인 응답이 휴면 계정 해제나 비밀번호 변경 같은 웹 단계를 요구할 때(`WRC000116`, `WRC000420`) |
| [`KorailDynaPathError`][korail_mobile_api.KorailDynaPathError] | `KorailApiError` | DynaPath 토큰을 붙이는 경로의 응답에서 차단 코드를 감지했을 때. HTTP 상태와 봉투보다 먼저 판정합니다. |
| [`KorailDynaPathRequiredError`][korail_mobile_api.KorailDynaPathRequiredError] | `KorailApiError` | DynaPath를 끈 설정으로 로그인 요청을 보내려 할 때(요청을 보내지 않음) |
| [`KorailAppError`][korail_mobile_api.KorailAppError] | `KorailApiError` | 서버가 실패로 응답했을 때. 결과 코드가 [결과 코드와 예외](#result-codes)의 표에 없으면 이 클래스 그대로 발생합니다. |
| [`KorailNoResultsError`][korail_mobile_api.KorailNoResultsError] | `KorailAppError` | 조회 조건에 맞는 결과가 없을 때 |
| [`KorailNoDirectTrainError`][korail_mobile_api.KorailNoDirectTrainError] | `KorailNoResultsError` | 직통 열차가 없을 때 |
| [`KorailSoldOutError`][korail_mobile_api.KorailSoldOutError] | `KorailAppError` | 매진됐거나 남은 좌석이 없을 때 |
| [`KorailSeatUnavailableError`][korail_mobile_api.KorailSeatUnavailableError] | `KorailAppError` | 지정한 좌석을 이용할 수 없을 때 |
| [`KorailReservationRefusedError`][korail_mobile_api.KorailReservationRefusedError] | `KorailAppError` | 중복 예약, 구매 한도, 예약 가능 시간, 지원하지 않는 할인 등의 이유로 예약을 거절했을 때 |
| [`KorailInvalidRequestError`][korail_mobile_api.KorailInvalidRequestError] | `KorailAppError` | 서버가 입력값 검증에서 거절했을 때 |
| [`KorailNotEntitledError`][korail_mobile_api.KorailNotEntitledError] | `KorailAppError` | 할인이나 상품을 이용할 자격이 없을 때 |
| [`KorailServiceUnavailableError`][korail_mobile_api.KorailServiceUnavailableError] | `KorailAppError` | 서비스나 연결을 이용할 수 없다는 안내로 응답했을 때. 서버 장애만을 뜻하지는 않습니다. |
| [`KorailRateLimitError`][korail_mobile_api.KorailRateLimitError] | `KorailAppError` | 요청 횟수 초과·반복 호출 차단 안내(`BT019`, `BT023`). 해제 시각이나 재시도 간격은 알 수 없습니다. |
| [`KorailProcessingError`][korail_mobile_api.KorailProcessingError] | `KorailAppError` | 요청이 처리 중이거나 이미 완료됐을 수 있다는 안내(`WRT900900`). 예약·승차권 목록을 먼저 확인하세요. |
| [`KorailAlreadyProcessedError`][korail_mobile_api.KorailAlreadyProcessedError] | `KorailAppError` | 이미 반환된 승차권(`EZZ000014`)·취소된 예약(`EVZ000102`). 현재 요청을 성공으로 바꾸지는 않습니다. |
| [`KorailAppUpdateRequiredError`][korail_mobile_api.KorailAppUpdateRequiredError] | `KorailAppError` | 앱 업데이트를 요구하는 응답일 때(`SUPDATE`, 서버 코드 [`-8204`](#app-update)) |
| [`KorailNetFunnelError`][korail_mobile_api.KorailNetFunnelError] | `KorailApiError` | 대기열을 통과하지 못했을 때. 이 예외가 나면 API 요청은 보내지 않은 것입니다. |
| [`KorailQueueRejectedError`][korail_mobile_api.KorailQueueRejectedError] | `KorailNetFunnelError` | 대기열 서버가 요청을 차단했을 때(`301`, `302`) |

- 대기열 서버와의 네트워크 오류는 `KorailTransportError`로 나오지 않습니다. 관문에 따라 경고 로그를 남기고 건너뛰거나 `KorailNetFunnelError`로 바뀝니다. 자세한 규칙은 [설정](configuration.md#netfunnel)을 참고하세요.
  다만 httpx가 해석하지 못하는 대기열 주소는 `httpx.InvalidURL`을 그대로 전파하지 않고 `KorailTransportError`입니다.
- 숫자 입력의 비ASCII 숫자(`²`, `١`, 전각 `１` 등)와 값이 `None`인 요청 필드는 빈 값(`key=`)으로 보내지 않고 요청 전에 `KorailProtocolError`로 거절합니다. 빈 문자열 `""`은 생략합니다.
- `KorailDynaPathError`는 차단 코드가 들어 있는 응답 필드를 확인하지 못해 응답 최상위의 정수 값을 모두 검사합니다. 따라서 다른 필드의 같은 값을 차단으로 판정할 수 있습니다.
- 로그인에서 `KorailDynaPathError`(HTTP `403`, 차단 코드 `-2000`·`-8202` 등)가 나면 요청이 나간 네트워크의 IP 대역이 원인일 수 있습니다. KORAIL은 데이터센터·VPN 대역에서 오는 요청을 막으며, 이때 "VPN 또는 데이터센터를 통해서는 서비스를 이용할 수 없습니다"나 "매크로 등 미허가 도구 사용 시 이용이 제한될 수 있습니다" 같은 안내가 `str(error)`와 `raw`에 담겨 옵니다. 클라우드 서버(Oracle Cloud, Vercel 등)에서 막히고 같은 코드와 설정이 가정용 네트워크에서는 정상 로그인된 사례가 보고됐습니다.
  요청 형식을 바꿔서 해결되는 문제가 아니며, 요청이 나가는 네트워크가 달라져야 합니다. KORAIL 요청만 본인이 관리하는 다른 네트워크로 보내려면 [`proxy`](configuration.md#proxy) 설정을 쓰세요. 프록시도 데이터센터·VPN 대역에 있으면 같은 이유로 막힐 수 있습니다.
- 프록시에 연결하지 못하면 API 요청은 `KorailTransportError`로 끝납니다. 대기열 요청의 실패는 관문 규칙을 따릅니다([설정](configuration.md#netfunnel)).
- 설정 객체를 만들 때의 오류는 라이브러리 예외가 아닙니다. `KorailConfig`, `DynapathConfig`, `DynapathTokenSettings`는 `ValueError`를, `build_config_from_env`는 필수 환경변수가 없으면 `RuntimeError`를 발생시킵니다. 클라이언트를 만들 때 `proxy`와 `transport`를 함께 넘기면 `ValueError`, SOCKS 프록시에 필요한 패키지가 없으면 `ImportError`가 발생합니다.

## 예외에 담긴 정보

모든 라이브러리 예외에는 아래 속성이 있습니다. 값이 없으면 `None`입니다.

| 속성 | 타입 | 뜻 |
|---|---|---|
| `code` | `str` \| `None` | 서버 결과 코드(`h_msg_cd`)입니다. 대기열 예외에서는 대기열 응답 코드(예: `"301"`)입니다. 서버 응답 없이 난 오류는 `None`입니다. |
| `message` | `str` \| `None` | 서버 결과 메시지(`h_msg_txt`)입니다. 대기열 예외에서는 라이브러리가 쓴 설명입니다. |
| `display_message` | `str` \| `None` | 읽을 서버 메시지를 우선하고, 비어 있으면 앱 사전의 한국어 안내를 표시합니다. 태그·스크립트·스타일은 제외하고 줄바꿈 태그는 개행으로 바꿉니다. 원문은 보존합니다. |
| `raw` | `object` \| `None` | 서버가 보낸 응답 원문입니다. JSON이면 읽은 값(보통 `dict`), JSON이 아니면 `bytes`, 대기열 응답이면 `str`입니다. |
| `parser_raw` | `object` \| `None` | 응답을 읽다가 멈췄을 때 파서가 보던 부분 원문입니다. 이때 `raw`에는 받은 응답 전체가 들어 있습니다. |
| `request_sent` | `bool` \| `None` | HTTP 전송 계층에 넘긴 뒤 전송·응답 해석에 실패하면 `True`입니다. 서버 처리 성공을 뜻하지 않으며, `None`만으로 미전송을 단정할 수는 없습니다. |

`raw`는 복구 자료이지 전송 여부 표식이 아닙니다. 예를 들어 HTTP 200으로 JSON `null`을 받으면 `raw=None`이면서 `request_sent=True`일 수 있습니다.
입력 거절인 `KorailInvalidInputError`는 요청 전 오류이며 `request_sent=None`입니다. 반면 정상적으로 받은 서버 실패 예외도 이 속성이 `None`일 수 있으므로 예외 종류와 함께 확인하세요.
페이지·쪽 크기 등 정수 입력을 십진 문자열로 바꾸다가 Python의 변환 한도를 넘으면 `KorailInvalidInputError`이며 원래 `ValueError`를 `__cause__`에 보존합니다. 거대 숫자를 오류 메시지에 넣거나 전역 한도를 바꾸지 않으며, 새 페이지 범위 제한도 아닙니다. 이 거절은 HTTP·토큰 공급자·대기열 진입 전에 발생합니다.
`PaidTicket.from_refund_detail`와 `StationRefundExecutionRequest.from_verification`에 기대한 응답 모델이 아닌 값을 넘겨도 요청 전 `KorailInvalidInputError`입니다. 정상 모델의 subclass와 기존 필드·날짜·첫 원표 선택 규칙은 유지하며, 팩토리가 자동 조회·환불을 실행하지 않습니다.
typed 조회의 수신 후 도메인 파싱 실패도 `request_sent=True`이며 전체 `raw`·부분 `parser_raw`·원래 cause를 보존합니다. 순수 파서나 `from_raw()` 직접 호출에는 전송 표식을 붙이지 않습니다.

`display_message`·`resolve_error_message`는 HTML-safe 마크업이 아닌 일반 텍스트입니다. 텍스트 경로로 출력하고, HTML 문맥에서는 호출자가 이스케이프하세요. 비교식이나 문자 참조로 된 태그 모양도 텍스트로 남을 수 있습니다.

예외마다 채워지는 속성은 다음과 같습니다.

| 예외 | 채워지는 값 |
|---|---|
| `KorailAppError`와 하위 예외, `KorailSessionExpiredError`, `KorailAccountLockedError` | `code`, `message`, `raw` |
| `KorailAuthError`(로그인 실패) | `code`, `message`, `raw`. 기존 `str(error)`도 유지합니다. 로그인하지 않고 호출해 난 경우에는 모두 `None`입니다. |
| `KorailAuthContinuationRequired` | `code`, `message`, `raw`, `redirect_url`(서버가 준 웹 주소, 없으면 `""`) |
| `KorailTransportError` | HTTP 상태 오류이면 `raw`에 응답 본문. 네트워크 오류이면 원래의 `httpx` 예외가 `__cause__`에 들어 있습니다. 이 `httpx` 예외에 붙은 요청에는 메서드와 쿼리를 뺀 URL만 남고 본문·쿠키·DynaPath 토큰은 지웁니다. 예외의 종류와 객체는 그대로입니다. |
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
실패 응답의 결과 코드가 `P058`이면 [`KorailSessionExpiredError`][korail_mobile_api.KorailSessionExpiredError]를 발생시키고, 그 밖에는 결과 코드로 [`KorailAppError`][korail_mobile_api.KorailAppError]의 하위 예외를 고릅니다.

- 표의 결과 코드가 와도 `strResult`가 `SUCC`이면 예외가 아닙니다.
- 실패를 응답 모델로 돌려주는 메서드(예: [`pay_with_card`](../api/payments.md#pay_with_card))는 이 분류를 거치지 않습니다. 각 메서드 설명에 표시했습니다.
- 이 분류는 라이브러리가 정한 것입니다. 앱이 같은 코드에서 같은 화면을 보여 준다는 뜻은 아닙니다.

결과 없음도 메서드별 계약입니다. `list_reservations`의 `FAIL/P100`, `list_discount_coupons`·`get_pass_schedule`의 `FAIL/WRG000000`은 빈 응답 모델로 반환하되 실패 봉투와 원문을 보존합니다. 반면 `list_airport_bus_schedules`의 `FAIL/WRG000000`은 `KorailNoResultsError`입니다. 결과 코드만 보고 모든 조회를 같은 빈 목록으로 처리하지 마세요.

| 예외 | 결과 코드 |
|---|---|
| `KorailNoResultsError` | 21개 (예: `WRG000000`, `P100`, `P114`) |
| `KorailNoDirectTrainError` | `WRD000061` |
| `KorailSoldOutError` | 12개 (예: `ERR211161`, `WRT300001`) |
| `KorailSeatUnavailableError` | 7개 (예: `WRI411345`) |
| `KorailReservationRefusedError` | 32개 (예: `WRR800029`, `ERR911531`, `ERR299943`) |
| `KorailInvalidRequestError` | 87개 (예: `ERB000001`, `WRG200018`) |
| `KorailNotEntitledError` | 12개 (예: `WRC000419`, `WRC800030`) |
| `KorailServiceUnavailableError` | `S000`, `S001`, `S002`, `S003`, `SEMGTK` |
| `KorailRateLimitError` | `BT019`, `BT023` |
| `KorailProcessingError` | `WRT900900` |
| `KorailAlreadyProcessedError` | `EZZ000014`, `EVZ000102` |
| `KorailAppUpdateRequiredError` | `SUPDATE`; 서버 코드 [`-8204`](#app-update) |
| `KorailAppError` | 위에 없는 모든 결과 코드 |

`ERR299943`("예약할인이 지원되지 않습니다")는 열차·상품이 요청한 할인을 지원하지 않는 예약 제약으로,
`KorailReservationRefusedError`에 속합니다. 키즈카드 발급 대상이 아닌 `WRC000419`나
할인 대상 회원이 아닌 `WRC800030`은 `KorailNotEntitledError`로 유지합니다.
`teenager > 0`인 열차 예약은 서버로 보내기 전에 `KorailProtocolError`로 거절합니다.

`S000`·`S003`은 앱 7.0.8의 `NetworkConstants` 서비스 오류 목록과 `CommonOut.checkServiceError`에서 확인했습니다.
`FAIL` 기본값과 로그인 요구 코드 `P058`도 일반 오류 분기의 복원값과 일치합니다.
`S001`·`S002` 및 새 요청 제한·처리 중·기처리 예외는 앱 메시지에 근거한 라이브러리 정책입니다.
로그인의 `WRC000390`은 `KorailAccountLockedError`이며, 다른 요청에서는 일반 `KorailAppError`입니다.
`S035`·`P092`의 재로그인 안내를 조회할 수 있지만 그 코드나 메시지만으로 로컬 세션을 비우지는 않습니다.

??? note "결과 코드 전체 목록"

    | 예외 | 결과 코드 |
    |---|---|
    | `KorailNoResultsError` | `ERR000100`, `IRR800002`, `IRT200279`, `IRZ000005`, `MRT200648`, `P100`, `P114`, `WRC000008`, `WRC000256`, `WRD000016`, `WRG000000`, `WRG500116`, `WRS600208`, `WRS600209`, `WRS600210`, `WRT100192`, `WRT200125`, `WRT300003`, `WRT300005`, `WRT800083`, `WRT800091` |
    | `KorailNoDirectTrainError` | `WRD000061` |
    | `KorailSoldOutError` | `EAZ000038`, `ERI411321`, `ERR211161`, `ERR800048`, `IRT010110`, `IRT010510`, `IRT011010`, `IRT011210`, `IRT011310`, `WRG500113`, `WRG500114`, `WRT300001` |
    | `KorailSeatUnavailableError` | `ERR521128`, `WRI411345`, `WRS200019`, `WRS600242`, `WRS800009`, `WRS900309`, `WRT800176` |
    | `KorailReservationRefusedError` | `ERR299920`, `ERR299922`, `ERR299932`, `ERR299933`, `ERR299934`, `ERR299935`, `ERR299936`, `ERR299937`, `ERR299939`, `ERR299941`, `ERR299943`, `ERR299992`, `ERR299993`, `ERR521143`, `ERR521158`, `ERR521185`, `ERR800052`, `ERR800056`, `ERR911051`, `ERR911081`, `ERR911421`, `ERR911501`, `ERR911528`, `ERR911531`, `S-ERR911411`, `S021`, `WRR664254`, `WRR664325`, `WRR700001`, `WRR800029`, `WRR800045`, `WRX000007` |
    | `KorailInvalidRequestError` | `ERB000001`, `ERR800001`, `ERR800002`, `ERR800003`, `ERR800004`, `ERR800005`, `ERR800006`, `ERR800008`, `ERR800009`, `ERR800010`, `ERR800011`, `ERR800012`, `ERR800014`, `ERR800015`, `ERR800016`, `ERR800017`, `ERR800018`, `ERR800019`, `ERR800020`, `ERR800021`, `ERR800022`, `ERR800023`, `ERR800024`, `ERR800025`, `ERR800026`, `ERR800029`, `ERR800030`, `ERR800031`, `ERR800033`, `ERR800034`, `ERR800035`, `ERR800036`, `ERR800037`, `ERR800038`, `ERR930224`, `ERR930226`, `ERR930227`, `ERR930228`, `ERR930250`, `ERR930260`, `ERR930261`, `ERR930267`, `ERR930268`, `ERR930278`, `ERR930279`, `ERR930280`, `ERR930292`, `ERR930293`, `ERR930310`, `ERR930312`, `ERR930328`, `ERR930329`, `WRC000063`, `WRC000210`, `WRC000260`, `WRC000370`, `WRC000392`, `WRC000436`, `WRG200001`, `WRG200002`, `WRG200003`, `WRG200004`, `WRG200005`, `WRG200006`, `WRG200007`, `WRG200008`, `WRG200009`, `WRG200010`, `WRG200011`, `WRG200012`, `WRG200013`, `WRG200014`, `WRG200015`, `WRG200016`, `WRG200017`, `WRG200018`, `WRG200019`, `WRG200020`, `WRR664227`, `WRT100002`, `WRT100124`, `WRT400191`, `WRT400235`, `WRT400356`, `WRT800053`, `WRT800074`, `WRT800075` |
    | `KorailNotEntitledError` | `ERR800049`, `MRR000008`, `MRT200005`, `WRC000107`, `WRC000302`, `WRC000373`, `WRC000412`, `WRC000419`, `WRC000446`, `WRC800030`, `WRR664211`, `WRR800058` |
    | `KorailServiceUnavailableError` | `S000`, `S001`, `S002`, `S003`, `SEMGTK` |
    | `KorailRateLimitError` | `BT019`, `BT023` |
    | `KorailProcessingError` | `WRT900900` |
    | `KorailAlreadyProcessedError` | `EZZ000014`, `EVZ000102` |
    | `KorailAppUpdateRequiredError` | `SUPDATE`; 서버 코드 `-8204` |

### 앱 업데이트 요구(`-8204`) {#app-update}

서버가 실패 코드 `-8204`("원활한 예매 및 결제 서비스를 위해 최신 버전으로 업데이트해 주세요")로 응답하면 로그인과 실패를 예외로 분류하는 경로에서는 `KorailAppUpdateRequiredError`가 발생합니다.
`pay_with_card`와 `get_guide_seat_condition`처럼 실패 모델을 반환하는 경로는 `-8204`도 `h_msg_cd`에 남기므로 `str_result`와 함께 확인하세요. `logout`은 세션 만료 이외의 `FAIL`을 예외로 바꾸지 않습니다. 이 안내는 기존 정책을 설명하며 새 예외를 추가하지 않습니다.
`-8204`는 앱에서 확인한 리터럴이 아니라 [#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)에서 관측된 서버 코드이며, 서버 메시지는 예외에 그대로 남습니다.
네트워크 대역 차단(`-8202` 등, `KorailDynaPathError`)과 다른 응답이며, 프록시나 네트워크를 바꿔 해결된다는 근거는 없습니다.
요청 버전을 바꿔 시도하는 방법과 한계는 [요청 버전](configuration.md#request-version)에 있습니다. 이 예외도 자동 재시도하지 않습니다.

## 메시지 사전과 표시

현재 개발 사전은 앱 7.0.10의 일반 결과 코드 10,305개에 대한 메시지 17,256개를 포함합니다.
7.0.8 대비 `WRD000058` 한국어 안내만 1개월에서 2개월로 바뀌었고 영어는 그대로입니다.
이는 요청 기본 `AppVersion=7.0.8`·오류 분류·날짜 제한을 바꾸거나 7.0.10 실서버 호환을 보장하지 않습니다.
한국어·영어·일본어·중국어를 지원하고 번역이 없으면 한국어를 사용합니다.
성공·안내·과거 코드도 들어 있으므로 사전 조회 결과를 성공·실패 판정으로 사용하지 마세요.
앱 설정이나 임의 리소스 키는 포함하지 않습니다.

```python
from korail_mobile_api import get_error_message, resolve_error_message

print(get_error_message("BT019"))  # 요청횟수(6회)를 초과하였습니다.
print(get_error_message("S003", language="en"))  # API Error
print(resolve_error_message("S003", "서버 안내<br>잠시 후 확인"))
# 서버 안내
# 잠시 후 확인
```

`get_error_message`는 앱 사전의 원문을 반환합니다. `resolve_error_message`는 서버 메시지를 우선하고
읽을 메시지가 없을 때 사전을 사용하며, 표시할 일반 텍스트를 반환합니다.
HTML이나 치환 표시는 실행하지 않습니다. `P058` 사전 원문은 웹 이동 스크립트이므로 읽을 메시지가 없으면
SDK의 세션 만료 안내를 표시합니다. 이 표시는 세션 상태나 응답의 성공·실패를 바꾸지 않습니다.
지원 언어는 `ko`, `en`, `ja`/`jp`, `zh`/`cn`이며 `en-US` 같은 지역값도 받습니다.
지원하지 않는 언어는 `ValueError`, 알 수 없는 코드에 메시지도 없으면 `None`입니다.

예외와 `BaseKorailResponse`의 `display_message`는 한국어를 기본으로 사용합니다.
다른 언어는 `resolve_error_message(error.code, error.message, language="ja")`처럼 조회하세요.
응답 모델에서는 `code`·`message` 대신 `h_msg_cd`·`h_msg_txt`를 넘깁니다.
`message`, `h_msg_txt`, `raw`, 기존 예외 문자열은 그대로 보존하므로 카드 결제의 `FAIL` 모델에도 사용할 수 있습니다.

## 예외 처리 순서

하위 예외를 먼저 잡고 상위 예외를 나중에 잡습니다. `KorailNoDirectTrainError`는 `KorailNoResultsError`의 하위 예외이므로 먼저 잡아야 합니다.
직통 열차가 없을 때 환승 조회로 넘어가는 동작은 [`search_trains_with_transfer_fallback`](../api/trains.md#search_trains_with_transfer_fallback)이 대신 해 줍니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import (
    KorailAppError,
    KorailClient,
    KorailNoDirectTrainError,
    KorailNoResultsError,
    TrainSearchQuery,
)

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

client = KorailClient()
query = TrainSearchQuery(
    departure_station="서울",
    arrival_station="부산",
    departure_date=departure_date,
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

로그인 후 서버 세션이 끝나면 다음 요청에서 [`KorailSessionExpiredError`][korail_mobile_api.KorailSessionExpiredError]가 발생합니다.
이때 라이브러리는 로컬 세션과 쿠키를 비우지만, 다시 로그인하거나 요청을 다시 보내지는 않습니다.

- `KorailSessionExpiredError`는 `KorailAuthError`의 하위 예외입니다. 둘을 따로 처리하려면 `KorailSessionExpiredError`를 먼저 잡으세요.
- 조회 메서드는 다시 로그인한 뒤 다시 호출하면 됩니다.
- 상태 변경 메서드는 다시 호출하기 전에 [결과를 확인](#mutations)하세요.
- 다시 로그인이 `KorailAuthError`로 실패하면 반복해서 재시도하지 마세요. 비밀번호 오류가 누적되면 계정이 잠길 수 있습니다(예: 결과 코드 `WRC000390`).

아래 예제는 로그인한 클라이언트와 조회 조건을 만들고, 조회 메서드에만 쓰는 다시 로그인 함수를 정의합니다. 이 가이드의 나머지 예제는 여기서 만든 `client`, `query`를 이어 씁니다.

```python
from datetime import datetime, timedelta, timezone

from getpass import getpass

from korail_mobile_api import KorailClient, KorailSessionExpiredError, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

member_no = input("회원번호·전화번호·이메일: ")
password = getpass("비밀번호: ")

client = KorailClient()
client.login(member_no, password)
query = TrainSearchQuery(
    departure_station="서울",
    arrival_station="부산",
    departure_date=departure_date,
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


tickets = read_with_relogin(client.list_tickets)
```

다 쓴 클라이언트는 `client.logout()`과 `client.close()`로 정리합니다.

## 상태 변경 요청이 실패했을 때 {#mutations}

예약, 결제, 환불처럼 서버의 상태를 바꾸는 메서드는 API 레퍼런스의 정보 표에 "상태 변경: 예"로 표시돼 있습니다.
라이브러리는 이런 요청을 자동으로 다시 보내지 않습니다. 응답을 읽지 못했어도 서버에서는 이미 처리됐을 수 있기 때문입니다.
예외 종류에 따라 요청이 서버에 닿았는지가 다릅니다.

| 예외 | 요청 | 할 일 |
|---|---|---|
| `KorailNetFunnelError`, `KorailQueueRejectedError` | 보내지 않았습니다. | 대기열 상황을 보고 다시 호출할지 정합니다. |
| `KorailInvalidInputError` | 보내지 않았습니다. | 입력을 고친 뒤 호출합니다. |
| `KorailAuthError`(로그인하지 않음) | 보내지 않았습니다. | 로그인한 뒤 호출합니다. |
| `KorailProtocolError`(응답을 읽지 못함) | 보냈고 응답을 받았습니다. | 서버에서 처리됐을 수 있습니다. `raw`와 예약 내역으로 결과를 확인합니다. |
| `KorailDynaPathError` | 보냈고 차단 코드가 든 응답을 받았습니다. | 서버에서 처리됐는지 알 수 없으므로 예약 내역으로 결과를 확인합니다. |
| `KorailTransportError` | 서버에 닿았는지 알 수 없습니다. | 예약 내역이나 승차권 목록으로 결과를 확인합니다. |
| `KorailAppError`와 하위 예외 | 보냈고 서버가 실패로 응답했습니다. | `code`와 `message`로 사유를 확인합니다. |
| `KorailSessionExpiredError` | 보냈고 서버가 세션 만료로 응답했습니다. | 다시 로그인한 뒤 결과를 확인하고 다시 호출할지 정합니다. |

결과는 결제 전 홀드라면 [`list_reservations`](../api/reservations.md#list_reservations), 발권된 승차권이라면 [`list_tickets`](../api/account.md#list_tickets)로 확인합니다.
아래 예제는 예약 전에 살아 있는 홀드의 PNR을 기록해 두고, 예약이 불확실하게 끝나면 새 PNR이 생겼는지 비교합니다. 입력 거절은 `KorailInvalidInputError`로 구분하고, 전송·해석 실패는 `request_sent`를 확인합니다. `raw=None`만으로 상태 확인을 건너뛰지 않습니다.

!!! warning "실제로 처리됩니다"
    이 예제의 `reserve()`는 실제로 좌석을 점유하는 홀드를 만듭니다. 결제하지 않을 홀드는 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)로 취소하세요. 응답을 읽지 못해 예외가 나도 서버에서는 처리됐을 수 있으므로 다시 호출하기 전에 결과를 확인하세요.

```python
from korail_mobile_api import KorailInvalidInputError, KorailProtocolError, KorailTransportError


def held_pnrs():
    history = client.list_reservations()
    return {row.pnr_no for row in history.trains if row.pnr_no}


train = next(t for t in client.search_trains(query).trains if t.general_reservation_code == "11")
before = held_pnrs()
try:
    hold = client.reserve(train)
except KorailInvalidInputError:
    raise  # 예약 입력을 거절했으며 예약 요청은 보내지 않았습니다.
except (KorailTransportError, KorailProtocolError) as error:
    if error.request_sent is not True:
        raise  # 전송 표식이 없는 오류는 원인별로 확인하며 미전송이라고 단정하지 않습니다.
    created = held_pnrs() - before
    if created:
        print("홀드가 만들어졌습니다. 다시 예약하지 마세요:", sorted(created))
    else:
        print("새 홀드가 보이지 않습니다. 확인한 뒤 다시 예약할지 정하세요.")
    raise
```

## 기존 예약을 가져오지 못했을 때 {#existing-reservation}

[`get_reservation_hold`](../api/reservations.md#get_reservation_hold)는 상세를 읽은 뒤 PNR, 창구번호,
여정·좌석, 정산액을 검사하고, 결제 플래그가 명시된 경우에만 `Y`인지 검사합니다. 필수값 누락이나 불일치는 `KorailProtocolError`이며
전체 상세 응답은 예외의 `.raw`에 남습니다. 이 호출은 조회만 하므로 검증 실패가 새 예약이나 결제를 뜻하지 않습니다.

같은 계정의 예약인지, 앱에서 아직 결제 가능한 상태인지 먼저 확인하세요.
일반 상세 조회만 필요하면 [`get_ticket_reservation_detail`](../api/reservations.md#get_ticket_reservation_detail)을 사용합니다.
오류를 피하려고 창구번호·금액·결제 플래그를 임의로 채워 결제를 이어가지 마세요.
세션 만료와 서버 거절, 전송 오류는 기존 조회 API와 같은 예외로 전달되며 자동 재시도하지 않습니다.

## 예약 응답을 읽지 못한 홀드 취소 {#unparsed-hold}

예약 응답을 읽지 못해 `KorailProtocolError`가 나면 홀드는 서버에 이미 만들어졌을 수 있습니다. 응답에 예약번호(PNR)가 있으면 예외의 `raw`에 남습니다. JSON `null` 등 식별자가 없는 응답은 이 방법으로 복구할 수 없으므로 예약 내역에서 대상을 확인하세요.
같은 상세를 읽는 [`get_reservation_hold`](../api/reservations.md#get_reservation_hold)도 같은 이유로 실패할 수 있습니다.
[`HoldReference.from_raw`][korail_mobile_api.HoldReference]로 `raw`의 예약번호(`h_pnr_no`)와 여정 수(`h_jrny_cnt`)를 읽어 [`cancel_unpaid_hold`](../api/reservations.md#cancel_unpaid_hold)에 넘깁니다.
첫 여정의 순번·변경 번호는 `raw`에서 읽을 수 있을 때만 쓰고, 없으면 홀드로 취소할 때와 같은 대체값을 보냅니다. 두 값이 없으면 `from_raw`가, 형식이 맞지 않으면 `cancel_unpaid_hold`가 요청 전에 거절합니다.
`HoldReference`는 취소에만 씁니다. 결제는 [`get_reservation_hold`](../api/reservations.md#get_reservation_hold)로 검증한 홀드로 합니다.

!!! warning "실제로 처리됩니다"
    `cancel_unpaid_hold`는 홀드를 실제로 취소합니다. 취소할 예약번호가 맞는지 [`list_reservations`](../api/reservations.md#list_reservations)로 먼저 확인하세요.

```python
from korail_mobile_api import HoldReference, KorailProtocolError

# train: 위 예제에서 고른 열차
try:
    hold = client.reserve(train)
except KorailProtocolError as error:
    if not isinstance(error.raw, dict):
        raise  # 요청 전 입력 검사에서 거절됐거나 JSON 객체가 아닌 응답입니다.
    response = client.cancel_unpaid_hold(HoldReference.from_raw(error.raw))
    print(response.str_result, response.h_msg_cd)
```

## 카드 결제가 거절됐을 때 {#card-decline}

[`pay_with_card`](../api/payments.md#pay_with_card)는 카드 거절 같은 실패 응답에서 예외를 발생시키지 않고 [`ReservationPaymentResponse`][korail_mobile_api.ReservationPaymentResponse]를 반환합니다.
거절이면 `str_result`가 `"FAIL"`이고, 응답에 `strResult`가 없으면 `None`입니다. 사유는 `h_msg_cd`와 `h_msg_txt`에 있습니다.
`str_result`가 `"SUCC"`일 때만 결제 완료로 처리하세요.

다음 경우에는 여전히 예외가 발생합니다.

- 요청 전 검사: 예약대기 홀드, 결제 금액이 0원인 홀드, 형식이 맞지 않는 카드 입력은 요청을 보내기 전에 [`KorailProtocolError`][korail_mobile_api.KorailProtocolError]로 거절합니다.
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

휴면 계정 해제나 비밀번호 변경처럼 웹 화면에서 처리해야 하면 [`login`](../api/session.md#login)이 [`KorailAuthContinuationRequired`][korail_mobile_api.KorailAuthContinuationRequired]를 발생시킵니다.
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

!!! danger "원문과 모델은 마스킹하지 않습니다"
    응답 모델과 예외의 `raw`에는 서버가 보낸 응답이 가공 없이 들어 있습니다. 이름, 전화번호, 고객번호, 예약번호, 결제 정보 같은 개인정보가 포함될 수 있습니다.
    모델의 `repr`(`print` 출력)에는 `raw`와 호출자가 넣은 비밀값(세션 쿠키, 반환 비밀번호, 카드 정보, 입력 모델의 이름·전화번호·생년월일·고객번호, 기기 식별자)이 나오지 않지만, 그 밖의 응답 필드는 그대로 출력되고 속성 값 자체는 가리지 않습니다. [`KorailSession`][korail_mobile_api.KorailSession]에는 세션 쿠키 값과 로그인 ID도 들어 있습니다.
    모델이 바꿀 수 없는(frozen) dataclass여도 `raw` 안의 사전과 목록은 복사하거나 고정하지 않습니다.
    오류를 기록할 때는 예외의 클래스 이름과 `code`처럼 필요한 값만 남기고, `raw`와 모델 전체를 로그나 오류 보고에 넣지 마세요.
    네트워크 오류로 `KorailTransportError.__cause__`에 붙는 `httpx` 예외에는 메서드와 쿼리를 뺀 URL만 남고 요청 본문·쿠키·DynaPath 토큰은 지웁니다. 응답 모델, `raw`, `dataclasses.asdict`와 pickle 결과는 여전히 마스킹하지 않습니다.
