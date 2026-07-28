# API 레퍼런스

`korail_mobile_api` 의 `__all__` 이 내보내는 이름이 공개면이다. 아래 쪽들은 그
이름을 정의한 모듈별로 나뉘어 있고, 내용은 소스의 docstring 을 그대로 렌더링한
것이다 — 이 사이트가 따로 관리하는 설명은 없다.

모듈 쪽은 모듈을 통째로 싣는다. 그래서 `__all__` 에 없는 모듈 상수(예:
`constants` 의 `DYNAPATH_ALLOWLIST_PATHS`)도 여기서 볼 수 있다. 최상위에서
`from korail_mobile_api import ...` 로 꺼낼 수 있는 것만이 안정된 이름이고,
나머지는 모듈 경로로 가져다 쓰는 만큼 바뀔 수 있다.

| 모듈 | 무엇이 들어 있나 |
| --- | --- |
| [client](client.md) | `KorailClient`. 로그인·읽기·변경 메서드 전부 |
| [config](config.md) | `KorailConfig`, `build_config_from_env` — 기기 신원과 기본값 |
| [consent](consent.md) | `MutationConsent`, `MutationCategory`, `require_mutation_consent` |
| [constants](constants.md) | 호스트, 앱 버전, DynaPath 허용목록 같은 고정값 |
| [dynapath](dynapath.md) | `DynapathConfig` 와 토큰 설정 |
| [errors](errors.md) | 예외 계층과 `classify_app_error` |
| [limousine_models](limousine_models.md) | 리무진 연계 편의 응답 타입 |
| [live](live.md) | 라이브 테스트가 쓰는 진입점 |
| [models](models.md) | 로그인·검색·예약의 요청/응답 타입 |
| [mutation_models](mutation_models.md) | `MutationPreview` 와 변경 결과 타입 |
| [netfunnel](netfunnel.md) | 가상대기실 상태와 설정 |
| [read_models](read_models.md) | 읽기 라우트의 응답 타입 — 가장 큰 묶음이다 |
| [read_payloads](read_payloads.md) | 읽기 요청을 만드는 payload 타입 |

docstring 이 없는 dataclass 도 필드를 보여 주려고 함께 싣는다. 설명이 붙어 있지
않다는 것은 그 타입이 서버 응답을 그대로 담는 그릇이라는 뜻이다.
