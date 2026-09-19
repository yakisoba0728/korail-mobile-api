# korail-mobile-api — https://github.com/yakisoba0728/korail-mobile-api
# Copyright (c) 2026 yakisoba0728
# SPDX-License-Identifier: Apache-2.0
#
# Apache License 2.0 으로 배포됩니다(전문: LICENSE, 귀속 고지: NOTICE).
# 재배포 시 이 고지를 소스 형태로 그대로 유지해야 하고(§4(c)), 수정했다면
# 수정했다는 사실을 눈에 띄게 표시해야 합니다(§4(b)).

"""The four build hooks in mkdocs_hooks.py, called directly.

``mkdocs build --strict`` runs them in CI, but a build that succeeds says
little about what they did: a link left pointing nowhere or an anchor left
unrewritten still builds. These call each hook with just the attributes it
reads, so every decision it makes is pinned here.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from mkdocs.exceptions import PluginError
from mkdocs.structure.files import InclusionLevel


ROOT = Path(__file__).parents[1]


def _hooks() -> Any:
    spec = importlib.util.spec_from_file_location("mkdocs_hooks", ROOT / "mkdocs_hooks.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hooks = _hooks()


def _config(tmp_path: Path, **extra: Any) -> SimpleNamespace:
    return SimpleNamespace(
        repo_url="https://github.com/example/repo/",
        config_file_path=str(tmp_path / "mkdocs.yml"),
        docs_dir=str(tmp_path / "docs"),
        **extra,
    )


def _file(src_uri: str, *, excluded: bool = False) -> SimpleNamespace:
    level = InclusionLevel.EXCLUDED if excluded else InclusionLevel.INCLUDED
    return SimpleNamespace(src_uri=src_uri, inclusion=level, page=None)


def _markdown(tmp_path: Path, text: str, *, page: str = "guide/start.md") -> str:
    files = [
        _file("index.md"),
        _file("guide/start.md"),
        _file("guide/next.md"),
        _file("internal/notes.md", excluded=True),
    ]
    return hooks.on_page_markdown(
        text,
        page=SimpleNamespace(file=SimpleNamespace(src_uri=page)),
        config=_config(tmp_path),
        files=files,
    )


BLOB = "https://github.com/example/repo/blob/main/"


@pytest.mark.parametrize(
    ("link", "expected"),
    [
        ("[n](next.md)", "[n](next.md)"),
        ("[n](next.md#part)", "[n](next.md#part)"),
        ("[i](../index.md)", "[i](../index.md)"),
        ("[r](../../README.md)", f"[r]({BLOB}README.md)"),
        ("[r](../../README.md#안전-모델)", f"[r]({BLOB}README.md#안전-모델)"),
        ("[o](../other.md)", f"[o]({BLOB}docs/other.md)"),
        ("[x](../internal/notes.md)", f"[x]({BLOB}docs/internal/notes.md)"),
        ("[w](https://example.com/a.md)", "[w](https://example.com/a.md)"),
        ("[a](#local)", "[a](#local)"),
        ("[s](/abs.md)", "[s](/abs.md)"),
        ("![img](../../missing.png)", "![img](../../missing.png)"),
        ("[up](../../../outside.md)", "[up](../../../outside.md)"),
    ],
    ids=[
        "site-page", "site-page-with-fragment", "site-page-up", "repo-file",
        "repo-file-with-fragment", "docs-file-not-on-site", "excluded-counts-as-absent",
        "external", "anchor-only", "absolute", "image", "outside-repo",
    ],
)
def test_links_to_files_not_on_the_site_go_to_github(tmp_path, link, expected):
    assert _markdown(tmp_path, link) == expected


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (":class:<code>KorailClient</code>", "<code>KorailClient</code>"),
        (
            ":meth:<code>~korail_mobile_api.client.KorailClient.reserve</code>",
            "<code>reserve</code>",
        ),
        (":attr:<code>Name &lt;a.b.name&gt;</code>", "<code>Name</code>"),
        ("<p>.. code-block:: text</p>\n<pre>x</pre>", "<pre>x</pre>"),
        ("<code>plain</code>", "<code>plain</code>"),
    ],
    ids=["role", "tilde-keeps-last-name", "titled-role", "directive-line", "untouched"],
)
def test_rest_roles_and_directive_lines_are_cleaned(html, expected):
    assert hooks.on_page_content(html) == expected


def _page(src_uri: str, url: str, content: str) -> SimpleNamespace:
    page = SimpleNamespace(file=SimpleNamespace(src_uri=src_uri), url=url, content=content)
    page.file.page = page
    return page


def test_an_anchor_is_sent_to_the_one_other_page_that_has_it():
    home = _page(
        "index.md",
        "",
        '<h2 id="own">x</h2><a href="#own">a</a><a href="#elsewhere">b</a>'
        '<a href="#twice">c</a><a href="#nowhere">d</a>',
    )
    guide = _page("guide.md", "guide/", '<h2 id="elsewhere">y</h2><h2 id="twice">z</h2>')
    other = _page("other.md", "other/", '<h2 id="twice">w</h2>')
    files = [SimpleNamespace(page=p) for p in (home, guide, other)] + [
        SimpleNamespace(page=None)
    ]
    env = object()

    assert hooks.on_env(env, files=files) is env
    assert 'href="#own"' in home.content
    assert 'href="guide/#elsewhere"' in home.content
    # Two holders: no way to choose, so it is left as it was.
    assert 'href="#twice"' in home.content
    assert 'href="#nowhere"' in home.content


def _site(tmp_path: Path, index: str | None, *assets: str) -> SimpleNamespace:
    site = tmp_path / "site"
    site.mkdir()
    if index is not None:
        (site / "index.html").write_text(index, encoding="utf-8")
    for asset in assets:
        path = site / asset
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return SimpleNamespace(site_dir=str(site))


def test_a_site_without_an_index_page_fails_the_build(tmp_path):
    with pytest.raises(PluginError, match=r"index\.html"):
        hooks.on_post_build(config=_site(tmp_path, None))


def test_a_missing_local_asset_fails_the_build_and_is_named(tmp_path):
    index = (
        '<link href="assets/site.css"><script src="assets/app.js?v=1"></script>'
        '<a href="https://example.com/x.css">r</a><a href="#top">t</a>'
        '<img src="data:image/png;base64,AA">'
    )
    config = _site(tmp_path, index, "assets/site.css")
    with pytest.raises(PluginError, match=r"assets/app\.js\?v=1"):
        hooks.on_post_build(config=config)


def test_a_site_whose_local_assets_all_exist_passes(tmp_path):
    # Remote, in-page, data and mailto references are not files in site_dir and
    # must not be counted as missing ones.
    index = (
        '<link href="assets/site.css"><script src="assets/app.js?v=1"></script>'
        '<a href="https://example.com/x.css">r</a><a href="//cdn.example/y.js">c</a>'
        '<a href="#top">t</a><img src="data:image/png;base64,AA">'
        '<a href="mailto:someone@example.com">m</a>'
    )
    hooks.on_post_build(config=_site(tmp_path, index, "assets/site.css", "assets/app.js"))
