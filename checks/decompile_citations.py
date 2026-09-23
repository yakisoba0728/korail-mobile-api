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

경로 비교는 **경로 구성 요소 단위**입니다. ``pkg/TestCase.java`` 는
``…/pkg/TestCase.java`` 에만 맞고 ``…/notpkg/TestCase.java`` 에는 맞지 않습니다
(최종 감사 C32 — 예전엔 문자열 ``endswith`` 라 맞았습니다). 확장자 생략형
``pkg/TestCase:1`` 은 마지막 구성 요소의 확장자를 떼고 같은 규칙으로 봅니다.

"폐기 표기" 면제는 **그 인용이 든 문장 안**에, **명시적인 철회·부재 표현**이
있을 때만 줍니다(C33). 예전에는 인용 앞뒤 최대 40줄의 주석 덩어리 어디에든
``There is no`` 같은 흔한 구절이 있으면 면제해서, "There is no reason to
doubt…" 한 줄이 무관한 없는 인용을 덮었습니다.

줄 번호가 터무니없으면(**원문 숫자열이** 9자리 초과, 앞의 0 포함) **틀린
인용**(exit 1)으로 셉니다. 폐기 표기로 면제되지 않습니다 — 없는 파일의 옛 줄
번호라도 그런 숫자는 오타입니다. 예전엔 5,000자리 숫자에서 ``int()`` 가 죽어
traceback 과 exit 1 을 냈고(C34), 그 뒤엔 앞의 0 을 떼고 길이를 재서 ``0``
5,000개 + ``1`` 이 통과한 뒤 ``int()`` 가 죽었습니다(재감사 RC34).

``analysis/`` 아래의 **디렉터리 심볼릭 링크도 따라갑니다**(순환은 실제 경로로
한 번만). 예전엔 ``os.walk`` 가 링크된 하위 디렉터리에 들어가지 않아, 그
안을 가리키는 인용이 전부 "absent" 로 보였습니다.

인용된 파일을 **못 읽으면**(권한 없음, 끊긴 심볼릭 링크 등) 그 인용의 줄 범위를
판정할 수 없으므로 **검사 불완전**(exit 2)입니다. 예전엔 길이 0 으로 취급해
"out of range" 실패로 오판했습니다(C35).

종료 코드: 0 = 미표기 없음, 1 = 미표기 인용 있음, 2 = 검사 불완전(analysis/
없음, 소스·대상 파일을 못 읽음, 인용 0건, 검사기 자체의 예상 못 한 예외).

    python3 checks/decompile_citations.py [--root DIR]

``--root`` (또는 환경 변수 ``KORAIL_CHECK_ROOT``)는 저장소 루트를 바꿉니다.
"""
import collections
import os
import pathlib
import re
import sys
import traceback

EXTS = ("java", "smali", "xml", "json", "tsv", "kt")
SEG = r"[A-Za-z_$][\w$-]*"
CITE_RE = re.compile(
    r"(?<![\w/.-])"
    r"(?P<target>(?:" + SEG + r"/)*" + SEG + r"(?:\.(?:" + "|".join(EXTS) + r"))?)"
    r":(?P<line>\d+)(?:\s*[-–]\s*(?P<end>\d+))?"
    r"(?![\w.])"
)
#: 이보다 긴 줄 번호는 오타로 봅니다. 가장 긴 디컴파일 파일도 7자리를 넘지
#: 않습니다. ``int()`` 에 넘기기 **전에** 자릿수로 거릅니다.
MAX_LINE_DIGITS = 9

# 면제 표현. **인용과 같은 문장 안**에 있어야 합니다(``explained`` 참고).
#
# 2026-09-23: 이 목록이 좁아서 "미표기" 수가 부풀려졌고, 한국어 표현 몇 개를
# 더했습니다. 최종 감사(C33)에서 반대 방향이 드러났습니다 — ``There is no``,
# ``is wrong``, ``0건``, ``그 클래스는`` 처럼 **철회와 무관하게도 흔히 쓰는**
# 구절이 들어 있었고, 판정 범위가 문장이 아니라 주변 40줄이었습니다. 흔한
# 구절은 뺐습니다.
#
# 재감사(RC33): 같은 문장이어도 ``없습니다``·``없다`` 만으로는 부족했습니다 —
# "MissingClass.java:1 의 구현에는 문제가 없습니다" 가 면제됐습니다. 이제는
# **무엇이** 없는지까지 말해야 합니다("7.0.6 에 없", "7.0.6 에는 그 클래스가
# 없", "디컴파일에 없", "존재하지 않", "없는 파일"…). 같은 이유로 ``찾지 못``·
# ``확인하지 못``·``no such``·``absent``·``부재``·``not exist`` 같은 일반
# 부정도 뺐습니다(영어는 "does not exist", "no longer exists" 처럼 대상의
# 부재를 말하는 꼴만).
MARKERS = [
    # 그 인용이 옛 판·옛 서술의 것이라는 표기
    "6.5.0", "옛 인용", "예전 인용", "원래 인용", "원래 근거", "옛 근거",
    "인용하던", "인용이던", "이전 판", "이전 서술", "종전", "예전 주석", "원래 주석",
    "old citation", "The original rationale", "the original claim",
    # 철회
    "폐기", "철회", "withdrawn", "withdraw", "stale", "스테일",
    # 부재 — 인용 대상이 없다는 말이어야 합니다
    "없는 경로", "없는 파일", "없는 이름", "없는 클래스",
    "존재하지 않", "does not exist", "doesn't exist", "no longer exist",
    "no longer present", "not in the 7.0.6", "absent from the 7.0.6",
    "absent from 7.0.6", "no such file", "no such class", "no such path",
    "디컴파일에 없", "7.0.6 에 없", "7.0.6에 없",
    # 미출처·재도출
    "미출처", "출처 없", "재도출",
]
_MARKER_RE = re.compile(
    "|".join(re.escape(k) for k in MARKERS)
    # "The old ``X.smali:1-2`` citation" — 인용이 사이에 끼는 꼴
    + r"|\bold\s+\S+\s+citation"
    # "7.0.6 에는 그 클래스가 없고", "7.0.6 에는 두 클래스도 그 메서드 이름도
    # 없습니다" — 판 번호 바로 뒤에 **인용 대상을 가리키는 명사**가 와야 합니다.
    # "7.0.6 에는 문제가 없습니다" 는 맞지 않습니다.
    + r"|7\.0\.6\s*에(?:는|도|서는|서도)?\s+(?:그|두|세|이|해당)?\s*"
      r"(?:클래스|파일|경로|메서드|심볼)[^.。]{0,40}?없"
)
#: 바로 **다음** 문장이 앞 인용을 되받아 설명하는 꼴. 이 말로 시작하는 다음
#: 문장에 철회·부재 표현이 있으면 그 인용의 설명으로 봅니다("… BaseActivity
#: .java:629 를 근거로 달고 있었습니다. 7.0.6 에는 그 클래스도 … 없습니다").
#: 되받는 말이 없으면 이웃 문장은 보지 않습니다 — 그게 C33 의 거짓 면제였습니다.
_BACKREF_RE = re.compile(
    r"그 클래스|그 파일|그 경로|그 인용|그 줄|이 인용|\b[Bb]oth are\b|\bneither class\b"
    r"|\b[Tt]hat (?:file|class|citation|path)\b"
)

#: 문장 경계: 마침표류 뒤 공백, 빈 줄, 목록 머리표로 시작하는 줄.
_SENTENCE_END = re.compile(r"(?<=[.!?。])\s+|\n\s*\n|\n(?=\s*(?:[*\-•]|\d+\.)\s)")


def is_shorthand(t):
    stem = t.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    # ``…$$serializer.java:39-79`` — 앞의 클래스명이 바로 앞 문장에 적혀 있고
    # 생략 부호로 이어받은 형태. 파일은 실재합니다.
    return t in EXTS or stem in ("", "…", "...") or stem.startswith("$$")


def looks_like_class(name):
    if "/" in name:
        return True
    return bool(re.search(r"[a-z][A-Z]", name.rsplit("/", 1)[-1]))


def _root_from_argv(argv):
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root 뒤에 디렉터리가 필요합니다", file=sys.stderr)
            raise SystemExit(2)
        return pathlib.Path(argv[i + 1])
    return pathlib.Path(os.environ.get("KORAIL_CHECK_ROOT", "."))


def _source_files(root, incomplete):
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
            incomplete.append(f"{path.name} ({type(error).__name__})")


class Inventory:
    """``analysis/`` 아래 인용 대상 파일. 경로는 analysis 기준 구성 요소 튜플."""

    def __init__(self, analysis, incomplete):
        self.analysis = analysis
        self.by_base = collections.defaultdict(list)
        self.by_stem = collections.defaultdict(list)
        self._lines = {}

        def onerror(error):
            # rglob 은 못 읽는 하위 디렉터리를 조용히 건너뜁니다. 그러면 그 안을
            # 가리키는 인용이 "없음" 으로 보입니다.
            incomplete.append(f"analysis 하위 디렉터리를 못 읽음: {error.filename}")

        #: 경로 -> 실제 경로. 조상 판정에 씁니다.
        real_of = {}
        for dirpath, dirs, filenames in os.walk(analysis, onerror=onerror, followlinks=True):
            # 링크를 따라가므로 **순환**만 끊습니다 — 실제 디렉터리가 자기 조상과 같을 때.
            # 예전에는 "같은 실제 디렉터리는 한 번만" 이라 먼저 닿은 경로(링크 쪽일 수
            # 있음)로만 색인해, 실제 경로를 쓴 올바른 인용이 이름 순서에 따라 [absent]
            # 가 됐습니다(2026-09-23 최종 검토). 이제 도달 가능한 경로마다 색인합니다.
            try:
                real = os.path.realpath(dirpath)
            except OSError as error:
                incomplete.append(f"analysis 하위 디렉터리를 못 읽음: {dirpath} ({error})")
                dirs[:] = []
                continue
            parent = os.path.dirname(dirpath)
            ancestors = set()
            while parent in real_of:
                ancestors.add(real_of[parent])
                parent = os.path.dirname(parent)
            if real in ancestors:
                dirs[:] = []
                continue
            real_of[dirpath] = real
            rel = pathlib.Path(dirpath).relative_to(analysis).parts
            for name in filenames:
                if name.rsplit(".", 1)[-1] not in EXTS or "." not in name:
                    continue
                parts = (*rel, name)
                self.by_base[name].append(parts)
                self.by_stem[name.rsplit(".", 1)[0]].append(parts)

    def candidates(self, target, has_ext):
        """``target`` 의 구성 요소가 **끝에서부터 통째로** 맞는 파일들.

        인용은 ``analysis/jadx/…`` 처럼 저장소 루트 기준으로도 쓰므로, 비교는
        ``("analysis", *경로)`` 에 대해 합니다."""
        tparts = tuple(target.split("/"))
        n = len(tparts)
        pool = self.by_base if has_ext else self.by_stem
        out = []
        for c in pool.get(tparts[-1], []):
            full = ("analysis", *c)
            if len(full) < n:
                continue
            if has_ext:
                if full[-n:] == tparts:
                    out.append(c)
            elif full[len(full) - n:-1] == tparts[:-1]:
                out.append(c)
        return out

    def nlines(self, parts):
        """줄 수, 또는 못 읽었으면 그 오류 이름(문자열)."""
        if parts not in self._lines:
            path = self.analysis.joinpath(*parts)
            try:
                with open(path, "rb") as handle:
                    count = 0
                    last = b"\n"
                    for chunk in iter(lambda: handle.read(1 << 20), b""):
                        count += chunk.count(b"\n")
                        last = chunk[-1:]
                    self._lines[parts] = count + (last != b"\n")
            except OSError as error:
                self._lines[parts] = type(error).__name__
        return self._lines[parts]


def block(lines, i):
    """인용이 든 주석·독스트링 덩어리의 줄 범위 ``(lo, hi)``."""
    lo, hi = i, i
    while lo > 0 and i - lo < 40 and (lines[lo-1].strip().startswith("#") or '"""' in lines[lo-1]
          or (lines[lo-1].strip() and not re.match(r"\s*(def |class |@|return |[a-z_]+ *=)", lines[lo-1]))): lo -= 1
    while hi < len(lines)-1 and hi - i < 40 and (lines[hi+1].strip().startswith("#") or '"""' in lines[hi+1]
          or (lines[hi+1].strip() and not re.match(r"\s*(def |class |@|return )", lines[hi+1]))): hi += 1
    return lo, hi


def _strip(line):
    s = line.strip()
    if s.startswith("#"):
        s = s.lstrip("#:").strip()
    return s.replace('"""', " ")


def sentences(lines, i, col):
    """(인용이 든 문장, 바로 다음 문장). 문장은 인용이 든 주석·독스트링 덩어리
    안에서만 자릅니다."""
    lo, hi = block(lines, i)
    text, offset = "", 0
    for j in range(lo, hi + 1):
        stripped = _strip(lines[j])
        if j == i:
            # 줄 앞 공백과 ``#`` 을 떼어 낸 만큼 열 위치를 옮깁니다.
            lead = len(lines[j]) - len(lines[j].lstrip())
            raw = lines[j].lstrip()
            if raw.startswith("#"):
                lead += len(raw) - len(raw.lstrip("#:").lstrip())
            offset = len(text) + max(0, col - lead)
        text += stripped + "\n"
    bounds = [0]
    for m in _SENTENCE_END.finditer(text):
        bounds.extend((m.start(), m.end()))
    bounds.append(len(text))
    pieces = [(bounds[k], bounds[k + 1]) for k in range(0, len(bounds), 2)]
    for k, (a, b) in enumerate(pieces):
        if a <= offset < b or (offset >= b and k == len(pieces) - 1):
            following = text[slice(*pieces[k + 1])] if k + 1 < len(pieces) else ""
            return text[a:b], following
    return text, ""


def explained(lines, i, col):
    """그 인용이 든 **문장**에 철회·부재 표현이 있는가. 또는 바로 다음 문장이
    그 인용을 되받으며(``_BACKREF_RE``) 그런 표현을 쓰는가."""
    here, following = sentences(lines, i, col)
    if _MARKER_RE.search(here):
        return True
    return bool(_BACKREF_RE.search(following) and _MARKER_RE.search(following))


def main(argv):
    root = _root_from_argv(argv)
    analysis = root / "analysis"
    if not analysis.is_dir():
        print(
            "analysis/ 가 없습니다 — 이 검사는 디컴파일 트리가 있어야 합니다.\n"
            "그 트리는 .gitignore 로 빠져 있습니다(앱 바이너리는 재배포 대상이"
            " 아닙니다). 로컬에 풀어 둔 뒤 다시 실행하십시오."
        )
        # 검사하지 않았으면 **통과가 아니라 검사 불완전**입니다(exit 2).
        return 2

    incomplete = []
    inv = Inventory(analysis, incomplete)

    total = shorthand = 0
    unexpl, expl, undetermined = [], [], []
    for py, text in _source_files(root / "src" / "korail_mobile_api", incomplete):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            for m in CITE_RE.finditer(line):
                t = m.group("target")
                has_ext = t.rsplit("/", 1)[-1].rsplit(".", 1)[-1] in EXTS
                if is_shorthand(t):
                    shorthand += 1
                    continue
                if not has_ext and not looks_like_class(t):
                    continue
                total += 1
                rec_where = (py.name, i + 1, t)
                start_s = m.group("line")
                end_s = m.group("end") or start_s
                # **원문 숫자열 길이**로 거릅니다. 앞의 0 도 셉니다 — ``lstrip("0")``
                # 뒤의 길이를 보면 ``0``×5000 + ``1`` 이 통과해 ``int()`` 가 죽었습니다
                # (재감사 RC34). 이 검사 전에는 ``int()`` 를 부르지 않습니다.
                longest = max(start_s, end_s, key=len)
                if len(longest) > MAX_LINE_DIGITS:
                    # 면제 없이 틀린 인용입니다. 숫자는 잘라서 보여 줍니다.
                    shown = longest if len(longest) <= 20 else f"{longest[:8]}…({len(longest)}자리)"
                    unexpl.append((*rec_where, f"line number not plausible: {shown}"))
                    continue
                start, end = int(start_s), int(end_s)
                cands = inv.candidates(t, has_ext)
                bad = None
                if not cands:
                    bad = "absent"
                # 끝 줄만 보다가 ``File.java:0`` 과 ``File.java:8-3`` 이 통과했습니다.
                # 줄 번호는 1부터이고 범위는 뒤집히면 안 됩니다.
                elif start < 1:
                    bad = "line<1"
                elif end < start:
                    bad = f"range reversed ({start}-{end})"
                else:
                    sizes = {c: inv.nlines(c) for c in cands}
                    readable = [n for n in sizes.values() if isinstance(n, int)]
                    if any(n >= end for n in readable):
                        continue  # 읽을 수 있는 후보 하나가 맞으면 충분합니다.
                    unreadable = [c for c, n in sizes.items() if not isinstance(n, int)]
                    if unreadable:
                        # 못 읽은 후보가 맞는 파일일 수 있습니다. 판정 불가(C35).
                        undetermined.append(rec_where)
                        for c in unreadable:
                            incomplete.append(
                                f"인용 대상을 못 읽음: {'/'.join(c)} ({sizes[c]})"
                            )
                        continue
                    bad = f"line>{max(readable)}"
                if not bad:
                    continue
                rec = (*rec_where, bad)
                (expl if explained(lines, i, m.start()) else unexpl).append(rec)

    print(f"citations examined          : {total}   (+{shorthand} shorthand/ellipsis skipped)")
    print(f"resolve to a real file      : {total - len(expl) - len(unexpl) - len(undetermined)}")
    print(f"absent or out-of-range      : {len(expl) + len(unexpl)}")
    print(f"  labelled as stale in prose: {len(expl)}")
    print(f"  UNEXPLAINED               : {len(unexpl)}")
    if undetermined:
        print(f"undetermined (unreadable)   : {len(undetermined)}")
    print()
    for f, n in collections.Counter(r[0] for r in unexpl).most_common():
        print(f"  {n:4}  {f}")
    print()
    for r in sorted(unexpl):
        print(f"  {r[0]}:{r[1]}  {r[2]}  [{r[3]}]")

    # 실패·스킵·입력 부재를 모두 0 으로 끝내면 자동 점검의 관문으로 쓸 수 없습니다.
    if incomplete:
        print("검사 불완전 —", "; ".join(dict.fromkeys(incomplete)))
        return 2
    if total == 0:
        print("인용을 하나도 못 찾았습니다 — 저장소 루트에서 실행했습니까?")
        return 2
    return 1 if unexpl else 0


if __name__ == "__main__":
    try:
        code = main(sys.argv[1:])
    except SystemExit:
        raise
    except Exception:
        # 검사기 자신이 죽었으면 검사가 끝난 것이 아닙니다. traceback 의
        # exit 1 을 "미표기 발견" 과 구별할 수 없으므로 2 로 끝냅니다.
        traceback.print_exc()
        print("검사 불완전 — 검사기 내부 오류", file=sys.stderr)
        code = 2
    sys.exit(code)
