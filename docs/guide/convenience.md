# 간편 API

[`Korail`][korail_mobile_api.facade.Korail]은 기존 `KorailClient` 위에 자주 쓰는 작업을 묶은 선택형 진입점입니다. 전체 API나 세부 요청 옵션은 `korail.client`에서 그대로 사용합니다.

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

시간대가 없는 `datetime`은 한국 시각(KST)으로 읽고, 시간대가 있는 값은 KST로 변환합니다. 이미 지난 시각은 요청 전에 거절합니다. 시각을 생략하면 현재 KST를 사용합니다. 결과는 기존 `TrainSearchResult`이며 한 페이지씩 옵니다. `result.next_page()`가 값을 돌려주면 같은 조건과 `continuation=...`으로 다음 페이지를 조회하세요. `next_page()`가 `None`이어도 더 조회해야 하는 경우에는 [원래 조회 API의 마지막 열차 시각 방식](trains.md#next-page)을 사용합니다.

기본적으로 첫 검색에서 역 목록을 가져와 역 이름·코드를 확인한 후 클라이언트 수명 동안 캐시합니다. 잘못된 역은 검색 요청 전에 `ValueError`로 거절하고 가까운 역 이름을 제안합니다. 이 추가 조회가 필요 없으면 `Korail(validate_stations=False)`로 생성하세요. 역 목록은 `korail.stations.all(refresh=True)`로 갱신할 수 있습니다.

`include_nearby_stations=True`는 인접역 일정 표시 필드 `adjStnScdlOfrFlg=Y`를 보냅니다. 기본값은 이전과 같은 `N`입니다. 2026-09-28 실서버에서 두 값 모두 검색 성공 응답을 받았지만, 결과에 미치는 효과는 확인하지 못했습니다.

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

`korail.reservations.create(train)`은 실제 미결제 홀드를 만듭니다. 예약 상세가 필요하면 `korail.reservations.detail(hold)`을 별도로 호출하세요. 예약 성공 직후 자동 상세 조회는 하지 않습니다. `korail.reservations.cancel(hold)`은 실제 취소이고, `korail.reservations.pay(hold, card)`는 실제 카드 청구입니다. `korail.tickets.refund_fee(ticket)`는 수수료 조회이며, `korail.tickets.refund(ticket, commission=fee)`는 실제 환불입니다. 각 메서드는 기존 클라이언트의 입력 검증과 응답 모델을 그대로 사용합니다. 자세한 주의사항은 [예약](reservations.md)과 [결제·환불](payments.md)에 있습니다.

앱이나 다른 도구에서 만든 예약은 로그인한 `korail`의 클라이언트로 가져올 수 있습니다(2.3.0 이상).
금액을 확인하고 준비한 `CardPayment`를 넘기면 간편 API에서도 이어서 결제할 수 있습니다.

```python
hold = korail.client.get_reservation_hold(input("결제할 예약번호(PNR): ").strip())
print(hold.pnr_no, hold.received_amount)
payment = korail.reservations.pay(hold, card)  # 실제 카드 청구
print(payment.str_result, payment.h_msg_cd, payment.h_msg_txt)
```

가져오기 단계의 검증 조건과 실서버 확인 범위는 [기존 예약 가져오기](payments.md#existing-reservation)에 있습니다.

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
