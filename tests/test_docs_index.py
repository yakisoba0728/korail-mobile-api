# korail-mobile-api — Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
# 수정 시 §4(b)에 따라 수정 사실을 표시해야 합니다.

"""`docs/README.md` 의 색인이 실제 문서와 어긋나지 않게 합니다.

색인은 손으로 유지되는 목록이고, 손으로 유지되는 목록은 썩습니다. 그 표는 스스로
"여기 있는 전부는 아래와 같습니다" 라고 말하므로, 한 줄이 빠지면 표가 거짓말을
합니다. 실제로 두 번 그랬습니다 — 한 번은 README 를 줄이면서 다섯 줄이 사라졌고,
한 번은 `7.0.6-implementation-followup.md` 가 만들어질 때 줄이 추가되지 않았습니다.
파일은 그대로 있었으므로 링크 검사도 `mkdocs build --strict` 도 통과했습니다.

그래서 두 가지를 봅니다. 표가 `docs/` 바로 아래 문서를 빠짐없이 싣는지(문서를
추가하고 색인을 잊으면 여기서 걸립니다), 그리고 표의 각 줄이 실재하는 파일을
가리키는지(문서를 지우고 줄을 남기면 걸립니다). 하위 디렉터리의 보고서들은 자기
디렉터리의 README 가 가리키므로, 그쪽은 고아가 아닌지만 확인합니다.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "README.md"


def _tracked_docs() -> list[str]:
    return subprocess.run(
        ["git", "ls-files", "docs"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout.decode("utf-8").splitlines()


def _site_pages() -> set[str]:
    """`mkdocs.yml` 의 `nav` 가 싣는 산문 페이지(레퍼런스 제외).

    사이트 원본은 색인이 아니라 `nav` 가 가리킵니다. 제외 목록이 아니라 `nav` 에서
    읽는 것은, 제외 목록에서 읽으면 그 목록을 자기 자신과 비교하게 되기 때문입니다.
    """
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    block = mkdocs.split("\nnav:\n", maxsplit=1)[1]
    block = re.split(r"\n(?=\S)", block, maxsplit=1)[0]
    pages = set(
        re.findall(r"^\s*-\s*(?:[^:\n]+:\s*)?([\w./-]+\.md)\s*$", block, re.MULTILINE)
    )
    return {page for page in pages if not page.startswith("reference/")}


def _indexed_targets() -> set[str]:
    """색인 표의 각 줄이 가리키는 `docs/` 상대 경로."""
    rows = re.findall(
        r"^\|\s*\[[^\]]+\]\(([^)#]+)\)",
        INDEX.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    return {target.strip() for target in rows}


def test_the_index_lists_every_document_directly_under_docs() -> None:
    expected = {
        path.removeprefix("docs/")
        for path in _tracked_docs()
        if path.endswith(".md") and path.count("/") == 1
    }
    # 사이트가 싣는 산문 페이지는 `nav` 가, 색인 자신은 아무도 싣지 않습니다.
    expected -= _site_pages() | {"README.md"}
    missing = sorted(expected - _indexed_targets())
    assert missing == [], missing


def test_every_index_row_points_at_a_document_that_exists() -> None:
    dangling = sorted(
        target for target in _indexed_targets()
        if not (ROOT / "docs" / target).exists()
    )
    assert dangling == [], dangling


def test_no_document_under_docs_is_unreachable() -> None:
    """하위 디렉터리까지 포함해, 어디에서도 링크되지 않은 문서가 없는지."""
    tracked = _tracked_docs()
    # docs/internal/ 은 개발 아카이브입니다. 그 안의 감사 보고서 하나하나까지
    # 색인할 이유는 없고, 디렉터리 자체는 README 가 가리킵니다.
    documents = {
        path for path in tracked
        if path.endswith(".md") and not path.startswith("docs/internal/")
    }
    documents -= {f"docs/{page}" for page in _site_pages()} | {"docs/README.md"}

    sources = [ROOT / "README.md"] + [
        ROOT / path for path in tracked if path.endswith(".md")
    ]
    haystack = "\n".join(
        path.read_text(encoding="utf-8") for path in sources if path.is_file()
    )
    # 링크는 문서마다 다른 상대 경로로 적힙니다(`agent-reports/01-x.md`,
    # `../README.md`, `docs/RELEASE.md`). 경로를 맞추려 들면 그 형태를 전부
    # 열거하게 되므로, 마크다운 링크 안에 파일명이 나오는지만 봅니다.
    linked = set(re.findall(r"\]\([^)]*?([\w.\-]+\.md)[)#]", haystack))
    unreachable = sorted(
        path for path in documents
        if path.rsplit("/", maxsplit=1)[-1] not in linked
    )
    assert unreachable == [], unreachable
