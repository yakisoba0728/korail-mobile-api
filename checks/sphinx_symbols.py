"""Sphinx 롤(:meth:/:func:/:class:/:attr:/:data:)이 가리키는 파이썬 심볼이
실재하는지 검사합니다.

자바 인용 탐지기는 이 종류를 구조적으로 못 봅니다 — 대상이 디컴파일이 아니라
**우리 자신의 코드**이기 때문입니다. 실제로 `_complete_login` 이라는, 존재한
적 없는 메서드 인용이 그렇게 살아남았습니다.
"""
import ast, re, pathlib, collections

ROLE_RE = re.compile(r":(?:meth|func|class|attr|data|exc|mod):`~?([A-Za-z_][\w.]*)`")

defined = set()
for f in pathlib.Path("src/korail_mobile_api").glob("*.py"):
    tree = ast.parse(f.read_text())
    mod = f.stem
    defined.add(mod); defined.add(f"korail_mobile_api.{mod}")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            defined.add(node.target.id)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name): defined.add(t.id)
                # ``self.pending = ...`` 같은 인스턴스 속성. 이걸 빼먹어서
                # 멀쩡한 :attr: 인용이 실패로 잡혔습니다.
                elif isinstance(t, ast.Attribute): defined.add(t.attr)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Attribute):
            defined.add(node.target.attr)

EXTERNAL = {"StrEnum","ValueError","httpx","TypeError","KeyError","Mapping"}

bad = collections.defaultdict(list)
total = 0
for f in sorted(pathlib.Path("src/korail_mobile_api").glob("*.py")):
    for i, line in enumerate(f.read_text().splitlines(), 1):
        for sym in ROLE_RE.findall(line):
            total += 1
            tail = sym.rsplit(".", 1)[-1]
            if tail in EXTERNAL or sym.split('.')[0] in EXTERNAL: continue
            if tail not in defined and sym not in defined:
                bad[sym].append(f"{f.name}:{i}")
print(f"Sphinx 심볼 인용 {total}건, 해석 실패 {sum(len(v) for v in bad)}건")
for sym, where in sorted(bad.items()):
    print(f"  {sym:44} {', '.join(where[:4])}")
