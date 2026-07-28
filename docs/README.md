# docs/

이 디렉터리에는 성격이 다른 두 묶음이 있습니다.

- **`docs/` 바로 아래 문서**는 패키지를 설명합니다. 클라이언트가 무엇을 보내고, 서버가
  무엇을 답하며, 어디까지 라이브 서비스로 확인됐는지를 다룹니다.
- **`docs/internal/`** 은 개발 기록입니다. 감사, 재검증 기록, 설계 명세, 구현 계획이
  들어 있고 패키지 사용에는 필요하지 않습니다.

`index.md`·`quickstart.md`·`safety.md`·`errors.md`·`changelog.md`·`reference/` 는 문서
사이트의 원본입니다. 최상위 `mkdocs.yml` 이 이 여섯만 사이트로 올립니다. 산문은 README 와
CHANGELOG 의 절을 그대로 끌어다 쓰고(`include-markdown`), `reference/` 는 모듈마다 한
줄씩 mkdocstrings 지시자만 두어 docstring 에서 생성합니다. 사이트를 보려면
`pip install -e ".[docs]"` 뒤에 `mkdocs serve` 하면 됩니다.

최상위 README 의 [문서](../README.md#문서) 표에는 자주 찾는 것만 올려 두었습니다. 여기
있는 전부는 아래와 같습니다.

| 문서 | 내용 |
| --- | --- |
| [api-status-by-service.md](api-status-by-service.md) | 서비스별 Retrofit 엔트리 165개와 각각의 라이브 성공·실패·미실행 상태 |
| [api-endpoints.md](api-endpoints.md) | 원본 엔드포인트 표 — 메서드, 경로, 요청 파라미터, 반환 타입 |
| [pass-schedule-read.md](pass-schedule-read.md) | 정기권 조회의 정확한 요청·응답 타입과 라이브 검증 경계 |
| [verification-record.md](verification-record.md) | 증거 기록. 기능별 APK `파일:줄` 인용과 라이브 실행 결과 |
| [MUTATION_HANDOFF.md](MUTATION_HANDOFF.md) | 상태변경 표면의 운영 인수인계 — 무엇이 증명됐고 무엇이 남았는지 |
| [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) | 패키지 경계와 라우트 인벤토리의 날짜별 진행 기록 |
| [korail-apk-analysis.md](korail-apk-analysis.md) | APK 자체 — 구조, 호스트, 로그인, 보안, 결제, WebView |
| [library-build-guide.md](library-build-guide.md) | 정적 분석을 이 라이브러리로 옮긴 과정과 지켜야 할 정책 |
| [deep-dive/README.md](deep-dive/README.md) | 하위 시스템 보고서 20편과 읽는 순서 |
| [RELEASE.md](RELEASE.md) | 릴리스가 통과하는 테스트·빌드·배포 게이트 |
| [internal/README.md](internal/README.md) | 개발 기록. 사용자 문서가 아닙니다 |

이 표가 빠짐없는지는 `tests/test_docs_site.py` 가 확인합니다. `docs/` 아래 문서가
어디에서도 링크되지 않으면 테스트가 실패하므로, 새 문서를 넣으면 여기 한 줄을 더해야
합니다.
