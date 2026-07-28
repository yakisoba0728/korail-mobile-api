"""문서 사이트가 패키지와 어긋나면 여기서 먼저 실패한다.

`mkdocs build --strict` 는 CI 가 돌린다. 이 모듈은 그 빌드가 돌기 전에, 그리고
mkdocs 없이도 확인할 수 있는 것만 본다 — 레퍼런스 쪽의 목록이 공개면과 같은지,
사이트가 쓰는 README 절 제목이 아직 있는지, 워크플로가 사이트를 실제로 빌드하고
배포는 수동으로만 도는지.

레퍼런스 모듈 목록은 `__init__.py` 의 `from .X import ...` 에서 유도한다. 손으로
적은 목록과 대조하는 것이 아니라, 손으로 적은 것(`mkdocs.yml` 의 차례와
`docs/reference/` 의 파일)이 유도된 것과 같은지를 본다.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "korail_mobile_api"
REFERENCE_DIR = ROOT / "docs" / "reference"
MKDOCS = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")


def _reexported_submodules() -> set[str]:
    """`__init__.py` 가 상대 import 로 이름을 꺼내 오는 서브모듈."""
    source = (ROOT / "src" / PACKAGE_NAME / "__init__.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module
    }


def test_every_reexporting_module_has_a_reference_page() -> None:
    modules = _reexported_submodules()
    assert modules

    pages = {path.stem for path in REFERENCE_DIR.glob("*.md")} - {"index"}
    assert pages == modules

    for module in sorted(modules):
        page = (REFERENCE_DIR / f"{module}.md").read_text(encoding="utf-8")
        # mkdocstrings 는 이 한 줄에서 쪽 전체를 만든다. 손으로 적은 심볼 목록이
        # 없다는 것이 이 단언의 내용이다.
        assert f"::: {PACKAGE_NAME}.{module}\n" in page
        assert "::: " in page and page.count("::: ") == 1


def test_the_navigation_lists_exactly_those_pages() -> None:
    navigated = set(re.findall(r"reference/([a-z_]+)\.md", MKDOCS)) - {"index"}
    assert navigated == _reexported_submodules()

    # 차례에 있는 쪽이 exclude_docs 로 빠져 있으면 mkdocs 가 조용히 뺀다.
    for page in ("index.md", "quickstart.md", "safety.md", "errors.md", "changelog.md"):
        assert f"!/{page}" in MKDOCS
    assert "!/reference/" in MKDOCS


def test_the_exclusion_only_covers_markdown() -> None:
    """제외 패턴이 마크다운보다 넓으면 테마의 CSS·JS 까지 빠진다.

    `exclude_docs` 는 docs_dir 뿐 아니라 테마가 넣는 파일에도 걸린다. `/*` 한
    줄이면 사이트가 스타일 없이 만들어지는데, `mkdocs build --strict` 는 그래도
    성공한다. 그래서 패턴의 모양 자체를 여기서 고정한다.
    """
    block = MKDOCS.split("exclude_docs: |", maxsplit=1)[1].split("\n\n", maxsplit=1)[0]
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    assert lines[0] == "*.md"
    assert all(line.startswith("!/") and line.endswith(".md") for line in lines[1:])


def test_the_reference_index_links_every_module_page() -> None:
    index = (REFERENCE_DIR / "index.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(([a-z_]+)\.md\)", index))
    assert linked == _reexported_submodules()


def test_the_included_readme_sections_still_exist() -> None:
    """사이트는 README 를 절 제목으로 잘라 싣는다. 제목이 바뀌면 조각이 사라진다."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    delimiters = set(re.findall(r'(?:start|end)="([^"]+)"', "".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "docs").glob("*.md")
    )))
    assert delimiters
    for delimiter in sorted(delimiters):
        assert delimiter in readme, delimiter


def test_ci_builds_the_site_and_deployment_is_manual_only() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    deploy = (ROOT / ".github/workflows/docs-deploy.yml").read_text(encoding="utf-8")

    assert "mkdocs build --strict" in ci
    assert 'pip install -e ".[docs]"' in ci

    # 저장소가 private 인 동안 Pages 는 유료 플랜을 요구한다. 배포는 사람이
    # 누를 때만 돈다 — push 나 태그로는 돌지 않는다.
    # 트리거 블록만 본다. 산문에는 "push" 라는 낱말이 나오지만(왜 push 로는
    # 돌리지 않는지를 적어 두었다) 트리거로는 없어야 한다.
    triggers = deploy.split("\non:\n", maxsplit=1)[1].split("\n\n", maxsplit=1)[0]
    assert "workflow_dispatch:" in triggers
    assert "push" not in triggers
    assert not re.search(r"(?m)^\s*tags\s*:", deploy)
    assert "mkdocs build --strict" in deploy


def test_the_docs_extra_installs_the_site_toolchain() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    docs_extra = pyproject.split("\ndocs = [", maxsplit=1)[1].split("]", maxsplit=1)[0]
    for requirement in ("mkdocs>=", "mkdocs-material>=", "mkdocstrings"):
        assert requirement in docs_extra


def test_the_built_site_is_not_tracked() -> None:
    # Binary stdin, not ``text=True``. Text mode translates the ``\n`` into
    # ``\r\n`` on Windows, git takes the carriage return as part of the path,
    # and the answer comes back as the quoted ``"site/index.html\r"`` -- a
    # different question, answered correctly.
    result = subprocess.run(
        ["git", "check-ignore", "--stdin"],
        cwd=ROOT,
        input=b"site/index.html\n",
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.decode("utf-8").splitlines() == ["site/index.html"]
