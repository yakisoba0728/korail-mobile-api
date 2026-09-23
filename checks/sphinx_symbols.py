"""Sphinx 롤이 가리키는 파이썬 심볼이 **그 역할 그대로** 실재하는지 검사합니다.

대상 롤: ``:meth:`` ``:func:`` ``:class:`` ``:attr:`` ``:data:`` ``:exc:`` ``:mod:``.

디컴파일 인용 검사기는 이 종류를 구조적으로 못 봅니다 — 대상이 남의 코드가
아니라 우리 코드이기 때문입니다.

이 검사기의 이전 판은 모든 정의를 짧은 이름 하나의 집합에 쏟고 **끝 이름만**
비교했습니다. 그래서 없는 클래스의 멤버도 다른 클래스에 같은 이름이 있으면
통과했고, 함수에 ``:class:`` 를 붙여도, 지역 함수를 전역 ``:func:`` 로 불러도
통과했습니다(2026-09-23 외부 감사). 지금은 이렇게 봅니다:

* 모듈 이름으로 시작하면 **그 모듈 안에서만** 찾습니다. 그 모듈이
  ``from .a import Real`` (``as R`` 포함)로 들여온 이름도 그 모듈의 이름으로
  셉니다 — 종류는 원래 정의를 따라갑니다(최종 감사 C29).
* ``A.b`` 에서 ``A`` 가 우리 클래스가 아니면 **실패**입니다. 전역 끝 이름으로
  되돌아가지 않습니다.
* 이름의 정체는 **마지막 바인딩**입니다. ``Real = 1`` 뒤에 ``from .a import
  Real`` 이 오면 ``Real`` 은 a 의 클래스입니다(재감사 RC29).
* 역할이 심볼 종류와 맞아야 합니다(``:class:`` 는 클래스, ``:meth:`` 는 메서드…).
  ``:exc:`` 는 클래스이면서 MRO 에 ``BaseException`` 이 있어야 합니다. 평범한
  클래스는 실패입니다(C28). 우리 모듈이 재노출한 외부 이름(``from builtins
  import list as Plain``)도 import 해서 실제 객체를 보고, 예외가 아니면 실패,
  찾을 수 없으면 검사 불완전입니다(재감사 RC28 — 예전엔 건너뛰고 통과).
* 모듈 최상위 정의만 ``:func:``/``:class:`` 의 대상입니다. 함수 안의 지역 함수는
  아닙니다.
* 클래스 멤버는 클래스 본문의 정의와, 그 클래스 메서드 안의 ``self.x = …``
  뿐입니다. 다른 객체의 ``other.x = …`` 는 셈하지 않습니다.
* 상속 멤버는 파이썬과 같은 **C3 MRO** 순서로 찾습니다(재감사 NC07 — 예전엔
  LIFO 스택이라 ``C(A, B)`` 에서 B 를 먼저 봤습니다). 부모 이름은 **그 모듈의
  바인딩을 따라** 풉니다(``from .a import Parent``, ``from . import a`` +
  ``a.Parent``, 별칭, 내장 이름). 그 모듈에 정의도 import 도 안 된 부모는
  다른 모듈의 같은 이름 클래스로 대신하지 **않고** 해석 실패입니다(C30,
  재감사 RC30 — 파이썬에서도 ``NameError`` 입니다). ``import *`` 뒤에 숨었을
  수 있거나 점 표기가 아닌 부모 식이면 검사 불완전(exit 2)입니다.

한계: 모듈 없이 짧은 클래스 이름만 쓴 ``Config.x`` 는 같은 이름의 클래스가 여러
모듈에 있으면 **그중 하나라도** ``x`` 를 가지면 통과합니다 — 문맥 없이는 어느
``Config`` 인지 알 수 없습니다. 이 경우를 따로 세어 보고합니다.

종료 코드: 0 = 전부 해석됨, 1 = 해석 실패 있음, 2 = 검사 불완전(소스를 못 읽음,
구문 오류로 못 풂, 인용 0건, 검사기 자체의 예상 못 한 예외).

    python3 checks/sphinx_symbols.py [--root DIR]

``--root`` (또는 환경 변수 ``KORAIL_CHECK_ROOT``)는 저장소 루트를 바꿉니다.
기본은 현재 디렉터리이고, ``checks/selftest/run.py`` 가 가짜 트리에 씁니다.
"""
from __future__ import annotations

import ast
import builtins
import collections
import importlib
import os
import pathlib
import re
import sys
import traceback

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


def _builtin_exception(name: str) -> bool | None:
    """내장 이름이면 예외인지 여부, 내장 이름이 아니면 ``None``."""
    obj = getattr(builtins, name, None)
    if not isinstance(obj, type):
        return None
    return issubclass(obj, BaseException)


def _root_from_argv(argv: list[str]) -> pathlib.Path:
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root 뒤에 디렉터리가 필요합니다", file=sys.stderr)
            raise SystemExit(2)
        return pathlib.Path(argv[i + 1])
    return pathlib.Path(os.environ.get("KORAIL_CHECK_ROOT", "."))


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


def _dotted(node: ast.expr) -> str | None:
    """``a.b.C`` / ``C`` / ``Generic[T]`` 의 점 표기. 그 밖의 식은 ``None``."""
    if isinstance(node, ast.Subscript):
        node = node.value
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


#: import 해석 결과. ("mod", 모듈) / ("sym", 모듈, 이름) / ("ext", 점 표기)
Target = tuple

_MISSING = object()


def _import_object(dotted: str):
    """외부 점 표기 ``dotted`` 가 가리키는 실제 객체. 못 찾으면 ``_MISSING``.

    가장 긴 import 가능한 모듈 접두사를 import 하고 나머지는 속성으로 따라갑니다.
    어떤 접두사도 모듈이 아니면 내장 이름으로 봅니다(``list`` → ``builtins.list``)."""
    parts = dotted.split(".")
    for i in range(len(parts), 0, -1):
        try:
            obj = importlib.import_module(".".join(parts[:i]))
        except Exception:
            continue
        for attr in parts[i:]:
            obj = getattr(obj, attr, _MISSING)
            if obj is _MISSING:
                return _MISSING
        return obj
    obj = getattr(builtins, parts[0], _MISSING)
    for attr in parts[1:]:
        if obj is _MISSING:
            break
        obj = getattr(obj, attr, _MISSING)
    return obj


def _external_is_exception(dotted: str) -> bool | None:
    """외부 이름이 예외 계열인가. import 해서 **실제 객체**를 봅니다.
    찾을 수 없으면 ``None``(확인 불가 — 통과가 아닙니다)."""
    obj = _import_object(dotted)
    if obj is _MISSING:
        return None
    return isinstance(obj, type) and issubclass(obj, BaseException)


class Unknown(Exception):
    """정적으로 판정할 수 없음(검사 불완전, exit 2)."""


class Broken(Exception):
    """파이썬에서도 성립하지 않는 상속(정의 안 된 부모, 클래스 아닌 부모,
    순환, C3 모순). 이런 클래스의 멤버·예외 인용은 해석 실패입니다."""


class Index:
    def __init__(self) -> None:
        self.modules: set[str] = set()
        #: 모듈 -> {최상위 정의 이름: 종류}. **마지막 바인딩**이 import 이면 여기 없습니다.
        self.toplevel: dict[str, dict[str, str]] = collections.defaultdict(dict)
        #: 모듈 -> {지역 이름: (level, from 모듈 또는 None, 원래 이름, is_import)}.
        #: **마지막 바인딩**이 정의·대입이면 여기 없습니다.
        self.imports: dict[str, dict[str, tuple]] = collections.defaultdict(dict)
        #: ``from x import *`` 가 있는 모듈 — 거기서 못 푼 이름은 판정 불가입니다.
        self.star: set[str] = set()
        #: (모듈, 클래스) -> {멤버 이름: 종류}
        self.members: dict[tuple[str, str], dict[str, str]] = {}
        #: (모듈, 클래스) -> 부모 식의 점 표기(점 표기가 아닌 식은 None)
        self.bases: dict[tuple[str, str], list[str | None]] = {}
        #: 짧은 클래스 이름 -> [(모듈, 클래스)]
        self.by_name: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
        self._mro: dict[tuple[str, str], list[tuple]] = {}
        #: 외부 MRO 노드 -> 실제 객체(못 찾으면 _MISSING)
        self._ext_obj: dict[tuple, object] = {}

    # -- 색인 ---------------------------------------------------------------

    def add_module(self, mod: str, tree: ast.Module) -> None:
        """최상위 바인딩을 **소스 순서대로** 적용합니다. 파이썬처럼 같은 이름의
        **마지막** 바인딩이 이깁니다 — ``Real = 1`` 뒤의 ``from .a import Real``
        은 import 입니다(재감사 RC29; 예전엔 정의·대입이 늘 import 를 이겼습니다).
        ``if``/``try`` 안의 바인딩도 셉니다. ``try`` 는 예외 처리기를 먼저,
        정상 경로(본문·else·finally)를 나중에 적용합니다 — 정상 경로가 이깁니다."""
        self.modules.add(mod)
        top = self.toplevel[mod]
        imports = self.imports[mod]
        classes: dict[str, ast.ClassDef] = {}

        def bind_def(name: str, kind: str, node: ast.ClassDef | None = None) -> None:
            imports.pop(name, None)
            classes.pop(name, None)
            top[name] = kind
            if node is not None:
                classes[name] = node

        def bind_import(local: str, entry: tuple) -> None:
            top.pop(local, None)
            classes.pop(local, None)
            imports[local] = entry

        def walk(body: list[ast.stmt]) -> None:
            for node in body:
                if isinstance(node, ast.ClassDef):
                    bind_def(node.name, "class", node)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    bind_def(node.name, "function")
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    bind_def(node.target.id, "data")
                elif isinstance(node, ast.Assign):
                    for t in node.targets:
                        if isinstance(t, ast.Name):
                            bind_def(t.id, "data")
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            self.star.add(mod)
                            continue
                        local = alias.asname or alias.name
                        bind_import(local, (node.level, node.module, alias.name, False))
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.asname:
                            bind_import(alias.asname, (0, None, alias.name, True))
                        else:
                            head = alias.name.split(".", 1)[0]
                            bind_import(head, (0, None, head, True))
                elif isinstance(node, ast.If):
                    walk(node.body)
                    walk(node.orelse)
                elif isinstance(node, ast.Try):
                    for handler in node.handlers:
                        walk(handler.body)
                    for part in (node.body, node.orelse, node.finalbody):
                        walk(part)

        walk(tree.body)
        # 뒤 바인딩에 가려진 클래스는 ``mod.Name`` 으로 닿지 않으므로 색인하지 않습니다.
        for node in classes.values():
            self._add_class(mod, node)

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
        self.bases[key] = [_dotted(b) for b in node.bases]
        self.by_name[node.name].append(key)

    # -- import 따라가기 -----------------------------------------------------

    def _import_target(self, mod: str, local: str) -> Target | None:
        """``mod`` 의 지역 이름 ``local`` 이 import 로 가리키는 곳."""
        entry = self.imports[mod].get(local)
        if entry is None:
            return None
        level, frm, name, is_import = entry
        if is_import:  # ``import x.y as z`` / ``import x``
            if name == PACKAGE:
                return ("mod", "__init__")
            if name.startswith(PACKAGE + "."):
                sub = name[len(PACKAGE) + 1:]
                return ("mod", sub) if sub in self.modules else None
            return ("ext", name)
        if level == 1 or (level == 0 and frm and (frm == PACKAGE or frm.startswith(PACKAGE + "."))):
            if level == 1:
                pkgmod = frm or ""
            else:
                pkgmod = "" if frm == PACKAGE else frm[len(PACKAGE) + 1:]
            if pkgmod == "":  # ``from . import a`` / ``from korail_mobile_api import X``
                if name in self.modules and name != "__init__":
                    return ("mod", name)
                return ("sym", "__init__", name)
            if pkgmod in self.modules:
                return ("sym", pkgmod, name)
            return None  # 패키지 안인데 그런 모듈이 없습니다.
        if level > 1:
            return None  # 패키지 밖 상대 import — 우리 트리가 아닙니다.
        return ("ext", f"{frm}.{name}" if frm else name)

    def lookup(self, mod: str, name: str, _seen: frozenset = frozenset()) -> Target | None:
        """``mod.name`` 의 정체. 재노출을 원래 정의까지 따라갑니다.

        반환: ("def", 모듈, 이름, 종류) / ("mod", 모듈) / ("ext", 점 표기) / None
        """
        if (mod, name) in _seen or mod not in self.modules:
            return None
        kind = self.toplevel[mod].get(name)
        if kind is not None:
            return ("def", mod, name, kind)
        target = self._import_target(mod, name)
        if target is None:
            return None
        if target[0] == "sym":
            return self.lookup(target[1], target[2], _seen | {(mod, name)})
        return target

    def _resolve_base(self, mod: str, expr: str | None) -> tuple:
        """부모 식 ``expr`` 을 ``mod`` 의 바인딩 문맥에서 풉니다.

        반환: ("cls", 키) / ("ext", 점 표기). 그 모듈에 정의도 import 도 안 된
        이름은 **다른 모듈의 같은 이름 클래스로 대신하지 않습니다**(재감사 RC30;
        예전엔 전역에서 이름으로 찾아 "느슨함" 으로 세고 통과시켰습니다). 파이썬
        에서도 ``NameError`` 이므로 ``Broken`` 입니다. ``import *`` 뒤에 숨었을
        수 있거나 점 표기가 아닌 식이면 ``Unknown``."""
        if expr is None:
            raise Unknown(f"{mod}: 점 표기가 아닌 부모 식")
        parts = expr.split(".")
        head = self.lookup(mod, parts[0])
        scope, rest = mod, parts[1:]
        while head is not None and head[0] == "mod" and rest:
            scope = head[1]
            head = self.lookup(head[1], rest[0])
            rest = rest[1:]
        if head is not None and not rest:
            if head[0] == "def" and head[3] == "class":
                return ("cls", (head[1], head[2]))
            if head[0] == "ext":
                return ("ext", head[1])
            raise Broken(f"{mod}: 부모 {expr} 는 클래스가 아닙니다")
        if head is not None and head[0] == "ext":
            return ("ext", ".".join([head[1], *rest]))
        if (
            head is None
            and len(parts) == 1
            and parts[0] not in self.imports[mod]
            and hasattr(builtins, parts[0])
        ):
            return ("ext", f"builtins.{parts[0]}")
        if head is None and scope in self.star:
            raise Unknown(f"{mod}: 부모 {expr} 가 import * 뒤에 있을 수 있습니다")
        raise Broken(f"{mod}: 부모 {expr} 가 그 모듈에 정의·import 되어 있지 않습니다")

    def _ext_mro(self, dotted: str) -> list[tuple]:
        """외부 부모의 선형화. import 되면 실제 ``__mro__``, 아니면 그 한 노드."""
        obj = _import_object(dotted)
        if isinstance(obj, type):
            out = []
            for c in obj.__mro__:
                node = ("ext", f"{c.__module__}.{c.__qualname__}")
                self._ext_obj[node] = c
                out.append(node)
            return out
        node = ("ext", dotted)
        self._ext_obj[node] = obj
        return [node]

    def mro(self, key: tuple[str, str], _visiting: frozenset = frozenset()) -> list[tuple]:
        """파이썬과 같은 C3 선형화(재감사 NC07 — 예전엔 LIFO 스택이라
        ``C(A, B)`` 에서 B 를 먼저 봤습니다). 노드: ("cls", 키) / ("ext", 이름).
        풀 수 없으면 ``Unknown``, 파이썬도 거부할 상속이면 ``Broken``."""
        if key in self._mro:
            return self._mro[key]
        if key in _visiting:
            raise Broken(f"{key[0]}.{key[1]}: 순환 상속")
        if key not in self.members:
            raise Broken(f"{key[0]}.{key[1]}: 클래스가 아닙니다")
        seqs: list[list[tuple]] = []
        direct: list[tuple] = []
        for expr in self.bases.get(key, []):
            kind, value = self._resolve_base(key[0], expr)
            lin = self.mro(value, _visiting | {key}) if kind == "cls" else self._ext_mro(value)
            seqs.append(list(lin))
            direct.append(lin[0])
        seqs.append(direct)
        result = [("cls", key)]
        while True:
            seqs = [s for s in seqs if s]
            if not seqs:
                break
            for s in seqs:
                head = s[0]
                if not any(head in t[1:] for t in seqs):
                    break
            else:
                raise Broken(f"{key[0]}.{key[1]}: MRO 를 만들 수 없습니다(C3 모순)")
            result.append(head)
            seqs = [t[1:] if t[0] == head else t for t in seqs]
        self._mro[key] = result
        return result

    def member_kind(self, key: tuple[str, str], name: str) -> str | None:
        """MRO 순서로 처음 만나는 정의의 종류. 멤버는 우리 클래스 것만 압니다.
        ``Unknown`` 은 그대로 올리고, ``Broken`` 이면 None(해석 실패)."""
        try:
            order = self.mro(key)
        except Broken:
            return None
        for node in order:
            if node[0] == "cls":
                kind = self.members[node[1]].get(name)
                if kind is not None:
                    return kind
        return None

    def is_exception(self, key: tuple[str, str]) -> bool | None:
        """예외 계열인가 — None 은 확인 불가(외부 부모를 못 찾음, import * 등)."""
        try:
            order = self.mro(key)
        except Unknown:
            return None
        except Broken:
            return False
        unknown = False
        for node in order:
            if node[0] != "ext":
                continue
            obj = self._ext_obj.get(node, _MISSING)
            if obj is _MISSING:
                unknown = True
            elif isinstance(obj, type) and issubclass(obj, BaseException):
                return True
        return None if unknown else False


class Resolution:
    """``kinds``: None = 해석 실패, 빈 집합 = 검사 대상 아님(외부 이름).
    ``classes``: 클래스로 풀렸다면 그 키들. ``ambiguous``: 이름으로만 풀었는가.
    ``external``: 우리 모듈이 재노출한 외부 이름(``:exc:`` 는 실제 객체를
    확인합니다). ``unknown``: 판정 불가 사유(검사 불완전)."""

    def __init__(self, kinds, ambiguous=False, classes=(), external=None, unknown=None):
        self.kinds = kinds
        self.ambiguous = ambiguous
        self.classes = list(classes)
        self.external = external
        self.unknown = unknown


def resolve(index: Index, sym: str) -> Resolution:
    if sym.startswith(PACKAGE + "."):
        sym = sym[len(PACKAGE) + 1:]
    elif sym == PACKAGE:
        return Resolution({"module"})
    parts = sym.split(".")
    if parts[0] in EXTERNAL_ROOTS or sym in EXTERNAL_NAMES:
        return Resolution(set())

    if parts[0] in index.modules:
        target: Target | None = ("mod", parts[0])
        rest = parts[1:]
        while target is not None and target[0] == "mod" and rest:
            target = index.lookup(target[1], rest[0])
            rest = rest[1:]
        if target is None:
            return Resolution(None)
        if target[0] == "ext":
            # 외부 이름의 재노출. 종류는 따지지 않지만 ``:exc:`` 는 main 에서
            # 실제 객체로 확인합니다(재감사 RC28 — 예전엔 그냥 건너뛰었습니다).
            return Resolution(set(), external=".".join([target[1], *rest]))
        if target[0] == "mod":
            return Resolution({"module"}) if not rest else Resolution(None)
        _, mod, name, kind = target
        if not rest:
            return Resolution({kind}, classes=[(mod, name)] if kind == "class" else [])
        if len(rest) == 1 and kind == "class":
            try:
                member = index.member_kind((mod, name), rest[0])
            except Unknown as why:
                return Resolution(None, unknown=str(why))
            return Resolution({member} if member else None)
        return Resolution(None)

    if len(parts) == 1:
        kinds = {
            top[parts[0]] for top in index.toplevel.values() if parts[0] in top
        }
        for members in index.members.values():
            if parts[0] in members:
                kinds.add(members[parts[0]])
        classes = index.by_name.get(parts[0], [])
        return Resolution(kinds or None, len(classes) > 1, classes)

    if len(parts) == 2:
        candidates = index.by_name.get(parts[0], [])
        if not candidates:
            # 소유 클래스가 우리 코드에 없습니다. 끝 이름으로 되돌아가지 않습니다.
            return Resolution(None)
        kinds: set[str] = set()
        unknown = None
        for key in candidates:
            try:
                member = index.member_kind(key, parts[1])
            except Unknown as why:
                unknown = str(why)
                continue
            if member is not None:
                kinds.add(member)
        if not kinds and unknown:
            return Resolution(None, unknown=unknown)
        return Resolution(kinds or None, len(candidates) > 1)

    return Resolution(None)


def main(argv: list[str]) -> int:
    root = _root_from_argv(argv)
    src = root / "src" / PACKAGE
    incomplete: list[str] = []
    files = list(_source_files(src, incomplete))
    index = Index()
    for path, text in files:
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as error:
            # 이 모듈의 정의를 모르면, 이 모듈을 가리키는 인용의 성패를 알 수
            # 없습니다. 실패로 세지 않고 검사 불완전으로 끝냅니다(C31).
            incomplete.append(f"{path.name}:{error.lineno} (SyntaxError: {error.msg})")
            continue
        index.add_module(path.stem, tree)

    total = 0
    ambiguous = 0
    unverifiable: list[str] = []
    bad: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for path, text in files:
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in ROLE_RE.finditer(line):
                role, sym = m.group("role"), m.group("sym")
                where = f"{path.name}:{lineno}"
                total += 1
                res = resolve(index, sym)
                if res.unknown:
                    unverifiable.append(f":{role}:`{sym}` {where} ({res.unknown})")
                    continue
                if res.kinds is not None and not res.kinds:
                    # 외부 이름. ``:exc:`` 이면 그래도 예외여야 합니다.
                    if role != "exc":
                        continue
                    if res.external is not None:
                        # 우리 모듈이 재노출한 외부 이름 — 실제 객체를 봅니다(RC28).
                        verdict = _external_is_exception(res.external)
                    else:
                        verdict = _builtin_exception(sym.rsplit(".", 1)[-1])
                        if verdict is None:
                            continue  # EXTERNAL_ROOTS 아래 — 검사 대상 아님
                    if verdict is None:
                        unverifiable.append(f":exc:`{sym}` {where} ({res.external} 를 못 찾음)")
                    elif not verdict:
                        bad[("exc≠non-exception", sym)].append(where)
                    continue
                ambiguous += res.ambiguous
                if res.kinds is None:
                    bad[(role, sym)].append(where)
                    continue
                if not res.kinds & ROLE_KINDS[role]:
                    bad[(f"{role}≠{'/'.join(sorted(res.kinds))}", sym)].append(where)
                    continue
                if role == "exc":
                    verdicts = []
                    for key in res.classes:
                        verdicts.append(index.is_exception(key))
                    if any(v is True for v in verdicts):
                        continue
                    if any(v is None for v in verdicts):
                        unverifiable.append(f":exc:`{sym}` {where}")
                    else:
                        bad[("exc≠non-exception", sym)].append(where)

    failures = sum(len(where) for where in bad.values())
    print(
        f"Sphinx 심볼 인용 {total}건, 해석 실패 {failures}건"
        f" (이름만으로 풀어 느슨하게 통과: {ambiguous}건)"
    )
    for (role, sym), where in sorted(bad.items()):
        print(f"  :{role}:`{sym}`  {', '.join(where[:4])}")
    if unverifiable:
        incomplete.append("판정 불가: " + ", ".join(unverifiable))
    if incomplete:
        print("검사 불완전 —", "; ".join(incomplete))
        return 2
    if total == 0:
        print("심볼 인용을 하나도 못 찾았습니다 — 저장소 루트에서 실행했습니까?")
        return 2
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception:
        # 검사기 자신이 죽었으면 검사가 끝난 것이 아닙니다. traceback 의
        # exit 1 을 "실패 발견" 과 구별할 수 없으므로 2 로 끝냅니다.
        traceback.print_exc()
        print("검사 불완전 — 검사기 내부 오류", file=sys.stderr)
        code = 2
    sys.exit(code)
