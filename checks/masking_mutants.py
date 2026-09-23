"""마스킹 하네스가 **비어 있지 않은지** 확인합니다.

:mod:`checks.masking_invariants` 가 통과한다는 사실은, 그 하네스가 잘못된
구현을 실제로 걸러 낸다는 것이 확인돼야 의미가 있습니다. 외부 감사가 이
방법으로 하네스의 거짓 통과를 여러 번 찾아냈습니다.

``redaction.py`` 에 일부러 결함을 심고 하네스가 **실패하는지** 봅니다.
원본은 항상 되돌립니다.

성공 조건은 넷 모두입니다. 하나라도 빠지면 실패로 끝납니다:

1. 시작 전 **깨끗한 원본에서 하네스가 통과**해야 합니다. 원래 실패하는
   하네스라면 모든 변이가 "잡힌" 것처럼 보이기 때문입니다.
2. 모든 변이의 **앵커가 실재**해야 합니다. 앵커가 없어 건너뛴 변이는 아무 것도
   검증하지 않은 것입니다 — 예전에는 전부 건너뛰어도 성공으로 끝났습니다.
3. 모든 변이에서 하네스가 **실패**해야 합니다.
4. 원복 후 하네스가 **다시 통과**해야 합니다. 예전에는 원복 후 결과를 출력만
   하고 종료 코드에 반영하지 않았습니다.

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
        "parts.append(json.dumps(redact_text(node)))",
        "parts.append(json.dumps(redact_text(node))[:-1])",
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
        "if CARD_RE.fullmatch(node.text)",
        "if False",
    ),
    (
        # v7 회귀. 이 변이를 하네스가 통과했었습니다.
        "JSON 안의 문자열에 값 패턴만 적용(v7)",
        "parts.append(json.dumps(redact_text(node)))",
        "parts.append(json.dumps(CARD_RE.sub('[REDACTED_CARD]', node)))",
    ),
    (
        # 키 본문과 인덱스 접미사가 밑줄 정의를 따로 가졌을 때의 누락.
        "인덱스 접미사가 escape 밑줄을 못 받음",
        '    r"(?:" + _UNDERSCORE + r"?\\d+" + _UNDERSCORE'
        ' + r"?|" + _UNDERSCORE + r")"',
        '    r"(?:_?\\d+_?|_)"',
    ),
    (
        # v8 회귀. 로그 전체의 escape 를 먼저 풀어 값을 바꿨습니다.
        "로그 전체의 ASCII escape 를 먼저 풂(v8)",
        "    redacted = value\n",
        "    redacted = re.sub(r'\\\\u00([2-7][0-9A-Fa-f])',"
        " lambda m: chr(int(m.group(1), 16)), value)\n",
    ),
]


def _harness_passes() -> bool:
    return subprocess.run(HARNESS, capture_output=True, text=True).returncode == 0


def _digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    if not SRC.is_file():
        print(f"{SRC} 가 없습니다 — 저장소 루트에서 실행했습니까?")
        return 2
    if not _harness_passes():
        print("기준선 실패: 깨끗한 원본에서 하네스가 이미 실패합니다.")
        print("이 상태에서는 어떤 변이도 '잡혔다'고 말할 수 없습니다.")
        return 1

    original = SRC.read_bytes()
    original_digest = _digest(SRC)
    problems = 0
    with tempfile.TemporaryDirectory() as tmp:
        backup = pathlib.Path(tmp) / "redaction.py"
        shutil.copy(SRC, backup)
        try:
            for name, old, new in MUTANTS:
                text = original.decode("utf-8")
                if old not in text:
                    print(f"  앵커 없음  {name}  <-- 이 변이는 아무 것도 검증 못 함")
                    problems += 1
                    continue
                SRC.write_text(text.replace(old, new, 1), encoding="utf-8")
                caught = not _harness_passes()
                print(f"  {'잡음' if caught else '놓침  <-- 하네스 구멍'}  {name}")
                problems += not caught
        finally:
            shutil.copy(backup, SRC)

    if _digest(SRC) != original_digest:
        print("원복 실패: redaction.py 가 원본과 다릅니다.")
        return 1
    if not _harness_passes():
        print("원복 후 하네스가 실패합니다.")
        return 1
    print(f"변이 {len(MUTANTS)}개, 문제 {problems}개, 원복 후 기준선 통과")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
