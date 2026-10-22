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
이 라이브러리는 코레일+ 안드로이드 앱 7.0.8의 확인된 요청·응답 계약을 기준으로 합니다.

2.6.0은 오류 사전을 7.0.10 기준으로 갱신하고 요청 순서 정정·환불 대상 연결 검증·초장문 숫자 처리 보완을 포함합니다.
2.6.1은 운임 입력 팩토리·선택적 검색 이어보기·멤버십·공항버스 간편 조회를 추가합니다. 새 간편 흐름은 오프라인 검증만 완료했습니다.
2.6.2는 기본 `2!` DynaPath 헤더, `-8204` 분류, 버전 환경변수, 결제 안전 검사와 요청 전 입력 검사를 추가합니다. 2.6.2로는 로그인 없는 열차 조회만 실서버에서 확인했습니다.
요청 기본 `AppVersion=7.0.8`과 API `Version`은 패키지 버전과 별개로 유지합니다.
[7.0.10 정적 검토](verification-7010.md)는 85개 메서드 행의 대조이며 전체 wire 계약·실서버 호환 검증이 아닙니다.
환불 대상 연결의 fail-closed 변경은 [환불 가이드](guide/payments.md#commission)에 안내합니다.

!!! warning "2026-10-23 현재 상태"
    2026-10-21부터 `-8204`(앱 업데이트 안내) 실패가 보고됐습니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)). 보고는 `2!` 헤더 도입 전 코드였습니다.
    2026-10-23 확인에서 2.6.2 기본 설정의 로그인 없는 열차 조회는 성공했습니다. 2.6.2 이상을 쓰세요. 확인 범위는 [실서버 확인 현황](status.md#live-check-262)에 있습니다.

!!! warning "비공식 라이브러리입니다"
    KORAIL이 제공하거나 승인한 API가 아닙니다. KORAIL이 서버나 앱을 바꾸면 예고 없이 동작하지 않을 수 있습니다.
    예약·결제·환불 메서드는 호출하는 즉시 실제로 처리됩니다. 사용하기 전에 [법적 고지](legal.md)를 읽어 주세요.

## 설치

Python 3.11 이상이 필요합니다.

```sh
pip install korail-mobile-api
```

검색 필터·객실 우선 선택·메시지 사전과 신규 오류 분류는 2.5.0부터 제공합니다.
환불 대상 연결 검증과 7.0.10 메시지 사전은 2.6.0부터 제공합니다.
운임 입력 팩토리·검색 이어보기·멤버십·공항버스 간편 조회는 2.6.1부터 제공합니다.
이전 버전은 `pip install --upgrade korail-mobile-api`로 갱신하세요.

## 예제

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import KorailClient, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

client = KorailClient()
try:
    result = client.search_trains(
        TrainSearchQuery(
            departure_station_code="서울",
            arrival_station_code="부산",
            departure_date=departure_date,
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

    `KorailClient`의 공개 메서드 85개를 매개변수, 반환값, 예외와 함께 정리했습니다.

-   :material-cog-outline: **[동작 원리](concepts/how-it-works.md)**

    ---

    요청을 만드는 규칙, 대기열, 응답을 읽는 규칙, 앱과 다르게 처리한 부분과 확인되지 않은 부분입니다.

</div>

## 지원 범위

2026년 9월 28일 7.0.8 재검증에서는 공개 메서드 84개 중 59개가 응답 파싱, 10개가 서버 거절 확인, 13개가 전제 자료 부족으로 미실행, 2개가 로컬 메서드였습니다. 메서드별 근거는 [7.0.8 전수 확인표](verification-708.md)에 있습니다. [실서버 확인 현황](status.md)에는 2026년 9월 24~26일의 7.0.6 시기 기록도 남겨 두었습니다.

2.3.0에는 기존 예약번호로 카드 결제용 홀드를 가져오는 [`get_reservation_hold`](api/reservations.md#get_reservation_hold)를 추가했습니다.
현재 공개 메서드는 85개이며, 새 메서드의 기존 예약 상세 조회는 2026년 9월 29일 실서버에서 확인했습니다. 실제 카드 결제와 N카드 예약 복원은 별도 검증하지 않았습니다. [기존 예약 결제 가이드](guide/payments.md#existing-reservation)를 참고하세요.

2.4.0에는 KORAIL API·대기열 요청만 지정한 프록시로 보내는 [`proxy`](guide/configuration.md#proxy) 설정을 추가했습니다. 프록시를 거친 실서버 요청은 아직 확인하지 않았습니다.

2.5.0에는 [간편 검색 필터·객실 우선 선택·역 이름·기존 예약 조회](guide/convenience.md)와
[메시지 사전·표시 메시지·새 오류 분류](guide/errors.md)를 추가했습니다. 청소년 예약 사전 거절과 정리 중 원래 예외 보존도 적용합니다.
출시 전 `main`에서 HTTP 105건과 대표 흐름을 확인했고 승인된 임시 홀드 2개는 모두 취소했습니다.
실제 결제·환불은 실행하지 않았으며 상세 범위와 한계는 [2.5.0 출시 전 검증](verification-250.md)에 있습니다.

| 지원 | 지원하지 않음 |
|---|---|
| 로그인, 열차 조회(직통·환승), 호차·좌석 조회, 운임 조회 | 간편 로그인(카카오·네이버 등) |
| 예약(일반·좌석 지정·예약대기·환승·병합), 결제 전 취소 | 여행상품 검색·예약·결제 |
| 카드 결제, 할인 재계산, 환불 | 부가서비스 구매·결제·환불 |
| 승차권·예약 내역, 영수증, 마일리지, 쿠폰, 지연확인증 | 정기권·패스 구매 |
| 정기권·패스 조회, N카드, 여행상품 예약 조회·취소, 공항버스, 대리수령 조회·회수, 셀프 체크인 | 다른 회원에게 승차권 전달, 승차권 변경 |
