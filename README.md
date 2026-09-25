> [!IMPORTANT]
> ## 🚆 The Journey Begins Again
>
> ### **여기서, 여정이 다시 시작됩니다.**
>
> 2026년 9월 1일, KORAIL과 SR의 통합과 함께 KTX와 SRT 역시 하나의 체계로 합쳐졌습니다.
> 두 갈래로 이어져 오던 서비스가 하나의 선로 위에서 만난 것처럼,
> **[`srt-mobile-api`](https://github.com/yakisoba0728/srt-mobile-api)의 개발과 기록도
> 이제 `korail-mobile-api`로 이어집니다.**
>
> `srt-mobile-api`는 여기서 멈췄지만, 그 안에서 확인한 수많은 요청과 응답,
> 시행착오와 검증의 기록까지 사라지는 것은 아닙니다.
> 그 경험은 이 프로젝트의 다음 장을 이루는 기반으로 남습니다.
>
> **우리는 SRT를 기억할 것입니다.**  
> 하나의 프로젝트는 종착역에 도착했지만, 그 여정은 이곳에서 다시 출발합니다.
>
> **One journey ended. Another begins here.**
>
> → [`srt-mobile-api` — Final Stop](https://github.com/yakisoba0728/srt-mobile-api)

# korail-mobile-api

KORAIL 안드로이드 앱 7.0.6의 요청·응답 구조를 바탕으로 만든 동기식 Python 클라이언트입니다. **비공식 프로젝트이며 KORAIL 및 SR과 관계가 없고, 공식 지원·승인·서비스를 제공하지 않습니다.**

자기 계정으로만 사용하고 KORAIL의 서비스 이용약관과 이용 제한을 준수하십시오. 예약은 실제 좌석을 점유하고, 결제는 실제 카드 청구를 발생시키며, 취소·환불에는 수수료가 발생할 수 있습니다. **계정·카드 사용, 실예약·실결제 및 환불 결과 확인의 책임은 사용자에게 있습니다.** 자동화의 허용 여부와 제3자 코드·상표의 권리는 이 프로젝트의 라이선스만으로 보장되지 않습니다.

## 설치

Python **3.11 이상**이 필요합니다. 배포 이름은 `korail-mobile-api`, import 이름은 `korail_mobile_api`입니다. PyPI에 게시된 뒤에는 다음과 같이 설치합니다.

```sh
python -m pip install korail-mobile-api
```

게시 전에는 저장소 루트에서 `python -m pip install .` 또는 빌드한 wheel을 설치하십시오. 실행 의존성은 `httpx>=0.24.1`, `cryptography>=42.0.8`이며 상한은 두지 않습니다. 하한은 Python 3.11에서 전체 오프라인 테스트가 통과한 정확한 버전이고, CI의 minimum 작업이 같은 버전을 설치해 다시 확인합니다.

## 빠른 시작

아래 단계는 같은 Python 세션에서 순서대로 실행하는 예입니다. **조회 단계까지만 실행하면 결제하지 않습니다.** 예약·결제·환불 단계는 각각 설명을 읽고 필요한 작업만 실행하십시오. 예시에는 실제 회원번호·카드번호·승차권 식별자가 없습니다. 객체 전체나 `raw`를 출력하면 개인정보가 노출될 수 있습니다.

### 1. 로그인하고 열차 조회

```python
from getpass import getpass

from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
query = TrainSearchQuery(
    departure_station_code=input("출발역 이름: "),
    arrival_station_code=input("도착역 이름: "),
    departure_date=input("출발일 YYYYMMDD: "),
    departure_time=input("출발시각 HHMMSS: "),
    passengers=1,
)
search = client.search_trains(query)
for index, train in enumerate(search.trains):
    print(index, train.train_no, train.departure_time, train.arrival_time)
```

로그인 ID는 숫자만 쓴 회원번호·전화번호(하이픈 없이 11자리) 또는 이메일입니다. `input_flag`를 생략하면 `010-1234-5678`처럼 숫자만도 이메일도 아닌 입력은 앱처럼 보내지 않고 `KorailProtocolError`로 거절합니다. 실패한 로그인은 계정 잠금 횟수에 들어갈 수 있습니다.

청소년·유아·안내견은 `teenager_passengers`·`infant_passengers`·`guide_dog_passengers`로 넣으면 앱처럼 어른·어린이 칸에 합쳐 조회합니다. 예약할 `KorailPassengerCounts`와 같은 구성으로 조회하십시오.

`departure_station_code`와 `arrival_station_code`에는 역 이름도 넣을 수 있습니다. 숫자 역 코드를 넣으면 역 데이터를 조회해 이름으로 변환합니다. 날짜와 시간은 각각 `YYYYMMDD`, `HHMMSS` 형식입니다. 한 번의 조회가 모든 페이지나 모든 열차를 반환한다는 보장은 없습니다.

### 2. 실제 좌석 예약

```python
selected = search.trains[int(input("예약할 열차의 목록 번호: "))]
hold = client.reserve(selected)
print("예약 결과:", hold.str_result, hold.h_msg_cd)
```

`reserve`는 단순 가격 조회가 아니라 결제 전 예약을 만듭니다. 조회와 예약의 승객 구성은 일치시켜야 합니다. 이 예시는 기본 성인 1명입니다. 예약대기 응답은 일반 좌석 확보와 같지 않으므로 응답과 결제기한을 확인하고 필요한 경우 별도의 `confirm_standby_hold` 흐름을 사용하십시오. 예약대기 홀드는 앱처럼 결제하지 않으며 `hold.payable`이 `False`이고 `pay_with_card`가 전송 전에 거절합니다. 결제하지 않을 홀드는 `client.cancel_unpaid_hold(hold)`로 취소할 수 있습니다. 결제한 승차권에는 이 취소 대신 환불을 사용합니다.

### 3. 카드 결제 — 실제 청구

**다음 호출은 테스트가 아닙니다. 실제 카드 청구와 발권이 발생합니다.** 예약 내용과 금액을 확인한 후 실행하십시오. 카드정보를 코드·파일·로그에 하드코딩하지 마십시오.

```python
from korail_mobile_api import CardPayment

card = CardPayment(
    card_number=getpass("카드번호: "),
    card_password=getpass("카드 비밀번호 앞 두 자리: "),
    card_expire=getpass("카드 유효기간 YYMM: "),
    birthday=getpass("개인 생년월일 YYMMDD: "),
)
payment = client.pay_with_card(hold, card)
print("결제 결과:", payment.str_result, payment.h_msg_cd)
if payment.str_result != "SUCC":
    raise RuntimeError("결제 성공을 확인하지 못했습니다. 재결제 전에 승차권 목록과 카드 내역을 확인하십시오.")
```

**카드 거절은 예외가 아니라 `str_result="FAIL"`인 `ReservationPaymentResponse`로 돌아올 수 있습니다.** 예외가 없었다는 이유만으로 성공이라고 판단하지 마십시오. 성공 응답의 `reservation_no`가 비어 있을 수 있으므로 `hold.pnr_no`와 승차권 목록으로 발권 결과를 확인합니다. 전송 오류·파싱 오류가 나도 서버에서는 결제됐을 수 있으므로 같은 결제를 자동 재시도하지 마십시오.

### 4. 환불 수수료 확인 후 승차권 한 장 환불

환불은 **PNR 전체가 아니라 승차권 한 장 단위**이며 실제 환불·수수료가 발생합니다. 아래 예시는 방금 예약한 PNR의 현재 승차권을 목록에서 찾아 사용자가 한 장을 선택합니다. 목록이 비어 있거나 신원이 불완전하면 임의로 식별자를 만들지 말고 공식 앱에서 확인하십시오.

```python
from korail_mobile_api import OriginalTicketReference, PaidTicket

listing = client.get_ticket_list()
tickets = [
    ticket
    for reservation in listing.reservations
    for ticket in reservation.tickets
    if ticket.pnr_no == hold.pnr_no
]
for index, ticket in enumerate(tickets):
    print(
        index,
        ticket.ticket_status_name,
        [(leg.train_no, leg.departure_date, leg.departure_time) for leg in ticket.trains],
    )
target = tickets[int(input("환불할 승차권의 목록 번호: "))]

# 수수료·상세 조회에는 목록의 return_sale_date(MMDD)를 사용합니다.
reference = OriginalTicketReference(
    sale_window_no=target.sale_window_no,
    sale_date=target.return_sale_date,
    sale_sequence=target.sale_sequence,
    return_password=target.return_password,
)
detail = client.get_refund_ticket_detail(reference)
commission = client.get_refund_commission(reference)
print("수수료 조회 결과:", commission.str_result, commission.h_msg_cd)
print("예상 환불액 / 수수료:", commission.refund_amount, commission.refund_fee)
# commission의 금액 필드를 확인한 뒤 다음 줄을 따로 실행하십시오.
paid_ticket = PaidTicket.from_refund_detail(detail)
refunded = client.refund(
    paid_ticket,
    commission=commission,
    pbp_acceptance_target_flag=target.pbp_acceptance_target_flag,
)
print("환불 결과:", refunded.str_result, refunded.h_msg_cd)
```

목록 식별자는 선택 필드이므로 `None`이면 `OriginalTicketReference`가 입력을 거절합니다. 애플리케이션에서는 값이 모두 있는지 먼저 확인하고 사용자에게 안내하십시오. 동반자 할인 등은 해당 `RefundCompanion`도 수수료 조회에 전달해야 하며, 위 예시는 그런 할인이 없는 기본 승차권입니다. 수수료 조회의 `return_sale_date`와 실제 환불에 쓰는 상세의 `sale_date`를 혼용하지 마십시오. `PaidTicket.from_refund_detail`은 환불 신원을 상세 응답에서 구성합니다. 여러 장은 각 장의 수수료·환불 결과·남은 목록을 따로 확인합니다.

작업을 마치면 `client.close()`를 호출하십시오. 실제 프로그램에서는 `try/finally`의 `finally`에 **`close()`만** 두고, 결제·환불 같은 상태 변경을 자동 정리 작업으로 넣지 마십시오. 이 클라이언트는 컨텍스트 매니저를 제공하지 않습니다.

## 예외 처리와 결과 확인

```python
from korail_mobile_api import (
    KorailApiError,
    KorailAuthError,
    KorailNoResultsError,
    KorailProtocolError,
    KorailSessionExpiredError,
    KorailTransportError,
)

try:
    result = client.search_trains(query)
except KorailSessionExpiredError:
    print("세션이 만료됐습니다. 다시 로그인하십시오.")
except KorailAuthError:
    print("로그인 상태나 추가 인증 절차를 확인하십시오.")
except KorailNoResultsError:
    print("조회 결과가 없습니다.")
except (KorailTransportError, KorailProtocolError):
    print("통신·응답 처리 실패 또는 입력 오류입니다. 상태 변경 작업은 결과 확인 없이 재시도하지 마십시오.")
except KorailApiError as error:
    print("KORAIL 처리 실패 코드:", error.code)
```

`KorailApiError` 계층의 `code`, `message`, `raw`, `parser_raw`는 제공되지 않으면 `None`입니다. `raw`는 원문이며 마스킹되지 않습니다. 전송 전 입력 검증(잘못된 카드 입력, 좌석 중복, 결제할 수 없는 홀드, 닫힌 클라이언트 등)도 대부분 `KorailProtocolError`입니다. 이 예외나 `raw` 유무만으로는 요청이 서버에 닿았는지 알 수 없으므로 상태 변경 뒤에는 예약·승차권 목록으로 먼저 확인하십시오. 설정 객체 생성 같은 일부 검증은 `ValueError`·`TypeError`를 낼 수 있어 모든 Python 오류가 이 계층에 포함되지는 않습니다. 일부 메서드는 실패 봉투도 타입화된 응답으로 반환하므로 메서드별 반환 계약을 함께 확인하십시오. 특히 결제는 위의 `str_result` 확인이 필수입니다.

## DynaPath와 NetFunnel

API 요청은 7.0.6 앱처럼 `User-Agent: korailtalk`로 보냅니다. 대기열 요청은 앱의 대기열 SDK처럼 안드로이드 기본 User-Agent(`Dalvik/2.1.0 (Linux; U; Android 17; SM-S948N Build/CP2A.260605.016)`)를 붙인 빈 본문 POST로 보냅니다. 각각 `KorailConfig.user_agent`, `netfunnel_user_agent`로 바꿀 수 있습니다. 기기를 바꿀 때는 `constants.build_dalvik_user_agent`로 만든 값과 DynaPath 기기값을 같은 기기로 맞추십시오.

DynaPath 요청 헤더는 기본 활성화되고 기기 값은 합성됩니다. 실제 기기를 사용했다는 보장이나 서버 수용 보장이 아닙니다. 설정은 `KorailConfig`와 `DynapathConfig`로 지정합니다. `KorailConfig(disable_dynapath=True)`는 명시적으로 끄는 옵션이지만, DynaPath가 필요한 경로는 토큰 없이 호출할 수 없으며 전송 전에 거절될 수 있습니다. 차단 응답은 `KorailDynaPathError`로 확인합니다. 토큰·기기 식별자·로그인 정보를 공개 이슈에 올리지 마십시오.

NetFunnel은 대기열 프로토콜입니다. 관련 조회·예약·결제 메서드는 관문 진입(5101), 필요 시 대기(5002), 작업 후 반납(5004)을 처리합니다. 대기 중에는 호출이 오래 걸릴 수 있으며 `netfunnel_wait_limit`으로 누적 대기 상한을 설정할 수 있습니다. 기본값 `None`은 상한 없음입니다. 서버의 대기 지시와 실패를 존중하십시오. 일부 앱 `aid`·`mode` 상수는 보호돼 있어 현재 매핑의 완전한 정적 일치를 확인하지 못했습니다. 오프라인 테스트 통과는 대기열 우회나 모든 실서버 동작의 보장이 아닙니다.

```python
from korail_mobile_api import KorailConfig

config = KorailConfig(netfunnel_wait_limit=120.0)
# 이후 새 클라이언트를 만들 때 KorailClient(config)를 사용합니다.
```

`base_url`·`netfunnel_url`을 변경하면 로그인 정보·요청이 그 주소로 향할 수 있습니다. 신뢰하지 않는 주소나 설정을 사용하지 마십시오.

## 공개 API와 버전 정책

**SemVer(major.minor.patch)**를 따릅니다. 버전의 단일 원본은 `korail_mobile_api.__version__`이며 wheel·sdist 메타데이터는 이 값을 읽습니다. v1.0.0~v1.1.1은 GitHub 릴리스로만 공개했고 PyPI에는 아직 올리지 않았습니다. 현재 소스는 v1.1.1과 호환되지 않는 변경을 포함하므로([변경 이력](https://github.com/yakisoba0728/korail-mobile-api/blob/main/CHANGELOG.md)) SemVer로는 major 변경에 해당합니다. 첫 PyPI 버전 번호는 배포 때 정하며, 이 문서가 업로드 완료를 뜻하지는 않습니다.

호환성 약속은 최상위 `__all__`의 클라이언트·설정·요청/응답 모델·열거형·예외·타입 별칭, `KorailClient`의 공개 메서드 서명과 명시된 의미, 공개 모델의 필드·생성자, 문서화된 예외 종류와 `code`·`raw` 보존 계약입니다. 이름 제거, 호환되지 않는 서명·반환 타입 변경, 지원 Python 하한 상향은 major 변경으로 다룹니다. 호환되는 기능 추가는 minor, 기존 계약의 오류 수정은 patch입니다. 모델 필드 추가도 기존 위치 인자 호출을 깨지 않는 경우에만 minor로 다룹니다.

내부 모듈·밑줄 이름, 낮은 수준의 파서/빌더/전송·세션 매니저·대기열 실행기, 공개 목록에서 제외한 상수·헬퍼는 호환성 약속 대상이 아닙니다. `__version__`은 조회용으로 유지합니다. `raw`에 원문을 남긴다는 계약은 유지하지만, 서버 원문의 개별 키·값·문구, 보호된 상수의 서버 수용 여부와 KORAIL 서비스의 지속성은 보장하지 않습니다. 서버 변경 대응이 공개 계약을 깨뜨려야 하면 이를 변경 이력에 명시하고 위 버전 규칙을 적용합니다.

## 개발과 오프라인 검증

```sh
python -m pip install -e '.[dev]'
python -m ruff check src checks tests
python -m ruff format --check src checks tests
python -m mypy
python -m pyright
python -m pytest tests/
python -m build
python -m twine check dist/*
```

`pytest`는 테스트 전체의 소켓 연결을 차단하고 `httpx.MockTransport`로만 응답합니다. 기존 `checks/contract_api.py`(G9/G10/G11)와 `checks/netfunnel_offline.py`도 pytest에서 실행합니다. 패키징 테스트는 네트워크 없는 자식 프로세스에서 선택한 PEP 517 백엔드로 sdist와 wheel을 실제 빌드하며, CI는 별도로 표준 `python -m build`와 `twine check`를 실행합니다. **실서버 수용 테스트가 아닙니다.**

[검사 안내](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/README.md) · [수용 기준](https://github.com/yakisoba0728/korail-mobile-api/blob/main/checks/ACCEPTANCE.md) · [변경 이력](https://github.com/yakisoba0728/korail-mobile-api/blob/main/CHANGELOG.md) · [라이선스](https://github.com/yakisoba0728/korail-mobile-api/blob/main/LICENSE)

wheel에는 실행 패키지와 `py.typed`, 메타데이터·LICENSE만 포함합니다. sdist에는 재현 가능한 오프라인 검사를 위해 `checks/`와 `tests/`도 포함합니다. `analysis/`, APK, 자격증명 파일은 배포 대상이 아닙니다. 아래 두 기록용 모듈은 소스 보존을 위해 wheel과 sdist에 남기지만 정상 import 경로 및 공개 API에는 연결하지 않습니다. 이 파일의 존재는 기능 지원을 뜻하지 않습니다.

## 직접 지원하지 않는 기능

### 부가서비스(MaaS) 구매·결제·환불

렌터카·카셰어링·짐배송·레저이용권·관광택시·주차 같은 부가서비스는 KORAIL 앱의 자체 기능이 아니라 제휴사 서비스입니다.

- **예약은 제휴사 사이트에서만 됩니다.** 앱 메뉴의 중계 페이지(`/ebizmaas/EbizMaasShopView.do`)가 요청번호를 발급하고, 암호화된 본인 정보를 제휴사 사이트(야놀자, 짐캐리, 로이쿠, SK·롯데 렌터카, 그린카, KN파킹)로 넘깁니다. 제휴사에서 상품을 고르면 그때 KORAIL 장바구니에 결제 전 항목이 생깁니다. KORAIL API로는 이 항목을 만들 수 없습니다.
- **결제와 환불은 폼 값을 알 수 없습니다.** 부가서비스 결제(`pay.intgStl.do`)와 환불(`addService.coptCnc.do`)에 들어가는 상수가 앱에서 보호돼 있습니다.

그래서 부가서비스는 조회만 지원합니다: `get_maas_menu_list`, `get_maas_station_data`, `get_maas_service_details`, `get_cart_list`.

앱 코드와 같게 만들어 두었지만 실서버에서 확인하지 못한 세 호출(환불 수수료 `maas.cncFee.do`, 결제 전 상태 확인 `maas.rsvStt.do`, 결제 전 해제 `addService.cancelPay.do`)은 공개 API에서 빼고 기록용으로 `src/korail_mobile_api/_maas_unsupported.py`에 남겨 두었습니다. 이 모듈은 어디에서도 쓰지 않습니다.

공항버스는 KORAIL 자체 예약이라 조회·예약·결제·환불·취소를 모두 지원합니다(`reserve_limousine`).

### 여행상품 예약·결제·환불

지역 여행상품·테마열차 같은 KORAIL 여행상품은 KORAIL 웹(`/ebizmk/prd/rvStep1.do` → `rvStep2.do` → `reservation.do`)에서만 예약할 수 있고, 앱에는 예약을 만드는 API가 없습니다. 웹의 결제 버튼은 앱으로 넘기는 링크(`korailtalk://payment`)이고, 앱은 통합결제(`pay.intgStl.do`)로 결제하는데 그 폼의 `stlPrsJobId`가 앱에서 보호돼 있습니다.

그래서 라이브러리는 이미 만들어진 여행상품 예약의 조회(`get_product_reservations`, `get_product_detail`)와 취소(`cancel_product_reservation`)만 지원합니다. 2026-09-24에 웹에서 만든 결제 전 예약으로 조회와 취소(수수료 0원)를 확인했습니다. 결제된 여행상품의 환불은 결제를 할 수 없어 확인하지 못했습니다.

### 간편(소셜) 로그인

앱의 카카오·네이버·구글 로그인은 각 제공자 SDK로 먼저 인증한 뒤, 그 결과로 받은 고객 식별값을 KORAIL 로그인에 보냅니다. 제공자 인증은 기기와 앱에 묶인 외부 SDK 흐름이라 라이브러리가 대신할 수 없고, 함께 보내는 `checkValidPw` 값도 앱에서 보호돼 있습니다. 소셜 계정으로 실서버에서 확인한 적도 없어서, `login_social`은 공개 API에서 빼고 기록용으로 `src/korail_mobile_api/_social_login_unsupported.py`에 남겨 두었습니다. 로그인은 회원번호·전화번호·이메일과 비밀번호(`login`)로 합니다.

## 지원하지만 검증하지 못한 기능

### N카드(할인카드)

N카드 관련 기능은 앱 코드와 같게 만들어 두었지만, N카드가 없는 계정이라 **모두 검증 못 함**입니다. 코드에서도 해당 메서드·요청 빌더·파서·모델 설명에 "검증 못 함"을 달아 두었습니다.

| 메서드 | 역할 | 검증 못 한 이유 |
|---|---|---|
| `get_discount_card_usage_history` | N카드 사용 내역 | N카드 없음(서버는 `ERR000100` 조회 자료 없음) |
| `get_discount_card_schedule` | N카드로 탈 수 있는 열차 | N카드 없음(서버는 `WRR000100` 입력값 오류) |
| `get_delivery_recipient` | N카드 2인 승차권의 수령자 후보 | N카드 승차권 없음(서버는 `IRZ000005` 조회 자료 없음) |
| `register_discount_card` | N카드 구매(결제 전 생성) | 실제 구매로 이어져 시도하지 않음 |
| `extend_discount_card` | N카드 기간 연장 | N카드 없음 |
| `reserve_with_discount_card` | N카드로 좌석 홀드 | N카드 없음 |

N카드 결제는 여행상품과 같은 통합결제(`pay.intgStl.do`)라 역시 보호 상수 `stlPrsJobId`에 막혀 있습니다.
