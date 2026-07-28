# 개시 게이트

이 패키지를 개시할 때마다 거치는 빌드·검증 절차입니다. 오프라인 테스트, wheel·sdist 빌드,
두 산출물에 대한 동작 기반 계약 검사, 그리고 체크아웃 바깥의 새 환경에서 하는 임포트로
이루어집니다. 여기의 어떤 절차도 `smart.letskorail.com` 과 통신하지 않습니다.

## 전제

- 추적 대상 파일이 깨끗한 워크트리에서 시작합니다.
- Python 3.11 이상을 쓰고 테스트·빌드 도구를 로컬에 설치합니다.
- 이 게이트에서 라이브 테스트는 금지입니다. 자격증명, 로컬 라이브 설정, 쿠키, 토큰, 운영
  응답 데이터를 불러오면 안 됩니다.

## 테스트·빌드·검증

저장소 루트에서 실행합니다.

```bash
set -euo pipefail

artifact_dir=""
venv_dir=""
outside_dir=""
checkout="$PWD"

cleanup() {
  cd "$checkout" 2>/dev/null || true
  if [[ -n "$artifact_dir" ]]; then rm -rf "$artifact_dir"; fi
  if [[ -n "$venv_dir" ]]; then rm -rf "$venv_dir"; fi
  if [[ -n "$outside_dir" ]]; then rm -rf "$outside_dir"; fi
  rm -rf "$checkout/build" "$checkout/dist"
  find "$checkout" -type d -name '*.egg-info' -prune -exec rm -rf {} +
}
trap cleanup EXIT

python3 -m pip install -e ".[test]"
python3 -m pip install build
PYTHONPATH="$PWD/src" pytest -q -m "not live"

artifact_dir="$(mktemp -d)"
venv_dir="$(mktemp -d)"
outside_dir="$(mktemp -d)"
python3 -m build --wheel --sdist --outdir "$artifact_dir" .
wheel_path="$(find "$artifact_dir" -maxdepth 1 -name '*.whl' -print -quit)"
sdist_path="$(find "$artifact_dir" -maxdepth 1 -name '*.tar.gz' -print -quit)"
python3 scripts/verify_distribution.py "$wheel_path" "$sdist_path"
python3 -m venv "$venv_dir"
"$venv_dir/bin/python" -m pip install "$wheel_path"

checkout="$PWD"
cd "$outside_dir"
unset PYTHONPATH
"$venv_dir/bin/python" - <<PY
from pathlib import Path
import korail_mobile_api
from korail_mobile_api import KorailClient

package_path = Path(korail_mobile_api.__file__).resolve()
assert "site-packages" in package_path.parts
assert Path("$checkout").resolve() not in package_path.parents
print(KorailClient.__name__, package_path)
PY
cd "$checkout"
cleanup
trap - EXIT
```

검증기는 wheel 하나와 소스 배포본 하나를 정확히 하나씩만 받아야 합니다. 새 환경의
임포트는 체크아웃 바깥의 `site-packages` 에서 해결돼야 합니다.

`EXIT` 트랩이 성공·실패 양쪽에서 임시 디렉터리와 로컬 빌드 메타데이터를 지웁니다. 마지막의
명시적 `cleanup` 호출은 모든 검사를 통과한 뒤에야 그 트랩을 해제합니다. 끝으로
`git status --short` 와 `git diff --check` 를 확인합니다.

## 버전 정책

`1.0.0` 부터 이 프로젝트는 유의적 버전(SemVer)을 따릅니다. 메이저 자리는
`korail_mobile_api` 자신의 공개 Python API — `korail_mobile_api.__all__` 에 있는 이름과 그
시그니처 — 에 대한 파괴적 변경을 뜻합니다.

이 약속의 대상은 이 패키지의 API 뿐입니다. 엔드포인트, 요청 필드, 응답 형태는 KORAIL 이
버전을 매기는 것이며 예고 없이 바뀔 수 있습니다. 서버 쪽 변경으로 이 클라이언트가
망가지는 것은 이 클라이언트의 파괴적 변경이 아닙니다.

## 공개 개시 요건

공개 GitHub 저장소로의 개시는 네 가지를 전제로 하며, `1.0.0` 기준으로 넷 다 충족합니다.

- **라이선스.** Apache-2.0. `pyproject.toml` 의 PEP 639 `license` SPDX 식으로 선언하고
  두 빌드 산출물 모두에 `LICENSE` 로 넣습니다.
- **소유자 메타데이터.** `pyproject.toml` 의 `authors` 항목이며 `Author-email` 헤더로
  나갑니다.
- **정규 URL.** `pyproject.toml` 의 `[project.urls]` 이며 `Project-URL` 헤더로 나갑니다.
- **명시적 승인.** 저장소 소유자가 이 프로젝트를 Apache-2.0 으로 공개하는 것을 명시적으로
  승인했습니다.

앞의 세 가지는 `scripts/verify_distribution.py` 가 빌드마다 `pyproject.toml` 과 대조해
정확한 값을 강제합니다.

## 동작 기반 검증 계약

배포 검증기(`scripts/verify_distribution.py`)와 그 오프라인 스위트
(`tests/test_release_readiness.py`)가 강제하는 것은 파일 존재 확인이 아니라 동작 기반
계약입니다. 스위트는 wheel·sdist 픽스처를 실제로 만들어 검증기의 `main()` 을 돌리고,
아카이브와 메타데이터가 실제로 거부되는지를 단언합니다. 규칙마다 그것을 노리는 픽스처가
하나씩 있습니다.

- 정규 멤버 경로와 정규화 후 이름. 중복된 멤버를 실은 wheel 이나 sdist 는 거부됩니다.
- 0바이트 `py.typed` 마커. 두 아카이브 모두에서 일반 파일이면서 비어 있어야 합니다.
- 정확한 메타데이터. `Name`, `Version`, `Requires-Python`, `License-Expression`,
  `Author-email` 은 각각 단 하나여야 하고, classifier 집합과 `Project-URL`·`License-File`
  집합은 중복 없이 `pyproject.toml` 이 선언한 값과 일치해야 하며, 런타임
  `Requires-Dist` 는 정규화 후 `pyproject.toml` 과 같아야 합니다. PEP 639 빌드가 결코 내지
  않는 구식 헤더(`License`, `Author`, `Maintainer`, `Maintainer-email`, `Home-page`,
  `Download-URL`)는 거부합니다. 그 헤더가 있다는 것은 이 빌드가 아닌 무언가가 메타데이터를
  썼다는 뜻입니다.
- 아카이브 형태. sdist 는 풀지 않고 엄격한 gzip tar(`r:gz`)로 검사하며, 두 아카이브 중
  어디에든 심볼릭 링크, 하드 링크, 장치, FIFO 같은 특수 멤버가 있으면 거부합니다.
- 잘못됐거나 지원하지 않는 입력에는 고정된 stderr 한 줄만 냅니다. 경로, 트레이스백,
  아카이브 멤버, 예외 문구를 흘리지 않습니다.

게이트 자체는 위에 정의한 `set -euo pipefail`, `EXIT` 뒷정리 트랩, 오프라인 선택
`pytest -q -m "not live"` 로 돌아갑니다.
