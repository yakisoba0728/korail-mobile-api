# 시작하기

이 페이지는 라이브러리를 설치하고, 열차를 조회하고, 로그인해서 내 승차권을 확인하는 데까지 한 번에 따라 합니다.

!!! warning "2026-10-23 현재 상태"
    2026-10-21부터 `-8204`(앱 업데이트 안내) 실패가 보고됐습니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)). 보고는 `2!` 헤더 도입 전 코드였습니다.
    2026-10-23 08:16 KST의 2.6.2 기본 설정 익명 조회 성공은 [당시 기록](records.md#live-check-262)에 있습니다.
    같은 날 23:34:34 KST에는 `3.0.0.dev0` 개발 wheel의 기본 요청 버전으로 익명 서울→부산 직통 첫 페이지 조회 1회가 `SUCC`/`IRG000000`, 열차 10개를 반환했습니다([입력·커밋·관측 한계](records.md#live-check-300-dev0-20261023)).
    이 문서는 배포 전인 3.0.0을 설명합니다. 한 노선·날짜·시각의 관측은 출시판의 호환 보증이 아니며, 3.0의 로그인·인증 조회·예약·취소·결제·환불은 실서버 미검증입니다.

## 요구 사항

- Python 3.11 이상
- 의존성: `httpx` 0.24.1 이상, `cryptography` 42.0.8 이상 (설치할 때 함께 설치됩니다)

## 설치

PyPI에서 설치합니다. PyPI의 최신 배포는 2.6.2(2.x API)이며, 이 문서의 3.0 이름을 쓰려면 아래 개발 버전을 설치하세요.

```sh
pip install korail-mobile-api
```

### 개발 버전 {#development-version}

배포 전인 3.0(`main`)은 GitHub에서 설치합니다.

```sh
pip install --force-reinstall "git+https://github.com/yakisoba0728/korail-mobile-api@main"
```

현재 `main`의 패키지 버전은 `3.0.0.dev0`이며 배포판 2.6.2와 다릅니다. 개발 중에는 여러 커밋이 같은 개발 버전을 쓸 수 있어 `--force-reinstall`로 다시 설치합니다. 재현이 필요하면 `@main` 대신 확인할 커밋을 지정하세요. 2.x 코드를 옮기는 방법은 [3.0으로 옮기기](migration-3.0.md)에 있습니다.

저장소를 내려받았다면 저장소 루트에서 설치할 수도 있습니다.

```sh
pip install .
```

패키지 이름은 `korail-mobile-api`이고, import 이름은 `korail_mobile_api`입니다.
SOCKS 프록시를 쓰려면 `pip install "korail-mobile-api[socks]"`로 설치합니다([프록시](guide/configuration.md#proxy)).

## 클라이언트 만들기

모든 기능은 [`KorailClient`][korail_mobile_api.KorailClient]의 메서드로 제공됩니다.
자주 쓰는 역·열차·예약·승차권 작업은 선택형 [`Korail` 간편 API](guide/convenience.md)로도 호출할 수 있습니다.
설정 없이 만들면 기본 요청 버전 `AppVersion=7.0.8`·API `Version=250601003`과 SDK 2.0.1 `2!` 진단 DynaPath 토큰을 씁니다([설정과 검증 범위](guide/configuration.md#dynapath)).
위 현재 상태처럼 이 기본값의 요청이 거절될 수 있습니다.

클라이언트는 내부에 HTTP 연결 풀을 가지고 있습니다. `with` 문으로 쓰면 블록이 끝날 때 `close()`로 연결을 닫습니다.
`close()`는 서버 로그아웃을 하지 않습니다. 간편 API의 `Korail`도 같습니다.

```python
from korail_mobile_api import KorailClient

with KorailClient() as client:
    ...  # 조회·예약 등
```

설정을 바꾸려면 [`KorailConfig`][korail_mobile_api.KorailConfig]를 넘깁니다. 자세한 내용은 [설정](guide/configuration.md)을 참고하세요.

## 열차 조회

열차 조회에는 로그인이 필요하지 않습니다. 조회 조건은 [`TrainSearchQuery`][korail_mobile_api.TrainSearchQuery]로 만듭니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import KorailClient, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

with KorailClient() as client:
    query = TrainSearchQuery(
        departure_station="서울",
        arrival_station="부산",
        departure_date=departure_date,
        departure_time="090000",
        passengers=1,
    )
    result = client.search_trains(query)
    for train in result.trains:
        print(train.train_class_name, train.train_no, train.departure_time, train.arrival_time)
```

| 필드 | 형식 | 설명 |
|---|---|---|
| `departure_station`, `arrival_station` | 역 이름 또는 역 코드 | 역 코드를 넣으면 역 목록을 조회해 역 이름으로 바꿔 보냅니다. |
| `departure_date` | `YYYYMMDD` | 출발일입니다. |
| `departure_time` | `HHMMSS` | 이 시각 이후에 출발하는 열차를 조회합니다. 기본값은 `"000000"`입니다. |
| `passengers` | 정수 | 어른 인원입니다. 어린이·경로 등은 `child_passengers`, `senior_passengers` 같은 필드로 따로 넣습니다. |

결과는 [`TrainSearchResult`][korail_mobile_api.TrainSearchResult]입니다.
`trains`에 열차가 [`TrainSummary`][korail_mobile_api.TrainSummary] 목록으로 들어 있습니다.
조건에 맞는 열차가 없으면 예외 없이 `trains`가 비어 있을 수 있으므로 비었는지 확인하세요.
서버가 결과 없음으로 실패를 알리면 [`KorailNoResultsError`][korail_mobile_api.KorailNoResultsError]가 발생합니다.
직통 열차가 없다는 결과 코드(`WRD000061`)에는 그 하위 클래스인 [`KorailNoDirectTrainError`][korail_mobile_api.KorailNoDirectTrainError]가 발생합니다.
이때 환승 조회로 이어 가려면 [`search_trains_with_transfer_fallback`](api/trains.md#search_trains_with_transfer_fallback)을 사용하세요.

### 다음 페이지

조회 결과는 한 번에 한 페이지씩 옵니다. 다음 페이지가 있으면 `next_page()`가 이어서 조회할 때 쓸 값을 돌려줍니다.
아래 예제는 새 클라이언트로 첫 페이지와 다음 페이지를 조회한 뒤 연결을 닫습니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import KorailClient, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")
with KorailClient() as client:
    query = TrainSearchQuery(
        departure_station="서울",
        arrival_station="부산",
        departure_date=departure_date,
        departure_time="090000",
    )
    result = client.search_trains(query)
    continuation = result.next_page()
    if continuation is not None:
        more = client.search_trains(query, continuation=continuation)
        print(len(more.trains), "편")
```

직통 조회에서는 다음 페이지가 있어도 `next_page()`가 `None`일 수 있습니다.
이때는 `result.next_query_from_last_departure(query)`로 마지막 열차의 출발일·출발 시각부터 조회할 조건을 만들 수 있습니다.
마지막 열차가 다시 포함될 수 있습니다. 열차 번호만 같다고 다른 날짜·구간의 행까지 합치지 마세요. 복합 식별자와 조회 상한을 적용하는 [`korail.trains.iter_search`](guide/convenience.md#필요한-만큼-이어-읽기)를 우선 사용하거나 [열차 조회](guide/trains.md#next-page)의 기준을 따르세요.

## 로그인

승차권 조회, 예약, 결제처럼 계정이 필요한 기능은 먼저 로그인해야 합니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient

with KorailClient() as client:
    session = client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    try:
        tickets = client.list_tickets()
        for reservation in tickets.reservations:
            print(len(reservation.tickets), "장")
    finally:
        client.logout()
```

로그인 ID는 회원번호, 전화번호(하이픈 없이), 이메일 중 하나입니다. 하이픈이 들어간 전화번호처럼 숫자만도 이메일도 아닌 값은 요청을 보내기 전에 거절하며, 이때 [`KorailInvalidInputError`][korail_mobile_api.KorailInvalidInputError]가 발생합니다.

로그인에 실패하면 [`KorailAuthError`][korail_mobile_api.KorailAuthError]가 발생합니다.
예외의 `code`에 서버가 돌려준 결과 코드가 들어 있습니다. 비밀번호를 여러 번 틀리면 계정이 잠길 수 있으니 반복해서 재시도하지 마세요.
서비스 이용 불가 응답이나 앱 업데이트 요구 응답(`SUPDATE`, 서버 코드 `-8204`)에는 `KorailAuthError` 대신 [`KorailServiceUnavailableError`][korail_mobile_api.KorailServiceUnavailableError]나 [`KorailAppUpdateRequiredError`][korail_mobile_api.KorailAppUpdateRequiredError]가 발생합니다.
이런 응답은 로그인 요청을 보내기 전에 서비스 상태를 확인하는 단계에서 올 수도 있습니다.

휴면 계정 해제나 비밀번호 변경처럼 웹 화면에서 처리해야 하는 경우에는 [`KorailAuthContinuationRequired`][korail_mobile_api.KorailAuthContinuationRequired]가 발생합니다.
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
위 예제처럼 `logout()`은 `with` 블록 안의 `finally`에서 부르면, 로그아웃이 실패해도 블록이 끝날 때 연결은 닫힙니다.

## 세션 만료

로그인 후 시간이 지나 서버 세션이 끝나면, 다음 요청에서 [`KorailSessionExpiredError`][korail_mobile_api.KorailSessionExpiredError]가 발생합니다.
이때 라이브러리는 로컬 세션을 비우므로 다시 `login()`을 호출하면 됩니다.

## 다음 단계

- [열차 조회](guide/trains.md): 환승 조회, 호차·좌석 배치, 운임 조회
- [예약](guide/reservations.md): 좌석을 잡고, 예약 내역을 확인하고, 취소하기
- [결제와 환불](guide/payments.md): 카드 결제, 할인 재계산, 환불
- [오류 처리](guide/errors.md): 예외 종류와 응답 원문(`raw`) 확인
