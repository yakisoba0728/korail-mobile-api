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

코레일+ 안드로이드 앱의 요청·응답 형식을 바탕으로 만든 비공식 동기 Python 클라이언트입니다.
열차 조회, 예약·결제·환불과 승차권·계정 조회를 지원합니다. 응답은 타입이 붙은 dataclass로 읽고 서버 원문은 `.raw`에 남깁니다.

KORAIL과 관계없는 개인 프로젝트이며 공식 API가 아닙니다. KORAIL이 서버나 앱을 바꾸면 언제든 깨질 수 있고,
예약·결제·환불 메서드는 부르는 순간 실제로 처리됩니다. 쓰기 전에 아래 법적 고지를 읽어 주세요.

## 현재 상태 (2026-10-23)

- 2026-10-21부터 익명 열차 조회를 포함한 모든 요청이 `-8204`("원활한 예매 및 결제 서비스를 위해 최신 버전으로 업데이트해 주세요")로 실패한다는 보고가 있습니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)).
- 보고된 실패는 `2!` 기본 헤더 도입 전 `main`(1b89779)에서 기본값과 `app_version="7.0.10"`만 바꾼 설정으로 재현됐습니다.
- 2026-10-23 08:16 KST에 PyPI의 2.6.2로 로그인 없는 직통 열차 조회(서울→부산)를 실서버에서 확인했습니다. 기본 조합(`2!`·7.0.8·250601003)과 `KorailConfig(app_version="7.0.10", version="250722001")` 모두 `SUCC`/`IRG000000`이었습니다. 기본 요청 버전은 바꾸지 않습니다.
  로그인·예약·결제는 2.6.2로 다시 확인하지 않았습니다.
- 이 README는 배포 전인 3.0.0(`main`)을 설명합니다. 3.0 코드로는 실서버에 요청하지 않았습니다. PyPI의 최신 배포는 2.6.2이며 사용법은 [2.6.2 README](https://github.com/yakisoba0728/korail-mobile-api/blob/v2.6.2/README.md)에 있습니다.

자세한 내용은 [실서버 확인 현황](https://yaki.kr/korail-mobile-api/status/)과 [설정 가이드의 요청 버전](https://yaki.kr/korail-mobile-api/guide/configuration/#request-version)에 있습니다.
2.x에서 옮겨 오려면 [3.0으로 옮기기](https://yaki.kr/korail-mobile-api/migration-3.0/)를 보세요. 옛 이름의 별칭은 없습니다.

## 설치

Python 3.11 이상이 필요합니다. 필수 의존성은 `httpx>=0.24.1`과 `cryptography>=42.0.8`입니다.

```sh
# PyPI 최신 배포 2.6.2 (2.x API)
pip install korail-mobile-api
# 배포 전 3.0 (main)
pip install --force-reinstall "git+https://github.com/yakisoba0728/korail-mobile-api@main"
```

`main`의 패키지 버전 문자열은 아직 배포판과 같아서 `--force-reinstall`이 필요합니다. SOCKS 프록시를 쓰려면 `korail-mobile-api[socks]`로 설치하세요.

## 빠르게 써보기

간편 API `Korail`은 KST `datetime`을 받고, 처음 검색할 때 역 목록을 받아 입력을 확인합니다.

```python
from datetime import datetime, timedelta, timezone

from korail_mobile_api import Korail

with Korail() as korail:
    result = korail.trains.search(
        "서울", "부산", depart_after=datetime.now(timezone(timedelta(hours=9))) + timedelta(days=1)
    )
    for train in result.trains:
        print(train.train_no, train.departure_time, train.arrival_time)
```

<p align="center">
  <img src="https://raw.githubusercontent.com/yakisoba0728/korail-mobile-api/main/docs/assets/demo.svg" alt="열차 조회 실행 예시" width="100%">
</p>

로그인하면 내 승차권을 볼 수 있습니다. 로그인 ID는 하이픈 없는 회원번호·전화번호나 이메일이며, 실패가 계정 잠금 횟수에 들어갈 수 있으니 반복하지 마세요.

```python
from getpass import getpass

from korail_mobile_api import Korail

with Korail() as korail:
    korail.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    try:
        tickets = korail.tickets.all()
        print(sum(len(r.tickets) for r in tickets.reservations), "장")
    finally:
        korail.logout()
```

`with` 블록은 연결만 닫고 서버 로그아웃은 하지 않습니다. 모든 메서드와 요청 옵션은 `korail.client`(`KorailClient`)에 있습니다. [시작하기](https://yaki.kr/korail-mobile-api/getting-started/)와 [간편 API 가이드](https://yaki.kr/korail-mobile-api/guide/convenience/)를 참고하세요.

## 예약·결제·환불

**아래 메서드는 부르는 순간 실제로 처리됩니다.** 홀드는 좌석을 잡고, 결제는 카드에 청구되며, 환불에는 수수료가 붙을 수 있습니다.

| 하려는 것 | 메서드 | 알아둘 점 |
|---|---|---|
| 홀드(결제 전 예약) 만들기 | `reserve`, `reserve_transfer`, `reserve_merge`, `reserve_airport_bus` | 승객 구성은 조회할 때와 같게 넣습니다. |
| 홀드 취소 | `cancel_unpaid_hold` | 홀드나 `HoldReference`를 받습니다. 결제한 승차권은 환불합니다. |
| 기존 예약 가져오기 | `get_reservation_hold(pnr_no)` | 예약번호(PNR)로 결제용 홀드를 조회만 합니다. |
| 카드 결제 | `pay_with_card` | 홀드의 `received_amount`를 결제합니다. 0원·예약대기 홀드는 요청 전에 거절하고, 카드 거절은 FAIL 응답으로 돌아옵니다. |
| 환불 | `get_refund_fee` → `refund(..., commission=...)` | 승차권 한 장씩입니다. 실제 수수료 조회의 성공 응답과 원표 식별자·동반자 정보가 일치해야 합니다([환불 가이드](https://yaki.kr/korail-mobile-api/guide/payments/#commission)). |
| 할인 재계산 | `PriceRecalculationRequest.for_hold` → `recalculate_price` | 결제는 재계산된 홀드로 합니다. |

변경 요청은 자동으로 다시 보내지 않습니다. 예외의 `request_sent`가 `True`이면 서버에서 이미 처리됐을 수 있으니,
다시 보내기 전에 예약은 `list_reservations()`, 결제·환불은 `list_tickets()`로 확인하세요.
예약 응답을 읽지 못한 홀드는 [`HoldReference.from_raw`로 취소](https://yaki.kr/korail-mobile-api/guide/errors/#unparsed-hold)할 수 있습니다.

## 지원 범위

**메서드 제공, 오프라인 테스트 통과, 실서버 성공은 서로 다른 확인 범위입니다.** 영역별 최근 실서버 기록은 [실서버 확인 현황](https://yaki.kr/korail-mobile-api/status/)에 있습니다.

| 지원 | 지원하지 않음 |
|---|---|
| 로그인, 열차 조회(직통·환승), 호차·좌석 조회, 운임 조회 | 간편 로그인(카카오·네이버 등) |
| 예약(일반·좌석 지정·예약대기·환승·병합), 홀드 취소 | 여행상품 검색·예약·결제 |
| 카드 결제, 할인 재계산, 환불 | 부가서비스 구매·결제·환불 |
| 승차권·예약 내역, 영수증, 마일리지, 쿠폰, 지연확인증 | 정기권·패스 구매 |
| 정기권·패스 조회, N카드, 여행상품 예약 조회·취소, 공항버스, 대리수령 조회·회수, 셀프 체크인 | 다른 회원에게 승차권 전달, 승차권 변경 |

N카드 일부 기능, 셀프 체크인 좌석 확인·등록·취소, 역에서 산 승차권 환불, 전달 승차권 회수는 메서드가 있지만 정상 흐름을 실서버에서 확인하지 못했습니다.

## 자주 묻는 질문

**모든 요청이 `-8204`로 실패해요.** 2026-10-21부터 보고된 앱 업데이트 안내 응답입니다([#32](https://github.com/yakisoba0728/korail-mobile-api/issues/32)). 네트워크 차단(`-8202` 등)과 다르며,
로그인을 포함한 모든 경로에서 `KorailAppUpdateRequiredError`로 분류하고 서버 메시지를 남깁니다. 위 현재 상태를 참고하세요.

**클라우드 서버에서는 로그인이 막혀요.** KORAIL은 데이터센터·VPN IP 대역의 요청을 막습니다. `KorailDynaPathError`(HTTP 403, `-8202` 등)가 나면
요청 형식이 아니라 네트워크 문제일 가능성이 큽니다. `KorailConfig(proxy="socks5://...")`로 KORAIL 요청만 본인이 관리하는 다른 네트워크로 보낼 수 있습니다([프록시](https://yaki.kr/korail-mobile-api/guide/configuration/#proxy)).

**비밀번호나 카드 번호는 어디에 저장되나요?** 어디에도 저장하지 않고 KORAIL 서버로만 보냅니다. 다만 응답 모델과 예외의 `.raw`에는 개인정보가 그대로 있습니다.
`repr()`이 비밀값을 숨기는 것은 출력뿐이며 속성·`.raw`·`dataclasses.asdict`·pickle은 가리지 않으니 로그에 그대로 남기지 마세요.

**SRT는요?** 2026년 9월 통합으로 KTX에 합쳐져 예매는 코레일+ 앱 하나로 합니다. SRT 앱용이던 [srt-mobile-api](https://github.com/yakisoba0728/srt-mobile-api)의 개발과 기록은 이 저장소에서 이어갑니다.

## 문서와 참여

- [문서 사이트](https://yaki.kr/korail-mobile-api/) — 시작하기, 가이드, 메서드 83개의 API 레퍼런스, [요청 흐름](https://yaki.kr/korail-mobile-api/concepts/how-it-works/)
- [변경 이력](https://github.com/yakisoba0728/korail-mobile-api/blob/main/CHANGELOG.md) · [3.0으로 옮기기](https://yaki.kr/korail-mobile-api/migration-3.0/) · [배포 절차](https://yaki.kr/korail-mobile-api/releasing/)
- [동작 규칙 (checks/BEHAVIOR.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/BEHAVIOR.md) · [오프라인 검사 기준 (checks/ACCEPTANCE.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/ACCEPTANCE.md) · [에이전트 작업 가이드 (AGENTS.md)](https://github.com/yakisoba0728/korail-mobile-api/blob/main/AGENTS.md)
- 한국철도공사 <https://www.korail.com> · 코레일+ 앱 [Google Play](https://play.google.com/store/apps/details?id=com.korail.talk) · [App Store](https://apps.apple.com/kr/app/id1000558562)

누구나 이슈와 Pull Request로 참여해 이 저장소를 중심으로 함께 개선하는 방식을 지향합니다. 버그나 앱 업데이트로 달라진 부분을 찾으면 이슈로 알려 주세요.
기여를 위한 포크를 환영하며 코드의 이용·수정·재배포에는 [Apache License 2.0](https://github.com/yakisoba0728/korail-mobile-api/blob/main/LICENSE)이 그대로 적용됩니다.
다만 저작자의 사전 승인 없이 포크나 다른 저장소를 이 프로젝트의 공식 운영본·공식 후속 프로젝트로 표방하거나, 공식 승인·제휴가 있는 것처럼 안내하는 행위를 금합니다.

## 개발

개발 환경과 전체 검사 명령은 [배포 절차의 로컬 검증](https://yaki.kr/korail-mobile-api/releasing/#로컬-검증)에 있습니다. 에이전트로 작업한다면 먼저 [AGENTS.md](https://github.com/yakisoba0728/korail-mobile-api/blob/main/AGENTS.md)를 읽어 주세요.
테스트는 합성 응답과 소켓 차단으로 실행하며 실서버 수용을 증명하지 않습니다. README의 사용 예제는 테스트 밖에서 실행하면 실제 서버에 접속합니다.

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
