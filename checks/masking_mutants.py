"""마스킹 하네스가 **비어 있지 않은지** 확인합니다.

:mod:`checks.masking_invariants` 가 통과한다는 사실은, 그 하네스가 잘못된
구현을 실제로 걸러 낸다는 것이 확인돼야 의미가 있습니다. 외부 감사가 이
방법으로 하네스의 거짓 통과를 여러 번 찾아냈습니다.

``redaction.py`` 에 일부러 결함을 심고 하네스가 **실패하는지** 봅니다.
결함은 **임시 복사본**에만 심습니다. 원본 파일은 쓰지 않습니다 — 예전에는 원본에
심었다가 되돌렸는데, 도중에 프로세스가 죽으면(외부 재현기의 시간 제한) 변이가
원본에 남았고, 같은 트리를 쓰던 다른 검사가 변이된 코드를 시험했습니다
(2026-09-23 재현).

성공 조건은 넷 모두입니다. 하나라도 빠지면 0 으로 끝나지 않습니다:

1. 시작 전 **깨끗한 원본에서 하네스가 정확히 0** 이어야 합니다. 원래 실패하는
   하네스라면 모든 변이가 "잡힌" 것처럼 보이기 때문입니다.
2. 모든 변이의 **앵커가 정확히 한 곳에 실재**해야 합니다. 앵커가 없어 건너뛴
   변이는 아무 것도 검증하지 않은 것입니다 — 예전에는 전부 건너뛰어도 성공으로
   끝났습니다.
3. 모든 변이에서 하네스가 **정확히 1**(사례 실패)이어야 합니다. 2 나 그 밖의
   종료, 시간 초과, 문법이 깨진 변이는 "잡음"이 아니라 **검사 불완전**입니다
   (외부 감사 C36).
4. 변이를 다 돈 뒤 **원본이 바이트 그대로**이고, 원본에서 하네스가 **다시 0** 이어야
   합니다.

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
        "            inner = _redact_text(node)",
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
        "    return _repr_iterative(masked)\n",
        "    return redact_text(str(value))\n",
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
        "    while shown in used or shown in reserved:",
        "    while shown in used:",
    ),
    (
        # 옛 구현: 한 번 본 컨테이너를 전부 기억(전역 방문 집합).
        "순환 판정이 전역 방문 집합(외부 C07)",
        "            on_path.discard(item)",
        "            pass",
    ),
    (
        "가린 뒤 str() 로 문자열화(외부 C08)",
        "    return _repr_iterative(masked)\n",
        "    return str(masked)\n",
    ),
    (
        # 옛 구현: 구조 경로가 실패하면 곧장 텍스트 경로.
        "URL 폴백이 퍼센트 인코딩 키를 못 봄(외부 C09)",
        "    except (ValueError, UnicodeError):\n        return _redact_url_fallback(value)",
        "    except (ValueError, UnicodeError):\n        return redact_text(value)",
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
    (
        "맨 숫자를 어디서나 JSON 문서로 봄(카드 문자열에 따옴표 두 겹)",
        """    roots = '{["-0123456789' if scalar_root else '{["'""",
        """    roots = '{["-0123456789'""",
    ),
    (
        "set·frozenset 을 그대로 둠",
        "        is_sequence = isinstance(item, (list, tuple, set, frozenset))",
        "        is_sequence = isinstance(item, (list, tuple))",
    ),
    (
        "숫자 카드번호를 그대로 둠",
        "        elif _is_card_shaped_number(item):",
        "        elif False:",
    ),
    # --- 재감사(2026-09-23) RC08·NC01~NC06·NC11·NN03. 고친 것을 옛 결함 그대로 되돌립니다.
    (
        "반복 문자열화가 set·frozenset 을 재귀 repr 로 씀(재감사 RC08)",
        "        elif kind is list or kind is tuple or kind is set or kind is frozenset:",
        "        elif kind is list or kind is tuple:",
    ),
    (
        "문자열이 아닌 매핑 키를 그대로 둠(재감사 NC01)",
        "                    masked_text = _masked_key_text(child_key)\n",
        "                    masked_text = None\n",
    ),
    (
        # 옛 구현은 이미 쓴 이름만 피했고, 문자열이 아닌 키는 번호 없이 str() 이었습니다.
        "폼의 문자열 아닌 키가 원래 문자열 키와 겹쳐도 모름(재감사 NC01)",
        "            name = _unique_key(\n",
        "            name = (lambda text, _u, _r: text)(\n",
    ),
    (
        "float 카드번호를 그대로 둠(재감사 NC02)",
        "        return 1e13 <= abs(value) < 1e19 or bool(_NUMBER_CARD_RE.search(repr(value)))",
        "        return False",
    ),
    (
        "Decimal 카드번호를 그대로 둠(재감사 NC02)",
        "        if not value.is_finite():",
        "        if True:",
    ),
    (
        # 옛 구현: 가린 원소를 무조건 set 에 다시 넣음 — dict 원소에서 TypeError.
        "가린 set 원소가 해시 불가면 예외(재감사 NC03)",
        "        except Exception:  # noqa: BLE001\n            # 가린 원소가 해시할 수 없거나",
        "        except ZeroDivisionError:  # noqa: BLE001\n            # 가린 원소가 해시할 수 없거나",
    ),
    (
        # 옛 구현: 폼의 set·frozenset 값은 str() 뒤 텍스트 경로.
        "폼의 set 값을 str() 로 뭉갬(재감사 NC04)",
        "    masked = redact_value(value)\n    if masked is value:",
        "    if isinstance(value, (set, frozenset)):\n        return _redact_text(str(value))\n"
        "    masked = redact_value(value)\n    if masked is value:",
    ),
    (
        # 옛 구현: 공백 때문에 구조 처리를 포기하면 곧장 텍스트 경로.
        "상대·scheme 생략 URL 포기 시 텍스트 경로(재감사 NC05)",
        '        if parsed.path.startswith("/") or parsed.netloc:\n',
        "        if False:\n",
    ),
    (
        # 옛 구현: &·; + 키= 경계를 = 형식에만.
        "콜론 형식 값이 &키= 에서 안 끝남(재감사 NC06)",
        "    boundary = eq or not _FIELD_KEY_RE.match(text, start)",
        "    boundary = eq",
    ),
    (
        # 반대 방향: 쿠키 헤더 값(키=값 목록)까지 ;키= 에서 끊으면 꼬리가 샙니다.
        "쿠키 헤더 값을 ;키= 에서 끊음(NC06 의 반대 방향)",
        "    boundary = eq or not _FIELD_KEY_RE.match(text, start)",
        "    boundary = True",
    ),
    (
        "URL 폴백이 디코딩한 쿼리 키의 카드번호를 안 봄(재감사 NC11)",
        "        if masked_name != decoded_name:",
        "        if False:",
    ),
    (
        "URL 폴백이 디코딩한 쿼리 값의 카드번호를 안 봄(재감사 NC11)",
        "                if masked_item != decoded_item:",
        "                if False:",
    ),
    (
        # 옛 구현: 자릿수 한도를 넘는 정수의 str()/repr() 이 ValueError.
        "큰 정수의 문자열화가 예외(재감사 NN03)",
        '            return f"<int {value.bit_length()} bits>"',
        "            raise",
    ),
]


#: 하네스 한 번의 시간 한도(초). 넘으면 "잡음"이 아니라 **검사 불완전**입니다.
HARNESS_TIMEOUT = 600


def _harness_status(cwd: pathlib.Path | None = None) -> str:
    """하네스 한 번의 결과: ``"pass"``(0) · ``"fail"``(1) · ``"incomplete"``(그 밖).

    예전에는 "0 이 아니면 잡음"이었습니다. 그래서 변이 상태에서 **언제나 2**(검사
    불완전)를 내는 하네스도 모든 변이를 잡은 것으로 셈해졌고 최종 종료 코드가
    0 이었습니다(외부 감사 C36). 잡음은 **정확히 1** — 사례가 실패했다는 뜻 —
    일 때뿐입니다. 시간 초과도 불완전입니다.
    """
    try:
        code = subprocess.run(
            HARNESS, capture_output=True, text=True, timeout=HARNESS_TIMEOUT,
            cwd=cwd,
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
    # 입력을 **먼저** 읽습니다. 읽을 수 없으면(권한 000 등) 검사 불완전입니다 —
    # 예전에는 기준선 하네스를 돌린 뒤 여기서 ``PermissionError`` traceback 으로
    # 종료 코드 1(= "실패")이 났습니다(재감사 NC10).
    try:
        original = SRC.read_bytes()
        original.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"검사 불완전: {SRC} 를 읽지 못했습니다 — {type(error).__name__}: {error}")
        return 2
    original_digest = hashlib.sha256(original).hexdigest()
    baseline = _harness_status()
    if baseline != "pass":
        print(f"기준선 {baseline}: 깨끗한 원본에서 하네스가 종료 코드 0 이 아닙니다.")
        print("이 상태에서는 어떤 변이도 '잡혔다'고 말할 수 없습니다.")
        return 1 if baseline == "fail" else 2

    missed = 0
    incomplete = 0
    with tempfile.TemporaryDirectory() as tmp:
        # 하네스는 ``src`` 를 cwd 기준으로 import 하므로 트리째 복사해 거기서 돌립니다.
        root = pathlib.Path(tmp)
        shutil.copytree("src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        (root / "checks").mkdir()
        shutil.copy(HARNESS[1], root / HARNESS[1])
        target = root / SRC
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
            target.write_text(mutated, encoding="utf-8")
            status = _harness_status(root)
            if status == "fail":
                print(f"  잡음  {name}")
            elif status == "pass":
                print(f"  놓침  <-- 하네스 구멍  {name}")
                missed += 1
            else:
                print(f"  불완전(하네스가 0/1 이 아닌 종료)  {name}")
                incomplete += 1
        target.write_bytes(original)

    if _digest(SRC) != original_digest:
        print("원본 변경됨: redaction.py 가 실행 중에 바뀌었습니다.")
        return 1
    after = _harness_status()
    if after != "pass":
        print(f"변이 뒤 원본에서 하네스가 {after} 입니다.")
        return 1 if after == "fail" else 2
    print(
        f"변이 {len(MUTANTS)}개, 놓침·앵커 문제 {missed}개, 불완전 {incomplete}개, "
        "원본 무변경·기준선 재통과"
    )
    if missed:
        return 1
    return 2 if incomplete else 0


if __name__ == "__main__":
    # 실행기 자체의 예상 못 한 예외(임시 디렉터리·복사·파일 읽기 실패 등)는
    # "놓침"이 아니라 **검사 불완전(2)** 입니다. traceback 의 종료 코드 1 은
    # "실패"와 구분되지 않았습니다(재감사 NC10).
    try:
        exit_code = main()
    except Exception as error:  # noqa: BLE001
        print(f"검사 불완전: 변이 실행기 오류 — {type(error).__name__}: {error}")
        exit_code = 2
    sys.exit(exit_code)
