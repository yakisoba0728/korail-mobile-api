# 배포 절차

패키지 버전은 `src/korail_mobile_api/__init__.py`의 `__version__` 한 곳에서 관리합니다.
`pyproject.toml`과 배포 파일의 메타데이터는 이 값을 읽습니다. 아래 명령은 **2.4.0** 기준입니다.
다음 배포에서는 버전, 변경 이력, 태그와 파일 경로를 함께 바꾸세요.

## 문서와 버전

- `CHANGELOG.md`에 버전·날짜·사용자에게 달라진 동작과 검증 한계를 기록합니다. 문서 사이트의 변경 이력은 이 파일을 그대로 포함합니다.
- 새 공개 메서드의 정확한 시그니처와 예외를 API 레퍼런스에 추가하고, API 목록·가이드·README·실서버 확인 현황을 맞춥니다.
- 미배포 기능은 Unreleased와 개발 버전 설치 필요 여부를 표시합니다. 릴리스할 때 실제 포함된 기능의 안내를 최소 지원 버전으로 바꿉니다.
- 과거 실서버 확인 기록의 날짜와 집계는 유지합니다. 오프라인 테스트 통과를 실서버 성공으로 바꾸지 않습니다.
- README는 PyPI에도 표시되므로 외부 문서 링크와 이미지에 절대 URL을 씁니다.

2.4.0의 `proxy` 설정은 API·대기열 전송 계층 구성과 요청 경로를 합성 테스트로 확인했습니다.
프록시를 거친 실서버 요청은 아직 확인하지 않았으므로, 확인 전에는 변경 이력의 검증 한계 문구를 유지합니다.
기존 메서드의 실서버 확인 범위는 [실서버 확인 현황](status.md)에 있습니다.

## 로컬 검증

저장소 루트에서 가상환경을 만들고 개발·문서 의존성을 설치합니다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]' -r docs/requirements.txt
.venv/bin/python -m ruff check src checks tests
.venv/bin/python -m ruff format --check src checks tests
.venv/bin/python -m mypy
.venv/bin/python -m pyright
.venv/bin/python -m pytest tests/ --cov=korail_mobile_api --cov-branch --cov-report=term-missing:skip-covered --cov-fail-under=90
.venv/bin/python -m mkdocs build --strict
git diff --check
```

전체 테스트에는 원래의 두 오프라인 검사, 공개 API 목록, 문서 시그니처·예제, 실제 패키지 빌드와
배포 파일 내용 검사가 포함됩니다. 테스트는 소켓을 차단하고 가짜 응답만 사용합니다.

CI는 Python 3.11·3.12·3.13·3.14와 Python 3.11의 선언된 최소 의존성 조합을 검사합니다.
빌드한 wheel을 별도 가상환경에 설치해 import·버전·의존성·오프라인 검사도 확인합니다.
배포 워크플로는 지정한 태그에서 이 CI를 다시 실행하고 모두 통과해야 업로드합니다.

## 배포 파일 만들기

다른 버전의 파일과 섞이지 않도록 버전별 디렉터리에 만듭니다.
`python -m build`는 sdist를 만든 뒤 그 sdist에서 wheel을 빌드합니다.

```sh
.venv/bin/python -m build --outdir dist/2.4.0
.venv/bin/python -m twine check --strict dist/2.4.0/*.whl dist/2.4.0/*.tar.gz
```

배포 파일은 다음 두 개입니다.

- `dist/2.4.0/korail_mobile_api-2.4.0-py3-none-any.whl`
- `dist/2.4.0/korail_mobile_api-2.4.0.tar.gz`

wheel에는 런타임 소스·`py.typed`·패키지 메타데이터와 라이선스가 들어갑니다.
sdist에는 README·변경 이력·검사·테스트도 포함됩니다. 문서 사이트는 별도 배포합니다.

## 태그와 PyPI 업로드

검증한 변경을 커밋하고 원격 저장소에 반영한 뒤, **그 커밋**에 태그를 만듭니다.
작업 트리가 깨끗하고 원하는 커밋을 가리키는지 먼저 확인하세요.

```sh
git status --short
git log -1 --oneline
git tag -a v2.4.0 -m 'Release 2.4.0'
git push origin v2.4.0
gh workflow run publish.yml --ref v2.4.0
```

이 마지막 명령은 실제 PyPI 업로드를 시작합니다. 워크플로는 태그 이름과 패키지 버전 일치를 검사하고,
CI·빌드·`twine check --strict`를 거친 뒤 PyPI Trusted Publishing으로 업로드합니다.
PyPI의 게시자 설정은 이 저장소의 `publish.yml`과 `pypi` 환경에 연결돼 있어야 합니다.
이미 게시한 버전 번호는 새 파일을 올리는 데 재사용할 수 없습니다.

Actions의 **Publish to PyPI** 실행 결과와 PyPI에 표시되는 버전을 확인합니다.
실패했다면 어느 단계까지 완료됐는지 확인하고, 업로드 완료 여부가 불명확한 상태에서 버전을 덮어쓰려 하지 마세요.

## 문서 사이트와 공개 기록

패키지 업로드가 성공하면 릴리스와 같은 커밋의 문서를 배포합니다.
현재 `github-pages` 환경은 `main` 브랜치에서만 배포를 허용하므로,
원격 `main`과 릴리스 태그가 같은 커밋인지 확인한 뒤 `main`에서 실행합니다.

```sh
git fetch origin --tags
test "$(git rev-parse origin/main)" = "$(git rev-parse 'v2.4.0^{commit}')" &&
    gh workflow run docs-deploy.yml --ref main
```

**Docs site** 워크플로가 성공했는지 확인하고, 문서 사이트의 변경 이력과
[기존 예약 가이드](guide/payments.md#existing-reservation)가 해당 버전 내용인지 확인합니다.
워크플로 실행의 커밋도 릴리스 태그와 일치해야 합니다. `main`이 앞서간 경우에는 위 명령을 그대로 진행하지 말고 배포할 문서 버전을 먼저 확인하세요.
GitHub Release를 만들 때는 `CHANGELOG.md`의 2.4.0 항목을 릴리스 설명으로 사용하고 같은 태그를 지정하세요.

마지막으로 새 가상환경에서 `pip install korail-mobile-api==2.4.0`을 실행해
`korail_mobile_api.__version__`과 설치된 패키지 메타데이터가 `2.4.0`인지 확인합니다.
