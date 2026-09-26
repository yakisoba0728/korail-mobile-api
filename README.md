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

KORAIL 안드로이드 앱 7.0.6의 요청을 재현하는 **비공식 동기식 Python 클라이언트**입니다.
KORAIL·SR의 공식 지원이나 승인을 받지 않았습니다. 자기 계정으로 이용약관과 이용 제한을 준수해 사용하십시오.

## 설치

Python 3.11 이상과 `httpx>=0.24.1`, `cryptography>=42.0.8`가 필요합니다.
PyPI 배포 없이 저장소에서 설치합니다.

```sh
python -m pip install "git+https://github.com/yakisoba0728/korail-mobile-api"
# 내려받은 저장소에서는:
python -m pip install .
```

## 로그인과 조회

```python
from getpass import getpass
from korail_mobile_api import KorailClient, TrainSearchQuery

client = KorailClient()
try:
    client.login(input("회원번호·전화번호·이메일: "), getpass("비밀번호: "))
    result = client.search_trains(TrainSearchQuery(
        departure_station_code=input("출발역 이름: "),
        arrival_station_code=input("도착역 이름: "),
        departure_date=input("출발일 YYYYMMDD: "),
        departure_time=input("출발시각 HHMMSS: "),
        passengers=1,
    ))
    for train in result.trains:
        print(train.train_no, train.departure_time, train.arrival_time)
finally:
    client.clear_session()
    client.close()
```

위 예시는 예약·결제를 하지 않습니다. 숫자 역 코드는 역 목록으로 이름을 찾아 전송합니다.
한 번의 조회가 모든 페이지를 반환하는 것은 아닙니다. 로그인 ID는 숫자만 쓴 회원번호·전화번호 또는 이메일입니다.
`close()`는 연결만 닫고, `clear_session()`은 로컬 정보만 폐기하며, `logout()`은 서버 로그아웃도 시도합니다.

## 응답과 변경 요청

응답은 전용 dataclass로 반환합니다. 서버 코드 필드는 미래의 값도 받을 수 있도록 `str`이고,
선택 스칼라가 없으면 `None`입니다. 좌석·역의 18개 기본값 예외는 [동작 계약](checks/BEHAVIOR.md)에 명시합니다.
`raw`는 `Mapping[str, object]`로 노출되지만 실제 원문 객체를 복사하거나 동결하지 않습니다.
모델·예외·`repr`·`raw`의 개인정보와 카드정보는 자동 마스킹하지 않습니다.

**예약·결제·환불 메서드는 호출 즉시 실제 상태를 변경합니다.** 사전 동의 인자나 미리보기 단계는 없습니다.
예약은 좌석을 점유하고, 결제는 실제 청구를 만들며, 환불에는 수수료가 발생할 수 있습니다.

| 작업 | 호출과 주의사항 |
|---|---|
| 미결제 예약 | `reserve`, `reserve_transfer`, `reserve_merge`, `reserve_limousine`; 승객 구성은 조회와 일치시킵니다. |
| 예약 취소 | `cancel_unpaid_hold`; 기본은 가능 여부 확인 후 취소입니다. 결제된 표에는 사용하지 않습니다. |
| 결제 | `pay_with_card`; 카드 거절은 예외가 아닌 FAIL 모델입니다. 대기 홀드·0원 홀드는 카드 결제를 거절합니다. |
| 환불 | 먼저 `get_refund_commission`, 다음 `refund(..., commission=...)`; PNR 전체가 아닌 승차권 한 장씩입니다. |
| 할인 재계산 | `PriceRecalculationRequest.for_hold`로 좌석별 입력을 만들고 `recalculate_price`; 선택적 장바구니 추가 결과도 확인합니다. |

변경 요청은 자동 재전송하지 않습니다. 전송 오류나 응답 파싱 오류만으로 실패했다고 판단하지 말고
예약·승차권 목록과 결제 결과를 확인하십시오. 예외의 `raw`는 전체 응답, `parser_raw`는 파서가 남긴 부분 원문입니다.
모델의 위치 인자보다 키워드 인자를 권장합니다. 공개 이름과 서명 변경은 [CHANGELOG](CHANGELOG.md)에 있습니다.

## 설정과 한계

DynaPath와 NetFunnel은 기본 활성화입니다. DynaPath 기본 기기 식별자는 합성값이며 서버 수용을 보장하지 않습니다.
실제 기기 설정은 `build_config_from_env()`로 구성할 수 있습니다. 임의의 `base_url`·`netfunnel_url`은
자격증명 유출로 이어질 수 있으므로 신뢰할 수 있는 주소만 사용하십시오.

보호된 리터럴과 앱의 모든 분기를 재현하지는 않습니다. N카드 일부 기능, 셀프 체크인 변경,
전달 승차권 회수 등의 실서버 수용은 검증되지 않았습니다. 미지원 MaaS 변경·소셜 로그인·여행상품 검색은
`_*_unsupported.py` 세 모듈에 기록만 남깁니다. 자세한 차이와 사용 흐름은 [동작 계약](checks/BEHAVIOR.md)을 따릅니다.

## 개발 검사

개발 도구를 설치한 뒤 저장소 루트에서 실행합니다. 테스트와 두 검사기는 합성 응답을 사용합니다.

```sh
python -m pip install -e '.[dev]'
ruff check src checks tests
ruff format --check src checks tests
mypy
pyright
pytest tests/
python checks/contract_api.py
python checks/netfunnel_offline.py
```

검사 통과는 운영 서버 수용의 증거가 아닙니다. 검사기의 종료 코드는 [checks/README.md](checks/README.md)를 참조하십시오.
버전은 `src/korail_mobile_api/__init__.py`의 `__version__` 한 곳에서 관리합니다.
라이선스는 [Apache-2.0](LICENSE)이며 제3자 서비스·상표·코드에 대한 권리를 부여하지 않습니다.
