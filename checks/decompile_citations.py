"""Citation existence audit over src/korail_mobile_api/*.py.

Widened from the old ``[A-Z][A-Za-z0-9_$]+\\.java:`` detector, which could not
structurally see three forms we really write: short/obfuscated class names
behind a package segment (``S4/D.java:``), extensionless citations
(``ResearchService:59``), and smali/xml/json targets.

Three false-positive classes are excluded deliberately:
  * bare-extension shorthand -- ``(smali:35513-35521)`` right after the class
    was named in the same sentence; the extension is not the class name
  * an ellipsis prefix standing in for the class -- ``...$$serializer.java:39``
  * a name with MANY candidate files: out-of-range is only reported when EVERY
    candidate is too short, not just the first one found
"""
import re, sys, pathlib, collections

EXTS = ("java", "smali", "xml", "json", "tsv", "kt")
SEG = r"[A-Za-z_$][\w$-]*"
CITE_RE = re.compile(
    r"(?<![\w/.-])"
    r"(?P<target>(?:" + SEG + r"/)*" + SEG + r"(?:\.(?:" + "|".join(EXTS) + r"))?)"
    r":(?P<line>\d+)(?:\s*[-–]\s*(?P<end>\d+))?"
    r"(?![\w.])"
)
# 2026-09-23: 이 목록이 좁아서 "미표기" 수가 부풀려졌습니다. 실제로 쓰고 있는
# 한국어 표현 중 "원래 인용"·"원래 근거였던"·"없는 경로"·"없는 파일" 이 빠져
# 있었고, 그 아홉 건이 전부 이미 제대로 표기돼 있었습니다.
MARKERS = ["6.5.0", "옛 인용", "예전 인용", "원래 인용", "원래 근거", "폐기",
           "부재", "없습니다", "없다", "없는 경로", "없는 파일", "없는 이름",
           "존재하지", "withdrawn", "does not exist", "no longer", "stale",
           "미출처", "출처 없", "재도출", "확인하지 못", "찾지 못", "absent",
           "디컴파일에 없", "7.0.6 에 없", "0건", "스테일", "인용하던",
           "인용이던", "withdraw", "철회", "그 클래스는", "없는 클래스",
           "The old citation", "old citation", "is wrong", "There is no",
           "no such", "not exist", "6.5.0-era"]

def is_shorthand(t):
    stem = t.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    # ``…$$serializer.java:39-79`` — 앞의 클래스명이 바로 앞 문장에 적혀 있고
    # 생략 부호로 이어받은 형태. 파일은 실재합니다.
    return t in EXTS or stem in ("", "…", "...") or stem.startswith("$$")

def looks_like_class(name):
    if "/" in name: return True
    return bool(re.search(r"[a-z][A-Z]", name.rsplit("/", 1)[-1]))

INCOMPLETE: list[str] = []


def _source_files(root: pathlib.Path):
    """읽을 수 있는 ``.py`` 만. 못 읽는 파일은 건너뛰고 알립니다.

    ``glob("*.py")`` 결과를 그대로 열었더니, 아카이브를 그대로 푼 환경에서
    macOS AppleDouble(``._foo.py``)을 만나 ``UnicodeDecodeError`` 로 **검사기
    자체가 죽었습니다**. 점검 도구가 환경 부산물 하나에 멈춰서는 안 됩니다
    (2026-09-23).
    """
    for path in sorted(root.glob("*.py")):
        if path.name.startswith("._"):
            continue  # macOS AppleDouble — 소스가 아닙니다.
        try:
            yield path, path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as error:
            # **실제 소스**를 못 읽었으면 검사가 완료된 것이 아닙니다. 건너뜀만
            # 출력하고 성공으로 끝내던 것을 고쳤습니다(2026-09-23 외부 감사).
            print(f"  읽지 못함: {path.name} ({type(error).__name__})")
            INCOMPLETE.append(path.name)


ANALYSIS = pathlib.Path("analysis")
if not ANALYSIS.is_dir():
    print(
        "analysis/ 가 없습니다 — 이 검사는 디컴파일 트리가 있어야 합니다.\n"
        "그 트리는 .gitignore 로 빠져 있습니다(앱 바이너리는 재배포 대상이"
        " 아닙니다). 로컬에 풀어 둔 뒤 다시 실행하십시오."
    )
    raise SystemExit(0)

EXT_GLOBS = ("*.java", "*.smali", "*.xml", "*.json", "*.tsv", "*.kt")
inv = [str(f) for g in EXT_GLOBS for f in ANALYSIS.rglob(g)]
by_base, by_stem = collections.defaultdict(list), collections.defaultdict(list)
for p in inv: by_base[p.rsplit("/", 1)[-1]].append(p)
for b, ps in by_base.items(): by_stem[b.rsplit(".", 1)[0]].extend(ps)
LINES = {}
def nlines(p):
    if p not in LINES:
        try: LINES[p] = sum(1 for _ in open(p, errors="ignore"))
        except OSError: LINES[p] = 0
    return LINES[p]

def block(lines, i):
    lo, hi = i, i
    while lo > 0 and i - lo < 40 and (lines[lo-1].strip().startswith("#") or '"""' in lines[lo-1]
          or (lines[lo-1].strip() and not re.match(r"\s*(def |class |@|return |[a-z_]+ *=)", lines[lo-1]))): lo -= 1
    while hi < len(lines)-1 and hi - i < 40 and (lines[hi+1].strip().startswith("#") or '"""' in lines[hi+1]
          or (lines[hi+1].strip() and not re.match(r"\s*(def |class |@|return )", lines[hi+1]))): hi += 1
    return "\n".join(lines[lo:hi+1])

total = shorthand = 0
unexpl, expl = [], []
for py, _text in _source_files(pathlib.Path("src/korail_mobile_api")):
    lines = _text.splitlines()
    for i, text in enumerate(lines):
        for m in CITE_RE.finditer(text):
            t = m.group("target")
            has_ext = t.rsplit("/", 1)[-1].rsplit(".", 1)[-1] in EXTS
            if is_shorthand(t): shorthand += 1; continue
            if not has_ext and not looks_like_class(t): continue
            total += 1
            # 두 색인 모두 **basename** 으로 키를 잡습니다. 확장자 생략형에서
            # 경로가 붙은 토큰을 그대로 조회하던 탓에, 실재하는
            # ``pkg/TestCase.java`` 를 ``pkg/TestCase:1`` 로 인용하면 없는
            # 것으로 오판했습니다(2026-09-23 확인).
            base = t.rsplit("/", 1)[-1]
            cands = by_base.get(base, []) if has_ext else by_stem.get(base, [])
            if "/" in t and cands:
                # 확장자 생략형이면 후보의 확장자를 떼고 비교해야 합니다.
                # ``c`` 는 ``.java`` 로 끝나는데 ``t`` 에는 확장자가 없어서,
                # 실재하는 ``pkg/TestCase.java`` 를 ``pkg/TestCase:1`` 로 인용하면
                # 후보가 전부 지워져 "없음"으로 오판했습니다(2026-09-23 확인).
                cands = [
                    c for c in cands
                    if (c if has_ext else c.rsplit(".", 1)[0]).endswith(t)
                ]
            start = int(m.group("line"))
            end = int(m.group("end") or m.group("line"))
            bad = None
            if not cands:
                bad = "absent"
            # 끝 줄만 보다가 ``File.java:0`` 과 ``File.java:8-3`` 이 통과했습니다.
            # 줄 번호는 1부터이고 범위는 뒤집히면 안 됩니다.
            elif start < 1:
                bad = "line<1"
            elif end < start:
                bad = f"range reversed ({start}-{end})"
            elif all(nlines(c) < end for c in cands):
                bad = f"line>{max(nlines(c) for c in cands)}"
            if not bad: continue
            rec = (py.name, i+1, t, bad)
            (expl if any(k in block(lines, i) for k in MARKERS) else unexpl).append(rec)

print(f"citations examined          : {total}   (+{shorthand} shorthand/ellipsis skipped)")
print(f"resolve to a real file      : {total - len(expl) - len(unexpl)}")
print(f"absent or out-of-range      : {len(expl) + len(unexpl)}")
print(f"  labelled as stale in prose: {len(expl)}")
print(f"  UNEXPLAINED               : {len(unexpl)}")
print()
for f, n in collections.Counter(r[0] for r in unexpl).most_common():
    print(f"  {n:4}  {f}")
print()
for r in sorted(unexpl): print(f"  {r[0]}:{r[1]}  {r[2]}  [{r[3]}]")

# 실패·스킵·입력 부재를 모두 0 으로 끝내면 자동 점검의 관문으로 쓸 수 없습니다.
if total == 0:
    print("인용을 하나도 못 찾았습니다 — 저장소 루트에서 실행했습니까?")
    raise SystemExit(2)
if INCOMPLETE:
    print("검사 불완전 — 읽지 못한 소스:", ", ".join(INCOMPLETE))
    raise SystemExit(2)
raise SystemExit(1 if unexpl else 0)
