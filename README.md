<div align="center">

# korail-mobile-api

**KORAIL 앱이 쓰는 API 를, 파이썬에서 그대로.**

로그인하고, 열차를 찾고, 승차권과 예약을 읽습니다.<br>
좌석을 잡거나 결제·환불하는 일은 consent 객체를 건네야만 일어납니다.

[![문서](https://img.shields.io/badge/%EB%AC%B8%EC%84%9C-yaki.kr-1f6feb?style=flat-square)](https://yaki.kr/korail-mobile-api/)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![타입](https://img.shields.io/badge/typed-py.typed-2f6f4e?style=flat-square)](src/korail_mobile_api/py.typed)
[![오프라인 테스트](https://img.shields.io/badge/offline%20tests-2443-4c1?style=flat-square)](#문서)
[![License](https://img.shields.io/badge/license-Apache--2.0-green?style=flat-square)](LICENSE)

[문서](https://yaki.kr/korail-mobile-api/) ·
[빠른 시작](#빠른-시작) ·
[무엇을 할 수 있나](#무엇을-할-수-있나) ·
[안전 모델](#안전-모델) ·
[에러 처리](#에러-처리) ·
[한계](#한계)

</div>

---

> [!WARNING]
> - **리버스 엔지니어링 결과입니다.** 라우트와 필드명은 `com.korail.talk` 6.5.0
>   APK 에서 읽어냈습니다. KORAIL 은 규격을 공개하지 않고 안정성도 약속하지 않습니다.
> - **실서비스입니다.** `smart.letskorail.com` 은 진짜 발권 시스템입니다. 여기서
>   만든 예약은 누군가 취소해야 하고, 결제는 진짜 돈입니다.
> - **KORAIL 과 아무 관계가 없습니다.** 본인 계정으로, 본인 책임으로 쓰세요.
>   무보증입니다. 취약점은 [SECURITY.md](SECURITY.md) 로 알려주세요.

## 설치

PyPI 에는 올리지 않았습니다. 저장소에서 바로 받으면 됩니다.

```bash
python3 -m pip install "korail-mobile-api @ git+https://github.com/yakisoba0728/korail-mobile-api"
```

| 항목 | 값 |
| --- | --- |
| 파이썬 | 3.11 이상 |
| 의존성 | `httpx`, `cryptography` |
| 타입 | `py.typed` 동봉 |

## 빠른 시작

읽기만 하는 예제입니다.

```python
from korail_mobile_api import KorailClient, KorailConfig, TrainSearchQuery

client = KorailClient(KorailConfig(enable_dynapath=True))
client.login("<회원번호·이메일·휴대폰번호>", "<비밀번호>")
query = TrainSearchQuery("서울", "부산", "20260810", departure_time="080000")
for train in client.search_trains(query).trains[:5]:
    print(train.train_no, train.departure_time, train.general_availability_name)
client.logout()
client.close()
```

역은 이름으로도 코드로도 넘깁니다. 날짜는 `YYYYMMDD`, 시각은 `HHMMSS` 로 앱과
같습니다. 다음 쪽은 `result.next_page()` 를 `search_trains(query, continuation=...)`
에 넣어 받습니다.

### DynaPath

`x-dynapath-m-token` 은 앱의 안티 오토메이션 헤더입니다. **기본은 꺼짐**이고
`KorailConfig(enable_dynapath=True)` 로 켭니다. 자동화 탐지를 통과하려는 값이라
보낼지 말지를 이 패키지가 정하지 않습니다.

켜지 않고 로그인하면 나가기 전에 `KorailDynaPathRequiredError` 로 막힙니다. 막히는
건 `login.Login` 하나고 읽기는 토큰 없이도 나갑니다. 켜면
`DYNAPATH_ALLOWLIST_PATHS` 의 6개 경로에만 붙습니다. 기기 값은 합성이니, 진짜 단말
값을 쓰려면 환경변수로 넘기고 `KorailClient(build_config_from_env())` 로 만듭니다.

```bash
export KORAIL_DYNAPATH_DEVICE_ID="<Settings.Secure.ANDROID_ID, 16 hex>"
export KORAIL_DYNAPATH_OS_VERSION="15"          # Build.VERSION.RELEASE
export KORAIL_DYNAPATH_DEVICE_MODEL="SM-S928N"  # Build.MODEL
```

<details>
<summary><b>이 값들을 어디서 구하나</b></summary>

기기를 USB 디버깅으로 연결하고 `adb` 로 읽으면 됩니다.

| 환경변수 | 원본 | 명령 |
| --- | --- | --- |
| `KORAIL_DYNAPATH_DEVICE_ID` | `Settings.Secure.ANDROID_ID` | `adb shell settings get secure android_id` |
| `KORAIL_DYNAPATH_OS_VERSION` | `Build.VERSION.RELEASE` | `adb shell getprop ro.build.version.release` |
| `KORAIL_DYNAPATH_DEVICE_MODEL` | `Build.MODEL` | `adb shell getprop ro.product.model` |

`ANDROID_ID` 는 안드로이드 8부터 앱 서명키별로 갈립니다. `adb shell` 이 보는 값은
KORAIL 앱이 보는 값과 다릅니다. 이 라이브러리에는 상관없습니다 — `di` 가 필요로 하는
건 16자 hex 이고, env 경로를 쓰는 이유는 값이 진짜여서가 아니라 프로세스를 넘어
**안정적**이기 때문입니다. 합성 기본값으로도 실서버 로그인이 됩니다(2026-07-31 확인).

</details>

<details>
<summary><b>앱 버전과 API 버전은 다릅니다</b></summary>

요청에 실리는 `Version=250601003` 은 앱 버전(`6.5.0`)도 versionCode(`60500002`)도
아닌 별개 상수입니다. APK 안에 있어서 기기 속성으로는 나오지 않습니다.

```bash
adb shell dumpsys package com.korail.talk | grep versionName   # 6.5.0
adb shell pm path com.korail.talk                              # APK 경로
adb pull <위 경로>
unzip -p base.apk 'classes*.dex' | strings | grep -m1 'Device=AD&Version='
# Device=AD&Version=250601003&Key=korail1234567890
```

마지막 줄이 모든 요청에 실리는 공통 세 필드입니다 — 차례로
`KORAIL_DEVICE_ANDROID`, `KORAIL_API_VERSION`, `KORAIL_APP_KEY` 입니다. 서버가 최소
버전을 올리면 여기를 갱신해야 합니다.

</details>

<details>
<summary><b>srt-mobile-api 와 같이 쓸 때</b></summary>

이름이 겹치는데 타입이 다릅니다. 둘 다 쓴다면 별칭으로 import 하세요.

| 이름 | korail | srt |
| --- | --- | --- |
| `TrainSearchQuery.passengers` | `int`, 기본 `1` | `PassengerCounts` |
| `TrainSearchQuery.departure_time` | `"000000"` | `"060000"` |
| `DiscountCoupon` | `coupon_no`, `discount_values` | `coupon_number`, `discount_rate` |
| `MutationCategory` | 7개 | 5개 (공통 4개) |

</details>

## 무엇을 할 수 있나

경계 안에 라우트 60개와 공개 메서드 77개가 있습니다. 라우트는 읽기 58개에
로그인·로그아웃을 더한 것이고, 변경 라우트 9개는 읽기 전용 허용목록에 올라가지
않습니다. 메서드 중 변경 메서드 13개가 consent 게이트를 지나고, 나머지 64개는
로그인·읽기만 보내거나 아무것도 보내지 않습니다.

### 읽기

| 하고 싶은 것 | 메서드 |
| --- | --- |
| 날짜별 열차 | `search_trains(query)` |
| 직통이 없을 때 | `search_trains_with_transfer_fallback(query)`, `search_transfer_trains(query)`, `get_transfer_stations(...)` |
| 객차와 좌석표 | `get_seat_cars(train)`, `get_seat_inventory(train, car_no)` |
| 정차역·운행일·역 목록 | `get_train_schedule(...)`, `get_train_calendar()`, `get_station_data()`, `get_station_info()` |
| 승차권·예약·구매 이력 | `get_ticket_list()`, `get_ticket_reservation_detail(request)`, `get_reservation_history()`, `get_product_reservations(...)` |
| 환불 수수료·좌석 변경·원표 | `get_refund_commission(ticket)`, `get_refund_ticket_detail(ticket)`, `get_self_seat_change_info(request)`, `get_original_ticket_inquiry(tickets)` |
| 포인트·마일리지 | `get_korail_point_summary()`, `get_mileage_history(request)` |
| N카드·정기권·리무진 | `get_discount_card_usage_history(card_no)`, `get_pass_menu(menu_no)`, `get_pass_schedule(request)`, `get_limousine_schedules(query)`, `get_limousine_seat_inventory(query)`, `get_limousine_schedule_view(query)` |

로그인 없이 되는 것도 있습니다. `get_service_status()`, `get_app_data()`,
`get_notice()`, `get_uuid()`, `get_maas_menu_list()` 가 그렇습니다. 메서드별 라우트는
[docs/api-status-by-service.md](docs/api-status-by-service.md) 에 있습니다.

### 예약

`reserve` 하나가 예약 화면의 네 동작을 덮습니다. `job_type` 으로 고르고, 생략하면
좌석 미지정입니다. 승객은 `KorailPassengerCounts`(8종, 합계 9명까지), 등급은
`KorailSeatClass` 로 넘깁니다.

| `job_type` | `txtJobId` | 무엇을 잡나 |
| --- | --- | --- |
| `IMMEDIATE` (기본) | `1101` | 좌석 미지정 |
| `SEAT_DESIGNATED` | `1103` | 좌석지정 |
| `STANDBY` | `1102` | 예약대기 — `confirm_standby_hold` 로 마무리 |
| `MERGE_STANDING` | `1202` | 입석+좌석 병합의 첫 hold — 두 번째는 `reserve_merge` |

환승은 `reserve_transfer(legs, ...)`, 할인카드 승객은
`reserve_with_discount_card(train, card_no=...)` 입니다. 좌석지정에는 함정이
있습니다 — 폼에 나가는 건 `KorailSeatAssignment.seat_no` 인데 서버가 돌려주는 건
`seat_spec` 이라, 대조는 `seat_spec` 과 `h_seat_no` 로 해야 합니다.

### 상태를 바꾸는 것

| 메서드 | consent | 하는 일 |
| --- | --- | --- |
| `cancel_unpaid_hold(hold, …)` | `cancel` | 결제 전 hold 해제 |
| `pay_with_fake_card(hold, card, …)` | `payment` | 청구되지 않는 테스트 카드 |
| `pay_with_card(hold, card, …)` | `payment` | 실카드. 기본으로 막힘 |
| `refund(ticket, …)` | `refund` | 결제된 승차권 환불 |
| `recalculate_price(request, …)` | `price_recalculation` | 할인 바뀐 hold 의 운임 재계산 |
| `add_to_cart(request, …)` | `cart` | 잡힌 PNR 을 장바구니로 |
| `register_discount_card(request, …)` | `discount_card` | N카드 구매 |
| `extend_discount_card(ticket, …)` | `discount_card` | N카드 기간연장 |

### 가상대기실

`KorailNetFunnelClient` 가 `nf.letskorail.com` 의 대기열을 다룹니다.
**기본적으로 꺼져 있습니다.** `KorailConfig(netfunnel_enabled=True)` 로 켠 뒤
`with queue.slot(inquiry_action(...))` 안에서 부릅니다. 핸드셰이크와 반납은
확인했지만 **대기 경로는 실서버에서 한 번도 돌지 않았습니다.**

## 안전 모델

관례가 아니라 코드가 막고, 오프라인 스위트가 그걸 고정합니다.

- 변경 메서드 13개는 전부 `require_mutation_consent` 로 시작합니다. 끄는 스위치는 없습니다.
- 범주 플래그는 전부 기본 `False` 라, 예약을 허가한 consent 로는 취소하지 못합니다.
- `dry_run=True` 가 기본입니다. 통신하지 않고 `MutationPreview` 만 돌려주며 payload 는
  `redact_payload` 를 지납니다.
- 변경 라우트에 닿는 메서드는 `post_mutation_form` 뿐이고, 라우트와 범주가 맞는지 다시 봅니다.
- 청구되는 실카드는 `pay_with_card` 로만 갑니다. `real_card_acknowledged` 와
  `fake_card_only=False` 를 **둘 다** 세워야 하고, 하나만 세우면 전송 게이트가 거절합니다.

```python
from korail_mobile_api import MutationConsent

preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
preview.payload    # 마스킹된 폼. 아무것도 나가지 않았습니다
hold = client.reserve(train, consent=MutationConsent(allow_reserve=True, dry_run=False))
client.cancel_unpaid_hold(hold, consent=MutationConsent(allow_cancel=True, dry_run=False))
```

## 에러 처리

서버 실패는 앱이 실제로 분기하는 `h_msg_cd` 로 가릅니다. 한국어 문구로는 가르지
않습니다. 아래 위 열 개가 `KorailAppError` 의 하위 타입입니다.

### 에러 분류

| 예외 | 코드 | 뜻과 다음 수 |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | 결과가 없습니다. 요청은 정상이니 조건을 바꿔야 합니다 |
| `KorailNoDirectTrainError` | `WRD000061` | 직통이 없습니다. 환승으로 다시 물으면 됩니다 |
| `KorailSoldOutError` | `ERR211161` | 매진입니다. 다른 열차를 골라야 합니다 |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | 열차가 아니라 좌석 문제입니다. 좌석지정을 빼면 될 수 있습니다 |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | 예약 거절입니다. 이유는 `message` 에 있습니다 |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | payload 가 틀렸습니다. 고쳐야 합니다 |
| `KorailNotEntitledError` | `ERR299943`* | 이 계정은 그 운임을 살 자격이 없습니다 |
| `KorailServiceUnavailableError` | `SEMGTK` | 백엔드가 죽었습니다 |
| `KorailAppUpdateRequiredError` | `SUPDATE` | 클라이언트 버전 거부. 아래 위장된 경우와 다릅니다 |
| `KorailAppError` | 나머지 | 미분류. `code` 와 `raw` 는 그대로입니다 |
| `KorailSessionExpiredError` | `P058` | 세션이 끊겼으니 다시 로그인해야 합니다. `KorailAppError` 가 아닙니다 |
| `KorailDynaPathError` | *(응답 헤더)* | 스로틀이 아니라 플래그가 걸린 겁니다 |

예외 없이 매핑만 보려면 `classify_app_error` 를 씁니다. `*` 는 APK 분기가 아니라
실서버 관측이고, 어느 쪽이 어느 쪽인지와 **일부러 분류하지 않고 남겨 둔 관측 하나**는
[docs/verification-record.md](docs/verification-record.md) 에 있습니다. 경고 코드가
붙은 성공 응답은 **성공으로 남습니다.**

**이 라이브러리는 스스로 재시도하지 않습니다.** 재시도한 예약은 중복 예약이기 때문입니다.

### 앱 업데이트하라는 말이 진짜 버전 문제가 아닐 때

로그인이 실패하면서 앱을 업데이트하라고 하면 대개 버전 문제가 아닙니다. 앱처럼
보이지 않는 클라이언트에 서버가 `MACRO ERROR` 로 답하면서, 사용자에게는
*"원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…"* 를 보여줍니다.
진짜 버전 게이트는 전부를 막으니, `get_app_data()` 는 되는데 `login` 만 실패하는지
보고 `error.code` 가 `SUPDATE` 인지 확인하면 갈립니다.

## 한계

요청을 만들 수 있는 것과 서버가 받아주는 것은 다릅니다. 연산별 상태는
[docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) 에 있습니다.

| 상태 | 대상 |
| --- | --- |
| 왕복까지 확인 | 즉시·좌석지정·예약대기·입석+좌석 hold, `confirm_standby_hold`, `cancel_unpaid_hold`, `add_to_cart`, 청구 없이 거절된 `pay_with_fake_card`, 실카드 `pay_with_card` 와 `refund` |
| 업무 응답을 받음 | `get_self_seat_change_info` → `WRT800176 좌석변경가능시간아님` |
| 만들었지만 보낸 적 없음 | `reserve_merge`, `recalculate_price`, 할인카드 전체, `get_original_ticket_inquiry` |

`pay_with_card` 와 `refund` 는 2026-07-31 에 실제 돈으로 확인했습니다. 서울→광명
8,400원 승차권 한 장을 출발 31일 전에 사고 바로 반환했습니다 — 결제
`IRT000000 정상발매처리,정상발권처리`, 반환 `IRT200277 반환이 정상 처리되었습니다`,
수수료 0원, 계정은 예약 0건으로 복귀. 확인된 것은 **개인 신용카드 일시불 한 건**
뿐입니다. 할부·법인카드·복수 승객·부분 환불은 여전히 미확인이고, 출발일에 가까운
반환은 수수료가 붙습니다 — 금액은 `get_refund_commission` 이 서버에서 읽어 옵니다.

**환승은 구현했고 실서버 검증 안 됨.** `search_transfer_trains` 와 `reserve_transfer`
는 보낸 적이 없습니다. 실환승 hold 는
KORAIL 앱에서 취소할 준비가 되어 있지 않으면 보내면 안 됩니다.

일부러 넣지 않은 것도 있습니다.

- **신원 서류 제출** — 주민등록번호 조각을 보내는데 검증할 방법이 없습니다.
- **비밀번호를 싣는 포인트 라우트** — 틀리면 계정이 잠깁니다.
- **정기권 구매** — 15만~25만원인데 취소·환불 라우트가 없습니다.
- **여행변경과 롤백, 예약 인원 변경** — 깨끗한 되돌리기가 없습니다.
- **비회원 오프라인 반환, 체크인, 회원정보 변경** — 이 버전에 없습니다.
- **승무원 호출** — `/classes/com.korail.mobile.push.callCrew.do` 는 transport
  허용목록에서 계속 제외되어 있습니다.
- **인증·NetFunnel·DynaPath 우회, 범용 WebView 자동화** — 영구히 범위 밖입니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [문서 사이트](https://yaki.kr/korail-mobile-api/) | 이 README 와 API 레퍼런스를 합쳐 놓은 것 |
| [docs/verification-record.md](docs/verification-record.md) | 근거 기록. APK 인용, 실행별 코드, 정정 |
| [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) | 변경 표면의 검증 상태 |
| [docs/api-status-by-service.md](docs/api-status-by-service.md) | Retrofit 항목 165개의 서비스별 상태 |
| [docs/RELEASE.md](docs/RELEASE.md) | 릴리스 게이트 |
| [docs/README.md](docs/README.md) | 문서 전체 색인 |
| [CHANGELOG.md](CHANGELOG.md) | 무엇이 바뀌었나 |

게이트는 `python3 -m pytest -q -m "not live"` 이고 네트워크를 쓰지 않습니다 —
`2443 passed, 1 deselected`. 빠진 하나는 `KORAIL_MOBILE_API_LIVE=1` 이 있을 때만 도는
실서버 테스트입니다. 기여는 [CONTRIBUTING.md](CONTRIBUTING.md), 규범은
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 참고.

## 라이선스

Apache License 2.0 — [LICENSE](LICENSE), [NOTICE](NOTICE).
