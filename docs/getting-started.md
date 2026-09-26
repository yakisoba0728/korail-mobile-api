# 시작하기

이 페이지는 라이브러리를 설치하고, 열차를 조회하고, 로그인해서 내 승차권을 확인하는 데까지 한 번에 따라 합니다.

## 요구 사항

- Python 3.11 이상
- 의존성: `httpx` 0.24.1 이상, `cryptography` 42.0.8 이상 (설치할 때 함께 설치됩니다)

## 설치

PyPI에는 배포하지 않습니다. GitHub 저장소에서 바로 설치합니다.

```sh
pip install "git+https://github.com/yakisoba0728/korail-mobile-api"
```

저장소를 내려받았다면 저장소 루트에서 설치할 수도 있습니다.

```sh
pip install .
```

패키지 이름은 `korail-mobile-api`이고, import 이름은 `korail_mobile_api`입니다.

## 클라이언트 만들기

모든 기능은 [`KorailClient`][korail_mobile_api.client.KorailClient]의 메서드로 제공됩니다.
설정 없이 만들면 코레일+ 앱 7.0.6과 같은 기본값을 사용합니다.

```python
from korail_mobile_api import KorailClient

client = KorailClient()
```

클라이언트는 내부에 HTTP 연결 풀을 가지고 있습니다. 다 쓰고 나면 `close()`로 닫습니다.
`with` 문은 지원하지 않으므로 `try`/`finally`로 닫는 것을 권장합니다.

```python
client = KorailClient()
try:
    ...  # 조회·예약 등
finally:
    client.close()
```

설정을 바꾸려면 [`KorailConfig`][korail_mobile_api.config.KorailConfig]를 넘깁니다. 자세한 내용은 [설정](guide/configuration.md)을 참고하세요.

## 열차 조회

열차 조회에는 로그인이 필요하지 않습니다. 조회 조건은 [`TrainSearchQuery`][korail_mobile_api.models.TrainSearchQuery]로 만듭니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    query = TrainSearchQuery(
        departure_station_code="서울",
        arrival_station_code="부산",
        departure_date="20261002",
        departure_time="090000",
        passengers=1,
    )
    result = client.search_trains(query)
    for train in result.trains:
        print(train.train_class_name, train.train_no, train.departure_time, train.arrival_time)
finally:
    client.close()
```

| 필드 | 형식 | 설명 |
|---|---|---|
| `departure_station_code`, `arrival_station_code` | 역 이름 또는 역 코드 | 역 코드를 넣으면 역 목록을 조회해 역 이름으로 바꿔 보냅니다. |
| `departure_date` | `YYYYMMDD` | 출발일입니다. |
| `departure_time` | `HHMMSS` | 이 시각 이후에 출발하는 열차를 조회합니다. 기본값은 `"000000"`입니다. |
| `passengers` | 정수 | 어른 인원입니다. 어린이·경로 등은 `child_passengers`, `senior_passengers` 같은 필드로 따로 넣습니다. |

결과는 [`TrainSearchResult`][korail_mobile_api.models.TrainSearchResult]입니다.
`trains`에 열차가 [`TrainSummary`][korail_mobile_api.models.TrainSummary] 목록으로 들어 있습니다.
조건에 맞는 열차가 없으면 예외 없이 `trains`가 비어 있을 수 있으므로 비었는지 확인하세요.
서버가 결과 없음으로 실패를 알리면 [`KorailNoResultsError`][korail_mobile_api.errors.KorailNoResultsError]가 발생합니다.
직통 열차가 없다는 결과 코드(`WRD000061`)에는 그 하위 클래스인 [`KorailNoDirectTrainError`][korail_mobile_api.errors.KorailNoDirectTrainError]가 발생합니다.
이때 환승 조회로 이어 가려면 [`search_trains_with_transfer_fallback`](api/trains.md#search_trains_with_transfer_fallback)을 사용하세요.

### 다음 페이지

조회 결과는 한 번에 한 페이지씩 옵니다. 다음 페이지가 있으면 `next_page()`가 이어서 조회할 때 쓸 값을 돌려줍니다.

```python
continuation = result.next_page()
if continuation is not None:
    more = client.search_trains(query, continuation=continuation)
```

직통 조회에서는 다음 페이지가 있어도 `next_page()`가 `None`일 수 있습니다.
이때는 `result.next_query_from_last_departure(query)`로 마지막 열차의 출발일·출발 시각부터 조회할 조건을 만들 수 있습니다.
마지막 열차가 다시 포함될 수 있으니 열차 번호로 중복을 거르세요. 자세한 내용은 [열차 조회](guide/trains.md)를 참고하세요.

## 로그인

승차권 조회, 예약, 결제처럼 계정이 필요한 기능은 먼저 로그인해야 합니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient

client = KorailClient()
try:
    session = client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    tickets = client.get_ticket_list()
    for reservation in tickets.reservations:
        print(len(reservation.tickets), "장")
finally:
    try:
        client.logout()
    finally:
        client.close()
```

로그인 ID는 회원번호, 전화번호(하이픈 없이), 이메일 중 하나입니다. 하이픈이 들어간 전화번호처럼 숫자만도 이메일도 아닌 값은 요청을 보내기 전에 거절하며, 이때 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.

로그인에 실패하면 [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError]가 발생합니다.
예외의 `code`에 서버가 돌려준 결과 코드가 들어 있습니다. 비밀번호를 여러 번 틀리면 계정이 잠길 수 있으니 반복해서 재시도하지 마세요.
서비스 이용 불가 응답이나 앱 업데이트 요구 응답에는 `KorailAuthError` 대신 [`KorailServiceUnavailableError`][korail_mobile_api.errors.KorailServiceUnavailableError]나 [`KorailAppUpdateRequiredError`][korail_mobile_api.errors.KorailAppUpdateRequiredError]가 발생합니다.
이런 응답은 로그인 요청을 보내기 전에 서비스 상태를 확인하는 단계에서 올 수도 있습니다.

휴면 계정 해제나 비밀번호 변경처럼 웹 화면에서 처리해야 하는 경우에는 [`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired]가 발생합니다.
이 예외의 `redirect_url`에 서버가 알려 준 주소가 들어 있습니다. 라이브러리는 이 단계를 자동으로 진행하지 않습니다.
`KorailAuthContinuationRequired`는 `KorailAuthError`의 하위 클래스이므로, 따로 처리하려면 `KorailAuthError`보다 먼저 잡으세요.

## 로그아웃과 정리

세 메서드는 하는 일이 다릅니다.

| 메서드 | 서버 로그아웃 | 로컬 세션·쿠키 | 연결 풀 |
|---|:-:|:-:|:-:|
| `logout()` | 요청함 | 비움 | 유지 |
| `clear_session()` | 요청하지 않음 | 비움 | 유지 |
| `close()` | 요청하지 않음 | 유지 | 닫음 |

`logout()`은 서버 요청이 실패해도 로컬 세션은 비웁니다. 다만 서버 쪽 세션이 실제로 끝났는지까지는 보장하지 않습니다.
전송 오류가 나거나 세션 만료(`P058`) 응답을 받으면 `logout()`도 예외를 발생시킵니다. 그 밖의 `FAIL` 응답은 예외로 바꾸지 않습니다.
따라서 위 예제처럼 `close()`는 `logout()`과 별도의 `finally`에서 호출하세요.

## 세션 만료

로그인 후 시간이 지나 서버 세션이 끝나면, 다음 요청에서 [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError]가 발생합니다.
이때 라이브러리는 로컬 세션을 비우므로 다시 `login()`을 호출하면 됩니다.

## 다음 단계

- [열차 조회](guide/trains.md): 환승 조회, 호차·좌석 배치, 운임 조회
- [예약](guide/reservations.md): 좌석을 잡고, 예약 내역을 확인하고, 취소하기
- [결제와 환불](guide/payments.md): 카드 결제, 할인 재계산, 환불
- [오류 처리](guide/errors.md): 예외 종류와 응답 원본 확인
