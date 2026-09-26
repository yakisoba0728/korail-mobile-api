# 설정

이 가이드는 [`KorailConfig`][korail_mobile_api.config.KorailConfig]로 클라이언트의 동작을 바꾸는 방법을 설명합니다.
설정 필드 전체, DynaPath 토큰, 대기열(NetFunnel), 언어 필드, 환경변수로 설정을 만드는 방법을 차례로 다룹니다.
설정을 넘기지 않으면 코레일+ 앱 7.0.6을 기준으로 정한 기본값을 쓰며, 대부분은 바꿀 필요가 없습니다.

## 설정 만들기

`KorailConfig`는 바꿀 수 없는(frozen) dataclass입니다. 바꿀 필드만 키워드 인자로 넘겨 만들고, [`KorailClient`][korail_mobile_api.client.KorailClient]의 첫 번째 인자로 넘깁니다.
설정은 클라이언트를 만들 때 적용됩니다. 설정을 바꾸려면 새 설정으로 새 클라이언트를 만드세요.

```python
from korail_mobile_api import KorailClient, KorailConfig

config = KorailConfig(timeout=30.0, netfunnel_wait_limit=120.0)
client = KorailClient(config)
try:
    calendar = client.get_train_calendar()
finally:
    client.close()
```

이미 있는 설정에서 몇 필드만 바꾸려면 `dataclasses.replace`를 씁니다. DynaPath 기기값은 원래 설정의 값을 그대로 이어받습니다.

```python
import dataclasses

from korail_mobile_api import KorailConfig

base = KorailConfig()
longer_wait = dataclasses.replace(base, netfunnel_wait_limit=300.0)
```

## 설정 필드

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `base_url` | `str` | `"https://smart.letskorail.com"` | KORAIL API 서버 주소입니다. 검사하지 않고 그대로 씁니다. |
| `device` | `str` | `"AD"` | 공통 필드 `Device`의 값입니다. |
| `version` | `str` | `"250601003"` | 공통 필드 `Version`의 값입니다. |
| `key` | `str` | `"korail1234567890"` | 공통 필드 `Key`의 값입니다. |
| `timeout` | `float` | `60.0` | API 요청의 제한 시간(초)입니다. |
| `user_agent` | `str` | `"korailtalk"` | API 요청의 `User-Agent` 헤더입니다. |
| `dynapath` | [`DynapathConfig`][korail_mobile_api.dynapath.DynapathConfig] | 설정마다 새로 합성 | DynaPath 토큰 설정입니다. [DynaPath](#dynapath)를 참고하세요. |
| `device_width` | `int` | `1440` | 공통 코드 조회(로그인 포함)의 `deviceWidth` 값입니다. |
| `device_height` | `int` | `3120` | 공통 코드 조회(로그인 포함)의 `deviceHeight` 값입니다. |
| `android_sdk_int` | `int` | `37` | 공통 코드 조회(로그인 포함)의 `OSVersion` 값입니다. |
| `advertising_id` | `str` | `""` | 승차권 목록 조회([`get_ticket_list`](../api/account.md#get_ticket_list))의 `txtDeviceId` 값입니다. 빈 문자열이면 보내지 않습니다. |
| `netfunnel_url` | `str` | `"https://nf.letskorail.com"` | 대기열 서버 주소입니다. 검사하지 않고 그대로 씁니다. |
| `netfunnel_timeout` | `float` | `3.0` | 대기열 요청 하나의 제한 시간(초)입니다. |
| `netfunnel_user_agent` | `str` | `"Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)"` | 대기열 요청의 `User-Agent` 헤더입니다. |
| `netfunnel_enabled` | `bool` | `True` | 대기열을 거칠지 여부입니다. |
| `lang` | `str` \| `None` | `None` | 공통 필드 `lang`의 값입니다. `None`이면 보내지 않습니다. |
| `netfunnel_wait_limit` | `float` \| `None` | `None` | 대기열에서 기다릴 누적 시간의 상한(초)입니다. `None`이면 제한하지 않습니다. |
| `netfunnel_actions` | `Mapping[str, str]` \| `None` | `None` | 관문별 대기열 식별값을 바꿉니다. |
| `disable_dynapath` | `bool` | `False` | `True`이면 DynaPath 토큰을 붙이지 않습니다. |

`device`, `version`, `key`, `user_agent`를 바꾸면 앱과 다른 요청이 됩니다.
API 요청의 `User-Agent`와 대기열 요청의 `User-Agent`는 서로 다른 설정입니다.

## DynaPath {#dynapath}

DynaPath는 앱이 보호하는 경로에 붙이는 토큰 헤더(`x-dynapath-m-token`)입니다. 기본으로 켜져 있습니다.
토큰은 기기 식별자, 앱 시작 시각, 안드로이드 버전, 기기 모델 같은 기기값과 요청 시각으로 만듭니다.

토큰을 붙이는 경로는 [`DynapathConfig`][korail_mobile_api.dynapath.DynapathConfig]의 `allowlist_paths`이며, 기본값은 다음 여섯 경로입니다.
앱이 토큰을 붙이는 경로 목록과 같은지는 앱 내부 값이 공개돼 있지 않아 확인하지 못했습니다.

- `/classes/com.korail.mobile.login.Login`
- `/classes/com.korail.mobile.seatMovie.ScheduleView`
- `/classes/com.korail.mobile.seatMovie.ScheduleViewSpecial`
- `/classes/com.korail.mobile.trn.prcFare.do`
- `/classes/com.korail.mobile.certification.TicketReservation`
- `/classes/com.korail.mobile.nonMember.NonMemTicket`

### 기본 기기값

`dynapath`를 지정하지 않으면 `KorailConfig`를 만들 때마다 기기값을 새로 합성합니다.
기기 식별자는 16자리 16진수 무작위 값, 앱 시작 시각은 설정을 만든 시각, 안드로이드 버전은 `"17"`, 기기 모델은 `"SM-S948N"`입니다.
같은 설정 객체를 쓰는 동안에는 같은 기기값을 씁니다. 실제 기기의 값을 쓰려면 [환경변수로 설정 만들기](#from-env)를 참고하세요.

### 직접 지정하기

`DynapathConfig(enabled=True, ...)`를 `dynapath`로 넘기면 그 설정을 그대로 씁니다.
켜진 `DynapathConfig`에는 `token_settings`와 `token_provider` 중 정확히 하나를 넣어야 하며, 그렇지 않으면 `ValueError`가 발생합니다.

| `DynapathConfig` 필드 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `enabled` | `bool` | `False` | 토큰을 붙일지 여부입니다. `KorailConfig`에 직접 넘길 때는 `True`로 만듭니다. |
| `token_settings` | [`DynapathTokenSettings`][korail_mobile_api.dynapath.DynapathTokenSettings] \| `None` | `None` | 라이브러리가 토큰을 만들 때 쓰는 기기값입니다. |
| `token_provider` | [`DynapathTokenProvider`][korail_mobile_api.dynapath.DynapathTokenProvider] \| `None` | `None` | 토큰을 직접 만들어 주는 함수입니다. |
| `timestamp_ms_provider` | `Callable[[], int]` \| `None` | `None` | `token_settings`로 토큰을 만들 때 쓰는 시각(밀리초) 공급 함수입니다. `None`이면 현재 시각입니다. |
| `random_text_provider` | `Callable[[], str]` \| `None` | `None` | `token_settings`로 토큰을 만들 때 쓰는 무작위 문자열 공급 함수입니다. `None`이면 무작위로 만듭니다. |
| `header_name` | `str` | `"x-dynapath-m-token"` | 토큰 헤더 이름입니다. |
| `allowlist_paths` | `frozenset[str]` | 위의 여섯 경로 | 토큰을 붙일 경로입니다. |
| `device_name` | `str` | `"SM-S948N"` | `token_provider`에 넘기는 기기 이름입니다. |
| `os_version` | `str` | `"17"` | `token_provider`에 넘기는 안드로이드 버전입니다. |

[`DynapathTokenSettings`][korail_mobile_api.dynapath.DynapathTokenSettings]는 다섯 값을 반드시 받습니다. 비어 있거나 공백뿐이면 `ValueError`가 발생하며, `app_start_ts`는 정수로 읽을 수 있어야 합니다.
나머지 필드에는 라이브러리 기본값이 있으며, 바꾸면 앱과 다른 토큰이 됩니다.

| 필드 | 뜻 |
|---|---|
| `device_id` | 기기 식별자입니다. |
| `as_value` | 앱 서명에서 나온 값입니다. |
| `app_start_ts` | 앱 시작 시각(밀리초 단위 epoch)을 숫자 문자열로 넣습니다. |
| `os_version` | 안드로이드 버전입니다. 예: `"17"` |
| `device_model` | 기기 모델명입니다. 예: `"SM-S948N"` |

`token_provider`는 토큰을 붙이는 경로의 요청마다 [`DynapathRequestContext`][korail_mobile_api.dynapath.DynapathRequestContext](`method`, `path`, `url`, `device`, `version`, `key`, `user_agent`, `device_name`, `os_version`)를 받아 토큰 문자열을 돌려주는 함수입니다.
`None`을 돌려주면 헤더를 붙이지 않습니다. 함수가 예외를 발생시키면 요청을 보내지 않고 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]를 발생시킵니다.

### 끄기

`disable_dynapath=True`로 끕니다. 켜진 `DynapathConfig`를 함께 넘기면 `ValueError`가 발생합니다.
꺼진 `DynapathConfig(enabled=False, ...)`만 넘기는 것으로는 끌 수 없습니다. 기본값과 다른 꺼진 설정을 넘기면 `ValueError`가 발생하고, 기본값과 같으면 기기값을 합성해 켭니다.

```python
from korail_mobile_api import KorailClient, KorailConfig

client = KorailClient(KorailConfig(disable_dynapath=True))
```

!!! warning "DynaPath를 끄면 로그인할 수 없습니다"
    DynaPath를 끄면 [`login`](../api/session.md#login)은 서비스 상태 확인과 공통 코드 조회까지 보낸 뒤, 로그인 요청을 보내기 전에 [`KorailDynaPathRequiredError`][korail_mobile_api.errors.KorailDynaPathRequiredError]를 발생시킵니다.
    따라서 로그인이 필요한 메서드는 모두 쓸 수 없습니다. 라이브러리가 요청 전에 거절하는 경로는 로그인뿐이지만, 열차 조회처럼 토큰을 붙이던 다른 경로도 서버에서 거절될 수 있습니다.

## 대기열(NetFunnel) {#netfunnel}

열차 조회, 예약, 결제, 예약 내역 조회는 요청 전에 대기열을 거칩니다. 대기열은 작업 종류별 관문으로 나뉩니다.
대기열 서버와 주고받는 순서는 [요청 흐름](../concepts/how-it-works.md)의 "대기열 통과" 단계를 참고하세요.

| 관문 | 메서드 | 대기열 서버 오류 시 |
|---|---|---|
| `inquiry` | [`search_trains`](../api/trains.md#search_trains), [`search_transfer_trains`](../api/trains.md#search_transfer_trains), [`search_trains_with_transfer_fallback`](../api/trains.md#search_trains_with_transfer_fallback), [`get_seat_assignment_schedule`](../api/trains.md#get_seat_assignment_schedule) | 경고 로그를 남기고 대기열 없이 요청을 보냅니다. |
| `peak_season_inquiry` | 위 네 메서드에 `peak_season=True`를 넘겼을 때 | 같음 |
| `product_inquiry` | 열차 조회 세 메서드에 `use_special_schedule=True`를 넘겼을 때(`peak_season`보다 우선) | 같음 |
| `reserve` | [`reserve`](../api/reservations.md#reserve), [`reserve_transfer`](../api/reservations.md#reserve_transfer), [`reserve_with_discount_card`](../api/passes.md#reserve_with_discount_card) | 요청을 보내지 않고 [`KorailNetFunnelError`][korail_mobile_api.errors.KorailNetFunnelError]를 발생시킵니다. |
| `pay` | [`pay_with_card`](../api/payments.md#pay_with_card) | 같음 |
| `reservation_view` | [`get_reservation_history`](../api/reservations.md#get_reservation_history) | 같음 |

- 대기열 서버가 요청을 차단하면(`301`, `302`) 모든 관문에서 [`KorailQueueRejectedError`][korail_mobile_api.errors.KorailQueueRejectedError]가 발생합니다.
- `reserve`, `pay`, `reservation_view` 관문은 대기열 서버가 최종적으로 통과(`200`)로 답하지 않으면 요청을 보내지 않고 `KorailNetFunnelError`를 발생시킵니다.
- 대기열 요청이 실패하면 관문을 통과하는 동안 한 번만 다시 보냅니다. 다시 보내기 전에는 실패한 요청의 제한 시간(`netfunnel_timeout`)이 다 찰 때까지 기다립니다.
- 대기열을 건너뛰거나 입장 키 반납이 실패하면 `korail_mobile_api.netfunnel` 로거에 경고를 남깁니다.

### 대기 시간 제한

`netfunnel_wait_limit`를 정하면 관문을 통과하는 데 걸린 누적 시간이 이 값을 넘을 때 API 요청을 보내지 않고 `KorailNetFunnelError`를 발생시킵니다.
다음 대기를 시작하기 전에 대기 후 시각이 상한을 넘을지 확인하고, 통과한 직후에도 한 번 더 확인합니다. API 요청과 입장 키 반납에 걸린 시간은 포함하지 않습니다.

```python
from korail_mobile_api import KorailClient, KorailConfig, KorailNetFunnelError, TrainSearchQuery

client = KorailClient(KorailConfig(netfunnel_wait_limit=120.0))
try:
    query = TrainSearchQuery(
        departure_station_code="서울",
        arrival_station_code="부산",
        departure_date="20261002",
        departure_time="090000",
        passengers=1,
    )
    result = client.search_trains(query)
except KorailNetFunnelError as error:
    print("대기열을 통과하지 못했습니다:", error.code, error.message)
finally:
    client.close()
```

### 관문 식별값

`netfunnel_actions`는 관문 이름(`inquiry`, `peak_season_inquiry`, `product_inquiry`, `reserve`, `pay`, `reservation_view`)을 키로, 대기열 서버에 보낼 식별값을 값으로 받습니다.
라이브러리의 기본 식별값은 앱 내부 값이 공개돼 있지 않아 확인하지 못한 값입니다. 정확한 값을 알 때만 바꾸세요.
목록에 없는 관문 이름과 빈 문자열 값은 무시합니다.

### 대기열 끄기

`netfunnel_enabled=False`이면 대기열 클라이언트를 만들지 않고 모든 요청을 바로 보냅니다.

!!! warning "대기열을 끄는 것은 권장하지 않습니다"
    앱은 이 요청들을 보내기 전에 대기열을 거칩니다. 대기열을 끄면 앱과 다르게 동작하고 KORAIL의 혼잡 제어를 건너뛰게 됩니다.
    기다리는 시간이 문제라면 대기열을 끄는 대신 `netfunnel_wait_limit`로 상한을 정하세요.

## 언어 필드(`lang`)

`lang`을 정하면 공통 필드를 싣는 요청에서 `Key` 다음(공통 필드에 `Key`가 없는 요청은 `Version` 다음)에 `lang`을 보냅니다.
`None`이면 보내지 않습니다. 앱이 보내는 값은 앱 내부 값이 공개돼 있지 않아 확인하지 못했으므로, 라이브러리는 기본값을 추측해 보내지 않습니다.

## 환경변수로 설정 만들기 {#from-env}

[`build_config_from_env`][korail_mobile_api.live.build_config_from_env]는 환경변수에서 실제 기기의 값을 읽어 `KorailConfig`를 만듭니다.
DynaPath 토큰의 기기값과 대기열 `User-Agent`에 같은 기기값을 씁니다. 앱 시작 시각은 함수를 호출한 시각입니다.
계정 ID, 비밀번호, 카드 정보 같은 자격 증명은 읽거나 저장하지 않습니다.

| 환경변수 | 필수 | 기본값 | 쓰이는 곳 |
|---|:-:|---|---|
| `KORAIL_DYNAPATH_DEVICE_ID` | 예 | - | 토큰의 기기 식별자(`device_id`) |
| `KORAIL_DYNAPATH_OS_VERSION` | 예 | - | 토큰의 `os_version`, `DynapathConfig.os_version`, 대기열 `User-Agent`의 안드로이드 버전 |
| `KORAIL_DYNAPATH_DEVICE_MODEL` | 예 | - | 토큰의 `device_model`, `DynapathConfig.device_name`, 대기열 `User-Agent`의 기기 모델 |
| `KORAIL_ANDROID_BUILD_ID` | `KORAIL_NETFUNNEL_USER_AGENT`가 없을 때 | - | 대기열 `User-Agent`의 `Build/...` 부분 |
| `KORAIL_NETFUNNEL_USER_AGENT` | 아니요 | 위 기기값으로 만든 `Dalvik/2.1.0 (...)` 문자열 | `netfunnel_user_agent` |
| `KORAIL_DYNAPATH_AS_VALUE` | 아니요 | 라이브러리 기본값 | 토큰의 `as_value` |
| `KORAIL_ADVERTISING_ID` | 아니요 | `""` | `advertising_id` |
| `KORAIL_BASE_URL` | 아니요 | `"https://smart.letskorail.com:443"` | `base_url` |
| `KORAIL_USER_AGENT` | 아니요 | `"korailtalk"` | `user_agent` |
| `KORAIL_DEVICE_WIDTH` | 아니요 | `1440` | `device_width` |
| `KORAIL_DEVICE_HEIGHT` | 아니요 | `3120` | `device_height` |
| `KORAIL_ANDROID_SDK_INT` | 아니요 | `37` | `android_sdk_int` |

필수 환경변수가 없거나 비어 있으면 `RuntimeError`가 발생합니다. 정수 필드에 숫자가 아닌 값을 넣으면 `ValueError`가 발생합니다.
대기열 설정과 `lang`처럼 표에 없는 필드는 기본값을 씁니다. 바꾸려면 `dataclasses.replace`를 씁니다.

```sh
export KORAIL_DYNAPATH_DEVICE_ID="<기기 식별자>"
export KORAIL_DYNAPATH_OS_VERSION="<안드로이드 버전>"
export KORAIL_DYNAPATH_DEVICE_MODEL="<기기 모델명>"
export KORAIL_ANDROID_BUILD_ID="<빌드 ID>"
```

```python
import dataclasses

from korail_mobile_api import KorailClient, build_config_from_env

config = dataclasses.replace(build_config_from_env(), netfunnel_wait_limit=120.0)
client = KorailClient(config)
try:
    status = client.get_service_status()
finally:
    client.close()
```

## 서버 주소

!!! danger "서버 주소는 검사하지 않습니다"
    `base_url`과 `netfunnel_url`은 검사하지 않고 그대로 씁니다. `build_config_from_env`도 `KORAIL_BASE_URL` 환경변수 값을 그대로 씁니다.
    `base_url`이 다른 서버를 가리키면 로그인 ID와 비밀번호, 세션 쿠키, 카드 정보까지 모든 API 요청이 그 서버로 갑니다. 비밀번호 암호화 키도 같은 서버에서 받으므로, 그 서버에 대해서는 암호화가 보호가 되지 않습니다.
    `netfunnel_url`이 다른 서버를 가리키면 대기열 요청이 그 서버로 가고, 그 서버의 응답에 따라 API 요청을 보낼지와 언제 보낼지가 정해집니다.
    신뢰할 수 있는 주소가 아니면 바꾸지 마세요.
