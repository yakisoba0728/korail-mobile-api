"""Sphinx 롤(:meth:/:func:/:class:/:attr:/:data:)이 가리키는 파이썬 심볼이
실재하는지 검사합니다.

자바 인용 탐지기는 이 종류를 구조적으로 못 봅니다 — 대상이 디컴파일이 아니라
**우리 자신의 코드**이기 때문입니다. 실제로 `_complete_login` 이라는, 존재한
적 없는 메서드 인용이 그렇게 살아남았습니다.
"""
import ast, re, sys, pathlib, collections

ROLE_RE = re.compile(r":(?:meth|func|class|attr|data|exc|mod):`~?([A-Za-z_][\w.]*)`")

SRC = pathlib.Path("src/korail_mobile_api")

def _source_files(root: pathlib.Path):
    """읽을 수 있는 ``.py`` 만. 못 읽는 파일은 건너뛰고 알립니다.

    ``glob("*.py")`` 결과를 그대로 열었더니, 아카이브를 그대로 푼 환경에서
    macOS AppleDouble(``._foo.py``)을 만나 ``UnicodeDecodeError`` 로 **검사기
    자체가 죽었습니다**. 점검 도구가 환경 부산물 하나에 멈춰서는 안 됩니다
    (2026-09-23).
    """
    for path in sorted(root.glob("*.py")):
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as error:
            print(f"  건너뜀: {path.name} ({type(error).__name__})")


defined: set[str] = set()
#: 클래스 이름 -> 그 클래스가 가진 멤버 이름. 점 있는 인용(``A.b``)은 이쪽으로
#: 봅니다. 예전에는 모든 정의를 한 집합에 쏟고 **끝 이름만** 비교해서, 소유
#: 클래스가 아예 무시됐습니다 — 다른 클래스에 같은 이름이 있으면 통과했습니다.
members: dict[str, set[str]] = collections.defaultdict(set)
#: 클래스 -> 부모 클래스. ``raw`` 처럼 **상속받은** 멤버를 오탐하지 않으려면
#: 부모까지 올라가야 합니다. 이걸 빼먹고 돌렸더니 첫 실행에서 바로
#: ``CartAddResponse.raw`` 를 잘못 잡았습니다(2026-09-23 확인).
bases: dict[str, set[str]] = collections.defaultdict(set)


def _all_members(cls: str, seen: set[str] | None = None) -> set[str]:
    seen = seen or set()
    if cls in seen:
        return set()
    seen.add(cls)
    out = set(members.get(cls, ()))
    for parent in bases.get(cls, ()):
        out |= _all_members(parent, seen)
    return out



def _member_names(body: list[ast.stmt]) -> set[str]:
    names: set[str] = set()
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # ``__init__`` 안의 ``self.x = ...``
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Assign):
                        for t in sub.targets:
                            if isinstance(t, ast.Attribute):
                                names.add(t.attr)
                    elif isinstance(sub, ast.AnnAssign) and isinstance(
                        sub.target, ast.Attribute
                    ):
                        names.add(sub.target.attr)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


for f, text in _source_files(SRC):
    tree = ast.parse(text)
    defined.add(f.stem)
    defined.add(f"korail_mobile_api.{f.stem}")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    defined.add(t.id)
                # ``self.pending = ...`` 같은 인스턴스 속성.
                elif isinstance(t, ast.Attribute):
                    defined.add(t.attr)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute):
            defined.add(node.target.attr)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            members[node.name] |= _member_names(node.body)
            bases[node.name] |= {
                b.id for b in node.bases if isinstance(b, ast.Name)
            }

EXTERNAL = {"StrEnum","ValueError","httpx","TypeError","KeyError","Mapping"}

bad = collections.defaultdict(list)
total = 0
for f, text in _source_files(SRC):
    for i, line in enumerate(text.splitlines(), 1):
        for sym in ROLE_RE.findall(line):
            total += 1
            tail = sym.rsplit(".", 1)[-1]
            if tail in EXTERNAL or sym.split(".")[0] in EXTERNAL:
                continue
            owner = sym.rsplit(".", 2)[-2] if "." in sym else None
            if owner is not None and owner in members:
                # 소유 클래스를 아는 경우에는 **그 계보 안에서만** 찾습니다.
                if tail not in _all_members(owner):
                    bad[sym].append(f"{f.name}:{i}")
                continue
            if tail not in defined and sym not in defined:
                bad[sym].append(f"{f.name}:{i}")

# ``sum(len(v) for v in bad)`` 는 dict 를 돌면 **키**가 나오므로 심볼 문자열의
# 길이를 더하고 있었습니다. 실패 건수가 아니었습니다(2026-09-23 확인).
failures = sum(len(v) for v in bad.values())
print(f"Sphinx 심볼 인용 {total}건, 해석 실패 {failures}건")
for sym, where in sorted(bad.items()):
    print(f"  {sym:44} {', '.join(where[:4])}")
if total == 0:
    print("심볼 인용을 하나도 못 찾았습니다 — 저장소 루트에서 실행했습니까?")
    sys.exit(2)
sys.exit(1 if failures else 0)
