"""``sphinx_symbols.py`` 와 ``decompile_citations.py`` 자신의 회귀 시험.

최종 감사(C28–C35)가 이 두 검사기에서 거짓 통과·거짓 실패·traceback 을
찾아냈습니다. 그 탐침 픽스처를 임시 디렉터리에 그대로 짓고, 검사기를
``--root`` 로 그 트리에 돌려 **종료 코드**를 확인합니다. 고친 쪽(맞는 입력은
여전히 통과)도 함께 둡니다 — 거짓 통과를 막다가 거짓 실패를 만들면 안 됩니다.

재감사(RC28–RC34, NC07, NC09)의 탐침도 같은 방식으로 들어 있습니다.

종료 코드: 0 = 전부 기대대로, 1 = 기대와 다른 사례 있음, 2 = 시험 불완전
(검사기를 못 찾음, 시간 초과, 실행한 사례가 ``MIN_CASES`` 보다 적음 — 0개
포함, 이 스크립트 자신의 예상 못 한 예외).

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
#: ("mode000", 텍스트) = 권한 없는 일반 파일, ("dirlink", 루트 기준 경로) =
#: 그 디렉터리를 가리키는 심볼릭 링크.
#:
#: ``meta`` 사례는 검사기 대신 **이 스크립트 자신**을 ``python -c`` 로 돌립니다
#: (``{run}`` 자리에 이 파일 경로가 들어갑니다).
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
    dict(id="RC28 re-exported builtin non-exception under :exc:", checker=SPHINX, expect=1,
         files={PKG + "a.py": "from builtins import list as Plain\n# :exc:`a.Plain`\n"}),
    dict(id="RC28 re-exported builtin exception under :exc:", checker=SPHINX, expect=0,
         files={PKG + "a.py": "from builtins import ValueError as VE\n# :exc:`a.VE`\n"}),
    dict(id="RC28 re-exported stdlib non-exception under :exc:", checker=SPHINX, expect=1,
         files={PKG + "a.py": "from collections import OrderedDict as OD\n# :exc:`a.OD`\n"}),
    dict(id="RC28 unresolvable re-export under :exc: is incomplete", checker=SPHINX, expect=2,
         files={PKG + "a.py": "from no_such_module_rc28 import Thing\n# :exc:`a.Thing`\n"}),
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
    dict(id="RC29 later import overrides earlier assignment", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Real:\n    pass\n",
        PKG + "b.py": "Real = 1\nfrom .a import Real\n# :class:`b.Real`\n"}),
    dict(id="RC29 later assignment overrides earlier import", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Real:\n    pass\n",
        PKG + "b.py": "from .a import Real\nReal = 1\n# :class:`b.Real`\n"}),
    dict(id="RC29 later def overrides earlier class", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class Real:\n    def m(self): pass\ndef Real(): pass\n"
                      "# :meth:`a.Real.m`\n"}),
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
    # 예전엔 이 사례를 "느슨함 1건" 으로 통과시켰습니다(expect=0). 재감사 RC30:
    # c 에 없는 Parent 를 b.Parent 로 대신하면 안 됩니다.
    dict(id="RC30 unbound base name is not a same-named class elsewhere", checker=SPHINX,
         expect=1, files={
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "class Child(Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    dict(id="RC30 unbound base under :exc: is not an exception", checker=SPHINX, expect=1,
         files={
        PKG + "b.py": "class Parent(Exception):\n    pass\n",
        PKG + "c.py": "class Child(Parent): pass\n# :exc:`c.Child`\n"}),
    dict(id="RC30 base behind import * is incomplete", checker=SPHINX, expect=2, files={
        PKG + "b.py": "class Parent:\n    def ghost(self): pass\n",
        PKG + "c.py": "from .b import *\nclass Child(Parent): pass\n# :meth:`c.Child.ghost`\n"}),
    # -- NC07 멤버는 C3 MRO 순서로 --------------------------------------------------
    dict(id="NC07 MRO picks A.foo (method) first", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class A:\n def foo(self): pass\nclass B:\n @property\n def foo(self): pass\n"
                      "class C(A, B): pass\n# :meth:`a.C.foo`\n"}),
    dict(id="NC07 MRO: A.foo is not an attribute", checker=SPHINX, expect=1, files={
        PKG + "a.py": "class A:\n def foo(self): pass\nclass B:\n @property\n def foo(self): pass\n"
                      "class C(A, B): pass\n# :attr:`a.C.foo`\n"}),
    dict(id="NC07 diamond: sibling before shared base", checker=SPHINX, expect=0, files={
        PKG + "a.py": "class Base:\n foo = 1\nclass L(Base): pass\n"
                      "class R(Base):\n def foo(self): pass\n"
                      "class D(L, R): pass\n# :meth:`a.D.foo`\n"}),
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
    dict(id="RC33 generic negation in same sentence does not exempt", checker=CITES,
         expect=1, files={
        PKG + "a.py": "# MissingClass.java:1 의 구현에는 문제가 없습니다.\n"}),
    dict(id="RC33 generic English negation does not exempt", checker=CITES, expect=1, files={
        PKG + "a.py": "# MissingClass.java:1 has no such problem; the value is absent in logs.\n"}),
    dict(id="RC33 'found nothing' does not exempt", checker=CITES, expect=1, files={
        PKG + "a.py": "# MissingClass.java:1 에서 버그를 찾지 못했습니다.\n"}),
    dict(id="RC33 '7.0.6 에는 문제가 없' does not exempt", checker=CITES, expect=1, files={
        PKG + "a.py": "# MissingClass.java:1 은 7.0.6 에는 문제가 없습니다.\n"}),
    dict(id="RC33 '7.0.6 에는 그 클래스가 없' exempts", checker=CITES, expect=0, files={
        PKG + "a.py": "# MissingClass.java:1 을 달고 있었으나 7.0.6 에는 그 클래스가 없습니다.\n"}),
    dict(id="RC33 '존재하지 않' exempts", checker=CITES, expect=0, files={
        PKG + "a.py": "# 출처였던 MissingClass.java:1 이 존재하지 않기 때문입니다.\n"}),
    # -- C34 터무니없는 줄 번호 ---------------------------------------------------
    dict(id="C34 5000-digit line number is invalid", checker=CITES, expect=1, no_traceback=True,
         files={PKG + "a.py": "# RealClass.java:" + "9" * 5000 + "\n",
                "analysis/RealClass.java": "// line\n"}),
    dict(id="C34 absurd line is not exempt by marker", checker=CITES, expect=1, no_traceback=True,
         files={PKG + "a.py": "# stale: RealClass.java:1-" + "9" * 5000 + "\n",
                "analysis/RealClass.java": "// line\n"}),
    dict(id="RC34 leading zeros count toward the digit limit", checker=CITES, expect=1,
         no_traceback=True, stdout_has="line number not plausible", files={
        PKG + "a.py": "# RealClass.java:" + "0" * 5000 + "1\n",
        "analysis/RealClass.java": "// line\n"}),
    dict(id="RC34 leading zeros in range end", checker=CITES, expect=1, no_traceback=True,
         stdout_has="line number not plausible", files={
        PKG + "a.py": "# RealClass.java:1-" + "0" * 5000 + "1\n",
        "analysis/RealClass.java": "// line\n"}),
    dict(id="RC34 ten raw digits is over the limit", checker=CITES, expect=1, files={
        PKG + "a.py": "# RealClass.java:0000000001\n", "analysis/RealClass.java": "// line\n"}),
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
    # -- 링크된 analysis 하위 디렉터리 --------------------------------------------
    dict(id="symlinked analysis subdirectory is followed", checker=CITES, expect=0, files={
        PKG + "a.py": "# pkg/RealClass.java:2\n",
        "elsewhere/pkg/RealClass.java": "// one\n// two\n",
        "elsewhere/loop": ("dirlink", "elsewhere"),
        "analysis/linked": ("dirlink", "elsewhere")}),
    # 링크가 실제 경로보다 먼저 닿아도(이름 순서) 실제 경로 인용이 맞아야 함(최종 검토).
    dict(id="real path cited while an earlier-sorted link aliases it", checker=CITES, expect=0, files={
        PKG + "a.py": "# analysis/jadx/sources/com/korail/RealClass.java:2\n",
        "analysis/jadx/sources/com/korail/RealClass.java": "// one\n// two\n",
        "analysis/aaa": ("dirlink", "analysis/jadx/sources/com")}),
    # -- NC09 사례 수 하한 --------------------------------------------------------
    dict(id="NC09 zero cases is incomplete", meta=True, expect=2, code=(
        "import runpy\nns = runpy.run_path({run!r})\nns['CASES'].clear()\n"
        "raise SystemExit(ns['main']())\n")),
    dict(id="NC09 fewer cases than MIN_CASES is incomplete", meta=True, expect=2, code=(
        "import runpy\nns = runpy.run_path({run!r})\n"
        "keep = [c for c in ns['CASES'] if c.get('via_env')]\n"
        "ns['CASES'][:] = keep\nraise SystemExit(ns['main']())\n")),
]

#: 등록된 사례 수. 실행한 사례가 이보다 적으면(0개 포함) 시험 불완전입니다 —
#: ``CASES`` 가 비었는데 "실패 0개" 로 통과하던 것을 막습니다(재감사 NC09).
#: 사례를 더하거나 빼면 이 수도 고치십시오. 모자라면 exit 2, 넘치면 exit 1
#: (``_self_consistent``)로 알려 줍니다.
MIN_CASES = 61


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
        elif isinstance(value, tuple) and value[0] == "dirlink":
            (root / value[1]).mkdir(parents=True, exist_ok=True)
            path.symlink_to(root / value[1], target_is_directory=True)
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
        locked = [] if case.get("meta") else _build(root, case)
        try:
            if case.get("needs_unreadable") and locked and os.access(locked[0], os.R_OK):
                return None, "건너뜀: mode 000 파일을 읽을 수 있는 권한(root?)"
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            env.pop("KORAIL_CHECK_ROOT", None)
            if case.get("meta"):
                cmd = [sys.executable, "-c", case["code"].format(run=str(pathlib.Path(__file__).resolve()))]
            elif case.get("inject"):
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
    failed = skipped = ran = 0
    for case in CASES:
        ok, detail = _run(case)
        ran += 1
        if ok is None:
            skipped += 1
            print(f"  건너뜀  {case['id']}  ({detail})")
        elif ok:
            print(f"  통과    {case['id']}")
        else:
            failed += 1
            print(f"  실패    {case['id']}: {detail}")
    print(f"사례 {ran}개(등록 하한 {MIN_CASES}개), 실패 {failed}개, 건너뜀 {skipped}개")
    if failed:
        return 1
    if ran == 0 or ran < MIN_CASES:
        # 사례가 없거나 모자라면 "실패 0개" 는 아무것도 증명하지 않습니다(NC09).
        print(f"시험 불완전 — 실행한 사례 {ran}개가 하한 {MIN_CASES}개보다 적습니다")
        return 2
    if ran > MIN_CASES:
        print(f"MIN_CASES({MIN_CASES})가 실제 사례 수({ran})와 다릅니다 — 하한을 고치십시오")
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
