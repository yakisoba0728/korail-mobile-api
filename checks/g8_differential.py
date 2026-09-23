"""G8 차등 검사 — 1.1.1 wheel 이 받던 응답을 지금 파서가 거절하는지 봅니다.

기준은 고정된 wheel ``korail_mobile_api-1.1.1-py3-none-any.whl`` 입니다
(``analysis/reports/7.0.6-additions/dist/``). 두 버전을 **한 프로세스에서**
나란히 import 합니다 — wheel 은 임시 폴더에 풀어 패키지 이름을
``korail_mobile_api_g8_wheel`` 로 바꿔 두므로 현재 ``src`` 의
``korail_mobile_api`` 와 모듈이 섞이지 않습니다(wheel 안의 import 는 전부
상대 import 입니다).

입력은 합성값뿐이고 네트워크를 쓰지 않습니다.

1. 두 버전의 ``read_parsers``/``mutation_parsers`` 에 **같은 이름으로** 있는
   ``parse_*`` 함수를 모읍니다. 인자가 ``BaseKorailResponse`` 인 것은 각
   버전의 ``BaseKorailResponse.from_raw`` 로 감쌉니다.
2. 함수마다 키 후보는 두 버전 소스에서 그 함수가 (모듈 안에서 추이적으로)
   참조하는 문자열 상수입니다.
3. 봉투 ``{"strResult":"SUCC","h_msg_cd":"IRZ000001","h_msg_txt":"ok"}`` 에서
   출발해, 어느 한 버전이라도 **내려가 읽는** 키(리스트의 행 / 객체)를
   탐지해 중첩 위치를 만듭니다(깊이 ``MAX_DEPTH`` 까지). 탐지는 "빈 자식은 받는데
   이상한 값으로 채운 자식은 거절" 로 합니다.
4. 각 위치에 각 키 × 각 이상한 값(``True``, ``1.5``, ``[]``, ``{}``,
   ``None``, 정수, ``10**5000``, 문자열 …)을 넣고, 리스트 위치에는 객체가
   아닌 원소도 섞습니다. wheel 이 받았는데 지금 거절하면 회귀입니다.

종료 코드: 0 통과, 1 회귀 있음, 2 wheel 을 찾거나 불러오지 못함.

    python3 checks/g8_differential.py [--wheel PATH] [--src PATH]

``--src`` 는 검사할 트리를 바꿉니다(기본은 이 저장소의 ``src``). 검사기 자신이
회귀를 잡는지 확인할 때 — 예컨대 고치기 전 커밋의 ``src`` 를 풀어 넣으면 exit 1
이어야 합니다.
"""
from __future__ import annotations

import ast
import copy
import importlib
import inspect
import os
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
WHEEL_NAME = "korail_mobile_api-1.1.1-py3-none-any.whl"
WHEEL_REL = Path("analysis/reports/7.0.6-additions/dist") / WHEEL_NAME
WHEEL_PKG = "korail_mobile_api_g8_wheel"
MODULES = ("read_parsers", "mutation_parsers")
ENV = {"strResult": "SUCC", "h_msg_cd": "IRZ000001", "h_msg_txt": "ok"}
KEY_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,40}$")
MAX_DEPTH = 6

#: 새 필드든 기존 필드든 가리지 않고 던지는 값들. ``10**5000`` 은 파이썬의
#: 정수→문자열 자릿수 한도를 넘어 ``str()`` 이 ``ValueError`` 를 냅니다.
ODD: tuple[Any, ...] = (
    True, False, 1.5, [], {}, None, 7, 0, -1, 10**5000, "", "s", "7",
    [{}], [7], ["s"], {"a": 1}, {"a": []},
)
#: 리스트 위치에 섞는, 객체가 아닌 원소.
BAD_ELEMENTS: tuple[Any, ...] = (None, 7, "s", True, 1.5, [], [{}], 10**5000)

#: 1.1.1 에도 **있던** 필드를 그 뒤에 더 엄격하게 읽게 된 자리들 — 알고 있는
#: 기존 필드 정책 변경입니다. G8 은 "새로 모델링한 선택 필드" 만 대상이므로
#: 이것들은 G8 위반으로 세지 않지만, 숨기지도 않습니다: 매 실행마다 "허용" 으로
#: 사유와 함께 출력합니다. 적용 대상은 wheel 이 **같은 자리의 같은 키를
#: 읽던**(값에 따라 거절도 하던) 그룹뿐이고, 새 필드로 분류된 회귀에는 이
#: 목록이 먹지 않습니다. 이 목록을 늘리는 것은 "기존 필드 변경" 을 선언하는
#: 일이지 G8 회귀를 덮는 수단이 아닙니다.
ALLOWED: dict[tuple[str, str], str] = {
    ("parse_ticket_duplication_check_response", "rsvCnt"):
        "N03/D09: 1.1.1 은 7·\"7\" 을 int 7 로 돌려줬고, 지금은 7 을 거절하고"
        " \"7\" 을 str 로 돌려줍니다(의도적 형 변경, 동작 유지·설명만 정정)",
    ("parse_cart_list_response", "h_tk_cnt"):
        "기존 필드 형 변경: 1.1.1 은 int 로 강제 변환(정수 JSON 수용), 지금은"
        " CartInfo.java:51 의 String 선언대로 문자열만(read_models.CartItem.ticket_count)",
    ("parse_pass_menu_response", "afterDay"):
        "기존 필드 형 변경: 1.1.1 은 _optional_integer, 지금은 PassMenuOutItem.java:28"
        " 의 String 선언대로 문자열만(read_parsers._PASS_MENU_ITEM_FIELDS 주석)",
    ("parse_pbp_acceptance_specification_response", "psgTpDvNm"):
        "기존 필드 필수화: Seat.java:53-59 합성 생성자가 다섯 필드를 요구(W4)",
    ("parse_pbp_acceptance_specification_response", "psrmClCd"):
        "기존 필드 필수화: Seat.java:53-59 합성 생성자가 다섯 필드를 요구(W4)",
    ("parse_pbp_acceptance_specification_response", "psrmClNm"):
        "기존 필드 필수화: Seat.java:53-59 합성 생성자가 다섯 필드를 요구(W4)",
    ("parse_pbp_acceptance_specification_response", "seatNo"):
        "기존 필드 필수화: Seat.java:53-59 합성 생성자가 다섯 필드를 요구(W4)",
}


def _main_checkout() -> Path | None:
    """git worktree 안이면 본 checkout 경로(``analysis/`` 는 커밋되지 않음)."""
    dot_git = ROOT / ".git"
    if dot_git.is_file():
        text = dot_git.read_text(encoding="utf-8").strip()
        if text.startswith("gitdir:"):
            gitdir = Path(text.split(":", 1)[1].strip())
            if not gitdir.is_absolute():
                gitdir = (ROOT / gitdir).resolve()
            # <main>/.git/worktrees/<name>
            if gitdir.parent.name == "worktrees":
                return gitdir.parent.parent.parent
    return None


def find_wheel(argv: list[str]) -> Path | None:
    if "--wheel" in argv:
        index = argv.index("--wheel")
        return Path(argv[index + 1]) if index + 1 < len(argv) else None
    if os.environ.get("KORAIL_G8_WHEEL"):
        return Path(os.environ["KORAIL_G8_WHEEL"])
    candidates = [ROOT / WHEEL_REL]
    main = _main_checkout()
    if main is not None:
        candidates.append(main / WHEEL_REL)
    return next((c for c in candidates if c.is_file()), candidates[0])


def load_versions(
    wheel: Path, scratch: Path, src: Path = SRC
) -> dict[str, dict[str, Any]]:
    with zipfile.ZipFile(wheel) as archive:
        members = [n for n in archive.namelist() if n.startswith("korail_mobile_api/")]
        if not members:
            raise RuntimeError("wheel has no korail_mobile_api package")
        archive.extractall(scratch, members)
    shutil.move(str(scratch / "korail_mobile_api"), str(scratch / WHEEL_PKG))
    sys.path.insert(0, str(scratch))
    sys.path.insert(0, str(src))
    versions: dict[str, dict[str, Any]] = {}
    for label, package, source_dir in (
        ("wheel", WHEEL_PKG, scratch / WHEEL_PKG),
        ("current", "korail_mobile_api", src / "korail_mobile_api"),
    ):
        models = importlib.import_module(f"{package}.models")
        mods = {m: importlib.import_module(f"{package}.{m}") for m in MODULES}
        sources = {m: (source_dir / f"{m}.py").read_text(encoding="utf-8") for m in MODULES}
        versions[label] = {"base": models.BaseKorailResponse, "mods": mods, "src": sources}
    current_file = Path(versions["current"]["mods"]["read_parsers"].__file__).resolve()
    if src.resolve() not in current_file.parents:
        raise RuntimeError(f"current parsers imported from {current_file}, not src/")
    return versions


def _top_level(tree: ast.Module) -> dict[str, ast.AST]:
    nodes: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            nodes[node.name] = node
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    nodes[target.id] = node
    return nodes


def key_universe(source: str, function: str) -> set[str]:
    nodes = _top_level(ast.parse(source))
    seen: set[str] = set()
    todo = [function]
    keys: set[str] = set()
    while todo:
        name = todo.pop()
        if name in seen or name not in nodes:
            continue
        seen.add(name)
        for node in ast.walk(nodes[name]):
            if isinstance(node, ast.Name) and node.id in nodes:
                todo.append(node.id)
            elif (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and KEY_RE.match(node.value)
            ):
                keys.add(node.value)
    return keys


def make_caller(fn: Callable[..., Any], base: Any) -> Callable[[dict[str, Any]], bool] | None:
    params = list(inspect.signature(fn).parameters.values())
    required = [
        p for p in params
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    if len(required) != 1:
        return None
    annotation = str(required[0].annotation)
    wrap = "BaseKorailResponse" in annotation

    def call(payload: dict[str, Any]) -> bool:
        try:
            fn(base.from_raw(payload) if wrap else payload)
        except Exception:  # noqa: BLE001 — 어떤 예외든 "거절" 입니다.
            return False
        return True

    return call


# 위치: [(key, "list"|"map", 그 단계의 기본 자식)] — 마지막 자식에 값을 넣습니다.
Path_ = tuple[tuple[str, str, tuple[tuple[str, Any], ...]], ...]


def build(path: Path_, leaf: dict[str, Any], elements: list[Any] | None = None) -> dict[str, Any]:
    child: Any = leaf
    for depth in range(len(path) - 1, -1, -1):
        key, kind, _ = path[depth]
        if kind == "list":
            child = [child] + (list(elements) if elements and depth == len(path) - 1 else [])
        container = dict(path[depth - 1][2]) if depth > 0 else dict(ENV)
        container[key] = child
        child = container
    return copy.deepcopy(child if path else {**ENV, **leaf})


def discover(
    callers: list[Callable[[dict[str, Any]], bool]],
    universe: set[str],
) -> list[Path_]:
    """어느 한 버전이라도 내려가 읽는 위치들을 찾습니다."""
    probes = [
        {k: bad for k in universe}
        for bad in ([], "s", 1.5, {"a": []}, True, 7, 10**5000, [7], {})
    ]
    found: list[Path_] = [()]
    frontier: list[Path_] = [()]
    for _ in range(MAX_DEPTH):
        next_frontier: list[Path_] = []
        for parent in frontier:
            used = {step[0] for step in parent}
            for key in sorted(universe - used):
                for kind in ("list", "map"):
                    # 기본 자식: 두 버전이 **다** 받는 것을 우선합니다. 그래야 그
                    # 위치의 회귀를 기본 자식 탓이 아니라 넣은 키 탓으로 돌릴 수
                    # 있습니다. 둘 다 받는 것이 없으면 wheel 이 받는 것.
                    accepted: list[tuple[dict[str, Any], list[bool]]] = []
                    for candidate in ({}, {k: "1" for k in universe}):
                        path = parent + ((key, kind, tuple(candidate.items())),)
                        accepted.append(
                            (candidate, [call(build(path, candidate)) for call in callers])
                        )
                    base_child = next(
                        (c for c, oks in accepted if all(oks)),
                        next((c for c, oks in accepted if oks[0]),
                             next((c for c, oks in accepted if any(oks)), None)),
                    )
                    if base_child is None:
                        continue
                    path = parent + ((key, kind, tuple(base_child.items())),)
                    for call in callers:
                        if not call(build(path, base_child)):
                            continue
                        if any(not call(build(path, {**base_child, **p})) for p in probes):
                            found.append(path)
                            next_frontier.append(path)
                            break
        frontier = next_frontier
        if not frontier:
            break
    return found


def describe(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool) and value.bit_length() > 64:
        return f"<int {value.bit_length()} bits>"
    return repr(value)[:40]


def main(argv: list[str]) -> int:
    wheel = find_wheel(argv)
    if wheel is None or not wheel.is_file():
        print(f"wheel 없음: {wheel}")
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="g8_wheel_"))
    try:
        try:
            src = Path(argv[argv.index("--src") + 1]) if "--src" in argv else SRC
            versions = load_versions(wheel, scratch, src)
        except Exception as error:  # noqa: BLE001
            print(f"wheel 을 불러오지 못함: {type(error).__name__}: {error}")
            return 2
        return run(versions)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def run(versions: dict[str, dict[str, Any]]) -> int:
    wheel_v, current_v = versions["wheel"], versions["current"]
    #: (함수, 위치, 키) → 분류와 거절된 값들. 분류는 "wheel 이 그 위치의 그 키를
    #: 엄격하게 읽었는가" — 같은 자리에 던진 값 중 하나라도 wheel 이 거절했으면
    #: 1.1.1 에도 있던(읽던) 필드, 전부 받았으면 1.1.1 이 읽지 않던 필드입니다.
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    totals = {"functions": 0, "skipped": 0, "inputs": 0, "wheel_accepted": 0, "locations": 0}
    for module in MODULES:
        wmod, cmod = wheel_v["mods"][module], current_v["mods"][module]
        names = sorted(
            n for n, f in inspect.getmembers(wmod, inspect.isfunction)
            if n.startswith("parse_") and f.__module__ == wmod.__name__
            and callable(getattr(cmod, n, None))
        )
        for name in names:
            old = make_caller(getattr(wmod, name), wheel_v["base"])
            new = make_caller(getattr(cmod, name), current_v["base"])
            if old is None or new is None:
                totals["skipped"] += 1
                print(f"  건너뜀(시그니처): {module}.{name}")
                continue
            totals["functions"] += 1
            universe = key_universe(wheel_v["src"][module], name) | key_universe(
                current_v["src"][module], name
            )
            locations = discover([old, new], universe)
            totals["locations"] += len(locations)

            def batch(where: str, key: str, cases: list[tuple[str, dict[str, Any]]]) -> None:
                wheel_rejected_some = False
                failed: list[str] = []
                for label, payload in cases:
                    totals["inputs"] += 1
                    if not old(payload):
                        wheel_rejected_some = True
                        continue
                    totals["wheel_accepted"] += 1
                    if not new(payload):
                        failed.append(label)
                if failed:
                    groups[(f"{module}.{name}", where, key)] = {
                        "existing": wheel_rejected_some,
                        "values": failed,
                    }

            for path in locations:
                base_leaf = dict(path[-1][2]) if path else {}
                where = "/".join(f"{k}[]" if kind == "list" else k for k, kind, _ in path) or "."
                base_payload = build(path, base_leaf)
                if old(base_payload) and not new(base_payload):
                    # 기본 자식부터 지금 거절됩니다. 그 위의 키별 결과는 전부 이
                    # 탓이므로 키에 돌리지 않고 위치 하나로 보고합니다.
                    totals["inputs"] += 1
                    groups[(f"{module}.{name}", where, "<base>")] = {
                        "existing": True,
                        "values": [describe(base_leaf)],
                    }
                    continue
                for key in sorted(universe):
                    batch(where, key, [
                        (describe(value), build(path, {**base_leaf, key: value}))
                        for value in ODD
                    ])
                if path and path[-1][1] == "list":
                    cases = [
                        (f"+element {describe(e)}", build(path, base_leaf, [e]))
                        for e in BAD_ELEMENTS
                    ]
                    # 원소가 객체 하나만이 아니라 여럿일 때도.
                    cases.append(("x2", build(path, base_leaf, [base_leaf])))
                    batch(where, "<elements>", cases)

    def allowed_reason(group: tuple[str, str, str]) -> str | None:
        return ALLOWED.get((group[0].split(".")[1], group[2]))

    regressions = {
        g: v for g, v in groups.items()
        if not (v["existing"] and allowed_reason(g) is not None)
    }
    allowed = {g: v for g, v in groups.items() if g not in regressions}
    new_field = {g: v for g, v in regressions.items() if not v["existing"]}
    existing = {g: v for g, v in regressions.items() if v["existing"]}
    print(
        f"함수 {totals['functions']} (건너뜀 {totals['skipped']}), 위치 {totals['locations']}, "
        f"입력 {totals['inputs']}, wheel 수용 {totals['wheel_accepted']}"
    )
    print(
        f"회귀: 새 필드 {len(new_field)}군 / 기존 필드 좁힘 {len(existing)}군 "
        f"(입력 {sum(len(v['values']) for v in regressions.values())}건), "
        f"허용된 기존 필드 변경 {len(allowed)}군"
    )
    for group, info in sorted(allowed.items()):
        function, where, key = group
        print(f"  허용 {function} @{where} {key}: {', '.join(info['values'][:6])}"
              f"  [{allowed_reason(group)}]")
    for label, table in (("새 필드", new_field), ("기존 필드 좁힘", existing)):
        for (function, where, key), info in sorted(table.items()):
            print(f"  {label} {function} @{where} {key}: {', '.join(info['values'][:6])}"
                  + (" …" if len(info["values"]) > 6 else ""))
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
