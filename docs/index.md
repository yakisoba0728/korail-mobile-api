# korail-mobile-api

KORAIL(한국철도공사) 안드로이드 앱이 쓰는 API 를 파이썬에서 그대로 호출하는
클라이언트다. 로그인하고, 열차를 검색하고, 내 승차권과 예약을 읽는다. 좌석을
잡거나 취소·결제·환불하는 것은 명시적인 consent 객체 뒤에서만 일어난다. 보내는
경로와 폼 필드는 앱이 보내는 것과 같다.

!!! warning "읽기 전에"

    - **문서가 아니라 리버스 엔지니어링의 결과다.** 라우트·필드명·상태코드는
      `com.korail.talk` 6.5.0 APK 를 디컴파일해 읽어낸 것이고, 가능한 범위에서만
      실서버로 확인했다. KORAIL 은 규격을 공개하지 않고 안정성도 약속하지 않는다.
    - **실서비스에 붙는다.** `smart.letskorail.com` 은 실제 발권 시스템이다. 이
      라이브러리가 만든 예약은 누군가 취소해야 하는 진짜 예약이고, 결제는 진짜 돈이다.
    - **KORAIL 과 제휴·후원·지원 관계가 없다.** 본인 계정을 쓰고, 결과는 본인이
      감당하라. 무보증이다.

## 이 사이트의 구성

| 페이지 | 무엇이 있나 |
| --- | --- |
| [빠른 시작](quickstart.md) | 설치, 로그인·검색·조회까지의 최소 코드, 기본 설정이 실제로 보내는 것 |
| [안전 모델](safety.md) | consent 객체, 범주별 플래그, `dry_run`, 실카드 결제에만 붙는 승인 |
| [API 레퍼런스](reference/index.md) | `korail_mobile_api` 가 export 하는 이름 전부. docstring 에서 생성한다 |
| [에러](errors.md) | 예외 계층, `h_msg_cd` 분류표, 안티 매크로 거부를 버전 문제와 구별하는 법 |
| [변경 이력](changelog.md) | CHANGELOG 그대로 |

APK 근거 기록·라우트 인벤토리·감사 기록은 사이트에 올리지 않는다. 저장소의
[README](https://github.com/yakisoba0728/korail-mobile-api#문서) 가 문서별 표로
안내한다.

## 설치

{%
  include-markdown "../README.md"
  start="## 설치"
  end="## 빠른 시작"
  heading-offset=-1
%}
