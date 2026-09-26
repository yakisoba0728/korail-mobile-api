"""문서(docs/)가 코드와 어긋나지 않는지 확인합니다.

- API 페이지의 시그니처 블록이 소스의 시그니처와 같고, 공개 메서드가 모두 한 번씩 문서화돼 있어야 합니다.
- 문서의 Python 예제는 문법이 맞아야 하고, 쓰는 import 이름과 ``client.<메서드>`` 가 공개 API 에 있어야 합니다.

docs/ 는 sdist 에 들어가지 않으므로 없으면 건너뜁니다.
"""

from __future__ import annotations

import ast
import pathlib
import re
import textwrap

import pytest

import korail_mobile_api

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CLIENT = ROOT / "src" / "korail_mobile_api" / "client.py"

pytestmark = pytest.mark.skipif(
    not DOCS.is_dir() or not CLIENT.is_file(), reason="docs/ is not shipped in the sdist"
)

_FENCE = re.compile(r"^([ \t]*)```python[^\n]*\n(.*?)^\1```", re.S | re.M)


def _param(arg: ast.arg, default: ast.expr | None) -> str:
    text = arg.arg
    if arg.annotation is not None:
        text += f": {ast.unparse(arg.annotation)}"
    if default is not None:
        text += f" = {ast.unparse(default)}" if arg.annotation is not None else f"={ast.unparse(default)}"
    return text


def _signature(fn: ast.FunctionDef) -> str:
    args = fn.args
    positional = args.posonlyargs + args.args
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    parts = [_param(a, d) for a, d in zip(positional, defaults) if a.arg != "self"]
    if args.vararg is not None:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")
    parts += [_param(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    if args.kwarg is not None:
        parts.append("**" + args.kwarg.arg)
    returns = f" -> {ast.unparse(fn.returns)}" if fn.returns is not None else ""
    return f"KorailClient.{fn.name}({', '.join(parts)}){returns}"


def _client_signatures() -> dict[str, str]:
    tree = ast.parse(CLIENT.read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "KorailClient")
    return {
        n.name: _signature(n) for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
    }


def _normalise(text: str) -> str:
    return re.sub(r"\s+", "", text).replace(",)", ")").replace('"', "'")


def _python_blocks() -> list[tuple[pathlib.Path, str]]:
    blocks = []
    for path in sorted(DOCS.rglob("*.md")):
        for match in _FENCE.finditer(path.read_text(encoding="utf-8")):
            blocks.append((path, textwrap.dedent(match.group(2))))
    return blocks


def _is_signature(block: str) -> bool:
    return block.lstrip().startswith("KorailClient.")


def test_every_public_method_has_one_signature_matching_the_source() -> None:
    expected = _client_signatures()
    seen: dict[str, pathlib.Path] = {}
    for path, block in _python_blocks():
        if not _is_signature(block):
            continue
        name = block.lstrip().split("(", 1)[0].removeprefix("KorailClient.")
        assert name in expected, f"{path.relative_to(ROOT)}: unknown method {name}"
        assert name not in seen, f"{name} is documented in both {seen[name]} and {path}"
        assert _normalise(block) == _normalise(expected[name]), (
            f"{path.relative_to(ROOT)}: signature of {name} differs from the source:\n{expected[name]}"
        )
        seen[name] = path.relative_to(ROOT)
    assert sorted(seen) == sorted(expected), f"undocumented: {sorted(set(expected) - set(seen))}"


def test_examples_compile_and_use_only_public_names() -> None:
    public_methods = set(_client_signatures())
    exported = set(korail_mobile_api.__all__)
    for path, block in _python_blocks():
        if _is_signature(block):
            continue
        where = path.relative_to(ROOT)
        tree = ast.parse(block, filename=str(where))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "korail_mobile_api":
                missing = [alias.name for alias in node.names if alias.name not in exported]
                assert not missing, f"{where}: not exported from korail_mobile_api: {missing}"
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("korail_mobile_api."):
                raise AssertionError(f"{where}: import from the package root instead of {node.module}")
        for name in re.findall(r"\bclient\.(\w+)\s*\(", block):
            assert name in public_methods, f"{where}: KorailClient has no public method {name}"
