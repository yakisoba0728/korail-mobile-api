---
hide:
  - navigation
---

# korail-mobile-api

![korail-mobile-api](assets/banner-light.svg#only-light)
![korail-mobile-api](assets/banner-dark.svg#only-dark)

`korail-mobile-api`는 코레일+ 안드로이드 앱이 KORAIL 서버에 보내는 요청을 그대로 재현하는 비공식 Python 클라이언트입니다.
열차 조회, 예약, 결제, 환불과 승차권·계정 조회를 Python 코드로 할 수 있습니다.

2026년 9월 KORAIL과 SR이 통합되면서 SRT는 KTX로 합쳐졌고, 코레일톡은 코레일+로 이름이 바뀌었습니다.
이 라이브러리는 코레일+ 안드로이드 앱 7.0.6을 기준으로 합니다.

!!! warning "비공식 라이브러리입니다"
    KORAIL이 제공하거나 승인한 API가 아닙니다. KORAIL이 서버나 앱을 바꾸면 예고 없이 동작하지 않을 수 있습니다.
    예약·결제·환불 메서드는 호출하는 즉시 실제로 처리됩니다. 사용하기 전에 [법적 고지](legal.md)를 읽어 주세요.

## 설치

Python 3.11 이상이 필요합니다. PyPI에는 배포하지 않으며 GitHub에서 설치합니다.

```sh
pip install "git+https://github.com/yakisoba0728/korail-mobile-api"
```

## 예제

```python
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    result = client.search_trains(
        TrainSearchQuery(
            departure_station_code="서울",
            arrival_station_code="부산",
            departure_date="20261002",
            departure_time="090000",
        )
    )
    for train in result.trains:
        print(train.train_class_name, train.train_no, train.departure_time, train.arrival_time)
finally:
    client.close()
```

## 문서 구성

<div class="grid cards" markdown>

-   :material-rocket-launch-outline: **[시작하기](getting-started.md)**

    ---

    설치부터 첫 열차 조회, 로그인과 로그아웃까지 한 번에 따라 합니다.

-   :material-book-open-variant: **[가이드](guide/trains.md)**

    ---

    열차 조회, 예약, 결제와 환불, 설정, 오류 처리를 작업 순서대로 설명합니다.

-   :material-code-braces: **[API 레퍼런스](api/index.md)**

    ---

    `KorailClient`의 공개 메서드 84개를 매개변수, 반환값, 예외와 함께 정리했습니다.

-   :material-cog-outline: **[동작 원리](concepts/how-it-works.md)**

    ---

    요청을 만드는 규칙, 대기열, 응답을 읽는 규칙, 앱과 다르게 처리한 부분과 확인되지 않은 부분입니다.

</div>

## 지원 범위

공개 메서드 84개 중 66개는 실서버에서 정상 응답을 확인했습니다. 메서드별 결과는 [실서버 확인 현황](status.md)에 있습니다.

| 지원 | 지원하지 않음 |
|---|---|
| 로그인, 열차 조회(직통·환승), 호차·좌석 조회, 운임 조회 | 간편 로그인(카카오·네이버 등) |
| 예약(일반·좌석 지정·예약대기·환승·병합), 결제 전 취소 | 여행상품 검색·예약·결제 |
| 카드 결제, 할인 재계산, 환불 | 부가서비스 구매·결제·환불 |
| 승차권·예약 내역, 영수증, 마일리지, 쿠폰, 지연확인증 | 정기권·패스 구매 |
| 정기권·패스 조회, N카드, 여행상품 예약 조회·취소, 공항버스, 대리수령 조회·회수, 셀프 체크인 | 다른 회원에게 승차권 전달, 승차권 변경 |
