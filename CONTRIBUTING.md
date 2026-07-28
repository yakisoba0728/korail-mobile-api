# 기여 안내

## 작업 순서

1. 포크하고 `main` 에서 브랜치를 딴다.
2. 변경한다. 문서를 건드린다면 그것을 검사하는 테스트가 있다고 보면 된다. 숫자나 주장을
   손으로 쓰기 전에 아래 "문서는 재는 것이지 주장하는 것이 아니다"를 먼저 읽어라.
3. 풀 리퀘스트를 열기 전에 오프라인 게이트 세 개를 돌린다.

   ```bash
   pip install -e ".[dev]"                                     # test + ruff + pyright
   env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
   ruff check .                                                # 0 이어야 한다
   pyright                                                     # 오류 0 이어야 한다
   ```

   셋 다 네트워크 없이 통과해야 하고, CI 도 같은 셋을 돌린다. 스위트만 돌리고 싶다면
   `".[test]"` 로도 충분하다.

   두 도구는 설정을 `pyproject.toml` 에서만 읽으므로, 편집기(Pylance + Ruff 확장 —
   `.vscode/extensions.json` 참고)가 CI 와 똑같은 결과를 보여준다. 규칙에 이견이 있다면
   `[tool.ruff.lint]` 나 `[tool.pyright]` 의 해당 항목 옆 주석을 보라. 무엇을 재서 그렇게
   정했는지 적혀 있다.

   되돌리지 말아야 할 결정이 둘 있다.

   - **`ruff format` 은 쓰지 않는다.** 이 코드베이스의 손으로 정렬한 주석 표와 APK 근거
     블록은 그 자체가 문서인데 포매터가 그것을 다시 쓴다. 게이트는 `ruff check` 이고
     포매팅은 게이트가 아니다.
   - **pyright 은 `basic` 모드로 돌되 모듈 단위 `strict` 목록을 함께 쓴다.** 그 목록은
     취향이 아니라 `strict` 에서 이미 오류 0 을 기록한 모듈 전부이며, 파일별로 pyright 을
     한 번씩 돌리면 다시 유도할 수 있다. 목록에 모듈을 추가하는 것은 환영이고, 목록에
     있는 모듈을 실패하게 만드는 것은 회귀다.
4. 기여의 일부로 라이브 서비스 테스트(`-m live` / `KORAIL_MOBILE_API_LIVE=1`)를 돌리지
   마라. 실제 계정이 필요하고 `smart.letskorail.com` 에 실제 요청을 보낸다. 그것은
   관리자가 자기 계정에 대해 판단할 일이지 기여가 유발할 일이 아니다. 대신 어떤 근거를
   담을지는 아래 "버그 신고"를 보라.
5. 풀 리퀘스트를 연다. **열기 전에 `.github/pull_request_template.md` 의 체크리스트에서
   자격증명·PNR·실제 서버 응답을 붙여넣지 말라는 항목을 읽어라.** 이는 PR 설명뿐 아니라
   그 안의 모든 diff, 픽스처, 스크린샷에 적용된다.

## 문서는 재는 것이지 주장하는 것이 아니다

라우트 개수, 메서드 이름, 테스트 개수처럼 코드에서 유도되는 값은 문서에 손으로 적는 순간
코드가 움직일 때 조용히 틀린다. `tests/test_readme.py` 와 `tests/test_release_readiness.py`
는 기대값을 테스트 안에 얼려두는 대신 코드(`korail_mobile_api.__all__`,
`safety.KORAIL_READ_ONLY_ROUTES`, `inspect.getmembers(KorailClient, ...)` 등)에서 유도한
다음, 문서가 그 유도된 값을 말하고 있는지를 단언한다.

공개 이름, 라우트, 상태 변경 메서드를 더하거나 지우면 그것을 언급하는 문장을 고칠 때까지
기존 테스트가 실패한다. 새로 세어야 할 값이 생기면 문서든 테스트든 손으로 적지 말고 코드에서
유도하라.

## 동의·안전 모델을 바꾸는 경우

이 패키지는 훨씬 큰 읽기 전용 표면 위에 작은 동의 기반 상태 변경 표면을 얹고 있다
(`docs/MUTATION_HANDOFF.md` 와 `SECURITY.md` 참고). 모든 상태 변경 메서드는 기본이 거부이며,
범주로 게이트되고, 라우트 소유자를 확인하고, 폼 형태를 확인한 뒤에야 프로세스 밖으로
나간다. 기제는 `src/korail_mobile_api/consent.py` 와 `safety.py` 에 있고, 이 표면이 승인될
때 지켜진 기준은 `docs/library-build-guide.md` ("Suggested Library Modules" / mutation
policy)에 있다.

다음 중 하나라도 건드리는 풀 리퀘스트는 "고치는 것뿐"이라는 이유로 낮은 기준이 적용되지
않는다.

- `safety.py` 의 허용 목록에 상태 변경 라우트나 범주를 추가하는 것,
- `require_mutation_consent`, `post_mutation_form`, `get_mutation_query` 가 받아들이는
  범위를 넓히는 것,
- 기본값(`dry_run`, `fake_card_only`, `real_card_acknowledged`, 범주별 `allow_*` 플래그)을
  허용하는 쪽으로 바꾸는 것,
- `redact_payload` 가 민감하다고 보는 대상을 바꾸는 것.

구체적으로는 이렇다.

- **근거는 주장이 아니라 file:line 으로 대라.** 앱이 무엇을 보내는지에 대한 주장에는
  디컴파일된 APK 인용(`ClassName.java:NN` 또는 그에 해당하는 smali)이나 범위가 정해진
  라이브 실행 근거가 필요하다. 이 저장소의 다른 감사들이 쓰는 인용 규율과 같다. "앱이 X 를
  할 것 같다"는 근거가 아니고, "`TCReservationDao.java:23-40` 이 이 FieldMap 을 만든다"가
  근거다.
- **디컴파일된 소스를 붙여넣지 마라.** `file:line` 을 가리키고 내용은 자기 말로 설명하라.
  와이어 이름(라우트 경로, `@Field`/`@Query` 키, 리터럴 상수값)만 짧은 백틱으로 인용하라.
  이 저장소는 앱의 소스 텍스트를 재생산하지 않으며, 그렇게 한 PR 은 병합 전에 다시 써야
  한다.
- **새 상태 변경 기능은 테스트 통과가 아니라 검토를 통과해야 한다.** 이 프로젝트가 지금까지
  모든 상태 변경 범주에 적용한 네 가지 기준은 그대로다. 별도의 안전 설계, 새 근거, 독립
  검토, 그리고 사용자의 명시적 승인. 스위트가 초록이라는 것은 코드가 만든 대로 동작한다는
  뜻이지 그것이 존재해도 된다는 뜻이 아니다. 큰 diff 를 보내기 전에 기능과 근거를 적은
  이슈를 먼저 열어라.
- **손으로 유지되는 목록을 새로 만들지 마라.** 변경 때문에 어딘가의 개수나 이름 목록을
  고쳐야 한다면, 기존 테스트가 하듯 `safety.py` / `consent.MUTATION_CATEGORIES` / 클라이언트
  클래스에서 유도되게 만들어라.

## 버그 신고

버그 신고 템플릿(`.github/ISSUE_TEMPLATE/`)으로 이슈를 연다. 실제 출력을 붙여넣기보다
디컴파일된 APK 인용(`file:line`)이나 최소한으로 위생처리한 재현을 우선하라. 무엇을 넣지
말아야 하는지는 템플릿에 있다.

보안과 관련된 문제(의도치 않은 상태 변경, 승인되지 않은 과금, 자격증명·개인정보 노출로
이어질 수 있는 것)는 공개 이슈 대신
[GitHub Security Advisories](https://github.com/yakisoba0728/korail-mobile-api/security/advisories/new)
를 쓴다. `SECURITY.md` 를 보라.
