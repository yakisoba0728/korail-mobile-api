"""문서 빌드 전용 griffe 확장.

- 필드 바로 위의 ``#:`` 주석을 그 필드의 설명으로 씁니다.
- 문서에는 앱 소스 인용(``Foo.java:12-34`` 등)을 싣지 않습니다. 코드의 docstring 은 그대로 둡니다.
- Sphinx 표기(``:class:`Foo```)는 코드 표기로 바꾸고, 비공개 믹스인은 상속 목록에서 뺍니다.
"""

from __future__ import annotations

import ast
import re
from typing import Any

import griffe

_SOURCE = r"[\w$./]+\.(?:java|smali|kt)(?::[\d,\-–]+)?|[\w$./]+\.json:[\d,\-–]+"
_PAREN = re.compile(r"\s*\((?=[^()]*\.(?:java|smali|kt)\b|[^()]*\.json:\d)[^()]*\)")
_ROLE = re.compile(r":(?:class|attr|func|meth|data|mod|exc):`~?([^`]+)`")
_LABELLED = re.compile(
    r"(?:앱 근거|근거|라우트|바인딩|앱 호출|키 근거|메시지 근거|호출부|앱 선언)\s*:\s*(?:``)?"
    + _SOURCE
    + r"(?:``)?(?:\s*[,;]\s*(?:``)?"
    + _SOURCE
    + r"(?:``)?)*\s*\.?"
)
_BARE = re.compile(r"(?:``)?" + _SOURCE + r"(?:``)?(?:\s*[,;]\s*(?:``)?" + _SOURCE + r"(?:``)?)*")


def clean(text: str) -> str:
    text = _ROLE.sub(r"``\1``", text)
    text = _PAREN.sub("", text)
    text = _LABELLED.sub("", text)
    text = _BARE.sub("", text)
    text = re.sub(r"\(\s*[,;]?\s*\)", "", text)
    text = re.sub(r"[ \t]+([.,;])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"^[ \t]*[.,;][ \t]*", "", text, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


class DocsExtension(griffe.Extension):
    def on_attribute_instance(
        self, *, node: ast.AST | griffe.ObjectNode, attr: griffe.Attribute, **kwargs: Any
    ) -> None:
        if attr.docstring is not None or attr.lineno is None:
            return
        lines = (
            attr.parent.filepath.read_text(encoding="utf-8").splitlines()
            if attr.parent and attr.parent.filepath
            else []
        )
        comments: list[str] = []
        index = attr.lineno - 2
        while index >= 0 and lines[index].strip().startswith("#:"):
            comments.insert(0, lines[index].strip()[2:].strip())
            index -= 1
        if comments:
            attr.docstring = griffe.Docstring(" ".join(comments), parent=attr)

    def on_package(self, *, pkg: griffe.Module, **kwargs: Any) -> None:
        def walk(obj: griffe.Object | griffe.Alias) -> None:
            if isinstance(obj, griffe.Alias):
                return
            if obj.docstring is not None:
                obj.docstring.value = clean(obj.docstring.value)
            if isinstance(obj, griffe.Class):
                obj.bases = [base for base in obj.bases if not str(base).rsplit(".", 1)[-1].startswith("_")]
            for member in obj.members.values():
                walk(member)

        walk(pkg)
