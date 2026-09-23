"""``sphinx_symbols.py`` 와 ``decompile_citations.py`` 자신의 회귀 시험.

최종 감사(C28–C35)가 이 두 검사기에서 거짓 통과·거짓 실패·traceback 을
찾아냈습니다. 그 탐침 픽스처를 임시 디렉터리에 그대로 짓고, 검사기를
``--root`` 로 그 트리에 돌려 **종료 코드**를 확인합니다. 고친 쪽(맞는 입력은
여전히 통과)도 함께 둡니다 — 거짓 통과를 막다가 거짓 실패를 만들면 안 됩니다.

종료 코드: 0 = 전부 기대대로, 1 = 기대와 다른 사례 있음, 2 = 시험 불완전
(검사기를 못 찾음, 시간 초과, 이 스크립트 자신의 예상 못 한 예외).

    python3 checks/selftest/run.py
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile
import traceback

HERE = pathlib.Path(__file__).resolve().parent
CHECKS = HERE.parent
SPHINX = CHECKS / "sphinx_symbols.py"
CITES = CHECKS / "decompile_citations.py"

PKG = "src/korail_mobile_api/"

#: 파일 값: 문자열 = 텍스트, bytes = 그대로, None = 끊긴 심볼릭 링크,
#: ("mode000", 텍스트) = 권한 없는 일반 파일.
CASES: list[dict] = [
    # -- C28 :exc: 는 예외 계열이어야 합니다 ------------------------------------
    dict(id="C28 plain class under :exc:", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Plain:\n    pass\n# :exc:`a.Plain`\n"}),
    dict(id="C28 builtin-derived exception", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class E(ValueError):\n    pass\n# :exc:`a.E`\n"}),
    dict(id="C28 transitive via re-exported base", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Base(Exception):\n    pass\n",
        PKG + "b.py": "from .a import Base as B\nclass E2(B):\n    pass\n# :exc:`b.E2`\n"}),
    dict(id="C28 plain class through plain parent", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Base:\n    pass\nclass E(Base):\n    pass\n# :exc:`E`\n"}),
    dict(id="C28 builtin non-exception under :exc:", checker=SPHINX, expect=1, files={
        PKG + "a.py": "def f(): pass\n# :func:`a.f` :exc:`dict`\n"}),
    # -- C29 재노출 ---------------------------------------------------------------
    dict(id="C29 from .a import Real", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Real:\n    def m(self): pass\n",
        PKG + "b.py": "from .a import Real\n# :class:`b.Real` :meth:`b.Real.m`\n"}),
    dict(id="C29 from .a import Real as R", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Real:\n    pass\n",
        PKG + "b.py": "from .a import Real as R\n# :class:`b.R`\n"}),
    dict(id="C29 re-export keeps original kind", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Real:\n    pass\n",
        PKG + "b.py": "from .a import Real\n# :func:`b.Real`\n"}),
    dict(id="C29 name not imported is still absent", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Real:\n    pass\n",
        PKG + "b.py": "from .a import Real\n# :class:`b.Other`\n"}),
    # -- C30 부모는 import 를 따라 풉니다 ------------------------------------------
    dict(id="C30 base from wrong same-named module", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Parent:\n    pass\n",
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "from .a import Parent\nclass Child(Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    dict(id="C30 base via from-import (right module)", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Parent:\n    pass\n",
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "from .b import Parent as P\nclass Child(P): pass\n# :meth:`c.Child.ghost`\n"}),
    dict(id="C30 base via module attribute", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Parent:\n    pass\n",
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "from . import b\nclass Child(b.Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    dict(id="C30 base via module attribute (wrong module)", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Parent:\n    pass\n",
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "from . import a\nclass Child(a.Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    dict(id="C30 unresolvable base is reported ambiguous", checker=SPHINX, expect=0,
         stdout_has="느슨하게 통과: 1건", files={
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "class Child(Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    # -- C31 구문 오류 / 못 읽는 소스 ---------------------------------------------
    dict(id="C31 SyntaxError is incomplete", checker=SPHINX, expect=2, no_traceback=True,
         stdout_has="a.py:2", files={PKG + "a.py": "# :func:`f`\ndef f(:\n"}),
    dict(id="sphinx undecodable source is incomplete", checker=SPHINX, expect=2, files={
        PKG + "a.py": b"\xff", PKG + "b.py": "def f(): pass\n# :func:`b.f`\n"}),
    dict(id="sphinx internal error is incomplete", checker=SPHINX, expect=2,
         inject=(
             "import ast\n_parse = ast.parse\n"
             "def boom(*a, **k):\n"
             "    if 'filename' in k: raise RuntimeError('injected')\n"
             "    return _parse(*a, **k)\n"
             "ast.parse = boom\n"),
         files={PKG + "a.py": "def f(): pass\n# :func:`a.f`\n"}),
    # -- C32 경로 구성 요소 단위 비교 ---------------------------------------------
    dict(id="C32 pkg/ does not match notpkg/", checker=CITES, expect=1, files={
        PKG + "a.py": "# pkg/TestCase.java:1\n",
        "analysis/notpkg/TestCase.java": "// not the cited path\n"}),
    dict(id="C32 pkg/ matches pkg/", checker=CITES, expect=0, files={
        PKG + "a.py": "# pkg/TestCase.java:1\n",
        "analysis/x/pkg/TestCase.java": "// line\n"}),
    dict(id="C32 extensionless stem matches pkg/", checker=CITES, expect=0, files={
        PKG + "a.py": "# pkg/TestCase:1\n",
        "analysis/x/pkg/TestCase.java": "// line\n"}),
    dict(id="C32 extensionless stem rejects notpkg/", checker=CITES, expect=1, files={
        PKG + "a.py": "# pkg/TestCase:1\n",
        "analysis/notpkg/TestCase.java": "// line\n"}),
    dict(id="C32 analysis/-rooted citation", checker=CITES, expect=0, files={
        PKG + "a.py": "# analysis/x/pkg/TestCase.java:1\n",
        "analysis/x/pkg/TestCase.java": "// line\n"}),
    # -- C33 면제는 그 인용의 문장에만 --------------------------------------------
    dict(id="C33 unrelated 'There is no' does not exempt", checker=CITES, expect=1, files={
        PKG + "a.py": "# 아래 클래스는 존재하고 정상입니다.\n"
                      "# There is no reason to doubt the implementation.\n"
                      "# MissingClass.java:1 implements this contract.\n"}),
    dict(id="C33 marker in previous sentence does not exempt", checker=CITES, expect=1, files={
        PKG + "a.py": "# The helper is absent from logs.\n"
                      "# MissingClass.java:1 implements this contract.\n"}),
    dict(id="C33 same-sentence withdrawal exempts", checker=CITES, expect=0, files={
        PKG + "a.py": "# MissingClass.java:1 was a 6.5.0 citation and does not exist in 7.0.6.\n"}),
    dict(id="C33 back-referencing next sentence exempts", checker=CITES, expect=0, files={
        PKG + "a.py": "# 이 동작의 근거는 MissingClass.java:1 입니다.\n"
                      "# 7.0.6 에는 그 클래스가 없습니다.\n"}),
    dict(id="C33 next sentence without back-reference does not exempt", checker=CITES,
         expect=1, files={
        PKG + "a.py": "# 이 동작의 근거는 MissingClass.java:1 입니다.\n"
                      "# 로그에는 카드번호가 없습니다.\n"}),
    # -- C34 터무니없는 줄 번호 ---------------------------------------------------
    dict(id="C34 5000-digit line number is invalid", checker=CITES, expect=1, no_traceback=True,
         files={PKG + "a.py": "# RealClass.java:" + "9" * 5000 + "\n",
                "analysis/RealClass.java": "// line\n"}),
    dict(id="C34 absurd line is not exempt by marker", checker=CITES, expect=1, no_traceback=True,
         files={PKG + "a.py": "# stale: RealClass.java:1-" + "9" * 5000 + "\n",
                "analysis/RealClass.java": "// line\n"}),
    # -- C35 못 읽는 대상 파일 ----------------------------------------------------
    dict(id="C35 permission-denied target is incomplete", checker=CITES, expect=2,
         needs_unreadable=True, files={
        PKG + "a.py": "# RealClass.java:1\n",
        "analysis/RealClass.java": ("mode000", "// valid first line\n")}),
    dict(id="C35 dangling-symlink target is incomplete", checker=CITES, expect=2, files={
        PKG + "a.py": "# RealClass.java:1\n", "analysis/RealClass.java": None}),
    dict(id="C35 unreadable duplicate but a readable match passes", checker=CITES, expect=0,
         files={PKG + "a.py": "# RealClass.java:1\n",
                "analysis/one/RealClass.java": "// line\n",
                "analysis/two/RealClass.java": None}),
    # -- 그 밖의 불완전 -----------------------------------------------------------
    dict(id="cites undecodable source is incomplete", checker=CITES, expect=2, files={
        PKG + "a.py": b"\xff", PKG + "b.py": "# RealClass.java:1\n",
        "analysis/RealClass.java": "// line\n"}),
    dict(id="cites internal error is incomplete", checker=CITES, expect=2,
         inject="import os\ndef boom(*a, **k): raise RuntimeError('injected')\nos.walk = boom\n",
         files={PKG + "a.py": "# RealClass.java:1\n", "analysis/RealClass.java": "// line\n"}),
    dict(id="cites missing analysis/ is incomplete", checker=CITES, expect=2, no_analysis=True,
         files={PKG + "a.py": "# RealClass.java:1\n"}),
    dict(id="cites via KORAIL_CHECK_ROOT", checker=CITES, expect=0, via_env=True, files={
        PKG + "a.py": "# RealClass.java:1\n", "analysis/RealClass.java": "// line\n"}),
]


def _build(root: pathlib.Path, case: dict) -> list[pathlib.Path]:
    (root / PKG).mkdir(parents=True)
    if not case.get("no_analysis"):
        (root / "analysis").mkdir()
    locked = []
    for rel, value in case["files"].items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if value is None:
            path.symlink_to(root / "missing-file")
        elif isinstance(value, bytes):
            path.write_bytes(value)
        elif isinstance(value, tuple):
            path.write_text(value[1], encoding="utf-8")
            path.chmod(0)
            locked.append(path)
        else:
            path.write_text(value, encoding="utf-8")
    return locked


def _run(case: dict) -> tuple[bool | None, str]:
    """(기대대로인가 — None 은 건너뜀, 설명)."""
    with tempfile.TemporaryDirectory(prefix="korail-selftest-") as d:
        root = pathlib.Path(d)
        locked = _build(root, case)
        try:
            if case.get("needs_unreadable") and locked and os.access(locked[0], os.R_OK):
                return None, "건너뜀: mode 000 파일을 읽을 수 있는 권한(root?)"
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("KORAIL_CHECK_ROOT", None)
            if case.get("inject"):
                code = (
                    case["inject"]
                    + "import runpy, sys\n"
                    + f"sys.argv = [{str(case['checker'])!r}, '--root', {d!r}]\n"
                    + f"runpy.run_path({str(case['checker'])!r}, run_name='__main__')\n"
                )
                cmd = [sys.executable, "-c", code]
            elif case.get("via_env"):
                env["KORAIL_CHECK_ROOT"] = d
                cmd = [sys.executable, str(case["checker"])]
            else:
                cmd = [sys.executable, str(case["checker"]), "--root", d]
            r = subprocess.run(
                cmd, cwd=d, env=env, capture_output=True, text=True, timeout=60
            )
        finally:
            for path in locked:
                path.chmod(0o644)
    problems = []
    if r.returncode != case["expect"]:
        problems.append(f"exit {r.returncode}, 기대 {case['expect']}")
    if case.get("no_traceback") and "Traceback" in r.stderr:
        problems.append("traceback 이 났습니다")
    if case.get("stdout_has") and case["stdout_has"] not in r.stdout:
        problems.append(f"출력에 {case['stdout_has']!r} 가 없습니다")
    detail = "; ".join(problems)
    if problems:
        tail = (r.stdout.strip() + "\n" + r.stderr.strip()).strip()[-600:]
        detail += "\n      " + tail.replace("\n", "\n      ")
    return not problems, detail


def main() -> int:
    for checker in (SPHINX, CITES):
        if not checker.is_file():
            print(f"검사기가 없습니다: {checker}")
            return 2
    failed = skipped = 0
    for case in CASES:
        ok, detail = _run(case)
        if ok is None:
            skipped += 1
            print(f"  건너뜀  {case['id']}  ({detail})")
        elif ok:
            print(f"  통과    {case['id']}")
        else:
            failed += 1
            print(f"  실패    {case['id']}: {detail}")
    print(f"사례 {len(CASES)}개, 실패 {failed}개, 건너뜀 {skipped}개")
    if failed:
        return 1
    if skipped:
        print("검사 불완전 — 건너뛴 사례가 있습니다")
        return 2
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except subprocess.TimeoutExpired as error:
        print(f"시험 불완전 — 시간 초과: {error}")
        code = 2
    except Exception:
        traceback.print_exc()
        print("시험 불완전 — 자체 시험 내부 오류", file=sys.stderr)
        code = 2
    sys.exit(code)
