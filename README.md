> [!IMPORTANT]
> 이전 [`srt-mobile-api`](https://github.com/yakisoba0728/srt-mobile-api)의 개발과 기록은 이 저장소에서 이어갑니다.
>
> 이 프로젝트는 누구나 이슈와 Pull Request로 참여하고, 이 저장소를 중심으로 함께 개선하는 방식을 지향합니다.
> 저작자의 사전 승인 없이 포크나 다른 저장소를 이 프로젝트의 공식 운영본·공식 후속 프로젝트로 표방하거나, 공식 승인·제휴가 있는 것처럼 안내하는 행위를 금합니다.
> 기여를 위한 포크를 환영하며, 코드의 이용·수정·재배포에는 [Apache License 2.0](https://github.com/yakisoba0728/korail-mobile-api/blob/main/LICENSE)이 그대로 적용됩니다.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/banner-dark.svg">
    <img src="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/banner-light.svg" alt="korail-mobile-api — 코레일+ 앱 기반 비공식 Python 클라이언트" width="100%">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/yakisoba0728/korail-mobile-api/actions/workflows/ci.yml"><img src="https://github.com/yakisoba0728/korail-mobile-api/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <a href="https://pypi.org/project/korail-mobile-api/"><img src="https://img.shields.io/pypi/v/korail-mobile-api" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-3776AB?logo=python&amp;logoColor=white" alt="Python 3.11 | 3.12 | 3.13 | 3.14">
  <img src="https://img.shields.io/badge/typing-mypy%20strict-2A6DB2" alt="mypy strict">
  <a href="https://github.com/yakisoba0728/korail-mobile-api/blob/main/LICENSE"><img src="https://img.shields.io/github/license/yakisoba0728/korail-mobile-api" alt="License"></a>
</p>

<p align="center">
  <a href="https://yaki.kr/korail-mobile-api/">문서</a> ·
  <a href="#설치">설치</a> ·
  <a href="#빠르게-써보기">빠르게 써보기</a> ·
  <a href="#예약결제환불">예약·결제·환불</a> ·
  <a href="#지원-범위">지원 범위</a> ·
  <a href="#동작-방식">동작 방식</a> ·
  <a href="#개발">개발</a> ·
  <a href="#법적-고지">법적 고지</a>
</p>

코레일+ 안드로이드 앱의 요청·응답 형식을 바탕으로 만든 비공식 동기 Python 클라이언트입니다.
열차 조회, 예약·결제·환불과 승차권·계정 조회를 지원합니다.

KORAIL과는 관계없는 개인 프로젝트입니다. 공식 API가 아니라서 KORAIL이 서버나 앱을 바꾸면 언제든 깨질 수 있습니다.
쓰기 전에 [법적 고지](#법적-고지)는 꼭 읽어 주세요.

**현재 상태 (2026-10-23):** 2026-10-21부터 익명 열차 조회를 포함한 모든 요청이 `-8204`("원활한 예매 및 결제 서비스를 위해 최신 버전으로 업데이트해 주세요")로 실패한다는 보고가 있습니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)).
`2!` 기본 헤더 도입 전 `main`(1b89779)에서 기본 `AppVersion` 7.0.8과 `app_version="7.0.10"`만 바꾼 설정(API `Version` 250601003) 모두 실패했습니다.
기록된 실서버 성공은 2026-10-23 `AppVersion=7.0.10`·API `Version=250722001`·기본 `2!` 헤더 조합으로 병합 전 작업 트리에서 한 번 관측한 것뿐입니다.
2.6.2는 기본 버전을 바꾸지 않으며, 2.6.2의 기본 조합(`2!`·7.0.8·250601003)은 실서버에서 시도하지 않았습니다.
`KorailConfig(app_version="7.0.10", version="250722001")`이나 `build_config_from_env()`의 `KORAIL_APP_VERSION`·`KORAIL_API_VERSION`으로 시도해 볼 수 있지만 동작을 보장하지 않습니다.
자세한 내용은 [실서버 확인 현황](https://yaki.kr/korail-mobile-api/status/)과 [설정 가이드의 요청 버전](https://yaki.kr/korail-mobile-api/guide/configuration/#request-version)을 참고하세요.

2.6.2부터 기본 DynaPath로 SDK 2.0.1 `2!` 진단 헤더를 사용합니다. 프로파일·환경변수로 제공한 기기값만 토큰에 추가하며, 명시적 v1 설정·외부 공급자·대기열·무재시도 정책은 유지합니다. [검증 조건과 한계](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/verification-7010.md#diagnostic-20261023)를 참고하세요.

- **타입이 붙은 응답** — 서버 응답을 dataclass로 읽고, 원문은 `.raw`에 남깁니다. `.raw`의 개인정보는 자동으로 가리지 않습니다.
- **실수하기 어렵게** — 결제 금액은 홀드의 `received_amount`를 쓰며, 0원·예약대기 홀드의 카드 결제를 차단합니다. 2.6.0부터 환불은 성공한 수수료 조회와 대상 승차권의 연결도 확인합니다. 예약대기 홀드의 재계산은 요청 전에 거절하고, `reserve_merge`는 병합 유형으로만 보냅니다.
- **변경 요청 재전송 없음** — 예약·결제·환불 결과가 불명확해도 자동으로 같은 요청을 다시 보내지 않습니다.
- **오프라인 검증** — CI에서 Python 3.11~3.14와 최소 의존성 조합, 타입·포맷·문서, checkout 밖에 설치한 wheel까지 검사합니다.

## 버전과 호환 범위

**PyPI 배포본과 `main`의 미배포 변경은 구분하세요.** 패키지 버전 문자열이 같아도 포함된 변경이 다를 수 있습니다.

| 구분 | 현재 `main` |
|---|---|
| 패키지 버전 | `2.6.2`; 버전별 변경은 [CHANGELOG.md](https://github.com/yakisoba0728/korail-mobile-api/blob/main/CHANGELOG.md)에 기록 |
| 요청 기본 `AppVersion` | `7.0.8`(API `Version` 기본값 `250601003`과 별개); 2026-10-23 현재 이 기본값의 실서버 동작은 미확인 |
| 오류 메시지 사전 | 앱 `7.0.10` 기준 |

2.6.0에는 사전 갱신, 요청 필드 순서 정정, 환불 대상 연결 검증과 초장문 마일리지 숫자 처리 보완이 포함됩니다.
2.6.1에는 운임 입력 팩토리, 선택적 검색 이어보기와 멤버십·공항버스 간편 조회가 있습니다. 사용법은 [간편 API 가이드](https://yaki.kr/korail-mobile-api/guide/convenience/)를 참고하세요. 새 간편 흐름은 오프라인 검증만 완료했으며 실서버 확인 범위와 구분합니다.
2.6.2에는 기본 `2!` 헤더, `-8204` 분류, 버전 환경변수, 결제 안전 검사와 요청 전 입력 검사 보강이 있습니다. 2.6.2 코드로는 오프라인으로만 검증했습니다.
**2.5.0에서 수수료 응답을 직접 생성·파싱해 환불하던 호출은 변경해야 합니다.** 실제 수수료 조회 반환값과 원표 반환일·동반자 정보를 맞추세요.
사전의 앱 버전을 요청 기본값이나 전체 호환 인증으로 간주하지 않습니다.
`KorailConfig(app_version="7.0.10")`으로 명시한 제한적 실서버 확인과 정적 검토의 범위는
[7.0.10 검증 기록](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/verification-7010.md)에 구분돼 있습니다.

## 설치

Python 3.11 이상이 필요합니다.

```sh
pip install korail-mobile-api
```

검색 필터·객실 우선 선택·메시지 사전과 신규 오류 분류는 2.5.0부터 제공합니다.
환불 대상 연결 검증과 7.0.10 메시지 사전은 2.6.0부터 제공합니다.
운임 입력 팩토리·검색 이어보기·멤버십·공항버스 간편 조회는 2.6.1부터 제공합니다.
`-8204` 분류, `KORAIL_APP_VERSION`·`KORAIL_API_VERSION` 환경변수와 결제 안전 검사는 2.6.2부터 제공합니다.
이전 버전은 `pip install --upgrade korail-mobile-api`로 갱신하세요.

**개발 버전 설치:** `main`의 Unreleased 변경이 필요하면 GitHub에서 바로 설치할 수 있습니다.

```sh
pip install --force-reinstall "git+https://github.com/yakisoba0728/korail-mobile-api@main"
```

필수 런타임 의존성은 `httpx>=0.24.1`과 `cryptography>=42.0.8`입니다. SOCKS 프록시를 쓰려면 `pip install "korail-mobile-api[socks]"`로 설치하세요.

기존 예약을 가져오는 `get_reservation_hold`는 2.3.0부터 제공합니다. 이전 버전은 `pip install --upgrade korail-mobile-api`로 갱신하세요.

## 빠르게 써보기

열차 조회는 로그인 없이 됩니다. 다만 2026-10-23 현재 기본 설정 요청이 `-8204`로 거절될 수 있습니다(위 현재 상태 참고).

자주 쓰는 조회는 `with`와 KST `datetime`을 받는 간편 API로 시작할 수 있습니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail

with Korail() as korail:
    result = korail.trains.search(
        "서울", "부산", depart_after=datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)
    )
    for train in result.trains:
        print(train.train_no, train.departure_time)
```

간편 API는 처음 검색할 때 역 목록을 받아 입력을 확인합니다. 전체 요청 옵션과 모든 메서드는 아래의 `KorailClient`로 사용할 수 있습니다. 자세한 내용은 [간편 API 가이드](https://yaki.kr/korail-mobile-api/guide/convenience/)에 있습니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import KorailClient, TrainSearchQuery

departure_date = (datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)).strftime("%Y%m%d")

client = KorailClient()
try:
    query = TrainSearchQuery(
        departure_station_code="서울",
        arrival_station_code="부산",
        departure_date=departure_date,
        departure_time="090000",
    )
    result = client.search_trains(query)
    for t in result.trains:
        print(t.train_class_name, t.train_no, t.departure_time, t.arrival_time)
finally:
    client.close()
```

<p align="center">
  <img src="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/demo.svg" alt="열차 조회 실행 예시" width="100%">
</p>

역은 이름이나 역 코드 어느 쪽으로 넣어도 됩니다. 날짜는 `YYYYMMDD`, 시각은 `HHMMSS`입니다.
결과는 한 페이지씩 옵니다. `result.next_page()`가 `None`이 아니면 `client.search_trains(query, continuation=result.next_page())`로 다음 페이지를 받습니다.
`None`이면 `result.next_query_from_last_departure(query)`로 마지막 열차의 출발일·출발 시각부터 조회할 조건을 만들어 다시 조회할 수 있습니다. 마지막 열차가 다시 포함될 수 있으니 열차 번호로 중복을 거르세요.

로그인하면 내 승차권과 예약 내역도 볼 수 있습니다.

```python
from getpass import getpass

from korail_mobile_api import KorailClient

client = KorailClient()
try:
    client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    tickets = client.list_tickets()
    print(sum(len(r.tickets) for r in tickets.reservations), "장")
finally:
    try:
        client.logout()
    finally:
        client.close()
```

로그인 ID는 하이픈 없는 회원번호·전화번호나 이메일입니다. 로그인에 실패하면 계정 잠금 횟수에 들어갈 수 있으니 조심하세요.

## 예약·결제·환불

**예약·결제·취소·환불 메서드는 부르는 순간 실제로 처리됩니다.** 확인 창이나 미리보기 같은 건 없습니다.
예약하면 좌석이 잡히고, 결제하면 카드가 실제로 청구되고, 환불에는 수수료가 붙을 수 있습니다.

| 하려는 것 | 메서드 | 알아둘 점 |
|---|---|---|
| 좌석 잡기 (결제 전) | `reserve`, `reserve_transfer`, `reserve_merge`, `reserve_airport_bus` | 승객 구성은 조회할 때와 같게 넣습니다. |
| 결제 전 취소 | `cancel_unpaid_hold` | 결제한 표에는 쓰지 않습니다. |
| 기존 예약 가져오기 | `get_reservation_hold(pnr_no)` | 같은 계정의 예약 상세에서 결제용 홀드를 가져옵니다. 조회만 하며 새 예약이나 결제를 만들지 않습니다. |
| 카드 결제 | `pay_with_card` | 카드 거절은 예외가 아니라 FAIL 응답으로 돌아옵니다. |
| 환불 | `get_refund_fee` → `refund(..., commission=...)` | 승차권 한 장씩입니다. 실제 수수료 조회의 성공 응답과 원표 식별자·동반자 정보가 일치해야 하며, 직접 생성·파싱한 응답이나 원표 반환일이 없는 입력은 요청 전에 거절합니다. |
| 할인 재계산 | `PriceRecalculationRequest.for_hold` → `recalculate_price` | 결제는 재계산된 홀드로 합니다. |

변경 요청은 자동으로 다시 보내지 않습니다. 응답을 못 읽어서 예외가 나도 서버에서는 이미 처리됐을 수 있습니다.
그럴 땐 다시 보내지 말고 예외의 `.raw`를 보고, 예약은 `list_reservations()`, 결제·환불은 `list_tickets()`로 먼저 확인하세요.
예약 응답을 읽지 못한 홀드는 `get_reservation_hold`도 같은 이유로 실패할 수 있습니다. 취소 방법은 [오류 처리 가이드](https://yaki.kr/korail-mobile-api/guide/errors/#unparsed-hold)에 있습니다.

2.6.0부터 환불은 대상 연결을 확인할 수 없으면 거절하는 fail-closed 정책입니다. `PaidTicket.from_refund_detail()` 사용을 권하며, 수동 생성 시 현재 `sale_date`와 별도로 `return_sale_date`를 명시하세요. 수수료 조회 연결은 금액의 유효기간이나 서버 승인을 보장하지 않습니다. [환불 가이드](https://yaki.kr/korail-mobile-api/guide/payments/#commission)를 참고하세요.

앱이나 다른 패키지에서 예약한 표는 로그인 후 `hold = client.get_reservation_hold(pnr_no)`로 가져와
금액을 확인하고 `client.pay_with_card(hold, card)`로 결제할 수 있습니다.
창구번호와 금액을 임의로 채우지 않으며, 유효한 여정·좌석·정산액이 필요합니다. 결제 플래그는 상세에서 생략될 수 있고, 명시된 경우에만 `Y`를 요구합니다.
2026년 9월 29일 실서버에서 기존 예약 가져오기를 확인했습니다. 실제 카드 결제와 N카드 예약 복원은 별도 검증하지 않았습니다. [기존 예약 결제 예제](https://yaki.kr/korail-mobile-api/guide/payments/#existing-reservation)를 참고하세요.

## 지원 범위

현재 공개 메서드는 85개입니다. **메서드 제공, 오프라인 테스트 통과, 실서버 성공은 서로 다른 확인 범위입니다.**

2026년 10월 19일에는 개발 소스의 `AppVersion=7.0.10`을 명시해 64개 메서드(로컬 전용 2개 포함)를 실행한 기록이 있습니다.
일부 조회·인증과 직통·환승 임시 예약 후 취소를 확인했지만 실제 카드 결제·환불은 하지 않았습니다.
유효한 수수료 응답과 환불 대상 연결의 정상 실서버 흐름도 미검증입니다.
전체 내역과 미실행 21개의 한계는 [7.0.10 제한적 실서버 확인](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/verification-7010.md)을 참고하세요.

아래 표는 별도의 과거 기록입니다. 당시의 84개 메서드를 2026년 9월 28일 코레일+ 7.0.8 설정으로 확인했고,
이후 추가한 `get_reservation_hold`의 실서버 조회는 9월 29일 확인했습니다. 새 기록을 아래 집계에 합산하지 않습니다.
메서드별 결과는 [7.0.8 검증표](https://yaki.kr/korail-mobile-api/verification-708/)와 [실서버 확인 현황](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/status.md)에 있습니다.

| 7.0.8 결과 | 메서드 수 | 의미 |
|---|---:|---|
| 응답 파싱 | 59 | 실서버 호출 후 반환 객체를 받았습니다. 빈 목록·결과 없음도 포함됩니다. |
| 서버 거절 | 10 | 요청은 도달했으나 정상 결과는 받지 못했습니다. |
| 미실행 | 13 | 보유 N카드, 유효한 승차권, 좌석 QR, 결제수단 등의 전제 자료가 없었습니다. |
| 로컬 메서드 | 2 | 네트워크를 사용하지 않습니다. |

2026년 9월 24~26일의 [7.0.6 시기 검증 기록](https://yaki.kr/korail-mobile-api/status/)에는 카드 결제와 환불 성공 사례가 있습니다. 이는 7.0.8에서 결제·환불을 재실행했다는 뜻이 아닙니다.

메서드는 있지만 정상 실서버 흐름을 확인하지 못한 주요 경로입니다.

- N카드: 구매, 기간 연장, N카드로 예약, 사용 내역, 이용 가능 열차의 정상 조회, 2인 승차권 수령자 조회
- 셀프 체크인: 좌석 확인, 등록, 취소
- 역에서 산 승차권 환불: 확인, 실행
- 다른 회원에게 전달한 승차권 회수

간편 로그인(카카오·네이버 등), 여행상품 검색·예약·결제, 부가서비스 구매·결제·환불은 지원하지 않습니다.
앱에서 필요한 값이 암호화돼 있거나 외부 SDK를 거쳐야 해서입니다.
정기권·패스 구매, 다른 회원에게 승차권 전달, 승차권 변경도 지원하지 않습니다. 관련 정보를 조회하는 메서드는 있지만 실행하는 메서드는 없습니다.

## 동작 방식

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/flow-dark.svg">
    <img src="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/flow-light.svg" alt="요청 흐름" width="100%">
  </picture>
</p>

- 폼은 확인한 앱 직렬화 순서를 따릅니다. 환불·수수료 조회는 공통 필드를 먼저, 은행 직접 필드는 `Device, Version, Key, AppVersion` 순서로 만듭니다. 순서에 따른 서버 영향은 미확인입니다.
- 좌석배정 조회의 `*2` 이상 번호 그룹은 앱 DTO와 동일한 형식으로 확인된 것이 아니라 기존 SDK 확장입니다.
- 열차 조회, 일부 예약(`reserve`, `reserve_transfer`, `reserve_with_discount_card`), 카드 결제, 예약 내역 조회 전에는 앱처럼 NetFunnel 대기열을 거칩니다. 기본으로 켜져 있습니다.
- 로그인 비밀번호는 앱처럼 AES로 암호화해서 보냅니다.
- 응답을 못 읽으면 받은 원문 전체를 예외의 `.raw`에 담아 던집니다.

더 자세한 규칙과 앱과 다르게 처리한 부분은 [checks/BEHAVIOR.md](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/BEHAVIOR.md)에 정리해 뒀습니다.

## 자주 묻는 질문

**SRT는요?**
SRT는 2026년 9월 통합 때 KTX로 합쳐져서 이제 따로 없습니다. 예매는 코레일+ 앱 하나로 하고, 이 라이브러리도 그 앱의 요청을 씁니다.
SRT 앱용으로 만들었던 [srt-mobile-api](https://github.com/yakisoba0728/srt-mobile-api)는 개발을 멈추고 이 저장소로 이어졌습니다.

**대기열을 끄면 빨라지나요?**
`KorailConfig(netfunnel_enabled=False)`로 끌 수는 있습니다. 하지만 앱과 다르게 동작하게 되고 KORAIL의 혼잡 제어를 건너뛰는 셈이라 권하지 않습니다.

**모든 요청이 `-8204`로 실패해요.**
2026-10-21부터 보고된 서버 응답으로, 앱 업데이트 안내입니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)). 네트워크 차단(`-8202` 등)과는 다릅니다.
2.6.2부터 로그인을 포함한 모든 경로에서 `KorailAppUpdateRequiredError`로 분류하고 서버 메시지를 그대로 남깁니다.
기록된 성공은 2026-10-23 `AppVersion=7.0.10`·API `Version=250722001`·기본 `2!` 헤더 조합의 1회 관측뿐입니다.
`KorailConfig(app_version="7.0.10", version="250722001")`로 두 값을 함께 바꿔 시도할 수 있지만 동작을 보장하지 않습니다. `app_version`만 바꾼 설정은 실패가 보고됐습니다.

**클라우드 서버에서는 로그인이 막혀요.**
KORAIL은 데이터센터·VPN IP 대역에서 오는 요청을 막습니다. Oracle Cloud나 Vercel 같은 곳에서 `KorailDynaPathError`(HTTP 403, `-8202` 등)가 나고, 같은 코드가 집 네트워크에서는 되는 사례가 보고됐습니다.
라이브러리의 요청 형식 문제가 아니라 요청이 나가는 네트워크의 문제입니다. 2.4.0부터는 `KorailConfig(proxy="socks5://...")`로 KORAIL 요청만 본인이 관리하는 다른 네트워크로 보낼 수 있습니다. 자세한 내용은 [설정 가이드의 프록시](https://yaki.kr/korail-mobile-api/guide/configuration/#proxy)를 보세요.

**비밀번호나 카드 번호는 어디에 저장되나요?**
어디에도 저장하지 않습니다. KORAIL 서버로만 보내고 파일로 쓰지 않습니다.
다만 응답 모델과 예외의 `.raw`에는 개인정보가 그대로 들어 있으니 로그에 그대로 찍지 않도록 조심하세요.
2.6.2부터 네트워크 오류로 `KorailTransportError.__cause__`에 붙는 httpx 예외에는 메서드와 쿼리를 뺀 URL만 남고 본문·쿠키·DynaPath 토큰은 지웁니다. 응답 모델, `.raw`, `dataclasses.asdict`와 pickle 결과는 여전히 가리지 않습니다.

## 문서와 링크

- [문서 사이트](https://yaki.kr/korail-mobile-api/) — 시작하기, 가이드, 메서드 83개 전체의 API 레퍼런스
- [동작 규칙 (checks/BEHAVIOR.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/BEHAVIOR.md) — 요청을 만드는 규칙, 응답을 읽는 규칙, 앱과 다르게 한 부분
- [변경 이력 (CHANGELOG.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/CHANGELOG.md)
- [오프라인 검사 기준 (checks/ACCEPTANCE.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/ACCEPTANCE.md)
- [AI 에이전트 작업 가이드 (AGENTS.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/AGENTS.md) — 작업별 코드 위치, 안전 경계, 테스트와 완료 기준
- [배포 절차](https://yaki.kr/korail-mobile-api/releasing/) — 버전, 검증, 패키지 빌드, PyPI와 문서 배포
- 한국철도공사 공식 홈페이지 — <https://www.korail.com>
- 코레일+ 앱 — [Google Play](https://play.google.com/store/apps/details?id=com.korail.talk) · [App Store](https://apps.apple.com/kr/app/id1000558562)
- 이전 SRT 클라이언트 — [srt-mobile-api](https://github.com/yakisoba0728/srt-mobile-api)

## 개발

저장소 루트 기준 macOS·Linux 예시입니다. 에이전트로 작업한다면 먼저 [AGENTS.md](https://github.com/yakisoba0728/korail-mobile-api/blob/main/AGENTS.md)를 읽어 주세요.

```sh
git clone https://github.com/yakisoba0728/korail-mobile-api
cd korail-mobile-api
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]' -r docs/requirements.txt

.venv/bin/python -m pytest tests/ --cov=korail_mobile_api --cov-branch --cov-report=term-missing:skip-covered --cov-fail-under=90
.venv/bin/python -m ruff check src checks tests
.venv/bin/python -m ruff format --check src checks tests
.venv/bin/python -m mypy
.venv/bin/python -m pyright
.venv/bin/actionlint -shellcheck= -pyflakes=
.venv/bin/python -m mkdocs build --strict
git diff --check
```

전체 테스트는 합성 응답과 소켓 차단을 사용하며, 두 기존 오프라인 검사·문서 예제·실제 wheel/sdist 내용 검사도 포함합니다.
CI는 새 가상환경에 wheel을 설치하고 checkout 밖에서 공개 호출·7.0.10 독립 계약·환불 연결을 다시 확인합니다.
신규 간편 조회도 설치된 wheel에서 검사합니다. 주간 CI와 Dependabot으로 갱신을 확인하고, actionlint와 Trivy로 워크플로·해석된 런타임 의존성·비밀·설정을 검사합니다. 스캔은 실서버 호환 검사나 모든 취약점의 부재를 보장하지 않습니다. 패키지·문서 배포는 계속 수동입니다.
이는 전체 wire 계약이나 실서버 수용을 증명하지 않습니다. README의 사용 예제는 테스트 밖에서 실행하면 실제 서버에 접속합니다.
검사별 한계는 [오프라인 검사 기준](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/ACCEPTANCE.md),
배포 검증은 [배포 절차](https://github.com/yakisoba0728/korail-mobile-api/blob/main/docs/releasing.md)에 있습니다.
버그나 앱 업데이트로 달라진 부분을 찾으면 이슈로 알려 주세요.

## 법적 고지

- 이 프로젝트는 한국철도공사(KORAIL)와 관계없는 개인의 비공식 프로젝트이며, 후원·승인·지원을 받지 않았습니다. 통합 전의 (주)에스알(SR)과도 관계없습니다.
- KORAIL, 코레일, 코레일+, 코레일톡, KTX, SRT 등의 이름과 상표는 각 권리자의 것입니다. 이 저장소는 무엇과 호환되는지 설명하려고 이름만 씁니다. 저장소의 이미지는 직접 만들었고 공식 로고는 쓰지 않았습니다.
- 저장소에는 앱 설치 파일(APK)이나 디컴파일한 앱 소스를 넣지 않았습니다. 라이브러리는 앱과 호환되도록 요청 형식만 재현합니다.
- 이 라이브러리로 하는 예약·결제·환불은 전부 실제 거래입니다. 그 결과와 비용은 사용자 책임입니다.
- KORAIL 서비스를 쓸 때는 KORAIL의 이용약관과 여객운송약관을 따라야 합니다. 자동화된 방식으로 쓰는 것이 약관에 맞는지는 사용자가 직접 확인해야 합니다.
- KORAIL은 매크로 탐지 시스템을 운영하고 있습니다. 자동 프로그램 사용이 의심되면 로그인·조회 단계부터 접속을 막고, 대량 구매·취소에 쓰인 카드는 1년 동안 승차권 결제를 제한한다고 밝혔습니다([2025년 10월 보도](https://www.paxetv.com/news/articleView.html?idxno=248146)).
- 승차권을 상습적으로 또는 영업으로 산 값보다 비싸게 되팔거나 이를 알선하는 행위는 [철도사업법 제10조의2](https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%B2%A0%EB%8F%84%EC%82%AC%EC%97%85%EB%B2%95)로 금지돼 있고, 최대 1천만 원의 과태료가 부과될 수 있습니다. 이 라이브러리를 암표, 좌석 선점, 대량 예매에 쓰지 마세요.
- 계정과 카드 정보 관리는 사용자 몫입니다. 라이브러리는 로그나 `.raw`의 개인정보를 가리지 않습니다.
- 이 소프트웨어는 Apache License 2.0에 따라 "있는 그대로" 제공되며 어떤 보증도 하지 않습니다. 사용하다 생긴 손해에 대해 저작자는 책임지지 않습니다.
- 어떤 용도로 쓰든 막지는 않습니다. 다만 되도록 개인 용도로만 쓰고, 상업적이거나 불법적인 용도로는 쓰지 말아 주세요. 라이선스 조건이 아니라 부탁입니다.

## 라이선스

[Apache License 2.0](https://github.com/yakisoba0728/korail-mobile-api/blob/main/LICENSE)
