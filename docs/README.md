# docs/

이 디렉터리에는 성격이 다른 두 묶음이 있다.

**`docs/` 바로 아래 문서는 패키지를 설명한다.** 클라이언트가 무엇을 보내고, 서버가 무엇을
답하며, 어디까지 라이브 서비스로 확인됐고 어디부터는 확인되지 않았는지를 다룬다.
`korail-mobile-api` 를 쓰는 사람이 볼 만한 자료다.

**`docs/internal/` 은 개발 기록이다.** 감사, 재검증 기록, 설계 명세, 구현 계획이 들어 있다.
리버스 엔지니어링 클라이언트의 근거를 남기려고 보관하는 것이지 패키지 사용에 필요한
자료는 아니다.

**`index.md`·`quickstart.md`·`safety.md`·`errors.md`·`changelog.md`·`reference/`
는 문서 사이트의 원본이다.** 최상위 `mkdocs.yml` 이 이 여섯만 사이트로 올린다.
산문은 README 와 CHANGELOG 의 절을 그대로 끌어다 쓰고(`include-markdown`),
`reference/` 는 모듈마다 한 줄씩 mkdocstrings 지시자만 두어 docstring 에서
생성한다. 사이트를 보려면 `pip install -e ".[docs]"` 뒤에 `mkdocs serve` 한다.

문서별 내용은 최상위 README 의 [문서](../README.md#문서) 표를 보라.
