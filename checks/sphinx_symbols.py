"""Sphinx 롤이 가리키는 파이썬 심볼이 **그 역할 그대로** 실재하는지 검사합니다.

대상 롤: ``:meth:`` ``:func:`` ``:class:`` ``:attr:`` ``:data:`` ``:exc:`` ``:mod:``.

디컴파일 인용 검사기는 이 종류를 구조적으로 못 봅니다 — 대상이 남의 코드가
아니라 우리 코드이기 때문입니다.

이 검사기의 이전 판은 모든 정의를 짧은 이름 하나의 집합에 쏟고 **끝 이름만**
비교했습니다. 그래서 없는 클래스의 멤버도 다른 클래스에 같은 이름이 있으면
통과했고, 함수에 ``:class:`` 를 붙여도, 지역 함수를 전역 ``:func:`` 로 불러도
통과했습니다(2026-09-23 외부 감사). 지금은 이렇게 봅니다:

* 모듈 이름으로 시작하면 **그 모듈 안에서만** 찾습니다.
* ``A.b`` 에서 ``A`` 가 우리 클래스가 아니면 **실패**입니다. 전역 끝 이름으로
  되돌아가지 않습니다.
* 역할이 심볼 종류와 맞아야 합니다(``:class:`` 는 클래스, ``:meth:`` 는 메서드…).
* 모듈 최상위 정의만 ``:func:``/``:class:`` 의 대상입니다. 함수 안의 지역 함수는
  아닙니다.
* 클래스 멤버는 클래스 본문의 정의와, 그 클래스 메서드 안의 ``self.x = …``
  뿐입니다. 다른 객체의 ``other.x = …`` 는 셈하지 않습니다.
* 상속은 부모를 따라 올라갑니다. ``Base as Parent`` 같은 import 별칭과
  ``base.Base`` 같은 속성형 부모도 풉니다.

한계: 모듈 없이 짧은 클래스 이름만 쓴 ``Config.x`` 는 같은 이름의 클래스가 여러
모듈에 있으면 **그중 하나라도** ``x`` 를 가지면 통과합니다 — 문맥 없이는 어느
``Config`` 인지 알 수 없습니다. 이 경우를 따로 세어 보고합니다.

종료 코드: 0 = 전부 해석됨, 1 = 해석 실패 있음, 2 = 검사 불완전(소스를 못 읽음
또는 인용 0건).

    python3 checks/sphinx_symbols.py
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re
import sys

SRC = pathlib.Path("src/korail_mobile_api")
PACKAGE = "korail_mobile_api"

ROLE_RE = re.compile(
    r":(?P<role>meth|func|class|attr|data|exc|mod):`~?(?P<sym>[A-Za-z_][\w.]*)`"
)

#: 역할 -> 받아들이는 심볼 종류
ROLE_KINDS = {
    "class": {"class"},
    "exc": {"class"},
    "func": {"function"},
    "meth": {"method"},
    "attr": {"attribute", "data", "property"},
    "data": {"data", "attribute"},
    "mod": {"module"},
}

#: 우리 코드가 아닌 첫 머리. 여기로 시작하면 검사 대상이 아닙니다.
EXTERNAL_ROOTS = {
    "httpx", "json", "re", "typing", "collections", "dataclasses", "urllib",
    "enum", "datetime", "pathlib", "abc", "functools", "itertools", "os",
    "sys", "hashlib", "base64", "hmac", "secrets", "time", "logging",
    "cryptography", "decimal", "contextlib", "traceback", "copy", "pickle",
}
EXTERNAL_NAMES = {
    "StrEnum", "IntEnum", "Enum", "ValueError", "TypeError", "KeyError",
    "Mapping", "Sequence", "Exception", "RuntimeError", "OSError",
    "UnicodeDecodeError", "UnicodeEncodeError", "RecursionError",
}


def _source_files(root: pathlib.Path, incomplete: list[str]):
    """읽을 수 있는 ``.py``. AppleDouble(``._*``)은 조용히 넘기고, 그 밖에 못
    읽는 파일은 **검사 불완전**으로 기록합니다 — 실제 소스를 못 읽고서 성공으로
    끝나면 안 됩니다."""
    for path in sorted(root.glob("*.py")):
        if path.name.startswith("._"):
            continue
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as error:
            incomplete.append(f"{path.name} ({type(error).__name__})")


def _is_property(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for dec in node.decorator_list:
        name = dec.id if isinstance(dec, ast.Name) else getattr(dec, "attr", "")
        if name in {"property", "cached_property"}:
            return True
    return False


class Index:
    def __init__(self) -> None:
        self.modules: set[str] = set()
        #: 모듈 -> {최상위 이름: 종류}
        self.toplevel: dict[str, dict[str, str]] = collections.defaultdict(dict)
        #: (모듈, 클래스) -> {멤버 이름: 종류}
        self.members: dict[tuple[str, str], dict[str, str]] = {}
        #: (모듈, 클래스) -> 부모 이름(별칭 풀기 전)
        self.bases: dict[tuple[str, str], list[str]] = {}
        #: 짧은 클래스 이름 -> [(모듈, 클래스)]
        self.by_name: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
        #: 모듈 -> {별칭: 원래 이름}
        self.aliases: dict[str, dict[str, str]] = collections.defaultdict(dict)

    def add_module(self, mod: str, tree: ast.Module) -> None:
        self.modules.add(mod)
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.toplevel[mod][node.name] = "class"
                self._add_class(mod, node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.toplevel[mod][node.name] = "function"
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                self.toplevel[mod][node.target.id] = "data"
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        self.toplevel[mod][t.id] = "data"
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.asname:
                        self.aliases[mod][alias.asname] = alias.name

    def _add_class(self, mod: str, node: ast.ClassDef) -> None:
        key = (mod, node.name)
        members: dict[str, str] = {}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                members[item.name] = "property" if _is_property(item) else "method"
                for sub in ast.walk(item):
                    targets: list[ast.expr] = []
                    if isinstance(sub, ast.Assign):
                        targets = list(sub.targets)
                    elif isinstance(sub, ast.AnnAssign):
                        targets = [sub.target]
                    for t in targets:
                        # ``self.x`` 만. ``other.x = …`` 는 이 클래스의 멤버가 아닙니다.
                        if (
                            isinstance(t, ast.Attribute)
                            and isinstance(t.value, ast.Name)
                            and t.value.id == "self"
                        ):
                            members.setdefault(t.attr, "attribute")
            elif isinstance(item, ast.ClassDef):
                members[item.name] = "class"
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                members[item.target.id] = "attribute"
            elif isinstance(item, ast.Assign):
                for t in item.targets:
                    if isinstance(t, ast.Name):
                        members[t.id] = "attribute"
        self.members[key] = members
        bases: list[str] = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
        self.bases[key] = bases
        self.by_name[node.name].append(key)

    def _resolve_base(self, mod: str, name: str) -> list[tuple[str, str]]:
        original = self.aliases[mod].get(name, name)
        same_module = (mod, original)
        if same_module in self.members:
            return [same_module]
        return list(self.by_name.get(original, []))

    def member_kind(self, key: tuple[str, str], name: str) -> str | None:
        seen: set[tuple[str, str]] = set()
        stack = [key]
        while stack:
            current = stack.pop()
            if current in seen or current not in self.members:
                continue
            seen.add(current)
            kind = self.members[current].get(name)
            if kind is not None:
                return kind
            for base in self.bases.get(current, []):
                stack.extend(self._resolve_base(current[0], base))
        return None


def resolve(index: Index, sym: str) -> tuple[set[str] | None, bool]:
    """``sym`` 의 가능한 종류 집합과 '짧은 이름이라 모호함' 여부.

    ``None`` 은 해석 실패, 빈 집합은 검사 대상 아님(외부 이름).
    """
    if sym.startswith(PACKAGE + "."):
        sym = sym[len(PACKAGE) + 1:]
    elif sym == PACKAGE:
        return {"module"}, False
    parts = sym.split(".")
    if parts[0] in EXTERNAL_ROOTS or sym in EXTERNAL_NAMES:
        return set(), False

    if parts[0] in index.modules:
        mod, rest = parts[0], parts[1:]
        if not rest:
            return {"module"}, False
        top = index.toplevel[mod]
        if len(rest) == 1:
            kind = top.get(rest[0])
            return ({kind} if kind else None), False
        if len(rest) == 2 and top.get(rest[0]) == "class":
            kind = index.member_kind((mod, rest[0]), rest[1])
            return ({kind} if kind else None), False
        return None, False

    if len(parts) == 1:
        kinds = {
            top[parts[0]] for top in index.toplevel.values() if parts[0] in top
        }
        for members in index.members.values():
            if parts[0] in members:
                kinds.add(members[parts[0]])
        return (kinds or None), False

    if len(parts) == 2:
        candidates = index.by_name.get(parts[0], [])
        if not candidates:
            # 소유 클래스가 우리 코드에 없습니다. 끝 이름으로 되돌아가지 않습니다.
            return None, False
        kinds = {
            k for key in candidates
            if (k := index.member_kind(key, parts[1])) is not None
        }
        return (kinds or None), len(candidates) > 1

    return None, False


def main() -> int:
    incomplete: list[str] = []
    files = list(_source_files(SRC, incomplete))
    index = Index()
    for path, text in files:
        index.add_module(path.stem, ast.parse(text))

    total = 0
    ambiguous = 0
    bad: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in ROLE_RE.finditer(line):
                role, sym = m.group("role"), m.group("sym")
                total += 1
                kinds, is_ambiguous = resolve(index, sym)
                if kinds is not None and not kinds:
                    continue  # 외부 이름
                ambiguous += is_ambiguous
                if kinds is None:
                    bad[(role, sym)].append(f"{path.name}:{lineno}")
                elif not kinds & ROLE_KINDS[role]:
                    bad[(f"{role}≠{'/'.join(sorted(kinds))}", sym)].append(
                        f"{path.name}:{lineno}"
                    )

    failures = sum(len(where) for where in bad.values())
    print(
        f"Sphinx 심볼 인용 {total}건, 해석 실패 {failures}건"
        f" (짧은 클래스 이름이 모호해 느슨하게 통과: {ambiguous}건)"
    )
    for (role, sym), where in sorted(bad.items()):
        print(f"  :{role}:`{sym}`  {', '.join(where[:4])}")
    if incomplete:
        print("검사 불완전 — 읽지 못한 소스:", ", ".join(incomplete))
        return 2
    if total == 0:
        print("심볼 인용을 하나도 못 찾았습니다 — 저장소 루트에서 실행했습니까?")
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
