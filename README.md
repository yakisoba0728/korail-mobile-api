# korail-mobile-api

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

KORAIL(한국철도공사) 안드로이드 앱이 쓰는 API 를 파이썬에서 그대로 호출하는
클라이언트입니다. 로그인·열차 검색·승차권 조회는 바로 되고, 좌석을 잡거나
취소·결제·환불하는 것은 명시적인 consent 객체 뒤에서만 일어납니다. 보내는 경로와
폼 필드는 앱이 보내는 것과 같습니다.

> [!WARNING]
> - **공개 문서가 아니라 리버스 엔지니어링의 결과입니다.** 여기의 라우트·필드명·
>   상태코드는 `com.korail.talk` 6.5.0 APK 를 디컴파일해 읽어낸 것입니다. KORAIL 은
>   규격을 공개하지 않고 안정성도 약속하지 않습니다.
> - **실서비스에 붙습니다.** `smart.letskorail.com` 은 실제 발권 시스템입니다. 이
>   라이브러리가 만든 예약은 누군가 취소해야 하는 진짜 예약이고, 결제는 진짜 돈입니다.
> - **KORAIL 과 제휴·후원·지원 관계가 없습니다.** 본인 계정을 써야 하고 결과는 본인이
>   감당해야 합니다. 무보증입니다. 취약점 제보는 [SECURITY.md](SECURITY.md) 를 먼저
>   읽어야 합니다.

## 설치

PyPI 배포는 없습니다. 저장소에서 바로 설치하면 됩니다.

```bash
python3 -m pip install "korail-mobile-api @ git+https://github.com/yakisoba0728/korail-mobile-api"
```

| 항목 | 값 |
| --- | --- |
| 파이썬 | 3.11 이상 (`requires-python = ">=3.11"`) |
| 런타임 의존성 | `httpx`, `cryptography` — 이 둘뿐입니다 |
| 타입 | 타입 주석 완비, `py.typed` 동봉 |
| 라이선스 | Apache-2.0 |

고쳐 쓸 체크아웃이라면 개발 설치를 하고 오프라인 스위트를 한 번 돌리면 됩니다.

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest -q -m "not live"
```

## 빠른 시작

아래는 로그인하고 검색하고 읽어오기만 합니다. 상태를 바꾸지 않고 돈도 건드리지
않습니다.

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
client.login("<회원번호·이메일·휴대폰번호 중 하나>", "<비밀번호>")

result = client.search_trains(
    TrainSearchQuery("서울", "부산", "20260810", departure_time="080000")
)
for train in result.trains[:5]:
    print(
        train.train_no,
        train.departure_time,
        train.arrival_time,
        train.general_availability_name,   # 예약가능 / 매진 / …
    )

summary = client.get_korail_point_summary()
print(summary.korail_point, summary.discount_coupon_count)

client.logout()
client.close()
```

역은 이름(`"서울"`)으로도 코드로도 넘길 수 있고, 날짜와 시각은 앱이 쓰는
`YYYYMMDD`·`HHMMSS` 문자열 그대로입니다. 다음 페이지는 `result.next_page()` 가
돌려주는 continuation 을 `search_trains(query, continuation=...)` 에 다시 넣어
받으면 됩니다.

네 가지 파라미터는 `str` 이 아니라 `Literal` 별칭이라 편집기가 값을 완성해 줍니다:
`MutationCategory`, `KorailMileageLedger`, `KorailMileageMovement`,
`KorailSelfSeatChangeRoomClassCode`. 그 밖의 코드값은 서버가 얼마든지 새로 만들 수
있으므로 `str` 로 둡니다.

### DynaPath — 로그인에 필요합니다

`x-dynapath-m-token` 안티 오토메이션 헤더는 **기본적으로 꺼져 있습니다**. 자동화
탐지를 통과하기 위한 값이라 보낼지 말지를 이 패키지가 대신 정하지 않습니다.

```python
from korail_mobile_api import KorailClient, KorailConfig

client = KorailClient(KorailConfig(enable_dynapath=True))
client.login("<회원번호·이메일·휴대폰번호 중 하나>", "<비밀번호>")
```

켜지 않고 로그인하면 요청이 나가기 전에 `KorailDynaPathRequiredError` 로 막히고,
무엇을 켜야 하는지 예외 메시지가 알려 줍니다. 막히는 곳은 `login.Login`
하나뿐이고, 검색을 비롯한 읽기는 토큰 없이도 나갑니다.

토큰은 설정이 가진 기기 값으로 로컬에서 만들고, 붙는 곳은 앱이 붙이는
`DYNAPATH_ALLOWLIST_PATHS` 의 6개 경로뿐입니다. 기기 값은 **합성이고 인스턴스마다
다릅니다** — 모든 설치본이 공통으로 보내는 식별자야말로 안티 매크로 검사가 찾는
것이기 때문입니다. 진짜 단말 값을 실행 간에 고정하려면 환경변수로 넘기면 됩니다.

```bash
export KORAIL_DYNAPATH_DEVICE_ID="<Settings.Secure.ANDROID_ID, 16 hex chars>"
export KORAIL_DYNAPATH_OS_VERSION="15"          # Build.VERSION.RELEASE
export KORAIL_DYNAPATH_DEVICE_MODEL="SM-S928N"  # Build.MODEL
```

```python
from korail_mobile_api import KorailClient, build_config_from_env

client = KorailClient(build_config_from_env())
```

뒤의 두 값은 토큰과 User-Agent 양쪽에 쓰이므로 헤더와 토큰이 서로 다른 단말을
주장하는 일이 없습니다. 나머지 환경변수와 각 기본값의 근거는
[docs/verification-record.md](docs/verification-record.md) 에 있습니다.

### srt-mobile-api 와 함께 쓸 때

`TrainSearchQuery`, `DiscountCoupon`, `MutationCategory` 는 두 패키지가 모두
export 하지만 **같은 타입이 아닙니다.**

| 이름 | korail | srt |
| --- | --- | --- |
| `TrainSearchQuery.passengers` | `int`, 기본 `1` | `PassengerCounts` |
| `TrainSearchQuery.departure_time` 기본값 | `"000000"` | `"060000"` |
| `DiscountCoupon` | `coupon_no`, `discount_values`, … | `coupon_number`, `discount_rate`, … |
| `MutationCategory` | 7개 값 | 5개 값, 공통은 4개 |

각 앱의 기본값을 그대로 옮긴 것이라 통일하지 않았습니다. 한 모듈에서 둘 다
필요하면 별칭으로 import 해야 하고(`from korail_mobile_api import TrainSearchQuery
as KorailTrainSearchQuery`), 한쪽에서 만든 값이 다른 쪽에서 통할 것이라고 가정하면
안 됩니다.

## 무엇을 할 수 있나

이 패키지의 경계에는 라우트 60개와 공개 메서드 77개가 들어 있습니다. 라우트 60개는
읽기 58개에 로그인 POST 와 로그아웃 GET 을 더한 것이고, 변경 라우트 9개는 별도
집합이라 읽기 전용 허용목록에 올라가지 않습니다. 공개 메서드 77개 가운데 consent
게이트가 걸린 변경 메서드 13개를 뺀 나머지 64개는 로그인·읽기 요청만 보내거나
아무것도 보내지 않습니다.

### 검색과 조회

| 하고 싶은 것 | 메서드 |
| --- | --- |
| 특정 날짜의 열차 | `search_trains(query)`, 다음 쪽은 `result.next_page()` |
| 직통이 없을 때 | `search_trains_with_transfer_fallback(query)`, `search_transfer_trains(query)` |
| 어느 역에서 환승할 수 있나 | `get_transfer_stations(departure_station_code, arrival_station_code)` |
| 객차 목록과 한 객차의 좌석표 | `get_seat_cars(train)`, `get_seat_inventory(train, car_no)` |
| 실제 정차역과 운행일 | `get_train_schedule(...)`, `get_train_calendar()` |
| 역 목록 | `get_station_data()`, `get_station_info()` |
| 내 승차권과 한 장의 상세 | `get_ticket_list()`, `get_ticket_reservation_detail(request)` |
| 예약 내역과 구매 이력 | `get_reservation_history()`, `get_product_reservations(...)` |
| 환불 수수료와 그 승차권 | `get_refund_commission(ticket)`, `get_refund_ticket_detail(ticket)` |
| 포인트·쿠폰·복지 플래그·마일리지 원장 | `get_korail_point_summary()`, `get_mileage_history(request)` |
| 좌석이나 열차를 아직 바꿀 수 있나 | `get_self_seat_change_info(request)` |
| 반환번호로 원표를 찾기 | `get_original_ticket_inquiry(tickets)` |
| 리무진버스 시간표와 좌석 | `get_limousine_schedules(query)`, `get_limousine_seat_inventory(query)`, `get_limousine_schedule_view(query)` |

로그인 없이 되는 계정 무관 읽기도 있습니다: `get_service_status()`,
`get_app_data()`, `get_notice()`, `get_uuid()`, `get_maas_menu_list()`,
`get_maas_station_data(additional_service_code)`. 메서드마다 어떤 라우트가 붙는지는
[docs/api-status-by-service.md](docs/api-status-by-service.md) 에 있습니다.

### 예약

`reserve` 하나가 예약 화면의 네 동작을 모두 덮습니다. 키워드 전용 `job_type` 으로
고르고, 주지 않으면 좌석 미지정 일반 예약이 나갑니다.

| `job_type` | `txtJobId` | 무엇을 잡나 |
| --- | --- | --- |
| `IMMEDIATE` (기본) | `1101` | 좌석 미지정 일반 예약 |
| `SEAT_DESIGNATED` | `1103` | 좌석지정 — `get_seat_inventory` 에서 고른 호차·좌석번호 |
| `STANDBY` | `1102` | 예약대기 — 매진 열차의 대기열. `confirm_standby_hold` 로 마무리합니다 |
| `MERGE_STANDING` | `1202` | 입석+좌석 — 병합예약의 첫 hold. 두 번째는 `reserve_merge` |

`reserve` 는 `KorailPassengerCounts`(승객 행 8종, 합계 9명까지)와
`KorailSeatClass`(일반실·특실)도 받습니다.

좌석지정에는 함정이 하나 있습니다. 폼에 나가는 것은 `KorailSeatAssignment.seat_no`
이고, 예약을 다시 읽으면 서버는 사람이 읽는 표시 `seat_spec` 을 돌려줍니다. 예약된
좌석을 대조할 때는 `seat_spec` 을 응답의 `h_seat_no` 와 비교해야 합니다. `seat_no`
를 비교하면 제대로 된 예약이 틀린 것처럼 보입니다.

같은 라우트와 같은 `reserve` consent 를 쓰는 진입점이 둘 더 있습니다.
`reserve_transfer(legs, ...)` 는 환승을 하나의 PNR 로 잡고,
`reserve_with_discount_card(train, card_no=...)` 는 할인카드 승객 행 하나를 잡습니다.

### 취소·결제·환불

| 메서드 | consent 범주 | 하는 일 |
| --- | --- | --- |
| `cancel_unpaid_hold(hold, consent=...)` | `cancel` | 결제 전 hold 를 풉니다 |
| `pay_with_fake_card(hold, card, consent=...)` | `payment` | 청구되지 않는 테스트 카드로만 결제합니다 |
| `pay_with_card(hold, card, consent=...)` | `payment` | 실카드로 결제합니다. 기본으로 막혀 있습니다 |
| `refund(ticket, consent=...)` | `refund` | 결제된 승차권을 환불합니다 |
| `recalculate_price(request, consent=...)` | `price_recalculation` | 할인 선택이 바뀐 hold 의 운임을 다시 씁니다 |
| `add_to_cart(request, consent=...)` | `cart` | 이미 잡힌 PNR 을 장바구니에 넣습니다 |

모두 `dry_run=True` 가 기본입니다. 자세한 것은 [안전 모델](#안전-모델) 을 보면
됩니다.

### 할인카드·복지·정기권

- N카드: `get_discount_card_usage_history(card_no)` 와
  `get_discount_card_schedule(request)` 로 읽고,
  `register_discount_card(request, consent=...)` 로 사고,
  `extend_discount_card(ticket, consent=...)` 로 기간연장합니다.
- 정기권: `get_pass_menu(menu_no)`, `get_pass_available_dates(...)`,
  `get_pass_schedule(request)` 로 상품·개시 가능일·묶을 수 있는 열차를 읽습니다.
  정기권 **구매**는 구현하지 않았습니다([한계](#한계) 참고).
- 복지: `get_korail_point_summary()` 가 복지 플래그(`h_hdcp_flg`)를 들고 옵니다.
  이 계정이 장애·안내견 승객 행을 예약할 수 있는지를 결정하는 값입니다.

### 가상대기실 (NetFunnel)

`KorailNetFunnelClient` 는 `nf.letskorail.com` 의 대기열을 다루는 독립
클라이언트이고 **기본적으로 꺼져 있습니다**. 대기열 모양의 실패가 보일 때 켜면
됩니다.

```python
from korail_mobile_api import (
    KorailClient, KorailConfig, KorailNetFunnelClient, inquiry_action,
)

config = KorailConfig(netfunnel_enabled=True)    # 명시적 옵트인
queue = KorailNetFunnelClient(config)
client = KorailClient(config)

with queue.slot(inquiry_action(peak_season=True)):
    result = client.search_trains(query)
```

핸드셰이크와 반납은 실서버에서 확인했지만,
**대기 경로는 실서버에서 한 번도 돌지 않았습니다** — 폴링 루프와 ttl 대기는
오프라인 픽스처로만 덮여 있습니다.

## 안전 모델

관례가 아니라 코드로 강제하고, 오프라인 스위트가 고정합니다.

1. **상태를 바꾸는 것은 consent 객체 없이 움직이지 않습니다.** 변경 메서드 13개는
   전부 `require_mutation_consent(consent, category)` 로 시작해 무엇을 만들기도 전에
   `KorailMutationNotAllowedError` 를 올립니다. 이걸 끄는 전역 스위치도 환경변수도
   없습니다.
2. **범주마다 따로 동의합니다.** `MutationConsent` 의 범주별 플래그(`allow_reserve`,
   `allow_payment`, `allow_cancel`, `allow_refund`, `allow_discount_card`,
   `allow_price_recalculation`, `allow_cart`)는 전부 기본 `False` 입니다. 예약을
   허가한 consent 로 취소할 수 없습니다.
3. **`dry_run=True` 가 기본이고, dry run 은 아무것도 보내지 않습니다.** 변경 메서드는
   입력을 검증하고 보냈을 폼을 담은 `MutationPreview` 를 돌려줍니다. 이 payload 는
   생성 시점에 `redact_payload` 를 지나므로 카드번호·PNR·신원이 남지 않습니다.
4. **`dry_run=False` 만 전송하고, 통로는 하나뿐입니다.**
   `KorailHttpClient.post_mutation_form` 이 변경 라우트에 닿을 수 있는 유일한
   메서드입니다. consent 를 다시 검사하고, 라우트가 알려진 변경 라우트인지 그리고
   주장한 범주에 속하는지를 둘 다 단언합니다. 읽기 전송 경로는 모든 변경 라우트를
   거절합니다.
5. **카드를 실은 결제에는 승인이 하나 더 붙습니다.** `pay_with_fake_card` 는
   `fake_card_only=True` 가 아니면 거절합니다. 청구되는 실카드는 **오직**
   `pay_with_card` 로만 갈 수 있고, `real_card_acknowledged=True` 와
   `fake_card_only=False` 를 **둘 다** 세운 consent 여야 합니다. 둘 중 하나만 세운
   모호한 consent 는 전송 게이트가 따로 한 번 더 거절합니다.

```python
from korail_mobile_api import MutationConsent

# 기본 consent — 보내지 않고 미리 봅니다.
preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
preview.note       # 'dry-run: not sent'
preview.payload    # 마스킹됨. 프로세스 밖으로 나간 것이 없습니다

# 진짜로 잡는 consent.
hold = client.reserve(
    train,
    consent=MutationConsent(allow_reserve=True, dry_run=False),
)
client.cancel_unpaid_hold(
    hold,
    consent=MutationConsent(allow_cancel=True, dry_run=False),
)

# 청구되는 실카드는 플래그 둘이 함께 있어야 합니다.
MutationConsent(
    allow_payment=True,
    dry_run=False,
    fake_card_only=False,
    real_card_acknowledged=True,
)
```

## 에러 처리

서버 쪽 실패는 앱 자신이 분기하는 필드인 `h_msg_cd` 로 분류합니다. 한국어 메시지
문구로는 분류하지 않습니다. 아래 표의 위 열 개는 `KorailAppError` 의 하위 타입이라
기존 `except KorailAppError` 가 그대로 잡고 `code`·`message`·`raw` 를 모두 싣습니다.

### 에러 분류

| 예외 | 코드 | 호출자가 할 일 |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | **아무것도 없었습니다.** 요청 자체는 정상입니다. 재시도는 소용없습니다. 다른 질문을 해야 합니다. |
| `KorailNoDirectTrainError` | `WRD000061` | *직통*이 없습니다. 환승 검색으로 다시 물으면 됩니다. `KorailNoResultsError` 의 하위입니다. |
| `KorailSoldOutError` | `ERR211161` | **재고가 없습니다.** 이 열차는 재시도해도 소용없습니다. 다른 열차를 골라야 합니다. |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | 열차가 아니라 *좌석*이 문제입니다. 좌석지정을 **빼고** 다시 하면 될 수 있습니다. |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | 예약이 거절됐습니다. 이미 들고 있는 예약을 확인해야 합니다. 이유는 `message` 에 있습니다. |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | **payload 를 고쳐야 합니다.** 그대로 재시도해도 소용없습니다. |
| `KorailNotEntitledError` | `ERR299943`* | **이 계정은 그 운임을 살 자격이 없습니다.** 요청 모양은 맞습니다. |
| `KorailServiceUnavailableError` | `SEMGTK` | 요청이 아니라 백엔드가 죽었습니다. |
| `KorailAppUpdateRequiredError` | `SUPDATE` | 이 클라이언트 버전이 거부됐습니다. 아래의 위장된 경우와 구별해야 합니다. |
| `KorailAppError` | 그 밖의 전부 | 미분류입니다. `code` 와 `raw` 는 그대로 있습니다. |
| `KorailSessionExpiredError` | `P058` | **다시 로그인해야 합니다.** `KorailAuthError` 이고, 의도적으로 `KorailAppError` 가 *아닙니다*. |
| `KorailDynaPathError` | *(코드 없음 — 응답 헤더)* | 스로틀이 아니라 플래그가 걸린 것입니다. 안티 매크로 거부에는 `h_msg_cd` 자체가 없습니다. |

올리지 않고 매핑만 원하면 `classify_app_error` 를 쓰면 됩니다. `*` 가 붙은 코드는
APK 분기가 아니라 이 저장소의 실서버 관측입니다. 어느 쪽이 어느 쪽인지, 그리고
일부러 분류하지 않고 남겨 둔 관측 하나는
[docs/verification-record.md](docs/verification-record.md) 에 있습니다.

성공 응답에 붙은 경고 코드는 성공으로 남습니다. 앱이 `FAIL` 이 아닌 응답의 모르는
코드를 성공으로 처리하고, 이 클라이언트도 같습니다.

**이 라이브러리는 스스로 재시도하지 않습니다.** 특히 `reserve` 는 절대 재시도하지
않습니다. 재시도한 예약은 중복 예약이기 때문입니다.

### 안티 매크로 거부가 버전 문제처럼 보입니다

**`login` 이 앱을 업데이트하라고 하면 대개 앱 버전 문제가 아닙니다.** 로그인에
적용되는 검사는 앱처럼 보이지 않는 클라이언트에 `MACRO ERROR` 로 답하면서, 사용자에게
보이는 문구로는 *"원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…"* 를
내보냅니다. 곧이곧대로 받으면 낡은 `KORAIL_API_VERSION` 을 찾으러 가게 됩니다.

구별하는 방법은 둘입니다.

- **다른 것이 되는지 봅니다.** `get_app_data()`, `get_notice()` 같은 계정 무관 읽기는
  정상 응답하는데 `login` 만 실패합니다. 진짜 버전 게이트는 전부를 거절합니다.
- **원본 코드를 봅니다.** 한국어 문구 대신 `error.code` 와 `error.raw` 를 읽으면
  됩니다. `SUPDATE` 는 버전 게이트이고, `MACRO` 가 실린 코드나 메시지는 아닙니다.

해결책은 버전을 올리는 것이 아니라 앱처럼 보이는 것입니다. `KorailDynaPathError` 는
반대 방향의 실패로, 토큰을 보냈는데 서버가 거절한 것입니다. 이때는
`build_config_from_env` 로 본인 단말 값을 쓰면 됩니다.

## 한계

요청을 만들 수 있다는 것과 서버가 그것을 받아 준다는 것은 다릅니다. 연산별 상태는
[docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) 가 추적합니다. 요약하면 이렇습니다.

| 상태 | 대상 |
| --- | --- |
| 왕복까지 실서버 확인 | 즉시·좌석지정·예약대기·입석+좌석 hold, `confirm_standby_hold`, `cancel_unpaid_hold`, `add_to_cart`, 서버가 청구 없이 거절한 `pay_with_fake_card` 시도 |
| 실서버가 업무 응답을 준 읽기 | `get_self_seat_change_info` 가 `WRT800176 좌석변경가능시간아님` 을 돌려줬습니다 |
| 만들었지만 한 번도 보내지 않음 | `pay_with_card`, `refund`, `reserve_merge`, 할인카드 표면 전체, `recalculate_price` |
| 아직 못 돌려 본 읽기 | `get_original_ticket_inquiry` — 실제로 발권된 승차권의 반환번호가 있어야 합니다 |

**환승은 구현했고 실서버 검증 안 됨.** `search_transfer_trains` 와
`reserve_transfer` 는 앱의 요청 빌더에서 그대로 옮겼지만 보낸 적이 없습니다. 검색
쪽은 `get_transfer_stations` 로 싸게 찔러볼 수 있습니다. 실환승 hold 는 그렇지
않으니, KORAIL 앱에서 취소할 준비가 되어 있지 않으면 보내면 안 됩니다.

일부러 구현하지 않은 것도 있습니다.

- **신원 서류 제출.** 복지 인증 라우트는 주민등록번호 조각이나 정부 증명서 번호를
  전송합니다. 검증할 수 없는 제출기를 배포하지 않기로 했습니다.
- **비밀번호를 싣는 포인트 라우트.** 틀린 추측 한 번이 제휴사 쪽 상태 변화이고,
  반복하면 계정이 잠깁니다. 읽기인 제휴 라우트 둘은 들어 있습니다.
- **정기권 구매.** 결제액이 15만~25만원인데 취소·환불 라우트가 없습니다. 정기권
  *읽기* 세 개는 그대로 있습니다.
- **승차권 여행변경과 그 롤백, 예약 인원 변경.** 이미 결제된 승차권이 있어야 하고,
  깨끗한 되돌리기가 없습니다. 같이 들어왔던 *읽기* 둘은 남겼습니다.
- **비회원 오프라인 반환.** 실물 승차권이 있어야 검증할 수 있습니다. 비회원 신원
  모델 전체가 같이 빠졌습니다.
- **승무원 호출 제출.** `/classes/com.korail.mobile.push.callCrew.do` 는 transport
  허용목록과 공개 클라이언트에서 계속 제외되어 있습니다.
- **체크인, 회원정보 변경, 포인트·마일리지 변경, 파괴적 승차권 연산.** 이 버전에는
  없습니다.
- **인증 우회, NetFunnel·DynaPath 우회, 범용 WebView 자동화.** 영구히 범위 밖입니다.

각 주장의 근거 — file:line 인용, 실행마다 서버가 돌려준 코드 — 는
[docs/verification-record.md](docs/verification-record.md) 에 있습니다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [docs/verification-record.md](docs/verification-record.md) | 근거 기록: APK 인용, 실행별 코드, 정정 |
| [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) | 변경 표면의 검증 상태 |
| [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) | 패키지 경계와 라우트 인벤토리 |
| [docs/api-status-by-service.md](docs/api-status-by-service.md) | Retrofit 항목 165개의 서비스별 상태 |
| [docs/api-endpoints.md](docs/api-endpoints.md) | 원본 엔드포인트 표 |
| [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) | APK 자체의 구조·보안·결제 |
| [docs/deep-dive/README.md](docs/deep-dive/README.md) | 하위 시스템별 심층 보고서 |
| [docs/library-build-guide.md](docs/library-build-guide.md) | 정적 분석을 라이브러리로 옮긴 방법과 정책 |
| [docs/pass-schedule-read.md](docs/pass-schedule-read.md) | 정기권 일정 읽기의 타입과 검증 경계 |
| [docs/RELEASE.md](docs/RELEASE.md) | 릴리스가 통과해야 하는 게이트 |
| [docs/internal/README.md](docs/internal/README.md) | 감사·설계 기록. 사용자 문서가 아닙니다 |
| [CHANGELOG.md](CHANGELOG.md) | 무엇이 바뀌었나 |

## 개발

```bash
env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
```

오프라인 스위트가 게이트이고 네트워크를 쓰지 않습니다: `2436 passed, 1 deselected`.
빠진 하나는 `KORAIL_MOBILE_API_LIVE=1` 과 직접 마련한 자격증명이 함께 있을 때만 도는
실서버 테스트입니다. 이 저장소는 계정을 동봉하지 않습니다.

문서도 이 스위트가 고정합니다. 특정 주장·수치·메서드 이름이 그것을 실어야 할 문서에
아직 있는지를 단언합니다 — 아무도 확인하지 않는 주장은 아무도 믿을 수 없기
때문입니다. 기여 절차는 [CONTRIBUTING.md](CONTRIBUTING.md), 커뮤니티 규범은
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 에 있습니다.

## 라이선스

Apache License 2.0 — [LICENSE](LICENSE) 와 [NOTICE](NOTICE) 참고.
