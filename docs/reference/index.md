# 타입 레퍼런스

메서드의 입력과 반환값으로 쓰이는 공개 타입입니다. 모두 `korail_mobile_api`에서 바로 가져올 수 있습니다.

```python
from korail_mobile_api import TrainSearchQuery, KorailPassengerCounts
```

응답 모델은 모두 고정된(frozen) dataclass입니다. 서버가 보낸 원본은 `raw` 필드에 그대로 남습니다.

| 페이지 | 내용 |
|---|---|
| [열차·공통 모델](models.md) | 열차 조회, 좌석, 역·달력 같은 공통 응답과 조회 입력입니다. |
| [계정 조회 모델](read-models.md) | 승차권·예약 내역·계정 정보 조회의 응답 모델입니다. |
| [조회 입력](requests.md) | 계정 조회 메서드에 넘기는 입력 타입입니다. |
| [예약·결제 모델](mutation-models.md) | 예약·결제·환불 메서드의 입력과 응답 모델입니다. |
| [공항버스 모델](limousine-models.md) | 공항버스(리무진) 조회 입력과 응답 모델입니다. |
| [예외](errors.md) | 라이브러리가 발생시키는 예외입니다. 모두 `KorailApiError`를 상속합니다. |
| [상수](constants.md) | 객실 등급, 예약 작업 종류 같은 열거형과 입력 타입 별칭입니다. |
| [설정](config.md) | 클라이언트 설정과 DynaPath 토큰 설정입니다. |
