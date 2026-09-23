"""마스킹 하네스가 **비어 있지 않은지** 확인합니다.

:mod:`checks.masking_invariants` 가 통과한다는 사실은, 그 하네스가 잘못된
구현을 실제로 걸러 낸다는 것이 확인돼야 의미가 있습니다. 외부 감사가 정확히
이 방법으로 하네스의 거짓 통과 두 건을 찾아냈습니다 — 결함 표식을 붙이는
헬퍼를 두고도 사례의 금지 목록에 그 표식을 넣지 않아, 깨진 JSON 을 돌려주는
구현이 통과하고 있었습니다.

``redaction.py`` 에 일부러 결함을 심고 하네스가 **실패하는지** 봅니다.
하나라도 통과하면 그 하네스는 그만큼 못 미더운 것입니다. 원본은 항상
되돌립니다.

    python3 checks/masking_mutants.py
"""
import subprocess, sys, pathlib, shutil
SRC = pathlib.Path("src/korail_mobile_api/redaction.py")
BAK = pathlib.Path("/tmp/redaction.mutate.bak")
MUTANTS = [
    ("JSON 출력을 깨뜨림", 'parts.append(json.dumps(redact_text(node)))',
     'parts.append(json.dumps(redact_text(node))[:-1])'),
    ("중복 키의 둘째를 버림", 'for index, (name, item) in enumerate(node.items):',
     'for index, (name, item) in enumerate(list(dict(node.items).items())):'),
    ("민감 키 판정을 끔", 'if key is not None and is_sensitive_key(key):',
     'if False:'),
    ("카드 마스킹을 끔", 'if CARD_RE.fullmatch(node.text)', 'if False'),
]
shutil.copy(SRC, BAK)
fails = 0
try:
    for name, old, new in MUTANTS:
        s = BAK.read_text()
        if old not in s:
            print(f"  SKIP  {name} (앵커 없음)"); continue
        SRC.write_text(s.replace(old, new, 1))
        r = subprocess.run([sys.executable, "checks/masking_invariants.py"],
                           capture_output=True, text=True)
        caught = r.returncode != 0
        print(f"  {'잡음' if caught else '놓침 <-- 문제'}  {name}")
        fails += not caught
finally:
    shutil.copy(BAK, SRC)
r = subprocess.run([sys.executable, "checks/masking_invariants.py"], capture_output=True, text=True)
print("원복 후:", r.stdout.strip().splitlines()[-1], "exit", r.returncode)
sys.exit(1 if fails else 0)
