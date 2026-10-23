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
요청 형식은 코레일+ 안드로이드 앱 7.0.8에서 확인한 계약과 [7.0.10 정적 검토](verification-7010.md)를 근거로 합니다.
이 문서는 배포 전인 3.0.0을 설명합니다. 2.x에서 옮겨 오려면 [3.0으로 옮기기](migration-3.0.md)를 보세요.

!!! warning "2026-10-23 현재 상태"
    2026-10-21부터 `-8204`(앱 업데이트 안내) 실패가 보고됐습니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)). 보고는 `2!` 헤더 도입 전 코드였습니다.
    2026-10-23 08:16 KST의 2.6.2 기본 설정 익명 조회 성공은 [당시 기록](records.md#live-check-262)에 있습니다.
    같은 날 23:34:34 KST에는 `3.0.0.dev0` 개발 wheel의 기본 요청 버전으로 익명 서울→부산 직통 첫 페이지 조회 1회가 `SUCC`/`IRG000000`, 열차 10개를 반환했습니다([입력·커밋·관측 한계](records.md#live-check-300-dev0-20261023)).
    3.0.0은 배포 전이며 한 노선·날짜·시각의 관측은 출시판의 호환 보증이 아닙니다. 3.0의 로그인·인증 조회·예약·취소·결제·환불은 실서버 미검증입니다.

!!! warning "비공식 라이브러리입니다"
    KORAIL이 제공하거나 승인한 API가 아닙니다. KORAIL이 서버나 앱을 바꾸면 예고 없이 동작하지 않을 수 있습니다.
    예약·결제·환불 메서드는 호출하는 즉시 실제로 처리됩니다. 사용하기 전에 [법적 고지](legal.md)를 읽어 주세요.

## 설치

Python 3.11 이상이 필요합니다.

```sh
pip install korail-mobile-api
```

PyPI의 최신 배포는 2.6.2(2.x API)입니다. 3.0 개발판은 [개발 버전](getting-started.md#development-version)으로 설치합니다.

## 예제

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import KorailClient, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

with KorailClient() as client:
    result = client.search_trains(
        TrainSearchQuery(
            departure_station="서울",
            arrival_station="부산",
            departure_date=departure_date,
            departure_time="090000",
        )
    )
    for train in result.trains:
        print(train.train_class_name, train.train_no, train.departure_time, train.arrival_time)
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

    `KorailClient`의 공개 메서드 83개를 매개변수, 반환값, 예외와 함께 정리했습니다.

-   :material-cog-outline: **[동작 원리](concepts/how-it-works.md)**

    ---

    요청을 만드는 규칙, 대기열, 응답을 읽는 규칙, 앱과 다르게 처리한 부분과 확인되지 않은 부분입니다.

</div>

## 지원 범위

메서드 제공, 오프라인 테스트 통과, 실서버 성공은 서로 다른 확인 범위입니다. 영역별 최근 실서버 기록은 [실서버 확인 현황](status.md#by-area)에, 날짜별 원래 기록은 [날짜별 실서버 기록](records.md)에 있습니다.

| 지원 | 지원하지 않음 |
|---|---|
| 로그인, 열차 조회(직통·환승), 호차·좌석 조회, 운임 조회 | 간편 로그인(카카오·네이버 등) |
| 예약(일반·좌석 지정·예약대기·환승·병합), 홀드 취소 | 여행상품 검색·예약·결제 |
| 카드 결제, 할인 재계산, 환불 | 부가서비스 구매·결제·환불 |
| 승차권·예약 내역, 영수증, 마일리지, 쿠폰, 지연확인증 | 정기권·패스 구매 |
| 정기권·패스 조회, N카드, 여행상품 예약 조회·취소, 공항버스, 대리수령 조회·회수, 셀프 체크인 | 다른 회원에게 승차권 전달, 승차권 변경 |
