# 세션·공통

로그인과 로그아웃, 클라이언트 정리, 그리고 로그인 없이 받을 수 있는 공통 정보(서비스 상태, 앱 메인 캐시, 공통 코드, 역 목록, 운행 달력 등)를 다룹니다.
로그인하면 세션이 클라이언트 안에 보관되고, 이후 요청에 자동으로 쓰입니다.
다 쓴 클라이언트는 `logout()`으로 로그아웃한 뒤 `close()`로 연결을 닫습니다.

흐름:

1. [`login`](#login)으로 세션을 만듭니다.
2. 조회·예약·결제 등 필요한 메서드를 호출합니다.
3. [`logout`](#logout)으로 서버에 로그아웃을 요청하고 로컬 세션을 비웁니다.
4. [`close`](#close)로 연결 풀을 닫습니다.

## `login`

회원 계정으로 로그인하고 세션을 만듭니다.

```python
KorailClient.login(
    member_no: str,
    password: str,
    *,
    input_flag: KorailLoginInputFlag | None = None,
    check_valid_pw: Literal['Y', 'N'] = 'Y',
    cust_id: str | None = '',
    etr_path: str | None = '',
) -> KorailSession
```

로그인 전에 기존 로컬 세션과 쿠키를 먼저 비웁니다.
그다음 앱과 같은 순서로 세 요청을 보냅니다. 서비스 상태를 확인하고([`get_service_status`](#get_service_status)와 같은 요청), 공통 코드를 조회해 비밀번호 암호화 정보를 받은 뒤, 로그인 요청을 보냅니다.
암호화 정보는 로그인할 때마다 새로 받습니다. 비밀번호는 이 정보로 AES 암호화해서 보내며, 쓸 수 있는 키를 받지 못하면 평문으로 보내지 않고 거절합니다.
로그인 요청에는 DynaPath 토큰 헤더를 붙입니다.

`input_flag`를 지정하지 않으면 로그인 ID의 형식으로 종류를 정합니다. `@`가 들어 있으면 이메일(`"5"`), 11자리 숫자이면 전화번호(`"4"`), 그 밖의 숫자이면 회원번호(`"2"`)입니다.
숫자만으로 된 값도 이메일도 아닌 ID(하이픈이 든 전화번호, 앞뒤 공백, 전각 숫자 등)는 요청을 보내기 전에 거절합니다.

성공 여부는 결과 코드(`IRZ000001` 또는 `S200`)와 세션 쿠키(`JSESSIONID`)로 판정합니다.
성공하면 세션을 클라이언트에 보관하고 반환합니다. 실패하면 세션을 보관하지 않으며, 웹 단계가 필요한 경우를 빼면 쿠키도 비웁니다.
휴면 계정 해제나 비밀번호 변경처럼 웹 화면에서 처리해야 하는 경우에는 [`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired]가 발생하며, 라이브러리는 그 웹 단계를 진행하지 않습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `member_no` | `str` | 필수 | 로그인 ID입니다. 회원번호, 하이픈 없는 전화번호, 이메일 중 하나입니다. |
| `password` | `str` | 필수 | 비밀번호입니다. 암호화해서 보냅니다. |
| `input_flag` | [`KorailLoginInputFlag`][korail_mobile_api.constants.KorailLoginInputFlag] \| `None` | `None` | 로그인 ID의 종류입니다. `"2"`는 회원번호, `"4"`는 전화번호, `"5"`는 이메일입니다. `None`이면 `member_no`의 형식으로 정합니다. 값을 지정하면 ID 형식 검사를 하지 않습니다. |
| `check_valid_pw` | `Literal['Y', 'N']` | `"Y"` | 로그인 요청의 `checkValidPw` 필드로 보내는 값입니다. |
| `cust_id` | `str` \| `None` | `""` | 로그인 요청의 `custId` 필드입니다. 빈 문자열이나 `None`이면 보내지 않습니다. |
| `etr_path` | `str` \| `None` | `""` | 로그인 요청의 `etrPath` 필드입니다. 빈 문자열이나 `None`이면 보내지 않습니다. |

**반환값**

[`KorailSession`][korail_mobile_api.models.KorailSession] — 로그인한 세션입니다. `jsessionid`(세션 쿠키 값), `member_no`(로그인에 쓴 ID), `member_card_no`, `customer_no`, `raw`(로그인 응답 원본)가 들어 있습니다. `member_card_no`와 `customer_no`는 응답에 없으면 `None`입니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | `input_flag`가 `None`이고 `member_no`가 숫자만으로 된 값도 이메일도 아닐 때(요청 전). 서버에서 받은 암호화 정보에 쓸 수 있는 AES 키가 없을 때(로그인 요청을 보내지 않음). |
| [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError] | 로그인 응답의 결과 코드가 성공 코드가 아닐 때. `code`에 결과 코드, `raw`에 응답 원본이 들어 있습니다. 성공 코드인데 `JSESSIONID` 쿠키가 없을 때도 발생합니다. |
| [`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired] | 결과 코드가 `WRC000116` 또는 `WRC000420`일 때. `redirect_url`에 서버가 알려 준 주소가 들어 있습니다. |
| [`KorailServiceUnavailableError`][korail_mobile_api.errors.KorailServiceUnavailableError] | 로그인 응답의 결과 코드가 `SEMGTK`일 때 |
| [`KorailAppUpdateRequiredError`][korail_mobile_api.errors.KorailAppUpdateRequiredError] | 로그인 응답의 결과 코드가 `SUPDATE`일 때 |
| [`KorailAppError`][korail_mobile_api.errors.KorailAppError]와 하위 예외 | 로그인 전의 서비스 상태 확인이나 공통 코드 조회가 실패로 응답했을 때. 로그인 요청은 보내지 않습니다. |
| [`KorailDynaPathRequiredError`][korail_mobile_api.errors.KorailDynaPathRequiredError] | `KorailConfig(disable_dynapath=True)`로 만든 클라이언트에서 호출했을 때. 서비스 상태 확인과 공통 코드 조회까지 보낸 뒤, 로그인 요청을 보내기 전에 발생합니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from getpass import getpass

from korail_mobile_api import KorailAuthContinuationRequired, KorailAuthError

try:
    session = client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
except KorailAuthContinuationRequired as error:
    print("웹에서 먼저 처리해야 합니다:", error.redirect_url)
except KorailAuthError as error:
    print("로그인 실패:", error.code)
```

## `logout`

서버에 로그아웃을 요청하고 로컬 세션을 비웁니다.

```python
KorailClient.logout() -> None
```

로그인한 상태이면 로그아웃 요청을 보내고, 요청 결과와 관계없이 로컬 세션과 쿠키를 비웁니다.
로그인하지 않은 상태에서 호출하면 요청을 보내지 않고 로컬 상태만 비웁니다.

서버가 실패(`FAIL`)로 응답해도 예외를 발생시키지 않습니다.
다만 결과 코드가 `P058`이면 [`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError]가, 네트워크 오류나 읽을 수 없는 응답이면 해당 예외가 발생합니다. 이때도 로컬 세션은 이미 비워져 있습니다.
서버 쪽 세션이 실제로 끝났는지는 보장하지 않습니다. 연결 풀은 닫지 않으므로 [`close`](#close)를 따로 호출하세요.

**매개변수**

매개변수가 없습니다.

**반환값**

`None`

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
try:
    tickets = client.get_ticket_list()
finally:
    try:
        client.logout()
    finally:
        client.close()
```

## `clear_session`

서버에 알리지 않고 로컬 세션과 쿠키만 비웁니다.

```python
KorailClient.clear_session() -> None
```

요청을 보내지 않습니다. 서버 쪽 세션은 끝내지 않습니다.
웹 단계가 남은 로그인 시도([`KorailAuthContinuationRequired`][korail_mobile_api.errors.KorailAuthContinuationRequired]) 상태도 함께 비웁니다.
이후 로그인이 필요한 메서드는 다시 [`login`](#login)을 호출할 때까지 [`KorailAuthError`][korail_mobile_api.errors.KorailAuthError]를 발생시킵니다.

세션 만료([`KorailSessionExpiredError`][korail_mobile_api.errors.KorailSessionExpiredError])가 발생하면 라이브러리가 이 메서드를 호출해 로컬 세션을 비웁니다.

**매개변수**

매개변수가 없습니다.

**반환값**

`None`

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 해당 없음 |

**예제**

```python
from korail_mobile_api import KorailAuthError

client.clear_session()
try:
    client.get_ticket_list()
except KorailAuthError:
    print("다시 로그인해야 합니다.")
```

## `close`

HTTP 연결 풀과 대기열 연결 풀을 닫습니다.

```python
KorailClient.close() -> None
```

요청을 보내지 않으며, 로그인 세션과 쿠키는 그대로 둡니다. 서버 세션을 끝내려면 먼저 [`logout`](#logout)을 호출하세요.
대기열을 끈 설정(`netfunnel_enabled=False`)에서는 HTTP 연결 풀만 닫습니다.

닫은 클라이언트로 요청을 보내는 메서드를 호출하면 요청을 보내지 않고 [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError]가 발생합니다.
닫은 클라이언트를 다시 여는 메서드는 없으므로 새 [`KorailClient`][korail_mobile_api.client.KorailClient]를 만드세요.
`with` 문은 지원하지 않으므로 `try`/`finally`로 닫습니다.

**매개변수**

매개변수가 없습니다.

**반환값**

`None`

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 해당 없음 |

**예제**

```python
from korail_mobile_api import KorailClient

client = KorailClient()
try:
    calendar = client.get_train_calendar()
finally:
    client.close()
```

## `get_service_status`

예매 서비스가 열려 있는지 확인합니다.

```python
KorailClient.get_service_status(
    timestamp_ms: int | None = None,
) -> ServiceStatusResponse
```

서비스 상태 캐시 파일을 요청하고 응답 봉투로 판정합니다.
서버가 성공으로 응답하면 응답 모델을 반환하고, 실패로 응답하면 결과 코드에 맞는 예외를 발생시킵니다.
실패 응답의 결과 코드가 `SEMGTK`이면 [`KorailServiceUnavailableError`][korail_mobile_api.errors.KorailServiceUnavailableError], `SUPDATE`이면 [`KorailAppUpdateRequiredError`][korail_mobile_api.errors.KorailAppUpdateRequiredError]가 발생합니다.
요청에는 `timeStamp` 하나만 싣고 공통 필드(`Device`, `Version`, `Key`)는 싣지 않습니다.
[`login`](#login)도 로그인 전에 같은 요청을 보냅니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `timestamp_ms` | `int` \| `None` | `None` | 요청의 `timeStamp` 값(밀리초 단위 epoch)입니다. `None`이면 호출 시각을 씁니다. 넘긴 값은 검사하지 않습니다. |

**반환값**

[`ServiceStatusResponse`][korail_mobile_api.read_models.ServiceStatusResponse] — 봉투 필드(`str_result`, `h_msg_cd`, `h_msg_txt`)만 담습니다. 그 밖의 값은 `raw`에 있습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
from korail_mobile_api import KorailAppError

try:
    status = client.get_service_status()
    print(status.h_msg_cd, status.h_msg_txt)
except KorailAppError as error:
    print("예매 서비스를 이용할 수 없습니다:", error.code, error.message)
```

## `get_app_data`

앱 메인 화면이 쓰는 캐시 파일(버전 정보, 공지, 안내 문구)을 받아 옵니다.

```python
KorailClient.get_app_data(timestamp_ms: int | None = None) -> AppDataResponse
```

요청에는 `timeStamp` 하나만 싣습니다. 이 캐시 파일은 봉투 필드가 없어도 정상 응답으로 읽습니다.
`version`은 응답의 버전 정보가 객체일 때만 채우고, `notice`는 공지가 객체로 들어 있을 때만 채웁니다. 둘 다 없으면 `None`입니다.
문자열 필드는 응답에 없거나 타입이 맞지 않으면 `None`입니다. 모델에 없는 값은 `raw`에 그대로 있습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `timestamp_ms` | `int` \| `None` | `None` | 요청의 `timeStamp` 값(밀리초 단위 epoch)입니다. `None`이면 호출 시각을 씁니다. 넘긴 값은 검사하지 않습니다. |

**반환값**

[`AppDataResponse`][korail_mobile_api.models.AppDataResponse] — `disability_certification_msg`, `railplus_cardinfo`, `version`, `notice`를 담습니다. `version`은 [`AppVersionInfo`][korail_mobile_api.models.AppVersionInfo](`message`, `new_version`, `store_url`), `notice`는 [`NoticeResponse`][korail_mobile_api.models.NoticeResponse]입니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
app_data = client.get_app_data()
if app_data.version is not None:
    print(app_data.version.new_version, app_data.version.store_url)
if app_data.notice is not None:
    print(app_data.notice.post_title)
```

## `get_notice`

앱 메인 캐시에 들어 있는 공지를 읽습니다.

```python
KorailClient.get_notice(timestamp_ms: int | None = None) -> NoticeResponse
```

[`get_app_data`](#get_app_data)와 같은 요청을 보내고, 그 안의 공지만 돌려줍니다.
공지가 없으면 예외 대신 공지 필드가 모두 `None`인 응답을 반환합니다.
어느 경우든 봉투 필드와 `raw`는 캐시 응답 전체의 값입니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `timestamp_ms` | `int` \| `None` | `None` | 요청의 `timeStamp` 값(밀리초 단위 epoch)입니다. `None`이면 호출 시각을 씁니다. 넘긴 값은 검사하지 않습니다. |

**반환값**

[`NoticeResponse`][korail_mobile_api.models.NoticeResponse] — `board_id`, `post_sequence`, `post_title`, `post_content`를 담습니다. 값이 없으면 `None`입니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
notice = client.get_notice()
if notice.post_title is not None:
    print(notice.post_title)
    print(notice.post_content)
```

## `get_common_code`

공통 코드 이름으로 서버의 앱 설정값을 조회합니다.

```python
KorailClient.get_common_code(code: str | Sequence[str] = '') -> BaseKorailResponse
```

코드 이름 여러 개를 넘기면 한 요청에 `code` 필드를 여러 번 실어 한 번에 조회합니다.
응답에서 각 코드의 값은 `raw`에 코드 이름을 키로 들어 있습니다. 값의 형식은 코드마다 다르며 라이브러리는 해석하지 않습니다.
요청에는 공통 필드와 함께 설정의 `device_width`, `device_height`, `android_sdk_int`를 `deviceWidth`, `deviceHeight`, `OSVersion`으로 싣습니다.
[`login`](#login)은 이 요청으로 비밀번호 암호화 정보를 받습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `code` | `str` \| `Sequence[str]` | `""` | 조회할 코드 이름 하나 또는 여러 개입니다. 기본값 `""`이면 빈 `code` 필드 하나를 보냅니다. |

**반환값**

[`BaseKorailResponse`][korail_mobile_api.models.BaseKorailResponse] — 봉투 필드와 `raw`만 담습니다. 코드별 값은 `raw[코드 이름]`으로 읽습니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
codes = ["app.main.popup", "app.holiday.popup"]
response = client.get_common_code(codes)
for code in codes:
    print(code, response.raw.get(code))
```

## `get_uuid`

서버가 발급하는 단말 검증값을 받아 옵니다.

```python
KorailClient.get_uuid() -> UuidResponse
```

본문이 없는 POST를 보내며, 공통 필드와 DynaPath 헤더는 싣지 않습니다.
응답의 `mutMrkVrfCd` 값을 `verification_code`로 돌려줍니다. 봉투 필드가 일부 없어도 읽습니다.
라이브러리의 다른 메서드는 이 값을 사용하지 않습니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`UuidResponse`][korail_mobile_api.models.UuidResponse] — `verification_code`에 검증값이 문자열로 들어 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 응답에 `mutMrkVrfCd`가 없거나, 빈 값이거나, 문자열·정수가 아닐 때. `raw`에 응답 원본이 들어 있습니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
uuid = client.get_uuid()
print(uuid.verification_code)
```

## `get_station_info`

역 데이터의 판본과 수록 역 수를 조회합니다.

```python
KorailClient.get_station_info() -> StationInfoResponse
```

본문이 없는 POST를 보냅니다. 응답에 봉투 필드가 없어도 정상 응답으로 읽습니다.
`count`와 `map_version`은 반드시 있어야 합니다. JSON 정수로 오면 문자열로 바꿔 담고, 빈 문자열도 그대로 받습니다.
`count`는 정수로 바꾸지 않은 문자열입니다. 역 목록 자체는 [`get_station_data`](#get_station_data)로 받습니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`StationInfoResponse`][korail_mobile_api.models.StationInfoResponse] — `count`(역 수, 문자열)와 `map_version`(역 데이터 판본)을 담습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 응답에 `count`나 `map_version`이 없거나, `null`이거나, 문자열·정수가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
info = client.get_station_info()
print(info.map_version, info.count)
```

## `get_station_data`

전체 역 목록을 코드·이름·좌표와 함께 받아 옵니다.

```python
KorailClient.get_station_data() -> StationDataResponse
```

본문이 없는 POST를 보냅니다. 응답에 봉투 필드가 없어도 정상 응답으로 읽습니다.
응답의 `stns.stn` 목록은 반드시 있어야 합니다. 역마다 코드(`stn_cd`)와 이름(`stn_nm`)이 응답에서 빠지면 앱과 같이 빈 문자열(`""`)이 되고, `null`이거나 타입이 맞지 않으면 거절합니다.
좌표와 안내 문구 같은 나머지 필드는 없거나 타입이 맞지 않으면 `None`입니다.

[`search_trains`](trains.md#search_trains)에 역 이름 대신 역 코드를 넘기면 라이브러리가 이 메서드로 역 목록을 받아 이름으로 바꿉니다.
이때 만든 역 코드와 이름의 대응표는 클라이언트에 보관해 두고 다시 씁니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`StationDataResponse`][korail_mobile_api.models.StationDataResponse] — `stations`에 역이 [`KorailStation`][korail_mobile_api.models.KorailStation] 튜플로 들어 있습니다. 각 역에는 `code`, `name`, `longitude`, `latitude`, `group`, `major`, `popup_type`, `popup_message`, `popup_link_title`, `popup_link_url`, `area`, `stop`, `raw`가 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 응답에 `stns.stn` 목록이 없을 때, 목록에 객체가 아닌 행이 있을 때, 역 코드나 이름이 `null`이거나 문자열·정수가 아닐 때 |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
stations = client.get_station_data().stations
seoul = next(station for station in stations if station.name == "서울")
print(seoul.code, seoul.latitude, seoul.longitude)
```

## `get_train_calendar`

지금 예매할 수 있는 운행일 달력을 받아 옵니다.

```python
KorailClient.get_train_calendar() -> TrainCalendarResponse
```

공통 필드와 `timeStamp`(호출 시각)를 실어 요청합니다.
날짜마다 운행일(`run_date`)과 여러 구분 코드, 운행 플래그 일곱 개를 담습니다. 이 코드와 플래그의 뜻은 앱 내부 값이 공개돼 있지 않아 라이브러리가 해석하지 않고 서버 값을 그대로 담습니다.
앱은 이 달력으로 출발일이 성수기인지 판단하지만, 판정 기준값이 앱 내부 값이라 공개돼 있지 않아 라이브러리는 판단하지 않습니다. [`search_trains`](trains.md#search_trains)의 `peak_season`은 호출자가 정합니다.

달력 목록(`runningCalendar`)이 없거나 목록이 아니면 빈 `days`를 반환하고, 객체가 아닌 행은 건너뜁니다.

**매개변수**

매개변수가 없습니다.

**반환값**

[`TrainCalendarResponse`][korail_mobile_api.models.TrainCalendarResponse] — `days`에 날짜가 [`TrainCalendarDay`][korail_mobile_api.models.TrainCalendarDay] 튜플로 들어 있습니다. 각 날짜에는 `run_date`, `business_day_stage_code`, `day_division_code`, `holiday_division_code`, `sale_day_division_code`와 `a_train_operation_flag`부터 `x_train_operation_flag`까지의 운행 플래그 일곱 개가 있으며, 없는 값은 `None`입니다.

**예외**

이 메서드에만 해당하는 예외는 없습니다. 공통 예외는 [API 레퍼런스 개요](index.md#공통-예외)를 참고하세요.

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
calendar = client.get_train_calendar()
run_dates = [day.run_date for day in calendar.days if day.run_date]
print(len(run_dates), run_dates[:3])
```

## `get_crew_request_list`

승무원 호출 화면에 띄울 요청 사유 목록을 조회합니다.

```python
KorailClient.get_crew_request_list(
    *,
    timestamp_ms: int | None = None,
) -> CrewRequestListResponse
```

공통 필드와 `timeStamp`를 실어 요청합니다.
사유마다 메시지 코드와 문구를 담습니다. 사유 목록(`prsList`)이 없거나 목록이 아니면 `items`는 빈 튜플이고, 객체가 아닌 행은 건너뜁니다.
이 메서드는 선택지만 조회합니다. 승무원 호출 요청을 보내는 메서드는 없습니다.

**매개변수**

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `timestamp_ms` | `int` \| `None` | `None` | 요청의 `timeStamp` 값(밀리초 단위 epoch)입니다. `None`이면 호출 시각을 씁니다. 넘긴 값은 검사하지 않습니다. |

**반환값**

[`CrewRequestListResponse`][korail_mobile_api.read_models.CrewRequestListResponse] — `items`에 사유가 [`CrewRequestOption`][korail_mobile_api.read_models.CrewRequestOption] 튜플로 들어 있습니다. 각 사유에는 `message_code`, `content`, `raw`가 있습니다.

**예외**

| 예외 | 발생 조건 |
|---|---|
| [`KorailProtocolError`][korail_mobile_api.errors.KorailProtocolError] | 응답의 `strResult`가 `SUCC`도 `FAIL`도 아닐 때. `FAIL`이면 공통 예외인 [`KorailAppError`][korail_mobile_api.errors.KorailAppError]가 발생합니다. |

**정보**

| 로그인 | 대기열 | 상태 변경 | 실서버 확인 |
|:-:|:-:|:-:|:-:|
| 필요 없음 | - | 아니요 | 확인됨 |

**예제**

```python
for option in client.get_crew_request_list().items:
    print(option.message_code, option.content)
```
