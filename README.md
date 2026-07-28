# korail-mobile-api

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)

KORAIL(한국철도공사) 안드로이드 앱이 쓰는 API 를 파이썬에서 그대로 호출하는
클라이언트다. 로그인하고, 열차를 검색하고, 내 승차권과 예약을 읽는다. 좌석을
잡거나 취소·결제·환불하는 것은 명시적인 consent 객체 뒤에서만 일어난다. 보내는
경로와 폼 필드는 앱이 보내는 것과 같다.

> [!WARNING]
> - **문서가 아니라 리버스 엔지니어링의 결과다.** 여기의 라우트·필드명·상태코드는
>   `com.korail.talk` 6.5.0 APK 를 디컴파일해 읽어낸 것이고, 가능한 범위에서만
>   실서버로 확인했다. KORAIL 은 규격을 공개하지 않고 안정성도 약속하지 않는다.
> - **실서비스에 붙는다.** `smart.letskorail.com` 은 실제 발권 시스템이다. 이
>   라이브러리가 만든 예약은 누군가 취소해야 하는 진짜 예약이고, 결제는 진짜 돈이다.
> - **KORAIL 과 제휴·후원·지원 관계가 없다.** 본인 계정을 쓰고, 결과는 본인이
>   감당하라. 무보증이다. 취약점 제보는 [SECURITY.md](SECURITY.md) 를 먼저 읽어라.

## 설치

PyPI 배포는 없다. 저장소에서 바로 설치한다.

```bash
python3 -m pip install "korail-mobile-api @ git+https://github.com/yakisoba0728/korail-mobile-api"
```

| 항목 | 값 |
| --- | --- |
| 파이썬 | 3.11 이상 (`requires-python = ">=3.11"`) |
| 런타임 의존성 | `httpx`, `cryptography` — 이 둘뿐이다 |
| 타입 | 타입 주석 완비, `py.typed` 동봉 |
| 라이선스 | Apache-2.0 |

고쳐 쓸 체크아웃이라면 개발 설치를 하고 오프라인 스위트를 한 번 돌려라.

```bash
python3 -m pip install -e ".[test]"
python3 -m pytest -q -m "not live"
```

## 빠른 시작

아래는 로그인하고 검색하고 읽어오기만 한다. 상태를 바꾸지 않고 돈도 건드리지 않는다.

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

`KorailClient()` 는 설정 없이 만들어진다. 역은 이름(`"서울"`)으로도 코드로도
넘길 수 있고, 앱이 내려받는 역 목록으로 해석한다. 날짜와 시각은 앱이 쓰는
`YYYYMMDD`·`HHMMSS` 문자열 그대로다. 다음 페이지는 `result.next_page()` 가
돌려주는 continuation 을 `search_trains(query, continuation=...)` 에 다시 넣어
받는다.

네 가지 파라미터는 `str` 이 아니라 `Literal` 별칭이라 편집기가 값을 완성해 주고
오타가 요청이 아니라 오류가 된다: `MutationCategory`(`require_mutation_consent`),
`KorailMileageLedger` 와 `KorailMileageMovement`(`MileageHistoryRequest`),
`KorailSelfSeatChangeRoomClassCode`(`SelfSeatChangeInfoRequest`). 넷 다
export 되어 있어 직접 만든 래퍼에 붙일 수 있다. 그 밖의 코드값은 `str` 로 둔다 —
응답에서 읽은 코드는 서버가 얼마든지 새로 만들 수 있기 때문이다.

### 기본 설정이 보내는 것

`login` 은 KORAIL 의 안티 매크로 검사 뒤에 있다. 앱처럼 보이지 않는 요청은
거절되므로 기본값은 장식이 아니다.

- **User-Agent.** 앱은 UA 를 직접 박지 않는다. `HttpURLConnection` 위의
  Retrofit v1 을 쓰므로 서버가 보는 것은 플랫폼의 Dalvik 문자열이고,
  `KORAIL_USER_AGENT` 가 그 모양이다.
- **DynaPath.** `x-dynapath-m-token` 안티 오토메이션 헤더는 **기본적으로 켜져 있다**.
  붙는 곳은 앱이 붙이는 경로뿐이고, 그 목록은
  `korail_mobile_api.constants.DYNAPATH_ALLOWLIST_PATHS` 의 6개 경로다. 토큰은
  설정이 가진 기기 값으로 로컬에서 만든다. 이 값을 만들려고 사용자 컴퓨터에서
  읽어오는 것은 없다.

기기 값은 **합성이고 인스턴스마다 다르다.** `KorailConfig()` 는 매번 자기 `di`
— 실기기에서는 `Settings.Secure.ANDROID_ID` 인 필드 — 를 새로 만든다. 모든 설치본이
공통으로 보내는 식별자야말로 안티 매크로 검사가 찾는 것이기 때문이다. 그 값은
설정 객체가 사는 동안만 유지되고 프로세스를 넘기지 않는다.

진짜 기기 신원 — 본인의 `ANDROID_ID`, 모델, 안드로이드 릴리스 — 을 실행 간에
고정하고 싶으면 환경변수로 넘겨라.

```bash
export KORAIL_DYNAPATH_DEVICE_ID="<Settings.Secure.ANDROID_ID, 16 hex chars>"
export KORAIL_DYNAPATH_OS_VERSION="15"          # Build.VERSION.RELEASE
export KORAIL_DYNAPATH_DEVICE_MODEL="SM-S928N"  # Build.MODEL
```

```python
from korail_mobile_api import KorailClient, build_config_from_env

client = KorailClient(build_config_from_env())
```

뒤의 두 값은 토큰과 User-Agent 양쪽에 쓰인다. UA 를 따로 적는 대신 같은 값에서
파생시켜, 헤더와 토큰이 서로 다른 단말을 주장하는 일이 없게 한 것이다. 나머지
(`KORAIL_BASE_URL`, 화면 크기, `KORAIL_ANDROID_SDK_INT`, `KORAIL_ADVERTISING_ID`)
에는 기본값이 있다. [docs/verification-record.md](docs/verification-record.md)
참고.

DynaPath 를 끄려면 — 모의 transport 를 쓰거나 맨 프로토콜을 보려면 — 명시해야 한다.

```python
from korail_mobile_api import DynapathConfig, KorailClient, KorailConfig

client = KorailClient(KorailConfig(dynapath=DynapathConfig()))
```

끄면 무엇을 포기하는지는 알고 해라. DynaPath 없이, 그리고 이 패키지 이름을 단
User-Agent 로 보냈을 때 읽기는 성공했고 `login` 은 실패했다. 그 실패는 아래
[에러 처리](#에러-처리) 의 위장된 형태로 나타난다. 둘 중 무엇이 로그인을 되살렸는지
하나씩 분리해 확인하지는 않았으므로, DynaPath 만 끄고 앱 모양 User-Agent 는 남긴
설정은 "깨진 것으로 확인된" 것이 아니라 "확인되지 않은" 상태다.

### srt-mobile-api 와 함께 쓸 때

`TrainSearchQuery`, `DiscountCoupon`, `MutationCategory` 는 두 패키지가 모두
export 하지만 같은 타입이 아니다.

| 이름 | korail | srt |
| --- | --- | --- |
| `TrainSearchQuery.passengers` | `int`, 기본 `1` | `PassengerCounts` |
| `TrainSearchQuery.departure_time` 기본값 | `"000000"` | `"060000"` |
| `DiscountCoupon` | `coupon_no`, `discount_values`, `expiration_date`, … | `coupon_number`, `discount_rate`, `remaining_uses`, … |
| `MutationCategory` | 7개 값 | 5개 값, 공통은 4개 |

각 앱의 기본값을 그대로 옮긴 것이라 통일하지 않았다. 한 모듈에서 둘 다 필요하면
별칭으로 import 하고(`from korail_mobile_api import TrainSearchQuery as KorailTrainSearchQuery`),
한쪽에서 만든 값이 다른 쪽에서 통할 것이라고 가정하지 마라.

## 무엇을 할 수 있나

이 패키지의 경계에는 라우트 60개와 공개 메서드 77개가 들어 있다. 라우트
60개는 읽기 58개에 로그인 POST 와 로그아웃 GET 을 더한 것이다. 변경 라우트 9개는
별도 집합으로 관리되며 읽기 전용 허용목록에 올라가지 않는다. 공개 메서드 77개
가운데 consent 게이트가 걸린 변경 메서드 13개를 뺀 나머지 64개는 로그인·읽기
요청만 보내거나 아무것도 보내지 않는다.

### 검색과 조회

| 하고 싶은 것 | 메서드 |
| --- | --- |
| 특정 날짜의 열차 | `search_trains(query)`, 다음 쪽은 `result.next_page()` |
| 직통이 없을 때 | `search_trains_with_transfer_fallback(query)`, 또는 처음부터 `search_transfer_trains(query)` |
| 어느 역에서 환승할 수 있나 | `get_transfer_stations(departure_station_code, arrival_station_code)` |
| 객차 목록과 한 객차의 좌석표 | `get_seat_cars(train)`, `get_seat_inventory(train, car_no)` |
| 실제 정차역과 운행일 | `get_train_schedule(...)`, `get_train_calendar()` |
| 역 목록 | `get_station_data()`, `get_station_info()` |
| 내 승차권과 한 장의 상세 | `get_ticket_list()`, `get_ticket_reservation_detail(request)` |
| 예약 내역과 구매 이력 | `get_reservation_history()`, `get_product_reservations(...)` |
| 환불하면 얼마가 떼이나, 그 승차권은 무엇인가 | `get_refund_commission(ticket)`, `get_refund_ticket_detail(ticket)` |
| 포인트·쿠폰·복지 플래그·마일리지 원장 | `get_korail_point_summary()`, `get_mileage_history(request)` |
| 좌석이나 열차를 아직 바꿀 수 있나 | `get_self_seat_change_info(request)` |
| 반환번호로 원표를 찾기 | `get_original_ticket_inquiry(tickets)` |
| 리무진버스 시간표와 좌석 | `get_limousine_schedules(query)`, `get_limousine_seat_inventory(query)`, `get_limousine_schedule_view(query)` |

로그인 없이 되는 계정 무관 읽기도 있다. `get_service_status()`(무엇을 하기 전에
서비스가 살아 있는지), `get_app_data()`, `get_notice()`, `get_uuid()`,
`get_maas_menu_list()`, `get_maas_station_data(additional_service_code)`.
메서드마다 어떤 라우트가
붙는지는 [docs/api-status-by-service.md](docs/api-status-by-service.md) 에 있다.

### 예약

`reserve` 하나가 예약 화면의 네 동작을 모두 덮는다. 키워드 전용 `job_type` 으로
고르고, 주지 않으면 좌석 미지정 일반 예약이 나간다.

| `job_type` | `txtJobId` | 무엇을 잡나 |
| --- | --- | --- |
| `IMMEDIATE` (기본) | `1101` | 좌석 미지정 일반 예약 |
| `SEAT_DESIGNATED` | `1103` | 좌석지정 — `get_seat_inventory` 에서 고른 호차·좌석번호 |
| `STANDBY` | `1102` | 예약대기 — 매진 열차의 대기열. `confirm_standby_hold` 로 마무리한다 |
| `MERGE_STANDING` | `1202` | 입석+좌석 — 병합예약에 필요한 두 hold 중 첫 번째. 두 번째는 `reserve_merge` |

`reserve` 는 `KorailPassengerCounts`(승객 행 8종, 합계 9명까지)와
`KorailSeatClass`(일반실·특실)도 받는다.

좌석지정에는 함정이 하나 있다. 좌석은 식별자를 두 개 갖는다. 폼에 나가는 것은
`KorailSeatAssignment.seat_no` 이고, 예약을 다시 읽으면 서버는 사람이 읽는 표시
`seat_spec` 을 돌려준다. 예약된 좌석을 대조할 때는 `seat_spec` 을 응답의
`h_seat_no` 와 비교하라. `seat_no` 를 비교하면 제대로 된 예약이 틀린 것처럼 보인다.

같은 라우트와 같은 `reserve` consent 를 쓰는 진입점이 둘 더 있다.
`reserve_transfer(legs, ...)` 는 환승을 두 여정을 담은 하나의 PNR 로 잡고,
`reserve_with_discount_card(train, card_no=...)` 는 할인카드 승객 행 하나를 잡는다.

### 취소·결제·환불

| 메서드 | consent 범주 | 하는 일 |
| --- | --- | --- |
| `cancel_unpaid_hold(hold, consent=...)` | `cancel` | 결제 전 hold 를 푼다 |
| `pay_with_fake_card(hold, card, consent=...)` | `payment` | 청구되지 않는 테스트 카드로만 결제한다. 다른 카드는 거절한다 |
| `pay_with_card(hold, card, consent=...)` | `payment` | 실카드로 결제한다. 기본으로 막혀 있다 — [안전 모델](#안전-모델) 참고 |
| `refund(ticket, consent=...)` | `refund` | 결제된 승차권을 환불한다 |
| `recalculate_price(request, consent=...)` | `price_recalculation` | 운임 재계산. 할인 선택이 바뀐 hold 의 금액을 다시 쓴다 |
| `add_to_cart(request, consent=...)` | `cart` | 이미 잡힌 PNR 을 장바구니에 넣는다. 새로 만드는 것이 없어 예약도 결제도 아니다 |

모두 `dry_run=True` 가 기본이다.

### 할인카드·복지·정기권

- `get_discount_card_usage_history(card_no)` 와 `get_discount_card_schedule(request)`
  는 N카드를 읽는다. 어디에 썼는지, 아직 어떤 열차에 쓸 수 있는지.
- `register_discount_card(request, consent=...)` 는 새로 사고,
  `extend_discount_card(ticket, consent=...)` 는 기간연장이다. 둘 다 `discount_card`
  consent 범주다.
- `get_pass_menu(menu_no)`, `get_pass_available_dates(...)`, `get_pass_schedule(request)`
  는 정기권 상품, 개시 가능일, 묶을 수 있는 열차를 읽는다. 정기권 **구매**는
  구현하지 않았다 — [한계](#한계) 참고.
- `get_korail_point_summary()` 가 복지 플래그(`h_hdcp_flg`, 장애인증·보조견 이름)를
  들고 온다. 이 계정이 장애·안내견 승객 행을 예약할 수 있는지를 결정하는 값이다.

### 가상대기실 (NetFunnel)

`KorailNetFunnelClient` 는 `nf.letskorail.com` 의 KORAIL 대기열을 다루는 독립
클라이언트다. **기본적으로 꺼져 있다**. 이 저장소가 지금까지 보낸 실호출 중
대기열에 걸린 것이 하나도 없기 때문이다. `KorailClient` 에서는 닿을 수 없게
분리해 두었다 — API origin 가드와 큐 origin 가드가 별개이고, 옵트인하지 않은
설정으로 큐 클라이언트를 만들면 소켓이 생기기 전에 예외가 난다.

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

대기열 모양의 실패가 보일 때 켜라. 그러라고 만든 것이다. 핸드셰이크와 반납은
실서버에서 확인했지만 **대기 경로는 실서버에서 한 번도 돌지 않았다** — 서버가 이
클라이언트를 실제로 기다리게 한 적이 없어서, 폴링 루프와 ttl 대기와 경계값은
오프라인 픽스처로만 덮여 있다.

## 안전 모델

이 라이브러리의 정체성이다. 관례가 아니라 코드로 강제하고, 오프라인 스위트가
고정한다.

**1. 상태를 바꾸는 것은 consent 객체 없이 움직이지 않는다.** 변경 메서드 13개는
전부 `require_mutation_consent(consent, category)` 로 시작해서, 무엇을 만들기도
전에 `KorailMutationNotAllowedError` 를 올린다. 이걸 끄는 전역 스위치도 환경변수도
없다.

**2. 범주마다 따로 동의한다.** `MutationConsent` 는 범주별 플래그를 하나씩 갖는다 —
`allow_reserve`, `allow_payment`, `allow_cancel`, `allow_refund`,
`allow_discount_card`, `allow_price_recalculation`, `allow_cart` — 전부 기본
`False` 다. 예약을 허가한 consent 로 취소할 수 없고, 견적 금액 결제를 허가한
consent 로 재가격할 수 없다.

**3. `dry_run=True` 가 기본이고, dry run 은 아무것도 보내지 않는다.** 기본 consent
로는 변경 메서드가 입력을 검증하고, 보냈을 폼을 그대로 담은 `MutationPreview` 를
돌려준다. 이 payload 는 생성 시점에 `redact_payload` 를 통과하므로 진짜 값으로
만들었더라도 카드번호·PNR·신원이 남지 않는다. 자동으로 그렇게 된다. 직접
로깅하려면 `from korail_mobile_api.redaction import redact_payload, redact_mapping,
redact_value, redact_text, redact_url, is_sensitive_key` 로 가져다 쓸 수 있다.

```python
from korail_mobile_api import MutationConsent

preview = client.reserve(train, consent=MutationConsent(allow_reserve=True))
preview.route      # '/classes/com.korail.mobile.certification.TicketReservation'
preview.note       # 'dry-run: not sent'
preview.payload    # 마스킹됨. 프로세스 밖으로 나간 것이 없다
```

**4. `dry_run=False` 만 전송하고, 통로는 하나뿐이다.**
`KorailHttpClient.post_mutation_form` 이 변경 라우트에 닿을 수 있는 유일한
메서드다. consent 를 다시 검사하고, `dry_run=True` 인 consent 는 그 자리에서
거절하며, 라우트가 알려진 변경 라우트인지 그리고 주장한 범주에 속하는지를 둘 다
단언한다. 읽기 전송 경로는 모든 변경 라우트를 거절하므로, 읽기가 부수효과로
상태를 바꾸는 일은 없다.

**실제로 열차를 예약하는 consent 는 이렇게 생겼다.**

```python
hold = client.reserve(
    train,
    consent=MutationConsent(allow_reserve=True, dry_run=False),
)
hold.pnr_no        # 결정을 내려야 하는 진짜 미결제 예약

client.cancel_unpaid_hold(
    hold,
    consent=MutationConsent(allow_cancel=True, dry_run=False),
)
```

**5. 카드를 실은 결제에는 승인이 하나 더 붙는다.** 결제 폼은 카드번호를 평문으로
싣는다. `pay_with_fake_card` 는 `fake_card_only=True` 가 아니면 거절하므로 청구되지
않는 테스트 카드만 보낼 수 있다. 청구되는 실카드는 **오직** `pay_with_card` 로만
갈 수 있고, `real_card_acknowledged=True` 와 `fake_card_only=False` 를 **둘 다**
세운 consent 여야 한다.

```python
MutationConsent(
    allow_payment=True,
    dry_run=False,
    fake_card_only=False,
    real_card_acknowledged=True,
)
```

두 플래그 모두 안전한 쪽이 기본이고, 전송 게이트는 둘 다 아니거나 둘 다인 consent
를 따로 한 번 더 거절한다. 모호한 consent 는 절대 나가지 않는다.

## 에러 처리

서버 쪽 실패는 앱 자신이 분기하는 필드인 `h_msg_cd` 로 분류한다. 한국어 메시지
문구로는 분류하지 않는다.

표의 위 열 개는 전부 `KorailAppError` 의 하위 타입이라 기존
`except KorailAppError` 가 잡던 것을 그대로 잡고, `code`·`message`·`raw` 를
모두 싣는다. 마지막 둘은 `KorailAppError` 가 아니다 — `KorailSessionExpiredError`
는 `KorailAuthError` 이고 세 값을 다 갖지만, `KorailDynaPathError` 는
`KorailApiError` 이고 `raw` 만 있다. 서버가 코드를 주지 않기 때문이다.

### 에러 분류

| 예외 | 코드 | 호출자가 할 일 |
| --- | --- | --- |
| `KorailNoResultsError` | `WRG000000`, `P114`, `P100`*, `WRT300005`* | **아무것도 없었다.** 요청 자체는 정상이다. 재시도는 소용없다. 다른 질문을 하라. |
| `KorailNoDirectTrainError` | `WRD000061` | *직통*이 없다. 환승 검색으로 다시 물어라 — 앱이 그렇게 한다. `KorailNoResultsError` 의 하위. |
| `KorailSoldOutError` | `ERR211161` | **재고가 없다.** 이 열차는 재시도해도 소용없다. 다른 열차를 골라라. |
| `KorailSeatUnavailableError` | `WRI411345`, `ERR911081`, `WRT800176` | 열차가 아니라 *좌석*이 문제다. 좌석지정을 **빼고** 다시 하면 될 수 있다. |
| `KorailReservationRefusedError` | `WRR800029`, `ERR911531`, `ERR911051` | 예약이 거절됐다. 이미 들고 있는 예약을 확인하라. 이유는 `message` 에 있다. |
| `KorailInvalidRequestError` | `WRG200018`*, `WRT100002`*, `WRT100124`* | **payload 를 고쳐라.** 필드가 거절됐다. 그대로 재시도해도 소용없다. |
| `KorailNotEntitledError` | `ERR299943`* | **이 계정은 그 운임을 살 자격이 없다.** 요청 모양은 맞다. 누가 묻느냐 때문에 거절된 것이다. |
| `KorailServiceUnavailableError` | `SEMGTK` | 요청이 아니라 백엔드가 죽었다. |
| `KorailAppUpdateRequiredError` | `SUPDATE` | 이 클라이언트 버전이 거부됐다. 재시도 간격으로 해결되지 않는다. 아래의 위장된 경우와 구별하라. |
| `KorailAppError` | 그 밖의 전부 | 미분류. `code` 와 `raw` 는 그대로 있다. 이렇게 매핑이 자란다. |
| `KorailSessionExpiredError` | `P058` | **다시 로그인하라.** `KorailAuthError` 이고, 의도적으로 `KorailAppError` 가 *아니다*. |
| `KorailDynaPathError` | *(코드 없음 — 응답 헤더)* | 스로틀이 아니라 플래그가 걸린 것이다. 안티 매크로 거부에는 `h_msg_cd` 자체가 없다. |

올리지 않고 매핑만 원하면 `classify_app_error` 를 쓰면 된다. `*` 가 붙은 코드는
APK 분기가 아니라 이 저장소의 실서버 관측이다. 어느 쪽이 어느 쪽인지, 그리고
일부러 분류하지 않고 남겨 둔 관측 하나는
[docs/verification-record.md](docs/verification-record.md) 에 있다.

성공 응답에 붙은 경고 코드는 성공으로 남는다. 앱은 `FAIL` 이 아닌 응답의 모르는
코드를 성공으로 처리하고, 이 클라이언트도 같다.

**이 라이브러리는 스스로 재시도하지 않는다.** 특히 `reserve` 는 절대 재시도하지
않는다. 재시도한 예약은 중복 예약이기 때문이다. 분류는 *호출자*가 결정하라고 있다.

### 안티 매크로 거부가 버전 문제처럼 보인다

**`login` 이 앱을 업데이트하라고 하면 대개 앱 버전 문제가 아니다.** 로그인에
적용되는 검사는 앱처럼 보이지 않는 클라이언트에 `MACRO ERROR` 로 답하고, 사용자에게
보이는 문구로는 *"원활한 서비스 이용을 위해 앱을 최신 버전으로 업데이트한 뒤…"* 를
내보낸다. 이걸 곧이곧대로 받으면 낡은 `KORAIL_API_VERSION` 을 찾으러 가게 된다.
그것은 `KorailAppUpdateRequiredError` 의 `SUPDATE` 가 진짜로 뜻하는 바이고, 여기서
일어난 일이 아니다.

구별하는 방법은 둘이다.

- **다른 것이 되는지 본다.** 안티 매크로 거부는 클라이언트가 아니라 계정 모양이다.
  `get_app_data()`, `get_notice()` 같은 계정 무관 읽기는 정상 응답하는데 `login`
  만 실패한다. 진짜 버전 게이트는 전부를 거절한다. "읽기는 되는데 로그인만 거절"
  이 그 신호다.
- **원본 코드를 본다.** `login` 은 이 라이브러리가 파싱하는 라우트다. 호출해서
  한국어 문구 대신 `error.code` 와 `error.raw` 를 읽어라. `SUPDATE` 는 버전
  게이트다. `MACRO` 가 실린 코드나 메시지는 아니다.

해결책은 버전을 올리는 것이 아니라 앱처럼 보이는 것이다. 위의 기본 설정이 그
목적이고, DynaPath 를 끄거나 `user_agent` 를 직접 덮어쓰는 것이 의도적으로만
해야 할 변경인 이유다.

`KorailDynaPathError` 는 반대 방향의 실패이고, 기본 설정으로도 여기에 닿는다.
토큰이 붙는 경로 6개 중 하나가 `search_trains` 가 쓰는 `ScheduleView` 라서, 빠른
시작의 *첫* 호출부터 토큰이 실린다.

그 토큰은 이 라이브러리가 합성한 기기 id 와 `"Android"` 라는 `device_model` 로
만든다. **두 값 모두 실서버로 확인한 적이 없다.** 확인된 것은
`build_config_from_env` 로 진짜 단말 값을 실은 같은 요청이다. 서버가 토큰의 존재가
아니라 내용을 검사한다면, 증상은 토큰 없이 잘 되던 읽기에서
`KorailDynaPathError` 가 나는 것이다. 빠져나갈 길은 둘이고 위에 다 있다.
`KorailConfig(dynapath=DynapathConfig())` 로 토큰을 안 보내거나,
`build_config_from_env` 로 본인 단말 값을 보내라.

## 한계

### 실서버로 확인되지 않은 것

요청을 만들 수 있다는 것과 서버가 그것을 받아 준다는 것은 다르다. 연산별 상태는
[docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) 가 추적한다. 요약하면:

| 상태 | 대상 |
| --- | --- |
| 왕복까지 실서버 확인 | 즉시·좌석지정·예약대기·입석+좌석 hold, `confirm_standby_hold`, `cancel_unpaid_hold`, `add_to_cart`, 그리고 서버가 청구 없이 거절한 `pay_with_fake_card` 시도 |
| 실서버가 업무 응답을 준 읽기 | `get_self_seat_change_info` 가 `WRT800176 좌석변경가능시간아님` 을 돌려줬다. 라우트·필드 계약·에러 분류가 모두 맞물린다는 증거다 |
| 만들었지만 한 번도 보내지 않음 | `pay_with_card`, `refund`, `reserve_merge`, 할인카드 표면 전체, `recalculate_price`. 전송 경로는 막힌 코드가 아니라 살아 있는 코드다 |
| 아직 못 돌려 본 읽기 | `get_original_ticket_inquiry` — 실제로 발권된 승차권의 반환번호가 있어야 한다 |

**환승은 구현했고 실서버 검증 안 됨.** `search_transfer_trains` 와
`reserve_transfer` 는 앱의 요청 빌더에서 그대로 옮겼지만, 이 패키지가 환승 검색이나
환승 hold 를 보낸 적은 없다. 검색 쪽은 싸게 찔러볼 수 있다 —
`get_transfer_stations` 는 그냥 읽기다. 실환승 hold 는 그렇지 않으니,
KORAIL 앱에서 취소할 준비가 되어 있지 않으면 보내지 마라.

각 주장의 근거 — file:line 인용, 실행마다 서버가 돌려준 코드 — 는
[docs/verification-record.md](docs/verification-record.md) 에 있다.

### 구현하지 않은 것과 그 이유

- **신원 서류 제출.** 복지 인증 라우트(`certification.disabled.do`, `MeritCert`,
  `assemblyCert`, `pbep.*`)는 주민등록번호 조각이나 정부 증명서 번호를 전송하고
  계정에 자격을 *등록*한다. 검증할 수 없는 신원 서류 제출기를 배포하는 쪽이 아예
  없는 쪽보다 나쁘다고 판단했다.
- **비밀번호를 싣는 포인트 라우트.** `mlg.lpotAthn.do` 와 `xPoint.XPointView` 는
  사용자가 입력한 포인트 비밀번호로 인증하고 실패 횟수를 돌려준다. 틀린 추측 한
  번이 제휴사 쪽 상태 변화이고 반복하면 계정이 잠긴다. 읽기가 아니므로 넣지
  않았다. 읽기인 제휴 라우트 둘은 들어 있다.
- **정기권 구매.** 결제액이 15만~25만원인데 이 패키지에는 취소·환불 라우트가 없고,
  `passPayIssue` 는 배포된 앱에서 도달할 수 없어 폼을 대조할 앱 캡처조차 없다.
  정기권 *읽기* 세 개는 그대로 있다.
- **승차권 여행변경과 그 롤백, 예약 인원 변경.** 어느 것을 돌려 보려 해도 이미
  결제된 승차권이 필요하다. 변경은 운임 차액에 변경수수료를 더해 청구하고 깨끗한
  되돌리기가 없다. 영구히 미검증인 돈 경로가 변경 허용목록에 앉아 있게 된다.
  같이 들어왔던 *읽기* 둘은 남겼다. 읽기는 비용이 없고 혼자서도 쓸모가 있다.
- **비회원 오프라인 반환.** 역 창구 환불 쌍은 종이에 인쇄된 반환번호와 신청인
  이름으로 승차권을 식별한다. 검증하려면 실물 승차권이 있어야 한다. 비회원 신원
  모델 전체가 같이 빠졌다.
- **승무원 호출 제출.** `/classes/com.korail.mobile.push.callCrew.do` 는 승무원
  요청 읽기의 상태 변경 짝이고, transport 허용목록과 공개 클라이언트에서 계속
  제외되어 있다. 승무원 요청 옵션을 읽는 것으로 호출이 나가는 일은 없다.
- **이 계정에 자격이 없는 것.** N카드 읽기와 1~3급 장애·안내견 승객 행은 요청
  모양이 아니라 누가 묻느냐 때문에 거절된다. 증명하려면 실제 등록이 되어 있는
  계정이 있어야 한다.
- **체크인, 회원정보 변경, 포인트·마일리지 변경, 파괴적 승차권 연산.** 이 버전에는
  없다.
- **인증 우회, NetFunnel·DynaPath 우회, 범용 WebView 자동화.** 영구히 범위 밖이다.

## 문서

| 문서 | 내용 |
| --- | --- |
| [docs/verification-record.md](docs/verification-record.md) | 근거 기록. 기능별 APK file:line 인용, 제한된 실행마다의 코드와 건수, 철회된 주장과 정정 |
| [docs/MUTATION_HANDOFF.md](docs/MUTATION_HANDOFF.md) | 변경 표면. 무엇이 증명됐고, 남은 증명 하나하나가 얼마를 치러야 하는지 |
| [docs/IMPLEMENTATION_PROGRESS.md](docs/IMPLEMENTATION_PROGRESS.md) | 패키지 경계, 라우트 인벤토리, 검증 상태 |
| [docs/api-status-by-service.md](docs/api-status-by-service.md) | Retrofit 항목 165개를 서비스별로. 각각의 실서버 성공/실패/미실행 |
| [docs/api-endpoints.md](docs/api-endpoints.md) | 원본 엔드포인트 표: 메서드, 경로, 요청 파라미터, 반환 타입 |
| [docs/korail-apk-analysis.md](docs/korail-apk-analysis.md) | APK 자체: 구조, 호스트, 로그인, 보안, 결제, WebView |
| [docs/deep-dive/README.md](docs/deep-dive/README.md) | 하위 시스템별 심층 보고서와 읽는 순서 |
| [docs/library-build-guide.md](docs/library-build-guide.md) | 정적 분석을 이 라이브러리로 옮긴 방법과 지켜야 할 정책 |
| [docs/pass-schedule-read.md](docs/pass-schedule-read.md) | 정기권 일정 읽기의 요청·응답 타입과 실검증 경계 |
| [docs/RELEASE.md](docs/RELEASE.md) | 릴리스가 통과해야 하는 테스트·빌드·배포 게이트 |
| [docs/internal/README.md](docs/internal/README.md) | 감사·재검증·설계 기록. 사용자 문서가 아니다 |
| [CHANGELOG.md](CHANGELOG.md) | 무엇이 바뀌었나 |

## 개발

```bash
env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
```

오프라인 스위트가 게이트이고 네트워크를 쓰지 않는다: `2427 passed, 1 deselected`.
빠진 하나는 명시적으로 옵트인해야 하는 실서버 테스트다. 실서버 테스트는
`KORAIL_MOBILE_API_LIVE=1` 과 직접 마련한 자격증명이 함께 있을 때만 돈다. 이
저장소는 계정을 동봉하지 않는다.

문서는 오프라인 스위트가 고정한다. 주로 `tests/test_readme.py` 와
`tests/test_release_readiness.py` 가, 기능별 모듈은 각자의 주장을 붙든다. 특정
주장·수치·메서드 이름이 그것을 실어야 할 문서에 아직 있는지를 단언한다. 이 파일과
`docs/verification-record.md` 도 대상이다. 의도적이다 — 아무도 확인하지 않는 주장은
아무도 믿을 수 없다.

APK 와 디컴파일 산출물 디렉터리는 커밋하지 않는다. 문서, 재현 가능한 인벤토리
출력, 클라이언트 소스, 오프라인 계약 테스트는 커밋한다.

기여 절차는 [CONTRIBUTING.md](CONTRIBUTING.md) 에 있다. 오프라인 게이트는
`pytest -q -m "not live"`, `ruff check .`, `pyright` 셋이고 모두 `pyproject.toml`
에 설정되어 있으며 CI 가 셋 다 돌린다. 커뮤니티 규범은
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) 를 보라.

## 라이선스

Apache License 2.0 — [LICENSE](LICENSE) 와 [NOTICE](NOTICE) 참고.
