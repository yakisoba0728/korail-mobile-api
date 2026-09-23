"""마스킹 하네스가 **비어 있지 않은지** 확인합니다.

:mod:`checks.masking_invariants` 가 통과한다는 사실은, 그 하네스가 잘못된
구현을 실제로 걸러 낸다는 것이 확인돼야 의미가 있습니다. 외부 감사가 이
방법으로 하네스의 거짓 통과를 여러 번 찾아냈습니다.

``redaction.py`` 에 일부러 결함을 심고 하네스가 **실패하는지** 봅니다.
원본은 항상 되돌립니다.

성공 조건은 넷 모두입니다. 하나라도 빠지면 0 으로 끝나지 않습니다:

1. 시작 전 **깨끗한 원본에서 하네스가 정확히 0** 이어야 합니다. 원래 실패하는
   하네스라면 모든 변이가 "잡힌" 것처럼 보이기 때문입니다.
2. 모든 변이의 **앵커가 정확히 한 곳에 실재**해야 합니다. 앵커가 없어 건너뛴
   변이는 아무 것도 검증하지 않은 것입니다 — 예전에는 전부 건너뛰어도 성공으로
   끝났습니다.
3. 모든 변이에서 하네스가 **정확히 1**(사례 실패)이어야 합니다. 2 나 그 밖의
   종료, 시간 초과, 문법이 깨진 변이는 "잡음"이 아니라 **검사 불완전**입니다
   (외부 감사 C36).
4. 원복 후 하네스가 **다시 0** 이어야 합니다. 예전에는 원복 후 결과를 출력만
   하고 종료 코드에 반영하지 않았습니다.

종료 코드: 0 통과, 1 실패(놓친 변이·앵커 문제·기준선 실패), 2 검사 불완전.

    python3 checks/masking_mutants.py
"""
import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile

SRC = pathlib.Path("src/korail_mobile_api/redaction.py")
HARNESS = [sys.executable, "checks/masking_invariants.py"]

#: (이름, 원래 코드, 결함을 심은 코드). 각각 **실제로 있었던** 회귀를 되살립니다.
MUTANTS = [
    (
        "JSON 출력을 깨뜨림",
        "            parts.append(json.dumps(inner))",
        "            parts.append(json.dumps(inner)[:-1])",
    ),
    (
        "중복 키의 둘째를 버림",
        "for index, (name, item) in enumerate(node.items):",
        "for index, (name, item) in enumerate(list(dict(node.items).items())):",
    ),
    (
        "민감 키 판정을 끔(JSON 순회)",
        "        if key is not None and is_sensitive_key(key):\n"
        "            parts.append(",
        "        if False:\n"
        "            parts.append(",
    ),
    (
        "카드 마스킹을 끔",
        "if _NUMBER_CARD_RE.search(node.text)",
        "if False",
    ),
    (
        # v7 회귀. 이 변이를 하네스가 통과했었습니다.
        "JSON 안의 문자열에 값 패턴만 적용(v7)",
        "            inner = redact_text(node)",
        "            inner = CARD_RE.sub('[REDACTED_CARD]', node)",
    ),
    (
        # 키 본문과 인덱스 접미사가 밑줄 정의를 따로 가졌을 때의 누락.
        "인덱스 접미사가 escape 밑줄을 못 받음",
        '    r"(?:" + _UNDERSCORE + r"?\\d+" + _UNDERSCORE'
        ' + r"?|" + _UNDERSCORE + r")"',
        '    r"(?:_?\\d+_?|_)"',
    ),
    # --- 최종 감사 C01~C09·C12. 고친 것을 하나씩 되돌립니다.
    (
        # C12: 감사가 쓴 변이 그대로 — 구조 마스킹을 최상위 한 겹만.
        "구조 마스킹이 최상위 한 겹만(C12)",
        "        if is_mapping:\n            mapping_out",
        "        if is_mapping and parent is result:\n            mapping_out",
    ),
    (
        "폼 값의 중첩 구조를 문자열로 뭉갬(C01)",
        "        return _repr_iterative(redact_value(value))",
        "        return redact_text(str(value))",
    ),
    # C03(scheme 생략 URL)은 변이로 두지 않습니다. ``redact_url`` 의 구조 경로와
    # 텍스트 경로의 userinfo 패턴 **둘 다** ``//user@host`` 를 가리므로, 한쪽을
    # 되돌려도 마스킹 결과가 같습니다 — 어떤 마스킹 사례로도 죽일 수 없는 동등
    # 변이입니다. 두 층을 한꺼번에 끄는 변이는 C03 이 아니라 전혀 다른 것을
    # 시험하게 됩니다. C03 자체는 하네스의 ``final/C03_schemerel`` 이 봅니다.
    (
        "가린 게 없어도 재직렬화(C05)",
        "        if not changed:\n            return value",
        "        if False:\n            return value",
    ),
    (
        # 옛 정규식 ``\\.`` 는 백슬래시 뒤 LF 를 escape 쌍으로 못 받아, 따옴표 값이
        # 깨지고 공백(그 LF)까지만 가려졌습니다. 그 동작을 그대로 되살립니다.
        "따옴표 값 escape 쌍이 줄바꿈 못 넘음(C06)",
        '        if char == "\\\\":\n            index += 2',
        '        if char == "\\\\" and text[index + 1 : index + 2] == "\\n":\n'
        "            return _WHITESPACE_RE.search(text, start).start(), True\n"
        '        if char == "\\\\":\n            index += 2',
    ),
    (
        "host 의 카드번호를 안 봄(C07)",
        "    host = _mask_key_text(host)",
        "    host = host",
    ),
    (
        "URL 처리 예외를 안 삼킴(C08)",
        "    except (ValueError, UnicodeError):\n        return _redact_url_fallback(value)",
        "    except ZeroDivisionError:\n        return _redact_url_fallback(value)",
    ),
    (
        "JSON 키의 카드번호를 안 가림(G5)",
        "                shown = _mask_key(name, used_keys, reserved_keys)",
        "                shown = name",
    ),
    (
        # v8 회귀. 로그 전체의 escape 를 먼저 풀어 값을 바꿨습니다.
        "로그 전체의 ASCII escape 를 먼저 풂(v8)",
        "    redacted = value\n",
        "    redacted = re.sub(r'\\\\u00([2-7][0-9A-Fa-f])',"
        " lambda m: chr(int(m.group(1), 16)), value)\n",
    ),
    # --- 외부 감사 C01~C10·C37. 고친 것을 하나씩, **옛 결함 그대로** 되돌립니다.
    (
        "폼 키를 그대로 내보냄(외부 C01)",
        "        name = _mask_key(original, used_keys, reserved_keys)",
        "        name = original",
    ),
    (
        "쿼리 키를 그대로 내보냄(외부 C02)",
        "            _mask_key_text(key),\n",
        "            key,\n",
    ),
    (
        # 옛 구현은 키·host 에 카드번호만 봤습니다.
        "키·host 에 세션 토큰을 안 봄(외부 C03)",
        '    return SESSION_RE.sub(r"\\1[REDACTED]", CARD_RE.sub("[REDACTED_CARD]", name))',
        '    return CARD_RE.sub("[REDACTED_CARD]", name)',
    ),
    (
        # 옛 구현: 리터럴 전체에 CARD_RE.fullmatch — 부호·소수·지수가 붙으면 놓침.
        "숫자 리터럴 전체가 카드번호일 때만 가림(외부 C04)",
        "            if _NUMBER_CARD_RE.search(node.text):",
        "            if CARD_RE.fullmatch(node.text):",
    ),
    (
        # 감사 C37 이 쓴 변이 그대로 — 숫자를 float 로 정규화.
        "숫자 리터럴을 정규화(외부 C37)",
        "                parts.append(node.text)",
        "                parts.append(str(float(node.text)))",
    ),
    (
        # 옛 정규식은 ``[^\s,]`` — 쉼표에서 값이 끝났습니다.
        "쉼표가 따옴표 없는 값을 끝냄(외부 C05)",
        '_EQ_VALUE_END_RE = re.compile(r"\\s|[&;](?=" + _NEXT_FIELD_KEY + r")")',
        '_EQ_VALUE_END_RE = re.compile(r"[\\s,]|[&;](?=" + _NEXT_FIELD_KEY + r")")',
    ),
    (
        # 옛 구현은 이미 쓴 이름만 피했습니다.
        "가린 키가 원래 키와 겹쳐도 모름(외부 C06)",
        "    while candidate in used or candidate in reserved:",
        "    while candidate in used:",
    ),
    (
        # 옛 구현: 한 번 본 컨테이너를 전부 기억(전역 방문 집합).
        "순환 판정이 전역 방문 집합(외부 C07)",
        "            on_path.discard(item)",
        "            pass",
    ),
    (
        "가린 뒤 str() 로 문자열화(외부 C08)",
        "        return _repr_iterative(redact_value(value))",
        "        return str(redact_value(value))",
    ),
    (
        # 옛 구현: 구조 경로가 실패하면 곧장 텍스트 경로.
        "URL 폴백이 퍼센트 인코딩 키를 못 봄(외부 C09)",
        "        return _redact_url_fallback(value)",
        "        return redact_text(value)",
    ),
    (
        # 옛 정규식은 한 겹만 봤습니다 — 안쪽 여는 괄호를 세지 않으면 첫 닫는
        # 괄호에서 끝납니다.
        "괄호 값을 한 겹만 봄(외부 C10)",
        "            openers.append(index)",
        "            openers.append(index) if not openers else None",
    ),
    (
        # 옛 구현: json.loads 가 RecursionError 를 내면 자유 텍스트 경로(옛 L6).
        "깊은 JSON 을 표준 json 으로만 읽음(외부 C10·L6)",
        "        return _load_json_iteratively(stripped)",
        "        return json.loads(stripped, object_pairs_hook=_Pairs,"
        " parse_float=_RawNumber, parse_int=_RawNumber,"
        " parse_constant=_RawNumber)",
    ),
    (
        # 옛 구현: 따옴표 없는 값은 키가 따옴표여도 맨 ``[REDACTED]``.
        "산문 JSON 에 맨 [REDACTED] 를 넣음(외부 C10)",
        "        wrap = key_quote",
        '        wrap = ""',
    ),
]


#: 하네스 한 번의 시간 한도(초). 넘으면 "잡음"이 아니라 **검사 불완전**입니다.
HARNESS_TIMEOUT = 600


def _harness_status() -> str:
    """하네스 한 번의 결과: ``"pass"``(0) · ``"fail"``(1) · ``"incomplete"``(그 밖).

    예전에는 "0 이 아니면 잡음"이었습니다. 그래서 변이 상태에서 **언제나 2**(검사
    불완전)를 내는 하네스도 모든 변이를 잡은 것으로 셈해졌고 최종 종료 코드가
    0 이었습니다(외부 감사 C36). 잡음은 **정확히 1** — 사례가 실패했다는 뜻 —
    일 때뿐입니다. 시간 초과도 불완전입니다.
    """
    try:
        code = subprocess.run(
            HARNESS, capture_output=True, text=True, timeout=HARNESS_TIMEOUT
        ).returncode
    except subprocess.TimeoutExpired:
        return "incomplete"
    return {0: "pass", 1: "fail"}.get(code, "incomplete")


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _compiles(text: str) -> bool:
    """문법이 깨진 변이는 아무 결함도 시험하지 않습니다 — 불완전으로 셉니다."""
    try:
        compile(text, str(SRC), "exec")
    except SyntaxError:
        return False
    return True


def main() -> int:
    """종료 코드: 0 통과, 1 실패(놓친 변이·앵커 문제·기준선 실패), 2 검사 불완전."""
    if not SRC.is_file():
        print(f"{SRC} 가 없습니다 — 저장소 루트에서 실행했습니까?")
        return 2
    baseline = _harness_status()
    if baseline != "pass":
        print(f"기준선 {baseline}: 깨끗한 원본에서 하네스가 종료 코드 0 이 아닙니다.")
        print("이 상태에서는 어떤 변이도 '잡혔다'고 말할 수 없습니다.")
        return 1 if baseline == "fail" else 2

    original = SRC.read_bytes()
    original_digest = _digest(SRC)
    missed = 0
    incomplete = 0
    with tempfile.TemporaryDirectory() as tmp:
        backup = pathlib.Path(tmp) / "redaction.py"
        shutil.copy(SRC, backup)
        try:
            for name, old, new in MUTANTS:
                text = original.decode("utf-8")
                count = text.count(old)
                if count != 1:
                    # 0 이면 아무 것도 검증 못 하고, 2 이상이면 어느 자리를 바꿨는지
                    # 알 수 없습니다.
                    print(f"  앵커 {count}곳  {name}  <-- 정확히 한 곳이어야 함")
                    missed += 1
                    continue
                mutated = text.replace(old, new, 1)
                if not _compiles(mutated):
                    print(f"  불완전(문법 오류)  {name}")
                    incomplete += 1
                    continue
                SRC.write_text(mutated, encoding="utf-8")
                status = _harness_status()
                if status == "fail":
                    print(f"  잡음  {name}")
                elif status == "pass":
                    print(f"  놓침  <-- 하네스 구멍  {name}")
                    missed += 1
                else:
                    print(f"  불완전(하네스가 0/1 이 아닌 종료)  {name}")
                    incomplete += 1
        finally:
            shutil.copy(backup, SRC)

    if _digest(SRC) != original_digest:
        print("원복 실패: redaction.py 가 원본과 다릅니다.")
        return 1
    after = _harness_status()
    if after != "pass":
        print(f"원복 후 하네스가 {after} 입니다.")
        return 1 if after == "fail" else 2
    print(
        f"변이 {len(MUTANTS)}개, 놓침·앵커 문제 {missed}개, 불완전 {incomplete}개, "
        "원복 후 기준선 통과"
    )
    if missed:
        return 1
    return 2 if incomplete else 0


if __name__ == "__main__":
    sys.exit(main())
