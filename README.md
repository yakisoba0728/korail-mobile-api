# korail-mobile-api

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)

KORAIL(한국철도공사) 안드로이드 앱이 쓰는 API 를 파이썬에서 그대로 호출하는
클라이언트입니다. 로그인·열차 검색·승차권 조회는 바로 되고, 좌석을 잡거나
취소·결제·환불하는 것은 명시적인 consent 객체 뒤에서만 일어납니다.

> [!WARNING]
> - **공개 문서가 아니라 리버스 엔지니어링의 결과입니다.** 라우트·필드명·상태코드는
>   `com.korail.talk` 6.5.0 APK 에서 읽어낸 것이고, KORAIL 은 규격을 공개하지도 안정성을
>   약속하지도 않습니다.
> - **실서비스에 붙습니다.** `smart.letskorail.com` 은 실제 발권 시스템이라, 여기서 만든
>   예약은 누군가 취소해야 하는 진짜 예약이고 결제는 진짜 돈입니다.
> - **KORAIL 과 제휴·후원·지원 관계가 없습니다.** 본인 계정을 써야 하고 결과는 본인이
>   감당해야 합니다. 무보증입니다. 취약점 제보는 [SECURITY.md](SECURITY.md) 참고.

## 설치

PyPI 배포는 없습니다. 저장소에서 바로 설치하면 됩니다.

```bash
python3 -m pip install "korail-mobile-api @ git+https://github.com/yakisoba0728/korail-mobile-api"
```

| 항목 | 값 |
| --- | --- |
| 파이썬 | 3.11 이상 |
| 런타임 의존성 | `httpx`, `cryptography` — 이 둘뿐입니다 |
| 라이선스 | Apache-2.0, 타입 주석 완비(`py.typed`) |

## 빠른 시작

아래는 읽어오기만 합니다. 상태를 바꾸지 않고 돈도 건드리지 않습니다.

```python
from korail_mobile_api import KorailClient, KorailConfig, TrainSearchQuery

client = KorailClient(KorailConfig(enable_dynapath=True))
client.login("<회원번호·이메일·휴대폰번호 중 하나>", "<비밀번호>")
query = TrainSearchQuery("서울", "부산", "20260810", departure_time="080000")
for train in client.search_trains(query).trains[:5]:
    print(train.train_no, train.departure_time, train.general_availability_name)
client.logout()
client.close()
```

역은 이름(`"서울"`)으로도 코드로도 넘길 수 있고, 날짜와 시각은 앱이 쓰는
`YYYYMMDD`·`HHMMSS` 그대로입니다. 다음 쪽은 `result.next_page()` 의 continuation 을
`search_trains(query, continuation=...)` 에 넣어 받으면 됩니다.

### DynaPath — 로그인에 필요합니다

`x-dynapath-m-token` 안티 오토메이션 헤더는 **기본적으로 꺼져 있습니다**. 자동화
탐지를 통과하기 위한 값이라 보낼지 말지를 이 패키지가 대신 정하지 않습니다. 위처럼
`KorailConfig(enable_dynapath=True)` 로 켜지 않고 로그인하면 요청이 나가기 전에
`KorailDynaPathRequiredError` 로 막힙니다. 막히는 곳은 `login.Login` 하나뿐이고,
읽기는 토큰 없이도 나갑니다. 토큰은 설정이 가진 기기 값으로 로컬에서 만들고, 붙는
곳은 `DYNAPATH_ALLOWLIST_PATHS` 의 6개 경로뿐입니다. 기기 값은 합성이고 인스턴스마다
다르므로, 진짜 단말 값을 쓰려면 환경변수로 넘긴 뒤 `KorailClient(build_config_from_env())`
로 만들면 됩니다. 뒤의 두 값은 User-Agent 에도 쓰여서 헤더와 토큰이 서로 다른 단말을
주장하지 않습니다.

```bash
export KORAIL_DYNAPATH_DEVICE_ID="<Settings.Secure.ANDROID_ID, 16 hex chars>"
export KORAIL_DYNAPATH_OS_VERSION="15"          # Build.VERSION.RELEASE
export KORAIL_DYNAPATH_DEVICE_MODEL="SM-S928N"  # Build.MODEL
```

나머지 환경변수는 [docs/verification-record.md](docs/verification-record.md) 참고.

### srt-mobile-api 와 함께 쓸 때

`TrainSearchQuery`, `DiscountCoupon`, `MutationCategory` 는 두 패키지가 모두 export
하지만 **같은 타입이 아닙니다.** 둘 다 쓰려면 별칭으로 import 해야 합니다.

| 이름 | korail | srt |
| --- | --- | --- |
| `TrainSearchQuery.passengers` | `int`, 기본 `1` | `PassengerCounts` |
| `TrainSearchQuery.departure_time` 기본값 | `"000000"` | `"060000"` |
| `DiscountCoupon` | `coupon_no`, `discount_values`, … | `coupon_number`, `discount_rate`, … |
| `MutationCategory` | 7개 값 | 5개 값, 공통은 4개 |

## 무엇을 할 수 있나

이 패키지의 경계에는 라우트 60개와 공개 메서드 77개가 들어 있습니다. 라우트 60개는
읽기 58개에 로그인 POST 와 로그아웃 GET 을 더한 것이고, 변경 라우트 9개는 읽기 전용
허용목록에 올라가지 않습니다. 공개 메서드 77개 가운데 consent 게이트가 걸린 변경
메서드 13개를 뺀 나머지 64개는 로그인·읽기 요청만 보내거나 아무것도 보내지 않습니다.

### 읽기

| 하고 싶은 것 | 메서드 |
| --- | --- |
| 특정 날짜의 열차 | `search_trains(query)`, 다음 쪽은 `result.next_page()` |
| 직통이 없을 때 | `search_trains_with_transfer_fallback(query)`, `search_transfer_trains(query)`, `get_transfer_stations(...)` |
| 객차 목록과 한 객차의 좌석표 | `get_seat_cars(train)`, `get_seat_inventory(train, car_no)` |
| 정차역·운행일·역 목록 | `get_train_schedule(...)`, `get_train_calendar()`, `get_station_data()`, `get_station_info()` |
| 내 승차권·예약 내역·구매 이력 | `get_ticket_list()`, `get_ticket_reservation_detail(request)`, `get_reservation_history()`, `get_product_reservations(...)` |
| 환불 수수료·좌석 변경 여지·반환번호 원표 | `get_refund_commission(ticket)`, `get_refund_ticket_detail(ticket)`, `get_self_seat_change_info(request)`, `get_original_ticket_inquiry(tickets)` |
| 포인트·쿠폰·복지 플래그·마일리지 | `get_korail_point_summary()`, `get_mileage_history(request)` |
| N카드·정기권·리무진버스 | `get_discount_card_usage_history(card_no)`, `get_pass_menu(menu_no)`, `get_pass_schedule(request)`, `get_limousine_schedules(query)`, `get_limousine_seat_inventory(query)`, `get_limousine_schedule_view(query)` |

로그인 없이 되는 계정 무관 읽기도 있습니다: `get_service_status()`, `get_app_data()`,
`get_notice()`, `get_uuid()`, `get_maas_menu_list()`, `get_maas_station_data(...)`.
메서드별 라우트는 [docs/api-status-by-service.md](docs/api-status-by-service.md) 참고.

### 예약

`reserve` 하나가 예약 화면의 네 동작을 덮습니다. 키워드 전용 `job_type` 으로 고르고,
주지 않으면 좌석 미지정 일반 예약이 나갑니다. `KorailPassengerCounts`(승객 행 8종, 합계 9명까지)와 `KorailSeatClass` 도 받습니다.

| `job_type` | `txtJobId` | 무엇을 잡나 |
| --- | --- | --- |
| `IMMEDIATE` (기본) | `1101` | 좌석 미지정 일반 예약 |
| `SEAT_DESIGNATED` | `1103` | 좌석지정 — `get_seat_inventory` 에서 고른 호차·좌석번호 |
| `STANDBY` | `1102` | 예약대기. `confirm_standby_hold` 로 마무리합니다 |
| `MERGE_STANDING` | `1202` | 입석+좌석 병합예약의 첫 hold. 두 번째는 `reserve_merge` |

같은 consent 를 쓰는 진입점이 둘 더 있습니다. `reserve_transfer(legs, ...)` 는 환승을
하나의 PNR 로, `reserve_with_discount_card(train, card_no=...)` 는 할인카드 승객 행
하나를 잡습니다. 그리고 **좌석지정에는 함정이 있습니다.** 폼에 나가는 것은
`KorailSeatAssignment.seat_no` 인데 서버가 돌려주는 것은 `seat_spec` 이므로, 대조할
때는 `seat_spec` 을 `h_seat_no` 와 비교해야 합니다.

### 상태를 바꾸는 것

| 메서드 | consent 범주 | 하는 일 |
| --- | --- | --- |
| `cancel_unpaid_hold(hold, consent=...)` | `cancel` | 결제 전 hold 를 풉니다 |
| `pay_with_fake_card(hold, card, consent=...)` | `payment` | 청구되지 않는 테스트 카드로만 결제합니다 |
| `pay_with_card(hold, card, consent=...)` | `payment` | 실카드로 결제합니다. 기본으로 막혀 있습니다 |
| `refund(ticket, consent=...)` | `refund` | 결제된 승차권을 환불합니다 |
| `recalculate_price(request, consent=...)` | `price_recalculation` | 할인이 바뀐 hold 의 운임을 다시 씁니다 |
| `add_to_cart(request, consent=...)` | `cart` | 이미 잡힌 PNR 을 장바구니에 넣습니다 |
| `register_discount_card(request, consent=...)` | `discount_card` | N카드를 새로 삽니다 |
| `extend_discount_card(ticket, consent=...)` | `discount_card` | N카드를 기간연장합니다 |

### 가상대기실 (NetFunnel)

`KorailNetFunnelClient` 는 `nf.letskorail.com` 의 대기열을 다루는 독립 클라이언트이고
**기본적으로 꺼져 있습니다**. `KorailConfig(netfunnel_enabled=True)` 로 옵트인한 뒤
`with queue.slot(inquiry_action(...))` 안에서 호출하면 됩니다. 핸드셰이크와 반납은
확인했지만 **대기 경로는 실서버에서 한 번도 돌지 않았습니다** — 폴링 루프와 ttl
대기는 오프라인 픽스처로만 덮여 있습니다.

## 안전 모델

관례가 아니라 코드로 강제하고, 오프라인 스위트가 고정합니다.

1. 변경 메서드 13개는 전부 `require_mutation_consent(consent, category)` 로 시작해
   `KorailMutationNotAllowedError` 를 올립니다. 이걸 끄는 스위치는 없습니다.
2. `MutationConsent` 의 범주별 플래그(`allow_reserve`, `allow_payment`,
   `allow_cancel`, `allow_refund`, `allow_discount_card`, `allow_price_recalculation`,
   `allow_cart`)는 전부 기본 `False` 라, 예약을 허가한 consent 로 취소할 수 없습니다.
3. `dry_run=True` 가 기본이고, dry run 은 아무것도 보내지 않습니다. 보냈을 폼을 담은
   `MutationPreview` 를 돌려주는데, 그 payload 는 `redact_payload` 를 지납니다.
4. `KorailHttpClient.post_mutation_form` 이 변경 라우트에 닿을 수 있는 유일한
   메서드입니다. consent 를 다시 검사하고, 알려진 변경 라우트인지와 주장한 범주에
   속하는지를 둘 다 단언합니다.
5. 청구되는 실카드는 **오직** `pay_with_card` 로만 갈 수 있고, `real_card_acknowledged`
   와 `fake_card_only=False` 를 **둘 다** 세운 consent 여야 합니다. 하나만 세운 모호한
   consent 는 전송 게이트가 거절합니다.

```python
from korail_mobile_api import MutationConsent

preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
preview.payload    # 마스킹됨. 프로세스 밖으로 나간 것이 없습니다
hold = client.reserve(train, consent=MutationConsent(allow_reserve=True, dry_run=False))
client.cancel_unpaid_hold(hold, consent=MutationConsent(allow_cancel=True, dry_run=False))
```

## 에러 처리

서버 쪽 실패는 앱 자신이 분기하는 필드인 `h_msg_cd` 로 분류합니다. 한국어 메시지 문구로는 분류하지 않습니다. 아래 표의 위 열 개는 `KorailAppError` 의 하위 타입입니다.

### 에러 분류

| 예외 | 코드 | 호출자가 할 일 |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | **아무것도 없었습니다.** 요청 자체는 정상입니다. 재시도는 소용없습니다. 다른 질문을 해야 합니다. |
| `KorailNoDirectTrainError` | `WRD000061` | *직통*이 없습니다. 환승 검색으로 다시 물으면 됩니다. |
| `KorailSoldOutError` | `ERR211161` | **재고가 없습니다.** 이 열차는 재시도해도 소용없습니다. 다른 열차를 골라야 합니다. |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | 열차가 아니라 *좌석*이 문제입니다. 좌석지정을 **빼고** 다시 하면 될 수 있습니다. |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | 예약이 거절됐습니다. 이유는 `message` 에 있습니다. |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | **payload 를 고쳐야 합니다.** 그대로 재시도해도 소용없습니다. |
| `KorailNotEntitledError` | `ERR299943`* | **이 계정은 그 운임을 살 자격이 없습니다.** 요청 모양은 맞습니다. |
| `KorailServiceUnavailableError` | `SEMGTK` | 요청이 아니라 백엔드가 죽었습니다. |
| `KorailAppUpdateRequiredError` | `SUPDATE` | 이 클라이언트 버전이 거부됐습니다. 아래의 위장된 경우와 구별해야 합니다. |
| `KorailAppError` | 그 밖의 전부 | 미분류입니다. `code` 와 `raw` 는 그대로 있습니다. |
| `KorailSessionExpiredError` | `P058` | **다시 로그인해야 합니다.** 의도적으로 `KorailAppError` 가 *아닙니다*. |
| `KorailDynaPathError` | *(코드 없음 — 응답 헤더)* | 스로틀이 아니라 플래그가 걸린 것입니다. |

올리지 않고 매핑만 원하면 `classify_app_error` 를 쓰면 됩니다. `*` 가 붙은 코드는 APK
분기가 아니라 실서버 관측이고, 어느 쪽이 어느 쪽인지와 일부러 분류하지 않고 남겨 둔
관측 하나는 [docs/verification-record.md](docs/verification-record.md) 에 있습니다.
성공 응답에 붙은 경고 코드는 성공으로 남습니다. 그리고 **이 라이브러리는 스스로
재시도하지 않습니다.** 특히 `reserve` 는 절대 재시도하지 않습니다.
재시도한 예약은 중복 예약이기 때문입니다.

### 안티 매크로 거부가 버전 문제처럼 보입니다

**`login` 이 앱을 업데이트하라고 하면 대개 앱 버전 문제가 아닙니다.** 로그인 검사는
앱처럼 보이지 않는 클라이언트에 `MACRO ERROR` 로 답하면서, 사용자에게는
*"원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…"* 를 내보냅니다. 진짜
버전 게이트는 전부를 거절하므로, `get_app_data()` 는 정상인데 `login` 만 실패하는지
보고 `error.code` 가 `SUPDATE` 인지 읽으면 구별됩니다.

## 한계

요청을 만들 수 있다는 것과 서버가 받아 준다는 것은 다릅니다. 연산별 상태는 [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) 가 추적합니다.

| 상태 | 대상 |
| --- | --- |
| 왕복까지 실서버 확인 | 즉시·좌석지정·예약대기·입석+좌석 hold, `confirm_standby_hold`, `cancel_unpaid_hold`, `add_to_cart`, 청구 없이 거절된 `pay_with_fake_card` 시도 |
| 업무 응답을 준 읽기 | `get_self_seat_change_info` 가 `WRT800176 좌석변경가능시간아님` 을 돌려줬습니다 |
| 만들었지만 보내지 않음 | `pay_with_card`, `refund`, `reserve_merge`, `recalculate_price`, 할인카드 표면 전체, 그리고 발권된 승차권의 반환번호가 필요한 `get_original_ticket_inquiry` |

**환승은 구현했고 실서버 검증 안 됨.** `search_transfer_trains` 와 `reserve_transfer`
는 보낸 적이 없습니다. `get_transfer_stations` 로는 싸게 찔러볼 수 있지만 실환승 hold 는
KORAIL 앱에서 취소할 준비가 되어 있지 않으면 보내면 안 됩니다.

일부러 구현하지 않은 것도 있습니다.

- **신원 서류 제출** — 주민등록번호 조각과 정부 증명서 번호를 전송하는데 검증할 수 없습니다.
- **비밀번호를 싣는 포인트 라우트** — 틀린 추측을 반복하면 계정이 잠깁니다.
- **정기권 구매** — 결제액이 15만~25만원인데 취소·환불 라우트가 없습니다.
- **승차권 여행변경과 그 롤백, 예약 인원 변경** — 깨끗한 되돌리기가 없습니다.
- **비회원 오프라인 반환, 체크인, 회원정보·포인트 변경** — 이 버전에는 없습니다.
- **승무원 호출 제출** — `/classes/com.korail.mobile.push.callCrew.do` 는 transport 허용목록에서 계속 제외되어 있습니다.
- **인증 우회, NetFunnel·DynaPath 우회, 범용 WebView 자동화** — 영구히 범위 밖입니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [docs/verification-record.md](docs/verification-record.md) | 근거 기록: APK 인용, 실행별 코드, 정정 |
| [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) | 변경 표면의 검증 상태 |
| [docs/api-status-by-service.md](docs/api-status-by-service.md) | Retrofit 항목 165개의 서비스별 상태 |
| [docs/RELEASE.md](docs/RELEASE.md) | 릴리스 게이트 |
| [CHANGELOG.md](CHANGELOG.md) | 무엇이 바뀌었나 |

`python3 -m pytest -q -m "not live"` 가 게이트이고 네트워크를 쓰지 않습니다:
`2436 passed, 1 deselected`. 빠진 하나는 `KORAIL_MOBILE_API_LIVE=1` 과 직접 마련한
자격증명이 함께 있을 때만 도는 실서버 테스트입니다. 기여는
[CONTRIBUTING.md](CONTRIBUTING.md), 규범은 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 참고.

## 라이선스

Apache License 2.0 — [LICENSE](LICENSE) 와 [NOTICE](NOTICE) 참고.
