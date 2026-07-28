# 기여 안내

## 작업 순서

1. 포크하고 `main` 에서 브랜치를 땁니다.
2. 변경합니다. 문서를 건드린다면 그것을 검사하는 테스트가 있다고 보면 됩니다.
3. 풀 리퀘스트를 열기 전에 오프라인 게이트 세 개를 돌립니다.

   ```bash
   pip install -e ".[dev]"                                     # test + ruff + pyright
   env -u KORAIL_MOBILE_API_LIVE python3 -m pytest -q -m "not live"
   ruff check .                                                # 0 이어야 합니다
   pyright                                                     # 오류 0 이어야 합니다
   ```

   셋 다 네트워크 없이 통과해야 하고, CI 도 같은 셋을 돌립니다. 스위트만 돌리려면
   `".[test]"` 로도 충분합니다. 두 도구는 설정을 `pyproject.toml` 에서만 읽으므로
   편집기(Pylance + Ruff 확장 — `.vscode/extensions.json` 참고)가 CI 와 같은 결과를
   보여줍니다. 규칙의 근거는 `[tool.ruff.lint]` 와 `[tool.pyright]` 의 주석에 있습니다.

   되돌리지 말아야 할 결정이 둘 있습니다.

   - **`ruff format` 은 쓰지 않습니다.** 손으로 정렬한 주석 표와 APK 근거 블록을
     포매터가 다시 씁니다. 게이트는 `ruff check` 이고 포매팅은 게이트가 아닙니다.
   - **pyright 은 `basic` 모드로 돌되 모듈 단위 `strict` 목록을 함께 씁니다.** 그
     목록은 `strict` 에서 이미 오류 0 을 기록한 모듈 전부입니다. 목록에 모듈을
     추가하는 것은 환영이고, 목록에 있는 모듈을 실패하게 만드는 것은 회귀입니다.
4. 기여의 일부로 라이브 서비스 테스트(`-m live` / `KORAIL_MOBILE_API_LIVE=1`)를 돌리면
   안 됩니다. 실제 계정이 필요하고 `smart.letskorail.com` 에 실제 요청을 보냅니다.
   그것은 관리자가 자기 계정에 대해 판단할 일입니다.
5. 풀 리퀘스트를 엽니다. **열기 전에 `.github/pull_request_template.md` 의 체크리스트에서
   자격증명·PNR·실제 서버 응답을 붙여넣지 말라는 항목을 읽어야 합니다.** PR 설명뿐 아니라
   그 안의 모든 diff, 픽스처, 스크린샷에 적용됩니다.

## 문서는 재는 것이지 주장하는 것이 아닙니다

라우트 개수, 메서드 이름, 테스트 개수처럼 코드에서 유도되는 값은 문서에 손으로 적는 순간
코드가 움직일 때 조용히 틀립니다. `tests/test_readme.py` 와
`tests/test_release_readiness.py` 는 기대값을 코드(`korail_mobile_api.__all__`,
`safety.KORAIL_READ_ONLY_ROUTES`, `inspect.getmembers(KorailClient, ...)` 등)에서
유도한 다음, 문서가 그 값을 말하고 있는지를 단언합니다.

공개 이름, 라우트, 상태 변경 메서드를 더하거나 지우면 그것을 언급하는 문장을 고칠 때까지
기존 테스트가 실패합니다. 새로 세어야 할 값이 생기면 문서든 테스트든 손으로 적지 말고
코드에서 유도해야 합니다.

## 동의·안전 모델을 바꾸는 경우

모든 상태 변경 메서드는 기본이 거부이며, 범주로 게이트되고, 라우트 소유자를 확인하고,
폼 형태를 확인한 뒤에야 프로세스 밖으로 나갑니다. 기제는
`src/korail_mobile_api/consent.py` 와 `safety.py` 에 있고, 배경은
`docs/MUTATION_HANDOFF.md` 와 `SECURITY.md` 에 있습니다.

다음 중 하나라도 건드리는 풀 리퀘스트에는 "고치는 것뿐"이라는 이유로 낮은 기준이 적용되지
않습니다. `safety.py` 의 허용 목록에 상태 변경 라우트나 범주를 추가하는 것,
`require_mutation_consent` / `post_mutation_form` / `get_mutation_query` 가 받아들이는
범위를 넓히는 것, 기본값(`dry_run`, `fake_card_only`, `real_card_acknowledged`, 범주별
`allow_*` 플래그)을 허용하는 쪽으로 바꾸는 것, `redact_payload` 가 민감하다고 보는 대상을
바꾸는 것입니다. 이 경우 다음 넷을 지켜야 합니다.

- **근거는 주장이 아니라 file:line 으로 대야 합니다.** 앱이 무엇을 보내는지에 대한 주장에는
  디컴파일된 APK 인용(`ClassName.java:NN` 또는 그에 해당하는 smali)이나 범위가 정해진
  라이브 실행 근거가 필요합니다. "앱이 X 를 할 것 같다"는 근거가 아니고,
  "`TCReservationDao.java:23-40` 이 이 FieldMap 을 만든다"가 근거입니다.
- **디컴파일된 소스를 붙여넣으면 안 됩니다.** `file:line` 을 가리키고 내용은 자기 말로
  설명하면 됩니다. 와이어 이름(라우트 경로, `@Field`/`@Query` 키, 리터럴 상수값)만 짧은
  백틱으로 인용하면 됩니다. 이 저장소는 앱의 소스 텍스트를 재생산하지 않습니다.
- **새 상태 변경 기능은 테스트 통과가 아니라 검토를 통과해야 합니다.** 별도의 안전 설계,
  새 근거, 독립 검토, 사용자의 명시적 승인이 필요합니다. 큰 diff 를 보내기 전에 기능과
  근거를 적은 이슈를 먼저 열어야 합니다.
- **손으로 유지되는 목록을 새로 만들면 안 됩니다.** 개수나 이름 목록은 기존 테스트가 하듯
  `safety.py` / `consent.MUTATION_CATEGORIES` / 클라이언트 클래스에서 유도되게 해야 합니다.

## 버그 신고

버그 신고 템플릿(`.github/ISSUE_TEMPLATE/`)으로 이슈를 엽니다. 실제 출력을 붙여넣기보다
디컴파일된 APK 인용(`file:line`)이나 최소한으로 위생처리한 재현을 우선해야 합니다.

보안과 관련된 문제(의도치 않은 상태 변경, 승인되지 않은 과금, 자격증명·개인정보 노출로
이어질 수 있는 것)는 공개 이슈 대신
[GitHub Security Advisories](https://github.com/yakisoba0728/korail-mobile-api/security/advisories/new)
를 씁니다. `SECURITY.md` 를 참고하면 됩니다.
