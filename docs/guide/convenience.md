# 간편 API

[`Korail`][korail_mobile_api.Korail]은 기존 `KorailClient` 위에 자주 쓰는 작업을 묶은 선택형 진입점입니다. 전체 API나 세부 요청 옵션은 `korail.client`에서 그대로 사용합니다.

!!! note "2.6.1의 추가 기능"
    `trains.iter_search`, `PriceFareLeg.from_train`, `membership`, `airport_bus`는 2.6.1부터 제공합니다. 이 흐름의 검증은 소켓을 차단한 합성 응답 기준이며 실서버 성공 기록은 추가하지 않았습니다.

!!! note "2.5.0의 추가 기능"
    검색 필터, 좌석 상태·소요 시간·요약 헬퍼, `KorailReserveOption`, `stations.names()`, `reservations.find()`(3.0부터 `reservations.get()`)와 청소년 예약 사전 거절은 2.5.0부터 제공합니다.

## 로그인 없이 열차 찾기

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail, KorailPassengerCounts

with Korail() as korail:
    result = korail.trains.search(
        "서울",
        "부산",
        depart_after=datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1),
        passengers=KorailPassengerCounts(adult=2, child=1),
    )
    for train in result.trains:
        print(train.train_no, train.departure_time)
```

시간대가 없는 `datetime`은 한국 시각(KST)으로 읽고, 시간대가 있는 값은 KST로 변환합니다. 이미 지난 시각은 요청 전에 거절합니다. 시각을 생략하면 현재 KST를 사용합니다. 결과는 기존 `TrainSearchResult`이며 한 페이지씩 옵니다. `result.next_page()`가 값을 돌려주면 같은 조건과 `continuation=...`으로 다음 페이지를 조회하세요. 2.6.2부터 이때 첫 페이지의 `depart_after`를 그대로 넘겨야 하며, 생략하면 `ValueError`입니다. 그 사이 시각이 지나도 이어보기 요청은 이미 지난 시각으로 거절하지 않습니다. `next_page()`가 `None`이어도 더 조회해야 하는 경우에는 [원래 조회 API의 마지막 열차 시각 방식](trains.md#next-page)을 사용합니다.

기본적으로 첫 검색에서 역 목록을 가져와 역 이름·코드를 확인한 후 클라이언트 수명 동안 캐시합니다. 2.6.2부터 이 목록은 한 번만 받아 간편 API와 `korail.client`가 함께 쓰며, 승객 구성은 역 목록을 받기 전에 검사합니다. 잘못된 역은 검색 요청 전에 `ValueError`로 거절하고 가까운 역 이름을 제안합니다. 이 추가 조회가 필요 없으면 `Korail(validate_stations=False)`로 생성하세요. 역 목록은 `korail.stations.all(refresh=True)`로 갱신할 수 있습니다.

`include_nearby_stations=True`는 인접역 일정 표시 필드 `adjStnScdlOfrFlg=Y`를 보냅니다. 기본값은 이전과 같은 `N`입니다. 2026-09-28 실서버에서 두 값 모두 검색 성공 응답을 받았지만, 결과에 미치는 효과는 확인하지 못했습니다.

### 좌석 상태로 결과 고르기

기본 검색은 이전처럼 매진 열차까지 모두 반환합니다(`include_no_seats=True`). `include_no_seats=False`를 넘기면 일반실 또는 특실 예약 코드가 `"11"`인 열차만 남깁니다. 여기에 `include_waiting_list=True`를 지정하면 일반실 예약대기 플래그가 `" 9"`인 열차도 포함합니다. 없는 값이나 모르는 상태 코드를 가용으로 추측하지 않습니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail

depart_after = datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)
with Korail() as korail:
    result = korail.trains.search(
        "서울",
        "부산",
        depart_after=depart_after,
        include_no_seats=False,
        include_waiting_list=True,
    )
    for train in result.trains:
        print(train.summary())
        print(train.has_general_seat(), train.has_special_seat(), train.has_waiting_list())
    continuation = result.next_page()
    if continuation is not None:
        more = korail.trains.search(
            "서울",
            "부산",
            depart_after=depart_after,
            continuation=continuation,
            include_no_seats=False,
            include_waiting_list=True,
        )
        for train in more.trains:
            print(train.summary())
```

필터는 받은 한 페이지에만 적용합니다. `result.raw`, `result.response`, `result.metadata`는 서버 원본을 유지하고, 필터 전 열차 목록은 `result.unfiltered_trains`에 있습니다. 필터를 쓰지 않았으면 이 필드는 `None`입니다. `metadata.result_count`는 필터 전 서버의 값이며 표시할 열차 수는 `len(result.trains)`로 확인하세요.

필터 후 목록이 비어도 `next_page()`와 `next_query_from_last_departure(query)`는 필터 전 목록을 사용합니다. 따라서 뒤쪽 페이지를 놓치거나 마지막 표시 열차부터 다시 조회하지 않습니다. 다음 페이지를 검색할 때는 같은 필터 옵션을 다시 넘기세요. 필터 때문에 후속 요청을 자동으로 보내지는 않습니다.

`TrainSummary.duration_minutes`와 `duration_text`는 실제 출발·도착 날짜를 함께 계산해 자정이나 하루를 넘는 운행도 처리합니다. 날짜·시각이 없거나 잘못됐거나 도착이 출발보다 빠르면 `None`입니다. `summary()`는 원문 `raw`를 출력하지 않습니다. 역 이름 집합은 `korail.stations.names()`로 얻을 수 있습니다.

### 필요한 만큼 이어 읽기

`iter_search`는 **순회할 때** 다음 페이지를 요청합니다. `max_pages`는 필수이며 1~20 범위의 정수입니다. 각 업무 조회 전에 기존 대기열 정책을 그대로 적용합니다. 기본 `search`는 계속 한 페이지만 요청합니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail

with Korail() as korail:
    for train in korail.trains.iter_search(
        "서울", "부산", max_pages=3,
        depart_after=datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1),
    ):
        print(train.summary())
```

서버 커서가 있으면 먼저 사용하고, 없으면 필터 전 마지막 열차의 출발 날짜·시각으로 이어갑니다. 열차 번호·출발 일시·출도착역·운행일·열차 그룹/종별의 조합으로 중복을 제외합니다. 빈 페이지, 새 행 없음, 반복 커서, 시각 진전 없음, 명시적 마지막 페이지(`N`)에서 중단합니다. 시각을 임의로 더하지 않으므로 같은 시각의 서버 페이지 경계를 모두 열거한다고 보장하지 않습니다.
열차 번호·출발 일시·출도착역이 부족해 식별할 수 없는 행은 임의로 합치지 않고 그대로 전달한 뒤 추가 조회를 멈춥니다. 입력 시각은 처음 순회할 때 검증하고 고정하므로 대기열이 길어져도 후속 커서 조회의 시각이 바뀌지 않습니다.

필터 때문에 한 페이지가 비어도 서버 원본을 기준으로 이어갑니다. 첫 요청의 결과 없음 오류는 그대로 발생하며, 후속 요청의 결과 없음은 정상 종료합니다. 그 밖의 후속 오류는 이미 전달한 열차를 되돌리지 않고 그대로 발생합니다. 자동 재시도·감시·예약은 하지 않습니다. `max_pages`는 업무 조회 횟수의 상한이며 역 목록·대기열 요청은 별도입니다.

## 로그인과 승차권

```python
from getpass import getpass

from korail_mobile_api import Korail

with Korail.logged_in(input("회원번호·전화번호·이메일: "), getpass("비밀번호: ")) as korail:
    tickets = korail.tickets.all()
    print(sum(len(row.tickets) for row in tickets.reservations), "장")
    korail.logout()
```

`logged_in`은 로그인에 실패하면 연결을 닫고 원래 오류를 발생시킵니다. `with`가 끝나면 HTTP 연결을 닫지만 서버 로그아웃을 자동 요청하지는 않습니다. 로그아웃이 필요하면 예제처럼 명시적으로 호출하세요.

## 예약과 결제 전 확인

아래 예약 예제는 위 로그인 예제의 `with` 블록 안에서 `korail.logout()` 전에 실행합니다.
`train`은 그 블록에서 조회해 고른 열차이고, `card`는 준비한 `CardPayment`입니다.

`korail.reservations.create(train)`은 실제 미결제 홀드를 만듭니다. 예약 상세가 필요하면 `korail.reservations.detail(hold)`을 별도로 호출하세요. 예약 성공 직후 자동 상세 조회는 하지 않습니다. `korail.reservations.cancel(hold)`은 실제 취소이고, `korail.reservations.pay(hold, card)`는 실제 카드 청구입니다. `korail.tickets.refund_quote(ticket)`는 수수료 조회이며, `korail.tickets.refund(ticket, commission=fee)`는 실제 환불입니다. 각 메서드는 기존 클라이언트의 입력 검증과 응답 모델을 그대로 사용합니다. 자세한 주의사항은 [예약](reservations.md)과 [결제·환불](payments.md)에 있습니다.

`korail.tickets.refund_quote(ticket, *, companion=RefundCompanion())`는 동반자 정보도 받습니다(2.6.0부터, 3.0 전 이름은 `refund_fee`).
조회의 `ticket`은 `OriginalTicketReference`이고 환불 입력은 `PaidTicket.from_refund_detail(detail)`로 만듭니다.
동반자가 있으면 `RefundCompanion(name=paid.companion_name, certificate_no=paid.companion_certificate_no)`를
키워드 `companion=`으로 넘기세요. 실제 수수료 조회 응답과 환불 입력의 원표·동반자가 일치해야 하며,
직접 생성·파싱한 수수료 응답이나 원표 반환일이 없는 입력은 거절합니다. 자동 조회·재시도는 하지 않습니다.

### 일반실·특실 우선 선택

승객 구성은 [예약 승객 구성](reservations.md#passengers)과 같은 검증을 적용합니다.
`passengers.teenager > 0`이면 `reservations.create()`도 대기열·예약 요청 전에 `KorailProtocolError`로 거절합니다.

검색 인원은 예약에 자동 전달되지 않습니다. 아래처럼 같은 승객 객체를 두 호출에 전달하세요. 예약 성공이 요청 할인 적용을 보장하지는 않으므로 결제 전에 실제 정산액과 상세의 적용 결과도 확인합니다.

```python
from korail_mobile_api import KorailPassengerCounts

passengers = KorailPassengerCounts(adult=2, child=1)
result = korail.trains.search("서울", "부산", passengers=passengers)
train = next(train for train in result.trains if train.has_general_seat())
hold = korail.reservations.create(train, passengers=passengers)
print(hold.received_amount)
```

기본 예약은 일반실이고, `seat_class=KorailSeatClass.SPECIAL`로 특실을 직접 지정할 수 있습니다. 즉시 예약에서는 `option`으로 가용 객실을 고를 수도 있습니다.
아래 코드는 앞 예제의 예약 호출을 대체합니다. 검색과 `passengers`는 그대로 두고 두 예약 예제를 연달아 실행하지 마세요.

```python
from korail_mobile_api import KorailReserveOption

hold = korail.reservations.create(
    train,
    passengers=passengers,
    option=KorailReserveOption.GENERAL_FIRST,
)
```

| 옵션 | 선택 순서 |
| --- | --- |
| `GENERAL_FIRST` | 일반실, 없으면 특실 |
| `SPECIAL_FIRST` | 특실, 없으면 일반실 |
| `GENERAL_ONLY` | 일반실만 |
| `SPECIAL_ONLY` | 특실만 |

조회 결과의 객실 가용 코드로 요청 전에 선택하며, 허용한 객실에 좌석이 없으면 `KorailProtocolError`가 발생합니다. `option`과 `seat_class`를 함께 지정하거나 즉시 예약 이외의 `job_type`과 함께 지정하면 거절합니다. 예약대기는 기존처럼 `job_type=KorailReservationJobType.STANDBY`로 명시해야 합니다. 실제 요청 후 매진·실패가 발생해도 다른 객실로 재시도하지 않습니다.

앱이나 다른 도구에서 만든 예약은 `korail.reservations.get(pnr)`으로 가져올 수 있습니다. 기존 `korail.client.get_reservation_hold(pnr)`와 같은 검증을 거치며 직접 상세 조회를 한 번 실행합니다. 조회 실패나 결제에 사용할 수 없는 예약은 예외로 전달합니다.
금액을 확인하고 준비한 `CardPayment`를 넘기면 간편 API에서도 이어서 결제할 수 있습니다.

```python
hold = korail.reservations.get(input("결제할 예약번호(PNR): ").strip())
print(hold.pnr_no, hold.received_amount)
payment = korail.reservations.pay(hold, card)  # 실제 카드 청구
print(payment.str_result, payment.h_msg_cd, payment.h_msg_txt)
```

가져오기 단계의 검증 조건과 실서버 확인 범위는 [기존 예약 가져오기](payments.md#existing-reservation)에 있습니다.

## 마일리지와 쿠폰 조회

로그인한 상태에서 사용합니다. 마일리지 날짜는 `date` 또는 `datetime`이며, 시간대가 있으면 KST로 바꾼 날짜를 사용합니다. 종료일 기본값은 오늘 KST, 시작일 기본값은 종료일의 30일 전입니다. 기간·원장·증감·페이지 검증은 기존 조회를 따릅니다.

```python
from datetime import date

history = korail.membership.mileage(start_date=date(2026, 10, 1), end_date=date(2026, 10, 19))
for entry in history.entries:
    print(entry.departure_date, entry.point_amount)
coupons = korail.membership.coupons(page_no=1)
print(len(coupons.items))
```

기존 `MileageHistoryResponse`·`DiscountCouponListResponse`를 그대로 반환합니다. 한 페이지만 읽으며 잔액 필드를 임의로 합치거나 잘못된 금액을 0으로 바꾸지 않습니다.

## 공항버스 조회

정류장 이름·코드를 받아 기존 공항버스 조회를 호출합니다. 운행 그룹 `service_code`는 호출자가 확인한 값을 명시합니다. 보호된 예약 판매 구분은 추측하지 않으며 `reservation_sale_division_code` 기본 빈 값은 기존 조회처럼 전송에서 빠집니다. 객실·좌석 속성은 기존 SDK의 일반실(`1`)·버스 속성(`015`)을 사용합니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail

with Korail() as korail:
    stops = korail.airport_bus.stops()
    for stop in stops:
        print(stop.name, stop.code)
    result = korail.airport_bus.search(
        input("출발 정류장 이름·코드: "), input("도착 정류장 이름·코드: "),
        service_code=input("확인한 운행 그룹 코드: "),
        depart_after=datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1),
    )
    if result.schedules:
        inventory = korail.airport_bus.seats(result.schedules[0], passenger_count=1)
        print(len(inventory.seats))
```

정류장 목록은 이름·코드 공통코드를 한 번 받아 캐시하며 `stops(refresh=True)`로 갱신합니다. 목록 길이·필수값·이름/코드의 중복이 잘못되면 전체 원문을 가진 `KorailProtocolError`로 거절하고 잘못된 응답은 캐시하지 않습니다. 입력이 여러 정류장의 이름·코드와 겹치면 임의로 고르지 않고 `ValueError`로 거절합니다. 검색은 `LimousineScheduleResponse`, 좌석 조회는 배치·창문·원문을 포함한 `LimousineSeatInventoryResponse`입니다. 좌석 조회는 편의 필수 식별값을 에코하고 승객 수는 1~9명으로 제한합니다. 예약·결제·취소는 자동 실행하지 않습니다.

## 한 기기의 값 사용하기

```python
from korail_mobile_api import Korail, KorailDeviceProfile, build_config_from_profile

profile = KorailDeviceProfile(
    device_id="실제 기기 식별자",
    model="실제 기기 모델",
    android_release="안드로이드 버전",
    build_id="빌드 ID",
    android_sdk_int=37,
    width=1440,
    height=3120,
)
config = build_config_from_profile(profile)
with Korail(config) as korail:
    ...
```

호출자가 제공한 기기값을 DynaPath 토큰, 대기열 `User-Agent`, 화면·OS 설정에 함께 적용합니다. API `User-Agent`는 앱 관측값인 `korailtalk`를 유지합니다. 프로파일은 자격 증명이나 세션을 담지 않습니다. 이미 환경변수로 기기값을 관리한다면 [환경변수 설정](configuration.md#from-env)을 사용할 수도 있습니다.
