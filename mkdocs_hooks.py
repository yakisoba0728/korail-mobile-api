"""MkDocs 빌드 훅 넷. 저장소 파일 링크, reST 롤, 쪽을 넘는 앵커, 그리고 자산 확인.

**저장소 파일을 가리키는 링크.** 사이트는 `docs/` 의 일부만 페이지로 올린다.
README 와 `docs/` 의 나머지 문서는 저장소에 그대로 있으므로, 사이트에 없는
파일을 가리키는 상대 링크는 끊어진 링크가 아니라 GitHub 의 그 파일을 가리키는
링크여야 한다. 판정은 파일 목록으로 한다 — 사이트에 있으면 두고, 없으면
`blob/main/<경로>` 로 바꾼다. 어느 문서를 예외로 할지 적어 두는 목록은 없다.

**reST 롤.** 이 패키지의 docstring 은 ``:class:`X```/``:meth:`X``` 로 서로를
가리킨다. Pylance 는 이 표기를 읽지만 mkdocstrings 는 마크다운으로 넘기므로
``:class:`` 라는 접두사가 본문에 그대로 남는다. 접두사를 걷어 코드 조각만
남긴다. Sphinx 의 ``~`` 는 "마지막 이름만 보여라"라는 뜻이라 그대로 따른다.
``.. code-block:: text`` 지시자 줄도 같은 이유로 지운다 — 뒤따르는 들여쓴
블록은 마크다운에서도 코드 블록이라 지시자 줄만 군더더기로 남는다.

**쪽을 넘는 앵커.** README 는 한 파일이라 `#안전-모델` 처럼 같은 문서 안을
가리킨다. 이 사이트는 그 절들을 여러 쪽에 나눠 담으므로 같은 링크가 제자리에서
아무 데도 가지 않게 된다. 모든 쪽이 렌더링된 뒤에 앵커 색인을 만들어, 자기
쪽에 없고 다른 쪽에 딱 하나 있는 앵커만 그 쪽으로 돌린다. 어느 절이 어느
쪽에 있는지 적어 두지 않는다 — 렌더링 결과에서 읽는다.

**자산 확인.** `exclude_docs` 는 docs_dir 뿐 아니라 테마가 넣는 파일에도 걸린다.
`/*` 같은 패턴 하나면 테마의 CSS 와 JS 가 통째로 빠지는데, 그래도 빌드는
`--strict` 로도 성공한다 — 나오는 것은 스타일이 하나도 없는 사이트다. 빌드
끝에 첫 쪽이 참조하는 지역 자산이 실제로 있는지 세어 본다.
"""

from __future__ import annotations

import posixpath
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from mkdocs.exceptions import PluginError
from mkdocs.structure.files import InclusionLevel
from mkdocs.utils import get_relative_url


if TYPE_CHECKING:  # pragma: no cover - 타입 힌트 전용
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page


# `[텍스트](대상)` 의 대상만 잡는다. 이미지(`![...]`)는 앞의 `!` 로 걸러 낸다.
_MARKDOWN_LINK = re.compile(r"(?<!!)\[(?P<text>[^\]\n]*)\]\((?P<target>[^)\s]+)\)")
_EXTERNAL_SCHEME = re.compile(r"\A(?:[a-z][a-z0-9+.-]*:|//|#|/)", re.IGNORECASE)
_REST_ROLE = re.compile(
    r":(?:class|meth|func|mod|attr|data|exc|obj|const):<code>(?P<body>[^<]*)</code>"
)
_DIRECTIVE_PARAGRAPH = re.compile(r"<p>\s*\.\.\s+code-block::[^<]*</p>\s*")
_HTML_ID = re.compile(r'\sid="(?P<value>[^"]+)"')
_FRAGMENT_HREF = re.compile(r'href="#(?P<anchor>[^"]+)"')
_ASSET_REFERENCE = re.compile(r'(?:href|src)="(?P<target>[^"]+)"')
_REMOTE_REFERENCE = ("http://", "https://", "//", "#", "data:", "mailto:")


def _blob_url(config: MkDocsConfig, repo_path: str) -> str:
    return f"{config.repo_url.rstrip('/')}/blob/main/{repo_path}"


def _docs_dir_name(config: MkDocsConfig) -> str:
    """저장소 뿌리에서 본 docs_dir 의 이름. mkdocs.yml 이 뿌리에 있다는 사실만 쓴다."""
    root = Path(config.config_file_path).parent
    return Path(config.docs_dir).relative_to(root).as_posix()


def on_page_markdown(
    markdown: str,
    *,
    page: Page,
    config: MkDocsConfig,
    files: Files,
    **_: Any,
) -> str:
    """사이트에 없는 파일을 가리키는 상대 링크를 GitHub 링크로 바꾼다."""
    # `exclude_docs` 로 뺀 파일도 Files 에는 남아 있다(mkdocs 는 지우는 대신
    # inclusion 등급을 낮춘다). 사이트에 실제로 올라가는 것만 "있는 것"으로 센다.
    known = {
        file.src_uri
        for file in files
        if file.inclusion is not InclusionLevel.EXCLUDED
    }
    page_dir = posixpath.dirname(page.file.src_uri)
    docs_dir_name = _docs_dir_name(config)

    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        if _EXTERNAL_SCHEME.match(target):
            return match.group(0)
        path, separator, fragment = target.partition("#")
        if not path:
            return match.group(0)
        resolved = posixpath.normpath(posixpath.join(page_dir, path))
        if resolved in known:
            return match.group(0)
        # docs_dir 안에서 풀리지 않았다. 같은 경로를 저장소 뿌리 기준으로 다시
        # 계산하면 (docs/ 밖으로 나가는 `../` 도 여기서 정리된다) 저장소에 있는
        # 파일이라면 그 경로가 나온다.
        repo_path = posixpath.normpath(posixpath.join(docs_dir_name, page_dir, path))
        if repo_path.startswith(".."):
            return match.group(0)
        url = _blob_url(config, repo_path) + separator + fragment
        return f"[{match.group('text')}]({url})"

    return _MARKDOWN_LINK.sub(replace, markdown)


def on_page_content(html: str, **_: Any) -> str:
    """docstring 에서 온 reST 표기를 읽을 수 있는 형태로 남긴다."""

    def replace(match: re.Match[str]) -> str:
        body = match.group("body").strip()
        # ``:attr:`보일 이름 <전체.경로>``` 형태는 앞쪽이 보일 이름이다.
        title, separator, _ = body.partition("&lt;")
        target = title.strip() if separator else body
        if target.startswith("~"):
            target = target[1:].rsplit(".", maxsplit=1)[-1]
        return f"<code>{target}</code>"

    return _DIRECTIVE_PARAGRAPH.sub("", _REST_ROLE.sub(replace, html))


def on_env(env: Any, *, files: Files, **_: Any) -> Any:
    """자기 쪽에 없는 앵커 링크를 그 앵커가 실제로 있는 쪽으로 돌린다.

    이 이벤트는 모든 쪽의 마크다운 변환이 끝난 뒤, 템플릿을 채우기 전에
    돈다. 그래서 여기서만 "다른 쪽에 무엇이 있는지"를 볼 수 있다.
    """
    pages = [
        file.page
        for file in files
        if file.page is not None and file.page.content is not None
    ]
    anchors: dict[str, list[Page]] = {}
    owned: dict[str, set[str]] = {}
    for page in pages:
        identifiers = {match.group("value") for match in _HTML_ID.finditer(page.content or "")}
        owned[page.file.src_uri] = identifiers
        for identifier in identifiers:
            anchors.setdefault(identifier, []).append(page)

    for page in pages:
        mine = owned[page.file.src_uri]

        def replace(match: re.Match[str], mine: set[str] = mine, page: Page = page) -> str:
            anchor = match.group("anchor")
            if anchor in mine:
                return match.group(0)
            holders = anchors.get(anchor, [])
            if len(holders) != 1:
                return match.group(0)
            target = get_relative_url(holders[0].url, page.url)
            return f'href="{target}#{anchor}"'

        page.content = _FRAGMENT_HREF.sub(replace, page.content or "")
    return env


def on_post_build(*, config: MkDocsConfig, **_: Any) -> None:
    """첫 쪽이 부르는 지역 자산이 전부 site_dir 에 있는지 확인한다."""
    site = Path(config.site_dir)
    index = site / "index.html"
    if not index.is_file():
        raise PluginError("site_dir 에 index.html 이 없다")

    html = index.read_text(encoding="utf-8")
    missing = sorted(
        {
            target
            for target in _ASSET_REFERENCE.findall(html)
            if target
            and not target.startswith(_REMOTE_REFERENCE)
            and not (site / posixpath.normpath(target.split("#")[0].split("?")[0])).exists()
        }
    )
    if missing:
        raise PluginError(f"빌드된 사이트에 없는 자산을 부른다: {', '.join(missing)}")
